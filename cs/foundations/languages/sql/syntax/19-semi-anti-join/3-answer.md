# sql/19-세미·안티 조인 — EXISTS·IN·NOT IN·NOT EXISTS — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력은 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 실행 계획도 실제로 받은 것이고, 지어낸 출력은 없다.\
> 표는 기존 `emp`·`dept` 만 썼다 — **새로 만든 표가 없다.**\
> 문서 근거는 [PG 18 Subquery Expressions](https://www.postgresql.org/docs/18/functions-subquery.html) · [MySQL 8.4 EXISTS/NOT EXISTS](https://dev.mysql.com/doc/refman/8.4/en/exists-and-not-exists-subqueries.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. 세미 조인의 세 표기

**(A) 2행 · (B) 2행 · (C) 3행.** 조인만 늘어난다.

```text
### SQL: SELECT d.id, d.name FROM dept d WHERE d.id IN (SELECT e.dept_id FROM emp e) ORDER BY d.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name                       +----+-------+
----+-------                     | id | name  |
 10 | sales                      +----+-------+
 20 | dev                        | 10 | sales |
(2 rows)                         | 20 | dev   |
                                 +----+-------+

### SQL: SELECT d.id, d.name FROM dept d WHERE EXISTS (SELECT 1 FROM emp e WHERE e.dept_id = d.id) ORDER BY d.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name                       +----+-------+
----+-------                     | id | name  |
 10 | sales                      +----+-------+
 20 | dev                        | 10 | sales |
(2 rows)                         | 20 | dev   |
                                 +----+-------+

### SQL: SELECT d.id, d.name FROM dept d JOIN emp e ON e.dept_id = d.id ORDER BY d.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name                       +----+-------+
----+-------                     | id | name  |
 10 | sales                      +----+-------+
 10 | sales                      | 10 | sales |
 20 | dev                        | 10 | sales |
(3 rows)                         | 20 | dev   |
                                 +----+-------+
```

**왜 그런가**

```text
 sales 부서에는 사원이 둘(ann, bob) 있다

 IN / EXISTS : "하나라도 있나?" -> 있다 -> sales 를 한 번 남긴다
 JOIN        : "짝을 다 만들어라" -> ann 과 한 줄, bob 과 한 줄 -> sales 가 두 줄
```

★ **세미 조인의 값은 「행이 안 는다」 하나다.** 그 위에 `COUNT`·`SUM` 을 씌우면 차이가 답을 바꾼다([13번](../13-inner-join/)의 팬아웃).

`DISTINCT` 를 붙이면 조인도 2행이 되지만, **늘렸다가 줄인 것**이다.

```text
### SQL: SELECT DISTINCT d.id, d.name FROM dept d JOIN emp e ON e.dept_id = d.id ORDER BY d.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name                       +----+-------+
----+-------                     | id | name  |
 10 | sales                      +----+-------+
 20 | dev                        | 10 | sales |
(2 rows)                         | 20 | dev   |
                                 +----+-------+
```

---

### 2. `EXISTS` 의 `SELECT` 목록

**안 터진다. `SELECT` 목록은 계산되지 않는다.**

```text
### SQL: SELECT d.id FROM dept d WHERE EXISTS (SELECT 1/0 FROM emp e WHERE e.dept_id = d.id) ORDER BY d.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id                              +----+
----                             | id |
 10                              +----+
 20                              | 10 |
(2 rows)                         | 20 |
                                 +----+

### SQL: SELECT d.id FROM dept d WHERE EXISTS (SELECT NULL FROM emp e WHERE e.dept_id = d.id) ORDER BY d.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id                              +----+
----                             | id |
 10                              +----+
 20                              | 10 |
(2 rows)                         | 20 |
                                 +----+
```

**왜 그런가**

```text
 EXISTS 가 보는 것
   서브쿼리가 행을 하나라도 냈나?  ->  예 / 아니오
        ↑
  "무엇을 냈나"는 안 본다 — 그래서 SELECT 목록을 계산할 이유가 없다
```

```text
 SELECT 1      -> 관례. 아무 뜻 없다
 SELECT NULL   -> 같다
 SELECT *      -> 같다
 SELECT 1/0    -> 같다 (터지지도 않는다)   <- 가장 강한 증거
```

★ **`SELECT *` 가 `SELECT 1` 보다 느리다는 것은 미신이다.** `SELECT 1/0` 이 에러 없이 도는 것이 그 반증이다.\
두 엔진 다 같았다.

---

### 3. 안티 조인의 세 표기

**(A) 0행 · (B) `hr` 1행 · (C) `hr` 1행. 같은 의도인데 `NOT IN` 만 다르다.**

```text
### SQL: SELECT d.id, d.name FROM dept d WHERE d.id NOT IN (SELECT e.dept_id FROM emp e) ORDER BY d.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name                       (빈 결과 — 출력이 한 줄도 없다)
----+------
(0 rows)

### SQL: SELECT d.id, d.name FROM dept d WHERE NOT EXISTS (SELECT 1 FROM emp e WHERE e.dept_id = d.id) ORDER BY d.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name                       +----+------+
----+------                      | id | name |
 30 | hr                         +----+------+
(1 row)                          | 30 | hr   |
                                 +----+------+

### SQL: SELECT d.id, d.name FROM dept d LEFT JOIN emp e ON e.dept_id = d.id WHERE e.id IS NULL ORDER BY d.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name                       +----+------+
----+------                      | id | name |
 30 | hr                         +----+------+
(1 row)                          | 30 | hr   |
                                 +----+------+
```

```text
 (A) NOT IN          0행     <- 틀렸다
 (B) NOT EXISTS      hr      <- 맞다
 (C) LEFT JOIN …     hr      <- 맞다
        ↑
 세 문장이 같은 의도로 쓰였고, 하나만 다른 답을 냈는데 에러는 없다
```

**정답은 `hr` 이다.** `hr`(30번)에 소속된 사원이 하나도 없다.

`NOT IN` 이 왜 0행인지는 4번, `NOT EXISTS` 가 왜 안전한지는 7번이다.

---

### 4. `NOT IN` 이 비는 이유

**`in_res` = `NULL` · `notin_res` = `NULL` · `hit` = `TRUE` 다.**

```text
### SQL: SELECT 30 IN (10,20,NULL) AS in_res, 30 NOT IN (10,20,NULL) AS notin_res, 10 IN (10,20,NULL) AS hit;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 in_res | notin_res | hit        +--------+-----------+------+
--------+-----------+-----       | in_res | notin_res | hit  |
        |           | t          +--------+-----------+------+
(1 row)                          |   NULL |      NULL |    1 |
                                 +--------+-----------+------+
```

**PG 의 빈 칸이 MySQL 의 `NULL` 이다. PG 의 `t` 가 MySQL 의 `1` 이다.** 두 엔진이 같은 값을 냈다.

**계산 과정**

```text
 30 NOT IN (10, 20, NULL)
     ↓  IN 을 OR 로 풀면
 NOT ( 30 = 10   OR   30 = 20   OR   30 = NULL )
        ↓             ↓              ↓
      FALSE         FALSE        UNKNOWN
        ↓
     FALSE OR FALSE = FALSE
     FALSE OR UNKNOWN = UNKNOWN          <- TRUE 가 없으므로 UNKNOWN 이 이긴다
        ↓
 NOT UNKNOWN = UNKNOWN
        ↓
 WHERE 는 UNKNOWN 을 FALSE 와 똑같이 버린다  ->  이 행은 결과에 없다
```

★ **`30` 자리에 무엇을 넣어도 같다.**

```text
 x 가 목록에 있으면    ->  OR 중 하나가 TRUE  ->  NOT TRUE  = FALSE     -> 탈락
 x 가 목록에 없으면    ->  FALSE … UNKNOWN    ->  NOT UNKNOWN = UNKNOWN -> 탈락
                                                        ↓
                                    어느 쪽이든 탈락 — 그래서 언제나 0행
```

**일반화 — 목록에 `NULL` 이 하나라도 있으면 `NOT IN` 은 `TRUE` 가 될 수 없다.**\
이 규칙의 뿌리는 [04번](../04-null-three-valued-logic/)의 3값 논리이고, 거기서 같은 0행을 이미 봤다.

---

### 5. `IN` 은 왜 멀쩡한가

**`IN` 은 `TRUE` 하나면 되고, `NOT IN` 은 `FALSE` 가 전부여야 하기 때문이다.**

```text
 IN     = ( … OR … OR … )          TRUE 가 하나라도 있으면 TRUE
          ↓
   10 IN (10,20,NULL)
   = (10=10) OR (10=20) OR (10=NULL)
   =  TRUE   OR  FALSE  OR UNKNOWN
   =  TRUE                              <- UNKNOWN 이 있어도 TRUE 가 이긴다

 NOT IN = NOT ( … OR … OR … )       OR 전체가 FALSE 여야 TRUE
          ↓
   UNKNOWN 이 하나만 있어도 OR 전체가 FALSE 가 될 수 없다
   -> NOT 의 입력이 FALSE 가 아니다 -> 결과가 TRUE 가 될 수 없다
```

```text
 OR 의 3값 진리표에서
   TRUE  OR 무엇이든    = TRUE        <- IN 을 구해 준다
   FALSE OR UNKNOWN     = UNKNOWN     <- NOT IN 을 죽인다
```

★ **그래서 이 사고는 「테스트로 안 잡힌다」.**

```text
 개발자가 하는 일                          결과
 IN 으로 짜고 돌려 본다      ->  맞는다   ->  "목록은 정상이네"
 조건을 뒤집어 NOT IN 으로   ->  0행      ->  "그런 데이터가 없구나"
                                                ↑
                          맞는지 틀린지 구분할 방법이 결과에 없다
```

---

### 6. 목록이 깨끗하면 안전한가

**아니다. 0행이다. 이번에는 바깥 값이 `NULL` 이라 무너졌다.**

```text
### SQL: SELECT e.name FROM emp e WHERE e.dept_id NOT IN (SELECT d.id FROM dept d) ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name                            (빈 결과 — 출력이 한 줄도 없다)
------
(0 rows)

### SQL: SELECT e.name FROM emp e WHERE NOT EXISTS (SELECT 1 FROM dept d WHERE d.id = e.dept_id) ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name                            +------+
------                           | name |
 dan                             +------+
(1 row)                          | dan  |
                                 +------+
```

**왜 그런가**

```text
 목록은 깨끗하다:    (10, 20, 30)     dept.id 는 PRIMARY KEY 다
 그런데 바깥 값이 NULL:  dan.dept_id

 NULL NOT IN (10, 20, 30)
     ↓
 NOT ( NULL=10  OR  NULL=20  OR  NULL=30 )
        ↓          ↓           ↓
     UNKNOWN    UNKNOWN     UNKNOWN
     ↓
 NOT UNKNOWN = UNKNOWN   ->  dan 탈락
```

★ **`NOT IN` 은 두 방향에서 무너진다.**

| `NULL` 이 어디에 | 무슨 일이 | 얼마나 위험한가 |
|---|---|---|
| **목록 쪽** | 모든 행이 탈락 → **0행** | 0행이라 **이상하다는 건 보인다** |
| **바깥 값 쪽** | `NULL` 인 행만 탈락 | **결과가 그럴듯해서 안 보인다** |

**여기서는 소속 없는 사원이 `dan` 하나뿐이라 0행이 됐지만**, 사원이 100명이고 그중 5명이 소속 없음이라면\
**그 5명만 조용히 빠진 「거의 맞는 목록」**이 나온다. 아무도 모른다.

★ **「목록에 `NULL` 이 없으니 안전하다」는 절반만 맞다.** **비교의 양쪽 모두** `NOT NULL` 이어야 한다.\
그리고 그 보장이 **내일도 유효한지**는 아무도 모른다 — 그래서 결론은 **`NOT EXISTS` 를 쓴다**다.

---

### 7. `NOT EXISTS` 가 안전한 이유

**`NULL` 이 서브쿼리 **안**에서 소비되기 때문이다. 바깥은 「행이 남았나」만 본다.**

```text
 NOT IN 이 하는 일                      NOT EXISTS 가 하는 일
 값 하나를 목록의 값들과 비교한다        조건에 맞는 행을 세어 0 인지 본다
        ↓                                       ↓
 비교에 NULL 이 끼면 UNKNOWN 이 나온다    NULL 은 안쪽 WHERE 가 이미 버린다
        ↓                                       ↓
 그 UNKNOWN 이 바깥 WHERE 로 나간다       바깥이 받는 것은 개수 — 0 아니면 1 이상
        ↓                                       ↓
 세 번째 진릿값이 살아 있다               진릿값이 둘뿐이다
```

**`hr` 을 예로 단계별로**

```text
 NOT EXISTS (SELECT 1 FROM emp e WHERE e.dept_id = 30)

 1) 안쪽 WHERE 가 emp 네 행을 판정한다
      ann  10 = 30  -> FALSE    버림
      bob  10 = 30  -> FALSE    버림
      cho  20 = 30  -> FALSE    버림
      dan  NULL = 30 -> UNKNOWN 버림      <- NULL 이 여기서 끝난다
 2) 남은 행 = 0
 3) EXISTS = FALSE
 4) NOT EXISTS = TRUE           ->  hr 이 남는다
```

★ **3단계에서 이미 `TRUE`/`FALSE` 둘뿐이다.** `UNKNOWN` 이 바깥으로 새 나갈 통로가 구조적으로 없다.

**처방 셋**

| 처방 | 언제 | 대가 |
|---|---|---|
| **`NOT EXISTS` 로 바꾼다** | **기본 선택** | 없음. 상관 서브쿼리라 조금 길다 |
| 서브쿼리에 `IS NOT NULL` 을 건다 | `NOT IN` 형태를 유지해야 할 때 | 누가 지우면 다시 터진다. **바깥 값 쪽은 못 막는다** |
| 그 열에 `NOT NULL` 제약을 건다 | 설계를 고칠 수 있을 때 | 데이터 정리가 필요하다. 대신 영구히 안 터진다 |

```text
### SQL: SELECT d.id, d.name FROM dept d
         WHERE d.id NOT IN (SELECT e.dept_id FROM emp e WHERE e.dept_id IS NOT NULL) ORDER BY d.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name                       +----+------+
----+------                      | id | name |
 30 | hr                         +----+------+
(1 row)                          | 30 | hr   |
                                 +----+------+
```

**두 번째 처방이 6번의 사고는 못 막는다는 점을 잊지 마라** — 그쪽은 바깥 값이 `NULL` 이었다.

---

### 8. `IS NULL` 을 걸 열 고르기

**2행이 된다. 사원이 있는 `dev` 까지 「빈 부서」로 잡힌다.**

```text
### SQL: SELECT d.id, d.name FROM dept d LEFT JOIN emp e ON e.dept_id = d.id
         WHERE e.salary IS NULL ORDER BY d.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name                       +----+------+
----+------                      | id | name |
 20 | dev                        +----+------+
 30 | hr                         | 20 | dev  |
(2 rows)                         | 30 | hr   |
                                 +----+------+
```

**왜 그런가**

```text
 LEFT JOIN 의 결과 (걸러지기 전)
 d.name  | e.name | e.id  | e.salary
 --------+--------+-------+----------
 sales   | ann    |   1   |   300
 sales   | bob    |   2   |   500
 dev     | cho    |   3   |   NULL     <- 원래부터 NULL 인 값
 hr      | (없음) | NULL  |   NULL     <- 짝이 없어 채워진 NULL

 e.id IS NULL      ->  hr 만            (id 는 PRIMARY KEY 라 원래 NULL 일 수 없다)
 e.salary IS NULL  ->  dev + hr         (두 종류의 NULL 이 섞인다)
```

★ **`LEFT JOIN` 뒤에는 `NULL` 이 두 종류다.**

```text
 (가) 원래 값이 NULL 인 것          cho.salary
 (나) 짝이 없어 채워진 NULL         hr 행 전체
        ↑
  안티 조인은 (나) 만 찾고 싶은데, NULL 가능한 열로 보면 (가) 도 잡힌다
```

**규칙 — `IS NULL` 은 `NOT NULL` 인 열에 건다.** 보통 오른쪽 표의 기본키다.

★ **`NOT EXISTS` 에는 이 함정이 없다.** 열을 고를 일 자체가 없기 때문이다.\
그래서 세 형태 중 **`NOT EXISTS` 가 가장 실수하기 어렵다.**

`LEFT JOIN` 뒤 조건의 자리 문제는 [15번](../15-on-vs-where-in-outer-join/)이 정본이다 — 이 조건을 `ON` 으로 옮기면 안티 조인이 아예 무너진다.

---

### 9. `IN` 과 `EXISTS` 의 계획

**두 엔진 모두 한 글자도 다르지 않다.**

```text
### SQL: EXPLAIN SELECT d.id, d.name FROM dept d WHERE d.id IN (SELECT e.dept_id FROM emp e);
--- PG 18.6 ---
 Hash Join  (cost=28.62..61.72 rows=635 width=36)
   Hash Cond: (d.id = e.dept_id)
   ->  Seq Scan on dept d  (cost=0.00..22.70 rows=1270 width=36)
   ->  Hash  (cost=26.12..26.12 rows=200 width=4)
         ->  HashAggregate  (cost=24.12..26.12 rows=200 width=4)
               Group Key: e.dept_id
               ->  Seq Scan on emp e  (cost=0.00..21.30 rows=1130 width=4)

### SQL: EXPLAIN SELECT d.id, d.name FROM dept d WHERE EXISTS (SELECT 1 FROM emp e WHERE e.dept_id = d.id);
--- PG 18.6 ---
 Hash Join  (cost=28.62..61.72 rows=635 width=36)
   Hash Cond: (d.id = e.dept_id)
   ->  Seq Scan on dept d  (cost=0.00..22.70 rows=1270 width=36)
   ->  Hash  (cost=26.12..26.12 rows=200 width=4)
         ->  HashAggregate  (cost=24.12..26.12 rows=200 width=4)
               Group Key: e.dept_id
               ->  Seq Scan on emp e  (cost=0.00..21.30 rows=1130 width=4)
```

```text
### SQL: EXPLAIN FORMAT=TREE SELECT d.id, d.name FROM dept d WHERE d.id IN (SELECT e.dept_id FROM emp e);
--- MySQL 8.4.10 ---
-> Nested loop inner join  (cost=1.45 rows=4)
    -> Filter: (`<subquery2>`.dept_id is not null)  (cost=0.988..0.8 rows=4)
        -> Table scan on <subquery2>  (cost=1.69..3.6 rows=4)
            -> Materialize with deduplication  (cost=1.05..1.05 rows=4)
                -> Filter: (e.dept_id is not null)  (cost=0.65 rows=4)
                    -> Table scan on e  (cost=0.65 rows=4)
    -> Single-row index lookup on d using PRIMARY (id=`<subquery2>`.dept_id)  (cost=0.35 rows=1)

### SQL: EXPLAIN FORMAT=TREE SELECT d.id, d.name FROM dept d WHERE EXISTS (SELECT 1 FROM emp e WHERE e.dept_id = d.id);
--- MySQL 8.4.10 ---
-> Nested loop inner join  (cost=1.45 rows=4)
    -> Filter: (`<subquery2>`.dept_id is not null)  (cost=0.988..0.8 rows=4)
        -> Table scan on <subquery2>  (cost=1.69..3.6 rows=4)
            -> Materialize with deduplication  (cost=1.05..1.05 rows=4)
                -> Filter: (e.dept_id is not null)  (cost=0.65 rows=4)
                    -> Table scan on e  (cost=0.65 rows=4)
    -> Single-row index lookup on d using PRIMARY (id=`<subquery2>`.dept_id)  (cost=0.35 rows=1)
```

★ **비용 숫자까지 같다.** 두 문법이 같은 의미로 정규화됐다는 뜻이다.

```text
 두 엔진이 공통으로 한 일
   오른쪽(emp.dept_id)을 먼저 중복 제거한다      PG: HashAggregate
                                                MySQL: Materialize with deduplication
        ↓
   그 결과와 왼쪽을 붙인다
        ↓
   "여러 짝"이 애초에 안 생긴다 — 그래서 행이 안 는다
```

**「`IN` 이 느리니 `EXISTS` 로 바꿔라」는 이 판에서는 근거가 없다.**\
느린 질의를 고칠 때 볼 것은 **문법이 아니라 인덱스·통계·조인 순서**다(목록의 **47번**·**58번 주제**).

> **재현 주** — PG 의 추정 행 수(`rows=1130`·`rows=1270`)는 **통계가 없을 때의 기본값**이다. 두 표가 작아 실제(4·3)와 무관하다.\
> **여기서 볼 것은 비용 수치가 아니라 계획의 모양과 연산자 이름**이고, 통계가 쌓이면 수치는 달라질 수 있다.

---

### 10. `JOIN + DISTINCT` 의 계획

**중복 제거가 조인 「뒤」로 간다. `IN`/`EXISTS` 는 「앞」이다.**

```text
### SQL: EXPLAIN SELECT DISTINCT d.id, d.name FROM dept d JOIN emp e ON e.dept_id = d.id;
--- PG 18.6 ---
 HashAggregate  (cost=68.50..79.80 rows=1130 width=36)
   Group Key: d.id, d.name
   ->  Hash Join  (cost=38.58..62.85 rows=1130 width=36)
         Hash Cond: (e.dept_id = d.id)
         ->  Seq Scan on emp e  (cost=0.00..21.30 rows=1130 width=4)
         ->  Hash  (cost=22.70..22.70 rows=1270 width=36)
               ->  Seq Scan on dept d  (cost=0.00..22.70 rows=1270 width=36)
--- MySQL 8.4.10 (FORMAT=TREE) ---
-> Table scan on <temporary>  (cost=2.75..4.44 rows=3)
    -> Temporary table with deduplication  (cost=1.9..1.9 rows=3)
        -> Nested loop inner join  (cost=1.6 rows=3)
            -> Filter: (e.dept_id is not null)  (cost=0.55 rows=3)
                -> Table scan on e  (cost=0.55 rows=3)
            -> Single-row index lookup on d using PRIMARY (id=e.dept_id)  (cost=0.283 rows=1)
```

```text
 IN / EXISTS                          JOIN + DISTINCT
 +--------------------------+         +--------------------------+
 | 1. 오른쪽을 접는다(dedup) |         | 1. 조인한다 (행이 는다)   |
 | 2. 조인한다               |         | 2. 접는다 (dedup)         |
 +--------------------------+         +--------------------------+
   중간 결과가 안 커진다                 중간 결과가 커졌다 줄어든다
```

**두 엔진이 같은 이야기를 한다** — PG 는 `HashAggregate` 가 `Hash Join` **위**에, MySQL 은 `Temporary table with deduplication` 이 `Nested loop` **위**에 있다.

★ **결과가 같다고 같은 질의가 아니다.** 팬아웃이 큰 1:N 에서는 중간 결과 크기가 다르고, 그것이 메모리·디스크 사용으로 나타난다.

그리고 **`DISTINCT` 는 「존재 여부」가 아니라 「중복 제거」를 시킨 것**이라, `SELECT` 목록에 열을 하나 더하면 조용히 중복이 되살아난다. 세미 조인에는 그 위험이 없다.

---

### 11. `NOT EXISTS` 와 `NOT IN` 의 계획

**`NOT EXISTS` 만 안티 조인 연산자가 된다. `NOT IN` 은 필터 속 서브쿼리로 남는다.**

```text
### SQL: EXPLAIN SELECT d.id, d.name FROM dept d WHERE NOT EXISTS (SELECT 1 FROM emp e WHERE e.dept_id = d.id);
--- PG 18.6 ---
 Hash Right Anti Join  (cost=38.58..69.13 rows=635 width=36)
   Hash Cond: (e.dept_id = d.id)
   ->  Seq Scan on emp e  (cost=0.00..21.30 rows=1130 width=4)
   ->  Hash  (cost=22.70..22.70 rows=1270 width=36)
         ->  Seq Scan on dept d  (cost=0.00..22.70 rows=1270 width=36)
--- MySQL 8.4.10 (FORMAT=TREE) ---
-> Hash antijoin (e.dept_id = d.id)  (cost=1.86 rows=12)
    -> Covering index scan on d using name  (cost=0.65 rows=4)
    -> Hash
        -> Table scan on e  (cost=0.413 rows=3)
### SQL: EXPLAIN SELECT d.id, d.name FROM dept d WHERE d.id NOT IN (SELECT e.dept_id FROM emp e);
--- PG 18.6 ---
 Seq Scan on dept d  (cost=24.12..50.00 rows=635 width=36)
   Filter: (NOT (ANY (id = (hashed SubPlan 1).col1)))
   SubPlan 1
     ->  Seq Scan on emp e  (cost=0.00..21.30 rows=1130 width=4)
--- MySQL 8.4.10 (FORMAT=TREE) ---
-> Filter: <in_optimizer>(d.id,<exists>(select #2) is false)  (cost=0.65 rows=4)
    -> Covering index scan on d using name  (cost=0.65 rows=4)
    -> Select #2 (subquery in condition; dependent)
        -> Limit: 1 row(s)  (cost=0.417 rows=1)
            -> Filter: <is_not_null_test>(e.dept_id)  (cost=0.417 rows=1.67)
                -> Filter: ((<cache>(d.id) = e.dept_id) or (e.dept_id is null))  (cost=0.417 rows=1.67)
                    -> Table scan on e  (cost=0.417 rows=3)
```

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| `NOT EXISTS` | **`Hash Right Anti Join`** | **`Hash antijoin`** |
| `NOT IN` | `Seq Scan` + `Filter: NOT (ANY …)` + `SubPlan` | `Filter: <in_optimizer>(… is false)` + 서브쿼리 |

★ **두 엔진이 「안티 조인」이라는 말을 자기 계획에 직접 쓴다.** 이 주제의 이름이 계획에 그대로 나온다.

**MySQL 계획에 `NULL` 처리가 글자로 드러나 있다.**

```text
 Filter: <in_optimizer>(d.id, <exists>(select #2) is false)
                                                  ↑
            TRUE 가 아니라 "FALSE 인 경우" 를 따로 지목한다
            (IN 의 결과가 TRUE / FALSE / NULL 셋이기 때문)

 Filter: ((<cache>(d.id) = e.dept_id) or (e.dept_id is null))
                                          ↑
            "값이 같거나, 아니면 NULL 이거나" 를 조건에 끼워 넣었다
            = NULL 이 있으면 "모른다" 를 만들어 내기 위한 장치
```

**안티 조인으로 바꿨다면 이 두 장치가 전부 사라진다** — 그리고 답도 달라진다.

**실제로 돈 것까지 확인한다.**

```text
### SQL: EXPLAIN (ANALYZE, COSTS OFF, TIMING OFF, SUMMARY OFF, BUFFERS OFF)
         SELECT d.id FROM dept d WHERE NOT EXISTS (SELECT 1 FROM emp e WHERE e.dept_id = d.id);
--- PG 18.6 ---
 Hash Right Anti Join (actual rows=1.00 loops=1)
   Hash Cond: (e.dept_id = d.id)
   ->  Seq Scan on emp e (actual rows=4.00 loops=1)
   ->  Hash (actual rows=3.00 loops=1)
         Buckets: 2048  Batches: 1  Memory Usage: 17kB
         ->  Seq Scan on dept d (actual rows=3.00 loops=1)

### SQL: EXPLAIN (ANALYZE, COSTS OFF, TIMING OFF, SUMMARY OFF, BUFFERS OFF)
         SELECT d.id FROM dept d WHERE d.id NOT IN (SELECT e.dept_id FROM emp e);
--- PG 18.6 ---
 Seq Scan on dept d (actual rows=0.00 loops=1)
   Filter: (NOT (ANY (id = (hashed SubPlan 1).col1)))
   Rows Removed by Filter: 3
   SubPlan 1
     ->  Seq Scan on emp e (actual rows=4.00 loops=1)
```

★ **`Rows Removed by Filter: 3`** — `hr` 을 포함한 **세 행이 전부** 떨어졌다는 사실이 계획에 숫자로 찍힌다.\
`actual rows=0.00` 은 "데이터가 없어서"가 아니라 "전부 걸러져서"다. **그 구분이 계획에는 남아 있다.**

---

### 12. `NOT IN` 이 그 연산자를 못 쓰는 이유

**안티 조인은 두 값짜리 연산인데 `NOT IN` 은 세 번째 값을 내야 하기 때문이다. 느린 게 아니라 다른 연산이다.**

```text
 안티 조인이 하는 일
   왼쪽 행마다: 오른쪽에 짝이 있나?
      있다  -> 버린다
      없다  -> 남긴다
        ↑
   두 갈래뿐이다

 NOT IN 이 해야 하는 일
   왼쪽 값마다: 목록의 모든 값과 다른가?
      하나와 같다        -> FALSE    -> 버린다
      전부 다르다(확실)  -> TRUE     -> 남긴다
      모르겠다(NULL 때문)-> UNKNOWN  -> 버린다   <- 세 번째 갈래
        ↑
   "버린다"가 두 가지 이유로 나온다
```

```text
 만약 옵티마이저가 NOT IN 을 안티 조인으로 바꾼다면

   안티 조인 : "짝이 없으니 남긴다"  ->  hr 을 내놓는다
   NOT IN    : "모르니 버린다"       ->  0행
        ↑
   답이 달라진다 — 그래서 바꿀 수 없다
```

★ **이것이 「`NOT IN` 이 느리다」는 흔한 설명이 틀린 이유다.**\
옵티마이저는 **같은 답이 나오는 변환만** 할 수 있고, `NOT IN` 의 의미가 안티 조인과 다르므로 그 변환이 금지된다.\
그 결과가 느린 계획으로 **나타날 뿐**이다.

**따라서 처방도 달라진다.**

```text
 "느려서 문제" 라면    ->  인덱스를 걸거나 통계를 갱신한다
 "의미가 달라서 문제"  ->  질의를 NOT EXISTS 로 고친다        <- 이쪽이다
```

**한쪽이라도 `NOT NULL` 이 보장되면 옵티마이저가 변환할 수 있게 된다** — 이것이 `NOT NULL` 제약이 세 번째 처방인 이유다.\
MySQL 계획의 `Filter: (e.dept_id is not null)` 이 그 사정을 보여 준다 — **`NULL` 을 미리 빼야 다음 단계로 갈 수 있다.**

---

### 13. `LEFT JOIN … IS NULL` 의 계획

**두 엔진이 갈렸다. MySQL 은 안티 조인으로 바꿨고, PG 는 외부 조인 + 필터로 남겼다.**

```text
### SQL: EXPLAIN SELECT d.id, d.name FROM dept d LEFT JOIN emp e ON e.dept_id = d.id WHERE e.id IS NULL;
--- PG 18.6 ---
 Hash Right Join  (cost=38.58..62.85 rows=6 width=36)
   Hash Cond: (e.dept_id = d.id)
   Filter: (e.id IS NULL)
   ->  Seq Scan on emp e  (cost=0.00..21.30 rows=1130 width=8)
   ->  Hash  (cost=22.70..22.70 rows=1270 width=36)
         ->  Seq Scan on dept d  (cost=0.00..22.70 rows=1270 width=36)
--- MySQL 8.4.10 (FORMAT=TREE) ---
-> Filter: (e.id is null)  (cost=1.79 rows=4)
    -> Hash antijoin (e.dept_id = d.id)  (cost=1.79 rows=4)
        -> Covering index scan on d using name  (cost=0.65 rows=4)
        -> Hash
            -> Table scan on e  (cost=0.138 rows=3)
```

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| `LEFT JOIN … IS NULL` | `Hash Right Join` + `Filter` | **`Hash antijoin`** + `Filter` |
| `NOT EXISTS` | `Hash Right Anti Join` | `Hash antijoin` |

★ **MySQL 은 `LEFT JOIN … IS NULL` 을 `NOT EXISTS` 와 같은 연산자로 처리했다.** PG 는 안 그랬다.

```text
 이 관찰에서 외울 것과 외우면 안 될 것

 외울 것        : 세 형태의 "결과"는 정의돼 있다 — NOT IN 만 다르다
 외우면 안 될 것 : "MySQL 은 바꾸고 PG 는 안 바꾼다"
                    ↑
        이것은 이 데이터·이 통계·이 버전에서의 옵티마이저 선택이다
```

**이 한 줄이 이 문항의 요점이다** — **결과는 언어가 보장하고, 계획은 아무도 보장하지 않는다.**\
계획 비교는 「왜 이 문법을 고르나」를 이해하는 데 쓰고, **「이 문법이 항상 빠르다」로 일반화하지 않는다.**

셋 중 무엇을 쓸지는 그래서 **성능이 아니라 정확성과 읽기 쉬움**으로 고른다.

| 형태 | 결과 | 실수하기 쉬운가 | 권장 |
|---|---|---|---|
| `NOT EXISTS` | 정확 | **가장 어렵다** — 고를 열이 없다 | ★ 기본 |
| `LEFT JOIN … IS NULL` | 정확 (열을 맞게 골랐을 때) | `NULL` 가능 열을 고르면 틀린다 | 오른쪽 다른 열도 볼 때 |
| `NOT IN` | **`NULL` 이 있으면 틀린다** | 양쪽 다 위험 | 쓰지 않는다 |

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| 세미 조인 세 표기 (1번) | PG 18.6 · MySQL 8.4.10 | 각 4회 | `DISTINCT` 형까지 |
| `EXISTS` 의 `SELECT` 목록 (2번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **`SELECT 1/0` 이 안 터진 것이 근거다** |
| 안티 조인 세 표기 (3번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | **`NOT IN` 만 0행** |
| `NOT IN` 식 계산 (4번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `30 IN/NOT IN (10,20,NULL)` |
| 바깥 값이 `NULL` (6번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **목록이 깨끗해도 0행** |
| `IS NOT NULL` 처방 (7번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | |
| `IS NULL` 열 고르기 (8번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **`e.salary IS NULL` 이 2행** |
| `IN`/`EXISTS` 계획 (9번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **두 엔진 다 완전히 같은 계획** |
| `JOIN`+`DISTINCT` 계획 (10번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | dedup 이 조인 뒤로 간다 |
| `NOT EXISTS`/`NOT IN` 계획 (11번) | PG 18.6 · MySQL 8.4.10 | 각 2회 + PG `ANALYZE` 2회 | **`Anti Join` 연산자 이름** · `Rows Removed by Filter: 3` |
| `LEFT JOIN … IS NULL` 계획 (13번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **여기서만 두 엔진이 갈렸다** |

**구현 의존 항목** — 9~13번의 **계획 전부**다. 연산자 이름·모양·비용은 옵티마이저의 선택이고, 통계·버전에 따라 달라질 수 있다.\
추정 행 수는 **통계가 없을 때의 기본값**이라 재현되지 않을 수 있다. 볼 것은 모양과 연산자 이름이다.

★ **추측이 아니라 실측이다** — 작성 중 한 번, 제출 전 한 번 **같은 서버·같은 버전**에서 같은 계획을 찍었더니\
**MySQL 의 `NOT IN` 계획이 달랐다**(`run only once` + `Materialize with deduplication` → `dependent` + `or (e.dept_id is null)`).\
바뀐 것은 MySQL 의 추정 행 수(`rows=4` → `rows=3`)뿐이고, **버전도 데이터도 안 건드렸다.**\
같은 두 번 사이에 **PG 계획은 한 글자도 안 달라졌고, 결과는 양쪽 다 똑같았다.**\
위에 실은 계획은 **제출 전 재확인 시점의 출력**이다. 수렴 관찰(`IN` = `EXISTS`)·안티 조인 연산자·`NOT IN` 이 안티 조인이 아니라는 것은 **두 번 다 같았다.**

**언어 보장 항목** — 1~8번. `NOT IN` 의 `NULL` 처리, `NOT EXISTS` 의 안전, `EXISTS` 의 `SELECT` 목록 무관, 세미 조인이 행을 안 늘리는 것은 전부 결과의 정의다.

**방언이 갈리는 항목** — **결과는 한 자리도 안 갈렸다.** 갈린 것은 **13번의 실행 계획 하나**뿐이다.\
목록 README 의 `19 … 표준` 표기는 **결과 기준으로 확인됐다** — 14·15번과 같은 성격이다(결과는 같고 계획만 갈린다).

**순서 보장** — 없다. 위 출력에 `ORDER BY` 를 붙인 것은 그 때문이다.\
**`emp`·`dept` 변경** — 없다. 이 주제는 기존 두 표를 읽기만 했다.
