# api-design/08-schema-and-serialization — 질문

## 질문

1. (왜) 레코드 `{id=1, amount=5000}`이 JSON·Protobuf·Avro에서 각각 몇 바이트였나? 크기 차이는 각 형식이 "필드를 무엇으로 식별하나"와 어떻게 연결되나?
2. (예측) Node 22에서 `JSON.parse('{"id":9007199254740993}').id`는 무엇인가? 이 값을 다시 `JSON.stringify`해 서버로 보내면 무슨 일이 생기나? RFC 8259는 어느 범위의 정수를 "상호운용 가능"하다고 하나?
3. (계산) Protobuf에서 `int32 i = 1`에 300을 넣으면 바이트는? `int32`에 -1을 넣을 때와 `sint32`에 -1을 넣을 때 메시지 크기는 각각 몇 바이트이고 왜 다른가?
4. (예측) v1 `int64 amount = 2`를 지우고 v2에서 `int64 user_id = 2`로 재사용했다. v1이 쓴 `amount=5000`을 v2가 읽으면 어떻게 되나? 이것을 컴파일 단계에서 막는 방법과 protoc의 반응은?
5. (경계) v2가 보낸 메시지(새 필드 `memo`, 새 enum 값 `REFUNDED`)를 v1 Java 서비스가 받아 일부를 고쳐 다시 보낸다. v2는 `memo`와 `REFUNDED`를 되찾나? 같은 중계를 Jackson DTO(모르는 필드 무시)로 하면?
6. (예측) Avro writer 스키마 `{id: long, amount: long}`로 쓴 레코드를 다음 reader 스키마로 읽으면? (a) `email: string, default ""` 추가 (b) 기본값 없는 `email` 추가 (c) 필드 순서를 바꾸고 `amount`를 double로 (d) `amount` 삭제.
7. (경계) proto3에서 `int32 discount = 3`에 0을 넣으면 선 위에 무엇이 실리나? 부분 갱신 API에서 이것이 왜 문제이고, 어떻게 피하나?
8. (장애 진단) 웹 화면에서만 가끔 "주문을 찾을 수 없음"이 뜨고 모바일 앱은 정상이다. 서버 로그의 조회 ID는 실제 ID와 끝자리가 다르다. 원인과 이미 숫자로 공개한 API를 고치는 순서는?
9. (적용) 공개 HTTP API, 내부 서비스 RPC, 대용량 이벤트 스트림에 각각 어떤 형식을 고르고, 그 이유는?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
