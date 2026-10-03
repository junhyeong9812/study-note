# api-design/28-api-symptom-index — 증상 사전: 이중 처리·목록 중복/누락·구 앱만 크래시·ID 끝자리 변형·412/409/429·웹훅 역순 → 원인·첫 진단·leaf — 정리 (힌트)

## 해결하는 문제

API 설계 영역의 다른 노트는 **원인에서 증상으로** 간다.\
"결제 POST에 멱등 계약이 없다 → 타임아웃 뒤 재시도하면 두 번 청구된다"처럼 쓴다.\
현장에서는 반대 방향이 필요하다.\
손에 든 것은 "결제가 두 번 됐어요"라는 고객 문의, 구 앱 크래시 리포트의 `InvalidFormatException` 한 줄, 서버 로그에 찍힌 존재하지 않는 ID 같은 것뿐이다.

이 노트는 그 **역방향 색인**이다.

```text
  다른 노트 (정방향)                              이 노트 (역방향)
  설계 결정 --> 결함 --> 보이는 증상                증상 --> 어디서·어떤 모양으로 --> 흔한 원인 --> 첫 진단 --> leaf
  "멱등 키를 재시도 루프 안에서 만든다"              "결제가 두 건, 간격이 수백 ms. 두 요청의 키가 같은지부터 본다"
```

쉬운 예: 택배 분실 신고 창구다.\
"물건이 안 왔다"만으로 범인을 찾지 않는다. 창구는 "송장 번호부터 보여 달라"고 한다.\
송장 하나로 출고·간선·배달 중 어느 구간에서 사라졌는지 가른다.

똑같은 구조다.\
"결제가 두 번 됐다"면 먼저 두 요청의 `Idempotency-Key`를 본다.\
키가 **없으면** 멱등 계약 자체가 없다([05-1](../05-idempotency-keys/2-summary.md)).\
키가 **서로 다르면** 클라이언트가 재시도마다 키를 새로 만들었다([05-1](../05-idempotency-keys/2-summary.md) 실험 S3, [27-1](../27-case-refund/2-summary.md)).\
키가 **같은데도** 두 번이면 서버의 보관 기간이 짧거나([05-4](../05-idempotency-keys/2-summary.md)), 확인과 기록 사이에 다른 요청이 끼었다([26-1](../26-case-delivery-webhook/2-summary.md)).\
같은 "두 번"인데 고치는 곳이 클라이언트·서버·저장소로 다르다.

실무 예:
- API 장애는 **보는 쪽과 고치는 쪽이 다르다.** 구 앱 크래시는 클라이언트 크래시 리포트에만 보이고, 서버 지표는 200으로 정상이다([07-1](../07-versioning-and-compatibility/2-summary.md)). 원인은 서버 배포다.
- 같은 결함이 **어느 계층에서 보이느냐**에 따라 이름이 바뀐다. 504는 LB가, 이중 리포트는 앱 로그가, "두 번 눌렀다"는 고객이 말한다([13-1](../13-long-running-operations/2-summary.md)).
- 많은 API 장애는 **예외 없이** 진행된다. 중복·누락·끝자리 변형·역행·조용한 절단은 에러 로그가 비어 있다. 대사(건수·합계 비교)와 고객 문의로 늦게 드러난다.

  - *역색인(inverted index)*: "문서 → 단어" 목록을 뒤집어 "단어 → 문서" 목록으로 만든 것이다. 여기서는 "leaf → 증상"을 "증상 → leaf"로 뒤집었다.
  - *leaf 표기 `NN-k`*: API 설계 영역 `NN`번 노트의 「장애 시나리오와 대처」 `k`번째 시나리오다. 01~21은 `### k.` 제목, 사례 22~27(옛 형식)은 같은 절의 굵은 번호 `**k.**` 항목이다. 예: `05-1` = 05번 노트의 시나리오 1(타임아웃 뒤 재시도 → 이중 결제).
  - *메시지 옆 버전*: 각 leaf 실험에서 실제로 찍힌 메시지다. 같은 결함이라도 라이브러리 판이 다르면 문구가 다를 수 있다(예: Jackson 2.19.2와 3.0.0은 모르는 필드에서 반대로 동작했다, [07-3](../07-versioning-and-compatibility/2-summary.md)).
  - *대사(reconciliation)*: 두 기록(우리 DB와 PG, 원천과 사본)을 맞춰 보고 불일치를 찾는 작업이다.

## 동작·원리

### 0. 증상이 보이는 자리 — 요청 한 건이 지나는 계층

```text
  [클라이언트]  ──요청──▶  [LB·게이트웨이·CDN]  ──▶  [API 서버]  ──▶  [DB·브로커·외부 공급자]
   크래시 리포트            504·429·캐시 MISS          4xx/5xx·예외 로그      느린 쿼리·lag·공급자 콘솔
   "두 번 눌렀다"           접근 로그(메서드·경로)      처리 건수 지표          중복 행·음수 재고
   끝자리 바뀐 ID 재전송      upstream timed out         grpc-timeout=null      redelivered=true

  보이는 자리 ≠ 원인 자리
   구 앱만 크래시      보이는 곳: 클라이언트      원인: 서버의 enum 값 추가(필드 추가는 엄격 설정일 때) 07-1 · 21-2 · 07-3
   ID 끝자리 변형      보이는 곳: 서버 404 로그    원인: 클라이언트 JSON 숫자 파서(binary64)   08-1
   이중 결제          보이는 곳: 고객·대사       원인: 클라이언트 키 생성 위치·서버 키 계약    05-1 · 27-1
   상태 역행          보이는 곳: 상태 이력       원인: 받는 쪽이 도착 순서대로 덮어씀         09-2 · 26-2
```

- 그래서 증상을 받으면 **어느 계층의 기록에서 봤는지**를 먼저 적는다. 클라이언트에서만 보이면 원인은 서버 배포·계약 변경 쪽일 가능성이 크고, 서버에서만 보이면 클라이언트 재시도·파서 쪽일 가능성이 크다.

### 0-1. 첫 확보 — 증상 하나에 붙일 다섯 가지

| 확보할 것 | 왜 | 어디서 |
|---|---|---|
| 요청 식별자(요청 ID·멱등 키·이벤트 id·webhook-id) | 같은 논리 작업의 여러 시도를 묶는다. 이중 처리·중복 전달 진단의 출발점 | 접근 로그, 감사 로그, 수신 테이블 |
| HTTP 상태 + 본문 형식(`Content-Type`) | 200+에러 본문, HTML 오류 페이지, problem+json을 가른다 | `curl -i`, 클라이언트 로그 |
| 시각 두 개(발생 시각·수신 시각) | 역순 도착·타임스탬프 창·보관 기간 초과를 가른다 | 이벤트 `occurred_at`, 서버 수신 로그 |
| 클라이언트 판·라이브러리 판 | "구 앱만"·"업그레이드 뒤부터"를 가른다 | User-Agent, 크래시 리포트, 의존성 목록 |
| 배포·설정 변경 시각 | 증상 시작과 맞물리는 변경을 찾는다 | 배포 기록, 게이트웨이 설정 이력 |

### 1. "같은 일이 두 번 일어났다" — 이중 결제·이중 주문·알림 두세 통

먼저 **두 처리의 요청 식별자**를 나란히 놓는다.

```text
  같은 논리 작업이 두 번 처리됐다
     │
     ├─ 키가 아예 없다 ────────────────────────────▶ 재시도 안전 계약 부재          05-1 · 02-3
     ├─ 키가 서로 다르다 ──────────────────────────▶ 키를 재시도 루프 안에서 만듦     05-1(S3) · 27-1
     ├─ 키가 같고, 두 번째가 "처음 보는 키"로 처리 ──▶ 보관 기간 < 재시도 기간        05-4
     ├─ 키(이벤트 id)가 같고 200ms 간격·다른 인스턴스 ─▶ 조회 후 처리(TOCTOU)       26-1 · 23-4
     ├─ 우리 쪽은 실패로 기록, 공급자 콘솔엔 전부 성공 ─▶ 응답만 늦은 것을 실패로 재시도 10-1 · 15-4
     ├─ 앞단 504, 앱 로그엔 정상 완료 두 건 ──────────▶ LB 타임아웃 < 처리 시간       13-1
     ├─ 브로커 redelivered=true·같은 오프셋 두 번 ────▶ 처리 후 ack 전 끊김(정상 동작) 20-3
     └─ 복원·환불·적립이 "+"로 두 번 ─────────────────▶ 이력 없는 증감 연산          24-3 · 27-2
```

| 보이는 것 (메시지·도구 판) | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| 같은 계정·금액의 결제가 수백 ms 간격으로 여러 건, 서버 로그는 전부 201. 05 실험 S1·S3: 4번 시도 모두 `timeout` → `payment 행 4`(JDK 21.0.12 + PostgreSQL 17.11) | 멱등 계약 없음, 또는 시도마다 새 키 | 두 요청의 `Idempotency-Key` 비교. 키 생성 코드가 재시도 루프 안인가 | [05-1](../05-idempotency-keys/2-summary.md) · [27-1](../27-case-refund/2-summary.md) |
| 서버 로그에 같은 본문의 POST 두 번, 첫 번째는 응답 기록 없이 연결 종료. 02·05 실험: `jdk.httpclient.enableAllMethodRetry=true`일 때 POST·PUT·DELETE도 서버 도착 2회, 기본값에선 1회(JDK 21.0.12) | 라이브러리·게이트웨이가 비멱등 메서드를 자동 재시도 | 클라이언트·게이트웨이의 재시도 대상 메서드 설정 | [02-3](../02-rest-and-resource-modeling/2-summary.md) · [05-1](../05-idempotency-keys/2-summary.md) |
| 같은 키의 두 번째 요청이 "처음 보는 키"로 처리. 오프라인에 쌓인 요청이 하루 뒤 도착 | 키 보관 기간(Stripe v1은 24시간 이후 정리 가능)보다 클라이언트 재시도 기간이 길다 | 두 요청의 시각 차 vs 보관 기간 | [05-4](../05-idempotency-keys/2-summary.md) |
| 클라이언트 `504`, nginx 로그 `upstream timed out (110: Operation timed out) while reading response header from upstream`, 서버 집계 `{"syncReports":2,...}`(13 실험, nginx 1.31.6 + JDK 21.0.12) | 동기 처리 시간이 LB 읽기 타임아웃보다 길다. 클라이언트는 결과 불명을 실패로 보고 재시도 | LB 타임아웃과 처리 시간 분포 비교. 앱 로그에서 같은 요청 완료 건수 | [13-1](../13-long-running-operations/2-summary.md) |
| 같은 notification_key로 `SocketTimeoutException` 2건 뒤 성공 1건, 공급자 콘솔은 3건 모두 "전송 완료". 10 실험 B: 멱등 키 없음 `도착 3통`, 있음 `도착 1통` | 공급자는 처리했는데 응답만 늦음 | 공급자 쪽 기록과 우리 시도 기록 대조 | [10-1](../10-notification-delivery-pipeline/2-summary.md) |
| gRPC 결제 RPC가 `DEADLINE_EXCEEDED` 뒤 재시도되어 이중 승인 | `DEADLINE_EXCEEDED`는 "서버가 했는지 모름" | 재시도 정책의 대상 코드에 `DEADLINE_EXCEEDED`가 있나 | [15-4](../15-rpc-and-grpc/2-summary.md) |
| AMQP `redelivered=true`, Kafka 같은 오프셋 두 번. 20 실험: `enable.auto.commit=false` 그룹 `g-manual`이 2회차에도 `m1 m2 m3`(apache/kafka 4.1.0) | 처리 뒤 ack·커밋 전에 끊김 — at-least-once의 정상 동작 | 소비자가 메시지 ID로 멱등 처리하나 | [20-3](../20-messaging-protocols/2-summary.md) |
| 같은 `event_id` 처리 로그 2건, 다른 인스턴스, 200ms 간격 | "조회 → 없으면 처리"의 TOCTOU, dedup 기록과 처리를 따로 커밋 | dedup이 유일 제약 + 같은 트랜잭션인가 | [26-1](../26-case-delivery-webhook/2-summary.md) · [09-2](../09-async-apis-and-webhooks/2-summary.md) |
| 같은 사용자에게 쿠폰 두 장, 200ms 간격·서로 다른 인스턴스 | 발급 이력 조회 후 INSERT(TOCTOU), 인스턴스 안 `synchronized` | `UNIQUE (promotion_id, user_id)`가 있나 | [23-4](../23-case-coupon-issue/2-summary.md) |
| 같은 `order_id` 복원 요청 2건 → 재고가 두 배 | 조건 없는 `qty = qty + ?`, 차감 이력 없음 | 증감에 "한 번만" 판정 근거(이력·상태)가 있나 | [24-3](../24-case-stock-deduct/2-summary.md) |
| 두 상담원의 부분 환불 둘 다 200, 합계가 결제액 초과 | `SELECT SUM` → 앱 비교 → INSERT(집계 조건 동시성 이상) | 상한 검사와 누적이 한 문장인가 | [27-2](../27-case-refund/2-summary.md) |
| 롤백된 주문의 "주문 완료" 메일. 10 실험 A: `롤백 뒤 orders=0, 도착한 알림=[user1:주문 o1 완료]` | 트랜잭션 안에서 외부 발송 직접 호출 | 발송 호출이 커밋 전에 있나 | [10-2](../10-notification-delivery-pipeline/2-summary.md) |

- **재시도를 끄는 것은 처방이 아니다.** 재시도를 끄면 이중 처리 대신 유실이 생긴다. 05 실험 S2는 같은 키로 재시도해 `시도2=201 replayed`, `payment 행 1`이 됐다 — 재시도는 남기고 중복을 서버가 거른다([05-1](../05-idempotency-keys/2-summary.md)).
- 이중 처리의 반대편인 "한 번도 안 됨"도 같은 표에서 출발한다. 처리 전 ack([20-2](../20-messaging-protocols/2-summary.md)), dedup만 커밋되고 처리 실패([26-1](../26-case-delivery-webhook/2-summary.md))는 키가 하나인데 결과가 0건이다.

### 2. "목록에 같은 게 두 번 나오거나 빠진다" — 페이지·스트림·집계

먼저 **데이터가 그 사이에 바뀌었나**를 본다.

```text
  목록·내보내기 결과의 건수가 원천과 다르다
     │
     ├─ 페이지를 넘기는 사이 삽입·삭제가 있었다 ─────▶ offset 기준이 밀림          06-2
     ├─ 데이터가 안 바뀌었는데도 경계에서 흔들린다 ────▶ 정렬 키 동률, tie-breaker 없음 06-3
     ├─ 정렬 옵션을 바꿔도 순서가 그대로다 ──────────▶ ORDER BY $1 (상수 정렬)       12-3
     ├─ 스트림·내보내기가 "완료"인데 행 수가 적다 ────▶ 끝 상태(OK)를 확인 안 함       16-2
     ├─ 메시지 몇 개가 에러 없이 사라졌다 ────────────▶ QoS 0·처리 전 ack           20-1 · 20-2
     ├─ 합계가 건별 합의 정확히 두 배 ───────────────▶ JOIN 카디널리티(1:N)         25-1
     └─ 배치 직후 1~2분만 "어제까지"만 보인다 ─────────▶ replica 지연·반쯤 생성된 회차   25-3
```

| 보이는 것 (메시지·도구 판) | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| 무한 스크롤에서 같은 글 두 번, 동기화 배치 누락. 06 실험: 페이지마다 삽입 3·삭제 1이면 offset `중복 40`, 삽입 1·삭제 3이면 `누락 33`, 커서는 둘 다 0(JDK 21.0.12 + PostgreSQL 17.11) | offset이 앞쪽 변화에 밀림 | 받은 ID 목록의 중복 수, 원천과 건수 차 | [06-2](../06-pagination/2-summary.md) |
| 같은 `created_at` 행들 근처에서만 중복·누락 | 정렬·커서에 유일 키가 없음 | `ORDER BY`·커서에 `id`가 있나 | [06-3](../06-pagination/2-summary.md) |
| "최신순"을 골라도 순서가 안 바뀜, 에러 없음. SQL 로그 `ORDER BY $1`, 계획에 Sort 노드 없음 | 식별자를 값으로 바인딩 → 상수 정렬 | 실제 실행 SQL·계획 | [12-3](../12-filtering-sorting-search/2-summary.md) |
| 내보내기 "완료"인데 행 수가 적음, 클라이언트 오류 없음. 16 실험: `나쁜 예: 처리 완료로 기록, 받은 seq=[1, 2, 3, 4, 5] (요청은 10개)`(grpc-java 1.72.0) | `onError`를 삼키고 "더 안 온다"를 완료로 봄 | 서버 로그의 종료 상태(`UNAVAILABLE`), 총 건수 대조 | [16-2](../16-grpc-streaming-modes/2-summary.md) |
| 발행 수와 수신 수 차이, 재전송 흔적 없음 | MQTT QoS 0(구독이 0이면 그 구간도 0) | 발행·구독 양쪽 QoS | [20-1](../20-messaging-protocols/2-summary.md) |
| 브로커 기준 lag 0인데 하위 DB에 결과 없음. 20 실험: 커밋한 그룹 `g-auto`는 2회차에 `m4`부터 받았다 — 커밋이 처리보다 앞서면 m1~m3는 다시 오지 않는다(실험은 유실 자체를 만들지 않음) | 처리 전 ack·커밋 | ack·커밋 위치가 처리 앞인가 | [20-2](../20-messaging-protocols/2-summary.md) |
| 특정 판매자만 합계가 정확히 두 배 | JOIN에 회차 조건 누락 | "합계 = 건별 합" 대조 | [25-1](../25-case-settlement-report/2-summary.md) |
| 배치 완료 직후만 최신 회차가 안 보임, 알람 없음 | 쓰기는 primary, 읽기는 replica | replica 지연 지표의 배치 시각 스파이크 | [25-3](../25-case-settlement-report/2-summary.md) |

- 커서로 바꿔도 **정렬 키 값이 바뀌는 행**(예: 수정 시각 정렬에서 수정된 행)은 여전히 건너뛰거나 다시 나올 수 있다. 06은 이 경우를 문서화하거나 스냅샷 방식으로 다루라고 쓴다([06-2](../06-pagination/2-summary.md)).

### 3. "구 앱만 크래시한다" — 서버는 200, 클라이언트만 실패

먼저 **서버 배포 시각과 클라이언트 오류 시작 시각**을 맞춰 보고, 오류 메시지가 역직렬화 단계인지 본다.

```text
  서버 지표 정상(200), 특정 클라이언트 판만 실패·이상
     │
     ├─ "not one of the values accepted for Enum" ───▶ enum 값 추가             07-1 · 21-2
     ├─ "Unrecognized field" ────────────────────────▶ 필드 추가 + 엄격 역직렬화   07-3 · 07 실험 · 01 실험
     ├─ 예외 없이 0·null·빈 값 ──────────────────────▶ 필드 삭제·이름·의미 변경     07-2 · 21-1 · 01-5
     ├─ 예외 없이 엉뚱한 값(금액이 user_id 자리에) ──────▶ Protobuf 필드 번호 재사용    08-2
     ├─ 서버가 커서 형식을 바꾼 뒤 파트너만 400 ──────────▶ 토큰 내용에 의존            06-4
     ├─ 라이브러리 메이저 업그레이드 뒤부터 ─────────────▶ 기본값 변경               07-3
     ├─ 중계 서비스를 거친 쪽만 새 필드가 빔 ────────────▶ 구 DTO 왕복으로 필드 소실     08-3
     ├─ 새 스키마 소비자가 옛 레코드에서 실패 ───────────▶ Avro 기본값 없는 새 필드     08-4
     ├─ 정렬·문구·필드 순서에 기댄 코드만 이상 ──────────▶ 문서에 없는 동작 의존(Hyrum) 01-1 · 01-2 · 01-3
     └─ 특정 날짜부터 404·410, 한 API 키에 집중 ────────▶ Sunset 뒤 남은 호출자       07-4
```

| 보이는 것 (메시지·도구 판) | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| 구 앱 주문 목록이 안 열림. `InvalidFormatException: Cannot deserialize value of type ... from String "REFUNDED": not one of the values accepted for Enum class: [PAID]`(Jackson 2.19.2·3.0.0 모두 기본값에서) | enum을 닫힌 집합으로 역직렬화 | 응답에 새 enum 값이 나간 배포 시각 | [07-1](../07-versioning-and-compatibility/2-summary.md) · [21-2](../21-api-documentation-openapi/2-summary.md) |
| 명세 검증 시 `/status must be equal to one of the allowed values ["PENDING","PAID"]`(ajv 8.20.0) | 구현에만 enum 값 추가, 명세는 그대로 | 응답을 명세 스키마로 검증 | [21-2](../21-api-documentation-openapi/2-summary.md) |
| `UnrecognizedPropertyException: Unrecognized field "memo" ... not marked as ignorable`(Jackson 2.19.2 기본, `FAIL_ON_UNKNOWN_PROPERTIES=true`). 01 실험에서도 `tier` 추가로 같은 예외 | 클라이언트가 모르는 필드에 실패 | 클라이언트 `ObjectMapper` 설정 | [07-3](../07-versioning-and-compatibility/2-summary.md)(07 실험·01 실험) |
| 정산 화면 금액 0원, 예외 없음. 07 실험: 필드 삭제 → `OK id=3 amount=0 status=PAID`(`long`), `amount=null`(`Long`) | 삭제된 필드가 기본값이 됨. 단위 변경은 어떤 파서도 못 잡음 | 필수 필드의 0·null 비율 지표 | [07-2](../07-versioning-and-compatibility/2-summary.md) |
| SDK가 `createdAt`을 null로 읽음, 서버 로그 오류 없음. 21 실험: `/ must have required property 'createdAt'`, `/ must NOT have additional properties created_at` | 네이밍 전략 변경을 명세와 대조하지 않음 | 응답 vs 명세 스키마 계약 테스트 | [21-1](../21-api-documentation-openapi/2-summary.md) |
| Jackson 2→3 업그레이드 뒤 "모르는 필드면 실패" 테스트가 깨지거나 오타 필드가 조용히 무시됨. 07 실험: `FAIL_ON_UNKNOWN_PROPERTIES` 2.19.2 `true`, 3.0.0 `false` | 기본값 변경 | 설정을 코드에 명시했나 | [07-3](../07-versioning-and-compatibility/2-summary.md) |
| 배포 중 일부 주문의 `user_id`가 5000·12000 같은 금액 모양 숫자, 파싱 에러 없음 | Protobuf 필드 번호 재사용 — 구 서비스는 번호 2가 `amount`, 새 서비스는 `user_id`. 08 실험: 번호를 `reserved`로 두면 `Field "user_id" uses reserved number 2.`로 컴파일 단계에서 막힘(protoc 25.5) | 이상 값이 나온 기간과 배포 기간 겹침, `.proto` 이력의 번호 변경 | [08-2](../08-schema-and-serialization/2-summary.md) |
| 커서 형식을 바꾼 배포 뒤 일부 파트너 연동만 400 | 클라이언트가 읽을 수 있는 토큰을 해석·생성 | 파트너가 보낸 토큰이 서명 없는 옛 형식인가 | [06-4](../06-pagination/2-summary.md) |
| 게이트웨이·BFF를 거친 뒤 `memo`가 비어 있음 | 중계 서비스가 구 DTO로 역직렬화 → 재직렬화(08 실험: Jackson 왕복에서 소실) | 경로별로 필드가 사라지는 지점 | [08-3](../08-schema-and-serialization/2-summary.md) |
| `AvroTypeException: Found Order, expecting Order, missing required field email`(Avro 1.12.0) | reader에만 있는 필드에 기본값 없음 | 새 필드 기본값, 레지스트리 호환성 검사 | [08-4](../08-schema-and-serialization/2-summary.md) |
| 부분 갱신으로 0을 보냈는데 안 바뀜. 08 실험: `i=0 (기본값) 0B` | proto3 암묵적 존재 필드는 기본값을 선에 싣지 않음 | 필드가 `optional`인가, 필드 마스크가 있나 | [08-5](../08-schema-and-serialization/2-summary.md) |
| 일부 화면의 "최근 주문"이 엉뚱함, 에러 없음. 01 실험 v2: `최근 가입(끝 원소)=jang`(v1은 `oh`) | 응답 순서에 기댐(계약 아님) | 클라이언트의 `get(0)`·`last()` | [01-1](../01-api-as-contract/2-summary.md) |
| 같은 404를 짧은 간격으로 반복, 클라이언트 로그 "unknown error". 01 실험 v2: `없는 사용자 판정=false` | `message` 문구로 분기 | 서버가 기계용 `code`·`type`을 주나 | [01-2](../01-api-as-contract/2-summary.md) · [04-3](../04-error-format-problem-details/2-summary.md) |
| 배치가 "처리 0건"으로 정상 종료. 01 실험 v2: `읽은 사용자 수=0 / 12` | 응답 원문을 정규식으로 처리 | 처리 건수 0 경보, JSON 파서 사용 | [01-3](../01-api-as-contract/2-summary.md) |
| 생성 직후 GET 404, 몇 초 뒤엔 보임 | 동기 반영을 비동기로 바꿈(관찰 가능한 의미 변경) | 일관성 수준이 문서에 있나 | [01-4](../01-api-as-contract/2-summary.md) |
| 응답 크기 소폭 증가, 특정 기능 표시가 일제히 바뀜 | "기본값이면 생략"을 "항상 포함"으로 | `@JsonInclude` 정책 변경 이력 | [01-5](../01-api-as-contract/2-summary.md) |
| v1 제거 직후 특정 파트너 배치가 404·410, 한 API 키에 집중 | 공지·헤더만 보내고 실제 호출자를 확인 안 함 | 버전별·키별 호출 지표 | [07-4](../07-versioning-and-compatibility/2-summary.md) |
| 컬럼 이름 정리 뒤 외부 클라이언트 파손 | 엔티티 직렬화를 그대로 응답 | API 표현 DTO가 따로 있나 | [02-4](../02-rest-and-resource-modeling/2-summary.md) |

- 엄격 역직렬화를 끄는 것만으로는 [07-2](../07-versioning-and-compatibility/2-summary.md)(조용한 0)를 못 막는다. 크래시가 "조용한 오답"으로 바뀔 뿐이다. 관대하게 읽는 쪽은 **필수 필드의 null 검사**와 **알 수 없는 enum용 `UNKNOWN` 분기**를 함께 둔다(07 실험의 `[J2 관대] enum 값 추가 -> OK ... status=UNKNOWN`).

### 4. "ID 끝자리가 바뀐다" — 존재하지 않는 ID로 조회한 로그

```text
  서버 로그: GET /orders/9007199254740992  → 404   (원래 ID ...993)
            GET /orders/1234567890123456800 → 404 (원래 ID ...789)
                     ▲ 끝자리가 0·짝수로 바뀜, 웹 클라이언트에서만, 모바일(Java·Kotlin)은 정상
```

| 보이는 것 (메시지·도구 판) | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| 08 실험(Node v22.23.2): `id -> 9007199254740992  safe? false`, `orderId -> 1234567890123456800`, `9007199254740993 === 9007199254740992 -> true`. 다시 직렬화하면 바뀐 값이 서버로 감 | 64비트 ID를 JSON 숫자로 냄. JS `JSON.parse`가 binary64로 읽음 | 404 로그의 ID가 실제 ID와 앞자리 같고 끝자리만 다른가. ID가 `Number.MAX_SAFE_INTEGER`(9007199254740991)를 넘나 | [08-1](../08-schema-and-serialization/2-summary.md) |

- ID가 작을 때는 안 보이다가 시퀀스·Snowflake ID가 커지면서 **어느 날부터** 드러난다. 실사건(Twitter, 2010)과 그 시각 계산은 [29-api-incidents](../29-api-incidents/2-summary.md)에 있다.
- 첫 진단으로 404 ID를 `BigInt`로 원래 ID와 비교하는 대신, 같은 ID를 `"id_str"`처럼 문자열로도 내고 있는지 응답을 본다. 08의 대처는 문자열 필드 **추가** + 숫자 필드 폐기 절차다([07](../07-versioning-and-compatibility/2-summary.md)).

### 5. 상태 코드로 찾기 — 412 · 409 · 422 · 428 · 429

| 코드 | 보이는 것 (메시지·도구 판) | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|---|
| 412 | 저장 버튼에 "알 수 없는 오류", 또는 같은 자원·같은 ETag PUT이 초당 여러 번. 11 실험 L2: `Bob PUT If-Match "1": 412 {"title":"precondition failed","detail":"resource changed; GET again"}` | 412를 일반 4xx로 처리하거나 다시 GET 없이 같은 ETag로 재시도 | 412 뒤 GET이 오는가 | [11-2](../11-concurrency-control-in-apis/2-summary.md) |
| 412 | 조건부 쓰기를 붙였더니 PUT이 전부 412. 11 실험 L3: `현재 ETag "3", 보낸 If-Match W/"3" → 412` | 약한 ETag를 `If-Match`에(강한 비교). 앞단 프록시가 압축하며 ETag를 약하게 바꾸기도 함(nginx 1.7.3+) | 원 서버와 앞단의 `ETag` 비교(`curl -i`) | [11-3](../11-concurrency-control-in-apis/2-summary.md) |
| 412 | 어떤 인스턴스를 거치면 412. 같은 자원의 GET ETag가 요청마다 다름 | ETag를 인스턴스별 값으로 만듦 | 같은 자원 GET 여러 번의 ETag | [11-5](../11-concurrency-control-in-apis/2-summary.md) |
| 412 없음 + 변경 소실 | 같은 자원에 PUT 두 건 둘 다 200. 11 실험 L1: `최종: {"title":"초안","tags":"a,b"} ← Alice의 제목 변경이 사라짐` | 조건 없는 전체 교체 PUT | 감사 로그의 판 번호 | [11-1](../11-concurrency-control-in-apis/2-summary.md) · [22-1](../22-case-order-point/2-summary.md) |
| 412가 나오는데도 소실 | 같은 If-Match의 PUT 둘 다 200. 11 실험 L4 check-then-write: `{200=2, 412=18}`·`{200=14, 412=6}`·`{200=9, 412=11}`(실행마다 다름), atomic은 늘 `{200=1, 412=19}` | 비교와 UPDATE가 따로 | `UPDATE … WHERE version = ?` 한 문장인가 | [11-4](../11-concurrency-control-in-apis/2-summary.md) |
| 428 | `Bob PUT (If-Match 없음): 428 {"title":"If-Match required",...}`(11 실험 L2) | 구 클라이언트가 조건 없이 보냄 — 서버가 의도적으로 막은 것 | 클라이언트 판별 비율 | [11-1](../11-concurrency-control-in-apis/2-summary.md) |
| 409 | 같은 키의 409가 초당 수십 건. 05 실험 S6: 같은 키 동시 10요청 → `{201=1, 409=9}` | 처리 중인 키에 대기 없이 재시도 | 409 직후 재요청 간격 | [05-5](../05-idempotency-keys/2-summary.md) |
| 409 | 첫 요청 200, 3초 뒤 두 번째 409 → 프론트가 에러 토스트, 포인트는 빠짐 | "재시도 후 409 = 이미 적용됨" 계약이 없음 | 같은 주문의 첫 요청 결과 | [22-2](../22-case-order-point/2-summary.md) |
| 422 | 응답 금액과 요청 금액이 다름(지문 검사 없을 때), 또는 05 실험 S4: `2차(5000): 422 {"title":"Idempotency-Key is already used"}` | 같은 키에 다른 본문 | 클라이언트가 본문을 바꾸며 키를 재사용했나 | [05-2](../05-idempotency-keys/2-summary.md) |
| 422·400 반복 | 같은 사용자의 422(또는 400)가 짧은 간격으로 여러 번 | 검증 오류를 하나씩만 돌려줌 | `errors[]`가 있나 | [04-5](../04-error-format-problem-details/2-summary.md) |
| 429 | 리미터를 켠 뒤 요청이 오히려 늘어남. 14 실험 A: `Retry-After 무시: ... 서버가 받은 요청 84, 그중 429 64` vs 준수 `23, 그중 429 3`(JDK 21.0.12) | `Retry-After` 없음·클라이언트 백오프 없음 | 429 직후 재요청 간격 | [14-2](../14-rate-limit-and-quota-contracts/2-summary.md) · [03-5](../03-status-codes-for-apis/2-summary.md) |
| 429 | 한 고객사 직원 전원이 오전 9시에 429. 14 실험 B: `IP 키: 429를 한 번 이상 받은 사용자 267/300, API 키: 0/300` | 인증된 API까지 IP를 제한 키로 | 429가 한 IP에 몰리고 그 뒤 계정이 여럿인가 | [14-1](../14-rate-limit-and-quota-contracts/2-summary.md) |
| 429 | 공격 중 `/login` 429가 일반 사용자에게 고르게 퍼짐 | `/login` 전체에 한도 하나 | IP별·계정별 한도가 분리돼 있나 | [14-3](../14-rate-limit-and-quota-contracts/2-summary.md) |
| 429 | 한 테넌트의 대량 작업 중 다른 테넌트가 간헐 429. 14 실험 C: `공유 한도 100: A 성공 99, B 성공 1/10` | 서비스 전체에 한도 하나 | 429를 테넌트별로 집계 | [14-4](../14-rate-limit-and-quota-contracts/2-summary.md) |
| 429 | 재시도 간격을 늘려도 특정 객체에만 429, Stripe `lock_timeout` | 속도 제한이 아닌 객체 잠금 경합 | 사유 헤더(`Stripe-Rate-Limited-Reason`) 유무 | [14-5](../14-rate-limit-and-quota-contracts/2-summary.md) |
| 429 | 같은 키의 429가 몇 주 동안 `Retry-After: 1`로 이어짐 | 쿼터 소진을 과부하처럼 응답 | problem `type`이 쿼터 초과를 구분하나 | [14-6](../14-rate-limit-and-quota-contracts/2-summary.md) |
| 429 | 작업 하나당 GET 수백 건, 간격 100ms 미만 | 폴링 클라이언트가 `Retry-After` 무시 | 작업 조회 경로의 키별 요청 수 | [13-2](../13-long-running-operations/2-summary.md) |

- 412·409·429는 모두 "**지금 그대로 다시 보내면 또 같은 결과**"라는 신호다. 다른 점은 다시 보내기 전에 할 일이다. 412는 다시 GET, 409(멱등 키 처리 중)는 기다림, 429는 `Retry-After`만큼 기다림이다. 셋을 같은 재시도 루프에 넣으면 412는 영원히 412다([11-2](../11-concurrency-control-in-apis/2-summary.md)).

### 6. "웹훅이 역순·중복으로 오거나 전부 거부된다"

```text
  보내는 쪽 ─(서명 v1,...  webhook-id  webhook-timestamp)─▶ 받는 쪽
                                                              │ 1. 원문 바이트로 서명 검증   ← 실패: 09-3(재직렬화) · 09-1(위조)
                                                              │ 2. 타임스탬프 창            ← 실패: 09-6(시계 어긋남)
                                                              │ 3. id 중복 제거             ← 없으면: 09-2 · 26-1
                                                              │ 4. 버전·상태 전이 비교       ← 없으면: 09-2 · 26-2 (역행)
                                                              ▼ 5. 2xx는 적재 성공 뒤에만      ← 어기면: 26-3 (영구 유실)
```

| 보이는 것 (메시지·도구 판) | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| 상태 이력에 `SHIPPED` 뒤 `PAID`. 09 실험 C: 도착 `e3(SHIPPED) e1(CREATED) e2(PAID) e2(PAID)` → `그냥 덮어쓰기 최종 = PAID`, `id 중복 제거 + seq 비교 최종 = SHIPPED`(JDK 21.0.12) | 도착 순서대로 덮어씀, 중복 제거 없음 | 이벤트의 발생 시각·버전과 수신 시각을 나란히 | [09-2](../09-async-apis-and-webhooks/2-summary.md) · [26-2](../26-case-delivery-webhook/2-summary.md) |
| 결제하지 않은 주문이 "결제 완료", PG 대시보드엔 그 결제 없음 | 서명 검증 없이 본문을 믿음. 09 실험 B3: `본문 위조(금액 1000→1): REJECT(signature)` — 검증이 있으면 거절됨 | 웹훅 로그의 발신지, PG 쪽 기록 | [09-1](../09-async-apis-and-webhooks/2-summary.md) |
| 프레임워크 업그레이드 뒤 서명 실패 100%. 09 실험 B4: `파싱 후 재직렬화 본문 : REJECT(signature)` | 미들웨어가 파싱·재직렬화한 문자열로 검증 | 원문 바이트로 다시 계산하면 맞나 | [09-3](../09-async-apis-and-webhooks/2-summary.md) |
| 특정 서버 한 대에서만 거부, 일정한 차이. 09 실험 B5: `REJECT(timestamp 600s 차이)` | 그 서버 시계가 어긋남 | 서버별 NTP 상태 | [09-6](../09-async-apis-and-webhooks/2-summary.md) |
| 장애 복구 뒤에도 일부 결제가 "대기", 보내는 쪽에 "Failed"·엔드포인트 비활성화 메일 | 재전송 기간(명세 예시 약 3.1일, Stripe 라이브 3일) 초과 | 장애 기간 vs 보내는 쪽 재전송 기간 | [09-4](../09-async-apis-and-webhooks/2-summary.md) |
| 한 시간대 배송 200건이 영원히 "배송중", 그 시간 우리 5xx 0건 | 큐 적재 실패를 삼키고 200 | 브로커 장애 시각과 200 응답 겹침 | [26-3](../26-case-delivery-webhook/2-summary.md) |
| 한 택배사 메시지 하나가 전체를 30분 막음, 같은 메시지 파싱 예외 무한 반복 | 단일 직렬 큐 + 상한 없는 재시도 + poison pill | 큐 적체가 한 방향으로만 자라나 | [26-4](../26-case-delivery-webhook/2-summary.md) |
| (보내는 쪽) 웹훅 워커가 클라우드 메타데이터 주소로 요청 | 고객이 준 URL을 검사 없이 호출(SSRF) | 등록 URL·DNS가 사설 대역인가 | [09-5](../09-async-apis-and-webhooks/2-summary.md) |

### 7. "대시보드는 정상인데 사용자는 실패를 본다"

| 보이는 것 (메시지·도구 판) | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| 하류 장애 중 에러율 0%. 03 실험 `OK_WITH_ERROR_BODY`: `서버 집계={2xx=10}`, `성공=10(그중 본문은 실패=5)`(JDK 21.0.12) | 실패를 200 + 에러 본문으로 응답 | 본문의 `"ok":false`·`error` 비율을 따로 센다 | [03-1](../03-status-codes-for-apis/2-summary.md) |
| HTTP 200인데 본문 `"status": 500`, 또는 반대 | problem 본문만 만들고 HTTP 상태를 안 바꿈, 중간자가 상태를 바꿈 | 같은 응답의 HTTP 상태와 `status` 멤버 | [04-4](../04-error-format-problem-details/2-summary.md) |
| GraphQL 위젯이 빔, HTTP 200, `errors`에 항목 + 해당 필드 null | 부분 성공을 2xx로 돌려줌(GraphQL over HTTP 초안) | `errors` 수·`path`별 지표 | [17-3](../17-graphql/2-summary.md) |
| DB 풀 고갈 동안 "입력값을 확인하세요", 400 급증, 5xx 평소대로 | catch-all이 400 | 400 급증과 서버 커넥션 타임아웃 로그 겹침 | [03-3](../03-status-codes-for-apis/2-summary.md) |
| 클라이언트 크래시 리포트 `Unexpected character '<'`, 또는 `type`·`code`가 null. 04 실험 기본값: `GET /orders/abc -> 400 application/json {"timestamp":...,"error":"Bad Request",...}`(problem+json이 아님, Spring Boot 4.1.1) | 오류 경로마다 형식이 다름 | 오류 응답의 `Content-Type` 분포 | [04-1](../04-error-format-problem-details/2-summary.md) |

### 8. "느리다·멈춘다·타임아웃" — 지연이 어디서 쌓이나

```text
  지연 증상
     ├─ 깊은 페이지만 느림 ─────────────────────▶ offset 풀스캔·디스크 정렬      06-1 · 12-2
     ├─ 특정 정렬·필터·검색어만 느림 ──────────────▶ 인덱스 없는 정렬·필터·LIKE    12-1 · 12-4 · 12-5
     ├─ 목록 크기에 비례해 SQL 수가 늘어남 ─────────▶ GraphQL N+1               17-1
     ├─ 짧은 요청 하나 뒤 CPU·응답 크기 폭증 ────────▶ 깊이·복잡도 제한 없음        17-2
     ├─ 하위 하나가 느리면 전체가 느림 ─────────────▶ 집계·동기 사슬에 예산 없음     19-3 · 18-4
     ├─ 하류가 멈추면 스레드가 다 묶임 ──────────────▶ gRPC 데드라인 없음           15-1
     ├─ Pod를 늘려도 기존 Pod만 포화 ──────────────▶ 장수 HTTP/2 연결·스트림       15-2 · 16-1
     ├─ 원 서버 CPU 포화, 캐시 적중률 0 ────────────▶ 조회를 POST로               02-1 · 18-2
     └─ 접속자 수에 비례해 "변화 없음" 응답 ─────────▶ 푸시가 필요한데 폴링          18-3
```

| 보이는 것 (메시지·도구 판) | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| 느린 쿼리 로그에 큰 `OFFSET`. 06 실험(PostgreSQL 17.11): `offset=500000` 자식 노드 `rows=500020`, `Execution Time: 233.113 ms` vs keyset `0.120 ms` | offset은 건너뛸 행을 만들고 버림 | `EXPLAIN ANALYZE` 자식 노드 `actual rows` | [06-1](../06-pagination/2-summary.md) |
| 한 클라이언트가 `page_size=100000`, 또는 목록마다 `count(*)` | 상한 없음, 매번 전체 건수 | 요청의 `page_size` 분포 | [06-5](../06-pagination/2-summary.md) |
| "이름순" 클릭 뒤 DB CPU 포화, 다른 API까지 느림. 12 실험: `Parallel Seq Scan` + `Sort Method: top-N heapsort`, `Execution Time: 366.446 ms`. 정상 쿼리 지연 `1.150 ms → 6.554 ms`(pgbench) | 허용 목록 없이 임의 정렬 | 계획의 `Seq Scan` + `Sort` | [12-1](../12-filtering-sorting-search/2-summary.md) |
| `Sort Method: external merge  Disk: 16880kB`, `Execution Time: 2879.601 ms`(12 실험 Q3) | 정렬 + 깊은 offset이 `work_mem` 초과 | `temp_files` 증가 | [12-2](../12-filtering-sorting-search/2-summary.md) |
| `Filter: (name ~~* '%abc12%'::text)`, `Rows Removed by Filter: 333322`, `1299.773 ms` → pg_trgm GIN `4.046 ms`(12 실험 Q6) | 앞이 열린 패턴은 B+Tree로 못 찾음 | 계획의 `Rows Removed by Filter` | [12-4](../12-filtering-sorting-search/2-summary.md) |
| 결과 10건인데 `Rows Removed by Filter: 333330`, `76.107 ms`(12 실험 Q5b) | 드문 값 필터에 맞는 인덱스 없음 | 필터 값별 지연 | [12-5](../12-filtering-sorting-search/2-summary.md) |
| 요청 하나에 `WHERE id = ?`가 수십~수백 번. 17 실험: `N=100 리졸버 그대로 SQL 101개`, `DataLoader SQL 2개`(graphql-js 16.14.2·dataloader 2.2.3) | 필드 리졸버가 원소마다 조회 | 요청당 DB 쿼리 수 | [17-1](../17-graphql/2-summary.md) |
| 본문 수백 바이트, 응답 수백 KB. 17 실험: `깊이+3: 응답 275541 바이트, SQL 1112개` | 순환 관계를 제한 없이 겹친 쿼리 | 요청 깊이·별칭 수 로그 | [17-2](../17-graphql/2-summary.md) |
| 홈 API p99가 하위 하나와 같이 움직임. 19 실험: `B 병렬, 타임아웃 없음 : 3053 ms` → `C 병렬, 호출별 300ms 예산 : 307 ms ... missing=[recommendations]`(JDK 21.0.12) | 집계에 타임아웃·부분 응답 정책 없음 | 집계 시간 ≈ 가장 느린 하위 호출인가 | [19-3](../19-api-gateway-and-bff/2-summary.md) |
| 결제가 알림·포인트·추천을 동기로 불러 그중 하나만 느려도 결제가 느림 | 기다릴 필요 없는 일을 동기 RPC로 | 호출 사슬의 각 구간 지연 | [18-4](../18-api-style-selection/2-summary.md) |
| 스레드 덤프에 `blockingUnaryCall` 대기. 15 실험: `grpc-timeout=null`, `3초 경과: 데드라인 없는 호출 done=false`(grpc-java 1.72.0) | gRPC 기본값은 데드라인 없음 | 서버에서 `grpc-timeout` 없는 요청 수 | [15-1](../15-rpc-and-grpc/2-summary.md) |
| Pod별 RPC 수 편차. 15 실험: `pick_first 100회 -> {srv-a=100}`, `round_robin 100회 -> {srv-a=50, srv-b=50}` | L4는 연결을 나누고, 채널은 연결 하나에 다중화 | 클라이언트 LB 정책 | [15-2](../15-rpc-and-grpc/2-summary.md) · [16-1](../16-grpc-streaming-modes/2-summary.md) |
| 원 서버 CPU 포화, 캐시 상태 비어 있음. 02 실험: `POST /getProduct #1~#3 X-Cache-Status=`(빈 값), 백엔드 도착 `POST /getProduct=3` vs `GET /products/1=1`(nginx 1.31.6). 18 실험: `GQL POST /graphql - - - - -`, 도달 `"POST /graphql":5` | 조회를 POST로(`proxy_cache_methods` 기본 `GET HEAD`) | 접근 로그의 메서드 분포 | [02-1](../02-rest-and-resource-modeling/2-summary.md) · [18-2](../18-api-style-selection/2-summary.md) |
| 같은 엔드포인트가 요청 대부분, 응답 본문 크기가 거의 같음 | 서버가 먼저 알려야 할 정보를 폴링 | 응답 중 "변화 없음" 비율 | [18-3](../18-api-style-selection/2-summary.md) |

### 9. "메모리·연결이 터진다·자원이 안 풀린다"

| 보이는 것 (메시지·도구 판) | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| `RESOURCE_EXHAUSTED: gRPC message exceeds maximum size 4194304: 5000007`(grpc-java 1.72.0) | 기본 최대 수신 메시지 4MiB | 응답 크기 분포 | [15-5](../15-rpc-and-grpc/2-summary.md) |
| 느린 클라이언트가 붙으면 서버 RSS 상승·OOMKilled. 16 실험: `blind: onNext 20000개 ... RSS 83MB → 292MB` vs `ready: ... 최대 RSS 90MB` | `isReady()` 없이 `onNext` | 스트림별 버퍼 적체 | [16-3](../16-grpc-streaming-modes/2-summary.md) |
| 클라이언트가 떠난 뒤에도 서버 부하 유지. `CANCELLED: call already cancelled. Use ServerCallStreamObserver.setOnCancelHandler() ...`(grpc-java 1.72.0) | 서버가 취소를 확인 안 함 | 취소 뒤 생산 횟수 | [16-4](../16-grpc-streaming-modes/2-summary.md) |
| 구독 스트림이 일정 시간마다 끊김. 16 실험: `받은 수 10 뒤 DEADLINE_EXCEEDED` | 단항용 데드라인 기본값이 스트림에도 걸림 | 끊기는 주기 = 공통 데드라인 설정값인가 | [16-5](../16-grpc-streaming-modes/2-summary.md) |
| 소비자 힙이 가득 참 | AMQP prefetch 무제한 | `basic.qos` 설정 | [20-5](../20-messaging-protocols/2-summary.md) |
| 죽은 소비자의 몫이 몇 분 동안 처리 안 됨, unacked가 안 줄어듦 | TCP가 상대 소멸을 늦게 앎, 하트비트 꺼짐·김 | 하트비트·`session.timeout.ms` 설정 | [20-4](../20-messaging-protocols/2-summary.md) |
| 업로드가 몰릴 때 API 서버 메모리·대역폭 포화 | 앱 서버가 업로드를 중계 | 업로드 경로의 바이트 수 | [19-5](../19-api-gateway-and-bff/2-summary.md) |
| 진행률이 몇 시간째 40%, `lease_until`이 과거인 RUNNING 행 | 워커가 죽었는데 상태를 끝낼 주체 없음 | 워커 배포·OOM 시각과 겹침 | [13-3](../13-long-running-operations/2-summary.md) |

### 10. "남의 것이 보인다·안이 보인다" — 노출

| 보이는 것 (메시지·도구 판) | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| `/operations/1001`, `1002`…를 순서대로 조회하니 다른 고객의 리포트 링크 | 순번 ID + 소유자 검사 없음 | 조회 경로에 소유자 검사가 있나 | [13-6](../13-long-running-operations/2-summary.md) |
| 남의 번호는 403, 없는 번호는 404 → 존재 여부가 샘 | 존재 확인을 권한 확인보다 먼저 | 한 클라이언트의 연속 id 404·403 | [03-4](../03-status-codes-for-apis/2-summary.md) |
| 고객 B 결제 응답에 고객 A의 결제 결과 | 멱등 저장소를 키 문자열 하나로만 조회 | 재생 응답의 계정 ID ≠ 요청 계정 | [05-3](../05-idempotency-keys/2-summary.md) |
| 드물게 다른 사람의 이름·권한 정보, 부하 높을 때만 | DataLoader를 서버 전역으로 생성 | 로더 생성 위치 | [17-4](../17-graphql/2-summary.md) |
| 500 응답에 SQL·제약 이름·클래스 경로. 04 실험(`spring.web.error.*`): `[message] could not execute statement [ERROR: duplicate key value violates unique constraint \"uk_member_email\"] [insert into member ...]` | 개발용 노출 옵션이 운영에 남음 | 일부러 실패시킨 응답에 내부 정보 패턴 | [04-2](../04-error-format-problem-details/2-summary.md) |
| GraphQL `errors[].message`에 `internal: db timeout`(17 실험) | 리졸버 예외 문구를 그대로 직렬화 | 오류 포매터가 있나 | [17-5](../17-graphql/2-summary.md) |
| 모든 gRPC 오류가 `UNKNOWN`. 15 실험: `Fail(throw) → UNKNOWN(2) desc=Application error processing RPC` | 도메인 예외를 그대로 던짐 — 정보는 안 새지만 클라이언트가 재시도 판단 불가 | 오류 코드 분포 | [15-3](../15-rpc-and-grpc/2-summary.md) |
| 아무도 누르지 않은 "승인", User-Agent가 링크 미리보기 봇 | `GET /approve?id=…`처럼 안전 메서드에 상태 변경 | 승인 로그의 User-Agent | [02-2](../02-rest-and-resource-modeling/2-summary.md) |

- 순번 ID 자체는 결함이 아니다. **조회에 인가 검사가 없는 것**이 결함이고, 순번 ID는 그것을 대량으로 훑게 만든다. 실사건(Optus, 2022)과 로컬 재현은 [29-api-incidents](../29-api-incidents/2-summary.md)에 있다.

### 11. 알림 발송 — "세 통 갔다·안 갔다·스팸함·밤 11시"

| 보이는 것 (메시지·도구 판) | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| 정상 고객의 비밀번호 재설정 메일까지 스팸함, `5.7.x` 정책 거절 증가 | `5.1.1` 하드 바운스를 재시도·억제 목록 미반영. 10 실험 D: `mail-x: 시도 1회, 마지막 550 5.1.1 user unknown` → 억제 목록 | 바운스율·평판 지표 | [10-3](../10-notification-delivery-pipeline/2-summary.md) |
| 푸시 성공률이 몇 달에 걸쳐 하락, FCM `UNREGISTERED`(404)·APNs `410` | 무효 토큰을 지우지 않음 | 실패 중 "무효 토큰" 비율 | [10-4](../10-notification-delivery-pipeline/2-summary.md) |
| 광고성 메시지 발송 시각이 21:00~08:00 KST | 예약 시각을 UTC로 계산, 광고성 구분 없음. 10 실험 E: `광고 2026-10-04T22:30 KST → 2026-10-05T08:00+09:00[Asia/Seoul]`(미루는 쪽) | 발송 로그 시각을 수신자 시간대로 | [10-5](../10-notification-delivery-pipeline/2-summary.md) |

- 중복 발송([10-1](../10-notification-delivery-pipeline/2-summary.md))과 롤백 뒤 발송([10-2](../10-notification-delivery-pipeline/2-summary.md))은 1절 표에 있다.

### 12. 구조·운영·문서 — 한 번에 안 보이고 쌓여서 보이는 것

| 보이는 것 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| 서비스 기능 하나 바꾸는데 게이트웨이 설정도 바꿔야 함, 게이트웨이 저장소 변경 빈도가 더 높음 | 업무 규칙을 게이트웨이에 쌓음(분산 모놀리스) | 게이트웨이 변경 이력 중 업무 규칙 비율 | [19-1](../19-api-gateway-and-bff/2-summary.md) |
| 모바일 응답에 웹용 필드가 잔뜩, 팀 간 변경 대기 | 범용 API 하나로 모든 화면 | 클라이언트별 사용 필드 비율 | [19-2](../19-api-gateway-and-bff/2-summary.md) |
| 게이트웨이 하나의 장애·설정 실수로 전체 불응 | 단일 장애점, 설정 변경이 전 경로에 영향 | 게이트웨이 인스턴스 수·설정 배포 방식 | [19-4](../19-api-gateway-and-bff/2-summary.md) |
| `/v1`~`/v4`가 각자 다른 버그, 수정 하나를 네 번 | 파괴적 변경마다 구현 복사 | 버전별 코드 경로 수 | [07-5](../07-versioning-and-compatibility/2-summary.md) |
| 인스턴스를 늘리자 "다음 단계" 요청이 간헐 실패, 고정 세션을 켜야 동작 | 중간 상태를 서버 메모리 세션에 | 같은 사용자의 요청이 다른 인스턴스로 갔을 때 오류 | [02-5](../02-rest-and-resource-modeling/2-summary.md) |
| 브라우저에서 gRPC 서비스 호출 실패 | 브라우저는 네이티브 gRPC 불가(gRPC-Web + 프록시 필요) | 프록시 유무 | [18-1](../18-api-style-selection/2-summary.md) |
| 개발자 포털 예제를 그대로 보내면 400 | 스키마만 고치고 예제는 안 고침 | 예제를 스키마로 검증하나 | [21-3](../21-api-documentation-openapi/2-summary.md) |
| 문서 빌드 실패. 21 실험: `Missing $ref pointer "#/components/schemas/Ordr". Token "Ordr" does not exist.`(@apidevtools/swagger-parser 12.1.0) | 명세 참조 오타·중복 `operationId` | PR 단계 명세 검증 | [21-4](../21-api-documentation-openapi/2-summary.md) |
| 취소했는데 작업이 SUCCEEDED, 비용 청구 | 취소는 "시도", 완료와 경합 | 상태 전이가 조건부 UPDATE 한 번인가 | [13-4](../13-long-running-operations/2-summary.md) |
| 주말 뒤 작업 결과를 가지러 왔더니 404 | 끝난 작업 자원 만료, 보관 기간 문서 없음 | `finished_at`과 정리 작업 로그 | [13-5](../13-long-running-operations/2-summary.md) |
| 4xx를 5xx로 → 같은 요청이 3~4번씩 도착. 03 실험 `ALL_500`: `서버 도착=19 ... 5xx=11` | 검증 예외가 500으로 빠지고 재시도됨 | 5xx 중 검증 예외 스택 비율 | [03-2](../03-status-codes-for-apis/2-summary.md) |

### 13. 데이터 정합성 — 에러 없이 숫자가 틀린다 (사례 22~27)

| 보이는 것 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| 원장 합이 잔액과 안 맞음, 예외 0건, 피크 사용자에게만 | `SELECT` → 앱 계산 → `UPDATE balance = 2000`(lost update) | 조건부 UPDATE·affected rows 판정인가 | [22-1](../22-case-order-point/2-summary.md) |
| 잔액은 줄었는데 주문의 사용 포인트 0, 배포 재시작과 겹침 | 두 UPDATE가 다른 트랜잭션(부분 실패) | 원장 있음·주문 기록 없음 건 | [22-3](../22-case-order-point/2-summary.md) |
| 피크에만 `Deadlock found when trying to get lock; try restarting transaction`(MySQL) / `ERROR: deadlock detected`(PostgreSQL) | 잠금 순서가 요청마다 다름 | 실패 쌍의 잠금 순서 | [22-4](../22-case-order-point/2-summary.md) · [24-2](../24-case-stock-deduct/2-summary.md) |
| 1,000장인데 발급 1,007건, `remaining` -7 | 읽고 빼서 쓰기, `GET` 후 `DECR` | 차감이 한 명령·조건부 UPDATE인가 | [23-1](../23-case-coupon-issue/2-summary.md) |
| "받았다고 떴는데 쿠폰함이 빔", 요청 카운터 1,000 / 실발급 986 | 큐 적재 시점에 성공 응답 | 요청 키·실발급 키 대사 | [23-2](../23-case-coupon-issue/2-summary.md) |
| 캐시 노드 재시작 뒤 무관한 API까지 느림, 재시작 끝나도 회복 안 됨 | 캐시 미스 폴백 + 재시도의 metastable | DB 커넥션 풀 고갈·캐시 히트율 | [23-3](../23-case-coupon-issue/2-summary.md) |
| 인기 상품 재고 -3, 예외 0건 | 검사와 차감이 따로 | 판매 이력 합 > 입고량 | [24-1](../24-case-stock-deduct/2-summary.md) |
| 재고가 있는데 품절 표시, 문의 없음 | 만료 없는 예약, Redis-DB 이원화 언더셀 | 오래된 hold, Redis vs DB 재고 | [24-4](../24-case-stock-deduct/2-summary.md) |
| 엑셀 다운로드 504, 재시도할수록 전체 느림, `LIMIT 50 OFFSET 950000`류 반복 | 동기 전체 훑기 + 깊은 offset + 상한 없음 | slow query log | [25-2](../25-case-settlement-report/2-summary.md) |
| 지난달 리포트 숫자가 바뀜 | 정정을 원본 UPDATE로 | 확정 회차 행의 UPDATE 흔적 | [25-4](../25-case-settlement-report/2-summary.md) |
| PG는 취소됐는데 앱은 "환불 처리 중", 환불 건이 `REQUESTED`에 머묾 | 결과 기록·복원 단계 실패 뒤 이어 처리할 주체 없음 | 오래된 `REQUESTED`·결과 불명 건 + PG 조회 | [27-3](../27-case-refund/2-summary.md) |
| 부분 환불 세 번 뒤 포인트 1원 차이 | 건별 반올림의 합 ≠ 원값 | 마지막 환불의 계산 방식 | [27-4](../27-case-refund/2-summary.md) |

- 이 절의 공통점은 **예외가 없다**는 것이다. 사례 노트들이 반복해 쓰듯, 이런 실패는 규칙 기반 대사(합계 = 건별 합, 판매 합 ≤ 입고, 요청 키 수 = 실발급 수)로만 잡힌다.

## 쓰이는 자료구조·알고리즘

- **결정 트리**: 각 절의 그림은 "싼 질문부터" 가지를 나누는 결정 트리다. 같은 증상을 원인별로 가르는 첫 질문(키가 같나, 데이터가 바뀌었나, 어느 판에서만인가)을 루트에 둔다.
- **역색인**: leaf → 증상 목록을 증상 → leaf 목록으로 뒤집은 것이다. 이 노트의 링크 무결성은 스크립트로 확인했다(관련 주제·근거의 실험 목록).
- **그룹화·조인(로그 진단)**: 이중 처리 진단은 "요청 식별자로 group by → 건수 > 1"이다. 역순 진단은 "이벤트 id로 정렬한 발생 시각 vs 수신 시각" 비교다. 대사는 두 기록을 키로 조인해 한쪽에만 있는 행을 찾는 것이다.
- **부동소수 표현(binary64)**: ID 끝자리 변형은 가수 52비트 + 숨은 비트 1개 = 53비트를 넘는 정수가 가까운 표현 가능 값으로 반올림되는 현상이다. 2^60~2^61 구간에서는 인접한 표현 가능 값 사이가 256이다([29](../29-api-incidents/2-summary.md) 실험) → 영역 표 [architecture](../../architecture/README.md)(03-floating-point-ieee754, 미작성).
- **단조 버전 비교**: 412·역행 방지는 "가진 판 번호 ≥ 받은 판 번호면 무시"라는 비교 하나다([11](../11-concurrency-control-in-apis/2-summary.md), [09](../09-async-apis-and-webhooks/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 순서

1. 증상을 **보인 계층**과 **시작 시각**으로 적는다(0절).
2. 첫 확보 다섯 가지(0-1절)를 모은다. 특히 요청 식별자와 클라이언트 판.
3. 이 노트의 절을 고른다. 하나의 사건이 여러 절에 걸칠 수 있다(예: 504 → 재시도 → 이중 처리는 8절과 1절).
4. 표의 "첫 진단"을 싼 것부터 실행한다.
5. leaf로 가서 원리·대처를 읽는다. 대처가 "재시도 끄기"·"타임아웃 늘리기"·"검증 끄기"처럼 증상만 끄는 쪽이면 다시 본다(장애 시나리오 1).

### 2. 진단 명령 모음 (leaf 실험에서 쓴 방식)

```bash
# 헤더 그대로 보기 — 상태 코드, Content-Type, ETag, Retry-After, 캐시 상태
curl -i https://api.example.com/orders/1

# 원 서버와 앞단의 ETag 비교 (11-3: 압축하며 약한 ETag로 바뀌는가)
curl -si -H 'Accept-Encoding: gzip' https://edge.example.com/docs/1 | grep -i etag
curl -si                             http://origin.internal/docs/1   | grep -i etag

# 같은 멱등 키·이벤트 id가 두 번 처리됐나 (1절) — 접근 로그가 JSON 줄이라고 가정
jq -r 'select(.path=="/payments") | .idempotency_key' access.log | sort | uniq -c | awk '$1>1'

# Kafka 소비자 그룹의 커밋 위치와 lag (20 실험 방식)
kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group g-auto

# 느린 목록·정렬 쿼리의 실제 계획 (06·12 실험 방식)
psql -c "EXPLAIN (ANALYZE, BUFFERS, COSTS OFF) SELECT ... ORDER BY created_at DESC, id DESC LIMIT 20 OFFSET 500000"
```

- `jq` 줄은 접근 로그 형식이 JSON이라는 가정의 예시다. 형식은 시스템마다 다르다.

### 3. 증상별 "하지 말 것" 한 줄

| 증상 | 하지 말 것 | 왜 | leaf |
|---|---|---|---|
| 이중 처리 | 재시도를 끈다 | 이중 대신 유실이 된다. 키로 서버가 거른다 | [05-1](../05-idempotency-keys/2-summary.md) |
| 이중 처리(504 뒤) | LB 타임아웃만 늘린다 | 다음 데이터 증가에 다시 넘는다. 202 + 작업 자원으로 | [13-1](../13-long-running-operations/2-summary.md) |
| 구 앱만 크래시 | 클라이언트 역직렬화를 통째로 관대하게만 | 크래시가 조용한 0원으로 바뀐다 | [07-2](../07-versioning-and-compatibility/2-summary.md) |
| ID 끝자리 변형 | 숫자 필드를 문자열로 **교체** | 그 자체가 파괴적 변경이다. 문자열 필드를 추가 | [08-1](../08-schema-and-serialization/2-summary.md) |
| 412 반복 | 같은 ETag로 재시도 | 같은 ETag로는 영원히 412 | [11-2](../11-concurrency-control-in-apis/2-summary.md) |
| 429 폭주 | 한도를 올린다 | `Retry-After`가 없으면 올린 한도도 곧 찬다 | [14-2](../14-rate-limit-and-quota-contracts/2-summary.md) |
| 웹훅 서명 실패 100% | 검증을 잠시 끈다 | 그 사이가 위조 창이 된다. 원문 바이트로 검증 | [09-3](../09-async-apis-and-webhooks/2-summary.md) · [09-1](../09-async-apis-and-webhooks/2-summary.md) |
| 타임스탬프 거부 | 창을 0으로 두거나 끈다 | 재전송 공격 창이 열린다. 시계를 맞춘다 | [09-6](../09-async-apis-and-webhooks/2-summary.md) |

## 장애 시나리오와 대처

### 1. 증상만 끄는 처방 — 재시도 끄기·타임아웃 늘리기·검증 끄기

- **현상**: 이중 결제 문의가 줄었다. 그런데 "결제했는데 주문이 없다" 문의가 생겼다. 또는 504가 사라졌다가 한 달 뒤 다시 났다.
- **보이는 형태**: 재시도 설정이 0으로 바뀐 배포, LB 타임아웃 상향 변경, 웹훅 서명 검증 플래그 off.
- **원인**: 증상이 나온 계층에서 증상을 막았다. 원인 계층(멱등 계약, 동기 처리 구조, 원문 바이트 검증)은 그대로다.
- **대처**: 처방을 고를 때 "이 변경이 원인 계층을 바꾸나"를 묻는다. 05의 키 계약([05-1](../05-idempotency-keys/2-summary.md)), 13의 202 + 작업 자원([13-1](../13-long-running-operations/2-summary.md)), 09의 원문 경로([09-3](../09-async-apis-and-webhooks/2-summary.md))가 원인 계층 처방이다.

### 2. 서버 지표만 보고 "우리 문제 아님"

- **현상**: 구 앱 크래시, 웹 화면의 엉뚱한 주문, GraphQL 빈 위젯이 접수됐다. 서버 대시보드는 2xx 100%라 클라이언트 팀으로 넘겼다.
- **보이는 형태**: 서버 로그에 오류 없음. 클라이언트 크래시 리포트·고객 문의에만 증상.
- **원인**: 원인이 서버 변경(enum 추가 [07-1](../07-versioning-and-compatibility/2-summary.md), 숫자 ID [08-1](../08-schema-and-serialization/2-summary.md), 부분 성공 [17-3](../17-graphql/2-summary.md))인데 보이는 곳이 클라이언트다.
- **대처**: 서버 배포 시각과 클라이언트 오류 시작 시각을 겹쳐 본다(0절). 서버 쪽에 계약 테스트(명세 스키마 검증, [21-1](../21-api-documentation-openapi/2-summary.md))와 본문 기준 지표(`errors` 수, 200 + 에러 본문 수)를 둔다.

### 3. 같은 증상, 다른 원인 — "두 번"을 한 처방으로

- **현상**: 이중 처리 사고마다 "멱등 키를 넣자"로 끝냈는데 재발한다.
- **보이는 형태**: 키는 있다. 그런데 두 처리의 키가 다르거나([27-1](../27-case-refund/2-summary.md)), 키가 같아도 두 인스턴스가 동시에 통과했거나([26-1](../26-case-delivery-webhook/2-summary.md)), 보관 기간이 지났다([05-4](../05-idempotency-keys/2-summary.md)).
- **원인**: 1절 결정 트리의 가지를 가르지 않았다.
- **대처**: 키를 비교하는 첫 질문부터 다시 한다. 키 생성 위치(재시도 루프 밖), 키 저장의 원자성(유일 제약 + 같은 트랜잭션), 보관 기간 ≥ 재시도 기간을 각각 확인한다.

### 4. 예외 없는 실패를 아무도 세지 않음

- **현상**: 목록 누락, 스트림 절단, 정산 두 배, 쿠폰 미발급이 며칠 뒤 고객 문의로 드러난다.
- **보이는 형태**: 에러 로그·5xx 없음. 처리 건수·합계 지표가 없거나 아무도 보지 않는다.
- **원인**: 성공 응답·정상 종료를 "맞게 됐다"로 봤다([16-2](../16-grpc-streaming-modes/2-summary.md), [01-3](../01-api-as-contract/2-summary.md), [25-1](../25-case-settlement-report/2-summary.md), [23-2](../23-case-coupon-issue/2-summary.md)).
- **대처**: 건수 0 경보, 총 건수 대조(서버가 끝에 총 건수를 줌), 정기 대사 배치를 둔다. 13절의 대사 규칙을 지표로 만든다.

### 5. 색인의 메시지를 그대로 믿음 — 판이 다르면 문구가 다르다

- **현상**: 색인의 메시지로 검색했는데 운영 로그에 같은 문구가 없다.
- **보이는 형태**: 운영 라이브러리 판이 leaf 실험과 다르다(예: Jackson 3.x에서는 모르는 필드에 예외가 안 남, [07-3](../07-versioning-and-compatibility/2-summary.md)).
- **원인**: 메시지는 판과 설정에 따라 바뀐다. 이 노트의 메시지는 각 leaf 실험 환경의 출력이다.
- **대처**: 메시지 대신 **모양**으로 찾는다(예외 클래스 이름, 상태 코드, 계획 노드 이름). 판을 확인하고 해당 leaf의 실험 환경과 대조한다.

## 핵심 문장

- 이 노트는 **증상 → 보인 계층 → 결정 트리 → 흔한 원인 → 첫 진단 → leaf** 순서의 역색인이다. 고치지 않고 어느 노트로 갈지 정한다.
- API 장애는 보이는 계층과 원인 계층이 자주 다르다. 구 앱 크래시는 서버 배포에서, 끝자리 바뀐 404는 클라이언트 파서에서 온다.
- "두 번 처리됐다"의 첫 질문은 두 요청의 식별자가 같은가다. 없음·다름·같음마다 고칠 곳이 클라이언트·저장소·서버로 갈린다.
- 412·409·429는 "그대로 다시 보내지 말라"는 신호이고, 다시 보내기 전 할 일(다시 GET·대기·`Retry-After`)이 각각 다르다.
- 중복·누락·역행·절단·정산 오차는 대개 예외 없이 진행된다. 건수·합계·버전을 비교하는 대사가 유일한 그물이다.

## 관련 주제·근거

- 선행: API 설계 영역 전체([../curriculum.md](../curriculum.md)). 이 노트의 `NN-k` 링크는 각 leaf 「장애 시나리오와 대처」의 시나리오를 가리킨다(2026-10-04 판을 읽고 대조, 링크는 스크립트로 확인).
- leaf 노트
  - [01-api-as-contract](../01-api-as-contract/2-summary.md) · [02-rest-and-resource-modeling](../02-rest-and-resource-modeling/2-summary.md) · [03-status-codes-for-apis](../03-status-codes-for-apis/2-summary.md) · [04-error-format-problem-details](../04-error-format-problem-details/2-summary.md) — 원리
  - [05-idempotency-keys](../05-idempotency-keys/2-summary.md) · [06-pagination](../06-pagination/2-summary.md) · [07-versioning-and-compatibility](../07-versioning-and-compatibility/2-summary.md) · [08-schema-and-serialization](../08-schema-and-serialization/2-summary.md) · [09-async-apis-and-webhooks](../09-async-apis-and-webhooks/2-summary.md) · [10-notification-delivery-pipeline](../10-notification-delivery-pipeline/2-summary.md) · [11-concurrency-control-in-apis](../11-concurrency-control-in-apis/2-summary.md) · [12-filtering-sorting-search](../12-filtering-sorting-search/2-summary.md) · [13-long-running-operations](../13-long-running-operations/2-summary.md) · [14-rate-limit-and-quota-contracts](../14-rate-limit-and-quota-contracts/2-summary.md) — 신뢰성 계약
  - [15-rpc-and-grpc](../15-rpc-and-grpc/2-summary.md) · [16-grpc-streaming-modes](../16-grpc-streaming-modes/2-summary.md) · [17-graphql](../17-graphql/2-summary.md) · [18-api-style-selection](../18-api-style-selection/2-summary.md) · [19-api-gateway-and-bff](../19-api-gateway-and-bff/2-summary.md) · [20-messaging-protocols](../20-messaging-protocols/2-summary.md) · [21-api-documentation-openapi](../21-api-documentation-openapi/2-summary.md) — 스타일·문서
  - 사례(옛 형식): [22-case-order-point](../22-case-order-point/2-summary.md) · [23-case-coupon-issue](../23-case-coupon-issue/2-summary.md) · [24-case-stock-deduct](../24-case-stock-deduct/2-summary.md) · [25-case-settlement-report](../25-case-settlement-report/2-summary.md) · [26-case-delivery-webhook](../26-case-delivery-webhook/2-summary.md) · [27-case-refund](../27-case-refund/2-summary.md)
- 후속: [29-api-incidents](../29-api-incidents/2-summary.md) — 실사건(Twitter 64비트 ID와 `id_str` 2010, Optus 인가 없는 API로 고객 정보 대량 조회 2022)
- 다른 영역 색인: [reliability/52-reliability-symptom-index](../../reliability/52-reliability-symptom-index/2-summary.md)(재시도 폭풍·타임아웃 쪽) · [distributed/35-distributed-symptom-index](../../distributed/35-distributed-symptom-index/2-summary.md)(중복 전달·순서 쪽) · [database/56-db-symptom-index](../../database/56-db-symptom-index/2-summary.md)(느린 쿼리·lost update 쪽) · [network/52-network-symptom-index](../../network/52-network-symptom-index/2-summary.md)(HTTP·캐시·연결 쪽) · [testing/20-test-symptom-index](../../testing/20-test-symptom-index/2-summary.md) · [software-design/55-design-symptom-index](../../software-design/55-design-symptom-index/2-summary.md)
- 근거 문서: 메시지·수치는 각 leaf의 실험 출력을 따른다. 판: JDK 21.0.11·21.0.12 temurin, Jackson 2.19.2(01·04·07·08)·3.0.0(07), Spring Boot 4.1.1·Spring Framework 7.0.9(04), PostgreSQL 17.11(05·06·10·11·12), pgJDBC 42.7.7(05·10·11), pg_trgm 1.6(12), nginx 1.31.6(02·13·18·19), Node v22.23.2(08·17·18·19·21), graphql-js 16.14.2·dataloader 2.2.3(17), grpc-java 1.72.0·protobuf-java 3.25.5(15·16), protoc 25.5·Avro 1.12.0(08), apache/kafka 4.1.0(20), @apidevtools/swagger-parser 12.1.0·ajv 8.20.0(21). 사례 22~27의 메시지(MySQL·PostgreSQL 데드락 문구 등)는 사례 노트 본문을 따른다(실험 출력 아님).
- 실험 목록
  - 이 노트는 새 실험을 돌리지 않았다(종합 노트 — 브리핑 §5에서 선택). 메시지·수치는 leaf 01~21의 실험 출력과 사례 22~27 본문에서 옮겼다.
  - 시나리오 추출·대조: `scratchpad/ad/28/extract.py`가 01~27 각 `2-summary.md`의 「장애 시나리오와 대처」 절에서 `### k.`(01~21)와 `**k.`(22~27) 항목을 뽑는다. `scratchpad/ad/28/check_links.py`가 (1) 뽑은 시나리오 전부가 이 노트에 `[NN-k](../NN-slug/2-summary.md)`로 한 번 이상 걸렸는지 (2) 이 노트의 모든 `[NN-k]`가 실재하는 시나리오인지 (3) 상대 링크 경로가 실재하는지 확인한다.
