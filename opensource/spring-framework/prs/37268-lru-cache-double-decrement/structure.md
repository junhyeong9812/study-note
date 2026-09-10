# PR #37268 - 무대의 실구조와 워크플로우

> PR #37268의 무대가 되는 실구조와 워크플로우. 문제와 수정은 [README.md](README.md),
> 테스트는 [tests.md](tests.md), 착수 시점 분석은 [analysis.md](analysis.md) 참조.
>
> 기준: 로컬 HEAD `ee7ed0093d6`(브랜치 `fix/lru-cache-double-decrement` = upstream main
> `c1d4a766929` 리베이스 + fix 커밋). **이 시점의 `ConcurrentLruCache.java`에는 이미
> 수정이 반영돼 있다** - 아래 file:line은 "수정 후" 좌표이며, 가드 세 줄과 주석 한 줄이
> 늘어난 만큼 `markAsRemoved` 아래쪽 좌표가 수정 전보다 4씩 밀려 있다.

## 1. 무대 - 실구조

이 결함의 무대는 **락 경합을 피하려고 작업을 버퍼에 적어 두었다가 나중에 한꺼번에
처리하는 캐시**이고, 그 지연 처리가 만드는 "아직 반영되지 않은 작업의 큐"가 결함의
발화 조건이다. 계층을 위에서 아래로 그리면 이렇다.

```
+------------------------------------------------------------------------------+
| 공개 API              spring-core/util/ConcurrentLruCache.java                |
|   get(K)        캐시 조회 + miss 시 생성·삽입                        :100-112  |
|   remove(K)     명시적 제거 - 이 결함의 두 번째 재료                  :233-241  |
|   clear()       전부 비우기 (evictionLock 직접 획득)                 :184-198  |
|   size()        map 의 실제 크기를 반환                              :177-179  |
|   capacity()    생성 시 정한 상한                                    :160-162  |
+------------------------------------------------------------------------------+
                 |                                    |
      읽기 경로  v                        쓰기 경로     v
+---------------------------------+  +---------------------------------------+
| processRead(node)      :128-134 |  | processWrite(task)           :136-140 |
|   readOperations.recordRead     |  |   writeOperations.add(task)           |
|   -> 링 버퍼 4개에 노드 기록      |  |   drainStatus = REQUIRED              |
|   -> shouldDrainBuffers 면 드레인 |  |   drainOperations() 를 "직접" 호출     |
|   ** 드레인을 보장하지 않는다 **  |  |   ** 쓰기만이 드레인을 밀어낸다 **      |
+---------------------------------+  +---------------------------------------+
                 |                                    |
                 +------------------+-----------------+
                                    v
+------------------------------------------------------------------------------+
| drainOperations()                                                    :142-154 |
|   evictionLock.tryLock()  <- 실패하면 그냥 돌아간다 (작업은 큐에 남는다)         |
|     drainStatus = PROCESSING                                                  |
|     readOperations.drain()     읽기 버퍼 -> evictionQueue.moveToBack           |
|     writeOperations.drain()    쓰기 큐에서 최대 16건을 꺼내 run()      :468-476 |
|   finally: drainStatus CAS -> IDLE, unlock                                    |
|                                                                              |
|   ** tryLock 실패가 곧 "작업이 큐에 쌓인다" 이고, 그것이 결함의 무대다 **        |
+------------------------------------------------------------------------------+
                                    v
+------------------------------------------------------------------------------+
| 쓰기 작업 두 종류 (둘 다 evictionLock 아래에서만 실행된다)                       |
|                                                                              |
|   AddTask.run()                                                     :272-279 |
|     currentSize.lazySet(currentSize.get() + 1)          카운터 +1     :274    |
|     if (node.isActive()) { evictionQueue.add(node); evictEntries(); }        |
|                                                                              |
|     evictEntries()                                                  :281-290 |
|       while (currentSize.get() > capacity) {   <- 기준이 map 이 아니다 :282    |
|         node = evictionQueue.poll();                                 :283    |
|         cache.remove(node.key, node);          map 에서 실제 제거      :287    |
|         markAsRemoved(node);                   카운터 -1              :288    |
|       }                                                                      |
|                                                                              |
|   RemovalTask.run()                                                 :305-309 |
|     evictionQueue.remove(node);                                      :307    |
|     markAsRemoved(node);                       카운터 -1              :308    |
+------------------------------------------------------------------------------+
                                    v
+------------------------------------------------------------------------------+
| 상태 기계 - 결함이 사는 자리                                                   |
|                                                                              |
|   CacheEntryState  ACTIVE -> PENDING_REMOVAL -> REMOVED               :357-360|
|   CacheEntry       record(value, state)                               :363-368|
|   Node             extends AtomicReference<CacheEntry<V>>             :488-520|
|                                                                              |
|   markForRemoval(node)   ACTIVE -> PENDING_REMOVAL                   :247-258 |
|     if (!current.isActive()) return;      <- 가드가 "있던" 쪽         :250-252 |
|                                                                              |
|   markAsRemoved(node)    무엇이든 -> REMOVED + 카운터 -1              :204-216 |
|     if (current.state == REMOVED) return;  <- 이번에 추가한 가드      :207-209 |
|     if (compareAndSet(current, removed)) currentSize -1               :211-213 |
+------------------------------------------------------------------------------+
```

이 그림에서 읽어야 할 사실은 셋이다. 첫째, **`evictEntries`의 루프 조건이 map이 아니라
`currentSize`다.** 캐시의 크기 판단이 전적으로 그 카운터에 걸려 있으므로 카운터가
어긋나면 축출 정책 전체가 어긋난다. 둘째, **`markAsRemoved`를 부르는 자리가 셋인데
그 셋이 서로를 모른다.** 축출은 자기가 뽑은 노드가 이미 제거 대기 중인지 모르고,
`RemovalTask`는 자기 노드가 이미 축출됐는지 모른다. 셋째, **읽기는 드레인을 보장하지
않고 쓰기만 보장한다.** 이 사실이 조사 과정에서 결정적이었다(4절).

## 2. 두 개의 제거 경로가 같은 노드를 만나는 방식

노드 하나가 캐시에서 사라지는 길은 셋이고, 그중 둘이 겹칠 수 있다. 세 길을 고정 축으로
비교하면 겹침이 어디서 생기는지가 드러난다.

| 경로 | 진입점 | map에서 빼는 자리 | `markAsRemoved` 호출 | 언제 실행되나 |
|---|---|---|---|---|
| 축출 | `AddTask.evictEntries()` | `cache.remove(node.key, node)` :287 | :288 | 드레인 중 |
| 명시적 제거 | `remove(K)` | `this.cache.remove(key)` :234 (즉시) | `RemovalTask.run()` :308 | **나중에** 드레인 중 |
| 전체 비우기 | `clear()` | `cache.remove(node.key, node)` :189 | :190 | 즉시(락 직접 획득) |

**둘째 행의 "즉시"와 "나중에"가 벌어지는 틈이 결함의 시간 창이다.** `remove(K)`는 map
조작을 즉시 끝내고 카운터 조정만 큐에 미룬다. 그 사이에 노드는 `evictionQueue` 안에
`PENDING_REMOVAL` 상태로 남아 있고, 축출은 상태를 보지 않고 큐 머리부터 뽑으므로 그
노드를 뽑을 수 있다.

```
[수정 전]  capacity=2, 캐시에 A,B. 다른 스레드가 evictionLock 보유 중

  스레드 1: get("C")
    put -> map = {A,B,C}                                      map 3 / 카운터 2
    processWrite(AddTask(C)) -> tryLock 실패 -> 큐에 적재       (드레인 못 함)

  스레드 2: remove("A")
    cache.remove("A") -> map = {B,C}                          map 2 / 카운터 2
    markForRemoval(A): ACTIVE -> PENDING_REMOVAL              (A 는 큐에 그대로)
    processWrite(RemovalTask(A)) -> 큐에 적재

  락 해제 후 드레인 - writeOperations.drain() 이 큐를 순서대로 실행
    (1) AddTask(C).run()
          카운터 +1 -> 3
          evictionQueue.add(C)
          evictEntries: 3 > 2 -> poll() = A
            cache.remove("A", A)  -> 이미 없음, 무효
            markAsRemoved(A)      -> PENDING_REMOVAL -> REMOVED, 카운터 -1 -> 2
          루프 조건 2 > 2 거짓 -> 종료
    (2) RemovalTask(A).run()
          evictionQueue.remove(A) -> 이미 빠짐, 무효
          markAsRemoved(A)        -> REMOVED -> REMOVED, CAS 성공!, 카운터 -1 -> 1
                                                          ^^^^^^^^^^^^^^^^^^^^
                                                          이 한 줄이 결함이다
    결과: map 2 / 카운터 1  (어긋남 k = 1)

[수정 후]  같은 시나리오
    (2) RemovalTask(A).run()
          markAsRemoved(A) -> current.state == REMOVED -> return (감산 없음)
    결과: map 2 / 카운터 2  (일치)
```

**두 감산이 같은 `writeOperations.drain()` 호출 안에서 차례로 일어난다는 점**을 다시
강조해 둔다. `markAsRemoved`의 호출자 셋은 전부 `evictionLock` 아래에서만 실행되므로 -
`clear()`는 :185에서 직접 `lock()`하고, `AddTask`와 `RemovalTask`는 :143의 `tryLock`
안쪽에서 실행된다 - 두 호출이 시간상 겹칠 수 없다. 가드가 막는 것은 동시 진입이 아니라
**순차 이중 처리**다. 이 사실은 리뷰(F5)에서 교정된 것이고, 교정 전 우리 설명은
"동시 진입 시 CAS 승자만 감산"이었다.

그렇다고 CAS 루프가 장식인 것은 아니다. `markAsRemoved`가 상대하는 유일한 동시 전이는
락 **밖**에서 호출되는 `markForRemoval`(즉 `remove(K)`의 :238)의
`ACTIVE -> PENDING_REMOVAL`이다. 그 전이와 겹치면 CAS가 실패하고 루프가 재시도하는데,
가드가 CAS와 **같은 `current` 스냅샷**을 쓰므로 재시도에서 상태를 다시 읽어 판단이
갱신된다. check-then-act 원자성이 이 구조로 성립한다.

## 3. 카운터와 map이 갈라지는 방식 - 부호와 개수

이 결함의 핵심 산수는 "어긋남이 왜 스스로 줄지 않는가"이고, 그것은 `get(새 키)` 한
번이 두 값을 각각 얼마나 움직이는지로 결정된다. 어긋남이 k만큼 쌓인 상태
(`map = capacity + k`, `currentSize = capacity`)에서 출발해 한 번의 삽입을 추적한다.

| 단계 | 코드 | map | `currentSize` |
|---|---|---|---|
| 출발 | - | capacity + k | capacity |
| `put` | `cache.putIfAbsent` :119 | **+1** -> capacity+k+1 | 변화 없음 |
| `AddTask.run` | `lazySet(get() + 1)` :274 | - | **+1** -> capacity+1 |
| `evictEntries` 조건 | `capacity+1 > capacity` :282 | - | - |
| 축출 1회 | `cache.remove` :287 / `markAsRemoved` :288 | **-1** -> capacity+k | **-1** -> capacity |
| 조건 재확인 | `capacity > capacity` 거짓 | - | - |
| **합산** | | **순변화 0** | 순변화 0 |

**순변화가 0이라는 것이 이 결함의 최종 형태다.** 캐시는 매번 정확히 한 번씩 축출을
수행하고 있고 - 놀고 있는 것이 아니다 - 그런데 들어온 만큼만 나가므로 초과분 k는 단
하나도 줄지 않는다. 수천 번을 더 넣어도 같은 일이 반복된다. 그래서 "일시적 초과"가
아니라 "영구 초과"다.

수정 후에는 `currentSize == map`이므로 같은 계산이 이렇게 바뀐다.

```
출발:   map = 카운터 = capacity + k
put:    map = 카운터 = capacity + k + 1
evictEntries: capacity+k+1 > capacity 인 동안 반복 -> k+1 회
        map = 카운터 = capacity
```

**한 번의 `get(새 키)`으로 k+1회 축출이 일어나 즉시 수렴한다.** 이 대비가 그대로
테스트의 판별식이 됐다 - "유계 예산 안에서 capacity로 돌아오는가"([tests.md](tests.md)).

## 4. 조사 서사 - 없는 2차 결함을 고칠 뻔한 이야기

이 작업에서 가장 오래 걸린 구간은 결함을 찾은 다음이었다. 가드를 넣고 JUnit이 green이
됐는데도 독립 하네스에서 red가 남았고, 그 red의 정체를 확정하는 데 네 단계가 필요했다.
순서대로 적는다.

**(1) 잔여 red - 5/20.** 가드 적용 후 하네스를 다시 돌리자 20회 중 5회가 여전히
`size > capacity`로 끝났다. 처음 반응은 "2차 결함이 있다"였다.

**(2) 계측이 방향을 뒤집었다.** 리플렉션으로 `currentSize`를 읽어 보니 red 트라이얼에서
카운터는 `2`로 **정확한데** map이 46이었다. 즉 이번 초과는 카운터가 거짓말해서 생긴
것이 아니다. 우리가 고친 결함은 고쳐져 있었다.

**(3) 잘못된 가설과 실험 패치.** 그러면 무엇인가. "`evictEntries`가 이미 map에서 빠진
노드를 뽑아 축출 기회를 낭비한다"는 가설을 세웠다. 실제로 그런 낭비는 존재한다 -
`PENDING_REMOVAL` 노드를 poll하면 `cache.remove`가 무효라 map은 안 줄고 카운터만 준다.
그래서 "map에서 실제로 제거된 경우에만 카운터를 줄이자"는 실험 패치를 만들어 돌렸는데
**여전히 red**였고, 이번에는 카운터가 반대 방향으로(과소) 틀어졌다. 가설이 원인을
설명하지 못한다는 뜻이다.

**(4) 진짜 원인은 하네스였다.** quiesce 코드가 `cache.get(1)`을 열 번 부르는 것이었다.
그런데 키 1은 이미 캐시에 있을 수 있고, 있으면 그 호출은 **읽기**다. 읽기는
`processRead`를 타는데 그것은 읽기 버퍼에만 기록하고 `shouldDrainBuffers`가 참일 때만
드레인을 시도한다(:128-134). 즉 **읽기 히트는 쓰기 큐의 드레인을 보장하지 않는다.**
그래서 아직 실행되지 않은 `AddTask` 백로그가 남았고, 그 백로그에 든 노드들은 map에는
이미 있는데 카운터에는 아직 안 더해진 상태였다. 초과의 정체는 결함이 아니라 **측정
시점의 미완료 작업** - 측정 아티팩트였다.

**(5) 판별식 전환.** quiesce를 "매번 새 키를 넣어 쓰기를 유발한다"로 바꾸자 하네스가
결정적으로 갈렸다. 가드 단독으로 **0/30**, 같은 판별식에서 baseline은 **28/30**. 파라미터를
50k로 올리니 baseline이 15/15가 됐고, 최종형(수렴 quiesce + 유계 예산)으로는
**baseline 20/20 red / fix 0/20**이 나왔다.

**(6) 실험 패치는 불채택.** `evictEntries`의 낭비 축출은 실재하지만, 그것이 만드는 초과는
카운터가 정확한 한 **transient**다 - 완전 드레인 후에는 "계수된 노드 = 큐에 있는 노드"가
성립하고, 후속 삽입 압력으로 곧 수렴한다. 축출 순서 변경은 spec §4의 금지영역이기도
하다. 최소 diff 원칙에 따라 가드 단독으로 확정했다.

이 서사에서 남는 교훈은 하나다. **하네스도 검증 대상이다.** 도구를 의심하지 않으면
없는 결함을 고치게 되고, 실험 패치가 우연히 red를 없앴다면 그 잘못된 수정이 그대로
PR에 실렸을 것이다. 여기서 도구를 의심하게 만든 것은 "계측"이었다 - 카운터를 직접
읽어 본 순간 가설의 전제(카운터가 여전히 틀렸다)가 반증됐다.

## 5. 스프링 전역에서의 자리

`ConcurrentLruCache`는 `org.springframework.util`의 공개 클래스지만 javadoc이 "for
internal use in Spring Framework"라고 못 박은, **프레임워크 내부의 상한 있는 메모이제이션
도구**다. 파싱 결과처럼 만드는 비용이 큰 값을 키 하나당 한 번만 만들고 재사용하되,
무한히 쌓이지는 않게 하는 자리에 쓰인다.

```
[프레임워크 안에서 이 캐시를 쓰는 아홉 곳]

spring-core       MimeTypeUtils                    cachedMimeTypes (64)      :166
spring-context    ReloadableResourceBundleMessageSource  customLocaleProperties (64)  :128
spring-expression InternalSpelExpressionParser     patternCache              :103
                  OperatorMatches                  patternCache              :59
spring-jdbc       NamedParameterJdbcTemplate       parsedSqlCache (256)      :90
spring-r2dbc      NamedParameterExpander           parsedSqlCache            :48
spring-test       TestContextAnnotationUtils       cachedEnclosingConfigurationModes (32)  :85
spring-web        ExceptionHandlerMethodResolver   lookupCache (24)          :84

   전부 get(K) 만 호출한다.
   remove(K) 를 호출하는 프로덕션 코드: 0 곳
   clear() 를 호출하는 프로덕션 코드: 1 곳 (TestContextAnnotationUtils:413)
```

**이 목록이 "왜 아무도 보고하지 않았나"의 답이다.** 결함이 발화하려면 `remove(K)`가
축출과 겹쳐야 하는데, 프레임워크 자신은 이 캐시를 순수한 read-through 캐시로만 쓴다.
한 번 들어간 항목은 축출로만 나가고, 그 경로에서는 노드당 `markAsRemoved`가 한 번만
불린다. 즉 스프링 내부 사용만으로는 이 결함에 닿지 않는다.

닿을 수 있는 쪽은 이 공개 클래스를 직접 쓰면서 무효화가 필요한 외부 코드다. 캐시된
값이 원본 변경에 따라 낡을 수 있는 워크로드 - 설정 리로드, 테넌트별 무효화, 패턴 캐시
갱신 - 라면 `remove(K)`를 부르게 되고, 부하가 있는 상태라면 축출과 겹친다. 그리고 그
겹침의 결과는 예외가 아니라 "메모리를 예상보다 많이 쓰는 캐시"다.

`clear()`도 같은 모양의 이중 처리 경로를 갖고 있었다는 점은 따로 적어 둘 만하다.
`clear()`는 큐에서 노드를 뽑아 `markAsRemoved`한 뒤 `writeOperations.drainAll()`로 남은
작업을 전부 실행하는데(:188-193), 그 남은 작업에 방금 처리한 노드의 `RemovalTask`가
있으면 두 번째 감산이 일어난다. 게다가 `clear()`는 `currentSize`를 0으로 리셋하지 않고
이 산술에 전적으로 의존하므로 어긋남이 그대로 남는다 - "전부 비웠는데 카운터는 음수"
같은 상태가 가능하다. 같은 가드가 이 경로도 닫는다.

## 6. 관련 개념

이 무대의 배경 중 하나는 별도 문서로 정리돼 있으므로 링크로 연결한다.

- [동시성 버그 테스트의 경합 보장](../../concepts/race-condition-test-guarantees/race-condition-test-guarantees.md) -
  "경합을 보장한다"는 말이 실제로 보장해야 하는 것(결함 검출력), false green과 false
  red의 비용 비대칭, 보장 기법의 스펙트럼(반복 스트레스 + 누적 판별식 -> 진입 보장
  latch/barrier -> 종료 안전 join(timeout) + try/finally -> 창 확장 -> 결정론 주입 ->
  jcstress). 이 PR의 리뷰 지적 U1-R1에서 파생된 문서이고, 이 테스트의 before/after가
  그 안의 사례로 들어가 있다.
