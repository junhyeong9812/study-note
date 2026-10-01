# database/05-window-functions-and-cte — 질문

## 질문

1. (왜) `GROUP BY`와 윈도 함수는 결과 행 수에서 어떻게 다른가? 윈도 함수 없이 "행마다 누계"를 구하면 어떤 방식이 되고 비용은 어떤가?
2. (예측) `sales`가 (09-01, 10), (09-02, 20), (09-02, 30), (09-03, 40)이다. `SUM(amt) OVER (ORDER BY d)`와 `SUM(amt) OVER (ORDER BY d ROWS UNBOUNDED PRECEDING)`의 값을 행마다 적어라. 차이의 이유는?
3. (예측) 같은 데이터에서 `ORDER BY d`로 `row_number`, `rank`, `dense_rank`를 구하라. `row_number`가 동률 두 행에 주는 번호는 매번 같은가?
4. (경계) `last_value(amt) OVER (ORDER BY d, amt)`가 항상 현재 행 값을 내는 이유와 고치는 방법은? `row_number`는 왜 이 문제가 없나?
5. (경계) `WHERE row_number() OVER (…) = 1`이 실패하는 이유는? 고쳐 쓴 쿼리를 쓰고, PostgreSQL 17 계획에서 볼 수 있는 최적화 흔적은?
6. (연결) PostgreSQL 17에서 CTE는 언제 바깥 쿼리에 녹아 들어가고 언제 먼저 계산되나? 먼저 계산되면 성능에 어떤 영향이 있나? MySQL 8.4는 CTE를 어떻게 다루나?
7. (그림) `WITH RECURSIVE`의 실행을 작업 테이블로 설명하라. 조직도 ceo ← cto ← (dev, ops)에서 회차별 작업 테이블을 적고, 어떤 그래프 탐색과 같은지 말하라.
8. (장애 진단) 조직도 API가 어느 날 응답하지 않는다. PostgreSQL과 MySQL에서 각각 어떤 에러·현상이 보이나? 원인과, 쿼리·서버·쓰기 경로 세 층의 대처를 써라.
9. (장애 진단) 경로 문자열을 쌓는 재귀 CTE가 PostgreSQL에선 되는데 MySQL 8.4에선 `ERROR 1406 Data too long`으로 실패한다. 원인과 해결은?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
