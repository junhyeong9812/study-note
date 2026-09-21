# sql/08-ORDER BY — 정렬 키·NULL 위치·정렬 안정성 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력은 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 문서를 보고 적은 출력은 없다.\
> 동률 순서는 **각 엔진에서 같은 질의를 10회씩** 돌려 확인했다(5번).\
> 문서 근거는 [PG 18 SELECT](https://www.postgresql.org/docs/18/sql-select.html) · [MySQL 8.4 ORDER BY Optimization](https://dev.mysql.com/doc/refman/8.4/en/order-by-optimization.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. `ORDER BY salary` 의 행 순서

**출력**

```text
### SQL: SELECT id, salary FROM emp ORDER BY salary;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | salary                     +----+--------+
----+--------                    | id | salary |
  1 |    300                     +----+--------+
  4 |    400                     |  3 |   NULL |
  2 |    500                     |  1 |    300 |
  3 |   NULL                     |  4 |    400 |
(4 rows)                         |  2 |    500 |
                                 +----+--------+
```

**PG 는 `300, 400, 500, NULL` · MySQL 은 `NULL, 300, 400, 500` 이다.**

**왜 그런가** — 두 엔진이 `NULL` 을 정렬에서 다르게 취급한다.

```text
PG 18.6                              MySQL 8.4.10
NULL 을 "가장 큰 값" 으로 본다         NULL 을 "가장 작은 값" 으로 본다
  ASC  -> 작은 것부터 -> NULL 이 끝      ASC  -> 작은 것부터 -> NULL 이 처음
```

**주의할 것** — 이것은 [04번](../04-null-three-valued-logic/)의 비교 규칙과 **다른 층위의 규칙**이다.

```text
비교에서는                    정렬에서는
NULL > 400  ->  UNKNOWN       NULL 이 400 보다 뒤 (PG) / 앞 (MySQL)
NULL = NULL ->  UNKNOWN       NULL 끼리는 같은 자리에 모인다
```

정렬은 「참/거짓」이 아니라 **줄을 세워야 끝나는 일**이라, `UNKNOWN` 으로 둘 수가 없다.\
그래서 엔진이 **「`NULL` 을 어디에 둘지」를 따로 정해야 했고, 두 엔진이 반대로 정한 것**이다.

---

### 2. `ORDER BY salary DESC` 로 「상위 1명」을 뽑으면

**출력**

```text
### SQL: SELECT id, salary FROM emp ORDER BY salary DESC;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | salary                     +----+--------+
----+--------                    | id | salary |
  3 |   NULL                     +----+--------+
  2 |    500                     |  2 |    500 |
  4 |    400                     |  4 |    400 |
  1 |    300                     |  1 |    300 |
(4 rows)                         |  3 |   NULL |
                                 +----+--------+
```

**PG 에서는 `cho`(급여 모름), MySQL 에서는 `bob`(500) 이 1등이다.**

**왜 그런가** — 1번의 규칙을 `DESC` 로 뒤집은 것뿐이다. PG 는 `NULL` 이 가장 크므로 내림차순에서 맨 앞이다.

```text
"급여 상위 1명" 이라는 요구사항

PG   ORDER BY salary DESC LIMIT 1  ->  cho   <- 급여를 모르는 사람
MySQL 같은 질의                     ->  bob   <- 의도한 답
```

**이것이 이 주제에서 가장 비싼 사고다.**

```text
에러가 나나?              안 난다
숫자가 이상한가?           NULL 이라 "값 없음" 으로 보인다
테스트에서 잡히나?         NULL 인 행이 없는 데이터면 안 잡힌다
언제 드러나나?             급여 미입력 사원이 한 명 생겼을 때
```

처방은 둘 — PG 전용이면 `DESC NULLS LAST`, 이식이 필요하면 `WHERE salary IS NOT NULL` 을 명시하거나 4번의 키를 쓴다.\
**어느 쪽이든 「기본값에 기대지 않는 것」이 핵심**이다.

---

### 3. `ORDER BY salary NULLS FIRST` 를 받아 주는 엔진

**PostgreSQL 18.6 만 받아 준다.**

```text
### SQL: SELECT id, salary FROM emp ORDER BY salary NULLS FIRST;
--- PG 18.6 ---
 id | salary
----+--------
  3 |   NULL
  1 |    300
  4 |    400
  2 |    500
(4 rows)
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near 'NULLS FIRST' at line 1
```

```text
### SQL: SELECT id, salary FROM emp ORDER BY salary DESC NULLS LAST;
--- PG 18.6 ---
 id | salary
----+--------
  2 |    500
  4 |    400
  1 |    300
  3 |   NULL
(4 rows)
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near 'NULLS LAST' at line 1
```

**왜 그런가** — MySQL 8.4.10 에는 이 문법 자체가 없다. `ERROR 1064` 는 **파서가 그 토큰을 모른다**는 뜻이다.

| | PG 18.6 | MySQL 8.4.10 |
|---|---|---|
| `ASC` 기본 | 맨 뒤 | 맨 앞 |
| `DESC` 기본 | 맨 앞 | 맨 뒤 |
| `NULLS FIRST`/`LAST` | **있다** | **없다** |

**재미있는 대응이 하나 있다** — PG 의 `DESC NULLS LAST` 결과(`500, 400, 300, NULL`)가 **MySQL 의 `DESC` 기본 결과와 같다.**\
즉 MySQL 습관대로 쓰려면 PG 에서 매번 한 마디를 더 적어야 한다. 반대로 PG 습관은 MySQL 에서 **아예 적을 수가 없다.**

---

### 4. `NULLS LAST` 를 못 쓸 때 추가하는 정렬 키

**`(salary IS NULL)` 을 첫 번째 정렬 키로 넣는다.** 양쪽 엔진에서 돈다.

```text
ORDER BY (salary IS NULL), salary
          ^^^^^^^^^^^^^^^^
    값이 있으면 FALSE(0), 없으면 TRUE(1)
    -> 0 이 앞, 1 이 뒤  ->  NULL 인 행이 뒤로 간다 (= NULLS LAST)
```

```text
### SQL: SELECT id, salary FROM emp ORDER BY (salary IS NULL), salary;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | salary                     +----+--------+
----+--------                    | id | salary |
  1 |    300                     +----+--------+
  4 |    400                     |  1 |    300 |
  2 |    500                     |  4 |    400 |
  3 |   NULL                     |  2 |    500 |
(4 rows)                         |  3 |   NULL |
                                 +----+--------+
```

**네 줄이 양쪽에서 같다.** 기본값에 기대지 않았기 때문이다.

`CASE` 로 쓰면 앞뒤를 마음대로 정할 수 있고 의도도 드러난다.

```text
### SQL: SELECT id, name, salary FROM emp ORDER BY CASE WHEN salary IS NULL THEN 0 ELSE 1 END, salary DESC;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name | salary              +----+------+--------+
----+------+--------             | id | name | salary |
  3 | cho  |   NULL              +----+------+--------+
  2 | bob  |    500              |  3 | cho  |   NULL |
  4 | dan  |    400              |  2 | bob  |    500 |
  1 | ann  |    300              |  4 | dan  |    400 |
(4 rows)                         |  1 | ann  |    300 |
                                 +----+------+--------+
```

**대가** — 정렬 키가 하나 늘고 **표현식**이 되어, 인덱스로 정렬을 대신하던 계획을 못 쓸 수 있다.\
큰 표에서는 계획을 확인한다(목록의 46·47·58번 주제).

조건 식 자체의 정본은 [06번](../06-conditional-expressions-case-coalesce/)이다.

---

### 5. `ann`·`bob` 의 앞뒤는 보장되나 — 열 번 같으면 보장인가

**보장되지 않는다. 그리고 열 번 같아도 보장이 아니다.**

각 엔진에서 같은 질의를 10회씩 돌렸다.

```text
=== PG 18.6 — SELECT name FROM emp ORDER BY dept_id;  (10회) ===
ann bob cho dan
ann bob cho dan
ann bob cho dan
ann bob cho dan
ann bob cho dan
ann bob cho dan
ann bob cho dan
ann bob cho dan
ann bob cho dan
ann bob cho dan

=== MySQL 8.4.10 — 같은 질의 (10회) ===
dan ann bob cho
dan ann bob cho
dan ann bob cho
dan ann bob cho
dan ann bob cho
dan ann bob cho
dan ann bob cho
dan ann bob cho
dan ann bob cho
dan ann bob cho
```

**10/10 동일하다.** 그런데 이것은 **관찰이지 보장이 아니다.**

**왜 보장이 아닌가** — 규칙을 보면 안다.

```text
ORDER BY dept_id 가 정하는 것        ORDER BY dept_id 가 안 정하는 것
  dept_id 가 다른 행들의 앞뒤          dept_id 가 같은 행들(ann·bob)의 앞뒤
```

질의문이 안 정한 것은 **엔진이 편한 대로** 된다. 그리고 「편한 대로」는 **계획에 따라 달라진다.**

```text
안전한 추론                         위험한 추론
"질의문이 순서를 정하지 않았다"       "열 번 돌려도 안 바뀌더라"
 -> 보장 없음                        -> 보장된다   <- 틀렸다
```

6번이 그 반증이다.

---

### 6. 같은 바깥 `ORDER BY` 인데 무엇이 달라지나

**출력**

```text
### SQL: SELECT name, dept_id FROM (SELECT * FROM emp ORDER BY id DESC) t ORDER BY dept_id;
--- PG 18.6 ---
 name | dept_id
------+---------
 bob  |      10       <- ann 과 bob 이 뒤바뀌었다
 ann  |      10
 cho  |      20
 dan  |    NULL
(4 rows)
--- MySQL 8.4.10 ---
+------+---------+
| name | dept_id |
+------+---------+
| dan  |    NULL |
| ann  |      10 |    <- MySQL 에서는 이 판에서 안 뒤바뀌었다
| bob  |      10 |
| cho  |      20 |
+------+---------+
```

**PG 에서 `ann` 과 `bob` 의 앞뒤가 뒤집혔다.** 5번에서는 `ann bob` 이었고 여기서는 `bob ann` 이다.

**왜 그런가** — 안쪽에서 `id DESC` 로 넣어 준 순서(`dan, cho, bob, ann`)를 바깥 정렬이 **동률 구간에서 그대로 물려받았다.**

```text
안쪽 결과 (id DESC)        바깥 ORDER BY dept_id
 dan  NULL                   10 인 것들: bob, ann  (들어온 순서대로)
 cho  20          ---->      20:        cho
 bob  10                     NULL:      dan
 ann  10
```

**바깥 질의문은 한 글자도 안 바뀌었다.** 바뀐 것은 입력 순서뿐인데 결과가 달라졌다.

MySQL 에서는 이 판이 안 바뀌었는데, `LIMIT` 을 붙이면 바뀐다.

```text
### SQL: SELECT name, dept_id FROM (SELECT * FROM emp ORDER BY name DESC LIMIT 4) t ORDER BY dept_id;
--- MySQL 8.4.10 ---
+------+---------+
| name | dept_id |
+------+---------+
| dan  |    NULL |
| bob  |      10 |    <- 이번엔 MySQL 에서도 뒤바뀌었다
| ann  |      10 |
| cho  |      20 |
+------+---------+
```

MySQL 은 **`LIMIT` 없는 파생 테이블의 `ORDER BY` 를 지키지 않아도 된다**고 문서가 말한다 — 그래서 첫 판에서 효과가 없었다.

**두 엔진에서 조건이 다를 뿐, 결론은 같다** — **동률 순서는 질의문 밖의 사정으로 정해진다.**

---

### 7. 동률 순서를 질의문 안에서 확정하는 법

**마지막 정렬 키에 고유한 열을 더한다.**

```text
### SQL: SELECT name, dept_id FROM emp ORDER BY dept_id, name;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | dept_id                  +------+---------+
------+---------                 | name | dept_id |
 ann  |      10                  +------+---------+
 bob  |      10                  | dan  |    NULL |
 cho  |      20                  | ann  |      10 |
 dan  |    NULL                  | bob  |      10 |
(4 rows)                         | cho  |      20 |
                                 +------+---------+
```

**`ann` 앞 `bob` 뒤가 이제 질의문에 적혀 있다.** 계획이 어떻게 바뀌어도 같다.

**그런데 `NULL` 자리는 같이 고정되지 않는다.** 위 출력에서 `dan`(`dept_id NULL`)은 여전히 PG 에서 맨 뒤, MySQL 에서 맨 앞이다.

```text
고유 키를 더하면 고정되는 것       여전히 고정 안 되는 것
  동률 행들의 앞뒤                  NULL 이 앞이냐 뒤냐
```

**둘 다 고정하려면 두 처방을 겹친다.**

```sql
ORDER BY (dept_id IS NULL),   -- NULL 을 뒤로 (양쪽 엔진)
         dept_id,             -- 1차 키
         id;                  -- 고유 키 -> 동률 제거
```

실무에서는 **기본키 한 열을 맨 뒤에 붙이는 것**이 거의 항상 정답이다.

```text
비용                              얻는 것
정렬 키 하나 추가                 결정적 정렬
(대개 인덱스에 이미 들어 있다)      페이지네이션 사고 하나가 통째로 사라진다
```

> **결정적 정렬(deterministic order)** — 같은 데이터면 언제나 같은 순서가 나오는 정렬.\
> 예: `ORDER BY dept_id, id` 는 `id` 가 고유하므로 결정적이다.

---

### 8. `ORDER BY` 없는 질의 — 갱신 전후의 순서

**PostgreSQL 18.6 에서 달라진다.**

```text
--- (A) 갱신 전 ---
### SQL: SELECT id, name FROM emp;
--- PG 18.6 ---
 id | name
----+------
  1 | ann
  2 | bob
  3 | cho
  4 | dan
(4 rows)

--- UPDATE emp SET name = name WHERE id = 1;  (값은 그대로) ---

--- (B) 같은 질의를 다시 ---
### SQL: SELECT id, name FROM emp;
--- PG 18.6 ---
 id | name
----+------
  2 | bob
  3 | cho
  4 | dan
  1 | ann       <- ann 이 맨 뒤로 갔다
(4 rows)
```

MySQL 8.4.10 에서 같은 절차를 밟으면 **순서가 그대로**였다(`1 ann / 2 bob / 3 cho / 4 dan`).

(전부 트랜잭션 안에서 하고 `ROLLBACK` 했다. 롤백 뒤 다시 던지니 PG 도 원래 순서로 돌아왔다.)

**왜 그런가** — 저장 구조가 드러난 것이다.

```text
PG                                     MySQL (InnoDB)
UPDATE 는 제자리 수정이 아니다          기본키로 묶인 구조(클러스터드 인덱스)
 -> 새 판본을 뒤에 쓰고                  -> 행이 기본키 순서대로 놓여 있다
    옛 판본을 죽은 것으로 표시           -> 갱신해도 자리가 안 바뀐다
 -> 순차 스캔이 새 자리에서 읽는다
```

**데이터의 값은 하나도 안 바뀌었다.** `name = name` 이었다. 바뀐 것은 물리적 위치뿐인데 결과의 줄 순서가 달라졌다.

| | PG 18.6 | MySQL 8.4.10 |
|---|---|---|
| 갱신 후 `ORDER BY` 없는 순서 | **바뀐다** | 그대로 |

**「지금 잘 나온다」가 가장 위험한 근거인 이유가 이것이다.**\
개발 중에는 순서가 맞다가 **운영에서 `UPDATE` 한 번**에 바뀐다. 그리고 그것은 버그가 아니라 **명세대로**다.

MVCC 의 정본은 목록의 56번 주제다.

---

### 9. `ORDER BY dept_id DESC, salary ASC` — 두 엔진에서 다른 자리

**출력**

```text
### SQL: SELECT name FROM emp ORDER BY dept_id DESC, salary ASC;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name                            +------+
------                           | name |
 dan                             +------+
 cho                             | cho  |
 ann                             | ann  |
 bob                             | bob  |
(4 rows)                         | dan  |
                                 +------+
```

**다른 것은 `dan` 의 자리 하나뿐이다.**

**왜 그런가** — 1차 키 `dept_id DESC` 에서 `NULL` 의 위치만 갈렸고, 나머지는 같은 규칙이다.

```text
1차 키: dept_id DESC
  PG    ->  NULL(dan), 20(cho), 10(ann·bob)      <- NULL 이 가장 크다
  MySQL ->  20(cho), 10(ann·bob), NULL(dan)      <- NULL 이 가장 작다

2차 키: salary ASC  (dept_id 가 10 인 두 행에만 적용)
  ann(300) 먼저, bob(500) 나중    <- 양쪽 동일
```

**여기서 확인할 것이 셋이다.**

1. **방향은 키마다 따로 붙는다.** `dept_id DESC, salary ASC` 에서 `DESC` 가 뒤까지 번지지 않는다.
2. **2차 키는 1차가 같을 때만 본다.** `cho` 와 `dan` 은 `dept_id` 가 달라 `salary` 를 볼 필요가 없었다.
3. **`ann`·`bob` 의 앞뒤가 이번엔 보장된다** — `salary` 가 300과 500으로 다르기 때문이다. 5번의 동률이 2차 키로 해소됐다.

---

### 10. `ORDER BY` 가 `SELECT` 밖의 열을 쓸 수 있는 이유와 그 예외

**`ORDER BY` 가 7번 칸이라 앞 칸들의 결과를 다 갖고 있기 때문이다. 예외는 `DISTINCT` 가 있을 때다.**

9번 질의가 그 예다 — `SELECT name` 만 했는데 `dept_id`·`salary` 로 정렬했다.

```text
1 FROM     emp 의 모든 열이 살아 있다
...
5 SELECT   출력 열은 name 하나로 좁혀진다
           (그래도 원래 행의 다른 열들은 정렬용으로 남아 있다)
7 ORDER BY dept_id, salary 를 쓸 수 있다
```

**`DISTINCT` 가 끼면 이 자유가 사라진다.**

```text
### SQL: SELECT DISTINCT dept_id FROM emp ORDER BY salary;
--- PG 18.6 ---
ERROR:  for SELECT DISTINCT, ORDER BY expressions must appear in select list
LINE 1: SELECT DISTINCT dept_id FROM emp ORDER BY salary;
                                                  ^
--- MySQL 8.4.10 ---
ERROR 3065 (HY000) at line 1: Expression #1 of ORDER BY clause is not in SELECT list, references column 'study.emp.salary' which is not in SELECT list; this is incompatible with DISTINCT
```

**왜 사라지나** — `DISTINCT` 가 `ann`(300)과 `bob`(500)을 한 행으로 접으면, **그 한 행의 `salary` 가 무엇인지 정할 수 없다.**

```text
6 DISTINCT  (10) 한 행으로 접힌다. salary 는 300 인가 500 인가?
7 ORDER BY  정할 수 없으므로 문법 차원에서 막는다
```

자세한 규칙은 [07번](../07-distinct-and-duplicate-removal/)이 정본이다.\
**한 줄로** — `ORDER BY` 는 원래 자유롭고, `DISTINCT` 가 그 자유를 회수한다.

---

### 11. `'a' < 'B'` 와 `'A' = 'a'` — 두 엔진의 답

**출력**

```text
### SQL: SELECT 'a' < 'B' AS a_lt_B, 'A' = 'a' AS a_eq_A;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 a_lt_b | a_eq_a                 +--------+--------+
--------+--------                | a_lt_B | a_eq_A |
 t      | f                      +--------+--------+
(1 row)                          |      1 |      1 |
                                 +--------+--------+
```

**`'a' < 'B'` 는 둘 다 참이지만, `'A' = 'a'` 는 PG 가 거짓·MySQL 이 참이다.**

**왜 그런가** — 기본 collation 이 다르다.

```text
PG 18.6                            MySQL 8.4.10
datcollate = en_US.utf8            collation_database = utf8mb4_0900_ai_ci
사전순으로 비교하되                  ai = accent-insensitive
대소문자는 서로 다른 값              ci = case-insensitive
  -> 'A' = 'a' 는 거짓                -> 'A' 와 'a' 가 같은 값
```

**정렬에서 무슨 일이 생기나** — 같은 네 문자열을 줄 세웠다.

```text
### SQL: SELECT x FROM (SELECT 'B' AS x UNION ALL SELECT 'a' UNION ALL SELECT 'A' UNION ALL SELECT 'b') t ORDER BY x;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 x                               +---+
---                              | x |
 a                               +---+
 A                               | a |
 b                               | A |
 B                               | B |
(4 rows)                         | b |
                                 +---+
```

**세 번째·네 번째가 다르다.**

```text
PG:    a, A, b, B      A 와 a 는 다른 값이고 순서도 정해져 있다
MySQL: a, A, B, b      A 와 a 는 같은 값 -> 동률 -> 앞뒤가 보장되지 않는다
                       B 와 b 도 마찬가지
```

**MySQL 쪽 결과가 5번과 같은 문제**라는 점이 중요하다 — **대소문자가 다른 이름들이 전부 동률**이므로, 이름순 정렬이 **같은 엔진 안에서도 보장되지 않는다.**

(PG 쪽 출력 열 이름이 `a_lt_b`·`a_eq_a` 로 소문자인 것은 별칭 접힘이다 — [02번](../02-select-list-column-aliases/).)

---

### 12. `COLLATE` 로 두 엔진을 같게 만들 수 있나

**결과는 같게 만들 수 있지만, 그 문법은 이식되지 않는다.**

```text
### SQL: SELECT x FROM (SELECT 'B' AS x UNION ALL SELECT 'a' UNION ALL SELECT 'A' UNION ALL SELECT 'b') t ORDER BY x COLLATE "C";
--- PG 18.6 ---
 x
---
 A
 B
 a
 b
(4 rows)
--- MySQL 8.4.10 ---
ERROR 1273 (HY000) at line 1: Unknown collation: 'C'
```

```text
### SQL: SELECT x FROM (SELECT 'B' AS x UNION ALL SELECT 'a' UNION ALL SELECT 'A' UNION ALL SELECT 'b') t ORDER BY x COLLATE utf8mb4_bin;
--- PG 18.6 ---
ERROR:  collation "utf8mb4_bin" for encoding "UTF8" does not exist
LINE 1: ...ALL SELECT 'A' UNION ALL SELECT 'b') t ORDER BY x COLLATE ut...
                                                             ^
--- MySQL 8.4.10 ---
+---+
| x |
+---+
| A |
| B |
| a |
| b |
+---+
```

**두 결과가 `A B a b` 로 같다.** 바이트 값 순서로 세우라고 명시했기 때문이다.

**그런데 이름이 서로 다르다.**

| | PG 18.6 | MySQL 8.4.10 |
|---|---|---|
| 바이트 순서 collation 이름 | `"C"` | `utf8mb4_bin` |
| 상대 이름을 던지면 | `collation "utf8mb4_bin" ... does not exist` | `ERROR 1273 Unknown collation: 'C'` |

**그래서 `COLLATE` 절은 이식되지 않는다.** 한 문장을 양쪽에 그대로 쓸 수 없다.

**실무 처방은 질의가 아니라 스키마다.**

```text
질의마다 COLLATE 를 붙인다          열 정의에서 collation 을 고정한다
 -> 빠뜨리는 질의가 생긴다           -> 그 열의 모든 비교·정렬이 같아진다
 -> 이식할 때마다 이름을 바꾼다       -> 인덱스도 그 기준으로 만들어진다
```

collation 의 정본은 [39번](../39-collation/)이다.\
여기서 인출할 것은 하나 — **문자열의 대소 관계는 데이터가 아니라 설정이 정한다.**

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| ★ `NULL` 기본 위치 (1·2번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | `ASC`·`DESC` 양쪽 |
| `NULLS FIRST`/`LAST` (3번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | **MySQL 은 `ERROR 1064`** |
| 이식 가능한 `NULL` 키 (4번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | `(x IS NULL)` · `CASE` 양쪽 |
| ★ 동률 순서 반복 실행 (5번) | PG 18.6 · MySQL 8.4.10 | **각 10회** | **10/10 동일 — 그래도 보장 아님** |
| ★ 입력 순서를 바꾼 반증 (6번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | `id DESC` 판 · `LIMIT` 판 |
| 고유 키 추가 (7번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | |
| ★ `UPDATE` 후 순서 변화 (8번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | **트랜잭션 + `ROLLBACK`** · 롤백 후 원복 확인 |
| 여러 키·방향 (9번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | |
| `SELECT` 밖 열 · `DISTINCT` (10번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **에러 메시지가 근거** |
| ★ collation 비교·정렬 (11번) | PG 18.6 · MySQL 8.4.10 | **각 5회** | 정렬은 5회 반복 — 각 엔진 내부는 5/5 동일 |
| `COLLATE` 명시 (12번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **양쪽 에러 메시지가 근거** |
| 표현식·서수 정렬 | PG 18.6 · MySQL 8.4.10 | 각 2회 | |

**구현 의존 항목** — 5·6·8·11번이 전부 구현 의존이다. 그리고 **그게 이 주제의 요점이다.**\
「10회 같았다」·「5회 같았다」는 **관찰**이고, 보장은 질의문이 적은 것뿐이다.\
8번의 `UPDATE` 후 순서 변화는 **저장 구조**(PG 의 MVCC 대 InnoDB 의 클러스터드 인덱스)에서 나온다.

**언어 보장 항목** — 1·2·3·4·7·9·10번. 어느 키로 줄 세우는지, 방향이 키마다 따로인 것,\
`ORDER BY` 가 `SELECT` 밖의 열을 쓸 수 있는 것, `DISTINCT` 가 그 자유를 회수하는 것은 **두 엔진에서 같았다.**\
`NULL` 기본 위치는 「엔진마다 고정」이라는 뜻에서 보장이지, 표준이 정한 값이 아니다.

**버전** — `NULLS FIRST`/`LAST` 는 MySQL 8.4.10 에 없다. 다음 버전에서는 **3번(문법 유무)과 5·6·8번(순서 관찰)**을 다시 돌린다.\
특히 **8번은 저장 구조가 바뀌면 달라지는 항목**이다.
