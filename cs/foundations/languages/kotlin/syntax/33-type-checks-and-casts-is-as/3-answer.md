# kotlin/syntax/33 — 타입 검사·캐스트: `is`/`as`/`as?` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javac`·`javap` 에서 실제로 얻었다(C# 은 **.NET SDK 10.0.401** 의 `csc`).\
> 역어셈블은 **기본 `-jvm-target`(1.8 · `major version: 52`)** 이 정본이다.
> ★★ 아래 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적은 자리가 없다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ `A true false true` · `B null null 3` · `C … ClassCastException …` · `D` 는 ★★ **`NullPointerException`**

**출력**

```kotlin
// castforms.kt
fun c1(x: Any?) = x is String
fun c2(x: Any?) = x !is String
fun c3(x: Any?) = x as String
fun c4(x: Any?) = x as? String
fun c5(x: Any?) = x as String?
fun c6(x: Any?) = if (x is String) x.length else -1

fun main() {
    println("A ${c1("s")} ${c1(null)} ${c2(1)}")
    println("B ${c4(1)} ${c5(null)} ${c6("abc")}")
    println("C " + runCatching { c3(1) }.exceptionOrNull())
    println("D " + runCatching { c3(null) }.exceptionOrNull())
}
```

```text
===== kotlinc castforms.kt -d o33c =====
(exit 0)
===== java -cp o33c:kotlin-stdlib.jar CastformsKt =====
A true false true
B null null 3
C java.lang.ClassCastException: class java.lang.Integer cannot be cast to class java.lang.String (java.lang.Integer and java.lang.String are in module java.base of loader 'bootstrap')
D java.lang.NullPointerException: null cannot be cast to non-null type kotlin.String
(exit 0)
```

```text
===== javap -c -p o33c/CastformsKt.class | awk '/ c[0-9]\(/,/^$/' =====
  public static final boolean c1(java.lang.Object);
    Code:
       0: aload_0
       1: instanceof    #9                  // class java/lang/String
       4: ireturn

  public static final boolean c2(java.lang.Object);
    Code:
       0: aload_0
       1: instanceof    #9                  // class java/lang/String
       4: ifne          11
       7: iconst_1
       8: goto          12
      11: iconst_0
      12: ireturn

  public static final java.lang.String c3(java.lang.Object);
    Code:
       0: aload_0
       1: ldc           #17                 // String null cannot be cast to non-null type kotlin.String
       3: invokestatic  #23                 // Method kotlin/jvm/internal/Intrinsics.checkNotNull:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_0
       7: checkcast     #9                  // class java/lang/String
      10: areturn

  public static final java.lang.String c4(java.lang.Object);
    Code:
       0: aload_0
       1: instanceof    #9                  // class java/lang/String
       4: ifeq          14
       7: aload_0
       8: checkcast     #9                  // class java/lang/String
      11: goto          15
      14: aconst_null
      15: areturn

  public static final java.lang.String c5(java.lang.Object);
    Code:
       0: aload_0
       1: checkcast     #9                  // class java/lang/String
       4: areturn

  public static final int c6(java.lang.Object);
    Code:
       0: aload_0
       1: instanceof    #9                  // class java/lang/String
       4: ifeq          17
       7: aload_0
       8: checkcast     #9                  // class java/lang/String
      11: invokevirtual #31                 // Method java/lang/String.length:()I
      14: goto          18
      17: iconst_m1
      18: ireturn
(exit 0)
```

**왜 그런가**

- ★★★ `c3`(`as String`) — **`Intrinsics.checkNotNull(x, "null cannot be cast to non-null type kotlin.String")` → `checkcast String`**. `null` 은 앞의 검사에서 **NPE**, 딴 타입은 뒤의 `checkcast` 에서 **CCE** 다.
- ★★ `c4`(`as?`) — **`instanceof` → `ifeq` → `aconst_null`**, 맞으면 `checkcast`. 예외 경로가 없다.
- ★★ `c5`(`as String?`) — **`checkcast` 하나.** `null` 을 허용하는 타입이라 검사가 없다(`B` 의 둘째 `null`).
- ★ `c1` 은 `instanceof` 하나 — `null` 은 `false`(`A` 의 둘째 칸).

### 2. ★★ `f2`(`is List<*>`)와 `f4`(`Collection<String> is List<String>`)는 통과 · 나머지 셋은 「`cannot check for instance of erased type`」

**출력**

```kotlin
// erase.kt
fun f1(x: Any) = x is List<String>
fun f2(x: Any) = x is List<*>
fun f3(x: List<Any>) = x is List<String>
fun f4(x: Collection<String>) = x is List<String>
fun <T> f5(x: Any) = x is T
```

```text
===== kotlinc erase.kt -d o33e =====
erase.kt:1:23: error: cannot check for instance of erased type 'List<String>'.
fun f1(x: Any) = x is List<String>
                      ^^^^^^^^^^^^
erase.kt:3:29: error: cannot check for instance of erased type 'List<String>'.
fun f3(x: List<Any>) = x is List<String>
                            ^^^^^^^^^^^^
erase.kt:5:27: error: cannot check for instance of erased type 'T (of fun <T> f5)'.
fun <T> f5(x: Any) = x is T
                          ^
(exit 1)
===== echo "물은 함수 $(grep -c '^fun ' erase.kt) · error 줄 $(kotlinc erase.kt -d o33e2 2>&1 | grep -c ': error:')" =====
물은 함수 5 · error 줄 3
(exit 0)
```

**왜 그런가**

- ★★★ 런타임에는 `List` 까지만 남는다. `List<String>` 의 `String` 은 **물을 수 없는 질문**이다 — `f1`·`f3`·`f5`.
- ★★ `f4` 가 되는 이유 — 정적 타입 `Collection<String>` 이 **이미 원소가 `String` 임을 보장**하므로 남은 질문은 「`List` 인가」뿐이다. `f2` 는 타입 인자를 **아예 안 묻는다**(`*`).
- ★ `is T` 를 푸는 것은 `inline` + **`reified`** 다([12번 주제](../12-reified-type-parameters/)).

### 3. ★★ 3번째 줄 「`unchecked cast`」 경고 · 10번째 줄 「`this cast can never succeed`」 경고 · 예외는 ★ **5번째 줄**에서

**출력**

```kotlin
// unchk.kt
fun main() {
    val raw: Any = listOf(1, 2)
    val xs = raw as List<String>
    println("A ${xs.size}")
    println("B " + runCatching { xs[0].length }.exceptionOrNull())
    val n: Any = 1
    println("C " + runCatching { n as Long }.exceptionOrNull())
    println("D ${(n as Int).toLong()}")
    val m = 1
    println("E " + runCatching { m as Long }.exceptionOrNull())
}
```

```text
===== kotlinc unchk.kt -d o33u =====
unchk.kt:3:18: warning: unchecked cast of 'Any' to 'List<String>'.
    val xs = raw as List<String>
                 ^^^^^^^^^^^^^^^
unchk.kt:10:36: warning: this cast can never succeed. Use 'toLong' to perform numeric conversion.
    println("E " + runCatching { m as Long }.exceptionOrNull())
                                   ^^^^^^^
(exit 0)
===== java -cp o33u:kotlin-stdlib.jar UnchkKt =====
A 2
B java.lang.ClassCastException: class java.lang.Integer cannot be cast to class java.lang.String (java.lang.Integer and java.lang.String are in module java.base of loader 'bootstrap')
C java.lang.ClassCastException: class java.lang.Integer cannot be cast to class java.lang.Long (java.lang.Integer and java.lang.Long are in module java.base of loader 'bootstrap')
D 1
E java.lang.ClassCastException: class java.lang.Integer cannot be cast to class java.lang.Long (java.lang.Integer and java.lang.Long are in module java.base of loader 'bootstrap')
(exit 0)
```

**왜 그런가**

- ★★★ `raw as List<String>` 의 `checkcast` 는 **`List` 만** 확인한다 — `A 2` 로 통과. 틀린 것이 드러나는 것은 원소를 **`String` 으로 꺼내 쓰는** `xs[0].length`(5번째 줄)이다.
- ★★ `C`·`E` — `Integer` 는 `Long` 이 **아니다.** 캐스트는 **상자를 바꾸지 않는다.** 정적 타입이 `Int` 인 `E` 에만 경고가 났다.
- ★ `D 1` — 바꾸려면 **`toLong()`**.

### 4. ★★★ 막히는 것 — `t1`·`t2`·`t3`·`t5`·`t11` · 이유를 **안 말하는** 것은 `t5`·`t11`

**출력**

```kotlin
// scast.kt
class H1 { var v: Any = "x" }
class H2 { val v: Any get() = "x" }
open class H3 { open val v: Any = "x" }
class H4 { val v: Any = "x" }

fun t1(h: H1) { if (h.v is String) println(h.v.length) }
fun t2(h: H2) { if (h.v is String) println(h.v.length) }
fun t3(h: H3) { if (h.v is String) println(h.v.length) }
fun t4(h: H4) { if (h.v is String) println(h.v.length) }
fun t5(x: Any) { var y = x; val r = { y = 1 }; if (y is String) println(y.length); r() }
fun t6(x: Any) { if (x is String) println(x.length) }
fun t7(x: Any) { x as String; println(x.length) }
fun t8(x: Any) { if (x !is String) return; println(x.length) }
fun t9(x: Any) = when (x) { is String -> x.length; is Int -> x + 1; else -> 0 }
fun t10(x: Any) { if (x is String && x.length > 0) println(x.length) }
fun t11(x: Any) { if (x is String || x.length > 0) println(0) }
```

```text
===== kotlinc scast.kt -d o33s =====
scast.kt:6:44: error: smart cast to 'String' is impossible, because 'v' is a mutable property that could be mutated concurrently.
fun t1(h: H1) { if (h.v is String) println(h.v.length) }
                                           ^^^
scast.kt:7:44: error: smart cast to 'String' is impossible, because 'v' is a property that has an open or custom getter.
fun t2(h: H2) { if (h.v is String) println(h.v.length) }
                                           ^^^
scast.kt:8:44: error: smart cast to 'String' is impossible, because 'v' is a property that has an open or custom getter.
fun t3(h: H3) { if (h.v is String) println(h.v.length) }
                                           ^^^
scast.kt:10:75: error: unresolved reference 'length' on receiver of type 'Any'.
fun t5(x: Any) { var y = x; val r = { y = 1 }; if (y is String) println(y.length); r() }
                                                                          ^^^^^^
scast.kt:16:40: error: unresolved reference 'length' on receiver of type 'Any'.
fun t11(x: Any) { if (x is String || x.length > 0) println(0) }
                                       ^^^^^^
(exit 1)
===== echo "물은 함수 $(grep -c '^fun t' scast.kt) · error 줄 $(kotlinc scast.kt -d o33s2 2>&1 | grep -c ': error:')" =====
물은 함수 11 · error 줄 5
(exit 0)
```

**왜 그런가**

- ★★★ **물은 함수 11 · 에러 줄 5.** `t1`(`var` 프로퍼티)·`t2`(커스텀 getter)·`t3`(`open`)은 [04번 주제](../04-smart-casts/) (2)와 **같은 문구**다 — `is` 든 `!= null` 이든 **같은 안정 값 판정**이다.
- ★★ `t5`(람다가 고치는 지역 `var`)·`t11`(`||` 오른쪽)은 「`unresolved reference 'length' on receiver of type 'Any'.`」 — 좁혀지지 **않았으니** `Any` 로 본 결과만 말한다.
- ★★ **통과한 여섯이 결론의 절반**이다 — `t4`(같은 모듈 `val`) · `t6` · ★ **`t7`(`as` 한 줄 뒤)** · `t8`(`!is … return`) · `t9`(`when`) · `t10`(`&&`).

### 5. ★ 둘 다 막힌다 — `u1` 은 「`public API property declared in different module.`」 · `u2` 는 「`open or custom getter.`」

**출력**

```kotlin
// lib33.kt
class Far { val v: Any = "x" }
open class FarOpen { open val v: Any = "x" }
```

```kotlin
// use33.kt
fun u1(f: Far) { if (f.v is String) println(f.v.length) }
fun u2(f: FarOpen) { if (f.v is String) println(f.v.length) }
```

```text
===== kotlinc mA/lib33.kt -d o33mA =====
(exit 0)
===== kotlinc -cp o33mA mB/use33.kt -d o33mB =====
mB/use33.kt:1:45: error: smart cast to 'String' is impossible, because 'v' is a public API property declared in different module.
fun u1(f: Far) { if (f.v is String) println(f.v.length) }
                                            ^^^
mB/use33.kt:2:49: error: smart cast to 'String' is impossible, because 'v' is a property that has an open or custom getter.
fun u2(f: FarOpen) { if (f.v is String) println(f.v.length) }
                                                ^^^
(exit 1)
```

**왜 그런가**

- ★★ 다른 모듈의 `val` 은 **그 모듈이 다음 판에서 getter 를 달 수 있으므로** 안정 값이 아니다. 같은 `val` 이 **같은 모듈**(4번의 `t4`)에서는 통과했다.
- ★ `u2` 는 `open` 이 먼저 걸려 **다른 문구**가 나왔다.

### 6. ★★ 경고 둘(「`cast is redundant.`」) · `A` NPE · `B null null` · `C` NPE · `D ClassCastException` — `A`·`C` 는 **같은 클래스, 다른 메시지**

**출력**

```java
// Jsrc.java
public class Jsrc {
    public static String name() { return null; }
    public static Object any() { return 42; }
}
```

```kotlin
// plat.kt
fun main() {
    println("A " + runCatching { Jsrc.name() as String }.exceptionOrNull())
    println("B ${Jsrc.name() as String?} ${Jsrc.name() as? String}")
    println("C " + runCatching { val s: String = Jsrc.name(); s }.exceptionOrNull())
    println("D " + runCatching { Jsrc.any() as String }.exceptionOrNull()?.javaClass?.simpleName)
}
```

```text
===== javac -d o33p Jsrc.java =====
(exit 0)
===== kotlinc -cp o33p plat.kt -d o33p =====
plat.kt:3:30: warning: cast is redundant.
    println("B ${Jsrc.name() as String?} ${Jsrc.name() as? String}")
                             ^^^^^^^^^^
plat.kt:3:56: warning: cast is redundant.
    println("B ${Jsrc.name() as String?} ${Jsrc.name() as? String}")
                                                       ^^^^^^^^^^
(exit 0)
===== java -cp o33p:kotlin-stdlib.jar PlatKt =====
A java.lang.NullPointerException: null cannot be cast to non-null type kotlin.String
B null null
C java.lang.NullPointerException: name(...) must not be null
D ClassCastException
(exit 0)
```

```text
===== javap -c -p o33p/PlatKt.class | grep -E 'instanceof|checkcast|Intrinsics' =====
      26: invokestatic  #39                 // Method kotlin/jvm/internal/Intrinsics.checkNotNull:(Ljava/lang/Object;Ljava/lang/String;)V
      96: instanceof    #78                 // class java/lang/String
     147: invokestatic  #85                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullExpressionValue:(Ljava/lang/Object;Ljava/lang/String;)V
     219: invokestatic  #39                 // Method kotlin/jvm/internal/Intrinsics.checkNotNull:(Ljava/lang/Object;Ljava/lang/String;)V
     222: checkcast     #78                 // class java/lang/String
(exit 0)
```

**왜 그런가**

- ★★★ `A` — 「`null cannot be cast to non-null type kotlin.String`」(`Intrinsics.checkNotNull`, 26번). `String!` 은 이미 `String` 이라 **`checkcast` 가 없다.**
- ★★ `C` — 「`name(...) must not be null`」(`checkNotNullExpressionValue`, 147번). 캐스트 없이 **`String` 변수에 담는 자리**의 검사다([05번 주제](../05-platform-types/)).
- ★ `as String?`·`as? String` 이 **redundant** 인 이유 — 플랫폼 타입은 `String` 과 `String?` **둘 다로** 읽힌다. `as? String` 은 그래도 `instanceof`(96번)를 남겼다.

### 7. `checkcast` 는 **`null` 을 통과시킨다** — 그래서 kotlinc 가 **`Intrinsics.checkNotNull`** 을 앞에 심었고, 예외가 **`NullPointerException`** 이 된다 · CCE 로는 **못 잡는다**

- 1번 `c3` 의 1·3번 오프셋이 그 검사다. 두지 않으면 `as String` 의 결과(null 불가 타입)에 **`null` 이 실려** 먼 자리에서 터진다 — 그 틈을 캐스트 자리에서 막은 것이다.
- ★★ 예외 **종류**는 JVM 백엔드의 선택이다. 언어가 약속한 것은 「실패하면 예외」까지다 — `catch (e: ClassCastException)` 은 이 경우를 **못 잡는다**(1번 `D`).

### 8. 캐스트는 **보는 눈(정적 타입)** 만 바꾸고 **값(상자)** 은 안 바꾼다 — `Int` 면 컴파일 경고, `Any` 면 침묵

- 3번 `C` — `Any` 인 `1` 은 `Integer` 상자다. `as Long` 은 그 상자를 `Long` 으로 **보라는 요구**일 뿐이라 `ClassCastException`.
- 3번 `E` — 정적 타입이 `Int` 면 컴파일러가 **결과를 미리 안다**: 「`this cast can never succeed. Use 'toLong' to perform numeric conversion.`」 `Any` 는 무엇이든 될 수 있어 **경고가 없다.**

### 9. **`instanceof java/lang/String`** — `is String` 과 **한 글자도 같다**

```kotlin
// aliascheck.kt
typealias UserId = String

fun isUser(x: Any) = x is UserId
fun isStr(x: Any) = x is String

fun main() {
    println("A ${isUser("u-1")} ${isUser(7)} ${isStr("u-1")}")
}
```

```text
===== kotlinc aliascheck.kt -d o33a =====
(exit 0)
===== java -cp o33a:kotlin-stdlib.jar AliascheckKt =====
A true false true
(exit 0)
===== javap -c -p o33a/AliascheckKt.class | awk '/ is(User|Str)\(/,/^$/' =====
  public static final boolean isUser(java.lang.Object);
    Code:
       0: aload_0
       1: ldc           #9                  // String x
       3: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_0
       7: instanceof    #17                 // class java/lang/String
      10: ireturn

  public static final boolean isStr(java.lang.Object);
    Code:
       0: aload_0
       1: ldc           #9                  // String x
       3: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_0
       7: instanceof    #17                 // class java/lang/String
      10: ireturn
(exit 0)
```

- ★★ 별칭은 **새 타입이 아니므로**([29번 주제](../29-type-aliases-and-nested-type-aliases/) (1)) 검사로도 가를 수 없다 — `isUser("u-1")` 과 `isStr("u-1")` 이 둘 다 `true`.
- ★ 검사로 가르고 싶으면 **`value class`**([26번 주제](../26-value-class-and-boxing/)).

### 10. `o as string` = Kotlin **`as?`** · `(string)o` = Kotlin **`as`** · `int` 는 `null` 을 못 담아서 **`CS0077`**

```csharp
// cast33.cs
object o = 42;
var s = o as string;
System.Console.WriteLine($"A {s == null}");
int? n = o as int?;
System.Console.WriteLine($"B {n}");
System.Console.WriteLine($"C {o is string} {o is int k && k > 0}");
try { string t = (string)o; } catch (System.InvalidCastException e) { System.Console.WriteLine("D " + e.GetType().Name); }
```

```csharp
// cast33bad.cs
object o = 42;
int bad = o as int;
```

```text
===== csc -out:cast33.dll cast33.cs =====
(exit 0)
===== dotnet cast33.dll =====
A True
B 42
C False True
D InvalidCastException
(exit 0)
===== csc -out:cast33bad.dll cast33bad.cs =====
cast33bad.cs(2,11): error CS0077: The as operator must be used with a reference type or nullable type ('int' is a non-nullable value type)
(exit 1)
```

- ★★★ `A True` — C# `as` 는 실패하면 **`null`**. `D InvalidCastException` — 괄호 캐스트는 **예외**. 이름이 **반대로** 붙었다.
- ★★ 「`The as operator must be used with a reference type or nullable type ('int' is a non-nullable value type)`」 — 결과로 `null` 을 담을 수 없으니 **거부**한다. `o as int?` 는 된다(`B 42`). Kotlin 의 `as? Int` 는 결과가 **`Int?`(박싱)** 라 이 문제가 없다.

### 11. 실패의 **뜻**을 잃는다 — 「아니면 버그」면 `as`, 「아닐 수도 있다」면 `as?`

- `as?` 는 실패를 **`null` 이라는 정상 값**으로 바꾼다. 버그여야 할 실패가 `null` 로 위장해 흐르면 **원인 자리가 사라진다.**
- ★ 기준은 성능이 아니다(이 문서는 시간을 **안 쟀다**). **실패가 무엇을 뜻하느냐**다 — `as?` 를 쓰면 **그 자리에서** `?: error(…)`·`?: return` 으로 처리하라.

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

```text
===== javap -version =====
21.0.5
(exit 0)
```

```text
===== dotnet --version =====
10.0.401
(exit 0)
```

★ **흔들리는 칸과 안 흔들리는 칸**

| 흔들린다 | 안 흔들린다 |
|---|---|
| **없다** — 해시코드·주소·시간을 찍지 않았다 | 출력 — 예외 메시지 **전문** 포함(같은 JDK 판) · `javap` 출력 |
| | 컴파일 진단의 **문구·`파일:줄:칸`·캐럿** · `csc` 의 `CS0077` · 「물은 함수 · error 줄」 |
| | 모든 **종료 코드** |

> 근거 — 캡처 스크립트를 처음부터 다시 돌려 **블록 전체를 바이트 단위로 대조**했다.
>
> 실측 — `capture.sh blocks` 와 `capture.sh blocks-recheck` 를 처음부터 따로 돌려 `normalize-shaky.py` 로 대조했다 —\
> **블록 104개 · 동일 104 · 흔들린 칸 0 · ★고칠 것 0**(30\~33 네 주제를 한 캡처로 받았다). `diff -rq` 도 차이 0 이다.\
> ★ **정규화 규칙은 하나도 안 썼다** — 기본 넷(주소·PID·스레드 id·시간)에 걸리는 칸이 애초에 없었다.

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `castforms.kt` | ★★★ 네 연산자의 번역 · `null` 이 NPE 인 것 | `kotlinc` → `java` · `javap -c -p`(`awk` 필터) |
| `erase.kt` | ★★ 소거된 검사 — 물은 5 · 에러 3 | `kotlinc`(실패가 결과) · 세기 |
| `unchk.kt` | 비검사 캐스트 · 수 캐스트 | `kotlinc`(경고) → `java` |
| `scast.kt` | ★★★ `is` 스마트 캐스트 — 물은 11 · 에러 5 | `kotlinc`(실패가 결과) · 세기 |
| `lib33.kt` · `use33.kt` | 다른 모듈의 프로퍼티 | `kotlinc` → `kotlinc -cp`(실패가 결과) |
| `Jsrc.java` · `plat.kt` | 플랫폼 타입의 `as` | `javac` → `kotlinc`(경고) → `java` · `javap`(필터) |
| `aliascheck.kt` | 별칭 검사 = `instanceof String` | `kotlinc` → `java` · `javap`(`awk` 필터) |
| `cast33.cs` · `cast33bad.cs` | C# `as`/괄호 캐스트 · `CS0077` | `csc` → `dotnet` · `csc`(실패가 결과) |
| `form33.kt` | 형태 한 벌 | `kotlinc` → `java` |

**구현 의존 항목** — `instanceof`/`checkcast`/`checkNotNull` 로의 번역, ★★ **`null as String` 의 예외 종류(NPE)**, 예외 메시지 전문(JDK), 별칭 검사의 명령, 진단 문구와 스마트 캐스트 통과 목록 — 이 컴파일러·판의 산출물이다.\
반면 **「`as` 는 예외 · `as?` 는 `null`」「소거된 타입 인자는 검사 못 한다」「스마트 캐스트는 안정 값에서만」** 은 **언어의 계약**이다.

**★ 던져 봤더니 예상과 달랐던 것 — 세 건**

1. ★★★ **`null as String` 이 `ClassCastException` 이 아니라 `NullPointerException` 이었다**(1·7번). 문서는 「`as` 가 실패하면 `ClassCastException`」이라고 적는데, `null` 의 경우는 kotlinc 가 심은 `checkNotNull` 이 **먼저** 터진다.
2. ★★ **`as String?`·`as? String` 이 플랫폼 타입에서 「`cast is redundant`」 경고**를 받았다(6번). Java 에서 온 값을 「확정」하려는 캐스트를 컴파일러는 **할 일이 없는 것**으로 본다.
3. ★ **`Collection<String> is List<String>` 은 통과했다**(2번). 「제네릭 타입 인자는 `is` 로 못 묻는다」를 넓게 외우면 틀린다 — 정적 타입이 이미 답한 인자는 **물을 필요가 없어서** 된다.
