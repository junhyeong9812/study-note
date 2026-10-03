# api-design/10-notification-delivery-pipeline — 알림 발송 파이프라인: outbox → 큐 → 공급자, 멱등 발송 키, 실패 분류, 억제 목록, 야간 제한, 푸시 토큰 — 정리 (힌트)

## 해결하는 문제

"주문이 끝나면 고객에게 문자를 보낸다." 코드로는 한 줄이다.

```java
orderRepository.save(order);
smsClient.send(user.phone(), "주문 완료");   // 이 한 줄이 문제의 시작
```

이 한 줄이 실제 서비스에서 만드는 사고는 다섯 가지다.

```text
  (1) 중복     공급자 응답이 타임아웃 → 재시도 → 같은 문자 3통
  (2) 유령     문자를 보낸 뒤 트랜잭션이 롤백 → 주문은 없는데 "주문 완료" 문자
  (3) 평판     없는 메일 주소(하드 바운스)에 계속 발송 → 발송 도메인 평판 하락 → 정상 메일까지 스팸함
  (4) 죽은 토큰 앱을 지운 기기의 푸시 토큰에 계속 발송 → 실패율 상승, 공급자 할당량 낭비
  (5) 법·사용자 밤 11시 광고 푸시 → 수신자 별도 동의가 없으면 법 위반(한국 정보통신망법 제50조 ③)
```

- *알림 공급자(provider)*: 실제로 문자·메일·푸시를 단말까지 보내 주는 외부 서비스. SMS 대행사, 메일 발송 대행사(ESP), FCM(Firebase Cloud Messaging)·APNs(Apple Push Notification service) 등.
- *하드 바운스*: 주소 자체가 없어서 영구히 실패한 메일. SMTP `5.1.1`(없는 사용자) 같은 응답이다 → [network/51-email-delivery-and-authentication](../../network/51-email-delivery-and-authentication/2-summary.md).

쉬운 예: 택배 발송 창구다.
- 접수(주문 확정)와 발송(트럭 출발)을 나눈다. 접수가 취소되면 송장도 같이 찢는다.
- 송장 번호(발송 키)가 같으면 두 번 부치지 않는다.
- "수취인 불명"으로 돌아온 주소는 주소록에 표시해 다음부터 안 보낸다.

똑같은 구조다. 업무 트랜잭션과 발송을 **outbox**로 나누고, **멱등 발송 키**로 중복을 막고, **억제 목록**으로 죽은 주소를 거른다.

실무 예: 주문·결제·배송 알림, 비밀번호 재설정 메일, 마케팅 푸시, 2단계 인증 문자.

## 동작·원리

### 1. 전체 그림

```text
   업무 트랜잭션 (한 DB 커밋)
  ┌──────────────────────────────────────┐
  │ INSERT orders ...                    │
  │ INSERT notification_outbox           │   ← 발송 "의도"만 기록
  │   (notification_key UNIQUE, ...)     │
  └──────────────────────────────────────┘
                 │ 커밋된 것만
                 ▼
   릴레이 ──> 큐 ──> 발송 워커 ─────────────────────> 공급자 (SMS·ESP·FCM·APNs)
                       │ ① 억제 목록·선호·야간 확인         │
                       │ ② 멱등 키를 실어 전송              │
                       │ ③ 응답 분류                       ▼
                       │    성공 ─────> 기록          단말·메일함
                       │    일시 실패 ─> 백오프 재큐
                       │    영구 실패 ─> 억제 목록·토큰 삭제, 재시도 안 함
                       ▼
                 발송 이력 (notification_key별 상태)
```

- *outbox*: 업무 데이터와 "보낼 메시지"를 같은 트랜잭션으로 같은 DB에 쓰고, 별도 릴레이가 커밋된 행만 꺼내 보내는 패턴 → [distributed/16-outbox-and-dual-write](../../distributed/16-outbox-and-dual-write/2-summary.md).
- *릴레이*: outbox 표를 읽어(폴링 또는 CDC) 큐로 옮기는 프로세스.
- 이 그림은 [09-async-apis-and-webhooks](../09-async-apis-and-webhooks/2-summary.md)의 웹훅 송신과 같은 뼈대다. 받는 쪽이 고객 서버가 아니라 알림 공급자일 뿐이다.

### 2. 멱등 발송 키 — 어디서 만들고 어디까지 지키나

```text
  notification_key = "<사건 종류>:<사건 ID>:<수신자>:<채널>"
  예) order-completed:o2:user1:sms

  지키는 곳                       막는 중복
  ───────────────────            ──────────────────────────────────────
  outbox UNIQUE(notification_key) 같은 사건을 코드가 두 번 적재
  발송 이력 상태(SENT)             릴레이·워커가 같은 행을 다시 집음 (전송 전 확인)
  공급자 멱등 키(지원할 때만)        "공급자는 받았는데 우리 쪽 응답만 유실" → 재시도
```

- 키는 **사건에서** 만든다. 재시도할 때마다 새로 만들면 키가 아무것도 막지 못한다(사례 26의 Grab 사고와 같은 모양 → [26-case-delivery-webhook](../26-case-delivery-webhook/2-summary.md) 「실패 사례」).
- 마지막 줄이 핵심이다. 우리 DB만으로는 "공급자가 받았는지 모른다"는 구간을 닫을 수 없다.
  - 공급자가 멱등 키(또는 요청 ID 중복 거부)를 지원하면 그 키를 실어 보낸다.
  - 지원하지 않으면 재시도 = 중복 가능이다. 이때는 재시도 횟수·간격으로 중복 확률을 줄이는 수밖에 없다. 공급자 문서에서 지원 여부를 확인한다.
- 수신자의 단말 쪽에도 중복을 줄이는 장치가 있다(예: FCM의 collapse 키). 다만 FCM 문서는 collapsible 메시지를 "아직 기기에 전달되지 않았다면 새 메시지로 대체될 수 있는 메시지"로 정의한다. 이미 전달된 알림은 거르지 못하는 "덮어쓰기" 의미라 발송 키를 대신하지 않는다(Firebase "Non-collapsible and collapsible messages", 2026-10-04 열람).

### 3. 실패를 셋으로 나눈다

| 분류 | 예(공급자 문서) | 처리 |
|---|---|---|
| 성공 | 2xx | 이력 SENT |
| 일시 실패 | FCM `UNAVAILABLE`(503), `INTERNAL`(500), `QUOTA_EXCEEDED`(429), SMTP `4yz`, 타임아웃 | 백오프 + 지터로 재시도, `Retry-After` 준수, 기한 지나면 실패 |
| 영구 실패 — 수신처 문제 | FCM `UNREGISTERED`(404), APNs `410 Unregistered`·`ExpiredToken`, SMTP `5.1.1` | 재시도 안 함. 토큰 삭제, 주소는 억제 목록 |
| 영구 실패 — 우리 문제 | FCM `INVALID_ARGUMENT`(400, 페이로드 4096바이트 초과 등), `SENDER_ID_MISMATCH`(403), `THIRD_PARTY_AUTH_ERROR`(401) | 재시도 안 함. 알람 — 코드·설정을 고친다 |

- FCM 오류 문서(ErrorCode 참조, 2026-02-03 갱신판)
  - `UNREGISTERED`: 앱 삭제, 토큰 만료, 앱 갱신 후 수신 미설정 등. "이 토큰을 앱 서버에서 지우고 더 쓰지 말라."
  - `UNAVAILABLE`: `Retry-After`가 있으면 따르고, 지수 백오프를 쓰라. 여러 메시지면 지터를 고려하라. 문제를 일으키는 발신자는 차단 목록에 오를 수 있다고 적는다.
  - `QUOTA_EXCEEDED`의 메시지 속도 초과: 최소 1분부터 지수 백오프.
  - `INVALID_ARGUMENT`는 토큰 문제일 수도, 페이로드 문제일 수도 있다. FCM 토큰 관리 문서는 "메시지가 유효하다고 확인된 경우에만" 토큰 문제로 보라고 한다.
- APNs 응답 문서: `410`은 "기기 토큰이 그 토픽에서 더 이상 활성이 아니다". `Unregistered`면 앱이 같은 토큰을 다시 받아 등록하지 않는 한 그 토큰으로 더 보낼 필요가 없다. 410 응답의 `timestamp`는 APNs가 토큰이 무효라고 확인한 시각(밀리초)이다.
- 이메일 `4yz`/`5yz` 구분과 `5.1.x`만 억제한다는 원칙은 network/51의 핵심 문장과 같다.

### 4. 억제 목록 · 선호 · 야간 제한 — 공급자에 보내기 전에 거른다

```text
  발송 요청 ─> [억제 목록에 있나?] ─예─> 버림(기록만)
                  │아니오
                  ▼
             [사용자가 이 채널·종류를 껐나?] ─예─> 버림
                  │아니오
                  ▼
             [광고성인가? 지금 21:00~08:00인가? 야간 별도 동의가 없나?] ─예─> 08:00로 미룸
                  │아니오
                  ▼
                 발송
```

- 검사 자리는 워커의 **발송 직전**이다(1절 그림 ①, 적용 2절 코드). 적재 뒤에 억제 목록에 들어간 주소(늦게 온 바운스 웹훅)나 큐에서 기다리다 야간 창에 들어간 메시지도 잡으려면 그래야 한다. 릴레이에서 미리 한 번 거르는 것은 선택이다(해석).
- *억제 목록(suppression list)*: 보내면 안 되는 주소·번호·토큰의 집합. 하드 바운스, 수신 거부, 스팸 신고, 무효 토큰이 들어간다.
- *수신 거부(unsubscribe)*: 광고성 정보는 수신 거부·동의 철회 후 보내면 안 된다(정보통신망법 제50조 ②). 이메일 원클릭 수신 거부는 RFC 8058(→ network/51).
- 야간 제한: 정보통신망법 제50조 ③ "오후 9시부터 그 다음 날 오전 8시까지의 시간에 전자적 전송매체를 이용하여 영리목적의 광고성 정보를 전송하려는 자는 제1항에도 불구하고 그 수신자로부터 별도의 사전 동의를 받아야 한다. 다만, 대통령령으로 정하는 매체의 경우에는 그러하지 아니하다."(국가법령정보센터, 2026-10-02 시행판, 2026-10-04 열람)
  - 예외 매체: 같은 법 시행령 제61조 ② "법 제50조 제3항 단서에서 '대통령령으로 정하는 매체'란 전자우편을 말한다." 즉 **광고 메일은 야간 제한의 예외**이고, 문자·푸시 같은 다른 전자적 전송매체가 야간 별도 동의 대상이다(조문 기준. 구체 적용은 법무 확인).
  - 이 조항은 **영리목적 광고성** 정보에 대한 것이다. 주문·배송 같은 거래 알림을 이 조항이 막지는 않는다(해석). 다만 사용자 경험상 야간 발송을 줄이는 선택은 별개다.
  - 시각은 **수신자 기준 한국 시간**으로 계산한다(해석 — 조문은 시간대를 따로 적지 않는다). 서버 시계가 UTC면 `ZoneId.of("Asia/Seoul")`로 바꿔 판단한다.

### 실험: 롤백·응답 유실·릴레이 크래시·실패 분류·야간 보류

PostgreSQL 17 일회용 컨테이너 + JDK 21 단일 파일. 공급자는 **프로세스 안의 가짜**다: 받은 메시지를 "도착"으로 세고, 멱등 키를 주면 같은 키를 한 번만 도착시키며, 설정한 횟수만큼 "처리는 하고 응답만 잃는다"(타임아웃 흉내).

```java
static class Provider {
    final List<String> delivered = new ArrayList<>();
    final Set<String> keys = new HashSet<>();
    int loseResponses;                                   // 처리 후 응답만 잃는 횟수
    String send(String to, String text, String idemKey) throws Exception {
        if (idemKey == null || keys.add(idemKey)) delivered.add(to + ":" + text);
        if (loseResponses-- > 0) throw new java.net.SocketTimeoutException("read timed out");
        return "202";
    }
}
// A. 트랜잭션 안에서 바로 발송 → 롤백
c.setAutoCommit(false);
c.createStatement().execute("INSERT INTO orders VALUES ('o1')");
p.send("user1", "주문 o1 완료", null);                    // 커밋 전에 외부로 나간다
c.rollback();
// A'. outbox: 같은 트랜잭션에 발송 의도만 기록 → 롤백
c.createStatement().execute("INSERT INTO outbox(notification_key,to_addr,body) VALUES ('order-completed:o2','user1','주문 o2 완료')");
c.rollback();
// C. 릴레이: 보내고 sent_at 기록 전에 크래시 → 재시작해서 다시 집는다
while (r.next()) {
    q.send(r.getString(3), r.getString(4), withKey ? r.getString(2) : null);
    if (run == 1) break;                                 // 크래시
    c.createStatement().execute("UPDATE outbox SET sent_at=now() WHERE id=" + r.getLong(1));
}
```

(실험, PostgreSQL 17.11 `postgres:17` + JDK 21.0.12 eclipse-temurin, pgJDBC 42.7.7, 전용 네트워크, 2026-10-04)

```text
DB: 17.11 (Debian 17.11-1.pgdg13+2)
A 직접 발송: 롤백 뒤 orders=0, 도착한 알림=[user1:주문 o1 완료]
A outbox   : 롤백 뒤 outbox=0 → 릴레이가 보낼 것 없음
B 멱등 키 없음: 시도 3회, 도착 3통
B 멱등 키 있음: 시도 3회, 도착 1통
C 같은 발송 키 두 번 적재: 23505 ERROR: duplicate key value violates unique constraint "outbox_notification_key_key"
C 릴레이 크래시 후 재시작, 공급자 멱등 키 없음: 도착 2통
C 릴레이 크래시 후 재시작, 공급자 멱등 키 있음: 도착 1통
D tokA: 시도 3회, 마지막 200
D tokB: 시도 1회, 마지막 404 UNREGISTERED
D mail-x: 시도 1회, 마지막 550 5.1.1 user unknown
D 억제 목록 = [mail-x, tokB] → 다음 발송은 워커가 공급자에 보내기 전에 걸러진다
E 광고 2026-10-04T20:59 KST → 2026-10-04T20:59+09:00[Asia/Seoul]
E 광고 2026-10-04T22:30 KST → 2026-10-05T08:00+09:00[Asia/Seoul]
E 광고 2026-10-05T07:59 KST → 2026-10-05T08:00+09:00[Asia/Seoul]
E 광고 2026-10-05T08:00 KST → 2026-10-05T08:00+09:00[Asia/Seoul]
```

- 관찰
  - A: DB 롤백은 이미 나간 문자를 되돌리지 못한다. outbox는 롤백과 함께 사라져서 보낼 것이 남지 않는다.
  - B: 응답만 두 번 잃자 재시도 세 번이 그대로 세 통이 됐다. 커리큘럼 ⚠의 "같은 알림 3번"이 이 모양이다. 공급자 쪽 멱등 키가 있으면 한 통이다.
  - C: outbox의 UNIQUE는 "같은 사건 두 번 적재"를 DB가 거절하게 한다(SQLSTATE `23505`). 하지만 릴레이가 보낸 뒤 기록 전에 죽는 구간은 UNIQUE가 못 막는다. 이 구간은 공급자 멱등 키가 닫는다.
  - D: 일시 실패만 재시도하고, 영구 실패는 한 번에 멈추고 억제 목록에 넣었다(공급자 응답은 각본으로 준 값이다).
  - E: 20:59는 바로, 21:00 이후와 08:00 이전은 08:00으로 미뤘다. 경계(08:00 정각)는 허용으로 처리했다.
- 한계: 공급자는 가짜다. 실제 공급자의 멱등 키 지원 여부·보관 기간은 공급자마다 다르다.

### 5. 푸시 토큰 수명

```text
  앱 설치 ─> 토큰 발급 ─> 서버에 (user, token, updated_at) 저장
                │
                ├─ 앱이 열릴 때마다 토큰을 다시 올리고 updated_at 갱신
                ├─ 토큰이 바뀌면(갱신 콜백) 새 토큰으로 교체
                └─ 발송 결과 UNREGISTERED / 410 ─> 즉시 삭제
  주기 작업: updated_at이 오래된 토큰 정리
```

- FCM 등록 관리 문서("Best practices for FCM registration management", 2026-10-01 갱신판. 예전 제목은 "… registration token management". FCM이 등록 토큰에서 Firebase 설치 ID(FID) 기반 등록으로 옮겨 가는 중이며 두 방식을 함께 지원한다고 적는다)
  - 앱 서버는 등록이 업로드될 때마다 타임스탬프를 갱신하라.
  - FCM에 한 달 넘게 연결하지 않은 기기의 등록을 stale(오래된 등록)로 부르고, 이런 등록으로 보낸 메시지는 전달될 가능성이 낮다고 적는다.
  - Android에서 270일 비활성인 등록은 FCM이 만료로 보고 보내기를 거부한다.
  - 토큰 갱신 주기는 한 달이 배터리와 탐지의 균형점이며, 주 1회보다 자주 할 이점은 없다고 적는다.
- 죽은 토큰을 두면 발송마다 404·410이 돌아온다. 실패율 지표가 오염되고 진짜 장애가 묻힌다.

## 쓰이는 자료구조·알고리즘

- **outbox 표 + UNIQUE 인덱스** — 같은 사건의 이중 적재를 DB가 판정한다(B+Tree 유일 인덱스) → [distributed/16-outbox-and-dual-write](../../distributed/16-outbox-and-dual-write/2-summary.md).
- **재시도 큐 + 지수 백오프 + 지터** — `next_attempt_at` 순으로 꺼내는 지연 큐(최소 힙 또는 DB 인덱스) → [data-structure/07-heap](../../data-structure/07-heap/2-summary.md) · [reliability/06-retry-backoff-jitter](../../reliability/06-retry-backoff-jitter/2-summary.md).
- **억제 목록 = 해시 셋** — 발송 직전 O(1) 조회. 이메일 주소는 정규화(소문자 등)한 값을 키로 둔다. 매우 크면 앞단에 블룸 필터를 두고 "있을 수도 있음"만 정밀 조회하는 방식도 쓴다 → [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md) · [data-structure/11-bloom-filter](../../data-structure/11-bloom-filter/2-summary.md).
- **실패 분류 표** — 공급자 응답 코드 → {재시도, 억제, 알람}. 코드가 아닌 표(설정)로 두면 공급자를 바꿔도 분기 코드가 그대로다.
- **시간대 변환·창 계산** — 수신자 시간대로 바꾸고 `[21:00, 08:00)` 창이면 다음 08:00으로 미룬다(실험 E의 `nextAllowed`).
- **DLQ(dead letter queue)** — 재시도 기한을 넘긴 메시지를 따로 모아 사람이 본다 → [distributed/18-consumer-failure-handling](../../distributed/18-consumer-failure-handling/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 순서

1. 알림을 **거래성**(주문·결제·보안)과 **광고성**으로 나눈다. 광고성은 동의·수신 거부·야간 규칙을 받는다.
2. 업무 트랜잭션에서는 outbox 행만 쓴다. 키 = 사건 + 수신자 + 채널.
3. 워커는 보내기 전에 억제 목록·사용자 선호·야간 창을 본다.
4. 공급자 멱등 키를 지원하면 notification_key를 그대로 싣는다.
5. 응답을 표로 분류해 재시도·억제·알람으로 보낸다. 재시도는 기한을 둔다(예: 거래성 문자 30분, 예시).
6. 바운스·수신 거부는 공급자 웹훅으로도 들어온다. 그 웹훅 수신은 [09](../09-async-apis-and-webhooks/2-summary.md)의 받는 쪽 규칙(서명·중복 제거)을 따른다.
7. 지표·알람을 붙인다(아래 3절).

### 2. 코드 — 발송 워커의 뼈대 (Java)

```java
void dispatch(OutboxRow row) {
    if (history.isSent(row.key())) return;                        // 이미 SENT면 다시 보내지 않는다(같은 행을 다시 집은 경우)
    Recipient r = recipients.load(row.recipientId());
    if (suppression.contains(row.channel(), r.address())) { history.mark(row.key(), "SUPPRESSED"); return; }
    if (!prefs.allows(r, row.category(), row.channel()))  { history.mark(row.key(), "OPTED_OUT");  return; }
    ZonedDateTime now = ZonedDateTime.now(r.zone());
    if (row.isAdvertising() && row.channel() != EMAIL && !r.nightConsent()) {   // 전자우편은 야간 예외(시행령 제61조 ②)
        ZonedDateTime allowed = nextAllowed(now);                     // 21:00~08:00이면 다음 08:00
        if (allowed.isAfter(now)) { queue.delayUntil(row, allowed.toInstant()); return; }
    }
    ProviderResult res = provider.send(r.address(), row.body(), row.key());  // 멱등 키 = notification_key
    switch (classify(res)) {                                          // 공급자별 분류 표
        case SUCCESS        -> history.mark(row.key(), "SENT");
        case RETRY          -> retryOrDeadLetter(row, res.retryAfter());   // 백오프 + 지터, 기한 초과면 DLQ
        case INVALID_TARGET -> { suppression.add(row.channel(), r.address()); history.mark(row.key(), "INVALID"); }
        case OUR_BUG        -> { history.mark(row.key(), "FAILED"); alarms.fire("notification-config", res); }
    }
}
```

- `history.mark`도 notification_key로 멱등하게 쓴다(같은 키에 같은 상태를 두 번 써도 같은 결과).
- 첫 줄의 SENT 확인은 2절 표의 "전송 전 확인"이다. 다만 `provider.send` 성공 뒤 `mark` 전에 죽으면 SENT가 남지 않는다(실험 C의 크래시 구간). 이 구간은 공급자 멱등 키가 맡는다.
- 워커가 여럿이면 같은 행을 두 워커가 집지 않게 `SELECT … FOR UPDATE SKIP LOCKED`로 가져가는 방식이 흔하다(PostgreSQL 9.5+) → [distributed/29-outbox-vs-dispatch-log](../../distributed/29-outbox-vs-dispatch-log/2-summary.md).

### 3. 진단

```sql
-- 같은 사건·수신자에 실제로 몇 번 보냈나 (발송 시도 로그 기준)
SELECT notification_key, count(*) FROM send_attempt WHERE status = 'ACCEPTED'
GROUP BY 1 HAVING count(*) > 1 ORDER BY 2 DESC LIMIT 20;

-- 채널별 영구 실패 비율 (죽은 토큰·하드 바운스가 쌓이는지)
SELECT channel, avg((result IN ('UNREGISTERED','HARD_BOUNCE'))::int) AS invalid_ratio
FROM send_attempt WHERE created_at > now() - interval '1 day' GROUP BY 1;
```

- 지표: outbox 적체(가장 오래된 미발송 행의 나이), 채널별 성공·일시 실패·영구 실패 비율, 재시도 횟수 분포, DLQ 크기, 억제로 걸러진 수, 야간 보류 수.
- 메일 평판은 우리 지표만으로 안 보인다. Gmail Postmaster Tools 같은 수신 측 지표를 함께 본다(→ network/51).

## 장애 시나리오와 대처

### 1. 재시도로 같은 알림 3번 발송 (⚠ 커리큘럼)

- 현상: 고객이 "배송 출발" 문자를 세 통 받았다는 CS.
- 보이는 형태: 발송 로그에 같은 notification_key로 `SocketTimeoutException` 2건 뒤 성공 1건. 공급자 콘솔에는 3건 모두 "전송 완료".
- 원인: 공급자는 처리했는데 응답만 늦었다. 우리는 실패로 보고 재시도했다(실험 B "멱등 키 없음: 도착 3통").
- 대처: 공급자 멱등 키를 싣는다(실험 B "있음: 1통"). 지원하지 않으면 재시도 전 공급자 조회 API로 상태를 확인하거나, 재시도 횟수·간격을 줄인다. 타임아웃을 공급자 처리 시간 분포에 맞게 늘린다 → [reliability/05-timeouts-and-deadline-propagation](../../reliability/05-timeouts-and-deadline-propagation/2-summary.md).

### 2. 롤백됐는데 "주문 완료" 메일이 나감 (⚠ 커리큘럼)

- 현상: 결제 실패로 주문이 없는데 고객은 "주문 완료" 메일을 받았다.
- 보이는 형태: 주문 표에 없는 주문 번호가 메일 발송 로그에 있다. 같은 시각 트랜잭션 롤백 로그.
- 원인: 트랜잭션 안에서 외부 발송을 직접 호출했다(실험 A). Spring이라면 `@Transactional` 메서드 안의 `send()`, 또는 커밋 전 이벤트 리스너.
- 대처: outbox로 바꾼다. 당장은 Spring `@TransactionalEventListener(phase = AFTER_COMMIT)`로 커밋 뒤에 보내는 방법도 있지만, 커밋 뒤·발송 전 크래시면 유실된다 — 유실이 싫으면 outbox다.

### 3. 하드 바운스 주소에 계속 발송 → 전체 도달률 붕괴 (⚠ 커리큘럼)

- 현상: 어느 날부터 정상 고객의 비밀번호 재설정 메일까지 스팸함으로 간다.
- 보이는 형태: 바운스율 상승, Postmaster Tools 평판 하락, 수신 서버의 `5.7.x` 정책 거절 증가.
- 원인: `5.1.1` 하드 바운스를 일시 실패처럼 재시도했거나 억제 목록에 넣지 않았다. 오래된 가입자 목록에 대량 광고를 보냈다.
- 대처: 하드 바운스·스팸 신고·수신 거부를 즉시 억제 목록에 넣는다. 바운스 웹훅을 받아 반영한다. 거래성 메일과 광고 메일의 발송 도메인(또는 서브도메인)을 나눠 평판을 분리하는 방법도 쓴다 → network/51 장애 5.

### 4. 만료된 FCM/APNs 토큰 누적 → 발송 실패율 상승 (⚠ 커리큘럼)

- 현상: 푸시 성공률이 몇 달에 걸쳐 서서히 떨어진다. 실제 장애와 구분이 안 된다.
- 보이는 형태: FCM `UNREGISTERED`(404), APNs `410 Unregistered`가 실패의 대부분. 한 사용자에 토큰이 수십 개.
- 원인: 실패 응답을 받고도 토큰을 지우지 않았다. 토큰 갱신 때 옛 토큰을 교체하지 않고 추가만 했다.
- 대처: 404·410이면 즉시 삭제(FCM 문서: "앱 서버에서 지우고 더 쓰지 말라"). `updated_at`이 오래된 토큰을 주기적으로 정리한다(FCM 문서의 한 달 기준). 실패율 지표에서 "무효 토큰"을 따로 센다.

### 5. 광고 푸시를 밤 11시에 발송 (⚠ 커리큘럼)

- 현상: 민원·신고 접수.
- 보이는 형태: 발송 로그 시각이 21:00~08:00(KST) 사이인 광고성 메시지. 야간 수신 동의 칼럼이 비어 있다.
- 원인: 캠페인 예약 시각을 UTC로 계산했다(UTC 14:00 = KST 23:00). 또는 거래성·광고성 구분 없이 같은 큐로 보냈다.
- 대처: 광고성 여부를 메시지 속성으로 강제하고, 워커에서 수신자 시간대 기준 야간 창을 검사해 미룬다(실험 E). 야간 별도 동의를 따로 저장한다. 전자우편은 시행령 제61조 ②의 예외 매체라 이 창에서 뺄 수 있다. 전송자 명칭·연락처, 수신 거부 방법 표기(제50조 ④)도 템플릿에 넣는다. 구체 적용은 법무 확인을 거친다.

## 핵심 문장

- 업무 트랜잭션 안에서는 발송하지 않고 outbox 행만 쓴다. 롤백되면 발송 의도도 같이 사라진다.
- 멱등 발송 키는 사건에서 만들고, outbox UNIQUE → 발송 이력 → 공급자 멱등 키 세 곳에서 지킨다. 마지막 곳이 없으면 "응답 유실 후 재시도"의 중복은 줄일 수만 있다.
- 실패는 일시·영구(수신처)·영구(우리 잘못) 셋으로 나눈다. 재시도는 일시 실패에만, 기한을 두고 한다.
- 하드 바운스·수신 거부·무효 토큰은 억제 목록과 토큰 삭제로 다음 발송 전에 거른다. 계속 보내면 평판과 지표가 같이 망가진다.
- 광고성 메시지는 동의·수신 거부·야간(21:00~08:00, 수신자 시간 기준, 전자우편은 시행령상 예외) 규칙을 공급자에 보내기 직전(워커)에 검사한다.

## 관련 주제·근거

- 선행
  - [05-idempotency-keys](../05-idempotency-keys/2-summary.md) — 멱등 키의 범위와 저장
  - [09-async-apis-and-webhooks](../09-async-apis-and-webhooks/2-summary.md) — 외부로 보내는 비동기 전달의 계약, 바운스·상태 웹훅 수신
  - [distributed/18-consumer-failure-handling](../../distributed/18-consumer-failure-handling/2-summary.md) — 재시도·DLQ·poison 메시지
- 연결
  - [26-case-delivery-webhook](../26-case-delivery-webhook/2-summary.md) — 받는 쪽 사례(중복·순서·200의 뜻)
  - [network/51-email-delivery-and-authentication](../../network/51-email-delivery-and-authentication/2-summary.md) — SMTP 응답 코드, 하드 바운스, SPF·DKIM·DMARC, 원클릭 수신 거부, 대량 발송자 요건
  - [distributed/16-outbox-and-dual-write](../../distributed/16-outbox-and-dual-write/2-summary.md) · [distributed/29-outbox-vs-dispatch-log](../../distributed/29-outbox-vs-dispatch-log/2-summary.md)
  - [reliability/13-idempotency](../../reliability/13-idempotency/2-summary.md) · [reliability/06-retry-backoff-jitter](../../reliability/06-retry-backoff-jitter/2-summary.md)
  - [14-rate-limit-and-quota-contracts](../14-rate-limit-and-quota-contracts/2-summary.md) — 공급자의 429·할당량을 받는 쪽 예절
- 문서
  - Firebase "Best practices for FCM registration management" <https://firebase.google.com/docs/cloud-messaging/manage-tokens> (2026-10-01 갱신판, 2026-10-04 열람) — 업로드마다 타임스탬프 갱신, 한 달 넘게 미연결이면 stale, Android 270일 만료, 갱신 주기 월 1회, `UNREGISTERED`/`INVALID_ARGUMENT` 처리, FID 기반 등록으로 전환 중
  - Firebase "Non-collapsible and collapsible messages" <https://firebase.google.com/docs/cloud-messaging/customize-messages/collapsible-message-types> — collapsible = 아직 전달 전이면 새 메시지로 대체될 수 있는 메시지
  - FCM REST v1 ErrorCode <https://firebase.google.com/docs/reference/fcm/rest/v1/ErrorCode> (2026-02-03 갱신판) — 코드별 HTTP 상태와 권장 처리, 메시지 4096바이트(토픽 2048), `UNAVAILABLE` 시 Retry-After·지수 백오프
  - Apple "Handling notification responses from APNs" <https://developer.apple.com/documentation/usernotifications/handling-notification-responses-from-apns> — 410·`Unregistered`·`ExpiredToken`·`timestamp`
  - 정보통신망 이용촉진 및 정보보호 등에 관한 법률 제50조(국가법령정보센터 <https://www.law.go.kr>, 법률 제21988호 2026-10-02 시행판, 2026-10-04 열람) — ① 사전 동의 ② 수신 거부 후 전송 금지 ③ 21시~08시 별도 동의(대통령령 매체 예외) ④ 전송자 명칭·연락처와 수신 거부 방법 표기
  - 같은 법 시행령 제61조 ②(대통령령 제36728호 2026-10-02 시행판) — 제50조 ③ 단서의 예외 매체 = 전자우편
  - Standard Webhooks 명세 — 재전송 일정·실패 분류(09번 노트)
- 실험 목록
  - 롤백·응답 유실·릴레이 크래시·실패 분류·야간 보류(A~E) — `Np.java`, `postgres:17`(17.11) 일회용 컨테이너 `sn-ad-w09-pg` + eclipse-temurin:21-jdk(21.0.12) + pgJDBC 42.7.7, 전용 네트워크 `sn-ad-w09-net`, 1회(결정적 출력), D 출력 문구만 고쳐 같은 환경에서 다시 돌림(나머지 줄 동일). 공급자는 프로세스 안 가짜
