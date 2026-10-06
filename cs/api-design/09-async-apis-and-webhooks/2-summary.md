# api-design/09-async-apis-and-webhooks — 웹훅·콜백·재전송·서명: 서버가 먼저 알려 주는 API의 계약 — 정리 (힌트)

## 해결하는 문제

보통의 API는 클라이언트가 묻고 서버가 답한다. 그런데 "결제가 끝났나?"처럼 **언제 바뀔지 모르는 상태**는 묻는 쪽이 계속 물어야 한다.

```text
  폴링(polling) — 클라이언트가 주기적으로 묻는다
  클라이언트 ──GET /payments/p1──> 서버   "아직"
  클라이언트 ──GET /payments/p1──> 서버   "아직"
  클라이언트 ──GET /payments/p1──> 서버   "아직"
  클라이언트 ──GET /payments/p1──> 서버   "완료"   ← 앞의 세 번은 헛걸음, 완료를 안 시점도 늦다

  웹훅(webhook) — 바뀐 쪽이 먼저 알린다
  서버 ──POST https://고객사/hooks {type: payment.succeeded}──> 고객사 서버
```

- *폴링*: 클라이언트가 같은 조회를 일정 간격으로 반복하는 방식.
- *웹훅*: 사건이 생긴 쪽이 상대가 미리 등록해 둔 URL로 HTTP 요청을 보내는 방식. Standard Webhooks 명세는 "HTTP 콜백의 흔한 이름"이며 서비스 API의 일부, 일종의 "역방향 API"라고 정의한다.
- *콜백 URL*: 요청 한 건에 "끝나면 여기로 알려 달라"고 URL을 실어 보내는 변형. 구독형 웹훅은 URL을 한 번 등록해 두고 사건마다 받는다.

쉬운 예: 택배 조회 페이지를 10분마다 새로 고치는 것(폴링)과, 택배사가 "배송 완료" 문자를 보내 주는 것(웹훅)의 차이다.

똑같은 구조다.\
다만 문자가 두 번 오거나, 늦게 오거나, 가짜 문자가 올 수 있다. 웹훅도 그렇다.

실무 예:
- PG(결제 대행사)가 결제 승인·취소를 가맹점 서버로 통지한다.
- GitHub가 push 이벤트를 CI 서버로 보낸다.
- 우리 회사가 플랫폼이 되어 입점사에게 "주문 생성" 이벤트를 보낸다.

웹훅을 여는 순간 보내는 쪽은 **남의 서버를 부르는 HTTP 클라이언트**가 되고, 받는 쪽은 **인터넷 누구나 부를 수 있는 엔드포인트**를 연다. 그래서 계약에 다음이 들어가야 한다.

| 계약 항목 | 정하지 않으면 |
|---|---|
| 성공의 뜻(무슨 응답이면 다 끝났나) | 보내는 쪽이 재전송을 멈출 시점을 모른다 |
| 재전송 정책(얼마나, 언제까지) | 받는 쪽이 중복·유실 범위를 모른다 |
| 진짜 보낸 사람 확인(서명) | 누구나 "결제 완료"를 위조해 보낼 수 있다 |
| 순서·중복 보장 수준 | 받는 쪽이 옛 이벤트로 새 상태를 덮는다 |

이 노트는 이 계약을 **설계하는 쪽**(주로 보내는 쪽)에서 본다. 받는 쪽의 구체적인 사례 풀이(dedup 트랜잭션, 상태 전이 표, "200의 뜻")는 사례 [26-case-delivery-webhook](../26-case-delivery-webhook/2-summary.md)에 있다.

## 동작·원리

### 1. 비동기 API의 세 모양

```text
  (a) 폴링            클라이언트 ──묻기──> 서버        (반복)
  (b) 웹훅/콜백        서버 ──알리기──> 클라이언트 서버   (사건마다)
  (c) 작업 자원        클라이언트 ──POST──> 서버 ──202 + /operations/7──>
                     클라이언트 ──GET /operations/7──> 서버  (끝날 때까지)
```

- (c)는 "내가 시킨 긴 일"의 진행을 보는 모양이다. [13-long-running-operations](../13-long-running-operations/2-summary.md)에서 다룬다.
- (b)는 "내가 시키지 않은 사건"도 받는다(분쟁 접수, 구독 갱신 등).
- 실무에서는 섞어 쓴다. 웹훅으로 "바뀌었다"를 알리고, 받는 쪽이 API로 최신 상태를 다시 조회한다(아래 5절 thin payload).

### 2. 전달 한 번 — Standard Webhooks 헤더

```text
  보내는 쪽 워커                                        받는 쪽 엔드포인트
  ─────────────                                        ──────────────────
  POST /hooks
    webhook-id: msg_2KWPBgLlAfxdpx2AI54pPJ85f4W   ──>  ① 타임스탬프가 허용 창 안인가
    webhook-timestamp: 1674087231                      ② 서명이 맞나 (원문 바이트로)
    webhook-signature: v1,K5oZ...pI4=                  ③ webhook-id를 이미 처리했나
    {"type":"contact.created", ...}                    ④ 큐·DB에 넣는다
                                                <──    ⑤ 2xx
  2xx면 끝. 그 밖의 응답·타임아웃이면 재전송 예약.
```

- *Standard Webhooks*: 웹훅 형식을 업계 공통으로 맞추자는 공개 명세다(github.com/standard-webhooks, 명세 파일 마지막 커밋 2025-02-16 확인). IETF RFC가 아니라 커뮤니티 명세다.
- 헤더 셋(명세 「Webhook headers」)
  - *webhook-id*: 메시지 고유 ID. 재전송해도 같다 → 받는 쪽의 멱등 키.
  - *webhook-timestamp*: 이 **시도**의 유닉스 초. 재전송마다 새로 찍는다. 이벤트가 일어난 시각(본문 `timestamp`)과 다르다.
  - *webhook-signature*: 서명 목록(공백 구분). 키 회전 중에는 옛 키·새 키 서명을 둘 다 싣는다.
- 성공 판정(명세 「Delivery success and failure」): 2xx만 성공. 3xx는 실패(리다이렉트를 따르지 말고 URL을 고치라), `410 Gone`은 "더 받지 않겠다" → 엔드포인트 비활성화, `429`·`502`·`504`는 속도를 줄이라는 신호, 응답에 `retry-after`가 있으면 다음 시도 시각에 반영.
- 요청 타임아웃 권고: 15~30초(명세 「Request timeouts」).

### 3. 재전송 시간축

명세가 든 예시 일정(「Deliverability and reliability」):

```text
  시도:  1   2    3     4      5     6     7      8      9      10
  지연:  0   5s   5m    30m    2h    5h    10h    14h    20h    24h
  누적: 00:00:00 ─────────────────────────────────────────────> 75:35:05 (약 3.1일)
         ↑ 받는 쪽이 3일 넘게 죽어 있으면 이 메시지는 자동으로는 더 오지 않는다
```

- 명세 권고: 며칠에 걸친 지수 백오프 + 무작위 지터. 오래 계속 실패하면 다른 경로(이메일 등)로 알리고 엔드포인트를 끄는 것을 권한다.
- Stripe(문서 「Automatic retries」, 2026-10-04 확인): 라이브 모드에서 최대 3일, 지수 백오프. 샌드박스는 몇 시간 동안 3회. 대시보드 수동 재전송은 이벤트 생성 후 15일, CLI는 30일까지.
- 결론: **웹훅은 기간이 정해진 재시도다.** 그 기간을 넘기면 유실된다. 그래서 보내는 쪽은 실패 목록·수동 재전송(명세 「Visibility into failures and manual retries」)을, 받는 쪽은 대사(조회 API로 맞춰 보기)를 둔다.

### 4. 서명 — 무엇을, 어떻게 서명하나

```text
  서명 대상 = webhook-id + "." + webhook-timestamp + "." + 본문 원문 바이트
              msg_2KW...  .  1674087231          .  {"type":"contact.created",...}

  대칭(v1)  : HMAC-SHA256(공유 비밀, 서명 대상) → base64   비밀 형식 whsec_<base64>
  비대칭(v1a): ed25519 개인키로 서명, 받는 쪽은 공개키로 검증     whsk_ / whpk_
```

- *HMAC*: 비밀 키와 메시지를 함께 해시해서 "비밀을 아는 쪽이 이 내용을 보냈다"를 증명하는 값.
- id와 타임스탬프까지 서명하는 이유: 본문만 서명하면 공격자가 캡처한 요청의 타임스탬프 헤더만 바꿔 다시 보낼 수 있다. 타임스탬프가 서명 안에 있으면 바꾸는 순간 서명이 깨진다.
- 받는 쪽 검증 때 지킬 것(명세 「Verifying signatures」 — 명세는 항목만 들고 검사 순서는 정하지 않는다. 위 그림·실험 코드는 타임스탬프 → 서명 → id 순으로 했다)
  - 상수 시간 비교로 서명을 비교한다. 아니면 타이밍 공격으로 서명을 한 바이트씩 맞혀 갈 수 있다.
  - 타임스탬프가 허용 오차 안인지 본다 → **재전송(replay) 공격** 차단.
  - webhook-id를 멱등 키로 저장한다(명세 예: "redis에 5분" — 예시다. 허용 창이 ±라서 보관 기간은 허용 오차의 2배 이상이 안전하다. 아래 실험 E).
  - *재전송 공격*: 정상 요청을 엿들어 그대로 다시 보내는 공격. 서명은 진짜라서 서명만으로는 못 막는다.
- 허용 오차 기본값: Standard Webhooks Java 참조 라이브러리 `TOLERANCE_IN_SECONDS = 5 * 60`(WebhookBase.java — `now - 300`보다 오래된 것과 `now + 300`보다 미래인 것을 둘 다 거부한다. 창의 폭은 10분), Stripe 공식 라이브러리 기본 5분. Stripe 문서는 오차 0이 "최신성 검사를 끈다"는 뜻이니 쓰지 말라고 적는다.
- 본문 원문이 중요하다. 명세는 "본문을 JSON으로 파싱했다 다시 직렬화하면 공백 하나로도 서명이 깨진다"를 **매우 흔한 실패**로 꼽는다. Stripe 문서도 "raw body를 건드리지 말라"고 적는다.
- 대칭 vs 비대칭: 명세는 비대칭을 우선 권한다. 대칭 비밀은 받는 쪽도 들고 있어서, 받는 쪽 유출이 곧 위조 능력이 되기 때문이다. 대칭은 빠르고 단순하다.

### 실험: 서명·재전송 창·중복·순서

JDK만으로 명세의 서명 방식을 구현하고 다섯 가지 공격·사고를 넣어 본다. 코드 핵심:

```java
static String sign(byte[] key, String id, long ts, String body) throws Exception {
    Mac mac = Mac.getInstance("HmacSHA256");
    mac.init(new SecretKeySpec(key, "HmacSHA256"));
    byte[] sig = mac.doFinal((id + "." + ts + "." + body).getBytes(StandardCharsets.UTF_8));
    return "v1," + Base64.getEncoder().encodeToString(sig);
}
static String verify(byte[] key, String id, long ts, String sigHeader, String rawBody, long now) throws Exception {
    if (Math.abs(now - ts) > 300) return "REJECT(timestamp " + (now - ts) + "s 차이)";
    String expected = sign(key, id, ts, rawBody).split(",")[1];
    boolean ok = false;
    for (String s : sigHeader.split(" ")) {                       // 키 회전: 서명 여러 개
        String[] p = s.split(",", 2);
        if (p[0].equals("v1") && MessageDigest.isEqual(p[1].getBytes(), expected.getBytes())) ok = true;
    }
    if (!ok) return "REJECT(signature)";
    if (!seen.add(id)) return "DUPLICATE(이미 처리한 webhook-id)";
    return "ACCEPT";
}
```

- A는 명세 저장소 Python 테스트(`test_sign_function`)의 시험 벡터와 같은 값이 나오는지 본다.
- C는 같은 주문의 이벤트가 `seq` 3 → 1 → 2 → 2(중복) 순서로 도착할 때를 본다.

(실험, JDK 21.0.12 eclipse-temurin, `--network none`, 2026-10-04)

```text
A 시험 벡터: v1,g0hM9SsE+OTPJTGt/tmIKtSyZlE3uFJELVlNIOLJ1OE=  일치=true
B1 정상                 : ACCEPT
B2 같은 요청 재전송      : DUPLICATE(이미 처리한 webhook-id)
B3 본문 위조(금액 1000→1): REJECT(signature)
B4 파싱 후 재직렬화 본문 : REJECT(signature)
B5 10분 전 캡처 재전송   : REJECT(timestamp 600s 차이)
B6 서명 모르는 공격자    : REJECT(signature)
B7 회전 중(옛+새 서명)   : ACCEPT
C 도착 순서: e3(SHIPPED) e1(CREATED) e2(PAID) e2(PAID)
C 그냥 덮어쓰기 최종 = PAID
C id 중복 제거 + seq 비교 최종 = SHIPPED (적용 1, 중복 1, 오래됨 2)
```

- 관찰
  - B4: 내용은 같은데 공백만 다른 본문이 거부됐다. 프레임워크가 본문을 객체로 바꾼 뒤 검증하면 이 일이 생긴다.
  - B5: 서명은 진짜지만 타임스탬프 창 밖이라 거부됐다. 창 안에서 다시 보내면 B2처럼 id 중복으로 걸린다. 그래서 id 보관 기간은 허용 창 전체 폭(허용 오차 × 2)보다 길어야 한다(적용 2의 실험 E).
  - C: 도착 순서대로 덮으면 이미 배송된 주문이 `PAID`로 되돌아간다. id 중복 제거만으로는 못 막는다. 서로 **다른** 이벤트의 순서 문제라서다. 이벤트에 단조 증가 버전(`seq`)을 실어 주면 받는 쪽이 비교할 수 있다.

### 5. 순서·중복 — 계약에 무엇을 적나

```text
  보내는 쪽이 줄 수 있는 것                받는 쪽이 해야 하는 것
  ────────────────────────                ──────────────────────
  webhook-id (재전송해도 같음)      ──>   id로 중복 제거
  자원 버전·seq (단조 증가)         ──>   저장된 버전보다 작거나 같으면 버림
  thin payload (id만)              ──>   API로 최신 상태를 조회해 반영
  "순서를 보장하지 않는다"고 명시    ──>   순서에 기대지 않는 처리
```

- Stripe 문서 「Event ordering」: 생성 순서대로 전달을 보장하지 않는다고 적는다. snapshot 이벤트의 `created`는 초 단위라 여러 이벤트가 같은 값을 가질 수 있으니 순서·중복 판정에 쓰지 말고 이벤트 ID를 쓰라고 한다. 같은 사건에 Event 객체가 두 개 생기는 경우도 있어 `data.object`의 ID + 이벤트 type으로 구분하라고 한다.
- 이벤트 시각(`occurred_at`)으로 순서를 판단하면 보내는 쪽 시계 정밀도·동률 문제가 남는다. 사례 26의 결론과 같다 — 받는 쪽 상태 전이 규칙이 더 견고하다.
- **thin vs full payload**(명세 「"Thin" vs "full" payloads」)
  - *full payload*: 바뀐 객체 전체를 싣는다. 받는 쪽이 추가 조회 없이 처리한다.
  - *thin payload*: ID와 바뀐 사실만 싣는다. 받는 쪽이 API로 최신을 읽는다.
  - 명세가 꼽는 thin의 장점: 데이터가 적다, 나중에 full로 바꿀 수 있지만 반대는 어렵다, 데이터 접근을 조회 API의 권한·감사 로그로 통제할 수 있다.
  - 순서 관점의 장점(해석): 받는 쪽이 매번 최신을 조회하므로 늦게 온 알림이 옛 상태를 실어 오지 않는다. 대가는 조회 호출 증가다.
  - Stripe도 2026-10 문서 기준 snapshot 이벤트와 thin 이벤트를 나눠 제공한다(thin은 `fetchRelatedObject()`로 최신 객체를 읽는다).
- 본문 크기: 명세는 보통 20kb 아래로 작게 두고, 큰 데이터는 링크로 넘기라고 권한다.

### 6. 보내는 쪽의 보안 — SSRF

```text
  고객이 등록한 웹훅 URL:  http://169.254.169.254/latest/meta-data/   ← 클라우드 메타데이터
                          http://10.0.3.7:9200/_all                  ← 내부 검색 클러스터
  보내는 쪽 워커가 그대로 POST하면 → 내부망 요청을 대신 해 주는 꼴
```

- *SSRF(Server-Side Request Forgery)*: 공격자가 고른 URL로 서버가 대신 요청하게 만드는 공격.
- 명세 「Server side request forgery」: 웹훅은 고객이 아무 URL이나 등록하므로 특히 취약하다. 대책은 내부 IP를 거르는 전용 프록시(예: Stripe smokescreen)를 거치게 하고, 워커를 내부 서비스에 닿지 않는 서브넷에 두는 것.
- 등록할 때 한 번 검사하는 것으로는 부족하다(해석): DNS가 나중에 내부 IP로 바뀔 수 있다. 그래서 명세는 **보낼 때** 거르는 프록시를 권한다.

## 쓰이는 자료구조·알고리즘

- **HMAC-SHA256 서명 + 상수 시간 비교** — JDK 21 `MessageDigest.isEqual`의 @implNote: 첫 인자의 모든 바이트를 검사하고, 걸리는 시간은 첫 인자 길이에만 달려 있다(내용과 무관). `String.equals`는 처음 다른 글자에서 멈춘다. 서명 원리는 security 영역 [05-mac-and-hmac](../../security/05-mac-and-hmac/2-summary.md).
- **재전송 일정 = 다음 시도 시각 순 우선순위 큐** — 실패한 전달을 `next_attempt_at`으로 정렬해 꺼낸다(최소 힙 또는 DB 인덱스) → [data-structure/07-heap](../../data-structure/07-heap/2-summary.md). 간격은 지수 백오프 + 지터 → [reliability/06-retry-backoff-jitter](../../reliability/06-retry-backoff-jitter/2-summary.md).
- **중복 억제 집합(TTL)** — webhook-id → 처리 결과. 해시 셋 + 만료. 보관 기간 ≥ 타임스탬프 허용 창 전체 폭(±오차라서 오차 × 2), 그리고 받는 쪽이 원하면 재전송 기간까지 → [reliability/13-idempotency](../../reliability/13-idempotency/2-summary.md).
- **단조 버전 비교** — 저장된 `version`보다 큰 이벤트만 반영. DB에서는 조건부 UPDATE(`WHERE version < :v`) 한 줄.
- **서명 목록(키 회전)** — 헤더에 서명을 여러 개 싣고 하나라도 맞으면 통과. 옛 키는 기한을 두고 뺀다(Stripe는 최대 24시간 동안 옛 비밀을 유지할 수 있다).

## 적용 — 풀어나가는 법

### 1. 보내는 쪽(웹훅 제공자) 설계 순서

1. 이벤트 종류를 정한다. 명세 권고: `user.created`처럼 점으로 구분한 계층 이름, 종류마다 스키마 고정, 받는 쪽이 종류를 골라 구독.
2. 성공의 뜻을 문서에 적는다: "2xx = 받았다. 처리 결과는 묻지 않는다."
3. 재전송 일정·최대 기간·끄는 조건(`410`, N일 연속 실패)을 문서에 적는다.
4. 서명 방식(대칭/비대칭), 비밀 형식, 허용 오차 권고, 키 회전 절차를 적는다.
5. 순서 보장 수준을 적는다("보장하지 않는다" + 버전 필드 또는 thin payload).
6. 실패 목록 조회·수동 재전송·엔드포인트 관리 API를 준다.
7. 워커는 내부망에 닿지 않게 둔다(SSRF).

전달 기록은 DB 테이블 하나로 시작할 수 있다(예시 스키마):

```sql
CREATE TABLE webhook_delivery (
  msg_id          text        NOT NULL,      -- webhook-id, 재전송해도 같다
  endpoint_id     bigint      NOT NULL,
  attempt         int         NOT NULL DEFAULT 0,
  next_attempt_at timestamptz NOT NULL,
  status          text        NOT NULL,      -- PENDING / DELIVERED / FAILED / DISABLED
  last_status     int,                       -- 마지막 HTTP 상태
  PRIMARY KEY (msg_id, endpoint_id)
);
CREATE INDEX ON webhook_delivery (next_attempt_at) WHERE status = 'PENDING';
```

- 이벤트를 이 표에 넣는 일은 업무 트랜잭션과 같이 커밋해야 "주문은 생겼는데 웹훅은 안 나감"이 없다. 이것이 outbox다 → [distributed/16-outbox-and-dual-write](../../distributed/16-outbox-and-dual-write/2-summary.md).

전달 워커의 응답 분기(Java, JDK `HttpClient`):

```java
HttpResponse<Void> r = client.send(signedRequest(d), HttpResponse.BodyHandlers.discarding()); // 요청 타임아웃 15~30초
int s = r.statusCode();
if (s / 100 == 2)      markDelivered(d);
else if (s == 410)     disableEndpoint(d.endpointId());               // 받는 쪽이 그만 받겠다고 함
else {
    Duration wait = r.headers().firstValue("Retry-After").map(v -> Duration.ofSeconds(Long.parseLong(v)))
                     .orElse(backoffWithJitter(d.attempt()));          // 3xx·4xx·5xx 모두 실패로 보고 재예약
    if (d.attempt() + 1 >= MAX_ATTEMPTS) markFailedAndNotify(d);      // 실패 목록에 남기고 다른 경로로 알림
    else reschedule(d, Instant.now().plus(wait));
}
```

- `Retry-After`가 HTTP-date 형식일 수도 있다(RFC 9110 §10.2.3). 위 코드는 초 형식만 처리한 단순판이다.
- 타임아웃·연결 실패(`IOException`)도 재예약 분기로 보낸다.

### 2. 받는 쪽 엔드포인트 (Java, `com.sun.net.httpserver`)

```java
server.createContext("/hooks/acme", ex -> {
    byte[] raw = ex.getRequestBody().readAllBytes();               // ① 파싱 전에 원문 바이트를 확보
    String id = ex.getRequestHeaders().getFirst("webhook-id");
    long ts = Long.parseLong(ex.getRequestHeaders().getFirst("webhook-timestamp"));
    String sig = ex.getRequestHeaders().getFirst("webhook-signature");
    String v = verifySignature(key, id, ts, sig, new String(raw, UTF_8), Instant.now().getEpochSecond()); // 창·서명만 본다(id 표시 없음)
    if (v.startsWith("REJECT")) { reply(ex, 401); return; }         // ② 위조·재전송: 4xx, 로그·지표
    switch (inbox.insertIfAbsent(id, raw)) {                        // ③④ 중복 판정 + 저장을 한 번에 (INSERT … webhook_id UNIQUE)
        case DUPLICATE -> reply(ex, 200);   // 이미 저장됨: 성공으로 답해 재전송을 멈춘다
        case FAILED    -> reply(ex, 503);   // 저장 실패: id 표시도 남지 않았으니 재전송이 다시 들어온다
        case INSERTED  -> reply(ex, 200);   // ⑤ 저장 성공 = 2xx
    }
});
```

- 실험 코드의 `verify`처럼 id를 **먼저** 표시하고 그 뒤 저장하면 안 된다. 저장이 실패해 503을 줘도, 같은 id의 재전송이 DUPLICATE → 200으로 삼켜져 이벤트가 사라진다. 중복 표시는 저장 성공과 같은 단위여야 한다.

(실험 D·E, `Wh2.java`, JDK 21.0.12 eclipse-temurin, `--network none`, 2026-10-04 — D는 첫 시도에서 큐 저장 실패 후 같은 id 재전송, E는 ts로 서명된 요청이 보내는 쪽 시계가 앞서 ts-290초에 처음 도착하고 490초 뒤 다시 온 경우)

```text
D 나쁜 순서(표시→저장): 1차 503, 재전송 200 → 저장된 건수 0
D 고친 순서(저장=표시): 1차 503, 재전송 200, 한 번 더 200 → 저장된 건수 1
E 보관 300초: 첫 수신(now=ts-290) ACCEPT, 490초 뒤 재전송(now=ts+200) ACCEPT
E 보관 600초: 첫 수신(now=ts-290) ACCEPT, 490초 뒤 재전송(now=ts+200) DUPLICATE
```

- D: 나쁜 순서에서는 보내는 쪽이 200을 받고 재전송을 멈췄는데 저장된 이벤트는 0건이다.
- E: 서명된 요청은 [ts-300, ts+300] 어느 때나 창 안이다. id를 5분만 기억하면 창이 끝나기 전에 잊어버려 같은 요청이 다시 ACCEPT된다. 10분(허용 오차 × 2)이면 막힌다.

- 무거운 처리는 큐 뒤 워커가 한다. Stripe 문서도 복잡한 로직 전에 2xx를 빨리 돌려주고, 비동기 큐로 처리하라고 권한다.
- 워커 쪽 중복 제거·상태 전이·"200의 뜻"은 사례 [26-case-delivery-webhook](../26-case-delivery-webhook/2-summary.md)에 자세히 있다.
- 실험의 `seen` 집합은 메모리라 서버가 여러 대면 못 막는다. 실무에서는 DB 유일 제약(위 `inbox`)으로 저장과 함께 하거나, Redis `SET NX EX`를 쓰면 저장 실패 때 그 키를 지운다.

### 3. 진단

- 서명을 직접 만들어 보내 본다(키는 예시 값):

```bash
SECRET_B64=MfKQ9r8GKYqrTwjUPD8ILPZIo2LaLaSw; ID=msg_test1; TS=$(date +%s); BODY='{"type":"ping"}'
SIG=$(printf '%s.%s.%s' "$ID" "$TS" "$BODY" \
  | openssl dgst -sha256 -mac HMAC -macopt hexkey:$(echo -n $SECRET_B64 | base64 -d | xxd -p -c 256) -binary | base64)
curl -i -X POST http://localhost:8080/hooks/acme -H "webhook-id: $ID" -H "webhook-timestamp: $TS" \
  -H "webhook-signature: v1,$SIG" --data-binary "$BODY"
```

- 이 `openssl` 줄에 위 시험 벡터(`msg_p5jXN8AQM9LWM0D4loKWxJek`, `1614265330`, `{"test": 2432232314}`)를 넣으면 `g0hM9SsE+OTPJTGt/tmIKtSyZlE3uFJELVlNIOLJ1OE=`가 나온다(OpenSSL 3.0.13, 2026-10-04 확인). `--data-binary`는 본문 바이트를 바꾸지 않고 보낸다.

- 지표
  - 보내는 쪽: 엔드포인트별 실패율·연속 실패 횟수, 전달 지연(이벤트 생성 → 2xx), 대기 중 재전송 수.
  - 받는 쪽: 서명 실패 수(0이 아니면 공격이거나 비밀·직렬화 문제), 타임스탬프 거부 수(시계 문제), 중복 비율, 마지막 수신 시각(부재 감지).

## 장애 시나리오와 대처

### 1. 서명 검증 없음 → 위조 이벤트로 주문 확정 (⚠ 커리큘럼)

- 현상: 결제하지 않은 주문이 "결제 완료"로 바뀌고 상품이 출고됐다.
- 보이는 형태: 웹훅 로그에 PG가 쓰지 않는 IP에서 온 `payment.succeeded`. PG 대시보드에는 그 결제가 없다.
- 원인: 웹훅 URL이 노출됐고(앱 번들·문서·로그), 받는 쪽이 본문만 믿었다.
- 대처: 서명 검증 + 타임스탬프 창 + id 중복 제거를 파싱 전에 한다. 금액처럼 중요한 값은 thin 방식으로 API를 다시 조회해 확인한다. Stripe 문서는 서명 검증에 더해 발신 IP 허용 목록도 쓰라고 권한다.

### 2. 순서 역전·중복 전달 → 상태 역행 (⚠ 커리큘럼)

- 현상: 배송 완료였던 주문이 "결제 완료"로 돌아갔다. 같은 알림이 두 번 갔다.
- 보이는 형태: 상태 이력에 `SHIPPED` 뒤 `PAID`. 같은 webhook-id 처리 로그 2건.
- 원인: 도착 순서대로 덮어썼다(실험 C의 "그냥 덮어쓰기 최종 = PAID"). 중복 제거가 없거나 메모리에만 있었다.
- 대처: 보내는 쪽은 버전 필드나 thin payload를 주고 "순서 보장 없음"을 문서에 적는다. 받는 쪽은 id 중복 제거 + 버전 비교 또는 상태 전이 규칙을 둔다 → 사례 [26](../26-case-delivery-webhook/2-summary.md)의 장애 1·2.

### 3. 배포 뒤 웹훅 서명 검증이 전부 실패

- 현상: 프레임워크 업그레이드 뒤 서명 실패율이 100%가 됐다. 보내는 쪽은 계속 재전송한다.
- 보이는 형태: `REJECT(signature)`만 찍힌다. 같은 요청을 원문 그대로 다시 계산하면 맞는다.
- 원인: 미들웨어가 본문을 JSON으로 파싱한 뒤 다시 직렬화한 문자열로 검증했다(실험 B4). 또는 문자셋 변환, 줄바꿈 정규화.
- 대처: 웹훅 경로만 원문 바이트를 그대로 받게 한다. 실패를 4xx로 돌려주므로 보내는 쪽 재전송 기간 안에 고치면 유실은 없다. 기간을 넘겼다면 보내는 쪽의 수동 재전송을 쓴다.

### 4. 받는 쪽이 사흘 죽어 있었다 → 일부 이벤트 영구 유실

- 현상: 장애 복구 뒤에도 그 기간의 결제 일부가 "대기"에 남아 있다.
- 보이는 형태: 보내는 쪽 대시보드에 "Failed" 이벤트. 엔드포인트가 비활성화됐다는 메일.
- 원인: 재전송 기간(명세 예시 약 3.1일, Stripe 라이브 3일)을 넘겼다. 연속 실패로 엔드포인트가 꺼졌을 수도 있다.
- 대처: 엔드포인트를 다시 켜고 실패 목록을 수동 재전송한다. 대사 작업(조회 API로 "대기" 주문의 실제 상태 확인)을 정기적으로 돌린다. 웹훅만으로 정합성을 보장하려 하지 않는다.

### 5. 보내는 쪽 — 웹훅 워커가 내부 시스템을 찔렀다 (SSRF)

- 현상: 보안팀이 웹훅 워커에서 클라우드 메타데이터 주소로 나간 요청을 발견했다.
- 보이는 형태: 등록된 엔드포인트 URL이 사설 IP·링크 로컬 주소이거나, 등록 뒤 DNS가 내부 IP로 바뀌었다.
- 원인: 고객이 준 URL을 검사 없이 그대로 불렀다.
- 대처: 내부 대역을 막는 송신 전용 프록시를 거치고, 워커를 격리된 서브넷에 둔다(명세 권고). 리다이렉트를 따르지 않는다(명세: 3xx는 실패).

### 6. 정상 웹훅이 "timestamp" 사유로 거부된다

- 현상: 특정 서버 한 대에서만 웹훅이 거부된다.
- 보이는 형태: `REJECT(timestamp 400s 차이)`처럼 일정한 차이.
- 원인: 그 서버 시계가 어긋났다. 허용 창이 5분이면 몇 분 어긋남도 바로 걸린다.
- 대처: NTP로 시계를 맞춘다(Stripe 문서도 NTP를 권한다). 창을 0으로 두거나 끄지 않는다.

## 핵심 문장

- 웹훅은 "역방향 API"다. 보내는 쪽은 성공의 뜻(2xx), 재전송 일정·기간, 서명, 순서 보장 수준을 계약으로 적어야 한다.
- 서명은 id·타임스탬프·본문 원문을 함께 덮어야 하고, 받는 쪽은 파싱 전에 타임스탬프 창 → 서명(상수 시간 비교) → id 중복 제거를 검사한다.
- 서명이 진짜여도 재전송 공격과 중복은 남는다. 타임스탬프 창과 id 저장이 그 몫이다.
- id 중복 제거는 같은 이벤트만 거른다. 다른 이벤트 사이의 순서 역전은 버전 비교·상태 전이 규칙·thin payload로 막는다.
- 재전송은 기간이 있다. 그 뒤의 유실은 수동 재전송과 대사로 메운다.
- 고객이 URL을 등록하는 순간 보내는 쪽 워커는 SSRF 표적이 된다.

## 관련 주제·근거

- 선행
  - [05-idempotency-keys](../05-idempotency-keys/2-summary.md) — 멱등 키(이 노트의 webhook-id가 받는 쪽의 멱등 키).
  - [security 05-mac-and-hmac](../../security/05-mac-and-hmac/2-summary.md)
  - [reliability/13-idempotency](../../reliability/13-idempotency/2-summary.md) — 키 저장소·결과 재생
- 사례
  - [26-case-delivery-webhook](../26-case-delivery-webhook/2-summary.md) — 받는 쪽 사례: dedup 트랜잭션, 상태 전이 표, 200의 뜻, 저빈도 폴링 보정
- 후속
  - [10-notification-delivery-pipeline](../10-notification-delivery-pipeline/2-summary.md) — 같은 "outbox → 큐 → 외부 전달" 구조를 이메일·SMS·푸시에 적용
  - [13-long-running-operations](../13-long-running-operations/2-summary.md) — 내가 시킨 긴 일은 작업 자원 + 폴링(또는 완료 웹훅)
  - [14-rate-limit-and-quota-contracts](../14-rate-limit-and-quota-contracts/2-summary.md) — 받는 쪽이 429·Retry-After로 속도를 조절할 때
  - [distributed/16-outbox-and-dual-write](../../distributed/16-outbox-and-dual-write/2-summary.md) — 이벤트 기록과 업무 커밋을 묶기
  - [reliability/06-retry-backoff-jitter](../../reliability/06-retry-backoff-jitter/2-summary.md) — 재전송 간격
  - [network/33-http-semantics](../../network/33-http-semantics/2-summary.md) — 상태 코드·메서드 의미
- 문서
  - Standard Webhooks 명세 <https://github.com/standard-webhooks/standard-webhooks/blob/main/spec/standard-webhooks.md> (2026-10-04 열람, 명세 파일 마지막 커밋 2025-02-16) — 헤더, 서명 대상, v1/v1a, 키 회전, 재전송 일정 예시, 2xx/3xx/410/429 처리, 타임아웃 15~30초, SSRF, thin/full payload
  - Standard Webhooks Java 참조 라이브러리 `libraries/java/src/main/java/com/standardwebhooks/WebhookBase.java` — `TOLERANCE_IN_SECONDS = 5 * 60`
  - Stripe "Receive Stripe events in your webhook endpoint" <https://docs.stripe.com/webhooks> (2026-10-04 열람) — 3일 재시도, 순서 보장 없음, `Stripe-Signature: t=…,v1=…`, 라이브러리 기본 허용 오차 5분, raw body, 비밀 회전 최대 24시간, 수동 재전송 15일/30일
  - RFC 9110 §10.2.3 Retry-After <https://www.rfc-editor.org/rfc/rfc9110>
  - OWASP API Security Top 10 2023 API7 Server Side Request Forgery <https://owasp.org/API-Security/editions/2023/en/0xa7-server-side-request-forgery/>
- 실험 목록
  - 서명·재전송 창·중복·순서(A 시험 벡터, B1~B7, C) — `Wh.java`, eclipse-temurin:21-jdk(JDK 21.0.12), `--network none`, 1회(결정적 출력)
  - 중복 표시와 저장의 원자성(D), id 보관 기간 vs ±허용 창(E) — `Wh2.java`, 같은 환경, 1회(결정적 출력)
