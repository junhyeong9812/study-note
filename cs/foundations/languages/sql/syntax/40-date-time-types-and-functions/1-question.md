# sql/40-날짜·시간 타입과 함수 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,\
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.\
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.

대상은 **PostgreSQL 18.6** 과 **MySQL 8.4.10** 두 서버다. 「두 엔진에서」라고 물으면 **각각** 답한다.

★ **시간대를 먼저 읽어라 — 이 주제의 답은 이 설정에서 나온 것이다.**

```text
PG     SHOW timezone              ->  Etc/UTC
MySQL  @@global.time_zone         ->  SYSTEM
       @@session.time_zone        ->  SYSTEM
       @@system_time_zone         ->  UTC
       mysql.time_zone_name 행 수 ->  1795  (시간대 이름표가 적재돼 있다)

MySQL sql_mode 는 기본값 — STRICT_TRANS_TABLES · NO_ZERO_DATE 포함
```

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 0. 환경을 어떻게 확인하나 (연결)

- 두 엔진에서 「지금 이 서버의 시간대가 무엇인가」를 확인하는 명령은 각각 무엇인가?

### 1. ★ 날짜에 1 을 더하면 (예측)

```sql
SELECT DATE '2026-09-21' + 1 AS plus1;
SELECT DATE '2026-09-30' + 1 AS plus1;
```

- 두 문이 두 엔진에서 각각 무엇을 돌려주는가?

### 2. ★ 날짜끼리 빼면 (예측)

```sql
SELECT DATE '2026-09-21' - DATE '2026-09-01' AS diff;   -- (a)
SELECT DATE '2026-10-01' - DATE '2026-09-21' AS diff;   -- (b)
```

- (a) 와 (b) 가 두 엔진에서 각각 무엇인가 — 그리고 왜 (a) 만 같은가?

### 3. `INTERVAL` 문법 (예측)

```sql
SELECT DATE '2026-09-21' + INTERVAL '1 day' AS r;   -- (a)
SELECT DATE '2026-09-21' + INTERVAL 1 DAY  AS r;    -- (b)
```

- 두 문이 두 엔진에서 각각 어떻게 되는가?

### 4. 잘못된 날짜 (예측)

```sql
SELECT CAST('2026-02-30' AS DATE) AS d;     -- (a)
INSERT INTO t40 VALUES ('2026-02-30');      -- (b) t40 (d DATE)
```

- (a) 와 (b) 가 두 엔진에서 각각 어떻게 되는가?

### 5. ★ 시간대가 붙은 타입 (예측)

```sql
-- PG:    (ts timestamptz, dt timestamp)
-- MySQL: (ts TIMESTAMP,   dt DATETIME)
-- 둘 다 '2026-09-21 10:00:00' 을 넣고, 세션 시간대를 +09:00 으로 바꾼 뒤 다시 읽는다
```

- 두 열이 두 엔진에서 각각 어떻게 보이는가 — 그리고 두 엔진의 타입 이름은 어떻게 대응하는가?

### 6. ★ 트랜잭션 안에서 `NOW()` (예측)

```sql
BEGIN;  SELECT now();  SELECT pg_sleep(1);  SELECT now();  COMMIT;              -- PG
START TRANSACTION;  SELECT NOW(6);  SELECT SLEEP(1);  SELECT NOW(6);  COMMIT;   -- MySQL
```

- 두 번 찍은 값이 두 엔진에서 각각 같은가 다른가?

### 7. 한 문 안에서는 (경계)

- `SELECT NOW(6), SLEEP(1), NOW(6), SYSDATE(6)` 의 네 값 중 어느 것이 같고 어느 것이 다른가?

### 8. ★ 기간을 자르는 조건 (예측)

```sql
-- 2026-09-30 00:00:00 / 2026-09-30 13:45:00 / 2026-10-01 00:00:00 세 행이 있다
WHERE at BETWEEN '2026-09-01' AND '2026-09-30'      -- (a)
WHERE at >= '2026-09-01' AND at < '2026-10-01'      -- (b)
```

- (a) 와 (b) 가 각각 몇 행을 돌려주는가 — 두 엔진에서 다른가?

### 9. 절단과 추출 (경계)

- `DATE_TRUNC`·`DATEDIFF`·`EXTRACT(DOW ...)` 는 두 엔진에 각각 있는가?

### 10. 시간대 이름이 안 통할 때 (경계)

- `CONVERT_TZ(t,'UTC','Asia/Seoul')` 이 `NULL` 을 돌려주는 서버가 있는 이유는 무엇인가?

### 11. 그래서 어떻게 설계하나 (연결)

- 여러 지역의 사용자가 쓰는 서비스에서 시각을 어떻게 저장하고 언제 환산하는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
