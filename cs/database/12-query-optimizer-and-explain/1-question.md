# database/12-query-optimizer-and-explain — 질문

## 질문

1. (왜) 옵티마이저가 고르는 계획은 "가장 빠른 계획"이라고 말할 수 없다. 왜인가? 옵티마이저가 실제로 최소화하는 것은 무엇이고, 그 입력은 무엇인가?
2. (계산) PostgreSQL 17 기본 설정에서 4,673페이지·500,000행 테이블의 Seq Scan 총비용은 얼마로 표시되나? 식과 함께 답하라. 이 숫자의 단위는 무엇인가?
3. (예측) 20만 행 테이블에서 `city = 'c11'`은 0.5%, `country = 'k1'`은 5%다. city가 정해지면 country가 정해지고, c11의 country는 k1이다. `WHERE city = 'c11' AND country = 'k1'`을 걸면 PostgreSQL은 몇 행쯤으로 추정하나? 실제는 몇 행인가? 무엇으로 고치나?
4. (그림) `FROM A, B, C` 세 테이블의 조인 순서를 System R 방식 동적 계획법으로 고르는 과정을 그려라. 이 방식이 모든 순서를 다 나열하는 것보다 나은 점은? PostgreSQL은 테이블이 몇 개부터 이 방식을 포기하나?
5. (읽기) 다음 계획에서 문제의 출발점은 어느 노드인가? 이 쿼리가 느린 이유를 한 문장으로 말하라.
   `Nested Loop (rows=6) (actual rows=100010 loops=1)` → 자식 `Index Scan on o2 (rows=6) (actual rows=100010 loops=1)`, `Index Only Scan on cust (rows=1) (actual rows=1 loops=100010)`
6. (장애 진단) 야간 배치가 끝난 뒤 아침부터 특정 조회만 느려졌다. 코드 배포는 없었다. 무엇을 어떤 순서로 확인하고, 긴급 조치와 재발 방지는 무엇인가? PostgreSQL 17의 자동 ANALYZE 문턱은 얼마인가?
7. (경계) MySQL 8.4에서 인덱스가 없는 `status` 컬럼에 `WHERE status = 'new'`를 걸면 히스토그램이 없을 때 `filtered`는 얼마로 나오나? 히스토그램을 만들면? 히스토그램은 데이터가 바뀌면 자동으로 갱신되나?
8. (장애 진단) 애플리케이션에서만 어떤 파라미터 값일 때 쿼리가 느리다. 같은 SQL을 psql에서 상수로 넣어 돌리면 빠르다. 그것도 커넥션마다 몇 번 실행된 뒤부터 느려진다. PostgreSQL에서 무엇이 의심되고 어떻게 확인·대처하나?
9. (경계) `EXPLAIN`과 `EXPLAIN ANALYZE`는 무엇이 다른가? `UPDATE`에 `EXPLAIN ANALYZE`를 쓸 때의 주의점, 그리고 `loops=100010`인 노드의 `actual rows=1`을 어떻게 읽어야 하나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
