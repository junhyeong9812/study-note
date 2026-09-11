# PR #37268 - 착수 분석: ConcurrentLruCache의 이중 size 감산

> 착수 시점(2026-09-10)에 작성한 분석을 학습용으로 다듬은 것이다. 기준
> upstream/main `572850bdcf1`. 결함 위치는
> `spring-core/src/main/java/org/springframework/util/ConcurrentLruCache.java`의
> `markAsRemoved`(수정 전 좌표 L203-212).
>
> 이 문서는 "무엇을 읽고 어떤 순서로 결함을 확정했는가"의 기록이므로, 완성된 해설인
> [README.md](README.md)와 겹치는 부분이 있다. 여기에만 있는 것은 **이름표 사전**(2절),
> **계약과 기원의 추적**(5절), **검토했으나 기각한 대안**(7.2절), 그리고 착수 시점에
> 열려 있던 결정과 그 해소 방식(8절)이다.

## 0. 결론 먼저

`markAsRemoved`에 상태 가드가 없어, 같은 노드가 두 정리 경로를 차례로 지나면
`currentSize`가 두 번 감산된다. 감산 어긋남은 자기수정되지 않고 누적되며, 그 뒤로
캐시는 "아직 여유가 있다"고 믿어 **capacity를 영구 초과**한 채 동작한다. 예외도 로그도
없다.

같은 파일 안에 정답이 있다는 점이 이 결함의 성격을 말해 준다. 형제 메서드
`markForRemoval`(L243-254)은 `isActive()` 조기 반환 가드를 갖고 있고, 그쪽은 부작용조차
없다. **부작용이 없는 전이에 가드가 있고 부작용이 있는 전이에 없다** - 한 파일 안의
비대칭이고, 수정은 그 비대칭을 없애는 것이다(약 3줄).

착수 전에 실행으로 재현했다. capacity=2인 캐시가 `size()=3`으로 고착했고, 방금 넣은
항목이 엉뚱하게 축출되는 부수 피해까지 관측됐다.

## 1. 무대 - 쓰기 버퍼와 세 개의 제거 경로

이 캐시는 경합을 피하려고 읽기/쓰기 작업을 버퍼에 쌓았다가 `evictionLock` 아래에서
드레인한다. 그 설계가 클래스 서두에 한 줄로 적혀 있다 - "Read and write operations are
internally recorded in dedicated buffers, then drained at chosen times to avoid
contention"(L40-41). 노드가 캐시에서 빠지는 길은 셋이다.

- **축출 경로**: `AddTask.run()`(L269-283)이 `currentSize`를 올린 뒤 `evictEntries()`를
  부른다. `currentSize > capacity`인 동안 `evictionQueue.poll()`한 노드를
  `cache.remove` + `markAsRemoved`.
- **명시적 제거 경로**: `remove(K)`(공개 API)가 `cache.remove(key)`로 map에서 즉시 빼고
  -> `markForRemoval`(ACTIVE -> PENDING_REMOVAL) -> `processWrite(new RemovalTask(node))`.
  `RemovalTask.run()`(L293-306)은 나중에 `evictionQueue.remove(node)` + `markAsRemoved(node)`.
- **전체 비우기**: `clear()`(L184-197)도 큐를 비우며 각 노드에 `markAsRemoved`. 세 번째
  진입점이다.

**둘째 경로가 map 조작은 즉시 끝내고 카운터 조정만 미룬다는 점**이 결함의 시간 창을
만든다. 그 사이에 노드는 큐 안에 PENDING_REMOVAL로 남아 있고, 축출은 상태를 보지 않고
큐 머리부터 뽑는다.

## 2. 핵심 이름표

이 파일을 처음 읽을 때 헷갈리는 지점이 "크기가 두 군데 있다"는 것이다. 이름표를 먼저
고정해 두면 이후 추적이 단순해진다.

| 이름 | 역할 | 결함과의 관계 |
|---|---|---|
| `currentSize` (`AtomicInteger`, L54) | 캐시가 **믿는** 크기. 축출 판단(`> capacity`)의 유일한 근거 | 이중 감산의 피해자. `private`이라 공개 API로는 관측 불가 |
| `this.cache` (`ConcurrentHashMap`, L56) | 실제로 들어 있는 엔트리. `size()`가 반환하는 값 | 피해가 드러나는 표면. 부푸는 쪽 |
| `markAsRemoved` (L203) | 노드를 REMOVED로 전이 + `currentSize` 감산 | **현재 상태를 검사하지 않음** - 이미 REMOVED여도 CAS가 성공하고 또 감산 |
| `markForRemoval` (L243) | ACTIVE -> PENDING_REMOVAL 전이 | `!current.isActive()`면 조기 반환. **가드가 "있는" 형제** |
| `CacheEntryState` (L353) | ACTIVE / PENDING_REMOVAL / REMOVED 3상태 | REMOVED -> REMOVED 재전이가 막혀 있지 않은 것이 본질 |
| `CacheEntry` (L359) | `record(value, state)` - 노드가 들고 있는 불변 스냅샷 | 상태의 단일 진리원. map이 아니다 |
| `Node` (L484) | `AtomicReference<CacheEntry<V>>`를 상속 | CAS 대상. 노드 자신이 원자 참조다 |
| `AddTask.evictEntries` (L277) | 초과분 축출 - poll한 노드를 `markAsRemoved` | PENDING_REMOVAL 노드도 poll될 수 있음(1차 감산) |
| `RemovalTask.run` (L293) | 큐에서 노드 제거 + `markAsRemoved` | 같은 노드에 2차 감산 |
| `evictionLock` (L64) | 드레인 직렬화 | 이 락이 경합 중일 때 쓰기 큐에 `[AddTask, RemovalTask]`가 쌓이는 것이 발화 조건 |
| `drainStatus` (L72) | IDLE / REQUIRED / PROCESSING | 읽기 경로가 드레인을 "시도할지" 정하는 힌트. 보장이 아니다 |

`Node`가 `AtomicReference`를 **상속**한다는 점은 처음 읽을 때 놓치기 쉽다.
`node.get()`은 필드 조회가 아니라 원자 참조 읽기이고, `node.compareAndSet(...)`이 곧
상태 전이다. 그래서 상태 기계 전체가 락 없이 CAS 하나로 돌아간다.

## 3. 결함 경로 단계 추적

capacity=2, 캐시에 A와 B. 다른 스레드가 `evictionLock`을 보유 중이다(실전에서는 그
스레드의 드레인이 진행 중인 상황).

| 단계 | 동작 | `currentSize` | map 실크기 |
|---|---|---|---|
| 1 | `get("C")` miss -> map에 C 투입, `AddTask(C)` 큐잉(락 경합으로 드레인 불가) | 2 | 3 (A,B,C) |
| 2 | `remove("A")` -> `cache.remove(A)`, `markForRemoval(A)`, `RemovalTask(A)` 큐잉 | 2 | 2 (B,C) |
| 3 | 락 해제 후 드레인: `AddTask(C)` - 카운터 3, `evictEntries`가 3 > 2를 보고 poll = A -> `cache.remove(A, A)` 무효 -> **`markAsRemoved(A)` 1차 감산** | 2 | 2 |
| 4 | 계속 `evictEntries`: 2 > 2 거짓 -> 종료. 다만 실측에서는 poll 순서에 따라 **C가 대신 축출**되기도 한다 | | |
| 5 | 같은 드레인에서 `RemovalTask(A)`: `evictionQueue.remove(A)` 무효 -> **`markAsRemoved(A)` 2차 감산** | **1** | 2 |
| 6 | 이후 `get("D")`, `get("E")` - 카운터가 실제보다 1 작아 축출이 덜 일어남 | 2 | **3 고착** |

착수 시점의 실측 출력은 이렇다.

```
after drain: cache.size()=2, internal currentSize=1
after adding D and E: cache.size()=3 (capacity=2), internal currentSize=2
contains C=false
```

셋째 줄이 부수 피해다 - 방금 넣은 C가 엉뚱하게 축출됐다. `evictEntries`가 초과분을
정리하면서 큐 머리에 있던 C를 뽑았기 때문이다.

## 4. 왜 스스로 회복되지 않나

착수 시점에는 "드리프트가 누적된다"까지만 적었고, **왜 줄지 않는지**는 이해 게이트에서
수지 계산으로 확정됐다. 그 계산이 이 결함의 최종 형태다.

카운터가 map보다 k만큼 작게 어긋난 상태(`map = capacity + k`, `currentSize = capacity`)
에서 새 키 하나를 넣으면 이렇게 된다.

| | map | `currentSize` |
|---|---|---|
| `put` | +1 | - |
| `AddTask.run` | - | +1 (`capacity+1`) |
| `evictEntries` (조건 `capacity+1 > capacity`, **1회만**) | -1 | -1 (`capacity`) |
| **순변화** | **0** | 0 |

**순변화가 0이므로 map은 `capacity + k`에 동결된다.** 캐시가 축출을 안 하는 것이
아니라, 매번 정확히 한 번씩 축출을 하면서 제자리를 돈다. 반면 수정 후에는
`currentSize == map`이므로 같은 삽입에서 `evictEntries`가 **k+1회** 돌아 즉시 수렴한다.

이 대비가 그대로 테스트 판별식이 됐다 - "수렴하는가"를 물으면 red와 green이 갈린다
([tests.md](tests.md)).

## 5. 계약과 기원

**계약.** 클래스 javadoc은 "Simple LRU cache, **bounded by a specified cache
capacity**"라고 선언한다(L33-34). 그런데 `size()`가 map의 실크기를 반환하는 반면 축출은
`currentSize`를 기준으로 하므로, 두 값이 갈라지는 순간 "정상 상태에서 size <= capacity"
라는 불변식이 조용히 깨진다. 불변식을 **선언하는 자리**(javadoc)와 **집행하는
자리**(`evictEntries`의 루프 조건)가 서로 다른 값을 보고 있고, 둘을 맞춰 주는 검사는
없다.

**기존 테스트.** `ConcurrentLruCacheTests`는 단일 스레드 시나리오 네 건뿐이었다. 단일
스레드에서는 `processWrite`가 매번 `drainOperations()`를 직접 부르고 락 경합도 없으므로
쓰기 큐에 `[AddTask, RemovalTask]`가 나란히 쌓이는 상황이 만들어지지 않는다. 즉 이
경로는 테스트로 고정된 적이 없다. 또한 이 파일에는 리플렉션을 쓰는 선례가 없어, 결정론
재현을 커밋하기 어렵다는 제약이 착수 시점부터 있었다.

**기원.** 이 클래스는 ben-manes의 `ConcurrentLinkedHashMap`을 단순화해 포팅한 것이다
(javadoc L36-38이 그렇게 밝힌다). 원본은 dead 엔트리의 weight를 0으로 만들어 두 번째
`makeDead`가 크기 합계에 영향을 주지 못하게 **자기방어**한다. 즉 원본에는 "두 번 죽여도
안전하다"는 불변식이 자료구조 차원에 박혀 있었고, weight 개념을 버리고 단순 카운터로
포팅하는 과정에서 그 방어가 사라졌다. 단순화가 불변식 하나를 함께 지워 버린 사례다.

**이력.** 파일 자체는 활성 상태다 - 최근에도 upstream이 null-safety 관련 폴리싱을 했다
(`2588fb078e7`). 즉 방치된 코드가 아니라 계속 손대는 코드인데도 이 비대칭은 남아
있었다.

## 6. 발화 조건 - 왜 아무도 못 봤나

착수 시점에는 "동시성 코드라 안 보였다"고만 적었는데, 문서화 단계에서 저장소를 전수로
훑어 더 정확한 답을 얻었다. **프레임워크 자신은 `remove(K)`를 부르지 않는다.**

`ConcurrentLruCache`를 쓰는 프로덕션 코드는 여덟 곳이고(`MimeTypeUtils`,
`NamedParameterJdbcTemplate`, SpEL 패턴 캐시 둘, `NamedParameterExpander`,
`ReloadableResourceBundleMessageSource`, `TestContextAnnotationUtils`,
`ExceptionHandlerMethodResolver`), 그 여덟 곳은 전부 `get(K)`만 호출한다. `remove(K)`
호출은 0곳이고, `clear()` 호출은 `spring-test`의 한 줄뿐이다
(`TestContextAnnotationUtils:413`). 스프링 내부 사용만으로는 결함 경로에 닿지 않는다.

닿는 쪽은 이 공개 클래스를 직접 쓰면서 무효화가 필요한 외부 코드다. 그리고 그런
코드에서도 증상은 예외가 아니라 "메모리를 예상보다 많이 쓰는 캐시"이므로, 원인을
감산 회수로 되짚는 사람은 없다.

## 7. 수정안

### 7.1 채택안 - 종단 상태 가드

```java
private void markAsRemoved(Node<K, V> node) {
	for (; ; ) {
		CacheEntry<V> current = node.get();
		if (current.state == CacheEntryState.REMOVED) {   // 이미 제거된 노드 - 감산 금지
			return;
		}
		CacheEntry<V> removed = new CacheEntry<>(current.value, CacheEntryState.REMOVED);
		if (node.compareAndSet(current, removed)) {
			this.currentSize.lazySet(this.currentSize.get() - 1);
			return;
		}
	}
}
```

정당화는 세 겹이다.

1. **형제 관용구와 동형.** `markForRemoval`의 조기 반환과 같은 형태이므로 이 파일을
   읽는 사람에게 새로운 것이 없다.
2. **REMOVED가 종단 상태라는 사실.** `REMOVED`에서 나가는 전이가 없으므로 - 유일하게
   다른 전이를 만드는 `markForRemoval`이 `!isActive()`에서 즉시 반환한다 - 한 번
   REMOVED가 된 노드의 모든 후속 방문이 가드에 걸린다. 노드당 감산 정확히 1회.
   반대편에서 증분도 노드당 1회다(`put`의 `putIfAbsent`가 null을 반환할 때만 `AddTask`가
   큐잉되므로, L119-122). 1:1로 짝이 맞는다.
3. **원자성이 CAS 루프로 성립.** 가드가 CAS와 같은 `current` 스냅샷을 쓰므로,
   검사와 갱신 사이에 상태가 바뀌면 CAS가 실패하고 재시도가 상태를 다시 읽는다.

**`== REMOVED`이지 `!= ACTIVE`가 아니라는 점**이 이 가드의 유일한 함정이다.
`markAsRemoved`는 PENDING_REMOVAL 노드를 정상 처리해야 하는 메서드이므로 -
`remove(K)`가 만든 PENDING_REMOVAL을 `RemovalTask`가 확정하는 것이 정규 흐름이다 -
`!isActive()`로 썼다면 감산이 통째로 빠져 카운터가 반대 방향으로 어긋난다. 기존 테스트
`removeAndSize`가 그 실수를 즉시 잡는다.

### 7.2 검토했으나 기각한 대안

**대안 A - `evictEntries`가 실제 제거 여부를 확인하게 한다.** `cache.remove(key, node)`의
반환값을 보고 map에서 진짜로 빠졌을 때만 감산하자는 안이다. 조사 도중 실험 패치까지
만들어 돌렸고 **기각**했다. 이유가 둘인데, 첫째는 그것으로 red가 사라지지 않았다는
것이고(이번엔 카운터가 반대로 틀어졌다), 둘째는 그 낭비 축출이 만드는 초과가 카운터가
정확한 한 **transient**라는 것이다 - 완전 드레인 후에는 "계수된 노드 = 큐에 있는 노드"가
성립하고 후속 삽입 압력으로 수렴한다. 축출 순서 변경은 명세의 금지영역이기도 하다.
자세한 경위는 [structure.md](structure.md) 4절.

**대안 B - `currentSize`와 map을 주기적으로 대조해 보정한다.** 자기수복 코드를 넣는
안이다. 기각. 결함은 "카운터가 틀어질 수 있는 구조"가 아니라 "한 전이가 멱등이 아닌
것"이므로, 원인을 고치지 않고 증상을 닦는 셈이 된다. 게다가 대조 자체가 락을 필요로
해서 이 클래스가 피하려던 경합을 되불러온다.

**대안 C - `size()`/`capacity()` javadoc에 "드레인 전에는 일시적으로 초과할 수 있다"를
명시한다.** 리뷰의 열린 질문으로 제기됐다. 타당한 지적이지만 명세의 "부수 개선 금지"에
걸려 **범위 밖으로 유지**했다. 별건으로 다룰 만하다.

### 7.3 영향 범위와 검증 계획

동작이 바뀌는 경로는 "이미 REMOVED인 노드에 `markAsRemoved`가 다시 불리는 경우"
하나뿐이고, 그 경우의 기존 동작은 잘못된 감산이다. 거기에 의존하는 코드는 상정할 수
없다. 정상 경로 - ACTIVE 노드의 축출, PENDING_REMOVAL 노드의 확정 제거 - 는 가드를
그대로 통과하므로 정의상 무영향이며, 기존 테스트 네 건이 그 사실의 실행 증거가 된다.

검증 계획은 명세 §5로 네 항목을 고정했다: red 테스트, `:spring-core:test` 전체,
checkstyle, 그리고 결정론 스모크 재실행. 마지막 항목이 리뷰에서 "기록 없음"으로 걸려
다시 돌렸다(F4).

## 8. 착수 시점의 열린 결정과 그 해소

명세를 합의할 때 열려 있던 것이 하나, 실증이 필요했던 가정이 둘이었다. 셋 다 구현
과정에서 해소됐고, 그 해소 방식이 이 작업의 성격을 보여 준다.

**열린 결정 - 테스트 방식.** 결정론 재현은 `private evictionLock`을 리플렉션으로
잡아야 해서 upstream 테스트로는 이례적이다. 두 안을 놓고 시작했다.

- **A안**: 2스레드 유계 스트레스. 드리프트가 누적되므로 수천 회 뒤 불변식을 단언한다.
  **채택 조건을 미리 못 박았다** - "pre-fix 20회 반복이 전부 red인지 실측한 뒤 채택".
- **B안**: 리플렉션 결정론 테스트. 신뢰도는 완벽하나 스타일이 이례적이다.

A안을 독립 하네스로 실측하니 20/20 red가 나와 채택했고, B안은 커밋하지 않는 스모크로만
남겼다. **"조건부 채택"을 명세에 적어 둔 것이 여기서 값을 했다** - 실측이 나쁘게 나왔다면
B안으로 갈 근거가 이미 합의돼 있었다.

**가정 1 - 드리프트가 누적이므로 한 번의 경합만 잡아도 최종 단언이 실패한다.** 이것이
A안 전체가 서 있는 전제였고, 따라서 착수 직후에 실증하기로 했다. 20k 작업 후 size가
30~39까지 자란 것으로 해소됐다(경합이 한 번이 아니라 수십 번 났다는 뜻이기도 하다).

**가정 2 - `CacheEntry.state`가 테스트 없이 접근 가능한 형태인가.** 수정 코드가 그
필드를 직접 읽으므로 record인지 확인이 필요했다. `private record CacheEntry<V>(V value,
CacheEntryState state)`(L359)로 확인됐고, 바로 아래 줄의 기존 코드가 이미 `current.value`를
직접 읽고 있어 파일 관례와도 일치했다(리뷰가 이 점을 별도로 확인해 줬다).

## 9. 범위 밖

- **`clear()`의 같은 모양 경합**은 이 가드로 함께 해소된다. 별도 수정 불필요.
- **축출 순서 이상**(방금 넣은 항목이 대신 나가는 것)도 이 수정의 부수 효과로 사라지지만,
  PR의 주장은 size 불변식에 한정했다. 명세 §4의 "부수 개선은 주장하지 않는다".
- **백포트 여부**는 메인테이너 트리아지 소관으로 두고 PR은 main을 대상으로 열었다.
- **`size()` javadoc의 일시적 초과 명시**는 위 7.2 대안 C 참조.
