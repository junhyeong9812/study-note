# sql/49-INSERT — 다중 행·INSERT SELECT·기본값 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,\
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.\
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.

이 편은 **자기 표를 만들어 쓰고 지운다.** `emp`·`dept` 는 건드리지 않는다.

```text
t49_a                                   CREATE TABLE t49_a (
+-------+--------------------------+      id    int PRIMARY KEY,
| id    | int PRIMARY KEY          |      name  varchar(10) NOT NULL,
| name  | varchar(10) NOT NULL     |      grade varchar(5) DEFAULT 'B',
| grade | varchar(5) DEFAULT 'B'   |      price int DEFAULT 100,
| price | int DEFAULT 100          |      qty   int DEFAULT 1,
| qty   | int DEFAULT 1            |      total int GENERATED ALWAYS AS (price*qty) STORED
| total | GENERATED (price*qty)    |    );
+-------+--------------------------+

t49_src                                 t49_p (id PK, name)
+-----+-------+-------+                 t49_c (id PK, p_id -> t49_p.id, memo)
| 101 | src-a |    10 |
| 102 | src-b |    20 |
| 103 | src-c |    30 |
+-----+-------+-------+
```

환경 — PostgreSQL 18.6 · MySQL 8.4.10, MySQL 의 `sql_mode` 에 `STRICT_TRANS_TABLES` 가 켜져 있다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 안 적은 칸은 무엇이 되나 (예측)

```sql
INSERT INTO t49_a (id,name) VALUES (1,'ann'),(2,'bob'),(3,'cho');
SELECT * FROM t49_a ORDER BY id;
```

- `grade`·`price`·`qty`·`total` 네 칸에는 각각 무엇이 들어가 있는가?

### 2. ★★ 부분 실패 — 앞의 것이 남나 (예측)

```sql
-- t49_a 에는 이미 id=1 이 있다
INSERT INTO t49_a (id,name) VALUES (20,'v20'),(1,'dup'),(21,'v21');
```

- 두 엔진에서 각각 무엇이 일어나고, **끝난 뒤 `id=20`·`id=21` 인 행이 존재하는가**?

### 3. ★★ 같은 입력에 `IGNORE` 만 붙이면 (예측)

```sql
INSERT IGNORE INTO t49_a (id,name) VALUES (20,'v20'),(1,'dup'),(21,'v21');
```

- MySQL 8.4.10 에서 2번과 무엇이 달라지고, PostgreSQL 은 이 문을 받는가?

### 4. ★ `IGNORE` 가 `NOT NULL` 을 만나면 (예측)

```sql
INSERT IGNORE INTO t49_a (id) VALUES (30);   -- name 은 NOT NULL 이고 기본값이 없다
SHOW WARNINGS;
SELECT id, CONCAT('[',name,']') AS name_shown, LENGTH(name) AS len FROM t49_a WHERE id=30;
```

- 이 행은 들어가는가? 들어간다면 `name` 에 무엇이 들어 있는가?

### 5. 생성 열에 값을 주면 (예측)

```sql
INSERT INTO t49_a (id,name,total) VALUES (9,'gen',999);
INSERT INTO t49_a VALUES (5,'eve',DEFAULT,7,3,DEFAULT);
```

- 두 문은 각각 두 엔진에서 통과하는가? 통과하면 `total` 은 얼마인가?

### 6. 「전부 기본값인 한 행」 (경계)

```sql
INSERT INTO t49_d DEFAULT VALUES;
INSERT INTO t49_d VALUES ();
```

- 두 문은 두 엔진에서 각각 통과하는가?

### 7. 값 개수가 모자라면 (경계)

```sql
INSERT INTO t49_p VALUES (3);     -- t49_p 는 열이 둘(id, name)이다
```

- 두 엔진에서 각각 어떻게 되는가?

### 8. `NOT NULL` 을 어기는 두 가지 방법 (경계)

```sql
INSERT INTO t49_a (id) VALUES (10);
INSERT INTO t49_a (id,name) VALUES (11,NULL);
```

- 두 문의 에러가 두 엔진에서 각각 같은가, 다른가?

### 9. ★ 외래키를 어기는 삽입 (예측)

```sql
CREATE TABLE t49_c (id int PRIMARY KEY, p_id int REFERENCES t49_p(id), memo varchar(10));
INSERT INTO t49_c VALUES (100, 99, 'orphan');    -- t49_p 에 99 는 없다
```

- 두 엔진에서 각각 이 문이 막히는가?

### 10. `SELECT` 가 0행이면 (경계)

```sql
INSERT INTO t49_a (id,name) SELECT id, name FROM t49_src WHERE price > 999;
```

- 이 문은 에러인가? 적재 스크립트가 여기서 무엇을 놓치게 되나?

### 11. 자기 표에서 읽어 자기 표에 넣으면 (왜)

```sql
INSERT INTO t49_src (id,name,price) SELECT id+100, name, price FROM t49_src;
```

- 3행짜리 표에 몇 행이 들어가고, 왜 무한히 늘지 않는가?

### 12. `LAST_INSERT_ID()` 는 무엇을 돌려주나 (예측)

```sql
INSERT INTO t49_ai (v) VALUES ('d'),('e');   -- 직전까지 1,2,3 이 들어 있었다
SELECT LAST_INSERT_ID();
```

- MySQL 8.4.10 에서 이 값은 얼마인가?

### 13. 길이를 넘기면 (연결)

```sql
INSERT INTO t49_a (id,name) VALUES (31,'abcdefghijklmno');   -- name 은 varchar(10)
```

- 두 엔진에서 각각 어떻게 되고, MySQL 쪽 결과는 무엇에 달려 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
