# sql/58-`EXPLAIN` 읽기 — 계획 트리의 구조 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 계획·출력·에러는 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 문서를 보고 적은 계획은 없다.\
> **측정 조건** — 숫자 칸(3\~7·12\~14번)은 `study` 안의 **20만 행 표 `t58_big`**(`id` PK · `grp` 인덱스)에서 찍었다.\
> PG 쪽은 `BEGIN … ROLLBACK` 안에서, MySQL 쪽은 `DROP TABLE IF EXISTS` 로 지웠다. **`emp`·`dept` 는 읽기만 했다.**\
> PG 계획 중 `max_parallel_workers_per_gather = 0` 을 건 것은 그 블록에 적었다.\
> ★ **모든 계획 블록은 제출 직전에 다시 찍어 대조했다** — 결과는 맨 끝 「실행 검증」에 있다.\
> 문서 근거는 [PG 18 Using EXPLAIN](https://www.postgresql.org/docs/18/using-explain.html) · [MySQL 8.4 EXPLAIN Output Format](https://dev.mysql.com/doc/refman/8.4/en/explain-output.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. 가장 먼저는 `Seq Scan on emp e`, 가장 나중은 `Limit`

**출력**

```text
### SQL: EXPLAIN SELECT d.name, count(*) AS c FROM emp e JOIN dept d ON e.dept_id = d.id WHERE e.salary > 100 GROUP BY d.name ORDER BY c DESC LIMIT 2;
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

**왜 그런가** — 계획은 **자식이 만든 행을 부모가 받는** 구조다. 자식이 먼저 돌아야 부모가 받을 게 생긴다.

```text
읽는 규칙 1. 들여쓰기가 깊을수록 먼저 돈다
읽는 규칙 2. 한 부모의 자식이 여럿이면 위에 쓰인 자식이 먼저다
```

```text
 순서   노드                              하는 일
  1     Seq Scan on emp e (Filter)        emp 를 훑으며 salary>100 을 거른다
  2     Hash -> Seq Scan on dept d        dept 를 훑어 해시 표를 만든다
  3     Hash Join                         1 의 행을 2 의 해시 표에 비춰 붙인다
  4     HashAggregate                     d.name 으로 묶어 센다
  5     Sort                              count(*) 내림차순
  6     Limit                             2행만 꺼내고 멈춘다
```

**`Hash Join` 의 두 자식은 역할이 다르다.** 아래쪽 `Hash` 가 **먼저 다 돌아 해시 표를 만들어야**\
위쪽 입력을 한 행씩 흘려 보낼 수 있다 — 그래서 `Hash` 쪽을 「빌드(build)」, 다른 쪽을 「프로브(probe)」라 부른다.\
PG 는 **더 작은 쪽으로 해시 표를 만든다**(여기서는 `dept`).

「가장 나중」은 언제나 맨 위 노드이고, 그 노드가 내놓는 행이 곧 질의의 결과다.

---

### 2. `WHERE` 노드는 없다 — `Filter` 가 되어 스캔 안으로 내려갔다

**출력** — 1번 계획의 해당 부분이다.

```text
--- PG 18.6 ---
 ->  Seq Scan on emp e  (cost=0.00..24.12 rows=377 width=4)
       Filter: (salary > 100)
```

**왜 그런가** — 01 의 논리 순서는 **결과의 정의**이지 실행 절차가 아니다.

```text
 01 의 논리 순서 (무엇을)              58 의 물리 계획 (어떻게)
 +---------------------------+        +---------------------------+
 | 1 FROM   emp 를 읽는다     |        | Seq Scan on emp e         |
 | 2 WHERE  salary>100 을 건다|  -->   |   Filter: (salary > 100)  |
 +---------------------------+        +---------------------------+
   두 단계 — "읽고 나서 거른다"          한 단계 — "읽으면서 바로 거른다"
```

**같은 답이 나오기만 하면 엔진은 단계를 합치고, 옮기고, 순서를 바꾼다.**\
걸러진 행은 위 노드로 **올라가지 않으므로**, 합치는 편이 언제나 싸다.

★ **`WHERE` 가 계획에 나타나는 모습은 셋이다.** 어디에 나타나느냐로 비용이 갈린다.

```text
Index Cond:   인덱스에서 그 범위만 찾는다        -> 조건 밖 행은 아예 안 읽는다
Filter:       읽어 온 행을 버린다               -> 다 읽고 나서 버린다
Hash Cond:    조인 조건으로 쓰였다               -> 붙이는 기준이 됐다
```

같은 질의를 MySQL 에 던지면 `WHERE` 는 `Extra` 칸의 **`Using where`** 라는 문구로 나타난다(8번).

---

### 3. 시작 비용 · 전체 비용 · 추정 행 수 · 행의 바이트 수

**출력** — 이름은 지어낼 필요가 없다. 같은 계획을 JSON 으로 찍으면 엔진이 이름을 붙여 준다.

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

> 실제 출력에서 `Parallel Aware`·`Async Capable`·`Alias`·`Disabled` 네 줄과 줄 끝의 `+` 표시를 지웠다.
> 지운 줄은 이 답이 설명하는 네 숫자와 무관하다.

**왜 그런가** — 텍스트 형식의 `cost=0.00..24.12 rows=377 width=4` 와 위 JSON 은 **같은 계획의 같은 숫자**다.

| 텍스트 | JSON 이름 | 뜻 |
|---|---|---|
| `cost=` 앞 | `Startup Cost` | **첫 행**을 내놓기까지의 비용 |
| `..` 뒤 | `Total Cost` | **마지막 행**까지의 비용 |
| `rows=` | `Plan Rows` | 이 노드가 내놓을 것이라 **추정한** 행 수 |
| `width=` | `Plan Width` | 한 행의 평균 **바이트** 추정 |

★ **`rows=377` 인데 `emp` 는 4행이다.** 이 표는 한 번도 `ANALYZE` 된 적이 없다.

```text
### SQL: SELECT c.relname, c.reltuples, c.relpages FROM pg_class c WHERE c.relname IN ('emp','dept');
--- PG 18.6 ---
 relname | reltuples | relpages
---------+-----------+----------
 dept    |        -1 |        0
 emp     |        -1 |        0
(2 rows)
```

`reltuples = -1` 은 「**아직 센 적 없음**」이다. 그래서 `rows=` 는 통계가 아니라 **기본 가정**에서 나왔다.\
**`rows=` 는 언제나 추정이다** — 실측과 얼마나 어긋나는지는 [60번](../60-explain-analyze-estimates-vs-actuals/)의 주제다.

---

### 4. 몇 초도 아니고 밀리초도 아니다 — 임의 단위다

**왜 그런가** — PG 문서가 정의하는 비용의 기준은 「**디스크 페이지 한 장을 순차로 읽는 일 = 1.0**」이다.

```text
cost=3472.00   ->  "3,472 페이지어치 일"      (O)
cost=3472.00   ->  "3,472초"                 (X)
cost=3472.00   ->  "3.472초"                 (X)
```

그래서 **비용끼리는 비교할 수 있어도, 비용을 시간으로 번역할 수는 없다.**\
캐시에 다 올라와 있으면 비싼 계획이 더 빠를 수도 있다.

**시간이 궁금하면 `EXPLAIN ANALYZE` 를 쓴다**(16번 · 60번). 거기에는 `actual time=` 이 붙는다.\
다만 시간은 흔들리므로, 근거로 쓸 때는 **시간이 아니라 `actual rows` 를 본다**([09번](../09-limit-offset-keyset-pagination/)이 그렇게 했다).

---

### 5. `width` 는 줄고 `cost` 는 그대로다

**출력**

```text
### SQL: EXPLAIN SELECT * FROM t58_big;
--- PG 18.6 ---
 Seq Scan on t58_big  (cost=0.00..3472.00 rows=200000 width=29)

### SQL: EXPLAIN SELECT id FROM t58_big;
--- PG 18.6 ---
 Seq Scan on t58_big  (cost=0.00..3472.00 rows=200000 width=4)
```

**왜 그런가**

```text
 SELECT *                              SELECT id
 +---------------------------+         +---------------------------+
 | 같은 페이지를 다 읽는다     |         | 같은 페이지를 다 읽는다     |
 | 한 행에서 29바이트를 올린다 |         | 한 행에서 4바이트를 올린다  |
 | cost 3472 / width 29      |         | cost 3472 / width 4       |
 +---------------------------+         +---------------------------+
   -> 스캔 비용은 "읽은 페이지 수"로 정해진다. 고른 열과 무관하다.
```

행 단위 저장(row store)에서는 **열 하나만 필요해도 그 행이 들어 있는 페이지 전체를 읽는다.**\
그래서 `SELECT *` 를 줄이는 것은 **네트워크로 내보내는 양**을 줄이지, 스캔을 싸게 만들지 않는다.

**스캔 자체를 싸게 하려면 읽을 페이지 수를 줄여야 한다** — 조건으로 좁히거나(`Index Cond`),\
필요한 열이 전부 인덱스에 있어 표를 안 읽게 하거나(`Index Only Scan`). 후자는 [59번](../59-scan-join-sort-operators/)에서 본다.

`width=4` 의 정체는 `VERBOSE` 로 확인된다.

```text
### SQL: EXPLAIN (VERBOSE) SELECT id, grp FROM t58_big WHERE id = 500;
--- PG 18.6 ---
 Index Scan using t58_big_pkey on public.t58_big  (cost=0.42..8.44 rows=1 width=8)
   Output: id, grp
   Index Cond: (t58_big.id = 500)
```

`Output: id, grp` — `int` 둘이라 `width=8` 이다.

---

### 6. `Limit` 의 전체 비용 = 자식 `Sort` 의 **시작** 비용

**출력**

```text
### SQL: EXPLAIN SELECT id FROM t58_big ORDER BY pad;
--- PG 18.6 (max_parallel_workers_per_gather = 0) ---
 Sort  (cost=25869.64..26369.64 rows=200000 width=25)
   Sort Key: pad
   ->  Seq Scan on t58_big  (cost=0.00..3472.00 rows=200000 width=25)

### SQL: EXPLAIN SELECT id FROM t58_big ORDER BY pad LIMIT 1;
--- PG 18.6 (max_parallel_workers_per_gather = 0) ---
 Limit  (cost=4472.00..4472.00 rows=1 width=25)
   ->  Sort  (cost=4472.00..4972.00 rows=200000 width=25)
         Sort Key: pad
         ->  Seq Scan on t58_big  (cost=0.00..3472.00 rows=200000 width=25)
```

**왜 그런가** — 정렬은 **전부 봐야 1등을 안다.** 첫 행을 내놓기 전에 일이 거의 끝나 있다.

```text
 Seq Scan            Sort                    Limit
 시작 0.00           시작 4472.00            시작 4472.00
 전체 3472.00        전체 4972.00            전체 4472.00
   ^                   ^                       ^
 첫 행이 바로 나온다  정렬이 끝나야 첫 행     자식의 "시작"만 치르면 1행을 얻는다
```

`Limit 1` 은 자식에게서 **한 행만** 받는다. 한 행을 받는 데 드는 비용이 곧 자식의 **시작 비용**이므로\
`Limit` 의 전체 비용이 `Sort` 의 시작 비용과 **같은 숫자**(4472.00)가 된다.

★ **`Sort` 자체도 싸졌다** — 25869.64 → 4472.00. `LIMIT` 이 있으면 전량 정렬 대신 **상위 n개만 유지**하면 되기 때문이다.\
「정렬은 무조건 비싸다」가 아니라 「**몇 개가 필요한지 알려 주면 덜 비싸진다**」가 맞다.

*(이 두 블록은 병렬 계획을 끄고 찍었다. 켜 두면 같은 질의가 `Limit → Gather Merge → Sort → Parallel Seq Scan` 으로 나오는데, 그때도 `Limit` 의 전체 비용 4236.83 은 자식 `Gather Merge` 의 시작 비용 4236.72 바로 위였다 — 규칙은 같다.)*

---

### 7. 0.45 — 자식의 전체 비용 6679 와 무관하다

**출력**

```text
### SQL: EXPLAIN SELECT id FROM t58_big ORDER BY id LIMIT 1;
--- PG 18.6 ---
 Limit  (cost=0.42..0.45 rows=1 width=4)
   ->  Index Only Scan using t58_big_pkey on t58_big  (cost=0.42..6679.42 rows=200000 width=4)
```

**왜 그런가** — `id` 에는 기본키 인덱스가 있다. **인덱스는 이미 정렬돼 있다.**

```text
 ORDER BY pad (인덱스 없음)            ORDER BY id (인덱스 있음)
 +---------------------------+        +---------------------------+
 | 20만 행을 다 읽고          |        | 인덱스 맨 앞으로 내려가    |
 | 정렬한 뒤                  |        | 한 행을 꺼낸다             |
 | 1행을 꺼낸다               |        |                           |
 | Limit 전체 4472.00        |        | Limit 전체 0.45           |
 +---------------------------+        +---------------------------+
```

자식의 전체 비용 6679.42 는 「**끝까지 다 읽으면**」의 값이다. `LIMIT 1` 은 끝까지 안 간다.\
**시작 비용 0.42 에 한 행어치(0.03)를 더한 0.45 가 실제로 치르는 값**이다.

★ 이것이 [09번](../09-limit-offset-keyset-pagination/) 키셋 페이지네이션이 서는 토대다 —\
인덱스가 정렬 키를 덮고 있으면 「앞에서 n개」가 거의 공짜이고, `OFFSET` 이 깊어져도 **인덱스에서 그 자리로 바로 내려간다.**

---

### 8. PostgreSQL 은 11줄, MySQL 은 2줄이다

**출력**

```text
--- PG 18.6 ---  (1번의 계획 · 11줄)
 Limit
   ->  Sort
         ->  HashAggregate
               ->  Hash Join
                     ->  Seq Scan on emp e
                     ->  Hash
                           ->  Seq Scan on dept d
```

```text
### SQL: EXPLAIN (같은 질의)
--- MySQL 8.4.10 ---
| id | select_type | table | type   | key     | ref             | rows | filtered | Extra                                        |
|  1 | SIMPLE      | e     | ALL    | NULL    | NULL            |    3 |    33.33 | Using where; Using temporary; Using filesort |
|  1 | SIMPLE      | d     | eq_ref | PRIMARY | study.e.dept_id |    1 |   100.00 | NULL                                         |
```

> **표 테두리를 지웠다.** MySQL `EXPLAIN` 의 12칸 표는 그대로 실으면 화면을 넘는다.
> `partitions`·`possible_keys`·`key_len` 세 칸과 `+---+` 테두리만 지웠고, 남긴 칸은 원본 그대로다.

**왜 그런가** — **한 줄이 세는 단위가 다르다.**

```text
 PostgreSQL: 한 줄 = 한 연산자          MySQL: 한 줄 = 한 "표에 접근하는 법"
 +----------------------------+        +----------------------------+
 | Limit, Sort, HashAggregate |        | e 를 어떻게 읽나            |
 | Hash Join, Hash,           |        | d 를 어떻게 읽나            |
 | Seq Scan x 2               |        |                            |
 | -> 7개 노드 + 조건 줄들     |        | -> 표가 둘이니 두 줄         |
 +----------------------------+        +----------------------------+
   연산이 노드 이름으로 보인다            연산은 Extra 칸의 문구로 보인다
```

MySQL 은 오랫동안 「**조인 순서와 인덱스 선택**」을 보여 주는 도구였고, 그 형식이 남아 있다.\
PG 는 처음부터 **실행 트리 자체**를 찍는다. 그래서 줄 수가 이렇게 벌어진다.

**MySQL 에도 트리 형식이 있다.**

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

★ **연산자 선택은 두 엔진이 달랐다** — PG 는 `Hash Join`, MySQL 은 `Nested loop inner join` 이다.\
같은 데이터·같은 질의인데 다르다. **옵티마이저의 선택**이지 규칙이 아니다([59번](../59-scan-join-sort-operators/)).

★ **MySQL 은 조건에 `and (e.dept_id is not null)` 을 스스로 덧붙였다.** 내부 조인에서 `dept_id` 가 `NULL` 인 행은\
어차피 짝이 없으므로 미리 버린 것이다 — 질의문에 없던 조건이 계획에 생기는 예다([13번](../13-inner-join/)).

---

### 9. `Extra` 칸의 `Using temporary; Using filesort`

**출력** — 8번 MySQL 표의 첫 줄 `Extra` 칸이다.

```text
Extra: Using where; Using temporary; Using filesort
        ^^^^^^^^^^  ^^^^^^^^^^^^^^^  ^^^^^^^^^^^^^^
        WHERE 를 건다  임시 표를 만든다  따로 정렬한다
                       (= GROUP BY)     (= ORDER BY)
```

**왜 그런가** — MySQL 표 형식은 **표마다 한 줄**이다. 정렬·집계는 어느 한 표에 속한 일이 아니므로\
따로 줄을 얻지 못하고 **문구로** 표시된다.

| PG 의 노드 | MySQL 표의 표시 | MySQL `FORMAT=TREE` |
|---|---|---|
| `Sort` | `Extra: Using filesort` | `Sort: c DESC` |
| `HashAggregate` | `Extra: Using temporary` | `Aggregate using temporary table` |
| `Filter` | `Extra: Using where` | `Filter: (…)` |
| `Limit` | (안 보인다) | `Limit: 2 row(s)` |
| `Index Only Scan` | `Extra: Using index` | `Covering index scan …` |

★ **`LIMIT` 은 MySQL 표 형식에 아예 안 나온다.** 표 형식으로는 안 보이는 것이 있다는 뜻이고,\
그래서 8.0 이후로는 **`FORMAT=TREE` 를 기본으로 보는 편**이 PG 와 대조하기에도 낫다.

---

### 10. `ALL`+`NULL` 은 「인덱스를 하나도 안 썼다」, `eq_ref` 는 「상대마다 정확히 한 행」

**출력** — 8번 표의 두 줄이다.

```text
| table | type   | key     | ref             | rows |
| e     | ALL    | NULL    | NULL            |    3 |   <- emp 전체를 훑는다
| d     | eq_ref | PRIMARY | study.e.dept_id |    1 |   <- e 의 행마다 dept 한 행
```

**왜 그런가** — `type` 은 **행을 찾아가는 방법**이고, 좋은 쪽부터 줄을 세울 수 있다.

```text
 좋다 <-------------------------------------------------> 나쁘다
 const  eq_ref   ref    range   index    ALL
   |      |       |       |       |       |
   |      |       |       |       |       +- 표 전체를 훑는다
   |      |       |       |       +--------- 인덱스 전체를 훑는다
   |      |       |       +----------------- 인덱스의 한 범위
   |      |       +------------------------- 인덱스로 여러 행
   |      +--------------------------------- 조인 상대마다 정확히 한 행 (유니크 키)
   +---------------------------------------- 상수 한 행 (기본키 = 상수)
```

- **`type=ALL` + `key=NULL`** — 후보 인덱스도 없고(`possible_keys=NULL`) 쓴 인덱스도 없다. 표를 통째로 읽는다.\
  작은 표에서는 정상이다. 큰 표에서 이게 보이면 **가장 먼저 의심할 줄**이다.
- **`eq_ref`** — 조인의 안쪽 표를 **유니크 인덱스**로 찾는다. `ref` 칸의 `study.e.dept_id` 가 「무엇으로 찾나」다.\
  바깥 행 하나당 안쪽 행이 **최대 하나**라고 옵티마이저가 판단했다는 뜻이다.

**`rows × filtered/100` 이 위로 올라가는 행 수다.** 첫 줄은 `3 × 33.33/100 ≈ 1` 이다.\
`emp` 는 실제로 4행이고 `salary > 100` 인 행은 3행인데 `rows=3`·`filtered=33.33` 으로 잡혔다 —\
**둘 다 추정이고 둘 다 틀렸다.** 이 어긋남이 [60번](../60-explain-analyze-estimates-vs-actuals/)의 주제다.

---

### 11. 아니다 — 「인덱스 순서를 못 써서 따로 정렬한다」는 뜻이다

**왜 그런가** — 이름이 `filesort` 라서 오해를 부르지만, **메모리에서 끝날 수도 있다.**

```text
 Using filesort 가 뜨는 이유            뜨지 않는 경우
 +---------------------------+        +---------------------------+
 | ORDER BY 한 열에          |        | ORDER BY 한 열이           |
 | 쓸 수 있는 인덱스가 없다    |        | 인덱스의 순서와 같다        |
 | -> 행을 모아 따로 정렬한다  |        | -> 읽는 순서가 곧 정렬 순서 |
 +---------------------------+        +---------------------------+
```

```text
### SQL: EXPLAIN SELECT id FROM t58_big ORDER BY pad LIMIT 1;     -- pad 에 인덱스 없음
--- MySQL 8.4.10 ---
| table   | type | key  | rows   | Extra          |
| t58_big | ALL  | NULL | 199680 | Using filesort |

### SQL: EXPLAIN SELECT id FROM t58_big ORDER BY id LIMIT 1;      -- id 는 기본키
--- MySQL 8.4.10 ---
| table   | type  | key     | rows | Extra       |
| t58_big | index | PRIMARY |    1 | Using index |
```

> 표 테두리와 `partitions`·`possible_keys`·`key_len`·`ref`·`filtered` 칸을 지웠다.

**두 번째 줄에서 `rows=1` 이 된 것**에 주목한다 — 인덱스 순서를 그대로 쓰므로 **한 행만 읽고 끝낸다.**\
PG 의 7번 계획(`Limit cost=0.42..0.45`)과 **같은 이야기**를 다른 형식으로 한 것이다.

`Using filesort` 가 정말 디스크를 썼는지는 이 출력으로 알 수 없다. 그것을 보려면 `EXPLAIN ANALYZE` 나\
상태 변수를 봐야 한다 — **`EXPLAIN` 의 문구는 「무엇을 할 작정인가」이지 「무엇을 했나」가 아니다.**

---

### 12. `Index Cond` 는 안 읽고, `Filter` 는 읽고 버린다

**출력**

```text
### SQL: EXPLAIN SELECT grp, count(*) c FROM t58_big WHERE id < 5000 GROUP BY grp HAVING count(*) > 4 ORDER BY c DESC LIMIT 3;
--- PG 18.6 (max_parallel_workers_per_gather = 0) ---
 Limit  (cost=237.48..237.48 rows=3 width=12)
   ->  Sort  (cost=237.48..238.31 rows=332 width=12)
         Sort Key: (count(*)) DESC
         ->  HashAggregate  (cost=220.75..233.19 rows=332 width=12)
               Group Key: grp
               Filter: (count(*) > 4)
               ->  Index Scan using t58_big_pkey on t58_big  (cost=0.42..194.45 rows=5259 width=4)
                     Index Cond: (id < 5000)
```

**왜 그런가**

```text
 Index Cond: (id < 5000)               Filter: (id < 5000) 였다면
 +-----------------------------+      +-----------------------------+
 | 인덱스에서 id<5000 구간만    |      | 20만 행을 전부 읽고          |
 | 찾아 내려간다                |      | 조건에 맞는 것만 남긴다       |
 | 읽는 행: 약 5,000           |      | 읽는 행: 200,000            |
 | cost 0.42..194.45           |      | cost 0.00..3972.00 급       |
 +-----------------------------+      +-----------------------------+
   조건 밖 행은 "존재조차 안 읽는다"     조건 밖 행도 다 읽고 나서 버린다
```

**행 수로 40배, 비용으로 20배 차이**다(`194.45` 대 `3972.00` — 후자는 5번의 `Seq Scan` 비용이다).

★ **같은 `WHERE` 절인데 계획에서 어느 이름으로 뜨는지가 성능을 가른다.**

- `Index Cond` — 인덱스를 **탔다.** 열에 함수를 씌우거나 타입이 안 맞으면 여기로 못 간다([47 인덱스를 언제 타고 언제 안 타나](../47-when-indexes-are-used/)).
- `Filter` — 읽고 나서 버린다. PG 는 `EXPLAIN ANALYZE` 에서 **몇 행을 버렸는지**까지 알려 준다(`Rows Removed by Filter`, 60번).

MySQL 쪽도 같은 구조다 — `Index range scan … over (id < 5000)` 이 `Index Cond` 에 해당한다(13번 출력).

---

### 13. PG 는 `HashAggregate` **안**에, MySQL 은 집계 **위**에 놓는다

**출력**

```text
--- PG 18.6 --- (12번 계획의 일부)
 ->  HashAggregate  (cost=220.75..233.19 rows=332 width=12)
       Group Key: grp
       Filter: (count(*) > 4)        <- 집계 노드 안에 붙었다
```

```text
### SQL: EXPLAIN FORMAT=TREE (같은 질의)
--- MySQL 8.4.10 ---
-> Limit: 3 row(s)
    -> Sort: c DESC
        -> Filter: (count(0) > 4)                            <- 별도 노드다
            -> Table scan on <temporary>
                -> Aggregate using temporary table
                    -> Filter: (t58_big.id < 5000)  (cost=1874 rows=9360)
                        -> Index range scan on t58_big using PRIMARY over (id < 5000)  (cost=1874 rows=9360)
```

**왜 그런가** — `HAVING` 은 **집계가 끝난 뒤의 그룹을 거르는 것**이다. 그 조건을 *집계 노드의 출력 필터로 붙이든*\
*집계 위에 노드를 하나 더 세우든* **결과는 같다.** 어느 쪽을 고를지는 구현이 정한다.

```text
 PostgreSQL                            MySQL
 HashAggregate                         Filter: (count(0) > 4)
   Group Key: grp                        └ Table scan on <temporary>
   Filter: (count(*) > 4)                    └ Aggregate using temporary table
 (한 노드가 묶고 세고 거른다)             (묶고 센 뒤, 임시표를 다시 읽으며 거른다)
```

★ **계획의 모양은 결과의 정의가 아니다.** 두 계획이 다르게 생겼지만 같은 행을 돌려준다.\
그래서 계획을 비교할 때는 **모양이 아니라 「어느 노드에서 행이 몇 개로 줄어드나**」를 본다.

MySQL 이 `count(*)` 를 `count(0)` 으로 바꿔 적은 것도 같은 성격이다 — **의미가 같은 다시 쓰기**다([21번](../21-aggregate-functions-count-forms/)).

---

### 14. 없다 — 식 계산은 노드가 되지 않는다

**왜 그런가** — 12번 계획을 다시 보면 `grp` 를 고르고 `count(*)` 를 계산하는 일에 **해당하는 줄이 없다.**

```text
 노드가 되는 것                        노드가 안 되는 것
 +---------------------------+        +---------------------------+
 | 표를 읽는다 (Scan)         |        | 열을 고른다                |
 | 붙인다 (Join)              |        | 식을 계산한다 (a+b, upper())|
 | 묶는다 (Aggregate)         |        | 별칭을 붙인다               |
 | 줄 세운다 (Sort)           |        | 타입을 변환한다             |
 | 자른다 (Limit)             |        |                           |
 +---------------------------+        +---------------------------+
   행 집합의 모양을 바꾸는 일             한 행 안에서 끝나는 일
```

**행 집합의 모양을 바꾸는 일만 노드가 된다.** 열을 고르고 식을 계산하는 것은 어느 노드든 **지나가면서** 한다.

계획에서 그 흔적을 보려면 `VERBOSE` 를 쓴다 — `Output:` 줄이 「이 노드가 위로 올리는 열」이다(5번).

이것이 5번의 답과 한 이야기다 — **`SELECT` 목록을 줄여도 스캔은 안 싸진다.** 스캔에는 그 일이 없기 때문이다.

---

### 15. 계획이 아니라 에러가 나온다

**출력**

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

**왜 그런가** — 계획을 세우려면 **표와 열이 실재해야 한다.** 어느 인덱스를 쓸지, 몇 바이트짜리 열인지를\
카탈로그에서 읽어야 하기 때문이다. 그래서 `EXPLAIN` 은 **파싱 → 이름 확인 → 계획 수립** 순서로 가고,\
앞 두 단계에서 막히면 계획이 아예 안 나온다.

★ **그래서 `EXPLAIN` 은 문법·오타 검사기로도 쓸 수 있다** — 질의를 돌리지 않고(16번) 이름 오류를 잡는다.\
PG 는 `^` 로 위치를 짚고 `HINT` 로 비슷한 이름까지 제안한다. MySQL 은 「없다」까지만 말한다.

---

### 16. `EXPLAIN` 은 안 돈다. `EXPLAIN ANALYZE` 는 돈다

**왜 그런가**

```text
EXPLAIN SELECT …            계획만 만든다.  rows= 는 전부 추정
        ↓
EXPLAIN ANALYZE SELECT …    실제로 돌린다.  actual rows= 가 붙는다
```

★ **PG 에서는 `EXPLAIN ANALYZE` 가 `INSERT`·`UPDATE`·`DELETE` 도 실제로 반영한다.**\
「계획만 보려고」 던진 문장이 행을 지울 수 있다는 뜻이다. 반드시 **트랜잭션으로 감싼다** — 실측은 [60번](../60-explain-analyze-estimates-vs-actuals/)에 있다.

**그래서 판단 순서는 이렇다.**

```text
1. EXPLAIN 으로 모양을 본다           (안전하다 — 안 돈다)
2. 필요하면 EXPLAIN ANALYZE 로 실측    (돈다 — 변경문이면 트랜잭션으로 감싼다)
```

순서를 바꾸면 위험하다. 특히 **대량 갱신·삭제 질의의 계획이 궁금할 때**는 `EXPLAIN` 만 쓴다.

---

### 17. 달라질 수 있다 — 근거로는 흔들리지 않는 칸을 쓴다

**왜 그런가** — [19번](../19-semi-anti-join/)에 실측이 있다. **버전도 데이터도 안 바꿨는데 MySQL 의 `NOT IN` 계획이 두 번 달랐다.**\
통계 추정이 흔들린 것이 원인이었고, 그 편은 **재확인 시점의 출력으로 갱신하고 드리프트가 있었다는 사실을 본문에 남겼다.**

```text
 흔들리는 칸 (근거로 쓰지 않는다)       흔들리지 않는 칸 (근거로 쓴다)
 +---------------------------+        +---------------------------+
 | actual time=              |        | 노드 이름 (Hash Join …)    |
 | cost= 의 소수점            |        | Index Cond / Filter       |
 | rows= (추정치)             |        | actual rows=              |
 | Buffers 의 hit/read 배분   |        | loops=                    |
 +---------------------------+        +---------------------------+
```

- **계획을 기록에 남길 때는 엔진 버전과 찍은 시각을 같이 적는다.**
- **모양만 비교할 때는 `COSTS OFF`** 를 붙인다. 숫자를 지우면 드리프트에 덜 흔들린다.
- **결론을 계획 하나에 걸지 않는다.** 「이 질의는 해시 조인을 쓴다」가 아니라\
  「이 데이터·이 통계에서는 해시 조인이 뽑혔다」로 적는다.

★ 이 편도 그 규칙을 따랐다 — **본문의 모든 계획 블록을 제출 직전에 다시 찍어 대조했다.** 결과는 바로 아래에 있다.

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| ★ 조인+집계+정렬+LIMIT 계획 (1·8·9번) | PG 18.6 · MySQL 8.4.10 | **각 3회** | 표 형식 · `FORMAT=TREE` 둘 다 |
| `WHERE` 가 `Filter` 로 가는 것 (2번) | PG 18.6 | 2회 | 1번 계획에서 읽음 |
| `FORMAT JSON` 칸 이름 (3번) | PG 18.6 | 1회 | **칸 이름의 근거** |
| `emp`·`dept` 의 통계 상태 (3번) | PG 18.6 | 2회 | `reltuples = -1` |
| `width` 대 `cost` (5번) | PG 18.6 | 각 2회 | `SELECT *` 대 `SELECT id` |
| ★ 정렬 + `LIMIT` 의 시작 비용 (6번) | PG 18.6 | **3회** | 병렬 끈 판 · 켠 판 둘 다 |
| 인덱스 정렬 + `LIMIT` (7번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | PG `cost=0.42..0.45` |
| MySQL `type`·`Extra` (10·11번) | MySQL 8.4.10 | 각 2회 | `ALL`·`eq_ref`·`index` |
| ★ `Index Cond` 대 `Filter` (12번) | PG 18.6 · MySQL 8.4.10 | **각 3회** | 논리 순서 대조의 본문 |
| `HAVING` 의 자리 (13번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **두 엔진이 갈린 자리** |
| `VERBOSE` 의 `Output:` (5·14번) | PG 18.6 | 1회 | `width=8` 의 정체 |
| 없는 표·오타 (15번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **에러가 근거** |
| 병렬 계획 | PG 18.6 | 1회 | 6번 주석의 근거 |

★ **계획 드리프트 재확인(제출 직전)** — 본문의 계획 블록을 전부 다시 찍어 1차 관찰과 대조했다.

```text
 다시 찍어도 같았던 것                        다시 찍었더니 달라진 것
 PG 의 11줄 계획 (1번) — 한 글자도 같음        ★ 12·13번의 cost 와 rows=
 PG 의 FORMAT JSON 칸 이름과 값 (3번)            Index Scan 0.42..194.45 rows=5259  (1차)
 PG 의 t58_big 계획 B1~B7 (5·6·7번)                       0.42..186.23 rows=5075  (2차)
 MySQL 표 형식 (8·10·11번) — rows·filtered 포함           0.42..183.87 rows=4997  (3차·본문)
 MySQL FORMAT=TREE (8번)
 48번 편의 뷰 계획 두 개
```

★ **드리프트가 실제로 있었다.** 원인은 `t58_big` 을 판마다 새로 만들고 `ANALYZE` 를 다시 돌린 것이다 —\
`ANALYZE` 는 표본 조사라 판마다 추정이 조금씩 다르다. **본문 12·13번은 3차(재확인 시점) 출력으로 갱신했다.**

**흔들린 것과 안 흔들린 것이 정확히 갈렸다.**

```text
 흔들렸다                                안 흔들렸다
 cost= 의 값                             연산자 이름 (Index Scan · HashAggregate …)
 rows= (추정)                            Index Cond 와 Filter 의 구분
                                         트리의 모양과 깊이
                                         MySQL 의 type · key · Extra
```

**그래서 이 편의 결론은 전부 오른쪽 칸 위에 세웠다** — 17번의 규칙이 그것이다.\
[59번](../59-scan-join-sort-operators/)에서는 같은 흔들림이 **경계 위에서 연산자까지 뒤집는 것**을 8판 반복으로 관찰했다.


**구현 의존 항목** — 1·8·12·13번의 **연산자 선택과 계획 모양**이다. `Hash Join` 대 `Nested loop`,\
`HAVING` 이 붙는 노드의 위치, `WHERE` 가 `Index Cond` 가 되느냐는 전부 **옵티마이저의 선택**이다.\
재현되는 것은 숫자가 아니라 **읽는 규칙**(아래에서 위로 · 시작/전체 비용의 뜻 · 칸 이름)이다.

**언어 보장 항목** — 3·4·14·15·16번. 네 칸의 이름은 **엔진이 JSON 으로 알려 준 것**이고,\
`cost` 가 임의 단위인 것과 `EXPLAIN` 이 질의를 돌리지 않는 것은 문서에 적혀 있다.\
「`SELECT` 목록이 노드가 되지 않는다」(14번)는 두 엔진의 계획 어디에도 그 줄이 없다는 **관찰**이다.

**버전** — `EXPLAIN FORMAT=TREE` 는 MySQL 8.0.16 부터다. PG 18 은 `actual rows` 를 **소수 둘째 자리까지**\
찍는데(예: `rows=10.00`), 이는 이전 버전과 표기가 다르다. 버전이 오르면 **1·8·12·13번**을 다시 돌린다.
