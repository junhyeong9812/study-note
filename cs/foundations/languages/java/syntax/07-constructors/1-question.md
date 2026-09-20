# java/syntax/07 — 생성자: `this()`/`super()`·(25) 유연한 생성자 본문 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다. 특히 **"21 에서는? 25 에서는?"** 을 나눠 답하라.
> 선행: [06 클래스 멤버와 초기화 순서](../06-initialization-order/).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 위임 체인의 출력 순서를 예측하라 (예측)

```java
class Animal {
    String kind;
    Animal() {
        this("unknown");
        System.out.println("  Animal() 본문");
    }
    Animal(String kind) {
        System.out.println("  Animal(String) 본문: kind=" + kind);
        this.kind = kind;
    }
}
class Dog extends Animal {
    int age;
    Dog() { System.out.println("  Dog() 본문"); }
    Dog(int age) {
        super("dog");
        System.out.println("  Dog(int) 본문: age=" + age);
        this.age = age;
    }
}
// main: new Dog();  그 다음 new Dog(3);
```

- `new Dog()` 는 생성자를 몇 개 거치며, 출력은 무엇인가?
- `Dog()` 에는 `super()` 도 `this()` 도 없는데 왜 `Animal` 의 코드가 도는가?
- `new Dog(3)` 의 출력이 `new Dog()` 보다 짧은 이유는 무엇인가?

### 2. `javap` 로 `this()` 와 `super()` 를 구분하라 (예측)

```text
javap -c -p Animal 의 두 생성자에서 첫 invokespecial 의 대상은 각각 무엇인가?

  Animal();                          Animal(java.lang.String);
    0: aload_0                          0: aload_0
    1: ldc  "unknown"                   1: invokespecial ???
    3: invokespecial ???                4: ...
```

- 두 생성자 모두 같은 JVM 명령으로 시작한다 — 그 명령은 무엇인가?
- `this(...)` 와 `super()` 를 바이트코드에서 구분하는 단서는 무엇인가?
- `Animal(String)` 에는 `super()` 를 안 썼는데 왜 호출이 보이는가?

### 3. 왜 `this()`/`super()` 가 첫 문장이어야 했나 (왜)

- 이 규칙이 막으려는 사고는 무엇인가?
- 이 규칙이 실무에서 만든 불편은 무엇인가 — 구체적으로 어떤 코드를 못 쓰게 했나?
- Java 21 에서 "`super()` 에 넘길 인자를 먼저 검증"하려면 어떤 형태로 우회했나?

### 4. 부모에 무인자 생성자가 없다 (예측)

```java
class HasCtor { HasCtor(int x) { } }
class Sub extends HasCtor {
    Sub() { }
}
```

- 컴파일되는가? 안 된다면 에러 메시지는 무엇을 요구하는가?
- 에러가 가리키는 **줄과 열**은 어디인가, 그리고 그 자리에 무엇이 있는가?
- 라이브러리 저자가 여기서 배워야 할 하위 호환성 규칙은 무엇인가?

### 5. 같은 소스, 21 과 25 (예측)

```java
class Base { Base(int n) { System.out.println("  Base(" + n + ")"); } }
class Sub extends Base {
    private final int[] data;
    Sub(int[] src) {
        int[] copy = src.clone();
        if (copy.length == 0) throw new IllegalArgumentException("비었다");
        this.data = copy;
        super(copy.length);
        System.out.println("  Sub 본문: data.length=" + data.length);
    }
}
// main: new Sub(new int[]{5,2,8});  그 다음 new Sub(new int[0]) 을 try/catch
```

- JDK 21.0.5 에서 컴파일하면 무슨 일이 생기는가?
- JDK 25.0.1 에서는 무엇이 출력되는가?
- 빈 배열을 넘겼을 때 `Base` 생성자는 불리는가?

### 6. 25 의 프롤로그에서 되는 것과 안 되는 것 (경계)

- 프롤로그에서 **할 수 있는** 것 네 가지를 들어라.
- 프롤로그에서 **할 수 없는** 것 세 가지를 들어라.
- "쓰기는 되고 읽기는 안 된다"는 비대칭의 이유는 무엇인가?
- 그 규칙을 어겼을 때 나오는 컴파일 에러 문구는 무엇인가?

### 7. 06 편의 함정을 25 로 고치면 (예측)

```java
class Base {
    Base() { System.out.println("  Base 생성자가 본 값: " + describe()); }
    String describe() { return "Base"; }
}
class Fixed extends Base {
    private String name;
    Fixed(String n) {
        this.name = n;
        super();
        System.out.println("  Fixed 생성자가 본 값: " + describe());
    }
    @Override String describe() { return "name=" + name; }
}
// main: new Fixed("derived");
```

- 두 줄의 출력은 각각 무엇인가?
- 06 편에서 같은 구조가 무엇을 출력했는지 기억나는가 — 무엇이 달라졌나?
- `javap -c -p Fixed` 에서 `putfield` 와 `invokespecial` 중 무엇이 먼저 나오는가?
- 그런데도 "생성자에서 오버라이드 가능한 메서드를 부르지 마라"가 여전히 유효한 이유는 무엇인가?

### 8. 프롤로그 대입과 필드 초기화식을 같이 두면 (경계)

```java
class Sub extends Base {
    private int v = 100;
    Sub(int x) {
        this.v = x;
        super();
    }
}
```

- JDK 25 에서 이 코드는 컴파일되는가?
- 컴파일된다면 `v` 는 무엇이 되겠는가 — 그 판단의 근거는 06 편의 어느 규칙인가?
- javac 가 이 조합을 어떻게 처리하는가?

### 9. 유연한 생성자 본문은 JVM 을 바꿨나 (왜)

- `putfield` 가 `invokespecial` 앞에 오는 바이트코드가 **원래도** 유효했는가?
- 그렇다면 21 에서 막혔던 것은 누구였나?
- 25 로 컴파일한 클래스 파일을 21 JVM 이 못 읽는 이유는 무엇인가?

### 10. `this` 를 미리 쓰면 (경계)

```java
class Node {
    private final Node next;
    Node(Node next) { this.next = next; }
    Node() { this(this); }
}
// 그리고
class Loop {
    Loop()      { this(1); }
    Loop(int x) { this();  }
}
```

- 각각 어떤 에러가 나는가?
- `Loop` 의 문제는 런타임에 잡히는가 컴파일 타임에 잡히는가?
- `this(this)` 의 에러 문구가 25 의 프롤로그 규칙 위반과 같은 이유는 무엇인가?

### 11. 생성자를 하나도 안 쓰면 (예측)

```java
class NoCtor { }
```

- `javap -c -p NoCtor` 에는 무엇이 보이는가?
- 그 본문은 몇 줄인가?
- `class HasCtor { HasCtor(int x) { } }` 에는 왜 무인자 생성자가 없는가?

### 12. 정본 경계 (연결)

- "필드 초기화식과 초기화 블록이 어느 순서로 도는가"는 어느 문서가 정본인가?
- `this(...)` 로 위임하는 생성자에 초기화 블록이 복사되지 않는다는 사실은 어느 문서에서 나왔는가?
- 유연한 생성자 본문이 **왜** 들어왔는지(JEP 의 논쟁)는 어디를 보는가?
- `record` 의 컴팩트 생성자는 이 주제의 프롤로그와 같은 것인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
