# api-design/21-api-documentation-openapi — 질문

## 질문

1. (왜) 위키에 손으로 쓴 API 문서는 왜 결국 구현과 어긋나나? 이를 막는 핵심 장치는 무엇인가?
2. (그림) OpenAPI 3.1 문서의 뼈대(`openapi`·`info.version`·`paths`·operation·`responses`·`components/schemas`·`$ref`)를 트리로 그려라. `openapi`와 `info.version`은 각각 무엇의 버전인가?
3. (경계) 명세 우선(design-first)과 코드 우선(code-first)은 무엇이 다른가? 코드 우선에서도 따로 해야 하는 일은?
4. (예측) 명세가 `id: string`, `status: [PENDING, PAID]`, 필수 `createdAt`, `additionalProperties: false`인데 구현이 `{ id: 1001, status: 'CANCELLED', amount: 12000, created_at: '...' }`를 200으로 돌려준다. 명세 스키마로 검증하면 어떤 오류가 몇 개 나오나? "200이면 통과" 테스트는 몇 개를 잡나?
5. (경계) OpenAPI 3.1의 Schema Object와 JSON Schema는 어떤 관계인가? 3.0.3에서는 어땠나? 이 차이가 검증 도구 선택에 주는 의미는?
6. (경계) 명세의 `example`이 스키마와 맞지 않으면 OpenAPI 형식상 오류인가? 실무에서는 어떻게 다루나?
7. (연결) 응답 스키마의 `additionalProperties: false`는 서버 쪽 드리프트 검사와 클라이언트 쪽 검증에서 각각 어떤 효과를 내나? 하위 호환 규칙과 어떻게 부딪히나?
8. (장애 진단) 배포 뒤 파트너가 "주문 생성 시각이 비어 있다"고 신고했다. 서버 로그엔 오류가 없다. 무엇을 의심하고, 재발을 막으려면 CI에 무엇을 넣나?
9. (장애 진단) 문서 빌드가 `Missing $ref pointer "#/components/schemas/Ordr"`로 실패했다. 원인과, 이런 오류를 머지 전에 잡는 방법은?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
