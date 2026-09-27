# java/syntax/52 — `Duration`·`Period`·`DateTimeFormatter` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **선행** — [`../51-java-time-types/`](../51-java-time-types/) 의 질문을 먼저 푼다. 갭·중복을 모르면 1~4번이 안 풀린다.
> 예측형 문항의 출력은 **Temurin JDK 21.0.5** 기준이다. 세 판에서 갈린 것은 12번이 따로 묻는다.
> 이 머신의 기본 시간대는 `Asia/Seoul`, 기본 `Locale` 은 `ko_KR` 이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 서머타임이 있는 날 하루를 더하면 (예측)

```java
ZonedDateTime spring = LocalDateTime.of(2026, 3, 7, 12, 0).atZone(ZoneId.of("America/New_York"));
spring.plus(Period.ofDays(1));
spring.plus(Duration.ofDays(1));
spring.plusDays(1);
spring.plusHours(24);
```

- 네 줄의 결과는 각각 무엇인가?
- 네 줄 중 같은 답을 내는 것끼리 묶어라.
- `Period` 쪽과 `Duration` 쪽의 **실제 경과 시간**은 각각 얼마인가?
- `plusDays` 와 `plusHours(24)` 중 어느 쪽이 `Period` 쪽인가?
- 예외나 경고가 나는가?

### 2. 가을에는 반대로 틀린다 (예측)

```java
ZonedDateTime fall = LocalDateTime.of(2026, 10, 31, 12, 0).atZone(ZoneId.of("America/New_York"));
fall.plus(Period.ofDays(1));
fall.plus(Duration.ofDays(1));
```

- 두 줄의 결과는 각각 무엇인가?
- `Period` 쪽의 실제 경과 시간은 얼마인가?
- 봄과 비교해 `Duration` 쪽이 어긋나는 **방향**이 어떻게 달라지는가?
- "매일 자정에 배치"를 `Duration.ofDays(1)` 로 돌리면 1년에 몇 번 자정이 아닌가?
- 같은 코드를 `Asia/Seoul` 에서 돌리면 어떻게 되는가?

### 3. 같은 구간을 네 가지로 재면 (예측)

```java
ZonedDateTime from = LocalDateTime.of(2026, 3, 7, 12, 0).atZone(ZoneId.of("America/New_York"));
ZonedDateTime to   = LocalDateTime.of(2026, 3, 8, 12, 0).atZone(ZoneId.of("America/New_York"));
Duration.between(from, to);
ChronoUnit.DAYS.between(from, to);
ChronoUnit.HOURS.between(from, to);
Period.between(from.toLocalDate(), to.toLocalDate());
```

- 네 줄의 결과는 각각 무엇인가?
- 23시간밖에 안 흘렀는데 `DAYS.between` 이 1 인 이유는 무엇인가?
- `Period.between` 이 `ZonedDateTime` 을 직접 못 받는 이유는 무엇인가?
- 넷 중 "실제로 흐른 시간"을 답하는 것은 어느 것인가?
- "며칠 지났나"를 세려면 어느 것을 골라야 하는가?

### 4. `ChronoUnit.between` 의 버림 (예측)

```java
LocalDateTime t1 = LocalDateTime.of(2026, 1, 31, 10, 0);
LocalDateTime t2 = LocalDateTime.of(2026, 3, 1, 15, 30);
ChronoUnit.DAYS.between(t1, t2);
ChronoUnit.HOURS.between(t1, t2);
ChronoUnit.MONTHS.between(t1, t2);
ChronoUnit.DAYS.between(t2, t1);
```

- 네 줄의 결과는 각각 무엇인가?
- 실제 간격은 며칠 몇 시간 몇 분인가?
- 버림은 **내림**인가 **0 방향 절사**인가 — 넷째 줄이 그 답이다?
- "30일 무료 체험"을 `DAYS.between < 30` 으로 쓰면 무엇이 어긋나는가?
- javadoc 은 이 계산을 뭐라고 적는가?

### 5. `Duration` 과 `Period` 를 섞으면 (예측)

```java
Duration.ofHours(1).plus(Duration.ofMinutes(30));
Duration.ofHours(1).plus(Period.ofDays(1));
Period.ofDays(1).plus(Period.ofMonths(1));
Period.ofDays(1).plus(Duration.ofHours(1));
LocalDate.of(2026,1,31).plus(Duration.ofDays(1));
LocalDate.of(2026,1,31).plus(Period.ofDays(1));
```

- 여섯 줄 중 성공하는 것과 실패하는 것을 가르라.
- 실패하는 것들은 **컴파일 에러인가 런타임 예외인가** — 각각 무엇인가?
- 왜 한쪽은 컴파일에서, 다른 쪽은 런타임에서 막히는가?
- `LocalDate.plus(Duration.ofDays(1))` 의 메시지에 `Seconds` 가 나오는 이유는 무엇인가?
- "1개월 3시간"을 한 값으로 표현할 수 있는가?

### 6. `toString` 이 예상과 다르다 (예측)

```java
Duration.ofDays(1);
Period.ofDays(1);
Period.ofWeeks(2);
Duration.ofHours(25);
Duration.ofHours(25).toDaysPart();
Duration.ofHours(25).toHoursPart();
Period.ofMonths(1).getDays();
```

- 일곱 줄의 결과는 각각 무엇인가?
- `Duration.ofDays(1)` 이 `P1D` 가 아닌 이유는 무엇인가?
- `Period.ofWeeks(2)` 가 `P2W` 가 아닌 이유는 무엇인가?
- `Duration.getUnits()` 와 `Period.getUnits()` 는 각각 무엇을 돌려주는가?
- `Period.ofMonths(1).getDays()` 가 0 인 이유는 무엇인가?

### 7. `Period` 는 정규화되지 않는다 (경계)

```java
Period p = Period.between(LocalDate.of(2026, 1, 31), LocalDate.of(2026, 3, 1));
p;                p.getDays();       p.toTotalMonths();
ChronoUnit.DAYS.between(LocalDate.of(2026,1,31), LocalDate.of(2026,3,1));
Period.of(0, 13, 0);   Period.of(0, 13, 0).normalized();
```

- `p` 는 무엇인가?
- `p.getDays()` 는 무엇이고, 그것이 왜 "총 일수"가 아닌가?
- 실제 총 일수는 얼마인가?
- `normalized()` 는 무엇을 정리하고 무엇을 안 하는가, 왜인가?
- `Period.of(0,1,0).equals(Period.ofDays(30))` 은 무엇인가?

### 8. `YYYY` 와 `yyyy` 를 연말에 찍으면 (예측)

```java
DateTimeFormatter big   = DateTimeFormatter.ofPattern("YYYY-MM-dd", Locale.ENGLISH);
DateTimeFormatter small = DateTimeFormatter.ofPattern("yyyy-MM-dd", Locale.ENGLISH);
for (LocalDate d = LocalDate.of(2025, 12, 25); !d.isAfter(LocalDate.of(2026, 1, 6)); d = d.plusDays(1)) {
    System.out.println(d + "  " + d.format(small) + "  " + d.format(big));
}
```

- 열세 날 중 두 값이 **다른** 날은 며칠이며 어느 날인가?
- 다른 날의 `YYYY` 값은 무엇인가?
- 1월 쪽에서도 어긋나는가?
- 이 패턴을 로그 파일명에 쓰면 정렬 순서가 어떻게 되는가?
- `Locale` 을 안 주고 기본값(`ko_KR`)으로 돌리면 결과가 달라지는가?

### 9. 같은 `YYYY` 가 `Locale` 에 또 달렸다 (예측)

```java
LocalDate probe = LocalDate.of(2026, 12, 27);   // 일요일
for (Locale loc : new Locale[]{Locale.ENGLISH, Locale.FRANCE, Locale.KOREA}) {
    probe.format(DateTimeFormatter.ofPattern("YYYY", loc));
}
probe.get(IsoFields.WEEK_BASED_YEAR);
```

- 세 `Locale` 의 `YYYY` 는 각각 무엇인가?
- 갈리는 이유는 `WeekFields` 의 어느 두 값 때문인가?
- 세 `Locale` 의 `firstDayOfWeek` 와 `minimalDaysInFirstWeek` 는 각각 무엇인가?
- `IsoFields.WEEK_BASED_YEAR` 는 무엇을 돌려주며, 세 `Locale` 중 어느 것과 같은가?
- ISO 8601 주 기반 연도를 확실히 얻으려면 무엇을 써야 하는가?

### 10. 비슷하게 생긴 패턴 글자 (예측)

```java
ZonedDateTime z = LocalDateTime.of(2026, 3, 8, 16, 5, 9).atZone(ZoneId.of("Asia/Seoul"));
z.format(DateTimeFormatter.ofPattern("MM/dd", Locale.ENGLISH));
z.format(DateTimeFormatter.ofPattern("mm/DD", Locale.ENGLISH));
z.format(DateTimeFormatter.ofPattern("HH:mm", Locale.ENGLISH));
z.format(DateTimeFormatter.ofPattern("hh:mm", Locale.ENGLISH));
z.format(DateTimeFormatter.ofPattern("z", Locale.ENGLISH));
z.format(DateTimeFormatter.ofPattern("Z", Locale.ENGLISH));
z.format(DateTimeFormatter.ofPattern("XXX", Locale.ENGLISH));
z.format(DateTimeFormatter.ofPattern("VV", Locale.ENGLISH));
```

- 여덟 줄의 결과는 각각 무엇인가?
- `M`/`m`·`D`/`d`·`H`/`h` 의 뜻은 각각 무엇인가?
- `hh:mm` 만 쓰면 무엇이 사라지는가?
- `z`·`Z`·`X`·`V` 는 각각 무엇을 찍는가?
- `u` 와 `y` 는 언제 갈리는가?

### 11. `ResolverStyle` 과 포맷 실패 (예측)

```java
DateTimeFormatter f = DateTimeFormatter.ofPattern("uuuu-MM-dd", Locale.ENGLISH);
LocalDate.parse("2026-02-30", f.withResolverStyle(ResolverStyle.STRICT));
LocalDate.parse("2026-02-30", f.withResolverStyle(ResolverStyle.SMART));
LocalDate.parse("2026-02-30", f.withResolverStyle(ResolverStyle.LENIENT));
LocalDate.parse("2026-03-08", DateTimeFormatter.ofPattern("yyyy-MM-dd", Locale.ENGLISH).withResolverStyle(ResolverStyle.STRICT));
LocalDate.of(2026,3,8).format(DateTimeFormatter.ISO_DATE_TIME);
LocalDateTime.of(2026,3,8,16,30).format(DateTimeFormatter.ISO_INSTANT);
Instant.parse("2026-03-08T07:30:00Z").format(DateTimeFormatter.ISO_LOCAL_DATE);
```

- 세 `ResolverStyle` 로 2월 30일을 파싱하면 각각 무엇이 나오는가?
- 기본 `ResolverStyle` 은 무엇인가?
- `STRICT` 에서 `yyyy` 가 거부되는 이유는 무엇이고, 대신 무엇을 써야 하는가?
- 마지막 세 줄은 각각 무엇으로 실패하는가 — 그중 하나는 컴파일에서 막힌다, 어느 것인가?
- `Instant` 를 포맷하려면 어떻게 해야 하는가?

### 12. 세 JDK 에서 무엇이 달랐나 (경계)

- 17·21·25 에서 `tzdb` 판은 각각 무엇인가?
- `DateTimeParseException` 의 메시지가 세 판에서 어떻게 갈렸는가?
- 갈린 부분은 메시지의 **어느 조각**인가?
- 그래서 예외 메시지를 테스트로 고정하면 무슨 일이 생기는가?
- 예외 **타입**은 계약인가?

### 13. 어느 것을 고르는가 (연결)

- HTTP 클라이언트 타임아웃 — `Duration` 인가 `Period` 인가?
- "한 달 무료 체험" 만료일 — 무엇으로 계산하는가, 30일과 어떻게 다른가?
- 나이 계산 — 무엇을 쓰는가?
- 두 로그 줄의 시각 차이 — 무엇을 쓰는가?
- 파티션 키로 쓸 `2026-03-08` 문자열 — 어떤 포매터를 쓰는가, 왜 `ofPattern` 을 피하는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
