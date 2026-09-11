# PR #37268 - 테스트 해설 (테스트 하나하나)

> `ConcurrentLruCacheTests`에 추가된 1건 + 같은 파일의 기존 4건이 맡은 가드 역할.
> 각 테스트를 "무엇을 주장하나 / 왜 red 또는 가드인가 / 단언 하나하나의 의미"로
> 해설한다. 이 PR의 테스트는 동시성 테스트라 **단언보다 배치와 종료 처리가 더 많은
> 것을 결정하므로**, 그 부분에 지면을 더 썼다. 배경 개념은
> [동시성 버그 테스트의 경합 보장](../../concepts/race-condition-test-guarantees/race-condition-test-guarantees.md).

배치 전체를 먼저 본다. 이 결함은 **두 스레드가 같은 노드를 서로 다른 경로로 정리할
때만** 발화하므로, 새 테스트 하나가 그 경합 전부를 맡고 기존 넷은 "단일 스레드에서의
정상 동작이 그대로인가"를 맡는 구도가 된다. 두 축으로 줄 세우면 이렇다.

| | 제거 경로가 하나뿐 | 제거 경로가 둘이 겹침 |
|---|---|---|
| 단일 스레드 | T2 `getAndSize`(축출) / T3 `removeAndSize`(명시적 제거) / T4 `clearAndSize` - 가드 | (구조적으로 불가) |
| 두 스레드 | - | **T5 `removeRacingWithEvictionDoesNotExceedCapacity` - red** |

오른쪽 아래 칸이 비어 있었던 것이 이 결함이 4년 넘게 살아남은 이유다. 기존 넷은
전부 왼쪽 열에 있고, 왼쪽 열에서는 쓰기 큐가 매 호출마다 즉시 드레인되므로
`[AddTask, RemovalTask]`가 나란히 쌓이는 상황 자체가 만들어지지 않는다.

## T5. `removeRacingWithEvictionDoesNotExceedCapacity` - red

새로 추가한 유일한 테스트다. 전문은 이렇다.

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

- **주장**: 명시적 제거와 축출이 겹쳐 돌아간 뒤, 남은 쓰기 작업을 전부 드레인하면
  캐시는 capacity로 돌아온다.
- **fix 전 red인 이유**: 겹침이 한 번이라도 나면 `currentSize`가 map보다 작아지고, 그
  어긋남은 [README 3절](README.md)의 수지 계산대로 순변화 0으로 동결된다. 예산
  50,000회를 다 써도 `size()`가 capacity 아래로 내려오지 않는다. 실측 red는
  `size=38 > capacity=2`, 예산 소진.

### 무대 만들기 - 두 스레드가 각각 무엇을 담당하나

이 테스트의 절반은 단언이 아니라 **결함 경로를 실제로 밟게 만드는 배치**다. 두 스레드가
서로 다른 재료를 공급한다.

| 스레드 | 하는 일 | 만들어 내는 것 |
|---|---|---|
| 메인 | `get(1)`부터 `get(50_000)`까지 전부 새 키 | 매번 miss -> `put` -> `AddTask` 큐잉 -> 드레인 시 `evictEntries()` 발동 |
| remover | `get(0)` 다음 `remove(0)`을 무한 반복 | 노드 0을 살렸다 죽였다 하며 `RemovalTask(0)`를 계속 큐잉 |

**capacity를 2로 잡은 것이 재료 배합의 핵심이다.** 캐시가 작을수록 축출이 매 삽입마다
일어나므로 `evictEntries()`가 큐 머리를 뽑는 빈도가 최대가 되고, 큐 머리에 노드 0이
놓일 확률도 높아진다. 반대로 capacity가 크면 축출이 드물어 겹칠 기회가 줄어든다.

**`get(0)`이 `remove(0)` 앞에 있는 이유**는 재료 자체가 사라지지 않게 하기 위해서다.
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

`remove(0)`만 연속으로 돌리면 두 번째 호출부터는 `node == null`에서 조기 반환하고,
`markForRemoval`도 `RemovalTask` 큐잉도 일어나지 않는다. 즉 경합 재료가 아예 생산되지
않는다. `get(0)`이 매 사이클 노드를 다시 넣어 줘야 `remove`가 유효해진다. 이 쌍이 이
테스트에서 유일하게 "왜 이렇게 썼는지 안 보이는" 줄이었고, 실제로 이해 게이트의 질문
하나가 정확히 이 지점이었다([gates.md](gates.md) G1-Q2).

### 수렴 quiesce - 이 테스트에서 가장 중요한 열 줄

경합을 일으키는 것보다 어려운 것이 **언제 단언할 것인가**였다. 이 캐시는 드레인 전에
일시적으로 capacity를 넘는 것이 정상이므로, 스레드를 세운 직후에 `size() <= capacity()`를
단언하면 정상 동작도 red가 된다. 그래서 마지막 준비 단계가 필요하다.

```java
int budget = 50_000;
int key = 100_000;
while (cache.size() > cache.capacity() && budget-- > 0) {
	cache.get(key++);
}
```

이 네 줄에 든 선택 셋이 각각 다른 실패를 막는다.

- **`key++`로 매번 새 키를 쓰는 이유**: 이미 있는 키를 `get`하면 그것은 **읽기**이고,
  읽기는 읽기 버퍼에만 기록될 뿐 쓰기 큐의 드레인을 보장하지 않는다(`processRead`,
  :128-134). 새 키여야 miss -> `put` -> `processWrite`가 되고, `processWrite`는
  `drainStatus`를 REQUIRED로 세운 뒤 `drainOperations()`를 직접 부른다(:136-140). 즉
  **새 키만이 백로그를 밀어낸다.**
- **`budget`으로 유계인 이유**: 무한 루프면 fix 전 실행이 영원히 끝나지 않는다. 예산이
  소진되면 루프를 빠져나와 마지막 단언에서 red가 되게 했다.
- **`100_000`에서 시작하는 이유**: 메인 루프가 쓴 1~50,000과 겹치지 않게 하기 위해서다.
  겹치면 그 `get`이 히트가 되어 쓰기를 유발하지 못한다.

**이 루프의 형태가 곧 판별식이다.** "수렴하는가"를 묻고 있고, 수정 전과 후의 차이가
정확히 수렴 여부이므로 red와 green이 갈린다. 이 판별식에 도달하기까지 잘못된
quiesce로 헤맨 과정은 [structure.md](structure.md) 4절에 있다.

### 네 단언이 각각 막는 것

단언은 넷인데, 결함을 보는 것은 마지막 하나뿐이고 앞의 셋은 전부 **이 테스트가
거짓으로 통과하는 경로**를 막는다. 그 구도를 표로 두면 이렇다.

| 단언 | 막는 실패 모드 | 없으면 어떻게 되나 |
|---|---|---|
| `remover.isAlive()).isFalse()` | 워커가 종료되지 않았는데 통과 | `join(5000)`은 타임아웃돼도 조용히 반환한다 - 행에 걸린 스핀 스레드가 남은 채로 통과하고, 스위트 내내 CPU와 `evictionLock`을 물고 돈다 |
| `failure.get()).isNull()` | 워커가 예외로 죽었는데 통과 | 스레드 안의 uncaught 예외는 stderr 한 줄만 남기고 사라진다 - 경합 0회 실행이 정상 green과 구분 불가 |
| `removals.get()).isGreaterThan(0)` | 워커가 살아 있었으나 일을 못 했는데 통과 | remover가 스케줄되지 못하거나 `remove`가 계속 `false`를 반환해도 최종 단언은 당연히 통과 |
| `cache.size()).isLessThanOrEqualTo(cache.capacity())` | (이것이 결함을 보는 단언) | - |

앞의 셋은 전부 **위장 green** 차단이다. 동시성 테스트에서 이 셋이 없으면 "테스트가
있다"는 사실만 남고 검출력은 0이 될 수 있는데, 그 0이 정상 green과 겉모습이 같아
아무도 모른다. 셋 다 리뷰에서 지적받아 추가됐다(F2 = U1-R1로 둘째와 셋째, N1으로
첫째 - [README 6절](README.md)).

`isAlive()` 단언이 왜 `join(5000)`과 한 쌍인지는 따로 적어 둘 만하다. 원래 코드는 무제한
`join()`이었고, 리뷰가 "테스트가 실패하면 영원히 매달린다"고 지적해 `join(5000)`으로
바꿨다. 그런데 `Thread.join(millis)`는 **타임아웃 시 예외를 던지지 않고 조용히
반환한다.** 그래서 `join(5000)` 자체는 "최대 5초 기다렸다"만 보증할 뿐 종료를 전혀
보증하지 못한다. `isAlive()` 단언이 그 빈틈을 메워 "join이 대기만 한 것이 아니라 실제
종료로 반환했다"를 확인한다. 순서도 의미가 있다 - 이 단언이 `failure.get()` 읽기보다
앞에 오므로, `join`의 happens-before를 타고 워커가 완전히 종료한 뒤 기록된 값을 읽는
것이 보장된다.

### 왜 latch로 진입을 강제하지 않았나

리뷰(U1-R1)가 제안한 것 중 하나가 `CountDownLatch`나 `CyclicBarrier`로 두 스레드의
진입을 맞추는 것이었다. 채택하지 않았고, 그 대신 `removals > 0` 관측 단언을 넣었다.
이유는 latch가 보장하는 것과 이 테스트가 필요로 하는 것이 다르기 때문이다. latch는
"두 스레드가 같은 시점에 출발했다"를 보장하지만, 이 결함이 요구하는 것은 **특정
인터리빙**(축출이 poll한 노드가 하필 방금 remove된 그 노드)이고 그것은 latch로
만들어지지 않는다. 반면 `removals > 0`은 "워커가 실제로 제거를 성공시켰다"를 사후
관측으로 확정한다 - 보장의 종류가 더 약하지만 이 테스트가 실제로 필요로 하는 축이다.

리뷰의 post-fix 지적 N2가 이 한계를 정확히 짚었다 - `removals > 0`은 제거 성공만
증명하지 같은 노드에서의 경합을 증명하지 않는다. 공개 API로는 그 이상을 증명할 수
없으므로 **부분 수용**으로 처리하고, 한계를 PR 본문에 직접 적었다("a single
interleaving cannot be forced through the public API"). 결정론을 원하면 리플렉션으로
`evictionLock`을 선점해야 하는데(아래 스모크가 그 방식이다), upstream 테스트 스타일이
아니라 커밋하지 않았다.

## T1~T4. 기존 테스트 4건 - 무회귀 가드 (전후 green)

새 테스트가 경합 경로를 맡는 동안, 나머지 경로가 그대로임을 고정하는 쪽은 이미 있던
넷이다. 별도로 추가한 것이 아니라 **기존 테스트가 가드 역할을 하도록 배치를 짠 것**이다.

| 테스트 | 지키는 것 | 이 수정과의 관계 |
|---|---|---|
| `zeroCapacity` (:38-59) | capacity 0이면 아무것도 캐시하지 않음 | `get`이 `capacity == 0`에서 조기 반환(:101-103)하므로 가드 경로에 닿지 않음 |
| `getAndSize` (:61-77) | 세 번째 키를 넣으면 첫 키가 축출됨 | **축출 경로가 여전히 감산한다는 증거 - 핵심 가드** |
| `removeAndSize` (:79-95) | `remove` 후 size가 줄고, 이후 삽입이 정상 축출 | **명시적 제거 경로가 여전히 감산한다는 증거** |
| `clearAndSize` (:97-113) | `clear` 후 size 0, 이후 삽입 정상 | `clear`의 `markAsRemoved` 호출도 여전히 감산 |

`getAndSize`와 `removeAndSize` 둘이 이 중 핵심이다. 새 가드는 "감산을 건너뛰는" 코드이므로,
**잘못 만들면 감산이 아예 안 되는 방향으로 깨질 수 있다.** 구체적으로 가드를
`== REMOVED`가 아니라 `!isActive()`로 썼다면 PENDING_REMOVAL 노드가 전부 감산 없이
빠져나가 카운터가 커지는 쪽으로 어긋나는데, 그 경우 `removeAndSize`가 즉시 깨진다 -
`remove("k2")` 후 `get("k3")`를 넣었을 때 축출이 일어나지 않아 `size()`가 3이 되기
때문이다. 즉 **이 네 건이 fix 전후 모두 green이라는 사실이 "정상 감산 경로는 하나도
건드리지 않았다"의 실행 증거**다.

## 실측 요약

이 결함의 검증에서 특이한 점은, "테스트가 red인가"를 확인하는 일이 그 자체로 반복
실험이었다는 것이다. 확률적 테스트이므로 한 번의 red는 증거가 되지 못한다.

| 회차 | 하네스 형태 | 판별식 | baseline(수정 전) | fix 후 |
|---|---|---|---|---|
| 1 | 20k ops, 히트 quiesce 10회 | 마지막 `size <= capacity` | **20/20 red** (size 30~39) | 5/20 red (잔여) |
| 2 | 20k ops, 히트 quiesce 50회 + 계측 | 〃 | - | red 트라이얼에서 `currentSize=2`(정확), map=46 |
| 3 | 20k ops, 새 키 quiesce 64회 | 〃 | 28/30 red | **0/30** |
| 4 | 50k ops, 수렴 quiesce(예산 50k) | 수렴 여부 | **20/20 red** | **0/20** |

1회차의 "fix 후 5/20 red"가 조사의 출발점이었고, 3회차에서 그것이 하네스의 quiesce
결함이었음이 확정됐다(자세한 서사는 [structure.md](structure.md) 4절). 최종적으로
커밋된 JUnit 테스트는 4회차 형태이고, spec §5가 요구한 "pre-fix 20회 전부 red" 조건을
그 형태로 재실측해 충족했다.

JUnit 실행 결과는 이렇다.

- **fix 전**: `ConcurrentLruCacheTests` **5 tests, 1 failed** - 새 테스트가
  `size=38 > capacity=2`(예산 소진)로 실패, 기존 4건은 green. 최초 20k 파라미터
  시절의 red는 `size=29 > capacity=2`였다.
- **fix 후**: 같은 파일 **5/5 green**, `spring-core` 전체 **5,188 tests, 0 failures**,
  checkstyle EXIT=0.
- **diff 규모**: 2파일, +50/-1. 프로덕션 변경은 가드 세 줄 + 주석 갱신이다.

## 커밋에 남기지 않은 실행 프로브

테스트로 커밋한 것 외에, 별도 클래스를 만들어 돌리고 결과만 취한 확인이 둘 있다.
커밋에는 없지만 결함 판정과 수정 검증의 근거이므로 기록해 둔다(원본: 세션 scratchpad
`Smoke.java`, `RedCheck.java`부터 `RedCheck4.java`).

**probe 1 - 결정론 스모크.** 리플렉션으로 `evictionLock`을 다른 스레드가 선점하게 만들어
[README 3절](README.md)의 4단계 시나리오를 그대로 재현한다. 확률이 아니라 결정론이므로
"이 경로가 정말 고쳐졌는가"를 확정할 수 있는 유일한 증거다.

```
[수정 전]
after drain: cache.size()=2, internal currentSize=1
after adding D and E: cache.size()=3 (capacity=2), internal currentSize=2
contains C=false

[수정 후]
size=2, currentSize=2, D/E 정상 축출
```

수정 전 출력의 셋째 줄이 부수 피해다 - 방금 넣은 C가 엉뚱하게 축출됐다. `evictEntries`가
초과분을 처리하면서 큐 머리에 있던 C를 뽑아 버렸기 때문인데, 이 순서 이상은 가드 하나로
함께 사라진다. 다만 PR의 주장은 size 불변식에 한정했고 축출 순서 개선은 주장하지 않았다
(spec §4 금지영역).

이 스모크의 재실행이 리뷰 지적 **F4**의 내용이다. spec §5가 검증 항목으로 명시해 두었는데
fix 후 결과가 기록에 없어 "명세 미충족" 판정을 받았고, 다시 돌려 결과를 log에 남겼다.

**probe 2 - red 신뢰도 하네스.** `RedCheck` 계열 네 개가 위 실측 표의 각 회차다.
`RedCheck2`는 리플렉션으로 `currentSize`를 직접 읽어 계측하는 버전인데, 이 계측이
조사의 방향을 뒤집었다 - fix 후 남은 red 트라이얼에서 `currentSize=2`로 **정확한데**
map은 46이었고, 그래서 "카운터는 고쳐졌다, 문제는 다른 데 있다"가 확정됐다. 이후
`RedCheck3`가 quiesce를 새 키 방식으로 바꾸자 0/30이 나오면서 "다른 데"가 하네스
자신이었음이 드러났다.
