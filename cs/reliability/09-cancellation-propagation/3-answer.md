# reliability/09-cancellation-propagation — 정답

## 정답

### 1. 타임아웃 ≠ 멈춤, 그리고 goodput 0

- 타임아웃은 기다리던 쪽이 기다리기를 멈춘 것이다. 작업을 멈추려면 신호가 작업까지 가고 작업이 확인해야 한다.
- 과부하 과정
  1. 처리가 느려져 클라이언트가 타임아웃으로 떠난다.
  2. 서버는 떠난 요청을 끝까지 처리하느라 새 요청이 더 늦어진다. 새 요청도 떠난다.
  3. 결국 서버는 100% 바쁜데 제때 끝나 쓰이는 응답(goodput)은 0에 가깝다.

### 2. `CompletableFuture`

(실험, JDK 21.0.12)

- `orTimeout`: 500ms에 `TimeoutException`을 받았지만 작업은 1.8초 뒤 20단계(전부)를 했다. 포기 뒤 15단계.
- `cancel(true)`: `true`를 돌려주고 `isCancelled=true`인데도 똑같이 20단계를 했다.
- 이유: JDK 문서상 `CompletableFuture.cancel`의 `mayInterruptIfRunning`은 효과가 없다. 인터럽트로 처리를 제어하지 않기 때문이다. 미래 객체만 완료(취소) 상태가 된다.

### 3. Executor `Future.cancel(true)`

(실험)

- (a) sleep: 0단계 — sleep이 `InterruptedException`을 던져 바로 멈췄다.
- (b) 인터럽트 삼킴: 16단계(재실행 15~16) — 예외를 잡을 때 플래그가 지워졌고 아무도 다시 세우지 않았다.
- (c) 확인 없는 CPU 루프: 16단계(재실행 15~16) — 인터럽트는 플래그만 세운다. 보지 않으면 의미가 없다.
- (d) 단계마다 확인: 1단계 — 진행 중이던 단계를 끝내고 다음 확인 지점에서 멈췄다. 확인 간격이 멈추는 데 걸리는 최대 시간이다.

### 4. Go 서버와 `r.Context()`

(실험, Go 1.23.12)

- `time.Sleep`만: 2007ms까지 20단계를 다 했다. 끝날 때 `ctx.Err()=context canceled` — 서버는 끊긴 것을 알았지만 핸들러가 보지 않았다.
- `select`로 `Done` 확인: 501ms에 `context canceled`로 멈췄다. 4단계.
- 덤: 300ms 부모 아래 5초 자식의 데드라인은 부모와 같았다(`WithDeadline` 문서).

### 5. Resilience4j TimeLimiter

- `cancelRunningFuture` 기본값은 `true`(2.4.0 `TimeLimiterConfig`, timeout 기본 1초).
- `Future` 경로: 타임아웃이면 `future.cancel(true)`를 부른다.
- `CompletionStage` 경로: 결과 future를 `TimeoutException`으로 완료시킬 뿐 원래 작업을 취소하지 않는다.
- 스레드가 새는 이유 두 단계
  1. TimeLimiter가 원래 작업에 취소를 보내지 않는다.
  2. 보냈더라도 `CompletableFuture.cancel`은 인터럽트하지 않는다.
  그래서 블로킹 하류 호출 중인 풀 스레드가 타임아웃 뒤에도 그 호출이 끝날 때까지 붙잡혀 있다.

### 6. 구조적 동시성

```text
 scope ─┬─ fork: 2초 작업    ← 형제 실패 → 스코프 종료 → 인터럽트 → 멈춤
        └─ fork: 0.5초 뒤 예외
 scope.join() → 기다리기 끝(예외는 안 던진다 — throwIfFailed()·exception()으로 꺼낸다)
 스코프를 닫을 때 남은 하위 작업 정리
```

- 실험(JDK 21 preview `ShutdownOnFailure`, `scope.exception()`으로 실패 메시지를 꺼냈다): 형제 실패 뒤 2초 작업은 5단계(재실행 4단계)에서 멈췄다(포기 뒤 0단계). `joinUntil(+500ms)`도 같았다.
- JDK 21(JEP 453)은 생성자(`new StructuredTaskScope.ShutdownOnFailure()`)로 만든다. JDK 25(JEP 505)는 정적 팩토리 `StructuredTaskScope.open()`과 `Joiner`로 정책을 고르게 바뀌었다. 둘 다 preview다(JDK 26 JEP 525도 preview).

### 7. 소켓 읽기와 인터럽트

- JEP 444에 따르면 `java.net.Socket` 블로킹 I/O를 **가상 스레드**에서 부르면 인터럽트 가능하게 명세가 바뀌었다. 인터럽트하면 스레드가 깨어나고 소켓이 닫힌다.
- 같은 문서가 이것을 "가상 스레드에서"로 한정하므로, 플랫폼 스레드에서 생성자로 만든 소켓의 블로킹 읽기는 인터럽트로 깨어나지 않는다. 그 경우 소켓 타임아웃이 필요하다.

### 8. 외부 PG 호출의 취소 설계

- 커밋 지점 앞(보내기 전)
  - 남은 예산이 PG의 p99.x보다 작으면 보내지 않고 실패·대기로 돌린다.
  - 그 앞의 단계(검증·재고 예약)는 취소 = 중단·롤백이다.
- 커밋 지점 뒤(보낸 뒤)
  - 취소 신호가 와도 그 호출은 자기 타임아웃까지 기다려 결과를 확정하려 한다.
  - 확정 못 하면 "모름(UNKNOWN)"으로 기록한다. 같은 멱등 키로 상태를 조회·재시도한다.
  - 그래도 모르면 사후 대사로 넘긴다. 실패로 단정해 사용자에게 재결제를 유도하면 이중 결제가 된다.

### 9. 종료 기한을 넘기는 배치

- `catch (InterruptedException e) {}`처럼 인터럽트를 삼키는 블록, 로그만 찍고 계속하는 블록.
- 긴 CPU 루프에 `isInterrupted()` 확인 지점이 없는 곳.
- 플랫폼 스레드에서 타임아웃 없는 소켓·JDBC 호출(인터럽트가 안 닿는다).
- `CompletableFuture.cancel`이나 `orTimeout`에 기대는 취소 코드.
- 대처: 플래그를 되살리거나 위로 던지고, 단계마다 확인하고, I/O마다 타임아웃을 건다.
