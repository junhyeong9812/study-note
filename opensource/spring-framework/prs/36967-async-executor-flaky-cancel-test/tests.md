# PR #36967 — 테스트 해설 (테스트 하나하나)

> PR #36967 테스트 해설. 형식·개념은 ../37153/tests.md, ../37153/guard-tests.md 참조.

이 PR은 프로덕션 코드를 한 줄도 바꾸지 않았고 테스트 메서드 하나만 고쳤으므로, 여기서는 테스트가 부수물이 아니라 **산출물 그 자체**다.\
그래서 red/가드라는 평소의 이분법이 그대로 적용되지 않는다.\
고친 대상은 결함이 아니라 **신호**였고, 바뀐 것은 단언의 내용이 아니라 그 단언이 관측하는 실행 순서의 결정성이다.

> **red 테스트 / 가드 테스트** — red는 "고치기 전에는 반드시 실패하는" 결함 증명용 테스트, 가드는 "고친 뒤 다시 깨지지 않게 지키는" 회귀 방지용 테스트.\
> 예: `taskTerminationTimeoutWithImmediateCancel`은 둘 중 어느 쪽도 아니다 — 고치기 전에도 5만 회 중 49,996회는 통과했기 때문이다.

아래에서는 그 한 건을 수정 전 형태와 수정 후 형태로 나눠 해설하고, 함께 사라진 보조 장치와 기법의 출처, 그리고 이 변경으로 줄어든 커버리지를 어느 테스트가 대신 받는지까지 짚는다.

## 1. taskTerminationTimeoutWithImmediateCancel — 수정 전 (비결정)

수정 전 테스트는 태스크를 제출하자마자 executor를 닫고 `Future`가 취소되었는지 확인하는 형태였다.

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

- **주장**: executor를 닫자마자 제출된 태스크는 시작 전에 취소되고, 그 결과 `future.get()`이 `CancellationException`을 던진다.
- **무엇이 비결정적이었나**: 단언이 성립하려면 `close()`가 `cancelled = true`를 세우는 일이 워커 스레드가 `TaskTrackingRunnable.run()` 첫머리의 `checkCancelled`를 읽는 일보다 **먼저** 일어나야 한다.\
  그런데 쓰기는 테스트 스레드에서, 읽기는 `submit`이 띄운 별도 워커 스레드에서 일어나고, 두 지점 사이에 순서를 강제하는 장치가 테스트 어디에도 없다.\
  `submit` 호출과 try 블록 종료 사이에는 문장이 하나도 없어 두 스레드가 사실상 동시에 출발한다.
- **가시성이 아니라 순서 문제라는 점**: `cancelled`의 쓰기와 읽기는 둘 다 `synchronized (threads)` 안에 있으므로 메모리 가시성은 보장된다.\
  보장되지 않는 것은 둘 중 누가 먼저 모니터를 잡느냐다.\
  이 구분이 중요한데, 가시성 문제라면 `volatile`로 고치겠지만 순서 문제는 그렇게 고쳐지지 않는다.

> **가시성(visibility)** — 한 스레드가 쓴 값을 다른 스레드가 최신 값으로 볼 수 있느냐의 문제.\
> 예: `cancelled`는 `volatile`이 아니지만 쓰기·읽기가 같은 `threads` 모니터 안이라 낡은 `false`가 보이는 일은 없다 — 이 테스트가 흔들린 이유가 아니다.

- **워커가 이기면 어떻게 되나**: `checkCancelled`를 통과할 때 `cancelled`가 아직 false이므로 워커는 자신을 `activeThreads`에 등록하고, 사실상 빈 태스크를 마이크로초 안에 끝낸 뒤 빠져나온다.\
  `FutureTask`는 정상 완료 상태가 되고, 뒤늦은 `future.cancel(false)`는 아무 효과 없이 false를 반환한다.\
  `future.get()`은 예외 대신 `null`을 돌려주고 단언은 "예외가 기대되었으나 없었다"로 실패한다.
- **실측**: 저자가 같은 시나리오를 타이트 루프로 돌린 결과 로컬에서 50,000회당 2~4회 실패했고, 부하가 걸린 CI 러너에서는 더 잦았다.\
  즉 이 테스트는 red도 green도 아니라 확률적으로 둘 다였다.

> **타이트 루프(tight loop)** — 다른 작업 없이 같은 코드만 최대 속도로 반복하는 루프.\
> 예: 실패율이 0.008% 수준이라 단발 실행으로는 재현되지 않으므로, 같은 시나리오를 5만 회 연속으로 돌려 실패 횟수를 세는 방식이 쓰였다.

### 1.1 수정 전 결과를 정하는 두 축

같은 테스트 코드인데 결과가 갈리는 조건을 두 축으로 잡으면 이렇다.\
가로축은 어떤 머신에서 도는가, 세로축은 두 사건 중 무엇이 먼저 도착하는가다.

```text
                  | 로컬 머신              | 부하 걸린 CI 러너
------------------+------------------------+------------------------
close 가 먼저     | 통과                   | 통과
도착              | 50,000회 중 대부분     | 여기도 대부분은 통과
------------------+------------------------+------------------------
워커가 먼저       | 실패                   | 실패
도착              | 50,000회 중 2~4회      | 로컬보다 잦음
```

머신이 바꾸는 것은 결과가 아니라 아래 줄에 떨어질 확률이며, 그래서 로컬에서는 "통과하는 테스트"로 보이고 CI에서만 주기적으로 빨간불이 난다.

## 2. taskTerminationTimeoutWithImmediateCancel — 수정 후 (결정)

수정 후 테스트는 스레드를 아예 띄우지 않고 태스크 래퍼를 가로채, 같은 스레드에서 순서대로 실행한다.

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

- **주장 (첫 단언)**: `close()`가 취소 플래그를 세운 뒤에 래퍼를 실행하면, 래퍼는 사용자 태스크를 실행하기 **전에** `CancellationException`을 던진다.
- **주장 (둘째 단언)**: 그 결과로 `FutureTask`가 취소 상태가 되어 `future.get()`도 같은 예외를 던진다.
- **어떻게 결정론화했나**: 경쟁에서 이기려 한 것이 아니라 경쟁 참가자 하나를 없앴다.\
  익명 서브클래스가 `doExecute`를 오버라이드해 넘어온 `Runnable`을 `AtomicReference`에 저장만 하고 **스레드를 띄우지 않는다**.\
  그러면 시퀀스가 전부 테스트 스레드 한 줄 위에 놓인다.

> **캡처(capture)** — 실행할 대상을 붙잡아만 두고, 언제 실행할지는 잡은 쪽이 나중에 정하는 것.\
> 예: `captured.set(task)`로 `TaskTrackingRunnable`을 보관해 두었다가, `close()`가 끝난 뒤에 `captured.get().run()`으로 직접 돌린다.

  먼저 `submit`이 래퍼를 만들어 캡처하고 반환한다.\
  이어서 try-with-resources가 `close()`를 호출하고, `activeThreads`가 비어 있으므로 `threads.wait(100)`을 건너뛴 채 `cancelled = true`를 세운다.\
  마지막으로 다음 줄에서 테스트 스레드가 직접 `captured.get().run()`을 호출하면 래퍼가 `synchronized (threads)` 안에서 이미 세워진 플래그를 읽는다.\
  쓰기와 읽기가 같은 스레드의 연속된 두 문장이므로 언어 사양이 순서를 보장한다.
- **캡처되는 것이 무엇인지가 핵심**: `execute`는 `activeThreads != null` 분기에서 `doExecute(new TaskTrackingRunnable(taskToUse, future))`를 호출한다.\
  따라서 잡히는 것은 사용자 람다 `() -> {}`가 아니라 **취소 검사를 품고 있는 래퍼**다.\
  검증 대상 로직이 래퍼 안에 있으므로 래퍼를 잡아야 의미가 있고, 사용자 람다를 잡았다면 이 테스트는 아무것도 검증하지 못한다.
- **무엇이 실물로 남았나**: `checkCancelled`가 `future.cancel(false)`를 부르고 `CancellationException`을 던지는 프로덕션 취소 체인 전체가 실제로 실행된다.\
  목킹되거나 우회된 부분은 없다.\
  사라진 것은 `Thread.start()` 한 번뿐이고, 그것은 이 테스트가 검증하려던 대상이 아니다.\
  결정론화를 이유로 검증 대상 자체를 목으로 바꾸면 테스트가 빈 껍데기가 되는데, 여기서는 통제한 것과 실물로 남긴 것의 경계가 정확히 그어져 있다.
- **단언이 둘로 늘어난 이유**: 수정 전에는 예외가 워커 스레드 안에서 삼켜져 테스트가 볼 수 없었고, 그 결과 원인(래퍼가 던진 취소)은 관측하지 못한 채 결과(`future.get()`)만 간접적으로 확인했다.\
  이제 같은 스레드에서 래퍼를 직접 부르므로 원인과 결과를 각각 직접 단언한다.

## 3. 함께 사라진 보조 장치

수정 전 테스트의 `AtomicBoolean finished`와 태스크 본문의 `IllegalStateException`은 단언 대상이 아니라 탐지 장치였다.\
`close()`가 반환하고 `finished.set(true)`가 실행된 뒤에도 태스크 본문이 돌아간다면 "취소되었어야 할 태스크가 뒤늦게 실행됐다"는 뜻이므로, 예외를 던져 눈에 띄게 만든 것이다.\
실행 시점을 통제할 수 없을 때 사후에 그 시점을 추정하려던 우회 수단인 셈이다.

수정 후에는 테스트가 실행 시점을 직접 정하므로 이 장치의 존재 이유가 사라진다.\
태스크 본문도 `() -> {}`로 줄었다.\
결정론화가 단언을 늘리면서 동시에 보조 장치를 지운다는 점이 이 diff의 성격을 잘 보여준다 — 통제권을 얻으면 탐지 장치가 필요 없어진다.

## 4. 기법의 출처와 유지되는 커버리지

캡처 기법 자체는 이 PR에서 발명된 것이 아니다.\
같은 테스트 클래스의 `cancelledThrottledTaskReleasesPermit`가 먼저 같은 방식을 쓰고 있었고, 거기에는 의도를 밝히는 주석이 붙어 있다.

```java
AtomicReference<Runnable> captured = new AtomicReference<>();
// capture the wrapper without running it, to control the cancellation timing
```

즉 이 PR은 새 관용구를 도입한 것이 아니라 같은 파일에 이미 있던 관용구를 인접 테스트에 적용했다.\
리뷰 부담이 낮았던 이유이기도 하다.

반대로 잃은 것도 있다.\
이 테스트는 더 이상 실제 워커 스레드 위에서의 취소를 실행하지 않는다.\
그 커버리지는 같은 클래스의 `taskTerminationTimeoutWithLateInterrupt`, `taskTerminationTimeoutWithEarlyInterrupt`, `cancelRemainingTasksOnClose`가 계속 담당한다 — 이들은 실제 스레드와 인터럽트 경로를 다룬다.\
결정론화가 스위트 전체의 동시성 커버리지를 지운 것이 아니라, 한 테스트에서 그 축을 덜어내고 다른 테스트에 맡긴 배치다.

### 4.1 커버리지 4칸

두 축으로 나눠 보면 어느 칸을 누가 맡는지가 드러난다.\
가로축은 태스크가 실행되는 스레드, 세로축은 취소가 언제 닿는가다.

```text
                     | 인라인 실행            | 실제 워커 스레드
                     | (테스트 스레드에서)    | (Thread.start 이후)
---------------------+------------------------+--------------------------
태스크 시작 전 취소  | 이 PR 이후의           | 수정 전 테스트가 노리던 칸
(checkCancelled)     | taskTermination...     | = 도착 순서가 정해지지
                     | ImmediateCancel        |   않아 결과가 흔들리던 자리
---------------------+------------------------+--------------------------
실행 중 인터럽트     | 해당 없음              | ...WithLateInterrupt
(close 의 interrupt) | 인터럽트할 워커         | ...WithEarlyInterrupt
                     | 스레드가 없다          | cancelRemainingTasksOnClose
```

이 PR은 왼쪽 위 칸으로 옮겨 앉아 결정론을 얻었고, 오른쪽 아래 칸은 원래부터 다른 세 테스트가 실제 스레드로 지키고 있다.

## fixture와 mock

이 테스트의 유일한 대체물은 `doExecute`를 오버라이드한 익명 서브클래스다.\
이것이 흉내 내는 것은 "실행기가 태스크를 실제로 시작하는 순간"이고, 흉내 냄으로써 그 순간의 **타이밍을 테스트 코드가 소유**하게 된다.

중요한 것은 이 오버라이드가 Mockito 목이 아니라 프로덕션이 스스로 열어 둔 확장점이라는 점이다.\
`doExecute`는 "실제 실행 방식을 갈아 끼우라"고 존재하는 protected 템플릿 메서드이므로, 이를 오버라이드하는 것은 프로덕션 계약 바깥으로 나가는 조작이 아니라 계약 안쪽의 정당한 사용이다.

> **Mockito 목(mock)** — 라이브러리가 만들어 주는 가짜 객체. 진짜 구현 대신 끼워 넣어 호출만 기록한다.\
> 예: 여기서는 목을 쓰지 않았다 — `SimpleAsyncTaskExecutor`를 그대로 상속해 `doExecute` 한 메서드만 다르게 구현했을 뿐이라 나머지 로직은 전부 진짜다.

`AtomicReference`는 동시성 때문에 쓴 것이 아니다.\
람다 안에서 바깥 변수에 값을 넣으려면 effectively final 제약을 우회할 홀더가 필요해서 쓴 것이고, 수정 후 이 테스트에는 스레드가 하나뿐이다.

> **effectively final** — 한 번 대입한 뒤 다시 바꾸지 않는 지역 변수. 자바는 람다·익명 클래스 안에서 이런 변수만 참조할 수 있게 허용한다.\
> 예: `Runnable captured;`에 익명 클래스 안에서 대입할 수는 없으므로, 대신 바뀌지 않는 `AtomicReference` 상자를 두고 그 **안의 값**을 바꾼다.

`setTaskTerminationTimeout(100)`은 남아 있지만 수정 후에는 실제로 대기를 유발하지 않는다.\
래퍼를 한 번도 시작하지 않아 `activeThreads`가 계속 비어 있고, `close()`의 `if (!threads.isEmpty())` 검사가 `threads.wait(...)`를 건너뛰기 때문이다.\
테스트가 빨라진 부수 효과가 여기서 나온다.\
값 자체는 "종료 타임아웃이 설정된 실행기"라는 시나리오 조건을 유지하기 위해 남겨진 셈이다.

## 실측·역할 요약

실증은 반복 실행이다.\
수정 전 버전은 50,000회 반복에서 2~4회 실패했고, 수정 후 버전은 50,000회 중 50,000회 통과했다.\
실패율이 1만분의 1 수준이라 단발 실행으로는 어느 쪽도 검증되지 않으므로, 이런 대량 반복이 사실상 유일한 증거 형태다.

역할을 한 줄로 정리하면, 이 PR의 테스트 변경은 결함을 잡는 red 테스트도 회귀를 막는 가드도 아니라, **다른 모든 테스트의 신호를 되살리는 정비**다.\
flaky 테스트는 "빨간불이면 내 변경이 잘못됐다"는 명제를 무너뜨리고, 그 명제가 무너지면 개발자가 빨간불을 재실행으로 넘기는 습관을 들이면서 진짜 회귀까지 함께 통과하게 된다.\
실제로 이 PR의 계기가 그것이었다 — 무관한 PR #36965의 CI가 이 테스트 때문에 빨간불이 됐다.

> **flaky 테스트(플래키 테스트)** — 같은 코드·같은 입력인데 돌릴 때마다 통과와 실패가 오가는 테스트.\
> 예: 이 테스트는 5만 회 중 2~4회만 실패했고, 그 2~4회가 무관한 PR의 CI를 빨갛게 만들었다.
