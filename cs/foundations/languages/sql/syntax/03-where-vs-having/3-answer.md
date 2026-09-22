# sql/03-WHERE 와 HAVING 의 차이 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력은 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 에러 메시지도 실행 계획도 실제로 받은 것이고, 지어낸 출력은 없다.\
> 문서 근거는 [PG 18 SELECT](https://www.postgresql.org/docs/18/sql-select.html) · [MySQL 8.4 SELECT](https://dev.mysql.com/doc/refman/8.4/en/select.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. 두 절 사이에 어느 절이 끼어 있고, 그것이 판정 대상을 어떻게 바꾸는가

**`GROUP BY` 가 끼어 있고, 그것이 「한 줄」의 뜻을 사람에서 팀으로 바꾼다.**

```text
1. FROM      표를 만든다
2. WHERE     행을 버린다        <- 여기서 한 줄 = 사원 한 명
3. GROUP BY  행을 묶는다        <- 이 칸이 단위를 바꾼다
4. HAVING    그룹을 버린다      <- 여기서 한 줄 = 부서 한 개
5. SELECT    열을 만든다
```

`WHERE` 가 받는 것과 `HAVING` 이 받는 것은 **모양 자체가 다르다.**

```text
WHERE 가 받는 것 — 행 4개                  HAVING 이 받는 것 — 그룹 3개
+----+------+---------+--------+          dept_id=10   { ann(300), bob(500) }
|  1 | ann  |      10 |    300 |          dept_id=20   { cho(NULL) }
|  2 | bob  |      10 |    500 |          dept_id=NULL { dan(400) }
|  3 | cho  |      20 |   NULL |
|  4 | dan  |    NULL |    400 |
+----+------+---------+--------+
   판정 재료: salary 라는 값 하나            판정 재료: {300, 500} 이라는 값 묶음
```

그래서 두 절이 **쓸 수 있는 도구가 다르다.**

- `HAVING` 은 묶음을 값 하나로 접는 **집계 함수**를 쓴다 — `MAX({300,500}) = 500`.
- `WHERE` 는 접을 묶음이 아직 없으니 집계 함수를 **쓸 수 없다**(6번).

> **집계 함수(aggregate function)** — 여러 행을 값 하나로 접는 함수.\
> 예: `COUNT(*)` 은 그룹 안 행 수, `MAX(salary)` 는 그룹 안 최댓값.

이 한 그림이 나머지 답 전부의 근거다. 자세한 여덟 칸은 [01번](../01-logical-query-processing-order/)이 정본이다.

---

### 2. `dept_id=10` 의 `cnt` 는 (A)와 (B)에서 각각 얼마인가

**(A) `WHERE` 는 1, (B) `HAVING` 은 2 다.** 두 질의 다 2행을 준다.

```text
### SQL: SELECT dept_id, COUNT(*) AS cnt FROM emp WHERE salary >= 400 GROUP BY dept_id ORDER BY dept_id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | cnt                   +---------+-----+
---------+-----                  | dept_id | cnt |
      10 |   1                   +---------+-----+
    NULL |   1                   |    NULL |   1 |
(2 rows)                         |      10 |   1 |
                                 +---------+-----+

### SQL: SELECT dept_id, COUNT(*) AS cnt FROM emp GROUP BY dept_id HAVING MAX(salary) >= 400 ORDER BY dept_id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | cnt                   +---------+-----+
---------+-----                  | dept_id | cnt |
      10 |   2                   +---------+-----+
    NULL |   1                   |    NULL |   1 |
(2 rows)                         |      10 |   2 |
                                 +---------+-----+
```

**왜 그런가** — 버리는 시점이 다르기 때문이다.

```text
(A) WHERE salary >= 400 — 사람을 먼저 버린다
emp 4행 --WHERE--> [bob 500] [dan 400] --GROUP BY--> {10:[bob]}      -> cnt 1
                   (ann 300 탈락 · cho NULL 탈락)    {NULL:[dan]}

(B) HAVING MAX(salary) >= 400 — 팀을 통째로 판정한다
emp 4행 --GROUP BY--> {10:[ann,bob]} {20:[cho]} {NULL:[dan]}
        --HAVING-->   {10:[ann,bob]}            {NULL:[dan]}         -> cnt 2
                      (ann 은 조건에 안 맞지만 팀이 살아서 같이 산다)
```

**두 문은 다른 질문에 답하고 있다.**

| | 무엇을 묻는가 | `dept_id=10` 의 답 |
|---|---|---|
| (A) | 급여 400 이상인 사람이 부서마다 **몇 명**인가 | 1명 (`bob`) |
| (B) | **한 명이라도** 400 이상인 부서의 **전체 인원**은 | 2명 (`ann`, `bob`) |

그래서 "`WHERE` 든 `HAVING` 이든 되는데 `WHERE` 가 빠르다"는 말은 **반쪽만 맞다.**\
둘이 바꿔 쓸 수 있는 것은 **조건이 그룹 키에 걸릴 때뿐**이다(4번).

---

### 3. (B)에서 `dept_id=20`(`cho`) 이 사라진 이유

**`MAX(NULL)` 이 `NULL` 이고, `NULL >= 400` 이 `UNKNOWN` 이라서다. `HAVING` 도 `TRUE` 만 통과시킨다.**

```text
그룹 dept_id=20 의 판정

  그룹 내용      { cho(salary=NULL) }
       ↓
  MAX(salary)    NULL          <- 집계가 NULL 을 건너뛰고 나니 남은 값이 없다
       ↓
  NULL >= 400    UNKNOWN       <- 모르는 값과 400 의 크기 비교는 판정 불가
       ↓
  HAVING 의 처분  버린다        <- TRUE 가 아니면 전부 버린다
```

`WHERE` 가 `UNKNOWN` 행을 버리는 것과 **완전히 같은 규칙**이 4번 칸에서도 돈다.\
`HAVING` 만 `NULL` 을 봐 주는 특례는 없다.

```text
### SQL: SELECT dept_id, MAX(salary) AS mx FROM emp GROUP BY dept_id ORDER BY dept_id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id |  mx                   +---------+------+
---------+------                 | dept_id | mx   |
      10 |  500                  +---------+------+
      20 | NULL                  |    NULL |  400 |
    NULL |  400                  |      10 |  500 |
(3 rows)                         |      20 | NULL |
                                 +---------+------+
```

`dev`(20) 의 `MAX` 가 `NULL` 인 것이 보인다. 이 행이 `HAVING MAX(salary) >= 400` 에서 조용히 빠진다.\
3값 논리 자체는 [04번](../04-null-three-valued-logic/)이 정본이다.

> **`UNKNOWN`** — `TRUE`/`FALSE` 가 아닌 세 번째 진릿값.\
> 예: `NULL >= 400`. `WHERE` 도 `HAVING` 도 이것을 `FALSE` 와 똑같이 버린다.

---

### 4. 그룹 키에 건 조건은 왜 결과가 같은가

**결과는 같다. `dept_id` 는 그룹 키라서 그룹 안의 모든 행에서 값이 같기 때문이다.**

```text
### SQL: SELECT dept_id, SUM(salary) AS s FROM emp WHERE dept_id = 10 GROUP BY dept_id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id |  s                    +---------+------+
---------+-----                  | dept_id | s    |
      10 | 800                   +---------+------+
(1 row)                          |      10 |  800 |
                                 +---------+------+

### SQL: SELECT dept_id, SUM(salary) AS s FROM emp GROUP BY dept_id HAVING dept_id = 10;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id |  s                    +---------+------+
---------+-----                  | dept_id | s    |
      10 | 800                   +---------+------+
(1 row)                          |      10 |  800 |
                                 +---------+------+
```

**왜 이 경우에만 같은가** — 그룹 키는 **그룹 전체에서 한 값**이라 "행 단위 판정"과 "그룹 단위 판정"이 어긋날 수 없다.

```text
그룹 키 dept_id 에 건 조건                비집계 열 salary 에 건 조건
{10: [ann(10), bob(10)]}                 {10: [ann(300), bob(500)]}
     ↑       ↑                                 ↑        ↑
  둘 다 10 — 행 판정 = 그룹 판정            300 과 500 — 어느 값으로 판정하나?
                                            -> 그래서 집계로 접어야 한다
```

이것이 2번과 갈린 이유이기도 하다 — 2번의 `salary` 는 그룹 키가 아니라서, `HAVING` 에 쓰려면 `MAX()` 로 접어야 했고 **접는 순간 뜻이 달라졌다.**

---

### 5. 4번의 두 질의를 `EXPLAIN ANALYZE` 에 걸면

**PG 18.6 은 두 계획이 한 글자도 다르지 않고, MySQL 8.4.10 은 다르다.**

```text
### SQL: EXPLAIN ANALYZE SELECT dept_id, COUNT(*) FROM emp WHERE dept_id = 10 GROUP BY dept_id;
--- PG 18.6 ---
 GroupAggregate  (cost=0.00..24.15 rows=1 width=12) (actual time=0.012..0.012 rows=1.00 loops=1)
   Buffers: shared hit=1
   ->  Seq Scan on emp  (cost=0.00..24.12 rows=6 width=4) (actual time=0.009..0.010 rows=2.00 loops=1)
         Filter: (dept_id = 10)
         Rows Removed by Filter: 2
         Buffers: shared hit=1

### SQL: EXPLAIN ANALYZE SELECT dept_id, COUNT(*) FROM emp GROUP BY dept_id HAVING dept_id = 10;
--- PG 18.6 ---
 GroupAggregate  (cost=0.00..24.15 rows=1 width=12) (actual time=0.010..0.011 rows=1.00 loops=1)
   Buffers: shared hit=1
   ->  Seq Scan on emp  (cost=0.00..24.12 rows=6 width=4) (actual time=0.007..0.008 rows=2.00 loops=1)
         Filter: (dept_id = 10)
         Rows Removed by Filter: 2
         Buffers: shared hit=1
```

PG 는 `HAVING dept_id = 10` 을 **`Seq Scan` 의 `Filter` 로 내렸다.** 내가 `HAVING` 에 적었다는 흔적이 계획에 남지 않는다.

```text
### SQL: EXPLAIN ANALYZE SELECT dept_id, COUNT(*) FROM emp WHERE dept_id = 10 GROUP BY dept_id;
--- MySQL 8.4.10 ---  (출력의 표 테두리는 지웠다 — 폭이 200자를 넘는다)
-> Group aggregate: count(0)  (cost=0.75 rows=1) (actual time=0.0341..0.0342 rows=1 loops=1)
    -> Filter: (emp.dept_id = 10)  (cost=0.65 rows=1) (actual time=0.0259..0.0303 rows=2 loops=1)
        -> Table scan on emp  (cost=0.65 rows=4) (actual time=0.0238..0.0266 rows=4 loops=1)

### SQL: EXPLAIN ANALYZE SELECT dept_id, COUNT(*) FROM emp GROUP BY dept_id HAVING dept_id = 10;
--- MySQL 8.4.10 ---
-> Filter: (emp.dept_id = 10)  (actual time=0.053..0.0539 rows=1 loops=1)
    -> Table scan on <temporary>  (actual time=0.0491..0.0497 rows=3 loops=1)
        -> Aggregate using temporary table  (actual time=0.0482..0.0482 rows=3 loops=1)
            -> Table scan on emp  (cost=0.65 rows=4) (actual time=0.0206..0.0235 rows=4 loops=1)
```

**두 계획의 결론.**

| | PG 18.6 | MySQL 8.4.10 |
|---|---|---|
| `WHERE` 버전 | `Filter` 가 스캔에 · 집계로 들어간 행 **2** | `Filter` 가 스캔 위에 · 집계로 들어간 행 **2** |
| `HAVING` 버전 | **똑같다** — `Filter` 가 스캔에 · 행 **2** | **다르다** — 임시 테이블에 그룹 **3개**를 다 만든 뒤 1개로 거른다 |

집계에 건 조건은 **어느 엔진도 못 내린다.** PG 에서 그 모습이 이렇다.

```text
### SQL: EXPLAIN ANALYZE SELECT dept_id, COUNT(*) FROM emp GROUP BY dept_id HAVING MAX(salary) >= 400;
--- PG 18.6 ---
 HashAggregate  (cost=29.78..32.28 rows=67 width=12) (actual time=0.029..0.031 rows=2.00 loops=1)
   Group Key: dept_id
   Filter: (max(salary) >= 400)
   Batches: 1  Memory Usage: 32kB
   Rows Removed by Filter: 1
   Buffers: shared hit=1
   ->  Seq Scan on emp  (cost=0.00..21.30 rows=1130 width=8) (actual time=0.010..0.011 rows=4.00 loops=1)
         Buffers: shared hit=1
```

`Filter` 가 스캔이 아니라 **`HashAggregate` 에 붙었고**, 스캔이 `rows=4.00` — 4행을 전부 읽었다.\
같은 자리에서 `WHERE salary >= 400` 은 `rows=2.00` 이었다. 이것이 「묶기 전에 버리기」와 「묶은 뒤에 버리기」의 실측이다.

★ **여기서 외울 것은 「PG 가 내려 준다」가 아니다.** 그건 **구현 세부사항**이고 버전·데이터 분포에 따라 달라질 수 있다.\
외울 것은 **「내가 적은 자리가 그대로 도는 엔진이 있다」** — 그러니 **뜻이 같으면 `WHERE` 에 적는다.**\
(측정 조건: 4행짜리 표, 도커 컨테이너 1회 실행. 재현되는 것은 절대 시간이 아니라 **계획의 모양과 `rows` 값**이다.)

---

### 6. `SELECT dept_id FROM emp WHERE COUNT(*) > 1 GROUP BY dept_id;` 는 무엇을 돌려주는가

**아무것도 안 돌려준다. 두 엔진 다 에러다.**

```text
### SQL: SELECT dept_id FROM emp WHERE COUNT(*) > 1 GROUP BY dept_id;
--- PG 18.6 ---
ERROR:  aggregate functions are not allowed in WHERE
LINE 1: SELECT dept_id FROM emp WHERE COUNT(*) > 1 GROUP BY dept_id;
                                      ^
--- MySQL 8.4.10 ---
ERROR 1111 (HY000) at line 1: Invalid use of group function
```

**왜 그런가** — `WHERE` 는 2번 칸이고 `GROUP BY` 는 3번 칸이다. **셀 그룹이 아직 없다.**

```text
2번 칸에서 손에 든 것            COUNT(*) 이 필요로 하는 것
+---------------------+        +---------------------+
| 행 하나              |        | 행들의 묶음          |
|  id=1 ann 10 300    |        |  { ann, bob }       |
+---------------------+        +---------------------+
     이 한 줄에서 "몇 개"를 셀 수 있나? — 셀 대상이 없다
```

같은 뜻을 쓰려면 **4번 칸으로 옮긴다.**

```sql
SELECT dept_id FROM emp GROUP BY dept_id HAVING COUNT(*) > 1;
```

이것이 `HAVING` 이 존재하는 **유일한 이유**다. `WHERE` 로 쓸 수 있었다면 `HAVING` 은 필요 없었다.

---

### 7. `HAVING salary >= 400` — 두 엔진이 각각 무엇을 말하는가

**둘 다 거부하되, 거부하는 말이 다르다.**

```text
### SQL: SELECT dept_id, COUNT(*) AS cnt FROM emp GROUP BY dept_id HAVING salary >= 400;
--- PG 18.6 ---
ERROR:  column "emp.salary" must appear in the GROUP BY clause or be used in an aggregate function
LINE 1: ... COUNT(*) AS cnt FROM emp GROUP BY dept_id HAVING salary >= ...
                                                             ^
--- MySQL 8.4.10 ---
ERROR 1054 (42S22) at line 1: Unknown column 'salary' in 'having clause'
```

| | 무슨 말인가 | 함의 |
|---|---|---|
| PG 18.6 | "그 열은 `GROUP BY` 에 있거나 집계 안에 있어야 한다" | `salary` 를 **알고는 있다**. 이 자리에서 쓸 수 없다고 말한다 |
| MySQL 8.4.10 | "`having clause` 에 `salary` 라는 열이 **없다**" | 이 자리에서는 그 이름을 **찾지 못했다**고 말한다 |

**왜 다른가** — MySQL 의 `HAVING` 은 이름을 **출력 열 목록에서 먼저 찾는다.** 출력 열은 `dept_id` 와 `cnt` 뿐이니 `salary` 는 말 그대로 모르는 이름이다.\
바로 그 탐색 순서 때문에 MySQL 에서는 열 별칭이 `HAVING` 에서 통한다(8번). **두 현상은 같은 원인의 앞뒷면이다.**

```text
MySQL 의 HAVING 이름 찾기            PG 의 HAVING 이름 찾기
  1) SELECT 목록의 별칭에서 찾는다      1) 기반 테이블의 열에서만 찾는다
  2) 없으면 테이블 열에서 찾는다        (SELECT 목록의 별칭은 안 본다)
       ↓                                    ↓
  cnt 는 1)에서 찾는다  -> 통과          cnt 는 어디에도 없다 -> 에러
  salary 는 둘 다 실패 -> "Unknown"     salary 는 1)에서 찾지만 그룹 키가
                                        아니다 -> "must appear in GROUP BY"
```

`GROUP BY` 의 비집계 열 규칙 자체는 [목록의 **22번 주제**](../22-group-by-nonaggregated-columns/)가 정본이다.

---

### 8. `HAVING cnt >= 2` — 두 엔진에서 각각 무엇이 나오는가

**PG 18.6 은 에러, MySQL 8.4.10 은 정상 동작한다.**

```text
### SQL: SELECT dept_id, COUNT(*) AS cnt FROM emp GROUP BY dept_id HAVING cnt >= 2;
--- PG 18.6 ---
ERROR:  column "cnt" does not exist
LINE 1: ..., COUNT(*) AS cnt FROM emp GROUP BY dept_id HAVING cnt >= 2;
                                                              ^
--- MySQL 8.4.10 ---
+---------+-----+
| dept_id | cnt |
+---------+-----+
|      10 |   2 |
+---------+-----+
```

**왜 그런가** — `cnt` 는 **5번 칸(`SELECT`)에서 태어나는 이름**이고 `HAVING` 은 4번 칸이다.\
PG 는 그 순서를 그대로 지킨다. MySQL 은 `HAVING` 에서 출력 열 목록을 먼저 뒤지는 확장을 갖고 있다(7번의 그림).

**이식성 있는 형태는 식을 그대로 적는 것이다.** 양쪽 다 돈다.

```text
### SQL: SELECT dept_id, COUNT(*) AS cnt FROM emp GROUP BY dept_id HAVING COUNT(*) >= 2;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | cnt                   +---------+-----+
---------+-----                  | dept_id | cnt |
      10 |   2                   +---------+-----+
(1 row)                          |      10 |   2 |
                                 +---------+-----+
```

| 별칭을 쓸 수 있나 | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| `WHERE` | ✗ | ✗ |
| `GROUP BY` | ✓ | ✓ |
| `HAVING` | **✗** | **✓** |
| `ORDER BY` | ✓ | ✓ |

**깨지는 방향이 한쪽뿐이다.**

```text
MySQL 에서 쓴 질의를 PG 로              PG 에서 쓴 질의를 MySQL 로
        │                                      │
        ▼                                      ▼
 HAVING 에 별칭이 있으면 깨진다           깨지지 않는다
```

같은 표는 [01번](../01-logical-query-processing-order/)에도 있다 — **경계: 거기는 여덟 칸 전체의 별칭 가시성, 여기는 그것이 `HAVING` 을 쓸 때 실제로 무엇을 바꾸나.**

---

### 9. `SELECT COUNT(*) AS cnt FROM emp HAVING COUNT(*) > 100;` 의 결과 행 수

**0행이다.**

```text
### SQL: SELECT COUNT(*) AS cnt FROM emp HAVING COUNT(*) > 100;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 cnt                             (빈 결과 — 출력이 한 줄도 없다)
-----
(0 rows)
```

**왜 그런가** — `GROUP BY` 가 없고 집계가 있으면 **표 전체가 그룹 하나**다. 그 한 그룹이 `HAVING` 에서 떨어지면 남는 행이 없다.

```text
GROUP BY 가 없다                      GROUP BY 가 있다
+---------------------------+         dept_id=10   { ann, bob }
| { ann, bob, cho, dan }    |         dept_id=20   { cho }
|   그룹 "하나"              |         dept_id=NULL { dan }
+---------------------------+              그룹 3개
   HAVING 이 떨어뜨리면 -> 0행          HAVING 이 다 떨어뜨리면 -> 0행
   통과하면 -> 1행
```

조건이 참이면 1행이다.

```text
### SQL: SELECT COUNT(*) AS cnt FROM emp HAVING COUNT(*) > 1;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 cnt                             +-----+
-----                            | cnt |
   4                             +-----+
(1 row)                          |   4 |
                                 +-----+
```

**여기가 실무에서 조용히 터지는 자리다.** 「집계 질의는 행이 없어도 한 줄은 나온다」가 보통은 맞다.

```text
### SQL: SELECT COUNT(*) AS cnt FROM emp WHERE 1 = 0;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 cnt                             +-----+
-----                            | cnt |
   0                             +-----+
(1 row)                          |   0 |
                                 +-----+
```

`WHERE` 가 전부 걸러도 **1행(값 0)** 이 나온다. 그런데 `HAVING` 이 걸면 **행 자체가 없어진다.**\
`getSingleResult()` 같은 호출이 여기서 예외를 던진다.

---

### 10. `HAVING COUNT(*) = 0` 으로 사원 없는 부서를 찾을 수 있는가

**못 찾는다. 항상 0행이다.**

```text
### SQL: SELECT dept_id, COUNT(*) AS cnt FROM emp GROUP BY dept_id HAVING COUNT(*) = 0;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | cnt                   (빈 결과 — 출력이 한 줄도 없다)
---------+-----
(0 rows)
```

**왜 그런가** — `GROUP BY` 는 **행이 있는 그룹만 만든다.** 행 0개짜리 그룹은 애초에 생기지 않는다.

```text
emp 에 있는 dept_id 값              GROUP BY 가 만드는 그룹
  10, 10, 20, NULL          ---->   {10} {20} {NULL}     <- 3개
                                     ^
  dept.id = 30 (hr) 은                hr(30) 은 여기 없다.
  emp 에 한 번도 안 나온다             없는 그룹은 셀 수도 없다
```

`hr` 부서를 보려면 **`dept` 를 기준으로 조인**해야 한다. 그러면 `hr` 의 행이 만들어지고 `NULL` 로 채워진다.

```text
### SQL: SELECT d.name AS dept, COUNT(*) AS star, COUNT(e.id) AS emp_cnt
         FROM dept d LEFT JOIN emp e ON e.dept_id = d.id GROUP BY d.id, d.name ORDER BY d.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept  | star | emp_cnt          +-------+------+---------+
-------+------+---------         | dept  | star | emp_cnt |
 sales |    2 |       2          +-------+------+---------+
 dev   |    1 |       1          | sales |    2 |       2 |
 hr    |    1 |       0          | dev   |    1 |       1 |
(3 rows)                         | hr    |    1 |       0 |
                                 +-------+------+---------+
```

`hr` 의 `COUNT(*)` 은 **1**(조인이 만든 `NULL` 행 하나)이고 `COUNT(e.id)` 는 **0**이다.\
그래서 사원 없는 부서를 세려면 `HAVING COUNT(e.id) = 0` 을 쓴다 — `COUNT(*)` 이 아니다.\
외부 조인 규칙은 [14번](../14-left-right-outer-join/)이 정본이다.

---

### 11. 어디에 적을지 한 문장으로 판정하는 기준

**"이 조건을 판정하는 데 같은 그룹의 다른 행이 필요한가?"**

```text
같은 그룹의 다른 행이 필요한가?
        │                              │
       아니오                          예
        ↓                              ↓
     WHERE                          HAVING
 (행 하나로 판정됨)            (그룹 전체를 봐야 판정됨)

  salary >= 400                  COUNT(*) >= 2
  dept_id = 10                   SUM(salary) > 1000
  name LIKE 'a%'                 MAX(salary) >= 400
```

이 기준이 좋은 이유는 **세 가지를 한꺼번에 맞춰 주기** 때문이다.

1. **결과가 맞는다** — 행 단위 조건을 `HAVING` 에 옮기면 집계로 접어야 하고, 접는 순간 뜻이 변한다(2번).
2. **비용이 맞는다** — `WHERE` 로 버린 행은 묶일 일이 없다. MySQL 은 `HAVING` 을 내려 주지 않는다(5번).
3. **이식성이 맞는다** — `HAVING` 에서만 생기는 별칭·비집계 열 방언을 아예 안 만난다(7·8번).

**예외는 하나다.** 조건이 **그룹 키**에 걸리면 어느 쪽에 써도 결과가 같다(4번).\
그래도 `WHERE` 에 쓴다 — 같은 답을 더 싸게, 더 이식성 있게 얻는다.

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| `WHERE` / `HAVING` 결과 대비 (2·4번) | PG 18.6 · MySQL 8.4.10 | 각 4회 | 양쪽 출력 본문에 수록 |
| 집계·비집계·별칭 거부 (6·7·8번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | **에러 메시지가 근거다** |
| `EXPLAIN ANALYZE` 계획 대비 (5번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | **구현 의존** — 버전이 오르면 다시 찍어야 한다 |
| `GROUP BY` 없는 `HAVING` (9번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | 0행·1행 양쪽 확인 |
| 빈 그룹 (10번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | `LEFT JOIN` 대조까지 |

**구현 의존 항목** — 5번의 계획 비교. PG 18.6 이 `HAVING` 의 그룹 키 조건을 스캔 필터로 내린 것도, MySQL 8.4.10 이 안 내린 것도 **옵티마이저의 선택**이다. 버전이 오르면 **5번만 다시 돌리면 된다.**

**언어 보장 항목** — 1\~4·6\~11번. 두 절의 처리 순서와 이름 가시성은 문서가 정한 것이고, 계획이 바뀌어도 결과는 바뀌지 않는다.
