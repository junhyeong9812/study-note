# data-engineering/09-data-contracts-and-schema-registry — 데이터 계약과 스키마 레지스트리 호환성 — 정리 (힌트)

## 해결하는 문제

주문 서비스 팀이 이벤트의 `region` 필드 이름을 `region_code`로 바꿨다. 주문 서비스의 테스트는 모두 초록이다. 다음 날 아침 분석 대시보드의 "지역별 매출"이 이렇게 보인다.

```text
  2026-10-01   KR-11 130,300   KR-26 129,900   KR-41 130,100
  2026-10-02   (NULL) 390,300                                  ← 에러 없음. 지역이 통째로 NULL
```

- 하류 변환 SQL은 `payload->>'region'`을 읽는다. 키가 없으면 PostgreSQL은 에러 대신 NULL을 준다. 그래서 잡은 성공하고 숫자만 틀린다(아래 실험).
- 원인은 "생산자와 소비자 사이에 무엇을 약속했는지"가 어디에도 적혀 있지 않고, 검사하는 곳도 없다는 것이다.
  - *데이터 계약(data contract)*: 데이터를 내보내는 쪽(생산자)과 쓰는 쪽(소비자)이 합의한 약속. 스키마(필드·타입), 의미(이 숫자가 무엇인가), 품질 기준, 갱신 주기(SLA), 소유자를 담는다.
  - *스키마 레지스트리*: 토픽·데이터셋별 스키마 버전을 저장하고, 새 버전을 등록할 때 옛 버전과의 호환성을 검사하는 서버.

쉬운 예: 택배 송장 양식이다.
- 보내는 사람이 "받는 분 주소" 칸 이름을 "배송지"로 바꿔 인쇄했다. 택배 기사의 스캐너는 "받는 분 주소" 칸을 찾다가 빈칸으로 읽는다.
- 양식을 바꾸기 전에 "이 양식을 지금 스캐너가 읽을 수 있나"를 검사하는 창구가 있었다면 인쇄 전에 막혔다.

똑같은 구조다.\
"양식" = 스키마, "검사 창구" = 레지스트리의 호환성 검사, "양식 + 칸의 뜻 + 언제까지 도착 + 문의처" = 데이터 계약이다.

실무 예:
- enum에 새 값 `PARTIALLY_REFUNDED`가 생긴다. 하류 `CASE`문이 모르는 값을 "기타"로 보내, 상태별 리포트의 "기타"가 0%에서 33%로 뛴다.
- 레지스트리 호환성을 `NONE`으로 두었다. 생산자가 필수 필드를 지운 스키마를 등록했고, 그 필드가 필요한 고정 reader 스키마(예: 생성 클래스)로 읽는 소비자가 실패한다.
- 기본 호환성 `BACKWARD`(비transitive)로 운영했다. 최신 스키마를 reader로 고정한 새 소비자를 토픽 처음부터 재생하자 오래된 레코드에서 실패한다.

## 동작·원리

### 1. 계약에 담기는 것 — 스키마만이 아니다

```text
  ┌──────────────── 데이터 계약 (예: orders 이벤트) ────────────────┐
  │ 스키마   order_id long 필수 · region string 선택(기본 null) ...   │ ← 레지스트리가 기계적으로 검사
  │ 의미     amount = 부가세 포함 원 단위, 환불은 음수 이벤트로 따로   │ ← 사람이 읽고 합의
  │ 품질     order_id 중복 0 · region NULL 비율 < 1%                │ ← 10번(품질 검사)이 실행
  │ SLA      매일 09:00까지 전날 분 도착 · 보존 3년                  │ ← 10번(신선도)이 감시
  │ 소유자   주문팀 · 변경 공지 채널                                │ ← 깨졌을 때 누구에게 묻나
  └──────────────────────────────────────────────────────────────┘
        생산자(주문팀) ── 계약 ──▶ 소비자(정산·분석·추천 팀)
```

- 스키마 호환성은 계약의 한 칸일 뿐이다. 필드 이름·타입이 그대로여도 **의미**가 바뀔 수 있다(`amount`가 부가세 포함에서 제외로).
  - 이런 변경은 레지스트리가 못 잡는다. 계약에 적고, 버전을 올리고, 공지하는 수밖에 없다.
- 공개 표준 예: Bitol **ODCS(Open Data Contract Standard)**. 2026-10 기준 문서의 최신판은 v3.2.0이다(`apiVersion: v3.2.0`, `kind: DataContract`).
  - 절 구성: Fundamentals·Schema·Data Quality·Support·Pricing·Team·Roles·Service-Level Agreement·Servers 등.
  - 품질 칸에 `metric: nullValues`, `mustBe: 0` 같은 라이브러리 지표(`nullValues`·`missingValues`·`invalidValues`·`duplicateValues`·`rowCount`)를 쓴다.
  - SLA 칸에 `latency`·`frequency`·`retention`·`timeOfAvailability` 같은 속성을 쓴다(ODCS 전체 예제 파일).

```yaml
# ODCS v3.2.0 형태를 줄인 예 (필드 이름은 ODCS 예제에서, 값은 예시)
apiVersion: v3.2.0
kind: DataContract
id: orders-events
version: 2.0.0
schema:
  - name: orders
    properties:
      - name: order_id
        logicalType: integer
        required: true
      - name: region
        logicalType: string
        quality:
          - metric: nullValues
            mustBeLessThan: 3        # (예시) 하루 NULL 3건 미만
    quality:
      - metric: rowCount
        mustBeGreaterThan: 0
team:
  name: order-team
slaProperties:
  - property: frequency
    value: 1
    unit: d
```

- `mustBeLessThan`은 ODCS 데이터 품질 절의 비교 연산자 이름을 따랐다. 연산자 전체 목록은 ODCS 문서의 Data Quality 절을 본다.

### 2. 레지스트리가 하는 일 — 등록 시점의 문지기

```text
  생산자 빌드/배포                    스키마 레지스트리                         소비자
  ─────────────────                  ───────────────────                      ─────────
  새 스키마 v3 ── 등록 요청 ──▶  subject "orders-value"
                                 v1, v2 저장됨 · 호환성 모드 BACKWARD
                                 v3 vs (v2 또는 v1·v2) 검사
                                   통과 → ID 부여 · 버전 3
                                   실패 → 409 Incompatible schema ──▶ 생산자 배포 중단
  메시지 = [0][스키마 ID 4바이트][Avro 바이트] ─────────────────────────▶  ID로 스키마 조회 → 해석
```

- Confluent 문서의 wire format(페이로드 앞에 ID를 붙이는 기본 형식): 0번 바이트 = 형식 버전(0), 1~4번 바이트 = 스키마 ID(빅엔디언), Protobuf면 메시지 인덱스, 그 뒤가 데이터.
  - Confluent Platform 8.1.1부터는 ID 대신 16바이트 GUID를 헤더에 싣는 형식도 고를 수 있다.
- *subject*: 스키마 버전들을 묶는 이름. 기본 전략 `TopicNameStrategy`는 토픽 이름에서 subject를 만든다(예: `orders-value`). 그래서 한 토픽의 모든 메시지가 한 스키마 계열을 따른다고 가정한다(Confluent "Formats, Serializers, and Deserializers").
- 레지스트리는 **바이트를 검사하지 않는다**. 등록되는 스키마 문서끼리를 비교한다. 그래서 레지스트리를 거치지 않고 JSON을 직접 쓰는 생산자에게는 아무 효과가 없다.
- 예외: Confluent의 Data Contracts 기능(Confluent Enterprise·Confluent Cloud Advanced 패키지, 7.4 이상)은 스키마에 `metadata`·`ruleSet`을 붙인다. CEL 같은 데이터 품질 규칙은 클라이언트 SerDes가 직렬화·역직렬화 때 값에 대해 실행한다(Confluent "Data Contracts" 문서). 레지스트리 서버가 아니라 클라이언트가 실행 주체다.
- Confluent `KafkaAvroDeserializer`의 기본값(`specific.avro.reader=false`)은 메시지의 스키마 ID로 가져온 **writer 스키마 그대로** `GenericRecord`를 만든다(Confluent `AbstractKafkaAvroDeserializer.getReaderSchema`). 그래서 아래의 "missing required field" 같은 해석 실패는 소비자가 별도 reader 스키마(생성 클래스 등)로 읽을 때 나온다. 기본 소비자에서는 역직렬화는 되고, 애플리케이션이 없는 필드를 쓰는 단계에서 문제가 드러날 수 있다.

### 3. 호환성 모드 — 누가 누구의 데이터를 읽나

```text
  버전 순서: X-2 → X-1 → X(새로 등록하려는 스키마)

  BACKWARD             X로 읽는 소비자 ◀── X-1로 쓴 데이터        (X-2 데이터는 보장 없음)
  BACKWARD_TRANSITIVE  X로 읽는 소비자 ◀── X-1, X-2, …로 쓴 데이터
  FORWARD              X로 쓴 데이터  ──▶ X-1로 읽는 소비자       (X-2 소비자는 보장 없음)
  FORWARD_TRANSITIVE   X로 쓴 데이터  ──▶ X-1, X-2, …로 읽는 소비자
  FULL(_TRANSITIVE)    위 두 방향 모두
  NONE                 검사 안 함

  배포 순서: BACKWARD 계열 → 소비자 먼저 · FORWARD 계열 → 생산자 먼저 · FULL 계열 → 순서 무관
```

- Confluent 문서 기준
  - 기본 호환성은 `BACKWARD`이고, 비transitive다. 문서는 그 이유로 "소비자를 토픽 처음으로 되감을 수 있게"를 든다.
  - BACKWARD는 X가 X·X-1의 데이터를 읽는 것만 보장한다. X-2는 보장하지 않는다.
  - 업그레이드 순서: BACKWARD 계열은 소비자를 먼저, FORWARD 계열은 생산자를 먼저 올린다. FULL 계열은 독립적으로 올릴 수 있다.
  - Protobuf는 `BACKWARD_TRANSITIVE`를 권한다. 새 메시지 타입 추가가 forward 호환이 아니기 때문이다.
- 판정의 바탕은 포맷의 해석 규칙이다. Avro는 reader 필드를 이름으로 writer 필드에 짝짓고, reader에만 있는 필드는 기본값을 쓴다([api-design/08](../../api-design/08-schema-and-serialization/2-summary.md) §4). 그래서 "기본값이 있느냐"가 판정을 가른다.

Confluent 문서의 Avro 규칙표(변경 → 허용 여부. "optional" = 기본값이 있는 필드):

| 변경 | BACKWARD | FORWARD | FULL |
|---|---|---|---|
| 선택 필드 추가 | ✔ | ✔ | ✔ |
| 선택 필드 삭제 | ✔ | ✔ | ✔ |
| 필수 필드 추가 | | ✔ | |
| 필수 필드 삭제 | ✔ | | |
| union 갈래 추가 | ✔ | | |
| union 갈래 삭제 | | ✔ | |
| 스칼라 타입 넓히기 | ✔ | | |
| 스칼라 타입 좁히기 | | ✔ | |

- 같은 표의 Protobuf 열은 다르다. 예를 들어 Protobuf는 스칼라 타입 넓히기·좁히기가 세 모드 모두 ✔이고, 필수 필드 추가·삭제는 셋 다 빈칸이다. 포맷마다 규칙이 다르므로 Avro 규칙을 일반 원리로 옮기지 않는다.
- JSON Schema는 `compatibilityPolicy`(lenient·strict)와 `additionalProperties`(열림·닫힘)에 따라 표가 또 달라진다(같은 문서).

### 실험: 필드 집합 비교로 판정하기 (모형)

Avro 해석 규칙을 "reader 필드마다 writer에 같은 이름이 있거나, 없으면 기본값이 있어야 한다 + 타입 승격" 한 줄로 줄인 판정기다. 실제 레지스트리가 아니라 **모형**이다(`Compat.java`, eclipse-temurin:21-jdk, OpenJDK 21.0.12).

```java
static List<String> canRead(Schema reader, Schema writer) {
    var problems = new ArrayList<String>();
    var w = writer.byName();
    for (var rf : reader.fields()) {
        var wf = w.get(rf.name());
        if (wf == null) {
            if (!rf.hasDefault()) problems.add("reader 필드 '" + rf.name() + "'가 writer에 없고 기본값도 없음");
        } else if (!promotable(wf.type(), rf.type())) {
            problems.add("'" + rf.name() + "' 타입 " + wf.type() + " → " + rf.type() + " 승격 불가");
        }
    }
    return problems;   // writer에만 있는 필드는 무시
}
// BACKWARD = canRead(새, 옛) · FORWARD = canRead(옛, 새) · FULL = 둘 다
// *_TRANSITIVE = 옛 버전 전부에 대해 반복
```

```text
== A. 변경 종류별 판정 (모형, 직전 버전과만 비교)
change                   BW  FW  FULL
Add optional field       ✔   ✔   ✔
Remove optional field    ✔   ✔   ✔
Add required field       ✘   ✔   ✘
Remove required field    ✔   ✘   ✘
Widen a scalar type      ✔   ✘   ✘
Narrow a scalar type     ✘   ✔   ✘
```

- 모형이 낸 6행이 위 Confluent Avro 표의 같은 6행과 일치했다. union 두 행은 모형에 넣지 않았다.
- 필드를 **지우는** 변경이 BACKWARD에서 통과하는 이유: 새 reader는 그 필드를 모른다. 옛 데이터에 있어도 무시하면 된다.

```text
== B. 이름 바꾸기 region → region_code
기본값 없는 새 이름  BACKWARD -> [BW vs v1: reader 필드 'region_code'가 writer에 없고 기본값도 없음]
둘 다 기본값 null    FULL     -> []  (통과)
v2로 쓴 레코드        = {region_code=KR-11, order_id=1001}
v1 소비자가 읽은 결과 = {order_id=1001, region=null}   <- region 조용히 null
```

- 이름 바꾸기는 해석 규칙에서 "옛 필드 삭제 + 새 필드 추가"다.
- 두 필드가 모두 기본값 null인 선택 필드면, 삭제도 추가도 "선택 필드" 변경이라 **FULL까지 통과한다**. 그리고 옛 소비자는 새 레코드의 `region`을 기본값 null로 읽는다.
- 즉 **호환성 검사 통과 ≠ 의미 보존**이다. 레지스트리는 "읽을 수 있나"만 보고, "같은 값이 나오나"는 보지 않는다.
- Avro에는 `aliases`(옛 이름을 별칭으로 선언)가 있다. reader 스키마의 별칭으로 writer의 옛 이름을 짝지을 수 있다. 단 명세는 구현이 이것을 "선택적으로(may optionally)" 쓴다고 적는다(Avro 1.12.0 명세 Aliases). 이 모형에는 넣지 않았다.

```text
== C. 비transitive BACKWARD의 구멍
v2 등록 BACKWARD            -> []
v3 등록 BACKWARD            -> []
v3 등록 BACKWARD_TRANSITIVE -> [BW vs v1: reader 필드 'region'가 writer에 없고 기본값도 없음]
v3 소비자가 v1 레코드를 재생 -> 실패: missing required field region
```

- 마지막 줄의 실패 문구는 모형이 던진 예외다(`Compat.java`). v3 스키마를 reader로 고정한 소비자를 흉내 낸 것이다.
- v1 `{id}` → v2 `{id, region="KR" 기본값}` → v3 `{id, region 기본값 없음}`.
- v3는 v2와만 비교하면 통과한다(v2 데이터에는 region이 있다). v1과 비교하면 실패한다.
- 토픽 보존 기간 안에 v1 레코드가 남아 있으면, v3를 reader 스키마로 고정한 소비자를 처음부터 재생하는 순간 실패한다. 커리큘럼 ⚠ 칸의 "처음부터 재생할 때 오래된 레코드를 못 읽는다"가 이것이다.

### 4. 강제 지점 — 어디서 막나

```text
  ① 생산자 CI ──▶ ② 레지스트리 등록 ──▶ ③ 직렬화기 ──▶ ④ 브로커 ──▶ ⑤ 적재·변환 ──▶ ⑥ 품질 검사
   스키마 diff       호환성 모드           등록된 스키마로   스키마 ID      컬럼 제약·      NULL 비율·
   계약 리뷰                              직렬화            검증(선택)     계약 검사 SQL   허용값(10번)
  ◀──── 앞일수록 싸게 막는다 ────────────────────────────────── 뒤일수록 "이미 들어온 뒤"에 안다 ────▶
```

- ①② 앞단: 스키마 변경 PR에서 레지스트리 호환성 검사를 돌린다(Confluent 문서는 Schema Registry Maven Plugin으로 호환성을 검사하는 방법을 든다). 생산자 배포 전에 막힌다.
- ③ 직렬화기 설정
  - `auto.register.schemas` — 직렬화기가 객체에서 스키마를 만들어 등록을 시도할지 여부.
  - `use.latest.version` — 자동 등록을 끈 상태에서, 그 subject의 최신 버전 스키마로 직렬화한다.
  - 생산자 코드가 바뀌면 운영 중에 새 스키마가 등록되는 경로가 생긴다. 그래서 등록을 CI로 옮기고 운영 직렬화기는 등록하지 않게 하는 설계를 쓰기도 한다(해석).
- ④ 브로커 쪽 스키마 ID 검증(Broker-Side Schema ID Validation)은 Confluent Cloud·Confluent Platform(Confluent Server) 기능이다. 토픽 설정 `confluent.value.schema.validation=true`로 켠다(Confluent "Schema Validation" 문서). 같은 계열 문서는 키·값이 null인 메시지는 이 검증을 통과한다고 적는다.
  - Apache Kafka 4.1의 토픽 설정 목록(`TopicConfig.java`)에는 스키마 관련 설정이 없다. 오픈소스 Kafka 브로커만으로는 이 검증이 없다.
- ⑤⑥ 뒷단: 레지스트리 밖으로 들어오는 데이터(JSON 파일, DB 추출, SaaS API)에는 이것밖에 없다. 실험 2가 이 경우다.

### 실험: 이름 바뀐 필드가 하류에서 NULL이 된다 (PostgreSQL 17)

(실험, `postgres:17` 컨테이너 — PostgreSQL 17.11, `--network none`, 합성 주문 600건)

```sql
-- 착륙 테이블: 상류 이벤트를 JSON 그대로 적재(ELT)
-- 1일차 키: order_id, region, status(PAID·SHIPPED), amount
-- 2일차 키: order_id, region_code(이름 바뀜), status(+PARTIALLY_REFUNDED), amount
CREATE TABLE fct_orders AS
SELECT load_day, (payload->>'order_id')::int AS order_id, payload->>'region' AS region,
       CASE payload->>'status' WHEN 'PAID' THEN '결제' WHEN 'SHIPPED' THEN '배송' ELSE '기타' END AS status_group,
       (payload->>'amount')::int AS amount
FROM raw_orders;
```

```text
== 일자별 지역 매출 (region NULL 행 포함)
  load_day  | region | orders | revenue
 2026-10-01 | KR-11  |    100 |  130300
 2026-10-01 | KR-26  |    100 |  129900
 2026-10-01 | KR-41  |    100 |  130100
 2026-10-02 | (NULL) |    300 |  390300
== 일자별 상태 그룹 비율
 2026-10-01 | 결제 | 150      2026-10-01 | 배송 | 150
 2026-10-02 | 결제 | 100      2026-10-02 | 기타 | 100      2026-10-02 | 배송 | 100
== inner join 차원 조인 시 2일차 매출
 2026-10-01 |    300 |  390300          ← 2일차 행이 통째로 사라짐
```

- 세 번째 출력의 제목(스크립트의 `\echo` 문구)은 "2일차 매출"이지만, 실제 쿼리는 inner join 뒤 **일자별** 매출이다. 나온 행은 1일차(390,300) 하나이고, 2일차 행은 없다.

- 스크립트 종료 코드는 0이었다. 에러는 한 줄도 없다.
- 2일차 지역이 전부 NULL이 됐다. 지역 차원과 inner join하는 리포트에서는 2일차 매출 390,300이 **행째 빠진다**(03번 차원 모델링의 "inner join으로 매출이 줄어든다"와 같은 모양).
- 새 enum 값은 `ELSE '기타'`로 흘러 "기타"가 0건에서 100건(33%)이 됐다.

같은 데이터에 계약 검사를 걸면 원인이 바로 보인다.

```sql
WITH contract(k) AS (VALUES ('order_id'),('region'),('status'),('amount')),
     seen AS (SELECT DISTINCT load_day, jsonb_object_keys(payload) AS k FROM raw_orders)
SELECT s.load_day, 'unexpected' AS kind, s.k FROM seen s WHERE s.k NOT IN (SELECT k FROM contract)
UNION ALL
SELECT d.load_day, 'missing', c.k FROM (SELECT DISTINCT load_day FROM raw_orders) d CROSS JOIN contract c
WHERE NOT EXISTS (SELECT 1 FROM seen s WHERE s.load_day = d.load_day AND s.k = c.k);
```

```text
== 계약 검사 1: 컬럼별 NULL 비율          2026-10-01 0.0 / 2026-10-02 100.0
== 계약 검사 2: 계약에 없는 키 / 사라진 키
 2026-10-02 | missing    | region
 2026-10-02 | unexpected | region_code
== 계약 검사 3: 허용값 밖 status
 2026-10-02 | PARTIALLY_REFUNDED |   100
== 강제 지점: 계약을 적재 테이블 제약으로 옮기면
INSERT 0 300
ERROR:  null value in column "region" of relation "fct_orders_strict" violates not-null constraint
DETAIL:  Failing row contains (2026-10-02, 1001, null, SHIPPED, 1100).
```

- 적재 테이블에 `NOT NULL`·`CHECK (status IN (...))`를 걸자, 조용한 NULL이 **적재 실패**로 바뀌었다. 차단할지 경고만 할지는 10번에서 다룬다.
- 주의: 이 스크립트를 psql 기본 설정으로 돌리면 ERROR가 나도 psql 종료 코드는 0이었다. `-v ON_ERROR_STOP=1`을 주자 종료 코드 3으로 끝났다(재실행 확인). 오케스트레이터가 종료 코드만 본다면 이 설정까지 있어야 실패가 실패로 보인다.

## 쓰이는 자료구조·알고리즘

- **필드 집합 비교** — Avro 레코드 필드 변경에 한한 판정 모형 = reader 필드 집합과 writer 필드 집합의 차집합 검사 + 기본값 유무 + 타입 승격표. 이름 → 필드 조회는 해시 맵([data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)).
  - BACKWARD: (새 reader 필드 − 옛 writer 필드) ⊆ 기본값 있는 필드.
  - FORWARD: (옛 reader 필드 − 새 writer 필드) ⊆ 기본값 있는 필드.
  - transitive: 위 검사를 옛 버전 n개에 반복 — 등록 비용 O(n × 필드 수).
- **버전 목록 + 전역 ID** — subject마다 버전 1, 2, 3…, 스키마 내용마다 ID. 같은 스키마가 여러 subject에 있으면 같은 ID를 쓸 수 있다(Confluent 문서).
- **계약 검사 SQL** — 키 집합 차이(`jsonb_object_keys` × 계약 목록), NULL 비율, 허용값 밖 개수. 10번의 품질 검사와 같은 "실패 행을 고르는 쿼리" 형태다.

## 적용 — 풀어나가는 법

### 1. 증상에서 출발

| 증상 | 먼저 볼 것 | 확인 방법 |
|---|---|---|
| 특정 날부터 한 컬럼이 전부 NULL | 상류 필드 이름·경로 변경 | 원천 JSON 키 집합 diff(계약 검사 2) |
| "기타"·"Unknown" 비율 급증 | enum 새 값 | 허용값 밖 값 목록(계약 검사 3) |
| 소비자 `SerializationException`·역직렬화 실패 | 호환성 모드 `NONE`·필수 필드 삭제 | 레지스트리 `GET /config/{subject}`, 버전 diff |
| 재처리·새 소비자만 실패 | 비transitive 모드 | 실패 레코드의 스키마 ID → 그 버전과 현재 버전 비교 |
| 숫자 크기가 갑자기 1000배 | 단위 의미 변경(원 → 천 원) | 계약 문서 버전 이력 — 레지스트리로는 안 보임 |

### 2. 호환성 모드 고르기

- 소비자가 **처음부터 재생**할 일이 있다(새 소비자 추가, 재처리, 07번 Kappa) → `BACKWARD_TRANSITIVE` 또는 `FULL_TRANSITIVE`.
- 생산자와 소비자 배포 순서를 통제할 수 없다(팀이 다름) → `FULL` 계열.
- `NONE`은 토픽을 새로 만들어 옮기는 일회성 전환 때만 잠깐 쓴다. 호환 불가 변경이 꼭 필요하면 Confluent 문서도 "새 토픽을 만들어 옮기는" 쪽을 든다.

### 3. 이름을 바꿔야 할 때 — expand/contract

```text
  v1 {region}                   ① expand: v2 {region, region_code} 둘 다 채워 보냄
                                ② 소비자들이 region_code로 이전(계보 11번으로 소비자 목록 확인)
                                ③ contract: v3 {region_code} — region 삭제(선택 필드라 BACKWARD 통과)
```

- DB 컬럼 이름 바꾸기와 같은 절차다([database/26-schema-migration](../../database/26-schema-migration/2-summary.md) §4 expand/contract).
- ③을 계약 버전의 메이저 변경으로 공지하고, 이전 기간을 계약 SLA에 적는다.

### 4. 소비자 쪽 방어 — 모르는 값을 숨기지 않는다

```java
// 취약: 모르는 상태를 조용히 "기타"로
String group = switch (status) { case "PAID" -> "결제"; case "SHIPPED" -> "배송"; default -> "기타"; };

// 고친 판: 모르는 값은 따로 세고, 비율이 넘으면 알린다
enum Group { PAID, SHIPPED, UNKNOWN }
Group group = switch (status) {
    case "PAID" -> Group.PAID;
    case "SHIPPED" -> Group.SHIPPED;
    default -> { unknownStatus.increment(status); yield Group.UNKNOWN; }   // 지표: 값별 카운터
};
```

- "기타"는 집계의 한 범주라 리포트에서 정상처럼 보인다. `UNKNOWN`은 따로 세어 10번의 분포 검사가 잡게 한다.
- 위 코드는 설명용 조각이다(`unknownStatus`는 가상의 카운터). 이 노트에서 실행하지 않았다.

### 5. 진단 명령 (Confluent Schema Registry REST API 형태)

```bash
curl -s "$SR/config/orders-value?defaultToGlobal=true" # 실제 적용되는 호환성 모드(subject 설정이 없으면 전역)
curl -s $SR/subjects/orders-value/versions             # 등록 버전 목록
curl -s $SR/subjects/orders-value/versions/2/schema    # 특정 버전 스키마
curl -s -X POST -H 'Content-Type: application/vnd.schemaregistry.v1+json' \
  --data @candidate.json "$SR/compatibility/subjects/orders-value/versions?verbose=true"   # 등록 전 검사(등록과 같은 범위)
```

- 경로는 Confluent "Schema Registry API Reference"에서 확인했다. `GET /config/{subject}`에 `defaultToGlobal=true`를 주지 않으면 subject에 직접 설정된 값만 본다. `POST /compatibility/subjects/{subject}/versions`는 등록과 같은 검사를 한다 — transitive 모드면 모든 옛 버전과 비교한다. `.../versions/latest`는 최신 버전 하나와만 비교하므로 실험 C 같은 v1 비호환을 놓칠 수 있다. 호환성 검사 응답은 `is_compatible`(불리언)이고, `verbose=true`면 이유 목록 `messages`가 붙는다. 호환되지 않는 스키마를 `POST /subjects/{subject}/versions`로 등록하면 `409 Conflict – Incompatible schema`다.
- 이 노트에서는 Schema Registry를 띄우지 않았다. 위 동작은 문서 기준이다.

## 장애 시나리오와 대처

### 1. 상류 컬럼 이름 변경 → 하류 컬럼이 조용히 NULL (⚠ 커리큘럼)

- 현상: 지역별 매출 대시보드에서 특정 날부터 지역이 "(NULL)" 하나로 합쳐진다. 차원과 inner join하는 리포트는 그날 매출이 통째로 빠진다.
- 보이는 형태: 잡 성공, 에러 로그 없음. `region` NULL 비율 0% → 100%(실험). 원천 키 집합에 `region_code`가 새로 나타남.
- 원인: 생산자가 필드 이름을 바꿨다. JSON 경로 접근은 없는 키를 NULL로 돌려준다. 레지스트리를 쓰더라도, 옛·새 필드가 모두 선택 필드면 호환성 검사를 통과한다(모형 실험 B).
- 대처: 즉시 — 변환 SQL이 두 키를 `coalesce(payload->>'region_code', payload->>'region')`로 읽게 고치고 해당 기간을 재적재(08번 파티션 덮어쓰기). 재발 방지 — 계약에 필수 필드로 명시, 적재 계약 검사(키 diff·NULL 비율), 이름 변경은 expand/contract.

### 2. enum 새 값 → "기타" 급증 (⚠ 커리큘럼)

- 현상: 주문 상태 리포트의 "기타"가 평소 0%에서 33%로 뛴다(실험).
- 원인: 상류가 `PARTIALLY_REFUNDED`를 추가했다. 하류 `CASE`의 `ELSE '기타'`가 흡수했다. Avro에서도 reader enum에 없는 기호는 reader의 enum 기본값으로 바뀐다(Avro 명세 — [api-design/08](../../api-design/08-schema-and-serialization/2-summary.md) §4).
- 대처: 허용값 검사(계약 검사 3)를 경고로 걸고, 소비자에서 `UNKNOWN`을 따로 센다. enum 값 추가를 계약 변경 공지 대상으로 둔다.

### 3. 호환성 `NONE` → 소비자 역직렬화 실패 (⚠ 커리큘럼)

- 현상: 생산자 배포 직후 소비자 lag이 쌓이고, 소비자 로그에 역직렬화 예외가 반복된다.
- 보이는 형태: 별도 reader 스키마로 읽는 Avro 소비자라면 `missing required field` 같은 해석 실패(api-design/08 실험 문구 `AvroTypeException: ... missing required field email`). 기본 `GenericRecord` 소비자는 writer 스키마로 읽으므로, 없는 필드를 쓰는 애플리케이션 코드에서 드러날 수 있다.
- 원인: 검사가 꺼져 있어 기본값 없는 필드 추가·필수 필드 삭제가 그대로 등록됐다.
- 대처: 즉시 — 생산자 롤백(옛 스키마로 쓰기), 이미 쓰인 새 레코드는 새 스키마를 아는 임시 소비자로 옮기거나 건너뛰기 결정. 재발 방지 — subject 호환성을 BACKWARD 이상으로, CI에서 등록 전 검사.

### 4. 비transitive `BACKWARD` → 재생할 때만 실패 (⚠ 커리큘럼)

- 현상: 운영 소비자는 멀쩡한데, 새 분석 소비자를 `earliest`로 붙이거나 재처리를 돌리면 특정 오프셋에서 실패한다.
- 보이는 형태(최신 스키마를 reader로 고정한 소비자 기준): 실패 레코드의 스키마 ID가 오래된 버전(v1)이다. v3는 v2와만 검사되어 등록됐다(모형 실험 C).
- 원인: Confluent 기본 모드 `BACKWARD`는 직전 버전과만 비교한다.
- 대처: 즉시 — 그 소비자가 해당 필드에 기본값을 주도록 reader 스키마를 고친다. 재발 방지 — 재생이 있는 토픽은 `BACKWARD_TRANSITIVE`. 이미 섞인 토픽은 보존 기간이 옛 레코드를 밀어낼 때까지, 또는 새 토픽으로 옮길 때까지 위험이 남는다.

### 5. 의미 변경 — 스키마는 그대로, 숫자만 다르다

- 현상: 매출이 하루 사이 약 10% 떨어진다. 주문 수는 그대로다.
- 원인(예시): `amount`의 의미가 부가세 포함에서 제외로 바뀌었다. 타입·이름은 같아 레지스트리·계약 검사 1~3 모두 통과한다.
- 대처: 계약의 "의미" 칸과 버전 이력, 변경 공지 채널. 분포 검사(10번 — 주문당 평균 금액의 급변)가 사후 신호가 된다.

## 핵심 문장

- 데이터 계약은 스키마·의미·품질·SLA·소유자를 함께 적은 약속이다. 레지스트리의 등록 시 호환성 검사는 그중 스키마 칸만 기계적으로 검사한다(Confluent의 계약 규칙 기능을 쓰면 값 검증도 붙지만, 실행은 클라이언트 SerDes다).
- Avro 레코드 필드 변경에 한하면 호환성 판정은 필드 집합 비교로 볼 수 있다(모형 — 실제 판정은 포맷별 해석 규칙을 따른다). BACKWARD는 "새 스키마로 옛 데이터를 읽나", FORWARD는 "옛 스키마로 새 데이터를 읽나"이고, 기본값 유무가 결과를 가른다.
- 호환성 검사 통과는 의미 보존이 아니다. 기본값 있는 필드의 이름 바꾸기는 FULL까지 통과하고, 옛 소비자는 그 값을 조용히 null로 읽는다.
- Confluent 기본 `BACKWARD`는 직전 버전과만 비교한다. 처음부터 재생하는 소비자가 있으면 transitive 모드를 쓴다.
- 레지스트리 밖으로 들어오는 데이터는 적재 시점의 계약 검사(키 diff·NULL 비율·허용값·제약)로 막는다. 앞단에서 막을수록 싸다.

## 관련 주제·근거

- 선행
  - [01-system-of-record-and-derived-data](../01-system-of-record-and-derived-data/2-summary.md) — 이 영역 앞 노트
  - [api-design/08-schema-and-serialization](../../api-design/08-schema-and-serialization/2-summary.md) — Avro writer/reader 해석, Protobuf 번호·`reserved`
  - [testing/13-contract-testing](../../testing/13-contract-testing/2-summary.md) — 소비자 주도 계약(예제 기반)과의 차이
- 후속·연결
  - [10-data-quality-and-data-observability](../10-data-quality-and-data-observability/2-summary.md) — 계약의 품질·SLA 칸을 실행하는 곳
  - [11-data-lineage](../11-data-lineage/2-summary.md) — 스키마를 바꾸기 전에 소비자 목록·영향 범위 찾기
  - [15-data-mesh-and-data-products](../15-data-mesh-and-data-products/2-summary.md) — 계약을 데이터 제품의 인터페이스로
  - [api-design/07-versioning-and-compatibility](../../api-design/07-versioning-and-compatibility/2-summary.md), [database/26-schema-migration](../../database/26-schema-migration/2-summary.md)(expand/contract), [distributed/22-event-sourcing](../../distributed/22-event-sourcing/2-summary.md)(옛 이벤트 버전 다루기), [distributed/17-queues-logs-and-delivery-semantics](../../distributed/17-queues-logs-and-delivery-semantics/2-summary.md)
- 근거
  - Confluent "Schema Evolution and Compatibility for Schema Registry on Confluent Platform"(문서 표기 Confluent Platform 8.3, 2026-10-07 열람) — 호환성 유형 정의, 기본 BACKWARD·비transitive, Avro/Protobuf/JSON Schema 규칙표, 업그레이드 순서, Protobuf BACKWARD_TRANSITIVE 권장 <https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html>
  - Confluent "Schema Registry API Reference" — `GET /config/{subject}`(`defaultToGlobal`), `POST /compatibility/subjects/{subject}/versions`(등록과 같은 검사)·`.../versions/{version}`(`is_compatible`·`verbose`), 등록 409 <https://docs.confluent.io/platform/current/schema-registry/develop/api.html>
  - Confluent "Formats, Serializers, and Deserializers" — wire format(0번 바이트·4바이트 ID·빅엔디언), 8.1.1 헤더 GUID, `TopicNameStrategy`, `auto.register.schemas`·`use.latest.version` <https://docs.confluent.io/platform/current/schema-registry/fundamentals/serdes-develop/index.html>
  - Bitol ODCS v3.2.0 — 절 구성, Data Quality 라이브러리 지표, 전체 예제 파일(`slaProperties`·`team`·`quality`) <https://bitol-io.github.io/open-data-contract-standard/latest/>
  - Confluent "Data Contracts for Schema Registry" — `metadata`·`ruleSet`, CEL 품질 규칙의 클라이언트 실행, Enterprise·Advanced 요건 <https://docs.confluent.io/platform/current/schema-registry/fundamentals/data-contracts.html> · Confluent `AbstractKafkaAvroDeserializer.java`(기본 reader = writer 스키마) <https://github.com/confluentinc/schema-registry/blob/master/avro-serializer/src/main/java/io/confluent/kafka/serializers/AbstractKafkaAvroDeserializer.java>
  - Apache Avro 1.12.0 Specification — Schema Resolution(이름 짝짓기·기본값·승격·enum 기본값·aliases) <https://avro.apache.org/docs/1.12.0/specification/>
  - Confluent "Validate Broker-side Schemas IDs" — `confluent.value.schema.validation` <https://docs.confluent.io/platform/current/schema-registry/schema-validation.html> · Apache Kafka 4.1 `TopicConfig.java`(스키마 설정 없음) <https://github.com/apache/kafka/blob/4.1/clients/src/main/java/org/apache/kafka/common/config/TopicConfig.java>
- 실험 목록
  - 호환성 판정 모형(변경 6종 × BW/FW/FULL, 이름 변경, 비transitive 구멍) — `Compat.java`, eclipse-temurin:21-jdk(OpenJDK 21.0.12), `--network none`
  - JSON 착륙 → 변환에서 이름 변경 NULL·enum "기타"·inner join 누락, 계약 검사 SQL 3종, NOT NULL·CHECK 강제(psql 기본 종료 코드 0 vs `ON_ERROR_STOP=1` 종료 코드 3) — postgres:17(PostgreSQL 17.11) 일회용 컨테이너, `--network none`, 합성 주문 600건
