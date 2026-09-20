# sql/15-OUTER JOIN 에서 ON 과 WHERE 의 차이 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · Table Expressions (Joined Tables)](https://www.postgresql.org/docs/18/queries-table-expressions.html) · [PostgreSQL 18 · SELECT](https://www.postgresql.org/docs/18/sql-select.html) · [MySQL 8.4 · JOIN Clause](https://dev.mysql.com/doc/refman/8.4/en/join.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력은 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 실행 계획도 실제로 받은 것이고, 지어낸 출력은 없다.\
> **버전** — 이 주제에서 버전에 갈리는 것은 없다. **두 엔진의 결과가 전부 같았다** — 갈린 것은 실행 계획뿐이다.\
> **선행** — [03 WHERE 와 HAVING 의 차이](../03-where-vs-having/)(조건의 자리가 결과를 바꾼다는 감각) · [14 LEFT·RIGHT OUTER JOIN](../14-left-right-outer-join/)(보존 측이 무엇인가).\
> **이 주제는 12~16 묶음의 정점이다** — [13번](../13-inner-join/)에서 「같다」고 배운 두 자리가 여기서 갈린다.

## 한눈에 — 쉽게 말하면

**`ON` 은 「누구와 짝지을까」이고 `WHERE` 는 「누구를 명단에 남길까」다. 내부 조인에서는 결과가 같고, 외부 조인에서는 갈린다.**

- 출석부에 회비 기록을 붙이는 일로 돌아가자([14번](../14-left-right-outer-join/)).
- **`ON` 에 조건을 건다** — "3월 회비 기록만 붙여라."\
  조건에 안 맞는 기록은 **안 붙는다.** 그래도 **출석부의 사람은 그대로 남고** 회비란만 빈칸이 된다.
- **`WHERE` 에 조건을 건다** — "회비란이 3월인 줄만 남겨라."\
  빈칸인 줄은 **3월이 아니므로 통째로 지워진다.** 출석부에서 사람이 사라진다.
- 같은 문장인데 **하나는 빈칸을 만들고 하나는 줄을 지운다.**

```text
        FROM emp e LEFT JOIN dept d ON e.dept_id = d.id [조건]
                          │
                1번 칸: 조인이 여기서 끝난다
                          │
         ┌────────────────┴────────────────┐
         │                                 │
   ON 에 조건을 더함                  WHERE 에 조건을 더함
         │                                 │
 짝짓기 단계에서 탈락                조인이 다 끝난 뒤 탈락
         │                                 │
 보존 측 행은 NULL 로 채워져 남는다     행이 통째로 사라진다
         │                                 │
       4행                               2행
```

이 출석부가 **똑같은 구조로** `ON` 과 `WHERE` 다.\
그리고 **왜 그런지는 [01번](../01-logical-query-processing-order/)의 여덟 칸 그림 하나로 끝난다** — `ON` 은 1번 칸 **안**, `WHERE` 는 2번 칸이다.\
**1번 칸이 「보존 측을 되살리는 일」까지 끝내고 나서** 2번 칸이 시작된다.

> **`ON` 절** — 두 표의 행을 **짝짓는 규칙**. 외부 조인에서는 여기서 탈락해도 보존 측 행이 남는다.\
> 예: `ON e.dept_id = d.id AND d.name = 'sales'` — `cho` 는 짝을 못 지어 `dept` 열이 `NULL` 이 된 채 남는다.

> **`WHERE` 절** — 조인이 **다 끝난 뒤**의 행 필터. 남은 행을 판정해 버린다.\
> 예: `WHERE d.name = 'sales'` — `NULL` 인 행은 `UNKNOWN` 이라 버려진다.

## 이 주제가 답하려는 질문

1. **왜 내부 조인에서는 같고 외부 조인에서는 다른가?** — 처리 순서 하나로 설명된다.
2. **「`LEFT JOIN` 인데 `INNER JOIN` 이 돼 버리는」 대표 실수는 어디서 나는가?**
3. **조건을 어느 쪽에 적을지 무엇으로 판정하나?** — 기준이 한 문장으로 떨어진다.

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
        ^          ^
        |          +-- dan 은 소속이 없다 (dept_id NULL)
        +------------- cho 는 급여가 없다 (salary NULL)
```

**이 주제에서는 `cho` 와 `dan` 둘 다 일을 한다.**\
`ON` 에 조건을 걸면 `cho` 가 짝을 잃고, `WHERE` 에 걸면 `dan` 이 `UNKNOWN` 에 걸려 사라진다.\
[04번](../04-null-three-valued-logic/)에서 `cho` 가 급여 `NULL` 로, [16번](../16-full-outer-join/)에서 `dan` 이 왼쪽-only 행으로 쓰인 그 두 행이다.

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

### 1. ★ 같은 조건을 두 자리에 넣고 나란히 본다

**언제 쓰나** — 외부 조인에 조건을 더 걸 때마다. **이 절 하나가 주제 전부다.**

조인도 같고 조건도 같다. **다른 것은 조건이 적힌 자리뿐이다.**

```text
(A) ON 에 넣는다                              (B) WHERE 에 넣는다
FROM emp e LEFT JOIN dept d                   FROM emp e LEFT JOIN dept d
  ON e.dept_id = d.id                           ON e.dept_id = d.id
 AND d.name = 'sales'                         WHERE d.name = 'sales'
```

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

### SQL: SELECT e.name AS emp, d.name AS dept FROM emp e LEFT JOIN dept d
         ON e.dept_id = d.id WHERE d.name = 'sales' ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | dept                      +-----+-------+
-----+-------                    | emp | dept  |
 ann | sales                     +-----+-------+
 bob | sales                     | ann | sales |
(2 rows)                         | bob | sales |
                                 +-----+-------+
```

```text
      (A) ON — 4행                        (B) WHERE — 2행
   +------+-------+                    +------+-------+
   | ann  | sales |                    | ann  | sales |
   | bob  | sales |                    | bob  | sales |
   | cho  | NULL  |  <- 남았다          +------+-------+
   | dan  | NULL  |  <- 남았다
   +------+-------+                      cho 와 dan 이 사라졌다
   "모든 사원 + 그 중 sales 인            "sales 부서 사원만"
    사람의 부서명"                        = INNER JOIN 과 같은 모양
```

두 그림의 결론 — **`LEFT JOIN` 이라고 적었는데 (B)는 `INNER JOIN` 결과다.**\
대가 — (B)를 쓰고 「모든 사원 목록」이라고 믿으면 사원 둘이 조용히 사라진다. **에러도 경고도 없다.**

★ **이것이 이 주제의 중심 사고다.** 「어디서 틀리나」의 모든 항목이 이 한 대비에서 파생된다.

---

### 2. 왜 그런가 — 01번의 여덟 칸으로 설명된다

**언제 쓰나** — 1번의 결과를 외우는 대신 **재산출**하고 싶을 때.

```text
1. FROM   ┌─────────────────────────────────────────┐
          │ (a) 모든 짝을 만든다        4 x 3 = 12행 │   <- 12번
          │ (b) ON 으로 거른다              3행      │   <- 13번
          │ (c) 보존 측의 짝 못 찾은 행을            │   <- 14번
          │     NULL 로 채워 되살린다       4행      │
          └─────────────────────────────────────────┘
                              ↓
2. WHERE   판정해서 버린다                 ? 행          <- 여기가 15번
                              ↓
3~8. GROUP BY … LIMIT
```

★ **핵심은 `ON` 이 (b)에서 일하고 (c)가 그 **뒤에** 온다는 것이다.**\
`ON` 에서 탈락한 보존 측 행은 **(c)에서 반드시 되살아난다.** 그래서 `ON` 에 무엇을 넣어도 왼쪽 행 수는 안 준다.

```text
(A) ON 에 조건을 더한 경로                (B) WHERE 에 조건을 더한 경로

(a) 12행                                  (a) 12행
(b) ON: dept_id 가 같고 AND name='sales'  (b) ON: dept_id 가 같다
     -> ann-sales, bob-sales  (2행)            -> ann-sales, bob-sales, cho-dev (3행)
(c) 짝 없는 왼쪽을 되살린다                (c) 짝 없는 왼쪽을 되살린다
     -> + cho(NULL), dan(NULL)  (4행)          -> + dan(NULL)  (4행)
                ↓                                       ↓
2. WHERE: 없음                            2. WHERE d.name = 'sales'
                ↓                                cho  -> 'dev' <> 'sales'  FALSE  버림
              4행                                dan  -> NULL = 'sales'  UNKNOWN 버림
                                                        ↓
                                                      2행
```

그림 해설 — **(B)에서 `dan` 을 죽인 것은 `UNKNOWN` 이다.** (c)가 채워 넣은 `NULL` 이 2번 칸의 비교에 들어갔다([04번](../04-null-three-valued-logic/)).\
`cho` 는 `FALSE` 로, `dan` 은 `UNKNOWN` 으로 — **이유는 다른데 처분은 같다.** `WHERE` 는 `TRUE` 만 통과시킨다.\
비용 — 없다. 이건 **의미의 문제**다.

**극단값으로 확인하면 규칙이 더 또렷해진다.** `ON FALSE` 는 아무 짝도 못 짓게 하는데, 그래도 4행이 나온다.

```text
### SQL: SELECT e.name AS emp, d.name AS dept FROM emp e LEFT JOIN dept d ON FALSE ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | dept                      +-----+------+
-----+------                     | emp | dept |
 ann | NULL                      +-----+------+
 bob | NULL                      | ann | NULL |
 cho | NULL                      | bob | NULL |
 dan | NULL                      | cho | NULL |
(4 rows)                         | dan | NULL |
                                 +-----+------+
```

**`ON` 은 보존 측 행을 지울 수 없다.** 짝을 못 짓게 할 수 있을 뿐이다. 이것이 규칙의 전부다.\
같은 `FALSE` 를 `WHERE` 에 두면 **0행**이 된다 — `WHERE` 에는 그 제약이 없다.

```text
### SQL: SELECT e.name AS emp, d.name AS dept FROM emp e LEFT JOIN dept d ON e.dept_id = d.id WHERE FALSE;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | dept                      (빈 결과 — 출력이 한 줄도 없다)
-----+------
(0 rows)
```

---

### 3. 왜 내부 조인에서는 같았나

**언제 쓰나** — [13번](../13-inner-join/)에서 「같다」고 배운 것과 여기가 충돌하는 것 같을 때.

```text
INNER JOIN 의 1번 칸                    OUTER JOIN 의 1번 칸
(a) 모든 짝                             (a) 모든 짝
(b) ON 으로 거른다                      (b) ON 으로 거른다
    (c) 가 없다                         (c) 짝 못 찾은 보존 측을 되살린다
         ↓                                       ↓
 ON 에서 탈락 = 행이 없다                ON 에서 탈락 = NULL 로 채워져 남는다
 WHERE 에서 탈락 = 행이 없다             WHERE 에서 탈락 = 행이 없다
         ↓                                       ↓
     도착지가 같다                           도착지가 다르다
```

★ **(c) 단계가 있느냐 없느냐 하나다.** `INNER JOIN` 에는 되살리는 단계가 없으니 두 경로의 도착지가 같다.

같은 조건을 내부 조인의 두 자리에 넣으면 실제로 같다.

```text
### SQL: SELECT e.name AS emp, d.name AS dept FROM emp e JOIN dept d
         ON e.dept_id = d.id AND d.name = 'sales' ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | dept                      +-----+-------+
-----+-------                    | emp | dept  |
 ann | sales                     +-----+-------+
 bob | sales                     | ann | sales |
(2 rows)                         | bob | sales |
                                 +-----+-------+

### SQL: SELECT e.name AS emp, d.name AS dept FROM emp e JOIN dept d
         ON e.dept_id = d.id WHERE d.name = 'sales' ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | dept                      +-----+-------+
-----+-------                    | emp | dept  |
 ann | sales                     +-----+-------+
 bob | sales                     | ann | sales |
(2 rows)                         | bob | sales |
                                 +-----+-------+
```

**같은 2행이다.** 그리고 1번 절의 `LEFT JOIN + WHERE` 도 2행이었다 — **세 질의가 같은 답을 낸다.**\
비용 — 없다. 하지만 **`INNER` 에서 든 습관이 `LEFT` 로 바꾸는 순간 사고가 된다.**\
「지금 잘 나오는데요」로 넘어간 `WHERE` 조건이 조인 형태를 바꿀 때 터진다.

---

### 4. 조건이 **보존 측 열**에 걸리면 — 또 다른 결과가 나온다

**언제 쓰나** — 1번과 반대 방향. 조건의 대상이 왼쪽(보존 측) 열일 때. **여기도 갈리고, 갈리는 모양이 다르다.**

```text
(A) ON 에 넣는다                              (B) WHERE 에 넣는다
FROM emp e LEFT JOIN dept d                   FROM emp e LEFT JOIN dept d
  ON e.dept_id = d.id                           ON e.dept_id = d.id
 AND e.salary >= 400                          WHERE e.salary >= 400
```

```text
### SQL: SELECT e.name AS emp, d.name AS dept FROM emp e LEFT JOIN dept d
         ON e.dept_id = d.id AND e.salary >= 400 ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | dept                      +-----+-------+
-----+-------                    | emp | dept  |
 ann | NULL                      +-----+-------+
 bob | sales                     | ann | NULL  |
 cho | NULL                      | bob | sales |
 dan | NULL                      | cho | NULL  |
(4 rows)                         | dan | NULL  |
                                 +-----+-------+

### SQL: SELECT e.name AS emp, d.name AS dept FROM emp e LEFT JOIN dept d
         ON e.dept_id = d.id WHERE e.salary >= 400 ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | dept                      +-----+-------+
-----+-------                    | emp | dept  |
 bob | sales                     +-----+-------+
 dan | NULL                      | bob | sales |
(2 rows)                         | dan | NULL  |
                                 +-----+-------+
```

```text
    (A) ON — 4행                          (B) WHERE — 2행
 ann | NULL    <- 급여 300 이라 짝이 안 붙었다   bob | sales
 bob | sales                                   dan | NULL   <- 남았다!
 cho | NULL
 dan | NULL                                   ann·cho 는 급여 조건에서 탈락
```

두 그림의 결론 — **(A)는 `ann` 을 「부서 없는 사람」으로 만들었다.** 급여가 300이라 짝짓기에서 떨어졌을 뿐인데 부서명이 `NULL` 이 됐다.\
**(B)는 `dan` 을 남겼다.** 조건이 왼쪽 열(`e.salary`)에 걸렸으므로 조인이 만든 `NULL` 과 무관하다 — `dan` 의 급여 400 은 실제 값이다.\
대가 — **(A)는 거의 항상 실수다.** 보존 측 열 조건을 `ON` 에 넣으면 「거르기」가 아니라 「짝 못 짓게 하기」가 된다.

★ **규칙이 하나 더 나온다.**

| 조건이 걸린 열 | `ON` 에 두면 | `WHERE` 에 두면 |
|---|---|---|
| **상대 측**(`d.*`) | 짝만 안 붙는다. 보존 측 행은 남는다 — **대개 이게 의도다** | 행이 사라진다 — **외부 조인이 무너진다** |
| **보존 측**(`e.*`) | 짝만 안 붙는다 — **대개 의도가 아니다** | 행이 사라진다 — **대개 이게 의도다** |

**즉 「`ON` 이 항상 맞다」도 「`WHERE` 가 항상 맞다」도 아니다.** 조건의 대상이 어느 쪽 열인지가 먼저다.

---

### 5. `RIGHT JOIN` 에서도 똑같다 — 보존 측만 바뀐다

**언제 쓰나** — 규칙이 `LEFT` 전용이 아님을 확인할 때.

```text
### SQL: SELECT e.name AS emp, d.name AS dept FROM emp e RIGHT JOIN dept d
         ON e.dept_id = d.id AND e.salary >= 400 ORDER BY d.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp  | dept                     +------+-------+
------+-------                   | emp  | dept  |
 bob  | sales                    +------+-------+
 NULL | dev                      | bob  | sales |
 NULL | hr                       | NULL | dev   |
(3 rows)                         | NULL | hr    |
                                 +------+-------+

### SQL: SELECT e.name AS emp, d.name AS dept FROM emp e RIGHT JOIN dept d
         ON e.dept_id = d.id WHERE e.salary >= 400 ORDER BY d.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | dept                      +------+-------+
-----+-------                    | emp  | dept  |
 bob | sales                     +------+-------+
(1 row)                          | bob  | sales |
                                 +------+-------+
```

그림 해설 — `RIGHT` 의 보존 측은 `dept` 다. **`ON` 버전은 부서 3개가 다 남았고**(3행), `WHERE` 버전은 1행이 됐다.\
`ann`(300)이 짝짓기에서 떨어지면서 `sales` 의 짝이 `bob` 하나가 됐고, `dev`·`hr` 은 짝이 없어 `NULL` 로 남았다.\
대가 — 규칙은 같다. **보존 측이 어느 쪽인지만 바뀐다.**

`FULL OUTER JOIN` 에서도 같다 — [16번](../16-full-outer-join/)에서 `WHERE d.name = 'sales'` 가 5행을 2행으로 무너뜨렸다.\
**양쪽이 보존 측이므로 양쪽이 다 무너진다.**

---

### 6. 옵티마이저는 이 차이를 알고 있다

**언제 쓰나** — 「`WHERE` 로 써도 엔진이 알아서 해 주겠지」를 의심할 때. **정반대다 — 엔진은 내 뜻대로 정확히 무너뜨린다.**

1번의 두 질의를 `EXPLAIN` 에 건다.

```text
### SQL: EXPLAIN SELECT e.name, d.name FROM emp e LEFT JOIN dept d ON e.dept_id = d.id AND d.name = 'sales';
--- PG 18.6 ---
 Hash Left Join  (cost=8.18..32.46 rows=1130 width=64)
   Hash Cond: (e.dept_id = d.id)
   ->  Seq Scan on emp e  (cost=0.00..21.30 rows=1130 width=36)
   ->  Hash  (cost=8.17..8.17 rows=1 width=36)
         ->  Index Scan using dept_name_key on dept d  (cost=0.15..8.17 rows=1 width=36)
               Index Cond: (name = 'sales'::text)

### SQL: EXPLAIN SELECT e.name, d.name FROM emp e LEFT JOIN dept d ON e.dept_id = d.id WHERE d.name = 'sales';
--- PG 18.6 ---
 Hash Join  (cost=8.18..32.46 rows=1 width=64)
   Hash Cond: (e.dept_id = d.id)
   ->  Seq Scan on emp e  (cost=0.00..21.30 rows=1130 width=36)
   ->  Hash  (cost=8.17..8.17 rows=1 width=36)
         ->  Index Scan using dept_name_key on dept d  (cost=0.15..8.17 rows=1 width=36)
               Index Cond: (name = 'sales'::text)
```

★ **맨 윗줄이 `Hash Left Join` 에서 `Hash Join` 으로 바뀌었다.**\
**PG 가 `LEFT JOIN` 을 `INNER JOIN` 으로 바꿔 버렸다.** 내가 `LEFT` 라고 적었는데도.

MySQL 은 더 나간다.

```text
### SQL: EXPLAIN FORMAT=TREE SELECT e.name, d.name FROM emp e LEFT JOIN dept d
         ON e.dept_id = d.id AND d.name = 'sales';
--- MySQL 8.4.10 ---  (출력의 표 테두리는 지웠다 — 폭이 200자를 넘는다)
-> Nested loop left join  (cost=2.05 rows=4)
    -> Table scan on e  (cost=0.65 rows=4)
    -> Filter: (d.`name` = 'sales')  (cost=0.275 rows=1)
        -> Single-row index lookup on d using PRIMARY (id=e.dept_id)  (cost=0.275 rows=1)

### SQL: EXPLAIN FORMAT=TREE SELECT e.name, d.name FROM emp e LEFT JOIN dept d
         ON e.dept_id = d.id WHERE d.name = 'sales';
--- MySQL 8.4.10 ---
-> Filter: (e.dept_id = '10')  (cost=0.65 rows=1)
    -> Table scan on e  (cost=0.65 rows=4)
```

**`WHERE` 버전에서 `dept` 표가 계획에서 통째로 사라졌다.**\
"`d.name` 이 `'sales'` 여야 하고, 그런 부서는 `id=10` 하나뿐이고, `NULL` 행은 어차피 다 떨어진다" — 그래서 **조인 자체를 없앴다.**

| | `ON` 버전 | `WHERE` 버전 |
|---|---|---|
| PG 18.6 | `Hash Left Join` | **`Hash Join`** — 외부 조인이 내부 조인이 됐다 |
| MySQL 8.4.10 | `Nested loop left join` | **조인 없음** — `dept` 가 계획에서 사라졌다 |

두 그림의 결론 — **「외부 조인이 내부 조인으로 무너진다」는 비유가 아니다.** 옵티마이저가 실제로 그렇게 다시 쓴다.\
대가 — **엔진은 내 실수를 고쳐 주지 않는다.** 내가 적은 것의 *뜻*을 정확히 이행하고, 그 뜻은 이미 내부 조인이었다.

> **읽을 때 주의** — 위 PG 계획의 `rows=1130` 같은 추정치는 통계가 없어서 나온 기본값이다.\
> 이 표들은 `ANALYZE` 를 돌린 적이 없다. **여기서 볼 것은 행 수 추정이 아니라 노드 이름**이다.\
> 계획을 읽는 법은 목록의 **58번 주제**, 추정과 실측의 어긋남은 **60번 주제**가 정본이다.

---

### 7. 고치는 법 셋

**언제 쓰나** — 1번의 (B)처럼 무너진 질의를 손에 들었을 때.

```text
무엇을 원했나?
    │
    ├─ "보존 측을 다 남기고, 조건에 맞는 것만 붙이고 싶다"
    │       -> (A) 조건을 ON 으로 옮긴다                    <- 가장 흔한 의도
    │
    ├─ "보존 측을 다 남기되 조건은 결과에 걸고 싶다"
    │       -> (B) WHERE 에 OR 상대측키 IS NULL 을 더한다
    │
    └─ "사실 짝이 있는 행만 필요했다"
            -> (C) 그냥 INNER JOIN 이라고 적는다            <- 뜻을 드러낸다
```

```text
(A) ### SQL: SELECT e.name AS emp, d.name AS dept FROM emp e LEFT JOIN dept d
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

(B) ### SQL: SELECT e.name AS emp, d.name AS dept FROM emp e LEFT JOIN dept d ON e.dept_id = d.id
             WHERE d.name = 'sales' OR d.id IS NULL ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | dept                      +-----+-------+
-----+-------                    | emp | dept  |
 ann | sales                     +-----+-------+
 bob | sales                     | ann | sales |
 dan | NULL                      | bob | sales |
(3 rows)                         | dan | NULL  |
                                 +-----+-------+
```

그림 해설 — **(A)와 (B)는 다른 답이다.** (A)는 4행, (B)는 3행 — `cho` 가 (B)에서 빠진다.\
(A)는 「`cho` 를 남기되 `sales` 가 아니니 부서란을 비운다」, (B)는 「`cho` 는 부서가 있고 `sales` 가 아니니 뺀다」.\
**둘 중 무엇이 맞는지는 요구사항이 정한다.** 문법이 정해 주지 않는다.\
대가 — (B)의 `IS NULL` 은 **`NULL` 일 수 없는 열**(기본키)에 걸어야 한다. `d.name IS NULL` 로 쓰면 원본 `NULL` 과 섞인다([14번](../14-left-right-outer-join/)).

**반조인 패턴은 (B)의 특수형이다** — `WHERE 상대측키 IS NULL` 만 남기면 「짝이 없는 것만」이 된다.

```text
### SQL: SELECT e.name AS emp, d.name AS dept FROM emp e LEFT JOIN dept d
         ON e.dept_id = d.id AND e.salary >= 400 WHERE d.id IS NULL ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | dept                      +-----+------+
-----+------                     | emp | dept |
 ann | NULL                      +-----+------+
 cho | NULL                      | ann | NULL |
 dan | NULL                      | cho | NULL |
(3 rows)                         | dan | NULL |
                                 +-----+------+
```

`ON` 의 조건과 `WHERE` 의 `IS NULL` 을 **같이 쓰는 것**이 「조건에 맞는 짝이 없는 행」을 뽑는 표준형이다.\
여기서는 「급여 400 이상이면서 부서가 있는」 조건을 못 채운 셋(`ann`·`cho`·`dan`)이 나왔다.

## 문법 — 어느 절에서 무엇이 보이나

```sql
FROM 왼쪽표 LEFT JOIN 오른쪽표
  ON <짝짓는 규칙>            -- 1번 칸 안. 보존 측 행을 지울 수 없다
WHERE <결과 필터>              -- 2번 칸. 조인이 다 끝난 뒤. 무엇이든 지울 수 있다
```

규칙 여섯.

1. **`ON` 은 보존 측 행을 지울 수 없다.** 짝을 못 짓게 할 뿐이다. `ON FALSE` 도 4행을 준다.
2. **`WHERE` 는 무엇이든 지운다.** 조인이 만든 `NULL` 행도 예외가 아니다.
3. **내부 조인에서는 두 자리가 같다** — 되살리는 단계가 없어 도착지가 같기 때문이다([13번](../13-inner-join/)).
4. **상대 측 열 조건을 `WHERE` 에 두면 외부 조인이 내부 조인으로 무너진다.** 옵티마이저가 실제로 그렇게 다시 쓴다.
5. **보존 측 열 조건을 `ON` 에 두면 「거르기」가 아니라 「짝 못 짓게 하기」가 된다.** 대개 실수다.
6. **`IS NULL` 로 되살릴 때는 `NULL` 일 수 없는 열**(기본키)에 건다.

판정 기준이 한 문장으로 떨어진다.

```text
이 조건이 "붙이는 규칙"인가, "결과에 남길지의 규칙"인가?
        │                              │
    붙이는 규칙                    결과 필터
        ↓                              ↓
       ON                            WHERE

바꿔 물으면 — "조건에 안 맞는 보존 측 행을 결과에서 보고 싶은가?"
        보고 싶다 -> ON          안 보고 싶다 -> WHERE
```

## 어디서 틀리나

★ **이 절이 이 주제의 본체다.** 위의 모든 그림이 여기 한 줄씩으로 요약된다.

- **★ 「`LEFT JOIN` 인데 `INNER JOIN` 이 돼 버린다」 — 상대 측 열 조건을 `WHERE` 에 둔다.**\
  가장 흔하고 가장 조용하다. 4행이 2행이 됐다. **어디서 틀리나: `WHERE d.name = 'sales'` 의 `d.` 가 상대 측이다.**\
  조건에 상대 측 별칭이 보이면 **`ON` 으로 옮길지 먼저 묻는다.**
- **★ 상대 측 열에 `<>`·`NOT IN` 을 `WHERE` 에 둔다.**\
  등호보다 더 조용하다. 「아닌 것을 고른다」인데 **`NULL` 행은 `UNKNOWN` 이라 「아닌 것」에도 안 들어간다**([14번](../14-left-right-outer-join/)).\
  `OR 상대측키 IS NULL` 을 같이 쓴다.
- **★ `INNER JOIN` 으로 쓰다가 `LEFT JOIN` 으로 바꾼다.**\
  조인 형태만 바꾸고 `WHERE` 는 그대로 두면 **바뀐 게 없다.** 바꾸기 전에 `WHERE` 의 상대 측 조건을 전부 `ON` 으로 옮긴다.
- **보존 측 열 조건을 `ON` 에 둔다.**\
  `ON … AND e.salary >= 400` 은 `ann` 을 「부서 없는 사람」으로 만들었다. 거르려던 것이면 `WHERE` 가 맞다.
- **`ON` 과 `WHERE` 중 무엇이 「항상 맞다」를 외우려 한다.**\
  둘 다 아니다. **조건의 대상이 보존 측인지 상대 측인지가 먼저**다(4번의 표).
- **`IS NULL` 을 `NULL` 가능한 열에 건다.**\
  `WHERE d.name IS NULL` 은 「짝이 없다」와 「이름이 원래 `NULL` 이다」를 섞는다. 기본키를 본다.
- **결과가 맞는지 행 수로 확인하지 않는다.**\
  이 사고는 **에러를 안 낸다.** 보존 측 행 수와 결과 행 수를 비교하는 것이 유일한 방어선이다.
- **`ORDER BY` 없이 두 엔진 출력을 비교한다.**\
  행 순서는 보장되지 않는다. **집합은 같은데 순서가 달라서 다르게 보이는 것**과 진짜 차이를 구분할 수 없다.

## 구현 세부사항 대 언어 보장

| | 무엇인가 | 누가 보장하나 |
|---|---|---|
| `ON` 이 1번 칸 안, `WHERE` 가 2번 칸 | **결과의 정의** | 언어 — 두 엔진 결과가 전부 같았다 |
| `ON` 이 보존 측 행을 못 지운다 | **결과의 정의** | 언어 — `ON FALSE` 도 4행 |
| `WHERE` 가 `UNKNOWN` 행을 버린다 | **결과의 정의** | 언어([04번](../04-null-three-valued-logic/)) |
| 옵티마이저가 `Left Join` 을 `Join` 으로 다시 쓴다 | 구현 세부 | 결과가 같을 때만 허용된다 — **결과가 바뀐 게 아니라 이미 그런 뜻이었다** |
| MySQL 이 `dept` 표를 계획에서 없앤다 | 구현 세부 | 통계·인덱스에 달렸다 |
| 결과 **행 순서** | 아무도 보장 안 함 | `ORDER BY` 없이는 약속이 없다 |

★ **이 주제에서 구현 세부가 하는 일은 「증거 제공」뿐이다.**\
계획이 `Hash Join` 으로 바뀌는 것은 **결과가 그렇게 정의되어 있다는 증거**이지, 계획이 결과를 바꾼 것이 아니다.\
옵티마이저를 꺼도 답은 2행이다.

**이 주제는 두 엔진에서 결과가 한 번도 안 갈렸다.** 조건의 자리 규칙은 방언이 아니라 언어의 뼈대다.

## 언제 쓰고 언제 안 쓰나

- **`ON` 에 둔다 — 「붙이는 규칙」일 때.** 「3월 실적만 붙여라」·「활성 상태인 주소만 붙여라」.\
  보존 측 행은 다 남고, 안 맞는 것은 `NULL` 로 보인다.
- **`WHERE` 에 둔다 — 「결과에서 빼라」일 때.** 보존 측 열 조건은 거의 항상 이쪽이다.
- **`WHERE` 에 두되 `OR 키 IS NULL` 을 붙인다 — 「빼되 짝 없는 행은 남겨라」일 때.**
- **`INNER JOIN` 이라고 적는다 — 사실 짝 있는 것만 필요할 때.**\
  `LEFT JOIN` + `WHERE` 로 같은 답을 내지 말고 **뜻을 드러낸다.** 읽는 사람도 옵티마이저도 이쪽이 낫다.
- **조인 형태를 바꿀 때는 조건 자리를 다시 본다.** `INNER` → `LEFT` 로 바꾸는 순간 `WHERE` 의 뜻이 달라진다.

## 핵심 문장

- **`ON` 은 짝짓는 규칙, `WHERE` 는 결과 필터다.** `ON` 은 1번 칸 안, `WHERE` 는 2번 칸이다.
- 1번 칸은 **(a) 모든 짝 → (b) `ON` 으로 거름 → (c) 보존 측 되살림** 순으로 끝난다.\
  **`ON` 에서 탈락한 보존 측 행은 (c)에서 반드시 되살아난다** — 그래서 `ON FALSE` 도 4행이다.
- **내부 조인에는 (c)가 없다.** 그래서 [13번](../13-inner-join/)에서는 두 자리가 같았다.
- ★ **상대 측 열 조건을 `WHERE` 에 두면 외부 조인이 내부 조인으로 무너진다** — 4행이 2행이 됐다.\
  **어디서 틀리나: 조건에 `d.` 가 보이는데 `WHERE` 에 있으면 의심한다.**
- **보존 측 열 조건을 `ON` 에 두면 「짝 못 짓게 하기」가 된다** — `ann` 이 부서 없는 사람이 됐다. 대개 실수다.
- **옵티마이저가 실제로 `Hash Left Join` 을 `Hash Join` 으로 다시 쓴다.** MySQL 은 표를 아예 없앴다.\
  **엔진이 실수를 고쳐 주는 게 아니라, 내가 적은 뜻이 이미 내부 조인이었다.**
- 고치는 법 셋 — **`ON` 으로 옮기기 / `OR 키 IS NULL` 더하기 / `INNER JOIN` 이라고 적기.** 셋은 **다른 답**을 낸다.

## 관련 자료

- [PostgreSQL 18 · Table Expressions](https://www.postgresql.org/docs/18/queries-table-expressions.html) — `ON` 이 `FROM` 단계에 속한다는 것이 조인 정의에 있다.
- [MySQL 8.4 · JOIN Clause](https://dev.mysql.com/doc/refman/8.4/en/join.html)
- [01 논리적 질의 처리 순서](../01-logical-query-processing-order/) — **경계: 그쪽은 여덟 칸의 순서까지, 여기는 1번 칸 내부의 세 단계부터.**
- [03 WHERE 와 HAVING 의 차이](../03-where-vs-having/) — **같은 「조건을 어디 두나」 문제의 집계판**이다. 그쪽은 `GROUP BY` 가 사이에 끼고, 여기는 「되살리기」가 사이에 낀다.
- [13 INNER JOIN](../13-inner-join/) — **경계: 그쪽은 두 자리가 같다는 것까지, 여기는 왜 같았고 언제 갈리나부터.**
- [14 LEFT·RIGHT OUTER JOIN](../14-left-right-outer-join/) — **경계: 그쪽은 보존 측과 `NULL` 채우기까지, 여기는 조건의 자리 규칙부터.**
- [16 FULL OUTER JOIN](../16-full-outer-join/) — 양쪽이 보존 측이라 양쪽이 무너진다. 5행이 2행이 되는 예가 있다.
- [04 NULL 의 3값 논리](../04-null-three-valued-logic/) — `WHERE` 가 `UNKNOWN` 행을 버리는 규칙.
- **`EXISTS`/`NOT EXISTS`** 는 목록의 **19번 주제**, **계획 읽기**는 **58번 주제**가 정본이다.
- [SQL 주제 목록](../README.md)

## 용어 풀이

- **`ON` 절** — 두 표의 행을 짝짓는 규칙. `FROM`(1번 칸) 안에서 판정된다.\
  예: `ON e.dept_id = d.id AND d.name = 'sales'` — `cho` 는 짝을 못 지어 `NULL` 로 남는다.
- **`WHERE` 절** — 조인이 다 끝난 뒤의 행 필터. 2번 칸이다.\
  예: `WHERE d.name = 'sales'` — `NULL` 행은 `UNKNOWN` 이라 버려진다.
- **보존 측(preserved side)** — 「한 행도 안 버린다」고 약속된 쪽. `ON` 은 이 약속을 지키고 `WHERE` 는 안 지킨다.\
  예: `emp LEFT JOIN dept` 의 보존 측은 `emp`.
- **상대 측(null-supplying side)** — 짝이 없으면 `NULL` 로 채워지는 쪽.\
  예: `emp LEFT JOIN dept` 의 `dept`. **여기 열에 건 조건을 `WHERE` 에 두면 무너진다.**
- **외부 조인이 무너진다(join collapse)** — `WHERE` 때문에 `LEFT JOIN` 이 `INNER JOIN` 과 같아지는 것.\
  예: 4행이 2행이 되고, 계획이 `Hash Left Join` 에서 `Hash Join` 으로 바뀐다.
- **`UNKNOWN`** — `TRUE`/`FALSE` 가 아닌 세 번째 진릿값.\
  예: `NULL = 'sales'`. `WHERE` 는 이것을 `FALSE` 와 똑같이 버린다.
- **반조인(anti join)** — 「짝이 없는 행만」 뽑는 형태. `ON` 조건 + `WHERE 키 IS NULL`.\
  예: `ON … AND e.salary >= 400 WHERE d.id IS NULL` 은 그 조건의 짝이 없는 셋을 준다.
- **`Hash Left Join` / `Hash Join`** — PG 계획에 뜨는 노드 이름. 앞은 외부 조인, 뒤는 내부 조인이다.\
  예: `WHERE` 를 붙인 순간 앞이 뒤로 바뀐다 — 옵티마이저가 무너짐을 알아본 증거다.
- **조건 내리기(predicate pushdown)** — 옵티마이저가 조건을 더 이른 단계로 옮기는 최적화.\
  예: MySQL 이 `d.name='sales'` 를 `e.dept_id='10'` 으로 바꿔 `dept` 표를 없앴다.
