# kotlin/syntax/17 — 위임 프로퍼티: `by lazy`·`observable`·`Map` 위임 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Delegated properties](https://kotlinlang.org/docs/delegated-properties.html) · [`kotlin.Lazy` / `lazy()`](https://kotlinlang.org/api/core/kotlin-stdlib/kotlin/-lazy/) · [`kotlin.properties.Delegates`](https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.properties/-delegates/) · [Properties](https://kotlinlang.org/docs/properties.html).
> **실행 검증** — 이 문서의 모든 출력·에러·예외·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javap` 에서 실제로 얻었다.\
> `kotlinc` 9회(컴파일 실패 2벌) · `java` 17회(그중 **12회는 같은 프로그램을 되풀이 돌린 것**) · `javap` 8회.\
> **stdlib 의 `Lazy` 구현 세 벌은 `kotlin-stdlib.jar` 를 풀어 직접 역어셈블했다.**
> ⚠️ **`-jvm-target` 을 밝히지 않은 바이트코드 주장은 반쪽이다.** 이 문서의 역어셈블은 전부 **기본값 1.8**(`major version: 52`)이다.
> ⚠️ **되풀이 돌리면 달라지는 블록이 하나 있다**((4)의 스레드 실험). 그 자리에 **대조할 것이 무엇인지** 적어 두었고,
> 전체 선언표는 3-answer 의 「흔들리는 칸 / 안 흔들리는 칸」이다.
> **버전** — `by`·`lazy`·`Delegates.observable`/`vetoable`/`notNull`·`Map` 위임은 전부 **1.0** 이다.\
> `LazyThreadSafetyMode` 도 1.0 이고, 그 뒤로 기본값이 바뀐 적이 없다(이 문서는 **2.4.20 에서 직접 확인**했다).
> **경계** — backing field 와 커스텀 접근자는 [16번 주제](../16-properties-backing-field-lateinit-const/)가, 초기화 시점은 [15번 주제](../15-class-declaration-constructors-and-init/)가,\
> `inline` 이 무엇을 없애는지는 [11번 주제](../11-inline-functions/)가, 연산자 규약 전반은 목록의 **31번 주제**,\
> **클래스** 위임(`class A : B by b`)은 목록의 **21번 주제**가 정본이다 — 여기는 **프로퍼티** 위임만 다룬다.
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**`by` 는 「이 프로퍼티를 읽고 쓰는 일을 저 객체에게 맡긴다」는 선언이다.**

[16번 주제](../16-properties-backing-field-lateinit-const/)에서 프로퍼티는 **접근자 한 쌍 + (있을 수도 없을 수도 있는) 서랍**이었다.\
위임 프로퍼티는 그 중간에 **대리인 객체**를 하나 끼운다 — **서랍에는 값이 아니라 대리인이 들어간다.**

> **위임 객체(delegate)** — `by` 뒤에 오는 객체. `getValue`/`setValue` 라는 **연산자 규약**을 가진다.\
> **연산자 규약(operator convention)** — 「이 이름과 이 시그니처의 함수가 있으면 이 문법이 풀린다」는 약속.\
> 인터페이스를 구현할 필요가 없다 — **이름과 모양만 맞으면 된다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 창구 뒤에 앉은 대리인 | 위임 객체 — `x$delegate` 필드에 들어간다 |
| 손님이 물으면 대리인이 답한다 | `getValue(thisRef, property)` |
| 손님이 맡기면 대리인이 받는다 | `setValue(thisRef, property, value)` |
| 대리인에게 건네는 신분증 | `KProperty` — 어느 프로퍼티인지 알려 주는 객체 |
| 신분증을 미리 만들어 벽에 걸어 둔다 | `$$delegatedProperties` — 클래스당 정적 배열 |
| 처음 물을 때만 창고에 다녀오고 그 뒤엔 외운다 | `by lazy` |
| 다녀오는 동안 문을 잠근다 / 여럿이 다녀와도 하나만 채택 / 안 잠근다 | `SYNCHRONIZED` / `PUBLICATION` / `NONE` |
| 맡길 때마다 상부에 보고한다 | `Delegates.observable` |
| 맡긴 것을 퇴짜 놓을 수 있다 | `Delegates.vetoable` |
| 서류철 자체를 대리인으로 쓴다 | `Map` 위임 |

```text
   val url: String by lazy { … }

   getUrl()                      url$delegate (필드)
   ┌───────────────┐             ┌──────────────────────┐
   │ getfield      │────────────▶│ kotlin.Lazy 객체       │
   │  url$delegate │             │  initializer: Function0│
   │ Lazy.getValue()│◀───────────│  _value: 아직 없음     │
   └───────────────┘             └──────────────────────┘
                                          │ 첫 호출에만
                                          ▼
                                    initializer 실행 → _value 에 저장
```

**서랍에 값이 아니라 대리인이 들어 있다는 것 하나가 이 주제의 전부다.**

## 이 주제가 답하려는 질문

1. `by` 는 **무엇으로 풀리나** — 인터페이스인가 규약인가, 그리고 필드에는 무엇이 들어가나.
2. `by lazy` 의 **기본 스레드 모드**는 무엇이고 세 모드가 각각 **무엇을 보장하나**.
3. 위임이 **언제 터지나** — 컴파일 타임인가 런타임인가.

## 동작 방식

### (1) ★★ `by` 는 **인터페이스가 아니라 규약**으로 풀린다

**언제 쓰나** — 남이 만든 위임을 쓰다가 직접 하나 만들어야 할 때.

`Loud` 는 아무 인터페이스도 구현하지 않는다. `getValue`/`setValue` 를 `operator` 로 선언했을 뿐이다.

```text
===== 소스: custom.kt =====
import kotlin.reflect.KProperty

class Loud(private var stored: String) {
    operator fun getValue(thisRef: Any?, property: KProperty<*>): String {
        println("   getValue  — thisRef=${thisRef?.let { it::class.simpleName }}, property.name=${property.name}")
        return stored
    }

    operator fun setValue(thisRef: Any?, property: KProperty<*>, value: String) {
        println("   setValue  — property.name=${property.name}, value=$value")
        stored = value
    }
}

class Screen {
    var title: String by Loud("처음")
}

fun main() {
    val s = Screen()
    println("A 읽는다")
    println("   결과 : ${s.title}")
    println("B 쓴다")
    s.title = "바뀜"
    println("C 다시 읽는다")
    println("   결과 : ${s.title}")
}
```

**출력** (`java -cp ocustom:kotlin-stdlib.jar CustomKt`)

```text
A 읽는다
   getValue  — thisRef=Screen, property.name=title
   결과 : 처음
B 쓴다
   setValue  — property.name=title, value=바뀜
C 다시 읽는다
   getValue  — thisRef=Screen, property.name=title
   결과 : 바뀜
```

```text
   s.title              →  Loud.getValue(thisRef = s, property = KProperty(name="title"))
   s.title = "바뀜"      →  Loud.setValue(thisRef = s, property = …,  value = "바뀜")
                                             ↑                ↑
                                       누구의 프로퍼티냐   어느 프로퍼티냐
```

그림 해설:

- ★★ **`ReadWriteProperty` 를 구현하지 않았는데 돌았다.** Kotlin 은 **이름과 시그니처만 본다** —\
  이것이 「연산자 규약」이다(목록의 **31번 주제**가 규약 전반의 정본).
- ★ **`thisRef` 가 `Screen`** 이다 — 위임 객체가 **누구의 프로퍼티인지** 알 수 있다.\
  최상위·지역 프로퍼티면 `null` 이 온다.
- ★★ **`property.name` 이 `"title"`** 이다. 위임 객체 하나를 여러 프로퍼티가 공유해도 **누가 물었는지 구분**할 수 있다.\
  `Map` 위임((6))이 정확히 이 이름을 키로 쓴다.
- ★ 읽을 때마다 `getValue` 가 돈다 — **`by` 는 캐시가 아니다.** 캐시는 `lazy` 가 하는 일이다.

규약을 안 지키면 컴파일러가 **요구 시그니처를 그대로 불러 준다.**

```text
===== 소스: badby.kt =====
class Plain(var stored: String)

class Screen {
    var title: String by Plain("x")
}
===== kotlinc badby.kt =====
badby.kt:4:23: error: type 'Plain' has no method 'getValue(Screen, KMutableProperty1<*, *>)', so it cannot serve as a delegate.
    var title: String by Plain("x")
                      ^^
badby.kt:4:23: error: type 'Plain' has no method 'setValue(Screen, KMutableProperty1<*, *>, String)', so it cannot serve as a delegate for var (read-write property).
    var title: String by Plain("x")
                      ^^
(exit 1)
```

```text
===== 소스: badby2.kt =====
import kotlin.reflect.KProperty

class ReadOnly(private val stored: String) {
    operator fun getValue(thisRef: Any?, property: KProperty<*>): String = stored
}

class Screen {
    var title: String by ReadOnly("x")
}
===== kotlinc badby2.kt =====
badby2.kt:8:23: error: type 'ReadOnly' has no method 'setValue(Screen, KMutableProperty1<*, *>, String)', so it cannot serve as a delegate for var (read-write property).
    var title: String by ReadOnly("x")
                      ^^
(exit 1)
```

- ★★ 에러 문구가 **필요한 메서드의 시그니처를 통째로 적어 준다** —\
  `getValue(Screen, KMutableProperty1<*, *>)` · `setValue(Screen, KMutableProperty1<*, *>, String)`.\
  **규약이 무엇인지 외울 필요가 없다 — 던져 보면 알려 준다.**
- ★ `val` 이면 `getValue` 만, `var` 면 **둘 다** 필요하다. 두 번째 파일이 그 경우다.

### (2) ★★★ 필드는 `x$delegate` 가 되고 **`KProperty` 는 미리 만들어 둔다**

**언제 쓰나** — 「`by` 를 쓰면 비용이 얼마나 드나」가 궁금할 때. **이 주제의 네 번째 창이다.**

```text
===== 소스: dcode.kt =====
import kotlin.properties.Delegates

class Conf {
    val url: String by lazy { "http://x" }
    var level: Int by Delegates.observable(0) { _, old, new ->
        println("   level $old -> $new")
    }
}
```

**출력** (`javap -p -s odcode/Conf.class`)

```text
Compiled from "dcode.kt"
public final class Conf {
  static final kotlin.reflect.KProperty<java.lang.Object>[] $$delegatedProperties;
    descriptor: [Lkotlin/reflect/KProperty;
  private final kotlin.Lazy url$delegate;
    descriptor: Lkotlin/Lazy;
  private final kotlin.properties.ReadWriteProperty level$delegate;
    descriptor: Lkotlin/properties/ReadWriteProperty;
  public Conf();
    descriptor: ()V

  public final java.lang.String getUrl();
    descriptor: ()Ljava/lang/String;

  public final int getLevel();
    descriptor: ()I

  public final void setLevel(int);
    descriptor: (I)V

  private static final java.lang.String url_delegate$lambda$0();
    descriptor: ()Ljava/lang/String;

  static {};
    descriptor: ()V
}
```

**출력** (`javap -c -p odcode/Conf.class` — 접근자와 정적 초기화)

```text
  public final java.lang.String getUrl();
    Code:
       0: aload_0
       1: getfield      #37                 // Field url$delegate:Lkotlin/Lazy;
       4: astore_1
       5: aload_1
       6: invokeinterface #74,  1           // InterfaceMethod kotlin/Lazy.getValue:()Ljava/lang/Object;
      11: checkcast     #76                 // class java/lang/String
      14: areturn

  public final int getLevel();
    Code:
       0: aload_0
       1: getfield      #60                 // Field level$delegate:Lkotlin/properties/ReadWriteProperty;
       4: aload_0
       5: getstatic     #82                 // Field $$delegatedProperties:[Lkotlin/reflect/KProperty;
       8: iconst_0
       9: aaload
      10: invokeinterface #85,  3           // InterfaceMethod kotlin/properties/ReadWriteProperty.getValue:(Ljava/lang/Object;Lkotlin/reflect/KProperty;)Ljava/lang/Object;
      15: checkcast     #87                 // class java/lang/Number
      18: invokevirtual #90                 // Method java/lang/Number.intValue:()I
      21: ireturn

  public final void setLevel(int);
    Code:
       0: aload_0
       1: getfield      #60                 // Field level$delegate:Lkotlin/properties/ReadWriteProperty;
       4: aload_0
       5: getstatic     #82                 // Field $$delegatedProperties:[Lkotlin/reflect/KProperty;
       8: iconst_0
       9: aaload
      10: iload_1
      11: invokestatic  #49                 // Method java/lang/Integer.valueOf:(I)Ljava/lang/Integer;
      14: invokeinterface #96,  4           // InterfaceMethod kotlin/properties/ReadWriteProperty.setValue:(Ljava/lang/Object;Lkotlin/reflect/KProperty;Ljava/lang/Object;)V
      19: return

  private static final java.lang.String url_delegate$lambda$0();
    Code:
       0: ldc           #99                 // String http://x
       2: areturn

  static {};
    Code:
       0: iconst_1
       1: anewarray     #102                // class kotlin/reflect/KProperty
       4: astore_0
       5: aload_0
       6: iconst_0
       7: new           #104                // class kotlin/jvm/internal/MutablePropertyReference1Impl
      10: dup
      11: ldc           #2                  // class Conf
      13: ldc           #106                // String level
      15: ldc           #108                // String getLevel()I
      17: iconst_0
      18: invokespecial #111                // Method kotlin/jvm/internal/MutablePropertyReference1Impl."<init>":(Ljava/lang/Class;Ljava/lang/String;Ljava/lang/String;I)V
      21: aastore
      22: aload_0
      23: putstatic     #82                 // Field $$delegatedProperties:[Lkotlin/reflect/KProperty;
      26: return
}
```

```text
   클래스 Conf
   ┌────────────────────────────────────────────────────────────┐
   │ static $$delegatedProperties : KProperty[]   ← 길이 1 ★     │
   │        [0] = MutablePropertyReference1Impl(Conf, "level",   │
   │                                            "getLevel()I")   │
   │ private final url$delegate   : kotlin.Lazy                  │
   │ private final level$delegate : ReadWriteProperty            │
   └────────────────────────────────────────────────────────────┘

   getUrl()   : getfield url$delegate   → Lazy.getValue()            ← 인자 없음 ★
   getLevel() : getfield level$delegate → ReadWriteProperty.getValue(
                                            this, $$delegatedProperties[0])
   setLevel() : … ReadWriteProperty.setValue(this, [0], Integer.valueOf(v))
```

그림 해설:

- ★★★ **프로퍼티마다 `<이름>$delegate` 필드가 하나씩 생긴다.** [16번 주제](../16-properties-backing-field-lateinit-const/)의 서랍 자리에\
  **값이 아니라 위임 객체**가 들어 있다.
- ★★★ **`$$delegatedProperties` 의 길이가 `1` 이다**(`iconst_1; anewarray`). 위임 프로퍼티가 둘인데 하나다.\
  **`by lazy` 는 `KProperty` 를 안 쓰기 때문**이다 — `getUrl()` 은 `Lazy.getValue()` 를 **인자 없이** 부른다.\
  stdlib 의 `Lazy.getValue` 확장이 `inline` 이라 **`this.value` 로 접힌 것**이다.
- ★★ 일반 위임은 다르다 — `getLevel()` 은 **`this` 와 `$$delegatedProperties[0]` 을 넘긴다.**\
  그 배열은 **`static {}` 에서 한 번 만들어 둔다** — 호출마다 만드는 것이 아니다.
- ★ 배열 원소는 **`MutablePropertyReference1Impl(Conf.class, "level", "getLevel()I", 0)`** 이다.\
  (1)에서 람다가 받은 `property.name` 이 여기서 온다.
- ★ `getLevel()` 에 `checkcast Number; intValue()` 가 붙는다 — **`Int` 가 박싱된다.**\
  위임 인터페이스가 제네릭이라 **원시 타입이 그대로 못 지나간다**([12번 주제](../12-reified-type-parameters/)).
- ★ 비용 이야기는 **구조까지만** 한다 — 「객체가 프로퍼티마다 하나」·「`KProperty` 는 클래스당 한 번」이 **센 것**이고,\
  그것이 얼마나 느린지는 **재지 않았다.**

### (3) ★★ `by lazy` 의 **기본 모드는 `SYNCHRONIZED`** 다 — 던져서 확인했다

**언제 쓰나** — `lazy { }` 를 그냥 쓰면서 스레드 안전한지 모를 때.

문서를 읽는 대신 **위임 객체의 런타임 클래스를 직접 꺼내** 확인했다.

```text
===== 소스: lazymode.kt =====
class Conf {
    val d: String by lazy { "default" }
    val s: String by lazy(LazyThreadSafetyMode.SYNCHRONIZED) { "sync" }
    val p: String by lazy(LazyThreadSafetyMode.PUBLICATION) { "pub" }
    val n: String by lazy(LazyThreadSafetyMode.NONE) { "none" }
}

fun main() {
    val c = Conf()
    for (name in listOf("d", "s", "p", "n")) {
        val f = Conf::class.java.getDeclaredField("$name\$delegate")
        f.isAccessible = true
        println("A $name 의 위임 객체 클래스 : ${f.get(c)::class.qualifiedName}")
    }
    println("B 기본과 SYNCHRONIZED 가 같은 클래스인가 : " +
        (Conf::class.java.getDeclaredField("d\$delegate").also { it.isAccessible = true }.get(c)::class ==
         Conf::class.java.getDeclaredField("s\$delegate").also { it.isAccessible = true }.get(c)::class))
}
```

**출력** (`java -cp olazy:kotlin-stdlib.jar LazymodeKt`)

```text
A d 의 위임 객체 클래스 : kotlin.SynchronizedLazyImpl
A s 의 위임 객체 클래스 : kotlin.SynchronizedLazyImpl
A p 의 위임 객체 클래스 : kotlin.SafePublicationLazyImpl
A n 의 위임 객체 클래스 : kotlin.UnsafeLazyImpl
B 기본과 SYNCHRONIZED 가 같은 클래스인가 : true
```

- ★★ **인자 없는 `lazy { }` 가 `SYNCHRONIZED` 와 같은 클래스**(`kotlin.SynchronizedLazyImpl`)를 만든다.\
  `B : true` 가 그것을 **클래스 동일성으로** 못박는다.
- ★ 세 모드가 **서로 다른 구현 클래스**로 내려간다는 것도 같이 보인다 —\
  `SafePublicationLazyImpl` · `UnsafeLazyImpl`.
- ★ 꺼내는 방법이 (2)의 결과를 그대로 쓴 것이다 — 필드 이름이 **`d$delegate`** 라는 것을 알아야 리플렉션으로 꺼낼 수 있다.

### (4) ★★ 세 모드가 **무엇을 보장하나** — 필드와 명령으로, 그리고 스레드로

**언제 쓰나** — 「`NONE` 이 빠르다던데」라는 말을 들었을 때.

먼저 **구조**를 본다. 세 구현의 필드와 `getValue()` 안의 동기화 명령이다.

**출력** (`javap -p -s` 세 벌 · `getValue()` 안의 `monitorenter`/`compareAndSet` 개수)

```text
$ javap -p -s kotlin/SynchronizedLazyImpl.class   # 필드만
final class kotlin.SynchronizedLazyImpl<T> implements kotlin.Lazy<T>, java.io.Serializable {
  private kotlin.jvm.functions.Function0<? extends T> initializer;
    descriptor: Lkotlin/jvm/functions/Function0;
  private volatile java.lang.Object _value;
    descriptor: Ljava/lang/Object;
  private final java.lang.Object lock;
    descriptor: Ljava/lang/Object;
$ javap -p -s kotlin/SafePublicationLazyImpl.class   # 필드만
final class kotlin.SafePublicationLazyImpl<T> implements kotlin.Lazy<T>, java.io.Serializable {
  public static final kotlin.SafePublicationLazyImpl$Companion Companion;
    descriptor: Lkotlin/SafePublicationLazyImpl$Companion;
  private volatile kotlin.jvm.functions.Function0<? extends T> initializer;
    descriptor: Lkotlin/jvm/functions/Function0;
  private volatile java.lang.Object _value;
    descriptor: Ljava/lang/Object;
  private final java.lang.Object final;
    descriptor: Ljava/lang/Object;
  private static final java.util.concurrent.atomic.AtomicReferenceFieldUpdater<kotlin.SafePublicationLazyImpl<?>, java.lang.Object> valueUpdater;
    descriptor: Ljava/util/concurrent/atomic/AtomicReferenceFieldUpdater;
$ javap -p -s kotlin/UnsafeLazyImpl.class   # 필드만
public final class kotlin.UnsafeLazyImpl<T> implements kotlin.Lazy<T>, java.io.Serializable {
  private kotlin.jvm.functions.Function0<? extends T> initializer;
    descriptor: Lkotlin/jvm/functions/Function0;
  private java.lang.Object _value;
    descriptor: Ljava/lang/Object;
$ 세 구현의 getValue() 안에 무엇이 있나
SynchronizedLazyImpl     monitorenter 1 · compareAndSet 0
SafePublicationLazyImpl  monitorenter 0 · compareAndSet 1
UnsafeLazyImpl           monitorenter 0 · compareAndSet 0
```

```text
   SYNCHRONIZED   _value 가 volatile + lock 객체 + monitorenter 1
   PUBLICATION    _value·initializer 가 volatile + AtomicReferenceFieldUpdater + CAS 1
   NONE           평범한 필드 둘 · 동기화 명령 0
```

- ★ **여기까지는 구조 사실이다** — 「무엇을 쓰는가」이고 **속도가 아니다.**\
  이 문서는 **세 모드의 비용을 재지 않았다.** 「`NONE` 이 빠르다」는 말은 **이 문서가 뒷받침하지 않는다.**

이제 **행동**을 본다. 8스레드가 동시에 한 번씩 읽는 프로그램을 **12판** 돌렸다.

```text
===== 소스: race2.kt =====
import java.util.concurrent.CountDownLatch
import java.util.concurrent.atomic.AtomicInteger
import java.util.Collections

class Box(mode: LazyThreadSafetyMode) {
    val calls = AtomicInteger(0)
    val v: Any by lazy(mode) {
        calls.incrementAndGet()
        Thread.sleep(5)
        Any()
    }
}

fun probe(mode: LazyThreadSafetyMode): String {
    val box = Box(mode)
    val seen = Collections.synchronizedSet(Collections.newSetFromMap(java.util.IdentityHashMap<Any, Boolean>()))
    val start = CountDownLatch(1)
    val done = CountDownLatch(8)
    repeat(8) {
        Thread {
            start.await()
            seen.add(box.v)
            done.countDown()
        }.start()
    }
    start.countDown()
    done.await()
    return "초기화 람다 호출 ${box.calls.get()}회 · 스레드들이 본 서로 다른 객체 ${seen.size}개"
}

fun main() {
    for (mode in LazyThreadSafetyMode.entries) {
        println("$mode : ${probe(mode)}")
    }
}
```

**출력** (`java -cp orace2:kotlin-stdlib.jar Race2Kt` — 12판)

```text
   SYNCHRONIZED : 초기화 람다 호출 1회 · 스레드들이 본 서로 다른 객체 1개
   PUBLICATION : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 1개
   NONE : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 8개
   --- 1 판 끝 ---
   SYNCHRONIZED : 초기화 람다 호출 1회 · 스레드들이 본 서로 다른 객체 1개
   PUBLICATION : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 1개
   NONE : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 6개
   --- 2 판 끝 ---
   SYNCHRONIZED : 초기화 람다 호출 1회 · 스레드들이 본 서로 다른 객체 1개
   PUBLICATION : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 1개
   NONE : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 8개
   --- 3 판 끝 ---
   SYNCHRONIZED : 초기화 람다 호출 1회 · 스레드들이 본 서로 다른 객체 1개
   PUBLICATION : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 1개
   NONE : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 8개
   --- 4 판 끝 ---
   SYNCHRONIZED : 초기화 람다 호출 1회 · 스레드들이 본 서로 다른 객체 1개
   PUBLICATION : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 1개
   NONE : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 8개
   --- 5 판 끝 ---
   SYNCHRONIZED : 초기화 람다 호출 1회 · 스레드들이 본 서로 다른 객체 1개
   PUBLICATION : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 1개
   NONE : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 8개
   --- 6 판 끝 ---
   SYNCHRONIZED : 초기화 람다 호출 1회 · 스레드들이 본 서로 다른 객체 1개
   PUBLICATION : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 1개
   NONE : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 8개
   --- 7 판 끝 ---
   SYNCHRONIZED : 초기화 람다 호출 1회 · 스레드들이 본 서로 다른 객체 1개
   PUBLICATION : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 1개
   NONE : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 8개
   --- 8 판 끝 ---
   SYNCHRONIZED : 초기화 람다 호출 1회 · 스레드들이 본 서로 다른 객체 1개
   PUBLICATION : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 1개
   NONE : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 7개
   --- 9 판 끝 ---
   SYNCHRONIZED : 초기화 람다 호출 1회 · 스레드들이 본 서로 다른 객체 1개
   PUBLICATION : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 1개
   NONE : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 8개
   --- 10 판 끝 ---
   SYNCHRONIZED : 초기화 람다 호출 1회 · 스레드들이 본 서로 다른 객체 1개
   PUBLICATION : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 1개
   NONE : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 7개
   --- 11 판 끝 ---
   SYNCHRONIZED : 초기화 람다 호출 1회 · 스레드들이 본 서로 다른 객체 1개
   PUBLICATION : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 1개
   NONE : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 7개
   --- 12 판 끝 ---
```

> ★★ **이 블록은 다시 돌리면 달라진다.** 대조할 것은 숫자가 아니라 **세 성질**이다 —\
> ① `SYNCHRONIZED` 는 **초기화가 1회**이고 모두 같은 객체를 본다.\
> ② `PUBLICATION` 은 **초기화가 여러 번 돌 수 있는데도 모두가 한 객체를 본다.**\
> ③ `NONE` 은 **초기화도 여러 번, 본 객체도 여러 개일 수 있다.**\
> 실제로 `NONE` 의 「서로 다른 객체 개수」는 12판에서 **8 이 8판, 7 이 3판, 6 이 1판**으로 갈렸다 —\
> **갈린다는 사실 자체가 결론**이고, 어느 숫자가 나오는지는 한 판의 결과일 뿐이다.

- ★★ 12판 내내 **①과 ②는 한 글자도 안 갈렸다.** 그런데 **그것이 「보장」의 근거는 아니다** —\
  보장은 stdlib 의 구현(위의 `monitorenter`·CAS)과 문서에서 오고, 이 실행은 **그 보장과 어긋나지 않았다**까지다.
- ★★★ **`PUBLICATION` 의 핵심**은 「**초기화가 8번 돌았는데 모두가 같은 객체를 본다**」는 것이다.\
  「여러 번 돌아도 괜찮은 계산」에만 쓸 수 있다는 뜻이고, **부수 효과가 있으면 못 쓴다.**
- ★★ **`NONE` 은 스레드마다 다른 객체를 본다.** 「여러 번 돈다」보다 이쪽이 훨씬 나쁘다 —\
  객체 동일성(`===`)이나 캐시를 기대한 코드가 조용히 깨진다.
- ★ **「안 터졌다」가 「안전하다」가 아니다.** `NONE` 은 단일 스레드에서는 12판 내내 아무 문제가 없다.\
  이 실험이 8스레드를 동시에 출발시켜야만 드러났다.

### (5) ★ `observable`·`vetoable`·`notNull` — 콜백이 **언제** 도느냐가 갈린다

**언제 쓰나** — 값이 바뀔 때 로그·검증을 끼우고 싶을 때.

```text
===== 소스: obs.kt =====
import kotlin.properties.Delegates

class Form {
    var name: String by Delegates.observable("빈칸") { prop, old, new ->
        println("   observable — ${prop.name}: '$old' -> '$new'")
    }

    var age: Int by Delegates.vetoable(0) { prop, old, new ->
        println("   vetoable   — ${prop.name}: $old -> $new  (통과? ${new >= 0})")
        new >= 0
    }

    var required: String by Delegates.notNull<String>()
}

fun main() {
    val f = Form()
    println("A name 에 대입")
    f.name = "kim"
    println("   지금 값 : ${f.name}")

    println("B age 에 10")
    f.age = 10
    println("   지금 값 : ${f.age}")

    println("C age 에 -1 (거부된다)")
    f.age = -1
    println("   지금 값 : ${f.age}")

    println("D notNull 을 대입 전에 읽으면")
    try {
        f.required
    } catch (e: Throwable) {
        println("   ${e::class.qualifiedName} : ${e.message}")
    }
}
```

**출력** (`java -cp oobs:kotlin-stdlib.jar ObsKt`)

```text
A name 에 대입
   observable — name: '빈칸' -> 'kim'
   지금 값 : kim
B age 에 10
   vetoable   — age: 0 -> 10  (통과? true)
   지금 값 : 10
C age 에 -1 (거부된다)
   vetoable   — age: 10 -> -1  (통과? false)
   지금 값 : 10
D notNull 을 대입 전에 읽으면
   java.lang.IllegalStateException : Property required should be initialized before get.
```

```text
   observable : 대입한다 ──▶ 필드에 쓴다 ──▶ 콜백(old, new)      ← 사후 통보
   vetoable   : 대입한다 ──▶ 콜백(old, new) ──▶ true 면 쓴다     ← 사전 승인
                                          └──▶ false 면 안 쓴다
   notNull    : 읽는다 ──▶ 아직 대입 전이면 IllegalStateException
```

그림 해설:

- ★★ **`observable` 의 콜백은 값이 바뀐 **뒤**에 돈다.** 막을 수 없다 — 통보다.
- ★★ **`vetoable` 의 콜백은 **앞**에서 돌고 `Boolean` 을 돌려준다.** `C` 에서 `-1` 이 거부돼 값이 `10` 으로 남았다.\
  ★ 그런데 **콜백은 돌았다** — 「거부된 시도」도 관찰할 수 있다.
- ★ **`Delegates.notNull()` 은 `lateinit` 이 못 하는 자리를 메운다** — **원시 타입**이다([16번 주제](../16-properties-backing-field-lateinit-const/)).\
  단 예외가 다르다 — **`IllegalStateException`**(`Property required should be initialized before get.`)이고\
  `lateinit` 의 `UninitializedPropertyAccessException` 이 아니다.
- ★ 값은 위임 객체 안에 있다 — 클래스에는 `<이름>$delegate` 만 있다((2)).

### (6) ★ `Map` 위임 — 실패가 **읽을 때** 온다

**언제 쓰나** — JSON·설정 맵을 타입 있는 객체로 감쌀 때.

```text
===== 소스: mapdel.kt =====
class User(val src: Map<String, Any?>) {
    val name: String by src
    val age: Int by src
}

class MutUser(val src: MutableMap<String, Any?>) {
    var name: String by src
}

fun main() {
    val u = User(mapOf("name" to "kim", "age" to 30))
    println("E name : ${u.name}   age : ${u.age}")

    val m = mutableMapOf<String, Any?>("name" to "lee")
    val mu = MutUser(m)
    println("F 처음 : ${mu.name}")
    mu.name = "park"
    println("G 대입 뒤 프로퍼티 : ${mu.name}")
    println("H 대입 뒤 맵 자체   : $m")

    println("I 키가 없으면")
    val bad = User(mapOf("age" to 1))
    try {
        bad.name
    } catch (e: Throwable) {
        println("   ${e::class.qualifiedName} : ${e.message}")
    }

    println("J 타입이 다르면")
    val wrong = User(mapOf("name" to "kim", "age" to "서른"))
    try {
        wrong.age
    } catch (e: Throwable) {
        println("   ${e::class.qualifiedName} : ${e.message}")
    }
}
```

**출력** (`java -cp omap:kotlin-stdlib.jar MapdelKt`)

```text
E name : kim   age : 30
F 처음 : lee
G 대입 뒤 프로퍼티 : park
H 대입 뒤 맵 자체   : {name=park}
I 키가 없으면
   java.util.NoSuchElementException : Key name is missing in the map.
J 타입이 다르면
   java.lang.ClassCastException : class java.lang.String cannot be cast to class java.lang.Number (java.lang.String and java.lang.Number are in module java.base of loader 'bootstrap')
```

- ★ `val` 은 `Map`, `var` 는 `MutableMap` 이 필요하다. stdlib 이 그 두 타입에 `getValue`/`setValue` **확장**을 달아 뒀다.
- ★★ **프로퍼티 이름이 그대로 키**다((1)의 `property.name`). `G`·`H` 에서 대입이 **맵 자체를 바꾼 것**이 보인다.
- ★★★ **실패가 생성 시점이 아니라 읽는 시점에 온다.**\
  `I` — 키가 없으면 **`java.util.NoSuchElementException: Key name is missing in the map.`**\
  `J` — 타입이 다르면 **`java.lang.ClassCastException`** 이고, 메시지가 `String cannot be cast to Number` 다.\
  ★ `Int` 를 요구했는데 **`Number` 로 캐스트**한다 — (2)에서 본 박싱·`intValue()` 경로 그대로다.
- ★ 그래서 **`Map` 위임은 타입 검사를 런타임으로 미루는 도구**다. `User(…)` 를 만드는 데는 성공하고\
  **그 객체를 쓰는 쪽에서 터진다** — 경계에서 한 번 검증하는 코드가 따로 필요하다.

### (7) ★ 지역 변수에도 된다 — 그리고 **`by lazy` 는 인라인이 아니다**

**언제 쓰나** — 함수 안에서 비싼 값을 조건부로만 계산하고 싶을 때.

```text
===== 소스: local.kt =====
fun expensive(): String {
    println("   초기화 람다가 돌았다")
    return "값"
}

fun main() {
    println("K 지역 변수에 by lazy 를 건다")
    val v: String by lazy { expensive() }
    println("   선언만 했을 때 — 위에 아무 줄도 안 찍혔어야 한다")
    println("   첫 번째 읽기 : $v")
    println("   두 번째 읽기 : $v")
}
```

**출력** (`java -cp olocal:kotlin-stdlib.jar LocalKt`)

```text
K 지역 변수에 by lazy 를 건다
   선언만 했을 때 — 위에 아무 줄도 안 찍혔어야 한다
   초기화 람다가 돌았다
   첫 번째 읽기 : 값
   두 번째 읽기 : 값
```

**출력** (`javap -c -p olocal/LocalKt.class` — `main()`)

```text
  public static final void main();
    Code:
       0: ldc           #27                 // String K 지역 변수에 by lazy 를 건다
       2: getstatic     #15                 // Field java/lang/System.out:Ljava/io/PrintStream;
       5: swap
       6: invokevirtual #21                 // Method java/io/PrintStream.println:(Ljava/lang/Object;)V
       9: invokedynamic #45,  0             // InvokeDynamic #0:invoke:()Lkotlin/jvm/functions/Function0;
      14: invokestatic  #51                 // Method kotlin/LazyKt.lazy:(Lkotlin/jvm/functions/Function0;)Lkotlin/Lazy;
      17: astore_0
      18: ldc           #53                 // String    선언만 했을 때 — 위에 아무 줄도 안 찍혔어야 한다
      20: getstatic     #15                 // Field java/lang/System.out:Ljava/io/PrintStream;
      23: swap
      24: invokevirtual #21                 // Method java/io/PrintStream.println:(Ljava/lang/Object;)V
      27: new           #55                 // class java/lang/StringBuilder
      30: dup
      31: invokespecial #58                 // Method java/lang/StringBuilder."<init>":()V
      34: ldc           #60                 // String    첫 번째 읽기 :
      36: invokevirtual #64                 // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
      39: aload_0
      40: invokestatic  #68                 // Method main$lambda$1:(Lkotlin/Lazy;)Ljava/lang/String;
      43: invokevirtual #64                 // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
      46: invokevirtual #71                 // Method java/lang/StringBuilder.toString:()Ljava/lang/String;
      49: getstatic     #15                 // Field java/lang/System.out:Ljava/io/PrintStream;
      52: swap
      53: invokevirtual #21                 // Method java/io/PrintStream.println:(Ljava/lang/Object;)V
      56: new           #55                 // class java/lang/StringBuilder
      59: dup
      60: invokespecial #58                 // Method java/lang/StringBuilder."<init>":()V
      63: ldc           #73                 // String    두 번째 읽기 :
      65: invokevirtual #64                 // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
      68: aload_0
      69: invokestatic  #68                 // Method main$lambda$1:(Lkotlin/Lazy;)Ljava/lang/String;
      72: invokevirtual #64                 // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
      75: invokevirtual #71                 // Method java/lang/StringBuilder.toString:()Ljava/lang/String;
      78: getstatic     #15                 // Field java/lang/System.out:Ljava/io/PrintStream;
      81: swap
      82: invokevirtual #21                 // Method java/io/PrintStream.println:(Ljava/lang/Object;)V
      85: return

```

- ★ **된다.** 선언 시점에는 아무 일도 안 일어나고 **첫 읽기에서 한 번만** 초기화 람다가 돈다.
- ★★ **`$$delegatedProperties` 가 없다.** 지역 변수라 `KProperty` 를 만들 필요가 없어\
  **`Lazy` 객체 하나가 지역 슬롯(`astore_0`)에 담길 뿐**이다.
- ★★★ **`invokedynamic … Function0` → `invokestatic kotlin/LazyKt.lazy` 가 실제 호출로 남아 있다.**\
  [11번 주제](../11-inline-functions/)의 `inline` 함수들과 정반대다 — **`lazy()` 는 인라인이 아니고 객체를 만든다.**\
  [14번 주제](../14-scope-functions/)의 다섯이 클래스 파일에 **한 흔적도 안 남긴 것**과 나란히 놓고 보면 대비가 분명하다.
- ★ 읽기는 `main$lambda$1(Lkotlin/Lazy;)` 라는 **합성 메서드**를 거친다 — 지역 위임의 접근자가 그것이다.

### (8) 위임을 고르는 자리 — 요약

```text
   값이 안 바뀌고 계산이 비싸다          → by lazy
     여러 스레드가 읽는다                 → 기본(SYNCHRONIZED) 그대로
     여러 번 계산돼도 되고 부수 효과 없다 → PUBLICATION
     한 스레드만 읽는 것이 확실하다       → NONE   ★ 아니면 객체가 갈린다
   바뀔 때 알아야 한다                  → Delegates.observable
   바뀌는 것을 막아야 한다               → Delegates.vetoable
   나중에 주입되는데 원시 타입이다        → Delegates.notNull   (참조 타입이면 lateinit)
   맵을 타입 있는 객체로 감싼다          → Map 위임  ★ 실패는 읽을 때 온다
   그 밖에 반복되는 접근자 로직           → getValue/setValue 직접 구현
```

## 문법 — 형태와 규칙

```kotlin
// 형태
val a: String by lazy { … }                      // 읽기 전용
var b: Int    by Delegates.observable(0) { p, old, new -> … }
var c: Int    by Delegates.vetoable(0) { p, old, new -> new >= 0 }
var d: Int    by Delegates.notNull()
val e: String by mapOf("e" to "x")               // Map 위임 (val 은 Map 으로 충분)
var f: String by mutableMapOf<String, Any?>("f" to "x")   // var 는 MutableMap 이어야 한다

// 직접 만들 때 — 인터페이스 구현이 아니라 규약
//   ★ 위 일곱 형태를 한 클래스에 모아 실제로 컴파일·실행해 확인했다(formcheck.kt).
class Loud(private var stored: String) {
    operator fun getValue(thisRef: Any?, property: KProperty<*>): String = stored
    operator fun setValue(thisRef: Any?, property: KProperty<*>, value: String) { stored = value }
}
```

- **`val` 은 `getValue` 만, `var` 는 `getValue` + `setValue`** 가 필요하다.
- **`operator` 를 빼면 안 된다.** 규약 함수는 `operator` 표시가 있어야 문법이 풀린다.
- **`thisRef` 는 클래스 프로퍼티면 그 인스턴스, 최상위·지역이면 `null`** 이다.
- **위임은 프로퍼티마다 객체 하나**다. `$$delegatedProperties` 는 **클래스마다 하나**다.
- `by lazy` 의 **기본 모드는 `SYNCHRONIZED`** 다.
- `lazy` 는 **`inline` 이 아니다** — 객체가 생긴다((7)).
- 위임은 **`val`/`var` 선언에만** 쓴다. 파라미터·함수에는 못 쓴다.

## 어디서 틀리나

1. ★★★ **`Map` 위임의 실패를 생성 시점으로 착각한다.** 키가 없어도 **객체는 만들어지고** 읽을 때 터진다((6)).
2. ★★ **`PUBLICATION` 을 「조금 느슨한 SYNCHRONIZED」로 읽는다.** **초기화 람다가 여러 번 돈다** —\
  부수 효과(파일 쓰기·카운터 증가)가 있으면 쓰면 안 된다((4)).
3. ★★ **`NONE` 을 「단일 스레드니까 괜찮다」로 쓰고 나중에 스레드가 붙는다.** 그때부터 **객체 동일성이 깨진다**((4)).
4. ★ **`observable` 로 값을 막으려 한다.** 콜백은 **바뀐 뒤**에 돈다 — 막으려면 `vetoable` 이다((5)).
5. ★ **`notNull` 의 예외를 `lateinit` 과 같게 본다.** `IllegalStateException` 이라 catch 절이 다르다((5)).
6. ★ **위임 객체를 여러 프로퍼티가 공유해 놓고 `property.name` 을 안 본다.** 전부 같은 값이 된다((1)).
7. **`operator` 를 빠뜨린다.** 에러가 「그런 메서드가 없다」로 나와 이름 오타처럼 보인다((1)).

## 구현 세부사항 대 언어 보장

| 사실 | 어느 층인가 | 근거 |
|---|---|---|
| `by` 가 **규약**(`getValue`/`setValue`)으로 풀리는 것 | **언어 보장** | (1) — 인터페이스 없이 돌았다 |
| `val` 은 `getValue` 만, `var` 는 둘 다 | **언어 보장** | (1) — 에러 |
| `by lazy` 기본이 **`SYNCHRONIZED`** | **stdlib 계약**(`lazy()` 의 기본 인자) | (3) — 런타임 클래스 |
| `PUBLICATION` 이 **한 객체만 노출**하는 것 | **stdlib 계약** | (4) — CAS · 12판 관찰 |
| `NONE` 이 **아무 보장도 안 하는 것** | **stdlib 계약** | (4) — 관찰이 갈렸다 |
| `Map` 위임이 **읽을 때** 터지는 것 | **stdlib 구현의 결과** | (6) |
| 필드 이름이 **`x$delegate`** 인 것 | ★ **이 판의 관찰** | (2) |
| **`$$delegatedProperties`** 라는 이름과 정적 배열 | ★ **이 판의 관찰** | (2) |
| `by lazy` 가 **`KProperty` 를 안 받는 것** | **JVM 구현**(stdlib 확장이 `inline`) | (2) — 배열 길이 1 |
| `MutablePropertyReference1Impl` 이라는 클래스 | ★ **이 판의 관찰** | (2) |
| 세 `Lazy` 구현의 **필드·동기화 명령** | ★ **이 판의 관찰**(계약의 구현 수단) | (4) |
| `NONE` 에서 관찰된 **객체 개수** | ★ **한 판의 결과** — 되풀이하면 갈린다 | (4) |

- ★★ **가장 조심할 자리**: (4)의 세 모드는 **「무엇을 보장하나」가 계약**이고,\
  **「어떻게 구현했나」(lock·CAS)와 「몇 번 돌았나」는 관찰**이다. 둘을 섞으면\
  「`PUBLICATION` 은 CAS 라 빠르다」 같은 **재지 않은 성능 주장**이 된다 — 이 문서는 **속도를 재지 않았다.**
- ★ **`by lazy` 가 `KProperty` 를 안 받는 것**은 최적화지 문법이 아니다.\
  직접 만든 위임은 (1)에서 본 대로 **항상 `KProperty` 를 받는다.**

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 비싼 값을 **처음 쓸 때 한 번** | `by lazy` | 생성자가 가벼워진다([15번 주제](../15-class-declaration-constructors-and-init/)) |
| 여러 스레드가 읽는다 | 기본 `lazy { }` | 기본이 `SYNCHRONIZED` 다 |
| 여러 번 계산돼도 되고 **부수 효과가 없다** | `lazy(PUBLICATION)` | 모두가 한 객체를 본다 |
| **정말** 한 스레드만 쓴다 | `lazy(NONE)` | 아니면 객체가 갈린다 |
| 값 변경을 **기록**한다 | `observable` | 사후 통보 |
| 값 변경을 **막는다** | `vetoable` | 사전 승인 |
| 늦게 주입되는 **참조 타입** | `lateinit`([16번 주제](../16-properties-backing-field-lateinit-const/)) | 위임 객체가 안 생긴다 |
| 늦게 주입되는 **원시 타입** | `Delegates.notNull()` | `lateinit` 이 못 붙는다 |
| 맵을 타입 있게 감싼다 | `Map` 위임 + **경계 검증** | 실패가 읽을 때 오므로 |
| 매번 **다시 계산**해야 한다 | 커스텀 게터([16번 주제](../16-properties-backing-field-lateinit-const/)) | 위임은 과하다 |

## 핵심 문장

1. **`by` 는 인터페이스가 아니라 규약이다** — `operator fun getValue`/`setValue` 이름과 모양만 맞으면 된다.
2. **서랍에는 값이 아니라 대리인이 들어간다** — 필드 이름이 `<프로퍼티>$delegate` 다.
3. **`KProperty` 는 클래스당 한 번 `$$delegatedProperties` 에 만들어 둔다** — 호출마다 만들지 않는다.
4. ★ **`by lazy` 만 `KProperty` 를 안 받는다** — 그래서 위임이 둘인데 배열 길이가 `1` 이었다.
5. **`by lazy` 의 기본은 `SYNCHRONIZED`** 다 — 런타임 클래스를 꺼내 확인했다.
6. ★★ **`PUBLICATION` 은 「한 번만 돈다」를 보장하지 않는다.** 보장하는 것은 「**모두가 한 객체를 본다**」다.
7. ★★ **`Map` 위임은 읽을 때 터진다** — 없는 키는 `NoSuchElementException`, 타입 불일치는 `ClassCastException`.
8. **`lazy()` 는 인라인이 아니다** — 프로퍼티마다 객체가 생긴다.

## 관련 자료

- [16번 주제 — 프로퍼티](../16-properties-backing-field-lateinit-const/) — **그쪽이 backing field 와 `lateinit` 의 정본**, 여기는 그 서랍에 대리인이 들어가는 경우.
- [15번 주제 — 클래스 선언·`init` 순서](../15-class-declaration-constructors-and-init/) — **그쪽이 초기화 시점의 정본**, 여기는 그 시점을 **첫 사용까지 미루는** 도구.
- [11번 주제 — 인라인 함수](../11-inline-functions/) — **그쪽이 `inline` 의 정본**, 여기는 (7)에서 `lazy` 가 **그것이 아니라는** 대비만.
- [14번 주제 — scope function](../14-scope-functions/) — **인라인이라 아무것도 안 남는 쪽**과의 대비.
- [12번 주제 — `reified` 타입 파라미터](../12-reified-type-parameters/) — (2)의 박싱·`checkcast` 가 왜 생기나.
- 목록의 **31번 주제** — 연산자 규약 전반(`get`/`set`/`invoke`/`plus` …). **`getValue`/`setValue` 는 그중 하나다.**
- 목록의 **21번 주제** — **클래스** 위임(`class A : B by b`). 이름만 같고 다른 문법이다.
- 목록의 **35번 주제** — `@delegate:` use-site target(애너테이션을 위임 필드에 붙이기).
- 목록의 **40번 주제** — 읽기 전용 컬렉션이 뷰라는 것((6)에서 `Map` 을 그대로 쓰는 이유).

## 용어 풀이

- **위임 프로퍼티** — 읽기·쓰기를 다른 객체에 맡긴 프로퍼티. `by` 로 선언한다.
- **위임 객체(delegate)** — `by` 뒤의 객체. `x$delegate` 필드에 담긴다.
- **연산자 규약** — 이름·시그니처만 맞으면 문법이 풀리는 약속. 인터페이스가 아니다.
- **`KProperty`** — 프로퍼티를 가리키는 리플렉션 객체. `name` 등을 가진다.
- **`$$delegatedProperties`** — 클래스마다 하나 생기는 `KProperty` 정적 배열.
- **`LazyThreadSafetyMode`** — `lazy()` 의 스레드 모드 열거형. `SYNCHRONIZED`(기본)·`PUBLICATION`·`NONE`.
- **`monitorenter`** — JVM 의 잠금 진입 명령(`synchronized` 가 이것으로 내려간다).
- **CAS(compare-and-set)** — 잠금 없이 「예상값이면 바꾼다」를 원자적으로 하는 연산.
- **`AtomicReferenceFieldUpdater`** — 특정 필드에 CAS 를 거는 JDK 도구.
- **`observable`/`vetoable`/`notNull`** — `kotlin.properties.Delegates` 가 주는 기성 위임 셋.

## 더 들어가면

- **`provideDelegate`** 라는 규약이 하나 더 있다 — 위임 객체를 **만드는 시점에** 프로퍼티 정보를 받아\
  검증하거나 다른 객체를 돌려줄 수 있다. ★ **이 문서는 던져 보지 않았다.**
- **`Lazy` 에는 `isInitialized()` 가 있다**((4)의 역어셈블에 보인다). [16번 주제](../16-properties-backing-field-lateinit-const/)의\
  `::x.isInitialized` 와 **이름만 같고 다른 것**이다 — 그쪽은 컴파일러가 `getfield; ifnull` 로 바꾸는 문법이고,\
  이쪽은 `Lazy` 인터페이스의 **진짜 메서드**다.
- **`InitializedLazyImpl`** 이라는 네 번째 구현도 jar 안에 있다(`lazyOf(value)` 가 쓴다).\
  ★ **이 문서는 그 경로를 안 던져 봤다.**
- ★ **위임을 `Serializable` 로 쓰는 문제** — 세 `Lazy` 구현이 전부 `java.io.Serializable` 을 구현하고\
  `writeReplace` 를 갖고 있다((4)의 역어셈블). 직렬화하면 **초기화된 값만** 남는 설계인데,\
  ★ **실제로 직렬화해 보지는 않았다.**
