# PR #36916 — Balance throttle permits in SimpleAsyncTaskExecutor

## 0. 정향

이 PR은 `SimpleAsyncTaskExecutor`의 동시성 제한(throttle)이 조용히 무너지는 두 경로를 막는다. 원인은 하나다. permit을 **획득하는 조건**과 **반납하는 조건**이 서로 달랐다. 획득은 특정 분기에서만 일어나는데 반납은 태스크 래퍼의 `finally`에서 무조건 일어났고, 반대로 반납 코드가 실행되기 전에 예외로 빠져나가는 경로도 있었다. 결과는 카운트가 음수로 내려가 제한이 헐거워지거나, permit이 영구히 새어 제한이 꽉 막히는 것이다.

- PR: https://github.com/spring-projects/spring-framework/pull/36916
- 상태: **OPEN** (2026-06-13 생성, 라벨 `status: waiting-for-triage`, 리뷰 미할당)
- base: `main` / head: `fix/simpleasync-immediate-throttle`
- 변경: +76 / -11, 파일 2개 (프로덕션 1, 테스트 1)
  - `spring-core/src/main/java/org/springframework/core/task/SimpleAsyncTaskExecutor.java`
  - `spring-core/src/test/java/org/springframework/core/task/SimpleAsyncTaskExecutorTests.java`

## 1. 배경 — throttle과 permit 모델

### 1.1 SimpleAsyncTaskExecutor는 풀이 없다

`SimpleAsyncTaskExecutor`는 태스크마다 스레드를 새로 만든다. 클래스 Javadoc이 성격과 대응책을 함께 못박는다.

```java
/**
 * {@link TaskExecutor} implementation that fires up a new Thread for each task.
 * Provides a {@link #setVirtualThreads virtual threads} option on JDK 21+.
 *
 * <p>Supports a graceful shutdown through {@link #setTaskTerminationTimeout},
 * at the expense of task tracking overhead per execution thread at runtime.
 * Supports limiting concurrent threads through {@link #setConcurrencyLimit};
 * by default, the number of concurrent task executions is unlimited.
 * ...
 * <p><b>NOTE: This implementation does not reuse threads!</b>
 */
```

풀이 없다는 것은 곧 "최대 동시 실행 수"를 강제해 주는 자료구조도 없다는 뜻이다. 스레드 풀이라면 max pool size가 구조적으로 상한을 보장하지만, 여기서는 상한을 **별도의 카운터**로 직접 세야 한다. 그 카운터가 throttle이다.

### 1.2 throttle = 카운터 + 락 + 조건변수

동시성 제한 로직 자체는 `SimpleAsyncTaskExecutor`가 아니라 범용 지원 클래스 `org.springframework.util.ConcurrencyThrottleSupport`에 있다. 이 클래스의 Javadoc은 사용 계약을 한 문장으로 요약한다. "`afterAccess`는 보통 `finally` 블록에서 호출해야 한다."

```java
/**
 * Support class for throttling concurrent access to a specific resource.
 *
 * <p>Designed for use as a base class, with the subclass invoking
 * the {@link #beforeAccess()} and {@link #afterAccess()} methods at
 * appropriate points of its workflow. Note that {@code afterAccess}
 * should usually be called in a {@code finally} block!
 */
```

내부 상태는 네 개뿐이다. 락, 조건변수, 한도, 그리고 현재 카운트다.

```java
	private final Lock concurrencyLock = new ReentrantLock();

	private final Condition concurrencyCondition = this.concurrencyLock.newCondition();

	private int concurrencyLimit = UNBOUNDED_CONCURRENCY;

	private int concurrencyCount = 0;
```

`beforeAccess()`가 permit 획득이다. 한도에 도달했으면 `onLimitReached()`를 부르고, 통과하면 카운트를 1 올린다.

```java
	protected void beforeAccess() {
		if (this.concurrencyLimit == NO_CONCURRENCY) {
			onAccessRejected("Concurrency limit set to NO_CONCURRENCY - not allowed to enter");
		}
		if (this.concurrencyLimit > 0) {
			this.concurrencyLock.lock();
			try {
				if (this.concurrencyCount >= this.concurrencyLimit) {
					onLimitReached();
				}
				if (logger.isDebugEnabled()) {
					logger.debug("Entering throttle at concurrency count " + this.concurrencyCount);
				}
				this.concurrencyCount++;
			}
			finally {
				this.concurrencyLock.unlock();
			}
		}
	}
```

기본 `onLimitReached()`는 **자리가 날 때까지 호출 스레드를 블로킹**한다. 큐에 쌓아 두고 돌아가는 방식이 아니라 제출자를 세우는 방식이다.

```java
	protected void onLimitReached() {
		boolean interrupted = false;
		while (this.concurrencyCount >= this.concurrencyLimit) {
			...
			try {
				this.concurrencyCondition.await();
			}
			...
		}
	}
```

`afterAccess()`가 permit 반납이다. 카운트를 1 내리고 대기 중인 스레드 하나를 깨운다.

```java
	protected void afterAccess() {
		if (this.concurrencyLimit >= 0) {
			boolean debug = logger.isDebugEnabled();
			this.concurrencyLock.lock();
			try {
				this.concurrencyCount--;
				...
				this.concurrencyCondition.signal();
			}
			finally {
				this.concurrencyLock.unlock();
			}
		}
	}
```

여기서 permit 모델의 불변식이 하나 도출된다. **`beforeAccess()` 호출 1회당 `afterAccess()` 호출이 정확히 1회**여야 한다. 카운터에는 "누가 몇 개를 들고 있는지"에 대한 소유권 정보가 없으므로, 짝이 어긋나면 아무도 알아채지 못한 채 한도의 의미만 조용히 달라진다.

### 1.3 executor 쪽 어댑터

`SimpleAsyncTaskExecutor`는 이 지원 클래스를 내부 어댑터로 감싸 `protected` 메서드들을 바깥 클래스에서 쓸 수 있게 하고, 거절 정책을 executor의 예외 타입으로 바꾼다.

```java
	private class ConcurrencyThrottleAdapter extends ConcurrencyThrottleSupport {

		@Override
		protected void beforeAccess() {
			super.beforeAccess();
		}

		@Override
		protected void onLimitReached() {
			if (rejectTasksWhenLimitReached) {
				onAccessRejected("Concurrency limit reached: " + getConcurrencyLimit());
			}
			super.onLimitReached();
		}

		@Override
		protected void onAccessRejected(String msg) {
			throw new TaskRejectedException(msg);
		}

		@Override
		protected void afterAccess() {
			super.afterAccess();
		}
	}
```

## 2. 수정 전 동작 방식 — 획득 경로와 반납 경로

### 2.1 획득은 세 갈래 중 한 갈래에서만 일어난다

모든 실행은 결국 deprecated 오버로드 `execute(Runnable, long)`으로 모인다. `execute(Runnable)`과 `submit(...)`도 내부적으로 이 메서드를 `TIMEOUT_INDEFINITE`로 호출한다. 이 메서드가 세 갈래로 갈린다.

```java
		Runnable taskToUse = (this.taskDecorator != null ? this.taskDecorator.decorate(task) : task);
		Future<?> future = (task instanceof Future<?> f ? f : null);
		if (isThrottleActive() && startTimeout > TIMEOUT_IMMEDIATE) {
			this.concurrencyThrottle.beforeAccess();
			try {
				doExecute(new TaskTrackingRunnable(taskToUse, future));
			}
			catch (Throwable ex) {
				// Release concurrency permit if thread creation fails
				this.concurrencyThrottle.afterAccess();
				throw new TaskRejectedException("Failed to start execution thread for task: " + task, ex);
			}
		}
		else if (this.activeThreads != null) {
			doExecute(new TaskTrackingRunnable(taskToUse, future));
		}
		else {
			doExecute(taskToUse);
		}
```

세 갈래를 permit 관점에서 정리하면 다음과 같다. 수정 전 기준이다.

| 분기 | 조건 | `beforeAccess()` 호출 | 래퍼로 감싸는가 |
|---|---|---|---|
| 1 (throttled) | throttle 활성 && `startTimeout > TIMEOUT_IMMEDIATE` | 예 | 예 |
| 2 (tracking-only) | 위가 아니고 `activeThreads != null` | **아니오** | **예** |
| 3 (plain) | 나머지 | 아니오 | 아니오 |

분기 2의 조합이 문제의 씨앗이다. permit은 얻지 않았는데 래퍼는 씌운다.

`activeThreads`가 언제 생기는지도 알아두면 좋다. 종료 대기나 취소를 켜면 생긴다.

```java
	private void trackActiveThreadsIfNecessary() {
		this.activeThreads = (this.taskTerminationTimeout > 0 || this.cancelRemainingTasksOnClose ?
				ConcurrentHashMap.newKeySet() : null);
	}
```

### 2.2 반납은 래퍼의 finally에서 무조건 일어난다

반납 지점은 `TaskTrackingRunnable.run()` 하나다. 수정 전 코드다.

```java
		@Override
		public void run() {
			Set<Thread> threads = activeThreads;
			Thread thread = null;
			if (threads != null) {
				thread = Thread.currentThread();
				synchronized (threads) {
					checkCancelled(this.future);
					threads.add(thread);
				}
			}
			try {
				this.task.run();
			}
			finally {
				if (threads != null) {
					threads.remove(thread);
					if (closed.get()) {
						synchronized (threads) {
							if (threads.isEmpty()) {
								threads.notify();
							}
						}
					}
				}
				concurrencyThrottle.afterAccess();
			}
		}
```

이 코드는 두 가지를 동시에 가정한다. 첫째, 이 래퍼가 만들어졌다면 permit도 하나 획득했을 것이다. 둘째, `run()`에 들어왔다면 `finally`에 반드시 도달할 것이다. **두 가정 모두 성립하지 않는다.** 분기 2가 첫 번째 가정을 깨고, `try` 앞에 놓인 `checkCancelled(this.future)`가 두 번째 가정을 깬다.

`checkCancelled`는 취소 플래그가 서 있으면 예외를 던진다. `close()`가 이 플래그를 세운다.

```java
	private void checkCancelled(@Nullable Future<?> future) {
		if (this.cancelled) {  // within synchronization from TaskTrackingRunnable
			if (future != null) {
				future.cancel(false);
			}
			throw new CancellationException(getClass().getSimpleName() + " has cancelled all remaining tasks");
		}
	}
```

참고로 스레드 생성 실패 경로(`doExecute`가 던지는 경우)는 이미 분기 1의 `catch`에서 permit을 반납하도록 고쳐져 있었고, 그 동작은 기존 테스트 `executeFailsToStartThreadReleasesConcurrencyPermit`이 지키고 있다. 이 PR은 그 옆에 남아 있던 나머지 두 구멍을 막는 작업이다.

## 3. 무엇이 문제였나 — 두 시나리오

### 3.1 획득 없는 반납: 카운트가 음수로 내려간다

첫 번째 시나리오는 분기 2에서 나온다. throttle을 켜고(`setConcurrencyLimit(2)`), 동시에 종료 추적도 켠 상태(`setTaskTerminationTimeout(10_000)`)에서 `execute(task, TIMEOUT_IMMEDIATE)`를 호출하면, 조건 `startTimeout > TIMEOUT_IMMEDIATE`가 거짓이므로 분기 1을 건너뛴다. `activeThreads != null`이므로 분기 2로 들어가 래퍼만 씌운 채 실행된다. permit은 얻지 않았다. 그런데 `run()`의 `finally`는 `afterAccess()`를 부른다. `concurrencyCount`가 -1이 된다.

피해는 **제한이 조용히 헐거워지는 것**이다. 진입 판정이 `concurrencyCount >= concurrencyLimit`이므로, 카운트가 -1로 시작하면 한도 2인 throttle이 실제로는 3개를 동시에 통과시킨다. immediate 태스크를 던질 때마다 카운트는 더 내려가고, 설정한 `concurrencyLimit`과 실제 동시성의 괴리는 계속 벌어진다. 아무 로그도, 아무 예외도 남지 않는다.

이 경로에 도달하려면 deprecated 오버로드 `execute(Runnable, long)`을 직접 써야 한다는 점은 짚어 둘 만하다. 일반적인 `execute(Runnable)`과 `submit(...)`은 `TIMEOUT_INDEFINITE`를 넘기므로 항상 분기 1로 간다. 즉 이 시나리오의 노출면은 좁다.

### 3.2 반납 없는 획득: permit이 영구히 샌다

두 번째 시나리오가 더 넓고 더 아프다. 분기 1을 정상적으로 타서 permit을 하나 얻은 태스크가, 실행 스레드에 도착했을 때 이미 executor가 닫혀 있으면 `checkCancelled`가 `CancellationException`을 던진다. 수정 전 코드에서 이 호출은 `try` **바깥**에 있었다. 따라서 `finally`는 실행되지 않고, `afterAccess()`도 호출되지 않는다. 획득한 permit이 그대로 사라진다.

피해는 앞과 정반대다. **throttle의 유효 용량이 영구히 줄어든다.** 한도 1이라면 한 번의 취소로 카운트가 1에 고정되고, 이후 모든 제출자는 `onLimitReached()`의 `await()`에서 무한히 블로킹된다. 아무도 반납하지 않을 permit을 기다리기 때문이다. `rejectTasksWhenLimitReached`를 켜 두었다면 블로킹 대신 모든 후속 제출이 `TaskRejectedException`으로 거절된다. 어느 쪽이든 executor가 사실상 죽는다.

그리고 이 경로는 `submit(...)`과 `execute(Runnable)` 같은 통상 API로도 도달한다. 필요한 조건은 throttle 활성 + 취소 추적 활성 + 태스크가 스레드에 도달하기 전 `close()` 뿐이다. 종료 시점 경합이라는, 애플리케이션 셧다운마다 실제로 벌어지는 상황이다.

두 시나리오를 한 문장으로 묶으면 이렇다. **permit 획득은 `execute`에서 조건부로 일어나는데, 반납은 `run()`에서 무조건 일어나면서 동시에 예외로 건너뛸 수도 있었다.**

## 4. 수정 해설

수정의 방향은 permit 소유 여부를 **추측하지 말고 기록하자**는 것이다. `execute`가 실제로 `beforeAccess()`를 불렀는지를 래퍼에 명시적으로 넘긴다.

생성자에 `releaseThrottle` 플래그가 추가된다.

```java
		private final boolean releaseThrottle;

		public TaskTrackingRunnable(Runnable task, @Nullable Future<?> future, boolean releaseThrottle) {
			Assert.notNull(task, "Task must not be null");
			this.task = task;
			this.future = future;
			this.releaseThrottle = releaseThrottle;
		}
```

호출부에서는 두 분기가 서로 다른 값을 넘긴다. permit을 얻은 분기 1만 `true`다.

```java
		if (isThrottleActive() && startTimeout > TIMEOUT_IMMEDIATE) {
			this.concurrencyThrottle.beforeAccess();
			try {
				doExecute(new TaskTrackingRunnable(taskToUse, future, true));
			}
			...
		}
		else if (this.activeThreads != null) {
			doExecute(new TaskTrackingRunnable(taskToUse, future, false));
		}
```

`run()`에서는 두 가지가 바뀐다. 첫째, 스레드 추적 블록 전체가 `try` **안으로** 들어간다. 둘째, `afterAccess()`가 플래그 아래로 들어간다.

```java
		@Override
		public void run() {
			Set<Thread> threads = activeThreads;
			Thread thread = null;
			try {
				if (threads != null) {
					thread = Thread.currentThread();
					synchronized (threads) {
						checkCancelled(this.future);
						threads.add(thread);
					}
				}
				this.task.run();
			}
			finally {
				if (threads != null) {
					threads.remove(thread);
					...
				}
				// Release the throttle permit only if one was acquired (see execute),
				// and always release it once acquired -- even if checkCancelled() above threw.
				if (this.releaseThrottle) {
					concurrencyThrottle.afterAccess();
				}
			}
		}
```

두 변경이 각각 하나씩의 시나리오를 막는다. 플래그가 3.1(획득 없는 반납)을, `try` 범위 확장이 3.2(반납 없는 획득)를 막는다. 둘을 합치면 앞서 도출한 불변식이 회복된다. **획득한 permit은 정확히 한 번, 반드시 반납된다.**

`try` 범위를 넓힐 때 걸리는 지점이 하나 있고, 코드는 그것을 피해 간다. `finally`의 `threads.remove(thread)`가 `checkCancelled` 실패 시에도 실행되는데, `thread` 대입이 `synchronized` 블록보다 **앞에** 있으므로 이 시점에 `thread`는 이미 `null`이 아니다. `ConcurrentHashMap.newKeySet()`은 `null` 인자를 거부하므로, 대입 순서가 반대였다면 `finally`에서 `NullPointerException`이 났을 것이다. 아직 집합에 넣지 않은 스레드를 지우는 것이므로 동작상으로는 무해한 no-op이다.

## 5. 검증 — 테스트가 고정하는 것

테스트는 두 개가 추가되며, 둘 다 `concurrencyCount`를 리플렉션으로 직접 읽어 **숫자 자체를 고정**한다. 타이밍이나 데드락 여부로 간접 관찰하지 않는다.

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

첫 번째 테스트가 3.1을 고정한다. `doExecute`를 오버라이드해 래퍼를 **인라인 실행**하므로 스레드가 뜨지 않고, 따라서 관측이 결정론적이다.

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

수정 전이라면 마지막 단언에서 -1이 나온다. 즉 이 테스트는 "immediate 태스크는 throttle 회계를 건드리지 않는다"를 계약으로 못박는다.

두 번째 테스트가 3.2를 고정한다. 이번에는 래퍼를 **붙잡아만 두고 실행하지 않아서**, 취소 플래그를 세운 뒤에 실행하는 타이밍을 테스트가 직접 지배한다.

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

이 테스트는 중간 단언(`isOne()`)으로 permit이 실제로 획득되었음을 먼저 확인한 뒤, 취소 후에도 0으로 돌아오는지를 본다. 획득 자체가 일어나지 않아서 우연히 통과하는 위장 그린을 배제하는 구조다. 수정 전이라면 마지막 단언에서 1이 나온다.

## 6. 상태와 교훈

이 PR은 2026-06-13에 생성되어 현재 **OPEN**이며 `status: waiting-for-triage` 라벨이 붙어 있다. 리뷰는 아직 배정되지 않았고, 기여자 본인의 트리아지용 코멘트 한 건이 달려 있다. 그 코멘트는 실질 피해를 "설정한 동시성 한도가 조용히 지켜지지 않게 되고, 아무것도 그것을 보고하지 않는다"로 요약한다.

교훈 하나. **획득과 반납이 짝을 이루는 리소스는, 획득 조건과 반납 조건이 서로 다른 메서드에 흩어지는 순간 깨진다.** 여기서 `beforeAccess()`는 `execute`의 조건문 안에 있었고 `afterAccess()`는 `run()`의 `finally`에 있었다. 두 조건이 같다는 보장은 코드 어디에도 없었고, 실제로 달랐다. 소유 여부를 상태로 들고 다니게 만든 것이 수정의 본질이다.

교훈 둘. **`finally`는 그것이 감싸는 범위만큼만 보증한다.** `checkCancelled`가 `try` 한 줄 위에 있다는 사실만으로 정리 코드 전체가 무력화되었다. 정리 대상 리소스를 획득한 시점부터 `try`가 시작되어야 한다.

한 문장 덧붙이면, #36967이 같은 테스트 클래스에서 확립한 결정론화 기법(`doExecute` 오버라이드로 래퍼를 가로채 테스트 스레드에서 실행)을 이 PR의 두 테스트가 그대로 재사용한다.

---

연관 ko-docs (모듈 지도): `spring-core/07-유틸리티와-부가-인프라.md`
