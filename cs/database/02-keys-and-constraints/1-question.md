# database/02-keys-and-constraints — 질문

## 질문

1. (왜) "SELECT로 이메일이 없으면 INSERT"를 앱에서 하는데도 중복 계정이 생긴다. 두 요청의 시간축을 그려 이유를 설명하고, `UNIQUE` 제약은 왜 같은 상황에서 중복을 막는지 설명하라.
2. (경계) `member(id, email, phone, name)`에서 id와 email이 각각 유일하다. 슈퍼키·후보 키·기본 키·대체 키를 예로 구분하라.
3. (예측) 세션 A가 `BEGIN; INSERT email='b@x.com'`을 하고 커밋하지 않았다. 세션 B가 같은 이메일을 INSERT하면 B는 어떻게 되나? A가 커밋할 때와 롤백할 때 각각 B의 결과는? 이때 `pg_stat_activity`에서 B의 대기는 어떻게 보이나?
4. (예측) PostgreSQL과 MySQL에서 각각 다음은 성공하나 실패하나? (a) `UNIQUE` 열에 NULL 두 개, (b) `CHECK (qty > 0)` 열에 NULL, (c) PostgreSQL `UNIQUE NULLS NOT DISTINCT` 열에 NULL 두 개.
5. (연결) 외래 키 검사는 자식 INSERT 때와 부모 DELETE 때 각각 무엇을 조회하나? PostgreSQL과 MySQL은 자식 FK 열 인덱스를 어떻게 다르게 다루나?
6. (경계) `ON DELETE NO ACTION`과 `RESTRICT`는 PostgreSQL에서 무엇이 다른가? MySQL InnoDB에서는?
7. (설계) 운영 중인 수천만 행 `orders` 테이블에 `CHECK (qty > 0)`과 FK를 새로 걸어야 한다. PostgreSQL에서 쓰기를 오래 막지 않고 거는 순서와, 그 전에 돌릴 점검 쿼리를 써라.
8. (장애 진단) PostgreSQL에서 회원 한 명 삭제가 수 초 걸리고, `EXPLAIN ANALYZE`에 `Trigger for constraint orders_member_id_fkey: time=…`이 크게 나온다. 원인과 대처는? MySQL이면 같은 문제가 생기나?
9. (장애 진단) 앱이 JDBC로 PostgreSQL과 MySQL에 가입 INSERT를 한다. 중복 이메일일 때 각 DB의 에러 코드는 무엇이고, Spring은 어떤 예외로 바꾸나? 앱은 이 예외를 어떻게 처리해야 하나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
