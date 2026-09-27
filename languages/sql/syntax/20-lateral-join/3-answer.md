# sql/20-LATERAL 조인 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력은 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 에러 메시지도 실제로 받은 것이고, 지어낸 출력은 없다.\
> 버전은 `SELECT VERSION()` 으로 두 서버에서 직접 확인했다.\
> 표는 기존 `emp`·`dept` 만 썼다 — **새로 만든 표가 없다.**\
> 문서 근거는 [PG 18 LATERAL Subqueries](https://www.postgresql.org/docs/18/queries-table-expressions.html#QUERIES-LATERAL) · [MySQL 8.4 Lateral Derived Tables](https://dev.mysql.com/doc/refman/8.4/en/lateral-derived-tables.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. `LATERAL` 없이 왼쪽 참조

**두 엔진 다 에러다. 다만 PG 만 답을 알려 준다.**

```text
### SQL: SELECT d.name AS dept, t.name AS emp FROM dept d
         JOIN (SELECT e.name, e.dept_id FROM emp e WHERE e.dept_id = d.id ORDER BY e.id LIMIT 1) AS t ON true;
--- PG 18.6 ---
ERROR:  invalid reference to FROM-clause entry for table "d"
LINE 1: ...CT e.name, e.dept_id FROM emp e WHERE e.dept_id = d.id ORDER...
                                                             ^
DETAIL:  There is an entry for table "d", but it cannot be referenced from this part of the query.
HINT:  To reference that table, you must mark this subquery with LATERAL.
--- MySQL 8.4.10 ---
ERROR 1054 (42S22) at line 1: Unknown column 'd.id' in 'where clause'
```

**`LATERAL` 을 붙이면 통과한다.** 바꾼 것은 그 한 낱말뿐이다.

```text
### SQL: SELECT d.name AS dept, t.name AS emp FROM dept d
         JOIN LATERAL (SELECT e.name FROM emp e WHERE e.dept_id = d.id ORDER BY e.id LIMIT 1) AS t ON true
         ORDER BY d.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept  | emp                     +-------+-----+
-------+-----                    | dept  | emp |
 sales | ann                     +-------+-----+
 dev   | cho                     | sales | ann |
(2 rows)                         | dev   | cho |
                                 +-------+-----+
```

★ **PG 의 세 줄짜리 에러가 이 주제 전체를 요약한다.**

```text
 ERROR  — 못 한다
 DETAIL — 그 표는 있는데 이 자리에서는 못 부른다      <- 왜 못 하는지
 HINT   — 부르려면 LATERAL 로 표시하라                <- 어떻게 하면 되는지
```

**MySQL 은 `Unknown column` 이라고만 한다.** 표가 있다는 사실조차 안 알려 주므로, `LATERAL` 을 모르면 **오타를 찾으며 헤매게 된다.**

---

### 2. 막는 이유

**`FROM` 의 항목들은 서로 「형제」라, 오른쪽을 만들 시점에 「왼쪽의 현재 행」이라는 것이 아직 없기 때문이다.**

```text
 FROM dept d , (SELECT … WHERE e.dept_id = d.id)
      └──┬──┘   └────────────┬─────────────────┘
         │                   │
         └─── 둘이 동시에 만들어진다 ───┘
                     ↓
        서브쿼리를 만들 때 d 는 "표"이지 "행" 이 아니다
                     ↓
              d.id 가 무엇을 가리킬지 정의되지 않는다
```

**이 벽은 버그가 아니라 설계다.**

```text
 벽이 있어서 얻는 것
   FROM 항목을 어떤 순서로 계산해도 된다
   -> 옵티마이저가 조인 순서를 자유롭게 고를 수 있다
        ↑
   LATERAL 은 그 자유를 일부 포기하는 대신 참조를 얻는 표시다
```

`SELECT` 칸의 상관 서브쿼리는 왜 되나 — **그 자리에는 이미 바깥 행이 정해져 있기 때문**이다([11번](../11-subquery-scalar-correlated-any-all/)).

```text
 SELECT 칸                          FROM 칸
 FROM 이 행을 다 만든 뒤 계산된다    아직 행이 만들어지는 중이다
   -> "지금 행" 이 있다               -> "지금 행" 이 없다
   -> 참조 허용                       -> 참조 거부 (LATERAL 로 명시해야 허용)
```

벽 자체의 정본은 [10번](../10-from-clause-aliases-derived-tables/)이다.

---

### 3. `CROSS JOIN LATERAL` 의 결과

**2행이다. `hr` 이 없다.**

```text
### SQL: SELECT d.name AS dept, t.name AS emp, t.salary FROM dept d
         CROSS JOIN LATERAL (SELECT e.name, e.salary FROM emp e WHERE e.dept_id = d.id
                             ORDER BY e.salary DESC LIMIT 1) AS t ORDER BY d.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept  | emp | salary           +-------+-----+--------+
-------+-----+--------          | dept  | emp | salary |
 sales | bob |    500           +-------+-----+--------+
 dev   | cho |                  | sales | bob |    500 |
(2 rows)                        | dev   | cho |   NULL |
                                +-------+-----+--------+
```

**왜 그런가**

```text
 왼쪽 행       서브쿼리가 받은 조건          서브쿼리 결과      결과 행
 -----------   ---------------------------   ----------------   --------
 sales(10)     e.dept_id = 10                bob (500)          1줄
 dev(20)       e.dept_id = 20                cho (NULL)         1줄
 hr(30)        e.dept_id = 30                0행                없음     <- 사라진다
```

★ **`CROSS JOIN LATERAL` 은 서브쿼리가 0행이면 왼쪽 행을 버린다.** [13번](../13-inner-join/)의 내부 조인과 같은 성질이다.

**`cho` 가 남은 것에 주목하라.** 급여가 `NULL` 인데도 `ORDER BY salary DESC LIMIT 1` 이 그 한 행을 골랐다 — **비교가 아니라 정렬**이라 `NULL` 도 자리를 갖는다([08번](../08-order-by-null-position-stability/)).

---

### 4. 되살리는 방법

**`LEFT JOIN LATERAL … ON true` 다. `ON` 에는 `true` 를 적는다.**

```text
### SQL: SELECT d.name AS dept, t.name AS emp, t.salary FROM dept d
         LEFT JOIN LATERAL (SELECT e.name, e.salary FROM emp e WHERE e.dept_id = d.id
                            ORDER BY e.salary DESC LIMIT 1) AS t ON true ORDER BY d.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept  | emp | salary           +-------+------+--------+
-------+-----+--------          | dept  | emp  | salary |
 sales | bob |    500           +-------+------+--------+
 dev   | cho |                  | sales | bob  |    500 |
 hr    |     |                  | dev   | cho  |   NULL |
(3 rows)                        | hr    | NULL |   NULL |
                                +-------+------+--------+
```

**왜 `ON true` 인가**

```text
 보통의 LEFT JOIN               LEFT JOIN LATERAL
 ON e.dept_id = d.id            조건이 이미 서브쿼리 WHERE 안에 있다
        ↑                                ↑
  ON 이 짝짓기 규칙이다          ON 에 쓸 것이 남아 있지 않다
        ↓                                ↓
                               그래도 LEFT JOIN 은 문법상 ON 을 요구한다
                                        ↓
                                    ON true 를 적는다 (관용구)
```

**두 엔진 다 `ON true` 를 받는다.** 쉼표 표기(`, LATERAL …`)는 `CROSS` 와 같아서 `hr` 을 못 살린다 — **`LEFT` 가 필요하면 `JOIN` 형태로 써야 한다.**

`ON` 에 진짜 조건을 적을 수도 있다. 다만 뜻이 달라진다.

```text
### SQL: SELECT d.name, t.name FROM dept d
         LEFT JOIN LATERAL (SELECT e.name, e.salary FROM emp e WHERE e.dept_id = d.id) AS t
         ON t.salary > 400 ORDER BY d.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name  | name                    +-------+------+
-------+------                   | name  | name |
 sales | bob                      +-------+------+
 dev   |                          | sales | bob  |
 hr    |                          | dev   | NULL |
(3 rows)                          | hr    | NULL |
                                  +-------+------+
```

`ON` 에서 떨어진 `cho` 는 **사라지지 않고 `NULL` 로 남았다.** 서브쿼리 `WHERE` 로 걸렀다면 같은 3행이지만, 조건을 `WHERE` 절로 올렸다면 행이 사라졌을 것이다 — 그 차이는 [15번](../15-on-vs-where-in-outer-join/)이 정본이다.

---

### 5. 상관 서브쿼리로는 안 되는 것

**에러다. 스칼라 서브쿼리는 1행만 낼 수 있다.**

```text
### SQL: SELECT d.name AS dept, (SELECT e.name FROM emp e WHERE e.dept_id = d.id
                                 ORDER BY e.salary DESC, e.id LIMIT 2) AS top FROM dept d ORDER BY d.id;
--- PG 18.6 ---
ERROR:  more than one row returned by a subquery used as an expression
--- MySQL 8.4.10 ---
ERROR 1242 (21000) at line 1: Subquery returns more than 1 row
```

**`LATERAL` 로 쓰면 된다.**

```text
### SQL: SELECT d.name AS dept, t.name AS emp, t.salary FROM dept d
         LEFT JOIN LATERAL (SELECT e.name, e.salary FROM emp e WHERE e.dept_id = d.id
                            ORDER BY e.salary DESC, e.id LIMIT 2) AS t ON true
         ORDER BY d.id, t.salary DESC;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept  | emp | salary           +-------+------+--------+
-------+-----+--------          | dept  | emp  | salary |
 sales | bob |    500           +-------+------+--------+
 sales | ann |    300           | sales | bob  |    500 |
 dev   | cho |                  | sales | ann  |    300 |
 hr    |     |                  | dev   | cho  |   NULL |
(4 rows)                        | hr    | NULL |   NULL |
                                +-------+------+--------+
```

**왜 그런가**

```text
 SELECT 칸의 서브쿼리                FROM 칸의 LATERAL
 값 하나가 들어갈 칸이다              표 하나가 들어갈 자리다
        ↓                                   ↓
 2행이 오면 어느 것을 쓸지 못 정한다   2행이 오면 결과가 2줄이 된다
        ↓                                   ↓
       에러                             정상 — 행이 늘어날 뿐
```

★ **이것이 `LATERAL` 의 존재 이유다.** [11번](../11-subquery-scalar-correlated-any-all/)의 1행 1열 계약을 푸는 문법이 `LATERAL` 이다.

```text
 상관 서브쿼리   ->  행마다 값 하나
 LATERAL        ->  행마다 표 하나
```

---

### 6. 여러 열

**`CROSS JOIN LATERAL` 로 집계 서브쿼리를 붙인다. `hr` 은 `cnt` = 0, `total` = `NULL` 이다.**

```text
### SQL: SELECT d.name AS dept, s.cnt, s.total FROM dept d
         CROSS JOIN LATERAL (SELECT COUNT(*) AS cnt, SUM(e.salary) AS total FROM emp e
                             WHERE e.dept_id = d.id) AS s ORDER BY d.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept  | cnt | total             +-------+-----+-------+
-------+-----+-------            | dept  | cnt | total |
 sales |   2 |   800             +-------+-----+-------+
 dev   |   1 |                   | sales |   2 |   800 |
 hr    |   0 |                   | dev   |   1 |  NULL |
(3 rows)                         | hr    |   0 |  NULL |
                                 +-------+-----+-------+
```

**왜 그 값들인가**

```text
 hr   : 사원 0명 -> COUNT(*) = 0 · SUM(salary) = NULL
                      ↑              ↑
            행을 세면 0          더할 것이 없으면 NULL (0 이 아니다)

 dev  : cho 하나인데 salary 가 NULL -> COUNT(*) = 1 · SUM = NULL
                                        ↑
                      COUNT(*) 은 행을 세고, SUM 은 NULL 을 건너뛴다
```

★ **`COUNT` 와 `SUM` 이 빈 입력에서 다르게 동작한다** — 0 과 `NULL`. 정본은 [21번](../21-aggregate-functions-count-forms/)다.

**같은 것을 상관 서브쿼리로 쓰면 서브쿼리를 두 번 적어야 한다.**

```text
 상관 서브쿼리로                            LATERAL 로
 SELECT d.name,                            SELECT d.name, s.cnt, s.total
   (SELECT COUNT(*) FROM emp e             FROM dept d CROSS JOIN LATERAL (
      WHERE e.dept_id = d.id) AS cnt,        SELECT COUNT(*) AS cnt, SUM(e.salary) AS total
   (SELECT SUM(salary) FROM emp e           FROM emp e WHERE e.dept_id = d.id) AS s
      WHERE e.dept_id = d.id) AS total
 FROM dept d
        ↑                                          ↑
  WHERE 조건이 두 군데 — 고칠 때 둘 다           한 군데
```

---

### 7. `CROSS` 로 써도 되는 경우

**집계 서브쿼리는 그룹 없이 쓰면 입력이 0행이어도 반드시 1행을 내기 때문이다.**

```text
 LATERAL 안이 …            입력이 0행일 때        CROSS 로 쓰면
 ------------------------  ---------------------  --------------------------
 SELECT … LIMIT N          0행                    왼쪽 행이 사라진다  <- 3번
 SELECT COUNT(*), SUM(…)   1행 (0, NULL)          왼쪽 행이 남는다    <- 6번
```

```text
 GROUP BY 가 없는 집계는 "전체를 한 그룹으로" 본다
        ↓
 그 그룹은 행이 0개여도 그룹 자체는 존재한다
        ↓
 그래서 결과가 1행 — COUNT 는 0, SUM 은 NULL
        ↓
 CROSS JOIN LATERAL 이 버릴 이유가 없다
```

★ **`GROUP BY` 를 붙이면 이야기가 달라진다** — 그룹이 없으면 0행이 되고, 그러면 `CROSS` 가 다시 왼쪽 행을 버린다.

**판단 규칙 한 줄** — **서브쿼리가 0행을 낼 수 있으면 `LEFT … ON true`, 없으면 `CROSS` 도 된다.**\
헷갈리면 **언제나 `LEFT … ON true` 를 쓰는 편이 안전하다** — 왼쪽 행이 사라지는 것은 조용한 사고다.

---

### 8. 순서를 바꾸면

**통과하지 않는다. `LATERAL` 은 왼쪽만 본다.**

```text
### SQL: SELECT d.name, t.name FROM LATERAL (SELECT e.name, e.dept_id FROM emp e WHERE e.dept_id = d.id) AS t, dept d;
--- PG 18.6 ---
ERROR:  missing FROM-clause entry for table "d"
LINE 1: ...CT e.name, e.dept_id FROM emp e WHERE e.dept_id = d.id) AS t...
                                                             ^
--- MySQL 8.4.10 ---
ERROR 1054 (42S22) at line 1: Unknown column 'd.id' in 'where clause'
```

**왜 그런가**

```text
 FROM  LATERAL (… d 참조 …) ,  dept d
       └───────┬──────────┘    └──┬──┘
               │                  │
        여기서 d 를 부를 때    d 는 아직 안 나왔다
```

★ **PG 의 에러 문구가 1번과 다르다.**

```text
 1번 (LATERAL 없이, 오른쪽에서 왼쪽 참조)
   invalid reference to FROM-clause entry   + HINT: … mark … with LATERAL
        ↑  "표는 있는데 이 자리에서는 못 쓴다"

 8번 (LATERAL 인데 오른쪽 참조)
   missing FROM-clause entry for table "d"
        ↑  "그런 표가 (아직) 없다"
```

**두 문구의 차이가 두 상황의 차이를 그대로 말한다.** 1번은 「있는데 못 쓴다」, 8번은 「아직 없다」다.

★ **그래서 `LATERAL` 이 든 `FROM` 절은 순서가 뜻을 가진다.** 일반 `FROM` 항목은 순서를 바꿔도 결과가 같지만 여기는 아니다.\
읽기에는 오히려 좋다 — **적힌 순서가 곧 계산 순서**다.

---

### 9. `RIGHT JOIN LATERAL`

**왼쪽을 참조하면 에러다. PG 는 `DETAIL` 로 규칙을 그대로 말한다.**

```text
### SQL: SELECT d.name, t.name FROM dept d RIGHT JOIN LATERAL (SELECT e.name FROM emp e WHERE e.dept_id = d.id) AS t ON true;
--- PG 18.6 ---
ERROR:  invalid reference to FROM-clause entry for table "d"
LINE 1: ...TERAL (SELECT e.name FROM emp e WHERE e.dept_id = d.id) AS t...
                                                             ^
DETAIL:  The combining JOIN type must be INNER or LEFT for a LATERAL reference.
--- MySQL 8.4.10 ---
ERROR 1054 (42S22) at line 1: Unknown column 'd.id' in 'where clause'
```

**왜 그런가**

```text
 RIGHT JOIN 은 "오른쪽을 다 남긴다" 는 뜻이다
        ↓
 왼쪽에 짝이 없는 경우에도 오른쪽 행이 결과에 있어야 한다
        ↓
 그런데 오른쪽(LATERAL)을 만들려면 왼쪽 행이 있어야 한다
        ↓
 "왼쪽 행이 없을 때의 d.id" 를 정의할 수 없다   ->  거부
```

★ **PG 의 `DETAIL` 이 [주제 목록](../README.md)의 MySQL 항목(「`INNER`/`CROSS`/`LEFT` 에만」)과 같은 내용을 말한다.**\
**두 엔진의 제약이 같다** — 목록에는 MySQL 쪽에만 적혀 있지만 실행해 보니 PG 도 똑같이 막는다.

**단, 제약은 「참조」에 걸리지 「문법 형태」에 걸리지 않는다.** 왼쪽을 안 쓰면 `RIGHT JOIN LATERAL` 도 통과한다.

```text
### SQL: SELECT d.name AS dept, t.name AS emp FROM dept d
         RIGHT JOIN LATERAL (SELECT e.name, e.dept_id FROM emp e) AS t ON t.dept_id = d.id ORDER BY t.name;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept  | emp                     +-------+-----+
-------+-----                    | dept  | emp |
 sales | ann                     +-------+-----+
 sales | bob                     | sales | ann |
 dev   | cho                     | sales | bob |
       | dan                     | dev   | cho |
(4 rows)                         | NULL  | dan |
                                 +-------+-----+
```

PG 문구의 **`for a LATERAL reference`** 가 그 조건을 달고 있었던 것이다.

---

### 10. 계획에서 확인하기

**PG 는 `loops=3`, MySQL 은 `Invalidate materialized tables (row from d)` 다.**

```text
### SQL: EXPLAIN SELECT d.name, t.name FROM dept d
         CROSS JOIN LATERAL (SELECT e.name FROM emp e WHERE e.dept_id = d.id ORDER BY e.salary DESC LIMIT 1) AS t;
--- PG 18.6 ---
 Nested Loop  (cost=24.16..30728.13 rows=1270 width=64)
   ->  Seq Scan on dept d  (cost=0.00..22.70 rows=1270 width=36)
   ->  Limit  (cost=24.16..24.16 rows=1 width=36)
         ->  Sort  (cost=24.16..24.17 rows=6 width=36)
               Sort Key: e.salary DESC
               ->  Seq Scan on emp e  (cost=0.00..24.12 rows=6 width=36)
                     Filter: (dept_id = d.id)
--- MySQL 8.4.10 (FORMAT=TREE) ---
-> Nested loop inner join  (cost=11.9 rows=4)
    -> Invalidate materialized tables (row from d)  (cost=0.65 rows=4)
        -> Covering index scan on d using name  (cost=0.65 rows=4)
    -> Table scan on t  (cost=2.96..2.96 rows=1)
        -> Materialize (invalidate on row from d)  (cost=0.45..0.45 rows=1)
            -> Limit: 1 row(s)  (cost=0.35 rows=1)
                -> Sort: e.salary DESC, limit input to 1 row(s) per chunk  (cost=0.35 rows=3)
                    -> Filter: (e.dept_id = d.id)  (cost=0.35 rows=3)
                        -> Table scan on e  (cost=0.35 rows=3)
```

```text
### SQL: EXPLAIN (ANALYZE, COSTS OFF, TIMING OFF, SUMMARY OFF, BUFFERS OFF)
         SELECT d.name, t.name FROM dept d
         CROSS JOIN LATERAL (SELECT e.name FROM emp e WHERE e.dept_id = d.id ORDER BY e.salary DESC LIMIT 1) AS t;
--- PG 18.6 ---
 Nested Loop (actual rows=2.00 loops=1)
   ->  Seq Scan on dept d (actual rows=3.00 loops=1)
   ->  Limit (actual rows=0.67 loops=3)
         ->  Sort (actual rows=0.67 loops=3)
               Sort Key: e.salary DESC
               Sort Method: quicksort  Memory: 25kB
               ->  Seq Scan on emp e (actual rows=1.00 loops=3)
                     Filter: (dept_id = d.id)
                     Rows Removed by Filter: 3
```

★ **읽는 법**

```text
 loops=3            dept 가 3행이므로 안쪽이 세 번 돌았다
 actual rows=0.67   한 번당 평균이다 — 세 번 중 두 번만 1행을 냈다 (hr 이 0행)
 0.67 x 3 = 2       그래서 최종 결과가 2행이다      <- 3번의 답과 맞는다
 Filter: (dept_id = d.id)   d.id 가 안쪽 필터로 들어가 있다 = 상관 참조의 흔적
```

**MySQL 쪽은 문장으로 말해 준다** — `Materialize (invalidate on row from d)`.\
"만들어 둔 것을 `d` 의 행이 바뀔 때마다 버린다" — **그것이 `LATERAL` 의 정의 그 자체다.**

★ **`LATERAL` 은 사실상 중첩 루프를 강제한다.** 왼쪽 행이 정해져야 오른쪽을 만들 수 있으므로,\
해시 조인이나 머지 조인으로 바꿀 여지가 없다. **비용은 왼쪽 행 수 × 안쪽 한 번 비용**이다.

> **재현 주** — PG 의 추정 행 수(`rows=1270`·`rows=6`)는 **통계가 없을 때의 기본값**이고 실제(3·4)와 무관하다.\
> **여기서 볼 것은 비용 수치가 아니라 `loops` 와 연산자 이름**이다.\
> ★ **같은 서버·같은 버전에서 두 번 찍었더니 MySQL 의 추정 행 수가 `rows=4` → `rows=3` 으로 달라져 있었다**(PG 는 불변).\
> 계획의 모양과 `Invalidate materialized tables` 는 두 번 다 같았다. 위에 실은 것은 **재확인 시점의 출력**이다.

---

### 11. 버전

**PostgreSQL 9.3 부터, MySQL 8.0.14 부터다. 근거는 둘 다 릴리스 노트다.**

```text
 PostgreSQL   9.3+       릴리스 노트로 확인
 MySQL        8.0.14+    릴리스 노트로 확인
        ↑
 MySQL 매뉴얼 페이지에는 기능 도입 버전이 거의 적혀 있지 않다
```

이번 검증에 쓴 서버는 둘 다 그보다 한참 위다.

```text
### SQL: SELECT VERSION();
--- PG 18.6 ---
 PostgreSQL 18.6 (Debian 18.6-1.pgdg13+2) on x86_64-pc-linux-gnu, compiled by gcc (Debian 14.2.0-19) 14.2.0, 64-bit
--- MySQL 8.4.10 ---
+-----------+
| VERSION() |
+-----------+
| 8.4.10    |
+-----------+
```

★ **이 규칙이 이 폴더 전체의 약속이다** — **매뉴얼에 없으면 릴리스 노트로 접지하고, 둘 다 없으면 버전을 적지 않는다**([주제 목록](../README.md)의 「버전 기준」).

**실무에서 의미** — MySQL 5.7 을 쓰는 곳에서는 `LATERAL` 이 없다. 그때의 대안은 **상관 서브쿼리(N=1 만)** 이거나 **`GROUP BY` + 조인**이다.

---

### 12. 언제 안 쓰나

**윈도우 함수 `ROW_NUMBER` 로 쓸 수 있다. 경계는 「어느 쪽이 싼가」가 아니라 「무엇의 정본인가」다.**

```text
 LATERAL 로 그룹별 상위 N              ROW_NUMBER 로 그룹별 상위 N
 왼쪽 행마다 안쪽을 돈다                한 번 훑으면서 그룹마다 번호를 매긴다
        ↓                                      ↓
 왼쪽이 적고 안쪽이 인덱스를 타면 빠르다  왼쪽이 많으면 대체로 이쪽이 낫다
```

| 요구 | 무엇을 쓰나 |
|---|---|
| 값 하나만 | 상관 서브쿼리 ([11번](../11-subquery-scalar-correlated-any-all/)) |
| 그룹마다 여러 행·여러 열 | **`LATERAL`** |
| 그룹마다 상위 N, 표가 클 때 | `ROW_NUMBER` ([목록의 **29번 주제**](../29-ranking-functions/)) |
| 「있는지만」 | `EXISTS` ([19번](../19-semi-anti-join/)) |
| 왼쪽 값을 인자로 받는 함수 | `LATERAL` (PG 는 키워드 생략 가능) |

**경계 한 줄** — **여기는 「`FROM` 에서 왼쪽 행을 참조하는 문법」까지, 29번은 「창을 나눠 행마다 번호를 매기는 함수」부터.**

★ **성능으로 고르지 마라.** 어느 쪽이 빠른지는 **인덱스가 그 정렬 순서를 이미 만들어 주느냐**에 달렸고, 그것은 계획을 봐야 안다([목록의 **47번 주제**](../47-when-indexes-are-used/)·[**58번 주제**](../58-explain-plan-tree/)).

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| `LATERAL` 없이 왼쪽 참조 (1번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **PG 의 `HINT` 가 근거다** + `LATERAL` 붙인 정상형 |
| `CROSS JOIN LATERAL` (3번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `hr` 이 사라진다 |
| `LEFT JOIN LATERAL … ON true` (4번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | `ON true` · `ON <조건>` 둘 다 |
| 쉼표 표기 `, LATERAL` | PG 18.6 · MySQL 8.4.10 | 각 1회 | 상위 2명 |
| 스칼라로 2행 (5번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **에러 메시지가 근거다** + `LATERAL` 정상형 |
| 여러 열 집계 (6·7번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `hr` 의 `0` / `NULL` |
| 순서 뒤집기 (8번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **에러 메시지가 근거다** |
| `RIGHT JOIN LATERAL` (9번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **PG 의 `DETAIL` 이 근거다** + 참조 없는 통과형 |
| 두 표를 참조하는 `LATERAL` | PG 18.6 · MySQL 8.4.10 | 각 1회 | `d` 와 `e` 둘 다 |
| 계획 (10번) | PG 18.6 · MySQL 8.4.10 | 각 1회 + PG `ANALYZE` 1회 | **`loops=3`** · `Invalidate materialized tables` |
| 버전 (11번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `SELECT VERSION()` |
| PG 의 함수 앞 키워드 생략 | PG 18.6 · MySQL 8.4.10 | 각 2회 | `generate_series` — MySQL 은 `ERROR 1064` |

**구현 의존 항목** — 10번의 계획뿐이다. `loops` 값과 연산자 이름은 옵티마이저의 선택이고, 추정 행 수는 **통계 없는 기본값**이라 재현되지 않을 수 있다.

**언어 보장 항목** — 1~9·11번. `LATERAL` 없는 참조 거부, 왼쪽만 참조, `RIGHT` 불가, 0행일 때 `CROSS`/`LEFT` 의 차이, 여러 행·여러 열은 전부 문법과 결과의 정의다.

**방언이 갈리는 항목** — **문법과 제약은 한 자리도 안 갈렸다.** 갈린 것은 둘이다.

1. **에러 문구의 질** — PG 만 `HINT`/`DETAIL` 로 `LATERAL` 과 조인 종류 제약을 알려 준다.
2. **PG 의 함수 앞 키워드 생략** — MySQL 에는 `generate_series` 자체가 없어 비교 대상이 성립하지 않는다.

목록 README 의 `20 … 차이` 표기는 **맞다** — 다만 갈리는 자리가 **도입 버전과 위 두 가지**이고, **`LATERAL` 자체의 동작과 제약은 같다.**\
README 가 MySQL 쪽에만 적어 둔 「`INNER`/`CROSS`/`LEFT` 에만」 제약은 **PG 에도 똑같이 있다**(9번의 `DETAIL`).

**순서 보장** — 없다. 위 출력에 `ORDER BY` 를 붙인 것은 그 때문이다.\
**`emp`·`dept` 변경** — 없다. 이 주제는 기존 두 표를 읽기만 했다.
