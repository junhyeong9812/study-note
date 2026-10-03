# testing/08-integration-tests-real-dependencies — 질문

## 질문

1. (왜) 리포지토리 테스트를 H2나 mock으로만 돌리면 무엇을 검증하지 못하나? SWE@G 14장의 "충실도"와 "밀폐성"으로 설명하라.
2. (예측) 한 트랜잭션에서 `insert (1)` → 중복 `insert (1)`(예외를 잡아 무시) → `insert (2)` → `commit`을 한다. H2 2.5.252(PostgreSQL 모드)와 PostgreSQL 17에서 각각 어떻게 되나? PostgreSQL 쪽 SQLSTATE는?
3. (예측) H2를 문서 권장 URL(`MODE=PostgreSQL;DATABASE_TO_LOWER=TRUE;DEFAULT_NULL_ORDERING=HIGH`)로 띄웠다. `ON CONFLICT (k) DO UPDATE`, `body->>'name'`, `varchar_col > 5`는 H2와 PostgreSQL 17에서 각각 어떻게 되나?
4. (경계) 실험에서 H2와 PostgreSQL의 차이를 세 층으로 나눴다. 각 층의 예를 들고, 왜 세 번째 층이 가장 위험한지 말하라.
5. (연결) Testcontainers가 테스트 하나를 돌릴 때 일어나는 일을 순서대로 그려라. Ryuk는 무엇을 하나?
6. (경계) JUnit 5에서 `@Container`를 static 필드에 둘 때와 인스턴스 필드에 둘 때 수명이 어떻게 다른가? 공유했을 때 새로 생기는 위험은?
7. (연결) Spring Boot에서 `@DataJpaTest`에 Testcontainers를 붙였는데 실제로는 H2로 돌 수 있는 경우는? 어떻게 확인·차단하나?
8. (장애 진단) 운영 로그에 `55P03 could not obtain lock on row`가 나오고 재시도가 동작하지 않는다. 테스트에서는 재시도 경로가 초록이었다. 무엇을 의심하고 어떻게 고치나?
9. (장애 진단) 25P02 오류가 난 코드를 고치는 방법 두 가지를 대라. 실험에서 쓴 방법은?
10. (적용) 어떤 테스트를 실제 엔진으로 올리고 어떤 테스트를 단위 테스트에 남기나? 판단 기준을 말하라.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
