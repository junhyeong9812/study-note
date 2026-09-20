# sql/52-UPSERT (ON CONFLICT · ON DUPLICATE KEY UPDATE) — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,\
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.\
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.

예시 테이블은 이 폴더의 네 주제가 공유한다. 이 주제는 `dept` 만 쓴다.

```text
dept                                CREATE TABLE dept (
+----+-------+                        id   int PRIMARY KEY,     -- 유니크 제약 1
| id | name  |                        name text UNIQUE NOT NULL -- 유니크 제약 2
+----+-------+                      );
| 10 | sales |
| 20 | dev   |
| 30 | hr    |
+----+-------+
```

아래 질의는 전부 `BEGIN` / `ROLLBACK` 으로 감싸 돌린다 — 매번 위 세 행에서 시작한다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 왜 두 문으로 나누면 안 되나 (왜)

- `SELECT` 로 존재를 확인한 뒤 `INSERT` 또는 `UPDATE` 하는 코드는 무엇이 문제인가?

### 2. ★ 같은 입력, 다른 답 (예측)

```sql
-- PG
INSERT INTO dept VALUES (40, 'hr') ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name;
-- MySQL
INSERT INTO dept VALUES (40, 'hr') AS new ON DUPLICATE KEY UPDATE name = new.name;
```

- 두 엔진에서 각각 무엇이 일어나고, 끝난 뒤 `id = 40` 인 행이 존재하는가?

### 3. 영향 행 수 (예측)

```sql
INSERT INTO dept VALUES (40,'legal')  AS new ON DUPLICATE KEY UPDATE name = new.name;
INSERT INTO dept VALUES (40,'legal2') AS new ON DUPLICATE KEY UPDATE name = new.name;
INSERT INTO dept VALUES (40,'legal2') AS new ON DUPLICATE KEY UPDATE name = new.name;
```

- MySQL 8.4.10 에서 세 문의 `ROW_COUNT()` 는 각각 얼마인가?

### 4. 삽입인가 갱신인가 (경계)

- 한 upsert 문이 삽입했는지 갱신했는지를 확실히 알아내는 방법이 두 엔진에 각각 있는가?

### 5. 대상을 안 적으면 (경계)

```sql
INSERT INTO dept VALUES (30,'people') ON CONFLICT DO UPDATE SET name = EXCLUDED.name;
INSERT INTO dept VALUES (40,'hr')     ON CONFLICT DO NOTHING;
```

- PostgreSQL 18.6 에서 두 문은 각각 통과하는가?

### 6. 한 문 안에 같은 키가 둘 (예측)

```sql
INSERT INTO dept VALUES (40,'legal'), (40,'legal2') ... 충돌 처리 ...
```

- 두 엔진에서 각각 무엇이 일어나는가?

### 7. 조건부 갱신 (연결)

- 「넣으려는 값이 기존 값보다 클 때만 덮어써라」를 두 엔진에서 각각 어떻게 쓰는가?

### 8. `RETURNING` (경계)

```sql
INSERT INTO dept VALUES (50,'tmp') RETURNING id, name;
```

- MySQL 8.4.10 에서 이 문은 도는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
