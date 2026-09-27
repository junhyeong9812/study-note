# java/syntax/15 — `sealed` (17+): `permits` 와 허용 계층의 조건 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **「어기면 무엇이 출력되나」형**이 많다.
> `sealed` 는 규약을 거는 기능이라, 되는 코드보다 **javac 가 거부하는 코드**가 지식의 대부분이다.
> 모든 코드는 Temurin **JDK 21.0.5** 기준이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 조건 셋 중 ① — 하위 타입에 수식어를 안 붙이면 (예측)

```java
public class Ex {
    sealed interface Shape permits Circle { }
    static class Circle implements Shape { }
    public static void main(String[] args) { }
}
```

- 이것은 컴파일되는가?
- 안 된다면 javac 는 **정확히 무엇을 출력하는가**?
- `static class Circle` 을 `record Circle(double r)` 로 바꾸면 통과하는가, 그 이유는 무엇인가?
- 하위 타입이 붙일 수 있는 수식어는 몇 가지이며 각각 무엇을 뜻하는가?

### 2. 조건 셋 중 ② — 명단과 상속이 어긋나면 (예측)

```java
// (a)
sealed interface Shape permits Circle { }
record Circle(double r) implements Shape { }
record Triangle(double b, double h) implements Shape { }

// (b)
sealed interface Shape permits Circle, Ghost { }
record Circle(double r) implements Shape { }
record Ghost() { }
```

- (a)와 (b)는 각각 컴파일되는가?
- 안 된다면 **두 에러 메시지는 어떻게 다른가**?
- (a)에서 `Triangle` 이 `Circle` 과 같은 파일에 있는데도 막히는 이유는 무엇인가?
- 손자 타입(`Circle` 의 하위)을 `permits` 에 적을 수 있는가?

### 3. 조건 셋 중 ③ — 다른 패키지를 `permits` 하면 (예측)

```text
src/
  shapes/Shape.java     public sealed interface Shape permits Circle, other.Triangle { }
  shapes/Circle.java    public record Circle(double r) implements Shape { }
  other/Triangle.java   public record Triangle(double b, double h) implements shapes.Shape { }
```

- 이 트리를 `javac -d out $(find src -name '*.java')` 로 컴파일하면 어떻게 되는가?
- 에러가 난다면 메시지의 **첫 구절**은 무엇인가 — 그 구절이 규칙의 정확한 모양에 대해 무엇을 알려 주는가?
- `src/module-info.java` 에 `module demo { exports shapes; exports other; }` 를 **한 줄 추가**하면 결과가 바뀌는가?
- 바뀐다면 `javap -v` 의 `PermittedSubclasses` 에는 무엇이 찍히는가?

### 4. `default` 없는 `switch` 와 하위 타입 추가 (예측)

```java
sealed interface Shape permits Circle, Square, Triangle { }
record Circle(double r) implements Shape { }
record Square(double s) implements Shape { }
record Triangle(double b, double h) implements Shape { }

static double area(Shape s) {
    return switch (s) {
        case Circle c -> Math.PI * c.r() * c.r();
        case Square q -> q.s() * q.s();
    };
}
```

- 이것은 컴파일되는가? 안 된다면 무엇이 출력되는가?
- `default -> 0` 을 추가하면 통과하는가?
- **통과하는데도 그러지 않는 것이 나은 이유**를 한 문장으로 말하면 무엇인가?
- 이 에러는 앞의 1~3번 에러들과 성격이 어떻게 다른가?

### 5. 분리 컴파일 — 이미 컴파일된 `switch` 는 (예측)

```text
1차:  Shape.java    public sealed interface Shape permits Circle, Square { }
      Ex.java       switch (s) { case Circle c -> "원"; case Square q -> "정사각형"; }   // default 없음
      -> javac Shape.java Circle.java Square.java Ex.java   (성공)

2차:  Shape.java 를 permits Circle, Square, Triangle 로 고치고 Triangle.java 를 추가
      -> javac -cp out -d out Shape.java Triangle.java      (Ex.java 는 다시 컴파일하지 않는다)
```

- 2차 컴파일은 성공하는가?
- 고친 뒤 `java Ex` 로 `new Circle(1)` 을 `switch` 에 넣으면 무엇이 나오는가?
- `Triangle` 인스턴스를 넣으면 무엇이 나오는가 — 예외라면 **정확한 클래스 이름**은 무엇인가?
- javac 가 이것을 컴파일 시점에 막아 주지 못하는 이유는 무엇인가?

### 6. `non-sealed` 갈래에서 완결성은 어디까지 가나 (예측)

```java
sealed interface Shape permits Circle, Poly { }
record Circle(double r) implements Shape { }
static non-sealed class Poly implements Shape { }
static class Tri extends Poly { }

static String name(Shape s) {
    return switch (s) {
        case Circle c -> "원";
        case Tri t    -> "삼각형";
    };
}
```

- 이 `switch` 는 컴파일되는가? 안 된다면 무엇이 출력되는가?
- `case Tri t` 를 `case Poly p` 로 고치면 어떻게 되는가 — `new Tri()` 를 넣으면 어느 가지로 가는가?
- `Tri` 에는 아무 수식어도 안 붙었는데 왜 에러가 나지 않는가?
- `Poly` 를 `non-sealed` 로 둔 대가를 한 문장으로 말하면 무엇인가?

### 7. `permits` 를 생략하면 명단의 범위는 어디까지인가 (경계)

- `sealed interface Node { }` 처럼 `permits` 를 생략하면 명단은 어떻게 정해지는가?
- 그 범위는 **파일**인가 **패키지**인가?
- 하위 타입을 같은 패키지의 **다른 파일**로 옮기면 무슨 일이 일어나는가 — 에러는 몇 개 나는가?
- 하위 타입이 하나도 없는 `sealed` 타입은 선언할 수 있는가?

### 8. 명단은 어디에 남는가 (왜)

- `permits` 는 컴파일 후에도 남는가, 컴파일러가 확인만 하고 버리는가?
- 남는다면 그것을 어떤 도구로 볼 수 있는가 — `javap -p` 로 보이는가?
- `sealed` 를 나타내는 **접근 플래그**는 무엇인가?
- `non-sealed` 클래스의 클래스 파일에는 `non-sealed` 의 흔적이 남는가?

### 9. 리플렉션으로 물으면 무엇이 돌아오나 (경계)

```java
record Circle(double r) implements Shape { }   // Shape 는 sealed
System.out.println(Circle.class.isSealed());
System.out.println(java.util.Arrays.toString(Circle.class.getPermittedSubclasses()));
System.out.println(java.util.Arrays.toString(String.class.getPermittedSubclasses()));
```

- 이 세 줄은 각각 무엇을 출력하는가?
- `sealed` 가 아닌 타입에 `getPermittedSubclasses()` 를 부르면 **빈 배열인가 `null` 인가**?
- 두 메서드는 각각 어느 Java 버전부터인가 — 그 근거는 무엇인가?
- `Cat` 이 `non-sealed` 이고 `Animal` 이 `sealed` 일 때 `Animal.class.isSealed()` 는 무엇인가?

### 10. 버전 — 이 주제는 몇부터인가 (경계)

- `sealed` · `permits` · `non-sealed` 는 어느 버전에서 정식이 되었는가?
- 같은 프로그램을 `javac --release 16` 으로 컴파일하면 무엇이 출력되는가?
- `--release 17` 로 올리면 전부 통과하는가 — 안 된다면 **이번에는 무엇이 막히는가**?
- 이 주제에서 "sealed 는 N부터"라고 외울 때 **같이 외워야 할 다른 숫자**는 무엇이며 왜인가?

### 11. 익명 클래스와 람다는 왜 막히나 (경계)

```java
// (a)
sealed interface Shape permits Circle { }
record Circle(double r) implements Shape { }
Shape s = new Shape() { };

// (b)
sealed interface Op permits Add { int apply(int x); }
record Add(int n) implements Op { public int apply(int x) { return x + n; } }
Op o = x -> x + 1;
```

- (a)와 (b)는 각각 어떤 에러를 내는가?
- (b)의 `Op` 는 추상 메서드가 **정확히 하나**인데 왜 람다를 못 받는가?
- (b)의 에러 메시지에 `sealed` 라는 낱말이 나오는가?
- 이 제약이 테스트 코드 작성 방식에 어떤 영향을 주는가?

### 12. 무엇을 골라야 하나 — `enum` · `record` · Visitor (연결)

- 선택지마다 **들고 다닐 데이터의 모양이 다르면** `enum` 과 `sealed` 중 무엇을 쓰는가?
- `sealed` + `record` 조합이 만드는 것을 한 낱말로 무엇이라 부르는가?
- Visitor 패턴을 쓰려던 자리에 `sealed` 를 쓰면 "새 연산 추가"와 "새 타입 추가" 중 무엇이 싸지고 무엇이 비싸지는가?
- 라이브러리의 공개 인터페이스에 `sealed` 를 붙이면 안 되는 경우는 어떤 경우인가?
- `enum` 이 `sealed` 인터페이스를 구현할 수 있는가 — 그때 `enum` 쪽 `isSealed()` 는 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
