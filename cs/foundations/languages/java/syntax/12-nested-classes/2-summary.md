# java/syntax/12 — 중첩 클래스: static nested·inner·지역·익명 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [JLS SE 21 §8.1.3 Inner Classes and Enclosing Instances](https://docs.oracle.com/javase/specs/jls/se21/html/jls-8.html) · [§8.1.1.4 `static` Classes](https://docs.oracle.com/javase/specs/jls/se21/html/jls-8.html) · [§8.5 Member Class and Interface Declarations](https://docs.oracle.com/javase/specs/jls/se21/html/jls-8.html) · [§14.3 Local Class and Interface Declarations](https://docs.oracle.com/javase/specs/jls/se21/html/jls-14.html)
> **실행 검증** — 이 문서의 모든 실행 출력·역어셈블 출력·컴파일 에러는 실제로 돌려 얻은 것이다.\
> 기본 JDK 는 Temurin **21.0.5**. 캡처 발자국(12-c)과 수거 관찰(12-leak)은 **17.0.13 · 21.0.5 · 25.0.1** 세 개에서 돌렸다.\
> 컴파일 에러는 `javac --release 8 / 15 / 16 / 21` 로 릴리스를 바꿔 가며 찍었다.\
> 바이트코드는 `javap -c -p` · `javap -v -p` 출력을 그대로 옮겼다.
> **버전** — 중첩 클래스 자체는 **JDK 1.1**에서 들어왔다(그 전에는 없었다 — [`../../../../../../history/java/jdk-1.1.md`](../../../../../../history/java/jdk-1.1.md)).\
> 이 주제에서 버전이 갈리는 것은 둘이다. **inner 클래스 안의 `static` 멤버는 Java SE 16부터** 허용된다.\
> **`private` 을 넘나드는 접근의 구현 방식은 JDK 11(JEP 181 nestmate)에서 바뀌었다** — 그 전에는 합성 브리지 메서드가 생겼다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 JLS 로, 동작은 실행·역어셈블 출력으로 접지했다.

## 한눈에 — 쉽게 말하면

**중첩 클래스 네 종류는 "집 한 채에 딸린 공간" 네 가지와 같다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 본채 | 바깥 클래스의 **인스턴스** (`Ex` 객체 하나) |
| 마당 끝의 별채 — 본채가 없어도 혼자 선다 | `static` nested 클래스 |
| 본채에 딸린 방 — 본채가 있어야만 생긴다 | inner(내부) 클래스 |
| 방 열쇠에 늘 같이 달려 있는 본채 현관 열쇠 | 컴파일러가 넣는 숨은 필드 `this$0` |
| 본채에서 한 가지 일을 하는 동안만 쓰려고 짜 넣은 가구 | 지역 클래스 |
| 그 가구에 이름조차 안 붙인 것 | 익명 클래스 |
| 가구를 짤 때 그 자리에 있던 물건을 **복사해 넣은** 것 | 캡처된 지역 변수 (`val$...` 필드) |
| 방 열쇠를 남에게 줬더니 본채를 허물 수 없게 된 것 | inner 인스턴스가 오래 사는 목록에 남아 바깥 객체가 수거되지 않는 것 |

- 별채는 **주소만 알면** 지을 수 있다. 본채가 아직 없어도 된다.
- 방은 **본채를 먼저 지어야** 생긴다 — 방 하나를 만들려면 "어느 본채의 방인지"를 대야 한다.
- 그리고 방 열쇠에는 **본채 현관 열쇠가 늘 같이 달려 있다.** 방만 쓰겠다고 열쇠를 받아 가도 본채가 딸려 온다.
- 이 딸려 오는 열쇠 하나가 이 주제의 모든 비용과 사고의 출처다.

```text
static nested                        inner
+-------------------------------+    +-------------------------------+
| new Ex.Nested()               |    | outer.new Inner()             |
|                               |    |                               |
| class Ex$Nested {             |    | class Ex$Inner {              |
|   (필드 없음)                  |    |   final Ex this$0;   <-- 딸려옴 |
| }                             |    | }                             |
+-------------------------------+    +-------------------------------+
  본채 없이도 만들 수 있다              본채를 먼저 대야 만들 수 있다
```

두 칸 다 `javap -p` 출력 그대로다(12-a). **차이는 필드 한 줄뿐이고, 그 한 줄이 전부를 가른다.**

**똑같은 구조로** Java 가 이렇게 동작한다: 별채 = `static class`, 방 = `class`(안에 `static` 없음), 딸려 오는 열쇠 = `this$0` 필드.

실무에서 이게 터지는 자리는 **리스너·콜백·`Runnable` 을 inner 클래스로 만들어 오래 사는 곳에 등록하는 코드**다.\
등록한 것은 작은 콜백 하나인데, 그 콜백이 `this$0` 로 바깥 객체를 붙잡고 있어 **바깥이 통째로 메모리에 남는다.**

> **중첩 클래스(nested class)** — 다른 클래스(나 인터페이스)의 선언 **안에** 선언된 클래스.\
> 예: `class Ex { class Inner {} }` 의 `Inner`. 네 종류를 통틀어 부르는 말이다.

> **inner 클래스(inner class)** — 중첩 클래스 중 `static` 이 **붙지 않은** 것.\
> JLS §8.1.3 의 정의를 그대로 옮기면: "An *inner class* is a nested class that is not explicitly or implicitly `static`."\
> 예: 멤버 클래스에서 `static` 을 뺀 것 · 지역 클래스 · 익명 클래스가 전부 여기 속한다.

> **바깥 인스턴스(enclosing instance)** — inner 클래스의 객체 하나가 딸려 있는 바깥 클래스의 객체.\
> JLS §8.1.3: "An instance `i` of a direct inner class C of a class or interface O is associated with an instance of O, known as the *immediately enclosing instance of `i`*."\
> 예: `outer.new Inner()` 에서 `outer` 가 그 `Inner` 객체의 바깥 인스턴스다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **네 종류는 무엇이 다른가** — 그리고 그 차이는 결국 **몇 가지 질문**에서 갈리는가.
2. inner 인스턴스 하나를 오래 들고 있으면 **왜 바깥 객체가 통째로 남는가** — 어디까지가 언어 보장이고 어디부터가 컴파일러 마음인가.
3. **익명 클래스와 람다는 무엇이 다른가** — `this` 와 캡처에서.

## 동작 방식

### (1) 한 프로그램에 넷을 다 넣으면 무엇이 생기나

**언제 쓰나** — "내가 쓴 중첩 클래스가 클래스 파일로 어떻게 떨어지나"를 확인할 때.

직접 쓴 최소 예제다 (`Ex.java (12-a)`).

```java
public class Ex {
    private String name = "바깥";
    static class Nested { ... }                       // (1) static nested
    class Inner { ... name ... }                      // (2) inner — 바깥 필드를 읽는다
    String localAndAnon(int seed) {
        int captured = seed * 10;                     // effectively final
        class Local { ... name ... captured ... }     // (3) 지역 클래스
        Runnable anon = new Runnable() { ... };       // (4) 익명 클래스
        ...
    }
    // main 안에서 익명 Runnable 하나와 람다 하나를 더 만든다
}
```

전체 소스는 [1-question.md](1-question.md) 1번에 있다.

**실행 결과** (`Ex.java (12-a)`, JDK 21.0.5)

```text
Nested
Inner -> 바깥
Anon  -> 바깥 / captured=40
Local -> 바깥 / captured=40
--- 클래스 이름 ---
Ex$Nested
Ex$Inner
Ex$2
Ex$$Lambda/0x0000764094005000
```

**생성된 클래스 파일**

```text
Ex$1.class
Ex$1Local.class
Ex$2.class
Ex$Inner.class
Ex$Nested.class
Ex.class
```

파일 목록 해설 (한 줄씩):

- 중첩 클래스는 **전부 별개의 `.class` 파일**이 된다. 바깥 클래스 파일 안에 들어가지 않는다.
- 이름 규칙이 종류마다 다르다.\
  멤버 클래스(nested·inner)는 **`바깥$이름`**, 지역 클래스는 **`바깥$번호이름`**, 익명 클래스는 **`바깥$번호`**.
- 익명 클래스의 번호는 **바깥 클래스 안에서 나온 순서**대로 1, 2 … 가 붙는다.
- **람다만 `.class` 파일이 없다.** 실행 시점에 `Ex$$Lambda/0x…` 라는 이름으로 만들어진다 — 이름에 메모리 주소가 섞여 있어 **실행할 때마다 달라진다.**
- 그래서 "람다는 익명 클래스의 설탕"이라는 말은 틀렸다 — 컴파일 산출물부터 다르다.

비용 — 중첩 클래스 하나당 클래스 파일 하나가 늘어난다.\
로딩·검증 대상이 그만큼 는다. **실행 성능에 대한 수치는 이 문서에 없다** — 측정하지 않았다.

> **지역 클래스(local class)** — 메서드·생성자·초기화 블록 **본문 안**에서 선언된 이름 있는 클래스(JLS §14.3).\
> 예: 위 `localAndAnon` 안의 `class Local`. 그 블록 밖에서는 이름조차 보이지 않는다.

> **익명 클래스(anonymous class)** — `new 인터페이스이름() { ... }` 형태로 **선언과 생성을 한 번에** 하는 이름 없는 클래스.\
> 예: 위의 `new Runnable() { public void run() { ... } }`. 클래스 파일에는 `Ex$1` 같은 번호 이름이 붙는다.

### (2) 갈림길은 하나 — "바깥 인스턴스가 필요한가"

**언제 쓰나** — 네 종류 중 무엇을 쓸지 고를 때. 그리고 왜 어떤 것은 되고 어떤 것은 안 되는지 판단할 때.

```text
                    이 클래스가 바깥 인스턴스를 필요로 하는가?
                                    |
              +---------------------+---------------------+
              | 아니다                                    | 그렇다
              v                                           v
        +-------------+                            +-------------+
        | this$0 없음  |                            | this$0 있음  |
        +-------------+                            +-------------+
              |                                           |
   - static nested                              - inner (멤버)
   - static 메서드 안의 지역/익명 클래스            - 인스턴스 메서드 안의 지역/익명 클래스
              |                                           |
   new Ex.Nested() 로 바로 만든다                 outer.new Inner() 로만 만든다
   바깥 인스턴스 필드는 못 읽는다                   바깥 인스턴스 필드를 그냥 읽는다
   바깥이 죽으면 같이 죽는다                       바깥을 살려 둔다
```

`javap -p` 가 이 갈림길을 그대로 보여 준다 (`Ex.java (12-a)`, 출력 그대로).

```text
--- javap -p Ex$Nested
Compiled from "Ex.java"
class Ex$Nested {
  Ex$Nested();
  java.lang.String show();
}
--- javap -p Ex$Inner
Compiled from "Ex.java"
class Ex$Inner {
  final Ex this$0;
  Ex$Inner(Ex);
  java.lang.String show();
}
--- javap -p Ex$1Local
Compiled from "Ex.java"
class Ex$1Local {
  final int val$captured;
  final Ex this$0;
  Ex$1Local();
  java.lang.String show();
}
--- javap -p Ex$1
Compiled from "Ex.java"
class Ex$1 implements java.lang.Runnable {
  final int val$captured;
  final Ex this$0;
  Ex$1();
  public void run();
}
```

그림 해설 (한 단계씩):

- `Ex$Nested` 에는 **필드가 하나도 없다.** 바깥과 아무 연결이 없다.
- `Ex$Inner` 에는 `final Ex this$0` 이 있고, **생성자가 `Ex` 를 받는다**(`Ex$Inner(Ex)`).\
  소스에는 인자 없는 생성자를 쓴 적이 없는데 컴파일러가 만들어 넣은 것이다.
- `Ex$1Local`·`Ex$1` 에는 **`this$0` 과 `val$captured` 가 둘 다** 있다 — 바깥 인스턴스도 붙잡고 캡처한 지역 변수도 복사해 들고 있다.
- JLS §8.1.3 이 정한 경계가 이것이다.\
  "An instance of an inner local class or an anonymous class whose declaration occurs in a **static context** has no immediately enclosing instance. Also, an instance of a `static` nested class (§8.1.1.4) has no immediately enclosing instance."

같은 지역 클래스를 `static` 메서드와 인스턴스 메서드에 하나씩 두고 비교하면 이 문장이 그대로 나온다 (`Ex.java (12-st)`).

`static void inStatic()` 와 `void inInstance()` 안에 **똑같이 생긴 `class L`** 을 하나씩 두고,\
둘 다 지역 변수 `n` 을 읽되 인스턴스 쪽만 바깥 필드 `field` 를 읽게 했다.

```text
static 메서드 안의 지역 클래스, n=1
인스턴스 메서드 안의 지역 클래스, n=2, 바깥 필드
Compiled from "Ex.java"
class Ex$1L {
  final int val$n;
  Ex$1L();
  void go();
}
Compiled from "Ex.java"
class Ex$2L {
  final int val$n;
  final Ex this$0;
  Ex$2L();
  void go();
}
```

- **글자 하나 안 다른 두 지역 클래스**인데, `static` 메서드 안의 것(`Ex$1L`)에는 `this$0` 이 **없다.**
- `n` 을 캡처한 `val$n` 은 양쪽 다 있다 — 지역 변수 캡처는 `static` 여부와 무관하다.
- 익명 클래스도 같다. `main` 안(= `static` 문맥)에서 만든 `Ex$2` 에는 `this$0` 이 없다.

```text
--- JDK 21.0.5 · javap -p Ex$2  (static main 안의 익명 클래스)
Compiled from "Ex.java"
class Ex$2 implements java.lang.Runnable {
  Ex$2();
  public void run();
}
--- JDK 17.0.13 · 같은 클래스
Compiled from "Ex.java"
class Ex$2 implements java.lang.Runnable {
  Ex$2();
  public void run();
}
```

- **두 JDK 다 `this$0` 이 없다.** 아래 (6)에서 볼 17/21 차이와 구분해야 한다 —\
  여기는 "안 써서 뺀 것"이 아니라 **`static` 문맥에는 바깥 인스턴스가 애초에 없어서** 없는 것이다.

비용 — `this$0` 이 있는 쪽은 객체 하나당 참조 한 칸이 늘고, 그보다 훨씬 큰 비용은 **그 참조가 바깥 객체 전체를 도달 가능하게 만든다**는 것이다((6) 참조).

> **`this$0`** — 컴파일러가 inner 클래스에 몰래 넣는 `final` 필드. 바깥 인스턴스를 가리킨다.\
> 예: `Ex$Inner` 의 `final Ex this$0`. 소스에는 없고 `javap -p` 로만 보인다.\
> **이 이름은 언어 명세가 정한 것이 아니라 `javac` 의 관례다**(「구현 세부사항 대 언어 보장」 참조).

> **`static` 문맥(static context)** — `static` 메서드·`static` 초기화 블록·`static` 필드 초기화식처럼 `this` 가 없는 자리.\
> 예: `public static void main` 의 본문. 여기서 선언된 지역·익명 클래스에는 바깥 인스턴스가 없다.

### (3) `this$0` 는 `super()` 보다 **먼저** 대입된다

**언제 쓰나** — "바깥 인스턴스는 언제부터 쓸 수 있나"를 따질 때. 06번 주제(초기화 순서)와 이어지는 자리다.

`Ex$Inner` 의 생성자를 역어셈블하면 이렇다 (`javap -c -p`, 출력 그대로).

```text
Compiled from "Ex.java"
class Ex$Inner {
  final Ex this$0;

  Ex$Inner(Ex);
    Code:
       0: aload_0
       1: aload_1
       2: putfield      #1                  // Field this$0:LEx;
       5: aload_0
       6: invokespecial #7                  // Method java/lang/Object."<init>":()V
       9: return

  java.lang.String show();
    Code:
       0: aload_0
       1: getfield      #1                  // Field this$0:LEx;
       4: getfield      #13                 // Field Ex.name:Ljava/lang/String;
       7: invokedynamic #19,  0             // InvokeDynamic #0:makeConcatWithConstants
      12: areturn
}
```

```text
Ex$Inner(Ex) 가 하는 일 (위에서 아래로)

  0  aload_0            새로 만들어지는 Inner 객체 자신
  1  aload_1            생성자가 받은 Ex — 소스에는 없는 인자
  2  putfield this$0    바깥 참조를 먼저 심는다          <-- 여기
       |
  6  invokespecial Object."<init>"    그 다음에야 super()
       |
  9  return
```

그림 해설 (한 단계씩):

- **`putfield this$0` 이 `invokespecial <init>` 보다 앞에 있다.**\
  "생성자의 첫 문장은 `super()` 여야 한다"는 소스 규칙이 바이트코드 수준에서는 이렇게 깨져 있다.
- 순서를 이렇게 잡은 이유는 06번 주제와 이어진다 — **상위 클래스 생성자가 오버라이드된 메서드를 부를 수 있고**, 그 메서드가 바깥 필드를 읽으면 그때 `this$0` 이 이미 채워져 있어야 하기 때문이다.
- `show()` 는 `getfield this$0` → `getfield Ex.name` 두 단계로 바깥 필드를 읽는다 — 소스에서는 그냥 `name` 이라고 썼을 뿐인데 **간접 참조가 한 번 더 있다.**
- `Ex.this` 라고 명시적으로 쓰든 그냥 `name` 이라고 쓰든 **같은 바이트코드**가 나온다.

비용 — 바깥 필드 접근마다 `getfield` 가 한 번 더 든다. 그 비용이 실제로 얼마인지, JIT 가 얼마나 지워 주는지는 **측정하지 않았다** — 이 문서에 수치는 없다.

### (4) 지역 변수는 **복사**된다 — 그래서 `final` 이어야 한다

**언제 쓰나** — "왜 지역 변수를 바꾸면 컴파일이 안 되나"를 따질 때.

`Ex$1Local` 의 생성자를 열면 이렇다 (`javap -c -p`, 출력 그대로).

```text
  Ex$1Local();
    Code:
       0: aload_0
       1: aload_1
       2: putfield      #1                  // Field this$0:LEx;
       5: aload_0
       6: iload_2
       7: putfield      #7                  // Field val$captured:I
      10: aload_0
      11: invokespecial #11                 // Method java/lang/Object."<init>":()V
      14: return
```

`javap -c` 는 생성자를 `Ex$1Local()` — **인자 없는 것처럼** 찍는다. 그런데 바이트코드는 `aload_1` 과 `iload_2` 를 쓴다.\
`javap -v` 로 진짜 서명을 보면 이렇다 (출력 그대로).

```text
    descriptor: (LEx;I)V
    flags: (0x0000)
    Code:
      stack=2, locals=3, args_size=3
    MethodParameters:
      Name                           Flags
      <no name>                      final mandated
      <no name>                      final synthetic
    Signature: #16                          // ()V
```

```text
소스가 쓴 것                         클래스 파일에 있는 것
+---------------------------+       +---------------------------+
| int captured = seed * 10; |       | Ex$1Local(Ex, int)        |
| class Local {             |       |   this$0     = 1번 인자    |
|   ... captured ...        |       |   val$captured = 2번 인자  |
| }                         |       |                           |
| new Local()               |       | 값을 그 자리에서 복사한다   |
+---------------------------+       +---------------------------+
  변수를 "보는" 것처럼 보인다          실제로는 생성 시점의 값 사본이다
```

그림 해설 (한 단계씩):

- 생성자의 진짜 descriptor 는 **`(LEx;I)V`** — `Ex` 하나와 `int` 하나를 받는다.
- 두 인자 다 `MethodParameters` 에서 **`final`** 로 표시돼 있다.\
  `mandated`(언어가 요구해서 생긴 것)와 `synthetic`(컴파일러가 만든 것)으로 종류까지 갈라 적혀 있다.
- `Signature: ()V` 는 **제네릭 서명**이고, 여기서는 "소스에 쓴 대로는 인자가 없다"는 뜻이다.\
  `javap -c` 가 인자를 안 보여 준 것은 이쪽을 찍었기 때문이다 — **눈에 보이는 서명과 진짜 서명이 다르다.**
- 결론: 지역 클래스는 변수를 **가리키는 것이 아니라 값을 복사해 간다.**
- 그래서 원본 변수가 나중에 바뀌면 **둘이 어긋난다.** 언어는 그 어긋남을 허용하는 대신 **원본을 못 바꾸게** 막는다.

`Ex.java (12-err1)` 로 그 금지를 직접 확인했다.

```java
public class Ex {
    void run() {
        int count = 0;
        class Local {
            void show() { System.out.println(count); }
        }
        count = 1;
        new Local().show();
    }
}
```

```text
err1/Ex.java:5: error: local variables referenced from an inner class must be final or effectively final
            void show() { System.out.println(count); }
                                             ^
1 error
```

- 에러가 가리키는 줄은 **`count` 를 읽는 줄**이지 `count = 1;` 이 아니다.\
  "읽은 변수가 effectively final 이 아니었다"는 것이 진단 내용이기 때문이다.
- `count = 1;` 한 줄만 지우면 컴파일된다. 값이 안 바뀌면 복사본과 원본이 어긋날 일이 없다.
- JLS §8.1.3 이 이렇게 못박는다.\
  "Any local variable, formal parameter, or exception parameter used but not declared in an inner class must either be `final` or effectively final (§4.12.4)."
- **필드는 이 제약을 안 받는다.** 필드는 복사되지 않고 `this$0` 을 통해 **매번 읽기** 때문이다.\
  그래서 "바뀌는 값을 캡처하고 싶으면 필드나 배열 한 칸에 담는다"는 우회가 성립한다.

비용 — 캡처 변수 하나당 필드 한 칸. `int` 하나면 작지만, 큰 배열이나 컬렉션을 캡처하면 **그 크기만큼 도달 가능해진다.**

> **effectively final** — `final` 이라고 안 썼지만 **초기화 뒤로 한 번도 대입되지 않은** 지역 변수.\
> 예: `int captured = seed * 10;` 뒤에 `captured` 에 다시 대입하는 줄이 없으면 effectively final 이다.\
> 이 개념 자체는 [**03번 주제**](../03-variables-and-assignment/)(변수와 대입)가 정본이다.

> **`val$...` 필드** — 컴파일러가 캡처한 지역 변수를 담으려고 만드는 합성 필드. 예: `captured` 는 `final int val$captured` 가 된다(이 이름도 `javac` 의 관례다).

> **합성(synthetic)** — 소스에 쓰지 않았는데 컴파일러가 만들어 넣은 멤버에 붙는 표시.\
> 예: `this$0`·`val$captured`·아래의 `access$000` 이 전부 합성 멤버다. `javap -v` 의 flags 에서 보인다.

### (5) 익명 클래스 대 람다 — `this` 가 가리키는 것이 다르다

**언제 쓰나** — 콜백 안에서 `this` 를 쓸 때. 그리고 둘 중 무엇을 쓸지 고를 때.

같은 메서드 안에 익명 클래스와 람다를 하나씩 두고 `this` 를 찍었다 (`Ex.java (12-b)`).

```java
public class Ex {
    private String id = "Ex 인스턴스";
    public String toString() { return id; }
    void compare() {
        Runnable anon   = new Runnable() { public void run() { /* this · this.getClass() · Ex.this 를 찍는다 */ } };
        Runnable lambda = () -> { /* this · this.getClass() 를 찍는다 */ };
        anon.run(); lambda.run();
    }
}
```

**실행 결과** (JDK 21.0.5)

```text
anon   this = Ex$1@232204a1
anon   this.getClass() = Ex$1
anon   Ex.this = Ex 인스턴스
lambda this = Ex 인스턴스
lambda this.getClass() = Ex
--- 캡처한 필드 목록 ---
anon   field: Ex this$0
lambda fields: 1
```

```text
익명 클래스 안에서                      람다 안에서
+-----------------------------+       +-----------------------------+
| this      -> Ex$1 객체       |       | this      -> Ex 객체         |
| Ex.this   -> Ex 객체         |       | Ex.this   -> Ex 객체 (같은 것) |
| 새 스코프가 하나 생긴다        |       | 새 스코프가 생기지 않는다      |
+-----------------------------+       +-----------------------------+
  바깥을 쓰려면 Ex.this 로 한정          바깥이 그냥 이어진다
```

그림 해설 (한 단계씩):

- 익명 클래스의 `this` 는 **익명 클래스 자기 자신**(`Ex$1`)이다. 바깥을 쓰려면 `Ex.this` 로 한정해야 한다.
- 람다의 `this` 는 **바깥 인스턴스 그 자체**다. `getClass()` 가 `Ex` 를 돌려준다 — 새 클래스가 아니다.
- 이것이 "람다는 익명 클래스의 축약"이 아닌 두 번째 이유다.\
  익명 클래스는 **스코프를 하나 더 만들고**, 람다는 만들지 않는다.
- 익명 클래스는 바깥을 **하나도 안 쓰는 경우에도** `this$0` 을 들고 있을 수 있고((6) 참조), 람다는 필요한 것만 `arg$1` 같은 필드로 가져간다.
- 람다 문법·캡처 규칙 전체는 [**29번 주제**](../29-lambda-expressions/)가 정본이다. 여기서는 **중첩 클래스와의 대비**만 본다.

비용 — 익명 클래스는 클래스 파일 하나 + `new` 마다 객체 하나. 람다는 (6)에서 보듯 **비캡처면 인스턴스가 재사용**되기도 한다.

> **`Ex.this` (한정된 `this`)** — 중첩 클래스 안에서 **바깥 클래스의 인스턴스**를 가리키는 문법.\
> 예: 익명 `Runnable` 안에서 `this` 는 그 `Runnable` 이고, `Ex.this` 가 바깥 `Ex` 객체다.

### (6) 바깥을 안 쓰면 참조도 안 남을까 — JDK 17 과 21 이 갈린다

**언제 쓰나** — "이 콜백은 바깥을 안 쓰니까 안전하다"고 판단하려 할 때. **그 판단이 버전에 달려 있다.**

바깥을 안 쓰는 익명 클래스와 람다를 각각 만들어 필드를 찍었다 (`Ex.java (12-c)`).

**실행 결과** (세 JDK, 출력 그대로)

```text
--- JDK 17.0.13-tem
anonTask()         class=Ex$1
    field Ex this$0
lambdaTask()       class=Ex$$Lambda$1/0x00007f3548000c58
    (필드 없음)
lambdaUsingField() class=Ex$$Lambda$2/0x00007f3548003800
    field Ex arg$1
--- 같은 람다를 두 번 만들면 ---
비캡처 람다 동일 인스턴스? true
익명 클래스 동일 인스턴스? false
--- JDK 21.0.5-tem
anonTask()         class=Ex$1
    (필드 없음)
lambdaTask()       class=Ex$$Lambda/0x000071a11c000c30
    (필드 없음)
lambdaUsingField() class=Ex$$Lambda/0x000071a11c004800
    field Ex arg$1
--- 같은 람다를 두 번 만들면 ---
비캡처 람다 동일 인스턴스? true
익명 클래스 동일 인스턴스? false
--- JDK 25.0.1-tem
anonTask()         class=Ex$1
    (필드 없음)
lambdaTask()       class=Ex$$Lambda/0x00000000a1040460
    (필드 없음)
lambdaUsingField() class=Ex$$Lambda/0x00000000a1041000
    field Ex arg$1
--- 같은 람다를 두 번 만들면 ---
비캡처 람다 동일 인스턴스? true
익명 클래스 동일 인스턴스? false
```

```text
바깥을 하나도 안 쓰는 익명 클래스 (인스턴스 메서드 안에서 만든 것)

  JDK 17.0.13                          JDK 21.0.5 · 25.0.1
  +---------------------------+        +---------------------------+
  | class Ex$1 {              |        | class Ex$1 {              |
  |   final Ex this$0;        |        |   (필드 없음)              |
  | }                         |        | }                         |
  +---------------------------+        +---------------------------+
    안 쓰는데도 바깥을 붙잡는다            안 쓰면 안 붙잡는다
```

그림 해설 (한 단계씩):

- **소스는 한 글자도 다르지 않다.** `javac` 버전만 다르다.
- JDK 17 은 바깥을 안 쓰는 익명 클래스에도 `this$0` 을 남겼고, 21·25 는 안 남겼다.
- 람다는 세 버전 다 같았다 — 안 쓰면 필드가 없고, 쓰면 `arg$1` 하나가 생긴다. 다만 람다 클래스 **이름**은 17이 `Ex$$Lambda$1/0x…`, 21·25 가 `Ex$$Lambda/0x…` 로 모양이 다르다.
- **비캡처 람다는 두 번 만들어도 같은 인스턴스**였다(`==` 가 `true`). 익명 클래스는 매번 새 객체였다.
- ★ 이것은 **세 버전에서 관찰한 결과**이지 보장이 아니다 — "21 이상이면 안 붙잡는다"를 설계 근거로 쓰면 안 된다(「구현 세부사항 대 언어 보장」).

**그래서 바깥 객체가 실제로 수거되나** — `WeakReference` 와 `System.gc()` 로 관찰했다 (`Ex.java (12-leak)`).

8MB 짜리 `payload` 를 든 `Owner` 안에 태스크 셋을 뒀다 —\
`UsingTask`(inner, 바깥 메서드를 쓴다) · `UnusedTask`(inner, 바깥을 안 쓴다) · `NestedTask`(`static` nested).\
태스크 하나를 `static` 목록에 넣고 `Owner` 지역 변수를 버린 뒤 `System.gc()` 를 돌렸다.

**관찰 결과** (세 JDK, 출력 그대로)

```text
--- JDK 17.0.13-tem
inner  (outer 사용)    필드 this$0   Owner 수거됨? false
inner  (outer 미사용)  필드 this$0   Owner 수거됨? false
nested (static)       필드 없음       Owner 수거됨? true
--- JDK 21.0.5-tem
inner  (outer 사용)    필드 this$0   Owner 수거됨? false
inner  (outer 미사용)  필드 없음       Owner 수거됨? true
nested (static)       필드 없음       Owner 수거됨? true
--- JDK 25.0.1-tem
inner  (outer 사용)    필드 this$0   Owner 수거됨? false
inner  (outer 미사용)  필드 없음       Owner 수거됨? true
nested (static)       필드 없음       Owner 수거됨? true
```

```text
REGISTRY 에 태스크 하나만 넣었는데 무엇이 살아 있나

  inner (바깥 사용)                      static nested
  REGISTRY                              REGISTRY
     |                                     |
     +-> UsingTask 객체                    +-> NestedTask 객체
            |                                     (끝)
            +-- this$0 --> Owner 객체
                             |
                             +-- payload (8MB)   <-- 같이 살아남는다
```

그림 해설 (한 단계씩):

- `Owner` 지역 변수는 이미 버렸는데도, **태스크 하나가 `this$0` 로 `Owner` 를 붙잡고 있다.**
- 붙잡힌 것은 태스크가 쓰는 `size()` 만이 아니라 **`Owner` 객체 전체**다 — 8MB 짜리 `payload` 까지 딸려 온다.
- `static nested` 는 세 JDK 다 수거됐다. 붙잡는 참조가 없기 때문이다.
- **"바깥 미사용" 줄이 JDK 17 에서만 `false` 다.** 위의 `this$0` 유무와 정확히 대응한다.
- ★ `System.gc()` 는 **수거를 보장하지 않는다.** 이 표는 「이 머신의 이 실행에서 이렇게 관찰됐다」까지다 — `true` 는 "그 시점에 도달 불가였다"는 강한 신호, `false` 는 "여전히 도달 가능하다"로 읽는다.
- 도달 가능성 개념 자체와 GC 알고리즘은 [`../../언어-특성/README.md`](../../언어-특성/README.md) 가 정본이다.\
  여기서는 **"어떤 문법이 어떤 참조를 만드나"**까지만 다룬다.

비용 — 누수의 크기는 콜백의 크기가 아니라 **바깥 객체가 끌고 있는 것 전부**의 크기다.

> **도달 가능(reachable)** — GC 루트(스레드 스택·`static` 필드 등)에서 참조를 따라가 닿을 수 있는 상태.\
> 예: `static` 목록 → 태스크 → `this$0` → `Owner` 로 이어지면 `Owner` 는 도달 가능하고, 수거되지 않는다.

> **`WeakReference`** — 대상을 붙잡지 않는 참조. 다른 강한 참조가 없으면 대상이 수거되고 `get()` 이 `null` 이 된다.\
> 예: 위 실험은 `ref.get() == null` 로 "수거됐나"를 읽었다.

### (7) `private` 을 넘나드는 접근 — JDK 11 이 방식을 바꿨다

**언제 쓰나** — "바깥의 `private` 필드를 어떻게 그냥 읽지?"가 궁금할 때.

```java
public class Ex {
    private int secret = 7;
    class Inner {
        private int innerSecret = 9;
        int readOuter() { return secret; }          // 바깥의 private 읽기
    }
    int readInner(Inner i) { return i.innerSecret; } // 안쪽의 private 읽기
}
```

같은 소스를 `--release 21` 과 `--release 8` 로 컴파일해 `javap -p` 로 비교했다 (`Ex.java (12-nest)`, 출력 그대로).

```text
--- release 21
public class Ex {
  private int secret;
  int readInner(Ex$Inner);
}
--- release 8
public class Ex {
  private int secret;
  int readInner(Ex$Inner);
  static int access$000(Ex);
}
```

(`javap -p` 출력에서 생성자·`main` 줄을 뺀 것이다. 전문은 [3-answer.md](3-answer.md) 10번에 있다.)

```text
release 21 (nestmate)                  release 8 (합성 브리지)
+-----------------------------+        +-----------------------------+
| Inner.readOuter()           |        | Inner.readOuter()           |
|   -> getfield Ex.secret     |        |   -> Ex.access$000(outer)   |
|      (직접 읽는다)            |        |      -> getfield Ex.secret  |
+-----------------------------+        +-----------------------------+
  메서드가 늘지 않는다                    package-private 메서드가 는다
```

그림 해설 (한 단계씩):

- `--release 8` 쪽에만 **`static int access$000(Ex)`** 가 생겼다. 소스에 없는 메서드다.
- `Ex$Inner` 쪽에도 짝이 생긴다 — `static int access$100(Ex$Inner)`.
- JVM 은 원래 `private` 을 **클래스 단위**로 봤다. 소스에서 한 클래스처럼 보이는 것도 클래스 파일은 둘이라\
  컴파일러가 **접근을 대신 해 주는 다리**를 놓아야 했다.
- **JDK 11 의 nestmate(JEP 181)** 가 클래스 파일에 `NestHost`/`NestMembers` 속성을 넣어 "이들은 한 둥지다"를 JVM 에 알린다 — 그래서 다리가 필요 없어졌다.
- `Ex.class` 의 속성을 열면 둥지 명단이 그대로 있다 (`javap -v`, 출력 그대로).

```text
NestMembers:
  Ex$Inner
  Ex$Nested
  Ex$2
  Ex$1
  Ex$1Local
```

- **이름 없는 익명 클래스까지 명단에 들어 있다.** 둥지는 소스의 중첩 구조 그대로 만들어진다.
- 같은 `javap -v` 의 `InnerClasses` 속성은 종류까지 구분해 적는다 — `Nested` 줄에만 `static` 이 붙고,\
  익명·지역 클래스 줄에는 바깥 클래스 이름(`of class Ex`)이 없다(출력 전문은 [3-answer.md](3-answer.md) 10번).\
  이 속성들이 `getEnclosingClass()`·`isAnonymousClass()` 같은 리플렉션 API 의 근거가 된다.

비용 — `--release 8` 에서는 합성 메서드가 쌍마다 하나씩 늘고, **`private` 이 package-private 표면으로 새어 나간다**(같은 패키지의 다른 클래스가 `access$000` 을 호출할 수 있다).

> **nestmate (JEP 181, JDK 11)** — 소스에서 한 최상위 클래스 안에 있던 클래스들을 JVM 이 **한 둥지**로 인정해,\
> 서로의 `private` 에 직접 접근하게 한 것.\
> 예: `Ex` 와 `Ex$Inner` 가 같은 둥지라 `Inner.readOuter()` 가 `Ex.secret` 을 바로 `getfield` 한다.

## 문법 — 형태와 규칙

직접 쓴 최소 예제다.

### 네 가지 선언 형태

```java
class Outer {
    private int field = 1;

    static class Nested { }                  // (1) static nested — 바깥 인스턴스 없음
    class Inner { int get() { return field; } }   // (2) inner — 바깥 인스턴스 필요

    void m() {
        int captured = 2;
        class Local { int get() { return field + captured; } }   // (3) 지역
        Runnable anon = new Runnable() {                          // (4) 익명
            public void run() { System.out.println(field + captured); }
        };
    }
}
```

| 종류 | 선언 위치 | 이름 | 바깥 인스턴스 | 생성 문법 |
|---|---|---|---|---|
| static nested | 클래스 본문 (`static` 붙임) | 있음 | **없음** | `new Outer.Nested()` |
| inner (멤버) | 클래스 본문 (`static` 안 붙임) | 있음 | **있음** | `outer.new Inner()` |
| 지역 | 메서드·생성자·초기화 블록 본문 | 있음 (블록 안에서만) | 인스턴스 문맥이면 있음 | `new Local()` |
| 익명 | 식(expression) 안 | 없음 | 인스턴스 문맥이면 있음 | `new I() { ... }` |

### 꼭 기억할 형태 셋

- **`outer.new Inner()`** — inner 인스턴스를 바깥에서 만드는 유일한 문법.\
  `new outer.Inner()` 가 아니다. **`new` 앞에 인스턴스가 온다.**
- **`Outer.this`** — 중첩 클래스 안에서 바깥 인스턴스를 가리킨다.\
  이름이 겹치지 않으면 생략해도 되지만, 익명 클래스 안에서 `this` 는 **바깥이 아니다.**
- **`Outer.Nested`** — static nested 는 타입 이름으로 바로 쓴다. `import Outer.Nested;` 도 된다.

### 무엇을 넣을 수 있나

- `static` nested 는 **일반 최상위 클래스와 같다.** `static` 필드·초기화 블록·다른 중첩 클래스를 전부 가질 수 있다.
- inner 클래스는 **Java SE 16 이전에는 `static` 멤버를 못 가졌다**(상수 변수만 예외).\
  16부터 허용된다 — JLS §8.1.3 의 "Prior to Java SE 16, an inner class could not declare static initializers, and could only declare `static` members that were constant variables (§4.12.4)."
- 지역 클래스는 **접근 제어자를 못 붙인다.** `public class Local` 은 컴파일 에러다.
- 익명 클래스는 **생성자를 선언할 수 없다.** 이름이 없으니 생성자 이름도 쓸 수 없다 —\
  대신 **인스턴스 초기화 블록**을 쓴다([**06번 주제**](../06-initialization-order/)).

## 어디서 틀리나

여섯 중 **셋은 컴파일 에러로 막히고, 셋은 조용히 지나간다.** 위험한 것은 뒤의 셋이다.

### 1. 리스너·콜백을 inner 로 만들어 오래 사는 곳에 등록한다 (조용히 지나간다)

```java
class Screen {
    private final byte[] bitmap = new byte[8 * 1024 * 1024];
    class Tick implements Runnable { public void run() { repaint(); } }   // inner
    void start() { Scheduler.REGISTRY.add(new Tick()); }                  // 전역 목록에 등록
    void repaint() { }
}
```

- 등록한 것은 `Tick` 하나지만, `Tick` 이 `this$0` 로 `Screen` 을 붙잡는다.
- `Screen` 을 버려도 **`bitmap` 8MB 가 같이 남는다** — (6)의 `Owner` 실험이 이것이다.
- 화면을 열고 닫기를 반복하면 **닫은 화면들이 전부 쌓인다.** 에러는 나지 않고 힙만 는다.
- 방어 셋.
  - 콜백을 **`static` nested** 로 만들고 필요한 것만 생성자로 받는다.
  - 또는 **람다**로 바꾼다 — 필요한 필드만 `arg$1` 로 가져간다.
  - 바깥이 꼭 필요하면 **`WeakReference<Screen>` 을 필드로** 들고 간다.
- **"이 inner 는 바깥을 안 쓴다"는 방어가 못 된다** — 5번을 보라.

### 2. `static` 문맥에서 inner 를 만들려 한다 (컴파일 에러)

```java
public class Ex {
    private int v = 1;
    class Inner { int get() { return v; } }
    static class Nested { int get() { return v; } }   // 바깥 인스턴스 필드 접근
    public static void main(String[] args) {
        Inner i = new Inner();                        // 바깥 인스턴스 없이 생성
    }
}
```

```text
err2/Ex.java:4: error: non-static variable v cannot be referenced from a static context
    static class Nested { int get() { return v; } }
                                             ^
err2/Ex.java:6: error: non-static variable this cannot be referenced from a static context
        Inner i = new Inner();
                  ^
2 errors
```

- 두 에러가 **같은 원인의 양면**이다. 둘 다 "여기엔 `this` 가 없다"는 말이다.
- 첫째 — `static` nested 는 바깥 인스턴스가 없으니 **인스턴스 필드 `v` 를 읽을 수 없다.**\
  `static` 필드였다면 읽힌다.
- 둘째 — `main` 은 `static` 문맥이라 `new Inner()` 가 쓸 **암묵적 바깥 인스턴스**가 없다.\
  에러가 `v` 가 아니라 **`this`** 를 가리키는 것이 이 진단의 핵심이다.
- 고치는 법은 바깥 인스턴스를 대는 것 — `Ex e = new Ex(); Ex.Inner i = e.new Inner();`
- **에러 메시지가 `static context` 라고 말할 때 진짜 범인은 대개 이 암묵적 `this`** 다.

### 3. inner 클래스 안에 `static` 멤버를 둔다 (16 이전에는 컴파일 에러)

```java
public class Ex {
    class Inner {
        static int COUNT = 0;
        static void touch() { COUNT++; }
    }
}
```

```text
--- release 15
err3/Ex.java:3: error: Illegal static declaration in inner class Ex.Inner
        static int COUNT = 0;
                   ^
  modifier 'static' is only allowed in constant variable declarations
2 errors
--- release 16
(컴파일 성공)
--- release 21
Inner.COUNT = 1
```

- **`--release 16` 부터 통과한다.** 소스는 한 글자도 안 바꿨다.
- 에러 메시지의 "only allowed in **constant variable** declarations" 가 16 이전의 예외를 말한다 —\
  `static final int X = 1;` 같은 상수 변수는 그때도 됐다([**06번 주제**](../06-initialization-order/)의 상수 변수).
- 이 완화는 `record` 를 들여오면서 따라온 것이다(JEP 395) — inner 클래스 안에 `record` 를 선언할 수 있어야 했다.
- 함정: **팀의 빌드 타깃이 15 이하면 최신 IDE 에서 짜다가 CI 에서만 깨진다.**

### 4. 익명 클래스 안의 `this` 가 바깥인 줄 안다 (조용히 지나간다)

```java
button.addListener(new Listener() {
    public void on() { register(this); }   // this = 익명 Listener 객체
});
button.addListener(() -> register(this));  // this = 바깥 인스턴스
```

- 두 줄이 **완전히 다른 객체를 등록한다.** 컴파일도 실행도 정상이다.
- (5)의 실행 결과가 그대로다 — 익명은 `Ex$1`, 람다는 `Ex`.
- 익명 클래스를 람다로 리팩토링하면 `this` 의 뜻이 **조용히 바뀐다.**\
  `this` 를 넘기는 코드가 있으면 그 줄만 깨진다.
- 방어: 익명 클래스 안에서 바깥을 쓸 거면 **`Outer.this` 로 명시**한다 — 리팩토링해도 뜻이 안 변한다.

### 5. "바깥을 안 쓰니 안 붙잡겠지"라고 판단한다 (버전에 달려 있다)

- (6)에서 봤듯 **JDK 17 은 안 쓰는 익명 클래스에도 `this$0` 을 남겼다.**
- 같은 소스, 같은 실행, `javac` 버전만 달랐는데 **누수 여부가 갈렸다.**
- 이것은 **최적화이지 명세가 아니다.** 21에서 됐다고 다른 컴파일러(ECJ 등)에서도 된다는 보장이 없다.
- 판단 규칙: **"바깥을 안 쓴다"가 아니라 "`static` 으로 선언했다"를 근거로 삼는다.**\
  `static` 은 언어 보장이고, 참조 제거는 컴파일러 재량이다.

### 6. 이중 중괄호 초기화 (조용히 지나간다)

```java
Map<String,String> m = new HashMap<>() {{ put("a", "1"); }};
```

- 이것은 **익명 `HashMap` 하위 클래스 + 인스턴스 초기화 블록**이다([**06번 주제**](../06-initialization-order/)).
- 그 익명 클래스가 **바깥 인스턴스를 붙잡는다** — 맵 하나를 만들었을 뿐인데 바깥이 딸려 간다.
- 게다가 타입이 `HashMap` 이 아니라 `Ex$1` 이라 **직렬화가 깨지고**, 클래스 파일도 하나 더 생긴다.
- 대안은 `Map.of(...)` 나 `var m = new HashMap<String,String>(); m.put(...)` 이다.

### 7. 지역 변수를 캡처한 뒤 바꾼다 (컴파일 에러)

- (4)의 `local variables referenced from an inner class must be final or effectively final` 이 그대로 나온다.
- 흔한 오해: **"캡처한 변수를 바꾸려면 `final` 을 떼면 된다."** 반대다 — 안 바꿔야 통과한다.
- 자주 쓰는 우회 `int[] box = {0};` 은 **배열 참조가 안 바뀌는 것**이라 통과한다. 다만 그 배열은 **여러 스레드에서 안전하지 않다**(목록의 **33번 주제**).

## 구현 세부사항 대 언어 보장

이 주제는 **구현 세부가 눈에 너무 잘 보여서** 그것을 언어 사실로 외우기 쉽다. 경계를 나눈다.

| 내가 본 것 | 무엇인가 | 근거 |
|---|---|---|
| inner 는 바깥 인스턴스를 **필요로 한다** | **언어 보장** | JLS §8.1.3 — 바깥 인스턴스가 결정되는 시점까지 명세가 정한다 |
| `static` nested·`static` 문맥의 지역/익명에는 바깥 인스턴스가 **없다** | **언어 보장** | JLS §8.1.3 — "has no immediately enclosing instance" |
| 캡처한 지역 변수는 `final` 또는 effectively final 이어야 한다 | **언어 보장** | JLS §8.1.3 |
| inner 안의 `static` 멤버는 SE 16부터 허용 | **언어 보장** | JLS §8.1.3 의 "Prior to Java SE 16 …" |
| 필드 이름이 **`this$0`** 이라는 것 | **구현 세부** | `javac` 의 관례. 명세는 이름을 정하지 않는다 |
| 캡처 필드 이름이 **`val$captured`** 라는 것 | **구현 세부** | 〃 |
| 익명 클래스 이름이 **`Ex$1`·`Ex$2`** 라는 것 | **구현 세부** | 번호 부여 순서도 컴파일러 재량이다 |
| 안 쓰는 바깥 참조를 **버린다/안 버린다** | **구현 세부** | JDK 17↔21 에서 갈렸다 — 같은 소스, 다른 결과 |
| **`access$000`** 브리지가 생긴다/안 생긴다 | **구현 세부** | `--release 8` 과 21 에서 갈렸다(JEP 181) |
| 비캡처 람다가 **같은 인스턴스**로 재사용된다 | **구현 세부** | 세 JDK 에서 `true` 로 관찰했을 뿐, javadoc 이 약속하지 않는다 |
| `System.gc()` 뒤 **수거됐다** | **관찰** | `System.gc()` 는 수거를 보장하지 않는다 |

판단 규칙 두 줄.

- **설계 근거로 쓸 수 있는 것은 위 표의 「언어 보장」 줄뿐이다.**\
  "21에서는 안 붙잡으니 inner 로 둬도 된다"는 컴파일러 버전에 코드를 거는 것이다.
- **`javap` 출력은 "무슨 일이 일어나는지"를 배우는 데 쓰고, "무슨 일이 보장되는지"의 근거로는 쓰지 않는다.**

## 언제 쓰고 언제 안 쓰나

| 쓸 것 | 안 쓸 것 |
|---|---|
| 바깥과 개념적으로 한 덩어리인 보조 타입 -> `static` nested (`Map.Entry` 가 이 모양이다) | 바깥을 안 쓰는데 `static` 을 안 붙인 멤버 클래스 — 기본값을 `static` 으로 잡는다 |
| 바깥 인스턴스의 상태를 **정말로** 들여다봐야 하는 뷰·이터레이터 -> inner | 리스너·콜백·`Runnable`·`TimerTask` -> inner (누수 경로 1번) |
| 한 메서드 안에서만 쓰는 타입, 이름을 붙여야 읽히는 것 -> 지역 클래스 | 두 메서드가 같이 쓰는 지역 클래스 — 그러면 nested 로 올린다 |
| 추상 메서드가 **둘 이상**인 인터페이스 구현 -> 익명 클래스 | 추상 메서드가 **하나**뿐인 인터페이스 -> 람다가 낫다 |
| 상태를 가지는 콜백 -> 익명 클래스나 지역 클래스 | 컬렉션 초기화 -> 이중 중괄호 (6번) |

판단 규칙 세 줄.

- **`static` 을 기본값으로 둔다.** 바깥 인스턴스가 정말 필요할 때만 뗀다 — 떼는 것은 결정이지 기본이 아니다.
- **오래 사는 곳에 등록할 것은 inner 로 만들지 않는다.** 등록 대상의 수명이 바깥 수명을 넘는다.
- **추상 메서드 하나짜리면 람다**, 그 이상이거나 `this` 가 필요하면 익명 클래스.

## 핵심 문장

- 중첩 클래스 네 종류는 **"바깥 인스턴스가 필요한가" 하나로 갈린다.** 나머지 차이(이름·선언 위치)는 그 결과다.
- inner 클래스에는 컴파일러가 **바깥을 가리키는 `final` 필드 하나**를 넣고, 생성자에 인자를 하나 더 붙인다 — 소스에는 안 보인다.
- 그 필드 하나 때문에 **작은 콜백이 바깥 객체 전체를 도달 가능하게** 만든다. 누수의 크기는 콜백이 아니라 바깥이 정한다.
- 지역 변수는 **참조되는 것이 아니라 복사된다.** 그래서 `final` 또는 effectively final 이어야 한다 — 필드는 이 제약을 안 받는다.
- 익명 클래스의 `this` 는 **자기 자신**이고 람다의 `this` 는 **바깥 인스턴스**다. 둘은 서로의 축약이 아니다.
- **`this$0` 라는 이름도, 안 쓰는 참조를 버리는 것도 언어 보장이 아니다.** 보장은 "inner 는 바깥 인스턴스를 필요로 한다"까지다.

## 관련 자료

경계를 먼저 선언한다 — 링크만으로는 중복이 안 막힌다.

- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 12번)
- [`../06-initialization-order/`](../06-initialization-order/) — **그쪽은** 필드·블록·생성자가 도는 순서. **여기는** 그 순서 안에서 `this$0` 이 `super()` 앞에 대입된다는 것과, 익명 클래스가 생성자 대신 인스턴스 초기화 블록을 쓰는 이유
- [**09번 주제**](../09-inheritance-overriding/)(상속과 오버라이딩) — **그쪽은** 동적 디스패치와 필드 숨김. **여기는** 중첩이 만드는 **이름 가리기**(중첩 클래스 안에서 같은 이름이 바깥을 가린다)만
- [**11번 주제**](../11-interfaces-default-methods/)(인터페이스 — `default`/`static`/`private` 메서드) — **그쪽은** 인터페이스 멤버 규칙. **여기는** 익명 클래스가 그 인터페이스를 **그 자리에서 구현**하는 문법만. 참고로 인터페이스 안의 중첩 클래스는 **언제나 암묵적 `static`** 이다
- [`../13-enum-classes/`](../13-enum-classes/) — **그쪽은** `enum` 의 상수별 본문. 그 본문이 실제로는 **익명 하위 클래스**라 (1)의 `$1` 이름 규칙이 거기서 다시 보인다
- [`../14-records/`](../14-records/) — `record` 는 **암묵적 `static`** 이라 inner 가 될 수 없고, 그 때문에 SE 16의 inner-`static` 완화가 필요했다
- [`../15-sealed-classes/`](../15-sealed-classes/) — **그쪽은** `permits` 와 허용 계층. 같은 파일에 하위 타입을 모으는 관용구가 중첩 클래스 위에 선다
- [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) — **그쪽은** 계약 다섯 조항. **여기와 겹치는 것**은 익명 클래스로 만든 객체가 타입 이름이 없어 `equals` 대상 판정이 어려워진다는 점 하나
- [**29번 주제**](../29-lambda-expressions/)(람다) — **람다는 그쪽이 정본이다.** 여기의 (5)·(6)은 **중첩 클래스와 대비되는 부분**만 · [**03번 주제**](../03-variables-and-assignment/)(effectively final 의 정의) · 목록의 **33번 주제**(`int[] box` 우회의 스레드 안전성)
- [`../../언어-특성/README.md`](../../언어-특성/README.md) — **그쪽은** GC·JIT·클래스로더·메모리 모델. **여기는** GC 알고리즘을 쓰지 않는다 — "어떤 문법이 어떤 참조를 만드나"와 **도달 가능성**까지만
- [`../../../../oop-basics/`](../../../../oop-basics/) — **그쪽은** 캡슐화·합성 개념(파이썬 기반). **여기는** 자바 문법이 그것을 **어떻게 강제하나** — "안쪽이 바깥을 안다"를 `this$0` 이라는 실제 필드로 강제한다
- [`../../../../../engineering/design-patterns-gof/`](../../../../../engineering/design-patterns-gof/) — **패턴 자체는 그쪽.** 여기는 이터레이터·빌더·상태 패턴의 **구현 수단**으로 중첩 클래스가 어떻게 쓰이나
- [`../../../../../data-structure/`](../../../../../data-structure/) — **자료구조 원리는 그쪽.** 여기는 연결 리스트의 `Node`·트리의 `TreeNode` 에 `static` 을 붙여야 하는 이유만
- [`../../../../../../history/java/jdk-1.1.md`](../../../../../../history/java/jdk-1.1.md) — **그쪽은** 중첩 클래스가 **언제 왜** 들어왔나(1.1). **여기는 어떻게 쓰고 무엇을 못 하나**
- [`java-8.md`](../../../../../../history/java/java-8.md) (람다가 들어온 맥락) · [`java-11.md`](../../../../../../history/java/java-11.md) (nestmate JEP 181) · [`java-16.md`](../../../../../../history/java/java-16.md) (`record` JEP 395 와 함께 inner-`static` 제약이 풀린 버전)

## 용어 풀이

- **중첩 클래스(nested class)** — 다른 클래스·인터페이스 선언 안에 선언된 클래스. 네 종류의 총칭.
- **inner 클래스(inner class)** — 중첩 클래스 중 명시적으로도 암묵적으로도 `static` 이 아닌 것(JLS §8.1.3). 멤버·지역·익명 셋이 여기 속한다.
- **`static` nested 클래스** — `static` 이 붙은 멤버 클래스. 바깥 인스턴스가 없고 일반 최상위 클래스와 능력이 같다.
- **지역 클래스 / 익명 클래스** — 앞은 메서드·생성자·초기화 블록 본문에서 선언된 이름 있는 클래스(블록 밖에서는 이름이 안 보인다), 뒤는 `new 타입() { ... }` 으로 선언과 생성을 한 번에 하는 이름 없는 클래스(생성자를 선언할 수 없다).
- **바깥 인스턴스(enclosing instance)** — inner 객체 하나가 딸려 있는 바깥 클래스의 객체. 생성 시점에 정해진다.
- **`this$0`** — 컴파일러가 inner 클래스에 넣는 합성 `final` 필드. 바깥 인스턴스를 가리킨다. **이름은 명세가 아니라 `javac` 의 관례다.**
- **`val$...` / 합성 멤버(synthetic member)** — 앞은 캡처한 지역 변수를 담는 합성 필드(이름 규칙은 역시 구현 세부), 뒤는 소스에 없는데 컴파일러가 만들어 넣은 필드·메서드 일반(`javap -v` 의 flags 에 표시된다).
- **effectively final** — `final` 이라고 쓰지 않았지만 초기화 뒤 다시 대입되지 않은 지역 변수.
- **`static` 문맥(static context)** — `this` 가 없는 자리(`static` 메서드·`static` 초기화 블록 등). 여기서 만든 지역·익명 클래스에는 바깥 인스턴스가 없다.
- **nestmate (JEP 181, JDK 11)** — 한 최상위 클래스에서 나온 클래스들을 JVM 이 한 둥지로 인정해 서로의 `private` 에 직접 접근하게 한 것.
- **`access$000`** — nestmate 이전에 `private` 접근을 대신해 주려고 컴파일러가 만들던 합성 브리지 메서드.
- **도달 가능(reachable)** — GC 루트에서 참조를 따라 닿을 수 있는 상태. 도달 가능하면 수거되지 않는다.
- **`NestMembers` / `InnerClasses`** — 클래스 파일 속성. 앞은 둥지 명단, 뒤는 중첩 관계와 종류(`static` 여부)를 적는다.

## 더 들어가면

- **인터페이스 안의 중첩 클래스는 언제나 암묵적 `static`** 이다(인터페이스에는 인스턴스가 없다). `enum`·`record`·중첩 `interface` 도 마찬가지로 암묵적 `static` 이다.
- **`Map.Entry` 가 `static` nested 의 표준 예**다. 엔트리 하나가 맵 전체를 붙잡으면 곤란하기 때문이다.\
  반대로 **`ArrayList` 의 이터레이터는 inner** 다 — 리스트의 `modCount` 를 실시간으로 봐야 하기 때문이다(목록의 **43번 주제**).
- **`this$0` 은 리플렉션에 그대로 보인다**((5)의 실행 출력이 그것이다). 프레임워크가 중첩 클래스를 인스턴스화하려다 실패하는 사고가 여기서 난다 — 인자 없어 보이는 생성자가 **실제로는 인자를 받기** 때문이다.
- **지역 클래스 이름의 숫자**(`Ex$1Local`)는 같은 이름의 지역 클래스가 여러 메서드에 있을 수 있어 붙는다 — 12-st 의 `Ex$1L`·`Ex$2L` 이 소스에서는 둘 다 `class L` 이다.
