# sql/06-조건 식 — CASE·COALESCE·NULLIF·GREATEST/LEAST — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력은 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 문서를 보고 적은 출력은 없다.\
> 문서 근거는 [PG 18 Conditional Expressions](https://www.postgresql.org/docs/18/functions-conditional.html) · [MySQL 8.4 Flow Control Functions](https://dev.mysql.com/doc/refman/8.4/en/flow-control-functions.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. 단순 `CASE` 와 검색 `CASE` 의 차이

**단순형은 값 하나를 여러 값과 `=` 로 견주고, 검색형은 조건을 그대로 판정한다.**

```text
단순 CASE                            검색 CASE
CASE dept_id                         CASE
  WHEN 10 THEN 'sales'                 WHEN dept_id = 10 THEN 'sales'
  WHEN 20 THEN 'dev'                   WHEN salary > 400 THEN 'rich'
  ELSE 'none'                          WHEN dept_id IS NULL THEN 'none'
END                                  END
      ↑                                     ↑
 dept_id = 10 으로 전개된다            조건이 무엇이든 된다
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

**단순형이 `=` 에 묶여 있다는 것이 모든 차이의 원인이다.**

| | 단순 `CASE` | 검색 `CASE` |
|---|---|---|
| 쓸 수 있는 조건 | **`=` 비교만** | 아무 조건이나 |
| `> 400` 같은 범위 | 불가 | 가능 |
| `IS NULL` | **불가** (2번 참조) | 가능 |
| 읽기 | 대상이 한 번만 적혀 짧다 | 조건마다 대상을 반복 |

**둘 다 「위에서부터 훑어 처음 `TRUE` 에서 멈춘다」는 점은 같다.**\
그리고 두 형태 모두 **`FALSE` 와 `UNKNOWN` 을 구분하지 않는다** — 둘 다 「이 칸 아님」이다.

---

### 2. `CASE dept_id WHEN NULL THEN ...` 에서 `dan` 의 결과

**출력**

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

**`dan` 도 `not matched` 다. 네 행 전부 `ELSE` 로 떨어졌다.**

**왜 그런가** — 단순형의 `WHEN NULL` 은 `dept_id = NULL` 로 전개된다.

```text
dan 의 dept_id 는 NULL 이다

  WHEN NULL  ->  dept_id = NULL
             ->  NULL = NULL
             ->  UNKNOWN            <- TRUE 가 아니다
             ->  이 칸 아님 -> ELSE
```

**「`NULL` 인 행」을 뜻하는 것이 아니라 「아무것도」를 뜻한다.** `WHEN NULL` 절은 존재 자체가 무의미하다.

검색형 + `IS NULL` 로 바꾸면 잡힌다.

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

**무서운 것은 에러가 아니라는 점이다.** 문법도 타입도 맞다. 결과가 그럴듯해서 리뷰를 통과한다.\
`IS NULL` 이 유일한 방법이라는 것은 [05번](../05-null-comparison-is-distinct-from/)에서 본 규칙 그대로다.

---

### 3. `ELSE` 를 뺐을 때의 네 값과 `cho`/`ann` 의 구별

**출력**

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

**`ann`·`cho`·`dan` 이 전부 `NULL` 이다. 구별되지 않는다.**

**왜 그런가** — 두 가지가 겹쳤다.

```text
 id | salary | salary > 400 | CASE 의 처분
----+--------+--------------+---------------
  1 |    300 | FALSE        | 이 칸 아님 -> ELSE 없음 -> NULL
  2 |    500 | TRUE         | 'high'
  3 |   NULL | UNKNOWN      | 이 칸 아님 -> ELSE 없음 -> NULL   <- FALSE 와 같은 칸
  4 |    400 | FALSE        | 이 칸 아님 -> ELSE 없음 -> NULL
```

1. **`ELSE` 를 생략하면 `NULL` 이다** — 「덮지 못한 행」이 조용히 `NULL` 이 된다.
2. **`FALSE` 와 `UNKNOWN` 이 같은 칸으로 떨어진다** — 「급여가 400 이하」와 「급여를 모름」이 구별되지 않는다.

셋을 나누려면 `WHEN` 을 하나 더, `ELSE` 도 적는다.

```sql
CASE WHEN salary IS NULL THEN 'unknown'   -- 이 줄을 먼저 둬야 한다
     WHEN salary > 400   THEN 'high'
     ELSE 'low'
END
```

**`IS NULL` 절을 위에 두는 순서가 중요하다.** 아래에 두면 앞 `WHEN` 들이 전부 `UNKNOWN` 으로 흘려보낸 뒤라 결과는 같지만, 읽는 사람이 의도를 못 읽는다.

---

### 4. `CASE WHEN 1 = 0 THEN 1/0 ELSE 99 END` 의 결과

**출력**

```text
### SQL: SELECT CASE WHEN 1 = 0 THEN 1/0 ELSE 99 END AS r;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 r                               +------+
----                             | r    |
 99                              +------+
(1 row)                          |   99 |
                                 +------+
```

**양쪽 다 `99` 다. 그런데 MySQL 의 결과는 단락 평가의 증거가 못 된다.**

**왜 그런가** — MySQL 에서는 `1/0` 이 애초에 에러가 아니다.

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

| | PG 18.6 | MySQL 8.4.10 |
|---|---|---|
| `1/0` 단독 | **`ERROR: division by zero`** | **`NULL`** |
| `CASE ... THEN 1/0 ELSE 99` | `99` → **평가 안 됐다는 증거** | `99` → **아무것도 증명 못 한다** |

```text
PG 의 추론                          MySQL 의 추론
1/0 은 던지면 에러다                1/0 은 던져도 NULL 이다
그런데 에러가 안 났다                에러가 안 났다
 -> THEN 항이 평가되지 않았다        -> 평가됐는지 아닌지 알 수 없다
```

**이것이 「같은 실험을 두 엔진에 던져야 하는」 이유다.** 한쪽에서만 결론이 선다.

행 단위 조건에서도 PG 의 단락 평가가 확인된다 — `ann`(salary 300)에서 분모가 0인데 에러가 안 났다.

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

(`cho` 가 `-1` 인 것은 조건이 `UNKNOWN` → `ELSE` 이기 때문이고, 값이 PG `0` · MySQL `0.0050` 인 것은 정수 나눗셈 차이다 — [36번](../36-numeric-types-and-functions/).)

---

### 5. 집계가 낀 `CASE` — PG 는 무엇을 돌려주나

**출력**

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

**PG 18.6 은 `ERROR: division by zero` 를 던진다.** `COUNT(*) < 0` 은 절대 참이 될 수 없는데도.

**왜 그런가** — **집계 함수는 `CASE` 보다 먼저 평가된다.**

```text
평가 순서
 1) 행을 전부 훑으며 집계값을 만든다
      COUNT(*)              -> 4
      MIN(1/(salary-300))   -> ann 에서 1/0  ->  여기서 터진다
 2) 만들어진 값들을 CASE 에 넣는다
      CASE WHEN 4 < 0 THEN <집계2> ELSE 0 END
```

집계는 「행 전체를 접는」 연산이라 **`CASE` 의 어느 항에 있든 한 번은 계산돼야** 한다. 단락 평가가 여기까지는 못 간다.

**MySQL 의 `0` 은 반증이 아니다** — MySQL 에서 `1/0` 은 `NULL` 이라 터질 일이 없다. 이 실험은 **PG 에서만 결론이 선다.**

> ⚠️ **같은 식이라도 조건이 상수면 PG 도 에러를 안 냈다.**
>
> ```text
> ### SQL: SELECT CASE WHEN 1 = 0 THEN MIN(1/(salary-300)) ELSE 0 END AS r FROM emp;
> --- PG 18.6 ---                  --- MySQL 8.4.10 ---
>  r                               +------+
> ---                              | r    |
>  0                               +------+
> (1 row)                          |    0 |
>                                  +------+
> ```
>
> 조건이 상수 `1 = 0` 이면 계획 단계에서 그 항이 통째로 사라진 것으로 보인다.\
> **즉 「`CASE` 안의 집계가 평가되나」는 조건이 상수냐에 따라 갈린다.** 이런 자리는 「되더라」를 근거로 삼지 말아야 한다.

**실무 처방** — 0 나눗셈은 `CASE` 로 감싸지 말고 **`NULLIF` 로 분모를 `NULL` 로 만든다**(9번).\
`NULLIF` 는 조건 분기가 아니라 **값 변환**이라 집계 앞뒤 어디서든 같게 동작한다.

---

### 6. `CASE WHEN TRUE THEN 1 ELSE 'x' END` 을 거부하는 엔진

**PostgreSQL 18.6 이 거부한다.**

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

**왜 그런가** — `CASE` 는 **식**이고, 식에는 **타입이 하나** 있어야 한다.

```text
CASE WHEN TRUE THEN 1 ELSE 'x' END
                    ^      ^
                 integer  text
                    \      /
              이 식의 타입은 무엇인가?   <- 값을 계산하기 전에 정해져야 한다
```

조건이 `TRUE` 라 `ELSE` 항이 **쓰이지 않는데도** 거부하는 것이 핵심이다 — **타입 통일은 값이 아니라 식의 성질**이라 평가 이전에 결정된다.

MySQL 은 `'x'` 를 정수 문맥으로 끌고 가 조용히 통과시킨다. 이것이 안전한 게 아니라 **문제를 나중으로 미루는 것**이다 — 조건이 바뀌어 `ELSE` 가 쓰이는 날 `0` 같은 값이 나온다.

| | PG 18.6 | MySQL 8.4.10 |
|---|---|---|
| 타입이 안 맞는 `CASE` | **즉시 에러** | 암시 변환으로 통과 |
| 언제 알게 되나 | **작성 즉시** | 그 분기가 실제로 쓰일 때 |

암시 변환 규칙의 정본은 [35번](../35-type-system-and-casting/)이다.

---

### 7. `COALESCE(NULL, NULL, NULL)` 의 결과

**출력**

```text
### SQL: SELECT COALESCE(NULL, NULL, NULL) AS all_null;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 all_null                        +----------+
----------                       | all_null |
 NULL                            +----------+
(1 row)                          |     NULL |
                                 +----------+
```

**`NULL` 이다. 「`COALESCE` 를 쓰면 `NULL` 이 사라진다」는 믿음이 깨진다.**

**왜 그런가** — `COALESCE` 가 하는 일은 「`NULL` 제거」가 아니라 「**`NULL` 이 아닌 첫 값 고르기**」다.

```text
COALESCE(a, b, c)
    ↓
  a 가 NULL 이 아닌가?  --예--> a
        |아니오
  b 가 NULL 이 아닌가?  --예--> b
        |아니오
        c                        <- c 도 NULL 이면 NULL
```

**마지막 인자에 `NULL` 이 아닌 값이 있어야 `NULL` 이 안 나온다.**\
`COALESCE(a, b)` 에서 `b` 가 다른 열이면 그 열도 `NULL` 일 수 있다 — 그때는 아무것도 보장되지 않는다.

정당한 쓰임은 **마지막 인자가 상수**일 때다.

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

`dept_id = 20`(`cho` 혼자, 급여 `NULL`)의 합이 `NULL` 대신 `0` 이다 — 「전부 `NULL` 인 그룹의 `SUM` 은 `NULL`」([04번](../04-null-three-valued-logic/))의 처방이다.

---

### 8. `COALESCE(salary, 'none')` — 두 엔진의 결과

**출력**

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

**PG 는 에러, MySQL 은 전부 문자열로 바꿔 통과한다.**

**왜 그런가** — `COALESCE` 도 식이므로 **인자 타입이 하나로 통일**돼야 한다.

```text
PG                                 MySQL
integer 와 text 를 하나로?          전부 문자열로 맞춘다
  -> 'none' 을 integer 로 읽어 본다   -> 300, 500, 'none', 400  (전부 문자열)
  -> 실패 -> 에러
```

**MySQL 쪽 결과가 더 위험하다.** 에러가 안 났지만 **열의 타입이 숫자에서 문자열로 바뀌었다.**

```text
숫자 열이었을 때의 정렬     문자열이 된 뒤의 정렬
  300, 400, 500            '300', '400', '500', 'none'
                            ^ 사전순이라 '1000' 이 '300' 보다 앞이다
```

즉 이후의 **비교·정렬·집계가 전부 문자열 규칙**으로 바뀐다. 결과만 봐서는 알아채기 어렵다.\
처방은 **기본값의 타입을 열에 맞추는 것**이다 — `COALESCE(salary, 0)`.

---

### 9. `NULLIF(salary, 0)` 이 무엇을 무엇으로 바꾸나

**분모가 0인 경우를 `NULL` 로 바꿔, 나눗셈 결과를 에러 대신 `NULL` 로 만든다.**

```text
NULLIF(a, b)
    ↓
  a = b 인가?  --예--> NULL
       |아니오/모름
       a

1000 / NULLIF(salary, 0)
         ↓ salary 가 0 이면
       1000 / NULL   ->  NULL     <- 에러가 아니라 "값 없음"
```

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

**`CASE` 대신 `NULLIF` 를 쓰는 이유는 5번에 있다.**

```text
CASE WHEN salary <> 0 THEN 1000/salary ELSE NULL END
     ^^^^^^^^^^^^^^^^^^
   조건 분기라서 집계 앞에서 단락 평가가 깨질 수 있다

1000 / NULLIF(salary, 0)
       ^^^^^^^^^^^^^^^^
   값 변환이라서 어디서든 같게 동작한다
```

`COALESCE` 와 짝지으면 「빈 값이면 기본값」이 한 줄이 된다.

```text
### SQL: SELECT COALESCE(NULLIF('', ''), 'default') AS r;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
    r                            +---------+
---------                        | r       |
 default                         +---------+
(1 row)                          | default |
                                 +---------+
```

**대가** — `NULL` 이 된 값은 뒤이은 집계에서 **조용히 건너뛰어진다**([04번](../04-null-three-valued-logic/)). 「에러가 안 났다」가 「계산에 들어갔다」를 뜻하지 않는다.

---

### 10. `GREATEST(1, 2, NULL)` 과 `LEAST(1, 2, NULL)`

**출력**

```text
### SQL: SELECT GREATEST(1, 2, NULL) AS g, LEAST(1, 2, NULL) AS l;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 g | l                           +------+------+
---+---                          | g    | l    |
 2 | 1                           +------+------+
(1 row)                          | NULL | NULL |
                                 +------+------+
```

**PG 는 `2`/`1`, MySQL 은 둘 다 `NULL` 이다.**

`NULL` 이 없으면 결과가 같다는 것도 확인해 두면 차이의 원인이 분명해진다.

```text
### SQL: SELECT GREATEST(1, 2, 3) AS g, LEAST(1, 2, 3) AS l;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 g | l                           +---+---+
---+---                          | g | l |
 3 | 1                           +---+---+
(1 row)                          | 3 | 1 |
                                 +---+---+
```

**왜 그런가** — 같은 이름인데 **철학이 정반대**다.

```text
PG                                MySQL
집계 함수처럼 NULL 을 건너뛴다      비교 연산처럼 NULL 에 전염된다
 GREATEST(1,2,NULL) = 2            GREATEST(1,2,NULL) = NULL
 인자가 전부 NULL 이어야 NULL       하나만 NULL 이어도 NULL
```

| | PG 18.6 | MySQL 8.4.10 |
|---|---|---|
| `GREATEST(1, 2, NULL)` | `2` | `NULL` |
| `LEAST(1, 2, NULL)` | `1` | `NULL` |
| 전부 `NULL` | `NULL` | `NULL` |

**이 차이는 에러 없이 답만 바꾼다.** MySQL 에서는 「최댓값이 왜 자꾸 `NULL` 이지」로 드러나기라도 하지만, PG 에서는 **`NULL` 인 열을 무시해도 되는지가 검토 없이 지나간다.**

양쪽에서 같게 하려면 `COALESCE` 로 먼저 `NULL` 을 없앤다.

```text
### SQL: SELECT GREATEST(COALESCE(1, -2147483648), COALESCE(2, -2147483648), COALESCE(NULL, -2147483648)) AS portable_greatest;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 portable_greatest               +-------------------+
-------------------              | portable_greatest |
                 2               +-------------------+
(1 row)                          |                 2 |
                                 +-------------------+
```

다만 그 「충분히 작은 값」이 도메인 지식이라 깨지기 쉽다 — **열에 `NOT NULL` 을 거는 쪽이 근본 처방**이다([목록의 **45번 주제**](../45-check-not-null-default-generated-columns/)).

---

### 11. `IFNULL`·`IF` 의 이식 가능한 대체

**`IFNULL(a, b)` → `COALESCE(a, b)` · `IF(c, a, b)` → `CASE WHEN c THEN a ELSE b END`.**

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

**왜 그런가** — 둘 다 MySQL 의 축약형이다. PG 의 에러가 「문법 오류」가 아니라 「**그런 함수 없음**」인 것이 힌트다 — 문법 구조는 함수 호출로 읽혔고 이름만 없다.

`COALESCE` 로 바꾼 같은 질의는 양쪽에서 돈다.

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

| MySQL 전용 | 양쪽에서 도는 대체 | 대가 |
|---|---|---|
| `IFNULL(a, b)` | `COALESCE(a, b)` | 없음 — 글자 수만 조금 늘어난다 |
| `IF(c, a, b)` | `CASE WHEN c THEN a ELSE b END` | 없음 |

**`IFNULL` 과 `NULLIF` 는 이름이 닮았지만 정반대다** — 앞은 `NULL` 을 값으로 바꾸고, 뒤는 값을 `NULL` 로 바꾼다. `NULLIF` 는 **양쪽 엔진에 다 있다.**

---

### 12. `COALESCE` 를 저장 시점·계산 중간·출력 직전 중 어디에 두나

**출력 직전이 원칙이다.**

```text
저장 시점에 덮는다
  emp 에 salary = 0 으로 넣는다
  -> "급여를 모른다" 와 "급여가 0원이다" 가 영원히 구별 불가
  -> 정보가 사라진다. 복구 불가

계산 중간에 덮는다
  AVG(COALESCE(salary, 0))
  -> 분모가 COUNT(*) 가 되어 평균이 내려간다
  -> 1200/4 = 300  (진짜 평균 400 과 다르다)

출력 직전에 덮는다
  SELECT COALESCE(AVG(salary), 0) ...
  -> 계산은 NULL 을 건너뛰고, 화면에만 0 이 보인다
```

가운데 항목은 [04번](../04-null-three-valued-logic/)에서 확인한 값으로 검산된다 — `AVG(salary)` 는 `1200/3 = 400` 이지 `1200/4 = 300` 이 아니다.

| 덮는 자리 | 정보 손실 | 계산 오염 | 언제 쓰나 |
|---|---|---|---|
| 저장 시점 | **영구 손실** | — | 도메인상 진짜로 0일 때만 |
| 계산 중간 | 없음 | **있다** | 「모름을 0으로 세는 것」이 요구사항일 때만 |
| 출력 직전 | 없음 | 없음 | **기본값** |

**한 문장으로** — **덮는 자리가 뒤로 갈수록 정보가 오래 남는다.**\
그리고 애초에 「모름」이 도메인상 의미가 없다면 **`NOT NULL` + 기본값**으로 스키마에서 막는 편이 가장 강하다([목록의 **45번 주제**](../45-check-not-null-default-generated-columns/)).

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| 단순 / 검색 `CASE` (1번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | |
| ★ `WHEN NULL` (2번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | `IS NULL` 판과 대조 |
| `ELSE` 생략 (3번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `FALSE`/`UNKNOWN` 이 같은 칸 |
| 단락 평가 (4번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | `1/0` 단독 실행 포함 — **MySQL 에서는 증거가 안 된다** |
| ★ 집계가 낀 `CASE` (5번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | **PG `division by zero` 가 근거** · 상수 조건판 대조 |
| 타입 통일 (6번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **에러 메시지가 근거** |
| `COALESCE` 전부 `NULL` (7번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | `SUM` 처방 포함 |
| `COALESCE` 타입 혼합 (8번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **에러 메시지가 근거** |
| `NULLIF` (9번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | 상수·열·`COALESCE` 조합 |
| ★ `GREATEST`/`LEAST` + `NULL` (10번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | `NULL` 없는 판과 대조 · 이식 형태 |
| `IFNULL`·`IF` (11번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **양쪽 에러 메시지가 근거** |
| `COALESCE` 위치 (12번) | — | — | 04번의 `AVG` 실측값으로 검산 |

**구현 의존 항목** — 5번의 「상수 조건이면 에러가 안 난다」가 대표적이다. **계획 단계 최적화의 결과**로 보이며 버전·통계에 따라 달라질 수 있다.\
6·8번의 암시 변환, 4번의 `1/0` 결과도 엔진 선택이다 — MySQL 의 `1/0` 은 `sql_mode` 설정에 걸린다.

**언어 보장 항목** — 1·2·3·7·9·11번. `WHEN` 을 앞에서부터 훑는 것, 단순 `CASE` 가 `=` 로 견주는 것,\
`ELSE` 생략이 `NULL` 인 것, `COALESCE`·`NULLIF` 의 의미는 **두 엔진에서 같았다.**

**버전** — 이 주제에서 버전에 갈리는 것은 없다. 다음 버전에서는 **4·5·6·8·10번**(엔진 선택·최적화가 걸린 자리)을 다시 돌린다.
