# sql/33-재귀 CTE — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력·에러는 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 지어낸 출력은 없다.\
> ★ **무한 재귀는 전부 안전장치를 걸고 돌렸다** — MySQL `cte_max_recursion_depth = 5`, PG `statement_timeout = '300ms'`.\
> 표는 기존 `emp` 만 썼다 — **새로 만든 표가 없다.** 계층은 CTE 안에서 만들었다.\
> 문서 근거는 [PG 18 WITH Queries](https://www.postgresql.org/docs/18/queries-with.html) · [MySQL 8.4 WITH](https://dev.mysql.com/doc/refman/8.4/en/with.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. 세 조각과 회차

**`lvl` 은 1 · 2 · 2 · 3 이 나오고, 엔진은 4회차를 돌고 「재귀 항이 0행을 냈기 때문에」 멈춘다.**

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

**왜 그런가** — 회차마다 입력이 되는 것은 **직전 회차가 새로 만든 행들**뿐이다.

```text
 회차  작업 테이블 W        재귀 항이 찾은 것      결과 R 에 더해진 것
 ----  -------------------  ---------------------  --------------------
  1    (고정점)             ann                    ann            lvl=1
  2    {ann}                mgr_id=1 인 사람       bob, cho       lvl=2
  3    {bob, cho}           mgr_id ∈ {2,3} 인 사람 dan            lvl=3
  4    {dan}                mgr_id=4 인 사람       (없다) 0행  ★ 멈춘다
```

**고정점이 4회차를 만든 것이 아니다** — `dan` 의 부하를 찾으러 갔다가 아무도 못 찾은 그 회차가 네 번째다.\
`lvl = 2` 에 두 행이 있는 것이 **갈래가 둘**이라는 뜻이고, 그것이 곧 나무 모양이다.

---

### 2. `RECURSIVE` 를 빼면

**두 엔진 다 실패한다. MySQL 쪽은 「표 이름 오타」와 구분이 안 된다.**

```text
### SQL: WITH staff AS (...), tree AS ( ... JOIN tree t ... ) SELECT * FROM tree;   -- RECURSIVE 만 뺐다
--- PG 18.6 ---
ERROR:  relation "tree" does not exist
LINE 4: ...id, s.name, s.mgr_id, t.lvl + 1 FROM staff s JOIN tree t ON ...
                                                             ^
DETAIL:  There is a WITH item named "tree", but it cannot be referenced from this part of the query.
HINT:  Use WITH RECURSIVE, or re-order the WITH items to remove forward references.
--- MySQL 8.4.10 ---
ERROR 1146 (42S02) at line 1: Table 'study.tree' doesn't exist
```

**왜 그런가** — `RECURSIVE` 없는 `WITH` 에서 이름은 **위에서 아래로만** 보인다([32번](../32-cte-with-clause/) 3번 절).\
`tree` 를 정의하는 도중에 `tree` 를 부르는 것은 **아직 안 세워진 이름을 부르는 것** — 전방 참조와 같은 취급이다.

★ **MySQL 쪽 메시지가 위험한 이유** — `Table 'study.tree' doesn't exist` 는 **오타로 읽힌다.**\
실제로 MySQL 매뉴얼이 이 오해를 **미리 적어 둔다**.

> "If you forget `RECURSIVE` for a recursive CTE, this error is a likely result: `ERROR 1146 (42S02): Table 'cte_name' doesn't exist`"\
> — [MySQL 8.4 · WITH](https://dev.mysql.com/doc/refman/8.4/en/with.html)

**매뉴얼이 예고할 만큼 흔한 실수다.** PG 는 `HINT: Use WITH RECURSIVE` 라고 답을 그대로 준다.

---

### 3. 고리에 `UNION`

**끝난다. `UNION` 의 중복 제거가 끝나게 했다.**

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

**왜 그런가** — 고리를 한 바퀴 돌아 `ann` 이 다시 나오는 순간, **그 행은 이미 결과에 있으므로 버려진다.** 버리고 나면 새 행이 0개다.

```text
 회차   재귀 항이 만든 행    UNION 이 한 일         새 행 수
 ----   ------------------   --------------------   --------
  1     (고정점) ann                                   1
  2     bob, cho             둘 다 처음               2
  3     dan                  처음                     1
  4     ann                  이미 있다 -> 버린다      0   ★ 멈춘다
```

★ **중복 제거가 안전장치를 겸한 것**이지, 안전장치로 설계된 것이 아니다.\
그래서 **행의 내용이 매번 달라지면 못 막는다**(7번 문항). `UNION` 을 믿을 수 있는 조건은 **재귀 CTE 가 내는 열이 전부 「그 노드의 정체」뿐일 때**다.

---

### 4. 같은 질의를 `UNION ALL` 로

**영원히 돈다. 시험하기 전에 안전장치부터 건다.**

```text
### SQL: SET SESSION cte_max_recursion_depth = 5;      -- ★ 먼저 이것
         WITH RECURSIVE cyc AS (...), t AS (
           SELECT id, name FROM cyc WHERE id = 1
           UNION ALL
           SELECT c.id, c.name FROM cyc c JOIN t ON c.mgr_id = t.id
         ) SELECT * FROM t;
--- MySQL 8.4.10 ---
ERROR 3636 (HY000) at line 2: Recursive query aborted after 6 iterations. Try increasing @@cte_max_recursion_depth to a larger value.

### SQL: SET statement_timeout = '300ms';               -- ★ 먼저 이것
         WITH RECURSIVE cyc AS (...), t AS ( ... UNION ALL ... ) SELECT count(*) FROM t;
--- PG 18.6 ---
ERROR:  canceling statement due to statement timeout
```

**왜 그런가** — `UNION ALL` 은 **아무것도 안 버린다.** 고리를 돌 때마다 같은 행이 또 나오고, 그때마다 새 행이 생기니 종료 조건(0행)이 오지 않는다.

```text
 UNION 의 회차 흐름              UNION ALL 의 회차 흐름
 1: ann                         1: ann
 2: bob, cho                    2: bob, cho
 3: dan                         3: dan
 4: (0행) 끝                    4: ann      <- 또 나온다
                                5: bob, cho
                                6: dan
                                ...  결과가 계속 불어난다
```

★ **안전장치를 거는 순서가 중요하다.** 질의를 던지고 나서 `Ctrl-C` 로 끊는 것은 안전장치가 아니다 —\
서버 쪽은 이미 작업 테이블을 부풀리고 있고, 클라이언트를 끊어도 서버가 계속 돌 수 있다.\
**`SET` 을 같은 세션에서 먼저 실행하고, 그다음 질의를 던진다.**

---

### 5. 두 엔진이 끊는 방식

**MySQL 은 `1000` 을 돌려주고, PG 는 「그런 설정 없다」고 한다.**

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
 MySQL                                PostgreSQL
 기본 1000 회차에서 자동으로 끊긴다    아무도 안 끊는다
   -> 실수해도 ERROR 3636 으로 끝난다    -> 디스크·메모리가 다할 때까지 돈다
   -> 「너무 짧아서」 걸리는 일이 더 흔하다  -> statement_timeout 을 직접 걸어야 한다
```

**운영에서 뜻하는 것.**

- **PG** — `statement_timeout` 을 역할·세션 단위로 걸어 두지 않으면, 재귀 CTE 하나가 **서버를 갉아먹는다.** 그리고 질의에는 깊이 열을 붙인다. **둘 다 한다.**
- **MySQL** — 기본값 1000 이 **정상 질의를 막을 수도 있다.** 깊이 1200 짜리 계층을 펴려면 `SET SESSION cte_max_recursion_depth` 를 올려야 하고, 그때부터는 PG 와 같은 처지가 된다.

★ **PG 의 `unrecognized configuration parameter` 는 「부재의 증거」로 쓸 수 있는 드문 출력이다** — 문서에 없다는 추측이 아니라 **서버가 모른다고 대답했다.**

---

### 6. 깊이 열로 끊기

**5행이 나온다. `ann` 이 두 번 나오는 것이 사이클의 증거다.**

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
  1 | ann  |   4      <- 한 바퀴 돌아 뿌리로 돌아왔다
(5 rows)
```

**왜 그런가** — `ann(1) → cho(3) → dan(4) → ann(1)` 이 고리다. `lvl = 4` 에서 `ann` 이 다시 나왔고, `WHERE t.lvl < 4` 가 그 다음 회차를 막았다.

```text
 lvl=1  ann        <- 시작
 lvl=2  bob, cho   <- ann 의 부하
 lvl=3  dan        <- cho 의 부하
 lvl=4  ann        <- dan 의 부하 = ann  ★ 같은 id 가 또 나왔다 = 사이클
 lvl=5  (WHERE t.lvl < 4 가 막았다)
```

**사이클을 알아보는 법** — **같은 `id` 가 다른 `lvl` 로 두 번 이상** 나오면 고리다.\
`UNION` 이었다면 이 행이 조용히 접혀 **고리가 있었는지조차 모른다** — 3번과 6번의 차이가 그것이다.

★ **멈춘 이유가 「데이터가 다해서」가 아니다.** `WHERE t.lvl < 4` 를 5 로 바꾸면 행이 더 나온다.\
**답이 잘렸는지 보려면 `MAX(lvl)` 을 한도와 비교**해야 한다 — 같으면 잘렸을 가능성이 있다.

---

### 7. 깊이 열과 `UNION` 을 같이 쓰면

**`lvl` 이 매번 달라서 행이 「같은 행」이 되지 않는다. 그래서 안 접힌다.**

```text
 UNION 이 비교하는 것 = 출력 행 전체 (07번의 규칙 그대로)

 lvl 이 없을 때                       lvl 이 있을 때
 (1, 'ann')                           (1, 'ann', 1)
 (1, 'ann')  <- 같다 -> 접힌다         (1, 'ann', 4)  <- 다르다 -> 안 접힌다
                                                  ^
                                       lvl 하나 때문에 영원히 새 행이 나온다
```

**왜 그런가** — `UNION` 의 중복 판정 기준은 **열 하나가 아니라 출력 행 전체**다([07번](../07-distinct-and-duplicate-removal/)의 `DISTINCT` 와 같은 기준).\
깊이 열은 회차마다 증가하도록 만든 열이므로, **설계상 절대 같아질 수 없다.**

**같은 함정이 경로 문자열에도 있다** — `path` 를 누적하면 그것도 매번 달라진다.

그래서 규칙은 이렇게 된다.

| 재귀 CTE 가 내는 열 | 안전장치 |
|---|---|
| 노드의 정체만(id·name) | `UNION` 으로 충분하다 |
| **깊이 열·경로 열이 섞인다** | **`UNION` 은 무력하다.** `WHERE lvl < N` 을 반드시 건다 |
| 둘 다 쓰고 싶다 | 깊이 열로 끊고, 중복은 바깥 `SELECT DISTINCT` 로 지운다 |

---

### 8. `LIMIT` 이 멈춰 주나

**두 엔진이 정확히 반대다.**

| | 바깥 `SELECT` 의 `LIMIT` | CTE 본문 안의 `LIMIT` |
|---|---|---|
| **PG 18.6** | **멈춘다** — 5행이 나온다 | **문법 미구현** — `ERROR` |
| **MySQL 8.4.10** | **안 멈춘다** — `ERROR 3636` | **멈춘다** — 5행이 나온다 |

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

**왜 그런가** — MySQL 매뉴얼이 이유를 적는다.

> "The recursive `SELECT` part of a recursive CTE can also use a `LIMIT` clause… The effect on the result set is the same as when using `LIMIT` in the outermost `SELECT`, **but is also more efficient, since using it with the recursive `SELECT` stops the generation of rows as soon as the requested number of them has been produced.**"\
> — [MySQL 8.4 · WITH](https://dev.mysql.com/doc/refman/8.4/en/with.html)

"본문 안의 것이 **생성을 멈춘다**"는 말은 곧 **바깥 것은 안 멈춘다**는 뜻이고, 위 `ERROR 3636` 이 그것을 실측으로 확인했다.\
PG 는 재귀 CTE 를 **요구된 만큼만 끌어오는 방식**으로 돌리므로 바깥 `LIMIT` 이 그대로 브레이크가 된다.

★ **`LIMIT` 을 종료 조건으로 삼으면 이식되지 않는다.** 네 칸 중 **두 칸이 에러**다.\
이식 가능한 종료 조건은 **깊이 열 하나뿐**이다(6번).

**덧 — PG 의 그 에러는 괄호를 치면 사라진다. 그리고 사라지는 쪽이 더 나쁘다.**

```text
### SQL: WITH RECURSIVE t(n) AS (SELECT 1 UNION ALL (SELECT n+1 FROM t LIMIT 3)) SELECT * FROM t;
--- PG 18.6 (SET statement_timeout='2s') ---
ERROR:  canceling statement due to statement timeout
```

괄호 없이 쓰면 `LIMIT` 이 **CTE 본문 전체**에 걸려 PG 가 `not implemented` 로 거절한다. 괄호를 치면 `LIMIT` 이 **재귀 항 하나**에만 걸리고, 이건 문법상 멀쩡해서 통과한다. 통과했을 뿐 멈추지는 않는다 — 위 타임아웃은 **PG 가 막은 것이 아니라 내가 건 타이머가 막은 것**이고, 타이머가 없었으면 그대로 돌았다.

함정의 모양이 이렇다: 브레이크를 걸려고 `LIMIT` 을 쓴다 → 거절당한다 → 괄호를 쳐 본다 → **통과한다** → 걸렸다고 믿는다. 에러가 사라진 것을 고쳐진 것으로 읽은 것이고, 실제로 없어진 것은 **경고해 주던 유일한 신호**다.\
이유는 3번의 종료 조건으로 돌아간다 — 괄호 친 `LIMIT` 은 **한 회차가 내놓는 행 수**를 자를 뿐 **회차 수**를 건드리지 않는다. 매 회차가 1행씩 내놓는 한 재귀 항이 0행을 내는 순간은 오지 않는다.

---

### 9. 재귀 항에 못 쓰는 것

**셋 다 거부된다. 두 엔진이 같은 셋을 막는다.**

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

**왜 그런가** — 셋 다 **「작업 테이블이 직전 회차 한 덩어리」라는 평가 모델**이 깨지기 때문이다.

```text
 자기 참조 2회    t a 와 t b 가 각각 어느 회차인가?  -> 정의되지 않는다
 집계             아직 다 안 만들어진 것을 요약한다  -> 무엇을 요약하나
 외부 조인        짝이 없어도 NULL 행을 만들어 낸다  -> 0행이 영영 안 온다 = 안 끝난다
```

★ **셋째가 특히 중요하다** — 외부 조인은 **"찾은 게 없어도 행을 만든다"**([14번](../14-left-right-outer-join/)). 재귀의 종료 조건이 바로 그 "찾은 게 없음"이므로, 외부 조인을 허용하면 **종료 조건 자체가 사라진다.**\
그래서 이 금지는 문법 취향이 아니라 **무한 루프를 문법 단계에서 막는 장치**다.

**집계가 필요하면** — 재귀는 전개만 하고, 집계는 바깥 `SELECT` 에서 한다.

---

### 10. MySQL 만 터지는 자리

**PG 는 5행, MySQL 은 `ERROR 1406`. 고정점에서 `CAST` 로 넓히면 고쳐진다.**

```text
### SQL: WITH RECURSIVE p(n, path) AS (SELECT 1, 'a' UNION ALL SELECT n+1, <연결> FROM p WHERE n < 5)
         SELECT * FROM p;
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

**왜 그런가** — MySQL 매뉴얼이 규칙을 적는다.

> "The types of the CTE result columns are inferred from the column types of the **nonrecursive `SELECT` part only**… For type determination, the recursive `SELECT` part is ignored."\
> — [MySQL 8.4 · WITH](https://dev.mysql.com/doc/refman/8.4/en/with.html)

```text
 고정점  SELECT 1, 'a'        ->  path 의 타입·폭이 여기서 확정된다 (1 글자)
 재귀 항 CONCAT(path,'b')     ->  2 글자를 넣으려 한다 -> ERROR 1406
                                  (재귀 항은 타입 결정에서 무시된다)
 PG 는 'a' 가 text 라 폭 개념이 없다 -> 그냥 자란다
```

**고치는 법.**

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

★ **같은 질의를 `emp.name` 으로 쓰면 안 터진다** — `emp.name` 이 `varchar(20)` 이고 가장 긴 경로가 `ann/cho/dan`(11자)이라 들어간다.

```text
### SQL: WITH RECURSIVE staff AS (...), p AS (
           SELECT id, name AS path FROM staff WHERE mgr_id IS NULL
           UNION ALL SELECT s.id, <연결> FROM staff s JOIN p ON s.mgr_id = p.id
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

**그래서 더 위험하다** — 얕을 때 통과하고 **깊어지는 날 운영에서 처음 터진다.**\
[11번](../11-subquery-scalar-correlated-any-all/)의 "오늘 되던 질의가 내일 터진다"와 같은 모양의 사고다.

---

### 11. PG 전용 문법

**`SEARCH` 는 나무 순서 열을, `CYCLE` 은 고리 표시 열을 만들어 준다. MySQL 은 둘 다 `ERROR 1064`.**

```text
### SQL: WITH RECURSIVE cyc AS (...), t AS ( ... UNION ALL ... )
         CYCLE id SET is_cycle USING path SELECT id, name, is_cycle FROM t;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name | is_cycle            ERROR 1064 (42000) at line 1: ... near 'CYCLE id SET is_cycle
----+------+----------           USING path SELECT id, name, is_cycle FROM t' at line 1
  1 | ann  | f
  2 | bob  | f
  3 | cho  | f
  4 | dan  | f
  1 | ann  | t      <- 고리를 닫는 행. 여기서 멈춘다
(5 rows)

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

**`CYCLE` 이 `UNION` 과 다른 점.**

```text
 UNION                              CYCLE
 고리를 조용히 접는다                고리를 만나면 표시하고 멈춘다
 -> 결과 4행. 고리가 있었는지 모른다  -> 결과 5행. 마지막 행에 is_cycle = t
 -> UNION ALL 을 못 쓴다              -> UNION ALL 을 쓰면서도 안전하다
```

**`SEARCH` 의 `ord`** — `{(1),(3),(4)}` 는 **뿌리부터 이 노드까지의 경로**다. 그걸로 정렬하면 나무를 깊이 우선으로 훑은 순서가 나온다.\
`SEARCH BREADTH FIRST` 로 바꾸면 층별 순서가 된다.

★ **MySQL 에는 문법이 아예 없다**(`ERROR 1064` 둘 다). 이식이 필요하면 **깊이 열(6번)과 경로 문자열(10번)을 직접 쓴다** — 그것이 PG 문서가 말하는 "internally rewritten" 의 손으로 쓴 판이다.

---

### 12. 방향 뒤집기

**조인 조건을 `s.id = u.mgr_id` 로 바꾼다. 멈추는 이유는 뿌리의 `mgr_id` 가 `NULL` 이기 때문이다.**

```text
 내려가기 (부하)                     올라가기 (상사)
 JOIN staff s ON s.mgr_id = t.id     JOIN staff s ON s.id = u.mgr_id
                 ^^^^^^^^   ^^^^                    ^^^^   ^^^^^^^^
            새 행의 상사 = 기존 행         새 행 = 기존 행의 상사
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

**왜 멈추는가** — `ann.mgr_id` 가 `NULL` 이라 `s.id = NULL` 이 **모든 행에서 `UNKNOWN`** 이 된다([04번](../04-null-three-valued-logic/)).\
조인이 한 행도 못 맞추니 재귀 항이 0행을 내고, 그것이 종료 조건이다.

★ **뿌리의 `NULL` 이 종료 조건을 겸한다.** 계층 표에서 뿌리를 `NULL` 로 두는 설계가 흔한 이유가 이것이다 —\
`mgr_id = 0` 이나 `mgr_id = 자기 id` 로 두면 **`0` 을 찾으러 가거나 자기를 무한히 찾는다.**

---

### 13. 어디까지가 이 주제인가

**[`algorithm/11-bfs`](../../../../../algorithm/11-bfs/) · [`12-dfs`](../../../../../algorithm/12-dfs/) 를 본다. 여기가 아니다.**

```text
 algorithm/11-bfs · 12-dfs (정본)        sql/33 (여기)
 --------------------------------        --------------------------------
 탐색 순서를 왜 그렇게 정하나             WITH RECURSIVE 의 세 조각
 방문 표시 · 큐와 스택                    고정점 / 재귀 항 / UNION [ALL]
 최단 경로 · 연결 성분 · 복잡도           종료 조건과 안전장치
 가중치 · 우선순위 큐                     두 엔진의 문법·에러·제한
```

**경계 한 줄** — **그래프 탐색 알고리즘 자체는 거기, 여기는 재귀 CTE 의 문법과 종료 조건이다.**

이 주제의 1번 절에 나온 회차 도식(`W = {ann} → {bob, cho} → {dan} → {}`)은 **엔진이 정의한 평가 절차**를 그린 것이지 알고리즘 설명이 아니다.\
그 절차가 결과적으로 너비 우선 탐색과 같은 모양이 되는 것은 사실이지만, **그 사실을 근거로 재귀 CTE 를 탐색 도구로 쓰지 마라** — 방문 표시도, 가중치도, 우선순위도 이 문법에는 없다.

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| 계층 데이터(CTE) 확인 (1번 전) | PG 18.6 · MySQL 8.4.10 | 각 2회 | `staff` · `cyc` |
| 기본 재귀 전개 (1번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `lvl` 1·2·2·3 |
| `RECURSIVE` 누락 (2번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **에러 메시지가 근거다** — PG 의 `HINT` |
| 고리 + `UNION` (3번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **정상 종료** |
| 고리 + `UNION ALL` (4번) | MySQL 8.4.10 · PG 18.6 | 각 1회 | ★ **안전장치 걸고** — `ERROR 3636` / `statement timeout` |
| 깊이 제한 설정 유무 (5번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **PG 의 `unrecognized configuration parameter` 가 근거다** |
| 깊이 열 (6번) | PG 18.6 | 1회 | `ann` 이 두 번 — 사이클이 보인다 |
| 깊이 열 + `UNION` (7번) | — | — | 3번·6번의 출력에서 따라 나온다(별도 실행 아님) |
| `LIMIT` 네 칸 (8번) | PG 18.6 · MySQL 8.4.10 | 각 2회 + 반복 2회 | ★ **안전장치 걸고** · 조인형·계수형 둘 다 |
| 재귀 항 금지 셋 (9번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | **에러 메시지가 근거다** |
| 열 폭 (10번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | `ERROR 1406` → `CAST` → `emp.name` 판 |
| `SEARCH`/`CYCLE` (11번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **MySQL 의 `ERROR 1064` 가 근거다** |
| 올라가기 (12번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | |
| 주제 경계 (13번) | — | — | 실행 대상 아님 |

**안전장치 확인** — 무한 재귀를 던진 문은 4번(2회)·8번(2회) 넷이고, **넷 다 `SET` 을 같은 세션에서 먼저 실행했다.**\
MySQL 은 `cte_max_recursion_depth = 5`(4번) / 기본 1000(8번), PG 는 `statement_timeout = '300ms'`(4번) / `'3s'`(8번).\
실험 뒤 두 서버에 정상 질의를 다시 던져 **응답이 정상임을 확인했고, 남은 세션·임시 객체가 없다** — 재귀 CTE 는 객체를 만들지 않으므로 잔재가 생길 자리가 없다.

**구현 의존 항목** — 5·8번. `cte_max_recursion_depth` 는 **MySQL 의 설정**이고, 바깥 `LIMIT` 이 생성을 멈추느냐는 **엔진의 평가 방식**이다.\
`after 6 iterations`·`after 1001 iterations` 의 **숫자가 설정값보다 1 크다**는 것도 그 엔진의 세는 방식이다 — 값 자체를 외우지 말고 "설정값 근처에서 끊긴다"로 읽는다.

★ **한쪽에서만 결론이 서는 실험** — 4번의 두 에러는 **서로를 대신하지 못한다.**\
`ERROR 3636` 은 MySQL 이 **회차를 세서** 끊은 증거이고, `canceling statement due to statement timeout` 은 PG 가 **시간으로** 끊은 증거다.\
"두 엔진 다 무한 재귀를 막아 준다"로 읽으면 틀린다 — **PG 는 내가 건 타이머가 막은 것이지 PG 가 막은 것이 아니다.**\
11번도 한쪽만 근거다 — MySQL 의 `ERROR 1064` 는 **문법 부재의 근거**일 뿐, `SEARCH`/`CYCLE` 의 동작은 **PG 출력만이 근거**다.

**언어 보장 항목** — 1·2·3·9·12번. 세 조각 구조, `RECURSIVE` 필수, `UNION` 의 고리 끊기, 재귀 항 금지 셋, 종료 조건은 두 엔진에서 같았다(문구만 다르다).\
**방언이 갈리는 항목** — 5·8·10·11번. 깊이 제한 설정의 유무, `LIMIT` 의 위치, 열 폭 확정 규칙, `SEARCH`/`CYCLE` 이다.

**순서 보장** — 없다. 재귀 CTE 의 출력 순서도 보장되지 않는다. 위 출력에 `ORDER BY` 를 붙인 것은 그 때문이고, **깊이 순서가 필요하면 `lvl` 로 정렬**한다.
