# database/08-btree-indexes — 질문

## 질문

1. (왜) 디스크 위 인덱스로 정렬 배열이나 이진 탐색 트리 대신 B+트리를 쓰는 이유를 "노드 = 페이지"와 "갈래 수"로 설명하라. B-트리와 달리 값을 잎에만 두고 잎을 잇는 것은 무엇을 쉽게 하나?
2. (계산) bigint 키 20만 개의 PostgreSQL PK 인덱스가 잎 547페이지, 내부 3페이지였다. 잎당 키는 대략 몇 개인가? 갈래 수를 400으로 잡으면 3층과 4층이 담을 수 있는 행은 대략 몇 개인가?
3. (그림) 꽉 찬 잎 `[30 35 40 50 55]`에 45를 넣는 과정을 그려라. 분할이 루트까지 번지면 무슨 일이 생기나?
4. (예측) 같은 20만 행을 순차 bigint 키와 UUIDv4 키로 넣었다. PostgreSQL `pgstatindex`의 `avg_leaf_density`·`leaf_fragmentation`은 각각 어떻게 나오고, 왜 그런가? 같은 UUID 인덱스를 `REINDEX`하면?
5. (경계) PostgreSQL과 InnoDB는 반쯤 빈 잎을 어떻게 다루나? 대량 삭제 뒤 인덱스가 줄지 않는 이유는?
6. (연결) InnoDB에서 `SELECT * FROM users WHERE email = ?`와 `SELECT id FROM users WHERE email = ?`는 트리를 몇 번 내려가나? PostgreSQL에서 같은 두 쿼리는? "커버링"이 성립하는 조건을 엔진별로 말하라.
7. (예측) `email`, `created_at`에 각각 인덱스가 있다. 다음 조건 중 인덱스를 타는 것과 못 타는 것을 고르고 이유를 대라: `lower(email) = ?`, `date(created_at) = ?`, `created_at >= ? AND created_at < ?`, (MySQL) `email = 777`, `email LIKE '%777@ex.com'`.
8. (경계) PostgreSQL에서 `timestamptz` 칼럼에 `(created_at::date)` 식 인덱스를 만들려고 하면 어떻게 되나? 왜 그렇고, 대신 무엇을 하나?
9. (장애 진단) PK를 UUIDv4로 바꾼 뒤 삽입 처리량이 떨어지고 WAL·복제 트래픽이 늘었다. 어떤 지표로 원인을 확인하고, 어떻게 고치나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
