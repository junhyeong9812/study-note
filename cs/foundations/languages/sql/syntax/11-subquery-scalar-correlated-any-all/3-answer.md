# sql/11-서브쿼리 — 스칼라·상관·ANY/ALL — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력은 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 에러 메시지도 실제로 받은 것이고, 지어낸 출력은 없다.\
> 표는 기존 `emp`·`dept` 만 썼다 — **새로 만든 표가 없다.**\
> 문서 근거는 [PG 18 Subquery Expressions](https://www.postgresql.org/docs/18/functions-subquery.html) · [MySQL 8.4 Subqueries](https://dev.mysql.com/doc/refman/8.4/en/subqueries.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. 스칼라 서브쿼리의 세 가지 결말

**(A) 값 500 이 4행에 붙는다 · (B) `NULL` · (C) 에러.**

```text
### SQL: SELECT name, (SELECT MAX(salary) FROM emp) AS top FROM emp ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | top                      +------+------+
------+-----                     | name | top  |
 ann  | 500                      +------+------+
 bob  | 500                      | ann  |  500 |
 cho  | 500                      | bob  |  500 |
 dan  | 500                      | cho  |  500 |
(4 rows)                         | dan  |  500 |
                                 +------+------+

### SQL: SELECT (SELECT id FROM dept WHERE name = 'nope') AS zero_rows;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 zero_rows                       +-----------+
-----------                      | zero_rows |
                                 +-----------+
(1 row)                          |      NULL |
                                 +-----------+

### SQL: SELECT name, (SELECT id FROM dept) AS d FROM emp ORDER BY id;
--- PG 18.6 ---
ERROR:  more than one row returned by a subquery used as an expression
--- MySQL 8.4.10 ---
ERROR 1242 (21000) at line 1: Subquery returns more than 1 row
```

**왜 그런가** — 스칼라 서브쿼리의 계약은 **1행 1열**이고, 행 수에 따라 처분이 셋으로 갈린다.

```text
 서브쿼리가 낸 행 수      처분
 ---------------------   ------------------------------------------
 0 행                    NULL          <- 에러가 아니다
 1 행                    그 값
 2 행 이상               에러          <- 값 하나를 고를 방법이 없다
       ↑
 0 과 2 의 처분이 다르다는 것이 이 문항의 전부다
```

**(B) 의 빈 칸과 `NULL` 은 같은 값이다** — psql 이 `NULL` 을 빈 칸으로 찍을 뿐이다.

이 `NULL` 은 **조용하다.** 바깥 조건에 들어가면 행이 통째로 사라진다.

```text
### SQL: SELECT name FROM emp WHERE dept_id = (SELECT dept_id FROM emp WHERE name = 'zzz');
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name                            (빈 결과 — 출력이 한 줄도 없다)
------
(0 rows)
```

`dept_id = NULL` 이 네 행 모두에서 `UNKNOWN` 이라 전부 떨어졌다([04번](../04-null-three-valued-logic/)).\
**"조건에 맞는 게 없다"가 아니라 "비교 자체가 성립하지 않았다"다.**

---

### 2. 열이 둘인 스칼라 서브쿼리

**에러다. 두 엔진 다 거부한다.**

```text
### SQL: SELECT (SELECT id, name FROM dept WHERE id = 10) AS two_cols;
--- PG 18.6 ---
ERROR:  subquery must return only one column
LINE 1: SELECT (SELECT id, name FROM dept WHERE id = 10) AS two_cols...
               ^
--- MySQL 8.4.10 ---
ERROR 1241 (21000) at line 1: Operand should contain 1 column(s)
```

**왜 그런가** — 값이 들어갈 칸은 하나인데 두 개를 내밀었다. 어느 것을 쓸지 정할 방법이 없다.

`ANY`/`ALL` 자리에서도 같은 계약이 걸린다.

```text
### SQL: SELECT name FROM emp WHERE dept_id > ANY (SELECT id, name FROM dept);
--- PG 18.6 ---
ERROR:  subquery has too many columns
LINE 1: SELECT name FROM emp WHERE dept_id > ANY (SELECT id, name FR...
                                           ^
--- MySQL 8.4.10 ---
ERROR 1241 (21000) at line 1: Operand should contain 1 column(s)
```

| 자리 | PG 18.6 | MySQL 8.4.10 |
|---|---|---|
| 값 자리 | `subquery must return only one column` | `ERROR 1241 … Operand should contain 1 column(s)` |
| `ANY` 자리 | `subquery has too many columns` | `ERROR 1241 … Operand should contain 1 column(s)` |

**PG 는 자리마다 문구가 다르고 MySQL 은 하나로 통일했다.** 같은 계약을 같은 강도로 지킨다.

---

### 3. 그 에러가 나는 시점

**열 개수는 문장만 봐도 알지만, 행 개수는 데이터를 봐야 알기 때문이다.**

```text
 (SELECT id, name FROM dept …)        (SELECT id FROM dept …)
        ↑                                     ↑
 SELECT 목록에 두 개가 적혀 있다      한 개다 — 문장은 합격
        ↓                                     ↓
 파싱·분석 단계에서 잡힌다            몇 행이 걸릴지는 돌려 봐야 안다
                                              ↓
                                      실행 중에 두 번째 행을 만나는 순간 터진다
```

**증거 — 같은 문장이 조건 하나 차이로 통과하기도 하고 터지기도 한다.**

```text
### SQL: SELECT (SELECT x.id FROM (SELECT 10 AS id UNION ALL SELECT 20) AS x WHERE x.id >= 20) AS ok;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 ok                              +------+
----                             | ok   |
 20                              +------+
(1 row)                          |   20 |
                                 +------+

### SQL: SELECT (SELECT x.id FROM (SELECT 10 AS id UNION ALL SELECT 20) AS x WHERE x.id >= 10) AS boom;
--- PG 18.6 ---
ERROR:  more than one row returned by a subquery used as an expression
--- MySQL 8.4.10 ---
ERROR 1242 (21000) at line 1: Subquery returns more than 1 row
```

★ **실무에서 무서운 쪽은 행 에러다.** 문장은 멀쩡하므로 리뷰도 통과하고 테스트도 통과한다.\
데이터가 늘어난 **어느 날 밤**에 처음 터진다.

**처방** — 1행이 보장되지 않으면 스칼라로 쓰지 않는다. `LIMIT 1` 을 붙일 거면 `ORDER BY` 로 **어느 행인지**를 정하고, 그게 정해지지 않으면 요구사항이 덜 정해진 것이다.

---

### 4. 상관 서브쿼리의 결과

**4행이다. `dan` 의 `dept` 칸은 `NULL` 이고 행은 남는다.**

```text
### SQL: SELECT e.name, (SELECT d.name FROM dept d WHERE d.id = e.dept_id) AS dept FROM emp e ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | dept                     +------+-------+
------+-------                   | name | dept  |
 ann  | sales                    +------+-------+
 bob  | sales                    | ann  | sales |
 cho  | dev                      | bob  | sales |
 dan  |                          | cho  | dev   |
(4 rows)                         | dan  | NULL  |
                                 +------+-------+
```

**왜 그런가** — 바깥 행마다 서브쿼리가 한 번씩 돌았다.

```text
 바깥 행      서브쿼리가 받은 조건        서브쿼리 결과   붙은 값
 ----------   -------------------------   -------------   --------
 ann          d.id = 10                   1행 'sales'     sales
 bob          d.id = 10                   1행 'sales'     sales
 cho          d.id = 20                   1행 'dev'       dev
 dan          d.id = NULL                 0행             NULL     <- 1번의 (B)
```

★ **행이 사라지지 않은 것이 조인과의 결정적 차이다.**

```text
 스칼라 서브쿼리로 붙이기            INNER JOIN 으로 붙이기
 SELECT e.name, (SELECT d.name …)    FROM emp e JOIN dept d ON e.dept_id = d.id
        ↓                                    ↓
      4행 (dan 은 NULL)                    3행 (dan 이 사라진다)   <- 13번
        ↑                                    ↑
 바깥 행 수가 그대로다              짝이 없으면 행이 없어진다
```

`LEFT JOIN` 과 결과가 같아진다([14번](../14-left-right-outer-join/)) — 다만 **열이 하나만 필요할 때**는 이쪽이 짧다.\
열이 여럿 필요하면 서브쿼리를 두 번 써야 하고, 그때가 [`LATERAL`](../20-lateral-join/)의 자리다.

---

### 5. 계획에서 상관을 알아보는 낱말

**PG 는 `InitPlan`(비상관) 대 `SubPlan`(상관), MySQL 은 `run only once`(비상관) 대 `dependent`(상관) 다.**

```text
### SQL: EXPLAIN SELECT e.name, (SELECT MAX(salary) FROM emp) AS top FROM emp e;   -- 비상관
--- PG 18.6 ---
 Seq Scan on emp e  (cost=24.14..45.44 rows=1130 width=36)
   InitPlan 1
     ->  Aggregate  (cost=24.12..24.14 rows=1 width=4)
           ->  Seq Scan on emp  (cost=0.00..21.30 rows=1130 width=4)
--- MySQL 8.4.10 (FORMAT=TREE) ---
-> Table scan on e  (cost=0.55 rows=3)
-> Select #2 (subquery in projection; run only once)
    -> Aggregate: max(emp.salary)  (cost=0.85 rows=1)
        -> Table scan on emp  (cost=0.55 rows=3)
### SQL: EXPLAIN SELECT e.name, (SELECT d.name FROM dept d WHERE d.id = e.dept_id) AS dept FROM emp e;   -- 상관
--- PG 18.6 ---
 Seq Scan on emp e  (cost=0.00..9253.40 rows=1130 width=64)
   SubPlan 1
     ->  Index Scan using dept_pkey on dept d  (cost=0.15..8.17 rows=1 width=32)
           Index Cond: (id = e.dept_id)
--- MySQL 8.4.10 (FORMAT=TREE) ---
-> Table scan on e  (cost=0.55 rows=3)
-> Select #2 (subquery in projection; dependent)
    -> Single-row index lookup on d using PRIMARY (id=e.dept_id)  (cost=0.35 rows=1)
```

| | 비상관 | 상관 |
|---|---|---|
| PostgreSQL 18.6 | `InitPlan 1` | `SubPlan 1` |
| MySQL 8.4.10 | `subquery in projection; run only once` | `subquery in projection; dependent` |

**몇 번 돌았는지는 `EXPLAIN ANALYZE` 가 센다.**

```text
### SQL: EXPLAIN (ANALYZE, COSTS OFF, TIMING OFF, SUMMARY OFF, BUFFERS OFF)
         SELECT e.name, (SELECT d.name FROM dept d WHERE d.id = e.dept_id) FROM emp e;
--- PG 18.6 ---
 Seq Scan on emp e (actual rows=4.00 loops=1)
   SubPlan 1
     ->  Index Scan using dept_pkey on dept d (actual rows=0.75 loops=4)
           Index Cond: (id = e.dept_id)
           Index Searches: 3
```

★ **`loops=4`.** `emp` 가 4행이니 서브쿼리가 네 번 돌았다.\
`Index Searches: 3` 은 `dan` 의 `NULL` 에서는 **찾아볼 것도 없이 건너뛰었다**는 뜻이다.

**주의 — 이것은 보장이 아니라 이 판의 선택이다.** 「바깥 행마다 다시 돈다」는 **의미론**이고, 엔진은 같은 답이 나오면 조인으로 바꿔 한 번에 끝내도 된다.\
실제로 `EXISTS` 형태는 두 엔진 다 세미 조인으로 바꿔 버린다([19번](../19-semi-anti-join/)).\
위 계획의 추정 행 수(`rows=1130`)는 **통계가 없을 때의 기본값**이므로, 여기서 볼 것은 비용 수치가 아니라 **계획의 모양**이다.

---

### 6. 한정자를 뺐을 때

**`0, 0, 0` 이 나온다. 에러는 안 난다.**

```text
### SQL: SELECT d.name, (SELECT COUNT(*) FROM emp e WHERE e.dept_id = id) AS n FROM dept d ORDER BY d.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name  | n                       +-------+------+
-------+---                      | name  | n    |
 sales | 0                       +-------+------+
 dev   | 0                       | sales |    0 |
 hr    | 0                       | dev   |    0 |
(3 rows)                         | hr    |    0 |
                                 +-------+------+
```

**왜 그런가** — **이름은 안쪽부터 찾는다.** `emp` 에도 `id` 열이 있어서 거기서 이미 찾아졌다.

```text
 안쪽 SELECT 가 id 를 찾는 순서
   1) 자기 FROM 의 emp 에서 찾는다  ->  찾았다! emp.id
   2) (바깥으로 나가지 않는다)
        ↓
 쓴 것:      e.dept_id = id
 읽힌 것:    e.dept_id = e.id
        ↓
 ann: 10 = 1 ?  FALSE      bob: 10 = 2 ?  FALSE
 cho: 20 = 3 ?  FALSE      dan: NULL = 4 ? UNKNOWN
        ↓
 어느 부서에서도 0
```

한정자를 붙이면 바로 맞는다.

```text
### SQL: SELECT d.name, (SELECT COUNT(*) FROM emp e WHERE e.dept_id = d.id) AS n FROM dept d ORDER BY d.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name  | n                       +-------+------+
-------+---                      | name  | n    |
 sales | 2                       +-------+------+
 dev   | 1                       | sales |    2 |
 hr    | 0                       | dev   |    1 |
(3 rows)                         | hr    |    0 |
                                 +-------+------+
```

★ **이것이 이 주제에서 가장 비싼 사고다.** 문법도 맞고 타입도 맞고 `hr` 의 0 은 **정답이기까지 하다.**\
`sales` 가 2 여야 하는 걸 아는 사람만 틀렸다는 걸 안다.

> **silent failure(무음 실패)** — 에러 없이 틀린 값이 나오는 실패.\
> 예: 사원 수가 `0, 0, 0` 으로 나온 것. 타입도 맞고 값도 그럴듯하다.

**처방 — 상관 서브쿼리 안에서는 모든 열에 한정자를 붙인다.**\
별칭을 쓰는 이유가 짧게 쓰려는 게 아니라는 것이 여기서 드러난다.

---

### 7. 바깥에서 안쪽 별칭 부르기

**에러다. 범위는 한 방향이다.**

```text
### SQL: SELECT e.name FROM emp e WHERE EXISTS (SELECT 1 FROM dept d WHERE d.id = e.dept_id) AND d.name = 'sales';
--- PG 18.6 ---
ERROR:  missing FROM-clause entry for table "d"
LINE 1: ...(SELECT 1 FROM dept d WHERE d.id = e.dept_id) AND d.name = '...
                                                             ^
--- MySQL 8.4.10 ---
ERROR 1054 (42S22) at line 1: Unknown column 'd.name' in 'EXISTS subquery'
```

**왜 그런가**

```text
      바깥 질의  (emp e)
         │
         │  안쪽은 바깥을 본다       ↓ 허용
         ▼
      안쪽 질의  (dept d)
         │
         │  바깥은 안쪽을 못 본다    ↑ 거부
         X
```

안쪽 서브쿼리는 **바깥 행 하나가 정해진 뒤** 계산되므로 바깥 값을 볼 수 있다.\
반대로 바깥은 안쪽이 **몇 번이나 따로따로 돌았는지도 모르므로** 안쪽 별칭에 의미를 줄 수 없다.

[10번](../10-from-clause-aliases-derived-tables/)의 「파생 테이블 안에서 만든 이름은 밖에서 안 보인다」와 **같은 벽**이다.

---

### 8. `ANY` 와 `ALL`

**(A) `bob`·`dan` 2행 · (B) 0행.**

```text
### SQL: SELECT name, salary FROM emp WHERE salary > ANY (SELECT salary FROM emp WHERE dept_id = 10) ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | salary                   +------+--------+
------+--------                  | name | salary |
 bob  |    500                   +------+--------+
 dan  |    400                   | bob  |    500 |
(2 rows)                         | dan  |    400 |
                                 +------+--------+

### SQL: SELECT name, salary FROM emp WHERE salary > ALL (SELECT salary FROM emp WHERE dept_id = 10) ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | salary                   (빈 결과 — 출력이 한 줄도 없다)
------+--------
(0 rows)
```

**왜 그런가** — `sales` 의 급여 목록은 `(300, 500)` 이다.

```text
 목록 = (300, 500)

           > ANY : 하나라도 TRUE 면 TRUE   = "최솟값 300 보다 크면"
           > ALL : 전부 TRUE 여야 TRUE     = "최댓값 500 보다 크면"

 ann 300   300>300 F, 300>500 F   ->  ANY: 탈락   ALL: 탈락
 bob 500   500>300 T, 500>500 F   ->  ANY: 통과   ALL: 탈락   <- 자기 자신에게 막힌다
 cho NULL  UNKNOWN, UNKNOWN       ->  ANY: 탈락   ALL: 탈락
 dan 400   400>300 T, 400>500 F   ->  ANY: 통과   ALL: 탈락
```

★ **`> ALL` 이 0행인 이유는 `bob` 자신이 목록 안에 있기 때문이다.** `500 > 500` 은 `FALSE` 다.\
"최고 급여자"를 뽑으려 했다면 `>= ALL` 이거나 목록에서 자기를 빼야 한다.

---

### 9. 목록에 `NULL` 이 섞이면

**(A) 0행 · (B) 0행. 반대인 두 연산이 같은 답을 냈다 — 그것이 `NULL` 의 지문이다.**

```text
### SQL: SELECT name, salary FROM emp WHERE salary > ANY (SELECT salary FROM emp WHERE dept_id = 20) ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | salary                   (빈 결과 — 출력이 한 줄도 없다)
------+--------
(0 rows)

### SQL: SELECT name, salary FROM emp WHERE salary > ALL (SELECT salary FROM emp WHERE dept_id = 20) ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | salary                   (빈 결과 — 출력이 한 줄도 없다)
------+--------
(0 rows)
```

**왜 그런가** — `dev` 부서의 사원은 `cho` 하나이고 그 급여가 `NULL` 이라, **목록이 `(NULL)` 한 칸짜리**다.

```text
 목록 = (NULL)

 어떤 값 x 에 대해서도   x > NULL  ->  UNKNOWN
                                          ↓
 ANY : "TRUE 가 하나라도 있나?"  -> 없다 (UNKNOWN 뿐)  -> TRUE 아님 -> 탈락
 ALL : "전부 TRUE 인가?"         -> 아니다 (UNKNOWN)   -> TRUE 아님 -> 탈락
                                          ↓
                                  네 행 전부 탈락 — 양쪽 다 0행
```

★ **논리적으로 반대인 두 연산이 같은 답을 내면 세 번째 진릿값이 낀 것이다.**\
이 신호는 진단에 그대로 쓸 수 있다 — `ANY` 와 `ALL` 을 둘 다 돌려 보고 **둘 다 비면** 목록에 `NULL` 이 있다.

이것이 [04번](../04-null-three-valued-logic/)의 `NOT IN` 사고와 **같은 뿌리**다.\
`<> ALL` 이 곧 `NOT IN` 이므로(아래 11번 문항), `NOT IN` 이 0행이 되는 것도 이 절의 특수한 경우다 — 그 정본은 [19번](../19-semi-anti-join/)이다.

**처방 셋** — 목록에서 `NULL` 을 빼거나(`WHERE salary IS NOT NULL`), 그 열에 `NOT NULL` 제약을 걸거나, `EXISTS` 형태로 바꾼다.

---

### 10. 목록이 비어 있으면

**(A) 4행 — 전부 통과한다. (B) 0행. `cho` 는 (A) 에 들어간다.**

```text
### SQL: SELECT name, salary FROM emp WHERE salary > ALL (SELECT salary FROM emp WHERE dept_id = 99) ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | salary                   +------+--------+
------+--------                  | name | salary |
 ann  |    300                   +------+--------+
 bob  |    500                   | ann  |    300 |
 cho  |                          | bob  |    500 |
 dan  |    400                   | cho  |   NULL |
(4 rows)                         | dan  |    400 |
                                 +------+--------+

### SQL: SELECT name, salary FROM emp WHERE salary > ANY (SELECT salary FROM emp WHERE dept_id = 99) ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | salary                   (빈 결과 — 출력이 한 줄도 없다)
------+--------
(0 rows)
```

**왜 그런가**

```text
 목록 = ()  (비어 있다)

 ALL : "전부 TRUE 인가?"  -> 검사할 것이 없다 -> 반례도 없다 -> TRUE
 ANY : "하나라도 TRUE ?"  -> 후보가 없다      -> TRUE 도 없다 -> FALSE
```

★ **`cho` 가 살아남은 것이 이 문항의 핵심이다.**\
`cho.salary` 는 `NULL` 인데도 통과했다 — **비교가 한 번도 일어나지 않았기 때문**이다. 비교할 상대가 없으면 `NULL` 도 걸릴 일이 없다.

**9번과 10번을 나란히 놓으면 이 주제에서 가장 헷갈리는 대비가 나온다.**

```text
 "아무 값도 없어 보이는" 두 목록                  같은 > ALL 의 결과
 ----------------------------------------------   ------------------
 목록 = (NULL)   — 칸은 있는데 값이 없다            0행   <- 9번
 목록 = ()       — 칸 자체가 없다                   4행   <- 10번
                          ↑
            정반대다. "비었다"는 말로 둘을 뭉뚱그리면 반드시 틀린다
```

---

### 11. `IN` 과 `= ANY`

**`IN` 은 `= ANY`, `NOT IN` 은 `<> ALL` 이다. `SOME` 은 `ANY` 의 동의어다.**

```text
 x IN     (목록)   ==   x =  ANY (목록)
 x NOT IN (목록)   ==   x <> ALL (목록)
 ANY               ==   SOME
```

```text
### SQL: SELECT name FROM emp WHERE dept_id = ANY (SELECT id FROM dept) ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name                            +------+
------                           | name |
 ann                             +------+
 bob                             | ann  |
 cho                             | bob  |
(3 rows)                         | cho  |
                                 +------+

### SQL: SELECT name FROM emp WHERE dept_id = SOME (SELECT id FROM dept) ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name                            +------+
------                           | name |
 ann                             +------+
 bob                             | ann  |
 cho                             | bob  |
(3 rows)                         | cho  |
                                 +------+

### SQL: SELECT name FROM emp WHERE dept_id IN (SELECT id FROM dept) ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name                            +------+
------                           | name |
 ann                             +------+
 bob                             | ann  |
 cho                             | bob  |
(3 rows)                         | cho  |
                                 +------+
```

**세 문장이 같은 3행을 준다.** `dan` 은 `dept_id` 가 `NULL` 이라 `NULL = 10/20/30` 이 전부 `UNKNOWN` 이어서 빠졌다.

★ **`NOT IN` 이 `<> ALL` 이라는 사실이 9번과 이어진다.**\
9번에서 본 대로 `ALL` 은 목록에 `NULL` 이 하나라도 있으면 `TRUE` 가 될 수 없다 — 그래서 **`NOT IN` 도 통째로 빈다.**\
`NOT IN` 의 함정 전체는 [19번](../19-semi-anti-join/)이 정본이고, [04번](../04-null-three-valued-logic/)이 그 3값 논리 뿌리다.

---

### 12. `FROM` 안에서 바깥을 참조하면

**통과하지 않는다. `SELECT` 칸에서 되는 이유는 그 자리에는 이미 「바깥 행」이 정해져 있기 때문이다.**

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

**왜 그런가**

```text
 SELECT 칸의 서브쿼리                    FROM 칸의 서브쿼리
 ----------------------------------      ----------------------------------
 FROM 이 이미 행을 만들어 놨다            FROM 항목들은 서로 "형제"다
   -> "지금 처리 중인 바깥 행" 이 있다      -> d 와 t 가 동시에 만들어진다
   -> e.dept_id 를 읽을 수 있다            -> t 를 만들 때 d 의 "현재 행"이 없다
        ↓                                        ↓
      허용                                     거부
```

★ **PG 의 `HINT` 가 답을 문장으로 알려 준다** — "그 표를 참조하려면 이 서브쿼리를 `LATERAL` 로 표시하라."\
MySQL 은 그냥 "모르는 열"이라고만 한다. **같은 벽인데 한쪽만 문을 알려 준다.**

그 문이 [20번 `LATERAL`](../20-lateral-join/)이다. 벽 자체(`FROM` 형제끼리는 서로를 모른다)는 [10번](../10-from-clause-aliases-derived-tables/)이 정본이다.

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| 스칼라 세 결말 (1번) | PG 18.6 · MySQL 8.4.10 | 각 4회 | 0행·1행·2행 + `NULL` 전파 |
| 열 개수 계약 (2번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **에러 메시지가 근거다** (값 자리·`ANY` 자리) |
| 실행 시점 에러 (3번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | 같은 문장이 조건 하나로 갈린다 |
| 상관 서브쿼리 결과 (4번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | |
| 계획의 상관/비상관 (5번) | PG 18.6 · MySQL 8.4.10 | 각 2회 + PG `ANALYZE` 1회 | `loops=4` 가 근거다 |
| 한정자 누락 (6번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **에러 없이 `0,0,0`** — 무음 실패 |
| 별칭 범위 (7번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **에러 메시지가 근거다** |
| `ANY`/`ALL` 기본 (8번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | |
| `NULL` 섞인 목록 (9번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **양쪽 다 0행** |
| 빈 목록 (10번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | `> ALL` 이 `NULL` 급여까지 통과 |
| `IN`=`= ANY`=`SOME` (11번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | 세 문장이 같은 결과 |
| `FROM` 의 상관 참조 (12번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **PG 의 `HINT` 가 근거다** |

**구현 의존 항목** — 5번의 계획 모양뿐이다. `InitPlan`/`SubPlan`·`dependent` 는 **그 엔진의 표기**이고, 실제로 몇 번 도는지는 옵티마이저의 선택이다.\
계획의 추정 행 수는 통계가 없을 때의 기본값이라 **재현되지 않을 수 있다.** 볼 것은 수치가 아니라 모양이다.\
★ **실측이다** — 작성 중 한 번, 제출 전 한 번 같은 서버·같은 버전에서 찍었더니 **MySQL 의 추정 행 수가 `rows=4` → `rows=3` 으로 달라져 있었다.**\
PG 계획은 한 글자도 안 달라졌고, `InitPlan`/`SubPlan` 구분도 두 번 다 같았다. 위에 실은 것은 **재확인 시점의 출력**이다.

**언어 보장 항목** — 1\~4·6\~12번. 1행 1열 계약, 0행의 `NULL`, 이름 해석 순서, `ANY`/`ALL` 의 `NULL`·빈 집합 처리는 전부 결과의 정의다.\
**방언이 갈리는 항목** — **없다.** 이 주제에서 던진 모든 문이 두 엔진에서 같은 성패·같은 결과를 냈고, 다른 것은 **에러 문구**뿐이다.\
단 **`FROM` 안의 상관 참조(12번)는 에러 문구의 질이 크게 다르다** — PG 만 `LATERAL` 을 알려 준다.

**순서 보장** — 없다. 위 출력에 `ORDER BY` 를 붙인 것은 그 때문이다.
