# reliability/13-idempotency — 멱등 키 저장소·중복 억제·결과 재생 — 정리 (힌트)

## 해결하는 문제

재시도는 "응답을 못 받았으니 다시 보낸다"이다.\
그런데 응답을 못 받았다고 처리가 안 된 것은 아니다.\
받는 쪽이 "이 요청은 이미 했다"를 기억하지 못하면 재시도는 곧 두 번 실행이다.

```text
 클라이언트 ── POST /payments (1000원) ──▶ 서버: 결제 실행 ✔
            ◀──────── 응답 유실(타임아웃) ──╳
 클라이언트 ── POST /payments (1000원) ──▶ 서버: 또 실행 ✔      → 2000원 출금 (⚠ 중복 결제)
```

쉬운 예: 택배 송장 번호다.
- 같은 물건을 두 번 접수해도 송장 번호가 같으면 택배사는 두 번째 접수를 "이미 접수됨"으로 돌려준다.
- 송장 번호를 손님(클라이언트)이 먼저 정해 오면, 접수 창구(서버)는 번호만 보고 중복을 안다.

똑같은 구조다.\
실무 예: 결제 승인·환불, 포인트 적립, 쿠폰 발급, 주문 생성, 메시지 소비자의 중복 처리. Stripe의 `Idempotency-Key` 헤더가 대표다.

- 기초(접수증 비유, at-least-once vs exactly-once, 기록 다섯 조각, `ConcurrentHashMap.compute`로 선점, TOCTOU 측정)는 원본 [ops-patterns/06-idempotency-store](../../ops-patterns/06-idempotency-store/2-summary.md)에 있다.
- 이 노트는 **DB 위의 멱등 키 저장소**를 다룬다: 유일 제약으로 선점하기, 지문 검사, 처리 중 재요청, 그리고 커리큘럼 ⚠의 **"키 저장과 처리의 비원자성"**을 실험으로 보인다.

## 동작·원리

### 1. 멱등이 성립하는 범위 — 세 층을 나눈다

```text
 프로토콜   HTTP: GET·HEAD·PUT·DELETE 등은 정의상 멱등, POST는 아니다 (RFC 9110 §9.2.2)
 API 계약   POST에 Idempotency-Key를 붙이면 "같은 키 = 같은 결과"를 서버가 약속 (Stripe, IETF 초안)
 구현       키 저장소 + 유일 제약 + 지문 + 상태 기계 — 이게 없으면 위 약속은 말뿐
```

- *멱등(idempotent)*: 같은 요청을 여러 번 보내도 서버 상태에 대한 효과가 한 번 보낸 것과 같은 성질. 응답까지 같을 필요는 없다(RFC 9110의 정의는 "의도한 효과"가 같은 것).
- 멱등 키는 "효과"뿐 아니라 **첫 응답을 재생**해 준다(Stripe는 첫 요청의 상태 코드와 본문을 저장해 돌려주고, 재생 응답에는 `Idempotent-Replayed: true` 헤더가 붙는다. 무엇을 저장·재생하는지는 API마다 다르다). 재시도한 클라이언트가 첫 시도의 결과(승인 번호)를 받아야 다음 단계로 갈 수 있기 때문이다.
- 보장의 범위: 같은 키가 저장소에 **살아 있는 동안**, **같은 범위(사용자·계정) 안에서**만 성립한다. Stripe는 키를 24시간 이상 지나면 지울 수 있고, 지운 뒤 같은 키가 오면 새 요청으로 처리한다(Stripe API 문서 "Idempotent requests").

### 2. 키 저장소의 판정 순서

```text
 요청 (user, key, body)
   │
   ├─ INSERT (user, key, 지문, 'in_progress') ON CONFLICT DO NOTHING
   │      ├─ 1행 삽입 → 내가 선점. 처리하러 간다
   │      └─ 0행      → 이미 있다. 기존 행을 읽는다
   │                    ├─ 지문 다름        → 422 (같은 키, 다른 본문)
   │                    ├─ in_progress      → 409 (처리 중 — 기다리지 않는다)
   │                    └─ completed        → 저장된 응답 재생 (Idempotent-Replayed: true)
   └─ 처리 끝 → status='completed', response=… 저장
```

- *지문(fingerprint)*: 요청 본문에서 의미 있는 필드만 정규화해 해시한 값. 같은 키에 다른 금액이 오는 오용을 잡는다.
- *선점(claim)*: "이 키는 내가 처리한다"를 **원자적으로** 기록하는 것. DB에서는 유일 제약이 원자성을 준다. 확인(SELECT) 후 삽입(INSERT)으로 나누면 그 틈에 여럿이 동시에 이긴다.
- 상태 코드: IETF 초안(draft-ietf-httpapi-idempotency-key-header-07, 2025-10-15 게시, 2026-04-18 만료 — RFC 아님)은 키 누락 400, 다른 본문 422, 처리 중 재요청 409를 권한다. Stripe는 409를 "같은 멱등 키 등으로 다른 요청과 충돌"로 쓰고, 재생 응답에 `Idempotent-Replayed: true` 헤더를 붙인다(Stripe "Advanced error handling").

### 3. 무엇을 저장하나 — 실패 응답도 저장하나?

| 결과 | Stripe(문서 2026-10-01 열람) | 이유 |
|---|---|---|
| 성공 | 상태 코드·본문 저장, 재생 | 기본 |
| 400 등 처리 시작 후 실패 | 저장, 같은 키면 같은 400 | 본문을 고치려면 **새 키**를 써라 |
| 500 | 저장, 같은 500 재생. 결과는 "불확정"으로 취급 | 부작용이 났을 수 있어 새 키 재시도를 권하지 않는다. Stripe가 사후 대사·웹훅으로 정리 |
| 검증 실패·동시 충돌·429 | 저장 안 함 | 엔드포인트 실행이 시작되기 전이라 재시도 가능 |

- 정책은 둘 중 하나를 고르는 것이다.
  - "실패도 저장" — 일시 오류가 그 키의 영구 결과가 된다. 대신 부작용 여부가 불확실한 요청을 두 번 실행하지 않는다.
  - "실패면 재선점 허용" — 일시 오류가 지나면 같은 키로 성공할 수 있다. 대신 실패 전에 부작용이 났다면 두 번 실행될 수 있다.
- 참고: 원본 §「특히 생각해볼 것」의 "FAILED는 재선점을 허용한다"는 후자를 고른 설계다. Stripe는 500에 대해 전자를 고르고 대사로 정리한다. 어느 쪽이든 "실패 전에 외부 부작용이 있었나"를 알 수 있어야 안전하다.

### 4. 커리큘럼 ⚠ — 키 저장과 처리의 비원자성

처리가 **로컬 DB만** 바꾸면 키 기록과 처리를 한 트랜잭션에 넣을 수 있다. 외부 호출이 끼면 그럴 수 없다.

```text
 (a) 로컬만:   BEGIN ─ INSERT key ─ UPDATE balance ─ UPDATE key=completed ─ COMMIT
               죽으면 전부 롤백 → 재시도가 처음부터. 안전

 (b) 외부 호출: [tx1] INSERT key(in_progress) COMMIT
               ── PG 승인 호출 ──▶ 외부에서 돈이 빠짐 ✔
               ╳ 여기서 프로세스가 죽음
               [tx2] UPDATE key=completed   ← 실행되지 않음
               → 키는 in_progress로 남는다. 결과를 모른다.
               락 만료 뒤 재선점한 재시도가 PG를 또 부르면 → 이중 청구
```

- 이 틈은 없앨 수 없다. PG 승인 API처럼 분산 트랜잭션(2단계 커밋)에 참여하지 않는 외부 호출은 로컬 DB 트랜잭션에 함께 묶을 수 없다.
- 줄이는 방법
  1. **외부에도 같은 멱등 키를 넘긴다** — 외부 시스템이 중복을 막아 준다(아래 실험 E2).
  2. **복구 지점(recovery point)** — Brandur(2017)의 설계. 외부 호출 사이의 로컬 변경 묶음을 "원자 단계"로 나누고, 각 단계 끝에 `recovery_point`를 기록한다. 재시도는 마지막 복구 지점부터 이어서 한다.
  3. **대사(reconciliation)** — 결과를 모르는 키(오래된 in_progress)는 외부 기록과 맞춰 확정한다. 재선점 전에 "외부에서 이미 승인됐나"를 조회한다.
  - *외부 상태 변경(foreign state mutation)*: 다른 시스템의 데이터를 바꾸는 호출(카드 승인, 메일 발송). Brandur는 이것을 로컬 ACID가 끝나는 경계로 본다.

### 5. 중복 억제는 받는 쪽마다 따로

```text
 클라이언트 ─(키 K)─▶ API 서버 ─(키 K)─▶ PG          각 경계에서 같은 키로 중복 억제
                         └─(이벤트, 메시지 ID)─▶ 소비자   소비자는 처리한 메시지 ID를 기록
```

- 메시지 소비자의 중복 처리(같은 메시지 두 번 배달)도 같은 구조다. 메시지 ID를 키로 "처리함" 기록과 처리 결과를 한 트랜잭션에 넣는다. [distributed/18-consumer-failure-handling](../../distributed/18-consumer-failure-handling/2-summary.md).

### 실험: PostgreSQL 위의 멱등 키 — 동시 20요청과 중간 크래시

- 환경: PostgreSQL 17.11(전용 컨테이너 `sn-rl-w12-pg`), 격리 수준 READ COMMITTED(기본), Java 21 + JDBC 42.7.4, 처리 시간 20ms.
- 실험 A naive: `SELECT`로 키를 확인하고 없으면 처리 후 키를 `INSERT`(유일 제약 없음).
- 실험 B claim: 유일 키 `(user_id, idem_key)`에 `INSERT … ON CONFLICT DO NOTHING`으로 선점을 **먼저 커밋**하고 처리. 진 쪽은 기존 행을 보고 409/재생(선점 INSERT가 커밋되기 전 짧은 순간에 겹치면 그 커밋만큼은 기다린다).
- 실험 C onetx: 선점·처리·완료를 **한 트랜잭션**에. 진 쪽의 `INSERT`는 유일 인덱스에서 이긴 쪽 커밋을 기다렸다가 0행을 받고 재생한다.
- 실험 E 외부 호출 뒤 크래시(E1 외부에 키 미전달, E2 전달): 선점 → "외부 PG"(별도 테이블, 로컬 트랜잭션 밖) 호출 → 완료 기록 전에 죽음 → 1.2초 뒤 재시도. 재선점 규칙: `in_progress`이고 `locked_at`이 1초 넘게 지났으면 가져온다.

핵심 코드(전체: 실험 목록의 `Idem.java`):

```java
// B. 선점 — 유일 제약이 원자성을 준다
try (PreparedStatement ps = c.prepareStatement(
        "INSERT INTO idem(user_id,idem_key,fingerprint,status,locked_at) VALUES (?,?,?,'in_progress',now()) ON CONFLICT DO NOTHING")) {
    ps.setLong(1, user); ps.setString(2, key); ps.setString(3, fp);
    if (ps.executeUpdate() == 0) return existing(c, user, key, fp);   // 422 / 409 / 재생
}
// E. 주인이 죽은 키 재선점
"INSERT INTO idem(...) VALUES (1,?,'amount=500','in_progress',now())
 ON CONFLICT (user_id,idem_key) DO UPDATE SET locked_at = now()
   WHERE idem.status='in_progress' AND idem.locked_at < now() - interval '1 second'"
```

(실험, PostgreSQL 17.11 + JDK 21.0.12, 두 컨테이너 모두 `--cpus=2`, 2026-10-01 — naive의 중복 수와 claim의 409 수는 실행마다 다르다: 집필 2회·점검 3회 실행에서 naive 5라운드 합 9~17개, claim 409는 6~57번)

```text
PostgreSQL 170011, 격리 수준 READ COMMITTED(기본)
naive      5라운드 x 동시 20요청 → 결제 행 17개 (라운드당 3.4) · 응답 {executed=17, replay=83}
claim      5라운드 x 동시 20요청 → 결제 행 5개 (라운드당 1.0) · 응답 {409 처리 중=22, executed=5, replay=73}
onetx      5라운드 x 동시 20요청 → 결제 행 5개 (라운드당 1.0) · 응답 {executed=5, replay=95}
같은 키, 다른 금액: 422 다른 본문
E1. 외부에 키를 넘기지 않음
  시도 1: 선점 성공
  시도 1: 외부 결제 후 완료 기록 전에 프로세스 죽음
  시도 2: 선점 성공
  시도 2: 완료 기록
  → 외부 결제 건수 2 (외부에 키 전달 안 함)
E2. 외부에도 같은 키를 넘김
  시도 1: 선점 성공
  시도 1: 외부 결제 후 완료 기록 전에 프로세스 죽음
  시도 2: 선점 성공
  시도 2: 완료 기록
  → 외부 결제 건수 1 (외부에 키 전달 함)
```

- 관찰 1 — naive는 같은 키 20요청에서 라운드당 평균 1.8~3.4건을 결제했다. 확인과 기록 사이 20ms 동안 들어온 요청이 모두 "처음"이라고 판단했다.
- 관찰 2 — claim·onetx는 모든 라운드에서 정확히 1건이다. 유일 제약이 선점을 원자로 만든다.
- 관찰 3 — 차이는 진 쪽의 응답이다. claim은 처리 중에 온 요청에 `409`를 22번 돌려줬다(실행마다 6~57번 — 클라이언트가 다시 와야 한다). onetx는 진 쪽이 유일 인덱스에서 기다렸다가 전부 재생을 받았다(대신 그동안 DB 연결과 스레드를 잡는다).
- 관찰 4 — E1: 키 저장소는 "처리 중"인 채 주인을 잃었고, 재선점한 재시도가 외부 결제를 **한 번 더** 불렀다. 키 저장소는 자기 DB 안의 중복만 막는다.
- 관찰 5 — E2: 외부에 같은 키를 넘기자 외부가 두 번째 호출을 무시해 1건으로 끝났다. 실험의 외부 쪽 중복 검사는 순차 실행을 가정한 `WHERE NOT EXISTS`다. 실제 외부 시스템은 동시 요청에도 버티게 유일 제약을 둬야 한다.

## 쓰이는 자료구조·알고리즘

- **키-결과 맵(TTL)** — DB에서는 `(user_id, idem_key)` 기본 키의 B+Tree 인덱스가 그 맵이다. 유일 인덱스 삽입이 "검사 + 기록"을 원자로 만든다. 인덱스 구조는 [data-structure/15-b-tree](../../data-structure/15-b-tree/2-summary.md), 메모리 판은 [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md).
- **상태 기계** — 없음 → in_progress → completed(응답 저장). in_progress → (locked_at 만료) → 재선점. Brandur 설계는 여기에 `recovery_point`(글의 예: started → ride_created → charge_created → finished)를 더한다.
- **lease(기한 있는 소유)** — `locked_at` + 만료 시간. 주인이 죽은 키를 되찾는 규칙. 시간으로 끊기므로 늦게 깨어난 옛 주인을 막으려면 fencing이 필요하다([distributed/12-coordination-and-fencing](../../distributed/12-coordination-and-fencing/2-summary.md)).
- **해시 지문** — 정규화한 본문(필드 정렬·공백 제거·의미 없는 필드 제외)의 SHA-256. 문자열 해시는 [algorithm/27-string-hashing](../../algorithm/27-string-hashing/2-summary.md).
- **TTL 청소(리퍼)** — 오래된 키를 지운다. Brandur 설계의 reaper는 약 72시간 뒤 지운다(감사 필요와 저장 공간의 절충).

## 적용 — 풀어나가는 법

### 1. 순서

1. **멱등이 필요한 쓰기를 고른다** — 재시도가 있는 POST(결제·주문·적립). GET·PUT·DELETE는 설계만 맞으면 본래 멱등이다.
2. **키 생성 주체와 단위** — 클라이언트가 **요청 단위로** 만든다(UUID v4 등). 시도마다 새로 만들면 중복을 못 잡는다. Stripe는 개인정보를 키로 쓰지 말라고 하고 최대 255자다.
3. **키 범위** — 저장소 키는 `(사용자 또는 계정, 클라이언트 키)`.
4. **지문** — 금액·대상·통화처럼 의미 있는 필드만.
5. **선점은 유일 제약으로** — `INSERT … ON CONFLICT DO NOTHING` 또는 Redis `SET key val NX EX ttl`.
6. **로컬만 바꾸면 한 트랜잭션** — 키·처리·응답을 함께 커밋.
7. **외부 호출이 끼면** — 외부에도 키 전달, 복구 지점, 오래된 in_progress의 대사.
8. **TTL과 실패 저장 정책을 정해 문서화** — 클라이언트 재시도 기간보다 길게.

### 2. 스키마와 Java(JDBC) 골격

```sql
CREATE TABLE idempotency_keys (
  user_id        bigint      NOT NULL,
  idem_key       text        NOT NULL,
  fingerprint    text        NOT NULL,
  status         text        NOT NULL,          -- in_progress | completed
  recovery_point text        NOT NULL DEFAULT 'started',
  response_code  int,
  response_body  jsonb,
  locked_at      timestamptz,
  created_at     timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, idem_key)
);
CREATE INDEX ON idempotency_keys (created_at);   -- 청소용
```

```java
Response pay(long userId, String key, PayRequest req) throws SQLException {
    String fp = sha256(req.canonical());                       // 금액·통화·대상만
    try (Connection c = ds.getConnection()) {
        Claim claim = tryClaim(c, userId, key, fp);            // INSERT ... ON CONFLICT DO NOTHING
        switch (claim.kind()) {
            case MISMATCH   -> { return Response.status(422); }
            case IN_FLIGHT  -> { return Response.status(409).header("Retry-After", "1"); }
            case COMPLETED  -> { return claim.saved().withHeader("Idempotent-Replayed", "true"); }
            case MINE       -> {}
        }
        // 외부 호출에도 같은 키 — 외부가 중복을 막게 한다
        PgResult r = pgClient.approve(req, /* idempotencyKey */ userId + ":" + key);
        c.setAutoCommit(false);
        insertPayment(c, userId, r);                            // 로컬 변경과
        complete(c, userId, key, 201, r.toJson());              // 키 완료를 한 트랜잭션에
        c.commit();
        return Response.status(201).body(r);
    }
}
```

- `pgClient.approve` 뒤 `commit` 전에 죽으면 키는 in_progress로 남는다. 이 키의 재선점 경로는 **외부 조회 → 이미 승인됐으면 로컬만 기록**이어야 한다.

### 3. 진단

```sql
-- 주인 잃은 키(결과 불명) — 대사 대상
SELECT user_id, idem_key, locked_at, recovery_point
  FROM idempotency_keys
 WHERE status = 'in_progress' AND locked_at < now() - interval '5 minutes';

-- 이미 생긴 중복 결제 *의심 건* 찾기(같은 사용자·금액이 같은 분에 2건)
-- 별개 주문도 잡히고 분 경계를 넘은 중복은 놓친다 → 주문 ID·PG 거래 ID와 대조해 확정한 뒤 환불
SELECT user_id, amount, count(*), min(created_at), max(created_at)
  FROM payment
 GROUP BY user_id, amount, date_trunc('minute', created_at)
HAVING count(*) > 1;
```

- 지표: 재생 비율(`Idempotent-Replayed`), 409 비율, 422 비율, 오래된 in_progress 수.

## 장애 시나리오와 대처

### 1. 재시도 → 중복 결제·이중 적립 (⚠)

- 현상: 고객 한 명에게 같은 금액이 몇 초 간격으로 두 번 청구됐다. 적립금이 두 배로 들어갔다.
- 보이는 형태: 같은 사용자·금액의 결제 행이 짧은 간격으로 둘. 그 사이에 게이트웨이 타임아웃 또는 클라이언트 재시도 로그.
- 원인: 멱등 키가 없거나, 있어도 "확인 후 기록"이라 동시 요청이 둘 다 통과했다(실험 naive: 같은 키 20요청에 라운드당 1.8~3.4건).
- 대처: 유일 제약 기반 선점. 이미 생긴 중복은 진단 SQL로 찾아 환불·조정한다.

### 2. 키 저장과 처리의 비원자성 → 외부 이중 청구 (⚠)

- 현상: 서버 재시작 직후 몇몇 고객이 PG 쪽에서 두 번 청구됐다. 우리 DB에는 결제가 한 건뿐이다.
- 보이는 형태: 키가 `in_progress`인 채 `locked_at`이 오래됐다가 재선점됐다. PG 거래 내역에 같은 주문의 승인이 둘.
- 원인: 외부 호출 뒤 완료 기록 전에 죽었다. 재선점한 재시도가 외부를 또 불렀다(실험 E1: 외부 결제 2건).
- 대처: 외부에도 같은 키를 넘긴다(실험 E2: 1건). 재선점 전에 외부 조회로 결과를 확정한다. 복구 지점으로 이어서 처리한다.

### 3. 같은 키에 다른 본문 → 엉뚱한 응답 재생

- 현상: 고객이 금액을 고쳐 다시 결제했는데 이전 금액의 승인 응답이 왔다.
- 보이는 형태: 응답 금액과 요청 금액이 다르다. 에러 로그 없음.
- 원인: 지문 검사 없이 키만으로 재생했다. 클라이언트가 "다시 시도" 버튼에서 키를 재사용했다.
- 대처: 지문 불일치는 422. 본문을 바꾸면 새 키를 쓰게 클라이언트를 고친다(Stripe도 "원 요청을 고치려면 새 키").

### 4. 재시도가 TTL보다 늦게 온다

- 현상: 모바일 앱이 오프라인 중 쌓아 둔 요청을 하루 뒤 보냈더니 두 번째 주문이 생겼다.
- 보이는 형태: 같은 키의 두 번째 요청이 "처음 보는 키"로 처리됐다. 키 행의 생성 시각이 청소 주기보다 오래전.
- 원인: 키 보관 기간(예: 24시간)이 클라이언트 재시도 기간보다 짧다.
- 대처: TTL을 클라이언트의 최대 재시도 기간보다 길게 잡는다. 업무 키(장바구니 ID·주문 번호)를 자연 키로 써 유일 제약을 업무 테이블에도 둔다. Stripe는 장바구니 ID에서 키를 파생하는 방법을 예로 든다.

### 5. 처리 중 재요청이 스레드를 묶는다

- 현상: 느린 결제 하나에 클라이언트가 재시도를 거듭하자 서버 스레드·DB 연결이 고갈됐다.
- 보이는 형태: 같은 키의 요청들이 DB 락 대기(`Lock: transactionid` 대기 이벤트)에 걸려 있다.
- 원인: 한 트랜잭션 방식(실험 onetx)에서 진 쪽이 유일 인덱스에서 이긴 쪽 커밋을 기다린다.
- 대처: 처리가 길거나 외부 호출이 있으면 선점을 먼저 커밋하고 진 쪽에 즉시 409를 준다(실험 claim). 클라이언트는 409에 백오프 후 재시도한다.

## 핵심 문장

- 응답을 못 받은 것과 처리가 안 된 것은 다르다. 재시도가 안전하려면 받는 쪽이 키로 기억해야 한다.
- 선점은 유일 제약 하나로 원자적으로 한다. 실험에서 "확인 후 기록"은 같은 키 20요청에 라운드당 1.8~3.4건을 결제했고, 유일 제약은 매번 1건이었다.
- 키 저장소는 자기 DB 안의 중복만 막는다. 외부 호출(2단계 커밋에 참여하지 않는 PG 승인 같은)과 키 기록 사이의 틈은 없앨 수 없으니 외부에도 같은 키를 넘기고, 결과가 불명인 키는 대사로 확정한다.
- 판정 순서는 지문 → 상태다. 같은 키에 다른 본문이면 재생하지 않고 422로 거절한다.
- 실패 응답을 저장할지, 재선점을 허용할지는 "실패 전에 부작용이 있었나"를 알 수 있느냐로 고른다.

## 관련 주제·근거

- 선행
  - [06-retry-backoff-jitter](../06-retry-backoff-jitter/2-summary.md) — 재시도가 이 문제의 출발점
  - 원본 [ops-patterns/06-idempotency-store](../../ops-patterns/06-idempotency-store/2-summary.md) — 메모리 판 구현, TOCTOU 측정, TTL 청소의 경주
- 후속·연결
  - [distributed/12-coordination-and-fencing](../../distributed/12-coordination-and-fencing/2-summary.md) — 주인 잃은 키 재선점과 늦은 옛 주인
  - [distributed/16-outbox-and-dual-write](../../distributed/16-outbox-and-dual-write/2-summary.md) — DB와 다른 시스템에 함께 쓰기
  - [distributed/17-queues-logs-and-delivery-semantics](../../distributed/17-queues-logs-and-delivery-semantics/2-summary.md) · [distributed/18-consumer-failure-handling](../../distributed/18-consumer-failure-handling/2-summary.md) — 소비자 쪽 중복 처리
  - [database/22-database-side-timeouts](../../database/22-database-side-timeouts/2-summary.md) — 락 대기 한도
  - [domain-modeling/25-reconciliation](../../domain-modeling/25-reconciliation/2-summary.md) · [31-batch-job-restart-and-checkpoint](../31-batch-job-restart-and-checkpoint/2-summary.md) — 멱등 재실행
  - [api-design/05-idempotency-keys](../../api-design/05-idempotency-keys/2-summary.md) — API 계약 쪽
- 근거
  - Stripe API 문서 "Idempotent requests"(첫 결과의 상태 코드·본문 저장, 500 포함, 24시간 뒤 정리 가능, 255자, 파라미터 비교, 실행 시작 전 실패는 저장 안 함) <https://docs.stripe.com/api/idempotent_requests>
  - Stripe "Advanced error handling"(400·500 캐시, 500은 불확정, 429는 멱등 계층 앞, `Idempotent-Replayed`, 409 Conflict) <https://docs.stripe.com/error-low-level>
  - IETF draft-ietf-httpapi-idempotency-key-header-07(2025-10-15, 만료 2026-04-18 — RFC 아님): §2.6 Enforcement, §2.7 400·422·409 <https://datatracker.ietf.org/doc/draft-ietf-httpapi-idempotency-key-header/>
  - Brandur Leach, "Implementing Stripe-like Idempotency Keys in Postgres", 2017-10-27(원자 단계·복구 지점·외부 상태 변경·completer·reaper) <https://brandur.org/idempotency-keys>
  - RFC 9110 §9.2.2 Idempotent Methods
- 실험 목록
  - 실험 A~C 동시 20요청 × 5라운드: naive / claim / onetx, 지문 불일치 422 — `Idem.java`, PostgreSQL 17.11 전용 컨테이너, JDK 21 + JDBC 42.7.4, 2회 실행
  - 실험 E1·E2 외부 호출 뒤 크래시 → 재선점 재시도: 외부 키 전달 없음(2건) vs 있음(1건) — 같은 파일
