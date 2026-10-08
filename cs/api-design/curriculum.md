# API 설계 — `cs/api-design/` 커리큘럼

> **생성 문서** — `docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md` §15에서 `scripts/notes/gen_area_readme.py`로 만든다. 직접 고치지 말고 커리큘럼을 고친 뒤 재실행한다.
> 번호 = 권장 학습 순서. 상태: `미작성` · `원고 있음` · `초안(Claude)` · `검수 완료`. ⚠ 깨지면·🔧·📚 세부는 커리큘럼 본문에 있다.
> 현황: 미작성 0 · 원고 있음 0 · 초안(Claude) 29 · 검수 완료 0

> 원리(계약·자원·의미론) → 신뢰성 계약(멱등·페이지·버전·스키마) → 스타일(REST·RPC·GraphQL·비동기) → 기존 사례 6편. **HTTP 프로토콜 본문은 network/33~35**, 여기선 설계 판단만.
> 뼈대: Fielding 박사논문 5장(2000), RFC 9110·9457, Google AIP(aip.dev), Kleppmann DDIA 4장, Stripe API 문서.

## 15.1 원리

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 01 | `api-as-contract` | API = 공개 계약, Hyrum의 법칙 | 필수 | 초안(Claude) | [01-api-as-contract](01-api-as-contract/) |
| 02 | `rest-and-resource-modeling` | 자원·표현·균일 인터페이스·성숙도 모델 | 필수 | 초안(Claude) | [02-rest-and-resource-modeling](02-rest-and-resource-modeling/) |
| 03 | `status-codes-for-apis` | 상태 코드 선택(4xx vs 5xx, 409/422/429) | 필수 | 초안(Claude) | [03-status-codes-for-apis](03-status-codes-for-apis/) |
| 04 | `error-format-problem-details` | 에러 응답 표준 형식 | 권장 | 초안(Claude) | [04-error-format-problem-details](04-error-format-problem-details/) |

## 15.2 신뢰성 계약

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 05 | `idempotency-keys` | `Idempotency-Key`·멱등 메서드·재시도 안전 | 필수 | 초안(Claude) | [05-idempotency-keys](05-idempotency-keys/) |
| 06 | `pagination` | offset vs 커서(keyset) | 필수 | 초안(Claude) | [06-pagination](06-pagination/) |
| 07 | `versioning-and-compatibility` | 하위 호환 규칙·버저닝·폐기(Deprecation/Sunset) | 필수 | 초안(Claude) | [07-versioning-and-compatibility](07-versioning-and-compatibility/) |
| 08 | `schema-and-serialization` | JSON·Protobuf·Avro, 스키마 진화 | 필수 | 초안(Claude) | [08-schema-and-serialization](08-schema-and-serialization/) |
| 09 | `async-apis-and-webhooks` | 웹훅·콜백·재전송·서명 | 필수 | 초안(Claude) | [09-async-apis-and-webhooks](09-async-apis-and-webhooks/) |
| 10 | `notification-delivery-pipeline` | 이메일·SMS·푸시 발송 파이프라인: outbox → 큐 → 공급자, 멱등 발송 키, 재시도 vs 영구 실패 구분, 억제 목록(바운스·수신 거부), 사용자 선호·야간 발송 제한, 푸시 토큰 무효화 | 필수 | 초안(Claude) | [10-notification-delivery-pipeline](10-notification-delivery-pipeline/) |
| 11 | `concurrency-control-in-apis` | ETag·`If-Match`·조건부 요청 | 권장 | 초안(Claude) | [11-concurrency-control-in-apis](11-concurrency-control-in-apis/) |
| 12 | `filtering-sorting-search` | 필터·정렬 파라미터 설계 | 권장 | 초안(Claude) | [12-filtering-sorting-search](12-filtering-sorting-search/) |
| 13 | `long-running-operations` | `202 Accepted` + 작업 자원·폴링 | 권장 | 초안(Claude) | [13-long-running-operations](13-long-running-operations/) |
| 14 | `rate-limit-and-quota-contracts` | 제한 키 선택(사용자·API 키·IP·테넌트), 429와 `Retry-After`, `RateLimit` 헤더, 요금제 쿼터 vs 보호용 스로틀, 클라이언트 동작 계약 | 권장 | 초안(Claude) | [14-rate-limit-and-quota-contracts](14-rate-limit-and-quota-contracts/) |

## 15.3 스타일·문서

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 15 | `rpc-and-grpc` | RPC 의미론·gRPC·데드라인·상태 코드 | 권장 | 초안(Claude) | [15-rpc-and-grpc](15-rpc-and-grpc/) |
| 16 | `grpc-streaming-modes` | 단항·서버·클라이언트·양방향 스트리밍, 흐름 제어·데드라인·취소 | 권장 | 초안(Claude) | [16-grpc-streaming-modes](16-grpc-streaming-modes/) |
| 17 | `graphql` | 스키마·리졸버·쿼리 복잡도 | 권장 | 초안(Claude) | [17-graphql](17-graphql/) |
| 18 | `api-style-selection` | REST·gRPC·GraphQL·WebSocket/SSE·메시지 큐 중 선택 기준 | 필수 | 초안(Claude) | [18-api-style-selection](18-api-style-selection/) |
| 19 | `api-gateway-and-bff` | Gateway Routing·Aggregation·Offloading(인증·TLS·속도 제한)·Gatekeeper, BFF(클라이언트별 백엔드), Valet Key(직접 접근 위임) | 필수 | 초안(Claude) | [19-api-gateway-and-bff](19-api-gateway-and-bff/) |
| 20 | `messaging-protocols` | AMQP·MQTT·Kafka 프로토콜, 브로커 vs RPC, QoS·ack 모델 | 권장 | 초안(Claude) | [20-messaging-protocols](20-messaging-protocols/) |
| 21 | `api-documentation-openapi` | 명세 우선·OpenAPI·예제 | 권장 | 초안(Claude) | [21-api-documentation-openapi](21-api-documentation-openapi/) |

## 15.4 사례 (기존 6편 — 번호만 이동)

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 22 | `case-order-point` | 주문·포인트 API 사례 | 권장 | 초안(Claude) | [22-case-order-point](22-case-order-point/) |
| 23 | `case-coupon-issue` | 선착순 쿠폰 발급 | 권장 | 초안(Claude) | [23-case-coupon-issue](23-case-coupon-issue/) |
| 24 | `case-stock-deduct` | 재고 차감 | 권장 | 초안(Claude) | [24-case-stock-deduct](24-case-stock-deduct/) |
| 25 | `case-settlement-report` | 정산 리포트 | 권장 | 초안(Claude) | [25-case-settlement-report](25-case-settlement-report/) |
| 26 | `case-delivery-webhook` | 배송 웹훅 | 권장 | 초안(Claude) | [26-case-delivery-webhook](26-case-delivery-webhook/) |
| 27 | `case-refund` | 환불 | 권장 | 초안(Claude) | [27-case-refund](27-case-refund/) |

## 15.5 영역 마감

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 28 | `api-symptom-index` | 역색인: 이중 처리, 목록 중복/누락, 구 앱만 크래시, ID 끝자리 변형, 412/409/429, 웹훅 역순 | 필수 | 초안(Claude) | [28-api-symptom-index](28-api-symptom-index/) |
| 29 | `api-incidents` | 실사건: Twitter 64비트 ID와 JS 정밀도 → `id_str` 도입(2010) · Optus 무인증 API 열거 유출(2022) [?] | 권장 | 초안(Claude) | [29-api-incidents](29-api-incidents/) |
