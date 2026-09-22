# java/syntax/11 — 인터페이스: `default`/`static`/`private` 메서드와 충돌 해소 (8+) — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [JLS SE 21 §9.4 Method Declarations](https://docs.oracle.com/javase/specs/jls/se21/html/jls-9.html) · [§9.4.1 Inheriting Methods with Override-Equivalent Signatures](https://docs.oracle.com/javase/specs/jls/se21/html/jls-9.html) · [§8.4.8 Inheritance, Overriding, and Hiding](https://docs.oracle.com/javase/specs/jls/se21/html/jls-8.html) · [§9.3 Field (Constant) Declarations](https://docs.oracle.com/javase/specs/jls/se21/html/jls-9.html)
> **실행 검증** — 이 문서의 모든 출력·에러 메시지는 Temurin **JDK 21.0.5** 에서 실제로 돌려 얻은 것이다.\
> 정상 실행되는 프로그램은 **17.0.13 · 21.0.5 · 25.0.1** 셋에서 다 돌려 **출력이 한 글자도 다르지 않음**을 확인했다.\
> 바이트코드와 멤버 목록은 `javap -c -p` · `javap -p` 출력을 그대로 옮겼다.
> **버전** — `default`·`static` 메서드는 **Java 8**, `private`(및 `private static`) 메서드는 **Java 9** 부터.\
> 그 이전 릴리스로 컴파일하면 거부된다(아래 「구현 세부사항 대 언어 보장」).
> **범위** — 인터페이스가 **왜 Java 8 에서 바뀌었나**(람다·스트림을 넣으려는 동기)는\
> [`../../../../../../history/java/java-8.md`](../../../../../../history/java/java-8.md) 가 정본이다. 여기는 **그래서 무엇을 쓰고 무엇이 막히나**만 다룬다.
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**인터페이스는 계약서인데, Java 8 부터 그 계약서에 "기본 조항"이 들어갈 수 있게 됐다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 계약서 | 인터페이스 |
| 반드시 채워야 하는 빈칸 | `abstract` 메서드 |
| 안 고치면 이대로 적용되는 **기본 조항** | `default` 메서드 |
| 계약서에 딸린 **부속 서식**(계약과 무관하게 쓰는 양식) | `static` 메서드 |
| 기본 조항들이 공유하는 **내부 계산식** | `private` 메서드 (9+) |
| 계약서 두 장에 **같은 조항이 다르게** 적혀 있다 | `default` 다중 상속 충돌 |
| 계약서보다 **취업규칙**(회사 규정)이 우선 | 클래스가 인터페이스를 이긴다 |

- 기본 조항이 생기기 전에는, 계약서에 조항 하나를 **추가하면 기존 계약자가 전부 위반 상태**가 됐다.\
  `Collection` 에 `forEach` 를 넣는 순간 세상의 모든 구현체가 깨졌다는 뜻이다.
- `default` 는 그것을 푼다 — **"안 고치면 이 내용으로 간다"**.
- 그런데 계약서를 **두 장** 상속하면 같은 조항이 둘일 수 있다.\
  Java 는 임의로 고르지 않고 **계약자에게 직접 쓰라고 시킨다.**

```text
default 메서드가 푼 문제 (전/후 대비)

  Java 7 까지                          Java 8 부터
  +----------------------------+      +----------------------------+
  | interface Iterable {       |      | interface Iterable {       |
  |   Iterator iterator();     |      |   Iterator iterator();     |
  | }                          |      |   default void forEach(..) |
  |                            |      |     { ... }                |
  | forEach 를 추가하면         |      | }                          |
  | 모든 구현체가 컴파일 에러   |      | 구현체는 아무것도 안 해도 된다|
  +----------------------------+      +----------------------------+
    -> 추가할 수 없다                    -> 추가할 수 있다
```

**똑같은 구조로** Java 가 이렇게 동작한다: 실제로 `java.lang.Iterable` 이 그 모양이다.

```text
javap -p java.lang.Iterable  (JDK 21.0.5) — 출력 그대로

public interface java.lang.Iterable<T> {
  public abstract java.util.Iterator<T> iterator();
  public default void forEach(java.util.function.Consumer<? super T>);
  public default java.util.Spliterator<T> spliterator();
}
```

실무에서 이게 물리는 자리는 **인터페이스 둘을 함께 구현할 때**다.\
각자 `default` 로 같은 이름을 갖고 있으면 컴파일이 멈추고, 내가 직접 골라 줘야 한다.

> **`default` 메서드** — 인터페이스가 **본문까지 제공하는** 인스턴스 메서드(Java 8+).\
> 예: `List.sort(Comparator)` 는 `default` 라, 구현체가 안 만들어도 `list.sort(...)` 가 된다.

> **다중 상속 충돌(diamond problem)** — 여러 상위 타입에서 **같은 시그니처의 구현**이 내려오는 것.\
> 예: `A.who()` 와 `B.who()` 가 둘 다 `default` 인데 한 클래스가 둘을 구현하면 어느 쪽인지 정할 수 없다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. 인터페이스에 본문이 생기면서 **다중 상속 충돌**이 따라왔다 — Java 는 그것을 어떤 순서로 푸는가.
2. `default`·`static`·`private` 은 각각 **누구를 위한 것**인가, 그리고 **상속되는가**.
3. 인터페이스의 **상수**는 왜 함정인가.

## 동작 방식

### (1) 네 종류가 한 인터페이스에 들어간다

**언제 쓰나** — 인터페이스를 설계할 때 무엇을 어디에 둘지 정할 때.

```java
interface Greeter {
    String name();                                        // 암묵적 public abstract
    default String greet() { return prefix() + name(); }  // default
    static Greeter of(String n) { return () -> n; }       // static
    private String prefix() { return "안녕, "; }           // private (9+)
}
class Loud implements Greeter {
    public String name() { return "자바"; }
    @Override public String greet() { return "!!! " + Greeter.super.greet() + " !!!"; }
}
```

**실행 결과** (`Ex.java`, JDK 21.0.5 — 17·25 동일)

```text
g1.greet() = 안녕, 람다
g2.greet() = !!! 안녕, 자바 !!!
```

```text
javap -c -p Greeter — 출력 그대로 (선언하지 않은 제어자가 붙어 있다)

interface Greeter {
  public abstract java.lang.String name();

  public default java.lang.String greet();
    Code:
       0: aload_0
       1: invokeinterface #1,  1            // InterfaceMethod prefix:()Ljava/lang/String;
       6: aload_0
       7: invokeinterface #7,  1            // InterfaceMethod name:()Ljava/lang/String;
      12: invokedynamic #10,  0             // InvokeDynamic #0:makeConcatWithConstants:(...)
      17: areturn

  public static Greeter of(java.lang.String);
    Code:
       0: aload_0
       1: invokedynamic #14,  0             // InvokeDynamic #1:name:(Ljava/lang/String;)LGreeter;
       6: areturn

  private java.lang.String prefix();
    Code:
       0: ldc           #17                 // String 안녕,
       2: areturn

  private static java.lang.String lambda$of$0(java.lang.String);
```

그림 해설 (한 단계씩):

- `String name();` 이라고만 썼는데 `javap` 에는 **`public abstract`** 가 붙어 있다 — 암묵적으로 붙는다.
- `greet()` 안의 호출은 **`invokeinterface`** 다. 인터페이스 타입에 대한 호출이라 명령이 다르다.
- `of` 는 **`static`** 이라 인터페이스 이름으로만 부른다.
- `prefix()` 는 **`private`** — 바깥에서 안 보이고, `default` 메서드들의 공통부를 모으는 자리다.
- 람다 `() -> n` 은 `invokedynamic` 과 **합성 메서드 `lambda$of$0`** 로 컴파일된다.

비용 — `invokeinterface` 는 `invokevirtual` 보다 탐색이 한 겹 더 있을 수 있다.\
JIT 최적화는 [`../../언어-특성/README.md`](../../언어-특성/README.md) 의 영역이다.

### (2) `X.super.m()` — 어느 계약서의 조항인지 지목한다

**언제 쓰나** — 인터페이스가 준 기본 구현을 재정의하면서 그 안에서 다시 쓸 때.

`Loud.greet()` 의 바이트코드다.

```text
javap -c -p Loud — 출력 그대로

  public java.lang.String greet();
    Code:
       0: aload_0
       1: invokespecial #9                  // InterfaceMethod Greeter.greet:()Ljava/lang/String;
       4: ...
```

그림 해설 (한 단계씩):

- `Greeter.super.greet()` 는 **`invokespecial`** 이다 — 09 편의 `super.m()` 과 같은 명령이다.
- 다른 점은 대상이 **`InterfaceMethod`** 라는 것이다.
- 클래스는 상위 클래스가 하나라 `super.` 로 충분하지만, 인터페이스는 여럿이라 **이름을 앞에 붙인다.**
- `Greeter.super.greet()` 라고 쓰려면 `Loud` 가 **`Greeter` 를 직접 구현**해야 한다.\
  할아버지 인터페이스는 지목할 수 없다.

비용 — 정적 바인딩이라 `invokeinterface` 보다 싸다.

### (3) 충돌 해소 — 세 규칙이 순서대로 적용된다

**언제 쓰나** — 인터페이스를 둘 이상 구현할 때.

```java
interface A  { default String who() { return "A"; } }
interface B  { default String who() { return "B"; } }
interface B2 extends B { default String who() { return "B2(가장 구체적)"; } }

class Resolved implements A, B {                 // 충돌 -> 직접 재정의로 해소
    @Override public String who() { return A.super.who() + "+" + B.super.who(); }
}
class Specific implements B, B2 { }              // B2 가 B 를 이긴다 — 재정의 불필요

class Base { public String who() { return "Base(클래스)"; } }
class ClassWins extends Base implements A { }    // 클래스가 인터페이스를 이긴다
```

**실행 결과** (`Ex.java`, JDK 21.0.5 — 17·25 동일)

```text
Resolved  : A+B
Specific  : B2(가장 구체적)
ClassWins : Base(클래스)
```

```text
세 규칙의 적용 순서

  1) 클래스가 인터페이스를 이긴다
       Base.who() 가 있으면 A.who() 는 보이지도 않는다
              |
              v  (클래스 쪽에 없으면)
  2) 더 구체적인 인터페이스가 이긴다
       B2 extends B 이면 B2.who() 가 B.who() 를 덮는다
              |
              v  (우열이 없으면)
  3) 컴파일 에러 — 내가 직접 재정의해야 한다
       class C implements A, B { }   -> inherits unrelated defaults
```

그림 해설 (한 단계씩):

- **1) 클래스가 이긴다** — `ClassWins` 는 `who()` 를 **아예 갖지 않는다.**

  ```text
  javap -p ClassWins — 출력 그대로

  class ClassWins extends Base implements A {
    ClassWins();
  }
  ```

  브리지도 합성 메서드도 없다. 그냥 `Base` 것을 물려받을 뿐이다.
- **2) 더 구체적인 인터페이스가 이긴다** — `Specific` 도 `who()` 를 갖지 않는다.

  ```text
  javap -p Specific — 출력 그대로

  class Specific implements B,B2 {
    Specific();
  }
  ```

  `B2 extends B` 라 우열이 있으므로 컴파일러가 알아서 정한다.
- **3) 우열이 없으면 멈춘다** — `A` 와 `B` 는 무관한 인터페이스다.

  ```text
  Ex.java:3: error: types A and B are incompatible;
  class C implements A, B { }                      // 둘 다 default 를 준다
  ^
    class C inherits unrelated defaults for who() from types A and B
  1 error
  ```

- 해소는 **내가 재정의하는 것**뿐이다. 그 안에서 `A.super.who()` 로 골라 쓸 수 있다.
- ★ **Java 는 임의로 고르지 않는다.** C++ 의 가상 상속이나 파이썬의 MRO 처럼 **순서로 결정하지 않는다.**

비용 — 없다. 전부 컴파일 타임 결정이다.

### (4) `default` 와 `abstract` 가 만나면 `abstract` 가 이긴다

**언제 쓰나** — 한 인터페이스는 구현을 주는데 다른 인터페이스는 안 줄 때.

```java
interface HasDefault { default String who() { return "default"; } }
interface IsAbstract { String who(); }
class C implements HasDefault, IsAbstract { }
```

```text
Ex.java:3: error: C is not abstract and does not override abstract method who() in IsAbstract
class C implements HasDefault, IsAbstract { }     // 한쪽은 default, 한쪽은 abstract
^
1 error
```

그림 해설 (한 단계씩):

- **기본 구현이 있는데도 에러다.** "빈칸이 남아 있다"고 말한다.
- 규칙: 상속된 시그니처 중 **하나라도 `abstract` 면** 그 클래스는 그것을 구현해야 한다.
- 설계 함의: 인터페이스에 같은 이름을 **`abstract` 로 재선언**하면 **`default` 를 강제로 무효화**할 수 있다.\
  하위 인터페이스에서 "이건 반드시 직접 구현하라"고 못박는 수단이다.

비용 — 없다.

## 문법 — 형태와 규칙

직접 쓴 최소 예제다.

### 인터페이스가 가질 수 있는 멤버

```java
interface Logger {
    int LEVEL = 3;                                            // public static final (암묵)
    void log(String m);                                       // public abstract (암묵)
    default void info(String m)  { write("INFO", m); }        // 8+
    default void error(String m) { write("ERROR", m); }       // 8+
    private void write(String level, String m) { log("[" + level + "] " + m); }   // 9+
    static Logger stdout() { return System.out::println; }    // 8+
}
```

**실행 결과** (`Ex.java`, JDK 21.0.5 — 17·25 동일)

```text
[INFO] 시작
[ERROR] 실패
```

| 멤버 | 암묵 제어자 | 상속되나 | 버전 |
|---|---|---|---|
| 상수 | `public static final` | 이름으로 물려받는다 | 1.0 |
| 추상 메서드 | `public abstract` | 그렇다 | 1.0 |
| `default` 메서드 | `public` | **그렇다** | 8 |
| `static` 메서드 | — | **아니다** | 8 |
| `private` 메서드 | — | 아니다(밖에서 안 보인다) | 9 |
| `private static` 메서드 | — | 아니다 | 9 |

### 못 하는 것

- **인스턴스 필드를 둘 수 없다.** 상수뿐이다(`static final`).
- **생성자가 없다.**
- **`protected` 멤버를 둘 수 없다**([10 편](../10-access-modifiers/)).
- **`Object` 의 `public` 메서드를 `default` 로 줄 수 없다.**

## 어디서 틀리나

### 1. `static` 메서드가 상속된다고 믿는다

```java
interface Greeter { static Greeter of() { return null; } }
class Impl implements Greeter { }
// Greeter.of();  Impl.of();
```

```text
Ex.java:6: error: cannot find symbol
        Impl.of();         // 구현 클래스 이름으로는?
            ^
  symbol:   method of()
  location: class Impl
1 error
```

- 클래스의 `static` 메서드는 **상속되고 숨김도 된다**(09 편). 인터페이스의 `static` 은 **상속되지 않는다.**
- 이유: 상속되면 여러 인터페이스에서 같은 이름의 `static` 이 내려올 때 또 충돌이 난다.\
  그것을 아예 안 만들기로 한 것이다.
- 그래서 **`Greeter.of()` 라고 인터페이스 이름으로만** 부른다 — 오히려 읽기에 명확하다.

### 2. `default` 로 `toString`·`equals`·`hashCode` 를 주려 한다

```java
interface Bad {
    default String toString() { return "인터페이스가 준 toString"; }
    default boolean equals(Object o) { return true; }
    default int hashCode() { return 0; }
}
```

```text
Ex.java:2: error: default method toString in interface Bad overrides a member of java.lang.Object
    default String toString() { return "인터페이스가 준 toString"; }
                   ^
Ex.java:3: error: default method equals in interface Bad overrides a member of java.lang.Object
    default boolean equals(Object o) { return true; }
                    ^
Ex.java:4: error: default method hashCode in interface Bad overrides a member of java.lang.Object
    default int hashCode() { return 0; }
                ^
3 errors
```

- 세 개 다 막힌다. 이유는 **「클래스가 인터페이스를 이긴다」** 규칙이다.\
  모든 클래스가 `Object` 를 상속하므로, 인터페이스의 `default` 는 **절대 불리지 않는다.**\
  불릴 수 없는 코드를 쓰게 두느니 컴파일 에러로 막는 것이다.
- 그래서 **"인터페이스로 `toString` 을 공짜로 주기"는 Java 에서 불가능**하다.\
  추상 클래스를 쓰거나 각 구현체가 직접 써야 한다.
- 계약 자체는 [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) 가 정본이다.

### 3. 같은 이름의 상수를 둘에서 물려받는다

```java
interface X { int LIMIT = 10; }
interface Y { int LIMIT = 20; }
class Both implements X, Y {
    int use() { return LIMIT; }     // 어느 LIMIT?
}
```

```text
Ex.java:4: error: reference to LIMIT is ambiguous
    int use() { return LIMIT; }     // 어느 LIMIT?
                       ^
  both variable LIMIT in X and variable LIMIT in Y match
1 error
```

- `default` 메서드와 달리 **상수는 「더 구체적인 것이 이긴다」가 없다.** 그냥 모호하다.
- 고치려면 `X.LIMIT` 처럼 **이름을 붙인다.**
- 상수를 인터페이스에 모으는 관용구(constant interface)가 위험한 이유 중 하나다.

### 4. 인터페이스 상수가 "불변"이라고 믿는다

```java
interface Limits {
    int MAX = 10;                       // public static final 이 암묵적으로 붙는다
    int[] TABLE = {1, 2, 3};            // 참조는 final 이지만 내용은 아니다
}
class Impl implements Limits { }
```

**실행 결과** (`Ex.java`, JDK 21.0.5 — 17·25 동일)

```text
Limits.MAX = 10
Impl.MAX   = 10
TABLE      = [99, 2, 3]
```

```text
javap -p -c Limits — 출력 그대로

interface Limits {
  public static final int MAX;

  public static final int[] TABLE;

  static {};
    Code:
       0: iconst_3
       1: newarray       int
       ...
      15: putstatic     #1                  // Field TABLE:[I
      18: return
}
```

- **`Limits.TABLE[0] = 99` 가 아무 저항 없이 통과한다.** `final` 은 **참조**에 걸린 것이지 내용이 아니다.
- `Impl.MAX` 로도 읽힌다 — 구현 클래스 이름으로 상수가 노출된다. 이것이 constant interface 의 실질적 해악이다.
- 인터페이스에도 **`<clinit>`(`static {}`)이 있다.** 06 편의 클래스 초기화가 그대로 적용된다.
- `MAX` 는 **컴파일 타임 상수**라 `putstatic` 이 없다 — 호출부에 `10` 이 박힌다([06 편](../06-initialization-order/)).
- 방어: 상수는 **`enum` 이나 `final class` 의 `static final`** 에 둔다. 인터페이스에 두지 않는다.

### 5. `@FunctionalInterface` 가 세는 것을 잘못 안다

```java
@FunctionalInterface
interface F {
    String apply(String s);
    default String twice(String s) { return apply(apply(s)); }   // default 는 세지 않는다
    static F identity() { return s -> s; }                        // static 도 세지 않는다
    boolean equals(Object o);                                     // Object 의 public 메서드도 안 센다
}
@FunctionalInterface
interface G { String a(); String b(); }                           // 추상이 둘
```

```text
Ex.java:8: error: Unexpected @FunctionalInterface annotation
@FunctionalInterface
^
  G is not a functional interface
    multiple non-overriding abstract methods found in interface G
1 error
```

- **`F` 는 통과한다.** 추상 메서드가 `apply` 하나뿐이기 때문이다.
- `default`·`static`·**`Object` 의 `public` 메서드 재선언**은 세지 않는다.\
  `Comparator` 가 `equals(Object)` 를 선언해 두고도 함수형 인터페이스인 것이 그 예다.
- `G` 는 추상이 둘이라 거부된다.

## 구현 세부사항 대 언어 보장

| 항목 | 누가 보장하나 |
|---|---|
| 충돌 해소 세 규칙(클래스 > 구체적 인터페이스 > 에러) | **언어 보장** — JLS §9.4.1, §8.4.8 |
| `static` 인터페이스 메서드가 상속되지 않는 것 | **언어 보장** — JLS §8.4.8 |
| `Object` 메서드를 `default` 로 못 주는 것 | **언어 보장** — JLS §9.4.1.2 |
| 인터페이스 멤버의 암묵 제어자(`public abstract` / `public static final`) | **언어 보장** — JLS §9.3, §9.4 |
| `invokeinterface` 와 `invokevirtual` 중 어느 것이 쓰이는지 | **구현 세부** — 수신자의 선언 타입에 따른 javac 선택 |
| 람다가 `invokedynamic` + `lambda$of$0` 로 컴파일되는 것 | **구현 세부** — [**29번 주제**](../29-lambda-expressions/) 영역 |

★ **버전 게이트는 실측으로 확인했다.**

```text
$ javac --release 8 Ex.java        (interface I { private void helper() { } ... })
Ex.java:1: error: private interface methods are not supported in -source 8
interface I { private void helper() { } private static void s() { } }
                                 ^
  (use -source 9 or higher to enable private interface methods)
1 error
```

- `private` 인터페이스 메서드는 **Java 9** 부터다. 8 로는 거부된다.
- `default`·`static` 은 8 부터인데, **JDK 21 의 `javac` 는 `--release 7` 자체를 받지 않는다.**

  ```text
  $ javac --release 7 Ex.java
  error: release version 7 not supported
  ```

  그래서 "7 에서는 `default` 가 거부된다"는 **이 머신에서 재현할 수 없다** — 확인한 것은 9 게이트뿐이다.

## 언제 쓰고 언제 안 쓰나

| 쓸 것 | 안 쓸 것 |
|---|---|
| 기존 인터페이스에 메서드 추가 -> `default` | 상태(필드)가 필요한 기본 구현 — 인터페이스에는 인스턴스 필드가 없다 |
| 인터페이스와 짝을 이루는 팩토리 -> `static` | 구현 클래스 이름으로 부를 수 있을 거라 기대하기 |
| `default` 둘의 공통부 -> `private` (9+) | `protected` 로 공통부 빼기(인터페이스에 불가) |
| 상수 -> `enum` 또는 `final class` | **constant interface** — 구현 클래스에 상수가 새어 나간다 |

판단 규칙 세 줄.

- **`default` 는 "진화의 수단"이지 "추상 클래스 대용"이 아니다.** 상태가 필요하면 추상 클래스다.
- **인터페이스를 둘 이상 구현하면 이름 충돌을 먼저 확인한다.** 상수 이름까지 포함해서.
- **`Object` 의 세 메서드는 인터페이스로 줄 수 없다.** 설계에서 미리 빼 둔다.

## 핵심 문장

- `default` 메서드는 **이미 배포된 인터페이스에 메서드를 추가**할 수 있게 하려고 들어왔다(Java 8).
- 충돌 해소는 **① 클래스가 인터페이스를 이긴다 ② 더 구체적인 인터페이스가 이긴다 ③ 그 외에는 컴파일 에러**.
- 에러가 났을 때 해소는 **직접 재정의**뿐이고, 그 안에서 **`X.super.m()`** 으로 골라 쓴다.
- `static` 인터페이스 메서드는 **상속되지 않는다.** 인터페이스 이름으로만 부른다.
- 인터페이스 상수는 `public static final` 이고, **`final` 은 참조에만 걸린다** — 배열 내용은 바뀐다.

## 관련 자료

- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 11번)
- [`../09-inheritance-overriding/`](../09-inheritance-overriding/) — **오버라이딩 규칙이 정본**이다. 여기는 **그 규칙에 인터페이스가 끼었을 때의 충돌 해소**만 더한다
- [`../10-access-modifiers/`](../10-access-modifiers/) — **인터페이스 멤버의 암묵 `public` 과 `protected` 불가**가 그쪽 정본
- [`../06-initialization-order/`](../06-initialization-order/) — **인터페이스에도 `<clinit>` 이 있다.** 상수 접기와 초기화 시점은 그쪽이 정본
- [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) — **`equals`/`hashCode` 계약은 거기.** 여기는 **인터페이스로는 줄 수 없다**는 사실까지
- [`../../../../oop-basics/`](../../../../oop-basics/) — **추상 클래스와 다형성 개념은 거기**(§17 abc).\
  ★ 그쪽은 「추상 메서드로 구현을 강제한다」까지, 여기는 「**구현을 제공할 수도 있게 된 뒤 생긴 규칙들**」부터다.\
  다중 상속 충돌·`X.super`·`static` 미상속은 파이썬의 MRO 와 전혀 다른 해법이라 그 문서에 없다
- [`../../../../../../history/java/java-8.md`](../../../../../../history/java/java-8.md) — **왜 들어왔나는 거기**, 여기는 **무엇을 쓰고 무엇이 막히나**
- [`../../언어-특성/README.md`](../../언어-특성/README.md) — `invokeinterface` 의 JIT 최적화는 그쪽
- [**15번 주제**](../15-sealed-classes/)(`sealed`) · **29번 주제**(람다) · **31번 주제**(함수형 인터페이스)

## 용어 풀이

- **인터페이스(interface)** — 타입과 계약을 선언하는 참조 타입. 인스턴스 필드와 생성자가 없다.
- **`default` 메서드** — 본문을 가진 인터페이스 인스턴스 메서드(Java 8+). 구현체가 안 만들어도 된다.
- **`static` 인터페이스 메서드** — 인터페이스에 딸린 정적 메서드(Java 8+). **상속되지 않는다.**
- **`private` 인터페이스 메서드** — `default` 들의 공통부를 모으는 비공개 메서드(Java 9+).
- **다중 상속 충돌(diamond problem)** — 여러 상위 타입에서 같은 시그니처 구현이 내려오는 것.
- **`X.super.m()`** — 지목한 인터페이스 `X` 의 `default` 구현을 직접 부르는 문법. `X` 를 **직접 구현**해야 쓸 수 있다.
- **클래스가 인터페이스를 이긴다(class wins)** — 클래스 계층에 구현이 있으면 인터페이스의 `default` 는 고려되지 않는다.
- **constant interface** — 상수만 모아 둔 인터페이스를 구현해 상수를 끌어 쓰는 관용구. 안티패턴이다.
- **함수형 인터페이스** — 추상 메서드가 **정확히 하나**인 인터페이스. `default`·`static`·`Object` 메서드는 세지 않는다.
- **`invokeinterface`** — 인터페이스 타입 수신자에 대한 호출 명령.

## 더 들어가면

- **`default` 는 이진 호환이지만 의미 호환은 아니다.**\
  인터페이스에 `default` 를 추가하면 기존 구현체는 다시 컴파일되고 돌지만,\
  그 구현체에 **우연히 같은 이름의 메서드**가 이미 있으면 그쪽이 이긴다(클래스가 인터페이스를 이긴다).

  ```text
  실행 결과 (11/f/Ex.java, JDK 21.0.5)
  x.describe() = Old 가 원래 갖고 있던 메서드
  ```

  경고도 에러도 없다. **의도치 않은 재정의가 조용히 성립한다.**
- **`SequencedCollection`(Java 21)이 `default` 의 실물 사례다.**\
  `javap -p java.util.List` 에 `addFirst`·`getFirst`·`reversed` 가 전부 `public default` 로 들어 있다 —\
  기존 `List` 구현체를 하나도 안 고치고 새 API 를 얹은 것이다.
- **추상 클래스와의 선택 기준**은 **상태**다. 필드가 필요하면 추상 클래스, 동작만이면 인터페이스.\
  Java 8 이후에도 이 기준은 바뀌지 않았다.
- **인터페이스의 `private` 인스턴스 메서드는 `static` 메서드에서 부를 수 없다.**\
  `private static` 은 양쪽에서 다 부를 수 있다.

  ```text
  Ex.java:9: error: non-static method helper() cannot be referenced from a static context
      static String bad() { return helper(); }      // static 에서 private 인스턴스 메서드
                                   ^
  1 error
  ```
