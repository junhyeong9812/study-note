# sql/09-LIMIT·OFFSET·FETCH FIRST 와 키셋 페이지네이션 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · SELECT · LIMIT Clause](https://www.postgresql.org/docs/18/sql-select.html) · [MySQL 8.4 · LIMIT Optimization](https://dev.mysql.com/doc/refman/8.4/en/limit-optimization.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력은 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 지어낸 출력은 없다.\
> **측정 조건** — 비용 비교(3절)는 **20만 행 세션 임시 표**에 기본키 인덱스를 걸고 `EXPLAIN ANALYZE` 를 **각 3회** 돌린 것이다.\
> 도커 컨테이너 안의 단발 측정이라 **절댓값이 아니라 자릿수와 `actual rows` 를 본다.** 임시 표는 롤백·삭제해 잔재가 없다.\
> **버전** — `FETCH FIRST` 는 PG 에 있고 MySQL 8.4.10 에는 문법이 없다(`ERROR 1064`).\
> **선행** — [08 ORDER BY](../08-order-by-null-position-stability/). **정렬이 결정적이지 않으면 페이지네이션은 성립하지 않는다.**

## 한눈에 — 쉽게 말하면

**`OFFSET` 은 「앞의 N개를 건너뛰라」가 아니라 「앞의 N개를 만들어 놓고 버리라」다.**

- 도서관에서 「10,001번째부터 10권」을 달라고 했다.
- 사서는 **1번부터 10,010번까지 전부 꺼낸 다음 앞의 10,000권을 도로 넣는다.**\
  건너뛰려면 **어디가 10,000번째인지 알아야 하는데, 그건 세어 봐야 안다.**
- 「내가 지난번에 10,000번 책까지 봤어요. **그 다음부터** 10권」이라고 하면?\
  사서는 **책장에서 바로 그 자리를 찾아** 10권만 꺼낸다.
- 이 둘의 차이가 **`OFFSET` 과 키셋 페이지네이션**이다.

| 비유 | 실체 |
|---|---|
| 「10,001번째부터」 | `OFFSET 10000 LIMIT 10` |
| 앞의 10,000권을 꺼냈다 도로 넣기 | 행을 만들고 버리는 비용 |
| 「10,000번 책 다음부터」 | `WHERE id > 10000 ORDER BY id LIMIT 10` |
| 책장에서 바로 그 자리 찾기 | 인덱스 탐색 |
| 내가 보는 사이 새 책이 꽂히는 것 | 페이지 사이에 들어온 `INSERT` |

```text
OFFSET 100000 LIMIT 10                 키셋 (WHERE id > 100000 LIMIT 10)
+-----------------------------+        +-----------------------------+
| 인덱스를 앞에서부터 훑는다    |        | 인덱스에서 100000 자리로     |
| 100,010 행을 만든다          |        | 바로 내려간다               |
| 앞 100,000 행을 버린다       |        | 10 행을 만든다              |
+-----------------------------+        +-----------------------------+
  실측: 자식 노드 actual rows            실측: 자식 노드 actual rows
        = 100,010                             = 10
```

이 사서가 **똑같은 구조로** SQL 의 행 제한이다.\
「페이지가 뒤로 갈수록 느려진다」·「같은 글이 2페이지에도 나온다」가 전부 이 그림 하나로 설명된다.

> **`OFFSET`** — 정렬된 결과에서 앞의 n 행을 **버리는** 지시. 건너뛰는 것이 아니라 만들고 버린다.\
> 예: `LIMIT 10 OFFSET 100000` 은 100,010 행을 만든 뒤 10 행만 남긴다.

> **키셋 페이지네이션(keyset pagination)** — 「마지막으로 본 행의 키」를 조건으로 다음 페이지를 뽑는 방식.\
> 예: `WHERE id > 100000 ORDER BY id LIMIT 10`. 「몇 번째」가 아니라 「어디까지 봤나」로 자른다.

## 이 주제가 답하려는 질문

1. **`OFFSET` 이 깊어질수록 왜 비싸지나** — 그리고 그것을 계획에서 어떻게 확인하나.
2. **페이지 사이에 데이터가 바뀌면 무슨 일이 생기나** — 같은 행이 두 번 나오는 이유.
3. **키셋 페이지네이션이 무엇을 고치고 무엇을 못 고치나.**

## 예시 데이터 — 이 묶음이 공유하는 것

이 폴더의 SQL 주제들이 **같은 두 표**를 쓴다. 표가 같으면 주제 간 비교가 공짜로 된다.

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

문법과 페이지 경계 실험은 이 네 행으로 한다 — **`LIMIT 2` 면 4행도 두 페이지다.**

비용 측정(3절)만은 행이 많아야 해서 **`study` 안에 20만 행짜리 세션 임시 표**를 만들어 썼다.\
PG 쪽은 `BEGIN ... ROLLBACK` 으로 감쌌고, MySQL 쪽은 `CREATE TEMPORARY TABLE` 후 `DROP` 했다. **`emp`·`dept` 는 건드리지 않았다.**

## 동작 방식

### 1. `LIMIT` 은 여덟 번째 칸이다 — 일을 줄여 주지 않는다

**언제 쓰나** — 결과의 앞부분만 필요할 때. **앞 일곱 칸의 일은 그대로 한다.**

```text
1 FROM     표를 읽는다            <- 다 읽어야 한다
2 WHERE    행을 버린다
3 GROUP BY 묶는다
4 HAVING   그룹을 버린다
5 SELECT   열을 만든다
6 DISTINCT 중복을 지운다
7 ORDER BY 줄을 세운다            <- 전부 봐야 1등을 안다
8 LIMIT    앞 n 행만 꺼낸다       <- 여기서 나머지를 버린다
```

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

그림 해설 — `ann`(id 1)도 **정렬까지는 참여했고** 마지막 칸에서 버려졌다.\
대가 — 정렬은 조기 종료가 안 된다. **예외는 정렬 키에 인덱스가 있어 이미 순서대로 읽을 수 있을 때**뿐이고, 그 예외가 3절의 키셋이 서는 토대다.

범위를 넘어가면 조용히 0행이다.

```text
### SQL: SELECT id FROM emp ORDER BY id LIMIT 2 OFFSET 100;
--- PG 18.6 ---
 id
----
(0 rows)
--- MySQL 8.4.10 ---
(빈 결과 — 한 줄도 찍히지 않는다)
```

음수는 양쪽 다 막는다 — **다만 에러의 성격이 다르다.**

```text
### SQL: SELECT id FROM emp ORDER BY id LIMIT -1;
--- PG 18.6 ---
ERROR:  LIMIT must not be negative
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near '-1' at line 1
```

PG 는 **값 검사**(`must not be negative`), MySQL 은 **문법 오류**다 — MySQL 문법에서 `LIMIT` 뒤는 애초에 부호 없는 정수만 온다.

---

### 2. 방언 — 같은 일을 네 가지 문법으로

**언제 쓰나** — 질의를 다른 엔진으로 옮길 때. **행 제한은 방언 차이가 큰 자리다.**

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

반대로 MySQL 의 두 값 `LIMIT` 은 PG 가 막는다 — **그런데 PG 가 그 문법을 알아보고 안내까지 한다.**

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

`LIMIT` 없이 `OFFSET` 만 쓰는 것과 `LIMIT ALL` 도 갈린다.

```text
### SQL: SELECT id FROM emp ORDER BY id OFFSET 2;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id                              ERROR 1064 (42000) at line 1: You have an error in your SQL
----                               syntax; check the manual that corresponds to your MySQL
  3                                server version for the right syntax to use near 'OFFSET 2'
  4                                at line 1
(2 rows)
```

```text
### SQL: SELECT id FROM emp ORDER BY id LIMIT ALL;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id                              ERROR 1064 (42000) at line 1: You have an error in your SQL
----                               syntax; check the manual that corresponds to your MySQL
  1                                server version for the right syntax to use near 'ALL' at line 1
  2
  3
  4
(4 rows)
```

`WITH TIES` 도 PG 에만 있다 — **동률까지 함께 가져오는** 지시다.

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

「1행만」이라고 했는데 **2행이 나왔다** — `dept_id = 10` 인 두 행이 동률이라 둘 다 왔다.

| 문법 | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| `LIMIT n` | ✓ | ✓ |
| `LIMIT n OFFSET m` | ✓ | ✓ |
| `LIMIT m, n` (건너뛸 수, 개수) | **`LIMIT #,# syntax is not supported`** | ✓ |
| `OFFSET m` 단독 | ✓ | **`ERROR 1064`** |
| `LIMIT ALL` | ✓ | **`ERROR 1064`** |
| `FETCH FIRST n ROWS ONLY` | ✓ | **`ERROR 1064`** |
| `OFFSET m ROWS FETCH NEXT n ROWS ONLY` | ✓ | **`ERROR 1064`** |
| `FETCH FIRST n ROWS WITH TIES` | ✓ | **`ERROR 1064`** |
| `LIMIT 18446744073709551615 OFFSET m` | **`bigint out of range`** | ✓ (「끝까지」 관용구) |

그림 해설 — **양쪽에서 도는 것은 `LIMIT n [OFFSET m]` 하나뿐이다.**\
대가 — `WITH TIES` 가 없는 엔진에서 같은 요구를 풀려면 윈도우 함수(`RANK`)로 한 겹 감싸야 한다([목록의 **29번 주제**](../29-ranking-functions/)).

---

### 3. ★ `OFFSET` 이 깊어질수록 비싸지는 이유 — 계획으로 본다

**언제 쓰나** — 「뒤쪽 페이지가 느리다」는 말을 들었을 때. **근거는 `actual rows` 한 칸이다.**

20만 행 임시 표(`id` 기본키)에서 같은 10행을 세 방식으로 뽑았다.

```text
--- PG 18.6 : EXPLAIN (ANALYZE, COSTS OFF, TIMING OFF, SUMMARY OFF) ---

=== (A) OFFSET 0 ===
 Limit (actual rows=10.00 loops=1)
   Buffers: local hit=2 read=2
   ->  Index Only Scan using big_pkey on big (actual rows=10.00 loops=1)
         Heap Fetches: 10
         Buffers: local hit=2 read=2

=== (B) OFFSET 100000 ===
 Limit (actual rows=10.00 loops=1)
   Buffers: local hit=4 read=715 written=1
   ->  Index Only Scan using big_pkey on big (actual rows=100010.00 loops=1)
         Heap Fetches: 100010
         Buffers: local hit=4 read=715 written=1

=== (C) 키셋: WHERE id > 100000 ===
 Limit (actual rows=10.00 loops=1)
   Buffers: local hit=4
   ->  Index Only Scan using big_pkey on big (actual rows=10.00 loops=1)
         Index Cond: (id > 100000)
         Heap Fetches: 10
         Buffers: local hit=4
```

```text
--- MySQL 8.4.10 : EXPLAIN ANALYZE ---

=== (A) OFFSET 0 ===
-> Limit: 10 row(s)  (cost=0.0177 rows=10) (actual time=0.268..0.269 rows=10 loops=1)
    -> Covering index scan on big using PRIMARY  (cost=0.0177 rows=10) (actual time=0.0117..0.0127 rows=10 loops=1)

=== (B) OFFSET 100000 ===
-> Limit/Offset: 10/100000 row(s)  (cost=5169 rows=10) (actual time=9.06..9.06 rows=10 loops=1)
    -> Covering index scan on big using PRIMARY  (cost=5169 rows=100010) (actual time=0.364..6.88 rows=100010 loops=1)

=== (C) 키셋 ===
-> Limit: 10 row(s)  (cost=20118 rows=10) (actual time=0.335..0.336 rows=10 loops=1)
    -> Filter: (big.id > 100000)  (cost=20118 rows=100161) (actual time=0.334..0.335 rows=10 loops=1)
        -> Covering index range scan on big using PRIMARY over (100000 < id)  (cost=20118 rows=100161) (actual time=0.329..0.329 rows=10 loops=1)
```

**핵심은 자식 노드의 `actual rows` 다.**

| | 자식 노드가 실제로 만든 행 | 최종 행 |
|---|---|---|
| (A) `OFFSET 0` | **10** | 10 |
| (B) `OFFSET 100000` | **100,010** | 10 |
| (C) 키셋 | **10** | 10 |

그림 해설 — **(B)에서 100,010 행을 만들어 100,000 행을 버렸다.** 「건너뛴다」가 아니라 「만들고 버린다」임이 숫자로 보인다.\
PG 의 `Heap Fetches: 100010`, MySQL 의 노드 이름 `Limit/Offset: 10/100000` 이 같은 이야기를 한다.

시간도 각각 3회씩 재 봤다.

```text
--- PG 18.6 (EXPLAIN ANALYZE, 3회) ---
(B) OFFSET 100000 : Limit (actual time=13.062..13.064)
                    Limit (actual time=10.572..10.573)
                    Limit (actual time=12.893..12.895)
(C) 키셋          : Limit (actual time=0.015..0.017)
                    Limit (actual time=0.016..0.018)
                    Limit (actual time=0.026..0.029)

--- MySQL 8.4.10 (EXPLAIN ANALYZE, 3회) ---
(B) OFFSET 100000 : actual time=9.81..9.81 / 10.2..10.2 / 9.74..9.74
(C) 키셋          : actual time=0.466..0.468 / 0.466..0.468 / 0.355..0.357
```

**신호 대 잡음** — 흔들림은 PG 가 약 20%·MySQL 이 약 5% 인데, (B)와 (C)의 차이는 PG 약 **500배** · MySQL 약 **25배** 다.\
신호가 잡음보다 훨씬 크므로 **방향은 재현된다.** 다만 **절댓값은 이 머신·이 데이터의 것**이고, 읽을 것은 `actual rows` 와 자릿수다.

대가 — 키셋도 공짜가 아니다. **인덱스가 정렬 키를 덮고 있어야** 이 계획이 나온다. 5절에서 그 조건을 본다.

---

### 4. ★ 페이지 사이에 행이 들어오면 — 같은 행이 두 번 나온다

**언제 쓰나** — 사용자가 목록을 넘기는 동안 데이터가 바뀔 때. **즉 운영 중 항상.**

「2행씩」으로 `emp` 를 넘기는데, 1페이지와 2페이지 **사이에** `id = 0` 인 행이 들어왔다고 하자.

```text
1페이지를 읽은 시점               id=0 이 들어온 뒤
 순서: ann(1) bob(2) cho(3) dan(4)   순서: zed(0) ann(1) bob(2) cho(3) dan(4)
        ^^^^^^^^^^^                          ^^^^^^^^^^^^^^^^^
        OFFSET 0 LIMIT 2                     OFFSET 2 LIMIT 2 가 가리키는 자리
        -> ann, bob                          -> bob, cho        <- bob 이 또 나온다
```

PG 에서 트랜잭션 안에 넣고 실행한 결과다(끝에 `ROLLBACK`).

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

--- 같은 시점, 키셋으로 2페이지를 뽑으면 ---
### SQL: SELECT id, name FROM emp WHERE id > 2 ORDER BY id LIMIT 2;
--- PG 18.6 ---
 id | name
----+------
  3 | cho
  4 | dan
(2 rows)
```

MySQL 8.4.10 에서도 **똑같았다** — `OFFSET` 판은 `bob`·`cho`, 키셋 판은 `cho`·`dan`.\
(양쪽 다 `ROLLBACK` 후 `emp` 가 4행인 것을 확인했다.)

**삭제되면 반대 방향의 사고가 난다 — 행이 통째로 사라진다.** 같은 절차에서 `INSERT` 대신 `DELETE` 를 넣었다.

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

--- 같은 시점, 키셋으로 2페이지를 뽑으면 ---
### SQL: SELECT id, name FROM emp WHERE id > 2 ORDER BY id LIMIT 2;
--- PG 18.6 ---
 id | name
----+------
  3 | cho
  4 | dan
(2 rows)
```

MySQL 8.4.10 에서도 **똑같았다** — `OFFSET` 판은 `dan` 한 행, 키셋 판은 `cho`·`dan`.\
(양쪽 다 `ROLLBACK` 후 `emp` 가 4행인 것을 확인했다.)

그림 해설 — **`OFFSET` 은 「몇 번째」를 세는데, 앞쪽이 밀리면 그 번호가 다른 행을 가리킨다.**\
삽입은 **중복**을, 삭제는 **누락**을 만든다. 그리고 **누락 쪽이 더 위험하다** — 화면에 아무 흔적도 안 남는다.\
대가 — 키셋은 「몇 번째」가 아니라 「**내가 어디까지 봤나**」를 기준으로 삼아 두 경우 모두 옳은 페이지를 줬다.

---

### 5. 키셋 페이지네이션 — 「마지막으로 본 키」로 자른다

**언제 쓰나** — 무한 스크롤·다음 버튼·배치 순회. **페이지 번호를 찍어야 하는 화면이 아니면 기본 선택지다.**

```text
OFFSET 방식                            키셋 방식
page1: ORDER BY id LIMIT 2             page1: ORDER BY id LIMIT 2
       -> ann(1), bob(2)                      -> ann(1), bob(2)   마지막 키 = 2
page2: ORDER BY id LIMIT 2 OFFSET 2    page2: WHERE id > 2 ORDER BY id LIMIT 2
       "앞 2개를 만들어 버려라"                "2 다음 자리로 바로 가라"
```

```text
### SQL: SELECT id, name FROM emp WHERE id > 2 ORDER BY id LIMIT 2;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id | name                       +----+------+
----+------                      | id | name |
  3 | cho                        +----+------+
  4 | dan                        |  3 | cho  |
(2 rows)                         |  4 | dan  |
                                 +----+------+
```

**정렬 키가 여러 개면 행 생성자로 한 번에 비교한다.** 양쪽 엔진 모두 된다.

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

그림 해설 — `(dept_id, id) > (10, 1)` 은 **사전식 비교**다. `dept_id` 가 크거나, 같으면서 `id` 가 큰 행이 온다.\
`WHERE dept_id >= 10 AND id > 1` 로 풀어 쓰면 **틀린다** — `dept_id = 20, id = 1` 인 행을 놓친다.\
대가 — **`NULL` 이 든 정렬 키에는 이 비교가 안 통한다.** 위 결과에 `dan`(`dept_id NULL`)이 안 나온 것이 그 증거다 — `(NULL, 4) > (10, 1)` 이 `UNKNOWN` 이라 `WHERE` 가 버렸다([05번](../05-null-comparison-is-distinct-from/)).\
**키셋의 정렬 키는 `NOT NULL` 이어야 한다.**

---

### 6. 정렬이 결정적이지 않으면 페이지네이션이 성립하지 않는다

**언제 쓰나** — 두 방식 어느 쪽을 쓰든. **이 절이 [08번](../08-order-by-null-position-stability/)에 걸리는 지점이다.**

```text
정렬 키가 고유하지 않으면
  page1: ORDER BY dept_id LIMIT 2   ->  ann, bob   (동률 순서는 보장 없음)
  page2: ORDER BY dept_id LIMIT 2 OFFSET 2
         계획이 바뀌어 bob, ann 순이 됐다면
         -> page2 가 cho, dan 이 아니라 다른 것을 줄 수 있다
```

08번에서 **같은 `ORDER BY dept_id` 인데 `ann`·`bob` 의 앞뒤가 뒤집히는 것**을 실측으로 봤다.\
그 위에 `LIMIT`/`OFFSET` 을 얹으면 **경계에 걸친 행이 중복되거나 사라진다.**

`ORDER BY` 자체가 없으면 더하다.

```text
### SQL: SELECT id FROM emp LIMIT 2;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 id                              +----+
----                             | id |
  1                              +----+
  2                              |  1 |
(2 rows)                         |  2 |
                                 +----+
```

지금은 양쪽 다 `1, 2` 를 준다. **그래도 보장이 아니다.** 08번에서 **값을 바꾸지 않는 `UPDATE` 한 번**으로 PG 의 무정렬 순서가 바뀌는 것을 봤다.

그림 해설 — **페이지네이션의 전제는 「전체 순서가 하나로 정해져 있다**」이다.\
대가 — 전제를 세우는 비용은 **정렬 키 맨 뒤에 기본키 한 열**이다. 거의 공짜다.

---

### 7. 키셋이 못 고치는 것

**언제 쓰나** — 키셋으로 바꿀지 결정할 때. **만능이 아니다.**

```text
키셋이 고치는 것                      키셋이 못 고치는 것
+---------------------------+        +---------------------------+
| 깊은 페이지의 비용         |        | "37페이지로 점프"          |
| 페이지 경계에서 행이 밀림   |        | "전체 몇 페이지" 표시       |
| (중복·누락)                |        | 임의 정렬 기준으로 뒤로 가기 |
+---------------------------+        +---------------------------+
```

| | `OFFSET` 방식 | 키셋 방식 |
|---|---|---|
| 깊은 페이지 비용 | **O(건너뛴 행 수)** | 앞쪽과 같다 |
| 페이지 경계 안정성 | **중복·누락 생김** | 안정적 |
| 임의 페이지 점프 | 가능 | **불가** |
| 전체 페이지 수 | `COUNT(*)` 로 가능 | 따로 세야 한다 |
| 정렬 키 조건 | 없음(결정적이기만 하면) | **`NOT NULL` + 인덱스** |

그림 해설 — **UI 가 무엇을 요구하는지가 결정한다.** 무한 스크롤·「다음」 버튼·배치 순회는 키셋이 맞고, 페이지 번호 격자가 필요하면 `OFFSET` 을 쓰되 **깊이를 제한**한다(예: 100페이지까지).\
대가 — 배치 순회에서 `OFFSET` 을 쓰면 **전체 비용이 O(n²)** 이 된다. 10,000페이지를 다 돌면 마지막 페이지에서만 100만 행을 버린다.

## 문법 — 형태와 규칙

```sql
-- 양쪽 엔진에서 도는 유일한 형태
SELECT ... ORDER BY <결정적 정렬 키> LIMIT <개수> [OFFSET <건너뛸 수>]

-- PostgreSQL 전용
... OFFSET <m>                                  -- LIMIT 없이
... LIMIT ALL
... FETCH FIRST <n> ROWS ONLY
... OFFSET <m> ROWS FETCH NEXT <n> ROWS ONLY
... FETCH FIRST <n> ROWS WITH TIES

-- MySQL 전용
... LIMIT <건너뛸 수>, <개수>
```

규칙 여섯.

1. **`LIMIT` 은 8번 칸이다.** 앞 일곱 칸의 일을 줄여 주지 않는다.
2. **`OFFSET` 은 만들고 버린다.** 깊어질수록 만드는 행이 늘어난다 — 계획의 `actual rows` 로 확인된다.
3. **`ORDER BY` 가 결정적이어야** 페이지네이션이 성립한다. 정렬 키 맨 뒤에 고유 열을 더한다.
4. **양쪽에서 도는 문법은 `LIMIT n [OFFSET m]` 하나**다. 나머지는 전부 한쪽 전용이다.
5. **키셋은 「몇 번째」가 아니라 「어디까지 봤나**」로 자른다. 복합 키는 행 생성자 `(a, b) > (x, y)` 로 비교한다.
6. **키셋의 정렬 키는 `NOT NULL` 이어야 한다.** `NULL` 이 섞이면 비교가 `UNKNOWN` 이 되어 행이 사라진다.

## 어디서 틀리나

- **`LIMIT` 을 붙이면 빨라질 거라 믿는다.**\
  8번 칸이다. 정렬은 전부 해야 1등을 안다(인덱스로 순서를 대신할 때만 예외).
- **`OFFSET` 이 「건너뛴다」고 믿는다.**\
  만들고 버린다. `OFFSET 100000` 에서 자식 노드가 **100,010 행**을 만든 것을 계획에서 봤다.
- **뒤쪽 페이지가 느린 원인을 인덱스에서 찾는다.**\
  인덱스는 이미 타고 있다. 원인은 **버리는 행 수**이고, 인덱스를 더 만들어도 안 낫는다.
- **배치 순회에 `OFFSET` 을 쓴다.**\
  전체 비용이 O(n²) 이 된다. 키셋으로 바꾸면 O(n) 이다.
- **페이지 사이에 데이터가 안 바뀐다고 가정한다.**\
  1페이지와 2페이지 사이에 한 행이 들어오면 **`bob` 이 두 번** 나오는 것을 봤다. 삭제되면 한 행이 조용히 건너뛰어진다.
- **정렬 키가 고유하지 않은 채 페이지를 나눈다.**\
  동률 순서는 보장이 없다([08번](../08-order-by-null-position-stability/)). 경계에 걸친 행이 중복되거나 사라진다.
- **`ORDER BY` 없이 `LIMIT` 을 쓴다.**\
  「지금 잘 나온다」는 보장이 아니다. PG 에서는 `UPDATE` 한 번으로 순서가 바뀐다.
- **키셋 조건을 `WHERE a >= x AND b > y` 로 푼다.**\
  틀린다. `(a, b) > (x, y)` 는 **사전식 비교**라서 `a > x` 인 모든 행도 포함해야 한다.
- **키셋의 정렬 키에 `NULL` 이 들어갈 수 있는 열을 쓴다.**\
  `(NULL, 4) > (10, 1)` 이 `UNKNOWN` 이라 그 행이 사라진다.
- **`FETCH FIRST` 를 MySQL 에 쓴다.**\
  `ERROR 1064` 다. 반대로 `LIMIT 1, 2` 는 PG 가 **`LIMIT #,# syntax is not supported`** 로 막는다.

## 구현 세부사항 대 언어 보장

| 항목 | 누가 보장하나 | 근거 |
|---|---|---|
| `LIMIT` 이 8번 칸인 것 | **양쪽 문서가 정한 순서** | 두 엔진 동일 출력 |
| `OFFSET` 이 만들고 버리는 것 | **결과의 정의에서 따라 나온다** | `actual rows=100010` |
| 키셋 결과가 같은 페이지를 주는 것 | **`WHERE` 조건의 의미** | 두 엔진 동일 출력 |
| 행 생성자 비교 `(a,b) > (x,y)` | **양쪽 문서가 정한 규칙** | 두 엔진 동일 출력 |
| `FETCH FIRST`·`LIMIT m,n`·`LIMIT ALL`·`OFFSET` 단독 | **각 엔진의 문법** | 상대 엔진에서 `ERROR 1064` / `not supported` |
| 계획에 `Index Only Scan` 이 뜨는 것 | **옵티마이저 구현** | 통계·인덱스에 따라 달라진다 |
| 측정된 시간(10ms 대 0.02ms) | **이 머신·이 데이터** | 자릿수만 재현된다 |

정리하면 — **「`LIMIT` 이 마지막 칸」과 「`OFFSET` 은 만들고 버린다」만 언어 보장이고, 문법 표면과 비용의 절댓값은 전부 엔진·환경이다.**

## 언제 쓰고 언제 안 쓰나

- **무한 스크롤·「다음」 버튼·배치 순회 → 키셋.** 깊이와 무관하게 비용이 같고 경계가 안정적이다.
- **페이지 번호 격자가 UI 요구사항이면 `OFFSET`.** 대신 **깊이를 제한**한다(「100페이지 이후는 검색을 좁혀 주세요」).
- **정렬 키 맨 뒤에 기본키를 붙인다.** 두 방식 모두의 전제다.
- **키셋의 정렬 키는 `NOT NULL` + 인덱스가 있는 열로 고른다.** 없으면 키셋이 안 서거나 조용히 행을 빠뜨린다.
- **이식이 필요하면 `LIMIT n OFFSET m` 만 쓴다.** `FETCH FIRST`·`LIMIT m,n` 은 한쪽 전용이다.
- **「전체 몇 건」이 꼭 필요한지 묻는다.** `COUNT(*)` 는 페이지마다 다시 세면 그 자체가 비싸다 — 근사값이나 「100+ 건」 표시로 끝나는 경우가 많다.

## 핵심 문장

- `LIMIT` 은 **여덟 번째 칸**이다. 앞의 일을 줄여 주지 않는다.
- **`OFFSET` 은 건너뛰는 게 아니라 만들고 버린다** — `OFFSET 100000` 에서 자식 노드가 **100,010 행**을 만들었다.
- 그래서 **깊은 페이지의 비용은 인덱스로 못 고친다.** 버리는 행 수가 원인이다.
- **페이지 사이에 행이 들어오면 같은 행이 두 번 나온다** — 삭제되면 조용히 건너뛴다.
- **키셋은 「몇 번째」가 아니라 「어디까지 봤나**」로 자른다. 깊이와 무관하게 `actual rows` 가 10이었다.
- **전제는 결정적 정렬**이다 — 정렬 키 맨 뒤에 고유 열을 더한다([08번](../08-order-by-null-position-stability/)).
- **양쪽에서 도는 문법은 `LIMIT n [OFFSET m]` 하나**다.

## 관련 자료

- [PostgreSQL 18 · SELECT](https://www.postgresql.org/docs/18/sql-select.html) — `LIMIT`·`OFFSET`·`FETCH` 가 같은 페이지에 있다.
- [MySQL 8.4 · LIMIT Optimization](https://dev.mysql.com/doc/refman/8.4/en/limit-optimization.html)
- [08 ORDER BY](../08-order-by-null-position-stability/) — **경계: 그쪽은 「순서가 어떻게 정해지나」까지, 여기는 그 순서 위에서 페이지를 자를 때 무엇이 깨지나부터.** 이 주제의 전제가 그쪽에 있다.
- [01 논리적 질의 처리 순서](../01-logical-query-processing-order/) — **경계: 그쪽은 `LIMIT` 이 8번 칸이라는 것까지, 여기는 그래서 비용이 어디서 나나부터.**
- [05 NULL 비교](../05-null-comparison-is-distinct-from/) — 키셋 조건에 `NULL` 이 끼면 `UNKNOWN` 이 되어 행이 사라진다.
- [07 DISTINCT 와 중복 제거](../07-distinct-and-duplicate-removal/) — `DISTINCT` 는 6번 칸, `LIMIT` 은 8번 칸이라 **접은 뒤에** 자른다.
- **`EXPLAIN` 읽기**는 목록의 **58·60번 주제**, **인덱스를 언제 타나**는 **46·47번 주제**, **`WITH TIES` 를 대신할 순위 함수**는 [**29번 주제**](../29-ranking-functions/)가 정본이다. 여기서는 계획을 **「몇 행을 만들었나」 한 칸만** 읽는다.
- [SQL 주제 목록](../README.md)

## 용어 풀이

- **`LIMIT`** — 결과의 앞 n 행만 내보내라는 지시. 논리적 처리 순서의 마지막 칸이다.\
  예: `ORDER BY id LIMIT 2` 는 정렬을 다 한 뒤 앞 2행을 준다.
- **`OFFSET`** — 앞의 n 행을 **만들고 버리는** 지시.\
  예: `LIMIT 10 OFFSET 100000` 은 100,010 행을 만든 뒤 10행만 남긴다.
- **키셋 페이지네이션(keyset pagination)** — 「마지막으로 본 행의 키」를 조건으로 다음 페이지를 뽑는 방식.\
  예: `WHERE id > 2 ORDER BY id LIMIT 2`. seek method 라고도 부른다.
- **결정적 정렬(deterministic order)** — 같은 데이터면 언제나 같은 순서가 나오는 정렬.\
  예: `ORDER BY dept_id, id`. 페이지네이션의 전제다.
- **행 생성자(row constructor)** — 여러 값을 묶어 「행 값」 하나로 만드는 표기.\
  예: `(dept_id, id) > (10, 1)` 은 사전식으로 한 번에 비교한다.
- **사전식 비교(lexicographic comparison)** — 앞 항목부터 견주고, 같으면 다음 항목을 보는 비교.\
  예: `(20, 1) > (10, 999)` 는 참이다. 첫 항목에서 이미 갈렸다.
- **`actual rows`** — `EXPLAIN ANALYZE` 가 찍는, 그 노드가 **실제로 만들어 낸 행 수**.\
  예: `OFFSET 100000` 판에서 자식 노드가 100,010 이었다.
- **`Index Only Scan`** — 표를 안 보고 인덱스만 읽어 답하는 PG 의 접근 방식.\
  예: `id` 만 뽑는 질의에서 기본키 인덱스로 끝났다.
- **`WITH TIES`** — 마지막 행과 동률인 행들을 함께 가져오라는 지시. PG 에만 있다.\
  예: `FETCH FIRST 1 ROWS WITH TIES` 가 동률 때문에 2행을 줬다.

## 더 들어가면

- **`OFFSET` 비용의 정확한 모양은 O(offset + limit) 이다.** 페이지 번호에 비례해 선형으로 늘고, **전체를 순회하면 O(n²)** 이 된다. 「마지막 페이지가 유독 느리다」가 아니라 「페이지 번호에 비례해 느려진다」가 맞는 서술이고, 그래서 **중간 페이지에서도 이미 느리다.**
- **키셋은 인덱스가 정렬 순서를 그대로 갖고 있어야 값이 나온다.** `ORDER BY created_at DESC, id DESC` 로 페이지를 넘긴다면 `(created_at DESC, id DESC)` 복합 인덱스가 있어야 한다. 인덱스 열 순서와 방향이 안 맞으면 **키셋을 써도 전체를 훑는다** — 계획을 한 번은 찍어 봐야 하는 이유다(목록의 [**46**](../46-index-definition-composite-partial-expression/)·[**47**](../47-when-indexes-are-used/)·[**58**](../58-explain-plan-tree/)번 주제).
- **커서 토큰을 노출할 때의 주의** — 키셋의 「마지막 키」를 그대로 URL 에 실으면 내부 식별자가 새어 나간다. 실무에서는 정렬 키 값을 인코딩해 불투명한 커서 문자열로 만든다. **암호화가 아니라 난독화라는 점**은 분명히 해 둬야 한다 — 권한 검사는 여전히 서버가 한다.
