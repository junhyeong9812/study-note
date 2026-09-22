# sql/58-`EXPLAIN` 읽기 — 계획 트리의 구조 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · EXPLAIN](https://www.postgresql.org/docs/18/sql-explain.html) · [PostgreSQL 18 · Using EXPLAIN](https://www.postgresql.org/docs/18/using-explain.html) · [MySQL 8.4 · EXPLAIN Output Format](https://dev.mysql.com/doc/refman/8.4/en/explain-output.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 계획·출력·에러는 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 지어낸 계획은 없다.\
> **이 편이 만든 객체와 그 뒷정리** — 표 `t58_big`(20만 행). PG 는 `BEGIN … ROLLBACK` 안에서 만들었고,
> MySQL 은 DDL 이 암묵 커밋이라 `DROP TABLE IF EXISTS t58_big` 로 직접 지웠다. **기존 `emp`·`dept` 는 읽기만 했다.**\
> ★ **실행 계획은 관찰이지 보장이 아니다.** 아래 계획은 **제출 직전에 전부 다시 찍어 대조한 것**이다 —
> 드리프트 결과는 3-answer 의 「실행 검증」 표에 적었다.\
> **선행** — [01 논리적 질의 처리 순서](../01-logical-query-processing-order/) · [13 INNER JOIN](../13-inner-join/).
> **이 주제의 축이 01 이다** — 논리 순서와 물리 계획이 다르다는 것.

## 한눈에 — 쉽게 말하면

**`EXPLAIN` 은 「엔진이 이 질의를 어떤 순서로, 어떤 방법으로 풀 작정인지」를 적은 계획서다.**

- 「서울에서 부산까지」라고만 말하면 **무엇을 원하는지**는 정해지지만 **어떻게 갈지**는 안 정해진다.
- 내비게이션은 그 요청을 받아 **「고속도로 → 휴게소 → 국도」** 같은 구체적 경로를 짠다.
- 그 경로는 **도로 상황(통계)에 따라 매번 달라질 수 있다.** 같은 출발·도착인데 어제와 다른 길을 줄 수 있다.
- SQL 도 똑같다 — `SELECT` 는 **무엇을** 말하고, 계획은 **어떻게**를 말한다.

| 비유 | 실체 |
|---|---|
| "서울에서 부산까지" | `SELECT … FROM … WHERE …` (무엇을) |
| 내비게이션이 짠 경로 | 계획 트리(plan tree) (어떻게) |
| 경로 안내 한 줄 | 계획 노드(node) — `Seq Scan`·`Hash Join`… |
| 예상 소요 시간 | `cost=…` |
| 도로 상황 | 통계(statistics) |
| 어제와 다른 길이 나온다 | 통계가 바뀌면 계획이 바뀐다 |

```text
 논리적 처리 순서 (01번 — 무엇을)      물리적 계획 트리 (58번 — 어떻게)
 +---------------------------+        +---------------------------+
 | 1 FROM                    |        | Limit                     |  <- 마지막에 도는 것이 맨 위
 | 2 WHERE                   |        |  -> Sort                  |
 | 3 GROUP BY                |        |    -> HashAggregate       |
 | 4 HAVING                  |        |      -> Hash Join         |
 | 5 SELECT                  |        |        -> Seq Scan  emp   |  <- 먼저 도는 것이 맨 아래
 | 7 ORDER BY                |        |        -> Hash            |
 | 8 LIMIT                   |        |          -> Seq Scan dept |
 +---------------------------+        +---------------------------+
   위에서 아래로 읽는다                  아래에서 위로 읽는다
```

**똑같은 구조다** — 두 그림은 **같은 질의 하나**를 서로 다른 축으로 본 것이다.\
01 이 「결과가 왜 그 값인가」를 설명한다면, 58 은 「그 값을 얻는 데 왜 그만큼 걸리나」를 설명한다.

> **계획 트리(plan tree)** — 질의를 실행할 연산자들을 부모-자식으로 엮은 나무. **자식이 만든 행을 부모가 받는다.**\
> 예: `Sort` 의 자식이 `Seq Scan` 이면, 표를 다 읽어 만든 행을 정렬한다는 뜻이다.

> **연산자(operator / node)** — 계획 트리의 한 칸. 「표를 순서대로 읽어라」·「해시로 붙여라」 같은 한 가지 일을 한다.\
> 예: `Seq Scan`·`Index Scan`·`Hash Join`·`Sort`. 어느 조건에서 무엇이 뽑히는지는 [59번](../59-scan-join-sort-operators/)에서 본다.

## 이 주제가 답하려는 질문

1. **계획 트리를 어느 방향으로 읽나** — 그리고 그 방향이 01 의 논리 순서와 어떻게 다른가.
2. **`cost=0.00..3472.00 rows=200000 width=29` 의 네 숫자는 각각 무엇인가.**
3. **두 엔진의 `EXPLAIN` 출력 형식이 왜 이렇게 다른가** — 같은 질의를 던져 나란히 놓으면 무엇이 보이나.

## 예시 데이터 — 이 묶음이 공유하는 것

구조를 보는 데는 **기존 `emp`·`dept`** 를 쓴다(읽기만 한다).

```text
emp (사원)                          dept (부서)
+----+------+---------+--------+    +----+-------+
| id | name | dept_id | salary |    | id | name  |
+----+------+---------+--------+    +----+-------+
|  1 | ann  |      10 |    300 |    | 10 | sales |
|  2 | bob  |      10 |    500 |    | 20 | dev   |
|  3 | cho  |      20 |   NULL |    | 30 | hr    |
|  4 | dan  |    NULL |    400 |    +----+-------+
+----+------+---------+--------+
```

**다만 4행·3행으로는 숫자 칸이 안 읽힌다** — 표가 너무 작으면 엔진은 언제나 전체 스캔을 고르고,\
PG 쪽은 **`emp`·`dept` 가 한 번도 `ANALYZE` 된 적이 없어** 추정치가 실제와 무관한 기본값이다.

```text
### SQL: SELECT c.relname, c.reltuples, c.relpages FROM pg_class c WHERE c.relname IN ('emp','dept');
--- PG 18.6 ---
 relname | reltuples | relpages
---------+-----------+----------
 dept    |        -1 |        0
 emp     |        -1 |        0
(2 rows)
```

`reltuples = -1` 은 「**아직 센 적 없음**」이다. 그래서 숫자 칸(2절)과 연산자(3절)는 **20만 행짜리 `t58_big`** 에서 본다.\
추정이 실제와 어긋나는 것 자체가 주제인 [60번](../60-explain-analyze-estimates-vs-actuals/)에서 이 `-1` 이 다시 나온다.

```sql
-- PG: BEGIN … ROLLBACK 안에서
CREATE TABLE t58_big AS SELECT g AS id, (g % 1000) AS grp, repeat('x',20) AS pad FROM generate_series(1,200000) g;
ALTER TABLE t58_big ADD PRIMARY KEY (id);
CREATE INDEX t58_big_grp ON t58_big (grp);
ANALYZE t58_big;
```

## 동작 방식

### 1. ★ 트리는 아래에서 위로 읽는다 — 논리 순서와 반대다

**언제 쓰나** — 계획을 처음 볼 때. **읽는 방향을 틀리면 나머지가 전부 어긋난다.**

같은 질의를 두 엔진에 던졌다.

```sql
SELECT d.name, count(*) AS c
FROM emp e JOIN dept d ON e.dept_id = d.id
WHERE e.salary > 100
GROUP BY d.name
ORDER BY c DESC
LIMIT 2;
```

```text
### SQL: EXPLAIN (위 질의)
--- PG 18.6 ---
 Limit  (cost=73.11..73.12 rows=2 width=40)
   ->  Sort  (cost=73.11..74.06 rows=377 width=40)
         Sort Key: (count(*)) DESC
         ->  HashAggregate  (cost=65.57..69.34 rows=377 width=40)
               Group Key: d.name
               ->  Hash Join  (cost=38.58..63.69 rows=377 width=32)
                     Hash Cond: (e.dept_id = d.id)
                     ->  Seq Scan on emp e  (cost=0.00..24.12 rows=377 width=4)
                           Filter: (salary > 100)
                     ->  Hash  (cost=22.70..22.70 rows=1270 width=36)
                           ->  Seq Scan on dept d  (cost=0.00..22.70 rows=1270 width=36)
(11 rows)
```

**읽는 규칙은 둘뿐이다.**

```text
규칙 1. 들여쓰기가 깊을수록 먼저 돈다 (맨 아래 → 맨 위)
규칙 2. 한 부모의 자식이 여럿이면 위에 쓰인 자식이 먼저다
```

```text
 읽는 순서                                     무슨 일이 일어나나
 6  Limit                                      2행만 꺼내고 끝낸다
 5  └ Sort                                     count(*) 내림차순으로 줄 세운다
 4    └ HashAggregate                          d.name 으로 묶어 센다
 3      └ Hash Join                            두 입력을 해시로 붙인다
 1        ├ Seq Scan on emp (Filter)           emp 를 훑으며 salary>100 을 거른다   <- 첫 번째
 2        └ Hash → Seq Scan on dept            dept 를 훑어 해시 표를 만든다
```

그림 해설 — **맨 아래 `Seq Scan on emp` 가 가장 먼저 돌고, 맨 위 `Limit` 이 마지막이다.**\
01 의 논리 순서는 `FROM → WHERE → GROUP BY → … → LIMIT` 로 **위에서 아래**였다. 계획은 **아래에서 위**다.

**★ 두 순서가 실제로 어긋나는 자리를 하나 짚는다.** 01 의 순서대로면 `WHERE` 는 `FROM` *다음*의 독립 단계다.\
그런데 계획에는 `WHERE` 라는 노드가 **없다.** `Filter: (salary > 100)` 이 되어 **`Seq Scan` 안으로 들어갔다.**

```text
 01 의 논리 순서                        58 의 물리 계획
 +---------------------------+         +---------------------------+
 | 1 FROM   emp 를 읽는다     |         | Seq Scan on emp           |
 | 2 WHERE  salary>100 을 건다|   -->   |   Filter: (salary > 100)  |  <- 한 노드로 합쳐졌다
 +---------------------------+         +---------------------------+
   두 단계                                한 단계 — 읽으면서 바로 거른다
```

**논리 순서는 「결과가 무엇인가」를 정의하고, 계획은 그 결과를 내는 아무 방법이나 쓸 수 있다.**\
같은 답이 나오기만 하면 엔진은 단계를 합치고, 옮기고, 순서를 바꾼다.

비용 — 이 합치기가 공짜 최적화다. 걸러진 행은 **위 노드로 올라가지 않는다.**

---

### 2. ★ `cost=시작..전체 rows= width=` — 네 숫자의 뜻

**언제 쓰나** — 계획의 어느 노드가 비싼지 찾을 때.

```text
Seq Scan on t58_big  (cost=0.00..3472.00 rows=200000 width=29)
                           ^^^^  ^^^^^^^      ^^^^^^       ^^
                           시작   전체         행 수        행 폭
```

**이름은 지어낼 필요가 없다 — 엔진이 붙여 준다.** 같은 계획을 JSON 으로 찍으면 칸 이름이 그대로 나온다.

```text
### SQL: EXPLAIN (FORMAT JSON) SELECT id FROM emp WHERE salary > 100;
--- PG 18.6 ---
 [
   {
     "Plan": {
       "Node Type": "Seq Scan",
       "Relation Name": "emp",
       "Startup Cost": 0.00,
       "Total Cost": 24.12,
       "Plan Rows": 377,
       "Plan Width": 4,
       "Filter": "(salary > 100)"
     }
   }
 ]
```

> 위 JSON 은 실제 출력에서 `Parallel Aware`·`Async Capable`·`Alias`·`Disabled` 네 줄과 줄 끝의 `+` 표시를 지운 것이다.
> 지운 줄은 이 절이 설명하는 네 숫자와 무관하다.

| 칸 | JSON 이름 | 뜻 | 단위 |
|---|---|---|---|
| `cost=` 앞 숫자 | `Startup Cost` | **첫 행을 내놓기까지** 드는 비용 | 임의 단위(디스크 페이지 1장 읽기 = 1.0 기준) |
| `..` 뒤 숫자 | `Total Cost` | **마지막 행까지** 다 내놓는 비용 | 〃 |
| `rows=` | `Plan Rows` | 이 노드가 내놓을 것이라고 **추정한** 행 수 | 행 |
| `width=` | `Plan Width` | 한 행의 **평균 바이트 수** 추정 | 바이트 |

> **비용(cost)** — 초가 아니라 **엔진 내부의 임의 단위**다. 디스크 페이지 하나를 순차로 읽는 비용을 1.0 으로 잡는다.\
> 예: `cost=0.00..3472.00` 은 「3,472 페이지어치 일」이라는 뜻이지 3,472초가 아니다.

**`width` 는 고르는 열에 따라 변한다.** 같은 표, 같은 스캔인데 숫자가 바뀐다.

```text
### SQL: EXPLAIN SELECT * FROM t58_big;
--- PG 18.6 ---
 Seq Scan on t58_big  (cost=0.00..3472.00 rows=200000 width=29)

### SQL: EXPLAIN SELECT id FROM t58_big;
--- PG 18.6 ---
 Seq Scan on t58_big  (cost=0.00..3472.00 rows=200000 width=4)
```

그림 해설 — `width` 가 29 에서 4 로 줄었다(`int` 하나만 고르면 4바이트).\
**`cost` 는 안 줄었다** — 어차피 같은 페이지를 다 읽기 때문이다. **`SELECT *` 를 줄인다고 스캔이 싸지지는 않는다.**

**★ 시작 비용은 「어디서 멈출 수 있나」를 말한다.** 이것이 `LIMIT` 과 만나면 극적으로 보인다.

```text
### SQL: EXPLAIN SELECT id FROM t58_big ORDER BY pad;
--- PG 18.6 (max_parallel_workers_per_gather = 0) ---
 Sort  (cost=25869.64..26369.64 rows=200000 width=25)
   Sort Key: pad
   ->  Seq Scan on t58_big  (cost=0.00..3472.00 rows=200000 width=25)
```

```text
### SQL: EXPLAIN SELECT id FROM t58_big ORDER BY pad LIMIT 1;
--- PG 18.6 (max_parallel_workers_per_gather = 0) ---
 Limit  (cost=4472.00..4472.00 rows=1 width=25)
   ->  Sort  (cost=4472.00..4972.00 rows=200000 width=25)
         Sort Key: pad
         ->  Seq Scan on t58_big  (cost=0.00..3472.00 rows=200000 width=25)
```

```text
 Seq Scan               Sort                      Limit
 시작 0.00              시작 4472.00              전체 4472.00
 전체 3472.00           전체 4972.00
   ^                      ^                         ^
 첫 행이 바로 나온다    정렬이 다 끝나야           자식의 "시작"만 치르면
                       첫 행이 나온다              1행을 얻는다
```

그림 해설 — **`Limit` 의 전체 비용(4472.00)이 자식 `Sort` 의 시작 비용(4472.00)과 정확히 같다.**\
정렬은 첫 행을 내놓기 전에 전부 끝나야 하므로 시작 비용이 크고, `LIMIT 1` 은 그 시작 비용만 치르고 끝난다.\
대가 — `Sort` 노드 자체도 `LIMIT` 때문에 싸졌다(25869 → 4472). 1등만 찾으면 되므로 전량 정렬을 안 한다.

**정렬 키에 인덱스가 있으면 시작 비용이 사라진다.**

```text
### SQL: EXPLAIN SELECT id FROM t58_big ORDER BY id LIMIT 1;
--- PG 18.6 ---
 Limit  (cost=0.42..0.45 rows=1 width=4)
   ->  Index Only Scan using t58_big_pkey on t58_big  (cost=0.42..6679.42 rows=200000 width=4)
```

자식의 전체 비용은 6679 인데 `Limit` 의 전체 비용은 **0.45** 다 — **이미 정렬된 순서로 읽으니 한 행만 꺼내면 된다.**\
[09번](../09-limit-offset-keyset-pagination/)의 키셋 페이지네이션이 서는 토대가 바로 이 계획이다.

---

### 3. ★ 같은 질의, 완전히 다른 두 출력 형식

**언제 쓰나** — 두 엔진을 오갈 때. **형식이 다르다는 것 자체가 이 절의 주제다.**

1절의 질의를 MySQL 에 그대로 던지면 **트리가 아니라 표**가 나온다.

```text
### SQL: EXPLAIN SELECT d.name, count(*) AS c FROM emp e JOIN dept d ON e.dept_id = d.id WHERE e.salary > 100 GROUP BY d.name ORDER BY c DESC LIMIT 2;
--- MySQL 8.4.10 ---
| id | select_type | table | type   | key     | ref             | rows | filtered | Extra                                        |
|  1 | SIMPLE      | e     | ALL    | NULL    | NULL            |    3 |    33.33 | Using where; Using temporary; Using filesort |
|  1 | SIMPLE      | d     | eq_ref | PRIMARY | study.e.dept_id |    1 |   100.00 | NULL                                         |
```

> **표 테두리를 지웠다.** MySQL 의 `EXPLAIN` 표는 12칸이라 그대로 실으면 화면을 넘는다.
> 위는 `partitions`·`possible_keys`·`key_len` 세 칸과 `+---+` 테두리만 지운 것이다. 남긴 칸은 원본 그대로다.

```text
 PostgreSQL 의 EXPLAIN                 MySQL 의 EXPLAIN
 +----------------------------+       +----------------------------+
 | 한 줄 = 한 연산자           |       | 한 줄 = 한 "표에 접근하는 법" |
 | 11줄 (Limit·Sort·Hash…)    |       | 2줄 (e, d)                 |
 | 연산은 노드 이름으로 보인다  |       | 연산은 Extra 칸의 문구로    |
 | 들여쓰기가 부모-자식이다     |       | 줄 순서가 조인 순서다        |
 +----------------------------+       +----------------------------+
```

그림 해설 — **정렬과 집계가 MySQL 표에서는 노드가 아니라 `Extra` 칸의 문구**다(`Using temporary; Using filesort`).\
「어느 표를 어떻게 읽나」는 표 형식이 더 잘 보이고, 「무슨 연산을 어떤 순서로 하나」는 트리가 더 잘 보인다.

**MySQL 표의 칸을 읽는 법**

| 칸 | 뜻 | 무엇을 보나 |
|---|---|---|
| `id` | 셀렉트 블록 번호 | 같은 번호면 같은 블록, 큰 번호가 먼저 돈다 |
| `select_type` | 그 블록의 성격 | `SIMPLE`·`PRIMARY`·`DERIVED`·`SUBQUERY` |
| `table` | 접근 대상 | 별칭이 그대로 뜬다. `<derived2>` 면 임시 결과 |
| **`type`** | **접근 방법** | 좋은 쪽부터 `const` → `eq_ref` → `ref` → `range` → `index` → **`ALL`** |
| `possible_keys` | 쓸 수 있었던 인덱스 | 비어 있으면 애초에 후보가 없었다 |
| **`key`** | **실제로 고른 인덱스** | `NULL` 이면 인덱스를 안 썼다 |
| **`rows`** | 이 표에서 읽을 것이라 **추정한** 행 수 | 곱하면 대략의 작업량이 된다 |
| `filtered` | 그중 조건을 통과할 것이라 추정한 **비율(%)** | `rows × filtered/100` 이 위로 올라갈 행 수 |
| **`Extra`** | 추가로 하는 일 | `Using filesort`·`Using temporary`·`Using index`·`Using where` |

> **`type`** — 「그 표의 행을 어떻게 찾아가나」. `ALL` 은 전부 훑기, `const` 는 상수 한 행, `ref` 는 인덱스로 여러 행,\
> `range` 는 인덱스 범위, `eq_ref` 는 조인 상대마다 정확히 한 행.\
> 예: `type=ALL` 에 `key=NULL` 이면 인덱스를 하나도 안 썼다는 뜻이다.

> **`Extra` 의 `Using filesort`** — **파일에 쓴다는 뜻이 아니다.** 인덱스 순서를 못 써서 **따로 정렬한다**는 뜻이고,\
> 메모리에서 끝날 수도 있다. 예: `ORDER BY pad` 처럼 인덱스 없는 열로 정렬할 때.

**MySQL 에도 트리 형식이 있다 — `FORMAT=TREE` 다.**

```text
### SQL: EXPLAIN FORMAT=TREE (같은 질의)
--- MySQL 8.4.10 ---
-> Limit: 2 row(s)
    -> Sort: c DESC, limit input to 2 row(s) per chunk
        -> Table scan on <temporary>
            -> Aggregate using temporary table
                -> Nested loop inner join  (cost=0.9 rows=1)
                    -> Filter: ((e.salary > 100) and (e.dept_id is not null))  (cost=0.55 rows=1)
                        -> Table scan on e  (cost=0.55 rows=3)
                    -> Single-row index lookup on d using PRIMARY (id=e.dept_id)  (cost=0.35 rows=1)
```

**이제 PG 트리와 나란히 놓고 읽을 수 있다.**

| 하는 일 | PostgreSQL 18.6 | MySQL 8.4.10 (`FORMAT=TREE`) |
|---|---|---|
| 행 제한 | `Limit` | `Limit: 2 row(s)` |
| 정렬 | `Sort` + `Sort Key:` | `Sort: c DESC, limit input to …` |
| 집계 | `HashAggregate` + `Group Key:` | `Aggregate using temporary table` |
| 조인 | `Hash Join` + `Hash Cond:` | `Nested loop inner join` |
| 표 훑기 | `Seq Scan on emp e` | `Table scan on e` |
| 조건 | `Filter:` | `Filter:` |
| 인덱스 한 행 | `Index Scan` + `Index Cond:` | `Single-row index lookup … (id=e.dept_id)` |

★ **연산자 선택 자체는 두 엔진이 달랐다** — PG 는 `Hash Join`, MySQL 은 `Nested loop inner join` 을 골랐다.\
같은 데이터·같은 질의인데 다르다. 이것은 **옵티마이저의 선택**이지 규칙이 아니다. 무엇이 언제 뽑히는지는 [59번](../59-scan-join-sort-operators/)에서 본다.

★ **MySQL 은 `e` 를 먼저 읽고 `d` 를 찾아갔다.** 질의문에 `FROM emp e JOIN dept d` 라고 쓴 순서와 같아 보이지만,\
**그것이 보장은 아니다** — 옵티마이저는 조인 순서를 자유롭게 바꾼다. PG 쪽은 해시 표를 `dept` 로 만들었다(더 작은 쪽).

---

### 4. 계획에 뜨지 않는 것 — `EXPLAIN` 은 질의를 돌리지 않는다

**언제 쓰나** — 계획만 보고 「빠르겠네」라고 판단할 때.

```text
EXPLAIN SELECT …            계획만 만든다. 질의는 안 돈다.  rows= 는 전부 "추정"
EXPLAIN ANALYZE SELECT …    실제로 돌린다.  actual rows= 가 붙는다  <- 60번 주제
```

**그래서 `EXPLAIN` 만으로는 추정이 맞았는지 알 수 없다.** 1절의 PG 계획에서 `rows=377`·`rows=1270` 을 봤는데,\
`emp` 는 4행이고 `dept` 는 3행이다 — 통계가 없어서 나온 기본값이다(예시 데이터 절).\
이 어긋남을 어떻게 읽고 어떻게 고치는지가 [60번](../60-explain-analyze-estimates-vs-actuals/)의 주제다.

**틀린 질의는 계획도 안 나온다 — 파싱·이름 확인은 먼저 한다.**

```text
### SQL: EXPLAIN SELECT * FROM nope;
--- PG 18.6 ---
ERROR:  relation "nope" does not exist
LINE 1: EXPLAIN SELECT * FROM nope;
                              ^
--- MySQL 8.4.10 ---
ERROR 1146 (42S02) at line 1: Table 'study.nope' doesn't exist
```

```text
### SQL: EXPLAIN SELECT id FROM emp WHERE salay > 1;
--- PG 18.6 ---
ERROR:  column "salay" does not exist
LINE 1: EXPLAIN SELECT id FROM emp WHERE salay > 1;
                                         ^
HINT:  Perhaps you meant to reference the column "emp.salary".
```

그림 해설 — **오타는 `EXPLAIN` 단계에서 잡힌다.** 계획을 세우려면 표·열이 실재해야 하기 때문이다.\
`^` 표시와 `HINT` 가 어느 낱말이 문제인지 짚어 준다 — PG 쪽 에러가 더 친절하다.

---

### 5. ★ 논리 순서가 계획 어디로 갔나 — 한 질의에서 전부 짚기

**언제 쓰나** — 01 과 58 을 잇는 자리. **이 절이 이 주제의 과녁이다.**

```sql
SELECT grp, count(*) c FROM t58_big
WHERE id < 5000
GROUP BY grp
HAVING count(*) > 4
ORDER BY c DESC
LIMIT 3;
```

```text
### SQL: EXPLAIN (위 질의)
--- PG 18.6 (max_parallel_workers_per_gather = 0) ---
 Limit  (cost=225.56..225.56 rows=3 width=12)
   ->  Sort  (cost=225.56..226.38 rows=331 width=12)
         Sort Key: (count(*)) DESC
         ->  HashAggregate  (cost=208.85..221.28 rows=331 width=12)
               Group Key: grp
               Filter: (count(*) > 4)
               ->  Index Scan using t58_big_pkey on t58_big  (cost=0.42..183.87 rows=4997 width=4)
                     Index Cond: (id < 5000)
```

> ★ **이 블록은 제출 직전 재확인 시점의 출력이다.** 작성 중 1차 관찰에서는 같은 자리가
> `Index Scan … (cost=0.42..194.45 rows=5259)` 였다 — **표 생성과 `ANALYZE` 를 다시 돌리면 추정치가 흔들린다.**
> **연산자 이름과 트리 모양은 세 번 다 같았고**, 흔들린 것은 `cost` 와 `rows=` 뿐이다.
> 그래서 아래 해설은 숫자가 아니라 **`Index Cond` 라는 이름**을 근거로 쓴다.

```text
### SQL: EXPLAIN FORMAT=TREE (같은 질의)
--- MySQL 8.4.10 ---
-> Limit: 3 row(s)
    -> Sort: c DESC
        -> Filter: (count(0) > 4)
            -> Table scan on <temporary>
                -> Aggregate using temporary table
                    -> Filter: (t58_big.id < 5000)  (cost=1874 rows=9360)
                        -> Index range scan on t58_big using PRIMARY over (id < 5000)  (cost=1874 rows=9360)
```

**논리 절이 계획의 어느 칸이 됐는지 짝지어 보면 이렇다.**

| 01 의 논리 절 | PG 계획에서 | MySQL 계획에서 | 무엇이 달라졌나 |
|---|---|---|---|
| `FROM t58_big` | `Index Scan … on t58_big` | `Index range scan … using PRIMARY` | **표를 순서대로 읽지 않았다** — 인덱스로 들어갔다 |
| `WHERE id < 5000` | `Index Cond: (id < 5000)` | `over (id < 5000)` + `Filter` | **독립 단계가 아니라 스캔 안으로 내려갔다** |
| `GROUP BY grp` | `HashAggregate` + `Group Key: grp` | `Aggregate using temporary table` | 정렬 대신 해시·임시표로 묶었다 |
| `HAVING count(*) > 4` | `Filter:` — **집계 노드에 붙었다** | `Filter: (count(0) > 4)` — **집계 위 별도 노드** | 같은 뜻인데 붙는 자리가 다르다 |
| `SELECT grp, count(*)` | 노드가 없다 | 노드가 없다 | **식 계산은 노드가 안 된다** |
| `ORDER BY c DESC` | `Sort` + `Sort Key:` | `Sort: c DESC` | 그대로 한 노드 |
| `LIMIT 3` | `Limit` | `Limit: 3 row(s)` | 그대로 한 노드 |

★ **짚을 것 셋.**

1. **`WHERE` 는 노드가 아니다.** 인덱스를 탈 수 있으면 `Index Cond` 로 **스캔 안쪽까지** 내려간다.\
   `Index Cond` 는 「인덱스에서 이 범위만 찾아라」이고, `Filter` 는 「읽어 온 뒤 버려라」다 — **비용이 완전히 다르다.**
2. **`SELECT` 목록은 계획에 안 보인다.** 열을 고르고 식을 계산하는 것은 노드가 되지 않는다.\
   그래서 「`SELECT` 를 줄이면 빨라지나」의 답이 2절의 `width` 만 줄고 `cost` 는 그대로였던 것이다.
3. **`HAVING` 의 자리가 두 엔진에서 달랐다.** PG 는 `HashAggregate` 노드 **안에** `Filter` 로 넣었고,\
   MySQL 은 집계 **위에** 별도 `Filter` 노드를 세웠다. 결과는 같다 — **계획의 모양은 결과의 정의가 아니다.**

**같은 질의에서 `Index Cond` 가 `Filter` 였다면 얼마였을까** — 인덱스 스캔을 꺼서 직접 찍어 봤다.

```text
### SQL: SET enable_indexscan=off; SET enable_bitmapscan=off; SET enable_indexonlyscan=off;  (같은 질의)
--- PG 18.6 ---
 Limit  (cost=4013.69..4013.70 rows=3 width=12)
   ->  Sort  (cost=4013.69..4014.52 rows=331 width=12)
         Sort Key: (count(*)) DESC
         ->  HashAggregate  (cost=3996.98..4009.41 rows=331 width=12)
               Group Key: grp
               Filter: (count(*) > 4)
               ->  Seq Scan on t58_big  (cost=0.00..3972.00 rows=4997 width=4)
                     Filter: (id < 5000)
```

**`Index Cond: 183.87` 대 `Filter: 3972.00` — 21배다.** 같은 조건, 같은 결과, 다른 이름.

비용 — 이 질의에서 실제로 무거운 곳은 맨 아래 스캔이고, 위의 세 노드는 그 위에 얹힌 잔돈이다.\
**계획을 읽는 실무 동작은 「가장 큰 `cost` 를 가진 가장 아래 노드를 찾는 것**」이다.

## 문법 — 어느 절에서 무엇이 보이나

SQL 에서 이 절의 본체는 형태가 아니라 「**어느 옵션을 붙이면 무엇이 더 보이나**」다.

```sql
-- PostgreSQL
EXPLAIN SELECT …;
EXPLAIN (ANALYZE) SELECT …;                 -- 실제로 돌린다 (60번)
EXPLAIN (VERBOSE) SELECT …;                 -- Output: 로 열 목록을 보여 준다
EXPLAIN (COSTS OFF) SELECT …;               -- cost= 칸을 지운다 (모양만 볼 때)
EXPLAIN (BUFFERS) SELECT …;                 -- 버퍼 접근 수 (ANALYZE 와 함께)
EXPLAIN (FORMAT JSON|XML|YAML|TEXT) SELECT …;
EXPLAIN (ANALYZE, TIMING OFF, SUMMARY OFF) SELECT …;   -- 시간 칸을 빼 재현성을 높인다

-- MySQL
EXPLAIN SELECT …;                           -- 표 형식 (기본)
EXPLAIN FORMAT=TREE SELECT …;               -- 트리 형식
EXPLAIN FORMAT=JSON SELECT …;
EXPLAIN ANALYZE SELECT …;                   -- 트리 + 실측 (60번)
EXPLAIN FOR CONNECTION <id>;                -- 돌고 있는 다른 세션의 계획
```

- **PG 는 옵션을 괄호 안에 쉼표로** 나열한다. `EXPLAIN ANALYZE SELECT` 처럼 괄호 없이 쓰는 옛 형태도 받는다.
- **MySQL 은 `FORMAT=` 하나**다. `EXPLAIN ANALYZE` 는 언제나 트리 형식이다.
- `EXPLAIN` 만으로는 **질의가 돌지 않는다.** 단 `EXPLAIN ANALYZE` 는 돈다 — PG 에서는 `INSERT`·`UPDATE`·`DELETE` 도 **실제로 반영된다**(60번).
- `VERBOSE` 는 계획 각 노드가 **어떤 열을 위로 올리는지**(`Output:`) 보여 준다.

```text
### SQL: EXPLAIN (VERBOSE) SELECT id, grp FROM t58_big WHERE id = 500;
--- PG 18.6 ---
 Index Scan using t58_big_pkey on public.t58_big  (cost=0.42..8.44 rows=1 width=8)
   Output: id, grp
   Index Cond: (t58_big.id = 500)
```

`width=8` 의 정체가 `Output: id, grp` 다 — `int` 둘이라 4+4 바이트다.

## 어디서 틀리나

| 틀리는 자리 | 무슨 일이 일어나나 | 근거 |
|---|---|---|
| 계획을 위에서 아래로 읽는다 | 실행 순서를 정반대로 이해한다 | 1절 |
| `cost` 를 초로 읽는다 | 「3472초 걸리겠네」 — **임의 단위다** | 2절 |
| `cost` 하나만 본다 | 시작 비용과 전체 비용을 안 나누면 `LIMIT` 의 동작이 안 보인다 | 2절 |
| `rows=` 를 사실로 읽는다 | **추정이다.** `emp` 는 4행인데 `rows=377` 이 나왔다 | 예시 데이터 절 · 60번 |
| `Index Cond` 와 `Filter` 를 같게 본다 | 전자는 **안 읽고 건너뛰고**, 후자는 **읽고 버린다** | 5절 |
| `SELECT` 목록을 줄이면 스캔이 싸질 것 같다 | `width` 만 줄고 `cost` 는 그대로다 | 2절 |
| MySQL `Extra` 의 `Using filesort` 를 「디스크에 쓴다」로 읽는다 | **따로 정렬한다**는 뜻이고 메모리일 수 있다 | 3절 |
| MySQL 표의 줄 순서를 질의문 순서로 읽는다 | 줄 순서는 **조인 순서**이고, 옵티마이저가 바꾼다 | 3절 |
| 한 번 본 계획을 「이 질의의 계획」으로 외운다 | 통계가 흔들리면 바뀐다 | [19번](../19-semi-anti-join/)의 실측 |
| `EXPLAIN` 했으니 질의가 돌았다고 생각한다 | `EXPLAIN` 만으로는 안 돈다. **`EXPLAIN ANALYZE` 는 돈다** | 4절 · 60번 |

## 구현 세부사항 대 언어 보장

| 항목 | 성격 | 근거 |
|---|---|---|
| 계획을 아래에서 위로 읽는 것 | **PG 출력 형식의 규칙** — 문서에 명시 | 1절 |
| `cost` 가 임의 단위인 것 | **PG 문서의 정의** | 2절 |
| 네 칸의 이름(`Startup Cost` 등) | **엔진이 JSON 으로 알려 준다** — 추론 아님 | 2절 |
| `WHERE` 가 `Index Cond` 로 내려가는 것 | **옵티마이저의 선택** — 인덱스가 없으면 `Filter` 가 된다 | 5절 |
| 어느 조인·스캔 연산자가 뽑히나 | **옵티마이저의 선택** — 두 엔진이 실제로 갈렸다 | 3절 |
| `HAVING` 이 붙는 노드의 위치 | **엔진 구현** — PG 는 집계 노드 안, MySQL 은 위 | 5절 |
| `EXPLAIN` 출력 형식 | **엔진마다 완전히 다르다** | 3절 |
| 오타·없는 표가 `EXPLAIN` 에서 잡히는 것 | **양쪽 공통** | 4절 |

★ **이 편의 모든 계획은 「관찰」이다.** [19번](../19-semi-anti-join/)에 같은 서버·같은 버전·같은 데이터에서\
계획이 두 번 달랐던 실측이 있다. 그래서 이 편은 **제출 직전에 모든 계획 블록을 다시 찍어 대조**했고,\
근거로 쓰는 것은 흔들리는 시간이 아니라 **노드 이름·`Index Cond`·칸 이름**이다.

## 언제 쓰고 언제 안 쓰나

```text
 EXPLAIN 으로 충분하다                 EXPLAIN ANALYZE 가 필요하다 (60번)
 +----------------------------+       +----------------------------+
 | 인덱스를 타는지 확인         |       | 추정이 맞았는지 확인         |
 | 조인 순서·방법 확인          |       | 어느 노드에서 시간이 가는지  |
 | 계획의 모양만 볼 때          |       | 행이 어디서 불어나는지       |
 | 돌리면 위험한 질의(대량 갱신)|       | 느린 이유를 짚어야 할 때     |
 +----------------------------+       +----------------------------+
```

- **먼저 `EXPLAIN` 으로 모양을 보고, 필요하면 `EXPLAIN ANALYZE` 로 실측한다.** 순서를 바꾸면 위험하다 —
  `EXPLAIN ANALYZE` 는 질의를 **진짜로 돌린다**(60번).
- 모양만 비교할 때는 `COSTS OFF` 를 붙인다. 숫자가 흔들려도 **모양은 잘 안 흔들린다.**
- 계획을 기록에 남길 때는 **엔진 버전과 찍은 시각**을 같이 적는다. 그것이 없으면 나중에 대조가 안 된다.

## 핵심 문장

1. **계획 트리는 아래에서 위로 읽는다** — 01 의 논리 순서와 방향이 반대다.
2. **논리 절과 계획 노드는 1:1 이 아니다** — `WHERE` 는 스캔 안으로 내려가고, `SELECT` 는 노드가 되지 않는다.
3. **`cost=시작..전체 rows= width=`** — 시작은 첫 행까지, 전체는 마지막 행까지, `rows` 는 추정 행 수, `width` 는 행의 바이트다.
4. **`LIMIT` 의 전체 비용은 자식의 시작 비용과 같다** — 그래서 정렬에 인덱스가 있으면 `LIMIT` 이 거의 공짜다.
5. **PG 는 트리, MySQL 은 표** — MySQL 의 `FORMAT=TREE` 가 그 둘을 나란히 놓게 해 준다.
6. **계획은 관찰이지 보장이 아니다** — 같은 서버·같은 버전에서도 통계가 흔들리면 바뀐다.

## 관련 자료

- [01 논리적 질의 처리 순서](../01-logical-query-processing-order/) — **그쪽은 「결과가 왜 그 값인가」(의미)까지, 여기는 「그 값을 어떤 방법으로 얻나」(실행)부터다.** 별칭을 `WHERE` 에서 못 쓰는 이유는 그쪽, `WHERE` 가 `Index Cond` 가 되는 이유는 여기.
- [13 INNER JOIN](../13-inner-join/) — 1절 계획의 `Hash Join` 이 붙이는 것이 그쪽의 조인이다. **그쪽은 어떤 행이 남나까지, 여기는 그것을 어떤 연산자로 만드나부터.**
- [59 스캔·조인·정렬 연산자](../59-scan-join-sort-operators/) — 이 편은 계획을 **읽는 법**만 다룬다. 어느 연산자가 언제 뽑히는지는 그쪽.
- [60 `EXPLAIN ANALYZE`](../60-explain-analyze-estimates-vs-actuals/) — 이 편의 `rows=` 가 추정이라는 것, 그 추정이 틀리는 것이 그쪽 주제다.
- [09 LIMIT·OFFSET](../09-limit-offset-keyset-pagination/) — 2절의 「시작 비용과 `LIMIT`」이 그 편의 키셋 페이지네이션이 서는 토대다.
- [19 세미·안티 조인](../19-semi-anti-join/) — 같은 서버에서 계획이 두 번 달랐던 실측. 「계획은 관찰이다」의 근거.

## 용어 풀이

- **계획 트리(plan tree)** — 실행할 연산자를 부모-자식으로 엮은 나무. 예: `Sort` 의 자식이 `Seq Scan`.
- **노드(node) / 연산자(operator)** — 계획 트리의 한 칸. 예: `Hash Join`·`Sort`·`Limit`.
- **비용(cost)** — 엔진 내부의 임의 단위. 디스크 페이지 하나 순차 읽기 = 1.0 기준. 예: `cost=0.00..3472.00`.
- **시작 비용(startup cost)** — 첫 행을 내놓기까지의 비용. 예: `Sort` 는 정렬이 끝나야 첫 행이 나오므로 크다.
- **전체 비용(total cost)** — 마지막 행까지 다 내놓는 비용. 예: `Seq Scan` 의 `..3472.00`.
- **`rows=`** — 이 노드가 내놓을 것이라 **추정한** 행 수. 예: `emp` 가 4행인데 `rows=377` 로 나왔다.
- **`width=`** — 한 행의 평균 바이트 추정. 예: `int` 둘이면 `width=8`.
- **`Index Cond`** — 인덱스 안에서 범위를 좁히는 조건. 예: `Index Cond: (id < 5000)` 은 5,000 이상을 **안 읽는다.**
- **`Filter`** — 읽어 온 행을 버리는 조건. 예: `Filter: (salary > 100)` 은 다 읽고 나서 거른다.
- **통계(statistics)** — 옵티마이저가 추정에 쓰는 표·열의 요약값. 예: PG 의 `reltuples`, MySQL 의 인덱스 카디널리티.
- **`type`**(MySQL) — 그 표의 행을 찾아가는 방법. 예: `ALL`(전부 훑기) · `eq_ref`(상대마다 한 행).
- **`Using filesort`**(MySQL) — 인덱스 순서를 못 써서 따로 정렬한다는 뜻. **파일에 쓴다는 뜻이 아니다.**
- **`Using temporary`**(MySQL) — 중간 결과를 임시 표에 담는다는 뜻. 예: `GROUP BY` 를 처리할 때.
- **옵티마이저(optimizer)** — 같은 답을 내는 여러 계획 중 비용이 가장 낮아 보이는 것을 고르는 부분.

## 더 들어가면

- **`EXPLAIN (FORMAT JSON)` 은 도구를 위한 것이다.** 사람이 읽기는 나쁘지만, 계획을 프로그램으로 비교하거나\
  시각화 도구에 넣을 때는 이쪽을 쓴다. 2절에서 칸 이름을 확인하는 데 썼다.
- **`EXPLAIN FOR CONNECTION`**(MySQL) — **지금 돌고 있는 다른 세션의 계획**을 볼 수 있다. 「이 질의가 왜 안 끝나지」를 살아 있는 상태에서 보는 용도다. *(이 편에서는 돌려 보지 않았다.)*
- **병렬 계획** — PG 는 표가 크면 `Gather`·`Parallel Seq Scan` 노드를 쓴다. 이 편의 2절은 읽기를 단순하게 하려고\
  `max_parallel_workers_per_gather = 0` 을 걸고 찍었고, **그 사실을 계획 블록마다 적었다.** 걸지 않으면 같은 질의가\
  `Limit → Gather Merge → Sort → Parallel Seq Scan` 으로 나온다(실제로 그렇게도 찍어 봤다).
- **계획 캐시** — 준비된 문(prepared statement)은 계획을 재사용할 수 있다. 같은 문장인데 어떤 날 갑자기 느려지는\
  현상의 한 원인이다. 그 자체는 이 편의 범위 밖이다.
