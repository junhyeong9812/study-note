# domain-modeling/14-money-arithmetic-rounding-allocation — 금액 연산: 자릿수·반올림 모드·반올림 위치·배분·직렬화 — 정리 (힌트)

## 해결하는 문제

금액은 정확한 타입(`BigDecimal`·최소 단위 정수)으로 들어도 **나누고 곱하는 순간** 반올림이 생긴다. 반올림을 어디서 어떻게 하는지 정하지 않으면 돈이 생기거나 사라진다.

```text
  10,000원을 3명에게
    각자 10000/3 = 3333.33… → 3333   3333 × 3 = 9,999      ← 1원이 사라짐
  최대 잔여 배분
    3334, 3333, 3333                                      합 10,000
```

- 같은 종류의 어긋남이 여러 자리에서 생긴다.
  - 줄마다 세금을 반올림한 합 ≠ 합계에 한 번 매긴 세금
  - 할인 → 세금 순서 ≠ 세금 → 할인 순서
  - 통화마다 소수 자릿수가 다르다(JPY 0, KWD 3)
  - `BigDecimal("1.0").equals(new BigDecimal("1.00"))`이 `false`

쉬운 예: 피자 한 판 값을 셋이 나눠 낸다.
- 1원 단위 지폐는 없고 누군가 1원을 더 내야 한다. 누가 낼지 정하지 않으면 1원이 빈다.

똑같은 구조다.\
**곱셈(비례 요금)** 과 **배분(정해진 총액을 나눔)** 은 다른 연산이다. Fowler는 "multiplication works well for the former, but an allocator works better for the latter"라고 썼다(PoEAA Money 초안, 아래 근거).

실무 예:
- 주문서는 줄별 세금 합(33원)을 보내고 PG는 합계 기준 세금(32원)을 기대해 금액 불일치로 결제가 거절된다.
- 부분 환불에서 할인액을 상품별로 나누다 1원이 남는다.
- 해외 통화 결제에서 JPY·KWD를 소수 2자리로 가정해 금액이 틀린다.

## 동작·원리

### 1. 금액 표현 두 가지 — 둘 다 "정확한 소수"다

```text
  최소 단위 정수(long)              BigDecimal (unscaled × 10^-scale)
  KRW 1,000      → 1000             1000        (scale 0)
  USD 12.30      → 1230 센트        12.30       (unscaled 1230, scale 2)
  KWD 1.234      → 1234 필스        1.234       (unscaled 1234, scale 3)
```

- 덧셈·뺄셈은 둘 다 정확하다. 차이는 곱셈·나눗셈에서 반올림을 어디서 하느냐다.
- `BigDecimal`의 스케일·`equals`·생성 방법은 [java/syntax/53-bigdecimal](../../../languages/java/syntax/53-bigdecimal/2-summary.md)에 있다. 최소 단위 정수 + 통화로 다통화를 다루는 연습은 [advanced/05-multi-currency](../advanced/05-multi-currency/2-summary.md)에 있다. 여기서는 되풀이하지 않는다.

### 2. 통화별 소수 자릿수 — ISO 4217 "minor unit"

| 통화 | ISO 4217 minor unit(2026-09-17 공표 목록) | JDK 21 `getDefaultFractionDigits()` |
|---|---|---|
| KRW | 0 | 0 |
| JPY | 0 | 0 |
| USD·EUR | 2 | 2 |
| KWD·BHD | 3 | 3 |
| CLF | 4 | 4 |

- *minor unit*: 그 통화의 최소 단위가 소수 몇째 자리인가. ISO 4217 목록의 `CcyMnrUnts` 칸이다.
- JDK 21.0.12의 `java.util.Currency`는 실험 E에서 위 표와 같은 값을 냈다.
- 주의: 결제사마다 특정 통화의 실제 처리 자릿수를 ISO와 다르게 두는 예외가 있다(adv/05가 인용한 Stripe 문서). 결제사 연동에서는 그 결제사의 표가 기준이다.

### 3. 반올림 모드 — 기본값이 없다

(실험 D, JDK 21.0.12 — `new BigDecimal(v).setScale(0, mode)`)

```text
  값    HALF_UP   HALF_EVEN HALF_DOWN DOWN      FLOOR     CEILING   
  2.5   3         2         2         2         2         3         
  3.5   4         4         3         3         3         4         
  -2.5  -3        -2        -2        -2        -3        -2        
  2.4   2         2         2         2         2         3         
  2.6   3         3         3         2         2         3         
  setScale(0) 모드 없이 -> Rounding necessary
  10000.divide(3) 모드 없이 -> Non-terminating decimal expansion; no exact representable decimal result.
```

- *HALF_UP*: 절반이면 0에서 먼 쪽. 학교에서 배우는 반올림. 음수 -2.5 → -3.
- *HALF_EVEN*: 절반이면 짝수 쪽. javadoc이 "banker's rounding"이라 부른다. 2.5 → 2, 3.5 → 4.
- *DOWN*은 0 쪽으로 자르고, *FLOOR*는 음의 무한대 쪽으로 자른다. 음수에서 갈린다(-2.5 → -2 vs -3).
- `setScale(n)`·`divide(x)`처럼 모드를 받는 연산에서 모드를 빼면, 반올림이 필요할 때 `ArithmeticException`이다. 조용히 반올림하지 않는다.
- 단, 조용히 줄이는 경로도 있다(JDK 21.0.12·PostgreSQL 17.11 재현).
  - `new MathContext(1)`은 기본 모드가 HALF_UP이다(javadoc): `new BigDecimal("2.5").round(new MathContext(1))` → `3`. `MathContext.DECIMAL64`·`DECIMAL128`은 HALF_EVEN이다.
  - `longValue()`·`intValue()`는 소수부를 버린다(javadoc): `2.5` → `2`, `-2.7` → `-2`.
  - PostgreSQL `numeric(19,4)` 열에 `1.23455`를 넣으면 예외 없이 `1.2346`이 된다(문서 8.1.2 "the system will round the value").
- DB도 다르다. PostgreSQL 17에서 `round(2.5::numeric)` = 3, `round(2.5::float8)` = 2, `round(-2.5::numeric)` = -3이었다(로컬 재현). 17판 문서는 `numeric`의 동률을 "0에서 먼 쪽", `double precision`은 플랫폼 의존(대개 짝수 쪽)이라고 적는다. 앱과 DB가 같은 금액을 각자 반올림하면 이 차이가 드러난다.

### 4. 반올림 위치 — 줄마다인가, 합계에 한 번인가

```text
  가격 105, 105, 105  세율 10%  HALF_UP

  줄마다      10.5→11  10.5→11  10.5→11   합 33
  합계에 한 번          315 × 0.1 = 31.5 → 32
                                         ^ 1원 차이
```

(실험 B, JDK 21.0.12)

```text
== B. 줄 단위 반올림 vs 합계 후 반올림 (부가세 10%, HALF_UP)
  가격 [105, 105, 105]: 줄별 세액 합 33 / 합계 세액 32
  무작위 주문 10000건(줄 1~10, 가격 100~100,099원, seed 42): 세액 불일치 4309건, 최대 4원
```

- 무작위 주문의 43%에서 두 방식의 세액이 달랐다. 한 건 최대 4원.
- 어느 쪽이 맞는지는 코드가 아니라 **세법·약관·결제사 계약**이 정한다. 코드는 그 결정을 한 곳(정책 객체)에 두고 양쪽(주문·결제·정산)이 같은 것을 쓰게 한다.
- 줄별 금액을 보여 주면서 합계도 맞추고 싶으면, 합계 세액을 정한 뒤 **줄에 배분**한다(§5). 그러면 세로 합과 합계가 같다.

### 5. 할인·세금 계산 순서

(실험 C, JDK 21.0.12 — 단계마다 HALF_UP으로 원 단위)

```text
== C. 할인·세금 순서 (가격 9,999원, 할인 15%, 세율 10%, 단계마다 HALF_UP으로 원 단위)
  할인→세금: 8499 → 9349   세금→할인: 10999 → 9349
  가격 1~100,000원 전수: 15% 할인·10% 세금 순서로 결과가 갈린 가격 33000개, 1만 원 이상 첫 예 10005원
    10005원: 할인→세금 8504 → 9354 / 세금→할인 11006 → 9355
  정액 할인 100원(가격 1,000): 할인→세금 990 / 세금→할인 1000
```

- 정률 할인과 정률 세금은 정확히 계산하면 순서가 상관없다(곱셈은 교환 가능). 그런데 **단계마다 반올림**하면 1~100,000원 중 33%에서 1원이 갈렸다.
- 정액 할인은 반올림이 없어도 순서가 결과를 바꾼다(990 vs 1000). 할인이 세금 기준액을 줄이느냐의 문제라 법·약관이 정한다.

### 6. 배분 — 곱셈이 아니라 allocator

```text
  Fowler 의 문제(Matt Foemmel's conundrum): 5센트를 70% : 30% 로
    3.5 → 4,  1.5 → 2   합 6 (1센트 생김)       둘 다 내림: 3 + 1 = 4 (1센트 사라짐)

  배분기: 내림한 뒤 남은 몫(1)을 규칙에 따라 한 칸에 준다 → 4, 1   합 5
```

- Fowler의 PoEAA Money 초안(ISA 판)에는 두 배분기가 있다.
  - `allocate(int n)`: 같은 몫 n개. 나머지를 앞 칸부터 1씩.
  - `allocate(long[] ratios)`: 비율 배분. 각 칸을 내림하고, 남은 몫을 **앞 칸부터** 1씩 준다.
- 본문은 "scattering pennies across the allocated monies in a way that looks pseudo-random from the outside"라고 쓰지만, 같은 글의 코드 예시는 앞 칸부터 준다. 규칙이 정해져 있다면(예: 금액이 큰 칸 우선) 그 규칙을 코드로 옮겨야 한다.
- *최대 잔여 방식(largest remainder, Hamilton 방식)*: 각 칸을 내림한 뒤, 버린 소수 부분(잔여)이 큰 칸부터 1씩 준다. 정확한 비례값에 가장 가까운 정수 배분 중 하나다.

(실험 A, JDK 21.0.12)

```text
== A. 10,000원을 3명에게
  나눗셈 후 각자 반올림: 3333 x3 = 9999 (소실 1원)
  최대 잔여: [3334, 3333, 3333] 합 10000
  1:2:3 정확값 [1666.6667, 3333.3333, 5000.0000] -> 각자 HALF_UP [1667, 3333, 5000] 합 10000
  1:2:3 최대 잔여 [1667, 3333, 5000] 합 10000
  100원 6명 [17, 17, 17, 17, 16, 16] 합 100
  100원 비율 [1, 1, 1]: 각자 HALF_UP [33, 33, 33] 합 99 / 최대 잔여 [34, 33, 33] 합 100
  5원 비율 [1, 1]: 각자 HALF_UP [3, 3] 합 6 / 최대 잔여 [3, 2] 합 5
  10원 비율 [1, 1, 1, 1, 1, 1]: 각자 HALF_UP [2, 2, 2, 2, 2, 2] 합 12 / 최대 잔여 [2, 2, 2, 2, 1, 1] 합 10
  5 비율 [7, 3]: Fowler(앞 칸부터) [4, 1] / 최대 잔여 [4, 1]
  7 비율 [2, 3, 5]: Fowler(앞 칸부터) [2, 2, 3] / 최대 잔여 [1, 2, 4]
```

- 각자 반올림은 우연히 맞을 때도 있다(1:2:3). 그러나 1원이 사라지거나(합 99) 생긴다(합 6, 12). 합이 맞는다는 보장이 없다.
- 배분기는 **합 = 총액**을 보장한다. 남은 몫을 누구에게 주느냐는 방식마다 다르다(7을 2:3:5 → Fowler `[2,2,3]`, 최대 잔여 `[1,2,4]`). 정확값은 1.4·2.1·3.5라 최대 잔여 쪽이 비례에 더 가깝다.

### 7. 직렬화 — 경계에서 정밀도와 스케일을 잃는다

(실험, Node.js v18.19.1, 2026-10-03)

```text
숫자로 받은 값  : 9007199254740992  원문과 같나? false
문자열로 받은 값: 9007199254740993  BigInt -> 9007199254740993
0.1 + 0.2 = 0.30000000000000004
19.99 * 100 = 1998.9999999999998  Math.round -> 1999
1.005.toFixed(2) = 1.00
Number.MAX_SAFE_INTEGER = 9007199254740991
```

- JSON 숫자를 JS `Number`(IEEE 754 double)로 읽으면 2^53을 넘는 정수와 대부분의 소수가 정확하지 않다. `1.005.toFixed(2)`가 `1.00`인 것도 1.005가 double로 1.00499…이기 때문이다.
- 그래서 금액은 **문자열**(`"12.30"`)이나 **최소 단위 정수 + 통화 코드**로 주고받는 관행이 있다. 정수도 `Number.MAX_SAFE_INTEGER`(9,007,199,254,740,991)를 넘을 수 있는 단위면 문자열로 둔다.
- 스케일도 정보다. Java 쪽에서 `new BigDecimal("100").stripTrailingZeros()`는 `1E+2`가 되고 `toString()`이 지수 표기를 낸다(실험 F). 직렬화에는 `toPlainString()`을 쓰거나 통화 자릿수로 `setScale`한 값을 쓴다.

## 쓰이는 자료구조·알고리즘

- **고정 소수점 정수**: 최소 단위 `long`. 덧셈 정확, 오버플로 범위만 확인(`Math.addExact`).
- **`BigDecimal`**: 임의 정밀도 정수(unscaled value)와 `int` 스케일. 연산마다 결과 스케일 규칙이 있다(javadoc, [java/syntax/53](../../../languages/java/syntax/53-bigdecimal/2-summary.md) 「연산이 스케일을 어떻게 정하는가」).
- **최대 잔여 배분**: n칸 내림 O(n) + 잔여 기준 정렬 O(n log n) + 남은 몫(< n) 분배. 동률이면 순번 등 결정적 규칙으로 정한다(아래 코드는 앞 순번).
- **반올림 모드 = 전략 객체**: `RoundingMode`를 값으로 주입한다. 정책이 바뀌면 그 값만 바뀐다.
- **해시 동등성과 스케일**: `HashSet`은 `equals`·`hashCode`를, `TreeSet`은 `compareTo`를 쓴다. 스케일만 다른 금액이 한쪽에서는 둘, 다른 쪽에서는 하나다(실험 F).

## 적용 — 풀어나가는 법

### 1. 쉬운 예 — Money에 배분을 넣는다

```java
public record Money(long minor, Currency currency) {
  /** 최대 잔여 배분: 합 == this 를 보장한다. 동률은 앞 순번 우선. */
  public List<Money> allocate(long... weights) {
    long sumW = Arrays.stream(weights).sum();
    long[] out = new long[weights.length], rem = new long[weights.length];
    long given = 0;
    for (int i = 0; i < weights.length; i++) {
      out[i] = Math.floorDiv(Math.multiplyExact(minor, weights[i]), sumW);
      rem[i] = Math.floorMod(Math.multiplyExact(minor, weights[i]), sumW);
      given += out[i];
    }
    Integer[] idx = IntStream.range(0, weights.length).boxed().toArray(Integer[]::new);
    Arrays.sort(idx, (x, y) -> rem[y] != rem[x] ? Long.compare(rem[y], rem[x]) : Integer.compare(x, y));
    for (int k = 0; k < minor - given; k++) out[idx[k]]++;
    return Arrays.stream(out).mapToObj(v -> new Money(v, currency)).toList();
  }
}
```

- 실험 A의 `allocate` 함수와 같은 알고리즘이다(실험 코드는 `scratchpad/dm/12/Exp14.java`).
- 테스트는 불변식 하나로 쓴다: **배분 결과의 합 == 원래 금액**, 각 몫과 정확한 비례값의 차이 < 1 최소 단위.

### 2. 실무 예 — 세금·할인 정책을 한 곳에

```java
public interface TaxPolicy {           // "어디서 반올림하나"를 정책으로 이름 붙인다
  Money taxFor(List<Money> lines);
}
final class TaxOnTotal implements TaxPolicy {        // 합계에 한 번
  public Money taxFor(List<Money> lines) {
    long total = lines.stream().mapToLong(Money::minor).sum();
    long tax = BigDecimal.valueOf(total).multiply(new BigDecimal("0.1")).setScale(0, RoundingMode.HALF_UP).longValue();
    return new Money(tax, lines.get(0).currency());
  }
}
// 줄별 표시가 필요하면: 합계 세액을 정한 뒤 줄 금액 비율로 allocate → 세로 합 == 합계
```

- 주문·결제 요청·영수증·정산이 **같은 정책 객체**를 쓴다. 한쪽만 바뀌면 결제사 금액 검증에서 거절된다.
- JPA 매핑 주의: `@Column(precision = 19, scale = 4)`는 스키마를 생성할 때의 열 정의(`numeric(19,4)`)다. 열 스케일을 통화 자릿수보다 크게 두면 DB에서 읽은 값의 스케일이 4가 된다(PostgreSQL 17에서 1.0 저장 → `1.0000`, 로컬 재현). 그래서 `equals` 비교가 깨질 수 있다 — 값 객체 생성자에서 통화 자릿수로 맞추거나 `compareTo`로 비교한다.

### 3. 진단 — 배분·대사 검사 쿼리

```sql
-- 주문 할인액을 줄에 배분했는데 합이 안 맞는 주문 (PostgreSQL 17, 예시 스키마)
SELECT o.id, o.discount_total, sum(l.discount) AS allocated
FROM orders o JOIN order_line l ON l.order_id = o.id
GROUP BY o.id, o.discount_total
HAVING sum(l.discount) <> o.discount_total;
```

- PostgreSQL `numeric`의 `=`는 스케일을 보지 않는다: `numeric '1.0' = numeric '1.00'`은 참이고 `DISTINCT`도 하나로 친다(로컬 재현). Java `BigDecimal.equals`와 다르다. 앱에서 중복 판정을 하면 결과가 DB와 다를 수 있다.

## 장애 시나리오와 대처

### 1. 10,000원을 3명에게 나눠 1원 소실 (⚠)
- 현상: 더치페이·정산 분배 후 합이 9,999원. 1원이 어느 계정에도 없다.
- 보이는 형태: 원장 대사에서 차액 1원 행. 금액이 작아 지표로는 안 보인다.
- 원인: 배분을 곱셈(나눗셈 후 각자 반올림)으로 했다.
- 대처: 배분기(`allocate`)로 바꾸고 "합 == 원금" 불변식을 테스트·런타임 검사로 둔다. 남는 몫을 받는 규칙(앞 순번·큰 잔여·주최자)을 정책으로 적는다.

### 2. 줄 단위 반올림 vs 합계 후 반올림 → PG 금액 불일치로 결제 거절 (⚠)
- 현상: 일부 주문만 결제 승인 요청이 "금액 불일치"로 거절된다.
- 보이는 형태: 결제사 응답 코드(예: amount mismatch 계열 — 결제사마다 다름). 실험 B에서 무작위 주문의 43%가 1~4원 차이.
- 원인: 주문 서비스는 줄별 세금 합, 결제 요청은 합계 기준 세금으로 각각 계산했다.
- 대처: 세액 계산을 하나의 정책으로 모으고, 결제 요청 금액은 주문에 저장된 확정 금액을 그대로 쓴다(다시 계산하지 않는다).

### 3. JPY(0자리)·KWD(3자리)를 소수 2자리로 가정 (⚠)
- 현상: 엔화 금액이 100배, 디나르 금액이 1/10로 처리된다. 또는 결제사가 "소수 자릿수 오류"로 거절한다.
- 보이는 형태: 해외 통화 첫 결제에서만 터진다. 실험 E: "센트 가정"으로 JPY 1,000 → minor 100000, KWD 1.234 → 123.4.
- 원인: `× 100`·`setScale(2)`를 통화와 무관하게 고정했다.
- 대처: `Currency.getDefaultFractionDigits()`(또는 결제사 표)로 통화별 자릿수를 쓴다. 0·3자리 통화를 테스트 데이터에 넣는다.

### 4. `BigDecimal("1.0").equals("1.00")`이 false → 중복 판정 실패 (⚠)
- 현상: 같은 금액의 중복 청구 검사가 통과돼 이중 청구가 나간다. 또는 캐시 키가 둘로 갈린다.
- 보이는 형태: 실험 F — `equals false / compareTo 0`, `HashSet size 2 / TreeSet size 1`.
- 원인: `equals`는 값과 스케일을 모두 비교한다(javadoc). 입력 경로마다 스케일이 달랐다(DB `numeric(19,4)` → 1.0000, JSON → 1.0).
- 대처: 금액은 `Money` 값 객체로 감싼다. `BigDecimal`로 든다면 생성자에서 통화 자릿수로 `setScale`한다([12](../12-time-money-and-units/2-summary.md) 적용 §2). 그러면 `equals`·`hashCode`가 일관된다. 최소 단위 `long`(적용 §1의 `Money`)이면 스케일 문제가 없다. 맨 `BigDecimal` 비교는 `compareTo`.

### 5. JSON 숫자로 금액을 보내 정밀도 손실
- 현상: 큰 금액(최소 단위 정수)이나 소수 금액이 프런트엔드·다른 언어 서비스에서 1 단위 달라진다.
- 보이는 형태: Node 실험 — `9007199254740993` → `9007199254740992`, `19.99 * 100` → `1998.9999999999998`.
- 원인: JSON 숫자를 double로 해석하는 파서.
- 대처: 금액은 문자열 또는 안전 범위 안의 최소 단위 정수 + 통화 코드로 보낸다. API 계약 문서에 형식을 적는다.

## 핵심 문장

- 곱셈(비례 요금)과 배분(총액 나누기)은 다른 연산이다. 배분은 "합 == 원금"을 보장하는 allocator로 한다.
- 모드 인자를 받는 `BigDecimal` 연산(`setScale`·`divide`)은 모드가 빠지면 반올림 대신 던진다. 다만 `MathContext(precision)`(HALF_UP)·`longValue()`(자르기)·DB `numeric(p,s)` 저장은 조용히 줄인다. HALF_UP·HALF_EVEN·DOWN·FLOOR는 절반과 음수에서 갈린다.
- 반올림 위치(줄마다 vs 합계에 한 번)와 할인·세금 순서는 결과를 바꾼다. 법·약관이 정하고, 코드는 그 결정을 한 정책 객체에 둔다.
- 통화 소수 자릿수는 ISO 4217 데이터다(KRW·JPY 0, USD 2, KWD·BHD 3, CLF 4). "센트" 고정 가정은 틀린다.
- `BigDecimal.equals`는 스케일까지 비교한다. 금액 값 객체가 스케일을 통화 자릿수로 고정하면 동등성이 일관된다.
- 경계(JSON)에서는 금액을 문자열이나 최소 단위 정수 + 통화로 보낸다.

## 관련 주제·근거

- 선행
  - [12-time-money-and-units](../12-time-money-and-units/2-summary.md) — 개관
  - 부동소수점: [architecture/03-floating-point-ieee754](../../architecture/03-floating-point-ieee754/2-summary.md), 원고 [foundations/data-representation](../../foundations/data-representation/README.md)
- 연결
  - [advanced/05-multi-currency](../advanced/05-multi-currency/2-summary.md) — 다통화 반올림 순서·경유 환산·반올림 모드 측정
  - [advanced/06-tax](../advanced/06-tax/2-summary.md)(마지막 몫은 빼기로) · [advanced/04-refund](../advanced/04-refund/2-summary.md)(부분 환불 비례 배분) · [advanced/03-subscription-change](../advanced/03-subscription-change/2-summary.md)(반올림 위치)
  - [basic/19-tax](../basic/19-tax/) · [basic/22-settlement](../basic/22-settlement/) — 기초 연습
  - [languages/java/syntax/53-bigdecimal](../../../languages/java/syntax/53-bigdecimal/2-summary.md) — 스케일·`equals`·`divide`·반올림 모드 문법
  - [24-double-entry-ledger](../24-double-entry-ledger/2-summary.md) — 배분 결과를 분개로 남긴다 · [25-reconciliation](../25-reconciliation/2-summary.md) — 금액 불일치 대사
  - [23-versioned-rules-and-effective-dating](../23-versioned-rules-and-effective-dating/2-summary.md) — 세율·요율의 판과 적용 시각
- 근거
  - Fowler 『PoEAA』(2002) 18장 Money <https://martinfowler.com/eaaCatalog/money.html> · 초안(ISA) Money 페이지 사본 — Foemmel's conundrum, `allocate(int)`·`allocate(long[] ratios)` 코드, "multiplication … allocator" 문장 <http://thierryroussel.free.fr/java/books/martinfowler/www.martinfowler.com/isa/money.html>(개인 미러 — 원본 `martinfowler.com/isa/money.html`은 2026-10-03 확인 때 404)
  - ISO 4217 목록(SIX, 2026-09-17 공표) <https://www.six-group.com/dam/download/financial-information/data-center/iso-currrency/lists/list-one.xml>
  - Java SE 21 API — `java.math.RoundingMode`, `BigDecimal`(`equals`·`compareTo`·`setScale`·`stripTrailingZeros`·`toPlainString`), `java.util.Currency`
  - JSR 354 Money and Currency API <https://jcp.org/en/jsr/detail?id=354> — 이 노트 실험은 JSR 354 구현(Moneta)을 쓰지 않았다
  - PostgreSQL 17 문서 9.3 Mathematical Functions(`round` 동률 처리) <https://www.postgresql.org/docs/17/functions-math.html>, 8.1.2 Arbitrary Precision Numbers
  - ECMA-262 Number 타입(IEEE 754 binary64), `Number.MAX_SAFE_INTEGER`
- 실험 목록
  - `Exp14.java` — JDK 21.0.12(eclipse-temurin:21-jdk, `--cpus=2`): A 배분(나눗셈·각자 반올림·최대 잔여·Fowler), B 줄 vs 합계 세액(10,000건 seed 42), C 할인·세금 순서(1~100,000원 전수), D 반올림 모드 표, E 통화 자릿수, F `equals`/`compareTo`/`HashSet`/`TreeSet`/`stripTrailingZeros`, G `double` 합
  - 2차 리뷰 재현(같은 환경): `S.java` — `new BigDecimal("2.5").longValue()`=2, `("-2.7").longValue()`=-2, `new MathContext(1).getRoundingMode()`=HALF_UP, `2.5.round(MathContext(1))`=3
  - `json14.js` — Node.js v18.19.1(호스트): JSON 큰 정수, 소수 연산
  - PostgreSQL 17.11(postgres:17 일회용 컨테이너): `numeric '1.0' = '1.00'`(참, DISTINCT 1개), `round(2.5::numeric)`=3 vs `round(2.5::float8)`=2, `numeric(19,4)` 열에 1.0 저장 → `1.0000`, `1.23455` 저장 → `1.2346`(2차 리뷰 재현)
