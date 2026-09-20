# java/syntax/24 — `record` 패턴 (21): 중첩 해체 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> ★ **이 주제의 무게는 2·3(`null`)에 있다.** 문법은 한 시간이면 외우지만 그 규칙은 계속 틀린다.
> 모든 코드는 Temurin **JDK 21.0.5** 기준이다 — **17 에서는 파싱조차 안 된다**(9번).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 한 줄이 무엇으로 펼쳐지나 (예측)

```java
record Point(int x, int y) { }
record Line(Point from, Point to) { }

static String withRecordPattern(Object o) {
    if (o instanceof Line(Point(int ax, int ay), Point(int bx, int by)))
        return "(" + ax + "," + ay + ")-(" + bx + "," + by + ")";
    return "그 밖";
}
```

- 컴포넌트 값을 누가 꺼내는가 — 컴파일러가 만드는 명령은 무엇인가?
- 접근자 호출 결과마다 무엇이 따라붙는가?
- `javap -c -p` 의 **예외 테이블**에는 무엇이 있는가 — 그 구간은 어디인가?
- 이 사실이 실무에서 주는 주의 하나는 무엇인가?

### 2. ★ `null` 컴포넌트 — 네 가지 (예측)

```java
record Holder(Object o) { }      // 컴포넌트 타입이 Object
record Typed(Point p) { }        // 컴포넌트 타입이 Point

new Holder(null) instanceof Holder(Object o)             // (a)
new Holder(null) instanceof Holder(String s)             // (b)
new Typed(null)  instanceof Typed(Point p)               // (c)
new Typed(null)  instanceof Typed(Point(var x, var y))   // (d)
```

- (a)~(d)는 각각 `true` 인가 `false` 인가?
- (a)가 `true` 일 때 `o` 의 값은 무엇인가?
- 네 결과를 **한 문장의 규칙**으로 정리하면 무엇인가?
- 그 규칙이 바이트코드의 **어느 차이**에서 나오는가?

### 3. ★ 완결한데 안 맞는다 (예측)

```java
sealed interface I permits A, B { }
record A(int n) implements I { }
record B(String s) implements I { }
record R(I i) { }

static String f(R r) {
    return switch (r) {
        case R(A a) -> "A " + a.n();
        case R(B b) -> "B " + b.s();
    };
}
static String g(R r) {
    return switch (r) { case R(I i) -> "I " + i; };
}
```

- `f` 는 `default` 가 없는데 컴파일되는가?
- `f(new R(new A(1)))` · `g(new R(null))` · `f(new R(null))` 은 각각 무엇인가?
- 예외라면 **정확한 클래스 이름**은 무엇인가?
- `MatchException` 의 javadoc 은 이 상황을 예고하고 있는가 — 몇 번째 사례인가?
- 이 `MatchException` 은 [**23번 주제**](../23-switch-pattern-matching/)의 것과 원인이 같은가?

### 4. 접근자가 던지면 (예측)

```java
record Bad(int v) {
    @Override public int v() { throw new IllegalStateException("접근자가 터졌다"); }
}
record Wrap(Bad b) { }
...
Object o = new Wrap(new Bad(1));
if (o instanceof Wrap(Bad(int v))) System.out.println("v=" + v);
```

- 무엇이 던져지는가 — `IllegalStateException` 인가 다른 것인가?
- 원래 예외는 어디로 가는가?
- 이것을 만드는 바이트코드 장치는 무엇인가?
- 여기서 나오는 실무 규칙은 무엇인가?

### 5. `var` 와 제네릭 (예측)

```java
record Point(int x, int y) { }
record Box<T>(T value) { }

// (a)
if (o instanceof Point(var x, var y)) return "x=" + x + " y=" + y + " (x+y=" + (x + y) + ")";

// (b)
case Box<?>(String s)  -> "문자열 상자 " + s.toUpperCase();

// (c)
static String inferred(Box<String> b) { if (b instanceof Box(String s)) return "추론된 String " + s; return "?"; }
```

- (a)에서 `(x + y)` 는 무엇을 출력하는가 — `var` 가 무슨 타입으로 추론됐는가?
- (b)처럼 타입 인자를 적을 수 있는가 — `Box<String>(String s)` 는 어떤가?
- (c)처럼 타입 인자를 생략하면 추론되는가?
- `instanceof var v` 는 왜 막히는데 `Point(var x, var y)` 는 되는가?

### 6. 중첩과 이름 (경계)

```java
// (a)
case Colored(Line(Point(var ax, var ay), Point(var bx, var by)), String color) -> ...;

// (b)
case Line(Point from, Point(int bx, int by)) -> ...;

// (c)
if (o instanceof Point(int x, int y) p) System.out.println(p);
```

- (a)는 몇 겹인가 — 깊이 제한이 있는가?
- (b)처럼 한쪽만 해체할 수 있는가?
- (c)는 컴파일되는가 — 안 된다면 에러가 **몇 개**이며 어떤 종류인가?
- 통째와 해체가 **같은 자리에** 동시에 필요하면 어떻게 하는가?

### 7. 개수와 타입이 안 맞으면 (경계)

```java
// (a)
if (o instanceof Point(int x)) ...

// (b)
if (o instanceof Point(var x, var y, var z)) ...

// (c)
if (o instanceof Point(String x, int y)) ...

// (d)
static class Plain { int x, y; }
if (o instanceof Plain(int x, int y)) ...
```

- (a)~(d)는 각각 어떤 에러를 내는가?
- (a)와 (b)의 메시지에서 `required:`/`found:` 는 각각 무엇으로 찍히는가?
- (d)의 메시지가 알려 주는 이 문법의 **정식 이름**은 무엇인가?
- `record` 에 컴포넌트를 추가하면 기존 `record` 패턴은 어떻게 되는가 — 그것은 좋은 일인가?

### 8. ★ 원시 타입을 넓혀 받으려 하면 (경계 · 버전)

```java
record Point(int x, int y) { }
if (o instanceof Point(long x, long y)) System.out.println(x + y);
```

- JDK 21 에서는 무엇이 출력되는가 — 에러는 **몇 개**인가?
- JDK **25** 에서는 같은 메시지인가?
- 25 에서 `--enable-preview` 를 붙이면 컴파일되는가 — 출력은?
- 두 메시지가 다르다는 사실이 문서 작성에 주는 규칙은 무엇인가?

### 9. ★ 17 에서 컴파일하면 (경계 · 버전)

```java
record Point(int x, int y) { }
if (o instanceof Point(int x, int y)) System.out.println(x + y);
```

- JDK 17 의 javac 는 무엇을 출력하는가?
- JDK 21 의 `javac --release 20` 은 같은 메시지인가?
- 두 메시지가 이렇게 다른 이유는 무엇인가?
- [**23번 주제**](../23-switch-pattern-matching/)의 패턴 `switch` 를 17 에서 컴파일했을 때와 비교하면?

### 10. 가드와 함께 (예측)

```java
return switch (o) {
    case Point(int x, int y) when x == y                   -> "대각선 위의 점 " + x;
    case Point(int x, int y)                               -> "점 " + x + "," + y;
    case Line(Point(var ax, var ay), Point p) when ax == 0 -> "y축에서 시작하는 선, to=" + p;
    case Line(Point a, Point b)                            -> "선 " + a + "-" + b;
    default                                                -> "그 밖";
};
```

- `f(new Point(3, 3))` 와 `f(new Point(1, 2))` 는 각각 무엇인가?
- 가드 안에서 해체로 꺼낸 이름(`ax`)을 쓸 수 있는가?
- 한 가지 안에서 통째(`Point p`)와 해체를 섞을 수 있는가?
- `case Point(int x, int y) when x == y` 를 뒤로 옮기면 어떻게 되는가?

### 11. 언제 쓰고 언제 안 쓰나 (연결)

- `record` 패턴을 안 쓰는 편이 나은 경우 넷은 무엇인가?
- 컴포넌트에 `null` 이 들어올 수 있으면 먼저 무엇을 하는가 — 그 문법은 어느 주제가 정본인가?
- 사용자 정의 해체(deconstructor)는 21·25 에 있는가?
- 그 사실이 설계에 주는 압력은 무엇인가?

### 12. 정본 경계 (연결)

- 이 주제와 **14번**(`record`)·**22번**(타입 패턴)·**23번**(패턴 `switch`)·**15번**(`sealed`)의 경계는 각각 어디인가?
- `MatchException` 은 23번과 24번에 각각 **어떤 사례**로 나오는가?
- 무조건 패턴에 `instanceof` 가 없다는 것은 보장인가 구현 세부인가 — 그 **결과**는?
- 이 주제에서 **판마다 메시지가 달랐던 자리 둘**은 어디인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
