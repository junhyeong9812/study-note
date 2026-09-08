# PR #36932 — 무대의 실구조와 워크플로우

> PR #36932의 무대가 되는 실구조·워크플로우. 문제·수정은 README.md, 테스트는 tests.md 참조.
>
> 기준: upstream main 526c706d1c3. 이 문서의 `파일:줄` 인용은 모두 이 커밋 기준이며, PR 시점의 base 코드와 다른 곳은 본문에서 명시한다.

이 문서가 다루는 것은 `spring-core`의 백오프(back-off) 계열 세 타입 — `BackOff`, `BackOffExecution`, `ExponentialBackOff` — 이 서로를 어떻게 붙들고 있고, `nextBackOff()` 한 번이 어떤 경로를 지나 밀리초 하나를 만들어 내는가다. PR이 바꾼 줄은 `applyJitter` 안의 한 줄이지만, 그 줄이 왜 그 자리에 있는지는 "설정 객체와 실행 객체를 나눈 구조"와 "지터가 마지막에 덧씌워지는 순서"를 알아야 보인다.

---

## 1. 무대 — 실구조

**백오프 계열은 설정을 담는 전략 객체와 상태를 담는 실행 객체를 물리적으로 분리한 2층 구조다.** 위층 `BackOff`는 설정만 들고 있고 자신은 아무 상태도 갖지 않는다. `start()`를 부를 때마다 아래층 `BackOffExecution`이 새로 찍혀 나오며, 시도 횟수와 현재 간격 같은 가변 상태는 전부 그 아래층에 산다.

```
  org.springframework.util.backoff
  ┌───────────────────────────────────────────────────────────────────┐
  │ interface BackOff                          BackOff.java:48        │
  │   BackOffExecution start()                 BackOff.java:54        │
  └───────────────────────────────────────────────────────────────────┘
        △                                    △
        │ implements                         │ implements
        │                                    │
  ┌─────┴───────────────────────────┐  ┌─────┴───────────────────────┐
  │ FixedBackOff                    │  │ ExponentialBackOff          │
  │   FixedBackOff.java:29          │  │   ExponentialBackOff.java:63│
  │   interval, maxAttempts         │  │   ← 이 PR의 무대            │
  └─────────────────────────────────┘  └──────────┬──────────────────┘
                                                  │
                          설정 필드 6개 (ExponentialBackOff.java:98~108)
                          ┌───────────────────────────────────────────┐
                          │ long   initialInterval = 2000    (:98)    │
                          │ long   jitter          = 0       (:100)   │
                          │ double multiplier      = 1.5     (:102)   │
                          │ long   maxInterval     = 30000   (:104)   │
                          │ long   maxElapsedTime  = MAX     (:106)   │
                          │ long   maxAttempts     = MAX     (:108)   │
                          └───────────────────────────────────────────┘
                                                  │
                                     start()  (ExponentialBackOff.java:262)
                                                  │ new
                                                  ▼
  ┌───────────────────────────────────────────────────────────────────┐
  │ private class ExponentialBackOffExecution                         │
  │                                    ExponentialBackOff.java:279    │
  │   상태 필드 3개                                                    │
  │     long currentInterval    = -1     (:281)  ← "미계산" 표시       │
  │     long currentElapsedTime = 0      (:283)                       │
  │     int  attempts           = 0      (:285)                       │
  │                                                                   │
  │   long nextBackOff()                 (:288)  진입점               │
  │     └─ long computeNextInterval()    (:298)  지수 증가 본체        │
  │          └─ long applyJitter(long)   (:314)  ← PR이 바꾼 메서드   │
  └───────────────────────────────────────────────────────────────────┘
                                                  △
                                                  │ implements
  ┌───────────────────────────────────────────────────────────────────┐
  │ interface BackOffExecution           BackOffExecution.java:30     │
  │   long STOP = -1                     BackOffExecution.java:36     │
  │   long nextBackOff()                 BackOffExecution.java:43     │
  └───────────────────────────────────────────────────────────────────┘
```

이 배치에서 세 가지가 이 PR과 직접 얽힌다.

첫째, **내부 클래스가 `private`이고 바깥 인스턴스를 캡처한다**(`ExponentialBackOff.java:279`). 실행 객체는 설정값을 자기 필드로 복사해 두지 않고 매번 `getInitialInterval()`, `getJitter()`, `getMaxInterval()` 같은 바깥 게터를 호출한다(`:299`, `:302`, `:308`, `:315`, `:317`, `:322`). 그래서 실행 도중 세터가 불리면 그 값이 즉시 다음 계산에 반영된다. `applyJitter`가 `initialInterval`을 직접 다시 읽는 것(`:317`)도 이 때문이다.

둘째, **세터의 검증 강도가 필드마다 다르다.** `setJitter`는 음수를 거부하는 어서션을 갖고 있고(`:165`), `setMultiplier`는 1 미만을 거부한다(`:188~191`). 반면 `setInitialInterval`(`:139~141`), `setMaxInterval`(`:203~205`), `setMaxElapsedTime`(`:220~222`), `setMaxAttempts`(`:243~245`)에는 아무 검증도 없다. 즉 `initialInterval = 0`은 구조적으로 통과하는 값이다.

셋째, **`currentInterval`의 `-1`은 값이 아니라 표시(sentinel)다**(`:281`). 이 필드가 음수인 동안은 "아직 한 번도 계산하지 않음"을 뜻하고, 첫 계산 이후에는 실제 간격이 들어간다. 그래서 첫 회차와 이후 회차의 분기가 이 한 필드로 갈린다(`:301`).

---

## 2. 수정 전 동작 워크플로우

**`nextBackOff()` 한 번은 종료 판정, 지수 증가, 지터 적용의 3단을 차례로 거치고, 지터는 저장되지 않고 반환값에만 얹힌다.** 아래는 기본 설정(`initialInterval = 2000`, `multiplier = 1.5`, `maxInterval = 30000`, `jitter = 0`)으로 세 번 연속 호출했을 때의 실제 흐름이다.

```
 호출자 (예: RetryTemplate.java:153)
   │
   │ execution.nextBackOff()
   ▼
 ExponentialBackOffExecution#nextBackOff            (:288)
   │
   ├─[1] 종료 판정                                   (:289)
   │     currentElapsedTime >= maxElapsedTime ?  또는  attempts >= maxAttempts ?
   │        예 ──▶ return STOP (-1)                  (:290)
   │        아니오 ↓
   │
   ├─[2] computeNextInterval()                       (:292 → :298)
   │        │
   │        ├─ maxInterval = getMaxInterval()        (:299)
   │        ├─ 3분기로 nextInterval 결정             (:301~309)  ← 3절 분기도
   │        ├─ this.currentInterval = nextInterval   (:310)   (*) 지터 적용 "전" 값을 저장
   │        └─ return min(applyJitter(nextInterval), maxInterval)   (:311)
   │                        │
   │                        └─[3] applyJitter(interval)          (:314)
   │                               jitter == 0 이므로 그대로 반환  (:325)
   │
   ├─ currentElapsedTime += nextInterval             (:293)
   ├─ attempts++                                     (:294)
   └─ return nextInterval                            (:295)


 3회 연속 호출의 상태 추이
 ┌──────┬──────────────────┬──────────────────┬───────────────┬──────────┐
 │ 회차 │ 진입 시 current  │ 탄 분기          │ nextInterval  │ 반환값   │
 │      │ Interval         │                  │ (=저장값)     │          │
 ├──────┼──────────────────┼──────────────────┼───────────────┼──────────┤
 │  1   │       -1         │ currentInterval<0│     2000      │   2000   │
 │  2   │      2000        │ else (배수)      │     3000      │   3000   │
 │  3   │      3000        │ else (배수)      │     4500      │   4500   │
 └──────┴──────────────────┴──────────────────┴───────────────┴──────────┘
```

(*) 표시한 `:310`이 이 구조의 핵심 설계 선택이다. `currentInterval`에 저장되는 것은 `applyJitter`를 통과하기 **전** 값이므로, 지터의 무작위성이 다음 회차의 배수 계산에 누적되지 않는다. 지터는 매 회차 마지막에 한 번 덧씌워지는 표면 장식이며, 지수 증가의 뼈대는 결정론적으로 유지된다.

두 번째 시나리오는 이 PR의 무대인 `initialInterval = 0`, `jitter = 100` 조합이다. 아래는 **수정 전** 코드(당시 `:320`이 `long applicableJitter = jitter * (interval / initialInterval);`) 기준의 흐름이다.

```
 backOff.setInitialInterval(0);   ← 검증 없음 (:139)
 backOff.setJitter(100);          ← jitter >= 0 이므로 통과 (:165)
 backOff.start().nextBackOff()
   │
   ├─[1] 종료 판정: elapsed=0, attempts=0 → 통과       (:289)
   │
   ├─[2] computeNextInterval()                          (:298)
   │        currentInterval == -1 → 첫 분기             (:301)
   │        nextInterval = getInitialInterval() = 0     (:302)
   │        this.currentInterval = 0                    (:310)
   │        applyJitter(0) 호출                         (:311)
   │           │
   │           ├─ jitter = 100 > 0 → 지터 블록 진입     (:315~316)
   │           ├─ initialInterval = getInitialInterval() = 0   (:317)
   │           └─ jitter * (interval / initialInterval)
   │                     = 100 * (0 / 0)
   │                              └──▶ ArithmeticException: / by zero
   │                                   ← 결함이 살던 자리
   ▼
 호출자에게 ArithmeticException 전파 (재시도 경로 한복판에서)
```

여기서 `interval`이 0이 되는 것은 우연이 아니라 구조적 귀결이다. `initialInterval`이 0이면 첫 회차 값이 0이고, `:310`이 0을 저장하며, 다음 회차는 `0 * multiplier`(`:308`)라 어떤 배수를 줘도 0에 머문다. 즉 이 설정에서는 간격 자체가 영원히 자라지 않는다. 이 사실이 수정에서 배율의 기본값을 1로 고정한 근거가 된다.

**현재 코드와의 차이**: 현재 `main`의 `:320`은 `long applicableJitter = (long) (jitter * (initialInterval > 0 ? ((double) interval / initialInterval) : 1));`이다. PR이 넣은 삼항 조건은 그대로 남아 있고, 후속 gh-36943이 정수 나눗셈을 `double` 나눗셈으로 바꾸면서 캐스트가 바깥으로 나왔다. 위 흐름의 예외 발생 지점은 PR 시점 base 코드 기준이다.

---

## 3. 분기 처리 워크플로우

**한 번의 `nextBackOff()` 안에는 조건 분기가 세 자리에 있고, 버그는 그중 가장 안쪽인 지터 분기의 나눗셈에 있었다.** 아래 분기도에서 `[BUG]`로 표시한 곳이 결함이 살던 자리다.

```
 nextBackOff()  (:288)
 │
 ├── 분기 A: 종료 조건  (:289)
 │   │
 │   ├─ currentElapsedTime >= maxElapsedTime ────────▶ return STOP (-1)   (:290)
 │   ├─ attempts >= maxAttempts ─────────────────────▶ return STOP (-1)   (:290)
 │   └─ 그 외 ↓
 │
 └── computeNextInterval()  (:298)
     │
     ├── 분기 B: 간격 결정  (:301~309)   3-way
     │   │
     │   ├─ currentInterval < 0                   (:301)   "첫 회차"
     │   │     nextInterval = initialInterval             (:302)
     │   │
     │   ├─ currentInterval >= maxInterval        (:304)   "상한 도달, 고정"
     │   │     nextInterval = maxInterval                 (:305)
     │   │
     │   └─ else                                  (:307)   "배수 증가"
     │         nextInterval = min(currentInterval * multiplier, maxInterval)  (:308)
     │
     ├── this.currentInterval = nextInterval      (:310)  ← 분기와 무관하게 항상 저장
     │
     └── applyJitter(nextInterval)  (:311 → :314)
         │
         └── 분기 C: 지터 적용 여부  (:316)
             │
             ├─ jitter <= 0 ──────────────────────▶ return interval  (:325)
             │                                       (기본 경로. 아무것도 안 함)
             │
             └─ jitter > 0
                  │
                  │  [BUG] 수정 전:  jitter * (interval / initialInterval)
                  │        initialInterval == 0 이면 정수 나눗셈 0/0 → ArithmeticException
                  │        수정 후:  initialInterval > 0 인지 먼저 보고, 아니면 배율 1
                  │
                  ├─ applicableJitter 산출                          (:320)
                  ├─ min = max(interval - applicableJitter, initialInterval)   (:321)
                  ├─ max = min(interval + applicableJitter, maxInterval)       (:322)
                  └─ return min + (long)(Math.random() * (max - min))          (:323)
                       │
                       └─▶ 바깥에서 한 번 더 절단: min(결과, maxInterval)  (:311)
```

분기 B와 분기 C가 서로 독립이라는 점이 결함의 성격을 규정한다. 분기 B가 어느 갈래를 타든 `initialInterval`이 0이면 `nextInterval`은 0이고, 분기 C는 `jitter`만 보고 진입 여부를 정한다. 즉 두 분기는 각각 정상적으로 동작하지만, 조합의 한 칸, 곧 `initialInterval == 0`이면서 `jitter > 0`인 칸이 비어 있었다. 같은 `applyJitter` 안에서 `jitter == 0`인 갈래(`:325`)는 `initialInterval == 0`을 아무 문제 없이 처리하는데 `jitter > 0`인 갈래만 터진다는 비대칭이 그 빈칸의 증거다.

분기 C 안쪽의 절단 두 줄(`:321`, `:322`)도 읽어 둘 가치가 있다. 하한이 `initialInterval`인 것은 "지터가 아무리 작게 흔들어도 최초 대기보다 짧아지지는 않는다"는 규칙이고, 상한이 `maxInterval`인 것은 "지터가 상한을 뚫지 않는다"는 규칙이다. `initialInterval = 0`인 경우 하한 규칙은 자동으로 `max(음수, 0) = 0`이 되어 무해하게 흡수된다.

---

## 4. 스프링 전역에서의 자리

**`ExponentialBackOff`는 `spring-core`의 재시도 지원(`org.springframework.core.retry`)이 기본으로 조립하는 대기 시간 계산기이며, 그 위에 `spring-context`의 `@Retryable` AOP와 `spring-jms`의 리스너 컨테이너 복구 루프가 얹혀 있다.** 아래 세 갈래가 grep으로 실확인한 진입 경로다.

```
 [경로 1] @Retryable 애너테이션 → AOP 인터셉터 → RetryTemplate

   @Retryable(delay=..., jitter=...)            Retryable.java:171, :211
        │
        │  RetryAnnotationBeanPostProcessor$...:105~113
        │    parseDuration(retryable.delay(), ...)   → MethodRetrySpec.delay
        │    parseDuration(retryable.jitter(), ...)  → MethodRetrySpec.jitter
        ▼
   MethodRetrySpec (record, jitter 컴포넌트)     MethodRetrySpec.java:54
        │
        │  AbstractRetryInterceptor:108~118
        │    RetryPolicy.builder().delay(spec.delay()).jitter(spec.jitter())...build()
        ▼
   RetryPolicy.Builder#build()                  RetryPolicy.java:479
        │
        │  커스텀 BackOff가 없으면 ExponentialBackOff를 직접 조립:
        │    new ExponentialBackOff()                       RetryPolicy.java:489
        │    setMaxAttempts(maxRetries)                     RetryPolicy.java:490
        │    setInitialInterval(delay.toMillis())           RetryPolicy.java:491  (*)
        │    setJitter(jitter.toMillis())                   RetryPolicy.java:492  (*)
        │    setMultiplier(multiplier)                      RetryPolicy.java:493
        │    setMaxInterval(maxDelay.toMillis())            RetryPolicy.java:494
        ▼
   RetryTemplate#execute
        retryPolicy.getBackOff().start()          RetryTemplate.java:145
        execution.nextBackOff()                   RetryTemplate.java:153
        == BackOffExecution.STOP ? break          RetryTemplate.java:154
        Thread.sleep(sleepTime)                   RetryTemplate.java:160
```

(*) 표시한 두 줄이 이 PR의 피해 범위를 결정한다. `@Retryable`의 `delay`가 그대로 `initialInterval`로, `jitter`가 그대로 `jitter`로 흘러들어 간다. 그리고 `Retryable.java:200~203`의 Javadoc이 `delay = 0`과 양수 `jitter`의 조합을 명시적으로 문서화하고 있으므로(이 문서 문장 자체는 후속 gh-36946이 추가한 것이다), 그 조합은 사용자에게 열려 있는 설정이다.

```
 [경로 2] 커스텀 BackOff 없이 RetryPolicy만 쓰는 경우

   RetryPolicy 기본 구현                        RetryPolicy.java:83~84
        default BackOff getBackOff() { return new FixedBackOff(DEFAULT_DELAY, DEFAULT_MAX_RETRIES); }
        → 이 경로는 FixedBackOff이므로 지터가 개입하지 않는다.
        → ExponentialBackOff는 Builder를 거칠 때만 등장한다 (RetryPolicy.java:489).

   Builder 기본값                               RetryPolicy.java:153~175
        DEFAULT_MAX_RETRIES = 3      (:153)
        DEFAULT_DELAY       = 1000   (:158)
        DEFAULT_JITTER      = 0      (:164)   ← 기본은 지터 없음
        DEFAULT_MULTIPLIER  = 1.0    (:169)
        DEFAULT_MAX_DELAY   = MAX    (:175)


 [경로 3] spring-jms 리스너 컨테이너의 복구 루프

   DefaultMessageListenerContainer
        BackOffExecution execution = this.backOff.start();   DefaultMessageListenerContainer.java:1154
        applyBackOffTime(execution)                          DefaultMessageListenerContainer.java:1249
             long interval = execution.nextBackOff();        DefaultMessageListenerContainer.java:1254
             interval == BackOffExecution.STOP ? return false
             lifecycleCondition.await(interval, MILLISECONDS)
        → 여기서는 사용자가 setBackOff(...)로 ExponentialBackOff를 직접 주입할 때 무대가 된다.
        → 레퍼런스 문서: framework-docs/modules/ROOT/pages/integration/jms/using.adoc:259
```

세 경로의 공통점은 **`nextBackOff()`가 이미 무언가 실패한 뒤의 복구 경로에서 불린다**는 것이다. `RetryTemplate.java:145`가 초기 시도 실패의 catch 블록 안에서 실행되고, `DefaultMessageListenerContainer.java:1249`가 리스너 복구 시도에서 불린다. 그래서 이 자리에서 던져지는 예외는 원래의 실패 원인을 가리는 성질을 갖는다. `ArithmeticException`이 여기서 터지면 사용자는 "왜 재시도가 안 되는가"가 아니라 "왜 0으로 나누는가"를 먼저 보게 된다.

`ExponentialBackOff` 자체를 직접 참조하는 프로덕션 코드는 grep 기준 `RetryPolicy.java:30`(import)과 `:489`(생성) 한 자리뿐이고, 나머지는 `BackOff` 인터페이스를 통해 간접적으로만 닿는다. 즉 이 클래스는 인터페이스 뒤에 숨은 기본 구현이며, 그 사실이 결함의 노출 폭(직접 호출은 드물지만 기본 경로라 폭넓게 깔려 있음)을 설명한다.

---

## 5. 관련 개념

`../../concepts/`에는 이 문서가 참조할 만한 기존 개념 문서가 없으므로(현재 있는 네 건은 애너테이션 계약·컴파일 층위·JLS·Mockito 주제다), 필요한 개념을 여기에 직접 서술한다.

### 5.1 전략 객체와 실행 객체의 분리

`BackOff`(설정)와 `BackOffExecution`(상태)을 나눈 것은 **하나의 설정을 여러 재시도 시퀀스가 동시에 공유할 수 있게 하려는 배치**다. `BackOffExecution`의 Javadoc이 "Implementations may be stateful but do not need to be thread-safe"(`BackOffExecution.java:23`)라고 못 박은 것이 그 계약이다. 스레드 안전성의 책임은 실행 객체를 공유하지 않는 것으로 해결되고, 그래서 호출자는 재시도 루프에 진입할 때마다 `start()`를 한 번 부른다(`RetryTemplate.java:145`, `DefaultMessageListenerContainer.java:1154`).

이 분리가 테스트에 미치는 영향도 있다. `ExponentialBackOff` 인스턴스에 세터를 아무리 불러도 아무 계산이 일어나지 않으므로, 결함을 재현하려면 반드시 `start()`를 거쳐 `nextBackOff()`를 불러야 첫 회차 경로(`currentInterval == -1`)에 들어간다.

### 5.2 지터와 thundering herd

지터는 계산된 대기 시간 주변으로 난수를 뿌려 **여러 클라이언트의 재시도 시각을 흩어 놓는 장치**다. 지터가 없으면 같은 순간에 실패한 N개의 클라이언트가 정확히 같은 시각에 동시 재시도하고, 이미 무너진 서버를 다시 밀어붙인다. 이것을 thundering herd라 부른다.

`ExponentialBackOff`의 지터 설계에서 눈여겨볼 점은 **지터 폭도 간격과 같은 비율로 자란다**는 것이다(`:320`). 간격이 초기값의 몇 배까지 자랐는지를 배율로 재고, 그 배율만큼 설정된 `jitter`를 확대한다. 간격이 2000에서 30000으로 자랐는데 흔들림 폭이 100ms에 머물면 지터의 분산 효과가 상대적으로 사라지기 때문이다. 이 "비율로 재는" 설계가 곧 나눗셈을 코드에 들여왔고, 분모 검증의 빈칸이 결함이 되었다.

### 5.3 자바 정수 나눗셈의 0 처리

자바에서 정수형(`int`, `long`) 나눗셈의 분모가 0이면 JVM은 `ArithmeticException: / by zero`를 던진다. 반면 부동소수 나눗셈은 예외 대신 `Infinity`나 `NaN`을 만든다. 수정 전 `:320`의 `interval / initialInterval`은 양쪽이 모두 `long`이라 정수 나눗셈이었고, 그래서 `0 / 0`이 즉시 예외가 되었다.

같은 정수 나눗셈이 낳은 두 번째 문제도 이 자리에 있다. 정수 나눗셈은 소수부를 버리므로 기본 설정에서 `3000 / 2000`이 1이 된다. 간격이 2000에서 4000으로 자라기 전까지 배율이 1에 머물러 지터 폭이 계단처럼 뛴다. 이 계단 현상은 후속 gh-36943이 `(double) interval / initialInterval`로 바꾸며 정리했고, 현재 `:320`의 캐스트 위치가 그 흔적이다.

### 5.4 sentinel 값으로서의 음수

`currentInterval = -1`(`:281`)과 `BackOffExecution.STOP = -1`(`BackOffExecution.java:36`)은 둘 다 "의미 있는 밀리초 값이 될 수 없는 음수"를 표시로 쓰는 관용이다. 전자는 내부 상태의 "미계산"을, 후자는 반환값의 "더 이상 재시도하지 말라"를 뜻한다. 대기 시간이 논리상 음수가 될 수 없으므로 이 표시들은 유효값과 충돌하지 않는다.

주의할 점은 두 `-1`이 서로 무관하다는 것이다. `currentInterval`은 절대 밖으로 나가지 않고, `STOP`은 `:290`에서만 반환된다. `applyJitter`가 음수를 낼 수 없는 이유도 `:321`의 하한 절단이 `initialInterval` 아래로 내려가지 못하게 막기 때문이다.
