# kotlin/syntax/25 — `object` 선언·`companion object`·`object` 식 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javap`·`javac` 에서 실제로 얻었다.\
> 역어셈블은 **기본 `-jvm-target`(1.8 · `major version: 52`)** 이 정본이다.
> ★★ 아래 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적은 자리가 없다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ `B` 와 `C` **사이**, 그리고 `C` 와 `D` **사이**에 하나씩 낀다

**출력**

```text
===== 소스: objinit.kt =====
object Registry {
    init { println("  <Registry 가 초기화된다>") }
    val name = "reg"
    fun ping() = "pong"
}

class Service {
    companion object {
        init { println("  <Service.Companion 이 초기화된다>") }
        const val VERSION = "1.0"
        val tag = "svc"
        @JvmStatic fun boot() = "booted"
    }
}

class Named {
    companion object Factory {
        fun make() = "made"
    }
}

fun main() {
    println("A 시작 — 아직 아무것도 안 건드렸다")
    println("B ${Service.VERSION}")
    println("C ${Registry.ping()}")
    println("D ${Service.tag}")
    println("E ${Service.boot()}")
    println("F ${Named.Factory.make()} ${Named.make()}")
    println("G ${Registry === Registry}")
}
===== kotlinc objinit.kt -d o25i =====
(exit 0)
===== java -cp o25i:kotlin-stdlib.jar ObjinitKt =====
A 시작 — 아직 아무것도 안 건드렸다
B 1.0
  <Registry 가 초기화된다>
C pong
  <Service.Companion 이 초기화된다>
D svc
E booted
F made made
G true
(exit 0)
```

**왜 그런가**

```text
   A 시작 — 아직 아무것도 안 건드렸다   <- 여기까지 어느 클래스도 초기화 안 됐다
   B 1.0                                <- ★ const 를 읽었는데 Companion 이 안 돌았다
     <Registry 가 초기화된다>           <- Registry.ping() 을 부르는 그 순간
   C pong
     <Service.Companion 이 초기화된다>  <- Service.tag(const 아님)를 읽는 그 순간
   D svc
   E booted
   F made made
   G true
```

- ★★★ **`A` 가 먼저 찍힌다.** `object` 는 **선언만으로는 아무 일도 안 한다** — 첫 접근에 `<clinit>` 이 돈다(JVM 의 클래스 초기화 규칙).
- ★★★ **`B` 가 이 문항의 핵심**이다. `Service.VERSION` 은 **`const val`** 이라 **값이 호출부에 박혀** `Service` 클래스를 **아예 건드리지 않는다.** 그러므로 초기화 메시지가 **안 나온다.**
- 반면 `D` 의 `Service.tag` 는 `const` 가 아니라 **진짜 정적 필드를 읽어야** 하므로 그때 `<clinit>` 이 돈다.
- ★ 순서가 **`Registry` 가 먼저**인 것도 그대로 읽어야 한다 — `C` 를 만들면서 `Registry.ping()` 을 부르는 것이 `D` 의 `Service.tag` 보다 앞이기 때문이다. **선언 순서가 아니라 접근 순서**다.
- `F made made` — `Named.Factory.make()` 와 `Named.make()` 는 **같은 것**이다. 이름을 준 companion 도 **바깥 이름으로 바로** 부를 수 있다.
- `G true` — `object` 는 싱글턴이므로 `===` 가 참이다.

### 2. ★★ `INSTANCE` 라는 `public static final` 필드 하나다

**출력**

```text
===== javap -p o25i/Registry.class o25i/Service.class 'o25i/Service$Companion.class' o25i/Named.class =====
Compiled from "objinit.kt"
public final class Registry {
  public static final Registry INSTANCE;
  private static final java.lang.String name;
  private Registry();
  public final java.lang.String getName();
  public final java.lang.String ping();
  static {};
}
Compiled from "objinit.kt"
public final class Service {
  public static final Service$Companion Companion;
  public static final java.lang.String VERSION;
  private static final java.lang.String tag;
  public Service();
  public static final java.lang.String boot();
  public static final java.lang.String access$getTag$cp();
  static {};
}
Compiled from "objinit.kt"
public final class Service$Companion {
  private Service$Companion();
  public final java.lang.String getTag();
  public final java.lang.String boot();
  public Service$Companion(kotlin.jvm.internal.DefaultConstructorMarker);
}
Compiled from "objinit.kt"
public final class Named {
  public static final Named$Factory Factory;
  public Named();
  static {};
}
(exit 0)
```

**왜 그런가**

| 선언 | 클래스 파일 |
|---|---|
| `object Registry` | `class Registry` + **`public static final Registry INSTANCE;`** + `private Registry();` + `static {};` |
| `class Service { companion object }` | `class Service` 에 **`public static final Service$Companion Companion;`** · 별도 클래스 `Service$Companion` |
| `class Named { companion object Factory }` | `class Named` 에 **`public static final Named$Factory Factory;`** |

- ★★★ **싱글턴의 실체는 정적 필드 하나**다. 생성자가 `private` 이므로 밖에서 못 만들고, **`static {}`(`<clinit>`)이 딱 한 번** 채운다.
- ★★ **이중 검사 잠금 코드가 안 보이는 이유** — JVM 이 클래스 초기화를 **한 번만·스레드 안전하게** 수행한다고 명세가 보장하기 때문이다. **언어가 그 보장을 JVM 에서 빌려 쓴다.** 직접 쓸 필요가 없다.
- ★ 이름을 **안 주면 `Companion`**, 주면 **그 이름**(`Factory`)이 필드 이름이 된다.
- ★ `Service$Companion` 의 생성자가 **둘**이다 — `private` 과 합성 생성자(`DefaultConstructorMarker`). [23번 주제](../23-sealed-classes-and-when-exhaustiveness/)의 `sealed` 에서 본 것과 같은 모양이다.
- ★ [24번 주제](../24-enum-class-vs-sealed/)의 `enum` 상수도 **정확히 같은 집안**이다 — `public static final Color RED;` 를 `<clinit>` 이 채운다.

### 3. ★ `VERSION` 에는 `ConstantValue`, `tag` 는 **바깥 클래스**에 산다

**출력**

```text
===== javap -v -p o25i/Service.class | grep -E '^  public static final|^  private static final|^    ConstantValue:|^    flags:' =====
  public static final Service$Companion Companion;
    flags: (0x0019) ACC_PUBLIC, ACC_STATIC, ACC_FINAL
  public static final java.lang.String VERSION;
    flags: (0x0019) ACC_PUBLIC, ACC_STATIC, ACC_FINAL
    ConstantValue: String 1.0
  private static final java.lang.String tag;
    flags: (0x001a) ACC_PRIVATE, ACC_STATIC, ACC_FINAL
    flags: (0x0001) ACC_PUBLIC
  public static final java.lang.String boot();
    flags: (0x0019) ACC_PUBLIC, ACC_STATIC, ACC_FINAL
  public static final java.lang.String access$getTag$cp();
    flags: (0x1019) ACC_PUBLIC, ACC_STATIC, ACC_FINAL, ACC_SYNTHETIC
    flags: (0x0008) ACC_STATIC
  public static final #15= #20 of #2;     // Companion=class Service$Companion of class Service
(exit 0)
```

**왜 그런가**

| 멤버 | 어디에 | 무엇이 붙었나 |
|---|---|---|
| `Companion` | `Service` | `ACC_PUBLIC, ACC_STATIC, ACC_FINAL` |
| `const val VERSION` | `Service` | `ACC_PUBLIC, ACC_STATIC, ACC_FINAL` + ★ **`ConstantValue: String 1.0`** |
| companion 의 `val tag` | ★ **`Service`**(바깥) | `ACC_PRIVATE, ACC_STATIC, ACC_FINAL` |
| `getTag()` | `Service$Companion` | 게터는 companion 안에 있다(2번의 `javap`) |
| `access$getTag$cp()` | `Service` | `ACC_SYNTHETIC` — **둘을 잇는 다리** |
| `@JvmStatic fun boot()` | `Service` **와** `Service$Companion` | **양쪽에 다 있다**(7번) |

- ★★ **`ConstantValue` 가 붙은 것이 1번의 `B` 가 그렇게 나온 이유**다. 호출부는 이 필드를 **읽지 않고** 상수 풀의 값을 그대로 쓴다.
- ★★ **companion 의 프로퍼티는 바깥 클래스의 정적 필드**다. companion 안에 있는 것은 **접근자뿐**이고, `private` 필드를 다른 클래스(`Service$Companion`)가 읽어야 하므로 **합성 다리**(`access$getTag$cp`)가 필요하다.
- ★ 「**호출부에 박히면 라이브러리를 고쳐도 안 따라온다**」는 파급은 [16번 주제](../16-properties-backing-field-lateinit-const/)가 실측 정본이다. 여기서는 **어디에 사는가**까지만 봤다.

### 4. ★★ 익명 타입은 **지역과 `private` 안에서만** 보인다 — 그리고 **호출마다 새 객체**다

**출력**

```text
===== 소스: objexpr.kt =====
interface Greeter { fun greet(): String }

class Holder {
    private fun priv() = object { val extra = "priv-extra" }
    fun usePriv(): String = priv().extra
}

fun localScope(): String {
    val anon = object : Greeter {
        val extra = "local-extra"
        override fun greet() = "hi"
    }
    return "${anon.greet()}/${anon.extra}"
}

fun declared(): Greeter = object : Greeter {
    val extra = "안 보인다"
    override fun greet() = "hi2"
}

fun counterFactory(): Greeter {
    var n = 0
    return object : Greeter {
        override fun greet(): String { n++; return "호출 $n 번째" }
    }
}

fun main() {
    println("A ${localScope()}")
    println("B ${Holder().usePriv()}")
    println("C ${declared().greet()}")
    val c = counterFactory()
    println("D ${c.greet()} ${c.greet()}")
    println("E ${counterFactory().greet()}")
    println("F ${c === counterFactory()}")
    println("G ${declared().javaClass.name}")
}
===== kotlinc objexpr.kt -d o25e =====
(exit 0)
===== java -cp o25e:kotlin-stdlib.jar ObjexprKt =====
A hi/local-extra
B priv-extra
C hi2
D 호출 1 번째 호출 2 번째
E 호출 1 번째
F false
G ObjexprKt$declared$1
(exit 0)
```

**왜 그런가**

| 줄 | 값 | 뜻 |
|---|---|---|
| `A` | `hi/local-extra` | **지역 변수**에 담으면 익명 타입이 보존된다 |
| `B` | `priv-extra` | **`private` 함수**의 추론 반환 타입도 익명 타입 그대로다 |
| `C` | `hi2` | 반환 타입을 `Greeter` 로 적었으니 거기까지만 |
| `D` | `호출 1 번째 호출 2 번째` | 같은 인스턴스의 `n` 이 이어진다 |
| `E` | `호출 1 번째` | ★ **새로 부르면 새 인스턴스** — `n` 이 0부터 |
| `F` | `false` | ★ 그래서 `===` 가 거짓이다 |
| `G` | `ObjexprKt$declared$1` | 익명 클래스 이름 |

- ★★ `D`·`E`·`F` 를 묶으면 답이 나온다 — **`object` 식은 호출할 때마다 새 인스턴스**다. `object` **선언**이 하나뿐인 것과 정반대다.
- `B` 가 읽히는 이유 — `private fun priv()` 의 반환 타입이 **추론**되고, 그 타입은 **클래스 밖으로 안 나가므로** 익명 타입 그대로 둬도 된다. 공개 함수였다면 `Any` 로 내려앉는다(5번).
- `G` 의 이름은 **`파일Kt$함수이름$번호`** 규칙이다 — 난수가 아니지만 **소스를 고치면 번호가 바뀔 수 있으므로** 근거로 쓸 때는 **모양**만 읽는다.
- ★ `counterFactory` 의 `var n = 0` 을 익명 객체가 **잡아 쓰고 고친다.** Java 의 익명 클래스가 사실상 final 만 잡는 것과 다르다([10번 주제](../10-lambdas-and-higher-order-functions/)).

### 5. ★★ 에러 **두 줄** — 그런데 `receiver of type` 이 서로 다르다

**출력**

```text
===== 소스: objexprbad.kt =====
class Holder {
    fun pub() = object { val extra = "pub-extra" }
}

interface Greeter { fun greet(): String }

fun declared(): Greeter = object : Greeter {
    val extra = "x"
    override fun greet() = "hi"
}

fun main() {
    println(Holder().pub().extra)
    println(declared().extra)
}
===== kotlinc objexprbad.kt -d o25eb =====
objexprbad.kt:13:28: error: unresolved reference 'extra' on receiver of type 'Any'.
    println(Holder().pub().extra)
                           ^^^^^
objexprbad.kt:14:24: error: unresolved reference 'extra' on receiver of type 'Greeter'.
    println(declared().extra)
                       ^^^^^
(exit 1)
```

**왜 그런가**

```text
   fun pub() = object { val extra = "pub-extra" }        <- 공개 함수 + 타입 추론
       -> 추론된 반환 타입이 Any 로 내려앉는다
       -> unresolved reference 'extra' on receiver of type 'Any'.

   fun declared(): Greeter = object : Greeter { val extra = "x"; ... }
       -> 내가 Greeter 라고 적었다
       -> unresolved reference 'extra' on receiver of type 'Greeter'.
```

- ★★★ **증상은 같고 원인이 다르다.**
  - 첫째는 **컴파일러가 타입을 좁혔다** — 익명 타입은 **이름을 댈 수 없으므로** 공개 시그니처에 쓸 수 없다. 가장 가까운 이름 있는 상위 타입(`Any`)으로 내려앉는다.
  - 둘째는 **내가 좁혔다** — `Greeter` 라고 적었으니 그 타입의 멤버만 보인다.
- ★★ 한 줄로 — 「**익명 타입은 지역(local)과 `private` 안에서만 산다.**」 밖으로 내보낼 거면 **인터페이스를 선언해서** 내보낸다.
- ★ 이것은 [12번 주제](../12-reified-type-parameters/)의 소거와는 **다른 이유**다. 소거는 런타임에 타입 정보가 사라지는 것이고, 이쪽은 **컴파일러가 공개 API 에 이름 없는 타입을 쓰지 못하게** 막는 것이다.

### 6. ★ 에러 **네 줄** — 타입 파라미터·`inner`·둘째 companion·생성자

**출력**

```text
===== 소스: objforbid.kt =====
object Box<T> {
    fun get(): T? = null
}

class Outer {
    inner companion object
}

class Two {
    companion object A
    companion object B
}

object WithCtor(val x: Int)
===== kotlinc objforbid.kt -d o25b =====
objforbid.kt:1:11: error: type parameters are prohibited for objects.
object Box<T> {
          ^^^
objforbid.kt:6:5: error: modifier 'inner' is not applicable to 'companion object'.
    inner companion object
    ^^^^^
objforbid.kt:11:5: error: only one companion object is allowed per class.
    companion object B
    ^^^^^^^^^
objforbid.kt:14:16: error: objects cannot have constructors.
object WithCtor(val x: Int)
               ^^^^^^^^^^^^
(exit 1)
```

**왜 그런가**

| 시도 | 문구 |
|---|---|
| `object Box<T>` | `type parameters are prohibited for objects.` |
| `inner companion object` | `modifier 'inner' is not applicable to 'companion object'.` |
| 둘째 `companion object` | `only one companion object is allowed per class.` |
| `object WithCtor(val x: Int)` | `objects cannot have constructors.` |

- ★★★ **타입 파라미터가 금지된 이유** — `object` 는 **인스턴스가 하나**인데 타입 파라미터는 **인스턴스마다 타입이 다르다**는 뜻이다. `Box<Int>` 와 `Box<String>` 이 **같은 객체여야 하는데** 타입이 달라야 한다 — 모순이다.
- **생성자가 없는 것**은 2번의 `private Registry()` 와 짝이다 — 인스턴스가 하나이므로 **인자를 받을 시점 자체가 없다.**
- ★ **우회는 함수에 타입 파라미터를 다는 것**이다 — `object Boxes { fun <T> emptyBox(): List<T> = emptyList() }`. 실제로 돌려 확인한 것이 9번의 `F` 다.
- `inner` 가 안 되는 이유 — `inner` 는 **바깥 인스턴스를 잡는다**는 뜻인데 companion 은 **클래스당 하나**라 잡을 바깥 인스턴스가 정해지지 않는다.

### 7. ★★ 통과한다 — 그리고 **네 가지 호출 형태**가 각각 다르다

**출력**

```text
===== 소스: objjava.kt =====
object Single {
    const val TAG = "single"
    fun hello() = "obj-hello"
    @JvmStatic fun staticHello() = "obj-static-hello"
}

class Svc {
    companion object {
        const val VERSION = "9.9"
        val tag = "svc-tag"
        fun plain() = "companion-plain"
        @JvmStatic fun jvmStatic() = "companion-jvmstatic"
    }
}
===== 소스: UseIt.java =====
public class UseIt {
    public static void main(String[] args) {
        System.out.println("A " + Single.INSTANCE.hello());
        System.out.println("B " + Single.staticHello());
        System.out.println("C " + Single.TAG);
        System.out.println("D " + Svc.Companion.plain());
        System.out.println("E " + Svc.jvmStatic());
        System.out.println("F " + Svc.VERSION);
        System.out.println("G " + Svc.Companion.getTag());
    }
}
===== kotlinc objjava.kt -d o25j =====
(exit 0)
===== javac -cp o25j:kotlin-stdlib.jar -d o25j UseIt.java =====
(exit 0)
```

```text
===== java -cp o25j:kotlin-stdlib.jar UseIt =====
A obj-hello
B obj-static-hello
C single
D companion-plain
E companion-jvmstatic
F 9.9
G svc-tag
(exit 0)
```

**왜 그런가**

| Java 코드 | 무엇을 거치나 | 왜 |
|---|---|---|
| `Single.INSTANCE.hello()` | **`INSTANCE` 를 거친다** | `hello()` 는 `Single` 의 **인스턴스 메서드**다 |
| `Single.staticHello()` | 바로 | `@JvmStatic` 이 **정적 메서드**를 만들었다 |
| `Single.TAG` | 바로 | `const val` 은 **정적 필드**다 |
| `Svc.Companion.plain()` | **`Companion` 을 거친다** | `plain()` 은 **`Svc$Companion`** 의 메서드다 |
| `Svc.jvmStatic()` | 바로 | `@JvmStatic` |
| `Svc.VERSION` | 바로 | `const val` |
| `Svc.Companion.getTag()` | **`Companion` 을 거친다** | 게터가 companion 안에 있다(3번) |

- ★★★ **`@JvmStatic` 이 바꾸는 것을 한 줄로** — 「**바깥 클래스에 정적 메서드를 하나 더 만든다**」. 원래 것은 **그대로 남는다**(2번의 `javap` 에 `Service.boot()` 와 `Service$Companion.boot()` 가 **둘 다** 있다).
- ★★ **`Single.hello()` 와 `Svc.plain()` 의 차이가 이 주제의 요점**이다 — 앞엣것은 **같은 클래스**에 있는 인스턴스 메서드이고, 뒤엣것은 **다른 클래스**에 있다. 그래서 8번의 에러 문구가 갈린다.
- ★ Kotlin 쪽에서만 보면 `Single.hello()`·`Svc.plain()` 이 **둘 다 그냥 된다.** 차이가 **Java 에서만 드러나므로** 이 주제는 Java 를 섞어 던져야 한다.

### 8. ★★ 에러 **세 줄**이고 문구가 **둘로 갈린다**

**출력**

```text
===== 소스: BadUse.java =====
public class BadUse {
    public static void main(String[] args) {
        System.out.println(Single.hello());
        System.out.println(Svc.plain());
        System.out.println(Svc.getTag());
    }
}
===== javac -cp o25j:kotlin-stdlib.jar -d o25j BadUse.java =====
BadUse.java:3: error: non-static method hello() cannot be referenced from a static context
        System.out.println(Single.hello());
                                 ^
BadUse.java:4: error: cannot find symbol
        System.out.println(Svc.plain());
                              ^
  symbol:   method plain()
  location: class Svc
BadUse.java:5: error: cannot find symbol
        System.out.println(Svc.getTag());
                              ^
  symbol:   method getTag()
  location: class Svc
3 errors
(exit 1)
```

**왜 그런가**

```text
   Single.hello()
     -> non-static method hello() cannot be referenced from a static context
        ^^^^^^^^^^^^^^^^^^^^^^ 있기는 있다. 인스턴스 메서드일 뿐이다

   Svc.plain()  ·  Svc.getTag()
     -> cannot find symbol   symbol: method plain()   location: class Svc
        ^^^^^^^^^^^^^^^^^^^ 아예 없다. Svc$Companion 에 있다
```

- ★★★ `object` 는 「**있는데 정적이 아니다**」이고, `companion` 은 「**아예 다른 클래스에 있다**」다. 이 두 에러의 차이가 **두 문법의 차이 그 자체**다.
- 고치는 법 — Kotlin 쪽에 **`@JvmStatic`** 을 붙인다. 그러면 `Single.hello()`·`Svc.plain()` 을 **그대로** 쓸 수 있다.
- ★ 프로퍼티는 **`@JvmField`** 나 `const` 를 쓴다. 애너테이션 전부를 훑는 것은 [목록의 **39번 주제**](../39-java-interop-annotations/)다.

### 9. **객체이기 때문에** 인터페이스 구현·확장·변수 담기가 된다

**출력**

```text
===== 소스: objmisc.kt =====
interface Loader<T> { fun load(raw: String): T }

object Ten : Comparable<Int> {
    override fun compareTo(other: Int) = 10 - other
}

class User(val name: String) {
    companion object : Loader<User> {
        override fun load(raw: String) = User(raw)
    }
}

class Order(val id: Int) {
    companion object Named
}

fun User.Companion.fromInt(n: Int) = User("u$n")
fun Order.Named.fromString(s: String) = Order(s.length)

object Boxes {
    fun <T> emptyBox(): List<T> = emptyList()
}

fun main() {
    println("A ${Ten.compareTo(3)} ${Ten > 3}")
    println("B ${User.load("kim").name}")
    println("C ${(User.Companion as Loader<User>).load("lee").name}")
    println("D ${User.fromInt(7).name}")
    println("E ${Order.fromString("abcd").id}")
    println("F ${Boxes.emptyBox<Int>()}")
}
===== kotlinc objmisc.kt -d o25m =====
(exit 0)
===== java -cp o25m:kotlin-stdlib.jar ObjmiscKt =====
A 7 true
B kim
C lee
D u7
E 4
F []
(exit 0)
```

**왜 그런가**

| `static` 으로는 안 되는데 `companion object` 로는 되는 것 | 근거 |
|---|---|
| ① **인터페이스를 구현**한다 | `B kim` — `companion object : Loader<User>` |
| ② **변수에 담아 넘긴다** | `C lee` — `User.Companion` 을 `Loader<User>` 로 캐스팅해 썼다 |
| ③ **확장 함수를 받는다** | `D u7` · `E 4` — `fun User.Companion.fromInt(...)` |

- `A 7 true` — **`object` 선언도 인터페이스를 구현한다.** `Comparable<Int>` 를 구현했으니 `Ten > 3` 이라는 연산자까지 붙는다.
- ★★ `D`·`E` — 이름을 **안 준** companion 은 **`User.Companion`**, **이름을 준** 쪽은 **`Order.Named`** 를 수신자로 적는다. 호출부는 `User.fromInt(7)` 처럼 **정적 팩토리로 보인다**([13번 주제](../13-extension-functions-and-properties/)가 확장의 정본이다).
- `F []` — 타입 파라미터는 `object` 에 못 붙지만 **함수에는 붙는다**(6번의 우회).
- ★★ **대가는 7번·8번**이다 — Java 쪽에서 `Svc.Companion.plain()` 을 거쳐야 하고, 안 그러면 「`cannot find symbol`」이 난다.
- ★ **`@JvmStatic` 이 그 대가를 되산다** — 객체로서의 성질을 **그대로 두면서** 바깥 클래스에 정적 메서드를 **하나 더** 만들어 준다. 없애는 것이 아니라 **더하는 것**이라 둘 다 쓸 수 있다.

### 10. **프로세스 전체가 공유한다** — 그래서 전역 변수와 같다

**왜 그런가**

```text
   object Counter { var n = 0 }
        |
        +-- 스레드 A ----+
        +-- 스레드 B ----+---> 전부 같은 INSTANCE 의 같은 필드를 본다
        +-- 테스트 1 ----+
        +-- 테스트 2 ----+
```

- 인스턴스가 **하나**이므로(2번) 그 안의 `var` 는 **모든 스레드·모든 테스트가 공유**한다.
- **테스트 사이에 상태가 남는 문제**가 정확히 이것이다 — 테스트 1이 바꾼 값을 테스트 2가 본다. JUnit 이 인스턴스를 새로 만들어도 **`object` 는 새로 안 만들어진다.**
- ★★ 「싱글턴이라 편하다」와 「전역이라 위험하다」는 **같은 사실의 앞뒷면**이다. 편한 이유가 「어디서든 이름만으로 닿는다」이고, 위험한 이유도 **똑같이** 「어디서든 이름만으로 닿는다」다.
- ★ 그래서 `object` 에는 **상태를 안 두는 쪽**이 기본이다 — 상수·순수 함수·불변 설정. 상태가 필요하면 **동시성 장치**를 같이 둬야 한다(목록의 **56번 주제**).

### 11. **전부 `<clinit>` 이 채우는 `static final` 필드**라는 점이 같다

**왜 그런가**

```text
   object Registry        ->  public static final Registry INSTANCE;   + static {}
   enum class Color       ->  public static final Color RED, GREEN, BLUE;  + static {}
   data object Marked     ->  public static final Marked INSTANCE;     + static {}
                              + toString() / hashCode() / equals()
   companion object       ->  public static final Outer$Companion Companion;  + static {}
```

- [24번 주제](../24-enum-class-vs-sealed/)의 `enum` 상수는 **`public static final` 필드**이고 `<clinit>` 이 만든다 — `object` 의 `INSTANCE` 와 **완전히 같은 구조**다. 「싱글턴이 공짜」인 이유가 둘 다 여기 있다.
- [22번 주제](../22-data-class-generated-members/)의 `data object` 는 그냥 `object` 에 **`toString`·`hashCode`·`equals` 세 메서드를 더한 것**이다. `INSTANCE` 구조는 그대로다.
- `Outer$Companion` 은 **정적 중첩 클래스**다([`../../../java/syntax/12-nested-classes/`](../../../java/syntax/12-nested-classes/)) — 바깥 인스턴스를 안 잡으므로 `inner` 가 아니고, 그래서 6번에서 `inner companion object` 가 막힌다.
- ★ 한 문장으로 — 「**Kotlin 의 싱글턴 문법은 전부 `<clinit>` + `static final` 필드라는 같은 JVM 장치 위에 서 있다.**」 다른 것은 **누가 그 필드를 갖고 있느냐**뿐이다.

## 실행 검증

```text
===== kotlinc -version =====
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
(exit 0)
```

```text
===== java -version =====
openjdk version "21.0.5" 2024-10-15 LTS
OpenJDK Runtime Environment Temurin-21.0.5+11 (build 21.0.5+11-LTS)
OpenJDK 64-Bit Server VM Temurin-21.0.5+11 (build 21.0.5+11-LTS, mixed mode, sharing)
(exit 0)
```

```text
===== javac -version =====
javac 21.0.5
(exit 0)
```

★ **흔들리는 칸과 안 흔들리는 칸**(제출 전 재대조에서 「고칠 것」과 「설계상 다른 것」을 가르는 선언이다)

| 흔들린다 | 안 흔들린다 |
|---|---|
| **없다** — 기본 `toString`·해시코드를 **하나도 안 찍었다** | `javap` 출력 **전체**(`INSTANCE`·플래그·`ConstantValue`) |
| | 초기화 메시지가 **찍히는 순서** — `<clinit>` 시점은 결정적이다 |
| | 컴파일 에러·`javac` 에러의 **문구와 개수** |
| | 익명 클래스 이름 `ObjexprKt$declared$1` — **규칙적 이름**이다 |
| | 모든 **종료 코드** · `println` 출력 |

> ★ 익명 클래스 이름은 「흔들릴 것 같지만 안 흔들리는」 칸이다 — **`파일Kt$함수이름$번호`** 규칙이라 같은 소스에서 늘 같다. 다만 **소스를 고치면 번호가 바뀔 수 있으므로** 근거로는 **모양**만 읽는다.
>
> 근거 — 캡처 스크립트를 처음부터 다시 돌려 **블록 전체를 바이트 단위로 대조**했고, 이 주제에서 **달라진 파일은 0개**였다.

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `objinit.kt` | ★★★ **초기화가 첫 접근에 도는 것** · **`const` 가 그것을 건너뛰는 것** | `kotlinc` → `java` → `javap -p` → `javap -v` |
| `objexpr.kt` | ★★ 익명 타입이 **지역·`private` 에서 보존되는 것** · **호출마다 새 인스턴스** | `kotlinc` → `java` |
| `objexprbad.kt` | ★★ 공개 함수에서 **`Any` 로 내려앉는 것** | `kotlinc` (컴파일 실패가 결과) |
| `objforbid.kt` | 타입 파라미터·`inner`·둘째 companion·생성자 금지 | `kotlinc` (컴파일 실패가 결과) |
| `objmisc.kt` | ★ `object`·`companion` 이 **인터페이스를 구현**하고 **확장을 받는** 것 | `kotlinc` → `java` |
| `objjava.kt` + `UseIt.java` | ★★ **Java 에서 부르는 네 가지 형태** — `@JvmStatic`·`const` 가 바꾸는 것 | `kotlinc` → `javac` → `java` |
| `BadUse.java` | ★★ **못 부르는 것의 에러가 둘로 갈리는 것** | `javac` (컴파일 실패가 결과) |
| `form25.kt` | `object`·companion·`const`·`@JvmStatic`·`object` 식이 **한 프로그램에서 도는 것**(`Z`·`Y`·`X`) | `kotlinc` → `java` |

**구현 의존 항목** — **필드 이름 `INSTANCE`·기본 이름 `Companion`**(단 이 둘은 **Java 상호운용 계약으로 문서화**돼 있다), `access$getTag$cp` 라는 합성 다리의 이름, 익명 클래스 이름 규칙, `javap` 의 표시 형식, 에러 메시지의 **문구 그 자체** — 이 컴파일러·JDK 판의 산출물이다.\
반면 **「`object` 는 싱글턴이고 첫 접근에 한 번 초기화된다」·「companion 은 클래스당 하나다」·「`object` 는 타입 파라미터·생성자를 못 받는다」·「`object` 식은 호출마다 새 인스턴스다」·「익명 타입은 공개 시그니처에 못 나간다」** 는 **언어의 계약**이다.

**★ 던져 봤더니 예상과 달랐던 것 — 두 건**

1. ★★★ **`const val` 을 읽어도 클래스가 초기화되지 않는다.** 「`Service.VERSION` 을 읽으면 `Service` 가 로딩되고 companion 초기화가 돌겠지」라고 예상했는데 **`B 1.0` 이 초기화 메시지보다 먼저** 찍혔다(1번). `ConstantValue` 가 붙어 **호출부에 값이 박히므로** 클래스를 건드리지도 않는다(3번). 「`const` 는 그냥 빠른 상수」로만 알고 있으면 **초기화 순서를 예측할 때 틀린다.**
2. ★★ **`companion object` 의 프로퍼티가 companion 이 아니라 바깥 클래스에 산다.** `Service$Companion` 안에 `tag` 필드가 있을 줄 알았는데 **`Service` 에 `private static final String tag;`** 가 있었고, companion 에는 **게터만** 있었다(3번). 그래서 `access$getTag$cp()` 라는 합성 다리가 필요했다 — **「companion 은 별도 클래스다」를 「모든 것이 그 안에 있다」로 읽으면 틀린다.**

**안 터진 것도 출력이다** — 2번의 `javap` 어디에도 **이중 검사 잠금이나 `synchronized` 가 없다.**
Kotlin 의 싱글턴 보장은 **코드로 구현된 것이 아니라 JVM 의 클래스 초기화 규칙을 빌려 온 것**이고, 그 사실이 **「코드가 없다」는 관찰**로만 드러난다.
