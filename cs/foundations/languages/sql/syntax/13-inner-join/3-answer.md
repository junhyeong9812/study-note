# sql/13-INNER JOIN — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력은 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 에러 메시지도 실제로 받은 것이고, 지어낸 출력은 없다.\
> 8~10번의 `proj`·`emp_proj` 는 **트랜잭션 안에서 만들고 롤백**했다(MySQL 은 `CREATE` → 질의 → `DROP`). DB 에 남기지 않았다.\
> 문서 근거는 [PG 18 Table Expressions](https://www.postgresql.org/docs/18/queries-table-expressions.html) · [MySQL 8.4 JOIN Clause](https://dev.mysql.com/doc/refman/8.4/en/join.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. 결과 행 수와 사라진 행

**3행이다. `emp` 의 `dan` 과 `dept` 의 `hr` 이 결과에 없다.**

```text
### SQL: SELECT e.name AS emp, d.name AS dept FROM emp e JOIN dept d ON e.dept_id = d.id ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | dept                      +-----+-------+
-----+-------                    | emp | dept  |
 ann | sales                     +-----+-------+
 bob | sales                     | ann | sales |
 cho | dev                       | bob | sales |
(3 rows)                         | cho | dev   |
                                 +-----+-------+
```

**왜 그런가** — [12번](../12-cartesian-product-cross-join/)의 12행을 `ON` 으로 거른 것이다.

```text
카티션곱 12행                ON e.dept_id = d.id      처분
 ann x sales                 10 = 10   TRUE           남김
 ann x dev, hr               FALSE                    버림
 bob x sales                 10 = 10   TRUE           남김
 bob x dev, hr               FALSE                    버림
 cho x dev                   20 = 20   TRUE           남김
 cho x sales, hr             FALSE                    버림
 dan x sales, dev, hr        NULL = ?  UNKNOWN        버림   <- dan 은 세 행 전부
                                                      ----
                                                      3행

 hr 은 TRUE 를 만들어 줄 왼쪽 행이 애초에 없었다
```

**양쪽에서 각각 하나씩 사라진다는 점이 대칭이다.**

| 사라진 것 | 어느 쪽 | 왜 |
|---|---|---|
| `dan` | 왼쪽(`emp`) | `dept_id` 가 `NULL` 이라 어느 부서와도 `TRUE` 가 안 된다 |
| `hr` | 오른쪽(`dept`) | 그 부서에 속한 사원이 하나도 없다 |

`INNER` 키워드를 붙여도 같다 — 생략 가능한 기본값이다.

```text
### SQL: SELECT e.name AS emp, d.name AS dept FROM emp e INNER JOIN dept d ON e.dept_id = d.id ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | dept                      +-----+-------+
-----+-------                    | emp | dept  |
 ann | sales                     +-----+-------+
 bob | sales                     | ann | sales |
 cho | dev                       | bob | sales |
(3 rows)                         | cho | dev   |
                                 +-----+-------+
```

---

### 2. `dan` 의 세 짝이 전부 떨어진 이유

**`UNKNOWN` 이다.**

```text
 dan.dept_id = NULL

 NULL = 10   ->  UNKNOWN      (FALSE 가 아니다 — "모른다"다)
 NULL = 20   ->  UNKNOWN
 NULL = 30   ->  UNKNOWN
                    ↓
 ON 은 TRUE 만 통과시킨다 — FALSE 와 UNKNOWN 을 똑같이 버린다
```

★ **`ON` 은 `WHERE` 와 똑같은 규칙으로 판정한다.** 세 번째 진릿값이 있다는 사실과, `TRUE` 만 살아남는다는 사실.\
[04번](../04-null-three-valued-logic/)의 규칙이 조인에서 그대로 작동한다.

> **`UNKNOWN`** — `TRUE`/`FALSE` 가 아닌 세 번째 진릿값. `NULL` 이 비교에 끼면 나온다.\
> 예: `NULL = 10`. "모르는 값이 10 인지"는 답할 수 없다.

**여기서 무서운 것은 `NULL` 이 「같지 않다」가 아니라 「모른다」라는 점이다.**\
`FALSE` 라면 "다른 값이었구나"로 읽히지만 `UNKNOWN` 은 "값이 없어서 판정 자체가 안 됐다"다. 그런데 **결과에서는 둘 다 똑같이 사라진다.**

되살리려면 조인 형태를 바꾼다 — `LEFT JOIN` 이 `dan` 을 살리고([14번](../14-left-right-outer-join/)), `FULL OUTER` 가 `dan` 과 `hr` 을 둘 다 살린다([16번](../16-full-outer-join/)).

---

### 3. 결과 3행만 보고 「원래 4명」을 알 수 있나

**알 수 없다. 그것이 `INNER JOIN` 의 가장 위험한 성질이다.**

```text
 받아 든 결과                  이 결과가 나올 수 있는 원본들
+-----+-------+               (A) 사원이 3명이고 전부 부서가 있다
| ann | sales |               (B) 사원이 4명인데 한 명은 부서가 없다   <- 실제
| bob | sales |               (C) 사원이 100명인데 97명이 부서가 없다
| cho | dev   |
+-----+-------+                결과만으로는 셋을 구분할 수 없다
```

**에러도 경고도 없다.** 「사원 목록을 뽑았다」고 믿고 3행을 쓰면 `dan` 은 존재하지 않는 사람이 된다.

확인하는 방법은 **양쪽 행 수를 따로 세어 맞춰 보는 것**뿐이다.

```text
### SQL: SELECT (SELECT COUNT(*) FROM emp) AS emp_rows,
                (SELECT COUNT(*) FROM dept) AS dept_rows,
                (SELECT COUNT(*) FROM emp e JOIN dept d ON e.dept_id = d.id) AS joined_rows;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp_rows | dept_rows | joined_rows    +----------+-----------+-------------+
----------+-----------+-------------   | emp_rows | dept_rows | joined_rows |
        4 |         3 |           3    +----------+-----------+-------------+
(1 row)                                |        4 |         3 |           3 |
                                       +----------+-----------+-------------+
```

`emp` 4행이 조인 뒤 3행이 됐다 — **한 명이 어딘가에서 빠졌다.** 이 한 줄이 사고를 잡는다.

★ **습관으로 만들 것** — 조인을 쓴 뒤에는 **행 수가 줄었는지 늘었는지 먼저 센다.**\
줄었으면 `INNER` 가 버린 것이고(이 주제), 늘었으면 팬아웃이다(8번).

---

### 4. `ON` 과 `WHERE` 는 결과가 같은가

**같다. 두 질의 다 2행이다.**

```text
### SQL: SELECT e.name AS emp, d.name AS dept FROM emp e JOIN dept d
         ON e.dept_id = d.id AND d.name = 'sales' ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | dept                      +-----+-------+
-----+-------                    | emp | dept  |
 ann | sales                     +-----+-------+
 bob | sales                     | ann | sales |
(2 rows)                         | bob | sales |
                                 +-----+-------+

### SQL: SELECT e.name AS emp, d.name AS dept FROM emp e JOIN dept d
         ON e.dept_id = d.id WHERE d.name = 'sales' ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | dept                      +-----+-------+
-----+-------                    | emp | dept  |
 ann | sales                     +-----+-------+
 bob | sales                     | ann | sales |
(2 rows)                         | bob | sales |
                                 +-----+-------+
```

**왜 같은가** — 내부 조인은 **짝을 못 지은 행을 어차피 버린다.**

```text
INNER JOIN 에서의 두 경로

 ON 에서 탈락한 행   ->  짝이 안 지어졌다  ->  결과에 없다
 WHERE 에서 탈락한 행 ->  행이 걸러졌다    ->  결과에 없다
                                              ↑
                                     도착지가 같다
```

`ON TRUE` 로 아예 조건을 `WHERE` 로 몰아도 마찬가지다.

```text
### SQL: SELECT e.name AS emp, d.name AS dept FROM emp e JOIN dept d ON TRUE
         WHERE e.dept_id = d.id ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | dept                      +-----+-------+
-----+-------                    | emp | dept  |
 ann | sales                     +-----+-------+
 bob | sales                     | ann | sales |
 cho | dev                       | bob | sales |
(3 rows)                         | cho | dev   |
                                 +-----+-------+

### SQL: SELECT e.name AS emp, d.name AS dept FROM emp e, dept d WHERE e.dept_id = d.id ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | dept                      +-----+-------+
-----+-------                    | emp | dept  |
 ann | sales                     +-----+-------+
 bob | sales                     | ann | sales |
 cho | dev                       | bob | sales |
(3 rows)                         | cho | dev   |
                                 +-----+-------+
```

**네 가지 표기가 전부 같은 답을 낸다.** 내부 조인에서 조건의 자리는 **취향 문제**다.

---

### 5. 그런데 왜 `ON` 에 적나

**이유 둘 — 읽는 사람을 위해서, 그리고 나중에 `LEFT JOIN` 으로 바꿔도 뜻이 안 변하게 하려고.**

**(1) 두 종류의 조건이 눈으로 분리된다.**

```text
조건이 섞인 표기                        조건이 분리된 표기
FROM emp e, dept d                     FROM emp e JOIN dept d
WHERE e.dept_id = d.id                   ON e.dept_id = d.id      <- "어떻게 붙이나"
  AND d.name = 'sales'                 WHERE d.name = 'sales'     <- "무엇을 남기나"
  AND e.salary >= 400                    AND e.salary >= 400
    ↑
 어느 게 조인 조건인지 세어 봐야 안다      표가 셋 넷이 돼도 한눈에 보인다
```

표가 늘수록 차이가 커진다. `WHERE` 에 조건 다섯 줄이 섞여 있으면 **조인 조건이 빠졌는지 세어 봐야** 안다([12번](../12-cartesian-product-cross-join/)의 9행 사고).

**(2) 조인 형태를 바꿔도 뜻이 안 변한다. 이것이 결정적이다.**

```text
INNER JOIN 일 때                    LEFT JOIN 으로 바꾼 뒤
 ON  에 적은 조건 -> 2행              ON  에 적은 조건 -> 4행  (뜻: 붙이는 규칙)
 WHERE 에 적은 조건 -> 2행            WHERE 에 적은 조건 -> 2행 (뜻: 결과 필터)
       같다                                 달라진다
```

`ON` 에 적어 두면 「이건 붙이는 규칙이다」라는 뜻이 형태를 바꿔도 유지된다.\
`WHERE` 에 적어 두면 `LEFT JOIN` 으로 바꾸는 순간 **외부 조인이 내부 조인으로 무너진다.**

★ **그것이 이 묶음의 정점인 [15번](../15-on-vs-where-in-outer-join/)이다.**\
여기서 「같다」고 배운 것이 거기서 「다르다」로 뒤집히고, 그 뒤집힘의 이유가 바로 [01번](../01-logical-query-processing-order/)의 처리 순서다.

---

### 6. `JOIN` 에 `ON` 이 없으면 — 두 엔진에서 각각

**PG 18.6 은 구문 오류, MySQL 8.4.10 은 12행 카티션곱이다.**

```text
### SQL: SELECT e.name, d.name FROM emp e JOIN dept d;
--- PG 18.6 ---
ERROR:  syntax error at or near ";"
LINE 1: SELECT e.name, d.name FROM emp e JOIN dept d;
                                                    ^
--- MySQL 8.4.10 ---
+------+-------+
| name | name  |
+------+-------+
| dan  | dev   |
| cho  | dev   |
| bob  | dev   |
| ann  | dev   |
| dan  | hr    |
| cho  | hr    |
| bob  | hr    |
| ann  | hr    |
| dan  | sales |
| cho  | sales |
| bob  | sales |
| ann  | sales |
+------+-------+
```

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| `JOIN` 에 `ON` 없음 | **✗ 구문 오류** | **✓ 12행 (카티션곱)** |

**왜 다른가** — PG 는 `JOIN` 에 `ON` 또는 `USING` 을 **문법으로 의무화**한다. 조건 없는 조인은 `CROSS JOIN` 이라고 따로 적어야 한다.\
MySQL 은 `JOIN`·`INNER JOIN`·`CROSS JOIN` 을 **문법적 동의어**로 다뤄 조건 유무를 가리지 않는다([MySQL 8.4 JOIN 페이지](https://dev.mysql.com/doc/refman/8.4/en/join.html)).

**[12번](../12-cartesian-product-cross-join/)의 사고와 정확히 대칭이다.**

```text
                              PG 18.6          MySQL 8.4.10
 JOIN 에 ON 을 빠뜨림        구문 오류         12행 (조용)
 CROSS JOIN 에 ON 을 붙임    구문 오류         3행 (내부 조인)
       ↑                        ↑                  ↑
  두 실수 다 흔하다       형태와 조건이 1:1    세 이름이 전부 동의어
```

★ **양쪽에서 도는 습관** — 조건이 있으면 `JOIN … ON`, 없으면 `CROSS JOIN`. 이 규칙만 지키면 어느 엔진에서도 의도대로 돈다.\
그리고 MySQL 쪽 사고는 **시끄럽지 않으므로** 행 수를 세는 습관(3번)이 유일한 방어선이다.

> `ORDER BY` 가 없어 MySQL 출력의 줄 순서는 보장되지 않는다. 12행이라는 개수가 요점이다.

---

### 7. `ON e.dept_id > d.id` 는 통과하는가

**통과한다. 1행이 나온다.**

```text
### SQL: SELECT e.name AS emp, d.name AS dept FROM emp e JOIN dept d ON e.dept_id > d.id ORDER BY e.id, d.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | dept                      +-----+-------+
-----+-------                    | emp | dept  |
 cho | sales                     +-----+-------+
(1 row)                          | cho | sales |
                                 +-----+-------+
```

**왜 1행인가** — 12쌍을 `>` 로 판정하면 `TRUE` 가 하나뿐이다.

```text
 emp.dept_id | dept.id | dept_id > id | 처분
-------------+---------+--------------+------
   10 (ann)  |  10     | FALSE        | 버림
   10 (ann)  |  20, 30 | FALSE        | 버림
   10 (bob)  |  10,20,30| FALSE       | 버림
   20 (cho)  |  10     | TRUE         | 남김   <- 20 > 10
   20 (cho)  |  20, 30 | FALSE        | 버림
 NULL (dan)  |  전부    | UNKNOWN      | 버림
```

★ **`ON` 은 조건식이지 등호 전용 문법이 아니다.** 구간표·이력 테이블을 `ON a.d BETWEEN b.from AND b.to` 로 붙이는 것이 실전 용법이다.

**다만 대가가 둘 있다.**

1. **해시 조인을 못 쓴다.** 해시는 등호에만 맞는다. 큰 표에서는 중첩 루프가 되어 느려진다(목록의 **59번 주제**).
2. **`FULL OUTER JOIN` 에서는 아예 거부된다** — PG 가 `FULL JOIN is only supported with merge-joinable or hash-joinable join conditions` 로 막는다([16번](../16-full-outer-join/)).

**내부 조인에는 그 제약이 없다.** 위에서 부등호가 그냥 통했다 — **알고리즘 제약이 문법 제약으로 드러나는 것은 `FULL` 뿐이다.**

---

### 8. `emp JOIN emp_proj` 의 행 수와 `ann` 의 행

**3행이고, `ann` 의 행은 2개다.**

<details>
<summary>팬아웃 확인용 표 — 트랜잭션 안에서 만들고 롤백했다 (PostgreSQL)</summary>

```sql
BEGIN;
CREATE TABLE proj (id int PRIMARY KEY, name text NOT NULL);
CREATE TABLE emp_proj (emp_id int, proj_id int, PRIMARY KEY (emp_id, proj_id));
INSERT INTO proj     VALUES (100,'atlas'), (200,'beta');
INSERT INTO emp_proj VALUES (1,100), (1,200), (2,100);
-- 아래 질의들을 여기서 돌린다
ROLLBACK;
```

MySQL 은 DDL 에 트랜잭션이 안 걸리므로 `CREATE` → 질의 → `DROP TABLE` 로 확인했다.\
두 DB 모두 실험 뒤 `emp`·`dept` 만 남아 있다.

</details>

```text
### SQL: SELECT e.name AS emp, ep.proj_id, e.salary
         FROM emp e JOIN emp_proj ep ON e.id = ep.emp_id ORDER BY e.id, ep.proj_id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | proj_id | salary          +-----+---------+--------+
-----+---------+--------         | emp | proj_id | salary |
 ann |     100 |    300          +-----+---------+--------+
 ann |     200 |    300          | ann |     100 |    300 |
 bob |     100 |    500          | ann |     200 |    300 |
(3 rows)                         | bob |     100 |    500 |
                                 +-----+---------+--------+
```

**두 가지가 동시에 일어났다.**

```text
 emp 4행                 emp JOIN emp_proj 3행
+------+                +-----+---------+
| ann  |  --- 2줄 --->  | ann |     100 |   <- 늘었다 (팬아웃)
|      |                | ann |     200 |
| bob  |  --- 1줄 --->  | bob |     100 |
| cho  |  --- 0줄       +-----+---------+
| dan  |  --- 0줄          cho·dan 은 사라졌다 (INNER)
+------+
```

- **줄었다** — `cho`·`dan` 은 `emp_proj` 에 행이 없어 `INNER JOIN` 이 버렸다(1번의 규칙).
- **늘었다** — `ann` 은 `emp_proj` 에 행이 둘이라 두 줄이 됐다.

★ **「조인하면 행이 준다」는 반쪽만 맞다.** `INNER` 는 줄이고 1:N 은 늘린다. 둘이 동시에 일어난다.

---

### 9. 그 위에 `SUM` 을 씌우면

**1100 이 나온다. 정답은 800 이다.**

```text
### SQL: SELECT SUM(e.salary) AS total FROM emp e JOIN emp_proj ep ON e.id = ep.emp_id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 total                           +-------+
-------                          | total |
  1100                           +-------+
(1 row)                          |  1100 |
                                 +-------+
```

```text
 정답 (사원 단위)                 나온 값 (배정 단위)
 ann  300                        ann  300   (atlas 행)
 bob  500                        ann  300   (beta 행)    <- 같은 급여를 또 더했다
-----                            bob  500
 800                            -----
                                 1100
```

사원별로 쪼개면 어디서 늘었는지가 보인다.

```text
### SQL: SELECT e.name AS emp, COUNT(*) AS rows_per_emp, SUM(e.salary) AS salary_sum
         FROM emp e JOIN emp_proj ep ON e.id = ep.emp_id GROUP BY e.name ORDER BY e.name;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | rows_per_emp | salary_sum  +-----+--------------+------------+
-----+--------------+------------ | emp | rows_per_emp | salary_sum |
 ann |            2 |        600  +-----+--------------+------------+
 bob |            1 |        500  | ann |            2 |        600 |
(2 rows)                          | bob |            1 |        500 |
                                  +-----+--------------+------------+
```

`ann` 의 `salary_sum` 이 **600** — 300 이 두 번 들어갔다.

★ **조인이 틀린 게 아니다.** 3행은 「사원-프로젝트 배정」이라는 단위에서 정확하다.\
틀린 것은 **그 단위 위에 사원 단위 집계를 씌운 것**이다.

```text
 결과 한 줄의 단위가 무엇인가?

 emp 만 읽을 때          한 줄 = 사원 한 명       -> SUM(salary) 가 맞는다
 emp JOIN emp_proj      한 줄 = 배정 하나         -> SUM(salary) 는 뜻이 없다
```

**이것이 silent failure 다** — 에러도 없고, 타입도 맞고, 값도 그럴듯하다.\
`COUNT(*)` 로 「사원 수」를 세는 것도 같은 사고다. 조인 뒤의 `COUNT(*)` 은 **행 수**이고, 사원 수는 `COUNT(DISTINCT e.id)` 다(목록의 **21번 주제**).

---

### 10. 처방 둘과 각각의 쓰임

**(A) 행을 아예 안 늘린다 — `EXISTS` / `IN`.** 상대 표의 **값이 필요 없을 때.**

```text
### SQL: SELECT SUM(e.salary) AS total FROM emp e
         WHERE EXISTS (SELECT 1 FROM emp_proj ep WHERE ep.emp_id = e.id);
--- PG 18.6 ---
 total 
-------
   800
(1 row)

### SQL: SELECT SUM(salary) AS total FROM emp WHERE id IN (SELECT emp_id FROM emp_proj);
--- MySQL 8.4.10 ---
+-------+
| total |
+-------+
|   800 |
+-------+
```

**(B) 늘리기 전에 접는다 — 선집계 후 조인.** 상대 표의 **요약값이 필요할 때.**

```text
### SQL: SELECT e.name AS emp, e.salary, p.n AS proj_cnt FROM emp e
         JOIN (SELECT emp_id, COUNT(*) AS n FROM emp_proj GROUP BY emp_id) p ON p.emp_id = e.id
         ORDER BY e.id;
--- PG 18.6 ---
 emp | salary | proj_cnt 
-----+--------+----------
 ann |    300 |        2
 bob |    500 |        1
(2 rows)
```

`emp_proj` 를 **먼저 사원당 1행으로 접었으므로** 조인해도 행이 안 는다. 그래서 `salary` 가 한 번만 나온다.

```text
 (A) EXISTS                          (B) 선집계 후 조인
 emp 4행                             emp 4행       emp_proj 3행
   ↓ "짝이 있나?"만 본다                              ↓ GROUP BY emp_id
 emp 2행 (ann, bob)                                 2행 (ann:2, bob:1)
   ↓                                    ↓ 1:1 로 붙는다
 SUM = 800                           emp 2행 — 행이 안 늘었다
```

| 처방 | 언제 | 대가 |
|---|---|---|
| `EXISTS` / `IN` | 상대 표의 **존재 여부만** 필요 | 상대 표의 값은 못 쓴다 |
| 선집계 후 조인 | 상대 표의 **요약값**(개수·합계)이 필요 | 집계를 한 번 더 돈다 |
| `COUNT(DISTINCT …)` | 이미 조인해 버린 결과를 고칠 때 | `SUM` 은 이걸로 못 고친다 |

★ **`SUM` 은 `DISTINCT` 로 못 고친다.** 같은 급여를 가진 두 사원이 있으면 `SUM(DISTINCT salary)` 가 한 명을 지운다.\
행이 늘어난 뒤에 고치려 하지 말고 **애초에 안 늘리는 것**이 처방이다.

팬아웃 처방 전체는 목록의 **25번 주제**, `EXISTS`/`IN`/`NOT IN` 은 **19번 주제**가 정본이다.\
**경계: 여기는 「조인이 행을 늘린다」는 사실과 처방이 둘 있다는 것까지, 선택 기준의 세부는 25번.**

---

### 11. `SELECT COUNT(*) FROM emp NATURAL JOIN dept;` 의 결과

**0 이다. 에러가 아니라 0행이다.**

```text
### SQL: SELECT COUNT(*) AS n FROM emp NATURAL JOIN dept;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 n                               +---+
---                              | n |
 0                               +---+
(1 row)                          | 0 |
                                 +---+
```

**왜 그런가** — `NATURAL JOIN` 은 **이름이 같은 열 전부**를 조인 조건으로 삼는다.

```text
 emp 의 열 : id, name, dept_id, salary
 dept 의 열: id, name
              ↑    ↑
        둘 다 겹친다
              ↓
 조인 조건이 자동으로 이렇게 만들어진다
   ON emp.id = dept.id AND emp.name = dept.name
              ↓
 emp.id 는 1~4, dept.id 는 10~30 — 겹치는 값이 없다
 게다가 name 까지 같아야 한다
              ↓
            0행
```

★ **의도는 「부서로 붙이기」였는데 붙은 것은 `id` 와 `name` 이다.** 심지어 `dept_id` 는 조건에 들어가지도 않았다.

`USING (id)` 도 같은 함정이다 — 이름만 같고 **의미가 다른 열**로 붙는다.

```text
### SQL: SELECT * FROM emp JOIN dept USING (id);
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name | dept_id | salary | name    (빈 결과 — 출력이 한 줄도 없다)
----+------+---------+--------+------
(0 rows)
```

**두 엔진 다 조용하다.** 문법이 맞고 실행도 되고 결과만 비어 있다 — **에러가 났으면 오히려 안전했을 자리**다.

```text
 시끄러운 실패                        조용한 실패
 SELECT id FROM emp e JOIN dept d     SELECT * FROM emp NATURAL JOIN dept
   -> ERROR: column "id" is ambiguous   -> 0 rows
        ↑                                      ↑
  같은 겹침이 원인인데                    한쪽은 막고 한쪽은 안 막는다
```

`USING`·`NATURAL` 의 규칙 전체는 목록의 **18번 주제**가 정본이다.\
**여기서 인출할 것은 하나다 — `NATURAL JOIN` 은 스키마가 바뀌면 조용히 뜻이 바뀐다.**

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| `INNER JOIN` 기본 결과 (1번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | `INNER` 생략형까지 |
| 행 수 대조 (3번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | |
| `ON` 대 `WHERE` 네 표기 (4번) | PG 18.6 · MySQL 8.4.10 | 각 4회 | **전부 같은 결과** — 15번의 복선 |
| `JOIN` 에 `ON` 누락 (6번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **PG 구문 오류가 근거다** |
| 부등호 `ON` (7번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | |
| 팬아웃 (8·9번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | **트랜잭션 안에서 만들고 롤백** — DB 에 잔재 없음 |
| 처방 (10번) | PG 18.6(EXISTS·선집계) · MySQL 8.4.10(IN) | 3회 | |
| `NATURAL JOIN`·`USING` (11번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **0행이 근거다** |

**구현 의존 항목** — 없다. 이 주제의 모든 결과는 결과의 정의에서 나온다.\
단 **행 순서는 보장되지 않으므로** 출력에 `ORDER BY` 를 붙였다. 6번만 `ORDER BY` 없이 던졌고, 거기서는 **개수 12** 가 요점이다.

**언어 보장 항목** — 1~5·7~11번. `ON` 의 `TRUE`-만-통과 규칙, 짝 없는 행의 소멸, 팬아웃의 곱셈은 전부 문서가 정한 것이다.\
**문법이 갈리는 항목** — 6번(`JOIN` 에 `ON` 누락). 두 매뉴얼에 도입 버전이 없어 **버전은 적지 않았다.**
