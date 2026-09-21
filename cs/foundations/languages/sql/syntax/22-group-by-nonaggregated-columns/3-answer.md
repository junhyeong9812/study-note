# sql/22-`GROUP BY` 와 비집계 열 규칙 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력·에러는 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 지어낸 출력은 없다.\
> 문서 근거는 [PG 18 Table Expressions](https://www.postgresql.org/docs/18/queries-table-expressions.html) · [MySQL 8.4 Handling of GROUP BY](https://dev.mysql.com/doc/refman/8.4/en/group-by-handling.html) · [PG 16 릴리스 노트](https://www.postgresql.org/docs/release/16.0/).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. `GROUP BY` 는 3번 칸이고, 거기서 입력이 행에서 그룹으로 바뀐다

```text
FROM ──> WHERE ──> GROUP BY ──> HAVING ──> SELECT ──> ORDER BY
  1        2          3            4          5          6
                      ^
              여기서 입력이 "행" 에서 "그룹" 으로 바뀐다
              이 선을 넘은 칸들은 원래 행을 못 본다
```

```text
  3번 칸의 입력 (행 4개)            3번 칸의 출력 (그룹 3개)
+----+------+---------+--------+   +---------+------------------------+
| id | name | dept_id | salary |   | 그룹 키 | 그 안에 있는 행들       |
+----+------+---------+--------+   +---------+------------------------+
|  1 | ann  |      10 |    300 |   |      10 | (1,ann,300) (2,bob,500)|
|  2 | bob  |      10 |    500 |-->|      20 | (3,cho,NULL)           |
|  3 | cho  |      20 |   NULL |   |    NULL | (4,dan,400)            |
|  4 | dan  |    NULL |    400 |   +---------+------------------------+
+----+------+---------+--------+
```

★ **4번 칸부터는 행이 없고 그룹만 있다.**\
그래서 `SELECT name` 은 「`dept_id=10` 봉투에서 이름 하나를 꺼내라」인데, 봉투에 `ann` 과 `bob` 둘이 들어 있어 **답이 정해지지 않는다.**

쓸 수 있는 것은 **둘뿐**이다.

```text
 쓸 수 있는 것                      쓸 수 없는 것
 +--------------------------+       +--------------------------+
 | 그룹 키 (GROUP BY 에 적은|       | 비집계 열                 |
 |   것) — 봉투 이름        |       |   — 봉투 안의 쪽지 하나    |
 | 집계 함수의 결과          |       |                          |
 |   — 봉투 안을 센 값       |       |                          |
 +--------------------------+       +--------------------------+
```

집계 없이 `GROUP BY` 만 쓰면 **`DISTINCT` 와 같아진다** — 그룹 키만 남으니 당연하다.

```text
### SQL: SELECT dept_id FROM emp GROUP BY dept_id ORDER BY dept_id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id                         +---------+
---------                        | dept_id |
      10                         +---------+
      20                         |    NULL |
    NULL                         |      10 |
(3 rows)                         |      20 |
                                 +---------+
```

> **그룹 키(group key)** — `GROUP BY` 에 적은 식. 한 그룹 안에서 값이 하나로 정해진다.\
> 예: `GROUP BY dept_id` 면 `dept_id=10` 그룹의 모든 행이 10이다.

---

### 2. 양쪽 다 거부한다 — 다만 메시지가 다르다

**출력**

```text
### SQL: SELECT dept_id, name FROM emp GROUP BY dept_id;
--- PG 18.6 ---
ERROR:  column "emp.name" must appear in the GROUP BY clause or be used in an aggregate function
LINE 1: SELECT dept_id, name FROM emp GROUP BY dept_id;
                        ^
--- MySQL 8.4.10 ---
ERROR 1055 (42000) at line 1: Expression #2 of SELECT list is not in GROUP BY clause and contains nonaggregated column 'study.emp.name' which is not functionally dependent on columns in GROUP BY clause; this is incompatible with sql_mode=only_full_group_by
```

**왜 그런가**

| | 메시지가 제시하는 탈출구 |
|---|---|
| PostgreSQL 18.6 | **둘** — `GROUP BY` 에 넣거나 집계로 감싸라 |
| MySQL 8.4.10 | **셋** — 그 둘에 더해 **「함수 종속이 아니다」**와 **`sql_mode=only_full_group_by`** 를 지목한다 |

★ **MySQL 의 메시지가 설정 이름을 말해 주는 것**이 이 주제의 분기점이다. PG 에는 그런 설정이 **없다.**

```text
 PG 의 세계                         MySQL 의 세계
 +------------------------+         +------------------------+
 | 규칙은 하나다           |         | 규칙이 설정에 달렸다     |
 | 예외는 기본키뿐         |         | 기본은 거부(8.0 부터)   |
 | 끌 수 있는 스위치가 없다 |         | 끄면 값이 나온다         |
 +------------------------+         +------------------------+
```

**거부가 정상이고, 그게 이 규칙의 값이다.** 여기서 안 막히면 5번의 「조용히 틀린 값」을 받는다.

---

### 3. 거부된다. 그리고 MySQL 의 번호가 **다르다** — `1140`

**출력**

```text
### SQL: SELECT name, COUNT(*) FROM emp;
--- PG 18.6 ---
ERROR:  column "emp.name" must appear in the GROUP BY clause or be used in an aggregate function
LINE 1: SELECT name, COUNT(*) FROM emp;
               ^
--- MySQL 8.4.10 ---
ERROR 1140 (42000) at line 1: In aggregated query without GROUP BY, expression #1 of SELECT list contains nonaggregated column 'study.emp.name'; this is incompatible with sql_mode=only_full_group_by
```

**왜 그런가**

```text
 GROUP BY 가 없어도 집계가 하나 있으면
 +-------------------------------------+
 | 표 전체가 "한 그룹" 이 된다           |
 | 그 한 그룹 안에 4행이 들어 있다       |
 | name 은 ann/bob/cho/dan 넷이다       |
 +-------------------------------------+
   -> 2번과 똑같은 문제다
```

| | `GROUP BY` 있음 | `GROUP BY` 없음(집계만) |
|---|---|---|
| PostgreSQL 18.6 | `column "emp.name" must appear in …` | **한 글자도 같은 메시지** |
| MySQL 8.4.10 | **`ERROR 1055`** | **`ERROR 1140`** — 번호와 문구가 다르다 |

★ **PG 가 두 경우에 같은 메시지를 내는 것 자체가 「같은 규칙의 두 모습」이라는 근거다.**\
MySQL 은 번호를 갈라 놓아 **로그에서 두 경우를 구분할 수 있다** — 옮길 때는 이게 편하다.

---

### 4. `HAVING` 과 `ORDER BY` — 3번 칸 뒤의 칸 전부

MySQL 문서가 세 자리를 한 문장에 담는다: *"MySQL rejects queries for which the select list, `HAVING` condition, or `ORDER BY` list refer to nonaggregated columns …"*.

**출력 — `ORDER BY`**

```text
### SQL: SELECT dept_id, COUNT(*) AS c FROM emp GROUP BY dept_id ORDER BY name;
--- PG 18.6 ---
ERROR:  column "emp.name" must appear in the GROUP BY clause or be used in an aggregate function
LINE 1: ...t_id, COUNT(*) AS c FROM emp GROUP BY dept_id ORDER BY name;
                                                                  ^
--- MySQL 8.4.10 ---
ERROR 1055 (42000) at line 1: Expression #1 of ORDER BY clause is not in GROUP BY clause and contains nonaggregated column 'study.emp.name' which is not functionally dependent on columns in GROUP BY clause; this is incompatible with sql_mode=only_full_group_by
```

```text
 GROUP BY (3번 칸)
   |
   +--> HAVING   (4번) -- 같은 규칙   <- 03번이 정본
   +--> SELECT   (5번) -- 같은 규칙   <- 2·3번
   +--> ORDER BY (6번) -- 같은 규칙   <- 여기
        ^
   세 칸 모두 "그룹" 만 본다. 규칙이 셋이 아니라 하나다
```

★ **경계: `HAVING` 쪽 실측과 에러, 그리고 `HAVING` 의 별칭 방언은 [03번](../03-where-vs-having/)이 정본이다.** 여기서는 **같은 규칙이 세 칸에 걸린다는 것**까지.

**`WHERE` 는 이 규칙과 무관하다.** 2번 칸이라 그룹을 아직 모르고, 대신 **집계 함수를 못 쓴다**([03번](../03-where-vs-having/)).

---

### 5. 돈다. `ann` 이 나왔다. **보장되지 않는다**

**출력**

```text
### SQL: SELECT @@sql_mode;  (MySQL 8.4.10 기본값)
ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION
```

```text
### SQL: (only_full_group_by 를 뺀 세션)
SELECT dept_id, name, salary FROM emp GROUP BY dept_id ORDER BY dept_id;
--- MySQL 8.4.10 ---
+---------+------+--------+
| dept_id | name | salary |
+---------+------+--------+
|    NULL | dan  |    400 |
|      10 | ann  |    300 |
|      20 | cho  |   NULL |
+---------+------+--------+
```

**왜 그런가**

MySQL 문서가 직접 적는다: *"the server is free to choose any value from each group, so unless they are the same, the values chosen are nondeterministic, which is probably not what you want."*

```text
 dept_id=10 봉투 안                  나온 값
 +-------------------+               +-----+
 | ann (300)         |               | ann |
 | bob (500)         |   ──?──>      +-----+
 +-------------------+                  ^
                              "엔진이 먼저 만난 행" 이지
                              "규칙이 고른 행" 이 아니다
```

★ **이 한 줄이 위험한 이유** — `salary` 열까지 같이 뽑으면 `ann` 의 300 이 따라 나온다.\
즉 **한 줄에 실린 값들이 「같은 행에서 왔다」는 것조차 보장되지 않는다.** 열마다 다른 행에서 올 수 있다.\
그러면 **실제로 존재한 적 없는 행**이 화면에 나타난다.

**PG 에는 이 스위치가 없다.** 같은 질의를 PG 에 던지면 2번의 에러 그대로다.

---

### 6. 안 된다. 그것은 **관찰**이지 **보장**이 아니다

**출력 — 10회 실행**

```text
### SQL: (only_full_group_by 를 뺀 세션) SELECT dept_id, name, salary FROM emp GROUP BY dept_id ORDER BY dept_id;
--- MySQL 8.4.10 · 같은 세션 설정으로 10회 ---
 run 1 : NULL dan 400 | 10 ann 300 | 20 cho NULL
 run 2 : NULL dan 400 | 10 ann 300 | 20 cho NULL
 run 3 : NULL dan 400 | 10 ann 300 | 20 cho NULL
 run 4 : NULL dan 400 | 10 ann 300 | 20 cho NULL
 run 5 : NULL dan 400 | 10 ann 300 | 20 cho NULL
 run 6 : NULL dan 400 | 10 ann 300 | 20 cho NULL
 run 7 : NULL dan 400 | 10 ann 300 | 20 cho NULL
 run 8 : NULL dan 400 | 10 ann 300 | 20 cho NULL
 run 9 : NULL dan 400 | 10 ann 300 | 20 cho NULL
 run 10: NULL dan 400 | 10 ann 300 | 20 cho NULL
   -> 10 / 10 동일
```

**왜 그런가**

★ **10회 같았다는 것은 「이 데이터·이 계획에서 그랬다」는 뜻일 뿐이다.**\
그리고 **바꿀 수 있다** — 같은 두 행을 **입력 순서만 뒤집어** 넣으면 값이 따라 바뀐다.

```text
### SQL: (only_full_group_by 를 뺀 세션)
SELECT dept_id, name FROM (SELECT * FROM emp WHERE id=2 UNION ALL SELECT * FROM emp WHERE id=1) t GROUP BY dept_id;
--- MySQL 8.4.10 ---
+---------+------+
| dept_id | name |
+---------+------+
|      10 | bob  |     <- bob 을 먼저 주면 bob
+---------+------+

### SQL: SELECT dept_id, name FROM (SELECT * FROM emp WHERE id=1 UNION ALL SELECT * FROM emp WHERE id=2) t GROUP BY dept_id;
--- MySQL 8.4.10 ---
+---------+------+
| dept_id | name |
+---------+------+
|      10 | ann  |     <- ann 을 먼저 주면 ann
+---------+------+
```

```text
 "10회 돌려서 같았다" 가 말해 주는 것          말해 주지 않는 것
 +-------------------------------+            +-------------------------------+
 | 이 데이터 · 이 계획에서는      |            | 다음 배포에서도 같을 것        |
 | ann 이 나왔다                  |            | 행이 늘어도 같을 것            |
 +-------------------------------+            | 인덱스를 추가해도 같을 것      |
   관찰이다                                    +-------------------------------+
                                                 보장이 아니다 — 문서가 부정한다
```

★ **같은 값이 계속 나오는 쪽이 더 위험하다.** 테스트가 통과하고 코드가 배포되고, 계획이 바뀌는 날 조용히 값이 바뀐다.\
**관찰은 관찰로, 보장은 문서로만 적는다.**

> **비결정적(nondeterministic)** — 같은 입력에 같은 답이 나온다고 **약속되지 않은** 것.\
> 예: 여기 `name`. 10회 같았지만 입력 순서를 바꾸니 달라졌다.

---

### 7. 안 된다. 문서가 부정하고 실행으로도 확인했다

MySQL 문서: *"the selection of values from each group cannot be influenced by adding an `ORDER BY` clause."*

**출력 — 네 가지로 흔들어 봤다**

```text
--- MySQL 8.4.10 (only_full_group_by 를 뺀 세션) ---
(A) SELECT dept_id, name FROM emp GROUP BY dept_id ORDER BY dept_id;
      10 -> ann
(B) SELECT dept_id, name FROM (SELECT * FROM emp ORDER BY name DESC) t GROUP BY dept_id ORDER BY dept_id;
      10 -> ann      <- 안쪽에서 역순 정렬해도 ann
(C) SELECT dept_id, name FROM emp GROUP BY dept_id ORDER BY name DESC;
      10 -> ann      <- 바깥 ORDER BY 는 "줄 순서" 만 바꾼다
(D) SELECT dept_id, name FROM emp FORCE INDEX(PRIMARY) GROUP BY dept_id ORDER BY dept_id;
      10 -> ann      <- 인덱스를 강제해도 ann
```

**왜 그런가**

```text
 ORDER BY 는 6번 칸이다
 GROUP BY(3) ──> ... ──> ORDER BY(6)
      ^                       |
      |                       |
  값은 여기서 이미 정해졌다   여기서는 "줄 순서" 만 바꾼다
```

★ **`ORDER BY` 는 값을 고르는 도구가 아니라 줄을 세우는 도구다.** 처리 순서로 보면 당연하다([01번](../01-logical-query-processing-order/)).\
(C)에서 `ORDER BY name DESC` 는 **이미 정해진 세 줄을 재배열**했을 뿐이다.

**「그룹별 특정 행」이 필요하면 도구가 다르다.**

```text
 원하는 것                          쓸 것
 그룹별 최댓값 하나                  MAX(salary)          <- 값 하나면 집계로 충분
 그룹별 최고 급여자의 "이름"          순위 함수 (29번 주제)
 그룹별 상위 N행                     순위 함수 · LATERAL (20번)
```

---

### 8. 돈다. **기본키가 `GROUP BY` 에 있으면 그룹 하나 = 행 하나**이기 때문이다

**출력**

```text
### SQL: SELECT id, name, dept_id, salary, COUNT(*) AS c FROM emp GROUP BY id ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name | dept_id | salary | c    +----+------+---------+--------+---+
----+------+---------+--------+---   | id | name | dept_id | salary | c |
  1 | ann  |      10 |    300 | 1    +----+------+---------+--------+---+
  2 | bob  |      10 |    500 | 1    |  1 | ann  |      10 |    300 | 1 |
  3 | cho  |      20 |   NULL | 1    |  2 | bob  |      10 |    500 | 1 |
  4 | dan  |    NULL |    400 | 1    |  3 | cho  |      20 |   NULL | 1 |
(4 rows)                             |  4 | dan  |    NULL |    400 | 1 |
                                     +----+------+---------+--------+---+
```

**왜 그런가**

```text
 GROUP BY id                    각 봉투 안에 행이 정확히 하나
 +----------------+             +----------------+
 | 봉투 id=1      |             | (1, ann, 10, 300) |
 | 봉투 id=2      |             | (2, bob, 10, 500) |
 | 봉투 id=3      |             | (3, cho, 20, NULL)|
 | 봉투 id=4      |             | (4, dan, NULL,400)|
 +----------------+             +----------------+
   -> name 을 꺼내라는 요구에 답이 하나뿐이다 -> 허용
```

`COUNT(*)` 이 전부 **1**인 것이 그 증거다. **이것이 함수 종속이고, 두 엔진 다 인정한다.**

> **함수 종속(functional dependency)** — 한 열의 값이 정해지면 다른 열의 값도 하나로 정해지는 관계.\
> 예: `emp.id` 가 정해지면 `emp.name` 도 하나다.

★ **주의 — 이것은 성능 최적화가 아니다.** 「기본키로 묶으면 `DISTINCT` 가 공짜」 같은 이야기가 아니라,\
**문법 검사를 통과시켜 주는 예외**일 뿐이다. 그룹 만드는 비용은 그대로 든다.

---

### 9. ★ (A)·(B) 모두 **PG 는 거부, MySQL 은 허용**한다

**출력 — (A) `UNIQUE NOT NULL` 열로 묶기**

```text
### SQL: SELECT d.id, d.name FROM dept d GROUP BY d.name ORDER BY d.name;
--- PG 18.6 ---
ERROR:  column "d.id" must appear in the GROUP BY clause or be used in an aggregate function
LINE 1: SELECT d.id, d.name FROM dept d GROUP BY d.name ORDER BY d.n...
               ^
--- MySQL 8.4.10 ---
+----+-------+
| id | name  |
+----+-------+
| 20 | dev   |
| 30 | hr    |
| 10 | sales |
+----+-------+
```

**출력 — (B) 조인 건너편의 열**

```text
### SQL: SELECT e.id, e.name, d.name AS dept, COUNT(*) AS c
         FROM emp e JOIN dept d ON e.dept_id = d.id GROUP BY e.id ORDER BY e.id;
--- PG 18.6 ---
ERROR:  column "d.name" must appear in the GROUP BY clause or be used in an aggregate function
LINE 1: SELECT e.id, e.name, d.name AS dept, COUNT(*) AS c FROM emp ...
                             ^
--- MySQL 8.4.10 ---
+----+------+-------+---+
| id | name | dept  | c |
+----+------+-------+---+
|  1 | ann  | sales | 1 |
|  2 | bob  | sales | 1 |
|  3 | cho  | dev   | 1 |
+----+------+-------+---+
```

**왜 그런가**

| 그룹 키 | 다른 열 | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|---|
| **같은 표의 기본키**(`emp.id`) | 같은 표의 열 | **허용**(8번) | **허용** |
| `UNIQUE NOT NULL` 열(`dept.name`) | 같은 표의 열 | **거부** | **허용** |
| 기본키(`emp.id`) | **조인 건너편**(`d.name`) | **거부** | **허용** |

```text
 PG 의 인정 범위                    MySQL 의 인정 범위
 +---------------------+            +--------------------------------+
 | GROUP BY 에 그 표의 |            | 기본키 또는 UNIQUE NOT NULL     |
 | 기본키가 있을 때,   |            | 그리고 조인을 건너서도 따라간다  |
 | 그 표의 열만        |            | e.id -> e.dept_id -> d.id       |
 +---------------------+            |            -> d.name            |
                                    +--------------------------------+
```

MySQL 문서가 종속의 근거를 **기본키**와 **`UNIQUE NOT NULL` 열**로 적는다.\
PG 문서는 **`GROUP BY` 에 그 표의 기본키가 포함된 경우**만 예외로 든다.

★ **갈리는 방향이 한쪽이다 — MySQL 에서 돌던 질의가 PG 에서 깨진다.**\
(B)의 `c` 가 **전부 1**인 것에 주목하라 — MySQL 이 옳게 판단하고 있다. 값이 틀린 게 아니라 **PG 가 못 알아보는 것**이다.\
그래도 **이식하려면 PG 쪽에 맞춰야 한다.** `GROUP BY e.id, e.name, d.name` 으로 다 적으면 양쪽에서 돈다.

---

### 10. `ANY_VALUE()` — PG 18.6 에도 있다

**출력**

```text
### SQL: SELECT dept_id, ANY_VALUE(name) AS a_name, COUNT(*) AS c FROM emp GROUP BY dept_id ORDER BY dept_id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | a_name | c            +---------+--------+---+
---------+--------+---           | dept_id | a_name | c |
      10 | ann    | 2            +---------+--------+---+
      20 | cho    | 1            |    NULL | dan    | 1 |
    NULL | dan    | 1            |      10 | ann    | 2 |
(3 rows)                         |      20 | cho    | 1 |
                                 +---------+--------+---+
```

**왜 그런가**

```text
 설정을 끄는 것                      ANY_VALUE 를 쓰는 것
 +---------------------------+       +---------------------------+
 | 세션·서버 전체에 걸린다     |       | 이 열 하나에만 걸린다      |
 | 코드만 보면 의도를 모른다   |       | "아무거나 좋다" 가 코드에   |
 | 다른 질의의 오타도 통과된다 |       |   적혀 있다               |
 | PG 에는 아예 없는 스위치    |       | 두 엔진 모두 있다          |
 +---------------------------+       +---------------------------+
```

★ **`ANY_VALUE` 는 값을 「고르는」 함수가 아니라 「아무 값이어도 좋다」를 **선언하는** 함수다.**\
PG 문서가 *"Returns an arbitrary value from the non-null input values"* 라고 적는다 — **arbitrary 가 계약이다.**\
값 자체는 5·6번과 똑같이 보장되지 않는다. 달라지는 것은 **읽는 사람이 그것을 안다**는 점뿐이다.

**버전** — PG 는 **16 부터**다([PG 16 릴리스 노트](https://www.postgresql.org/docs/release/16.0/): *"Add aggregate function `ANY_VALUE()` which returns any value from a set"*).\
MySQL 은 8.4 매뉴얼의 GROUP BY 처리 페이지에 있고 **도입 버전은 확인하지 못해 적지 않는다.**

★ **대표값이 「아무거나」가 아니라면 `ANY_VALUE` 를 쓰지 마라.** 「가장 이른 이름」이면 `MIN(name)` 이라고 **무엇인지 적는다.**

---

### 11. 표현식·별칭·서수는 되고, 집계는 안 된다

**출력 — 표현식**

```text
### SQL: SELECT salary * 12 AS annual, COUNT(*) AS c FROM emp GROUP BY salary * 12 ORDER BY 1;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 annual | c                      +--------+---+
--------+---                     | annual | c |
   3600 | 1                      +--------+---+
   4800 | 1                      |   NULL | 1 |
   6000 | 1                      |   3600 | 1 |
   NULL | 1                      |   4800 | 1 |
(4 rows)                         |   6000 | 1 |
                                 +--------+---+
```

**출력 — 별칭**

```text
### SQL: SELECT salary * 12 AS annual, COUNT(*) AS c FROM emp GROUP BY annual ORDER BY 1;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 annual | c                      +--------+---+
--------+---                     | annual | c |
   3600 | 1                      +--------+---+
   4800 | 1                      |   NULL | 1 |
   6000 | 1                      |   3600 | 1 |
   NULL | 1                      |   4800 | 1 |
(4 rows)                         |   6000 | 1 |
                                 +--------+---+
```

**출력 — 서수**

```text
### SQL: SELECT dept_id, COUNT(*) AS c FROM emp GROUP BY 1 ORDER BY 1;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | c                     +---------+---+
---------+---                    | dept_id | c |
      10 | 2                     +---------+---+
      20 | 1                     |    NULL | 1 |
    NULL | 1                     |      10 | 2 |
(3 rows)                         |      20 | 1 |
                                 +---------+---+
```

**출력 — 집계**

```text
### SQL: SELECT dept_id, COUNT(*) AS c FROM emp GROUP BY COUNT(*);
--- PG 18.6 ---
ERROR:  aggregate functions are not allowed in GROUP BY
LINE 1: SELECT dept_id, COUNT(*) AS c FROM emp GROUP BY COUNT(*);
                                                        ^
--- MySQL 8.4.10 ---
ERROR 1056 (42000) at line 1: Can't group on 'c'
```

**왜 그런가**

| `GROUP BY` 에 쓸 수 있나 | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| 열 | ✓ | ✓ |
| 표현식(`salary * 12`) | ✓ | ✓ |
| `SELECT` 의 열 별칭 | **✓** | **✓** |
| 서수(`GROUP BY 1`) | ✓ | ✓ |
| 집계 함수 | ✗ `aggregate functions are not allowed in GROUP BY` | ✗ `ERROR 1056 Can't group on 'c'` |

★ **`GROUP BY` 의 별칭은 양쪽에서 된다.** 갈리는 것은 `HAVING` 이다([03번](../03-where-vs-having/)이 정본 — PG 는 `column "cnt" does not exist`).\
`WHERE` 는 **양쪽 다 안 된다** — 별칭은 5번 칸에서 태어나는데 `WHERE` 는 2번 칸이다([01번](../01-logical-query-processing-order/)).

집계가 거부되는 이유는 **처리 순서**다 — 집계는 `GROUP BY` 가 그룹을 만든 **뒤**에 계산되므로 `GROUP BY` 의 입력이 될 수 없다.\
MySQL 이 별칭 `'c'` 로 부르는 것은 MySQL 이 `GROUP BY` 에서 **출력 열 이름을 먼저 찾기** 때문이다. **거부한다는 사실은 같다**([21번](../21-aggregate-functions-count-forms/)).

**서수의 대가** — `SELECT` 목록을 고치면 **조용히 다른 열로 묶인다.** 짧은 임시 질의에만 쓴다.

---

### 12. `GROUP BY` 는 **3그룹**, `COUNT(DISTINCT)` 는 **2**다

**출력**

```text
### SQL: SELECT dept_id, COUNT(*) AS c, SUM(salary) AS s FROM emp GROUP BY dept_id ORDER BY dept_id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | c |  s                +---------+---+------+
---------+---+------             | dept_id | c | s    |
      10 | 2 |  800              +---------+---+------+
      20 | 1 | NULL              |    NULL | 1 |  400 |
    NULL | 1 |  400              |      10 | 2 |  800 |
(3 rows)                         |      20 | 1 | NULL |
                                 +---------+---+------+
```

```text
### SQL: SELECT COUNT(DISTINCT dept_id) AS c_dist FROM emp;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 c_dist                          +--------+
--------                         | c_dist |
      2                          +--------+
(1 row)                          |      2 |
                                 +--------+
```

**왜 그런가**

```text
 dept_id = [10, 10, 20, NULL]

 GROUP BY dept_id        -> 3 그룹   (10 · 20 · NULL)     NULL 도 한 그룹이 된다
 COUNT(DISTINCT dept_id) -> 2        (10 · 20)            NULL 은 아예 안 센다
                              ^^^
          같은 데이터 · 같은 열인데 3 과 2 다. 규칙이 다르기 때문이다
```

```text
 비교에서는                        묶기에서는
 NULL = NULL  ->  UNKNOWN          NULL 과 NULL  ->  같은 그룹
 (같다고 하지 않는다)                (하나로 접는다)
```

★ **「세기」와 「묶기」를 나눠서 외운다.**\
`COUNT(DISTINCT)` 는 **`NULL` 을 버린 뒤** 가짓수를 세므로 `NULL` 이 한 가지로 안 잡힌다([21번](../21-aggregate-functions-count-forms/)).\
`GROUP BY` 는 **구별 불가능성**을 기준으로 삼아 `NULL` 끼리 한 그룹으로 접는다([04번](../04-null-three-valued-logic/)).

`dept_id=20` 의 `SUM` 이 `NULL` 인 것은 또 다른 규칙이다 — `cho` 의 급여가 없어서 **더할 값이 하나도 없다**([21번](../21-aggregate-functions-count-forms/)).

★ **이 `NULL` 그룹은 「소속 없음」이라는 뜻이 있는 그룹이다.**\
[23번](../23-grouping-sets-rollup-cube/)에서 **소계 행이 만드는 `NULL`** 과 이것이 한 화면에 섞인다 — 거기서 둘을 가르는 법을 본다.

> **구별 불가능성(not distinct)** — 「같다」가 아니라 「서로 구별할 수 없다」는 기준.\
> 예: `GROUP BY` 가 이 기준을 써서 `NULL` 둘을 한 그룹으로 만든다.

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| 그룹 키만 남는 것 (1번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 집계 없는 `GROUP BY` |
| 비집계 열 거부 (2·3·4번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | `SELECT`·집계만·`ORDER BY` — **전부 에러를 그대로 실었다** |
| `@@sql_mode` 확인 (5번) | MySQL 8.4.10 | 1회 | `ONLY_FULL_GROUP_BY` 가 기본에 포함 |
| ★ 끈 상태 반복 실행 (6번) | MySQL 8.4.10 | **10회** | **10/10 동일** — 그래도 보장 아님 |
| ★ 입력 순서를 뒤집기 (6번) | MySQL 8.4.10 | 각 1회 | **`ann` ↔ `bob` 으로 바뀌었다** |
| `ORDER BY`·인덱스로 흔들기 (7번) | MySQL 8.4.10 | 4회 | 네 가지 모두 `ann` — 문서대로 안 바뀐다 |
| 기본키 종속 (8번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 양쪽 허용 |
| ★ 종속성 경계 (9번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | `UNIQUE NOT NULL` · 조인 건너편 — **양쪽 다 갈렸다** |
| `ANY_VALUE()` (10번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **PG 18.6 에도 있다** |
| `GROUP BY` 에 쓸 수 있는 것 (11번) | PG 18.6 · MySQL 8.4.10 | 각 4회 | 표현식·별칭·서수·집계 |
| `NULL` 그룹 대 `COUNT(DISTINCT)` (12번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | 3 대 2 |

**구현 의존 항목** — ★ **5·6·7번 전부.** `only_full_group_by` 를 끈 뒤의 값은 **엔진이 만난 행 순서**에 달렸다.\
10회 동일은 **관찰**로만 적었고, 입력 순서를 바꿔 **반증**했다.

**방언 항목** — 2·3(에러 번호) · 5·6·7(`sql_mode` 자체가 PG 에 없다) · 9(종속성 범위) · 10(`ANY_VALUE` 도입 버전).\
**언어 보장 항목** — 1·4·8·11·12. 그룹 키와 집계만 쓸 수 있다는 규칙, 기본키 예외, `NULL` 이 한 그룹이 되는 것은 두 문서가 같은 모양으로 적는다.

**버전** — `ANY_VALUE()` 는 **PG 16+**(릴리스 노트로 확인). MySQL 쪽 도입 버전은 **확인 못 해 적지 않았다.**\
다음 버전에서 다시 볼 것 — **9번(종속성 범위)**과 **5번(`sql_mode` 기본값)**이다.
