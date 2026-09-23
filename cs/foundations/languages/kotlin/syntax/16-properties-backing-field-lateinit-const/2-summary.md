# kotlin/syntax/16 — 프로퍼티: backing field·커스텀 접근자·`lateinit`·`const` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Properties](https://kotlinlang.org/docs/properties.html) · [Classes](https://kotlinlang.org/docs/classes.html) · [Null safety](https://kotlinlang.org/docs/null-safety.html) · [언어 기능·제안 상태표](https://kotlinlang.org/docs/kotlin-language-features-and-proposals.html).
> **실행 검증** — 이 문서의 모든 출력·에러·예외·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javap` 에서 실제로 얻었다.\
> `kotlinc` 15회(컴파일 실패 7벌) · `java` 5회 · `javap` 7회. **라이브러리와 앱을 따로 컴파일해 「라이브러리만 다시 빌드」를 실제로 재현했다.**
> ⚠️ **`-jvm-target` 을 밝히지 않은 바이트코드 주장은 반쪽이다.** 이 문서의 역어셈블은 전부 **기본값 1.8**(`major version: 52`)이다.
> ⚠️ **다시 돌리면 달라지는 블록은 없다** — 예외는 잡아서 타입과 메시지만 찍었다. 재대조 근거는 3-answer 의 「흔들리는 칸」 표다.
> **버전** — `field`·커스텀 접근자·`lateinit`(프로퍼티)·`const` 는 **1.0**, `lateinit` **지역 변수**는 **1.2**,\
> ★ **explicit backing fields(`field = …`)는 이 판에서 확인했다 — `-language-version 2.3` 이 「only available since language version 2.4」로 거부한다.**\
> 2.4.20 에서는 **플래그 없이·경고 없이** 컴파일된다.
> **경계** — 초기화가 **언제** 도는지는 [15번 주제](../15-class-declaration-constructors-and-init/)가, 위임(`by lazy`·`observable`)은 [17번 주제](../17-delegated-properties/)가,\
> 확장 프로퍼티에 backing field 가 **없다**는 사실은 [13번 주제](../13-extension-functions-and-properties/)가,\
> 널 불가 타입의 보장은 [03번 주제](../03-null-safe-types/)가 정본이다.\
> `@JvmField`·`@get:`/`@field:` 같은 상호운용·use-site target 은 목록의 **35번 주제**·**39번 주제**다.\
> 여기는 **프로퍼티 하나가 필드와 접근자로 어떻게 쪼개지나**만 다룬다.
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**Kotlin 의 프로퍼티는 「필드」가 아니다. 접근자(게터·세터) 한 쌍이고, 필드는 필요할 때만 딸려 온다.**

> **backing field(뒷받침 필드)** — 그 프로퍼티의 값을 실제로 **저장하는 칸**.\
> **접근자 안에서 `field` 라는 이름으로만** 부를 수 있고, **접근자가 그 이름을 안 쓰면 칸 자체가 안 생긴다.**

그래서 **「필드가 생겼나」를 눈으로 확인하는 방법이 있다 — `javap -p` 로 필드 목록을 찍어 보는 것**이다.\
이 문서의 축이 그것이다.

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 창구 직원 둘(주는 사람 · 받는 사람) | 게터와 세터 |
| 창구 뒤의 서랍 | backing field |
| 서랍에서 꺼내 준다 | 접근자가 `field` 를 쓴다 → 서랍이 생긴다 |
| 그 자리에서 계산해 알려 준다 | 커스텀 게터가 `field` 를 안 쓴다 → **서랍이 없다** |
| 서랍은 있는데 아직 비어 있다 | `lateinit` — 대입 전 |
| 빈 서랍에 손을 넣으면 소리가 난다 | `UninitializedPropertyAccessException` |
| 값을 **손님 수첩에 베껴 적어** 보낸다 | `const val` — 호출부에 상수로 박힌다 |
| 창구가 바뀌어도 수첩은 안 바뀐다 | 라이브러리를 고쳐도 `const` 는 안 따라온다 |

```text
   var age: Int = 0              val full: String
       ↑                             get() = "$first $last"
   ┌────────────┐                ┌────────────┐
   │ getAge()   │                │ getFull()  │
   │ setAge(I)  │                │ (세터 없음)│
   ├────────────┤                ├────────────┤
   │ 서랍 age:I │ ★ 있다         │  (없다) ★  │
   └────────────┘                └────────────┘
     field 를 쓰는 기본 접근자      field 를 안 쓰는 커스텀 게터
```

**「프로퍼티를 선언했으니 필드가 있겠지」가 이 주제에서 가장 자주 틀리는 전제다.**

## 이 주제가 답하려는 질문

1. backing field 는 **어느 자리에 생기고 어느 자리에 안 생기나** — 그리고 그것을 어떻게 확인하나.
2. `lateinit` 은 **무엇에 못 붙고**, 초기화 전에 읽으면 무엇이 나오나.
3. `const val` 은 `val` 과 **런타임에 무엇이 다른가** — 그 차이가 언제 사고가 되나.

## 동작 방식

### (1) ★★★ 필드 목록이 답한다 — 다섯 프로퍼티 중 **셋만** 서랍을 받는다

**언제 쓰나** — 커스텀 게터를 달아 놓고 「이건 저장되나?」가 헷갈릴 때. **이 주제의 네 번째 창이다.**

```text
===== 소스: fields.kt =====
class Person(val first: String, val last: String) {
    // ① 기본 접근자 — 저장한다
    var age: Int = 0

    // ② 커스텀 게터에서 field 를 안 쓴다 — 계산만 한다
    val full: String
        get() = "$first $last"

    // ③ 커스텀 게터에서 field 를 쓴다 — 저장한다
    var nickname: String = "none"
        get() = field.uppercase()
        set(value) {
            field = value.trim()
        }

    // ④ 세터만 커스텀이고 게터는 기본 — 저장한다
    var note: String = ""
        set(value) {
            field = "[$value]"
        }

    // ⑤ 계산 프로퍼티인데 var — 게터·세터 둘 다 field 를 안 쓴다
    var initial: String
        get() = first.take(1)
        set(value) {
            println("   버린다: $value")
        }
}
```

**출력** (`javap -p -s ofields/Person.class`)

```text
Compiled from "fields.kt"
public final class Person {
  private final java.lang.String first;
    descriptor: Ljava/lang/String;
  private final java.lang.String last;
    descriptor: Ljava/lang/String;
  private int age;
    descriptor: I
  private java.lang.String nickname;
    descriptor: Ljava/lang/String;
  private java.lang.String note;
    descriptor: Ljava/lang/String;
  public Person(java.lang.String, java.lang.String);
    descriptor: (Ljava/lang/String;Ljava/lang/String;)V

  public final java.lang.String getFirst();
    descriptor: ()Ljava/lang/String;

  public final java.lang.String getLast();
    descriptor: ()Ljava/lang/String;

  public final int getAge();
    descriptor: ()I

  public final void setAge(int);
    descriptor: (I)V

  public final java.lang.String getFull();
    descriptor: ()Ljava/lang/String;

  public final java.lang.String getNickname();
    descriptor: ()Ljava/lang/String;

  public final void setNickname(java.lang.String);
    descriptor: (Ljava/lang/String;)V

  public final java.lang.String getNote();
    descriptor: ()Ljava/lang/String;

  public final void setNote(java.lang.String);
    descriptor: (Ljava/lang/String;)V

  public final java.lang.String getInitial();
    descriptor: ()Ljava/lang/String;

  public final void setInitial(java.lang.String);
    descriptor: (Ljava/lang/String;)V
}
```

```text
   프로퍼티          field 를 쓰나          필드 목록에 있나
   ───────────────  ────────────────────  ─────────────────
   first (주 생성자) 기본 접근자           ✔ first
   last  (주 생성자) 기본 접근자           ✔ last
   age               기본 접근자           ✔ age
   nickname          게터·세터 둘 다 쓴다  ✔ nickname
   note              세터만 쓴다(게터 기본) ✔ note
   full              게터가 계산만 한다     ✘ ★
   initial           게터·세터 둘 다 안 쓴다 ✘ ★

   → 필드 5개 · 접근자 12개
```

그림 해설:

- ★★★ **필드는 `first`·`last`·`age`·`nickname`·`note` 다섯 개**다. `full` 과 `initial` 은 **없다.**\
  그런데 **`getFull()`·`getInitial()`·`setInitial()` 은 있다** — 접근자는 있고 서랍만 없는 상태다.
- ★★ **기준은 「`field` 를 쓰느냐」 하나**다. 접근자를 **하나만** 커스텀해도, 그 커스텀이 `field` 를 쓰거나\
  **나머지 한쪽이 기본 접근자**면 서랍이 생긴다 — `note` 가 그 경우다(세터만 커스텀, 게터는 기본).
- ★ **`initial` 은 `var` 인데 필드가 없다.** 「`var` 니까 저장한다」도 틀린 전제다.\
  세터가 값을 그냥 버리고 있고 컴파일러는 **아무 말도 안 한다.**
- ★ 주 생성자의 `val first` 도 **필드 + 게터**로 쪼개진다 — Kotlin 에는 「필드를 직접 노출」하는 문법이 없다\
  (`@JvmField` 가 그것을 뚫는 도구이고 정본은 목록의 **39번 주제**다).

### (2) `field` 는 **접근자 안에만 있는 이름**이다

**언제 쓰나** — 세터에서 `this.age = value` 라고 쓰고 무한 재귀를 만들 때.

```text
===== 소스: fieldout.kt =====
class Person {
    var age: Int = 0
    fun bump() {
        field = field + 1
    }
}
===== kotlinc fieldout.kt =====
fieldout.kt:4:9: error: unresolved reference 'field'.
        field = field + 1
        ^^^^^
fieldout.kt:4:17: error: unresolved reference 'field'.
        field = field + 1
                ^^^^^
(exit 1)
```

- ★ **접근자 밖에서는 `field` 라는 이름이 존재하지 않는다.** 메서드 안에서 쓰면 `unresolved reference` 다.
- ★ 반대로 **접근자 안에서 프로퍼티 이름을 쓰면 자기 접근자를 다시 부른다**(무한 재귀).\
  `set(value) { field = value }` 라고 써야 하는 이유다.
- 서랍이 없으면 **초기값을 줄 자리도 없다.**

```text
===== 소스: nofield.kt =====
class Person(val first: String) {
    val full: String = "x"
        get() = first
}
===== kotlinc nofield.kt =====
nofield.kt:2:24: error: initializer is prohibited here because this property has no backing field.
    val full: String = "x"
                       ^^^
(exit 1)
```

- ★ 에러 문구가 이유를 그대로 말한다 — **「이 프로퍼티에는 backing field 가 없어서 초기화식이 금지된다」.**\
  (1)의 `full` 에 `= "x"` 를 붙인 것이다.

### (3) ★★ `lateinit` 이 **못 붙는 자리** — 에러가 다섯 종류다

**언제 쓰나** — 주입·초기화가 늦는 값을 nullable 없이 쓰고 싶을 때.

```text
===== 소스: badlateinit.kt =====
class Holder {
    lateinit var n: Int
    lateinit var s: String?
    lateinit val v: String
}
===== kotlinc badlateinit.kt =====
badlateinit.kt:2:5: error: 'lateinit' modifier is not allowed on properties of primitive types.
    lateinit var n: Int
    ^^^^^^^^
badlateinit.kt:3:5: error: 'lateinit' modifier is not allowed on properties of a type with nullable upper bound.
    lateinit var s: String?
    ^^^^^^^^
badlateinit.kt:4:5: error: 'lateinit' modifier is allowed only on mutable properties.
    lateinit val v: String
    ^^^^^^^^
(exit 1)
```

```text
===== 소스: badlateinit2.kt =====
class Holder<T> {
    lateinit var d: Double
    lateinit var b: Boolean
    lateinit var init: String = "a"
    lateinit var t: T
    lateinit var acc: String
        get() = "x"
}
===== kotlinc badlateinit2.kt =====
badlateinit2.kt:2:5: error: 'lateinit' modifier is not allowed on properties of primitive types.
    lateinit var d: Double
    ^^^^^^^^
badlateinit2.kt:3:5: error: 'lateinit' modifier is not allowed on properties of primitive types.
    lateinit var b: Boolean
    ^^^^^^^^
badlateinit2.kt:4:5: error: 'lateinit' modifier is not allowed on properties with initializer.
    lateinit var init: String = "a"
    ^^^^^^^^
badlateinit2.kt:5:5: error: 'lateinit' modifier is not allowed on properties of a type with nullable upper bound.
    lateinit var t: T
    ^^^^^^^^
badlateinit2.kt:6:5: error: 'lateinit' modifier is not allowed on properties with a custom getter or setter.
    lateinit var acc: String
    ^^^^^^^^
(exit 1)
```

```text
   lateinit 이 요구하는 것          거부되는 것
   ─────────────────────────────  ──────────────────────────────────
   var 여야 한다                  val v: String          → mutable properties
   원시 타입이 아니어야 한다       Int · Double · Boolean → primitive types
   nullable 상한이 아니어야 한다   String? · T(상한 없음) → nullable upper bound
   초기화식이 없어야 한다          = "a"                 → with initializer
   접근자가 기본이어야 한다        get() = "x"           → custom getter or setter
```

그림 해설:

- ★★ **선언 여덟 개에 에러 여덟 건, 문구는 다섯 가지**다. 전부 `'lateinit' modifier is not allowed on …` 형태이고\
  `val` 만 `is allowed only on mutable properties` 로 말이 반대다.
- ★★ **`T`(상한 없는 타입 파라미터)가 nullable 로 걸린다.** 상한을 안 쓰면 `Any?` 라서다 —\
  `<T : Any>` 로 바꾸면 통과한다.
- ★ **왜 이런 제약인가**: `lateinit` 의 구현이 「**필드가 `null` 이면 아직 초기화 안 된 것**」이기 때문이다(4번).\
  원시 타입에는 `null` 이 없어 「아직」을 표시할 값이 없고, nullable 타입에서는 **`null` 이 정상 값**이라 구분이 안 된다.\
  `val` 은 나중에 대입할 수 없고, 커스텀 접근자는 **필드를 안 만들 수도 있다**((1)).
- ★ 프로퍼티만이 아니라 **지역 변수와 최상위 변수에도 붙는다**(지역은 1.2 부터).

```text
===== 소스: latescope.kt =====
lateinit var topLevel: String

fun main() {
    lateinit var local: String
    local = "지역도 된다"
    topLevel = "최상위도 된다"
    println("F $local / $topLevel")
}
===== kotlinc latescope.kt =====
(exit 0)
===== java -cp ols:kotlin-stdlib.jar LatescopeKt =====
F 지역도 된다 / 최상위도 된다
```

### (4) ★★ 초기화 전에 읽으면 — 예외 이름과 `isInitialized` 의 실체

**언제 쓰나** — `lateinit` 을 쓰기로 정한 뒤 「안전하게 확인하는 법」이 필요할 때.

```text
===== 소스: late.kt =====
class Service {
    lateinit var conn: String

    fun status(): String = if (::conn.isInitialized) "초기화됨: $conn" else "아직"

    fun use(): Int = conn.length
}

fun main() {
    val s = Service()
    println("A 초기화 전 status() : ${s.status()}")
    try {
        s.use()
    } catch (e: Throwable) {
        println("B 잡힌 예외 : ${e::class.qualifiedName}")
        println("C 메시지    : ${e.message}")
    }
    s.conn = "jdbc:...";
    println("D 대입 후 status()   : ${s.status()}")
    println("E use()              : ${s.use()}")
}
```

**출력** (`java -cp olate:kotlin-stdlib.jar LateKt`)

```text
A 초기화 전 status() : 아직
B 잡힌 예외 : kotlin.UninitializedPropertyAccessException
C 메시지    : lateinit property conn has not been initialized
D 대입 후 status()   : 초기화됨: jdbc:...
E use()              : 8
```

**출력** (`javap -p -s olate/Service.class`)

```text
Compiled from "late.kt"
public final class Service {
  public java.lang.String conn;
    descriptor: Ljava/lang/String;
  public Service();
    descriptor: ()V

  public final java.lang.String getConn();
    descriptor: ()Ljava/lang/String;

  public final void setConn(java.lang.String);
    descriptor: (Ljava/lang/String;)V

  public final java.lang.String status();
    descriptor: ()Ljava/lang/String;

  public final int use();
    descriptor: ()I
}
```

**출력** (`javap -c -p olate/Service.class` — 게터와 `status()`)

```text
  public final java.lang.String getConn();
    Code:
       0: aload_0
       1: getfield      #17                 // Field conn:Ljava/lang/String;
       4: dup
       5: ifnull        9
       8: areturn
       9: pop
      10: ldc           #18                 // String conn
      12: invokestatic  #24                 // Method kotlin/jvm/internal/Intrinsics.throwUninitializedPropertyAccessException:(Ljava/lang/String;)V
      15: aconst_null
      16: areturn

  public final java.lang.String status();
    Code:
       0: aload_0
       1: getfield      #17                 // Field conn:Ljava/lang/String;
       4: ifnull        32
       7: new           #36                 // class java/lang/StringBuilder
      10: dup
      11: invokespecial #37                 // Method java/lang/StringBuilder."<init>":()V
      14: ldc           #39                 // String 초기화됨:
      16: invokevirtual #43                 // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
      19: aload_0
      20: invokevirtual #45                 // Method getConn:()Ljava/lang/String;
      23: invokevirtual #43                 // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
      26: invokevirtual #48                 // Method java/lang/StringBuilder.toString:()Ljava/lang/String;
      29: goto          34
      32: ldc           #50                 // String 아직
      34: areturn

```

```text
   getConn()                       ::conn.isInitialized
   ┌─────────────────────────┐     ┌─────────────────────────┐
   │ getfield conn           │     │ getfield conn           │
   │ ifnull ──┐              │     │ ifnull  → false         │
   │ areturn  │              │     │ else    → true          │
   │          ▼              │     └─────────────────────────┘
   │ throwUninitialized…()   │       ★ 리플렉션이 아니다
   └─────────────────────────┘
```

그림 해설:

- ★★ **예외는 `kotlin.UninitializedPropertyAccessException`** 이고 메시지는\
  `lateinit property conn has not been initialized` 다 — **프로퍼티 이름이 들어 있다.**
- ★★ **필드가 `public` 이다.** 보통 프로퍼티는 `private` 필드 + 접근자인데((1)),\
  `lateinit` 은 `public java.lang.String conn` 이다. **「아직 대입 안 됨」을 바깥에서도 볼 수 있어야 해서**다.
- ★★★ **`::conn.isInitialized` 는 리플렉션이 아니다.** 바이트코드가 `getfield conn; ifnull` 뿐이다 —\
  컴파일러가 **널 검사 한 줄로 바꿔 놓았다.** 그래서 비용 걱정 없이 쓸 수 있다\
  (비용을 **잰 것은 아니다** — 잰 것은 「명령이 둘뿐」이라는 구조다).
- ★ 게터는 `getfield → ifnull → 예외` 다. **필드가 `null` 인지로 「초기화됐나」를 판정**하는 것이 보이고,\
  이것이 (3)의 제약을 전부 설명한다.
- ★ `isInitialized` 를 **아무 데서나 부를 수는 없다.**

```text
===== 소스: badinit.kt =====
class Service {
    var plain: String = "x"
    lateinit var conn: String
    fun check(): Boolean = ::plain.isInitialized
}

fun outside(s: Service): Boolean = s::conn.isInitialized
===== kotlinc badinit.kt =====
badinit.kt:4:36: error: this declaration can only be called on a reference to a 'lateinit' property.
    fun check(): Boolean = ::plain.isInitialized
                                   ^^^^^^^^^^^^^
badinit.kt:7:44: error: backing field of 'var conn: String' is not accessible at this point.
fun outside(s: Service): Boolean = s::conn.isInitialized
                                           ^^^^^^^^^^^^^
(exit 1)
```

- 첫 에러는 **`lateinit` 이 아닌 프로퍼티에는 못 쓴다**는 것,\
  둘째는 **backing field 에 접근할 수 있는 자리(그 클래스 안)에서만 쓸 수 있다**는 것이다.

### (5) ★★★ `const val` 은 **호출부에 박힌다** — 라이브러리를 고쳐도 안 따라온다

**언제 쓰나** — `const` 를 붙일지 말지 정할 때. **이 주제에서 실무 사고가 가장 큰 자리다.**

라이브러리와 앱을 **따로 컴파일**했다.

```text
===== 소스: lib.kt =====
object Config {
    const val VERSION: String = "1.0"
    val BUILD: String = "1.0"
}

===== 소스: app.kt =====
fun main() {
    println("F const val VERSION : ${Config.VERSION}")
    println("G      val BUILD    : ${Config.BUILD}")
}
```

**출력** (`javap -c -p oapp/AppKt.class`)

```text
Compiled from "app.kt"
public final class AppKt {
  public static final void main();
    Code:
       0: ldc           #8                  // String F const val VERSION : 1.0
       2: getstatic     #14                 // Field java/lang/System.out:Ljava/io/PrintStream;
       5: swap
       6: invokevirtual #20                 // Method java/io/PrintStream.println:(Ljava/lang/Object;)V
       9: new           #22                 // class java/lang/StringBuilder
      12: dup
      13: invokespecial #25                 // Method java/lang/StringBuilder."<init>":()V
      16: ldc           #27                 // String G      val BUILD    :
      18: invokevirtual #31                 // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
      21: getstatic     #37                 // Field Config.INSTANCE:LConfig;
      24: invokevirtual #41                 // Method Config.getBUILD:()Ljava/lang/String;
      27: invokevirtual #31                 // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
      30: invokevirtual #44                 // Method java/lang/StringBuilder.toString:()Ljava/lang/String;
      33: getstatic     #14                 // Field java/lang/System.out:Ljava/io/PrintStream;
      36: swap
      37: invokevirtual #20                 // Method java/io/PrintStream.println:(Ljava/lang/Object;)V
      40: return

  public static void main(java.lang.String[]);
    Code:
       0: invokestatic  #47                 // Method main:()V
       3: return
}
```

```text
   F 줄 : ldc "F const val VERSION : 1.0"   ★ 문자열째 상수로 접혔다
                                              Config 를 아예 안 본다
   G 줄 : new StringBuilder
          getstatic Config.INSTANCE
          invokevirtual Config.getBUILD()   ★ 실행할 때 물어본다
```

- ★★★ **`F` 줄에는 `Config` 가 안 나온다.** `ldc` 하나로 끝이다 —\
  **보간 문자열째 컴파일 타임에 접혔다.** `G` 줄은 `StringBuilder` 를 만들고 `getBUILD()` 를 **실행 시점에** 부른다.

그럼 라이브러리만 고쳐서 다시 빌드하면 어떻게 되나.

**출력** (`java` → `kotlinc lib.kt` → `java`)

```text
$ java -cp oapp:olib:kotlin-stdlib.jar AppKt        # lib 은 1.0
F const val VERSION : 1.0
G      val BUILD    : 1.0
$ kotlinc lib.kt -d olib                            # 라이브러리만 2.0 으로 다시 컴파일
(exit 0)
$ java -cp oapp:olib:kotlin-stdlib.jar AppKt        # app 은 한 글자도 안 고쳤다
F const val VERSION : 1.0
G      val BUILD    : 2.0
```

- ★★★ **`F` 가 `1.0` 그대로다.** 라이브러리는 `2.0` 이 됐고 `G` 는 따라왔는데 `F` 만 옛날 값이다.\
  **앱을 다시 컴파일하지 않으면 영원히 `1.0`** 이다.
- ★ 이것이 **버전 문자열·설정 키를 `const` 로 두면 안 되는 이유**다. 반대로 **바뀌지 않는 것**(수학 상수,\
  프로토콜 매직 넘버)에는 `const` 가 맞다.

바이트코드에 이유가 남아 있다.

**출력** (`javap -p -s olib/Config.class` 와 `javap -v`)

```text
Compiled from "lib.kt"
public final class Config {
  public static final Config INSTANCE;
    descriptor: LConfig;
  public static final java.lang.String VERSION;
    descriptor: Ljava/lang/String;
  private static final java.lang.String BUILD;
    descriptor: Ljava/lang/String;
  private Config();
    descriptor: ()V

  public final java.lang.String getBUILD();
    descriptor: ()Ljava/lang/String;

  static {};
    descriptor: ()V
}
$ javap -v -p olib/Config.class   # VERSION 부분만
  public static final java.lang.String VERSION;
    descriptor: Ljava/lang/String;
    flags: (0x0019) ACC_PUBLIC, ACC_STATIC, ACC_FINAL
    ConstantValue: String 2.0
    RuntimeInvisibleAnnotations:
      0: #13()
        org.jetbrains.annotations.NotNull

```

- ★★ **`ConstantValue: String 2.0`** 이라는 속성이 붙어 있다. JVM 의 `ConstantValue` 는\
  「**컴파일러가 이 값을 호출부에 복사해도 된다**」는 표시다. `const val` 이 그것을 켠 것이다.
- ★ `VERSION` 은 `public static final` 인데 `BUILD` 는 **`private static final` + `getBUILD()`** 다.\
  `const` 는 **필드를 직접 노출**하고 일반 `val` 은 게터를 거친다.
- `const` 를 못 쓰는 자리가 있다.

```text
===== 소스: badconst.kt =====
class Holder {
    const val inClass: Int = 1
}

const val listConst: List<Int> = listOf(1)
const val computed: Int get() = 1
===== kotlinc badconst.kt =====
badconst.kt:2:5: error: const 'val' is only allowed on top level, in named objects, in companion objects or companion blocks.
    const val inClass: Int = 1
    ^^^^^
badconst.kt:5:1: error: const 'val' has type 'List<Int>'. Only primitive types and 'String' are allowed.
const val listConst: List<Int> = listOf(1)
^^^^^
badconst.kt:6:25: error: const 'val' cannot have a getter.
const val computed: Int get() = 1
                        ^^^^^^^^^
(exit 1)
```

- ★ 셋 다 **`ConstantValue` 를 쓸 수 없는 조건**이다 — 인스턴스마다 다르면(클래스 안), 값이 객체면(`List`),\
  계산이면(게터) **컴파일 타임에 복사할 값이 없다.**

### (6) ★ explicit backing fields — **이 판에서 직접 확인했다**

**언제 쓰나** — 바깥에는 `List` 로 내고 안에서는 `MutableList` 로 쓰고 싶을 때.

예전 관용구는 **private 백킹 프로퍼티 + public 게터** 두 개를 선언하는 것이었다.\
2.4 부터는 프로퍼티 하나에 **`field` 절**을 붙여 「바깥 타입 / 안쪽 타입」을 갈라 적는다.

```text
===== 소스: ebf.kt =====
class Holder {
    val items: List<String>
        field = mutableListOf<String>()

    fun add(s: String) {
        items.add(s)
    }
}

fun main() {
    val h = Holder()
    h.add("a")
    println("H 바깥에서 본 타입 : ${h.items::class.simpleName}, 값 ${h.items}")
}
===== kotlinc ebf.kt =====
(exit 0)
===== kotlinc -language-version 2.3 ebf.kt =====
ebf.kt:3:9: error: the feature "explicit backing fields" is only available since language version 2.4
        field = mutableListOf<String>()
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
(exit 1)
===== java -cp oebf:kotlin-stdlib.jar EbfKt =====
H 바깥에서 본 타입 : ArrayList, 값 [a]
```

**출력** (`javap -p -s oebf/Holder.class`)

```text
Compiled from "ebf.kt"
public final class Holder {
  private final java.util.List<java.lang.String> items;
    descriptor: Ljava/util/List;
  public Holder();
    descriptor: ()V

  public final java.util.List<java.lang.String> getItems();
    descriptor: ()Ljava/util/List;

  public final void add(java.lang.String);
    descriptor: (Ljava/lang/String;)V
}
```

- ★★ **2.4.20 에서는 플래그도 opt-in 도 없이 컴파일된다**(경고 0건, `exit 0`).\
  그리고 **`-language-version 2.3` 으로 던지면 거부한다** — `only available since language version 2.4`.\
  ★ README 판 이력표의 **「16 explicit backing fields — 2.3.0 도입 → Stable 2.4.0」과 어긋나지 않는다.**\
  (이 환경에서 잴 수 있는 것은 「**2.4 부터**」까지다 — 2.4.0 과 2.4.20 중 어느 쪽에서 Stable 이 됐는지는 **못 잰다.**)
- ★ 필드 타입은 `java.util.List` 이고 **게터도 `List` 를 낸다.** 바깥에서 본 런타임 클래스는 `ArrayList` 다 —\
  **읽기 전용은 뷰일 뿐**이라는 사실이 여기서도 그대로다(정본은 목록의 **40번 주제**).
- ★ `add` 는 클래스 **안**이라 `MutableList` 로 보인다. 컴파일러가 두 타입을 자리마다 갈라 쓰는 것이다.

### (7) 확장 프로퍼티에는 애초에 서랍이 없다

[13번 주제](../13-extension-functions-and-properties/)에서 이미 본 사실이다 — **확장 프로퍼티는 정적 게터 하나**로 컴파일되고\
클래스 밖에 있으므로 **필드를 만들 자리 자체가 없다.**

- 그래서 `val Cup.cups: Int = ml / 200` 은 (2)에서 본 **같은 에러**로 막힌다.
- ★ 이 주제의 시각으로 다시 읽으면 이렇다 — **확장 프로퍼티는 「커스텀 게터만 있는 프로퍼티」의 극단이다.**\
  (1)의 `full` 과 같은 자리에 있고, 다만 **클래스 밖**이라 선택의 여지조차 없다.
- 정본은 그쪽이고 여기서는 **필드 유무라는 한 축으로 줄 세우는 것**까지만 한다.

## 문법 — 형태와 규칙

```kotlin
// 형태 — 프로퍼티 하나의 전체 문법
var 이름: 타입 = 초기값
    get() = field            // 게터 (없으면 기본)
    set(value) { field = value }   // 세터 (없으면 기본 · val 이면 못 쓴다)

val 계산: String get() = "…"   // field 를 안 쓴다 → 필드 없음 → 초기값 금지
lateinit var x: String         // var · 원시 아님 · 널 불가 · 초기화식 없음 · 기본 접근자
const val K: Int = 1           // 최상위 / object / companion · 원시 또는 String · 게터 금지

val items: List<String>        // 2.4+ explicit backing field
    field = mutableListOf()
```

- **`field` 는 접근자 안에서만** 쓸 수 있는 이름이다. 그 바깥에는 존재하지 않는다.
- **접근자가 `field` 를 한 번도 안 쓰면 필드가 안 생긴다** — 그러면 초기화식도 못 쓴다.
- **`val` 은 세터가 없다.** 커스텀 게터는 가질 수 있다.
- **가시성은 세터만 따로 줄 수 있다** — `var x: Int = 0; private set`.
- **`lateinit` 은 5가지 조건**을 전부 만족해야 한다((3)).
- **`const val` 은 원시 타입과 `String` 만**, 최상위·`object`·`companion object` 에서만.
- `::x.isInitialized` 는 **`lateinit` 프로퍼티**에, **backing field 가 보이는 자리**에서만.

## 어디서 틀리나

1. ★★★ **`const val` 을 버전·설정에 쓴다.** 라이브러리를 고쳐도 **호출부가 옛 값을 들고 있다**((5)).\
   재컴파일 전까지 조용히 틀린다.
2. ★★ **커스텀 게터를 달고 「저장되겠지」 한다.** 필드가 없다((1)). 게터가 **호출될 때마다 다시 계산**한다.
3. ★★ **세터에서 프로퍼티 이름을 쓴다.** `set(v) { age = v }` 는 **자기 세터를 다시 부른다**(무한 재귀).\
   `field` 를 써야 한다((2)).
4. ★ **`lateinit` 을 `Int` 에 붙인다.** 원시 타입에는 「아직」을 표시할 `null` 이 없다((3)).
5. ★ **`lateinit` 을 검사 없이 읽는다.** `UninitializedPropertyAccessException` 은\
   `NullPointerException` 이 아니라 **`kotlin` 패키지의 예외**라 catch 절을 잘못 쓰면 안 잡힌다((4)).
6. ★ **`var` 에 커스텀 접근자 둘 다 달고 `field` 를 안 쓴다.** 값이 조용히 버려진다((1)의 `initial`).
7. **`isInitialized` 를 클래스 밖에서 부른다.** `backing field … is not accessible` 로 막힌다((4)).

## 구현 세부사항 대 언어 보장

| 사실 | 어느 층인가 | 근거 |
|---|---|---|
| `field` 를 안 쓰면 **backing field 가 없다** | **언어 보장** | 공식 문서 · (1) 필드 목록 |
| 프로퍼티가 **접근자 한 쌍**으로 컴파일되는 것 | **언어 보장**(JVM 대상) | (1) |
| `lateinit` 의 **다섯 제약** | **언어 보장** | (3) — 에러 |
| `UninitializedPropertyAccessException` 이 나는 것 | **언어 보장** | (4) |
| `const val` 이 **호출부에 복사되는 것** | **언어 보장**(JVM `ConstantValue` 계약) | (5) — 두 번 실행 |
| `lateinit` 필드가 **`public`** 인 것 | ★ **이 판의 관찰** | (4) |
| `isInitialized` 가 **`getfield; ifnull`** 로 내려가는 것 | **JVM 구현** | (4) |
| 예외·에러 문구의 정확한 낱말 | ★ **이 컴파일러 버전** | 전부 |
| `= 0` 대입 생략 같은 최적화 | ★ **이 컴파일러** | [15번 주제](../15-class-declaration-constructors-and-init/) |
| explicit backing fields 가 **2.4 부터**인 것 | **언어 버전 게이트**(에러가 그렇게 말한다) | (6) |

- ★★ **가장 조심할 자리**: (5)는 **「구현이 그래서」가 아니라 언어가 약속한 것**이다.\
  `const` 의 **뜻 자체**가 「**컴파일 타임 상수**」라서 복사가 정상 동작이다.\
  그래서 「버전 올리면 고쳐지겠지」가 아니라 **설계 단계에서 `const` 를 안 쓰는 것**이 유일한 해법이다.
- ★ **`lateinit` 필드가 `public` 인 것은 관찰이다.** 「`lateinit` 은 캡슐화를 깬다」고 외우지 말고\
  **이 판에서 그렇더라**로 두고, 필요하면 다시 찍어 확인한다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 값을 저장한다 | 기본 접근자 `var`/`val` | 필드 + 접근자가 자동 |
| 다른 프로퍼티로 **매번 계산**한다 | 커스텀 게터(`field` 안 씀) | 상태를 두 군데 두지 않는다 |
| 값을 저장하되 **쓸 때 가공**한다 | 커스텀 세터 + `field` | 서랍은 있고 입구만 바꾼다 |
| **처음 쓸 때 한 번만** 계산한다 | `by lazy` | 계산이 비싸면 — [17번 주제](../17-delegated-properties/) |
| 생성 후 주입되는 참조 타입 값 | `lateinit var` | nullable 로 안 만들고 널 검사를 줄인다 |
| 생성 후 주입되는 **원시 타입** 값 | `Delegates.notNull()` | `lateinit` 이 못 붙는다 — [17번 주제](../17-delegated-properties/) |
| 절대 안 바뀌는 수·문자열 | `const val` | 호출부에 박혀도 문제없다 |
| **바뀔 수 있는** 수·문자열 | 일반 `val` | 박히면 안 된다((5)) |
| 바깥엔 읽기 전용, 안에선 가변 | `field = …`(2.4+) | 프로퍼티 하나로 끝난다((6)) |

## 핵심 문장

1. **프로퍼티는 접근자 한 쌍이고 필드는 딸려 오는 것이다.** 선언했다고 저장되는 게 아니다.
2. **`field` 를 안 쓰면 서랍이 안 생긴다** — 그리고 서랍이 없으면 초기화식도 못 쓴다.
3. **`field` 는 접근자 안에만 있는 이름**이다. 세터에서 프로퍼티 이름을 쓰면 무한 재귀다.
4. **`lateinit` 은 「필드가 `null` 이면 아직」으로 구현된다** — 제약 다섯이 전부 거기서 나온다.
5. **`isInitialized` 는 리플렉션이 아니라 `getfield; ifnull` 이다.**
6. ★★ **`const val` 은 호출부에 복사된다** — 라이브러리를 고쳐도 재컴파일 전에는 안 따라온다.
7. **확인 방법이 있다** — `javap -p` 로 **필드 목록**을 찍으면 서랍의 유무가 그대로 보인다.

## 관련 자료

- [15번 주제 — 클래스 선언·`init` 순서](../15-class-declaration-constructors-and-init/) — **그쪽은 필드가 언제 채워지나가 정본, 여기는 그 필드가 생기기는 하나.**
- [17번 주제 — 위임 프로퍼티](../17-delegated-properties/) — **그쪽은 `by lazy`·`observable`·`notNull` 이 정본, 여기는 `lateinit` 까지.**
- [13번 주제 — 확장 함수·확장 프로퍼티](../13-extension-functions-and-properties/) — **그쪽이 확장 프로퍼티의 정본**, 여기는 (7)에서 같은 축으로 줄 세우기만.
- [03번 주제 — null 안전 타입](../03-null-safe-types/) — **그쪽이 널 불가 보장의 정본**, 여기는 `lateinit` 이 그 보장을 **런타임으로 미루는** 도구라는 것만.
- [01번 주제 — `val`/`var` 와 기본 타입](../01-val-var-and-basic-types/) — 원시 타입과 박싱의 정본. (3)의 「원시 타입」 제약이 거기서 온다.
- 목록의 **35번 주제** — `@field:`/`@get:` use-site target. 애너테이션이 **필드에 붙나 게터에 붙나**.
- 목록의 **39번 주제** — `@JvmField`·`@JvmStatic`. 필드를 직접 노출하는 법.
- 목록의 **40번 주제** — 읽기 전용 컬렉션이 **뷰**라는 것((6)의 `ArrayList`).
- 목록의 **22번 주제** — `data class` 가 주 생성자 프로퍼티만 보는 것.

## 용어 풀이

- **프로퍼티(property)** — Kotlin 의 선언 단위. 게터(+세터)로 컴파일된다.
- **backing field** — 그 프로퍼티의 값을 저장하는 필드. `field` 로만 부를 수 있다.
- **접근자(accessor)** — 게터와 세터. Kotlin 에서는 프로퍼티 선언 안에 쓴다.
- **`lateinit`** — 「나중에 대입하겠다」는 표시. 대입 전 읽으면 예외.
- **`UninitializedPropertyAccessException`** — `kotlin` 패키지의 예외. `NPE` 가 아니다.
- **`const val`** — 컴파일 타임 상수. 호출부에 값이 복사된다.
- **`ConstantValue`** — JVM 클래스 파일의 필드 속성. 상수 복사를 허용하는 표시.
- **explicit backing field** — `field = …` 절로 **바깥 타입과 안쪽 타입을 갈라 적는** 문법(2.4+).
- **`ldc`** — 상수 풀의 값을 스택에 올리는 JVM 명령.
- **`getfield`/`putfield`** — 인스턴스 필드를 읽고 쓰는 JVM 명령.

## 더 들어가면

- **세터 가시성만 좁히기** — `var count: Int = 0; private set` 은 게터는 public, 세터는 private 인 쌍을 만든다.\
  (6)의 explicit backing field 와 **목적이 비슷하고 수단이 다르다** — 그쪽은 **타입**을 가르고 이쪽은 **가시성**을 가른다.\
  ★ **이 문서는 `private set` 의 바이트코드를 찍어 보지 않았다.**
- ★ **`lateinit` 의 「아직」 표시가 `null` 이라는 것**은 (4)의 게터 바이트코드로 확인했지만,\
  **`@JvmField` 를 붙인 `lateinit`** 이나 **상속받은 `lateinit`** 은 이 문서에서 **안 던져 봤다.**
- **`const` 와 `ConstantValue` 는 Java 의 「상수 변수」와 같은 장치**다. Java 쪽에서 같은 사고가 나는 자리는\
  [`../../../java/syntax/06-initialization-order/`](../../../java/syntax/06-initialization-order/)의 「컴파일 타임 상수는 필드 읽기가 아니다」 절이 정본이다.
- **위임 프로퍼티는 필드가 「값」이 아니라 「위임 객체」를 담는다** — `x$delegate` 다.\
  이 문서의 필드 목록 시각으로 [17번 주제](../17-delegated-properties/)를 읽으면 한 축으로 이어진다.
