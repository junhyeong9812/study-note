# PR #36916 — 테스트 해설 (테스트 하나하나)

> PR #36916 테스트 해설. 형식·개념은 ../37153/tests.md, ../37153/guard-tests.md 참조.

이 PR은 `SimpleAsyncTaskExecutorTests`에 테스트 두 건과 리플렉션 헬퍼 하나를 추가했다.\
두 건 모두 red이고, 각각 README 3.1(획득 없는 반납)과 3.2(반납 없는 획득)에 정확히 하나씩 대응한다.\
두 테스트의 공통 설계는 **비결정성을 제거하고 카운터 값을 직접 고정**하는 것이다 — 데드락이나 타임아웃 같은 간접 증상으로 관찰하지 않는다.

> **red 테스트** — 수정을 적용하기 전에는 실패하고, 적용한 뒤에 통과하는 테스트.\
> 예: 첫 테스트는 fix 전 `concurrencyCount`가 -1이라 `isZero()` 단언에서 실패한다 — 그래야 그 테스트가 정말 이 결함을 잡고 있음이 증명된다.

## 1. immediate 태스크는 throttle 회계를 건드리지 않는다 — red

첫 테스트는 permit을 얻지 않은 분기로 들어간 태스크가 permit을 반납하지 않는다는 것을 카운터 값으로 못 박는다.

```java
@Test  // immediate-timeout tasks bypass the throttle: no permit acquired, so none released
@SuppressWarnings("deprecation")
void immediateTaskDoesNotReleaseThrottlePermit() throws Exception {
	// doExecute runs the wrapper inline so the throttle accounting is observed deterministically
	SimpleAsyncTaskExecutor executor = new SimpleAsyncTaskExecutor() {
		@Override
		protected void doExecute(Runnable task) {
			task.run();
		}
	};
	executor.setConcurrencyLimit(2);
	executor.setTaskTerminationTimeout(10_000);  // enables active-thread tracking

	executor.execute(() -> {}, AsyncTaskExecutor.TIMEOUT_IMMEDIATE);

	// The task never acquired a permit, so afterAccess() must not have been called.
	assertThat(concurrencyCount(executor)).isZero();
}
```

- **주장**: permit을 얻지 않은 분기(tracking-only)로 실행된 태스크는 permit을 반납해서도
  안 된다. 태스크가 끝난 뒤 `concurrencyCount`는 0이어야 한다.
- **fix 전**: `startTimeout > TIMEOUT_IMMEDIATE`가 거짓이라 분기 1을 건너뛰고
  `beforeAccess()`를 부르지 않는다. 그런데 `activeThreads != null`이므로 래퍼는 씌워지고,
  `run()`의 `finally`가 조건 없이 `afterAccess()`를 호출한다. 카운트는 -1이 되어
  `isZero()` 단언이 실패한다. red다.
- **fix 후**: 이 분기는 `new TaskTrackingRunnable(taskToUse, future, false)`로 만들어지므로
  `releaseThrottle`이 false이고 `afterAccess()`가 호출되지 않는다. 0 유지.

**설정 두 줄이 각각 하나의 조건을 켠다.**\
`setConcurrencyLimit(2)`는 throttle을 활성화해 `isThrottleActive()`를 참으로 만들고, `setTaskTerminationTimeout(10_000)`은 `trackActiveThreadsIfNecessary()`가 `activeThreads` 집합을 만들게 한다.\
이 두 조건이 동시에 켜져 있어야 문제의 분기 2에 도달한다.\
하나만 켜면 분기 3(plain)으로 빠져 래퍼조차 씌워지지 않으므로 버그가 재현되지 않는다.\
즉 설정 두 줄이 재현 조건 명세 그 자체다.

**`TIMEOUT_IMMEDIATE`와 deprecated 오버로드**는 이 시나리오의 유일한 진입로다.\
`execute(Runnable)`이나 `submit(...)`은 항상 `TIMEOUT_INDEFINITE`를 넘기므로 분기 1로 간다.\
`@SuppressWarnings("deprecation")`이 붙은 것은 그래서이고, 동시에 이 결함의 노출면이 좁다는 사실을 코드에 남긴 표시이기도 하다.

## 2. 취소된 throttled 태스크도 permit을 반납한다 — red

둘째 테스트는 반대 방향을 겨눈다.\
permit을 얻은 태스크가 실행 직전에 취소로 이탈해도 그 permit이 돌아오는지를 본다.

```java
@Test  // a throttled task cancelled before it runs must still release its acquired permit
@SuppressWarnings("deprecation")
void cancelledThrottledTaskReleasesPermit() throws Exception {
	AtomicReference<Runnable> captured = new AtomicReference<>();
	// capture the wrapper without running it, to control the cancellation timing
	SimpleAsyncTaskExecutor executor = new SimpleAsyncTaskExecutor() {
		@Override
		protected void doExecute(Runnable task) {
			captured.set(task);
		}
	};
	executor.setConcurrencyLimit(1);
	executor.setCancelRemainingTasksOnClose(true);  // close() marks remaining tasks cancelled

	executor.execute(() -> {}, AsyncTaskExecutor.TIMEOUT_INDEFINITE);  // acquires a permit
	assertThat(concurrencyCount(executor)).isOne();

	executor.close();  // sets the cancelled flag

	// The wrapper hits checkCancelled() and throws before running the task, but the
	// acquired permit must still be released.
	assertThatExceptionOfType(CancellationException.class)
			.isThrownBy(() -> captured.get().run());
	assertThat(concurrencyCount(executor)).isZero();
}
```

- **주장**: permit을 얻은 태스크가 실행 직전에 취소로 예외를 맞아도, 그 permit은 반드시
  반납된다. 예외는 여전히 `CancellationException`으로 호출자에게 전파된다.
- **fix 전**: 마지막 단언에서 실패한다. `checkCancelled(this.future)`가 `try` 블록
  **바깥**에 있어 예외가 나면 `finally`에 도달하지 못하고, `afterAccess()`가 호출되지
  않는다. 카운트는 1에 머문다. 중간 단언(`isOne()`)과 예외 단언은 fix 전에도 통과한다.
- **fix 후**: 추적 블록 전체가 `try` 안으로 들어가 `checkCancelled`가 던져도 `finally`가
  실행되고, `releaseThrottle`이 true이므로 `afterAccess()`가 불려 0으로 돌아온다.

**세 단언의 배치가 이 테스트의 핵심이다.**\
중간 단언 `isOne()`은 위장 그린을 배제한다.\
이 단언이 없으면 "애초에 permit을 얻지 않아서 마지막에 0인" 구현도 통과한다.\
획득해서 1이 되고, 취소를 거쳐, 다시 0으로 돌아오는 **왕복 전체**를 값으로 고정해야 "정확히 한 번 반납"이 증명된다.\
예외 단언은 무회귀 축이다.\
permit을 반납하도록 고치면서 취소 예외를 삼켜 버리는 오수정을 막는다 — 취소는 여전히 시끄러워야 한다.

> **위장 그린(green washing)** — 실제로는 아무것도 검증하지 않았는데 통과해서 안전해 보이는 테스트.\
> 예: 마지막 `isZero()`만 두면 permit을 애초에 얻지 못한 구현도 0이므로 통과한다 — 그래서 중간에 `isOne()`을 세운다.

**`setConcurrencyLimit(1)`을 고른 이유**는 피해의 성격을 드러내기 위해서다.\
한도가 1인데 permit이 새면 유효 용량이 0이 되어 이후 모든 제출자가 `onLimitReached()`의 `await()`에서 영구 블로킹된다.\
테스트는 그 데드락을 실제로 일으키지 않고 카운터 값 1로 대신 관측한다 — 데드락을 재현하는 테스트는 타임아웃에 의존해 느리고 불안정해지기 때문이다.

`setCancelRemainingTasksOnClose(true)`는 두 가지를 동시에 켠다.\
`activeThreads` 집합을 만들어 래퍼가 씌워지게 하고, `close()`가 `cancelled` 플래그를 세우게 한다.\
이 플래그가 `checkCancelled`의 방아쇠다.

두 테스트가 고정하는 카운터의 궤적을 나란히 놓으면 방향이 정반대라는 것이 보인다.

```text
테스트 1 (limit 2, immediate)          테스트 2 (limit 1, 취소)
+----------------------------+        +----------------------------+
| 시작        count = 0      |        | 시작        count = 0      |
| execute     permit 없음    |        | execute     permit 획득    |
| run() 끝                   |        |             count = 1      |
|   fix 전    count = -1     |        | close() 후 run() 이 예외   |
|   fix 후    count =  0     |        |   fix 전    count = 1      |
| 단언        isZero()       |        |   fix 후    count = 0      |
|                            |        | 단언        isZero()       |
+----------------------------+        +----------------------------+
  -> 과다 반납(음수)을 막는다             -> 반납 누락(양수 고착)을 막는다
```

## 3. 두 테스트가 공유하는 결정론화 기법 — `doExecute` 오버라이드

두 테스트 모두 `SimpleAsyncTaskExecutor`를 익명 서브클래스로 만들어 `doExecute`를 가로챈다.\
목적은 같지만 방식은 반대다.

첫 테스트는 `task.run()`으로 **인라인 실행**한다.\
원래라면 새 스레드가 만들어져 태스크를 실행하고, 테스트 스레드는 그 스레드가 끝나기를 기다려야 카운터를 읽을 수 있다.\
인라인 실행은 그 스레드 경계를 없애 `execute()` 반환 시점에 이미 `run()`의 `finally`까지 끝나 있게 만든다.\
대기도 슬립도 없이 카운터를 읽을 수 있다.

둘째 테스트는 `captured.set(task)`로 **붙잡아만 두고 실행하지 않는다.**\
이 시나리오는 "permit을 얻은 태스크가 실행되기 전에 `close()`가 일어난다"는 **순서**가 본질인데, 실제 스레드에 맡기면 그 순서가 스케줄러에 달린 경합이 된다.\
래퍼를 손에 쥐고 있으면 테스트가 직접 `close()` 후에 `run()`을 부를 수 있어 경합이 사라진다.

`doExecute`가 흉내 내는 것은 **스레드 생성과 실행이라는 비결정 요소**다.\
프로덕션에서는 `new Thread(task).start()`가 일어나는 자리이고, 테스트는 그 자리에 "지금 여기서 실행" 또는 "나중에 내가 실행"을 끼워 넣는다.\
검증 대상인 permit 회계는 스레드가 실제로 떠야만 성립하는 로직이 아니라 `execute()`와 `run()`의 코드 경로에만 달려 있으므로, 이 대체가 검증의 유효성을 해치지 않는다.\
README가 적어 둔 대로 이 기법은 같은 테스트 클래스에서 #36967이 확립한 것을 그대로 재사용한 것이다.

두 오버라이드가 스레드 경계를 어떻게 다르게 접는지를 그리면 이렇다.

```text
프로덕션                    테스트 1 (인라인)           테스트 2 (캡처)
-----------------------    -----------------------    -----------------------
execute()                  execute()                  execute()
  beforeAccess()             beforeAccess() 없음        beforeAccess() count=1
  doExecute(래퍼)            doExecute -> task.run()    doExecute -> captured.set
    newThread().start()        같은 스레드에서 끝       아무것도 실행 안 함
  return                     return 시점에 이미        return
    |                        finally 까지 완료           |
    v                          |                       close()  cancelled=true
  워커 스레드 run()            v                         |
  (언제 시작될지 모름)       count 를 바로 읽는다         v
                                                     captured.get().run()
                                                       테스트가 순서를 지배
```

Mockito를 쓰지 않은 이유도 여기서 나온다.\
관측 대상이 협력자 호출 여부가 아니라 **실제 `ConcurrencyThrottleSupport` 인스턴스의 내부 카운트**이므로, 실물 객체를 그대로 두고 실행 타이밍만 통제하는 편이 더 직접적이다.

## 4. 헬퍼 — 카운터를 리플렉션으로 읽는다

두 테스트가 공유하는 헬퍼는 private 필드 두 개를 리플렉션으로 뚫어 `concurrencyCount`를 읽는다.

> **리플렉션(reflection)** — 실행 중에 클래스의 필드·메서드를 이름 문자열로 찾아 접근하는 기능.\
> 예: `getDeclaredField("concurrencyCount")` + `setAccessible(true)`로 private 카운터 값을 테스트에서 직접 읽는다.

```java
private static int concurrencyCount(SimpleAsyncTaskExecutor executor) throws Exception {
	Field throttleField = SimpleAsyncTaskExecutor.class.getDeclaredField("concurrencyThrottle");
	throttleField.setAccessible(true);
	Object throttle = throttleField.get(executor);
	Field countField = ConcurrencyThrottleSupport.class.getDeclaredField("concurrencyCount");
	countField.setAccessible(true);
	return countField.getInt(throttle);
}
```

- **역할**: `concurrencyCount`는 private이고 공개 접근자가 없다. `ConcurrencyThrottleSupport`가
  노출하는 것은 `getConcurrencyLimit()`과 `isThrottleActive()`뿐이라, permit 회계의
  균형을 값으로 확인하려면 리플렉션 외에 방법이 없다.
- **리플렉션을 감수한 판단**: 대안은 두 가지였고 둘 다 나쁘다. 한도만큼 태스크를 채워
  다음 제출이 블로킹되는지 보는 방식은 타임아웃에 의존해 flaky하고, 카운트가 음수로
  내려간 경우(3.1)는 애초에 블로킹이 **덜 일어나는** 방향이라 그 방식으로는 관측조차
  안 된다. 내부 상태를 직접 읽는 것이 이 결함을 결정론적으로 고정하는 유일한 길이다.
- **비용**: 필드 이름에 결합되므로 필드가 바뀌면 테스트가 깨진다. 다만 두 필드 모두
  프레임워크 내부이고 이름이 오래 안정적이었다는 점, 그리고 대안이 flaky 테스트라는 점을
  감안한 선택이다.
- **헬퍼로 뺀 이유**: 두 테스트가 같은 관측을 세 번 수행하므로 중복을 없애고, 테스트
  본문에는 "무엇을 기대하는가"만 남긴다.

> **flaky 테스트** — 코드가 그대로인데도 어떤 날은 통과하고 어떤 날은 실패하는 테스트.\
> 예: 데드락이 걸렸는지를 타임아웃으로 판정하면 머신이 느린 날 거짓 실패가 나온다 — 그래서 카운터 값을 직접 읽는 쪽을 골랐다.

## fixture

새 fixture 클래스는 없다.\
각 테스트가 자기 안에서 익명 서브클래스와 설정 두세 줄로 필요한 상태를 조립한다.\
이 방식이 적절한 이유는 두 시나리오가 **서로 다른 설정 조합**을 요구하기 때문이다.\
첫 테스트는 `concurrencyLimit=2 + taskTerminationTimeout`, 둘째는 `concurrencyLimit=1 + cancelRemainingTasksOnClose`로, 공유 fixture로 묶으면 어느 설정이 어느 재현 조건인지가 흐려진다.\
설정 줄마다 붙은 인라인 주석(`// enables active-thread tracking`, `// close() marks remaining tasks cancelled`)이 그 대응을 명시한다.

> **fixture** — 테스트가 돌기 전에 갖춰 두는 준비 상태(객체·설정).\
> 예: 여기서는 "익명 서브클래스 + `setConcurrencyLimit` + 추적 설정" 두세 줄이 fixture 역할을 하고, 별도 공용 클래스는 두지 않았다.

기존 테스트 `executeFailsToStartThreadReleasesConcurrencyPermit`은 이 PR이 손대지 않았고, 세 번째 permit 누수 경로(스레드 생성 실패)를 계속 지킨다.\
이번 두 테스트와 합치면 `execute`의 세 갈래에서 permit이 어떻게 흐르는지가 전부 테스트로 고정된다.

## 실측·역할 요약

fix 전 기준으로 정리하면 다음과 같다.

| 테스트 | 분류 | fix 전 `concurrencyCount` | 기대값 |
|---|---|---|---|
| `immediateTaskDoesNotReleaseThrottlePermit` | red | -1 | 0 |
| `cancelledThrottledTaskReleasesPermit` | red | 1 | 0 |

가드 테스트는 별도로 추가되지 않았다.\
두 red가 각각 반대 방향의 불균형(과다 반납 / 반납 누락)을 잡고 있어 서로가 서로의 반대편 오수정을 막는 구조이기 때문이다.\
`releaseThrottle` 플래그를 무조건 true로 두면 첫 테스트가 깨지고, 무조건 false로 두거나 `try` 범위를 되돌리면 둘째 테스트가 깨진다.\
여기에 기존 테스트가 스레드 생성 실패 경로를 지키므로, 세 건이 함께 "획득한 permit은 정확히 한 번 반납된다"는 불변식을 값으로 둘러싼다.
