# PR #37268 - 테스트 해설 (테스트 하나하나)

> `ConcurrentLruCacheTests`에 추가된 1건 + 같은 파일의 기존 4건이 맡은 가드 역할.
> 각 테스트를 "무엇을 주장하나 / 왜 red 또는 가드인가 / 단언 하나하나의 의미"로
> 해설한다. 이 PR의 테스트는 동시성 테스트라 **단언보다 배치와 종료 처리가 더 많은
> 것을 결정하므로**, 그 부분에 지면을 더 썼다. 배경 개념은
> [동시성 버그 테스트의 경합 보장](../../concepts/race-condition-test-guarantees/race-condition-test-guarantees.md).

배치 전체를 먼저 본다.\
이 결함은 **두 스레드가 같은 노드를 서로 다른 경로로 정리할 때만** 발화한다.\
그래서 새 테스트 하나가 그 경합 전부를 맡고 기존 넷은 "단일 스레드에서의 정상 동작이 그대로인가"를 맡는 구도가 된다.\
두 축으로 줄 세우면 이렇다.

> **red 테스트 / 가드 테스트** — red는 수정 전에 반드시 실패해야 하는 테스트, 가드는 수정 전후 모두 통과해야 하는 테스트.\
> 예: red 가 없으면 결함을 겨냥하지 못한 것이고, 가드가 깨지면 기존 동작을 망가뜨린 것이다.

| | 제거 경로가 하나뿐 | 제거 경로가 둘이 겹침 |
|---|---|---|
| 단일 스레드 | T2 `getAndSize`(축출) / T3 `removeAndSize`(명시적 제거) / T4 `clearAndSize` - 가드 | (구조적으로 불가) |
| 두 스레드 | - | **T5 `removeRacingWithEvictionDoesNotExceedCapacity` - red** |

같은 배치를 fix 전후 결과까지 넣은 격자로 보면 각 칸이 무엇을 덮는지가 드러난다.

```text
                          |  fix 전  |  fix 후  |  덮는 것
--------------------------+----------+----------+--------------------------
T5 경합 (두 스레드)       |  FAIL    |  PASS    |  수정이 결함을 고쳤나
   size=38 > capacity=2   |          |          |
--------------------------+----------+----------+--------------------------
T1 zeroCapacity           |  PASS    |  PASS    |  가드 경로에 닿지 않음
T2 getAndSize (축출)      |  PASS    |  PASS    |  축출이 여전히 감산하나
T3 removeAndSize (제거)   |  PASS    |  PASS    |  제거가 여전히 감산하나
T4 clearAndSize (비우기)  |  PASS    |  PASS    |  clear 도 여전히 감산하나
```

-> 오른쪽 세 줄이 중요한 이유는, 새 가드가 "감산을 건너뛰는" 코드라서 잘못 쓰면 반대 방향으로 깨질 수 있기 때문이다.

오른쪽 아래 칸이 비어 있었던 것이 이 결함이 4년 넘게 살아남은 이유다.\
기존 넷은 전부 왼쪽 열에 있고, 왼쪽 열에서는 쓰기 큐가 매 호출마다 즉시 드레인되므로 `[AddTask, RemovalTask]`가 나란히 쌓이는 상황 자체가 만들어지지 않는다.

## T5. `removeRacingWithEvictionDoesNotExceedCapacity` - red

새로 추가한 유일한 테스트다.\
전문은 이렇다.

```java
@Test
void removeRacingWithEvictionDoesNotExceedCapacity() throws Exception {
	ConcurrentLruCache<Integer, String> cache = new ConcurrentLruCache<>(2, key -> "value" + key);
	AtomicBoolean stop = new AtomicBoolean();
	AtomicInteger removals = new AtomicInteger();
	AtomicReference<Throwable> failure = new AtomicReference<>();
	Thread remover = new Thread(() -> {
		try {
			while (!stop.get()) {
				cache.get(0);
				if (cache.remove(0)) {
					removals.incrementAndGet();
				}
			}
		}
		catch (Throwable ex) {
			failure.set(ex);
		}
	});
	remover.start();
	try {
		for (int i = 1; i <= 50_000; i++) {
			cache.get(i);
		}
	}
	finally {
		stop.set(true);
		remover.join(5000);
	}
	int budget = 50_000;
	int key = 100_000;
	while (cache.size() > cache.capacity() && budget-- > 0) {
		cache.get(key++);
	}

	assertThat(remover.isAlive()).isFalse();
	assertThat(failure.get()).isNull();
	assertThat(removals.get()).isGreaterThan(0);
	assertThat(cache.size()).isLessThanOrEqualTo(cache.capacity());
}
```
(ConcurrentLruCacheTests.java:115-154)

이 테스트가 주장하는 것과 수정 전에 red가 되는 이유를 먼저 두 줄로 적어 둔다.

- **주장**: 명시적 제거와 축출이 겹쳐 돌아간 뒤, 남은 쓰기 작업을 전부 드레인하면 캐시는 capacity로 돌아온다.
- **fix 전 red인 이유**: 겹침이 한 번이라도 나면 `currentSize`가 map보다 작아지고, 그 어긋남은 [README 3절](README.md)의 수지 계산대로 순변화 0으로 동결된다.\
  예산 50,000회를 다 써도 `size()`가 capacity 아래로 내려오지 않는다.\
  실측 red는 `size=38 > capacity=2`, 예산 소진.

테스트가 네 국면으로 나뉜다는 것을 먼저 보면 이후 설명이 붙을 자리가 생긴다.

```text
  [1] 무대 만들기
      capacity 2 캐시 + remover 스레드 기동
              |
              v
  [2] 경합 유발
      메인: get(1) ~ get(50_000)   (매번 새 키 -> 축출 유발)
      remover: get(0) + remove(0) 반복  (RemovalTask 계속 큐잉)
              |
              v
  [3] 수렴 quiesce
      stop + join(5000)
      새 키로 쓰기를 유발하며 size 가 capacity 로 돌아오길 기다린다 (예산 50k)
              |
              v
  [4] 단언 4 개
      isAlive false / failure null / removals > 0 / size <= capacity
```

### 무대 만들기 - 두 스레드가 각각 무엇을 담당하나

이 테스트의 절반은 단언이 아니라 **결함 경로를 실제로 밟게 만드는 배치**다.\
두 스레드가 서로 다른 재료를 공급한다.

| 스레드 | 하는 일 | 만들어 내는 것 |
|---|---|---|
| 메인 | `get(1)`부터 `get(50_000)`까지 전부 새 키 | 매번 miss -> `put` -> `AddTask` 큐잉 -> 드레인 시 `evictEntries()` 발동 |
| remover | `get(0)` 다음 `remove(0)`을 무한 반복 | 노드 0을 살렸다 죽였다 하며 `RemovalTask(0)`를 계속 큐잉 |

**capacity를 2로 잡은 것이 재료 배합의 핵심이다.**\
캐시가 작을수록 축출이 매 삽입마다 일어나므로 `evictEntries()`가 큐 머리를 뽑는 빈도가 최대가 되고, 큐 머리에 노드 0이 놓일 확률도 높아진다.\
반대로 capacity가 크면 축출이 드물어 겹칠 기회가 줄어든다.

**`get(0)`이 `remove(0)` 앞에 있는 이유**는 재료 자체가 사라지지 않게 하기 위해서다.\
`remove(K)`의 첫 줄이 그 이유를 그대로 보여 준다.

```java
public boolean remove(K key) {
	Node<K, V> node = this.cache.remove(key);
	if (node == null) {
		return false;                     // 이미 없는 키면 여기서 끝
	}
	markForRemoval(node);
	processWrite(new RemovalTask(node));
	return true;
}
```
(ConcurrentLruCache.java:233-241)

`get(0)`이 있을 때와 없을 때 remover 가 무엇을 생산하는지 나란히 보면 이렇다.

```text
   remove(0) 만 반복                    get(0) + remove(0) 반복
+---------------------------+       +---------------------------+
| 1 회차: 노드 있음         |       | 매 회차: get(0) 이 노드를 |
|   -> RemovalTask 큐잉     |       |          다시 넣는다      |
| 2 회차 이후: node == null |       |   -> remove 가 유효       |
|   -> 조기 반환, 큐잉 없음 |       |   -> RemovalTask 계속 큐잉|
+---------------------------+       +---------------------------+
  경합 재료가 1 회로 끝난다            경합 재료가 계속 공급된다
```

`remove(0)`만 연속으로 돌리면 두 번째 호출부터는 `node == null`에서 조기 반환하고, `markForRemoval`도 `RemovalTask` 큐잉도 일어나지 않는다.\
즉 경합 재료가 아예 생산되지 않는다.\
`get(0)`이 매 사이클 노드를 다시 넣어 줘야 `remove`가 유효해진다.\
이 쌍이 이 테스트에서 유일하게 "왜 이렇게 썼는지 안 보이는" 줄이었고, 실제로 이해 게이트의 질문 하나가 정확히 이 지점이었다([gates.md](gates.md) G1-Q2).

### 수렴 quiesce - 이 테스트에서 가장 중요한 열 줄

경합을 일으키는 것보다 어려운 것이 **언제 단언할 것인가**였다.\
이 캐시는 드레인 전에 일시적으로 capacity를 넘는 것이 정상이므로, 스레드를 세운 직후에 `size() <= capacity()`를 단언하면 정상 동작도 red가 된다.\
그래서 마지막 준비 단계가 필요하다.

> **quiesce(정지 대기)** — 측정하기 전에 진행 중인 작업이 전부 끝나기를 기다려 상태를 안정시키는 일.\
> 예: 쓰기 버퍼가 아직 드레인되지 않았는데 크기를 재면, 결함이 아닌 것도 결함처럼 보인다.

```java
int budget = 50_000;
int key = 100_000;
while (cache.size() > cache.capacity() && budget-- > 0) {
	cache.get(key++);
}
```

이 네 줄에 든 선택 셋이 각각 다른 실패를 막는다.

- **`key++`로 매번 새 키를 쓰는 이유**: 이미 있는 키를 `get`하면 그것은 **읽기**이고, 읽기는 읽기 버퍼에만 기록될 뿐 쓰기 큐의 드레인을 보장하지 않는다(`processRead`, :128-134).\
  새 키여야 miss -> `put` -> `processWrite`가 되고, `processWrite`는 `drainStatus`를 REQUIRED로 세운 뒤 `drainOperations()`를 직접 부른다(:136-140).\
  즉 **새 키만이 백로그를 밀어낸다.**
- **`budget`으로 유계인 이유**: 무한 루프면 fix 전 실행이 영원히 끝나지 않는다.\
  예산이 소진되면 루프를 빠져나와 마지막 단언에서 red가 되게 했다.
- **`100_000`에서 시작하는 이유**: 메인 루프가 쓴 1~50,000과 겹치지 않게 하기 위해서다.\
  겹치면 그 `get`이 히트가 되어 쓰기를 유발하지 못한다.

세 선택이 각각 어떤 실패를 막는지 격자로 두면 이렇다.

```text
  선택              |  빼면 생기는 일
--------------------+---------------------------------------------
  key++ (새 키)     |  읽기 히트가 되어 쓰기 큐가 안 비워진다
                    |  -> 정상 동작도 red (측정 아티팩트)
--------------------+---------------------------------------------
  budget (유계)     |  fix 전 실행이 영원히 안 끝난다
                    |  -> CI 가 멈춘다
--------------------+---------------------------------------------
  100_000 부터      |  메인 루프의 1~50,000 과 겹쳐 히트가 된다
                    |  -> 첫 줄과 같은 실패
```

**이 루프의 형태가 곧 판별식이다.**\
"수렴하는가"를 묻고 있고, 수정 전과 후의 차이가 정확히 수렴 여부이므로 red와 green이 갈린다.\
이 판별식에 도달하기까지 잘못된 quiesce로 헤맨 과정은 [structure.md](structure.md) 4절에 있다.

> **판별식(predicate)** — 참인지 거짓인지로 결과를 가르는 조건식.\
> 예: 여기서는 "정해진 예산 안에 size가 capacity로 돌아오는가"가 통과·실패를 가른다.

### 네 단언이 각각 막는 것

단언은 넷인데, 결함을 보는 것은 마지막 하나뿐이고 앞의 셋은 전부 **이 테스트가 거짓으로 통과하는 경로**를 막는다.\
그 구도를 표로 두면 이렇다.

| 단언 | 막는 실패 모드 | 없으면 어떻게 되나 |
|---|---|---|
| `remover.isAlive()).isFalse()` | 워커가 종료되지 않았는데 통과 | `join(5000)`은 타임아웃돼도 조용히 반환한다 - 행에 걸린 스핀 스레드가 남은 채로 통과하고, 스위트 내내 CPU와 `evictionLock`을 물고 돈다 |
| `failure.get()).isNull()` | 워커가 예외로 죽었는데 통과 | 스레드 안의 uncaught 예외는 stderr 한 줄만 남기고 사라진다 - 경합 0회 실행이 정상 green과 구분 불가 |
| `removals.get()).isGreaterThan(0)` | 워커가 살아 있었으나 일을 못 했는데 통과 | remover가 스케줄되지 못하거나 `remove`가 계속 `false`를 반환해도 최종 단언은 당연히 통과 |
| `cache.size()).isLessThanOrEqualTo(cache.capacity())` | (이것이 결함을 보는 단언) | - |

같은 넷을 "무엇을 확인하는 층인가"로 세로로 쌓으면 이렇다.

```text
  [층 4] 결함을 본다
         size <= capacity
              ^
              |  아래 셋이 전부 통과해야 이 단언에 의미가 생긴다
              |
  [층 3] 워커가 실제로 일했나        removals > 0
              ^
  [층 2] 워커가 예외로 죽지 않았나   failure == null
              ^
  [층 1] 워커가 정말 끝났나          isAlive() == false
```

-> 아래 세 층은 결함이 아니라 "이 테스트 자체가 거짓말하지 않는가"를 본다.

> **위장 green(false green)** — 실제로는 아무것도 검증하지 못했는데 통과로 보이는 테스트 결과.\
> 예: 경합 상대 스레드가 한 번도 안 돌았다면, 그 테스트의 통과는 "결함이 없다"의 증거가 아니다.

앞의 셋은 전부 **위장 green** 차단이다.\
동시성 테스트에서 이 셋이 없으면 "테스트가 있다"는 사실만 남고 검출력은 0이 될 수 있는데, 그 0이 정상 green과 겉모습이 같아 아무도 모른다.\
셋 다 리뷰에서 지적받아 추가됐다(F2 = U1-R1로 둘째와 셋째, N1으로 첫째 - [README 6절](README.md)).

`isAlive()` 단언이 왜 `join(5000)`과 한 쌍인지는 따로 적어 둘 만하다.\
원래 코드는 무제한 `join()`이었고, 리뷰가 "테스트가 실패하면 영원히 매달린다"고 지적해 `join(5000)`으로 바꿨다.\
그런데 `Thread.join(millis)`는 **타임아웃 시 예외를 던지지 않고 조용히 반환한다.**\
그래서 `join(5000)` 자체는 "최대 5초 기다렸다"만 보증할 뿐 종료를 전혀 보증하지 못한다.\
`isAlive()` 단언이 그 빈틈을 메워 "join이 대기만 한 것이 아니라 실제 종료로 반환했다"를 확인한다.\
순서도 의미가 있다 - 이 단언이 `failure.get()` 읽기보다 앞에 오므로, `join`의 happens-before를 타고 워커가 완전히 종료한 뒤 기록된 값을 읽는 것이 보장된다.

> **happens-before** — 한 스레드에서 일어난 쓰기가 다른 스레드에서 확실히 보이도록 자바 메모리 모델이 정해 둔 순서 관계.\
> 예: `join()`이 정상 반환하면, 그 스레드가 쓴 값들은 기다린 쪽에서 반드시 보인다.

### 왜 latch로 진입을 강제하지 않았나

리뷰(U1-R1)가 제안한 것 중 하나가 `CountDownLatch`나 `CyclicBarrier`로 두 스레드의 진입을 맞추는 것이었다.\
채택하지 않았고, 그 대신 `removals > 0` 관측 단언을 넣었다.\
이유는 latch가 보장하는 것과 이 테스트가 필요로 하는 것이 다르기 때문이다.

> **latch / barrier** — 여러 스레드가 같은 지점에서 만나 함께 출발하도록 맞추는 동기화 도구.\
> 예: `CountDownLatch`로 두 스레드를 세워 뒀다가 동시에 풀면 "같은 시점에 출발했다"까지는 보장된다.

latch는 "두 스레드가 같은 시점에 출발했다"를 보장하지만, 이 결함이 요구하는 것은 **특정 인터리빙**(축출이 poll한 노드가 하필 방금 remove된 그 노드)이고 그것은 latch로 만들어지지 않는다.\
반면 `removals > 0`은 "워커가 실제로 제거를 성공시켰다"를 사후 관측으로 확정한다 - 보장의 종류가 더 약하지만 이 테스트가 실제로 필요로 하는 축이다.

보장의 종류를 나란히 놓으면 이렇다.

```text
        latch 가 주는 것                  removals > 0 이 주는 것
+-----------------------------+     +-----------------------------+
| 두 스레드가 같은 시점에     |     | 워커가 실제로 제거를        |
| 출발했다                    |     | 성공시켰다 (사후 관측)      |
+-----------------------------+     +-----------------------------+
| 주지 않는 것:               |     | 주지 않는 것:               |
| 축출이 poll 한 노드이 하필  |     | 같은 노드에서 겹쳤다는      |
| 그 노드였다는 보장          |     | 보장 (N2 가 짚은 한계)      |
+-----------------------------+     +-----------------------------+
```

리뷰의 post-fix 지적 N2가 이 한계를 정확히 짚었다 - `removals > 0`은 제거 성공만 증명하지 같은 노드에서의 경합을 증명하지 않는다.\
공개 API로는 그 이상을 증명할 수 없으므로 **부분 수용**으로 처리하고, 한계를 PR 본문에 직접 적었다("a single interleaving cannot be forced through the public API").\
결정론을 원하면 리플렉션으로 `evictionLock`을 선점해야 하는데(아래 스모크가 그 방식이다), upstream 테스트 스타일이 아니라 커밋하지 않았다.

## T1~T4. 기존 테스트 4건 - 무회귀 가드 (전후 green)

새 테스트가 경합 경로를 맡는 동안, 나머지 경로가 그대로임을 고정하는 쪽은 이미 있던 넷이다.\
별도로 추가한 것이 아니라 **기존 테스트가 가드 역할을 하도록 배치를 짠 것**이다.

| 테스트 | 지키는 것 | 이 수정과의 관계 |
|---|---|---|
| `zeroCapacity` (:38-59) | capacity 0이면 아무것도 캐시하지 않음 | `get`이 `capacity == 0`에서 조기 반환(:101-103)하므로 가드 경로에 닿지 않음 |
| `getAndSize` (:61-77) | 세 번째 키를 넣으면 첫 키가 축출됨 | **축출 경로가 여전히 감산한다는 증거 - 핵심 가드** |
| `removeAndSize` (:79-95) | `remove` 후 size가 줄고, 이후 삽입이 정상 축출 | **명시적 제거 경로가 여전히 감산한다는 증거** |
| `clearAndSize` (:97-113) | `clear` 후 size 0, 이후 삽입 정상 | `clear`의 `markAsRemoved` 호출도 여전히 감산 |

`getAndSize`와 `removeAndSize` 둘이 이 중 핵심이다.\
새 가드는 "감산을 건너뛰는" 코드이므로, **잘못 만들면 감산이 아예 안 되는 방향으로 깨질 수 있다.**\
구체적으로 가드를 `== REMOVED`가 아니라 `!isActive()`로 썼다면 PENDING_REMOVAL 노드가 전부 감산 없이 빠져나가 카운터가 커지는 쪽으로 어긋난다.\
그 경우 `removeAndSize`가 즉시 깨진다 - `remove("k2")` 후 `get("k3")`를 넣었을 때 축출이 일어나지 않아 `size()`가 3이 되기 때문이다.\
즉 **이 네 건이 fix 전후 모두 green이라는 사실이 "정상 감산 경로는 하나도 건드리지 않았다"의 실행 증거**다.

## 실측 요약

이 결함의 검증에서 특이한 점은, "테스트가 red인가"를 확인하는 일이 그 자체로 반복 실험이었다는 것이다.\
확률적 테스트이므로 한 번의 red는 증거가 되지 못한다.

| 회차 | 하네스 형태 | 판별식 | baseline(수정 전) | fix 후 |
|---|---|---|---|---|
| 1 | 20k ops, 히트 quiesce 10회 | 마지막 `size <= capacity` | **20/20 red** (size 30~39) | 5/20 red (잔여) |
| 2 | 20k ops, 히트 quiesce 50회 + 계측 | 〃 | - | red 트라이얼에서 `currentSize=2`(정확), map=46 |
| 3 | 20k ops, 새 키 quiesce 64회 | 〃 | 28/30 red | **0/30** |
| 4 | 50k ops, 수렴 quiesce(예산 50k) | 수렴 여부 | **20/20 red** | **0/20** |

네 회차가 무엇을 바꿔 가며 신뢰도를 올렸는지 세로로 보면 이렇다.

```text
  회차 1  히트 quiesce      baseline 20/20 red  /  fix 5/20 red
             |                                     ^
             |                                     |  잔여 red - 2 차 결함인가?
             v
  회차 2  + 계측            currentSize = 2 (정확), map = 46
             |                                     |
             |                                     v
             |                              카운터는 고쳐졌다. 원인은 딴 데다
             v
  회차 3  새 키 quiesce     baseline 28/30 red  /  fix 0/30
             |                                     ^
             |                                     |  원인은 하네스였다
             v
  회차 4  수렴 판별식       baseline 20/20 red  /  fix 0/20   <- 커밋된 형태
```

1회차의 "fix 후 5/20 red"가 조사의 출발점이었고, 3회차에서 그것이 하네스의 quiesce 결함이었음이 확정됐다(자세한 서사는 [structure.md](structure.md) 4절).\
최종적으로 커밋된 JUnit 테스트는 4회차 형태이고, spec §5가 요구한 "pre-fix 20회 전부 red" 조건을 그 형태로 재실측해 충족했다.

JUnit 실행 결과는 이렇다.

- **fix 전**: `ConcurrentLruCacheTests` **5 tests, 1 failed**.\
  새 테스트가 `size=38 > capacity=2`(예산 소진)로 실패, 기존 4건은 green.\
  최초 20k 파라미터 시절의 red는 `size=29 > capacity=2`였다.
- **fix 후**: 같은 파일 **5/5 green**, `spring-core` 전체 **5,188 tests, 0 failures**, checkstyle EXIT=0.
- **diff 규모**: 2파일, +50/-1.\
  프로덕션 변경은 가드 세 줄 + 주석 갱신이다.

## 커밋에 남기지 않은 실행 프로브

테스트로 커밋한 것 외에, 별도 클래스를 만들어 돌리고 결과만 취한 확인이 둘 있다.\
커밋에는 없지만 결함 판정과 수정 검증의 근거이므로 기록해 둔다(원본: 세션 scratchpad `Smoke.java`, `RedCheck.java`부터 `RedCheck4.java`).

> **프로브(probe)** — 커밋하지 않고 한 번 돌려 사실만 확인하고 버리는 임시 실행 코드.\
> 예: 리플렉션으로 내부 락을 선점해 특정 순서를 강제로 만들어 보는 작은 `main` 하나.

**probe 1 - 결정론 스모크.**\
리플렉션으로 `evictionLock`을 다른 스레드가 선점하게 만들어 [README 3절](README.md)의 4단계 시나리오를 그대로 재현한다.\
확률이 아니라 결정론이므로 "이 경로가 정말 고쳐졌는가"를 확정할 수 있는 유일한 증거다.

> **결정론(deterministic)** — 몇 번을 돌려도 같은 순서로 같은 결과가 나오는 성질.\
> 예: 락을 미리 선점해 두면 드레인 시점이 고정되므로, 운에 기대지 않고 같은 인터리빙을 재현할 수 있다.

```text
[수정 전]
after drain: cache.size()=2, internal currentSize=1
after adding D and E: cache.size()=3 (capacity=2), internal currentSize=2
contains C=false

[수정 후]
size=2, currentSize=2, D/E 정상 축출
```

수정 전 출력의 셋째 줄이 부수 피해다 - 방금 넣은 C가 엉뚱하게 축출됐다.\
`evictEntries`가 초과분을 처리하면서 큐 머리에 있던 C를 뽑아 버렸기 때문인데, 이 순서 이상은 가드 하나로 함께 사라진다.\
다만 PR의 주장은 size 불변식에 한정했고 축출 순서 개선은 주장하지 않았다(spec §4 금지영역).

이 스모크의 재실행이 리뷰 지적 **F4**의 내용이다.\
spec §5가 검증 항목으로 명시해 두었는데 fix 후 결과가 기록에 없어 "명세 미충족" 판정을 받았고, 다시 돌려 결과를 log에 남겼다.

**probe 2 - red 신뢰도 하네스.**\
`RedCheck` 계열 네 개가 위 실측 표의 각 회차다.\
`RedCheck2`는 리플렉션으로 `currentSize`를 직접 읽어 계측하는 버전인데, 이 계측이 조사의 방향을 뒤집었다 - fix 후 남은 red 트라이얼에서 `currentSize=2`로 **정확한데** map은 46이었고, 그래서 "카운터는 고쳐졌다, 문제는 다른 데 있다"가 확정됐다.\
이후 `RedCheck3`가 quiesce를 새 키 방식으로 바꾸자 0/30이 나오면서 "다른 데"가 하네스 자신이었음이 드러났다.

> **계측(instrumentation)** — 겉으로 안 보이는 내부 값을 일부러 꺼내 보는 일.\
> 예: 리플렉션으로 private 필드를 읽어, 어긋남의 원인이 카운터인지 map인지 갈랐다.
