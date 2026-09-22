# sql/29-순위 함수 — `ROW_NUMBER`·`RANK`·`DENSE_RANK`·`NTILE` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력·에러는 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 지어낸 출력은 없다.\
> 모든 질의는 [1-question.md](1-question.md) 머리의 `WITH emp8 AS (...)` CTE 를 앞에 붙여 돌렸다.\
> 문서 근거는 [PG 18 Window Functions](https://www.postgresql.org/docs/18/functions-window.html) · [MySQL 8.4 Window Function Descriptions](https://dev.mysql.com/doc/refman/8.4/en/window-function-descriptions.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 1. `rk` = `1 1 3 3 3 6 6` · `drk` = `1 1 2 2 2 3 3` — `RANK` 는 **내 앞의 사람 수**를 센다

**출력**

```text
### SQL: SELECT name, salary, ROW_NUMBER() OVER w AS rn, RANK() OVER w AS rk,
                DENSE_RANK() OVER w AS drk, NTILE(3) OVER w AS nt
         FROM emp8 WHERE salary IS NOT NULL
         WINDOW w AS (ORDER BY salary DESC) ORDER BY salary DESC, id;
--- PG 18.6 ---
 name | salary | rn | rk | drk | nt
------+--------+----+----+-----+----
 bob  |    500 |  1 |  1 |   1 |  1
 fay  |    500 |  2 |  1 |   1 |  1
 dan  |    400 |  5 |  3 |   2 |  2
 gus  |    400 |  3 |  3 |   2 |  1
 hui  |    400 |  4 |  3 |   2 |  2
 ann  |    300 |  7 |  6 |   3 |  3
 eve  |    300 |  6 |  6 |   3 |  3
(7 rows)
--- MySQL 8.4.10 ---
+------+--------+----+----+-----+----+
| name | salary | rn | rk | drk | nt |
+------+--------+----+----+-----+----+
| bob  |    500 |  1 |  1 |   1 |  1 |
| fay  |    500 |  2 |  1 |   1 |  1 |
| dan  |    400 |  3 |  3 |   2 |  1 |
| gus  |    400 |  4 |  3 |   2 |  2 |
| hui  |    400 |  5 |  3 |   2 |  2 |
| ann  |    300 |  6 |  6 |   3 |  3 |
| eve  |    300 |  7 |  6 |   3 |  3 |
+------+--------+----+----+-----+----+
```

**왜 그런가**

```text
       500  500 | 400  400  400 | 300  300
RANK   :  1    1 |   3    3    3 |   6    6
             내 앞에 몇 명 있나 + 1
             400 앞에는 2명  -> 3
             300 앞에는 5명  -> 6     (4·5 가 비는 이유)

DENSE  :  1    1 |   2    2    2 |   3    3
             내 앞에 몇 "종류" 있나 + 1
             400 앞에는 500 한 종류 -> 2
             300 앞에는 500·400 두 종류 -> 3
```

★ **`rk`·`drk` 는 두 엔진에서 한 자리도 안 다르다.** `rn`·`nt` 는 갈렸다 — 3번이 그 이유를 판다.

> **순위 함수(ranking function)** — 값이 아니라 줄 선 자리로 결과를 내는 윈도우 함수.\
> 예: `RANK() OVER (ORDER BY salary DESC)`. `OVER` 없이는 못 쓴다.

---

### 2. `RANK <= 3` 이면 **5명**, `DENSE_RANK <= 3` 이면 **7명 전부**

```text
        bob fay dan gus hui ann eve
RANK  :   1   1   3   3   3   6   6      <= 3 인 사람: bob fay dan gus hui  -> 5명
DENSE :   1   1   2   2   2   3   3      <= 3 인 사람: 일곱 명 전부         -> 7명
```

★ **같은 한국어 문장이 두 가지 SQL 이 되고, 답이 5와 7로 갈린다.**\
애매한 것은 함수가 아니라 **요구**다. 「3등까지」를 받으면 이렇게 되물어야 한다 —

- **동점자가 나오면 몇 명까지 주나?** (`RANK` 면 동점자를 다 주고 그만큼 뒤가 밀린다)
- **「3등」이 사람의 등수인가 값의 등급인가?** (값의 등급이면 `DENSE_RANK` 다)

★ **랭킹의 도메인 규칙은 여기가 정본이 아니다.**\
동점 정책·재집계·보상 배분은 [`domain-modeling/basic/24-leaderboard`](../../../../../domain-modeling/basic/24-leaderboard/)와 [`advanced/19-leaderboard-recount`](../../../../../domain-modeling/advanced/19-leaderboard-recount/)가 다룬다.\
**여기는 함수가 무엇을 돌려주는지까지**다.

---

### 3. 한 엔진 안에서는 10회가 전부 같았다 — **그런데 두 엔진의 답이 다르다**

**출력**

```text
### SQL: SELECT name, ROW_NUMBER() OVER (ORDER BY salary DESC) AS rn FROM emp8 WHERE salary IS NOT NULL;
         (결과를 한 줄로 이어 붙여 10회 비교)
--- PG 18.6 · 10회 ---
bob:1 fay:2 gus:3 hui:4 dan:5 eve:6 ann:7      <- 10회 전부 같았다
--- MySQL 8.4.10 · 10회 ---
bob:1 fay:2 dan:3 gus:4 hui:5 ann:6 eve:7      <- 10회 전부 같았다
```

**왜 그런가**

```text
ORDER BY salary DESC 가 말한 것        말하지 않은 것
"500 > 400 > 300"                     gus·hui·dan 중 누가 먼저인가
                                       ann·eve 중 누가 먼저인가
                                       ^^^^^^^^^^^^^^^^^^^^^^^^^
                                ROW_NUMBER 는 이걸 알아야 번호를 매긴다
                                -> 질의문이 안 정했으니 엔진이 정한다
```

★ **「10회 같았다」는 보장이 아니다.** 같은 계획을 열 번 쓴 것뿐이다.\
**반증은 엔진을 바꿨을 때 나왔다** — `gus`·`hui`·`dan` 의 자리와 `ann`·`eve` 의 자리가 서로 다르다.

**입력 순서를 바꾸면 한 엔진 안에서도 뒤집힌다.**

```text
### SQL: SELECT name, salary, ROW_NUMBER() OVER (ORDER BY salary DESC) AS rn
         FROM (SELECT * FROM emp8 WHERE salary IS NOT NULL ORDER BY name DESC LIMIT 7) t ORDER BY rn;
--- PG 18.6 ---
 name | salary | rn
------+--------+----
 bob  |    500 |  1
 fay  |    500 |  2
 gus  |    400 |  3
 hui  |    400 |  4
 dan  |    400 |  5
 eve  |    300 |  6
 ann  |    300 |  7
(7 rows)
--- MySQL 8.4.10 ---
+------+--------+----+
| name | salary | rn |
+------+--------+----+
| fay  |    500 |  1 |
| bob  |    500 |  2 |
| hui  |    400 |  3 |
| gus  |    400 |  4 |
| dan  |    400 |  5 |
| eve  |    300 |  6 |
| ann  |    300 |  7 |
+------+--------+----+
```

★ **이 실험은 한쪽에서만 결론이 선다 — 그래서 그렇게 적는다.**

| 엔진 | 10회 반복 | 입력 순서 바꾸기 | 그 엔진 안에서 반증이 났나 |
|---|---|---|---|
| PG 18.6 | 전부 같음 | **기본 판과 같음** | **안 났다** |
| MySQL 8.4.10 | 전부 같음 | **`bob`/`fay`·`gus`/`hui` 가 뒤집혔다** | **났다** |

**한 엔진 안의 반증은 MySQL 쪽에서만 나왔다.** PG 는 세 판이 전부 같았다.\
결론이 서는 근거는 **두 엔진의 기본 판이 이미 다르다는 것**이고, 입력 순서 실험은 **MySQL 에서만** 그것을 보강한다.

「PG 는 안정적이다」라고 읽으면 안 된다 — **관찰이 세 판뿐**이고, 계획이 바뀌면(인덱스·병렬) 달라질 수 있다.

> **비결정적(non-deterministic)** — 같은 질의·같은 데이터인데 답이 하나로 정해지지 않는 것.\
> 예: 동률이 있고 고유 키가 없는 `ROW_NUMBER`.

---

### 4. 조건은 **동률**과 **고유 키 없음** 둘 다 — `RANK` 는 순서를 알 필요가 없다

```text
ROW_NUMBER 가 비결정적이 되는 조건 (둘 다 성립해야 한다)
  (1) 윈도우 ORDER BY 기준에 같은 값이 있다        -> 동률이 생긴다
  (2) ORDER BY 에 그 동률을 깨는 고유 키가 없다     -> 순서가 안 정해진다

RANK / DENSE_RANK 는
  동률에 "같은 값" 을 준다 -> 동률 안의 순서가 답에 안 들어간다 -> 항상 결정적이다
```

★ **[28번](../28-window-frames-rows-range-groups/) 3번의 `ROWS` 대 `RANGE` 와 똑같은 구조**다.

| | 무엇을 세나 | 동률 안의 순서가 필요한가 | 결정적인가 |
|---|---|---|---|
| `ROW_NUMBER` · `ROWS` 프레임 | **행** | 필요하다 | **아니다** |
| `RANK`·`DENSE_RANK` · `RANGE` 프레임 | **값** | 필요 없다 | 그렇다 |

**「행을 세느냐 값을 보느냐」** 한 줄이 두 주제를 함께 설명한다.\
뿌리는 [08번](../08-order-by-null-position-stability/) 5번 — **동률의 순서는 아무도 보장하지 않는다.**

---

### 5. `ORDER BY` 에 **고유 키를 더한다** — `ORDER BY salary DESC, id`

**출력**

```text
### SQL: SELECT name, salary, ROW_NUMBER() OVER (ORDER BY salary DESC, id) AS rn
         FROM emp8 WHERE salary IS NOT NULL ORDER BY rn;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | salary | rn              +------+--------+----+
------+--------+----             | name | salary | rn |
 bob  |    500 |  1              +------+--------+----+
 fay  |    500 |  2              | bob  |    500 |  1 |
 dan  |    400 |  3              | fay  |    500 |  2 |
 gus  |    400 |  4              | dan  |    400 |  3 |
 hui  |    400 |  5              | gus  |    400 |  4 |
 ann  |    300 |  6              | hui  |    400 |  5 |
 eve  |    300 |  7              | ann  |    300 |  6 |
(7 rows)                         | eve  |    300 |  7 |
                                 +------+--------+----+
```

「부서별 최고 연봉자 한 명」은 이렇게 쓴다.

```sql
WITH ranked AS (
  SELECT dept_id, name, salary,
         ROW_NUMBER() OVER (PARTITION BY dept_id ORDER BY salary DESC, id) AS rn
  FROM emp8 WHERE salary IS NOT NULL
)
SELECT dept_id, name, salary FROM ranked WHERE rn = 1;
```

★ **`, id` 여섯 글자가 두 엔진을 같게 만들었다.** [08번](../08-order-by-null-position-stability/) 5번의 처방과 같은 것이다.

★ **고유 키를 고를 때도 판단이 있다.** `id` 로 끊으면 「동점이면 먼저 입사한 사람」이라는 **정책이 생긴 것**이다.\
아무 열이나 넣어 에러를 없애는 게 아니라, **어느 정책이 맞는지 정하고 그 열을 넣는다.**

★ **`WHERE rn = 1` 이 바깥 질의에 있어야 한다.** 윈도우 결과는 같은 질의의 `WHERE` 에서 못 거른다([31번](../31-window-evaluation-timing/)).

---

### 6. `NTILE(3)` → **3·3·2** · `NTILE(5)` → **2·2·2·1·1** — 나머지는 **앞 조**에 붙는다

**출력**

```text
### SQL: SELECT name, salary, NTILE(3) OVER (ORDER BY id) AS nt, NTILE(4) OVER (ORDER BY id) AS nt4,
                NTILE(5) OVER (ORDER BY id) AS nt5
         FROM emp8 ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | salary | nt | nt4 | nt5  +------+--------+----+-----+-----+
------+--------+----+-----+----- | name | salary | nt | nt4 | nt5 |
 ann  |    300 |  1 |   1 |   1  +------+--------+----+-----+-----+
 bob  |    500 |  1 |   1 |   1  | ann  |    300 |  1 |   1 |   1 |
 cho  |   NULL |  1 |   2 |   2  | bob  |    500 |  1 |   1 |   1 |
 dan  |    400 |  2 |   2 |   2  | cho  |   NULL |  1 |   2 |   2 |
 eve  |    300 |  2 |   3 |   3  | dan  |    400 |  2 |   2 |   2 |
 fay  |    500 |  2 |   3 |   3  | eve  |    300 |  2 |   3 |   3 |
 gus  |    400 |  3 |   4 |   4  | fay  |    500 |  2 |   3 |   3 |
 hui  |    400 |  3 |   4 |   5  | gus  |    400 |  3 |   4 |   4 |
(8 rows)                         | hui  |    400 |  3 |   4 |   5 |
                                 +------+--------+----+-----+-----+
```

**왜 그런가**

```text
8행 3조 : 8 = 3*2 + 2  -> 앞 두 조에 하나씩 더  -> 3 · 3 · 2
8행 4조 : 8 = 4*2 + 0  -> 나머지 없음          -> 2 · 2 · 2 · 2
8행 5조 : 8 = 5*1 + 3  -> 앞 세 조에 하나씩 더  -> 2 · 2 · 2 · 1 · 1
```

★ **나머지는 뒤가 아니라 앞에 붙는다.** PG 문서는 *"dividing the partition as equally as possible"* 까지만 적으므로\
**「가능한 한 고르게」의 구체적 배분은 실행으로 확인한 것**이다. 두 엔진이 한 자리도 안 갈렸다.

★ **`ORDER BY id`(고유 키)를 썼기 때문에 두 엔진이 같았다.** 1번처럼 `ORDER BY salary DESC` 로 하면\
조의 **크기**는 같아도 **누가 어느 조인지**가 갈린다 — 그 출력이 1번의 `nt` 열이다.

---

### 7. 앞에서부터 한 행씩 들어가고 **9~20조는 결과에 안 나온다**

**출력**

```text
### SQL: SELECT name, salary, NTILE(20) OVER (ORDER BY id) AS nt FROM emp8 ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | salary | nt              +------+--------+----+
------+--------+----             | name | salary | nt |
 ann  |    300 |  1              +------+--------+----+
 bob  |    500 |  2              | ann  |    300 |  1 |
 cho  |   NULL |  3              | bob  |    500 |  2 |
 dan  |    400 |  4              | cho  |   NULL |  3 |
 eve  |    300 |  5              | dan  |    400 |  4 |
 fay  |    500 |  6              | eve  |    300 |  5 |
 gus  |    400 |  7              | fay  |    500 |  6 |
 hui  |    400 |  8              | gus  |    400 |  7 |
(8 rows)                         | hui  |    400 |  8 |
                                 +------+--------+----+
```

**왜 그런가 — 그리고 결과만 봐서는 모른다**

```text
조가 20개인데 행이 8개
  -> 1~8조에 한 행씩
  -> 9~20조는 빈 조 -> 행이 없으니 결과에 나타날 방법이 없다

화면에 보이는 것: nt 가 1..8         <- 아무 이상이 없어 보인다
화면에 없는 것  : "12개 조가 비었다"  <- 아무도 말해 주지 않는다
```

★ **에러도 경고도 없다.** 「20분위로 나눴다」고 적어 놓고 실제로는 8개 조뿐인 것을 **결과만으로는 알 수 없다.**\
드러내려면 **`MAX(nt)` 나 `COUNT(*)` 를 같이 뽑아** 조 개수를 확인해야 한다.

★ **조 개수가 파라미터로 들어오는 코드에서 위험하다.** 데이터가 적은 날만 조용히 이상해진다 —\
[04번](../04-null-three-valued-logic/)·[21번](../21-aggregate-functions-count-forms/)에서 본 것과 같은 성격의 **무음 실패**다.

---

### 8. 셋이 서로 다른 방식으로 갈린다 — **MySQL 은 파서가, PG 는 식으로 받는다**

**출력**

```text
### SQL: SELECT name, salary, NTILE(0) OVER (ORDER BY salary) AS nt FROM emp8;
--- PG 18.6 ---
ERROR:  argument of ntile must be greater than zero
--- MySQL 8.4.10 ---
ERROR 1210 (HY000) at line 1: Incorrect arguments to ntile
```

```text
### SQL: SELECT name, salary, NTILE(-1) OVER (ORDER BY salary) AS nt FROM emp8;
--- PG 18.6 ---
ERROR:  argument of ntile must be greater than zero
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near '-1) OVER (ORDER BY salary) AS nt FROM emp8' at line 7
```

```text
### SQL: SELECT name, salary, NTILE(NULL) OVER (ORDER BY salary) AS nt FROM emp8;
--- PG 18.6 ---
 name | salary |  nt
------+--------+------
 ann  |    300 | NULL
 eve  |    300 | NULL
 dan  |    400 | NULL
 hui  |    400 | NULL
 gus  |    400 | NULL
 fay  |    500 | NULL
 bob  |    500 | NULL
 cho  |   NULL | NULL
(8 rows)
--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near 'NULL) OVER (ORDER BY salary) AS nt FROM emp8' at line 7
```

**왜 그런가**

| 인자 | PG 18.6 | MySQL 8.4.10 | 어디서 걸리나 |
|---|---|---|---|
| `0` | `argument of ntile must be greater than zero` | `ERROR 1210` 잘못된 인자 | **둘 다 실행 단계** |
| `-1` | 같은 `ERROR`(0과 동일) | **`ERROR 1064` 문법 오류** | PG 는 실행, **MySQL 은 파서** |
| `NULL` | **돈다 — 전 행이 `NULL`** | **`ERROR 1064` 문법 오류** | PG 는 값으로, **MySQL 은 파서** |

★ **MySQL 의 파서는 `NTILE` 자리에 「부호 없는 정수 리터럴」만 받는다.** `-1` 도 `NULL` 도 **문법**에서 막힌다.\
PG 는 그 자리를 **식**으로 받으므로 `NULL` 이 들어오면 계산해서 **전 행에 `NULL`** 을 돌려준다.

★ **PG 쪽이 더 위험하다.** 조 개수를 파라미터로 받는 코드에 `NULL` 이 흘러 들어오면\
**에러 없이 조 번호가 통째로 `NULL`** 이 된다 — 7번과 같은 무음 실패다.\
「엄격한 쪽이 불편하다」가 아니라 「**막아 주는 쪽이 안전하다**」로 읽어야 하는 자리다.

`NTILE` 은 값이 아니라 **순서**로 조를 나누므로 `cho`(salary `NULL`)도 조에 들어간다 — 어느 조인지는 9번의 `NULL` 위치가 정한다.

---

### 9. `cho` 는 PG 에서 **1등**, MySQL 에서 **8등** — `bob` 은 **2등**과 **1등**이다

**출력**

```text
### SQL: SELECT name, salary, ROW_NUMBER() OVER w AS rn, RANK() OVER w AS rk,
                DENSE_RANK() OVER w AS drk, NTILE(3) OVER w AS nt
         FROM emp8 WINDOW w AS (ORDER BY salary DESC) ORDER BY salary DESC, id;
--- PG 18.6 ---
 name | salary | rn | rk | drk | nt
------+--------+----+----+-----+----
 cho  |   NULL |  1 |  1 |   1 |  1
 bob  |    500 |  2 |  2 |   2 |  1
 fay  |    500 |  3 |  2 |   2 |  1
 dan  |    400 |  6 |  4 |   3 |  2
 gus  |    400 |  4 |  4 |   3 |  2
 hui  |    400 |  5 |  4 |   3 |  2
 ann  |    300 |  8 |  7 |   4 |  3
 eve  |    300 |  7 |  7 |   4 |  3
(8 rows)
--- MySQL 8.4.10 ---
+------+--------+----+----+-----+----+
| name | salary | rn | rk | drk | nt |
+------+--------+----+----+-----+----+
| bob  |    500 |  1 |  1 |   1 |  1 |
| fay  |    500 |  2 |  1 |   1 |  1 |
| dan  |    400 |  3 |  3 |   2 |  1 |
| gus  |    400 |  4 |  3 |   2 |  2 |
| hui  |    400 |  5 |  3 |   2 |  2 |
| ann  |    300 |  6 |  6 |   3 |  2 |
| eve  |    300 |  7 |  6 |   3 |  3 |
| cho  |   NULL |  8 |  8 |   4 |  3 |
+------+--------+----+----+-----+----+
```

**왜 그런가**

```text
ORDER BY salary DESC

PG   : NULL 을 "가장 큰 값" 으로 본다   -> DESC 에서 맨 앞  -> cho 가 1등
MySQL: NULL 을 "가장 작은 값" 으로 본다 -> DESC 에서 맨 뒤  -> cho 가 8등

그 한 행 때문에 PG 에서는 모든 등수가 하나씩 밀린다
  bob : PG 2등 / MySQL 1등
  ann : PG 7등 / MySQL 6등
```

★★ **「최고 연봉자」를 뽑는 질의가 PG 에서는 급여가 없는 사람을 뽑는다.** 에러도 경고도 없다.

뿌리는 [08번](../08-order-by-null-position-stability/)의 `NULL` 위치 규칙 하나이고, 그것이 창 안으로 그대로 들어왔다([27번](../27-partition-by-and-window-order-by/) 6번).

**고치는 법 둘.**

```sql
-- (1) 순위에서 빼는 것이 요구에 맞으면 — 가장 정직하다
... FROM emp8 WHERE salary IS NOT NULL

-- (2) 남겨야 하면 NULL 을 맨 뒤로 고정한다 (두 엔진 모두에서 돈다)
RANK() OVER (ORDER BY (salary IS NULL), salary DESC)
```

★ PG 의 `NULLS LAST` 는 **MySQL 에서 `ERROR 1064`** 다. 이식할 질의에는 `(열 IS NULL)` 키를 쓴다([08번](../08-order-by-null-position-stability/) 3번).

---

### 10. `ROW_NUMBER` 면 **3행**, `RANK` 면 **5행**

**출력**

```text
### SQL: WITH ranked AS (SELECT dept_id, name, salary,
                ROW_NUMBER() OVER (PARTITION BY dept_id ORDER BY salary DESC, id) AS rn
                FROM emp8 WHERE salary IS NOT NULL)
         SELECT dept_id, name, salary FROM ranked WHERE rn = 1 ORDER BY (dept_id IS NULL), dept_id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | name | salary         +---------+------+--------+
---------+------+--------        | dept_id | name | salary |
      10 | bob  |    500         +---------+------+--------+
      20 | gus  |    400         |      10 | bob  |    500 |
    NULL | dan  |    400         |      20 | gus  |    400 |
(3 rows)                         |    NULL | dan  |    400 |
                                 +---------+------+--------+
```

```text
### SQL: WITH ranked AS (SELECT dept_id, name, salary,
                RANK() OVER (PARTITION BY dept_id ORDER BY salary DESC) AS rk
                FROM emp8 WHERE salary IS NOT NULL)
         SELECT dept_id, name, salary, rk FROM ranked WHERE rk = 1 ORDER BY (dept_id IS NULL), dept_id, name;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 dept_id | name | salary | rk    +---------+------+--------+----+
---------+------+--------+---    | dept_id | name | salary | rk |
      10 | bob  |    500 |  1    +---------+------+--------+----+
      10 | fay  |    500 |  1    |      10 | bob  |    500 |  1 |
      20 | gus  |    400 |  1    |      10 | fay  |    500 |  1 |
      20 | hui  |    400 |  1    |      20 | gus  |    400 |  1 |
    NULL | dan  |    400 |  1    |      20 | hui  |    400 |  1 |
(5 rows)                         |    NULL | dan  |    400 |  1 |
                                 +---------+------+--------+----+
```

**왜 그런가**

```text
sales : bob(500) fay(500)  <- 동률
dev   : gus(400) hui(400)  <- 동률   (cho 는 salary NULL 이라 제외됐다)
NULL  : dan(400)

ROW_NUMBER = 1 : 부서마다 정확히 한 행 -> 3행
RANK       = 1 : 동률을 다 남긴다      -> 2+2+1 = 5행
```

★ **「부서별 1위」라는 같은 말이 3행도 되고 5행도 된다.** 요구가 어느 쪽인지 먼저 정한다.

★ **`ROW_NUMBER` 쪽에 `, id` 를 넣었다.** 안 넣으면 `bob` 이 올지 `fay` 가 올지 정해지지 않는다(3번).\
「한 행만」이 요구라면 **어느 한 행인지도 요구가 정해야** 한다 — 안 정하면 엔진이 몰래 정한다.

★ **두 질의 모두 결과가 두 엔진에서 같다.** `, id` 와 `WHERE salary IS NOT NULL` 이 갈릴 자리를 둘 다 막았기 때문이다.

---

### 11. 에러가 아니고 **값도 안 바뀐다** — 순위 함수는 프레임을 무시한다

**출력**

```text
### SQL: SELECT name, salary, RANK() OVER (ORDER BY salary) AS plain,
                RANK() OVER (ORDER BY salary ROWS UNBOUNDED PRECEDING) AS framed,
                ROW_NUMBER() OVER (ORDER BY salary ROWS UNBOUNDED PRECEDING) AS rn_framed
         FROM emp8 WHERE salary IS NOT NULL ORDER BY salary, id;
--- PG 18.6 ---
 name | salary | plain | framed | rn_framed
------+--------+-------+--------+-----------
 ann  |    300 |     1 |      1 |         2
 eve  |    300 |     1 |      1 |         1
 dan  |    400 |     3 |      3 |         3
 gus  |    400 |     3 |      3 |         5
 hui  |    400 |     3 |      3 |         4
 bob  |    500 |     6 |      6 |         7
 fay  |    500 |     6 |      6 |         6
(7 rows)
--- MySQL 8.4.10 ---
+------+--------+-------+--------+-----------+
| name | salary | plain | framed | rn_framed |
+------+--------+-------+--------+-----------+
| ann  |    300 |     1 |      1 |         1 |
| eve  |    300 |     1 |      1 |         2 |
| dan  |    400 |     3 |      3 |         3 |
| gus  |    400 |     3 |      3 |         4 |
| hui  |    400 |     3 |      3 |         5 |
| bob  |    500 |     6 |      6 |         6 |
| fay  |    500 |     6 |      6 |         7 |
+------+--------+-------+--------+-----------+
```

**왜 그런가**

```text
plain 과 framed 가 두 엔진 모두에서 한 자리도 안 다르다
 -> 프레임 지정이 RANK 의 값에 아무 영향을 주지 않았다
 -> "에러가 아니라 무시된다"
```

PG 문서가 `row_number`·`rank`·`dense_rank`·`percent_rank`·`cume_dist`·`ntile`·`lag`·`lead` 를\
**프레임에 의존하지 않는 함수**로 묶어 적는다.

★ **`rn_framed` 열은 여전히 두 엔진에서 갈린다.** 그건 프레임 때문이 아니라 **동률 순서** 때문이다(3번).\
**「프레임을 의심할 자리」와 「동률을 의심할 자리」를 구분**하는 것이 이 출력의 값이다.

★ 다만 **`FIRST_VALUE`·`LAST_VALUE`·`NTH_VALUE` 는 프레임을 본다** — 그 비대칭이 [30번](../30-offset-and-boundary-functions/)의 함정을 만든다.

---

### 12. `RANK` 는 **전부 1**, `ROW_NUMBER` 는 **1~8 (순서는 보장 없음)**

**출력**

```text
### SQL: SELECT name, salary, RANK() OVER () AS rk, DENSE_RANK() OVER () AS drk,
                ROW_NUMBER() OVER () AS rn
         FROM emp8 ORDER BY id;
--- PG 18.6 ---                  --- MySQL 8.4.10 ---
 name | salary | rk | drk | rn   +------+--------+----+-----+----+
------+--------+----+-----+----  | name | salary | rk | drk | rn |
 ann  |    300 |  1 |   1 |  1   +------+--------+----+-----+----+
 bob  |    500 |  1 |   1 |  2   | ann  |    300 |  1 |   1 |  1 |
 cho  |   NULL |  1 |   1 |  3   | bob  |    500 |  1 |   1 |  2 |
 dan  |    400 |  1 |   1 |  4   | cho  |   NULL |  1 |   1 |  3 |
 eve  |    300 |  1 |   1 |  5   | dan  |    400 |  1 |   1 |  4 |
 fay  |    500 |  1 |   1 |  6   | eve  |    300 |  1 |   1 |  5 |
 gus  |    400 |  1 |   1 |  7   | fay  |    500 |  1 |   1 |  6 |
 hui  |    400 |  1 |   1 |  8   | gus  |    400 |  1 |   1 |  7 |
(8 rows)                         | hui  |    400 |  1 |   1 |  8 |
                                 +------+--------+----+-----+----+
```

**왜 그런가**

```text
ORDER BY 가 없다 -> 비교할 키가 없다 -> 모든 행이 서로의 피어 (28번 2번)

RANK       : "내 앞에 몇 명" -> 아무도 내 앞이 아니다 -> 전부 1
DENSE_RANK : 같은 이유로 전부 1
ROW_NUMBER : 피어여도 번호는 나눠야 한다 -> 1..8
                                          ^^^^
                          그런데 그 순서가 무엇인지는 아무도 안 정했다
```

★ **에러가 아니다.** `RANK() OVER ()` 를 써 놓고 「왜 다 1등이지」라고 묻게 되는 자리다 — `ORDER BY` 를 빠뜨린 것이다.

★ **`ROW_NUMBER() OVER ()` 는 「입력 순서대로 번호를 준다」가 아니다.** 지금 두 엔진이 `1~8` 을 같은 순서로 준 것은\
**관찰이지 보장이 아니다** — 3번과 [28번](../28-window-frames-rows-range-groups/) 11번이 같은 성격의 함정을 다뤘다.

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| 네 함수 나란히 (1번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `rk`·`drk` 는 같고 `rn`·`nt` 는 갈렸다 |
| ★ `ROW_NUMBER` 반복 (3번) | PG 18.6 · MySQL 8.4.10 | **각 10회** | **엔진 안에서는 전부 같고 엔진 간에는 달랐다** |
| ★ 입력 순서 바꾸기 (3번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **MySQL 에서만 뒤집혔다 — 그렇게 적었다** |
| 고유 키를 더한 뒤 (5번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **갈림이 사라졌다** |
| `NTILE` 배분 (6번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | 3·4·5 조를 한 질의에 |
| `NTILE(20)` (7번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **빈 조는 결과에 안 나온다** |
| `NTILE` 인자 (8번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | **에러 다섯 · PG 의 `NTILE(NULL)` 만 돈다** |
| `NULL` 의 순위 (9번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **`cho` 가 1등 대 8등** |
| 그룹별 1위 (10번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | 3행 대 5행 |
| 프레임 무시 (11번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `plain` = `framed` |
| `ORDER BY` 없는 순위 (12번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | `RANK` 전부 1 |
| `PERCENT_RANK`·`CUME_DIST` | PG 18.6 · MySQL 8.4.10 | 각 1회 | 소수점 끝자리까지 같았다(2-summary 「더 들어가면」) |

**구현 의존 항목** — **동률에서 `ROW_NUMBER`·`NTILE` 이 누구에게 어느 번호를 주나**와 **`NULL` 의 순위 위치**.\
둘 다 `ORDER BY` 가 답을 끝까지 정하지 않은 자리이고, 고유 키와 `(열 IS NULL)` 키로 각각 막을 수 있다.

**방언 항목** — **9번**(`NULL` 위치)과 **8번**(`NTILE` 인자 검사: MySQL 은 파서가, PG 는 식으로).\
**언어 보장 항목** — 1·2·4·6·7·11·12번. `RANK`/`DENSE_RANK` 의 정의, `NTILE` 의 조 크기, 프레임 무시,\
`ORDER BY` 없을 때 전부 1인 것은 두 엔진의 출력이 같았다.\
단 **`NTILE` 의 「나머지를 앞 조에」는 문서가 아니라 실행으로 확인한 것**이다 — 문서는 *"as equally as possible"* 까지만 적는다.

**버전** — 네 함수 모두 PG 8.4 · MySQL 8.0 부터다. 버전이 오르면 **8·9번**을 다시 찍는다.

**재지 않은 것** — 순위 계산의 비용, 순위를 미리 저장하는 것과의 트레이드오프. **측정하지 않았으므로 적지 않았다.**
