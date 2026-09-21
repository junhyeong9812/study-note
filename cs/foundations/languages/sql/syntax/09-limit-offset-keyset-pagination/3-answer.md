# sql/09-LIMIT·OFFSET·FETCH FIRST 와 키셋 페이지네이션 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력은 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 문서를 보고 적은 출력은 없다.\
> **측정 조건**(6·7번) — `study` 안의 **20만 행 세션 임시 표**(`big(id PK, val)`), `EXPLAIN ANALYZE` **각 3회**.\
> 도커 컨테이너 안의 단발 측정이라 **절댓값이 아니라 `actual rows` 와 자릿수**를 본다. 임시 표는 롤백·삭제해 잔재가 없다.\
> 문서 근거는 [PG 18 SELECT](https://www.postgresql.org/docs/18/sql-select.html) · [MySQL 8.4 LIMIT Optimization](https://dev.mysql.com/doc/refman/8.4/en/limit-optimization.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. `LIMIT 2 OFFSET 1` 에서 `ann` 은 어디까지 참여했나

**정렬까지 전부 참여하고, 마지막 8번 칸에서 버려졌다.**

```text
### SQL: SELECT id, name FROM emp ORDER BY id LIMIT 2 OFFSET 1;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name                       +----+------+
----+------                      | id | name |
  2 | bob                        +----+------+
  3 | cho                        |  2 | bob  |
(2 rows)                         |  3 | cho  |
                                 +----+------+
```

**왜 그런가** — `LIMIT` 은 논리적 처리 순서의 **여덟 번째 칸**이다([01번](../01-logical-query-processing-order/)).

```text
1 FROM     emp 4행을 읽는다           <- ann 참여
2 WHERE    (없음)
5 SELECT   id, name 두 열을 만든다     <- ann 참여
7 ORDER BY id 로 4행을 줄 세운다       <- ann 참여 (1등이었다)
8 LIMIT    OFFSET 1 로 ann 을 버리고    <- 여기서 탈락
           2행을 꺼낸다
```

**`OFFSET` 은 「건너뛴다」가 아니라 「만들고 버린다」**는 것이 이 한 행에 다 들어 있다.\
건너뛰려면 「어디가 1번째인지」를 알아야 하는데, 그건 **세어 봐야 안다.**

범위 밖 `OFFSET` 은 조용히 0행이다.

```text
### SQL: SELECT id FROM emp ORDER BY id LIMIT 2 OFFSET 100;
--- PG 18.6 ---
 id
----
(0 rows)
--- MySQL 8.4.10 ---
(빈 결과 — 한 줄도 찍히지 않는다)
```

음수는 양쪽 다 막되 **성격이 다르다** — PG 는 값 검사, MySQL 은 문법 오류다.

```text
### SQL: SELECT id FROM emp ORDER BY id LIMIT -1;
--- PG 18.6 ---
ERROR:  LIMIT must not be negative
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near '-1' at line 1
```

---

### 2. `FETCH FIRST 2 ROWS ONLY` 를 받아 주는 엔진

**PostgreSQL 18.6 만 받아 준다.**

```text
### SQL: SELECT id, name FROM emp ORDER BY id FETCH FIRST 2 ROWS ONLY;
--- PG 18.6 ---
 id | name
----+------
  1 | ann
  2 | bob
(2 rows)
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near 'FETCH FIRST 2 ROWS ONLY' at line 1
```

`OFFSET ... ROWS FETCH NEXT ... ROWS ONLY` 형태도 같다.

```text
### SQL: SELECT id, name FROM emp ORDER BY id OFFSET 1 ROWS FETCH NEXT 2 ROWS ONLY;
--- PG 18.6 ---
 id | name
----+------
  2 | bob
  3 | cho
(2 rows)
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near 'OFFSET 1 ROWS FETCH NEXT 2 ROWS ONLY' at line 1
```

**왜 그런가** — `FETCH FIRST` 는 PG 문서가 **표준형으로 소개하는** 문법이고, MySQL 8.4.10 은 이 형태를 구현하지 않았다.\
`ERROR 1064` 는 파서가 그 토큰을 모른다는 뜻이다.

**실무 함의** — 「표준이니까 이식성이 좋겠지」가 여기서 틀린다.\
**이식성이 있는 것은 오히려 `LIMIT n OFFSET m`** 이다 — 표준형은 아니지만 양쪽에 다 있다.

---

### 3. `LIMIT 1, 2` 에 대한 PG 의 에러 메시지

**에러 문구와 함께 `HINT` 로 대안까지 알려 준다.**

```text
### SQL: SELECT id, name FROM emp ORDER BY id LIMIT 1, 2;
--- PG 18.6 ---
ERROR:  LIMIT #,# syntax is not supported
LINE 1: SELECT id, name FROM emp ORDER BY id LIMIT 1, 2;
                                             ^
HINT:  Use separate LIMIT and OFFSET clauses.
--- MySQL 8.4.10 ---
+----+------+
| id | name |
+----+------+
|  2 | bob  |
|  3 | cho  |
+----+------+
```

**왜 이 에러가 특별한가** — 일반적인 문법 오류가 아니라 **「그 문법을 알고 있고, 지원하지 않는다」**는 메시지다.

```text
모르는 문법이면              PG 가 낸 것
syntax error at or near ...  LIMIT #,# syntax is not supported
                             HINT: Use separate LIMIT and OFFSET clauses.
                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                   MySQL 에서 옮겨 오는 사람을 위한 안내
```

**의미를 읽을 때 주의할 것이 하나 있다** — MySQL 의 `LIMIT 1, 2` 는 **`LIMIT 2 OFFSET 1`** 이다.

```text
MySQL  LIMIT <건너뛸 수>, <개수>      LIMIT 1, 2  ->  1개 건너뛰고 2개
표준   LIMIT <개수> OFFSET <건너뛸 수> LIMIT 2 OFFSET 1
             ^^^^^^                          ^^^^^^^
             순서가 반대다
```

출력이 `bob`·`cho` 인 것이 그 증거다 — 2번 칸 건너뛰고 2행이 아니라, **1행 건너뛰고 2행**이다.\
**순서를 헷갈리면 에러 없이 다른 페이지가 나온다.**

---

### 4. `OFFSET` 단독과 `LIMIT ALL` 은 어느 엔진에서 도나

**둘 다 PostgreSQL 18.6 전용이다.**

```text
### SQL: SELECT id FROM emp ORDER BY id OFFSET 2;
--- PG 18.6 ---
 id
----
  3
  4
(2 rows)
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near 'OFFSET 2' at line 1
```

```text
### SQL: SELECT id FROM emp ORDER BY id LIMIT ALL;
--- PG 18.6 ---
 id
----
  1
  2
  3
  4
(4 rows)
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near 'ALL' at line 1
```

**왜 그런가** — MySQL 문법에서 `OFFSET` 은 **`LIMIT` 에 딸린 부속**이지 독립 절이 아니다. `LIMIT` 없이 올 수 없다.\
`LIMIT ALL` 도 마찬가지로 `LIMIT` 뒤에 **부호 없는 정수만** 오기 때문에 `ALL` 을 못 받는다.

**MySQL 에서 「n 번째부터 끝까지」를 쓰려면** 개수 자리에 아주 큰 수를 넣는다. 던져 봤다.

```text
### SQL: SELECT id FROM emp ORDER BY id LIMIT 18446744073709551615 OFFSET 2;
--- PG 18.6 ---
ERROR:  bigint out of range
--- MySQL 8.4.10 ---
+----+
| id |
+----+
|  3 |
|  4 |
+----+
```

이번에도 **정확히 서로를 거부한다** — PG 는 그 수가 `bigint` 범위를 넘어 막고, MySQL 은 부호 없는 64비트라 받는다.

| | PG 18.6 | MySQL 8.4.10 |
|---|---|---|
| `OFFSET m` 단독 | ✓ | **`ERROR 1064`** |
| `LIMIT ALL` | ✓ | **`ERROR 1064`** |
| `LIMIT 18446744073709551615 OFFSET m` | **`bigint out of range`** | ✓ |
| 「끝까지」를 표현하려면 | `LIMIT ALL` 또는 `LIMIT` 생략 | 개수 자리에 아주 큰 수 |

**정리하면 — 양쪽에서 도는 형태는 `LIMIT n [OFFSET m]` 하나다.**

---

### 5. `FETCH FIRST 1 ROWS WITH TIES` 가 내는 행 수

**2행이다.**

```text
### SQL: SELECT id, dept_id FROM emp ORDER BY dept_id FETCH FIRST 1 ROWS WITH TIES;
--- PG 18.6 ---
 id | dept_id
----+---------
  1 |      10
  2 |      10
(2 rows)
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near 'FETCH FIRST 1 ROWS WITH TIES' at line 1
```

**왜 그런가** — `WITH TIES` 는 **마지막 행과 정렬 키 값이 같은 행들을 함께** 가져온다.

```text
ORDER BY dept_id 로 세운 순서 (PG)
  1 | 10   <- 1행째
  2 | 10   <- 정렬 키가 같다 -> WITH TIES 가 데려온다
  3 | 20
  4 | NULL
```

```text
ONLY  : "정확히 n 행"            -> 동률이면 누가 잘릴지 보장 없음
TIES  : "n 행 + 동률인 것 전부"   -> 행 수가 n 보다 많을 수 있다
```

**「상위 3명」 같은 요구에 정확히 맞는 문법**이다 — 3등이 둘이면 넷을 줘야 하는 것이 보통의 요구다.\
[08번](../08-order-by-null-position-stability/)에서 본 「동률 순서는 보장 없음」의 **정직한 처리 방법**이기도 하다. 자르지 않고 다 준다.

MySQL 에는 없으므로 순위 함수로 한 겹 감싼다 — `RANK() OVER (ORDER BY dept_id) <= 1`.\
순위 함수의 정본은 목록의 **29번 주제**다.

---

### 6. `OFFSET 100000` 계획의 자식 노드 `actual rows`

**100,010 이다.** 10행을 얻으려고 100,010 행을 만들었다.

```text
--- PG 18.6 : EXPLAIN (ANALYZE, COSTS OFF, TIMING OFF, SUMMARY OFF) ---
=== (B) OFFSET 100000 ===
 Limit (actual rows=10.00 loops=1)
   Buffers: local hit=4 read=715 written=1
   ->  Index Only Scan using big_pkey on big (actual rows=100010.00 loops=1)
         Heap Fetches: 100010
         Buffers: local hit=4 read=715 written=1
```

```text
--- MySQL 8.4.10 : EXPLAIN ANALYZE ---
-> Limit/Offset: 10/100000 row(s)  (cost=5169 rows=10) (actual time=9.06..9.06 rows=10 loops=1)
    -> Covering index scan on big using PRIMARY  (cost=5169 rows=100010) (actual time=0.364..6.88 rows=100010 loops=1)
```

**왜 그런가** — `OFFSET` 은 **결과를 만든 뒤 앞에서부터 버리는** 연산이다.

```text
     Limit (rows=10)              <- 부모: 최종 10행
         ^
         | 100,010 행을 받아
         | 앞 100,000 을 버린다
         |
  Index Only Scan (rows=100010)   <- 자식: 실제로 만든 행
```

**「인덱스를 타는데 왜 느리지」의 답이 여기 있다.**

```text
인덱스는 이미 타고 있다             느린 원인은 버리는 행 수다
  Index Only Scan / Covering index   100,000 행을 만들어 버렸다
  -> 인덱스를 더 만들어도 안 낫는다
```

PG 의 `Heap Fetches: 100010` 과 MySQL 의 노드 이름 `Limit/Offset: 10/100000` 이 같은 말을 한다.\
비교 대상으로 `OFFSET 0` 은 자식 `actual rows` 가 **10** 이었다.

시간도 3회씩 쟀다.

```text
--- PG 18.6 (3회) ---
 Limit (actual time=13.062..13.064)
 Limit (actual time=10.572..10.573)
 Limit (actual time=12.893..12.895)

--- MySQL 8.4.10 (3회) ---
 actual time=9.81..9.81 / 10.2..10.2 / 9.74..9.74
```

**절댓값은 이 머신의 것이다.** 읽을 것은 `actual rows` 와, 다음 문항과의 자릿수 차이다.

---

### 7. 키셋으로 바꾼 계획의 자식 노드 `actual rows`

**10 이다.** 결과는 6번과 같은 10행인데 만든 행이 10,001배 적다.

```text
--- PG 18.6 ---
=== (C) 키셋: WHERE id > 100000 ===
 Limit (actual rows=10.00 loops=1)
   Buffers: local hit=4
   ->  Index Only Scan using big_pkey on big (actual rows=10.00 loops=1)
         Index Cond: (id > 100000)
         Heap Fetches: 10
         Buffers: local hit=4
```

```text
--- MySQL 8.4.10 ---
-> Limit: 10 row(s)  (cost=20118 rows=10) (actual time=0.335..0.336 rows=10 loops=1)
    -> Filter: (big.id > 100000)  (cost=20118 rows=100161) (actual time=0.334..0.335 rows=10 loops=1)
        -> Covering index range scan on big using PRIMARY over (100000 < id)  (cost=20118 rows=100161) (actual time=0.329..0.329 rows=10 loops=1)
```

**왜 그런가** — 조건이 **인덱스 탐색 조건**으로 내려갔다.

```text
OFFSET 판                              키셋 판
Index Only Scan (조건 없음)             Index Only Scan
  -> 앞에서부터 순서대로 훑는다             Index Cond: (id > 100000)
  -> 100,010 행                          -> 인덱스에서 그 자리로 바로 내려간다
                                         -> 10 행
```

PG 의 `Index Cond: (id > 100000)`, MySQL 의 `index range scan ... over (100000 < id)` 가 그 증거다.\
(MySQL 의 추정 `rows=100161` 은 **추정치**이고, 실제로 만든 것은 `actual ... rows=10` 이다. 추정과 실측이 어긋나는 자리를 읽는 법은 목록의 60번 주제다.)

**두 문항을 나란히 놓으면 이렇다.**

| | 자식 노드 `actual rows` | 시간(3회 중앙값 근처) |
|---|---|---|
| PG `OFFSET 100000` | **100,010** | 약 10~13 ms |
| PG 키셋 | **10** | 약 0.015~0.029 ms |
| MySQL `OFFSET 100000` | **100,010** | 약 9.7~10.2 ms |
| MySQL 키셋 | **10** | 약 0.36~0.47 ms |

**신호 대 잡음** — 흔들림은 PG 약 20% · MySQL 약 5% 인데, 차이는 PG 약 **500배** · MySQL 약 **25배** 다.\
신호가 잡음보다 훨씬 크므로 **방향은 재현된다.** 두 엔진의 배율이 다른 것은 절댓값이 환경에 걸려 있다는 뜻이고, **외울 것은 배율이 아니라 `actual rows` 가 10 이라는 사실**이다.

---

### 8. 페이지 사이에 행이 들어왔을 때의 page2

**`bob`·`cho` 가 나온다. `bob` 은 1페이지에 이미 나왔던 행이다.**

```text
--- page1: LIMIT 2 OFFSET 0 ---
### SQL: SELECT id, name FROM emp ORDER BY id LIMIT 2 OFFSET 0;
--- PG 18.6 ---
 id | name
----+------
  1 | ann
  2 | bob
(2 rows)

--- 그 사이에 INSERT INTO emp VALUES (0,'zed',10,100); 가 일어난다 ---

--- page2: LIMIT 2 OFFSET 2 ---
### SQL: SELECT id, name FROM emp ORDER BY id LIMIT 2 OFFSET 2;
--- PG 18.6 ---
 id | name
----+------
  2 | bob       <- 1페이지에 이미 나왔던 행
  3 | cho
(2 rows)
```

MySQL 8.4.10 에서도 **똑같았다.** (양쪽 다 `ROLLBACK` 후 `emp` 가 4행인 것을 확인했다.)

**왜 그런가** — `OFFSET` 은 **「몇 번째」**를 센다. 앞쪽에 행이 끼어들면 그 번호가 **다른 행**을 가리킨다.

```text
page1 을 읽은 시점 순서            id=0 이 들어온 뒤 순서
  ann(1) bob(2) cho(3) dan(4)       zed(0) ann(1) bob(2) cho(3) dan(4)
  ^^^^^^^^^^^^^                            ^^^^^^^^^^^^^
  OFFSET 0 LIMIT 2                  OFFSET 2 LIMIT 2 가 가리키는 자리
  -> ann, bob                       -> bob, cho
                                        ^^^ 한 칸 밀려서 bob 이 또 나온다
```

**사용자 눈에는 「같은 글이 2페이지에도 있네」로 보인다.** 에러도 경고도 없다.

---

### 9. 행이 삭제되면 page2 에 무엇이 나오나

**`dan` 한 행만 나온다. `cho` 가 통째로 사라진다.**

```text
--- page1: LIMIT 2 OFFSET 0 ---
### SQL: SELECT id, name FROM emp ORDER BY id LIMIT 2 OFFSET 0;
--- PG 18.6 ---
 id | name
----+------
  1 | ann
  2 | bob
(2 rows)

--- 그 사이에 DELETE FROM emp WHERE id = 1; 이 일어난다 ---

--- page2: LIMIT 2 OFFSET 2 ---
### SQL: SELECT id, name FROM emp ORDER BY id LIMIT 2 OFFSET 2;
--- PG 18.6 ---
 id | name
----+------
  4 | dan       <- cho 가 통째로 빠졌다
(1 row)
```

MySQL 8.4.10 에서도 **똑같았다.** (양쪽 다 `ROLLBACK` 후 4행 확인.)

**왜 그런가** — 8번의 반대 방향이다.

```text
page1 을 읽은 시점                 ann 이 지워진 뒤
  ann(1) bob(2) cho(3) dan(4)       bob(2) cho(3) dan(4)
  ^^^^^^^^^^^^^                            ^^^^^^^^^^^^
  OFFSET 0 LIMIT 2                  OFFSET 2 LIMIT 2 가 가리키는 자리
  -> ann, bob                       -> dan 하나 (그 뒤가 없다)
                                       cho 는 어느 페이지에도 안 나온다
```

**삽입은 중복을, 삭제는 누락을 만든다.**

| | 증상 | 사용자가 알아채나 |
|---|---|---|
| 앞쪽에 `INSERT` | 같은 행이 두 페이지에 | **알아챈다** — 눈에 띈다 |
| 앞쪽에 `DELETE` | 한 행이 어느 페이지에도 안 나옴 | **못 알아챈다** |

**누락 쪽이 훨씬 위험하다.** 화면에 아무 흔적도 안 남고, 배치 순회라면 **그 행만 조용히 처리가 안 된다.**\
「전부 처리했다」고 로그에 찍히는 무음 실패다.

---

### 10. 같은 시점에 키셋으로 뽑으면

**두 경우 모두 옳은 페이지(`cho`·`dan`)를 준다.**

```text
--- INSERT 가 일어난 시점 ---
### SQL: SELECT id, name FROM emp WHERE id > 2 ORDER BY id LIMIT 2;
--- PG 18.6 ---
 id | name
----+------
  3 | cho
  4 | dan
(2 rows)

--- DELETE 가 일어난 시점 ---
### SQL: SELECT id, name FROM emp WHERE id > 2 ORDER BY id LIMIT 2;
--- PG 18.6 ---
 id | name
----+------
  3 | cho
  4 | dan
(2 rows)
```

MySQL 8.4.10 에서도 **양쪽 다 `cho`·`dan`** 이었다.

**왜 영향을 안 받나** — **기준이 「몇 번째」가 아니라 「어디까지 봤나」**이기 때문이다.

```text
OFFSET 방식                           키셋 방식
"앞의 2개를 버려라"                    "id 가 2보다 큰 것부터"
 -> 앞쪽이 바뀌면 2가 다른 자리다        -> id=2 는 데이터가 바뀌어도 id=2 다
 -> zed 가 들어오면 한 칸 밀린다         -> zed 는 id=0 이라 조건에 안 걸린다
 -> ann 이 지워지면 한 칸 당겨진다        -> ann 이 지워져도 id>2 는 그대로다
```

**앞쪽에서 무슨 일이 일어나도 경계가 안 움직인다.** 이것이 키셋의 본질적 이득이고, 성능은 그 부산물이다.

> **키셋 페이지네이션** — 「마지막으로 본 행의 키」를 조건으로 다음 페이지를 뽑는 방식. seek method 라고도 한다.\
> 예: 1페이지 마지막이 `id = 2` 였으면 2페이지는 `WHERE id > 2 ORDER BY id LIMIT 2`.

**단, 전제가 있다** — 정렬이 **결정적**이어야 한다. 정렬 키가 고유하지 않으면 「마지막으로 본 키」가 경계를 못 정한다([08번](../08-order-by-null-position-stability/)).

---

### 11. 복합 키 키셋의 결과와 `dan` 이 빠진 이유

**출력**

```text
### SQL: SELECT id, dept_id FROM emp WHERE (dept_id, id) > (10, 1) ORDER BY dept_id, id LIMIT 2;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | dept_id                    +----+---------+
----+---------                   | id | dept_id |
  2 |      10                    +----+---------+
  3 |      20                    |  2 |      10 |
(2 rows)                         |  3 |      20 |
                                 +----+---------+
```

**`bob`(10, 2)과 `cho`(20, 3)가 나온다. `dan` 은 `dept_id` 가 `NULL` 이라 빠졌다.**

**왜 `dan` 이 빠지나** — 행 생성자 비교에 `NULL` 이 끼면 `UNKNOWN` 이 되고, `WHERE` 가 버린다.

```text
dan: (dept_id, id) = (NULL, 4)

  (NULL, 4) > (10, 1)
    -> 첫 항목부터 비교한다: NULL > 10  ->  UNKNOWN
    -> 전체가 UNKNOWN
    -> WHERE 가 버린다                    <- 에러도 경고도 없다
```

[05번](../05-null-comparison-is-distinct-from/)의 규칙이 그대로 나타난 것이다.

**행 생성자 비교가 무엇을 하는지도 짚어 둔다 — 사전식 비교다.**

```text
(dept_id, id) > (10, 1) 의 뜻

  dept_id > 10                     이거나
  dept_id = 10 AND id > 1          이것

흔한 오답: WHERE dept_id >= 10 AND id > 1
  -> (20, 1) 인 행을 놓친다. dept_id 는 크지만 id 가 1 이라 조건에 안 걸린다
```

**두 가지 교훈이 한 문항에 있다.**

1. **복합 키 키셋은 행 생성자로 쓴다.** `AND` 로 풀면 행을 놓친다.
2. **키셋의 정렬 키는 `NOT NULL` 이어야 한다.** `NULL` 이 섞이면 그 행이 **어느 페이지에도 안 나온다.**

---

### 12. 키셋으로 바꾸면 포기하는 기능 둘

**「임의 페이지로 점프」와 「전체 페이지 수 표시」다.**

```text
키셋이 고치는 것                      키셋이 못 고치는 것
+---------------------------+        +---------------------------+
| 깊은 페이지의 비용          |        | "37페이지로 점프"          |
|   actual rows 100010 -> 10 |        |   "어디까지 봤나" 를 모른다  |
| 페이지 경계의 중복·누락     |        | "전체 148페이지" 표시       |
|   bob 중복 / cho 누락 해결  |        |   따로 COUNT(*) 를 세야 한다 |
+---------------------------+        +---------------------------+
```

**왜 점프가 안 되나** — 키셋의 조건은 **직전 페이지의 마지막 키**에서 나온다.

```text
OFFSET 방식                     키셋 방식
37페이지 = OFFSET 36*20         37페이지 = ?
 -> 번호만 있으면 계산된다        -> 36페이지의 마지막 키를 알아야 한다
                                 -> 그걸 알려면 1~36 페이지를 지나와야 한다
```

| | `OFFSET` 방식 | 키셋 방식 |
|---|---|---|
| 깊은 페이지 비용 | **O(건너뛴 행 수)** | 앞쪽과 같다 |
| 경계 안정성 | **중복·누락** | 안정적 |
| 임의 페이지 점프 | 가능 | **불가** |
| 전체 페이지 수 | `COUNT(*)` 로 가능 | 따로 세야 한다 |
| 정렬 키 조건 | 결정적이기만 하면 됨 | **`NOT NULL` + 인덱스** |

**그래서 UI 가 결정한다.**

```text
무한 스크롤 · "다음" 버튼 · 배치 순회   ->  키셋
페이지 번호 격자가 요구사항            ->  OFFSET, 단 깊이를 제한한다
                                          ("100페이지 이후는 검색을 좁혀 주세요")
```

**배치 순회에 `OFFSET` 을 쓰면 안 되는 이유는 특히 분명하다** — 페이지마다 버리는 행이 누적돼 **전체 비용이 O(n²)** 이 된다.\
10,000페이지짜리 순회라면 마지막 페이지 하나에서만 100만 행을 만들어 버린다.

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| `LIMIT`/`OFFSET` 기본 (1번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | 범위 밖 · 음수 포함 |
| `FETCH FIRST` (2번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **MySQL `ERROR 1064`** |
| `LIMIT m,n` (3번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **PG 의 `HINT` 가 근거** |
| `OFFSET` 단독 · `LIMIT ALL` (4번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **양쪽 에러 메시지가 근거** |
| `WITH TIES` (5번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 1행 요청에 2행 |
| ★ `OFFSET` 비용 (6번) | PG 18.6 · MySQL 8.4.10 | **각 4회** | 20만 행 임시 표 · `EXPLAIN ANALYZE` · **구현 의존** |
| ★ 키셋 비용 (7번) | PG 18.6 · MySQL 8.4.10 | **각 4회** | 같은 표 · **구현 의존** |
| ★ 페이지 경계 `INSERT` (8번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **트랜잭션 + `ROLLBACK`** · 4행 원복 확인 |
| ★ 페이지 경계 `DELETE` (9번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 〃 |
| 키셋 대조 (10번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | `INSERT`·`DELETE` 시점 양쪽 |
| 행 생성자 키셋 (11번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `dan` 이 빠지는 것 확인 |
| `ORDER BY` 없는 `LIMIT` | PG 18.6 · MySQL 8.4.10 | 각 1회 | 08번의 반증 실험과 함께 읽는다 |

**구현 의존 항목** — 6·7번의 계획과 시간이다. `Index Only Scan`·`Covering index scan` 이 뽑힌 것은 **옵티마이저의 선택**이고,\
시간의 절댓값은 **이 머신·이 데이터**의 것이다. 재현되는 것은 **`actual rows`(100,010 대 10)와 자릿수 차이**다.\
MySQL 의 추정 `rows=100161` 처럼 **추정과 실측이 어긋나는 것**도 그 자체가 관찰 대상이다(목록의 60번 주제).

**언어 보장 항목** — 1·2·3·4·5·8·9·10·11·12번. `LIMIT` 이 8번 칸인 것, `OFFSET` 이 만들고 버리는 것,\
경계가 밀리면 중복·누락이 생기는 것, 행 생성자가 사전식으로 비교되고 `NULL` 에서 `UNKNOWN` 이 되는 것은 **두 엔진에서 같았다.**\
문법 표면(2·3·4·5번)만은 엔진마다 다르고, 그 차이도 **양쪽 출력으로 고정**했다.

**버전** — `FETCH FIRST`·`LIMIT ALL`·`OFFSET` 단독·`WITH TIES` 는 MySQL 8.4.10 에 없다.\
다음 버전에서는 **2·4·5번(문법 유무)과 6·7번(계획)**을 다시 돌린다.
