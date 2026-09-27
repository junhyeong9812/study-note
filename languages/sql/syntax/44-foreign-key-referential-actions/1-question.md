# sql/44-외래키와 참조 동작 (ON DELETE·ON UPDATE) — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,\
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.\
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.

대상은 **PostgreSQL 18.6** 과 **MySQL 8.4.10** 두 서버다. 「두 엔진에서」라고 물으면 **각각** 답한다.\
MySQL 의 `@@foreign_key_checks` 는 **`1`(켜짐)** 이다.

이 편이 쓴 표는 전부 직접 만들었다가 지운 것이다. `emp`·`dept` 는 읽지 않는다.

```text
t44_p (부모)                자식들 — ON DELETE 만 서로 다르다
+----+-------+              t44_c          (절 없음)      -> 10, 20
| id | name  |              t44_noaction   NO ACTION      -> 30
+----+-------+              t44_restrict   RESTRICT       -> 40
| 10 | sales |              t44_cascade    CASCADE        -> 50
| 20 | dev   |              t44_setnull    SET NULL       -> 60
| 30 | a     |              t44_sd         SET DEFAULT    -> 80  (pid 의 DEFAULT 는 20)
| 40 | b     |
| 50 | c     |              자식마다 다른 부모 행을 가리키게 해서
| 60 | d     |              한 동작씩 따로 발동시킬 수 있게 했다
| 80 | f     |
+----+-------+
```

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ 열 뒤에 `REFERENCES` 를 쓰면 (예측)

```sql
CREATE TABLE t44_c (id int PRIMARY KEY, pid int REFERENCES t44_p(id), name varchar(10));
INSERT INTO t44_c VALUES (3,99,'cho');     -- 부모에 99 는 없다
DELETE FROM t44_p WHERE id=10;             -- 자식이 10 을 가리키는 중
```

- 두 엔진에서 세 문이 각각 어떻게 되는가?

### 2. 1번의 결과를 어떻게 미리 아는가 (연결)

- 외래키가 실제로 만들어졌는지 확인하는 방법은 두 엔진에서 각각 무엇인가?

### 3. 외래키가 막는 두 방향 (경계)

- 표 수준 `FOREIGN KEY` 로 제대로 만들었을 때, 막히는 두 가지 조작은 각각 무엇이고 MySQL 의 에러 코드는 무엇인가?

### 4. `NULL` 인 참조 열 (예측)

```sql
INSERT INTO t44_c VALUES (4,NULL,'dan');
```

- 두 엔진에서 각각 어떻게 되고, 왜 그런가?

### 5. ★★ `ON DELETE` 네 동작 (예측)

```sql
DELETE FROM t44_p WHERE id=30;   -- NO ACTION
DELETE FROM t44_p WHERE id=40;   -- RESTRICT
DELETE FROM t44_p WHERE id=50;   -- CASCADE
DELETE FROM t44_p WHERE id=60;   -- SET NULL
```

- 네 문이 각각 어떻게 되고, 자식 표는 어떻게 남는가?

### 6. ★ MySQL 에서 `NO ACTION` 과 `RESTRICT` 는 같은가 (경계)

- 두 엔진에서 각각 같은가 다른가 — 그리고 **그 판정의 근거가 되는 실험**은 무엇인가?

### 7. ★ 다섯째 동작 (예측)

```sql
CREATE TABLE t44_sd (id int PRIMARY KEY, pid int DEFAULT 20,
  FOREIGN KEY (pid) REFERENCES t44_p(id) ON DELETE SET DEFAULT);
DELETE FROM t44_p WHERE id=80;
```

- 두 엔진에서 각각 어떻게 되고, **스키마만 읽어서는 왜 알 수 없는가**?

### 8. ★ 외래키가 인덱스를 요구하나 (예측)

- `FOREIGN KEY (pid) REFERENCES t44_p(id)` 를 선언한 뒤 `pid` 에 인덱스가 있는가 — 두 엔진에서 각각?

### 9. 그 인덱스는 무엇에 쓰이나 (왜)

- 8번의 인덱스가 없으면 어떤 조작이 느려지는가?

### 10. `ON UPDATE CASCADE` (예측)

```sql
UPDATE t44_up SET id=7 WHERE id=1;     -- 자식 t44_uc 가 1 을 가리키는 중
```

- 자식의 `pid` 는 어떻게 되는가?

### 11. ★ `SET NULL` 인데 자식 열이 `NOT NULL` 이면 (예측)

```sql
CREATE TABLE t44_snn (id int PRIMARY KEY, pid int NOT NULL,
  FOREIGN KEY (pid) REFERENCES t44_p(id) ON DELETE SET NULL);
-- 그리고 부모를 지운다
```

- 두 엔진에서 **언제** 막히는가?

### 12. 부모 열이 유일하지 않으면 (예측)

```sql
CREATE TABLE t44_np (id int, v int);
CREATE TABLE t44_nc (id int PRIMARY KEY, pid int, FOREIGN KEY (pid) REFERENCES t44_np(id));
```

- 두 엔진에서 각각 어떻게 되고, 그 이유는 무엇인가?

### 13. 그래서 어떻게 고르나 (연결)

- 「부모가 지워지면 자식은?」에 답할 때 네(또는 다섯) 동작 중 무엇을 고를지의 판단 기준은 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
