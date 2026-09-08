# PR #36967 분석 — 즉시 취소 종료 테스트의 결정론화

> 기준: 수정 전 = `0c60266986`의 `SimpleAsyncTaskExecutorTests.java:154-168` / 수정 후 = 머지 커밋 `bbfe6a04738`의 같은 파일 :155-170. 프로덕션 파일 `SimpleAsyncTaskExecutor.java`는 이 PR 전후로 바이트 동일하므로 프로덕션 줄번호는 현재 main에서도 그대로 유효하다.
> 중복 회피: 무대 전경과 3분기 흐름은 `structure.md` §1-§3, 서사형 설명과 교훈은 `README.md`, 테스트 diff 해설은 `tests.md`. 이 문서는 이름표 사전(§2.5)과 race 단계 추적(§3), 대안 기각 근거(§5)를 맡는다.

## 0. 결론

**결함**: `taskTerminationTimeoutWithImmediateCancel` 테스트는 `cancelled` 플래그의 **쓰기**(테스트 스레드의 `close()`)와 **읽기**(워커 스레드의 `checkCancelled`) 사이 순서를 강제하는 장치 없이 "쓰기가 먼저 이긴다"고 가정했고, 그 가정이 뒤집히면 태스크가 정상 완료되어 `future.get()`이 예외 대신 `null`을 돌려주면서 간헐 실패했다(로컬 타이트 루프 5만 회 중 2~4회, 부하 걸린 CI에서 더 잦음).

**수정**: `doExecute`를 오버라이드해 워커 스레드를 아예 띄우지 않고 `TaskTrackingRunnable` 래퍼를 캡처한 뒤, `close()`가 플래그를 세운 **다음** 테스트 스레드에서 그 래퍼를 직접 `run()`한다 — 경합의 한쪽 참가자를 없애 순서를 언어가 보장하는 프로그램 순서로 만든다(테스트 전용, +10/-8).

**상태**: MERGED. 2026-07-12 `bclozel` 머지, 7.0.x `d01e490b524` -> main `bbfe6a04738`. 프로덕션 동작 불변이라 릴리스 노트 대상은 아니다.

**주의 — 이 PR의 결함은 프로덕션이 아니라 테스트에 있다.** `SimpleAsyncTaskExecutor`의 취소 로직은 두 인터리빙 모두에서 자기 계약대로 동작한다. 무너진 것은 "빨간불이면 내 변경이 잘못됐다"는 테스트 스위트의 신호 신뢰성이다.

## 1. 무대

이 PR이 손대는 파일과 그 파일이 검증하는 프로덕션 코드는 다음 세 줄로 고정된다.

- 모듈: `spring-core`, 패키지 `org.springframework.core.task`
- 변경 파일(유일): `spring-core/src/test/java/org/springframework/core/task/SimpleAsyncTaskExecutorTests.java`
- 검증 대상 프로덕션: `spring-core/src/main/java/org/springframework/core/task/SimpleAsyncTaskExecutor.java` (무변경)

테스트가 밟는 공개 진입 API는 `submit(Runnable)`(:340)과 `AutoCloseable.close()`(:390) 둘이다. `submit`은 `FutureTask`를 만들어 `execute(future, TIMEOUT_INDEFINITE)`(:342)로 위임하고, `close()`는 try-with-resources 블록 종료로 자동 호출된다. 실제 검증 대상은 그 둘 사이에 낀 내부 클래스 `TaskTrackingRunnable.run()`(:481)의 취소 게이트다.

이 테스트와 취소 프로덕션 코드는 둘 다 메인테이너 Juergen Hoeller가 도입한 것이다 — 프로덕션은 `cff48fff2d6`(2026-02-24), 테스트는 `b6833ff31f6`(2026-02-28, gh-36362 "Cancel late-executing tasks within revised closed handling"). 즉 이 PR은 남의 코드를 고치는 것이 아니라 그 커밋이 함께 넣은 테스트의 타이밍 가정을 보완한다.

동작 조건은 `setTaskTerminationTimeout(100)` 한 줄이 결정한다. 이 값이 0보다 크면 `trackActiveThreadsIfNecessary()`(:283)가 `activeThreads` 집합을 만들고, 그래야 `execute`가 분기 2(:330)를 타서 사용자 람다 대신 `TaskTrackingRunnable` 래퍼를 `doExecute`에 넘긴다. 캡처할 가치가 있는 객체가 래퍼라는 사실이 수정의 성립 조건이다 — 분기 3이었다면 잡히는 것은 취소 검사가 없는 맨 람다일 뿐이다.

## 2. 전체 메서드 그래프

테스트 스레드와 워커 스레드가 각각 어떤 메서드를 밟는지를 두 줄기로 나란히 놓으면, 경합이 일어나는 두 문장이 어디인지 보인다.

```
[테스트 스레드]                                        [워커 스레드 — 수정 후에는 없음]

 setTaskTerminationTimeout(100)                :193
   trackActiveThreadsIfNecessary()             :283
     activeThreads = ConcurrentHashMap.newKeySet()   :284

 submit(Runnable)                              :340
   new FutureTask<>(task, null)                :341
   execute(future, TIMEOUT_INDEFINITE)         :342
     isActive()                                :313
     future = (task instanceof Future<?> f)    :318   -> FutureTask
     isThrottleActive() == false               :319   -> 분기 1 아님
     activeThreads != null                     :330   -> 분기 2
       doExecute(new TaskTrackingRunnable(taskToUse, future))   :331
         |
         +-- [수정 전] newThread(task).start()  :361-362  ===========> run() 시작 :481
         |                                                              |
         +-- [수정 후] captured.set(task)                                |
                       (스레드 생성 없음)                                 |
                                                                        |
 try-with-resources 종료                                                 |
 close()                                       :390                     |
   closed.compareAndSet(false, true)           :391                     |
   threads = activeThreads                     :392                     |
   cancelRemainingTasksOnClose == false        :394                     |
   taskTerminationTimeout(100) > 0             :401                     |
     synchronized (threads) {                  :402                     |
       threads.isEmpty() -> wait 생략          :404                     |
       cancelled = true                        :411  <== 쓰기           |
     }                                                                  |
     threads.forEach(Thread::interrupt)        :415                     |
                                                                        v
 [수정 후] captured.get().run()  <-- 테스트 스레드에서 직접        TaskTrackingRunnable.run() :481
   TaskTrackingRunnable.run()                  :481                   thread = currentThread()  :485
     synchronized (threads) {                  :486                   synchronized (threads) {  :486
       checkCancelled(this.future)             :487  <== 읽기           checkCancelled(future)   :487
         cancelled ?                           :423                       cancelled ?            :423
           future.cancel(false)                :425                          (false 면 통과)
           throw CancellationException         :427                       threads.add(thread)    :488
     }                                                                  try { task.run() }       :492
                                                                        -> FutureTask 정상 완료
 assertThatExceptionOfType(CancellationException.class)
        .isThrownBy(captured.get()::run)       테스트:168
 assertThatExceptionOfType(CancellationException.class)
        .isThrownBy(future::get)               테스트:169
```

수정 전에는 오른쪽 줄기가 실제 스레드였고, `close()`의 `cancelled = true`(:411)와 `checkCancelled`의 읽기(:423)가 **서로 다른 스레드의 두 문장**이라 순서가 스케줄러 소관이었다. 수정 후에는 오른쪽 줄기가 사라지고 두 문장이 같은 스레드의 연속된 코드가 된다.

## 2.5 핵심 이름표 사전

이 무대의 함정은 "가시성은 이미 보장되어 있다"는 점이다. `cancelled`의 쓰기와 읽기는 둘 다 `synchronized (threads)` 안에 있으므로 `volatile`이 없어도 값은 반드시 보인다. 보장되지 않는 것은 **누가 먼저 모니터를 잡는가**다. 아래 표는 각 이름표가 순서 문제의 어느 쪽에 서 있는지를 명시한다.

### 2.5.1 프로덕션 쪽 이름표 (테스트가 실행하는 대상)

먼저 테스트가 실행하는 프로덕션 쪽 이름표 아홉 개다.

| 이름표 | 역할 | 언제 값이 정해지나 | 누가 읽나 | 이 flaky와의 관계 |
|---|---|---|---|---|
| `cancelled` (:101) | "남은 태스크를 취소하라" 신호. `volatile` 아님, `activeThreads` 모니터로만 보호(선언 옆 주석이 계약) | `close()`의 :396(조기) 또는 :411(타임아웃 후). 이 테스트는 :411 | `checkCancelled`(:423) | **경합의 대상 그 자체.** 쓰기와 읽기가 다른 스레드에 있는 한 순서가 미정 |
| `activeThreads` (:93) | 실행 중 워커 집합. `null`이면 추적 안 함 | `trackActiveThreadsIfNecessary()`(:284) — `taskTerminationTimeout > 0`이므로 생성 | `execute` :330, `close()` :392, `run()` :482 | 두 역할을 겸한다. (1) 래퍼를 씌워 캡처 대상을 만든다 (2) `close()`가 `wait`를 건너뛸지 정한다 |
| `closed` (:99) | `AtomicBoolean`. 제출 차단 표시 | `close()`의 CAS(:391) | `isActive()`(:276), `run()`의 finally(:497) | 직접 관련 없음. `submit`이 `close()`보다 앞서므로 제출은 통과한다 |
| `taskTerminationTimeout` (:91) | 종료 대기 밀리초. 테스트는 100 | `setTaskTerminationTimeout(100)` (테스트 :165) | `trackActiveThreadsIfNecessary`(:284), `close()`(:401,:405) | 이 한 줄이 `activeThreads`를 켜서 래퍼 경로를 만든다. **수정 성립의 전제** |
| `doExecute(Runnable)` :361 | 실제 실행 방식. 기본 `newThread(task).start()` | protected 템플릿 메서드 | `execute`의 세 분기 | **수정의 지렛대.** 프로덕션이 오버라이드하라고 열어 둔 확장점이며, 여기가 스레드 경계를 만드는 유일한 자리 |
| `checkCancelled(Future)` :422 | 취소 신호 확인 + 정식 취소 | 호출 시 `cancelled` 읽기 | `run()` :487 (호출자가 이미 모니터 안이라는 전제, :423 주석) | 읽기 쪽 당사자. `future.cancel(false)`(:425) 후 `CancellationException`(:427) |
| `TaskTrackingRunnable` :468 | 사용자 태스크 데코레이터. 취소 검사·등록·해제를 전부 품는다 | `execute` 분기 2(:331)에서 생성 | 워커(수정 전) 또는 테스트 스레드(수정 후) | **비-static 내부 클래스**라 바깥 executor 인스턴스를 암묵 참조한다. 캡처해 두었다가 나중에 실행해도 같은 executor의 `cancelled`를 읽는다 — 캡처 기법이 성립하는 토대 |
| `TaskTrackingRunnable.future` (:472) | 대응 `FutureTask` | 생성자. `submit` 경로라 non-null | `checkCancelled`(:487) | `cancel(false)`의 대상. 두 번째 단언이 관측하는 결과의 출처 |
| `FutureTask` 상태 | NEW -> (CANCELLED | NORMAL) | `cancel(false)` 또는 `task.run()` 완료 | `future.get()` | 두 인터리빙의 결과가 갈리는 최종 관측점. CANCELLED면 `get()`이 던지고, NORMAL이면 `null`을 돌려준다 |

### 2.5.2 테스트 쪽 이름표

다음은 테스트 코드 자체의 이름표이며, 수정 전후 값을 나란히 놓는다.

| 이름표 | 수정 전 | 수정 후 | 역할과 flaky와의 관계 |
|---|---|---|---|
| `finished` (`AtomicBoolean`, 전 :156) | 존재 | **삭제** | 보조 장치였다. `close()` 반환 후에도 태스크 본문이 돌면 `IllegalStateException`을 던져 "늦게 실행됐다"를 눈에 띄게 하려는 것. 단언 대상이 아니었고, 워커 스레드가 예외를 삼키므로 실제 관측력도 약했다 |
| `captured` (`AtomicReference<Runnable>`, 후 :157) | 없음 | 신설 | **수정의 핵심 이름표.** `doExecute`가 받은 래퍼를 여기에 넣어 두고, 실행 시점을 테스트가 지배한다 |
| 익명 서브클래스의 `doExecute` 오버라이드 (후 :160-163) | 없음 | 신설 | `newThread(task).start()`를 `captured.set(task)`로 대체 — 스레드가 생기지 않으므로 경합 참가자가 하나로 준다 |
| 태스크 람다 (전 :160-164 / 후 :166) | `if (finished.get()) throw ...` | `() -> {}` | 수정 전 람다는 `finished` 장치의 일부. 수정 후에는 태스크가 실행되지 않아야 하는 시나리오이므로 본문이 필요 없다 |
| `future` (전 :157 / 후 :158) | `Future<?>` | 동일 | `submit`의 반환. 두 버전 모두 마지막 단언의 대상 |
| 단언 1 (후 :168) | 없음 | `isThrownBy(captured.get()::run)` | **원인**을 직접 관측한다. 래퍼가 태스크 실행 전에 `CancellationException`을 던지는 것 |
| 단언 2 (전 :167 / 후 :169) | `isThrownBy(future::get)` | 동일 | **결과**를 관측한다. 단언 1이 부른 `future.cancel(false)` 때문에 `get()`이 던진다 |

## 3. flaky 메커니즘 단계 추적

핵심은 하나다. `submit` 호출과 try 블록 종료 사이에 문장이 하나도 없어서 두 스레드가 사실상 동시에 출발한다. 테스트가 원하는 것은 두 가능한 배열 중 하나뿐이다.

### 3.1 두 인터리빙

두 스레드의 도착 순서에 따라 갈리는 두 실행 경로를 단계별로 대조한다.

| 단계 | 통과 인터리빙 (close가 이김) | 실패 인터리빙 (워커가 이김) |
|---|---|---|
| `submit` 반환 | 스레드 출발 예약 | 스레드 출발 예약 |
| 모니터 획득 순서 | `close()`가 `synchronized(threads)` :402 선점 | `run()`이 `synchronized(threads)` :486 선점 |
| `threads.isEmpty()` (:404) | true (워커 미등록) -> `wait` 생략 | close가 아직 도달 안 함 |
| `cancelled` 값 | :411에서 `true` | 이 시점 아직 `false` |
| `checkCancelled` (:423) 관측값 | `true` | **`false`** -> 통과 |
| 그 다음 | `future.cancel(false)`(:425) -> `CancellationException`(:427) | `threads.add(thread)`(:488) -> `task.run()`(:492) 즉시 완료 |
| `FutureTask` 상태 | CANCELLED | **NORMAL** |
| 뒤늦은 `close()` | 이미 끝남 | `cancelled = true`를 세우지만 무효. `FutureTask.cancel(false)`는 완료된 태스크에 `false` 반환 |
| `future.get()` | `CancellationException` -> **단언 통과** | `null` 반환, 예외 없음 -> **단언 실패** |

워커가 이기기 쉬운 이유는 태스크가 너무 가볍다는 것이다 — 본문이 `AtomicBoolean` 한 번 읽기라 실행에 들어가기만 하면 마이크로초 안에 끝난다. 반대편 `close()`는 try-with-resources 종료를 거쳐 모니터를 잡아야 한다. 부하 걸린 CI 러너에서는 테스트 스레드가 CPU를 빼앗기는 폭이 커져 실패 확률이 올라간다.

### 3.2 실측

gradle 반복은 JVM 워밍업이 섞여 부적합하다고 보고, gradle 없이 컴파일한 타이트 루프로 5만 회를 돌려 측정했다.

| 시나리오 | 5만 회 중 `notCancelled`(= 단언 실패 조건) |
|---|---|
| 수정 전 코드 그대로 | 4 (약 0.008%) |
| 수정 후 코드 | 0 (5만/5만 통과) |

이 수치가 문제의 성격을 규정한다. 로컬에서 한 번 돌려서는 절대 재현되지 않는데, 하루 수십 번 도는 CI에서는 주기적으로 빨간불을 만든다. 실제로 이 PR의 계기는 무관한 PR #36965의 CI가 이 테스트 때문에 빨개진 것이었다.

### 3.3 수정 후의 단계

수정 후에는 위 표의 "순서" 행이 사라진다. 스레드가 하나뿐이므로 프로그램 순서가 곧 실행 순서다.

| 단계 | 값·상태 |
|---|---|
| `submit` -> `execute` -> `doExecute` (오버라이드) | `captured` = `TaskTrackingRunnable`. 스레드 미생성 |
| try-with-resources 종료 -> `close()` | `threads`가 비어 있어 `wait(100)` 생략 -> `cancelled = true` (:411) |
| `captured.get().run()` (테스트 :168) | `checkCancelled`가 `true` 관측 -> `future.cancel(false)` -> `CancellationException` |
| `future.get()` (테스트 :169) | `FutureTask`가 CANCELLED -> `CancellationException` |

부수 효과로 테스트가 빨라졌다. 래퍼를 한 번도 시작하지 않으므로 `activeThreads`가 계속 비어 있고, `close()`의 `if (!threads.isEmpty())`(:404)가 `threads.wait(100)`(:405)을 건너뛴다. 스레드 생성 비용도 사라진다.

## 4. 계약

이 flaky를 둘러싼 계약은 다섯 개이고, 그중 실제로 깨진 것은 마지막 하나뿐이다.

| 계약 | 출처 | 이 flaky가 어기는가 |
|---|---|---|
| "닫히는 중인 executor에 뒤늦게 도착한 태스크는 취소되고, 그 `Future.get()`은 `CancellationException`을 던진다" | `checkCancelled`(:422-429) + gh-36362 커밋의 의도 | 프로덕션은 지킨다. **테스트가 이 계약을 안정적으로 검증하지 못했을 뿐** |
| `cancelled`는 `activeThreads` 모니터 안에서만 접근한다 | 필드 선언 옆 주석(:101), `checkCancelled` 주석(:423) | 양쪽 모두 준수. 그래서 **가시성이 아니라 순서**가 문제였다 |
| `doExecute`는 실제 실행 방식을 갈아 끼우라고 열린 protected 템플릿 메서드 | `doExecute` javadoc(:354-360) | 수정이 이 계약 안쪽을 정당하게 사용한다. 검증 대상 로직을 목킹한 것이 아니라 스레드 생성만 걷어냈다 |
| `FutureTask.cancel(false)`는 이미 완료된 태스크에 대해 아무 효과 없이 `false`를 반환한다 | `java.util.concurrent` 계약 | 결함이 아니라 전제. 이 성질 때문에 실패 인터리빙이 "늦은 취소"로 복구되지 못한다 |
| 테스트는 같은 코드·같은 입력에 대해 같은 결과를 낸다 | 테스트 스위트의 존재 이유 | **이것이 위반된 계약이다** |

## 5. 수정안

### 5.1 before / after (실파일)

수정 전후 테스트 메서드 전문을 나란히 둔다.

```java
// before  SimpleAsyncTaskExecutorTests.java:154-168 (0c60266986)
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

```java
// after  SimpleAsyncTaskExecutorTests.java:155-170 (bbfe6a04738)
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

### 5.2 왜 그 위치인가

경계를 정확히 그은 것이 이 수정의 전부다. **제거한 것은 `Thread.start()` 한 번**이고, **남긴 것은 검증 대상 전부**다. `checkCancelled`가 `future.cancel(false)`를 부르고 `CancellationException`을 던지는 취소 체인은 실물 그대로 실행되며 우회도 목킹도 없다. 달라진 것은 그 체인이 도는 스레드뿐이고, 스레드 정체는 이 테스트가 검증하려던 대상이 아니었다.

가로채는 지점이 `doExecute`여야 하는 이유도 하나뿐이다. 여기가 **래퍼가 완성된 뒤 스레드가 생기기 직전**의 유일한 확장점이다. 더 위(`execute`)를 오버라이드하면 래퍼 생성 로직 자체를 다시 써야 하고, 더 아래(`newThread`)를 오버라이드하면 스레드 객체를 받긴 하지만 `start()`를 호출하지 않는 것이 `newThread`의 계약과 어긋난다.

단언이 하나에서 둘로 늘어난 것도 의도적이다. 수정 전에는 워커 스레드가 삼킨 `CancellationException`을 테스트가 볼 수 없어 **결과만** 간접 확인할 수 있었다. 수정 후에는 원인(단언 1)과 결과(단언 2)를 각각 직접 관측한다.

### 5.3 검토된 대안과 기각 이유

채택하지 않은 접근이 여섯 가지 있었고, 각각의 기각 사유는 다음과 같다.

| 대안 | 내용 | 기각 이유 |
|---|---|---|
| `submit` 후 `Thread.sleep(...)` | 워커를 늦춰 close가 이기게 한다 | 확률만 낮출 뿐 조건이 남는다. 더 느린 머신에서 되살아나고 테스트는 느려진다. **확률을 낮추는 수정과 조건을 제거하는 수정은 다르다** |
| `CountDownLatch`로 순서 강제 | 워커가 게이트 앞에서 기다리게 한다 | 래치를 놓을 자리가 태스크 본문뿐인데, 문제의 게이트(`checkCancelled`)는 태스크 본문보다 **앞**이라 그 지점을 잡을 수 없다 |
| `@RepeatedTest`로 반복 | 실패 확률을 누적 노출 | 결함이 아니라 증상을 늘린다. 0.008%짜리 실패는 반복 100회로도 안 잡히고, 잡히면 오히려 CI가 더 자주 빨개진다 |
| 프로덕션에 `volatile cancelled` 추가 | 메모리 모델 강화 | **원인 오진.** 양쪽 접근이 이미 같은 모니터 안이라 가시성은 보장되어 있다. 문제는 순서이고 volatile은 순서를 만들지 못한다 |
| 테스트 삭제 또는 `@Disabled` | 신호 소음 제거 | gh-36362가 도입한 취소 계약의 유일한 회귀 방어선을 없앤다 |
| `close()` 전에 워커 등록을 기다린다 | `activeThreads`가 채워질 때까지 폴링 | 시나리오가 바뀐다. 이 테스트가 검증하는 것은 "**아직 시작하지 않은** 태스크의 취소"이고, 등록을 기다리면 이미 게이트를 통과한 상태가 된다 |

### 5.4 잃은 커버리지와 그 보전

이 테스트는 더 이상 실제 스레드 위에서 취소를 실행하지 않는다. 그 몫은 같은 클래스의 다른 테스트가 맡는다 — `taskTerminationTimeoutWithLateInterrupt`(머지 후 :172-191)와 `taskTerminationTimeoutWithEarlyInterrupt`(그 아래)는 실제 워커와 인터럽트 경로를 다루며, 태스크 본문이 `Thread.sleep(500)`/`sleep(200)`이고 close 쪽 마진이 100ms/설정 타임아웃이라 이번 같은 마진 0 경합이 없다. 즉 `Thread.start()` 이후의 실동시성 커버리지는 유지된다.

## 6. 범위 밖과 인접 영향

**같은 캡처 기법을 먼저 쓴 곳.** `doExecute`를 오버라이드해 래퍼를 잡아 두는 패턴은 저자의 다른 작업 #36916의 `cancelledThrottledTaskReleasesPermit`에서 먼저 등장했고, 거기 주석이 의도를 명시한다 — `// capture the wrapper without running it, to control the cancellation timing`. #36916은 이 글 작성 시점에 아직 OPEN이므로, 기법 자체가 upstream에 먼저 들어온 것은 이 PR 쪽이다.

**프로덕션 불변.** 이 PR은 `SimpleAsyncTaskExecutor.java`를 한 줄도 바꾸지 않았다. 따라서 하위호환 논점이 없고, 백포트도 테스트 파일만 따라간다(7.0.x -> main).

**남는 관찰(이 PR이 다루지 않음).**

- 캡처 기법은 "태스크가 실행 **전에** 취소되는" 시나리오에만 결정론을 준다. 실행 **중** 인터럽트되는 시나리오는 워커 스레드가 실제로 필요하므로 같은 도구가 통하지 않는다.
- `captured.get()`이 `null`이면 NPE가 나겠지만, `submit -> execute -> doExecute` 경로가 항상 래퍼를 넘기므로(분기 2 성립) 실제로는 불가능하다. 다만 이 안전성은 `setTaskTerminationTimeout(100)`이 앞에 있다는 사실에 의존하므로, 그 줄을 지우면 분기 3으로 빠져 캡처되는 것이 맨 람다가 되고 단언 1이 조용히 무의미해진다 — 테스트 설정 두 줄이 서로 결합되어 있다는 점은 기록해 둘 만하다.
- 이 테스트가 검증하는 프로덕션 코드에는 별개의 결함(취소 시 throttle permit 누수)이 남아 있다. `checkCancelled`가 `try` 바깥에서 던지기 때문인데, 이 테스트는 throttle을 켜지 않으므로(`setConcurrencyLimit` 미호출) 그 경로에 닿지 않는다. 해당 결함은 #36916의 대상이다.
