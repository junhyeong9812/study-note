# java/syntax/11 — 인터페이스: `default`/`static`/`private` 메서드와 충돌 해소 (8+) — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 특히 **"컴파일되나, 된다면 무엇이 불리나"**.
> 선행: [09 상속과 오버라이딩](../09-inheritance-overriding/).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `default` 는 무엇을 풀려고 들어왔나 (왜)

- Java 7 까지 배포된 인터페이스에 메서드를 추가하면 무슨 일이 일어났는가?
- `default` 는 그것을 어떻게 푸는가?
- `java.lang.Iterable` 을 `javap -p` 로 열면 그 증거가 몇 줄 보이는가?
- Java 21 에서 같은 수법으로 `List` 에 추가된 메서드들은 무엇인가?

### 2. 네 종류가 한 인터페이스에 (예측)

```java
interface Greeter {
    String name();
    default String greet() { return prefix() + name(); }
    static Greeter of(String n) { return () -> n; }
    private String prefix() { return "안녕, "; }
}
class Loud implements Greeter {
    public String name() { return "자바"; }
    @Override public String greet() { return "!!! " + Greeter.super.greet() + " !!!"; }
}
// main: Greeter g1 = Greeter.of("람다");  Greeter g2 = new Loud();
```

- `g1.greet()` 와 `g2.greet()` 는 각각 무엇을 출력하는가?
- `javap -p Greeter` 에서 `String name();` 에 어떤 제어자가 붙어 있는가?
- `greet()` 안의 호출 명령은 무엇인가?
- `Greeter.super.greet()` 는 어떤 명령으로 컴파일되는가, 09 편의 무엇과 같은가?

### 3. 충돌 세 규칙 (예측)

```java
interface A  { default String who() { return "A"; } }
interface B  { default String who() { return "B"; } }
interface B2 extends B { default String who() { return "B2(가장 구체적)"; } }

class Resolved implements A, B { @Override public String who() { return A.super.who() + "+" + B.super.who(); } }
class Specific implements B, B2 { }
class Base { public String who() { return "Base(클래스)"; } }
class ClassWins extends Base implements A { }
```

- 세 클래스의 `who()` 는 각각 무엇을 돌려주는가?
- `javap -p ClassWins` 와 `javap -p Specific` 에는 `who()` 가 들어 있는가?
- `class C implements A, B { }` 는 어떻게 되는가, 에러 문구는 무엇인가?
- Java 가 「순서로 자동 결정」하지 않는 이유는 무엇인가?

### 4. `default` 와 `abstract` 가 만나면 (예측)

```java
interface HasDefault { default String who() { return "default"; } }
interface IsAbstract { String who(); }
class C implements HasDefault, IsAbstract { }
```

- 컴파일되는가? 기본 구현이 있는데도?
- 에러 문구는 무엇을 요구하는가?
- 이 규칙을 **설계 수단으로** 쓰면 무엇을 할 수 있는가?

### 5. `static` 인터페이스 메서드는 상속되나 (경계)

```java
interface Greeter { static Greeter of() { return null; } }
class Impl implements Greeter { }
// Greeter.of();  Impl.of();
```

- 둘 중 무엇이 컴파일되는가?
- 안 되는 쪽의 에러 문구는 무엇인가?
- 클래스의 `static` 메서드(09 편의 숨김)와 무엇이 다른가?
- 왜 이렇게 설계했겠는가?

### 6. `Object` 의 메서드를 `default` 로 (예측)

```java
interface Bad {
    default String toString() { return "인터페이스가 준 toString"; }
    default boolean equals(Object o) { return true; }
    default int hashCode() { return 0; }
}
```

- 에러가 몇 개 나는가?
- 에러 문구는 무엇인가?
- 왜 막는가 — 어느 규칙에서 따라 나오는가?
- 그래서 "인터페이스로 `toString` 을 공짜로 주기"는 가능한가?

### 7. 인터페이스 상수의 함정 (예측)

```java
interface Limits {
    int MAX = 10;
    int[] TABLE = {1, 2, 3};
}
class Impl implements Limits { }
// Limits.MAX / Impl.MAX / Limits.TABLE[0] = 99; 후 TABLE 출력
```

- 세 줄의 출력은 각각 무엇인가?
- `TABLE[0] = 99` 가 왜 막히지 않는가?
- `javap -p -c Limits` 에서 `MAX` 와 `TABLE` 중 `putstatic` 이 있는 것은 어느 쪽인가, 왜인가?
- 상수는 어디에 두는 것이 옳은가?

### 8. 같은 이름의 상수를 둘에서 (경계)

```java
interface X { int LIMIT = 10; }
interface Y { int LIMIT = 20; }
class Both implements X, Y { int use() { return LIMIT; } }
```

- 컴파일되는가? 에러 문구는 무엇인가?
- `default` 메서드의 「더 구체적인 것이 이긴다」가 상수에도 적용되는가?
- 고치려면 어떻게 쓰는가?

### 9. `@FunctionalInterface` 가 세는 것 (경계)

```java
@FunctionalInterface
interface F {
    String apply(String s);
    default String twice(String s) { return apply(apply(s)); }
    static F identity() { return s -> s; }
    boolean equals(Object o);
}
@FunctionalInterface
interface G { String a(); String b(); }
```

- `F` 는 통과하는가?
- 무엇을 세고 무엇을 안 세는가?
- `G` 의 에러 문구는 무엇인가?
- JDK 안에서 `equals(Object)` 를 선언한 함수형 인터페이스의 실물은 무엇인가?

### 10. `private` 인터페이스 메서드 (경계)

- 어느 버전부터인가? `--release 8` 로 컴파일하면 무슨 에러가 나는가?
- `private` 인스턴스 메서드를 `static` 메서드에서 부를 수 있는가?
- 무엇을 위해 쓰는가?

### 11. `default` 를 추가했는데 조용히 안 불린다 (예측)

```java
interface Api {
    void run();
    default String describe() { return "Api 가 준 기본 구현"; }   // 나중에 추가된 default
}
class Old implements Api {
    public void run() { }
    public String describe() { return "Old 가 원래 갖고 있던 메서드"; }   // 우연히 같은 이름
}
// main: Api x = new Old();  x.describe();
```

- 출력은 무엇인가?
- 경고나 에러가 있는가?
- 어느 규칙이 작동한 것인가?
- 라이브러리 저자가 `default` 를 추가할 때 조심해야 할 것은 무엇인가?

### 12. 정본 경계 (연결)

- `default` 가 **왜** 들어왔나(설계 논쟁)는 어디를 보는가?
- 오버라이딩 규칙 자체는 어느 주제가 정본인가?
- 인터페이스 멤버의 암묵 `public` 과 `protected` 불가는 어느 주제인가?
- `oop-basics` 의 추상 클래스(§17)와 이 주제는 어디서 갈리는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
