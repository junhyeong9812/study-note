# PR #36967 — Make immediate-cancel task termination test deterministic

## 0. 정향

이 PR은 프로덕션 코드를 한 줄도 건드리지 않고, 테스트 하나가 스레드 스케줄링 운에 의존하던 것을 제거한다. 대상은 `SimpleAsyncTaskExecutorTests.taskTerminationTimeoutWithImmediateCancel` 단 하나이며, 변경은 테스트 메서드 본문 약 12줄이다. 고친 방법은 백그라운드 스레드를 아예 띄우지 않고 태스크 래퍼를 가로채 테스트 스레드에서 직접 실행하는 것이다. 그 12줄이 왜 필요한지 이해하려면 `SimpleAsyncTaskExecutor`의 종료 대기와 취소 메커니즘을 먼저 알아야 하므로, 이 문서는 거기서부터 출발한다.

이 PR의 좌표는 다음 네 가지다.

- PR: https://github.com/spring-projects/spring-framework/pull/36967
- 상태: MERGED (2026-07-12, `bclozel` 머지)
- 머지 커밋: `d01e490b524` (7.0.x), 그 뒤 `bbfe6a04738` (main)
- 변경 파일: `spring-core/src/test/java/org/springframework/core/task/SimpleAsyncTaskExecutorTests.java` (테스트 전용, 프로덕션 동작 불변)

## 1. 배경

### 1.1 SimpleAsyncTaskExecutor는 태스크마다 스레드를 새로 띄운다

`SimpleAsyncTaskExecutor`는 이름 그대로 가장 단순한 `TaskExecutor` 구현이다. 클래스 Javadoc의 첫 문장이 성격을 요약한다.

```java
/**
 * {@link TaskExecutor} implementation that fires up a new Thread for each task.
 * Provides a {@link #setVirtualThreads virtual threads} option on JDK 21+.
 * ...
 * <p><b>NOTE: This implementation does not reuse threads!</b> Consider a
 * thread-pooling TaskExecutor implementation instead, in particular for
 * executing a large number of short-lived tasks.
 */
```

스레드를 실제로 만드는 지점은 `doExecute`이고, 이는 오버라이드를 전제로 한 protected 템플릿 메서드다. 이 확장점이 뒤에서 수정의 핵심 도구가 된다.

```java
	/**
	 * Template method for the actual execution of a task.
	 * <p>The default implementation creates a new Thread and starts it.
	 * @param task the Runnable to execute
	 * @see #newThread
	 * @see Thread#start()
	 */
	protected void doExecute(Runnable task) {
		newThread(task).start();
	}
```

### 1.2 종료 대기(graceful shutdown)를 위해 실행 중 스레드를 추적한다

풀이 없으므로 "종료"라는 개념도 직접 만들어야 한다. `setTaskTerminationTimeout(long)`에 0보다 큰 값을 주면 실행 중 스레드 집합을 추적하기 시작한다.

```java
	private void trackActiveThreadsIfNecessary() {
		this.activeThreads = (this.taskTerminationTimeout > 0 || this.cancelRemainingTasksOnClose ?
				ConcurrentHashMap.newKeySet() : null);
	}
```

`activeThreads`가 `null`이 아니면 `execute`는 사용자 태스크를 그대로 스레드에 넘기지 않고 `TaskTrackingRunnable`이라는 내부 래퍼로 감싼다. `submit`이 만든 `FutureTask`도 이 경로를 탄다.

```java
		Runnable taskToUse = (this.taskDecorator != null ? this.taskDecorator.decorate(task) : task);
		Future<?> future = (task instanceof Future<?> f ? f : null);
		if (isThrottleActive() && startTimeout > TIMEOUT_IMMEDIATE) {
			...
		}
		else if (this.activeThreads != null) {
			doExecute(new TaskTrackingRunnable(taskToUse, future));
		}
		else {
			doExecute(taskToUse);
		}
```

`submit(Runnable)`이 `FutureTask`를 만들어 `execute`에 넘기기 때문에, `execute` 안의 `task instanceof Future<?> f` 검사가 성립한다. 즉 래퍼는 자신이 감싼 태스크에 대응하는 `Future` 핸들을 알고 있다.

### 1.3 취소 플래그와 그것을 읽는 곳

`close()`는 두 가지 일을 한다. 실행 중 스레드가 끝나기를 최대 `taskTerminationTimeout` 만큼 기다리고, 그 뒤 `cancelled` 플래그를 세운 다음 남은 스레드를 인터럽트한다.

```java
	@Override
	public void close() {
		if (this.closed.compareAndSet(false, true)) {
			Set<Thread> threads = this.activeThreads;
			if (threads != null) {
				if (this.cancelRemainingTasksOnClose) {
					synchronized (threads) {
						this.cancelled = true;
					}
					// Early interrupt for remaining tasks on close
					threads.forEach(Thread::interrupt);
				}
				if (this.taskTerminationTimeout > 0) {
					synchronized (threads) {
						try {
							if (!threads.isEmpty()) {
								threads.wait(this.taskTerminationTimeout);
							}
						}
						catch (InterruptedException ex) {
							Thread.currentThread().interrupt();
						}
						this.cancelled = true;
					}
					if (!this.cancelRemainingTasksOnClose) {
						// Late interrupt for remaining tasks after timeout
						threads.forEach(Thread::interrupt);
					}
				}
			}
		}
	}
```

`cancelled`는 `volatile`이 아니라 `activeThreads` 모니터로 보호되는 평범한 boolean이다. 필드 선언에 그 계약이 주석으로 붙어 있다.

```java
	private boolean cancelled = false;  // within activeThreads synchronization
```

플래그를 읽는 쪽은 `TaskTrackingRunnable.run()`의 맨 앞이다. 래퍼는 자기 스레드를 집합에 등록하기 직전에 취소 여부를 확인한다.

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

`checkCancelled`는 아직 시작되지 않은 태스크를 정식으로 취소 처리한다. 대응하는 `Future`가 있으면 `cancel(false)`로 취소 상태를 남기고, 워커 스레드에는 `CancellationException`을 던진다.

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

이 `future.cancel(false)` 경로는 비교적 최근에 들어온 동작이다. Juergen Hoeller의 커밋 `b6833ff31f6` ("Cancel late-executing tasks within revised closed handling", gh-36362)이 `checkCancelled`에 `Future` 인자를 추가하고 던지는 예외를 `TaskRejectedException`에서 `CancellationException`으로 바꾸면서 도입했다. 이번 PR이 다루는 테스트도 바로 그 커밋이 함께 추가한 것이다.

### 1.4 flaky 테스트란 무엇이고 왜 문제인가

flaky 테스트는 같은 코드와 같은 입력에 대해 실행할 때마다 결과가 달라지는 테스트다. 원인은 대개 테스트 밖의 비결정적 요소, 즉 스레드 스케줄링, 실시간 시계, 파일시스템 순서, 네트워크 지연 같은 것들이다.

문제는 실패 자체보다 신호가 망가진다는 데 있다. 테스트 스위트의 존재 이유는 "빨간불이면 내 변경이 잘못됐다"는 명제를 유지하는 것인데, flaky 테스트는 이 명제를 무너뜨린다. 실제로 이 PR의 계기가 그것이었다. 저자가 올린 무관한 PR #36965의 CI가 빨간불이 되었고, 원인은 그 PR의 변경이 아니라 이 테스트였다. 이런 일이 반복되면 개발자는 빨간불을 재실행으로 넘기는 습관을 들이고, 그 순간 진짜 회귀도 함께 통과하게 된다.

## 2. 수정 전 동작 방식

수정 전 테스트는 아래와 같았다. 태스크를 제출하자마자 executor를 닫고, `Future`가 취소되었는지 확인한다.

```java
	@Test
	void taskTerminationTimeoutWithImmediateCancel() {
		AtomicBoolean finished = new AtomicBoolean();
		Future<?> future;
		try (SimpleAsyncTaskExecutor executor = new SimpleAsyncTaskExecutor()) {
			executor.setTaskTerminationTimeout(100);
			future = executor.submit(() -> {
				if (finished.get()) {
					throw new IllegalStateException();
				}
			});
		}
		finished.set(true);
		assertThatExceptionOfType(CancellationException.class).isThrownBy(future::get);
	}
```

의도한 시나리오를 서사로 풀면 이렇다. 테스트 스레드가 `submit`으로 워커 스레드를 하나 띄운다. 워커가 미처 실행에 들어가기 전에 try-with-resources 블록이 끝나면서 `close()`가 호출된다. `close()`는 `activeThreads`가 아직 비어 있으므로 대기 없이 `cancelled = true`를 세우고 빠져나온다. 뒤늦게 깨어난 워커가 `TaskTrackingRunnable.run()` 첫머리의 `checkCancelled`에서 이 플래그를 읽고, `future.cancel(false)`를 호출한 뒤 `CancellationException`을 던진다. 마지막 단언은 이렇게 취소된 `FutureTask`에서 `get()`이 `CancellationException`을 던지는 것을 확인한다.

`finished` 플래그와 `IllegalStateException`은 단언 대상이 아니라 보조 장치였다. `close()`가 반환하고 `finished.set(true)`가 실행된 뒤에도 태스크 본문이 돌아간다면, 그것은 "취소되었어야 할 태스크가 뒤늦게 실행됐다"는 뜻이므로 예외를 던져 눈에 띄게 만든 것이다.

여기서 중요한 것은 이 시나리오 전체가 두 스레드의 도착 순서에 걸려 있다는 점이다. 테스트 코드 어디에도 "워커가 `close()` 이후에 실행되도록" 강제하는 장치가 없다. `submit`과 try 블록 종료 사이에는 문장이 하나도 없으므로 두 스레드가 사실상 동시에 출발한다. 테스트가 원하는 순서는 그중 한 가지 배열일 뿐이다.

## 3. 무엇이 문제였나

문제는 가시성이 아니라 시간 순서다. `cancelled`의 쓰기와 읽기는 둘 다 `synchronized (threads)` 안에서 일어나므로 메모리 가시성은 보장된다. 보장되지 않는 것은 둘 중 무엇이 먼저 모니터를 잡느냐다. 아래 두 인터리빙이 모두 합법이다.

성공 인터리빙에서는 테스트 스레드가 먼저 도착한다. `close()`가 `synchronized (threads)`에 들어가 보니 `threads`가 비어 있어 `wait`를 건너뛰고 `cancelled = true`를 세운다. 그 뒤 워커가 모니터를 잡고 `checkCancelled`에서 플래그를 읽어 `future.cancel(false)`를 호출한다. `FutureTask`는 아직 실행 전이므로 취소가 성립하고, `get()`은 `CancellationException`을 던진다.

실패 인터리빙에서는 워커가 먼저 도착한다. 워커가 `checkCancelled`를 통과할 때 `cancelled`는 아직 `false`다. 워커는 자신을 `threads`에 등록하고, 사실상 아무 일도 하지 않는 태스크 본문을 즉시 끝낸 뒤 자신을 집합에서 제거한다. `FutureTask`는 정상 완료 상태가 된다. 그 뒤 `close()`가 `cancelled = true`를 세우지만 이미 늦었다. `FutureTask.cancel(false)`는 완료된 태스크에 대해 아무 효과 없이 `false`를 반환하고, `future.get()`은 예외 대신 `null`을 돌려준다. 단언이 "CancellationException을 기대했으나 아무 예외도 나오지 않았다"로 실패한다.

이 경쟁에서 워커가 이기기 쉬운 이유는 태스크가 너무 가볍기 때문이다. 태스크 본문은 `AtomicBoolean` 하나를 읽는 것이 전부이므로, 워커가 실행에 들어가기만 하면 마이크로초 단위로 끝난다. 반면 `close()`는 try-with-resources 종료를 거쳐야 하고 모니터 획득도 필요하다. 스레드 시작 지연이 조금만 짧아지면 순서가 뒤집힌다.

부하가 걸린 CI 러너에서 실패가 잦아지는 것도 같은 이유다. 러너에서는 테스트 스레드가 CPU를 빼앗겨 `close()` 진입이 지연되는 폭이 훨씬 커지고, 그만큼 워커가 먼저 도착할 확률이 올라간다. 저자가 PR 본문에 적은 실측은 다음과 같다.

| 조건 | 실패율 |
|------|--------|
| 수정 전, 로컬 50,000회 반복 | 약 2~4회 실패 |
| 수정 전, 부하 걸린 CI 러너 | 로컬보다 잦음 |
| 수정 후, 50,000회 반복 | 0회 실패 |

이 수치가 문제의 성격을 보여준다. 실패율이 1만분의 1 수준이므로 로컬에서 한 번 돌려서는 절대 재현되지 않고, 그럼에도 하루 수십 번 도는 CI에서는 주기적으로 빨간불을 만든다. 재현이 어려운 저확률 실패는 원인 규명 없이 "재실행하면 통과한다"로 처리되기 가장 쉬운 유형이다.

## 4. 수정 해설

수정의 발상은 경쟁을 이기려 하는 대신 경쟁 자체를 없애는 것이다. 두 스레드의 순서를 맞추려고 `sleep`이나 `CountDownLatch`를 끼워 넣는 대신, 스레드를 하나로 줄여 읽기와 쓰기가 프로그램 순서대로 일어나게 만든다.

```java
	@Test
	void taskTerminationTimeoutWithImmediateCancel() {
		AtomicReference<Runnable> captured = new AtomicReference<>();
		Future<?> future;
		try (SimpleAsyncTaskExecutor executor = new SimpleAsyncTaskExecutor() {
			@Override
			protected void doExecute(Runnable task) {
				captured.set(task);
			}
		}) {
			executor.setTaskTerminationTimeout(100);
			future = executor.submit(() -> {});
		}
		assertThatExceptionOfType(CancellationException.class).isThrownBy(captured.get()::run);
		assertThatExceptionOfType(CancellationException.class).isThrownBy(future::get);
	}
```

도구는 1장에서 본 `doExecute` 템플릿 메서드다. 익명 서브클래스가 이를 오버라이드해 넘어온 `Runnable`을 `AtomicReference`에 저장만 하고 아무것도 실행하지 않는다. `execute`가 `activeThreads != null` 분기에서 `doExecute(new TaskTrackingRunnable(taskToUse, future))`를 호출하므로, 잡히는 것은 사용자 람다가 아니라 취소 검사를 담고 있는 `TaskTrackingRunnable` 래퍼다. 이 구분이 핵심이다. 검증 대상 로직이 래퍼 안에 있기 때문에 래퍼를 잡아야 의미가 있다.

이제 시퀀스가 한 스레드 위에서 결정된다. `submit`이 래퍼를 만들어 `captured`에 넣고 즉시 반환한다. try-with-resources가 `close()`를 호출하고, `activeThreads`는 비어 있으므로 `threads.wait(100)`을 건너뛴 채 `cancelled = true`를 세운다. 그 다음 줄에서 테스트 스레드가 직접 `captured.get().run()`을 호출하면, 래퍼는 `synchronized (threads)` 안에서 `checkCancelled`를 실행하고 이미 세워진 플래그를 읽는다. 순서가 코드에 적힌 그대로이므로 뒤집힐 여지가 없다.

검증되는 프로덕션 경로는 그대로다. `checkCancelled`가 `future.cancel(false)`를 부르고 `CancellationException`을 던지는 취소 체인 전체가 실제로 실행되며, 우회하거나 목킹된 부분이 없다. 사라진 것은 `Thread.start()` 한 번뿐이고, 그것은 이 테스트가 검증하려던 대상이 아니다.

단언이 하나에서 둘로 늘어난 것도 의도적이다. 첫 단언은 래퍼가 태스크를 실행하기 전에 `CancellationException`을 던진다는 것을, 둘째 단언은 그 결과로 `FutureTask`가 취소 상태가 되어 `get()`이 같은 예외를 던진다는 것을 확인한다. 원래 테스트는 워커 스레드가 삼킨 예외를 볼 수 없어 둘째 것만 간접적으로 확인할 수 있었다. 이제 원인과 결과를 각각 직접 관찰한다.

`finished`/`IllegalStateException` 보조 장치는 필요가 없어져 삭제됐다. 태스크가 언제 실행되는지를 테스트가 직접 통제하므로, "늦게 실행되었는지"를 사후에 탐지할 이유가 없다. 태스크 본문도 `() -> {}`로 줄었다.

이 캡처 기법 자체는 저자가 같은 클래스를 다루던 관련 작업(`fix/simpleasync-immediate-throttle` 브랜치의 `cancelledThrottledTaskReleasesPermit`)에서 먼저 쓴 것이다. 거기서는 주석이 의도를 명시한다.

```java
		AtomicReference<Runnable> captured = new AtomicReference<>();
		// capture the wrapper without running it, to control the cancellation timing
```

## 5. 검증

고정된 것은 실행 순서다. 수정 전에는 `cancelled` 쓰기와 읽기가 서로 다른 스레드에 있어 순서가 스케줄러 소관이었고, 수정 후에는 같은 스레드의 연속된 두 문장이 되어 언어 사양이 순서를 보장한다. 테스트 결과를 좌우하던 유일한 비결정 요소가 제거된 것이다.

저자가 제시한 실증은 반복 실행이다. 같은 시나리오를 타이트 루프로 돌렸을 때 수정 전에는 50,000회당 2~4회가 실패했고, 수정 후 버전은 50,000회 중 50,000회가 통과했다. 저확률 실패는 단발 실행으로 검증할 수 없으므로 이런 대량 반복이 사실상 유일한 증거 형태다.

부수 효과로 테스트가 빨라졌다. 래퍼를 한 번도 시작하지 않으므로 `activeThreads`가 계속 비어 있고, `close()`의 `if (!threads.isEmpty())` 검사가 `threads.wait(this.taskTerminationTimeout)`을 건너뛴다. 스레드 생성 비용도 사라진다.

반대로 잃은 것도 명시해 둘 만하다. 이 테스트는 더 이상 실제 스레드 위에서의 취소를 실행하지 않으므로, `Thread.start()` 이후의 실제 동시성 동작은 다른 테스트가 담당한다. 같은 클래스의 `taskTerminationTimeoutWithLateInterrupt`, `taskTerminationTimeoutWithEarlyInterrupt`, `cancelRemainingTasksOnClose`가 실제 워커 스레드와 인터럽트 경로를 다루므로 그쪽 커버리지는 유지된다.

## 6. 상태와 교훈

PR은 2026-07-12에 `bclozel`이 머지했고, 별도 리뷰 코멘트나 변경 요청 없이 그대로 반영됐다. 7.0.x에 `d01e490b524`로 들어간 뒤 main에 `bbfe6a04738`로 올라왔다. 프로덕션 코드 변경이 없어 릴리스 노트 대상은 아니다.

교훈은 두 가지다.

첫째, flaky 테스트는 타이밍을 조절해 고치는 것이 아니라 타이밍 의존을 제거해 고친다. `Thread.sleep`을 넣어 워커를 늦추거나 `close()` 전에 대기를 삽입하는 방식은 실패 확률만 낮출 뿐 원인을 남겨 두고, 대신 테스트를 느리게 만들며 더 느린 머신에서 되살아난다. 이 PR은 경쟁의 한쪽 참가자를 없애 확률을 0으로 만들었다. 확률을 낮추는 수정과 조건을 제거하는 수정은 다르며, 후자만이 재발하지 않는다.

둘째, 결정론화의 지렛대는 프로덕션 코드가 이미 열어 둔 확장점이다. `doExecute`는 "실제 실행 방식"을 갈아 끼우라고 존재하는 protected 템플릿 메서드이고, 이를 오버라이드하는 것은 프로덕션 계약 안쪽의 정당한 사용이다. 테스트를 결정론적으로 만들겠다고 검증 대상 로직을 목킹해 버리면 테스트가 아무것도 검증하지 않게 되지만, 여기서는 스레드 생성이라는 검증 대상 밖의 요소만 걷어내고 취소 로직은 실물 그대로 실행했다. 무엇을 통제하고 무엇을 실물로 남길지의 경계를 정확히 긋는 것이 이런 수정의 전부다.

---

연관 ko-docs (모듈 지도): `spring-core/07-유틸리티와-부가-인프라.md`
