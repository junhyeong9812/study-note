# PR #36967 — 무대 구조와 워크플로우

> PR #36967의 무대가 되는 실구조·워크플로우. 문제·수정은 README.md, 테스트는 tests.md 참조.
> 기준: upstream main `526c706d1c3`. 이 PR은 이미 머지되어 있으므로 테스트 파일의 현재 코드는 "수정 후"다. 수정 전 형태가 필요한 곳은 그때마다 명시한다. 프로덕션 코드(`SimpleAsyncTaskExecutor`)는 이 PR로 바뀌지 않았으므로 아래 인용은 수정 전후가 동일하다.

이 문서가 다루는 것은 `SimpleAsyncTaskExecutor`가 종료할 때 아직 시작하지 않은 태스크를 취소하는 경로의 실구조다.\
클래스 계층과 세 상태 필드에서 출발해, 수정 전 테스트가 밟던 두 스레드 흐름을 따라간다.\
그다음 세 곳의 분기도로 결과가 갈리던 자리를 짚고, 이 executor가 프레임워크 전역에서 차지하는 자리와 배경 개념을 정리한다.

> **`TaskExecutor`** — "이 작업을 실행해 달라"만 요청하고 어떤 스레드에서 도는지는 구현에 맡기는 Spring의 실행 추상화.\
> 예: `@Async`가 붙은 메서드 호출은 곧장 실행되지 않고 이 추상화를 거쳐 다른 스레드로 넘어간다.

## 1. 무대 — 실구조

이 PR의 무대는 `spring-core`의 `SimpleAsyncTaskExecutor`와 그 안에 사는 내부 클래스 두 개, 그리고 이들이 공유하는 세 개의 상태 필드다.\
PR 자체는 테스트 한 메서드만 바꾸지만, 그 테스트가 검증하는 대상은 "닫히는 중인 executor에 뒤늦게 도착한 태스크를 어떻게 취소하는가"라는 프로덕션 로직이고, 그 로직은 아래 구조 안에 흩어져 있다.

먼저 클래스 계층이다.\
`SimpleAsyncTaskExecutor`는 스레드 생성 설정을 상위 클래스에서, 동시성 제한 로직을 내부 어댑터를 통해 또 다른 상위 클래스에서 빌려 온다.

```text
┌──────────────────────────────┐        ┌──────────────────────────────────┐
│ CustomizableThreadCreator    │        │ ConcurrencyThrottleSupport       │
│ CustomizableThreadCreator.java│       │ ConcurrencyThrottleSupport.java  │
│  + createThread(Runnable) :150│       │  # beforeAccess()           :119 │
│  # nextThreadName()       :163│       │  # onLimitReached()         :145 │
└──────────────┬───────────────┘        │  # onAccessRejected(String) :178 │
               │ extends                │  # afterAccess()            :186 │
               ▼                        └──────────────┬───────────────────┘
┌──────────────────────────────────────────────────┐   │ extends
│ SimpleAsyncTaskExecutor                          │   │
│   SimpleAsyncTaskExecutor.java:66                │   │
│   implements AsyncTaskExecutor, Serializable,    │   │
│              AutoCloseable                       │   │
│                                                  │   │
│  - concurrencyThrottle : ConcurrencyThrottleAdapter ──┘  :83
│  - virtualThreadDelegate : @Nullable VirtualThreadDelegate :85
│  - threadFactory : @Nullable ThreadFactory              :87
│  - taskDecorator : @Nullable TaskDecorator              :89
│  - taskTerminationTimeout : long                        :91
│  ★ activeThreads : @Nullable Set<Thread>                :93
│  - cancelRemainingTasksOnClose : boolean                :95
│  - rejectTasksWhenLimitReached : boolean                :97
│  ★ closed : AtomicBoolean                               :99
│  ★ cancelled : boolean  // within activeThreads sync   :101
│                                                          │
│  + setTaskTerminationTimeout(long)                      :193
│  + setCancelRemainingTasksOnClose(boolean)              :214
│  + isActive() : boolean                                 :275
│  - trackActiveThreadsIfNecessary()                      :283
│  + execute(Runnable)                                    :296
│  + execute(Runnable, long) @Deprecated  ★ 분기 본체      :311
│  + submit(Runnable) : Future<?>                         :340
│  + submit(Callable<T>) : Future<T>                      :348
│  # doExecute(Runnable)   ★ protected 확장점              :361
│  # newThread(Runnable) : Thread                         :374
│  + close()               ★ 취소 플래그를 세우는 곳        :390
│  - checkCancelled(@Nullable Future<?>)                  :422
└──────────┬───────────────────────────────────┬───────────┘
           │ 내부 클래스                        │ 내부 클래스
           ▼                                   ▼
┌───────────────────────────────┐   ┌────────────────────────────────────┐
│ ConcurrencyThrottleAdapter    │   │ TaskTrackingRunnable               │
│   (private class)        :437 │   │   (private class)             :468 │
│  beforeAccess/afterAccess를   │   │  - task : Runnable            :470 │
│  바깥 클래스에 노출           │   │  - future : @Nullable Future<?>:472│
│  onLimitReached → 거부 정책   │   │  + run()                      :481 │
│  onAccessRejected → Task-     │   │      ├ checkCancelled(future) :487 │
│    RejectedException     :454 │   │      ├ threads.add(thread)    :488 │
└───────────────────────────────┘   │      ├ task.run()             :492 │
                                    │      └ finally: 제거·notify   :494 │
                                    └────────────────────────────────────┘
```

세 개의 별표 필드가 이 PR이 다루는 시나리오의 전부다.\
`activeThreads`는 종료 대기가 필요할 때만 만들어지는 스레드 집합이고(`:283~286`), `closed`는 executor가 더 이상 제출을 받지 않는다는 표시이며(`:99`, `:275~277`), `cancelled`는 "남은 태스크를 취소하라"는 신호다.\
`cancelled`는 `volatile`이 아니라 `activeThreads` 모니터로만 보호된다는 계약이 선언 옆 주석에 박혀 있다(`:101`).

> **모니터(monitor)** — 자바에서 객체 하나에 딸려 있는 자물쇠. `synchronized (obj)` 블록은 그 객체의 모니터를 잡아야 들어갈 수 있다.\
> 예: 여기서는 `activeThreads` 집합 객체가 자물쇠 역할을 하고, `cancelled`를 읽고 쓰는 두 코드가 모두 그 자물쇠를 잡는다.

세 필드가 언제 만들어지고 누가 읽는지를 한 화면에 놓으면 이렇다.

```text
별표 필드 세 개의 일생

activeThreads : Set<Thread>              :93
   생성   setTaskTerminationTimeout(100)
            -> trackActiveThreadsIfNecessary()          :283~286
   읽기   execute :330   (래퍼를 씌울지 정한다)
          close   :392   (무엇을 기다릴지 정한다)
          run     :482   (자신을 등록할 집합)
   겸직   이 집합 객체 자체가 cancelled 를 지키는 자물쇠다

closed : AtomicBoolean                   :99
   세움   close() 의 compareAndSet(false, true)          :391
   읽기   isActive()  :275~277
          run() 의 finally  :497

cancelled : boolean   (volatile 아님)    :101
   세움   close()  :397 (즉시 취소 설정) 또는 :411 (타임아웃 후)   <- 쓰기
   읽기   checkCancelled()  :423                                 <- 읽기
   계약   activeThreads 모니터 안에서만 접근한다 (선언 옆 주석)
```

`TaskTrackingRunnable`은 사용자 태스크를 감싸는 데코레이터인데, 이 PR의 관점에서 중요한 것은 그 안에 검증 대상 로직 전체가 들어 있다는 사실이다.\
취소 검사(`:487`)와 등록·해제·통지(`:488`, `:495~503`)가 모두 이 래퍼의 `run()` 안에서 일어난다.\
사용자 람다는 그 한가운데 `this.task.run()`(`:492`)으로 한 번 불릴 뿐이다.

> **데코레이터(decorator)** — 원본 객체를 같은 인터페이스의 다른 객체로 감싸, 앞뒤에 할 일을 덧붙이는 구조.\
> 예: `TaskTrackingRunnable`은 사용자 `Runnable`을 감싸 실행 전에 취소 검사를, 실행 후에 집합 해제를 덧붙인다.

## 2. 수정 전 동작 워크플로우

대표 시나리오는 문제가 된 테스트가 의도한 흐름, 즉 "제출 직후 close, 뒤늦게 시작한 워커가 취소를 발견"이다.\
수정 전 테스트는 두 스레드가 등장한다.

수정 전 테스트 코드(diff의 `-` 쪽)는 다음과 같았다.\
현재 파일(`SimpleAsyncTaskExecutorTests.java:155~170`)은 이미 수정 후 형태이므로 이 조각은 diff에서 재구성한 것이다.

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

이 코드가 만드는 두 스레드의 흐름을 나란히 놓으면 이렇다.\
왼쪽이 테스트(제출) 스레드, 오른쪽이 executor가 띄운 워커 스레드다.\
두 줄기가 만나는 곳은 `activeThreads` 모니터 하나뿐이다.

```text
[테스트 스레드]                              [워커 스레드]

setTaskTerminationTimeout(100)      :193
  └ trackActiveThreadsIfNecessary() :283
      activeThreads = newKeySet()   :284
        (timeout > 0 이므로 추적 켜짐)

submit(runnable)                    :340
  └ new FutureTask<>(task, null)    :341
  └ execute(future, TIMEOUT_INDEFINITE) :342
       ├ isActive()? true           :313
       ├ taskToUse = task (decorator 없음)   :317
       ├ future = (task instanceof Future) → FutureTask :318
       ├ isThrottleActive()? false  :319
       └ activeThreads != null → true       :330
            doExecute(new TaskTrackingRunnable(taskToUse, future)) :331
              └ newThread(task).start()     :361~362
                        ─────────────────────────► 스레드 출발
                                                   (여기서부터 순서 미정)

try-with-resources 종료
close()                             :390
  ├ closed.compareAndSet(false,true):391
  ├ threads = activeThreads (비어 있음)     :392
  ├ cancelRemainingTasksOnClose? false     :394
  └ taskTerminationTimeout > 0 → true      :401
       synchronized (threads) {            :402
         threads.isEmpty() → wait 생략     :404
         cancelled = true                  :411   ★ 쓰기
       }
       threads.forEach(Thread::interrupt)  :415
                                                   TaskTrackingRunnable.run()  :481
                                                     threads = activeThreads   :482
                                                     thread = currentThread()  :485
                                                     synchronized (threads) {  :486
                                                       checkCancelled(future)  :487  ★ 읽기
                                                         cancelled? true       :423
                                                         future.cancel(false)  :425
                                                         throw Cancellation…   :427
                                                     }
                                                   (예외로 run() 이탈,
                                                    스레드가 삼킴)
finished.set(true)
future.get() → CancellationException
```

두 번째 시나리오로, 정상 완료 경로도 함께 보아 두면 대비가 분명해진다.\
executor가 닫히기 전에 워커가 도착하면 취소 검사는 통과하고 태스크가 실제로 실행된다.

```text
TaskTrackingRunnable.run()                          :481
  synchronized (threads) {                          :486
    checkCancelled(future) → cancelled == false     :423 (아무 일 없음)
    threads.add(thread)                             :488
  }
  try { this.task.run() }        ← 사용자 람다 실행  :492
  finally {                                         :494
    threads.remove(thread)                          :496
    if (closed.get()) {                             :497
      synchronized (threads) {                      :498
        if (threads.isEmpty()) threads.notify()     :499~500
      }                          ← close()의 wait 를 깨움
    }
    concurrencyThrottle.afterAccess()               :505
  }
```

이 두 흐름이 같은 코드에서 갈리는 지점이 `checkCancelled` 한 줄이고, 어느 쪽으로 갈지는 `cancelled`가 언제 세워졌는가에 달려 있다.\
수정 전 테스트에서 그 시점은 두 스레드의 도착 순서가 정한다.

## 3. 분기 처리 워크플로우

무대의 조건 분기는 세 곳에 모여 있다.\
태스크를 어떤 형태로 넘길지 정하는 `execute`, 종료 시 무엇을 기다릴지 정하는 `close`, 그리고 태스크를 실행할지 취소할지 정하는 `TaskTrackingRunnable.run`이다.

`execute(Runnable, long)`의 3분기는 "래퍼로 감쌀 것인가, 그리고 동시성 허가를 받을 것인가"를 정한다.

> **동시성 스로틀(concurrency throttle)** — 동시에 실행 중인 태스크 수에 상한을 두고, 상한을 넘으면 막거나 거부하는 장치.\
> 예: `beforeAccess()`로 허가를 받고 `afterAccess()`로 반납하며, 한도를 넘으면 `TaskRejectedException`이 난다(`:454`).

```text
execute(task, startTimeout)                          :311
  │
  ├ task == null ────────────────────► Assert 실패                       :312
  ├ !isActive() ─────────────────────► throw TaskRejectedException       :313~315
  │
  │ taskToUse = taskDecorator != null ? decorate(task) : task            :317
  │ future    = task instanceof Future<?> f ? f : null                   :318
  │            └─ submit() 이 FutureTask 를 넘기므로 여기서 성립
  │
  ├─[A] isThrottleActive() && startTimeout > TIMEOUT_IMMEDIATE           :319
  │       concurrencyThrottle.beforeAccess()  (한도 초과 시 블록/거부)    :320
  │       try  doExecute(new TaskTrackingRunnable(taskToUse, future))    :322
  │       catch 스레드 생성 실패 → afterAccess() 로 허가 반납 후 재던짐   :324~328
  │
  ├─[B] activeThreads != null   ★ 이 PR 테스트가 타는 분기                :330
  │       doExecute(new TaskTrackingRunnable(taskToUse, future))         :331
  │       (setTaskTerminationTimeout(100) 이 activeThreads 를 켰다)
  │
  └─[C] 그 외 (추적도 스로틀도 없음)                                      :333
          doExecute(taskToUse)      ← 래퍼 없이 원본을 그대로 넘김        :334
```

분기 [B]가 이 PR의 시나리오다.\
여기서 `doExecute`에 전달되는 것이 사용자 람다가 아니라 `TaskTrackingRunnable` 래퍼라는 사실이 중요하다 — 수정 후 테스트가 가로채는 대상이 바로 이 래퍼이고, 검증하려는 취소 로직이 그 안에 들어 있기 때문이다.\
분기 [C]였다면 잡아 봐야 사용자 람다일 뿐 취소 검사가 없다.

`close()`의 분기는 두 개의 독립 스위치를 조합한다.

```text
close()                                              :390
  │
  ├ closed.compareAndSet(false, true) 실패 ─────► 아무것도 하지 않음(재진입 방지) :391
  │
  └ threads = activeThreads                          :392
     │
     ├ threads == null ────────────────────────► 종료 대기 없음 (추적 꺼짐)      :393
     │
     └ threads != null
         │
         ├─ cancelRemainingTasksOnClose == true                                :394
         │     synchronized (threads) { cancelled = true }                     :395~397
         │     threads.forEach(Thread::interrupt)   ← 즉시 인터럽트             :399
         │
         └─ taskTerminationTimeout > 0             ★ 이 PR 시나리오             :401
               synchronized (threads) {                                        :402
                 ├ threads.isEmpty()  → wait 생략   ★ 테스트가 타는 경로        :404
                 └ !threads.isEmpty() → threads.wait(taskTerminationTimeout)   :405
                 │     (InterruptedException → 현재 스레드 재인터럽트)          :408~410
                 cancelled = true                   ★ 취소 플래그 확정          :411
               }
               if (!cancelRemainingTasksOnClose)                               :413
                 threads.forEach(Thread::interrupt) ← 타임아웃 후 늦은 인터럽트 :415
```

수정 전 테스트가 밟는 경로는 `threads.isEmpty()`가 참인 쪽(`:404`)이다.\
워커가 아직 자신을 등록하지 않았기 때문인데, 이것이 참이 되느냐는 것 자체가 두 스레드의 순서에 달려 있다.

마지막으로 `TaskTrackingRunnable.run()`의 분기가 결과를 확정한다.\
버그가 살던 자리, 정확히는 "테스트 결과가 갈리던 자리"가 여기다.

```text
TaskTrackingRunnable.run()                                        :481
  │
  ├ threads = activeThreads                                       :482
  │
  ├ threads == null ──────────────► 등록 없이 곧장 task.run()      :484
  │
  └ threads != null
      synchronized (threads) {                                    :486
        checkCancelled(this.future)                               :487
        │
        ├─★ cancelled == true                        checkCancelled:423
        │     ├ future != null → future.cancel(false)             :425
        │     └ throw CancellationException                       :427
        │        → run() 이탈, task.run() 도달하지 않음
        │        → FutureTask 는 CANCELLED 상태
        │        → 이후 future.get() 이 CancellationException
        │
        └── cancelled == false
              threads.add(thread)                                 :488
              try { this.task.run() }                             :492
              → FutureTask 정상 완료(NORMAL)
              → 이후 future.cancel(false) 는 false 반환, 무효
              → future.get() 은 null 반환, 예외 없음
      }
      finally {                                                   :494
        threads.remove(thread)                                    :496
        if (closed.get() && threads.isEmpty()) threads.notify()    :497~503
        concurrencyThrottle.afterAccess()                          :505
      }
```

두 갈래 중 어느 쪽으로 가느냐는 `cancelled`의 쓰기(`close():411`)와 읽기(`checkCancelled():423`) 중 무엇이 먼저 모니터를 잡느냐로 결정된다.\
두 문장이 서로 다른 스레드에 있는 한 이 순서를 코드가 강제하지 못하며, 이것이 수정 전 테스트가 비결정적이었던 구조적 이유다.\
메모리 가시성은 양쪽 모두 `synchronized (threads)` 안에 있어 보장되므로, 문제는 가시성이 아니라 순서다.

세 분기도를 한 그림으로 겹치면 갈림길이 자물쇠 하나로 좁혀진다.

```text
cancelled 한 변수를 두고 두 스레드가 같은 자물쇠를 잡는다

  [테스트 스레드]                 자물쇠              [워커 스레드]
  close()                      activeThreads        TaskTrackingRunnable.run()
     |                          (모니터)                    |
     | synchronized(threads) :402  |   synchronized(threads) :486
     +--------------------------> [ ] <--------------------+
                                   |
              둘 중 하나만 들어간다. 누가 먼저인지는 정해져 있지 않다
                                   |
        +--------------------------+--------------------------+
        |                                                     |
  close 가 먼저 잡았다                                  run 이 먼저 잡았다
  cancelled = true        :411                   checkCancelled -> false  :423
        |                                                     |
        v                                                     v
  run 이 나중에 읽어 true 관측  :423              threads.add(thread)      :488
  future.cancel(false)    :425                   task.run()               :492
  throw CancellationException :427               FutureTask 정상 완료(NORMAL)
        |                                                     |
        v                                                     v
  future.get() -> CancellationException          future.get() -> null (예외 없음)
```

같은 코드가 같은 입력으로 두 결과를 낸다 — 갈림길은 자물쇠 진입 순서 하나뿐이다.

## 4. 스프링 전역에서의 자리

`SimpleAsyncTaskExecutor`는 Spring의 `TaskExecutor` 추상화에서 "풀 없이 태스크마다 스레드를 띄우는" 최소 구현이자, 다른 executor가 설정되지 않았을 때 여러 상위 기능이 말없이 집어 드는 기본값이다.\
따라서 이 클래스의 종료·취소 동작은 비동기 실행 전반의 안전망이다.

패키지 안에서의 위치는 다음과 같다.\
grep으로 확인한 인터페이스 계층과 형제 구현이다.

```text
org.springframework.core.task
   TaskExecutor  (Executor 확장, 순수 실행 추상화)
      │
      ├─ AsyncTaskExecutor        submit(Runnable)/submit(Callable) 추가
      │     │                     AsyncTaskExecutor.java:43
      │     │                     (javadoc :38 이 SimpleAsync… 를 대표 구현으로 지목)
      │     │
      │     └─★ SimpleAsyncTaskExecutor   SimpleAsyncTaskExecutor.java:66
      │             │   (스레드 재사용 없음, virtual thread 옵션, 종료 대기)
      │             │
      │             └─ SimpleAsyncTaskScheduler        (extends)
      │                   SimpleAsyncTaskScheduler.java:103
      │                   implements TaskScheduler, SmartLifecycle
      │                   → 이 PR이 다루는 close/cancel 경로를 그대로 상속
      │
      ├─ SyncTaskExecutor              SyncTaskExecutor.java:43 (호출 스레드에서 즉시 실행)
      └─ VirtualThreadTaskExecutor     VirtualThreadTaskExecutor.java:32
```

프레임워크 상위 기능에서 이 executor가 불려 나오는 실제 진입점은 다음 네 곳이다.

첫째, `@Async` 메서드 실행.\
`AsyncExecutionInterceptor.getDefaultExecutor(beanFactory)`가 컨텍스트에서 `TaskExecutor` 빈이나 `taskExecutor`라는 이름의 `Executor`를 찾지 못하면 `new SimpleAsyncTaskExecutor()`로 떨어진다(`AsyncExecutionInterceptor.java:155~158`).\
`EnableAsync`의 javadoc(`EnableAsync.java:64`)이 이 폴백을 명시한다.\
즉 `@Async`만 켜고 executor를 지정하지 않은 애플리케이션은 이 클래스 위에서 돈다.

둘째, JMS 리스너 컨테이너.\
`DefaultMessageListenerContainer.createDefaultTaskExecutor()`가 빈 이름을 스레드 이름 접두사로 삼아 `new SimpleAsyncTaskExecutor(threadNamePrefix)`를 만든다(`DefaultMessageListenerContainer.java:901~905`).\
리스너 스레드가 이 executor 위에서 장기 실행되므로 컨테이너 종료 시 종료 대기 동작이 직접 관계된다.

셋째, 애플리케이션 이벤트 비동기 멀티캐스팅.\
`SimpleApplicationEventMulticaster`는 `taskExecutor`가 설정되어 있으면 리스너 호출을 그 executor에 넘긴다(`SimpleApplicationEventMulticaster.java:139~143`).\
javadoc이 권장 구현으로 `SimpleAsyncTaskExecutor`를 지목한다(`:90`).

넷째, 스케줄링.\
`SimpleAsyncTaskScheduler`가 이 클래스를 상속해 `TaskScheduler`와 `SmartLifecycle`을 함께 구현한다(`SimpleAsyncTaskScheduler.java:103~104`).\
상속이므로 `close()`·`TaskTrackingRunnable`·`cancelled` 경로가 스케줄러에도 그대로 살아 있다.

이 PR이 프로덕션 코드를 건드리지 않았음에도 의미가 있는 이유가 여기서 나온다.\
위 네 경로가 모두 같은 취소 로직에 의존하므로, 그 로직을 지키는 테스트가 신뢰할 수 없는 신호를 내면 회귀 탐지가 통째로 무뎌진다.\
실제로 이 테스트의 간헐 실패는 무관한 PR(#36965)의 CI를 빨갛게 만들어 발견되었다.

## 5. 관련 개념

### 5.1 `doExecute`는 왜 protected인가 — 프로덕션이 열어 둔 확장점

`doExecute(Runnable)`(`:361~363`)의 javadoc은 자신을 "실제 실행을 위한 템플릿 메서드"라고 규정하고, 기본 구현이 새 스레드를 만들어 시작한다고 명시한다.\
즉 "실행 방식을 갈아 끼우라"고 열어 둔 자리다.\
`newThread(Runnable)`(`:374`) 역시 protected이며, 그 아래에서 virtual thread 위임자와 외부 `ThreadFactory` 중 무엇을 쓸지 고른다(`:375~380`).

> **템플릿 메서드(template method)** — 전체 절차는 상위 클래스가 고정해 두고, 그중 한 단계만 하위 클래스가 갈아 끼우도록 열어 둔 메서드.\
> 예: `execute`가 정하는 "래퍼를 씌워 넘긴다"는 절차는 그대로 두고, `doExecute`의 "새 스레드로 실행한다"만 바꿔 끼울 수 있다.

이 확장점이 결정론화의 지렛대가 된다.\
오버라이드해서 넘어온 `Runnable`을 저장만 하고 실행하지 않으면, 스레드가 하나도 생기지 않은 채 래퍼를 손에 넣을 수 있다.\
중요한 것은 이렇게 해도 검증 대상이 목킹되지 않는다는 점이다.\
걷어내는 것은 `Thread.start()` 한 번이고, `checkCancelled`가 `future.cancel(false)`를 부르고 `CancellationException`을 던지는 취소 체인은 실물 그대로 실행된다.

> **목킹(mocking)** — 검증 대상의 실제 구현 대신 가짜 객체를 끼워 넣어 동작을 흉내 내는 것.\
> 예: 여기서는 취소 로직 자체를 가짜로 바꾸지 않았으므로 목킹이 아니다 — 실행 스레드만 바뀌었다.

### 5.2 `FutureTask`의 상태 전이와 `cancel(false)`

`submit(Runnable)`은 사용자 태스크를 `FutureTask`로 감싸고(`:341`) 그것을 `execute`에 넘긴다.\
`execute`는 `task instanceof Future<?> f` 검사(`:318`)로 그 `FutureTask`를 다시 꺼내 래퍼에 물려 준다.\
이 왕복 덕분에 래퍼가 "자신이 감싼 태스크에 대응하는 Future 핸들"을 알게 된다.

> **`FutureTask`** — 아직 끝나지 않은 작업의 결과를 나중에 꺼낼 수 있게 해 주는 핸들이자, 그 작업 자체를 담은 `Runnable`.\
> 예: `submit`이 돌려준 `Future`에 `get()`을 부르면 결과가 날 때까지 기다렸다가 값을 받거나 예외를 받는다.

`FutureTask`는 상태 기계이며 완료 상태는 되돌릴 수 없다.\
아직 실행되지 않은 상태에서 `cancel(false)`를 부르면 CANCELLED로 전이하고 이후 `get()`이 `CancellationException`을 던진다.\
반면 이미 정상 완료(NORMAL)된 태스크에 같은 호출을 하면 아무 효과 없이 `false`를 돌려주고, `get()`은 그대로 결과값을 반환한다.\
3장 분기도의 두 갈래가 관측 가능한 서로 다른 결과를 내는 근거가 이 성질이다.

`cancel`의 인자가 `false`인 것도 의미가 있다.\
실행 중인 스레드를 인터럽트하지 말라는 뜻인데, 이 경로는 애초에 "아직 시작하지 않은 태스크"만 다루므로 인터럽트가 필요 없다.\
실행 중 스레드에 대한 인터럽트는 `close()`가 별도로 담당한다(`:399`, `:415`).

### 5.3 가시성과 순서는 다른 문제다

`cancelled`는 `volatile`이 아니지만(`:101`), 쓰기(`close():411`)와 읽기(`checkCancelled():423`)가 모두 같은 `activeThreads` 객체의 모니터 안에서 일어난다.\
모니터의 해제-획득 쌍은 happens-before 관계를 만들므로 가시성은 보장된다.\
즉 "워커가 낡은 `false`를 본다"는 일은 일어나지 않는다.

> **happens-before** — "앞 동작이 남긴 값은 뒤 동작에서 반드시 보인다"를 자바 메모리 모델이 보장하는 관계.\
> 예: 한 스레드가 모니터를 놓고 다른 스레드가 그 모니터를 잡으면, 놓기 전에 쓴 값은 잡은 뒤에 반드시 보인다.

> **가시성(visibility)과 순서(ordering)** — 가시성은 "쓴 값이 보이는가", 순서는 "두 동작 중 무엇이 먼저 일어나는가"다.\
> 예: 여기서는 값이 보이는 것은 보장되지만, `close()`와 `run()` 중 누가 먼저 모니터를 잡는지는 보장되지 않는다.

보장되지 않는 것은 두 임계 구역의 진입 순서다.\
모니터는 상호 배제와 가시성을 주지만 어느 쪽이 먼저 들어갈지는 정하지 않는다.\
동시성 테스트가 흔들릴 때 원인을 가시성으로 오진하면 `volatile`을 붙이는 식의 무효한 수정으로 이어지므로, 두 문제를 분리해서 보는 것이 이 무대의 핵심 독법이다.\
이 PR은 순서 문제를 순서 문제로 다뤘다 — 두 문장을 한 스레드 위에 올려 프로그램 순서가 곧 실행 순서가 되게 만들었다.

### 5.4 flaky 테스트와 "확률을 낮추는 수정" 대 "조건을 제거하는 수정"

flaky 테스트는 같은 코드·같은 입력에 대해 실행마다 결과가 달라지는 테스트다.\
원인은 대개 테스트 밖의 비결정 요소, 즉 스레드 스케줄링·실시간 시계·파일시스템 순서다.\
해로운 이유는 실패 자체보다 신호가 망가지는 데 있다.\
"빨간불이면 내 변경이 잘못됐다"는 명제가 무너지면 개발자는 빨간불을 재실행으로 넘기게 되고, 그 습관이 진짜 회귀까지 통과시킨다.

> **flaky 테스트(flaky test)** — 코드를 바꾸지 않았는데도 돌릴 때마다 통과와 실패를 오가는 테스트.\
> 예: 이 테스트는 5만 회 중 몇 회만 실패하므로 로컬에서 한 번 돌려서는 정상으로 보인다.

수정 방법에는 두 종류가 있고 성질이 다르다.\
`Thread.sleep`이나 대기를 끼워 넣어 원하는 순서가 나올 확률을 높이는 것은 확률을 낮추는 수정이다.\
원인은 남아 있고, 테스트는 느려지며, 더 느린 머신에서 되살아난다.\
반대로 경쟁의 참가자 하나를 없애 순서 자체를 결정하는 것은 조건을 제거하는 수정이다.\
이 무대에서 후자를 가능하게 한 것이 5.1의 `doExecute` 확장점이다.

### 5.5 종료 대기(graceful shutdown)를 풀 없이 구현한다는 것

스레드 풀 기반 executor는 풀 자체가 실행 중 태스크 목록을 알고 있어 `awaitTermination` 같은 API를 자연스럽게 제공한다.\
`SimpleAsyncTaskExecutor`에는 풀이 없으므로 "무엇이 실행 중인지"를 별도로 기록해야 한다.\
그 기록이 `activeThreads`이고, 기록 비용 때문에 기본값은 추적 꺼짐이다.

> **종료 대기(graceful shutdown)** — 종료 신호를 받은 뒤 곧장 끊지 않고, 이미 실행 중인 작업이 끝날 시간을 주고 닫는 것.\
> 예: `setTaskTerminationTimeout(100)`은 "최대 100ms까지는 실행 중 태스크를 기다린다"는 설정이다.

`setTaskTerminationTimeout(long)`(`:193~197`)과 `setCancelRemainingTasksOnClose(boolean)`(`:214~217`)이 둘 다 `trackActiveThreadsIfNecessary()`(`:283`)를 부르는 이유가 그것이다.\
둘 중 하나라도 켜지면 집합이 만들어지고, 그 순간부터 모든 태스크가 `TaskTrackingRunnable`로 감싸인다(`execute:330~331`).\
javadoc이 "0보다 큰 타임아웃은 태스크마다 추적 래퍼를 씌우므로 상당한 오버헤드가 있다"고 경고하는 것도 이 구조 때문이다(`:178~183`).

그 스위치 하나가 켜고 끄는 것을 나란히 놓으면 이렇다.

```text
 추적 꺼짐 (기본값)                     추적 켜짐 (timeout > 0)
 +-------------------------------+     +-------------------------------+
 | activeThreads = null     :93  |     | activeThreads = newKeySet()   |
 |                               |     |                        :284   |
 | execute 분기 [C]         :333  |     | execute 분기 [B]         :330  |
 |   doExecute(taskToUse)  :334  |     |   doExecute(new Task-         |
 |   = 사용자 람다 그대로         |     |     TrackingRunnable(..)):331  |
 |                               |     |   = 취소 검사를 품은 래퍼      |
 | close() 는 종료 대기 없음 :393 |     | close() 가 wait / cancelled   |
 |                               |     |   경로를 탄다        :401~411  |
 +-------------------------------+     +-------------------------------+
   취소 검사가 통과할 자리조차 없다        검증 대상 로직이 여기 들어 있다
```

이 설계가 이 PR의 테스트에 직접적인 영향을 준다.\
테스트가 `setTaskTerminationTimeout(100)`을 부르는 것은 100ms를 기다리기 위해서가 아니라, 추적을 켜서 `TaskTrackingRunnable` 경로를 활성화하기 위해서다.\
그리고 실제로는 집합이 비어 있어 `wait`가 생략되므로(`close():404`) 100ms를 기다리지도 않는다.
