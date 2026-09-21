# sql/19-세미·안티 조인 — EXISTS·IN·NOT IN·NOT EXISTS — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · Subquery Expressions](https://www.postgresql.org/docs/18/functions-subquery.html) · [MySQL 8.4 · Subqueries with EXISTS or NOT EXISTS](https://dev.mysql.com/doc/refman/8.4/en/exists-and-not-exists-subqueries.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력은 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 실행 계획도 실제로 받은 것이고, 지어낸 출력은 없다.\
> 표는 기존 `emp`·`dept` 두 개만 썼다. **새로 만든 표가 없다.**\
> **버전** — `EXISTS`·`IN`·`NOT IN`·`NOT EXISTS` 모두 두 엔진에 오래전부터 있고, 두 매뉴얼에 도입 버전이 없어 **버전은 적지 않는다.**\
> **선행** — [05번](../05-null-comparison-is-distinct-from/)(`NULL` 비교) · [11 서브쿼리](../11-subquery-scalar-correlated-any-all/) · [13 INNER JOIN](../13-inner-join/).\
> **가장 중요한 선행** — [04 NULL 의 3값 논리](../04-null-three-valued-logic/). **이 주제의 중심 사고가 거기서 시작한다.**

## 한눈에 — 쉽게 말하면

**세미 조인 = 「저쪽에 짝이 있나?」만 묻고 **값은 안 가져오는** 조인. 안티 조인은 그 반대 — 「짝이 없는 것만」.**

- 조인은 **두 명단을 붙여 한 줄로 만든다.** 붙이면 행이 늘어날 수 있다([13번](../13-inner-join/)의 팬아웃).
- 그런데 "사원이 **있는** 부서 목록"을 뽑을 때는 **사원 정보가 필요 없다.** 있는지만 알면 된다.
- 그럴 때 쓰는 것이 **세미 조인**이다. 오른쪽 표를 **보기만 하고 붙이지 않는다** — 그래서 행이 안 는다.

```text
 INNER JOIN                       세미 조인 (EXISTS / IN)
 +----------------------+         +----------------------+
 | sales  (ann 때문)    |         | sales                |
 | sales  (bob 때문)    |  <- 2줄 | dev                  |
 | dev    (cho 때문)    |         +----------------------+
 +----------------------+           2행 — 부서 목록이다
   3행 — 사원 수만큼 늘었다
```

- 반대가 **안티 조인** — "사원이 **없는** 부서". `hr` 하나다.

| 비유 | 실체 |
|---|---|
| 출석부에 이름이 있나만 확인 | 세미 조인 — `EXISTS` / `IN` |
| 확인만 하고 그 사람 정보는 안 적는다 | **행이 안 늘어난다** |
| 출석부에 없는 사람만 찾기 | 안티 조인 — `NOT EXISTS` / `NOT IN` / `LEFT JOIN … IS NULL` |
| 출석부에 **판독 불가 칸**이 하나 있다 | 목록에 `NULL` 이 섞였다 |
| 그래서 "없다"를 아무에게도 말할 수 없게 된다 | **`NOT IN` 이 0행이 된다** |

**똑같은 구조다** — "이 명단에 없는 사람을 찾아 줘"라는 부탁에, 명단 한 칸이 **읽을 수 없는 글씨**라면\
어떤 이름에 대해서도 "명단에 없다"고 단언할 수 없다. 그 칸이 그 이름일지도 모르기 때문이다.\
`NOT IN` 이 하는 일이 정확히 그것이고, 그래서 **한 행도 못 내놓는다.**

> **세미 조인(semi join)** — 오른쪽에 짝이 있는지만 보고 왼쪽 행을 남기는 조인. 오른쪽 열은 결과에 안 나온다.\
> 예: `WHERE EXISTS (SELECT 1 FROM emp e WHERE e.dept_id = d.id)` — 사원이 있는 부서.

> **안티 조인(anti join)** — 오른쪽에 짝이 **없는** 왼쪽 행만 남기는 조인.\
> 예: `WHERE NOT EXISTS (…)` — 사원이 없는 부서(`hr`).

## 이 주제가 답하려는 질문

1. **`NOT IN` 은 왜 결과가 통째로 비나?** — 그리고 **양쪽 어디에 `NULL` 이 있어도** 그런가?
2. **`NOT EXISTS` 는 왜 안전한가?** — 무엇이 다르기에.
3. **`IN` 과 `EXISTS` 와 `JOIN` 은 성능이 다른가?** — 실행 계획이 같은 모양으로 수렴하나.

## 예시 데이터 — 이 묶음이 공유하는 것

이 폴더의 SQL 주제들은 **같은 두 표**를 쓴다. 표가 같으면 주제 간 비교가 공짜로 된다.

```text
emp (사원)                          dept (부서)
+----+------+---------+--------+    +----+-------+
| id | name | dept_id | salary |    | id | name  |
+----+------+---------+--------+    +----+-------+
|  1 | ann  |      10 |    300 |    | 10 | sales |
|  2 | bob  |      10 |    500 |    | 20 | dev   |
|  3 | cho  |      20 |   NULL |    | 30 | hr    |  <- 사원이 없는 부서
|  4 | dan  |    NULL |    400 |    +----+-------+
+----+------+---------+--------+
        ^
        +-- dan 은 소속이 없다 (dept_id NULL)   <- 이 한 칸이 이 주제의 폭탄이다
```

★ **이 주제의 주인공은 `dan` 과 `hr` 이다.**

```text
 emp.dept_id 를 목록으로 만들면          dept.id 를 목록으로 만들면
   (10, 10, 20, NULL)                      (10, 20, 30)
                 ↑                                    ↑
        dan 의 NULL 이 섞여 있다            NULL 이 없다 (PRIMARY KEY)

 "사원이 없는 부서" 를 NOT IN 으로 물으면  ->  목록에 NULL 이 있다   -> 0행
 "부서가 없는 사원" 을 NOT IN 으로 물으면  ->  목록은 깨끗한데       -> 역시 0행 ?
                                               ↑
                          양쪽 모두 무너진다 — 아래 4번·5번 절
```

<details>
<summary>표를 만드는 문 (PostgreSQL)</summary>

```sql
CREATE TABLE dept (
  id   int PRIMARY KEY,
  name text UNIQUE NOT NULL
);
CREATE TABLE emp (
  id      int PRIMARY KEY,
  name    text NOT NULL,
  dept_id int,
  salary  int
);
INSERT INTO dept VALUES (10,'sales'), (20,'dev'), (30,'hr');
INSERT INTO emp  VALUES (1,'ann',10,300), (2,'bob',10,500), (3,'cho',20,NULL), (4,'dan',NULL,400);
```

MySQL 은 `text` → `varchar(20)` 만 바꾸면 같다.

</details>

## 동작 방식

### 1. 세미 조인 — 「있는지만」 보면 행이 안 는다

**언제 쓰나** — 상대 표의 **값이 필요 없고 존재 여부만** 필요할 때.

```text
(전) dept 3행 · emp 4행                  (후) 세 형태의 결과
                                          IN      : sales, dev        2행
 "사원이 있는 부서"                       EXISTS  : sales, dev        2행
                                          JOIN    : sales, sales, dev 3행   <- 늘었다
```

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

`DISTINCT` 를 붙이면 조인도 2행이 된다 — **사후에 지우는 것**이다.

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

```text
 세미 조인               조인 + DISTINCT
 짝을 하나 찾으면 멈춘다   짝을 전부 만든 뒤 중복을 지운다
        ↓                        ↓
 애초에 안 늘린다           늘렸다가 줄인다
                                 ↑
        결과는 같지만 「늘렸다」는 사실이 집계에서 사고를 낸다 — 13번의 팬아웃
```

그림 해설 — **세미 조인의 값은 「행이 안 는다」 하나다.** `SUM` 이나 `COUNT` 를 씌울 때 이 차이가 답을 바꾼다([13번](../13-inner-join/)).\
비용 — 세미 조인은 오른쪽 값을 못 쓴다. **값이 필요하면 조인이 맞다.**

★ **`EXISTS` 는 `SELECT` 목록을 아예 계산하지 않는다.** 0 으로 나누는 식을 넣어도 안 터진다.

```text
### SQL: SELECT d.id FROM dept d WHERE EXISTS (SELECT 1/0 FROM emp e WHERE e.dept_id = d.id) ORDER BY d.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id                              +----+
----                             | id |
 10                              +----+
 20                              | 10 |
(2 rows)                         | 20 |
                                 +----+
```

**`1/0` 이 있는데도 에러가 없다.** 관례로 `SELECT 1` 을 쓰지만 `SELECT NULL` 이든 `SELECT *` 든 **무엇을 적어도 같다** — 엔진이 보는 것은 **행이 하나라도 나왔는가**뿐이다.

---

### 2. 안티 조인 — 「짝이 없는 것만」

**언제 쓰나** — "주문이 없는 고객", "로그가 없는 서버", "사원이 없는 부서"처럼 **빠진 것**을 찾을 때.

```text
 dept 3행에서 "사원이 없는 부서"를 찾는다
   sales(10) : ann, bob 이 있다   -> 제외
   dev(20)   : cho 가 있다        -> 제외
   hr(30)    : 아무도 없다        -> 정답
```

```text
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

**그런데 `NOT IN` 만 아무것도 못 준다.**

```text
### SQL: SELECT d.id, d.name FROM dept d WHERE d.id NOT IN (SELECT e.dept_id FROM emp e) ORDER BY d.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name                       (빈 결과 — 출력이 한 줄도 없다)
----+------
(0 rows)
```

그림 해설 — **같은 의도, 세 가지 표기, 두 가지 답.** 이것이 이 주제의 중심이다.\
비용 — **에러가 없다.** 0행은 "그런 부서가 없구나"로 읽힌다. 다음 절이 그 이유다.

---

### 3. `NOT IN` + `NULL` — 결과가 통째로 비는 이유

**언제 쓰나** — 안티 조인을 `NOT IN` 으로 쓸 때. **이 주제에서 가장 비싼 한 칸이다.**

먼저 **식 하나로** 본다. 표가 없어도 재현된다.

```text
### SQL: SELECT 30 IN (10,20,NULL) AS in_res, 30 NOT IN (10,20,NULL) AS notin_res, 10 IN (10,20,NULL) AS hit;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 in_res | notin_res | hit        +--------+-----------+------+
--------+-----------+-----       | in_res | notin_res | hit  |
        |           | t          +--------+-----------+------+
(1 row)                          |   NULL |      NULL |    1 |
                                 +--------+-----------+------+
```

**PG 의 빈 칸이 MySQL 의 `NULL` 이다.** 두 엔진이 같은 값을 냈다.

```text
 30 NOT IN (10, 20, NULL)
     ↓ 풀어 쓰면
 NOT (30 = 10  OR  30 = 20  OR  30 = NULL)
      ↓          ↓            ↓
    FALSE      FALSE      UNKNOWN
      ↓          ↓            ↓
     FALSE OR FALSE OR UNKNOWN  =  UNKNOWN       <- TRUE 가 하나도 없다
      ↓
 NOT UNKNOWN  =  UNKNOWN
      ↓
 WHERE 가 UNKNOWN 행을 버린다   ->   그 행은 결과에 없다
```

★ **`30` 자리에 무엇을 넣어도 같다.** 목록에 `NULL` 이 하나라도 있으면 `NOT IN` 은 **`TRUE` 가 될 수 없다.**

```text
 x 가 목록에 있으면       ->  NOT IN 은 FALSE     -> 탈락
 x 가 목록에 없으면       ->  NOT IN 은 UNKNOWN   -> 탈락    <- NULL 때문
                                                     ↓
                                     어느 쪽이든 탈락 = 언제나 0행
```

**반대로 `IN` 은 멀쩡하다.** `10 IN (10,20,NULL)` 은 `TRUE` 다 — **하나만 맞으면 나머지는 안 봐도 되기 때문**이다.

```text
 IN     : TRUE 가 하나라도 있으면 TRUE     -> NULL 이 끼어도 찾을 건 찾는다
 NOT IN : FALSE 가 전부여야 TRUE          -> NULL 하나가 그것을 막는다
              ↑
  그래서 IN 으로 테스트해 보고 안심한 뒤 NOT IN 을 배포하는 사고가 난다
```

**이 계산의 뿌리는 [04번](../04-null-three-valued-logic/)**이고, 거기서 이미 같은 0행을 봤다.\
**여기서 새로 인출할 것은 두 가지다** — ① **바깥 값이 `NULL` 이어도 똑같이 무너진다**(다음 절) ② **`NOT EXISTS` 는 왜 안전한가**(그 다음 절).

---

### 4. **양쪽 어디에 `NULL` 이 있어도** `NOT IN` 은 무너진다

**언제 쓰나** — "목록에 `NULL` 만 없으면 `NOT IN` 을 써도 된다"고 생각할 때.

방향을 뒤집어 **"부서가 없는 사원"**을 찾아 본다. 이번엔 목록이 `dept.id` 라 **`NULL` 이 없다**(기본키다).

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

```text
 이번에는 목록이 깨끗하다:  (10, 20, 30)
 그런데 바깥 값이 NULL 이다:  dan.dept_id = NULL

 NULL NOT IN (10, 20, 30)
     ↓
 NOT (NULL = 10 OR NULL = 20 OR NULL = 30)
      ↓
 NOT (UNKNOWN OR UNKNOWN OR UNKNOWN)  =  NOT UNKNOWN  =  UNKNOWN
      ↓
 dan 도 탈락 — 정작 찾던 그 행이
```

그림 해설 — **`NOT IN` 은 두 방향에서 무너진다.**

| 어디에 `NULL` 이 있나 | 결과 | 무엇을 잃나 |
|---|---|---|
| **목록 쪽** (`emp.dept_id`) | 0행 | **전부** — 어느 행도 못 나온다 |
| **바깥 값 쪽** (`e.dept_id`) | 그 행만 탈락 | **정답으로 찾아야 할 그 행** |

비용 — 두 번째가 더 음험하다. **결과가 0행이 아니라 「거의 맞는 답」이 나오기 때문**이다.\
여기서는 `emp` 에 소속 없는 사원이 `dan` 하나뿐이라 0행이 됐지만, 여럿이었다면 **`NULL` 인 행만 조용히 빠진 목록**이 나왔을 것이다.

★ **「목록에 `NULL` 이 없으니 안전하다」는 절반만 맞다.** **비교의 양쪽 모두** `NOT NULL` 이어야 한다.

---

### 5. `NOT EXISTS` 는 왜 안전한가

**언제 쓰나** — 안티 조인을 쓸 때. **기본 선택이 이것이다.**

```text
 NOT IN 이 묻는 것                        NOT EXISTS 가 묻는 것
 "이 값이 저 목록의 어느 것과도 다른가?"    "조건에 맞는 행이 하나도 없는가?"
        ↓                                         ↓
 값과 값을 비교한다 -> NULL 이 끼면 UNKNOWN  행이 있나 없나만 센다 -> 0 아니면 1 이상
        ↓                                         ↓
 세 번째 진릿값이 바깥으로 새 나온다         진릿값이 둘뿐이다 — UNKNOWN 이 없다
```

```text
 NOT EXISTS (SELECT 1 FROM emp e WHERE e.dept_id = 30)

   안쪽 WHERE 가 UNKNOWN 행을 버린다   <- NULL 은 여기서 이미 처리된다
        ↓
   남은 행 개수 = 0
        ↓
   EXISTS = FALSE   ->   NOT EXISTS = TRUE       <- 깔끔한 두 값
```

★ **`NULL` 은 서브쿼리 **안**에서 소비된다.** `dan` 의 `NULL` 은 안쪽 `WHERE` 에서 `UNKNOWN` 이 되어 버려지고,\
바깥은 **「행이 남았나」**만 본다. **`UNKNOWN` 이 바깥으로 새 나갈 통로가 없다.**

**처방 셋 — 세 번째가 가장 근본적이다.**

| 처방 | 언제 | 대가 |
|---|---|---|
| **`NOT EXISTS` 로 바꾼다** | **기본 선택** | 없음. 상관 서브쿼리라 조금 길다 |
| 서브쿼리에 `WHERE … IS NOT NULL` 을 건다 | `NOT IN` 형태를 유지해야 할 때 | 누가 나중에 지우면 다시 터진다. **바깥 값 쪽은 여전히 못 막는다** |
| 그 열에 `NOT NULL` 제약을 건다 | 설계를 고칠 수 있을 때 | 데이터 정리가 필요하다. 대신 **영구히 안 터진다** |

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

---

### 6. 안티 조인의 세 번째 형태 — `LEFT JOIN … IS NULL`

**언제 쓰나** — 짝 없는 행을 찾을 때. **함정이 하나 있다.**

```text
 LEFT JOIN 은 짝 없는 행을 NULL 로 채워 남긴다        <- 14번
        ↓
 그 "NULL 로 채워진" 표시를 조건으로 쓴다
        ↓
 WHERE 오른쪽열 IS NULL   ->   짝이 없던 행만 남는다
```

```text
### SQL: SELECT d.id, d.name FROM dept d LEFT JOIN emp e ON e.dept_id = d.id WHERE e.id IS NULL ORDER BY d.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name                       +----+------+
----+------                      | id | name |
 30 | hr                         +----+------+
(1 row)                          | 30 | hr   |
                                 +----+------+
```

★ **어느 열로 `IS NULL` 을 볼지가 함정이다.** `NULL` 이 들어갈 수 있는 열을 고르면 **원래 `NULL` 이던 행까지 잡힌다.**

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

```text
 e.id IS NULL     -> id 는 PRIMARY KEY 라 원래 NULL 일 수 없다
                     NULL 이면 "채워진 것" 뿐이다        -> 1행  (정답)

 e.salary IS NULL -> cho 의 salary 가 원래 NULL 이다
                     "채워진 것"과 "원래 NULL"이 섞인다   -> 2행  (틀림)
                            ↑
        dev 부서에는 사원 cho 가 있는데 "사원이 없는 부서"로 잡혔다
```

그림 해설 — **`IS NULL` 로 볼 열은 `NOT NULL` 인 열이어야 한다.** 보통 기본키를 쓴다.\
비용 — 에러가 없다. **2행이 "부서 둘이 비었구나"로 읽힌다.**

★ **`NOT EXISTS` 에는 이 함정이 없다.** 열을 고를 일이 없기 때문이다.

---

### 7. 세 형태의 **실행 계획이 수렴하는지** 실측

**언제 쓰나** — "`IN` 이 느리다던데 `EXISTS` 로 바꿔야 하나"가 떠오를 때.

**먼저 세미 조인 — `IN` 과 `EXISTS` 의 계획을 나란히 놓는다.**

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

★ **한 글자도 다르지 않다.** 비용 숫자까지 같다.

MySQL 도 같다.

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

★ **두 엔진 모두 `IN` 과 `EXISTS` 의 계획이 완전히 같다.** 문법 차이가 계획 차이로 남지 않았다.

**`JOIN + DISTINCT` 는 갈린다.**

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
 IN / EXISTS                         JOIN + DISTINCT
 오른쪽을 먼저 접고(dedup) 조인       조인해서 늘린 다음 중복 제거
        ↓                                    ↓
 중복 제거가 조인 "앞"                중복 제거가 조인 "뒤"
        ↓                                    ↓
 늘어난 적이 없다                     늘어났다가 줄어든다
```

그림 해설 — **두 엔진 다 같은 이야기를 한다.** `IN`·`EXISTS` 는 **접고 붙이고**, `JOIN + DISTINCT` 는 **붙이고 접는다.**\
비용 — 작은 표에서는 티가 안 나지만, 팬아웃이 큰 1:N 에서는 **중간 결과의 크기가 다르다.**

**안티 조인 쪽은 이름부터 다르다.**

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

★ **`NOT EXISTS` 는 두 엔진이 「안티 조인」이라고 이름 붙여 준다** — `Hash Right Anti Join`(PG) · `Hash antijoin`(MySQL).\
**`NOT IN` 은 안티 조인이 되지 못한다.** 필터 안의 서브쿼리로 남는다.

```text
 왜 NOT IN 은 안티 조인으로 못 바뀌나

 안티 조인은 "짝이 없으면 남긴다"는 두 값짜리 규칙이다
 NOT IN 은 목록에 NULL 이 있으면 "모른다"를 내야 한다 — 세 번째 값
        ↓
 옵티마이저가 두 값짜리 연산으로 바꾸면 답이 달라진다
        ↓
 그래서 못 바꾼다 — 느린 게 아니라 "다른 연산"이다
```

**즉 `NOT IN` 은 「느려서」 피하는 게 아니라 「틀려서」 피하는 것이고, 그 틀림이 계획에까지 드러난다.**

**세 번째 형태의 계획은 두 엔진이 갈렸다.**

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

| 형태 | PG 18.6 의 계획 | MySQL 8.4.10 의 계획 |
|---|---|---|
| `IN` | `Hash Join` + 선 dedup | `Nested loop` + `Materialize with deduplication` |
| `EXISTS` | **`IN` 과 완전히 같다** | **`IN` 과 완전히 같다** |
| `JOIN` + `DISTINCT` | 조인 **뒤** `HashAggregate` | 조인 **뒤** `Temporary table with deduplication` |
| `NOT EXISTS` | **`Hash Right Anti Join`** | **`Hash antijoin`** |
| `NOT IN` | `Seq Scan` + `SubPlan` (안티 조인 아님) | `<in_optimizer>` 서브쿼리 (안티 조인 아님) |
| `LEFT JOIN … IS NULL` | `Hash Right Join` + `Filter` | **`Hash antijoin`** + `Filter` |

★ **마지막 줄이 이 실측에서 유일하게 갈린 자리다** — **MySQL 은 `LEFT JOIN … IS NULL` 을 안티 조인으로 바꿨고, PG 는 외부 조인 + 필터로 남겼다.**\
이것은 **옵티마이저의 선택**이지 보장이 아니다. 통계와 버전에 따라 달라질 수 있다.

> **재현 주** — 위 계획의 추정 행 수(PG 의 `rows=1130`·`rows=1270`)는 **통계가 없을 때의 기본값**이다.\
> 두 표가 워낙 작아 실제 행 수(4·3)와 무관하다. **여기서 볼 것은 비용 수치가 아니라 계획의 모양과 연산자 이름**이다.

★ **같은 서버·같은 버전에서 두 번 찍었더니 MySQL 쪽이 달랐다 — 실측이다.**

```text
 작성 중 1차 관찰 (MySQL 8.4.10)          같은 날 재확인 (같은 서버·같은 버전)
 NOT IN 의 계획                            NOT IN 의 계획
   Select #2 (… run only once)               Select #2 (… dependent)
   Materialize with deduplication            Filter: (… or (e.dept_id is null))
   Index lookup on <materialized_subquery>   Table scan on e
        ↑                                          ↑
  서브쿼리를 한 번 만들어 재사용            바깥 행마다 다시 도는 형태
```

```text
 두 번 다 같았던 것                        두 번 사이에 달라진 것
 IN 과 EXISTS 의 계획이 서로 같다           MySQL 의 추정 행 수 (rows=4 -> rows=3)
 NOT EXISTS 가 Hash antijoin 이다          그 결과 NOT IN 의 계획 모양
 NOT IN 은 안티 조인이 아니다               PG 쪽은 한 글자도 안 달라졌다
```

**결과는 두 번 다 똑같았다**(`NOT IN` 은 0행, `NOT EXISTS` 는 `hr`). **달라진 것은 계획뿐이다.**\
★ **이것이 「계획은 아무도 보장하지 않는다」의 실측 근거다** — 버전도 데이터도 안 바꿨는데 통계 추정이 흔들려 계획이 바뀌었다.\
위에 실은 것은 **재확인 시점의 출력**이다.

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

★ **`Rows Removed by Filter: 3`.** `hr` 을 포함한 **세 행이 전부** 필터에서 떨어졌다는 것이 계획에 찍힌다.

## 문법 — 어느 절에서 무엇이 보이나

```sql
-- 세미 조인 (있는 것만)
WHERE col IN (SELECT ...)                          -- 비상관. 목록을 만든다
WHERE EXISTS (SELECT 1 FROM t WHERE t.k = 바깥.k)   -- 상관. 행이 있나만 본다

-- 안티 조인 (없는 것만)
WHERE NOT EXISTS (SELECT 1 FROM t WHERE t.k = 바깥.k)   -- 기본 선택
WHERE col NOT IN (SELECT ...)                            -- NULL 이 끼면 0행
FROM 왼쪽 LEFT JOIN 오른쪽 ON …  WHERE 오른쪽.NOT_NULL열 IS NULL
```

규칙 일곱.

1. **세미·안티 조인은 행을 안 늘린다.** 오른쪽 값을 결과에 안 쓰기 때문이다.
2. **`EXISTS` 의 `SELECT` 목록은 계산되지 않는다.** `SELECT 1/0` 을 넣어도 안 터진다.
3. **`NOT IN` 은 목록에 `NULL` 이 하나라도 있으면 언제나 0행**이다.
4. **`NOT IN` 은 바깥 값이 `NULL` 이어도 그 행을 잃는다.** 양쪽이 다 `NOT NULL` 이어야 안전하다.
5. **`NOT EXISTS` 는 `NULL` 을 서브쿼리 안에서 소비한다.** 진릿값이 둘뿐이다.
6. **`LEFT JOIN … IS NULL` 의 `IS NULL` 은 `NOT NULL` 인 열에 걸어야 한다.** 보통 기본키다.
7. **`IN` 과 `EXISTS` 는 계획이 같다.** 둘 중 고르는 기준은 성능이 아니라 **읽기 쉬움**이다.

읽을 때 붙잡을 것은 **"`NULL` 이 어디에 있을 수 있나"** 하나다.

```text
 목록 쪽에 NULL 가능?   -> NOT IN 쓰지 마라
 바깥 값에 NULL 가능?   -> NOT IN 쓰지 마라
 둘 다 NOT NULL 보장?   -> NOT IN 도 되지만, 그 보장이 내일도 유효한가?
                             ↑
              그냥 NOT EXISTS 를 쓰면 이 질문 자체가 없어진다
```

## 어디서 틀리나

- **`NOT IN` 의 서브쿼리에 `NULL` 이 섞인다.**\
  결과가 **항상 0행**이다. 에러도 경고도 없다. `NOT EXISTS` 로 바꾼다.
- **바깥 값이 `NULL` 일 수 있는데 `NOT IN` 을 쓴다.**\
  `dan` 이 빠졌다. **목록이 깨끗해도 무너진다.**
- **`IN` 으로 테스트하고 `NOT IN` 을 배포한다.**\
  `IN` 은 `NULL` 이 섞여도 찾을 건 찾는다. 뒤집은 순간만 터진다.
- **`LEFT JOIN … IS NULL` 에서 `NULL` 이 가능한 열을 고른다.**\
  `e.salary IS NULL` 로 썼더니 사원이 있는 `dev` 까지 "빈 부서"로 잡혔다.
- **세미 조인 대신 `JOIN` 을 쓰고 집계를 씌운다.**\
  행이 늘어 합계가 부풀려진다([13번](../13-inner-join/)의 팬아웃).
- **`EXISTS (SELECT * …)` 가 느릴까 봐 `SELECT 1` 로 바꾼다.**\
  아무 차이가 없다. `SELECT` 목록은 계산되지 않는다.
- **`IN` 이 `EXISTS` 보다 느리다고 믿고 기계적으로 바꾼다.**\
  두 엔진 다 **계획이 한 글자도 안 달랐다.** 고칠 것은 문법이 아니라 인덱스·통계다.
- **`NOT IN` 을 「느려서」 피한다고 설명한다.**\
  틀린 설명이다. **답이 틀려서** 피하는 것이고, 옵티마이저가 안티 조인으로 못 바꾸는 이유도 그것이다.

## 구현 세부사항 대 언어 보장

| | 무엇인가 | 누가 보장하나 |
|---|---|---|
| `NOT IN` 이 `NULL` 섞인 목록에서 0행 | **결과의 정의** | 언어 — 3값 논리에서 따라 나온다 |
| 바깥 값이 `NULL` 이면 `NOT IN` 이 그 행을 버린다 | **결과의 정의** | 언어 |
| `NOT EXISTS` 가 `NULL` 에 안전 | **결과의 정의** | 언어 — 진릿값이 둘뿐이다 |
| `EXISTS` 의 `SELECT` 목록이 계산되지 않는다 | **결과의 정의** | 언어 — 두 엔진에서 `1/0` 이 안 터졌다 |
| 세미 조인이 행을 안 늘린다 | **결과의 정의** | 언어 |
| **`IN` 과 `EXISTS` 의 계획이 같다** | **옵티마이저의 선택** | **아무도** — 이 데이터·이 버전에서 같았을 뿐이다 |
| `NOT EXISTS` 가 `Anti Join` 연산자로 뜬다 | 옵티마이저의 선택 + 그 엔진의 표기 | 아무도 |
| `LEFT JOIN … IS NULL` 이 안티 조인이 되는가 | **옵티마이저의 선택** | **두 엔진이 갈렸다** — MySQL 은 바꿨고 PG 는 안 바꿨다 |

- ★ **결과는 언어가 보장하고, 계획은 아무도 보장하지 않는다.** 위 계획 비교는 **관찰**이지 규칙이 아니다.\
  「`IN` 과 `EXISTS` 는 같다」를 **보장으로 외우면 안 된다** — 이 판에서 같았다는 관찰이다.\
  ★ **같은 서버·같은 버전에서 두 번 찍었더니 MySQL 의 `NOT IN` 계획이 달랐다**(7번 절). 버전도 데이터도 안 바꿨는데 바뀌었다.
- 계획의 추정 행 수는 **통계 없는 기본값**이라 재현되지 않을 수 있다. 볼 것은 모양과 연산자 이름이다.
- **결과의 순서는 보장되지 않는다.** 위 출력에 `ORDER BY` 를 붙인 것은 그 때문이다.

## 언제 쓰고 언제 안 쓰나

- **쓴다 — `EXISTS`, 상대 표의 값이 필요 없을 때.** 행이 안 늘어난다.
- **쓴다 — `IN`, 목록이 짧거나 상수일 때.** 읽기 쉽다. 계획은 `EXISTS` 와 같았다.
- **쓴다 — `NOT EXISTS`, 안티 조인의 기본 선택.** `NULL` 을 생각할 필요가 없어진다.
- **쓴다 — `LEFT JOIN … IS NULL`, 안 붙은 쪽의 다른 열도 함께 봐야 할 때.** 단 `IS NULL` 은 `NOT NULL` 열에.
- **안 쓴다 — `NOT IN`, 양쪽 중 하나라도 `NULL` 이 가능할 때.** 사실상 **거의 언제나**다.
- **안 쓴다 — `JOIN` + `DISTINCT`, 존재 여부만 필요할 때.** 늘렸다 줄이는 것이고 집계와 섞이면 틀린다.
- **주의 — `IN` 의 목록이 아주 길 때.** 수만 개짜리 상수 목록은 조인이나 임시 표로 바꾼다.

## 핵심 문장

- 세미 조인은 **「있는지만」 보고 행을 안 늘린다.** `JOIN` 은 3행, `IN`/`EXISTS` 는 2행이었다.
- **`NOT IN` 은 목록에 `NULL` 이 하나만 있어도 언제나 0행**이다. `NOT (… OR UNKNOWN)` 이 `UNKNOWN` 이기 때문이다.
- **`NOT IN` 은 바깥 값이 `NULL` 이어도 그 행을 잃는다** — 목록이 깨끗해도 `dan` 이 사라졌다. **양쪽이 다 위험하다.**
- **`NOT EXISTS` 는 `NULL` 을 서브쿼리 안에서 소비한다.** 바깥은 「행이 있나」만 보므로 `UNKNOWN` 이 새 나갈 통로가 없다.
- **`LEFT JOIN … IS NULL` 은 `NOT NULL` 열에 걸어야 한다.** `e.salary IS NULL` 로 쓰면 사원이 있는 부서까지 잡힌다.
- **`IN` 과 `EXISTS` 의 계획은 두 엔진에서 한 글자도 안 달랐다.** 고칠 것은 문법이 아니다.
- **`NOT EXISTS` 만 `Anti Join` 연산자가 된다.** `NOT IN` 은 안 된다 — **느려서가 아니라 답이 다르기 때문**이다.

## 관련 자료

- [PostgreSQL 18 · Subquery Expressions](https://www.postgresql.org/docs/18/functions-subquery.html) — `EXISTS`·`IN`·`NOT IN` 의 정의와 `NULL` 주의.
- [MySQL 8.4 · Subqueries with EXISTS or NOT EXISTS](https://dev.mysql.com/doc/refman/8.4/en/exists-and-not-exists-subqueries.html) — `EXISTS` 의 `SELECT` 목록이 무관하다는 서술.
- [04 NULL 의 3값 논리](../04-null-three-valued-logic/) — **경계: 그쪽은 `UNKNOWN` 의 계산 규칙과 `NOT IN` 이 0행이라는 사실까지, 여기는 그 사고의 양방향성·`NOT EXISTS` 의 안전 근거·실행 계획부터.**
- [11 서브쿼리 — 스칼라·상관·ANY/ALL](../11-subquery-scalar-correlated-any-all/) — **경계: 그쪽은 서브쿼리 일반의 계약과 `ANY`/`ALL` 까지, 여기는 `EXISTS`/`IN` 계열의 선택과 계획부터.**
- [13 INNER JOIN](../13-inner-join/) — **경계: 그쪽은 「조인이 행을 늘린다」까지, 여기는 「안 늘리는 형태」부터.**
- [14 LEFT·RIGHT OUTER JOIN](../14-left-right-outer-join/) — 6번 절의 `LEFT JOIN … IS NULL` 이 기대는 규칙.
- [15 OUTER JOIN 에서 ON 과 WHERE 의 차이](../15-on-vs-where-in-outer-join/) — `LEFT JOIN … IS NULL` 에서 조건의 자리가 왜 중요한가.
- [18 USING 과 NATURAL JOIN](../18-using-and-natural-join/) — 외부 조인 + `USING` 이 짝 유무를 덮는 자리.
- [05 NULL 비교 — IS NULL·IS DISTINCT FROM·NULL 안전 등호](../05-null-comparison-is-distinct-from/) — **경계: 그쪽은 `NULL` 을 비교하는 연산자까지, 여기는 그것이 `NOT IN` 을 어떻게 무너뜨리나부터.**
- [25 조인 팬아웃 — 행 수와 집계가 어긋나는 자리](../25-join-fan-out/) — **경계: 그쪽은 팬아웃 처방의 선택 기준까지, 여기는 그 처방 중 세미 조인의 의미론부터.**
- **`EXPLAIN` 읽기**는 목록의 **58번 주제**가 정본이다.
- [SQL 주제 목록](../README.md)

## 용어 풀이

- **세미 조인(semi join)** — 오른쪽에 짝이 있는지만 보고 왼쪽 행을 남기는 조인. 오른쪽 열은 결과에 없다.\
  예: `WHERE EXISTS (SELECT 1 FROM emp e WHERE e.dept_id = d.id)` — 2행.
- **안티 조인(anti join)** — 오른쪽에 짝이 **없는** 왼쪽 행만 남기는 조인.\
  예: `WHERE NOT EXISTS (…)` — `hr` 하나.
- **`EXISTS`** — 서브쿼리가 한 행이라도 내면 `TRUE` 인 술어. `SELECT` 목록은 계산되지 않는다.\
  예: `EXISTS (SELECT 1/0 …)` 가 에러 없이 돈다.
- **`NOT EXISTS`** — 서브쿼리가 한 행도 안 낼 때 `TRUE`. 진릿값이 둘뿐이라 `NULL` 에 안전하다.\
  예: `NOT IN` 이 0행을 줄 자리에서 `hr` 을 제대로 찾아낸다.
- **`NOT IN` 의 `NULL` 함정** — 목록에 `NULL` 이 있으면 `NOT IN` 이 `TRUE` 가 될 수 없어 결과가 빈다.\
  예: `30 NOT IN (10,20,NULL)` 은 `TRUE` 가 아니라 `NULL` 이다.
- **`UNKNOWN`** — `TRUE`/`FALSE` 가 아닌 세 번째 진릿값. `NULL` 이 비교에 끼면 나온다.\
  예: `30 = NULL`. `WHERE` 는 이것을 `FALSE` 와 똑같이 버린다.
- **팬아웃(fan-out)** — 1:N 조인으로 왼쪽 행이 여러 줄로 불어나는 현상.\
  예: `sales` 가 사원 둘 때문에 두 줄이 됐다. 세미 조인은 이것을 안 만든다.
- **실행 계획(execution plan)** — 엔진이 질의를 어떤 연산자로 돌지 정한 트리.\
  예: `Hash Right Anti Join` — PG 가 `NOT EXISTS` 에 붙인 이름.
- **`Anti Join` 연산자** — 안티 조인을 한 번에 처리하는 조인 연산자.\
  예: PG 의 `Hash Right Anti Join`, MySQL 의 `Hash antijoin`. **`NOT IN` 에는 안 붙는다.**
- **`Rows Removed by Filter`** — PG 의 `EXPLAIN ANALYZE` 가 찍는, 필터가 버린 행 수.\
  예: `NOT IN` 질의에서 3 — 세 부서가 전부 떨어졌다는 증거.

## 더 들어가면

- **`NOT IN` 을 안전하게 만드는 유일한 근본 처방은 `NOT NULL` 제약**이다. 서브쿼리에 `IS NOT NULL` 을 거는 것은 **목록 쪽만** 막는다 — 바깥 값 쪽은 여전히 뚫려 있다.
- **`IS DISTINCT FROM`** 은 `NULL` 을 같은 값처럼 비교하는 연산자다. 안티 조인을 값 비교로 쓰고 싶을 때 쓰인다 — [05번](../05-null-comparison-is-distinct-from/).
- **세미 조인은 `LIMIT 1` 과 의미가 같지 않다.** `EXISTS` 는 "하나라도 있나"를 묻고 멈추지만, 엔진이 실제로 첫 행에서 멈춘다는 보장은 계획에 달렸다.
- **`NOT EXISTS` 의 상관 조건에 `NULL` 이 들어가도 안전한 이유**는 「안쪽 `WHERE` 가 먼저 `UNKNOWN` 을 버린다」다. 그래서 `NOT EXISTS` 는 사실상 **「짝이 확실히 있는 경우만 제외」**를 뜻한다 — 「짝이 있을지도 모르는 경우」는 제외하지 않는다.
