# reliability/09-cancellation-propagation — 타임아웃이 나면 작업을 실제로 멈추는 법 — 정리 (힌트)

## 해결하는 문제

"타임아웃이 났다"는 **기다리던 쪽이 기다리기를 멈췄다**는 뜻일 뿐이다. 기다림을 받던 작업이 멈췄다는 뜻이 아니다.\
멈추지 않은 작업은 결과를 받을 사람이 없는데 CPU·스레드·커넥션·락을 계속 쓴다.

```text
 평소                      과부하
 요청 ──> 처리 ──> 응답      요청이 몰림 → 처리가 느려짐 → 클라이언트가 타임아웃으로 떠남
                            서버는 떠난 요청을 끝까지 처리 → 새 요청은 더 늦어짐 → 또 떠남
                            goodput(제때 끝나 쓰인 응답) → 0, 서버는 100% 바쁨
```

- *취소 전파(cancellation propagation)*: "그만해도 된다"는 신호를 작업과 그 작업이 만든 하위 작업(스레드·RPC·쿼리)까지 전달하는 것.
- *goodput*: 처리량 중 **쓸모 있게** 끝난 것. 클라이언트가 떠난 뒤 끝난 응답은 처리량에는 잡히지만 goodput은 아니다.
- *협조적 취소(cooperative cancellation)*: 밖에서 강제로 죽이지 않고, 실행 중인 코드가 신호를 **스스로 확인**하고 멈추는 방식. 대부분의 런타임이 이 방식이다.

쉬운 예: 단체 주문을 취소했다.
- 매장에 전화로 "취소"라고 말했다(신호). 그런데 주방장이 주문표를 다시 보지 않으면(확인 안 함) 요리는 계속된다.
- 주방장이 이미 배달 기사에게 넘겼다면(하위 작업), 기사에게도 전해야 한다(전파).
- 이미 결제 단말에 카드를 긁었다면 "취소"로는 안 된다. 환불이라는 다른 절차가 필요하다(취소 불가 구간).

똑같은 구조다.\
실무 예: Go의 `context` 취소, Java `Future.cancel(true)`·인터럽트, gRPC 취소, JDBC 쿼리 취소, Node `AbortController`, 외부 결제 호출의 결과가 모호해지는 경우.

"남은 예산을 실어 보내는" 쪽은 [05](../05-timeouts-and-deadline-propagation/2-summary.md)·[08](../08-time-budget-allocation/2-summary.md), 원본 [ops-patterns/deadline-propagation](../../ops-patterns/deadline-propagation/2-summary.md) §2(고아 작업)·§3-2(작업 스레드)·§4(취소가 닿지 않는 곳)에 있다. 이 노트는 **멈추는 쪽**을 언어·라이브러리별로 실험한다.

## 동작·원리

### 1. 취소 트리 — 부모가 취소되면 자식 전부

```text
 요청 ctx (데드라인 T+1s)
   ├─ 하위 RPC ctx ──── 하위 서버 ctx ── DB 쿼리
   ├─ 병렬 작업 1 (스레드)
   └─ 병렬 작업 2 (스레드)
 부모 취소(데드라인·클라이언트 끊김·형제 실패*) ─> 모든 자식에 신호
 * 형제 실패로 부모를 취소하는 것은 정책이다(errgroup.WithContext·ShutdownOnFailure) — Go context가 저절로 하지 않는다
 단, 각 노드가 신호를 "확인"해야 실제로 멈춘다
```

- Go `context`: 자식 컨텍스트는 부모의 `Done` 채널이 닫히면 같이 닫힌다. `WithDeadline`에 부모보다 늦은 시각을 주면 부모와 같게 본다(Go `context` 문서).
- 신호는 트리를 타고 내려간다. 그러나 각 노드는 그 신호를 **봐야** 멈춘다. 보지 않는 노드에서 트리가 끊긴다.

### 2. 런타임별 "신호"와 "멈추는 지점"

| 런타임 | 신호 | 멈추는 지점 | 함정 |
|---|---|---|---|
| Go | `ctx.Done()` 채널 닫힘 | `select`로 `Done`을 보는 곳, ctx를 받는 라이브러리 호출 | ctx를 안 넘기거나 안 보면 끝까지 돈다 |
| Java 스레드 | `Thread.interrupt()` → 인터럽트 플래그 | `sleep`·`wait`·`join`·`BlockingQueue.take`가 `InterruptedException`, 루프에서 `isInterrupted()` 확인 | 예외를 삼키면 신호가 사라진다. 플랫폼 스레드에서 생성자로 만든 `java.net.Socket` 블로킹 I/O는 인터럽트로 깨어나지 않는다(JEP 444는 가상 스레드에서만 인터럽트 가능하게 바꿨다) |
| Java `Future`(Executor) | `cancel(true)` = 실행 중 스레드 인터럽트 | 위와 같다 | 작업이 인터럽트를 확인해야 한다 |
| Java `CompletableFuture` | `cancel(true)`·`orTimeout` | 없음 — **미래 객체만** 완료시킨다 | JDK 문서: `mayInterruptIfRunning`은 "효과가 없다, 인터럽트로 처리를 제어하지 않기 때문" |
| Java 구조적 동시성 | 스코프 종료(shutdown) → 남은 하위 작업 인터럽트 | 하위 작업의 인터럽트 확인 지점 | JDK 21은 preview(`ShutdownOnFailure`), JDK 25·26도 preview이고 API가 바뀌었다(`StructuredTaskScope.open()`·`Joiner`) |
| gRPC | 클라이언트 취소·데드라인 → 서버 쪽 호출 `CANCELLED` | 서버 핸들러가 주기적으로 취소 확인 | gRPC 취소 가이드: 라이브러리는 핸들러를 인터럽트할 수단이 대체로 없다 |
| JDBC | `Statement.cancel()`·`setQueryTimeout` → DBMS와 드라이버가 지원하면 드라이버가 서버에 취소 요청(JDBC 계약은 "지원하면"까지만) | DB 서버의 쿼리 실행 | 소켓 타임아웃은 소켓만 닫는다. PostgreSQL 기본 설정에서는 서버 쿼리가 계속 돌 수 있다(14+ `client_connection_check_interval`을 켜면 더 일찍 알아챈다, [database/22](../../database/22-database-side-timeouts/2-summary.md) §2) |
| Node | `AbortController.abort()` → `AbortSignal` | `fetch`·스트림 등 signal을 받는 API | signal을 아래로 안 넘기면 소용없다 |

### 3. 실험: Java — 타임아웃 났을 때 작업은 멈췄나

- 작업: 100ms 단계 20개(2초), 단계마다 카운터 +1. 호출자는 500ms에 포기한다. 포기 뒤 1.8초를 더 보고, 그 사이 늘어난 단계 수를 센다.
- 작업 종류: sleep하는 작업(협조적), 인터럽트를 삼키는 작업, 확인 안 하는 CPU 루프, 단계마다 `isInterrupted()`를 확인하는 CPU 루프.

```java
// (1) CompletableFuture.orTimeout — 미래만 실패시킨다
CompletableFuture<Integer> cf = CompletableFuture.supplyAsync(task, pool).orTimeout(500, MILLISECONDS);
// (3)~(6) Executor Future — cancel(true)는 실행 중 스레드를 인터럽트한다
Future<Integer> f = pool.submit(task);
try { f.get(500, MILLISECONDS); } catch (TimeoutException e) { f.cancel(true); }
// (4) 인터럽트를 삼키는 작업
try { Thread.sleep(100); } catch (InterruptedException e) { /* 삼킴 */ }
// (7) 구조적 동시성(JDK 21 preview): 한 하위 작업이 실패하면 형제를 취소
try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
    scope.fork(() -> twoSecondTask());
    scope.fork(() -> { Thread.sleep(500); throw new IllegalStateException("결제 조회 실패"); });
    scope.join();   // 기다리기만 한다. 실패는 scope.exception()으로 꺼내거나 .throwIfFailed()로 던진다
}
// (8) 데드라인: scope.joinUntil(Instant.now().plusMillis(500))
```

(실험, JDK 21.0.12 Temurin `--enable-preview`, 컨테이너 `--cpus=2`, 2026-10-01 — 각 줄의 t는 그 경우의 시작 기준. 포기 시점 단계 수는 4·5단계 경계라 실행마다 1단계씩 다를 수 있다)

```text
t=  510ms (1) orTimeout: TimeoutException
t= 2332ms (1) CompletableFuture.orTimeout(500ms)           포기 시점  5단계 → 1.8초 뒤 20단계 (포기 뒤 15단계 더 함)
t=  509ms (2) cancel(true) 결과=true, isCancelled=true
t= 2310ms (2) CompletableFuture.cancel(true)               포기 시점  5단계 → 1.8초 뒤 20단계 (포기 뒤 15단계 더 함)
t= 2301ms (3) Future.cancel(true) + sleep하는 작업             포기 시점  4단계 → 1.8초 뒤  4단계 (포기 뒤  0단계 더 함)
t= 2302ms (4) Future.cancel(true) + 인터럽트를 삼키는 작업           포기 시점  4단계 → 1.8초 뒤 20단계 (포기 뒤 16단계 더 함)
t= 2301ms (5) Future.cancel(true) + 확인 안 하는 CPU 루프         포기 시점  4단계 → 1.8초 뒤 20단계 (포기 뒤 16단계 더 함)
t= 2301ms (6) Future.cancel(true) + 단계마다 확인하는 CPU 루프       포기 시점  5단계 → 1.8초 뒤  6단계 (포기 뒤  1단계 더 함)
t=  529ms (7) scope.join 반환, 예외=결제 조회 실패
t= 2330ms (7) StructuredTaskScope.ShutdownOnFailure        포기 시점  5단계 → 1.8초 뒤  5단계 (포기 뒤  0단계 더 함)
t=  501ms (8) joinUntil 500ms: TimeoutException → 스코프 종료
t= 2303ms (8) StructuredTaskScope.joinUntil(+500ms)        포기 시점  4단계 → 1.8초 뒤  4단계 (포기 뒤  0단계 더 함)
```

- 관찰 1: `CompletableFuture`는 `orTimeout`도 `cancel(true)`도 작업을 멈추지 못했다. `cancel(true)`는 `true`를 돌려주고 `isCancelled=true`인데 작업은 20단계를 다 했다. JDK 문서 그대로다.
- 관찰 2: Executor `Future.cancel(true)`는 sleep하는 작업을 즉시 멈췄다(0단계).
- 관찰 3: 같은 `cancel(true)`라도 인터럽트를 삼키거나 확인하지 않는 작업은 끝까지 돌았다(포기 뒤 16단계. 재실행에서는 포기 시점이 4·5단계 경계에 걸려 15~16단계 — 실행마다 다르다).
- 관찰 4: 단계마다 확인하는 CPU 루프는 진행 중이던 한 단계를 끝내고 멈췄다(1단계). 확인 간격이 곧 멈추는 데 걸리는 최대 시간이다.
- 관찰 5: 구조적 동시성은 형제 실패(7)·데드라인(8) 때 남은 하위 작업을 멈췄다(0단계). 스코프를 닫을 때 남은 작업을 정리하기 때문이다.

### 4. 실험: Go — 서버는 클라이언트가 끊은 것을 알지만, 핸들러가 봐야 멈춘다

```go
mux.HandleFunc("/ignore", func(w http.ResponseWriter, r *http.Request) {
    work(r.Context(), false, &ignore)   // ctx를 받기만 하고 안 본다(time.Sleep)
})
mux.HandleFunc("/check", func(w http.ResponseWriter, r *http.Request) {
    work(r.Context(), true, &check)     // select { case <-ctx.Done(): return ctx.Err() ... }
})
// 클라이언트: context.WithTimeout(500ms)로 요청
```

(실험, Go 1.23.12 `golang:1.23-alpine`, 컨테이너 `--cpus=2`, 2026-10-01 — t는 각 요청의 시작 기준)

```text
t=  501ms 클라이언트 /ignore: Get "http://127.0.0.1:18093/ignore": context deadline exceeded
t= 2007ms 서버 /ignore 끝: err=<nil>, ctx.Err()=context canceled
t=  501ms 서버 /check 끝: err=context canceled
t=  501ms 클라이언트 /check: Get "http://127.0.0.1:18093/check": context deadline exceeded
t= 2501ms 단계 수: /ignore=20, /check=4
부모 데드라인 == 자식 데드라인(자식에 5초를 줬는데도): true
```

- 관찰 1: 클라이언트가 500ms에 끊자 서버의 `r.Context()`는 취소됐다(`/ignore`가 끝날 때 `ctx.Err()=context canceled`). Go `net/http` 서버가 끊김을 알려 준 것이다.
- 관찰 2: 그래도 `/ignore` 핸들러는 2초·20단계를 다 했다. 신호를 보지 않았기 때문이다. `/check`는 4단계에서 멈췄다.
- 관찰 3: 300ms 부모 아래에 5초 자식을 만들어도 자식 데드라인은 부모와 같았다.

### 5. 라이브러리 타임아웃이 원래 작업을 취소하나 — Resilience4j TimeLimiter

- Resilience4j 2.4.0 `TimeLimiterImpl` 소스:
  - `Future`를 감쌀 때(`decorateFutureSupplier`): 타임아웃이면 `cancelRunningFuture`가 참일 때 `future.cancel(true)`를 부른다. 기본값은 참이다(`TimeLimiterConfig`, 기본 timeout 1초).
  - `CompletionStage`를 감쌀 때(`decorateCompletionStage`): 타임아웃이면 결과 future를 `TimeoutException`으로 **완료시킬 뿐**, 원래 작업을 취소하는 코드가 없다.
- 그리고 `CompletableFuture`는 취소해도 인터럽트하지 않는다(3절 관찰 1). 그래서 `CompletableFuture` 기반 TimeLimiter의 타임아웃 뒤에도 원래 작업은 계속 돈다. 그 작업이 풀 스레드에서 도는 블로킹 호출이면, 끝날 때까지 스레드를 붙잡는다(그동안은 새어 나간 것과 같다).
- `Future` 경로도 작업이 인터럽트를 확인해야 멈춘다(3절 관찰 3). 35번 실험에서 인터럽트를 무시하는 하류는 TimeLimiter 타임아웃 뒤에도 1.5초를 다 썼다([35](../35-timeout-design-worksheet/2-summary.md)).

### 6. 취소가 닿지 않는 구간 — 외부 결제 호출

```text
 주문 처리
   검증 ─ 재고 예약 ─┬─ PG 승인 요청 전송 ─────── 응답 대기 ─── 결과 기록
   (취소 = 중단)     │  여기부터 "보냈으면 보낸 것"                (이 사이에 데드라인이 오면?)
                    └ 커밋 지점: 보내기 직전에 남은 예산을 확인한다
 데드라인이 응답 대기 중에 오면:  결과 = 모름(UNKNOWN)
   → 기다리기를 멈춰도 PG는 승인했을 수 있다
   → 상태를 "확인 필요"로 기록 → 같은 멱등 키로 조회·재시도 → 그래도 모르면 대사(reconciliation)
```

- 외부에 효과를 내는 호출은 보낸 뒤에는 우리 쪽 취소 신호로 멈출 수 없다. 상대가 이미 처리했을 수 있다. 상대가 취소 API(예: Stripe PaymentIntent cancel — 특정 상태에서만)를 주더라도 그것은 별도 요청이고, 이미 일어난 효과를 확정해 주지 않는다([distributed/03](../../distributed/03-partial-failure-and-timeouts/2-summary.md) 실험 A: 타임아웃이 났는데 서버에서는 결제가 됐다).
- 그래서 둘로 나눈다.
  - 보내기 **전**: 남은 예산이 상대의 p99.x보다 작으면 보내지 않는다(08의 최소치 규칙).
  - 보낸 **뒤**: 취소 신호가 와도 그 호출만은 자기 타임아웃까지 기다려 결과를 확정하려 한다. 확정 못 하면 "모름" 상태로 기록하고 사후 확인 경로로 넘긴다.
- *대사(reconciliation)*: 우리 기록과 상대(PG)의 기록을 나중에 대조해 어긋난 것을 찾아 고치는 절차. [domain-modeling/25-reconciliation](../../domain-modeling/25-reconciliation/2-summary.md).

## 쓰이는 자료구조·알고리즘

- **취소 트리** — 부모 → 자식으로만 전파되는 트리. Go `context` 문서상 동작: 부모의 `Done`이 닫히면 자식의 `Done`도 닫힌다(자식 취소는 부모에 영향 없음). 내부 자료구조는 이번에 소스로 확인하지 않았다.
- **인터럽트 플래그** — 스레드마다 불리언 하나. 블로킹 메서드가 이를 보고 `InterruptedException`을 던지며 플래그를 지운다. 그래서 잡은 쪽이 다시 세우거나(`Thread.currentThread().interrupt()`) 위로 던져야 신호가 이어진다.
- **확인 지점(checkpoint)** — 루프·단계 경계에서 신호를 보는 자리. 확인 간격 = 멈추는 데 걸리는 최대 시간(3절 관찰 4).
- **구조적 동시성 = 스코프가 하위 작업의 수명을 소유** — 스코프를 벗어날 때 남은 하위 작업을 정리한다. 동시성 모델은 language 14 `concurrency-models`(미작성, [language 영역](../../language/README.md)). 유닉스 시그널과의 비교는 [os/06-signals](../../os/06-signals/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 순서

1. 작업 경계마다 "누가 이 작업의 수명을 소유하나"를 정한다(요청 문맥·스코프).
2. 신호 객체(ctx·`Future`·`AbortSignal`·스코프)를 **모든** 하위 호출에 넘긴다.
3. 긴 루프·단계 사이에 확인 지점을 둔다.
4. 블로킹 I/O는 그 I/O 자체에 타임아웃을 건다(인터럽트가 안 닿는 경우가 있다).
5. DB는 쿼리 타임아웃(취소 요청)과 서버 측 한도를 함께 건다.
6. 외부 효과 호출 앞에 커밋 지점을 두고, 그 뒤는 "모름" 처리 경로로 설계한다.
7. 지표: 취소 신호를 받은 뒤 끝난 작업 수, 데드라인 뒤 완료 수.

### 2. Java — 인터럽트를 삼키지 않는 관용구

```java
try {
    queue.take();
} catch (InterruptedException e) {
    Thread.currentThread().interrupt();   // 플래그를 되살려 위로 신호를 잇는다
    throw new CancellationException("요청 취소");
}

// CPU 루프: 단계마다 확인
for (Item it : items) {
    if (Thread.currentThread().isInterrupted()) throw new CancellationException();
    process(it);
}
```

- 타임아웃은 `CompletableFuture.orTimeout` 대신 **실제로 인터럽트하는 경로**로 건다: `ExecutorService.submit` + `Future.get(timeout)` + `cancel(true)`, 또는 구조적 동시성(JDK 버전에 맞는 API).
- 블로킹 소켓 호출은 가상 스레드에서 인터럽트로 깨울 수 있다(JEP 444 — 인터럽트하면 소켓을 닫는다). 플랫폼 스레드라면 소켓 타임아웃이 필요하다.

### 3. Java — DB 쿼리 취소

```java
try (PreparedStatement ps = c.prepareStatement(sql)) {
    ps.setQueryTimeout((int) Math.max(1, remaining.toSeconds()));  // 지원하는 드라이버(pgjdbc 등)는 서버에 취소 요청(초 단위)
    ps.executeQuery();
}
// 다른 스레드에서 즉시 취소: ps.cancel()
```

- pgjdbc는 취소 요청을 별도 연결로 보내고, 서버는 57014로 문장을 멈췄다. 소켓 타임아웃만으로는 서버 쿼리가 계속 돌았다([database/22](../../database/22-database-side-timeouts/2-summary.md) §2 실험). PostgreSQL 14+는 `client_connection_check_interval`로 끊긴 클라이언트를 알아챌 수 있다(같은 노트).

### 4. gRPC Java — 서버 핸들러에서 확인

```java
Context ctx = Context.current();
for (Chunk c : chunks) {
    if (ctx.isCancelled()) { return; }          // 클라이언트 취소·데드라인
    process(c);
}
// 또는 콜백: ctx.addListener(cancelled -> stopWork(), executor);
```

### 5. Node — `AbortController`를 아래로 넘긴다

```ts
async function handler(req: Request, signal: AbortSignal) {
  const user = await fetch(userUrl, { signal });             // 같은 신호를 하위 호출에
  const rows = await db.query({ text: sql, signal });         // 라이브러리가 signal을 받는다면(예시)
  for (const r of rows) { signal.throwIfAborted(); work(r); } // 루프 확인 지점
}
const ac = new AbortController();
setTimeout(() => ac.abort(), remainingMs);
```

- `db.query`의 `signal` 옵션은 예시다. 실제 지원 여부는 드라이버 문서로 확인한다.

### 6. 진단

```bash
# 자바: 요청이 끝났는데 아직 도는 작업 스레드 — 같은 스택이 쌓이는지
jcmd <pid> Thread.print | grep -c 'MyWorker.run'
# PostgreSQL: 앱이 떠난 뒤에도 도는 쿼리
psql -c "select pid, now()-query_start as running, state, left(query,60) from pg_stat_activity where state='active' order by running desc"
```

## 장애 시나리오와 대처

### 1. 클라이언트는 포기했는데 서버는 끝까지 처리 → goodput 0 (⚠ 커리큘럼)

- 현상: 과부하 때 서버 CPU는 100%인데 사용자 성공률은 0에 가깝다.
- 보이는 형태: 서버 처리 완료 로그는 많고, 응답 쓰기에서 `Broken pipe`·`ClosedChannelException`이 많다. 처리 시간이 클라이언트 타임아웃보다 긴 쪽에 몰린다.
- 원인: 취소 신호가 없거나 확인하지 않는다(4절 `/ignore`: 끊긴 것을 알면서 20단계를 다 함).
- 대처: 신호를 넘기고 확인 지점을 둔다. 입구에서 이미 만료된 요청은 버린다(원본 §7). 부하 차단([12-backpressure-and-load-shedding](../12-backpressure-and-load-shedding/2-summary.md) · 원본 [ops-patterns/05-backpressure](../../ops-patterns/05-backpressure/2-summary.md)).

### 2. `CompletableFuture` 타임아웃(Resilience4j TimeLimiter)이 원래 작업을 안 멈춘다 → 스레드가 새어 나간다 (⚠ 커리큘럼)

- 현상: TimeLimiter 타임아웃이 잦아진 뒤 전용 스레드 풀이 가득 차고 큐가 자란다. 타임아웃이 났지만 아직 안 끝난 블로킹 하류 호출이 풀 스레드를 붙잡고 있다(끝나면 놓는다 — 반복되면 풀이 찬다).
- 보이는 형태: 스레드 덤프에 하류 호출 중인 풀 스레드가 많다. TimeLimiter의 `TimeoutException` 지표가 높다.
- 원인: CompletionStage 경로는 결과만 실패시키고 원래 작업을 취소하지 않는다(Resilience4j 2.4.0 소스). `CompletableFuture.cancel(true)`도 인터럽트하지 않는다(3절 관찰 1).
- 대처: `Future` 경로 + `cancelRunningFuture=true`, 그리고 작업이 인터럽트를 확인하게 한다. 하류 호출 자체에 타임아웃을 건다(TimeLimiter는 바깥 방어선).

### 3. 인터럽트를 삼킨다 (⚠ 커리큘럼)

- 현상: 종료(shutdown)·취소를 해도 특정 작업이 끝까지 돈다. 애플리케이션 종료가 graceful shutdown 기한을 넘긴다.
- 보이는 형태: 코드에 `catch (InterruptedException e) {}` 또는 로그만 찍고 계속하는 블록. 3절 (4): `cancel(true)` 뒤에도 16단계를 더 했다.
- 원인: `InterruptedException`을 던질 때 플래그가 지워진다. 잡고 아무것도 안 하면 신호가 사라진다.
- 대처: 플래그를 되살리거나 위로 던진다(적용 2). 정적 분석 규칙으로 막는다.

### 4. 취소 불가 외부 호출 → 결과가 모호해진다 (⚠ 커리큘럼)

- 현상: 사용자에게는 실패(504)를 보였는데 PG에는 승인이 있다.
- 보이는 형태: 우리 주문 상태는 실패·대기, PG 정산 파일에는 승인. 응답 대기 중 타임아웃 로그.
- 원인: 보낸 뒤의 호출은 우리 쪽 신호로 멈출 수 없다. 기다리기를 멈춘 것을 실패로 기록했다.
- 대처: 커밋 지점 전 예산 확인, 보낸 뒤에는 "모름" 상태로 기록, 같은 멱등 키로 상태 조회, 사후 대사로 넘긴다([13-idempotency](../13-idempotency/2-summary.md) · [distributed/03](../../distributed/03-partial-failure-and-timeouts/2-summary.md)).

### 5. 앱은 취소했는데 DB 쿼리는 계속 돈다

- 현상·원인·대처: [database/22](../../database/22-database-side-timeouts/2-summary.md) 장애 5. 소켓 타임아웃은 소켓만 닫는다(PostgreSQL은 기본 설정에서 다음 소켓 입출력 때에야 끊김을 안다). 쿼리 타임아웃(취소 요청) + 서버 측 `statement_timeout`을 함께 쓴다.

## 핵심 문장

- 타임아웃은 기다리기를 멈출 뿐이다. 작업을 멈추려면 신호를 하위까지 넘기고, 작업이 그 신호를 확인해야 한다.
- 실험에서 `CompletableFuture`의 `orTimeout`·`cancel(true)`는 작업을 멈추지 못했다(포기 뒤 15단계). Executor `Future.cancel(true)`는 sleep하는 작업을 즉시 멈췄지만, 인터럽트를 삼키거나 확인하지 않는 작업은 끝까지 돌았다.
- Go 서버는 클라이언트 끊김을 `r.Context()`로 알려 주지만, 핸들러가 `Done`을 보지 않으면 20단계를 다 했다.
- Resilience4j TimeLimiter의 CompletionStage 경로는 결과만 실패시키고 원래 작업을 취소하지 않는다. 블로킹 작업이면 끝날 때까지 스레드를 붙잡는다.
- 외부에 효과를 낸 호출은 우리 쪽 신호로 되돌릴 수 없다. 보내기 전에 예산을 확인하고, 보낸 뒤 결과를 모르면 "모름"으로 기록해 조회·대사로 넘긴다.

## 관련 주제·근거

- 선행
  - [08-time-budget-allocation](../08-time-budget-allocation/2-summary.md) — 예산과 최소치 규칙
  - [05-timeouts-and-deadline-propagation](../05-timeouts-and-deadline-propagation/2-summary.md) — 서버는 취소를 확인할 책임이 있다
  - language 14 `concurrency-models` — 미작성, [language 영역](../../language/README.md)
  - [os/06-signals](../../os/06-signals/2-summary.md) — 프로세스 수준의 "그만해" 신호
  - 원본 [ops-patterns/deadline-propagation](../../ops-patterns/deadline-propagation/2-summary.md) §2·§3-2·§4
- 후속·연결
  - [database/22-database-side-timeouts](../../database/22-database-side-timeouts/2-summary.md) — DB 쿼리 취소 실험
  - [35-timeout-design-worksheet](../35-timeout-design-worksheet/2-summary.md) — Resilience4j 순서와 취소
  - [14-graceful-shutdown](../14-graceful-shutdown/2-summary.md) — 종료 때의 취소 · 원본 [ops-patterns/19-graceful-shutdown](../../ops-patterns/19-graceful-shutdown/2-summary.md)
  - [domain-modeling/25-reconciliation](../../domain-modeling/25-reconciliation/2-summary.md)
- 문서·소스
  - Go `context` 패키지 문서(`WithDeadline`, `Done`) — `go doc context.WithDeadline`(go1.23.12)
  - JDK 21 API `CompletableFuture.cancel` — "mayInterruptIfRunning - this value has no effect in this implementation because interrupts are not used to control processing"
  - JEP 453(JDK 21 preview), JEP 505(JDK 25 fifth preview — `open()` 정적 팩토리·`Joiner`), JEP 525(JDK 26 sixth preview) Structured Concurrency <https://openjdk.org/jeps/505>
  - JEP 444 Virtual Threads — 가상 스레드에서 `java.net.Socket` 블로킹 I/O가 인터럽트 가능(인터럽트 시 소켓을 닫음) <https://openjdk.org/jeps/444>
  - gRPC "Cancellation" 가이드 — 라이브러리는 핸들러를 인터럽트할 수단이 대체로 없다, 핸들러가 주기적으로 확인 <https://grpc.io/docs/guides/cancellation/>
  - Resilience4j 2.4.0 `resilience4j-timelimiter/.../internal/TimeLimiterImpl.java`(Future 경로 `cancel(true)`, CompletionStage 경로는 `completeExceptionally`만), `TimeLimiterConfig.java`(timeout 1s, cancelRunningFuture true)
  - Google SRE 책 22장 "Addressing Cascading Failures"의 "Cancellation propagation" 절 <https://sre.google/sre-book/addressing-cascading-failures/>
- 실험 목록
  - `Cancel.java` — CompletableFuture orTimeout/cancel, Executor Future.cancel × 작업 4종, StructuredTaskScope ShutdownOnFailure·joinUntil. JDK 21.0.12 `--enable-preview`, 컨테이너 `--cpus=2`
  - `goctx/main.go` — Go `net/http` 서버 `r.Context()` 취소를 보지 않는 핸들러 vs 보는 핸들러, 부모·자식 데드라인. Go 1.23.12
