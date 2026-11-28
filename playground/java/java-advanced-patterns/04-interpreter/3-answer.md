# java/java-advanced-patterns/04 — Interpreter Pattern (인터프리터 패턴) — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. `sqrt(((x * x) + (y * y)))` — 괄호가 세 겹이다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
수식: sqrt(((x * x) + (y * y)))
```

**왜 그런가**
- 잎 `x` · `y` 는 이름을 그대로 쓴다.
- `mul(x, x)` 는 `BinaryExpression` 이라 `(x * x)` 가 된다.
- `add(…)` 도 `BinaryExpression` 이라 바깥에 괄호를 하나 더 둘러 `((x * x) + (y * y))` 가 된다.
- `sqrt` 는 `FunctionExpression` 이라 `sqrt(` + 인자 + `)` 를 붙인다 — 그래서 여는 괄호가 세 개 겹친다.
- 근거: 2-summary 「동작 방식 (4)」.

### 2. 100 으로 나누기 → 1 에서 빼기 → price 곱하기, 40000 근처

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
discount / 100   = 20 / 100 = 0.2
1 - 0.2          = 0.8
price * 0.8      = 50000 * 0.8 = 40000.0  (으로 예상)
```

**왜 그런가**
- 바깥 `mul` 은 왼쪽 `var("price")` 를 먼저 평가해 50000 을 얻는다.
- 오른쪽 `sub` 는 다시 왼쪽 `num(1)`, 오른쪽 `div(...)` 차례로 평가한다 — 가장 깊은 `div` 가 먼저 값을 낸다.
- 자식 값이 다 나온 뒤에 부모가 연산하는 후위 순회다.
- `double` 끼리 계산하므로 아주 작은 부동소수 오차가 붙을 가능성은 남는다(원본에 근거 없음 — 추론).
- 근거: 2-summary 「동작 방식 (3)」.

### 3. `x*x` 는 계산되고, `y` 를 찾다가 예외로 끝난다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
sqrt → + → 왼쪽 *(x,x): x=3 → 9 (계산 끝)
         → 오른쪽 *(y,y): y 를 컨텍스트에서 찾음 → 없음
         → RuntimeException("정의되지 않은 변수: y")
```

**왜 그런가**
- `BinaryExpression.interpret` 는 왼쪽을 먼저 평가하므로 `x * x` 는 끝난다.
- 오른쪽의 `VariableExpression("y")` 가 `containsKey` 검사에서 실패해 `RuntimeException` 을 던진다.
- 예외가 위로 퍼지므로 `+` 와 `sqrt` 는 적용되지 않고 `println` 에 값이 가지 않는다.
- 근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 4」.

### 4. 트리는 값을 품지 않고 컨텍스트가 값을 품기 때문이다

트리에는 「`x` 라는 이름의 변수」만 들어 있고, 그 값은 `interpret(context)` 를 부를 때 넘기는 맵에서 꺼낸다.
그래서 트리는 그대로 두고 맵만 바꿔 넣으면 같은 계산 규칙으로 다른 결과가 나온다(트리 재사용).
근거: 2-summary 「동작 방식 (3)」 · 「핵심 문장 3」.

### 5. 단순함과 애매함 없는 차례를 얻고, 읽기 좋은 최소 괄호를 내준다

얻는 것: 우선순위 비교 로직 없이도 문자열의 계산 차례가 트리와 정확히 같아진다.
내주는 것: `(price * (1 - (discount / 100)))` 처럼 괄호가 겹쳐 사람이 읽기 번거롭다.
괄호를 줄이려면 연산자 우선순위를 비교하는 코드를 따로 넣어야 한다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 5」.

### 6. 소수 부분이 0 이냐 아니냐가 경계다 — `value == (int) value`

`3.0` 은 `(int)` 로 바꿔도 3 이라 같다고 판정되어 `3` 으로 쓴다.
`2.5` 는 `(int)` 로 바꾸면 2 라 다르다고 판정되어 `2.5` 로 쓴다.
이 규칙은 Java 가 보장하는 표기법이 아니라 이 코드의 `toFormula` 가 정한 규칙이다.
근거: 2-summary 「동작 방식 (4)」 · 「구현 세부사항 대 언어 보장」.

### 7. 바로 평가할 수 없다 — 문자열을 트리로 바꾸는 파서가 빠져 있다

이 코드는 `ExprDSL` 호출로 트리를 손으로 조립할 뿐, 문자열을 읽어 트리를 만드는 구문분석 단계가 없다.
`Stack` 은 import 만 되고 쓰이지 않는다.
따라서 원본의 「DSL 파서」라는 이름과 「외부 설정에서 로드 가능」이라는 주석은 파서를 따로 만들어야 성립한다.
근거: 2-summary 「어디서 틀리나 3」.

### 8. 문법이 크고 자주 바뀌면 파서 생성기가 낫다

규칙 하나가 클래스 하나라서, 규칙이 많아지거나 자주 바뀌면 클래스 수와 재귀 구조가 감당하기 어려워진다.
원본 팁은 이 패턴이 문법이 간단하고 변경이 적을 때 적합하고, 복잡한 문법에는 ANTLR 같은 파서 생성기가 낫다고 한다.
근거: 2-summary 「어디서 틀리나 1」 · 「언제 쓰고 언제 안 쓰나」.

### 9. 지금은 모든 노드를 고치고, Visitor 를 엮으면 방문자 하나만 더한다

지금 구조는 연산(`interpret`, `toFormula`)이 노드 안에 있으므로, 새 연산을 넣으려면 `Expression` 과 네 노드 클래스 모두에 메서드를 추가해야 한다.
Visitor 를 엮으면 노드는 방문자를 받아들이는 통로만 두고, 연산은 방문자 클래스로 빠진다 — 새 연산은 새 방문자 클래스 하나로 끝난다.
원본 팁: 표현식 트리와 Visitor 패턴을 조합하면 다양한 연산을 추가할 수 있다.
근거: 2-summary 「어디서 틀리나 2」.

## 실습 정답

### 실습 1. 수식 DSL 해석기 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 공통 계약 두 메서드 | `interface Expression` 의 `interpret`, `toFormula` |
| 2. 숫자 값 · 정수/소수 표기 | `NumberExpression.interpret`, `toFormula` 의 `value == (int) value` |
| 3. 변수 조회 · 미정의 예외 | `VariableExpression.interpret` 의 `containsKey` 검사와 `throw new RuntimeException` |
| 4. 왼쪽 → 오른쪽 평가 후 `switch` 식 | `BinaryExpression.interpret` 의 `l`, `r` 과 `switch (operator)` |
| 5. 0 나눗셈 · 모르는 연산자 예외 | `case "/" -> { … yield l / r; }` 와 `default ->` |
| 6. 항상 괄호 | `BinaryExpression.toFormula` 의 `"(" + … + ")"` |
| 7. 함수 적용 · 표기 · 예외 | `FunctionExpression.interpret` 의 `switch (funcName)` 과 `toFormula` |
| 8. 조립 도우미 | `class ExprDSL` 의 `num` · `var` · `add` · `sub` · `mul` · `div` · `sqrt` · `abs` |
| 9. 거리 트리와 두 컨텍스트 | `main` 의 `distance`, `ctx1`, `ctx2` |
| 10. 할인 트리와 가변 컨텍스트 | `main` 의 `discountCalc`, `ctx3.put(...)` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`java/java-advanced-patterns/reference/interpreter.java`

```java
// [고급 패턴 & 기법] Interpreter Pattern (인터프리터 패턴)
// 설명: 간단한 언어의 문법을 정의하고 해석하는 패턴. DSL 구현, 표현식 파싱과 평가
// 팁: Interpreter 패턴은 문법이 간단하고 변경이 적을 때 적합하다. 복잡한 문법은 파서 생성기(ANTLR 등)를 사용하는 것이 낫다. 정규 표현식, SQL WHERE절 파서, 템플릿 엔진 등이 이 패턴의 활용 예다. 표현식 트리와 Visitor 패턴을 조합하면 다양한 연산을 추가할 수 있다.

// === Interpreter 패턴: 수학 표현식 DSL 파서 & 평가기 ===

// 변수 바인딩 컨텍스트
import java.util.HashMap;
import java.util.Map;
// (학습용 import — 후위 표기식 파서에 활용 가능)
import java.util.Stack;

// 표현식 인터페이스 (Abstract Expression)
// 모든 노드가 interpret과 toFormula를 구현 — 트리 구조의 공통 계약
interface Expression {
    // 컨텍스트(변수 맵)에 따라 값을 평가
    double interpret(Map<String, Double> context);
    // 사람이 읽을 수 있는 수식 문자열로 출력
    String toFormula(); // 표현식을 문자열로 출력
}

// Terminal Expression: 숫자 리터럴
// 더 이상 분해되지 않는 잎 노드 — 자기 값을 그대로 반환
class NumberExpression implements Expression {
    private final double value;

    public NumberExpression(double value) {
        this.value = value;
    }

    @Override
    public double interpret(Map<String, Double> context) {
        return value;
    }

    @Override
    public String toFormula() {
        // 정수처럼 보이면 정수로 출력
        return value == (int) value ? String.valueOf((int) value) : String.valueOf(value);
    }
}

// Terminal Expression: 변수
// 컨텍스트에서 이름으로 값을 조회 — 미정의 시 런타임 예외
class VariableExpression implements Expression {
    private final String name;

    public VariableExpression(String name) {
        this.name = name;
    }

    @Override
    public double interpret(Map<String, Double> context) {
        if (!context.containsKey(name)) {
            throw new RuntimeException("정의되지 않은 변수: " + name);
        }
        return context.get(name);
    }

    @Override
    public String toFormula() { return name; }
}

// Non-Terminal Expression: 이항 연산
// 두 자식 표현식을 결합하는 내부 노드 (재귀 구조)
class BinaryExpression implements Expression {
    private final Expression left;
    private final Expression right;
    private final String operator;

    public BinaryExpression(Expression left, String operator, Expression right) {
        this.left = left;
        this.operator = operator;
        this.right = right;
    }

    @Override
    public double interpret(Map<String, Double> context) {
        // 자식부터 재귀 평가 → 우리 연산 적용 (후위 순회)
        double l = left.interpret(context);
        double r = right.interpret(context);
        // switch expression (Java 14+)으로 연산자별 분기
        return switch (operator) {
            case "+" -> l + r;
            case "-" -> l - r;
            case "*" -> l * r;
            case "/" -> {
                if (r == 0) throw new ArithmeticException("0으로 나눌 수 없음");
                yield l / r;
            }
            default -> throw new RuntimeException("알 수 없는 연산자: " + operator);
        };
    }

    @Override
    public String toFormula() {
        // 우선순위 보장을 위해 항상 괄호로 감쌈 (단순화)
        return "(" + left.toFormula() + " " + operator + " " + right.toFormula() + ")";
    }
}

// Non-Terminal Expression: 함수 호출
// 단일 인자 함수 (sqrt, abs 등)
class FunctionExpression implements Expression {
    private final String funcName;
    private final Expression argument;

    public FunctionExpression(String funcName, Expression argument) {
        this.funcName = funcName;
        this.argument = argument;
    }

    @Override
    public double interpret(Map<String, Double> context) {
        // 인자 표현식부터 평가
        double val = argument.interpret(context);
        return switch (funcName) {
            case "abs" -> Math.abs(val);
            case "sqrt" -> Math.sqrt(val);
            case "ceil" -> Math.ceil(val);
            case "floor" -> Math.floor(val);
            default -> throw new RuntimeException("알 수 없는 함수: " + funcName);
        };
    }

    @Override
    public String toFormula() {
        return funcName + "(" + argument.toFormula() + ")";
    }
}

// 간단한 표현식 빌더 (DSL)
// 정적 팩토리로 표현식 트리를 자연스럽게 조립 — 짧은 코드로 AST 구성
class ExprDSL {
    // 숫자 리터럴
    public static Expression num(double value) {
        return new NumberExpression(value);
    }

    // 변수 참조
    public static Expression var(String name) {
        return new VariableExpression(name);
    }

    // 산술 연산자들 — 이항 표현식 생성
    public static Expression add(Expression left, Expression right) {
        return new BinaryExpression(left, "+", right);
    }

    public static Expression sub(Expression left, Expression right) {
        return new BinaryExpression(left, "-", right);
    }

    public static Expression mul(Expression left, Expression right) {
        return new BinaryExpression(left, "*", right);
    }

    public static Expression div(Expression left, Expression right) {
        return new BinaryExpression(left, "/", right);
    }

    // 함수 호출 헬퍼
    public static Expression sqrt(Expression expr) {
        return new FunctionExpression("sqrt", expr);
    }

    public static Expression abs(Expression expr) {
        return new FunctionExpression("abs", expr);
    }
}

public class InterpreterDemo {
    public static void main(String[] args) {
        // DSL로 표현식 구성: sqrt(x^2 + y^2) = sqrt(x*x + y*y)
        // 트리 형태로 AST 직접 조립
        Expression distance = ExprDSL.sqrt(
            ExprDSL.add(
                ExprDSL.mul(ExprDSL.var("x"), ExprDSL.var("x")),
                ExprDSL.mul(ExprDSL.var("y"), ExprDSL.var("y"))
            )
        );

        System.out.println("수식: " + distance.toFormula());

        // 컨텍스트(변수 바인딩)에 따라 다른 결과
        // 같은 AST를 다른 입력으로 재평가 — 트리 재사용성
        Map<String, Double> ctx1 = Map.of("x", 3.0, "y", 4.0);
        System.out.println("x=3, y=4 -> 거리 = " + distance.interpret(ctx1));

        Map<String, Double> ctx2 = Map.of("x", 5.0, "y", 12.0);
        System.out.println("x=5, y=12 -> 거리 = " + distance.interpret(ctx2));

        // 할인 계산 DSL: price * (1 - discount / 100)
        // 비즈니스 룰을 표현식 트리로 — 외부 설정에서 로드 가능한 형태
        Expression discountCalc = ExprDSL.mul(
            ExprDSL.var("price"),
            ExprDSL.sub(ExprDSL.num(1), ExprDSL.div(ExprDSL.var("discount"), ExprDSL.num(100)))
        );

        System.out.println("\n할인 수식: " + discountCalc.toFormula());

        // 가변 컨텍스트 — 입력만 바꿔 다양한 시나리오 평가
        Map<String, Double> ctx3 = new HashMap<>();
        ctx3.put("price", 50000.0);
        ctx3.put("discount", 20.0);
        System.out.println("가격=50000, 할인=20% -> " + discountCalc.interpret(ctx3) + "원");

        ctx3.put("price", 30000.0);
        ctx3.put("discount", 10.0);
        System.out.println("가격=30000, 할인=10% -> " + discountCalc.interpret(ctx3) + "원");

        // 출력:
        // 수식: sqrt(((x * x) + (y * y)))
        // x=3, y=4 -> 거리 = 5.0
        // x=5, y=12 -> 거리 = 13.0
        //
        // 할인 수식: (price * (1 - (discount / 100)))
        // 가격=50000, 할인=20% -> 40000.0원
        // 가격=30000, 할인=10% -> 27000.0원
    }
}
```

**실행 결과** — 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다).

**풀이 요점**
- 노드 클래스는 Terminal 둘(`NumberExpression`, `VariableExpression`)과 Non-Terminal 둘(`BinaryExpression`, `FunctionExpression`)로 나뉜다.
- `interpret` 는 자식부터 재귀로 계산하는 후위 순회라서, 트리 모양이 곧 계산 차례다.
- 컨텍스트를 인자로 넘기므로 같은 트리를 여러 입력으로 다시 쓸 수 있다 — `ctx3` 는 `put` 으로 값만 바꿔 재평가한다.
- `ExprDSL` 의 정적 메서드 호출이 겹치는 모양이 그대로 AST 모양이다.
- 오류(미정의 변수, 0 나눗셈, 모르는 연산자 · 함수)는 조립할 때가 아니라 `interpret` 할 때 드러난다.
- `import java.util.Stack;` 은 쓰이지 않는다 — 문자열 파서는 이 코드의 범위 밖이다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
