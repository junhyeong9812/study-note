# PR #36916 — 무대의 실구조와 워크플로우

> PR #36916의 무대가 되는 실구조·워크플로우. 문제·수정은 README.md, 테스트는 tests.md 참조.
>
> 기준: upstream main `526c706d1c3`. 이 커밋에는 PR #36916이 아직 반영되지 않았으므로,
> 아래 file:line 인용은 전부 **수정 전 코드**를 그대로 가리킨다.

## 1. 무대 — 실구조

무대는 클래스 두 개와 그 안의 내부 클래스 두 개다.\
결론부터 말하면, **permit을 "획득하는 코드"와 "반납하는 코드"가 서로 다른 클래스, 다른 스레드, 다른 생명주기에 살고 있고, 둘 사이를 잇는 정보 통로가 없다.**\
그것이 이 PR이 다루는 구조적 사실이다.

> **permit(퍼밋)** — "한 자리를 점유할 권리" 한 장.\
> 예: `beforeAccess()`가 `concurrencyCount`를 1 올려 한 장을 집어가고, `afterAccess()`가 1 내려 돌려놓는다.

먼저 소유 관계다.

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ SimpleAsyncTaskExecutor            (SimpleAsyncTaskExecutor.java:66)     │
│   extends CustomizableThreadCreator                                      │
│   implements AsyncTaskExecutor, Serializable, AutoCloseable              │
│                                                                          │
│  필드                                                                     │
│    ConcurrencyThrottleAdapter concurrencyThrottle  :83  (final, 내부 클래스)│
│    VirtualThreadDelegate      virtualThreadDelegate :85                  │
│    ThreadFactory              threadFactory        :87                   │
│    TaskDecorator              taskDecorator        :89                   │
│    long                       taskTerminationTimeout :91                 │
│    Set<Thread>                activeThreads        :93  ← null 이면 추적 안 함│
│    boolean                    cancelRemainingTasksOnClose :95            │
│    boolean                    rejectTasksWhenLimitReached :97            │
│    AtomicBoolean              closed               :99                   │
│    boolean                    cancelled            :101 ← activeThreads   │
│                                                          동기화 안에서만 접근│
│  제출 API                                                                 │
│    execute(Runnable)              :296 → execute(task, TIMEOUT_INDEFINITE)│
│    submit(Runnable)               :340 → FutureTask 로 감싸 execute(...)   │
│    submit(Callable<T>)            :348 → FutureTask 로 감싸 execute(...)   │
│    execute(Runnable, long)        :311 ★ 모든 경로가 모이는 유일한 분기점   │
│                                                                          │
│  실행·종료                                                                │
│    doExecute(Runnable)            :361  newThread(task).start()          │
│    newThread(Runnable)            :374  가상/팩터리/기본 스레드 선택        │
│    close()                        :390  cancelled 세우고 종료 대기·인터럽트 │
│    checkCancelled(Future)         :422  cancelled 면 CancellationException │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │ ConcurrencyThrottleAdapter  (private inner, :437)                │    │
│  │   extends ConcurrencyThrottleSupport                             │    │
│  │   · beforeAccess()/afterAccess() 를 바깥 클래스에 노출 (:439,:457)│    │
│  │   · onLimitReached()  :444 → rejectTasksWhenLimitReached 면 거절  │    │
│  │   · onAccessRejected() :452 → TaskRejectedException 으로 치환      │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │ TaskTrackingRunnable  (private inner, :468)  implements Runnable │    │
│  │   Runnable  task    :470                                          │    │
│  │   Future<?> future  :472  ← task 가 Future 면 취소 통지용          │    │
│  │   run()             :481  ◀── 이 PR의 대상                         │    │
│  └──────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────┘
                    │ extends
                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ ConcurrencyThrottleSupport      (ConcurrencyThrottleSupport.java:50)     │
│   abstract, Serializable — 범용 동시 접근 제한 카운터                      │
│                                                                          │
│  상수  UNBOUNDED_CONCURRENCY = -1  :58    NO_CONCURRENCY = 0  :67         │
│                                                                          │
│  필드  Lock      concurrencyLock       :73  ReentrantLock                │
│        Condition concurrencyCondition  :75                               │
│        int       concurrencyLimit      :77  기본 -1                       │
│        int       concurrencyCount      :79  ★ 이 PR이 어긋나게 만든 값     │
│                                                                          │
│  beforeAccess()   :119  한도 도달 시 onLimitReached(), 통과하면 count++    │
│  onLimitReached() :145  기본 구현 = 자리가 날 때까지 await() 로 블로킹      │
│  afterAccess()    :186  count-- 후 signal()                              │
│  isThrottleActive() :108  limit >= 0                                     │
└──────────────────────────────────────────────────────────────────────────┘
```

이 구조에서 이 PR을 규정하는 사실이 세 가지 나온다.

**첫째, `concurrencyCount`에는 소유권 정보가 없다.**\
그냥 `int` 하나다(:79).\
"누가 몇 개를 들고 있는지"를 아무도 기록하지 않으므로, `beforeAccess()` 1회에 `afterAccess()` 1회라는 짝이 코드 배치만으로 보장되어야 한다.\
카운터 스스로는 짝이 어긋난 것을 탐지하지 못한다.

**둘째, 획득과 반납이 다른 스레드에서 일어난다.**\
`beforeAccess()`는 `execute(...)`가 실행되는 **제출 스레드**에서 호출되고(:320), `afterAccess()`는 `TaskTrackingRunnable`이 실행되는 **워커 스레드**에서 호출된다(:505).\
그 사이를 `doExecute(...)`(:361)의 `newThread(task).start()`가 가른다.

```text
제출 스레드                                  워커 스레드
──────────────                              ──────────────
execute(task, timeout)  :311
  concurrencyThrottle.beforeAccess()  :320
      count 0 → 1
  doExecute(new TaskTrackingRunnable(...))
      newThread(task).start()   :362
          ─────────────────────────────►   TaskTrackingRunnable.run()  :481
  return (제출 스레드는 여기서 손을 뗀다)          …
                                              finally { afterAccess() }  :505
                                                  count 1 → 0
```

경계를 넘어 전달되는 것은 `TaskTrackingRunnable` 객체 하나뿐이다.\
수정 전 그 객체는 `task`와 `future`만 들고 있었고(:470, :472), **"내 몫의 permit이 있는가"라는 정보는 싣지 않았다.**\
그래서 워커 스레드는 반납해야 할지를 추측할 수밖에 없었다.

**셋째, 래퍼를 씌우는 조건과 permit을 얻는 조건이 다르다.**\
아래 3절의 분기도가 이 불일치를 정면으로 다룬다.\
`activeThreads`는 종료 대기나 취소를 켰을 때만 생긴다.

```text
trackActiveThreadsIfNecessary()                    SimpleAsyncTaskExecutor.java:283
    activeThreads = (taskTerminationTimeout > 0 || cancelRemainingTasksOnClose)
                      ? ConcurrentHashMap.newKeySet() : null
        ▲                                   ▲
        │ setTaskTerminationTimeout(:193)    │ setCancelRemainingTasksOnClose(:214)
```

한편 throttle 활성 여부는 완전히 별개의 설정에서 온다.

```text
setConcurrencyLimit(n)   :246 → concurrencyThrottle.setConcurrencyLimit(n)
isThrottleActive()       :263 → concurrencyThrottle.isThrottleActive()  (limit >= 0)
```

두 스위치가 독립이므로, 둘 다 켠 상태가 존재한다.\
그 조합이 3절에서 문제가 된다.

두 스위치를 가로세로로 놓으면, 위험한 칸이 하나뿐이라는 것이 한눈에 보인다.

```text
                       추적 꺼짐                추적 켜짐
                   (activeThreads=null)   (activeThreads != null)
                 +----------------------+----------------------+
 throttle 꺼짐   | 분기 3 plain         | 분기 2 tracking-only |
 (limit = -1)    | 래퍼 없음            | permit 없음          |
                 | permit 없음          | afterAccess 는 no-op |
                 +----------------------+----------------------+
 throttle 켜짐   | 분기 1 + 래퍼        | 분기 1 또는 분기 2   |
 (setConcurrency | cancelled 를 세울    | 버그 A 와 버그 B 가  |
  Limit 호출)    | 통로가 없다          | 둘 다 노출된다       |
                 +----------------------+----------------------+
```

오른쪽 아래 한 칸, 즉 `setConcurrencyLimit`과 종료 추적을 **둘 다** 켠 설정만이 이 PR의 영향권이다.

## 2. 수정 전 동작 워크플로우

대표 시나리오 둘을 잡는다.\
하나는 `submit(...)`으로 throttle을 정상적으로 통과하는 흐름, 다른 하나는 `close()`가 끼어드는 종료 시점 흐름이다.

### 2.1 정상 경로 — permit 획득에서 반납까지

`concurrencyLimit=2`, `taskTerminationTimeout>0`으로 설정된 executor에 `submit()`으로 태스크를 넘기는 흐름이다.

```text
호출자
  │  executor.submit(runnable)                              :340
  ▼
FutureTask<Object> future = new FutureTask<>(task, null)    :341
  │  execute(future, TIMEOUT_INDEFINITE)                    :342
  ▼
execute(Runnable task, long startTimeout)                   :311
  │
  ├─ Assert.notNull(task, ...)                              :312
  ├─ if (!isActive()) throw TaskRejectedException           :313
  │      isActive() = !closed.get()                         :275
  ├─ taskToUse = taskDecorator != null ? decorate(task) : task   :317
  ├─ future = (task instanceof Future<?> f ? f : null)      :318
  │      · submit 경로에서는 FutureTask 이므로 future != null
  │
  ├─ [분기 판정] isThrottleActive() && startTimeout > TIMEOUT_IMMEDIATE   :319
  │      · limit 2 >= 0 → true,  Long.MAX_VALUE > 0 → true
  ▼
  concurrencyThrottle.beforeAccess()                        :320
  │      └→ ConcurrencyThrottleSupport.beforeAccess()       :119
  │            limit == NO_CONCURRENCY(0) ?  아니오
  │            limit > 0 → lock 획득
  │               count(0) >= limit(2) ?  아니오 → onLimitReached() 건너뜀
  │               count++  →  1                             :132
  │            unlock
  ▼
  doExecute(new TaskTrackingRunnable(taskToUse, future))    :322
  │      └→ newThread(task).start()                         :362
  │             virtualThreadDelegate / threadFactory / createThread 중 택1  :374
  ▼  ─────────────────────── 스레드 경계 ───────────────────────
  TaskTrackingRunnable.run()                                :481   [워커 스레드]
  │
  ├─ Set<Thread> threads = activeThreads                    :482
  ├─ if (threads != null)                                   :484
  │     thread = Thread.currentThread()                     :485
  │     synchronized (threads) {                            :486
  │         checkCancelled(this.future)   ← try 바깥!       :487
  │         threads.add(thread)                             :488
  │     }
  ├─ try { this.task.run() }                                :491-493
  └─ finally {                                              :494
        if (threads != null) {
            threads.remove(thread)                          :496
            if (closed.get()) { … threads.notify() }        :497-503
        }
        concurrencyThrottle.afterAccess()   ← 무조건 호출     :505
            └→ count-- → 0, signal()                        :191,:195
     }
```

여기까지는 짝이 맞는다.\
문제는 이 흐름의 **양 끝이 조건에 따라 따로 움직인다**는 데 있다.

### 2.2 종료 경로 — `close()`가 끼어드는 지점

`close()`는 워커 스레드와 다른 스레드에서 호출되며, `cancelled` 플래그를 세운다.

> **CAS(compare-and-set)** — "현재 값이 A일 때만 B로 바꾼다"를 원자적으로 수행하는 연산.\
> 예: `closed.compareAndSet(false, true)`가 성공한 스레드 하나만 `close()` 본문으로 들어가므로, 동시에 두 번 닫히는 일이 없다.

```text
close()                                                     :390
  │
  ├─ closed.compareAndSet(false, true) 성공한 스레드만 진입   :391
  ├─ threads = this.activeThreads                            :392
  ├─ if (threads != null)
  │     ├─ if (cancelRemainingTasksOnClose)                  :394
  │     │      synchronized (threads) { this.cancelled = true }   :395-397
  │     │      threads.forEach(Thread::interrupt)            :399  (조기 인터럽트)
  │     └─ if (taskTerminationTimeout > 0)                   :401
  │            synchronized (threads) {
  │                threads.wait(taskTerminationTimeout)      :405  ← 종료 대기
  │                this.cancelled = true                     :411
  │            }
  │            if (!cancelRemainingTasksOnClose)
  │                threads.forEach(Thread::interrupt)        :415  (지연 인터럽트)
  ▼
checkCancelled(Future)                                       :422   [워커 스레드에서 호출]
  │  ※ 호출자가 이미 synchronized(threads) 안에 있다는 전제 (:423 주석)
  ├─ if (this.cancelled)
  │     ├─ if (future != null) future.cancel(false)          :425
  │     └─ throw new CancellationException(...)              :427
  └─ 아니면 조용히 반환
```

`cancelled`가 서는 자리는 두 곳(:396, :411)이고, 두 곳 다 `close()` 안이다.\
워커 스레드는 `run()` 진입 직후 `checkCancelled`(:487)에서 그 플래그를 읽는다.\
즉 **"permit은 이미 얻었지만 아직 태스크는 시작하지 않은" 창**이 존재하고, 그 창 안에 `close()`가 들어오면 `run()`은 태스크를 실행하지 않고 예외로 빠져나간다.

## 3. 분기 처리 워크플로우

두 층의 분기를 본다.\
제출 시점 3분기(`execute`)와 실행 시점의 제어 흐름(`run`)이다.\
**버그는 두 분기가 서로를 모른다는 데서 나온다.**

### 3.1 제출 시점 — `execute(Runnable, long)`의 3분기

제출 스레드는 두 개의 조건을 차례로 물어 세 갈래 중 하나를 고르고, 그중 permit을 얻는 것은 첫 갈래뿐이다.

```text
execute(task, startTimeout)                                             :311
        │
        ▼
   isActive() ?  ── 아니오 ──► TaskRejectedException ("is not active")   :314
        │ 예
        ▼
   isThrottleActive() && startTimeout > TIMEOUT_IMMEDIATE ?             :319
        │                       (TIMEOUT_IMMEDIATE = 0,
        │                        TIMEOUT_INDEFINITE = Long.MAX_VALUE)
   ┌────┴─────────────────────────────────┐
   │ 예                                    │ 아니오
   ▼                                       ▼
[분기 1] throttled                   activeThreads != null ?            :330
  beforeAccess()   :320  count++      ┌────┴────────────┐
  try {                               │ 예              │ 아니오
    doExecute(new TaskTracking        ▼                 ▼
      Runnable(taskToUse, future))  [분기 2]          [분기 3] plain
  } catch (Throwable) {              tracking-only     doExecute(taskToUse)  :334
    afterAccess()  :326  count--     doExecute(new       · 래퍼 없음
    throw TaskRejectedException      TaskTracking        · permit 없음
  }                                    Runnable(...))    · 회계 무관 — 정상
                                       :331
      permit 있음 + 래퍼 있음          permit 없음 + 래퍼 있음  ◀◀ 버그 A의 씨앗
      → 짝이 맞을 수 있다              → 래퍼가 반납을 시도한다
```

분기표로 정리하면 불일치가 한 칸에 몰려 있다.

| 분기 | 조건 | `beforeAccess()` | 래퍼(`TaskTrackingRunnable`) | 수정 전 `finally`의 `afterAccess()` |
|---|---|---|---|---|
| 1 throttled | throttle 활성 && `startTimeout > 0` | 호출 | 씌움 | 호출 — **맞음** |
| 2 tracking-only | 위가 아님 && `activeThreads != null` | 호출 안 함 | 씌움 | 호출 — **틀림(버그 A)** |
| 3 plain | 나머지 | 호출 안 함 | 안 씌움 | 도달 안 함 — 맞음 |

분기 2에 도달하는 조합은 좁지만 실재한다.\
throttle을 켜 두고(`setConcurrencyLimit`) 동시에 종료 추적도 켠(`setTaskTerminationTimeout` 또는 `setCancelRemainingTasksOnClose`) 상태에서, deprecated 오버로드 `execute(task, TIMEOUT_IMMEDIATE)`를 직접 부르면 조건 `startTimeout > TIMEOUT_IMMEDIATE`가 `0 > 0`이라 거짓이 되어 분기 1을 건너뛴다.\
`execute(Runnable)`(:296)과 `submit(...)`(:340, :348)은 항상 `TIMEOUT_INDEFINITE`를 넘기므로 이 분기로 오지 않는다.

### 3.2 실행 시점 — `TaskTrackingRunnable.run()`의 제어 흐름

워커 스레드 쪽 흐름에서 눈여겨볼 것은 `checkCancelled`가 `try` 블록 바깥에 있어 예외 이탈 시 `finally`가 아예 시작되지 않는다는 점이다.

```text
run()                                                                   :481
   │
   ├─ threads = activeThreads ;  thread = null                          :482,:483
   │
   ├─ threads != null ?                                                 :484
   │     ├ 아니오 ──────────────────────────────┐
   │     └ 예                                    │
   │        thread = Thread.currentThread()  :485│
   │        synchronized (threads) {          :486│
   │            checkCancelled(future)        :487│  ◀◀ try 블록 바깥
   │              ├ cancelled == true  ──► CancellationException 던짐
   │              │                          │
   │              │     ┌────────────────────┘
   │              │     ▼
   │              │   run() 이 그대로 종료 — finally 미실행               ◀◀ 버그 B
   │              │   → afterAccess() 호출 안 됨 → permit 영구 손실
   │              └ cancelled == false → 계속
   │            threads.add(thread)           :488
   │        }                                     │
   │                                              │
   ├──────────────────────────────────────────────┘
   ▼
   try { task.run() }                                                   :491-493
   │
   └─ finally {                                                         :494
         threads != null ?
            ├ 예: threads.remove(thread)                                :496
            │     closed.get() ? → synchronized { isEmpty() → notify() } :497-503
            └ 아니오: 건너뜀
         concurrencyThrottle.afterAccess()   ← 조건 없이 항상            :505
      }
```

### 3.3 버그 A — 획득 없는 반납 (분기 2 + 무조건 반납)

스레드 간 인터리빙으로 보면 이렇다.\
`limit=2`, `taskTerminationTimeout>0`.

> **인터리빙(interleaving)** — 여러 스레드의 명령이 실제 실행 시 서로 끼어들어 섞이는 순서.\
> 예: 아래 표의 t0~t12는 제출 스레드와 워커 스레드의 동작이 번갈아 실행되는 한 가지 순서를 시각 순으로 펼친 것이다.

```text
시각  제출 스레드 T1                        워커 스레드 W1        concurrencyCount
────  ─────────────────────────────────   ──────────────────   ───────────────
 t0   execute(task, TIMEOUT_IMMEDIATE)                                  0
 t1   isThrottleActive() → true
      startTimeout(0) > 0 → false
      ⇒ 분기 1 건너뜀
 t2   activeThreads != null → 분기 2  :330                              0
      ※ beforeAccess() 호출 없음
 t3   doExecute(new TaskTracking
        Runnable(task, future))
      newThread(...).start()  ────────►  run() 시작   :481               0
 t4   return                              checkCancelled → 통과
 t5                                       threads.add(thread)           0
 t6                                       task.run()                    0
 t7                                       finally:
                                            threads.remove(thread)
 t8                                         afterAccess()   :505       -1  ◀◀ 어긋남
                                              count-- : 0 → -1

  이후 다른 제출자가 들어오면
 t9   T2: beforeAccess()
        count(-1) >= limit(2) ? 아니오 → 통과, count 0
 t10  T3: beforeAccess() → count 1
 t11  T4: beforeAccess() → count 2
 t12  T5: beforeAccess() → count(2) >= 2 → 대기
      ⇒ 한도 2인데 실제로는 3개가 동시에 통과했다
```

피해의 성격은 **조용한 완화**다.\
예외도 로그도 없고, `getConcurrencyLimit()`은 여전히 2를 돌려준다.\
immediate 태스크를 던질 때마다 카운트가 더 내려가므로 설정값과 실제 동시성의 괴리는 누적된다.

### 3.4 버그 B — 반납 없는 획득 (`checkCancelled`가 `try` 바깥)

이쪽은 세 스레드가 얽힌다.\
`limit=1`, `cancelRemainingTasksOnClose=true`.

```text
시각  제출 스레드 T1              close() 스레드 T2           워커 스레드 W1     count
────  ────────────────────────   ────────────────────────   ──────────────   ─────
 t0   execute(task, INDEFINITE)                                                0
 t1   분기 1 진입  :319
      beforeAccess()   :320                                                    1
 t2   doExecute(래퍼)
      newThread(...).start()  ──────────────────────────────► (스레드 생성 중)  1
 t3   return
 t4                             close()  :390                                  1
 t5                             closed CAS false→true  :391
 t6                             synchronized (threads) {
                                    cancelled = true  :396
                                }
 t7                             threads.forEach(interrupt)  :399
                                  · threads 는 아직 비어 있다
                                    (W1 이 add 하기 전)
 t8                                                        run() 시작  :481     1
 t9                                                        threads != null
                                                           thread = currentThread
 t10                                                       synchronized (threads) {
                                                             checkCancelled()  :487
                                                               cancelled → true
                                                               future.cancel(false)
                                                               throw Cancellation
                                                                 Exception  :427
                                                           }
 t11                                                       ▼
                                                           run() 이 try 에
                                                           들어가기 전에 종료
                                                           finally 미실행        1  ◀◀ 누수
 t12                                                       스레드 종료
                                                           (예외는 기본
                                                            UncaughtException
                                                            Handler 로)
```

이후 상태가 문제다.

```text
 t13  T3: execute(...) → beforeAccess()
          count(1) >= limit(1) → onLimitReached()   ConcurrencyThrottleSupport:127
            ├ rejectTasksWhenLimitReached == false (기본)
            │    → concurrencyCondition.await()  :157  ── 무한 대기
            │      (깨워 줄 afterAccess() 를 호출할 주체가 이제 없다)
            └ rejectTasksWhenLimitReached == true
                 → onAccessRejected(...) → TaskRejectedException  :454
```

즉 permit 하나가 영구히 사라져 throttle의 유효 용량이 줄고, 한도가 1이었다면 executor가 사실상 죽는다.\
그리고 이 경로는 `submit(...)`·`execute(Runnable)` 같은 통상 API로 도달한다 — 필요한 조건은 throttle 활성 + 추적 활성 + 태스크가 워커에 닿기 전 `close()`뿐이고, 그것은 애플리케이션 종료 때마다 벌어지는 경합이다.

### 3.5 이미 막혀 있던 세 번째 구멍

분기 1의 `catch`(:324-328)는 이 PR 이전에 이미 고쳐진 자리다.\
`doExecute`가 스레드 생성에 실패하면 워커가 아예 없으므로 아무도 반납할 수 없다 — 그래서 제출 스레드가 직접 반납한다.

```text
 t0   beforeAccess()                     count 0 → 1
 t1   doExecute(...) 가 Throwable 던짐
 t2   catch { afterAccess() }  :326      count 1 → 0
 t3   throw TaskRejectedException :327
```

세 구멍을 한 표로 놓으면 이 PR의 위치가 보인다.

| 구멍 | 원인 | 상태(HEAD 기준) |
|---|---|---|
| 스레드 생성 실패 | 워커가 없어 반납 주체 부재 | 이미 수정됨 (`:324-328`) |
| A: 획득 없는 반납 | 래퍼가 permit 유무를 모름 | **이 PR** |
| B: 반납 없는 획득 | `checkCancelled`가 `try` 바깥 | **이 PR** |

## 4. 스프링 전역에서의 자리

`SimpleAsyncTaskExecutor`는 `spring-core`의 `TaskExecutor` 계층에서 **여러 모듈의 기본 실행기(default)** 역할을 한다.\
grep으로 확인한 실제 생성·상속 지점은 다음과 같다.

> **폴백(fallback)** — 지정된 것이 없을 때 대신 쓰이는 기본 선택지.\
> 예: `@Async`에 executor를 지정하지 않으면 `AsyncExecutionInterceptor`가 `new SimpleAsyncTaskExecutor()`를 만들어 쓴다.

```text
org.springframework.core.task.SimpleAsyncTaskExecutor
   │
   ├─ [상속] SimpleAsyncTaskScheduler
   │      spring-context/.../scheduling/concurrent/SimpleAsyncTaskScheduler.java:103
   │        · doExecute(Runnable) 를 오버라이드해 targetTaskExecutor 로 위임 :222
   │        · execute/submit 을 오버라이드해 에러 핸들러로 감싼 뒤 super 호출 :255,:261
   │        · close() 오버라이드 — 트리거·고정지연 executor 종료 후 super.close() :375
   │      ⇒ throttle·추적 회계는 전부 상위 클래스 것을 그대로 쓴다
   │
   ├─ [상속] RequestMappingHandlerAdapter.MvcSimpleAsyncTaskExecutor
   │      spring-webmvc/.../mvc/method/annotation/RequestMappingHandlerAdapter.java:1068
   │        · Spring MVC 비동기 처리의 기본 executor (필드 :176)
   │
   ├─ [기본값] AsyncExecutionInterceptor.getDefaultExecutor(...)
   │      spring-aop/.../interceptor/AsyncExecutionInterceptor.java:157
   │        return (defaultExecutor != null ? defaultExecutor : new SimpleAsyncTaskExecutor())
   │      ⇒ @Async 에 지정된 executor 가 없을 때의 최종 폴백
   │        (EnableAsync javadoc :64 가 이 폴백을 명시)
   │
   ├─ [기본값] WebAsyncManager.DEFAULT_TASK_EXECUTOR
   │      spring-web/.../request/async/WebAsyncManager.java:67
   │
   ├─ [기본값] JdkClientHttpRequestFactory
   │      spring-web/.../client/JdkClientHttpRequestFactory.java:65
   │        httpClient.executor().orElseGet(SimpleAsyncTaskExecutor::new)
   │
   ├─ [기본값] DefaultMessageListenerContainer.createDefaultTaskExecutor()
   │      spring-jms/.../listener/DefaultMessageListenerContainer.java:905
   │
   └─ [기본값] spring-websocket 다수
          StandardWebSocketClient.java:68 / EndpointConnectionManager.java:60
          AnnotatedEndpointConnectionManager.java:49
          RestClientXhrTransport.java:57 / RestTemplateXhrTransport.java:64
```

여기서 노출면을 정확히 좁혀 두는 것이 중요하다.\
**버그 A·B 모두 `concurrencyLimit`을 명시적으로 설정한 경우에만 발생한다.**\
기본값은 `UNBOUNDED_CONCURRENCY`(-1)이고(`ConcurrencyThrottleSupport.java:77`), 그때 `isThrottleActive()`는 `limit >= 0`이 거짓이므로(:108) 분기 1 자체가 성립하지 않는다.\
위 목록의 "기본값" 항목들은 대부분 한도를 설정하지 않은 채 쓰이므로 영향권 밖이다.

영향권은 이렇게 정리된다.

```text
throttle 활성 (setConcurrencyLimit 호출)  ── 아니오 ──► 분기 3 또는 분기 2,
        │                                              반납 코드가 no-op
        │ 예                                            (afterAccess 는 limit<0 이면
        ▼                                                아무것도 안 함 :187)
활성 스레드 추적 (taskTerminationTimeout>0
  또는 cancelRemainingTasksOnClose=true)
        │
        ├─ 아니오 → 분기 1 + 래퍼, close() 가 cancelled 를 세울 통로가 없음
        │            ⇒ 버그 B 미발생 (checkCancelled 블록 자체가 실행 안 됨)
        │
        └─ 예 → 버그 A·B 노출
                 · A: execute(task, TIMEOUT_IMMEDIATE) 를 직접 호출할 때
                 · B: 종료 시점 경합 — submit/execute 통상 API 로 도달
```

한도를 설정하는 실제 사용처로는 `@ConcurrencyLimit` 문서가 이 executor를 명시적으로 가리킨다(`spring-context/.../resilience/annotation/ConcurrencyLimit.java:58`).\
다만 그 어노테이션 자체는 AOP 인터셉터(`ConcurrencyThrottleInterceptor`) 경로를 쓰므로, executor의 throttle과는 같은 지원 클래스를 공유할 뿐 다른 무대다.

## 5. 관련 개념

### 5.1 permit(허가증) 모델 — 소유권 없는 카운터

`ConcurrencyThrottleSupport`가 구현하는 것은 세마포어와 같은 형태의 permit 모델이다.\
다만 JDK의 `java.util.concurrent.Semaphore`와 달리 **획득한 주체를 기록하지 않는다.**

> **세마포어(semaphore)** — permit 개수를 세어 동시 진입자 수를 제한하는 동시성 도구.\
> 예: JDK의 `Semaphore`는 `acquire()`로 한 장 집고 `release()`로 돌려놓으며, 여기서는 그 역할을 `beforeAccess()`/`afterAccess()`가 맡는다.

```text
Semaphore 스타일 계약                     이 구현의 실제
──────────────────────────────         ─────────────────────────────
acquire() ↔ release() 짝                beforeAccess() ↔ afterAccess() 짝
permit 개수만 센다                       count 하나만 센다  (:79)
누가 들고 있는지 모른다                   똑같이 모른다
release() 를 더 부르면?                   count 가 음수로 내려간다
   Semaphore 는 permit 이 늘어난다         → 한도가 조용히 커진다 (버그 A)
acquire 후 release 를 빠뜨리면?           count 가 안 내려간다
   permit 이 영구 소실                     → 한도가 조용히 작아진다 (버그 B)
```

소유권이 없다는 것은 **정합성 검사가 불가능**하다는 뜻이다.\
그래서 이런 모델에서는 "코드 배치"가 유일한 방어선이 된다.\
획득 지점과 반납 지점이 같은 스코프 안에 있으면 `try`/`finally`가 짝을 강제하지만, 이 무대처럼 두 지점이 스레드 경계를 사이에 두고 갈라져 있으면 배치만으로는 부족하다 — 소유 여부를 **데이터로 실어 보내야** 한다.\
PR이 `TaskTrackingRunnable`에 `boolean releaseThrottle`을 추가하는 것이 정확히 그 조치다.

### 5.2 `try`/`finally`의 보증 범위

`finally`는 마법이 아니라 **그것이 감싸는 `try` 블록에 진입했을 때만** 실행된다.\
수정 전 `run()`은 정리해야 할 리소스(permit)를 이미 들고 있는 상태에서 `try` 밖에 실패 가능한 호출을 두었다.

```text
잘못된 배치 (수정 전)                     올바른 배치 (수정 후)
─────────────────────────────         ──────────────────────────────
if (threads != null) {                 try {
    synchronized (threads) {               if (threads != null) {
        checkCancelled(future);  ▲             synchronized (threads) {
        threads.add(thread);     │                 checkCancelled(future);
    }                            │                 threads.add(thread);
}                          여기서 던지면          }
try {                      아래 finally 가        }
    task.run();            아예 시작되지          task.run();
}                          않는다             }
finally {                              finally {
    …                                      …
    afterAccess();                         if (releaseThrottle) afterAccess();
}                                      }
```

일반화하면 규칙은 하나다.\
**정리 대상 리소스를 획득한 시점부터 `try`가 시작되어야 한다.**\
이 무대에서 리소스 획득은 다른 스레드(`execute`의 `beforeAccess()`)에서 일어났으므로, 워커 스레드 입장에서는 `run()`의 첫 줄부터 이미 "리소스를 들고 있는 상태"다.\
따라서 `run()` 본문 전체가 `try` 안에 있어야 한다.

`try` 범위를 넓힐 때 걸리는 지점이 하나 있는데, 코드는 그것을 피해 간다.\
`finally`의 `threads.remove(thread)`(:496)가 `checkCancelled` 실패 시에도 실행되는데, `thread` 대입(:485)이 `synchronized` 블록보다 앞에 있으므로 그 시점에 `thread`는 이미 non-null이다.\
`ConcurrentHashMap.newKeySet()`은 null 인자를 거부하므로 대입 순서가 반대였다면 `finally`에서 `NullPointerException`이 났을 것이다.\
아직 집합에 넣지 않은 스레드를 지우는 것이라 동작상 무해한 no-op이다.

### 5.3 조건 변수와 깨움 — 왜 누수가 곧 데드락인가

`onLimitReached()`의 기본 구현은 큐잉이 아니라 **제출 스레드 블로킹**이다.

```text
ConcurrencyThrottleSupport.onLimitReached()                              :145
    while (count >= limit) {
        concurrencyCondition.await();      :157   ← 여기서 잠든다
    }

깨우는 유일한 주체
ConcurrencyThrottleSupport.afterAccess()                                 :186
    count--                                :191
    concurrencyCondition.signal()          :195   ← 잠든 스레드 하나를 깨운다
```

`await()`와 `signal()`이 1:1로 대응하므로, 반납이 한 번 사라지면 **깨어날 기회도 한 번 사라진다.**\
한도가 1인 경우에는 그 한 번이 전부라, 이후 모든 제출자가 영구히 잠든다.\
버그 B의 피해가 "성능 저하"가 아니라 "정지"인 이유다.

`rejectTasksWhenLimitReached=true`(:229)로 두면 블로킹 대신 즉시 거절로 바뀌지만(`ConcurrencyThrottleAdapter.onLimitReached()` :444), 누수된 permit이 돌아오지 않는 것은 같으므로 결국 모든 후속 제출이 `TaskRejectedException`이 된다.\
어느 쪽이든 executor는 회복하지 못한다.

### 5.4 풀 없는 실행기 — 상한을 자료구조가 아니라 카운터가 지킨다

`SimpleAsyncTaskExecutor`는 스레드를 재사용하지 않는다(클래스 javadoc :46).\
태스크마다 `newThread(task).start()`(:362)다.

```text
스레드 풀 (ThreadPoolTaskExecutor)          이 실행기
─────────────────────────────────        ──────────────────────────────
고정된 워커 집합 + 작업 큐                태스크마다 새 스레드
maxPoolSize 가 구조적으로 상한            상한을 강제하는 자료구조가 없다
큐가 차면 거절 정책                       제출자를 세워서(블로킹) 상한을 흉내
동시 실행 수 = 살아 있는 워커 수           동시 실행 수 = concurrencyCount 가 믿는 값
```

오른쪽 열의 마지막 행이 핵심이다.\
**여기서 동시성 한도는 관측된 사실이 아니라 카운터가 "믿는" 값이다.**\
실제 살아 있는 스레드 수와 카운터를 대조하는 코드가 어디에도 없으므로, 카운터가 어긋나면 그것을 반증할 수단이 없다.\
버그 A와 B가 둘 다 예외 없이, 로그 없이 진행되는 구조적 이유가 이것이다.

`activeThreads`(:93)는 살아 있는 스레드 집합을 실제로 들고 있지만, 용도는 종료 대기와 인터럽트뿐이고(:399, :404-406, :415) throttle 회계와는 연결되어 있지 않다.\
즉 정합성 검증에 쓸 수 있는 재료가 옆에 있었는데도 쓰이지 않는다.
