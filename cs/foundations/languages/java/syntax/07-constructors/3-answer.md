# java/syntax/07 — 생성자: `this()`/`super()`·(25) 유연한 생성자 본문 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러 메시지는 **실제로 돌려 얻은 것**이다.\
> 21 기준 항목은 Temurin **17.0.13 · 21.0.5 · 25.0.1** 셋에서 다 돌려 출력이 같음을 확인했다.\
> **유연한 생성자 본문 항목은 25.0.1 에서만** 컴파일된다 — 21 의 에러도 함께 실었다.\
> 바이트코드는 `javap -c -p` 출력을 그대로 옮겼다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 위임 체인의 출력 순서를 예측하라

**출력** (`Ex.java`, JDK 21.0.5 — 17·25 동일)

```text
new Dog()
  Animal(String) 본문: kind=unknown
  Animal() 본문
  Dog() 본문
new Dog(3)
  Animal(String) 본문: kind=dog
  Dog(int) 본문: age=3
```

**왜 그런가**

```text
new Dog()  가 실제로 밟는 경로

  Dog()           첫 문장이 없다 -> 컴파일러가 super() 를 넣었다
    |
    +-> Animal()      첫 문장 this("unknown")
          |
          +-> Animal(String)   첫 문장이 없다 -> super() = Object()
                |
                +-> Object()
                |
                +-- "Animal(String) 본문" 출력      <- 가장 안쪽이 먼저 끝난다
          +-- "Animal() 본문" 출력
    +-- "Dog() 본문" 출력
```

- `new Dog()` 는 생성자 **셋**을 거친다(`Dog()` → `Animal()` → `Animal(String)`).\
  그런데 객체는 **하나**다 — 위임이지 생성이 아니다.
- `Dog()` 에 `super()` 도 `this()` 도 없으면 컴파일러가 **`super()` 를 첫 문장으로 넣는다.**
- 호출이 첫 문장이므로 본문 출력은 **가장 안쪽부터** 역순으로 나온다.
- `new Dog(3)` 은 `super("dog")` 로 `Animal(String)` 을 직접 부른다.\
  `Animal()` 을 건너뛰므로 두 줄이다.

### 2. `javap` 로 `this()` 와 `super()` 를 구분하라

**출력** (`javap -c -p Animal`, JDK 21.0.5)

```text
  Animal();
    Code:
       0: aload_0
       1: ldc           #1                  // String unknown
       3: invokespecial #3                  // Method "<init>":(Ljava/lang/String;)V
       6: getstatic     #9                  // Field java/lang/System.out:Ljava/io/PrintStream;
       9: ldc           #15                 // String   Animal() 본문
      11: invokevirtual #17                 // Method java/io/PrintStream.println:(Ljava/lang/String;)V
      14: return

  Animal(java.lang.String);
    Code:
       0: aload_0
       1: invokespecial #22                 // Method java/lang/Object."<init>":()V
       4: getstatic     #9                  // Field java/lang/System.out:Ljava/io/PrintStream;
       7: aload_1
       8: invokedynamic #27,  0             // InvokeDynamic #0:makeConcatWithConstants:(Ljava/lang/String;)Ljava/lang/String;
      13: invokevirtual #17                 // Method java/io/PrintStream.println:(Ljava/lang/String;)V
      16: aload_0
      17: aload_1
      18: putfield      #31                 // Field kind:Ljava/lang/String;
      21: return
```

**왜 그런가**

- 두 생성자 모두 **`invokespecial`** 로 시작한다. 명령 자체는 같다.
- 구분 단서는 **대상 클래스 이름**이다.

| `javap` 가 찍은 것 | 무슨 호출인가 |
|---|---|
| `Method "<init>":(...)` — 클래스 이름 없음 | `this(...)` (같은 클래스) |
| `Method java/lang/Object."<init>":()V` | `super()` (상위 클래스) |

- `Animal(String)` 에 `super()` 를 안 썼는데 호출이 보이는 이유: **컴파일러가 넣었다.**\
  `this(...)` 도 `super(...)` 도 안 쓴 생성자에는 `super()` 가 자동으로 들어간다(JLS §8.8.7).

> **`invokespecial`** — 대상이 **컴파일 타임에 고정되는** 호출 명령. 생성자와 `super.m()` 에 쓴다.\
> 예: `super.toString()` 은 `invokespecial`, `this.toString()` 은 `invokevirtual` 이라 디스패치 결과가 다르다.

### 3. 왜 `this()`/`super()` 가 첫 문장이어야 했나

**무엇을 막으려는 것인가**

- **상위 클래스가 초기화되기 전에 객체를 쓰는 것**이다.\
  기초 공사가 안 끝났는데 2층 방을 둘러보는 셈이다.
- 특히 `this` 가 밖으로 새어 나가면(다른 객체에 등록되거나 스레드에 넘어가면)\
  다른 코드가 **반쯤 만들어진 객체**를 보게 된다.

**만든 불편**

- `super(...)` 에 넘길 인자를 **미리 검증하거나 가공할 수 없었다.**
- 방어적 복사(`src.clone()`)를 해서 그 길이를 `super()` 에 넘기려면 식 안에서 다 해야 했다.
- 지역 변수를 만들 수 없으니 같은 계산을 여러 번 쓰면 **식을 반복**해야 했다.

**21 의 우회 형태** — `static` 헬퍼다.

```java
Sub(int[] src) {
    super(check(src).length);       // 정적 헬퍼로 우회 — 21 에서 되는 유일한 형태
    this.data = src.clone();
    System.out.println("  Sub 본문: data.length=" + data.length);
}
private static int[] check(int[] src) {
    if (src.length == 0) throw new IllegalArgumentException("비었다");
    return src;
}
```

**출력** (`Ex.java`, JDK 21.0.5)

```text
  Base(3)
  Sub 본문: data.length=3
  잡힘: 비었다
```

- 헬퍼가 **`static` 이어야 하는 이유**: 인스턴스 메서드는 `this` 를 필요로 하는데 아직 없다.

### 4. 부모에 무인자 생성자가 없다

**출력** (`javac Ex.java`, JDK 21.0.5)

```text
Ex.java:3: error: constructor HasCtor in class HasCtor cannot be applied to given types;
    Sub() { }         // 암묵적 super() 를 부르려 하는데 HasCtor() 가 없다
          ^
  required: int
  found:    no arguments
  reason: actual and formal argument lists differ in length
1 error
```

**왜 그런가**

- 컴파일되지 **않는다.** 에러는 `HasCtor(int)` 에 인자를 안 넘겼다고 말한다.
- 에러가 가리키는 자리는 **`Sub()` 의 닫는 중괄호 앞**이다.\
  그 자리에 **보이지 않는 `super()`** 가 있기 때문이다 — 소스에는 없는 코드를 에러가 가리킨다.
- 초보자가 "나는 인자를 안 넘겼는데 왜 `int` 를 달라고 하지?"에서 막히는 자리다.

**하위 호환성 규칙**

- `class Foo { }` 에 `Foo(int x)` 를 **추가하는 순간** 기본 생성자가 사라진다.
- 그러면 남의 `new Foo()` 도, `class Bar extends Foo { Bar() { } }` 도 전부 깨진다.
- 방어: 인자 있는 생성자를 추가할 때 **무인자 생성자를 명시적으로 같이 쓴다.**

### 5. 같은 소스, 21 과 25

**출력** — JDK **21.0.5** 는 컴파일을 거부한다.

```text
Ex.java:9: error: call to super must be first statement in constructor
        super(copy.length);                       // 그 다음에 super()
             ^
1 error
```

JDK **25.0.1** 은 컴파일되고 이렇게 출력한다.

```text
  Base(3)
  Sub 본문: data.length=3
  잡힘: 비었다
```

**왜 그런가**

- 25 의 **유연한 생성자 본문**(JEP 513)이 `super()` 앞에 지역 변수·검증·필드 대입을 허용한다.
- 빈 배열을 넘기면 **`Base` 생성자는 불리지 않는다.**\
  출력 셋째 줄이 `잡힘: 비었다` 뿐이고 `Base(0)` 이 없는 것이 그 증거다.
- 이것이 프롤로그의 실질적 값어치다 — **객체가 만들어지다 마는 일이 없다.**

같은 25 컴파일러라도 `--release 21` 을 주면 거부한다.

```text
Ex.java:8: error: flexible constructors is not supported in -source 21
        this.data = copy;                         // 필드 대입
        ^
  (use -source 25 or higher to enable flexible constructors)
```

### 6. 25 의 프롤로그에서 되는 것과 안 되는 것

**할 수 있는 것**

| 되는 것 | 예 |
|---|---|
| 지역 변수 선언·계산 | `int[] copy = src.clone();` |
| 인자 검증 후 `throw` | `if (n < 0) throw new IllegalArgumentException();` |
| **이 클래스가 선언한** 필드에 대입 | `this.data = copy;` |
| `static` 메서드 호출 | `Objects.requireNonNull(x)` |

**할 수 없는 것**

| 안 되는 것 | 에러 문구 |
|---|---|
| 필드 읽기 (`this.f`) | `cannot reference this before supertype constructor has been called` |
| 인스턴스 메서드 호출 | `cannot reference helper() before supertype constructor has been called` |
| `this` 를 인자로 넘기기 | 위와 같은 문구 |

**비대칭의 이유**

- **쓰기는 이 객체 안에서 끝난다.** 아무도 그 값을 볼 수 없다.
- **읽기는 밖으로 나간다.** 읽은 값을 출력하거나 넘기면, 상위 클래스가 아직 초기화 안 된 객체의 상태가 노출된다.
- 06 편의 「전방 참조 — 쓰기는 되고 읽기는 컴파일 에러」와 **같은 모양의 비대칭**이다.

### 7. 06 편의 함정을 25 로 고치면

**출력** (`Ex.java`, JDK **25.0.1**)

```text
  Base 생성자가 본 값: name=derived
  Fixed 생성자가 본 값: name=derived
```

**왜 그런가**

- 06 편의 같은 구조는 **`Base ctor : name=null`** 을 출력했다.\
  자식 필드 초기화가 `super()` 뒤에 있었기 때문이다.
- 25 에서는 `this.name = n` 이 `super()` **앞**에 있으므로, 부모 생성자가 `describe()` 를 부를 때 이미 채워져 있다.

`javap -c -p Fixed` (JDK 25.0.1) 에서 `putfield` 가 **먼저**다.

```text
  Fixed(java.lang.String);
    Code:
         0: aload_0
         1: aload_1
         2: putfield      #1                  // Field name:Ljava/lang/String;
         5: aload_0
         6: invokespecial #7                  // Method Base."<init>":()V
         9: getstatic     #13                 // Field java/lang/System.out:Ljava/io/PrintStream;
        12: aload_0
        13: invokevirtual #19                 // Method describe:()Ljava/lang/String;
        16: invokedynamic #23,  0             // InvokeDynamic #0:makeConcatWithConstants:(Ljava/lang/String;)Ljava/lang/String;
        21: invokevirtual #27                 // Method java/io/PrintStream.println:(Ljava/lang/String;)V
        24: return
```

**그런데도 규칙이 유효한 이유**

- 고쳐진 것은 **내가 통제하는 필드 하나**다.
- `Base` 의 생성자는 여전히 `describe()` 를 **동적 디스패치**로 부른다.\
  `Fixed` 의 하위 클래스가 또 재정의하면 그쪽 필드는 여전히 `null` 이다.
- 프롤로그는 **이 클래스가 선언한 필드만** 채울 수 있으므로, 계층이 셋이면 중간 계층은 못 막는다.
- 그래서 방어는 그대로다 — **생성자에서는 `private`·`final`·`static` 메서드만 부른다.**

### 8. 프롤로그 대입과 필드 초기화식을 같이 두면

**출력** (`javac Ex.java`, JDK **25.0.1**)

```text
Ex.java:5: error: cannot assign initialized field 'v' before supertype constructor has been called
        this.v = x;             // 프롤로그에서 대입
            ^
1 error
```

**왜 그런가**

- 컴파일되지 **않는다.**
- 만약 통과했다면 `v` 는 **`100`** 이 됐을 것이다.\
  근거는 06 편의 규칙 — **필드 초기화식은 `super()` 직후에 실행된다**(JLS §12.5 4단계).\
  프롤로그에서 넣은 `x` 를 초기화식이 덮는다.
- javac 는 그 조합을 **조용히 덮지 않고 막는다.** 에러 문구에 `initialized field` 가 박혀 있다.
- 방어: 프롤로그에서 채울 필드에는 초기화식을 두지 않는다. **둘 중 하나만** 쓴다.

### 9. 유연한 생성자 본문은 JVM 을 바꿨나

**바꾸지 않았다.**

- `putfield` 가 `invokespecial` 앞에 오는 바이트코드는 **원래도 유효했다.**\
  JVM 검증기는 "생성되는 객체의 자기 필드 쓰기"를 `super` 호출 전에도 허용해 왔다.
- 막고 있던 것은 **javac** 다 — 순수한 소스 레벨 제약이었다.
- 그래서 JEP 513 은 클래스 파일 포맷에 새 명령이나 속성을 넣지 않았다.

**그런데도 21 JVM 이 못 읽는 이유**

```text
$ java Ex        (JDK 21.0.5 로, 25.0.1 이 컴파일한 클래스를)
오류: 기본 클래스 Ex을(를) 로드하는 중 LinkageError가 발생했습니다.
	java.lang.UnsupportedClassVersionError: Ex has been compiled by a more recent version of the Java Runtime (class file version 69.0), this version of the Java Runtime only recognizes class file versions up to 65.0
```

- **클래스 파일 버전 번호** 때문이다. 25 는 69, 21 은 65 까지만 읽는다.
- 프롤로그를 안 쓴 클래스도 25 로 컴파일하면 똑같이 69 가 되어 21 에서 안 돈다.
- 즉 **기능이 아니라 버전 도장**이 막는 것이다.

### 10. `this` 를 미리 쓰면

**출력** (JDK 21.0.5)

```text
Ex.java:4: error: cannot reference this before supertype constructor has been called
    Node() { this(this); }        // 아직 만들어지지 않은 this 를 넘긴다
                  ^
1 error
```

```text
Ex.java:3: error: recursive constructor invocation
    Loop(int x)  { this();  }
                   ^
1 error
```

**왜 그런가**

- `this(this)` — 인자식은 `super()`/`this()` **앞에 평가되므로**, 아직 없는 `this` 를 읽는 셈이다.
- `Loop` 의 순환은 **컴파일 타임에** 잡힌다. `StackOverflowError` 가 아니다.\
  컴파일러가 생성자 위임 그래프를 보고 사이클을 찾는다.
- `this(this)` 의 에러 문구가 25 프롤로그 위반과 같은 이유:\
  둘 다 **"상위 생성자 호출 전에 `this` 를 참조했다"**는 하나의 규칙이다.\
  25 는 그 규칙을 **완화한 것이 아니라 정밀하게 만든 것**이다 — 쓰기만 예외로 뺐다.

### 11. 생성자를 하나도 안 쓰면

**출력** (`javap -c -p NoCtor`, JDK 21.0.5)

```text
Compiled from "Ex.java"
class NoCtor {
  NoCtor();
    Code:
       0: aload_0
       1: invokespecial #1                  // Method java/lang/Object."<init>":()V
       4: return
}
```

**왜 그런가**

- 소스에 없던 `NoCtor()` 가 있다 — **기본 생성자**다.
- 본문은 `super()` 한 줄, 바이트코드 세 줄이다.
- `HasCtor` 에 무인자 생성자가 없는 이유: **생성자를 하나라도 선언하면 기본 생성자는 안 만들어진다.**\
  "없으면 채워 준다"이지 "항상 있다"가 아니다.
- 기본 생성자의 접근 수준은 **클래스와 같다.** `public class` 면 `public`, package-private 클래스면 package-private 이다.

### 12. 정본 경계

**필드 초기화식·초기화 블록의 실행 순서**

- [`../06-initialization-order/`](../06-initialization-order/) 가 정본이다.\
  이 주제는 그 순서를 **전제**하고, `super()` 한 줄의 앞뒤만 다룬다.

**`this(...)` 위임 생성자에 초기화 블록이 복사되지 않는다는 사실**

- 06 편의 동작 방식 (3) — 두 생성자의 `javap -c -p` 를 나란히 놓아 증명한 것이다.
- 07 에서는 그것을 **표의 한 칸**으로만 재인용한다.

**유연한 생성자 본문이 왜 들어왔나**

- [`../../../../../../history/java/java-25.md`](../../../../../../history/java/java-25.md) 와 [JEP 513](https://openjdk.org/jeps/513) 이다.\
  여기는 **그래서 무엇을 쓸 수 있나**만 다룬다.

**`record` 의 컴팩트 생성자와 같은 것인가**

- **아니다.** 컴팩트 생성자는 `record` 전용 문법으로, **파라미터를 고쳐 쓰는** 자리다.\
  필드 대입은 컴파일러가 끝에 붙인다.
- `record` 는 암묵적으로 `java.lang.Record` 를 상속하므로 `super(...)` 를 쓸 수도 없다.
- [**14번 주제**](../14-records/)가 정본이다.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `07/a/Ex` | `this()`/`super()` 위임 체인의 출력 순서 | 17 · 21 · 25 (출력 동일) |
| `07/a` + `javap -c -p Animal` | `this()`/`super()` 가 대상 클래스 이름으로 갈림 | 21 |
| `07/c` + `javap -c -p NoCtor` | 기본 생성자가 클래스 파일에 있음 | 21 |
| `07/e1/Ex` | `this()` 가 첫 문장이 아님 — **21 에러 / 25 통과** | 21 · 25 (갈림) |
| `07/e2/Ex` | `super()` 와 `this()` 를 둘 다 쓰면 에러 | 21 |
| `07/e3/Ex` | `super()` 앞 필드 대입 — **21 에러 / 25 통과** | 17 · 21 · 25 (갈림) |
| `07/e4/Ex` | `super()` 앞 필드 읽기 — **21·25 둘 다 에러** | 17 · 21 · 25 |
| `07/e5/Ex` | `super()` 앞 인자 검증 — **21 에러 / 25 통과** | 17 · 21 · 25 (갈림) |
| `07/e6/Ex` | 부모에 무인자 생성자가 없음 | 21 |
| `07/e7/Ex` | `this(this)` — `cannot reference this before ...` | 21 |
| `07/e8/Ex` | 생성자 순환 위임 — `recursive constructor invocation` | 21 |
| `07/e9/Ex` | 프롤로그에서 필드 읽기 금지 | 25 |
| `07/e10/Ex` | 프롤로그에서 인스턴스 메서드 호출 금지 | 25 |
| `07/b/Ex` + `javap -c -p Fixed` | 프롤로그가 06 의 함정을 고침 · `putfield` 가 앞 | 25 (21 은 컴파일 에러) |
| `07/d/Ex` | 프롤로그 종합(계산·검증·대입) · 빈 배열이면 `Base` 미호출 | 25 (21 은 컴파일 에러) |
| `07/d` 클래스를 21 JVM 에 | `UnsupportedClassVersionError` 69.0 vs 65.0 | 25 컴파일 / 21 실행 |
| `07/d` + `javac --release 21` | `flexible constructors is not supported in -source 21` | 25 |
| `07/f/Ex` | 21 의 정적 헬퍼 우회책 | 17 · 21 · 25 (출력 동일) |
| `07/g/Ex` | 프롤로그 대입 + 초기화식 = 컴파일 에러 | 25 |

**구현 의존 항목** — `javap` 의 출력 형식(오프셋·상수 풀 번호 `#n`)은 컴파일러 버전에 따라 달라질 수 있다.\
명령 이름과 순서, 대상 클래스 이름은 **언어 규칙에 묶인 것**이라 바뀌지 않는다.

**버전이 오르면 다시 돌릴 것** — 유연한 생성자 본문 관련 항목 전부.\
21 에서 에러가 나던 것이 LTS 가 올라가면 통과하게 되므로, 「21 에러 / 25 통과」로 적힌 다섯 줄을 다시 찍는다.
