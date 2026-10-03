# api-design/13-long-running-operations — 긴 작업: `202 Accepted` + 작업 자원 + 폴링 — 정리 (힌트)

## 해결하는 문제

리포트 생성·대량 내보내기·영상 변환처럼 몇 초~몇 분 걸리는 일을 요청 하나 안에서 끝내려 하면, 중간 장비의 타임아웃이 먼저 끊는다.

```text
  클라이언트 ──POST /reports──> LB(읽기 타임아웃 60초) ──> 앱 서버 (리포트 90초 작업)
                                  │ 60초
  클라이언트 <──504 Gateway Timeout─┘                          ...계속 작업 중...
  클라이언트: "실패했나?" → 다시 POST                            90초에 리포트 1 완성
                                                             150초에 리포트 2 완성  ← 중복
```

- 클라이언트가 받은 `504`는 "LB가 기다리다 포기했다"는 뜻이지 "작업이 실패했다"는 뜻이 아니다. **결과 불명**이다.
- 결과 불명에서 재시도하면 같은 일이 두 번 돈다. 비용이 두 배가 되고, 부수효과(메일 발송, 결제)가 있으면 사고가 된다.
- 기본값 예: nginx `proxy_read_timeout` 기본 60초(두 번의 연속 읽기 사이 간격), AWS ALB 연결 유휴 타임아웃 기본 60초(설정 범위 1~4000초) — 각 공식 문서 2026-10-04 확인.

쉬운 예: 세탁소다. 옷을 맡기면 그 자리에서 기다리게 하지 않고 **번호표**를 준다. 손님은 번호표로 "다 됐나요?"를 묻고, 다 되면 찾아간다.

똑같은 구조다.\
`POST`는 접수만 하고 `202 Accepted`와 **작업 자원**(번호표) URL을 돌려준다. 클라이언트는 그 URL을 조회(폴링)해서 끝났는지, 결과가 무엇인지 본다.

- *작업 자원(operation resource, status monitor)*: 긴 작업 하나를 나타내는 별도 자원. 상태·진행률·결과·오류를 담는다.
- *폴링*: 끝날 때까지 같은 자원을 주기적으로 조회하는 것.

실무 예: 정산 리포트 생성(사례 [25-case-settlement-report](../25-case-settlement-report/2-summary.md)), 클라우드의 VM·DB 생성(Google Cloud·Azure API가 모두 이 모양), 대량 CSV 가져오기, 동영상 인코딩.

## 동작·원리

### 1. 시퀀스

```text
  클라이언트                     API 서버                     작업 큐·워커
     │ POST /reports                │                              │
     │ Idempotency-Key: k1 ────────>│ operations에 행 생성(PENDING) │
     │                              │──────── 작업 등록 ───────────>│
     │<── 202 Accepted ─────────────│                              │
     │    Location: /operations/7   │                              │ RUNNING
     │    Retry-After: 2            │                              │
     │                              │                              │
     │ GET /operations/7 ──────────>│                              │
     │<── 200 {done:false,          │                              │
     │        progress: 40%}        │                              │
     │    Retry-After: 2            │                              │
     │        ...                   │<──── 완료(결과 저장) ─────────│ SUCCEEDED
     │ GET /operations/7 ──────────>│                              │
     │<── 200 {done:true,           │                              │
     │        response:{report:..}} │                              │
```

- RFC 9110 §15.3.3 `202 Accepted`: "처리를 위해 받아들였지만 처리가 끝나지 않았다." 나중에 실제로 처리될지도 장담하지 않는다(의도적으로 "noncommittal"). 응답 표현은 현재 상태를 설명하고 **상태 모니터를 가리키거나 담는 것이 좋다**("ought to" — MUST가 아닌 권고 문장)고 적는다.
- 같은 절: "HTTP에는 비동기 작업의 상태 코드를 나중에 다시 보내는 수단이 없다." 그래서 결과는 작업 자원으로 따로 전달한다.
- `Retry-After`: 언제 다시 물어보면 되는지 알려 준다(RFC 9110 §10.2.3, 초 또는 HTTP-date).
- 완료 뒤 결과가 별도 자원이면 작업 자원에 링크를 두거나, 작업 자원을 `303 See Other`로 결과에 보내는 방식도 있다. RFC 9110 §15.4.4는 303을 "POST의 결과를 별도로 식별·북마크·캐시할 수 있는 자원으로 보내는" 데 쓴다고 설명한다.

### 2. 작업 자원의 모양 — 두 회사 관례

```text
  Google AIP-151 (google.longrunning.Operation)       Azure REST API Guidelines (status monitor)
  ─────────────────────────────────────────          ─────────────────────────────────────────
  name     : "operations/abc"                         id     : "abc"
  metadata : Any   ← 진행률·부분 실패                   kind   : (여러 종류일 때)
  done     : bool                                     status : NotStarted | Running |
  result (oneof)                                               Succeeded | Failed | Canceled
    error    : google.rpc.Status                      error  : (Failed일 때)
    response : Any                                    result : (Succeeded + 액션형 LRO일 때만)
```

- Google AIP-151(승인, 2019-07-25 작성, 2025-02-04 개정)
  - 오래 걸릴 수 있는 메서드는 최종 응답 대신 `google.longrunning.Operation`을 돌려줘야 한다(should).
  - "오래"의 기준: 작업마다 기대가 다르지만 **10초**를 경험칙으로 든다.
  - 응답·메타데이터 타입을 annotation으로 선언해야 한다(must). 나중에 바꾸면 하위 호환이 깨지는 변경이다.
  - 생성 중인 자원도 `Get`·`List`에 나오되, 상태 enum으로 "아직 못 쓴다"를 표시해야 한다(should).
  - 작업 시작을 막는 오류는 일반 오류 응답으로, 실행 중 실패는 `Operation.error`(google.rpc.Status)에 담아 돌려줘야 한다(must).
  - 같은 자원에 병렬 작업을 허용하지 않으면 두 번째 시도에 `ABORTED`를 돌려준다(must).
  - 완료된 작업 자원은 시간이 지나면 만료시킬 수 있다(may). 경험칙 **30일**.
- `google.longrunning.Operations` 서비스(operations.proto): `GetOperation`·`ListOperations`·`DeleteOperation`·`CancelOperation`·`WaitOperation`.
  - `CancelOperation`: 비동기 취소를 **시작**한다. 성공은 보장하지 않는다. 취소에 성공하면 작업은 지워지지 않고 `error.code = 1`(CANCELLED)로 남는다.
  - `WaitOperation`: 끝나거나 지정 시간까지 기다렸다 최신 상태를 준다. best-effort라 바로 돌아와도 끝났다는 보장이 없다.
- Azure REST API Guidelines(vNext)
  - p99 응답 시간이 1초를 넘으면 LRO로 만들라고 한다(AIP의 10초 경험칙보다 훨씬 짧다).
  - 시작 응답은 패턴마다 다르다: DELETE와 기존 자원에 대한 POST 액션은 `202 Accepted` + 상태 모니터, PUT은 생성이면 `201 Created`, 교체면 `200 OK` + 자원 본문 + `operation-location`, 자원 없는 액션(`PUT /operations/{id}`)은 `201 Created`. 오래 걸리는 POST로 자원을 **만들지 말라**(PUT을 쓰라)고 한다 — 아래 실험의 `POST /reports`는 AIP 쪽 모양이다.
  - 클라이언트가 `Operation-Id` 헤더로 작업 ID를 정할 수 있게 하고, 같은 ID에 **다른 요청**이 오면 `409 Conflict`를 돌려준다(같은 요청 재시도는 같은 응답).
  - 상태 모니터의 `result`는 성공한 **액션형** LRO(POST 액션·자원 없는 PUT 액션)에만 싣는다. 자원 생성·교체·삭제 LRO에는 `result`를 넣지 말라고 한다(결과는 자원 자체를 GET으로 본다). AIP는 모든 LRO가 `response` 타입을 선언하는 것과 다르다.
  - 상태 조회 응답은 `200 OK` + 끝나지 않았으면 `retry-after`(초). 끝난 상태 모니터는 문서에 적은 기간(최소 24시간) 동안 남겨 둔다.

### 3. 작업 상태 기계

```text
               ┌──────────── cancel ────────────┐
               │                                ▼
  PENDING ──> RUNNING ──> SUCCEEDED          CANCELED
     │           │
     │           └──────> FAILED
     └── cancel ──────────────────────────────> CANCELED

  끝 상태(SUCCEEDED·FAILED·CANCELED)에서는 다른 상태로 가지 않는다.
  done = (상태가 끝 상태인가)
```

- 상태 전이는 조건부 UPDATE로 지킨다: `UPDATE operations SET state='SUCCEEDED' … WHERE id=? AND state='RUNNING'`. 영향받은 행이 0이면 이미 다른 경로(취소·타임아웃)로 끝난 것이다.
- 취소와 완료가 경합하면 먼저 커밋한 쪽이 이긴다. AIP의 "취소는 시도일 뿐"이 이 뜻이다.
- 워커가 죽으면 RUNNING에 영원히 남는다. 그래서 **임대(lease)**·하트비트를 둔다: 워커가 `lease_until`을 주기적으로 늘리고, 만료된 RUNNING은 다른 워커가 다시 집거나 FAILED로 끝낸다.

### 실험: LB 3초 타임아웃 뒤 재시도 vs 202 + 작업 자원

nginx(`proxy_read_timeout 3s`) 뒤에 6초 걸리는 작업을 둔다. 백엔드는 `com.sun.net.httpserver`, 클라이언트는 JDK `HttpClient`. 각 경로가 실제로 만든 리포트 수를 서버가 센다.

```java
// 동기 경로: 요청 안에서 6초 일하고 응답
s.createContext("/reports-sync", ex -> {
    try { Thread.sleep(6000); } catch (InterruptedException e) {}
    int n = syncReports.incrementAndGet();
    send(ex, 200, "{\"report\":\"r-sync-" + n + "\"}", Map.of());
});
// 비동기 경로: 같은 Idempotency-Key면 같은 작업을 돌려주고, 새 키면 작업을 만들어 6초 뒤 완료
s.createContext("/reports", ex -> {
    String key = ex.getRequestHeaders().getFirst("Idempotency-Key");
    String name = key == null ? null : byKey.get(key);
    if (name == null) { /* operations/op-N 생성, byKey.putIfAbsent(key, name), 6초 뒤 done=true */ }
    send(ex, 202, "{\"name\":\"" + name + "\",\"done\":false}", Map.of("Location", "/" + name, "Retry-After", "2"));
});
```

```nginx
location / {
  proxy_pass http://sn-ad-w09-backend:8080;
  proxy_read_timeout 3s;
}
```

(실험, nginx 1.31.6 `nginx:alpine` + JDK 21.0.12 eclipse-temurin, 전용 네트워크, 2026-10-04)

```text
== 1. 동기 처리 + LB 3초 타임아웃, 결과 불명이라 한 번 재시도
  3.4s 시도1 → 504 (3.5s)
  6.5s 시도2 → 504 (3.0s)
 14.5s 서버 집계 {"syncReports":2,"asyncReports":0}
== 2. 202 + 작업 자원, 같은 Idempotency-Key로 재전송, Retry-After만큼 폴링
 14.5s POST → 202 Location=/operations/op-1 {"name":"operations/op-1","done":false}
 14.6s 재전송 POST → 202 Location=/operations/op-1
 14.6s GET /operations/op-1 → 200 {"name":"operations/op-1","done":false}
 16.6s GET /operations/op-1 → 200 {"name":"operations/op-1","done":false}
 18.6s GET /operations/op-1 → 200 {"name":"operations/op-1","done":false}
 20.6s GET /operations/op-1 → 200 {"name":"operations/op-1","done":true,"response":{"report":"r-async-1"}}
 20.6s 서버 집계 {"syncReports":2,"asyncReports":1}
```

nginx 에러 로그(같은 실행):

```text
2026/10/03 19:22:15 [error] 22#22: *1 upstream timed out (110: Operation timed out) while reading response header from upstream, client: 172.30.0.5, server: , request: "POST /reports-sync HTTP/1.1", upstream: "http://172.30.0.3:8080/reports-sync", host: "sn-ad-w09-nginx"
```

- 관찰
  - 1: 클라이언트는 `504`만 두 번 봤다. 서버는 리포트를 **두 개** 만들었다. 클라이언트는 둘 다 받지 못했다. 일은 두 배, 결과는 0이다.
  - 2: 같은 키로 다시 보내도 같은 작업(`op-1`)을 받았다. 폴링 네 번 만에 결과를 받았고 리포트는 하나다.
  - 경과 시간은 실행마다 조금 다르다. 집필 때 3회와 사실 점검 때 3회(같은 코드·이미지)를 합치면 첫 504는 3.2~3.5초, 둘째는 3.0초, 완료 확인은 20.3~20.6초였고 리포트 수(동기 2, 비동기 1)는 매번 같았다.
- 한계: 작업 저장소가 메모리라 서버가 재시작하면 작업이 사라진다. 실무는 DB 표에 둔다(아래 적용 2절).

### 4. 폴링 말고 알려 주기

- 폴링은 단순하지만 끝날 때까지 요청이 쌓인다.
- 대안
  - **완료 웹훅**: 작업이 끝나면 등록된 URL로 알린다 → [09-async-apis-and-webhooks](../09-async-apis-and-webhooks/2-summary.md). 웹훅은 유실될 수 있으니 작업 자원 조회를 같이 남긴다.
  - **긴 대기 조회**: AIP의 `WaitOperation`처럼 서버가 잠시 붙잡고 있다가 바뀌면 답한다. best-effort다.
  - **SSE·WebSocket**: 브라우저 진행률 표시 → [network/38-websocket-sse-long-lived](../../network/38-websocket-sse-long-lived/2-summary.md).

## 쓰이는 자료구조·알고리즘

- **작업 상태 기계** — 끝 상태가 정해진 유한 상태 기계. 전이는 조건부 UPDATE(비교 후 교체)로 원자적으로 한다 → [database/17-occ-and-timestamp-ordering](../../database/17-occ-and-timestamp-ordering/2-summary.md).
- **작업 큐** — PENDING 작업을 꺼내는 FIFO 또는 우선순위 큐. DB로 하면 `SELECT … FOR UPDATE SKIP LOCKED`로 워커끼리 나눠 가진다 → [data-structure/04-queue-deque](../../data-structure/04-queue-deque/2-summary.md).
- **멱등 키 → 작업 ID 맵** — 같은 키는 같은 작업을 돌려준다. DB 유일 인덱스 또는 `putIfAbsent` → [05-idempotency-keys](../05-idempotency-keys/2-summary.md) · [reliability/13-idempotency](../../reliability/13-idempotency/2-summary.md).
- **임대(lease) + 만료 스캔** — `lease_until < now()`인 RUNNING을 찾는 인덱스 범위 스캔. 워커 사망을 감지한다.
- **만료(TTL) 정리** — 끝난 작업을 `finished_at` 기준으로 지운다(AIP 경험칙 30일).

## 적용 — 풀어나가는 법

### 1. 언제 쓰나 — 판단 순서

1. p99 처리 시간이 경로상 가장 짧은 타임아웃(LB·게이트웨이·클라이언트 SDK)에 가까운가? AIP는 10초를 경험칙으로 든다.
2. 결과 불명 재시도가 위험한가(부수효과·비용)? 그렇다면 처리 시간이 짧아도 멱등 키는 필요하다.
3. 진행률·취소가 필요한가? 필요하면 작업 자원이 거의 유일한 답이다.
4. 타임아웃만 늘리는 것은 임시방편이다. 체인 전체(CDN·LB·게이트웨이·클라이언트)를 다 늘려야 하고, 연결이 끊기면 결과를 받을 길이 없다.

### 2. 스키마와 엔드포인트 (PostgreSQL + Java 스케치)

```sql
CREATE TABLE operations (
  id              uuid PRIMARY KEY,
  owner_id        bigint      NOT NULL,              -- 누가 만들었나 (조회 권한 검사용)
  idempotency_key text,
  request_hash    text        NOT NULL,              -- 같은 키 다른 본문 감지
  state           text        NOT NULL,              -- PENDING RUNNING SUCCEEDED FAILED CANCELED
  progress        int         NOT NULL DEFAULT 0,
  result          jsonb,
  error           jsonb,
  lease_until     timestamptz,
  created_at      timestamptz NOT NULL DEFAULT now(),
  finished_at     timestamptz,
  UNIQUE (owner_id, idempotency_key)
);
CREATE INDEX ON operations (state, lease_until) WHERE state IN ('PENDING','RUNNING');
```

```java
// POST /reports
Operation op = operations.findByKey(owner, key);
if (op != null && !op.requestHash().equals(hash(body))) return problem(409, "같은 키에 다른 요청");  // Azure: 409
if (op == null) op = operations.insertPending(owner, key, hash(body));       // UNIQUE 충돌이면 다시 조회
return response(202, op.toJson(), Map.of("Location", "/operations/" + op.id(), "Retry-After", "2"));

// GET /operations/{id}
Operation op = operations.find(id);
if (op == null || op.ownerId() != caller) return problem(404, "없는 작업");    // 남의 작업은 존재도 알리지 않는다
var headers = op.done() ? Map.<String,String>of() : Map.of("Retry-After", String.valueOf(suggestedDelay(op)));
return response(200, op.toJson(), headers);
```

- 같은 키 다른 본문에 무엇을 돌려줄지는 문서마다 다르다. Azure 가이드는 같은 `Operation-Id`에 다른 요청이면 `409`, IETF Idempotency-Key 초안(-07, 만료)은 `422`를 쓴다(위 코드는 Azure 쪽을 따랐다) → [05-idempotency-keys](../05-idempotency-keys/2-summary.md).
- 작업 자원 조회도 인가 대상이다. 작업 ID를 추측 가능한 순번으로 두면 남의 결과를 열람하는 열거 공격에 열린다. UUID + 소유자 검사.

### 3. 클라이언트 폴링 (JDK `HttpClient`)

```java
URI loc = URI.create(base + accepted.headers().firstValue("Location").orElseThrow());
Instant deadline = Instant.now().plus(Duration.ofMinutes(10));               // 전체 대기 상한
while (Instant.now().isBefore(deadline)) {
    HttpResponse<String> g = http.send(HttpRequest.newBuilder(loc).build(), BodyHandlers.ofString());
    Operation op = json.readValue(g.body(), Operation.class);
    if (op.done()) return op;                                                 // error 또는 response 확인
    long wait = g.headers().firstValue("Retry-After").map(Long::parseLong).orElse(2L);
    Thread.sleep(Duration.ofSeconds(wait).plusMillis(ThreadLocalRandom.current().nextLong(500)));  // 지터
}
throw new TimeoutException("작업이 아직 끝나지 않음: " + loc);                // 작업 ID는 남겨 나중에 다시 조회
```

- 클라이언트 쪽 상한이 지나도 작업은 계속 돈다. "포기"가 아니라 "나중에 다시 보기"다. 필요하면 취소 API를 부른다.

### 4. 진단

```bash
curl -i -X POST https://api.example.com/reports -H 'Idempotency-Key: k1' -d '{...}'   # 202, Location, Retry-After 확인
curl -i https://api.example.com/operations/<id>                                        # done·state·Retry-After 확인
```

```sql
-- 오래 RUNNING에 머문 작업 (워커 사망·임대 만료 의심)
SELECT id, state, lease_until, now() - created_at AS age FROM operations
WHERE state = 'RUNNING' AND lease_until < now() ORDER BY created_at LIMIT 20;
```

- 지표: 상태별 작업 수, PENDING 대기 시간, 실행 시간 분포, 작업당 폴링 횟수, 만료 정리 수.

## 장애 시나리오와 대처

### 1. 동기로 처리하다 LB 타임아웃 → 결과 불명 + 재시도 중복 (⚠ 커리큘럼)

- 현상: 리포트 버튼을 두 번 누른 것도 아닌데 리포트가 두 개 생기고, 화면에는 오류가 떴다.
- 보이는 형태: 클라이언트 `504`, LB 로그 `upstream timed out … while reading response header`(실험의 nginx 로그), 앱 로그에는 같은 요청이 정상 완료 두 건.
- 원인: 작업 시간이 LB 읽기 타임아웃보다 길다. 앱은 연결이 끊긴 줄 모르고 끝까지 일했다. 클라이언트는 결과 불명을 실패로 보고 재시도했다(실험 1: `syncReports: 2`).
- 대처: `202` + 작업 자원 + 멱등 키로 바꾼다(실험 2: 리포트 1개). 당장은 클라이언트 재시도를 막고 멱등 키를 받는다. 타임아웃 증가는 임시방편으로만.

### 2. 폴링 폭주

- 현상: 작업 조회 API가 전체 트래픽의 대부분을 차지하고 DB 부하가 오른다.
- 보이는 형태: 작업 하나당 GET 수백 건, 간격 100ms 미만.
- 원인: 클라이언트가 `Retry-After`를 무시하고 바쁜 루프로 폴링한다. 서버가 `Retry-After`를 주지 않는다.
- 대처: `Retry-After`를 작업 종류·진행률에 맞게 준다. SDK에 최소 간격·지터·전체 상한을 넣는다. 그래도 넘치면 작업 조회에 속도 제한(429) → [14-rate-limit-and-quota-contracts](../14-rate-limit-and-quota-contracts/2-summary.md). 완료 웹훅을 제공한다.

### 3. 작업이 RUNNING에서 영원히 멈춤

- 현상: 진행률이 몇 시간째 40%.
- 보이는 형태: `lease_until`이 과거인 RUNNING 행. 워커 배포·OOM 시각과 겹친다.
- 원인: 워커가 죽었는데 상태를 끝내는 주체가 없다.
- 대처: 임대·하트비트를 두고, 만료 스캐너가 재시도하거나 FAILED로 끝낸다. 작업 단계마다 체크포인트를 두면 처음부터 다시 하지 않는다 → [reliability/31-batch-job-restart-and-checkpoint](../../reliability/31-batch-job-restart-and-checkpoint/2-summary.md).

### 4. 취소했는데 결과가 나왔다

- 현상: 사용자가 취소를 눌렀는데 나중에 작업이 SUCCEEDED로 보인다. 또는 비용이 청구됐다.
- 보이는 형태: 취소 요청은 성공 응답, 작업 상태는 SUCCEEDED.
- 원인: 취소는 "시도"다(AIP `CancelOperation`: 성공 보장 없음). 완료와 취소가 경합해 완료가 먼저 커밋됐다.
- 대처: 취소 API 응답을 "요청 접수"로 문서화하고, 최종 상태는 작업 자원으로 확인하게 한다. 상태 전이를 조건부 UPDATE로 한 번만 일어나게 한다. 워커는 단계 사이마다 취소 플래그를 본다.

### 5. 며칠 뒤 조회하니 404

- 현상: 배치 클라이언트가 주말 뒤 작업 결과를 가지러 왔더니 404.
- 보이는 형태: 작업 `finished_at`이 만료 기준보다 오래됨, 정리 작업 로그.
- 원인: 끝난 작업 자원을 만료시켰다(AIP: 만료 허용, 경험칙 30일). 보관 기간이 문서에 없었다.
- 대처: 보관 기간을 계약에 적고, 결과물(파일 등)은 작업 자원과 별도 수명으로 둔다. 만료된 작업은 `404` 대신 `410 Gone`으로 "있었지만 지웠다"를 알리는 선택도 있다(해석).

### 6. 남의 작업 결과가 보인다

- 현상: 보안 점검에서 `/operations/1001`, `1002`…를 순서대로 조회하니 다른 고객의 리포트 링크가 나왔다.
- 원인: 작업 ID가 순번이고 조회에 소유자 검사가 없었다.
- 대처: 추측 불가능한 ID + 소유자 검사. 결과 파일은 짧은 수명의 서명 URL로 준다.

## 핵심 문장

- 504·타임아웃은 "실패"가 아니라 "결과 불명"이다. 긴 작업을 동기로 처리하면 재시도가 곧 중복이다.
- 긴 작업은 `202 Accepted` + 작업 자원(번호표)으로 바꾸고, 시작 요청에는 멱등 키를 받는다.
- 작업 자원은 상태 기계다. 끝 상태에서는 움직이지 않고, 전이는 조건부 UPDATE로 한 번만 일어난다.
- 폴링 간격은 서버가 `Retry-After`로 정하고, 클라이언트는 지터와 전체 상한을 둔다.
- 취소는 시도이고, 끝난 작업 자원은 만료된다. 둘 다 계약에 적는다.

## 관련 주제·근거

- 선행
  - [09-async-apis-and-webhooks](../09-async-apis-and-webhooks/2-summary.md) — 완료 알림을 웹훅으로 줄 때
  - [05-idempotency-keys](../05-idempotency-keys/2-summary.md) — 시작 요청의 멱등 키
- 사례·연결
  - [25-case-settlement-report](../25-case-settlement-report/2-summary.md) — 대용량 리포트의 동기 조회 타임아웃
  - [14-rate-limit-and-quota-contracts](../14-rate-limit-and-quota-contracts/2-summary.md) — 폴링 폭주를 막는 속도 제한, `Retry-After`
  - [reliability/05-timeouts-and-deadline-propagation](../../reliability/05-timeouts-and-deadline-propagation/2-summary.md) · [reliability/07-timeout-taxonomy-by-layer](../../reliability/07-timeout-taxonomy-by-layer/2-summary.md) — 계층별 타임아웃
  - [reliability/31-batch-job-restart-and-checkpoint](../../reliability/31-batch-job-restart-and-checkpoint/2-summary.md) — 재시작·체크포인트
  - [network/33-http-semantics](../../network/33-http-semantics/2-summary.md) — 202·303·Retry-After의 의미
- 문서
  - RFC 9110 §15.3.3 202 Accepted · §15.4.4 303 See Other · §10.2.3 Retry-After <https://www.rfc-editor.org/rfc/rfc9110>
  - Google AIP-151 Long-running operations <https://google.aip.dev/151> (원문 `aip/general/0151.md`, 2025-02-04 개정) — 10초 경험칙, operation_info, 병렬 작업 ABORTED, 만료 30일 경험칙, 오류 위치
  - googleapis `google/longrunning/operations.proto` — Operation 필드(name·metadata·done·error|response), Cancel·Wait의 best-effort 의미
  - Microsoft Azure REST API Guidelines (vNext) 「Long-Running Operations & Jobs」 <https://github.com/microsoft/api-guidelines/blob/vNext/azure/Guidelines.md> — p99 1초 기준, 패턴별 시작 응답(DELETE·POST 액션 202, PUT 생성 201·교체 200), 액션형 LRO에만 `result`, Operation-Id/409, status 열거값, retry-after, 상태 모니터 보관 최소 24시간
  - nginx `ngx_http_proxy_module` — `proxy_read_timeout` 기본 60s <https://nginx.org/en/docs/http/ngx_http_proxy_module.html>
  - AWS "Edit attributes for your Application Load Balancer" — 연결 유휴 타임아웃 기본 60초, 범위 1~4000초 <https://docs.aws.amazon.com/elasticloadbalancing/latest/application/edit-load-balancer-attributes.html>
- 실험 목록
  - LB 타임아웃 + 재시도 vs 202 + 작업 자원 — `Backend.java`·`Client.java`·`nginx.conf`, 일회용 컨테이너 `sn-ad-w09-backend`(eclipse-temurin:21-jdk) · `sn-ad-w09-nginx`(nginx:alpine, 1.31.6) · `sn-ad-w09-client`, 네트워크 `sn-ad-w09-net`, 3회(백엔드 재시작 후 반복). 사실 점검에서 같은 코드로 3회 재실행(nginx 1.31.6) — 504·리포트 수 동일
