# database/09-index-design — 질문

## 질문

1. (왜) 인덱스 `(a, b, c)`와 조건 `WHERE a = 5 AND b >= 42 AND c < 77`이 있다. 인덱스의 어느 구간을 읽고, `c < 77` 조건은 어디에 쓰이나? 이 규칙은 B+Tree의 어떤 성질에서 나오나?
2. (예측) 인덱스는 `(tenant_id, created_at)` 하나다. `WHERE created_at >= '2026-03-01' AND created_at < '2026-03-02'`를 PostgreSQL 17과 MySQL 8.4에서 각각 `SELECT *`와 `SELECT tenant_id, created_at`로 돌리면 계획이 어떻게 나올까?
3. (경계) PostgreSQL에서 `Index Only Scan`인데 `Heap Fetches: 800`이 나왔다. 반환 행은 400이다. 왜 힙을 읽었고, 언제 0이 되나? MySQL InnoDB 보조 인덱스의 커버링은 무엇이 다른가?
4. (설계) 주문 테이블에서 `status = 'pending'`은 1%, `'done'`은 99%다. "대기 주문을 오래된 순으로 10건" 쿼리를 위한 인덱스를 PostgreSQL과 MySQL에서 각각 설계하라. PostgreSQL 방식에 파라미터 바인딩(`status = ?`)을 쓰면 무엇을 조심해야 하나?
5. (장애 진단) 로그인 쿼리 `WHERE lower(email) = ?`가 느리다. `email`에는 인덱스가 있다. `EXPLAIN`에 무엇이 보이고, 고치는 방법 두 가지는?
6. (예측) `status = 'done'`(99%) 조건만으로는 인덱스가 쓰이지 않았다. 그런데 `status = 'done' ORDER BY created_at LIMIT 10`에서는 `(status, created_at)` 인덱스가 쓰였다. 왜인가?
7. (장애 진단) 보조 인덱스를 5개 추가한 뒤 적재 배치가 크게 느려졌다. 원인을 두 가지 들고, 지울 인덱스를 고를 때 확인할 것을 말하라.
8. (연결) PostgreSQL에서 인덱스 컬럼이 아닌 컬럼만 바꾸는 UPDATE와, 인덱스 컬럼 하나를 바꾸는 UPDATE는 인덱스 쓰기 양이 어떻게 다른가? 이것이 "인덱스를 줄여라"와 어떻게 연결되나?
9. (장애 진단) 운영 중 `CREATE INDEX CONCURRENTLY`가 유일성 위반으로 실패했다. 테이블에는 무엇이 남고, 그것이 왜 문제이며, 어떻게 정리하나? `CONCURRENTLY` 없이 만들면 무엇이 막히나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
