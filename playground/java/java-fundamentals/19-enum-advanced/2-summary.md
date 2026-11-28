# java/java-fundamentals/19 — Enum 고급 활용 — 정리 (힌트)

> 출처 — study-site 항목 `java/enum-advanced`(항목 데이터 `data/java/fundamentals.json`) · 정답 코드 study-practice `java/java-fundamentals/reference/enum-advanced.java`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다).

## 한눈에 — 쉽게 말하면

**고급 enum 은 「직원 명찰이 붙은 사람들」이다.**
명찰(상수 이름)만 달고 서 있는 게 아니라, 사람마다 할 줄 아는 일(메서드)을 저마다의 방식으로 해낸다.
「계산해!」라고 똑같이 말해도 덧셈 담당은 더하고, 나눗셈 담당은 나눈다.
부르는 쪽은 누가 무슨 담당인지 따지지 않고 같은 말만 하면 된다.
Java 의 enum 도 똑같은 구조다.
상수 하나하나가 객체이고, 상수마다 메서드를 다르게 구현할 수 있다.

| 비유 | 실체 |
|---|---|
| 명찰 이름 | enum 상수 (`PLUS`, `MINUS` …) |
| 「계산해!」라는 같은 지시 | 공통 메서드 `apply(x, y)` |
| 사람마다 다른 일 처리 방식 | 상수별 메서드 본문 |
| 일을 적어 둔 메모를 들고 다니기 | 람다를 필드로 저장 (`DoubleBinaryOperator op`) |
| 「이 자격증은 있다」 | 인터페이스 구현 (`implements Printable`) |
| 「다른 회사 소속으로는 못 바꾼다」 | 다른 클래스 상속 불가 (이미 `java.lang.Enum` 을 상속) |

```text
            op.apply(10, 3)   ← 부르는 쪽은 같은 말만 한다
                   │
     ┌──────┬──────┼──────┬───────┐
     ▼      ▼      ▼      ▼
   PLUS   MINUS  TIMES  DIVIDE    ← 상수마다 자기 방식으로 처리
   x+y    x-y    x*y    x/y
```

## 이 주제가 답하려는 질문

1. enum 상수마다 동작을 다르게 하려면 if-else 체인 대신 무엇을 쓰나?
2. 추상 메서드로 상수별 구현을 하는 방법과 람다를 필드로 담는 방법은 어떻게 다른가?
3. enum 은 무엇을 구현할 수 있고 무엇을 상속할 수 없나?
4. 상수 안에서 `switch (this)` 로 분기하는 방법은 상수별 메서드와 무엇이 다른가?

## 동작 방식

### (1) 추상 메서드 + 상수별 본문 — `Operation`

**언제 쓰나** — 상수마다 하는 일이 다르고, 새 상수를 추가할 때 구현을 빠뜨리면 컴파일러가 잡아 주기를 바랄 때.

enum 안에 추상 메서드를 선언하면, 모든 상수가 그 메서드를 직접 구현해야 한다.
각 상수 뒤의 `{ … }` 가 그 상수만의 본문이다.

> **enum** — 이름 붙은 상수 몇 개만 객체로 갖는 특별한 클래스.\
> 예: `enum Operation { PLUS, MINUS }` 의 `PLUS` 는 `Operation` 타입의 객체 하나다.

> **추상 메서드** — 선언만 있고 본문이 없어, 하위 쪽이 반드시 구현해야 하는 메서드.\
> 예: `public abstract double apply(double x, double y);`

> **상수별 메서드** — enum 상수마다 따로 적은 메서드 구현.\
> 예: `PLUS { public double apply(double x, double y) { return x + y; } }`

```text
입력 코드                                 무엇이 일어나나                       결과
─────────────────────────────────────    ──────────────────────────────────    ───────────────
enum Operation {                         상수 넷이 각자 apply 본문을 가짐
  PLUS   { apply → x + y },
  MINUS  { apply → x - y },
  TIMES  { apply → x * y },
  DIVIDE { y==0 이면 예외, 아니면 x / y };   마지막 상수 뒤 ; → 멤버 선언 시작
  abstract double apply(x, y);           모든 상수에 apply 구현을 강제
  toString() → switch(this) 로 기호      출력할 때 이름 대신 기호
}
for (op : Operation.values())            선언 순서대로 PLUS→…→DIVIDE         op 마다 다른 계산
  op.apply(10, 3)                        실제 상수의 본문이 불림(다형성)
```

- `abstract double apply(...)` 가 있으므로 어느 상수든 본문을 빠뜨리면 컴파일 오류가 된다.
- 상수 목록 뒤에 필드 · 메서드 같은 멤버가 오면, 마지막 상수 뒤에 세미콜론(`;`)이 꼭 있어야 한다.
- 루프의 `op.apply(x, y)` 는 `op` 가 실제로 어떤 상수인지에 따라 그 상수의 본문을 부른다.
- `toString()` 을 오버라이드했으므로 `printf` 의 `%s` 자리에는 `PLUS` 가 아니라 `+` 가 찍힌다.
- `DIVIDE` 는 `y == 0` 이면 `ArithmeticException("0으로 나눌 수 없음")` 을 던진다.

> **다형성** — 같은 메서드 호출이 실제 객체에 따라 다른 구현으로 이어지는 성질.\
> 예: `op.apply(10, 3)` 이 `op` 가 `PLUS` 면 13, `TIMES` 면 30 이 된다.

> **switch expression** — 값을 돌려주는 `switch`; `case A -> 값` 꼴로 쓴다.\
> 예: `return switch (this) { case PLUS -> "+"; … };`

`toString` 의 `switch (this)` 는 `default` 가 없다.
네 상수를 모두 `case` 로 다뤘으므로 빠진 경우가 없다.

### (2) 람다를 필드로 담기 — `OperationLambda`

**언제 쓰나** — 상수별 동작이 한 줄짜리 식이라, 상수마다 본문 블록을 쓰기가 번거로울 때.

상수마다 본문을 쓰는 대신, 생성자 인자로 **동작 자체(람다)** 를 넘겨 필드에 담아 둔다.

> **람다** — 이름 없는 함수를 값처럼 쓰는 식.\
> 예: `(x, y) -> x + y`

> **함수형 인터페이스** — 추상 메서드가 하나뿐이라 람다로 채울 수 있는 인터페이스.\
> 예: `DoubleBinaryOperator` — `(double, double) -> double`, 부르는 메서드는 `applyAsDouble`.

```text
입력 코드                                            무엇이 일어나나                       결과
──────────────────────────────────────────────     ──────────────────────────────────    ───────────
PLUS("+", (x, y) -> x + y)                         생성자 호출: symbol="+", op=람다
DIVIDE("/", (x, y) -> y != 0 ? x / y : Double.NaN) 0 이면 NaN 을 돌려주는 람다
private final String symbol;                        상수마다 자기 기호를 들고 있음
private final DoubleBinaryOperator op;              상수마다 자기 연산을 들고 있음
apply(x, y) → op.applyAsDouble(x, y)               담아 둔 람다에 일을 넘김(위임)          계산 결과
toString() → symbol                                switch 없이 필드를 돌려줌               "+" 등
```

- 상수 선언 `PLUS("+", …)` 는 생성자 `OperationLambda(String, DoubleBinaryOperator)` 를 부르는 것이다.
- `apply` 는 직접 계산하지 않고 `op.applyAsDouble(x, y)` 로 넘긴다.
- `toString` 이 `symbol` 을 돌려주므로 `switch` 가 필요 없다.
- `DIVIDE` 는 0 으로 나눌 때 예외를 던지지 않고 `Double.NaN`(「숫자가 아님」)을 돌려준다.

두 구현은 바깥에서 보기에 같다 — 둘 다 `op.apply(x, y)` 로 부르고, 둘 다 `%s` 에 기호가 찍힌다.
다른 점은 동작이 **어디에 있나**다(상수 본문 블록 대 필드에 담은 함수 객체).

### (3) 인터페이스 구현 + 정적 팩토리 — `Status`

**언제 쓰나** — enum 을 기존 인터페이스 타입으로 다루고 싶을 때, 그리고 바깥 문자열(화면 라벨 · 입력값)로 상수를 찾아야 할 때.

> **정적 팩토리 메서드** — `new` 대신 객체를 돌려주는 `static` 메서드.\
> 예: `Status.fromString("활성")` 이 `ACTIVE` 를 돌려준다.

```text
입력 코드                                       무엇이 일어나나                         결과
────────────────────────────────────────       ────────────────────────────────────    ────────────────
interface Printable { String format(); }
enum Status implements Printable {             enum 이 인터페이스를 구현(상속은 불가)
  ACTIVE("활성", "green"), …                    상수마다 label, color 필드
  format() → "[" + color 대문자 + "] " + label   ACTIVE.format()                         "[GREEN] 활성"
  static fromString(text):
    values() 를 차례로 돌며                      label 이 text 와 같거나
      s.label.equals(text)                      name() 이 대소문자 무시로 같으면         그 상수
      || s.name().equalsIgnoreCase(text)
    못 찾으면 IllegalArgumentException          "Unknown status: …"                      예외
}
```

- `Status` 는 `Printable` 타입 변수에 담을 수 있다 — enum 도 인터페이스를 구현하는 평범한 타입이다.
- `format()` 은 `color.toUpperCase()` 로 색 이름을 대문자로 바꿔 대괄호 안에 넣고, 뒤에 한글 라벨을 붙인다.
- `fromString` 은 두 갈래로 찾는다: 한글 라벨은 **정확히 같아야** 하고(`equals`), 상수 이름은 **대소문자를 무시**한다(`equalsIgnoreCase`).
- `Status` 는 `toString()` 을 오버라이드하지 않았다.
  그래서 문자열에 이어 붙이면 기본 `toString()` 이 쓰이고, 이는 상수 이름(`name()`)과 같다.

### (4) 메서드 안에서 `switch (this)` 로 가르기 — `PayrollDay`

**언제 쓰나** — 상수는 많은데 동작 종류는 몇 가지뿐이라(평일 / 주말), 상수마다 본문을 쓰면 같은 코드가 반복될 때.

모든 상수가 **같은 메서드 하나**를 공유하고, 그 안에서 `this` 가 어느 상수인지 보고 가른다.

```text
입력 코드                                         무엇이 일어나나                    결과(시간=10)
───────────────────────────────────────────      ───────────────────────────────    ──────────────
BASE_HOURS = 8, BASE_RATE = 10_000               enum 안의 정적 상수
basePay = hoursWorked * BASE_RATE                10 × 10,000                        100,000
overtimePay = switch (this) {
  case SATURDAY, SUNDAY -> 전체 시간 × 시급 × 0.5   10 × 10,000 × 0.5                  50,000
  default -> 8 초과면 (초과 시간) × 시급 × 0.5      (10 − 8) × 10,000 × 0.5            10,000
             아니면 0
}
return basePay + overtimePay                     주말 150,000 / 평일 110,000
```

- `case SATURDAY, SUNDAY ->` 처럼 콤마로 상수 여럿을 한 갈래에 묶을 수 있다.
- `default` 는 「주말이 아닌 모든 상수」를 뜻한다 — 지금은 월~금이다.
- `10_000` 의 밑줄은 읽기 좋게 끊은 것일 뿐 값은 10000 이다.
- `main` 은 `%,.0f` 로 찍는다 — 천 단위 구분 기호를 넣고 소수점 아래는 0자리다.
- `%-9s` 는 문자열을 9칸 폭에 왼쪽 정렬한다.

### (5) enum 이 자동으로 갖는 것과 못 하는 것

**언제 쓰나** — enum 에 무엇을 붙일 수 있는지 설계 단계에서 따질 때.

```text
enum Status implements Printable { … }
   │
   ├─ 자동으로 상속:   java.lang.Enum          ← 그래서 extends 를 더 쓸 수 없다
   ├─ 자동으로 구현:   Comparable, Serializable
   ├─ 직접 구현 가능:  Printable 같은 인터페이스 (여러 개도 가능)
   └─ 자동으로 생김:   values() — 상수를 선언 순서대로 담은 배열
                      name()   — 선언한 상수 이름 그대로의 문자열
```

- enum 은 이미 `java.lang.Enum` 을 상속하므로 `extends` 로 다른 클래스를 상속할 수 없다.
- 대신 `implements` 로 인터페이스는 얼마든지 구현할 수 있다.
- `Comparable` 과 `Serializable` 은 따로 쓰지 않아도 구현되어 있다.

> **전략 패턴** — 「어떻게 할지」를 객체로 떼어 내 바꿔 끼우게 하는 설계.\
> 예: `Operation.PLUS` · `Operation.TIMES` 가 각각 계산 방식 하나(전략)다.

## 문법 — 형태와 규칙

```java
enum Shape {
    CIRCLE {                                   // 상수별 본문
        @Override double area(double r) { return Math.PI * r * r; }
    },
    SQUARE {
        @Override double area(double a) { return a * a; }
    };                                         // 멤버가 이어지므로 ; 필수

    abstract double area(double v);            // 모든 상수가 구현해야 함
}

enum Unit {
    KM("km", v -> v * 1000), M("m", v -> v);   // 생성자 인자로 람다
    private final String sym;
    private final java.util.function.DoubleUnaryOperator toMeter;
    Unit(String sym, java.util.function.DoubleUnaryOperator f) { this.sym = sym; this.toMeter = f; }
    double meters(double v) { return toMeter.applyAsDouble(v); }
}
```

- 상수 뒤의 `{ … }` 가 상수별 본문이다. 본문 안 메서드에는 `@Override` 를 단다.
- enum 에 `abstract` 메서드가 있으면 모든 상수가 본문에서 그것을 구현해야 한다.
- 상수 목록 다음에 필드 · 생성자 · 메서드가 오면 마지막 상수 뒤에 `;` 를 쓴다.
- 상수에 괄호 인자를 주면 enum 의 생성자가 불린다: `PLUS("+", (x, y) -> x + y)`.
- enum 의 필드는 보통 `private final` 로 둔다 — 상수는 하나뿐인 공유 객체라 바뀌면 안 된다.
- `enum X implements I` 는 되고, `enum X extends C` 는 안 된다.
- `switch (this)` 의 `case` 에는 상수 이름만 쓴다(`Operation.PLUS` 가 아니라 `PLUS`).
- `case A, B ->` 로 여러 상수를 한 갈래로 묶는다.
- `values()` 는 상수를 선언 순서대로 담은 배열을, `name()` 은 선언한 이름 문자열을 돌려준다.

## 어디서 틀리나

### 1. if-else 체인으로 상수를 가르기

```java
// 이렇게 쓰지 않는다
if (op == PLUS) return x + y;
else if (op == MINUS) return x - y;
...
```

원본의 팁: 상수별 메서드 구현은 if-else 체인 대신 다형성을 활용한다.
if-else 체인은 상수가 늘 때마다 그 체인을 찾아 고쳐야 하고, 빠뜨려도 컴파일러가 알려 주지 않는다.
추상 메서드를 두면 새 상수가 본문을 빠뜨리는 순간 컴파일 오류가 난다.

### 2. 람다를 쓰면 더 간결해진다 — 하지만 할 수 있는 일이 다르다

원본의 팁: 람다와 조합하면 더 간결해진다.
`OperationLambda` 는 상수마다 한 줄이다.
대신 동작이 람다 한 개로 표현될 만큼 짧아야 읽기 좋다.
여러 줄의 검사와 예외가 필요하면 `Operation.DIVIDE` 처럼 본문 블록이 더 읽기 쉽다.

### 3. 두 `DIVIDE` 는 0 을 다르게 다룬다

- `Operation.DIVIDE` — `y == 0` 이면 `ArithmeticException` 을 던진다.
- `OperationLambda.DIVIDE` — `y != 0` 이 아니면 `Double.NaN` 을 돌려준다.

같은 이름의 연산이 0 에서 다르게 동작하므로, 부르는 쪽은 예외를 잡을지 `NaN` 을 검사할지 따로 준비해야 한다.
Java 의 `double` 나눗셈은 0 으로 나눠도 스스로 예외를 던지지 않고 무한대나 `NaN` 이 된다.
그래서 예외를 원하면 `Operation.DIVIDE` 처럼 직접 검사해서 던져야 한다. (원본에 근거 없음 — 추론)

### 4. enum 은 다른 클래스를 상속할 수 없다

원본의 팁: enum 은 다른 클래스를 상속할 수 없다 — 이미 `java.lang.Enum` 을 상속한다.
공통 동작을 물려주고 싶으면 상속 대신 인터페이스를 구현한다(`Status implements Printable`).

### 5. `Comparable` · `Serializable` 을 또 구현하려 하지 않는다

원본의 팁: enum 은 `Comparable`, `Serializable` 을 자동 구현한다.
따로 `implements Comparable` 을 쓸 필요가 없다.

### 6. 마지막 상수 뒤 세미콜론

상수 목록 뒤에 멤버가 오는데 `;` 를 빠뜨리면 컴파일 오류다.
`Operation` 의 `DIVIDE { … };` 의 `;` 가 그것이다.

### 7. `toString` 을 바꿨는지에 따라 찍히는 글자가 다르다

`Operation` 과 `OperationLambda` 는 `toString` 을 바꿨으므로 `%s` 에 기호가 찍힌다.
`Status` 와 `PayrollDay` 는 바꾸지 않았으므로 상수 이름(`ACTIVE`, `MONDAY`)이 찍힌다.
`fromString` 같은 찾기 메서드는 `toString` 이 아니라 `name()` 과 `label` 로 찾는다 — 표시용 문자열과 찾기용 문자열을 헷갈리지 않는다.

### 8. `fromString` 의 라벨은 정확히 같아야 한다

`name()` 은 `equalsIgnoreCase` 라 `"active"` 도 `ACTIVE` 로 찾지만, 라벨은 `equals` 라 `"활성 "`(뒤에 공백)처럼 조금만 달라도 못 찾는다.
못 찾으면 `null` 이 아니라 `IllegalArgumentException("Unknown status: …")` 이 난다.

### 9. `switch (this)` 의 `default` 는 새 상수를 조용히 삼킨다

`PayrollDay.pay` 의 `default` 는 「주말이 아니면 평일」로 처리한다.
나중에 `HOLIDAY` 같은 상수를 추가하고 `case` 를 깜빡하면, 컴파일러는 아무 말 없이 그 날을 평일 규칙으로 계산한다.
추상 메서드 방식(1번)이라면 같은 실수가 컴파일 오류로 드러난다.

원본의 주장 → 원본은 `PayrollDay` 를 「전략 패턴」이라 부른다.
왜 의심스러운가 → 계산 방식이 객체로 떨어져 나와 있지 않고 메서드 안의 `switch` 로 갈리므로, 전략을 바꿔 끼우는 구조라기보다 분기 구조에 가깝다.

### 10. 주석과 코드가 어긋나는 곳

원본의 주장 → 정답 코드의 주석은 `overtimePay` 를 「야간/주말 가산금 계산」이라 적는다.
왜 의심스러운가 → 코드에는 야간을 따지는 갈래가 없다; 실제로 계산하는 것은 주말 가산(전체 시간의 50%)과 평일 8시간 초과분 가산(50%)이다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| enum 은 `java.lang.Enum` 을 상속하므로 다른 클래스를 `extends` 할 수 없다 | 언어(Java 언어 명세) |
| enum 은 `Comparable` · `Serializable` 을 구현한다 | 표준 API(`java.lang.Enum` 의 선언) |
| `values()` 는 선언 순서대로 상수를 돌려준다 | 언어(컴파일러가 만드는 메서드의 명세) |
| 기본 `toString()` 은 `name()` 과 같은 이름을 돌려준다 | 표준 API(`java.lang.Enum` 문서) |
| 추상 메서드를 구현하지 않은 상수는 컴파일 오류 | 언어 |
| `double` 을 0 으로 나누면 예외 없이 무한대 · `NaN` | 언어(부동소수점 규칙) |
| `%,.0f` 의 천 단위 기호가 `,` 이고 `%.2f` 의 소수점이 `.` 이다 | 실행 환경의 기본 로캘(locale)에 따라 다르다 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 상수마다 동작이 다르고, 본문이 여러 줄 | 추상 메서드 + 상수별 본문 | 바깥의 if-else 체인 |
| 상수마다 동작이 한 줄짜리 식 | 람다를 생성자로 받아 필드에 담기 | 상수마다 긴 본문 블록 |
| enum 을 기존 타입 계층에 끼워 넣기 | 인터페이스 구현(`implements`) | 클래스 상속(`extends` — 불가) |
| 바깥 문자열 → 상수 찾기 | 정적 팩토리(`fromString`) | 호출하는 곳마다 반복문 복사 |
| 상수는 많고 동작 종류는 두셋 | `switch (this)` (새 상수 추가 시 주의) | 상수마다 같은 본문 반복 |

## 핵심 문장

1. **enum 상수는 각자 객체라서 메서드를 저마다 다르게 가질 수 있다** — 이것이 if-else 대신 쓰는 다형성이다.
2. **추상 메서드는 「모든 상수가 구현하라」는 강제다** — 새 상수가 구현을 빠뜨리면 컴파일이 막는다.
3. **람다를 필드로 담으면 같은 다형성을 한 줄로 쓴다** — 동작이 본문이 아니라 함수 객체에 있다.
4. **enum 은 인터페이스는 구현하고, 클래스는 상속하지 못한다** — 이미 `java.lang.Enum` 을 상속하고 `Comparable` · `Serializable` 도 자동으로 구현한다.
5. **`switch (this)` + `default` 는 짧지만, 새 상수를 조용히 기본 갈래로 보낸다.**

## 관련 자료

- `enum-basics` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `interface-basics` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/java/fundamentals.json` 의 `enum-advanced`

## 용어 풀이

- **enum** — 정해진 이름의 상수 객체들만 갖는 특별한 클래스.
- **상수별 메서드** — enum 상수 뒤 `{ … }` 안에 그 상수만의 방식으로 적은 메서드 구현.
- **추상 메서드** — 본문 없이 선언만 있어, 구현을 아래쪽(여기서는 각 상수)에 맡기는 메서드.
- **다형성** — 같은 호출이 실제 객체에 따라 다른 구현으로 이어지는 성질.
- **전략 패턴** — 「어떻게 할지」를 객체로 떼어 바꿔 끼우게 하는 설계.
- **람다** — 이름 없는 함수를 값처럼 넘기는 식.
- **함수형 인터페이스** — 추상 메서드가 하나뿐이라 람다로 채울 수 있는 인터페이스.
- **`DoubleBinaryOperator`** — `double` 둘을 받아 `double` 을 돌려주는 함수형 인터페이스; 메서드는 `applyAsDouble`.
- **위임** — 받은 일을 직접 하지 않고 다른 객체에 넘기는 것.
- **정적 팩토리 메서드** — `new` 대신 알맞은 객체를 찾아 돌려주는 `static` 메서드.
- **switch expression** — 값을 돌려주는 `switch`; `case … -> 값` 꼴.
- **`values()`** — enum 의 모든 상수를 선언 순서대로 담은 배열을 돌려주는 메서드.
- **`name()`** — 상수를 선언한 이름 그대로의 문자열.
- **`Double.NaN`** — 「숫자가 아님」을 뜻하는 `double` 값.
- **`java.lang.Enum`** — 모든 enum 이 자동으로 상속하는 부모 클래스.

## 더 들어가면

- 상수별 본문이 있는 상수는 enum 의 익명 하위 클래스 객체가 된다고 알려져 있다. 그래서 `PLUS.getClass()` 와 `Operation.class` 가 다를 수 있고, 원래 enum 타입은 `getDeclaringClass()` 로 얻는다 (확인 필요).
- `PayrollDay` 의 `switch` 위험을 피하는 방법으로, 「평일 / 주말」 계산 방식을 별도의 private enum(예: `PayType`)으로 떼어 내 각 요일 생성자에 넘기는 「전략 enum」 꼴이 널리 소개된다 (확인 필요).
- enum 을 키로 쓰는 맵 · 집합에는 `EnumMap` · `EnumSet` 이 있어, 일반 `HashMap` · `HashSet` 보다 가볍게 쓸 수 있다고 한다 (확인 필요).
- `switch` 를 식(expression)으로 쓰는 문법은 Java 14 무렵에 정식이 되었다고 알려져 있다 (확인 필요).
- `fromString` 처럼 매번 반복문을 도는 대신, 정적 `Map<String, Status>` 을 미리 만들어 찾는 방식도 흔하다 (확인 필요).
