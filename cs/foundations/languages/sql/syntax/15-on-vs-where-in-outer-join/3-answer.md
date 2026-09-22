# sql/15-OUTER JOIN 에서 ON 과 WHERE 의 차이 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력은 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 실행 계획도 실제로 받은 것이고, 지어낸 출력은 없다.\
> 문서 근거는 [PG 18 Table Expressions](https://www.postgresql.org/docs/18/queries-table-expressions.html) · [MySQL 8.4 JOIN Clause](https://dev.mysql.com/doc/refman/8.4/en/join.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. ★ (A) `ON` 과 (B) `WHERE` 의 결과 행 수

**(A)는 4행, (B)는 2행이다.**

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

★ **조인도 같고 조건도 같다. 다른 것은 조건이 적힌 자리뿐인데 답이 2배 차이가 난다.**\
그리고 (B)는 `LEFT JOIN` 이라고 적었는데 **`INNER JOIN` 결과**다.

```text
### SQL: SELECT COUNT(*) AS n FROM emp e LEFT JOIN dept d ON e.dept_id = d.id AND d.name = 'sales';
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 n                               +---+
---                              | n |
 4                               +---+
(1 row)                          | 4 |
                                 +---+

### SQL: SELECT COUNT(*) AS n FROM emp e LEFT JOIN dept d ON e.dept_id = d.id WHERE d.name = 'sales';
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 n                               +---+
---                              | n |
 2                               +---+
(1 row)                          | 2 |
                                 +---+
```

---

### 2. 왜 갈리나 — 처리 순서로

**`ON` 은 1번 칸 **안**에서, `WHERE` 는 2번 칸에서 일한다. 그리고 1번 칸은 「되살리기」까지 끝내고 나서 끝난다.**

```text
1. FROM   ┌─────────────────────────────────────────┐
          │ (a) 모든 짝을 만든다        4 x 3 = 12행 │   <- 12번
          │ (b) ON 으로 거른다                       │   <- 13번
          │ (c) 보존 측의 짝 못 찾은 행을            │   <- 14번
          │     NULL 로 채워 되살린다                │
          └─────────────────────────────────────────┘
                              ↓
2. WHERE   판정해서 버린다                                <- 여기가 이 주제
                              ↓
3~8. GROUP BY … LIMIT
```

**(A)와 (B)가 같은 칸들을 다른 값으로 통과한다.**

```text
(A) ON 에 조건을 더한 경로                (B) WHERE 에 조건을 더한 경로

(a) 12행                                  (a) 12행
(b) ON: dept_id 가 같고 AND name='sales'  (b) ON: dept_id 가 같다
     -> ann-sales, bob-sales      2행          -> ann-sales, bob-sales, cho-dev  3행
(c) 짝 없는 왼쪽을 되살린다                (c) 짝 없는 왼쪽을 되살린다
     -> + cho(NULL) + dan(NULL)   4행          -> + dan(NULL)                    4행
                ↓                                       ↓
2. WHERE 없음                             2. WHERE d.name = 'sales'
                ↓                                cho -> 'dev' <> 'sales'   FALSE   버림
              4행                                dan -> NULL = 'sales'     UNKNOWN 버림
                                                        ↓
                                                      2행
```

★ **결정적인 것은 (b) 다음에 (c)가 온다는 것이다.**\
`ON` 에서 탈락한 보존 측 행은 **(c)에서 반드시 되살아난다.** 그래서 `ON` 은 왼쪽 행 수를 줄일 수 없다.\
`WHERE` 는 (c)가 다 끝난 **뒤에** 오므로, 되살아난 행을 다시 지울 수 있다.

```text
 ON 이 할 수 있는 것              WHERE 가 할 수 있는 것
 "짝을 안 붙인다"                 "행을 지운다"
        ↓                                ↓
 결과 행 수는 그대로               결과 행 수가 준다
 오른쪽 열이 NULL 이 된다
```

---

### 3. `ON FALSE` 의 결과 행 수

**4행이다. 전부 `NULL` 과 함께.**

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

**왜 이 실험이 중요한가** — `ON` 이 할 수 있는 **최대한의 탈락**을 시킨 것인데도 보존 측 4행이 그대로다.

```text
(a) 12행
(b) ON FALSE  -> 통과하는 짝 0개
(c) 짝 없는 왼쪽 4행을 전부 되살린다  -> 4행
```

★ **`ON` 은 보존 측 행을 지울 수 없다. 이것이 규칙의 전부다.**\
같은 `FALSE` 를 `WHERE` 에 두면 0행이 된다 — `WHERE` 에는 그런 제약이 없다.

```text
### SQL: SELECT e.name AS emp, d.name AS dept FROM emp e LEFT JOIN dept d ON e.dept_id = d.id WHERE FALSE;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | dept                      (빈 결과 — 출력이 한 줄도 없다)
-----+------
(0 rows)
```

참고로 `WHERE TRUE` 는 아무것도 안 바꾼다.

```text
### SQL: SELECT e.name AS emp, d.name AS dept FROM emp e LEFT JOIN dept d ON e.dept_id = d.id
         WHERE TRUE ORDER BY e.id;
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

**`WHERE` 가 위험한 것은 `WHERE` 자체가 아니라 거기 적힌 조건이 `NULL` 행을 통과시키지 못하기 때문이다.**

---

### 4. (B)에서 `dan` 이 사라진 이유

**`UNKNOWN` 이다.**

```text
LEFT JOIN 이 만든 4행이 WHERE d.name = 'sales' 를 지난다

 emp | d.name |  d.name = 'sales'  | WHERE 의 처분
-----+--------+--------------------+---------------
 ann | sales  | TRUE               | 통과
 bob | sales  | TRUE               | 통과
 cho | dev    | FALSE              | 버림
 dan | NULL   | UNKNOWN            | 버림   <- 조인이 만든 NULL
```

★ **`cho` 와 `dan` 은 탈락 이유가 다른데 처분이 같다.**

| | 왜 탈락했나 | 진릿값 |
|---|---|---|
| `cho` | 부서가 `dev` 라 조건에 안 맞는다 | `FALSE` |
| `dan` | 부서가 없어서 **판정 자체가 안 된다** | `UNKNOWN` |

`WHERE` 는 **`TRUE` 만 통과**시키므로 둘을 구분하지 않는다([04번](../04-null-three-valued-logic/)).

★ **`dan` 의 `d.name` 은 원본에 없던 `NULL` 이다.** `dept.name` 은 `NOT NULL` 인데도 조인 결과에는 `NULL` 이 생겼다.\
**즉 스키마에 `NULL` 을 하나도 허용하지 않아도 외부 조인을 쓰는 순간 3값 논리가 돌아온다.**

> **`UNKNOWN`** — `TRUE`/`FALSE` 가 아닌 세 번째 진릿값.\
> 예: `NULL = 'sales'`. "모르는 값이 `'sales'` 인가?"는 답할 수 없다.

---

### 5. 내부 조인에서는 왜 같았나

**되살리는 단계 (c)가 없기 때문이다.**

```text
INNER JOIN 의 1번 칸                    OUTER JOIN 의 1번 칸
(a) 모든 짝                             (a) 모든 짝
(b) ON 으로 거른다                      (b) ON 으로 거른다
     (c) 가 없다                        (c) 짝 못 찾은 보존 측을 되살린다
         ↓                                       ↓
 ON 에서 탈락 = 행이 없다                ON 에서 탈락 = NULL 로 채워져 남는다
 WHERE 에서 탈락 = 행이 없다             WHERE 에서 탈락 = 행이 없다
         ↓                                       ↓
     도착지가 같다                           도착지가 다르다
```

실제로 던져 보면 내부 조인의 두 자리는 같은 2행을 준다.

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

★ **세 질의가 같은 2행을 낸다** — 내부 조인의 `ON`, 내부 조인의 `WHERE`, 그리고 1번의 `LEFT JOIN + WHERE`.\
**바로 그것이 사고의 구조다.** `INNER` 로 개발하며 `WHERE` 에 조건을 쌓는 습관이 들고, 나중에 `LEFT` 로 바꾸는 순간 **바뀐 게 없다.**

```text
 질의를 LEFT JOIN 으로 바꿨다
        ↓
 WHERE 의 상대 측 조건을 안 옮겼다
        ↓
 결과가 그대로다 — "바꿨는데 왜 그대로지?"가 아니라
 "바뀐 줄 알았는데 안 바뀌었다"를 모른 채 넘어간다
```

---

### 6. 조건이 보존 측 열에 걸리면

**(A) `ON` 은 4행, (B) `WHERE` 는 2행. 이번에는 (B)가 의도일 가능성이 높다.**

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
    (A) ON — 4행                             (B) WHERE — 2행
 ann | NULL   <- 급여 300 이라 짝이 안 붙었다   bob | sales
 bob | sales                                  dan | NULL   <- 남았다!
 cho | NULL   <- 급여 NULL 이라 UNKNOWN
 dan | NULL
                                              ann(300)·cho(NULL) 이 탈락
```

**(A)가 한 일** — `ann` 은 부서가 분명히 `sales` 인데 **부서명이 `NULL` 로 나왔다.**\
급여 조건이 **짝짓기 규칙**에 들어가서 "급여 400 미만인 사람은 부서와 짝짓지 마라"가 됐기 때문이다.\
**이건 거의 항상 실수다.** 급여로 **거르려던 것**이지 부서를 지우려던 게 아니다.

**(B)가 한 일** — `dan` 이 **남았다.** 조건이 왼쪽 열(`e.salary`)에 걸렸고 `dan` 의 급여 400 은 **실제 값**이라 `TRUE` 다.\
조인이 만든 `NULL` 과 무관하므로 외부 조인이 무너지지 않는다.

★ **여기서 배울 것 — 「`ON` 이 항상 맞다」가 아니다.** 4번(=문항 7)의 판정표가 필요한 이유다.

---

### 7. 네 칸 판정표

| 조건이 걸린 열 | `ON` 에 두면 | `WHERE` 에 두면 |
|---|---|---|
| **상대 측**(`d.*`) | 짝만 안 붙는다. 보존 측 행은 `NULL` 과 함께 남는다 — **대개 이게 의도다** | 행이 사라진다 — **외부 조인이 무너진다** |
| **보존 측**(`e.*`) | 짝만 안 붙는다. 조건에 안 맞는 행의 상대 측이 `NULL` 이 된다 — **대개 의도가 아니다** | 행이 사라진다 — **대개 이게 의도다** |

```text
                     ON                    WHERE
              ┌──────────────────┬──────────────────────┐
 상대 측 d.*  │  ✓ 대개 이것     │  ✗ 외부 조인이 무너짐 │
              ├──────────────────┼──────────────────────┤
 보존 측 e.*  │  ✗ 엉뚱한 NULL   │  ✓ 대개 이것          │
              └──────────────────┴──────────────────────┘
                     ↑                        ↑
              "붙이는 규칙"              "결과에서 빼라"
```

★ **대각선이 맞는 칸이다.** 상대 측 조건은 `ON`, 보존 측 조건은 `WHERE`.\
외우기 쉬운 이유가 있다 — **보존 측 행을 지우고 싶은 건 `WHERE` 뿐이고, `ON` 은 애초에 그럴 능력이 없다**(3번).

다만 **표는 「대개」이지 규칙이 아니다.** 진짜 판정은 한 문장이다.

```text
"조건에 안 맞는 보존 측 행을 결과에서 보고 싶은가?"
        보고 싶다 -> ON          안 보고 싶다 -> WHERE
```

---

### 8. `RIGHT JOIN` 에서의 행 수

**(A) `ON` 은 3행, (B) `WHERE` 는 1행이다.**

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

**규칙은 똑같고 보존 측만 바뀐다.** `RIGHT` 의 보존 측은 `dept` 다.

```text
(A) ON 경로                               (B) WHERE 경로
(b) ON: dept_id 같고 AND salary>=400      (b) ON: dept_id 같다
     -> bob-sales 만                            -> ann-sales, bob-sales, cho-dev
(c) 짝 없는 dept 를 되살린다                (c) 짝 없는 dept(hr) 를 되살린다
     -> + dev(NULL), hr(NULL)      3행          -> + hr(NULL)                4행
                ↓                                       ↓
              3행                          2. WHERE e.salary >= 400
                                                 ann  300     FALSE   버림
                                                 cho  NULL    UNKNOWN 버림
                                                 hr 행 e.salary NULL  UNKNOWN 버림
                                                        ↓
                                                      1행
```

★ **(B)에서 `hr` 까지 죽었다.** 조건이 보존 측이 아니라 **상대 측**(`emp`)에 걸렸기 때문이다 — `RIGHT` 에서는 `emp` 가 상대 측이다.\
**「`e.` 냐 `d.` 냐」가 아니라 「보존 측이냐 상대 측이냐」가 기준**이라는 것이 여기서 확인된다.

`FULL OUTER JOIN` 에서는 **양쪽이 보존 측**이라 양쪽이 다 무너진다 — [16번](../16-full-outer-join/)에서 5행이 2행이 됐다.

---

### 9. 옵티마이저는 이 차이를 아는가

**안다. PG 는 `Hash Left Join` 을 `Hash Join` 으로 바꾸고, MySQL 은 `dept` 표를 계획에서 아예 없앤다.**

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

★ **맨 윗줄만 다르다 — `Hash Left Join` → `Hash Join`.** 나머지 다섯 줄은 한 글자도 같다.\
**PG 가 내 `LEFT JOIN` 을 `INNER JOIN` 으로 다시 썼다.**

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

**`dept` 가 통째로 사라졌다.** MySQL 의 추론은 이렇다.

```text
 d.name = 'sales' 여야 한다
        ↓
 그런 dept 는 id=10 하나뿐이다 (name 이 UNIQUE)
        ↓
 조인이 붙으려면 e.dept_id = 10 이어야 한다
        ↓
 NULL 로 채워진 행은 이 조건을 못 통과한다
        ↓
 dept 를 읽을 필요가 없다 — e.dept_id = '10' 만 보면 된다
```

| | `ON` 버전 | `WHERE` 버전 |
|---|---|---|
| PG 18.6 | `Hash Left Join` | **`Hash Join`** |
| MySQL 8.4.10 | `Nested loop left join` | **조인 노드 없음** |

★ **여기서 뒤집어 읽을 것** — 엔진이 내 실수를 고쳐 준 게 아니다.\
**내가 적은 것의 뜻이 이미 내부 조인이었고, 엔진은 그 뜻을 정확히 이행했다.**\
옵티마이저를 꺼도 답은 2행이다 — **계획이 결과를 바꾼 게 아니라, 결과의 정의가 계획을 그렇게 만들었다.**

> **읽을 때 주의** — PG 계획의 `rows=1130` 같은 추정치는 **통계가 없어서 나온 기본값**이다(이 표들은 `ANALYZE` 를 돌린 적이 없다).\
> 여기서 볼 것은 행 수가 아니라 **노드 이름**이다. 계획 읽기는 [목록의 **58번 주제**](../58-explain-plan-tree/), 추정과 실측의 어긋남은 [**60번 주제**](../60-explain-analyze-estimates-vs-actuals/)가 정본이다.

---

### 10. 고치는 법 셋 — 그리고 셋은 같은 답을 주는가

**셋은 서로 다른 답을 준다. 무엇이 맞는지는 요구사항이 정한다.**

```text
(A) 조건을 ON 으로 옮긴다                 -> 4행
(B) WHERE 에 OR d.id IS NULL 을 더한다    -> 3행
(C) INNER JOIN 이라고 적는다              -> 2행
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

(B) ### SQL: SELECT e.name AS emp, d.name AS dept FROM emp e LEFT JOIN dept d
             ON e.dept_id = d.id WHERE d.name = 'sales' OR d.id IS NULL ORDER BY e.id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 emp | dept                      +-----+-------+
-----+-------                    | emp | dept  |
 ann | sales                     +-----+-------+
 bob | sales                     | ann | sales |
 dan | NULL                      | bob | sales |
(3 rows)                         | dan | NULL  |
                                 +-----+-------+
```

```text
      (A) 4행              (B) 3행              (C) 2행
   ann | sales          ann | sales          ann | sales
   bob | sales          bob | sales          bob | sales
   cho | NULL           dan | NULL
   dan | NULL
     ↑                    ↑                    ↑
 "cho 는 남기되       "cho 는 부서가       "짝 있는 것만"
  부서란을 비운다"      있으니 뺀다"
```

| | 무엇을 뜻하나 | 언제 |
|---|---|---|
| (A) `ON` 으로 옮기기 | **모든 사원**을 보이고 `sales` 인 사람만 부서명을 채운다 | 「기준 표 전체 + 조건부 부가정보」가 요구사항일 때 |
| (B) `OR 키 IS NULL` | `sales` 인 사람 **+ 부서가 아예 없는 사람** | 「조건에 맞는 것 + 미분류」가 요구사항일 때 |
| (C) `INNER JOIN` | `sales` 인 사람만 | 사실 이게 필요했을 때 — **뜻을 드러낸다** |

★ **(C)를 얕보지 마라.** `LEFT JOIN` + `WHERE` 로 같은 답을 내는 질의는 **읽는 사람을 속인다.**\
`LEFT` 라고 적혀 있으면 독자는 「기준 표가 다 나온다」고 읽는다. 뜻이 `INNER` 면 `INNER` 라고 적는다.

**(B)의 `IS NULL` 은 `NULL` 일 수 없는 열에 건다.** `d.name IS NULL` 로 쓰면 「짝이 없다」와 「이름이 원래 `NULL` 이다」가 섞인다([14번](../14-left-right-outer-join/)).

**반조인은 (B)의 특수형이다** — `OR` 없이 `IS NULL` 만 남기면 「짝이 없는 것만」이 된다.

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
여기서는 「급여 400 이상이면서 부서가 있는」 조건을 못 채운 셋이 나왔다.\
같은 일을 `NOT EXISTS` 로도 한다 — [목록의 **19번 주제**](../19-semi-anti-join/)가 정본이다.

---

### 11. 질의를 훑을 때 이 사고를 잡는 신호

**`WHERE` 절에 상대 측 별칭(`d.`)이 보이면 의심한다.**

```sql
FROM emp e
LEFT JOIN dept d ON e.dept_id = d.id
WHERE d.name = 'sales'        -- <- 여기. LEFT JOIN 의 상대 측이 WHERE 에 있다
  AND e.salary >= 400         -- <- 이건 보존 측이라 괜찮다
```

```text
훑는 순서 — 세 줄이면 끝난다

1. 이 조인의 보존 측이 어느 표인가?          -> LEFT 면 앞의 표
2. WHERE 에 상대 측 별칭이 있나?             -> 있으면 2-a 로
2-a. 그 조건이 NULL 행을 통과시키나?         -> 못 하면 외부 조인이 무너진 것
3. 무너진 게 의도인가?                       -> 의도면 INNER JOIN 이라고 적는다
```

**보조 신호 둘.**

- **`ORDER BY` 를 붙이고 행 수를 센다.** 보존 측 행 수보다 결과가 적으면 무너진 것이다.\
  이 사고는 **에러를 안 내므로** 행 수 대조가 유일한 자동 검사다.
- **`IS NULL` 이 없는 `LEFT JOIN + WHERE 상대측열`** 은 거의 항상 잘못이다.\
  `OR … IS NULL` 이 있거나 `WHERE 키 IS NULL`(반조인)이면 의도된 것이다.

★ **코드 리뷰 규칙으로 쓰면 이렇게 된다** — 「`LEFT JOIN` 이 있는 질의에서 `WHERE` 에 상대 측 열이 나오면, 리뷰어가 의도를 묻는다.」

---

### 12. 두 엔진의 **결과**가 다른 자리가 있는가

**없다. 이 주제의 모든 결과가 양쪽에서 같았다.**

| | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| `LEFT JOIN` + `ON` 조건 | 4행 | 4행 |
| `LEFT JOIN` + `WHERE` 조건 | 2행 | 2행 |
| `ON FALSE` | 4행 | 4행 |
| 보존 측 열 조건 (`ON` / `WHERE`) | 4행 / 2행 | 4행 / 2행 |
| `RIGHT JOIN` (`ON` / `WHERE`) | 3행 / 1행 | 3행 / 1행 |
| `OR 키 IS NULL` | 3행 | 3행 |

**갈린 것은 실행 계획뿐이다**(9번) — 그리고 그건 **결과가 아니라 구현**이다.

```text
 결과       두 엔진이 같다        -> 언어가 정한 것
 계획       두 엔진이 다르다      -> 옵티마이저가 정한 것
              ↑
   같은 뜻을 다른 방법으로 이행한 것이지
   다른 답을 낸 것이 아니다
```

★ **조건의 자리 규칙은 방언이 아니라 언어의 뼈대다.** 그래서 이 주제는 「어느 엔진에서는 되는데」가 없다.\
방언이 갈리는 것은 [16번](../16-full-outer-join/)의 `FULL OUTER JOIN` 부터다 — MySQL 8.4.10 에는 문법 자체가 없다(`ERROR 1064`).

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| ★ `ON` 대 `WHERE` (1번) | PG 18.6 · MySQL 8.4.10 | 각 4회 | 행 출력 + `COUNT(*)` 양쪽 |
| `ON FALSE` · `WHERE TRUE` (3번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **`ON` 이 보존 측을 못 지운다는 근거** |
| 내부 조인 대조 (5번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | 13번의 결과를 재확인 |
| 보존 측 열 조건 (6번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | |
| `RIGHT JOIN` (8번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | |
| 실행 계획 (9번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **구현 의존** — 버전·통계가 바뀌면 다시 찍어야 한다 |
| 고치는 법 셋 (10번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | 반조인 형태까지 |
| 방언 대조 (12번) | PG 18.6 · MySQL 8.4.10 | 각 항목 | **결과가 다른 자리 0건** |

**구현 의존 항목** — 9번의 계획뿐이다. `Hash Left Join` → `Hash Join` 도, MySQL 이 `dept` 를 없앤 것도 옵티마이저의 선택이다.\
다만 **그 선택이 가능하다는 사실 자체는 결과의 정의에서 나온다** — 결과가 같지 않으면 옵티마이저가 그렇게 바꿀 수 없다.

**언어 보장 항목** — 1\~8·10\~12번. `ON` 이 1번 칸 안이고 `WHERE` 가 2번 칸이라는 것, `ON` 이 보존 측을 못 지운다는 것,\
`WHERE` 가 `UNKNOWN` 을 버린다는 것은 전부 문서가 정한 것이고 두 엔진에서 같았다.

**버전** — 이 주제에서 버전에 갈리는 것은 없다. 다음 버전에서도 **9번(계획)과 12번(대조)만 다시 돌리면 된다.**
