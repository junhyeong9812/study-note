# java/syntax/52 — `Duration`·`Period`·`DateTimeFormatter` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 실제로 돌려 얻은 것이다. 프로그램 일곱(52-a\~52-g)을 **Temurin 17.0.13 · 21.0.5 · 25.0.1** 에서 각각 돌렸다.\
> ★ **세 판이 같았다고 적지 않는다.** 12번에서 실제로 갈렸다.\
> javadoc 인용은 JDK 21.0.5 의 `lib/src.zip` — `java.base/java/time/Duration.java`·`Period.java`·`temporal/TemporalUnit.java`·`format/DateTimeFormatter.java`·`format/DateTimeFormatterBuilder.java` 원문이다.\
> 측정 조건: 기본 시간대 `Asia/Seoul`, 기본 `Locale` `ko_KR`.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 서머타임이 있는 날 하루를 더하면

**출력** (`Ex.java` — 52-a, 17·21·25 동일 — tzdb 줄만 다르다)

```text
--- (1) 봄 — 하루가 23시간인 날. Period 와 Duration 이 갈린다
  출발            : 2026-03-07T12:00-05:00[America/New_York]
  plus(Period.ofDays(1))    : 2026-03-08T12:00-04:00[America/New_York]
  plus(Duration.ofDays(1))  : 2026-03-08T13:00-04:00[America/New_York]
  plusDays(1)               : 2026-03-08T12:00-04:00[America/New_York]
  plusHours(24)             : 2026-03-08T13:00-04:00[America/New_York]
  Period 쪽 실제 경과 시간  : PT23H
  Duration 쪽 실제 경과     : PT24H
```

**같은 답끼리 묶으면**

```text
  "벽시계 12:00 을 지킨다"          "24시간을 채운다"
  +--------------------------+      +--------------------------+
  | plus(Period.ofDays(1))   |      | plus(Duration.ofDays(1)) |
  | plusDays(1)              |      | plusHours(24)            |
  +--------------------------+      +--------------------------+
     -> 2026-03-08T12:00               -> 2026-03-08T13:00
     실제 경과 23시간                   실제 경과 24시간
```

**실제 경과 시간**

- `Period` 쪽 = **`PT23H`** (23시간)
- `Duration` 쪽 = **`PT24H`** (24시간)
- 그날 02:00 에 시계를 앞당겨 **한 시간이 사라졌기** 때문이다([`../51-java-time-types/`](../51-java-time-types/) 3번의 갭).

**`plusDays` 는 어느 쪽인가**

- **`Period` 쪽**이다. 날짜 필드를 한 칸 올린 뒤 그 지역의 오프셋을 다시 구한다.
- 이름이 `plusDays` / `plusHours` 로 나란히 생겼는데 **의미 축이 다르다.** 이것이 함정의 본체다.

**예외나 경고**

- **없다.** 네 줄 다 조용히 성공한다. 한 시간 다른 답이 나올 뿐이다.

### 2. 가을에는 반대로 틀린다

**출력** (`Ex.java` — 52-a, 17·21·25 동일)

```text
--- (2) 가을 — 하루가 25시간인 날
  출발            : 2026-10-31T12:00-04:00[America/New_York]
  plus(Period.ofDays(1))   : 2026-11-01T12:00-05:00[America/New_York]
  plus(Duration.ofDays(1)) : 2026-11-01T11:00-05:00[America/New_York]
  Period 쪽 실제 경과      : PT25H
  Duration 쪽 실제 경과    : PT24H
```

**`Period` 쪽 실제 경과**

- **`PT25H`** — 그날 새벽 01:00\~01:59 가 두 번 있었기 때문이다(중복 구간).

**방향의 차이**

```text
          Period 가 도착하는 벽시계    Duration 이 도착하는 벽시계
  봄      12:00                       13:00   (한 시간 늦게)
  가을    12:00                       11:00   (한 시간 일찍)

  Duration 은 언제나 24시간이다. 틀리는 방향만 반대다.
```

**1년에 몇 번**

- **두 번**이다(봄 전이와 가을 전이). 전이가 있는 지역 한정이다.
- 그리고 한 번 어긋나면 **그 다음 실행부터 계속 어긋난 시각**으로 돈다 — 누적된다.

**`Asia/Seoul` 에서 돌리면**

**출력** (`Ex.java` — 52-a)

```text
--- (3) 전이 없는 날에는 둘이 같다 — 그래서 서울에서 개발하면 안 보인다
  plus(Period.ofDays(1))   : 2026-03-08T12:00+09:00[Asia/Seoul]
  plus(Duration.ofDays(1)) : 2026-03-08T12:00+09:00[Asia/Seoul]
  두 결과가 같나 : true
```

- **완전히 같다.** 서울은 1989년 이후 전이가 없다.
- 그래서 **국내 테스트만으로는 이 버그가 안 잡힌다.** 전이 있는 지역을 테스트에 하나 넣어야 한다.

### 3. 같은 구간을 네 가지로 재면

**출력** (`Ex.java` — 52-a, 17·21·25 동일)

```text
--- (4) between — 같은 구간을 세 가지로 잰다
  from : 2026-03-07T12:00-05:00[America/New_York]
  to   : 2026-03-08T12:00-04:00[America/New_York]
  Duration.between        : PT23H   (23시간)
  ChronoUnit.DAYS.between : 1
  ChronoUnit.HOURS.between: 23
  Period.between(날짜만)   : P1D
```

**`DAYS.between` 이 1 인 이유**

```text
  ChronoUnit.DAYS.between(a, b) 가 하는 일

  a 의 타입(ZonedDateTime)에게 "DAYS 단위로 몇 칸 떨어졌나" 를 묻는다
                 |
  ZonedDateTime 은 달력으로 답한다 -> 3/7 -> 3/8 은 한 칸
                 |
  실제 경과가 23시간이어도 1 이다
```

- `ChronoUnit` 은 **대상 타입에게 위임한다.** 어떤 타입인지가 답을 바꾼다.
- 같은 호출을 `Instant` 두 개에 하면 **0** 이 나온다(23시간은 하루가 안 된다). 타입이 답을 바꾸는 증거다.

**`Period.between` 이 `ZonedDateTime` 을 못 받는 이유**

- 시그니처가 **`Period.between(LocalDate, LocalDate)` 하나뿐**이기 때문이다(52-g 에서 확인).
- `Period` 는 날짜만 다루는 타입이라, **시각을 어떻게 처리할지 정의되지 않는다.**

**"실제로 흐른 시간"을 답하는 것**

- **`Duration.between`** 뿐이다 — `PT23H`.
- `ChronoUnit.HOURS.between` 도 23 이지만 그것은 "완전한 시간 단위의 개수"다. 분 이하가 잘린다.

**"며칠 지났나"**

- 의도에 따라 다르다.
  - **달력으로 며칠 넘겼나** → `ChronoUnit.DAYS.between(날짜, 날짜)`
  - **24시간이 몇 번 흘렀나** → `Duration.between(...).toDays()`
- 이 예에서는 전자가 1, 후자도 `PT23H` 라 **0** 이다. 값이 다르다.

### 4. `ChronoUnit.between` 의 버림

**출력** (`Ex.java` — 52-b, 17·21·25 동일)

```text
--- (3) ChronoUnit.between 은 버림이다
  t1 : 2026-01-31T10:00   t2 : 2026-03-01T15:30
  DAYS.between   : 29
  HOURS.between  : 701
  MONTHS.between : 1   (1개월 하고 며칠이지만 1)
  Duration.between.toDays : 29
  방향을 뒤집으면 : -29
```

**실제 간격**

- 2026-01-31 10:00 → 2026-03-01 15:30
- 1월 31일에서 3월 1일까지 **29일**(2026년 2월은 28일), 거기에 **5시간 30분**.
- 총 **701시간 30분** — `HOURS.between` 이 701 인 것과 맞는다.

**내림인가 0 방향 절사인가**

```text
  실제       +29.23일          -29.23일
  내림       +29               -30       <- 아니다
  0 방향     +29               -29       <- 실측이 이쪽이다
                                ^^^
                  "방향을 뒤집으면 : -29" 가 그 증거다
```

- **0 방향 절사**다. 부호와 무관하게 소수부를 버린다.

**"30일 무료 체험"**

```java
if (ChronoUnit.DAYS.between(가입시각, 지금) < 30) { /* 무료 */ }
```

- 가입 후 **29일 23시간 59분**은 `DAYS.between` 이 29 라서 **아직 무료**다.
- 즉 실제로는 **30일 + 최대 하루 미만**까지 무료가 된다.
- 방어: 시각 비교로 바꾼다 — `지금.isBefore(가입시각.plus(Duration.ofDays(30)))`.

**javadoc**

> The calculation returns a whole number, representing the number of **complete units** between the two temporals.

- "complete units" 가 곧 버림이다.

### 5. `Duration` 과 `Period` 를 섞으면

**컴파일 에러** (`Ex.java` — 52-c, 17·21·25 동일)

```text
Ex.java:6: error: incompatible types: Period cannot be converted to Duration
        Duration d = Duration.ofHours(1).plus(Period.ofDays(1));
                                                           ^
Note: Some messages have been simplified; recompile with -Xdiags:verbose to get full output
1 error
```

**실행 결과** (`Ex.java` — 52-b, 17·21·25 동일)

```text
--- (1) 섞어 쓰면 — Duration 에 Period 를 더한다
Duration.ofHours(1).plus(Duration.ofMinutes(30)) : PT1H30M
Duration.ofHours(1).plus(Period.ofDays(1))       : 컴파일 에러 (아래 Ex.java 52-c)
Period.ofDays(1).plus(Period.ofMonths(1))        : P1M1D
Period.ofDays(1).plus(Duration.ofHours(1))       : java.time.DateTimeException: Unit must be Years, Months or Days, but was Seconds
--- (7) Duration 을 LocalDate 에 더하면
d1.plus(Duration.ofDays(1))  : java.time.temporal.UnsupportedTemporalTypeException: Unsupported unit: Seconds
d1.plus(Duration.ofHours(1)) : java.time.temporal.UnsupportedTemporalTypeException: Unsupported unit: Seconds
d1.plus(Period.ofDays(1))    : 2026-02-01
```

**성공 / 실패**

| 호출 | 결과 |
|---|---|
| `Duration.plus(Duration)` | **성공** — `PT1H30M` |
| `Duration.plus(Period)` | **컴파일 에러** |
| `Period.plus(Period)` | **성공** — `P1M1D` |
| `Period.plus(Duration)` | **런타임** `DateTimeException: Unit must be Years, Months or Days, but was Seconds` |
| `LocalDate.plus(Duration)` | **런타임** `UnsupportedTemporalTypeException: Unsupported unit: Seconds` |
| `LocalDate.plus(Period)` | **성공** — `2026-02-01` |

**왜 시점이 다른가**

```text
  Duration.plus(Duration other)          Period.plus(TemporalAmount amountToAdd)
         ^                                      ^
  타입이 Duration 으로 좁다               TemporalAmount 라 Period·Duration 둘 다 들어온다
         |                                      |
  컴파일러가 막는다                       메서드 안에서 단위를 보고 거부한다
```

- **좁은 시그니처 = 컴파일 타임 방어**, **넓은 시그니처 = 런타임 방어**.
- `LocalDate.plus(TemporalAmount)` 도 넓은 쪽이라 런타임에 막힌다.

**메시지에 `Seconds` 가 나오는 이유**

- `Duration` 은 속으로 **초와 나노만** 들고 있다. `ofDays(1)` 도 저장될 때는 `86400초` 다.
- 그래서 `LocalDate` 에게 전달되는 단위가 `Days` 가 아니라 **`Seconds`** 다.
- 즉 `Unsupported unit: Seconds` 는 "`Duration` 은 초 덩어리다"를 그대로 드러낸 메시지다.

**"1개월 3시간"을 한 값으로**

- **못 한다.** 표준 타입에 없다.
- 두 값을 따로 들고 순서대로 더한다.

```java
zdt.plus(Period.ofMonths(1)).plus(Duration.ofHours(3));
```

- 순서가 의미를 바꿀 수 있다(달 덧셈이 말일을 자르므로 — [`../51-java-time-types/`](../51-java-time-types/) 6번).

### 6. `toString` 이 예상과 다르다

**출력** (`Ex.java` — 52-a·52-g, 17·21·25 동일)

```text
--- (5) Duration 과 Period 의 내부 단위
  Duration.ofDays(1)      : PT24H  (초 86400)
  Period.ofDays(1)        : P1D  (년 0 월 0 일 1)
  Duration.getUnits()     : [Seconds, Nanos]
  Period.getUnits()       : [Years, Months, Days]
  Period.ofMonths(1).getDays() : 0   (월은 날로 환산되지 않는다)
  Period.of(1,2,3)        : P1Y2M3D
  Period.ofWeeks(2)       : P14D   (주는 날로 환산된다)
  Duration.ofHours(25)    : PT25H   (일로 올려 적지 않는다)
  Duration.ofHours(25).toDaysPart()/toHoursPart() : 1 / 1
--- Duration.toDays 와 toDaysPart
  ofHours(25).toDays()      : 1
  ofHours(25).toDaysPart()  : 1
  ofHours(25).toHours()     : 25
  ofHours(25).toHoursPart() : 1
```

**`Duration.ofDays(1)` 이 `P1D` 가 아닌 이유**

- `Duration` 의 저장 단위는 **초와 나노뿐**이다. 일 단위가 없다.
- 그러니 86,400초를 문자열로 적을 때 쓸 수 있는 가장 큰 단위가 **시간**이라 `PT24H` 가 된다.
- javadoc: "This class models a quantity or amount of time **in terms of seconds and nanoseconds**."

**`Period.ofWeeks(2)` 가 `P2W` 가 아닌 이유**

- `Period` 의 저장 단위는 **년·월·일**이다. 주가 없다.
- 한 주는 **항상 7일**이므로 안전하게 14일로 환산된다.
- 반대로 **월은 날로 환산되지 않는다** — 한 달이 며칠인지 모르기 때문이다(`Period.ofMonths(1).getDays() == 0`).

**`getUnits()`**

| | 돌려주는 것 |
|---|---|
| `Duration.getUnits()` | `[Seconds, Nanos]` |
| `Period.getUnits()` | `[Years, Months, Days]` |

- 이 두 줄이 이 주제 전체의 요약이다.

**`toDays` 대 `toDaysPart`**

```text
  Duration.ofHours(25) = 1일 1시간

  toDays()      1    <- 총 일수 (25 / 24)
  toDaysPart()  1    <- "일 자리"의 값
  toHours()     25   <- 총 시간
  toHoursPart() 1    <- "시간 자리"의 값
                ^^
  toDays 와 toDaysPart 는 이 예에서 우연히 같다.
  갈리는 것은 toHours(25) 와 toHoursPart(1) 쪽이다.
```

- `*Part()` 계열은 **Java 9** 부터다(`src.zip` 의 `@since 9` 확인).
- 사람이 읽을 문자열을 만들 때는 `*Part()` 를 쓴다 — `"1일 1시간"`.

### 7. `Period` 는 정규화되지 않는다

**출력** (`Ex.java` — 52-a·52-g, 17·21·25 동일)

```text
--- (7) Period 는 정규화되지 않는다
  Period.between(1/31, 3/1) : P1M1D
  toTotalMonths             : 1
  getDays                   : 1
  Period.of(0,13,0)         : P13M -> normalized P1Y1M
  ChronoUnit.DAYS.between(1/31, 3/1) : 29
--- Period 의 equals 는 필드 비교다
  Period.of(0,1,0).equals(Period.ofDays(30)) : false
  Period.of(0,13,0).equals(Period.of(1,1,0)) : false
  Period.of(0,13,0).normalized().equals(Period.of(1,1,0)) : true
  Period.ofWeeks(2).equals(Period.ofDays(14)) : true
```

**`p` 는**

- **`P1M1D`** — "1개월 1일".

**`p.getDays()` 가 총 일수가 아닌 이유**

```text
  Period.between 의 계산 순서

  1/31 --[월을 센다]--> 1개월 (도착 2/28, 말일로 잘림)
  2/28 --[남은 일을 센다]--> 1일 -> 3/1

  결과 P1M1D 에서
    getMonths() = 1    <- 센 월 수
    getDays()   = 1    <- "월을 세고 남은" 일 수
                   ^^^
       총 일수가 아니라 나머지다
```

**실제 총 일수**

- **29일** — `ChronoUnit.DAYS.between` 이 답한다.

**`normalized()` 가 정리하는 것**

- **년과 월만** 정리한다. `P13M` → `P1Y1M`.
- **일은 안 건드린다.** 한 달이 며칠인지 모르기 때문이다 — `P45D` 는 그대로 `P45D` 다.

**`equals`**

- **`Period.of(0,1,0).equals(Period.ofDays(30))` = `false`** — 필드가 다르다.
- `Period.of(0,13,0).equals(Period.of(1,1,0))` 도 **`false`** — 같은 길이인데 필드가 다르다.
- `normalized()` 를 거치면 **`true`** 가 된다.
- `Period.ofWeeks(2).equals(Period.ofDays(14))` 는 **`true`** — 주는 생성 시점에 날로 환산되므로 필드가 이미 같다.
- 대조적으로 `Duration.ofDays(1).equals(Duration.ofHours(24))` 는 **`true`** 다(둘 다 86,400초). `compareTo` 도 **0**.
- 즉 **`Duration` 은 값 비교, `Period` 는 필드 비교**다.

### 8. `YYYY` 와 `yyyy` 를 연말에 찍으면

**출력** (`Ex.java` — 52-d, 17·21·25 동일, `Locale.ENGLISH`)

```text
--- (1) YYYY 대 yyyy — 연말 연초를 훑는다 (Locale.ENGLISH)
  날짜        요일   yyyy         YYYY         다른가
  2025-12-25  Thu   2025-12-25   2025-12-25   
  2025-12-26  Fri   2025-12-26   2025-12-26   
  2025-12-27  Sat   2025-12-27   2025-12-27   
  2025-12-28  Sun   2025-12-28   2026-12-28   <<< 다르다
  2025-12-29  Mon   2025-12-29   2026-12-29   <<< 다르다
  2025-12-30  Tue   2025-12-30   2026-12-30   <<< 다르다
  2025-12-31  Wed   2025-12-31   2026-12-31   <<< 다르다
  2026-01-01  Thu   2026-01-01   2026-01-01   
  2026-01-02  Fri   2026-01-02   2026-01-02   
  2026-01-03  Sat   2026-01-03   2026-01-03   
  2026-01-04  Sun   2026-01-04   2026-01-04   
  2026-01-05  Mon   2026-01-05   2026-01-05   
  2026-01-06  Tue   2026-01-06   2026-01-06   
```

**며칠 · 어느 날**

- **나흘** — 2025-12-28(일) \~ 2025-12-31(수).

**`YYYY` 값**

- **2026** — 실제 연도보다 **1년 앞선다.**

```text
  2025년 12월 마지막 주 (Locale.ENGLISH: 주가 일요일에 시작, 첫 주 최소 1일)

   일    월    화    수  |  목    금    토
   28    29    30    31 |  1     2     3
   ^^^^^^^^^^^^^^^^^^^^ |
   2025년 날짜인데       | 여기서 해가 바뀐다
   이 주는 "2026년 1주"  |
```

- 주는 쪼개지지 않으므로 **이 주 전체가 2026년의 주**가 된다.
- 그 주에 속한 **2025년 날짜 나흘**이 `YYYY=2026` 을 받는다.

**1월 쪽에서도 어긋나는가**

- **이 실측 범위(1/1\~1/6, 그리고 6개 해의 1/1\~1/4)에서는 한 건도 없었다.**
- 이유는 `minimalDaysInFirstWeek=1` 이라 1월 1일이 든 주가 언제나 "그 해의 1주"가 되기 때문이다.
- 다만 `minimalDays=4` 인 `Locale`(프랑스·ISO)에서는 **1월 초가 전년도 주에 속할 수 있다.** 그 경우는 **안 돌려 봄**이다.

**로그 파일명의 정렬** (`Ex.java` — 52-f)

```text
  app-2025-12-25.log   (실제 2025-12-25)
  app-2025-12-26.log
  app-2025-12-27.log
  app-2026-01-01.log   <- 이름순으로는 여기
  app-2026-01-02.log
  app-2026-12-28.log   <- 실제로는 2025-12-28 인데 목록 끝으로 갔다
  app-2026-12-29.log
  app-2026-12-30.log
  app-2026-12-31.log
```

- **나흘치가 1년 뒤로 밀려** 목록 끝에 가 붙는다.
- 날짜 기반 로테이션·삭제 스크립트가 그 파일들을 **못 찾거나, 1년 뒤에 지운다.**

**기본 `Locale`(`ko_KR`)이면**

**출력** (`Ex.java` — 52-f, 17·21·25 동일)

```text
기본 Locale : ko_KR
--- 기본 Locale 로 (ofPattern 에 Locale 을 안 주면)
  yyyy-MM-dd : 2025-12-28
  YYYY-MM-dd : 2026-12-28
```

- **똑같이 어긋난다.** `ko_KR` 도 주가 일요일에 시작하고 `minimalDays=1` 이다.
- **`Locale` 을 안 준다고 안전해지지 않는다.**

### 9. 같은 `YYYY` 가 `Locale` 에 또 달렸다

**출력** (`Ex.java` — 52-d, 17·21·25 동일)

```text
--- (3) 같은 YYYY 가 Locale 에 따라 또 달라진다 — 2026-12-27(일)
  날짜/요일 : 2026-12-27 SUNDAY
  en       YYYY=2027  firstDayOfWeek=SUNDAY  minimalDays=1  주=1
  en_US    YYYY=2027  firstDayOfWeek=SUNDAY  minimalDays=1  주=1
  fr_FR    YYYY=2026  firstDayOfWeek=MONDAY  minimalDays=4  주=52
  ko_KR    YYYY=2027  firstDayOfWeek=SUNDAY  minimalDays=1  주=1
  ISO 기준 weekBasedYear : 2026  주 52
```

**세 `Locale` 의 `YYYY`**

| `Locale` | `YYYY` | `firstDayOfWeek` | `minimalDaysInFirstWeek` | 주 번호 |
|---|---|---|---|---|
| `en` | **2027** | SUNDAY | 1 | 1 |
| `fr_FR` | **2026** | MONDAY | 4 | 52 |
| `ko_KR` | **2027** | SUNDAY | 1 | 1 |

**갈리는 이유**

```text
  2026-12-27 은 일요일이다.

  주 시작 = 일요일 (en · ko_KR)        주 시작 = 월요일 (fr_FR)
  -> 12/27 이 새 주의 첫날               -> 12/27 은 지난 주의 마지막 날
  -> 그 주는 1/1, 1/2 를 품는다          -> 그 주는 12/21~12/27
  -> 첫 주 최소 1일이면 그 주가          -> 12/21 이 속한 주가 2026년 52주
     2027년 1주가 된다
        |                                        |
  YYYY = 2027                              YYYY = 2026
```

- **`firstDayOfWeek`** 와 **`minimalDaysInFirstWeek`** 두 값이 답을 정한다.
- `DateTimeFormatterBuilder` 소스의 패턴 설명이 `localized` 라고 명시한다.

  > `Y..Y 4..n append special **localized** WeekFields element for numeric week-based-year`

**`IsoFields.WEEK_BASED_YEAR`**

- **2026**, 주 **52**.
- 세 `Locale` 중 **`fr_FR` 과 같다** — 프랑스의 `WeekFields` 가 ISO 8601 정의(월요일 시작, 최소 4일)와 일치하기 때문이다.

**ISO 8601 을 확실히 얻으려면**

```java
// Locale 에 기대지 않는다
int isoYear = date.get(IsoFields.WEEK_BASED_YEAR);
int isoWeek = date.get(IsoFields.WEEK_OF_WEEK_BASED_YEAR);

// 또는 상수 포매터
date.format(DateTimeFormatter.ISO_WEEK_DATE);   // 2026-W52-7
```

### 10. 비슷하게 생긴 패턴 글자

**출력** (`Ex.java` — 52-d, 대상 `2026-03-08T16:05:09+09:00[Asia/Seoul]`, `Locale.ENGLISH`, 17·21·25 동일)

```text
  MM/dd vs mm/DD : 03/08 vs 05/67
  HH:mm : 16:05
  hh:mm : 04:05   (a 가 없으면 오전/오후가 사라진다)
  hh:mm a : 04:05 PM
  z          시간대 이름                 -> KST
  zzzz       시간대 이름 길게              -> Korean Standard Time
  Z          오프셋 +0900              -> +0900
  XXX        오프셋 +09:00             -> +09:00
  VV         지역 ID                  -> Asia/Seoul
```

**여덟 줄**

| 패턴 | 결과 |
|---|---|
| `MM/dd` | `03/08` |
| `mm/DD` | **`05/67`** |
| `HH:mm` | `16:05` |
| `hh:mm` | **`04:05`** |
| `z` | `KST` |
| `Z` | `+0900` |
| `XXX` | `+09:00` |
| `VV` | `Asia/Seoul` |

**글자의 뜻**

```text
  M = month        m = minute
  D = day-of-year  d = day-of-month
  H = 0~23         h = 1~12
  u = proleptic year   y = year-of-era   Y = week-based-year
```

- `mm/DD` 가 **`05/67`** 인 것을 보라. 3월 8일은 그 해 **67번째 날**이고, 05 는 분이다.
- **날짜처럼 생긴 자리에 전혀 다른 값**이 들어가는데, 형식이 그럴듯해서 눈으로는 안 잡힌다.

**`hh:mm` 만 쓰면**

- **오전/오후 표시가 사라진다.** 16:05 가 `04:05` 로 나온다.
- 파싱할 때도 `04:05` 만으로는 04시인지 16시인지 알 수 없다.
- `a` 를 같이 써야 한다 — `hh:mm a` → `04:05 PM`.

**`z`·`Z`·`X`·`V`**

| 글자 | 찍는 것 | 예 |
|---|---|---|
| `z` / `zzzz` | 시간대 **이름** | `KST` / `Korean Standard Time` |
| `Z` | 오프셋, 콜론 없이 | `+0900` |
| `X` / `XXX` | 오프셋, ISO 형식 | `+09` / `+09:00` |
| `V` / `VV` | **지역 ID** | `Asia/Seoul` |

- `z` 의 이름은 **`Locale` 에 따라 달라진다.** 기계가 읽을 형식에는 `X` 나 `V` 를 쓴다.

**`u` 와 `y` 가 갈리는 때**

**출력** (`Ex.java` — 52-d)

```text
--- (6) yyyy 대 uuuu — 기원전에서 갈린다
  LocalDate.of(-1, 6, 15) : -0001-06-15
  yyyy : 0002 BC
  uuuu : -0001
  yyyy 만 쓰고 G 없이 파싱 : 0001-06-15
```

- **기원전**에서 갈린다. `y` 는 연호 기준이라 기원전 1년이 "2 BC", `u` 는 `-0001`.
- 그리고 **`STRICT` 파싱**에서 갈린다(11번).

### 11. `ResolverStyle` 과 포맷 실패

**출력** (`Ex.java` — 52-d, `Locale.ENGLISH`)

```text
--- (7) 타입에 없는 필드를 찍으려 하면
LocalDate.format(ISO_DATE_TIME)  : java.time.temporal.UnsupportedTemporalTypeException: Unsupported field: HourOfDay
LocalDateTime.format(ISO_INSTANT) : java.time.temporal.UnsupportedTemporalTypeException: Unsupported field: InstantSeconds
Instant.format(...)              : 컴파일 에러 — Instant 에는 format 메서드가 없다 (Ex.java 52-e)
ISO_LOCAL_DATE.format(Instant)    : java.time.temporal.UnsupportedTemporalTypeException: Unsupported field: Year
Instant + zone 붙인 formatter     : 2026-03-08
ISO_INSTANT.withZone 으로 Instant : 2026-03-08 16:30
--- (8) 파싱 엄격도 — ResolverStyle
  STRICT 로 2026-02-30 : java.time.format.DateTimeParseException: Text '2026-02-30' could not be parsed: Invalid date 'FEBRUARY 30'
  SMART 로 2026-02-30 : 2026-02-28
  LENIENT 로 2026-02-30 : 2026-03-02
  STRICT + yyyy 로 2026-03-08 : java.time.format.DateTimeParseException: Text '2026-03-08' could not be parsed: Unable to obtain LocalDate from TemporalAccessor: {DayOfMonth=8, MonthOfYear=3, YearOfEra=2026},ISO of type java.time.format.Parsed
```

**세 `ResolverStyle`**

```text
  "2026-02-30"

  STRICT   -> DateTimeParseException: Invalid date 'FEBRUARY 30'
  SMART    -> 2026-02-28    (말일로 자른다)
  LENIENT  -> 2026-03-02    (30 - 28 = 2 를 3월로 넘긴다)
```

**기본값**

- **`SMART`** 다. `DateTimeFormatter.ofPattern` 의 javadoc 이 "It uses `ResolverStyle.SMART` resolver style." 라고 명시한다.
- 즉 **아무것도 설정 안 하면 2월 30일이 조용히 2월 28일**이 된다.

**`STRICT` 에서 `yyyy` 가 거부되는 이유**

```text
  yyyy 가 파싱해 넣는 필드 = YearOfEra (연호 안의 연도)

  {DayOfMonth=8, MonthOfYear=3, YearOfEra=2026}
                                ^^^^^^^^^
  연호(G, AD/BC)가 없으면 2026년이 AD 인지 BC 인지 확정할 수 없다
                |
  STRICT 는 추측하지 않는다 -> LocalDate 를 만들 수 없다고 거부
```

- 대신 **`uuuu`** 를 쓴다. `uuuu` 는 proleptic year 라 연호가 필요 없다.
- 위 출력의 세 `ResolverStyle` 실험이 `uuuu-MM-dd` 로 돼 있는 이유도 이것이다.

**마지막 세 줄의 실패**

| 호출 | 실패 방식 |
|---|---|
| `LocalDate.format(ISO_DATE_TIME)` | 런타임 `UnsupportedTemporalTypeException: Unsupported field: HourOfDay` |
| `LocalDateTime.format(ISO_INSTANT)` | 런타임 `UnsupportedTemporalTypeException: Unsupported field: InstantSeconds` |
| `Instant.format(...)` | **컴파일 에러** |

```text
Ex.java:6: error: cannot find symbol
        String s = Instant.parse("2026-03-08T07:30:00Z").format(DateTimeFormatter.ISO_LOCAL_DATE);
                                                        ^
  symbol:   method format(DateTimeFormatter)
  location: class Instant
1 error
```

- **`Instant` 에는 `format` 메서드가 아예 없다.** `LocalDate`·`LocalDateTime`·`ZonedDateTime` 에는 있다.
- 우회해서 `DateTimeFormatter.ISO_LOCAL_DATE.format(instant)` 로 부르면 런타임에 `Unsupported field: Year` 가 난다.

**`Instant` 를 포맷하려면**

```java
// 방법 1 — 지역을 붙인 뒤 포맷
instant.atZone(zone).format(DateTimeFormatter.ISO_LOCAL_DATE);        // 2026-03-08

// 방법 2 — 포매터에 지역을 붙인다
DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm", Locale.ENGLISH)
                 .withZone(ZoneId.of("Asia/Seoul"))
                 .format(instant);                                     // 2026-03-08 16:30
```

- 어느 쪽이든 **지역을 명시해야** 한다. `Instant` 에는 연·월·일이 없기 때문이다([`../51-java-time-types/`](../51-java-time-types/) 8번).

### 12. 세 JDK 에서 무엇이 달랐나

**tzdb 판**

| JDK | tzdb | 지역 개수 |
|---|---|---|
| 17.0.13 | 2024a | 603 |
| 21.0.5 | 2024a | 603 |
| 25.0.1 | **2025b** | **604** |

- 자세한 것은 [`../51-java-time-types/`](../51-java-time-types/) 13번이 정본이다.

**`DateTimeParseException` 의 메시지**

**출력** (`Ex.java` — 52-d 의 (8) 마지막 줄)

```text
JDK 17.0.13
  ... Unable to obtain LocalDate from TemporalAccessor: {YearOfEra=2026, MonthOfYear=3, DayOfMonth=8},ISO of type java.time.format.Parsed

JDK 21.0.5
  ... Unable to obtain LocalDate from TemporalAccessor: {DayOfMonth=8, MonthOfYear=3, YearOfEra=2026},ISO of type java.time.format.Parsed

JDK 25.0.1
  ... Unable to obtain LocalDate from TemporalAccessor: {DayOfMonth=8, YearOfEra=2026, MonthOfYear=3},ISO of type java.time.format.Parsed
```

**갈린 조각**

```text
  {YearOfEra=2026, MonthOfYear=3, DayOfMonth=8}   <- 17
  {DayOfMonth=8, MonthOfYear=3, YearOfEra=2026}   <- 21
  {DayOfMonth=8, YearOfEra=2026, MonthOfYear=3}   <- 25
  ^
  중괄호 안 필드 나열 순서. 세 판이 전부 다르다.
```

- 파싱된 필드를 담은 맵의 **순회 순서**다. 어디에도 정렬을 약속한 적이 없다.
- 예외 타입·문장 구조·필드 이름·값은 셋 다 같다. **순서만** 다르다.

**메시지를 테스트로 고정하면**

- **JDK 를 올릴 때마다 깨진다.** 세 번의 업그레이드에서 세 번 다 깨졌을 것이다.
- 게다가 깨지는 이유가 "동작이 바뀌어서"가 아니라 "**맵 순회 순서가 바뀌어서**"라 디버깅이 헛돈다.

**예외 타입은 계약인가**

- **그렇다.** `DateTimeFormatter.parse`·`LocalDate.parse` 의 javadoc 이 `DateTimeParseException` 을 `@throws` 로 명시한다.
- **메시지는 아니다.** javadoc 이 문구를 규정하지 않는다.

```java
// 안 된다
assertEquals("Text '2026-03-08' could not be parsed: ...", e.getMessage());

// 된다
assertThrows(DateTimeParseException.class, () -> LocalDate.parse(...));
```

### 13. 어느 것을 고르는가

| 요구 | 고를 것 | 이유 |
|---|---|---|
| HTTP 타임아웃 | **`Duration`** | 기계 시간이다. 서머타임과 무관해야 한다 |
| "한 달 무료 체험" 만료일 | **`Period.ofMonths(1)`** | 아래 |
| 나이 | **`Period.between(생일, 오늘).getYears()`** | 달력 기준이 사람의 정의와 맞는다 |
| 두 로그 줄의 시각 차이 | **`Duration.between(i1, i2)`** | 실제 흐른 시간이다 |
| 파티션 키 `2026-03-08` | **`DateTimeFormatter.ISO_LOCAL_DATE`** | 아래 |

**"한 달"과 30일의 차이**

```text
  1월 31일 가입

  Period.ofMonths(1)  -> 2월 28일 만료   (달력 한 칸, 말일로 잘림)
  Duration.ofDays(30) -> 3월 2일 만료    (30 × 86400초)

  3월 31일 가입

  Period.ofMonths(1)  -> 4월 30일 만료   (30일짜리 달)
  Duration.ofDays(30) -> 4월 30일 만료   (우연히 같다)

  5월 31일 가입

  Period.ofMonths(1)  -> 6월 30일 만료
  Duration.ofDays(30) -> 6월 30일 만료   (또 같다)
```

- **달마다 답이 다르다.** 약관에 "1개월"이라 적혀 있으면 `Period`, "30일"이라 적혀 있으면 `Duration` 또는 `plusDays(30)`.
- 위 표의 값은 `plusMonths`/`plusDays` 의 동작에서 **유도한 것**이고(1/31+1개월=2/28 은 [`../51-java-time-types/`](../51-java-time-types/) 6번에서 실행으로 확인했다), 3·5월 사례는 **안 돌려 봄**이다.

**`ofPattern` 을 피하는 이유**

- 손으로 쓰는 순간 `Y`·`m`·`D`·`h` 중 하나를 밟을 수 있다(8번·10번).
- `ISO_LOCAL_DATE` 는 **`Locale` 에 독립**이고, 패턴 글자를 쓰지 않으므로 그 함정이 원천적으로 없다.
- 꼭 패턴을 써야 하면 **`ofPattern("yyyy-MM-dd", Locale.ENGLISH)`** — `yyyy` 와 `Locale` 을 둘 다 명시한다.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Ex.java` (52-a) | 봄/가을 DST 에서 `Period` 대 `Duration`, 서울에서는 같다는 것, 네 가지 `between`, 내부 단위, 달 덧셈의 비결합, `Period` 비정규화 | 17 · 21 · 25 (**tzdb 줄만 다름**) |
| `Ex.java` (52-b) | `Period.plus(Duration)` 런타임 거부, `between` 의 인자 타입, 버림, 음수 표기, `Duration`/`Period` 파싱 문법, `LocalDate.plus(Duration)` | 17 · 21 · 25 (**출력 동일**) |
| `Ex.java` (52-c) | `Duration.plus(Period)` 가 **컴파일 에러**라는 것 | 17 · 21 · 25 (**메시지 동일**) |
| `Ex.java` (52-d) | `YYYY` 대 `yyyy` 6개 해 훑기, `Locale` 별 `WeekFields`, 패턴 글자 21개, `yyyy`/`uuuu`, 타입에 없는 필드, `ResolverStyle` 3종 | 17 · 21 · 25 (**★ 마지막 한 줄이 세 판 전부 다름**) |
| `Ex.java` (52-e) | `Instant.format(...)` 이 **컴파일 에러**라는 것 | 17 · 21 · 25 (**메시지 동일**) |
| `Ex.java` (52-f) | 기본 `Locale`(`ko_KR`)에서도 `YYYY` 가 어긋나는 것, 로그 파일명 9일치 | 17 · 21 · 25 (**출력 동일**) |
| `Ex.java` (52-g) | `Period`/`Duration` 의 `equals` 의미 차이, `toDays` 대 `toDaysPart` | 17 · 21 · 25 (**출력 동일**) |
| `src.zip` 열람 | `Duration`·`Period` 클래스 javadoc, `Duration.ofDays` 의 86400초, `toDaysPart` 의 `@since 9`, `TemporalUnit.between` 의 "complete units", `DateTimeFormatter` 의 immutable·`SMART` 기본값, 패턴 글자 표, `DateTimeFormatterBuilder` 의 `Y` = localized | 21 |

**구현 의존 항목** (버전이 오르면 다시 돌려야 하는 것)

- ★ **`DateTimeParseException` 메시지의 필드 나열 순서** — 17·21·25 가 전부 달랐다. **메시지를 테스트로 고정하지 마라.**
- ★ **tzdb 판** — 17·21 = 2024a, 25 = 2025b. 1·2번의 전이 날짜가 이 데이터에서 온다.
- `ko_KR`·`en` 의 `firstDayOfWeek`·`minimalDaysInFirstWeek` — CLDR 데이터에서 온다. JDK 판이나 `-Djava.locale.providers` 설정에 따라 달라질 수 있다. 이 머신의 세 판에서는 **같았다.**
- 기본 `Locale` 이 `ko_KR` 이라는 것 — 다른 머신에서는 52-f 의 결과가 달라질 수 있다.
- `SimpleDateFormat` 의 스레드 경쟁 — **안 돌려 봄.** 재현에 스레드와 반복이 필요하다.
- `minimalDays=4` 인 `Locale` 에서 **1월 초가 전년도 주에 속하는지** — **안 돌려 봄.**
- `Period`/`Duration` 의 오버플로 동작(`Period.ofDays(Integer.MAX_VALUE)` 를 더하기) — **안 돌려 봄.**
- 13번 표의 3월·5월 만료일 — **안 돌려 봄**(1월 사례만 51번에서 실행으로 확인했다).
