# sql/33-재귀 CTE — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · WITH Queries (Recursive Queries)](https://www.postgresql.org/docs/18/queries-with.html) · [MySQL 8.4 · WITH (Recursive CTEs)](https://dev.mysql.com/doc/refman/8.4/en/with.html) · [PostgreSQL 14 릴리스 노트](https://www.postgresql.org/docs/release/14.0/)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력·에러는 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 지어낸 출력은 없다.\
> ★ **무한 재귀 실험은 전부 안전장치를 걸고 돌렸다** — MySQL 은 `cte_max_recursion_depth` 를 5 로 낮추고, PG 는 `statement_timeout = '300ms'` 를 걸었다. **맨몸으로 돌린 무한 재귀는 하나도 없다.**\
> 표는 기존 `emp` 만 썼다. **새로 만든 표가 없다** — 계층 데이터는 **CTE 안에서** 만들었다.\
> **버전** — `WITH RECURSIVE` 자체는 두 엔진 모두 오래전부터 있다. PG 의 `SEARCH`/`CYCLE` 은 **14 부터**이고 MySQL 에는 **문법이 없다**(`ERROR 1064` 실행 확인).\
> **선행** — [32 CTE(`WITH`)](../32-cte-with-clause/) · [34 집합 연산](../34-set-operations-union-intersect-except/)(`UNION` 과 `UNION ALL` 의 차이가 이 주제의 종료 조건을 만든다).

## 한눈에 — 쉽게 말하면

**재귀 CTE = 「출발점 한 줄」 + 「이미 찾은 것에서 한 칸 더 가는 규칙」 + 「언제 멈추나」. 셋 중 셋째가 전부다.**

```text
        고정점 (anchor)              재귀 항 (recursive term)
  ┌─────────────────────┐      ┌───────────────────────────────┐
  │ 사장 ann 한 줄       │      │ "방금 찾은 사람의 부하를 찾아라" │
  └──────────┬──────────┘      └───────────────┬───────────────┘
             │                                 │
             ▼      UNION ALL 로 이어 붙인다     ▼
      1회차: ann
      2회차: bob, cho        <- ann 의 부하
      3회차: dan             <- cho 의 부하
      4회차: (아무도 없다)   <- 여기서 멈춘다   ★ 종료 조건
```

- **비유** — 연락망 타기다. **회장 한 사람에게만 전화한다**(고정점). 그 사람이 자기 부하들에게 돌린다(재귀 항).\
  **아무도 새로 전화받을 사람이 없으면 끝난다**(종료).
- **똑같은 구조다** — 그런데 **연락망에 고리가 있으면**(A가 B에게, B가 C에게, C가 다시 A에게) 전화가 영원히 돈다.\
  그걸 막는 방법이 둘 있다 — **"이미 전화받은 사람은 빼라"**(= `UNION`) 또는 **"3단계까지만"**(= 깊이 열).

| 비유 | 실체 |
|---|---|
| 회장 한 사람에게 먼저 전화 | **고정점(anchor)** — 재귀 CTE 를 참조하지 않는 첫 `SELECT` |
| 받은 사람이 자기 부하에게 돌린다 | **재귀 항** — 자기 자신(CTE 이름)을 참조하는 `SELECT` |
| 방금 새로 전화받은 사람들만 다음 차례를 돈다 | **작업 테이블(worktable)** — 직전 회차가 만든 행만 |
| 새로 받을 사람이 없으면 끝 | **종료** — 재귀 항이 0행을 내면 멈춘다 |
| "이미 받은 사람은 빼라" | **`UNION`** — 중복을 접어 고리를 끊는다 |
| "3단계까지만" | **깊이 열** — `WHERE lvl < 3` |
| "전화 3,000통 넘으면 끊어" | MySQL **`cte_max_recursion_depth`** (기본 1000) |
| 통화 시간 제한 | PG **`statement_timeout`** — PG 에는 깊이 제한 설정이 **없다** |

> **재귀 CTE(recursive CTE)** — 자기 이름을 자기 정의 안에서 참조하는 CTE. `WITH RECURSIVE` 로만 쓸 수 있다.\
> 예: `WITH RECURSIVE t(n) AS (SELECT 1 UNION ALL SELECT n+1 FROM t WHERE n < 5) SELECT * FROM t` — `t` 안에 `t` 가 있다.

## 이 주제가 답하려는 질문

1. **이 질의는 언제 멈추나?** — 멈추는 이유가 「데이터가 다 떨어져서」인가, 「내가 걸어 둔 장치 때문」인가.
2. **`UNION` 과 `UNION ALL` 이 여기서 무엇을 바꾸나?** — 중복 제거가 **무한 루프를 막는 장치**가 되는 자리.
3. **사이클이 있으면 무슨 일이 일어나나?** — 그리고 **안전하게** 그것을 시험하는 방법은.

## 예시 데이터 — 이 묶음이 공유하는 것

이 폴더의 SQL 주제들은 **같은 두 표**(`emp`·`dept`)를 쓴다. 그런데 **재귀에는 계층이 필요하고 `emp` 에는 자기 참조 열이 없다.**

**그래서 표를 만들지 않고 [32번](../32-cte-with-clause/)의 CTE 로 계층을 만든다.** 이 주제 자신의 도구를 데이터 준비에 쓰는 셈이다.

```sql
-- 이 주제의 모든 예제가 이 한 줄을 머리에 달고 있다
WITH RECURSIVE staff AS (
  SELECT id, name,
         CASE id WHEN 1 THEN NULL WHEN 2 THEN 1 WHEN 3 THEN 1 WHEN 4 THEN 3 END AS mgr_id
  FROM emp
), ...
```

```text
### SQL: WITH staff AS (SELECT id, name, CASE id WHEN 1 THEN NULL WHEN 2 THEN 1
                        WHEN 3 THEN 1 WHEN 4 THEN 3 END AS mgr_id FROM emp)
         SELECT * FROM staff ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name | mgr_id              +----+------+--------+
----+------+--------             | id | name | mgr_id |
  1 | ann  |                     +----+------+--------+
  2 | bob  |      1              |  1 | ann  |   NULL |
  3 | cho  |      1              |  2 | bob  |      1 |
  4 | dan  |      3              |  3 | cho  |      1 |
(4 rows)                         |  4 | dan  |      3 |
                                 +----+------+--------+
```

```text
 staff 가 만드는 나무 (깊이 3)

        ann (1)          mgr_id = NULL  <- 뿌리
        /      \
    bob (2)   cho (3)
                 \
                dan (4)
```

**왜 이 데이터가 이 주제에 맞나.**

- **뿌리를 `mgr_id IS NULL` 로 고를 수 있다.** `emp` 가 이미 `NULL` 을 품은 표라([04번](../04-null-three-valued-logic/)) 뿌리 판정이 자연스럽다 — 없는 값을 지어내지 않았다.
- **깊이가 3, 갈래가 2** 다. 깊이가 2면 "한 번 더 도는 것"과 "안 도는 것"이 구분되지 않고, 5 이상이면 출력이 한 화면을 넘는다. **`lvl` 열의 1·2·2·3 이 나무 모양 그대로다.**
- **네 행짜리라 무한 루프 실험이 안전하다.** 사이클을 만들어도 한 회차가 만드는 행이 1~2개라, 안전장치가 걸리기 전에 메모리가 부푸는 일이 없다.
- 표를 만들지 않으므로 **다른 주제의 `emp` 가 한 글자도 바뀌지 않는다.** [17번 SELF JOIN](../17-self-join/)은 같은 필요를 **트랜잭션 안에서 `staff` 표를 만들고 롤백**해서 풀었다 — 여기서는 CTE 로 풀었고, **그래서 `CREATE`/`DROP` 이 한 번도 없다.**

**사이클 실험용 데이터**는 화살표 하나만 돌려 만든다 — `ann` 의 상사를 `dan` 으로.

```text
### SQL: WITH cyc AS (SELECT id, name, CASE id WHEN 1 THEN 4 WHEN 2 THEN 1
                      WHEN 3 THEN 1 WHEN 4 THEN 3 END AS mgr_id FROM emp)
         SELECT * FROM cyc ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name | mgr_id              +----+------+--------+
----+------+--------             | id | name | mgr_id |
  1 | ann  |      4              +----+------+--------+
  2 | bob  |      1              |  1 | ann  |      4 |
  3 | cho  |      1              |  2 | bob  |      1 |
  4 | dan  |      3              |  3 | cho  |      1 |
(4 rows)                         |  4 | dan  |      3 |
                                 +----+------+--------+
```

```text
 cyc 가 만드는 고리

   ann(1) ──부하──> cho(3) ──부하──> dan(4) ──부하──> ann(1) ──> ...
                 \
                  bob(2)          <- 고리 밖에 매달린 가지
```

## 동작 방식

### 1. 재귀 CTE 의 세 조각

**언제 쓰나** — 계층·연쇄·수 목록처럼 **"한 칸 더" 를 반복해야** 하는 질의.

```text
WITH RECURSIVE tree AS (
    SELECT ... FROM staff WHERE mgr_id IS NULL      <- (1) 고정점: 자기를 안 부른다
    UNION ALL                                       <- (2) 이어 붙이는 방식
    SELECT ... FROM staff s JOIN tree t ON ...      <- (3) 재귀 항: tree 를 부른다
)                                          ^^^^
SELECT * FROM tree;                        자기 이름
```

엔진이 도는 방식은 이렇다.

```text
 결과 R = {}            작업 테이블 W = 고정점의 결과
      │
      ├─ 1회차:  W = {ann}            R = {ann}
      ├─ 2회차:  W 의 부하를 찾는다 = {bob, cho}   R = {ann, bob, cho}
      ├─ 3회차:  W = {bob, cho} 의 부하 = {dan}    R = {ann, bob, cho, dan}
      └─ 4회차:  W = {dan} 의 부하 = {}  <- 0행    ★ 여기서 멈춘다
```

★ **중요한 것은 「W 가 직전 회차의 결과만」이라는 점이다.** 매번 R 전체를 다시 도는 것이 아니다.

```text
### SQL: WITH RECURSIVE staff AS (...), tree AS (
           SELECT id, name, mgr_id, 1 AS lvl FROM staff WHERE mgr_id IS NULL
           UNION ALL
           SELECT s.id, s.name, s.mgr_id, t.lvl + 1 FROM staff s JOIN tree t ON s.mgr_id = t.id
         ) SELECT lvl, id, name, mgr_id FROM tree ORDER BY lvl, id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 lvl | id | name | mgr_id        +------+------+------+--------+
-----+----+------+--------       | lvl  | id   | name | mgr_id |
   1 |  1 | ann  |               +------+------+------+--------+
   2 |  2 | bob  |      1        |    1 |    1 | ann  |   NULL |
   2 |  3 | cho  |      1        |    2 |    2 | bob  |      1 |
   3 |  4 | dan  |      3        |    2 |    3 | cho  |      1 |
(4 rows)                         |    3 |    4 | dan  |      3 |
                                 +------+------+------+--------+
```

그림 해설 — `lvl` 열의 **1 · 2 · 2 · 3** 이 나무 모양 그대로다. 갈래가 둘인 층이 `lvl = 2` 다.\
비용 — 회차 수 = 나무의 깊이. **깊이가 깊으면 그만큼 돈다** — 그래서 종료 조건이 이 주제의 전부다.

> **고정점(anchor, 앵커 항)** — 재귀 CTE 의 첫 `SELECT`. **자기 이름을 부르지 않는다.**\
> 예: `SELECT … FROM staff WHERE mgr_id IS NULL` — 상사가 없는 사람, 즉 뿌리.
>
> **작업 테이블(worktable)** — 다음 회차의 입력이 되는, **직전 회차가 새로 만든 행들.**\
> 예: 2회차의 입력은 `{ann}` 이고 3회차의 입력은 `{bob, cho}` 다.

---

### 2. `RECURSIVE` 를 빼면 — **두 엔진 다 실패한다**

**언제 쓰나** — MySQL 은 `RECURSIVE` 가 필요 없다고 잘못 알고 있을 때. **필요하다.**

MySQL 매뉴얼이 이 에러를 **문장으로 예고한다** — 인용한다.

> "The `RECURSIVE` keyword must be included if any CTE in the `WITH` clause is recursive. … If you forget `RECURSIVE` for a recursive CTE, this error is a likely result: `ERROR 1146 (42S02): Table 'cte_name' doesn't exist`"\
> — [MySQL 8.4 · WITH](https://dev.mysql.com/doc/refman/8.4/en/with.html)

실제로 그 에러가 나왔다.

```text
### SQL: WITH staff AS (...), tree AS (
           SELECT id, name, mgr_id, 1 AS lvl FROM staff WHERE mgr_id IS NULL
           UNION ALL
           SELECT s.id, s.name, s.mgr_id, t.lvl + 1 FROM staff s JOIN tree t ON s.mgr_id = t.id
         ) SELECT * FROM tree;      -- RECURSIVE 만 뺐다
--- PG 18.6 ---
ERROR:  relation "tree" does not exist
LINE 4: ...id, s.name, s.mgr_id, t.lvl + 1 FROM staff s JOIN tree t ON ...
                                                             ^
DETAIL:  There is a WITH item named "tree", but it cannot be referenced from this part of the query.
HINT:  Use WITH RECURSIVE, or re-order the WITH items to remove forward references.
--- MySQL 8.4.10 ---
ERROR 1146 (42S02) at line 1: Table 'study.tree' doesn't exist
```

그림 해설 — **`RECURSIVE` 없는 `WITH` 에서 자기 참조는 「전방 참조」와 같은 취급**이다([32번](../32-cte-with-clause/) 3번 절).\
자기 이름은 아직 정의가 안 끝났으니 "뒤에 있는 이름"인 셈이다.\
★ **PG 의 `HINT` 가 정확히 `Use WITH RECURSIVE` 라고 말해 준다.** MySQL 은 "그런 표 없다"만 한다 — **매뉴얼이 그 메시지를 미리 적어 둔 이유가 그것이다.**\
비용 — MySQL 에서 이 에러를 받으면 **표 이름을 찾으러 가지 말고 `RECURSIVE` 를 먼저 의심한다.**

---

### 3. **`UNION` 은 중복을 접어 고리를 끊는다**

**언제 쓰나** — 데이터에 사이클이 있을 수 있을 때. **이것이 가장 싼 안전장치다.**

```text
 cyc: ann(1) -> cho(3) -> dan(4) -> ann(1) -> ...

 UNION ALL                              UNION
 1회차: {ann}                           1회차: {ann}
 2회차: {bob, cho}                      2회차: {bob, cho}
 3회차: {dan}                           3회차: {dan}
 4회차: {ann}   <- 또 나왔다             4회차: {ann} 은 이미 R 에 있다 -> 버린다
 5회차: {bob, cho}                              -> 새 행 0개 -> 멈춘다 ★
 ...  영원히
```

```text
### SQL: WITH RECURSIVE cyc AS (...), t AS (
           SELECT id, name FROM cyc WHERE id = 1
           UNION
           SELECT c.id, c.name FROM cyc c JOIN t ON c.mgr_id = t.id
         ) SELECT * FROM t ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name                       +------+------+
----+------                      | id   | name |
  1 | ann                        +------+------+
  2 | bob                        |    1 | ann  |
  3 | cho                        |    2 | bob  |
  4 | dan                        |    3 | cho  |
(4 rows)                         |    4 | dan  |
                                 +------+------+
```

그림 해설 — **사이클이 있는 데이터인데 정상 종료했다.** 두 엔진 다 4행.\
`UNION` 이 "이미 낸 행은 다시 안 낸다"이므로 **고리를 한 바퀴 돌면 새 행이 0개가 되고 그 순간 멈춘다.**\
비용 — ★ **공짜가 아니다.** `UNION` 은 지금까지 낸 행 전부와 대조해야 하므로 중복 제거 비용이 붙고([34번](../34-set-operations-union-intersect-except/)), **행의 「내용」이 같아야만 접힌다.**\
아래 4번의 깊이 열을 붙이는 순간 `lvl` 이 달라서 **안 접힌다** — 그때는 `UNION` 이 안전장치가 되지 못한다.

**그리고 `UNION` 은 원래 중복도 지운다.** 계층 전개에서 같은 사람이 두 경로로 도달할 수 있으면(그물 구조), `UNION` 은 **한 번만 내놓는다** — 그것이 의도인지 확인해야 한다.

---

### 4. **깊이 열로 끊는다** — 가장 확실한 종료 조건

**언제 쓰나** — 사이클 여부를 모를 때, 혹은 `UNION` 으로 접히지 않는 행을 낼 때.

```text
 재귀 항에 조건 한 줄을 더 붙인다

 SELECT c.id, c.name, t.lvl + 1
 FROM cyc c JOIN t ON c.mgr_id = t.id
 WHERE t.lvl < 4          <-- ★ 이 한 줄이 종료를 보장한다
                              lvl 이 단조 증가하므로 반드시 0행이 된다
```

```text
### SQL: WITH RECURSIVE cyc AS (...), t AS (
           SELECT id, name, 1 AS lvl FROM cyc WHERE id = 1
           UNION ALL
           SELECT c.id, c.name, t.lvl + 1 FROM cyc c JOIN t ON c.mgr_id = t.id WHERE t.lvl < 4
         ) SELECT * FROM t;
--- PG 18.6 ---
 id | name | lvl 
----+------+-----
  1 | ann  |   1
  2 | bob  |   2
  3 | cho  |   2
  4 | dan  |   3
  1 | ann  |   4      <- 고리를 한 바퀴 돌아 ann 이 다시 나왔다
(5 rows)
```

그림 해설 — **`ann` 이 두 번 나왔다**(`lvl` 1 과 4). **사이클이 눈에 보인다.**\
`UNION ALL` 이라 접히지 않았고, 멈춘 이유는 데이터가 아니라 **내가 건 `WHERE t.lvl < 4`** 다.\
비용 — 답이 잘렸을 수 있다. **깊이 한도에 걸려 끝났는지, 데이터가 다해서 끝났는지 구분하려면** `MAX(lvl)` 을 한도와 비교해 봐야 한다.

★ **`UNION` 과 깊이 열은 같은 일을 하지 않는다.**

| | `UNION` | 깊이 열 |
|---|---|---|
| 무엇을 막나 | **같은 행의 재방문** | **회차 수** |
| 사이클을 알 수 있나 | 모른다 — 조용히 접힌다 | **보인다**(위의 `ann` 두 번) |
| 언제 안 먹나 | 행에 `lvl`·경로 같은 **변하는 열**이 있으면 안 접힌다 | 항상 먹는다 |
| 결과가 잘릴 수 있나 | 아니다(고리만 끊는다) | **그렇다** — 한도에서 잘린다 |

---

### 5. 안전장치 없이 돌리면 — **두 엔진이 다르게 죽는다**

**언제 쓰나** — 절대 쓰지 않는다. **아래 출력은 안전장치를 걸고 받은 것이다.**

**MySQL 에는 깊이 제한 설정이 있다.** 기본 1000.

```text
### SQL: SHOW cte_max_recursion_depth;  /  SHOW VARIABLES LIKE 'cte_max_recursion_depth';
--- PG 18.6 ---
ERROR:  unrecognized configuration parameter "cte_max_recursion_depth"
--- MySQL 8.4.10 ---
+-------------------------+-------+
| Variable_name           | Value |
+-------------------------+-------+
| cte_max_recursion_depth | 1000  |
+-------------------------+-------+
```

```text
### SQL: SET SESSION cte_max_recursion_depth = 5;      -- ★ 안전장치
         WITH RECURSIVE cyc AS (...), t AS (
           SELECT id, name FROM cyc WHERE id = 1
           UNION ALL
           SELECT c.id, c.name FROM cyc c JOIN t ON c.mgr_id = t.id
         ) SELECT * FROM t;
--- MySQL 8.4.10 ---
ERROR 3636 (HY000) at line 2: Recursive query aborted after 6 iterations. Try increasing @@cte_max_recursion_depth to a larger value.
```

**PG 에는 그런 설정이 없다.** 위의 `unrecognized configuration parameter` 가 그 근거다. 그래서 **시간으로 끊는다.**

```text
### SQL: SET statement_timeout = '300ms';      -- ★ 안전장치
         WITH RECURSIVE cyc AS (...), t AS (
           SELECT id, name FROM cyc WHERE id = 1
           UNION ALL
           SELECT c.id, c.name FROM cyc c JOIN t ON c.mgr_id = t.id
         ) SELECT count(*) FROM t;
--- PG 18.6 ---
ERROR:  canceling statement due to statement timeout
```

그림 해설 — **두 에러 문구가 이 절의 근거 전부다.**\
MySQL 은 **회차를 센다**(`after 6 iterations` — 5 로 설정했는데 6 회차에서 끊었다). PG 는 **시간을 잰다.**\
★ **보고되는 수는 언제나 설정값 + 1 이다** — 기본값 1000 에서는 `after 1001 iterations` 가 나온다.
「한도를 넘은 그 회차」를 세기 때문이고, 그래서 **메시지의 숫자를 설정값으로 읽으면 하나씩 어긋난다.**\
비용 — ★ **PG 쪽이 더 위험하다.** 기본값으로는 **아무도 안 끊는다** — 디스크가 차거나 메모리가 마를 때까지 돈다.\
운영 PG 에는 `statement_timeout` 을 걸어 두고, 질의에는 깊이 열을 붙인다. **둘 다 한다.**

> **`cte_max_recursion_depth`** — MySQL 의 세션 변수. 재귀 회차가 이 값을 넘으면 `ERROR 3636` 으로 중단한다.\
> 예: `SET SESSION cte_max_recursion_depth = 5;` — 얕은 재귀만 허용한다.
>
> **`statement_timeout`** — PostgreSQL 의 세션 변수. 한 문장이 이 시간을 넘으면 취소한다.\
> 예: `SET statement_timeout = '300ms';` — 재귀 실험 전에 이것부터 건다.

---

### 6. `LIMIT` 이 멈춰 주나 — **두 엔진이 정확히 반대다**

**언제 쓰나** — "일단 몇 줄만 보고 싶은데"라고 생각할 때. **엔진마다 답이 다르다.**

```text
 바깥 SELECT 의 LIMIT                     CTE 본문 안의 LIMIT
 WITH RECURSIVE t(n) AS (...)             WITH RECURSIVE t(n) AS (
 SELECT * FROM t LIMIT 5;                   SELECT 1 UNION ALL SELECT n+1 FROM t LIMIT 5)
                                          SELECT * FROM t;

 PG    : 멈춘다  O                        PG    : 문법 미구현  X
 MySQL : 안 멈춘다  X                     MySQL : 멈춘다  O
```

```text
### SQL: SET statement_timeout='3s';   -- 안전장치
         WITH RECURSIVE t(n) AS (SELECT 1 UNION ALL SELECT n+1 FROM t) SELECT * FROM t LIMIT 5;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 n                               ERROR 3636 (HY000) at line 1: Recursive query aborted after 1001
---                              iterations. Try increasing @@cte_max_recursion_depth to a larger value.
 1
 2
 3
 4
 5
(5 rows)

### SQL: WITH RECURSIVE t(n) AS (SELECT 1 UNION ALL SELECT n+1 FROM t LIMIT 5) SELECT * FROM t;
--- PG 18.6 ---
ERROR:  LIMIT in a recursive query is not implemented
LINE 1: ...n) AS (SELECT 1 UNION ALL SELECT n+1 FROM t LIMIT 5) SELECT ...
                                                             ^
--- MySQL 8.4.10 ---
+------+
| n    |
+------+
|    1 |
|    2 |
|    3 |
|    4 |
|    5 |
+------+
```

MySQL 매뉴얼이 그 이유를 적는다.

> "The recursive `SELECT` part of a recursive CTE can also use a `LIMIT` clause… The effect on the result set is the same as when using `LIMIT` in the outermost `SELECT`, **but is also more efficient, since using it with the recursive `SELECT` stops the generation of rows as soon as the requested number of them has been produced.**"\
> — [MySQL 8.4 · WITH](https://dev.mysql.com/doc/refman/8.4/en/with.html)

그림 해설 — "**바깥 `LIMIT` 은 결과만 자르고 생성은 안 멈춘다**"는 말을 매뉴얼이 돌려 말한 것이고, 위 `ERROR 3636` 이 그것을 실측으로 확인해 준다.\
PG 는 반대다 — 바깥 `LIMIT` 이 **수요만큼만 끌어오므로** 생성이 멈추고, 본문 안의 `LIMIT` 은 **아예 구현돼 있지 않다.**\
비용 — ★ **`LIMIT` 을 종료 조건으로 삼으면 이식되지 않는다.** 이식이 필요하면 **깊이 열**(4번 절)이 유일한 공통 수단이다.

#### ★ 괄호를 치면 에러가 사라진다 — 그리고 그게 더 나쁘다

위의 `LIMIT in a recursive query is not implemented` 는 **괄호를 안 쳤을 때** 나온다. 재귀 항을 괄호로 감싸면 **PG 가 문장을 받아 준다.** 그런데 멈추지는 않는다.

```text
### SQL: WITH RECURSIVE t(n) AS (SELECT 1 UNION ALL (SELECT n+1 FROM t LIMIT 3)) SELECT * FROM t;
--- PG 18.6 (SET statement_timeout='2s' 를 먼저 걸었다) ---
ERROR:  canceling statement due to statement timeout

### SQL: ... UNION ALL (SELECT n+1 FROM t ORDER BY n LIMIT 1) ...
--- PG 18.6 (같은 타이머) ---
ERROR:  canceling statement due to statement timeout
```

**타임아웃은 PG 가 막은 것이 아니라 내가 건 타이머가 막은 것이다.** 타이머가 없었으면 그대로 돌았다.

이 칸이 왜 위험한가 — 순서를 따라가 보면 보인다. 브레이크를 걸려고 `LIMIT` 을 본문에 쓴다 → PG 가 `not implemented` 로 거절한다 → **"괄호 문제인가?" 하고 괄호를 친다** → 문장이 통과한다 → **브레이크가 걸렸다고 믿는다.** 에러가 사라진 것을 고쳐진 것으로 읽는 자리다. 실제로는 에러 메시지라는 유일한 경고를 없앤 것뿐이고, 남은 것은 무한 재귀다.

★ **에러가 사라졌다는 것은 문제가 풀렸다는 뜻이 아니다.** 괄호 친 `LIMIT` 은 재귀 항 **한 회차의 출력**을 자를 뿐, 회차를 몇 번 돌지는 건드리지 않는다. 매 회차가 1행씩 내놓으니 재귀 항이 0행을 내는 순간이 영영 오지 않는다 — **종료 조건은 「몇 행을 내놓느냐」가 아니라 「0행을 내놓느냐」다**(3번 절).

---

### 7. 재귀 항에 못 쓰는 것 — **세 엔진 규칙이 거의 같다**

**언제 쓰나** — 재귀 항에 집계나 외부 조인을 쓰고 싶을 때. **막힌다.**

```text
### SQL: WITH RECURSIVE t(n) AS (SELECT 1 UNION ALL SELECT a.n+1 FROM t a, t b WHERE a.n<3 AND b.n<3) SELECT * FROM t;
--- PG 18.6 ---
ERROR:  recursive reference to query "t" must not appear more than once
--- MySQL 8.4.10 ---
ERROR 3577 (HY000) at line 1: In recursive query block of Recursive Common Table Expression 't', the recursive table must be referenced only once, and not in any subquery

### SQL: WITH RECURSIVE t(n) AS (SELECT 1 UNION ALL SELECT MAX(n)+1 FROM t WHERE n < 5) SELECT * FROM t;
--- PG 18.6 ---
ERROR:  aggregate functions are not allowed in a recursive query's recursive term
--- MySQL 8.4.10 ---
ERROR 3575 (HY000) at line 1: Recursive Common Table Expression 't' can contain neither aggregation nor window functions in recursive query block

### SQL: ... UNION ALL SELECT s.id, s.name, t.lvl+1 FROM staff s LEFT JOIN t ON s.mgr_id = t.id ...
--- PG 18.6 ---
ERROR:  recursive reference to query "t" must not appear within an outer join
--- MySQL 8.4.10 ---
ERROR 3576 (HY000) at line 1: In recursive query block of Recursive Common Table Expression 't', the recursive table must neither be in the right argument of a LEFT JOIN, nor be forced to be non-first with join order hints
```

| 금지된 것 | PG 18.6 | MySQL 8.4.10 |
|---|---|---|
| 자기 이름을 **두 번** 참조 | `must not appear more than once` | `ERROR 3577` |
| 재귀 항의 **집계 함수** | `aggregate functions are not allowed` | `ERROR 3575`(윈도우 함수도) |
| 재귀 항이 **외부 조인의 NULL 쪽** | `must not appear within an outer join` | `ERROR 3576` |

그림 해설 — **두 엔진이 같은 셋을 같은 이유로 막는다.** 문구만 다르다.\
**왜 막나** — 작업 테이블은 "직전 회차의 행"이라는 **한 덩어리**다. 두 번 참조하면 어느 회차와 어느 회차를 짝지을지 정의되지 않고, 집계는 "아직 다 안 나온 것"을 요약하려는 것이며, 외부 조인은 **없는 행을 `NULL` 로 만들어 내** 재귀를 끝나지 않게 한다.\
비용 — 집계가 필요하면 **재귀는 전개만 하고, 집계는 바깥 `SELECT` 에서** 한다.

---

### 8. MySQL 의 조용한 함정 — **열 폭이 고정점에서 정해진다**

**언제 쓰나** — 재귀로 경로 문자열을 누적할 때. **MySQL 에서만 터진다.**

MySQL 매뉴얼이 규칙을 적는다.

> "The types of the CTE result columns are inferred from the column types of the **nonrecursive `SELECT` part only**… For type determination, the recursive `SELECT` part is ignored."\
> — [MySQL 8.4 · WITH](https://dev.mysql.com/doc/refman/8.4/en/with.html)

```text
### SQL: WITH RECURSIVE p(n, path) AS (SELECT 1, 'a' UNION ALL SELECT n+1, <연결> FROM p WHERE n < 5)
         SELECT * FROM p;          -- PG 는 path || 'b', MySQL 은 CONCAT(path,'b')
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 n | path                        ERROR 1406 (22001) at line 1: Data too long for column 'path' at row 1
---+-------
 1 | a
 2 | ab
 3 | abb
 4 | abbb
 5 | abbbb
(5 rows)
```

```text
 고정점이 'a' 한 글자           ->  MySQL: path 열의 폭 = 1 글자로 확정
 재귀 항이 'ab' 를 넣으려 한다  ->  2 글자 -> ERROR 1406
 PG 는 text 라 폭 개념이 없다   ->  그냥 자란다
```

**고치는 법** — 고정점에서 `CAST` 로 넓혀 둔다.

```text
### SQL: WITH RECURSIVE p(n, path) AS (SELECT 1, CAST('a' AS CHAR(100))
                                       UNION ALL SELECT n+1, CONCAT(path,'b') FROM p WHERE n < 5)
         SELECT * FROM p;
--- MySQL 8.4.10 ---
+------+-------+
| n    | path  |
+------+-------+
|    1 | a     |
|    2 | ab    |
|    3 | abb   |
|    4 | abbb  |
|    5 | abbbb |
+------+-------+
```

**같은 질의를 `emp.name` 으로 쓰면 안 터진다** — `emp.name` 이 `varchar(20)` 이라 `ann/cho/dan`(11자)이 들어간다.

```text
### SQL: WITH RECURSIVE staff AS (...), p AS (
           SELECT id, name AS path FROM staff WHERE mgr_id IS NULL
           UNION ALL
           SELECT s.id, <연결> FROM staff s JOIN p ON s.mgr_id = p.id
         ) SELECT * FROM p ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id |    path                    +------+-------------+
----+-------------               | id   | path        |
  1 | ann                        +------+-------------+
  2 | ann/bob                    |    1 | ann         |
  3 | ann/cho                    |    2 | ann/bob     |
  4 | ann/cho/dan                |    3 | ann/cho     |
(4 rows)                         |    4 | ann/cho/dan |
                                 +------+-------------+
```

비용 — ★ **그래서 더 위험하다.** 얕은 계층에서는 통과하고 **깊어지는 날 운영에서 처음 터진다.** [11번](../11-subquery-scalar-correlated-any-all/)의 "오늘 되던 질의가 내일 터진다"와 같은 종류다.

---

### 9. PG 14+ 의 전용 문법 — `SEARCH` 와 `CYCLE`

**언제 쓰나** — PG 에서만. 위의 깊이 열·사이클 표시를 **문법으로** 쓰는 것이다.

```text
### SQL: WITH RECURSIVE cyc AS (...), t AS (
           SELECT id, name FROM cyc WHERE id = 1
           UNION ALL
           SELECT c.id, c.name FROM cyc c JOIN t ON c.mgr_id = t.id
         ) CYCLE id SET is_cycle USING path
         SELECT id, name, is_cycle FROM t;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name | is_cycle            ERROR 1064 (42000) at line 1: You have an error in your SQL syntax;
----+------+----------           check the manual that corresponds to your MySQL server version for
  1 | ann  | f                   the right syntax to use near 'CYCLE id SET is_cycle USING path
  2 | bob  | f                   SELECT id, name, is_cycle FROM t' at line 1
  3 | cho  | f
  4 | dan  | f
  1 | ann  | t      <- 고리를 닫는 행에 t 가 찍히고, 거기서 멈춘다
(5 rows)
```

```text
### SQL: WITH RECURSIVE staff AS (...), t AS ( ... )
         SEARCH DEPTH FIRST BY id SET ord SELECT id, name, ord FROM t ORDER BY ord;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name |      ord            ERROR 1064 (42000) at line 1: ... near 'SEARCH DEPTH FIRST BY id
----+------+---------------      SET ord SELECT id, name, ord FROM t ORDER BY ord' at line 1
  1 | ann  | {(1)}
  2 | bob  | {(1),(2)}
  3 | cho  | {(1),(3)}
  4 | dan  | {(1),(3),(4)}
(4 rows)
```

그림 해설 — `CYCLE` 은 **`UNION ALL` 이면서도 고리에서 멈춘다.** 마지막 행에 `is_cycle = t` 가 찍혀 "**여기서 고리를 봤다**"고 알려 준다 — 3번의 `UNION` 이 조용히 접는 것과 다르다.\
`SEARCH DEPTH FIRST` 의 `ord` 는 **뿌리부터의 경로 그 자체**라, 그걸로 정렬하면 나무 순서가 나온다.\
비용 — **PG 14 부터**이고 **MySQL 에는 문법이 아예 없다**(`ERROR 1064` 둘 다). 이식이 필요하면 4번의 깊이 열과 8번의 경로 문자열을 직접 쓴다.

---

### 10. 계층 말고도 — **위로 올라가기**

**언제 쓰나** — "이 사람의 상사들을 전부" 같은 질의. 조인 방향만 뒤집으면 된다.

```text
 내려가기 (부하 찾기)                올라가기 (상사 찾기)
 JOIN staff s ON s.mgr_id = t.id     JOIN staff s ON s.id = t.mgr_id
                 ^^^^^^^^   ^^^^                    ^^^^   ^^^^^^^^
            새 행의 상사가 = 기존 행     새 행이 = 기존 행의 상사
```

```text
### SQL: WITH RECURSIVE staff AS (...), up AS (
           SELECT id, name, mgr_id, 0 AS up_lvl FROM staff WHERE id = 4
           UNION ALL
           SELECT s.id, s.name, s.mgr_id, u.up_lvl+1 FROM staff s JOIN up u ON s.id = u.mgr_id
         ) SELECT * FROM up ORDER BY up_lvl;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name | mgr_id | up_lvl     +------+------+--------+--------+
----+------+--------+--------    | id   | name | mgr_id | up_lvl |
  4 | dan  |      3 |      0     +------+------+--------+--------+
  3 | cho  |      1 |      1     |    4 | dan  |      3 |      0 |
  1 | ann  |        |      2     |    3 | cho  |      1 |      1 |
(3 rows)                         |    1 | ann  |   NULL |      2 |
                                 +------+------+--------+--------+
```

그림 해설 — 멈춘 이유는 **`ann.mgr_id` 가 `NULL`** 이라 조인이 아무것도 못 맞춘 것이다 — `NULL = 무엇`은 `UNKNOWN` 이므로([04번](../04-null-three-valued-logic/)) 0행이 되고 재귀가 끝난다.\
비용 — **뿌리의 `NULL` 이 종료 조건을 겸한다.** 그래서 계층 표에서 뿌리를 `NULL` 로 두는 설계가 흔하다.

**경계 한 줄** — **그래프 탐색 알고리즘 자체**(BFS·DFS·방문 표시·큐와 스택)는 [`algorithm/11-bfs`](../../../../../algorithm/11-bfs/) · [`algorithm/12-dfs`](../../../../../algorithm/12-dfs/)가 정본이고, 여기서는 **재귀 CTE 의 문법과 종료 조건**만 다룬다. 위 1번 절의 회차 도식은 **엔진이 정의한 평가 절차**이지 알고리즘 설명이 아니다.

## 문법 — 어느 절에서 무엇이 보이나

```sql
WITH RECURSIVE 이름 [(열, 열, ...)] AS (
      <고정점 SELECT>          -- 이름을 참조하지 않는다
    UNION [ALL]                -- ALL 이면 중복을 안 지운다
      <재귀 SELECT>            -- 이름을 딱 한 번 참조한다
)
[ SEARCH {DEPTH|BREADTH} FIRST BY 열 SET 정렬열 ]   -- PG 14+ 전용
[ CYCLE 열 SET 표시열 USING 경로열 ]                 -- PG 14+ 전용
SELECT ... FROM 이름;
```

금지 사례 — **문법이 맞아 보이는데 거부되는 것들**(7번 절).

```sql
-- X 자기 이름을 두 번            -> PG: must not appear more than once / MySQL: ERROR 3577
FROM t a, t b
-- X 재귀 항의 집계               -> PG: aggregate functions are not allowed / MySQL: ERROR 3575
SELECT MAX(n)+1 FROM t
-- X 외부 조인의 NULL 쪽          -> PG: must not appear within an outer join / MySQL: ERROR 3576
FROM staff s LEFT JOIN t ON ...
-- X RECURSIVE 빠뜨림             -> PG: relation "t" does not exist / MySQL: ERROR 1146
WITH t AS (... FROM t ...)
-- X PG 에서 본문 안 LIMIT        -> ERROR: LIMIT in a recursive query is not implemented
(SELECT 1 UNION ALL SELECT n+1 FROM t LIMIT 5)
```

규칙 여덟.

1. **`RECURSIVE` 는 두 엔진 다 필수다.** 빼면 "그런 표 없다"가 나온다.
2. **고정점은 자기를 부르지 않고, 재귀 항은 딱 한 번 부른다.**
3. **`UNION` 은 중복을 접어 고리를 끊는다.** `UNION ALL` 은 안 끊는다.
4. **종료는 재귀 항이 0행을 낼 때**다. 그때까지 안 멈추면 안전장치가 필요하다.
5. **깊이 열이 유일한 이식 가능한 안전장치**다(`WHERE lvl < N`).
6. **`LIMIT` 은 두 엔진이 정반대**다 — PG 는 바깥, MySQL 은 본문 안.
7. **MySQL 은 고정점에서 열 타입·폭이 확정된다.** 문자열 누적은 `CAST` 로 넓혀 둔다.
8. **`SEARCH`/`CYCLE` 은 PG 14+ 전용**이다. MySQL 은 `ERROR 1064`.

읽을 때 붙잡을 것은 **"이 질의는 왜 멈추나"** 하나다.

```text
 왜 멈추나?
   ├─ 데이터가 다했다          -> 정상. 나무에 잎이 끝났다
   ├─ UNION 이 접었다          -> 고리가 있었다는 뜻. 조용하다
   ├─ 깊이 열에 걸렸다         -> 답이 잘렸을 수 있다. MAX(lvl) 을 확인하라
   ├─ cte_max_recursion_depth  -> MySQL. ERROR 3636
   ├─ statement_timeout        -> PG. 여기까지 왔다면 설계를 다시 본다
   └─ 안 멈춘다                -> PG 기본값. 디스크가 찰 때까지 돈다
```

## 어디서 틀리나

- **`RECURSIVE` 를 빠뜨리고 MySQL 의 `Table 'x' doesn't exist` 를 오타로 읽는다.**\
  매뉴얼이 이 오해를 예고할 만큼 흔하다. **표를 찾으러 가지 말고 `RECURSIVE` 부터 보라.**
- **사이클을 생각하지 않는다.**\
  조직도·카테고리·친구 관계는 **언젠가 고리가 생긴다.** `UNION` 이든 깊이 열이든 **하나는 반드시** 건다.
- **깊이 열을 붙이고 `UNION` 이 지켜 줄 거라 믿는다.**\
  `lvl` 이 매번 달라서 **행이 안 접힌다.** 깊이 열을 쓸 거면 `WHERE lvl < N` 도 같이 쓴다.
- **바깥 `LIMIT` 으로 멈출 거라 믿는다.**\
  PG 에서는 멈추고 **MySQL 에서는 안 멈춘다**(`ERROR 3636`). 이식되지 않는다.
- **PG 에 깊이 제한 설정이 있을 거라 믿는다.**\
  **없다.** `SHOW cte_max_recursion_depth` 가 `unrecognized configuration parameter` 다. `statement_timeout` 을 직접 건다.
- **MySQL 에서 경로 문자열을 누적한다.**\
  고정점의 폭으로 잘린다 — `ERROR 1406`. **얕을 때는 통과하고 깊어지면 터진다.**
- **재귀 항에서 집계하려 한다.** 두 엔진 다 거부한다. 집계는 바깥 `SELECT` 에서.
- **깊이 한도에 걸린 결과를 완전한 답으로 쓴다.**\
  `MAX(lvl)` 이 한도와 같으면 **잘렸을 가능성**을 의심한다.
- **`SEARCH`/`CYCLE` 을 MySQL 로 옮긴다.** `ERROR 1064` 다.

## 구현 세부사항 대 언어 보장

| | 무엇인가 | 누가 보장하나 |
|---|---|---|
| 고정점 + 재귀 항 + `UNION [ALL]` 이라는 구조 | **문법의 정의** | 언어 — 두 엔진 같다 |
| `RECURSIVE` 가 필수라는 것 | **문법의 정의** | 언어 — 두 엔진 같다(문구만 다르다) |
| 재귀 항이 0행을 내면 끝난다는 것 | **평가의 정의** | 언어 — 두 엔진 같다 |
| `UNION` 이 고리를 끊는다는 것 | **결과의 정의에서 따라 나온다** | 언어 — 중복 제거의 귀결이다 |
| 자기 참조 1회·집계 금지·외부 조인 금지 | **문법의 정의** | 언어 — 두 엔진이 같은 셋을 막는다 |
| **`cte_max_recursion_depth` 기본 1000** | **MySQL 의 설정값** | MySQL — **PG 에는 대응물이 없다** |
| **바깥 `LIMIT` 이 생성을 멈추나** | **엔진의 평가 방식** | 서로 반대다 — PG 는 멈추고 MySQL 은 안 멈춘다 |
| **열 폭이 고정점에서 확정된다** | **MySQL 의 타입 결정 규칙** | MySQL 매뉴얼이 문장으로 적는다. PG 에는 해당 없음 |
| `SEARCH`/`CYCLE` | **PG 14+ 의 문법** | PG — MySQL 은 `ERROR 1064` |
| 회차마다 **몇 행이 만들어지나** | 데이터에 달렸다 | 아무도 — 그래서 안전장치가 필요하다 |

- ★ **「안 터졌다」는 「안전하다」가 아니다.** 이 주제의 사이클 실험은 **전부 4행짜리 데이터**에서 했다.\
  같은 질의가 100만 행에서는 **안전장치가 걸리기 전에 디스크를 채운다.** 여기서 본 것은 **문법의 동작**이지 규모의 안전성이 아니다.
- ★ **한쪽에서만 결론이 서는 실험이 있다** — 5번의 `ERROR 3636` 은 **MySQL 쪽만** 근거이고, `canceling statement due to statement timeout` 은 **PG 쪽만** 근거다.\
  두 에러는 **같은 사실(무한 재귀)의 서로 다른 증거**이지 서로를 대신하지 못한다.
- **PG 의 `unrecognized configuration parameter` 는 「부재의 증거」로 쓸 수 있는 드문 출력이다** — "문서에 없다"가 아니라 **서버가 모른다고 대답했다.**

## 언제 쓰고 언제 안 쓰나

- **쓴다 — 계층 전개.** 조직도·카테고리·댓글 스레드·부품 구성표.
- **쓴다 — 수 목록·날짜 목록 만들기.** MySQL 에는 `generate_series` 가 없어([12번](../12-cartesian-product-cross-join/)) **재귀 CTE 가 사실상 유일한 수단**이다.
- **쓴다 — 조상 찾기.** 조인 방향만 뒤집으면 된다(10번 절).
- **안 쓴다 — 깊이가 고정돼 있을 때.** 2~3단계면 `LEFT JOIN` 을 그만큼 이어 붙이는 편이 읽기 쉽다([17번](../17-self-join/)).
- **안 쓴다 — 최단 경로·연결 성분 같은 그래프 문제.** 답이 나오기는 하지만 그 자리는 [`algorithm/11-bfs`](../../../../../algorithm/11-bfs/)·[`12-dfs`](../../../../../algorithm/12-dfs/)의 도구가 맞다.
- **주의 — 사이클 가능성이 있으면 안전장치부터.** 쓰고 나서 거는 것이 아니라 **쓰면서 같이** 건다.
- **주의 — 운영 PG 에는 `statement_timeout` 을 세션·역할 단위로 걸어 둔다.** 기본값으로는 아무도 안 끊는다.

## 핵심 문장

- 재귀 CTE 는 **고정점 + 재귀 항 + 이어 붙이기**이고, **종료 조건이 이 주제의 전부**다.
- **종료는 재귀 항이 0행을 낼 때**다 — 데이터가 다해서든, `UNION` 이 접어서든, 내가 깊이로 끊어서든.
- **`UNION` 은 중복을 접어 고리를 끊는다.** 단 행에 `lvl` 같은 변하는 열이 있으면 **안 접힌다.**
- **`RECURSIVE` 는 두 엔진 다 필수**이고, MySQL 은 그 실수를 `Table 'x' doesn't exist` 로만 알려 준다.
- **MySQL 에는 `cte_max_recursion_depth`(기본 1000)가 있고 PG 에는 없다** — PG 는 `statement_timeout` 을 직접 건다.
- **`LIMIT` 은 두 엔진이 정반대다** — PG 는 바깥에서 멈추고, MySQL 은 본문 안에서만 멈춘다.
- **MySQL 은 고정점에서 열 폭이 확정된다** — 경로 누적은 `CAST` 로 넓히지 않으면 `ERROR 1406`.
- 재귀 항에는 **자기 참조 2회·집계·외부 조인의 NULL 쪽**을 못 쓴다. 두 엔진이 같은 셋을 막는다.

## 관련 자료

- [PostgreSQL 18 · WITH Queries (Recursive Queries)](https://www.postgresql.org/docs/18/queries-with.html) — 평가 절차(작업 테이블)와 `SEARCH`/`CYCLE` 이 한 페이지에 있다.
- [MySQL 8.4 · WITH (Recursive CTEs)](https://dev.mysql.com/doc/refman/8.4/en/with.html) — `RECURSIVE` 누락 에러·열 타입 규칙·`LIMIT` 을 **문장으로** 적는다.
- [PostgreSQL 14 릴리스 노트](https://www.postgresql.org/docs/release/14.0/) — `SEARCH`/`CYCLE` 도입.
- [32 CTE(`WITH`)](../32-cte-with-clause/) — **경계: 그쪽은 이름·가시성·최적화 장벽까지, 여기는 그 이름이 자기 자신을 부를 때부터.**
- [34 집합 연산 — UNION·INTERSECT·EXCEPT 와 ALL](../34-set-operations-union-intersect-except/) — **경계: 그쪽은 `UNION` 과 `UNION ALL` 의 의미·비용까지, 여기는 그 차이가 무한 루프를 막느냐부터.**
- [`algorithm/11-bfs`](../../../../../algorithm/11-bfs/) · [`algorithm/12-dfs`](../../../../../algorithm/12-dfs/) — **경계: 탐색 알고리즘 자체(방문 표시·큐와 스택·복잡도)는 거기, 여기는 재귀 CTE 의 문법과 종료 조건.**
- [17 SELF JOIN](../17-self-join/) — **경계: 그쪽은 깊이가 고정된 계층을 별칭 N개로 펴는 것까지, 여기는 깊이를 모를 때부터.** 그쪽은 같은 계층 데이터를 **표를 만들어** 다뤘고, 여기는 **CTE 로** 다뤘다.
- [04 NULL 의 3값 논리](../04-null-three-valued-logic/) — 뿌리의 `mgr_id IS NULL` 과, 올라가기가 `NULL` 에서 멈추는 이유.
- [12 카티션곱과 CROSS JOIN](../12-cartesian-product-cross-join/) — PG 의 `generate_series` 가 MySQL 에 없다는 것. 그 대체가 이 주제다.
- **`EXPLAIN` 계획 트리 읽는 법**은 [58번 주제](../58-explain-plan-tree/)가 정본이다.
- [SQL 주제 목록](../README.md)

## 용어 풀이

- **재귀 CTE(recursive CTE)** — 자기 이름을 자기 정의 안에서 참조하는 CTE.\
  예: `WITH RECURSIVE t(n) AS (SELECT 1 UNION ALL SELECT n+1 FROM t WHERE n < 5)`.
- **고정점(anchor, 앵커 항)** — 재귀 CTE 의 첫 `SELECT`. 자기 이름을 부르지 않는다.\
  예: `SELECT … FROM staff WHERE mgr_id IS NULL` — 상사가 없는 사람.
- **재귀 항(recursive term)** — 자기 이름을 참조하는 쪽의 `SELECT`. 딱 한 번만 참조할 수 있다.\
  예: `SELECT … FROM staff s JOIN tree t ON s.mgr_id = t.id`.
- **작업 테이블(worktable)** — 다음 회차의 입력이 되는, 직전 회차가 **새로 만든** 행들.\
  예: 2회차 입력은 `{ann}`, 3회차 입력은 `{bob, cho}`.
- **종료 조건(termination)** — 재귀가 멈추는 조건. **재귀 항이 0행을 낼 때** 멈춘다.\
  예: `dan` 의 부하를 찾았더니 아무도 없어서 끝난 것.
- **사이클(cycle, 고리)** — 따라가다 보면 자기 자신으로 돌아오는 참조.\
  예: `ann → cho → dan → ann`. 안전장치가 없으면 영원히 돈다.
- **`cte_max_recursion_depth`** — MySQL 세션 변수. 회차가 넘으면 `ERROR 3636` 으로 중단.\
  예: `SET SESSION cte_max_recursion_depth = 5;` — 얕은 재귀만 허용.
- **`statement_timeout`** — PostgreSQL 세션 변수. 한 문장이 이 시간을 넘으면 취소.\
  예: `SET statement_timeout = '300ms';` — 재귀 실험 전에 이것부터 건다.
- **깊이 열(depth column)** — 회차 수를 세는 열. `WHERE lvl < N` 으로 종료를 보장한다.\
  예: `t.lvl + 1` 을 재귀 항에서 올리고 `WHERE t.lvl < 4` 로 끊는다.
- **`SEARCH` 절** — PG 14+ 전용. 깊이/너비 우선 정렬용 열을 만들어 준다.\
  예: `SEARCH DEPTH FIRST BY id SET ord` → `ord` 가 `{(1),(3),(4)}` 같은 경로가 된다.
- **`CYCLE` 절** — PG 14+ 전용. 고리를 만나면 표시 열에 `t` 를 찍고 멈춘다.\
  예: `CYCLE id SET is_cycle USING path`.
- **`ERROR 1406`(Data too long)** — MySQL 이 열 폭을 넘는 값을 거부할 때의 에러.\
  예: 고정점이 `'a'` 한 글자라 `'ab'` 를 못 넣은 것.

## 더 들어가면

- **`UNION` 의 중복 제거는 공짜가 아니다.** 지금까지 낸 행 전부와 대조하므로 깊은 재귀에서는 그 비용이 지배한다 — [34번](../34-set-operations-union-intersect-except/)의 `HashAggregate` / `Union materialize with deduplication` 이 그 비용이다.
- **PG 의 `CYCLE` 절은 내부적으로 경로 배열을 만든다.** 문서가 "will be internally rewritten" 이라고 적는다 — 즉 4번 절의 수동 방식을 문법으로 감싼 것이다.
- **깊이가 고정된 계층은 재귀가 필요 없다.** `LEFT JOIN` 을 깊이만큼 이어 붙이면 된다([17번](../17-self-join/)) — 계획이 단순하고 인덱스도 잘 탄다.
- **MySQL 에서 수 목록이 필요하면** `WITH RECURSIVE seq(n) AS (SELECT 1 UNION ALL SELECT n+1 FROM seq WHERE n < 100)` 가 PG 의 `generate_series(1,100)` 자리를 대신한다.
- **재귀 CTE 를 뷰에 넣을 수 있다** — 그러면 이름이 문장 하나를 넘어 산다. 뷰는 [48번 주제](../48-views-and-materialized-views/).
