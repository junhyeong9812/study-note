# java/java-fundamentals/19 — Enum 고급 활용 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 선언 순서대로 네 줄, `%s` 에는 기호

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
10 + 3 = 13.00
10 - 3 = 7.00
10 * 3 = 30.00
10 / 3 = 3.33
```

**왜 그런가**
- `values()` 는 선언 순서(`PLUS` → `MINUS` → `TIMES` → `DIVIDE`)대로 상수를 돌려준다.
- `op.apply(x, y)` 는 실제 상수의 본문을 부른다 — 다형성이다.
- `%s` 는 `toString()` 을 쓰고, `Operation` 은 그것을 `switch (this)` 로 기호를 돌려주게 바꿨다. 그래서 `PLUS` 가 아니라 `+` 가 찍힌다.
- `%.0f` 는 소수점 아래 0자리(`10`), `%.2f` 는 2자리(`3.33`)다.
- 소수점 기호는 실행 환경의 기본 로캘에 따라 달라질 수 있다.

근거: 2-summary 「동작 방식 (1)」, 「구현 세부사항 대 언어 보장」.

### 2. 월요일 110,000 · 토요일 150,000

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
- `MONDAY.pay(10)` → `110000.0`
- `SATURDAY.pay(10)` → `150000.0`

**왜 그런가**
- 기본급은 둘 다 10 × 10,000 = 100,000 이다.
- 월요일은 `default` 갈래다: 10 > 8 이므로 (10 − 8) × 10,000 × 0.5 = 10,000 을 더한다.
- 토요일은 `case SATURDAY, SUNDAY` 갈래다: 전체 시간에 가산하므로 10 × 10,000 × 0.5 = 50,000 을 더한다.
- `println` 으로 `double` 을 찍으므로 `110000.0` 꼴이 된다; `main` 처럼 `%,.0f` 로 찍으면 `110,000` 꼴이다.

근거: 2-summary 「동작 방식 (4)」.

### 3. 첫 줄은 상수 이름, 둘째 줄은 `[GREEN] 활성`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
fromString("활성"): ACTIVE
[GREEN] 활성
```

**왜 그런가**
- `"활성"` 은 `ACTIVE` 의 `label` 과 `equals` 로 같으므로 `ACTIVE` 가 돌아온다.
- `Status` 는 `toString()` 을 오버라이드하지 않았다. 문자열에 이어 붙이면 기본 `toString()` 이 쓰이고, 이는 `name()` 과 같은 `ACTIVE` 다.
- `"active"` 는 라벨과는 다르지만 `name()` 과 `equalsIgnoreCase` 로 같으므로 역시 `ACTIVE` 가 돌아온다.
- `format()` 은 `"green".toUpperCase()` → `GREEN` 을 대괄호에 넣고 라벨을 붙인다.

근거: 2-summary 「동작 방식 (3)」, 「어디서 틀리나 7 · 8」.

### 4. 새 상수의 구현 누락을 컴파일러가 잡고, 동작이 상수 곁에 모인다

- 추상 메서드가 있으면 모든 상수가 그 메서드를 구현해야 하므로, 새 상수를 넣고 구현을 빠뜨리면 컴파일 오류가 난다.
- if-else 체인은 상수가 늘 때마다 체인을 찾아 고쳐야 하고, 빠뜨려도 컴파일러가 알려 주지 않는다.
- 부르는 쪽은 `op.apply(x, y)` 한 줄만 쓰고, 어떤 계산을 할지는 상수 자신이 정한다(다형성).

근거: 2-summary 「어디서 틀리나 1」, 「동작 방식 (1)」.

### 5. 컴파일 단계에서 막힌다

- `Operation` 에는 `public abstract double apply(...)` 가 있다.
- 본문 없는 `MODULO` 는 `apply` 를 구현하지 않으므로 컴파일 오류가 난다.
- 덧붙여 `toString` 의 `switch (this)` 에도 `MODULO` 의 `case` 가 없어 빠진 경우가 생긴다. (원본에 근거 없음 — 추론)

근거: 2-summary 「동작 방식 (1)」, 「문법 — 형태와 규칙」.

### 6. `implements` 는 되고 `extends` 는 안 된다

- enum 은 이미 `java.lang.Enum` 을 상속하므로 다른 클래스를 `extends` 할 수 없다.
- 인터페이스는 `implements` 로 구현할 수 있다 — `Status implements Printable` 처럼.
- 따로 쓰지 않아도 `Comparable` · `Serializable` 은 구현되어 있다.

근거: 2-summary 「동작 방식 (5)」, 「어디서 틀리나 4 · 5」.

### 7. 하나는 예외, 하나는 `NaN`

- `Operation.DIVIDE.apply(x, 0)` — `y == 0` 검사에 걸려 `ArithmeticException("0으로 나눌 수 없음")` 을 던지고 값을 돌려주지 않는다.
- `OperationLambda.DIVIDE.apply(x, 0)` — 람다의 `y != 0 ? x / y : Double.NaN` 에서 `Double.NaN` 을 돌려준다.
- 같은 이름의 연산이지만 부르는 쪽이 대비할 것(예외 잡기 대 `NaN` 검사)이 다르다.

근거: 2-summary 「어디서 틀리나 3」, 「동작 방식 (1) · (2)」.

### 8. `default` 가 모든 나머지 상수를 받기 때문이다

- `switch (this)` 에 `default` 갈래가 있어, 컴파일러가 보기에 빠진 경우가 없다.
- 그래서 `HOLIDAY` 는 `default` 로 가서 평일 규칙(8시간 초과분만 50% 가산)으로 계산된다.
- 추상 메서드 방식이었다면 `HOLIDAY` 가 구현을 빠뜨린 순간 컴파일 오류로 드러났을 것이다.

근거: 2-summary 「어디서 틀리나 9」.

### 9. 전략은 `op` 필드의 람다에 담기고, `applyAsDouble` 로 부른다

- 각 상수는 생성자 인자로 받은 람다를 `private final DoubleBinaryOperator op` 에 담는다 — 이 람다가 「어떻게 계산할지」, 곧 전략이다.
- `DoubleBinaryOperator` 는 `(double, double) -> double` 꼴의 함수형 인터페이스라 람다로 채울 수 있다.
- `apply(x, y)` 는 직접 계산하지 않고 `op.applyAsDouble(x, y)` 로 위임한다.
- 그래서 바깥에서는 `Operation` 과 똑같이 `op.apply(x, y)` 로 부르지만, 동작은 본문 블록이 아니라 함수 객체에 있다.

근거: 2-summary 「동작 방식 (2)」, 「동작 방식 (5)」의 전략 패턴 풀이.

## 실습 정답

### 실습 1. 네 가지 고급 enum 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 상수 넷이 본문에서 `apply` 구현 | `PLUS { … }` · `MINUS { … }` · `TIMES { … }` · `DIVIDE { … }` |
| 2. 추상 메서드로 구현 강제 | `public abstract double apply(double x, double y);` |
| 3. `DIVIDE` 0 검사 후 예외 | `if (y == 0) throw new ArithmeticException("0으로 나눌 수 없음");` |
| 4. 기호를 돌려주는 `toString` | `Operation.toString()` 의 `return switch (this) { … }` |
| 5. `(기호, 람다)` 로 상수 선언 | `PLUS("+", (x, y) -> x + y)` 등 |
| 6. 필드 둘 + 생성자 | `symbol` · `op` 필드, `OperationLambda(String symbol, DoubleBinaryOperator op)` |
| 7. 위임 | `OperationLambda.apply` 의 `op.applyAsDouble(x, y)` |
| 8. 0 이면 `NaN` | `DIVIDE("/", (x, y) -> y != 0 ? x / y : Double.NaN)` |
| 9. `toString` 이 `symbol` | `OperationLambda.toString()` 의 `return symbol;` |
| 10. 인터페이스 선언 | `interface Printable { String format(); }` |
| 11. `Status` 가 구현 + 라벨 · 색 | `enum Status implements Printable`, `ACTIVE("활성", "green")` 등, `Status(String label, String color)` |
| 12. `format()` | `"[" + color.toUpperCase() + "] " + label` |
| 13. `fromString` | `s.label.equals(text) \|\| s.name().equalsIgnoreCase(text)`, `throw new IllegalArgumentException("Unknown status: " + text)` |
| 14. 일곱 요일 | `MONDAY, TUESDAY, … SUNDAY;` |
| 15. 정적 상수 | `BASE_HOURS = 8`, `BASE_RATE = 10_000` |
| 16. 급여 계산 | `pay` 의 `basePay`, `switch (this)` 의 `case SATURDAY, SUNDAY ->` 와 `default ->` |
| 17. 출력 | `main` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`java/java-fundamentals/reference/enum-advanced.java`

```java
// [Java 기본 문법] Enum 고급 활용
// 설명: enum에 추상 메서드 정의, 인터페이스 구현, 전략 패턴 구현
// 팁: enum의 상수별 메서드 구현은 if-else 체인 대신 다형성을 활용한다. 람다와 조합하면 더 간결해진다. enum은 Comparable, Serializable을 자동 구현하며, 다른 클래스를 상속할 수 없다 (이미 java.lang.Enum을 상속).

// DoubleBinaryOperator: (double, double) -> double 함수형 인터페이스
import java.util.function.DoubleBinaryOperator;

// JVM 진입점 클래스
public class Main {

    // 추상 메서드 enum: 각 상수가 자신만의 구현 제공 (상수별 메서드)
    enum Operation {
        // 각 상수 뒤에 익명 클래스처럼 메서드 본문 정의
        PLUS {
            // @Override: 추상 메서드 구현 검증
            @Override
            public double apply(double x, double y) { return x + y; }
        },
        MINUS {
            @Override
            public double apply(double x, double y) { return x - y; }
        },
        TIMES {
            @Override
            public double apply(double x, double y) { return x * y; }
        },
        DIVIDE {
            @Override
            public double apply(double x, double y) {
                // 0으로 나누기는 명시적으로 예외 던지기
                if (y == 0) throw new ArithmeticException("0으로 나눌 수 없음");
                return x / y;
            }
        };  // 마지막 상수 뒤 세미콜론 (멤버 선언 시작)

        // 추상 메서드 - 각 상수가 반드시 구현해야 함
        public abstract double apply(double x, double y);

        // toString 오버라이드: 기호 표현
        @Override
        public String toString() {
            // switch expression으로 자기 자신(this)에 따라 기호 반환
            return switch (this) {
                case PLUS -> "+";
                case MINUS -> "-";
                case TIMES -> "*";
                case DIVIDE -> "/";
            };
        }
    }

    // 람다를 활용한 더 간결한 전략 패턴 (추상 메서드 대신 함수 객체 저장)
    enum OperationLambda {
        // 각 상수가 (기호, 연산 람다) 쌍을 가짐
        PLUS("+", (x, y) -> x + y),
        MINUS("-", (x, y) -> x - y),
        TIMES("*", (x, y) -> x * y),
        // DIVIDE는 0 검사 포함
        DIVIDE("/", (x, y) -> y != 0 ? x / y : Double.NaN);

        // 인스턴스 필드: 기호와 연산 함수
        private final String symbol;
        private final DoubleBinaryOperator op;

        // 생성자: 기호와 함수 받기
        OperationLambda(String symbol, DoubleBinaryOperator op) {
            this.symbol = symbol;
            this.op = op;
        }

        // 함수 객체를 통한 연산 위임
        double apply(double x, double y) {
            return op.applyAsDouble(x, y);
        }

        @Override
        public String toString() { return symbol; }
    }

    // 인터페이스 정의: enum이 구현할 동작
    interface Printable {
        String format();
    }

    // enum이 인터페이스 구현 가능 (단, 클래스 상속은 불가)
    enum Status implements Printable {
        // 각 상수에 라벨과 색상 할당
        ACTIVE("활성", "green"),
        INACTIVE("비활성", "gray"),
        SUSPENDED("정지", "red");

        private final String label;
        private final String color;

        Status(String label, String color) {
            this.label = label;
            this.color = color;
        }

        // 인터페이스 메서드 구현
        @Override
        public String format() {
            return "[" + color.toUpperCase() + "] " + label;
        }

        // static 팩토리 메서드: 문자열로 enum 찾기 (대소문자/라벨 모두 매칭)
        static Status fromString(String text) {
            for (Status s : values()) {
                // label 또는 name() 둘 다로 검색
                if (s.label.equals(text) || s.name().equalsIgnoreCase(text)) {
                    return s;
                }
            }
            // 매칭 실패 시 예외
            throw new IllegalArgumentException("Unknown status: " + text);
        }
    }

    // 전략 패턴: 요일별 급여 계산 (모든 상수가 같은 메서드, 내부에서 분기)
    enum PayrollDay {
        // 평일과 주말 모두 선언
        MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY,
        SATURDAY, SUNDAY;

        // enum 내 정적 상수
        private static final int BASE_HOURS = 8;
        private static final double BASE_RATE = 10_000;  // 시급

        // 급여 계산 메서드
        double pay(int hoursWorked) {
            // 기본 급여 = 시간 * 시급
            double basePay = hoursWorked * BASE_RATE;
            // switch expression으로 야간/주말 가산금 계산
            double overtimePay = switch (this) {
                // 콤마로 여러 상수 매칭
                case SATURDAY, SUNDAY ->
                    hoursWorked * BASE_RATE * 0.5;  // 주말: 전체 시간에 50% 추가
                default ->
                    // 평일: 8시간 초과분에만 50% 가산
                    hoursWorked > BASE_HOURS
                        ? (hoursWorked - BASE_HOURS) * BASE_RATE * 0.5  // 평일 초과근무
                        : 0;
            };
            return basePay + overtimePay;
        }
    }

    // main: 고급 enum 시연
    public static void main(String[] args) {
        System.out.println("=== 추상 메서드 enum ===");
        double x = 10, y = 3;
        // 모든 연산을 다형성으로 호출
        for (Operation op : Operation.values()) {
            System.out.printf("%.0f %s %.0f = %.2f%n", x, op, y, op.apply(x, y));
        }

        System.out.println();
        System.out.println("=== 람다 활용 전략 패턴 ===");
        // 동일한 인터페이스를 람다 기반으로 시연
        for (OperationLambda op : OperationLambda.values()) {
            System.out.printf("%.0f %s %.0f = %.2f%n", x, op, y, op.apply(x, y));
        }

        System.out.println();
        System.out.println("=== 인터페이스 구현 enum ===");
        // 모든 Status에 대해 format 호출
        for (Status status : Status.values()) {
            System.out.println(status.format());
        }
        // 정적 팩토리로 라벨에서 enum 얻기
        System.out.println("fromString(\"활성\"): " + Status.fromString("활성"));

        System.out.println();
        System.out.println("=== 전략 패턴: 급여 계산 ===");
        int hours = 10;  // 10시간 근무
        // 각 요일별 급여 출력
        for (PayrollDay day : PayrollDay.values()) {
            // %,.0f: 천단위 콤마 + 소수점 0자리
            System.out.printf("%-9s %d시간 근무: %,.0f원%n", day, hours, day.pay(hours));
        }
    }
}
```

**실행 결과** — 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다).

**풀이 요점**
- `Operation` 은 상수 본문 + 추상 메서드로, 새 상수가 구현을 빠뜨리면 컴파일이 막힌다.
- `OperationLambda` 는 같은 일을 람다 필드와 위임으로 한 줄씩 쓴다 — 바깥에서 부르는 모양은 같다.
- 두 `DIVIDE` 는 0 을 다르게 다룬다: 하나는 예외, 하나는 `Double.NaN`.
- `Status` 는 클래스 상속 대신 인터페이스를 구현하고, `toString` 을 바꾸지 않았으므로 문자열에 붙이면 상수 이름이 나온다.
- `PayrollDay` 는 `switch (this)` 하나로 평일 · 주말을 가르지만, `default` 때문에 새 상수를 추가해도 컴파일러가 경고하지 않는다.
- 정답 코드의 「야간/주말 가산금」 주석과 달리 야간 계산은 없다 — 주말 가산과 평일 초과근무 가산만 있다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
