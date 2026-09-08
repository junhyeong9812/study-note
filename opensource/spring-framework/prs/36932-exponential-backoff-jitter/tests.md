# PR #36932 — 테스트 해설 (테스트 하나하나)

> PR #36932 테스트 해설. 형식·개념은 ../37153/tests.md, ../37153/guard-tests.md 참조.

이 PR이 `ExponentialBackOffTests`에 추가한 테스트는 한 건이며 성격은 red다. 새 가드를
따로 만들지 않은 것은 이 파일에 이미 정확한 수열을 등호로 고정하는 테스트들이 여러 개
있었기 때문이고, 그 기존 테스트들이 보존 증명을 대신한다. 이 문서는 추가된 한 건을
해설한 뒤, 어느 기존 테스트가 어떤 보존을 책임지는지 지목한다.

## 1. initialInterval 0과 양수 jitter의 조합 — red

이 한 건은 각각은 허용되는 두 설정을 함께 준 뒤 첫 회차를 돌려, 예외가 나지 않는다는 것만 단언한다.

```java
@Test
void jitterWithZeroInitialInterval() {
	// 'initialInterval = 0' and 'jitter > 0' are both individually accepted
	// configurations, so their combination must not throw. With initialInterval
	// of 0, the first nextBackOff() previously evaluated 'jitter * (0 / 0)',
	// resulting in an integer division by zero.
	ExponentialBackOff backOff = new ExponentialBackOff();
	backOff.setInitialInterval(0);
	backOff.setJitter(100);

	BackOffExecution execution = backOff.start();
	assertThatNoException().isThrownBy(execution::nextBackOff);
}
```

- **주장**: `initialInterval = 0`과 `jitter > 0`은 각각 따로는 허용되는 설정이므로, 둘을
  함께 준 뒤 첫 `nextBackOff()`를 불러도 예외가 나면 안 된다. 반환값이 무엇인지는
  주장하지 않는다.
- **fix 전 결과와 이유**: red다. 수정 전 `applyJitter`의 식은
  `long applicableJitter = jitter * (interval / initialInterval);`이었고, 첫 회차에는
  `currentInterval`이 `-1`이라 `nextInterval = getInitialInterval()`, 즉 0이 된다. 그래서
  식이 `100 * (0 / 0)`이 되어 정수 나눗셈이 `ArithmeticException: / by zero`를 던진다.
  단언이 어긋나서 실패하는 것이 아니라 **`assertThatNoException()`이 잡아낸 예외로**
  실패하는 red다.
- **fix 후**: 식이 `jitter * (initialInterval > 0 ? (interval / initialInterval) : 1)`로
  바뀌어 나눗셈이 아예 평가되지 않는다. `applicableJitter`는 `100 * 1 = 100`,
  `min`은 `Math.max(0 - 100, 0) = 0`, `max`는 `Math.min(0 + 100, 30000) = 100`이 되어
  0 이상 99 이하의 난수가 반환된다.
- **왜 값이 아니라 예외 부재를 단언하나**: 반환값이 `Math.random()`에 의존하는
  난수이기 때문이다. 등호로 고정할 수 없고, 구간으로 고정하면 검증 대상이 흐려진다.
  이 테스트가 지키려는 계약은 "허용된 설정 조합이 크래시가 아니라 지연 값을 낸다"이고,
  `assertThatNoException()`이 그 문장을 그대로 표현한다. 난수 때문에 flaky해질 여지가
  없는 형태이기도 하다.
- **목·스텁이 없는 이유**: `ExponentialBackOff`는 밀리초 숫자를 돌려주는 순수 계산기이며
  스스로 잠들지 않는다. 협력 객체가 없으므로 흉내 낼 대상도 없고, 테스트는 실제 객체를
  그대로 조립해 첫 회차만 호출한다.
- **`backOff.start()`를 거치는 이유**: 상태(현재 간격, 누적 시간, 시도 횟수)는 설정
  객체가 아니라 `BackOffExecution`이 들고 있다. `start()`가 실행 상태 객체를 새로
  찍어내므로, 이 호출이 있어야 `currentInterval == -1`인 첫 회차 경로에 들어간다.

## 2. 픽스처가 흉내 내는 실제 상황

이 테스트의 픽스처는 사실상 두 줄의 세터 호출이다. 그러나 그 두 줄이 흉내 내는 실제
상황은 명확하다. `RetryPolicy.Builder#build()`가 사용자 설정을 그대로
`ExponentialBackOff`에 옮겨 붙이는 경로다.

```java
ExponentialBackOff exponentialBackOff = new ExponentialBackOff();
exponentialBackOff.setMaxAttempts(...);
exponentialBackOff.setInitialInterval(this.delay != null ? this.delay.toMillis() : DEFAULT_DELAY);
exponentialBackOff.setJitter(this.jitter != null ? this.jitter.toMillis() : DEFAULT_JITTER);
```

여기서 `delay`가 `initialInterval`로, `jitter`가 그대로 `jitter`로 흘러들어 간다. 그리고
그 위에는 `@Retryable` 애너테이션이 있고, `delay`의 Javadoc은 "Must be greater than or
equal to zero"라고 0을 명시적으로 허용한다. 즉 이 테스트의 두 줄은
`@Retryable(delay = 0, jitter = 100)` — "즉시 재시도하되 몰림만 흩자"는 합리적인 의도 —
을 가장 짧게 옮겨 놓은 것이다. 목으로 대체할 협력 객체가 없으므로, 흉내 내기는 값의
조합을 그대로 재현하는 형태로 이루어진다.

값 100은 임의가 아니라 조건을 만족하는 최소한의 선택이다. 필요한 것은 `jitter > 0`이라는
분기 진입 조건 하나이며, 100은 기본 `maxInterval`인 30000보다 충분히 작아 상한 절단이
개입하지 않는다.

## 3. 보존은 기존 테스트가 증명한다

새 가드가 없는 대신 같은 파일의 기존 테스트들이 그 역할을 나눠 맡는다. 아래는 이 PR의
수정이 건드리지 말아야 할 경로와 그것을 지키는 테스트의 대응이다. 표 앞의 공통 전제는
전부 `jitter`가 기본값 0이라 `applyJitter`의 분기 자체에 들어가지 않는다는 점이다.

| 기존 테스트 | 고정하는 값 | 이 PR에 대해 갖는 의미 |
|---|---|---|
| `defaultInstance` | 2000, 3000, 4500 | 기본 설정의 수열이 그대로인가 |
| `simpleIncrease` | 100, 200, 400, 800 | 배수 증가가 그대로인가 |
| `maxIntervalReached` | 2000, 4000, 4000, 4000 | 상한 절단이 그대로인가 |
| `maxAttemptsReached` | 2000, 4000, STOP | 종료 조건이 그대로인가 |

이 테스트들은 수정 전에도 후에도 green이다. 삼항식의 구조가 그 이유를 보장한다.
`initialInterval > 0`인 모든 호출에서 표현식은 수정 전과 문자 그대로 동일한
`interval / initialInterval`로 평가되므로, 새 분기는 이전에 예외였던 입력에만 닿는다.
즉 이번 한 줄의 "기존 동작 보존"은 새 테스트가 아니라 이미 있던 테스트들이 증명한다.

한 가지 빠진 축은 기록해 둘 만하다. 이 PR 시점의 파일에는 `jitter > 0`이면서
`initialInterval > 0`인 조합을 확인하는 테스트가 없었다. 즉 지터 경로의 양성 가드가
비어 있었고, 그 자리는 후속 gh-36943에서 `jitterScalesProportionallyWithInterval`이
추가되며 채워졌다.

## 4. 머지 후 폴리시

메인테이너가 커밋 0d706f8("Polish contribution")에서 이 테스트를 손봤다. 위 스니펫은
PR diff의 최종 상태이고, 현재 upstream의 같은 테스트는 다음과 같은 모양이다.

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

달라진 점은 세 가지다. `@Test  // gh-36932`로 이슈 번호가 표기되었고, 주석에서
"이전에는 `jitter * (0 / 0)`을 평가했다"는 원인 설명이 빠졌으며, 주석 위치가 단언 바로
앞으로 내려갔다. 원인 설명이 빠진 것은 삭제가 아니라 이동이다. 같은 폴리시 커밋이
프로덕션 코드 쪽에 왜 배율이 1인지를 설명하는 주석을 넣었다.

```java
// When initialInterval is 0 the interval never grows, so the scale factor
// stays at its baseline value of 1 and the full configured jitter is applied.
```

편집 판단은 명확하다. 설명은 테스트가 아니라 그 설명이 필요한 코드가 있는 자리에 둔다.
테스트 주석에는 그 테스트가 무엇을 주장하는지만 남긴다.

## 실측과 역할 요약

이 PR의 테스트 한 건에 대해 확인된 사실과 그 성격을 모아 둔다.

- 실측 기록: PR 본문은 재현 코드와 회귀 테스트 추가 사실을 적었으나 실행 결과 수치는
  남기지 않았다. 총 테스트 수나 실패 건수는 판별 근거 부족으로 남긴다.
- red 1건, 이 PR이 추가한 가드 0건. 보존 증명은 `defaultInstance`, `simpleIncrease`,
  `maxIntervalReached`, `maxAttemptsReached` 등 기존 테스트가 맡는다.
- 이 테스트가 고정하는 명제는 값의 범위가 아니라 예외 부재다. 무작위성이 개입하는
  코드에서 검증 대상을 고를 때의 전형적인 선택이며, 계약을 문장으로 옮기면
  "허용된 설정 조합은 던지지 않는다"가 된다.
