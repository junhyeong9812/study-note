# api-design/28-api-symptom-index — 정답

## 정답

### 1. 보이는 계층 ≠ 원인 계층

| 증상 | 보이는 곳 | 원인이 있는 곳 | leaf |
|---|---|---|---|
| 구 앱만 크래시 | 클라이언트 크래시 리포트(서버는 200) | 서버 배포 — enum 값 추가(필드 추가는 클라이언트가 엄격 역직렬화일 때. 필드 삭제는 크래시 없이 0·null) | [07-1](../07-versioning-and-compatibility/2-summary.md) · [21-2](../21-api-documentation-openapi/2-summary.md) · [07-3](../07-versioning-and-compatibility/2-summary.md) · [07-2](../07-versioning-and-compatibility/2-summary.md) |
| ID 끝자리 변형 | 서버 404 로그 | 클라이언트 JSON 숫자 파서(binary64) | [08-1](../08-schema-and-serialization/2-summary.md) |
| 이중 결제 | 고객 문의·대사 | 클라이언트의 키 생성 위치, 서버의 키 계약 | [05-1](../05-idempotency-keys/2-summary.md) · [27-1](../27-case-refund/2-summary.md) |

- 보인 계층의 지표만 보면 "우리 문제 아님"으로 넘기기 쉽다(장애 시나리오 2).
- 시작 시각은 원인 쪽의 변경(서버 배포·라이브러리 업그레이드·설정 변경)과 맞물리는지 확인하는 데 쓴다.

### 2. 이중 결제 — 키부터 비교

| 두 요청의 키 | 의심 | leaf |
|---|---|---|
| (가) 없음 | 멱등 계약 자체가 없다. 또는 라이브러리·게이트웨이가 POST를 자동 재시도 | [05-1](../05-idempotency-keys/2-summary.md) · [02-3](../02-rest-and-resource-modeling/2-summary.md) |
| (나) 서로 다름 | 키를 재시도 루프 안에서 만든다(클라이언트 버그) | [05-1](../05-idempotency-keys/2-summary.md) · [27-1](../27-case-refund/2-summary.md) |
| (다) 같음 | 보관 기간 < 재시도 기간, 또는 확인과 기록 사이에 다른 요청이 낌(TOCTOU) | [05-4](../05-idempotency-keys/2-summary.md) · [26-1](../26-case-delivery-webhook/2-summary.md) |

- 05 실험(JDK 21.0.12 + PostgreSQL 17.11, 서버 처리 300ms·요청 타임아웃 150ms·최대 4회)
  - S1 키 없음: 4번 모두 `timeout` → `payment 행 4`.
  - S3 시도마다 새 키: 4번 모두 `timeout` → `payment 행 4`.
  - S2 같은 키: `시도2=201 replayed` → `payment 행 1`.
- 그래서 재시도를 끄는 대신 같은 키로 재시도하고 서버가 거른다.

### 3. 504 뒤 리포트 두 개

1. 클라이언트가 동기 리포트 요청을 보낸다.
2. 처리 시간이 LB 읽기 타임아웃(실험 3초)보다 길다. nginx가 `upstream timed out`을 남기고 클라이언트에 504를 준다.
3. 앱은 연결이 끊긴 줄 모르고 끝까지 처리해 리포트 1을 만든다.
4. 클라이언트는 결과 불명을 실패로 보고 재시도한다. 같은 일이 반복되어 리포트 2가 생긴다.

- 13 실험(nginx 1.31.6 + JDK 21.0.12): `시도1 → 504`, `시도2 → 504`, `서버 집계 {"syncReports":2,"asyncReports":0}`.
- 타임아웃을 늘리면 그 순간의 504는 사라지지만 처리 시간이 다시 늘면 재발하고, 결과 불명 + 재시도라는 구조는 그대로다. 원인 처방은 `202` + 작업 자원 + 멱등 키다(같은 실험 2부: 재전송해도 같은 `operations/op-1`, `asyncReports` 1) → [13-1](../13-long-running-operations/2-summary.md).

### 4. offset 중복과 동률 정렬

- 앞쪽에 삽입이 많으면 이미 본 항목이 뒤로 밀려 **다음 쪽에 다시** 나온다 → 중복. 삭제가 많으면 아직 안 본 항목이 앞으로 당겨져 **건너뛴다** → 누락.
- 06 실험(JDK 21.0.12 + PostgreSQL 17.11): 삽입 3·삭제 1이면 offset `중복 40`, 삽입 1·삭제 3이면 offset `누락 33`. 커서는 두 경우 모두 중복 0·누락 0 → [06-2](../06-pagination/2-summary.md).
- 데이터가 안 바뀌어도 흔들리는 원인: `ORDER BY created_at`처럼 동률이 있는 정렬에 유일 키가 없으면 동률 행의 순서가 정해지지 않는다. 정렬과 커서에 `id`를 붙인다 → [06-3](../06-pagination/2-summary.md).

### 5. 구 앱만 크래시 — 세 갈래

| 리포트 | 원인 | leaf |
|---|---|---|
| (가) `InvalidFormatException: ... "REFUNDED": not one of the values accepted for Enum class: [PAID]` | 서버가 enum 값을 추가, 클라이언트는 닫힌 집합으로 역직렬화 | [07-1](../07-versioning-and-compatibility/2-summary.md) |
| (나) `UnrecognizedPropertyException: Unrecognized field "memo"` | 서버가 필드를 추가, 클라이언트가 모르는 필드에 실패 | [07-3](../07-versioning-and-compatibility/2-summary.md)(07 실험) |
| (다) 예외 없이 0원 | 필드 삭제·이름 변경 → 기본값(0·null). 단위 변경은 어떤 파서도 못 잡음 | [07-2](../07-versioning-and-compatibility/2-summary.md) · [21-1](../21-api-documentation-openapi/2-summary.md) |

- 07 실험: Jackson 2.19.2는 `FAIL_ON_UNKNOWN_PROPERTIES=true`라 (나)에서 예외, Jackson 3.0.0은 `false`라 `OK id=1 amount=5000 status=PAID`. enum 값 추가(가)는 두 판 모두 기본값에서 실패했다.

### 6. 끝자리 바뀐 404

- 원래 ID는 `9007199254740993`처럼 2^53-1(9007199254740991)을 넘는 값일 가능성이 크다. 끝자리가 0·짝수로 바뀐 값만 404로 쌓인다.
- 08 실험(Node v22.23.2):
  - `id      -> 9007199254740992  safe? false`
  - `9007199254740993 === 9007199254740992 -> true`
- JS의 `JSON.parse`는 숫자를 binary64로 읽는다. Java·Kotlin 클라이언트는 ID 필드를 `long`(64비트 정수)으로 선언해 읽으면 값을 그대로 다룬다(`double`로 선언하면 같은 문제가 난다).
- 대처 순서: (1) 문자열 필드(`id_str` 같은)를 **추가**한다. (2) 클라이언트를 문자열 필드로 옮긴다. (3) 숫자 필드는 폐기 절차(Deprecation·Sunset)로 내린다. 숫자 필드를 문자열로 바로 바꾸면 그 자체가 파괴적 변경이다 → [08-1](../08-schema-and-serialization/2-summary.md), [07](../07-versioning-and-compatibility/2-summary.md).

### 7. 412·409·429

| 코드 | 다시 보내기 전 할 일 | leaf |
|---|---|---|
| 412 | 다시 GET해 새 ETag를 받고, 변경을 다시 얹거나 사용자에게 충돌을 보인다 | [11-2](../11-concurrency-control-in-apis/2-summary.md) |
| 409(같은 멱등 키 처리 중) | 기다린다(지수 백오프 + 지터, 힌트가 있으면 따름) | [05-5](../05-idempotency-keys/2-summary.md) |
| 429 | `Retry-After`만큼 기다린다. 쿼터 소진이면 다음 주기까지 | [14-2](../14-rate-limit-and-quota-contracts/2-summary.md) · [14-6](../14-rate-limit-and-quota-contracts/2-summary.md) |

- 412를 같은 재시도 루프에 넣으면 같은 ETag로 보내므로 영원히 412다.
- 11 실험 L3: 현재 ETag `"3"`에 `If-Match: W/"3"`를 보내 412. `If-Match`는 강한 비교라 약한 ETag는 무엇과도 일치하지 않는다(RFC 9110 §13.1.1) → [11-3](../11-concurrency-control-in-apis/2-summary.md).

### 8. 웹훅 세 가지

| 증상 | 원인 | 빠진 단계 | leaf |
|---|---|---|---|
| (가) `SHIPPED` 뒤 `PAID` | 도착 순서대로 덮어씀 | 3. id 중복 제거, 4. 버전·상태 전이 비교 | [09-2](../09-async-apis-and-webhooks/2-summary.md) · [26-2](../26-case-delivery-webhook/2-summary.md) |
| (나) 서명 실패 100% | 미들웨어가 파싱·재직렬화한 문자열로 검증 | 1. **원문 바이트**로 서명 검증 | [09-3](../09-async-apis-and-webhooks/2-summary.md) |
| (다) 서버 한 대만 timestamp 거부 | 그 서버의 시계 어긋남 | 2. 타임스탬프 창 — 창이 아니라 시계를 고친다 | [09-6](../09-async-apis-and-webhooks/2-summary.md) |

- 다섯 단계: 1 원문 서명 검증 → 2 타임스탬프 창 → 3 id 중복 제거 → 4 버전·상태 전이 비교 → 5 적재 성공 뒤에만 2xx.
- 09 실험 C: `그냥 덮어쓰기 최종 = PAID`, `id 중복 제거 + seq 비교 최종 = SHIPPED`.

### 9. 대시보드 0%, 사용자는 실패

| 스타일 | 원인 | 셀 지표 | leaf |
|---|---|---|---|
| REST | 실패를 200 + 에러 본문으로(03 실험 `OK_WITH_ERROR_BODY`: 집계 `2xx=10`, 그중 본문 실패 5) | 본문의 에러 표시 수, 그리고 4xx·5xx로 바꾸기 | [03-1](../03-status-codes-for-apis/2-summary.md) |
| Problem Details | 본문 `status`와 HTTP 상태 불일치 | HTTP 상태와 `status` 멤버의 불일치 건수(생성자 버그·중간자 변경의 신호). 둘의 우선순위는 RFC 9457이 정하지 않으므로 팀이 정한다 | [04-4](../04-error-format-problem-details/2-summary.md) |
| GraphQL | 부분 성공을 2xx로(`errors` + null 필드) | `errors` 수·`path`별 오류 | [17-3](../17-graphql/2-summary.md) |

### 10. 메시지가 안 맞을 때

- 메시지는 라이브러리 판·설정·로케일에 따라 다르다. 이 색인의 메시지는 각 leaf 실험 환경(예: Jackson 2.19.2, grpc-java 1.72.0, PostgreSQL 17.11)의 출력이다.
- 메시지 대신 **모양**으로 찾는다: 예외 클래스 이름, 상태 코드, 계획 노드 이름(`Seq Scan`·`Sort`), 상태 코드 이름(`UNKNOWN`·`RESOURCE_EXHAUSTED`).
- 07 실험의 예: 서버가 필드를 추가했을 때 Jackson 2.19.2 기본값은 `UnrecognizedPropertyException`, Jackson 3.0.0 기본값은 예외 없이 `OK`였다. 3.x로 올린 운영에서는 "Unrecognized field"를 검색해도 나오지 않는다 → [07-3](../07-versioning-and-compatibility/2-summary.md).
