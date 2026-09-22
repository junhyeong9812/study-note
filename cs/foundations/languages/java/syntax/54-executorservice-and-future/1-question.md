# java/syntax/54 — `java.util.concurrent`: `ExecutorService`·`Future`·`CompletableFuture` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **선행** — [`../25-exceptions/`](../25-exceptions/) · [`../31-functional-interfaces/`](../31-functional-interfaces/) · [`../26-try-with-resources/`](../26-try-with-resources/) 의 질문을 먼저 푼다.
> ⚠️ 스레드 이름과 실행 순서는 **실행마다 다르다.** 순서를 묻는 문항은 "**정해져 있나 아닌가**"를 묻는 것이다.
> 시간 수치를 묻는 문항은 **자릿수**만 맞히면 된다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `shutdown` 과 `shutdownNow` 는 각각 무엇을 하나 (예측)

```java
ExecutorService es = Executors.newFixedThreadPool(1);
for (int i = 0; i < 5; i++) es.submit(() -> { 3초간 sleep; });
Thread.sleep(200);
List<Runnable> left = es.shutdownNow();
```

- `shutdown()` 직후 `isShutdown()` 과 `isTerminated()` 는 각각 무엇인가?
- 위 코드에서 `left.size()` 는 몇인가?
- `left` 에 든 객체의 **런타임 타입**은 무엇인가 — 내가 넣은 람다인가?
- `shutdownNow()` 가 실행 중이던 작업에 실제로 하는 일은 무엇인가?
- `while` 루프가 인터럽트를 확인하지 않으면 `awaitTermination(500ms)` 는 무엇을 반환하는가?

### 2. 닫는 것을 잊으면 (예측)

```java
public static void main(String[] args) {
    ExecutorService es = Executors.newFixedThreadPool(1);
    es.submit(() -> System.out.println("작업"));
    System.out.println("main 끝");
}
```

- 이 프로그램은 종료되는가?
- 안 된다면 그 이유는 무엇인가 — 풀 스레드의 어떤 성질 때문인가?
- `ThreadFactory` 로 데몬 스레드를 만들면 어떻게 달라지는가, 그리고 그 대가는?
- `close()`(21+) 는 `shutdown()` 과 무엇이 다른가 — 1.5초짜리 작업이 돌고 있으면 몇 ms 에 반환하는가?

### 3. 이 코드는 어느 JDK 에서 컴파일되나 (경계)

```java
try (ExecutorService es = Executors.newFixedThreadPool(1)) {
    es.submit(() -> System.out.println("작업"));
}
```

- JDK 17 에서 컴파일되는가? 에러 메시지는?
- `--release 17` 과 `--release 19` 중 어느 쪽이 통과하는가?
- `ExecutorService` 가 `AutoCloseable` 을 상속한 것은 어느 버전부터인가 — 무엇으로 확인했는가?
- 17 을 지원해야 하면 이 코드를 무엇으로 바꾸는가?

### 4. ★ 작업이 던진 예외는 어디로 가나 (예측)

```java
Future<?> f = es.submit(() -> { throw new IllegalStateException("터졌다"); });   // (A)
es.execute(() -> { throw new IllegalStateException("터졌다"); });               // (B)
es.submit(() -> { throw new IllegalStateException("터졌다"); });                // (C) 반환값을 안 받음
```

- (A) 직후 300ms 동안 화면에 무엇이 찍히는가?
- (A)에서 `f.get()` 은 무엇을 던지는가 — 그 예외의 `getMessage()` 와 `getCause()` 는?
- (B)는 어디로 가는가 — 핸들러가 없으면?
- (C)는 어떻게 되는가?
- 그래서 `submit` 을 쓸 때의 규칙 한 줄은?

### 5. `Future` 의 상태를 어떻게 읽나 (예측)

```java
Future<?> f = es.submit(() -> { Thread.sleep(5000); return 1; });
f.get(200, TimeUnit.MILLISECONDS);   // (A)
f.cancel(true);                      // (B)
f.get();                             // (C)
```

- (A)는 무엇을 던지는가 — 메시지는? 그 뒤 작업은 계속 도는가?
- (B) 뒤의 `isCancelled()` / `isDone()` / `state()` 는 각각 무엇인가?
- (C)는 무엇을 던지는가?
- `isDone() == true` 가 "성공"을 뜻하는가?
- 성공·실패·취소를 구분하는 메서드와 그 도입 버전은?

### 6. ★ `newFixedThreadPool` 에 10만 건을 던지면 (예측)

```java
ThreadPoolExecutor p = (ThreadPoolExecutor) Executors.newFixedThreadPool(2);
for (int i = 0; i < 100_000; i++) p.submit(() -> sleep(10));
```

- 예외가 몇 건 나는가?
- `p.getPoolSize()` 와 `p.getQueue().size()` 는 각각 무엇인가?
- 큐의 런타임 타입과 `remainingCapacity()` 는?
- 이 상황이 운영에서 위험한 이유를 "지표"라는 말을 써서 한 줄로 설명하라.

### 7. `maximumPoolSize` 는 언제 쓰이나 (예측)

```java
new ThreadPoolExecutor(2, 8, 1, TimeUnit.SECONDS, q, new CallerRunsPolicy());
// q 가 LinkedBlockingQueue 일 때와 ArrayBlockingQueue(2) 일 때
```

- 12건을 제출했을 때 각각 실제 최대 스레드 수는 몇인가?
- 왜 그런가 — `ThreadPoolExecutor` 가 스레드를 늘리는 조건은 무엇인가?
- 그래서 "스레드가 안 늘어난다"는 문제를 만나면 먼저 무엇을 보는가?

### 8. 거절 정책 넷은 각각 무엇을 하나 (경계)

스레드 1 + 큐 1 짜리 풀에 5건을 던졌다.

- `AbortPolicy` / `CallerRunsPolicy` / `DiscardPolicy` / `DiscardOldestPolicy` 에서 각각 몇 건이 실행되고 몇 건이 예외가 되는가?
- `CallerRunsPolicy` 에서 제출한 스레드가 직접 실행한 건수는?
- 넷 중 **운영에서 가장 위험한 것**은 어느 것이고 왜인가?
- 기본값은 어느 것인가?

### 9. `Future` 로 못 하는 것은 무엇인가 (왜)

- `Future` 인터페이스가 선언한 메서드를 모두 열거하라.
- "끝나면 이어서 ~해라"를 `Future` 로 표현할 수 있는가?
- `Future` 셋의 결과를 합치려면 어떻게 해야 하는가 — 그때 내 스레드는 무엇을 하고 있는가?
- `CompletableFuture` 가 그중 무엇을 메우는가?

### 10. `thenApply` 는 어느 스레드가 도나 (예측)

```java
CompletableFuture.supplyAsync(() -> 1, es).thenApply(x -> { /* 누가? */ return x; });
CompletableFuture.supplyAsync(() -> 1, es).thenApplyAsync(x -> { /* 누가? */ return x; });
CompletableFuture.supplyAsync(() -> 1).thenApply(...);   // executor 없음
```

- 세 경우에 실행 스레드는 각각 무엇인가?
- 같은 `thenApply` 라도 **이미 끝난 `CompletableFuture`** 에 붙일 때와 **아직 도는 것**에 붙일 때가 다른가?
- 30회 반복하면 결과가 흔들리는가?
- executor 를 안 주면 어느 풀을 쓰는가 — 그것이 왜 위험한가(어느 주제가 그것을 실측했나)?

### 11. `get()` 과 `join()` 은 무엇이 다른가 (경계)

- 작업이 예외를 던졌을 때 `get()` 과 `join()` 이 던지는 예외 타입은 각각 무엇인가?
- 두 예외는 상속 관계인가?
- `join()` 이 람다 안에서 쓰기 편한 이유는?
- 원인 예외는 어느 메서드로 꺼내는가?

### 12. 여러 작업을 기다리는 네 가지 (예측)

```java
es.invokeAll(tasks);     // A:300ms, B:100ms, C:200ms
es.invokeAny(tasks);
CompletableFuture.allOf(s1, s2).join();
CompletableFuture.anyOf(fast, slow).join();
```

- `invokeAll` 은 몇 ms 에 반환하고 결과 순서는 무엇인가 — 그 순서는 보장되는가?
- `invokeAny` 는 무엇을 반환하고 몇 ms 걸리는가?
- `allOf(...).join()` 의 반환값은 무엇인가?
- `anyOf` 는 무엇을 반환하는가?

### 13. `CompletableFuture.cancel(true)` 는 작업을 멈추나 (예측)

```java
CompletableFuture<String> slow = CompletableFuture.supplyAsync(() -> { sleep(800); return "x"; }, es);
sleep(100);
slow.cancel(true);
```

- `cancel(true)` 의 반환값과 `isCancelled()` 는?
- 실행 중이던 작업은 멈추는가?
- `FutureTask.cancel(true)` 와 무엇이 다른가?
- 정말 멈추려면 작업 쪽이 무엇을 해야 하는가?

### 14. 이 코드를 어떻게 고칠 것인가 (연결)

각각 무엇을 바꿀지 한 줄로 답하라.

```text
(A) es.submit(() -> repository.save(entity));                         // 반환값을 안 받는다
(B) ExecutorService es = Executors.newFixedThreadPool(200);           // 요청마다 외부 API 를 호출한다
(C) es.shutdown(); System.out.println("정리 끝");
(D) catch (ExecutionException e) { log.error("실패", e); }
(E) CompletableFuture.supplyAsync(() -> httpClient.send(req));        // 서버 코드
(F) new ThreadPoolExecutor(8, 64, 60, SECONDS, new LinkedBlockingQueue<>());
```

### 15. 주기 작업이 예외를 던지면 (예측)

```java
ses.scheduleAtFixedRate(() -> {
    int n = runs.incrementAndGet();
    if (n == 3) throw new IllegalStateException("3회차에서 터진다");
}, 0, 100, TimeUnit.MILLISECONDS);
```

- 1초 동안 몇 회 실행되는가 — 100ms 주기면 몇 회여야 하는가?
- 화면에 예외가 찍히는가?
- 반환된 `ScheduledFuture` 의 `isDone()` / `isCancelled()` / `state()` 는?
- 본문을 `try`/`catch` 로 감싸면 몇 회가 되는가?
- 그래서 주기 작업 본문의 규칙 한 줄은?

### 16. 풀 안에서 같은 풀을 기다리면 (예측)

```java
ExecutorService single = Executors.newSingleThreadExecutor();
Future<String> outer = single.submit(() -> {
    Future<String> inner = single.submit(() -> "안쪽 결과");
    return "바깥 + " + inner.get(2, TimeUnit.SECONDS);
});
```

- `outer.get()` 은 무엇을 반환하거나 던지는가?
- `inner.get()` 에 타임아웃이 없었다면 무엇이 달랐겠는가?
- 스레드 2개짜리 풀에서 2건이 서로를 기다리면 통과하는가 — 그것이 왜 더 위험한가?
- 스레드 2개를 막아 놓고 던진 3번째 작업은 몇 ms 를 기다리는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
