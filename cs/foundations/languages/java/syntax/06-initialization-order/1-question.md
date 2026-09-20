# java/syntax/06 — 클래스 멤버와 초기화 순서: static/인스턴스 초기화 블록 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력 순서를 맞힐 수 있는지**를 묻는다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 이 프로그램의 출력 순서를 예측하라 (예측)

```java
class Parent {
    static String sField = log("Parent static field");
    static { log("Parent static block"); }
    String iField = log("Parent instance field");
    { log("Parent instance block"); }
    Parent() { log("Parent constructor body"); }
    static String log(String s) { System.out.println(s); return s; }
}
class Child extends Parent {
    static String sField = log("Child static field");
    static { log("Child static block"); }
    String iField = log("Child instance field");
    { log("Child instance block"); }
    Child() { log("Child constructor body"); }
}
// main: new Child(); new Child();
```

- 첫 번째 `new Child()` 는 몇 줄을 출력하며 그 순서는 무엇인가?
- 두 번째 `new Child()` 는 몇 줄을 출력하며 무엇이 빠지는가?
- 빠진 줄들은 왜 빠졌는가?

### 2. 필드와 블록의 상대 순서 (경계)

```java
class X {
    { System.out.println("블록"); }
    int a = init("필드");
    static int init(String s) { System.out.println(s); return 0; }
}
```

- "블록"과 "필드" 중 무엇이 먼저 출력되는가?
- "필드 초기화식이 먼저, 초기화 블록이 나중"이라는 기억은 맞는가?
- 이 순서를 정하는 것은 무엇인가?

### 3. 초기화 블록은 클래스 파일의 어디로 가는가 (왜)

```java
class Point {
    { System.out.println("블록"); }
    Point() { this(0, 0); System.out.println("Point()"); }
    Point(int x, int y) { System.out.println("Point(int,int)"); }
}
// new Point();
```

- 이 세 줄의 출력 순서는 무엇인가?
- "블록"은 몇 번 출력되는가?
- `javap -c` 로 두 생성자를 열면 초기화 블록의 코드는 어느 쪽에 들어 있는가?
- 그 규칙을 한 문장으로 말하면 무엇인가?

### 4. 부모 생성자가 자식 메서드를 부르면 (예측)

```java
class Base {
    Base() { System.out.println("Base ctor    : " + describe()); }
    String describe() { return "Base"; }
}
class Derived extends Base {
    private String name = "derived";
    Derived() { System.out.println("Derived ctor : " + describe()); }
    @Override String describe() { return "name=" + name; }
}
// new Derived();
```

- 두 줄의 출력은 각각 무엇인가?
- `Base` 생성자에서 불린 `describe()` 는 어느 클래스의 것인가?
- 그 결과가 `NullPointerException` 이 아닌 이유는 무엇인가?
- 이 설계를 안전하게 만들려면 무엇을 바꾸는가?

### 5. `final` 필드 둘의 결과가 갈린다 (예측)

```java
class D2 extends B2 {
    private final int constant = 10;
    private final int computed = compute();
    static int compute() { return 10; }
    @Override String show() { return "constant=" + constant + " computed=" + computed; }
}
// B2 의 생성자가 show() 를 부른다
```

- 출력되는 두 값은 각각 무엇인가?
- 둘 다 `final int` 인데 결과가 갈리는 이유는 무엇인가?
- `javap` 로 `show()` 를 열면 `getfield` 명령이 몇 개 보이는가?
- `= 10` 을 `= compute()` 로 바꾸는 리팩토링은 무엇을 바꾸는가?

### 6. `static` 블록은 언제 도는가 (예측)

```java
class Holder {
    static final int     CONST = 42;
    static final Integer BOXED = 42;
    static { System.out.println(">> Holder <clinit> 실행됨"); }
}
// (a) System.out.println(Holder.CONST);
// (b) Holder[] arr = new Holder[3];
// (c) System.out.println(Holder.BOXED);
```

- (a)(b)(c) 중 어디에서 `>> Holder <clinit> 실행됨` 이 출력되는가?
- `CONST` 와 `BOXED` 가 갈리는 이유는 무엇인가?
- 배열을 만드는 것이 왜 클래스 초기화를 일으키지 않는가?
- JLS 가 정한 "클래스 초기화를 일으키는 네 가지"는 무엇인가?

### 7. 전방 참조 (경계)

```java
class Counter {
    static { count = 5; }
    static int count = 10;
}
// System.out.println(Counter.count);
```

- 출력은 무엇인가?
- 이 코드는 컴파일되는가?
- `static { System.out.println(count); }` 로 바꾸면 무슨 일이 생기는가?
- 쓰기는 되고 읽기는 안 되는 비대칭이 만드는 위험은 무엇인가?

### 8. 초기화가 순환하면 (예측)

```java
class A { static int aVal = B.bVal + 1; }
class B { static int bVal = A.aVal + 1; }
// System.out.println(A.aVal + " / " + B.bVal);
```

- 데드락이 나는가, 예외가 나는가, 값이 나오는가?
- 값이 나온다면 `A.aVal` 과 `B.bVal` 은 각각 무엇인가?
- `B.bVal` 을 먼저 읽으면 결과가 달라지는가?

### 9. 어디에 무엇을 쓰나 (연결)

- 생성자가 셋인데 공통으로 할 초기화가 있다면 어디에 쓰는가, 그 대안은 무엇인가?
- `static` 블록에 무거운 파일 읽기를 넣으면 무엇이 문제인가?
- 지연 싱글턴을 락 없이 안전하게 만드는 관용구는 이 주제의 어느 규칙에 기대는가?
- 이 주제가 다루지 않는 것(클래스 로딩·링킹)은 어느 문서가 정본인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
