# database/27-temporal-types-and-session-timezone — 시간 타입과 세션 시간대: 9시간 밀림과 날짜 경계 — 정리 (힌트)

## 해결하는 문제

"2026-10-01 10:00"이라는 글자만으로는 **시각**이 정해지지 않는다.\
서울의 10시와 런던의 10시는 9시간(서머타임 기간엔 8시간) 떨어진 다른 순간이다.

```text
  같은 글자 "2026-10-01 10:00"
     서울 기준으로 읽으면  → 2026-10-01 01:00 UTC
     UTC 기준으로 읽으면   → 2026-10-01 10:00 UTC     ← 둘은 9시간 차이
```

쉬운 예: 해외 친구에게 "내일 10시에 전화할게"라고 적은 쪽지다.
- 누구의 10시인지 안 적으면, 받는 사람은 자기 시계로 읽는다.

똑같은 구조다.\
앱(JVM)·드라이버·DB 세션이 각자 "기본 시간대"를 가지고, 시간대 없는 글자를 각자의 기준으로 읽는다.\
기준이 하나라도 어긋나면 값이 **조용히** 밀린다. 에러는 나지 않는다.

실무 예:
- 결제 시각이 DB에 9시간 뒤로 찍혀 있다. JVM은 KST, DB 세션은 UTC였다.
- 일별 매출 리포트에서 10월 1일 새벽 매출이 9월 30일로 잡힌다. `date_trunc('day', ...)`가 UTC 자정으로 잘랐다.
- MySQL `TIMESTAMP` 컬럼에 만기일 `2040-01-01`을 넣자 `ERROR 1292`가 난다.

## 동작·원리

### 1. 두 종류의 "시간" — 순간(instant) vs 벽시계(wall clock)

```text
  순간(instant)      타임라인 위의 한 점.  "UTC 기준 몇 초"로 환원된다.   예) 결제 시각, 로그 시각
  벽시계(local)      달력·시계에 적힌 글자. 어느 시간대인지 정보가 없다.   예) "매일 09:00 알림", 생일
```

  - *순간*: 전 세계 어디서 봐도 같은 한 점. 저장할 때는 UTC로 정규화하면 된다.
  - *벽시계 값*: "그 지역의 몇 시"라는 뜻이라, 시간대 규칙이 바뀌어도 글자를 지켜야 할 때 쓴다.

DB 타입은 이 둘에 대응한다.

| 뜻 | PostgreSQL 17 | MySQL 8.4 | Java(`java.time`) |
|---|---|---|---|
| 순간 | `timestamptz`(= timestamp with time zone) | `TIMESTAMP` | `Instant`, `OffsetDateTime` |
| 벽시계 | `timestamp`(= without time zone) | `DATETIME` | `LocalDateTime` |

- 주의: 이름에 속지 않는다. PG `timestamptz`는 **시간대를 저장하지 않는다.** 입력을 UTC로 바꿔 저장하고, 원래 시간대는 버린다(문서 8.5.1.3).
- PG에서 그냥 `timestamp`라고 쓰면 SQL 표준대로 **without time zone**이다(문서).

### 2. PostgreSQL 17 — 입력과 출력 모두 세션 `TimeZone`을 거친다

```text
  입력 '2026-10-01 00:30:00' ─┬─ timestamp  : 글자 그대로 저장(시간대 표시가 있어도 조용히 무시)
                             └─ timestamptz: 시간대 표시가 없으면 세션 TimeZone으로 해석 → UTC로 저장
  출력                         timestamptz  : 저장된 UTC → 세션 TimeZone으로 바꿔서 보여 줌
```

로컬 재현(예시, PostgreSQL 17.11). 세션을 `Asia/Seoul`로 두고 같은 글자를 두 컬럼에 넣은 뒤, 세션을 `UTC`로 바꿔 다시 읽었다.

```text
  SET TimeZone='Asia/Seoul';  INSERT ... ('2026-10-01 00:30:00', '2026-10-01 00:30:00')
                               a (timestamp)         b (timestamptz)
  Asia/Seoul 세션에서 읽기     2026-10-01 00:30:00   2026-10-01 00:30:00+09
  UTC 세션에서 읽기            2026-10-01 00:30:00   2026-09-30 15:30:00+00   ← 같은 순간, 표시만 바뀜
```

- `timestamptz`는 세션을 바꿔도 **같은 순간**이다. 표시만 달라진다.
- `timestamp`는 세션과 무관하게 글자가 그대로다. 대신 어느 시간대의 글자였는지는 아무도 모른다.

### 3. 9시간 밀림 — 시간대 없는 글자를 서로 다른 기준으로 읽을 때

```text
  앱(JVM=Asia/Seoul)이 "2026-10-01 10:00:00"(서울 10시) 글자를 보냄
       │
       ├─ DB 세션 TimeZone = Asia/Seoul → 01:00 UTC 로 저장   ✔ 의도대로
       └─ DB 세션 TimeZone = UTC        → 10:00 UTC 로 저장   ✘ 서울 기준 19:00 → 9시간 뒤로 밀림
```

로컬 재현(예시, PostgreSQL 17.11): 같은 글자를 UTC 세션과 Asia/Seoul 세션에서 `timestamptz`에 넣었다. 읽어 보니 두 행의 차이가 정확히 `-09:00:00`이었다.

MySQL 8.4의 `TIMESTAMP`도 같다. 문서: "MySQL converts TIMESTAMP values from the current time zone to UTC for storage, and back ... for retrieval. (This does not occur for other types such as DATETIME.)" 세션마다 `time_zone`을 따로 가질 수 있고, 기본은 서버 시간대(`SYSTEM`)다.

```text
  (예시, MySQL 8.4.10) SET time_zone='+09:00'; INSERT (1, '2026-10-01 00:30:00', 같은 값)
                         a DATETIME            b TIMESTAMP           UNIX_TIMESTAMP(b)
  +09:00 세션에서 읽기    2026-10-01 00:30:00   2026-10-01 00:30:00
  +00:00 세션에서 읽기    2026-10-01 00:30:00   2026-09-30 15:30:00   1790782200
```

- `DATETIME`은 세션이 바뀌어도 글자가 그대로다.
- 8.4는 리터럴에 오프셋을 붙일 수 있다. 로컬 재현에서 `+09:00` 세션에 `'2026-10-01 00:30:00+00:00'`을 넣으니 `DATETIME`에는 세션 시간대로 바꾼 `09:30:00`이 저장됐다. 원래 오프셋은 남지 않는다.

### 4. 드라이버라는 세 번째 기준

DB 세션 시간대와 별개로 **드라이버**도 변환을 한다. 계층이 셋이다.

```text
  Java 객체 ──(드라이버 변환)──▶ SQL 글자/바이너리 ──(세션 time_zone 해석)──▶ 저장값
   JVM 기본 시간대             connectionTimeZone 등                  DB 세션 설정
```

- **MySQL Connector/J 8.0.23+**(문서 6.3.11 Datetime types processing)
  - `preserveInstants`(기본 true): `java.sql.Timestamp`·`OffsetDateTime` 같은 순간 값을 순간 그대로 보존하려고 변환한다.
  - `connectionTimeZone`(기본 `LOCAL`): 드라이버가 "DB 세션 시간대"를 무엇으로 가정할지. `LOCAL`이면 **JVM 기본 시간대와 같다고 가정**한다.
  - `forceConnectionTimeZoneToSession`(기본 false): true면 그 시간대를 세션 `time_zone`에 실제로 설정한다.
  - 함정: 기본 조합(`LOCAL` + force=false)에서 JVM은 KST, 서버 세션은 UTC이면 가정이 틀린다. 드라이버는 변환하지 않고, 서버는 받은 글자를 UTC로 읽는다 → 9시간 밀림.
  - `serverTimezone`은 8.0.23부터 `connectionTimeZone`의 별칭이다.
- **PostgreSQL JDBC**(pgJDBC 문서 "Using Java 8 Date and Time classes")
  - `timestamptz` ↔ `OffsetDateTime`, `timestamp` ↔ `LocalDateTime`을 지원한다.
  - `ZonedDateTime`, `Instant`는 `setObject`/`getObject`로 **지원하지 않는다**고 적혀 있다. 읽어 온 `OffsetDateTime`은 항상 오프셋 0(UTC)이다.
- **Hibernate 6.6**(User Guide): `hibernate.jdbc.time_zone`을 주면 `setTimestamp(..., Calendar)`에 그 시간대를 넘긴다. 없으면 드라이버가 JVM 기본 시간대를 쓴다.

### 5. 날짜 경계 — "하루"는 시간대마다 다르다

`date_trunc('day', ts)`는 `timestamptz`를 **세션 TimeZone의 자정**으로 자른다(문서 9.9.2). PostgreSQL은 세 번째 인자로 시간대를 줄 수 있다.

```text
  (예시, PostgreSQL 17.11, 세션 UTC) 판매 4건 — 한국 시각
    09-30 23:59 KST  100
    10-01 00:30 KST  200   ← 한국 기준 10월 1일
    10-01 08:59 KST  300   ← 한국 기준 10월 1일
    10-01 09:00 KST  400

  date_trunc('day', sold_at)                 → 09-30: 600 / 10-01: 400   ✘ 새벽 매출이 전날로
  date_trunc('day', sold_at, 'Asia/Seoul')   → 09-30: 100 / 10-01: 900   ✔ 한국 기준
```

- 한국 00:00~08:59는 UTC로는 **전날** 15:00~23:59다. UTC 자정으로 자르면 이 9시간이 전날로 넘어간다.
- 범위 조회도 경계를 시간대 포함으로 쓴다: `sold_at >= '2026-10-01 00:00+09' AND sold_at < '2026-10-02 00:00+09'`. 반열린 구간 `[시작, 끝)`이면 경계 중복·누락이 없다.

### 6. MySQL `TIMESTAMP`의 2038년 상한

```text
  TIMESTAMP 범위: '1970-01-01 00:00:01' UTC ~ '2038-01-19 03:14:07' UTC   (문서 13.2.2)
  2^31 − 1 = 2147483647 초  →  1970-01-01 00:00:00 UTC + 2147483647 초 = 2038-01-19 03:14:07 UTC
```

- 부호 있는 32비트 초 카운터의 끝과 같은 날이다.
- 로컬 재현(MySQL 8.4.10, strict 모드): UTC 세션에서 `'2038-01-19 03:14:07'`은 들어갔다. `'2038-01-20 00:00:00'`은 `ERROR 1292 (22007): Incorrect datetime value`로 거절됐다.
- 세션이 `+09:00`이면 한계 글자가 `'2038-01-19 12:14:07'`이 된다. `'2038-01-19 12:14:08'`(= UTC 03:14:08)은 거절됐다. 상한은 **UTC 기준**이다.
- 소수 초 정밀도(예: `TIMESTAMP(6)`)를 쓰면 상한은 `'2038-01-19 03:14:07.499999'` UTC다(문서 13.2.2).
- `DATETIME`은 `'9999-12-31 23:59:59'`(소수 초 포함 시 `.499999`)까지 된다. PostgreSQL `timestamp`/`timestamptz`는 294276 AD까지다(문서 표 8.9).

## 쓰이는 자료구조·알고리즘

- **epoch 정수 표현**: 순간은 "기준 시각부터 몇 초·마이크로초"라는 정수 하나다. Unix·MySQL `TIMESTAMP`의 기준은 1970-01-01 UTC다. PostgreSQL 타임스탬프는 8바이트, 해상도 1마이크로초다(문서 표 8.9). 내부 기준일은 2000-01-01이다(소스 `src/include/datatype/timestamp.h`의 `POSTGRES_EPOCH_JDATE`). 32비트 초 정수의 상한이 2038년 문제다.
- **시간대 규칙 = 구간 표(IANA tz database)**: 지역마다 "이 순간부터 저 순간까지 오프셋 +9" 같은 구간 목록이다. 변환은 순간이 속한 구간을 찾아 그 구간의 오프셋을 적용하는 일이다. PostgreSQL은 IANA 데이터를 쓴다(문서 8.5.3). MySQL은 `mysql.time_zone*` 테이블을 채워야 이름(`Asia/Seoul`)을 쓸 수 있다. 비어 있으면 `ERROR 1298 Unknown or incorrect time zone`(문서 7.1.15). 이번 로컬 컨테이너(MySQL 8.4.10)에는 채워져 있었다.
- **반열린 구간 [start, end)**: 날짜 경계 계산의 기본 형태다. 이어 붙여도 겹침·틈이 없다.
- **B+Tree 범위 스캔**: `sold_at` 인덱스는 순간 순서로 정렬된다. 경계를 시간대 포함 상수로 쓰면 인덱스 범위 스캔을 **쓸 수 있다**(실제로 고를지는 비용 판단 — 작은 테이블이면 순차 스캔일 수 있다, 문서 14.1). 컬럼에 함수(`date(sold_at)`)를 씌우면 일반 인덱스를 못 탄다(09번 노트).

## 적용 — 풀어나가는 법

**1) 타입을 뜻으로 고른다.**

```text
  "언제 일어났나"(결제·로그·생성 시각)        → timestamptz / TIMESTAMP(2038 한계 주의) / Instant
  "그 지역 시계로 몇 시"(영업시간, 매일 알림)   → timestamp / DATETIME / LocalDateTime + 별도 시간대 컬럼
  "날짜만"(생일)                            → date / DATE / LocalDate
```

- MySQL에서 2038년 이후 값이 올 수 있으면 `DATETIME`을 쓰고 **UTC로 저장한다는 규약**을 둔다. 이때 DB는 변환해 주지 않으므로 규약을 코드로 강제해야 한다.

**2) 세 기준을 한 곳으로 모은다.**

```text
  JVM:     -Duser.timezone=UTC      (또는 코드에서 Instant/OffsetDateTime만 쓰기)
  드라이버: MySQL  connectionTimeZone=UTC&forceConnectionTimeZoneToSession=true
           Hibernate  hibernate.jdbc.time_zone=UTC
  DB 세션:  PG  SET TimeZone='UTC' 또는 ALTER ROLE app SET TimeZone='UTC'
```

**3) 지금 기준이 무엇인지 확인한다.**

```sql
-- PostgreSQL
SHOW TimeZone;
SELECT now(), now() AT TIME ZONE 'UTC';
-- MySQL
SELECT @@session.time_zone, @@global.time_zone, @@system_time_zone, NOW(), UTC_TIMESTAMP();
```

```java
// 앱 쪽: 드라이버가 받은 값과 JVM 시간대를 함께 로그로
log.info("jvmTz={}, now={}", java.time.ZoneId.systemDefault(), java.time.Instant.now());
```

**4) 집계는 "누구의 하루인가"를 명시한다.**

```sql
-- PostgreSQL 17: 한국 기준 일별 매출
SELECT date_trunc('day', sold_at, 'Asia/Seoul') AT TIME ZONE 'Asia/Seoul' AS kst_day,
       sum(amount)
FROM sales GROUP BY 1 ORDER BY 1;

-- MySQL 8.4: TIMESTAMP 컬럼이면 세션 time_zone을 맞추고 DATE()로 자른다
SET time_zone = '+09:00';
SELECT DATE(sold_at) AS kst_day, SUM(amount) FROM sales GROUP BY kst_day;
```

**5) API 경계는 RFC 3339 형식으로 오프셋을 붙인다.** `2026-10-01T01:00:00Z` 또는 `2026-10-01T10:00:00+09:00`. 오프셋 없는 글자는 받지 않는다.

## 장애 시나리오와 대처

**① 저장값이 9시간 밀림 (커리큘럼 ⚠)**
- 현상: 주문 상세의 결제 시각이 실제보다 9시간 늦게(또는 이르게) 보인다. 새로 쌓인 데이터만 그렇다.
- 보이는 형태: 에러 없음. 같은 행을 `UTC` 세션과 `Asia/Seoul` 세션에서 조회하면 한쪽만 맞는다. 배포나 서버 교체 직후부터 시작된 경우가 많다(새 이미지의 JVM·OS 시간대가 바뀜).
- 원인: JVM·드라이버·DB 세션 중 둘 이상이 서로 다른 시간대를 기준으로 시간대 없는 글자를 주고받았다. 예: Connector/J 기본값(`connectionTimeZone=LOCAL`)이 JVM(KST)=세션이라고 가정했는데 세션은 UTC였다.
- 대처: 기준을 UTC로 통일하고(적용 2단계), 순간은 `Instant`/`OffsetDateTime` + `timestamptz`/`TIMESTAMP`로 다룬다. 이미 밀린 데이터는 **밀린 기간을 특정한 뒤** 그 구간만 보정한다(보정은 되돌릴 수 없는 데이터 변경이므로 백업·표본 검증 후).

**② 일별 매출이 전날로 (커리큘럼 ⚠)**
- 현상: 한국 기준 10월 1일 새벽 매출이 9월 30일 합계에 들어간다.
- 보이는 형태: 대시보드 일 합계와 정산 시스템 일 합계가 다르다. 차이는 매일 00:00~08:59 KST 구간의 금액이다.
- 원인: 세션 시간대가 UTC인 채로 `date_trunc('day', ...)`·`DATE(...)`를 썼다. UTC 자정 = KST 09:00이다.
- 대처: `date_trunc(..., 'Asia/Seoul')`로 기준을 명시하거나, 경계를 `+09` 포함 상수로 쓴다. 리포트 쿼리마다 "누구의 하루"를 코드 리뷰 항목으로 둔다.

**③ MySQL `TIMESTAMP` 2038 상한 (커리큘럼 ⚠)**
- 현상: 30년 만기 대출·장기 구독의 만료일 저장이 실패한다. 또는 이미 비-strict 모드라 `0000-00-00 00:00:00`으로 들어가 있다.
- 보이는 형태: strict 모드면 `ERROR 1292 (22007): Incorrect datetime value`. 비-strict면 경고만 남고 "zero" 값으로 저장(문서 13.2.2).
- 원인: `TIMESTAMP`의 상한은 `2038-01-19 03:14:07` UTC다.
- 대처: 먼 미래 값은 `DATETIME`(UTC 규약) 또는 날짜만이면 `DATE`. 기존 컬럼 변경은 타입 변경이라 MySQL에서 COPY 재구축이다(26번 노트).

**④ 이름 있는 시간대가 안 먹는다 (MySQL)**
- 현상: `SET time_zone = 'Asia/Seoul'`이 실패하고 앱 기동이 멈춘다. 또는 드라이버가 세션 시간대를 설정하다 실패한다.
- 보이는 형태: `ERROR 1298 (HY000): Unknown or incorrect time zone`.
- 원인: `mysql` 스키마의 시간대 테이블이 비어 있다(문서 7.1.15).
- 대처: `mysql_tzinfo_to_sql /usr/share/zoneinfo | mysql -u root -p mysql`로 적재하거나, `'+09:00'` 같은 오프셋을 쓴다. 오프셋은 서머타임 규칙이 없다는 점을 알고 쓴다.

## 핵심 문장

- "순간"과 "벽시계 글자"는 다른 값이다. 순간은 `timestamptz`/`TIMESTAMP`/`Instant`, 벽시계는 `timestamp`/`DATETIME`/`LocalDateTime`에 담는다.
- PostgreSQL `timestamptz`는 시간대를 저장하지 않는다. UTC로 바꿔 저장하고, 출력할 때 세션 TimeZone으로 바꿔 보여 준다.
- JVM·드라이버·DB 세션 세 곳이 각자 기본 시간대를 가진다. 시간대 없는 글자를 순간으로 해석·변환하는 경로에서 기준이 어긋나면 값이 에러 없이 밀린다.
- "하루"는 시간대마다 다르다. 날짜로 자르거나 묶을 때는 어느 시간대의 자정인지 명시한다.
- MySQL `TIMESTAMP`는 2038-01-19 03:14:07 UTC가 상한이다(소수 초를 쓰면 `.499999`까지).

## 관련 주제·근거

- 선행
  - [13-transactions-acid](../13-transactions-acid/2-summary.md)
  - [04-sql-joins-and-aggregation](../04-sql-joins-and-aggregation/2-summary.md) — GROUP BY와 집계
  - [distributed/04-physical-clocks-and-ntp](../../distributed/04-physical-clocks-and-ntp/2-summary.md) — 벽시계와 NTP.
- 연결
  - [09-index-design](../09-index-design/2-summary.md) — 컬럼에 함수를 씌우면 인덱스를 못 타는 이유, 표현식 인덱스
  - [26-schema-migration](../26-schema-migration/2-summary.md) — 타입 변경은 재작성(MySQL COPY)
  - [50-temporal-and-bitemporal-tables](../50-temporal-and-bitemporal-tables/2-summary.md) — 유효 시간·기록 시간
  - [domain-modeling/13-instant-vs-local-time-and-tz-rules](../../domain-modeling/13-instant-vs-local-time-and-tz-rules/2-summary.md)
  - [data-analysis/18-data-cleaning-and-quality](../../data-analysis/18-data-cleaning-and-quality/2-summary.md)
- PostgreSQL 17 문서
  - 14.1 Using EXPLAIN(인덱스가 있어도 순차 스캔을 고르는 예) <https://www.postgresql.org/docs/17/using-explain.html>
  - 소스 `src/include/datatype/timestamp.h`(REL_17_STABLE) — `POSTGRES_EPOCH_JDATE` = 2000-01-01
  - 8.5 Date/Time Types(8.5.1.3 Time Stamps, 8.5.3 Time Zones, 표 8.9 범위·해상도) <https://www.postgresql.org/docs/17/datatype-datetime.html>
  - 9.9 Date/Time Functions — 9.9.2 `date_trunc(field, source [, time_zone])`, 9.9.4 `AT TIME ZONE` <https://www.postgresql.org/docs/17/functions-datetime.html>
- MySQL 8.4 Reference Manual
  - 13.2.2 The DATE, DATETIME, and TIMESTAMP Types(범위, TIMESTAMP 변환) <https://dev.mysql.com/doc/refman/8.4/en/datetime.html>
  - 7.1.15 MySQL Server Time Zone Support(세션 `time_zone`, 시간대 테이블, `ERROR 1298`) <https://dev.mysql.com/doc/refman/8.4/en/time-zone-support.html>
- 드라이버·ORM
  - MySQL Connector/J 6.3.11 Datetime types processing(`preserveInstants`·`connectionTimeZone`·`forceConnectionTimeZoneToSession` 기본값) <https://dev.mysql.com/doc/connector-j/en/connector-j-connp-props-datetime-types-processing.html> · "Preserving Time Instants" <https://dev.mysql.com/doc/connector-j/en/connector-j-time-instants.html>
  - pgJDBC "Using Java 8 Date and Time classes" <https://jdbc.postgresql.org/documentation/query/>
  - Hibernate ORM 6.6 User Guide — `hibernate.jdbc.time_zone`, `hibernate.timezone.default_storage` <https://docs.hibernate.org/orm/6.6/userguide/html_single/Hibernate_User_Guide.html>
- RFC 3339 "Date and Time on the Internet: Timestamps" — 5.6 형식(`time-offset = "Z" / ±hh:mm`), 4.3 `-00:00` <https://www.rfc-editor.org/rfc/rfc3339>
- 로컬 재현(PostgreSQL 17.11, MySQL 8.4.10): `timestamp`/`timestamptz`와 `DATETIME`/`TIMESTAMP`의 세션 시간대별 표시, 같은 글자의 세션별 저장 차이(-09:00:00), `date_trunc` UTC vs Asia/Seoul 일별 합계, 2038 경계 삽입(1292), DATETIME 오프셋 리터럴 변환
