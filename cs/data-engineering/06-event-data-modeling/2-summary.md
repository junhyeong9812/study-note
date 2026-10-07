# data-engineering/06-event-data-modeling — 이벤트 데이터 모델링: 세 시각, 봉투, 상태 스냅샷 vs 변경 이벤트 — 정리 (힌트)

## 해결하는 문제

이벤트를 "필요한 필드를 담은 JSON 한 덩어리"로만 보내면, 받는 쪽이 세 가지 질문에 답하지 못한다.

```text
  {"orderId": 42, "amount": 10000, "status": "PAID"}
   ├ 언제?      → 결제가 일어난 시각인가, 서버가 받은 시각인가, 집계 잡이 처리한 시각인가
   ├ 같은 것?   → 네트워크 재시도로 두 번 온 것과, 같은 금액의 다른 주문 두 건을 구별할 수 없다
   └ 무슨 일?   → "지금 PAID"만 있다. 무엇이 왜 바뀌었는지(결제됨? 환불 취소됨?) 모른다
```

- *이벤트*: "어떤 일이 일어났다"는 사실 하나를 담은 불변 레코드. 지난 일이라 고치지 않는다.
- *이벤트 데이터 모델링*: 이벤트에 어떤 시각·식별자·메타데이터·본문을 둘지 정하는 설계. 하류 집계의 정확도가 여기서 정해진다.

쉬운 예: 택배 송장이다.
- 보낸 날(접수일), 터미널 도착 시각, 배송 처리 시각이 따로 찍힌다.
- 송장 번호가 있어서 같은 상자가 두 번 스캔돼도 한 상자로 센다.
- "배송 완료"만 적힌 종이 한 장보다, 상태가 바뀔 때마다 남는 기록이 사고 조사에 쓸모 있다.

똑같은 구조다.\
이벤트의 시각 세 개, 이벤트 ID, 변경 기록이 송장의 세 요소다.

실무 예:
- 주문 이벤트로 일별 매출 대시보드를 만든다. 어느 시각으로 "하루"를 자르느냐에 따라 숫자가 달라진다.
- 모바일 앱 클릭 로그는 오프라인으로 몇 시간 늦게 오거나, 시계가 틀린 기기에서 "미래" 시각으로 온다.
- CDC 이벤트([05번](../05-change-data-capture/2-summary.md))는 "행이 이렇게 바뀌었다"는 상태 변경이다. "회원 등급이 프로모션 때문에 올랐다"는 업무 의미는 담지 않는다.

## 동작·원리

### 1. 시각은 셋이다

```text
  기기(생산자)            수집기·브로커                  집계 잡
  ──●────────────────────●──────────────────────────────●──────────>  벽시계
   event time            ingestion time                  processing time
   "결제가 일어난 시각"     "우리 시스템이 받은 시각"          "집계가 이 이벤트를 처리한 시각"
   기기 시계(틀릴 수 있다)   서버 시계(우리가 관리)              잡이 돈 시각(재처리하면 바뀐다)
```

- *이벤트 시각(event time)*: 일이 실제로 일어난 시각. 생산자가 기록한다. CloudEvents의 `time`이 원칙적으로 이것이다("Timestamp of when the occurrence happened", 1.0.2 명세). 단 명세는 발생 시각을 알 수 없으면 생산자가 다른 시각(예: 현재 시각)을 넣어도 된다고 하고, 같은 `source`의 생산자들이 그 규칙을 일관되게 지키라고만 요구한다. `time`이 곧 실제 발생 시각이라는 보장은 없다.
- *수집 시각(ingestion time)*: 우리 시스템이 이벤트를 받아 저장한 시각. 수집기나 브로커가 찍는다.
  - Kafka 4.1에서 레코드 타임스탬프는 토픽 설정 `message.timestamp.type`으로 정한다. `CreateTime`(기본)은 생산자가 넣은 값, `LogAppendTime`은 브로커가 붙인 시각이다(Topic Configs).
- *처리 시각(processing time)*: 집계·변환이 그 이벤트를 다룬 시각. 같은 이벤트도 재처리하면 처리 시각이 바뀐다.
- 업무 지표("10월 1일 매출")는 보통 이벤트 시각으로 자른다. 처리 시각 윈도의 결과가 도착 속도·장애에 따라 달라지는 이유, 워터마크와 늦은 이벤트는 [distributed/30 §2](../../distributed/30-batch-and-stream-processing/2-summary.md)에서 다뤘다.
- 수집 시각은 "언제 알았나"를 남긴다. "10월 1일 매출, 10월 2일 아침 기준"과 "지금 기준"을 구분할 수 있다. 늦게 온 데이터의 재계산 범위를 고를 때도 쓴다([08번](../08-idempotent-pipelines-and-backfill/2-summary.md)).

#### 실험 1: 같은 2,000건을 세 기준으로 하루씩 자르면

- 합성 데이터: 2026-10-01·10-02(한국 시간, KST) 하루 1,000건씩 86.4초 간격 주문. 처리 시각 = 이벤트 시각 + 2초, 30건 중 1건은 모바일 오프라인으로 + 90분.

(실험, `postgres:17` = PostgreSQL 17.11 전용 컨테이너 `--network none`, `e.sql`, 2026-10-07)

```text
         basis          |    day     | count
------------------------+------------+-------
 event_time, KST 날짜   | 2026-10-01 |  1000
 event_time, KST 날짜   | 2026-10-02 |  1000
 event_time, UTC 날짜   | 2026-09-30 |   375
 event_time, UTC 날짜   | 2026-10-01 |  1000
 event_time, UTC 날짜   | 2026-10-02 |   625
 processed_at, KST 날짜 | 2026-10-01 |   998
 processed_at, KST 날짜 | 2026-10-02 |  1000
 processed_at, KST 날짜 | 2026-10-03 |     2

-- 처리 시각으로 자르면 자정을 넘어 옮겨진 이벤트
 event_day  | processed_day | count
 2026-10-01 | 2026-10-02    |     2
 2026-10-02 | 2026-10-03    |     2
```

- 처리 시각 기준: 10-01 23시대에 일어나 90분 늦게 처리된 2건이 10-02로 넘어갔다. 10-01은 998, 10-02는 "10-01에서 넘어온 2 + 다음 날로 넘어간 2"가 상쇄돼 1000이 됐다. 합계가 맞아 보여도 날짜별 내용은 다르다.
- UTC 날짜 기준: 한국 시간 00:00~09:00(9시간 = 1,000건의 375)이 전날로 갔다. 같은 이벤트 시각이라도 **어느 시간대의 자정**으로 자르느냐가 지표를 바꾼다.
- 해석: 타임스탬프는 `timestamptz`(UTC 기준 시점)로 저장하고, "하루"는 업무 시간대(`AT TIME ZONE 'Asia/Seoul'`)로 자른다. 이 실험의 수치는 합성 데이터의 지연 분포가 만든 것이다.

### 2. 봉투(envelope) — 본문 바깥의 공통 머리

```text
  ┌─ 봉투(context attributes) ─────────────────────────────────────────────┐
  │ specversion : "1.0"                         ← CloudEvents 명세 버전        │
  │ id          : "ord-1-42"                    ← source 안에서 유일          │
  │ source      : "/shop/order-svc"             ← 누가 냈나                   │
  │ type        : "com.example.order.placed.v2" ← 무슨 일인가(+ 스키마 버전)    │
  │ subject     : "order/42"                    ← source 안의 대상             │
  │ time        : "2026-10-01T14:58:00Z"        ← 이벤트 시각                  │
  │ dataschema  : "https://example.com/schemas/order-placed/v2"               │
  │ ┌─ data(본문) ───────────────────────────┐                               │
  │ │ {"orderId": 42, "amount": 10000}       │                               │
  │ └────────────────────────────────────────┘                               │
  └─────────────────────────────────────────────────────────────────────────┘
  + 수집기가 따로 기록: received_at (수집 시각)
```

- *봉투*: 본문 형식과 무관하게 어느 이벤트에나 같은 이름으로 붙는 메타데이터 묶음. 라우팅·중복 제거·관측을 본문을 해석하지 않고 할 수 있다.
- CloudEvents 1.0.2 명세(Context Attributes)
  - 필수(REQUIRED): `id`, `source`, `specversion`, `type`.
  - 선택(OPTIONAL): `datacontenttype`, `dataschema`, `subject`, `time`. 그 밖에 확장 속성을 더할 수 있다.
  - `id`: "Producers MUST ensure that `source` + `id` is unique for each distinct event." 재전송한 이벤트는 같은 `id`를 가질 수 있고, 소비자는 `source`와 `id`가 같은 이벤트를 중복으로 볼 수 있다(MAY).
  - `subject`: `source` 안에서 이벤트의 대상. 본문을 몰라도 대상으로 거를 수 있게 해 준다.
  - `time`: 같은 `source`의 생산자는 실제 발생 시각을 쓰든 다른 방식을 쓰든 **일관되게** 써야 한다.
- 버전은 어디에?
  - `specversion`은 CloudEvents 명세 자체의 버전이다(1.0). 이벤트 본문 스키마의 버전이 아니다.
    - 흔한 오해: `specversion`을 올려 본문 스키마 변경을 알린다. 명세는 `type`에 버전을 담을 수 있다고 하고(예시 `com.example.object.deleted.v2`), 호환되지 않는 스키마 변경은 다른 `dataschema` URI로 나타내라고 한다(SHOULD).
  - 커리큘럼이 말한 봉투 필드 "id·type·version·source·subject" 중 version은 CloudEvents에서 `type`이나 `dataschema`로 들어간다.
- 본문 스키마의 호환성·진화 규칙은 [09번](../09-data-contracts-and-schema-registry/2-summary.md)과 [api-design/08](../../api-design/08-schema-and-serialization/2-summary.md), 이벤트 저장소에서 옛 이벤트를 읽는 문제(upcasting)는 [distributed/22 §3](../../distributed/22-event-sourcing/2-summary.md)에서 다룬다.

#### 실험 2: 재전송 중복 — ID가 있을 때와 없을 때

- 같은 2,000건에, 네트워크 타임아웃 뒤 재전송된 40건(`g % 50 = 0`)을 한 번 더 넣었다.

```text
       load       | rows | revenue
------------------+------+---------
 ID 없음          | 2040 |  204000
 (source,id) 유일 | 2000 |  200000

-- ID가 없어 "시각·금액이 같으면 같은 이벤트"로 추정하면?
-- 기존 주문(10-01 12:00 KST, 100원)과 같은 초·같은 금액의 서로 다른 주문 2건을 더 넣었다
               load                | rows | distinct_guess
-----------------------------------+------+----------------
 ID 없음 + 실제 다른 주문 2건 추가 | 2042 |           2000
```

- ID가 없으면 재전송분 40건이 그대로 매출 4,000을 부풀렸다(2%).
- `(source, id)`에 기본 키를 걸고 `ON CONFLICT DO NOTHING`으로 넣으니 2,000건·200,000 그대로였다.
- 내용으로 추정해 지우는 방법은 실제로 다른 주문 2건까지 지웠다. 진짜 서로 다른 주문은 2,002건인데 추정치는 2,000이다. 같은 내용의 다른 사건과 재전송을 구별하는 것은 생산자가 붙인 ID뿐이다.

### 3. 클라이언트 시계는 틀린다

- 기기 시계는 사용자가 바꾸거나 NTP 동기화가 안 돼 틀릴 수 있다([distributed/04](../../distributed/04-physical-clocks-and-ntp/2-summary.md)).
- 그래서 이벤트 시각(기기)과 수집 시각(서버)을 **둘 다** 남긴다. 이벤트 시각이 수집 시각보다 뒤면, 적어도 하나의 시계가 틀렸다는 뜻이다.

#### 실험 3: 시계가 3시간 빠른 기기 5대

```text
 future_events | beyond_5min_tolerance | max_lead
---------------+-----------------------+----------
             5 |                     5 | 02:59:58
```

- 1,000건 중 5건이 수집 시각보다 약 3시간 "미래"였다. 이벤트 시각으로 일별 집계하면 그 기기의 실제 21시 이후 주문(+3시간이면 자정을 넘는다)이 다음 날로 간다.
- 처리 정책 후보: 허용 오차(예시: 5분)를 넘으면 플래그를 달고, 집계용 시각을 수집 시각으로 대체하거나 격리 테이블로 보낸다. 어느 쪽이든 원래 값은 지우지 않는다.
- Kafka 4.1 토픽 설정 `message.timestamp.after.max.ms`(기본 3600000 = 1시간): `CreateTime`일 때 브로커 시각보다 그 이상 미래인 레코드를 **거부**한다. 반대로 과거 쪽 한도 `message.timestamp.before.max.ms`의 기본값은 사실상 무제한이다(Topic Configs). 브로커가 검사하는 것은 Kafka **레코드 타임스탬프**다. 본문 안의 `time`·기기 시각은 검사하지 않는다. 생산자가 타임스탬프를 넣지 않으면 Kafka 생산자가 자기 현재 시각을 붙인다(ProducerRecord API). 그래서 기기 시각을 레코드 타임스탬프로 넣는 경우, 또는 Kafka 생산자 자신의 시계가 1시간 넘게 빠른 경우에 쓰기 실패가 날 수 있다(해석).

### 4. 상태 스냅샷 vs 변경 이벤트

```text
  상태 스냅샷(하루 1회 전체 상태)          변경 이벤트(바뀔 때마다)
  09-30  user_007 basic                   10:00 user_007 basic → gold  (promo-2026-10)
  10-01  user_007 basic                   18:00 user_007 gold  → basic (refund-chargeback)
         → "변화 없음"                     → 두 번 바뀌었고, 이유도 있다
```

- *상태 스냅샷*: 어느 시점의 엔티티 전체 상태. "지금 무엇인가"에 답한다. 키별 최신 값만 남기는 compaction 토픽에 잘 맞는다.
- *변경 이벤트*: 무엇이 무엇에서 무엇으로 바뀌었나. 업무 이벤트라면 "왜"(원인 명령·사유)를 담는다. 상태가 필요하면 소비자가 순서대로 접어(fold) 만든다([01번](../01-system-of-record-and-derived-data/2-summary.md)).
- CDC 이벤트는 그 중간이다. `before`·`after` 행을 담아 "무엇이 바뀌었나"는 알지만, 업무상 이유는 없다.

#### 예시 4: 하루 1회 스냅샷 diff vs 변경 이벤트 (구성한 데이터)

(위와 같은 컨테이너, `e5.sql` — 메커니즘 측정이 아니라 차이를 보이려고 값을 직접 넣은 예시)

```text
      src      | customer | before | after |      reason
---------------+----------+--------+-------+-------------------
 change events | user_007 | basic  | gold  | promo-2026-10
 change events | user_007 | gold   | basic | refund-chargeback
 change events | user_008 | basic  | gold  | spend-threshold
 snapshot diff | user_008 | basic  | gold  |
```

- 스냅샷 diff는 user_007의 두 번 바뀜을 "변화 없음"으로 보였고, 어떤 행에도 이유가 없다.
- 선택 기준
  - 하류가 "현재 상태"만 필요하다(캐시·검색 인덱스) → 상태 스냅샷(또는 CDC 최신 값)이 단순하다.
  - "몇 명이 왜 등급이 올랐나", 감사, 사건 재구성이 필요하다 → 변경 이벤트가 필요하다.
  - 둘을 같이 보내는 설계도 있다: 변경 이벤트 본문에 바뀐 뒤 상태를 함께 담는다. 대신 이벤트가 커진다.
- DDIA 1판 11장의 절 "State, Streams, and Immutability"가 상태를 변경 로그의 적분으로 보는 관점을 다룬다(절 제목은 O'Reilly 목차로 확인).

## 쓰이는 자료구조·알고리즘

- **워터마크** — "이벤트 시각 t 이전은 더 오지 않을 것"이라는 선언. 이벤트 시각 집계를 언제 닫을지 정한다. [distributed/30 §2](../../distributed/30-batch-and-stream-processing/2-summary.md)
- **해시 기반 중복 제거** — `(source, id)`를 키로 한 해시 집합(또는 유일 인덱스)에 넣어 보고, 이미 있으면 버린다. 무한히 키울 수 없으니 "재전송이 올 수 있는 기간"만큼 키를 보관한다. [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
  - 메모리를 줄이려 블룸 필터를 쓰면 거짓 양성 때문에 **처음 보는 진짜 이벤트를 중복으로 버릴 수 있다**. 매출처럼 빠지면 안 되는 이벤트에는 맞지 않는다. [data-structure/11-bloom-filter](../../data-structure/11-bloom-filter/2-summary.md)
- **결정적 ID** — 재시도해도 같은 ID가 나오게 업무 키에서 만든다(예: 주문 번호 + 상태 전이 순번). 같은 입력 → 같은 해시. [algorithm/12-hash-functions](../../algorithm/12-hash-functions/2-summary.md)
- **폴드(fold)** — 변경 이벤트를 순서대로 적용해 상태를 만든다. 상태 스냅샷은 그 결과를 저장한 것이다.

## 적용 — 풀어나가는 법

### 1. 이벤트 스키마 점검표

- [ ] `id`: 생산자가 붙이나? 재시도해도 같은 값인가? `source` 안에서 유일한가?
- [ ] `type`: 업무 사건 이름(`order.placed`)인가, "행이 바뀌었다"인가? 버전을 `type`이나 `dataschema`에 담나?
- [ ] 시각: 이벤트 시각(`time`)과 수집 시각을 따로 두나? 시간대가 명시된 형식(RFC 3339, `Z` 또는 오프셋)인가?
- [ ] `subject`: 파티션 키·필터로 쓸 대상 식별자가 봉투에 있나?
- [ ] 본문: 상태만 담나, 변경과 이유를 담나? 하류가 무엇을 물을지 먼저 적는다.

### 2. 봉투를 코드로 (Java 21)

```java
// CloudEvents 1.0.2 필수: id·source·specversion·type / 선택: subject·time·dataschema
record OrderEvent(String id, URI source, String specversion, String type, String subject,
                  Instant time, URI dataschema, Map<String, Object> data) {
    OrderEvent {
        Objects.requireNonNull(id); Objects.requireNonNull(source); Objects.requireNonNull(type);
        if (!"1.0".equals(specversion)) throw new IllegalArgumentException("specversion");
    }
}
// 수집기는 기기 시각을 고치지 않고, 받은 시각을 따로 붙인다
record Received(OrderEvent event, Instant receivedAt) {
    boolean fromFuture(Duration tolerance) { return event.time().isAfter(receivedAt.plus(tolerance)); }
}
```

- 이 코드를 OpenJDK 21.0.12에서 돌려, 수집 시각보다 약 3시간 앞선 이벤트의 `fromFuture(5분)`이 `true`, 같은 `source|id`를 해시 집합에 두 번 넣으면 두 번째가 `false`인 것을 확인했다(`Envelope.java`).

### 3. 적재 테이블과 집계 쿼리 (PostgreSQL 17)

```sql
CREATE TABLE order_event (
  source      text        NOT NULL,
  id          text        NOT NULL,
  type        text        NOT NULL,
  subject     text,
  event_time  timestamptz NOT NULL,          -- 기기 시각(CloudEvents time)
  received_at timestamptz NOT NULL DEFAULT now(),  -- 수집 시각(여기서는 DB 적재 트랜잭션 시작 시각)
  data        jsonb       NOT NULL,
  PRIMARY KEY (source, id)                   -- 재전송 흡수
);
INSERT INTO order_event (source, id, type, subject, event_time, data)
VALUES ($1, $2, $3, $4, $5, $6) ON CONFLICT (source, id) DO NOTHING;

-- 업무 일자 = 이벤트 시각을 업무 시간대로 자른다
SELECT (event_time AT TIME ZONE 'Asia/Seoul')::date AS biz_day, count(*), sum((data->>'amount')::numeric)
FROM order_event GROUP BY 1 ORDER BY 1;
```

- `now()`는 PostgreSQL 17에서 현재 트랜잭션의 **시작** 시각이다. 여러 행을 한 긴 트랜잭션으로 적재하면 실제 받은 시각보다 앞선다. 수집기가 받은 시각을 값으로 넘기거나, 행마다 실제 시각이 필요하면 `clock_timestamp()`를 쓴다(9.9.5 Current Date/Time).

### 4. 진단 쿼리 — 늦게 옴·미래·중복

```sql
-- 지연 분포: 얼마나 늦게 오나 (워터마크·재계산 범위를 정하는 근거)
SELECT percentile_cont(ARRAY[0.5, 0.99, 0.999]) WITHIN GROUP (ORDER BY received_at - event_time) FROM order_event;
-- 미래 이벤트: 기기 시계 의심
SELECT count(*) FROM order_event WHERE event_time > received_at + interval '5 minutes';
-- 수집 시각 날짜와 이벤트 시각 날짜가 다른 건수 = 수집 시각으로 자르면 자정 경계에서 옮겨질 이벤트
-- (처리 시각 가설은 집계 잡이 남긴 processed_at으로 같은 비교를 한다. 이 테이블에는 없다)
SELECT count(*) FROM order_event
WHERE (event_time AT TIME ZONE 'Asia/Seoul')::date <> (received_at AT TIME ZONE 'Asia/Seoul')::date;
```

- 읽는 법: 99.9 백분위 지연이 2시간이면, 이벤트 시각 기준 하루 집계를 자정 직후 확정하면 늦은 이벤트 일부가 빠진다. 확정 시각을 늦추거나 재계산한다([08번](../08-idempotent-pipelines-and-backfill/2-summary.md)).

## 장애 시나리오와 대처

### 1. 처리 시각으로 일별 집계 → 자정 경계에서 수치가 어긋난다 (⚠)

- **현상**: 재무팀의 10월 1일 매출(주문 DB 기준)과 대시보드의 10월 1일 매출이 조금씩 다르다. 날마다 차이가 들쭉날쭉하다.
- **보이는 형태**: 대시보드의 날짜별 값이 원천의 이벤트 시각 기준 값과 다르지만, 며칠 합계는 거의 같다. 실험 1: 10-01 998건(진실 1,000).
- **원인**: 집계가 `processed_at`(또는 적재 시각)으로 날짜를 잘랐다. 자정 직전 이벤트가 늦게 처리되면 다음 날로 넘어간다. 재처리하면 또 바뀐다.
- **대처**: 이벤트 시각 + 업무 시간대로 자른다. 늦게 온 이벤트가 속한 날짜는 다시 계산한다(08번).

### 2. 이벤트 ID가 없다 → 중복을 제거할 수 없다 (⚠)

- **현상**: 네트워크가 불안정했던 날, 주문 수가 실제보다 2% 많다.
- **보이는 형태**: 같은 내용의 행이 둘씩 있지만, 진짜 같은 사건인지 알 수 없다. 실험 2: 2,040행·204,000원(진실 2,000·200,000).
- **원인**: 생산자가 at-least-once로 재전송했는데([distributed/17](../../distributed/17-queues-logs-and-delivery-semantics/2-summary.md)) 이벤트에 식별자가 없다. 내용 기반 추정은 진짜 다른 사건까지 지운다(실험 2: 2,002건이 2,000건으로).
- **대처**: 생산자가 재시도해도 변하지 않는 `id`를 붙인다. 적재는 `(source, id)` 유일 제약으로 받는다. 이미 쌓인 과거 데이터는 원천 DB와 대조해 맞추는 수밖에 없다.

### 3. 클라이언트 시계를 믿는다 → "미래" 이벤트가 생긴다 (⚠)

- **현상**: "오늘 밤 11시 이후 매출" 칸에 아직 오지 않은 시각의 주문이 찍혀 있다. 또는 기기 시간을 바꾼 사용자의 이벤트가 몇 년 뒤 날짜로 들어온다.
- **보이는 형태**: `event_time > received_at`인 행. 실험 3: 5건, 최대 2시간 59분 58초 앞섬.
- **원인**: 이벤트 시각은 기기 시계가 찍는다. 기기 시계는 우리가 관리하지 못한다.
- **대처**: 수집 시각을 따로 남기고, 허용 오차를 넘으면 플래그·격리한다. Kafka `CreateTime`을 쓰면 `message.timestamp.after.max.ms`(기본 1시간)를 넘는 레코드는 거부되므로 생산자 오류 로그도 함께 본다.

### 4. 상태 스냅샷만 보낸다 → 무엇이 왜 바뀌었는지 모른다 (⚠)

- **현상**: "이번 달 등급 강등이 왜 늘었나"에 답할 수 없다. 하루 안에 올랐다 내려간 회원은 보이지도 않는다.
- **보이는 형태**: 스냅샷 diff로는 하루 1회 상태 차이만 보인다. 예시 4: user_007의 두 번 변경이 "변화 없음".
- **원인**: 생산자가 현재 상태만 보낸다. 변경과 원인은 생산자 코드 안에서 사라졌다.
- **대처**: 업무 의미가 있는 상태 전이는 변경 이벤트(이전 값·새 값·사유)로 낸다. 현재 상태가 필요한 소비자를 위해 상태 토픽을 따로 두거나 이벤트에 바뀐 뒤 상태를 함께 싣는다.

### 5. 시간대를 정하지 않았다 → 대시보드마다 하루가 다르다

- **현상**: BI 도구의 "10월 1일"과 배치 리포트의 "10월 1일" 매출이 다르다.
- **보이는 형태**: 한쪽의 이른 아침 매출이 다른 쪽의 전날로 들어가 있다. 날짜별 차이는 "그날 한국 시간 00~09시 매출"과 "다음 날 00~09시 매출"의 차이다. 하루 매출이 고르면 거의 상쇄되고(실험 1의 10-01: KST·UTC 모두 1,000건), 새벽 매출이 요일·행사로 출렁이는 날이나 기간 양 끝 날짜에서 크게 보인다. 실험 1: UTC 날짜 기준으로 한국 시간 00~09시 375건이 전날로 갔다.
- **원인**: 한 도구는 UTC 자정, 다른 도구는 KST 자정으로 잘랐다. `timestamp`(시간대 없음)에 저장하면 어느 시간대 값인지도 모호해진다.
- **대처**: 저장은 `timestamptz`, 업무 일자 계산은 한 곳(뷰·공통 차원)에서 업무 시간대로 한다. 날짜 차원에 "업무 시간대"를 명시한다([03번](../03-dimensional-modeling/2-summary.md)의 공통 차원).

## 핵심 문장

- 이벤트에는 이벤트 시각·수집 시각·처리 시각이 있고, 업무 지표는 보통 이벤트 시각을 업무 시간대로 잘라 만든다.
- 처리 시각이나 다른 시간대로 하루를 자르면 자정 경계의 이벤트가 옆 날짜로 옮겨 가, 합계는 비슷한데 날짜별 숫자가 틀린다.
- 재전송과 "같은 내용의 다른 사건"을 구별하는 것은 생산자가 붙인 ID뿐이다. CloudEvents는 `source` + `id`의 유일성을 생산자에게 요구한다.
- 기기 시계는 틀리므로 이벤트 시각과 수집 시각을 둘 다 남기고, 미래 이벤트를 검사한다.
- 상태 스냅샷은 "지금"에, 변경 이벤트는 "무엇이 왜 바뀌었나"에 답한다. 하류가 물을 질문으로 고른다.

## 관련 주제·근거

- 선행
  - [05-change-data-capture](../05-change-data-capture/2-summary.md) — CDC 이벤트(행 변경)
  - [distributed/04-physical-clocks-and-ntp](../../distributed/04-physical-clocks-and-ntp/2-summary.md) — 벽시계가 틀리는 이유
  - [distributed/22-event-sourcing](../../distributed/22-event-sourcing/2-summary.md) — 이벤트를 원천으로 쓸 때, 이벤트 버전
- 후속·연결
  - [07-batch-stream-architectures](../07-batch-stream-architectures/2-summary.md) — 이벤트 로그 재처리
  - [08-idempotent-pipelines-and-backfill](../08-idempotent-pipelines-and-backfill/2-summary.md) — 늦게 온 이벤트의 파티션 재계산
  - [09-data-contracts-and-schema-registry](../09-data-contracts-and-schema-registry/2-summary.md) — 본문 스키마의 호환성
  - [01-system-of-record-and-derived-data](../01-system-of-record-and-derived-data/2-summary.md) — 상태 = 이벤트의 폴드
  - [distributed/30](../../distributed/30-batch-and-stream-processing/2-summary.md)(이벤트 시간 윈도·워터마크), [distributed/17](../../distributed/17-queues-logs-and-delivery-semantics/2-summary.md)(at-least-once 재전송), [reliability/13](../../reliability/13-idempotency/2-summary.md)(멱등 키), [api-design/08](../../api-design/08-schema-and-serialization/2-summary.md)(직렬화·스키마)
- 문서
  - CloudEvents Specification v1.0.2 — Context Attributes: REQUIRED(`id`·`source`·`specversion`·`type`), OPTIONAL(`datacontenttype`·`dataschema`·`subject`·`time`), `id` 유일성과 재전송, `type`의 버전 예시, `dataschema` 비호환 변경, `time`의 일관성 <https://github.com/cloudevents/spec/blob/v1.0.2/cloudevents/spec.md>
  - Kafka 4.1 Topic Configs — `message.timestamp.type`(CreateTime 기본·LogAppendTime), `message.timestamp.after.max.ms`(1시간), `message.timestamp.before.max.ms` <https://kafka.apache.org/41/configuration/topic-configs/>
  - DDIA 1판 11장 "Stream Processing" — 절 "Reasoning About Time", "State, Streams, and Immutability"(O'Reilly 목차, Internet Archive 2024 사본으로 확인)
- 실험 목록(scratchpad `de/05/exp06/`, 전용 컨테이너 `sn-de-w05-pg6` `--network none`, 2026-10-07)
  - 1 `e.sql` §1·2 — PostgreSQL 17.11, 이벤트 시각(KST·UTC) vs 처리 시각 일별 집계
  - 2 `e.sql` §3 — ID 없는 적재 vs `(source,id)` 기본 키 + `ON CONFLICT DO NOTHING`, 내용 기반 추정의 오삭제
  - 3 `e.sql` §4 — 시계가 3시간 빠른 기기의 미래 이벤트 검사
  - 예시 4 `e5.sql` — 스냅샷 diff vs 변경 이벤트(구성한 데이터)
  - `Envelope.java` — OpenJDK 21.0.12, 봉투 record·미래 검사·해시 집합 중복 판정
