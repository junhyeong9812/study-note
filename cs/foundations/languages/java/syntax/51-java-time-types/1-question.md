# java/syntax/51 — `java.time` — `Instant`·`LocalDate`/`LocalDateTime`·`ZonedDateTime` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **선행** — 없다. 이어지는 주제는 [`../52-duration-period-formatter/`](../52-duration-period-formatter/)다.
> 예측형 문항의 출력은 **Temurin JDK 21.0.5** 기준이다. 17·25 에서 갈린 것은 그 문항에 표시돼 있다.
> 이 머신의 기본 시간대는 `Asia/Seoul`, 기본 `Locale` 은 `ko_KR` 이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 같은 순간을 세 지역에서 보면 (예측)

```java
Instant t = Instant.parse("2026-03-08T07:30:00Z");
t.atZone(ZoneId.of("Asia/Seoul"));
t.atZone(ZoneId.of("America/New_York"));
t.atZone(ZoneOffset.UTC);
```

- 세 줄의 `toString` 은 각각 무엇인가?
- 뉴욕이 `-05:00` 이 아니라 `-04:00` 인 이유는 무엇인가?
- `Instant.toString()` 이 항상 `Z` 로 끝나는 이유는 무엇인가?
- 세 값의 `toEpochSecond()` 는 같은가 다른가?
- `ZonedDateTime` 의 `toString` 에 대괄호가 붙는 것은 무엇인가?

### 2. 같은 `LocalDateTime` 을 네 지역에 붙이면 (예측)

```java
LocalDateTime meeting = LocalDateTime.of(2026, 3, 8, 16, 30);
for (String z : new String[]{"Asia/Seoul", "Europe/Paris", "America/New_York", "UTC"}) {
    System.out.println(meeting.atZone(ZoneId.of(z)).toEpochSecond());
}
```

- 네 값은 같은가 다른가?
- 가장 이른 것과 늦은 것의 차이는 몇 시간인가?
- 그래서 `LocalDateTime` 을 DB 에 저장할 때 무엇을 같이 저장해야 하는가?
- 반대로 `LocalDateTime` 이 **맞는** 값은 어떤 것인가, 예를 셋 들어라.
- `LocalDateTime` 을 "순간"이라고 부르면 안 되는 이유를 한 문장으로?

### 3. 존재하지 않는 시각을 만들면 (예측)

```java
LocalDateTime gap = LocalDateTime.of(2026, 3, 8, 2, 30);
ZoneId ny = ZoneId.of("America/New_York");
gap.atZone(ny);
ny.getRules().getValidOffsets(gap);
ZonedDateTime.ofStrict(gap, ZoneOffset.ofHours(-5), ny);
```

- `atZone` 은 무엇을 돌려주는가 — 예외인가 값인가?
- `getValidOffsets` 는 무엇을 돌려주는가?
- `ofStrict` 는 무엇을 던지며 메시지는 무엇인가?
- 오프셋을 `-04:00` 으로 바꾸면 `ofStrict` 의 결과가 달라지는가?
- 사용자 입력을 **거부**하려면 무엇을 써야 하는가?

### 4. 시계가 뒤로 갈 때 — 두 번 있는 시각 (예측)

```java
LocalDateTime dup = LocalDateTime.of(2026, 11, 1, 1, 30);
ZonedDateTime d1 = dup.atZone(ZoneId.of("America/New_York"));
d1.withEarlierOffsetAtOverlap();
d1.withLaterOffsetAtOverlap();
```

- `getValidOffsets(dup)` 의 크기는 얼마인가?
- `atZone` 은 둘 중 어느 쪽을 고르는가?
- 두 `ZonedDateTime` 의 `toEpochSecond` 차이는 얼마인가?
- 두 값의 `toLocalDateTime()` 은 같은가, `equals` 는 어떤가, `isEqual` 은 어떤가?
- `Transition.getDuration()` 이 갭과 중복에서 어떻게 다른가?

### 5. 한국에 서머타임이 있었나 (경계)

```java
LocalDateTime.of(1988, 5, 8, 2, 30).atZone(ZoneId.of("Asia/Seoul"));
ZoneId.of("Asia/Seoul").getRules().isFixedOffset();
ZoneId.of("Asia/Seoul").getRules().nextTransition(Instant.parse("2026-01-01T00:00:00Z"));
```

- 첫 줄의 결과는 무엇인가?
- `isFixedOffset()` 은 무엇을 돌려주는가, 그리고 그것이 왜 함정인가?
- `nextTransition` 은 무엇을 돌려주는가?
- "오늘 서울에는 DST 가 없다"를 코드로 판정하려면 무엇을 물어야 하는가?
- 1988년 데이터를 `+09:00` 고정으로 처리하면 무엇이 틀리는가?

### 6. 불변성과 달 단위 덧셈 (예측)

```java
LocalDate base = LocalDate.of(2026, 1, 31);
base.plusMonths(1);
base.plusMonths(1).plusMonths(1);
base.plusMonths(2);
```

- 세 줄의 결과는 각각 무엇인가?
- `base` 자체는 어떻게 되는가?
- `plusMonths(1).plusMonths(1)` 과 `plusMonths(2)` 가 다른 이유는 무엇인가?
- 2월 31일을 요구했는데 예외가 안 나는 것은 3번의 갭 처리와 어떤 공통점이 있는가?
- 불변이라서 얻는 것과 치르는 것은 각각 무엇인가?

### 7. `Instant` 에 무엇을 더할 수 있나 (경계)

```java
Instant t = Instant.parse("2026-03-08T07:30:00Z");
t.plus(1, ChronoUnit.DAYS);
t.plus(1, ChronoUnit.MONTHS);
t.plus(Period.ofDays(1));
t.plus(Period.ofMonths(1));
t.getLong(ChronoField.YEAR);
t.truncatedTo(ChronoUnit.MONTHS);
```

- 여섯 줄 중 성공하는 것은 무엇이고 실패하는 것은 무엇인가?
- 실패하는 것들의 예외 타입과 메시지는 무엇인가?
- `DAYS` 가 되는데 `MONTHS` 가 안 되는 이유는 무엇인가?
- `Instant` 에게 "하루"는 정확히 무엇인가?
- 지역 달력 기준으로 한 달을 더하려면 어떻게 해야 하는가?

### 8. `get` 과 `getLong` 이 왜 다른가 (왜)

```java
Instant t = Instant.parse("2026-03-08T07:30:00Z");
t.isSupported(ChronoField.INSTANT_SECONDS);   // ?
t.get(ChronoField.INSTANT_SECONDS);           // ?
t.getLong(ChronoField.INSTANT_SECONDS);       // ?
```

- 세 줄의 결과는 각각 무엇인가?
- `isSupported` 가 `true` 인데 `get` 이 던지는 이유는 무엇인가?
- 예외 타입과 메시지는 무엇인가?
- `t.isSupported(ChronoField.YEAR)` 는 무엇이고, 위와 어떻게 다른 실패인가?
- 그래서 필드를 꺼낼 때의 규칙은 무엇인가?

### 9. 시간대 ID 문자열 (경계)

```java
ZoneId.of("KST");
ZoneId.of("Asia/Soul");
ZoneId.of("UTC+9");
ZoneId.of("+09:00");
```

- 네 줄 중 던지는 것은 무엇이고 통과하는 것은 무엇인가?
- 던지는 것의 예외 타입은 무엇인가?
- 약어와 오타를 코드에서 구분할 수 있는가?
- `"+09:00"` 이 통과했을 때 얻은 것은 `ZoneId` 인가 무엇인가, 무엇이 빠져 있는가?
- 그래서 어떻게 방어하는가?

### 10. `ZoneOffset` 과 `ZoneId` 를 바꿔 쓰면 (예측)

```java
LocalDateTime.of(2026, 7, 1, 12, 0).atOffset(ZoneOffset.ofHours(-5)).toInstant();
LocalDateTime.of(2026, 7, 1, 12, 0).atZone(ZoneId.of("America/New_York")).toInstant();
```

- 두 값은 같은가 다른가, 차이는 얼마인가?
- 왜 그렇게 되는가?
- 겨울 날짜(1월 1일)로 바꾸면 어떻게 되는가? (돌려 보고 답하라)
- 언제 `ZoneOffset` 을 쓰는 것이 맞는가?
- `OffsetDateTime` 필드로 미래 약속을 저장하면 무엇이 위험한가?

### 11. `equals` 와 `isEqual` 과 `compareTo` (경계)

```java
ZonedDateTime seoul = Instant.parse("2026-03-08T07:30:00Z").atZone(ZoneId.of("Asia/Seoul"));
ZonedDateTime ny    = Instant.parse("2026-03-08T07:30:00Z").atZone(ZoneId.of("America/New_York"));
```

- `seoul.equals(ny)` 는 무엇인가?
- `seoul.isEqual(ny)` 는 무엇인가?
- `seoul.compareTo(ny)` 는 무엇인가?
- 이 셋이 어긋나면 `TreeSet` 에서 무슨 일이 생기는가?
- 순간만 비교하려면 무엇으로 정규화해야 하는가?

### 12. `now()` 를 테스트하려면 (연결)

```java
Clock fixed = Clock.fixed(Instant.parse("2026-03-08T07:30:00Z"), ZoneId.of("Asia/Seoul"));
LocalDate.now(fixed);
LocalDate.now(fixed.withZone(ZoneId.of("America/New_York")));
```

- `Clock` 이 들고 있는 것은 몇 가지인가?
- 두 줄의 결과는 같은가 다른가?
- `Instant.now(clock)` 을 두 번 부르면 같은 값인가?
- `Clock.offset` 과 `Clock.tick` 은 각각 무엇을 하는가?
- `now()` 를 직접 부르는 코드의 테스트는 언제 깨지는가?

### 13. 같은 코드가 JDK 마다 다른 답을 낸 곳 (경계)

```java
ZoneRulesProvider.getVersions("Asia/Seoul").lastKey();
ZoneId.of("America/Coyhaique");
ZoneId.of("America/Asuncion").getRules().nextTransition(Instant.parse("2025-01-01T00:00:00Z"));
```

- 17·21·25 에서 첫 줄은 각각 무엇을 돌려주는가?
- 둘째 줄은 세 판에서 어떻게 갈리는가?
- 셋째 줄은 세 판에서 어떻게 갈리는가 — 이쪽이 왜 더 위험한가?
- 세 판의 사용 가능한 지역 개수는 각각 얼마인가?
- 그래서 "시간대 계산 결과"는 보장인가 아닌가?

### 14. 어느 타입을 고르는가 (연결)

- 주문 생성 시각을 DB 에 넣는다 — 무엇을 쓰는가?
- 사용자의 생일을 저장한다 — 무엇을 쓰는가?
- "매일 오전 7시" 알람을 저장한다 — 무엇을 쓰는가?
- 6개월 뒤 뉴욕에서 열리는 회의를 저장한다 — 무엇을 쓰는가, `Instant` 로 저장하면 무엇이 위험한가?
- `java.util.Date`·`SimpleDateFormat` 를 쓰면 안 되는 이유를 둘 들어라.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
