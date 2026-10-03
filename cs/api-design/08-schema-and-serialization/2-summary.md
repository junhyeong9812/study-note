# api-design/08-schema-and-serialization — JSON·Protobuf·Avro와 스키마 진화 — 정리 (힌트)

## 해결하는 문제

메모리 속 객체는 프로세스 밖으로 그대로 나갈 수 없다. 바이트로 바꿔 보내고, 받는 쪽이 같은 뜻으로 되살려야 한다.

```text
  보내는 쪽 (Java)                 선 위                       받는 쪽 (JS·Go·다른 버전의 Java)
  Order{id=9007199254740993,  ─▶  바이트 열  ─▶  누가, 어떤 스키마로, 어떤 숫자 타입으로 읽나?
        amount=5000}
```

- *직렬화(serialization)*: 메모리 객체 → 바이트. *역직렬화*: 바이트 → 객체.
- *스키마*: 바이트의 어디가 무슨 필드이고 무슨 타입인지에 대한 약속.
- 문제는 두 가지다.
  - **타입 체계가 다르다** — Java `long`은 64비트 정수지만 JS `Number`는 64비트 부동소수점이다.
  - **스키마가 시간이 지나며 바뀐다** — 쓰는 쪽과 읽는 쪽이 다른 판의 스키마를 가진 채 함께 돈다([07](../07-versioning-and-compatibility/2-summary.md)).

쉬운 예: 서식이 정해진 신청서다.
- 칸 이름이 적힌 신청서(JSON)는 누구나 읽지만 종이가 두껍다.
- 칸 번호만 적힌 신청서(Protobuf)는 얇다. 대신 번호표가 없으면 못 읽고, 번호의 뜻을 바꾸면 엉뚱하게 읽는다.
- 칸 이름도 번호도 없이 순서대로 적은 신청서(Avro)는 가장 얇다. 대신 쓴 사람이 쓴 양식을 같이 받아야 읽는다.

똑같은 구조다.\
실무 예: 주문 ID `1234567890123456789`가 브라우저에서 `1234567890123456800`이 된다. 삭제한 Protobuf 필드 번호를 새 필드에 재사용했더니, 구 서비스가 보낸 금액이 새 서비스에서 사용자 ID로 읽힌다.

## 동작·원리

### 1. 세 갈래 — 같은 레코드, 다른 바이트

(실험, protobuf-java 3.25.5 · Avro 1.12.0 · Jackson 2.19.2, JDK 21.0.11, 2026-10-04) — 레코드 `{id=1, amount=5000}`

```text
JSON=22B {"id":1,"amount":5000} | protobuf=5B [08 01 10 88 27] | avro=3B [02 90 4e]
```

```text
  JSON       {"id":1,"amount":5000}       필드 이름이 바이트에 들어 있다 (자기 기술)
  Protobuf   08 01 | 10 88 27              [태그=필드번호·타입][값] — 이름 대신 번호
             ↑id=1   ↑amount=5000
  Avro       02 | 90 4e                    태그도 이름도 없다 — 스키마 순서대로 값만
             ↑1  ↑5000   (zigzag varint)
```

| | JSON | Protobuf | Avro |
|---|---|---|---|
| 필드 식별 | 이름 | 번호(태그) | 스키마의 순서(읽을 때는 이름으로 맞춤) |
| 스키마 없이 읽기 | 가능 | 대략 가능(번호·와이어 타입만) | 불가 — 쓴 쪽 스키마 필요 |
| 정수 | 숫자 하나(정밀도는 구현 몫) | int32·int64·sint·fixed 구분 | int·long(zigzag varint) |
| 진화 규칙 | 관례(모르는 필드 무시) | 번호 재사용 금지·`reserved` | writer/reader 스키마 해석 + 기본값 |

### 2. JSON 숫자와 2^53

```text
  JS Number = IEEE 754 binary64: 가수 53비트
  2^53 - 1 = 9007199254740991 = Number.MAX_SAFE_INTEGER
  그 위로는 정수 사이에 빈칸이 생긴다:  ...990, 991, 992, (993 없음), 994, ...
```

- RFC 8259 §6
  - binary64를 쓰는 구현이 흔하므로, 그 이상의 정밀도를 기대하지 않으면 상호운용이 좋다.
  - [-(2^53)+1, (2^53)-1] 범위의 정수는 "구현들이 값에 정확히 합의한다"는 뜻에서 상호운용 가능하다.
  - 구현은 받는 숫자의 범위·정밀도에 한계를 둘 수 있다.
- 즉 JSON 문법은 큰 정수를 허용하지만, **읽는 쪽의 숫자 타입**이 값을 바꾼다. 이것은 문법 문제가 아니라 계층 간 타입 불일치다.

### 실험: 64비트 ID를 JSON 숫자로 보내면

(실험, node:22-alpine — Node v22.23.2, 2026-10-04)

```javascript
const o = JSON.parse('{"id":9007199254740993,"idStr":"9007199254740993","orderId":1234567890123456789}');
```

```text
node v22.23.2
MAX_SAFE_INTEGER = 9007199254740991
id      -> 9007199254740992  safe? false
orderId -> 1234567890123456800
idStr   -> 9007199254740993  BigInt: 9007199254740993
9007199254740993 === 9007199254740992 -> true
re-serialize -> {"id":9007199254740992,"idStr":"9007199254740993","orderId":1234567890123456800}
reviver context.source -> 9007199254740993
```

- 에러 없이 끝자리가 바뀐다. 다시 직렬화하면 **바뀐 값이 서버로 돌아간다**. 이 ID로 조회하면 다른 주문이나 404가 된다.
- 문자열로 보낸 `idStr`은 그대로다.
- Node 22.23.2에서는 `JSON.parse` reviver의 세 번째 인자 `context.source`로 원문 숫자 텍스트를 받을 수 있었다. 이것으로 BigInt를 만들 수 있지만, 모든 클라이언트 런타임이 지원한다고 기대할 수는 없다.
- 서버 쪽 대처(Jackson 2.19.2에서 확인)

```java
public record Order(@JsonFormat(shape = JsonFormat.Shape.STRING) long id, long amount) {}
```

```text
숫자 그대로 : {"id":9007199254740993,"amount":5000}
id만 문자열: {"id":"9007199254740993","amount":5000}
다시 읽기   : Order[id=9007199254740993, amount=5000]
```

- Protobuf의 JSON 매핑(ProtoJSON)도 `int64`·`fixed64`·`uint64`를 **10진 문자열**로 낸다(protobuf.dev "ProtoJSON Format"). 같은 문제를 같은 방법으로 피한 것이다.

### 3. Protobuf 와이어 형식 — 번호가 정체성이다

```text
  메시지 = [태그][값] [태그][값] ...        (TLV — 모르는 태그는 길이만 보고 건너뛸 수 있다)
  태그   = (필드 번호 << 3) | 와이어 타입
           와이어 타입 0=VARINT 1=I64 2=LEN 5=I32
  예) 필드 2, VARINT → (2<<3)|0 = 0x10
```

- *varint*: 7비트씩 끊어 작은 자리부터 담고, 바이트의 최상위 비트(MSB)를 "뒤에 더 있음" 표시로 쓴다. 작은 수는 1바이트, 큰 수는 최대 10바이트.
- 필드 번호 1~15는 태그가 1바이트, 16~2047은 2바이트다(proto3 가이드).

(실험, protobuf-java 3.25.5, `message Num { int32 i = 1; sint32 s = 2; int64 big = 16; }`)

```text
i=1                               2B  08 01
i=150                             3B  08 96 01
i=300                             3B  08 ac 02
i=-1 (int32)                     11B  08 ff ff ff ff ff ff ff ff ff 01
s=-1 (sint32)                     2B  10 01
s=1 (sint32)                      2B  10 02
big=1 (field 16)                  3B  80 01 01
i=0 (기본값)                         0B  
```

- 150 → `96 01`은 protobuf.dev 인코딩 문서의 예와 같다.
- `int32`의 -1은 2의 보수라 **10바이트 값 + 태그 = 11바이트**다. `sint32`는 zigzag로 -1 → 1이 되어 1바이트 값이다.
  - *zigzag*: 부호 있는 수를 0, -1, 1, -2, 2, … → 0, 1, 2, 3, 4, …로 접어 작은 절댓값을 작은 수로 만든다. 양수 p → 2p, 음수 n → 2|n|-1.
- 필드 16은 태그가 2바이트(`80 01`)다.
- `i=0`은 **0바이트** — proto3의 암묵적 존재(implicit presence) 필드는 기본값을 선에 싣지 않는다. 그래서 "0으로 설정함"과 "설정 안 함"을 구분할 수 없다(protobuf.dev "Field Presence"). 구분이 필요하면 proto3 `optional`(protoc 3.15.0부터 기본 허용)을 쓴다.

### 실험: 필드 번호 재사용 → 조용한 오역

```protobuf
// v1                                   // v2 — amount를 지우고 번호 2를 user_id에 재사용(잘못된 변경)
message Order {                         message Order {
  int64 id = 1;                           int64 id = 1;
  int64 amount = 2;                       int64 user_id = 2;
  string currency = 3;                    string currency = 3;
  Status status = 4;                      Status status = 4;
  enum Status { STATUS_UNSPECIFIED = 0;   string memo = 5;
                PAID = 1; }               enum Status { STATUS_UNSPECIFIED = 0; PAID = 1; REFUNDED = 2; }
}                                       }
```

```text
== 2. 필드 번호 재사용: v1이 amount(2)=5000으로 쓰고 v2가 user_id(2)로 읽는다
v1 bytes                         12B  08 01 10 88 27 1a 03 4b 52 57 20 01
v2 parse -> 예외 없음, user_id=5000 currency=KRW status=PAID
```

- 선 위에는 이름이 없다. 번호 2에 varint 5000이 있을 뿐이다. 그래서 파서는 **오류 없이** 금액을 사용자 ID로 읽는다.
- proto3 가이드: 번호 재사용은 디코딩을 모호하게 만들고, 결과는 파싱 오류(가장 나은 경우)부터 개인정보 유출·데이터 오염까지 간다. 필드를 지우면 번호를 `reserved`로 막으라고 한다.

```protobuf
message Order {
  reserved 2;
  reserved "amount";
  int64 id = 1;
  int64 user_id = 2;   // 컴파일 오류가 나야 정상
}
```

(실험, protoc `libprotoc 25.5`)

```text
order_v2_reserved.proto:4:12: Field "user_id" uses reserved number 2.
order_v2_reserved.proto:4:12: Suggested field numbers for exp.bad.Order: 3
exit=1
```

### 실험: 모르는 필드·모르는 enum 값을 구 리더가 받으면

```text
== 3. 새 필드·새 enum 값을 구 리더가 받는다
v1 parse -> status=UNRECOGNIZED statusValue=2 unknownFields=[5]
v1이 고쳐 다시 쓴 것을 v2가 읽음 -> memo=gift status=REFUNDED currency=USD
JSON(Jackson, 모르는 필드 무시) 왕복 -> {"id":7,"amount":5000,"status":"PAID"}
```

- v1(Java)은 모르는 enum 값 2를 `UNRECOGNIZED`로 받고, 원래 숫자는 `getStatusValue()`로 남긴다(proto3 열린 enum).
- 모르는 필드 5(`memo`)는 unknown field로 보존된다. v1 서비스가 메시지를 고쳐 다시 보내도 v2가 `memo=gift`·`REFUNDED`를 되찾는다.
  - *unknown field 보존*: 파서가 모르는 태그를 버리지 않고 들고 있다가 직렬화할 때 다시 쓴다. 현재 proto3 가이드 기준 동작이다.
  - proto3가 처음부터 그랬던 것은 아니다. 초기 proto3는 파싱할 때 모르는 필드를 버렸고, protobuf 3.5.0(2017-11-09) 릴리스부터 Java·C++·Python 등 대부분의 구현이 기본으로 보존한다(protobuf `CHANGES.txt` 3.5.0: "Unknown fields are now preserved in proto3 for most of the language implementations"). 3.5 이전 런타임이 중계에 끼어 있으면 새 필드가 사라질 수 있다.
  - 같은 가이드가 보존이 깨지는 경우로 **JSON으로 직렬화할 때**와 **필드를 하나씩 복사해 새 메시지를 만들 때**를 든다.
- JSON + Jackson(모르는 필드 무시)은 중계하면서 `memo`를 **잃었다**. 관대한 읽기와 보존은 다른 것이다.

### 4. Avro — writer 스키마와 reader 스키마

```text
  writer 스키마(쓴 쪽)  {id: long, amount: long}      바이트: 02 90 4e  (값만, 순서대로)
          │
          ▼  스키마 해석(resolution): 이름으로 짝짓기
  reader 스키마(읽는 쪽) {id: long, amount: long, email: string = ""}
          → writer에 없는 email은 reader의 기본값으로
```

- Avro 1.12.0 명세의 해석 규칙
  - 필드는 **이름으로** 짝짓는다. 순서가 달라도 된다.
  - writer에만 있는 필드는 무시한다.
  - reader에만 있는 필드는 기본값을 쓰고, 기본값이 없으면 오류다.
  - 승격: int → long·float·double, long → float·double, float → double, string ↔ bytes.
  - enum: writer의 기호가 reader에 없으면 reader의 enum 기본값, 없으면 오류.
- 바이트에 태그가 없으니 **쓴 쪽 스키마 없이는 한 바이트도 못 읽는다**. 그래서 Avro 파일은 헤더에 스키마를 싣고, 메시지 시스템은 스키마 레지스트리에 스키마를 두고 ID만 싣는 방식을 쓴다(레지스트리 상세는 data-engineering/09 — 미작성).

(실험, Avro 1.12.0 `GenericDatumReader(writer, reader)`)

```text
avro bytes (id=1, amount=5000)    3B  02 90 4e
reader: email 추가(default "") -> OK {"id": 1, "amount": 5000, "email": ""}
reader: email 추가(default 없음) -> AvroTypeException: Found Order, expecting Order, missing required field email
reader: 순서 바꿈 + amount long→double -> OK {"amount": 5000.0, "id": 1}
reader: amount 삭제 -> OK {"id": 1}
```

### 5. 진화 규칙 요약

| 변경 | JSON(관대한 리더) | Protobuf | Avro |
|---|---|---|---|
| 필드 추가 | 구 리더가 무시 | 구 리더가 unknown으로 보존 | reader에 기본값 있으면 OK |
| 필드 삭제 | 구 리더는 null·0 | 번호 `reserved` 필수 | 구 reader에 기본값 있어야 OK |
| 이름 변경 | 파괴 | 와이어엔 무관, JSON 매핑·코드엔 파괴 | 파괴(별칭 `aliases`로 완화) |
| 번호 재사용 | — | 조용한 오역 | — |
| 타입 변경 | 리더 구현 따라 | 호환 묶음 안에서만(int32·uint32·int64·uint64·bool 등) | 승격 규칙 안에서만 |

- Avro `aliases`는 명세에 있는 기능이지만 이 노트에서 실험하지 않았다.

## 쓰이는 자료구조·알고리즘

- **varint(가변 길이 정수)** — 7비트씩 끊고 MSB를 연속 표시로 쓴다.

```java
static byte[] varint(long v) {                 // unsigned 64비트로 취급
    var out = new java.io.ByteArrayOutputStream();
    while ((v & ~0x7FL) != 0) { out.write((int) ((v & 0x7F) | 0x80)); v >>>= 7; }
    out.write((int) v);
    return out.toByteArray();                  // 300 → ac 02
}
static long zigzag(long n) { return (n << 1) ^ (n >> 63); }   // -1 → 1, 1 → 2
```

- **TLV(Tag-Length-Value)** — 모르는 태그를 길이만 보고 건너뛰는 구조. forward 호환의 바탕이다.
- **이름 → 위치 해시 맵** — Avro 스키마 해석은 reader 필드 이름으로 writer 필드를 찾는 조회다.
- **IEEE 754 binary64** — 가수 53비트. 2^53 위에서 정수 간격이 2 이상이 된다.
- 관련: 키 비트 배치와 64비트 ID는 [database/28-key-strategy-surrogate-natural-public-id](../../database/28-key-strategy-surrogate-natural-public-id/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 형식 고르기

| 상황 | 고르는 것 | 이유 |
|---|---|---|
| 공개 HTTP API, 브라우저 클라이언트 | JSON | 사람이 읽고, 브라우저를 포함한 대부분의 런타임이 기본으로 읽는다 |
| 내부 서비스 간 RPC | Protobuf(gRPC) | 작고, 코드 생성, 진화 규칙이 명확([15](../15-rpc-and-grpc/2-summary.md)) |
| 대용량 레코드 저장·이벤트 스트림 | Avro(+레지스트리) 또는 Protobuf | 레코드마다 이름을 싣지 않는다, 스키마를 중앙에서 검사 |

### 2. JSON API 규칙

1. 64비트 정수 ID는 **문자열**로 낸다. 처음부터 문자열이면 나중에 바꿀 일이 없다(Stripe의 `ch_…` 같은 접두어 ID도 문자열이다).
2. 금액은 부동소수점이 아니라 최소 단위 정수(원·센트) 또는 10진 문자열로 낸다.
3. 응답 읽기는 관대하게, 요청 검증은 엄격하게 매퍼를 나눈다([07](../07-versioning-and-compatibility/2-summary.md)).
4. 중계 서비스는 모르는 필드를 버리지 않게 `Map`/`JsonNode`로 통과시키거나, 중계하지 말고 원문을 넘긴다.

### 3. Protobuf 규칙

1. 필드를 지우면 번호와 이름을 `reserved`로 막는다(실험: protoc가 재사용을 거부).
2. 필드 번호·타입을 바꾸지 않는다. 바꿔야 하면 새 번호로 새 필드를 만든다.
3. enum은 0번을 `XXX_UNSPECIFIED`로 둔다(proto3: 첫 값은 0이어야 한다).
4. 0과 "안 보냄"을 구분해야 하는 필드(부분 갱신의 할인율 등)는 `optional`.
5. 자주 쓰는 필드에 1~15번을 준다.
6. PR마다 이전 `.proto`와 비교해 파괴적 변경을 막는다(Buf CLI의 `buf breaking` 같은 도구 — 이 노트에서는 실행하지 않았다).

### 4. 진단

```bash
# 바이너리 protobuf를 스키마 없이 들여다보기 — 번호·와이어 타입만 보인다
protoc --decode_raw < order.bin
# JSON 응답에서 16자리 이상 숫자 ID 찾기 (2^53 ≈ 9.0e15 — 16자리)
curl -s https://api.example.com/orders | grep -oE '"[a-z_]*id":[0-9]{16,}'
```

## 장애 시나리오와 대처

### 1. 64비트 ID를 JSON 숫자로 → JS에서 정밀도 손실 (⚠ 커리큘럼)

- 현상: 웹 화면에서 주문 상세를 열면 가끔 404이거나 다른 주문이 뜬다. 모바일 앱(Java·Kotlin)에서는 정상이다.
- 보이는 형태: 서버 로그에 존재하지 않는 ID(끝자리가 0이나 짝수로 바뀐 값)로 조회한 기록.
- 원인: ID가 2^53-1을 넘었다. JS `JSON.parse`가 binary64로 읽으며 가까운 표현 가능한 값으로 바꾼다(실험: …993 → …992). ID가 작을 때는 문제가 안 보이다가 시퀀스·Snowflake ID가 커지면서 드러난다.
- 대처: ID를 문자열로 낸다(`@JsonFormat(shape = STRING)` 실험). 이미 숫자로 낸 API는 문자열 필드를 **추가**하고 숫자 필드를 폐기 절차로 내린다([07](../07-versioning-and-compatibility/2-summary.md)).

### 2. 필드 번호 재사용 → 조용한 오역 (⚠ 커리큘럼)

- 현상: 배포 중 일부 주문의 `user_id`가 5000·12000 같은 금액 모양 숫자로 저장된다.
- 보이는 형태: 파싱 에러 없음. 데이터 이상 탐지·고객 문의로 발견된다.
- 원인: 구 서비스가 번호 2를 `amount`로 쓰고, 새 서비스가 번호 2를 `user_id`로 읽었다(실험).
- 대처: 즉시 — 새 서비스 롤백, 오염된 기간의 레코드 식별. 재발 방지 — 삭제한 번호·이름을 `reserved`로, CI에서 `.proto` 파괴적 변경 검사.

### 3. 중계 서비스가 새 필드를 지운다

- 현상: 주문 서비스가 `memo`를 넣어 보냈는데, 게이트웨이·BFF를 거친 뒤 배송 서비스에서는 비어 있다.
- 원인: 중간 서비스가 구 스키마의 DTO로 역직렬화 → 재직렬화하며 모르는 필드를 버렸다(실험: Jackson 왕복에서 `memo` 소실). Protobuf도 JSON으로 바꾸거나 필드를 복사해 새 메시지를 만들면 잃는다(proto3 가이드).
- 대처: 중계 지점은 원문 통과·unknown 보존 경로를 쓰거나, 새 필드를 쓰기 전에 중계 서비스를 먼저 배포한다.

### 4. Avro 새 필드에 기본값이 없다

- 현상: 소비자를 새 스키마로 배포하자 옛 레코드를 읽는 순간 실패한다.
- 보이는 형태: `AvroTypeException: Found Order, expecting Order, missing required field email`(실험 문구).
- 원인: reader에만 있는 필드에 기본값이 없다(Avro 명세의 해석 규칙).
- 대처: 새 필드에 기본값을 둔다. 레지스트리의 호환성 검사로 배포 전에 막는다.

### 5. proto3에서 0과 "안 보냄"이 섞인다

- 현상: 부분 갱신 API로 할인율을 0으로 바꾸려 했는데 바뀌지 않는다. 또는 안 보낸 필드가 0으로 덮인다.
- 원인: 암묵적 존재 필드는 기본값을 선에 싣지 않는다(실험: `i=0` → 0바이트). 받는 쪽은 둘을 구분할 수 없다.
- 대처: `optional`로 명시적 존재(`hasX()`)를 쓰거나, 갱신할 필드 목록(필드 마스크)을 함께 보낸다.

## 핵심 문장

- 직렬화의 위험은 문법보다 **읽는 쪽 타입**에 있다. JSON은 큰 정수를 허용하지만 JS는 2^53 위에서 값을 바꾼다 — 64비트 ID는 문자열로 낸다.
- Protobuf에서 선 위의 정체성은 이름이 아니라 **필드 번호**다. 번호를 재사용하면 에러 없이 다른 필드로 읽히므로, 지운 번호는 `reserved`로 막는다.
- Protobuf는 모르는 필드를 보존해 중계해도 살아남지만, JSON 변환·필드 복사에서는 잃는다. 관대한 읽기와 보존은 다르다.
- Avro는 태그 없이 값만 싣고, 쓴 쪽과 읽는 쪽 스키마를 이름으로 맞춘다. 새 필드에 기본값이 없으면 옛 데이터를 못 읽는다.
- proto3 기본 필드는 0을 보내지 않는다. 0과 "없음"을 구분해야 하면 `optional`을 쓴다.

## 관련 주제·근거

- 선행: [07-versioning-and-compatibility](../07-versioning-and-compatibility/2-summary.md)
- 후속·연결: [15-rpc-and-grpc](../15-rpc-and-grpc/2-summary.md), [database/28-key-strategy-surrogate-natural-public-id](../../database/28-key-strategy-surrogate-natural-public-id/2-summary.md)(64비트 ID·외부 ID), [testing/13-contract-testing](../../testing/13-contract-testing/2-summary.md), data-engineering/09-data-contracts-and-schema-registry(미작성 — [data-engineering 영역](../../data-engineering/README.md)), [distributed/17-queues-logs-and-delivery-semantics](../../distributed/17-queues-logs-and-delivery-semantics/2-summary.md)
- 근거
  - RFC 8259 The JSON Data Interchange Format(2017-12) §4·§6 — https://www.rfc-editor.org/rfc/rfc8259
  - Protobuf Language Guide (proto3) — https://protobuf.dev/programming-guides/proto3/ (reserved, 필드 번호 범위, unknown fields, enum, 호환 타입)
  - Protobuf Encoding — https://protobuf.dev/programming-guides/encoding/ (varint 150 예, 태그 공식, zigzag)
  - Protobuf Field Presence — https://protobuf.dev/programming-guides/field_presence/ (proto3 `optional`, protoc 3.15.0)
  - ProtoJSON Format — https://protobuf.dev/programming-guides/json/ (int64 → 10진 문자열)
  - protobuf `CHANGES.txt`(v3.5.0, 2017-11-09 — proto3 unknown field 기본 보존) — https://github.com/protocolbuffers/protobuf/blob/v3.5.0/CHANGES.txt
  - Apache Avro 1.12.0 Specification — https://avro.apache.org/docs/1.12.0/specification/ (Schema Resolution, 이진 인코딩)
  - Kleppmann, DDIA 1판 4장 "Encoding and Evolution"(Thrift·Protobuf·Avro 비교 — 장 단위 참조)
- 실험 목록
  - 같은 레코드의 JSON·Protobuf·Avro 크기, varint·zigzag 바이트, 필드 번호 재사용, unknown 필드·enum 보존, Avro writer/reader 해석 — maven:3.9-eclipse-temurin-21(JDK 21.0.11), protobuf-java 3.25.5(protoc 3.25.5, protobuf-maven-plugin 0.6.1), Avro 1.12.0, Jackson 2.19.2
  - `reserved` 번호 재사용 컴파일 오류 — protoc 3.25.5 바이너리(eclipse-temurin:21-jdk 컨테이너)
  - JS 2^53 정밀도 손실·`context.source` — node:22-alpine(Node v22.23.2)
  - Jackson `@JsonFormat(shape = STRING)` 왕복 — Jackson 2.19.2
