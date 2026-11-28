# java/java-advanced-patterns/04 — Interpreter Pattern (인터프리터 패턴) — 정리 (힌트)

> 출처 — study-site 항목 `java/interpreter`(항목 데이터 `data/java/advanced-patterns.json`) · 정답 코드 study-practice `java/java-advanced-patterns/reference/interpreter.java`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다).

## 한눈에 — 쉽게 말하면

**Interpreter 패턴은 「레시피 카드 묶음」이다.**
레시피 카드 한 장에는 「밀가루 200g」 같은 재료 줄도 있고, 「앞의 두 가지를 섞는다」 같은 조합 줄도 있다.
카드 묶음은 한 번 써 두면 그대로이고, 오늘 냉장고에 무엇이 있느냐(재료 값)에 따라 결과물만 달라진다.
Interpreter 패턴도 똑같은 구조다.
문법의 각 규칙을 클래스 하나로 만들고, 그 클래스들의 객체를 트리로 엮은 뒤, 변수 값을 담은 맵(컨텍스트)을 넣어 트리를 「해석」한다.

| 비유 | 실체 |
|---|---|
| 레시피 카드 묶음 | 표현식 트리(`Expression` 객체들) |
| 재료 줄 | Terminal Expression (`NumberExpression`, `VariableExpression`) |
| 「섞는다」 같은 조합 줄 | Non-Terminal Expression (`BinaryExpression`, `FunctionExpression`) |
| 오늘 냉장고 속 재료 | 컨텍스트 `Map<String, Double>` |
| 요리하기 | `interpret(context)` |
| 카드를 소리 내어 읽기 | `toFormula()` |

```text
  [표현식 트리]  +  [컨텍스트 {x=3, y=4}]
        │                 │
        └──── interpret ──┘
                 │
                 ▼
               결과 값
```

> **Interpreter 패턴** — 간단한 언어의 문법을 클래스로 정의하고, 그 클래스로 만든 트리를 해석(평가)하는 디자인 패턴이다.\
> 예: 수식 `sqrt(x*x + y*y)` 를 객체 트리로 만들어 `x`, `y` 값을 넣고 계산한다.

> **DSL(도메인 특화 언어)** — 한 분야의 문제만 표현하도록 만든 작은 언어다.\
> 예: 할인 규칙 `price * (1 - discount / 100)` 만 적는 계산 언어.

## 이 주제가 답하려는 질문

1. 작은 언어의 문법 규칙을 객체지향 코드로 어떻게 옮기나?
2. 한 번 만든 표현식을 서로 다른 입력으로 어떻게 반복해 평가하나?
3. 같은 트리에서 「값 계산」과 「문자열로 보이기」처럼 서로 다른 일을 어떻게 하나?
4. 이 패턴은 어디까지 쓸 만하고, 어디서부터 다른 도구가 낫나?

## 동작 방식

### (1) 문법 규칙 하나 = 클래스 하나

**언제 쓰나** — 다룰 언어의 문법이 「숫자, 변수, 이항 연산, 함수 호출」처럼 몇 개의 규칙으로 끝날 때 쓴다.

```text
문법 규칙                          클래스
─────────────────────────────────────────────────────────
표현식    (공통 계약)          →  interface Expression
숫자      3, 100               →  NumberExpression      (Terminal)
변수      x, price             →  VariableExpression    (Terminal)
식 연산자 식   (+ - * /)       →  BinaryExpression      (Non-Terminal)
함수(식)  sqrt, abs, ceil, floor → FunctionExpression   (Non-Terminal)
```

- 맨 위 `Expression` 인터페이스가 모든 노드의 공통 계약이다 — `interpret(context)` 와 `toFormula()` 두 메서드를 강제한다.
- Terminal 은 더 쪼개지지 않는 잎 노드다 — 숫자는 자기 값을, 변수는 컨텍스트에서 찾은 값을 돌려준다.
- Non-Terminal 은 자식 `Expression` 을 필드로 가진 내부 노드다 — 그래서 트리가 재귀 구조가 된다.

> **Abstract Expression** — 모든 노드가 따르는 공통 인터페이스다.\
> 예: `interface Expression`.

> **Terminal Expression** — 자식이 없는 잎 노드 클래스다.\
> 예: `NumberExpression(3.0)`.

> **Non-Terminal Expression** — 다른 표현식을 자식으로 품는 내부 노드 클래스다.\
> 예: `BinaryExpression(left, "+", right)`.

### (2) 정적 팩토리로 트리를 조립한다

**언제 쓰나** — `new BinaryExpression(new VariableExpression("x"), "*", …)` 처럼 길어지는 생성 코드를 짧고 읽기 쉽게 만들 때 쓴다.

```text
ExprDSL.sqrt(                                   sqrt
  ExprDSL.add(                                   └─ +
    ExprDSL.mul(var("x"), var("x")),     →          ├─ *
    ExprDSL.mul(var("y"), var("y"))                 │  ├─ x
  )                                                 │  └─ x
)                                                   └─ *
                                                       ├─ y
                                                       └─ y
```

- `ExprDSL.num`, `var` 는 Terminal 노드를 만든다.
- `add`, `sub`, `mul`, `div` 는 연산자 문자열을 정해 `BinaryExpression` 을 만든다.
- `sqrt`, `abs` 는 함수 이름을 정해 `FunctionExpression` 을 만든다.
- 메서드 호출이 안쪽으로 겹치는 모양이 그대로 트리의 모양이 된다.
- 이렇게 만든 트리를 AST(추상 구문 트리)라고 부른다.

> **AST(추상 구문 트리)** — 식의 구조를 괄호나 공백 없이 노드와 자식 관계로만 나타낸 트리다.\
> 예: `x * x` 는 `*` 노드 아래 `x`, `x` 두 잎이 달린 트리다.

> **정적 팩토리** — `new` 대신 객체를 만들어 돌려주는 `static` 메서드다.\
> 예: `ExprDSL.num(1)` 은 `new NumberExpression(1)` 을 돌려준다.

### (3) `interpret` — 자식부터 재귀로 계산한다

**언제 쓰나** — 트리의 값을 구할 때마다 쓴다. 컨텍스트만 바꿔 넣으면 같은 트리가 다른 값을 낸다.

```text
distance.interpret({x=3, y=4})

sqrt ─ 인자부터 계산 ─▶ +  ─ 왼쪽 먼저 ─▶ *(x,x) → x=3 찾음, 3*3 = 9
                           ─ 오른쪽   ─▶ *(y,y) → y=4 찾음, 4*4 = 16
                         + 적용 → 9 + 16 = 25
       sqrt 적용 → sqrt(25) = 5
```

- `BinaryExpression.interpret` 는 `left.interpret(context)` 를 먼저, `right.interpret(context)` 를 다음에 부른다.
- 두 값이 모두 나온 뒤에야 자기 연산자를 적용한다 — 자식 → 부모 차례라서 후위 순회다.
- `FunctionExpression` 도 인자를 먼저 평가한 뒤 `Math.sqrt` 같은 함수를 적용한다.
- `VariableExpression` 은 컨텍스트 맵에서 자기 이름으로 값을 꺼낸다.
- 트리는 값을 품지 않으므로, 컨텍스트를 `{x=5, y=12}` 로 바꿔 다시 부르면 같은 트리에서 새 결과가 나온다(트리 재사용).

> **컨텍스트** — 해석할 때 넘겨주는 바깥 정보다. 여기서는 변수 이름 → 값의 맵이다.\
> 예: `Map.of("x", 3.0, "y", 4.0)`.

> **후위 순회** — 자식을 모두 처리한 뒤 부모를 처리하는 트리 방문 차례다.\
> 예: `+` 는 왼쪽·오른쪽 값이 다 나온 뒤에 더한다.

### (4) `toFormula` — 같은 트리, 다른 일

**언제 쓰나** — 만든 트리가 어떤 식인지 사람이 읽을 수 있게 확인할 때 쓴다.

```text
NumberExpression(1.0)    → "1"      (정수처럼 보이면 정수로)
NumberExpression(2.5)    → "2.5"
VariableExpression("x")  → "x"
BinaryExpression(x,*,x)  → "(x * x)"          (항상 괄호)
FunctionExpression(sqrt, e) → "sqrt(" + e + ")"
```

- `NumberExpression` 은 `value == (int) value` 로 소수 부분이 0 인지 보고, 그렇다면 정수 꼴로 쓴다.
- `BinaryExpression` 은 연산자 우선순위를 따지지 않고 **언제나** 바깥을 괄호로 감싼다 — 단순화한 선택이다.
- 그래서 문자열에 괄호가 넉넉히 붙지만, 계산 차례가 문자열에서 애매해지는 일은 없다.
- 노드마다 `interpret` 와 `toFormula` 를 둘 다 구현했다는 점이 중요하다 — 연산이 하나 늘 때마다 모든 노드 클래스에 메서드가 하나씩 늘어난다.

### (5) 해석 중에 생기는 오류

**언제 쓰나** — 잘못된 입력이 들어왔을 때 어디서 멈추는지 알아야 할 때 본다.

```text
상황                                   어디서 던지나               예외
────────────────────────────────────────────────────────────────────────────
컨텍스트에 없는 변수                    VariableExpression        RuntimeException("정의되지 않은 변수: …")
'/' 의 오른쪽 값이 0                    BinaryExpression          ArithmeticException("0으로 나눌 수 없음")
모르는 연산자 문자열                    BinaryExpression          RuntimeException("알 수 없는 연산자: …")
모르는 함수 이름                        FunctionExpression        RuntimeException("알 수 없는 함수: …")
```

- 오류는 트리를 만들 때가 아니라 `interpret` 를 부를 때 드러난다.
- 왼쪽 자식을 먼저 평가하므로, 문제 노드가 오른쪽에 있으면 왼쪽 계산은 끝난 뒤에 예외가 난다.

## 문법 — 형태와 규칙

```java
// 최소 예제 — 숫자와 덧셈만 있는 언어
interface Expr { double eval(); }

class Num implements Expr {
    private final double v;
    Num(double v) { this.v = v; }
    public double eval() { return v; }             // Terminal: 자기 값
}

class Add implements Expr {
    private final Expr l, r;
    Add(Expr l, Expr r) { this.l = l; this.r = r; }
    public double eval() { return l.eval() + r.eval(); }  // Non-Terminal: 자식 재귀
}

// 사용: (1 + 2) + 3
Expr e = new Add(new Add(new Num(1), new Num(2)), new Num(3));
```

- 공통 인터페이스 하나를 두고, 모든 노드가 그것을 구현한다.
- Terminal 은 자식 필드가 없고, Non-Terminal 은 자식 필드의 타입이 공통 인터페이스다.
- 연산 분기는 `switch` 식(`case "+" -> l + r;`)으로 쓸 수 있다 — 원본 주석은 Java 14+ 문법이라고 적는다.
- `switch` 식의 블록 갈래에서 값을 내려면 `yield` 를 쓴다(`case "/" -> { …; yield l / r; }`).
- 필드를 `final` 로 두어 한 번 만든 트리가 바뀌지 않게 한다.
- 컨텍스트는 `interpret` 의 인자로 넘긴다 — 트리 안에 넣지 않는다.

## 어디서 틀리나

### 1. 문법이 복잡해지면 클래스가 폭발한다

원본 팁: Interpreter 패턴은 **문법이 간단하고 변경이 적을 때** 적합하다.
규칙 하나마다 클래스가 하나라서, 우선순위 단계 · 문장 · 블록 같은 규칙이 늘면 클래스 수와 재귀 구조가 감당하기 어려워진다.
원본 팁은 복잡한 문법에는 ANTLR 같은 **파서 생성기**를 쓰는 편이 낫다고 한다.

> **파서 생성기** — 문법 정의를 넣으면 그 문법의 파서 코드를 만들어 주는 도구다.\
> 예: ANTLR.

### 2. 새 「연산」을 더하면 모든 노드를 고쳐야 한다

`interpret` 와 `toFormula` 처럼 연산이 노드 안에 있으므로, 예컨대 「변수 목록 뽑기」를 더하려면 모든 노드 클래스에 메서드를 추가해야 한다.
원본 팁: 표현식 트리와 **Visitor 패턴**을 조합하면 다양한 연산을 추가할 수 있다.
연산을 노드 밖의 방문자 객체로 빼면, 노드는 그대로 두고 방문자 클래스만 새로 만들면 된다.

> **Visitor 패턴** — 객체 구조는 그대로 두고, 그 구조를 도는 연산을 별도 객체로 분리하는 디자인 패턴이다.\
> 예: `FormulaVisitor`, `EvalVisitor` 를 따로 두고 같은 트리에 번갈아 적용한다.

### 3. 이 예제에는 「파서」가 없다 — 원본의 주장 → 왜 의심스러운가

원본은 예제를 「수학 표현식 DSL 파서 & 평가기」라 부르고, 키워드에 표현식파싱 · 파서 · 구문분석을 둔다.
그러나 코드에는 `"x*x + y*y"` 같은 문자열을 읽어 트리로 바꾸는 부분이 없다 — 트리는 `ExprDSL` 호출로 손으로 조립한다.
`import java.util.Stack;` 도 쓰이지 않는다(원본 주석이 「학습용 import — 후위 표기식 파서에 활용 가능」이라고 스스로 밝힌다).
Interpreter 패턴의 핵심은 **트리를 해석하는 쪽**이고, 문자열 → 트리 단계(구문분석)는 따로 만들어야 하는 일이다.
같은 까닭으로 「비즈니스 룰을 외부 설정에서 로드 가능한 형태」라는 주석도, 문자열을 트리로 바꾸는 파서가 있어야 비로소 맞는 말이다.

> **구문분석(파싱)** — 글자로 된 식을 읽어 문법에 맞는 트리로 바꾸는 일이다.\
> 예: 문자열 `"1 + 2"` → `BinaryExpression(Num 1, "+", Num 2)`.

### 4. 미정의 변수는 해석할 때야 터진다

트리를 만들 때는 변수 이름만 기억한다.
컨텍스트에 그 이름이 없으면 `interpret` 도중 `RuntimeException("정의되지 않은 변수: …")` 이 난다.

### 5. `toFormula` 의 괄호는 「최소」가 아니다

우선순위를 계산하지 않고 언제나 괄호로 감싸므로 `(price * (1 - (discount / 100)))` 처럼 괄호가 겹친다.
읽기 싫어 괄호를 줄이려면 연산자 우선순위 비교 로직을 따로 넣어야 한다.

### 6. 문자열로 연산자 · 함수를 고르면 오타가 실행 때야 드러난다

`BinaryExpression` 은 연산자를 `String` 으로 받으므로 `"%"` 같은 모르는 값도 생성은 된다.
`default` 갈래가 `interpret` 때 예외를 던질 뿐이다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `switch` 식 `case … ->` · `yield` 문법 | Java 언어(원본 주석: Java 14+) |
| `/` 의 오른쪽이 0 이면 `ArithmeticException` | 이 코드 — `r == 0` 을 직접 검사해 던진다(언어가 시킨 것이 아니다) |
| 모르는 변수 · 연산자 · 함수에서 `RuntimeException` | 이 코드의 선택 |
| `BinaryExpression.toFormula` 는 항상 괄호로 감싼다 | 이 코드의 설계(단순화) |
| 소수 부분이 0 이면 정수 꼴로 쓴다 | 이 코드의 `value == (int) value` 판정 |
| 왼쪽 자식을 오른쪽보다 먼저 평가한다 | 이 코드 — `l` 을 구하는 문장을 `r` 보다 먼저 썼기 때문이다 |
| Abstract / Terminal / Non-Terminal 의 나눔 | 언어가 아니라 디자인 패턴의 관례 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 규칙 몇 개짜리 계산식 · 조건식을 여러 입력으로 반복 평가 | Interpreter 패턴 | 매번 `if` 를 늘어놓는 하드코딩 |
| 문법이 크고 자주 바뀜 | 파서 생성기(ANTLR 등) | 손으로 만든 Interpreter 클래스 묶음 |
| 같은 트리에 연산을 계속 더해야 함 | 표현식 트리 + Visitor | 노드마다 메서드를 계속 추가 |
| 정규 표현식 · SQL WHERE 절 · 템플릿 엔진 같은 작은 언어 | Interpreter 식 트리 구조 | 문자열을 그때그때 잘라 처리 |
| 식이 한 번만 쓰이고 고정임 | 그냥 Java 식 | 트리 클래스 묶음(과설계) |

## 핵심 문장

1. **문법 규칙 하나가 클래스 하나다** — 잎은 Terminal, 자식을 품으면 Non-Terminal.
2. **해석은 재귀다** — 자식을 먼저 평가하고 부모가 그 값에 자기 연산을 적용한다.
3. **트리와 컨텍스트를 나눈다** — 같은 트리에 다른 변수 값을 넣어 다른 결과를 얻는다.
4. **연산이 늘면 노드가 다 바뀐다** — 그래서 연산을 자주 더하면 Visitor 와 엮는다.
5. **간단하고 잘 안 바뀌는 문법에만** — 복잡하면 파서 생성기로 간다.

## 관련 자료

- `visitor-pattern` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `pipeline-pattern` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `fluent-api` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/java/advanced-patterns.json` 의 `interpreter`

## 용어 풀이

- **Interpreter 패턴** — 문법을 클래스로 정의하고 객체 트리를 해석하는 디자인 패턴.
- **DSL(도메인 특화 언어)** — 한 분야만 표현하는 작은 언어.
- **expression(표현식)** — 값으로 평가되는 식, 여기서는 `Expression` 노드.
- **Abstract Expression** — 모든 노드의 공통 인터페이스.
- **Terminal Expression** — 자식 없는 잎 노드.
- **Non-Terminal Expression** — 자식 표현식을 품는 내부 노드.
- **AST(추상 구문 트리)** — 식의 구조를 노드와 자식 관계로 나타낸 트리.
- **컨텍스트** — 해석할 때 넘기는 바깥 정보(변수 → 값 맵).
- **후위 순회** — 자식 먼저, 부모 나중에 방문하는 차례.
- **정적 팩토리** — 객체를 만들어 돌려주는 `static` 메서드.
- **문법해석** — 문법 트리의 의미를 계산하는 일(여기서는 `interpret`).
- **구문분석(파싱) · 파서** — 글자 식을 트리로 바꾸는 일 · 그 일을 하는 코드.
- **파서 생성기** — 문법 정의로 파서 코드를 만들어 주는 도구(ANTLR 등).
- **Visitor 패턴** — 구조는 두고 연산을 별도 객체로 분리하는 패턴.
- **`switch` 식** — 값을 돌려주는 `switch`, 블록 갈래에서는 `yield` 로 값을 낸다.

## 더 들어가면

- Interpreter 패턴의 트리 구조는 Composite 패턴(부분과 전체를 같은 인터페이스로 다루기)과 모양이 같다고 흔히 설명한다(확인 필요).
- Java 의 `double` 나눗셈은 0 으로 나눠도 예외 없이 `Infinity` 나 `NaN` 이 된다 — 이 코드가 `ArithmeticException` 을 직접 던지는 까닭이다(확인 필요).
- `(int) value` 는 `int` 범위를 넘는 큰 값에서 잘리므로, `1e10` 같은 값은 소수 부분이 0 이어도 정수 꼴로 쓰이지 않을 수 있다(확인 필요).
- `Map.of(...)` 로 만든 맵은 바꿀 수 없고 `null` 값을 받지 않는다(Java 9+, 확인 필요).
- `0.1`, `0.2` 같은 수는 이진 부동소수로 정확히 나타낼 수 없어, 할인 계산 결과에 아주 작은 오차가 붙을 가능성이 있다(확인 필요).
- 문자열 식을 트리로 바꾸려면 재귀 하향 파서나 Stack 을 쓰는 후위 표기(셔팅 야드 알고리즘) 변환을 쓸 수 있다(확인 필요).
