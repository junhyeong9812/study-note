# database/10-collation-and-text-comparison — 질문

## 질문

1. (왜) collation은 무엇을 정하는 규칙이고, DB 안에서 어디어디에 쓰이나? 그중 규칙이 바뀌었을 때 가장 위험한 자리는 어디이고 왜인가?
2. (그림) UCA의 비교 단계 L1~L4를 예와 함께 그려라. `utf8mb4_0900_ai_ci`에서 `'a' = 'A'`이고 `'resume' = 'résumé'`인 이유를 `WEIGHT_STRING` 결과로 설명하라.
3. (예측) `CREATE TABLE users(email varchar(100) UNIQUE)`에 `'a@x.com'`, `'A@x.com'`을 차례로 넣는다. MySQL 8.4 기본 설정과 PostgreSQL 17 기본 설정에서 각각 결과는? 두 제품에서 결과를 반대로 만들려면 무엇을 바꾸나?
4. (경계) PostgreSQL의 deterministic과 nondeterministic collation은 무엇이 다른가? 비결정적 collation으로 대소문자 무시 UNIQUE를 만들 때 치르는 대가 세 가지는?
5. (예측) 같은 14개 문자열(`a`, `A`, `_x`, `é`, `Z` 등)을 PG `"C"`, PG `"en_US"`(glibc), PG ICU, MySQL `utf8mb4_bin`으로 정렬한다. `_x`와 `é`는 각각 어디쯤 오나? 이것이 "ICU vs libc"에 대해 알려 주는 것은?
6. (장애 진단) MySQL `ai_ci` 컬럼으로 `WHERE name > :last ORDER BY name LIMIT 20` 커서 페이지네이션을 한다. 일부 회원이 목록에서 사라진다. 원인과 고친 쿼리는? 앱에서 Java `String.compareTo`로 정렬해 커서를 만들면 무엇이 더 틀어지나?
7. (장애 진단) OS 메이저 업그레이드 후 PostgreSQL에서 `WHERE code = 'X-1'`이 행을 못 찾고, UNIQUE 컬럼에 중복이 생겼다. 오류 로그는 없다. 원인, 영향받는 경로·받지 않는 경로, 확인 방법과 대처는?
8. (연결) B+Tree 인덱스의 불변식과 collation은 어떻게 연결되나? 쿼리에 `COLLATE "C"`를 붙이면 PG에서 실행 계획이 어떻게 바뀌고, MySQL에서 collation이 다른 두 컬럼을 조인하면 무엇이 나오나?
9. (설계) 이메일(로그인 ID), 사람 이름 검색, API 토큰, 화면 표시 정렬 — 네 컬럼 각각에 어떤 비교 규칙을 두겠나? PostgreSQL에서 대소문자 무시 이메일 유일성을 만드는 두 방법과 각각의 주의점은?
10. (경계) 눈에 똑같은 `'한'`이 DB에서 같지 않다고 나온다. 왜 그런가? PostgreSQL 기본 collation, ICU 비결정적 collation, `normalize()`, MySQL `ai_ci`·`_bin`에서 각각 결과는?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
