# java/java-advanced-patterns/04 — Interpreter Pattern (인터프리터 패턴) — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 거리 트리의 `toFormula()` 문자열 (예측)

```java
// 질문용 발췌
Expression distance = ExprDSL.sqrt(
    ExprDSL.add(
        ExprDSL.mul(ExprDSL.var("x"), ExprDSL.var("x")),
        ExprDSL.mul(ExprDSL.var("y"), ExprDSL.var("y"))
    )
);
System.out.println("수식: " + distance.toFormula());
```

- 출력되는 한 줄은 괄호까지 정확히 어떤 글자인가?

### 2. 할인 트리에 price=50000, discount=20 을 넣으면 (예측)

```java
// 질문용 발췌
Expression discountCalc = ExprDSL.mul(
    ExprDSL.var("price"),
    ExprDSL.sub(ExprDSL.num(1), ExprDSL.div(ExprDSL.var("discount"), ExprDSL.num(100)))
);
Map<String, Double> ctx3 = new HashMap<>();
ctx3.put("price", 50000.0);
ctx3.put("discount", 20.0);
System.out.println(discountCalc.interpret(ctx3));
```

- 안쪽부터 어떤 차례로 계산되고, 마지막 값은 얼마로 예상되나?

### 3. 컨텍스트에 변수 하나가 빠지면 (예측)

```java
// 질문용 발췌
Map<String, Double> ctx = Map.of("x", 3.0);
System.out.println(distance.interpret(ctx));  // distance 는 1번 문항의 트리
```

- 이 호출은 어디까지 계산하다가 무슨 일로 끝나나?

### 4. 같은 트리가 다른 결과를 내는 까닭 (왜)

- `distance` 트리를 한 번만 만들었는데 `{x=3, y=4}` 와 `{x=5, y=12}` 에서 서로 다른 값을 내는 것은 왜 가능한가?

### 5. `BinaryExpression.toFormula` 가 늘 괄호를 붙이는 까닭 (왜)

- 연산자 우선순위를 따지지 않고 언제나 괄호로 감싸는 설계는 무엇을 얻고 무엇을 내주나?

### 6. 숫자 표기가 정수 꼴과 소수 꼴로 갈리는 지점 (경계)

- `NumberExpression.toFormula` 는 어떤 값에서 `3` 처럼, 어떤 값에서 `2.5` 처럼 쓰며 그 판정은 무엇으로 하나?

### 7. 이 예제가 「파서」라고 불리는 것의 한계 (경계)

- 이 코드로 사용자가 입력한 문자열 `"x*x + y*y"` 를 바로 평가할 수 있나, 없다면 무엇이 빠져 있나?

### 8. 이 패턴이 맞지 않게 되는 지점 (경계)

- 문법이 어떤 모습이 되면 Interpreter 패턴 대신 ANTLR 같은 도구를 고르는 게 낫나?

### 9. 연산을 하나 더 늘릴 때 Visitor 패턴과의 다리 (연결)

- 「트리 속 변수 이름 목록 뽑기」라는 새 연산을 넣을 때, 지금 구조와 Visitor 를 엮은 구조는 고쳐야 할 곳이 어떻게 다른가?

## 실습

### 실습 1. 수식 DSL 해석기 만들기

**만들 것** — 숫자 · 변수 · 사칙연산 · 단일 인자 함수로 된 수식을 객체 트리로 조립하고, 변수 맵을 넣어 값을 계산하며, 트리를 괄호 붙은 수식 문자열로 보여 주는 프로그램.

**요구 조건**

1단계 — 공통 계약
1. `Expression` 인터페이스는 `double interpret(Map<String, Double> context)` 와 `String toFormula()` 두 메서드를 가진다.

2단계 — Terminal 노드
2. `NumberExpression` 은 자기 값을 그대로 돌려주고, `toFormula` 에서 소수 부분이 0 이면 정수 꼴로, 아니면 소수 꼴로 쓴다.
3. `VariableExpression` 은 컨텍스트에서 자기 이름으로 값을 꺼내고, 이름이 없으면 `"정의되지 않은 변수: " + 이름` 메시지의 `RuntimeException` 을 던진다. `toFormula` 는 이름을 그대로 돌려준다.

3단계 — Non-Terminal 노드
4. `BinaryExpression` 은 왼쪽 → 오른쪽 차례로 자식을 평가한 뒤 연산자 `+ - * /` 를 `switch` 식으로 적용한다.
5. `/` 에서 오른쪽 값이 0 이면 `"0으로 나눌 수 없음"` 메시지의 `ArithmeticException` 을, 모르는 연산자면 `"알 수 없는 연산자: …"` `RuntimeException` 을 던진다.
6. `BinaryExpression.toFormula` 는 `(왼쪽 연산자 오른쪽)` 꼴로 언제나 괄호로 감싼다.
7. `FunctionExpression` 은 인자를 먼저 평가한 뒤 `abs` · `sqrt` · `ceil` · `floor` 중 하나를 `Math` 의 같은 이름 메서드로 적용하고, 모르는 이름이면 `"알 수 없는 함수: …"` 예외를 던진다. `toFormula` 는 `이름(인자)` 꼴이다.

4단계 — 조립 도우미
8. `ExprDSL` 클래스에 `num` · `var` · `add` · `sub` · `mul` · `div` · `sqrt` · `abs` 정적 메서드를 두어 각 노드를 만들어 돌려준다.

5단계 — 사용
9. `main` 에서 `sqrt(x*x + y*y)` 트리를 만들어 수식을 찍고, `{x=3, y=4}` 와 `{x=5, y=12}` 두 컨텍스트로 각각 평가해 찍는다.
10. `price * (1 - discount / 100)` 트리를 만들어 수식을 찍고, 하나의 `HashMap` 컨텍스트에 값을 `put` 으로 바꿔 가며 (50000, 20) 과 (30000, 10) 두 경우를 평가해 「원」을 붙여 찍는다.

**시작 코드**

```java
import java.util.HashMap;
import java.util.Map;

interface Expression {
    // TODO: 컨텍스트로 값을 평가하는 메서드
    // TODO: 수식 문자열을 돌려주는 메서드
}

class NumberExpression implements Expression {
    private final double value;
    public NumberExpression(double value) { this.value = value; }

    // TODO: interpret — 자기 값
    // TODO: toFormula — 소수 부분이 0 이면 정수 꼴
}

class VariableExpression implements Expression {
    private final String name;
    public VariableExpression(String name) { this.name = name; }

    // TODO: interpret — 컨텍스트에서 찾기, 없으면 예외
    // TODO: toFormula
}

class BinaryExpression implements Expression {
    private final Expression left;
    private final Expression right;
    private final String operator;

    public BinaryExpression(Expression left, String operator, Expression right) {
        this.left = left;
        this.operator = operator;
        this.right = right;
    }

    // TODO: interpret — 왼쪽, 오른쪽 재귀 평가 후 switch 식으로 연산
    // TODO: toFormula — 항상 괄호
}

class FunctionExpression implements Expression {
    private final String funcName;
    private final Expression argument;

    public FunctionExpression(String funcName, Expression argument) {
        this.funcName = funcName;
        this.argument = argument;
    }

    // TODO: interpret — 인자 먼저 평가, abs/sqrt/ceil/floor
    // TODO: toFormula — 이름(인자)
}

class ExprDSL {
    // TODO: num, var, add, sub, mul, div, sqrt, abs
}

public class InterpreterDemo {
    public static void main(String[] args) {
        // TODO: sqrt(x*x + y*y) 트리 조립
        Expression distance = null;

        System.out.println("수식: " + distance.toFormula());

        Map<String, Double> ctx1 = Map.of("x", 3.0, "y", 4.0);
        System.out.println("x=3, y=4 -> 거리 = " + distance.interpret(ctx1));

        Map<String, Double> ctx2 = Map.of("x", 5.0, "y", 12.0);
        System.out.println("x=5, y=12 -> 거리 = " + distance.interpret(ctx2));

        // TODO: price * (1 - discount / 100) 트리 조립
        Expression discountCalc = null;

        System.out.println("\n할인 수식: " + discountCalc.toFormula());

        Map<String, Double> ctx3 = new HashMap<>();
        ctx3.put("price", 50000.0);
        ctx3.put("discount", 20.0);
        System.out.println("가격=50000, 할인=20% -> " + discountCalc.interpret(ctx3) + "원");

        ctx3.put("price", 30000.0);
        ctx3.put("discount", 10.0);
        System.out.println("가격=30000, 할인=10% -> " + discountCalc.interpret(ctx3) + "원");
    }
}
```

**확인 방법** — 파일을 `InterpreterDemo.java` 로 저장하고 `javac InterpreterDemo.java && java InterpreterDemo` 로 돌린다. 찍힌 두 수식 문자열이 트리 모양과 같은 괄호 구조인지, 네 개의 값이 손으로 계산한 값(거리 5 · 13, 할인 후 40000 · 27000)과 맞는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
