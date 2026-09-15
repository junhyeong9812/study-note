# PR #36932 — Avoid divide-by-zero in `ExponentialBackOff` jitter

## 0. 정향

이 문서는 Spring Framework에 기여한 PR #36932를 처음부터 재구성하는 학습용 해설이다.\
다루는 대상은 `spring-core`의 재시도 대기 시간 계산기 `ExponentialBackOff`이며, 그 안의 지터(jitter) 계산식이 특정 설정 조합에서 0으로 나누기 예외를 던지던 문제다.

배경(이 클래스가 무엇인지)에서 시작해 수정 전 흐름, 재현, 수정, 검증, 그리고 머지 이후 메인테이너가 이어서 한 후속 작업까지 순서대로 따라간다.\
이 문서만 읽고도 "왜 이 한 줄이 문제였고 왜 이렇게 고쳤는가"를 남에게 설명할 수 있는 것이 목표다.

## 1. 배경 — `ExponentialBackOff`는 무엇을 하는 물건인가

`ExponentialBackOff`는 "실패한 작업을 다시 시도하기까지 얼마나 기다릴지"를 시도 횟수마다 점점 늘려가며 계산해 주는 전략 객체다.\
패키지는 `org.springframework.util.backoff`이고, `spring-core`에 있으며 4.1부터 존재한다.\
계산만 할 뿐 스스로 잠들지는 않는다.\
즉 이 클래스는 밀리초 숫자를 돌려주는 순수 계산기이고, 실제로 `Thread.sleep`을 부르는 쪽은 호출자다.

> **백오프(back-off)** — 실패한 작업을 곧바로 다시 부르지 않고 일정 시간 기다렸다가 재시도하는 것.\
> 예: 첫 실패 뒤 2000ms, 다음엔 3000ms, 그다음 4500ms를 기다린다.

핵심 용어를 먼저 정리한다. 아래 이름들은 이 문서 전체에서 같은 뜻으로 쓴다.

- `initialInterval`: 첫 번째 대기 시간(기본 2000ms).\
  호출자가 `setInitialInterval`로 바꾼다.
- `multiplier`: 매 시도마다 직전 간격에 곱하는 배수(기본 1.5).\
  1 미만은 거부된다.
- `maxInterval`: 간격의 상한(기본 30000ms).\
  여기 도달하면 더 커지지 않는다.
- `jitter`: 계산된 간격 주변으로 무작위로 흔들어 주는 폭(기본 0, 7.0에서 추가).\
  여러 클라이언트가 동시에 재시도해 서버를 다시 무너뜨리는 이른바 thundering herd를 흩어 놓는 장치다.
- `maxElapsedTime` / `maxAttempts`: 누적 대기 시간 또는 시도 횟수의 종료 조건.\
  넘으면 `BackOffExecution.STOP`을 돌려준다.

> **지터(jitter)** — 계산된 대기 시간 주변으로 난수를 뿌려 재시도 시각을 일부러 어긋나게 만드는 폭.\
> 예: 대기 4500ms에 지터 폭 200ms를 적용하면 4300~4699ms 사이의 아무 값이 나온다.

> **thundering herd** — 같은 순간에 실패한 여러 클라이언트가 정확히 같은 시각에 한꺼번에 재시도해 이미 무너진 서버를 다시 밀어붙이는 현상.\
> 예: 서버가 1초간 죽었다 살아나는 순간, 대기 중이던 클라이언트 전부가 같은 밀리초에 재시도한다.

사용 계약은 `BackOff` 인터페이스가 정의한다. 인터페이스 자체의 Javadoc이 사용법을 이렇게 못 박고 있다.

```java
 * <pre class="code">
 * BackOffExecution execution = backOff.start();
 *
 * // In the operation recovery/retry loop:
 * long waitInterval = execution.nextBackOff();
 * if (waitInterval == BackOffExecution.STOP) {
 *     // do not retry operation
 * }
 * else {
 *     // sleep, for example, Thread.sleep(waitInterval)
 *     // retry operation
 * }</pre>
```

즉 설정을 담은 `ExponentialBackOff` 하나가 `start()`를 통해 재시도 시도마다 독립적인 실행 상태 객체 `BackOffExecution`을 찍어낸다.\
상태(현재 간격, 누적 시간, 시도 횟수)는 설정 객체가 아니라 실행 객체가 들고 있으므로, 같은 설정을 여러 스레드가 공유해도 서로 간섭하지 않는다.

> **`BackOffExecution`(실행 객체)** — 설정 객체 하나에서 `start()`로 찍어내는, 재시도 시퀀스 한 번분의 상태를 들고 있는 객체.\
> 예: 두 스레드가 같은 `ExponentialBackOff`를 공유해도 각자 `start()`를 부르면 시도 횟수가 따로 센다.

이 클래스를 쓰는 소비자는 프레임워크 안에 이미 여럿이다.\
가장 중요한 경로는 `spring-core`의 재시도 지원인 `RetryPolicy`다.\
`RetryPolicy.Builder#build()`는 사용자가 커스텀 `BackOff`를 주지 않았을 때 `ExponentialBackOff`를 직접 조립한다.

```java
			else {
				ExponentialBackOff exponentialBackOff = new ExponentialBackOff();
				exponentialBackOff.setMaxAttempts(this.maxRetries != null ? this.maxRetries : DEFAULT_MAX_RETRIES);
				exponentialBackOff.setInitialInterval(this.delay != null ? this.delay.toMillis() : DEFAULT_DELAY);
				exponentialBackOff.setJitter(this.jitter != null ? this.jitter.toMillis() : DEFAULT_JITTER);
				exponentialBackOff.setMultiplier(this.multiplier != null ? this.multiplier : DEFAULT_MULTIPLIER);
				exponentialBackOff.setMaxInterval(this.maxDelay != null ? this.maxDelay.toMillis() : DEFAULT_MAX_DELAY);
				backOff = exponentialBackOff;
			}
```

여기서 `delay`가 `ExponentialBackOff`의 `initialInterval`로, `jitter`가 그대로 `jitter`로 흘러들어 간다는 점이 이 PR의 피해 범위를 결정한다.\
그 위에는 `spring-context`의 `@Retryable` 애너테이션이 있고, 애너테이션의 `delay`와 `jitter` 속성이 같은 경로로 내려온다.\
`@Retryable`의 Javadoc은 `delay`에 대해 "Must be greater than or equal to zero"라고 명시한다.\
즉 0은 문서상 허용된 값이다.\
그 외의 소비자로는 `RetryTemplate`, 그리고 `spring-jms`의 `DefaultMessageListenerContainer`가 `BackOffExecution`을 직접 돌린다.

> **`@Retryable`** — 메서드에 붙이면 실패 시 자동으로 재시도하도록 만들어 주는 `spring-context`의 애너테이션.\
> 예: `@Retryable(delay = 0, jitter = 100)`은 "즉시 재시도하되 몰림만 흩자"는 설정이다.

실제로 대기를 수행하는 쪽은 `RetryTemplate`이며, 위 인터페이스 계약을 그대로 구현한다.

```java
			BackOffExecution backOffExecution = this.retryPolicy.getBackOff().start();
```

```java
					long sleepTime = backOffExecution.nextBackOff();
					if (sleepTime == BackOffExecution.STOP) {
```

```java
					Thread.sleep(sleepTime);
```

## 2. 수정 전 동작 방식 — 한 번의 `nextBackOff()`가 지나가는 길

수정 전 코드에서 대기 시간 하나는 세 단계를 거쳐 만들어졌다.\
종료 조건 확인, 기본 간격 증가, 그리고 지터 적용이다.\
내부 클래스 `ExponentialBackOffExecution`이 이 셋을 나눠 맡는다.

아래는 그 세 단계를 세로로 편 것이다. 왼쪽은 단계, 오른쪽은 그 단계가 정하는 것이다.

```text
 호출자의 재시도 루프 (RetryTemplate)   실패 뒤 "얼마나 잘까"를 묻는다
        |
        | execution.nextBackOff()
        v
 [1] nextBackOff()                     종료할지 말지만 정하고 계산은 위임한다
        |
        +-- currentElapsedTime >= maxElapsedTime ?  -> return STOP (-1)
        +-- attempts >= maxAttempts ?               -> return STOP (-1)
        |   그 외
        v
 [2] computeNextInterval()             이번 회차의 "지터 전" 간격을 정한다
        |
        +-- currentInterval < 0            -> nextInterval = initialInterval (2000)
        +-- currentInterval >= maxInterval -> nextInterval = maxInterval (30000)
        +-- 그 외                          -> nextInterval = min(currentInterval * 1.5, 30000)
        |
        |   this.currentInterval = nextInterval    지터 적용 "전" 값만 저장
        v
 [3] applyJitter(nextInterval)         반환값에만 흔들림을 얹는다
        |
        +-- jitter == 0 -> interval 을 그대로 반환
        +-- jitter > 0  -> [interval - applicableJitter, interval + applicableJitter] 안의 난수
        |
        v
 min(그 결과, maxInterval)              상한으로 한 번 더 자른 뒤 호출자에게 돌려준다
```

첫 단계는 진입점 `nextBackOff()`로, 종료 조건만 보고 나머지는 위임한다.

```java
		@Override
		public long nextBackOff() {
			if (this.currentElapsedTime >= getMaxElapsedTime() || this.attempts >= getMaxAttempts()) {
				return STOP;
			}
			long nextInterval = computeNextInterval();
			this.currentElapsedTime += nextInterval;
			this.attempts++;
			return nextInterval;
		}
```

둘째 단계 `computeNextInterval()`이 지수 증가의 본체다.\
상태 변수 `currentInterval`은 `-1`로 시작하는데, 이 음수가 "아직 한 번도 계산한 적 없음"이라는 표시로 쓰인다.\
그래서 첫 호출은 `initialInterval`을 그대로 쓰고, 이후 호출은 직전 간격에 `multiplier`를 곱하되 `maxInterval`을 넘지 않는다.

> **센티널(sentinel)** — 유효값이 될 수 없는 값을 골라 "특별한 상태"를 나타내는 표시로 쓰는 관용.\
> 예: 대기 시간은 음수가 될 수 없으므로 `currentInterval = -1`을 "아직 미계산"의 표시로 쓴다.

```java
		private long computeNextInterval() {
			long maxInterval = getMaxInterval();
			long nextInterval;
			if (this.currentInterval < 0) {
				nextInterval = getInitialInterval();
			}
			else if (this.currentInterval >= maxInterval) {
				nextInterval = maxInterval;
			}
			else {
				nextInterval = Math.min((long) (this.currentInterval * getMultiplier()), maxInterval);
			}
			this.currentInterval = nextInterval;
			return Math.min(applyJitter(nextInterval), maxInterval);
		}
```

여기서 한 가지 중요한 설계 선택을 짚어 둘 필요가 있다.\
`this.currentInterval`에 저장되는 값은 지터를 적용하기 **전**의 간격이다.\
다음 시도의 배수 계산은 이 저장된 값에서 출발하므로, 지터의 무작위성이 다음 회차로 누적되지 않는다.\
지터는 매번 마지막에 덧씌워지는 표면 장식이다.

셋째 단계가 이번 PR의 무대인 `applyJitter`다. 수정 전 코드는 다음과 같았다.

```java
		private long applyJitter(long interval) {
			long jitter = getJitter();
			if (jitter > 0) {
				long initialInterval = getInitialInterval();
				long applicableJitter = jitter * (interval / initialInterval);
				long min = Math.max(interval - applicableJitter, initialInterval);
				long max = Math.min(interval + applicableJitter, getMaxInterval());
				return min + (long) (Math.random() * (max - min));
			}
			return interval;
		}
```

이 네 줄의 의도는 "지터도 간격과 같은 비율로 커져야 한다"이다.\
간격이 초기값의 몇 배까지 자랐는지를 `interval / initialInterval`로 재고, 그 배율만큼 설정된 `jitter`를 확대해 `applicableJitter`를 얻는다.\
그다음 `[interval - applicableJitter, interval + applicableJitter]` 범위를 잡되, 아래로는 `initialInterval` 밑으로 내려가지 않고 위로는 `maxInterval`을 넘지 않도록 잘라낸다.\
마지막으로 그 구간 안에서 균등 난수 하나를 뽑는다.\
`jitter`가 0이면 이 블록 전체를 건너뛰고 간격을 그대로 돌려준다.

## 3. 무엇이 문제였나 — `initialInterval = 0`과 양수 `jitter`의 조합

문제는 배율을 재는 `interval / initialInterval`이 정수 나눗셈이며 분모가 검증되지 않는다는 데 있다.\
`initialInterval`이 0이면 이 식은 즉시 `ArithmeticException: / by zero`를 던진다.\
재현 코드는 세 줄이면 충분하다.

> **정수 나눗셈(integer division)** — 양쪽이 모두 정수형(`int`·`long`)인 나눗셈.\
> 예: 소수부를 버려서 `3000 / 2000`이 1이 되고, 분모가 0이면 `ArithmeticException: / by zero`를 던진다(실수 나눗셈이었다면 `NaN`이 됐을 것이다).

```java
ExponentialBackOff backOff = new ExponentialBackOff();
backOff.setInitialInterval(0);
backOff.setJitter(100);

backOff.start().nextBackOff(); // throws ArithmeticException: / by zero
```

값을 하나씩 대입해 보면 경로가 분명하다.\
첫 `nextBackOff()`에서 `currentElapsedTime`은 0이고 `attempts`도 0이므로 종료 조건에 걸리지 않는다.\
`computeNextInterval()`은 `currentInterval`이 `-1`이므로 첫 분기를 타서 `nextInterval = 0`을 얻는다.\
그리고 `applyJitter(0)`이 호출된다.\
그 안에서 `jitter`는 100이라 분기에 들어가고, `initialInterval`은 0이므로 식은 `100 * (0 / 0)`이 된다.\
정수 0을 정수 0으로 나누는 순간 JVM은 예외를 던진다.

이것이 왜 실질적인 피해인가 하는 물음이 이 PR의 핵심 논거다.\
두 설정은 **각각은 정상적으로 허용된 값**이기 때문이다.\
`setJitter`는 음수만 거부하고, `setInitialInterval`에는 아무 검증도 없다.\
게다가 `jitter`가 0일 때 `initialInterval = 0`은 이미 잘 동작하며 대기 시간 0을 돌려준다.\
즉 사용자 관점에서는 받아들여진 설정인데 실행 시점에 터지는 것이고, 같은 `applyJitter` 안의 두 분기가 서로 다르게 행동하는 비일관성이다.

노출 경로도 이론적이지 않다.\
`RetryPolicy.Builder`가 `delay`를 그대로 `initialInterval`로 넘기고 `@Retryable`은 `delay = 0`을 문서상 허용하므로, `@Retryable(delay = 0, jitter = 100)`처럼 "즉시 재시도하되 몰림만 흩자"는 합리적인 의도가 그대로 런타임 예외로 이어진다.\
더 나쁜 것은 이 예외가 재시도 경로에서 터진다는 점이다.\
재시도 경로는 이미 무언가 실패해서 들어온 자리이므로, 원래의 실패 원인이 `ArithmeticException`에 가려질 수 있다.

## 4. 수정 해설 — 나눗셈을 없애는 대신 배율의 기본값을 정한다

수정은 프로덕션 코드 한 줄이다. 나눗셈을 시도하기 전에 분모를 확인하고, 분모가 0이면 배율을 1로 둔다.

```diff
-				long applicableJitter = jitter * (interval / initialInterval);
+				long applicableJitter = jitter * (initialInterval > 0 ? (interval / initialInterval) : 1);
```

같은 입력(`initialInterval = 0`, `jitter = 100`)을 수정 전후 코드에 각각 넣으면 이렇게 갈린다.

```text
수정 전                                      수정 후
+------------------------------------+    +------------------------------------+
| initialInterval = 0, jitter = 100  |    | initialInterval = 0, jitter = 100  |
| 배율 = 0 / 0  (정수 나눗셈)        |    | 배율 = 1 (분모가 0이라 기본값)     |
| applicableJitter = 100 * (0 / 0)   |    | applicableJitter = 100 * 1 = 100   |
| min = (도달 못 함)                 |    | min = max(0-100, 0) = 0            |
| max = (도달 못 함)                 |    | max = min(0+100, 30000) = 100      |
| -> ArithmeticException: / by zero  |    | -> 0 이상 99 이하의 난수           |
+------------------------------------+    +------------------------------------+
```

같은 설정이 크래시에서 "0에서 jitter 사이의 무작위 지연"으로 바뀐다.

선택의 근거는 "무엇이 이 상황에서 옳은 배율인가"이다.\
`initialInterval`이 0이면 간격은 영원히 자라지 않는다.\
`currentInterval`에 저장되는 값이 0이고, 다음 회차는 `0 * multiplier`라서 어떤 `multiplier`를 줘도 계속 0이기 때문이다.\
자라지 않는 간격에 곱해 줄 확대 배율은 존재할 이유가 없다.\
그래서 배율을 확대 이전의 기본값 1로 고정하고, 설정된 `jitter`를 그대로 적용 폭으로 쓴다.

그 결과 값이 어떻게 나오는지 재현 예시로 확인해 보자.\
`applicableJitter`는 `100 * 1 = 100`이 된다.\
`min`은 `Math.max(0 - 100, 0)`이므로 0이고, `max`는 `Math.min(0 + 100, 30000)`이므로 100이다.\
반환값은 `0 + (long) (Math.random() * 100)`, 즉 0 이상 99 이하의 난수다.\
예외 대신 "0에서 jitter 사이의 무작위 지연"이라는, 의도에 부합하는 결과가 나온다.

기존 동작의 보존은 조건식의 구조 자체가 보장한다.\
`initialInterval > 0`인 모든 경우 표현식은 수정 전과 문자 그대로 동일한 `interval / initialInterval`로 평가되므로, 기본 설정을 포함한 기존 사용자의 숫자는 한 톨도 바뀌지 않는다.\
새 분기는 이전에 예외였던 입력에만 닿는다.

의도적으로 하지 않은 선택도 기록해 둘 가치가 있다.\
`initialInterval = 0`을 아예 `IllegalArgumentException`으로 막는 길도 있었지만 그렇게 하지 않았다.\
그 방향은 이미 열려 있는 이슈 gh-35357 "Add validation support for `FixedBackOff` and `ExponentialBackOff`"의 영역이고, 지금 값을 거부하면 `jitter = 0`으로 잘 쓰고 있던 기존 사용자를 깨뜨린다.\
그래서 이 PR은 런타임 크래시만 좁게 막고 검증 설계와는 직교하도록 범위를 잡았다.

## 5. 검증 — 추가된 테스트가 고정하는 것

테스트는 `ExponentialBackOffTests`에 하나가 추가되었고, 고정하는 명제는 "허용된 두 설정의 조합은 던지지 않는다"이다.\
값의 범위가 아니라 예외 부재를 못 박는다는 점이 중요하다.

> **회귀 테스트(regression test)** — 한 번 고친 결함이 나중에 되살아나지 않는지 지키려고 남겨 두는 테스트.\
> 예: `jitterWithZeroInitialInterval`은 `initialInterval = 0` + `jitter = 100` 조합이 다시 예외를 던지면 즉시 빨간불을 켠다.

```java
	@Test  // gh-36932
	void jitterWithZeroInitialInterval() {
		ExponentialBackOff backOff = new ExponentialBackOff();
		backOff.setInitialInterval(0);
		backOff.setJitter(100);
		BackOffExecution execution = backOff.start();

		// 'initialInterval = 0' and 'jitter > 0' are both individually accepted
		// configurations, so their combination must not throw.
		assertThatNoException().isThrownBy(execution::nextBackOff);
	}
```

`assertThatNoException()`을 고른 이유는 반환값이 난수이기 때문이다.\
반환값은 0에서 99 사이의 어떤 값이든 될 수 있으므로 등호로 고정할 수 없고, 굳이 구간으로 고정하면 검증 대상이 흐려진다.\
이 테스트가 지키려는 계약은 "예외가 아니라 지연 값을 낸다"는 것이고, 어서션이 정확히 그 문장을 표현한다.

> **`assertThatNoException()`** — AssertJ가 제공하는, "이 코드를 돌려도 예외가 나지 않는다"만 단언하는 어서션.\
> 예: 반환값이 난수라 등호로 못 박을 수 없을 때, 값 대신 "던지지 않는다"는 계약만 고정한다.

기존 테스트들은 회귀 방지 역할을 나눠 맡는다.\
`defaultInstance`, `simpleIncrease`, `maxIntervalReached` 등은 `jitter = 0` 경로에서 2000, 3000, 4500과 같은 정확한 수열을 등호로 고정하고 있으므로, 수정이 `initialInterval > 0` 경로의 숫자를 건드렸다면 즉시 빨간불이 켜진다.\
즉 이번 한 줄의 "기존 동작 보존"은 새 테스트가 아니라 이미 있던 테스트들이 증명한다.

## 6. 상태와 교훈

PR의 GitHub 상태는 CLOSED지만 이는 거절이 아니라 Spring 팀의 관행이다.\
메인테이너가 기여 커밋을 직접 백포트 브랜치에 얹어 정리하면서 커밋 메시지에 `Closes gh-36932`를 넣으면, GitHub의 merge 버튼을 거치지 않았으므로 PR은 CLOSED로 남는다.\
실제 반영은 커밋 924849f55b7 "Avoid divide-by-zero in ExponentialBackOff jitter"로 `7.0.x`와 `main` 양쪽에 들어갔고, 작성자는 기여자 본인으로 보존되었다.\
Sam Brannen(sbrannen)의 코멘트가 이 사실과 후속 리비전 0d706f8을 알려 준다.

> **백포트(backport)** — 최신 브랜치에 넣은 수정을 이미 나간 이전 버전 브랜치에도 똑같이 적용하는 것.\
> 예: 이 수정은 `main`뿐 아니라 유지보수 브랜치 `7.0.x`에도 함께 들어갔다.

머지 이후 메인테이너가 이어서 한 작업이 세 갈래인데, 하나의 좁은 수정이 어떻게 주변 정리를 촉발하는지 보여 주는 좋은 사례다.\
시간 순서대로 정리하면 다음과 같다.

- 0d706f8 "Polish contribution": 프로덕션 코드에 왜 배율이 1인지 설명하는 주석 두 줄을 넣고, 테스트에 있던 장황한 설명 주석을 줄이면서 `@Test  // gh-36932`로 이슈 번호를 표기했다.\
  설명은 테스트가 아니라 코드가 있는 자리에 두는 편이 낫다는 편집 판단이다.
- 846a6a8 (gh-36946) "Document behavior for 0 delay combined with jitter": 새 동작을 문서로 승격했다.\
  `setJitter`의 Javadoc, `@Retryable#jitter`, `RetryPolicy.Builder#jitter`, 그리고 레퍼런스 문서 `resilience.adoc`에 "delay가 0이면 전체 jitter가 0에서 `min(jitter, maxDelay)` 사이의 무작위 지연으로 적용된다"는 설명이 동일한 문구로 들어갔다.
- b611fcf (gh-36943) "Use double division to calculate applied jitter": 수정하면서 드러난 정수 나눗셈 자체의 문제를 손봤다.

마지막 항목은 조금 더 볼 가치가 있다.\
배율을 정수로 계산하면 기본 설정에서 `3000 / 2000`이 1이 되어, 간격이 2000에서 4000으로 자라기 전까지 지터 폭이 100에 머문다.\
배율이 매끄럽게 늘지 않고 계단처럼 뛴다.\
메인테이너는 이를 staircase scaling effect라 부르며 실수 나눗셈으로 바꿨고, 그래서 현재 `main`의 코드는 이 PR이 넣은 조건식을 품은 채 한 겹 더 진화해 있다.

> **staircase scaling effect(계단 현상)** — 비율이 매끄럽게 커지지 않고 정수 경계에서만 한 칸씩 뛰는 현상.\
> 예: 간격이 2000에서 4000에 닿기 전까지 배율이 1에 머물러, 지터 폭이 계속 100으로 고정된다.

```java
				long initialInterval = getInitialInterval();
				// When initialInterval is 0 the interval never grows, so the scale factor
				// stays at its baseline value of 1 and the full configured jitter is applied.
				long applicableJitter = (long) (jitter * (initialInterval > 0 ? ((double) interval / initialInterval) : 1));
```

여기서 얻는 교훈은 두 가지다.

첫째, 버그 리포트의 설득력은 스택트레이스가 아니라 **계약의 비일관성**에서 나온다.\
"0으로 나눠서 터진다"만 말했다면 "0을 넣지 마라"는 답으로 끝났을 수 있다.\
이 PR이 받아들여진 이유는 두 설정이 각각 허용되고 `jitter = 0`일 때는 같은 조합이 이미 잘 동작한다는 사실, 즉 같은 메서드의 두 분기가 다르게 행동한다는 점을 근거로 세웠기 때문이다.\
수정의 정당성은 예외가 났다는 사실이 아니라 기존 계약이 스스로 모순된다는 데 있었다.

둘째, 좁게 고치고 인접한 설계 논의와 명시적으로 선을 그으면 리뷰가 빨라진다.\
이 PR은 검증 도입(gh-35357)에 손대지 않고 "어느 쪽으로 검증이 결정되든 호환된다"고 본문에 밝혔다.\
덕분에 리뷰어는 큰 설계 논쟁을 재개하지 않고 한 줄만 판단하면 됐고, 나눗셈 정밀도나 문서화 같은 파생 과제는 각자의 이슈로 분리되어 별도로 처리되었다.

---

연관 ko-docs (모듈 지도): `spring-core/07-유틸리티와-부가-인프라.md`
