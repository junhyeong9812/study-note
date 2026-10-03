# domain-modeling/13-instant-vs-local-time-and-tz-rules — 정답

## 정답

### 1. UTC 저장이 맞는 곳과 틀리는 곳

- 결제 시각은 이미 일어난 순간이다. 나중에 그 지역의 규칙이 바뀌어도 그 순간은 바뀌지 않는다. UTC(`Instant`)로 저장하면 된다.
- 미래 회의의 원본은 사람의 의도인 "현지 9시"다. UTC는 **저장하는 시점의 규칙**으로 계산한 값이다.
- 회의 전에 그 나라가 DST 규칙을 바꾸면, 저장한 UTC는 더 이상 현지 9시가 아니다. 의도를 버렸으니 되살릴 수도 없다(Skeet 2019).

### 2. 세 종류 시간과 저장 선택

```text
  타임라인(UTC) ──●── Instant            "언제 일어났나"
  규칙(tz ID)   ──┤   America/Winnipeg   판에 따라 오프셋이 다르다
  벽시계        ──●── LocalDateTime      "현지 몇 시"
  달력          ──●── LocalDate          "며칠"
```

| 값 | 원본 | 파생 |
|---|---|---|
| 결제 시각 | `Instant` | 표시용 현지 시각 |
| 미래 예약 | `LocalDateTime` + `ZoneId` | `Instant` + 규칙 판 |
| 생일 | `LocalDate` | — |
| 매일 09:00 알림 | `LocalTime` + `ZoneId` | 날마다 다음 실행 순간 |

### 3. 위니펙 예약 (실험 A)

- 2026b로 계산한 UTC: `2026-12-01T15:00:00Z`(12월 오프셋 -06:00).
- 2026e 모형(-05:00)으로 그 UTC를 읽으면 현지 **10:00**.
- 현지 + tz ID로 저장했다면 재계산 UTC는 `2026-12-01T14:00:00Z`, 현지 09:00 유지. 두 UTC의 차이는 `PT1H`.
- 실험의 2026e 규칙은 `ZoneRules.of(-05:00)`로 모형화했다. 2026-11-01 이후 시각에만 맞는 단순화다.

### 4. 매월 31일 (실험 B)

| n | 연쇄 `plusMonths(1)` | 기준일 `plusMonths(n)` |
|---|---|---|
| 1 | 2026-02-28 | 2026-02-28 |
| 2 | 2026-03-28 | 2026-03-31 |
| 3 | 2026-04-28 | 2026-04-30 |
| 4 | 2026-05-28 | 2026-05-31 |
| 5 | 2026-06-28 | 2026-06-30 |

- JDK 21 `plusMonths`는 없는 날짜를 그 달 말일로 자른다(`resolvePreviousValid`). 연쇄로 더하면 한 번 잘린 28일이 굳는다.
- "오늘이 31일인가" 스케줄러: 2026년 **7회**. 2·4·6·9·11월을 건너뛴다.

### 5. 벽시계 일치형 스케줄러 (실험 G)

| 알람 | 횟수 | 이유 |
|---|---|---|
| 2026-03-08 02:30 | 0 | 02:00~02:59가 없다(공백) |
| 2026-11-01 01:30 | 2 | 01:00~01:59가 두 번 있다(-04:00, -05:00) |
| 2026-11-01 02:30 | 1 | 02:30은 중복 구간 밖이다 |

- 미국 규칙에서 "두 번 울림"은 01시대 알람에서 생긴다. 실제 cron 구현이 이 모형과 같은지는 구현마다 확인해야 한다.

### 6. 공백 시각과 거부 정책

- `LocalDateTime.parse("2026-03-08T02:30").atZone(America/New_York)` → `2026-03-08T03:30-04:00`. 예외 없이 공백 길이(1시간)만큼 앞으로 민다(`ZonedDateTime` javadoc, [java/syntax/51](../../../languages/java/syntax/51-java-time-types/2-summary.md) (3)).
- 거부하려면 `zone.getRules().getValidOffsets(ldt).isEmpty()`를 검사하거나 `ZonedDateTime.ofStrict`를 쓴다. 실험 D 출력 끝에서 `2026-03-08 02:30 유효 오프셋 = []`.

### 7. 여러 층의 tzdata

- 같은 순간을 서로 다른 판으로 해석하면 앱과 DB의 현지 시각이 1시간 다를 수 있다. 앱이 파생 UTC를 계산한 판과 DB가 `AT TIME ZONE`으로 계산한 판도 다를 수 있다.
- 판이 같아도 중복 시각은 해석이 갈린다. Java 기본은 이른 오프셋, PostgreSQL은 전이 직후 오프셋(뉴욕에서는 표준시)이다(문서 B.2, 17.11 재현: 2026-11-01 01:30 뉴욕 → `06:30:00+00`). 두 층 비교 진단에서는 중복 구간 행을 따로 다룬다.
- 실측: JDK 21.0.12 번들은 2026b, JDK 17.0.19 번들은 2026a, postgres:17(17.11) 이미지가 쓰는 OS 사본은 2026c, IANA 최신은 2026e(2026-09-29).
- PostgreSQL 17 문서 8.5.3: 미래에는 "the latest known rules ... will continue to be observed indefinitely far into the future"라고 가정한다. 즉 미래 순간은 지금 아는 규칙으로 계산된다. PostgreSQL은 자체 tz 데이터를 포함하고, `--with-system-tzdata`로 빌드하면 OS 사본을 쓴다.

### 8. RFC 9557

- `[America/Winnipeg]`: RFC 3339 타임스탬프 뒤에 붙인 시간대 ID 접미사. 오프셋만으로는 알 수 없는 "어느 지역 규칙인가"를 전한다.
- `[!...]`: critical 플래그. 받는 쪽이 이 접미사를 처리할 수 없으면 그 문자열로 행동하면 안 된다. critical이면 오프셋·시간대 불일치도 처리해야 한다(RFC 용어 MUST, 3.4절).
- JDK 21의 `ZonedDateTime.parse("2022-07-08T00:14:07+00:00[Europe/London]")` → `2022-07-08T01:14:07+01:00[Europe/London]`. **순간(오프셋)을 지키고 현지 시각을 고쳤다.** `[!Europe/London]`은 `DateTimeParseException`이었다(Extra 실험).

### 9. 생일 쿠폰이 하루 일찍

- 원인: 생일(시각이 없는 날짜)을 UTC 자정 `Instant`로 저장했다. UTC보다 늦은 지역에서는 그 순간이 전날이다.
- 실험 C: 1990-05-10 → `America/Los_Angeles`에서 1990-05-09, `Asia/Seoul`에서 1990-05-10.
- 대처: `LocalDate`(PG `date`)로 저장한다. 발송 판단은 "사용자 tz ID 기준 오늘 날짜 == 생일"로 한다.

### 10. Azure 2012

- Microsoft 사후 분석 원문: "the GA calculated the valid-to date by simply taking the current date and adding one to its year". 2012-02-29에 만든 인증서의 만료일이 2013-02-29가 됐다. 없는 날짜라 인증서 생성이 실패했다.
- `java.time`: `LocalDate.of(2012,2,29).plusYears(1)`은 2013-02-28로 자른다(JDK 21.0.12에서 실행 확인. 실험 F의 2024-02-29 → 2025-02-28과 같은 자르기 규칙). `LocalDate.of(2013,2,29)`처럼 없는 날짜를 직접 만들면 `DateTimeException: Invalid date 'February 29' as '2013' is not a leap year`.
- 교훈: 날짜 필드를 직접 조작하지 말고 달력 연산을 쓴다. 다만 "2/28로 자르는 것"이 도메인 규칙(예: 1년 만기)과 맞는지는 따로 정한다.
