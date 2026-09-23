# kotlin/syntax/20 — 인터페이스: 기본 구현·프로퍼티 선언·충돌 해소(`super<T>`) — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Interfaces](https://kotlinlang.org/docs/interfaces.html) · [Inheritance — Overriding rules](https://kotlinlang.org/docs/inheritance.html) · [Java interop — Default methods](https://kotlinlang.org/docs/java-to-kotlin-interop.html) · [Compiler options — `-jvm-default`](https://kotlinlang.org/docs/compiler-reference.html).
> **실행 검증** — 이 문서의 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 에서 실제로 얻었다.\
> `kotlinc` 11회(컴파일 실패 5벌) · `javac` 3회(실패 1벌) · `java` 6회 · `javap` 7회 · `ls` 3회.\
> ★★ 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적지 않았다.
> ⚠️ **`-jvm-target` 을 밝히지 않은 바이트코드 주장은 반쪽이다.** 이 문서의 역어셈블은 전부 **기본값 1.8**(`major version: 52`)이고,\
> ★★★ **`-jvm-default` 도 같이 밝혀야 한다** — 이 플래그 하나로 인터페이스의 클래스 파일 **모양이 통째로 달라진다**((5)).
> **버전** — 인터페이스의 기본 구현·프로퍼티 선언·`super<T>` 는 전부 **1.0** 이다.\
> ★ 그러나 **그것이 바이트코드로 내려가는 방식은 2.2 에서 바뀌었다** — `-jvm-default` 의 기본값이 `enable` 이 되어 **진짜 JVM `default` 메서드**가 나온다((5)).
> **경계** — `open`/`override` 규칙은 [19번 주제](../19-inheritance-open-final-override/), 프로퍼티의 backing field 는 [16번 주제](../16-properties-backing-field-lateinit-const/),\
> 위임으로 계층을 피하는 길은 [21번 주제](../21-class-delegation-by/), `sealed interface` 와 `when` 완결성은 목록의 **23번 주제**가 정본이다.\
> Java 쪽 짝은 [`../../../java/syntax/11-interfaces-default-methods/`](../../../java/syntax/11-interfaces-default-methods/) — 거기는 **Java 8 이 왜 `default` 를 들였나**, 여기는 **Kotlin 이 그 위에서 무엇을 더 했나**.
> 이 본문은 Claude 작성이다(원고 없음).

★ **흔들리는 칸 / 안 흔들리는 칸** — 제출 전 재대조에서 「고칠 것」과 「설계상 다른 것」을 가르는 선언이다.

| 흔들린다 | 안 흔들린다 |
|---|---|
| (이 주제에는 없다 — 해시코드·시간을 싣지 않았다) | 컴파일 에러의 **문구·`파일:줄:칸`** |
| | `javap` 출력 **전체**(상수 풀 번호·오프셋 포함) · `ls` 가 찍은 **파일 목록** |
| | 모든 **종료 코드** · `println` 출력 |

> 근거 — 캡처 스크립트를 두 번 돌려 **블록 95개(실행 52 + 소스 43)를 바이트 단위로 대조**했다(전체 결과는 3-answer 의 「실행 검증」).

## 한눈에 — 쉽게 말하면

**인터페이스는 「상태 없는 계약」이다 — 여럿을 겹쳐 입을 수 있는 대신 서랍을 못 가진다.**

[19번 주제](../19-inheritance-open-final-override/)의 클래스는 **하나만** 상속할 수 있었다. 대신 상태(필드)를 가진다.\
인터페이스는 **여럿을 구현**할 수 있다. 대신 **상태를 가질 수 없다.**

> **backing field(뒷받침 필드)** — 프로퍼티 값이 실제로 들어가는 서랍.\
> 예: `val x = 1` 은 서랍이 있고, `val x get() = 1` 은 **서랍 없이 계산해서** 준다. 정본은 [16번 주제](../16-properties-backing-field-lateinit-const/)다.

비유는 문서 끝까지 이것 하나로 고정한다 — **자격증**이다.

| 비유 | 실체 |
|---|---|
| 자격증은 여러 장 딸 수 있다 | 인터페이스는 여럿 구현 가능 |
| 본적(本籍)은 하나뿐이다 | 클래스는 하나만 상속 |
| 자격증에는 「이건 이렇게 하세요」라는 표준 절차가 적혀 있다 | 기본 구현 |
| 자격증은 **짐을 들고 다니지 못한다** | backing field 없음 |
| 자격증마다 절차가 다르면 본인이 정해야 한다 | 같은 시그니처 충돌 → `override` 강제 |
| 「1급 자격증 절차로 하겠습니다」 | `super<Walker>.move()` |
| 본적이 자격증보다 세지 않다 | 클래스와 인터페이스가 충돌해도 **똑같이 강제**된다 |

```text
   interface Greeter                        class Korean : Greeter
   +---------------------------------+      +------------------------------+
   | val name          (구현 없음)   |----->| override val name  <- 서랍은  |
   | val shout  get() = …  (구현 O)  |      |                       여기 있다|
   | fun greet()      = …  (구현 O)  |      | override fun must…            |
   | fun mustImplement()  (구현 없음)|      | (greet·shout 는 안 적어도 된다)|
   +---------------------------------+      +------------------------------+
         구현은 있는데 서랍이 없다               서랍은 구현 클래스가 가진다
```

「**구현은 줄 수 있는데 상태는 못 준다**」가 이 주제의 절반이고, 나머지 절반은 「**겹쳐 입었을 때 누가 이기나**」이다.

## 이 주제가 답하려는 질문

1. 인터페이스가 **줄 수 있는 것과 못 주는 것**은 각각 무엇인가 — 구현은? 프로퍼티는? 상태는?
2. 같은 시그니처를 **둘에서** 상속하면 컴파일러가 무엇을 요구하나.
3. 그 기본 구현은 **JVM 에서 무엇이 되나** — Java 에서 그대로 보이나.

## 동작 방식

### (1) 기본 구현과 프로퍼티 — 구현 클래스가 채우는 것과 안 채워도 되는 것

**언제 쓰나** — 계약을 정의하면서 대부분의 구현자가 쓸 기본 동작을 같이 주고 싶을 때.

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

```text
   Greeter
     val name            abstract   -> 구현 클래스가 반드시 채운다
     val shout   get()=… 기본 구현  -> 안 채우면 이것이 돈다
     fun greet() = …     기본 구현  -> Loud 는 덮고 super 로 불러 쓴다
     fun mustImplement() abstract   -> 반드시 채운다
        |
        +-- Korean  : name·mustImplement 만 채웠다 -> A 줄
        +-- Loud    : greet 도 덮고 super.greet() 를 부른다 -> B 줄
```

- `A` — `Korean` 은 `greet()`·`shout` 를 안 적었는데 **인터페이스의 구현이 돈다.**
- `B` — `Loud` 는 `greet()` 를 덮고 **`super.greet()`** 로 원본을 불러 앞에 붙였다.\
  ★ 상위가 하나뿐일 때는 **`super` 에 꺾쇠가 필요 없다.** 둘 이상이면 (3)처럼 꺾쇠가 강제된다.
- `shout` 는 **게터만 있는 프로퍼티**다 — 값을 저장하지 않고 `name` 에서 계산한다.
- ★ 인터페이스의 프로퍼티는 **「선언」이지 「저장」이 아니다**((2)).

### (2) ★★ 인터페이스에는 **서랍이 없다** — 초기화도 `init` 도 생성자도 없다

**언제 쓰나** — 인터페이스에 상태를 두려다 막힐 때. 「왜 안 되지?」의 답이 여기 있다.

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

```text
   interface Config                       class Impl : Config
   +-----------------------------+        +---------------------------+
   | val url = "…"      금지     |        | override val url = "…"    |
   | init { … }         금지     |        |      <- 서랍은 여기 있다   |
   | constructor(x)     금지     |        +---------------------------+
   | var count; get() = field 금지|
   +-----------------------------+
      서랍(field)·초기화 시점·생성자가 전부 없다 — 셋은 한 덩어리다
```

- 에러 넷이 **같은 사실의 네 얼굴**이다 — 프로퍼티 초기화, `init` 블록, 생성자, 그리고 `field` 키워드.
- ★★ 왜 한 덩어리인가 — **저장할 자리가 있으려면 그것을 채울 시점(생성자)이 있어야** 한다.\
  인터페이스는 여럿 구현될 수 있으므로 「**이 인터페이스의 생성자가 언제 도나**」에 답이 없다.
- ★ 그래서 인터페이스 프로퍼티는 **추상 선언**이거나 **게터만 있는 계산 프로퍼티**뿐이다.\
  서랍의 정본은 [16번 주제](../16-properties-backing-field-lateinit-const/)다 — 거기서 「필드 있는 프로퍼티 / 없는 프로퍼티」를 갈랐고, **인터페이스는 항상 뒤쪽**이다.
- ★ 「`private fun` 은 되나?」는 된다 — **몸통이 있는 `private` 메서드**는 인터페이스에 둘 수 있다(아래 「문법」의 `decorate`).

### (3) ★★★ 같은 시그니처를 둘에서 상속하면 — **컴파일러가 거부한다**

**언제 쓰나** — 인터페이스를 여럿 겹쳐 입을 때. 이 주제의 본체다.

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

```text
   interface Walker          interface Swimmer
     fun move() = "걷는다"     fun move() = "헤엄친다"
            \                    /
             \                  /
            class Duck : Walker, Swimmer      <- 어느 쪽을 쓸 것인가?
                                                 컴파일러는 안 고른다
```

- 「`class 'Duck' must override 'move' because it inherits multiple interface methods for it.`」\
  ★★ **컴파일러가 규칙으로 하나를 고르지 않는다.** Java 8 도 같은 자리에서 같은 결정을 했다 — **사람이 적으라**는 것이다.
- 고치는 형태가 `super<T>` 다.

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

- `A` — `super<Walker>.move()` 와 `super<Swimmer>.move()` 를 **둘 다** 불러 이었다. 꺾쇠 안이 **어느 계약의 절차인지** 고르는 자리다.
- `B` — 충돌하지 않는 `legs()` 는 **아무것도 안 적어도** 그대로 상속된다. **충돌한 이름만** 강제된다.
- `C` — `Fish` 는 `Swimmer` 만 구현하므로 강제가 없다.
- `D` — `Walker` 타입으로 보든 `Swimmer` 타입으로 보든 **`Duck` 의 구현이 나온다.** 선언 타입이 아니라 **객체**가 고른다(가상 디스패치).\
  ★ [13번 주제](../13-extension-functions-and-properties/)의 확장 함수였다면 **여기서 갈렸을 것**이다 — 확장은 선언 타입으로 고른다.

### (4) ★★ 클래스와 인터페이스가 부딪치면 — **클래스가 이기지 않는다**

**언제 쓰나** — 상위 클래스가 이미 가진 메서드를 인터페이스도 기본 구현으로 갖고 있을 때.

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

- 문구가 (3)과 **미묘하게 다르다** — `multiple interface methods` 가 아니라 「`multiple implementations`」다.\
  ★ **에러 문구가 어느 조합인지 말해 준다** — 인터페이스끼리면 앞엣것, 클래스가 끼면 뒤엣것.
- ★★★ **Java 의 「클래스가 인터페이스를 이긴다(class wins)」 규칙이 Kotlin 에는 없다.**\
  같은 모양을 Java 로 그대로 던져 보면 **조용히 컴파일되고 클래스 구현이 선택된다.**

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

- Java 쪽은 `javac exit 0` 이고 `A`·`B` 둘 다 **클래스 구현**이 나온다 — 인터페이스 타입으로 봐도 그렇다.\
  Kotlin 은 같은 자리에서 **거부하고 사람에게 묻는다.**

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

- `A` — `super<Animal>` 과 `super<Walker>` 로 둘 다 부를 수 있다. **상위 클래스도 꺾쇠 안에 들어간다.**
- `B` — `Walker` 타입으로 캐스팅해도 `Dog` 의 구현이 나온다.
- `C` — `final override` 로 잠그는 것은 [19번 주제](../19-inheritance-open-final-override/)와 같다.

### (5) ★★★ 기본 구현은 JVM 에서 무엇이 되나 — **`-jvm-default` 가 세 모양을 만든다**

**언제 쓰나** — Java 에서 그 인터페이스를 구현할 때. 그리고 「`DefaultImpls` 가 생긴다」는 옛 지식을 확인할 때.

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

- ★★★ **인터페이스에 진짜 `default` 메서드가 있다.** `public default java.lang.String greet();` 이다.\
  ★ **「Kotlin 인터페이스의 메서드는 `abstract` 이고 구현은 `DefaultImpls` 에 있다」는 옛 모양이고, 2.4.20 의 기본값에서는 절반만 맞다.**
- 그런데 **`Greeter$DefaultImpls` 도 같이 생긴다.** 옛 컴파일러로 만든 코드와의 호환을 위한 것이다.
- `access$greet$jd` 라는 **정적 다리**도 생긴다.

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

```text
   -jvm-default=      인터페이스의 greet()      DefaultImpls 클래스   구현 클래스 Korean
   -----------------  ------------------------  -------------------  ---------------------
   enable (기본값)    public default            생긴다               greet() 포워딩이 있다
   no-compatibility   public default            안 생긴다            greet() 가 아예 없다
   disable            public abstract           생긴다               greet() 포워딩이 있다
```

- ★★ 세 모양이 **소스 한 글자 안 바꾸고** 플래그 하나로 갈린다. 그래서 **플래그를 안 밝힌 바이트코드 주장은 반쪽**이다.
- 포워딩이 어디로 가는지도 갈린다.

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

- 기본값에서는 `invokespecial … InterfaceMethod Greeter.greet` — **JVM 의 default 메서드를 `super` 호출**한다.
- `disable` 에서는 `invokestatic … Greeter$DefaultImpls.greet(LGreeter;)` — **정적 메서드에 자기를 넘긴다.**
- ★ `no-compatibility` 에서는 `Korean` 에 `greet()` 자체가 없다 — **JVM 의 인터페이스 default 메서드 해소에 그냥 맡긴다.**

### (6) ★★ Java 에서 구현하면 — 기본값에서는 그대로 보이고 `disable` 에서는 안 보인다

**언제 쓰나** — Kotlin 인터페이스를 Java 클래스가 구현할 때. Spring·라이브러리 경계에서 실제로 마주친다.

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

```text
   같은 JavaGreeter.java 를 두 번 컴파일했다
   +-------------------------------+   +--------------------------------------+
   | 인터페이스를 기본값으로 컴파일 |   | 인터페이스를 -jvm-default=disable 로 |
   | javac exit 0                  |   | javac exit 1 — 에러 3건              |
   | A 안녕, java / B JAVA         |   | "does not override abstract method"  |
   +-------------------------------+   +--------------------------------------+
```

- ★★★ **Java 클래스는 하나도 안 바뀌었다.** 바뀐 것은 **인터페이스를 어느 플래그로 컴파일했느냐**뿐인데 한쪽은 돌고 한쪽은 컴파일이 안 된다.
- `disable` 쪽 에러가 세 건인 것에 주목하라 — 「구현하지 않았다」 하나와 「그런 메서드가 없다」 둘.\
  ★ **Java 에서 보면 `DefaultImpls` 의 정적 메서드는 「그 인터페이스의 메서드」가 아니다.** 직접 `Greeter.DefaultImpls.greet(this)` 라고 적어야 부를 수 있다.
- ★ 그래서 Kotlin 2.2 의 기본값 변경은 **Java 상호운용을 위한 것**이다 — Java 구현자가 Kotlin 인터페이스의 기본 구현을 **그냥 물려받게** 되었다.

## 문법 — 형태와 규칙

**형태** — 추상 멤버·계산 프로퍼티·기본 구현·`private` 메서드·`companion object` 가 한 인터페이스에서 전부 도는 예제다.

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

**금지 사례**

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

**규칙 불릿**

- 인터페이스는 **몸통 있는 메서드**를 가질 수 있다(기본 구현).
- 인터페이스는 **상태를 못 가진다** — 프로퍼티 초기화·`init`·생성자·`field` 가 전부 금지다((2)).
- 인터페이스 프로퍼티는 **추상 선언**이거나 **게터만 있는 계산 프로퍼티**다.
- 인터페이스는 **인스턴스를 못 만든다**(「`does not have constructors`」).
- 상위를 구현할 때 **괄호가 없다** — `class C : Walker` (클래스는 `class C : Base()`).
- 같은 시그니처가 **둘 이상**에서 오면 `override` 가 **강제**되고 `super<T>` 로 고른다((3)·(4)).
- 상위가 하나면 `super.f()` 로 충분하고, 둘 이상이면 **꺾쇠가 강제**된다(「`multiple supertypes available`」).
- 인터페이스 멤버는 **기본이 `open`** 이다 — [19번 주제](../19-inheritance-open-final-override/)의 클래스와 정반대다. `open` 을 적을 필요가 없다.
- `private fun` 은 **몸통이 있으면** 둘 수 있다. `companion object` 도 둘 수 있다.

## 어디서 틀리나

1. ★★★ 「**`DefaultImpls` 가 생기고 인터페이스 메서드는 `abstract` 다**」 — **2.2 부터 기본값이 바뀌었다**((5)).\
   지금은 `default` 메서드가 나오고 `DefaultImpls` 는 **호환용으로 같이** 생긴다. 옛 블로그를 그대로 믿으면 틀린다.
2. ★★★ **Java 의 「클래스가 이긴다」 규칙을 기대한다.** Kotlin 에는 없다 — **컴파일 에러**다((4)).
3. ★★ **인터페이스에 상태를 두려 한다.** 프로퍼티는 선언할 수 있으므로 **될 것처럼 보인다** — 초기화하는 순간 막힌다((2)).
4. ★★ **`super.f()` 를 꺾쇠 없이 쓴다.** 상위가 둘 이상이면 「`multiple supertypes available`」이다.
5. ★ **충돌하지 않는 멤버까지 다시 적는다.** 강제되는 것은 **같은 시그니처가 겹친 것만**이다((3)의 `legs()`).
6. ★ **`-jvm-default` 를 안 밝히고 바이트코드를 말한다.** 세 모양이 전부 다르다((5)).
7. ★ **인터페이스 멤버에 `open` 을 적는다.** 불필요하다 — 기본이 열려 있다.
8. ★ **`DefaultImpls` 를 Java 에서 직접 부르려 한다.** 가능하지만 **API 가 아니다** — 컴파일러 판이 바뀌면 사라질 수 있다(`no-compatibility` 에서는 이미 없다).

## 구현 세부사항 대 언어 보장

| 항목 | 어느 쪽인가 | 근거 |
|---|---|---|
| 인터페이스가 기본 구현을 가질 수 있는 것 | **언어 보장** | (1) |
| 상태를 못 가지는 것(초기화·`init`·생성자·`field` 금지) | **언어 보장** | (2) |
| 같은 시그니처 충돌에서 `override` 가 강제되는 것 | **언어 보장** | (3)·(4) |
| `super<T>` 라는 해소 문법 | **언어 보장** | (3) |
| 클래스가 인터페이스를 **안 이기는** 것 | **언어 보장** | (4) |
| 인터페이스 멤버가 기본 `open` 인 것 | **언어 보장** | (1) |
| `DefaultImpls` 라는 **이름**과 그 클래스의 존재 | **JVM 백엔드의 구현** | (5) |
| `default` 메서드로 나가는 것 | **`-jvm-default` 기본값**(2.2+) | (5) |
| `access$greet$jd` 같은 합성 메서드 | **구현 세부** | (5) |
| `invokespecial` / `invokestatic` 중 무엇을 쓰나 | **구현 세부** | (5) |
| Java 에서 기본 구현을 물려받는 것 | **위 구현의 따름 결과** | (6) |

★ **이 표의 아래 다섯 줄이 이 주제에서 가장 위험한 자리다** — 언어 계약처럼 외워 버리기 쉽다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 상태 없는 계약 · 여럿 겹쳐 입어야 한다 | **인터페이스** | 다중 구현이 된다 |
| 공통 상태를 물려줘야 한다 | **추상 클래스** | 인터페이스는 서랍이 없다((2)) |
| 하위 타입을 내가 다 알고 싶다 | **`sealed interface`** | 목록의 **23번 주제** |
| 기능을 빌려 오되 계층을 안 만든다 | **위임** | [21번 주제](../21-class-delegation-by/) |
| 남의 타입에 함수만 더한다 | **확장 함수** | [13번 주제](../13-extension-functions-and-properties/) — 단 정적 디스패치다 |
| Java 에서 구현할 인터페이스를 낸다 | 인터페이스 + **기본값 `-jvm-default`** | (6) — `disable` 로 내면 Java 쪽이 깨진다 |
| 람다 하나로 넘길 계약 | **`fun interface`** | 목록의 **36번 주제** |

## 핵심 문장

1. 인터페이스는 **구현은 줄 수 있고 상태는 못 준다** — 초기화·`init`·생성자·`field` 가 한 덩어리로 금지된다.
2. 같은 시그니처가 둘에서 오면 **컴파일러가 안 고른다.** `override` + `super<T>` 로 사람이 적는다.
3. **클래스가 인터페이스를 이기지 않는다** — Java 와 다른 자리다.
4. 인터페이스 멤버는 **기본이 `open`** 이다 — 클래스와 정반대다.
5. **`-jvm-default` 가 세 모양을 만든다.** 2.2 부터 기본이 진짜 `default` 메서드이고, 그래서 **Java 가 그냥 물려받는다.**

## 관련 자료

- [19번 주제](../19-inheritance-open-final-override/) — `open`/`override` 의 기본값과 강제. **`override` 가 왜 키워드인지**는 거기가 정본이고, 여기는 **그것이 충돌 자리에서 어떻게 쓰이나**.
- [16번 주제](../16-properties-backing-field-lateinit-const/) — backing field. **서랍이 있는 프로퍼티와 없는 프로퍼티**의 정본이 거기, 여기는 **인터페이스는 항상 뒤쪽**이라는 사실만.
- [21번 주제](../21-class-delegation-by/) — 클래스 위임. **인터페이스 구현을 통째로 남에게 맡기는 길**이 거기.
- [13번 주제](../13-extension-functions-and-properties/) — 확장 함수의 정적 디스패치. (3)의 `D` 줄과 정면 대비다.
- [`../../../java/syntax/11-interfaces-default-methods/`](../../../java/syntax/11-interfaces-default-methods/) — Java 8 의 `default` 메서드. **왜 그것이 생겼나**와 **class wins 규칙**은 거기.
- [`../../../java/syntax/09-inheritance-overriding/`](../../../java/syntax/09-inheritance-overriding/) — Java 의 상속 규칙.
- 목록의 **23번 주제** — `sealed interface` 와 `when` 완결성. **하위 타입을 닫는 것**은 거기.
- 목록의 **36번 주제** — `fun interface`·SAM 변환.

## 용어 풀이

> **기본 구현(default implementation)** — 인터페이스가 메서드에 몸통을 같이 주는 것.\
> 예: `fun greet(): String = "안녕, $name"` — 구현 클래스가 안 적으면 이것이 돈다.

> **`DefaultImpls`** — Kotlin 컴파일러가 만드는 정적 클래스. 인터페이스 기본 구현의 몸통이 들어간다.\
> 예: `Greeter$DefaultImpls.greet(Greeter)` — 첫 인자가 `this` 다. **언어 기능이 아니라 구현 산출물**이다.

> **JVM default 메서드** — Java 8 이 들인 기능. 인터페이스가 몸통 있는 메서드를 갖는 것.\
> 예: `javap` 에 `public default` 로 찍힌다.

> **`-jvm-default`** — 기본 구현을 어느 모양으로 내릴지 정하는 컴파일러 플래그.\
> 예: `enable`(기본) · `no-compatibility` · `disable` 셋이 있고 세 모양이 다 다르다.

> **다이아몬드 문제(diamond problem)** — 같은 멤버를 두 상위에서 물려받아 어느 쪽인지 정해지지 않는 것.\
> 예: `Walker.move()` 와 `Swimmer.move()` 를 둘 다 물려받은 `Duck`.

> **`super<T>`** — 여러 상위 중 **T 의 구현**을 지목해 부르는 문법.\
> 예: `super<Walker>.move()`. 상위가 하나뿐이면 꺾쇠 없이 `super.move()` 로 쓴다.

> **class wins 규칙** — Java 의 해소 규칙. 클래스의 구현이 인터페이스의 기본 구현을 이긴다.\
> 예: Kotlin 에는 **없다** — 대신 컴파일 에러다((4)).

> **합성 메서드(synthetic method)** — 컴파일러가 소스에 없이 만들어 넣는 메서드.\
> 예: `access$greet$jd` — `javap` 에는 보이지만 소스 어디에도 없다.

## 더 들어가면

- **왜 2.2 에서 기본값을 바꿨나** — Kotlin 이 처음 나온 2016년에는 **Android 가 Java 6/7 바이트코드**를 요구해 `default` 메서드를 못 썼다.\
  그래서 `DefaultImpls` 라는 우회로가 태어났다. Android 가 desugaring 으로 그 제약을 걷어내면서 우회로가 필요 없어졌고, 기본값이 뒤집혔다.\
  ★ **언어 설계가 아니라 플랫폼 사정이 문법 아닌 것을 바꾼 사례**다 — 그래서 이것은 「언어 보장」이 아니라 「구현 세부」 칸에 있다.
- **`DefaultImpls` 를 지우면 바이너리 호환이 깨진다.** 옛 컴파일러로 만든 라이브러리가 그 정적 메서드를 직접 부르고 있기 때문이다.\
  `no-compatibility` 는 「내가 그 호환을 포기한다」는 선언이고, 라이브러리를 내놓는 쪽은 **함부로 쓰면 안 된다.**
- **인터페이스에 상태를 흉내 내는 관용구**가 있다 — 추상 프로퍼티를 선언해 두고 **구현 클래스가 서랍을 갖게** 하는 것이다((1)의 `name`).\
  「인터페이스가 상태를 가진 것처럼 보이지만 서랍은 언제나 구현 클래스에 있다」가 정확한 그림이다.
