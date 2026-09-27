# kotlin/syntax/16 — 프로퍼티: backing field·커스텀 접근자·`lateinit`·`const` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러·예외·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javap` 에서 실제로 얻었다.\
> 역어셈블은 **기본 `-jvm-target`(1.8 · `major version: 52`)** 이 정본이다.\
> **4번은 라이브러리와 앱을 따로 컴파일해 「라이브러리만 다시 빌드」를 실제로 재현한 것이다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 필드는 **다섯**, 접근자는 **열둘** — `full` 과 `initial` 은 서랍이 없다

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

**왜 그런가**

- ★★★ 필드는 `first`·`last`·`age`·`nickname`·`note` **다섯**이다.\
  `full`·`initial` 은 **필드가 없는데 접근자는 있다** — `getFull()`·`getInitial()`·`setInitial()`.
- ★★ 기준은 「**접근자가 `field` 라는 이름을 쓰느냐**」 하나다.\
  `nickname` 은 게터·세터 둘 다 쓰고, `note` 는 **세터만 커스텀이고 게터가 기본**이라 생긴다.\
  `age`·`first`·`last` 는 접근자가 통째로 기본이라 당연히 생긴다.
- ★ **`initial` 은 `var` 인데 필드가 없다.** 세터가 값을 그냥 버리는데 **컴파일러는 아무 말도 안 했다**(`exit 0`).\
  「`var` 니까 저장된다」는 틀린 전제다.
- 접근자는 `getFirst`·`getLast`·`getAge`/`setAge`·`getFull`·`getNickname`/`setNickname`·`getNote`/`setNote`·`getInitial`/`setInitial` **열둘**이다.
- ★ 한 문장으로: 「**접근자 중 하나라도 `field` 를 쓰거나 기본 접근자가 남아 있으면 서랍이 생긴다.**」

### 2. ★★ 에러 **여덟 건**, 문구 **다섯 가지**

**출력** (`kotlinc badlateinit.kt -d obl`)

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

**출력** (`kotlinc badlateinit2.kt -d obl2`)

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

**왜 그런가**

| 거부된 선언 | 문구 |
|---|---|
| `Int` · `Double` · `Boolean` | `'lateinit' modifier is not allowed on properties of primitive types.` |
| `String?` · `T`(상한 없음) | `'lateinit' modifier is not allowed on properties of a type with nullable upper bound.` |
| `val v` | `'lateinit' modifier is allowed only on mutable properties.` |
| `= "a"` | `'lateinit' modifier is not allowed on properties with initializer.` |
| `get() = "x"` | `'lateinit' modifier is not allowed on properties with a custom getter or setter.` |

- ★★ **`T` 는 상한을 안 쓰면 `Any?`** 라서 nullable 로 걸린다. **`<T : Any>`** 로 바꾸면 통과한다.
- ★★ **제약이 전부 구현에서 나온다** — `lateinit` 은 「**필드가 `null` 이면 아직 초기화 안 됨**」으로 구현된다(3번).\
  원시 타입에는 `null` 이 없고, nullable 타입에서는 `null` 이 **정상 값**이라 구분이 안 되고,\
  `val` 은 나중에 대입할 수 없고, 초기화식이 있으면 「아직」이 아니고, **커스텀 접근자는 필드를 안 만들 수도 있다**(1번).
- ★ 클래스 프로퍼티만이 아니라 **지역 변수(1.2+)와 최상위 변수**에도 붙는다.

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

### 3. ★★ `아직` · `kotlin.UninitializedPropertyAccessException` · **`public` 필드** · `getfield; ifnull`

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

**왜 그런가**

- ★★ 예외 이름은 **`kotlin.UninitializedPropertyAccessException`** 이다. **`NullPointerException` 이 아니다** —\
  `catch (e: NullPointerException)` 으로는 **안 잡힌다.** 메시지에 **프로퍼티 이름**이 들어 있다.
- ★★ **필드가 `public java.lang.String conn`** 이다. 1번의 다른 프로퍼티는 전부 `private` 인데 여기만 다르다.\
  「아직 대입 안 됨」을 밖에서도 읽을 수 있어야 하기 때문이다(★ **이 판의 관찰**이다).
- ★★★ **`::conn.isInitialized` 는 리플렉션이 아니다.** `status()` 의 바이트코드가 `getfield conn; ifnull` 로 시작한다 —\
  컴파일러가 **널 검사 한 줄로 바꿔 놓았다.** `KProperty` 객체도 안 만든다.
- ★ 게터는 `getfield → dup → ifnull → areturn` 이고, 널이면 `throwUninitializedPropertyAccessException("conn")` 이다.\
  **「필드가 `null` 인가」로 판정한다**는 것이 여기 그대로 있다 — 2번의 제약 전부가 이 세 명령에서 나온다.
- `E : 8` 은 `"jdbc:..."` 의 길이다 — 대입 후에는 평범한 필드 읽기가 된다.

### 4. ★★★ `F` 는 **`1.0` 그대로**, `G` 만 `2.0` — `ConstantValue` 때문이다

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

**왜 그런가**

- ★★★ **`F` 줄은 `ldc "F const val VERSION : 1.0"` 하나다.** `Config` 라는 이름조차 안 나온다 —\
  **보간 문자열째 컴파일 타임에 접혔다.**\
  `G` 줄은 `new StringBuilder` → `getstatic Config.INSTANCE` → `invokevirtual Config.getBUILD()` 로\
  **실행 시점에 라이브러리에 물어본다.**
- ★★★ 그래서 라이브러리를 `2.0` 으로 고쳐 **라이브러리만** 다시 컴파일하면 **`G` 만 따라오고 `F` 는 `1.0` 에 남는다.**\
  앱을 다시 컴파일하기 전까지 **조용히 옛 값**이다.
- ★★ 이것을 허용하는 속성 이름이 **`ConstantValue`** 다. `javap -v` 에 `ConstantValue: String 2.0` 이 보인다 —\
  JVM 명세가 「이 값을 호출부에 복사해도 된다」고 정해 둔 표시이고, **`const val` 이 그것을 켠다.**
- ★ 필드 모양도 다르다 — `VERSION` 은 **`public static final`** 이고 `BUILD` 는 `private static final` + `getBUILD()` 다.
- ★ 그래서 **버전 문자열·설정 키·기능 플래그에 `const` 를 쓰면 안 된다.**\
  반대로 **절대 안 바뀌는 것**(수학 상수·프로토콜 매직 넘버)에는 맞다.

### 5. ★ 에러 **3건** — 셋 다 **복사할 값이 없어서**다

**출력** (`kotlinc badconst.kt -d obc`)

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

**왜 그런가**

| 거부된 것 | 문구 | 왜 |
|---|---|---|
| 클래스 안 | `const 'val' is only allowed on top level, in named objects, in companion objects or companion blocks.` | 인스턴스마다 달라질 수 있다 |
| `List<Int>` | `const 'val' has type 'List<Int>'. Only primitive types and 'String' are allowed.` | 객체는 상수 풀에 못 넣는다 |
| 게터 | `const 'val' cannot have a getter.` | 계산이면 컴파일 타임 값이 없다 |

- ★ 공통점은 「**컴파일 타임에 호출부로 복사할 값이 없다**」이다. `ConstantValue` 에 넣을 것이 없으면 `const` 가 성립하지 않는다.
- 쓸 수 있는 자리는 **최상위 · `object` · `companion object`(그 안의 `companion` 블록 포함)** 이고,\
  타입은 **원시 타입과 `String`** 뿐이다.
- ★ 가시성도 다르다 — `const val` 은 **필드를 직접 public 으로 노출**하고, 일반 `val` 은 **게터를 거친다**(4번).

### 6. ★ 된다 — **플래그도 경고도 없이**, 그리고 `-language-version 2.3` 은 거부한다

**출력** (`kotlinc ebf.kt` · `-language-version 2.3` · 실행)

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

**왜 그런가**

- ★★ 2.4.20 에서는 **opt-in 도 플래그도 없이 `exit 0`** 이다. 경고 한 줄 없다.
- ★★ **`-language-version 2.3` 으로 던지면 명확히 말한다** —\
  `the feature "explicit backing fields" is only available since language version 2.4`.\
  ★ **README 판 이력표의 「2.3.0 도입 → Stable 2.4.0」과 어긋나지 않는다.**\
  ★ 다만 이 환경에서 **잴 수 있는 것은 「2.4 부터」까지**다 — 2.4.0 과 2.4.20 중 어디서 Stable 이 됐는지는 **못 잰다**\
  (`kotlinc` 가 한 판뿐이고 `-language-version` 은 **언어 버전**만 가른다).
- ★ 필드 타입은 `java.util.List` 이고 게터도 `List` 를 낸다. 그런데 **`H` 의 런타임 클래스는 `ArrayList`** 다 —\
  **읽기 전용은 별도 객체가 아니라 뷰**라는 사실이 여기서도 그대로다(정본은 [목록의 **40번 주제**](../40-read-only-collections-and-runtime-types/)).
- 클래스 **안**의 `add` 에서는 `MutableList` 로 보여 `items.add(s)` 가 통과한다.
- ★ 대체한 예전 관용구는 **private 백킹 프로퍼티 + public 게터** 두 개를 선언하는 것이다 —\
  `private val _items = mutableListOf<String>()` / `val items: List<String> get() = _items`.

### 7. `field` 는 **접근자 안에만** 있다 — 밖에서는 없는 이름이다

**출력** (`kotlinc fieldout.kt -d ofo`)

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

**출력** (`kotlinc nofield.kt -d onf`)

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

**왜 그런가**

- ★ 메서드 안에서 `field` 를 쓰면 **`unresolved reference 'field'`** 다 — 두 번 썼으니 에러도 2건이다.
- ★ 세터 안에서 **프로퍼티 이름**을 쓰면 컴파일은 되지만 **자기 세터를 다시 부른다**(무한 재귀).\
  그래서 `set(value) { field = value }` 라고 써야 한다.
- ★★ 커스텀 게터만 있는 프로퍼티에 `= "x"` 를 붙이면\
  **`initializer is prohibited here because this property has no backing field.`** 다.\
  ★ 이 문구가 **1번의 답을 컴파일러 입으로 다시 말한 것**이다 — 「서랍이 없으니 넣을 데가 없다」.

### 8. 둘 다 막힌다 — `lateinit` 이어야 하고 **필드가 보이는 자리**여야 한다

**출력** (`kotlinc badinit.kt -d obi`)

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

**왜 그런가**

- 첫째 — `this declaration can only be called on a reference to a 'lateinit' property.`\
  **`lateinit` 이 아닌 프로퍼티에는 못 쓴다.** 그쪽은 「아직」이라는 상태가 없기 때문이다.
- 둘째 — `backing field of 'var conn: String' is not accessible at this point.`\
  **backing field 에 접근할 수 있는 자리에서만** 쓸 수 있다. 3번에서 본 대로 `isInitialized` 는\
  **`getfield` 한 줄**이라, 그 필드가 안 보이는 자리에서는 성립하지 않는다.
- ★ 그래서 바깥에 알려야 하면 **클래스가 직접 `fun isReady(): Boolean = ::conn.isInitialized` 같은 것을 내줘야** 한다\
  (3번의 `status()` 가 그 모양이다).

### 9. 게터 세 명령이 제약 다섯을 전부 설명한다

**왜 그런가**

```text
   getConn()
     getfield conn        ← 필드를 읽고
     ifnull ──▶ throwUninitializedPropertyAccessException("conn")
     areturn              ← 널이 아니면 그대로 돌려준다
```

| 제약 | 이 구현에서 어떻게 따라 나오나 |
|---|---|
| 원시 타입 금지 | `int`·`double` 에는 **`null` 이라는 값이 없다** — 「아직」을 표시할 수가 없다 |
| nullable 금지 | `String?` 에서는 **`null` 이 정상 값**이다 — 「아직」과 구분이 안 된다 |
| `val` 금지 | 나중에 `putfield` 할 수 없다 |
| 초기화식 금지 | 이미 값이 들어가면 「아직」인 구간이 없다 |
| 커스텀 접근자 금지 | **접근자가 `field` 를 안 쓰면 필드 자체가 없다**(1번) — 검사할 대상이 사라진다 |

- ★ 그래서 **원시 타입을 늦게 주입해야 하면 `lateinit` 이 아니라 `Delegates.notNull()`** 이다 —\
  그쪽은 필드에 **박싱된 `Integer?`** 를 담아 「아직」을 표현한다([17번 주제](../17-delegated-properties/)).

### 10. 읽을 때마다 **다시 계산한다**

**왜 그런가**

- 커스텀 게터만 있는 프로퍼티는 **호출될 때마다 본문이 돈다.** 1번의 `full` 은 매번 문자열을 새로 만든다.
- ★ 문제가 되는 상황은 셋이다 — ① 계산이 **비싸고** 자주 읽힐 때 ② 계산에 **부수 효과**가 있을 때\
  ③ 호출마다 **다른 값**이 나와 `==` 나 캐시가 어긋날 때.
- ★ 「한 번만 계산하고 저장」은 **`by lazy`** 다 — 정본은 [17번 주제](../17-delegated-properties/).
- ★ 원시 타입을 늦게 주입해야 하면 **`Delegates.notNull()`** 이다(9번). 정본도 [17번 주제](../17-delegated-properties/)다.

### 11. 확장 프로퍼티는 **「서랍이 없는 칸」의 극단**이다

**왜 그런가**

- `val Cup.cups: Int = ml / 200` 은 **7번과 같은 에러**(`… has no backing field`)로 막힌다.\
  실제 전문과 「그 에러가 몇 줄인지」는 [13번 주제](../13-extension-functions-and-properties/)가 정본이다.
- 확장 프로퍼티는 **파일 클래스의 정적 게터**(`getLabel(Money)`)로 컴파일된다 — 클래스 밖이라 **필드를 만들 자리가 없다.**\
  정본은 [13번 주제](../13-extension-functions-and-properties/).

| 칸 | 필드 | 접근자 | 예 |
|---|---|---|---|
| 저장하는 프로퍼티 | 있다 | 있다 | `var age: Int = 0` |
| 계산 프로퍼티 | **없다** | 있다 | `val full get() = …` |
| **확장 프로퍼티** | **없다(선택의 여지도 없다)** | 있다(정적) | `val Money.label get() = …` |
| **위임 프로퍼티** | 있다 — 단 **값이 아니라 위임 객체**가 들어 있다 | 있다 | `val url by lazy { … }` |

- ★ 위임 프로퍼티의 필드는 **`url$delegate`** 이고 그 안에 `kotlin.Lazy` 객체가 들어 있다 —\
  정본은 [17번 주제](../17-delegated-properties/)다.

## 실행 검증

```text
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
openjdk version "21.0.5" 2024-10-15 LTS
OpenJDK Runtime Environment Temurin-21.0.5+11 (build 21.0.5+11-LTS)
OpenJDK 64-Bit Server VM Temurin-21.0.5+11 (build 21.0.5+11-LTS, mixed mode, sharing)
```

★ **흔들리는 칸과 안 흔들리는 칸**(제출 전 재대조에서 「고칠 것」과 「설계상 다른 것」을 가르는 선언이다)

| 흔들린다 | 안 흔들린다 |
|---|---|
| **없다** — 이 문서의 블록은 전부 결정적이다(예외를 **잡아서 타입과 메시지만** 찍었고 스택 트레이스를 싣지 않았다) | `javap` 출력 **전체** · 예외 타입과 메시지 본문 · 에러 문구 · 종료 코드 · 두 번에 걸친 `const` 실행 결과 |

> 근거 — **캡처 스크립트를 두 번 돌려 블록 82개를 바이트 단위로 대조**했고, 이 주제의 블록은 한 글자도 안 갈렸다.

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `fields.kt` | **필드 5개 · 접근자 12개** — `full`·`initial` 에 서랍이 없는 것 | `kotlinc` → `javap -p -s` |
| `nofield.kt` | 서랍이 없으면 **초기화식이 금지되는 것** | `kotlinc` (컴파일 실패가 결과) |
| `fieldout.kt` | `field` 가 **접근자 밖에는 없는 이름**인 것(에러 2건) | `kotlinc` (컴파일 실패가 결과) |
| `badlateinit.kt` · `badlateinit2.kt` | `lateinit` 제약 — **에러 8건 · 문구 5가지** | `kotlinc` 2회 (컴파일 실패가 결과) |
| `latescope.kt` | `lateinit` 이 **지역 변수·최상위**에도 붙는 것(`F`) | `kotlinc` → `java` |
| `late.kt` | `A`\~`E` · 예외 이름과 메시지 · **필드가 `public`** · `isInitialized` 가 `getfield; ifnull` 인 것 | `kotlinc` → `java` · `javap -p -s` · `javap -c -p` |
| `badinit.kt` | `isInitialized` 의 **두 가지 제약**(에러 2건) | `kotlinc` (컴파일 실패가 결과) |
| `lib.kt` · `app.kt` | `F`·`G` — **`const` 가 호출부에 박히는 것** · `ConstantValue` · 필드 가시성 | `kotlinc` 3회(lib 2벌) → `java` 2회 · `javap -c -p` · `javap -p -s` · `javap -v -p` |
| `badconst.kt` | `const` 를 못 쓰는 **세 자리**(에러 3건) | `kotlinc` (컴파일 실패가 결과) |
| `ebf.kt` | explicit backing field 가 **2.4.20 에서 통과**하고 **2.3 에서 거부되는 것**(`H`) | `kotlinc` 2회(언어 버전 2벌) → `java` · `javap -p -s` |

**구현 의존 항목** — 필드·접근자의 이름과 순서, `lateinit` 필드가 `public` 인 것,
`isInitialized` 가 `getfield; ifnull` 로 내려가는 것, `F` 줄이 보간 문자열째 접힌 것, 상수 풀 번호,
에러·예외 문구의 낱말 — **전부 이 컴파일러 버전의 산출물**이다.\
반면 **「`field` 를 안 쓰면 backing field 가 없다」·「`lateinit` 의 다섯 제약」·
「초기화 전 접근은 `UninitializedPropertyAccessException`」·「`const val` 은 호출부에 복사된다」·
「`const` 는 원시 타입과 `String` 만, 최상위·object·companion 에서만」·
「explicit backing fields 는 언어 버전 2.4 부터」** 는 **언어 규칙**이라 타깃과 무관하다.

**★ 던져 봤더니 예상과 달랐던 것 — 세 건**

1. ★★★ **`const` 가 「필드 읽기를 상수 읽기로 바꾸는」 정도가 아니었다.** `F` 줄은
   **보간 문자열 전체가 하나의 `ldc`** 로 접혔다 — `Config` 라는 이름이 호출부 바이트코드에 **아예 없다.**
   그래서 「라이브러리를 바꾸면 최소한 다시 연결은 되겠지」가 성립하지 않는다. **연결할 것 자체가 없다.**
2. ★★ **`lateinit` 의 backing field 가 `public` 이었다.** 같은 클래스의 다른 프로퍼티는 전부 `private` 인데
   `conn` 만 `public java.lang.String` 이다. 「프로퍼티는 항상 private 필드 + 접근자」라는 전제가 여기서 깨진다.
3. ★ **`::conn.isInitialized` 에 리플렉션이 없었다.** `KProperty` 를 만들 줄 알았는데
   `getfield conn; ifnull` 두 명령이 전부였다. `::` 라는 표기만 보고 비용을 짐작하면 틀린다.

**안 걸린 것도 출력이다** — `fields.kt` 의 `initial` 은 **`var` 인데 세터가 값을 버린다.**
컴파일러는 **경고도 에러도 없이 `exit 0`** 이었다. 「저장이 안 되고 있다」를 알려 주는 것은
컴파일러가 아니라 **`javap -p` 의 필드 목록**뿐이다.
