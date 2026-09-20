# java/syntax/52 — `Duration`·`Period`·`DateTimeFormatter` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **선행** — [`../51-java-time-types/`](../51-java-time-types/). 갭·중복을 모르면 이 문서의 절반이 안 읽힌다.
> **기준 소스** — Temurin **JDK 21.0.5** 표준 라이브러리 소스 `java.base/java/time/Duration.java`·`Period.java`·`format/DateTimeFormatter.java`·`format/DateTimeFormatterBuilder.java`·`temporal/ChronoUnit.java`(`lib/src.zip`) · [`DateTimeFormatter` javadoc (Java SE 21)](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/time/format/DateTimeFormatter.html) · [`Duration` javadoc](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/time/Duration.html) · [`Period` javadoc](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/time/Period.html)
> **실행 검증** — 이 문서의 모든 출력은 실제로 돌려 얻은 것이다. 프로그램 일곱(52-a~52-g)을 **17.0.13 · 21.0.5 · 25.0.1** 에서 각각 돌렸다.\
> ★ **세 판의 출력이 전부 같지는 않았다.** `DateTimeParseException` 의 메시지에 들어가는 **필드 나열 순서가 세 판에서 전부 달랐다**(아래 「구현 세부사항 대 언어 보장」이 정본).\
> tzdb 판도 갈린다(17·21 = 2024a, 25 = 2025b). 이 주제의 출력 중 갈린 것은 그 줄에 표시했다.
> **버전** — `Duration`·`Period`·`DateTimeFormatter` 전부 `src.zip` 의 **`@since 1.8`**.
> **측정 조건** — 기본 시간대 `Asia/Seoul`, 기본 `Locale` `ko_KR`. `Locale` 에 따라 갈리는 출력은 그 사실이 붙어 있다.
> **범위** — 시각 **한 점**을 어느 타입으로 적나는 [`../51-java-time-types/`](../51-java-time-types/) 가 정본이다.\
> 그쪽은 **`Instant`/`LocalDateTime`/`ZonedDateTime` 의 선택**까지, 여기는 **두 점 사이의 간격과 문자열 변환**부터다.\
> 로그 시각을 **어떻게 적재·집계하나**는 [`../../../../../ops-patterns/17-timeseries/`](../../../../../ops-patterns/17-timeseries/) 가 정본이다 — 여기는 **한 값을 문자열로 바꾸는 API 표면**까지만.
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**`Duration` 은 초시계, `Period` 는 달력에 친 동그라미다.**

| 비유 | 실체 |
|---|---|
| **초시계로 잰 시간** — "86,400초 지났다" | `Duration` |
| **달력에 동그라미 치고 세기** — "한 칸 넘겼다" | `Period` |
| 초시계가 세는 눈금 | 초와 나노 |
| 달력이 세는 칸 | 년·월·일 |
| **같은 "하루"가 두 값** | 초시계로는 24시간, 달력으로는 한 칸 |
| 값을 사람 글자로 옮겨 적는 **양식지** | `DateTimeFormatter` |
| 양식지의 **칸 이름** | 패턴 글자(`yyyy`·`MM`·`dd`) |
| **비슷하게 생긴 딴 칸** | `YYYY`(주 기반 연)·`mm`(분)·`DD`(그 해 몇 번째 날) |

- **초시계는 시계가 조정돼도 상관없다.** 24시간을 재라고 하면 86,400초를 잰다.
- **달력은 벽시계를 본다.** "내일 같은 시각"은 그 지역이 서머타임을 하면 23시간일 수도 25시간일 수도 있다.
- 그래서 **"하루 뒤"라는 말은 두 가지 뜻**이고, Java 는 그것을 **타입 두 개**로 갈라 놓았다.
- 양식지 쪽 함정은 **칸 이름이 헷갈리게 생긴 것**이다. `YYYY` 와 `yyyy` 는 1년에 며칠만 다르고, 그 며칠이 하필 **연말**이다.

```text
  뉴욕에서 2026-03-07 12:00 에 출발

   Period.ofDays(1)  "달력 한 칸"     Duration.ofDays(1)  "86,400초"
        |                                   |
        v                                   v
   2026-03-08 12:00                    2026-03-08 13:00
   실제로 흐른 시간 23시간              실제로 흐른 시간 24시간
        ^                                   ^
   벽시계는 같은 12시                  벽시계가 한 시간 밀렸다
```

그림 해설:

- 그날 새벽 02:00 에 시계를 한 시간 앞당겼기 때문에 **달력 한 칸이 23시간**이 됐다.
- `Duration` 은 그 사실을 모르고 **24시간을 채워** 벽시계 13:00 에 도착했다.
- **둘 다 맞다.** 무엇을 원했느냐가 다를 뿐이다.

> **기계 시간(machine time)** — 지구의 달력·시계 제도와 무관하게 흐른 물리적 시간. `Duration` 이 이것을 잰다.\
> 예: "타임아웃 30초"는 서머타임과 무관하게 30초다.

> **달력 시간(conceptual/calendar time)** — 사람이 달력 칸으로 세는 시간. `Period` 가 이것을 잰다.\
> 예: "한 달 무료 체험"은 30일이 아니라 "다음 달 같은 날짜까지"다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. "하루 뒤"를 왜 **타입 두 개**로 갈라 놓았나 — 언제 답이 달라지나.
2. 두 시각의 간격을 재는 방법이 셋(`Duration.between`·`Period.between`·`ChronoUnit.between`)인데 **무엇이 다른가.**
3. `YYYY` 와 `yyyy` 는 왜 1년에 며칠만 다르고, 그 며칠이 왜 하필 연말인가.

## 동작 방식

### (1) DST 가 있는 날 — 하루가 23시간이 된다

**언제 쓰나** — "내일 같은 시각에 다시" 같은 스케줄을 짤 때.

**실행 결과** (`Ex.java` — 52-a, 17·21·25 동일 — tzdb 줄만 다르다)

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

```text
  America/New_York 2026-03-07 12:00 에서 출발

  실제 흐른 시간   0h        12h         13h        23h   24h
                   |----------|-----------|-----------|-----|
  벽시계          3/7 12:00  3/8 00:00   3/8 01:00  3/8 12:00  3/8 13:00
                                          |
                                     02:00 에 03:00 으로 점프
                                     (한 시간이 사라졌다)

  Period.ofDays(1)   -> "벽시계로 3/8 12:00"   = 23시간 뒤
  Duration.ofDays(1) -> "24시간 뒤"            = 벽시계로 3/8 13:00
```

그림 해설 (한 단계씩):

- `plusDays(1)` 은 **`Period` 쪽**이다 — 벽시계 12:00 을 지킨다.
- `plusHours(24)` 는 **`Duration` 쪽**이다 — 24시간을 채워 13:00 이 된다.
- 메서드 이름이 `plusDays` 와 `plusHours` 로 비슷하게 생겼는데 **의미 축이 다르다.** 이것이 실무에서 가장 자주 밟는다.
- 둘 다 예외가 없다. **조용히 한 시간 다른 답**이 나온다.

비용 — `Period` 쪽은 시간대 규칙을 매번 조회한다. `Duration` 쪽은 덧셈 한 번이다. 대신 의미가 다르다.

### (2) 가을 — 하루가 25시간이 된다

**언제 쓰나** — 같은 코드가 반대 방향으로 틀리는 것을 볼 때.

**실행 결과** (`Ex.java` — 52-a, 17·21·25 동일)

```text
--- (2) 가을 — 하루가 25시간인 날
  출발            : 2026-10-31T12:00-04:00[America/New_York]
  plus(Period.ofDays(1))   : 2026-11-01T12:00-05:00[America/New_York]
  plus(Duration.ofDays(1)) : 2026-11-01T11:00-05:00[America/New_York]
  Period 쪽 실제 경과      : PT25H
  Duration 쪽 실제 경과    : PT24H
```

```text
  봄 (3/7 -> 3/8)                        가을 (10/31 -> 11/1)

  Period   12:00 -> 12:00   23시간        Period   12:00 -> 12:00   25시간
  Duration 12:00 -> 13:00   24시간        Duration 12:00 -> 11:00   24시간
                  ^^^^^                                    ^^^^^
             한 시간 늦게 도착                        한 시간 일찍 도착

  Duration 은 언제나 24시간이다 — 틀리는 방향만 반대다.
```

그림 해설 (한 단계씩):

- 봄에는 `Duration` 이 **뒤로** 밀리고, 가을에는 **앞으로** 당겨진다.
- `Period` 쪽은 언제나 벽시계 12:00 이다. **실제 경과 시간이 23/24/25 로 변한다.**
- "매일 자정에 배치"를 `Duration.ofDays(1)` 로 돌리면 **1년에 두 번 자정이 아닌 시각에 돈다.**

비용 — 어느 쪽이 맞는지는 도메인이 정한다. "매일 자정"은 `Period`, "정확히 24시간 뒤 만료"는 `Duration`.

### (3) 전이가 없는 지역에서는 차이가 안 보인다

**언제 쓰나** — 서울에서 개발하고 해외 지역을 지원할 때.

**실행 결과** (`Ex.java` — 52-a, 17·21·25 동일)

```text
--- (3) 전이 없는 날에는 둘이 같다 — 그래서 서울에서 개발하면 안 보인다
  plus(Period.ofDays(1))   : 2026-03-08T12:00+09:00[Asia/Seoul]
  plus(Duration.ofDays(1)) : 2026-03-08T12:00+09:00[Asia/Seoul]
  두 결과가 같나 : true
```

```text
  Asia/Seoul                              America/New_York

  Period   == Duration                    Period   != Duration
       |                                       |
  테스트 통과 · 코드 리뷰 통과              1년에 두 번, 한 시간 틀림
```

그림 해설 (한 단계씩):

- 서울은 1989년 이후 전이가 없다([`../51-java-time-types/`](../51-java-time-types/) (5)).
- 그래서 **국내 테스트만으로는 (1)의 차이가 드러나지 않는다.**
- 해외 지역을 하나라도 지원한다면 **`America/New_York` 같은 전이 있는 지역으로 테스트를 하나 두어야** 한다.

비용 — 테스트를 하나 더 쓰는 값. 안 쓰면 1년에 두 번 장애가 난다.

### (4) 세 가지 `between` — 같은 구간을 다르게 잰다

**언제 쓰나** — "며칠 지났나"를 계산할 때.

**실행 결과** (`Ex.java` — 52-a, 17·21·25 동일)

```text
--- (4) between — 같은 구간을 세 가지로 잰다
  from : 2026-03-07T12:00-05:00[America/New_York]
  to   : 2026-03-08T12:00-04:00[America/New_York]
  Duration.between        : PT23H   (23시간)
  ChronoUnit.DAYS.between : 1
  ChronoUnit.HOURS.between: 23
  Period.between(날짜만)   : P1D
```

```text
  같은 두 시각, 네 가지 답

  Duration.between         PT23H    <- 실제로 흐른 시간
  ChronoUnit.HOURS.between 23       <- 같은 값을 시간 단위로
  ChronoUnit.DAYS.between  1        <- 24시간이 아닌데도 1이다
  Period.between           P1D      <- 날짜만 보고 한 칸

           23시간밖에 안 지났는데 "1일"이 나온다.
           DAYS.between 은 "완전한 24시간"이 아니라
           날짜 필드가 한 칸 넘었는지를 센다 -- 는 착각이다.
           실제 규칙은 아래 (5) 에 있다.
```

그림 해설 (한 단계씩):

- `Duration.between` 은 **실제 흐른 시간**이다 — 23시간.
- `ChronoUnit.DAYS.between` 은 **1** 이다. 24시간이 안 흘렀는데 1이 나왔다.
- `ChronoUnit` 은 대상 타입에게 **"몇 단위만큼 떨어져 있나"**를 물어보고, `ZonedDateTime` 은 **달력으로** 답한다.
- `Period.between` 은 아예 `LocalDate` 만 받는다 — 시각을 버린 뒤 세는 것이다.

비용 — 셋이 다 다른 값을 낼 수 있다. **무엇을 세고 싶은지 먼저 정하고 메서드를 고른다.**

### (5) `ChronoUnit.between` 은 버림이다

**언제 쓰나** — "가입한 지 며칠 됐나"를 계산할 때.

**실행 결과** (`Ex.java` — 52-b, 17·21·25 동일)

```text
--- (3) ChronoUnit.between 은 버림이다
  t1 : 2026-01-31T10:00   t2 : 2026-03-01T15:30
  DAYS.between   : 29
  HOURS.between  : 701
  MONTHS.between : 1   (1개월 하고 며칠이지만 1)
  Duration.between.toDays : 29
  방향을 뒤집으면 : -29
```

```text
  2026-01-31 10:00  ------------------------>  2026-03-01 15:30

  실제 간격 = 29일 5시간 30분 = 701.5 시간

  DAYS.between   29       <- 29일 + 5시간 30분에서 소수부를 버린다
  HOURS.between  701      <- 701시간 + 30분에서 버린다
  MONTHS.between 1        <- 1개월 + 1일 5시간 30분에서 버린다

  전부 0 쪽으로 버린다. 뒤집으면 -29 (내림이 아니라 0 방향 절사다).
```

그림 해설 (한 단계씩):

- **소수부를 0 쪽으로 버린다.** 29.23일이 29 가 되고, −29.23일이 −29 가 된다.
- `Duration.between(...).toDays()` 도 같은 값을 낸다.
- "30일 지나면 만료"를 `DAYS.between >= 30` 으로 쓰면 **29일 23시간 59분은 아직 아니다.** 의도와 맞는지 확인해야 한다.

비용 — 버림이 의도와 다르면 하루가 틀린다. **경계가 중요하면 `LocalDate` 로 잘라서** 세는 쪽이 헷갈리지 않는다.

### (6) `Duration` 과 `Period` 는 섞이지 않는다

**언제 쓰나** — "1개월 1일 3시간" 같은 복합 간격을 다룰 때.

**컴파일 에러부터 만난다** (`Ex.java` — 52-c, 17·21·25 동일).

```java
Duration d = Duration.ofHours(1).plus(Period.ofDays(1));
```

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

```text
  Duration.plus 의 시그니처          Period.plus 의 시그니처

  plus(Duration other)               plus(TemporalAmount amountToAdd)
        ^                                  ^
  Duration 만 받는다                 아무 TemporalAmount 나 받는다
        |                                  |
  Period 를 넣으면                   Period 를 넣으면 런타임에
  컴파일 에러                        단위를 보고 거부한다
                                     "Unit must be Years, Months or Days, but was Seconds"
```

그림 해설 (한 단계씩):

- 한쪽은 **컴파일 타임**, 다른 쪽은 **런타임**에 막는다. 같은 실수인데 잡히는 시점이 다르다.
- `LocalDate.plus(Duration.ofDays(1))` 은 **`Duration` 이 초 단위라서** 거부된다 — 메시지가 `Unsupported unit: Seconds` 다.
- **`Duration.ofDays(1)` 조차 속은 "86,400초"** 라는 것이 이 메시지에 드러난다.
- 복합 간격이 필요하면 **두 값을 따로 들고** 순서대로 더한다.

```java
zdt.plus(Period.ofMonths(1)).plus(Duration.ofHours(3));   // 순서가 의미를 바꾼다
```

비용 — 타입 안전을 얻는 대신 복합 간격을 한 값으로 못 든다.

### (7) 내부 단위가 다르다

**언제 쓰나** — `toString` 결과가 예상과 다를 때. 두 값을 비교할 때.

**실행 결과** (`Ex.java` — 52-a, 17·21·25 동일)

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
```

```text
  Duration 이 실제로 들고 있는 것      Period 가 실제로 들고 있는 것

  +-------------------+                +----------------------+
  | seconds : long    |                | years  : int         |
  | nanos   : int     |                | months : int         |
  +-------------------+                | days   : int         |
        두 칸                          +----------------------+
                                              세 칸

  ofDays(1)  -> seconds 86400          ofDays(1)  -> days 1
  toString   -> "PT24H"                toString   -> "P1D"
                  ^                                    ^
            일 단위가 없어 시간으로 적는다        날 단위가 그대로 남는다
```

그림 해설 (한 단계씩):

- `Duration.ofDays(1).toString()` 이 **`P1D` 가 아니라 `PT24H`** 다. 일 단위를 저장하지 않기 때문이다.
- `Duration.ofHours(25)` 도 **`PT25H`** 다. "1일 1시간"으로 올려 적지 않는다.
- `Period.ofWeeks(2)` 는 **`P14D`** 다. 주는 저장 단위가 아니라 날로 환산된다.
- `Period.ofMonths(1).getDays()` 는 **0** 이다 — 월과 일은 **서로 환산되지 않는다.** 한 달이 며칠인지 모르기 때문이다.

비용 — `toString` 을 그대로 로그·DB 에 넣으면 **읽는 쪽이 단위를 오해**할 수 있다. `toDaysPart()`/`toHoursPart()` 로 쪼개 적는다.

### (8) `Period` 는 정규화되지 않는다

**언제 쓰나** — `Period.between` 결과를 비교하거나 저장할 때.

**실행 결과** (`Ex.java` — 52-a, 17·21·25 동일)

```text
--- (7) Period 는 정규화되지 않는다
  Period.between(1/31, 3/1) : P1M1D
  toTotalMonths             : 1
  getDays                   : 1
  Period.of(0,13,0)         : P13M -> normalized P1Y1M
  ChronoUnit.DAYS.between(1/31, 3/1) : 29
```

```text
  2026-01-31 에서 2026-03-01 까지

  Period.between  ->  P1M1D   "1개월 1일"
       |
       +-- 1/31 + 1개월 = 2/28 (말일로 잘림)
       +-- 2/28 + 1일   = 3/1
                              실제로는 29일이다

  ChronoUnit.DAYS.between -> 29

  P1M1D 와 29일은 같은 구간의 두 표현이고,
  "P1M1D 를 다른 날짜에 더하면 29일이 아닐 수 있다."
```

그림 해설 (한 단계씩):

- `P1M1D` 를 **다른 출발점에 더하면 결과 일수가 달라진다.** `Period` 는 **구간이 아니라 규칙**이다.
- `Period.of(0, 13, 0)` 은 `P13M` 으로 그대로 남는다. **`normalized()` 를 불러야** `P1Y1M` 이 된다.
- `normalized()` 는 **년↔월만** 정리한다. 일은 건드리지 않는다 — 한 달이 며칠인지 모르기 때문이다.
- 두 `Period` 의 `equals` 는 **필드 비교**다. `P1M` 과 `P30D` 는 같지 않고, `P13M` 과 `P1Y1M` 도 같지 않다.

비용 — `Period` 를 저장·비교하는 코드는 **정규화 규칙을 스스로 정해야** 한다.

### (9) `YYYY` 대 `yyyy` — 연말에 1년이 틀린다

**언제 쓰나** — 날짜 패턴을 손으로 쓸 때. 로그 파일명·파티션 키를 만들 때.

**실행 결과** (`Ex.java` — 52-d, 17·21·25 동일, `Locale.ENGLISH`)

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

```text
  2025년 12월 달력 끝부분 (주가 일요일에 시작한다고 볼 때)

   일   월   화   수   목   금   토
   21   22   23   24   25   26   27     <- 2025년의 마지막 완전한 주
  ----+----+----+----+----+----+----
   28   29   30   31 |  1    2    3     <- 이 주는 1월을 품는다
   ^^^^^^^^^^^^^^^^^ |
   "2026년의 첫 주"  | 여기서 해가 바뀐다

  yyyy 는 달력의 해를 본다  -> 2025
  YYYY 는 "이 날이 속한 주"의 해를 본다 -> 2026
```

그림 해설 (한 단계씩):

- **12월 28일부터 31일까지 나흘이 `YYYY=2026`** 이 됐다. 하루도 아니고 나흘이다.
- 그 나흘은 **"2026년의 첫 주"에 속한 2025년 날짜**다. 주 기반 연도는 주를 쪼개지 않으므로 이렇게 된다.
- 1월 1일부터는 다시 같아진다 — **틀리는 구간이 연말에만** 있다.

**다른 해도 같다** (`Ex.java` — 52-d)

```text
--- (2) 다른 해의 경계도 훑는다
  2019-12-29 (SUNDAY) yyyy=2019-12-29 YYYY=2020-12-29
  2019-12-30 (MONDAY) yyyy=2019-12-30 YYYY=2020-12-30
  2019-12-31 (TUESDAY) yyyy=2019-12-31 YYYY=2020-12-31
  2020-12-28 (MONDAY) yyyy=2020-12-28 YYYY=2021-12-28
  2020-12-29 (TUESDAY) yyyy=2020-12-29 YYYY=2021-12-29
  2020-12-30 (WEDNESDAY) yyyy=2020-12-30 YYYY=2021-12-30
  2020-12-31 (THURSDAY) yyyy=2020-12-31 YYYY=2021-12-31
  2021-12-28 (TUESDAY) yyyy=2021-12-28 YYYY=2022-12-28
  2021-12-29 (WEDNESDAY) yyyy=2021-12-29 YYYY=2022-12-29
  2021-12-30 (THURSDAY) yyyy=2021-12-30 YYYY=2022-12-30
  2021-12-31 (FRIDAY) yyyy=2021-12-31 YYYY=2022-12-31
  2024-12-29 (SUNDAY) yyyy=2024-12-29 YYYY=2025-12-29
  2024-12-30 (MONDAY) yyyy=2024-12-30 YYYY=2025-12-30
  2024-12-31 (TUESDAY) yyyy=2024-12-31 YYYY=2025-12-31
  2026-12-28 (MONDAY) yyyy=2026-12-28 YYYY=2027-12-28
  2026-12-29 (TUESDAY) yyyy=2026-12-29 YYYY=2027-12-29
  2026-12-30 (WEDNESDAY) yyyy=2026-12-30 YYYY=2027-12-30
  2026-12-31 (THURSDAY) yyyy=2026-12-31 YYYY=2027-12-31
  2027-12-28 (TUESDAY) yyyy=2027-12-28 YYYY=2028-12-28
  2027-12-29 (WEDNESDAY) yyyy=2027-12-29 YYYY=2028-12-29
  2027-12-30 (THURSDAY) yyyy=2027-12-30 YYYY=2028-12-30
  2027-12-31 (FRIDAY) yyyy=2027-12-31 YYYY=2028-12-31
```

- 훑은 여섯 해 **전부**에서 12월 말 며칠이 어긋났다. 이 문서가 훑은 범위(2019·2020·2021·2024·2026·2027 의 12월 28~31일과 1월 1~4일)에서는 **1월 쪽에서는 한 건도 안 나왔다.**
- 그러니 **"연말에만 틀린다"가 이 실측 범위에서의 관찰**이다. 모든 해·모든 Locale 에 대한 증명은 아니다.

**로그 파일명이 어떻게 되나** (`Ex.java` — 52-f, 기본 `Locale` `ko_KR`, 17·21·25 동일)

```text
기본 Locale : ko_KR
--- 기본 Locale 로 (ofPattern 에 Locale 을 안 주면)
  yyyy-MM-dd : 2025-12-28
  YYYY-MM-dd : 2026-12-28
--- 로그 파일명으로 쓰면 어떻게 되나 (2025-12-25 ~ 2026-01-02)
  app-2025-12-25.log   (실제 날짜 2025-12-25)
  app-2025-12-26.log   (실제 날짜 2025-12-26)
  app-2025-12-27.log   (실제 날짜 2025-12-27)
  app-2026-12-28.log   (실제 날짜 2025-12-28)
  app-2026-12-29.log   (실제 날짜 2025-12-29)
  app-2026-12-30.log   (실제 날짜 2025-12-30)
  app-2026-12-31.log   (실제 날짜 2025-12-31)
  app-2026-01-01.log   (실제 날짜 2026-01-01)
  app-2026-01-02.log   (실제 날짜 2026-01-02)
```

```text
  날짜순으로 나열된 파일들을 이름순으로 정렬하면

  app-2025-12-25.log
  app-2025-12-26.log
  app-2025-12-27.log
  app-2026-01-01.log   <- 1월 1일이 12월 28일보다 앞에 온다
  app-2026-01-02.log
  app-2026-12-28.log   <- 실제로는 2025년 12월 28일
  app-2026-12-31.log
       ^^^^
  나흘치가 1년 뒤로 밀려 파일 목록의 끝으로 간다
```

그림 해설 (한 단계씩):

- **파일명이 1년 미래로 간다.** 로테이션·삭제 정책이 그 파일들을 못 찾는다.
- 이름순 정렬이 **날짜순과 어긋난다.** 나흘치가 목록 끝으로 밀린다.
- 기본 `Locale` 이 `ko_KR` 일 때도 똑같이 일어났다 — `Locale` 을 안 줘도 안전하지 않다.

비용 — **이 버그는 1년에 나흘만 재현된다.** 그래서 테스트를 안 짜면 배포 후 연말에 발견된다.

### (10) `YYYY` 는 `Locale` 에 또 한 번 달렸다

**언제 쓰나** — `YYYY` 를 의도적으로 쓸 때(ISO 주 번호가 필요할 때).

**실행 결과** (`Ex.java` — 52-d, 17·21·25 동일)

```text
--- (3) 같은 YYYY 가 Locale 에 따라 또 달라진다 — 2026-12-27(일)
  날짜/요일 : 2026-12-27 SUNDAY
  en       YYYY=2027  firstDayOfWeek=SUNDAY  minimalDays=1  주=1
  en_US    YYYY=2027  firstDayOfWeek=SUNDAY  minimalDays=1  주=1
  fr_FR    YYYY=2026  firstDayOfWeek=MONDAY  minimalDays=4  주=52
  ko_KR    YYYY=2027  firstDayOfWeek=SUNDAY  minimalDays=1  주=1
  ISO 기준 weekBasedYear : 2026  주 52
```

```text
  2026-12-27 (일요일) 은 몇 년 몇 주인가

  en / en_US / ko_KR             fr_FR (= ISO 8601)
  주 시작 = 일요일                 주 시작 = 월요일
  첫 주의 최소 일수 = 1            첫 주의 최소 일수 = 4
        |                               |
  12/27 은 새 주의 시작             12/27 은 아직 지난 주의 끝
        |                               |
  2027년 1주                       2026년 52주
   YYYY = 2027                      YYYY = 2026
```

그림 해설 (한 단계씩):

- **같은 날, 같은 패턴, 다른 답**이다. `Locale` 이 주의 시작 요일과 첫 주의 정의를 바꾼다.
- `DateTimeFormatterBuilder` 의 소스 주석이 그 이유를 적는다.

  > `Y..Y 4..n append special localized WeekFields element for numeric week-based-year`

  **`localized`** 라는 단어가 핵심이다.
- **ISO 8601 의 주 기반 연도**를 원하면 `Locale` 에 기대지 말고 `IsoFields.WEEK_BASED_YEAR` 를 직접 쓴다.

비용 — `ofPattern` 에 `Locale` 을 안 주면 **실행 환경의 기본 `Locale`** 이 쓰인다. 서버 설정이 바뀌면 답이 바뀐다.

## 문법 — 형태와 규칙

### 패턴 글자 — 비슷하게 생긴 것들

**실행 결과** (`Ex.java` — 52-d, 대상은 `2026-03-08T16:05:09+09:00[Asia/Seoul]`, `Locale.ENGLISH`, 17·21·25 동일)

```text
--- (4) 패턴 글자 — 비슷하게 생긴 것들
  yyyy       연(달력 기준)               -> 2026
  YYYY       주 기반 연                 -> 2026
  uuuu       연(ISO proleptic)       -> 2026
  MM         월                      -> 03
  mm         분                      -> 05
  MMM        월 이름 짧게                -> Mar
  MMMM       월 이름 길게                -> March
  dd         일                      -> 08
  DD         그 해의 몇 번째 날            -> 67
  EEE        요일                     -> Sun
  hh         12시간제 시                -> 04
  HH         24시간제 시                -> 16
  a          오전/오후                  -> PM
  ss         초                      -> 09
  SSS        밀리초                    -> 000
  nnnnnnnnn  나노                     -> 000000000
  z          시간대 이름                 -> KST
  zzzz       시간대 이름 길게              -> Korean Standard Time
  Z          오프셋 +0900              -> +0900
  XXX        오프셋 +09:00             -> +09:00
  VV         지역 ID                  -> Asia/Seoul
```

| 헷갈리는 짝 | 큰 글자 | 작은 글자 | 언제 드러나나 |
|---|---|---|---|
| `Y` / `y` | **주 기반 연** | 달력 연 | **연말 나흘** |
| `M` / `m` | 월 | **분** | 언제나(값이 전혀 다르다) |
| `D` / `d` | **그 해 몇 번째 날** | 일 | 1월 10일 이후 |
| `H` / `h` | 24시간제 | **12시간제** | 오후(13시 이후) |
| `u` / `y` | proleptic 연(음수 가능) | 연호 기준 연 | 기원전, `STRICT` 파싱 |
| `Z` / `z` / `X` / `V` | 오프셋(`+0900`) | 이름(`KST`) | 오프셋(`+09:00`) / 지역 ID |

javadoc 의 패턴 표에서 그대로 온다.

> ```text
> u       year                        year    2004; 04
> y       year-of-era                 year    2004; 04
> D       day-of-year                 number  189
> d       day-of-month                number  10
> Y       week-based-year             year    1996; 96
> w       week-of-week-based-year     number  27
> ```

**`M`/`m` 과 `H`/`h` 의 실측**

```text
--- (5) hh 와 HH — 오후 4시를 12시간제로 찍으면
  HH:mm : 16:05
  hh:mm : 04:05   (a 가 없으면 오전/오후가 사라진다)
  hh:mm a : 04:05 PM
  MM/dd vs mm/DD : 03/08 vs 05/67
```

- `hh:mm` 만 쓰면 **오후 4시가 "04:05"** 로 나온다 — 오전인지 오후인지 알 수 없다.
- `mm/DD` 는 "05/67" — **분과 그 해 67번째 날**이다. 날짜처럼 보이는 자리에 전혀 다른 값이 들어간다.

### `yyyy` 대 `uuuu`

**실행 결과** (`Ex.java` — 52-d, 17·21·25 동일)

```text
--- (6) yyyy 대 uuuu — 기원전에서 갈린다
  LocalDate.of(-1, 6, 15) : -0001-06-15
  yyyy : 0002 BC
  uuuu : -0001
  yyyy 만 쓰고 G 없이 파싱 : 0001-06-15
```

- `yyyy` 는 **연호 기준 연(year-of-era)** 이다. 기원전 1년이 "2 BC" 로 나온다.
- `uuuu` 는 **proleptic year** 다. 음수를 그대로 적는다.
- `yyyy` 만 쓰고 연호(`G`)를 안 쓰면 **기원전인지 아닌지 알 수 없다.**
- 그래서 `STRICT` 파싱에서 `yyyy` 가 거부된다(다음 항).

### 파싱 엄격도 — `ResolverStyle`

**실행 결과** (`Ex.java` — 52-d, `Locale.ENGLISH`)

```text
--- (8) 파싱 엄격도 — ResolverStyle
  STRICT 로 2026-02-30 : java.time.format.DateTimeParseException: Text '2026-02-30' could not be parsed: Invalid date 'FEBRUARY 30'
  SMART 로 2026-02-30 : 2026-02-28
  LENIENT 로 2026-02-30 : 2026-03-02
  STRICT + yyyy 로 2026-03-08 : java.time.format.DateTimeParseException: Text '2026-03-08' could not be parsed: Unable to obtain LocalDate from TemporalAccessor: {DayOfMonth=8, MonthOfYear=3, YearOfEra=2026},ISO of type java.time.format.Parsed
                                                                                                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                                                                                                 ★ 이 나열 순서가 17·21·25 에서 전부 달랐다
```

```text
  "2026-02-30" 을 세 가지 엄격도로 파싱

  STRICT   -> 거부한다 (2월 30일은 없다)
  SMART    -> 2026-02-28 로 자른다   <- 기본값이다
  LENIENT  -> 2026-03-02 로 넘긴다 (30 - 28 = 2일을 3월로)
```

- **기본값은 `SMART`** 다. 아무 설정 없이 `ofPattern(...)` 을 쓰면 2월 30일이 2월 28일이 된다.
- `STRICT` 를 쓰면 `yyyy` 가 **거부된다** — 연호 없이는 연도를 확정할 수 없기 때문이다. `STRICT` 에는 **`uuuu`** 를 쓴다.
- 이 규칙은 실수하기 쉽다: "엄격하게 하려고 `STRICT` 를 켰더니 멀쩡한 날짜가 안 파싱된다."

### 이미 만들어진 포매터

```java
DateTimeFormatter.ISO_LOCAL_DATE        // 2026-03-08
DateTimeFormatter.ISO_LOCAL_DATE_TIME   // 2026-03-08T16:30:00
DateTimeFormatter.ISO_OFFSET_DATE_TIME  // 2026-03-08T16:30:00+09:00
DateTimeFormatter.ISO_INSTANT           // 2026-03-08T07:30:00Z
DateTimeFormatter.ISO_ZONED_DATE_TIME   // 2026-03-08T16:30:00+09:00[Asia/Seoul]
DateTimeFormatter.ISO_WEEK_DATE         // 2026-W11-7
DateTimeFormatter.BASIC_ISO_DATE        // 20260308
```

- **패턴을 손으로 쓸 이유가 없으면 쓰지 않는다.** 상수를 쓰면 (9)의 함정을 만날 일이 없다.
- 이 상수들은 **`Locale` 에 독립**이다(숫자만 쓰므로).

### `Duration` · `Period` 의 파싱

**실행 결과** (`Ex.java` — 52-b, 17·21·25 동일)

```text
--- (5) Duration 파싱과 Period 파싱은 문법이 다르다
Duration.parse("PT1H30M") : PT1H30M
Duration.parse("P1D")      : PT24H
Duration.parse("P1M")      : java.time.format.DateTimeParseException: Text cannot be parsed to a Duration
Period.parse("P1Y2M3D")    : P1Y2M3D
Period.parse("PT1H")       : java.time.format.DateTimeParseException: Text cannot be parsed to a Period
Period.parse("P1D")        : P1D
--- (6) 같은 문자열 P1M 이 두 타입에서 다른 뜻
  Period.parse("P1M")   : P1M   (1개월)
  Duration.parse("PT1M") : PT1M   (1분)
```

```text
  ISO-8601 기간 문자열

  P  1Y 2M 3D  T  4H 5M 6S
  ^            ^
  날짜 부분     시간 부분 (T 뒤)
      |            |
  Period 가 읽는다  Duration 이 읽는다

  T 앞의 M = 개월        T 뒤의 M = 분
  같은 글자, 다른 뜻 — 구분자는 T 하나뿐이다.
```

- **`Duration.parse("P1D")` 는 된다** — `PT24H` 로 바뀐다. 날짜 부분의 D 만 예외적으로 받는다.
- `Duration.parse("P1M")` 은 거부한다 — 한 달의 길이를 모르기 때문이다.
- 예외 메시지가 **`Text cannot be parsed to a Duration`** 으로 매우 짧다. 어디가 틀렸는지 안 알려준다.

## 어디서 틀리나

### 1. `plusDays` 와 `plusHours(24)` 를 같다고 생각한다

- (1)·(2)에서 본 것이다. 서머타임이 있는 지역에서 **한 시간 어긋난다.**
- 예외도 경고도 없다. 국내 테스트에서는 **차이가 안 보인다**((3)).
- 방어: **"벽시계 기준"이면 `plusDays`, "경과 시간 기준"이면 `plusHours`/`Duration`** 이라고 코드 주석이 아니라 **타입**으로 적는다.

### 2. `Duration` 을 `LocalDate` 에 더한다

```text
d1.plus(Duration.ofDays(1))  : java.time.temporal.UnsupportedTemporalTypeException: Unsupported unit: Seconds
```

- 메시지가 **`Unsupported unit: Seconds`** 다. `ofDays(1)` 인데 `Seconds` 라고 나온다.
- `Duration` 이 속으로 초만 들고 있기 때문이다((7)).
- 방어: `LocalDate` 에는 **`Period`** 를, `Instant` 에는 **`Duration`** 을. `ZonedDateTime` 은 둘 다 받되 뜻이 다르다.

### 3. `Period` 의 필드를 총량이라고 읽는다

```java
Period p = Period.between(LocalDate.of(2026,1,31), LocalDate.of(2026,3,1));
p.getDays();          // 1 — "총 1일"이 아니다
p.toTotalMonths();    // 1
ChronoUnit.DAYS.between(...);  // 29 — 이쪽이 총량이다
```

- `P1M1D` 의 `getDays()` 는 **"나머지 1일"** 이지 총 일수가 아니다.
- 총 일수를 원하면 **`ChronoUnit.DAYS.between`** 을 쓴다.
- `Period.getDays()` 로 "며칠 지났나"를 계산하는 코드는 **한 달을 통째로 잃는다.**

### 4. `YYYY` 를 쓴다

- (9)에서 본 것이다. **연말 나흘이 1년 미래로 간다.**
- 파일명·파티션 키·리포트 제목·캐시 키에 들어가면 **1년에 나흘만 재현되는 버그**가 된다.
- 방어: **`yyyy` 가 기본이다.** `YYYY` 는 "ISO 주 번호와 짝지어 쓸 때"에만, 그리고 그때도 `Locale` 을 명시한다((10)).
- 더 나은 방어: **`DateTimeFormatter.ISO_LOCAL_DATE` 같은 상수를 쓴다.**

### 5. 타입에 없는 필드를 포매터가 요구한다

**실행 결과** (`Ex.java` — 52-d, 17·21·25 동일)

```text
--- (7) 타입에 없는 필드를 찍으려 하면
LocalDate.format(ISO_DATE_TIME)  : java.time.temporal.UnsupportedTemporalTypeException: Unsupported field: HourOfDay
LocalDateTime.format(ISO_INSTANT) : java.time.temporal.UnsupportedTemporalTypeException: Unsupported field: InstantSeconds
Instant.format(...)              : 컴파일 에러 — Instant 에는 format 메서드가 없다 (Ex.java 52-e)
ISO_LOCAL_DATE.format(Instant)    : java.time.temporal.UnsupportedTemporalTypeException: Unsupported field: Year
Instant + zone 붙인 formatter     : 2026-03-08
ISO_INSTANT.withZone 으로 Instant : 2026-03-08 16:30
```

```text
Ex.java:6: error: cannot find symbol
        String s = Instant.parse("2026-03-08T07:30:00Z").format(DateTimeFormatter.ISO_LOCAL_DATE);
                                                        ^
  symbol:   method format(DateTimeFormatter)
  location: class Instant
1 error
```

- **`Instant` 에는 `format` 메서드가 아예 없다.** 컴파일에서 막힌다.
- 우회해서 `formatter.format(instant)` 로 부르면 **런타임에** `Unsupported field: Year` 가 난다.
- 해법은 둘이다 — `instant.atZone(zone)` 을 붙이거나, **`formatter.withZone(zone)`** 을 쓴다.
- 방어: **포매터와 대상 타입을 짝지어 고정한다.**

### 6. `SimpleDateFormat` 을 필드에 둔다

```java
// 위험 — SimpleDateFormat 은 스레드 안전하지 않다
private static final SimpleDateFormat SDF = new SimpleDateFormat("yyyy-MM-dd");

// 안전 — DateTimeFormatter 는 불변이다
private static final DateTimeFormatter DF = DateTimeFormatter.ofPattern("yyyy-MM-dd", Locale.ENGLISH);
```

- `DateTimeFormatter` 의 javadoc 이 "This class is immutable and thread-safe" 를 명시한다.
- 실측에서도 같은 인스턴스로 여러 값을 찍었다.

```text
--- (9) DateTimeFormatter 는 스레드 안전, SimpleDateFormat 은 아니다
  DateTimeFormatter 는 불변 — 같은 인스턴스를 재사용해도 된다(javadoc 명시)
  2026-01-01 / 2026-12-31
```

- **`SimpleDateFormat` 의 경쟁 조건은 이 문서에서 안 돌려 봤다** — 재현에 스레드·반복이 필요해 1분으로 끝나지 않는다. 여기서 보장하는 것은 `DateTimeFormatter` 쪽 javadoc 뿐이다.

### 7. `ofPattern` 에 `Locale` 을 안 준다

- (10)에서 본 것이다. `YYYY`·`MMM`·`EEE`·`a` 가 **기본 `Locale`** 에 따라 달라진다.
- 서버의 `-Duser.language` 설정이 바뀌면 **로그 형식이 조용히 바뀐다.**
- 방어: **기계가 읽을 문자열이면 `Locale.ENGLISH`(또는 `Locale.ROOT`) 를 명시**하고, 사람이 읽을 것만 사용자 `Locale` 을 쓴다.

### 8. `ChronoUnit.between` 의 버림을 잊는다

- (5)에서 본 것이다. 29일 5시간 30분이 **29** 다.
- "30일 무료 체험"을 `DAYS.between(가입, 지금) < 30` 으로 쓰면 **가입 30일째 5시간까지 무료**가 된다.
- 방어: 경계가 의미 있으면 **`LocalDate` 로 잘라서** 세거나, `isBefore(가입일.plusDays(30))` 처럼 **시각 비교**로 바꾼다.

## 구현 세부사항 대 언어 보장

### 예외 메시지가 세 판에서 전부 달랐다

**실행 결과** (`Ex.java` — 52-d 의 (8) 마지막 줄)

```text
JDK 17.0.13
  ... Unable to obtain LocalDate from TemporalAccessor: {YearOfEra=2026, MonthOfYear=3, DayOfMonth=8},ISO of type java.time.format.Parsed

JDK 21.0.5
  ... Unable to obtain LocalDate from TemporalAccessor: {DayOfMonth=8, MonthOfYear=3, YearOfEra=2026},ISO of type java.time.format.Parsed

JDK 25.0.1
  ... Unable to obtain LocalDate from TemporalAccessor: {DayOfMonth=8, YearOfEra=2026, MonthOfYear=3},ISO of type java.time.format.Parsed
```

```text
  같은 입력, 같은 예외 타입, 같은 문장 — 중괄호 안의 순서만 세 판이 전부 다르다

  17  YearOfEra, MonthOfYear, DayOfMonth
  21  DayOfMonth, MonthOfYear, YearOfEra
  25  DayOfMonth, YearOfEra, MonthOfYear
       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  파싱된 필드를 담은 Map 의 순회 순서다 — 정렬을 약속한 적이 없다
```

그림 해설 (한 단계씩):

- **예외 메시지를 파싱하거나 스냅샷 테스트로 고정하면 JDK 를 올릴 때마다 깨진다.**
- 46번에서 "메시지가 세 판에서 같았던 것은 운이지 계약이 아니다"라고 적었는데, **여기서 실제로 갈렸다.**
- 예외 **타입**(`DateTimeParseException`)은 javadoc 이 보장한다. 메시지는 아니다.

### 표

| 관측한 것 | 보장인가 | 근거 |
|---|---|---|
| `Duration` 이 초·나노만 들고 있다 | **보장** | javadoc — "a time-based amount of time ... in terms of seconds and nanoseconds" |
| `Period` 가 년·월·일만 들고 있다 | **보장** | javadoc — "a date-based amount of time ... years, months and days" |
| `Duration.ofDays(1)` = 86,400초 | **보장** | `Duration.ofDays` javadoc — "The seconds are calculated based on the standard definition of a day, where each day is 86400 seconds which implies a 24 hour day." |
| `ZonedDateTime.plusDays` 가 벽시계를 지킨다 | **보장** | javadoc — 날짜 필드를 더한 뒤 오프셋을 다시 구한다 |
| `Duration.plus(Period)` 가 컴파일 에러 | **보장** | 시그니처가 `plus(Duration)` 뿐이다 |
| `ChronoUnit.between` 이 완전한 단위만 센다 | **보장** | `TemporalUnit.between` javadoc — "The calculation returns a whole number, representing the number of **complete units** between the two temporals." |
| `ResolverStyle` 기본값이 `SMART` | **보장** | `DateTimeFormatter.ofPattern` javadoc |
| `Y` 가 `Locale` 에 의존한다 | **보장** | `DateTimeFormatterBuilder` 소스 — "append special **localized** WeekFields element" |
| `DateTimeFormatter` 가 불변·스레드 안전 | **보장** | javadoc 클래스 설명 |
| **`DateTimeParseException` 의 메시지 문구** | **보장 아님 — 세 판이 전부 달랐다** | 위 실측 |
| **특정 지역·날짜의 DST 전이** | **보장 아님 — tzdb 판에 달렸다** | [`../51-java-time-types/`](../51-java-time-types/) 13번 |
| `ko_KR` 의 `firstDayOfWeek` 가 일요일 | **보장 아님** | CLDR 데이터에서 온다. JDK 판·`-Djava.locale.providers` 에 따라 달라질 수 있다 |

**세 판에서 같았던 것**

- 52-a·52-b·52-f 는 **tzdb 줄 하나를 빼고 출력이 전부 같았다.**
- 52-d 는 **위 한 줄만 달랐다.**
- 52-c·52-e 의 컴파일 에러 메시지는 세 판이 같았다.
- **하지만 그것은 관찰이지 보장이 아니다.** 바로 위 한 줄이 반례다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 일 | 고를 것 | 왜 |
|---|---|---|
| 타임아웃·재시도 간격 | `Duration` | 기계 시간이다. 서머타임과 무관해야 한다 |
| 캐시 TTL | `Duration` | 같다 |
| "정확히 24시간 뒤 만료" | `Duration.ofDays(1)` 또는 `plusHours(24)` | 경과 시간이 계약이다 |
| "내일 같은 시각" | `Period.ofDays(1)` / `plusDays(1)` | 벽시계가 계약이다 |
| "한 달 무료 체험" | `Period.ofMonths(1)` | 달력 한 칸이다. 30일이 아니다 |
| 나이 계산 | `Period.between(생일, 오늘).getYears()` | 달력 기준이 맞다 |
| "며칠 지났나" | `ChronoUnit.DAYS.between` | 총량이 필요하다. `Period.getDays()` 가 아니다 |
| 두 로그 시각의 차이 | `Duration.between(instant1, instant2)` | |
| 사람에게 보여 줄 날짜 | `DateTimeFormatter.ofLocalizedDate(...)` + 사용자 `Locale` | |
| 기계가 읽을 날짜 | `DateTimeFormatter.ISO_LOCAL_DATE` 같은 상수 | 패턴을 손으로 안 쓰면 (9)의 함정이 없다 |
| 굳이 패턴을 써야 하면 | `ofPattern("yyyy-MM-dd", Locale.ENGLISH)` | `yyyy`·`Locale` 명시 |
| 엄격한 파싱 | `withResolverStyle(STRICT)` + **`uuuu`** | `STRICT` 는 `yyyy` 를 거부한다 |
| `Instant` 를 포맷 | `formatter.withZone(zone).format(instant)` | `Instant.format` 은 존재하지 않는다 |

판단 규칙 세 줄.

- **"초시계로 재나, 달력으로 세나"** — 앞이면 `Duration`, 뒤면 `Period`.
- **"총량인가, 나머지인가"** — 총량이면 `ChronoUnit.between`, 구성 요소면 `Period` 의 필드.
- **패턴 문자열을 손으로 쓰기 전에 상수부터 찾는다.** 손으로 쓰면 `Y`·`m`·`D`·`h` 중 하나를 밟는다.

## 핵심 문장

- `Duration` 은 **초시계**(초·나노), `Period` 는 **달력**(년·월·일)이다 — `Duration.ofDays(1)` 의 `toString` 이 `PT24H` 인 것이 그 증거다.
- 서머타임이 있는 날 **`plusDays(1)` 과 `plusHours(24)` 가 한 시간 다르다.** 실측에서 봄은 23시간, 가을은 25시간이었다.
- **전이가 없는 지역에서는 그 차이가 안 보인다** — 서울에서만 테스트하면 통과한다.
- `ChronoUnit.between` 은 **0 방향으로 버린다.** 29일 5시간 30분이 29다.
- **`YYYY` 는 연말 나흘을 1년 미래로 보낸다.** 훑은 여섯 해 전부에서 12월 28~31일이 어긋났고, 값은 `Locale` 에 또 달렸다.

## 관련 자료

- [`../51-java-time-types/`](../51-java-time-types/) — **이 주제의 선행.** 그쪽은 **시각 한 점을 어느 타입으로 적나**까지, 여기는 **두 점 사이의 간격과 문자열 변환**부터
- [`../../../../../ops-patterns/17-timeseries/`](../../../../../ops-patterns/17-timeseries/) — 시계열 버킷·롤업. 그쪽은 **간격을 어떻게 접어 저장하나**까지, 여기는 **그 간격을 재는 API 표면**까지
- [`../../../../../../history/java/java-8.md`](../../../../../../history/java/java-8.md) — `java.time` 도입 맥락과 `SimpleDateFormat` 의 문제. 연혁은 거기
- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 52번)
- [**53번 주제**](../53-bigdecimal/)(`BigDecimal`) — 같은 「정밀도」 계열. 그쪽은 **스케일과 반올림**, 여기는 **시간 단위와 버림**
- [**35번 주제**](../35-string/)(`String`) — 포매팅 결과를 담는 타입
- [**37번 주제**](../37-regex/)(정규식) — 날짜 문자열을 정규식으로 검증하려는 유혹. `DateTimeFormatter.parse` 가 정본이다
- [**25번 주제**](../25-exceptions/)(예외) — `DateTimeParseException` 은 unchecked 다

## 용어 풀이

- **`Duration`** — 초와 나노로 표현한 **기계 시간 간격**. 예: `Duration.ofDays(1)` 은 `PT24H`(86,400초)다.
- **`Period`** — 년·월·일로 표현한 **달력 간격**. 예: `Period.ofDays(1)` 은 `P1D` 이고, 더하는 날짜에 따라 실제 초가 다르다.
- **`ChronoUnit`** — 단위의 열거형(`DAYS`·`MONTHS`·`SECONDS` …). `between` 으로 "몇 단위 떨어졌나"를 묻는다.
- **ISO-8601 기간 문자열** — `P1Y2M3DT4H5M6S` 형태. `T` 앞은 날짜, 뒤는 시간이다. 예: `T` 앞의 `M` 은 개월, 뒤의 `M` 은 분이다.
- **`DateTimeFormatter`** — 시각 값과 문자열을 오가는 불변·스레드 안전 객체. 상수로 두고 공유해도 된다.
- **패턴 글자(pattern letter)** — `yyyy`·`MM`·`dd` 처럼 양식지의 칸을 지정하는 문자. 대소문자가 다른 뜻이다.
- **주 기반 연도(week-based year)** — "이 날이 속한 주"가 어느 해의 주인지. 패턴 글자 `Y`. 예: 2025-12-28(일)이 2026년 1주에 들어가 `YYYY=2026` 이 된다.
- **`WeekFields`** — 주의 시작 요일과 첫 주의 최소 일수를 담은 규칙. `Locale` 마다 다르다. 예: 프랑스는 월요일·4일, 한국은 일요일·1일이다.
- **proleptic year** — 연호를 쓰지 않고 음수까지 이어 쓴 연도. 패턴 글자 `u`. 예: 기원전 1년이 `-0001` 이다.
- **year-of-era** — 연호(AD/BC) 안에서의 연도. 패턴 글자 `y`. 예: 기원전 1년이 `0002 BC` 다.
- **`ResolverStyle`** — 파싱 결과를 얼마나 엄격히 검증할지. `STRICT`·`SMART`(기본)·`LENIENT`. 예: 2월 30일을 각각 거부·2월 28일로 자름·3월 2일로 넘김.
- **버림(truncation toward zero)** — 소수부를 0 쪽으로 잘라내는 것. 예: 29.23일 → 29, −29.23일 → −29.
- **정규화(normalize)** — `Period` 의 월을 년으로 올려 정리하는 것. 예: `P13M` → `P1Y1M`. 일은 건드리지 않는다.

## 더 들어가면

- **`Period.between` 의 계산 순서가 `P1M1D` 를 만든다.**\
  `1/31 → 3/1` 에서 먼저 월을 세고(1개월, 도착 2/28), 남은 일을 센다(1일).\
  그래서 `P1M1D` 를 **다른 출발점**에 더하면 29일이 아닐 수 있다. `Period` 는 구간이 아니라 **규칙**이다.
- **`Duration` 에는 `toDays()` 와 `toDaysPart()` 가 따로 있다.**\
  `toDays()` 는 총 일수, `toDaysPart()` 는 "일 자리의 값"이다. `Duration.ofHours(25)` 에서 둘 다 1 이라 차이가 안 보이지만, `toHoursPart()` 가 1 인 반면 `toHours()` 는 25 다.\
  `*Part()` 계열은 **Java 9** 부터다(`src.zip` 확인).
- **`ISO_WEEK_DATE` 는 `Locale` 에 독립이다.**\
  `Y`·`w` 패턴 글자는 `Locale` 에 기대지만, `DateTimeFormatter.ISO_WEEK_DATE` 상수는 **ISO 8601 규칙에 고정**된다.\
  `IsoFields.WEEK_BASED_YEAR`·`IsoFields.WEEK_OF_WEEK_BASED_YEAR` 도 마찬가지다 — (10)에서 `fr_FR` 과 같은 답(2026, 52주)을 냈다.
- **`DateTimeFormatterBuilder` 로 더 세밀하게 만들 수 있다.**\
  `appendPattern`·`parseCaseInsensitive`·`parseDefaulting`·`optionalStart` 같은 조립 API 가 있다.\
  "초가 있을 수도 없을 수도 있는 형식"처럼 패턴 하나로 안 되는 것이 그 자리다. 이 문서는 조립 API 를 **안 돌려 봤다** — `ofPattern` 표면까지가 범위다.
- **`Duration` 의 최대 범위는 `long` 초다.**\
  약 292억 년이다. `Period` 는 세 필드가 각각 `int` 라 훨씬 좁고, `Period.ofDays(Integer.MAX_VALUE)` 를 `LocalDate` 에 더하면 넘친다.\
  넘침의 구체적 동작은 **안 돌려 봄**이다.
