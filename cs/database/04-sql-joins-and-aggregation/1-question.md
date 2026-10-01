# database/04-sql-joins-and-aggregation — 질문

## 질문

1. (왜) SELECT 문의 논리 처리 순서를 적어라. 이 순서로 설명되는 현상 두 가지(별칭, 윈도 함수)를 들어라. 실제 실행 순서도 이와 같은가?
2. (계산) 주문 1에 상세 3줄(qty 1, 2, 1), 결제 2건(60, 40)이 있다. `ord ⋈ ord_item ⋈ payment`를 주문별로 묶어 `sum(qty)`, `sum(amount)`를 내면 값은? 올바른 값과 올바른 쿼리는?
3. (예측) `blacklist(customer)`에 `'lee'`와 `NULL`이 있다. 고객 kim·lee·park에 대해 `NOT IN (SELECT customer FROM blacklist)`와 `NOT EXISTS`는 각각 몇 건을 내나? 3치 논리로 설명하라.
4. (예측) `LEFT JOIN payment p ON p.order_id = o.id AND p.amount >= 50`과 `LEFT JOIN payment p ON p.order_id = o.id WHERE p.amount >= 50`의 결과 차이는? 결제가 없는 주문 3은 각각 어떻게 되나? PostgreSQL 계획에는 어떤 흔적이 남나?
5. (경계) `count(*)`, `count(col)`, `sum(col)`, `avg(col)`은 NULL을 어떻게 다루나? 모든 값이 NULL인 열에서 각각의 결과는?
6. (경계) `SELECT customer, total FROM ord GROUP BY customer`는 PostgreSQL 17과 MySQL 8.4에서 어떻게 되나? `GROUP BY id`(PK)로 바꾸면 `customer`를 SELECT에 쓸 수 있는 이유는?
7. (설계) 팬아웃을 `SUM(DISTINCT amount)`로 고치자는 제안이 나왔다. 왜 틀렸는지 반례를 들고, 올바른 두 가지 방법을 써라.
8. (장애 진단) "블랙리스트 제외 발송 대상"이 갑자기 0명이 됐다. 에러는 없다. 무엇을 의심하고 어떤 쿼리로 확인하며, 어떻게 고치나?
9. (연결) `NOT EXISTS`와 `NOT IN`은 PostgreSQL에서 각각 어떤 계획 노드로 실행되었나? 의미 차이가 알고리즘 선택에 어떤 영향을 주나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
