# sql/34-집합 연산 — `UNION`·`INTERSECT`·`EXCEPT` 와 `ALL` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력·에러·실행 계획은 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 지어낸 출력은 없다.\
> 표는 기존 `emp`·`dept` 만 썼다 — **새로 만든 표가 없다.**\
> 문서 근거는 [PG 18 Combining Queries](https://www.postgresql.org/docs/18/queries-union.html) · [MySQL 8.4 Set Operations](https://dev.mysql.com/doc/refman/8.4/en/set-operations.html) · [MySQL 8.0.31 릴리스 노트](https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-31.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. 셋의 행 수

**(A) 4행 `{10,20,30,NULL}` · (B) 2행 `{10,20}` · (C) 1행 `{NULL}` · (D) 1행 `{30}`.**

```text
### SQL: SELECT dept_id FROM emp UNION SELECT id FROM dept;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id                         +---------+
---------                        | dept_id |
                                 +---------+
      10                         |      10 |
      30                         |      20 |
      20                         |    NULL |
(4 rows)                         |      30 |
                                 +---------+

### SQL: SELECT dept_id FROM emp INTERSECT SELECT id FROM dept;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id                         +---------+
---------                        | dept_id |
      10                         +---------+
      20                         |      10 |
(2 rows)                         |      20 |
                                 +---------+

### SQL: SELECT dept_id FROM emp EXCEPT SELECT id FROM dept;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id                         +---------+
---------                        | dept_id |
                                 +---------+
(1 row)                          |    NULL |
                                 +---------+

### SQL: SELECT id FROM dept EXCEPT SELECT dept_id FROM emp;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id                              +------+
----                             | id   |
 30                              +------+
(1 row)                          |   30 |
                                 +------+
```

**왜 그런가** — 두 목록을 나란히 놓으면 전부 설명된다.

```text
 emp.dept_id = {10, 10, 20, NULL}      dept.id = {10, 20, 30}

  UNION      : 합치고 중복 제거 -> {10, 20, 30, NULL}            4행
  INTERSECT  : 양쪽에 다 있는 것 -> {10, 20}                      2행
  EXCEPT (emp-dept): 왼쪽에만    -> {NULL}                        1행
  EXCEPT (dept-emp): 왼쪽에만    -> {30}                          1행
```

★ **(C) 와 (D) 가 서로 다르다** — `EXCEPT` 는 **방향이 있다.** 교환법칙이 성립하지 않는다.\
PG 의 (C) 는 빈 칸으로 찍혔지만 `(1 row)` 이므로 **0행이 아니라 `NULL` 한 행**이다. MySQL 이 `NULL` 이라고 써 주니 대조하면 확실하다.

---

### 2. `ALL` 을 붙이면

**(A) 7행 · (B) 2행 · (C) 4행. `ALL` 이 붙으면 「있나 없나」가 아니라 「몇 개인가」를 다룬다.**

```text
### SQL: SELECT dept_id FROM emp UNION ALL SELECT id FROM dept;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id                         +---------+
---------                        | dept_id |
      10                         +---------+
      10                         |      10 |
      20                         |      10 |
                                 |      20 |
      10                         |    NULL |
      20                         |      20 |
      30                         |      30 |
(7 rows)                         |      10 |
                                 +---------+

### SQL: SELECT dept_id FROM emp EXCEPT ALL SELECT id FROM dept;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id                         +---------+
---------                        | dept_id |
                                 +---------+
      10                         |      10 |
(2 rows)                         |    NULL |
                                 +---------+

### SQL: SELECT dept_id FROM emp INTERSECT ALL SELECT dept_id FROM emp;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id                         +---------+
---------                        | dept_id |
                                 +---------+
      10                         |      10 |
      10                         |      10 |
      20                         |      20 |
(4 rows)                         |    NULL |
                                 +---------+
```

**왜 그런가** — `ALL` 은 연산의 무대를 **집합에서 다중집합(가방)으로** 옮긴다.

```text
 EXCEPT ALL 의 계산
 왼쪽  10 이 2개, 20 이 1개, NULL 이 1개
 오른쪽 10 이 1개, 20 이 1개, 30 이 1개
        ↓  개수를 뺀다 (음수면 0)
 10: 2-1 = 1   20: 1-1 = 0   NULL: 1-0 = 1   -> {10, NULL}  2행

 EXCEPT (ALL 없이) 의 계산
 10 은 오른쪽에 "있다" -> 버린다
 20 도 "있다"         -> 버린다
 NULL 은 "없다"       -> 남긴다                -> {NULL}      1행
```

`INTERSECT ALL` 이 4행인 것은 같은 목록끼리라 **모든 개수가 그대로 살아남았기** 때문이다.\
★ **`ALL` 이 빠진 쪽이 「더 짧다」가 아니라 「다른 연산」이다.**

---

### 3. `UNION` 이 접는 것

**(A) 1행 · (B) 4행. `UNION` 은 「가지 안의 중복」까지 지운다.**

```text
### SQL: SELECT dept_id FROM emp WHERE dept_id = 10 UNION SELECT dept_id FROM emp WHERE dept_id = 10;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id                         +---------+
---------                        | dept_id |
      10                         +---------+
(1 row)                          |      10 |
                                 +---------+

### SQL: SELECT dept_id FROM emp WHERE dept_id = 10 UNION ALL SELECT dept_id FROM emp WHERE dept_id = 10;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id                         +---------+
---------                        | dept_id |
      10                         +---------+
      10                         |      10 |
      10                         |      10 |
      10                         |      10 |
(4 rows)                         |      10 |
                                 +---------+
```

**왜 그런가** — `ann` 과 `bob` 이 둘 다 `dept_id = 10` 이라, **한 가지가 이미 2행**이다.

```text
 가지 A = {10, 10}   가지 B = {10, 10}

 UNION ALL:  10,10,10,10                      4행
 UNION    :  가지 사이의 중복을 지운다 -> ?    ← 여기까지만 생각하면 2행을 예상한다
             실제로는 가지 안의 중복도 지운다 -> 1행  ★
```

★ **`UNION` 은 "두 결과를 합친 뒤 `DISTINCT` 를 건" 것과 같다.** 가지 경계를 구분하지 않는다.\
그래서 **"가지 사이의 중복만 지울 것"이라는 기대가 틀린다** — 이것이 4번 문항의 사고로 이어진다.

---

### 4. 16번이 당한 함정

**4행이다. `name` 으로 뽑으면 5행이 된다 — 같은 질의인데 뽑는 열에 따라 행 수가 달라진다.**

```text
### SQL: SELECT e.dept_id AS e_dept, d.id AS d_id FROM emp e LEFT JOIN dept d ON e.dept_id = d.id
         UNION
         SELECT e.dept_id, d.id FROM emp e RIGHT JOIN dept d ON e.dept_id = d.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 e_dept | d_id                   +--------+------+
--------+------                  | e_dept | d_id |
        |                        +--------+------+
        |   30                   |     10 |   10 |
     20 |   20                   |     20 |   20 |
     10 |   10   <- 접혔다       |   NULL | NULL |
(4 rows)                         |   NULL |   30 |
                                 +--------+------+

### SQL: SELECT e.name AS emp, d.name AS dept FROM emp e LEFT JOIN dept d ON e.dept_id = d.id
         UNION
         SELECT e.name, d.name FROM emp e RIGHT JOIN dept d ON e.dept_id = d.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | dept                      +------+-------+
-----+-------                    | emp  | dept  |
 dan |                           +------+-------+
     | hr                        | ann  | sales |
 cho | dev                       | bob  | sales |
 ann | sales                     | cho  | dev   |
 bob | sales                     | dan  | NULL  |
(5 rows)                         | NULL | hr    |
                                 +------+-------+
```

**왜 그런가** — `ann` 과 `bob` 은 **부서 번호로 보면 똑같은 `(10, 10)`** 이고, **이름으로 보면 `('ann','sales')` 와 `('bob','sales')` 로 다르다.**

```text
 뽑는 열이 (e.dept_id, d.id) 일 때      뽑는 열이 (e.name, d.name) 일 때
 ann -> (10, 10)  ┐                     ann -> ('ann','sales')   다르다
 bob -> (10, 10)  ┘ 같다 -> 접힌다       bob -> ('bob','sales')   -> 안 접힌다
 = 4행                                   = 5행
```

★ **에러도 경고도 없다.** "사원 하나가 사라졌다"를 알아채려면 **행 수를 세어 봐야** 한다.\
[16번](../16-full-outer-join/)이 MySQL 의 `FULL OUTER JOIN` 우회를 만들다가 정확히 이것에 걸렸고, **올바른 우회는 `UNION ALL` + 반조인**이었다.

```text
### SQL: SELECT e.dept_id AS e_dept, d.id AS d_id FROM emp e LEFT JOIN dept d ON e.dept_id = d.id
         UNION ALL
         SELECT e.dept_id, d.id FROM emp e RIGHT JOIN dept d ON e.dept_id = d.id WHERE e.id IS NULL;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 e_dept | d_id                   +--------+------+
--------+------                  | e_dept | d_id |
     10 |   10                   +--------+------+
     10 |   10   <- 둘 다 살았다 |     10 |   10 |
     20 |   20                   |     10 |   10 |
        |                        |     20 |   20 |
        |   30                   |   NULL | NULL |
(5 rows)                         |   NULL |   30 |
                                 +--------+------+
```

**일반화하면 이렇다.**

> **행 수가 의미를 갖는 자리에 `UNION` 을 쓰지 마라.**\
> `UNION ALL` 로 합치고, 겹치는 부분은 **조건으로 직접 잘라내라**(여기서는 `WHERE e.id IS NULL`, [19번](../19-semi-anti-join/)의 반조인).

같은 함정이 **감사 로그 합치기·여러 소스 집계·목록 합치기**에서 그대로 재현된다 — **값이 같은 두 행이 실제로는 다른 사건일 때** 언제나.\
그리고 3번에서 봤듯 **한 가지 안의 중복도 지우므로**, "양쪽에 겹치는 게 없으니 괜찮다"는 판단도 안전하지 않다.

---

### 5. 열 개수가 다르면

**두 엔진 다 막는다.**

```text
### SQL: SELECT id, name FROM emp UNION SELECT id FROM dept;
--- PG 18.6 ---
ERROR:  each UNION query must have the same number of columns
LINE 1: SELECT id, name FROM emp UNION SELECT id FROM dept;
                                              ^
--- MySQL 8.4.10 ---
ERROR 1222 (21000) at line 1: The used SELECT statements have a different number of columns
```

**왜 그런가** — 열 개수는 **문장만 봐도 알 수 있다.** 데이터를 안 봐도 되니 파싱 단계에서 잡힌다.\
[11번](../11-subquery-scalar-correlated-any-all/)에서 "2열 이상은 파싱 때, 2행 이상은 돌릴 때 터진다"고 한 것과 같은 구분이다.

**이 에러는 친절한 편이다** — 다음 문항의 타입 쪽이 훨씬 위험하다.

---

### 6. 타입이 다르면

**PG 는 에러, MySQL 은 통과시키고 결과 열을 문자열로 만든다.**

```text
### SQL: SELECT id FROM emp UNION SELECT name FROM dept;
--- PG 18.6 ---
ERROR:  UNION types integer and text cannot be matched
LINE 1: SELECT id FROM emp UNION SELECT name FROM dept;
                                        ^
--- MySQL 8.4.10 ---
+-------+
| id    |
+-------+
| 1     |
| 2     |
| 3     |
| 4     |
| dev   |
| hr    |
| sales |
+-------+
```

**결과 열의 타입은 문자열이다.** 근거는 **정렬 순서**다 — `1,2,3,4,dev,hr,sales` 는 숫자 순이 아니라 **문자열 순**이다.\
(정수였다면 `dev` 가 들어갈 자리가 없고, 결과가 7행 다 나온 것 자체가 변환이 일어났다는 뜻이다.)

**숫자끼리는 양쪽 다 맞춰 준다.**

```text
### SQL: SELECT id FROM dept UNION SELECT '40';
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id                              +----+
----                             | id |
 10                              +----+
 30                              | 20 |
 40                              | 30 |
 20                              | 10 |
(4 rows)                         | 40 |
                                 +----+

### SQL: SELECT 1 AS v UNION ALL SELECT 1.5;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
  v                              +-----+
-----                            | v   |
   1                             +-----+
 1.5                             | 1.0 |
(2 rows)                         | 1.5 |
                                 +-----+
```

★ **[35번](../35-type-system-and-casting/)이 찾은 성격 차이가 여기서 다시 나온다** — **"PG 는 못 읽으면 문을 죽이고, MySQL 은 읽을 수 있는 데까지 읽고 경고만 남긴다."**\
여기서는 **경고조차 없었다.** `SHOW WARNINGS` 를 물어볼 것도 없이 그냥 통과다.

**그래서 MySQL 에서 `UNION` 을 쓸 때는 타입을 직접 맞춘다**(`CAST`). PG 에서 돌던 질의를 MySQL 로 옮길 때 **에러가 안 난다고 안심하면 안 된다** — 조용히 다른 답이 나온다.

---

### 7. 중복 제거의 값

**PG 는 `HashAggregate`, MySQL 은 `Union materialize with deduplication` 이 붙고 빠진다.**

```text
### SQL: EXPLAIN (COSTS OFF) SELECT dept_id FROM emp UNION SELECT id FROM dept;
--- PG 18.6 ---
          QUERY PLAN          
------------------------------
 HashAggregate                 <- 중복 제거
   Group Key: emp.dept_id
   ->  Append
         ->  Seq Scan on emp
         ->  Seq Scan on dept
(5 rows)
--- MySQL 8.4.10 ---
| -> Table scan on <union temporary>  (cost=2.27..4.49 rows=7)
    -> Union materialize with deduplication  (cost=1.9..1.9 rows=7)
        -> Table scan on emp  (cost=0.55 rows=3)
        -> Covering index scan on dept using name  (cost=0.65 rows=4)

### SQL: EXPLAIN (COSTS OFF) SELECT dept_id FROM emp UNION ALL SELECT id FROM dept;
--- PG 18.6 ---
       QUERY PLAN       
------------------------
 Append                        <- 그냥 이어 붙인다
   ->  Seq Scan on emp
   ->  Seq Scan on dept
(3 rows)
--- MySQL 8.4.10 ---
| -> Append  (cost=1.2 rows=7)
    -> Stream results  (cost=0.55 rows=3)
        -> Table scan on emp  (cost=0.55 rows=3)
    -> Stream results  (cost=0.65 rows=4)
        -> Covering index scan on dept using name  (cost=0.65 rows=4)
```

**왜 그런가** — 중복을 지우려면 **모든 행을 서로 비교**해야 한다. 해시 테이블을 만들거나 정렬해야 하고, 둘 다 **결과 전체를 붙들고 있어야** 한다.

```text
 UNION ALL                          UNION
 행이 나오는 대로 흘려보낸다         전부 모아 놓고 중복을 지운 뒤 내보낸다
 (MySQL: Stream results)            (MySQL: <union temporary> · materialize)
 -> 첫 행이 일찍 나온다              -> 첫 행이 마지막에 나온다
 -> 메모리가 안 든다                 -> 결과 크기만큼 든다
```

★ **MySQL 계획의 `Stream results` 라는 낱말이 그대로 그 차이다.**\
`Covering index scan on dept using name` 은 `dept.name` 에 `UNIQUE` 가 있어서 뜬 것이지 집합 연산의 성질이 아니다 — **데이터·스키마에 달린 선택**이다.

---

### 8. `ORDER BY` 의 자리

**(B) 만 통과한다.**

```text
### SQL: SELECT name FROM emp ORDER BY name UNION SELECT name FROM dept;      -- (A)
--- PG 18.6 ---
ERROR:  syntax error at or near "UNION"
LINE 1: SELECT name FROM emp ORDER BY name UNION SELECT name FROM de...
                                           ^
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near 'UNION SELECT name FROM dept' at line 1

### SQL: SELECT name FROM emp UNION SELECT name FROM dept ORDER BY name;      -- (B)
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name                            +-------+
-------                          | name  |
 ann                             +-------+
 bob                             | ann   |
 cho                             | bob   |
 dan                             | cho   |
 dev                             | dan   |
 hr                              | dev   |
 sales                           | hr    |
(7 rows)                         | sales |
                                 +-------+

### SQL: SELECT name AS a FROM emp UNION SELECT name AS b FROM dept ORDER BY b;   -- (C)
--- PG 18.6 ---
ERROR:  column "b" does not exist
LINE 1: ...e AS a FROM emp UNION SELECT name AS b FROM dept ORDER BY b;
                                                                     ^
DETAIL:  There is a column named "b" in table "*SELECT* 2", but it cannot be referenced from this part of the query.
--- MySQL 8.4.10 ---
ERROR 1054 (42S22) at line 1: Unknown column 'b' in 'order clause'
```

**왜 그런가**

```text
 (A) 가지 안의 ORDER BY
     "합치기 전에 정렬해 둔다"는 것은 의미가 없다 — 합치면 순서가 깨진다.
     그래서 문법이 아예 막는다. (괄호를 치면 LIMIT 과 함께 쓸 수 있다)

 (B) 맨 끝의 ORDER BY
     집합 연산이 다 끝난 결과에 한 번 건다. ★ 유일하게 맞는 자리다.

 (C) 둘째 가지의 별칭
     결과 열의 이름은 첫 가지가 정했다(9번). b 라는 이름은 결과에 없다.
     PG 의 DETAIL 이 그 사실을 말해 준다 — "*SELECT* 2 에는 b 가 있지만 여기서는 못 본다".
```

`LIMIT` 도 같다 — 가지마다 붙이려면 **괄호**가 필요하다.

```text
### SQL: SELECT name FROM emp LIMIT 1 UNION ALL SELECT name FROM dept LIMIT 1;
--- PG 18.6 ---
ERROR:  syntax error at or near "UNION"
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: ... near 'UNION ALL SELECT name FROM dept LIMIT 1' at line 1

### SQL: (SELECT name FROM emp ORDER BY id LIMIT 1) UNION ALL (SELECT name FROM dept ORDER BY id LIMIT 1);
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name                            +-------+
-------                          | name  |
 ann                             +-------+
 sales                           | ann   |
(2 rows)                         | sales |
                                 +-------+
```

**서수를 쓰면 이름 문제를 피한다** — `ORDER BY 2` 는 두 엔진 다 된다.

```text
### SQL: SELECT name, id FROM dept UNION ALL SELECT name, id FROM emp ORDER BY 2;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name  | id                      +-------+----+
-------+----                     | name  | id |
 ann   |  1                      +-------+----+
 bob   |  2                      | ann   |  1 |
 cho   |  3                      | bob   |  2 |
 dan   |  4                      | cho   |  3 |
 sales | 10                      | dan   |  4 |
 dev   | 20                      | sales | 10 |
 hr    | 30                      | dev   | 20 |
(7 rows)                         | hr    | 30 |
                                 +-------+----+
```

---

### 9. 결과 열의 이름

**`first_name` 이다 — 첫 가지가 정한다.**

```text
### SQL: SELECT id AS first_name FROM dept UNION ALL SELECT id AS second_name FROM emp;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 first_name                      +------------+
------------                     | first_name |
         10                      +------------+
         20                      |         20 |
         30                      |         30 |
          1                      |         10 |
          2                      |          1 |
          3                      |          2 |
          4                      |          3 |
(7 rows)                         |          4 |
                                 +------------+
```

**왜 그런가** — 집합 연산의 결과는 **하나의 결과 집합**이고, 열 이름은 하나여야 한다. 표준적으로 **첫 가지**가 그 이름을 준다.\
그래서 8번 (C) 가 실패한 것이다 — `b` 라는 이름은 결과 어디에도 없다.

★ **MySQL 쪽 순서를 보라 — `20, 30, 10, 1, 2, 3, 4` 다.**\
`dept` 의 기본키 순서(10, 20, 30)도 아니고 삽입 순서도 아니다. **`ORDER BY` 가 없으면 순서는 보장되지 않는다**([08번](../08-order-by-null-position-stability/)).\
"PG 에서 순서가 맞게 나왔다"를 근거로 쓰면 안 된다 — **같은 질의가 MySQL 에서 이미 다른 순서였다.**

---

### 10. `NULL` 은 합쳐지나

**1행이다. `NULL` 은 「하나의 값」으로 취급된다.**

```text
### SQL: SELECT NULL AS v INTERSECT SELECT NULL;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 v                               +------+
---                              | v    |
                                 +------+
(1 row)                          | NULL |
                                 +------+
```

**어떻게 어긋나는가**

```text
 WHERE 의 비교 규칙 (04번 · 05번)      집합 연산·DISTINCT 의 판정 (07번 · 여기)
 NULL = NULL   ->  UNKNOWN             NULL 과 NULL  ->  같은 값
   -> WHERE 가 그 행을 버린다             -> 한 행으로 접히고, 교집합에 남는다
```

**같은 `NULL` 인데 절이 다르면 반대로 취급된다.** 이 어긋남은 SQL 전체에 걸쳐 일관되게 나타난다.

- `WHERE`·`ON`·`HAVING` 의 **비교**: `NULL` 은 어떤 것과도 같지 않다.
- `DISTINCT`·`GROUP BY`·집합 연산의 **묶기**: `NULL` 끼리는 하나다.

1번 (C) 에서 `EXCEPT` 가 `NULL` 을 남긴 것도 같은 규칙이다 — `dept.id` 목록에 `NULL` 이 없으니 "빼이지 않고" 남았다.\
PG 의 `IS NOT DISTINCT FROM`([05번](../05-null-comparison-is-distinct-from/))이 **묶기 쪽 기준을 비교 연산자로 꺼내 쓴 것**이다.

---

### 11. 우선순위

**(A) 는 `{1, 2}` 2행, (B) 는 `{2}` 1행. `INTERSECT` 가 `UNION`·`EXCEPT` 보다 세게 붙는다.**

```text
### SQL: SELECT 1 AS v UNION SELECT 2 INTERSECT SELECT 2;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 v                               +---+
---                              | v |
 1                               +---+
 2                               | 1 |
(2 rows)                         | 2 |
                                 +---+

### SQL: (SELECT 1 AS v UNION SELECT 2) INTERSECT SELECT 2;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 v                               +---+
---                              | v |
 2                               +---+
(1 row)                          | 2 |
                                 +---+
```

**왜 그런가**

```text
 (A) 괄호 없이 = 1 UNION (2 INTERSECT 2) = 1 UNION {2} = {1, 2}
 (B) 괄호 주면 = (1 UNION 2) INTERSECT 2 = {1,2} INTERSECT {2} = {2}
```

MySQL 8.0.31 릴리스 노트도 같은 말을 적는다 — "`INTERSECT` groups before `EXCEPT` or `UNION` in terms of operator precedence".\
**두 엔진이 같은 우선순위를 쓴다.**

★ **그래도 괄호를 친다.** 우선순위를 외우는 것보다 싸고, 읽는 사람이 다시 확인하지 않아도 된다.\
곱셈이 덧셈보다 세다는 것을 알아도 `(a+b)*c` 를 괄호 없이 쓰지 않는 것과 같다.

---

### 12. 버전

**MySQL 8.0.31 부터다. 근거는 매뉴얼이 아니라 릴리스 노트다.**

> "In this release MySQL adds support for the SQL standard `INTERSECT` and `EXCEPT` table operators."\
> — [MySQL 8.0.31 릴리스 노트](https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-31.html)

**왜 릴리스 노트인가** — MySQL 매뉴얼 페이지에는 **기능 도입 버전이 거의 안 적혀 있다.**\
매뉴얼만 보면 "8.4 에 있다"까지만 알 수 있고 **"8.0.30 에도 있나"는 알 수 없다.** 그래서 릴리스 노트로 내려간다.

```text
 MySQL 8.0.30 이하        MySQL 8.0.31+ · 8.4         PostgreSQL
 UNION 만                 UNION · INTERSECT · EXCEPT  UNION · INTERSECT · EXCEPT
                          (DISTINCT/ALL 둘 다)        (전부 오래전부터)
```

**8.0.31 이전을 지원해야 하면** `INTERSECT` 는 `EXISTS`, `EXCEPT` 는 `NOT EXISTS` 로 쓴다([19번](../19-semi-anti-join/)).\
★ **단 그 우회는 `ALL` 의 개수 의미를 재현하지 못한다** — 2번의 `EXCEPT ALL` 이 낸 "2 − 1 = 1" 은 세미 조인으로 안 나온다.

---

### 13. 없는 낱말

**둘 다 두 엔진에서 문법 오류다.**

```text
### SQL: SELECT id FROM dept MINUS SELECT dept_id FROM emp;
--- PG 18.6 ---
ERROR:  syntax error at or near "SELECT"
LINE 1: SELECT id FROM dept MINUS SELECT dept_id FROM emp;
                                  ^
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near 'SELECT dept_id FROM emp' at line 1

### SQL: SELECT id, name FROM emp UNION CORRESPONDING SELECT name, id FROM dept;
--- PG 18.6 ---
ERROR:  syntax error at or near "CORRESPONDING"
LINE 1: SELECT id, name FROM emp UNION CORRESPONDING SELECT name, id...
                                       ^
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near 'CORRESPONDING SELECT name, id FROM dept' at line 1
```

- **`MINUS`** — 다른 엔진에서 쓰는 `EXCEPT` 의 동의어다. **여기서는 `EXCEPT` 를 쓴다.**\
  ★ PG 쪽 에러 위치를 보라 — 캐럿이 `MINUS` 가 아니라 **그다음 `SELECT`** 를 가리킨다. `MINUS` 를 **열 별칭**으로 읽고 넘어간 뒤 그다음 낱말에서 막힌 것이다.
- **`CORRESPONDING`** — **이름이 같은 열끼리 맞춰 주는** 표준 문법이다. 있으면 위 질의가 `id`↔`id`, `name`↔`name` 으로 붙었을 것이다.\
  **두 엔진 다 없으므로 열 순서를 직접 맞춰야 한다.** 그래서 열 순서를 잘못 맞춘 `UNION` 은 **타입이 우연히 맞으면 조용히 통과한다** — 6번의 MySQL 사례가 그 최악의 형태다.

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| 셋의 결과 (1번) | PG 18.6 · MySQL 8.4.10 | 각 4회 | `EXCEPT` 양방향 포함 |
| `ALL` 세 형태 (2번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | `INTERSECT ALL`·`EXCEPT ALL` 둘 다 |
| 가지 안의 중복 (3번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **1행 대 4행** |
| 16번 재인용 (4번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | 번호 판·이름 판·`UNION ALL` 판 |
| 열 개수 (5번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **에러 메시지가 근거다** |
| 타입 불일치 (6번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | **PG 의 에러와 MySQL 의 무경고 통과가 둘 다 근거다** |
| 계획 (7번) | PG 18.6 · MySQL 8.4.10 | 각 2회 × 2판 | 작성 중 1회 + 제출 직전 1회 — **드리프트 없음** |
| `ORDER BY`·`LIMIT` 자리 (8번) | PG 18.6 · MySQL 8.4.10 | 각 5회 | 가지 안·맨 끝·둘째 별칭·`LIMIT` 2종 |
| 결과 열 이름 (9번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **MySQL 의 뒤섞인 순서가 근거다** |
| `NULL` 취급 (10번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | |
| 우선순위 (11번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | 괄호 유무 |
| 도입 버전 (12번) | — | — | **릴리스 노트 인용**(실행 아님). 8.4.10 에서 동작하는 것은 1번이 보인다 |
| `MINUS`·`CORRESPONDING` (13번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **에러 메시지가 근거다** |

**구현 의존 항목** — 7번의 계획과 **모든 출력의 행 순서**다.\
`HashAggregate`·`Union materialize with deduplication`·`Stream results` 는 **그 엔진의 표기**이고, `Covering index scan on dept using name` 은 `dept.name` 의 `UNIQUE` 때문에 뜬 것이다.\
★ **순서는 실제로 흔들렸다** — 9번에서 MySQL 이 `20, 30, 10, 1, 2, 3, 4` 를 돌려줬다. `ORDER BY` 없는 출력에서 **순서로 아무것도 추론하지 마라.**

★ **한쪽에서만 결론이 서는 실험** — **6번(타입 불일치)이 그렇다.**\
PG 의 `UNION types integer and text cannot be matched` 는 **"PG 가 막는다"의 근거**이고, MySQL 의 7행 출력은 **"MySQL 이 문자열로 합친다"의 근거**다.\
두 출력은 **같은 사실의 양면이 아니라 서로 다른 두 사실**이다 — "집합 연산은 타입이 맞아야 한다"를 **양쪽 출력으로 함께 증명할 수는 없다.**\
12번도 실행이 근거가 아니다 — 8.4.10 에서 도는 것만 봐서는 **8.0.31 이라는 경계를 알 수 없고**, 그 경계는 릴리스 노트만이 근거다.

**언어 보장 항목** — 1\~5·8\~11·13번. 셋의 의미, `ALL` 의 개수 의미, 중복 판정 기준, `NULL` 취급, `ORDER BY` 의 자리, 결과 열 이름, 우선순위, `MINUS`/`CORRESPONDING` 부재는 **두 엔진에서 같았다**(에러 문구만 다르다).\
**방언이 갈리는 항목** — 6번(타입 불일치)과 12번(도입 버전) **둘뿐이다.** 그중 6번은 **에러가 아니라 조용한 차이**라 더 위험하다.

**순서 보장** — 없다. 위 출력에 `ORDER BY` 를 붙이지 **않은** 것들은 **순서를 근거로 쓰지 않는 자리**이고, 순서가 논점인 8번에는 붙였다.
