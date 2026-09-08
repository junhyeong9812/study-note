# PR #36932 분석 — ExponentialBackOff 지터의 0 나눗셈

> 기준: PR base = upstream `0c60266986`(수정 전) / 머지 커밋 = `924849f55b7`(수정) / 폴리시 = `0d706f8da60`. base와 머지 커밋은 한 줄만 다르므로 아래 줄번호는 두 커밋에서 동일하다. 현재 upstream/main은 후속 gh-36943 이후라 같은 코드가 :320에 있다(§6).
> 중복 회피: 2층 구조와 스프링 전역 배치는 `structure.md` §1·§4, 서사형 설명과 머지 후 이력은 `README.md`, 테스트 해설은 `tests.md`. 이 문서는 이름표 사전(§2.5)과 단계별 값 추적(§3), 대안 기각 근거(§5)를 맡는다.

## 0. 결론

**결함**: `applyJitter`가 "간격이 초기값의 몇 배까지 자랐는가"를 정수 나눗셈 `interval / initialInterval`로 재는데 분모를 검증하지 않아, `initialInterval = 0`과 양수 `jitter`를 함께 설정하면 첫 `nextBackOff()`가 `100 * (0 / 0)`을 평가해 `ArithmeticException: / by zero`를 던졌다.

**수정**: 나눗셈 앞에 분모를 확인하고 분모가 0이면 배율을 확대 이전의 기본값 1로 둔다 — 프로덕션 한 줄(`jitter * (initialInterval > 0 ? (interval / initialInterval) : 1)`)과 회귀 테스트 한 건.

**상태**: 반영 완료. GitHub PR 상태는 CLOSED지만 거절이 아니라 스프링 팀 관행이다 — 메인테이너가 기여 커밋을 직접 브랜치에 얹으면서 메시지에 `Closes gh-36932`를 넣으면 merge 버튼을 거치지 않아 PR이 CLOSED로 남는다. 실제 반영은 `924849f55b7`("Avoid divide-by-zero in ExponentialBackOff jitter", 작성자 보존)로 7.0.x와 main 양쪽에 들어갔고, sbrannen이 `0d706f8da60`("Polish contribution")으로 주석을 다듬었다.

## 1. 무대

변경이 닿는 두 파일부터 못 박아 둔다.

- 모듈: `spring-core`, 패키지 `org.springframework.util.backoff`
- 변경 파일: `spring-core/src/main/java/org/springframework/util/backoff/ExponentialBackOff.java` (1줄) + `spring-core/src/test/java/org/springframework/util/ExponentialBackOffTests.java` (1건 추가)

무대는 2층이다. 위층 `ExponentialBackOff`(:63)는 설정 6개만 들고 자신은 상태가 없고, `start()`(:258)를 부를 때마다 아래층 `private class ExponentialBackOffExecution`(:275)이 새로 찍혀 나온다. 가변 상태(현재 간격, 누적 시간, 시도 횟수)는 전부 아래층에 산다. 결함은 아래층의 가장 안쪽 메서드 `applyJitter`(:310)에 있었다.

공개 진입 API는 `BackOff` 인터페이스가 정의한다.

| 공개 API | 파일:줄 | 역할 | 결함 도달 |
|---|---|---|---|
| `ExponentialBackOff.setInitialInterval(long)` | :139 | 첫 대기 시간 설정. **검증 없음** | 0을 통과시키는 입구 |
| `ExponentialBackOff.setJitter(long)` | :160 | 흔들림 폭 설정. `jitter >= 0`만 검증(:161) | 양수를 통과시키는 입구 |
| `BackOff.start()` | :258 | 실행 객체 생성 | 계산 시작 |
| `BackOffExecution.nextBackOff()` | :284 | 다음 대기 밀리초 또는 `STOP`(-1) | **예외가 터지는 지점** |

부르는 쪽은 세 갈래다. (1) `@Retryable(delay=..., jitter=...)` -> `MethodRetrySpec` -> `RetryPolicy.Builder#build()`가 `setInitialInterval(delay)`·`setJitter(jitter)`를 그대로 흘려보낸다 -> `RetryTemplate`이 `nextBackOff()`를 돌린다. (2) `RetryPolicy.builder()`를 직접 조립하는 경우. (3) `spring-jms`의 `DefaultMessageListenerContainer`가 사용자 주입 `BackOff`를 복구 루프에서 돌리는 경우. 세 경로의 공통점은 **`nextBackOff()`가 이미 무언가 실패한 뒤의 복구 경로에서 불린다**는 것이고, 그래서 여기서 던져지는 예외는 원래 실패 원인을 가린다(경로별 줄번호는 `structure.md` §4).

## 2. 전체 메서드 그래프

아래 그래프는 설정 세터에서 시작해 한 번의 `nextBackOff()`가 지나는 세 단을 편 것이고, `<==` 표시가 결함이 사는 줄이다.

```
 [설정 단계 — 검증이 필드마다 다르다]
   setInitialInterval(0)      :139-141   검증 없음  ------+
   setJitter(100)             :160-163   jitter >= 0 만 검증(:161)  --+
   setMultiplier(m)           :179-182   m >= 1 검증(:184-187)        |
   setMaxInterval(n)          :199-201   검증 없음                    |
                                                                     |
 [실행 단계]                                                          |
   backOff.start()            :258  -> new ExponentialBackOffExecution()
        |                                  currentInterval = -1        :277
        |                                  currentElapsedTime = 0      :279
        |                                  attempts = 0                :281
        v
   execution.nextBackOff()    :284
        |
        +-- [A] 종료 판정                                              :285
        |      currentElapsedTime >= getMaxElapsedTime()  또는
        |      attempts >= getMaxAttempts()          -> return STOP(-1) :286
        |
        +-- computeNextInterval()                                      :288 -> :294
        |      |
        |      +-- [B] 간격 3분기                                      :297-305
        |      |     currentInterval < 0   -> nextInterval = getInitialInterval()  :298
        |      |     currentInterval >= maxInterval -> nextInterval = maxInterval  :301
        |      |     else -> min(currentInterval * multiplier, maxInterval)        :304
        |      |
        |      +-- this.currentInterval = nextInterval    (지터 적용 "전" 값 저장)  :306
        |      |
        |      +-- return min(applyJitter(nextInterval), maxInterval)               :307
        |             |
        |             v
        |          applyJitter(long interval)                                       :310
        |             jitter = getJitter()                                          :311
        |             +-- [C] jitter <= 0 -> return interval  (기본 경로, 무동작)   :319
        |             +-- jitter > 0
        |                   initialInterval = getInitialInterval()                  :313
        |                   applicableJitter = jitter * (interval / initialInterval)  :314  <== 결함
        |                   min = Math.max(interval - applicableJitter, initialInterval) :315
        |                   max = Math.min(interval + applicableJitter, getMaxInterval()):316
        |                   return min + (long)(Math.random() * (max - min))        :317
        |
        +-- currentElapsedTime += nextInterval                                      :289
        +-- attempts++                                                              :290
        +-- return nextInterval                                                     :291
```

데이터 흐름의 핵심은 :306이다. `currentInterval`에 저장되는 것은 **지터를 적용하기 전** 값이므로 무작위성이 다음 회차의 배수 계산으로 누적되지 않는다. 지터는 매 회차 마지막에 덧씌워지는 표면 장식이고, 그래서 `initialInterval = 0`이면 `nextInterval`은 첫 회차에 0이 되고 이후 `0 * multiplier`(:304)로 영원히 0에 머문다 — 이 사실이 §5의 "배율 기본값 1" 선택의 근거가 된다.

## 2.5 핵심 이름표 사전

이 무대에서 헷갈리는 것은 "간격"과 "지터 폭"이 서로 다른 두 축이고, 둘을 잇는 것이 **배율 하나**라는 점이다. 아래 세 표는 각 이름표가 그 세 축(간격 / 배율 / 지터 폭) 중 어디에 속하는지를 명시한다.

### 2.5.1 설정 필드와 상수 (위층 — 상태 없음)

위층 필드에서 눈여겨볼 것은 세터마다 검증 강도가 다르다는 점이다.

| 이름표 | 역할 | 기본값·정해지는 곳 | 누가 언제 읽나 | 이 결함과의 관계 |
|---|---|---|---|---|
| `initialInterval` (:98) | 첫 회차 대기 시간이자 **지터 하한**이자 **배율의 분모**. 세 역할을 겸한다 | 2000(`DEFAULT_INITIAL_INTERVAL` :68) / `setInitialInterval`(:139) — **검증 없음** | `computeNextInterval` :298, `applyJitter` :313 | **결함의 분모.** 0을 막는 코드가 어디에도 없다 |
| `jitter` (:100) | 간격 주변으로 흔들 폭의 기준값 | 0(`DEFAULT_JITTER` :74) / `setJitter`(:160), `jitter >= 0`만 검증(:161) | `applyJitter` :311 | 0이면 :312 분기가 거짓이라 결함 경로에 아예 못 들어간다. **양수여야 발동** |
| `multiplier` (:102) | 회차마다 간격에 곱하는 배수 | 1.5(:79) / `setMultiplier`(:179), `>= 1` 검증(:184-187) | `computeNextInterval` :304 | `initialInterval = 0`이면 어떤 값이어도 `0 * m = 0`이라 무력화된다. 결함 조건에서 간격이 자라지 않는 이유 |
| `maxInterval` (:104) | 간격 상한이자 **지터 상한** | 30000(:84) / `setMaxInterval`(:199) — 검증 없음 | `computeNextInterval` :295, `applyJitter` :316 | 수정 후 `max = min(0+100, 30000) = 100`을 만들어 반환 범위를 정한다 |
| `maxElapsedTime` (:106) / `maxAttempts` (:108) | 종료 조건 두 축 | `Long.MAX_VALUE`(:89,:95) | `nextBackOff` :285 | 기본이 무제한이라 첫 호출은 항상 종료 판정을 통과한다 — 결함이 **첫 호출에서** 터지는 이유 |
| `DEFAULT_JITTER = 0` (:74) | 지터 기본 꺼짐 | 상수 | `jitter` 필드 초기화 | 이 결함이 7.0 이전에는 존재할 수 없었던 이유(지터 자체가 7.0 신설) |

### 2.5.2 실행 상태 필드와 메서드 (아래층 — 상태 있음)

아래층에는 회차마다 갱신되는 상태 셋과 그것을 다루는 메서드 넷이 산다.

| 이름표 | 역할 | 입력 -> 출력 | 누가 언제 부르나 | 이 결함과의 관계 |
|---|---|---|---|---|
| `currentInterval` (:277) | 직전 회차의 **지터 적용 전** 간격. `-1`은 값이 아니라 "아직 미계산" 표시(sentinel) | -1로 시작, :306에서 갱신 | `computeNextInterval` :297,:300,:304 | 첫 회차 분기(:297)를 타게 해서 `nextInterval = initialInterval = 0`을 만든다 |
| `currentElapsedTime` (:279) | 누적 대기 시간 | 0으로 시작, :289에서 += | `nextBackOff` :285 | 첫 호출에서 0이라 종료 판정 통과 |
| `attempts` (:281) | 시도 횟수 | 0으로 시작, :290에서 ++ | `nextBackOff` :285 | 동일 |
| `nextBackOff()` (:284) | 진입점. 종료 판정 후 위임하고 상태를 갱신 | -> 밀리초 또는 `STOP`(-1) | 호출자의 재시도 루프(`RetryTemplate`, JMS 컨테이너) | 예외가 호출자에게 전파되는 경계 |
| `computeNextInterval()` (:294) | 지수 증가 본체. 3분기로 간격을 정하고 저장한 뒤 지터를 얹는다 | -> `min(applyJitter(nextInterval), maxInterval)` | `nextBackOff` :288 | :306의 "지터 전 값 저장"이 이 결함의 성격을 규정한다 |
| `applyJitter(long)` (:310) | 간격 주변 난수 구간을 만들고 하나 뽑는다 | `interval` -> 흔들린 밀리초 | `computeNextInterval` :307 | **결함이 살던 메서드** |
| `getInitialInterval()` (:146) | 위층 설정을 읽는 게터 | -> `initialInterval` | :298과 :313에서 **두 번** 호출 | 실행 객체가 설정을 복사해 두지 않고 매번 다시 읽으므로, 두 호출 사이에 세터가 불리면 값이 달라질 수 있다(이 결함과 무관하나 구조상 사실) |

### 2.5.3 `applyJitter` 안의 지역 변수 (결함의 현장)

결함이 사는 메서드의 지역 변수는 정상 값과 결함 값을 같은 줄에 놓고 봐야 성격이 드러난다.

| 이름표 | 역할 | 계산식 | 정상(기본 설정 3회차) | 결함 케이스(`initialInterval=0`, `jitter=100`) |
|---|---|---|---|---|
| `interval` (파라미터 :310) | 지터를 얹을 대상 간격 | `computeNextInterval`이 정한 값 | 4500 | **0** |
| `jitter` (:311) | 설정된 흔들림 기준값 | `getJitter()` | 0(기본) -> :319로 조기 반환 | 100 -> 지터 블록 진입 |
| `initialInterval` (:313) | 배율의 분모이자 하한 | `getInitialInterval()` | 2000 | **0** |
| `applicableJitter` (:314) | 실제 적용할 흔들림 폭 = 기준값 x 배율 | `jitter * (interval / initialInterval)` | (지터 켰다면) `100 * (4500/2000) = 100 * 2 = 200` | `100 * (0 / 0)` -> **ArithmeticException** |
| `min` (:315) | 난수 구간 하한. "지터가 최초 대기보다 짧게 만들지 않는다" | `Math.max(interval - applicableJitter, initialInterval)` | `max(4300, 2000) = 4300` | 수정 후: `max(0-100, 0) = 0` |
| `max` (:316) | 난수 구간 상한. "지터가 상한을 뚫지 않는다" | `Math.min(interval + applicableJitter, getMaxInterval())` | `min(4700, 30000) = 4700` | 수정 후: `min(0+100, 30000) = 100` |
| 반환값 (:317) | 구간 안의 균등 난수 | `min + (long)(Math.random() * (max - min))` | 4300~4699 | 수정 후: **0~99** |
| 바깥 절단 (:307) | 결과를 한 번 더 상한으로 자름 | `Math.min(applyJitter(...), maxInterval)` | 무영향 | 무영향 |

이 표에서 결함이 한 줄로 보인다. **`applicableJitter`의 배율 항 `interval / initialInterval`은 `long / long` 정수 나눗셈이고, 분모 `initialInterval`은 세터가 검증하지 않는 유일한 축이다.** 같은 메서드 안에서 `jitter == 0`인 갈래(:319)는 `initialInterval == 0`을 아무 문제 없이 처리하는데 `jitter > 0`인 갈래만 터진다는 비대칭이 이 PR의 논거였다.

## 3. 결함 경로 단계 추적

### 3.1 정상 케이스 vs 결함 케이스

정상 케이스는 기본 설정(`initialInterval = 2000`, `multiplier = 1.5`, `jitter = 0`), 결함 케이스는 `setInitialInterval(0)` + `setJitter(100)`이다. 둘 다 `start()` 직후 첫 `nextBackOff()`를 추적한다.

| 단계 | 정상 (기본 설정) | 결함 (`initialInterval=0`, `jitter=100`) |
|---|---|---|
| 진입 상태 | `currentInterval=-1`, `elapsed=0`, `attempts=0` | 동일 |
| :285 종료 판정 | `0 >= MAX`? 거짓 / `0 >= MAX`? 거짓 -> 통과 | 동일하게 통과 |
| :297 간격 분기 | `-1 < 0` 참 -> 첫 회차 | `-1 < 0` 참 -> 첫 회차 |
| :298 `nextInterval` | `getInitialInterval()` = **2000** | `getInitialInterval()` = **0** |
| :306 저장 | `currentInterval = 2000` | `currentInterval = 0` |
| :311 `jitter` | 0 | 100 |
| :312 지터 분기 | `0 > 0` 거짓 -> 블록을 건너뛰고 :319 `return interval`(=2000) | `100 > 0` 참 -> 블록 진입 |
| :313 `initialInterval` | (도달 안 함) | **0** |
| :314 `applicableJitter` | (도달 안 함) | `100 * (0 / 0)` -> **ArithmeticException: / by zero** |
| :307 바깥 절단 | `min(2000, 30000) = 2000` | 도달 못 함 |
| :289-291 | `elapsed=2000`, `attempts=1`, return 2000 | 도달 못 함 — 예외가 호출자로 전파 |

두 번째 회차 이후를 보면 결함 조건에서 간격이 자라지 않는다는 사실도 확인된다. `currentInterval = 0`이므로 :304가 `min((long)(0 * 1.5), 30000) = 0`을 낸다. 어떤 `multiplier`를 줘도 0이다. 즉 이 설정에서 배율 항 `interval / initialInterval`은 **개념적으로도 정의할 대상이 없다**.

### 3.2 수정 후의 같은 경로

같은 결함 케이스를 수정 후 코드로 다시 돌리면 각 줄의 값이 이렇게 정해진다.

| 단계 | 값 |
|---|---|
| :314 배율 항 | `initialInterval > 0`이 거짓 -> **1** (확대 이전 기본값) |
| :314 `applicableJitter` | `100 * 1 = 100` |
| :315 `min` | `Math.max(0 - 100, 0) = 0` (하한 규칙이 음수를 자동 흡수) |
| :316 `max` | `Math.min(0 + 100, 30000) = 100` |
| :317 반환 | `0 + (long)(Math.random() * 100)` = **0 이상 99 이하의 난수** |
| :307 바깥 절단 | `min(0~99, 30000)` = 그대로 |

예외 대신 "0에서 jitter 사이의 무작위 지연"이 나온다. `@Retryable(delay = 0, jitter = 100)`이 의도했을 "즉시 재시도하되 몰림만 흩자"에 정확히 부합한다.

## 4. 계약

이 무대에 걸린 약속 일곱과, 결함이 그중 무엇을 어기는지를 나란히 놓는다.

| 계약 | 출처 | 결함이 어기는가 |
|---|---|---|
| `jitter`는 0 이상이어야 한다 | `setJitter`의 `Assert.isTrue`(:161) | 지킨다 — 결함은 검증 통과 후에 난다 |
| `initialInterval`에는 제약이 없다 | `setInitialInterval`(:139-141)에 검증 코드 부재 | 지킨다. 그리고 **바로 이 사실이 문제** — 세터가 받아들인 값을 실행이 거부한다 |
| "resulting in a value between `interval - jitter` and `interval + jitter` but never below `initialInterval` or above `maxInterval`" | `setJitter` javadoc(:151-154) | 결함 케이스에서 이 계약을 **이행하지 못하고 예외로 이탈**한다. 수정 후에는 `[0, 100)`으로 계약대로 동작한다 |
| "If a `multiplier` is specified, it is applied to the jitter value as well." | `setJitter` javadoc(:155-156) | 이 문장이 배율 항의 존재 이유다. `initialInterval = 0`이면 간격이 자라지 않으므로 "적용할 배수"가 없고, 배율 1이 그 상태의 올바른 표현이다 |
| `@Retryable#delay`는 "Must be greater than or equal to zero" | `Retryable` javadoc | 0이 문서상 허용값이므로 결함 조합이 사용자에게 열려 있었다 |
| `nextBackOff()`는 밀리초 또는 `STOP`(-1)을 돌려준다 | `BackOffExecution` javadoc(:43 부근) | 위반 — 값을 돌려주는 대신 `ArithmeticException`을 던진다 |
| 기존 지터 없는 수열은 2000, 3000, 4500, ... | 기존 테스트 `defaultInstance`·`simpleIncrease`·`maxIntervalReached` | 수정이 이 수열을 건드리면 즉시 red. **보존 증명은 새 테스트가 아니라 기존 테스트가 한다** |

## 5. 수정안

### 5.1 before / after (실파일)

수정은 `applyJitter` 안의 배율 항 한 줄에만 닿는다. 아래 두 스니펫은 실파일에서 그대로 옮긴 것이다.

```java
// before  ExponentialBackOff.java:310-320 (0c60266986)
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

```java
// after (폴리시 0d706f8 포함)  ExponentialBackOff.java:310-322
		private long applyJitter(long interval) {
			long jitter = getJitter();
			if (jitter > 0) {
				long initialInterval = getInitialInterval();
				// When initialInterval is 0 the interval never grows, so the scale factor
				// stays at its baseline value of 1 and the full configured jitter is applied.
				long applicableJitter = jitter * (initialInterval > 0 ? (interval / initialInterval) : 1);
				long min = Math.max(interval - applicableJitter, initialInterval);
				long max = Math.min(interval + applicableJitter, getMaxInterval());
				return min + (long) (Math.random() * (max - min));
			}
			return interval;
		}
```

기여 커밋 `924849f55b7`은 삼항 조건만 넣었고, 설명 주석 두 줄은 sbrannen의 폴리시 `0d706f8da60`이 추가했다.

### 5.2 왜 그 위치인가

수정 지점은 **나눗셈이 있는 자리**여야 한다. 세 후보가 있었다.

1. 세터(`setInitialInterval`)에서 0을 거부한다 -> 계약 변경. `jitter = 0`으로 잘 쓰던 기존 사용자가 깨진다.
2. `computeNextInterval`에서 0을 특별 처리한다 -> 간격 계산 자체는 0에서 아무 문제가 없다. 고장난 것은 지터 쪽이므로 무관한 코드를 건드리게 된다.
3. `applyJitter`의 나눗셈 앞에서 분모를 본다 -> 결함이 있는 표현식과 수정이 같은 줄에 있고, 영향 범위가 그 표현식으로 한정된다.

3을 고른 뒤 남는 질문은 "그럼 배율을 얼마로 둘 것인가"다. 답은 `1`이며 근거는 §3.1의 마지막 관찰이다 — `initialInterval = 0`이면 간격이 영원히 자라지 않으므로 확대할 배수가 존재하지 않고, 확대 이전의 기본값이 곧 옳은 값이다. 폴리시 주석이 이 근거를 그대로 옮겨 적었다.

기존 동작 보존은 조건식의 구조 자체가 보장한다. `initialInterval > 0`인 모든 경우 표현식은 수정 전과 **문자 그대로 동일한** `interval / initialInterval`로 평가된다. 새 분기는 이전에 예외였던 입력에만 닿는다.

### 5.3 검토된 대안과 기각 이유

같은 예외를 다르게 막을 수 있었던 길이 다섯 있었고, 각각 다른 이유로 기각되었다.

| 대안 | 내용 | 기각 이유 |
|---|---|---|
| `setInitialInterval`에서 0 거부 | 입구에서 막는다 | 이미 열린 이슈 gh-35357("Add validation support for FixedBackOff and ExponentialBackOff")의 영역이고, `jitter = 0` + `initialInterval = 0`으로 정상 동작하던 사용자를 깨뜨린다. PR 본문이 "어느 쪽으로 검증이 결정되든 호환된다"고 명시해 이 논쟁을 분리했다 |
| `applicableJitter = 0`으로 두기 | 분모가 0이면 지터를 아예 끈다 | 사용자가 명시적으로 켠 기능을 조용히 무시한다. `min == max == 0`이 되어 반환이 항상 0 — thundering herd 분산이라는 지터의 목적이 사라진다 |
| 배율만 `double`로 바꾸기 | `(double) interval / initialInterval` | **예외는 사라지지만 결과가 조용히 틀린다.** `0.0/0.0`은 `NaN`이고 `100 * NaN`도 `NaN`이며 `(long) NaN`은 **0**이다. 즉 위 대안과 같은 "지터 무음 소실"이 된다. 후속 gh-36943이 double 나눗셈으로 바꾸면서도 **삼항 조건을 남긴 이유**가 정확히 이것이다 |
| `ArithmeticException`을 잡아 폴백 | try/catch | 정상 제어 흐름을 예외로 다룬다. 비용도 비용이지만 "왜 여기서 예외가 나는가"를 코드가 설명하지 못한다 |
| 더 친절한 예외로 치환 | `IllegalStateException("initialInterval must be > 0 when jitter is set")` | 두 설정이 각각 허용되고 `jitter = 0`일 때는 조합이 이미 동작한다는 사실과 충돌한다. 고칠 수 있는 것을 금지로 바꾸는 방향 |

### 5.4 테스트가 고정하는 명제

추가된 회귀 테스트는 값의 범위가 아니라 **예외 부재**를 고정한다. 반환값이 0~99의 난수라 등호로 못 박을 수 없고, 굳이 구간으로 고정하면 검증 대상이 흐려지기 때문이다.

```java
// ExponentialBackOffTests.java (폴리시 0d706f8 이후)
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

가드(양성 방향)는 이 PR이 추가하지 않았다. `initialInterval > 0` 경로의 숫자 보존은 기존 `defaultInstance`·`simpleIncrease`·`maxIntervalReached` 등이 정확한 수열을 등호로 고정해 이미 증명한다. 다만 `jitter > 0`이면서 `initialInterval > 0`인 조합의 양성 가드는 이 시점 파일에 없었고, 그 자리는 후속 gh-36943이 `jitterScalesProportionallyWithInterval`로 채웠다(상세는 `tests.md` §3).

## 6. 범위 밖과 인접 영향

**하위호환.** 공개 시그니처 변화 없음. 동작 변화는 이전에 `ArithmeticException`이던 입력 하나뿐이며, 예외에 의존하던 사용자는 존재할 수 없다. 백포트는 7.0.x와 main 양쪽.

**같은 패턴의 다른 위치.** `org.springframework.util.backoff`의 다른 구현 `FixedBackOff`에는 지터도 배율도 없어 나눗셈 자체가 없다. `ExponentialBackOff` 안에서 나눗셈은 :314 한 곳뿐이며, `computeNextInterval`의 `currentInterval * getMultiplier()`(:304)는 곱셈이라 이 결함 패턴에 해당하지 않는다.

**이 한 줄이 후속 작업 세 갈래를 촉발했고, 전부 2026-06-17에 sbrannen이 처리했다.**

| 커밋 | 이슈 | 내용 | 이 PR과의 관계 |
|---|---|---|---|
| `0d706f8da60` | gh-36932 | "Polish contribution" — 프로덕션에 배율 근거 주석 2줄, 테스트 주석을 단언 앞으로 이동하고 `// gh-36932` 표기 | 같은 이슈의 마무리. 설명은 테스트가 아니라 그 설명이 필요한 코드 자리에 둔다는 편집 판단 |
| `846a6a8f7cc` | gh-36946 | "Document behavior for 0 delay combined with jitter" — `setJitter` javadoc, `@Retryable#jitter`, `RetryPolicy.Builder#jitter`, `resilience.adoc`에 동일 문구 추가 | 새 동작을 **문서로 승격**. 이 PR이 만든 "0 delay + jitter" 조합이 이제 명시적 계약이 되었다 |
| `b611fcf114a` | gh-36943 | "Use double division to calculate applied jitter" — `(long) (jitter * (initialInterval > 0 ? ((double) interval / initialInterval) : 1))` | 정수 나눗셈이 낳은 **두 번째** 문제(계단 현상) 정리. 기본 설정에서 `3000/2000 = 1`이라 간격이 4000에 닿기 전까지 지터 폭이 100에 머무는 현상 |

마지막 항목이 이 PR의 삼항 조건을 그대로 품고 있다는 점이 중요하다. §5.3에서 본 대로 double 나눗셈만으로는 `NaN -> 0`이 되어 지터가 조용히 사라지므로, 분모 가드는 double 전환 이후에도 여전히 필요하다. 현재 upstream/main의 `applyJitter`(:314)와 그 안의 :320이 두 수정의 합성 결과다.

**범위 밖으로 남긴 것.** `setInitialInterval`·`setMaxInterval`·`setMaxElapsedTime`·`setMaxAttempts`의 검증 부재는 gh-35357의 영역으로 남겨 두었다. 이 PR은 "런타임 크래시만 좁게 막고 검증 설계와 직교한다"고 본문에 명시해 리뷰 범위를 한 줄로 좁혔고, 그 결과 파생 과제(정밀도·문서화)가 각자의 이슈로 분리되어 별도로 처리되었다.
