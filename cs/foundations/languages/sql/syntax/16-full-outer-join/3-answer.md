# sql/16-FULL OUTER JOIN — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력은 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 에러 메시지도 실제로 받은 것이고, 지어낸 출력은 없다.\
> 문서 근거는 [PG 18 Table Expressions](https://www.postgresql.org/docs/18/queries-table-expressions.html) · [MySQL 8.4 JOIN Clause](https://dev.mysql.com/doc/refman/8.4/en/join.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. `INNER` · `LEFT` · `RIGHT` · `FULL OUTER` 의 행 수

**3 · 4 · 4 · 5 다.**

```text
조인 조건 ON e.dept_id = d.id 를 통과하는 짝은 3개뿐이다

 emp          dept        짝?
------        ------      ----
 ann (10)  -- sales (10)   O
 bob (10)  -- sales (10)   O
 cho (20)  -- dev   (20)   O
 dan (NULL)   (어느 쪽과도 X — NULL = 10 은 UNKNOWN)
              hr    (30)   (짝지을 emp 가 없다)
```

```text
INNER (3행)          LEFT (4행)           RIGHT (4행)          FULL OUTER (5행)
+-----+-------+      +-----+-------+      +------+-------+     +------+-------+
| ann | sales |      | ann | sales |      | ann  | sales |     | ann  | sales |
| bob | sales |      | bob | sales |      | bob  | sales |     | bob  | sales |
| cho | dev   |      | cho | dev   |      | cho  | dev   |     | cho  | dev   |
+-----+-------+      | dan | NULL  |      | NULL | hr    |     | NULL | hr    |
                     +-----+-------+      +------+-------+     | dan  | NULL  |
                      + 왼쪽만 dan         + 오른쪽만 hr        +------+-------+
                                                                + 양쪽 다
```

PG 18.6 에서 네 형태를 실제로 돌린 출력이다.

```text
### INNER — SELECT e.name AS emp, d.name AS dept
            FROM emp e JOIN dept d ON e.dept_id = d.id ORDER BY e.id;
--- PG 18.6 ---                    --- MySQL 8.4.10 ---
 emp | dept
-----+-------                      +-----+-------+
 ann | sales                       | ann | sales |
 bob | sales                       | bob | sales |
 cho | dev                         | cho | dev   |
(3 rows)                           +-----+-------+

### LEFT
--- PG 18.6 ---                    --- MySQL 8.4.10 ---
 emp | dept
-----+-------                      +-----+-------+
 ann | sales                       | ann | sales |
 bob | sales                       | bob | sales |
 cho | dev                         | cho | dev   |
 dan | NULL                        | dan | NULL  |
(4 rows)                           +-----+-------+

### RIGHT
--- PG 18.6 ---                    --- MySQL 8.4.10 ---
 emp  | dept
------+-------                     +------+-------+
 ann  | sales                      | bob  | sales |
 bob  | sales                      | ann  | sales |
 cho  | dev                        | cho  | dev   |
 NULL | hr                         | NULL | hr    |
(4 rows)                           +------+-------+

### FULL OUTER
--- PG 18.6 ---                    --- MySQL 8.4.10 ---
 emp  | dept                       ERROR 1064 (42000)  <- 2번 참조
------+-------
 ann  | sales
 bob  | sales
 cho  | dev
 NULL | hr
 dan  | NULL
(5 rows)
```

**공식 — `FULL` = `LEFT` + `RIGHT` − `INNER`.**\
`4 + 4 − 3 = 5`. 가운데 겹치는 3행을 두 번 세지 않는다. 이 뺄셈이 5번·6번 문제의 열쇠다.

(`RIGHT` 출력에서 `ann`·`bob` 의 줄 순서가 두 엔진에서 다른 것은 `ORDER BY d.id` 로만 정렬해 동률이기 때문이다. 방언 차이가 아니다.)

> **외부 조인(outer join)** — 짝 못 찾은 행을 버리지 않고 반대쪽 열을 `NULL` 로 채워 남기는 조인.\
> 예: `dan` 은 부서가 없어도 `LEFT JOIN` 결과에 남고 `dept` 쪽 열이 `NULL` 이 된다.

---

### 2. `FULL OUTER JOIN` 을 두 엔진에 던지면

**PG 18.6 은 5행을 준다. MySQL 8.4.10 은 `ERROR 1064` 문법 오류를 낸다.**

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

`OUTER` 를 빼도 같다.

```text
### SQL: ... FROM emp e FULL JOIN dept d ON e.dept_id = d.id;
--- PG 18.6 ---   -> 위와 같은 5행
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: ... right syntax to use near 'FULL JOIN dept d ON e.dept_id = d.id'
```

**에러 번호가 말해 주는 것** — `1064` 는 MySQL 의 **문법 오류** 코드다.\
「이 기능은 지원하지 않습니다」가 아니라 **파서가 `FULL` 이라는 단어를 모른다.** 그래서 에러 메시지가 `FULL` 앞에서 끊긴다.

[MySQL 8.4 JOIN 페이지](https://dev.mysql.com/doc/refman/8.4/en/join.html)의 `joined_table` 문법에도 외부 조인은 이 두 줄뿐이다.

```text
table_reference {LEFT|RIGHT} [OUTER] JOIN table_reference join_specification
table_reference NATURAL [INNER | {LEFT|RIGHT} [OUTER]] JOIN table_factor
```

`FULL` 은 어디에도 없다.

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| `FULL OUTER JOIN` | ✓ 5행 | **✗ `ERROR 1064`** |
| `FULL JOIN` | ✓ 5행 | **✗ `ERROR 1064`** |
| `LEFT`/`RIGHT [OUTER] JOIN` | ✓ | ✓ |

**이 실패는 시끄럽다** — 배포 전에 반드시 터진다. 이 주제에서 조용히 틀리는 자리는 여기가 아니라 **우회 쪽**(5번)이다.

---

### 3. `(NULL, NULL)` 행의 두 `NULL` 은 각각 어디서 왔나

**왼쪽 `NULL` 은 원본 데이터(`dan.dept_id`), 오른쪽 `NULL` 은 조인이 만든 것이다.**

```text
### SQL: SELECT e.dept_id AS e_dept, d.id AS d_id
         FROM emp e FULL OUTER JOIN dept d ON e.dept_id = d.id ORDER BY d_id, e_dept;
--- PG 18.6 ---
 e_dept | d_id
--------+------
     10 |   10     ann — 짝 있음
     10 |   10     bob — 짝 있음
     20 |   20     cho — 짝 있음
   NULL |   30     hr  — 오른쪽만. 왼쪽 열은 조인이 채운 NULL
   NULL | NULL     dan — 왼쪽만. 오른쪽 열은 조인이 채운 NULL,
(5 rows)                 왼쪽 e_dept 는 원래부터 NULL
--- MySQL 8.4.10 ---
ERROR 1064 (42000) ... near 'FULL OUTER JOIN dept d ON e.dept_id = d.id ORDER BY d_id, e_dept'
```

```text
4번째 줄 (hr)                        5번째 줄 (dan)
+---------------------------+        +---------------------------+
| e_dept = NULL             |        | e_dept = NULL             |
|   -> 조인이 만든 NULL      |        |   -> 원본 데이터의 NULL    |
|      (짝지을 emp 가 없었다)|        |      (dan 은 소속이 없다)  |
| d_id = 30                 |        | d_id = NULL               |
|   -> 실제 값              |        |   -> 조인이 만든 NULL      |
+---------------------------+        +---------------------------+
        같은 열의 같은 NULL 인데 출처가 다르다
```

두 그림의 결론 — **결과만 봐서는 구분할 방법이 없다.** `NULL` 에는 출처 표시가 없다.

`dan` 이 짝을 못 찾은 이유도 `NULL` 때문이다 — `ON NULL = 10` 은 `UNKNOWN` 이고, `ON` 은 `TRUE` 만 통과시킨다([04번](../04-null-three-valued-logic/)).\
**그래서 `dan` 은 「부서 30번이 아닌 사람」도 아니고 「부서 30번인 사람」도 아니다.** 어디에도 안 붙는다.

이 구분 불가가 4번 문제로 이어진다.

---

### 4. 왜 `WHERE d.name IS NULL` 이 아니라 `WHERE d.id IS NULL` 인가

**`d.id` 는 기본키라 원본에 `NULL` 이 있을 수 없고, `d.name` 은 있을 수 있기 때문이다.**

```text
d.id 가 NULL 이다                     d.name 이 NULL 이다
   ↓                                     ↓
원본에는 NULL 이 없다 (PRIMARY KEY)    원본에도 NULL 이 있을 수 있다
   ↓                                     ↓
그러므로 조인이 만든 NULL 이다          그러므로 둘 중 어느 쪽인지 모른다
   = 짝을 못 찾았다                      = 판정 불가
```

`dept.name` 은 이 예시에서 마침 `NOT NULL` 이지만, **스키마가 바뀌면 조용히 틀린다.**\
기본키를 보는 습관은 스키마 변경에 안 깨진다.

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
ERROR 1064 (42000) ... near 'FULL OUTER JOIN dept d ON e.dept_id = d.id WHERE e.id IS NULL OR d.id IS NULL'
```

**이것이 대사 질의의 표준 형태다** — 「어느 한쪽에만 있는 것」 두 종류를 한 번에 뽑는다.

- `e.id IS NULL` → 오른쪽에만 있는 행 (`hr`)
- `d.id IS NULL` → 왼쪽에만 있는 행 (`dan`)

> **대사(reconciliation)** — 두 데이터 소스를 맞춰 보고 어긋난 곳을 찾는 일.\
> 예: 주문은 있는데 결제가 없는 건과, 결제는 있는데 주문이 없는 건을 한 질의로 뽑기.

양쪽을 한 장의 표로 합쳐 보려면 `COALESCE` 로 키를 붙인다.

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

`dan` 의 `dept_id` 가 여전히 `NULL` 인 것은 **양쪽 다 `NULL` 이라 채울 값이 없기** 때문이다 — `COALESCE` 도 없는 값을 만들지는 못한다.

---

### 5. `LEFT UNION RIGHT` 의 행 수는 `FULL OUTER` 와 같은가

**같지 않다. 4행이다. `FULL OUTER` 는 5행이다.**

**`UNION` 이 중복 행을 지우기 때문이다.**

```text
LEFT JOIN 이 내놓는 (e_dept, d_id)      RIGHT JOIN 이 내놓는 (e_dept, d_id)
  (10, 10)   ann                          (10, 10)   ann
  (10, 10)   bob                          (10, 10)   bob
  (20, 20)   cho                          (20, 20)   cho
  (NULL, NULL) dan                        (NULL, 30) hr
        \                                    /
         +------------ UNION ---------------+
                         ↓
    값이 같은 행을 하나로 접는다
    (10,10) 이 네 개 -> 한 개      <- ann 과 bob 이 여기서 사라진다
    (20,20) 이 두 개 -> 한 개
    (NULL,NULL) 한 개
    (NULL,30)   한 개
                         ↓
                       4행
```

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
   NULL |   30                                  10 |   10  <- 두 행이 살아 있다
     20 |   20                                  20 |   20
     10 |   10  <- 한 행으로 접혔다           NULL |   30
(4 rows)                                      NULL | NULL
                                           (5 rows)
--- MySQL 8.4.10 ---                       --- MySQL 8.4.10 ---
+--------+------+                          ERROR 1064 (42000) ...
| e_dept | d_id |
+--------+------+
|     10 |   10 |
|     20 |   20 |
|   NULL | NULL |
|   NULL |   30 |
+--------+------+
  4행 — PG 와 같다
```

**이 실패가 위험한 이유는 데이터에 따라 숨는다는 것이다.**

```text
이름 열로 뽑으면                    키 열로 뽑으면
 ann | sales                        (10, 10)
 bob | sales                        (10, 10)   <- 값이 같다
 cho | dev                          (20, 20)
 dan | NULL                         (NULL, NULL)
 NULL| hr                           (NULL, 30)
   -> ann ≠ bob 이라 안 접힌다        -> 접힌다
   -> 5행. 맞는 것처럼 보인다          -> 4행. 틀린다
```

실제로 이름 열 버전은 양쪽 엔진에서 5행이 나온다.

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

**테스트 데이터에서는 통과하고 운영 데이터에서 행이 줄어드는** 전형적인 무음 실패다.\
중복이 없는 표였기 때문에 맞은 것이지, 우회가 맞았던 게 아니다.

---

### 6. 5번을 고쳐 `FULL OUTER JOIN` 과 같게 만들려면

**`UNION` 을 `UNION ALL` 로 바꾸고, 오른쪽 가지에 `WHERE e.id IS NULL` 을 붙인다.**

```text
바꾸기 전                            바꾼 뒤
LEFT  전체  (4행)                    LEFT 전체            (4행)
UNION   <- 중복 제거로 겹침 처리      UNION ALL            (중복 제거 안 함)
RIGHT 전체  (4행)                    RIGHT 중 짝 없는 것만 (1행)
  -> 겹치는 3행을 값으로 접다가         -> 겹치는 3행을 아예 안 가져온다
     엉뚱한 중복까지 접는다              -> 4 + 1 = 5행
```

`FULL` = `LEFT` + `RIGHT` − `INNER` 라는 1번의 공식을, **빼기 대신 처음부터 안 더하는 방식**으로 구현한 것이다.

```text
### SQL: SELECT e.dept_id AS e_dept, d.id AS d_id
           FROM emp e LEFT JOIN dept d ON e.dept_id = d.id
         UNION ALL
         SELECT e.dept_id, d.id
           FROM emp e RIGHT JOIN dept d ON e.dept_id = d.id
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

**5행이고, PG 의 `FULL OUTER JOIN` 결과와 행 단위로 같다**(3번의 출력과 대조해 보라).\
MySQL 에서도 같은 5행이 나온다 — 이것이 MySQL 에서 쓸 수 있는 올바른 우회다.

`WHERE e.id IS NULL` 이 맞는 이유는 4번과 같다 — `e.id` 는 기본키라 **`NULL` 이면 조인이 만든 것**, 즉 짝 없는 오른쪽 행이다.

> **반조인(anti join)** — 「저쪽에 짝이 없는 행」만 남기는 조인. `WHERE 키 IS NULL` 이나 `NOT EXISTS` 로 쓴다.\
> 예: `RIGHT JOIN ... WHERE e.id IS NULL` 은 사원 없는 부서 `hr` 만 준다.

주의할 점 둘.

- **`UNION ALL` 은 중복 제거를 안 하므로 겹침을 직접 잘라야 한다.** 반조인 조건을 빼먹으면 3행이 두 번 들어간다.
- **`e.id` 대신 `e.dept_id IS NULL` 을 쓰면 틀린다.** `dan` 의 `dept_id` 가 원래 `NULL` 이라 `dan` 이 끼어든다.

---

### 7. `WHERE d.name = 'sales'` 를 붙이면 행 수는

**2행이고, `INNER JOIN` 에 같은 조건을 건 것과 똑같은 모양이다.**

```text
FULL OUTER 가 만든 5행이 WHERE 를 지난다

 emp  | dept  | d.name = 'sales' | 처분
------+-------+------------------+------
 ann  | sales | TRUE             | 통과
 bob  | sales | TRUE             | 통과
 cho  | dev   | FALSE            | 버림
 NULL | hr    | FALSE            | 버림
 dan  | NULL  | UNKNOWN          | 버림   <- NULL = 'sales' 는 UNKNOWN
                                   ↓
                                 2행
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
ERROR 1064 (42000) ... near 'FULL OUTER JOIN dept d ON e.dept_id = d.id WHERE d.name = 'sales''
```

**`FULL OUTER` 라고 적었는데 외부 조인의 효과가 전부 사라졌다.**

```text
ON 에 둔 조건                        WHERE 에 둔 조건
+---------------------------+       +---------------------------+
| 짝짓는 규칙                |       | 이미 만들어진 행의 필터    |
| 탈락해도 행은 NULL 로 남는다|       | 탈락하면 행이 없어진다     |
+---------------------------+       +---------------------------+
        외부 조인 유지                 외부 조인이 내부 조인으로 무너짐
```

`dan` 이 잘린 이유가 특히 조용하다 — `d.name` 이 `NULL` 이라 `NULL = 'sales'` 가 `UNKNOWN` 이고, `WHERE` 는 `UNKNOWN` 을 버린다([04번](../04-null-three-valued-logic/)).\
**즉 조건이 「`sales` 가 아니다」라서 잘린 게 아니라 「판정할 수 없어서」 잘렸다.**

같은 의도를 유지하려면 조건을 `ON` 으로 옮기거나 `NULL` 을 명시적으로 허용한다.

```sql
-- 조건을 ON 으로
FROM emp e FULL OUTER JOIN dept d ON e.dept_id = d.id AND d.name = 'sales'
-- 또는 NULL 도 통과시킨다
WHERE d.name = 'sales' OR d.id IS NULL OR e.id IS NULL
```

조건 위치의 규칙 자체는 [목록의 **15번 주제**](../15-on-vs-where-in-outer-join/)이 정본이다.

---

### 8. PG 가 `ON e.dept_id > d.id` 인 `FULL OUTER JOIN` 을 받아들이는가

**받아들이지 않는다. 다만 MySQL 과는 다른 이유로 거절한다.**

```text
### SQL: SELECT e.name AS emp, d.name AS dept
         FROM emp e FULL OUTER JOIN dept d ON e.dept_id > d.id;
--- PG 18.6 ---
ERROR:  FULL JOIN is only supported with merge-joinable or hash-joinable join conditions
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; ...
  right syntax to use near 'FULL OUTER JOIN dept d ON e.dept_id > d.id' at line 1
```

**두 에러는 같은 「안 된다」가 아니다.**

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| 무엇이 문제인가 | **이 조건으로는** 못 한다 | **이 문법 자체가** 없다 |
| 언제 걸리나 | 계획을 세울 때 | 파싱할 때 |
| 등호 조건이면 | 된다 | 여전히 안 된다 |

PG 가 거절하는 이유는 구현 방식에 있다.

```text
FULL 을 하려면 양쪽 모두에서 "짝 없는 행"을 알아내야 한다
        ↓
그걸 알려면 양쪽을 통째로 맞춰 봐야 한다
        ↓
PG 는 그 맞춤을 머지 조인 또는 해시 조인으로만 한다
        ↓
머지: 양쪽을 정렬해 나란히 훑는다   -> 등호 관계가 전제
해시: 키로 해시 표를 만들어 찾는다   -> 등호 관계가 전제
        ↓
부등호(>)는 둘 중 어느 쪽에도 안 맞는다 -> 거절
```

> **머지 조인 / 해시 조인** — 양쪽을 정렬해 훑거나 해시 표를 만들어 맞추는 조인 알고리즘.\
> 예: `ON a.id = b.id` 는 둘 다 가능하지만 `ON a.id > b.id` 는 중첩 루프로만 된다.

**우회는 4·6번과 같은 형태다** — `LEFT` 와 `RIGHT` 를 직접 합친다.

```sql
SELECT e.name AS emp, d.name AS dept
  FROM emp e LEFT JOIN dept d ON e.dept_id > d.id
UNION ALL
SELECT e.name, d.name
  FROM emp e RIGHT JOIN dept d ON e.dept_id > d.id
 WHERE e.id IS NULL;
```

`LEFT`·`RIGHT` 는 중첩 루프로도 돌 수 있어서 **부등호 조건이 허용된다.** 양쪽 엔진에서 확인했다.

```text
### SQL: SELECT e.name AS emp, d.name AS dept
         FROM emp e LEFT JOIN dept d ON e.dept_id > d.id ORDER BY e.id, d.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | dept                      +-----+-------+
-----+-------                    | emp | dept  |
 ann | NULL                      +-----+-------+
 bob | NULL                      | ann | NULL  |
 cho | sales                     | bob | NULL  |
 dan | NULL                      | cho | sales |
(4 rows)                         | dan | NULL  |
                                 +-----+-------+
```

(`cho` 의 `dept_id=20` 만 `sales`(10)보다 커서 짝을 찾았다. 나머지는 짝이 없어 `NULL` 로 남았다.)

**즉 `FULL` 의 제약은 「외부 조인의 제약」이 아니라 「양방향으로 해야 해서 생긴 제약」이다.**

## 실행 검증

**원저자가 몇 번 돌렸는지는 문서에 남아 있지 않아 모른다.** 아래 「몇 번」은 **2026-09-21 재검증에서 실제로 돌린 횟수**다 —\
본문의 실행 블록을 **전부 다시 던져** 문서 값과 대조했고, **어긋난 블록은 0건**이었다.\
좌우로 손 배치한 블록(1번의 네 형태, 5번의 A/B)도 **한 판씩 따로 던져** 칸을 맞췄다.

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| `INNER` (1번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 3행 |
| `LEFT` (1번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 4행 — `dan` 의 부서 칸이 `NULL` |
| `RIGHT` (1번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 4행 · **`ORDER BY d.id` 뿐이라 `ann`·`bob` 이 동률** |
| ★ `FULL OUTER JOIN` (1·2번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | PG 5행 / **MySQL `ERROR 1064`** |
| `OUTER` 를 뺀 `FULL JOIN` (2번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 같은 결과 / 같은 에러 |
| 키 두 열만 남긴 판 (3번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `(NULL, NULL)` 행이 나온다 |
| 짝 없는 행만 (4번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 2행 — 대사 질의의 표준형 |
| `COALESCE` 로 키 합치기 (4번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `dan` 의 키는 **여전히 `NULL`** |
| ★ `UNION` 우회 — 이름 열 (5번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **5행. 맞는 것처럼 보인다** |
| ★ `UNION` 우회 — 키 열 (5번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **4행. 여기서 무너진다** |
| `UNION ALL` + 반조인 (6번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 5행 — **PG 의 `FULL OUTER` 와 행 단위로 같다** |
| `WHERE` 로 무너뜨리기 (7번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 5행 → **2행** |
| ★ 부등호 `FULL` (8번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **PG 는 계획 오류 · MySQL 은 문법 오류** |
| 부등호 `LEFT` (8번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 4행 — 중첩 루프로 돌아간다 |

**★ 한쪽에서만 결론이 서는 실험** — 이 주제의 절반이 그렇다.\
`FULL OUTER JOIN` 의 **동작**은 **PG 출력만이 근거**이고, 「MySQL 에는 없다」는 **MySQL 의 `ERROR 1064` 만이 근거**다.\
둘을 바꿔 읽으면 틀린다 — 본문에서 MySQL 칸이 계속 `ERROR 1064` 인 것은 **출력이 없어서가 아니라 그것이 출력**이기 때문이다.\
반대로 **5·6번(우회)은 양쪽을 다 던져야 결론이 선다.** 한쪽만 보면 「`UNION` 으로 되더라」를 외우고 운영에서 행이 줄어든다.

**구현 의존 항목** — 8번의 **PG 쪽 거절 사유**다. `FULL JOIN is only supported with merge-joinable or hash-joinable join conditions` 은\
**표준이 금지한 것이 아니라 PG 가 `FULL` 을 머지/해시로만 구현했기 때문**이다. 다른 엔진은 다르게 할 수 있다.\
1번 `RIGHT` 출력에서 `ann`·`bob` 의 줄 순서가 두 엔진에서 다른 것도 같은 성격이다 — **동률의 순서는 관찰이지 보장이 아니다.**\
에러 번호·문구(`1064`)도 구현 세부다.

**언어 보장 항목** — 1·3·4·6·7번. `FULL` = `LEFT` + `RIGHT` − `INNER` 라는 셈, 짝 없는 행의 반대쪽 열이 **전부** `NULL` 로 채워진다는 것,\
조인이 만든 `NULL` 과 원본 `NULL` 이 결과에서 구분되지 않는다는 것, `UNION` 이 중복을 지우고 `UNION ALL` 이 안 지운다는 것,\
외부 조인에 `WHERE` 를 붙이면 내부 조인으로 무너진다는 것은 **두 엔진에서 같았다**(MySQL 은 우회 형태로 확인).

**방언이 갈리는 항목 — 버전이 오르면 다시 찍을 자리** — ① `FULL [OUTER] JOIN` 문법의 유무(**2번을 먼저 다시 돌린다** — 이 편 전체가 그 위에 서 있다)\
② 부등호 `FULL` 에 대한 PG 의 제약(8번) ③ 에러 번호·문구 ④ 동률 행의 줄 순서.

**DB 잔재** — 없다. 이 주제는 **`emp`·`dept` 를 읽기만 했다.** 두 엔진의 최종 표 목록은 [52 UPSERT](../52-upsert/)의 「실행 검증」에 있다.
