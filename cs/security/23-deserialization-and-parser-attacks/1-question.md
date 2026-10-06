# security/23-deserialization-and-parser-attacks — 질문

## 질문

1. (왜) 역직렬화·XXE·Log4Shell은 겉모습이 다르다. 셋을 한 문장의 공통 구조로 묶어라. 18번 인젝션과는 무엇이 같고 무엇이 다른가?
2. (예측) 서버가 `(Order) in.readObject()`로 받는다. 공격자가 `Order`가 아닌 클래스의 직렬화 바이트를 보내면 무엇이 어떤 순서로 일어나나? "캐스트에서 걸러지니 괜찮다"가 왜 틀렸나?
3. (그림) 직렬화 필터 `maxdepth=5;maxarray=1000;com.example.Order;java.lang.*;!*`가 스트림을 판정하는 흐름을 그려라. 끝의 `!*`를 빼면 무엇이 달라지나?
4. (예측) JDK 21 기본 `DocumentBuilderFactory`로 (a) `file:` 외부 엔티티 문서, (b) 10단계 × 10배 엔티티 폭탄을 파싱하면 각각 어떻게 되나? `disallow-doctype-decl=true`를 켜면?
5. (경계) Log4j 2.14.1에서 `log.info("ua={}", ua)`처럼 파라미터 바인딩을 썼는데도 왜 lookup이 실행됐나? `formatMsgNoLookups=true`는 어디까지 막고 어디는 못 막나?
6. (연결) Jackson·SnakeYAML·Python `pickle`에서 같은 위험을 만드는 기능은 무엇이고, 각각 안전한 쪽은?
7. (장애 진단) 앱 서버에서 외부 389 포트로 나가는 연결이 방화벽에 찍혔다. 접근 로그에서 무엇을 찾고, 어떤 순서로 대응하나?
8. (장애 진단) JVM 전체 직렬화 필터를 배포한 직후 세션이 노드 사이에서 사라진다. 로그 형태, 원인, 재발 없는 도입 순서는?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
