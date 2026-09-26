# kotlin/syntax/19 — 상속: `open`/`final` 기본값 뒤집기·`override` 강제 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javap` 에서 실제로 얻었다.\
> 역어셈블은 **기본 `-jvm-target`(1.8 · `major version: 52`)** 이 정본이다.
> ★★ 아래 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적은 자리가 없다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★ 컴파일 에러 — **클래스가 `final`** 이라서

**출력**

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

**왜 그런가**

- 「`this type is final, so it cannot be extended.`」 — `class Account` 는 `final class Account` 와 **같은 뜻**이다.
- Java 에서 같은 코드는 **그냥 컴파일된다.** 거기서는 `final` 을 적어야 잠긴다 — **기본값이 정반대**다.
- 고치려면 `open class Account(val owner: String)` 로 적는다.
- ★ 이 에러는 **클래스 자물쇠**다. 이것만 풀어도 멤버는 여전히 잠겨 있다(2번).

### 2. ★★ 또 컴파일 에러 — **이번엔 멤버 자물쇠**다

**출력**

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

**왜 그런가**

- 문구가 바뀌었다 — 「`'describe' in 'Account' is final and cannot be overridden.`」\
  1번은 `this type is final`(**타입**), 여기는 `'describe' … is final`(**멤버**)이다. **에러 문구가 어느 자물쇠인지 말해 준다.**
- `open class` 는 「이 클래스를 상속해도 된다」만 허가한다. **멤버를 덮어도 된다는 허가는 별개**다.

```text
   open class Account      <- 자물쇠 ① 풀림
   +---------------------------------------+
   |  fun describe()        <- 자물쇠 ② 잠김
   |  open fun describe()   <- 이렇게 적어야 풀린다
   +---------------------------------------+
```

- ★ Java 는 **둘 다 풀린 채로** 시작하므로 이 구분이 없다. Java 에서 온 사람이 가장 자주 밟는 자리다.

### 3. ★★★ 「가린다(hides)」 — 컴파일러가 **의도를 묻는다**

**출력**

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

**왜 그런가**

- 「`'describe' hides member of supertype 'Account' and needs an 'override' modifier.`」\
  ★ **가린다**는 낱말이 핵심이다 — 「새 메서드를 만들려 한 것이냐, 상위 것을 덮으려 한 것이냐」를 컴파일러가 묻는 것이다. 둘 다 말이 되므로 **사람이 정해야 한다.**
- Java 의 `@Override` 는 **애너테이션**이라 안 붙여도 컴파일된다(붙이면 검사해 줄 뿐이다).\
  Kotlin 의 `override` 는 **키워드**라 없으면 **컴파일이 안 된다.**
- ★★★ 막는 것은 오타가 아니다 — **상위 클래스가 나중에 바뀌는 것**이다(8번).

### 4. ★★★ 셋째 줄만 `C.f / B.g` 다 — `override` 는 그 자체가 `open` 이다

**출력**

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

**왜 그런가**

```text
   A   open fun f()        open fun g()
   |        |                   |
   B   override f()        final override g()   <- 여기서 잠근다
   |        |                   |
   C   override f()        (못 건드린다 -> B.g 가 나온다)
```

- ★★★ `B` 에 `open` 을 안 적었는데 `C` 가 `f()` 를 다시 오버라이드한다 — **`override` 는 그 자체가 `open` 을 함의**하기 때문이다.
- `g()` 는 `B` 에서 `final override` 로 잠갔다. 그래서 `C` 의 `g()` 는 **`B.g` 가 그대로 나온다.**
- ★★ 이 자리가 「기본값은 닫힘」이 **일관되지 않는 유일한 곳**이다. `open` 은 안 적으면 닫히는데 **`override` 는 안 적으면 열린다.**\
  내 클래스의 오버라이드가 더 아래에서 또 덮이는 것을 막고 싶으면 **`final override` 를 명시**해야 한다(10번).
- 셋 다 `List<A>` 에 담아 `x.f()` 를 불렀는데 각자의 구현이 나왔다 — **가상 디스패치**다(11번).

### 5. ★ `Square 의 넓이 = 9.0` · `Dot 의 넓이 = 0.0` · `[4.0, 0.0]`

**출력**

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

**왜 그런가**

- `A` — `Square` 가 `name`·`area()` 를 채웠고 `describe()` 는 `Shape` 의 구현이 돈다.
- `B` — `Dot` 은 `name` 만 채웠다. `area()` 는 **중간 층 `Rounded` 가 이미 채워** 놓았다.
- `C` — `List<Shape>` 를 돌며 `area()` 를 부르면 `Square` 는 `4.0`, `Dot` 은 `0.0` 이다.
- ★ `abstract fun area()` 에 `open` 이 없는데 오버라이드된다 — **`abstract` 가 `open` 을 함의**한다. 구현이 없으니 잠글 이유가 없다.
- ★ `Rounded` 는 `name` 을 **안 채웠으므로** 그 자체로는 인스턴스를 만들 수 없다 → `abstract` 여야 한다.\
  이렇게 **중간에서 일부만 채우는** 추상 클래스를 둘 수 있다.
- ★ `Rounded.area()` 는 `abstract` 를 `override` 한 것인데, 4번의 규칙에 따라 **다시 열려 있다** — `Dot` 이 원하면 또 덮을 수 있다.

### 6. ★★ `Any` 를 오버라이드하고 있다 — 모든 클래스의 상위 타입이다

**출력**

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

**왜 그런가**

- `A` — 내가 쓴 `toString()` 이 불린다.
- `B` — `==` 는 **`equals` 를 부르고**(`true`), `===` 는 **같은 객체인지**를 본다(`false`). 두 `Point(1, 2)` 는 다른 객체다.
- `C` — `hashCode()` 를 `x * 31 + y` 로 직접 구현했으므로 `1*31+2 = 33` 이다. **두 번 불러도 같다.**\
  ★ 여기서 기본 `hashCode()` 를 찍었다면 **실행마다 바뀌는 값**이 나왔을 것이다 — 그래서 일부러 직접 구현했다.
- `D` — 아무것도 오버라이드 안 한 `Plain` 은 `==` 가 **`Any.equals`(참조 비교)로 떨어져** `false` 다.\
  ★ `Plain(1).javaClass.name` 이 `Plain` 인 것도 같이 찍었다 — **기본 `toString()` 은 해시코드가 박혀 흔들리므로 싣지 않았다.**
- ★★ `Point` 는 `: Any()` 라고 적지 않았는데 **이미 `Any` 를 상속하고 있다.** `Any` 가 `equals`/`hashCode`/`toString` 셋을 `open` 으로 선언해 두었기 때문에 `open` 을 적을 필요가 없다.

### 7. ★ 3번과 **같은 에러**다 — `supertype` 자리에 `Any` 가 온다

**출력**

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

**왜 그런가**

- 「`'toString' hides member of supertype 'Any' and needs an 'override' modifier.`」\
  3번의 문구에서 `'Account'` 자리에 **`'Any'`** 가 들어갔을 뿐 규칙은 똑같다.
- ★★ **아무것도 상속하지 않은 클래스는 없다.** `class Point` 는 `class Point : Any()` 다.
- 그래서 `equals`·`hashCode`·`toString` 이라는 **이름 셋은 어떤 클래스에서도 이미 예약**되어 있다 — 새 메서드로 만들 수 없다.
- ★ 반대로 `override` 를 상위에 없는 이름에 붙이면 「`'g' overrides nothing.`」이 난다(9번 아래 「금지 사례」).

### 8. 막는 것은 「**상위 클래스가 나중에 바뀌는 것**」이다

**왜 그런가**

```text
   시점 1                        시점 2 — 라이브러리가 올라갔다
   -------------------------     ------------------------------------
   class Account                 class Account
     (describe() 없음)             fun describe()      <- 새로 추가됐다
        |                              |
   class Savings : Account()      class Savings : Account()
     fun describe()  <- 내 것        fun describe()  <- 이제 무엇인가?
```

- Java 에서는 **그 순간 조용히 오버라이드가 된다.** 내 메서드가 상위의 새 메서드를 덮게 되고, 상위 코드가 `describe()` 를 부르면 **내 구현이 불린다.**\
  이름이 같을 뿐 **뜻이 전혀 다른 메서드**일 수 있는데 아무도 안 묻는다.
- Kotlin 에서는 **그 순간 컴파일이 깨진다**(3번). 「`hides member of supertype`」이 나오고 사람이 셋 중 하나를 골라야 한다 —\
  `override` 를 붙이거나, 이름을 바꾸거나, 상속을 끊거나.
- ★★★ 이것이 **깨지기 쉬운 상위 클래스 문제**의 한 조각이고, Kotlin 은 그것을 **런타임 사고에서 컴파일 에러로 옮겼다.**
- ★ 같은 발상이 반대 방향에도 있다 — 상위에서 메서드가 **사라지면** 내 `override` 가 「`overrides nothing`」으로 깨진다. **양쪽 다 조용하지 않다.**

### 9. ★ `final` 은 진짜 **`ACC_FINAL` 비트**다 — 단 `override` 에는 안 붙는다

**출력**

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

**출력** — 플래그 비트로 본 것

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

**왜 그런가**

| Kotlin | `javap` | 클래스에 `final` | 메서드에 `ACC_FINAL` |
|---|---|---|---|
| `class Locked` | `public final class Locked` | **붙는다** | `m()` 에 **붙는다** |
| `open class Openish` | `public class Openish` | 안 붙는다 | `stillFinal()` 에 **붙는다** |
| `open fun overridable()` | `public java.lang.String overridable()` | — | **안 붙는다** |
| `class Sub : Openish()` | `public final class Sub` | **붙는다** | `override fun` 에 **안 붙는다** |
| `abstract class Abs` | `public abstract class Abs` | 안 붙는다 | `must()` 는 `abstract` |

- ★★ `0x0011` 은 `ACC_PUBLIC`(`0x0001`) + `ACC_FINAL`(`0x0010`) 이다. **주석이 아니라 클래스 파일의 비트**다.\
  그래서 **Java 쪽에서 상속하려 해도 막힌다** — 규칙이 Kotlin 컴파일러 안에만 있는 것이 아니다.
- ★★★ `Sub` 를 보라 — **클래스에는 `final` 이 붙었는데 `override` 한 메서드에는 안 붙었다.**\
  4번의 「`override` 는 그 자체가 `open`」이 **바이트코드에 그대로 나타난 것**이다. (실제로 상속은 클래스가 `final` 이라 못 하지만, **메서드 플래그만 보면 열려 있다.**)
- ★ [18번 주제](../18-visibility-modifiers/)의 `internal` 과 **정확히 반대**다. 거기는 JVM 에 해당 플래그가 **없어서** 이름 뭉개기로 흉내 냈고, 여기는 **플래그가 원래 있어서** 그대로 내려간다.\
  **「언어 기능이 JVM 에 있느냐 없느냐」가 그 기능의 새는 방식을 정한다** — 두 주제를 나란히 읽으면 이것이 보인다.
- `Openish` 의 `ACC_SUPER`(`0x0020`)는 `invokespecial` 의 옛 동작과 관련된 비트이고 이 주제와 무관하다.

### 10. 못 연다 — 그리고 그 자리가 이 언어의 **유일한 비대칭**이다

**출력**

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

**왜 그런가**

- 문구는 2번과 **같다** — 「`'g' in 'B' is final and cannot be overridden.`」. `final override` 로 잠근 것이 `final fun` 과 같은 자물쇠이기 때문이다.
- ★★ 규칙이 지켜지지 않는 자리는 **`override` 자신**이다.
  - `class`·`fun` 은 **안 적으면 닫힌다**(`final`).
  - **`override fun` 은 안 적으면 열린다**(`open`).
- 그래서 닫으려면 **`final override`** 를 **명시**해야 한다. 이 언어에서 `final` 을 직접 타이핑해야 하는 거의 유일한 자리다.
- ★ 왜 이런 예외를 뒀나 — **상위에서 `open` 이던 것이 중간 층을 지났다고 갑자기 닫히면 계층 설계가 끊기기 때문**이다.\
  기본값을 「이어받는다」로 두고, 끊고 싶을 때만 적게 했다.

### 11. **어느 타입을 보고 고르느냐**가 다르다

**왜 그런가**

```text
   상속(19번)                         확장 함수(13번)
   객체를 보고 고른다                 선언 타입을 보고 고른다
   invokevirtual                      invokestatic
   -------------------------------    -------------------------------
   val s: Shape = Square(2.0)         val s: Shape = Square(2.0)
   s.area()  -> Square.area()         s.area()  -> Shape 용 확장이 불린다
```

- [13번 주제](../13-extension-functions-and-properties/)의 확장 함수는 **선언 타입**으로 고른다 — 실행 때 객체가 무엇인지 안 본다(정적 디스패치).
- 5번의 `C` 줄을 확장 함수로 바꾸면 `List<Shape>` 안의 원소가 무엇이든 **`Shape` 용 확장 하나만** 불린다.\
  `Square` 용 확장을 따로 써 놔도 **안 불린다.**
- ★ 가르는 기준 한 줄 — 「**호출 지점에서 타입을 모르는 채로 갈라져야 하는가**」. 그렇다면 상속·인터페이스이고, 아니면 확장 함수로 충분하다.
- ★ 그래서 [21번 주제](../21-class-delegation-by/)의 위임이 중간 답이 된다 — **계층은 안 만들되 가상 디스패치는 유지**한다.

### 12. 구멍은 그대로 있고, **들어가는 문이 좁아졌다**

**왜 그런가**

- [15번 주제](../15-class-declaration-constructors-and-init/)의 실측 결론만 옮기면 — 상위 클래스 `init` 이 `open` 함수를 부르면 **하위 프로퍼티가 아직 안 채워져 있어** 널 불가 타입이 `null` 을 낸다(거기서 `Child(label=null, len=0)` 를 찍었다).\
  ★ **막는 법은 상위 생성자·`init` 에서 `open` 멤버를 부르지 않는 것**이다 — 언어가 막아 주지 않는다.
- Java 에서 구멍이 **더 넓은** 이유는 **모든 메서드가 기본적으로 열려 있기 때문**이다. 상위 생성자가 부르는 아무 메서드나 하위가 덮을 수 있다.
- Kotlin 에서 이 구멍에 빠지려면 프로그래머가 **먼저 `open` 을 적어야** 한다.\
  즉 **「나는 이것이 오버라이드될 것을 알고 있다」고 선언한 자리에서만** 난다.
- ★★ 기본값이 구멍을 **없애지는 못한다.** 줄어든 것은 **밟을 수 있는 면적**이지 깊이가 아니다 — 「기본값을 뒤집었으니 안전하다」로 읽으면 안 된다.

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
| **없다** — 흔들리는 값을 **일부러 싣지 않았다** | 컴파일 에러의 **문구·`파일:줄:칸`·캐럿 줄** |
| (기본 `toString()` 의 `Plain@1b6d3586` 꼴 해시코드가 그것인데, 6번에서 `javaClass.name` 으로 바꿔 피했다) | `javap` 출력 **전체**(`final` 수식어·플래그 비트값) |
| | `hashCode()` 값 — **직접 구현해 결정적**으로 만들었다(`33`) |
| | 모든 **종료 코드** · `println` 출력 |

> 근거 — 캡처 스크립트를 처음부터 두 번 돌려 **블록 95개(실행 52 + 소스 43)를 바이트 단위로 대조**했고, **달라진 파일은 0개**였다.

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `finaldef.kt` | **클래스 자물쇠** — `this type is final` | `kotlinc` (컴파일 실패가 결과) |
| `finalmem.kt` | **멤버 자물쇠** — `'describe' … is final` | `kotlinc` (컴파일 실패가 결과) |
| `nomodifier.kt` | `override` **강제** — `hides member of supertype` | `kotlinc` (컴파일 실패가 결과) |
| `chain.kt` | ★★ `override` 가 **자동으로 `open`** 인 것 · `final override` | `kotlinc` → `java` |
| `chainbad.kt` | 잠근 것을 **다시 못 여는 것** | `kotlinc` (컴파일 실패가 결과) |
| `abstr.kt` | `abstract` 가 `open` 을 함의 · **중간 층에서 일부만 채우기** | `kotlinc` → `java` |
| `anyover.kt` | `Any` 의 세 메서드 · `==` 대 `===` · 기본 `equals` | `kotlinc` → `java` |
| `anybad.kt` | `supertype` 자리에 **`Any`** 가 오는 것 | `kotlinc` (컴파일 실패가 결과) |
| `flags.kt` | ★ `ACC_FINAL` 이 붙는 자리 — **`override` 에는 안 붙는다** | `kotlinc` → `javap -p` · `javap -v` |
| `form19.kt` | 3단 계층 + `abstract` + `final override` 가 실제로 도는 것(`Z`) | `kotlinc` → `java` |
| `forbid19.kt` | 가시성 좁히기 · `overrides nothing` · 반환 타입 넓히기 | `kotlinc` (컴파일 실패가 결과) |

**구현 의존 항목** — 에러 메시지의 **문구 그 자체**, `ACC_SUPER` 가 같이 찍히는 것, 플래그 16진 값의 표시 형식,
`javap` 가 멤버를 나열하는 **순서** — **전부 이 컴파일러·JDK 판의 산출물**이다.\
반면 **「클래스·멤버의 기본값이 `final`」·「`override` 는 키워드이고 강제」·「`override` 는 `open` 을 함의」·
「`final override` 로 잠근다」·「`abstract` 는 `open` 을 함의」·「`Any` 의 세 메서드는 `open`」**
는 **언어의 계약**이다.

**★ 던져 봤더니 예상과 달랐던 것 — 두 건**

1. ★★★ **`Sub` 의 `override fun overridable()` 에 `ACC_FINAL` 이 안 붙는다.** 「어차피 클래스가 `final` 이니
   메서드에도 붙여 두겠지」라고 예상했는데 **안 붙었다**(9번). 컴파일러는 **`override` 의 개방성을 메서드 플래그에
   그대로 반영**하고, 실제 차단은 **클래스의 `ACC_FINAL` 에 맡긴다.** 「`final` 클래스의 메서드는 `final` 이다」로
   외우면 바이트코드를 볼 때 틀린다.
2. ★★ **가시성을 좁히려 했을 때 에러가 1건이 아니라 3건**이었다(`forbid19.kt`).
   `cannot weaken access privilege` 하나로 끝날 줄 알았는데, `private` 과 `override` 가 **서로 양립 불가**라는
   말을 컴파일러가 **양방향으로 한 번씩 더** 한다. 에러 개수를 세어 답하는 문항을 만들 때 이런 자리가 함정이다.

**안 터진 것도 출력이다** — `abstr.kt` 의 `Rounded` 는 `name` 을 안 채운 채로 `Shape` 를 상속하는데,
`abstract` 를 붙여 두기만 하면 **경고 한 줄 없이 컴파일된다.** 「덜 채운 클래스」는 에러가 아니라
**정상적인 설계 단위**라는 것을 컴파일러가 침묵으로 말한다.
