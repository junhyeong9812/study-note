# java/syntax/51 — `java.time` — `Instant`·`LocalDate`/`LocalDateTime`·`ZonedDateTime` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 실제로 돌려 얻은 것이다. 프로그램 다섯(51-a~51-e)을 **Temurin 17.0.13 · 21.0.5 · 25.0.1** 에서 각각 돌렸다.\
> ★ **세 판이 같았다고 적지 않는다.** 13번에서 실제로 갈렸고, 나머지 문항에는 "세 판 동일"을 관찰로만 적는다.\
> javadoc 인용은 JDK 21.0.5 의 `lib/src.zip` — `java.base/java/time/*.java` 원문이다.\
> 측정 조건: 기본 시간대 `Asia/Seoul`, 기본 `Locale` `ko_KR`.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 같은 순간을 세 지역에서 보면

**출력** (`Ex.java` — 51-a, 17·21·25 동일)

```text
--- (0) 기준 — 고정 시각 하나를 세 축으로 본다
Instant                        : 2026-03-08T07:30:00Z
epochSecond                    : 1772955000
Asia/Seoul 로 보면             : 2026-03-08T16:30+09:00[Asia/Seoul]
America/New_York 로 보면       : 2026-03-08T03:30-04:00[America/New_York]
UTC 로 보면                    : 2026-03-08T07:30Z
```

**뉴욕이 `-04:00` 인 이유**

- 2026-03-08 은 **서머타임이 이미 시작된 날**이다. 그날 02:00 에 시계를 앞당겼다(3번의 갭이 바로 이 전이다).
- 07:30Z 는 그 전이 뒤라서 `-04:00` 이 적용되고, 지역 시각은 03:30 이 된다.

**`Instant.toString()` 이 `Z` 로 끝나는 이유**

- `Instant` 는 **지역 개념이 없다.** 에포크 초 하나뿐이다.
- 그것을 사람이 읽는 문자열로 적으려면 기준이 하나 필요한데, 그 기준이 **UTC** 로 고정돼 있다.

**`toEpochSecond()` 는**

- **셋 다 같다** — `1772955000`. 애초에 같은 순간을 세 액자로 본 것이다.

**대괄호는 무엇인가**

```text
  2026-03-08T16:30+09:00[Asia/Seoul]
                  ^^^^^^ ^^^^^^^^^^
                  오프셋  시간대 ID(규칙의 이름)
```

- 오프셋만으로는 미래의 규칙 변경을 따라갈 수 없다. **ID 가 있어야 규칙이 따라온다**(10번).
- `OffsetDateTime` 은 대괄호가 없다 — 오프셋까지만 들고 있기 때문이다.

### 2. 같은 `LocalDateTime` 을 네 지역에 붙이면

**출력** (`Ex.java` — 51-a, 17·21·25 동일)

```text
--- (2) LocalDateTime 은 순간이 아니다 — 같은 값이 지역마다 다른 순간
Asia/Seoul         2026-03-08T16:30+09:00[Asia/Seoul]  ->  epochSecond 1772955000
Europe/Paris       2026-03-08T16:30+01:00[Europe/Paris]  ->  epochSecond 1772983800
America/New_York   2026-03-08T16:30-04:00[America/New_York]  ->  epochSecond 1773001800
UTC                2026-03-08T16:30Z[UTC]  ->  epochSecond 1772987400
```

**같은가 다른가 · 차이**

- **넷 다 다르다.**
- 가장 이른 것은 서울 `1772955000`, 가장 늦은 것은 뉴욕 `1773001800`.
- 차이는 `1773001800 − 1772955000 = 46800` 초 = **13시간**(출력에 있는 두 값의 뺄셈이다).

**DB 저장 시 같이 저장할 것**

- **그 값이 어느 지역 기준인지**다. 지역을 안 적으면 복원할 수 없다.
- 더 나은 답: **저장 자체를 `Instant`(또는 `TIMESTAMP WITH TIME ZONE`)로** 한다.

**`LocalDateTime` 이 맞는 값 셋**

1. **생일** — 어디서 살든 3월 8일이 생일이다.
2. **"매일 07:00" 알람** — 사용자가 이동하면 그 지역의 07:00 이어야 한다.
3. **계약서에 적힌 날짜·시각** — 문서의 글자가 값이다.

**한 문장**

- **지역을 붙이기 전까지 어느 순간인지 정해지지 않기 때문이다** — 실측에서 한 값이 13시간 폭의 후보들을 가졌다.

### 3. 존재하지 않는 시각을 만들면

**출력** (`Ex.java` — 51-b, 17·21·25 동일 — tzdb 줄만 다르다)

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
--- (2) 같은 갭을 ofStrict 로 만들면
  ofStrict(-05:00) : java.time.DateTimeException: LocalDateTime '2026-03-08T02:30' does not exist in zone 'America/New_York' due to a gap in the local time-line, typically caused by daylight savings
  ofStrict(-04:00) : java.time.DateTimeException: LocalDateTime '2026-03-08T02:30' does not exist in zone 'America/New_York' due to a gap in the local time-line, typically caused by daylight savings
```

**`atZone` 은 예외인가 값인가**

- **값이다.** `2026-03-08T03:30-04:00[America/New_York]`.
- **갭 길이(1시간)만큼 앞으로 민** 값이다. 이것이 이 주제에서 가장 조용한 함정이다.
- javadoc 이 규칙을 못박는다.

  > In the case of a gap, when clocks jump forward, there is no valid offset. Instead, **the local date-time is adjusted to be later by the length of the gap.**

**`getValidOffsets`**

- **빈 리스트 `[]`** — 크기 0. "유효한 오프셋이 하나도 없다"가 곧 "존재하지 않는다"의 정의다.

**`ofStrict` 가 던지는 것**

- `java.time.DateTimeException`.
- 메시지: `LocalDateTime '2026-03-08T02:30' does not exist in zone 'America/New_York' due to a gap in the local time-line, typically caused by daylight savings`

**오프셋을 `-04:00` 으로 바꾸면**

- **달라지지 않는다.** 두 줄의 메시지가 한 글자도 같았다.
- 오프셋이 문제가 아니라 **그 지역 시각 자체가 없어서**다.

**거부하려면**

```java
// 방법 1 — 유효 오프셋을 직접 확인한다
if (zone.getRules().getValidOffsets(input).isEmpty()) {
    throw new IllegalArgumentException("그 지역에 존재하지 않는 시각입니다");
}

// 방법 2 — ofStrict 에 맡긴다
ZonedDateTime.ofStrict(input, zone.getRules().getOffset(input), zone);
```

- `atZone` 은 **절대 거부하지 않는다.** 검증을 원하면 명시적으로 넣어야 한다.

### 4. 시계가 뒤로 갈 때 — 두 번 있는 시각

**출력** (`Ex.java` — 51-b, 17·21·25 동일)

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

**크기**

- **2** — `[-04:00, -05:00]`.

**`atZone` 이 고르는 쪽**

- **앞쪽(`-04:00`)** 이다. `withEarlierOffsetAtOverlap()` 과 에포크 초가 같다(`1793511000`).

**에포크 차이**

- `1793514600 − 1793511000 = 3600` 초 = **1시간**. 출력의 `PT1H` 와 맞는다.

**`toLocalDateTime`·`equals`·`isEqual`**

| 물음 | 답 | 왜 |
|---|---|---|
| `toLocalDateTime()` 이 같나 | **`true`** | 지역 시각 문자열이 같다 |
| `equals` | **`false`** | 오프셋이 다르다 |
| `isEqual` | **`false`** | **순간이 1시간 다르다** |

- 11번의 서울/뉴욕 예와 정확히 **반대**다. 거기서는 `equals=false, isEqual=true` 였다.
- 여기서는 `toLocalDateTime` 만 같고 나머지가 다르다 — **"보이는 글자가 같다"와 "같은 순간이다"는 완전히 독립**이다.

**`getDuration()`**

```text
  갭    Transition[Gap at ...]      duration = PT1H     양수 (시간이 사라졌다)
  중복  Transition[Overlap at ...]  duration = PT-1H    음수 (시간이 되돌아왔다)
```

### 5. 한국에 서머타임이 있었나

**출력** (`Ex.java` — 51-b, 17·21·25 동일)

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

**첫 줄의 결과**

- `1988-05-08T03:30+10:00[Asia/Seoul]` — **뉴욕과 똑같이 한 시간 밀렸다.**
- 1988년 여름 서울의 오프셋은 **`+10:00`** 이었다.

**`isFixedOffset()` 과 그 함정**

- **`false`** 다.
- 함정은 이 메서드가 "지금 고정인가"가 아니라 "**역사 전체에 전이가 하나도 없는가**"를 묻는다는 것이다.
- 1988년에 전이가 있었으므로 `Asia/Seoul` 은 영원히 `false` 다. 뉴욕과 **구별되지 않는다.**

**`nextTransition`**

- **`null`** — 2026-01-01 이후로는 예정된 전이가 없다.
- 같은 호출이 뉴욕에서는 `Transition[Gap at 2026-03-08T02:00-05:00 to -04:00]` 를 돌려준다.

**"오늘 DST 가 없다"의 판정**

```java
boolean noFutureDst = zone.getRules().nextTransition(Instant.now()) == null;
```

- `isFixedOffset()` 이 아니라 **`nextTransition(지금)` 이 `null` 인가**를 묻는다.

**1988년 데이터를 `+09:00` 고정으로 처리하면**

- 1988-05-08 ~ 1988-10-09 사이의 값이 **한 시간씩 틀린다.**
- 그 구간의 지역 시각을 `+09:00` 으로 되돌리면 UTC 가 한 시간 늦게 계산된다.
- (그 해 서울 올림픽 기간이 이 구간 안에 있다.)

### 6. 불변성과 달 단위 덧셈

**출력** (`Ex.java` — 51-a, 17·21·25 동일)

```text
--- (4) 불변이다 — plus 는 새 객체를 돌려준다
base        : 2026-01-31  (그대로다)
plusMonths(1): 2026-02-28  (2월 31일이 없어 말일로 잘린다)
plusMonths(1).plusMonths(1) : 2026-03-28
plusMonths(2)               : 2026-03-31
base == plus1 ?             : false
```

**세 줄의 결과**

- `plusMonths(1)` = `2026-02-28`
- `plusMonths(1).plusMonths(1)` = `2026-03-28`
- `plusMonths(2)` = `2026-03-31`

**`base` 는**

- **그대로 `2026-01-31`** 이다. `==` 도 `false` — 새 객체가 나왔다.

**왜 다른가**

```text
  1/31 --+1개월--> 2/31? 없다 --> 2/28 로 자른다 --+1개월--> 3/28
                                     ^
                           여기서 정보(31일)가 사라졌다

  1/31 --+2개월--> 3/31? 있다 --> 3/31
                                     ^
                           한 번에 가면 자르지 않는다
```

- **중간에 한 번 잘리면 그 정보가 돌아오지 않는다.** 그래서 결합법칙이 안 선다.
- 방어: 여러 번 더하지 말고 **한 번에** 더한다. `plusMonths(a).plusMonths(b)` 대신 `plusMonths(a + b)`.

**갭 처리와의 공통점**

- **요청한 값이 존재하지 않을 때 예외가 아니라 "가장 가까운 유효한 값"으로 조정한다**는 점이 같다.
- 갭은 앞으로 밀고, 월말은 뒤로 자른다. **방향은 달라도 "조용히 값이 바뀐다"는 성질이 같다.**

**불변의 득실**

| | |
|---|---|
| 얻는 것 | 락 없이 공유 가능 · 방어적 복사 불필요 · `final` 필드로 둘 수 있다 · 누가 고쳐 놓을 걱정이 없다 |
| 치르는 것 | 연산마다 새 객체 · 반환값을 **안 받으면 아무 일도 안 일어난다**(`date.plusDays(1);` 한 줄은 무의미하다) |

### 7. `Instant` 에 무엇을 더할 수 있나

**출력** (`Ex.java` — 51-d, 17·21·25 동일)

```text
--- (1) Instant 에 달력 단위를 더하면
t.plus(1, DAYS)      : 2026-03-09T07:30:00Z
t.plus(1, WEEKS)     : java.time.temporal.UnsupportedTemporalTypeException: Unsupported unit: Weeks
t.plus(1, MONTHS)    : java.time.temporal.UnsupportedTemporalTypeException: Unsupported unit: Months
t.plus(1, YEARS)     : java.time.temporal.UnsupportedTemporalTypeException: Unsupported unit: Years
t.plus(Period.ofDays(1))    : 2026-03-09T07:30:00Z
t.plus(Period.ofMonths(1))  : java.time.temporal.UnsupportedTemporalTypeException: Unsupported unit: Months
t.plus(Duration.ofDays(1))  : 2026-03-09T07:30:00Z
--- (2) Instant 에서 달력 필드를 꺼내면
t.getLong(YEAR)          : java.time.temporal.UnsupportedTemporalTypeException: Unsupported field: Year
t.truncatedTo(DAYS)      : 2026-03-08T00:00:00Z
t.truncatedTo(MONTHS)    : java.time.temporal.UnsupportedTemporalTypeException: Unit is too large to be used for truncation
```

**성공/실패**

| 호출 | 결과 |
|---|---|
| `plus(1, DAYS)` | **성공** — `2026-03-09T07:30:00Z` |
| `plus(1, MONTHS)` | 실패 — `Unsupported unit: Months` |
| `plus(Period.ofDays(1))` | **성공** — `Period` 여도 단위가 DAYS 면 된다 |
| `plus(Period.ofMonths(1))` | 실패 — `Unsupported unit: Months` |
| `getLong(YEAR)` | 실패 — `Unsupported field: Year` |
| `truncatedTo(MONTHS)` | 실패 — **`Unit is too large to be used for truncation`**(메시지가 다르다) |

- 예외 타입은 앞의 다섯이 전부 `java.time.temporal.UnsupportedTemporalTypeException` 이다.
- 마지막만 **메시지가 다르다** — 같은 타입인데 검사하는 자리가 달라서다.

**`DAYS` 는 되고 `MONTHS` 는 안 되는 이유**

- **하루는 길이가 고정이고, 한 달은 아니다.**
- `Instant` 에는 달력이 없으므로 "2월인지 3월인지"를 알 수 없고, 따라서 한 달이 며칠인지도 모른다.

**`Instant` 에게 하루는**

- **정확히 86,400초.** javadoc 이 못박는다.

  > `DAYS` - Returns an `Instant` with the specified number of days added. This is equivalent to `plusSeconds(long)` with the amount multiplied by **86,400 (24 hours)**.

- 따라서 서머타임이 있는 지역의 "하루"(23시간 또는 25시간)와는 **다른 뜻**이다. 그 차이는 [`../52-duration-period-formatter/`](../52-duration-period-formatter/) 가 정본이다.

**지역 달력 기준으로 한 달 더하기**

```java
Instant result = instant.atZone(zone)      // 지역을 붙이고
                        .plusMonths(1)     // 그 달력으로 더한 뒤
                        .toInstant();      // 다시 순간으로
```

### 8. `get` 과 `getLong` 이 왜 다른가

**출력** (`Ex.java` — 51-a, 17·21·25 동일)

```text
t.get(INSTANT_SECONDS)    : java.time.temporal.UnsupportedTemporalTypeException: Unsupported field: InstantSeconds
t.getLong(INSTANT_SECONDS): 1772955000
t.get(YEAR)               : java.time.temporal.UnsupportedTemporalTypeException: Unsupported field: Year
t.isSupported(ChronoField.YEAR)             : false
t.isSupported(ChronoField.INSTANT_SECONDS)  : true
```

**세 줄**

- `isSupported(INSTANT_SECONDS)` = **`true`**
- `get(INSTANT_SECONDS)` = **던진다**
- `getLong(INSTANT_SECONDS)` = **`1772955000`**

**`true` 인데 `get` 이 던지는 이유**

```text
  int get(TemporalField)        <- 반환 타입이 int (약 ±21억)
  long getLong(TemporalField)   <- 반환 타입이 long

  INSTANT_SECONDS 의 값 범위는 long 이다.
  1772955000 은 int 에 들어가지만, 필드의 "범위 자체"가 int 를 넘는다.
      |
  Instant.get 은 필드 범위를 보고 미리 거부한다 -> 값과 무관하게 던진다
```

- "**지금 값이 int 에 들어가느냐"가 아니라 "이 필드의 범위가 int 에 들어가느냐**"로 판단한다.
- 그래서 값이 작아도 던진다. `getLong` 을 써야 한다.

**예외 타입·메시지**

- `java.time.temporal.UnsupportedTemporalTypeException: Unsupported field: InstantSeconds`
- **메시지 문구가 `isSupported(YEAR)=false` 인 경우와 똑같다** — 두 실패의 원인이 전혀 다른데 메시지가 같다.

**`isSupported(YEAR)` 와의 차이**

| | `INSTANT_SECONDS` | `YEAR` |
|---|---|---|
| `isSupported` | `true` | **`false`** |
| 원인 | 반환 타입이 좁다 | **개념 자체가 없다** |
| 해결 | `getLong` 을 쓴다 | `atZone(...)` 을 먼저 붙인다 |

**규칙**

- **`getLong` 을 기본으로 쓴다.** `get` 은 `int` 로 확실히 들어가는 필드(연·월·일·시·분·초)에만.
- 던지는지 미리 알고 싶으면 **`isSupported` 를 먼저 묻되, 그것이 `get` 의 성공을 보장하지는 않는다**는 것을 안다.

### 9. 시간대 ID 문자열

**출력** (`Ex.java` — 51-d, 17·21·25 동일)

```text
--- (5) 시간대 ID 가 틀리면
ZoneId.of("KST")          : java.time.zone.ZoneRulesException: Unknown time-zone ID: KST
ZoneId.of("Asia/Soul")    : java.time.zone.ZoneRulesException: Unknown time-zone ID: Asia/Soul
ZoneId.of("UTC+9")        : UTC+09:00
ZoneId.of("+09:00")       : +09:00
ZoneOffset.of("+09:00")   : +09:00
ZoneId.of("Asia/Seoul")   : Asia/Seoul
```

**던지는 것 / 통과하는 것**

- 던진다: `"KST"`, `"Asia/Soul"`
- 통과한다: `"UTC+9"`, `"+09:00"`, `"Asia/Seoul"`

**예외 타입**

- `java.time.zone.ZoneRulesException` — `DateTimeException` 의 하위다.

**약어와 오타를 구분할 수 있나**

- **없다.** 둘 다 `Unknown time-zone ID: X` 로 같은 형태다.
- `"KST"` 가 "약어라 안 되는 것"이고 `"Asia/Soul"` 이 "철자가 틀린 것"인데, **API 가 그 차이를 알려주지 않는다.**

**`"+09:00"` 이 돌려준 것**

```text
  ZoneId.of("+09:00")  ->  실제 타입은 ZoneOffset (ZoneId 의 하위)
                           toString 도 "+09:00" 이다
                                |
                        규칙이 없다 — 영원히 +09:00 이다
```

- **빠져 있는 것은 전이 규칙**이다. 10번에서 그 결과를 본다.
- `"UTC+9"` 도 같다. `UTC+09:00` 으로 정규화되지만 역시 고정이다.

**방어**

```java
// 상수로 한 번만 쓴다
private static final ZoneId SEOUL = ZoneId.of("Asia/Seoul");

// 외부 입력이면 미리 검증한다
if (!ZoneId.getAvailableZoneIds().contains(input)) {
    throw new IllegalArgumentException("알 수 없는 시간대: " + input);
}
```

- 다만 `getAvailableZoneIds()` 의 내용 자체가 **JDK 판에 따라 다르다**(13번).

### 10. `ZoneOffset` 과 `ZoneId` 를 바꿔 쓰면

**출력** (`Ex.java` — 51-e, 17·21·25 동일)

```text
--- 겨울 (1월 1일)
  고정 -05:00 : 2026-01-01T12:00-05:00 -> 2026-01-01T17:00:00Z
  New_York    : 2026-01-01T12:00-05:00[America/New_York] -> 2026-01-01T17:00:00Z
  같은 순간인가 : true
--- 여름 (7월 1일)
  고정 -05:00 : 2026-07-01T12:00-05:00 -> 2026-07-01T17:00:00Z
  New_York    : 2026-07-01T12:00-04:00[America/New_York] -> 2026-07-01T16:00:00Z
  같은 순간인가 : false
```

**같은가 다른가 · 차이**

- **7월에는 다르다.** `17:00:00Z` 대 `16:00:00Z` — **1시간** 차이다.

**왜**

- `ZoneOffset.ofHours(-5)` 에는 **규칙이 없다.** 1월이든 7월이든 `-05:00` 이다.
- `ZoneId.of("America/New_York")` 는 7월이면 서머타임 규칙을 적용해 **`-04:00`** 을 쓴다.

**겨울로 바꾸면** (돌려 본 결과)

- **같아진다** — 둘 다 `2026-01-01T17:00:00Z`, `같은 순간인가 : true`.
- **이것이 함정의 핵심이다.** 겨울에 개발·테스트하면 차이가 안 보인다. 여름에 배포하면 틀린다.

```text
  1월 테스트                        7월 운영

  고정 -05:00  == New_York          고정 -05:00  != New_York
        |                                 |
   테스트 통과                        1시간 틀림 (조용히)
```

**`ZoneOffset` 이 맞는 때**

- **이미 확정된 순간의 표기**를 그대로 보존할 때. 예: 로그에 `2026-03-08T16:30+09:00` 이 찍혀 있고 그 문자열을 그대로 왕복시켜야 할 때.
- 프로토콜이 오프셋만 요구할 때(ISO-8601 의 대부분).

**`OffsetDateTime` 으로 미래 약속을 저장하면**

- 그 지역의 규칙이 **바뀌면 따라가지 못한다.** 실제로 여러 나라가 DST 를 폐지·도입해 왔다(13번의 파라과이가 그 예다).
- "2027년 7월 1일 뉴욕 12시 회의"를 `-04:00` 으로 박아 두면, 미국이 DST 를 폐지할 경우 **한 시간 틀린 약속**이 된다.
- 방어: **미래의 약속은 `ZonedDateTime`**(또는 `LocalDateTime` + `ZoneId` 를 따로) 로 저장한다.

### 11. `equals` 와 `isEqual` 과 `compareTo`

**출력** (`Ex.java` — 51-a, 17·21·25 동일)

```text
--- (6) 비교 — equals 와 isEqual 이 다르다
seoul : 2026-03-08T16:30+09:00[Asia/Seoul]
ny    : 2026-03-08T03:30-04:00[America/New_York]
seoul.equals(ny)  : false
seoul.isEqual(ny) : true
seoul.toInstant().equals(ny.toInstant()) : true
compareTo : 1
```

**셋의 답**

- `equals` = **`false`** (오프셋·지역이 다르다)
- `isEqual` = **`true`** (순간이 같다)
- `compareTo` = **`1`** (순간은 같은데 2차 기준에서 서울이 뒤로 갔다)

**`TreeSet` 에서 생기는 일**

```text
  HashSet<ZonedDateTime>            TreeSet<ZonedDateTime>
  (equals/hashCode 로 판단)          (compareTo 로 판단)

  seoul, ny 둘 다 들어간다           compareTo != 0 이므로 둘 다 들어간다
       |                                    |
  "같은 순간"이 두 원소             "같은 순간"이 두 원소
                                    게다가 정렬 순서가 순간 순서와 다를 수 있다
```

- `compareTo == 0` 인데 `equals == false` 인 조합은 아니지만, **그 반대(`isEqual==true` 인데 `compareTo!=0`)** 가 성립한다.
- `TreeMap` 의 키로 쓰면 **같은 순간의 두 키가 따로 들어가** 조회가 어긋난다.
- `ZonedDateTime` 의 `compareTo` javadoc 이 이 불일치를 명시한다 — [**28번 주제**](../28-comparable-comparator/)가 그 계약의 정본이다.

**정규화**

```java
Set<Instant> moments = zdts.stream().map(ZonedDateTime::toInstant).collect(toSet());
```

- **`Instant` 로 바꿔서** 넣는다. 순간만 따질 거면 애초에 `Instant` 가 맞는 타입이다.

### 12. `now()` 를 테스트하려면

**출력** (`Ex.java` — 51-c, 17·21·25 동일)

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

**`Clock` 이 들고 있는 것**

- **둘**이다 — **순간을 주는 능력**과 **지역(`getZone()`)**.

**두 줄의 결과**

- 이 예(07:30Z)에서는 **둘 다 `2026-03-08`** 로 같다. 서울 16:30, 뉴욕 02:30 이라 아직 같은 날이다.
- 지역이 날짜를 가르는 것은 **순간을 옮겨 봐야** 보인다. (7)에서 16:30Z 로 바꾸자 **3/9 대 3/8** 로 갈렸다.

**두 번 부르면**

- **같다.** `Clock.fixed` 의 정의다.

**`offset` 과 `tick`**

| | 하는 일 | 위 출력 |
|---|---|---|
| `Clock.offset(clock, d)` | 기준 시계에서 `d` 만큼 **옮긴** 시계 | `+1일` → `2026-03-09T07:30:00Z` |
| `Clock.tick(clock, d)` | `d` 단위로 **잘라 버린** 시계 | 07:30:45.123456789Z 를 1분 단위로 → `07:30:00Z` |

- `tick` 은 "초 이하를 버리고 싶다"에 쓴다. `Clock.tickSeconds`·`tickMinutes` 단축 팩토리도 있다.

**직접 부르는 코드의 테스트가 깨지는 때**

- 자정 직전에 돌 때(날짜가 넘어간다)
- 월말·연말(`plusMonths` 가 자른다 — 6번)
- 윤년 2월 29일
- 서머타임 전이일(3번·4번)
- CI 서버의 `TZ` 가 개발 머신과 다를 때

### 13. 같은 코드가 JDK 마다 다른 답을 낸 곳

**출력** (`Ex.java` — 51-c)

```text
===== JDK 17.0.13 =====
java.version : 17.0.13
tzdb version : 2024a
zone 개수    : 603
--- (1) tzdata 판에 따라 없는 지역이 있다
  America/Coyhaique : java.time.zone.ZoneRulesException: Unknown time-zone ID: America/Coyhaique
--- (2) 같은 이름인데 규칙이 바뀐 지역 — America/Asuncion 의 2026년 전이
  전이 1 : Transition[Overlap at 2025-03-23T00:00-03:00 to -04:00]
  전이 2 : Transition[Gap at 2025-10-05T00:00-04:00 to -03:00]
  전이 3 : Transition[Overlap at 2026-03-22T00:00-03:00 to -04:00]
  전이 4 : Transition[Gap at 2026-10-04T00:00-04:00 to -03:00]
  2026-01-15 현지 시각 : 2026-01-15T09:00-03:00[America/Asuncion]

===== JDK 21.0.5 =====
java.version : 21.0.5
tzdb version : 2024a
zone 개수    : 603
  (17 과 한 글자도 다르지 않다)

===== JDK 25.0.1 =====
java.version : 25.0.1
tzdb version : 2025b
zone 개수    : 604
--- (1) tzdata 판에 따라 없는 지역이 있다
  America/Coyhaique : America/Coyhaique  규칙 ZoneRules[currentStandardOffset=-03:00]
  2026-03-01 오프셋 : 2026-03-01T09:00-03:00[America/Coyhaique]
--- (2) 같은 이름인데 규칙이 바뀐 지역 — America/Asuncion 의 2026년 전이
  전이 1 : null
  2026-01-15 현지 시각 : 2026-01-15T09:00-03:00[America/Asuncion]
```

**첫 줄 — tzdb 판**

| JDK | tzdb |
|---|---|
| 17.0.13 | **2024a** |
| 21.0.5 | **2024a** |
| 25.0.1 | **2025b** |

**둘째 줄 — `America/Coyhaique`**

- **17·21 에서는 `ZoneRulesException: Unknown time-zone ID`** 로 던진다.
- **25 에서는 정상**이고 오프셋 `-03:00` 을 쓴다.
- 두 판의 지역 ID 목록을 전부 뽑아 `diff` 한 결과, **늘어난 것은 이 하나뿐**이었다.

```text
$ diff zones_21.0.5.txt zones_25.0.1.txt
99a100
> America/Coyhaique
```

**셋째 줄 — `America/Asuncion`**

```text
  tzdb 2024a (17·21)                    tzdb 2025b (25)

  2025-03-23 Overlap                    (전이 없음)
  2025-10-05 Gap                        nextTransition -> null
  2026-03-22 Overlap
  2026-10-04 Gap
```

- **ID 도 그대로, 코드도 그대로, 답만 다르다.**
- 이쪽이 더 위험한 이유: **예외가 없다.** `Coyhaique` 는 던지기라도 하지만, 여기는 조용히 다른 답이 나온다.
- 17·21 에서 "2026년 3월 22일에 시계를 되돌린다"고 계산한 배치가, 25 로 올리면 그 전이를 아예 모른다.

**지역 개수**

- 17 = **603**, 21 = **603**, 25 = **604**.

**보장인가**

- **보장이 아니다.** 시간대 계산의 결과는 **JDK 에 번들된 tzdb 판이 정한다.**
- 타입의 의미(갭에서 앞으로 민다, 중복에서 앞쪽을 고른다)는 javadoc 이 보장하지만, **어느 날짜가 갭인지는 데이터**다.
- 그래서 시간대에 민감한 시스템은 **tzdb 판을 명시적으로 관리**한다(JDK 업그레이드, 또는 `tzupdater` 같은 도구).

### 14. 어느 타입을 고르는가

| 요구 | 고를 것 | 이유 |
|---|---|---|
| 주문 생성 시각을 DB 에 | **`Instant`** (`TIMESTAMP WITH TIME ZONE`) | 이미 일어난 사실. 지역과 무관하고 비교·정렬이 단순 |
| 생일 | **`LocalDate`** | 시각도 지역도 의미가 없다 |
| "매일 오전 7시" 알람 | **`LocalTime`** + 사용자의 `ZoneId` 를 따로 | 사용자가 이동해도 그 지역의 07:00 이어야 한다 |
| 6개월 뒤 뉴욕 회의 | **`ZonedDateTime`** 또는 `LocalDateTime` + `ZoneId` | 아래 |

**미래 회의를 `Instant` 로 저장하면 위험한 이유**

- `Instant` 로 바꾸는 순간 **"뉴욕 시간 14시"라는 의도가 사라지고** 에포크 초만 남는다.
- 그 사이에 미국이 DST 규칙을 바꾸면, 저장된 순간은 그대로인데 **뉴욕의 벽시계로는 13시나 15시**가 된다.
- 회의는 "그 지역의 그 시각"에 열리는 것이지 "그 에포크 초"에 열리는 것이 아니다.
- 13번의 파라과이가 실제 사례다 — 2024a 를 쓰던 시스템이 저장해 둔 2026년 순간은, 2025b 기준으로는 **한 시간 어긋난 벽시계 시각**이 된다.

**`java.util.Date`·`SimpleDateFormat` 을 쓰면 안 되는 이유 둘**

1. **가변이다.** `Date.setTime(...)` 이 있어 남이 고쳐 놓을 수 있고, 방어적 복사가 필요하다.
2. **`SimpleDateFormat` 은 스레드 안전하지 않다.** 필드에 두고 공유하면 조용히 틀린 문자열이 나온다.\
   `DateTimeFormatter` 는 불변이라 공유해도 된다 — [`../52-duration-period-formatter/`](../52-duration-period-formatter/) 가 정본이다.
3. (덤) `Calendar` 의 월은 **0부터** 시작한다. `Calendar.MARCH == 2` 다.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Ex.java` (51-a) | 세 축의 `toString`·에포크, `LocalDateTime` 의 지역별 순간, `Instant` 의 지원 필드, 불변·월말 자르기, 타입 간 변환, `equals`/`isEqual`/`compareTo` | 17 · 21 · 25 (**출력 동일**) |
| `Ex.java` (51-b) | 갭의 `getValidOffsets`/`ofStrict`, 중복의 두 오프셋, 1988년 서울의 갭·중복, `isFixedOffset`/`nextTransition`, 갭을 건너뛰는 덧셈 | 17 · 21 · 25 (**tzdb 줄만 다름**) |
| `Ex.java` (51-c) | **tzdb 판·지역 개수**, `America/Coyhaique`, **`America/Asuncion` 의 전이**, `Clock.fixed`/`offset`/`tick`, `now()` 의 나노 자릿수 | 17 · 21 · 25 (**갈림 — 13번**) |
| `Ex.java` (51-d) | `Instant` 의 단위·필드 거부, 타입 변환 실패, 파싱 형식, 시간대 ID 오류, `LocalDateTime` 비교의 역전, `ZoneOffset` 대 `ZoneId` | 17 · 21 · 25 (**출력 동일**) |
| `Ex.java` (51-e) | 고정 오프셋과 지역 ID 가 겨울에는 같고 여름에는 다른 것 | 17 · 21 · 25 (**출력 동일**) |
| `TzList.java` | 21 과 25 의 지역 ID 전체 목록을 뽑아 `diff` — 차이가 `America/Coyhaique` 하나뿐 | 21 · 25 |
| `src.zip` 열람 | `Instant`·`LocalDate`·`LocalDateTime`·`ZonedDateTime`·`Clock` 의 `@since 1.8` · `ZonedDateTime` 클래스 javadoc 의 갭/중복 절 · `Instant.plus` 의 단위 목록 | 21 |

**구현 의존 항목** (버전이 오르면 다시 돌려야 하는 것)

- ★ **tzdb 판** — 17·21 은 2024a, 25 는 2025b. **`America/Asuncion` 의 2026년 전이가 있다/없다로 갈렸다.** 시간대 계산이 걸린 테스트는 JDK 를 올릴 때마다 다시 돌려야 한다.
- ★ **`ZoneId.getAvailableZoneIds()` 의 내용** — 603 대 604.
- `Clock.systemUTC().instant()` 의 **나노 자릿수** — 이 머신·이 OS 에서는 셋 다 나노까지 나왔다. Java 8 은 밀리초였다고 알려져 있으나 **이 머신에 8 이 없어 안 돌려 봄.**
- 예외 **메시지 문구** — javadoc 이 규정하지 않는다. 세 판에서 같았지만 그것은 관찰이지 계약이 아니다.
- 스택트레이스의 **줄 번호** — 51-a 를 처음 만들었을 때 `Instant.java:567`(17) 대 `:566`(21·25) 로 갈렸다.
- **기본 시간대·Locale** — 이 머신은 `Asia/Seoul`·`ko_KR`. `TimeZone.getDefault()` 가 다른 머신에서는 (7)의 마지막 두 줄이 달라진다.
- `atStartOfDay()` 가 자정이 아닌 값을 내는 지역이 현재 tzdb 에 남아 있는지 — **안 돌려 봄**(전 지역 전 날짜를 훑어야 한다).
