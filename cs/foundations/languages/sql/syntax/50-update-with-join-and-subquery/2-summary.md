# sql/50-UPDATE — 조인·서브쿼리를 쓰는 갱신 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · UPDATE](https://www.postgresql.org/docs/18/sql-update.html) · [MySQL 8.4 · UPDATE Statement](https://dev.mysql.com/doc/refman/8.4/en/update.html) · [MySQL 8.4 · mysql Client Options(`--safe-updates`)](https://dev.mysql.com/doc/refman/8.4/en/mysql-command-options.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력·에러·경고는 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 지어낸 출력은 없다.\
> ★ **환경 확인** — MySQL 의 `sql_safe_updates` 기본값은 **`0`**(꺼짐)이다. 5번 절은 이 값을 세션에서 켜고 끈 결과다.\
> `sql_mode` 는 `ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION`, `autocommit=1` 이다.\
> ★ **이 편이 만든 표와 그 뒷정리** — `study` DB 에 `t50_emp`·`t50_dept`·`t50_map`·`t50_u` 를 만들었고 **전부 지웠다.** `emp`·`dept` 는 **읽지도 않았다.**\
> ★ **`WHERE` 없는 `UPDATE` 가 이 주제의 절반이다 — 그 실험은 전부 `t50_emp` 에서만 했다.**\
> **선행** — [11 서브쿼리 — 스칼라·상관·ANY/ALL](../11-subquery-scalar-correlated-any-all/)(3번 절의 뿌리) · [49 INSERT](../49-insert-multi-row-and-insert-select/)(원자성).\
> **이어지는 것** — [51 DELETE 와 TRUNCATE](../51-delete-and-truncate/) 가 같은 위험을 삭제 쪽에서 다룬다.

## 한눈에 — 쉽게 말하면

**`UPDATE` 에서 어려운 것은 「무엇으로 바꾸나」가 아니라 「어느 행을 바꾸나」다.**

```text
UPDATE 표 SET 열 = 값 WHERE 조건
             ^^^^^^^^^ 쉽다      ^^^^^^^^ ★ 여기가 전부다
```

값이 **다른 표에 있으면** 문제가 둘로 갈린다.

```text
         "이 행의 새 값은 저 표의 어느 행인가"      "짝이 없는 행은 어떻게 하나"
         ────────────────────────────────         ───────────────────────────
조인형    UPDATE ... FROM (PG)                     ★ 건드리지 않는다
         UPDATE a JOIN b SET (MySQL)
서브쿼리형 SET c = (SELECT ... WHERE 상관)          ★ NULL 로 덮어쓴다
```

일상 비유로 바꾸면 **명부 두 권을 대조해 옮겨 적는 일**이다.

```text
조인형   : 두 명부에 다 있는 사람만 찾아 옮겨 적는다. 한쪽에만 있는 줄은 그대로 둔다
서브쿼리형: 내 명부의 모든 줄을 훑으며 저쪽에서 찾아 적는다.
           ★ 못 찾은 줄에는 "빈칸"을 적는다 — 원래 적혀 있던 것을 지우면서
```

"똑같은 구조다" — **의도가 같은 두 문장이 짝 없는 행에서 다른 답을 낸다.** 그것도 **에러 없이.**

| 비유 | 실체 |
|---|---|
| 두 명부에 다 있는 줄만 | `UPDATE ... FROM` · `UPDATE a JOIN b` |
| 내 명부 전부를 훑는다 | `SET c = (상관 서브쿼리)` |
| ★ 못 찾은 줄에 빈칸을 적는다 | **`NULL` 로 덮어쓴다** — 이 편의 핵심 사고 |
| 명부 이름을 서로 못 알아듣는다 | `FROM`(PG) 과 `JOIN`(MySQL) 의 상호 거부 |
| 조건 없이 전 장을 고친다 | `WHERE` 를 빠뜨린 `UPDATE` |
| 「키로 지목한 줄만 고치게 해 주세요」 | **MySQL 의 `sql_safe_updates`** |

★ **이 편에서 가장 값비싼 두 줄**

1. **`SET a = b, b = a` 가 PG 에서는 교환, MySQL 에서는 교환이 아니다.** 에러도 경고도 없다(6번).
2. **상관 서브쿼리 갱신은 짝 없는 행을 `NULL` 로 덮어쓴다.** 두 엔진에서 똑같이(3번).

## 이 주제가 답하려는 질문

1. **다른 표의 값으로 갱신하는 문을 두 엔진에서 어떻게 쓰나?** — 그리고 왜 서로 안 통하나.
2. **짝이 없는 행은 어떻게 되나?** — 조인형과 서브쿼리형이 어디서 갈리나.
3. **`WHERE` 를 빠뜨리면 무엇이 막아 주나?** — 막아 주는 것이 있기는 한가.

## 예시 데이터 — 이 편이 만든 표

★ **`emp`·`dept` 는 한 줄도 쓰지 않았다.** 이름만 같게 만든 **내 표**다 — `WHERE` 없는 갱신을 실험하기 때문이다.

```text
t50_emp                                        t50_dept
+----+------+---------+--------+-----------+   +----+-------+-------+
| id | name | dept_id | salary | dept_name |   | id | name  | bonus |
+----+------+---------+--------+-----------+   +----+-------+-------+
|  1 | ann  |      10 |    300 | NULL      |   | 10 | sales |    50 |
|  2 | bob  |      10 |    500 | NULL      |   | 20 | dev   |    70 |
|  3 | cho  |      20 |   NULL | NULL      |   | 30 | hr    |    10 |
|  4 | dan  |    NULL |    400 | NULL      |   +----+-------+-------+
+----+------+---------+--------+-----------+

★ id=4 (dan) 은 dept_id 가 NULL 이다 — 「짝이 없는 행」이다. 이 편의 주인공이다.

t50_map (짝이 둘인 실험용)        t50_u (원자성 실험용)
+---------+-------+               +----+----+
| dept_id | label |               | id | v  |
+---------+-------+               +----+----+
|      10 | AAA   |               |  1 | 10 |
|      10 | ZZZ   |   <- 같은 키가 둘 |  2 | 20 |
+---------+-------+               |  3 | 30 |
                                  +----+----+
```

아래 실험은 전부 **PG 는 `BEGIN`/`ROLLBACK`, MySQL 은 `START TRANSACTION`/`ROLLBACK`** 으로 감쌌다.\
그래서 기준 상태는 매번 위 그림과 같다.

## 동작 방식

### 1. ★★ 방언이 정면으로 갈린다 — `FROM` 대 `JOIN`

**언제 쓰나** — 다른 표의 값으로 갱신할 때. **이식성이 여기서 0이 된다.**

```text
PostgreSQL                              MySQL
UPDATE t50_emp e                        UPDATE t50_emp e
  SET dept_name = d.name                  JOIN t50_dept d ON d.id = e.dept_id
  FROM t50_dept d                         SET e.dept_name = d.name;
  WHERE d.id = e.dept_id;                     ^^^
      ^^^^                                  SET 이 조인 뒤에 온다
    FROM 이 SET 뒤에 온다
```

**PG 쪽 실제 출력.**

```text
BEGIN;
UPDATE t50_emp e SET dept_name = d.name FROM t50_dept d WHERE d.id = e.dept_id;
UPDATE 3
SELECT * FROM t50_emp ORDER BY id;
 id | name | dept_id | salary | dept_name 
----+------+---------+--------+-----------
  1 | ann  |      10 |    300 | sales
  2 | bob  |      10 |    500 | sales
  3 | cho  |      20 |        | dev
  4 | dan  |         |    400 |             <- ★ 짝이 없어 안 건드렸다
(4 rows)
ROLLBACK;
```

**MySQL 쪽 실제 출력.**

```text
START TRANSACTION;
UPDATE t50_emp e JOIN t50_dept d ON d.id = e.dept_id SET e.dept_name = d.name;
SELECT ROW_COUNT() AS affected;
+----------+
| affected |
+----------+
|        3 |
+----------+
SELECT * FROM t50_emp ORDER BY id;
+----+------+---------+--------+-----------+
| id | name | dept_id | salary | dept_name |
+----+------+---------+--------+-----------+
|  1 | ann  |      10 |    300 | sales     |
|  2 | bob  |      10 |    500 | sales     |
|  3 | cho  |      20 |   NULL | dev       |
|  4 | dan  |    NULL |    400 | NULL      |   <- ★ 여기도 안 건드렸다
+----+------+---------+--------+-----------+
ROLLBACK;
```

**결과는 똑같다.** 그런데 **서로의 문법을 정확히 거부한다.**

```text
### SQL: UPDATE t50_emp e SET dept_name = d.name FROM t50_dept d WHERE d.id = e.dept_id;
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that
  corresponds to your MySQL server version for the right syntax to use near
  'FROM t50_dept d WHERE d.id = e.dept_id' at line 1

### SQL: UPDATE t50_emp e JOIN t50_dept d ON d.id = e.dept_id SET e.dept_name = d.name;
--- PG 18.6 ---
ERROR:  syntax error at or near "JOIN"
LINE 1: UPDATE t50_emp e JOIN t50_dept d ON d.id = e.dept_id SET e.d...
                         ^
```

두 그림의 결론 — **같은 일을 하는 두 문장이 서로의 엔진에서 한 글자도 안 돈다.**\
[13 번의 `JOIN … ON` 누락](../13-inner-join/)·[45 번의 자동 증가](../45-check-not-null-default-generated-columns/)와 달리 **여기는 조용한 통과가 없다** — 둘 다 시끄럽다. 그 점은 안전하다.

비용 — **이식 가능한 형태가 필요하면 3번의 상관 서브쿼리를 쓴다. 다만 의미가 달라진다.**

> **다중 표 `UPDATE`(multi-table UPDATE)** — 갱신 대상 외의 표를 같이 읽어 값을 가져오는 갱신문.\
> 예: 사원 표의 부서명 칸을 부서 표에서 가져와 채우는 것.

### 2. 짝이 없는 행은 안 건드린다 — 조인형의 규칙

**언제 쓰나** — 1번의 결과를 해석할 때. **이 규칙이 3번과 대비되는 축이다.**

`dept_name` 을 먼저 `'(old)'` 로 채워 두고 같은 갱신을 돌리면 규칙이 눈에 보인다.

```text
(전) t50_emp — 전부 '(old)'
+----+------+---------+-----------+
| id | name | dept_id | dept_name |
+----+------+---------+-----------+
|  1 | ann  |      10 | (old)     |
|  2 | bob  |      10 | (old)     |
|  3 | cho  |      20 | (old)     |
|  4 | dan  |    NULL | (old)     |   <- 짝이 없다
+----+------+---------+-----------+
   ↓ UPDATE ... FROM (조인형)
```

```text
BEGIN;
UPDATE t50_emp SET dept_name='(old)';
UPDATE 4
UPDATE t50_emp e SET dept_name = d.name FROM t50_dept d WHERE d.id = e.dept_id;
UPDATE 3                                  <- ★ 4가 아니라 3이다
SELECT * FROM t50_emp ORDER BY id;
 id | name | dept_id | salary | dept_name 
----+------+---------+--------+-----------
  1 | ann  |      10 |    300 | sales
  2 | bob  |      10 |    500 | sales
  3 | cho  |      20 |        | dev
  4 | dan  |         |    400 | (old)      <- ★ 그대로 살아 있다
(4 rows)
ROLLBACK;
```

MySQL 도 같다.

```text
START TRANSACTION;
UPDATE t50_emp SET dept_name='(old)';
UPDATE t50_emp e JOIN t50_dept d ON d.id = e.dept_id SET e.dept_name = d.name;
SELECT * FROM t50_emp ORDER BY id;
+----+------+---------+--------+-----------+
| id | name | dept_id | salary | dept_name |
+----+------+---------+--------+-----------+
|  1 | ann  |      10 |    300 | sales     |
|  2 | bob  |      10 |    500 | sales     |
|  3 | cho  |      20 |   NULL | dev       |
|  4 | dan  |    NULL |    400 | (old)     |   <- ★ 그대로다
+----+------+---------+--------+-----------+
ROLLBACK;
```

그림 해설 — **조인이 안 붙은 행은 `UPDATE` 의 대상 집합에 아예 안 들어간다.**\
[13 INNER JOIN](../13-inner-join/)에서 짝 없는 행이 사라지는 것과 같은 규칙이 **갱신 대상**에 적용된 것이다.

비용 — **「값이 없는 행을 비워 두고 싶다」면 이 형태로는 안 된다.** 그때가 3번이다.

### 3. ★★ 상관 서브쿼리 갱신 — **짝이 없으면 `NULL` 로 덮어쓴다**

**언제 쓰나** — 이식 가능한 형태가 필요할 때. **그리고 이 편에서 가장 조용한 사고가 나는 자리다.**

```sql
UPDATE t50_emp e SET dept_name = (SELECT d.name FROM t50_dept d WHERE d.id = e.dept_id);
```

**두 엔진에서 다 돈다** — 이식 형태가 맞다. 그런데 **1번과 결과가 다르다.**

```text
(전) t50_emp — 전부 '(old)'                (후) 상관 서브쿼리 갱신
+----+---------+-----------+               +----+---------+-----------+
| id | dept_id | dept_name |               | id | dept_id | dept_name |
+----+---------+-----------+               +----+---------+-----------+
|  1 |      10 | (old)     |               |  1 |      10 | sales     |
|  2 |      10 | (old)     |      →        |  2 |      10 | sales     |
|  3 |      20 | (old)     |               |  3 |      20 | dev       |
|  4 |    NULL | (old)     |               |  4 |    NULL | ★ NULL    |
+----+---------+-----------+               +----+---------+-----------+
                                             ★ '(old)' 가 지워졌다
```

```text
BEGIN;
UPDATE t50_emp SET dept_name='(old)';
UPDATE 4
UPDATE t50_emp e SET dept_name = (SELECT d.name FROM t50_dept d WHERE d.id = e.dept_id);
UPDATE 4                                    <- ★ 3이 아니라 4다
SELECT * FROM t50_emp ORDER BY id;
 id | name | dept_id | salary | dept_name 
----+------+---------+--------+-----------
  1 | ann  |      10 |    300 | sales
  2 | bob  |      10 |    500 | sales
  3 | cho  |      20 |        | dev
  4 | dan  |         |    400 |             <- ★ '(old)' 가 NULL 이 됐다
(4 rows)
ROLLBACK;
```

MySQL 도 **데이터는 똑같이 된다.**

```text
START TRANSACTION;
UPDATE t50_emp SET dept_name='(old)';
UPDATE t50_emp e SET dept_name = (SELECT d.name FROM t50_dept d WHERE d.id = e.dept_id);
SELECT * FROM t50_emp ORDER BY id;
+----+------+---------+--------+-----------+
| id | name | dept_id | salary | dept_name |
+----+------+---------+--------+-----------+
|  1 | ann  |      10 |    300 | sales     |
|  2 | bob  |      10 |    500 | sales     |
|  3 | cho  |      20 |   NULL | dev       |
|  4 | dan  |    NULL |    400 | NULL      |   <- ★ 여기도 지워졌다
+----+------+---------+--------+-----------+
ROLLBACK;
```

**왜 그런가 — [11 번의 규칙](../11-subquery-scalar-correlated-any-all/)이 그대로다.**

```text
스칼라 서브쿼리가 0행을 돌려주면 에러가 아니라 NULL 이다   <- 11번 4절

  e.dept_id = 10   -> 서브쿼리가 'sales' 1행 -> 'sales' 를 쓴다
  e.dept_id = NULL -> 서브쿼리가 0행         -> ★ NULL 을 쓴다 (건너뛰는 게 아니다)
```

**`UPDATE` 는 `WHERE` 가 고른 행을 전부 갱신한다.** `WHERE` 가 없으니 **네 행이 다 대상**이고,\
네 번째 행의 새 값이 `NULL` 이었을 뿐이다.

```text
조인형      : 대상 집합 = 짝이 있는 행     -> 짝 없는 행은 손대지 않는다
서브쿼리형   : 대상 집합 = WHERE 가 고른 행 -> 짝 없는 행에 NULL 을 쓴다
```

대가 — **에러도 경고도 없다.** 운영 중인 표에서 이 문을 돌리면 **짝 없는 행의 기존 값이 조용히 사라진다.**

**처방** — 서브쿼리형을 쓸 거면 **`WHERE EXISTS` 로 대상 집합을 좁힌다.**

```text
BEGIN;
UPDATE t50_emp SET dept_name='(old)';
UPDATE t50_emp e SET dept_name = (SELECT d.name FROM t50_dept d WHERE d.id = e.dept_id)
  WHERE EXISTS (SELECT 1 FROM t50_dept d WHERE d.id = e.dept_id);
UPDATE 3                                   <- ★ 3으로 돌아왔다
SELECT * FROM t50_emp ORDER BY id;
 id | name | dept_id | salary | dept_name 
----+------+---------+--------+-----------
  1 | ann  |      10 |    300 | sales
  2 | bob  |      10 |    500 | sales
  3 | cho  |      20 |        | dev
  4 | dan  |         |    400 | (old)      <- ★ 살아남았다
(4 rows)
ROLLBACK;
```

같은 조건을 **두 번 적어야 한다** — `SET` 에 한 번, `WHERE` 에 한 번. 그 중복이 이 형태의 값이다.\
`EXISTS` 자체는 [19 SEMI·ANTI 조인](../19-semi-anti-join/)이 정본이다.

★ **영향 행 수는 두 엔진이 다르게 센다.** `dept_name` 이 원래 `NULL` 인 상태에서 같은 문을 돌리면,

```text
--- PG 18.6 ---            --- MySQL 8.4.10 ---
UPDATE 4                   affected = 3
```

**PG 는 「대상이 된 행 수」를, MySQL 은 「값이 실제로 바뀐 행 수」를 센다.**\
같은 사실을 [52 번의 upsert 영향 행 수](../52-upsert/)가 「무변화 = 0」으로 보여 준다.

### 4. 짝이 둘이면 — **조인형은 조용히 하나를 고르고, 서브쿼리형은 에러다**

**언제 쓰나** — 원본 표에 중복 키가 있을 수 있을 때. **원본을 믿을 수 없는 배치에서 난다.**

```text
t50_map
+---------+-------+
| dept_id | label |
+---------+-------+
|      10 | AAA   |    <- dept_id=10 이 둘
|      10 | ZZZ   |
+---------+-------+
```

```text
(A) 조인형 — PG                              (B) 조인형 — MySQL
BEGIN;                                       START TRANSACTION;
UPDATE t50_emp e SET dept_name = m.label     UPDATE t50_emp e
  FROM t50_map m WHERE m.dept_id=e.dept_id;    JOIN t50_map m ON m.dept_id=e.dept_id
ROLLBACK;                                      SET e.dept_name = m.label;
                                             ROLLBACK;
--- 실제 출력 ---                            --- 실제 출력 ---
UPDATE 2                                     affected = 2
 id | name | dept_name                       +----+------+-----------+
----+------+-----------                      | id | name | dept_name |
  1 | ann  | AAA                             +----+------+-----------+
  2 | bob  | AAA                             |  1 | ann  | AAA       |
  3 | cho  |                                 |  2 | bob  | AAA       |
  4 | dan  |                                 |  3 | cho  | NULL      |
(4 rows)                                     |  4 | dan  | NULL      |
                                             +----+------+-----------+
   -> 둘 중 하나(AAA)를 조용히 골랐다            -> 여기도 조용히 AAA
```

```text
(C) 서브쿼리형 — 양쪽
### SQL: UPDATE t50_emp e SET dept_name = (SELECT m.label FROM t50_map m WHERE m.dept_id = e.dept_id);
--- PG 18.6 ---
ERROR:  more than one row returned by a subquery used as an expression
--- MySQL 8.4.10 ---
ERROR 1242 (21000) at line 1: Subquery returns more than 1 row
```

두 그림의 결론 — **조인형은 「둘 중 하나」를 말없이 쓰고, 서브쿼리형은 거부한다.**\
3번에서는 서브쿼리형이 위험했는데, **여기서는 서브쿼리형이 안전하다.** 축이 다르다.

```text
짝이 0개일 때  : 조인형 안전 (안 건드림) / 서브쿼리형 위험 (NULL 덮어쓰기)
짝이 2개일 때  : 조인형 위험 (조용히 하나) / 서브쿼리형 안전 (에러)
```

PG 문서가 조인형의 이 성질을 문장으로 적는다 — 인용한다.

> "When using `FROM` you should ensure that the join produces at most one output row for each row to be modified. In other words, a target row shouldn't join to more than one row from the other table(s). If it does, then only one of the join rows will be used to update the target row, but **which one will be used is not readily predictable**."\
> — [PostgreSQL 18 · UPDATE](https://www.postgresql.org/docs/18/sql-update.html)

★ **이 실험에서 PG 는 세 판 모두 `AAA` 를 골랐다.** 그러나 **그것은 관찰이지 보장이 아니다** —\
문서가 「예측 가능하지 않다」고 명시했으므로 **`AAA` 를 기대하는 코드를 쓰면 안 된다.**\
([작성법 §2-1](../../../../../../reference/study-note-guide.md)의 「여러 번 같았다는 것은 보장이 아니다」가 그대로 적용되는 자리다.)

### 5. ★ `WHERE` 를 빠뜨리면 — 그리고 무엇이 막아 주나

**언제 쓰나** — 손으로 SQL 을 치는 순간마다. **이 절을 읽는 이유는 문법이 아니라 사고 예방이다.**

```text
### SQL: UPDATE t50_emp SET salary = 0;
--- PG 18.6 ---                            --- MySQL 8.4.10 ---
UPDATE 4                                   affected = 4
 id | name | dept_id | salary              +----+------+---------+--------+
----+------+---------+--------              | id | name | dept_id | salary |
  1 | ann  |      10 |      0              +----+------+---------+--------+
  2 | bob  |      10 |      0              |  1 | ann  |      10 |      0 |
  3 | cho  |      20 |      0              |  2 | bob  |      10 |      0 |
  4 | dan  |         |      0              |  3 | cho  |      20 |      0 |
(4 rows)                                   |  4 | dan  |    NULL |      0 |
                                           +----+------+---------+--------+
```

**전부다.** 경고도 확인도 없다. `salary` 가 `NULL` 이던 행까지 `0` 이 됐다.

★ **MySQL 에는 안전장치가 하나 있다 — 켜져 있지 않을 뿐이다.**

```text
### SQL: SELECT @@sql_safe_updates;
--- MySQL 8.4.10 ---
+--------------------+
| @@sql_safe_updates |
+--------------------+
|                  0 |          <- ★ 기본은 꺼짐
+--------------------+
```

켜고 네 가지를 던졌다.

```text
### SQL: SET sql_safe_updates = 1; UPDATE t50_emp SET salary = 0;
--- MySQL 8.4.10 ---
ERROR 1175 (HY000) at line 1: You are using safe update mode and you tried to update a table
  without a WHERE that uses a KEY column.

### SQL: SET sql_safe_updates = 1; UPDATE t50_emp SET salary = 0 WHERE name = 'ann';
--- MySQL 8.4.10 ---
ERROR 1175 (HY000) at line 1: You are using safe update mode and you tried to update a table
  without a WHERE that uses a KEY column.          <- ★ WHERE 가 있는데도 막혔다

### SQL: SET sql_safe_updates = 1; START TRANSACTION; UPDATE t50_emp SET salary = 0 WHERE id = 1; SELECT ROW_COUNT() AS affected; ROLLBACK;
--- MySQL 8.4.10 ---
+----------+
| affected |
+----------+
|        1 |                                       <- id 는 기본키다. 통과
+----------+

### SQL: SET sql_safe_updates = 1; UPDATE t50_emp SET salary = 0 WHERE salary > 0;
--- MySQL 8.4.10 ---
ERROR 1175 (HY000) at line 1: You are using safe update mode and you tried to update a table
  without a WHERE that uses a KEY column.
```

★ **그런데 `LIMIT` 하나면 통과한다.**

```text
### SQL: SET sql_safe_updates = 1; START TRANSACTION; UPDATE t50_emp SET salary = 0 WHERE salary > 0 LIMIT 10; SELECT ROW_COUNT() AS affected; ROLLBACK;
--- MySQL 8.4.10 ---
+----------+
| affected |
+----------+
|        3 |                                       <- ★ 세 행이 바뀌었다
+----------+
```

매뉴얼이 규칙을 그대로 적는다.

> "If this option is enabled, `UPDATE` and `DELETE` statements that do not use a key in the `WHERE` clause or a `LIMIT` clause produce an error."\
> — [MySQL 8.4 · mysql Client Options](https://dev.mysql.com/doc/refman/8.4/en/mysql-command-options.html)

그림으로 정리하면 이렇다.

```text
sql_safe_updates 가 보는 것
  WHERE 에 키(인덱스) 열이 있나  -> 있으면 통과
  LIMIT 이 있나                 -> 있으면 통과      ★ 행 수와 무관하다
  둘 다 없나                    -> ERROR 1175

★ "몇 행이 바뀌나" 를 보는 것이 아니다.
   WHERE salary > 0 LIMIT 10 은 3행을 바꾸면서 통과했고,
   WHERE name = 'ann' 은 1행만 바꾸는데도 막혔다.
```

**PG 에는 같은 변수가 없다.**

```text
### SQL: SET sql_safe_updates = 1;
--- PG 18.6 ---
ERROR:  unrecognized configuration parameter "sql_safe_updates"
```

대가 — **안전장치는 「키를 썼나」만 본다.** 기본키 하나로 표 전체를 지목할 수 있는 스키마라면 아무것도 못 막는다.\
★ 그리고 [51 번에서 보겠지만 **`TRUNCATE` 는 이 장치가 아예 못 본다.**](../51-delete-and-truncate/)

**처방** — 안전장치보다 먼저 쓸 습관은 하나다. **`SELECT` 로 먼저 세고, 그 `WHERE` 를 그대로 옮긴다.**

```sql
SELECT count(*) FROM t50_emp WHERE <조건>;   -- 먼저 이 숫자를 본다
UPDATE t50_emp SET ... WHERE <조건>;         -- 같은 조건을 붙여 넣는다
```

PG 라면 [`RETURNING`](../54-returning-and-data-modifying-cte/)으로 **바뀐 행을 눈으로 확인**하면서 트랜잭션 안에서 돌릴 수 있다.

### 6. ★★ `SET` 목록 안의 순서 — **PG 는 동시, MySQL 은 왼쪽부터**

**언제 쓰나** — 두 열의 값을 서로 바꿀 때. **같은 문장이 다른 답을 내는데 에러가 없다.**

```sql
UPDATE t50_emp SET dept_id = salary, salary = dept_id WHERE id = 1;
--                 ^^^^^^^^^^^^^^^^  ^^^^^^^^^^^^^^^^
--                 오른쪽의 salary 는 「바뀌기 전」인가 「바뀐 뒤」인가?
```

`id=1` 은 `dept_id=10`, `salary=300` 이다.

```text
(A) PostgreSQL 18.6                      (B) MySQL 8.4.10
BEGIN;                                   START TRANSACTION;
UPDATE t50_emp                           UPDATE t50_emp
  SET dept_id = salary,                    SET dept_id = salary,
      salary  = dept_id                        salary  = dept_id
  WHERE id = 1;                            WHERE id = 1;
SELECT id, dept_id, salary                SELECT id, dept_id, salary
  FROM t50_emp WHERE id=1;                  FROM t50_emp WHERE id=1;
ROLLBACK;                                ROLLBACK;
--- 실제 출력 ---                        --- 실제 출력 ---
 id | dept_id | salary                   +----+---------+--------+
----+---------+--------                  | id | dept_id | salary |
  1 |     300 |     10                   +----+---------+--------+
(1 row)                                  |  1 |     300 |    300 |
                                         +----+---------+--------+
   -> ★ 값이 교환됐다                       -> ★ 둘 다 300 이다. 10 이 사라졌다
```

두 그림의 결론 — **PG 는 오른쪽 식을 전부 「갱신 전 행」에 대고 평가**하고,\
**MySQL 은 왼쪽부터 차례로 대입해 두 번째 식이 이미 바뀐 값을 본다.**

```text
PG      : (dept_id, salary) = (salary_old, dept_id_old) = (300, 10)
MySQL   : dept_id := salary(=300)            -> dept_id 가 300 이 된다
          salary  := dept_id(=이제 300)      -> salary 도 300
```

매뉴얼이 MySQL 쪽을 명시한다.

> "Single-table `UPDATE` assignments are generally evaluated from left to right. For multiple-table updates, there is no guarantee that assignments are carried out in any particular order."\
> — [MySQL 8.4 · UPDATE Statement](https://dev.mysql.com/doc/refman/8.4/en/update.html)

대가 — **에러도 경고도 없고, 이식했을 때 데이터만 조용히 달라진다.**\
★ 다중 표 갱신에서는 **MySQL 자신도 순서를 보장하지 않는다** — 그쪽에서는 이 관용구를 쓰면 안 된다.

**처방** — 교환이 필요하면 **임시 값을 쓰거나** PG 의 다중 열 대입 문법을 쓴다.

```sql
-- PG 전용, 의도가 문장에 드러난다
UPDATE t50_emp SET (dept_id, salary) = (salary, dept_id) WHERE id = 1;
```

### 7. `UPDATE` 도 문 하나가 원자 단위다

**언제 쓰나** — 갱신이 중간에 제약을 어길 때. [49 번](../49-insert-multi-row-and-insert-select/)과 같은 성질인지 확인하는 자리다.

`t50_u` 에서 `v >= 20` 인 두 행의 `id` 를 **둘 다 99 로** 바꾸려 한다 — 두 번째에서 기본키가 충돌한다.

```text
### SQL: UPDATE t50_u SET id = 99 WHERE v >= 20;
--- PG 18.6 ---
ERROR:  duplicate key value violates unique constraint "t50_u_pkey"
DETAIL:  Key (id)=(99) already exists.
--- MySQL 8.4.10 ---
ERROR 1062 (23000) at line 1: Duplicate entry '99' for key 't50_u.PRIMARY'

### SQL: SELECT * FROM t50_u ORDER BY id;
--- PG 18.6 ---            --- MySQL 8.4.10 ---
 id | v                    +----+------+
----+----                  | id | v    |
  1 | 10                   +----+------+
  2 | 20                   |  1 |   10 |
  3 | 30                   |  2 |   20 |
(3 rows)                   |  3 |   30 |
                           +----+------+
```

**아무것도 안 바뀌었다** — 49 번 2절과 같다.

★ **그리고 MySQL 에는 여기에도 `IGNORE` 가 있다.**

```text
### SQL: UPDATE IGNORE t50_u SET id = 99 WHERE v >= 20; SHOW WARNINGS;
--- MySQL 8.4.10 ---
+---------+------+----------------------------------------------+
| Level   | Code | Message                                      |
+---------+------+----------------------------------------------+
| Warning | 1062 | Duplicate entry '99' for key 't50_u.PRIMARY' |
+---------+------+----------------------------------------------+

### SQL: SELECT * FROM t50_u ORDER BY id;
--- MySQL 8.4.10 ---
+----+------+
| id | v    |
+----+------+
|  1 |   10 |
|  3 |   30 |     <- ★ 이 행은 안 바뀌었고
| 99 |   20 |     <- ★ 이 행은 바뀌었다
+----+------+
```

**반만 갱신됐다.** [49 번 7절의 `INSERT IGNORE`](../49-insert-multi-row-and-insert-select/)와 같은 구조다 —\
**에러가 경고로 내려앉으면 문이 안 죽고, 문이 안 죽으면 나머지가 계속 처리된다.**

비용 — `UPDATE IGNORE` 를 쓴 문은 **「성공」을 돌려주고도 절반만 반영돼 있을 수 있다.**

## 문법 — 어느 절에서 무엇이 갈리나

```sql
-- 공통 (두 엔진 다 통과)
UPDATE t SET a = 1, b = 2 WHERE ...;
UPDATE t SET a = (SELECT ... WHERE ... = t.k);        -- 상관 서브쿼리 (이식 형태)
UPDATE t SET a = DEFAULT WHERE ...;                   -- 기본값으로 되돌리기

-- 다른 표의 값으로 (서로를 거부한다)
UPDATE t SET a = s.a FROM s WHERE s.k = t.k;          -- PG.    MySQL 은 ERROR 1064
UPDATE t JOIN s ON s.k = t.k SET t.a = s.a;           -- MySQL. PG 는 syntax error

-- PG 만
UPDATE t SET (a, b) = (b, a) WHERE ...;               -- 다중 열 대입
UPDATE t SET ... RETURNING ...;                       -- 54번
-- MySQL 만
UPDATE t SET ... ORDER BY k LIMIT n;                  -- 단일 표에서만
UPDATE IGNORE t SET ...;                              -- 에러를 경고로
```

★ **`ORDER BY`·`LIMIT` 은 MySQL 의 단일 표 갱신에만 있다.**

```text
### SQL: UPDATE t50_emp SET salary = 0 ORDER BY id LIMIT 1;
--- PG 18.6 ---
ERROR:  syntax error at or near "ORDER"
LINE 1: UPDATE t50_emp SET salary = 0 ORDER BY id LIMIT 1
                                      ^
--- MySQL 8.4.10 ---
(성공)
### SQL: SELECT id,salary FROM t50_emp ORDER BY id;
--- MySQL 8.4.10 ---
+----+--------+
| id | salary |
+----+--------+
|  1 |      0 |     <- 한 행만 바뀌었다
|  2 |    500 |
|  3 |   NULL |
|  4 |    400 |
+----+--------+

### SQL: UPDATE t50_emp e JOIN t50_dept d ON d.id=e.dept_id SET e.salary = 0 ORDER BY e.id LIMIT 1;
--- MySQL 8.4.10 ---
ERROR 1221 (HY000) at line 1: Incorrect usage of UPDATE and ORDER BY
```

> "For multiple-table syntax, `ORDER BY` and `LIMIT` cannot be used."\
> — [MySQL 8.4 · UPDATE Statement](https://dev.mysql.com/doc/refman/8.4/en/update.html)

#### 방언 요약

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| 다른 표의 값으로 | `SET … FROM 표 WHERE 조인조건` | `표 JOIN 표 ON … SET …` |
| 서로의 문법 | MySQL 형태는 `syntax error at or near "JOIN"` | PG 형태는 `ERROR 1064` |
| 이식 형태 | `SET c = (상관 서브쿼리)` — **양쪽 다 된다** | 〃 |
| 짝이 둘일 때 조인형 | **조용히 하나**(문서: not readily predictable) | **조용히 하나** |
| 짝이 둘일 때 서브쿼리형 | `more than one row returned…` | `ERROR 1242` |
| `SET` 목록 평가 | **동시**(갱신 전 행 기준) | ★ **왼쪽부터 순차** |
| 다중 열 대입 | `SET (a,b) = (b,a)` | 없음 |
| `ORDER BY`/`LIMIT` | **없다**(구문 오류) | 단일 표에서만(`ERROR 1221`) |
| 영향 행 수 | **대상이 된 행 수** | **값이 실제 바뀐 행 수** |
| `WHERE` 없는 갱신 방지 | 없다(`sql_safe_updates` 자체가 없다) | `sql_safe_updates`(**기본 꺼짐**) |
| 에러를 경고로 | 없다 | `UPDATE IGNORE` |
| `RETURNING` | 있다([54번](../54-returning-and-data-modifying-cte/)) | 없다 |

## 어디서 틀리나

1. ★★ **상관 서브쿼리 갱신에 `WHERE EXISTS` 를 안 붙인다.**\
   짝 없는 행의 기존 값이 **`NULL` 로 지워진다**(3번). 에러도 경고도 없다.
2. ★★ **`SET a = b, b = a` 가 어디서나 교환이라고 생각한다.**\
   **MySQL 에서는 교환이 아니다**(6번). 이식할 때 데이터만 조용히 달라진다.
3. **`UPDATE … FROM` 을 표준으로 안다.** MySQL 은 `ERROR 1064` 다(1번). 반대도 마찬가지다.
4. **조인형에서 원본의 중복을 확인하지 않는다.**\
   짝이 둘이면 **어느 값이 쓰일지 문서가 「예측 가능하지 않다」고 적는다**(4번).
5. **영향 행 수를 두 엔진에서 같게 기대한다.**\
   **PG 는 대상 행 수, MySQL 은 실제로 바뀐 행 수**다(3번). 「0이면 실패」로 짠 코드가 오판한다.
6. **`sql_safe_updates` 를 「대량 갱신 방지」로 이해한다.**\
   **행 수를 안 본다.** `LIMIT` 만 붙이면 통과하고, 인덱스 없는 열의 `WHERE` 는 1행이어도 막힌다(5번).
7. **`sql_safe_updates` 가 켜져 있을 거라고 가정한다.** 이 서버의 기본값은 **0** 이었다.
8. **`UPDATE IGNORE` 를 안전장치로 쓴다.**\
   **반만 갱신된 채로 성공을 돌려준다**(7번). `SHOW WARNINGS` 를 안 읽으면 흔적이 없다.
9. **`UPDATE … LIMIT` 이 이식 가능하다고 생각한다.** PG 에는 없다(문법 절).
10. **갱신 대상을 `SELECT` 로 먼저 세지 않는다.**\
    `WHERE` 를 그대로 옮겨 붙이는 습관 하나가 이 편의 사고 대부분을 막는다.

## 구현 세부사항 대 언어 보장

| | 언어(문서)가 보장하는 것 | 구현이 정하는 것 |
|---|---|---|
| 짝 없는 행 (조인형) | 갱신 대상에 안 들어간다 | — (두 엔진이 같았다) |
| 짝 없는 행 (서브쿼리형) | 0행 스칼라 서브쿼리는 `NULL`([11번](../11-subquery-scalar-correlated-any-all/)) | — (두 엔진이 같았다) |
| 다중 표 갱신 문법 | — | ★ **전부**(`FROM` 대 `JOIN`) |
| 짝이 둘일 때 조인형 | **PG 문서: 「예측 가능하지 않다」** | 실제로 어느 행이 쓰이나 |
| `SET` 목록 평가 순서 | **MySQL 문서: 「왼쪽에서 오른쪽」** | ★ PG 는 동시 — **두 문서가 서로 다른 것을 보장한다** |
| 영향 행 수의 정의 | — | **대상 행 수인가 변경 행 수인가** |
| `sql_safe_updates` | MySQL 문서: 키 또는 `LIMIT` 이 없으면 에러 | MySQL 전용 |
| 문 원자성 | 실패한 문의 변경은 취소된다 | `IGNORE` 로 포기할 수 있다(MySQL) |

- ★ **4번의 「세 판 다 `AAA`」는 관찰이다.** 문서가 명시적으로 「예측 가능하지 않다」고 적었으므로\
  **반복 실행이 같았다는 것이 보장의 근거가 되지 않는다.**
- **`t50_u_pkey` 대 `t50_u.PRIMARY` 같은 제약 이름 표기**는 구현 세부다.

## 언제 쓰고 언제 안 쓰나

- **쓴다 — 조인형(`FROM`/`JOIN`).** 「짝이 있는 행만 고친다」가 의도일 때. 대부분이 여기다.
- **쓴다 — 서브쿼리형 + `WHERE EXISTS`.** 이식성이 필요할 때. 조건을 두 번 적는 값을 치른다.
- **쓴다 — `UPDATE … RETURNING`(PG).** 무엇이 바뀌었는지 보면서 트랜잭션 안에서 돌릴 때([54번](../54-returning-and-data-modifying-cte/)).
- **안 쓴다 — `WHERE` 없는 `UPDATE` 를 손으로.** 먼저 `SELECT count(*)` 로 센다.
- **안 쓴다 — 조건 없는 서브쿼리형.** `NULL` 덮어쓰기를 부른다(3번).
- **안 쓴다 — `SET a = b, b = a` 관용구.** 방언에 따라 답이 다르다(6번).
- **안 쓴다 — `UPDATE IGNORE` 를 재시도 회피용으로.** 반만 반영된 상태가 남는다.
- **조심한다 — 대량 갱신.** 잠금과 되돌릴 양이 행 수에 비례한다 — [51 번](../51-delete-and-truncate/)이 그 수치를 잰다.
- **조심한다 — 갱신을 「있으면 고치고 없으면 넣기」로 확장할 때.** 그것은 [52 UPSERT](../52-upsert/)·[53 MERGE](../53-merge/)다.

## 핵심 문장

- ★ **조인형은 짝 없는 행을 안 건드리고, 상관 서브쿼리형은 `NULL` 로 덮어쓴다** — 에러 없이 갈린다.
- **그 차이의 뿌리는 [11 번](../11-subquery-scalar-correlated-any-all/)이다** — 0행 스칼라 서브쿼리는 에러가 아니라 `NULL` 이다.
- **처방은 `WHERE EXISTS`** — 같은 조건을 `SET` 과 `WHERE` 에 두 번 적는다.
- **`UPDATE … FROM`(PG) 과 `UPDATE a JOIN b SET`(MySQL) 은 서로를 구문 오류로 거부한다.**
- **짝이 둘이면 조인형은 조용히 하나를 고르고, 서브쿼리형은 에러다** — 위험의 방향이 반대다.
- ★ **`SET a = b, b = a` 는 PG 에서 교환이고 MySQL 에서는 아니다** — MySQL 은 왼쪽부터 순차다.
- **`sql_safe_updates` 는 행 수가 아니라 「키를 썼나·`LIMIT` 이 있나」만 본다.** 기본값은 꺼짐이다.
- **영향 행 수는 PG 가 대상 행 수, MySQL 이 실제 변경 행 수다.**

## 관련 자료

- [PostgreSQL 18 · UPDATE](https://www.postgresql.org/docs/18/sql-update.html) — `FROM` 절의 경고, 다중 열 대입, `RETURNING`.
- [MySQL 8.4 · UPDATE Statement](https://dev.mysql.com/doc/refman/8.4/en/update.html) — 다중 표 문법, `SET` 평가 순서, `ORDER BY`/`LIMIT` 제약.
- [MySQL 8.4 · mysql Client Options](https://dev.mysql.com/doc/refman/8.4/en/mysql-command-options.html) — `--safe-updates` 의 규칙.
- [11 서브쿼리 — 스칼라·상관·ANY/ALL](../11-subquery-scalar-correlated-any-all/) — **그쪽은 「스칼라 서브쿼리가 0행·2행이면 무엇이 되나」까지, 여기는 「그 값이 `UPDATE` 의 `SET` 에 들어가면 표가 어떻게 되나」부터.** 0행 = `NULL` 규칙을 여기서 다시 증명하지 않는다.
- [49 INSERT](../49-insert-multi-row-and-insert-select/) — 문 원자성의 정본. 7번은 그것이 `UPDATE` 에서도 같은지만 확인한다.
- [19 SEMI·ANTI 조인](../19-semi-anti-join/) — 3번 처방의 `EXISTS` 가 거기다.
- [13 INNER JOIN](../13-inner-join/) — 2번의 「짝 없는 행이 대상에서 빠진다」가 같은 규칙이다.
- [51 DELETE 와 TRUNCATE](../51-delete-and-truncate/) — **`WHERE` 를 빠뜨린 문의 위험을 삭제 쪽에서.** `sql_safe_updates` 가 `TRUNCATE` 를 못 막는 것도 거기.
- [52 UPSERT](../52-upsert/) · [53 MERGE](../53-merge/) — 갱신과 삽입을 한 문으로 합칠 때.
- [54 RETURNING 과 변경문을 품은 CTE](../54-returning-and-data-modifying-cte/) — 바뀐 행을 그 자리에서 확인하는 법.
- [SQL 주제 목록](../README.md) — 55(트랜잭션 경계)·57(잠금)이 이웃이다.

## 용어 풀이

- **다중 표 `UPDATE`(multi-table UPDATE)** — 갱신 대상 외의 표를 같이 읽어 값을 가져오는 갱신문.\
  예: 사원 표의 부서명 칸을 부서 표에서 가져와 채우는 것.
- **상관 서브쿼리(correlated subquery)** — 바깥 행의 값을 참조해 행마다 다시 도는 서브쿼리([11번](../11-subquery-scalar-correlated-any-all/)).\
  예: `(SELECT d.name FROM t50_dept d WHERE d.id = e.dept_id)` 의 `e.dept_id`.
- **스칼라 서브쿼리(scalar subquery)** — 1행 1열을 돌려주기로 계약된 서브쿼리.\
  예: 0행이면 에러가 아니라 `NULL` 이고, 2행이면 에러다.
- **짝 없는 행** — 조인 조건을 만족하는 상대 행이 없는 행.\
  예: `t50_emp` 의 `dan` — `dept_id` 가 `NULL` 이라 어떤 부서와도 안 붙는다.
- **영향 행 수(affected rows)** — 문이 바꿨다고 보고하는 행 수.\
  예: 같은 문에서 PG 는 4, MySQL 은 3 을 돌려줬다 — 세는 기준이 다르다.
- **`sql_safe_updates`** — MySQL 세션 변수. 키나 `LIMIT` 없는 `UPDATE`/`DELETE` 를 에러로 만든다.\
  예: 기본값은 `0`(꺼짐)이고, 켜도 `TRUNCATE` 는 못 막는다([51번](../51-delete-and-truncate/)).
- **`ERROR 1175`** — MySQL 이 안전 갱신 모드에서 문을 거절하는 코드.\
  예: `WHERE name='ann'`(인덱스 없는 열)도 이 에러가 난다.
- **`UPDATE IGNORE`** — MySQL 에서 갱신 중의 에러를 경고로 낮추는 수식어.\
  예: 두 행 중 하나만 갱신되고 나머지는 경고 1062 로 남는다.
- **다중 열 대입** — `SET (a, b) = (식1, 식2)` 형태. PG 에만 있다.\
  예: `SET (dept_id, salary) = (salary, dept_id)` 는 의도가 문장에 드러난다.
- **문 원자성(statement atomicity)** — 한 문이 실패하면 그 문의 변경이 전부 취소되는 성질.\
  예: 두 행 중 둘째가 기본키를 어기면 첫째도 안 바뀐다.

## 더 들어가면

- **PG 의 `UPDATE … FROM` 은 사실상 조인이다.** `EXPLAIN` 을 찍으면 조인 노드가 뜨고,\
  [59 번의 연산자](../59-scan-join-sort-operators/)가 그대로 나온다. 다만 **이 편에서는 계획을 싣지 않았다** —\
  계획은 통계에 흔들리고([작성법 §2-1](../../../../../../reference/study-note-guide.md)), 이 주제의 결론은 계획과 무관하다.
- **MySQL 의 다중 표 `UPDATE` 는 대상 표를 여럿 쓸 수 있다** — `SET a.x = …, b.y = …` 형태로 두 표를 한 문에서 고친다.\
  PG 의 `UPDATE … FROM` 은 **대상이 언제나 하나**다. **이 차이는 던져 보지 않았다.**
- **`UPDATE` 가 기본키를 바꾸면** 참조하는 자식 행이 어떻게 되는지는 `ON UPDATE` 동작이 정한다 —\
  [44 번](../44-foreign-key-referential-actions/)이 정본이다.
- **경쟁 상태에서 같은 행을 두 세션이 갱신하면** 나중 쪽이 대기하거나 교착이 난다.\
  **이 편에서는 동시 세션 실험을 하지 않았다** — [56 격리 수준](../56-isolation-levels-read-phenomena-mvcc/)·[57 명시적 잠금과 교착](../57-explicit-locking-and-deadlock/) 주제다.
