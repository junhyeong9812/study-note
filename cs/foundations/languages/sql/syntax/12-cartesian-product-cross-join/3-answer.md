# sql/12-카티션곱과 CROSS JOIN — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력은 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 에러 메시지도 실행 계획도 실제로 받은 것이고, 지어낸 출력은 없다.\
> 문서 근거는 [PG 18 Table Expressions](https://www.postgresql.org/docs/18/queries-table-expressions.html) · [MySQL 8.4 JOIN Clause](https://dev.mysql.com/doc/refman/8.4/en/join.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. `SELECT COUNT(*) FROM emp CROSS JOIN dept;` 의 결과

**12 다. 4 × 3 = 12 — 더하기가 아니라 곱하기다.**

```text
### SQL: SELECT COUNT(*) AS rows_cross FROM emp CROSS JOIN dept;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 rows_cross                      +------------+
------------                     | rows_cross |
         12                      +------------+
(1 row)                          |         12 |
                                 +------------+
```

12행을 눈으로 보면 이렇다 — **왼쪽 행마다 오른쪽 전부가 붙는다.**

```text
### SQL: SELECT e.name AS emp, d.name AS dept FROM emp e CROSS JOIN dept d ORDER BY e.id, d.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | dept                      +-----+-------+
-----+-------                    | emp | dept  |
 ann | sales                     +-----+-------+
 ann | dev                       | ann | sales |
 ann | hr                        | ann | dev   |
 bob | sales                     | ann | hr    |
 bob | dev                       | bob | sales |
 bob | hr                        | bob | dev   |
 cho | sales                     | bob | hr    |
 cho | dev                       | cho | sales |
 cho | hr                        | cho | dev   |
 dan | sales                     | cho | hr    |
 dan | dev                       | dan | sales |
 dan | hr                        | dan | dev   |
(12 rows)                        | dan | hr    |
                                 +-----+-------+
```

★ **이 12가 조인 네 형태 전부의 출발선이다.** 13번(3행)·14번(4행)·16번(5행)이 여기서 갈라진다(11번 답).

---

### 2. `dan` 의 행이 몇 개 들어 있나

**3개다.** `dan-sales`·`dan-dev`·`dan-hr` 이 전부 있다.

```text
카티션곱은 값을 보지 않는다

 dan.dept_id = NULL
       ↓
 "NULL 이니까 짝이 없다" -> 아니다
       ↓
 dan x sales,  dan x dev,  dan x hr   <- 조건이 없으므로 전부 만들어진다
```

**`NULL` 이 문제가 되는 것은 `ON` 부터다.** `ON e.dept_id = d.id` 를 걸면 `NULL = 10` 이 `UNKNOWN` 이라 `dan` 의 세 행이 전부 떨어진다([04번](../04-null-three-valued-logic/)).

```text
카티션곱 12행              ON e.dept_id = d.id            남는 것
 ann x sales               10 = 10  TRUE                  O
 ann x dev                 10 = 20  FALSE                 X
 ann x hr                  10 = 30  FALSE                 X
 bob x sales               10 = 10  TRUE                  O
 bob x dev/hr              FALSE                          X
 cho x dev                 20 = 20  TRUE                  O
 cho x sales/hr            FALSE                          X
 dan x sales/dev/hr        NULL = ?  UNKNOWN              X  <- 세 행 전부
                                                          ----
                                                          3행
```

그래서 [13번](../13-inner-join/)에서 `dan` 이 통째로 사라지고, [14번](../14-left-right-outer-join/)에서 `NULL` 로 되살아난다.

---

### 3. 쉼표와 `CROSS JOIN` 은 같은가, 그럼에도 (B)로 적는 이유

**결과는 같다. 그래도 (B)로 적는 이유는 「일부러 그랬다」를 남기기 위해서다.**

```text
### SQL: SELECT COUNT(*) AS rows_comma FROM emp, dept;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 rows_comma                      +------------+
------------                     | rows_comma |
         12                      +------------+
(1 row)                          |         12 |
                                 +------------+
```

12행으로 똑같다.

```text
FROM emp, dept                        FROM emp CROSS JOIN dept
  "표를 둘 적었다"처럼 보인다            "모든 짝을 만들었다"고 읽힌다
        ↓                                       ↓
 12행이 나왔을 때                       12행이 나왔을 때
 의도인지 사고인지 모른다                의도라고 알 수 있다
```

**이것이 표기법이 하는 일의 전부다.** 결과에 차이가 없으니 순전히 **읽는 사람을 위한 선택**이다.\
그리고 실무에서 카티션곱은 **거의 항상 사고**이므로, 의도를 표시할 수단이 있으면 반드시 쓴다.

조건이 있는 조인에도 같은 논리가 적용된다 — 쉼표 + `WHERE` 대신 `JOIN … ON` 을 쓰면 **조인 조건과 필터 조건이 눈으로 분리된다.**\
그 분리가 결과까지 바꾸는 자리가 [15번](../15-on-vs-where-in-outer-join/)이다.

---

### 4. `FROM emp e, dept d, dept d2 WHERE e.dept_id = d.id` 의 행 수

**9 다.**

```text
### SQL: SELECT COUNT(*) AS n FROM emp e, dept d, dept d2 WHERE e.dept_id = d.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 n                               +---+
---                              | n |
 9                               +---+
(1 row)                          | 9 |
                                 +---+
```

**왜 그런가** — `e` 와 `d` 는 조건으로 3행까지 좁혀졌는데, `d2` 에는 조건이 **하나도 없다.**

```text
 e x d  (조건 있음)      x    d2 (조건 없음)
      3행                 x       3행          =  9행
        ↑                         ↑
   ann-sales             sales, dev, hr 가
   bob-sales             각 행마다 통째로 붙는다
   cho-dev
```

```text
### SQL: SELECT COUNT(*) FROM emp e, dept d WHERE e.dept_id = d.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 count                           +----------+
-------                          | COUNT(*) |
     3                           +----------+
(1 row)                          |        3 |
                                 +----------+
```

3행 → 9행. **조건 하나가 빠지자 그 표의 행 수(3)만큼 곱해졌다.**

> **규칙** — 표 N개를 붙이려면 조인 조건이 **N−1개** 필요하다. 표 3개면 조건 2개.\
> 조건 개수를 세는 것이 카티션곱 사고를 잡는 가장 빠른 방법이다.

★ **이 사고가 무서운 것은 에러가 안 나기 때문이다.** 9행은 멀쩡한 결과처럼 보이고, `SUM` 을 씌우면 **세 배 부풀려진 숫자**가 조용히 나온다.

---

### 5. `CROSS JOIN … ON` — 두 엔진에서 각각

**PG 18.6 은 구문 오류, MySQL 8.4.10 은 `INNER JOIN` 처럼 3행을 준다.**

```text
### SQL: SELECT e.name, d.name FROM emp e CROSS JOIN dept d ON e.dept_id = d.id;
--- PG 18.6 ---
ERROR:  syntax error at or near "ON"
LINE 1: ...ELECT e.name, d.name FROM emp e CROSS JOIN dept d ON e.dept_...
                                                             ^
--- MySQL 8.4.10 ---
+------+-------+
| name | name  |
+------+-------+
| ann  | sales |
| bob  | sales |
| cho  | dev   |
+------+-------+
```

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| `CROSS JOIN … ON …` | **✗ 구문 오류** — 파서가 `ON` 을 받지 않는다 | **✓ 3행** — 내부 조인이 된다 |

**왜 다른가** — [MySQL 8.4 JOIN 페이지](https://dev.mysql.com/doc/refman/8.4/en/join.html)는 `JOIN`·`INNER JOIN`·`CROSS JOIN` 을 **문법적 동의어**로 다룬다.\
PG 는 `CROSS JOIN` 을 「조건 없는 조인」으로 못 박아, 조건이 붙는 것 자체를 문법으로 막는다.

```text
PG 의 문법 나무                    MySQL 의 문법 나무
 CROSS JOIN  ─ (조건 없음)          JOIN       ┐
 JOIN ... ON ─ (조건 있음)          INNER JOIN ├─ 전부 같은 것
                                    CROSS JOIN ┘   ON 이 있어도 되고 없어도 된다
```

**깨지는 방향이 한쪽뿐이다.**

```text
MySQL 에서 쓴 CROSS JOIN ... ON 을 PG 로     PG 에서 쓴 질의를 MySQL 로
              │                                       │
              ▼                                       ▼
        구문 오류로 깨진다                        깨지지 않는다
```

★ **조건이 있으면 `JOIN … ON` 이라고 적는다.** `CROSS JOIN` 은 조건이 **없을 때만** 쓰는 말로 두면 양쪽에서 돈다.\
반대 방향 사고(`JOIN` 에 `ON` 을 빠뜨리는 것)는 [13번](../13-inner-join/)에 있다.

---

### 6. 「실적 없는 구간이 보고서에서 빠지는」 문제를 어떻게 고치나

**`CROSS JOIN` 으로 뼈대를 먼저 만들고, 거기에 실적을 `LEFT JOIN` 으로 붙인다.**

```text
(전) 실적 표만 읽는다                    (후) 뼈대에 실적을 붙인다
 sales Q1  100                          sales Q1  100
 dev   Q2  200                          sales Q2    0   <- 행이 생겼다
                                        dev   Q1    0   <- 행이 생겼다
  2행 — 나머지는 "행 자체가 없다"          dev   Q2  200
                                        hr    Q1    0   <- hr 이 통째로 보인다
                                        hr    Q2    0
                                         6행 = 3부서 x 2분기
```

```text
### SQL: SELECT s.dept, s.q, COALESCE(r.amt, 0) AS amt
         FROM (SELECT d.id AS did, d.name AS dept, q.q
               FROM dept d CROSS JOIN (SELECT 1 AS q UNION ALL SELECT 2) AS q) AS s
         LEFT JOIN (SELECT 10 AS did, 1 AS q, 100 AS amt UNION ALL SELECT 20, 2, 200) AS r
           ON r.did = s.did AND r.q = s.q
         ORDER BY s.did, s.q;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept  | q | amt                 +-------+---+-----+
-------+---+-----                | dept  | q | amt |
 sales | 1 | 100                 +-------+---+-----+
 sales | 2 |   0                 | sales | 1 | 100 |
 dev   | 1 |   0                 | sales | 2 |   0 |
 dev   | 2 | 200                 | dev   | 1 |   0 |
 hr    | 1 |   0                 | dev   | 2 | 200 |
 hr    | 2 |   0                 | hr    | 1 |   0 |
(6 rows)                         | hr    | 2 |   0 |
                                 +-------+---+-----+
```

**세 부품이 각각 하는 일.**

```text
CROSS JOIN   부서 3 x 분기 2 = 6행짜리 뼈대를 만든다        <- 이 주제
LEFT JOIN    뼈대를 다 남기고 실적을 붙인다                 <- 14번
COALESCE     붙지 않은 칸의 NULL 을 0 으로 바꾼다           <- 목록의 06번 주제
```

**뼈대가 없으면 `LEFT JOIN` 도 못 구한다.** 「실적 표에 아예 없는 분기」는 어느 쪽 표에도 행이 없으므로 조인으로는 만들어지지 않는다.\
없는 행을 만들어 낼 수 있는 것은 **곱하기뿐**이다 — 이것이 `CROSS JOIN` 의 첫 번째 정당한 용도다.

비용 — 뼈대 행 수가 결과 행 수의 하한이다. 부서 1,000개 × 365일이면 **36만 5천 행이 항상** 만들어진다.

---

### 7. `generate_series` 는 두 엔진에서 다 도는가

**아니다. PostgreSQL 에만 있다.**

```text
### SQL: SELECT d.name AS dept, m AS month FROM dept d CROSS JOIN generate_series(1,3) AS m ORDER BY d.id, m;
--- PG 18.6 ---
 dept  | month 
-------+-------
 sales |     1
 sales |     2
 sales |     3
 dev   |     1
 dev   |     2
 dev   |     3
 hr    |     1
 hr    |     2
 hr    |     3
(9 rows)
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that
  corresponds to your MySQL server version for the right syntax to use near '(1,3) AS m' at line 1
```

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| `generate_series(1,3)` | ✓ 3행 | **✗ `ERROR 1064`** |

에러가 `1064`(문법 오류)라는 점이 말해 주는 것 — MySQL 파서에게 `generate_series` 는 **모르는 함수 이름**이다.

**MySQL 에서 수 목록을 만드는 두 가지 방법.**

```sql
-- (1) UNION ALL 목록 — 양쪽 엔진에서 다 돈다. 짧으면 이게 제일 읽기 쉽다
SELECT 1 AS q UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4

-- (2) 재귀 CTE — 길이가 가변이면 이쪽. 목록의 33번 주제가 정본이다
```

`VALUES` 리스트로 만들려 하면 **행 생성자 문법까지 갈린다** — PG 는 `(1),(2)`, MySQL 은 `ROW(1),ROW(2)` 다([10번](../10-from-clause-aliases-derived-tables/)).

---

### 8. `a.id < b.id` 와 `a.id <> b.id` 의 결과

**`<` 는 6, `<>` 는 12 다.**

```text
### SQL: SELECT a.name AS x, b.name AS y FROM emp a CROSS JOIN emp b WHERE a.id < b.id ORDER BY a.id, b.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
  x  |  y                        +-----+-----+
-----+-----                      | x   | y   |
 ann | bob                       +-----+-----+
 ann | cho                       | ann | bob |
 ann | dan                       | ann | cho |
 bob | cho                       | ann | dan |
 bob | dan                       | bob | cho |
 cho | dan                       | bob | dan |
(6 rows)                         | cho | dan |
                                 +-----+-----+

### SQL: SELECT COUNT(*) AS n FROM emp a CROSS JOIN emp b WHERE a.id <> b.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 n                               +----+
----                             | n  |
 12                              +----+
(1 row)                          | 12 |
                                 +----+
```

**왜 다른가** — 두 조건이 빼는 것이 다르다.

```text
4 x 4 = 16 쌍

 <>  :  자기 자신과의 짝 4개만 뺀다              16 - 4 = 12
        ann-bob 과 bob-ann 이 둘 다 남는다

 <   :  자기 짝 4개를 빼고, 순서만 다른 쌍도      (16 - 4) / 2 = 6
        하나씩만 남긴다
```

```text
     b→   ann  bob  cho  dan
 a↓
 ann       .    O    O    O        O = a.id < b.id 로 남는 6칸
 bob       x    .    O    O        x = <> 로는 남지만 < 로는 빠지는 6칸
 cho       x    x    .    O        . = 자기 짝 4칸 (둘 다 뺀다)
 dan       x    x    x    .
```

★ **"중복 없이 모든 쌍"이 필요하면 `<` 를 쓴다.** `<>` 는 같은 쌍을 두 번 세어 집계를 정확히 두 배로 만든다.\
비용은 **N²** 이다. 1,000행이면 100만 쌍 — 조합을 만들기 전에 **먼저 좁힌다.**

---

### 9. 한 행짜리 표를 곱하면 — 행 수와 `avg_sal`

**행 수는 4행 그대로이고, `avg_sal` 은 400 이다.**

```text
### SQL: SELECT e.name, e.salary, avg_t.avg_sal FROM emp e
         CROSS JOIN (SELECT AVG(salary) AS avg_sal FROM emp) AS avg_t ORDER BY e.id;
--- PG 18.6 ---                                 --- MySQL 8.4.10 ---
 name | salary |       avg_sal                  +------+--------+----------+
------+--------+----------------------          | name | salary | avg_sal  |
 ann  |    300 | 400.0000000000000000           +------+--------+----------+
 bob  |    500 | 400.0000000000000000           | ann  |    300 | 400.0000 |
 cho  |   NULL | 400.0000000000000000           | bob  |    500 | 400.0000 |
 dan  |    400 | 400.0000000000000000           | cho  |   NULL | 400.0000 |
(4 rows)                                        | dan  |    400 | 400.0000 |
                                                +------+--------+----------+
```

**행 수가 왜 안 느나** — `4 × 1 = 4`. **오른쪽이 한 행이면 곱해도 늘지 않는다.**\
이것이 `CROSS JOIN` 을 안심하고 쓸 수 있는 유일한 모양이다.

**`avg_sal` 이 왜 400 인가** — `AVG` 가 `cho` 의 `NULL` 을 **건너뛰기** 때문이다.

```text
 salary 네 값:  300, 500, NULL, 400
                      ↓
 AVG 는 NULL 을 안 센다 (분모에서도 빠진다)
                      ↓
 (300 + 500 + 400) / 3 = 400        <- 4 로 나누지 않는다
```

4로 나눴다면 300 이 나왔을 것이다. 집계가 `NULL` 을 다루는 규칙은 [04번](../04-null-three-valued-logic/)·목록의 **21번 주제**가 정본이다.

> **덤으로 보이는 차이** — 같은 400 인데 PG 는 소수 16자리, MySQL 은 4자리로 찍는다.\
> 값이 아니라 **표시 타입**의 차이다. 수치 타입·정밀도는 목록의 **36번 주제**다.

같은 일을 윈도우 함수로도 할 수 있다 — `AVG(salary) OVER ()`(목록의 **26번 주제**).

---

### 10. 엔진이 반드시 `|a| × |b|` 행을 만들어 보는가

**아니다. 조건이 있으면 만들지 않는다. 「카티션곱」은 결과의 정의이지 실행 방식이 아니다.**

```text
### SQL: EXPLAIN SELECT e.name, d.name FROM emp e, dept d WHERE e.dept_id = d.id;
--- PG 18.6 ---
 Hash Join  (cost=38.58..62.85 rows=1130 width=64)
   Hash Cond: (e.dept_id = d.id)
   ->  Seq Scan on emp e  (cost=0.00..21.30 rows=1130 width=36)
   ->  Hash  (cost=22.70..22.70 rows=1270 width=36)
         ->  Seq Scan on dept d  (cost=0.00..22.70 rows=1270 width=36)

### SQL: EXPLAIN SELECT e.name, d.name FROM emp e CROSS JOIN dept d;
--- PG 18.6 ---
 Nested Loop  (cost=0.00..17985.58 rows=1435100 width=64)
   ->  Seq Scan on dept d  (cost=0.00..22.70 rows=1270 width=32)
   ->  Materialize  (cost=0.00..26.95 rows=1130 width=32)
         ->  Seq Scan on emp e  (cost=0.00..21.30 rows=1130 width=32)
```

**조건이 있는 쪽은 `Hash Join`** — `dept` 로 해시 표를 만들고 `emp` 를 한 번 훑는다. **12행은 한 번도 만들어지지 않는다.**\
**조건이 없는 쪽은 `Nested Loop`** — 곱을 실제로 돈다.

MySQL 도 같은 갈림이고, 계획에 **"(no condition)"** 이라고 적어 준다.

```text
### SQL: EXPLAIN FORMAT=TREE SELECT e.name, d.name FROM emp e, dept d WHERE e.dept_id = d.id;
--- MySQL 8.4.10 ---  (출력의 표 테두리는 지웠다)
-> Nested loop inner join  (cost=2.05 rows=4)
    -> Filter: (e.dept_id is not null)  (cost=0.65 rows=4)
        -> Table scan on e  (cost=0.65 rows=4)
    -> Single-row index lookup on d using PRIMARY (id=e.dept_id)  (cost=0.275 rows=1)

### SQL: EXPLAIN FORMAT=TREE SELECT e.name, d.name FROM emp e CROSS JOIN dept d;
--- MySQL 8.4.10 ---
-> Inner hash join (no condition)  (cost=2.5 rows=16)
    -> Covering index scan on d using name  (cost=0.163 rows=4)
    -> Hash
        -> Table scan on e  (cost=0.65 rows=4)
```

| | 조건이 있을 때 | 조건이 없을 때 |
|---|---|---|
| PG 18.6 | `Hash Join` + `Hash Cond` | `Nested Loop` + `Materialize` |
| MySQL 8.4.10 | `Nested loop inner join` + 인덱스 조회 | `Inner hash join (no condition)` |

★ **결론 — 「카티션곱이라 느리다」가 아니라 「조건이 없어서 느리다」다.**\
조건이 있으면 옵티마이저가 그걸 조인 알고리즘의 열쇠로 쓴다. 조건이 없으면 쓸 열쇠가 없어 곱을 도는 것이다.

> **읽을 때 주의** — 위 PG 계획의 `rows=1130`·`rows=1270`·`rows=1435100` 은 **통계가 없어서 나온 기본 추정치**다.\
> 이 표들은 `ANALYZE` 를 돌린 적이 없어 PG 가 「평균적인 표 크기」를 가정했다. 실제 행 수는 4와 3이다.\
> **추정과 실측이 어긋나는 자리**를 읽는 법은 목록의 **60번 주제**가 정본이다.

- **결과는 정의가 정한다.** 옵티마이저가 무엇을 하든 답은 「모든 짝을 만든 뒤 걸렀을 때」와 같아야 한다([01번](../01-logical-query-processing-order/)).
- **비용은 엔진이 정한다.** 위 계획은 이 버전·이 데이터에서 관찰한 것이고 보장이 아니다.
- **진짜 위험한 것은 조건이 아예 없는 경우다.** 그건 정의도 실행도 곱이다(4번의 `d2`).

---

### 11. 네 형태를 12행 기준으로 한 줄씩

```text
             12행에서 무엇을 하나                    행 수   정본
CROSS JOIN   아무것도 안 한다                          12    이 주제
INNER JOIN   ON 으로 거른다                             3    13번
LEFT  JOIN   INNER + 짝 못 찾은 왼쪽을 NULL 로 되살린다   4    14번
RIGHT JOIN   INNER + 짝 못 찾은 오른쪽을 NULL 로 되살린다 4    14번
FULL  OUTER  INNER + 양쪽 다 되살린다                    5    16번
```

행 수의 산술도 한 줄로 떨어진다.

```text
 INNER       = 3                            (12행 중 ON 을 통과한 것)
 LEFT        = 3 + 1 (dan)     = 4          (왼쪽에만 있는 행 1개)
 RIGHT       = 3 + 1 (hr)      = 4          (오른쪽에만 있는 행 1개)
 FULL OUTER  = LEFT + RIGHT - INNER = 4 + 4 - 3 = 5
```

```text
   CROSS (12)              INNER (3)            LEFT (4)           FULL OUTER (5)
 ann-sales ann-dev        ann | sales          ann | sales        ann  | sales
 ann-hr    bob-sales      bob | sales          bob | sales        bob  | sales
 bob-dev   bob-hr         cho | dev            cho | dev          cho  | dev
 cho-sales cho-dev                             dan | NULL         NULL | hr
 cho-hr    dan-sales                                              dan  | NULL
 dan-dev   dan-hr
```

**그림 하나만 기억하면 된다** — 12행을 만들고, 거르고, 되살린다.\
`INNER` 는 [13번](../13-inner-join/), `LEFT`/`RIGHT` 는 [14번](../14-left-right-outer-join/), `FULL OUTER` 는 [16번](../16-full-outer-join/)이 정본이다.\
그리고 **「거르는 조건을 `ON` 에 두느냐 `WHERE` 에 두느냐」가 결과를 바꾸는 자리**가 [15번](../15-on-vs-where-in-outer-join/)이다.

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| 카티션곱 행 수·내용 (1·2번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | |
| 쉼표 표기 대비 (3번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | |
| 조건 누락 시 곱 (4번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | 3행 → 9행 |
| `CROSS JOIN … ON` (5번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **PG 구문 오류가 근거다** |
| 뼈대 + `LEFT JOIN` (6번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | |
| `generate_series` (7번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **`ERROR 1064` 가 근거다** |
| 조합 `<` 대 `<>` (8번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | 6 대 12 |
| 스칼라 `CROSS JOIN` (9번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 표시 정밀도 차이도 확인 |
| 조인 알고리즘 계획 (10번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **구현 의존** — 버전·통계가 바뀌면 다시 찍어야 한다 |

**구현 의존 항목** — 10번의 계획 전부. 조인 알고리즘 선택도, PG 의 행 추정치도 통계에 달려 있다(이 표들은 `ANALYZE` 를 돌린 적이 없다).

**언어 보장 항목** — 1~9·11번. 행 수의 곱셈, `NULL` 의 짝짓기, `CROSS JOIN` 의 문법은 문서가 정한 것이다.\
단 5번(`CROSS JOIN … ON`)과 7번(`generate_series`)은 **버전 표기를 적지 않았다** — 두 매뉴얼 어디에도 도입·제외 버전이 없어서다.
