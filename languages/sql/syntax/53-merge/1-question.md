# sql/53-MERGE — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,\
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.\
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.

★ **이 주제는 한쪽에서만 결론이 선다.** MySQL 8.4.10 에는 `MERGE` 가 없다 — 그것을 확인하는 것이 1번이고,\
나머지 문항의 동작은 전부 PostgreSQL 18.6 의 것이다.

```text
t53_tgt (대상)                      t53_src (원본)
+----+------+-----+                 +----+------+-----+
| id | name | qty |                 | id | name | qty |
+----+------+-----+                 +----+------+-----+
|  1 | ann  |  10 |  <- 원본에 없다  |  2 | bob2 |  99 |
|  2 | bob  |  20 |                 |  3 | cho  |  30 |  <- 값이 같다
|  3 | cho  |  30 |                 |  4 | dan  |  40 |  <- 대상에 없다
+----+------+-----+                 +----+------+-----+

t53_dup : (2,'x',1), (2,'y',2)   -- id=2 가 둘
```

아래 질의는 전부 `BEGIN`/`ROLLBACK` 으로 감싸 돌린다 — 매번 위 상태에서 시작한다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★ MySQL 에 `MERGE` 를 던지면 (예측)

```sql
MERGE INTO t53_tgt t USING t53_src s ON t.id = s.id
  WHEN MATCHED THEN UPDATE SET name = s.name, qty = s.qty
  WHEN NOT MATCHED THEN INSERT (id,name,qty) VALUES (s.id,s.name,s.qty);
```

- MySQL 8.4.10 은 무슨 에러를 내고, 그 번호가 뜻하는 것은 무엇인가?

### 2. 기본형이 만드는 표 (예측)

- 위 문을 PostgreSQL 18.6 에 던지면 `t53_tgt` 네 행이 각각 어떻게 되고, 보고되는 행 수는 얼마인가?

### 3. `WHEN` 절의 순서 (예측)

```sql
MERGE INTO t53_tgt t USING t53_src s ON t.id = s.id
  WHEN MATCHED AND s.qty > t.qty THEN UPDATE SET qty = s.qty
  WHEN MATCHED                   THEN DO NOTHING
  WHEN NOT MATCHED               THEN INSERT (id,name,qty) VALUES (s.id,s.name,s.qty);
```

- `id=3`(양쪽 다 `qty=30`) 은 어떻게 되고, 보고되는 행 수는 얼마인가?

### 4. `WHEN NOT MATCHED` 를 빼면 (경계)

```sql
MERGE INTO t53_tgt t USING t53_src s ON t.id = s.id
  WHEN MATCHED THEN UPDATE SET qty = s.qty;
```

- `id=4`(원본에만 있다) 는 어떻게 되는가? 에러인가?

### 5. ★★ `MERGE` 만 되는 일 (예측)

```sql
MERGE INTO t53_tgt t USING t53_src s ON t.id = s.id
  WHEN MATCHED               THEN UPDATE SET name=s.name, qty=s.qty
  WHEN NOT MATCHED           THEN INSERT (id,name,qty) VALUES (s.id,s.name,s.qty)
  WHEN NOT MATCHED BY SOURCE THEN DELETE;
```

- `id=1` 은 어떻게 되고, 이 일을 upsert 한 문으로 할 수 있는가?

### 6. ★★ upsert 만 되는 일 (예측)

```sql
ALTER TABLE t53_tgt ADD CONSTRAINT t53_tgt_name_uq UNIQUE (name);
MERGE INTO t53_tgt t USING (SELECT 9 AS id, 'ann' AS name, 5 AS qty) s ON t.id = s.id
  WHEN MATCHED     THEN UPDATE SET qty = s.qty
  WHEN NOT MATCHED THEN INSERT (id,name,qty) VALUES (s.id,s.name,s.qty);
```

- 이 문은 통과하는가? 같은 입력을 `ON CONFLICT (name)` 으로 쓰면 어떻게 되는가?

### 7. 동시 삽입에는 무엇을 쓰나 (연결)

- 다른 세션이 같은 키를 동시에 넣을 수 있을 때 PostgreSQL 문서는 `MERGE` 와 `INSERT … ON CONFLICT` 중 무엇을 권하는가?

### 8. 원본에 중복이 있으면 (예측)

```sql
MERGE INTO t53_tgt t USING t53_dup s ON t.id = s.id WHEN MATCHED THEN UPDATE SET qty = s.qty;
```

- 무엇이 일어나고, 같은 상황을 `UPDATE … FROM` 으로 던졌을 때와 어떻게 다른가?

### 9. 무엇을 했는지 돌려받기 (예측)

```sql
MERGE INTO t53_tgt t USING t53_src s ON t.id = s.id
  WHEN MATCHED               THEN UPDATE SET qty = s.qty
  WHEN NOT MATCHED           THEN INSERT (id,name,qty) VALUES (s.id,s.name,s.qty)
  WHEN NOT MATCHED BY SOURCE THEN DELETE
  RETURNING merge_action(), t.id, t.name, t.qty;
```

- 어떤 결과가 나오는가?

### 10. 버전 (경계)

- `MERGE` 는 PostgreSQL 어느 버전부터이고, 그 안에서도 나중에 들어온 것은 무엇인가?

### 11. 52 와의 경계 (연결)

- 「들어오는 행을 반영한다」와 「두 표를 맞춘다」 중 어느 쪽이 52이고 어느 쪽이 53인가?

### 12. 원본이 비어 있으면 (경계)

- 5번의 문에서 `t53_src` 가 0행이면 `t53_tgt` 는 어떻게 되는가? 무엇을 먼저 확인해야 하는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
