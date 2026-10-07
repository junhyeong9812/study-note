# domain-modeling/12-time-money-and-units — 금액·시간·단위를 값 객체로: 개관 — 정리 (힌트)

## 해결하는 문제

금액·시각·물리량을 **맨 숫자**(`double`, `long`, `String`)로 들면, 숫자에 붙어 있어야 할 뜻이 사라진다.

```text
  맨 숫자로 들 때 잃는 것

  10.0            ← 무슨 단위? N·s 인가 lbf·s 인가 (4.45배 차이)
  1000            ← 원인가 엔인가 달러 센트인가
  0.1 + 0.2       ← double 이면 0.30000000000000004
  "2026-12-01 09:00"  ← 어느 지역의 9시인가, 그 지역 규칙은 언제 판인가
```

- 세 가지 모두 **에러 없이** 틀린 값이 된다. 컴파일도 되고 예외도 안 난다.
  - *값 객체(value object)*: 식별자 없이 값으로만 같고 다름을 판단하는 객체. Evans 『DDD』 5장의 구성 요소다. 금액·기간·좌표가 대표적이다.

쉬운 예: 요리책의 "소금 2"다.
- 2 작은술인지 2 큰술인지 2 그램인지 안 적혀 있으면, 읽는 사람이 자기 습관대로 넣는다.

똑같은 구조다.\
코드도 숫자를 받는 쪽이 "아마 이 단위겠지"라고 가정한다. 보내는 쪽과 가정이 다르면 값이 조용히 어긋난다.

실무 예:
- 정산: 거래마다 수수료를 반올림해 더한 합과, 총액에 한 번 곱한 수수료가 몇 원 다르다(아래 실험 C에서 1,000건에 13원).
- 시간: 미국 동부 지점의 시간대별 매출 그래프에서 3월 둘째 일요일에는 02시 칸이 비고, 11월 첫째 일요일에는 01시 칸이 두 배다.
- 단위: Mars Climate Orbiter(1999). 지상 소프트웨어가 추력 충격량을 lbf·s로 냈고, 항법 소프트웨어는 N·s로 읽었다(NASA MIB Phase I 보고서, 상세는 [28-dm-incidents](../28-dm-incidents/2-summary.md)).

## 동작·원리

### 1. 값 = 크기 + 단위(또는 통화·시간대)

```text
  맨 숫자                       값 객체
  ┌──────────┐                  ┌───────────────────────────┐
  │  10.0    │                  │ amount = 10.0             │
  └──────────┘                  │ unit   = POUND_FORCE_SEC  │ ← 뜻이 값에 붙어 다닌다
                                └───────────────────────────┘
  더하기: 10.0 + 10.0 = 20.0     plus(): 단위가 다르면 환산하거나 거부한다
          (뜻이 다른 둘을 더함)
```

- 이 생각은 Fowler 『Analysis Patterns』(1997)의 **Quantity** 패턴(크기 + 단위)과 **Conversion Ratio**(단위 간 환산)에서 정리됐다(3장 "Observations and Measurements" — 출판사 InformIT 목차로 장 번호 확인, 본문은 열지 못했다).
- 금액은 Quantity의 한 경우다. 단위 자리에 **통화**가 들어간다. Fowler 『PoEAA』 18장 Money 패턴이 이것이다 <https://martinfowler.com/eaaCatalog/money.html>.
- 시간도 같다. "몇 시"라는 숫자에 **어느 지역의 규칙으로 읽을지**(시간대 ID)가 붙어야 순간이 정해진다.

### 2. 세 갈래의 지도 — 이 노트는 개관, 심화는 13·14

```text
                         금액·시간·단위
          ┌──────────────────┼──────────────────┐
         금액                시간                 단위
   정밀 소수(BigDecimal       순간(Instant)        Quantity(크기+단위)
   또는 최소 단위 정수)        현지 시각 + tz ID     환산 비율
   통화별 소수 자릿수          날짜(LocalDate)      더하기 전에 환산
   반올림 모드·위치            Period vs Duration
   배분(1원 나머지)            DST 공백·중복
          │                   tzdata 갱신
          ▼                    ▼
   14-money-arithmetic-   13-instant-vs-local-
   rounding-allocation    time-and-tz-rules
```

| 갈래 | 맨 숫자로 들 때의 실패 | 값 객체가 막는 것 | 심화 |
|---|---|---|---|
| 금액 | `double` 오차, "센트" 가정, 반올림 누적 | 정밀 소수 + 통화 + 명시적 반올림 | [14](../14-money-arithmetic-rounding-allocation/2-summary.md) |
| 시간 | 시간대 없는 글자, "하루 = 24시간" 가정 | 순간·현지 시각·날짜를 타입으로 나눔 | [13](../13-instant-vs-local-time-and-tz-rules/2-summary.md) |
| 단위 | 단위가 다른 둘을 그대로 더함 | 환산하거나 거부하는 `plus` | 이 노트 §1 |

### 3. 금액 — 세 겹의 위험은 원인이 다르다

```text
  ① 표현     double 은 0.1 을 정확히 못 든다      → BigDecimal 또는 최소 단위 정수
  ② 자릿수   KRW 0자리, USD 2자리, KWD 3자리       → 통화가 자릿수를 안다
  ③ 반올림   언제(줄마다? 합계에?) 어떻게(HALF_UP? HALF_EVEN?) → 규칙으로 명시
```

- ①을 고쳐도 ②·③은 따로 남는다. `BigDecimal`로 계산해도 줄마다 반올림하면 합계와 어긋난다.
  - *은행가 반올림(HALF_EVEN)*: 딱 절반(.5)일 때 짝수 쪽으로 보내는 반올림. Java `RoundingMode.HALF_EVEN` javadoc이 "banker's rounding"이라고 부른다. 절반 값이 고르게 나오면 올림·내림이 섞여 누적 편향이 줄어든다.
- 다통화의 반올림 순서·경유 환산은 연습 문제 [advanced/05-multi-currency](../advanced/05-multi-currency/2-summary.md)가 측정으로 보였다. 여기서는 되풀이하지 않는다.

### 4. 시간 — "하루"와 "몇 시"는 지역 규칙에 달렸다

```text
  America/New_York 2026년              하루의 길이(실험 D)
  03-07 ─────────────────────── 24h
  03-08 ──────────────────── 23h        02:00~02:59 가 없다(DST 시작)
  11-01 ────────────────────────── 25h  01:00~01:59 가 두 번 있다(DST 끝)
```

- *DST(일광 절약 시간, 서머타임)*: 여름에 시계를 당기는 제도. 1시간 DST면 시작하는 날은 23시간, 끝나는 날은 25시간이다.
  - 예외도 있다. Australia/Lord_Howe는 30분 DST라 2026-04-05가 24시간 30분, 2026-10-04가 23시간 30분이다. Pacific/Apia는 2011-12-30이 통째로 없다(실측 — 관련 주제·근거의 실험 목록 재현 메모).
- 그래서 "하루 뒤"에는 두 뜻이 있다.
  - 달력 기준 하루(`Period.ofDays(1)`): 같은 현지 시각의 다음 날.
  - 정확히 24시간(`Duration.ofHours(24)`): 타임라인 위의 고정 길이.
- 규칙 자체가 데이터다. IANA tz database가 지역별 규칙을 관리하고, 나라가 제도를 바꾸면 판이 갱신된다(13번 노트).

### 실험: 맨 숫자 vs 값 객체, 반올림 누적, 하루 길이

코드(핵심, `scratchpad/dm/12/Exp12.java`):

```java
enum Unit { NEWTON_SECOND(BigDecimal.ONE), POUND_FORCE_SECOND(new BigDecimal("4.4482216152605"));
  final BigDecimal toSi; Unit(BigDecimal f) { toSi = f; } }

record Impulse(BigDecimal value, Unit unit) {
  BigDecimal si() { return value.multiply(unit.toSi); }
  Impulse plus(Impulse o) { return new Impulse(si().add(o.si()), Unit.NEWTON_SECOND); } // 더하기 전에 환산
}
record Money(long minor, Currency cur) {
  Money plus(Money o) {
    if (!cur.equals(o.cur)) throw new IllegalArgumentException("통화가 다르다: " + cur + " + " + o.cur);
    return new Money(minor + o.minor, cur);
  }
}
// C. 거래 1000건(seed 7), 수수료율 3.3%: 건별 HALF_UP 후 합 vs 총액에 한 번
perTx += BigDecimal.valueOf(amt).multiply(rate).setScale(0, RoundingMode.HALF_UP).longValue();
long once = BigDecimal.valueOf(sum).multiply(rate).setScale(0, RoundingMode.HALF_UP).longValue();
```

- 1 lbf = 4.4482216152605 N은 정의값이다(0.45359237 kg × 9.80665 m/s²).

(실험, JDK 21.0.12 temurin 컨테이너 `--cpus=2`, 2026-10-03)

```text
== A. 단위 없는 숫자 vs 단위 붙은 값
  맨 double: 받는 쪽이 쓴 값 10.0 (실제 SI 값 44.48 N·s)
  Impulse 타입: 10 lbf·s + 10 N·s = 54.48 N·s
  Money(KRW) + Money(USD) -> 통화가 다르다: KRW + USD
== B. 금액을 double로 누적
  0.01달러 100만 번: double 10000.000000171856 / BigDecimal 10000.00
== C. 정산: 건별 수수료 반올림 누적 vs 합계에 한 번 (수수료율 3.3%, HALF_UP, 원 단위)
  거래 1000건(1,000~100,000원, seed 7) 총액 51714157: 건별 합 1706580 / 합계 1회 1706567 / 차이 13원
== D. '하루' 길이 (America/New_York)
  2026-03-07 = 24시간
  2026-03-08 = 23시간
  2026-11-01 = 25시간
  Asia/Seoul 2026-03-08 = 24시간
```

관찰과 해석:
- A: 맨 `double`은 받는 쪽이 단위를 착각해도 아무 신호가 없다. 값 객체는 단위를 들고 다니므로 환산하거나(물리량) 거부한다(통화).
- B: `double` 오차는 한 번에는 작다. 100만 번 더하면 소수점 아래 일곱째 자리에 드러난다.
- C: `BigDecimal`을 써도 **반올림 위치**가 다르면 합이 다르다. 이것은 ①(표현)이 아니라 ③(반올림 규칙)의 문제다.
- D: 서울은 2026년에 DST가 없어 24시간이다. 같은 코드가 뉴욕 지점에서는 23·25시간을 만난다.

## 쓰이는 자료구조·알고리즘

- **고정 소수점 정수(최소 단위 정수)**: 금액을 그 통화의 최소 단위 개수(`long`)로 든다. 1,000원 → 1000, $10.50 → 1050. 덧셈·뺄셈은 정확하다. 곱셈(이율·환율)과 나눗셈(n등분·배분)에서 반올림·나머지가 생긴다.
- **`BigDecimal` = 정수 + 스케일**: 값 = unscaled value × 10^-scale(`BigDecimal` javadoc). 스케일까지 값의 일부라 `equals`가 갈린다 — [languages/java/syntax/53-bigdecimal](../../../languages/java/syntax/53-bigdecimal/2-summary.md) (1)(2).
- **은행가 반올림(HALF_EVEN)**: 절반에서 짝수 쪽. 모드별 표는 14번 노트.
- **tz 전이 테이블**: 지역마다 "이 순간부터 오프셋이 몇이다"의 정렬된 배열 + 반복 규칙. JDK 21 `ZoneRules`는 마지막 저장 전이 이전(과거) 시각을 이 배열에서 `Arrays.binarySearch`로 찾고, 그 이후 시각은 반복 규칙으로 그해 전이를 만들어 비교한다(13번 노트).
- **환산 비율 표**: 단위(또는 통화) 짝 → 비율. 통화 환율표가 방향 있는 그래프라는 점은 [advanced/05-multi-currency](../advanced/05-multi-currency/2-summary.md) 참고.
- 부동소수점이 왜 0.1을 못 드는지: 원고 [foundations/data-representation](../../foundations/data-representation/README.md)([architecture/03-floating-point-ieee754](../../architecture/03-floating-point-ieee754/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 도메인 개념마다 타입을 먼저 정한다

| 도메인 개념(예시) | Java(`java.time`·`java.math`) | PostgreSQL 17 | JSON 직렬화 |
|---|---|---|---|
| 결제 금액 | `Money(BigDecimal 또는 long minor, Currency)` | `numeric(19,4)` + `char(3)` 또는 `bigint` minor + `char(3)` | 문자열 `"12.30"` 또는 정수 minor + 통화 코드 |
| 결제 시각(과거 사건) | `Instant` | `timestamptz` | RFC 3339 `...Z` |
| 회의 시작(미래 일정) | `LocalDateTime` + `ZoneId` | `timestamp` + `text`(tz ID) | 현지 시각 + tz ID를 별도 필드로(원본). 한 문자열이면 RFC 9557 `2026-12-01T09:00:00-06:00[America/Winnipeg]` — 오프셋이 필수이고, 그 오프셋은 만든 시점 규칙의 계산값이다 |
| 생일·만기일 | `LocalDate` | `date` | `"1990-05-10"` |
| 무게·거리 | `Quantity(BigDecimal, Unit)` | `numeric` + 단위 열(또는 열 이름에 단위 고정) | 값 + 단위 |

- 표의 선택은 출발점이다. 시간 쪽 근거는 13번, 금액 쪽 근거는 14번, DB 타입 쪽은 [database/27-temporal-types-and-session-timezone](../../database/27-temporal-types-and-session-timezone/2-summary.md)에 있다.

### 2. 값 객체로 감싼다 — 쉬운 예

```java
public record Money(BigDecimal amount, Currency currency) {
  public Money {
    Objects.requireNonNull(currency);
    // 통화가 감당 못 하는 자릿수는 입구에서 거부한다(예: 10.5원)
    amount = amount.setScale(currency.getDefaultFractionDigits(), RoundingMode.UNNECESSARY);
  }
  public Money plus(Money o) {
    if (!currency.equals(o.currency)) throw new IllegalArgumentException("통화 불일치");
    return new Money(amount.add(o.amount), currency);
  }
  // 곱셈은 반올림이 생기므로 모드를 인자로 받는다
  public Money times(BigDecimal factor, RoundingMode mode) {
    return new Money(amount.multiply(factor).setScale(currency.getDefaultFractionDigits(), mode), currency);
  }
}
```

- `RoundingMode.UNNECESSARY`는 반올림이 필요하면 `ArithmeticException`을 던진다(javadoc). 생성자에서 "조용한 반올림"을 막는다.
- 단, `getDefaultFractionDigits()`는 XAU·XXX 같은 의사 통화에 `-1`을 돌려준다(javadoc, 실측 XAU → -1). 그러면 `setScale(-1, …)`이 되므로, 이런 통화는 생성자에서 거부하거나 자릿수를 따로 정한다.
- JPA로 저장할 때는 `@Embeddable`로 두 열에 매핑하거나 `AttributeConverter`를 쓴다. 도메인 클래스가 ORM 어노테이션에 묶이는 문제는 [02-pojo-and-persistence-ignorance](../02-pojo-and-persistence-ignorance/2-summary.md)를 본다.

### 3. 실무 예 — 경계에서 단위를 확인한다

- 외부 API·파일 경계에서 받는 숫자는 **단위·통화·시간대가 계약에 적혀 있는지** 먼저 확인한다. MCO 보고서는 인터페이스 문서(SIS)가 N·s를 요구했는데 지켜지지 않았다고 적는다.
- 진단: 코드에서 금액·시각이 맨 타입으로 남은 곳을 찾는다.

```bash
# 금액 필드가 double/float 인 곳, 시간대 없는 now() 호출
grep -rnE '(double|float)\s+\w*(amount|price|fee|total)' src/
grep -rnE 'LocalDateTime\.now\(\)|new Date\(\)' src/
```

## 장애 시나리오와 대처

### 1. 반올림 누적 → 1원(또는 몇 원) 정산 불일치 (⚠)
- 현상: 가맹점 정산 리포트의 수수료 합계와, 거래별 수수료를 더한 값이 몇 원 다르다.
- 보이는 형태: 에러 없음. 대사 배치가 "금액 불일치" 행을 낸다. 실험 C에서 1,000건에 13원.
- 원인: 한쪽은 거래마다 반올림하고, 다른 쪽은 합계에 한 번 반올림했다.
- 대처: 반올림 위치를 계약(약관·정산 규칙)으로 정하고 양쪽이 같은 규칙을 쓴다. 상세는 [14](../14-money-arithmetic-rounding-allocation/2-summary.md) §4.

### 2. DST 전환일에 시간이 비거나 겹친다 (⚠)
- 현상: 시간대별 집계에서 그날 한 칸이 비거나, 한 칸에 두 시간치가 들어간다. 일 단위 SLA 계산이 23·25시간 날에 틀린다.
- 보이는 형태: 3월 둘째 일요일·11월 첫째 일요일(미국 규칙) 그래프의 이빨 빠짐, 하루 매출의 1/24 근사가 틀림.
- 원인: "하루 = 24시간", "모든 현지 시각은 한 번씩 존재한다"는 가정.
- 대처: 집계 버킷은 순간(UTC) 기준으로 자르고 표시만 현지화하거나, 현지 날짜 기준이면 그날의 실제 길이를 `Duration.between(d.atStartOfDay(zone), d.plusDays(1).atStartOfDay(zone))`로 계산한다. `atStartOfDay(ZoneId)`는 자정이 공백인 날(예: America/Santiago 2026-09-06, 00:00이 없음)에도 그날 첫 유효 시각을 준다(javadoc). 상세는 [13](../13-instant-vs-local-time-and-tz-rules/2-summary.md).

### 3. 단위 혼동 (⚠)
- 현상: 값의 크기가 일정한 배율(4.45배, 100배, 1000배)로 틀린다.
- 보이는 형태: 예외 없음. MCO에서는 궤도 결정 결과가 점점 어긋났다. 보고서에 따르면 9월 29일에 소형 힘 ΔV가 4.45배 작게 보고됐음이 발견됐다.
- 원인: 단위 없는 숫자가 경계를 넘었다. 보내는 쪽과 받는 쪽의 단위 가정이 달랐다.
- 대처: 경계를 넘는 값에 단위를 붙인다(값 객체·필드 이름 `impulseNs`·스키마). 받는 쪽에서 범위 검사를 한다.

### 4. 통화가 다른 금액을 더했다
- 현상: 다통화 장바구니 합계가 터무니없다(원 + 달러 센트).
- 보이는 형태: 예외 없음. 결제사 금액 검증에서 거절되거나 고객이 항의한다.
- 원인: 금액이 `long`이라 통화 정보가 없다.
- 대처: `Money.plus`가 통화 불일치를 거부한다(실험 A). 환산은 별도 객체가 맡는다 — [advanced/05-multi-currency](../advanced/05-multi-currency/2-summary.md).

## 핵심 문장

- 금액·시각·물리량은 크기와 뜻(통화·시간대·단위)을 함께 든 값 객체로 다룬다. 맨 숫자는 뜻이 어긋나도 에러를 내지 않는다.
- 금액의 위험은 세 겹이다 — 표현(`double`), 통화별 자릿수, 반올림 위치. `BigDecimal`은 첫째만 고친다.
- "하루"는 지역 규칙에 따라 대개 23·24·25시간이다(30분 DST·날짜 건너뛰기 지역은 또 다르다). 달력 기준 기간(`Period`)과 고정 길이(`Duration`)를 나눠 쓴다.
- 시간대 규칙과 통화 자릿수는 코드가 아니라 데이터(IANA tz database, ISO 4217)가 정하고, 그 데이터는 갱신된다.
- 단위가 다른 값을 더하기 전에 환산하거나 거부하는 것을 타입이 맡게 한다.

## 관련 주제·근거

- 선행
  - [04-entities-and-value-objects](../04-entities-and-value-objects/2-summary.md) — 값 객체의 동등성·불변성
  - 부동소수점: [foundations/data-representation](../../foundations/data-representation/README.md) 원고, [architecture/03-floating-point-ieee754](../../architecture/03-floating-point-ieee754/2-summary.md)
- 후속
  - [13-instant-vs-local-time-and-tz-rules](../13-instant-vs-local-time-and-tz-rules/2-summary.md) — 시간 심화
  - [14-money-arithmetic-rounding-allocation](../14-money-arithmetic-rounding-allocation/2-summary.md) — 금액 심화
  - [23-versioned-rules-and-effective-dating](../23-versioned-rules-and-effective-dating/2-summary.md) — 요율·세율의 시점
  - [24-double-entry-ledger](../24-double-entry-ledger/2-summary.md) — 금액이 움직이는 기록
  - [28-dm-incidents](../28-dm-incidents/2-summary.md)
- 연결
  - [advanced/05-multi-currency](../advanced/05-multi-currency/2-summary.md) — 다통화 반올림 순서·경유 환산 측정
  - [database/27-temporal-types-and-session-timezone](../../database/27-temporal-types-and-session-timezone/2-summary.md) — DB 시간 타입과 세션 시간대
  - [languages/java/syntax/51-java-time-types](../../../languages/java/syntax/51-java-time-types/2-summary.md) · [52-duration-period-formatter](../../../languages/java/syntax/52-duration-period-formatter/2-summary.md) · [53-bigdecimal](../../../languages/java/syntax/53-bigdecimal/2-summary.md) — 문법·API 세부
- 근거
  - Evans 『Domain-Driven Design』(2003) 5장 — Value Objects
  - Fowler 『Patterns of Enterprise Application Architecture』(2002) 18장 Money <https://martinfowler.com/eaaCatalog/money.html>
  - Fowler 『Analysis Patterns』(1997) 3장 Observations and Measurements — Quantity, Conversion Ratio(목차: <https://www.informit.com/store/analysis-patterns-reusable-object-models-9780201895421>)
  - IANA Time Zone Database <https://www.iana.org/time-zones>
  - ISO 4217 목록(SIX 배포 list-one.xml, 2026-09-17 공표판) <https://www.six-group.com/dam/download/financial-information/data-center/iso-currrency/lists/list-one.xml>
  - Java SE 21 API — `java.math.RoundingMode`(HALF_EVEN = "banker's rounding"), `BigDecimal`, `java.time.Period`·`Duration`
  - NASA Mars Climate Orbiter Mishap Investigation Board Phase I Report(1999-11-10) <https://llis.nasa.gov/llis_lib/pdf/1009464main1_0641-mr.pdf> — 근본 원인 "failure to use metric units in the coding of a ground software file, 'Small Forces'", 4.45배
- 실험 목록
  - `Exp12.java` — JDK 21.0.12(eclipse-temurin:21-jdk, `--cpus=2`): 단위 값 객체 vs `double`(A), `double` 100만 회 누적(B), 수수료 건별 vs 합계 반올림 1,000건(C), New_York·Seoul 하루 길이(D)
  - 2차 리뷰 재현(같은 환경, tzdb 2026b): Lord_Howe 2026-04-05 `PT24H30M`·2026-10-04 `PT23H30M`, Apia 2011-12-30 `atStartOfDay` → `2011-12-31T00:00+14:00`, Santiago 2026-09-06 00:00 유효 오프셋 `[]`·`atStartOfDay` → `01:00-03:00`·길이 `PT23H`, `Currency XAU` 자릿수 `-1`
