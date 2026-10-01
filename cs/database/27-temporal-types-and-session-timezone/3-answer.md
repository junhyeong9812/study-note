# database/27-temporal-types-and-session-timezone — 정답

## 정답

### 1. 순간 vs 벽시계

- 순간: 타임라인 위의 한 점. 어디서 봐도 같다. UTC로 정규화해 저장할 수 있다.
- 벽시계 값: "그 지역 시계로 몇 시"라는 글자. 어느 시간대인지 정보가 없다.

| | PostgreSQL 17 | MySQL 8.4 | Java |
|---|---|---|---|
| 결제 시각(순간) | `timestamptz` | `TIMESTAMP`(2038 한계면 `DATETIME` + UTC 규약) | `Instant`·`OffsetDateTime` |
| 매일 09:00 알림(벽시계) | `time`/`timestamp` + 시간대 컬럼 | `TIME`/`DATETIME` + 시간대 컬럼 | `LocalTime`/`LocalDateTime` + `ZoneId` |

- 알림을 순간으로 저장하면, 사용자의 시간대 규칙(서머타임 등)이 바뀔 때 "09:00"이라는 뜻이 깨진다.

### 2. 세션을 바꿔 읽기

```text
                     a (timestamp)         b (timestamptz)
  UTC 세션에서 읽기   2026-10-01 00:30:00   2026-09-30 15:30:00+00
```

- a는 글자 그대로다. b는 입력 때 Asia/Seoul로 해석돼 UTC 15:30(전날)으로 저장됐고, UTC 세션에서 그대로 보인다(로컬 재현, PostgreSQL 17.11).
- `timestamptz`는 **시간대를 저장하지 않는다.** UTC로 바꿔 저장하고 원래 시간대는 버린다. 출력 때 세션 TimeZone으로 바꿔 보여 줄 뿐이다(문서 8.5.1.3).

### 3. 9시간 밀림의 흐름

```text
  JVM(Asia/Seoul)  LocalDateTime 10:00  →  글자 "2026-10-01 10:00:00" (시간대 없음)
       │
  DB 세션(UTC)      "10:00"을 UTC로 해석  →  저장: 2026-10-01 10:00 UTC
       │
  서울 기준으로 보면                        2026-10-01 19:00 KST   ← 실제(10:00 KST)보다 9시간 뒤
```

- 로컬 재현(PostgreSQL 17.11): 같은 글자를 UTC 세션과 Asia/Seoul 세션에서 넣은 두 행의 차이가 `-09:00:00`이었다.
- 고치는 법: 글자에 오프셋을 붙이거나(`OffsetDateTime`), 세 기준(JVM·드라이버·세션)을 하나로 맞춘다.

### 4. Connector/J 기본값

| 속성 | 기본값 | 뜻 |
|---|---|---|
| `preserveInstants` | true | 순간 값을 보존하려고 변환한다 |
| `connectionTimeZone` | `LOCAL` | 세션 시간대가 JVM 기본 시간대와 같다고 **가정**한다 |
| `forceConnectionTimeZoneToSession` | false | 그 시간대를 세션에 실제로 설정하지는 않는다 |

- 문서(6.3.11)는 `connectionTimeZone=LOCAL`이면 `preserveInstants`가 효과가 없다고 적는다. 출발·도착 시간대가 같다고 보기 때문이다.
- 그래서 JVM(KST)과 서버 세션(UTC)이 다르면 드라이버는 변환하지 않고 KST 글자를 보낸다. 서버는 그것을 UTC로 읽는다 → 9시간 밀림.
- 해결 예: `connectionTimeZone=UTC&forceConnectionTimeZoneToSession=true`(세션도 UTC로 맞춤), 또는 `connectionTimeZone=SERVER`(서버에 물어 변환).

### 5. 일별 합계

```text
  UTC 기준으로 보면: 09-30 14:59 / 09-30 15:30 / 09-30 23:59 / 10-01 00:00 (UTC)

  date_trunc('day', sold_at)               09-30: 600   10-01: 400
  date_trunc('day', sold_at, 'Asia/Seoul') 09-30: 100   10-01: 900
```

```sql
SELECT date_trunc('day', sold_at, 'Asia/Seoul') AT TIME ZONE 'Asia/Seoul' AS kst_day, sum(amount)
FROM sales GROUP BY 1 ORDER BY 1;
```

- 로컬 재현(PostgreSQL 17.11)에서 위 숫자가 그대로 나왔다. 00:00~08:59 KST의 200+300이 전날로 넘어갔던 것이다.
- 범위 조회는 `sold_at >= '2026-10-01 00:00+09' AND sold_at < '2026-10-02 00:00+09'`처럼 경계에 오프셋을 넣은 반열린 구간으로 쓴다. 인덱스 범위 스캔도 쓸 수 있다(실제 선택은 비용 판단).

### 6. TIMESTAMP 범위

- 범위: `'1970-01-01 00:00:01'` UTC ~ `'2038-01-19 03:14:07'` UTC(문서 13.2.2). 소수 초 정밀도를 쓰면 상한은 `03:14:07.499999`다.
- 상한: 1970-01-01 00:00:00 UTC + (2^31 − 1)초 = 2038-01-19 03:14:07 UTC. 부호 있는 32비트 초의 끝이다.
- 세션 `+09:00`이면 UTC 03:14:07 = KST 12:14:07이다. `'2038-01-19 12:14:07'`까지 들어가고, `'2038-01-19 12:14:08'`은 `ERROR 1292`로 거절됐다(로컬 재현, MySQL 8.4.10, strict 모드). 상한은 UTC 기준이다.

### 7. pgJDBC와 java.time

- pgJDBC 문서는 `ZonedDateTime`, `Instant`, `OffsetTime`을 **지원하지 않는다**고 적는다. `setObject(i, instant)`에 기대지 않는다.
- `timestamptz` ↔ `OffsetDateTime`, `timestamp` ↔ `LocalDateTime`, `date` ↔ `LocalDate`를 쓴다.
- 읽어 온 `OffsetDateTime`은 항상 오프셋 0(UTC)이다. 백엔드가 UTC로 저장하기 때문이다(문서).

```java
ps.setObject(1, OffsetDateTime.ofInstant(Instant.now(), ZoneOffset.UTC));
OffsetDateTime paidAt = rs.getObject("paid_at", OffsetDateTime.class);   // 오프셋 +00:00
```

### 8. 배포 후 9시간 밀림 진단

1. 범위 특정: 밀린 행이 언제부터인지 찾는다(배포 시각과 맞는지). 옛 행은 멀쩡한지 본다.
2. JVM: 새 이미지의 `ZoneId.systemDefault()`, `-Duser.timezone`, 컨테이너 `TZ`.
3. 드라이버: 연결 URL의 `connectionTimeZone`/`serverTimezone`/`forceConnectionTimeZoneToSession`, Hibernate `hibernate.jdbc.time_zone`.
4. DB 세션: PG `SHOW TimeZone`(역할·DB 단위 `ALTER ROLE ... SET` 포함), MySQL `@@session.time_zone`.
5. 코드: `LocalDateTime`으로 순간을 다루는 곳이 있는지.

- 보정: 원인을 고쳐 새 밀림을 먼저 멈춘다. 그다음 **특정한 기간의 행만** `paid_at - interval '9 hours'`처럼 보정한다. 되돌릴 수 없는 데이터 변경이므로 백업, 대상 행 수 확인, 표본 대조 뒤에 한다.

### 9. ERROR 1298

- 원인: 이름 있는 시간대는 `mysql` 스키마의 시간대 테이블이 채워져 있어야 쓸 수 있다. 비어 있으면 1298이 난다(문서 7.1.15).
- 대처 1: `mysql_tzinfo_to_sql /usr/share/zoneinfo | mysql -u root -p mysql`로 적재한다.
- 대처 2: 이름 대신 `'+09:00'` 같은 오프셋을 쓴다(드라이버 `connectionTimeZone`도 오프셋으로).
- 한계: 오프셋은 고정 값이다. 서머타임이 있는 지역(예: America/New_York)은 계절마다 오프셋이 바뀌므로 오프셋 하나로는 틀린다. 한국은 현재 서머타임이 없어 `+09:00`이 실무상 동작한다. 다만 과거 날짜는 다르다. IANA 데이터로 변환하면 `1988-07-01 12:00 Asia/Seoul`은 UTC 02:00(= +10:00, 당시 서머타임)이 나왔다(로컬 재현, PostgreSQL 17.11 `timestamptz`·MySQL 8.4.10 `CONVERT_TZ` 모두). 오프셋 `+09:00`으로는 이 차이를 표현할 수 없다.
