# java/syntax/54 — `java.util.concurrent`: `ExecutorService`·`Future`·`CompletableFuture` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **선행** — [`../25-exceptions/`](../25-exceptions/) (예외 전파·삼키기) · [`../31-functional-interfaces/`](../31-functional-interfaces/) (`Runnable`·`Callable`·`Supplier` 의 시그니처) · [`../26-try-with-resources/`](../26-try-with-resources/) (`close()` 가 언제 불리나 — **`ExecutorService` 가 21에서 `AutoCloseable` 이다**).
> **기준 소스** — [`java.util.concurrent` 패키지 javadoc (Java SE 21)](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/package-summary.html) · [`ExecutorService`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/ExecutorService.html) · [`Future`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/Future.html) · [`CompletableFuture`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/CompletableFuture.html) · [`ThreadPoolExecutor`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/ThreadPoolExecutor.html) · 이 머신의 `lib/src.zip` 에서 **직접 읽은** `java.base/java/util/concurrent/Executors.java`·`ExecutorService.java`·`Future.java`.
> **실행 검증** — 이 문서의 모든 출력·에러·스택트레이스·컴파일 에러는 Temurin **JDK 21.0.5** 에서 실제로 돌려 얻은 것이다.\
> `ExecutorService` 의 `AutoCloseable` 여부는 **17.0.13 · 21.0.5 · 25.0.1** 과 `--release 17`/`--release 19` 로 각각 컴파일해 확인했다 — **17 에서는 컴파일 에러다.**
> ⚠️ **측정 조건** — JMH 가 아니다. 벽시계(`System.nanoTime`) 이고, 시간 수치는 `sleep` 으로 만든 **작업 길이가 지배**한다.\
> 머신 **24코어**(Linux x86-64). 스레드 이름·실행 순서는 **실행마다 다르다** — 이 문서의 출력은 한 번의 실행이고, 순서가 중요한 자리는 **반복 횟수**를 적었다.\
> 「JVM 이 안 끝난다」류는 `timeout 6` 으로 감싸 **종료 코드 124**(= 6초에 강제 종료됨)로 판정했다.
> **버전** — `ExecutorService`·`Future` 는 **`@since 1.5`**, `CompletableFuture` 는 **`@since 1.8`** 이다(`src.zip` 직접 확인).\
> ★ **`ExecutorService extends AutoCloseable` 과 `close()` 는 `@since 19`** 다 — `src.zip` 에서 `@since 19` 를 직접 읽었고 17 에서 컴파일 에러를 확인했다.\
> `Future.state()`·`resultNow()`·`exceptionNow()` 도 **`@since 19`**. `newVirtualThreadPerTaskExecutor` 는 **`@since 21`**.\
> `StructuredTaskScope` 는 **21 과 25 모두 `@PreviewFeature`** 다(`src.zip` 의 애너테이션을 직접 읽었다).
> **범위** — 스레드·스케줄링·컨텍스트 스위칭은 [`../../../../process-thread/`](../../../../process-thread/) 가 정본이다.\
> 그쪽은 **스레드가 무엇인가**까지, 여기는 **스레드를 직접 만들지 않고 일을 맡기는 API 의 형태**부터다.\
> **공용 ForkJoinPool 의 경합**은 [`../49-parallel-streams/`](../49-parallel-streams/) 가 이미 실측했다 — **여기서 다시 재지 않고 결론만 받는다.**\
> 락·`volatile` 의 문법은 [`../33-synchronized-and-volatile/`](../33-synchronized-and-volatile/) 가, 메모리 모델은 [`../../언어-특성/README.md`](../../언어-특성/README.md) §9 가 정본이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 javadoc·`src.zip` 으로, 출력은 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**`ExecutorService` 는 "일을 창구에 맡기는 것"이고, `Future` 는 "찾아갈 때 내는 번호표"다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 창구 직원 | 풀의 스레드(worker) |
| 대기 줄 | 작업 큐(`BlockingQueue`) |
| 접수증(번호표) | `Future` |
| **번호표를 들고 기다리기** | **`future.get()` — 블로킹된다** |
| **번호표를 버리기** | **`submit` 의 반환값을 안 받기 — 예외가 사라진다** |
| 접수 마감 | `shutdown()` — 받은 것은 다 처리한다 |
| 셔터 내리기 | `shutdownNow()` — 줄에 선 사람을 돌려보내고 진행 중인 것도 멈추려 한다 |
| 마감 후에 온 손님 | `RejectedExecutionException` |
| **정원 없는 대기 줄** | **`newFixedThreadPool` 의 무한 큐 — 줄이 끝없이 길어진다** |
| "끝나면 전화 주세요" | `CompletableFuture` — 값이 나오면 다음 단계를 잇는다 |

- 번호표는 **받아 둬야** 무슨 일이 있었는지 안다.\
  실측에서 `submit` 한 작업이 예외를 던졌는데 **화면에 아무것도 안 찍혔다.**
- 접수를 마감하지 않으면 **가게가 안 닫힌다.**\
  실측에서 `shutdown()` 을 빼먹은 프로그램이 **6초 뒤 강제 종료될 때까지 살아 있었다.**
- 대기 줄에 **정원이 없으면** 지표는 초록인 채로 메모리가 찬다.\
  실측에서 10만 건을 던졌더니 **스레드는 2개, 큐에는 99,992건**이 쌓였다.

```text
정원 없는 큐 (Executors.newFixedThreadPool)   정원 있는 큐 (ThreadPoolExecutor + ArrayBlockingQueue(3))

+----------------------------------+          +----------------------------------+
| 스레드 2  /  큐 99,992건          |          | 스레드 2  /  큐 3건 (상한)        |
| 예외 0건 · 에러 로그 0줄          |          | 20건 중 15건이 즉시 거절          |
+----------------------------------+          +----------------------------------+
   -> 어느 순간 OOM 으로 죽는다                  -> 밀리는 게 즉시 보인다
```

**똑같은 구조로** 자바가 이렇게 동작한다: 창구 = `ThreadPoolExecutor`, 대기 줄 = 그 안의 `BlockingQueue`.\
`Executors.newFixedThreadPool(n)` 은 `src.zip` 에서 읽은 그대로 **`new LinkedBlockingQueue<Runnable>()`** — **정원이 없다.**

실무에서 이게 사고를 내는 자리는 **"부하가 늘었는데 지표가 다 초록인데 갑자기 죽었다"** 이다.\
큐에 쌓이는 것은 **스레드 수에도, CPU 에도, 에러율에도 안 나타난다.**

> **`ExecutorService`** — 작업(`Runnable`/`Callable`)을 받아 스레드에서 실행해 주는 창구. `@since 1.5`.\
> 예: `es.submit(() -> 계산())` 을 부르면 내 스레드는 즉시 다음 줄로 간다.

> **`Future<V>`** — "나중에 값이 될 것"을 가리키는 번호표. `@since 1.5`.\
> 예: `f.get()` 을 부르는 순간 **내 스레드가 멈춰서** 결과를 기다린다.

> **작업 큐(work queue)** — 스레드가 다 바쁠 때 작업이 줄 서는 곳.\
> 예: `LinkedBlockingQueue` 는 정원이 `Integer.MAX_VALUE` 라 사실상 무한이다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 네 질문을 둔다.

1. 작업을 맡기고 **끝내는 절차**는 무엇인가 — 안 끝내면 무슨 일이 나나.
2. 작업이 던진 **예외는 어디로 가나** — `submit` 과 `execute` 가 왜 다른가.
3. `Executors` 의 팩토리들은 각각 **어떤 큐와 어떤 상한**을 갖는가.
4. `Future` 로 **안 되는 것**은 무엇이고 `CompletableFuture` 가 그중 무엇을 메우나.

## 동작 방식

### (1) 수명주기 — `shutdown` / `shutdownNow` / `close`

**언제 쓰나** — 풀을 만든 모든 코드에서. **안 하면 프로그램이 안 끝난다.**

**실행 결과** (`Ex.java` — 54-a, JDK 21.0.5)

```text
--- 1. shutdown 은 받은 일을 끝까지 한다
  shutdown() 호출
  isShutdown=true  isTerminated=false
      작업 1 끝
      작업 0 끝
      작업 3 끝
      작업 2 끝
  awaitTermination(5s) = true
  isTerminated=true
--- 2. shutdown 뒤에 submit 하면
  java.util.concurrent.RejectedExecutionException
  메시지: Task java.util.concurrent.FutureTask@5acf9800[Not completed, task = java.util.concurrent.Executors$RunnableAdapter@2c7b84de[Wrapped task = Ex$$Lambda/0x0000756444000c08@3fee733d]] rejected from java.util.concurrent.ThreadPoolExecutor@3d4eac69[Terminated, pool size = 0, active threads = 0, queued tasks = 0, completed tasks = 4]
--- 3. shutdownNow 는 큐에 남은 일을 돌려주고 돌던 스레드를 interrupt 한다
      작업 0 시작
  돌려받은 미실행 작업 수 : 4
  돌려받은 것의 타입      : java.util.concurrent.FutureTask
      작업 0 끝 (interrupted=true)
  awaitTermination(2s)  : true
--- 4. shutdownNow 가 멈추지 못하는 작업
  interrupt 를 확인하지 않는 루프: awaitTermination(500ms)=false
  실제로 끝나는 데 1900 ms 더 걸렸다
```

```text
shutdown()                                 shutdownNow()

  +------------------------+                 +------------------------+
  | 큐에 있는 것: 다 실행   |                 | 큐에 있는 것: 돌려준다  |
  | 새 접수: 거절          |                 | 새 접수: 거절          |
  | 진행 중: 끝까지        |                 | 진행 중: interrupt     |
  +------------------------+                 +------------------------+
          |                                           |
          v                                           v
   awaitTermination 으로 기다린다            돌려받은 List<Runnable> 로
                                             무엇이 안 돌았는지 안다
```

그림 해설 (한 단계씩):

- **`shutdown()` 은 즉시 반환한다.** `isShutdown=true` 인데 `isTerminated=false` 다.\
  **끝났는지 알려면 `awaitTermination` 을 따로 불러야 한다.**
- **`shutdownNow()` 는 큐에 남은 것을 `List<Runnable>` 로 돌려준다.** 실측에서 5건 중 1건만 돌고 **4건이 돌아왔다.**\
  돌려받은 것의 타입은 **`FutureTask`** 다 — 내가 넣은 람다가 아니다.
- **`shutdownNow()` 는 "멈춘다"가 아니라 "interrupt 를 보낸다"** 이다.\
  인터럽트를 안 보는 루프는 **500ms 안에 안 끝났고, 실제로 1,900 ms 를 더 돌았다.**
- 마감 뒤 `submit` 은 **`RejectedExecutionException`** 이고, 메시지에 **풀의 현재 상태가 통째로** 들어 있다\
  (`[Terminated, pool size = 0, active threads = 0, queued tasks = 0, completed tasks = 4]`).

비용 — `shutdown` 은 **접수만 막는다.** 실제로 끝났는지는 `awaitTermination` 이 답한다.

### (2) 안 닫으면 JVM 이 안 끝난다

**언제 쓰나** — CLI·배치·테스트가 "다 끝났는데 안 죽는다"일 때.

**실행 결과** (`Ex.java` — 54-b, 각각 `timeout 6` 으로 감쌌다, JDK 21.0.5)

```text
===== mode=forget
  main 끝 — shutdown 을 안 불렀다
  작업 실행됨
  [종료코드 124 — 124 는 timeout 이 6초에 죽였다는 뜻] 벽시계 6030 ms
===== mode=shutdown
  main 끝 — shutdown 을 불렀다
  작업 실행됨
  [종료코드 0 — 124 는 timeout 이 6초에 죽였다는 뜻] 벽시계 60 ms
===== mode=close
  try 블록 끝 — close() 가 불린다
  작업 실행됨
  close() 반환까지 9 ms
  [종료코드 0 — 124 는 timeout 이 6초에 죽였다는 뜻] 벽시계 75 ms
===== mode=close-long
  try 블록 끝 — close() 가 기다린다
  긴 작업 끝
  close() 가 1509 ms 기다렸다
  [종료코드 0 — 124 는 timeout 이 6초에 죽였다는 뜻] 벽시계 1579 ms
===== mode=daemon
  main 끝 — shutdown 안 불렀지만 데몬이다
  작업 실행됨(데몬 스레드)
  [종료코드 0 — 124 는 timeout 이 6초에 죽였다는 뜻] 벽시계 50 ms
```

```text
shutdown 을 안 불렀다                       shutdown / close 를 불렀다

  main 이 끝났다                              main 이 끝났다
  풀 스레드가 살아 있다 (데몬 아님)             풀 스레드가 종료됐다
        |                                           |
        v                                           v
  JVM 이 안 끝난다 (6초에 강제 종료, 코드 124)   60~75 ms 에 정상 종료 (코드 0)
```

그림 해설 (한 단계씩):

- **`Executors` 의 기본 스레드는 데몬이 아니다.** 실측에서 `isDaemon = false` 였다.\
  **비데몬 스레드가 하나라도 살아 있으면 JVM 은 안 끝난다.**
- **`close()`(21)는 `shutdown()` + 무기한 `awaitTermination`** 이다.\
  짧은 작업은 9 ms 에 반환했고, **1.5초짜리 작업이 있으면 1,509 ms 를 기다렸다.**
- `ThreadFactory` 로 데몬 스레드를 만들면 안 닫아도 JVM 이 끝난다 — **다만 작업이 중간에 잘린다.**

비용 — **`close()` 는 기다린다.** `try`-with-resources 로 감쌌다고 즉시 반환하지 않는다\
([`../26-try-with-resources/`](../26-try-with-resources/) 가 `close()` 호출 시점의 정본이다).

### (3) ★ `ExecutorService` 는 17 에서 `AutoCloseable` 이 아니다

**언제 쓰나** — 17 로 내려 컴파일할 때. **가장 자주 만나는 버전 경계다.**

**실행 결과** (`Ex.java` — 54-c, 같은 소스를 네 가지로 컴파일)

```text
=== JDK 21 javac (기본)
  컴파일 성공
=== JDK 21 javac --release 17
c/Ex.java:5: error: incompatible types: try-with-resources not applicable to variable type
        try (ExecutorService es = Executors.newFixedThreadPool(1)) {
                             ^
    (ExecutorService cannot be converted to AutoCloseable)
1 error
=== JDK 17 javac
c/Ex.java:5: error: incompatible types: try-with-resources not applicable to variable type
        try (ExecutorService es = Executors.newFixedThreadPool(1)) {
                             ^
    (ExecutorService cannot be converted to AutoCloseable)
1 error
=== JDK 25 javac
  컴파일 성공
=== JDK 21 javac --release 19
  컴파일 성공
```

**`src.zip` 에서 직접 읽은 선언**

```text
17.0.13 : public interface ExecutorService extends Executor {
21.0.5  : public interface ExecutorService extends Executor, AutoCloseable {
25.0.1  : public interface ExecutorService extends Executor, AutoCloseable {
          410:    default void close() {      (@since 19)
```

- **17 에는 `close()` 자체가 없다.** 인터페이스 선언에 `AutoCloseable` 이 없다.
- **19 부터 있다.** `--release 19` 가 통과하는 것으로 경계를 확인했다.
- 17 을 지원해야 하면 `try`-with-resources 대신 **`finally { es.shutdown(); }`** 를 쓴다.

### (4) ★ 예외가 어디로 가나 — `submit` 과 `execute` 가 갈린다

**언제 쓰나** — "작업이 도는지 안 도는지 모르겠다"일 때. **이 주제의 대표 사고다.**

**실행 결과** (`Ex.java` — 54-d, JDK 21.0.5)

```text
--- 1. submit 으로 던진 예외는 어디로 가나
  submit 직후 300ms — 화면에 아무것도 안 찍혔다
  f.isDone() = true
  f.state()  = FAILED   (@since 19)
  f.get() 이 던진 것 : java.util.concurrent.ExecutionException
  e.getMessage()   : java.lang.IllegalStateException: 터졌다
  e.getCause()     : java.lang.IllegalStateException: 터졌다
--- 2. execute 로 던진 예외는 어디로 가나
      [핸들러] Thread-0 : java.lang.IllegalStateException: 이번엔 execute
  (위 [핸들러] 줄이 execute 의 결과다)
--- 3. Future 를 안 받으면 submit 의 예외는 완전히 사라진다
  300ms 동안 아무 출력 없음
--- 4. 핸들러가 없으면 execute 의 예외는 어디로 찍히나
Exception in thread "pool-1-thread-1" java.lang.IllegalStateException: 기본 핸들러 경로
	at Ex.lambda$main$5(Ex.java:34)
	at java.base/java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1144)
	at java.base/java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:642)
	at java.base/java.lang.Thread.run(Thread.java:1583)
```

```text
submit(task)                               execute(task)

  예외 -> FutureTask 안에 저장              예외 -> 스레드 밖으로 전파
       |                                          |
       v                                          v
  f.get() 을 부를 때까지 아무도 모른다        UncaughtExceptionHandler 로 간다
  f 를 안 받으면 영영 모른다                  없으면 stderr 에 찍힌다
```

그림 해설 (한 단계씩):

- **`submit` 의 예외는 `Future` 안에 갇힌다.** 300 ms 동안 **화면에 한 줄도 안 찍혔다.**
- 꺼내는 순간 **`ExecutionException` 으로 한 겹 감싸여** 나온다.\
  `getMessage()` 가 **원인 예외의 `toString`** 이고, 진짜 원인은 `getCause()` 다.
- **`Future` 를 안 받으면 그 예외는 아무 데도 안 간다.** 이것이 가장 조용한 실패다.
- **`execute` 는 스레드 밖으로 던진다** — `UncaughtExceptionHandler` 가 있으면 거기로,\
  없으면 `Exception in thread "pool-1-thread-1" ...` 로 **stderr 에 찍힌다.**

**스택트레이스가 두 겹인 것**

```text
--- 5. 스택트레이스가 두 겹이다
  --- e 의 스택트레이스 (제출한 쪽)
      java.base/java.util.concurrent.FutureTask.report(FutureTask.java:122)
      java.base/java.util.concurrent.FutureTask.get(FutureTask.java:191)
      Ex.main(Ex.java:40)
  --- e.getCause() 의 스택트레이스 (실제로 터진 쪽)
      Ex.lambda$main$6(Ex.java:39)
      java.base/java.util.concurrent.FutureTask.run(FutureTask.java:317)
      java.base/java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1144)
      java.base/java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:642)
      java.base/java.lang.Thread.run(Thread.java:1583)
```

- **바깥 스택은 `get()` 을 부른 자리**이고, **`getCause()` 의 스택이 실제로 터진 자리**다.
- 로그에 `e` 만 찍으면 **원인 위치가 안 나온다.** 예외 연쇄는 [`../25-exceptions/`](../25-exceptions/) 가 정본이다.

**취소와 타임아웃**

```text
--- 6. 취소와 타임아웃
  get(200ms) : java.util.concurrent.TimeoutException (메시지 null)
  cancel(true) = true
  isCancelled  = true  isDone = true  state = CANCELLED
  취소 뒤 get() : java.util.concurrent.CancellationException
```

- `get(타임아웃)` 은 **`TimeoutException`**(메시지 `null`) 을 던진다. **작업은 계속 돈다.**
- `cancel(true)` 뒤에는 **`CancellationException`** 이다. `ExecutionException` 이 아니다.
- **`isDone()` 은 "성공"이 아니라 "끝났다"** 다 — 실패·취소도 `true` 다.\
  성공·실패·취소를 구분하려면 **`state()`**(`@since 19`) 를 쓴다: `SUCCESS`·`FAILED`·`CANCELLED`·`RUNNING`.

비용 — **`submit` 을 쓰면 `Future` 를 반드시 받는다.** 결과가 필요 없어도 `get()` 이나 `state()` 로 실패를 확인한다.

### (5) 풀 종류와 `newFixedThreadPool` 의 무한 큐

**언제 쓰나** — `Executors.new...` 중에서 고를 때.

**실행 결과** (`Ex.java` — 54-a, 작업 6개 제출, JDK 21.0.5)

```text
--- 5. 풀 종류별 스레드 이름과 개수 (작업 6개 제출)
  fixed(2)  스레드 2개 [pool-4-thread-1, pool-4-thread-2]
  single    스레드 1개 [pool-5-thread-1]
  cached    스레드 6개 [pool-6-thread-1, pool-6-thread-2, pool-6-thread-3, pool-6-thread-4, pool-6-thread-5, pool-6-thread-6]
--- 6. 풀 스레드는 데몬이 아니다
  isDaemon = false
```

**`src.zip` 에서 직접 읽은 팩토리 본문**

```text
    public static ExecutorService newFixedThreadPool(int nThreads) {
        return new ThreadPoolExecutor(nThreads, nThreads,
                                      0L, TimeUnit.MILLISECONDS,
                                      new LinkedBlockingQueue<Runnable>());
    }

    public static ExecutorService newCachedThreadPool() {
        return new ThreadPoolExecutor(0, Integer.MAX_VALUE,
                                      60L, TimeUnit.SECONDS,
                                      new SynchronousQueue<Runnable>());
    }
```

- **`newFixedThreadPool` 은 스레드에 상한이 있고 큐에는 없다.**
- **`newCachedThreadPool` 은 큐가 `SynchronousQueue`(정원 0)라 스레드에 상한이 없다** — `Integer.MAX_VALUE`.\
  실측에서 작업 6개에 **스레드 6개**가 생겼다.
- **두 팩토리가 정확히 반대 방향으로 무한하다.** 둘 다 부하가 몰리면 위험하다.

**실행 결과** (`Ex.java` — 54-e, JDK 21.0.5)

```text
--- 1. newFixedThreadPool 의 큐는 무한이다 (소스: new LinkedBlockingQueue<Runnable>())
  10만 건 제출 뒤 corePoolSize=2  maximumPoolSize=2  poolSize=2
  대기 큐에 쌓인 작업 수 : 99992
  큐 타입                : java.util.concurrent.LinkedBlockingQueue
  큐의 남은 자리          : 2147383656
--- 2. 정원이 있는 큐는 거절한다
  20건 중 받아들임 5 / 거절 15  (스레드 2 + 큐 3)
  거절 메시지: Task java.util.concurrent.FutureTask@30f39991[Not completed, task = java.util.concurrent.Executors$RunnableAdapter@2a84aee7[Wrapped task = Ex$$Lambda/0x0000737cb4000c08@a09ee92]] rejected from java.util.concurrent.ThreadPoolExecutor@279f2327[Running, pool size = 2, active threads = 2, queued tasks = 3, completed tasks = 0]
--- 3. maximumPoolSize 는 큐가 꽉 차야 쓰인다
  무한 큐        core=2 max=8 로 12건 제출 → 실제 최대 스레드 2개
  정원 2인 큐     core=2 max=8 로 12건 제출 → 실제 최대 스레드 8개
```

```text
무한 큐 (지표는 전부 초록)                  정원이 있는 큐 (밀어내기)
+---------------------------+              +---------------------------+
| 대기 99,992건             |              | 대기 3건 (상한)           |
| 스레드 2 · 예외 0 · CPU 낮음|              | 20건 중 15건 즉시 거절    |
+---------------------------+              +---------------------------+
  -> 어느 순간 OOM 으로 죽는다                -> 느려지는 게 즉시 보인다
```

그림 해설 (한 단계씩):

- **10만 건을 던졌는데 예외가 한 건도 안 났다.** 스레드는 2개, **큐에 99,992건**이 들어 있다.
- 큐의 남은 자리가 **21억**이다 — 사실상 메모리가 한계다.
- **`maximumPoolSize` 는 큐가 꽉 차야 쓰인다.** 무한 큐면 **영원히 `corePoolSize` 로만 돈다**(2개).\
  정원 2인 큐로 바꾸자 같은 설정이 **8개까지 늘었다.**
- ★ 그래서 **`new ThreadPoolExecutor(core, max, ...)` 에서 `max` 를 키워도 무한 큐면 아무 일도 안 일어난다.**

**거절 정책 네 가지**

```text
--- 4. 거절 정책 네 가지가 무엇을 하나 (스레드 1 + 큐 1 에 5건)
  AbortPolicy              실행 2건 / 예외 3건 / 그중 호출 스레드가 직접 실행 0건
  CallerRunsPolicy         실행 5건 / 예외 0건 / 그중 호출 스레드가 직접 실행 2건
  DiscardPolicy            실행 2건 / 예외 0건 / 그중 호출 스레드가 직접 실행 0건
  DiscardOldestPolicy      실행 2건 / 예외 0건 / 그중 호출 스레드가 직접 실행 0건
```

- **`AbortPolicy`(기본)** — `RejectedExecutionException` 을 던진다. **소리가 난다.**
- **`CallerRunsPolicy`** — 제출한 스레드가 **직접 실행**한다. 실측에서 5건 전부 돌았고 그중 **2건을 `main` 이 직접** 했다.\
  제출자가 느려지므로 **자연스러운 역압(backpressure)** 이 된다.
- **`DiscardPolicy`·`DiscardOldestPolicy`** — **조용히 버린다.** 예외 0건, 실행 2건.\
  **아무 흔적이 안 남는다** — 셋 중 가장 위험하다.

비용 — **운영 코드에서는 `Executors.newFixedThreadPool` 대신 `ThreadPoolExecutor` 를 직접 만든다.**\
큐에 정원을 주고, 거절 정책을 고르고, 스레드에 이름을 붙인다.

### (6) `Future` 로 안 되는 것 — `CompletableFuture` 의 경계

**언제 쓰나** — 결과 둘을 합치거나, 끝난 뒤 이어서 할 일이 있을 때.

**실행 결과** (`Ex.java` — 54-f, JDK 21.0.5)

```text
--- 1. Future 셋을 합치려면 하나씩 기다리는 수밖에 없다
  합 6, 307 ms (세 작업이 병렬로 돌아 300ms 근처)
  Future 가 가진 메서드 : [cancel, exceptionNow, get, get, isCancelled, isDone, resultNow, state]
--- 2. CompletableFuture 는 결과가 나오면 다음 단계를 붙인다
  thenCombine 결과 30, 302 ms
--- 3. 어느 스레드가 다음 단계를 도나
      supplyAsync(executor 지정) : pool-1-thread-1
      thenApply                  : main
      thenApplyAsync(기본)        : ForkJoinPool.commonPool-worker-1
      supplyAsync(기본)           : ForkJoinPool.commonPool-worker-1
--- 4. 예외가 감싸이는 방식이 다르다
  get()  : java.util.concurrent.ExecutionException → cause java.lang.IllegalStateException: CF 에서 터짐
  join() : java.util.concurrent.CompletionException → cause java.lang.IllegalStateException: CF 에서 터짐
  exceptionally 로 복구 : -1
  handle 로 둘 다 받기  : -2
--- 5. allOf / anyOf
  allOf().join() 반환값 : null (Void 다 — 값은 각자에서 꺼낸다)
  값은 따로: 1, 2
  anyOf().join()       : 빠른 쪽
--- 6. invokeAll 과 invokeAny
  invokeAll : 전부 isDone=true, 302 ms, 결과 순서 [A, B, C]
  invokeAny : B, 100 ms
--- 7. CompletableFuture.cancel 은 실행 중인 작업을 안 멈춘다
  cancel(true) = true  isCancelled=true
      (취소했는데도 작업은 끝까지 돌았다)
```

```text
Future                                     CompletableFuture

  메서드 8개 (get·cancel·isDone·state...)    thenApply / thenCombine / allOf /
  "값을 꺼낸다"만 할 수 있다                  exceptionally / handle ...
        |                                          |
        v                                          v
  합치려면 get() 으로 하나씩 기다린다          끝나면 다음 단계가 자동으로 이어진다
  기다리는 동안 내 스레드가 멈춘다             내 스레드는 즉시 돌아온다
```

그림 해설 (한 단계씩):

- **`Future` 의 메서드는 여덟 개뿐이다**(`get` 이 둘이니 실제로는 일곱 종류).\
  **"끝나면 ~해라"를 붙일 자리가 없다.** 합치려면 `get()` 으로 하나씩 기다린다.
- `CompletableFuture` 는 `thenCombine` 으로 **둘을 합쳐** 302 ms 에 끝냈다.
- **예외를 감싸는 타입이 다르다** — `get()` 은 `ExecutionException`, **`join()` 은 `CompletionException`**.\
  둘 다 `getCause()` 에 원인이 있다. `join()` 은 **검사 예외를 안 던져서** 람다 안에서 쓰기 편하다.
- **`allOf(...).join()` 은 `null` 을 준다**(`CompletableFuture<Void>`). 값은 각 `CompletableFuture` 에서 꺼낸다.
- **`invokeAll` 은 전부 끝날 때까지 블로킹**하고 **결과를 제출 순서대로** 준다(`[A, B, C]`).\
  **`invokeAny` 는 가장 먼저 끝난 하나**를 주고 나머지를 취소한다(100 ms 에 `B`).
- **`CompletableFuture.cancel(true)` 는 실행 중인 작업을 안 멈춘다.**\
  `isCancelled=true` 가 됐는데도 **작업은 끝까지 돌았다.** `FutureTask.cancel` 과 다른 점이다.

**다음 단계를 누가 도는가 — 30회 반복**

**실행 결과** (`Ex.java` — 54-g, 각 30회, 같은 명령을 3회)

```text
--- thenApply 를 누가 도나 (30회 반복)
  (A) 이미 끝난 CF 에 붙였을 때 : {main(붙인 스레드)=30}
  (B) 아직 도는 CF 에 붙였을 때 : {pool(작업을 돌린 스레드)=30}
--- thenApply 를 누가 도나 (30회 반복)
  (A) 이미 끝난 CF 에 붙였을 때 : {main(붙인 스레드)=30}
  (B) 아직 도는 CF 에 붙였을 때 : {pool(작업을 돌린 스레드)=30}
--- thenApply 를 누가 도나 (30회 반복)
  (A) 이미 끝난 CF 에 붙였을 때 : {main(붙인 스레드)=30}
  (B) 아직 도는 CF 에 붙였을 때 : {pool(작업을 돌린 스레드)=30}
```

- **`thenApply`(Async 없는 것)는 전용 스레드가 없다.**\
  이미 끝나 있으면 **붙이는 스레드**가, 아직 돌고 있으면 **완료시킨 스레드**가 실행한다.
- **`thenApplyAsync` 와 executor 없는 `supplyAsync` 는 공용 ForkJoinPool 로 간다.**\
  ★ **공용 풀을 남과 나눠 쓰는 위험은 [`../49-parallel-streams/`](../49-parallel-streams/) 가 이미 실측했다**(같은 코드가 풀 상태에 따라 2.6배 느려졌다).\
  결론만 받는다 — **서버 코드에서는 executor 를 명시한다.**

비용 — `CompletableFuture` 는 **블로킹을 안 하는 대신** 어느 스레드가 무엇을 도는지가 복잡해진다.\
**executor 를 명시하고 `*Async` 를 의식적으로 고른다.**

### (7) 주기 작업이 조용히 멈춘다

**언제 쓰나** — `ScheduledExecutorService` 로 헬스체크·정리·동기화를 돌릴 때.

**실행 결과** (`Ex.java` — 54-h, 100 ms 주기로 1초 동안, JDK 21.0.5)

```text
--- 1. 주기 작업이 예외를 던지면 그 뒤로 어떻게 되나
      1회차 실행
      2회차 실행
      3회차 실행
  1초 동안 실행된 횟수 : 3  (100ms 주기면 약 10회여야 한다)
  isDone=true  isCancelled=false  state=FAILED
  f.get() : java.util.concurrent.ExecutionException → cause java.lang.IllegalStateException: 3회차에서 터진다
  ★ 예외도 안 찍히고 주기만 조용히 멈춘다
--- 2. try/catch 로 감싸면
  1초 동안 실행된 횟수 : 11
```

```text
예외를 안 잡았을 때                          작업 안에서 try/catch 했을 때

  1회차 · 2회차 · 3회차(예외)                  1회차 ... 11회차
  +---------------------------+              +---------------------------+
  | 이후 실행: 0회             |              | 이후 실행: 계속            |
  | 화면 출력: 없음            |              | 화면 출력: 없음            |
  | 예외: Future 안에만 있다   |              | 예외: 내가 잡았다          |
  +---------------------------+              +---------------------------+
   -> 1초에 3회. 헬스체크가 죽었는데            -> 1초에 11회. 정상
      아무도 모른다
```

그림 해설 (한 단계씩):

- **한 번 예외가 나면 그 뒤로 영영 안 돈다.** 1초에 10회 돌아야 할 것이 **3회**에서 끝났다.
- **화면에 아무것도 안 찍힌다.** `submit` 과 같은 이유다 — 예외가 `Future` 안에 갇힌다((4)).
- `f.isDone()` 은 `true`, **`f.isCancelled()` 는 `false`**, `state()` 가 **`FAILED`** 다.  `get()` 을 해야 비로소 `ExecutionException` → 원인이 나온다.
- **고치는 법은 작업 본문을 `try`/`catch` 로 감싸는 것**이다 — 11회로 돌아왔다.

비용 — **주기 작업의 본문은 예외를 절대 밖으로 내보내지 않는다.** 이것이 `ScheduledExecutorService` 의 1번 함정이다.

### (8) 풀 안에서 같은 풀을 기다리면

**언제 쓰나** — 작업 안에서 또 작업을 제출할 때.

**실행 결과** (`Ex.java` — 54-h, JDK 21.0.5)

```text
--- 3. 같은 풀 안에서 같은 풀의 Future 를 기다리면 (단일 스레드 풀)
  java.util.concurrent.ExecutionException → cause java.util.concurrent.TimeoutException
--- 4. 스레드 2개짜리 풀에서 2건이 서로를 기다리면
  2건이 서로를 기다림 : a, b  (스레드가 2개라 통과한다)
  스레드 2개를 막아 놓고 3번째 작업 : c3  (1500 ms 기다렸다)
```

```text
단일 스레드 풀                              스레드 2개 풀

  바깥 작업이 유일한 스레드를 차지            2건이 서로를 기다려도 통과한다
  안쪽 작업은 큐에서 영원히 대기                 |
        |                                      v
        v                                 그러나 3번째 작업은 1,500 ms 를
  inner.get(2s) 가 TimeoutException         기다렸다 — 상한이 풀 크기다
```

그림 해설 (한 단계씩):

- **단일 스레드 풀에서 중첩 `get()` 은 영원히 안 끝난다.**  `get(2초)` 의 타임아웃이 없었다면 **예외도 없이 멈춰 있었을 것**이다.
- **스레드 2개면 2건이 서로를 기다려도 통과한다** — 그래서 **테스트에서 안 걸린다.**  운영에서 동시 요청이 풀 크기를 넘는 순간 걸린다.
- 세 번째 작업은 **1,500 ms** 를 기다렸다. **동시성의 상한은 풀 크기**다.
- ★ **규칙** — 작업 안에서 같은 풀에 제출하고 기다리지 않는다.  꼭 필요하면 **다른 풀**을 쓰거나 **가상 스레드**([`../56-virtual-threads/`](../56-virtual-threads/))로 간다.

비용 — 이 고갈은 **로그에 아무 흔적이 없다.** 응답이 안 올 뿐이다.

## 문법 — 형태와 규칙

### 만들고 닫는 최소 형태

```java
// 21+ — close() 가 shutdown + awaitTermination 을 한다
try (ExecutorService es = Executors.newFixedThreadPool(4)) {
    Future<Integer> f = es.submit(() -> 42);
    System.out.println(f.get());
}

// 17 이하 — close() 가 없다
ExecutorService es = Executors.newFixedThreadPool(4);
try {
    ...
} finally {
    es.shutdown();
    if (!es.awaitTermination(30, TimeUnit.SECONDS)) es.shutdownNow();
}
```

### `submit` 의 세 오버로드

```java
Future<?>        a = es.submit(() -> System.out.println("x"));   // Runnable  -> get() 은 null
Future<Integer>  b = es.submit(() -> 42);                        // Callable  -> get() 은 42
Future<String>   c = es.submit(() -> {}, "고정값");               // Runnable + 결과
es.execute(() -> System.out.println("x"));                       // 반환값 없음
```

- **람다가 값을 반환하면 `Callable`, 아니면 `Runnable` 로 추론된다.**\
  `Callable.call()` 은 **`throws Exception`** 이고 `Runnable.run()` 은 아니다 — [`../31-functional-interfaces/`](../31-functional-interfaces/) 참조.
- 그래서 **검사 예외를 던지는 람다는 `submit` 에는 되고 `execute` 에는 안 된다.**

### 운영용 풀을 직접 만드는 형태

```java
ThreadPoolExecutor pool = new ThreadPoolExecutor(
        8, 32,                                  // core, max
        60, TimeUnit.SECONDS,                   // 유휴 스레드 회수 시간
        new ArrayBlockingQueue<>(1000),         // 정원이 있는 큐
        r -> { Thread t = new Thread(r, "api-worker"); return t; },
        new ThreadPoolExecutor.CallerRunsPolicy());
```

- **큐에 정원을 준다.** 그래야 `max` 가 의미를 갖는다((5)).
- **스레드에 이름을 준다.** 스택트레이스와 스레드 덤프에서 바로 보인다.
- **거절 정책을 고른다.** 기본은 예외를 던지는 `AbortPolicy` 다.

### `Future` 와 `CompletableFuture` 의 API 표면

| 하려는 것 | `Future` | `CompletableFuture` |
|---|---|---|
| 값 꺼내기 | `get()` / `get(timeout)` | `get()` / `join()` |
| 끝났나 | `isDone()` | `isDone()` |
| 성공·실패·취소 구분 | `state()` (**19+**) | `state()` / `isCompletedExceptionally()` |
| 취소 | `cancel(true)` | `cancel(true)` — **실행 중인 것은 안 멈춘다** |
| 이어 붙이기 | **없다** | `thenApply` / `thenCompose` / `thenCombine` |
| 여러 개 기다리기 | `invokeAll`(executor 쪽) | `allOf` / `anyOf` |
| 예외 복구 | **없다** | `exceptionally` / `handle` / `whenComplete` |
| 직접 완료시키기 | **없다** | `complete(v)` / `completeExceptionally(t)` |

## 어디서 틀리나

### 1. `submit` 해 놓고 `Future` 를 안 받는다

- (4) 의 실측 — **300 ms 동안 아무것도 안 찍혔다.** 예외가 완전히 사라진다.
- 결과가 필요 없으면 **`execute` 를 쓴다.** 그러면 최소한 stderr 에는 찍힌다.

### 2. `shutdown()` 을 부르고 끝났다고 생각한다

- `shutdown()` 직후 `isTerminated=false` 다((1)).
- **`awaitTermination` 까지 불러야** 끝난 것을 안다.

### 3. `shutdownNow()` 가 작업을 멈춘다고 생각한다

- (1) 의 실측 — 인터럽트를 안 보는 루프는 **1,900 ms 를 더 돌았다.**
- 긴 루프 안에서 **`Thread.currentThread().isInterrupted()` 를 주기적으로 확인**해야 한다.

### 4. `InterruptedException` 을 삼킨다

- 삼키면 인터럽트 플래그가 지워져 **`shutdownNow()` 의 신호가 사라진다**.\
  [`../33-synchronized-and-volatile/`](../33-synchronized-and-volatile/) 의 실측 참조 — 잡은 직후 이미 `false` 다.

### 5. `Executors.newFixedThreadPool` 을 그대로 운영에 쓴다

- (5) 의 실측 — **큐에 99,992건이 쌓여도 예외 0건**이다.
- `ThreadPoolExecutor` 를 직접 만들고 **큐에 정원**을 준다.

### 6. `maximumPoolSize` 를 키워 놓고 안 늘어난다고 한다

- 무한 큐면 **영원히 `corePoolSize` 로만 돈다**(실측 2개).

### 7. `isDone()` 을 "성공"으로 읽는다

- 실패·취소도 `true` 다((4)). **`state()`**(19+) 를 쓰거나 `get()` 의 예외로 판정한다.

### 8. `ExecutionException` 을 그대로 로그에 찍는다

- 스택이 **`get()` 을 부른 자리**만 가리킨다((4)).
- **`getCause()` 를 찍어야** 실제로 터진 자리가 나온다.

### 9. 블로킹 I/O 를 공용 ForkJoinPool 에서 한다

- `CompletableFuture.supplyAsync(task)` 는 **executor 를 안 주면 공용 풀**이다((6)).
- ★ 공용 풀 경합의 실측은 [`../49-parallel-streams/`](../49-parallel-streams/) 가 정본이다 — **여기서 다시 재지 않는다.**
- **executor 를 반드시 지정한다.**

### 10. `CompletableFuture.cancel` 로 작업을 멈추려 한다

- (6) 의 실측 — `isCancelled=true` 인데 **작업은 끝까지 돌았다.**
- 정말 멈추려면 작업 쪽에서 **취소 플래그나 인터럽트를 확인**해야 한다.

### 11. `join()` 과 `get()` 의 예외 타입을 섞어 잡는다

- `get()` → **`ExecutionException`**, `join()` → **`CompletionException`**. 둘은 상속 관계가 아니다.

### 12. 스레드 풀 안에서 같은 풀의 작업을 `get()` 한다

- (8) 의 실측 — 단일 스레드 풀에서 **영원히 안 끝난다.** 타임아웃이 없으면 예외도 없다.
- 스레드 2개면 **통과한다** — 그래서 테스트에서 안 걸린다.

### 13. 주기 작업 본문에서 예외를 밖으로 내보낸다

- (7) 의 실측 — **1초에 10회 돌아야 할 것이 3회에서 멈췄고 화면에 아무것도 안 찍혔다.**
- 본문을 `try`/`catch` 로 감싼다. 감싸면 11회로 돌아온다.

## 구현 세부사항 대 언어 보장

| 관측한 것 | 누가 보장하나 | 버전에 갈리나 |
|---|---|---|
| `ExecutorService` 가 `AutoCloseable` 인 것 | **javadoc — `@since 19`** | ★ **갈린다.** 17 에서 컴파일 에러 |
| `Future.state()`·`resultNow()` | **javadoc — `@since 19`** | ★ 17 에 없다 |
| `newFixedThreadPool` 이 `LinkedBlockingQueue` 를 쓰는 것 | javadoc 이 "unbounded queue" 라고 적는다. **큐 클래스 이름은 구현 세부** | 17·21·25 소스 동일(확인함) |
| `RejectedExecutionException` 메시지에 풀 상태가 들어가는 것 | **구현 세부**(`ThreadPoolExecutor.toString`) | 21 에서만 확인 |
| 스레드 이름 `pool-N-thread-M` | **구현 세부**. `ThreadFactory` 로 바꿀 수 있다 | 21 에서만 확인 |
| 풀 번호(`pool-4`, `pool-5`)가 프로그램 안에서 증가하는 것 | 구현 세부 — **JVM 안의 전역 카운터** | 21 에서만 확인 |
| `thenApply` 가 붙인 스레드에서 도는 것 | **javadoc 이 "may be performed by the thread that completes ... or by any other caller" 로 적는다** — 어느 쪽인지는 보장 아님 | 21 에서 30회 × 3 반복 |
| `invokeAll` 의 결과 순서가 제출 순서인 것 | **javadoc 이 보장**("in the same sequential order as produced by the iterator") | 21 에서만 확인 |
| `shutdownNow` 가 `FutureTask` 를 돌려주는 것 | javadoc 은 `List<Runnable>` 만 약속한다. **구체 타입은 구현 세부** | 21 에서만 확인 |
| `StructuredTaskScope` 가 프리뷰인 것 | `src.zip` 의 `@PreviewFeature` | **21 과 25 모두 프리뷰** |

★ **"세 버전에서 같았다"는 보장이 아니다.** 이 문서에서 세 소스가 같았던 `Executors` 팩토리 본문도 **관찰**로만 적었다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| CPU 바운드 작업 N개를 나눠 돌린다 | `newFixedThreadPool(코어 수)` 또는 병렬 스트림 | 스레드를 코어 수 이상 만들 이유가 없다 |
| 요청마다 블로킹 I/O 를 한다 | **가상 스레드**([`../56-virtual-threads/`](../56-virtual-threads/)) | 스레드가 싸다. 풀 크기를 고민할 필요가 없다 |
| 운영 서버의 작업 큐 | `ThreadPoolExecutor` **직접 생성** | 정원·거절 정책·스레드 이름이 필요하다 |
| 결과 둘을 합친다 | `CompletableFuture.thenCombine` | `Future` 로는 하나씩 기다려야 한다 |
| 가장 먼저 끝난 하나만 쓴다 | `invokeAny` 또는 `anyOf` | 나머지를 자동으로 취소한다 |
| 주기 실행·지연 실행 | `ScheduledExecutorService` | `Timer` 는 예외 하나에 전체가 죽는다 |
| 짧은 배치 스크립트 | `try (ExecutorService es = ...)` (21+) | 닫는 것을 잊을 수 없다 |
| 스트림을 병렬로 돌린다 | `.parallel()` | [`../49-parallel-streams/`](../49-parallel-streams/) 가 정본. **블로킹 I/O 는 넣지 않는다** |

**가장 자주 틀리는 판단** — "느리니까 풀을 키운다".\
블로킹 I/O 라면 풀을 키우는 대신 **가상 스레드**로 가고, CPU 바운드라면 **풀을 키워도 안 빨라진다.**

## 핵심 문장

- **`submit` 의 예외는 `Future` 안에 갇힌다.** 받지 않으면 영영 모른다.
- **`shutdown()` 은 접수만 막는다.** 끝난 것은 `awaitTermination` 이 알려 준다.
- **안 닫으면 JVM 이 안 끝난다.** 풀 스레드는 데몬이 아니다.
- **`newFixedThreadPool` 의 큐는 무한이다.** 지표가 초록인 채로 메모리가 찬다.
- **`maximumPoolSize` 는 큐가 꽉 차야 쓰인다.**
- **`ExecutorService` 는 19부터 `AutoCloseable` 이다.** 17 에서는 컴파일 에러.

## 관련 자료

- [`../25-exceptions/`](../25-exceptions/) — 예외 연쇄와 삼키기.\
  그쪽은 **예외 문법 자체**까지, 여기는 **그 예외가 스레드 경계를 넘을 때 어디로 가나**부터.
- [`../31-functional-interfaces/`](../31-functional-interfaces/) — `Runnable`·`Callable`·`Supplier` 의 시그니처.\
  그쪽은 **어느 인터페이스를 고르나**까지, 여기는 **`submit` 이 둘 중 무엇으로 추론하나**부터.
- [`../26-try-with-resources/`](../26-try-with-resources/) — `close()` 가 불리는 시점과 억제 예외.\
  ★ **`ExecutorService` 가 21에서 `AutoCloseable` 이 된 덕에 그 규칙이 여기에도 적용된다.**
- [`../49-parallel-streams/`](../49-parallel-streams/) — **공용 ForkJoinPool 경합의 정본.**\
  `CompletableFuture` 의 기본 executor 가 그 풀이다. **여기서 다시 재지 않고 결론만 받는다.**
- [`../56-virtual-threads/`](../56-virtual-threads/) — 같은 `ExecutorService` 인터페이스를 쓰는 다른 실행 모델.\
  **이 주제의 "풀 크기를 얼마로 하나"라는 질문 자체를 없앤다.**
- [`../33-synchronized-and-volatile/`](../33-synchronized-and-volatile/) — 인터럽트 플래그·락.
- [`../55-atomics-and-concurrent-collections/`](../55-atomics-and-concurrent-collections/) — 여러 스레드가 함께 쓰는 자료구조.
- [`../../../../process-thread/`](../../../../process-thread/) — OS 스레드와 스케줄링. **그쪽이 정본이다.**

## 용어 풀이

- **`ExecutorService`** — 작업을 받아 스레드에서 실행하는 창구. `@since 1.5`.
- **`Future<V>`** — "나중에 값이 될 것"을 가리키는 번호표. `get()` 은 블로킹한다.
- **`CompletableFuture<V>`** — 결과가 나오면 다음 단계를 이어 붙일 수 있는 `Future`. `@since 1.8`.
- **작업 큐(work queue)** — 스레드가 다 바쁠 때 작업이 줄 서는 `BlockingQueue`.
- **`corePoolSize` / `maximumPoolSize`** — 평소 유지하는 스레드 수 / 큐가 꽉 찼을 때까지 늘릴 수 있는 상한.
- **거절 정책(`RejectedExecutionHandler`)** — 큐도 스레드도 꽉 찼을 때 무엇을 할지. 넷 중 하나를 고른다.
- **역압(backpressure)** — 처리보다 요청이 많을 때 **제출하는 쪽을 느리게 만드는 것**. `CallerRunsPolicy` 가 그 수단이다.
- **`RejectedExecutionException`** — 마감됐거나 정원이 찼을 때 `submit`/`execute` 가 던지는 것.
- **`ExecutionException`** — `Future.get()` 이 작업의 예외를 감싸 던지는 것. 원인은 `getCause()`.
- **`CompletionException`** — `CompletableFuture.join()` 이 쓰는 감싸개. `get()` 과 타입이 다르다.
- **`UncaughtExceptionHandler`** — 스레드 밖으로 나온 예외를 받는 마지막 손. 없으면 stderr.
- **데몬 스레드** — 이것만 남으면 JVM 이 끝나는 스레드. **풀의 기본 스레드는 데몬이 아니다.**

## 더 들어가면

- **`ScheduledExecutorService`** — `schedule`·`scheduleAtFixedRate`·`scheduleWithFixedDelay`.\
  주기 작업이 예외를 던지면 **그 이후 실행이 조용히 멈춘다** — (7) 에서 실측했다(10회 → 3회).\
  `scheduleAtFixedRate`(시작 시각 기준)와 `scheduleWithFixedDelay`(끝난 시각 기준)의 차이는 **측정하지 않았다.**
- **`CompletionService`** — 여러 작업을 던져 놓고 **끝난 순서대로** 받는다. `invokeAll`(제출 순서)과 다르다.
- **`StructuredTaskScope`** — 부모-자식 관계를 가진 동시 작업 묶음. **21·25 모두 프리뷰**다(`src.zip` 확인).\
  확정 문법만 다루는 이 목록의 방침상 여기서는 이름만 적는다.
- **`ForkJoinPool`** — 분할 정복용 풀. 병렬 스트림의 기본 실행기다. [`../49-parallel-streams/`](../49-parallel-streams/) 가 정본.
- **스레드 풀 크기 산정** — CPU 바운드는 코어 수 근처, I/O 바운드는 `코어 수 × (1 + 대기시간/계산시간)` 이 고전적 공식이다.\
  **이 문서는 그 공식을 측정으로 검증하지 않았다.** 가상 스레드는 이 계산 자체를 없앤다.
