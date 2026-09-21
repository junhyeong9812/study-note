# sql/06-조건 식 — CASE·COALESCE·NULLIF·GREATEST/LEAST — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · Conditional Expressions](https://www.postgresql.org/docs/18/functions-conditional.html) · [MySQL 8.4 · Flow Control Functions](https://dev.mysql.com/doc/refman/8.4/en/flow-control-functions.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력은 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 지어낸 출력은 없다.\
> **버전** — 네 조건 식 자체는 두 엔진 모두 오래전부터 있다. 이 주제에서 버전에 갈리는 것은 없다.\
> **선행** — [04 NULL 의 3값 논리](../04-null-three-valued-logic/). `CASE` 의 조건이 `UNKNOWN` 이면 어떻게 되는지가 이 주제의 절반이다.

## 한눈에 — 쉽게 말하면

**조건 식은 「값을 고르는 식」이지 「실행을 가르는 문」이 아니다.**

- 자판기를 생각하자. 버튼을 위에서부터 훑어 **처음으로 불이 켜진 버튼**의 상품이 나온다.
- 불이 하나도 안 켜지면? 아래쪽 「기타」 칸(`ELSE`)의 상품이 나온다.
- 「기타」 칸도 없으면? **아무것도 안 나온다** — 그게 `NULL` 이다.
- 중요한 건 이게 **`if` 문이 아니라 값 하나**라는 것이다.\
  `SELECT`·`WHERE`·`ORDER BY`·`GROUP BY` 어디에든 **숫자 하나처럼** 놓을 수 있다.

| 비유 | 실체 |
|---|---|
| 자판기 버튼을 위에서부터 훑기 | `CASE WHEN ... THEN ...` 을 앞에서부터 평가 |
| 처음 불이 켜진 버튼 | 처음 `TRUE` 가 된 `WHEN` 절 |
| 불이 안 켜짐 / 고장 표시 | `FALSE` / `UNKNOWN` — **둘 다 「이 버튼 아님」으로 취급** |
| 「기타」 칸 | `ELSE` |
| 「기타」 칸이 없을 때 나오는 것 | `NULL` |
| "빈 칸이면 기본 상품" 버튼 하나 | `COALESCE` |
| "이 값이면 없던 걸로" 버튼 | `NULLIF` |

```text
CASE WHEN c1 THEN v1
     WHEN c2 THEN v2
     ELSE    v3
END
         ↓ 평가
  c1 이 TRUE 인가?  --예--> v1        <- 여기서 끝. c2 는 보지도 않는다
        |아니오/모름
        v
  c2 가 TRUE 인가?  --예--> v2
        |아니오/모름
        v
      ELSE     --------> v3          <- ELSE 가 없으면 NULL
```

이 자판기가 **똑같은 구조로** SQL 의 조건 식이다.\
그리고 이 주제의 사고 대부분은 **「아니오」와 「모름」이 같은 칸으로 떨어진다**는 데서 나온다.

> **조건 식(conditional expression)** — 조건에 따라 **값 하나**를 고르는 식. 문(statement)이 아니다.\
> 예: `CASE WHEN salary > 400 THEN 'high' ELSE 'low' END` 는 문자열 하나와 같은 자격을 갖는다.

> **단락 평가(short-circuit evaluation)** — 결과가 정해지면 나머지 항을 계산하지 않는 것.\
> 예: `CASE WHEN 1=0 THEN 1/0 ELSE 99 END` 에서 `1/0` 을 계산하지 않아 에러가 안 난다.

## 이 주제가 답하려는 질문

1. **단순 `CASE` 와 검색 `CASE` 는 무엇이 다르고, 왜 단순 `CASE` 로는 `NULL` 을 못 잡나.**
2. **조건 식은 단락 평가되나** — 안 되는 자리는 어디인가.
3. **`NULL` 을 만난 `GREATEST`/`LEAST` 가 왜 두 엔진에서 다른 답을 내나.**

## 예시 데이터 — 이 묶음이 공유하는 것

이 폴더의 SQL 주제들이 **같은 두 표**를 쓴다. 표가 같으면 주제 간 비교가 공짜로 된다.

```text
emp (사원)                          dept (부서)
+----+------+---------+--------+    +----+-------+
| id | name | dept_id | salary |    | id | name  |
+----+------+---------+--------+    +----+-------+
|  1 | ann  |      10 |    300 |    | 10 | sales |
|  2 | bob  |      10 |    500 |    | 20 | dev   |
|  3 | cho  |      20 |   NULL |    | 30 | hr    |  <- 사원이 없는 부서
|  4 | dan  |    NULL |    400 |    +----+-------+
+----+------+---------+--------+
        ^          ^
        |          +-- dan 은 소속이 없다 (dept_id NULL)
        +------------- cho 는 급여가 없다 (salary NULL)
```

이 주제에서는 **`dan` 의 `dept_id NULL`** 이 `CASE` 의 「어느 칸으로도 안 떨어지는 행」을 만들고,\
**`cho` 의 `salary NULL`** 이 `COALESCE`·`NULLIF` 의 과녁이 된다.

## 동작 방식

### 1. 두 가지 `CASE` — 단순형과 검색형

**언제 쓰나** — 값 하나를 여러 값과 견줄 때는 단순형, 조건이 제각각일 때는 검색형.

```text
단순 CASE                          검색 CASE
CASE <식>                          CASE
  WHEN <값1> THEN ...                WHEN <조건1> THEN ...
  WHEN <값2> THEN ...                WHEN <조건2> THEN ...
  ELSE ...                           ELSE ...
END                                END

내부적으로 <식> = <값1> 로 견준다    조건을 그대로 판정한다
   ^^^^^^^^^^^^^^^^^^
   이 "=" 가 이 절의 전부다
```

```text
### SQL: SELECT id, name, CASE dept_id WHEN 10 THEN 'sales' WHEN 20 THEN 'dev' ELSE 'none' END AS simple_case
         FROM emp ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name | simple_case         +----+------+-------------+
----+------+-------------        | id | name | simple_case |
  1 | ann  | sales               +----+------+-------------+
  2 | bob  | sales               |  1 | ann  | sales       |
  3 | cho  | dev                 |  2 | bob  | sales       |
  4 | dan  | none                |  3 | cho  | dev         |
(4 rows)                         |  4 | dan  | none        |
                                 +----+------+-------------+
```

그림 해설 — `dan`(dept_id `NULL`)이 `ELSE` 로 떨어졌다. 여기까지는 의도대로다.\
대가 — 단순형은 **`=` 비교에 묶여 있다.** 범위 조건(`> 400`)·`IS NULL`·`LIKE` 를 쓰려면 검색형으로 가야 한다.

---

### 2. 단순 `CASE` 의 `WHEN NULL` 은 절대 안 맞는다

**언제 쓰나** — 「값이 없는 행을 따로 표시하자」고 생각했을 때. **여기가 함정이다.**

```text
CASE dept_id WHEN NULL THEN '...' ...
              ^^^^^^^^
     내부적으로 dept_id = NULL 로 견준다  ->  언제나 UNKNOWN  ->  절대 TRUE 가 안 된다
```

```text
### SQL: SELECT id, CASE dept_id WHEN NULL THEN 'matched NULL' ELSE 'not matched' END AS c
         FROM emp ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id |      c                     +----+-------------+
----+-------------               | id | c           |
  1 | not matched                +----+-------------+
  2 | not matched                |  1 | not matched |
  3 | not matched                |  2 | not matched |
  4 | not matched                |  3 | not matched |
(4 rows)                         |  4 | not matched |
                                 +----+-------------+
```

**`dan` 도 `not matched` 다.** `dept_id` 가 `NULL` 인 바로 그 행이 `WHEN NULL` 에 안 걸렸다.

검색형으로 `IS NULL` 을 쓰면 잡힌다.

```text
### SQL: SELECT id, CASE WHEN dept_id IS NULL THEN 'matched NULL' ELSE 'not matched' END AS c
         FROM emp ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id |      c                     +----+--------------+
----+--------------              | id | c            |
  1 | not matched                +----+--------------+
  2 | not matched                |  1 | not matched  |
  3 | not matched                |  2 | not matched  |
  4 | matched NULL               |  3 | not matched  |
(4 rows)                         |  4 | matched NULL |
                                 +----+--------------+
```

두 그림의 결론 — **`WHEN NULL` 은 「`NULL` 인 행」이 아니라 「아무것도」를 뜻한다.**\
대가 — 에러가 아니라 **전부 `ELSE` 로 떨어진다.** 「`ELSE` 가 좀 많네」 정도로 보여 리뷰에서 안 잡힌다.\
`NULL` 을 구분하려면 **반드시 검색형 + `IS NULL`** 이다([05번](../05-null-comparison-is-distinct-from/)).

---

### 3. `CASE` 는 단락 평가된다 — 대개는

**언제 쓰나** — 0 나눗셈·형변환 실패처럼 **계산 자체가 터질 수 있는 식**을 조건 뒤에 둘 때.

```text
CASE WHEN 1 = 0 THEN 1/0 ELSE 99 END
          ^^^^^      ^^^
     FALSE 다        평가되지 않는다  ->  에러 없이 99
```

```text
### SQL: SELECT CASE WHEN 1 = 0 THEN 1/0 ELSE 99 END AS r;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 r                               +------+
----                             | r    |
 99                              +------+
(1 row)                          |   99 |
                                 +------+
```

그림 해설 — PG 에서 `1/0` 은 **에러를 던지는 식**인데 에러가 안 났다. `THEN` 항이 평가되지 않은 것이다.

> ⚠️ **MySQL 에서는 이 예제가 단락 평가의 증거가 못 된다.** MySQL 은 `1/0` 자체가 에러가 아니라 `NULL` 이기 때문이다.

```text
### SQL: SELECT 1/0 AS r;
--- PG 18.6 ---
ERROR:  division by zero
--- MySQL 8.4.10 ---
+------+
| r    |
+------+
| NULL |
+------+
```

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| `1/0` | **`ERROR: division by zero`** | **`NULL`**(기본 `sql_mode` 기준) |

대가 — 「0 나눗셈은 에러니까 코드에서 걸러진다」는 가정이 MySQL 에서는 안 통한다. 거기서는 **조용히 `NULL` 이 흘러간다.**

**행 단위 조건에서도 단락 평가가 확인된다.**

```text
### SQL: SELECT id, CASE WHEN salary - 300 <> 0 THEN 1/(salary-300) ELSE -1 END AS r
         FROM emp ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | r                          +----+--------+
----+----                        | id | r      |
  1 | -1                         +----+--------+
  2 |  0                         |  1 |     -1 |
  3 | -1                         |  2 | 0.0050 |
  4 |  0                         |  3 |     -1 |
(4 rows)                         |  4 | 0.0100 |
                                 +----+--------+
```

`ann`(salary 300)에서 `salary - 300 = 0` 이라 `THEN` 항이 안 돌았고, 그래서 **PG 가 에러를 안 냈다.**\
`cho`(salary `NULL`)는 조건이 `UNKNOWN` 이라 역시 `ELSE` 로 갔다 — **「아니오」와 「모름」이 같은 칸**이라는 것이 여기서도 보인다.\
(값이 PG 는 `0`·MySQL 은 `0.0050` 인 것은 정수 나눗셈 차이다 — [36번](../36-numeric-types-and-functions/).)

---

### 4. 단락 평가가 깨지는 자리 — 집계 함수

**언제 쓰나** — `CASE` 안에 `SUM`·`MIN` 같은 집계가 들어갈 때. **여기서 PG 의 보호가 사라진다.**

```text
CASE WHEN COUNT(*) < 0 THEN MIN(1/(salary-300)) ELSE 0 END
          ^^^^^^^^^^^^      ^^^^^^^^^^^^^^^^^^
     절대 참이 아니다        그런데 이 집계는 계산된다
```

```text
### SQL: SELECT CASE WHEN COUNT(*) < 0 THEN MIN(1/(salary-300)) ELSE 0 END AS r FROM emp;
--- PG 18.6 ---
ERROR:  division by zero
--- MySQL 8.4.10 ---
+------+
| r    |
+------+
|    0 |
+------+
```

그림 해설 — **PG 가 에러를 냈다.** `COUNT(*) < 0` 은 절대 참이 될 수 없는데도 `MIN(1/(salary-300))` 이 계산됐고, `ann` 에서 `1/0` 이 터졌다.\
이유는 **집계가 `CASE` 보다 먼저 평가되기 때문**이다 — 집계는 행 전체를 훑어야 값이 나오므로, 「`CASE` 가 그 항에 도달했는가」와 무관하게 돌아간다.

```text
평가 순서
  1) 행을 훑으며 집계값을 만든다      MIN(1/(salary-300))  <- 여기서 터진다
  2) 그 값들을 CASE 에 넣는다         CASE WHEN ... THEN <집계값1> ELSE 0 END
```

MySQL 이 `0` 을 낸 것은 **단락 평가의 증거가 아니다** — MySQL 에서는 `1/0` 이 애초에 에러가 아니라 `NULL` 이라 터질 일이 없다.\
대가 — **「`CASE` 로 감쌌으니 안전하다」는 집계 앞에서 깨진다.** 안전하게 나누려면 `CASE` 가 아니라 `NULLIF` 로 **분모 자체를 `NULL` 로 만든다**(다음 절).

> ⚠️ 같은 식을 **상수 조건**(`WHEN 1 = 0`)으로 쓰면 PG 에서도 에러가 안 났다 — 계획 단계에서 그 항이 통째로 사라졌기 때문으로 보인다.\
> 즉 **조건이 상수냐 아니냐에 따라 결과가 갈린다.** 이런 자리는 「되더라」를 근거로 삼지 말고 구조를 바꾸는 편이 낫다.

---

### 5. `COALESCE` — 앞에서부터 `NULL` 이 아닌 첫 값

**언제 쓰나** — 「값이 없으면 기본값」을 식 수준에서 처리할 때. **출력 직전**에 쓰는 것이 원칙이다.

```text
COALESCE(a, b, c)
    ↓
  a 가 NULL 이 아닌가?  --예--> a
        |아니오
        v
  b 가 NULL 이 아닌가?  --예--> b
        |아니오
        v
        c                        <- 전부 NULL 이면 NULL
```

```text
### SQL: SELECT COALESCE(salary, 0) AS r, id FROM emp ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
  r  | id                        +-----+----+
-----+----                       | r   | id |
 300 |  1                        +-----+----+
 500 |  2                        | 300 |  1 |
   0 |  3                        | 500 |  2 |
 400 |  4                        |   0 |  3 |
(4 rows)                         | 400 |  4 |
                                 +-----+----+
```

```text
### SQL: SELECT COALESCE(NULL, NULL, NULL) AS all_null;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 all_null                        +----------+
----------                       | all_null |
 NULL                            +----------+
(1 row)                          |     NULL |
                                 +----------+
```

그림 해설 — 전부 `NULL` 이면 결과도 `NULL` 이다. `COALESCE` 는 **`NULL` 을 없애 준다고 보장하지 않는다.**\
대가 — 「모름」을 「0」으로 바꾼다는 것은 **도메인 결정**이다. 급여가 기록되지 않은 사람을 0원으로 보는 게 맞는지는 SQL 밖의 문제다.

가장 흔한 정당한 쓰임은 **집계 결과의 `NULL` 을 막는 것**이다.

```text
### SQL: SELECT dept_id, COALESCE(SUM(salary), 0) AS s FROM emp GROUP BY dept_id ORDER BY dept_id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id |  s                    +---------+-----+
---------+-----                  | dept_id | s   |
      10 | 800                   +---------+-----+
      20 |   0                   |    NULL | 400 |
    NULL | 400                   |      10 | 800 |
(3 rows)                         |      20 |   0 |
                                 +---------+-----+
```

`dept_id = 20`(`cho` 혼자, 급여 `NULL`)의 합이 `NULL` 대신 `0` 으로 나왔다([04번](../04-null-three-valued-logic/)에서 본 「전부 `NULL` 인 그룹의 `SUM` 은 `NULL`」의 처방이다).

#### 방언 — 인자 타입이 섞이면

```text
### SQL: SELECT COALESCE(salary, 'none') AS r, id FROM emp ORDER BY id;
--- PG 18.6 ---
ERROR:  invalid input syntax for type integer: "none"
LINE 1: SELECT COALESCE(salary, 'none') AS r, id FROM emp ORDER BY i...
                                ^
--- MySQL 8.4.10 ---
+------+----+
| r    | id |
+------+----+
| 300  |  1 |
| 500  |  2 |
| none |  3 |
| 400  |  4 |
+------+----+
```

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| `COALESCE(정수열, '문자열')` | **에러** — 하나의 타입으로 못 맞춘다 | **통과** — 전부 문자열로 맞춘다 |

그림 해설 — PG 는 「인자들의 타입을 하나로 통일할 수 있어야 한다」를 강하게 요구하고, MySQL 은 조용히 맞춘다.\
대가 — MySQL 에서 돌던 질의가 PG 에서 깨진다. 그리고 **MySQL 쪽에서는 숫자 열이 문자열로 바뀐 것을 결과만 봐서 알기 어렵다**(정렬·비교가 문자열 규칙으로 바뀐다).\
타입 규칙의 정본은 [35번](../35-type-system-and-casting/)이다.

---

### 6. `NULLIF` — 이 값이면 없던 걸로

**언제 쓰나** — 특정 값(대개 `0` 이나 빈 문자열)을 `NULL` 로 바꿔 **연산에서 빠지게** 할 때.

```text
NULLIF(a, b)
    ↓
  a = b 인가?  --예--> NULL
       |아니오/모름
       v
       a
```

가장 중요한 쓰임은 **0 나눗셈 회피**다. 분모를 `NULL` 로 만들면 나눗셈 결과가 `NULL` 이 된다.

```text
### SQL: SELECT NULLIF(300, 300) AS a, NULLIF(300, 500) AS b, NULLIF(NULL, 300) AS c;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
  a   |  b  |  c                 +------+------+------+
------+-----+------              | a    | b    | c    |
 NULL | 300 | NULL               +------+------+------+
(1 row)                          | NULL |  300 | NULL |
                                 +------+------+------+
```

```text
### SQL: SELECT id, salary, 1000 / NULLIF(salary, 0) AS ratio FROM emp ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | salary | ratio             +----+--------+--------+
----+--------+-------            | id | salary | ratio  |
  1 |    300 |     3             +----+--------+--------+
  2 |    500 |     2             |  1 |    300 | 3.3333 |
  3 |   NULL |  NULL             |  2 |    500 | 2.0000 |
  4 |    400 |     2             |  3 |   NULL |   NULL |
(4 rows)                         |  4 |    400 | 2.5000 |
                                 +----+--------+--------+
```

그림 해설 — `cho` 의 `ratio` 가 `NULL` 이다. `NULLIF` 가 아니라 **원래 `salary` 가 `NULL`** 이라서다.\
`NULLIF(salary, 0)` 은 급여가 정확히 0인 사원이 생겼을 때 나눗셈을 막아 준다 — **에러 대신 `NULL` 로 바꾸는 것**이 이 함수의 일이다.\
대가 — `NULL` 이 된 결과는 그 뒤 집계에서 **조용히 건너뛰어진다**([04번](../04-null-three-valued-logic/)). 「에러가 안 났다」가 「계산이 됐다」를 뜻하지 않는다.

`COALESCE` 와 짝지으면 「빈 문자열이면 기본값」이 한 줄로 된다.

```text
### SQL: SELECT COALESCE(NULLIF('', ''), 'default') AS r;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
    r                            +---------+
---------                        | r       |
 default                         +---------+
(1 row)                          | default |
                                 +---------+
```

```text
NULLIF('', '')      ->  NULL        <- 빈 문자열을 "값 없음"으로 바꾼다
COALESCE(NULL, 'default')  ->  'default'
```

---

### 7. `GREATEST`/`LEAST` — `NULL` 을 만나면 두 엔진이 갈린다

**언제 쓰나** — 여러 열 중 최댓값·최솟값을 **행 안에서** 고를 때(집계가 아니다 — 집계는 행을 접는다).

```text
### SQL: SELECT GREATEST(1, 2, 3) AS g, LEAST(1, 2, 3) AS l;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 g | l                           +---+---+
---+---                          | g | l |
 3 | 1                           +---+---+
(1 row)                          | 3 | 1 |
                                 +---+---+
```

`NULL` 이 없으면 똑같다. **하나라도 섞이면 갈린다.**

```text
### SQL: SELECT GREATEST(1, 2, NULL) AS g, LEAST(1, 2, NULL) AS l;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 g | l                           +------+------+
---+---                          | g    | l    |
 2 | 1                           +------+------+
(1 row)                          | NULL | NULL |
                                 +------+------+
```

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| `GREATEST(1, 2, NULL)` | **`2`** — `NULL` 을 건너뛴다 | **`NULL`** — 하나라도 `NULL` 이면 `NULL` |
| `LEAST(1, 2, NULL)` | **`1`** | **`NULL`** |
| 인자가 전부 `NULL` 이면 | `NULL` | `NULL` |

그림 해설 — **PG 는 집계 함수처럼 `NULL` 을 건너뛰고, MySQL 은 비교 연산처럼 `NULL` 에 전염된다.**\
같은 이름의 함수가 **정반대 철학**을 따르는 드문 자리다.\
대가 — 이 차이는 **에러 없이 답만 바꾼다.** MySQL 에서 「최댓값이 왜 자꾸 `NULL` 이지」로 나타나고, PG 에서는 「`NULL` 인 열을 무시해도 되나?」라는 도메인 질문이 조용히 넘어간다.

양쪽에서 같게 만들려면 **`COALESCE` 로 `NULL` 을 먼저 없앤다.**

```text
### SQL: SELECT GREATEST(COALESCE(1, -2147483648), COALESCE(2, -2147483648), COALESCE(NULL, -2147483648)) AS portable_greatest;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 portable_greatest               +-------------------+
-------------------              | portable_greatest |
                 2               +-------------------+
(1 row)                          |                 2 |
                                 +-------------------+
```

`GREATEST` 에는 **충분히 작은 값**, `LEAST` 에는 **충분히 큰 값**을 기본값으로 준다. 다만 그 「충분히」가 도메인 지식이라 깨지기 쉽다 — **`NOT NULL` 제약으로 막는 편이 낫다**(목록의 45번 주제).

---

### 8. MySQL 전용 축약형 — `IF`·`IFNULL`

**언제 쓰나** — MySQL 코드를 읽을 때. **쓰지는 않는다**(이식이 안 된다).

```text
### SQL: SELECT IFNULL(salary, 0) AS r, id FROM emp ORDER BY id;
--- PG 18.6 ---
ERROR:  function ifnull(integer, integer) does not exist
LINE 1: SELECT IFNULL(salary, 0) AS r, id FROM emp ORDER BY id;
               ^
HINT:  No function matches the given name and argument types. You might need to add explicit type casts.
--- MySQL 8.4.10 ---
+-----+----+
| r   | id |
+-----+----+
| 300 |  1 |
| 500 |  2 |
|   0 |  3 |
| 400 |  4 |
+-----+----+
```

```text
### SQL: SELECT IF(salary IS NULL, 'unknown', 'known') AS r, id FROM emp ORDER BY id;
--- PG 18.6 ---
ERROR:  function if(boolean, unknown, unknown) does not exist
LINE 1: SELECT IF(salary IS NULL, 'unknown', 'known') AS r, id FROM ...
               ^
HINT:  No function matches the given name and argument types. You might need to add explicit type casts.
--- MySQL 8.4.10 ---
+---------+----+
| r       | id |
+---------+----+
| known   |  1 |
| known   |  2 |
| unknown |  3 |
| known   |  4 |
+---------+----+
```

| MySQL 전용 | 양쪽에서 도는 대체 |
|---|---|
| `IFNULL(a, b)` | `COALESCE(a, b)` |
| `IF(c, a, b)` | `CASE WHEN c THEN a ELSE b END` |

그림 해설 — PG 의 에러가 「문법 오류」가 아니라 **「그런 함수 없음」**이다. 함수 이름의 문제일 뿐이라 대체가 쉽다.\
대가 — 없다. **`COALESCE` 와 `CASE` 만 쓰면 이 자리가 통째로 사라진다.**

## 문법 — 형태와 규칙

```sql
-- 단순 CASE — 내부적으로 = 로 견준다
CASE <식> WHEN <값> THEN <결과> [WHEN ...] [ELSE <결과>] END

-- 검색 CASE — 조건을 그대로 판정한다
CASE WHEN <조건> THEN <결과> [WHEN ...] [ELSE <결과>] END

COALESCE(a, b, ...)   -- 앞에서부터 NULL 이 아닌 첫 값. 전부 NULL 이면 NULL
NULLIF(a, b)          -- a = b 면 NULL, 아니면 a
GREATEST(a, b, ...)   -- 최댓값. NULL 처리가 엔진마다 다르다
LEAST(a, b, ...)      -- 최솟값. 〃
```

규칙 여섯.

1. **조건 식은 값이다.** `SELECT`·`WHERE`·`ORDER BY`·`GROUP BY`·집계 인자 어디에든 놓인다.
2. **`WHEN` 은 위에서부터 훑고 처음 `TRUE` 에서 멈춘다.** `FALSE` 와 `UNKNOWN` 은 **똑같이** 「이 칸 아님」이다.
3. **`ELSE` 를 생략하면 `NULL` 이다.** 「빠짐없이 덮었다」고 생각한 `CASE` 가 조용히 `NULL` 을 만든다.
4. **단순 `CASE` 의 `WHEN NULL` 은 절대 안 맞는다.** `NULL` 을 잡으려면 검색형 + `IS NULL`.
5. **`CASE` 는 단락 평가되지만 집계 함수는 예외다.** 집계는 `CASE` 보다 먼저 계산된다.
6. **결과 타입은 하나로 통일돼야 한다.** PG 는 못 맞추면 에러, MySQL 은 조용히 맞춘다.

`ELSE` 를 생략했을 때를 직접 확인한 출력이다.

```text
### SQL: SELECT id, CASE WHEN salary > 400 THEN 'high' END AS c FROM emp ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id |  c                         +----+------+
----+------                      | id | c    |
  1 | NULL                       +----+------+
  2 | high                       |  1 | NULL |
  3 | NULL                       |  2 | high |
  4 | NULL                       |  3 | NULL |
(4 rows)                         |  4 | NULL |
                                 +----+------+
```

`cho`(salary `NULL`)의 조건은 `UNKNOWN` 인데 결과는 `ann`·`dan`(조건 `FALSE`)과 **구별되지 않는다.**\
「급여가 400 이하인 사람」과 「급여를 모르는 사람」을 나누려면 `WHEN` 을 하나 더 둬야 한다.

결과 타입 통일도 두 엔진이 갈린다.

```text
### SQL: SELECT CASE WHEN TRUE THEN 1 ELSE 'x' END AS r;
--- PG 18.6 ---
ERROR:  invalid input syntax for type integer: "x"
LINE 1: SELECT CASE WHEN TRUE THEN 1 ELSE 'x' END AS r;
                                          ^
--- MySQL 8.4.10 ---
+---+
| r |
+---+
| 1 |
+---+
```

**조건이 `TRUE` 라서 `ELSE` 는 쓰이지도 않는데 PG 는 거부한다** — 타입 통일은 **값이 아니라 식의 성질**이라 평가 전에 정해지기 때문이다.

## 어디서 틀리나

- **단순 `CASE` 에 `WHEN NULL` 을 쓴다.**\
  절대 안 맞는다. 전부 `ELSE` 로 떨어지고 에러도 없다. 검색형 + `IS NULL` 을 쓴다.
- **`ELSE` 를 빼고 「전부 덮었다」고 믿는다.**\
  조건이 `UNKNOWN` 인 행이 조용히 `NULL` 이 된다. 위 출력의 `cho` 가 그 예다.
- **`FALSE` 와 `UNKNOWN` 을 구분해 줄 거라 기대한다.**\
  `CASE` 는 둘을 똑같이 「이 칸 아님」으로 본다. 나누려면 `WHEN x IS NULL` 을 **먼저** 둔다.
- **`CASE` 로 감싸면 안전하다고 믿는다 — 집계가 끼었을 때.**\
  집계는 `CASE` 보다 먼저 돈다. PG 에서 `division by zero` 를 실제로 봤다.
- **0 나눗셈이 항상 에러라고 믿는다.**\
  PG 는 에러, **MySQL 은 `NULL`** 이다. MySQL 에서는 조용히 흘러간다.
- **`COALESCE` 가 `NULL` 을 없애 준다고 믿는다.**\
  인자가 전부 `NULL` 이면 결과도 `NULL` 이다.
- **`COALESCE` 를 계산 중간에 쓴다.**\
  「몰랐다」는 사실이 그 자리에서 사라진다. 평균·비율이 조용히 틀어진다. **출력 직전**에 쓴다.
- **`GREATEST`/`LEAST` 의 `NULL` 처리가 같을 거라 본다.**\
  PG 는 건너뛰고(`2`), MySQL 은 `NULL` 이다. **에러 없이 답만 갈린다.**
- **`IFNULL`·`IF` 를 쓴다.**\
  MySQL 전용이다. `COALESCE`·`CASE` 로 쓰면 양쪽에서 돈다.
- **`COALESCE` 인자에 타입을 섞는다.**\
  PG 는 에러, MySQL 은 전부 문자열로 바꾼다. MySQL 쪽에서는 **정렬·비교 규칙이 조용히 바뀐다.**

## 구현 세부사항 대 언어 보장

| 항목 | 누가 보장하나 | 근거 |
|---|---|---|
| `WHEN` 을 앞에서부터 훑어 첫 `TRUE` 에서 멈추는 것 | **양쪽 문서가 정한 규칙** | 두 엔진 동일 출력 |
| 단순 `CASE` 가 `=` 로 견주는 것 | **양쪽 문서가 정한 규칙** | `WHEN NULL` 이 양쪽에서 안 맞음 |
| `ELSE` 생략 시 `NULL` | **양쪽 문서가 정한 규칙** | 두 엔진 동일 출력 |
| `COALESCE`·`NULLIF` 의 의미 | **양쪽 문서가 정한 규칙** | 두 엔진 동일 출력 |
| `CASE` 의 단락 평가 | **대체로 보장** — 단 **집계는 예외** | PG `division by zero` 실측 |
| 상수 조건에서 `THEN` 항이 통째로 사라지는 것 | **옵티마이저 구현** | 같은 식이 상수 조건일 때만 에러가 안 났다 |
| `1/0` 의 결과 | **엔진 선택** | PG 에러 / MySQL `NULL` |
| `GREATEST`/`LEAST` 의 `NULL` 처리 | **엔진 선택** | PG `2` / MySQL `NULL` |
| 결과 타입 통일 실패 시 | **엔진 선택** | PG 에러 / MySQL 암시 변환 |

정리하면 — **`CASE` 의 평가 규칙과 `COALESCE`·`NULLIF` 의 의미만 언어 보장이고, `NULL` 과 타입이 걸리면 전부 엔진 선택이다.**

## 언제 쓰고 언제 안 쓰나

- **`NULL` 이 섞일 수 있으면 무조건 검색 `CASE`.** 단순형은 `=` 에 묶여 있어 `NULL` 을 못 다룬다.
- **`ELSE` 는 항상 적는다.** 적을 값이 없으면 `ELSE NULL` 이라도 적어 「의도한 `NULL`」임을 남긴다.
- **0 나눗셈 회피는 `CASE` 가 아니라 `NULLIF`.** 분모를 `NULL` 로 만드는 쪽이 집계 앞에서도 안전하다.
- **`COALESCE` 는 출력 직전에만.** 계산 중간에 덮으면 「몰랐다」가 사라진다.
- **`GREATEST`/`LEAST` 는 이식 코드에 쓰지 않는다.** 꼭 써야 하면 `COALESCE` 로 `NULL` 을 먼저 없앤다.
- **`IFNULL`·`IF` 는 읽기만 하고 쓰지 않는다.** `COALESCE`·`CASE` 가 양쪽에서 돈다.
- **조건 분기가 세 갈래를 넘으면 `CASE` 가 아니라 매핑 표를 의심한다.** 코드에 박힌 분기는 데이터가 바뀔 때 같이 안 바뀐다.

## 핵심 문장

- 조건 식은 **문이 아니라 값**이다. 어디에나 숫자처럼 놓인다.
- `CASE` 는 **`FALSE` 와 `UNKNOWN` 을 똑같이** 「이 칸 아님」으로 본다.
- **단순 `CASE` 의 `WHEN NULL` 은 절대 안 맞는다.** 내부가 `=` 이기 때문이다.
- **`ELSE` 를 빼면 `NULL`** 이다 — 「전부 덮었다」는 착각이 여기서 난다.
- `CASE` 는 단락 평가되지만 **집계 함수는 먼저 계산된다.** PG 에서 실제로 터졌다.
- **`GREATEST`/`LEAST` 의 `NULL` 처리가 정반대다** — PG 는 건너뛰고 MySQL 은 `NULL` 이다.
- **`1/0` 이 PG 는 에러, MySQL 은 `NULL`** 이다. 「에러로 잡힌다」는 가정이 안 통한다.

## 관련 자료

- [PostgreSQL 18 · Conditional Expressions](https://www.postgresql.org/docs/18/functions-conditional.html) — `CASE`·`COALESCE`·`NULLIF`·`GREATEST`/`LEAST` 가 한 페이지에 있다.
- [MySQL 8.4 · Flow Control Functions](https://dev.mysql.com/doc/refman/8.4/en/flow-control-functions.html) — `CASE`·`IF`·`IFNULL`·`NULLIF`.
- [04 NULL 의 3값 논리](../04-null-three-valued-logic/) — **경계: 그쪽은 `UNKNOWN` 이 왜 생기나까지, 여기는 그 `UNKNOWN` 이 `CASE` 의 어느 칸으로 떨어지나부터.**
- [05 NULL 비교](../05-null-comparison-is-distinct-from/) — **경계: 그쪽은 `NULL` 을 「비교」하는 법, 여기는 `NULL` 을 「다른 값으로 바꾸는」 법.**
- [01 논리적 질의 처리 순서](../01-logical-query-processing-order/) — 집계가 `SELECT` 보다 먼저라는 것이 4절의 전제다.
- [35 타입 체계와 캐스팅](../35-type-system-and-casting/) — **경계: 타입 통일·암시 변환은 그쪽, 여기는 그것이 `CASE`·`COALESCE` 에서 어떻게 터지나.**
- [36 수치 타입과 수치 함수](../36-numeric-types-and-functions/) — **경계: 정수 나눗셈과 `1/0` 의 결과는 그쪽, 여기는 그 결과가 조건 식의 단락 평가 증거가 되는 것까지.**
- **`NOT NULL` 제약**은 목록의 **45번 주제**가 정본이다.
- [24 조건부 집계 — FILTER 와 CASE](../24-conditional-aggregation-filter-case/) — **경계: 그쪽은 `CASE` 를 집계와 엮는 패턴, 여기는 식 하나의 평가 규칙까지.**
- [SQL 주제 목록](../README.md)

## 용어 풀이

- **조건 식(conditional expression)** — 조건에 따라 값 하나를 고르는 식. 문이 아니다.\
  예: `CASE WHEN salary > 400 THEN 'high' ELSE 'low' END`.
- **단순 `CASE`** — `CASE <식> WHEN <값> ...` 형태. 내부적으로 `=` 로 견준다.\
  예: `CASE dept_id WHEN 10 THEN 'sales' END`.
- **검색 `CASE`** — `CASE WHEN <조건> ...` 형태. 조건을 그대로 판정한다.\
  예: `CASE WHEN dept_id IS NULL THEN 'none' END`.
- **단락 평가(short-circuit evaluation)** — 결과가 정해지면 나머지를 계산하지 않는 것.\
  예: `CASE WHEN 1=0 THEN 1/0 ELSE 99 END` 이 PG 에서 에러를 안 낸다.
- **`COALESCE`** — 앞에서부터 `NULL` 이 아닌 첫 값을 돌려주는 함수.\
  예: `COALESCE(salary, 0)` 은 `cho` 의 급여를 0으로 보이게 한다.
- **`NULLIF`** — 두 값이 같으면 `NULL`, 아니면 첫 값을 돌려주는 함수.\
  예: `1000 / NULLIF(salary, 0)` 은 0 나눗셈을 `NULL` 로 바꾼다.
- **`GREATEST`/`LEAST`** — 인자 중 최댓값·최솟값을 고르는 함수. **행 안의 계산**이지 집계가 아니다.\
  예: `GREATEST(1, 2, NULL)` 은 PG 에서 `2`, MySQL 에서 `NULL`.
- **타입 통일(type unification)** — 여러 갈래의 결과 타입을 하나로 맞추는 일.\
  예: `CASE WHEN TRUE THEN 1 ELSE 'x' END` 은 PG 에서 에러다.
- **암시 변환(implicit cast)** — 적지 않았는데 엔진이 알아서 타입을 바꾸는 것.\
  예: MySQL 의 `COALESCE(salary, 'none')` 이 숫자를 문자열로 바꾼다.
- **`sql_mode`** — MySQL 의 문법·검사 엄격도 설정 묶음.\
  예: `1/0` 이 `NULL` 인 것은 기본 `sql_mode` 기준의 동작이다.

## 더 들어가면

- **`CASE` 로 정렬 순서를 만드는 것**은 이 식이 「값」이라는 성질을 가장 잘 쓰는 자리다. `ORDER BY CASE WHEN salary IS NULL THEN 0 ELSE 1 END, salary DESC` 는 두 엔진에서 **같은 순서**를 낸다 — `NULLS FIRST` 문법이 없는 MySQL 에서도 통한다([08번](../08-order-by-null-position-stability/)).
- **`COALESCE` 를 어디에 두는가가 설계 결정이다.** 저장할 때 덮으면 원본이 사라지고, 질의 중간에 덮으면 집계가 틀어지고, 출력 직전에 덮으면 둘 다 피한다. **덮는 자리가 뒤로 갈수록 정보가 오래 남는다.**
- **`GREATEST`/`LEAST` 의 두 철학 중 어느 쪽이 옳은가**는 답이 없다. PG 쪽은 「집계처럼 `NULL` 을 건너뛴다」, MySQL 쪽은 「비교 연산처럼 `NULL` 에 전염된다」로 각자 일관적이다. 외울 것은 어느 쪽이 맞느냐가 아니라 **「이 함수는 엔진마다 다르다」**는 사실 하나다.
