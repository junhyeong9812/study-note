# kotlin/syntax/25 — `object` 선언·`companion object`·`object` 식 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Object declarations and expressions](https://kotlinlang.org/docs/object-declarations.html) · [Java 에서 Kotlin 호출하기](https://kotlinlang.org/docs/java-to-kotlin-interop.html)(`@JvmStatic`·`const`).
> **실행 검증** — 이 문서의 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 에서 실제로 얻었다.\
> `kotlinc` 5회(컴파일 실패 2벌) · `javac` 2회(1벌은 실패가 결과) · `java` 3회 · `javap` 2회. ★ **Java 를 섞어 던졌다** — `@JvmStatic` 은 Kotlin 쪽에서만 보면 아무것도 안 바뀐 것처럼 보이기 때문이다.\
> ★★ 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적지 않았다.
> ⚠️ **`-jvm-target` 을 밝히지 않은 바이트코드 주장은 반쪽이다.** 이 문서의 역어셈블은 전부 **기본값 1.8**(`major version: 52`)이다.
> **버전** — `object` 선언·`companion object`·`object` 식·`@JvmStatic`·`const` 는 전부 **1.0** 이다. `data object` 만 **1.9** 이고 그것은 [22번 주제](../22-data-class-generated-members/)가 정본이다.
> **경계** — `const val` 이 **호출부에 박히는 것**은 [16번 주제](../16-properties-backing-field-lateinit-const/)가 정본이라 여기서는 **「어디에 사는가」까지**만 본다.\
> 클래스 선언·`init` 순서는 [15번 주제](../15-class-declaration-constructors-and-init/), 확장 함수가 `companion` 에 붙는 것은 [13번 주제](../13-extension-functions-and-properties/)가 정본이다.\
> `@JvmStatic`·`@JvmField`·`@JvmName` 을 **전부 훑는 것**은 목록의 **39번 주제**이고, 여기는 **`object` 를 Java 에서 부르는 데 필요한 만큼**만 본다.
> 이 본문은 Claude 작성이다(원고 없음).

★ **흔들리는 칸 / 안 흔들리는 칸** — 제출 전 재대조에서 「고칠 것」과 「설계상 다른 것」을 가르는 선언이다.

| 흔들린다 | 안 흔들린다 |
|---|---|
| (이 주제에는 없다 — 기본 `toString`·해시코드를 **하나도 안 찍었다**) | `javap` 출력 **전체**(`INSTANCE` 필드·플래그·`ConstantValue`) |
| | 초기화 메시지가 **찍히는 순서** — `<clinit>` 시점은 결정적이다 |
| | 컴파일 에러의 **문구·`파일:줄:칸`** · `javac` 에러의 **문구와 개수** |
| | 익명 클래스 이름 `ObjexprKt$declared$1` — **컴파일러가 붙이는 규칙적 이름**이다 |
| | 모든 **종료 코드** · `println` 출력 |

> ★ 익명 클래스 이름은 「흔들릴 것 같지만 안 흔들리는」 칸이다 — 난수가 아니라 **`파일Kt$함수이름$번호`** 규칙이라 같은 소스에서 늘 같다. 다만 **소스를 한 줄만 고쳐도 번호가 바뀔 수 있으므로** 근거로 쓸 때는 **모양**(어느 함수에서 나왔나)만 읽는다.
>
> 근거 — 캡처 스크립트를 두 번 돌려 블록 전체를 바이트 단위로 대조했다(수치는 3-answer 의 「실행 검증」).

## 한눈에 — 쉽게 말하면

**Kotlin 에는 `static` 이라는 낱말이 없다.** 그 자리를 세 문법이 나눠 갖는다.

| 쓰고 싶은 것 | Kotlin 문법 | JVM 에서 실제로 |
|---|---|---|
| 전역 싱글턴 | `object Foo` | `Foo` 클래스 + **`public static final Foo INSTANCE`** |
| 클래스에 딸린 「정적 멤버」 | `companion object` | **별도 클래스** `Outer$Companion` + `Outer.Companion` 정적 필드 |
| 진짜 `static` 메서드 | `@JvmStatic` | 바깥 클래스에 **정적 메서드가 하나 더** 생긴다 |
| 진짜 `static final` 상수 | `const val` | 바깥 클래스의 **`ConstantValue` 가 붙은 정적 필드** |
| 이름 없는 일회용 객체 | `object : T { ... }` (식) | **익명 클래스** — 호출마다 새 인스턴스 |

비유는 문서 끝까지 이것 하나로 고정한다 — **건물 관리실**이다.

| 비유 | 실체 |
|---|---|
| 건물에 **딱 하나뿐인 관리실** | `object Foo` — 싱글턴 |
| 관리실 문은 **처음 누가 두드릴 때 열린다** | `object` 는 **첫 접근에 초기화**된다 |
| 각 층에 딸린 **작은 관리실** | `companion object` — 클래스마다 하나 |
| 층 관리실에 이름을 안 붙이면 그냥 「관리실」 | 이름을 안 주면 **`Companion`** |
| 로비 게시판에 **미리 복사해 붙여 둔 공지** | `const val` — **호출부에 박힌다**([16번 주제](../16-properties-backing-field-lateinit-const/)) |
| 층 관리실을 안 거치고 **층 입구에 낸 창구** | `@JvmStatic` — 바깥 클래스의 정적 메서드 |
| 필요할 때마다 **그 자리에서 만드는 임시 부스** | `object : T { ... }` 식 |

```text
   object Registry { ... }
   +---------------------------------------------+
   |  class Registry                             |
   |    public static final Registry INSTANCE;   |  <- 이것이 싱글턴의 실체
   |    private Registry();                      |  <- 밖에서 못 만든다
   |    static {};                               |  <- 여기서 INSTANCE 를 만든다
   +---------------------------------------------+   ★ 이 static {} 이 도는 시점이 (2)다

   class Service { companion object { ... } }
   +---------------------------------------------+   +---------------------------+
   |  class Service                              |   |  class Service$Companion  |
   |    public static final Service$Companion    |-->|    getTag()               |
   |                        Companion;           |   |    boot()                 |
   |    public static final String VERSION;      |   +---------------------------+
   |    private static final String tag;         |   ★ 필드는 바깥에, 메서드는 안에
   |    public static final String boot();       |   <- @JvmStatic 이 만든 것
   +---------------------------------------------+
```

**「`static` 이 없다」는 말은 「정적 멤버가 없다」가 아니라 「문법이 다르다」는 뜻**이다. `javap` 로 보면 `static` 이 잔뜩 있다.

## 이 주제가 답하려는 질문

1. `object` 는 **언제** 초기화되나 — 그리고 `const` 가 그것을 어떻게 건너뛰나.
2. `companion object` 는 **`static` 인가** — 아니라면 Java 에서 어떻게 불러야 하나.
3. `object` **식**이 만드는 것의 **타입**은 무엇인가 — 어디까지 보이나.

## 동작 방식

### (1) ★★ `object` 선언은 `INSTANCE` 정적 필드로 내려앉는다

**언제 쓰나** — 「Kotlin 싱글턴은 뭐가 다른가」를 물을 때, 그리고 Java 에서 그것을 부를 때.

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

```text
   object Registry                     class Named { companion object Factory }
   -----------------------------       ------------------------------------------
   public static final Registry        public static final Named$Factory Factory;
                       INSTANCE;       ^^^^^^^^^^^^^^^^^^^^^^ 이름을 준 대로 필드가 생긴다
   private Registry();
   static {};                          class Service { companion object }
                                       public static final Service$Companion Companion;
                                       ^^^^^^^^^^^^^^^^^^^ 이름을 안 주면 Companion
```

- ★★★ **싱글턴의 실체는 `public static final ... INSTANCE` 필드 하나**다. 생성자는 `private` 이라 밖에서 못 만들고, `static {}`(`<clinit>`)이 **딱 한 번** 채운다.
- 이중 검사 잠금(double-checked locking) 같은 것이 **코드에 없다.** JVM 이 클래스 초기화를 **한 번만·스레드 안전하게** 보장하기 때문이다 — **언어가 그 보장을 JVM 에 빌려 쓰는 것**이다.
- ★ `companion object` 에 **이름을 안 주면 `Companion`**, 주면 그 이름이 필드 이름이 된다(`Factory`). 둘 다 **바깥 클래스의 정적 필드**다.
- ★ `Service$Companion` 의 생성자가 **둘**이다 — `private Service$Companion()` 과 합성 생성자. [23번 주제](../23-sealed-classes-and-when-exhaustiveness/)의 `sealed` 에서 본 것과 같은 모양이다.
- ★ `enum` 상수도 **같은 집안**이다 — `public static final Color RED;` 를 `<clinit>` 이 채운다([24번 주제](../24-enum-class-vs-sealed/)).

### (2) ★★★ 초기화는 **지연**된다 — 그리고 `const` 는 그것을 건너뛴다

**언제 쓰나** — 무거운 초기화를 `object` 에 넣었을 때, 그리고 「언제 도나」를 예측해야 할 때.

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

```text
   출력 순서를 그대로 읽으면

   A 시작 — 아직 아무것도 안 건드렸다      <- 여기까지 어느 클래스도 초기화 안 됐다
   B 1.0                                   <- ★ const 를 읽었는데 Companion 이 안 돌았다
     <Registry 가 초기화된다>              <- Registry.ping() 을 부르는 순간
   C pong
     <Service.Companion 이 초기화된다>     <- Service.tag(const 아님)를 읽는 순간
   D svc
   E booted
   F made made
   G true
```

- ★★★ **`A` 가 먼저 찍힌다** — `object` 는 **선언만으로는 아무 일도 안 한다.** 첫 접근에 `<clinit>` 이 돈다(JVM 의 클래스 초기화 규칙).
- ★★★ **`B` 줄이 이 절의 핵심**이다. `Service.VERSION` 은 **`const val`** 이라 **호출부에 값이 박혀** `Service` 클래스를 **아예 건드리지 않는다.** 그래서 초기화 메시지가 **안 나온다.**
- 반면 `D` 의 `Service.tag` 는 `const` 가 아니라 **진짜 필드를 읽어야** 하므로 그때 `<clinit>` 이 돈다.
- ★ `F made made` — `Named.Factory.make()` 와 `Named.make()` 가 **같은 것**이다. 이름을 준 companion 도 **바깥 이름으로 바로 부를 수 있다.**
- ★ `G true` — `object` 는 싱글턴이므로 `===` 가 참이다.

**`const` 가 클래스 파일에서 어디에 사는가**

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

```text
   public static final Service$Companion Companion;   flags: PUBLIC STATIC FINAL
   public static final java.lang.String VERSION;      flags: PUBLIC STATIC FINAL
     ConstantValue: String 1.0                        <- ★ 값이 상수 풀에 박혀 있다
   private static final java.lang.String tag;         flags: PRIVATE STATIC FINAL
                                                      <- companion 의 val 인데 바깥 클래스에 산다
   public static final java.lang.String boot();       <- @JvmStatic 이 만든 정적 메서드
   public static final ... access$getTag$cp();        SYNTHETIC — companion 이 tag 를 읽는 다리
```

- ★★ **`const val VERSION` 에 `ConstantValue` 속성이 붙어 있다.** 그래서 호출부가 이 필드를 **안 읽고 값을 그대로 쓴다** — (2)의 `B` 가 그 결과다.
- ★★ **companion 의 프로퍼티는 바깥 클래스의 정적 필드**다(`private static final String tag`). companion **안**에 있는 것은 **접근자 메서드**뿐이고, 그 사이를 `access$getTag$cp()` 라는 **합성 다리**가 잇는다.
- ★ **호출부에 박히는 것의 파급**(라이브러리를 고쳐도 안 따라온다)은 [16번 주제](../16-properties-backing-field-lateinit-const/)가 정본이다. 여기서는 **어디에 사는가**까지만 본다.

### (3) ★★★ `companion object` 는 **별도 클래스**다 — Java 에서 던져 보면 드러난다

**언제 쓰나** — Kotlin API 를 Java 에서 쓰게 만들 때. **Kotlin 쪽에서만 보면 차이가 안 보인다.**

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

```text
   Java 에서 부르는 법
   --------------------------------------------------------------
   Single.INSTANCE.hello()      <- object 의 보통 함수 : INSTANCE 를 거친다
   Single.staticHello()         <- @JvmStatic  : 그냥 정적 메서드
   Single.TAG                   <- const val   : 그냥 정적 필드
   Svc.Companion.plain()        <- companion 의 보통 함수 : Companion 을 거친다
   Svc.jvmStatic()              <- @JvmStatic  : 그냥 정적 메서드
   Svc.VERSION                  <- const val   : 그냥 정적 필드
   Svc.Companion.getTag()       <- companion 의 val : 게터가 Companion 에 있다
```

**Java 에서 안 되는 것**

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

- ★★★ **에러가 세 줄인데 문구가 둘로 갈린다.**
  - `Single.hello()` → 「`non-static method hello() cannot be referenced from a static context`」 — Java 눈에 `hello()` 는 **`Single` 의 인스턴스 메서드**다. **존재는 하는데 정적으로 못 부른다.**
  - `Svc.plain()`·`Svc.getTag()` → 「`cannot find symbol`」 — **`Svc` 에는 아예 없다.** `Svc$Companion` 에 있다.
- ★★ 이 **두 에러의 차이가 `object` 와 `companion object` 의 차이**다. 앞엣것은 **같은 클래스에 있는데 인스턴스 멤버**이고, 뒤엣것은 **다른 클래스에 있다.**
- ★ 그래서 **`@JvmStatic` 이 바꾸는 것**을 한 줄로 — 「**바깥 클래스에 정적 메서드를 하나 더 만든다**」. 원래 것은 **그대로 남는다**((1)의 `javap` 에 `Service$Companion.boot()` 와 `Service.boot()` 가 **둘 다** 있다).
- ★ `@JvmStatic`·`@JvmField`·`@JvmName` 을 전부 훑는 것은 목록의 **39번 주제**다.

### (4) ★★ `object` 식(익명 객체) — **타입이 어디까지 보이나**가 요점이다

**언제 쓰나** — 리스너·콜백·일회용 구현을 만들 때.

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

```text
   지역 변수 / private 함수                공개 함수 / 선언 타입이 있는 함수
   ---------------------------------      ---------------------------------------
   val anon = object : Greeter {          fun declared(): Greeter = object : Greeter {
       val extra = "local-extra"              val extra = "안 보인다"
       override fun greet() = "hi"            override fun greet() = "hi2"
   }                                      }
   anon.extra  -> 보인다 (A)              declared().extra -> 안 보인다 (5번 블록)
   ^^^^^^^^^^                                               타입이 Greeter 로 좁혀진다
   타입이 「그 익명 타입」 그대로다
```

- `A hi/local-extra` — **지역 변수**에 담으면 익명 타입이 **그대로 보존**되어 `greet()` 도 `extra` 도 쓸 수 있다.
- `B priv-extra` — **`private` 함수**의 반환 타입도 익명 타입이 보존된다. 그래서 같은 클래스 안에서 `extra` 를 읽을 수 있다.
- `C hi2` — 반환 타입을 `Greeter` 로 **적어 뒀으니** 그 타입까지만 보인다.
- ★★ `D 호출 1 번째 호출 2 번째` / `E 호출 1 번째` — **`object` 식은 호출할 때마다 새 인스턴스**다. `counterFactory()` 를 두 번 부르면 **카운터가 따로 돈다.**
- `F false` — 그래서 `===` 가 거짓이다. **`object` 선언은 하나, `object` 식은 부를 때마다 하나**다.
- `G ObjexprKt$declared$1` — 익명 클래스의 이름이다. **`파일Kt$함수이름$번호`** 규칙이라 난수가 아니다.
- ★ `counterFactory` 의 `var n = 0` 을 익명 객체가 **잡아 쓰고 고친다.** Java 의 익명 클래스가 `final`(사실상 final)만 잡는 것과 다르다([10번 주제](../10-lambdas-and-higher-order-functions/)).

**공개 노출을 시도하면**

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

- 「`unresolved reference 'extra' on receiver of type 'Any'.`」 — **공개 함수의 추론된 반환 타입이 `Any` 로 내려앉았다.** 익명 타입은 **모듈 밖으로 새어 나갈 수 없다.**
- 둘째 에러는 「`... on receiver of type 'Greeter'.`」 — 이쪽은 **내가 `Greeter` 라고 적어서** 그렇다. **같은 증상, 다른 원인**이다.
- ★★ 그래서 규칙 한 줄 — 「**익명 타입은 지역(local)과 `private` 안에서만 산다.**」 밖으로 내보낼 거면 **인터페이스를 선언해서** 내보낸다.

### (5) ★ `object` 가 못 하는 것 — 금지 사례 전수

**언제 쓰나** — `object` 를 제네릭 싱글턴으로 쓰려다 막힐 때.

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

```text
   object Box<T>                <- 안 된다. 타입 파라미터를 못 받는다
   inner companion object       <- 안 된다. companion 에 inner 를 못 붙인다
   companion object A / B       <- 안 된다. 클래스당 하나뿐이다
   object WithCtor(val x: Int)  <- 안 된다. 생성자가 없다
```

- ★★★ **「`type parameters are prohibited for objects.`」** — `object` 는 **인스턴스가 하나**인데 타입 파라미터는 **인스턴스마다 다른 타입**을 뜻하므로 서로 모순이다.
- ★ 우회는 **함수에 타입 파라미터를 다는 것**이다 — `object Boxes { fun <T> empty(): List<T> = emptyList() }`. 혹은 `emptyList<T>()` 처럼 **stdlib 이 쓰는 관용구**(안에 캐스팅한 싱글턴을 둔다).
- **생성자가 없는 것**이 (1)의 `private Registry()` 와 짝이다 — 인스턴스가 하나이므로 **인자를 받을 시점이 없다.**
- `companion object` 는 **클래스당 하나**다. 이름만 다르게 둘을 둘 수 없다.

### (6) `object` 선언에 **붙는** 것 — 인터페이스·확장·제네릭 함수

**언제 쓰나** — 싱글턴에 계약을 물리거나, `companion` 을 정적 팩토리처럼 쓰려 할 때.

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

- `A 7 true` — **`object` 가 인터페이스를 구현한다.** `Comparable<Int>` 를 구현했으므로 `Ten > 3` 이라는 연산자까지 붙는다.
- `B kim` · `C lee` — ★★ **`companion object` 도 인터페이스를 구현한다.** `User.load(...)` 로 부르면 정적 팩토리처럼 보이고, `User.Companion` 을 `Loader<User>` 로 **변수에 담아 넘길 수도** 있다. **`static` 이었다면 둘 다 불가능하다.**
- `D u7` · `E 4` — ★★ **`companion` 에 확장 함수를 붙일 수 있다.** 이름을 안 준 쪽은 **`User.Companion`**, 이름을 준 쪽은 **`Order.Named`** 를 수신자로 적는다((1)에서 그 이름이 어디서 오는지 봤다). 호출부는 `User.fromInt(7)`·`Order.fromString("abcd")` 로 **정적 팩토리처럼** 보인다([13번 주제](../13-extension-functions-and-properties/)가 확장의 정본이다).
- `F []` — 타입 파라미터는 `object` 에 못 붙지만 **함수에는 붙는다**((5)의 우회).
- **안 되는 것** — 타입 파라미터·생성자·`inner`·클래스당 둘 이상의 companion((5)).
- ★ `data` 는 붙는다(1.9+ · [22번 주제](../22-data-class-generated-members/)). `private`·`internal` 가시성도 붙는다.

## 문법 — 형태와 규칙

**형태** — `object` 선언·`companion object`·`const`·`@JvmStatic`·`object` 식이 한 프로그램에서 전부 도는 최소 예제다.

```text
===== 소스: form25.kt =====
interface Handler { fun handle(): String }

object Bus {
    private val seen = mutableListOf<String>()
    fun send(m: String): Int { seen += m; return seen.size }
}

class Repo private constructor(val name: String) {
    companion object {
        const val SCHEMA = 3
        fun open(name: String) = Repo(name)
        @JvmStatic fun version() = "v$SCHEMA"
    }
}

fun makeHandler(tag: String): Handler = object : Handler {
    override fun handle() = "handled by $tag"
}

fun main() {
    println("Z ${Bus.send("a")} ${Bus.send("b")}")
    println("Y ${Repo.open("main").name} ${Repo.SCHEMA} ${Repo.version()}")
    println("X ${makeHandler("t1").handle()} ${makeHandler("t1") === makeHandler("t1")}")
}
===== kotlinc form25.kt -d o25form =====
(exit 0)
===== java -cp o25form:kotlin-stdlib.jar Form25Kt =====
Z 1 2
Y main 3 v3
X handled by t1 false
(exit 0)
```

**규칙 불릿**

- `object Foo` 는 **`Foo` 클래스 + `public static final Foo INSTANCE`** 다. 생성자는 `private` 이다((1)).
- 초기화는 **첫 접근**에 한 번이다. JVM 의 클래스 초기화 보장을 그대로 쓴다((2)).
- **`const val` 은 호출부에 박히므로** 그것만 읽으면 **클래스가 초기화되지 않는다**((2)).
- `companion object` 는 **별도 클래스** `Outer$Companion` 이고, 바깥 클래스에 **정적 필드**로 걸린다. 이름을 안 주면 **`Companion`** 이다((1)).
- companion 의 **프로퍼티는 바깥 클래스의 정적 필드**, **접근자는 companion 안**에 있다((2)의 `javap`).
- `@JvmStatic` 은 **바깥 클래스에 정적 메서드를 하나 더** 만든다. 원래 것은 남는다((3)).
- Java 에서 — `object` 의 보통 함수는 **`INSTANCE` 를 거치고**, companion 의 보통 함수는 **`Companion` 을 거친다**((3)).
- `object` **식**은 **호출마다 새 인스턴스**이고, 익명 타입은 **지역·`private` 안에서만** 보인다((4)).
- `object` 는 **타입 파라미터·생성자·`inner`** 를 못 받는다((5)).

## 어디서 틀리나

1. ★★★ **`object` 가 클래스 로딩 때 초기화된다고 믿는다.** **첫 접근**이다((2)) — 무거운 초기화를 넣어 두면 **언제 도는지가 호출 순서에 달린다.**
2. ★★★ **`const val` 만 읽었는데 초기화 로직이 돌 거라 기대한다.** 안 돈다((2)) — 값이 호출부에 박혀 **클래스를 건드리지도 않는다.**
3. ★★ **`companion object` 를 `static` 으로 읽는다.** **별도 클래스**다((1)·(3)). Java 에서 `Svc.plain()` 이 「`cannot find symbol`」로 막힌다.
4. ★★ **`@JvmStatic` 없이 Java 에 API 를 낸다.** `Svc.Companion.plain()` 을 쓰게 되어 **쓰는 쪽이 지저분해진다**((3)).
5. ★★ **공개 함수에서 익명 객체를 반환하고 멤버를 쓰려 한다.** 타입이 `Any` 로 내려앉는다((4)).
6. ★ **`object` 식이 싱글턴인 줄 안다.** **호출마다 새 인스턴스**다((4)의 `D`·`E`·`F`).
7. ★ **제네릭 싱글턴을 만들려 한다.** 「`type parameters are prohibited for objects.`」((5)).
8. ★ **`companion object` 를 둘 두려 한다.** 클래스당 하나다((5)).
9. ★ **`object` 안의 가변 상태를 아무 생각 없이 쓴다.** 싱글턴이라 **프로세스 전체가 공유**한다 — 동시성 문제가 여기서 시작된다(목록의 **56번 주제**).

## 구현 세부사항 대 언어 보장

| 항목 | 어느 쪽인가 | 근거 |
|---|---|---|
| `object` 가 **싱글턴**인 것 · 첫 접근에 초기화되는 것 | **언어 보장** | (2) |
| `companion object` 가 **클래스당 하나**인 것 | **언어 보장** | (5) |
| `object` 가 **타입 파라미터·생성자**를 못 받는 것 | **언어 보장** | (5) |
| `object` 식이 **호출마다 새 인스턴스**인 것 | **언어 보장** | (4) |
| 익명 타입이 **지역·`private` 밖으로 안 새는 것** | **언어 보장** | (4) |
| `const val` 이 **호출부에 박히는 것** | **언어 보장**([16번 주제](../16-properties-backing-field-lateinit-const/)) | (2) |
| **필드 이름이 `INSTANCE`** 인 것 | **JVM 백엔드의 구현**(단 **Java 상호운용 계약**으로 문서화돼 있다) | (1) |
| **`Companion`** 이라는 기본 이름 | 〃 | (1) |
| companion 의 프로퍼티가 **바깥 클래스 정적 필드**로 가는 것 · `access$getTag$cp` | **JVM 백엔드의 구현** | (2)의 `javap` |
| 익명 클래스 이름 `ObjexprKt$declared$1` | **JVM 백엔드의 구현** | (4) |
| `@JvmStatic` 이 **정적 메서드를 더하는** 것 | **상호운용 계약** | (3) |
| 에러 메시지의 **문구 그 자체** | **컴파일러 판의 산출물** | 전부 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 프로세스에 하나뿐인 레지스트리·캐시 | `object` | 이중 검사 잠금이 필요 없다((1)) |
| 클래스에 딸린 팩토리·상수 | `companion object` | 이름 공간이 그 클래스다 |
| Java 에서 자주 부를 API | `companion object` + **`@JvmStatic`** | (3) — 안 붙이면 `Companion` 을 거친다 |
| 컴파일 시점에 정해지는 상수 | `const val` | (2) — 단 호출부에 박힌다([16번 주제](../16-properties-backing-field-lateinit-const/)) |
| 리스너·콜백 한 번 쓰고 버린다 | `object` 식 | (4) — 단 매번 새 객체다 |
| 함수형 인터페이스 하나짜리 | **람다**가 낫다 | 목록의 **36번 주제**(SAM 변환) |
| 상태 없는 헬퍼 함수 모음 | **최상위 함수** | `object` 로 감쌀 이유가 없다 — Kotlin 은 최상위 함수가 된다 |
| 타입마다 달라지는 싱글턴 | **제네릭 함수**나 클래스 | (5) — `object` 는 타입 파라미터를 못 받는다 |
| 데이터 없는 `sealed` 변형 | `data object` | [22번 주제](../22-data-class-generated-members/)·[23번 주제](../23-sealed-classes-and-when-exhaustiveness/) |

## 핵심 문장

1. `object` 는 **`INSTANCE` 정적 필드 하나**이고, **첫 접근에** `<clinit>` 이 한 번 돈다 — 스레드 안전은 **JVM 에서 빌려 온 것**이다.
2. **`const val` 만 읽으면 클래스가 초기화되지 않는다** — 값이 호출부에 박히기 때문이다.
3. `companion object` 는 **`static` 이 아니라 별도 클래스** `Outer$Companion` 이다. 이름을 안 주면 **`Companion`**.
4. companion 의 **프로퍼티는 바깥 클래스에**, **접근자는 companion 안에** 산다.
5. `@JvmStatic` 은 **정적 메서드를 하나 더 만든다** — 원래 것을 없애지 않는다.
6. `object` **식**은 **호출마다 새 인스턴스**이고, 익명 타입은 **지역·`private` 밖으로 안 샌다.**

## 관련 자료

- [13번 주제](../13-extension-functions-and-properties/) — 확장 함수. **`companion` 에 확장을 붙여 정적 팩토리처럼 쓰는 관용구**의 문법이 거기다.
- [15번 주제](../15-class-declaration-constructors-and-init/) — 클래스 선언·`init`. `object` 의 `init` 도 같은 규칙이다.
- [16번 주제](../16-properties-backing-field-lateinit-const/) — **`const val` 이 호출부에 박히는 것의 파급**이 거기가 정본이다. 여기는 **어디에 사는가**까지다.
- [22번 주제](../22-data-class-generated-members/) — `data object`. `object` 에 `toString`/`equals` 를 얹는 문법이 거기다.
- [24번 주제](../24-enum-class-vs-sealed/) — `enum` 상수도 **`<clinit>` 이 만드는 `static final` 필드**다. 같은 집안이다.
- 목록의 **36번 주제** — `fun interface`·SAM 변환. **`object` 식 대신 람다를 쓸 수 있는 조건**이 거기다.
- 목록의 **39번 주제** — Java 상호운용 애너테이션 전부. 여기는 `@JvmStatic`·`const` 만 본다.
- [`../../../java/syntax/12-nested-classes/`](../../../java/syntax/12-nested-classes/) — Java 의 중첩·정적 중첩 클래스. `Outer$Companion` 이 그 구조다.
- [`../../언어-특성/README.md`](../../언어-특성/README.md) §9 — Java 상호운용의 **실제 비용**.

## 용어 풀이

> **`object` 선언** — 클래스 선언과 인스턴스 생성을 한 번에 하는 문법. 인스턴스가 **하나**다.\
> 예: `object Registry { fun ping() = "pong" }`.

> **`INSTANCE`** — `object` 선언이 만드는 **`public static final` 필드**의 이름. Java 에서 이것을 거쳐 부른다.\
> 예: `Registry.INSTANCE.ping()`.

> **`companion object`** — 클래스에 딸린 객체 선언. 클래스당 **하나**이고 **별도 클래스**로 컴파일된다.\
> 예: 이름을 안 주면 `Outer$Companion` + `Outer.Companion` 필드.

> **`@JvmStatic`** — companion·`object` 의 멤버를 **바깥 클래스의 정적 멤버로도** 내보내는 애너테이션.\
> 예: Java 에서 `Svc.jvmStatic()` 으로 부를 수 있게 된다.

> **`const val`** — 컴파일 시점 상수. 클래스 파일에 **`ConstantValue`** 로 박히고 **호출부에 값이 복사**된다.\
> 예: `const val VERSION = "1.0"`.

> **`object` 식(익명 객체)** — 이름 없는 일회용 객체를 그 자리에서 만드는 식.\
> 예: `object : Greeter { override fun greet() = "hi" }` — **호출마다 새 인스턴스**다.

> **클래스 초기화(`<clinit>`)** — 클래스가 처음 쓰일 때 JVM 이 한 번만 돌리는 정적 초기화 블록.\
> 예: `javap` 에 `static {};` 로 보인다. `object` 의 싱글턴 보장이 여기서 온다.

## 더 들어가면

- **왜 `static` 이라는 낱말을 안 뒀나** — `static` 멤버는 **객체가 아니어서** 인터페이스를 구현할 수도, 확장을 받을 수도, 변수에 담을 수도 없다. `companion object` 를 **진짜 객체**로 두면 그 셋이 전부 가능해진다. 대가가 (3)의 Java 쪽 지저분함이고, `@JvmStatic` 이 그 대가를 되사는 장치다.
- **`object` 의 가변 상태는 전역 변수다.** 프로세스 하나에 인스턴스가 하나이므로 **모든 스레드가 공유**한다. 테스트 사이에 상태가 남는 문제도 같은 뿌리다 — 「싱글턴이라 편하다」와 「전역이라 위험하다」는 **같은 사실의 앞뒷면**이다.
- **익명 타입이 밖으로 안 새는 규칙**((4))은 [12번 주제](../12-reified-type-parameters/)의 소거와는 **다른 이유**다. 소거는 런타임에 타입이 사라지는 것이고, 이쪽은 **컴파일러가 공개 시그니처에 이름 없는 타입을 쓰지 못하게** 막는 것이다 — **이름을 댈 수 없는 타입을 API 에 둘 수 없다**는 원칙이다.
