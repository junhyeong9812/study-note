# sql/40-날짜·시간 타입과 함수 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 본문은 Claude 작성이다 — 원고가 아니다.** SQL 은 원고 없이 공식 문서로 접지하는 문법 주제다([작성법 §2-1](../../../../../../reference/study-note-guide.md)).
>
> **기준 소스** — [PostgreSQL 18 · Date/Time Types](https://www.postgresql.org/docs/18/datatype-datetime.html) · [PostgreSQL 18 · Date/Time Functions and Operators](https://www.postgresql.org/docs/18/functions-datetime.html) · [MySQL 8.4 · Date and Time Data Types](https://dev.mysql.com/doc/refman/8.4/en/date-and-time-types.html) · [MySQL 8.4 · Date and Time Functions](https://dev.mysql.com/doc/refman/8.4/en/date-and-time-functions.html)\
> **실행 검증** — **PostgreSQL 18.6**(도커 `postgres:18`) · **MySQL 8.4.10**(도커 `mysql:8.4`), 2026-09-21.\
> 아래에 실린 출력·에러·경고는 **전부 이 두 서버에 실제로 던져서 받은 것**이다. 지어낸 출력은 없다.\
> ★ **시간대 조건** — PG `TimeZone` = **`Etc/UTC`** · MySQL `@@global.time_zone`·`@@session.time_zone` = **`SYSTEM`**(그 SYSTEM 이 `UTC`).\
> **이 설정이 4·5번의 답을 정한다.** 아래 「시간대 확인」 절에 직접 찍은 출력을 실었다.\
> MySQL `sql_mode` 는 기본값(`STRICT_TRANS_TABLES`·`NO_ZERO_DATE` 포함)이다 — 3번의 결과가 여기 달렸다.\
> **버전** — 도입 버전이 확인된 것은 없어 **버전을 적지 않는다.**\
> **선행** — [35 타입 체계와 캐스팅](../35-type-system-and-casting/)

## 한눈에 — 쉽게 말하면

**날짜·시간 타입의 핵심 질문은 하나다 — 「이 값에 시간대가 붙어 있나?」**

```text
'2026-09-21 10:00:00' 이라는 값이 있다

시간대가 없는 타입                    시간대가 있는 타입
──────────────                        ──────────────
"벽시계로 10시"                       "지구 어느 한 순간"
어디서 읽어도 10:00                   읽는 사람의 시간대로 환산해 보여 준다
                                        UTC 에서 보면 10:00
                                        서울에서 보면 19:00
```

| 비유 | 실체 |
|---|---|
| 벽에 걸린 시계 사진 | 시간대 없는 타입(`timestamp` / `DATETIME`) |
| 「지구 어느 순간」을 가리키는 좌표 | 시간대 있는 타입(`timestamptz` / `TIMESTAMP`) |
| 사진은 어디서 봐도 같은 시각을 보여 준다 | 시간대 없는 값은 안 바뀐다 |
| 좌표는 보는 곳의 시계로 환산된다 | 시간대 있는 값은 읽는 시간대로 바뀌어 보인다 |

> **시간대(time zone)** — 같은 순간을 지역마다 다른 시각으로 부르는 규칙.\
> 예: UTC 10:00 은 서울에서 19:00 이다. **같은 순간**이고 **다른 이름**이다.

★ **이름이 함정이다.** 두 엔진에서 **같은 이름이 반대 뜻**이다.

```text
MySQL TIMESTAMP  ≈  PG timestamptz    (시간대 있음 — 읽을 때 환산된다)
MySQL DATETIME   ≈  PG timestamp      (시간대 없음 — 안 바뀐다)
       ^^^^^^^^           ^^^^^^^^^
       "TIMESTAMP" 라는 이름이 두 엔진에서 다른 것을 가리킨다
```

그리고 **날짜 산술이 조용히 갈린다.**

```text
SELECT DATE '2026-09-21' + 1;

PG    -> 2026-09-22      날짜에 하루를 더했다
MySQL -> 20260922        ★ 날짜를 숫자 20260921 로 읽고 1 을 더했다
```

## 시간대 확인 — 이 문서의 결과가 나온 자리

★ **이것부터 찍는다.** 시간대를 안 밝힌 날짜 주장은 검증할 수 없다.

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

읽는 법.

- **PG 는 `Etc/UTC`**, **MySQL 은 `SYSTEM` 이고 그 SYSTEM 이 `UTC`** 다. **두 서버의 실효 시간대가 같다.**
- **`@@system_time_zone` 을 따로 봐야 한다.** `SYSTEM` 이라는 값만 보면 무엇인지 모른다.
- **`mysql.time_zone_name` 에 1,795행이 있다** — 이 서버는 **시간대 이름표가 적재돼 있다.**\
  적재되지 않은 서버에서는 `CONVERT_TZ(..., 'Asia/Seoul')` 이 `NULL` 을 돌려준다. **환경마다 다르다.**
- PG 의 `now()` 출력 끝에 **`+00`** 이 붙어 있다 — 시간대가 **값에 포함**돼 있다는 표시다.

## 이 주제가 답하려는 질문

1. **시간대가 붙은 타입과 안 붙은 타입은 무엇이 다른가?**
2. **날짜를 더하고 빼는 문법은 두 엔진에서 같은가?**
3. **트랜잭션 안에서 `NOW()` 는 고정되나?**

## 예시 데이터 — 이 묶음이 공유하는 것

값은 전부 리터럴로 만든다. 열 타입이 관련된 실험만 임시 표를 쓰고 **롤백하거나 지웠다.**

```sql
-- 시간대 실험
CREATE TEMP TABLE t40tz (ts timestamptz, dt timestamp);          -- PG
CREATE TEMPORARY TABLE t40tz (ts TIMESTAMP, dt DATETIME);        -- MySQL

-- 경계 조건 실험
CREATE TEMP TABLE t40e (id int, at timestamp);                   -- PG
CREATE TEMPORARY TABLE t40e (id int, at DATETIME);               -- MySQL
```

`emp`·`dept` 는 읽기만 하고 바꾸지 않는다.

## 동작 방식

### 1. 타입 넷 — 리터럴은 같다

**언제 쓰나** — 열을 정의할 때. 여기까지는 두 엔진이 같아서 안심하게 된다.

```text
### SQL: SELECT DATE '2026-09-21' AS d, TIME '10:30:00' AS t, TIMESTAMP '2026-09-21 10:30:00' AS ts;
--- PG 18.6 ---
     d      |    t     |         ts          
------------+----------+---------------------
 2026-09-21 | 10:30:00 | 2026-09-21 10:30:00
(1 row)

--- MySQL 8.4.10 ---
+------------+----------+---------------------+
| d          | t        | ts                  |
+------------+----------+---------------------+
| 2026-09-21 | 10:30:00 | 2026-09-21 10:30:00 |
+------------+----------+---------------------+
```

그림 해설 — **리터럴 표기와 출력이 한 자리도 안 갈렸다.**\
대가 — 여기서 안심하면 아래 2·4번에서 물린다. **표기가 같다고 의미가 같은 것이 아니다.**

```text
PostgreSQL                          MySQL
DATE                                DATE
TIME                                TIME
timestamp (= without time zone)     DATETIME
timestamptz (= with time zone)      TIMESTAMP     <- ★ 이름이 어긋난다
```

### 2. ★ 날짜 산술 — 같은 문장, 다른 종류의 답

**언제 쓰나** — 「하루 뒤」·「한 달 뒤」를 구할 때. **조용한 사고가 여기 있다.**

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
PostgreSQL                          MySQL
date + integer 는 "N일 뒤" 다        date + integer 는 수치 연산이다
       ↓                                    ↓
 2026-09-21 에 하루를 더한다          DATE 를 정수 20260921 로 바꾼다
       ↓                                    ↓
   2026-09-22 (날짜다)                20260921 + 1 = 20260922 (정수다)
```

그림 해설 — **MySQL 의 답이 날짜처럼 보이지만 정수다.** 이번에는 우연히 그럴듯했다.\
월말로 옮기면 바로 드러난다.

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

**`20260931`** — 9월 31일이라는 날짜는 없다. 그래도 에러가 안 난다.

**뺄셈에서 더 잘 드러난다.**

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

**같은 답이다. 그런데 이유가 다르다.** 달을 넘겨 보면 갈린다.

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

```text
PG    : 날짜 뺄셈 -> 일수 -> 10
MySQL : 20261001 - 20260921 = 80   <- 숫자를 뺀 것이다
```

그림 해설 — **같은 달 안에서는 우연히 맞는다.** 테스트 데이터가 같은 달이면 **통과한다.**\
대가 — 월말 경계에서만 틀리는 버그는 **한 달에 한 번 재현된다.** 가장 찾기 어려운 종류다.

**제대로 쓰려면 `INTERVAL` 이고, 그 문법이 갈린다.**

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

그림 해설 — **서로를 정확히 거부한다.** PG 는 `INTERVAL '1 day'`(따옴표 안에 전부),\
MySQL 은 `INTERVAL 1 DAY`(따옴표 없이 수와 단위 키워드).\
**이식하면 배포 전에 터지므로 조용하지 않다.** 위험한 것은 `+ 1` 쪽이다.

PG 의 결과 타입도 봐 둔다 — `date + interval` 은 **`timestamp`** 가 되어 `00:00:00` 이 붙는다.

**월말 처리는 둘 다 같다.**

```text
### SQL: SELECT DATE '2026-01-31' + INTERVAL '1 month' AS r;     (PG)
###      SELECT DATE_ADD(DATE '2026-01-31', INTERVAL 1 MONTH) AS r;  (MySQL)
--- PG 18.6 ---
          r          
---------------------
 2026-02-28 00:00:00
(1 row)

--- MySQL 8.4.10 ---
+------------+
| r          |
+------------+
| 2026-02-28 |
+------------+
```

**둘 다 2월 28일로 잘라 준다.** 「1월 31일의 한 달 뒤」가 존재하지 않는 문제를 같은 방식으로 푼다.

### 3. 잘못된 날짜 — PG 는 죽고 MySQL 은 자리에 따라 다르다

**언제 쓰나** — 외부에서 들어온 날짜 문자열을 변환할 때.

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
### SQL: SELECT CAST('2026-13-01' AS DATE) AS d;
--- PG 18.6 ---
ERROR:  date/time field value out of range: "2026-13-01"
LINE 1: SELECT CAST('2026-13-01' AS DATE) AS d;
                    ^
HINT:  Perhaps you need a different "DateStyle" setting.
--- MySQL 8.4.10 ---
+------+
| d    |
+------+
| NULL |
+------+
```

MySQL 은 경고로 말해 준다.

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

**그런데 열에 넣으면 MySQL 도 죽는다.**

```text
--- MySQL 8.4.10 ---
CREATE TEMPORARY TABLE t40 (d DATE);
INSERT INTO t40 VALUES ('2026-02-30');
ERROR 1292 (22007) at line 1: Incorrect date value: '2026-02-30' for column 'd' at row 1
```

그림 해설 — 36번의 `1/0` 과 **똑같은 모양**이다. `SELECT` 에서는 `NULL`, `INSERT` 에서는 에러.\
`sql_mode` 의 `STRICT_TRANS_TABLES` 가 경고를 에러로 올린다.\
대가 — **조회로 검증한 변환이 적재에서 터진다.** 테스트를 `SELECT` 로만 하면 이 차이를 못 본다.

PG 의 `HINT` 가 친절하다 — `DateStyle` 설정이 다르면 `2026-13-01` 이 다르게 읽힐 수도 있음을 알려 준다.

### 4. ★ 시간대 — 붙은 타입과 안 붙은 타입

**언제 쓰나** — 여러 지역의 사용자를 다룰 때. **이 주제에서 가장 비싼 구분이다.**

먼저 PG. **같은 세션에서 시간대만 바꿔 두 번 읽었다.**

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
SHOW timezone;
  TimeZone  
------------
 Asia/Seoul
(1 row)

SELECT TIMESTAMPTZ '2026-09-21 10:00:00+00' AS tz, TIMESTAMP '2026-09-21 10:00:00' AS notz;
           tz           |        notz         
------------------------+---------------------
 2026-09-21 19:00:00+09 | 2026-09-21 10:00:00
(1 row)
```

그림 해설 — **`tz` 는 `10:00+00` → `19:00+09` 로 바뀌었고, `notz` 는 안 바뀌었다.**\
값이 바뀐 게 아니다 — **같은 순간을 다른 이름으로 부른 것**이다. 오프셋 표시가 그 증거다.

**열에 담아도 같다.**

```text
(A) PostgreSQL 18.6                     (B) MySQL 8.4.10
BEGIN;                                   SELECT @@session.time_zone;  -> SYSTEM
CREATE TEMP TABLE t40tz                  CREATE TEMPORARY TABLE t40tz
  (ts timestamptz, dt timestamp);          (ts TIMESTAMP, dt DATETIME);
INSERT INTO t40tz VALUES                 INSERT INTO t40tz VALUES
  ('2026-09-21 10:00:00',                  ('2026-09-21 10:00:00',
   '2026-09-21 10:00:00');                  '2026-09-21 10:00:00');
SELECT ts, dt FROM t40tz;                SELECT ts, dt FROM t40tz;
--- 실제 출력 ---                        --- 실제 출력 ---
           ts           |         dt          +---------------------+---------------------+
------------------------+------------------   | ts                  | dt                  |
 2026-09-21 10:00:00+00 | 2026-09-21 10:00:00 +---------------------+---------------------+
(1 row)                                       | 2026-09-21 10:00:00 | 2026-09-21 10:00:00 |
                                              +---------------------+---------------------+
SET TIME ZONE 'Asia/Seoul';              SET SESSION time_zone = '+09:00';
SELECT ts, dt FROM t40tz;                SELECT ts, dt FROM t40tz;
--- 실제 출력 ---                        --- 실제 출력 ---
           ts           |         dt          +---------------------+---------------------+
------------------------+------------------   | ts                  | dt                  |
 2026-09-21 19:00:00+09 | 2026-09-21 10:00:00 +---------------------+---------------------+
(1 row)                                       | 2026-09-21 19:00:00 | 2026-09-21 10:00:00 |
ROLLBACK;                                     +---------------------+---------------------+
```

두 그림의 결론 — **동작이 완전히 같다.** 갈리는 것은 **타입 이름뿐**이다.

```text
MySQL TIMESTAMP  ->  PG timestamptz   (환산된다)
MySQL DATETIME   ->  PG timestamp     (안 바뀐다)
```

대가 — **이름만 보고 옮기면 정확히 반대가 된다.**\
`MySQL TIMESTAMP` 열을 `PG timestamp` 로 옮기면 **시간대 정보가 사라지고**,\
`MySQL DATETIME` 을 `PG timestamptz` 로 옮기면 **없던 환산이 생긴다.** 둘 다 에러 없이 일어난다.

**명시적 환산 함수는 문법이 다르다.**

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

MySQL 에서 **이름으로도 된다 — 단 시간대 표가 적재돼 있을 때만.**

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

그림 해설 — **이 서버는 1,795개의 시간대 이름을 갖고 있다.**\
적재되지 않은 서버에서는 같은 문이 **`NULL`** 을 돌려준다 — 에러가 아니다.\
대가 — **환경에 따라 조용히 `NULL` 이 되는 함수**다. 오프셋(`'+09:00'`)은 표 없이도 된다.

### 5. ★ `NOW()` 가 고정되나 — 트랜잭션 안에서 실측

**언제 쓰나** — 한 트랜잭션 안에서 여러 번 시각을 찍을 때. **감사 로그·이력 표에서 물린다.**

```text
(A) PostgreSQL 18.6                        (B) MySQL 8.4.10
BEGIN;                                      START TRANSACTION;
SELECT now(), statement_timestamp(),        SELECT NOW(6), SYSDATE(6);
       clock_timestamp();                   SELECT SLEEP(1);
SELECT pg_sleep(1);                         SELECT NOW(6), SYSDATE(6);
SELECT now(), statement_timestamp(),        COMMIT;
       clock_timestamp();
COMMIT;
--- 실제 출력 ---                          --- 실제 출력 ---
now_1   2026-09-21 00:01:03.680036+00      now_1     2026-09-21 00:01:05.861180
stmt_1  2026-09-21 00:01:03.680115+00      sysdate_1 2026-09-21 00:01:05.861212
clock_1 2026-09-21 00:01:03.680356+00
  (1초 잠)                                   (1초 잠)
now_2   2026-09-21 00:01:03.680036+00      now_2     2026-09-21 00:01:06.861700
stmt_2  2026-09-21 00:01:04.681759+00      sysdate_2 2026-09-21 00:01:06.861780
clock_2 2026-09-21 00:01:04.681828+00

 -> now 는 두 번 다 .680036 으로 같다        -> NOW() 가 1초 늘었다. 고정되지 않았다
```

두 그림의 결론 — **PG 의 `now()` 는 트랜잭션 전체에서 고정되고, MySQL 의 `NOW()` 는 문마다 갱신된다.**

**확증이 아니라 반증을 찾으려고 세 판을 돌렸다.**

```text
--- PG 18.6 ---                         --- MySQL 8.4.10 ---
run 1  .680036 / .680036  (같다)        run 1  05.861180 / 06.861700  (다르다)
run 2  .577746 / .577746  (같다)        run 2  19.656219 / 20.656607  (다르다)
run 3  .780803 / .780803  (같다)        run 3  21.881670 / 22.881925  (다르다)
```

**3판 모두 갈리지 않았다.** 그리고 이것은 두 문서가 정한 계약이다 — 우연이 아니다.

**MySQL 의 `NOW()` 도 「한 문 안에서는」 고정된다.**

```text
--- MySQL 8.4.10 ---
SELECT NOW(6) AS a, SLEEP(1) AS s, NOW(6) AS b, SYSDATE(6) AS c;
+----------------------------+---+----------------------------+----------------------------+
| a                          | s | b                          | c                          |
+----------------------------+---+----------------------------+----------------------------+
| 2026-09-21 00:01:06.862056 | 0 | 2026-09-21 00:01:06.862056 | 2026-09-21 00:01:07.862855 |
+----------------------------+---+----------------------------+----------------------------+
```

그림 해설 — `a` 와 `b` 가 **한 마이크로초도 안 틀리고 같다.** 사이에 1초를 잤는데도 그렇다.\
`c`(`SYSDATE()`)만 1초 늘었다 — **`SYSDATE()` 는 호출 순간의 실제 시각**이다.

**PG 쪽에도 세 층이 다 있다.**

```text
now() = transaction_timestamp()   트랜잭션 시작 시각   -> 트랜잭션 내내 고정
statement_timestamp()             문 시작 시각        -> 문마다 갱신
clock_timestamp()                 호출 순간의 시각     -> 부를 때마다 갱신

--- PG 18.6 ---
SELECT clock_timestamp() AS clock_a, clock_timestamp() AS clock_b;
            clock_a            |            clock_b            
-------------------------------+-------------------------------
 2026-09-21 00:01:04.682101+00 | 2026-09-21 00:01:04.682102+00
(1 row)
```

한 문 안에서도 **1마이크로초 차이**가 난다 — 고정되지 않는다는 증거다.

```text
                     PG                        MySQL
트랜잭션 내내 고정    now()                     (없다)
문마다 갱신          statement_timestamp()      NOW() / CURRENT_TIMESTAMP
부를 때마다 갱신      clock_timestamp()          SYSDATE()
```

대가 — **한 트랜잭션에서 여러 행에 시각을 찍을 때 결과가 다르다.**\
PG 는 전부 같은 시각이 박히고, MySQL 은 문마다 다른 시각이 박힌다.\
「이 트랜잭션에서 바뀐 행은 전부 같은 시각」을 보장하려면 **MySQL 에서는 변수에 담아 재사용**해야 한다.

**자동 커밋에서는 PG 도 문마다 바뀐다** — 문 하나가 곧 트랜잭션 하나이기 때문이다.

```text
--- PG 18.6 ---  (BEGIN 없이)
SELECT now() AS now_1;   2026-09-21 00:01:04.778621+00
SELECT pg_sleep(1);
SELECT now() AS now_2;   2026-09-21 00:01:05.780038+00
```

**`now()` 가 바뀌었다.** 「PG 의 `now()` 는 안 바뀐다」가 아니라 **「한 트랜잭션 안에서 안 바뀐다」**다.

`CURRENT_TIMESTAMP` 와 `NOW()` 는 같은 것이다 — **두 엔진 모두.**

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

PG 는 마이크로초까지, MySQL 은 기본이 초 단위다(`NOW(6)` 으로 자릿수를 지정한다).

### 6. 추출과 절단 — `EXTRACT` 는 같고 `DATE_TRUNC` 는 없다

**언제 쓰나** — 월별·일별로 묶을 때.

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

**표준 단위 이름은 같다.** 갈리는 것은 **PG 전용 단위**다.

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

**절단은 함수 자체가 서로 없다.**

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

그림 해설 — **MySQL 의 대응물은 `DATE_FORMAT` 으로 자리를 채우는 방식**이다. `DATE_TRUNC` 같은 전용 함수가 아니다.\
`DATEDIFF` 도 MySQL 에만 있다.

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

대가 — **함수 이름이 서로 없으면 이식에서 에러로 터진다. 시끄럽다.**\
2번의 `+ 1` 만 조용하다.

### 7. 경계 조건 — `BETWEEN` 이 하루를 빠뜨린다

**언제 쓰나** — 「9월 한 달치」를 뽑을 때. **두 엔진이 같은 함정을 갖는다.**

```text
(A) PostgreSQL 18.6                        (B) MySQL 8.4.10
BEGIN;                                      START TRANSACTION;
CREATE TEMP TABLE t40e (id int, at timestamp);  CREATE TEMPORARY TABLE t40e (id int, at DATETIME);
INSERT INTO t40e VALUES                     INSERT INTO t40e VALUES
  (1,'2026-09-30 00:00:00'),                  (1,'2026-09-30 00:00:00'),
  (2,'2026-09-30 13:45:00'),                  (2,'2026-09-30 13:45:00'),
  (3,'2026-10-01 00:00:00');                  (3,'2026-10-01 00:00:00');

SELECT id FROM t40e                         SELECT id FROM t40e
  WHERE at BETWEEN '2026-09-01'               WHERE at BETWEEN '2026-09-01'
               AND '2026-09-30'                            AND '2026-09-30'
  ORDER BY id;                                ORDER BY id;
--- 실제 출력 ---                          --- 실제 출력 ---
 id                                         +------+
----                                        | id   |
  1                                         +------+
(1 row)                                     |    1 |
                                            +------+

SELECT id FROM t40e                         SELECT id FROM t40e
  WHERE at >= '2026-09-01'                    WHERE at >= '2026-09-01'
    AND at <  '2026-10-01'                      AND at <  '2026-10-01'
  ORDER BY id;                                ORDER BY id;
--- 실제 출력 ---                          --- 실제 출력 ---
 id                                         +------+
----                                        | id   |
  1                                         |    1 |
  2                                         |    2 |
(2 rows)                                    +------+
ROLLBACK;                                   ROLLBACK;
```

두 그림의 결론 — **`BETWEEN` 이 `id=2` 를 빠뜨렸다. 두 엔진에서 똑같이.**

```text
'2026-09-30' 은 날짜만 적었으므로 '2026-09-30 00:00:00' 으로 읽힌다
        ↓
BETWEEN ... AND '2026-09-30 00:00:00'
        ↓
9월 30일 00:00:00 은 걸리고, 13:45:00 은 상한을 넘는다
        ↓
★ 하루치가 거의 통째로 빠진다
```

그림 해설 — **`>= 시작 AND < 다음 시작` 이 안전한 형태**다. 상한을 포함하지 않으므로 경계가 겹치지도 빠지지도 않는다.\
대가 — 이 사고는 **날짜만 저장하는 `DATE` 열에서는 안 난다.** 그래서 시간이 붙는 순간 처음 나타난다.

## 문법 — 형태와 규칙

```sql
-- 리터럴 (양쪽 공통)
DATE '2026-09-21'   TIME '10:30:00'   TIMESTAMP '2026-09-21 10:30:00'

-- 간격 산술
ts + INTERVAL '1 day'          -- PG. 따옴표 안에 수와 단위를 함께
ts + INTERVAL 1 DAY            -- MySQL. 따옴표 없이 수 + 단위 키워드
DATE_ADD(ts, INTERVAL 1 MONTH) -- MySQL

-- 절단
DATE_TRUNC('month', ts)                    -- PG
DATE_FORMAT(ts, '%Y-%m-01 00:00:00')       -- MySQL 의 대응 관용구

-- 시간대 환산
ts AT TIME ZONE 'Asia/Seoul'               -- PG
CONVERT_TZ(ts, 'UTC', 'Asia/Seoul')        -- MySQL (시간대 표가 적재돼 있어야)

-- 현재 시각
now() / transaction_timestamp()  statement_timestamp()  clock_timestamp()   -- PG
NOW() / CURRENT_TIMESTAMP        SYSDATE()                                  -- MySQL
```

규칙 여덟.

1. **`MySQL TIMESTAMP` ≈ `PG timestamptz`, `MySQL DATETIME` ≈ `PG timestamp`** 다. 이름이 어긋난다.
2. **`날짜 + 정수` 는 PG 에서 「N일 뒤」, MySQL 에서 「수치 덧셈」이다.** 쓰지 않는다.
3. **`날짜 - 날짜` 도 같은 함정이다.** 같은 달 안에서는 우연히 맞는다.
4. **`INTERVAL` 문법이 서로를 거부한다.** 이식에서 에러로 터지므로 오히려 안전하다.
5. **잘못된 날짜는 PG 에서 늘 에러, MySQL 에서 `SELECT` 는 `NULL` · `INSERT` 는 에러**다.
6. **`now()` 는 PG 에서 트랜잭션 내내 고정, MySQL 에서 문마다 갱신**된다. 둘 다 **한 문 안에서는 고정**이다.
7. **`EXTRACT` 의 표준 단위는 공통**이고 `DOW` 같은 PG 전용 단위가 있다.
8. **범위 조건은 `>= 시작 AND < 다음 시작`** 으로 쓴다. `BETWEEN` 은 하루를 빠뜨린다.

#### 방언 요약

| 자리 | PostgreSQL 18.6 | MySQL 8.4.10 |
|---|---|---|
| 시간대 있는 타입 | `timestamptz` | **`TIMESTAMP`** |
| 시간대 없는 타입 | `timestamp` | **`DATETIME`** |
| 리터럴 표기 | `DATE '...'`·`TIME '...'`·`TIMESTAMP '...'` | 같다 |
| `DATE '2026-09-21' + 1` | `2026-09-22`(날짜) | **`20260922`(정수)** |
| `DATE '2026-10-01' - DATE '2026-09-21'` | `10`(일수) | **`80`(수치 뺄셈)** |
| 간격 더하기 | `+ INTERVAL '1 day'` | `+ INTERVAL 1 DAY` (서로 구문 오류) |
| 월말 보정 | `2026-01-31 + 1 month` = `2026-02-28` | 같다 |
| `CAST('2026-02-30' AS DATE)` | `ERROR: date/time field value out of range` | `NULL` + 경고 1292 |
| `INSERT` 에 잘못된 날짜 | 에러 | `ERROR 1292`(strict 모드) |
| 시간대 환산 | `AT TIME ZONE` | `CONVERT_TZ()` (서로 없다) |
| 시간대 이름 지원 | 내장 | **`mysql.time_zone_name` 적재 필요** — 없으면 `NULL` |
| 절단 | `DATE_TRUNC('month', ts)` | 없다 — `DATE_FORMAT` 관용구 |
| 일수 차 | `date - date` | `DATEDIFF()` |
| `EXTRACT(DOW ...)` | 된다 | **`ERROR 1064`** |
| 트랜잭션 안 `NOW()` | **고정**(`now()` = 트랜잭션 시각) | **문마다 갱신** |
| 문 안에서 `NOW()` | 고정(`statement_timestamp`) | 고정 |
| 호출 순간의 시각 | `clock_timestamp()` | `SYSDATE()` |
| `BETWEEN` 경계 함정 | 있다 | 있다 — **같다** |

## 어디서 틀리나

- **`MySQL TIMESTAMP` 를 `PG timestamp` 로 옮긴다.**\
  이름은 같은데 **시간대 정보가 사라진다.** 옮길 곳은 `timestamptz` 다. 에러가 안 난다.
- **`날짜 + 1` 로 하루를 더한다.**\
  MySQL 에서 **정수 연산**이 된다. `2026-09-30 + 1` 은 `20260931` — 없는 날짜다.
- **`날짜 - 날짜` 로 일수를 구한다.**\
  같은 달 안에서는 맞는 답이 나와 **테스트를 통과한다.** 달을 넘기면 틀린다.
- **`BETWEEN 시작 AND 끝` 으로 기간을 자른다.**\
  끝날의 `00:00:00` 이후가 전부 빠진다. **두 엔진 공통**이다. `>= AND <` 로 쓴다.
- **트랜잭션 안에서 `NOW()` 가 같다고 가정한다.**\
  PG 에서는 맞고 **MySQL 에서는 틀리다.** 같은 시각을 박으려면 변수에 담는다.
- **`SELECT` 로만 날짜 변환을 검증한다.**\
  MySQL 은 `SELECT` 에서 `NULL`, `INSERT` 에서 `ERROR 1292` 다.
- **`CONVERT_TZ` 에 시간대 이름을 쓴다.**\
  **시간대 표가 적재된 서버에서만** 된다. 없으면 **에러가 아니라 `NULL`** 이다. 배포 환경에서 확인한다.
- **`EXTRACT(DOW ...)` 를 MySQL 로 옮긴다.**\
  `ERROR 1064` 다. 시끄러우니 안전하다 — MySQL 은 `DAYOFWEEK()` 계열을 쓴다.
- **시간대를 안 밝히고 날짜 결과를 보고한다.**\
  `SHOW timezone` / `SELECT @@session.time_zone` 을 안 찍으면 **그 결과는 재현할 수 없다.**

## 구현 세부사항 대 언어 보장

- **언어(문서)가 정한 것** — 타입의 의미(시간대 유무), `INTERVAL` 문법, 잘못된 날짜의 처리,\
  `now()`/`NOW()` 의 고정 범위, `EXTRACT` 의 단위. 두 매뉴얼의 날짜·시간 페이지가 정본이다.\
  ★ **5번의 결과는 「세 번 돌려 같았다」가 아니라 두 문서가 정한 계약이다** — 그래서 보장으로 적는다.
- **★ 설정이 정하는 것** — **4번의 모든 출력.**\
  PG `TimeZone` = `Etc/UTC`, MySQL `time_zone` = `SYSTEM`(= `UTC`)에서 나온 결과다.\
  다른 시간대의 서버에서는 **같은 질의가 다른 시각을 보여 준다.** 「시간대 확인」 절을 본문 앞에 둔 이유다.
- **★ 서버 구성이 정하는 것** — **`CONVERT_TZ` 에 이름을 쓸 수 있는지.**\
  이 서버에는 `mysql.time_zone_name` 에 1,795행이 적재돼 있다. **적재는 서버 구축 시의 선택**이다.\
  적재되지 않은 서버에서는 같은 문이 조용히 `NULL` 을 돌려준다.
- **`sql_mode` 가 정하는 것** — 3번의 `INSERT` 가 에러인지(`STRICT_TRANS_TABLES`).
- **정밀도** — PG 는 마이크로초, MySQL 은 기본이 초다(`NOW(6)` 으로 지정). 5번의 측정에 이 차이가 쓰였다.
- **`SLEEP`/`pg_sleep` 의 실제 잠든 시간**은 정확히 1초가 아니다 — 출력의 소수부가 그것을 보여 준다.\
  5번에서 읽을 것은 **절댓값이 아니라 「두 값이 같은가 다른가」**다.

## 언제 쓰고 언제 안 쓰나

- **쓴다 — 시각 저장에 `timestamptz` / `TIMESTAMP`.** 여러 지역의 사용자가 있으면 기본 선택이다.
- **쓴다 — 「벽시계 시각」에 `timestamp` / `DATETIME`.** 회의 시작처럼 **현지 시각 자체가 의미**인 경우.
- **쓴다 — `>= 시작 AND < 다음 시작`.** 기간 조건의 표준형이다.
- **안 쓴다 — `날짜 + 정수`·`날짜 - 날짜`.** 이식성이 없고 MySQL 에서 뜻이 다르다.
- **안 쓴다 — `BETWEEN` 으로 기간 자르기.** 시간이 붙은 열에서는 하루가 빠진다.
- **안 쓴다 — 열에 날짜 함수.** `WHERE DATE(at) = '2026-09-21'` 은 인덱스를 죽인다(35번 8번).\
  `WHERE at >= '2026-09-21' AND at < '2026-09-22'` 로 쓴다.
- **조심한다 — 애플리케이션과 DB 의 시간대가 다를 때.** 둘 다 UTC 로 맞추고 **표시할 때만 환산**하는 편이 대개 낫다.
- **조심한다 — MySQL 에서 트랜잭션 전체의 시각.** 변수에 한 번 담아 재사용한다.

## 핵심 문장

- 날짜·시간의 첫 질문은 **「시간대가 붙어 있나」** 하나다.
- **`MySQL TIMESTAMP` ≈ `PG timestamptz`, `MySQL DATETIME` ≈ `PG timestamp`** — **이름이 어긋난다.**
- **`DATE '2026-09-21' + 1` 은 PG 에서 `2026-09-22`, MySQL 에서 `20260922`(정수)** 다.
- **`DATE '2026-10-01' - DATE '2026-09-21'` 은 PG `10`, MySQL `80`** — 같은 달에서는 우연히 맞는다.
- `INTERVAL` 문법은 **PG `'1 day'` / MySQL `1 DAY`** 로 서로를 거부한다.
- 잘못된 날짜는 **PG 에서 늘 에러, MySQL 에서 `SELECT` 는 `NULL` · `INSERT` 는 `ERROR 1292`** 다.
- ★ **`now()` 는 PG 에서 트랜잭션 내내 고정, MySQL 의 `NOW()` 는 문마다 갱신**된다(3판 실측).\
  둘 다 **한 문 안에서는 고정**이고, 호출 순간의 시각은 `clock_timestamp()` / `SYSDATE()` 다.
- **`BETWEEN` 으로 기간을 자르면 두 엔진에서 똑같이 하루가 빠진다.** `>= AND <` 로 쓴다.
- **시간대를 안 밝힌 날짜 결과는 재현할 수 없다.**

## 관련 자료

- [PostgreSQL 18 · Date/Time Types](https://www.postgresql.org/docs/18/datatype-datetime.html) — `timestamp` 와 `timestamptz` 의 차이.
- [PostgreSQL 18 · Date/Time Functions and Operators](https://www.postgresql.org/docs/18/functions-datetime.html) — `now()`·`statement_timestamp()`·`clock_timestamp()` 의 고정 범위.
- [MySQL 8.4 · Date and Time Data Types](https://dev.mysql.com/doc/refman/8.4/en/date-and-time-types.html) — `TIMESTAMP` 가 시간대 환산을 한다는 것.
- [MySQL 8.4 · Date and Time Functions](https://dev.mysql.com/doc/refman/8.4/en/date-and-time-functions.html) — `NOW()` 와 `SYSDATE()` 의 차이.
- [35 타입 체계와 캐스팅](../35-type-system-and-casting/) — 문자열을 날짜로 바꾸는 변환의 일반 규칙.
- [36 수치 타입과 수치 함수](../36-numeric-types-and-functions/) — `SELECT` 는 `NULL` · `INSERT` 는 에러라는 같은 패턴(`1/0`).
- [04 NULL 의 3값 논리](../04-null-three-valued-logic/) — 변환 실패가 `NULL` 이 된 뒤의 전파.
- [SQL 주제 목록](../README.md) — 08(ORDER BY) · 45(기본값·생성 열) · 47(인덱스를 언제 타나) · 55(트랜잭션 경계) 가 이웃이다.

## 용어 풀이

- **시간대(time zone)** — 같은 순간을 지역마다 다른 시각으로 부르는 규칙.\
  예: UTC 10:00 은 서울에서 19:00 이다. 같은 순간, 다른 이름.
- **`timestamptz` / `TIMESTAMP`** — 시간대가 붙은 타입. 읽는 시간대로 환산돼 보인다.\
  예: 세션 시간대를 `Asia/Seoul` 로 바꾸면 `10:00:00+00` 이 `19:00:00+09` 로 보인다.
- **`timestamp` / `DATETIME`** — 시간대가 없는 타입. 「벽시계 시각」이다.\
  예: 세션 시간대를 바꿔도 `2026-09-21 10:00:00` 그대로다.
- **`INTERVAL`** — 기간을 나타내는 값.\
  예: PG `INTERVAL '1 day'`, MySQL `INTERVAL 1 DAY`. 서로 구문 오류를 낸다.
- **`AT TIME ZONE`** — PG 에서 시간대를 환산하는 연산자.\
  예: `TIMESTAMPTZ '...+00' AT TIME ZONE 'Asia/Seoul'` → 시간대 없는 서울 벽시계 시각.
- **`CONVERT_TZ`** — MySQL 의 시간대 환산 함수.\
  예: `CONVERT_TZ(t,'UTC','Asia/Seoul')`. 시간대 표가 없으면 **`NULL`** 이다.
- **`transaction_timestamp()`** — PG 에서 트랜잭션이 시작된 시각. `now()` 와 같다.\
  예: 1초를 자고 다시 불러도 값이 안 바뀐다.
- **`clock_timestamp()` / `SYSDATE()`** — 호출 순간의 실제 시각.\
  예: 한 문 안에서 두 번 부르면 마이크로초가 다르다.
- **`mysql.time_zone_name`** — MySQL 이 시간대 **이름**을 해석하려고 읽는 표.\
  예: 이 서버에는 1,795행이 적재돼 있어 `'Asia/Seoul'` 이 통한다.
- **경계 조건(`>=` / `<`)** — 기간을 자를 때 상한을 포함하지 않는 형태.\
  예: `at >= '2026-09-01' AND at < '2026-10-01'` 은 9월 전체를 빠짐없이 포함한다.

## 더 들어가면

- **`timestamptz` 는 시간대를 저장하지 않는다.** 이름과 달리, PG 는 값을 **UTC 한 순간**으로 저장하고\
  읽을 때 세션 시간대로 환산해 보여 준다. 「어느 시간대에서 입력했나」는 **남지 않는다.**\
  그 정보가 필요하면 시간대 이름을 **별도 열**에 저장해야 한다.
- **MySQL 의 `TIMESTAMP` 는 범위가 좁다.** 내부적으로 초 단위 정수로 저장해서 상한이 있다.\
  먼 미래 날짜를 담아야 하면 `DATETIME` 을 고려한다 — 대신 시간대 환산을 잃는다.
- **`NOW()` 의 고정 범위가 다른 이유는 설계 철학의 차이**다.\
  PG 는 「한 트랜잭션은 한 시점의 스냅숏」이라는 관점이 일관되고(목록의 56번 주제),\
  MySQL 은 「문 하나가 단위」에 가깝다. **어느 쪽도 버그가 아니다.**
- **시간대 계산의 진짜 어려움은 서머타임**이다. 「존재하지 않는 시각」과 「두 번 오는 시각」이 생긴다.\
  UTC 로 저장하고 **표시할 때만 환산**하면 그 문제가 데이터에 들어오지 않는다.
- **날짜 열에 함수를 씌우지 않는 습관**이 이 주제의 실무 핵심이다.\
  `DATE(at) = '2026-09-21'` 대신 `at >= '2026-09-21' AND at < '2026-09-22'` —\
  결과가 같고 **인덱스가 산다.** 35번·37번·38번·39번에서 반복된 그 한 문장이다.
