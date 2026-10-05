# domain-modeling/13-instant-vs-local-time-and-tz-rules — 순간·현지 시각·날짜, 그리고 바뀌는 시간대 규칙 — 정리 (힌트)

## 해결하는 문제

"시각은 UTC로 저장하라"는 조언은 **이미 일어난 사건**에는 맞다. **아직 오지 않은 현지 일정**에는 틀릴 수 있다.

```text
  2026-09: 위니펙 고객이 "12월 1일 오전 9시" 예약
           그때 JDK에 들어 있던 규칙(tzdb 2026b): 12월은 -06:00  →  UTC 15:00 으로 저장

  2026-09-29: tzdb 2026e 발표 — 매니토바가 -05:00 상시로 바뀐다
           새 규칙으로 UTC 15:00 을 다시 읽으면  →  현지 10:00   ← 고객은 9시에 왔다
```

- 순간을 저장하는 순간, "현지 9시"라는 **의도**는 버려진다. 규칙이 바뀌면 되살릴 수 없다.
  - *순간(instant)*: 타임라인 위의 한 점. 세계 어디서 봐도 같다. Java `Instant`.
  - *현지 시각(local date-time)*: 달력과 벽시계에 적힌 글자. 어느 지역인지 정보가 없다. Java `LocalDateTime`.
  - *시간대 ID(tz ID)*: `America/Winnipeg`처럼 지역을 가리키는 이름. 그 지역의 과거·미래 오프셋 규칙 전체를 뜻한다. `-06:00` 같은 고정 오프셋과 다르다.

쉬운 예: 친구와 "다음 달 첫 토요일 오후 3시, 광화문에서"라고 약속했다.
- 그 사이에 서울 시간이 1시간 당겨지는 법이 생겨도, 둘 다 **서울 시계로** 3시에 나온다.
- 약속을 "UTC 06:00"으로 적어 둔 사람만 엉뚱한 시각에 나온다.

똑같은 구조다.\
미래 일정은 "현지 시각 + tz ID"가 원본이고, UTC는 **그때의 규칙으로 계산한 파생값**이다(Jon Skeet, "Storing UTC is not a silver bullet", 2019).

실무 예:
- 위의 매니토바 변경은 실제 공지다. IANA tz database 2026e(2026-09-29) NEWS: "Manitoba moves to permanent -05 on 2026-10-31". 같은 NEWS는 법적 변경일이 10-31이지만 데이터에서는 "temporarily model the change to occur on 2026-11-01 at 02:00"이라고 적는다(NEWS가 밝힌 이유: Unicode CLDR의 캐나다 시간 표기 버그를 피하려는 임시 처리 — 2026b 항목 참고).
- 파라과이도 2024-10-06 이후 시계를 바꾸지 않기로 했고, tzdb 2025a(2025-01-15)가 이를 반영했다. 영향은 "timestamps starting 2025-03-22"부터다(같은 NEWS).
- 그 밖의 흔한 사고: 매월 31일 정기 결제가 2월에 빠진다. DST 전환일의 02:30 알람이 안 울리거나, 01:30 알람이 두 번 울린다. 생일이 해외 사용자에게 하루 전으로 보인다. 2월 29일에 서비스가 멈춘다(Azure 2012).

## 동작·원리

### 1. 시간 값은 세 종류다 — 무엇을 저장할지 고르는 표

```text
  타임라인(UTC) ────●──────────────────────────────▶
                    │ Instant  2026-12-01T15:00:00Z           "언제 일어났나"
                    │
   규칙(tz ID) ─────┤ America/Winnipeg, tzdb 판에 따라 -06:00 또는 -05:00
                    │
  벽시계 ───────────● LocalDateTime 2026-12-01T09:00            "현지 몇 시인가"
  달력 ─────────────● LocalDate     2026-12-01                  "며칠인가"(시각 없음)
```

| 도메인 값(예시) | 원본으로 저장할 것 | 파생값 | 이유 |
|---|---|---|---|
| 결제·로그·이벤트 발생 시각 | `Instant` | 표시용 현지 시각 | 이미 일어났다. 규칙이 바뀌어도 그 순간은 그대로다 |
| 미래 회의·예약·알람 | `LocalDateTime` + `ZoneId` | `Instant`(규칙 판과 함께) | 사람의 의도는 "현지 9시"다 |
| 생일·만기일·영업일 | `LocalDate`(필요하면 + `ZoneId`) | — | 시각이 없는 날짜다 |
| 매일 09:00 알림 | `LocalTime` + `ZoneId` | 날마다 계산 | 날마다 오프셋이 다를 수 있다 |

- Java 타입 하나하나의 문법·변환은 [languages/java/syntax/51-java-time-types](../../../languages/java/syntax/51-java-time-types/2-summary.md)에 있다. DB 쪽 `timestamp`/`timestamptz`와 세션 시간대는 [database/27-temporal-types-and-session-timezone](../../database/27-temporal-types-and-session-timezone/2-summary.md)에 있다. 이 노트는 **도메인에서 무엇을 원본으로 둘지**만 다룬다.

### 2. 미래 일정: 현지 시각이 원본, UTC는 재계산한다

```text
  저장 방식 1: UTC 만                     저장 방식 2: 현지 + tz ID (+ 파생 UTC, 규칙 판)
  ┌────────────────────────┐               ┌────────────────────────────────────────┐
  │ start_utc 15:00Z       │               │ local_start  2026-12-01 09:00          │
  └────────────────────────┘               │ tz_id        America/Winnipeg          │
       규칙 갱신 후 표시                    │ start_utc    15:00Z (tzdb 2026b 로 계산) │
       → 현지 10:00 (틀림)                  │ tzdb_version 2026b                     │
                                           └────────────────────────────────────────┘
                                                규칙 갱신 후 재계산
                                                → start_utc 14:00Z, 현지 09:00 유지
```

- Skeet의 권고(같은 글): 현지 시각과 tz ID를 원본으로 두고, UTC는 파생 필드("UTC start: derived field for convenience")로 둔다. 규칙 판 필드도 둔다 — Skeet는 이것을 "for optimization purposes"라고 적는다(어느 판으로 계산했는지 알면 판이 바뀐 행만 다시 계산하면 된다). 규칙이 바뀌면 재계산 코드의 주석대로 "Preserve the local time, but with the new time zone rules" UTC를 다시 계산한다.
- 반대 상황도 있다. 여러 지역 참가자가 있는 온라인 회의는 "누구의 현지 시각이 기준인가"를 먼저 정해야 한다. 주최자 지역을 기준으로 두면, 다른 지역 참가자의 현지 시각이 규칙 변경으로 바뀌는 것은 정상이다.

#### 실험 A: 규칙 갱신 전후의 위니펙 예약

- 환경: JDK 21.0.12에 번들된 tzdb는 **2026b**다(매니토바 변경 전).
- 새 규칙(2026e)은 `ZoneRules.of(ZoneOffset.ofHours(-5))`로 모형화했다. 이 모형은 2026-11-01 이후 시각에만 맞는 단순화다.

```java
LocalDateTime appt = LocalDateTime.parse("2026-12-01T09:00");
Instant storedUtc = appt.atZone(ZoneId.of("America/Winnipeg")).toInstant();   // 방식 1: 옛 규칙으로 UTC 저장
ZoneRules after2026e = ZoneRules.of(ZoneOffset.ofHours(-5));                  // 2026e 모형(2026-11-01 이후)
LocalDateTime shownFromUtc = LocalDateTime.ofInstant(storedUtc, after2026e.getOffset(storedUtc));
Instant recomputed = appt.toInstant(after2026e.getOffset(appt));              // 방식 2: 현지+tz ID 에서 재계산
```

(실험, JDK 21.0.12 temurin, tzdb 2026b, 2026-10-03)

```text
java 21.0.12 / tzdb 2026b
== A. 미래 예약: Winnipeg 2026-12-01 09:00 (현지)
  bundled next transition after 2026-06-01: Transition[Overlap at 2026-11-01T02:00-05:00 to -06:00]
  저장(옛 규칙으로 계산한 UTC) = 2026-12-01T15:00:00Z  offset -06:00
  방식1(UTC 저장) 새 규칙으로 표시 = 2026-12-01T10:00  <- 현지 시각이 바뀜
  방식2(현지+tzID 저장) 새 규칙으로 재계산 UTC = 2026-12-01T14:00:00Z  현지 2026-12-01T09:00
  두 UTC 차이 = PT1H
```

- 관찰: 번들 규칙(2026b)은 2026-11-01에 -05:00 → -06:00으로 되돌리는 전이를 아직 갖고 있다. 이 JDK로 계산해 저장한 UTC는 2026e 이후 1시간 틀린다.
- 해석: 방식 2만 고객의 의도(현지 9시)를 지킨다. 대신 tzdata가 갱신될 때 **재계산 작업**이 필요하다(적용 §3).

### 3. tzdata는 여러 층에 따로 들어 있다

```text
  IANA tz database (2026e, 2026-09-29)
        │ 각자 다른 속도로 받아 간다
        ├─▶ JDK 번들(tzdb.dat)    JDK 21.0.12 → 2026b, JDK 17.0.19 → 2026a  (실측)
        ├─▶ OS /usr/share/zoneinfo
        ├─▶ DB 서버(PostgreSQL 은 자체 사본 또는 OS 사본 — 빌드 옵션에 따라)
        │     postgres:17 이미지(17.11) → OS 사본, tzdata.zi 2026c  (실측)
        └─▶ 브라우저·모바일 OS
```

- 같은 순간을 서로 다른 층이 다른 판으로 해석하면, 앱과 DB의 현지 시각 표시가 1시간 다를 수 있다.
- JDK의 판은 코드로 확인한다: `ZoneRulesProvider.getVersions("UTC").lastEntry().getKey()`.
- JDK에 들어 있는 규칙이 특정 지역에서 판마다 달라지는 실측(JDK 17.0.13·21.0.5의 2024a vs 25.0.1의 2025b, `America/Asuncion`)은 [java/syntax/51](../../../languages/java/syntax/51-java-time-types/2-summary.md) 「tzdb 판이 갈렸다」에 있다. 같은 메이저 판이라도 패치 판마다 tzdb가 다르다 — 이 노트가 쓴 JDK 21.0.12(2026b)·17.0.19(2026a)에는 파라과이 변경(2025a)이 이미 들어 있어 `America/Asuncion` 2026-07-15 09:00이 `-03:00`이었다(`Tz.java`).
- PostgreSQL 17 문서 8.5.3은 IANA(Olson) 데이터를 쓴다고 적고, 미래에 대해서는 "the latest known rules for a given time zone will continue to be observed indefinitely far into the future"라고 가정한다. 미래 순간은 **지금 아는 규칙**으로 계산된다는 뜻이다.
- PostgreSQL은 소스에 자체 tz 데이터베이스를 포함한다. 빌드 옵션 `--with-system-tzdata=DIRECTORY`를 쓰면 OS 사본을 쓴다(17판 설치 문서 configure 옵션). 이 옵션의 장점으로 문서는 "DST 규칙이 바뀔 때마다 PostgreSQL 패키지를 올리지 않아도 된다"를 든다. 운영 중인 패키지가 어느 쪽으로 빌드됐는지는 배포판마다 확인해야 한다. 예: 이 노트에서 쓴 `postgres:17` 이미지(17.11)는 `pg_config --configure`에 `--with-system-tzdata=/usr/share/zoneinfo`가 있었고, 그 OS 사본(`tzdata.zi`)은 2026c였다 — 같은 날 JDK 21.0.12(2026b)와 판이 달랐다.

### 4. DST 공백·중복 — 도메인이 정책을 골라야 한다

```text
  America/New_York 2026-03-08 (공백)        2026-11-01 (중복)
  01:59 -05:00 │ 03:00 -04:00               01:00~01:59 -04:00  →  01:00~01:59 -05:00
         02:00~02:59 없음                          같은 글자가 두 순간
```

- `java.time`의 기본 동작(JDK 21 `ZonedDateTime` javadoc): 공백 안의 시각은 공백 길이만큼 **앞으로 민다**. 중복이면 **앞쪽(이른) 오프셋**을 고른다(새로 만들 때. 기존 `ZonedDateTime`을 조정할 때는 직전 오프셋이 유효하면 그것을 유지한다). 예외가 아니다. 실행 결과는 [java/syntax/51](../../../languages/java/syntax/51-java-time-types/2-summary.md) (3)(4).
- 도메인 질문은 "그 기본값이 우리 규칙과 같은가"다.

| 상황(예시) | 고를 수 있는 정책 |
|---|---|
| 사용자가 공백 시각(02:30)으로 예약 | 거부하고 다시 받기(`getValidOffsets().isEmpty()`) / 뒤로 밀기(03:30) |
| 매일 02:30 배치 | 그날은 03:30에 1회 / 그날은 건너뜀 |
| 중복 시각(01:30) 알람 | 첫 번째만 / 두 번째만 / 두 번 다 |
| 중복 구간의 로그 | 오프셋을 함께 저장해야 복원 가능 |

#### 실험 G: 벽시계 일치형 스케줄러

- "매 분 현지 시각을 보고 HH:mm이 같으면 울린다"는 단순한 스케줄러를 시뮬레이션했다(cron류의 동작을 단순화한 모형).

```java
for (Instant i = from; i.isBefore(to); i = i.plus(Duration.ofMinutes(1))) {
  ZonedDateTime z = i.atZone(ny);
  if (z.toLocalDate().equals(day) && z.toLocalTime().equals(t)) fired++;
}
```

(실험, JDK 21.0.12 temurin, tzdb 2026b, 2026-10-03)

```text
== G. 벽시계 일치형 스케줄러(매 분 현지 시각을 보고 HH:mm이 같으면 울림) 시뮬레이션
  2026-03-08 02:30 울린 횟수 = 0 []  (그날 길이 PT23H)
  2026-11-01 01:30 울린 횟수 = 2 [2026-11-01T01:30-04:00, 2026-11-01T01:30-05:00]  (그날 길이 PT25H)
  2026-11-01 02:30 울린 횟수 = 1 [2026-11-01T02:30-05:00]  (그날 길이 PT25H)
```

- 관찰: 미국 규칙에서 "두 번 울림"은 02:30이 아니라 **01:00~01:59** 구간의 알람에서 생긴다. 02:30이 걸리는 날은 봄 전환일(0회)이다.
- 실제 cron 구현이 이 모형과 같은지는 구현마다 다르다(예: 일부 cron은 DST 전환을 특별 처리한다) [?]. 쓰는 스케줄러의 문서를 확인한다.

### 5. 반복 일정·윤일 — 달력 연산은 "자르기"를 한다

```text
  기준일 1/31 에서 매달            연쇄로 매달(전 결과에 +1개월)
  1/31 → 2/28 → 3/31 → 4/30       1/31 → 2/28 → 3/28 → 4/28   ← 28일로 굳는다
```

- JDK 21 `LocalDate.plusMonths`는 결과 달에 그 날짜가 없으면 **그 달의 마지막 유효 날짜**로 자른다(소스 `resolvePreviousValid`: 2월은 28 또는 29, 4·6·9·11월은 30).
- 그래서 "기준일 + n개월"로 매번 기준에서 계산해야 31일이 돌아온다. 전 결과에 1개월씩 더하면 한 번 잘린 날짜가 그대로 굳는다.

#### 실험 B·C·D·E·F

(실험, JDK 21.0.12 temurin, tzdb 2026b, 2026-10-03)

```text
== B. 매월 31일 결제
  1개월: 연쇄 plusMonths(1) = 2026-02-28   기준일 plusMonths(1) = 2026-02-28
  2개월: 연쇄 plusMonths(1) = 2026-03-28   기준일 plusMonths(2) = 2026-03-31
  3개월: 연쇄 plusMonths(1) = 2026-04-28   기준일 plusMonths(3) = 2026-04-30
  4개월: 연쇄 plusMonths(1) = 2026-05-28   기준일 plusMonths(4) = 2026-05-31
  5개월: 연쇄 plusMonths(1) = 2026-06-28   기준일 plusMonths(5) = 2026-06-30
  '오늘이 31일이면 결제' 스케줄러: 2026년 실행 7회, 건너뛴 달 [FEB, APR, JUN, SEP, NOV]
== C. 생일(LocalDate)을 UTC 자정 Instant로 저장
  Asia/Seoul 에서 표시 = 1990-05-10
  America/Los_Angeles 에서 표시 = 1990-05-09
== D. 매일 02:30 알람 (America/New_York) 2026-03-07~09, 2026-10-31~11-02
  2026-03-07  현지규칙 atZone = 2026-03-07T02:30-05:00[America/New_York]   | 첫 알람+24h×0 = 2026-03-07T02:30-05:00[America/New_York]
  2026-03-08  현지규칙 atZone = 2026-03-08T03:30-04:00[America/New_York]   | 첫 알람+24h×1 = 2026-03-08T03:30-04:00[America/New_York]
  2026-03-09  현지규칙 atZone = 2026-03-09T02:30-04:00[America/New_York]   | 첫 알람+24h×2 = 2026-03-09T03:30-04:00[America/New_York]
  2026-10-31  현지규칙 atZone = 2026-10-31T02:30-04:00[America/New_York]   | 첫 알람+24h×0 = 2026-10-31T02:30-04:00[America/New_York]
  2026-11-01  현지규칙 atZone = 2026-11-01T02:30-05:00[America/New_York]   | 첫 알람+24h×1 = 2026-11-01T01:30-05:00[America/New_York]
  2026-11-02  현지규칙 atZone = 2026-11-02T02:30-05:00[America/New_York]   | 첫 알람+24h×2 = 2026-11-02T01:30-05:00[America/New_York]
== E. Period vs Duration (2026-03-07 12:00 New_York)
  plus(Period.ofDays(1))   = 2026-03-08T12:00-04:00[America/New_York]
  plus(Duration.ofHours(24)) = 2026-03-08T13:00-04:00[America/New_York]
  실제 흐른 시간(Period 쪽) = PT23H
== F. 2월 29일
  2024-02-29.plusYears(1) = 2025-02-28
  LocalDate.of(2013,2,29) -> Invalid date 'February 29' as '2013' is not a leap year
  2012-02-29 + 1년(연도 필드만 +1) 유효? false
  Year 2008 길이 = 366일, 2008-12-31 dayOfYear = 366
```

- B: "오늘이 31일인가"로 고르는 스케줄러는 1년에 다섯 달을 건너뛴다. "그 달에 31일이 없으면 말일"이라는 규칙을 도메인이 정하고 코드로 옮겨야 한다.
- D: 날마다 "현지 날짜 + 02:30"을 다시 계산하면 공백 날만 03:30이고 다음 날 02:30으로 돌아온다. 첫 알람 순간에 24시간씩 더하면 전환 뒤로 계속 1시간 밀린다(03-09 03:30, 11-02 01:30).
- C: 날짜를 UTC 자정 순간으로 바꾸면, UTC보다 늦은(서쪽) 지역에서 전날이 된다. 날짜는 `LocalDate`(PG `date`)로 둔다.
- E: 달력 기준 하루(`Period`)는 그날 23시간만 흘렀다. 근무 시간·요금 계산은 어느 쪽이 맞는지 정해야 한다. API 세부는 [java/syntax/52](../../../languages/java/syntax/52-duration-period-formatter/2-summary.md).
- F: `java.time`은 윤일에서 1년 뒤를 2/28로 자르고, 없는 날짜를 만들면 예외를 던진다. 연도 필드만 +1 하는 직접 계산은 2013-02-29라는 없는 날짜를 만든다 — Azure 2012 사고의 계산이 이 모양이었다(장애 §5).

### 6. 직렬화 — RFC 9557은 오프셋 뒤에 tz ID를 붙인다

```text
  RFC 3339:  2026-12-01T09:00:00-06:00
  RFC 9557:  2026-12-01T09:00:00-06:00[America/Winnipeg]
                                   └ 오프셋      └ 시간대 ID(괄호 안 접미사)
```

- RFC 9557(2024-04, Standards Track)은 RFC 3339 타임스탬프 뒤에 `[...]` 접미사를 붙이는 형식(IXDTF)을 정의한다. `[!...]`의 `!`는 "이 접미사를 처리 못 하면 이 문자열을 쓰지 말라"는 critical 표시다.
- 오프셋과 시간대가 맞지 않을 때(예: `2022-07-08T00:14:07+00:00[Europe/London]` — 7월 런던은 +01:00) critical이면 받는 쪽이 불일치를 처리해야 하고(RFC 용어 MUST), 아니면 처리해도 된다(MAY, 3.4절).
- 같은 RFC는 RFC 3339의 `Z` 해석도 고쳤다. `Z`는 "UTC 시각은 알지만 현지 오프셋은 모른다"는 뜻이다.

(실험, JDK 21.0.12 temurin, 2026-10-03 — `ZonedDateTime.parse`)

```text
  2022-07-08T00:14:07+01:00[Europe/London] -> 2022-07-08T00:14:07+01:00[Europe/London]  instant 2022-07-07T23:14:07Z
  2022-07-08T00:14:07+00:00[Europe/London] -> 2022-07-08T01:14:07+01:00[Europe/London]  instant 2022-07-08T00:14:07Z
  [!Europe/London] -> DateTimeParseException: Text '2022-07-08T00:14:07+00:00[!Europe/London]' could not be parsed, unparsed text found at index 25
```

- 관찰: JDK 21의 기본 파서는 오프셋이 시간대와 안 맞으면 **순간(오프셋)을 지키고 현지 시각을 고친다**(00:14 → 01:14). 미래 일정에서 원하는 것은 대개 반대(현지 시각 유지)다.
- JDK 21 파서는 critical 표시 `!`를 읽지 못한다. RFC 9557 문자열을 주고받으려면 상대 라이브러리의 지원 범위를 확인한다.

## 쓰이는 자료구조·알고리즘

- **tz 전이 테이블 + 이진 탐색**: 지역 규칙은 "이 순간부터 오프셋이 X"인 전이의 정렬된 배열과, 마지막 저장 전이 뒤에 쓰는 반복 규칙(`ZoneOffsetTransitionRule`)으로 이뤄진다. JDK 21 `ZoneRules.getOffset(Instant)`·`getOffsetInfo(LocalDateTime)`는 마지막 저장 전이 **이전** 시각이면 `Arrays.binarySearch(savingsInstantTransitions, …)`·`Arrays.binarySearch(savingsLocalTransitions, …)`로 찾는다. **이후** 시각이면 `findTransitionArray(year)`로 그해 전이를 만들어(캐시) 차례로 비교한다(openjdk/jdk21u `ZoneRules.java`, `lastRules` 분기).
  - 저장 배열은 생각보다 일찍 끝난다(실측, JDK 21.0.12/tzdb 2026b `getTransitions()` 마지막 원소): America/New_York·America/Winnipeg 2008-11-02, Europe/London 1997-10-26(셋 다 반복 규칙 2개). 그래서 이 노트의 2026년 실험은 반복 규칙 경로를 탄다. Asia/Seoul처럼 반복 규칙이 없는 지역은 늘 이진 탐색 경로다. → [algorithm/06-binary-search](../../algorithm/06-binary-search/2-summary.md)
- **반열린 구간 `[시작, 끝)` 연산**: "현지 날짜 D"는 순간 구간 `[D.atStartOfDay(zone), (D+1).atStartOfDay(zone))`다. 보통은 D 00:00 현지지만, 자정이 공백인 날은 그날 첫 유효 시각이다(javadoc — 예: America/Santiago 2026-09-06은 00:00이 없어 01:00-03:00부터). 길이는 대개 23·24·25시간이다. 30분 DST(Australia/Lord_Howe 2026-04-05 = 24h30m, 2026-10-04 = 23h30m)나 날짜 건너뛰기(Pacific/Apia 2011-12-30 없음)는 또 다르다(실측, JDK 21.0.12/tzdb 2026b). 일별 집계는 이 구간으로 자른다. → [data-structure/30-interval-tree](../../data-structure/30-interval-tree/2-summary.md)
- **달력 산술(자르기 규칙)**: `plusMonths`·`plusYears`는 결과가 없는 날짜면 말일로 자른다. 반복 일정은 "기준일 + n·주기"로 계산해 누적 오차를 피한다.

## 적용 — 풀어나가는 법

### 1. 쉬운 예 — 값마다 원본을 고른다

```java
// 이미 일어난 사건: 순간
public record PaymentCaptured(String paymentId, Instant capturedAt) {}

// 미래 일정: 현지 시각 + tz ID 가 원본. UTC 는 파생.
public record Appointment(LocalDateTime localStart, ZoneId zone) {
  public Instant startInstant(ZoneRules rules) {           // 규칙을 주입받아 계산 — 판 교체를 테스트할 수 있다
    List<ZoneOffset> valid = rules.getValidOffsets(localStart);
    if (valid.isEmpty()) throw new IllegalStateException("존재하지 않는 현지 시각: " + localStart); // 공백 정책 = 거부
    return localStart.toInstant(valid.get(0));               // 중복 정책 = 이른 오프셋
  }
}

// 생일: 날짜
public record Customer(String id, LocalDate birthday) {}
```

- `now()`는 `Clock`을 주입받아 부른다. 테스트에서 DST 전환일로 시계를 고정할 수 있다 — [java/syntax/51](../../../languages/java/syntax/51-java-time-types/2-summary.md) (7).

### 2. 실무 예 — 미래 일정 테이블과 재계산 작업

```sql
-- PostgreSQL 17 (예시 스키마)
CREATE TABLE appointment (
  id            bigint PRIMARY KEY,
  local_start   timestamp   NOT NULL,   -- 현지 벽시계(원본)
  tz_id         text        NOT NULL,   -- 'America/Winnipeg' (원본)
  start_utc     timestamptz NOT NULL,   -- 파생: 알림·정렬용
  tzdb_version  text        NOT NULL    -- 파생값을 계산한 규칙 판
);
```

- tzdata를 올린 배포 뒤에 재계산 배치를 돈다.
  1. `tzdb_version <> 새 판`이고 아직 오지 않은 일정을 고른다.
  2. 새 규칙으로 `local_start` + `tz_id` → `start_utc`를 다시 계산한다.
  3. 값이 바뀐 행 수를 세고, 바뀐 일정의 알림 큐도 다시 만든다.
- 진단: 앱이 파생값을 계산한 판과 DB가 표시하는 판이 다를 수 있다. 같은 행을 두 층에서 계산해 비교한다.
- 주의: 판이 같아도 **중복 시각의 해석**이 다르다. 위 앱 코드는 이른 오프셋(DST)을 고르고, PostgreSQL은 모호한 시각에 전이 직후의 오프셋을 붙인다 — 뉴욕처럼 대부분의 시간대에서는 표준시 해석이다(PostgreSQL 17 문서 B.2: "assigned the UTC offset that prevailed just after the transition"). 로컬 재현(PostgreSQL 17.11): `timestamp '2026-11-01 01:30' AT TIME ZONE 'America/New_York'` = `2026-11-01 06:30:00+00`(-05:00), Java 이른 오프셋이면 05:30Z(-04:00). 그래서 아래 쿼리는 중복 구간 행을 빼거나, 앱이 고른 오프셋을 함께 저장해 비교해야 한다.

```sql
-- DB 의 tz 규칙으로 다시 계산한 값과 저장된 파생값이 다른 미래 일정
SELECT id, local_start, tz_id, start_utc, (local_start AT TIME ZONE tz_id) AS db_recalc
FROM appointment
WHERE start_utc > now() AND start_utc <> (local_start AT TIME ZONE tz_id);
```

- `timestamp AT TIME ZONE zone`은 그 지역의 현지 시각으로 보고 `timestamptz`를 돌려준다(PostgreSQL 17 9.9.4). 모호·무효 시각 처리는 부록 B.2 <https://www.postgresql.org/docs/17/datetime-invalid-input.html>.

### 3. 반복 일정 규칙을 도메인 언어로 적는다

- "매월 31일" → "매월 기준일(31). 그 달에 없으면 말일" 같은 문장으로 정하고, `기준일.plusMonths(n)`으로 구현한다.
- "매일 02:30" → "공백 날은 03:30에 1회, 중복 날은 첫 번째 1회"처럼 DST 정책을 적는다.
- 테스트 날짜: 2월 28·29일, 31일이 없는 달, DST 시작·끝 날, 연말(12-31, 윤년의 366일째).

## 장애 시나리오와 대처

### 1. 미래 예약을 UTC로 저장했는데 그 나라가 DST 규칙을 바꿨다 → 1시간 어긋남 (⚠)
- 현상: 특정 지역 고객의 예약 알림·화면 시각이 1시간 다르다. 고객은 원래 시각에 온다.
- 보이는 형태: 에러 없음. tzdata 갱신(JDK·OS 업데이트) 뒤 그 지역 예약에서만 생긴다. 실험 A에서 위니펙 09:00 → 10:00.
- 원인: 의도(현지 시각)를 버리고 옛 규칙으로 계산한 순간만 남겼다.
- 대처: 현지 시각 + tz ID를 원본으로 저장하고, 규칙 판을 기록하고, tzdata 갱신 때 재계산한다. 이미 UTC만 남은 데이터는 "그때 쓰인 판"을 추정해 역산하고, 영향 받은 지역·기간을 IANA NEWS로 특정한다.

### 2. "매월 31일" 정기 결제가 2월에 누락 (⚠)
- 현상: 31일 가입자의 2월(그리고 4·6·9·11월) 결제가 안 된다. 또는 3월부터 28일에 결제된다.
- 보이는 형태: 월별 결제 건수가 달마다 출렁인다. 실험 B에서 "오늘이 31일인가" 방식은 2026년에 7회만 실행됐다.
- 원인: 날짜 일치로 고르는 스케줄러, 또는 전 결제일에 1개월씩 더하는 연쇄 계산.
- 대처: 기준일을 저장하고 `기준일.plusMonths(n)`으로 다음 결제일을 계산한다. "없는 날짜면 말일"을 약관·코드·테스트에 같은 문장으로 둔다.

### 3. DST 전환일 알람이 없거나 두 번 울림 (⚠)
- 현상: 미국 지역에서 3월 둘째 일요일 02:30 알람이 안 울리거나 03:30에 울린다. 11월 첫째 일요일 01:30 알람이 두 번 울린다.
- 보이는 형태: 그날만 알림 발송 로그가 0건 또는 2건. 실험 G.
- 원인: 벽시계 일치로 실행하거나, 첫 실행 순간에 24시간씩 더했다(이 방식은 전환 뒤 매일 1시간 밀린다 — 실험 D 출력 `첫 알람+24h×2 = 2026-03-09T03:30`).
- 대처: 날마다 "현지 날짜 + 현지 시각 + tz ID"로 다음 실행 순간을 새로 계산하고, 공백·중복 정책을 명시한다. 실행 기록에 "이 날짜 몫은 실행했다"를 남겨 중복 실행을 막는다.

### 4. 생일을 자정 UTC 타임스탬프로 저장 → 해외 사용자에게 하루 전 (⚠)
- 현상: 미국 서부 사용자에게 생일이 하루 전으로 보인다. 생일 쿠폰이 하루 일찍 나간다.
- 보이는 형태: 실험 C — 1990-05-10이 `America/Los_Angeles`에서 1990-05-09.
- 원인: 시각이 없는 날짜를 순간으로 바꿨다.
- 대처: `LocalDate` / PG `date`로 저장한다. "그 사용자의 현지 날짜로 생일인가"가 필요하면 사용자 tz ID로 오늘 날짜를 구해 비교한다.

### 5. 2월 29일 처리 버그 (⚠ — Zune 2008, Azure 2012)
- Zune 30(2008-12-31): 전원 관리 칩 드라이버의 날짜 계산 루프가 윤년의 366번째 날에 끝나지 않아 기기가 멈췄다. 공식 안내는 배터리를 다 소진한 뒤 2009-01-01 정오(GMT) 이후 재충전하는 것이었다(위키백과 "Zune 30" 요약 — 1차 출처 [?]).
- Azure(2012-02-29): Microsoft 사후 분석 원문 "the GA calculated the valid-to date by simply taking the current date and adding one to its year". 2013-02-29라는 없는 날짜가 만들어져 인증서 생성이 실패했다. 시작은 원문 표기로 "4:00PM PST, February 28th (00:00 UST February 29th)".
- 보이는 형태: 윤일·연말에만 나는 예외 또는 무한 루프.
- 대처: 날짜 산술은 직접 하지 않고 달력 라이브러리(`plusYears` 등)를 쓴다. 윤일·366일째를 고정 테스트 날짜로 둔다(`Clock` 주입).

## 핵심 문장

- 이미 일어난 사건은 순간(`Instant`)으로, 미래의 현지 일정은 "현지 시각 + tz ID"로, 날짜는 `LocalDate`로 저장한다.
- 미래 일정의 UTC는 그때의 tz 규칙으로 계산한 파생값이다. 규칙 판을 기록하고 tzdata 갱신 때 다시 계산한다.
- tz 규칙은 나라의 결정에 따라 바뀌는 데이터다(2025a 파라과이, 2026e 매니토바). JDK·OS·DB가 각자 다른 판을 들고 있을 수 있다.
- DST 공백·중복에서 `java.time`은 예외 대신 앞으로 밀거나 이른 오프셋을 고른다. 그 기본값이 도메인 정책과 같은지 확인한다.
- 달력 기준 기간(`Period`)과 고정 길이(`Duration`)는 전이가 낀 날 다르다. 반복 일정은 "기준일 + n·주기"로 계산한다.

## 관련 주제·근거

- 선행
  - [12-time-money-and-units](../12-time-money-and-units/2-summary.md) — 개관
  - [distributed/04-physical-clocks-and-ntp](../../distributed/04-physical-clocks-and-ntp/2-summary.md) — 벽시계 자체의 오차
- 연결
  - [database/27-temporal-types-and-session-timezone](../../database/27-temporal-types-and-session-timezone/2-summary.md) — `timestamp`/`timestamptz`, 세션 시간대, 9시간 밀림, 날짜 경계
  - [database/50-temporal-and-bitemporal-tables](../../database/50-temporal-and-bitemporal-tables/2-summary.md) — 유효 시간·기록 시간
  - [languages/java/syntax/51-java-time-types](../../../languages/java/syntax/51-java-time-types/2-summary.md) — 타입·공백·중복·tzdb 판 실측 · [52-duration-period-formatter](../../../languages/java/syntax/52-duration-period-formatter/2-summary.md) — `Duration`·`Period`·포매터
  - [testing/10-testing-time-and-concurrency](../../testing/10-testing-time-and-concurrency/2-summary.md)
  - [23-versioned-rules-and-effective-dating](../23-versioned-rules-and-effective-dating/2-summary.md) — 발효 시각도 "어느 지역의 자정인가"를 정해야 한다
- 근거
  - Jon Skeet, "Storing UTC is not a silver bullet"(2019-03-27) <https://codeblog.jonskeet.uk/2019/03/27/storing-utc-is-not-a-silver-bullet/>
  - IANA Time Zone Database <https://www.iana.org/time-zones> · NEWS <https://data.iana.org/time-zones/tzdb/NEWS> — 2025a(파라과이 -03 상시), 2026e(매니토바 -05 상시, 2026-09-29)
  - RFC 9557 "Date and Time on the Internet: Timestamps with Additional Information"(2024-04) <https://www.rfc-editor.org/rfc/rfc9557> — 접미사 형식, critical 플래그, 3.4 불일치, `Z` 재정의
  - Java SE 21 API — `ZonedDateTime`(공백·중복 규칙), `ZoneRules`, `LocalDate.plusMonths`, `Period`, `Duration` · 소스 openjdk/jdk21u `java/time/zone/ZoneRules.java`(binarySearch), `java/time/LocalDate.java`(`resolvePreviousValid`)
  - PostgreSQL 17 문서 8.5.3 Time Zones(IANA 데이터, 미래는 최신 규칙 가정), 9.9.4 `AT TIME ZONE` <https://www.postgresql.org/docs/17/datatype-datetime.html> · 설치 문서 `--with-system-tzdata` <https://www.postgresql.org/docs/17/install-make.html>
  - Microsoft, "Summary of Windows Azure Service Disruption on Feb 29th, 2012"(Bill Laing) <https://azure.microsoft.com/en-us/blog/summary-of-windows-azure-service-disruption-on-feb-29th-2012/>
  - Zune 30 2008-12-31 정지 — Wikipedia "Zune 30" <https://en.wikipedia.org/wiki/Zune_30>(2차 출처)
- 실험 목록
  - `Exp13.java` — JDK 21.0.12(eclipse-temurin:21-jdk, tzdb 2026b, `--cpus=2`): A 위니펙 예약 규칙 갱신 모형, B 매월 31일, C 생일 UTC 자정, D 02:30 알람(현지 규칙 vs +24h), E `Period` vs `Duration`, F 윤일, G 벽시계 일치형 스케줄러
  - `Extra.java` — RFC 9557 형식 문자열의 `ZonedDateTime.parse`
  - 참고: JDK 17.0.19(eclipse-temurin:17-jdk-jammy) 번들 tzdb는 2026a였다(`Tz.java`)
  - 참고: postgres:17(17.11) 컨테이너의 `pg_config --configure`·`/usr/share/zoneinfo/tzdata.zi` 첫 줄(`# version 2026c`)
  - 2차 리뷰 재현(2026-10-03): `getTransitions()` 마지막 원소·`getTransitionRules().size()`(New_York·Winnipeg·London·Seoul), Lord_Howe·Apia·Santiago `atStartOfDay` 하루 길이(JDK 21.0.12/tzdb 2026b), postgres:17(17.11) `timestamp '2026-11-01 01:30' AT TIME ZONE 'America/New_York'` → `06:30:00+00`
