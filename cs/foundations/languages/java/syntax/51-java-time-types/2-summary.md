# java/syntax/51 — `java.time` — `Instant`·`LocalDate`/`LocalDateTime`·`ZonedDateTime` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **선행** — 없다. 다만 간격·형식(`Duration`·`Period`·`DateTimeFormatter`)은 [`../52-duration-period-formatter/`](../52-duration-period-formatter/) 가 이어받는다.
> **기준 소스** — Temurin **JDK 21.0.5** 표준 라이브러리 소스 `java.base/java/time/Instant.java`·`LocalDate.java`·`LocalDateTime.java`·`ZonedDateTime.java`·`Clock.java`·`zone/ZoneRules.java`(`lib/src.zip`) · [`java.time` 패키지 javadoc (Java SE 21)](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/time/package-summary.html) · [`ZonedDateTime` javadoc (Java SE 21)](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/time/ZonedDateTime.html)
> **실행 검증** — 이 문서의 모든 출력은 실제로 돌려 얻은 것이다. 프로그램 다섯(51-a~51-e)을 **17.0.13 · 21.0.5 · 25.0.1** 에서 각각 돌렸다.\
> ★ **세 판의 출력이 전부 같지는 않았다.** `ZoneRulesProvider` 의 tzdb 판이 다르고, 그 때문에 **같은 코드가 다른 답**을 냈다(아래 「구현 세부사항 대 언어 보장」이 정본).
> **버전** — `Instant`·`LocalDate`·`LocalDateTime`·`ZonedDateTime`·`Clock` 전부 `src.zip` 의 **`@since 1.8`**.
> **측정 조건** — 이 머신의 기본 시간대는 `Asia/Seoul`, 기본 `Locale` 은 `ko_KR`, `file.encoding` 은 `UTF-8` 이다. 시간대에 의존하는 출력은 그 사실이 붙어 있다.
> **범위** — 시계열 데이터를 **버킷으로 접어 저장·조회하는 패턴**은 [`../../../../../ops-patterns/17-timeseries/`](../../../../../ops-patterns/17-timeseries/) 가 정본이다.\
> 그쪽은 **시간 축 위에 값을 어떻게 쌓고 굴리나**까지, 여기는 **그 축의 한 점을 Java 의 어느 타입으로 적나**까지다.\
> `java.time` 이 **왜 Java 8 에 들어왔나**(Joda-Time·`Calendar` 의 문제)는 [`../../../../../../history/java/java-8.md`](../../../../../../history/java/java-8.md) 가 정본이다.
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**세 타입은 "사진"·"메모"·"약속"이다.**

| 비유 | 실체 |
|---|---|
| **사진의 촬영 시각** — 지구 어디서 찍었든 하나의 순간 | `Instant` |
| **달력에 적은 메모** — "3월 8일 오후 4시 반"이라고만 쓴 쪽지 | `LocalDateTime` |
| 그 메모에서 **날짜만** 떼어 낸 것 | `LocalDate` |
| 그 메모에서 **시각만** 떼어 낸 것 | `LocalTime` |
| **"서울 시간으로 3월 8일 오후 4시 반"이라는 약속** | `ZonedDateTime` |
| 약속에 시간대 **이름 대신 숫자**만 적은 것 | `OffsetDateTime` |
| 시간대 규칙이 적힌 **세계 시각표** | `ZoneId` 와 그 뒤의 tzdb |
| 시각표가 **개정되는 것** | tzdata 판 갱신 |

- **사진은 한 장이다.** 서울에서 보든 뉴욕에서 보든 같은 순간이고, 숫자 하나(에포크 초)로 적힌다.
- **메모는 순간이 아니다.** "3월 8일 오후 4시 반"이라고만 적힌 쪽지는 **어느 지역인지 붙기 전까지** 언제인지 정해지지 않는다.
- **약속은 메모 + 지역이다.** 지역이 붙는 순간 비로소 사진 한 장으로 환산된다.
- 그래서 세 타입 사이의 변환은 **무엇을 보태고 무엇을 버리는지**가 전부다.

```text
  Instant                LocalDateTime            ZonedDateTime
  (기계 시각)             (사람이 읽는 값)           (둘 다)

  1772955000초           2026-03-08T16:30         2026-03-08T16:30+09:00[Asia/Seoul]
      |                        |                          |
  지역 없음                시간대 없음                  지역 있음
  어디서나 같다            지역마다 다른 순간            순간이 하나로 정해진다
      |                        |                          |
      +---- atZone(zone) ----> ? <--- toLocalDateTime ----+
      |                                                   |
      +<--------------- toInstant() ----------------------+
```

그림 해설:

- 왼쪽에서 오른쪽으로 갈 때는 **지역을 보태야** 한다(`atZone`).
- 오른쪽에서 왼쪽으로 갈 때는 **지역을 버린다**(`toLocalDateTime`) — 그 순간 순간이 아니게 된다.
- 가운데 `LocalDateTime` 만으로는 `Instant` 로 못 간다. **무엇이 빠졌는지가 타입에 적혀 있다.**

> **에포크(epoch)** — 1970-01-01T00:00:00Z 를 0으로 잡고 거기서 흐른 초를 세는 기준점.\
> 예: `Instant.parse("2026-03-08T07:30:00Z").getEpochSecond()` 는 `1772955000` 이다.

> **오프셋(offset)** — UTC 와의 시차. `+09:00` 처럼 숫자뿐이고 규칙이 없다.\
> 예: 서울은 늘 `+09:00` 이지만, 뉴욕은 계절에 따라 `-05:00` 과 `-04:00` 을 오간다.

> **시간대(time zone)** — 오프셋이 **언제 어떻게 바뀌는지의 규칙 묶음**. `Asia/Seoul`·`America/New_York` 같은 지역 ID 로 부른다.\
> 예: `America/New_York` 은 "3월 둘째 일요일 02:00 에 한 시간 앞당긴다"는 규칙을 들고 있다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. "언제"를 저장하려는데 **어느 타입**을 골라야 하나 — 무엇을 기준으로 가르나.
2. 시간대 규칙 때문에 **존재하지 않는 시각**을 만들면 무슨 일이 생기나 — 던지나, 조정되나.
3. `now()` 를 쓰는 코드를 **어떻게 테스트**하나.

## 동작 방식

### (1) 세 축 — 같은 순간을 세 가지로 본다

**언제 쓰나** — 필드 타입을 고를 때. API 응답 형식을 정할 때.

**실행 결과** (`Ex.java` — 51-a, 17·21·25 동일)

```text
--- (0) 기준 — 고정 시각 하나를 세 축으로 본다
Instant                        : 2026-03-08T07:30:00Z
epochSecond                    : 1772955000
Asia/Seoul 로 보면             : 2026-03-08T16:30+09:00[Asia/Seoul]
America/New_York 로 보면       : 2026-03-08T03:30-04:00[America/New_York]
UTC 로 보면                    : 2026-03-08T07:30Z
--- (1) 세 타입이 각각 무엇을 들고 있나
LocalDate      : 2026-03-08
LocalTime      : 16:30
LocalDateTime  : 2026-03-08T16:30
ZonedDateTime  : 2026-03-08T16:30+09:00[Asia/Seoul]
OffsetDateTime : 2026-03-08T16:30+09:00
Instant        : 2026-03-08T07:30:00Z
```

```text
  한 순간(에포크 초 1772955000)을 세 지역에서 본 모습

  UTC              2026-03-08 07:30 Z
  Asia/Seoul       2026-03-08 16:30 +09:00     같은 사진, 다른 액자
  America/New_York 2026-03-08 03:30 -04:00
                   ^^^^^^^^^^^^^^^^
                   날짜·시각·오프셋이 전부 다른데 순간은 하나다
```

그림 해설 (한 단계씩):

- `Instant` 의 `toString` 은 **항상 `Z`** 로 끝난다 — UTC 로만 적힌다.
- `atZone(...)` 을 붙이면 같은 순간이 **지역 달력 값**으로 번역된다.
- 뉴욕이 `-04:00` 인 것에 주목하라. 3월 8일은 이미 서머타임이 시작된 뒤다(아래 (3)).

비용 — `Instant` 는 `long` 둘(초·나노)이라 가볍다. `ZonedDateTime` 은 날짜·시각·오프셋·`ZoneId` 참조를 다 들고 있다.

### (2) `LocalDateTime` 은 순간이 아니다

**언제 쓰나** — "회의는 3월 8일 16시 30분"이라는 값을 DB 에 넣기 직전.

**실행 결과** (`Ex.java` — 51-a, 17·21·25 동일)

```text
--- (2) LocalDateTime 은 순간이 아니다 — 같은 값이 지역마다 다른 순간
Asia/Seoul         2026-03-08T16:30+09:00[Asia/Seoul]  ->  epochSecond 1772955000
Europe/Paris       2026-03-08T16:30+01:00[Europe/Paris]  ->  epochSecond 1772983800
America/New_York   2026-03-08T16:30-04:00[America/New_York]  ->  epochSecond 1773001800
UTC                2026-03-08T16:30Z[UTC]  ->  epochSecond 1772987400
```

```text
  LocalDateTime "2026-03-08T16:30" 하나를 네 지역에 붙였다

  Asia/Seoul        1772955000
  Europe/Paris      1772983800     차이 28800초 = 8시간
  UTC               1772987400     차이  3600초 = 1시간
  America/New_York  1773001800     차이 14400초 = 4시간
                    ^^^^^^^^^^
                    네 개가 전부 다른 순간이다
```

그림 해설 (한 단계씩):

- **같은 문자열이 네 개의 다른 순간**이 됐다. 가장 먼 둘의 차이는 46,800초(13시간)다.
- 그래서 `LocalDateTime` 으로 저장한 값은 **"어느 지역 기준인가"를 같이 저장하지 않으면 복원 불가**다.
- 반대로 그게 **필요한** 값도 있다 — 알람 "매일 07:00" 은 사용자가 어디로 이동하든 그 지역의 07:00 이어야 한다.

비용 — `LocalDateTime` 은 시간대 조회가 없어 싸고, 순서 비교도 단순하다. 대신 **순간의 의미가 없다.**

### (3) 존재하지 않는 시각 — 던지지 않고 조정된다

**언제 쓰나** — 서머타임이 있는 지역을 다룰 때. 예약·배치 시각을 사용자가 입력할 때.

**실행 결과** (`Ex.java` — 51-b, 17·21·25 동일 — tzdb 줄만 다르다)

```text
--- (1) 존재하지 않는 시각(갭) — 2026-03-08 02:30 America/New_York
  getValidOffsets : []  (개수 0)
  getTransition   : Transition[Gap at 2026-03-08T02:00-05:00 to -04:00]
  isGap / isOverlap : true / false
  duration          : PT1H
  atZone 결과     : 2026-03-08T03:30-04:00[America/New_York]   <- 던지지 않고 조정된다
  요청한 LocalDateTime : 2026-03-08T02:30
  실제 LocalDateTime   : 2026-03-08T03:30
  밀린 양              : PT1H
  ZonedDateTime.of(...) : 2026-03-08T03:30-04:00[America/New_York]
--- (3) 갭 앞뒤 1분 — 01:59 와 03:00 은 1분 차이다
  01:59 : 2026-03-08T01:59-05:00[America/New_York]
  +1분  : 2026-03-08T03:00-04:00[America/New_York]
  Duration.between : PT1M
```

```text
  America/New_York 의 2026-03-08 지역 시각 축

  01:58  01:59 | 03:00  03:01 ...
  -----------+ |
             | +------------
        -05:00 |  -04:00
               ^
      02:00 ~ 02:59 는 이 지역 달력에 존재하지 않는다

  atZone("02:30") 이 하는 일

    02:30  -->  [갭이다]  -->  갭 길이(1시간)만큼 앞으로 민다  -->  03:30
                                                                    ^
                                             예외가 아니라 조용히 다른 값이 된다
```

그림 해설 (한 단계씩):

- `getValidOffsets` 가 **빈 리스트**다 — 유효한 오프셋이 **0개**라는 것이 "존재하지 않는다"의 정의다.
- `atZone` 은 **예외를 던지지 않는다.** 갭 길이만큼 앞으로 민 값을 돌려준다.
- javadoc 이 그 규칙을 못박는다.

  > For Gaps, the general strategy is that if the local date-time falls in the middle of a Gap, then the resulting zoned date-time will have a local date-time **shifted forwards by the length of the Gap**, resulting in a date-time in the later offset, typically "summer" time.

- 01:59 에 1분을 더하면 **03:00** 이 된다. 지역 시각으로는 한 시간 뛰었지만 `Duration.between` 은 `PT1M` 이다.

**엄격하게 받으려면 `ofStrict` 를 쓴다.**

```text
--- (2) 같은 갭을 ofStrict 로 만들면
  ofStrict(-05:00) : java.time.DateTimeException: LocalDateTime '2026-03-08T02:30' does not exist in zone 'America/New_York' due to a gap in the local time-line, typically caused by daylight savings
  ofStrict(-04:00) : java.time.DateTimeException: LocalDateTime '2026-03-08T02:30' does not exist in zone 'America/New_York' due to a gap in the local time-line, typically caused by daylight savings
```

- **오프셋을 어느 쪽으로 주든 같은 메시지**다. 그 지역 시각 자체가 없기 때문이다.
- 즉 "사용자 입력을 거부하고 싶다"면 `atZone` 이 아니라 **`ofStrict` 또는 `getValidOffsets().isEmpty()` 검사**를 써야 한다.

비용 — `atZone` 은 조용히 성공한다(값이 달라질 뿐). `ofStrict` 는 시끄럽게 실패한다. **어느 쪽이 더 싼지는 도메인이 정한다.**

### (4) 두 번 있는 시각 — 중복 구간

**언제 쓰나** — 가을 전이가 있는 지역에서 로그·거래 시각을 읽을 때.

**실행 결과** (`Ex.java` — 51-b, 17·21·25 동일)

```text
--- (4) 두 번 있는 시각(중복) — 2026-11-01 01:30 America/New_York
  getValidOffsets : [-04:00, -05:00]  (개수 2)
  getTransition   : Transition[Overlap at 2026-11-01T02:00-04:00 to -05:00]
  isGap / isOverlap : false / true
  duration          : PT-1H
  atZone 기본        : 2026-11-01T01:30-04:00[America/New_York]   epochSecond 1793511000
  withEarlierOffset  : 2026-11-01T01:30-04:00[America/New_York]   epochSecond 1793511000
  withLaterOffset    : 2026-11-01T01:30-05:00[America/New_York]   epochSecond 1793514600
  두 순간의 차이     : PT1H
--- (5) 중복 구간에서 equals 와 isEqual
  toLocalDateTime 은 같다 : true
  equals  : false
  isEqual : false
```

```text
  America/New_York 2026-11-01 새벽

  실제 흐른 시간   00:30 ... 01:30(-04:00) ... 01:59 |시계를 되돌림| 01:00 ... 01:30(-05:00) ...
                                ^                                            ^
                             첫 번째 01:30                              두 번째 01:30
                          에포크 1793511000                          에포크 1793514600
                                        두 순간은 정확히 1시간 차이다

  "01:30" 이라고만 적힌 로그 한 줄은 둘 중 어느 것인지 알 수 없다.
```

그림 해설 (한 단계씩):

- `getValidOffsets` 가 **두 개**다 — 그것이 "두 번 있다"의 정의다.
- `atZone` 은 조용히 **앞쪽(`-04:00`)** 을 고른다. 이것도 예외가 아니다.
- `withEarlierOffsetAtOverlap`·`withLaterOffsetAtOverlap` 으로 **명시적으로** 고를 수 있다.
- 둘은 `toLocalDateTime` 이 같지만 **`equals` 도 `isEqual` 도 `false`** 다 — 서로 다른 순간이기 때문이다.
- `Transition` 의 `getDuration()` 이 **`PT-1H`(음수)** 다. 갭은 양수, 중복은 음수다.

비용 — 중복 구간의 데이터는 **저장할 때 오프셋을 같이 적지 않으면 복원 불가**다. `ZonedDateTime` 또는 `Instant` 로 저장해야 하는 이유다.

### (5) 한국에도 서머타임이 있었다

**언제 쓰나** — 오래된 데이터의 시각을 해석할 때. "우리나라는 DST 가 없으니 괜찮다"고 말하기 전에.

**실행 결과** (`Ex.java` — 51-b, 17·21·25 동일)

```text
--- (6) 한국에도 서머타임이 있었다 — 1988-05-08 02:00 Asia/Seoul
  getValidOffsets : []  (개수 0)
  getTransition   : Transition[Gap at 1988-05-08T02:00+09:00 to +10:00]
  isGap / isOverlap : true / false
  duration          : PT1H
  atZone : 1988-05-08T03:30+10:00[Asia/Seoul]
  getValidOffsets : [+10:00, +09:00]  (개수 2)
  getTransition   : Transition[Overlap at 1988-10-09T03:00+10:00 to +09:00]
  isGap / isOverlap : false / true
  duration          : PT-1H
  atZone : 1988-10-09T02:30+10:00[Asia/Seoul]
--- (7) 오늘의 서울에는 전이가 없다
  isFixedOffset : false
  NY isFixedOffset : false
  Seoul 다음 전이(2026-01-01 기준) : null
  NY 다음 전이(2026-01-01 기준)    : Transition[Gap at 2026-03-08T02:00-05:00 to -04:00]
```

```text
  Asia/Seoul 의 규칙                           America/New_York 의 규칙

  ... 1988년 여름: +10:00 (DST)               매년 3월·11월에 전이
  ... 1989년부터 : +09:00 고정                 nextTransition -> Gap at 2026-03-08
  nextTransition(2026) -> null                nextTransition -> 있다
       ^                                            ^
  "앞으로는 없다"                             "앞으로도 계속 있다"

  그런데 isFixedOffset 은 둘 다 false 다 — 과거에 전이가 있었기 때문이다.
```

그림 해설 (한 단계씩):

- **`Asia/Seoul` 의 1988-05-08 02:30 은 존재하지 않는 시각**이다. 뉴욕과 같은 갭이다.
- `isFixedOffset()` 이 `false` 라는 점이 함정이다 — "지금 고정"이 아니라 **"역사 전체가 고정"**을 묻는 메서드다.
- 미래만 보면 `nextTransition(2026-01-01)` 이 **`null`** 이다. 그것이 "지금은 DST 가 없다"의 올바른 판정이다.
- 1988년 데이터를 다루는 시스템에서 `Asia/Seoul` 을 `+09:00` 고정으로 처리하면 **여름 다섯 달이 한 시간씩 틀린다.**

비용 — 시간대 규칙은 **역사 전체**다. 오프셋 하나로 줄이면 언제나 어느 구간이 틀린다.

### (6) 불변이고 스레드 안전하다

**언제 쓰나** — 날짜 객체를 필드·상수로 둘 때. 여러 스레드가 공유할 때.

**실행 결과** (`Ex.java` — 51-a, 17·21·25 동일)

```text
--- (4) 불변이다 — plus 는 새 객체를 돌려준다
base        : 2026-01-31  (그대로다)
plusMonths(1): 2026-02-28  (2월 31일이 없어 말일로 잘린다)
plusMonths(1).plusMonths(1) : 2026-03-28
plusMonths(2)               : 2026-03-31
base == plus1 ?             : false
```

```text
  1월 31일에서 출발

  +1개월 -> 2월 31일? 없다 -> 2월 28일로 자른다
      |
      +1개월 -> 3월 28일        <- 잘린 값에서 다시 더했다
                  |
  1월 31일 --------+
      |
      +2개월 -> 3월 31일        <- 한 번에 더했다

  a.plus(1).plus(1)  !=  a.plus(2)
```

그림 해설 (한 단계씩):

- `plus*` 는 **원본을 고치지 않는다.** `base` 는 끝까지 `2026-01-31` 이다.
- 존재하지 않는 날짜는 **말일로 잘린다**(예외가 아니다 — (3)의 갭과 같은 성격이다).
- 그 자르기 때문에 **달 단위 덧셈은 결합법칙이 안 선다.** `+1+1` 과 `+2` 가 3일 차이다.
- 이 성질은 [`../52-duration-period-formatter/`](../52-duration-period-formatter/) 의 `Period` 절에서 다시 나온다.

비용 — 불변이라 매 연산이 새 객체를 만든다. 대신 **락 없이 공유**할 수 있고 방어적 복사가 필요 없다.

### (7) `Clock` 주입 — `now()` 를 테스트 가능하게

**언제 쓰나** — "3일 뒤 만료" 같은 로직을 단위 테스트할 때.

**실행 결과** (`Ex.java` — 51-c, 17·21·25 동일)

```text
--- (3) Clock 주입 — now() 를 테스트 가능하게
  Instant.now(fixed)       : 2026-03-08T07:30:00Z
  LocalDate.now(fixed)     : 2026-03-08
  LocalDateTime.now(fixed) : 2026-03-08T16:30
  ZonedDateTime.now(fixed) : 2026-03-08T16:30+09:00[Asia/Seoul]
  두 번 불러도 같다        : true
--- (4) 같은 Clock 을 다른 지역으로 보면
  LocalDate.now(seoul clock) : 2026-03-08
  LocalDate.now(ny clock)    : 2026-03-08
  Instant 는 같다            : true
--- (5) Clock.offset / tick — 시간을 옮기고 거칠게 만든다
  offset(+1일)      : 2026-03-09T07:30:00Z
  tick(1분)         : 2026-03-08T07:30:00Z
  systemUTC 의 zone : Z
  systemDefaultZone : Asia/Seoul
--- (7) 기본 시간대에 의존하는 호출 — 무엇이 바뀌면 답이 바뀌나
  TimeZone.getDefault() : Asia/Seoul
  LocalDate.now(Clock.fixed(t, Asia/Seoul))       : 2026-03-09
  LocalDate.now(Clock.fixed(t, America/New_York)) : 2026-03-08
```

```text
  테스트하기 어려운 코드                    테스트 가능한 코드

  class Service {                          class Service {
    boolean expired(LocalDate due) {         private final Clock clock;
      return due.isBefore(                   boolean expired(LocalDate due) {
        LocalDate.now());  <- 시스템 시계       return due.isBefore(
    }                                            LocalDate.now(clock));  <- 주입된 시계
  }                                          }
                                           }
  "내일 만료" 테스트가                      Clock.fixed(...) 를 넣으면
  자정에 깨진다                             언제 돌려도 같다
```

그림 해설 (한 단계씩):

- 모든 `now()` 에 **`Clock` 을 받는 오버로드**가 있다. 이것이 `java.time` 의 테스트 전략이다.
- `Clock.fixed` 는 **몇 번을 불러도 같은 값**이다 — 위에서 `true` 가 그 증거다.
- `Clock` 은 순간뿐 아니라 **지역도 들고 있다.** (7)에서 같은 순간이 두 지역에서 다른 **날짜**가 됐다(3/9 대 3/8).
- `Clock.offset(clock, Duration)` 으로 "하루 뒤"를, `Clock.tick(clock, Duration)` 으로 "분 단위로 뭉갠 시계"를 만든다.

비용 — 생성자에 인자가 하나 늘어난다. 그 대신 **시각에 의존하는 테스트가 결정적**이 된다.

## 문법 — 형태와 규칙

### 타입 지도 — 무엇을 들고 있나

| 타입 | 날짜 | 시각 | 오프셋 | 시간대 규칙 | 순간인가 | `toString` 예 |
|---|---|---|---|---|---|---|
| `Instant` | — | — | (UTC 고정) | — | **그렇다** | `2026-03-08T07:30:00Z` |
| `LocalDate` | 있다 | — | — | — | 아니다 | `2026-03-08` |
| `LocalTime` | — | 있다 | — | — | 아니다 | `16:30` |
| `LocalDateTime` | 있다 | 있다 | — | — | 아니다 | `2026-03-08T16:30` |
| `OffsetDateTime` | 있다 | 있다 | 있다 | — | **그렇다** | `2026-03-08T16:30+09:00` |
| `ZonedDateTime` | 있다 | 있다 | 있다 | 있다 | **그렇다** | `2026-03-08T16:30+09:00[Asia/Seoul]` |
| `Year`·`YearMonth`·`MonthDay` | 일부 | — | — | — | 아니다 | `2026`·`2026-03`·`--03-08` |

- **순간인가** 칸이 이 주제의 축이다. 아니면 지역을 보태야 순간이 된다.
- `OffsetDateTime` 은 순간이지만 **미래의 규칙 변경을 못 따라간다**(아래 「어디서 틀리나」 5).

### 서로 변환 — 무엇을 보태고 무엇을 버리나

**실행 결과** (`Ex.java` — 51-a, 17·21·25 동일)

```text
--- (5) 서로 변환 — 무엇을 보태야 하나
LocalDate  -> LocalDateTime : 2026-03-08T00:00
LocalDate  -> ZonedDateTime : 2026-03-08T00:00+09:00[Asia/Seoul]
LocalDateTime -> Instant    : 2026-03-08T07:30:00Z
LocalDateTime -> Instant(UTC): 2026-03-08T16:30:00Z
Instant -> LocalDate        : 2026-03-08
ZonedDateTime -> LocalDateTime(시간대를 버린다) : 2026-03-08T16:30
```

```java
// 보태기
localDate.atStartOfDay()                       // LocalDate -> LocalDateTime (00:00 을 보탠다)
localDate.atStartOfDay(zone)                   // LocalDate -> ZonedDateTime
localDateTime.atZone(zone)                     // LocalDateTime -> ZonedDateTime
localDateTime.toInstant(ZoneOffset.UTC)        // LocalDateTime -> Instant (오프셋을 보탠다)
instant.atZone(zone)                           // Instant -> ZonedDateTime

// 버리기
zonedDateTime.toInstant()                      // 지역 표현을 버린다
zonedDateTime.toLocalDateTime()                // 시간대를 버린다 (순간이 아니게 된다)
zonedDateTime.toLocalDate()                    // 시각도 버린다
LocalDate.ofInstant(instant, zone)             // 시각과 지역을 버린다 (9+)
```

- **`atStartOfDay()` 가 항상 00:00 은 아니다.** 그 지역 그 날짜의 자정이 갭이면 다른 시각이 나온다(아래 「더 들어가면」).

### 비교 — `equals` 와 `isEqual` 이 다르다

**실행 결과** (`Ex.java` — 51-a, 17·21·25 동일)

```text
--- (6) 비교 — equals 와 isEqual 이 다르다
seoul : 2026-03-08T16:30+09:00[Asia/Seoul]
ny    : 2026-03-08T03:30-04:00[America/New_York]
seoul.equals(ny)  : false
seoul.isEqual(ny) : true
seoul.toInstant().equals(ny.toInstant()) : true
compareTo : 1
```

| 물음 | 쓸 것 | 위 예의 답 |
|---|---|---|
| **같은 순간인가** | `isEqual` 또는 `toInstant().equals(...)` | `true` |
| **같은 값인가**(지역까지) | `equals` | `false` |
| 어느 쪽이 먼저인가 | `isBefore`/`isAfter` | — |
| 정렬 키로 | `compareTo` | `1` |

- **`compareTo` 가 `0` 이 아닌데 `isEqual` 은 `true`** 다. `ZonedDateTime.compareTo` 는 순간이 같으면 지역 값으로 2차 비교하기 때문이다.
- 그래서 **`TreeSet`·`SortedMap` 에 `ZonedDateTime` 을 넣으면 "같은 순간"이 두 원소로 들어간다.**
- 순간만 따지려면 **`Instant` 로 정규화해서** 넣는다.

### `Instant` 가 지원하는 것과 안 하는 것

**실행 결과** (`Ex.java` — 51-a, 17·21·25 동일)

```text
--- (3) Instant 는 지역 달력 필드를 모른다
t.getEpochSecond()  : 1772955000
t.get(INSTANT_SECONDS)    : java.time.temporal.UnsupportedTemporalTypeException: Unsupported field: InstantSeconds
t.getLong(INSTANT_SECONDS): 1772955000
t.get(YEAR)               : java.time.temporal.UnsupportedTemporalTypeException: Unsupported field: Year
2026
t.isSupported(ChronoField.YEAR)             : false
t.isSupported(ChronoField.INSTANT_SECONDS)  : true
t.isSupported(ChronoUnit.DAYS)              : true
t.isSupported(ChronoUnit.MONTHS)            : false
```

- **`get` 과 `getLong` 이 다르다.** `get` 은 `int` 를 돌려주므로 `INSTANT_SECONDS` 처럼 `int` 범위를 넘는 필드는 **지원해도 던진다.**
- `YEAR` 는 `isSupported` 가 `false` — **애초에 없는 개념**이다. `atZone` 을 붙인 뒤에야 `2026` 이 나온다.
- `ChronoUnit.DAYS` 는 지원한다. `Instant` 에게 하루는 **정확히 86,400초**다. javadoc 이 그렇게 적는다.

  > `DAYS` - Returns an `Instant` with the specified number of days added. This is equivalent to `plusSeconds(long)` with the amount multiplied by **86,400 (24 hours)**.

- `MONTHS`·`YEARS` 는 지원하지 않는다 — **길이가 달력에 달려 있어서**다.

## 어디서 틀리나

### 1. 이벤트 시각을 `LocalDateTime` 으로 저장한다

```java
class Order {
    private LocalDateTime createdAt;   // 위험하다
}
```

- 서버가 다른 지역으로 이전되거나, 컨테이너의 `TZ` 가 바뀌면 **과거 데이터의 의미가 바뀐다.**
- 같은 값이 지역마다 최대 26시간까지 다른 순간이다((2)).
- 방어: **과거에 일어난 일은 `Instant`**(또는 `TIMESTAMP WITH TIME ZONE`)로 저장한다.
- 반대로 **`LocalDateTime` 이 맞는 것**도 있다 — 생일, "매일 07:00 알람", 계약서에 적힌 날짜.

### 2. `Instant` 에 "하루"를 더한다

**실행 결과** (`Ex.java` — 51-d, 17·21·25 동일)

```text
--- (1) Instant 에 달력 단위를 더하면
t.plus(1, DAYS)      : 2026-03-09T07:30:00Z
t.plus(1, WEEKS)     : java.time.temporal.UnsupportedTemporalTypeException: Unsupported unit: Weeks
t.plus(1, MONTHS)    : java.time.temporal.UnsupportedTemporalTypeException: Unsupported unit: Months
t.plus(1, YEARS)     : java.time.temporal.UnsupportedTemporalTypeException: Unsupported unit: Years
t.plus(Period.ofDays(1))    : 2026-03-09T07:30:00Z
t.plus(Period.ofMonths(1))  : java.time.temporal.UnsupportedTemporalTypeException: Unsupported unit: Months
t.plus(Duration.ofDays(1))  : 2026-03-09T07:30:00Z
```

- `DAYS` 는 **되지만 뜻이 다르다** — `Instant` 에게 하루는 정확히 86,400초다. 서머타임이 있는 지역의 "하루"가 아니다.
- `WEEKS` 부터는 던진다. `Period.ofDays(1)` 은 되고 `Period.ofMonths(1)` 은 던진다.
- 방어: **지역 달력 기준으로 더해야 하면 `ZonedDateTime` 으로 바꿔서** 더하고 다시 `Instant` 로 돌아온다.

### 3. `Instant` 에서 연·월·일을 꺼내려 한다

**실행 결과** (`Ex.java` — 51-d, 17·21·25 동일)

```text
--- (2) Instant 에서 달력 필드를 꺼내면
t.getLong(YEAR)          : java.time.temporal.UnsupportedTemporalTypeException: Unsupported field: Year
t.getLong(DAY_OF_MONTH)  : java.time.temporal.UnsupportedTemporalTypeException: Unsupported field: DayOfMonth
t.with(YEAR, 2027)       : java.time.temporal.UnsupportedTemporalTypeException: Unsupported field: Year
t.truncatedTo(DAYS)      : 2026-03-08T00:00:00Z
t.truncatedTo(MONTHS)    : java.time.temporal.UnsupportedTemporalTypeException: Unit is too large to be used for truncation
--- (3) 타입을 잘못 변환하면
Instant.from(LocalDate)        : java.time.DateTimeException: Unable to obtain Instant from TemporalAccessor: 2026-03-08 of type java.time.LocalDate
Instant.from(LocalDateTime)    : java.time.DateTimeException: Unable to obtain Instant from TemporalAccessor: 2026-03-08T16:30 of type java.time.LocalDateTime
Instant.from(ZonedDateTime)    : 2026-03-08T07:30:00Z
LocalDate.from(Instant)        : java.time.DateTimeException: Unable to obtain LocalDate from TemporalAccessor: 2026-03-08T07:30:00Z of type java.time.Instant
LocalDateTime.ofInstant(t,zone) : 2026-03-08T16:30
```

- `Instant.from(LocalDate)` 는 **`DateTimeException`**(`UnsupportedTemporalTypeException` 이 아니다) — 메시지가 "Unable to obtain ... from TemporalAccessor" 다.
- `truncatedTo(DAYS)` 는 되지만 **UTC 기준 자정**이다. 서울 기준 자정이 아니다.
- 방어: **`from` 계열보다 `ofInstant`·`atZone` 처럼 지역을 명시하는 변환을 쓴다.** 타입 이름에 빠진 정보가 적혀 있다.

### 4. 시간대 ID 를 약어로 쓴다

**실행 결과** (`Ex.java` — 51-d, 17·21·25 동일)

```text
--- (5) 시간대 ID 가 틀리면
ZoneId.of("KST")          : java.time.zone.ZoneRulesException: Unknown time-zone ID: KST
ZoneId.of("Asia/Soul")    : java.time.zone.ZoneRulesException: Unknown time-zone ID: Asia/Soul
ZoneId.of("UTC+9")        : UTC+09:00
ZoneId.of("+09:00")       : +09:00
ZoneOffset.of("+09:00")   : +09:00
ZoneId.of("Asia/Seoul")   : Asia/Seoul
```

- **`"KST"` 는 없다.** `ZoneRulesException` 이 난다.
- 오타(`Asia/Soul`)도 **같은 예외·같은 형태의 메시지**다 — 약어와 오타를 구분할 수 없다.
- `"UTC+9"` 와 `"+09:00"` 은 **통과하지만 규칙이 없는 고정 오프셋**이 된다(다음 항).
- 방어: **IANA 지역 ID 를 상수로 두고** 문자열을 여기저기 쓰지 않는다.

### 5. `ZoneOffset` 을 `ZoneId` 대신 쓴다

**실행 결과** (`Ex.java` — 51-d, 17·21·25 동일)

```text
--- (7) ZoneOffset 만 붙이면 규칙이 없다 — 미래 날짜에서 어긋난다
  고정 오프셋 -05:00 : 2026-07-01T12:00-05:00  -> 2026-07-01T17:00:00Z
  규칙 있는 New_York : 2026-07-01T12:00-04:00[America/New_York]  -> 2026-07-01T16:00:00Z
  같은 순간인가      : false
```

```text
  "뉴욕 시간 7월 1일 12시"를 두 가지로 적었다

  ZoneOffset.ofHours(-5)      ZoneId.of("America/New_York")
       |                              |
  규칙이 없다                    7월이면 서머타임 -> -04:00
       |                              |
  17:00Z                         16:00Z
                                 ^^^^^^ 한 시간 차이
```

- 겨울에 맞춰 `-05:00` 을 박아 두면 **여름에 한 시간 틀린다.**
- 방어: **지역을 뜻하면 `ZoneId`**, 이미 확정된 순간의 표기를 뜻할 때만 `ZoneOffset`.

### 6. `LocalDateTime` 끼리 순서를 비교하고 순간이라 믿는다

**실행 결과** (`Ex.java` — 51-d, 17·21·25 동일)

```text
--- (6) 두 LocalDateTime 은 순서를 비교할 수 있지만 순간이 아니다
  a.isAfter(b) : true   (LocalDateTime 끼리는 b 가 이르다고 나온다)
  실제 순간     : 2026-03-08T00:00:00Z vs 2026-03-08T12:00:00Z
  az.isAfter(bz): false   (시간대를 붙이면 뒤집힌다)
```

- 서울 09:00 과 뉴욕 08:00 을 `LocalDateTime` 으로 비교하면 **서울이 뒤**라고 나온다.
- 실제 순간은 서울 09:00 이 **12시간 앞**이다. 시간대를 붙이면 결과가 **뒤집힌다.**
- 방어: 서로 다른 지역의 값을 비교하려면 **반드시 `Instant` 로 정규화**한다.

### 7. 파싱 형식을 타입과 안 맞춘다

**실행 결과** (`Ex.java` — 51-d, 17·21·25 동일)

```text
--- (4) 파싱 — 문자열이 타입에 안 맞으면
Instant.parse("2026-03-08T16:30")         : java.time.format.DateTimeParseException: Text '2026-03-08T16:30' could not be parsed at index 16
Instant.parse("2026-03-08T16:30:00+09:00") : 2026-03-08T07:30:00Z
LocalDateTime.parse("2026-03-08T07:30:00Z") : java.time.format.DateTimeParseException: Text '2026-03-08T07:30:00Z' could not be parsed, unparsed text found at index 19
LocalDate.parse("2026-02-30")             : java.time.format.DateTimeParseException: Text '2026-02-30' could not be parsed: Invalid date 'FEBRUARY 30'
LocalDate.of(2026, 2, 30)                 : java.time.DateTimeException: Invalid date 'FEBRUARY 30'
LocalDate.of(2026, 13, 1)                 : java.time.DateTimeException: Invalid value for MonthOfYear (valid values 1 - 12): 13
ZonedDateTime.parse("2026-03-08T16:30+09:00[Asia/Seoul]") : 2026-03-08T16:30+09:00[Asia/Seoul]
```

- **`Instant.parse` 는 오프셋을 요구한다.** `+09:00` 이 붙으면 받아서 UTC 로 환산한다.
- **`LocalDateTime.parse` 는 오프셋을 거부한다** — "unparsed text found at index 19", 즉 `Z` 가 남았다는 뜻이다.
- `LocalDate.of(2026, 2, 30)` 과 `parse("2026-02-30")` 은 **예외 타입이 다르다**(`DateTimeException` 대 `DateTimeParseException`). 둘 다 메시지는 `Invalid date 'FEBRUARY 30'` 을 품는다.
- 방어: **받는 형식과 타입을 짝지어 정한다.** API 경계에서는 `Instant`(ISO-8601 + `Z`)가 가장 헷갈리지 않는다.

### 8. `now()` 를 코드 안에서 직접 부른다

- 테스트가 **자정·월말·윤년·서머타임 전이일**에만 깨진다. 재현이 안 된다.
- 방어: `Clock` 을 주입한다((7)). `Clock.systemDefaultZone()` 을 기본값으로 두면 운영 코드는 그대로다.

## 구현 세부사항 대 언어 보장

이 주제의 가장 중요한 표다. **같은 코드가 JDK 판에 따라 다른 답을 냈다.**

### tzdb 판이 갈렸다

**실행 결과** (`Ex.java` — 51-c)

```text
===== JDK 17.0.13 =====            ===== JDK 21.0.5 =====           ===== JDK 25.0.1 =====
java.version : 17.0.13             java.version : 21.0.5            java.version : 25.0.1
tzdb version : 2024a               tzdb version : 2024a             tzdb version : 2025b
zone 개수    : 603                 zone 개수    : 603               zone 개수    : 604
```

```text
--- (1) tzdata 판에 따라 없는 지역이 있다
  [17 · 21] America/Coyhaique : java.time.zone.ZoneRulesException: Unknown time-zone ID: America/Coyhaique
  [25]      America/Coyhaique : America/Coyhaique  규칙 ZoneRules[currentStandardOffset=-03:00]
  [25]      2026-03-01 오프셋 : 2026-03-01T09:00-03:00[America/Coyhaique]

--- (2) 같은 이름인데 규칙이 바뀐 지역 — America/Asuncion 의 2026년 전이
  [17 · 21]
  전이 1 : Transition[Overlap at 2025-03-23T00:00-03:00 to -04:00]
  전이 2 : Transition[Gap at 2025-10-05T00:00-04:00 to -03:00]
  전이 3 : Transition[Overlap at 2026-03-22T00:00-03:00 to -04:00]
  전이 4 : Transition[Gap at 2026-10-04T00:00-04:00 to -03:00]
  2026-01-15 현지 시각 : 2026-01-15T09:00-03:00[America/Asuncion]

  [25]
  전이 1 : null
  2026-01-15 현지 시각 : 2026-01-15T09:00-03:00[America/Asuncion]
```

```text
  America/Asuncion 을 두 판에서 물었다

  tzdb 2024a (JDK 17 · 21)            tzdb 2025b (JDK 25)
  +-----------------------+           +-----------------------+
  | 2025-03-23 전이 있음  |           | 2025 이후 전이 없음   |
  | 2025-10-05 전이 있음  |           | nextTransition -> null|
  | 2026-03-22 전이 있음  |           |                       |
  | 2026-10-04 전이 있음  |           |                       |
  +-----------------------+           +-----------------------+
     "2026년 3월에 시계를 돌린다"        "앞으로 안 돌린다"

  같은 소스, 같은 클래스, 다른 답.
```

그림 해설 (한 단계씩):

- **시간대 규칙은 JDK 에 번들된 데이터다.** 코드가 아니라 데이터가 답을 정한다.
- 17 과 21 은 **2024a** 로 같았고, 25 만 **2025b** 였다. 지역 개수도 603 대 604.
- 늘어난 지역 하나는 두 판의 ID 목록을 diff 해서 확인했다 — **`America/Coyhaique`** 하나뿐이었다.
- `America/Asuncion` 은 **ID 가 그대로인데 규칙이 통째로 달라졌다.** 이쪽이 더 위험하다. 예외도 경고도 없이 답만 바뀐다.

**그래서 이렇게 읽는다.**

| 관측한 것 | 보장인가 | 근거 |
|---|---|---|
| `Instant`/`LocalDateTime`/`ZonedDateTime` 의 **의미** | **보장** | javadoc·JSR 310 |
| 갭에서 `atZone` 이 **앞으로 민다** | **보장** | `ZonedDateTime` javadoc — "shifted forwards by the length of the Gap" |
| 중복에서 `atZone` 이 **앞쪽 오프셋**을 고른다 | **보장** | 같은 javadoc — "the earlier offset" |
| `ofStrict` 가 갭에서 `DateTimeException` | **보장** | javadoc |
| `Instant` 의 하루 = 86,400초 | **보장** | `Instant.plus` javadoc |
| **특정 지역의 특정 날짜 오프셋** | **보장 아님 — tzdata 판에 달렸다** | 위 실측 |
| `ZoneId.of("America/Coyhaique")` 가 되는 것 | **보장 아님** | 17·21 에서는 던진다 |
| `nextTransition` 이 `null` 인 것 | **보장 아님** | 같은 지역이 판에 따라 갈렸다 |
| 예외 **메시지** 문구 | **보장 아님** | javadoc 이 규정하지 않는다 |
| `Clock.systemUTC()` 의 **나노 자릿수** | **보장 아님** | 아래 |

**`now()` 의 정밀도**

```text
--- (6) now() 의 정밀도는 구현 세부다
  [17] nano=130588974 / 131301156 / 131331797
  [21] nano=851345725 / 852154849 / 852194950
  [25] nano=568157881 / 568417598 / 568448844
```

- 세 판 모두 **끝 세 자리가 0 이 아니다** — 이 머신·이 OS 에서는 나노초까지 나온다.
- Java 8 의 `Instant.now()` 는 **밀리초 단위**였다. JDK 9 에서 소스가 바뀌었다.
- 그러니 `Instant.now()` 를 DB 에 넣고 다시 읽어 `equals` 로 비교하면 **정밀도가 깎여 실패**할 수 있다. `truncatedTo(ChronoUnit.MICROS)` 로 맞추는 것이 안전하다.

**세 판에서 같았던 것**

- 51-a·51-b·51-d 는 **tzdb 줄 하나를 빼고 출력이 전부 같았다.**
- 갭·중복·예외 타입·예외 메시지가 모두 같았다. **하지만 그것은 관찰이지 보장이 아니다** — 바로 위 `America/Asuncion` 이 반례다.

## 언제 쓰고 언제 안 쓰나

| 무엇을 표현하려는가 | 고를 것 | 왜 |
|---|---|---|
| **이미 일어난 일**(주문 생성·로그·측정) | `Instant` | 지역과 무관한 사실. 저장·비교·정렬이 단순 |
| 사용자에게 **보여 줄** 시각 | `ZonedDateTime` (표시 직전에 변환) | 보는 사람의 지역이 필요하다 |
| **앞으로 할 약속**(회의·예약) | `ZonedDateTime` 또는 `LocalDateTime` + `ZoneId` 따로 | 규칙이 바뀌면 "그 지역의 그 시각"을 따라가야 한다 |
| 생일·기념일·계약일 | `LocalDate` | 지역이 의미 없다 |
| 매일 반복되는 알람 | `LocalTime` (+ 지역은 따로) | "07:00"이 값이고 지역은 사용자 설정 |
| 영업시간 "09:00~18:00" | `LocalTime` 쌍 | |
| 로그 파일의 타임스탬프 | `Instant` 로 저장, 표시할 때만 변환 | |
| DB 컬럼 | `TIMESTAMP WITH TIME ZONE` ↔ `Instant`/`OffsetDateTime` | `TIMESTAMP` (무시간대)는 (1)의 함정 |
| API 의 JSON 필드 | ISO-8601 + `Z` (`Instant`) | 파싱이 한 가지로 정해진다 |
| **쓰면 안 되는 것** | `java.util.Date`·`Calendar`·`SimpleDateFormat` | 가변·스레드 비안전·월이 0부터 |

판단 규칙 세 줄.

- **"이 값이 지구상 어디서든 같은 순간을 뜻하나"** — 그렇다면 `Instant`.
- **"이 값에 지역을 붙여야 뜻이 완성되나"** — 그렇다면 `LocalDateTime` 으로 두고 지역을 **따로** 들고 다닌다.
- **"지역까지가 값의 일부인가"** — 그렇다면 `ZonedDateTime`.

## 핵심 문장

- 세 타입은 능력이 아니라 **무엇이 빠졌는지**로 갈린다 — `Instant` 는 지역이 없고, `LocalDateTime` 은 시간대가 없고, `ZonedDateTime` 은 둘 다 있다.
- **`LocalDateTime` 은 순간이 아니다.** 같은 값이 지역마다 다른 순간이고, 실측에서 네 지역이 최대 13시간 벌어졌다.
- 존재하지 않는 시각은 **예외가 아니라 조정**이다 — `atZone` 이 갭 길이만큼 앞으로 민다. 거부하려면 `ofStrict` 를 써야 한다.
- 중복 구간의 "01:30"은 **두 순간**이다. `withEarlierOffsetAtOverlap`/`withLaterOffsetAtOverlap` 로 골라야 한다.
- **시간대 규칙은 JDK 에 번들된 데이터다.** 17·21 은 tzdb 2024a, 25 는 2025b 였고, `America/Asuncion` 의 2026년 전이가 **있다/없다**로 갈렸다.

## 관련 자료

- [`../52-duration-period-formatter/`](../52-duration-period-formatter/) — **이 주제를 이어받는다.** 그쪽은 **두 시각 사이의 간격과 출력 형식**까지, 여기는 **한 시각을 어느 타입으로 적나**까지
- [`../../../../../ops-patterns/17-timeseries/`](../../../../../ops-patterns/17-timeseries/) — 시계열 버킷·롤업. 그쪽은 **시간 축 위에 값을 쌓고 접는 패턴**까지, 여기는 **그 축의 한 점을 표현하는 타입**까지
- [`../../../../../../history/java/java-8.md`](../../../../../../history/java/java-8.md) — `java.time` 이 **왜 들어왔나**(JSR 310·Joda-Time·`Calendar` 의 문제). 도입 맥락은 거기
- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 51번)
- [**53번 주제**](../53-bigdecimal/)(`BigDecimal`) — 같은 「정밀도」 계열. 그쪽은 **`double` 의 값이 틀리는 자리**, 여기는 **시각의 값이 틀리는 자리**
- [**27번 주제**](../27-equals-hashcode-contract/)(`equals` 계약) — `ZonedDateTime.equals` 와 `isEqual` 이 갈리는 이유가 그 계약이다
- [**25번 주제**](../25-exceptions/)(예외) — `DateTimeException` 은 unchecked 다. 어디서 막을지는 거기가 정본
- [**59번 주제**](../59-immutable-objects/)(불변 객체) — `java.time` 전체가 그 설계의 본보기다

## 용어 풀이

- **`Instant`** — 에포크로부터 흐른 초·나노로 표현한 **기계 시각**. 지역 개념이 없고 `toString` 은 항상 `Z` 로 끝난다.
- **`LocalDateTime`** — 날짜와 시각만 있고 시간대가 없는 값. 지역을 붙이기 전까지는 **순간이 아니다.**
- **`ZonedDateTime`** — 날짜·시각 + 오프셋 + 시간대 규칙. 순간 하나로 환산된다.
- **`OffsetDateTime`** — 날짜·시각 + 오프셋(숫자)만. 순간이지만 **미래 규칙 변경을 못 따라간다.**
- **에포크(epoch)** — 1970-01-01T00:00:00Z 를 0으로 삼는 기준점. 예: 2026-03-08T07:30Z 는 1,772,955,000초다.
- **오프셋(offset)** — UTC 와의 시차 숫자. 예: `+09:00`. 규칙이 없어 계절에 따라 바뀌지 않는다.
- **시간대(time zone)** — 오프셋이 언제 어떻게 바뀌는지의 규칙 묶음. 예: `America/New_York` 은 3월·11월 전이 규칙을 들고 있다.
- **tzdb / tzdata** — 세계 시간대 규칙의 표준 데이터베이스. JDK 에 번들되며 판 번호가 있다(예: `2024a`·`2025b`).
- **갭(gap)** — 시계를 앞당겨 **지역 달력에서 사라진 구간.** 예: 뉴욕의 2026-03-08 02:00~02:59.
- **중복(overlap)** — 시계를 되돌려 **같은 지역 시각이 두 번 오는 구간.** 예: 뉴욕의 2026-11-01 01:00~01:59.
- **`ZoneRules`** — 한 지역의 전이 규칙 전체. `getValidOffsets`·`getTransition`·`nextTransition` 으로 물어본다.
- **`Clock`** — "지금"을 돌려주는 객체. 순간과 지역을 함께 들고 있으며, `Clock.fixed` 로 테스트에서 고정한다.
- **`UnsupportedTemporalTypeException`** — 그 타입이 지원하지 않는 필드·단위를 물었을 때의 예외. `DateTimeException` 의 하위다.
- **서머타임(DST, daylight saving time)** — 여름에 시계를 한 시간 앞당기는 제도. 갭과 중복의 원인이다.

## 더 들어가면

- **`atStartOfDay()` 가 항상 00:00 은 아니다.**\
  자정이 갭인 지역이 있다(브라질이 그랬다). `LocalDate.atStartOfDay(ZoneId)` 의 javadoc 이 그 경우 "the time will be the earliest valid time after the gap" 이라고 적는다.\
  이 머신의 tzdb 2024a·2025b 에 그런 지역이 남아 있는지는 **안 돌려 봄**이다 — 전 지역 전 날짜를 훑어야 확인되는 것이라 1분으로 끝나지 않는다.
- **`Instant.now()` 의 정밀도는 Java 8 과 9 가 다르다.**\
  8 에서는 밀리초, 9부터 `Clock.systemUTC()` 가 더 잘게 센다. 이 머신에는 8 이 없어 **8 의 동작은 안 돌려 봄**이다.\
  17·21·25 는 셋 다 나노 자릿수까지 0 이 아닌 값을 냈다.
- **윤초(leap second)는 `java.time` 에 없다.**\
  `Instant` 의 하루는 **정확히 86,400초**다. 실제 UTC 의 윤초는 "smeared"(뭉개짐) 로 처리되는 것이 보통이고, 그 처리는 OS·NTP 서버의 몫이다.
- **`ZoneId.systemDefault()` 는 언제든 바뀔 수 있다.**\
  `TimeZone.setDefault(...)` 는 **JVM 전역**을 바꾼다. 라이브러리가 그걸 호출하면 그 뒤의 모든 `LocalDate.now()` 가 달라진다.\
  그래서 운영 코드에서는 **지역을 명시하거나 `Clock` 으로 주입**하는 쪽이 안전하다.
- **`compareTo` 와 `equals` 가 불일치한다.**\
  `ZonedDateTime` 의 `compareTo` 는 순간 → 지역 시각 → 지역 ID 순으로 비교한다. 실측에서 같은 순간의 서울/뉴욕이 `compareTo == 1` 이었다.\
  `Comparable` 계약이 권장하는 "compareTo == 0 이면 equals" 를 **의도적으로 어긴 것**이고, javadoc 에도 그 사실이 적혀 있다([**28번 주제**](../28-comparable-comparator/)가 그 계약의 정본이다).
