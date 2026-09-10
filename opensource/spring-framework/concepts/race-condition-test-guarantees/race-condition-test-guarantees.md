# 개념: 동시성 버그 테스트의 "경합 보장"

> U1(ConcurrentLruCache 이중 size 감산) 작업의 리뷰 지적 U1-R1을 계기로 쓴 배경 개념 문서.
> 실증 기준: spring-framework-fork 워킹트리
> `spring-core/src/test/java/org/springframework/util/ConcurrentLruCacheTests.java`,
> 실측 수치는 `docs/plans/2026-09-10/u1-lru-double-decrement/log.md`.

## 한 줄 정의 — 경합의 발생이 아니라 결함 검출력의 보장이다

"경합을 보장한다"는 말은 두 가지 중 하나를 뜻하는데, 실제로 지켜야 하는 것은 후자다. 전자는
**문제의 인터리빙이 매 실행마다 반드시 일어남**(결정론)이고, 후자는 **결함이 있으면 red가
된다는 신뢰도**다. 전자는 대부분의 실전 코드에서 내부 구조에 손대지 않고는 얻을 수 없고,
후자는 확률적 기법의 조합으로 실용 수준까지 끌어올릴 수 있다. 좋은 동시성 테스트는 경합이
일어났음을 증명하는 테스트가 아니라 **결함이 살아 있으면 통과할 수 없게 설계된** 테스트다.

## 문제의 정의 — start()는 실행을 보장하지 않는다

`Thread.start()`는 그 스레드가 언제 첫 명령을 실행하는지 아무것도 약속하지 않는다. JMM이
보장하는 것은 start() 이전의 쓰기가 새 스레드에 보인다는 happens-before 관계뿐이고, 실행
시점은 OS 스케줄러 소관이다. 그래서 start() 직후 동기화 없이 본 루프로 진행하면, 메인이
50,000회 루프를 다 돌고 `stop.set(true)`까지 세팅한 뒤에야 보조 스레드가 스케줄되어
`while (!stop.get())`을 한 번도 통과하지 못하는 실행이 원리적으로 가능하다. 이 실행에서는
두 스레드가 시간상 겹친 적이 없어 경합 창(window)이 아예 열리지 않고, 결함이 그대로 있어도
테스트는 green이다. 1코어 CI, 컨테이너 CPU 쿼터, 고부하 상태에서 충분히 현실적이다.

## false green과 false red의 비용은 대칭이 아니다

두 실패 양상은 비용 구조가 달라서, 설계는 그 비대칭에 맞춰야 한다.

| 양상 | 뜻 | 드러나는 방식 | 비용 |
|---|---|---|---|
| false green | 결함이 있는데 통과 | 아무도 모른다 (무음) | 회귀 방지 기능이 0 — 테스트가 있다는 착시까지 얹힘 |
| false red | 결함이 없는데 실패 (flaky) | 빌드가 빨개진다 | 시끄럽지만 관측 가능 — 조사·완화가 가능 |

false green은 관측되지 않으니 자기수정 기회가 없다. flaky는 아프지만 눈에 보이고 반복 수나
타임아웃으로 수렴시킬 수 있다. 그래서 **검출력을 먼저 확보하고 안정성을 나중에 다듬는**
순서가 옳다. U1에서 테스트를 먼저 써서 pre-fix red를 확인한 것(log.md의 "task 1 red: JUnit
size=29 > capacity=2")이 그 순서다 — red를 실측하지 않은 동시성 테스트는 검출력이 미지수인
채로 머지된다.

## 보장 기법 스펙트럼

기법은 "얼마나 강하게 경합을 강제하는가"와 "얼마나 대상 내부에 결합하는가"로 줄 세울 수 있다.

| 기법 | 보장하는 것 | 결합도 | 비용 |
|---|---|---|---|
| 반복 스트레스 + 누적 판별식 | 확률 상승 (누적형 결함이면 매우 높음) | 없음 | 실행 시간 |
| 진입 보장 (CountDownLatch/CyclicBarrier) | 상대 스레드가 살아 돌고 있음 | 테스트 코드만 | 거의 없음 |
| 종료 안전 (join(timeout) + try/finally) | 실패해도 스레드가 새지 않음 | 테스트 코드만 | 거의 없음 |
| 창 확장 (반복 수·키 패턴) | 충돌 확률 상향 | 없음 | 실행 시간 |
| 결정론 주입 (내부 락 선점) | 문제 인터리빙 자체 | 높음 (private 구조) | 리팩토링에 취약 |
| jcstress | 인터리빙 공간 탐색 | 별도 모듈 | 별도 하네스 |

### 반복 스트레스 + 누적 판별식

결함의 효과가 **누적되고 자기수정되지 않는** 종류라면 반복 스트레스만으로 검출력이 거의 1에
수렴한다. 한 번만 경합해도 흔적이 영구히 남으니 마지막에 불변식 하나만 단언하면 된다. U1이
그 유형이다 — `markAsRemoved`가 같은 노드를 두 번 지나면 `currentSize`가 1 작아지고, 그
드리프트는 이후 어떤 정상 동작으로도 복구되지 않는다. 실측으로도 20,000 ops에서 baseline
28/30 red(약 93%), 50,000 ops로 올리자 15/15 red(100%)였다. 반대로 효과가 일시적인 결함
(잠깐 잘못된 값을 반환하고 곧 자기수정)이라면 이 기법은 약하다 — 관측 시점 자체가 경합 창
안에 있어야 하므로 진입 보장이나 결정론 주입이 필요하다.

### 진입 보장 — CountDownLatch와 CyclicBarrier

`CountDownLatch`는 "상대가 최소 한 사이클을 돌았다"를 확인하고 본 루프에 들어가게 해서, 앞
절의 "보조 스레드가 한 번도 안 돌았다" 시나리오를 원천 배제한다.

```java
CountDownLatch started = new CountDownLatch(1);
Thread remover = new Thread(() -> {
    while (!stop.get()) {
        cache.get(0);
        cache.remove(0);
        started.countDown();
    }
});
remover.start();
assertThat(started.await(5, TimeUnit.SECONDS)).isTrue();
```

`CyclicBarrier`는 N개 스레드를 같은 지점에서 동시 출발시킨다. 두 스레드가 "동시에 같은 연산에
진입"해야 열리는 창이면 배리어가 맞고, U1처럼 한쪽이 계속 돌기만 하면 되는 경우엔 latch로
충분하다. 다만 둘 다 **본 루프 내내 겹쳐 돈다는 것까지는 보장하지 않는다** — 출발선뿐이다.

### 종료 안전 — join(timeout)과 try/finally

`join()`을 인자 없이 부르면 상대가 영영 끝나지 않을 때 테스트가 무한 대기한다. 더 흔한 사고는
본 루프의 단언이 실패해 예외로 빠져나가면서 `stop.set(true)`와 `join()`이 아예 실행되지 않는
경우다. 보조 스레드가 살아남아 다음 테스트의 캐시·CPU를 건드리고 "A를 고쳤더니 B가 깨진다"는
오염이 시작된다. 정지 신호와 join은 `finally`에, join에는 타임아웃을, 타임아웃 초과는 그
자체로 단언 실패로 다룬다.

### 창 확장

경합 창이 좁을수록 반복 횟수를 올리거나 충돌하기 쉬운 데이터 패턴을 쓴다. U1에서는 20,000 ->
50,000 상향만으로 red율이 93% -> 100%가 됐다. 키 패턴도 같은 축이다 — remover가 건드리는 키와
축출 압력을 만드는 키가 같은 큐 구간에 몰릴수록 창이 넓어진다. 비용은 실행 시간이므로
upstream 테스트라면 "1초 안쪽" 예산 안에서 최대 반복을 택하는 절충이 현실적이다.

### 결정론 주입

가장 확실한 방법은 문제 인터리빙을 코드로 강제하는 것이다. U1 스모크에서는 private
`evictionLock`을 리플렉션으로 잡아 드레인을 막아 둔 채 write 큐에 `[AddTask, RemovalTask]`를
쌓고, 그 뒤 락을 놓아 순서를 확정했다. 결함이 살아 있으면 100% red이고 빠르지만, private 필드
이름과 내부 자료구조에 결합해 리팩토링 한 번에 무력화된다. `ConcurrentLruCacheTests`에는
리플렉션 선례가 없어 upstream 테스트로는 이례적이라, U1에서는 스모크 전용으로만 쓰고 제출
테스트는 스트레스형(A안)을 택했다.

### jcstress

OpenJDK jcstress는 인터리빙 탐색 자체를 목적으로 하는 하네스로, 짧은 액터 메서드 쌍을 수백만
번 돌리며 관측된 결과 집합을 분류하고 허용/금지 결과를 선언하게 한다. JMM 수준의 가시성·재정렬
결함(non-volatile 게시 등)에 적합하다. 별도 모듈·빌드 설정이 필요해 단위 테스트 스위트에 섞기는
어렵고, 라이브러리 자료구조를 새로 만들 때의 검증 도구로 보는 편이 맞다. (U1에서는 쓰지 않았다.)

## 무엇을 단언할 것인가 — 과정이 아니라 불변식

단언 대상은 "경합이 일어났는가"가 아니라 **경합이 일어났다면 깨졌을 불변식**이어야 한다. 과정을
단언하면 테스트가 스케줄러 구현에 묶여 flaky해지고, 내부 상태를 관측하려다 관측 자체가 창을
바꾼다. U1의 단언은 공개 표면 한 줄이다 — `cache.size() <= cache.capacity()`. private이고
거짓말하는 쪽인 `currentSize`가 아니라, 피해가 드러나는 유일한 공개 관측면인 map 크기를 본다.

절충안은 불변식 단언은 그대로 두고 **경합 관측 신호를 보조 단언으로 덧붙이는** 것이다. remover
사이클 수를 세어 본 루프 구간 동안 최소 N회 돌았음을 확인하면, green이 "경합이 없어서 통과한"
green인지 "경합했는데도 불변식이 지켜진" green인지 구별된다. 검출력을 올리지는 않지만
**false green을 false red로 바꿔** 무음을 깨뜨린다.

함정이 하나 있다. 누적형 결함에서는 마지막 단언 시점이 **드레인이 끝난 상태**여야 한다. U1
하네스가 한동안 fix 후에도 red였던 원인은 2차 결함이 아니라 quiesce 결함이었다 — 읽기 히트는
write 큐 드레인을 유발하지 않아 미드레인 AddTask 백로그가 남았다. 유계 예산 안에서
`size() <= capacity()`가 될 때까지 쓰기를 유발하는 "수렴 quiesce"로 바꾸고 나서야
pre-fix(예산 소진, size 38)와 post-fix(수렴)가 결정론적으로 갈렸다.

## U1 사례 종합 — 현재 테스트의 약점과 보강안

현재 워킹트리 테스트는 스트레스 + 수렴 quiesce 골격은 갖췄지만 진입 보장과 종료 안전이 빠져
있다(`ConcurrentLruCacheTests.java:113-136`).

```java
	@Test
	void removeRacingWithEvictionDoesNotExceedCapacity() throws Exception {
		ConcurrentLruCache<Integer, String> cache = new ConcurrentLruCache<>(2, key -> "value" + key);
		AtomicBoolean stop = new AtomicBoolean();
		Thread remover = new Thread(() -> {
			while (!stop.get()) {
				cache.get(0);
				cache.remove(0);
			}
		});
		remover.start();
		for (int i = 1; i <= 50_000; i++) {
			cache.get(i);
		}
		stop.set(true);
		remover.join();
		int budget = 50_000;
		int key = 100_000;
		while (cache.size() > cache.capacity() && budget-- > 0) {
			cache.get(key++);
		}

		assertThat(cache.size()).isLessThanOrEqualTo(cache.capacity());
	}
```

약점은 셋이다. (1) `remover.start()` 직후 동기화 없이 본 루프 진입 — remover가 한 번도 안 돌아도
green. (2) `remover.join()`이 무제한 대기. (3) 본 루프에서 예외가 나면 `stop.set(true)`/`join()`이
실행되지 않아 스레드가 샌다. 보강안은 골격(스트레스 + 수렴 quiesce + 불변식 단언)을 그대로 두고
세 구멍만 막는다.

```java
	@Test
	void removeRacingWithEvictionDoesNotExceedCapacity() throws Exception {
		ConcurrentLruCache<Integer, String> cache = new ConcurrentLruCache<>(2, key -> "value" + key);
		AtomicBoolean stop = new AtomicBoolean();
		CountDownLatch started = new CountDownLatch(1);
		AtomicLong removerCycles = new AtomicLong();
		Thread remover = new Thread(() -> {
			while (!stop.get()) {
				cache.get(0);
				cache.remove(0);
				removerCycles.incrementAndGet();
				started.countDown();
			}
		});
		remover.start();
		long cyclesBefore;
		long cyclesAfter;
		try {
			assertThat(started.await(5, TimeUnit.SECONDS)).as("remover did not start").isTrue();
			cyclesBefore = removerCycles.get();
			for (int i = 1; i <= 50_000; i++) {
				cache.get(i);
			}
			cyclesAfter = removerCycles.get();
		}
		finally {
			stop.set(true);
			remover.join(10_000);
		}
		assertThat(remover.isAlive()).as("remover did not stop").isFalse();
		assertThat(cyclesAfter - cyclesBefore).as("threads did not overlap").isGreaterThan(1_000);

		int budget = 50_000;
		int key = 100_000;
		while (cache.size() > cache.capacity() && budget-- > 0) {
			cache.get(key++);
		}

		assertThat(cache.size()).isLessThanOrEqualTo(cache.capacity());
	}
```

`cyclesBefore`/`cyclesAfter`의 차를 보는 이유는 latch만으로는 출발선밖에 보장되지 않기 때문이다.
본 루프 시작 직전과 직후의 사이클 수 차이가 크다는 것은 두 스레드가 그 구간 동안 실제로 시간상
겹쳐 돌았다는 사후 증거다. 추가 import는 `java.util.concurrent.CountDownLatch`,
`java.util.concurrent.TimeUnit`, `java.util.concurrent.atomic.AtomicLong` 셋이다.

## 요약

- 결정론이 불가능해도 검출력은 설계할 수 있다 — 누적형 결함이면 스트레스 + 최종 불변식으로 충분하다.
- 동시성 테스트는 반드시 pre-fix red를 실측하고 그 비율을 기록한다. 실측 없는 red는 검출력 미지수다.
- start() 뒤에는 latch를, join에는 타임아웃을, 정지 신호에는 finally를 붙인다. 셋 다 비용이 거의 없다.
- 단언은 불변식(공개 표면)에, 경합 관측은 보조 단언에 둔다.
- 누적형 결함의 최종 단언 전에는 드레인 수렴을 명시적으로 유도한다 — 읽기만으로는 드레인되지 않는다.
