# sql/39-collation (문자열 비교와 정렬의 기준) — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,\
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.\
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.

대상은 **PostgreSQL 18.6** 과 **MySQL 8.4.10** 두 서버다. 「두 엔진에서」라고 물으면 **각각** 답한다.

★ **이 주제는 환경이 곧 답이다.** 아래 설정에서 나온 결과를 묻는 것이고,\
다른 설정이면 **같은 엔진에서도 답이 달라진다.**

```text
PG     pg_database.datcollate    = en_US.utf8     (datlocprovider = c → libc)
       server_encoding            = UTF8
MySQL  @@collation_server         = utf8mb4_0900_ai_ci
       @@collation_connection     = utf8mb4_0900_ai_ci
       (클라이언트를 --default-character-set=utf8mb4 로 붙였다)
```

정렬 실험은 이 여섯 값으로 한다.

```text
'apple'   'Banana'   'apricot'   'BANANA'   '_x'   'Zebra'
```

인덱스 실험은 두 엔진에 같은 모양으로 만든 표 `t39`(20,000행, `code varchar(20)` 에 인덱스)를 쓴다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 0. 환경을 어떻게 확인하나 (연결)

- 두 엔진에서 「지금 이 서버의 비교 규칙이 무엇인가」를 확인하는 명령은 각각 무엇인가?

### 1. ★ 같은 비교, 다른 답 (예측)

```sql
SELECT 'abc' = 'ABC' AS same_case, 'e' = 'é' AS accent, 'a' = 'a ' AS trailing_space;
```

- 세 값이 두 엔진에서 각각 무엇인가?

### 2. ★ 여섯 값을 줄 세우면 (예측)

```sql
-- 'apple' 'Banana' 'apricot' 'BANANA' '_x' 'Zebra' 를
ORDER BY v;                          -- (a) 기본
ORDER BY v COLLATE "C";              -- (b) PG
ORDER BY v COLLATE utf8mb4_bin;      -- (b) MySQL
```

- (a) 와 (b) 의 순서가 두 엔진에서 각각 어떻게 나오는가?

### 3. ★ 같은 DDL, 다른 결과 (예측)

```sql
CREATE TABLE t (v varchar(10) UNIQUE);
INSERT INTO t VALUES ('abc');
INSERT INTO t VALUES ('ABC');
```

- 두 엔진에서 각각 무엇이 일어나는가?

### 4. PG 에서 대소문자를 무시하려면 (경계)

- PG 에서 `'abc' = 'ABC'` 를 참으로 만들려면 무엇을 해야 하는가?

### 5. 뒤 공백 (예측)

```sql
SELECT 'a' = 'a ' COLLATE utf8mb4_general_ci AS pad_space,
       'a' = 'a ' COLLATE utf8mb4_0900_ai_ci AS no_pad;
```

- MySQL 에서 두 값이 무엇이고, 그 차이를 만드는 칸의 이름은 무엇인가?

### 6. 섞으면 (예측)

```sql
-- PG
SELECT ('abc' COLLATE "C") = ('ABC' COLLATE "en_US.utf8") AS r;
-- MySQL
SELECT ('abc' COLLATE utf8mb4_0900_as_cs) = ('ABC' COLLATE utf8mb4_general_ci) AS r;
```

- 두 문이 각각 어떻게 되는가?

### 7. ★ `COLLATE` 의 대가 (예측)

```sql
EXPLAIN SELECT * FROM t39 WHERE code = 'C000123';                        -- (a)
EXPLAIN SELECT * FROM t39 WHERE code COLLATE "C" = 'C000123';            -- (b) PG
EXPLAIN SELECT * FROM t39 WHERE code = 'C000123' COLLATE utf8mb4_bin;    -- (b) MySQL
```

- (a) 와 (b) 의 계획이 두 엔진에서 각각 어떻게 달라지는가?

### 8. 이름을 읽는 법 (경계)

- `utf8mb4_0900_as_ci` 는 무엇을 구분하고 무엇을 무시하는가?

### 9. `\dO` 가 0행이면 (경계)

- PG 에서 `\dO` 가 0행이라는 것은 「collation 이 없다」는 뜻인가?

### 10. 정렬이 왜 불안정한가 (왜)

- 같은 데이터가 서버를 옮겼을 때 다르게 줄 설 수 있는 이유는 무엇인가?

### 11. 그래서 어디에 적어야 하나 (연결)

- 「아이디는 대소문자를 구분하지 않는다」는 요구사항을 두 엔진에서 어디에 어떻게 적어야 하는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
