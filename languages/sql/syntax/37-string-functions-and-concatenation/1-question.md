# sql/37-문자열 함수와 연결 연산 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,\
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.\
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.

대상은 **PostgreSQL 18.6** 과 **MySQL 8.4.10** 두 서버다. 「두 엔진에서」라고 물으면 **각각** 답한다.

조건을 밝혀 둔다 — 이 답들은 이 환경에서 나온 것이다.

```text
PG    server_encoding = UTF8
MySQL character_set_server = utf8mb4, 클라이언트도 utf8mb4
      sql_mode 는 기본값 — PIPES_AS_CONCAT 이 들어 있지 않다
```

예시 표는 이 폴더의 주제들이 공유한다. 이 주제는 `emp`·`dept` 를 읽기만 한다.

```text
emp (사원)                          dept (부서)
+----+------+---------+--------+    +----+-------+
| id | name | dept_id | salary |    | id | name  |
+----+------+---------+--------+    +----+-------+
|  1 | ann  |      10 |    300 |    | 10 | sales |
|  2 | bob  |      10 |    500 |    | 20 | dev   |
|  3 | cho  |      20 |   NULL |    | 30 | hr    |
|  4 | dan  |    NULL |    400 |    +----+-------+
+----+------+---------+--------+
```

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★ 문자열을 붙이는 연산자 (예측)

```sql
SELECT 'a' || 'b' AS r;
```

- 두 엔진에서 각각 무엇이 나오는가?

### 2. 그 값이 왜 그 값인가 (왜)

```sql
SELECT 1 || 0 AS a, 0 || 0 AS b, 'x' || 1 AS c;
```

- MySQL 의 세 결과가 1번의 답을 어떻게 설명하는가?

### 3. ★ `NULL` 이 섞이면 (예측)

```sql
SELECT 'a' || NULL AS pipe, CONCAT('a', NULL) AS con, CONCAT_WS('-','a',NULL,'b') AS ws;
```

- 세 값이 두 엔진에서 각각 무엇인가?

### 4. ★ 길이를 세면 (예측)

```sql
SELECT LENGTH('한글abc') AS len, CHAR_LENGTH('한글abc') AS clen, OCTET_LENGTH('한글abc') AS olen;
SELECT LENGTH(CAST(1234567 AS CHAR)) AS len;
```

- 네 값이 두 엔진에서 각각 무엇인가?

### 5. 범위를 벗어난 자르기 (예측)

```sql
SELECT SUBSTRING('abcdef', 0, 3) AS zero_start, SUBSTRING('abcdef', -2) AS neg;
```

- 두 값이 두 엔진에서 각각 무엇인가?

### 6. 대소문자는 누가 정하나 (예측)

```sql
SELECT 'abc' = 'ABC' AS same_case;
```

- 두 엔진에서 각각 무엇이 나오고, 그것을 정하는 것은 무엇인가?

### 7. 갈리지 않는 것 (경계)

- `TRIM`·`REPLACE`·`UPPER`·`LPAD`·`REPEAT`·`REVERSE`·`POSITION` 중 두 엔진에서 다르게 도는 것이 있는가?

### 8. 설정으로 고칠 수 있나 (경계)

- MySQL 에서 `||` 를 연결로 쓰는 방법이 있는가 — 있다면 왜 그것을 처방으로 삼지 않는가?

### 9. 두 엔진에서 같게 만들려면 (연결)

- `NULL` 이 섞일 수 있는 열들을 이어 붙일 때, 두 엔진에서 같은 답을 보장하는 작성법은 무엇인가?

### 10. 길이 검증을 어떻게 쓰나 (연결)

- 「이름은 10글자까지」라는 요구사항을 두 엔진에서 같게 구현하려면 무엇을 쓰는가?

### 11. 왜 `WHERE` 에 문자열 함수를 안 쓰나 (연결)

- `WHERE UPPER(name) = 'ANN'` 이 두 엔진에서 각각 무엇을 잃게 만드는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
