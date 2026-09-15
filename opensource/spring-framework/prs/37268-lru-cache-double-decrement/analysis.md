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

`markAsRemoved`에 상태 가드가 없어, 같은 노드가 두 정리 경로를 차례로 지나면 `currentSize`가 두 번 감산된다.\
감산 어긋남은 자기수정되지 않고 누적되며, 그 뒤로 캐시는 "아직 여유가 있다"고 믿어 **capacity를 영구 초과**한 채 동작한다.\
예외도 로그도 없다.

> **착수 분석(analysis)** — 코드를 고치기 전에 실파일을 읽어 결함의 위치·경로·영향 범위를 확정해 두는 문서.\
> 예: 여기서 저장소 전체의 사용처 여덟 곳을 먼저 세어 뒀기 때문에 "왜 아무도 못 봤나"를 추정이 아니라 사실로 적을 수 있었다.

같은 파일 안에 정답이 있다는 점이 이 결함의 성격을 말해 준다.\
형제 메서드 `markForRemoval`(L243-254)은 `isActive()` 조기 반환 가드를 갖고 있고, 그쪽은 부작용조차 없다.\
**부작용이 없는 전이에 가드가 있고 부작용이 있는 전이에 없다** - 한 파일 안의 비대칭이고, 수정은 그 비대칭을 없애는 것이다(약 3줄).

> **가드(guard)** — 본문을 실행하기 전에 조건을 보고 그냥 돌아가 버리는 앞단 검사.\
> 예: `if (!current.isActive()) return;` 한 줄이 잘못된 상태의 노드를 본문에 들이지 않는다.

착수 전에 실행으로 재현했다.\
capacity=2인 캐시가 `size()=3`으로 고착했고, 방금 넣은 항목이 엉뚱하게 축출되는 부수 피해까지 관측됐다.

## 1. 무대 - 쓰기 버퍼와 세 개의 제거 경로

이 캐시는 경합을 피하려고 읽기/쓰기 작업을 버퍼에 쌓았다가 `evictionLock` 아래에서 드레인한다.\
그 설계가 클래스 서두에 한 줄로 적혀 있다 - "Read and write operations are internally recorded in dedicated buffers, then drained at chosen times to avoid contention"(L40-41).

> **드레인(drain)** — 버퍼에 쌓아 둔 작업을 한 스레드가 몰아서 꺼내 실행하는 일.\
> 예: 읽기·쓰기가 일어날 때마다 락을 잡는 대신, 큐에 적어 두었다가 한 번에 처리한다.

노드가 캐시에서 빠지는 길은 셋이다.

- **축출 경로**: `AddTask.run()`(L269-283)이 `currentSize`를 올린 뒤 `evictEntries()`를 부른다.\
  `currentSize > capacity`인 동안 `evictionQueue.poll()`한 노드를 `cache.remove` + `markAsRemoved`.
- **명시적 제거 경로**: `remove(K)`(공개 API)가 `cache.remove(key)`로 map에서 즉시 빼고 -> `markForRemoval`(ACTIVE -> PENDING_REMOVAL) -> `processWrite(new RemovalTask(node))`.\
  `RemovalTask.run()`(L293-306)은 나중에 `evictionQueue.remove(node)` + `markAsRemoved(node)`.
- **전체 비우기**: `clear()`(L184-197)도 큐를 비우며 각 노드에 `markAsRemoved`.\
  세 번째 진입점이다.

세 길이 어디서 만나는지 세로로 보면 이렇다.

```text
   축출 경로            명시적 제거 경로           전체 비우기
   AddTask              remove(K)                  clear()
      |                     |                          |
      |                map 에서 즉시 제거              |
      |                markForRemoval (PENDING)        |
      |                RemovalTask 를 큐에 적재        |
      |                     |                          |
      v                     v                          v
  evictEntries         RemovalTask.run            큐를 비우며
  큐 머리를 poll       (나중에 드레인 중)          하나씩 처리
      |                     |                          |
      +---------------------+--------------------------+
                            |
                            v
                    markAsRemoved(node)
                    <- 셋이 서로를 모른다
```

**둘째 경로가 map 조작은 즉시 끝내고 카운터 조정만 미룬다는 점**이 결함의 시간 창을 만든다.\
그 사이에 노드는 큐 안에 PENDING_REMOVAL로 남아 있고, 축출은 상태를 보지 않고 큐 머리부터 뽑는다.

> **시간 창(window)** — 두 사건 사이에 결함이 끼어들 수 있는 틈.\
> 예: map에서 빠진 순간부터 `RemovalTask`가 실행되는 순간까지가 이 결함의 창이다.

## 2. 핵심 이름표

이 파일을 처음 읽을 때 헷갈리는 지점이 "크기가 두 군데 있다"는 것이다.\
이름표를 먼저 고정해 두면 이후 추적이 단순해진다.

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

`Node`가 `AtomicReference`를 **상속**한다는 점은 처음 읽을 때 놓치기 쉽다.\
`node.get()`은 필드 조회가 아니라 원자 참조 읽기이고, `node.compareAndSet(...)`이 곧 상태 전이다.\
그래서 상태 기계 전체가 락 없이 CAS 하나로 돌아간다.

> **CAS(compare-and-set)** — "지금 값이 내가 본 그 값이면 새 값으로 바꿔라"를 한 번에 처리하는 원자 연산.\
> 예: 다른 스레드가 먼저 바꿔 버렸으면 실패하고, 실패하면 다시 읽어서 재시도한다.

노드 하나의 구조와 전이를 한 장으로 보면 이렇다.

```text
  Node<K,V> extends AtomicReference<CacheEntry<V>>
  +--------------------------------------------+
  | key                                        |
  | 원자 참조 -> CacheEntry(value, state)      |
  +--------------------------------------------+
                      |
              node.compareAndSet(old, new)
                      |
                      v
        상태가 ACTIVE -> PENDING_REMOVAL -> REMOVED 로 옮겨 간다
        (락 없이 CAS 하나로)
```

## 3. 결함 경로 단계 추적

capacity=2, 캐시에 A와 B다.\
다른 스레드가 `evictionLock`을 보유 중이다(실전에서는 그 스레드의 드레인이 진행 중인 상황).

| 단계 | 동작 | `currentSize` | map 실크기 |
|---|---|---|---|
| 1 | `get("C")` miss -> map에 C 투입, `AddTask(C)` 큐잉(락 경합으로 드레인 불가) | 2 | 3 (A,B,C) |
| 2 | `remove("A")` -> `cache.remove(A)`, `markForRemoval(A)`, `RemovalTask(A)` 큐잉 | 2 | 2 (B,C) |
| 3 | 락 해제 후 드레인: `AddTask(C)` - 카운터 3, `evictEntries`가 3 > 2를 보고 poll = A -> `cache.remove(A, A)` 무효 -> **`markAsRemoved(A)` 1차 감산** | 2 | 2 |
| 4 | 계속 `evictEntries`: 2 > 2 거짓 -> 종료. 다만 실측에서는 poll 순서에 따라 **C가 대신 축출**되기도 한다 | | |
| 5 | 같은 드레인에서 `RemovalTask(A)`: `evictionQueue.remove(A)` 무효 -> **`markAsRemoved(A)` 2차 감산** | **1** | 2 |
| 6 | 이후 `get("D")`, `get("E")` - 카운터가 실제보다 1 작아 축출이 덜 일어남 | 2 | **3 고착** |

착수 시점의 실측 출력은 이렇다.

```text
after drain: cache.size()=2, internal currentSize=1
after adding D and E: cache.size()=3 (capacity=2), internal currentSize=2
contains C=false
```

수정 전후의 최종 상태를 같은 시나리오로 나란히 놓으면 이렇다.

```text
        수정 전 (가드 없음)                    수정 후 (가드 있음)
+--------------------------------+     +--------------------------------+
| 드레인 직후                    |     | 드레인 직후                    |
|   size = 2, currentSize = 1    |     |   size = 2, currentSize = 2    |
+--------------------------------+     +--------------------------------+
| D, E 추가 후                   |     | D, E 추가 후                   |
|   size = 3 (capacity = 2)      |     |   size = 2                     |
|   currentSize = 2              |     |   currentSize = 2              |
|   contains C = false (오축출)  |     |   D / E 정상 축출              |
+--------------------------------+     +--------------------------------+
  최종 상태: capacity 초과 고착         최종 상태: capacity 유지
```

셋째 줄이 부수 피해다 - 방금 넣은 C가 엉뚱하게 축출됐다.\
`evictEntries`가 초과분을 정리하면서 큐 머리에 있던 C를 뽑았기 때문이다.

## 4. 왜 스스로 회복되지 않나

착수 시점에는 "드리프트가 누적된다"까지만 적었고, **왜 줄지 않는지**는 이해 게이트에서 수지 계산으로 확정됐다.\
그 계산이 이 결함의 최종 형태다.

> **드리프트(drift)** — 정답에서 조금씩 벗어난 오차가 쌓여 가는 현상.\
> 예: 경합 한 번에 카운터가 1씩 어긋나고, 그 어긋남이 되돌아오지 않으므로 계속 더해진다.

카운터가 map보다 k만큼 작게 어긋난 상태(`map = capacity + k`, `currentSize = capacity`)에서 새 키 하나를 넣으면 이렇게 된다.

| | map | `currentSize` |
|---|---|---|
| `put` | +1 | - |
| `AddTask.run` | - | +1 (`capacity+1`) |
| `evictEntries` (조건 `capacity+1 > capacity`, **1회만**) | -1 | -1 (`capacity`) |
| **순변화** | **0** | 0 |

**순변화가 0이므로 map은 `capacity + k`에 동결된다.**\
캐시가 축출을 안 하는 것이 아니라, 매번 정확히 한 번씩 축출을 하면서 제자리를 돈다.\
반면 수정 후에는 `currentSize == map`이므로 같은 삽입에서 `evictEntries`가 **k+1회** 돌아 즉시 수렴한다.

이 대비가 그대로 테스트 판별식이 됐다 - "수렴하는가"를 물으면 red와 green이 갈린다([tests.md](tests.md)).

> **수렴(convergence)** — 어긋난 값이 반복 동작을 거치며 정상 값으로 되돌아가는 것.\
> 예: 수정 후에는 삽입 한두 번이면 크기가 capacity로 돌아온다.

## 5. 계약과 기원

**계약.**\
클래스 javadoc은 "Simple LRU cache, **bounded by a specified cache capacity**"라고 선언한다(L33-34).\
그런데 `size()`가 map의 실크기를 반환하는 반면 축출은 `currentSize`를 기준으로 하므로, 두 값이 갈라지는 순간 "정상 상태에서 size <= capacity"라는 불변식이 조용히 깨진다.\
불변식을 **선언하는 자리**(javadoc)와 **집행하는 자리**(`evictEntries`의 루프 조건)가 서로 다른 값을 보고 있고, 둘을 맞춰 주는 검사는 없다.

> **불변식(invariant)** — 코드가 어떤 경로로 돌든 항상 참이어야 하는 문장.\
> 예: "정상 상태에서 크기는 capacity 이하다"가 이 캐시의 불변식이다.

선언과 집행이 서로 다른 값을 본다는 사실만 떼면 이렇다.

```text
      선언하는 자리                          집행하는 자리
+---------------------------+        +---------------------------+
| javadoc                   |        | evictEntries 의 루프 조건 |
| "bounded by a specified   |        | currentSize > capacity    |
|  cache capacity"          |        |                           |
+---------------------------+        +---------------------------+
   사용자가 보는 것: size()             축출이 보는 것: currentSize
   = map 의 실크기                      = 각 작업이 적어 준 숫자
              \                             /
               +--- 둘을 맞춰 주는 검사 없음 ---+
```

**기존 테스트.**\
`ConcurrentLruCacheTests`는 단일 스레드 시나리오 네 건뿐이었다.\
단일 스레드에서는 `processWrite`가 매번 `drainOperations()`를 직접 부르고 락 경합도 없으므로 쓰기 큐에 `[AddTask, RemovalTask]`가 나란히 쌓이는 상황이 만들어지지 않는다.\
즉 이 경로는 테스트로 고정된 적이 없다.\
또한 이 파일에는 리플렉션을 쓰는 선례가 없어, 결정론 재현을 커밋하기 어렵다는 제약이 착수 시점부터 있었다.

> **리플렉션(reflection)** — 실행 중에 클래스의 private 필드나 메서드에 이름으로 접근하는 자바 기능.\
> 예: `evictionLock`을 꺼내 미리 잡아 두면 드레인 시점을 마음대로 고정할 수 있다.

**기원.**\
이 클래스는 ben-manes의 `ConcurrentLinkedHashMap`을 단순화해 포팅한 것이다(javadoc L36-38이 그렇게 밝힌다).\
원본은 dead 엔트리의 weight를 0으로 만들어 두 번째 `makeDead`가 크기 합계에 영향을 주지 못하게 **자기방어**한다.\
즉 원본에는 "두 번 죽여도 안전하다"는 불변식이 자료구조 차원에 박혀 있었고, weight 개념을 버리고 단순 카운터로 포팅하는 과정에서 그 방어가 사라졌다.\
단순화가 불변식 하나를 함께 지워 버린 사례다.

원본과 포팅본이 같은 상황을 어떻게 다르게 막는지 나란히 보면 이렇다.

```text
   원본 ConcurrentLinkedHashMap          포팅본 ConcurrentLruCache
+------------------------------+     +------------------------------+
| 엔트리마다 weight 를 가진다  |     | 카운터 하나만 가진다         |
| 죽일 때 weight 를 0 으로     |     | 죽일 때 카운터를 1 깎는다    |
+------------------------------+     +------------------------------+
| 두 번째 makeDead:            |     | 두 번째 markAsRemoved:       |
|   0 을 빼므로 합계 불변      |     |   또 1 을 깎는다 (결함)      |
+------------------------------+     +------------------------------+
  자료구조가 스스로 방어한다           방어가 사라졌다
```

**이력.**\
파일 자체는 활성 상태다 - 최근에도 upstream이 null-safety 관련 폴리싱을 했다(`2588fb078e7`).\
즉 방치된 코드가 아니라 계속 손대는 코드인데도 이 비대칭은 남아 있었다.

## 6. 발화 조건 - 왜 아무도 못 봤나

착수 시점에는 "동시성 코드라 안 보였다"고만 적었는데, 문서화 단계에서 저장소를 전수로 훑어 더 정확한 답을 얻었다.\
**프레임워크 자신은 `remove(K)`를 부르지 않는다.**

> **전수 조사(exhaustive audit)** — 표본을 고르지 않고 해당하는 자리를 하나도 빼지 않고 전부 확인하는 것.\
> 예: 사용처 여덟 곳을 전부 열어 보고 `remove(K)` 호출이 0곳임을 세었다.

`ConcurrentLruCache`를 쓰는 프로덕션 코드는 여덟 곳이다(`MimeTypeUtils`, `NamedParameterJdbcTemplate`, SpEL 패턴 캐시 둘, `NamedParameterExpander`, `ReloadableResourceBundleMessageSource`, `TestContextAnnotationUtils`, `ExceptionHandlerMethodResolver`).\
그 여덟 곳은 전부 `get(K)`만 호출한다.\
`remove(K)` 호출은 0곳이고, `clear()` 호출은 `spring-test`의 한 줄뿐이다(`TestContextAnnotationUtils:413`).\
스프링 내부 사용만으로는 결함 경로에 닿지 않는다.

닿는 쪽은 이 공개 클래스를 직접 쓰면서 무효화가 필요한 외부 코드다.\
그리고 그런 코드에서도 증상은 예외가 아니라 "메모리를 예상보다 많이 쓰는 캐시"이므로, 원인을 감산 회수로 되짚는 사람은 없다.

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

1. **형제 관용구와 동형.**\
   `markForRemoval`의 조기 반환과 같은 형태이므로 이 파일을 읽는 사람에게 새로운 것이 없다.
2. **REMOVED가 종단 상태라는 사실.**\
   `REMOVED`에서 나가는 전이가 없으므로 - 유일하게 다른 전이를 만드는 `markForRemoval`이 `!isActive()`에서 즉시 반환한다 - 한 번 REMOVED가 된 노드의 모든 후속 방문이 가드에 걸린다.\
   노드당 감산 정확히 1회.\
   반대편에서 증분도 노드당 1회다(`put`의 `putIfAbsent`가 null을 반환할 때만 `AddTask`가 큐잉되므로, L119-122).\
   1:1로 짝이 맞는다.
3. **원자성이 CAS 루프로 성립.**\
   가드가 CAS와 같은 `current` 스냅샷을 쓰므로, 검사와 갱신 사이에 상태가 바뀌면 CAS가 실패하고 재시도가 상태를 다시 읽는다.

> **종단 상태(terminal state)** — 한 번 들어가면 빠져나오는 전이가 없는 상태.\
> 예: 노드가 REMOVED가 되면 다시 ACTIVE로 돌아가는 길이 없으므로, "이미 셌다"는 표시로 믿고 쓸 수 있다.

증분과 감산이 노드당 1:1 로 짝을 이루는 모습을 한 장으로 보면 이렇다.

```text
        노드 하나의 일생
  put (putIfAbsent 가 null 을 반환)
            |
            v
      AddTask 큐잉 1 회  ---->  카운터 +1  (정확히 1 회)
            |
            v
      ... 캐시에 머문다 ...
            |
            v
      markAsRemoved 첫 방문 ---->  카운터 -1  (정확히 1 회)
            |
            v
      markAsRemoved 이후 방문 ---> 가드에 걸려 아무 일도 없음
            |
            v
      currentSize == 계수된 노드 수
```

**`== REMOVED`이지 `!= ACTIVE`가 아니라는 점**이 이 가드의 유일한 함정이다.\
`markAsRemoved`는 PENDING_REMOVAL 노드를 정상 처리해야 하는 메서드이므로 - `remove(K)`가 만든 PENDING_REMOVAL을 `RemovalTask`가 확정하는 것이 정규 흐름이다 - `!isActive()`로 썼다면 감산이 통째로 빠져 카운터가 반대 방향으로 어긋난다.\
기존 테스트 `removeAndSize`가 그 실수를 즉시 잡는다.

### 7.2 검토했으나 기각한 대안

**대안 A - `evictEntries`가 실제 제거 여부를 확인하게 한다.**\
`cache.remove(key, node)`의 반환값을 보고 map에서 진짜로 빠졌을 때만 감산하자는 안이다.\
조사 도중 실험 패치까지 만들어 돌렸고 **기각**했다.\
이유가 둘인데, 첫째는 그것으로 red가 사라지지 않았다는 것이고(이번엔 카운터가 반대로 틀어졌다), 둘째는 그 낭비 축출이 만드는 초과가 카운터가 정확한 한 **transient**라는 것이다.\
완전 드레인 후에는 "계수된 노드 = 큐에 있는 노드"가 성립하고 후속 삽입 압력으로 수렴한다.\
축출 순서 변경은 명세의 금지영역이기도 하다.\
자세한 경위는 [structure.md](structure.md) 4절.

> **transient(일시적)** — 시간이 지나면 저절로 사라지는 상태.\
> 예: 드레인 전의 일시적 초과는 다음 쓰기에서 해소되므로 결함이 아니다.

**대안 B - `currentSize`와 map을 주기적으로 대조해 보정한다.**\
자기수복 코드를 넣는 안이다.\
기각.\
결함은 "카운터가 틀어질 수 있는 구조"가 아니라 "한 전이가 멱등이 아닌 것"이므로, 원인을 고치지 않고 증상을 닦는 셈이 된다.\
게다가 대조 자체가 락을 필요로 해서 이 클래스가 피하려던 경합을 되불러온다.

> **멱등(idempotent)** — 같은 호출을 여러 번 해도 결과가 한 번 한 것과 같은 성질.\
> 예: 가드가 붙은 뒤로는 `markAsRemoved`를 두 번 불러도 감산이 한 번만 일어난다.

**대안 C - `size()`/`capacity()` javadoc에 "드레인 전에는 일시적으로 초과할 수 있다"를 명시한다.**\
리뷰의 열린 질문으로 제기됐다.\
타당한 지적이지만 명세의 "부수 개선 금지"에 걸려 **범위 밖으로 유지**했다.\
별건으로 다룰 만하다.

세 대안이 각각 무엇을 건드리는지 나란히 두면 채택안만 범위가 좁다.

```text
  채택안   : markAsRemoved 세 줄    -> 원인을 고친다
  대안 A   : evictEntries 의 감산   -> red 가 안 사라졌고, 축출 순서는 금지영역
  대안 B   : 주기적 대조·보정        -> 증상만 닦고, 피하려던 락을 되불러온다
  대안 C   : javadoc 문구           -> 타당하나 이번 범위 밖
```

### 7.3 영향 범위와 검증 계획

동작이 바뀌는 경로는 "이미 REMOVED인 노드에 `markAsRemoved`가 다시 불리는 경우" 하나뿐이고, 그 경우의 기존 동작은 잘못된 감산이다.\
거기에 의존하는 코드는 상정할 수 없다.\
정상 경로 - ACTIVE 노드의 축출, PENDING_REMOVAL 노드의 확정 제거 - 는 가드를 그대로 통과하므로 정의상 무영향이며, 기존 테스트 네 건이 그 사실의 실행 증거가 된다.

검증 계획은 명세 §5로 네 항목을 고정했다.\
red 테스트, `:spring-core:test` 전체, checkstyle, 그리고 결정론 스모크 재실행이다.\
마지막 항목이 리뷰에서 "기록 없음"으로 걸려 다시 돌렸다(F4).

## 8. 착수 시점의 열린 결정과 그 해소

명세를 합의할 때 열려 있던 것이 하나, 실증이 필요했던 가정이 둘이었다.\
셋 다 구현 과정에서 해소됐고, 그 해소 방식이 이 작업의 성격을 보여 준다.

> **load-bearing 가정** — 그것이 참이어야 계획 전체가 성립하는, 아직 확인되지 않은 전제.\
> 예: "드리프트가 누적된다"가 거짓이었다면 스트레스 테스트 안 자체가 무너진다.

**열린 결정 - 테스트 방식.**\
결정론 재현은 `private evictionLock`을 리플렉션으로 잡아야 해서 upstream 테스트로는 이례적이다.\
두 안을 놓고 시작했다.

- **A안**: 2스레드 유계 스트레스.\
  드리프트가 누적되므로 수천 회 뒤 불변식을 단언한다.\
  **채택 조건을 미리 못 박았다** - "pre-fix 20회 반복이 전부 red인지 실측한 뒤 채택".
- **B안**: 리플렉션 결정론 테스트.\
  신뢰도는 완벽하나 스타일이 이례적이다.

두 안의 대가를 나란히 두면 이렇다.

```text
        A 안: 2 스레드 스트레스           B 안: 리플렉션 결정론
+------------------------------+     +------------------------------+
| 대상 내부에 결합하지 않는다  |     | private 필드에 결합한다      |
| upstream 스타일에 맞는다     |     | 이 파일에 선례가 없다        |
+------------------------------+     +------------------------------+
| 확률적 - red 신뢰도를        |     | 결정론 - 한 번이면 확정      |
| 실측으로 확보해야 한다       |     |                              |
+------------------------------+     +------------------------------+
  채택 (20/20 red 실측 후)            커밋하지 않는 스모크로 남김
```

A안을 독립 하네스로 실측하니 20/20 red가 나와 채택했고, B안은 커밋하지 않는 스모크로만 남겼다.\
**"조건부 채택"을 명세에 적어 둔 것이 여기서 값을 했다** - 실측이 나쁘게 나왔다면 B안으로 갈 근거가 이미 합의돼 있었다.

**가정 1 - 드리프트가 누적이므로 한 번의 경합만 잡아도 최종 단언이 실패한다.**\
이것이 A안 전체가 서 있는 전제였고, 따라서 착수 직후에 실증하기로 했다.\
20k 작업 후 size가 30~39까지 자란 것으로 해소됐다(경합이 한 번이 아니라 수십 번 났다는 뜻이기도 하다).

**가정 2 - `CacheEntry.state`가 테스트 없이 접근 가능한 형태인가.**\
수정 코드가 그 필드를 직접 읽으므로 record인지 확인이 필요했다.\
`private record CacheEntry<V>(V value, CacheEntryState state)`(L359)로 확인됐고, 바로 아래 줄의 기존 코드가 이미 `current.value`를 직접 읽고 있어 파일 관례와도 일치했다(리뷰가 이 점을 별도로 확인해 줬다).

> **record(레코드)** — 필드를 그대로 드러내는 불변 데이터 클래스를 짧게 선언하는 자바 문법.\
> 예: `record CacheEntry<V>(V value, CacheEntryState state)`는 `current.value`·`current.state`로 바로 읽을 수 있다.

## 9. 범위 밖

> **범위 밖(out of scope)** — 눈에 띄었지만 이번 변경에서 일부러 손대지 않기로 정한 것.\
> 예: 축출 순서가 함께 나아졌더라도, PR이 주장하는 범위는 size 불변식 하나로 좁혀 둔다.

- **`clear()`의 같은 모양 경합**은 이 가드로 함께 해소된다.\
  별도 수정 불필요.
- **축출 순서 이상**(방금 넣은 항목이 대신 나가는 것)도 이 수정의 부수 효과로 사라지지만, PR의 주장은 size 불변식에 한정했다.\
  명세 §4의 "부수 개선은 주장하지 않는다".
- **백포트 여부**는 메인테이너 트리아지 소관으로 두고 PR은 main을 대상으로 열었다.
- **`size()` javadoc의 일시적 초과 명시**는 위 7.2 대안 C 참조.

> **백포트(backport)** — 새 버전에서 고친 것을 옛 버전 브랜치에도 옮겨 넣는 일.\
> 예: main에 머지된 수정을 유지보수 중인 이전 릴리스 줄기에도 반영할지는 메인테이너가 정한다.
