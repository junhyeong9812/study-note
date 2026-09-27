# sql/42-테이블 정의와 변경 (CREATE·ALTER·DROP) — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,\
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.\
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.

대상은 **PostgreSQL 18.6** 과 **MySQL 8.4.10** 두 서버다. 「두 엔진에서」라고 물으면 **각각** 답한다.

이 주제는 DDL 이라 공유 표를 읽는 것으로는 예제가 서지 않는다.\
아래 표는 이 편이 **직접 만들었다가 지운 것**이다. `emp`·`dept` 는 건드리지 않았다.

```text
t42_a (실험용)                                      t42_b   ALGORITHM/LOCK 실험용
+------------+-----------------------------+       t42_tx  트랜잭션 안의 DDL 실험용
| id         | int PRIMARY KEY             |       t42_c   MODIFY 실험용
| name       | varchar(20) NOT NULL        |       v42_a   t42_a 를 보는 뷰
| note       | text                        |
| created_at | timestamp DEFAULT NOW       |       행은 (1, 'ann', NULL, <시각>) 하나
+------------+-----------------------------+
```

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 이미 있는 표를 또 만들면 (예측)

```sql
CREATE TABLE t42_a (id int);                 -- (a)  t42_a 가 이미 있다
CREATE TABLE IF NOT EXISTS t42_a (id int);   -- (b)
```

- 두 엔진에서 (a)·(b) 는 각각 무엇을 출력하는가?

### 2. ★ MySQL 이 「아무 말 없이」 통과했을 때 (연결)

- 1번 (b) 가 MySQL 에서 아무 출력도 안 냈다면, **건너뛴 것인지 새로 만든 것인지** 어떻게 아는가?

### 3. ★ 트랜잭션 안에서 표를 만들고 되돌리면 (예측)

```sql
BEGIN;                       -- MySQL 은 START TRANSACTION
CREATE TABLE t42_tx (id int);
ROLLBACK;
-- 이제 t42_tx 는 있는가?
```

- 두 엔진에서 각각 어떻게 되는가?

### 4. ★ 이 `ALTER` 가 표를 다시 쓰나 (예측)

```sql
ALTER TABLE t42_a ADD COLUMN c1 int DEFAULT 7;   -- (a)
ALTER TABLE t42_a ALTER COLUMN c1 TYPE bigint;   -- (b)  PG
```

- PG 에서 둘 중 무엇이 표 전체를 다시 쓰는가 — 그것을 **무엇으로 확인할 수 있는가**?

### 5. ★ MySQL 에게 방법을 지정하면 (예측)

```sql
ALTER TABLE t42_a MODIFY COLUMN c1 bigint, ALGORITHM=INSTANT;
ALTER TABLE t42_a MODIFY COLUMN c1 bigint, ALGORITHM=INPLACE, LOCK=NONE;
ALTER TABLE t42_a MODIFY COLUMN c1 bigint, ALGORITHM=COPY,    LOCK=NONE;
```

- 세 문이 각각 어떻게 되고, 그 에러들이 무엇을 말해 주는가?

### 6. PG 의 `ALTER TABLE` 은 무엇을 잠그나 (경계)

- `ALTER TABLE t ADD COLUMN memo text` 가 잡는 잠금은 무엇이고, 그동안 그 표를 **읽을 수 있는가**?

### 7. ★ 행이 있는 표에 `NOT NULL` 열을 추가하면 (예측)

```sql
-- t42_a 에 행이 하나 있다
ALTER TABLE t42_a ADD COLUMN req int NOT NULL;
```

- 두 엔진에서 각각 무엇이 나오고, **기존 행의 `req` 는 무엇이 되는가**?

### 8. ★ 표를 가리키는 뷰가 있는데 표를 지우면 (예측)

```sql
CREATE VIEW v42_a AS SELECT id, name FROM t42_a;
DROP TABLE t42_a;
SELECT * FROM v42_a;
```

- 두 엔진에서 세 문이 각각 어떻게 되는가?

### 9. `CASCADE` 는 어디까지 지우나 (경계)

- PG 의 `DROP TABLE t42_a CASCADE` 는 무엇을 같이 지우고, **그 사실을 어떻게 알려 주는가**?

### 10. MySQL 에서 타입만 바꾸려 했는데 (예측)

```sql
CREATE TABLE t42_c (id int NOT NULL DEFAULT 5, v varchar(5));
ALTER TABLE t42_c MODIFY COLUMN id bigint;
```

- `id` 의 정의는 이 뒤에 무엇이 되는가?

### 11. 이식할 때 먼저 찾을 것 (연결)

- PG 로 쓴 DDL 을 MySQL 로 옮길 때, **에러가 나서 안전한 것**과 **에러가 안 나서 위험한 것**은 각각 무엇인가?

### 12. 실험 뒷정리는 어떻게 하나 (연결)

- 두 엔진에서 실험용 표를 지우는 방법이 왜 달라야 하는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
