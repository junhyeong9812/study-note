# database/22-database-side-timeouts — 질문

## 질문

1. (왜) 앱이 요청 타임아웃으로 포기했는데 왜 DB 부하가 줄지 않나? 클라이언트 타임아웃과 서버 타임아웃은 각각 "무엇을" 멈추나?
2. (예측) pgjdbc에서 6초 쿼리에 (a) `socketTimeout=2`, (b) `setQueryTimeout(2)`를 각각 걸었다. 두 경우 앱이 받는 SQLSTATE, 서버 쪽 쿼리 상태, 커넥션 재사용 가능 여부를 비교하라.
3. (그림) 세션 A가 `BEGIN; SELECT * FROM t;` 뒤 놀고 있다. B가 `ALTER TABLE t ADD COLUMN ...`, 이어서 C가 `SELECT * FROM t`를 보낸다. 각자의 락 모드와 대기 관계를 그리고, C가 A와 충돌하지 않는데도 멈추는 이유를 설명하라. 어떻게 막나?
4. (경계) PostgreSQL 17의 `statement_timeout`·`lock_timeout`·`idle_in_transaction_session_timeout`·`transaction_timeout`은 각각 무엇을 재고, 넘으면 문장이 끝나나 세션이 끝나나? 기본값은?
5. (예측) MySQL 8.4에서 트랜잭션 안의 두 번째 UPDATE가 `ERROR 1205`로 실패했다. 첫 번째 UPDATE는 어떻게 되나? 앱이 그대로 COMMIT하면? 1213이면 무엇이 다른가?
6. (설계) 요청 데드라인·드라이버 query timeout·socketTimeout·statement_timeout·lock_timeout을 짧은 것부터 순서대로 놓고, 그 순서의 이유를 설명하라. `lock_timeout`을 `statement_timeout`보다 크게 두면?
7. (설계) 웹 앱·배치·마이그레이션이 같은 PostgreSQL을 쓴다. 전역 `postgresql.conf` 대신 어떻게 한도를 나누나? PgBouncer transaction 모드라면 무엇을 조심하나?
8. (장애 진단) `pg_stat_activity`에 `idle in transaction`이 40분째인 세션이 있다. 무엇이 나빠지고 있나? `idle_in_transaction_session_timeout`을 켜면 앱은 어떤 에러를 보게 되나?
9. (연결) MySQL 8.4의 `max_execution_time`으로 UPDATE 폭주를 막을 수 있나? DDL이 기다리는 락은 어떤 변수가 제한하고 기본값은?
10. (장애 진단) 앱 로그에는 `Read timed out`만 보이는데 DB CPU가 계속 100%다. 무엇을 확인하고, 서버가 끊긴 클라이언트의 쿼리를 스스로 멈추게 하려면 PostgreSQL에서 무엇을 켜나? 그 설정의 한계는?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
