# sql/46-인덱스 정의 (복합·부분·표현식·커버링) — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,\
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.\
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.

대상은 **PostgreSQL 18.6** 과 **MySQL 8.4.10** 두 서버다. 「두 엔진에서」라고 물으면 **각각** 답한다.\
★ 이 편은 「**어떻게 정의하나**」만 묻는다. **「그래서 탈까 안 탈까」는 [47번]**(../47-when-indexes-are-used/)이다.

```text
t46 (20,000행) — 이 편이 만들었다가 지운 표
+--------+-------------+-----------------------------------------+
| id     | int PK      | 1 .. 20000                              |
| a      | int         | id % 100   -> 값 100가지, 각 200행       |
| b      | int         | id % 10    -> 값 10가지, 각 2000행       |
| code   | varchar(20) | 'C000001' .. 'C020000'                  |
| v      | varchar(30) | 'name1' .. 'name20000'                  |
| status | varchar(10) | 'ACTIVE' 20행 · 'DONE' 19,980행          |
+--------+-------------+-----------------------------------------+
```

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 복합 인덱스가 저장하는 순서 (왜)

- `CREATE INDEX i ON t46 (a, b)` 가 만드는 정렬 순서를 그림으로 그리면 무엇인가?

### 2. ★ `(a,b)` 와 `(b,a)` (경계)

- 이 둘은 같은 인덱스인가 — 아니라면 어느 조건에서 갈리는가?

### 3. ★ 부분 인덱스 (예측)

```sql
CREATE INDEX t46_part_idx ON t46 (id) WHERE status = 'ACTIVE';
```

- 두 엔진에서 각각 어떻게 되고, 만들어진 쪽에서는 **몇 개 항목**이 들어가는가?

### 4. 부분 인덱스가 줄이는 두 가지 (왜)

- 부분 인덱스가 일반 인덱스보다 싼 이유 **두 가지**는 무엇인가?

### 5. ★ 표현식 인덱스의 괄호 (예측)

```sql
CREATE INDEX i ON t46 (lower(v));     -- (a)
CREATE INDEX i ON t46 ((lower(v)));   -- (b)
```

- 두 엔진에서 (a)·(b) 는 각각 어떻게 되는가?

### 6. ★ 접두 길이 (예측)

```sql
CREATE INDEX t46_pref_idx ON t46 (code(10));
```

- 두 엔진에서 각각 무엇이 나오고, **PG 의 에러 문구가 왜 그렇게 나오는가**?

### 7. 커버링 (예측)

```sql
CREATE INDEX t46_inc_idx ON t46 (a) INCLUDE (b);
```

- 두 엔진에서 각각 어떻게 되고, `(a, b)` 로 만드는 것과 무엇이 다른가?

### 8. ★ `UNIQUE` 인덱스와 `UNIQUE` 제약 (경계)

```sql
CREATE UNIQUE INDEX t46_uix ON t46 (code);            -- (A)
ALTER TABLE t46 ADD CONSTRAINT t46_ucon UNIQUE (v);   -- (B)
```

- 두 엔진의 카탈로그에서 (A)·(B) 는 어떻게 구분되는가?

### 9. 지울 때 (예측)

```sql
DROP INDEX t46_ucon;   -- PG
DROP INDEX t46_uix;    -- PG
```

- 두 문은 각각 어떻게 되는가?

### 10. 조건부 유일성 (예측)

```sql
ALTER TABLE t46 ADD CONSTRAINT t46_pu UNIQUE (code) WHERE status='ACTIVE';  -- (a)
CREATE UNIQUE INDEX t46_pu ON t46 (code) WHERE status='ACTIVE';             -- (b)
```

- PG 에서 (a)·(b) 는 각각 어떻게 되고, 그 차이가 무엇을 뜻하는가?

### 11. ★ 생성 열에 인덱스 (예측)

```sql
CREATE INDEX i ON t45_gv (total);   -- total 이 VIRTUAL
CREATE INDEX i ON t45_gs (total);   -- total 이 STORED
```

- 두 엔진에서 각각 어떻게 되고, 그것이 [45번](../45-check-not-null-default-generated-columns/)의 기본값과 어떻게 이어지는가?

### 12. 인덱스를 만들 때 무엇이 잠기나 (예측)

- PG 의 `CREATE INDEX` 가 잡는 잠금은 무엇이고, [42번의 `ALTER TABLE`](../42-create-alter-drop-table/)과 무엇이 다른가?

### 13. `CONCURRENTLY` 의 대가 (경계)

```sql
BEGIN; CREATE INDEX CONCURRENTLY i ON t46 (b); COMMIT;
```

- 이 문은 어떻게 되는가?

### 14. ★ `USING HASH` (예측)

```sql
CREATE INDEX i ON t46 (b) USING HASH;     -- (a)
CREATE INDEX i ON t46 USING hash (b);     -- (b)
```

- 두 엔진에서 (a)·(b) 는 각각 어떻게 되고, **통과한 쪽에서는 무엇이 만들어지는가**?

### 15. 없는 열에 (예측)

```sql
CREATE INDEX i ON t46 (nosuch);
```

- 두 엔진에서 각각 무엇이 나오고, 6번의 에러와 왜 다른가?

### 16. 그래서 무엇을 안 만드나 (연결)

- 인덱스를 **만들지 않기로 결정**할 때의 기준 세 가지는 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
