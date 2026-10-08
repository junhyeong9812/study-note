# api-design/05-idempotency-keys — 멱등 메서드·Idempotency-Key·재시도 안전 계약 — 정리 (힌트)

## 해결하는 문제

클라이언트가 응답을 못 받으면 결과를 모른다.\
"처리됐는지 모른다"를 안전하게 다시 시도할 수 있게 해 주는 약속이 없으면, 재시도는 곧 두 번 실행이다.

```text
 클라이언트 ── POST /payments (1000원) ──▶ 서버: 결제 처리 중 (300ms)
           ╳ 150ms 타임아웃 → "실패"로 판단
 클라이언트 ── POST /payments (1000원) ──▶ 서버: 또 결제
           ...
 결과: 버튼 한 번에 결제 4건  (실험 S1)
```

쉬운 예: 엘리베이터 버튼과 자판기 동전 투입구.
- 엘리베이터 버튼은 열 번 눌러도 "3층에 간다"는 효과가 한 번과 같다. 불안하면 또 눌러도 된다.
- 자판기에 동전을 넣었는데 반응이 없다고 또 넣으면 두 번 낸 것이다.
- 자판기가 "주문 번호"를 받아 "이 번호는 이미 받았다"고 기억하면, 동전 투입도 다시 해도 되는 동작이 된다.

똑같은 구조다.
- 엘리베이터 버튼 = HTTP의 멱등 메서드(PUT·DELETE·GET).
- 동전 투입 = POST.
- 주문 번호 = `Idempotency-Key` 헤더.

실무 예: 결제 승인, 송금, 주문 생성, 포인트 적립, 쿠폰 발급. 모바일 네트워크가 흔들리거나, 게이트웨이가 504를 내거나, 클라이언트 라이브러리가 연결 끊김에 재시도할 때 생긴다.

- 이 노트는 **API 계약**을 다룬다: 어떤 요청이 재시도해도 되나, 키를 누가·어떤 범위로 만드나, 같은 키에 다른 본문이 오면, 처리 중에 또 오면, 몇 시간 뒤에 오면 무엇을 돌려주나.
- 서버 내부의 키 저장소 구현(유일 제약 선점, 외부 호출과의 비원자성, 실패 저장 정책 실험)은 [reliability/13-idempotency](../../reliability/13-idempotency/2-summary.md)에 있다.

## 동작·원리

### 1. 재시도 안전성은 세 층에서 정해진다

```text
 ┌ 프로토콜 (RFC 9110) ─────────────────────────────────────────────┐
 │ GET·HEAD·OPTIONS·TRACE·PUT·DELETE = 멱등. POST = 멱등 아님     │
 │ 비멱등 요청은 멱등임을 알 수단이 없으면 자동 재시도 SHOULD NOT  │
 │ (§9.2.2) · 프록시는 비멱등 요청 자동 재시도 MUST NOT            │
 └──────────────────────────────────────────────────────────────────┘
 ┌ 클라이언트 라이브러리 (기본값이 제각각) ─────────────────────────┐
 │ 예: JDK 21 HttpClient는 끊긴 재사용 연결에서 GET·HEAD만 1회 재전송 │
 └──────────────────────────────────────────────────────────────────┘
 ┌ API 계약 (서버가 문서로 약속) ───────────────────────────────────┐
 │ POST에 Idempotency-Key → "같은 키 = 한 번만 실행, 결과 재생"      │
 │ 또는 PUT /payments/{클라이언트가 만든 ID} → 메서드 자체가 멱등     │
 └──────────────────────────────────────────────────────────────────┘
```

- *멱등(idempotent)*: 같은 요청을 여러 번 보내도 서버에 대한 **의도한 효과**가 한 번 보낸 것과 같은 성질(RFC 9110 §9.2.2).
  - 응답까지 같을 필요는 없다. 두 번째 `DELETE`는 404를 받을 수 있다.
  - 서버가 요청마다 로그를 남기는 것은 상관없다. 사용자가 요청한 효과가 아니기 때문이다.
- *안전(safe)*: 클라이언트가 상태 변경을 요청하지 않는 메서드(GET·HEAD 등). 안전하면 멱등이다. 역은 아니다.
- PATCH는 RFC 9110이 아니라 RFC 5789가 정의한다. §2는 PATCH가 "neither safe nor idempotent"라고 쓰면서, 멱등하게 보낼 수도 있다고 덧붙인다(예: `If-Match`로 기준 버전을 걸면 두 번째 요청은 실패한다).
- RFC 9110이 멱등을 따로 구분하는 이유가 재시도다. 응답을 읽기 전에 연결이 닫히면, 멱등 요청은 새 연결로 다시 보내도 된다고 적는다.
- 메서드 이름은 **약속**일 뿐이다. `PUT /counter`가 서버에서 `+1`을 하면 멱등이 아니다. 메서드와 구현을 맞추는 것이 API 설계자의 일이다. 메서드 표·쿠키·리다이렉트 같은 HTTP 의미론 전반은 [network/33-http-semantics](../../network/33-http-semantics/2-summary.md)에 있다.

### 실험 A: JDK HttpClient는 어떤 메서드를 스스로 다시 보내나

- 질문: 계층 두 번째 칸(라이브러리 기본값)은 실제로 어떻게 동작하나?
- 장치: 원시 `ServerSocket` 서버. 첫 요청에는 정상 응답하고 keep-alive로 연결을 남긴다. 같은 연결로 온 두 번째 요청은 **끝까지 읽은 뒤**(= 서버는 처리했다고 치고) 응답 없이 닫는다. 서버가 그 경로의 요청을 몇 번 받았는지 센다.

```java
// Retry05.java 핵심 — 연결을 재사용한 요청을 서버가 읽고 응답 없이 끊는다
if (path.startsWith("/x-") && n == 1) return;           // 처리했다고 치고 응답 없이 끊는다
...
http.send(req(base + "/warm-" + m, m), ofString());      // 1) 연결을 풀에 남긴다
http.send(req(base + "/x-" + m, m), ofString());         // 2) 같은 연결 재사용 → 끊김
```

(실험, JDK 21.0.12 temurin 컨테이너 `--cpus=2`, 2026-10-04 — 같은 결과로 2회 실행)

```text
JDK 21.0.12, jdk.httpclient.enableAllMethodRetry=null
GET    → 클라이언트: 응답 200                 서버가 받은 /x-GET 요청 수: 2
POST   → 클라이언트: 예외 IOException         서버가 받은 /x-POST 요청 수: 1
PUT    → 클라이언트: 예외 IOException         서버가 받은 /x-PUT 요청 수: 1
DELETE → 클라이언트: 예외 IOException         서버가 받은 /x-DELETE 요청 수: 1
JDK 21.0.12, jdk.httpclient.enableAllMethodRetry=true
GET    → 클라이언트: 응답 200                 서버가 받은 /x-GET 요청 수: 2
POST   → 클라이언트: 응답 200                 서버가 받은 /x-POST 요청 수: 2
PUT    → 클라이언트: 응답 200                 서버가 받은 /x-PUT 요청 수: 2
DELETE → 클라이언트: 응답 200                 서버가 받은 /x-DELETE 요청 수: 2
```

- 관찰 1 — 기본 설정에서 GET은 클라이언트 모르게 **두 번** 서버에 갔다. 호출 코드는 200 하나만 봤다.
- 관찰 2 — PUT·DELETE는 RFC상 멱등인데도 JDK는 다시 보내지 않았다. OpenJDK jdk21u 소스 `MultiExchange.isIdempotentRequest`가 `"GET", "HEAD"`만 참으로 돌려준다. 프로토콜의 멱등 목록과 라이브러리의 재시도 목록은 다르다.
- 관찰 3 — 시스템 속성 `jdk.httpclient.enableAllMethodRetry=true`를 켜면 POST도 다시 갔다. 서버 쪽 멱등 키 없이 이 속성을 켜면 중복 실행 경로가 하나 생긴다.
- 해석: 재시도는 이 실험처럼 라이브러리 안에서 조용히 일어날 수도 있다. 서버 API는 "클라이언트가 재시도할 것"을 전제로 설계해야 한다.
- 같은 소스(`getExceptionalCF`)에서 재시도 조건은 재사용 연결이 닫힌 경우(`ConnectionExpiredException`)와 연결 실패(`ConnectException`), 그리고 HTTP/2에서 상대가 처리하지 않았다고 알린 요청이다. 한 요청에 1회(`retriedOnce`)다.
  - GET·HEAD 제한(`canRetryRequest`)은 `ConnectionExpiredException` 쪽에만 걸린다. `ConnectException`(연결 자체가 안 됨 → 요청이 나가지 않음)과 "처리 안 됨" 응답은 메서드와 무관하게 다시 보낸다. 서버가 받지 않은 요청이라 중복 위험이 없다.

### 2. 타임아웃 뒤 클라이언트가 모르는 세 가지

```text
 시간 →
 (가) 요청 유실      C ──X                          서버는 모른다 → 재시도해도 1번
 (나) 처리 후 응답 유실 C ──▶ S [처리 완료] ──X      재시도하면 2번째 실행 (⚠)
 (다) 처리 중         C ──▶ S [처리 중......]        재시도가 처리 중인 것과 겹친다
       C: 150ms 타임아웃 ─┘
```

- 클라이언트 입장에서 셋은 구분되지 않는다. 다 "타임아웃"이다.
- 서버가 키를 기억하면 셋 다 안전해진다.
  - (가) 처음 보는 키 → 처리.
  - (나) 완료된 키 → 저장한 첫 응답을 **재생**.
  - (다) 처리 중인 키 → 409로 "아직 처리 중, 잠시 뒤 다시".

### 3. Idempotency-Key 계약의 부품

```text
 요청 (계정 A, 키 K, 본문 B)
   │
   ├─ 키 없음, 키 필수 작업       → 400  (초안 §2.7)
   ├─ (A, K) 처음                 → 선점 후 처리 → 201, 결과 저장
   ├─ (A, K) 있음, 지문(B) 다름   → 422  "다른 본문에 키 재사용"
   ├─ (A, K) 있음, 처리 중        → 409  (+ Retry-After 같은 힌트는 서버 선택)
   └─ (A, K) 있음, 완료           → 첫 응답 재생 (Stripe: Idempotent-Replayed: true)
```

- *지문(fingerprint)*: 요청 본문에서 의미 있는 필드를 정규화해 해시한 값. 같은 키에 다른 금액이 오는 오용을 잡는다. 초안 §2.4는 전체 본문 체크섬·선택 필드 체크섬·필드 값 비교·서명 등을 예로 든다(MAY).
- *키 범위(scope)*: 키를 무엇과 묶어 유일하게 보나. 초안 §5는 서버가 "클라이언트 키 + 서버만 아는 클라이언트 속성"의 복합 키를 쓰라고 권한다. 같은 키라도 계정이 다르면 다른 요청이다.
- *보관 기간(TTL)*: 이 기간이 지나면 같은 키도 새 요청이 된다. 초안은 기간을 정하지 않고 "문서에 공개하라"(SHOULD)고만 한다.
- *재생(replay)*: 두 번째 요청에 첫 요청의 상태 코드와 본문을 그대로 돌려주는 것. 클라이언트가 첫 시도의 결과(결제 ID)를 받아야 다음 단계로 갈 수 있다.

출처마다 규칙이 다르다. "멱등 키"라는 같은 이름 아래 약속이 다르므로, 쓰는 API의 문서를 확인해야 한다.

| 항목 | IETF draft-ietf-httpapi-idempotency-key-header-07 (초안, 2025-10-15, 만료 2026-04-18) | Stripe API v1 | Stripe API v2 | Google AIP-155 |
|---|---|---|---|---|
| 지위 | 만료된 Internet-Draft — RFC 아님 | 회사 관례 | 회사 관례 | 회사 설계 지침 |
| 전달 | `Idempotency-Key` 헤더, 값은 Structured Field **String**(따옴표) | `Idempotency-Key` 헤더 | `Idempotency-Key` 헤더 | 요청 메시지의 `request_id` 필드 |
| 형식 | UUID 등 무작위 값 권장 | V4 UUID 등 충분한 엔트로피, 최대 255자, 개인정보 금지 | UUID 권장, 안 주면 Stripe가 생성 | UUID를 받을 수 있어야(should), UUID만 허용해도 됨 |
| 대상 메서드 | POST·PATCH 같은 비멱등 메서드 | POST만. GET·DELETE에 보내면 효과 없음 | POST·DELETE | 표준 메서드 포함 요청 메시지 |
| 보관 | 서버가 정해 문서화(SHOULD) | 24시간 이상 지나면 지울 수 있음 | 30일 안, 같은 API·같은 계정 | "합리적 기간" |
| 실패 응답 | 완료된 결과는 성공이든 에러든 재생 | 첫 결과를 성공·실패 무관 저장, 500도 재생 | 실패했던 요청은 부작용 없이 **다시 실행**해 새 응답 | 이전 **성공** 응답을 돌려준다(should) |
| 다른 본문 | 422 | 에러(파라미터 비교) | — [?] | — |
| 처리 중 재요청 | 409 | 409 Conflict("같은 멱등 키 등으로 다른 요청과 충돌"), 저장하지 않으니 재시도 가능 | — [?] | — |

- 초안 §2.7은 400·422 뒤에는 클라이언트가 요청을 **고친 뒤** 재시도해야 하고, 409는 고칠 필요가 없다고 적는다.
- Stripe v1은 "실패도 저장"을, v2는 "실패면 다시 실행"을 고른다. 이 선택의 위험(부작용이 났을지 모르는 500을 다시 실행)은 [reliability/13 §3](../../reliability/13-idempotency/2-summary.md)에 있다.

### 4. 키 대신 쓸 수 있는 설계 — 메서드 자체를 멱등으로

```text
 (a) POST /payments            + Idempotency-Key: "k-1"      키 저장소 필요
 (b) PUT  /payments/pay_7f3e…  (ID를 클라이언트가 생성)        PUT이 본래 멱등
 (c) POST /orders/{orderId}/payment                          업무 키(주문당 결제 1건)를 유일 제약으로
```

- (b) 클라이언트가 자원 ID를 정하면 "만들기"가 "이 ID의 자원이 이 상태가 되게 하라"가 된다. 두 번 보내도 같은 자원 하나다. 이미 있으면 덮어쓸지, `If-None-Match: *`로 "없을 때만 생성"(412)으로 할지 정한다([11-concurrency-control-in-apis](../11-concurrency-control-in-apis/2-summary.md)).
- (c) 업무 규칙상 한 번뿐인 동작(주문당 결제 1건)은 업무 키에 유일 제약을 거는 쪽이 더 단단하다(설계 판단). 키 보관 기간이 지나도 막힌다. 사례 [22-case-order-point](../22-case-order-point/2-summary.md)의 "order_id가 이미 열쇠다"가 이 설계다.
- 키 방식이 맞는 경우: 같은 내용을 여러 번 정상적으로 할 수 있는 동작(같은 금액 송금을 두 번 하고 싶을 수 있다). 업무 키가 없어 "이번 시도"를 구분할 것이 키뿐이다.

### 실험 B: HTTP 수준에서 이중 결제와 멱등 키

- 환경: JDK 21.0.12(temurin 컨테이너) + PostgreSQL 17.11(전용 컨테이너 `sn-ad-w05-pg`), JDBC 42.7.7, 두 컨테이너 `--cpus=2`.
- 서버: JDK `com.sun.net.httpserver` `POST /payments`. 결제 처리 300ms(예시). 키 저장소 = `idem(account, idem_key)` 기본 키 + 지문 + 상태.
- 클라이언트: JDK `HttpClient`, 요청 타임아웃 150ms, 타임아웃·409면 200ms 쉬고 최대 4회 시도.

```java
// Idem05.java 핵심 — 서버
String key = raw.replaceAll("^\"|\"$", "");               // sf-string 따옴표 제거
String fp = sha256(canonical(body));                        // amount·to만, 정렬
INSERT INTO idem(account,idem_key,fingerprint,status) VALUES (?,?,?,'in_progress') ON CONFLICT DO NOTHING
if (n == 0) {                                               // 이미 있는 키
    if (!fp.equals(saved.fp))           → 422
    if (saved.status == in_progress)    → 409, Retry-After: 1
    else                                → 저장 응답 재생 + Idempotent-Replayed: true
}
// 처리(300ms) → 한 트랜잭션에서 payment INSERT + idem completed·응답 저장
```

```java
// 클라이언트 — 논리 작업 하나에 키 하나. 시도마다 같은 키를 보낸다
String key = UUID.randomUUID().toString();
for (int attempt = 1; attempt <= 4; attempt++) {
    String r = once(http, uri, acct, key, amount, Duration.ofMillis(150));
    if (!r.startsWith("timeout") && !r.startsWith("409")) break;
    Thread.sleep(200);
}
```

(실험, JDK 21.0.12 + PostgreSQL 17.11, 2026-10-04 — 3회 실행, S1·S2·S6 결과는 3회 모두 같았다. 결제 ID 숫자는 시퀀스 값이라 의미 없다)

```text
JDK 21.0.12, 서버 처리 300ms, 클라이언트 요청 타임아웃 150ms, 최대 4회 시도

[S1] 멱등 키 없음 + 타임아웃 재시도
  시도1=timeout | 시도2=timeout | 시도3=timeout | 시도4=timeout
  → payment 행 4

[S2] 같은 키로 재시도 (논리 작업 1개 = 키 1개)
  시도1=timeout | 시도2=201 replayed {"id":5}
  → payment 행 1

[S3] 클라이언트 버그: 시도마다 새 키
  시도1=timeout | 시도2=timeout | 시도3=timeout | 시도4=timeout
  → payment 행 4

[S4] 같은 키, 다른 금액
  1차(1000): 201 {"id":10}
  2차(5000): 422 {"title":"Idempotency-Key is already used"}
  3차(1000): 201 replayed {"id":10}
  다른 계정 같은 키(1000): 201 {"id":11}
  → payment 행 2

[S5] 키 없이 키 필수 엔드포인트 호출
  400 {"title":"Idempotency-Key is missing"}

[S6] 같은 키 동시 10요청
  상태 코드 분포 {201=1, 409=9}
  → payment 행 1
```

- 관찰 1 (S1) — 클라이언트는 네 번 다 "실패"를 봤는데 서버는 네 번 다 결제했다. 클라이언트가 본 것과 서버에서 일어난 일이 정반대다.
- 관찰 2 (S2) — 같은 키로 재시도하자 두 번째 시도가 첫 결과(`id 5`)를 재생받았다. 결제는 1건.
- 관찰 3 (S3) — 서버가 키를 지원해도, 클라이언트가 시도마다 새 키를 만들면 S1과 같다. 키는 **시도**가 아니라 **사용자 의도(논리 작업)** 단위다.
- 관찰 4 (S4) — 같은 키에 금액만 바꾸면 422. 원래 금액으로 다시 보내면 재생. 다른 계정이 같은 키 문자열을 쓰면 별개 요청으로 처리됐다(키 범위 = 계정).
- 관찰 5 (S6) — 동시 10요청 중 1개만 처리, 9개는 409. 유일 제약 선점이 원자성을 준다. 409를 받은 클라이언트는 잠시 뒤 같은 키로 다시 와서 재생을 받으면 된다.

## 쓰이는 자료구조·알고리즘

- **키-결과 저장소(TTL 있는 맵)** — DB에서는 `(account, idem_key)` 기본 키의 B+Tree 인덱스가 맵이다. 유일 인덱스 삽입이 "있나 확인 + 기록"을 한 번에 한다. [data-structure/15-b-tree](../../data-structure/15-b-tree/2-summary.md), Redis라면 `SET key val NX EX ttl`([data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)).
- **해시 지문** — 정규화한 본문의 SHA-256. 필드 순서·공백 차이로 지문이 갈리지 않게 정렬 후 해시한다. [algorithm/27-string-hashing](../../algorithm/27-string-hashing/2-summary.md).
- **상태 기계** — 없음 → in_progress → completed(응답 저장). in_progress 중 재요청 = 409.
- **재시도 + 지수 백오프** — 409·타임아웃·503에 같은 키로 다시. 대기 시간은 [reliability/06-retry-backoff-jitter](../../reliability/06-retry-backoff-jitter/2-summary.md).
- **무작위 식별자** — UUIDv4(122비트 무작위). 키가 추측 가능하면 남의 저장 응답을 꺼낼 위험(초안 §5 "Data leaks")이 생긴다.

## 적용 — 풀어나가는 법

### 1. API 설계자의 순서

1. **재시도가 일어나는 쓰기를 찾는다** — 결제·주문·송금처럼 두 번 실행되면 손해인 POST·PATCH.
2. **메서드로 해결되나 본다** — 클라이언트가 ID를 정해 PUT으로 만들 수 있나? 업무 키(주문 ID)로 유일 제약을 걸 수 있나? 되면 그쪽이 단순하다.
3. **안 되면 키 계약을 문서화한다**
   - 헤더 이름과 형식(UUID, 길이 상한), 필수 여부(없으면 400).
   - 범위: 계정·API 키 단위. 키 문자열만으로 전역 조회하지 않는다.
   - 지문 대상 필드와 불일치 시 422.
   - 처리 중 재요청 409와 재시도 간격.
   - 보관 기간: 클라이언트의 최대 재시도 기간보다 길게.
   - 실패 응답 저장 여부(Stripe v1식 "그대로 재생" vs v2식 "다시 실행").
4. **재생임을 알린다** — `Idempotent-Replayed: true` 같은 헤더(Stripe 관례)로 클라이언트·로그가 구분하게 한다.
5. **클라이언트 SDK에 키 생성을 넣는다** — 사용자가 버튼을 누를 때(논리 작업 시작) 키를 만들고, 재시도 루프 밖에 둔다.
6. **하류에도 키를 넘긴다** — PG·외부 API도 멱등 키를 받으면 같은 키(또는 파생 키)를 넘긴다(reliability/13 실험 E2).

### 2. 클라이언트 코드 모양 (JDK HttpClient)

```java
// 키는 "결제하기" 버튼을 누른 순간 한 번 만든다 — 재시도 루프 밖
String key = UUID.randomUUID().toString();
HttpRequest req = HttpRequest.newBuilder(URI.create(base + "/payments"))
        .timeout(Duration.ofSeconds(3))
        .header("Idempotency-Key", "\"" + key + "\"")       // 초안 형식. Stripe는 따옴표 없이
        .POST(BodyPublishers.ofString(json))
        .build();
for (int attempt = 1; attempt <= 5; attempt++) {
    try {
        HttpResponse<String> r = http.send(req, BodyHandlers.ofString());
        int s = r.statusCode();
        if (s == 409 || s == 429 || s == 503) { sleep(backoff(attempt, r)); continue; }  // 같은 키로 다시
        return r;                                          // 2xx, 400, 422: 재시도하지 않는다
    } catch (HttpTimeoutException | ConnectException e) {
        sleep(backoff(attempt, null));                     // 결과 불명 → 같은 키로 다시
    }
}
throw new PaymentUnknownException(key);                    // 끝까지 모르면 키로 조회·대사
```

- 400·422는 요청을 고쳐야 하는 에러다. 고친 요청에는 **새 키**를 쓴다(Stripe "Advanced error handling": 원 요청을 고치려면 새 키).
- 5xx를 같은 키로 재시도할지는 API 문서를 따른다. Stripe v1은 500을 저장해 같은 500을 재생하고, 새 키 재시도는 부작용 가능성 때문에 권하지 않는다.

### 3. 진단

```bash
# 재생 여부·409를 헤더로 본다
curl -i -X POST https://api.example.com/payments \
  -H 'Idempotency-Key: "8e03978e-40d5-43e8-bc93-6894a57f9324"' \
  -d 'amount=1000&to=shop-1'
# HTTP/1.1 201 ...                       (첫 요청)
# HTTP/1.1 201 ... Idempotent-Replayed: true   (같은 키 두 번째)
```

- 지표: 키 없는 쓰기 요청 비율, 재생 비율, 409·422 비율, 같은 계정·같은 금액의 짧은 간격 중복 건수.
- 로그에 키를 남겨 "이 결제는 몇 번 시도됐나"를 추적한다. 키에 개인정보를 넣지 않는다(Stripe 문서).

## 장애 시나리오와 대처

### 1. 타임아웃 뒤 재시도 → 이중 결제 (⚠)

- **현상**: 네트워크가 불안정한 날, 고객이 결제 한 번에 여러 번 청구됐다.
- **보이는 형태**: 같은 계정·금액의 결제가 수백 ms 간격으로 여러 건. 클라이언트 로그에는 같은 요청의 타임아웃이 여러 번. 서버 로그에는 전부 201.
- **원인**: 결제 POST에 멱등 계약이 없거나, 클라이언트가 시도마다 새 키를 만든다(실험 S1·S3: 결제 4건). 라이브러리 설정(`jdk.httpclient.enableAllMethodRetry=true` 같은)이 POST를 다시 보내기도 한다(실험 A). RFC 9110 §9.2.2는 프록시의 비멱등 요청 자동 재시도를 금지(MUST NOT)하지만, 설정으로 켤 수 있는 제품이 있다(nginx `proxy_next_upstream non_idempotent` — nginx 1.9.13부터 기본은 업스트림에 이미 보낸 POST·LOCK·PATCH를 다음 서버로 넘기지 않고, 이 옵션이 그것을 켠다).
- **대처**: 키 계약 도입, 키 생성을 재시도 루프 밖으로. 이미 생긴 중복은 같은 계정·금액·짧은 간격으로 후보를 찾아 PG 거래와 대사한 뒤 환불한다.

### 2. 같은 키에 다른 본문 — 처리 규칙이 없다 (⚠)

- **현상**: 고객이 금액을 고쳐 다시 결제했는데 이전 금액의 승인 결과가 왔다. 또는 반대로 키만 같으면 무조건 새로 처리해 이중 결제.
- **보이는 형태**: 응답 금액과 요청 금액이 다르다. 에러 로그는 없다.
- **원인**: 서버가 키만 보고 재생했다(지문 검사 없음). 클라이언트가 "다시 시도" 화면에서 키를 재사용했다.
- **대처**: 지문 불일치는 422로 거절(초안 §2.7, 실험 S4). 본문을 바꾸면 새 키를 만들도록 클라이언트를 고친다.

### 3. 키 범위가 전역 → 남의 응답이 재생된다

- **현상**: 고객 B가 결제했는데 고객 A의 결제 결과(다른 카드 끝자리)가 응답으로 왔다.
- **보이는 형태**: 재생 응답의 계정 ID가 요청 계정과 다르다.
- **원인**: 저장소를 키 문자열 하나로만 조회했다. 클라이언트 SDK 버그로 키가 짧거나 순차적이어서 겹쳤다.
- **대처**: 저장소 키를 `(계정, 클라이언트 키)`로(초안 §5 복합 키, 실험 S4의 다른 계정 = 별개 요청). 키 형식을 UUID로 검증하고 아니면 400.

### 4. 보관 기간보다 늦은 재시도

- **현상**: 오프라인에서 쌓인 요청을 앱이 하루 뒤 보냈더니 주문이 하나 더 생겼다.
- **보이는 형태**: 같은 키의 두 번째 요청이 "처음 보는 키"로 처리됐다.
- **원인**: 키 보관 기간(Stripe v1은 24시간 이후 정리 가능)보다 클라이언트 재시도 기간이 길다.
- **대처**: 보관 기간을 문서에 쓰고 SDK의 재시도 기간을 그보다 짧게. 한 번뿐인 동작은 업무 키 유일 제약을 함께 둔다(§4 (c)).

### 5. 409 폭주

- **현상**: 느린 결제 하나에 클라이언트들이 409를 받고 즉시 다시 와서 요청이 폭증한다.
- **보이는 형태**: 같은 키의 409가 초당 수십 건.
- **원인**: 클라이언트가 409를 받자마자 대기 없이 재시도한다.
- **대처**: 409에 `Retry-After` 같은 힌트를 주고, 클라이언트는 지수 백오프 + 지터로 기다린다. 처리 시간이 길면 202 + 작업 자원으로 바꾼다([13-long-running-operations](../13-long-running-operations/2-summary.md)).

## 핵심 문장

- 응답을 못 받은 것과 처리가 안 된 것은 다르다. 실험에서 클라이언트는 타임아웃 4번을 봤고 서버는 결제 4건을 만들었다.
- 재시도 안전성은 프로토콜(RFC 9110 멱등 메서드)·라이브러리 기본값(JDK 21 HttpClient는 GET·HEAD만 자동 재전송)·API 계약 세 층이 정한다. 층마다 목록이 다르다.
- 멱등 키는 시도가 아니라 사용자 의도 하나에 하나다. 시도마다 새 키를 만들면 키가 없는 것과 같다.
- 키 계약에는 범위(계정), 지문(다른 본문 422), 처리 중(409), 보관 기간, 실패 저장 정책이 들어간다. IETF 초안·Stripe v1·v2·AIP-155가 이 칸들을 서로 다르게 채운다.
- 클라이언트가 ID를 정하는 PUT이나 업무 키 유일 제약으로 풀 수 있으면 키 저장소보다 단순하다.

## 관련 주제·근거

- 선행
  - [03-status-codes-for-apis](../03-status-codes-for-apis/2-summary.md) — 400·409·422 선택
  - [reliability/13-idempotency](../../reliability/13-idempotency/2-summary.md) — 키 저장소 구현, 외부 호출과의 비원자성, 실패 저장 정책 실험
  - [network/33-http-semantics](../../network/33-http-semantics/2-summary.md) — 안전·멱등 메서드, 프록시 재시도 규칙
- 후속·연결
  - [11-concurrency-control-in-apis](../11-concurrency-control-in-apis/2-summary.md) — `If-None-Match: *`로 없을 때만 생성
  - [09-async-apis-and-webhooks](../09-async-apis-and-webhooks/2-summary.md) · [10-notification-delivery-pipeline](../10-notification-delivery-pipeline/2-summary.md) · [13-long-running-operations](../13-long-running-operations/2-summary.md) · [14-rate-limit-and-quota-contracts](../14-rate-limit-and-quota-contracts/2-summary.md)
  - 사례 [22-case-order-point](../22-case-order-point/2-summary.md)(업무 키가 멱등 키) · [23-case-coupon-issue](../23-case-coupon-issue/2-summary.md) · [27-case-refund](../27-case-refund/2-summary.md)
  - [reliability/06-retry-backoff-jitter](../../reliability/06-retry-backoff-jitter/2-summary.md) · [database/18-app-level-concurrency-patterns](../../database/18-app-level-concurrency-patterns/2-summary.md)(유니크 제약) · [distributed/16-outbox-and-dual-write](../../distributed/16-outbox-and-dual-write/2-summary.md)
  - 원본 [ops-patterns/06-idempotency-store](../../ops-patterns/06-idempotency-store/2-summary.md)
- 후속(AI 엔지니어링): [ai-engineering/20-agent-loop-and-tool-safety](../../ai-engineering/20-agent-loop-and-tool-safety/2-summary.md) — 에이전트 도구 재시도의 중복 부작용
- 근거
  - RFC 9110 §9.2.1 Safe Methods, §9.2.2 Idempotent Methods(정의, 자동 재시도 SHOULD NOT) <https://www.rfc-editor.org/rfc/rfc9110#section-9.2.2>
  - IETF draft-ietf-httpapi-idempotency-key-header-07(2025-10-15 게시, 2026-04-18 만료 — RFC 아님): §2.1 Item Structured Header String, §2.2 유일성·UUID, §2.3 만료 정책 공개, §2.4 지문, §2.6 재생·409, §2.7 400·422·409, §5 저엔트로피 키·복합 키 <https://datatracker.ietf.org/doc/draft-ietf-httpapi-idempotency-key-header/>
  - Stripe API "Idempotent requests"(성공·실패 무관 저장, 500 포함, 255자, V4 UUID, 개인정보 금지, 24시간 이후 정리 가능, 파라미터 비교, 실행 시작 전 실패는 저장 안 함, POST만) <https://docs.stripe.com/api/idempotent_requests>
  - Stripe "Advanced error handling"(400·500 저장, 429는 멱등 계층 앞, `Idempotent-Replayed: true`, 409 Conflict, 장바구니 ID에서 키 파생, 원 요청을 고치면 새 키) <https://docs.stripe.com/error-low-level>
  - Stripe "API v2 overview" §Idempotency(30일, POST·DELETE, 실패 요청 재실행) <https://docs.stripe.com/api-v2-overview>
  - Google AIP-155 Request identification(`request_id`, UUID4, 이전 성공 응답 반환, 합리적 기간) <https://google.aip.dev/155>
  - nginx `ngx_http_proxy_module` `proxy_next_upstream`(`non_idempotent`) <https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_next_upstream>
  - OpenJDK jdk21u `src/java.net.http/share/classes/jdk/internal/net/http/MultiExchange.java` — `isIdempotentRequest`(GET·HEAD), `jdk.httpclient.enableAllMethodRetry`, `retryOnFailure`(`ConnectionExpiredException`·`ConnectException`), `retriedOnce` <https://github.com/openjdk/jdk21u>
- 실험 목록
  - 실험 A: JDK 21 HttpClient 메서드별 자동 재전송(기본 / `enableAllMethodRetry=true`) — `Retry05.java`, eclipse-temurin:21-jdk, 2회
  - 실험 B: S1~S6 키 없음·같은 키·시도마다 새 키·다른 본문·키 누락·동시 10요청 — `Idem05.java`, JDK 21.0.12 + PostgreSQL 17.11 전용 컨테이너, 3회
