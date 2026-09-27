# sql/17-SELF JOIN — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력은 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 에러 메시지도 실제로 받은 것이고, 지어낸 출력은 없다.\
> 6~9번의 `staff` 는 **기존 `emp` 에서 만들어** 트랜잭션 안에서 쓰고 롤백했다(MySQL 은 `CREATE` → 질의 → `DROP`).\
> **`emp`·`dept` 는 한 행도 바꾸지 않았다.**\
> 문서 근거는 [PG 18 Table Expressions](https://www.postgresql.org/docs/18/queries-table-expressions.html) · [MySQL 8.4 JOIN Clause](https://dev.mysql.com/doc/refman/8.4/en/join.html).

<details>
<summary>staff 를 만드는 문 (6~9번에서만 쓴다)</summary>

```sql
-- PostgreSQL: 트랜잭션 안에서 만들고 롤백
BEGIN;
CREATE TABLE staff (id int PRIMARY KEY, name text, dept_id int, salary int, mgr_id int);
INSERT INTO staff (id, name, dept_id, salary, mgr_id)
SELECT e.id, e.name, e.dept_id, e.salary, v.mgr
FROM emp e JOIN (VALUES (1,NULL::int),(2,1),(3,1),(4,2)) AS v(id,mgr) ON v.id = e.id;
-- 질의들
ROLLBACK;
```

```sql
-- MySQL: DDL 에 트랜잭션이 안 걸리므로 CREATE -> 질의 -> DROP
CREATE TABLE staff (id int PRIMARY KEY, name varchar(20), dept_id int, salary int, mgr_id int);
INSERT INTO staff (id, name, dept_id, salary, mgr_id)
SELECT e.id, e.name, e.dept_id, e.salary, v.mgr
FROM emp e JOIN (SELECT 1 AS id, NULL AS mgr UNION ALL SELECT 2,1
                 UNION ALL SELECT 3,1 UNION ALL SELECT 4,2) AS v ON v.id = e.id;
-- 질의들
DROP TABLE staff;
```

`VALUES (…),(…)` 행 생성자를 MySQL 이 거부하므로 `UNION ALL` 목록으로 바꿨다([10번](../10-from-clause-aliases-derived-tables/)).\
두 DB 모두 실험 뒤 표가 남아 있지 않다.

</details>

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. 별칭 없이 같은 표를 두 번

**두 엔진 다 에러다.**

```text
### SQL: SELECT * FROM emp JOIN emp ON emp.id = emp.id;
--- PG 18.6 ---
ERROR:  table name "emp" specified more than once
--- MySQL 8.4.10 ---
ERROR 1066 (42000) at line 1: Not unique table/alias: 'emp'
```

쉼표 표기도 같다 — 이 결과는 [10번](../10-from-clause-aliases-derived-tables/)에서 이미 나왔다.

```text
### SQL: SELECT * FROM emp, emp;
--- PG 18.6 ---
ERROR:  table name "emp" specified more than once
--- MySQL 8.4.10 ---
ERROR 1066 (42000) at line 1: Not unique table/alias: 'emp'
```

**왜 그런가** — 별칭을 붙이면 통과한다. **막힌 것은 조인이 아니라 이름이다.**

```text
### SQL: SELECT e.name, m.name FROM staff e JOIN staff m ON e.mgr_id = m.id ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | name                     +------+------+
------+------                    | name | name |
 bob  | ann                      +------+------+
 cho  | ann                      | bob  | ann  |
 dan  | bob                      | cho  | ann  |
(3 rows)                         | dan  | bob  |
                                 +------+------+
```

★ **`SELF JOIN` 을 막는 것은 아무것도 없다.** 같은 표를 두 번 여는 것 자체는 허용되고, **이름이 하나뿐인 것**만 막힌다.

---

### 2. 막는 이유

**「한 이름에 두 대상을 넣을 수 없다」다. 중복이라서가 아니다.**

```text
 FROM emp JOIN emp ON emp.id = emp.id
                         ↑        ↑
                         └────────┴── 이 emp 는 왼쪽인가 오른쪽인가?
                                      답할 방법이 없다
```

**MySQL 의 문구가 이유를 정확히 말한다** — `Not unique table/alias`. "중복"이 아니라 **"유일하지 않다"** 다.

```text
 만약 허용했다면                        허용하지 않으니
 emp.id 가 어느 쪽인지 모른다             별칭을 강제한다
 ON 조건을 쓸 방법이 없다                 a.id / b.id 로 정확히 가리킨다
        ↓                                        ↓
 질의가 뜻을 못 가진다                    질의가 뜻을 가진다
```

`FROM` 은 **이름 공간을 만드는 칸**이고, 그 칸에서는 이름이 유일해야 한다([10번](../10-from-clause-aliases-derived-tables/)).\
**별칭은 편의가 아니라 `SELF JOIN` 의 전제 조건이다.**

★ 이 에러는 **시끄럽다** — 이 주제에서 조용히 지나가는 사고는 별칭이 아니라 4·5·9번의 `ON`·집계 쪽에서 난다.

---

### 3. 짝의 개수

**16 이다. 4 × 4 다.**

```text
### SQL: SELECT COUNT(*) AS n FROM emp a CROSS JOIN emp b;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 n                               +----+
----                             | n  |
 16                              +----+
(1 row)                          | 16 |
                                 +----+
```

**왜 그런가** — `SELF JOIN` 도 [12번](../12-cartesian-product-cross-join/)의 카티션곱에서 시작한다. 다른 표가 아니라 **같은 표를 두 번** 놓았을 뿐이다.

```text
 a\b    ann   bob   cho   dan
 ann     1     2     3     4
 bob     5     6     7     8        4 x 4 = 16
 cho     9    10    11    12
 dan    13    14    15    16
```

★ **행 수가 제곱으로 는다는 것이 `SELF JOIN` 의 유일한 고유 비용이다.**\
`emp` 가 1만 행이면 1억 짝이다. **`ON` 이 먼저 좁혀 주지 않으면 이 곱이 그대로 실행된다.**

---

### 4. `<>` 와 `<`

**(A) 2행 · (B) 1행. `<>` 는 같은 쌍을 순서만 바꿔 두 번 준다.**

```text
### SQL: SELECT a.name, b.name FROM emp a JOIN emp b
         ON a.dept_id = b.dept_id AND a.id <> b.id ORDER BY a.id, b.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | name                     +------+------+
------+------                    | name | name |
 ann  | bob                      +------+------+
 bob  | ann                      | ann  | bob  |
(2 rows)                         | bob  | ann  |
                                 +------+------+

### SQL: SELECT a.name, b.name FROM emp a JOIN emp b
         ON a.dept_id = b.dept_id AND a.id < b.id ORDER BY a.id, b.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | name                     +------+------+
------+------                    | name | name |
 ann  | bob                      +------+------+
(1 row)                          | ann  | bob  |
                                 +------+------+
```

**왜 그런가**

```text
 같은 부서(10)인 짝은 넷이다
   (ann,ann)  (ann,bob)  (bob,ann)  (bob,bob)

 a.id <> b.id  ->  자기 짝 둘만 막는다        남는 것: (ann,bob) (bob,ann)   2행
 a.id <  b.id  ->  자기 짝 + 뒤집힌 짝을 막는다  남는 것: (ann,bob)            1행
                      ↑
       a 쪽이 언제나 작은 id 라서 순서까지 고정된다
```

| 조건 | 자기 짝 | `(ann,bob)` | `(bob,ann)` | 행 수 |
|---|---|---|---|---|
| 없음 | 들어온다 | O | O | 5 (아래 5번) |
| `a.id <> b.id` | 막는다 | O | O | **2** |
| `a.id < b.id` | 막는다 | O | X | **1** |

★ **어느 쪽이 옳은지는 요구사항이 정한다.**

- "각 사원에게 동료 목록을 보여 준다" → **`<>`**. `ann` 의 줄과 `bob` 의 줄이 둘 다 필요하다.
- "겹치는 쌍의 목록을 뽑는다" → **`<`**. 같은 쌍을 두 번 보고하면 건수가 두 배가 된다.

**`<>` 로 쓰고 나중에 건수를 세는 것**이 이 주제에서 가장 흔한 조용한 사고다 — 에러가 없고 값만 두 배다.

---

### 5. 조건을 아예 빼면

**자기 자신과의 짝이 섞여 들어온다. 5행이 된다.**

```text
### SQL: SELECT a.name, b.name FROM emp a JOIN emp b ON a.dept_id = b.dept_id ORDER BY a.id, b.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | name                     +------+------+
------+------                    | name | name |
 ann  | ann                      +------+------+
 ann  | bob                      | ann  | ann  |
 bob  | ann                      | ann  | bob  |
 bob  | bob                      | bob  | ann  |
 cho  | cho                      | bob  | bob  |
(5 rows)                         | cho  | cho  |
                                 +------+------+
```

**왜 그런가**

```text
 ann-ann  : 자기 부서는 언제나 자기 부서와 같다 -> TRUE
 bob-bob  : 〃
 cho-cho  : 〃 (dev 에 혼자 있어도 자기와는 붙는다)
 dan-dan  : dept_id 가 NULL 이라 NULL = NULL -> UNKNOWN -> 탈락   <- 예외
```

★ **`dan` 은 자기 자신과도 안 붙는다.** `NULL = NULL` 조차 `UNKNOWN` 이기 때문이다([04번](../04-null-three-valued-logic/)).\
"자기 짝이 반드시 들어온다"는 직관도 `NULL` 앞에서는 깨진다.

**「동료 목록」을 뽑았다면 세 줄이 잘못 들어온 것이고, 에러는 없다.**\
`cho` 는 동료가 없는데 **자기 자신이 동료로 잡혀** 있다. 이것이 5번의 요점이다.

---

### 6. 상사 붙이기

**3행이다. `ann` 이 없다.**

```text
### SQL: SELECT e.name AS emp, m.name AS mgr FROM staff e JOIN staff m ON e.mgr_id = m.id ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | mgr                       +------+------+
-----+-----                      | emp  | mgr  |
 bob | ann                       +------+------+
 cho | ann                       | bob  | ann  |
 dan | bob                       | cho  | ann  |
(3 rows)                         | dan  | bob  |
                                 +------+------+
```

**왜 그런가**

```text
 e 쪽 (부하)   e.mgr_id   ON e.mgr_id = m.id      처분
 -----------   --------   ---------------------   ----------------
 ann           NULL       NULL = 1/2/3/4  UNKNOWN 버림   <- 꼭대기가 사라진다
 bob           1          1 = 1           TRUE    남김 (mgr = ann)
 cho           1          1 = 1           TRUE    남김 (mgr = ann)
 dan           2          2 = 2           TRUE    남김 (mgr = bob)
```

★ **사라진 행이 하필 꼭대기다.** 조직도에서 가장 중요한 행이 **조용히** 빠진다.\
[13번](../13-inner-join/)에서 `dan` 이 사라진 것과 **완전히 같은 원리**다 — 내부 조인은 `UNKNOWN` 을 `FALSE` 처럼 버린다.

---

### 7. 되살리는 방법

**`LEFT JOIN` 으로 바꾼다. 계층에서 꼭대기의 부모는 언제나 `NULL` 이므로 이 형태가 기본이다.**

```text
### SQL: SELECT e.name AS emp, m.name AS mgr FROM staff e LEFT JOIN staff m ON e.mgr_id = m.id ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | mgr                       +------+------+
-----+-----                      | emp  | mgr  |
 ann |                           +------+------+
 bob | ann                       | ann  | NULL |
 cho | ann                       | bob  | ann  |
 dan | bob                       | cho  | ann  |
(4 rows)                         | dan  | bob  |
                                 +------+------+
```

```text
 INNER JOIN 으로 계층 조회            LEFT JOIN 으로 계층 조회
 +------------------------+          +------------------------+
 | bob | ann              |          | ann | NULL             |  <- 꼭대기가 남는다
 | cho | ann              |          | bob | ann              |
 | dan | bob              |          | cho | ann              |
 +------------------------+          | dan | bob              |
   3행 — 꼭대기가 없다                +------------------------+
                                       4행 — 전원이 있다
```

**왜 계층은 거의 항상 `LEFT` 인가** — 계층에는 **정의상 부모가 없는 행이 하나 이상** 있다.\
그 행의 자기 참조 열은 `NULL` 이고, `NULL = m.id` 는 언제나 `UNKNOWN` 이다.\
즉 **`INNER JOIN` 을 쓰면 꼭대기를 잃는 것이 규칙**이지 예외가 아니다([14번](../14-left-right-outer-join/)).

★ 그래서 "사원 수가 하나 모자란다"는 신고가 들어오면 **계층 조인의 `INNER` 를 먼저 본다.**

---

### 8. 두 단계 위

**`dan` 하나뿐이다. 한계는 「깊이만큼 별칭이 필요하다」다.**

```text
### SQL: SELECT e.name AS emp, m.name AS mgr, g.name AS grand FROM staff e
         LEFT JOIN staff m ON e.mgr_id = m.id
         LEFT JOIN staff g ON m.mgr_id = g.id ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | mgr | grand               +------+------+-------+
-----+-----+-------              | emp  | mgr  | grand |
 ann |     |                     +------+------+-------+
 bob | ann |                     | ann  | NULL | NULL  |
 cho | ann |                     | bob  | ann  | NULL  |
 dan | bob | ann                 | cho  | ann  | NULL  |
(4 rows)                         | dan  | bob  | ann   |
                                 +------+------+-------+
```

**왜 그런가** — 트리에서 두 단계 위가 있는 행은 `dan` 뿐이다.

```text
        ann (1)          깊이 0
        /     \
     bob (2)  cho (3)    깊이 1  -> grand 는 NULL (ann 의 상사가 없다)
      /
   dan (4)               깊이 2  -> grand = ann
```

**한계**

```text
 별칭 하나 = 계층 한 단계
   e            본인
   e, m         + 상사
   e, m, g      + 상사의 상사
   e, m, g, x   + 그 위 … 계속 적어야 한다
                     ↑
   질의를 쓰는 시점에 깊이가 정해져 있어야 한다
```

★ **깊이가 미지수면 `SELF JOIN` 으로는 못 푼다.** 조직이 한 단 깊어지면 질의를 고쳐야 한다.\
그때 쓰는 것이 **재귀 CTE**([목록의 **33번 주제**](../33-recursive-cte/))다.\
**경계: 여기는 깊이가 고정일 때까지, 33번은 깊이가 미지수일 때부터.**

---

### 9. 부하 수 세기

**안 된다. `COUNT(*)` 는 부하가 없는 사람에게 1 을 준다. `COUNT(부하쪽 열)` 로 바꾼다.**

```text
### SQL: SELECT m.name AS mgr, COUNT(*) AS reports FROM staff m
         LEFT JOIN staff e ON e.mgr_id = m.id GROUP BY m.id, m.name ORDER BY m.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 mgr | reports                   +------+---------+
-----+---------                  | mgr  | reports |
 ann |       2                   +------+---------+
 bob |       1                   | ann  |       2 |
 cho |       1                   | bob  |       1 |
 dan |       1                   | cho  |       1 |
(4 rows)                         | dan  |       1 |
                                 +------+---------+

### SQL: SELECT m.name AS mgr, COUNT(e.id) AS reports FROM staff m
         LEFT JOIN staff e ON e.mgr_id = m.id GROUP BY m.id, m.name ORDER BY m.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 mgr | reports                   +------+---------+
-----+---------                  | mgr  | reports |
 ann |       2                   +------+---------+
 bob |       1                   | ann  |       2 |
 cho |       0                   | bob  |       1 |
 dan |       0                   | cho  |       0 |
(4 rows)                         | dan  |       0 |
                                 +------+---------+
```

**왜 그런가**

```text
 LEFT JOIN 이 남긴 cho 의 행
   m 쪽: cho          e 쪽: (전부 NULL)
                              ↓
   COUNT(*)      행을 센다      -> 1     <- 행은 있다
   COUNT(e.id)   NULL 은 안 센다 -> 0     <- 부하는 없다
```

★ **`COUNT(*)` 와 `COUNT(열)` 의 차이가 여기서 정확히 드러난다.**\
`LEFT JOIN` 뒤에는 **「행이 있다」와 「짝이 있다」가 다르다.** `COUNT(*)` 는 앞을 세고 `COUNT(열)` 은 뒤를 센다.

**에러가 안 난다.** `cho | 1` 은 "부하가 한 명 있구나"로 읽히고, 그 부하가 누구인지는 아무도 안 물어본다.\
`COUNT` 세 형태의 정본은 [21번](../21-aggregate-functions-count-forms/)다. **여기서 인출할 것은 「`LEFT JOIN` 뒤의 `COUNT(*)` 는 0 을 못 만든다」 하나다.**

---

### 10. 연속 행 비교

**2행이다. `bob` 은 위가 없어서, `cho` 는 급여가 `NULL` 이라 `lower` 칸에 없다.**

```text
### SQL: SELECT a.name AS lower, b.name AS higher, b.salary - a.salary AS gap
         FROM emp a JOIN emp b ON b.salary = (SELECT MIN(x.salary) FROM emp x WHERE x.salary > a.salary)
         ORDER BY a.salary;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 lower | higher | gap             +-------+--------+------+
-------+--------+-----            | lower | higher | gap  |
 ann   | dan    | 100             +-------+--------+------+
 dan   | bob    | 100             | ann   | dan    |  100 |
(2 rows)                          | dan   | bob    |  100 |
                                  +-------+--------+------+
```

**왜 그런가**

```text
 a 쪽       a.salary   (SELECT MIN(x.salary) WHERE x.salary > a.salary)   b 로 붙는 행
 --------   --------   ------------------------------------------------   ------------
 ann          300      400                                                dan
 dan          400      500                                                bob
 bob          500      (0행) -> NULL     b.salary = NULL 은 UNKNOWN       없음
 cho          NULL     x.salary > NULL 이 전부 UNKNOWN -> 0행 -> NULL     없음
```

**두 탈락이 서로 다른 이유라는 점이 중요하다.**

```text
 bob 이 빠진 이유                     cho 가 빠진 이유
 "자기보다 큰 값이 없다"                "비교 자체가 성립하지 않는다"
   -> 사다리의 맨 위라서 정상            -> 데이터가 없어서 (사고일 수 있다)
        ↑                                      ↑
      둘 다 결과에서는 똑같이 "없음"으로 보인다
```

★ **결과만 보면 둘을 구분할 수 없다.** 급여가 `NULL` 인 사원이 사다리에서 통째로 빠졌다는 것을 아무도 모른다.\
서브쿼리가 0행이면 `NULL` 이 되는 규칙은 [11번](../11-subquery-scalar-correlated-any-all/)이 정본이다.

이 질의는 **`a` 행마다 서브쿼리가 한 번씩 돈다.** 4행이라 괜찮지만 행이 많아지면 그대로 곱해진다.

---

### 11. 더 싼 방법

**윈도우 함수 `LAG`/`LEAD` 다. 표를 한 번만 훑는다.**

```text
 SELF JOIN 으로 이웃 찾기                 LAG/LEAD 로 이웃 찾기
 +--------------------------------+      +--------------------------------+
 | 표를 두 번 열고                |      | 표를 한 번 정렬해 훑으면서     |
 | a 행마다 "바로 위"를 찾는다    |      | 앞·뒤 행의 값을 바로 집는다    |
 +--------------------------------+      +--------------------------------+
   a 행마다 탐색이 붙는다                  한 번의 정렬로 끝난다
```

★ **이 주제에서 인출할 것은 「이웃 비교를 `SELF JOIN` 으로 쓸 수 있다」와 「그게 최선은 아니다」 둘이다.**

**경계** — `LAG`/`LEAD` 의 문법·프레임·`NULL` 처리는 [목록의 **30번 주제**](../30-offset-and-boundary-functions/)가 정본이다.\
**여기는 「같은 표를 두 별칭으로 여는 형태」까지, 30번은 「한 번 훑으며 이웃을 보는 함수」부터.**

`SELF JOIN` 이 여전히 맞는 자리도 있다.

| 요구 | 무엇을 쓰나 |
|---|---|
| 바로 앞·뒤 한 행 | `LAG`/`LEAD` (30번) |
| 조건에 맞는 다른 행 **전부** (동료 목록·겹친 예약) | `SELF JOIN` |
| 부모·조부모 (깊이 고정) | `SELF JOIN` |
| 조상 전체 (깊이 미지수) | 재귀 CTE (33번) |

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| 별칭 없는 자체 조인 (1·2번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | `JOIN`·쉼표 표기 + 별칭 붙인 정상형. **에러 메시지가 근거다** |
| 자체 카티션곱 개수 (3번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 16 |
| `<>` 대 `<` (4번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | 2행 대 1행 |
| 조건 없는 짝짓기 (5번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **`dan` 이 자기와도 안 붙는 것**이 근거다 |
| 상사 조인 `INNER` (6번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `staff` — 트랜잭션 롤백 / `DROP` |
| 상사 조인 `LEFT` (7번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 〃 |
| 두 단계 (8번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 〃 |
| `COUNT(*)` 대 `COUNT(열)` (9번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | 〃 · **1 대 0 이 근거다** |
| 연속 행 비교 (10번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `emp` 만 |
| `staff` 잔재 확인 | PG 18.6 · MySQL 8.4.10 | 각 1회 | `\dt` · `SHOW TABLES` 로 `emp`·`dept` 만 남은 것 확인 |

**구현 의존 항목** — 없다. 이 주제의 모든 결과는 결과의 정의에서 나온다.\
**방언이 갈리는 항목** — **없다.** 모든 문이 두 엔진에서 같은 성패·같은 결과를 냈고, 다른 것은 **에러 문구**뿐이다.\
목록 README 의 `17 … 표준` 표기는 **실행으로 확인됐다.**

**순서 보장** — 없다. 위 출력에 `ORDER BY` 를 붙인 것은 그 때문이다.\
**`emp`·`dept` 변경** — 없다. `staff` 만 만들었고 실험 뒤 남아 있지 않다.

**11번은 문서 대조로만 답했다** — `LAG`/`LEAD` 를 여기서 돌려 보지 않았다. 그 검증은 **30번 주제의 몫**이다.
