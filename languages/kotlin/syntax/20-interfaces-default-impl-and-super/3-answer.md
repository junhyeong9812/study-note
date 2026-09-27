# kotlin/syntax/20 — 인터페이스: 기본 구현·프로퍼티 선언·충돌 해소(`super<T>`) — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javap` 에서 실제로 얻었다.\
> 역어셈블은 **기본 `-jvm-target`(1.8 · `major version: 52`)** 이고, ★★ **`-jvm-default` 는 명시한 자리 말고는 전부 기본값**이다.
> ★★ 아래 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적은 자리가 없다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★ 안 적은 것은 인터페이스 구현이 돌고, 덮은 것은 `super` 로 원본을 부른다

**출력**

```text
===== 소스: greet.kt =====
interface Greeter {
    val name: String
    val shout: String
        get() = name.uppercase()

    fun greet(): String = "안녕, $name"
    fun mustImplement(): Int
}

class Korean(override val name: String) : Greeter {
    override fun mustImplement() = name.length
}

class Loud(override val name: String) : Greeter {
    override fun greet(): String = "${super.greet()}!!!"
    override fun mustImplement() = -1
}

fun main() {
    val k = Korean("준")
    println("A ${k.greet()} / ${k.shout} / ${k.mustImplement()}")
    val l = Loud("jun")
    println("B ${l.greet()} / ${l.shout} / ${l.mustImplement()}")
}
===== kotlinc greet.kt -d ogreet =====
(exit 0)
===== java -cp ogreet:kotlin-stdlib.jar GreetKt =====
A 안녕, 준 / 준 / 1
B 안녕, jun!!! / JUN / -1
(exit 0)
```

**왜 그런가**

- `A` — `Korean` 은 `name`·`mustImplement()` 만 채웠다. `greet()`·`shout` 는 **인터페이스의 기본 구현**이 돈다.
- `B` — `Loud` 는 `greet()` 를 덮고 **`super.greet()`** 로 원본을 불러 `!!!` 를 붙였다. `shout` 는 안 덮었으므로 `JUN` 이다.
- ★ **상위가 하나뿐이라 `super` 에 꺾쇠가 필요 없다.** 둘 이상이면 꺾쇠가 강제된다(4번·11번의 금지 사례).
- `shout` 는 **값을 저장하지 않는다.** `name.uppercase()` 를 부를 때마다 계산한다 — 인터페이스에는 **서랍이 없다**(2번·9번).
- ★ 인터페이스 멤버에 `open` 을 하나도 안 적었는데 `Loud` 가 덮는다 — **인터페이스 멤버는 기본이 `open`** 이다(10번).

### 2. ★★ 에러 **3 + 1 = 4건** — 전부 「서랍이 없다」의 다른 얼굴이다

**출력** — 프로퍼티 초기화·`init`·생성자

```text
===== 소스: ifacebad.kt =====
interface Config {
    val url: String = "https://example.com"

    init {
        println("인터페이스 init")
    }

    constructor(x: Int)
}
===== kotlinc ifacebad.kt -d o1 =====
ifacebad.kt:2:23: error: property initializers in interfaces are prohibited.
    val url: String = "https://example.com"
                      ^^^^^^^^^^^^^^^^^^^^^
ifacebad.kt:4:5: error: anonymous initializers in interfaces are prohibited.
    init {
    ^^^^
ifacebad.kt:8:5: error: interfaces cannot have constructors.
    constructor(x: Int)
    ^^^^^^^^^^^^^^^^^^^
(exit 1)
```

**출력** — 게터에서 `field` 를 쓰면

```text
===== 소스: ifacefield.kt =====
interface Counter {
    var count: Int
        get() = field
        set(v) { field = v }
}
===== kotlinc ifacefield.kt -d o2 =====
ifacefield.kt:2:5: error: property in interface cannot have a backing field.
    var count: Int
    ^^^^^^^^^^^^^^
(exit 1)
```

**왜 그런가**

- 문구 넷 —\
  「`property initializers in interfaces are prohibited.`」 ·\
  「`anonymous initializers in interfaces are prohibited.`」 ·\
  「`interfaces cannot have constructors.`」 ·\
  「`property in interface cannot have a backing field.`」
- ★★ 한 덩어리인 이유 — **저장할 자리(서랍)가 있으려면 그것을 채울 시점(생성자)이 있어야 한다.**\
  인터페이스는 **여럿이 동시에 구현될 수 있으므로** 「이 인터페이스의 생성자가 언제 도나」에 답이 없다. 그래서 서랍도, 초기화도, 생성자도 한꺼번에 없다.
- 그래서 인터페이스 프로퍼티에 가능한 형태는 둘뿐이다 —\
  ① **추상 선언**(`val name: String`) ② **게터만 있는 계산 프로퍼티**(`val shout: String get() = …`).
- ★ [16번 주제](../16-properties-backing-field-lateinit-const/)의 축으로 읽으면 인터페이스 프로퍼티는 **언제나** 「**필드 없는 칸**」이다. 필드가 필요하면 **구현 클래스가 갖는다**(1번의 `Korean.name`).

### 3. ★★★ 컴파일 에러 — **컴파일러가 안 고른다**

**출력**

```text
===== 소스: diamond.kt =====
interface Walker {
    fun move() = "걷는다"
}

interface Swimmer {
    fun move() = "헤엄친다"
}

class Duck : Walker, Swimmer

fun main() {
    println(Duck().move())
}
===== kotlinc diamond.kt -d o3 =====
diamond.kt:9:1: error: class 'Duck' must override 'move' because it inherits multiple interface methods for it.
class Duck : Walker, Swimmer
^^^^^^^^^^
(exit 1)
```

**왜 그런가**

- 「`class 'Duck' must override 'move' because it inherits multiple interface methods for it.`」
- ★★★ 고를 **규칙을 두지 않은 것이 설계**다. 「먼저 적은 쪽」이나 「알파벳 순」 같은 규칙을 만들면 **인터페이스 목록의 순서를 바꾸는 것만으로 동작이 바뀐다.**\
  Java 8 도 인터페이스끼리 충돌할 때 같은 결정을 했다 — **사람이 적으라.**
- 고치는 문법은 `override` + **`super<T>`** 다(4번).
- ★ 충돌한 **그 이름 하나만** 강제된다. 나머지 멤버는 그대로 상속된다(4번의 `legs()`).

### 4. ★ `걷는다 / 헤엄친다` · `2` · `헤엄친다` · 그리고 `D` 는 **양쪽이 같다**

**출력**

```text
===== 소스: diamondfix.kt =====
interface Walker {
    fun move() = "걷는다"
    fun legs(): Int = 2
}

interface Swimmer {
    fun move() = "헤엄친다"
}

class Duck : Walker, Swimmer {
    override fun move() = "${super<Walker>.move()} / ${super<Swimmer>.move()}"
}

class Fish : Swimmer

fun main() {
    println("A ${Duck().move()}")
    println("B ${Duck().legs()}")
    println("C ${Fish().move()}")
    val w: Walker = Duck()
    val s: Swimmer = Duck()
    println("D ${w.move()} / ${s.move()}")
}
===== kotlinc diamondfix.kt -d ofix =====
(exit 0)
===== java -cp ofix:kotlin-stdlib.jar DiamondfixKt =====
A 걷는다 / 헤엄친다
B 2
C 헤엄친다
D 걷는다 / 헤엄친다 / 걷는다 / 헤엄친다
(exit 0)
```

**왜 그런가**

- `A` — `super<Walker>.move()` 와 `super<Swimmer>.move()` 를 **둘 다** 불렀다. 꺾쇠 안이 **어느 계약의 절차를 쓸지** 지목하는 자리다.\
  ★ 하나만 골라도 되고 둘 다 써도 되고 아예 새로 써도 된다 — **강제되는 것은 「적는 것」이지 「고르는 것」이 아니다.**
- `B` — `legs()` 는 `Walker` 에만 있어 충돌이 없다. **아무것도 안 적어도 상속된다.**
- `C` — `Fish` 는 `Swimmer` 하나만 구현하므로 강제가 없고 기본 구현이 돈다.
- `D` — ★★ **`Walker` 로 보든 `Swimmer` 로 보든 `Duck` 의 구현이 나온다.** 선언 타입이 아니라 **객체**가 고른다(가상 디스패치).\
  ★ [13번 주제](../13-extension-functions-and-properties/)의 확장 함수였다면 **여기서 갈렸을 것**이다 — 확장은 선언 타입으로 고르므로 `Walker` 로 보면 `Walker` 용 확장이 불린다. **이 한 줄이 두 주제를 가르는 시금석**이다(12번).

### 5. ★★★ 역시 컴파일 에러다 — **Kotlin 에는 「클래스가 이긴다」가 없다**

**출력**

```text
===== 소스: clsiface.kt =====
open class Animal {
    open fun move() = "클래스 : 네 발로 간다"
}

interface Walker {
    fun move() = "인터페이스 : 걷는다"
}

class Dog : Animal(), Walker

fun main() {
    println(Dog().move())
}
===== kotlinc clsiface.kt -d o4 =====
clsiface.kt:9:1: error: class 'Dog' must override 'move' because it inherits multiple implementations for it.
class Dog : Animal(), Walker
^^^^^^^^^
(exit 1)
```

**출력** — `super<T>` 로 고치면

```text
===== 소스: clsifacefix.kt =====
open class Animal {
    open fun move() = "클래스 : 네 발로 간다"
}

interface Walker {
    fun move() = "인터페이스 : 걷는다"
}

class Dog : Animal(), Walker {
    override fun move() = "${super<Animal>.move()} + ${super<Walker>.move()}"
}

open class Cat : Animal() {
    final override fun move() = "고양이는 고양이답게"
}

fun main() {
    println("A ${Dog().move()}")
    println("B ${(Dog() as Walker).move()}")
    println("C ${Cat().move()}")
}
===== kotlinc clsifacefix.kt -d ocls =====
(exit 0)
===== java -cp ocls:kotlin-stdlib.jar ClsifacefixKt =====
A 클래스 : 네 발로 간다 + 인터페이스 : 걷는다
B 클래스 : 네 발로 간다 + 인터페이스 : 걷는다
C 고양이는 고양이답게
(exit 0)
```

**왜 그런가**

- ★ 문구가 3번과 **미묘하게 다르다.**
  - 인터페이스끼리 — 「`inherits multiple interface methods for it`」
  - 클래스 + 인터페이스 — 「`inherits multiple implementations for it`」\
  **에러 문구만 읽어도 어느 조합인지 알 수 있다.**
**출력** — 같은 모양을 Java 로 던지면

```text
===== 소스: ClassWins.java =====
class Animal {
    public String move() { return "클래스 : 네 발로 간다"; }
}

interface Walker2 {
    default String move() { return "인터페이스 : 걷는다"; }
}

public class ClassWins extends Animal implements Walker2 {
    public static void main(String[] args) {
        System.out.println("A " + new ClassWins().move());
        Walker2 w = new ClassWins();
        System.out.println("B " + w.move());
    }
}
===== javac -d ocw ClassWins.java =====
(exit 0)
===== java -cp ocw ClassWins =====
A 클래스 : 네 발로 간다
B 클래스 : 네 발로 간다
(exit 0)
```

- ★★★ Java 에서는 **조용히 컴파일되고**(`javac exit 0`) **클래스 구현이 선택된다** — `A`·`B` 둘 다 「클래스 : 네 발로 간다」다.\
  이것이 **class wins** 규칙이다. Kotlin 은 그 규칙을 **안 들였다** — 「클래스 쪽이 맞겠지」라는 짐작이 틀릴 수 있기 때문이다.
- 고친 판에서 `super<Animal>`·`super<Walker>` 둘 다 부를 수 있다 — **상위 클래스도 꺾쇠 안에 들어간다.**
- `B` — `Walker` 로 캐스팅해도 `Dog` 의 구현이 나온다(4번의 `D` 와 같은 이유).
- `C` — `final override` 로 더 아래에서 못 덮게 잠그는 것은 [19번 주제](../19-inheritance-open-final-override/)와 같다.

### 6. ★★★ **파일이 셋** 생기고, 인터페이스 메서드는 **`default`** 다

**출력**

```text
===== ls ogreet =====
GreetKt.class
Greeter$DefaultImpls.class
Greeter.class
Korean.class
Loud.class
META-INF
(exit 0)
===== javap -p ogreet/Greeter.class =====
Compiled from "greet.kt"
public interface Greeter {
  public abstract java.lang.String getName();
  public default java.lang.String getShout();
  public default java.lang.String greet();
  public abstract int mustImplement();
  public static java.lang.String access$getShout$jd(Greeter);
  public static java.lang.String access$greet$jd(Greeter);
}
(exit 0)
===== javap -p ogreet/Greeter$DefaultImpls.class =====
Compiled from "greet.kt"
public final class Greeter$DefaultImpls {
  public static java.lang.String getShout(Greeter);
  public static java.lang.String greet(Greeter);
}
(exit 0)
===== javap -p ogreet/Korean.class =====
Compiled from "greet.kt"
public final class Korean implements Greeter {
  private final java.lang.String name;
  public Korean(java.lang.String);
  public java.lang.String getName();
  public int mustImplement();
  public java.lang.String getShout();
  public java.lang.String greet();
}
(exit 0)
```

**왜 그런가**

- `ls` 가 답한다 — `Greeter.class` · **`Greeter$DefaultImpls.class`** · `Korean.class` · `Loud.class` · `GreetKt.class`(+ `META-INF`).
- ★★★ `javap` 에서 `greet()` 가 **`public default`** 다. **진짜 JVM default 메서드**다.\
  ★ 「Kotlin 인터페이스의 메서드는 `abstract` 이고 구현은 `DefaultImpls` 에 있다」는 **옛 모양**이고, 2.4.20 의 기본값에서는 **절반만 맞다**(7번).
- 그런데 `Greeter$DefaultImpls` 도 **같이** 생긴다 — 옛 컴파일러로 만든 바이너리와의 **호환용**이다.
- `Korean` 에도 `greet()`·`getShout()` 가 **있다.** 인터페이스에 default 가 있는데도 **포워딩 메서드를 따로 만든다**(7번에서 그것이 어디로 가는지 본다).
- `access$greet$jd` 는 **합성 메서드**다 — 소스에 없고 컴파일러가 만든 정적 다리다. `$jd` 는 `jvm-default` 의 약어로 읽힌다.\
  ★ **이름 규칙은 구현 세부다.** 판이 바뀌면 사라지거나 이름이 바뀔 수 있다.

### 7. 세 값이 **세 모양**을 만든다 — 그래서 플래그를 안 밝힌 주장은 반쪽이다

**출력**

```text
===== kotlinc greet.kt -jvm-default=no-compatibility -d onocompat =====
(exit 0)
===== ls onocompat =====
GreetKt.class
Greeter.class
Korean.class
Loud.class
META-INF
(exit 0)
===== javap -p onocompat/Greeter.class onocompat/Korean.class =====
Compiled from "greet.kt"
public interface Greeter {
  public abstract java.lang.String getName();
  public default java.lang.String getShout();
  public default java.lang.String greet();
  public abstract int mustImplement();
}
Compiled from "greet.kt"
public final class Korean implements Greeter {
  private final java.lang.String name;
  public Korean(java.lang.String);
  public java.lang.String getName();
  public int mustImplement();
}
(exit 0)
===== kotlinc greet.kt -jvm-default=disable -d odisable =====
(exit 0)
===== ls odisable =====
GreetKt.class
Greeter$DefaultImpls.class
Greeter.class
Korean.class
Loud.class
META-INF
(exit 0)
===== javap -p odisable/Greeter.class odisable/Korean.class =====
Compiled from "greet.kt"
public interface Greeter {
  public abstract java.lang.String getName();
  public abstract java.lang.String getShout();
  public abstract java.lang.String greet();
  public abstract int mustImplement();
}
Compiled from "greet.kt"
public final class Korean implements Greeter {
  private final java.lang.String name;
  public Korean(java.lang.String);
  public java.lang.String getName();
  public int mustImplement();
  public java.lang.String getShout();
  public java.lang.String greet();
}
(exit 0)
```

**출력** — 포워딩 메서드가 어디로 가나

```text
===== javap -c -p ogreet/Korean.class =====
Compiled from "greet.kt"
public final class Korean implements Greeter {
  private final java.lang.String name;

  public Korean(java.lang.String);
    Code:
       0: aload_1
       1: ldc           #11                 // String name
       3: invokestatic  #17                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_0
       7: invokespecial #20                 // Method java/lang/Object."<init>":()V
      10: aload_0
      11: aload_1
      12: putfield      #23                 // Field name:Ljava/lang/String;
      15: return

  public java.lang.String getName();
    Code:
       0: aload_0
       1: getfield      #23                 // Field name:Ljava/lang/String;
       4: areturn

  public int mustImplement();
    Code:
       0: aload_0
       1: invokevirtual #31                 // Method getName:()Ljava/lang/String;
       4: invokevirtual #36                 // Method java/lang/String.length:()I
       7: ireturn

  public java.lang.String getShout();
    Code:
       0: aload_0
       1: invokespecial #39                 // InterfaceMethod Greeter.getShout:()Ljava/lang/String;
       4: areturn

  public java.lang.String greet();
    Code:
       0: aload_0
       1: invokespecial #42                 // InterfaceMethod Greeter.greet:()Ljava/lang/String;
       4: areturn
}
(exit 0)
===== javap -c -p odisable/Korean.class =====
Compiled from "greet.kt"
public final class Korean implements Greeter {
  private final java.lang.String name;

  public Korean(java.lang.String);
    Code:
       0: aload_1
       1: ldc           #11                 // String name
       3: invokestatic  #17                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_0
       7: invokespecial #20                 // Method java/lang/Object."<init>":()V
      10: aload_0
      11: aload_1
      12: putfield      #23                 // Field name:Ljava/lang/String;
      15: return

  public java.lang.String getName();
    Code:
       0: aload_0
       1: getfield      #23                 // Field name:Ljava/lang/String;
       4: areturn

  public int mustImplement();
    Code:
       0: aload_0
       1: invokevirtual #31                 // Method getName:()Ljava/lang/String;
       4: invokevirtual #36                 // Method java/lang/String.length:()I
       7: ireturn

  public java.lang.String getShout();
    Code:
       0: aload_0
       1: invokestatic  #42                 // Method Greeter$DefaultImpls.getShout:(LGreeter;)Ljava/lang/String;
       4: areturn

  public java.lang.String greet();
    Code:
       0: aload_0
       1: invokestatic  #45                 // Method Greeter$DefaultImpls.greet:(LGreeter;)Ljava/lang/String;
       4: areturn
}
(exit 0)
```

**왜 그런가**

| `-jvm-default` | 인터페이스의 `greet()` | `DefaultImpls` | 구현 클래스 `Korean` |
|---|---|---|---|
| `enable` (**기본값**) | `public default` | **생긴다** | `greet()` 있음 → `invokespecial` 로 인터페이스 default 호출 |
| `no-compatibility` | `public default` | **안 생긴다** | **`greet()` 자체가 없다** |
| `disable` | `public abstract` | **생긴다** | `greet()` 있음 → `invokestatic Greeter$DefaultImpls.greet(LGreeter;)` |

- ★★ **소스는 한 글자도 안 바뀌었다.** 플래그 하나로 클래스 파일의 모양이 통째로 갈린다.
- `invokespecial … InterfaceMethod Greeter.greet` 는 **`super` 호출**이다 — JVM 의 default 메서드를 직접 부른다.
- `invokestatic … Greeter$DefaultImpls.greet(LGreeter;)` 는 **자기 자신을 첫 인자로 넘기는 정적 호출**이다. 몸통이 인터페이스 밖에 있으므로 그렇게 할 수밖에 없다.
- `no-compatibility` 에서 `Korean` 에 `greet()` 가 아예 없는 것은 **JVM 의 인터페이스 메서드 해소에 그냥 맡긴다**는 뜻이다 — 가장 깔끔하지만 **옛 바이너리와의 호환을 버린다.**
- ★ 「`DefaultImpls` 가 생긴다」는 지식은 **지금도 맞지만 이유가 바뀌었다** — 예전에는 **구현을 담는 유일한 자리**였고 지금은 **호환용 사본**이다.

### 8. ★★ 기본값이면 Java 가 그냥 물려받고, `disable` 이면 **에러 3건**이다

**출력** — 기본값으로 컴파일한 인터페이스

```text
===== 소스: JavaGreeter.java =====
public class JavaGreeter implements Greeter {
    public String getName() { return "java"; }
    public int mustImplement() { return 0; }

    public static void main(String[] args) {
        JavaGreeter g = new JavaGreeter();
        System.out.println("A " + g.greet());
        System.out.println("B " + g.getShout());
    }
}
===== javac -cp ogreet:kotlin-stdlib.jar -d ojava JavaGreeter.java =====
(exit 0)
===== java -cp ojava:ogreet:kotlin-stdlib.jar JavaGreeter =====
A 안녕, java
B JAVA
(exit 0)
```

**출력** — `-jvm-default=disable` 로 컴파일한 인터페이스

```text
===== javac -cp odisable:kotlin-stdlib.jar -d ojava2 JavaGreeter.java =====
JavaGreeter.java:1: error: JavaGreeter is not abstract and does not override abstract method greet() in Greeter
public class JavaGreeter implements Greeter {
       ^
JavaGreeter.java:7: error: cannot find symbol
        System.out.println("A " + g.greet());
                                   ^
  symbol:   method greet()
  location: variable g of type JavaGreeter
JavaGreeter.java:8: error: cannot find symbol
        System.out.println("B " + g.getShout());
                                   ^
  symbol:   method getShout()
  location: variable g of type JavaGreeter
3 errors
(exit 1)
```

**왜 그런가**

- ★★★ **`JavaGreeter.java` 는 한 글자도 안 바뀌었다.** 바뀐 것은 **인터페이스를 어느 플래그로 컴파일했느냐**뿐이다.
- 기본값에서는 인터페이스에 `default` 메서드가 있으므로 Java 가 **그냥 물려받는다** — `javac exit 0`, 실행하면 `안녕, java` / `JAVA`.
- `disable` 에서는 인터페이스 메서드가 `abstract` 라 Java 클래스가 **구현하지 않은 것**이 된다 —\
  「`JavaGreeter is not abstract and does not override abstract method greet() in Greeter`」 하나와 「`cannot find symbol`」 둘.
- ★ **Java 에서 `DefaultImpls` 의 정적 메서드는 「그 인터페이스의 메서드」가 아니다.** 부르려면 `Greeter.DefaultImpls.greet(this)` 라고 **직접 적어야** 한다.
- ★★ 그래서 2.2 의 기본값 변경은 **Java 상호운용을 위한 것**이었다 — 이 두 블록이 그 이유 전부다.

### 9. **저장할 자리가 있으려면 채울 시점이 있어야** 한다

**왜 그런가**

- 서랍(backing field)은 **어딘가에서 한 번 채워져야** 뜻이 있다. 클래스는 **생성자**가 그 시점이다.
- 인터페이스는 셋이든 넷이든 **겹쳐 입을 수 있다.** 그런데 인터페이스에 생성자가 있다면 —\
  세 인터페이스를 구현한 클래스에서 **세 생성자가 언제 어느 순서로 돌아야 하는가**에 답이 없다.\
  ★ C++ 의 다중 상속이 이 답을 만들려다 복잡해진 자리이고, Java·Kotlin 은 **아예 상태를 금지**해 문제를 없앴다.
- 그래서 [16번 주제](../16-properties-backing-field-lateinit-const/)의 축(필드 유무)에서 인터페이스 프로퍼티는 **언제나 「필드 없음」 칸**이다.\
  필드가 필요하면 **구현 클래스가 `override val` 로 갖는다** — 그때 서랍은 인터페이스가 아니라 **그 클래스**의 것이다.
- ★ 반대로 **`init` 이 없다는 것**은 「**인터페이스는 초기화 순서에 참여하지 않는다**」는 뜻이기도 하다 — [15번 주제](../15-class-declaration-constructors-and-init/)의 초기화 순서 표에 인터페이스가 안 나오는 이유다.

### 10. 인터페이스 멤버는 **기본이 `open`** 이다 — 클래스와 정반대다

**왜 그런가**

- 인터페이스 멤버에 `open` 을 적을 필요가 **없다.** 1번의 `Greeter` 에는 `open` 이 하나도 없는데 `Loud` 가 `greet()` 를 덮었다.
- [19번 주제](../19-inheritance-open-final-override/)의 클래스 멤버는 **기본이 `final`** 이라 `open` 을 적어야 했다. **정확히 반대**다.
- ★ 왜 반대인가 — 인터페이스는 「**구현되라고 있는 것**」이다. 기본을 닫으면 존재 이유와 모순된다.
- 인터페이스 멤버를 `final` 로 잠글 수는 **없다.** 잠그는 것은 **구현 클래스 쪽에서** `final override` 로 한다(5번의 `Cat`).
- ★ 그래서 「기본값을 뒤집었다」는 19번의 이야기는 **클래스에만 해당**한다. 이 언어 전체가 닫혀 있는 것이 아니다.

### 11. ★ `private fun` 도 `companion object` 도 되는데 `init` 만 안 된다

**출력**

```text
===== 소스: form20.kt =====
interface Named {
    val name: String
    val upper: String
        get() = name.uppercase()

    fun hello(): String = "hi " + decorate(name)
    fun must(): Int

    private fun decorate(s: String) = "<$s>"

    companion object {
        const val TAG = "Named"
    }
}

class Impl(override val name: String) : Named {
    override fun must() = name.length
}

fun main() {
    val i = Impl("kim")
    println("Z ${i.hello()} ${i.upper} ${i.must()} ${Named.TAG}")
}
===== kotlinc form20.kt -d oform =====
(exit 0)
===== java -cp oform:kotlin-stdlib.jar Form20Kt =====
Z hi <kim> KIM 3 Named
(exit 0)
```

**출력** — 금지 사례

```text
===== 소스: forbid20.kt =====
interface Walker {
    fun move(): String = "걷는다"
}

interface Swimmer {
    fun move(): String = "헤엄친다"
}

val w = Walker()

class Both : Walker, Swimmer {
    override fun move() = super.move()
}
===== kotlinc forbid20.kt -d oforbid =====
forbid20.kt:9:9: error: interface 'interface Walker : Any' does not have constructors.
val w = Walker()
        ^^^^^^
forbid20.kt:12:27: error: multiple supertypes available. Specify the intended supertype in angle brackets, e.g. 'super<Foo>'.
    override fun move() = super.move()
                          ^^^^^
(exit 1)
```

**왜 그런가**

- `private fun decorate` 는 **된다.** 몸통이 있고 그 인터페이스 안에서만 쓰이는 도우미다 — **상태가 아니므로** 금지 이유가 없다.
- `companion object` 도 **된다.** `const val TAG` 는 **인스턴스 상태가 아니라 정적 상수**다 — 역시 「채울 시점」 문제가 없다.
- `init` 만 안 되는 이유는 **인스턴스 초기화 시점을 요구하기 때문**이다(9번). `private fun` 과 `companion object` 는 그 시점을 요구하지 않는다.\
  ★ **가르는 선은 「몸통이 있느냐」가 아니라 「인스턴스가 만들어질 때 무언가 해야 하느냐」이다.**
- 금지 사례 둘 —
  - 「`interface 'interface Walker : Any' does not have constructors.`」 — **인터페이스는 인스턴스를 못 만든다.** (문구에 `: Any` 가 붙은 것도 볼 만하다 — [19번 주제](../19-inheritance-open-final-override/)의 「모든 것이 `Any` 를 상속한다」가 여기서도 보인다.)
  - 「`multiple supertypes available. Specify the intended supertype in angle brackets, e.g. 'super<Foo>'.`」 — 상위가 둘 이상이면 **`super` 에 꺾쇠가 강제**된다. 1번에서 꺾쇠가 없어도 됐던 것은 상위가 하나였기 때문이다.

### 12. 네 갈래 — **디스패치 · 상태 · 계층 · 소유권**으로 갈린다

**왜 그런가**

| 갈래 | 디스패치 | 상태를 가질 수 있나 | 계층이 생기나 | 남의 타입에 쓸 수 있나 |
|---|---|---|---|---|
| **인터페이스**(20번) | 가상 | 못 가진다 | 생긴다(다중) | 못 쓴다(그 타입을 고쳐야 한다) |
| **추상 클래스**(19번) | 가상 | 가진다 | 생긴다(단일) | 못 쓴다 |
| **확장 함수**([13번](../13-extension-functions-and-properties/)) | **정적** | 못 가진다 | 안 생긴다 | **쓴다** |
| **위임**([21번](../21-class-delegation-by/)) | 가상 | 위임 대상이 가진다 | 안 생긴다(합성) | 못 쓴다 |

- 4번의 `D` 줄을 확장 함수로 바꾸면 — **선언 타입이 고르게 된다.** `val w: Walker = Duck()` 에서 `w.move()` 는 `Walker` 용 확장이 불리고 `Duck` 의 것은 **안 불린다.**\
  ★ 충돌 자체가 **컴파일 에러가 아니라 조용한 오답**이 된다. 3번·5번의 에러가 애초에 안 난다.
- [21번 주제](../21-class-delegation-by/)의 위임이 대신해 주는 것은 「**인터페이스를 구현하기 위해 메서드를 전부 적는 일**」이다 — 계약은 그대로 두고 **구현을 남에게 맡긴다.**
- 한 줄 기준 —
  - **인터페이스** — 여럿이 같은 계약을 서로 다르게 이행해야 한다.
  - **추상 클래스** — 공통 **상태**까지 물려줘야 한다.
  - **확장 함수** — 남의 타입에 붙이고, 갈라질 일이 없다.
  - **위임** — 계약은 필요한데 **계층을 만들고 싶지 않다.**

## 실행 검증

```text
===== kotlinc -version =====
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
(exit 0)
===== java -version =====
openjdk version "21.0.5" 2024-10-15 LTS
OpenJDK Runtime Environment Temurin-21.0.5+11 (build 21.0.5+11-LTS)
OpenJDK 64-Bit Server VM Temurin-21.0.5+11 (build 21.0.5+11-LTS, mixed mode, sharing)
(exit 0)
===== javac -version =====
javac 21.0.5
(exit 0)
```

★ **흔들리는 칸과 안 흔들리는 칸**(제출 전 재대조에서 「고칠 것」과 「설계상 다른 것」을 가르는 선언이다)

| 흔들린다 | 안 흔들린다 |
|---|---|
| **없다** — 이 주제에는 해시코드·시간·스레드 순서를 싣지 않았다 | 컴파일 에러의 **문구·`파일:줄:칸`·캐럿 줄** |
| | `javap` 출력 **전체**(상수 풀 번호 `#39`·오프셋·선언 순서) |
| | `ls` 가 찍은 **파일 목록과 그 순서** |
| | 모든 **종료 코드** · `println` 출력 |

> 근거 — 캡처 스크립트를 처음부터 두 번 돌려 **블록 95개(실행 52 + 소스 43)를 바이트 단위로 대조**했고, **달라진 파일은 0개**였다.

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `greet.kt` | `A`·`B` — 기본 구현 · 계산 프로퍼티 · `super.greet()` | `kotlinc` → `java` |
| `greet.kt` (기본 플래그) | ★★★ **`default` 메서드 + `DefaultImpls` + `access$…$jd`** | `ls` · `javap -p` 3회 · `javap -c` |
| `greet.kt` (`no-compatibility`) | `DefaultImpls` **안 생김** · `Korean` 에 포워딩 **없음** | `kotlinc` → `ls` · `javap -p` |
| `greet.kt` (`disable`) | 인터페이스가 **`abstract`** · 포워딩이 `invokestatic` | `kotlinc` → `ls` · `javap -p` · `javap -c` |
| `ifacebad.kt` · `ifacefield.kt` | 금지 **4건** — 초기화·`init`·생성자·`field` | `kotlinc` 2회 (컴파일 실패가 결과) |
| `diamond.kt` · `diamondfix.kt` | 인터페이스끼리 충돌 → `super<T>` 해소 | `kotlinc` 2회 → `java` |
| `clsiface.kt` · `clsifacefix.kt` | ★★ 클래스 + 인터페이스 충돌 — **class wins 가 없다** | `kotlinc` 2회 → `java` |
| `ClassWins.java` | ★★ **Java 에서는 같은 모양이 조용히 컴파일되는 것** | `javac` → `java` |
| `JavaGreeter.java` | ★★ 같은 Java 파일이 **플래그에 따라 갈리는 것** | `javac` 2회(1벌 실패) → `java` |
| `form20.kt` | `private fun`·`companion object`·계산 프로퍼티가 도는 것(`Z`) | `kotlinc` → `java` |
| `forbid20.kt` | 인스턴스화 금지 · `super` 꺾쇠 강제 | `kotlinc` (컴파일 실패가 결과) |

**구현 의존 항목** — `DefaultImpls` 라는 **이름**과 그 존재, `access$greet$jd` 라는 합성 메서드,
`invokespecial`/`invokestatic` 중 무엇을 쓰는가, 상수 풀 번호, `-jvm-default` 의 **기본값이 `enable` 인 것**,
에러 메시지의 문구 — **전부 이 컴파일러 판의 산출물**이다.\
반면 **「인터페이스는 기본 구현을 가질 수 있다」·「상태를 못 가진다」·「같은 시그니처 충돌은 `override` 가 강제된다」·
「`super<T>` 로 고른다」·「클래스가 인터페이스를 이기지 않는다」·「인터페이스 멤버는 기본이 `open`」**
는 **언어의 계약**이다.

**★ 던져 봤더니 예상과 달랐던 것 — 세 건**

1. ★★★ **「Kotlin 인터페이스 메서드는 `abstract` 이고 구현은 `DefaultImpls` 에 있다」가 이제 틀렸다.**
   2.4.20 의 기본값에서는 **인터페이스에 진짜 `default` 메서드가 들어간다**(6번). 이 문서를 쓰기 전의 전제가
   **관찰로 뒤집혔다** — `javap` 를 안 찍고 옛 지식을 옮겨 적었으면 그대로 틀린 문서가 됐을 것이다.
2. ★★ **`DefaultImpls` 가 사라진 것이 아니라 둘이 공존한다.** 「default 메서드가 나오면 `DefaultImpls` 는 안 생기겠지」라고
   예상했는데 **둘 다 생긴다.** 없애려면 `-jvm-default=no-compatibility` 를 **명시**해야 한다(7번).
3. ★★ **구현 클래스에 포워딩 메서드가 여전히 생긴다.** 인터페이스에 default 가 있으면 `Korean` 은 비어 있을 줄 알았는데
   `greet()`·`getShout()` 가 **둘 다 있다**(6번). 정말로 비는 것은 `no-compatibility` 판뿐이다 —
   **「default 메서드가 생겼다」와 「구현 클래스가 비었다」는 다른 이야기**다.

**안 터진 것도 출력이다** — `diamondfix.kt` 의 `Fish` 는 `Swimmer` 하나만 구현하는데 **아무 경고도 없다.**
충돌이 없으면 강제도 없다는 것을, 컴파일러는 **아무 말도 하지 않음으로써** 말한다.
같은 이유로 `legs()` 도 조용히 상속된다 — **「무엇이 강제되지 않는가」를 확인하는 것도 실험의 절반**이다.
