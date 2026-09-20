# java/syntax/07 — 생성자: `this()`/`super()`·(25) 유연한 생성자 본문 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [JLS SE 21 §8.8 Constructor Declarations](https://docs.oracle.com/javase/specs/jls/se21/html/jls-8.html) · [§8.8.7 Constructor Body](https://docs.oracle.com/javase/specs/jls/se21/html/jls-8.html) · [§12.5 Creation of New Class Instances](https://docs.oracle.com/javase/specs/jls/se21/html/jls-12.html) · [JEP 513: Flexible Constructor Bodies](https://openjdk.org/jeps/513)
> **실행 검증** — 이 문서의 모든 출력과 에러 메시지는 Temurin **JDK 21.0.5** 와 **25.0.1** 에서 실제로 돌려 얻은 것이다.\
> 21 에서 되는 것은 **17.0.13 · 21.0.5 · 25.0.1** 셋에서 다 돌려 **출력이 한 글자도 다르지 않음**을 확인했다.\
> **유연한 생성자 본문은 25.0.1 에서만** 컴파일된다 — 21·17 의 에러 메시지도 같이 실었다.\
> 바이트코드는 `javap -c -p` 출력을 그대로 옮겼다.
> **버전** — `this()`/`super()` 규칙 자체는 Java 1.0 이래 같다.\
> **유연한 생성자 본문은 Java 25**(JEP 513) 부터다 — 22·23·24 에서 프리뷰였다.
> **범위** — 필드·초기화 블록이 **어느 순서로 도는가**는 [`../06-initialization-order/`](../06-initialization-order/) 가 정본이다.\
> 여기는 **`super()` 라는 한 줄의 앞뒤에 무엇을 쓸 수 있나**만 다룬다.
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**생성자는 건물을 짓는 것이고, `super()` 는 "기초 공사 끝"이라고 찍는 도장이다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 건물 한 채 | 객체 하나 |
| 기초 공사 (아래층) | 상위 클래스 부분의 생성 |
| 기초 공사 끝 도장 | `super(...)` 호출 |
| 같은 회사의 다른 시공 계획서로 넘기기 | `this(...)` 호출 |
| 도장 찍기 **전**에 자재를 재 보는 것 | 21 에서 **금지**, 25 에서 **허용** |
| 도장 찍기 **전**에 지어진 층을 둘러보는 것 | 21·25 **둘 다 금지** |

- 건물은 **아래층부터** 올린다. 기초 없이 2층을 지을 수 없다.\
  그래서 생성자는 **반드시** 상위 생성자를 먼저 끝낸다.
- 시공 계획서가 여럿이면 하나로 몰아준다.\
  `this(...)` 가 그것이다 — 계획서를 넘기는 쪽에서는 도장을 안 찍는다.
- Java 21 까지는 **도장이 서류의 첫 줄이어야 했다.**\
  자재를 재 보는 것(인자 검증)도, 치수를 적어 두는 것(필드 대입)도 도장 뒤로 밀려났다.
- Java 25 는 **도장 앞줄을 열었다.**\
  다만 **이미 지어진 층을 둘러보는 것**(`this` 를 읽는 것)은 여전히 막는다 — 아직 아래층이 없기 때문이다.

```text
생성자 본문의 두 구역 (Java 25)

  +----------------------------------------+
  |  프롤로그  (JEP 513 이 연 구역)          |   this 를 읽을 수 없다
  |    - 인자 검증 / 계산 / 지역 변수        |   인스턴스 메서드 호출 불가
  |    - 이 클래스 필드에 "쓰기"만 가능       |
  +----------------------------------------+
  |  super(...)  또는  this(...)            |   <- 21 까지는 여기가 첫 줄이어야 했다
  +----------------------------------------+
  |  에필로그  (원래부터 있던 본문)           |   this 를 마음껏 쓴다
  +----------------------------------------+
```

**똑같은 구조로** Java 가 이렇게 동작한다: 도장 = `invokespecial` 한 줄, 그 앞 = 프롤로그, 그 뒤 = 에필로그.

실무에서 이게 걸리는 자리는 **인자 검증**이다.\
`super(...)` 에 넘길 값을 먼저 검사하고 싶은데 21 에서는 그 자리에 문장을 못 써서,\
`super(check(x))` 같은 **정적 헬퍼**로 우회해 왔다. 25 는 그 우회를 없앤다.

> **프롤로그(prologue)** — `super()`/`this()` 호출보다 **앞에** 오는 문장들. JEP 513 이 만든 구역 이름이다.\
> 예: `if (lo < 0) throw new IllegalArgumentException(); super(lo, hi);` 에서 `if` 문장이 프롤로그다.

> **에필로그(epilogue)** — `super()`/`this()` 호출 **뒤의** 문장들. Java 1.0 부터 있던 "생성자 본문"이 이것이다.\
> 예: `super(n); this.cache = new HashMap<>();` 에서 두 번째 줄이 에필로그다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. `this()`/`super()` 가 **첫 문장이어야 한다**는 규칙은 무엇을 지키려는 것이고, 그 대가는 무엇인가.
2. `this(...)` 로 위임하면 무엇이 달라지는가 — 클래스 파일에서 어떻게 구분되는가.
3. Java 25 의 **유연한 생성자 본문**은 무엇을 풀었고, **무엇은 여전히 안 되는가**.

## 동작 방식

### (1) 생성자는 셋 중 하나로 시작한다 — 그리고 둘은 내가 안 쓴다

**언제 쓰나** — 생성자를 하나 읽을 때, 그 첫 줄이 무엇인지 정할 때.

```text
내가 쓴 생성자의 첫 문장          컴파일러가 만드는 것
+---------------------------+   +---------------------------+
| super(...) 라고 썼다       |   | 그대로                     |
| this(...)  라고 썼다       |   | 그대로                     |
| 아무것도 안 썼다           |   | super()  를 끼워 넣는다     |
+---------------------------+   +---------------------------+
```

`NoCtor` 는 생성자를 **하나도 안 썼는데** 클래스 파일에는 생성자가 있다.

```text
javap -c -p NoCtor  — 출력 그대로

class NoCtor {
  NoCtor();
    Code:
       0: aload_0
       1: invokespecial #1                  // Method java/lang/Object."<init>":()V
       4: return
}
```

그림 해설 (한 단계씩):

- 소스에 없던 `NoCtor()` 가 클래스 파일에 있다 — **기본 생성자(default constructor)** 다.
- 그 본문은 `super()` 한 줄뿐이다.
- 생성자를 **하나라도** 쓰면 기본 생성자는 안 만들어진다.\
  그래서 `Foo(int x)` 만 쓴 클래스는 `new Foo()` 가 컴파일 에러가 된다.

비용 — 없다(바이트 세 개). 다만 **기본 생성자가 사라지는 것**이 하위 호환성을 깬다.\
라이브러리에 인자 있는 생성자를 하나 추가하면 남의 `new Foo()` 가 깨진다.

> **기본 생성자(default constructor)** — 생성자를 하나도 선언하지 않은 클래스에 컴파일러가 넣어 주는 무인자 생성자.\
> 예: `class A { }` 의 클래스 파일에는 `A()` 가 들어 있고, 그 접근 수준은 클래스와 같다.

### (2) `this()` 와 `super()` 는 클래스 파일에서 **대상 클래스 이름**으로 갈린다

**언제 쓰나** — "이 생성자가 위로 갔나 옆으로 갔나"를 확인할 때.

```java
class Animal {
    String kind;
    Animal() {
        this("unknown");
        System.out.println("  Animal() 본문");
    }
    Animal(String kind) {
        // 여기에 암묵적 super() 가 들어간다
        System.out.println("  Animal(String) 본문: kind=" + kind);
        this.kind = kind;
    }
}
class Dog extends Animal {
    int age;
    Dog() {
        // 암묵적 super() — Animal() 이 불린다
        System.out.println("  Dog() 본문");
    }
    Dog(int age) {
        super("dog");
        System.out.println("  Dog(int) 본문: age=" + age);
        this.age = age;
    }
}
```

**실행 결과** (`Ex.java`, JDK 21.0.5 — 17·25 동일)

```text
new Dog()
  Animal(String) 본문: kind=unknown
  Animal() 본문
  Dog() 본문
new Dog(3)
  Animal(String) 본문: kind=dog
  Dog(int) 본문: age=3
```

```text
javap -c -p Animal  — 출력 그대로

  Animal();                                       Animal(java.lang.String);
    Code:                                           Code:
       0: aload_0                                      0: aload_0
       1: ldc  #1   // String unknown                  1: invokespecial #22   // Method java/lang/Object."<init>":()V
       3: invokespecial #3  // Method "<init>":(...)   4: getstatic  #9  // System.out
       6: getstatic #9  // System.out                  7: aload_1
       9: ldc #15   // String   Animal() 본문          8: invokedynamic #27  // makeConcat
      11: invokevirtual #17 // println               13: invokevirtual #17 // println
      14: return                                     16: aload_0
                                                     17: aload_1
     클래스 이름이 없다 = this(...)                   18: putfield #31  // Field kind
                                                     21: return

                                                    java/lang/Object 가 붙었다 = super()
```

그림 해설 (한 단계씩):

- 두 생성자 다 **`invokespecial` 한 개**로 시작한다. 명령은 같다.
- 갈리는 것은 **대상**이다 — 왼쪽은 `"<init>":(String)V`(같은 클래스라 이름 생략), 오른쪽은 `java/lang/Object."<init>"`.
- 그래서 `javap` 에서 `this()` 와 `super()` 를 구분하는 방법은 **대상 클래스 이름 하나**다.
- `Animal(String)` 에 `super()` 를 **안 썼는데도** `Object.<init>` 호출이 들어 있다 — 컴파일러가 넣었다.
- 실행 출력을 보면 `new Dog()` 가 **세 생성자를 거친다**: `Dog()` → `Animal()` → `Animal(String)`.\
  그런데 본문 출력은 **가장 안쪽부터** 나온다 — 호출이 첫 줄에 있으니 당연하다.

비용 — 위임 한 단계당 스택 프레임 하나. 체인이 깊어도 객체는 **하나**다.

### (3) Java 25 — 프롤로그가 열렸다

**언제 쓰나** — `super(...)` 에 넘길 값을 먼저 검증하거나 가공하고 싶을 때.

```java
class Base { Base(int n) { System.out.println("  Base(" + n + ")"); } }
class Sub extends Base {
    private final int[] data;
    Sub(int[] src) {
        int[] copy = src.clone();                 // 지역 변수 — 계산
        if (copy.length == 0)                     // 검증
            throw new IllegalArgumentException("비었다");
        this.data = copy;                         // 필드 대입
        super(copy.length);                       // 그 다음에 super()
        System.out.println("  Sub 본문: data.length=" + data.length);
    }
}
```

**실행 결과** (`Ex.java`, JDK **25.0.1**)

```text
  Base(3)
  Sub 본문: data.length=3
  잡힘: 비었다
```

같은 파일을 JDK 21.0.5 로 컴파일하면:

```text
Ex.java:9: error: call to super must be first statement in constructor
        super(copy.length);                       // 그 다음에 super()
             ^
1 error
```

그림 해설 (한 단계씩):

- 25 에서는 **지역 변수 선언·검증·필드 대입**이 `super()` 앞에 온다.
- `IllegalArgumentException` 이 프롤로그에서 던져지면 **`Base` 생성자는 아예 안 불린다.**\
  출력의 세 번째 줄이 그 증거다 — `Base(0)` 이 찍히지 않았다.
- 21 은 이 파일을 통째로 거부한다. **같은 소스가 버전에 따라 컴파일되고 안 되고가 갈린다.**

비용 — 없다. 바이트코드에 새 명령이 들어가지 않는다(아래 (4) 참조).

### (4) 프롤로그는 바이트코드에서도 그냥 앞에 있다

**언제 쓰나** — "JVM 이 바뀐 건가, 컴파일러만 바뀐 건가"를 판단할 때.

06 편의 함정 — 부모 생성자가 자식 메서드를 부르면 자식 필드가 `null` 이다 — 을 25 로 고친 것이다.

```java
class Base {
    Base() { System.out.println("  Base 생성자가 본 값: " + describe()); }
    String describe() { return "Base"; }
}
class Fixed extends Base {
    private String name;
    Fixed(String n) {
        this.name = n;        // 25: super() 앞에서 필드를 채운다
        super();
        System.out.println("  Fixed 생성자가 본 값: " + describe());
    }
    @Override String describe() { return "name=" + name; }
}
```

**실행 결과** (`Ex.java`, JDK **25.0.1**)

```text
  Base 생성자가 본 값: name=derived
  Fixed 생성자가 본 값: name=derived
```

```text
javap -c -p Fixed  (JDK 25.0.1) — 출력 그대로

  Fixed(java.lang.String);
    Code:
         0: aload_0
         1: aload_1
         2: putfield      #1                  // Field name:Ljava/lang/String;   <- super() 보다 앞이다
         5: aload_0
         6: invokespecial #7                  // Method Base."<init>":()V
         9: getstatic     #13                 // Field java/lang/System.out:Ljava/io/PrintStream;
        12: aload_0
        13: invokevirtual #19                 // Method describe:()Ljava/lang/String;
        16: invokedynamic #23,  0             // InvokeDynamic #0:makeConcatWithConstants:(Ljava/lang/String;)Ljava/lang/String;
        21: invokevirtual #27                 // Method java/io/PrintStream.println:(Ljava/lang/String;)V
        24: return
```

그림 해설 (한 단계씩):

- 오프셋 **2 의 `putfield` 가 오프셋 6 의 `invokespecial` 보다 앞**에 있다.\
  이것이 JEP 513 의 전부다 — 새 명령은 하나도 없다.
- 06 편에서 `name=null` 이던 자리가 `name=derived` 가 되었다.\
  부모 생성자가 부른 `describe()` 는 여전히 **동적 디스패치**되어 자식 것이 불리는데, 이번엔 필드가 이미 채워져 있다.
- 그래서 **JVM 은 안 바뀌었다.** `<init>` 안에서 `super` 호출 전에 자기 필드를 쓰는 것은 JVM 검증기가 원래 허용하던 일이고, **javac 가 금지하고 있었을 뿐**이다.

비용 — 없다. 대신 **아래 「어디서 틀리나」 4번**의 위험이 새로 생긴다.

> **`invokespecial`** — 생성자·`super.`·`private`(구버전) 호출에 쓰는 JVM 명령. 대상이 **컴파일 타임에 정해진다.**\
> 예: `this(...)` 와 `super(...)` 가 둘 다 이 명령이라, `javap` 에서는 대상 클래스 이름으로만 구분한다.

## 문법 — 형태와 규칙

직접 쓴 최소 예제다.

### 형태

```java
class C extends P {
    int x;

    C()          { this(0); }              // 옆으로 위임
    C(int x)     { super(); this.x = x; }  // 위로 위임 (super() 는 생략 가능)
    C(int x, int y) { /* 아무것도 안 씀 */ } // 컴파일러가 super() 를 넣는다
}
```

| 첫 문장 | 뜻 | 초기화식·초기화 블록이 복사되나 |
|---|---|---|
| `super(...)` | 상위 생성자 호출 | **복사된다** |
| `this(...)` | 같은 클래스의 다른 생성자 호출 | 복사되지 않는다 |
| (생략) | 컴파일러가 `super()` 를 넣는다 | **복사된다** |

- 마지막 칸의 근거는 [`../06-initialization-order/`](../06-initialization-order/) 의 동작 방식 (3)이다.
- `this(...)` 와 `super(...)` 를 **둘 다** 쓸 수는 없다. 첫 문장은 하나뿐이다.

### 21 의 규칙 — 세 줄

- `this(...)`/`super(...)` 는 **생성자의 첫 문장**이어야 한다.
- 그 인자식에서 **`this` 를 쓸 수 없다**(아직 객체가 없다).
- 생성자 위임이 **순환하면** 컴파일 에러다.

### 25 가 바꾼 것 — 프롤로그에서 되는 것과 안 되는 것

| 프롤로그에서 | 21 | 25 |
|---|---|---|
| 지역 변수 선언·계산 | 불가 | **가능** |
| 인자 검증 후 `throw` | 불가 | **가능** |
| **이 클래스** 필드에 대입(쓰기) | 불가 | **가능** |
| 필드 읽기 (`this.f`) | 불가 | **불가** |
| 인스턴스 메서드 호출 | 불가 | **불가** |
| `this` 를 어딘가에 넘기기 | 불가 | **불가** |
| `static` 메서드 호출 | 가능(식 안에서) | 가능 |

한 줄 규칙: **25 는 "쓰기"를 열었고 "읽기"는 여전히 막는다.**

## 어디서 틀리나

### 1. 첫 문장 규칙을 로그 한 줄로 어긴다 — 그리고 버전이 갈린다

```java
Animal() {
    System.out.println("  Animal()  -> this(\"unknown\") 위임");
    this("unknown");
}
```

```text
$ javac Ex.java        (JDK 21.0.5)
Ex.java:5: error: call to this must be first statement in constructor
        this("unknown");
            ^
1 error
```

```text
$ javac Ex.java && java Ex        (JDK 25.0.1)
new Dog()
  Animal()  -> this("unknown") 위임
  Animal(String) 본문: kind=unknown
  Dog() 본문
new Dog(3)
  Animal(String) 본문: kind=dog
  Dog(int) 본문: age=3
```

- **21 은 에러, 25 는 통과한다.** 프롤로그는 `super(...)` 앞만이 아니라 **`this(...)` 앞도** 연다.
- 에러 메시지가 **`this(...)` 줄**을 가리키는 것이 함정이다. 고칠 곳은 그 위의 줄인데.
- 이 한 예제가 07 의 전부를 보여 준다 — **같은 소스가 21 에서는 안 되고 25 에서는 된다.**

### 2. 부모에 무인자 생성자가 없는데 자식이 아무것도 안 쓴다

```java
class HasCtor { HasCtor(int x) { } }
class Sub extends HasCtor {
    Sub() { }         // 암묵적 super() 를 부르려 하는데 HasCtor() 가 없다
}
```

```text
$ javac Ex.java
Ex.java:3: error: constructor HasCtor in class HasCtor cannot be applied to given types;
    Sub() { }         // 암묵적 super() 를 부르려 하는데 HasCtor() 가 없다
          ^
  required: int
  found:    no arguments
  reason: actual and formal argument lists differ in length
1 error
```

- 에러가 **`Sub()` 의 닫는 괄호**를 가리킨다. 그 자리에 보이지 않는 `super()` 가 있기 때문이다.
- 초보자가 "인자를 안 넘겼는데 왜 int 를 달라고 하지?" 라고 막히는 자리다.
- 라이브러리 설계 함의: **무인자 생성자를 없애는 변경은 모든 하위 클래스를 깬다.**

### 3. `this()` 인자에 `this` 를 넘기거나, 위임이 순환한다

```text
$ javac Ex.java        (Node() { this(this); })
Ex.java:4: error: cannot reference this before supertype constructor has been called
    Node() { this(this); }        // 아직 만들어지지 않은 this 를 넘긴다
                  ^
1 error
```

```text
$ javac Ex.java        (Loop() { this(1); }  /  Loop(int x) { this(); })
Ex.java:3: error: recursive constructor invocation
    Loop(int x)  { this();  }
                   ^
1 error
```

- 순환 위임은 **런타임 `StackOverflowError` 가 아니라 컴파일 에러**다. 컴파일러가 그래프를 본다.
- `this(this)` 의 에러 문구 `cannot reference this before supertype constructor has been called` 는\
  25 의 프롤로그 규칙 위반에서도 **똑같이** 나온다 — 규칙이 하나로 합쳐진 것이다.

### 4. (25) 프롤로그에서 필드를 쓰고 **바로 읽으려** 한다

```java
Sub(int v) {
    this.v = v;                 // 쓰기는 된다
    System.out.println(this.v); // 방금 쓴 값을 읽으려 한다
    super();
}
```

```text
$ javac Ex.java        (JDK 25.0.1)
Ex.java:6: error: cannot reference this before supertype constructor has been called
        System.out.println(this.v); // 방금 쓴 값을 읽으려 한다
                           ^
1 error
```

인스턴스 메서드도 마찬가지다.

```text
$ javac Ex.java        (JDK 25.0.1)
Ex.java:6: error: cannot reference helper() before supertype constructor has been called
        helper();      // 인스턴스 메서드 호출
        ^
1 error
```

- **쓰기는 되고 읽기는 안 된다** — 06 편의 「전방 참조」와 같은 모양의 비대칭이다.
- 이유: 프롤로그는 **이 클래스가 새로 선언한 필드**만 건드릴 수 있고,\
  읽기를 허용하면 상위 클래스가 아직 초기화 안 된 상태에서 `this` 가 새어 나간다.
- 실무 함의: 25 에서 프롤로그를 쓰면 **검증 → 대입 → `super()`** 순서로만 쓴다. 중간에 확인 로그를 못 넣는다.

### 5. (25) 프롤로그에서 채울 필드에 초기화식을 같이 둔다

```java
class Sub extends Base {
    private int v = 100;        // 필드 초기화식
    Sub(int x) {
        this.v = x;             // 프롤로그에서 대입
        super();                // <- 이 직후에 초기화식이 실행된다
    }
}
```

```text
$ javac Ex.java        (JDK 25.0.1)
Ex.java:5: error: cannot assign initialized field 'v' before supertype constructor has been called
        this.v = x;             // 프롤로그에서 대입
            ^
1 error
```

- `super()` **직후**에 필드 초기화식이 돈다([06 편의 동작 방식 (2)](../06-initialization-order/2-summary.md)).\
  그러니 프롤로그에서 넣은 값은 **`100` 으로 덮일 것**이다.
- **javac 가 그 조합을 아예 막는다.** 조용히 덮이지 않고 컴파일 에러가 된다 — 에러 문구에 `initialized field` 가 박혀 있다.
- 방어: 프롤로그에서 채울 필드에는 **초기화식을 두지 않는다.** 둘 중 하나만 쓴다.

## 구현 세부사항 대 언어 보장

| 항목 | 누가 보장하나 |
|---|---|
| `this()`/`super()` 가 첫 문장(21) / 프롤로그 뒤(25) | **언어 보장** — JLS §8.8.7 |
| 프롤로그에서 `this` 읽기 금지 | **언어 보장** — JEP 513 이 명시 |
| `this(...)` 위임 생성자에 초기화식이 복사되지 않음 | **언어 보장** — JLS §12.5 |
| `invokespecial` 대상 이름으로 `this()`/`super()` 가 갈려 보이는 것 | **구현 세부** — javac 와 javap 의 출력 형식 |
| 프롤로그가 `putfield` 를 앞에 놓는 것 | **구현 세부** — JVM 은 원래 허용했다. javac 가 막고 있었을 뿐 |
| 기본 생성자의 바이트코드가 `aload_0; invokespecial; return` 세 줄인 것 | **구현 세부** |

★ 핵심: **유연한 생성자 본문은 클래스 파일 포맷도 JVM 도 바꾸지 않았다.**\
25 로 컴파일한 클래스 파일을 21 JVM 이 못 읽는 이유는 **클래스 파일 버전 번호** 때문이지 새 명령 때문이 아니다.

## 언제 쓰고 언제 안 쓰나

| 쓸 것 | 안 쓸 것 |
|---|---|
| 생성자 여럿을 **하나로 모으기** -> `this(...)` 위임 | 같은 코드를 생성자마다 복붙 |
| 21 에서 인자 검증 -> `super(check(x))` 정적 헬퍼 | 21 에서 검증하려고 `super()` 뒤로 미루기(부모가 이미 돌았다) |
| 25 에서 인자 검증 -> 프롤로그에 `if ... throw` | 25 프롤로그에서 로그 찍기(읽기가 막힌다) |
| 불변 객체의 방어적 복사 -> 25 프롤로그에서 `clone()` 후 대입 | 프롤로그에서 채울 필드에 초기화식을 같이 두기 |

판단 규칙 세 줄.

- **생성자에서는 오버라이드 가능한 메서드를 부르지 않는다.** 25 가 완화해 주지만, 규칙을 바꿀 만큼은 아니다.
- **21 코드를 25 로 옮길 때 정적 헬퍼를 프롤로그로 되돌릴지는 선택이다.** 헬퍼가 재사용되고 있으면 그대로 둔다.
- **라이브러리라면 무인자 생성자를 함부로 없애지 않는다.**

## 핵심 문장

- 생성자의 시작은 `super(...)` · `this(...)` · (생략 시 컴파일러가 넣는 `super()`) **셋 중 하나**다.
- 클래스 파일에서 둘은 같은 `invokespecial` 이고, **대상 클래스 이름**으로만 갈린다.
- `this(...)` 로 위임하는 생성자에는 **필드 초기화식과 초기화 블록이 복사되지 않는다.**
- **Java 25**(JEP 513)는 `super()` 앞에 **계산·검증·이 클래스 필드 쓰기**를 허용했다. **읽기와 인스턴스 메서드 호출은 여전히 금지**다.
- 유연한 생성자 본문은 **javac 만 바뀐 것**이다 — 바이트코드는 `putfield` 가 `invokespecial` 앞에 놓일 뿐이다.

## 관련 자료

- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 07번)
- [`../06-initialization-order/`](../06-initialization-order/) — **초기화 순서가 거기, 여기는 `super()` 한 줄의 앞뒤**다.\
  "필드식과 블록이 언제 도나"는 06 이 정본이고, "그 앞에 무엇을 쓸 수 있나"가 07 이다
- [`../../../../oop-basics/`](../../../../oop-basics/) — **생성자·상속의 개념은 거기**(파이썬 예제), 여기는 **Java 가 그 개념에 건 문법 제약**이다
- [`../../../../../../history/java/java-25.md`](../../../../../../history/java/java-25.md) — **유연한 생성자 본문이 왜 들어왔나(JEP 513 의 논쟁)는 거기**, 여기는 **그래서 무엇을 쓸 수 있나**다
- [**09번 주제**](../09-inheritance-overriding/)(상속과 오버라이딩) — 생성자에서 불린 메서드가 왜 자식 것이 되는지는 그쪽이 정본
- [**14번 주제**](../14-records/)(`record`) — 컴팩트 생성자는 이 주제의 프롤로그와 비슷하지만 별개의 문법이다

## 용어 풀이

- **생성자(constructor)** — 클래스 이름과 같고 반환형이 없는 특수 메서드. 클래스 파일에서는 `<init>` 라는 이름을 갖는다.
- **기본 생성자(default constructor)** — 생성자를 하나도 선언하지 않았을 때 컴파일러가 넣어 주는 무인자 생성자.
- **명시적 생성자 호출(explicit constructor invocation)** — `this(...)` 또는 `super(...)`. JLS §8.8.7.1 의 용어다.
- **프롤로그(prologue)** — `super()`/`this()` 앞의 문장들. Java 25 부터 쓸 수 있다.
- **에필로그(epilogue)** — `super()`/`this()` 뒤의 문장들. 원래의 생성자 본문.
- **유연한 생성자 본문(flexible constructor bodies)** — JEP 513. 프롤로그를 허용한 Java 25 기능.
- **위임(delegation)** — 생성자가 `this(...)` 로 같은 클래스의 다른 생성자에게 일을 넘기는 것.
- **`invokespecial`** — 생성자·`super.` 호출용 JVM 명령. 대상이 컴파일 타임에 고정된다.
- **`this` 누출(this escape)** — 객체가 완성되기 전에 `this` 참조가 밖으로 나가는 것. 프롤로그 규칙이 막으려는 것이 이것이다.
- **정적 팩토리 헬퍼** — `super(check(x))` 처럼 `super()` 인자식 안에서만 검증하려고 만드는 `static` 메서드. 21 의 우회책.

## 더 들어가면

- **`record` 의 컴팩트 생성자**는 겉모습이 프롤로그와 비슷하지만 다른 것이다.\
  컴팩트 생성자는 **파라미터를 고쳐 쓰는** 자리이고, 필드 대입은 컴파일러가 끝에 붙인다.\
  `record` 는 암묵적으로 `java.lang.Record` 를 상속하므로 `super()` 를 쓸 수도 없다.
- **21 의 우회책이 왜 `static` 이어야 했나** — 인스턴스 메서드는 `this` 를 필요로 하기 때문이다.\
  `super(check(x))` 에서 `check` 가 인스턴스 메서드면 `cannot reference this before ...` 가 나온다.
- **프롤로그와 검사 예외** — 프롤로그에서 던진 예외는 상위 생성자를 아예 안 부른다.\
  객체가 만들어지다 만 상태로 새어 나가지 않는다는 뜻이라, **불변 객체의 검증 위치로는 프롤로그가 더 안전하다.**
- **`this()` 위임 체인의 길이 제한은 없다.** 다만 순환은 컴파일러가 잡는다(`recursive constructor invocation`).
