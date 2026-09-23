# kotlin/syntax/19 — 상속: `open`/`final` 기본값 뒤집기·`override` 강제 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Inheritance](https://kotlinlang.org/docs/inheritance.html) · [Classes](https://kotlinlang.org/docs/classes.html) · [Any](https://kotlinlang.org/api/core/kotlin-stdlib/kotlin/-any/).
> **실행 검증** — 이 문서의 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 에서 실제로 얻었다.\
> `kotlinc` 11회(컴파일 실패 6벌) · `java` 4회 · `javap` 2회.\
> ★★ 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적지 않았다.
> ⚠️ **`-jvm-target` 을 밝히지 않은 바이트코드 주장은 반쪽이다.** 이 문서의 역어셈블은 전부 **기본값 1.8**(`major version: 52`)이다.
> **버전** — `open`/`final`/`abstract`/`override` 와 그 기본값은 전부 **1.0** 이다. 그 뒤로 바뀐 적이 없다.
> **경계** — 클래스 선언·`init` 순서는 [15번 주제](../15-class-declaration-constructors-and-init/)가 정본이고 **상위 생성자에서 `open` 멤버를 부르는 구멍도 거기서 이미 실측했다**(여기서는 결론만 인용한다).\
> 가시성은 [18번 주제](../18-visibility-modifiers/), 인터페이스의 기본 구현과 `super<T>` 는 [20번 주제](../20-interfaces-default-impl-and-super/),\
> 상속 대신 쓰는 합성은 [21번 주제](../21-class-delegation-by/)가 정본이다.\
> Java 쪽 짝은 [`../../../java/syntax/09-inheritance-overriding/`](../../../java/syntax/09-inheritance-overriding/) — **같은 JVM 디스패치 위에서 기본값만 뒤집은 것**이 이 주제의 전부다.
> 이 본문은 Claude 작성이다(원고 없음).

★ **흔들리는 칸 / 안 흔들리는 칸** — 제출 전 재대조에서 「고칠 것」과 「설계상 다른 것」을 가르는 선언이다.

| 흔들린다 | 안 흔들린다 |
|---|---|
| (이 주제에는 없다 — 기본 `toString`·해시코드를 일부러 안 찍었다) | 컴파일 에러의 **문구·`파일:줄:칸`** |
| | `javap` 출력 **전체**(`final` 수식어·`ACC_FINAL` 플래그 비트) |
| | `hashCode()` 값 — **직접 구현해 결정적**으로 만들었다 |

> ★ `Plain(1)` 의 기본 `toString()` 은 `Plain@1b6d3586` 처럼 **실행마다 바뀐다.** 그래서 이 문서는 그 값을 찍지 않고 `javaClass.name` 만 찍었다.
>
> 근거 — 캡처 스크립트를 두 번 돌려 **블록 95개(실행 52 + 소스 43)를 바이트 단위로 대조**했다(전체 결과는 3-answer 의 「실행 검증」).

## 한눈에 — 쉽게 말하면

**Kotlin 은 「상속해도 되나?」의 기본 답을 「안 된다」로 뒤집었다.**

Java 에서는 클래스를 만들면 누구나 상속할 수 있고, 막으려면 `final` 을 적어야 했다.\
Kotlin 은 반대다 — **아무것도 안 적으면 `final`** 이고, 열려면 `open` 을 적어야 한다.

> **`open`** — 「이것은 상속·오버라이드해도 된다」는 허가 표시.\
> 예: `open class A { open fun f() }` 처럼 **클래스와 멤버에 각각** 붙여야 한다. 클래스만 열면 멤버는 여전히 잠겨 있다.

비유는 문서 끝까지 이것 하나로 고정한다 — **건물 개조 허가**다.

| 비유 | 실체 |
|---|---|
| 기본은 「개조 금지」 팻말 | `final` — Kotlin 의 기본값 |
| 「이 건물은 증축해도 됩니다」 | `open class` |
| 「이 벽은 헐어도 됩니다」 | `open fun` — 클래스를 열어도 벽은 따로 열어야 한다 |
| 헐고 다시 세운 벽 | `override fun` |
| 다시 세운 벽은 **또 헐 수 있다** | `override` 가 자동으로 `open` 인 것 |
| 「여기까지. 더는 못 헐어」 | `final override` |
| 설계도에 구멍만 뚫어 놓고 넘긴다 | `abstract` — 열려 있고 **채워야 한다** |
| 관청이 이미 낸 표준 도면 세 장 | `Any` 의 `equals`·`hashCode`·`toString` |

```text
   Java                              Kotlin
   ------------------------------    ------------------------------
   class A            <- 열림        class A            <- 잠김
   final class A      <- 잠김        open class A       <- 열림

     void f()         <- 열림          fun f()          <- 잠김
     final void f()   <- 잠김          open fun f()     <- 열림

     @Override 는 권장               override 는 강제
     (안 붙여도 컴파일된다)          (안 붙이면 컴파일 에러)
```

**기본값을 뒤집은 것 하나, `override` 를 문법으로 강제한 것 하나 — 이 둘이 주제의 전부다.**

## 이 주제가 답하려는 질문

1. **무엇을 명시해야 상속이 열리나** — 클래스만? 멤버만? 둘 다?
2. `override` 를 **강제**해서 막는 실패는 구체적으로 무엇인가.
3. 한 번 `override` 한 멤버는 **그다음에 어떻게 되나** — 다시 잠기나, 열린 채인가.

## 동작 방식

### (1) ★★ 클래스도 잠겨 있고 멤버도 따로 잠겨 있다 — 자물쇠가 둘이다

**언제 쓰나** — 남의 클래스를 상속하려다 막힐 때, 그리고 내 클래스를 열지 말지 정할 때.

**클래스 자물쇠**

```text
===== 소스: finaldef.kt =====
class Account(val owner: String)

class Savings(owner: String) : Account(owner)
===== kotlinc finaldef.kt -d o1 =====
finaldef.kt:3:32: error: this type is final, so it cannot be extended.
class Savings(owner: String) : Account(owner)
                               ^^^^^^^
(exit 1)
```

**멤버 자물쇠** — 클래스를 열어도 멤버는 여전히 잠겨 있다.

```text
===== 소스: finalmem.kt =====
open class Account(val owner: String) {
    fun describe() = "Account($owner)"
}

class Savings(owner: String) : Account(owner) {
    override fun describe() = "Savings($owner)"
}
===== kotlinc finalmem.kt -d o2 =====
finalmem.kt:6:5: error: 'describe' in 'Account' is final and cannot be overridden.
    override fun describe() = "Savings($owner)"
    ^^^^^^^^
(exit 1)
```

```text
   open class Account          <- 자물쇠 ① 풀림
   +--------------------------------------+
   |  fun describe()            <- 자물쇠 ② 여전히 잠김
   |  open fun describe()       <- 풀려면 이것
   +--------------------------------------+
        두 자물쇠를 다 풀어야 오버라이드가 된다
```

- 첫 에러는 「`this type is final, so it cannot be extended.`」 — **클래스 자물쇠**다.
- 둘째는 「`'describe' in 'Account' is final and cannot be overridden.`」 — **멤버 자물쇠**다. `open class` 로 클래스를 열어도 멤버는 안 열린다.
- ★ Java 에서 온 사람이 가장 자주 밟는 자리다. Java 는 **자물쇠가 둘 다 풀린 채**로 시작한다.

### (2) ★★★ `override` 가 강제다 — 「같은 이름을 우연히 쓴 것」을 컴파일러가 잡는다

**언제 쓰나** — 상위 클래스에 나중에 메서드가 추가됐을 때. 이 규칙이 진짜 값을 내는 자리다.

```text
===== 소스: nomodifier.kt =====
open class Account(val owner: String) {
    open fun describe() = "Account($owner)"
}

class Savings(owner: String) : Account(owner) {
    fun describe() = "Savings($owner)"
}
===== kotlinc nomodifier.kt -d o3 =====
nomodifier.kt:6:9: error: 'describe' hides member of supertype 'Account' and needs an 'override' modifier.
    fun describe() = "Savings($owner)"
        ^^^^^^^^
(exit 1)
```

- 문구가 정확하다 — 「`'describe' hides member of supertype 'Account' and needs an 'override' modifier.`」\
  **가린다**(hides)는 낱말이 핵심이다. 컴파일러는 「너는 새 메서드를 만들려 한 것이냐, 덮으려 한 것이냐」를 묻는다.
- ★★ Java 의 `@Override` 는 **애너테이션**이라 안 붙여도 컴파일된다. Kotlin 의 `override` 는 **키워드**라 없으면 컴파일이 안 된다.
- ★★★ 이것이 막는 실패는 「오타」가 아니라 「**상위 클래스가 나중에 바뀌는 것**」이다.\
  라이브러리가 `describe()` 를 새로 추가하면, 내 하위 클래스의 기존 `describe()` 가 **의도치 않게 오버라이드가 된다.**\
  Kotlin 에서는 그 순간 **컴파일이 깨져** 사람이 결정하게 된다.
- ★ 반대 방향도 막힌다 — 상위에 없는 것에 `override` 를 붙이면 「`'g' overrides nothing.`」이다(아래 「문법」의 금지 사례).

### (3) ★★ `override` 한 멤버는 **자동으로 열린 상태**다 — 잠그려면 `final` 을 적는다

**언제 쓰나** — 3단 상속(A → B → C)을 설계할 때. 중간 층이 **의도와 다르게 열려 있다**는 것을 모르면 사고가 난다.

```text
===== 소스: chain.kt =====
open class A {
    open fun f() = "A.f"
    open fun g() = "A.g"
}

open class B : A() {
    override fun f() = "B.f"
    final override fun g() = "B.g"
}

class C : B() {
    override fun f() = "C.f"
}

fun main() {
    val list: List<A> = listOf(A(), B(), C())
    for (x in list) println("${x::class.simpleName} : ${x.f()} / ${x.g()}")
}
===== kotlinc chain.kt -d ochain =====
(exit 0)
===== java -cp ochain:kotlin-stdlib.jar ChainKt =====
A : A.f / A.g
B : B.f / B.g
C : C.f / B.g
(exit 0)
```

```text
   A   open fun f()      open fun g()
   |        |                 |
   B   override f()      final override g()     <- g 는 여기서 잠근다
   |        |                 |
   C   override f()      (못 건드린다)
        |
        v
   A : A.f / A.g      B : B.f / B.g      C : C.f / B.g
```

- `C` 가 `f()` 를 다시 오버라이드했다 — **`B` 에 `open` 을 안 적었는데도 된다.** `override` 는 **그 자체가 `open` 을 함의**한다.
- `g()` 는 `B` 에서 `final override` 로 잠갔다. 그래서 `C` 의 `g()` 는 **`B.g` 가 그대로 나온다.**

```text
===== 소스: chainbad.kt =====
open class A {
    open fun g() = "A.g"
}

open class B : A() {
    final override fun g() = "B.g"
}

class C : B() {
    override fun g() = "C.g"
}
===== kotlinc chainbad.kt -d o4 =====
chainbad.kt:10:5: error: 'g' in 'B' is final and cannot be overridden.
    override fun g() = "C.g"
    ^^^^^^^^
(exit 1)
```

- 잠긴 것을 다시 열려 하면 「`'g' in 'B' is final and cannot be overridden.`」 — (1)의 **멤버 자물쇠와 같은 에러**다.
- ★★ 여기가 Kotlin 이 「기본값은 닫힘」을 **일관되게 지키지 못하는 유일한 자리**다.\
  `open` 은 안 적으면 닫히는데 **`override` 는 안 적으면 열린다.** 닫으려면 `final` 을 **명시**해야 한다.

### (4) `abstract` 는 `open` 을 함의한다 — 그리고 「구현이 없다」를 더한다

**언제 쓰나** — 하위가 반드시 채워야 하는 구멍을 남길 때.

```text
===== 소스: abstr.kt =====
abstract class Shape {
    abstract val name: String
    abstract fun area(): Double
    open fun describe() = "$name 의 넓이 = ${area()}"
}

class Square(val side: Double) : Shape() {
    override val name = "Square"
    override fun area() = side * side
}

abstract class Rounded : Shape() {
    override fun area() = 0.0
}

class Dot : Rounded() {
    override val name = "Dot"
}

fun main() {
    println("A ${Square(3.0).describe()}")
    println("B ${Dot().describe()}")
    val shapes: List<Shape> = listOf(Square(2.0), Dot())
    println("C ${shapes.map { it.area() }}")
}
===== kotlinc abstr.kt -d oabstr =====
(exit 0)
===== java -cp oabstr:kotlin-stdlib.jar AbstrKt =====
A Square 의 넓이 = 9.0
B Dot 의 넓이 = 0.0
C [4.0, 0.0]
(exit 0)
```

```text
   abstract class Shape
     abstract val name        <- 구현 없음. open 을 안 적어도 열려 있다
     abstract fun area()      <- 구현 없음
     open fun describe()      <- 구현 있음. 열려 있다(open 을 적었다)
        |
        +-- class Square      : name/area 를 채운다
        |
        +-- abstract class Rounded : area 만 채우고 name 은 남긴다
                |
                +-- class Dot : name 을 채운다
```

- `abstract` 멤버에 **`open` 을 안 적었는데 오버라이드된다** — `abstract` 가 `open` 을 함의하기 때문이다.
- ★ `Rounded` 처럼 **중간에서 일부만 채우고 나머지를 남기는** 추상 클래스를 둘 수 있다. 남은 것이 하나라도 있으면 그 클래스도 `abstract` 여야 한다.
- ★ `Rounded.area()` 는 `abstract` 를 `override` 한 것인데 **`open` 이 아니어도 `Dot` 이 다시 덮을 수 있다**((3)의 규칙이 여기에도 걸린다).
- `C` 줄에서 `List<Shape>` 로 들고 `area()` 를 부르면 **각자의 구현이 나온다** — 상속의 본래 목적인 **가상 디스패치**다.

> **가상 디스패치(virtual dispatch)** — 어느 구현을 부를지 **컴파일 때가 아니라 실행 때 객체를 보고** 정하는 것.\
> 예: `List<Shape>` 안의 원소가 `Square` 면 `Square.area()` 가, `Dot` 이면 `Dot.area()` 가 불린다.

- ★★ [13번 주제](../13-extension-functions-and-properties/)의 **확장 함수는 정반대**다 — 확장은 **선언 타입**으로 고르는 정적 디스패치라 이 표가 통째로 성립하지 않는다.\
  「상속 계층을 늘려야 하는가, 확장 함수면 되는가」를 가르는 기준이 바로 **이 디스패치 차이**다.

### (5) `Any` 의 세 메서드는 처음부터 `open` 이다

**언제 쓰나** — 값처럼 쓰는 클래스를 만들 때(그리고 `data class` 가 무엇을 대신해 주는지 알기 전에).

```text
===== 소스: anyover.kt =====
class Point(val x: Int, val y: Int) {
    override fun equals(other: Any?): Boolean = other is Point && other.x == x && other.y == y
    override fun hashCode(): Int = x * 31 + y
    override fun toString(): String = "Point($x, $y)"
}

class Plain(val x: Int)

fun main() {
    println("A ${Point(1, 2)}")
    println("B ${Point(1, 2) == Point(1, 2)} / ${Point(1, 2) === Point(1, 2)}")
    println("C ${Point(1, 2).hashCode()} ${Point(1, 2).hashCode()}")
    println("D ${Plain(1) == Plain(1)} / ${Plain(1).javaClass.name}")
}
===== kotlinc anyover.kt -d oany =====
(exit 0)
===== java -cp oany:kotlin-stdlib.jar AnyoverKt =====
A Point(1, 2)
B true / false
C 33 33
D false / Plain
(exit 0)
```

- `Point` 는 `open` 을 하나도 안 적었는데 `equals`·`hashCode`·`toString` 셋을 **오버라이드한다.** `Any` 가 이 셋을 `open` 으로 선언했기 때문이다.

> **`Any`** — 모든 Kotlin 클래스의 최상위 타입. Java 의 `java.lang.Object` 자리다.\
> 예: `Any` 에는 `equals`·`hashCode`·`toString` 셋만 있다. `wait`/`notify` 는 **없다**.

- `B` 줄 — `==` 는 `equals` 를 부르고 `===` 는 **같은 객체인지**를 본다. 내가 쓴 `equals` 가 `true` 를, 참조 비교가 `false` 를 낸다.
- `D` 줄 — 아무것도 오버라이드 안 한 `Plain` 은 `==` 가 **참조 비교로 떨어져** `false` 다.
- ★ `override` 없이 `fun toString()` 이라고만 적으면 (2)와 같은 에러가 난다.

```text
===== 소스: anybad.kt =====
class Point(val x: Int, val y: Int) {
    fun toString(): String = "Point($x, $y)"
}
===== kotlinc anybad.kt -d o5 =====
anybad.kt:2:9: error: 'toString' hides member of supertype 'Any' and needs an 'override' modifier.
    fun toString(): String = "Point($x, $y)"
        ^^^^^^^^
(exit 1)
```

- ★★ 「**`Any` 도 상위 타입이다**」가 요점이다. 아무것도 상속하지 않은 것처럼 보이는 클래스도 이미 `Any` 를 상속하고 있다.

### (6) ★ 바이트코드 — `final` 은 진짜 `ACC_FINAL` 이다

**언제 쓰나** — 「기본값을 뒤집었다」가 말뿐인지 실제 플래그인지 확인할 때.

```text
===== 소스: flags.kt =====
class Locked {
    fun m() = "Locked.m"
}

open class Openish {
    fun stillFinal() = "stillFinal"
    open fun overridable() = "overridable"
}

class Sub : Openish() {
    override fun overridable() = "Sub.overridable"
}

abstract class Abs {
    abstract fun must(): String
}
===== kotlinc flags.kt -d oflags =====
(exit 0)
===== javap -p oflags/Locked.class oflags/Openish.class oflags/Sub.class oflags/Abs.class =====
Compiled from "flags.kt"
public final class Locked {
  public Locked();
  public final java.lang.String m();
}
Compiled from "flags.kt"
public class Openish {
  public Openish();
  public final java.lang.String stillFinal();
  public java.lang.String overridable();
}
Compiled from "flags.kt"
public final class Sub extends Openish {
  public Sub();
  public java.lang.String overridable();
}
Compiled from "flags.kt"
public abstract class Abs {
  public Abs();
  public abstract java.lang.String must();
}
(exit 0)
```

```text
===== javap -v -p oflags/Openish.class | grep -E '^(public|  public)|flags:' =====
public class Openish
  flags: (0x0021) ACC_PUBLIC, ACC_SUPER
  public Openish();
    flags: (0x0001) ACC_PUBLIC
  public final java.lang.String stillFinal();
    flags: (0x0011) ACC_PUBLIC, ACC_FINAL
  public java.lang.String overridable();
    flags: (0x0001) ACC_PUBLIC
(exit 0)
```

```text
   Kotlin                     javap                              플래그
   -----------------------    -------------------------------    ------------------
   class Locked            -> public final class Locked          ACC_PUBLIC ACC_FINAL
     fun m()               ->   public final String m()          ACC_PUBLIC ACC_FINAL
   open class Openish      -> public class Openish               ACC_PUBLIC (FINAL 없음)
     fun stillFinal()      ->   public final String stillFinal() ACC_PUBLIC ACC_FINAL
     open fun overridable()->   public String overridable()      ACC_PUBLIC
   class Sub : Openish()   -> public final class Sub             <- 클래스는 final
     override fun …        ->   public String overridable()      <- 메서드는 final 아님
   abstract class Abs      -> public abstract class Abs
     abstract fun must()   ->   public abstract String must()
```

- ★★ **`final` 이 주석이 아니라 클래스 파일의 `ACC_FINAL` 비트**다(`0x0011` = `ACC_PUBLIC`+`ACC_FINAL`).\
  그래서 **Java 쪽에서 상속하려 해도 막힌다** — 규칙이 Kotlin 컴파일러 안에만 있는 것이 아니다.\
  ★ [18번 주제](../18-visibility-modifiers/)의 `internal` 과 **정확히 반대**다. 거기는 JVM 에 플래그가 없어 이름으로 흉내 냈고, 여기는 **플래그가 그대로 있다.**
- ★ `Sub` 를 보라 — **클래스는 `final` 인데 메서드는 `final` 이 아니다.** (3)에서 본 「`override` 는 열려 있다」가 바이트코드에도 그대로 있다.\
  클래스가 `final` 이라 실제로 상속은 못 하지만, **메서드 플래그만 보면 열려 있다.**
- `Openish` 클래스에는 `ACC_FINAL` 이 없고 `ACC_SUPER` 만 있다 — `ACC_SUPER` 는 `invokespecial` 의 옛 동작과 관련된 비트라 여기서는 상관없다.

## 문법 — 형태와 규칙

**형태** — 3단 계층에서 `open`·`abstract`·`override`·`final override` 가 전부 도는 최소 예제다.

```text
===== 소스: form19.kt =====
open class Base {
    open fun f() = "Base.f"
    open val v = 1
    fun locked() = "locked"
}

abstract class Mid : Base() {
    abstract fun g(): String
    override fun f() = "Mid.f"
}

class Leaf : Mid() {
    override fun g() = "Leaf.g"
    final override val v = 2
}

fun main() {
    val l = Leaf()
    println("Z ${l.f()} ${l.g()} ${l.v} ${l.locked()}")
}
===== kotlinc form19.kt -d oform =====
(exit 0)
===== java -cp oform:kotlin-stdlib.jar Form19Kt =====
Z Mid.f Leaf.g 2 locked
(exit 0)
```

**금지 사례**

```text
===== 소스: forbid19.kt =====
open class Base {
    open fun f() = "f"
}

class Sub : Base() {
    private override fun f() = "Sub.f"
}

class NoSuper {
    override fun g() = "g"
}

open class P {
    open fun h() = "h"
}

class Q : P() {
    override fun h(): Int = 1
}
===== kotlinc forbid19.kt -d oforbid =====
forbid19.kt:6:5: error: cannot weaken access privilege private for 'f' in 'Base'.
    private override fun f() = "Sub.f"
    ^^^^^^^
forbid19.kt:6:5: error: modifier 'private' is incompatible with 'override'.
    private override fun f() = "Sub.f"
    ^^^^^^^
forbid19.kt:6:13: error: modifier 'override' is incompatible with 'private'.
    private override fun f() = "Sub.f"
            ^^^^^^^^
forbid19.kt:10:5: error: 'g' overrides nothing.
    override fun g() = "g"
    ^^^^^^^^
forbid19.kt:18:23: error: return type of 'fun h(): Int' is not a subtype of the return type of the overridden member 'fun h(): String' defined in 'P'.
    override fun h(): Int = 1
                      ^^^
(exit 1)
```

**규칙 불릿**

- 클래스는 **기본이 `final`** 이다. 열려면 `open class`.
- 멤버도 **기본이 `final`** 이다. 열려면 `open fun`/`open val`. **자물쇠가 둘**이다((1)).
- `override` 는 **키워드이고 강제**다. 빠뜨리면 「`hides member of supertype`」, 남는 자리에 붙이면 「`overrides nothing`」.
- **`override` 한 멤버는 자동으로 `open`** 이다. 잠그려면 `final override`((3)).
- **`abstract` 는 `open` 을 함의**한다. `abstract` 멤버가 하나라도 있으면 클래스도 `abstract` 여야 한다((4)).
- `Any` 의 `equals`/`hashCode`/`toString` 은 **처음부터 `open`** 이다((5)).
- 오버라이드할 때 **가시성은 넓힐 수 있고 좁힐 수 없다**([18번 주제](../18-visibility-modifiers/)).
- 반환 타입은 **더 좁은 타입으로** 바꿀 수 있고(공변) 넓히면 에러다(금지 사례의 세 번째).
- 상위 클래스를 적을 때 **생성자를 호출한다** — `class Sub : Base()`. 인터페이스는 괄호가 없다([20번 주제](../20-interfaces-default-impl-and-super/)).

## 어디서 틀리나

1. ★★★ **클래스만 열고 멤버를 안 연다.** `open class` 를 적어 놓고 `open fun` 을 빠뜨린다((1)). 에러 문구가 다르므로 **어느 자물쇠인지 먼저 읽어라.**
2. ★★★ **`override` 가 자동으로 열려 있다는 것을 모른다**((3)). 「내 클래스의 메서드는 닫혀 있겠지」가 3단 계층에서 거짓이 된다 — **잠그려면 `final override` 를 명시**해야 한다.
3. ★★ **`open` 클래스의 생성자·`init` 에서 `open` 멤버를 부른다.** 하위 필드가 아직 안 채워져 있어 널 불가 타입이 `null` 을 낸다.\
   ★ 이 구멍은 [15번 주제](../15-class-declaration-constructors-and-init/)가 **이미 실측으로 다뤘다**(`Child(label=null, len=0)`). 결론만 옮기면 — **상위 생성자·`init` 에서 `open` 멤버를 부르지 마라.**\
   ★★ 19번의 기본값이 이 구멍을 **좁힌다** — Java 는 모든 메서드가 열려 있어 누구나 밟을 수 있지만, Kotlin 은 `open` 을 적은 자리에서만 난다.
4. ★★ **`@Override` 습관으로 `override` 를 생략한다.** Java 는 경고(설정에 따라)지만 Kotlin 은 **컴파일 에러**다 — 다행히 조용히 안 샌다.
5. ★ **`abstract` 에 `open` 을 덧붙인다.** 불필요하고(함의되어 있다) 컴파일러가 경고한다.
6. ★ **가시성을 좁히려 한다.** `private override` 는 「`cannot weaken access privilege`」다([18번 주제](../18-visibility-modifiers/) 12번).
7. ★ **`final` 이 성능 때문이라고 믿는다.** 기본값을 뒤집은 이유는 **설계**(깨지기 쉬운 상위 클래스 문제)이지 속도가 아니다 — 이 문서는 **속도를 재지 않았고 재지 않은 성능 주장은 하지 않는다.**
8. ★ **`data class` 를 상속하려 한다.** `data class` 는 `open` 으로 만들 수 없다 — 목록의 **22번 주제**가 정본이다.

## 구현 세부사항 대 언어 보장

| 항목 | 어느 쪽인가 | 근거 |
|---|---|---|
| 클래스·멤버의 기본값이 `final` 인 것 | **언어 보장** | (1) |
| `override` 가 키워드이고 강제인 것 | **언어 보장** | (2) |
| `override` 가 `open` 을 함의하는 것 · `final override` | **언어 보장** | (3) |
| `abstract` 가 `open` 을 함의하는 것 | **언어 보장** | (4) |
| `Any` 의 세 메서드가 `open` 인 것 | **언어 보장** | (5) |
| `final` 이 `ACC_FINAL` 비트로 나가는 것 | **JVM 백엔드의 구현** | (6)의 `javap` |
| `override` 한 메서드에 `ACC_FINAL` 이 안 붙는 것 | **위 구현의 따름 결과** | (6) |
| 에러 메시지의 **문구 그 자체** | **컴파일러 판의 산출물** | 판이 바뀌면 문구가 바뀐다 |
| 「`final` 이면 JIT 가 더 잘 인라인한다」 | **측정 안 함** | 이 문서는 성능을 재지 않았다 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 하위가 반드시 채워야 하는 구멍 | `abstract` | 안 채우면 컴파일이 안 된다 |
| 기본 동작을 주되 바꿀 수 있게 | `open` + 구현 | 단 생성자에서 부르지 마라((3)의 주의) |
| 계약만 있고 상태가 없다 | **인터페이스** | [20번 주제](../20-interfaces-default-impl-and-super/) — 여럿을 섞을 수 있다 |
| 기능을 빌려 오되 계층은 안 만든다 | **위임** | [21번 주제](../21-class-delegation-by/) — 상속 대신 합성 |
| 남의 타입에 함수를 더한다 | **확장 함수** | [13번 주제](../13-extension-functions-and-properties/) — 단 정적 디스패치다 |
| 값처럼 쓸 타입 | `data class` | 목록의 **22번 주제** — `open` 이 안 된다 |
| 상속을 열 이유가 없다 | **아무것도 안 적는다** | 그것이 Kotlin 의 기본값이다 |

## 핵심 문장

1. **자물쇠가 둘이다** — 클래스와 멤버를 각각 `open` 해야 한다.
2. **`override` 는 키워드이고 강제**다. 그것이 막는 것은 오타가 아니라 **상위 클래스가 나중에 바뀌는 것**이다.
3. **`override` 는 그 자체가 `open`** 이다 — 잠그려면 `final override`.
4. **`abstract` 는 `open` 을 함의**하고, `Any` 의 세 메서드는 처음부터 열려 있다.
5. `final` 은 말이 아니라 **`ACC_FINAL` 비트**다 — Java 쪽에서도 막힌다.

## 관련 자료

- [15번 주제](../15-class-declaration-constructors-and-init/) — 클래스 선언·`init` 순서. **상위 생성자에서 `open` 멤버를 부르는 구멍의 실측은 거기**, 그 구멍을 기본값이 좁힌다는 결론은 여기.
- [18번 주제](../18-visibility-modifiers/) — 가시성. **오버라이드에서 가시성이 움직이는 방향**은 거기가 정본.
- [20번 주제](../20-interfaces-default-impl-and-super/) — 인터페이스. **여럿에서 상속했을 때의 충돌**은 거기.
- [21번 주제](../21-class-delegation-by/) — 클래스 위임. **상속을 안 쓰고 같은 것을 얻는 길**이 거기.
- [13번 주제](../13-extension-functions-and-properties/) — 확장 함수의 **정적 디스패치**. (4)의 가상 디스패치와 정면 대비다.
- [`../../../java/syntax/09-inheritance-overriding/`](../../../java/syntax/09-inheritance-overriding/) — Java 의 상속. **기본값이 열려 있던 쪽**이 무엇을 겪었는지.
- [`../../언어-특성/README.md`](../../언어-특성/README.md) §11 — 왜 기본값을 뒤집었나(설계 논지).
- 목록의 **22번 주제**와 목록의 **23번 주제** — `data class`·`sealed` 는 상속 계층을 **다른 방식으로** 닫는다.

## 용어 풀이

> **`open`** — 「상속·오버라이드해도 된다」는 허가 표시.\
> 예: `open class A { open fun f() }` — 클래스와 멤버에 각각 붙인다.

> **`final`** — 「더 못 고친다」는 표시. Kotlin 에서는 **안 적으면 이것**이다.\
> 예: `class A` 는 `final class A` 와 같다.

> **`override`** — 상위 멤버를 덮는다는 **키워드**. 애너테이션이 아니라 문법이다.\
> 예: 빠뜨리면 컴파일이 안 된다.

> **`abstract`** — 구현 없이 선언만 남기는 것. `open` 을 함의한다.\
> 예: `abstract fun area(): Double` — 하위가 반드시 채워야 한다.

> **가상 디스패치(virtual dispatch)** — 어느 구현을 부를지 실행 때 객체를 보고 정하는 것.\
> 예: `List<Shape>` 를 돌며 `area()` 를 부르면 원소마다 다른 구현이 불린다.

> **깨지기 쉬운 상위 클래스 문제(fragile base class problem)** — 상위 클래스를 고쳤더니 모르는 하위 클래스가 깨지는 것.\
> 예: 상위에 `describe()` 를 추가했더니 하위의 동명 메서드가 갑자기 오버라이드가 된다. (2)가 막는 것이 이것이다.

> **`ACC_FINAL`** — 클래스 파일의 접근 플래그 비트 하나. `0x0010` 이다.\
> 예: `javap -v` 로 보면 `flags: (0x0011) ACC_PUBLIC, ACC_FINAL` 처럼 나온다.

> **`Any`** — 모든 Kotlin 클래스의 최상위 타입.\
> 예: `equals`·`hashCode`·`toString` 셋만 갖고 있고 셋 다 `open` 이다.

## 더 들어가면

- **Spring 과 Kotlin 이 부딪치는 고전적인 자리**가 이 기본값이다. Spring 의 CGLIB 프록시는 클래스를 **상속해서** 만들기 때문에 `final` 클래스를 프록시할 수 없다.\
  그래서 `kotlin-allopen` 컴파일러 플러그인이 `@Component`·`@Transactional` 이 붙은 클래스를 자동으로 `open` 으로 바꾼다 — **언어 규칙을 빌드 도구가 되돌리는** 셈이다.\
  (컴파일러 플러그인 자체는 이 목록에서 뺀 주제다 — Kotlin 목록의 「뺀 것」 표를 보라.)
- **「상속을 쓸 것인가」를 먼저 물어라.** Kotlin 은 그 질문을 문법으로 강제하는 언어다 — `open` 을 적는 순간 「**나는 이 클래스가 상속될 것을 알고 설계했다**」고 선언하는 것이다.
- **`sealed`** 는 제3의 답이다 — 「열려 있지만 **내가 아는 하위 타입만**」. 목록의 **23번 주제**가 정본이다.
