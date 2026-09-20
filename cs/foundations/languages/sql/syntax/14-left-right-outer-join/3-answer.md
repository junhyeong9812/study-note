# sql/14-LEFT·RIGHT OUTER JOIN — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력은 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 지어낸 출력은 없다.\
> 문서 근거는 [PG 18 Table Expressions](https://www.postgresql.org/docs/18/queries-table-expressions.html) · [MySQL 8.4 JOIN Clause](https://dev.mysql.com/doc/refman/8.4/en/join.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. `LEFT JOIN` 의 결과 행 수와 더 있는 행

**4행이다. `INNER JOIN`(3행)에 `dan` 한 행이 더 있다.**

```text
### SQL: SELECT e.name AS emp, d.name AS dept FROM emp e LEFT OUTER JOIN dept d ON e.dept_id = d.id ORDER BY e.id;
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

```text
 INNER (3행)             LEFT (4행)
+-----+-------+         +-----+-------+
| ann | sales |         | ann | sales |
| bob | sales |         | bob | sales |
| cho | dev   |         | cho | dev   |
+-----+-------+         | dan | NULL  |   <- ON 에서 짝을 못 찾았지만
                        +-----+-------+      버리지 않고 NULL 로 채워 남겼다
```

**`hr` 은 여전히 없다.** `LEFT` 가 보존하는 것은 **왼쪽뿐**이다.\
`hr` 을 살리려면 `RIGHT`(4번), 둘 다 살리려면 `FULL OUTER`([16번](../16-full-outer-join/))다.

> **외부 조인(outer join)** — 짝 못 찾은 행을 버리지 않고 반대쪽 열을 `NULL` 로 채워 남기는 조인.\
> 예: `dan` 의 `dept` 쪽 열이 전부 `NULL` 이 된 채 결과에 남는다.

---

### 2. `dan` 의 행에서 `dept` 쪽 열 중 몇 개가 `NULL` 인가

**전부다. 일부만 채워지는 일은 없다.**

```text
### SQL: SELECT e.name AS emp, e.dept_id AS e_dept, d.id AS d_id, d.name AS dept
         FROM emp e LEFT JOIN dept d ON e.dept_id = d.id ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | e_dept | d_id | dept     +-----+--------+------+-------+
-----+--------+------+-------   | emp | e_dept | d_id | dept  |
 ann |     10 |   10 | sales    +-----+--------+------+-------+
 bob |     10 |   10 | sales    | ann |     10 |   10 | sales |
 cho |     20 |   20 | dev      | bob |     10 |   10 | sales |
 dan |   NULL | NULL | NULL     | cho |     20 |   20 | dev   |
(4 rows)                        | dan |   NULL | NULL | NULL  |
                                +-----+--------+------+-------+
```

`dan` 행의 `d_id` 와 `dept` 가 **둘 다** `NULL` 이다.

```text
 짝을 찾은 행                    짝을 못 찾은 행
+-------------------+           +-------------------+
| 왼쪽 열: 실제 값   |           | 왼쪽 열: 실제 값   |
| 오른쪽 열: 실제 값 |           | 오른쪽 열: 전부 NULL|  <- "가상의 빈 행"과 짝지은 셈
+-------------------+           +-------------------+
```

★ **`dan` 행에는 성격이 다른 `NULL` 이 둘 있다.**

| 열 | `NULL` 인 이유 |
|---|---|
| `e_dept`(`emp.dept_id`) | **원본 데이터**가 `NULL` — `dan` 은 소속이 없다 |
| `d_id`·`dept` | **조인이 만든** `NULL` — 짝을 못 찾아 채워졌다 |

**화면에서는 똑같이 보인다.** 이것이 6번·7번 사고의 뿌리다.

---

### 3. 「결과 행 수 = 왼쪽 행 수」는 맞는가

**아니다. 보장되는 것은 등식이 아니라 하한이다 — 결과 ≥ 왼쪽.**

```text
LEFT JOIN 이 보장하는 것              보장하지 않는 것
 왼쪽 행은 최소 한 번은 나온다          왼쪽 행이 정확히 한 번만 나온다
```

오른쪽에 짝이 여럿이면 **는다.** `dept` 를 왼쪽에 두면 바로 보인다.

```text
### SQL: SELECT d.name AS dept, e.name AS emp FROM dept d LEFT JOIN emp e ON e.dept_id = d.id
         ORDER BY d.id, e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept  | emp                     +-------+------+
-------+------                   | dept  | emp  |
 sales | ann                     +-------+------+
 sales | bob                     | sales | ann  |
 dev   | cho                     | sales | bob  |
 hr    | NULL                    | dev   | cho  |
(4 rows)                         | hr    | NULL |
                                 +-------+------+
```

`dept` **3행**이 결과 **4행**이 됐다.

```text
 dept 3행                     결과 4행
 sales  --- 2줄 --->          sales | ann     <- 팬아웃으로 늘었다
                              sales | bob
 dev    --- 1줄 --->          dev   | cho
 hr     --- 1줄 --->          hr    | NULL    <- 짝이 없어 NULL 로 남았다
```

★ **하나도 안 잃었고(3 ≥ 3), 하나는 늘었다.** `LEFT` 를 썼다고 `SUM` 이나 `COUNT` 가 안전해지지 않는다.\
[13번](../13-inner-join/)의 팬아웃이 외부 조인에서도 그대로 작동한다 — 집계 전에 **행 수를 센다**(목록의 **25번 주제**).

---

### 4. `(A) emp LEFT JOIN dept` 와 `(B) dept RIGHT JOIN emp` 는 같은가

**같다.**

```text
### SQL: SELECT e.name AS emp, d.name AS dept FROM dept d RIGHT JOIN emp e ON e.dept_id = d.id ORDER BY e.id;
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

1번의 `LEFT JOIN` 출력과 **한 글자도 다르지 않다.**

```text
 A LEFT  JOIN B        ==        B RIGHT JOIN A
   보존 측 = A                     보존 측 = A
        ↑                               ↑
  "앞에 적은 것"                  "뒤에 적은 것"
```

`RIGHT` 를 그대로 쓰면 **보존되는 쪽이 바뀐다** — `hr` 이 남고 `dan` 이 사라진다.

```text
### SQL: SELECT e.name AS emp, d.name AS dept FROM emp e RIGHT OUTER JOIN dept d ON e.dept_id = d.id
         ORDER BY d.id, e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp  | dept                     +------+-------+
------+-------                   | emp  | dept  |
 ann  | sales                    +------+-------+
 bob  | sales                    | ann  | sales |
 cho  | dev                      | bob  | sales |
 NULL | hr                       | cho  | dev   |
(4 rows)                         | NULL | hr    |
                                 +------+-------+
```

| | 보존 측 | 되살아나는 행 | 행 수 |
|---|---|---|---|
| `emp LEFT JOIN dept` | `emp` | `dan` | 4 |
| `emp RIGHT JOIN dept` | `dept` | `hr` | 4 |
| `dept RIGHT JOIN emp` | `emp` | `dan` | 4 |

---

### 5. `RIGHT JOIN` 을 덜 쓰는 이유

**문법이 나빠서가 아니라 읽는 방향이 뒤집히기 때문이다.**

```text
LEFT 로 통일한 질의                     RIGHT 가 섞인 질의
FROM emp e                             FROM dept d
  LEFT JOIN dept d ON ...                RIGHT JOIN emp e ON ...
  LEFT JOIN proj p ON ...                LEFT  JOIN proj p ON ...
       ↑                                      ↑
 첫 줄이 "무엇의 목록인가"를 말한다      첫 줄이 기준이 아니다 —
 아래로 읽으면 붙는 것만 늘어난다        둘째 줄까지 읽어야 기준을 안다
```

**조인이 셋 넷으로 늘면 차이가 커진다.**

- `LEFT` 만 쓰면 보존 측이 **항상 첫 표**다. 아래로 읽어 내려가기만 하면 된다.
- `RIGHT` 가 섞이면 줄마다 **어느 쪽이 보존 측인지 따져야** 한다.
- 그리고 `LEFT` 와 `RIGHT` 가 한 질의에 섞이면 **보존 측이 중간에서 바뀐다** — 사람이 추적하기 어렵다.

★ **4번이 보여 준 등식이 있으니 손해가 없다.** 기준 표를 `FROM` 바로 뒤로 옮기고 `LEFT` 로 적으면 똑같은 결과를 더 읽기 쉽게 얻는다.

> 「`RIGHT JOIN` 은 성능이 나쁘다」 같은 말은 근거가 없다. 위 두 출력이 같은 결과이고, 엔진이 무엇을 먼저 읽을지는 옵티마이저가 정한다.\
> **읽기 쉬움만이 이유다.**

---

### 6. 왜 `d.name IS NULL` 이 아니라 `d.id IS NULL` 인가

**`d.name` 은 원본에도 `NULL` 일 수 있지만, `d.id` 는 기본키라 원본에 절대 `NULL` 이 없기 때문이다.**

```text
 WHERE d.id IS NULL 이 뜻하는 것        WHERE d.name IS NULL 이 뜻하는 것
 "여기가 NULL 이면 조인이 만든 것이다"   "짝이 없거나, 짝이 있는데
  -> 짝을 못 찾은 행                      그 부서의 이름이 NULL 이거나"
        ↑                                        ↑
  판정이 하나로 정해진다                  두 경우가 섞인다
```

```text
### SQL: SELECT e.name AS emp, d.name AS dept FROM emp e LEFT JOIN dept d ON e.dept_id = d.id
         WHERE d.id IS NULL;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | dept                      +-----+------+
-----+------                     | emp | dept |
 dan | NULL                      +-----+------+
(1 row)                          | dan | NULL |
                                 +-----+------+
```

**이 예시 데이터에서는 `d.name` 으로도 같은 답이 나온다** — `dept.name` 이 `NOT NULL` 이기 때문이다.

```text
### SQL: SELECT e.name AS emp FROM emp e LEFT JOIN dept d ON e.dept_id = d.id
         WHERE d.name IS NULL ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp                             +-----+
-----                            | emp |
 dan                             +-----+
(1 row)                          | dan |
                                 +-----+
```

★ **그래서 더 위험하다.** 지금 맞으니까 옳은 줄 알고 쓰다가, **`name` 에 `NULL` 을 허용하는 열로 바꾸는 순간 조용히 틀린다.**\
「지금 잘 나오는데요」는 보장이 아니다 — [01번](../01-logical-query-processing-order/)의 `ORDER BY` 없는 `LIMIT` 과 같은 성격이다.

**규칙으로 고정한다 — 짝 여부는 `NULL` 일 수 없는 열로 판정한다.** 기본키가 그 자리다.\
같은 규칙을 [16번](../16-full-outer-join/)에서도 쓴다.

---

### 7. ★ `WHERE d.id <> 10` — 결과와 이유

**`cho` 한 행만 나온다. `dan` 이 사라졌다.**

```text
### SQL: SELECT e.name AS emp, d.name AS dept FROM emp e LEFT JOIN dept d ON e.dept_id = d.id
         WHERE d.id <> 10 ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | dept                      +-----+------+
-----+------                     | emp | dept |
 cho | dev                       +-----+------+
(1 row)                          | cho | dev  |
                                 +-----+------+
```

**왜 그런가 — 조인이 만든 `NULL` 이 3값 논리에 걸렸다.**

```text
LEFT JOIN 이 만든 4행이 WHERE d.id <> 10 을 지난다

 emp | d.id |  d.id <> 10  | WHERE 의 처분
-----+------+--------------+---------------
 ann |   10 | FALSE        | 버림
 bob |   10 | FALSE        | 버림
 cho |   20 | TRUE         | 통과
 dan | NULL | UNKNOWN      | 버림   <- "모르는 값이 10 이 아닌가?" 답할 수 없다
```

★ **`dan` 의 `d.id` 는 원본에 없던 `NULL` 이다.** `dept.id` 는 기본키라 `NULL` 이 들어갈 수 없는데도,\
**조인 결과에는 `NULL` 이 생겼고** 그것이 [04번](../04-null-three-valued-logic/)의 규칙에 걸렸다.

```text
04번에서 배운 것                     여기서 일어난 것
 WHERE 는 TRUE 만 통과시킨다          LEFT JOIN 이 NULL 을 만들었다
 NULL 이 비교에 끼면 UNKNOWN 이다            ↓
        ↓                            그 NULL 이 WHERE 의 비교에 들어갔다
 UNKNOWN 행은 버려진다                       ↓
                                     되살린 행이 다시 죽었다
```

**이것이 이 주제가 04번에 걸리는 핵심이다** — 원본에 `NULL` 이 하나도 없는 표끼리 조인해도, **외부 조인이면 `NULL` 이 생긴다.**\
즉 **3값 논리는 `NULL` 을 허용하는 스키마에서만 나오는 문제가 아니다.**

---

### 8. ★ `WHERE d.name = 'sales'` — 행 수와 같은 모양

**2행이다. `INNER JOIN` 의 결과와 같은 모양이다.**

```text
### SQL: SELECT e.name AS emp, d.name AS dept FROM emp e LEFT JOIN dept d ON e.dept_id = d.id
         WHERE d.name = 'sales' ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | dept                      +-----+-------+
-----+-------                    | emp | dept  |
 ann | sales                     +-----+-------+
 bob | sales                     | ann | sales |
(2 rows)                         | bob | sales |
                                 +-----+-------+
```

```text
 LEFT JOIN 이 만든 4행              WHERE d.name = 'sales'
 ann | sales                        TRUE     -> 통과
 bob | sales                        TRUE     -> 통과
 cho | dev                          FALSE    -> 버림
 dan | NULL                         UNKNOWN  -> 버림
                                              ↓
                                    "짝을 찾은 행 중 조건에 맞는 것"만 남았다
                                     = INNER JOIN 과 같은 성질
```

★ **`LEFT JOIN` 이라고 써 놓고 `INNER JOIN` 을 받은 것이다.**\
`NULL` 로 채워진 행은 **어떤 등호 조건도 통과하지 못하므로**, `WHERE` 에 오른쪽 열 등호 조건이 하나라도 있으면 보존 측 보장이 통째로 사라진다.

```text
      의도                                실제
 "모든 사원 + 그 중 sales 인 사람의 부서명"  "sales 부서 사원만"
        4행                                 2행
```

**같은 조건을 `ON` 에 두면 4행이 유지된다.**

```text
### SQL: SELECT e.name AS emp, d.name AS dept FROM emp e LEFT JOIN dept d
         ON e.dept_id = d.id AND d.name = 'sales' ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | dept                      +-----+-------+
-----+-------                    | emp | dept  |
 ann | sales                     +-----+-------+
 bob | sales                     | ann | sales |
 cho | NULL                      | bob | sales |
 dan | NULL                      | cho | NULL  |
(4 rows)                         | dan | NULL  |
                                 +-----+-------+
```

**4행이다. 그리고 `cho` 의 부서명이 `NULL` 이 됐다** — 짝짓기 단계에서 떨어졌으므로 「빈 짝」으로 채워진 것이다.

이 대비가 **[15번](../15-on-vs-where-in-outer-join/)의 전부**다. 왜 그렇게 되는지는 거기가 정본이다.\
**경계: 여기는 「`WHERE` 가 보존을 깬다」는 사실까지, 처리 순서로 설명하는 것과 실행 계획은 15번.**

---

### 9. 7번에서 `dan` 을 살리려면

**`OR d.id IS NULL` 을 더한다.**

```text
### SQL: SELECT e.name AS emp, d.name AS dept FROM emp e LEFT JOIN dept d ON e.dept_id = d.id
         WHERE d.id <> 10 OR d.id IS NULL ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | dept                      +-----+------+
-----+------                     | emp | dept |
 cho | dev                       +-----+------+
 dan | NULL                      | cho | dev  |
(2 rows)                         | dan | NULL |
                                 +-----+------+
```

**왜 이게 되나** — `OR` 가 `UNKNOWN` 을 `TRUE` 로 바꿔 준다.

```text
 dan 행의 판정

 d.id <> 10        UNKNOWN
 d.id IS NULL      TRUE          <- IS NULL 은 3값 논리를 벗어나는 연산자다
 -------------------------
 UNKNOWN OR TRUE = TRUE          <- 04번의 진리표: 한쪽이 TRUE 면 끝났다
```

★ **`IS NULL` 은 `= NULL` 과 다르다.** `= NULL` 은 `UNKNOWN` 을 주지만 `IS NULL` 은 `TRUE`/`FALSE` 만 준다.\
그래서 3값 논리의 구멍을 메우는 유일한 도구다([04번](../04-null-three-valued-logic/)·목록의 **05번 주제**).

**다른 두 가지 고치는 법.**

```sql
-- (A) 조건을 ON 으로 옮긴다 — 뜻이 "붙이는 규칙"으로 바뀐다 (15번)
SELECT e.name, d.name FROM emp e LEFT JOIN dept d ON e.dept_id = d.id AND d.id <> 10;

-- (B) 왼쪽 열로 판정한다 — 조인이 만든 NULL 을 아예 안 건드린다
SELECT e.name FROM emp e WHERE e.dept_id IS DISTINCT FROM 10;   -- PG
```

(B)의 `IS DISTINCT FROM` 은 방언이 갈리는 연산자라 목록의 **05번 주제**가 정본이다.\
**가장 안전한 것은 (A)** — 조건의 뜻이 「붙이는 규칙」인지 「결과 필터」인지를 자리로 말하게 하는 것이다.

---

### 10. `hr` 행의 `star` 와 `emp_cnt`

**`star` 는 1, `emp_cnt` 는 0 이다.**

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

**왜 다른가** — 두 `COUNT` 가 세는 것이 다르다.

```text
 hr 그룹에 들어 있는 것

 +----------+----------+
 | d.name   | e.id     |
 | 'hr'     | NULL     |   <- 조인이 만든 행 하나
 +----------+----------+

 COUNT(*)    행을 센다           -> 1    (행은 분명히 하나 있다)
 COUNT(e.id) NULL 아닌 값을 센다 -> 0    (e.id 가 NULL 이므로 안 센다)
```

★ **외부 조인 뒤의 `COUNT(*)` 은 「몇 건인가」의 답이 아니다.**\
「사원이 0명인 부서」를 찾으려고 `HAVING COUNT(*) = 0` 을 쓰면 영원히 안 맞는다 — 1이기 때문이다.\
맞는 것은 `HAVING COUNT(e.id) = 0` 이다.

```text
 틀린 질의                              맞는 질의
 GROUP BY ... HAVING COUNT(*) = 0       GROUP BY ... HAVING COUNT(e.id) = 0
   -> hr 의 COUNT(*) 은 1 이라 안 걸린다   -> hr 의 COUNT(e.id) 는 0 이라 걸린다
```

`INNER JOIN` 이었다면 `hr` 그룹 자체가 없었을 것이고, `GROUP BY` 는 **행이 없는 그룹을 만들지 않는다**([03번](../03-where-vs-having/)).\
그래서 **「0건을 표에 남기려면 외부 조인이 필요하다」** — 이것이 `LEFT JOIN` 의 세 번째 실전 형태다.

`COUNT` 의 세 형태는 목록의 **21번 주제**가 정본이다.

---

### 11. 이 주제에서 두 엔진의 출력이 다른 자리가 있는가

**없다. 위 모든 출력이 양쪽에서 같았다.**

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| `LEFT [OUTER] JOIN` | ✓ | ✓ |
| `RIGHT [OUTER] JOIN` | ✓ | ✓ |
| `OUTER` 생략 | ✓ | ✓ |
| 짝 없는 행의 `NULL` 채우기 | ✓ 전부 | ✓ 전부 |
| `WHERE` 가 보존을 깨는 것 | ✓ 같은 결과 | ✓ 같은 결과 |

**갈리는 것은 [16번](../16-full-outer-join/)부터다** — `FULL OUTER JOIN` 이 MySQL 8.4.10 에 아예 없다(`ERROR 1064`).

★ **단 하나 주의할 것은 「출력이 같다」와 「행 순서가 같다」가 다르다는 점이다.**\
`ORDER BY` 없이 던지면 순서는 어느 엔진도 약속하지 않는다.\
[16번](../16-full-outer-join/)에서 `RIGHT JOIN` 의 동률 행이 두 엔진에서 다른 순서로 나왔는데, **그것은 방언 차이가 아니라 순서 무보장**이었다.\
그래서 이 주제의 모든 출력에 `ORDER BY` 를 붙였다.

```text
 "두 엔진 출력이 같다"를 주장하려면
   ORDER BY 를 붙여야 한다
        ↑
 안 붙이면 "같은 집합인데 순서가 달라서 달라 보이는" 것과
 "정말 다른 결과"를 구분할 수 없다
```

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| `LEFT JOIN` 기본 (1·2번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | `OUTER` 생략형까지 |
| 팬아웃 (3번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `dept` 3행 → 4행 |
| `RIGHT` 와 뒤집기 (4번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | `LEFT` 출력과 문자 단위 대조 |
| 반조인 (6번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | `d.id` · `d.name` 양쪽으로 |
| `WHERE` 가 보존을 깨는 것 (7·8·9번) | PG 18.6 · MySQL 8.4.10 | 각 4회 | `ON` 버전까지 나란히 |
| `COUNT(*)` 대 `COUNT(열)` (10번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | |
| 방언 대조 (11번) | PG 18.6 · MySQL 8.4.10 | 각 항목 | **다른 자리 0건** |

**구현 의존 항목** — 없다. 이 주제의 결과는 전부 결과의 정의에서 나온다.\
**단 행 순서는 보장되지 않으므로** 모든 출력에 `ORDER BY` 를 붙였다.

**언어 보장 항목** — 1~10번 전부. 보존 규칙, `NULL` 채우기, `LEFT`/`RIGHT` 대칭은 두 문서가 같은 모양으로 적는다.\
**버전** — `LEFT`·`RIGHT [OUTER] JOIN` 에서 버전에 갈리는 것은 이 주제에 없다. 다음 버전에서도 **11번만 다시 확인하면 된다.**
