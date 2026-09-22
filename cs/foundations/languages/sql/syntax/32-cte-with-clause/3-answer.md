# sql/32-CTE(`WITH`) — 이름 붙인 서브질의와 가시성 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력·에러·실행 계획은 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 지어낸 출력은 없다.\
> 표는 기존 `emp`·`dept` 만 썼다 — **새로 만든 표가 없다.**\
> 문서 근거는 [PG 18 WITH Queries](https://www.postgresql.org/docs/18/queries-with.html) · [PG 12 릴리스 노트](https://www.postgresql.org/docs/release/12.0/) · [MySQL 8.4 WITH](https://dev.mysql.com/doc/refman/8.4/en/with.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. CTE 와 파생 테이블의 결과

**결과는 한 행도 다르지 않다. 달라진 것은 「정의가 한 군데냐 두 군데냐」뿐이다.**

```text
### SQL: WITH big AS (SELECT id, name, salary FROM emp WHERE salary >= 400)
         SELECT a.name AS x, b.name AS y FROM big a JOIN big b ON a.id < b.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
  x  |  y                        +-----+-----+
-----+-----                      | x   | y   |
 bob | dan                       +-----+-----+
(1 row)                          | bob | dan |
                                 +-----+-----+

### SQL: SELECT a.name AS x, b.name AS y
         FROM (SELECT id, name, salary FROM emp WHERE salary >= 400) a
         JOIN (SELECT id, name, salary FROM emp WHERE salary >= 400) b ON a.id < b.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
  x  |  y                        +-----+-----+
-----+-----                      | x   | y   |
 bob | dan                       +-----+-----+
(1 row)                          | bob | dan |
                                 +-----+-----+
```

**왜 그런가** — `salary >= 400` 이 고르는 것은 `bob`(500)·`dan`(400) 둘이고, `a.id < b.id` 가 `(2, 4)` 한 짝만 남긴다.

```text
 big = { bob(2), dan(4) }
 a  x  b  ->  (2,2) x  (2,4) O  (4,2) x  (4,4) x
                          ^ a.id < b.id 를 만족하는 유일한 짝
```

CTE 는 **이름을 붙였을 뿐**이므로 결과가 바뀔 이유가 없다.\
달라진 것은 **`SELECT id, name, salary FROM emp WHERE salary >= 400` 을 몇 번 적었나**다 — 파생 테이블 쪽은 두 번이고, **한쪽만 고치면 에러 없이 어긋난다.**

---

### 2. 파생 테이블로는 못 하는 것

**이름을 붙이면 「한 번 정의하고 여러 번 참조」할 수 있다. 그것 하나다.**

```text
 파생 테이블                              CTE
 FROM (SELECT ... 400) a                  WITH big AS (SELECT ... 400)
 JOIN (SELECT ... 400) b                  ... FROM big a JOIN big b
      ^^^^^^^^^^^^^^^^                              ^^^      ^^^
      정의가 두 군데                                이름이 두 번, 정의는 한 군데
      -> 한쪽만 고치면 조용히 어긋난다              -> 어긋날 수가 없다
```

**나머지는 전부 같다** — 결과도, 별칭 규칙도, 바깥을 못 본다는 것도 같다(바깥 참조는 [`LATERAL`](../20-lateral-join/)이다).\
그래서 **CTE 를 "성능 도구"로 배우면 틀린다.** 이름 붙이기는 **읽기와 유지보수**를 위한 것이고, 성능은 6~9번의 옵티마이저 이야기다.

---

### 3. CTE 끼리 서로 보기

**(A) 통과 · (B) 에러. 뒤에서 앞은 보이고, 앞에서 뒤는 안 보인다.**

```text
### SQL: WITH a AS (SELECT id FROM dept), b AS (SELECT id + 1 AS id FROM a) SELECT * FROM b ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id                              +----+
----                             | id |
 11                              +----+
 21                              | 11 |
 31                              | 21 |
(3 rows)                         | 31 |
                                 +----+

### SQL: WITH a AS (SELECT id FROM b), b AS (SELECT id FROM dept) SELECT * FROM a;
--- PG 18.6 ---
ERROR:  relation "b" does not exist
LINE 1: WITH a AS (SELECT id FROM b), b AS (SELECT id FROM dept) SEL...
                                  ^
DETAIL:  There is a WITH item named "b", but it cannot be referenced from this part of the query.
HINT:  Use WITH RECURSIVE, or re-order the WITH items to remove forward references.
--- MySQL 8.4.10 ---
ERROR 1146 (42S02) at line 1: Table 'study.b' doesn't exist
```

**왜 그런가** — `WITH` 목록은 **위에서 아래로** 이름을 세운다. `b` 를 정의하는 시점에 `a` 는 이미 이름이 있지만, `a` 를 정의하는 시점에 `b` 는 아직 없다.

★ **에러 메시지의 질이 크게 다르다.**

| | PG 18.6 | MySQL 8.4.10 |
|---|---|---|
| 무엇이 없다고 하나 | `relation "b" does not exist` | `Table 'study.b' doesn't exist` |
| **WITH 항목이라는 사실을 알려 주나** | `DETAIL: There is a WITH item named "b"` — **알려 준다** | 알려 주지 않는다 |
| **고치는 법을 알려 주나** | `HINT: Use WITH RECURSIVE, or re-order` — **알려 준다** | 알려 주지 않는다 |

**MySQL 쪽 메시지는 표 이름 오타와 구분이 안 된다.** `study.b` 라는 표를 찾으러 가면 시간을 버린다 — **`WITH` 목록의 순서부터 보라.**

---

### 4. 이름의 수명

**두 번째 문장은 에러다. CTE 는 아무 데도 저장되지 않는다.**

```text
### SQL: WITH t AS (SELECT id FROM dept) SELECT 1;   -- 첫 문장
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 ?column?                        +---+
----------                       | 1 |
        1                        +---+
(1 row)                          | 1 |
                                 +---+

### SQL: SELECT * FROM t;   -- 바로 다음 문장
--- PG 18.6 ---
ERROR:  relation "t" does not exist
--- MySQL 8.4.10 ---
ERROR 1146 (42S02) at line 1: Table 'study.t' doesn't exist
```

```text
 WITH t AS (...) SELECT 1 ;   SELECT * FROM t;
 └──── t 가 사는 범위 ────┘    ↑
                               여기서는 없는 이름이다
```

**왜 그런가** — CTE 는 **질의문의 일부**이지 객체가 아니다. 파싱된 문장이 끝나면 이름도 끝난다.\
문장을 넘겨 재사용하려면 **뷰**([48번 주제](../48-views-and-materialized-views/))나 임시 표여야 한다.

반대로 **괄호 안에 `WITH` 를 또 쓸 수는 있다** — 그 이름은 그 괄호 안에서만 산다.

```text
### SQL: SELECT (SELECT COUNT(*) FROM (WITH x AS (SELECT id FROM dept) SELECT * FROM x) AS s) AS n;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 n                               +------+
---                              | n    |
 3                               +------+
(1 row)                          |    3 |
                                 +------+
```

---

### 5. 이름이 겹치면

**에러가 아니다. CTE 가 이긴다 — 두 엔진 모두 조용히.**

```text
### SQL: WITH emp AS (SELECT 99 AS id, 'ghost' AS name) SELECT * FROM emp;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name                       +----+-------+
----+-------                     | id | name  |
 99 | ghost                      +----+-------+
(1 row)                          | 99 | ghost |
                                 +----+-------+
```

**왜 그런가** — 이름 해석은 **가장 가까운 것부터**다. 그 문장 안에서는 CTE 이름이 스키마의 표 이름보다 가깝다.

```text
 이름 emp 를 찾는 순서
   1) 이 문장의 WITH 목록   <- 여기서 찾으면 끝. 아래를 보지 않는다
   2) FROM 의 별칭
   3) 스키마의 실제 표
```

★ **이것이 이 주제의 무음 실패다.** 에러도 경고도 없고, 열 이름도 타입도 맞고, **값만 틀린다.**\
[11번](../11-subquery-scalar-correlated-any-all/)의 "한정자를 빼서 `0,0,0` 이 나온" 사고와 같은 종류다 — **이름 해석이 조용히 다른 것을 고른다.**

처방은 **CTE 이름에 접두어**(`cte_`·`x_`)를 붙이는 것이다.

---

### 6. 최적화 장벽이 서나

**다르다. `Index Cond` 냐 `Filter` 냐로 갈린다.**

```text
### SQL: EXPLAIN (COSTS OFF) WITH c AS (SELECT * FROM emp) SELECT * FROM c WHERE id = 1;
--- PG 18.6 ---
            QUERY PLAN            
----------------------------------
 Index Scan using emp_pkey on emp
   Index Cond: (id = 1)
(2 rows)

### SQL: EXPLAIN (COSTS OFF) WITH c AS MATERIALIZED (SELECT * FROM emp) SELECT * FROM c WHERE id = 1;
--- PG 18.6 ---
       QUERY PLAN        
-------------------------
 CTE Scan on c
   Filter: (id = 1)
   CTE c
     ->  Seq Scan on emp
(4 rows)
```

**왜 그런가** — 벽이 없으면 `WHERE id = 1` 이 **CTE 안으로 내려가** 인덱스 조건이 된다. 벽이 있으면 CTE 가 **네 행을 다 만든 뒤** 그 위에서 거른다.

```text
 (A) 인라인                          (B) MATERIALIZED
 emp ─[Index Cond: id=1]→ 1행         emp ─[Seq Scan]→ 4행 ─[Filter: id=1]→ 1행
      ^^^^^^^^^^^^^^^^^^                               ^^^^^^^^^^^^^^^^^^
      인덱스가 걸러 준다                                만든 뒤에 버린다
```

**구분하는 낱말 셋** — `CTE c` 노드가 있나 · `CTE Scan` 이 있나 · 조건이 `Index Cond` 인가 `Filter` 인가.\
셋 중 하나만 봐도 되지만, **`CTE` 라는 낱말이 계획에 뜨면 벽이 선 것**이라고 외우면 가장 싸다.

---

### 7. "CTE 는 최적화 장벽이다"는 언제부터 틀렸나

**PostgreSQL 12 부터다.** 11 이하에서는 참이었다.

> "Specifically, CTEs are automatically inlined if they have no side-effects, are not recursive, and are referenced only once in the query. Inlining can be prevented by specifying `MATERIALIZED`, or forced for multiply-referenced CTEs by specifying `NOT MATERIALIZED`. **Previously, CTEs were never inlined and were always evaluated before the rest of the query.**"\
> — [PostgreSQL 12 릴리스 노트](https://www.postgresql.org/docs/release/12.0/)

```text
 PG 11 이하                          PG 12 이상
 모든 CTE = 항상 물질화               조건 셋을 다 만족하면 인라인
 -> "CTE 는 최적화 장벽"이 참           1) 재귀가 아니고
 -> CTE 로 감싸서 일부러 벽을 세우는     2) 부작용(휘발성 함수)이 없고
    기법이 널리 쓰였다                   3) 참조가 한 번뿐이면
                                      -> 그 기법은 이제 안 먹는다
                                         (MATERIALIZED 를 명시해야 한다)
```

**바뀐 것은 문법이 아니라 기본값이다.** 같은 문장이 버전에 따라 다른 계획을 낸다 — 그래서 이 주제는 **버전을 적지 않으면 문장이 성립하지 않는다.**\
MySQL 쪽에는 이런 기본값 선언 자체가 매뉴얼에 없다(8번·12번).

---

### 8. 참조를 하나 더 늘리면

**PG 에만 `CTE` 라는 이름이 남는다. MySQL 8.4.10 의 계획에서는 `c` 가 사라진다.**

```text
### SQL: EXPLAIN (COSTS OFF) WITH c AS (SELECT * FROM emp)
         SELECT a.name, b.name FROM c a JOIN c b ON a.id < b.id;
--- PG 18.6 ---
          QUERY PLAN          
------------------------------
 Nested Loop
   Join Filter: (a.id < b.id)
   CTE c                        <- 한 번 만들고
     ->  Seq Scan on emp
   ->  CTE Scan on c a          <- 두 번 읽는다
   ->  CTE Scan on c b
(6 rows)
--- MySQL 8.4.10 ---
+---------------------------------------------------------------------------+
| EXPLAIN                                                                   |
+---------------------------------------------------------------------------+
| -> Nested loop inner join  (cost=1.7 rows=3)
    -> Table scan on emp  (cost=0.55 rows=3)
    -> Filter: (emp.id < emp.id)  (cost=0.117 rows=1)
        -> Index range scan on emp (re-planned for each iteration)  (cost=0.117 rows=3)
 |
+---------------------------------------------------------------------------+
```

**왜 그런가** — PG 문서의 기본 규칙이 "참조가 한 번일 때만 편다"이므로, 두 번이 되는 순간 벽이 선다.\
MySQL 8.4.10 은 **CTE 를 그냥 펴서 `emp` 를 두 번 읽었다** — `c` 라는 낱말이 계획 어디에도 없다.

**단 MySQL 도 집계가 들어가면 물질화한다.**

```text
### SQL: EXPLAIN FORMAT=TREE WITH s AS (SELECT dept_id, SUM(salary) AS tot FROM emp GROUP BY dept_id)
         SELECT a.dept_id, b.dept_id FROM s a JOIN s b ON a.tot < b.tot;
--- MySQL 8.4.10 ---
| -> Filter: (a.tot < b.tot)  (cost=5.04 rows=0)
    -> Inner hash join (no condition)  (cost=5.04 rows=0)
        -> Table scan on b  (cost=2.5..2.5 rows=0)
            -> Materialize CTE s if needed (query plan printed elsewhere)  (cost=0..0 rows=0)
        -> Hash
            -> Table scan on a  (cost=2.5..2.5 rows=0)
                -> Materialize CTE s if needed  (cost=0..0 rows=0)
                    -> Table scan on <temporary>
                        -> Aggregate using temporary table
                            -> Table scan on emp  (cost=0.55 rows=3)
```

★ **`if needed` 라는 낱말이 그대로 답이다** — MySQL 은 **약속하지 않는다.** 그때그때 정한다.\
그래서 **PG 에서 얻은 "CTE 를 두 번 참조하면 벽이 선다"는 결론을 MySQL 로 옮기면 안 된다.**

---

### 9. `MATERIALIZED` 를 MySQL 에

**`ERROR 1064` — 문법 자체가 없다. 대체 수단은 옵티마이저 힌트다.**

```text
### SQL: WITH c AS MATERIALIZED (SELECT * FROM emp) SELECT * FROM c WHERE id = 1;
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near 'MATERIALIZED (SELECT * FROM emp) SELECT * FROM c WHERE id = 1' at line 1

### SQL: WITH c AS NOT MATERIALIZED (SELECT * FROM emp) SELECT * FROM c WHERE id = 1;
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near 'NOT MATERIALIZED (SELECT * FROM emp) SELECT * FROM c WHERE id = 1' at line 1
```

MySQL 쪽 손잡이는 `/*+ NO_MERGE(…) */` 힌트다.

```text
### SQL: EXPLAIN FORMAT=TREE WITH c AS (SELECT * FROM emp) SELECT /*+ NO_MERGE(c) */ * FROM c WHERE salary >= 400;
--- MySQL 8.4.10 ---
| -> Table scan on c  (cost=3.16..3.16 rows=1)
    -> Materialize CTE c  (cost=0.65..0.65 rows=1)
        -> Filter: (emp.salary >= 400)  (cost=0.55 rows=1)
            -> Table scan on emp  (cost=0.55 rows=3)

### SQL: EXPLAIN FORMAT=TREE WITH c AS (SELECT * FROM emp) SELECT * FROM c WHERE salary >= 400;   -- 힌트 없이
--- MySQL 8.4.10 ---
| -> Filter: (emp.salary >= 400)  (cost=0.55 rows=1)
    -> Table scan on emp  (cost=0.55 rows=3)
```

★ **그런데 같은 물건이 아니다.** `NO_MERGE(c)` 를 줘서 `Materialize CTE c` 가 떴는데도, **그 안쪽에 `Filter: (emp.salary >= 400)` 이 그대로 있다** — 조건은 내려갔다.\
PG 의 `MATERIALIZED` 는 조건을 못 내려가게 하는데(6번의 `Filter` 가 **CTE 바깥**에 있었다), MySQL 의 `NO_MERGE` 는 **물질화만 시키고 조건은 내려보낸다.**\
**이름이 비슷하다고 같은 물건으로 외우면 틀린다.**

---

### 10. `NOT MATERIALIZED` 가 안 먹는 경우

**`CTE Scan` 이 뜬다 — 벽이 남는다. 이유는 성능이 아니라 정확성이다.**

```text
### SQL: EXPLAIN (COSTS OFF) WITH c AS NOT MATERIALIZED (SELECT random() AS r FROM emp) SELECT * FROM c;
--- PG 18.6 ---
       QUERY PLAN        
-------------------------
 CTE Scan on c
   CTE c
     ->  Seq Scan on emp
(3 rows)
```

**왜 그런가** — PG 문서의 조건은 **「비재귀 **그리고** 부작용 없음」이 먼저**다.

> "if a `WITH` query is non-recursive and side-effect-free (that is, it is a `SELECT` containing no volatile functions) then it can be folded into the parent query"\
> — [PostgreSQL 18 · WITH Queries](https://www.postgresql.org/docs/18/queries-with.html)

`random()` 은 휘발성이라 그 전제가 깨진다. `NOT MATERIALIZED` 는 **"참조가 여럿이어도 펴 달라"는 요청**이지, 전제를 뒤집는 명령이 아니다.

그리고 그 벽에는 **결과에 걸린 의미**가 있다.

```text
### SQL: WITH c AS NOT MATERIALIZED (SELECT random() AS r) SELECT (SELECT r FROM c) = (SELECT r FROM c) AS same;
--- PG 18.6 ---
 same 
------
 t
(1 row)
```

```text
 물질화 (실제)                        인라인 (만약 폈다면)
 random() 을 한 번 계산                random() 이 양쪽에서 따로 계산될 수 있다
   -> 두 번 읽어도 같은 값              -> 두 값이 달라질 수 있다
   -> same = t                          -> same 이 f 가 될 수 있다
```

**같은 문장이 다른 답을 낼 수 있으므로** 옵티마이저는 함부로 펴지 못한다. **성능 문제가 아니라 의미 문제다.**

---

### 11. 열 이름 다시 붙이기

**CTE 결과의 열 이름을 통째로 바꿔 붙인다. 두 엔진에서 같다.**

```text
### SQL: WITH d(k, v) AS (SELECT id, name FROM dept) SELECT k, v FROM d ORDER BY k;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 k  |   v                        +----+-------+
----+-------                     | k  | v     |
 10 | sales                      +----+-------+
 20 | dev                        | 10 | sales |
 30 | hr                         | 20 | dev   |
(3 rows)                         | 30 | hr    |
                                 +----+-------+
```

**왜 쓰나** — 안쪽 질의가 `SELECT id + 1` 처럼 **이름 없는 식**을 낼 때, 안쪽을 건드리지 않고 바깥에서 이름을 정할 수 있다.\
그리고 [33번](../33-recursive-cte/)의 재귀 CTE 에서는 **이 형태가 사실상 표준**이 된다 — `WITH RECURSIVE t(n) AS (…)`.

**주의** — 개수가 안 맞으면 에러다. 안쪽 `SELECT` 의 열 개수와 `(k, v)` 의 개수는 같아야 한다.

---

### 12. 계획을 근거로 써도 되나

**관찰이다. 보장이 아니다.**

| 외울 것 (규칙) | 외우면 안 되는 것 (관찰) |
|---|---|
| CTE 는 이름을 붙일 뿐 결과를 바꾸지 않는다 | `Index Scan using emp_pkey` 라는 계획 모양 |
| 이름은 앞→뒤로만 보이고 문장 하나만 산다 | `cost=0.55 rows=3` 같은 수치 |
| PG 12+ 는 **참조 1회 + 비재귀 + 부작용 없음**이면 편다 | "PG 는 항상 편다" / "MySQL 은 항상 편다" |
| 휘발성이 있으면 `NOT MATERIALIZED` 를 적어도 안 편다 | `Materialize CTE s if needed` 가 항상 뜬다는 것 |
| `MATERIALIZED` 는 PG 전용, MySQL 은 힌트 | 두 손잡이가 같은 물건이라는 것(9번에서 깨졌다) |

★ **실측** — 이 주제의 모든 `EXPLAIN` 을 **작성 중 한 번, 제출 직전 한 번** 같은 서버·같은 버전·같은 데이터에서 찍었다.\
**두 번의 출력이 한 글자도 달라지지 않았다.** 그것은 "이 서버의 통계가 안 흔들렸다"는 뜻이지 **"다음에도 같다"는 뜻이 아니다.**\
[11번](../11-subquery-scalar-correlated-any-all/)에서는 같은 조건에서 **MySQL 의 추정 행 수가 두 판 사이에 `rows=4` → `rows=3` 으로 달라진 적이 있다.**

그래서 `EXPLAIN (COSTS OFF)` 로 찍었다 — **볼 것은 비용이 아니라 노드의 모양**이고, 그마저도 **규칙을 확인하는 도구**이지 규칙 자체가 아니다.

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| CTE 와 파생 테이블의 결과 동일 (1번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | 두 형태를 각각 |
| 두 번 참조 (2번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 1번의 출력을 근거로 쓴다 |
| CTE 간 가시성 (3번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **에러 메시지가 근거다** — PG 의 `DETAIL`/`HINT` |
| 이름의 수명 (4번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | 두 문장 + 중첩 `WITH` |
| 이름 가리기 (5번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **에러 없이 CTE 가 이긴다** — 무음 실패 |
| `MATERIALIZED` 계획 (6번) | PG 18.6 | 3회 (기본·`MATERIALIZED`·`NOT`) | `Index Cond` 대 `Filter` |
| 인라인 도입 버전 (7번) | — | — | **릴리스 노트 인용**(실행 아님) |
| 참조 2회의 계획 (8번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | 단순 CTE + 집계 CTE |
| MySQL 의 `MATERIALIZED` (9번) | MySQL 8.4.10 | 3회 | **`ERROR 1064` 가 근거다** + `NO_MERGE` 힌트 2회 |
| 휘발성 CTE (10번) | PG 18.6 | 2회 | 계획 + `same = t` |
| 열 이름 다시 붙이기 (11번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | |
| 계획 재확인 (12번) | PG 18.6 · MySQL 8.4.10 | **전 계획 2회씩** | 작성 중 1회 + 제출 직전 1회 — **드리프트 없음** |

**구현 의존 항목** — 6·8·9·10번의 계획 전부. `CTE Scan`·`Materialize CTE … if needed`·`Index range scan … (re-planned for each iteration)` 은 **그 엔진의 표기**이고, 실제로 무엇을 고르는지는 옵티마이저의 선택이다.\
★ **한쪽에서만 결론이 서는 실험이 하나 있다** — **6번(`MATERIALIZED`)은 PG 출력만 근거가 된다.** MySQL 쪽은 문법이 없어 `ERROR 1064` 이므로, 그 에러는 **"MySQL 에 이 손잡이가 없다"의 근거일 뿐 "벽이 서나 안 서나"의 근거가 아니다.**\
MySQL 쪽 벽 유무의 근거는 **8번·9번의 `EXPLAIN FORMAT=TREE`** 다.

**언어 보장 항목** — 1~5·11번. 결과의 동일성, 가시성 규칙, 이름 수명, 이름 가리기, 열 이름 재지정은 두 엔진에서 같았다.\
**방언이 갈리는 항목** — 6·8·9번. `MATERIALIZED`/`NOT MATERIALIZED` 는 **PG 12+ 전용**이고, **참조 2회에서 PG 는 벽을 세우는데 MySQL 8.4.10 은 안 세웠다.**\
3번은 **성패가 같고 메시지의 질만 다르다** — PG 만 `WITH` 항목임을 알려 준다.

**순서 보장** — 없다. 위 출력에 `ORDER BY` 를 붙인 것은 그 때문이다.
