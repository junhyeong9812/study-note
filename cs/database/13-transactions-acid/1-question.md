# database/13-transactions-acid — 질문

## 질문

1. (왜) 트랜잭션이 없으면 계좌 이체 두 UPDATE 사이에서 생길 수 있는 문제 세 가지는? 각각 ACID의 어느 글자가 막나?
2. (경계) "원자성"은 동시성과 관련이 있나? DDIA가 더 나은 이름으로 꼽은 말은 무엇이고, 원자성을 구현하는 두 방법은?
3. (예측) `acc2(id, bal CHECK (bal >= 0))`에 (1,100), (2,0)이 있다. `BEGIN; UPDATE … bal+50 WHERE id=2; UPDATE … bal-150 WHERE id=1; COMMIT;`을 PostgreSQL 17과 MySQL 8.4 InnoDB에서 각각 실행하면 최종 상태는? 두 번째 UPDATE 뒤에 SELECT를 하나 더 보내면 PostgreSQL은 무엇을 돌려주나?
4. (경계) "C(일관성)는 DB가 보장한다"는 말은 어디까지 맞나? CMU 15-445가 나누는 두 종류의 일관성과 각각의 책임자는?
5. (그림) 스케줄 `R1(A) R2(A) W1(A) W2(A)`의 충돌 그래프를 그리고 직렬화 가능한지 판정하라. 이 스케줄이 현실에서 어떤 버그인지 말하라. `R1(A) W1(A) R2(A) W2(A)`는?
6. (연결) 커밋 응답을 받은 트랜잭션이 정전 뒤에도 남아 있으려면 무엇이 디스크에 있어야 하나? PostgreSQL 17과 MySQL 8.4에서 이를 약하게 만드는 설정 이름과 기본값, 약하게 했을 때 잃는 것은?
7. (장애 진단) 주문 트랜잭션이 롤백됐는데 고객은 "주문 완료" 메일을 받았다. 원인과 Spring에서의 고치는 방법 두 가지는?
8. (장애 진단) JDBC 코드에서 두 번째 UPDATE가 실패했는데 첫 번째 UPDATE는 반영돼 있다. 가능한 원인 두 가지는? JDBC `Connection`의 기본 커밋 모드는?
9. (장애 진단) PostgreSQL 애플리케이션 로그에 `current transaction is aborted, commands ignored until end of transaction block`이 한 번 나오기 시작하면 그 요청의 모든 쿼리가 실패한다. SQLSTATE와 원인, 대처는?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
