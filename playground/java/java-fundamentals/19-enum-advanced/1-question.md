# java/java-fundamentals/19 — Enum 고급 활용 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. `Operation` 의 네 상수로 10 과 3 을 계산하면 (예측)

```java
// 질문용 발췌
double x = 10, y = 3;
for (Operation op : Operation.values()) {
    System.out.printf("%.0f %s %.0f = %.2f%n", x, op, y, op.apply(x, y));
}
```

- 이 루프는 어떤 네 줄을 어떤 차례로 찍는가?
- `%s` 자리에는 무엇이 들어가는가?

### 2. 10시간 일한 월요일과 토요일의 급여 (예측)

```java
// 질문용 발췌
int hours = 10;
System.out.println(PayrollDay.MONDAY.pay(hours));
System.out.println(PayrollDay.SATURDAY.pay(hours));
```

- 두 줄은 각각 얼마를 계산하는가?

### 3. 라벨과 이름으로 `Status` 를 찾아 찍으면 (예측)

```java
// 질문용 발췌
System.out.println("fromString(\"활성\"): " + Status.fromString("활성"));
System.out.println(Status.fromString("active").format());
```

- 두 줄은 각각 무엇을 찍는가?

### 4. 상수별 메서드가 if-else 체인보다 나은 까닭 (왜)

- 상수마다 동작을 가를 때 if-else 체인 대신 추상 메서드 + 상수별 본문을 쓰면 무엇이 좋아지는가?

### 5. `Operation` 에 새 상수를 본문 없이 추가하면 (경계)

- `Operation` 에 `MODULO,` 처럼 본문 없는 상수를 하나 더 넣으면 어디서 막히는가?

### 6. enum 이 붙일 수 있는 부모의 범위 (경계)

- enum 선언에 `extends` 와 `implements` 중 무엇은 쓸 수 있고 무엇은 못 쓰는가, 그 까닭은?

### 7. 두 `DIVIDE` 에 0 을 넘기면 (경계)

- `y` 가 0 일 때 `Operation.DIVIDE.apply` 와 `OperationLambda.DIVIDE.apply` 는 각각 어떻게 끝나는가?

### 8. `PayrollDay` 에 `HOLIDAY` 를 넣고 `case` 를 깜빡하면 컴파일러가 조용한 까닭 (왜)

- 새 상수를 추가했는데 `pay` 의 `switch` 를 고치지 않아도 컴파일이 되는 까닭은 무엇이고, 그 상수는 어떻게 계산되는가?

### 9. `OperationLambda` 와 전략 패턴 · 함수형 인터페이스의 다리 (연결)

- `OperationLambda` 에서 「전략」은 어디에 담겨 있고, `DoubleBinaryOperator` 는 그 전략을 어떻게 부르게 해 주는가?

## 실습

### 실습 1. 네 가지 고급 enum 만들기

**만들 것** — 사칙연산 enum 두 가지(상수별 본문 방식 · 람다 방식), 인터페이스를 구현하는 상태 enum, 요일별 급여를 계산하는 enum 을 만들어, 미리 주어진 `main` 이 네 묶음을 찍게 한다.

**요구 조건**

1단계 — `Operation` (상수별 본문)
1. 상수 `PLUS` · `MINUS` · `TIMES` · `DIVIDE` 를 두고, 각 상수의 본문 블록에서 `apply(double x, double y)` 를 구현한다.
2. enum 에 `public abstract double apply(double x, double y);` 를 선언해 모든 상수가 구현하도록 강제한다.
3. `DIVIDE` 는 `y == 0` 이면 `ArithmeticException("0으로 나눌 수 없음")` 을 던지고, 아니면 `x / y` 를 돌려준다.
4. `toString()` 을 오버라이드해 `switch (this)` 식으로 상수마다 기호(`+` `-` `*` `/`)를 돌려준다.

2단계 — `OperationLambda` (람다 필드)
5. 각 상수를 `(기호 문자열, 연산 람다)` 두 인자로 선언한다.
6. `private final String symbol` 과 `private final DoubleBinaryOperator op` 필드를 두고 생성자에서 채운다.
7. `apply(x, y)` 는 `op.applyAsDouble(x, y)` 로 일을 넘긴다.
8. `DIVIDE` 의 람다는 `y` 가 0 이 아니면 `x / y`, 0 이면 `Double.NaN` 을 돌려준다.
9. `toString()` 은 `symbol` 을 돌려준다.

3단계 — `Printable` · `Status`
10. 인터페이스 `Printable` 에 `String format()` 을 선언한다.
11. `Status` 는 `Printable` 을 구현하고, 상수 `ACTIVE("활성", "green")` · `INACTIVE("비활성", "gray")` · `SUSPENDED("정지", "red")` 를 `label` · `color` 필드로 받는다.
12. `format()` 은 `"[" + 색 이름 대문자 + "] " + 라벨` 을 돌려준다.
13. 정적 메서드 `fromString(String text)` 은 `values()` 를 돌며 라벨이 정확히 같거나 `name()` 이 대소문자 무시로 같은 상수를 돌려주고, 못 찾으면 `IllegalArgumentException("Unknown status: " + text)` 을 던진다.

4단계 — `PayrollDay`
14. 상수 `MONDAY` 부터 `SUNDAY` 까지 일곱 개를 선언한다.
15. 정적 상수 `BASE_HOURS = 8`, `BASE_RATE = 10_000` 을 둔다.
16. `pay(int hoursWorked)` 는 기본급(시간 × 시급)에 가산금을 더해 돌려준다: `switch (this)` 로 토 · 일은 전체 시간 × 시급 × 0.5, 나머지는 8시간 초과분 × 시급 × 0.5(초과가 없으면 0).

5단계 — 출력
17. 시작 코드의 `main` 은 고치지 않는다 — 네 enum 이 완성되면 네 묶음을 찍는다.

**시작 코드**

```java
import java.util.function.DoubleBinaryOperator;

public class Main {

    enum Operation {
        // TODO: PLUS, MINUS, TIMES, DIVIDE — 각 상수 본문에서 apply 구현 (DIVIDE 는 0 검사)

        // TODO: 추상 메서드 apply 선언

        // TODO: toString 오버라이드 — switch (this) 로 기호 돌려주기
    }

    enum OperationLambda {
        // TODO: 상수 넷을 (기호, 람다) 로 선언 — DIVIDE 는 0 이면 Double.NaN

        // TODO: symbol, op 필드

        // TODO: 생성자

        double apply(double x, double y) {
            // TODO: op 에 위임
            return 0;
        }

        // TODO: toString 이 symbol 을 돌려주도록
    }

    interface Printable {
        // TODO: format() 선언
    }

    enum Status /* TODO: Printable 구현 */ {
        // TODO: ACTIVE("활성", "green"), INACTIVE("비활성", "gray"), SUSPENDED("정지", "red")
        ;

        private final String label = null;   // TODO: 생성자로 채우도록 바꾼다
        private final String color = null;   // TODO: 생성자로 채우도록 바꾼다

        // TODO: format() 구현 — "[" + 색 대문자 + "] " + 라벨

        static Status fromString(String text) {
            // TODO: 라벨 또는 name() 으로 찾고, 없으면 IllegalArgumentException
            return null;
        }
    }

    enum PayrollDay {
        // TODO: MONDAY ~ SUNDAY
        ;

        private static final int BASE_HOURS = 8;
        private static final double BASE_RATE = 10_000;

        double pay(int hoursWorked) {
            // TODO: 기본급 + switch (this) 로 가산금
            return 0;
        }
    }

    public static void main(String[] args) {
        System.out.println("=== 추상 메서드 enum ===");
        double x = 10, y = 3;
        for (Operation op : Operation.values()) {
            System.out.printf("%.0f %s %.0f = %.2f%n", x, op, y, op.apply(x, y));
        }

        System.out.println();
        System.out.println("=== 람다 활용 전략 패턴 ===");
        for (OperationLambda op : OperationLambda.values()) {
            System.out.printf("%.0f %s %.0f = %.2f%n", x, op, y, op.apply(x, y));
        }

        System.out.println();
        System.out.println("=== 인터페이스 구현 enum ===");
        for (Status status : Status.values()) {
            System.out.println(status.format());
        }
        System.out.println("fromString(\"활성\"): " + Status.fromString("활성"));

        System.out.println();
        System.out.println("=== 전략 패턴: 급여 계산 ===");
        int hours = 10;
        for (PayrollDay day : PayrollDay.values()) {
            System.out.printf("%-9s %d시간 근무: %,.0f원%n", day, hours, day.pay(hours));
        }
    }
}
```

**확인 방법** — `Main.java` 로 저장하고 `javac Main.java && java Main` 을 돌린다. 두 연산 묶음이 같은 네 줄(기호 포함)을 찍는지, `Status` 세 줄이 `[대문자 색] 라벨` 꼴인지, `fromString("활성")` 줄이 상수 이름을 찍는지, 급여가 평일과 주말에서 다르게 나오는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
