# sql/45-CHECK·NOT NULL·DEFAULT·생성 열·자동 증가 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,\
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.\
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.

대상은 **PostgreSQL 18.6** 과 **MySQL 8.4.10** 두 서버다. 「두 엔진에서」라고 물으면 **각각** 답한다.\
MySQL 의 `sql_mode` 에는 `STRICT_TRANS_TABLES` 가 켜져 있다.

이 편이 쓴 표는 전부 직접 만들었다가 지운 것이다. `emp`·`dept` 는 읽지 않는다.

```text
t45_chk                                   t45_gs / t45_gv / t45_gd
+-------+------------------------+        +-------+--------------------------+
| id    | int PRIMARY KEY        |        | id    | int PRIMARY KEY          |
| qty   | int CHECK (qty > 0)    |        | price | int                      |
| name  | varchar(10) NOT NULL   |        | qty   | int                      |
| grade | varchar(5) DEFAULT 'B' |        | total | GENERATED AS (price*qty) |
+-------+------------------------+        +-------+--------------------------+
                                            gs = STORED · gv = VIRTUAL · gd = 키워드 없음
```

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ `CHECK` 열에 `NULL` 을 넣으면 (예측)

```sql
INSERT INTO t45_chk (id,qty,name) VALUES (1,-5,'ann');   -- (a)
INSERT INTO t45_chk (id,qty,name) VALUES (2,NULL,'bob'); -- (b)
```

- 두 엔진에서 (a)·(b) 는 각각 어떻게 되는가?

### 2. ★ 왜 그런가 (왜)

- 1번 (b) 의 결과를 `CHECK` 의 판정 규칙 한 줄로 설명하면 무엇인가?

### 3. `WHERE` 와 `CHECK` 는 `UNKNOWN` 을 같이 다루나 (경계)

- 같은 `UNKNOWN` 을 `WHERE` 절과 `CHECK` 제약이 각각 어떻게 다루는가?

### 4. `NOT NULL` 을 어기면 (예측)

```sql
INSERT INTO t45_chk (id,qty,name) VALUES (3,5,NULL);
```

- 두 엔진에서 각각 무엇이 나오고, **에러 메시지의 `grade` 칸은 무엇으로 찍히는가**?

### 5. ★ `DEFAULT CURRENT_TIMESTAMP` 는 언제 계산되나 (예측)

```sql
CREATE TABLE t45_def (id int PRIMARY KEY, ts timestamp DEFAULT CURRENT_TIMESTAMP);
INSERT INTO t45_def (id) VALUES (1);
-- 2초 뒤
INSERT INTO t45_def (id) VALUES (2);
```

- 두 행의 `ts` 는 같은가 다른가 — 두 엔진에서 각각?

### 6. `DEFAULT` 를 바꾸면 기존 행은 (예측)

```sql
ALTER TABLE t45_def ALTER COLUMN g SET DEFAULT 'Z';
INSERT INTO t45_def (id) VALUES (3);
```

- `id` 1·2·3 의 `g` 는 각각 무엇인가?

### 7. ★ `CHECK` 에 못 쓰는 것 (예측)

```sql
CREATE TABLE t45_cs (id int, CHECK (id IN (SELECT id FROM t45_chk)));   -- (a)
CREATE TABLE t45_cn (d date, CHECK (d <= CURRENT_DATE));                -- (b)
```

- 두 엔진에서 (a)·(b) 는 각각 어떻게 되는가?

### 8. 7번 (b) 를 받아 주는 쪽의 위험 (왜)

- 한 엔진이 (b) 를 받아 준다면, 그 제약이 나중에 무엇과 어긋날 수 있는가?

### 9. ★ 생성 열의 `STORED` 와 `VIRTUAL` (예측)

```sql
... total int GENERATED ALWAYS AS (price*qty) STORED     -- (a)
... total int GENERATED ALWAYS AS (price*qty) VIRTUAL    -- (b)
... total int GENERATED ALWAYS AS (price*qty)            -- (c)
```

- 세 문이 두 엔진에서 각각 어떻게 되고, (c) 는 무엇이 되는가?

### 10. ★ 생성 열에 직접 대입하면 (예측)

```sql
INSERT INTO t45_gs (id,price,qty,total) VALUES (2,100,3,999);   -- (a)
UPDATE t45_gs SET total=999 WHERE id=1;                         -- (b)
INSERT INTO t45_gs (id,price,qty,total) VALUES (3,10,2,DEFAULT);-- (c)
```

- 세 문이 두 엔진에서 각각 어떻게 되는가?

### 11. ★ 자동 증가 세 이름 (예측)

```sql
CREATE TABLE a (id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY);  -- (a)
CREATE TABLE b (id serial PRIMARY KEY);                            -- (b)
CREATE TABLE c (id int AUTO_INCREMENT PRIMARY KEY);                -- (c)
```

- 세 문이 두 엔진에서 각각 어떻게 되고, **그중 가장 위험한 것은 무엇인가**?

### 12. 그래서 어떻게 설계하나 (연결)

- 「수량은 반드시 양수」라는 요구를 두 엔진에서 빠짐없이 강제하려면 무엇을 쓰는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
