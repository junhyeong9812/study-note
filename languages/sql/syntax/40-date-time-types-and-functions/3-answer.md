# sql/40-날짜·시간 타입과 함수 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 근거는 **실행 결과**다 — 아래 출력·에러·경고는 PostgreSQL 18.6(도커 `postgres:18`) 과 MySQL 8.4.10(도커 `mysql:8.4`) 에\
> 2026-09-21 에 실제로 던져 받은 것이다. 지어낸 출력은 없다.\
> ★ **시간대 조건** — PG `TimeZone` = `Etc/UTC` · MySQL `time_zone` = `SYSTEM`(그 SYSTEM 이 `UTC`) · `mysql.time_zone_name` 1,795행 적재.\
> MySQL `sql_mode` 는 기본값(`STRICT_TRANS_TABLES`·`NO_ZERO_DATE` 포함)이다.\
> 표를 쓴 실험은 전부 임시 표이거나 트랜잭션 롤백이고, `emp`·`dept` 는 읽기만 했다.\
> 문서 근거는 [PG 18 Date/Time Types](https://www.postgresql.org/docs/18/datatype-datetime.html) · [PG 18 Date/Time Functions](https://www.postgresql.org/docs/18/functions-datetime.html) · [MySQL 8.4 Date and Time Types](https://dev.mysql.com/doc/refman/8.4/en/date-and-time-types.html) · [MySQL 8.4 Date and Time Functions](https://dev.mysql.com/doc/refman/8.4/en/date-and-time-functions.html).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

---

### 0. 환경 확인 — **시간대를 안 밝히면 아래 답은 재현할 수 없다**

```text
--- PG 18.6 ---
SHOW timezone;
 TimeZone 
----------
 Etc/UTC
(1 row)

SELECT now();
              now              
-------------------------------
 2026-09-20 23:55:05.622928+00
(1 row)
```

```text
--- MySQL 8.4.10 ---
SELECT @@global.time_zone, @@session.time_zone, NOW(), @@system_time_zone;
+--------------------+---------------------+---------------------+--------------------+
| @@global.time_zone | @@session.time_zone | NOW()               | @@system_time_zone |
+--------------------+---------------------+---------------------+--------------------+
| SYSTEM             | SYSTEM              | 2026-09-20 23:55:05 | UTC                |
+--------------------+---------------------+---------------------+--------------------+

SELECT COUNT(*) AS tz_names FROM mysql.time_zone_name;
+----------+
| tz_names |
+----------+
|     1795 |
+----------+
```

**읽는 법 넷.**

1. **PG 는 `Etc/UTC`, MySQL 도 실효 `UTC`** 다 — 두 서버의 시각이 맞춰져 있다. 위 두 `NOW()` 가 같은 초를 가리킨다.
2. **`SYSTEM` 만 보면 무엇인지 모른다.** `@@system_time_zone` 을 같이 찍어야 `UTC` 임을 안다.
3. **`mysql.time_zone_name` 이 비어 있으면** `CONVERT_TZ(..., 'Asia/Seoul')` 이 **조용히 `NULL`** 이 된다(10번).
4. PG 의 `now()` 끝에 **`+00`** 이 붙어 있다 — 값에 시간대가 포함됐다는 표시다.

세션 시간대를 바꾸는 명령도 서로 다르다.

```text
PG    : SET TIME ZONE 'Asia/Seoul';   확인은 SHOW timezone;
MySQL : SET SESSION time_zone = '+09:00';   확인은 SELECT @@session.time_zone;
```

---

### 1. ★ `날짜 + 1` — **PG 는 하루 뒤, MySQL 은 수치 덧셈**

**출력**

```text
### SQL: SELECT DATE '2026-09-21' + 1 AS plus1;
--- PG 18.6 ---
   plus1    
------------
 2026-09-22
(1 row)

--- MySQL 8.4.10 ---
+----------+
| plus1    |
+----------+
| 20260922 |
+----------+
```

```text
### SQL: SELECT DATE '2026-09-30' + 1 AS plus1;
--- PG 18.6 ---
   plus1    
------------
 2026-10-01
(1 row)

--- MySQL 8.4.10 ---
+----------+
| plus1    |
+----------+
| 20260931 |
+----------+
```

**왜 그런가**

```text
PostgreSQL                          MySQL
date + integer 는 "N일 뒤" 로        date + integer 는 산술 문맥이다
정의된 연산자다                       -> DATE 를 정수로 바꾼다
       ↓                                    ↓
 2026-09-30 + 1일                     20260930 + 1
       ↓                                    ↓
   2026-10-01 (달이 넘어간다)          20260931 (9월 31일... 은 없다)
```

**첫 예는 그럴듯하고 둘째 예는 명백히 틀렸다.**\
`20260922` 만 보면 「형식이 좀 다를 뿐」로 넘어가기 쉽다 — **월말에서만 드러난다.**

**처방** — `날짜 + 정수` 를 쓰지 않는다. `INTERVAL` 을 쓴다(3번).\
`INTERVAL` 문법은 서로 거부하므로 **이식에서 에러로 터진다.** 그 편이 낫다.

---

### 2. ★ `날짜 - 날짜` — **같은 달에서만 우연히 맞는다**

**출력 (a)**

```text
### SQL: SELECT DATE '2026-09-21' - DATE '2026-09-01' AS diff;
--- PG 18.6 ---
 diff 
------
   20
(1 row)

--- MySQL 8.4.10 ---
+------+
| diff |
+------+
|   20 |
+------+
```

**출력 (b)**

```text
### SQL: SELECT DATE '2026-10-01' - DATE '2026-09-21' AS diff;
--- PG 18.6 ---
 diff 
------
   10
(1 row)

--- MySQL 8.4.10 ---
+------+
| diff |
+------+
|   80 |
+------+
```

**왜 (a) 만 같은가**

```text
(a) 같은 달, 같은 해
    PG    : 9월 21일 - 9월 1일 = 20일
    MySQL : 20260921 - 20260901 = 20
            ^^^^^^^^   ^^^^^^^^
            앞 6자리가 같으므로 남은 두 자리의 차이 = 일수 차이와 우연히 같다

(b) 달을 넘어간다
    PG    : 9월 21일부터 10월 1일까지 = 10일
    MySQL : 20261001 - 20260921 = 80
            ^^^^^^     ^^^^^^
            달 자리가 다르므로 자릿수 차이가 그대로 섞인다
```

**「같은 달 안에서는 맞는다」가 이 버그의 성질이다.**

```text
테스트 데이터가 같은 달이면        -> 통과한다
실제 데이터가 월말을 걸치면        -> 틀린다
        ↓
한 달에 한 번 재현되는 버그가 된다
```

**처방** — MySQL 에서는 `DATEDIFF()` 를 쓴다(9번). PG 에는 그 이름이 없다.\
양쪽에서 같은 코드를 쓰고 싶으면 **일수 계산을 애플리케이션으로 올린다.**

---

### 3. `INTERVAL` — **서로를 정확히 거부한다**

**출력 (a) — PG 표기**

```text
### SQL: SELECT DATE '2026-09-21' + INTERVAL '1 day' AS r;
--- PG 18.6 ---
          r          
---------------------
 2026-09-22 00:00:00
(1 row)

--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; ... near 'AS r' at line 1
```

**출력 (b) — MySQL 표기**

```text
### SQL: SELECT DATE '2026-09-21' + INTERVAL 1 DAY AS r;
--- PG 18.6 ---
ERROR:  syntax error at or near "1"
LINE 1: SELECT DATE '2026-09-21' + INTERVAL 1 DAY AS r;
                                            ^
--- MySQL 8.4.10 ---
+------------+
| r          |
+------------+
| 2026-09-22 |
+------------+
```

**왜 그런가**

```text
PostgreSQL                          MySQL
INTERVAL '1 day'                    INTERVAL 1 DAY
         ^^^^^^^                              ^ ^^^
    따옴표 안에 수와 단위가 함께       수와 단위 키워드가 따로
    (문자열을 interval 타입으로 읽는다)  (전용 문법이다)
```

**두 에러의 성격이 다르다.**

- MySQL 의 `ERROR 1064` 는 `'1 day'` 다음의 `AS r` 에서 막혔다 — 앞부분을 다르게 해석하고 있었다.
- PG 의 `syntax error at or near "1"` 은 `INTERVAL` 다음에 수가 오는 것을 모른다.

**둘 다 파서 단계에서 터진다 — 조용하지 않다.** 1번의 `+ 1` 과 정반대다.

**결과 타입도 봐 둔다.** PG 의 답이 `2026-09-22 00:00:00` 이다 — `date + interval` 은 **`timestamp`** 가 된다.\
`DATE` 를 유지하려면 `(DATE '2026-09-21' + INTERVAL '1 day')::date` 처럼 다시 캐스팅한다.

**월말 보정은 둘 다 같다.**

```text
--- PG 18.6 ---                             --- MySQL 8.4.10 ---
SELECT DATE '2026-01-31'                    SELECT DATE_ADD(DATE '2026-01-31',
       + INTERVAL '1 month' AS r;                           INTERVAL 1 MONTH) AS r;
          r                                 +------------+
---------------------                       | r          |
 2026-02-28 00:00:00                        +------------+
(1 row)                                     | 2026-02-28 |
                                            +------------+
```

**「1월 31일의 한 달 뒤」가 존재하지 않는 문제를 둘 다 「그 달의 마지막 날」로 푼다.**\
갈릴 만한 자리인데 안 갈렸다 — 확인해 둘 값어치가 있다.

---

### 4. 잘못된 날짜 — **36번의 `1/0` 과 똑같은 모양**

**출력 (a) — `SELECT`**

```text
### SQL: SELECT CAST('2026-02-30' AS DATE) AS d;
--- PG 18.6 ---
ERROR:  date/time field value out of range: "2026-02-30"
LINE 1: SELECT CAST('2026-02-30' AS DATE) AS d;
                    ^
--- MySQL 8.4.10 ---
+------+
| d    |
+------+
| NULL |
+------+
```

```text
--- MySQL 8.4.10 ---
SELECT CAST('2026-02-30' AS DATE) AS d;
SHOW WARNINGS;
+---------+------+----------------------------------------+
| Level   | Code | Message                                |
+---------+------+----------------------------------------+
| Warning | 1292 | Incorrect datetime value: '2026-02-30' |
+---------+------+----------------------------------------+
```

**출력 (b) — `INSERT`**

```text
--- MySQL 8.4.10 ---
CREATE TEMPORARY TABLE t40 (d DATE);
INSERT INTO t40 VALUES ('2026-02-30');
ERROR 1292 (22007) at line 1: Incorrect date value: '2026-02-30' for column 'd' at row 1
```

PG 는 (b)에서도 같은 `date/time field value out of range` 다.

**왜 그런가**

```text
MySQL 의 sql_mode 가 갈림길이다
  SELECT CAST(...)         -> 값이 필요한 자리 -> NULL + 경고 1292
  INSERT INTO t VALUES (…) -> 열에 쓰는 자리   -> STRICT_TRANS_TABLES 가 경고를 에러로 올린다
                                                 -> ERROR 1292
```

**36번의 `1/0` 과 한 글자도 다르지 않은 구조다.** 두 곳에서 같은 패턴을 본 것이 중요하다 —\
**MySQL 에서 「`SELECT` 로 검증」은 검증이 아니다.**

**PG 의 `HINT` 도 읽어 둔다.**

```text
--- PG 18.6 ---
SELECT CAST('2026-13-01' AS DATE) AS d;
ERROR:  date/time field value out of range: "2026-13-01"
LINE 1: SELECT CAST('2026-13-01' AS DATE) AS d;
                    ^
HINT:  Perhaps you need a different "DateStyle" setting.
```

**`DateStyle` 이라는 설정이 있다**고 알려 준다. `2026-13-01` 이 월·일 순서를 바꾸면 다르게 읽힐 수도 있기 때문이다.\
날짜 문자열 파싱은 **설정에 의존**한다 — 그래서 애플리케이션에서 타입으로 넘기는 편이 안전하다.

---

### 5. ★ 시간대 — **동작은 같고 이름이 어긋난다**

**출력 — PG(세션 시간대를 바꿔 두 번 읽었다)**

```text
--- PG 18.6 ---
SHOW timezone;
 TimeZone 
----------
 Etc/UTC
(1 row)

SELECT TIMESTAMPTZ '2026-09-21 10:00:00+00' AS tz, TIMESTAMP '2026-09-21 10:00:00' AS notz;
           tz           |        notz         
------------------------+---------------------
 2026-09-21 10:00:00+00 | 2026-09-21 10:00:00
(1 row)

SET TIME ZONE 'Asia/Seoul';
SELECT TIMESTAMPTZ '2026-09-21 10:00:00+00' AS tz, TIMESTAMP '2026-09-21 10:00:00' AS notz;
           tz           |        notz         
------------------------+---------------------
 2026-09-21 19:00:00+09 | 2026-09-21 10:00:00
(1 row)

SELECT pg_typeof(TIMESTAMPTZ '2026-09-21 10:00:00+00') AS t1,
       pg_typeof(TIMESTAMP '2026-09-21 10:00:00') AS t2, pg_typeof(now()) AS t3;
            t1            |             t2              |            t3            
--------------------------+-----------------------------+--------------------------
 timestamp with time zone | timestamp without time zone | timestamp with time zone
(1 row)
```

**출력 — 열에 담아서, 두 엔진 나란히**

```text
(A) PostgreSQL 18.6                        (B) MySQL 8.4.10
BEGIN;                                      SELECT @@session.time_zone;   -> SYSTEM
CREATE TEMP TABLE t40tz                     CREATE TEMPORARY TABLE t40tz
  (ts timestamptz, dt timestamp);             (ts TIMESTAMP, dt DATETIME);
INSERT INTO t40tz VALUES                    INSERT INTO t40tz VALUES
  ('2026-09-21 10:00:00',                     ('2026-09-21 10:00:00',
   '2026-09-21 10:00:00');                     '2026-09-21 10:00:00');
SELECT ts, dt FROM t40tz;                   SELECT ts, dt FROM t40tz;
--- 실제 출력 ---                           --- 실제 출력 ---
           ts           |         dt          +---------------------+---------------------+
------------------------+------------------   | ts                  | dt                  |
 2026-09-21 10:00:00+00 | 2026-09-21 10:00:00 +---------------------+---------------------+
(1 row)                                       | 2026-09-21 10:00:00 | 2026-09-21 10:00:00 |
                                              +---------------------+---------------------+
SET TIME ZONE 'Asia/Seoul';                 SET SESSION time_zone = '+09:00';
SELECT ts, dt FROM t40tz;                   SELECT ts, dt FROM t40tz;
--- 실제 출력 ---                           --- 실제 출력 ---
           ts           |         dt          +---------------------+---------------------+
------------------------+------------------   | ts                  | dt                  |
 2026-09-21 19:00:00+09 | 2026-09-21 10:00:00 +---------------------+---------------------+
(1 row)                                       | 2026-09-21 19:00:00 | 2026-09-21 10:00:00 |
ROLLBACK;                                     +---------------------+---------------------+
```

**왜 그런가**

```text
시간대가 붙은 값                      시간대가 없는 값
"지구 어느 한 순간" 을 저장한다        "벽시계 숫자" 를 저장한다
        ↓                                    ↓
읽는 사람의 시간대로 환산해 보여 준다   누가 읽든 그대로다
        ↓                                    ↓
 10:00+00  ->  19:00+09                10:00:00  ->  10:00:00
 (같은 순간, 다른 이름)                 (안 바뀐다)
```

**동작이 두 엔진에서 한 자리도 안 갈렸다. 갈리는 것은 이름뿐이다.**

```text
MySQL TIMESTAMP  ≈  PG timestamptz    <- 환산된다
MySQL DATETIME   ≈  PG timestamp      <- 안 바뀐다
      ^^^^^^^^^         ^^^^^^^^^
      같은 단어가 반대쪽을 가리킨다
```

**이식할 때 이것이 사고가 된다.**

```text
MySQL TIMESTAMP  ->  PG timestamp    로 옮기면  : 시간대 환산이 사라진다
MySQL DATETIME   ->  PG timestamptz  로 옮기면  : 없던 환산이 생긴다
        ↓
둘 다 에러가 안 난다. 데이터가 조용히 어긋난다
```

**명시적 환산은 문법이 서로 없다.**

```text
### SQL: SELECT TIMESTAMPTZ '2026-09-21 10:00:00+00' AT TIME ZONE 'Asia/Seoul' AS r;
--- PG 18.6 ---
          r          
---------------------
 2026-09-21 19:00:00
(1 row)

--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; ...
  right syntax to use near 'AT TIME ZONE 'Asia/Seoul' AS r' at line 1
```

```text
### SQL: SELECT CONVERT_TZ('2026-09-21 10:00:00','+00:00','+09:00') AS r;
--- PG 18.6 ---
ERROR:  function convert_tz(unknown, unknown, unknown) does not exist
LINE 1: SELECT CONVERT_TZ('2026-09-21 10:00:00','+00:00','+09:00') A...
               ^
--- MySQL 8.4.10 ---
+---------------------+
| r                   |
+---------------------+
| 2026-09-21 19:00:00 |
+---------------------+
```

**PG 의 `AT TIME ZONE` 결과에 오프셋이 없는 것**도 읽을 값어치가 있다 —\
`timestamptz AT TIME ZONE '...'` 은 **시간대 없는 값**을 돌려준다. 「그 지역의 벽시계 시각」이라는 뜻이다.

---

### 6. ★ 트랜잭션 안의 `NOW()` — **PG 는 고정, MySQL 은 갱신**

**출력 — 1판**

```text
(A) PostgreSQL 18.6                        (B) MySQL 8.4.10
BEGIN;                                      START TRANSACTION;
SELECT now() AS now_1,                      SELECT NOW(6) AS now_1,
       statement_timestamp() AS stmt_1,            SYSDATE(6) AS sysdate_1;
       clock_timestamp() AS clock_1;        SELECT SLEEP(1) AS slept;
SELECT pg_sleep(1);                         SELECT NOW(6) AS now_2,
SELECT now() AS now_2, ... ;                       SYSDATE(6) AS sysdate_2;
COMMIT;                                     COMMIT;
--- 실제 출력 ---                          --- 실제 출력 ---
now_1   2026-09-21 00:01:03.680036+00      now_1     2026-09-21 00:01:05.861180
stmt_1  2026-09-21 00:01:03.680115+00      sysdate_1 2026-09-21 00:01:05.861212
clock_1 2026-09-21 00:01:03.680356+00
   (1초 잠)                                   (1초 잠)
now_2   2026-09-21 00:01:03.680036+00      now_2     2026-09-21 00:01:06.861700
stmt_2  2026-09-21 00:01:04.681759+00      sysdate_2 2026-09-21 00:01:06.861780
clock_2 2026-09-21 00:01:04.681828+00

 -> now_1 = now_2 (.680036 으로 동일)         -> now_1 != now_2 (1초 늘었다)
 -> stmt / clock 은 1초 늘었다
```

**출력 — 반증을 찾으려고 세 판을 돌렸다**

```text
--- PG 18.6 ---                         --- MySQL 8.4.10 ---
run 1  .680036 / .680036  (같다)        run 1  05.861180 / 06.861700  (다르다)
run 2  .577746 / .577746  (같다)        run 2  19.656219 / 20.656607  (다르다)
run 3  .780803 / .780803  (같다)        run 3  21.881670 / 22.881925  (다르다)
```

**왜 그런가**

```text
PG 의 now() 는 transaction_timestamp() 와 같은 것이다
  = "이 트랜잭션이 시작된 시각"
        ↓
  트랜잭션이 끝날 때까지 같은 값

MySQL 의 NOW() 는 "이 문이 시작된 시각" 이다
        ↓
  문이 바뀌면 값도 바뀐다
```

**세 판이 다 같았다는 것을 「보장」의 근거로 쓰지 않는다.**\
보장의 근거는 **두 문서가 각각 그렇게 정의한다는 것**이고, 세 판은 그 설명이 **이 서버에서 실제로 성립함**을 보인 것이다.

**왜 이게 중요한가**

```text
한 트랜잭션에서 여러 표에 "지금 시각" 을 박는다

PG    : 전부 같은 시각이 박힌다 -> 나중에 "이 트랜잭션의 변경" 을 시각으로 묶을 수 있다
MySQL : 문마다 다른 시각이 박힌다 -> 못 묶는다
        ↓
   처방: 변수에 한 번 담아 재사용한다
          SET @tx_at = NOW(6);  그 뒤로는 @tx_at 만 쓴다
```

**자동 커밋에서는 PG 도 바뀐다** — 문 하나가 곧 트랜잭션 하나이기 때문이다.

```text
--- PG 18.6 ---  (BEGIN 없이)
SELECT now() AS now_1;   2026-09-21 00:01:04.778621+00
SELECT pg_sleep(1);
SELECT now() AS now_2;   2026-09-21 00:01:05.780038+00
```

「**PG 의 `now()` 는 안 바뀐다」가 아니라 「한 트랜잭션 안에서 안 바뀐다**」다.\
이 반례를 같이 두지 않으면 잘못 외운다.

---

### 7. 한 문 안에서는 — **`NOW()` 는 고정, `SYSDATE()` 는 아니다**

**출력**

```text
--- MySQL 8.4.10 ---
SELECT NOW(6) AS a, SLEEP(1) AS s, NOW(6) AS b, SYSDATE(6) AS c;
+----------------------------+---+----------------------------+----------------------------+
| a                          | s | b                          | c                          |
+----------------------------+---+----------------------------+----------------------------+
| 2026-09-21 00:01:06.862056 | 0 | 2026-09-21 00:01:06.862056 | 2026-09-21 00:01:07.862855 |
+----------------------------+---+----------------------------+----------------------------+
```

**답** — **`a` 와 `b` 는 같고, `c` 는 약 1초 늦다.**

**왜 그런가**

```text
a  NOW(6)      문 시작 시각        -> .862056
s  SLEEP(1)    1초 잔다
b  NOW(6)      문 시작 시각        -> .862056   <- 마이크로초까지 a 와 같다
c  SYSDATE(6)  호출 순간의 시각     -> .862855   <- 1초 뒤다
```

**`a` 와 `b` 가 한 마이크로초도 안 틀린 것**이 「문 단위로 고정」의 증거다.\
사이에 1초를 잤는데도 같다 — 값을 그 자리에서 읽은 게 아니라 **문 시작 때 정해 둔 것**을 쓴 것이다.

**PG 에도 같은 세 층이 있다.**

```text
                     PG                        MySQL
트랜잭션 내내 고정    now() = transaction_timestamp()   (없다)
문마다 갱신          statement_timestamp()             NOW() / CURRENT_TIMESTAMP
부를 때마다 갱신      clock_timestamp()                 SYSDATE()
```

PG 쪽 증거.

```text
--- PG 18.6 ---
SELECT clock_timestamp() AS clock_a, clock_timestamp() AS clock_b;
            clock_a            |            clock_b            
-------------------------------+-------------------------------
 2026-09-21 00:01:04.682101+00 | 2026-09-21 00:01:04.682102+00
(1 row)
```

**한 문 안에서 1마이크로초 차이**가 났다 — `clock_timestamp()` 는 고정되지 않는다.

`CURRENT_TIMESTAMP` 와 `NOW()` 는 **두 엔진 모두 같은 것**이다.

```text
### SQL: SELECT CURRENT_TIMESTAMP AS ct, NOW() AS n, CURRENT_DATE AS cd;
--- PG 18.6 ---
              ct               |               n               |     cd     
-------------------------------+-------------------------------+------------
 2026-09-21 00:00:39.686764+00 | 2026-09-21 00:00:39.686764+00 | 2026-09-21
(1 row)

--- MySQL 8.4.10 ---
+---------------------+---------------------+------------+
| ct                  | n                   | cd         |
+---------------------+---------------------+------------+
| 2026-09-21 00:00:39 | 2026-09-21 00:00:39 | 2026-09-21 |
+---------------------+---------------------+------------+
```

**정밀도가 다르다** — PG 는 마이크로초까지, MySQL 은 기본이 초다. 그래서 6·7번에서 `NOW(6)` 을 썼다.

---

### 8. ★ `BETWEEN` — **두 엔진에서 똑같이 하루가 빠진다**

**출력**

```text
(A) PostgreSQL 18.6                        (B) MySQL 8.4.10
BEGIN;                                      START TRANSACTION;
CREATE TEMP TABLE t40e (id int, at timestamp);  CREATE TEMPORARY TABLE t40e (id int, at DATETIME);
INSERT INTO t40e VALUES                     INSERT INTO t40e VALUES
  (1,'2026-09-30 00:00:00'),                  (1,'2026-09-30 00:00:00'),
  (2,'2026-09-30 13:45:00'),                  (2,'2026-09-30 13:45:00'),
  (3,'2026-10-01 00:00:00');                  (3,'2026-10-01 00:00:00');

-- (a) BETWEEN                              -- (a) BETWEEN
SELECT id FROM t40e WHERE at BETWEEN        SELECT id FROM t40e WHERE at BETWEEN
  '2026-09-01' AND '2026-09-30'               '2026-09-01' AND '2026-09-30'
  ORDER BY id;                                ORDER BY id;
--- 실제 출력 ---                          --- 실제 출력 ---
 id                                         +------+
----                                        | id   |
  1                                         +------+
(1 row)                                     |    1 |
                                            +------+

-- (b) >= AND <                             -- (b) >= AND <
SELECT id FROM t40e WHERE at >= '2026-09-01'  SELECT id FROM t40e WHERE at >= '2026-09-01'
  AND at < '2026-10-01' ORDER BY id;            AND at < '2026-10-01' ORDER BY id;
--- 실제 출력 ---                          --- 실제 출력 ---
 id                                         +------+
----                                        | id   |
  1                                         |    1 |
  2                                         |    2 |
(2 rows)                                    +------+
ROLLBACK;                                   ROLLBACK;
```

**답** — (a)는 **1행**, (b)는 **2행**. **두 엔진에서 같다.**

**왜 그런가**

```text
'2026-09-30' 에는 시각이 없다
        ↓
'2026-09-30 00:00:00' 으로 읽힌다
        ↓
BETWEEN ... AND '2026-09-30 00:00:00'

  id=1  09-30 00:00:00  ->  상한과 같다      -> 걸린다
  id=2  09-30 13:45:00  ->  상한을 넘는다    -> ★ 빠진다
  id=3  10-01 00:00:00  ->  상한을 넘는다    -> 빠진다 (이건 의도대로다)
        ↓
9월 30일 하루가 거의 통째로 빠진다
```

**`>= 시작 AND < 다음 시작` 이 안전한 형태다.**

```text
at >= '2026-09-01' AND at < '2026-10-01'
                          ^
              상한을 포함하지 않는다
                          ↓
    9월의 마지막 마이크로초까지 전부 포함되고
    10월 1일 00:00:00 은 다음 구간이 가져간다
        ↓
   구간을 이어 붙여도 겹치지도 빠지지도 않는다
```

**`DATE` 열에서는 이 사고가 안 난다** — 시각이 없으니 상한이 딱 맞는다.\
그래서 **`DATE` 를 `DATETIME`/`timestamp` 로 바꾸는 순간** 기존 질의가 조용히 틀리기 시작한다.

**덤 — `WHERE DATE(at) = '2026-09-30'` 으로 푸는 것은 더 나쁘다.**\
답은 맞지만 **열에 함수를 씌워 인덱스를 죽인다**(35번 8번). `>= AND <` 가 답도 맞고 인덱스도 산다.

---

### 9. 절단과 추출 — **`EXTRACT` 만 공통이다**

**출력 — `EXTRACT` 의 표준 단위(공통)**

```text
### SQL: SELECT EXTRACT(YEAR FROM TIMESTAMP '2026-09-21 10:30:45') AS y,
###             EXTRACT(DAY FROM ...) AS d, EXTRACT(HOUR FROM ...) AS h;
--- PG 18.6 ---
  y   | d  | h  
------+----+----
 2026 | 21 | 10
(1 row)

--- MySQL 8.4.10 ---
+------+------+------+
| y    | d    | h    |
+------+------+------+
| 2026 |   21 |   10 |
+------+------+------+
```

**출력 — PG 전용 단위**

```text
### SQL: SELECT EXTRACT(DOW FROM DATE '2026-09-21') AS dow;
--- PG 18.6 ---
 dow 
-----
   1
(1 row)

--- MySQL 8.4.10 ---
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax; ...
  right syntax to use near 'DOW FROM DATE '2026-09-21') AS dow' at line 1
```

**출력 — `DATE_TRUNC`**

```text
### SQL: SELECT DATE_TRUNC('month', TIMESTAMP '2026-09-21 10:30:45') AS r;
--- PG 18.6 ---
          r          
---------------------
 2026-09-01 00:00:00
(1 row)

--- MySQL 8.4.10 ---
ERROR 1305 (42000) at line 1: FUNCTION study.DATE_TRUNC does not exist
```

**출력 — MySQL 의 대응 관용구**

```text
### SQL: SELECT DATE_FORMAT('2026-09-21 10:30:45','%Y-%m-01 00:00:00') AS r;
--- PG 18.6 ---
ERROR:  function date_format(unknown, unknown) does not exist
LINE 1: SELECT DATE_FORMAT('2026-09-21 10:30:45','%Y-%m-01 00:00:00'...
               ^
--- MySQL 8.4.10 ---
+---------------------+
| r                   |
+---------------------+
| 2026-09-01 00:00:00 |
+---------------------+
```

**출력 — `DATEDIFF`**

```text
### SQL: SELECT DATEDIFF('2026-09-21','2026-09-01') AS diff;
--- PG 18.6 ---
ERROR:  function datediff(unknown, unknown) does not exist
LINE 1: SELECT DATEDIFF('2026-09-21','2026-09-01') AS diff;
               ^
HINT:  No function matches the given name and argument types. You might need to add explicit type casts.
--- MySQL 8.4.10 ---
+------+
| diff |
+------+
|   20 |
+------+
```

**정리하면**

| 이름 | PG 18.6 | MySQL 8.4.10 |
|---|---|---|
| `EXTRACT(YEAR/DAY/HOUR ...)` | ✅ | ✅ |
| `EXTRACT(DOW ...)` | ✅ | ✗ `ERROR 1064` |
| `DATE_TRUNC` | ✅ | ✗ `ERROR 1305 FUNCTION ... does not exist` |
| `DATE_FORMAT` | ✗ 함수 없음 | ✅ (절단의 대응 관용구) |
| `DATEDIFF` | ✗ 함수 없음 | ✅ |

**에러 코드가 둘로 갈린 것**도 읽을 값어치가 있다.

```text
ERROR 1064  파서가 막혔다         -> EXTRACT(DOW ...) : DOW 라는 단위 키워드를 모른다
ERROR 1305  함수를 못 찾았다      -> DATE_TRUNC       : 문법은 맞고 이름이 없다
```

**전부 시끄럽다.** 이 주제에서 조용한 것은 **1·2·5·8번**뿐이다.

---

### 10. `CONVERT_TZ` 가 `NULL` 이 되는 이유 — **시간대 이름표가 없어서**

**오프셋은 표 없이도 된다.**

```text
--- MySQL 8.4.10 ---
SELECT CONVERT_TZ('2026-09-21 10:00:00','+00:00','+09:00') AS r;
+---------------------+
| r                   |
+---------------------+
| 2026-09-21 19:00:00 |
+---------------------+
```

**이름은 표가 있어야 된다. 이 서버에는 있다.**

```text
--- MySQL 8.4.10 ---
SELECT CONVERT_TZ('2026-09-21 10:00:00','UTC','Asia/Seoul') AS r;
+---------------------+
| r                   |
+---------------------+
| 2026-09-21 19:00:00 |
+---------------------+

SELECT COUNT(*) AS tz_names FROM mysql.time_zone_name;
+----------+
| tz_names |
+----------+
|     1795 |
+----------+
```

**왜 `NULL` 이 되나**

```text
'Asia/Seoul' 이라는 이름을 해석하려면
  "서울이 UTC 대비 몇 시간이고, 서머타임이 언제 있었나" 를 알아야 한다
        ↓
그 정보는 mysql.time_zone_name 등의 시스템 표에 들어 있다
        ↓
그 표가 비어 있으면 -> 이름을 해석 못 한다
        ↓
★ 에러가 아니라 NULL 이다
```

**「에러가 아니라 `NULL`」이 이 문제의 성질이다.**\
개발 서버에서 되던 것이 운영 서버에서 조용히 `NULL` 이 되고,\
그 `NULL` 이 다시 다른 계산으로 퍼진다([04 NULL 의 3값 논리](../04-null-three-valued-logic/)).

**확인 방법과 처방.**

```text
확인  SELECT COUNT(*) FROM mysql.time_zone_name;   -> 0 이면 적재되지 않았다
처방  (1) 서버에 시간대 표를 적재한다 (서버 구축 시의 작업이다)
      (2) 오프셋('+09:00')만 쓴다   <- 단, 서머타임을 못 다룬다
      (3) 환산을 애플리케이션으로 올린다
```

**PG 에는 이 문제가 없다** — 시간대 정보가 내장이다. 대신 39번에서 본 것처럼\
**정렬 규칙은 OS 에 의존**한다. 어느 엔진이든 「**무엇을 밖에서 빌려 쓰나**」를 알아야 한다.

---

### 11. 어떻게 저장하고 언제 환산하나

**기본형은 한 문장이다 — 「UTC 로 저장하고, 표시할 때만 환산한다.」**

```text
입력                저장                      표시
사용자의 현지 시각   -> UTC 한 순간으로 -----> 보는 사람의 시간대로
       ↓                    ↓                        ↓
 클라이언트가          timestamptz (PG)        애플리케이션 또는
 시간대를 붙여 보낸다   TIMESTAMP (MySQL)       세션 시간대가 환산
```

**왜 이 형태인가**

| 저장 방식 | 「두 사건의 선후」 | 서머타임 | 이식 |
|---|---|---|---|
| **UTC + 시간대 있는 타입** | 항상 정확하다 | 데이터에 안 들어온다 | 타입 이름만 맞추면 된다 |
| 현지 시각 + 시간대 없는 타입 | **비교가 틀릴 수 있다** | 「없는 시각」·「두 번 오는 시각」이 생긴다 | 같다 |
| 문자열로 저장 | 정렬조차 안 맞는다 | — | — |

**「벽시계 시각 자체가 의미」인 경우는 예외다.**

```text
시간대 있는 타입이 맞는 것        시간대 없는 타입이 맞는 것
────────────────                  ────────────────
로그 시각                         "매주 화요일 09:00 회의"
결제 시각                         "생일"
주문 생성 시각                    "가게 영업 시작 시각 10:00"
        ↓                                 ↓
"그 순간이 언제였나" 가 의미      "시계가 무엇을 가리키나" 가 의미
```

**같이 정할 것 넷.**

1. **타입 이름을 맞췄나**(5번). `MySQL TIMESTAMP` ↔ `PG timestamptz` 다. 이름이 어긋난다.
2. **세션 시간대를 고정했나.** 애플리케이션 연결마다 시간대가 다르면 **같은 행이 다르게 보인다.**\
   대개 **연결 시점에 UTC 로 고정**하고 표시 층에서만 환산한다.
3. **시간대 표가 적재돼 있나**(10번). MySQL 에서 이름을 쓸 거면 **배포 환경에서 확인**한다.
4. **트랜잭션 시각을 어떻게 잡나**(6번). PG 는 `now()` 가 알아서 고정되고, MySQL 은 **변수에 담아야** 한다.

**질의를 쓸 때의 두 습관.**

```text
쓰지 말 것                          대신 쓸 것
─────────                           ─────────
WHERE DATE(at) = '2026-09-30'       WHERE at >= '2026-09-30' AND at < '2026-10-01'
WHERE at BETWEEN 시작 AND 끝        WHERE at >= 시작 AND at < 다음시작
at + 1                              at + INTERVAL ... (방언에 맞게)
end - start (일수)                  PG: end - start / MySQL: DATEDIFF(end, start)
```

**첫 두 줄이 같은 처방**이라는 점이 요점이다 — 8번의 경계 문제와 인덱스 문제를 **한 형태가 동시에 푼다.**

## 실행 검증

| 무엇을 | 어디서 | 몇 번 | 비고 |
|---|---|---|---|
| 시간대·환경 조회 (0번) | PG 18.6 · MySQL 8.4.10 | 각 3회 | `SHOW timezone` / `@@time_zone`·`@@system_time_zone`·`time_zone_name` |
| 리터럴 3종 (1번 앞) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **표기·출력이 동일** |
| `날짜 + 1` 두 경우 (1번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **월말 `20260931` 이 근거다** |
| `날짜 - 날짜` 두 경우 (2번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **같은 달/다른 달을 둘 다 실었다** |
| `INTERVAL` 두 표기 (3번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **양쪽 구문 오류가 근거다** |
| 월말 보정 (3번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **두 엔진 동일** |
| 잘못된 날짜 `SELECT` (4번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | `2026-02-30`·`2026-13-01` |
| 경고 1292 (4번) | MySQL 8.4.10 | 1회 | `SHOW WARNINGS` |
| 잘못된 날짜 `INSERT` (4번) | MySQL 8.4.10 | 1회 | **`ERROR 1292` 가 근거다** |
| 시간대 리터럴 + 세션 변경 (5번) | PG 18.6 | 2회 | `pg_typeof` 확인 포함 |
| 시간대 열 + 세션 변경 (5번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | 임시 표 · **동작이 동일** |
| `AT TIME ZONE` / `CONVERT_TZ` (5·10번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | **양쪽 없음 에러가 근거다** |
| 트랜잭션 안 `NOW()` (6번) | PG 18.6 · MySQL 8.4.10 | **각 3회** | **반증을 찾으려고 반복했다 — 3/3 동일** |
| 자동 커밋에서 `now()` (6번) | PG 18.6 | 1회 | **반례로 실었다** |
| 한 문 안의 `NOW()`/`SYSDATE()` (7번) | MySQL 8.4.10 | 1회 | **`a` = `b`, `c` 만 다름** |
| `clock_timestamp()` 2회 (7번) | PG 18.6 | 1회 | **1마이크로초 차이가 근거다** |
| `CURRENT_TIMESTAMP` 대 `NOW()` (7번) | PG 18.6 · MySQL 8.4.10 | 각 1회 | **같은 값** |
| `BETWEEN` 대 `>= AND <` (8번) | PG 18.6 · MySQL 8.4.10 | 각 2회 | 임시 표 롤백 · **두 엔진 동일** |
| `EXTRACT`·`DATE_TRUNC`·`DATE_FORMAT`·`DATEDIFF` (9번) | PG 18.6 · MySQL 8.4.10 | 각 4회 | **에러 코드 1064/1305 가 갈린다** |
| `CONVERT_TZ` 이름·오프셋 (10번) | MySQL 8.4.10 | 2회 | **표 적재 확인 포함** |

**★ 설정 의존 항목 — 5번 전부와 0번.**\
머리말·0번에 적은 시간대(PG `Etc/UTC` / MySQL 실효 `UTC`)에서 나온 결과다.\
**다른 시간대의 서버에서는 같은 질의가 다른 시각을 보여 준다.**

**`sql_mode` 의존 항목** — 4번의 `INSERT`. `STRICT_TRANS_TABLES` 가 경고를 에러로 올린다.

**서버 구성 의존 항목** — 10번. `mysql.time_zone_name` 이 비어 있으면 **같은 문이 `NULL`** 이다.

**언어 보장 항목** — 1·2·3·5·6·7·8·9번.\
`날짜 + 정수` 의 의미, `INTERVAL` 문법, 시간대 타입의 동작, `now()`/`NOW()` 의 고정 범위,\
`BETWEEN` 의 포함 규칙, 각 함수의 존재 여부 — 전부 두 매뉴얼이 정한 것이다.

**6번을 「여러 번 같았다」로만 적지 않은 이유** — 반복은 **반증을 찾는 절차**였지 보장의 근거가 아니다.\
보장의 근거는 두 문서가 `now()` 를 트랜잭션 시각으로, `NOW()` 를 문 시각으로 **정의한다는 사실**이다.\
그리고 **반례도 같이 실었다** — 자동 커밋에서는 PG 의 `now()` 도 바뀐다.

**측정 조건** — `pg_sleep(1)`·`SLEEP(1)` 이 정확히 1초가 아니다(출력의 소수부가 보여 준다).\
6·7번에서 읽을 것은 **절댓값이 아니라 「두 값이 같은가 다른가**」이고, 그 신호는 **1초 대 0마이크로초**라 잡음보다 훨씬 크다.

**버전을 적지 않은 이유** — 이 주제의 동작에 「어느 버전부터」가 붙은 것을 **두 매뉴얼에서도 릴리스 노트에서도 찾지 못했다.**

**DB 잔재** — 없다. `t40`·`t40tz`·`t40e` 는 전부 임시 표이거나 트랜잭션 롤백이고, `emp`·`dept` 는 읽기만 했다.
