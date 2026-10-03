# api-design/08-schema-and-serialization — 정답

## 정답

### 1. 세 형식의 크기

| 형식 | 크기(실험) | 바이트 | 식별 방식 |
|---|---|---|---|
| JSON | 22B | `{"id":1,"amount":5000}` | 필드 **이름**을 매번 싣는다 |
| Protobuf | 5B | `08 01 10 88 27` | 이름 대신 **번호**(태그 1바이트) |
| Avro | 3B | `02 90 4e` | 태그도 없음 — 스키마 **순서**대로 값만 |

- 자기 기술성을 덜어 낼수록 작아지고, 대신 읽는 쪽이 알아야 할 것(번호 → 이름, writer 스키마)이 늘어난다.

### 2. 2^53 너머의 정수

- 결과는 `9007199254740992`(실험, Node v22.23.2). 에러 없이 끝자리가 바뀐다.
- 다시 직렬화하면 바뀐 값이 서버로 간다 → 존재하지 않는 ID 조회(404)나 **다른 레코드** 조회.
- RFC 8259 §6: [-(2^53)+1, (2^53)-1] 범위의 정수는 구현들이 값에 정확히 합의한다는 의미에서 상호운용 가능하다. 그 밖은 구현이 범위·정밀도에 한계를 둘 수 있다.

### 3. varint·zigzag

- 300 → `08 ac 02`(실험). `08` = 필드 1·VARINT 태그, `ac 02` = 300의 varint(0101100 | 0000010, MSB 연속 비트).
- `int32` -1 → 11B(`08` + `ff×9 01`). 2의 보수로 64비트 전체가 1이라 varint 10바이트가 된다.
- `sint32` -1 → 2B(`10 01`). zigzag가 -1을 1로 접어 1바이트 값이 된다.
- 음수가 자주 오는 필드는 `sint32`/`sint64`가 작다.

### 4. 번호 재사용

- v2는 **예외 없이** `user_id=5000`으로 읽는다(실험). 선 위에는 "번호 2, varint 5000"만 있고 이름은 없다.
- 막는 법: 지운 필드의 번호·이름을 `reserved 2; reserved "amount";`로 막는다.
- protoc 3.25.5의 반응(실험): `Field "user_id" uses reserved number 2.` + 빈 번호 제안(`3`), 종료 코드 1.

### 5. 중계와 unknown field

- Protobuf(Java, protobuf-java 3.25.5): v1은 `status=UNRECOGNIZED`(`getStatusValue()=2`), `memo`는 unknown field 5로 보존한다. v1이 `currency`를 고쳐 다시 써도 v2는 `memo=gift`·`REFUNDED`를 되찾는다(실험).
- Jackson DTO(모르는 필드 무시): 재직렬화 결과 `{"id":7,"amount":5000,"status":"PAID"}` — `memo`를 **잃는다**(실험).
- 단, Protobuf도 JSON으로 바꾸거나 필드를 하나씩 복사해 새 메시지를 만들면 unknown field를 잃는다(proto3 가이드).
- 이 보존은 protobuf 3.5.0(2017-11)부터의 proto3 기본 동작이다. 그 전의 proto3 런타임은 모르는 필드를 버렸다(protobuf `CHANGES.txt` 3.5.0).

### 6. Avro 스키마 해석 (실험, Avro 1.12.0)

| reader | 결과 |
|---|---|
| (a) `email` default `""` | OK `{"id": 1, "amount": 5000, "email": ""}` |
| (b) `email` 기본값 없음 | `AvroTypeException: ... missing required field email` |
| (c) 순서 바꿈 + double | OK `{"amount": 5000.0, "id": 1}` — 이름으로 짝짓고 long → double 승격 |
| (d) `amount` 삭제 | OK `{"id": 1}` — writer에만 있는 필드는 무시 |

### 7. proto3의 0

- 아무것도 실리지 않는다. 실험에서 `i=0` 메시지는 0바이트였다. 암묵적 존재 필드는 기본값을 직렬화하지 않는다.
- 문제: 받는 쪽은 "0으로 설정"과 "안 보냄"을 구분하지 못한다. 부분 갱신에서 "할인율을 0으로"를 표현할 수 없거나, 안 보낸 필드를 0으로 덮는다(protobuf.dev "Field Presence"의 Patch 위험).
- 피하는 법: `optional int32 discount = 3;`(protoc 3.15.0부터 기본 허용)으로 `hasDiscount()`를 쓰거나, 갱신할 필드 목록(필드 마스크)을 함께 보낸다.

### 8. 웹에서만 주문을 못 찾는다

- 원인: 주문 ID가 2^53-1을 넘었고 JSON 숫자로 나간다. 브라우저 JS는 binary64로 읽어 끝자리를 바꾼다. Java·Kotlin 앱은 `long`으로 읽어 정상이다.
- 고치는 순서
  1. 응답에 문자열 ID 필드(`id_str` 등)를 **추가**한다. 서버는 `@JsonFormat(shape = STRING)`처럼 문자열로 낸다.
  2. 웹 클라이언트를 문자열 필드로 옮긴다.
  3. 숫자 필드는 폐기 절차(Deprecation → 사용량 확인 → Sunset)로 내린다([07](../07-versioning-and-compatibility/2-summary.md)).
- 처음부터 설계한다면 ID를 문자열로 낸다. ProtoJSON도 int64를 문자열로 낸다.

### 9. 형식 고르기

- 공개 HTTP API: JSON — 브라우저를 포함한 대부분의 런타임이 기본으로 읽고 사람이 디버깅하기 쉽다. 대신 ID는 문자열, 금액은 정수 최소 단위나 10진 문자열.
- 내부 서비스 RPC: Protobuf(gRPC) — 작고 코드 생성이 되며, 번호·`reserved` 규칙으로 진화가 명확하다.
- 대용량 이벤트 스트림·저장: Avro + 스키마 레지스트리(또는 Protobuf) — 레코드마다 이름을 싣지 않고, writer 스키마를 중앙에서 찾고, 배포 전에 호환성을 검사한다.
