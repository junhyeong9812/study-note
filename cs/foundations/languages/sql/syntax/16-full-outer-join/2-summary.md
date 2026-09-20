# sql/16-FULL OUTER JOIN — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-C](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · Table Expressions (Joined Tables)](https://www.postgresql.org/docs/18/queries-table-expressions.html) · [MySQL 8.4 · JOIN Clause](https://dev.mysql.com/doc/refman/8.4/en/join.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력은 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 에러 메시지도 실제로 받은 것이다.\
> **버전** — PG 는 오래전부터 지원한다. **MySQL 8.4.10 에는 `FULL OUTER JOIN` 이 없다** — 문법 오류가 난다(아래에 출력을 싣는다).\
> **선행** — [01 논리적 질의 처리 순서](../01-logical-query-processing-order/)(`FROM` 이 첫 칸이라는 것) · [04 NULL 의 3값 논리](../04-null-three-valued-logic/)(조인이 만들어 내는 `NULL`).

## 한눈에 — 쉽게 말하면

**`FULL OUTER JOIN` = 두 명단을 맞춰 보되, 어느 쪽에서도 짝 못 찾은 사람을 버리지 않는 것.**

- 동창회 명단과 회비 납부 명단이 있다.
- **`INNER`** — 양쪽에 다 있는 사람만. 「왔고 냈다」
- **`LEFT`** — 온 사람 전부. 안 낸 사람은 납부란이 빈칸.
- **`RIGHT`** — 낸 사람 전부. 안 온 사람은 참석란이 빈칸.
- **`FULL OUTER`** — **온 사람 + 낸 사람 전부.** 빈칸이 양쪽에 생긴다.

```text
     emp (사원)                dept (부서)
   +-----------+             +-----------+
   |  ann bob  |             |   sales   |
   |    cho    |             |    dev    |
   |           |             |           |
   |    dan    | <- 소속 없음 |    hr     | <- 사원 없음
   +-----------+             +-----------+
         \                       /
          \                     /
    INNER  :  ann bob cho 만
    LEFT   :  ann bob cho + dan
    RIGHT  :  ann bob cho + hr
    FULL   :  ann bob cho + dan + hr      <- 양쪽 다 살린다
```

이 명단 맞춤이 **똑같은 구조로** 조인이다.\
실무에서 `FULL OUTER JOIN` 이 필요한 자리는 대개 **대사(對査)** 다 — 두 시스템의 데이터를 맞춰 보고 「어느 쪽에만 있는 것」을 찾아내는 일.

> **외부 조인(outer join)** — 짝을 못 찾은 행을 버리지 않고 **반대쪽 열을 `NULL` 로 채워** 남기는 조인.\
> 예: `dan` 은 부서가 없지만 `LEFT JOIN` 결과에 남고 `dept` 쪽 열이 전부 `NULL` 이 된다.

## 예시 테이블 — SQL 네 주제가 같이 쓰는 데이터

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
        +-- dan 은 소속이 없다 (dept_id NULL)
```

**이 두 표가 `FULL OUTER JOIN` 을 설명하기에 딱 맞다** — 왼쪽에만 있는 행(`dan`)과 오른쪽에만 있는 행(`hr`)이 하나씩 있다.

## 동작 방식

### 1. 네 형태를 같은 데이터로 나란히 본다

**언제 쓰나** — 어느 형태를 쓸지 고를 때. 형태마다 다른 것은 **짝 못 찾은 행의 처분** 하나뿐이다.

조인 조건은 넷 다 같다: `ON e.dept_id = d.id`

```text
(전) FROM 이 만든 모든 짝 — 4 x 3 = 12행 중 ON 을 통과하는 것은 3행

 emp.dept_id | dept.id | 통과?
-------------+---------+-------
     10 (ann)|      10 | O
     10 (bob)|      10 | O
     20 (cho)|      20 | O
   NULL (dan)|   10/20/30 | X  (NULL = 10 은 UNKNOWN)
     -       |      30 | 짝지을 emp 가 없다
```

```text
   ↓ INNER JOIN           ↓ LEFT JOIN            ↓ RIGHT JOIN          ↓ FULL OUTER
+-----+-------+        +-----+-------+        +------+-------+      +------+-------+
| ann | sales |        | ann | sales |        | ann  | sales |      | ann  | sales |
| bob | sales |        | bob | sales |        | bob  | sales |      | bob  | sales |
| cho | dev   |        | cho | dev   |        | cho  | dev   |      | cho  | dev   |
+-----+-------+        | dan | NULL  |        | NULL | hr    |      | NULL | hr    |
   3행                 +-----+-------+        +------+-------+      | dan  | NULL  |
                          4행                     4행               +------+-------+
                     왼쪽만 있는 dan 을 살림   오른쪽만 있는 hr 을 살림     5행
```

**PG 18.6 에서 네 형태를 전부 돌린 실제 출력이다.**

```text
### INNER
 emp | dept          ### LEFT              ### RIGHT             ### FULL OUTER
-----+-------         emp | dept            emp  | dept           emp  | dept
 ann | sales         -----+-------         ------+-------        ------+-------
 bob | sales          ann | sales           ann  | sales          ann  | sales
 cho | dev            bob | sales           bob  | sales          bob  | sales
(3 rows)              cho | dev             cho  | dev            cho  | dev
                      dan | NULL            NULL | hr             NULL | hr
                     (4 rows)              (4 rows)               dan  | NULL
                                                                 (5 rows)
```

그림 해설 — **`FULL OUTER` 의 행 수(5) = `LEFT`(4) + `RIGHT`(4) − `INNER`(3)** 다. 가운데 3행을 두 번 세지 않는다.\
대가 — 짝 없는 행을 살린 대가로 **결과에 `NULL` 이 들어온다.** 그 `NULL` 은 원본 데이터의 `NULL` 과 **구분되지 않는다**(아래 3번).

`INNER`·`LEFT` 는 양쪽 엔진이 같다.

```text
### SQL: SELECT e.name AS emp, d.name AS dept
         FROM emp e LEFT JOIN dept d ON e.dept_id = d.id ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | dept                      +-----+-------+
-----+-------                    | emp | dept  |
 ann | sales                     +-----+-------+
 bob | sales                     | ann | sales |
 cho | dev                       | bob | sales |
 dan | NULL                      | cho | dev   |
(4 rows)                         | dan | NULL  |
                                 +-----+-------+
```

### 2. `FULL OUTER JOIN` — MySQL 에는 없다

**언제 쓰나** — 방언을 확인해야 할 때. 이 주제에서 가장 실용적인 사실이다.

**같은 문 하나를 두 엔진에 던진 실제 출력이다.**

```text
### SQL: SELECT e.name AS emp, d.name AS dept
         FROM emp e FULL OUTER JOIN dept d ON e.dept_id = d.id ORDER BY d.id, e.id;
--- PG 18.6 ---
 emp  | dept
------+-------
 ann  | sales
 bob  | sales
 cho  | dev
 NULL | hr
 dan  | NULL
(5 rows)
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that
  corresponds to your MySQL server version for the right syntax to use near
  'FULL OUTER JOIN dept d ON e.dept_id = d.id ORDER BY d.id, e.id' at line 1
```

`OUTER` 키워드를 빼도 마찬가지다.

```text
### SQL: ... FROM emp e FULL JOIN dept d ON e.dept_id = d.id;
--- PG 18.6 ---  -> 위와 같은 5행
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: ... right syntax to use near 'FULL JOIN dept d ON e.dept_id = d.id'
```

그림 해설 — **에러 번호가 1064(문법 오류)라는 점이 중요하다.** 「지원하지 않는 기능」이 아니라 **파서가 `FULL` 이라는 단어 자체를 모른다.**\
[MySQL 8.4 JOIN 페이지](https://dev.mysql.com/doc/refman/8.4/en/join.html)의 `joined_table` 문법에도 외부 조인은 `{LEFT|RIGHT} [OUTER] JOIN` 두 가지뿐이다.

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| `FULL OUTER JOIN` | ✓ | **✗ `ERROR 1064` 문법 오류** |
| `FULL JOIN` | ✓ | **✗ `ERROR 1064` 문법 오류** |
| `LEFT`/`RIGHT [OUTER] JOIN` | ✓ | ✓ |

대가 — MySQL 을 쓴다면 이 형태는 **우회로 만들어야** 하고, 우회에는 함정이 하나 있다(4번).

### 3. 결과의 `NULL` 은 어느 쪽에서 왔는가

**언제 쓰나** — `FULL OUTER` 결과를 읽을 때마다. 이 주제가 [04번](../04-null-three-valued-logic/)에 걸리는 자리다.

```text
FULL OUTER 결과 5행을 열 두 개만 남겨 보면

 e_dept | d_id     의미
--------+------    ----------------------------------------
     10 |   10     ann — 짝을 찾았다
     10 |   10     bob — 짝을 찾았다
     20 |   20     cho — 짝을 찾았다
   NULL |   30     hr  — 오른쪽만 있다. 왼쪽 열이 조인 때문에 NULL 이 됐다
   NULL | NULL     dan — 왼쪽만 있다. 오른쪽 열이 NULL 이고,
                         왼쪽 dept_id 는 원래부터 NULL 이었다
```

```text
### SQL: SELECT e.dept_id AS e_dept, d.id AS d_id
         FROM emp e FULL OUTER JOIN dept d ON e.dept_id = d.id ORDER BY d_id, e_dept;
--- PG 18.6 ---
 e_dept | d_id
--------+------
     10 |   10
     10 |   10
     20 |   20
   NULL |   30
   NULL | NULL
(5 rows)
--- MySQL 8.4.10 ---
ERROR 1064 (42000) ... near 'FULL OUTER JOIN dept d ON e.dept_id = d.id ORDER BY d_id, e_dept'
```

그림 해설 — 4번째 줄의 `NULL`(조인이 만든 것)과 5번째 줄 왼쪽의 `NULL`(원래 데이터)은 **결과만 봐서는 똑같다.**\
대가 — 그래서 「어느 쪽에만 있는 행인가」를 판정할 때는 **`NULL` 일 수 없는 열**을 봐야 한다. 기본키가 그 자리다.

```text
### SQL: SELECT e.name AS emp, d.name AS dept
         FROM emp e FULL OUTER JOIN dept d ON e.dept_id = d.id
         WHERE e.id IS NULL OR d.id IS NULL;
--- PG 18.6 ---
 emp  | dept
------+------
 dan  | NULL
 NULL | hr
(2 rows)
--- MySQL 8.4.10 ---
ERROR 1064 (42000) ...
```

`e.id`·`d.id` 는 둘 다 기본키라 원본에는 절대 `NULL` 이 없다.\
그러므로 **여기가 `NULL` 이면 그건 조인이 만든 것** — 즉 짝을 못 찾은 행이다. 이것이 대사 질의의 표준 형태다.

키를 하나로 합쳐 보고 싶으면 `COALESCE` 를 쓴다.

```text
### SQL: SELECT COALESCE(d.id, e.dept_id) AS dept_id, e.name AS emp, d.name AS dept
         FROM emp e FULL OUTER JOIN dept d ON e.dept_id = d.id ORDER BY dept_id;
--- PG 18.6 ---   (MySQL 8.4.10 은 FULL OUTER 자체가 없어 ERROR 1064 다)
 dept_id | emp  | dept
---------+------+-------
      10 | ann  | sales
      10 | bob  | sales
      20 | cho  | dev
      30 | NULL | hr
    NULL | dan  | NULL
(5 rows)
```

### 4. MySQL 우회 — `UNION` 인가 `UNION ALL` 인가

**언제 쓰나** — MySQL 에서 `FULL OUTER JOIN` 이 필요할 때. **여기가 이 주제의 가장 조용한 함정이다.**

흔히 보이는 우회는 「`LEFT` 와 `RIGHT` 를 `UNION`」이다. 이름 열로는 잘 돈다.

```text
### SQL: SELECT e.name AS emp, d.name AS dept FROM emp e LEFT JOIN dept d ON e.dept_id = d.id
         UNION
         SELECT e.name, d.name FROM emp e RIGHT JOIN dept d ON e.dept_id = d.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp  | dept                     +------+-------+
------+-------                   | emp  | dept  |
 dan  | NULL                     +------+-------+
 NULL | hr                       | ann  | sales |
 cho  | dev                      | bob  | sales |
 ann  | sales                    | cho  | dev   |
 bob  | sales                    | dan  | NULL  |
(5 rows)                         | NULL | hr    |
                                 +------+-------+
```

5행이다. 맞는 것처럼 보인다. **그런데 열을 바꿔 보면 무너진다.**

```text
(A) 잘못된 우회 — UNION                   (B) 정답 — PG 의 FULL OUTER JOIN
SELECT e.dept_id AS e_dept, d.id AS d_id   SELECT e.dept_id AS e_dept, d.id AS d_id
FROM emp e LEFT JOIN dept d                FROM emp e FULL OUTER JOIN dept d
  ON e.dept_id = d.id                        ON e.dept_id = d.id
UNION                                      ORDER BY d_id, e_dept;
SELECT e.dept_id, d.id
FROM emp e RIGHT JOIN dept d
  ON e.dept_id = d.id;
--- PG 18.6 ---                            --- PG 18.6 ---
 e_dept | d_id                              e_dept | d_id
--------+------                            --------+------
   NULL | NULL                                  10 |   10
   NULL |   30                                  10 |   10   <- 두 행이 살아 있다
     20 |   20                                  20 |   20
     10 |   10   <- 한 행으로 접혔다          NULL |   30
(4 rows)                                      NULL | NULL
                                           (5 rows)
--- MySQL 8.4.10 ---                       --- MySQL 8.4.10 ---
+--------+------+                          ERROR 1064 (42000) ...
| e_dept | d_id |                            near 'FULL OUTER JOIN dept d
+--------+------+                            ON e.dept_id = d.id ...'
|     10 |   10 |
|     20 |   20 |
|   NULL | NULL |
|   NULL |   30 |
+--------+------+
  4행 — PG 와 같다
```

두 그림의 결론 — **`UNION` 은 중복을 지운다.** `ann` 과 `bob` 이 `(10, 10)` 으로 같은 값이 되자 **두 행이 한 행으로 접혔다.**\
이름 열을 뽑을 때는 `ann` ≠ `bob` 이라 안 접혔을 뿐이다. **행 수가 데이터에 따라 달라지는 우회**다.

**올바른 우회는 `UNION ALL` + 반조인이다.**

```text
### SQL: SELECT e.dept_id AS e_dept, d.id AS d_id FROM emp e LEFT JOIN dept d ON e.dept_id = d.id
         UNION ALL
         SELECT e.dept_id, d.id FROM emp e RIGHT JOIN dept d ON e.dept_id = d.id
         WHERE e.id IS NULL;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 e_dept | d_id                   +--------+------+
--------+------                  | e_dept | d_id |
     10 |   10                   +--------+------+
     10 |   10                   |     10 |   10 |
     20 |   20                   |     10 |   10 |
   NULL | NULL                   |     20 |   20 |
   NULL |   30                   |   NULL | NULL |
(5 rows)                         |   NULL |   30 |
                                 +--------+------+
```

5행이다. **PG 의 `FULL OUTER JOIN` 결과와 정확히 같다.**

```text
설계                                      왜 맞나
LEFT JOIN 전체                            왼쪽 전부 + 짝 있는 것
    +
RIGHT JOIN 중 e.id IS NULL 인 것만         오른쪽 중 짝 없는 것만 (중복 없음)
    = UNION ALL (중복 제거를 안 한다)
```

대가 — `UNION ALL` 은 중복 제거를 안 하므로 **겹치는 부분을 직접 잘라내야** 한다. 그 자름이 `WHERE e.id IS NULL` 이다.\
`e.id` 는 기본키라 `NULL` 일 수 없고, 여기가 `NULL` 이면 **조인이 만든 `NULL`** — 즉 짝 없는 오른쪽 행이다.

### 5. `ON` 에 둘 조건과 `WHERE` 에 둘 조건

**언제 쓰나** — 외부 조인에 조건을 더 걸 때. 조건 위치 하나로 외부 조인이 **내부 조인으로 무너진다.**

```text
ON 은 "짝짓기 규칙"                 WHERE 는 "만들어진 행의 필터"
     ↓                                   ↓
짝을 못 찾아도 행은 남는다           NULL 로 채워진 행이 조건에 걸려 버려진다
```

```text
### SQL: SELECT e.name AS emp, d.name AS dept
         FROM emp e FULL OUTER JOIN dept d ON e.dept_id = d.id
         WHERE d.name = 'sales';
--- PG 18.6 ---
 emp | dept
-----+-------
 ann | sales
 bob | sales
(2 rows)
--- MySQL 8.4.10 ---
ERROR 1064 (42000) ...
```

그림 해설 — **`FULL OUTER` 라고 적었는데 결과는 `INNER JOIN` 과 똑같은 모양이다.**\
`dan` 의 `d.name` 은 `NULL`, `hr` 행의 `d.name` 은 `'sales'` 가 아니니 둘 다 `WHERE` 에서 잘렸다.\
대가 — 외부 조인에 `WHERE` 를 붙일 때는 **그 조건이 `NULL` 로 채워진 행도 통과시킬 수 있는지** 매번 확인해야 한다.

조건 위치의 규칙은 이 주제 밖이다 — 목록의 15번이 정본이다.

### 6. PG 의 제약 — `FULL JOIN` 은 등호 조인만

**언제 쓰나** — `FULL OUTER JOIN` 의 `ON` 에 부등호를 쓰려 할 때.

```text
### SQL: SELECT e.name AS emp, d.name AS dept
         FROM emp e FULL OUTER JOIN dept d ON e.dept_id > d.id;
--- PG 18.6 ---
ERROR:  FULL JOIN is only supported with merge-joinable or hash-joinable join conditions
--- MySQL 8.4.10 ---
ERROR 1064 (42000) ... near 'FULL OUTER JOIN dept d ON e.dept_id > d.id'
```

그림 해설 — PG 의 에러는 **문법 오류가 아니라 실행 가능성 오류**다. `FULL` 을 구현하려면 양쪽을 모두 훑어야 하고, PG 는 머지/해시 조인으로만 그걸 한다. 부등호는 그 두 알고리즘에 안 맞는다.\
대가 — 부등호 `FULL` 이 필요하면 `LEFT` 와 `RIGHT` 를 `UNION ALL` 로 직접 합쳐야 한다(4번의 형태).

두 에러가 **같은 「안 된다」가 아니라는 점**이 중요하다 — PG 는 *이 조건으로는* 안 되고, MySQL 은 *이 문법 자체가* 없다.

## 문법 — 형태와 규칙

```sql
-- PostgreSQL (MySQL 에는 없다)
FROM 왼쪽표 FULL [OUTER] JOIN 오른쪽표 ON <조건>
FROM 왼쪽표 FULL [OUTER] JOIN 오른쪽표 USING (공통열)

-- 두 엔진 공통
FROM 왼쪽표 [INNER] JOIN        오른쪽표 ON <조건>
FROM 왼쪽표 LEFT  [OUTER] JOIN  오른쪽표 ON <조건>
FROM 왼쪽표 RIGHT [OUTER] JOIN  오른쪽표 ON <조건>
```

규칙 다섯.

1. **`OUTER` 는 생략 가능하다.** `FULL JOIN` = `FULL OUTER JOIN`. (다만 MySQL 은 둘 다 없다.)
2. **`FULL` 의 행 수 = `LEFT` + `RIGHT` − `INNER`.** 위 예시에서 4 + 4 − 3 = 5.
3. **짝 없는 행의 반대쪽 열은 전부 `NULL` 로 채워진다.** 일부만 채워지는 일은 없다.
4. **짝 여부 판정은 `NULL` 일 수 없는 열로 한다** — 보통 기본키. 다른 열을 보면 원본 `NULL` 과 구분이 안 된다.
5. **`WHERE` 에 오른쪽/왼쪽 열 조건을 걸면 외부 조인이 무너진다.** 조건은 `ON` 으로 옮기거나 `IS NULL` 을 같이 허용한다.

`FULL OUTER JOIN` 을 쓰는 실전 형태는 사실상 **둘**이다.

```sql
-- (1) 대사 — 어느 쪽에만 있는 것 찾기
SELECT e.name AS emp, d.name AS dept
FROM emp e FULL OUTER JOIN dept d ON e.dept_id = d.id
WHERE e.id IS NULL OR d.id IS NULL;

-- (2) 합치기 — 양쪽을 다 보이는 한 장의 표
SELECT COALESCE(d.id, e.dept_id) AS dept_id, e.name AS emp, d.name AS dept
FROM emp e FULL OUTER JOIN dept d ON e.dept_id = d.id;
```

## 어디서 틀리나

- **MySQL 에서 `FULL OUTER JOIN` 을 쓴다.**\
  `ERROR 1064` 문법 오류다. 다행히 **바로 터진다** — 이 주제에서 유일하게 시끄러운 실패다.
- **MySQL 우회를 `UNION` 으로 만든다.**\
  중복 행이 조용히 접힌다. 위에서 5행이 4행이 됐다. **`UNION ALL` + `WHERE 키 IS NULL`** 이 맞다.
- **짝 여부를 `NULL` 가능한 열로 판정한다.**\
  `WHERE d.name IS NULL` 은 「짝이 없다」와 「부서명이 원래 `NULL` 이다」를 구분하지 못한다. 기본키를 본다.
- **외부 조인 결과에 `WHERE` 를 붙여 무너뜨린다.**\
  `FULL OUTER` 라고 써 놓고 `INNER` 결과를 받는다. 위에서 5행이 2행이 됐다.
- **`FULL` 의 `ON` 에 부등호를 쓴다(PG).**\
  `FULL JOIN is only supported with merge-joinable or hash-joinable join conditions` 로 거부된다.
- **`FULL OUTER` 결과에 집계를 씌우고 행 수를 잊는다.**\
  짝 없는 행이 `NULL` 로 들어오므로 `COUNT(열)` 과 `COUNT(*)` 이 어긋난다([04번](../04-null-three-valued-logic/)).
- **`FULL OUTER` 를 「그냥 둘 다 보고 싶을 때」 남발한다.**\
  대부분의 화면은 한쪽 기준이다. 기준이 있으면 `LEFT` 가 읽기도 쉽고 계획도 낫다.

## 언제 쓰고 언제 안 쓰나

- **쓴다 — 대사(reconciliation).** 두 소스를 맞춰 보고 「어느 쪽에만 있는 것」을 전부 뽑아야 할 때.\
  주문 테이블과 결제 테이블, 재고 장부와 실사 결과처럼 **양쪽 다 빠짐이 있을 수 있는** 짝.
- **쓴다 — 시계열 맞춤.** 두 기간별 집계를 나란히 놓을 때. 한쪽에만 있는 날짜를 잃지 않는다.
- **안 쓴다 — 기준 표가 분명할 때.** 「사원 목록에 부서명을 붙인다」는 `LEFT JOIN` 이다. `FULL` 을 쓰면 사원 없는 부서가 끼어들어 화면이 이상해진다.
- **안 쓴다 — MySQL 에서.** 문법이 없다. 우회는 되지만 읽기 어렵고 실수하기 쉽다. 설계 단계에서 피할 수 있으면 피한다.
- **대안을 먼저 본다.** 「어느 쪽에만 있는 것」만 필요하면 `NOT EXISTS` 두 번이 더 명확할 때가 많다.

## 핵심 문장

- `FULL OUTER JOIN` 은 **양쪽의 짝 없는 행을 모두 살린다.** 행 수는 `LEFT` + `RIGHT` − `INNER`.
- **MySQL 8.4.10 에는 없다** — `ERROR 1064` 문법 오류다. `FULL JOIN` 도 마찬가지다.
- MySQL 우회는 **`UNION` 이 아니라 `UNION ALL` + 반조인**이다. `UNION` 은 중복 행을 조용히 접는다.
- 짝 없는 행은 **`NULL` 일 수 없는 열**(기본키)로 판정한다. 다른 열은 원본 `NULL` 과 구분이 안 된다.
- 외부 조인에 `WHERE` 를 잘못 붙이면 **내부 조인으로 무너진다.**
- PG 도 **등호(머지/해시 가능) 조건에서만** `FULL` 을 지원한다.

## 관련 자료

- [PostgreSQL 18 · Table Expressions](https://www.postgresql.org/docs/18/queries-table-expressions.html) — 조인 형태별 정의.
- [MySQL 8.4 · JOIN Clause](https://dev.mysql.com/doc/refman/8.4/en/join.html) — `joined_table` 문법에 외부 조인은 `{LEFT|RIGHT} [OUTER] JOIN` 뿐이다.
- [01 논리적 질의 처리 순서](../01-logical-query-processing-order/) — 조인은 `FROM`(1번 칸)에서 일어난다.
- [04 NULL 의 3값 논리](../04-null-three-valued-logic/) — 조인이 만든 `NULL` 도 3값 논리를 따른다.
- [SQL 주제 목록](../README.md) — 12~15(조인 형태) · 19(반조인) · 34(집합 연산) · 25(조인 팬아웃) 이 이웃이다.

## 용어 풀이

- **외부 조인(outer join)** — 짝 못 찾은 행을 버리지 않고 반대쪽 열을 `NULL` 로 채워 남기는 조인.\
  예: `dan` 은 부서가 없어도 `LEFT JOIN` 결과에 남는다.
- **`FULL OUTER JOIN`** — 왼쪽·오른쪽 **양쪽**의 짝 없는 행을 모두 남기는 외부 조인.\
  예: `dan`(왼쪽만)과 `hr`(오른쪽만)이 둘 다 결과에 있다.
- **`ON` 절** — 두 표의 행을 **짝짓는 규칙**. 여기서 탈락해도 외부 조인이면 행이 남는다.\
  예: `ON e.dept_id = d.id`.
- **반조인(anti join)** — 「저쪽에 짝이 없는 행」만 남기는 조인. `WHERE 키 IS NULL` 이나 `NOT EXISTS` 로 쓴다.\
  예: `RIGHT JOIN ... WHERE e.id IS NULL` 은 사원 없는 부서만 준다.
- **`UNION` 과 `UNION ALL`** — 앞은 **중복 행을 제거**하고 뒤는 그대로 둔다.\
  예: `(10,10)` 이 두 행일 때 `UNION` 은 하나로 접고 `UNION ALL` 은 둘 다 남긴다.
- **대사(reconciliation)** — 두 데이터 소스를 맞춰 보고 어긋난 부분을 찾아내는 일.\
  예: 주문은 있는데 결제가 없는 건, 결제는 있는데 주문이 없는 건을 한 번에 뽑기.
- **머지 조인 / 해시 조인** — 양쪽을 정렬해 훑거나 해시 표를 만들어 맞추는 조인 알고리즘.\
  예: PG 가 `FULL JOIN` 을 이 둘로만 구현하기 때문에 `ON` 에 부등호를 못 쓴다.
- **`COALESCE`** — 앞에서부터 `NULL` 이 아닌 첫 값을 돌려주는 함수.\
  예: `COALESCE(d.id, e.dept_id)` 로 양쪽 키를 한 열로 합친다.
- **`ERROR 1064`** — MySQL 의 문법 오류 코드. 파서가 그 단어를 모른다는 뜻이다.\
  예: `FULL OUTER JOIN` 을 던지면 이 번호가 온다.
