# java/syntax/12 — 중첩 클래스: static nested·inner·지역·익명 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·역어셈블 출력·컴파일 에러는 **실제로 돌려 얻은 것**이다.\
> 기본은 Temurin **JDK 21.0.5**. 버전이 갈리는 항목은 **17.0.13 · 25.0.1** 도 함께 돌렸고 그 사실을 줄마다 적었다.\
> 바이트코드는 `javap -c -p` · `javap -v -p` 출력을 그대로 옮겼다.\
> 프로그램은 `Ex.java (12-a)` 처럼 **라벨로 식별**한다 — 맨 아래 「이 주제를 확인한 실행 목록」에 전부 있다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 네 종류를 한 파일에 넣으면 클래스 파일이 몇 개 생기는가

**출력** (`Ex.java (12-a)`, JDK 21.0.5 — 실행 결과와 생성 파일 목록)

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

```text
Ex$1.class
Ex$1Local.class
Ex$2.class
Ex$Inner.class
Ex$Nested.class
Ex.class
```

**왜 그런가**

- **클래스 파일은 6개**다 — `Ex` + 중첩 다섯.
- 이름은 `Ex$Nested` · `Ex$Inner` · `Ex$1Local` · `Ex$1` · `Ex$2`.

```text
소스에 쓴 것                          만들어진 클래스 파일       이름 규칙
+------------------------------+     +------------------+     +--------------------+
| static class Nested          | --> | Ex$Nested.class  |     | 바깥$이름           |
| class Inner                  | --> | Ex$Inner.class   |     | 바깥$이름           |
| class Local (인스턴스 메서드) | --> | Ex$1Local.class  |     | 바깥$번호이름        |
| new Runnable(){} (같은 메서드)| --> | Ex$1.class       |     | 바깥$번호           |
| new Runnable(){} (main 안)   | --> | Ex$2.class       |     | 바깥$번호           |
| () -> {}                     | --> | (없음)            |     | 실행 시점에 만들어진다 |
+------------------------------+     +------------------+     +--------------------+
```

- **람다는 클래스 파일을 만들지 않는다.** 실행 중에 `Ex$$Lambda/0x0000764094005000` 이라는 이름으로 생긴다.\
  이름에 **메모리 주소가 섞여 있어** 실행할 때마다 달라진다 — 이 값을 기억하거나 비교에 쓰면 안 된다.
- 익명 클래스의 번호는 **바깥 클래스 안에서 나온 순서**다. `localAndAnon` 안의 것이 `$1`, `main` 안의 것이 `$2`.
- 지역 클래스만 **번호 + 이름**이 붙는다. 같은 이름의 지역 클래스가 여러 메서드에 있을 수 있기 때문이다.
- `Inner` 를 `main`(= `static` 문맥)에서 만들려면 **바깥 인스턴스를 먼저 대야 한다.**

  ```java
  Ex outer = new Ex();
  Ex.Inner in = outer.new Inner();   // new 앞에 인스턴스가 온다
  ```

  `new outer.Inner()` 가 아니다. 순서를 헷갈리면 컴파일이 안 된다.

> **`outer.new Inner()`** — inner 인스턴스를 바깥에서 만드는 문법(한정된 클래스 인스턴스 생성식).\
> 예: `e.new Inner()` 는 "이 `e` 를 바깥 인스턴스로 삼는 `Inner` 하나"를 만든다.

### 2. `javap -p` 로 열면 어느 클래스에 무슨 필드가 있는가

**출력** (`Ex.java (12-a)` · `javap -p`, JDK 21.0.5 — 출력 그대로)

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

**왜 그런가**

- **필드가 하나도 없는 것은 `Ex$Nested`** 다. `static` 이 붙었으므로 바깥과 아무 연결이 없다.
- `Ex$Inner` 에는 **`final Ex this$0`** 하나. 타입이 바깥 클래스 `Ex` 다.
- `Ex$1Local` 과 `Ex$1` 에는 **둘씩** — `val$captured`(캡처한 지역 변수)와 `this$0`(바깥 인스턴스).
- `Ex$Inner` 의 생성자는 **`Ex$Inner(Ex)`** — 소스에 생성자를 안 썼는데 **인자를 하나 받는다.**\
  컴파일러가 바깥 인스턴스를 받으려고 만들어 넣은 것이다.

```text
                    이 클래스가 바깥 인스턴스를 필요로 하는가?
                                    |
              +---------------------+---------------------+
              | 아니다                                    | 그렇다
              v                                           v
        Ex$Nested                                  Ex$Inner · Ex$1Local · Ex$1
        필드 없음                                   final Ex this$0
        Ex$Nested()                                생성자가 Ex 를 받는다
```

- **네 종류의 차이는 결국 이 필드 한 줄이다.** 선언 위치·이름 규칙은 그 결과다.
- 주의: `Ex$1Local()` 은 인자가 없는 것처럼 보이지만 **진짜 서명은 다르다** — 4번에서 본다.

### 3. `this$0` 는 생성자의 어디에서 대입되는가

**출력** (`Ex.java (12-a)` · `javap -c -p Ex$Inner`, 출력 그대로)

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
       7: invokedynamic #19,  0             // InvokeDynamic #0:makeConcatWithConstants:(Ljava/lang/String;)Ljava/lang/String;
      12: areturn
}
```

**왜 그런가**

- `super()` 호출은 **6번 줄**의 `invokespecial Object."<init>"` 이다.
- `putfield this$0` 은 **2번 줄** — `super()` 보다 **먼저**다.

```text
  0  aload_0            만들어지는 Inner 객체 자신
  1  aload_1            생성자가 받은 Ex (소스에 없는 인자)
  2  putfield this$0    바깥 참조를 먼저 심는다      <-- super() 앞
       |
  6  invokespecial Object."<init>"
       |
  9  return
```

- **모순이 아니다.** "첫 문장은 `super()`"는 **소스 수준의 규칙**이고, 클래스 파일에는 그런 제약이 없다.\
  컴파일러가 쓰는 합성 코드는 그 규칙 밖에 있다.
- **왜 이 순서여야 하나** — [**06번 주제**](../06-initialization-order/)와 이어진다.\
  `super()` 가 도는 동안 상위 클래스 생성자가 **오버라이드된 메서드를 부를 수 있고**,\
  그 메서드가 바깥 필드를 읽으면 그때 `this$0` 이 **이미 채워져 있어야** 한다.\
  뒤에 대입했다면 그 경로에서 `NullPointerException` 이 났을 것이다.
- `Ex.this.name` 과 그냥 `name` 은 **같은 바이트코드**다 — `getfield this$0` → `getfield Ex.name` 두 단계.\
  소스에 안 보일 뿐 **간접 참조가 한 번 더** 있다.

> **`putfield` / `getfield`** — 객체의 인스턴스 필드에 쓰고 읽는 JVM 명령.\
> 예: `this$0` 대입이 `putfield`, 바깥 필드 읽기가 `getfield` 두 번이다.

### 4. 지역 변수를 캡처한 뒤 바꾸면

**출력** (`Ex.java (12-err1)` · `javac`, JDK 21.0.5 — 출력 그대로)

```text
err1/Ex.java:5: error: local variables referenced from an inner class must be final or effectively final
            void show() { System.out.println(count); }
                                             ^
1 error
```

**왜 그런가**

- **컴파일되지 않는다.**
- 에러가 가리키는 줄은 **`count` 를 읽는 줄**(5행)이다. `count = 1;` 이 아니다.\
  진단 내용이 "읽은 변수가 effectively final 이 아니었다"이기 때문이다 —\
  **읽는 자리**가 문제의 자리이고, 대입은 그 자리를 위반으로 만든 원인일 뿐이다.
- **`count = 1;` 한 줄만 지우면 통과한다.** 값이 안 바뀌면 제약이 성립한다.
- 이유는 **지역 변수가 참조되는 것이 아니라 복사되기 때문**이다.

**출력** (`Ex.java (12-a)` · `javap -c -p Ex$1Local` 과 `javap -v -p`, 출력 그대로)

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

- `javap -c` 는 `Ex$1Local()` — **인자 없는 것처럼** 찍는다. `Signature: ()V` 쪽을 보여 주기 때문이다.
- 그런데 바이트코드는 `aload_1` 과 `iload_2` 를 쓰고, **진짜 descriptor 는 `(LEx;I)V`** 다.\
  `args_size=3` 이 그것을 확인해 준다(`this` + 인자 둘).
- 두 인자는 `MethodParameters` 에서 **`final mandated`**(언어가 요구해 생긴 것)와 **`final synthetic`**(컴파일러가 만든 것)로 갈려 있다.
- 즉 지역 변수 `captured` 는 **생성 시점의 값 사본**으로 `val$captured` 에 들어간다.\
  원본이 나중에 바뀌면 사본과 어긋나므로, 언어는 **원본을 못 바꾸게** 막는다.
- JLS §8.1.3 의 문장이 그것이다.\
  "Any local variable, formal parameter, or exception parameter used but not declared in an inner class must either be `final` or effectively final (§4.12.4)."

**필드는 왜 제약을 안 받나**

- 필드는 **복사되지 않는다.** `this$0` 을 통해 **매번 읽는다**(3번의 `getfield` 두 단계).
- 그래서 바깥 필드는 얼마든지 바뀌어도 되고, 중첩 클래스는 늘 최신 값을 본다.
- 여기서 관용 우회가 나온다 — `int[] box = {0};` 처럼 **한 칸짜리 배열**을 캡처하면\
  배열 **참조**는 안 바뀌므로 effectively final 이고, 내용은 바꿀 수 있다.\
  단 그 배열은 스레드 간에 안전하지 않다([**33번 주제**](../33-synchronized-and-volatile/)).

### 5. `static` 메서드 안의 지역 클래스

**출력** (`Ex.java (12-st)`, JDK 21.0.5 — 출력 그대로)

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

**왜 그런가**

- **글자 하나 안 다른 두 지역 클래스**인데 필드 구성이 갈렸다.

```text
  static 메서드 안 (Ex$1L)            인스턴스 메서드 안 (Ex$2L)
  +---------------------------+      +---------------------------+
  | final int val$n;          |      | final int val$n;          |
  |                           |      | final Ex this$0;   <-- 추가 |
  +---------------------------+      +---------------------------+
    캡처는 한다, 바깥은 없다             캡처도 하고 바깥도 붙잡는다
```

- `val$n` 은 **양쪽 다 있다.** 지역 변수 캡처는 `static` 여부와 무관하다.
- `this$0` 은 **인스턴스 메서드 쪽에만** 있다.
- `inStatic` 안의 `L` 에서 `field` 를 읽으면 **컴파일 에러**다 — 읽을 바깥 인스턴스가 없다.\
  12-err2 의 `non-static variable v cannot be referenced from a static context` 가 같은 진단이다.
- **익명 클래스도 같다.** `main`(= `static` 문맥) 안에서 만든 `Ex$2` 에는 `this$0` 이 없다.

```text
--- JDK 21.0.5 · javap -p Ex$2
Compiled from "Ex.java"
class Ex$2 implements java.lang.Runnable {
  Ex$2();
  public void run();
}
--- JDK 17.0.13 · javap -p Ex$2
Compiled from "Ex.java"
class Ex$2 implements java.lang.Runnable {
  Ex$2();
  public void run();
}
```

- **두 JDK 다 없다.** 7번에서 볼 17↔21 차이와 헷갈리면 안 된다.
- 차이를 정하는 것은 "**어디에 선언했는가**"다. "바깥을 썼는가"가 아니다.\
  JLS §8.1.3: "An instance of an inner local class or an anonymous class whose declaration occurs in a **static context** has no immediately enclosing instance."
- 7번의 17↔21 차이는 **언어가 아니라 컴파일러의 최적화**다 — 근거의 층이 다르다.

### 6. 익명 클래스의 `this` 와 람다의 `this`

**출력** (`Ex.java (12-b)`, JDK 21.0.5 — 출력 그대로)

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

**왜 그런가**

```text
익명 클래스 안에서                      람다 안에서
+-----------------------------+       +-----------------------------+
| this      -> Ex$1 객체       |       | this      -> Ex 객체         |
| Ex.this   -> Ex 객체         |       | Ex.this   -> Ex 객체 (같은 것) |
| 새 스코프가 하나 생긴다        |       | 새 스코프가 생기지 않는다      |
+-----------------------------+       +-----------------------------+
```

- 익명 클래스는 **새 클래스**다. 그 안의 `this` 는 그 클래스의 객체(`Ex$1`)다.
- 람다는 **새 클래스를 만들지 않는다.** `this` 는 바깥 인스턴스 그대로이고 `getClass()` 가 `Ex` 를 준다.
- 바깥 인스턴스를 가리키려면 익명 클래스 안에서 **`Ex.this`** 라고 쓴다.
- **조용히 깨지는 모양**은 `this` 를 밖으로 넘기는 코드다.

  ```java
  button.addListener(new Listener() { public void on() { register(this); } });  // Ex$1 을 등록
  button.addListener(() -> register(this));                                      // Ex 를 등록
  ```

  컴파일도 실행도 정상인데 **등록되는 객체가 다르다.** `equals`·해제(`unregister`)가 어긋난다.
- 방어: 익명 클래스 안에서 바깥을 쓸 거면 **`Outer.this` 로 명시**한다. 리팩토링해도 뜻이 안 변한다.
- `getDeclaredFields()` 는 익명 쪽에 **`Ex this$0`** 하나를, 람다 쪽에 **필드 1개**를 보여 준다.\
  람다 쪽 1개는 `this` 를 캡처했기 때문이다(7번의 `arg$1` 과 같은 자리).
- 람다 문법·캡처 규칙 전체는 [**29번 주제**](../29-lambda-expressions/)가 정본이다. 여기서는 대비만 본다.

### 7. 바깥을 하나도 안 쓰는 익명 클래스는 바깥을 붙잡는가

**출력** (`Ex.java (12-c)`, 세 JDK — 출력 그대로)

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

**왜 그런가**

```text
바깥을 하나도 안 쓰는 익명 클래스 (인스턴스 메서드 안)

  JDK 17.0.13                          JDK 21.0.5 · 25.0.1
  +---------------------------+        +---------------------------+
  | class Ex$1 {              |        | class Ex$1 {              |
  |   final Ex this$0;        |        |   (필드 없음)              |
  | }                         |        | }                         |
  +---------------------------+        +---------------------------+
    안 쓰는데도 바깥을 붙잡는다            안 쓰면 안 붙잡는다
```

- **`anonTask()`** — JDK 17 은 `field Ex this$0` 을 남겼고, 21·25 는 필드가 없다.\
  **소스는 한 글자도 안 다르다.** `javac` 버전만 달랐다.
- **`lambdaUsingField()`** — 세 버전 다 `field Ex arg$1` 하나.\
  람다는 필요한 것만 가져간다 — 바깥 인스턴스가 필요하면 그것 하나를 인자처럼 받는다.
- **`lambdaTask()` 를 두 번 불러 `==` 로 비교하면 `true`** 다(세 버전 동일).\
  캡처가 없으면 만들 때마다 새로 만들 이유가 없어 **같은 인스턴스가 재사용**됐다.
- **익명 클래스는 `false`** 다. `new` 를 쓴 이상 매번 새 객체가 나온다.
- **언어가 보장하는 것은 몇 개인가 — 하나도 없다.**\
  이 네 줄은 전부 **컴파일러·런타임의 구현 세부**다.\
  `this$0` 이라는 이름, 안 쓰는 참조를 버리는 것, 람다 클래스 이름의 모양(17은 `$$Lambda$1/`, 21·25는 `$$Lambda/`),\
  비캡처 람다의 인스턴스 재사용 — 어느 것도 명세나 javadoc 이 약속하지 않는다.
- 그래서 **"바깥을 안 쓰니 안전하다"는 판단 근거가 될 수 없다.**\
  근거로 쓸 수 있는 것은 "**`static` 으로 선언했다**"뿐이다(11번).

### 8. 오래 사는 목록에 태스크를 넣으면 바깥이 수거되는가

**출력** (`Ex.java (12-leak)`, 세 JDK — 출력 그대로)

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

**왜 그런가**

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

- **JDK 21 기준** — `UsingTask`(inner, 바깥 사용)만 `false`, 나머지 둘은 `true`.
- **JDK 17 에서 달라지는 줄은 가운데** — `inner (outer 미사용)` 이 `false` 가 된다.\
  7번의 `this$0` 유무와 **정확히 대응한다.** 필드가 있으면 붙잡고, 없으면 안 붙잡는다.
- **붙잡히는 것은 `Owner` 객체 전체**다. 태스크가 쓰는 것은 `size()` 하나지만,\
  `this$0` 는 메서드가 아니라 **객체를 가리키므로** `payload` 8MB 가 통째로 도달 가능해진다.
- 누수의 크기는 **콜백의 크기가 아니라 바깥이 끌고 있는 것 전부**의 크기다.
- ★ **단정하면 안 된다.** `System.gc()` 는 수거를 **보장하지 않는다**(javadoc 이 "best effort" 라고 쓴 메서드다).\
  이 표는 「이 머신의 이 실행에서 이렇게 **관찰**됐다」까지다.
  - `true` — 그 시점에 도달 불가였다는 **강한 신호**.
  - `false` — **여전히 도달 가능하다**는 뜻으로 읽는다(참조 사슬이 살아 있다는 것은 `javap` 로 따로 확인했다).
- 도달 가능성 개념과 GC 알고리즘은 [`../../언어-특성/README.md`](../../언어-특성/README.md) 가 정본이다.\
  여기서는 "**어떤 문법이 어떤 참조를 만드나**"까지만 다룬다.

> **best effort** — "해 보기는 하지만 결과를 약속하지 않는다"는 API 의 태도.\
> 예: `System.gc()` 는 수거를 시도하라고 알릴 뿐이고, 실제로 수거가 일어나는지는 정해져 있지 않다.

### 9. inner 클래스 안에 `static` 멤버를 두면

**출력** (`Ex.java (12-err3)` · `javac --release 15 / 16 / 21` — 출력 그대로)

```text
--- release 15
err3/Ex.java:3: error: Illegal static declaration in inner class Ex.Inner
        static int COUNT = 0;
                   ^
  modifier 'static' is only allowed in constant variable declarations
err3/Ex.java:4: error: Illegal static declaration in inner class Ex.Inner
        static void touch() { COUNT++; }
                    ^
  modifier 'static' is only allowed in constant variable declarations
2 errors
--- release 16
(컴파일 성공)
--- release 21
Inner.COUNT = 1
```

**왜 그런가**

- `--release 15` 는 **`Illegal static declaration in inner class Ex.Inner`** 두 개를 낸다 — 필드와 메서드 각각.
- 부가 줄의 **"only allowed in constant variable declarations"** 는 16 이전의 **유일한 예외**를 말한다.\
  `static final int X = 1;` 처럼 **상수 변수**(`final` + 상수 식 + 기본형이나 `String`)는 그때도 허용됐다.\
  상수 변수의 정의는 [**06번 주제**](../06-initialization-order/)가 정본이다.
- **`--release 16` 부터 통과한다.** 소스는 한 글자도 안 바꿨다.
- JLS §8.1.3 이 그 경계를 적어 둔다.\
  "All of the rules that apply to nested classes apply to inner classes. In particular, an inner class may declare and inherit `static` members (§8.2), and declare static initializers (§8.7), even though the inner class itself is not `static`."\
  그리고: "Prior to Java SE 16, an inner class could not declare static initializers, and could only declare `static` members that were constant variables (§4.12.4)."
- 완화가 따라온 기능은 **`record`**(JEP 395, JDK 16)다.\
  `record` 는 암묵적으로 `static` 이라, inner 클래스 안에 `record` 를 쓰려면 이 제약이 풀려야 했다.
- **`static class Nested` 안에서는 원래부터 된다.** `static` nested 는 일반 최상위 클래스와 능력이 같다.
- 실무 함정: **빌드 타깃이 15 이하면 최신 IDE 에서는 통과하고 CI 에서만 깨진다.**

### 10. `private` 을 넘나드는 접근을 컴파일러가 어떻게 처리하는가

**출력** (`Ex.java (12-nest)` · `javap -p`, `--release 21` 과 `--release 8` — 출력 그대로)

```text
--- release 21
Compiled from "Ex.java"
public class Ex {
  private int secret;
  public Ex();
  int readInner(Ex$Inner);
  public static void main(java.lang.String[]);
}
Compiled from "Ex.java"
class Ex$Inner {
  private int innerSecret;
  final Ex this$0;
  Ex$Inner(Ex);
  int readOuter();
}
--- release 8
Compiled from "Ex.java"
public class Ex {
  private int secret;
  public Ex();
  int readInner(Ex$Inner);
  public static void main(java.lang.String[]);
  static int access$000(Ex);
}
Compiled from "Ex.java"
class Ex$Inner {
  private int innerSecret;
  final Ex this$0;
  Ex$Inner(Ex);
  int readOuter();
  static int access$100(Ex$Inner);
}
```

**왜 그런가**

```text
release 21 (nestmate)                  release 8 (합성 브리지)
+-----------------------------+        +-----------------------------+
| Inner.readOuter()           |        | Inner.readOuter()           |
|   -> getfield Ex.secret     |        |   -> Ex.access$000(outer)   |
|      (직접 읽는다)            |        |      -> getfield Ex.secret  |
+-----------------------------+        +-----------------------------+
  메서드가 늘지 않는다                    양쪽에 하나씩 는다
```

- **JVM 의 `private` 은 클래스 단위**다. 소스에서 한 클래스처럼 보여도 `Ex` 와 `Ex$Inner` 는 **별개의 클래스 파일**이라\
  원래대로면 서로의 `private` 을 못 읽는다.
- `--release 8` 은 그래서 **합성 브리지 메서드**를 만든다 — `Ex` 쪽에 `access$000`, `Ex$Inner` 쪽에 `access$100`.\
  `private` 필드를 읽어 주는 **package-private `static` 메서드**다.
- `--release 21` 에는 **그 메서드가 없다.** **JDK 11 의 nestmate(JEP 181)** 가 클래스 파일에\
  `NestHost`/`NestMembers` 속성을 넣어 "이들은 한 둥지다"를 JVM 에 알리기 때문이다.

```text
NestMembers:
  Ex$Inner
  Ex$Nested
  Ex$2
  Ex$1
  Ex$1Local
```

- 둥지 명단에는 **이름 없는 익명 클래스까지** 들어 있다(`Ex.java (12-a)` 의 `javap -v` 출력).
- **무엇이 새어 나갔나** — 브리지 메서드는 `private` 이 아니라 **package-private** 이다.\
  같은 패키지의 아무 클래스나 `Ex.access$000(someEx)` 를 호출해 **`private` 필드를 읽을 수 있었다.**\
  즉 `private` 을 지키려고 만든 장치가 **`private` 을 패키지 수준으로 낮췄다.** nestmate 가 그것을 없앴다.
- 곁가지: `InnerClasses` 속성은 종류까지 적는다 — `Nested` 줄에만 `static` 이 붙고,\
  익명·지역 클래스 줄에는 `of class Ex` 가 없다(소스에서 이름으로 참조할 수 없는 것들이라).

### 11. 무엇이 언어 보장이고 무엇이 구현 세부인가

**언어 보장 — 설계 근거로 쓸 수 있다**

| 사실 | 근거 |
|---|---|
| inner 는 바깥 인스턴스를 필요로 한다 | JLS §8.1.3 — 바깥 인스턴스가 정해지는 시점까지 명세가 정한다 |
| `static` nested 와 `static` 문맥의 지역/익명에는 바깥 인스턴스가 없다 | JLS §8.1.3 — "has no immediately enclosing instance" |
| 캡처한 지역 변수는 `final` 또는 effectively final 이어야 한다 | JLS §8.1.3 |
| inner 안의 `static` 멤버는 Java SE 16부터 허용 | JLS §8.1.3 의 "Prior to Java SE 16 …" |

**구현 세부 — 설계 근거로 쓸 수 없다**

| 사실 | 무엇이 그것을 보여 줬나 |
|---|---|
| 필드 이름이 **`this$0`** 이라는 것 | `javap -p`. 명세는 이름을 정하지 않는다 |
| 캡처 필드 이름이 **`val$captured`** 라는 것 | 〃 |
| 익명 클래스 이름이 **`Ex$1`·`Ex$2`** 라는 것 | 〃. 번호 부여 순서도 컴파일러 재량 |
| 안 쓰는 바깥 참조를 **버린다/안 버린다** | JDK 17↔21 에서 갈렸다(7번) |
| **`access$000`** 브리지가 생긴다/안 생긴다 | `--release 8` ↔ 21 에서 갈렸다(10번) |
| 비캡처 람다가 **같은 인스턴스**로 재사용된다 | 세 JDK 에서 `true` 로 관찰했을 뿐 |

**각 질문에 대한 답**

- **`this$0` 이라는 이름** — 구현 세부다. `javac` 의 관례이고, 다른 컴파일러가 다른 이름을 써도 된다.
- **"바깥을 안 쓰면 참조를 안 남긴다"** — 구현 세부다.\
  근거: 같은 소스가 JDK 17 에서는 `this$0` 을 남겼고 21·25 에서는 안 남겼다(7번).\
  같은 소스가 버전에 따라 갈리면 **그것은 명세가 정한 것이 아니다.**
- **"inner 는 바깥 인스턴스를 필요로 한다"** — 언어 보장이다. **JLS §8.1.3** 이 정한다.\
  그래서 `outer.new Inner()` 문법이 있고, `static` 문맥에서 `new Inner()` 가 컴파일 에러가 된다(12-err2).
- **`System.gc()` 뒤 수거된 것** — "수거된다"로 적으면 **관찰을 보장으로 승격**한 것이다.\
  `System.gc()` 는 수거를 약속하지 않으므로, 적을 수 있는 것은 "**이 실행에서 수거된 것으로 관찰됐다**"까지다.\
  더 나쁜 것은 **`true` 가 나온 줄을 "안전하다"로 읽는 것**이다 — 다른 JDK·다른 컴파일러에서 뒤집힐 수 있다.
- 판단 규칙 한 줄: **`javap` 출력은 "무슨 일이 일어나는지"를 배우는 데 쓰고, "무슨 일이 보장되는지"의 근거로는 쓰지 않는다.**

### 12. 어디에 무엇을 쓰나

**리스너·콜백의 기본값을 `static` nested 로 두는 이유**

- 콜백은 **등록되는 순간 수명이 바깥보다 길어진다.** 전역 목록·스케줄러·이벤트 버스가 들고 있기 때문이다.
- inner 로 만들면 `this$0` 하나 때문에 **바깥 객체 전체가 같이 산다**(8번의 8MB).
- `static` 은 **언어 보장**이다. "안 쓰니까 안 붙잡겠지"는 보장이 아니다(11번).
- 필요한 것이 있으면 **생성자로 받는다.** 받은 만큼만 붙잡는다.

```text
나쁜 계약                                   좋은 계약
+-------------------------------+          +-------------------------------+
| class Tick implements Runnable|          | static class Tick             |
|   (inner)                     |          |   implements Runnable {       |
|   run() { repaint(); }        |          |   private final Painter p;    |
| REGISTRY.add(new Tick());     |          |   Tick(Painter p) {...}       |
+-------------------------------+          +-------------------------------+
  Screen 전체가 남는다                        Painter 만 남는다
```

**이터레이터를 inner 로 두는 이유**

- 이터레이터는 **컬렉션의 현재 상태를 실시간으로 봐야 한다** — 크기, 배열, 수정 횟수(`modCount`).
- 값을 복사해 가면 fail-fast(순회 중 수정 감지)가 성립하지 않는다.
- 그리고 이터레이터의 수명은 **보통 순회 한 번**이라 바깥을 붙잡아도 오래 남지 않는다.
- 즉 **inner 를 쓰는 조건은 "바깥 상태를 봐야 한다 + 수명이 바깥을 안 넘는다"** 둘 다다.
- fail-fast 자체는 [**43번 주제**](../43-iterator-and-fail-fast/)가 정본이다.

**추상 메서드가 둘인 인터페이스를 그 자리에서 구현해야 하면**

- **익명 클래스**다. 람다는 **추상 메서드가 하나**인 인터페이스에만 쓸 수 있다.
- 그 밖에 익명 클래스를 써야 하는 자리 둘.
  - 구현 안에서 **자기 자신(`this`)이 필요할 때**(6번).
  - **상태(필드)를 들고 있어야** 할 때 — 람다에는 필드를 선언할 수 없다.

**이중 중괄호 초기화가 만드는 문제 셋**

```java
Map<String,String> m = new HashMap<>() {{ put("a", "1"); }};
```

1. **익명 하위 클래스가 바깥 인스턴스를 붙잡는다** — 맵 하나 만들었는데 바깥이 딸려 간다.
2. **타입이 `HashMap` 이 아니다.** `Ex$1` 이라 직렬화·`equals`·프레임워크 매핑이 어긋난다.
3. **클래스 파일이 하나 더 생긴다.** 이런 초기화를 여러 군데 쓰면 그만큼 늘어난다.

- 대안은 `Map.of("a","1")` 이거나 평범한 `put` 두 줄이다.
- 이 관용구가 인스턴스 초기화 블록을 쓴다는 사실은 [**06번 주제**](../06-initialization-order/)와 이어진다.

**이 주제가 다루지 않는 것**

- **람다 문법 전체와 캡처 규칙** — [**29번 주제**](../29-lambda-expressions/)가 정본이다. 여기의 6·7번은 **중첩 클래스와의 대비**만 다룬다.
- **GC 알고리즘·힙 구조** — [`../../언어-특성/README.md`](../../언어-특성/README.md) 가 정본이다.\
  여기는 **도달 가능성**까지만 쓰고 그 아래로 내려가지 않는다.
- **중첩 클래스가 언제 왜 들어왔나** — [`../../../../../../history/java/jdk-1.1.md`](../../../../../../history/java/jdk-1.1.md).\
  nestmate 는 [`java-11.md`](../../../../../../history/java/java-11.md), inner-`static` 완화는 [`java-16.md`](../../../../../../history/java/java-16.md).

---

## 이 주제를 확인한 실행 목록

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Ex.java (12-a)` | 네 종류의 실행 출력 · 생성된 클래스 파일 6개와 이름 규칙 | 21 |
| `Ex.java (12-a)` + `javap -p` | `Ex$Nested` 무필드 / `Ex$Inner` 의 `this$0` / 지역·익명의 `val$` + `this$0` | 21 |
| `Ex.java (12-a)` + `javap -c -p Ex$Inner` | `putfield this$0` 이 `super()` 보다 앞 | 21 |
| `Ex.java (12-a)` + `javap -v -p Ex$1Local` | 진짜 descriptor `(LEx;I)V` · `MethodParameters` 의 `final mandated`/`final synthetic` | 21 |
| `Ex.java (12-a)` + `javap -v -p Ex` | `NestMembers` 명단 · `InnerClasses` 의 `static` 표시 | 21 |
| `Ex.java (12-a)` + `javap -p Ex$2` | `static main` 안의 익명 클래스에는 `this$0` 이 없음 | 17 · 21 (동일) |
| `Ex.java (12-b)` | 익명의 `this` = `Ex$1` / 람다의 `this` = 바깥 인스턴스 | 21 |
| `Ex.java (12-c)` | 캡처 발자국 — **17만 안 쓰는 익명에 `this$0` 을 남김** · 비캡처 람다 인스턴스 재사용 | 17 · 21 · 25 (갈림) |
| `Ex.java (12-leak)` | `WeakReference` + `System.gc()` 로 바깥 수거 여부 **관찰** | 17 · 21 · 25 (갈림) |
| `Ex.java (12-st)` + `javap -p` | `static` 메서드 안 지역 클래스에는 `this$0` 없음 | 21 |
| `Ex.java (12-nest)` + `javap -p` | `--release 8` 에만 `access$000`/`access$100` 생성 | 21 (`--release 8` / `21`) |
| `Ex.java (12-err1)` `javac` | `local variables referenced from an inner class must be final or effectively final` | 21 |
| `Ex.java (12-err2)` `javac` | `non-static variable v` / `non-static variable this cannot be referenced from a static context` | 21 |
| `Ex.java (12-err3)` `javac` | `Illegal static declaration in inner class` — 15 실패 / 16·21 성공 | 21 (`--release 15` / `16` / `21`) |
