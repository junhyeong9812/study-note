# java/syntax/23 — `switch` 패턴 매칭 (21): 완결성 · `null` · `when` 가드 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> ★ **이 주제의 무게는 1(바이트코드)·3(`null`)·4(지배)에 있다.**
> 모든 코드는 Temurin **JDK 21.0.5** 기준이다 — **17 에서는 아예 컴파일되지 않는다**(11번).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★ 패턴 `switch` 는 무엇으로 컴파일되나 (예측)

```java
sealed interface Shape permits Circle, Square, Rect { }
record Circle(double r) implements Shape { }
record Square(double side) implements Shape { }
record Rect(double w, double h) implements Shape { }

static String name(Shape s) {
    return switch (s) {
        case Circle c -> "원";
        case Square q -> "정사각형";
        case Rect   r -> "직사각형";
    };
}
```

- 이것은 `if-else` 사슬로 펼쳐지는가, 아니면 다른 무언가가 되는가?
- 타입 판별에 쓰이는 **명령 이름**은 무엇인가?
- 같은 판의 javac 로 찍은 **`enum` `switch` 식**(21번 주제)과 어디서 갈라지는가?
- 소스에 `default` 가 없는데 바이트코드에는 있는가 — 있다면 무엇을 하는가?
- `javap -v -p` 의 `BootstrapMethods` 에는 무엇이 찍히는가?

### 2. 완결성을 만드는 네 가지 (경계)

- `default` 없이 완결하게 만드는 방법은 몇 가지이며 각각 무엇인가?
- 그중 **새 타입이 생겼을 때 빌드를 멈춰 주는 것**은 어느 것인가?
- `default` 와 `case Object o` 를 같이 쓰면 어떻게 되는가?
- 패턴 `switch` **문**(statement)은 완결해야 하는가 — 옛 `enum` `switch` 문과 다른가?

### 3. ★ `null` 을 넣으면 (예측)

```java
// (a) 옛 switch
enum Day { MON, SAT }
switch (d) { case MON: return "월"; case SAT: return "토"; default: return "?"; }

// (b)
switch (o) { case null -> "널이다"; case String s -> "문자열"; default -> "그 밖"; }

// (c)
switch (o) { case String s -> "문자열"; case null, default -> "널이거나 그 밖"; }

// (d)
switch (o) { case String s -> "문자열"; case Integer i -> "정수"; default -> "그 밖"; }

// (e) sealed 완결, case null 없음
switch (sh) { case Circle c -> "원"; case Square q -> "정사각형"; }
```

- (a)~(e)에 각각 `null` 을 넣으면 무엇이 나오는가?
- ★ (d)에는 **`default` 가 있다.** 그런데도 결과가 그런 이유는 무엇인가?
- (d)의 예외 스택 트레이스 **맨 윗줄**에는 무엇이 찍히는가?
- `case null` 이 **있을 때와 없을 때** 바이트코드는 어디가 달라지는가?
- `case null, String s ->` 처럼 다른 패턴과 묶을 수 있는가?

### 4. ★ `case` 의 순서 (예측)

```java
// (a)
switch (o) { case Object x -> "아무거나"; case String s -> "문자열"; default -> "그 밖"; }

// (b) Shape 는 sealed, Circle 은 그 하위
switch (sh) { case Shape x -> "도형"; case Circle c -> "원"; }

// (c)
switch (o) { case String s -> "문자열"; default -> "그 밖"; case Integer i -> "정수"; }
```

- (a)·(b)·(c)는 각각 어떤 에러를 내는가?
- (a)는 에러가 **몇 개** 나오며 왜 그런가?
- (c)에서 `default` 가 마지막이 아니어도 되는가 — 옛 `switch` 와 다른가?
- 이 규칙을 한 문장으로 말하면 무엇인가?

### 5. ★ 가드가 붙으면 지배는 어떻게 되나 (예측)

```java
// (a)
switch (o) {
    case String s when s.length() > 3 -> "긴 문자열";
    case String s when s.length() > 3 -> "또 긴 문자열";
    case String s -> "짧은 문자열";
    default -> "그 밖";
}

// (b)
switch (o) {
    case String s -> "문자열";
    case String s when s.length() > 3 -> "긴 문자열";
    default -> "그 밖";
}
```

- (a)는 컴파일되는가? 된다면 `f("a")` 의 출력은?
- (b)는 컴파일되는가? 안 된다면 에러는?
- 둘의 차이를 만드는 규칙은 무엇인가?
- 컴파일러가 (a)를 잡아 주지 않는 이유는 무엇이라고 생각하는가?

### 6. `when` 가드의 평가 순서 (예측)

```java
static StringBuilder log = new StringBuilder();
static boolean check(String tag, boolean v) { log.append(tag); return v; }

static String order(Object o) {
    return switch (o) {
        case String s when check("A", s.length() > 100) -> "A";
        case String s when check("B", s.length() > 10)  -> "B";
        case String s when check("C", s.length() > 1)   -> "C";
        case String s                                   -> "D";
        default                                         -> "그 밖";
    };
}
```

- `order("abc")` 의 반환값과 `log` 는 각각 무엇인가?
- `order("a")` 는?
- 이 결과가 가드 작성에 주는 실무 규칙은 무엇인가?
- `when` 은 예약어인가 — `yield` 와 비교하면?

### 7. 가드만으로 완결할 수 있나 (경계)

```java
static String f(Object o) {
    return switch (o) {
        case String s when s.length() > 3 -> "긴 문자열";
    };
}
```

- 이것은 컴파일되는가? 안 된다면 무엇이 출력되는가?
- `String` 이 아닌 값이 문제인가, 아니면 다른 이유가 있는가?
- 고치는 방법 둘은 무엇인가?
- 가드 붙은 `case` 와 무가드 `case` 는 완결성 계산에서 어떻게 다루어지는가?

### 8. selector 타입과 상수 레이블 (경계)

```java
static String f(Object o) {
    return switch (o) {
        case String s -> "문자열";
        case "hello"  -> "인사";
        default       -> "그 밖";
    };
}
```

- 이것은 컴파일되는가? 안 된다면 정확히 무엇이 출력되는가?
- `switch (s)` 에서 `s` 가 `String` 이면 `case "hello"` 는 되는가?
- `case null` 을 두 번 쓰면 어떤 에러인가?
- `case int[] a` 처럼 배열 타입을 패턴으로 쓸 수 있는가?

### 9. ★ `sealed` 계층이 컴파일 후에 바뀌었다 (예측)

```text
1차:  Shape.java   public sealed interface Shape permits Circle, Square { }
      Ex.java      switch (sh) { case Circle c -> "원"; case Square q -> "정사각형"; }   // default 없음
      -> javac -d out *.java   (성공)

2차:  Shape 를 permits Circle, Square, Triangle 로 고치고 Triangle.java 를 추가
      -> javac -cp out -d out Shape.java Triangle.java   (Ex 는 다시 컴파일하지 않는다)
```

- 2차 컴파일은 성공하는가?
- `Circle` 을 넣으면 무엇이 나오는가?
- `Triangle` 을 넣으면 무엇이 나오는가 — 예외라면 **정확한 클래스 이름**은?
- 1차 컴파일 직후 `javap -v -p` 의 `Method arguments` 에는 무엇이 있었는가 — 2차 뒤에 그것이 바뀌었는가?
- `MatchException` 의 javadoc 은 이 사례를 뭐라고 부르는가?

### 10. `if` 사슬과 무엇이 다른가 (왜)

```java
static String nameByIfElse(Shape s) {
    if (s instanceof Circle c) return "원";
    if (s instanceof Square q) return "정사각형";
    return "빠뜨린 것이 여기로 온다";
}
```

- `Rect` 를 넣으면 무엇이 나오는가?
- 컴파일러가 경고를 주는가?
- 같은 분기를 `sealed` + `switch` 로 쓰면 무엇이 달라지는가?
- 그래서 `if` 사슬을 `switch` 로 옮기는 기준은 무엇인가?

### 11. ★ 17 에서 컴파일하면 (경계 · 버전)

- JDK 17 의 javac 로 위 `name()` 을 컴파일하면 무엇이 출력되는가?
- JDK 21 의 `javac --release 17` 로 컴파일하면 메시지가 같은가?
- 17 에서 `--enable-preview` 를 붙이면 컴파일되는가?
- 그렇게 만든 클래스 파일을 `--enable-preview` 없이 실행하면? JDK 21 로 실행하면?
- 그 클래스 파일의 **버전 번호**는 무엇이며 무슨 뜻인가?

### 12. 정본 경계와 선행 버전 (연결)

- 이 주제와 **15번**(`sealed`)·**21번**(`switch` 문법)·**22번**(타입 패턴)·**24번**(`record` 패턴)의 경계는 각각 어디인가?
- 이 주제의 선행 넷은 각각 몇 부터인가?
- `invokedynamic typeSwitch` 라는 이름은 보장인가 구현 세부인가?
- "`default` 가 `null` 을 안 받는다"는 옛 `switch` 와 비교해 **바뀐 것인가 그대로인가**?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
