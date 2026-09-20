# java/syntax/54 — `java.util.concurrent`: `ExecutorService`·`Future`·`CompletableFuture` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러·스택트레이스·컴파일 에러는 **Temurin JDK 21.0.5 에서 실제로 돌려 얻은 것**이다.\
> ⚠️ **측정 조건** — JMH 가 아니다. 벽시계(`System.nanoTime`) 이고 시간은 `sleep` 이 지배한다. 머신 **24코어**(Linux x86-64).\
> 스레드 이름·완료 순서는 **실행마다 다르다.** 순서가 문제가 되는 자리는 **30회 반복**해 분포로 확인했다.\
> 「JVM 이 안 끝난다」류는 `timeout 6` 으로 감싸 **종료 코드 124**로 판정했다.\
> `AutoCloseable` 여부는 **17.0.13 · 21.0.5 · 25.0.1** 과 `--release 17`/`19` 로 각각 컴파일해 확인했다.
> javadoc 인용은 `lib/src.zip` 의 `java.base/java/util/concurrent/*.java` 원문이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `shutdown` 과 `shutdownNow` 는 각각 무엇을 하나

**출력** (`Ex.java` — 54-a, JDK 21.0.5)

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

**왜 그런가**

- `shutdown()` 직후는 **`isShutdown=true`, `isTerminated=false`** 다.\
  **접수만 막았을 뿐 아직 돌고 있다.** 끝난 것은 `awaitTermination` 이 알려 준다.
- **`left.size()` 는 4** 다. 1건만 실행 중이었고 나머지 4건이 큐에 있었다.
- 돌려받은 것의 타입은 **`java.util.concurrent.FutureTask`** 다 — **내가 넣은 람다가 아니다.**\
  `submit` 이 람다를 `FutureTask` 로 감싸기 때문이다. 그래서 돌려받아도 **바로 다시 실행할 수는 있어도 원본 람다를 꺼낼 수는 없다.**
- **`shutdownNow()` 가 하는 일은 "인터럽트를 보내는 것"**이다. 실행 중 작업의 `isInterrupted` 가 `true` 로 찍혔다.
- 인터럽트를 확인하지 않는 루프는 **`awaitTermination(500ms)` 가 `false`** 이고 **1,900 ms 를 더 돌았다.**\
  ★ **`shutdownNow` 는 "멈춘다"가 아니라 "멈춰 달라고 부탁한다"** 이다.

```text
shutdown()                                 shutdownNow()

  큐에 있는 것: 다 실행                      큐에 있는 것: List<Runnable> 로 반환
  새 접수: 거절                             새 접수: 거절
  진행 중: 끝까지                           진행 중: interrupt 를 보낸다
        |                                          |
        v                                          v
  awaitTermination 이 true 가 될 때까지      작업이 인터럽트를 안 보면
  기다려야 끝난 것이다                        그대로 계속 돈다
```

### 2. 닫는 것을 잊으면

**출력** (`Ex.java` — 54-b, 각각 `timeout 6` 으로 감쌌다, JDK 21.0.5)

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

**왜 그런가**

- **종료되지 않는다.** 6초 뒤 `timeout` 이 죽여서 **종료 코드 124** 가 나왔다.
- 이유는 **풀 스레드가 데몬이 아니기 때문**이다. 같은 프로그램에서 확인했다.

```text
--- 6. 풀 스레드는 데몬이 아니다
  isDaemon = false
```

  **비데몬 스레드가 하나라도 살아 있으면 JVM 은 끝나지 않는다.**
- `ThreadFactory` 로 데몬 스레드를 만들면 **50 ms 에 정상 종료**된다.\
  대가는 — **JVM 이 끝날 때 돌던 작업이 중간에 잘린다.** 로그·커밋이 날아갈 수 있다.
- **`close()`(21+) 는 `shutdown()` + 무기한 `awaitTermination`** 이다.\
  짧은 작업은 **9 ms**, 1.5초짜리 작업이 있으면 **1,509 ms** 를 기다렸다.\
  즉 `try`-with-resources 로 감쌌다고 즉시 나오지 않는다([`../26-try-with-resources/`](../26-try-with-resources/)).

### 3. 이 코드는 어느 JDK 에서 컴파일되나

**출력** (`Ex.java` — 54-c, 같은 소스를 다섯 가지로 컴파일)

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

**왜 그런가**

- **JDK 17 에서는 컴파일 에러다.**\
  `incompatible types: try-with-resources not applicable to variable type` /\
  `(ExecutorService cannot be converted to AutoCloseable)`
- **`--release 19` 는 통과하고 `--release 17` 은 실패한다.** 경계가 **19** 다.
- `src.zip` 에서 선언을 직접 읽어 확인했다.

```text
17.0.13 : public interface ExecutorService extends Executor {
21.0.5  : public interface ExecutorService extends Executor, AutoCloseable {
          407:     * @since 19
          410:    default void close() {
25.0.1  : public interface ExecutorService extends Executor, AutoCloseable {
```

- **17 을 지원해야 하면** `try`-with-resources 대신 이렇게 쓴다.

```java
ExecutorService es = Executors.newFixedThreadPool(4);
try {
    ...
} finally {
    es.shutdown();
    if (!es.awaitTermination(30, TimeUnit.SECONDS)) es.shutdownNow();
}
```

### 4. ★ 작업이 던진 예외는 어디로 가나

**출력** (`Ex.java` — 54-d, JDK 21.0.5)

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

**왜 그런가**

- **(A) 300 ms 동안 화면에 한 줄도 안 찍혔다.** `f.isDone()` 은 `true` 인데 아무 소리가 없다.
- **`f.get()` 은 `ExecutionException` 을 던진다.**\
  `getMessage()` 는 **원인 예외의 `toString`**(`java.lang.IllegalStateException: 터졌다`) 이고,\
  진짜 원인 객체는 `getCause()` 에 있다.
- **(B) 는 `UncaughtExceptionHandler` 로 간다.** 핸들러가 없으면\
  `Exception in thread "pool-1-thread-1" ...` 로 **stderr 에 찍힌다.**
- **(C) 는 아무 데도 안 간다.** 가장 조용한 실패다.
- **규칙 한 줄** — **`submit` 을 쓰면 `Future` 를 반드시 받는다.**\
  결과가 필요 없으면 `execute` 를 쓰거나, 받은 `Future` 를 `state()`/`get()` 으로 확인한다.

```text
submit(task)                               execute(task)

  예외 -> FutureTask 안에 저장               예외 -> 스레드 밖으로
       |                                          |
       v                                          v
  get() 을 부를 때까지 아무도 모른다           UncaughtExceptionHandler
  Future 를 버리면 영영 모른다                 없으면 stderr
```

**스택이 두 겹인 것**

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

- **`e` 만 로그에 찍으면 `get()` 을 부른 자리만 나온다.** `e.getCause()` 를 찍어야 범인이 보인다.

### 5. `Future` 의 상태를 어떻게 읽나

**출력** (`Ex.java` — 54-d, JDK 21.0.5)

```text
--- 6. 취소와 타임아웃
  get(200ms) : java.util.concurrent.TimeoutException (메시지 null)
  cancel(true) = true
  isCancelled  = true  isDone = true  state = CANCELLED
  취소 뒤 get() : java.util.concurrent.CancellationException
```

**왜 그런가**

- **(A) `TimeoutException`** 이고 **메시지는 `null`** 이다.\
  **작업은 취소되지 않는다** — 계속 돈다. `get(timeout)` 은 **기다리는 쪽만** 포기하는 것이다.
- **(B) `isCancelled()=true`, `isDone()=true`, `state()=CANCELLED`.**
- **(C) `CancellationException`** 이다 — `ExecutionException` 이 아니다.
- **`isDone()` 은 "성공"이 아니다.** javadoc 의 표현대로 *완료*(정상·예외·취소 모두)를 뜻한다.
- 구분하려면 **`Future.state()`** 를 쓴다 — **`@since 19`**(`src.zip` 직접 확인).\
  값은 `RUNNING` · `SUCCESS` · `FAILED` · `CANCELLED` 다. 위 출력에서 실패는 `FAILED`, 취소는 `CANCELLED` 로 찍혔다.
- 17 에서는 `state()` 가 없으므로 **`isCancelled()` + `get()` 의 예외 타입**으로 판별한다.

### 6. ★ `newFixedThreadPool` 에 10만 건을 던지면

**출력** (`Ex.java` — 54-e, JDK 21.0.5)

```text
--- 1. newFixedThreadPool 의 큐는 무한이다 (소스: new LinkedBlockingQueue<Runnable>())
  10만 건 제출 뒤 corePoolSize=2  maximumPoolSize=2  poolSize=2
  대기 큐에 쌓인 작업 수 : 99992
  큐 타입                : java.util.concurrent.LinkedBlockingQueue
  큐의 남은 자리          : 2147383656
```

**왜 그런가**

- **예외는 0건**이다. 10만 건을 전부 받아들였다.
- **`poolSize=2`, 큐에 `99,992`건.** 스레드는 안 늘고 줄만 길어진다.
- 큐 타입은 **`LinkedBlockingQueue`**, 남은 자리는 **21억**(`Integer.MAX_VALUE` 근처)이다.\
  `src.zip` 에서 팩토리 본문을 직접 읽어 확인했다.

```text
    public static ExecutorService newFixedThreadPool(int nThreads) {
        return new ThreadPoolExecutor(nThreads, nThreads,
                                      0L, TimeUnit.MILLISECONDS,
                                      new LinkedBlockingQueue<Runnable>());
    }
```

- **운영에서 위험한 이유** — **큐 길이는 어느 지표에도 안 나타난다.**\
  스레드 수 2(정상), CPU 낮음(정상), 에러율 0%(정상), 응답 지연만 조용히 늘다가 **OOM 으로 죽는다.**

```text
무한 큐 (지표는 전부 초록)                  정원이 있는 큐 (밀어내기)
+---------------------------+              +---------------------------+
| 대기 99,992건             |              | 대기 3건 (상한)           |
| 스레드 2 · 예외 0 · CPU 낮음|              | 20건 중 15건 즉시 거절    |
+---------------------------+              +---------------------------+
  -> 어느 순간 OOM 으로 죽는다                -> 느려지는 게 즉시 보인다
```

- 정원을 주면 즉시 소리가 난다.

```text
--- 2. 정원이 있는 큐는 거절한다
  20건 중 받아들임 5 / 거절 15  (스레드 2 + 큐 3)
  거절 메시지: Task java.util.concurrent.FutureTask@30f39991[Not completed, task = java.util.concurrent.Executors$RunnableAdapter@2a84aee7[Wrapped task = Ex$$Lambda/0x0000737cb4000c08@a09ee92]] rejected from java.util.concurrent.ThreadPoolExecutor@279f2327[Running, pool size = 2, active threads = 2, queued tasks = 3, completed tasks = 0]
```

- 거절 메시지에 **풀의 현재 상태가 통째로** 들어 있다 — 진단에 그대로 쓸 수 있다.

### 7. `maximumPoolSize` 는 언제 쓰이나

**출력** (`Ex.java` — 54-e, JDK 21.0.5)

```text
--- 3. maximumPoolSize 는 큐가 꽉 차야 쓰인다
  무한 큐        core=2 max=8 로 12건 제출 → 실제 최대 스레드 2개
  정원 2인 큐     core=2 max=8 로 12건 제출 → 실제 최대 스레드 8개
```

**왜 그런가**

- **무한 큐면 최대 2개**, **정원 2인 큐면 8개**까지 늘었다. 설정은 똑같다.
- `ThreadPoolExecutor` 가 스레드를 늘리는 조건은 이 순서다.

```text
작업이 들어온다
        |
        v
  스레드 < corePoolSize ?  --예--> 새 스레드를 만든다
        |아니오
        v
  큐에 넣을 수 있나 ?      --예--> 큐에 넣는다  <- 무한 큐면 항상 여기서 끝난다
        |아니오
        v
  스레드 < maximumPoolSize ? --예--> 새 스레드를 만든다
        |아니오
        v
  거절 정책을 부른다
```

- ★ **큐가 무한이면 "큐에 넣을 수 있나"가 항상 참**이라 세 번째 칸에 도달하지 않는다.
- **"스레드가 안 늘어난다"를 만나면 먼저 큐의 정원을 본다.**

### 8. 거절 정책 넷은 각각 무엇을 하나

**출력** (`Ex.java` — 54-e, 스레드 1 + 큐 1 에 5건, JDK 21.0.5)

```text
--- 4. 거절 정책 네 가지가 무엇을 하나 (스레드 1 + 큐 1 에 5건)
  AbortPolicy              실행 2건 / 예외 3건 / 그중 호출 스레드가 직접 실행 0건
  CallerRunsPolicy         실행 5건 / 예외 0건 / 그중 호출 스레드가 직접 실행 2건
  DiscardPolicy            실행 2건 / 예외 0건 / 그중 호출 스레드가 직접 실행 0건
  DiscardOldestPolicy      실행 2건 / 예외 0건 / 그중 호출 스레드가 직접 실행 0건
```

**왜 그런가**

| 정책 | 실행 | 예외 | 하는 일 |
|---|---|---|---|
| `AbortPolicy` | 2건 | **3건** | `RejectedExecutionException` 을 던진다. **기본값** |
| `CallerRunsPolicy` | **5건** | 0건 | 제출한 스레드가 **직접 실행**한다(실측 2건) |
| `DiscardPolicy` | 2건 | 0건 | **조용히 버린다** |
| `DiscardOldestPolicy` | 2건 | 0건 | **큐에서 가장 오래된 것을 버리고** 새것을 넣는다 |

- **`CallerRunsPolicy` 에서 `main` 이 직접 실행한 건수는 2건**이다.\
  제출자가 그동안 못 제출하므로 **자연스러운 역압**이 된다.
- **가장 위험한 것은 `DiscardPolicy`·`DiscardOldestPolicy`** 다.\
  실행 2건, 예외 0건 — **3건이 흔적 없이 사라졌다.** 로그도 지표도 없다.
- **기본값은 `AbortPolicy`** 다. 최소한 소리는 난다.

### 9. `Future` 로 못 하는 것은 무엇인가

**출력** (`Ex.java` — 54-f, 리플렉션으로 뽑은 목록, JDK 21.0.5)

```text
--- 1. Future 셋을 합치려면 하나씩 기다리는 수밖에 없다
  합 6, 307 ms (세 작업이 병렬로 돌아 300ms 근처)
  Future 가 가진 메서드 : [cancel, exceptionNow, get, get, isCancelled, isDone, resultNow, state]
```

**왜 그런가**

- 메서드는 **`cancel` · `exceptionNow` · `get` · `get(timeout)` · `isCancelled` · `isDone` · `resultNow` · `state`** 여덟 개다\
  (`exceptionNow`·`resultNow`·`state` 는 **`@since 19`**).
- **"끝나면 이어서 ~해라"를 표현할 자리가 없다.** 콜백을 등록하는 메서드가 없다.
- 셋을 합치려면 **`get()` 으로 하나씩 기다린다.** 그동안 **내 스레드는 블로킹되어 아무 일도 못 한다.**\
  실측 307 ms — 세 작업이 병렬로 돌아 **가장 긴 것(300 ms)만큼** 걸렸으니 병렬성은 있다.\
  잃는 것은 **내 스레드**다.
- **`CompletableFuture` 가 메우는 것** — 이어 붙이기(`thenApply`·`thenCompose`·`thenCombine`),\
  여러 개 합치기(`allOf`·`anyOf`), 예외 복구(`exceptionally`·`handle`), 직접 완료(`complete`).

### 10. `thenApply` 는 어느 스레드가 도나

**출력** (`Ex.java` — 54-f, JDK 21.0.5)

```text
--- 3. 어느 스레드가 다음 단계를 도나
      supplyAsync(executor 지정) : pool-1-thread-1
      thenApply                  : main
      thenApplyAsync(기본)        : ForkJoinPool.commonPool-worker-1
      supplyAsync(기본)           : ForkJoinPool.commonPool-worker-1
```

**출력** (`Ex.java` — 54-g, 각 30회 반복, 같은 명령을 3회)

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

**왜 그런가**

- **`thenApply` 에는 전용 스레드가 없다.**\
  이미 끝나 있으면 **붙이는 스레드**(30/30회 `main`), 아직 돌고 있으면 **완료시킨 스레드**(30/30회 `pool-`).
- **흔들리지 않았다** — 30회 × 3회 실행에서 전부 같았다.\
  ★ 그래도 **보장은 아니다.** javadoc 이 이렇게 적는다.

  > Actions supplied for dependent completions of *non-async* methods may be performed by the thread that
  > completes the current CompletableFuture, or by any other caller of a completion method.

- **`thenApplyAsync` 와 executor 없는 `supplyAsync` 는 공용 ForkJoinPool** 로 간다.\
  javadoc 도 "All *async* methods without an explicit Executor argument are performed using the `ForkJoinPool#commonPool()`" 라고 적는다.
- ★ **공용 풀을 남과 나눠 쓰는 위험은 [`../49-parallel-streams/`](../49-parallel-streams/) 가 이미 실측했다** —\
  같은 코드가 풀 상태에 따라 **2.6배** 느려졌다. **여기서 다시 재지 않고 결론만 받는다.**\
  서버 코드에서는 **executor 를 명시한다.**

### 11. `get()` 과 `join()` 은 무엇이 다른가

**출력** (`Ex.java` — 54-f, JDK 21.0.5)

```text
--- 4. 예외가 감싸이는 방식이 다르다
  get()  : java.util.concurrent.ExecutionException → cause java.lang.IllegalStateException: CF 에서 터짐
  join() : java.util.concurrent.CompletionException → cause java.lang.IllegalStateException: CF 에서 터짐
  exceptionally 로 복구 : -1
  handle 로 둘 다 받기  : -2
```

**왜 그런가**

- **`get()` 은 `ExecutionException`, `join()` 은 `CompletionException`** 이다.
- **두 예외는 상속 관계가 아니다.** `ExecutionException extends Exception`(검사 예외),\
  **`CompletionException extends RuntimeException`**(비검사).
- 그래서 **`join()` 이 람다 안에서 쓰기 편하다** — 검사 예외를 선언할 필요가 없다.\
  `Stream.map(f -> f.join())` 은 되고 `f.get()` 은 안 된다.
- 원인은 둘 다 **`getCause()`** 로 꺼낸다.
- 복구는 `exceptionally(t -> 기본값)` 나 `handle((v, t) -> ...)` 로 한다 — 실측에서 `-1`, `-2` 가 나왔다.

### 12. 여러 작업을 기다리는 네 가지

**출력** (`Ex.java` — 54-f, A:300ms · B:100ms · C:200ms, JDK 21.0.5)

```text
--- 5. allOf / anyOf
  allOf().join() 반환값 : null (Void 다 — 값은 각자에서 꺼낸다)
  값은 따로: 1, 2
  anyOf().join()       : 빠른 쪽
--- 6. invokeAll 과 invokeAny
  invokeAll : 전부 isDone=true, 302 ms, 결과 순서 [A, B, C]
  invokeAny : B, 100 ms
```

**왜 그런가**

- **`invokeAll` 은 302 ms** — 가장 긴 작업(300 ms)만큼 걸린다. **전부 끝날 때까지 블로킹**한다.\
  결과 순서는 **`[A, B, C]`**, 즉 **제출 순서**다. **이것은 보장된다** — javadoc 원문:

  > a list of Futures representing the tasks, in the same sequential order as produced by the iterator for the
  > given task list, each of which has completed

- **`invokeAny` 는 `B` 를 100 ms 에** 반환한다. 가장 먼저 끝난 하나를 주고 **나머지는 취소**한다.
- **`allOf(...).join()` 은 `null`** 이다 — 반환 타입이 `CompletableFuture<Void>` 다.\
  **값은 각 `CompletableFuture` 에서 따로 꺼낸다**(실측 `1, 2`).
- **`anyOf` 는 가장 먼저 끝난 것의 값**을 준다(`빠른 쪽`). 반환 타입은 `CompletableFuture<Object>` 다.

### 13. `CompletableFuture.cancel(true)` 는 작업을 멈추나

**출력** (`Ex.java` — 54-f, JDK 21.0.5)

```text
--- 7. CompletableFuture.cancel 은 실행 중인 작업을 안 멈춘다
  cancel(true) = true  isCancelled=true
      (취소했는데도 작업은 끝까지 돌았다)
```

**왜 그런가**

- **`cancel(true)` 는 `true` 를 반환하고 `isCancelled()` 도 `true`** 다.
- **그런데 작업은 끝까지 돌았다.** 800 ms 뒤 람다 안의 출력이 찍혔다.
- **`FutureTask.cancel(true)` 와 다른 점** — `FutureTask` 는 실행 스레드에 **인터럽트를 보낸다**(1번 답의 `interrupted=true`).\
  `CompletableFuture` 는 **인터럽트를 보내지 않는다.** 이미 시작된 계산을 건드리지 않고 **결과만 취소 상태로 만든다.**
- **정말 멈추려면** 작업 쪽이 **자기 취소 플래그나 인터럽트를 주기적으로 확인**해야 한다.\
  `CompletableFuture` 에는 그 신호를 보내는 표준 수단이 없으므로,\
  중단이 필요하면 **`ExecutorService.submit` 의 `Future`** 를 함께 들고 있어야 한다.

### 14. 이 코드를 어떻게 고칠 것인가

**(A) `es.submit(() -> repository.save(entity));` — 반환값을 안 받는다**

- **`execute` 로 바꾸거나 `Future` 를 받아 확인한다.**
- 근거: 4번 — `submit` 의 예외는 `Future` 안에 갇혀 **300 ms 동안 아무것도 안 찍혔다.**\
  저장이 실패해도 아무도 모른다.

**(B) `Executors.newFixedThreadPool(200)` — 요청마다 외부 API 를 호출한다**

- **가상 스레드로 바꾼다**(`Executors.newVirtualThreadPerTaskExecutor()`, [`../56-virtual-threads/`](../56-virtual-threads/)).
- 근거: 블로킹 I/O 는 스레드를 놀리는 일이다. 200 이라는 숫자에 근거가 없고, 늘리면 메모리가 든다.\
  17 을 써야 한다면 **`ThreadPoolExecutor` 로 바꾸고 큐에 정원**을 준다.

**(C) `es.shutdown(); System.out.println("정리 끝");`**

- **`awaitTermination` 을 넣는다.**
- 근거: 1번 — `shutdown()` 직후 `isTerminated=false` 다. **아직 돌고 있다.**

**(D) `catch (ExecutionException e) { log.error("실패", e); }`**

- **`e.getCause()` 를 찍는다** — `log.error("실패", e.getCause())`.
- 근거: 4번 — `e` 의 스택은 `get()` 을 부른 자리만 가리킨다.

**(E) `CompletableFuture.supplyAsync(() -> httpClient.send(req));` — 서버 코드**

- **executor 를 명시한다** — `supplyAsync(..., myExecutor)`.
- 근거: 10번 — executor 를 안 주면 **공용 ForkJoinPool** 이다.\
  공용 풀 경합의 실측은 [`../49-parallel-streams/`](../49-parallel-streams/) 가 정본이다.

**(F) `new ThreadPoolExecutor(8, 64, 60, SECONDS, new LinkedBlockingQueue<>());`**

- **큐에 정원을 준다** — `new LinkedBlockingQueue<>(1000)` 또는 `ArrayBlockingQueue<>(1000)`.
- 근거: 7번 — 무한 큐면 **`max=64` 가 영원히 안 쓰인다.** 실측에서 `max=8` 인데 스레드가 2개에서 멈췄다.

### 15. 주기 작업이 예외를 던지면

**출력** (`Ex.java` — 54-h, 100 ms 주기로 1초 동안, JDK 21.0.5)

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

**왜 그런가**

- **1초에 3회**다. 100 ms 주기면 **약 10회**여야 한다. **3회차 예외 이후 영영 안 돈다.**
- **화면에 예외가 안 찍힌다.** `submit` 과 같은 이유다 — 예외가 `Future` 안에 갇힌다(4번).
- `isDone()=true`, **`isCancelled()=false`**, `state()=FAILED` 다.\
  `get()` 을 해야 `ExecutionException` → `getCause()` 로 원인이 나온다.
- **`try`/`catch` 로 감싸면 11회**로 돌아온다.
- **규칙 한 줄** — ★ **주기 작업의 본문은 예외를 절대 밖으로 내보내지 않는다.**\
  헬스체크·정리 작업이 조용히 죽어 있는 사고가 여기서 난다.

### 16. 풀 안에서 같은 풀을 기다리면

**출력** (`Ex.java` — 54-h, JDK 21.0.5)

```text
--- 3. 같은 풀 안에서 같은 풀의 Future 를 기다리면 (단일 스레드 풀)
  java.util.concurrent.ExecutionException → cause java.util.concurrent.TimeoutException
--- 4. 스레드 2개짜리 풀에서 2건이 서로를 기다리면
  2건이 서로를 기다림 : a, b  (스레드가 2개라 통과한다)
  스레드 2개를 막아 놓고 3번째 작업 : c3  (1500 ms 기다렸다)
```

**왜 그런가**

- **`outer.get()` 은 `ExecutionException` 을 던지고 원인이 `TimeoutException`** 이다.\
  바깥 작업이 **유일한 스레드**를 차지했으므로 안쪽 작업은 큐에서 나오지 못한다.
- **타임아웃이 없었다면 예외도 없이 영원히 멈춰 있었을 것**이다.\
  교착과 같은 모양이다 — 다만 `ThreadMXBean.findDeadlockedThreads()` 는 **모니터 교착만** 찾으므로\
  이건 그 도구로도 안 잡힌다([`../33-synchronized-and-volatile/`](../33-synchronized-and-volatile/)).
- **스레드 2개면 2건이 서로를 기다려도 통과한다**(`a, b`).\
  ★ **그래서 더 위험하다** — 개발·테스트의 낮은 동시성에서는 멀쩡하다가\
  운영에서 동시 요청이 풀 크기를 넘는 순간 걸린다.
- 스레드 2개를 막아 놓고 던진 3번째 작업은 **1,500 ms** 를 기다렸다.\
  **동시성의 상한은 언제나 풀 크기**다.
- **고치는 법** — 중첩 제출에는 **다른 풀**을 쓰거나, **가상 스레드**([`../56-virtual-threads/`](../56-virtual-threads/))로 간다.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 반복 | 돌린 JDK |
|---|---|---|---|
| `Ex.java` (54-a) | `shutdown`/`shutdownNow`/`awaitTermination`, `RejectedExecutionException` 메시지, 돌려받은 작업의 타입, 인터럽트 무시 루프, 풀 3종의 스레드 수, `isDaemon` | 1회 | 21 |
| `Ex.java` (54-b) | 안 닫았을 때 JVM 종료 여부(종료 코드), `shutdown`/`close`/`close`(긴 작업)/데몬 스레드 | 모드당 1회 (`timeout 6`) | 21 |
| `Ex.java` (54-c) | `try`-with-resources + `ExecutorService` 의 컴파일 가부 | 1회 | **17 · 21 · 25 + `--release 17`/`19`** (**17 에서 에러**) |
| `Ex.java` (54-d) | `submit` 대 `execute` 의 예외 경로, `Future` 를 버렸을 때, 기본 핸들러 출력, 두 겹 스택, `TimeoutException`·`CancellationException`·`state()` | 1회 | 21 |
| `Ex.java` (54-e) | 무한 큐에 10만 건, 정원 큐의 거절, `maximumPoolSize` 조건, 거절 정책 4종 | 정책당 1회 | 21 |
| `Ex.java` (54-f) | `Future` 메서드 목록, `thenCombine`, 실행 스레드 4종, `get`/`join` 예외 타입, `allOf`/`anyOf`, `invokeAll`/`invokeAny`, `cancel` | 1회 | 21 |
| `Ex.java` (54-g) | `thenApply` 실행 스레드의 분포 | **30회 × 3회 실행** | 21 |
| `Ex.java` (54-h) | 주기 작업의 예외 뒤 실행 중단(1초 동안 3회 대 11회), 단일 스레드 풀의 중첩 `get()`, 풀 크기가 동시성 상한인 것 | 1회 | 21 |
| `src.zip` 열람 | `ExecutorService` 선언(17 대 21 대 25), `close()`·`state()`·`resultNow()` 의 `@since 19`, `newVirtualThreadPerTaskExecutor` 의 `@since 21`, `newFixedThreadPool`·`newCachedThreadPool` 본문, `invokeAll`·`CompletableFuture` javadoc, `StructuredTaskScope` 의 `@PreviewFeature` | — | 17 · 21 · 25 |

**측정 방법의 한계 (반드시 같이 읽을 것)**

- **JMH 가 아니다.** 시간 수치는 `sleep` 으로 만든 작업 길이가 지배한다 — **API 의 성능 비교가 아니다.**
- **스레드 이름·완료 순서는 실행마다 다르다.** 이 문서의 출력은 한 번의 실행이다.\
  순서가 결론이 되는 자리(`thenApply` 누가 도나)만 **30회 × 3회**로 확인했다.
- **머신 의존**이다 — 24코어. 풀 3종의 스레드 수 실험은 코어 수와 무관하지만 `cached` 의 생성 속도는 다를 수 있다.
- **재현하지 않은 것** — `scheduleAtFixedRate`(시작 시각 기준)와 `scheduleWithFixedDelay`(끝난 시각 기준)의 **주기 차이**.\
  작업이 주기보다 오래 걸릴 때 둘이 어떻게 달라지는지는 **측정하지 않았다.**

**구현 의존 항목** (버전이 오르면 다시 돌려야 하는 것)

- **`ExecutorService` 의 `AutoCloseable` 여부 — 17 과 19+ 가 실제로 달랐다.**
- `Future.state()`·`resultNow()`·`exceptionNow()` — **17 에 없다.**
- `RejectedExecutionException` 메시지 안의 풀 상태 문자열 — 구현 세부.
- 스레드 이름 `pool-N-thread-M` 과 풀 번호의 증가 — 구현 세부.
- `shutdownNow()` 가 돌려주는 객체의 구체 타입(`FutureTask`) — javadoc 은 `Runnable` 만 약속한다.
- `thenApply` 의 실행 스레드 — **javadoc 이 "any other caller" 도 허용한다.** 30회 관측은 보장이 아니다.
- **Java 8 의 동작은 안 돌려 봄** — 이 머신에 8이 없다.
