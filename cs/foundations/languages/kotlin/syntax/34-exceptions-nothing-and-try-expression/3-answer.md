# kotlin/syntax/34 — 예외: 검사 예외 없음·`Nothing` 타입·`try` 가 식이라는 것 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러·경고·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javac`·`java`·`javap` 에서 실제로 얻었다.\
> 역어셈블은 **기본 `-jvm-target`(1.8)** 이 정본이다.
> ★★ 아래 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적은 자리가 없다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ Java 는 「`unreported exception IOException`」로 멈추고 · Kotlin 은 `noCatch()` 까지 통과 · `A caught disk` · `B java.io.IOException: disk`

**출력**

```java
// CallJ.java
public class CallJ {
    public static void main(String[] args) {
        System.out.println(JIo.read());
    }
}
```

```kotlin
// callj.kt
fun noCatch(): String = JIo.read()

fun main() {
    val r = try { JIo.read() } catch (e: java.io.IOException) { "caught ${e.message}" }
    println("A $r")
    println("B " + runCatching { noCatch() }.exceptionOrNull())
}
```

```text
===== javac -d o34j JIo.java CallJ.java =====
CallJ.java:3: error: unreported exception IOException; must be caught or declared to be thrown
        System.out.println(JIo.read());
                                   ^
1 error
(exit 1)
===== javac -d o34k JIo.java =====
(exit 0)
===== kotlinc -cp o34k callj.kt -d o34k =====
(exit 0)
===== java -cp o34k:kotlin-stdlib.jar CalljKt =====
A caught disk
B java.io.IOException: disk
(exit 0)
```

**왜 그런가**

- ★★★ **검사 예외 규칙은 `javac` 의 규칙**이다. 같은 `JIo.read()` 를 Java 소스가 부르면 「잡거나 선언하라」는 의무가 생기고, Kotlin 소스가 부르면 **그 의무가 없다** — Kotlin 은 모든 예외를 비검사로 다룬다.
- ★★ 예외는 **그대로 난다**(`B`). 사라진 것은 **컴파일 시점의 알림**이다.
- ★ Kotlin 에서도 `catch (e: IOException)` 은 쓸 수 있다(`A`).

### 2. ★★★ `a()` 는 「`is never thrown in body of corresponding try statement`」 · `b()` 는 「`unreported exception`」 · `UseK2` 는 통과해 `A …declared` · `B java.io.IOException / instanceof IOException = true`

**출력**

```kotlin
// kio.kt
import java.io.IOException

fun plain(): String = throw IOException("plain")

@Throws(IOException::class)
fun declared(): String = throw IOException("declared")
```

```java
// UseK1.java
import java.io.IOException;

public class UseK1 {
    static void a() {
        try { KioKt.plain(); } catch (IOException e) { }
    }
    static void b() {
        KioKt.declared();
    }
}
```

```java
// UseK2.java
import java.io.IOException;

public class UseK2 {
    public static void main(String[] args) {
        try { KioKt.declared(); } catch (IOException e) { System.out.println("A " + e); }
        try { KioKt.plain(); } catch (Exception e) {
            System.out.println("B " + e.getClass().getName() + " / instanceof IOException = " + (e instanceof IOException));
        }
    }
}
```

```text
===== kotlinc kio.kt -d o34t =====
(exit 0)
===== javac -cp o34t -d o34t UseK1.java =====
UseK1.java:5: error: exception IOException is never thrown in body of corresponding try statement
        try { KioKt.plain(); } catch (IOException e) { }
                               ^
UseK1.java:8: error: unreported exception IOException; must be caught or declared to be thrown
        KioKt.declared();
                      ^
2 errors
(exit 1)
===== javac -cp o34t:kotlin-stdlib.jar -d o34t UseK2.java =====
(exit 0)
===== java -cp o34t:kotlin-stdlib.jar UseK2 =====
A java.io.IOException: declared
B java.io.IOException / instanceof IOException = true
(exit 0)
```

```text
===== javap -v -p o34t/KioKt.class | grep -E 'String (plain|declared)\(\);|Exceptions:|throws ' =====
  public static final java.lang.String plain();
  public static final java.lang.String declared() throws java.io.IOException;
    Exceptions:
      throws java.io.IOException
(exit 0)
```

**왜 그런가**

- ★★★ `plain()` 의 클래스 파일에는 **`throws` 가 없다.** `javac` 는 「이 메서드는 `IOException` 을 안 던진다」로 읽고, **안 던지는 검사 예외를 잡는 `catch` 를 에러로** 막는다 — 실제로는 던지는데도.
- ★★ `@Throws` 를 단 `declared()` 에는 **`Exceptions: throws java.io.IOException`** 이 생긴다. Java 에게는 진짜 검사 예외 메서드가 되어 **안 잡으면** 에러다(`b()`).
- ★★ `catch (Exception e)` 는 `plain()` 의 예외도 잡는다(`B`) — 잡는 길은 있지만 **어떤 검사 예외가 오는지 Java 가 알 방법**이 없다.

### 3. ★★ 진단 없음 · `A …NotImplementedError…` · `B 3 …IllegalStateException: none` · `C 10 …no` · `D …AssertionError: stop` · `E 0` — `die` 는 **`java.lang.Void`**, 호출 뒤에는 **`KotlinNothingValueException`**

**출력**

```kotlin
// nothing.kt
import kotlin.test.fail

fun die(msg: String): Nothing = throw IllegalStateException(msg)

fun n1(): Int {
    TODO()
    return 1
}

fun n2(s: String?): Int {
    val t = s ?: die("none")
    return t.length
}

fun n3(flag: Boolean): Int {
    val v = if (flag) 10 else throw IllegalArgumentException("no")
    return v
}

fun n4(): Int {
    fail("stop")
    return 4
}

fun main() {
    println("A " + runCatching { n1() }.exceptionOrNull())
    println("B ${n2("abc")} " + runCatching { n2(null) }.exceptionOrNull())
    println("C ${n3(true)} " + runCatching { n3(false) }.exceptionOrNull())
    println("D " + runCatching { n4() }.exceptionOrNull())
    val xs: List<String> = emptyList<Nothing>()
    println("E ${xs.size}")
}
```

```text
===== kotlinc -cp kotlin-test.jar nothing.kt -d o34n =====
(exit 0)
===== java -cp o34n:kotlin-stdlib.jar:kotlin-test.jar NothingKt =====
A kotlin.NotImplementedError: An operation is not implemented.
B 3 java.lang.IllegalStateException: none
C 10 java.lang.IllegalArgumentException: no
D java.lang.AssertionError: stop
E 0
(exit 0)
```

```text
===== javap -c -p o34n/NothingKt.class | awk '/ (die|n1|n2|n4)\(/,/^$/' =====
  public static final java.lang.Void die(java.lang.String);
    Code:
       0: aload_0
       1: ldc           #9                  // String msg
       3: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: new           #17                 // class java/lang/IllegalStateException
       9: dup
      10: aload_0
      11: invokespecial #21                 // Method java/lang/IllegalStateException."<init>":(Ljava/lang/String;)V
      14: athrow

  public static final int n1();
    Code:
       0: new           #26                 // class kotlin/NotImplementedError
       3: dup
       4: aconst_null
       5: iconst_1
       6: aconst_null
       7: invokespecial #29                 // Method kotlin/NotImplementedError."<init>":(Ljava/lang/String;ILkotlin/jvm/internal/DefaultConstructorMarker;)V
      10: athrow

  public static final int n2(java.lang.String);
    Code:
       0: aload_0
       1: dup
       2: ifnonnull     20
       5: pop
       6: ldc           #34                 // String none
       8: invokestatic  #36                 // Method die:(Ljava/lang/String;)Ljava/lang/Void;
      11: pop
      12: new           #38                 // class kotlin/KotlinNothingValueException
      15: dup
      16: invokespecial #41                 // Method kotlin/KotlinNothingValueException."<init>":()V
      19: athrow
      20: astore_1
      21: aload_1
      22: invokevirtual #46                 // Method java/lang/String.length:()I
      25: ireturn

  public static final int n4();
    Code:
       0: ldc           #62                 // String stop
       2: invokestatic  #67                 // Method kotlin/test/AssertionsKt.fail:(Ljava/lang/String;)Ljava/lang/Void;
       5: pop
       6: new           #38                 // class kotlin/KotlinNothingValueException
       9: dup
      10: invokespecial #41                 // Method kotlin/KotlinNothingValueException."<init>":()V
      13: athrow
(exit 0)
```

**왜 그런가**

- ★★★ `Nothing` 은 JVM 에 없으므로 **`Void`** 로 내린다(`die(…)Ljava/lang/Void;`). 호출 뒤의 `new KotlinNothingValueException … athrow` 는 **「돌아오면 안 되는 것이 돌아온」 경우**의 검문이다.
- ★★ `n4` 의 `return 4` 는 클래스 파일에 **없다** — `fail()` 의 반환 타입이 `Nothing` 이라 그 뒤를 버렸다. `n1` 은 `TODO()` 가 `inline` 이라 **`new NotImplementedError` 가 직접** 박혔다.
- ★ 진단이 없는 이유는 5번 — 도달 불가 경고는 이 판에서 **기본으로 안 나온다.**
- ★ `E 0` — `Nothing` 이 모든 타입의 하위 타입이고 `List` 가 공변이라 `List<Nothing>` 을 `List<String>` 에 넣을 수 있다.

### 4. ★★ 물은 함수 8 · 에러 7 — `p1`·`p2` 는 **`String`**, `p5` 는 **`Int`**, `p3` 는 `Nothing?`, `p7` 은 `List<Nothing?>`, `p4`·`p6` 은 `Comparable<*> & Serializable` · ★ **`p8` 은 에러 없음**

**출력**

```kotlin
// infer.kt
fun p1(s: String?) { val t = s ?: throw IllegalStateException(); val z: Int = t }
fun p2(s: String?) { val t = s ?: return; val z: Int = t }
fun p3() { val n = null; val z: Int = n }
fun p4(f: Boolean) { val v = if (f) 1 else "s"; val z: String = v }
fun p5(f: Boolean) { val v = if (f) 1 else error("e"); val z: String = v }
fun p6() { val r = try { 1 } catch (e: Exception) { "s" }; val z: Int = r }
fun p7() { val xs = listOf(null); val z: Int = xs }
fun p8() { val e = throw IllegalStateException(); val z: Int = e }
```

```text
===== kotlinc infer.kt -d o34i =====
infer.kt:1:77: error: initializer type mismatch: expected 'Int', actual 'String'.
fun p1(s: String?) { val t = s ?: throw IllegalStateException(); val z: Int = t }
                                                                            ^
infer.kt:2:54: error: initializer type mismatch: expected 'Int', actual 'String'.
fun p2(s: String?) { val t = s ?: return; val z: Int = t }
                                                     ^
infer.kt:3:37: error: initializer type mismatch: expected 'Int', actual 'Nothing?'.
fun p3() { val n = null; val z: Int = n }
                                    ^
infer.kt:4:63: error: initializer type mismatch: expected 'String', actual 'Comparable<*> & Serializable'.
fun p4(f: Boolean) { val v = if (f) 1 else "s"; val z: String = v }
                                                              ^
infer.kt:5:70: error: initializer type mismatch: expected 'String', actual 'Int'.
fun p5(f: Boolean) { val v = if (f) 1 else error("e"); val z: String = v }
                                                                     ^
infer.kt:6:71: error: initializer type mismatch: expected 'Int', actual 'Comparable<*> & Serializable'.
fun p6() { val r = try { 1 } catch (e: Exception) { "s" }; val z: Int = r }
                                                                      ^
infer.kt:7:46: error: initializer type mismatch: expected 'Int', actual 'List<Nothing?>'.
fun p7() { val xs = listOf(null); val z: Int = xs }
                                             ^
(exit 1)
===== echo "물은 함수 $(grep -c '^fun ' infer.kt) · error 줄 $(kotlinc infer.kt -d o34i2 2>&1 | grep -c ': error:')" =====
물은 함수 8 · error 줄 7
(exit 0)
```

**왜 그런가**

- ★★★ 두 가지를 합칠 때 한쪽이 `Nothing` 이면 **다른 쪽 타입이 그대로** 남는다 — 바닥 타입은 공통 상위 타입에 아무것도 보태지 않는다. 그래서 `s ?: throw` 는 **`String`**.
- ★★ **`p8`** — `throw` 식의 타입 `Nothing` 은 `Int` 에 **대입된다.** 에러가 안 난 칸이 바닥 타입의 증거다.
- ★ 대조군 `p4`·`p6` — `Int` 와 `String` 을 합치면 교집합 타입이 된다. `try`/`catch` 도 `if` 와 같은 규칙이다.

### 5. ★★ 기본 컴파일은 **경고 0줄** · `-Wextra` 에서만 「`unreachable code.`」 세 줄

**출력**

```kotlin
// unr.kt
fun u1(): Int {
    return 1
    println("after return")
}
fun u2(): Int {
    throw IllegalStateException()
    println("after throw")
}
fun u3(): Int {
    TODO()
    println("after TODO")
}
```

```text
===== kotlinc unr.kt -d o34u =====
(exit 0)
===== kotlinc -Wextra unr.kt -d o34u2 =====
unr.kt:3:5: warning: unreachable code.
    println("after return")
    ^^^^^^^^^^^^^^^^^^^^^^^
unr.kt:7:5: warning: unreachable code.
    println("after throw")
    ^^^^^^^^^^^^^^^^^^^^^^
unr.kt:11:5: warning: unreachable code.
    println("after TODO")
    ^^^^^^^^^^^^^^^^^^^^^
(exit 0)
===== echo "물은 자리 3 · 기본 warning 줄 $(kotlinc unr.kt -d o34u3 2>&1 | grep -c ': warning:') · -Wextra warning 줄 $(kotlinc -Wextra unr.kt -d o34u4 2>&1 | grep -c ': warning:')" =====
물은 자리 3 · 기본 warning 줄 0 · -Wextra warning 줄 3
(exit 0)
```

**왜 그런가**

- ★★★ 이 판(K2 2.4.20)은 도달 불가 경고를 **`-Wextra` 로 분류**했다. 기본 빌드에서는 `TODO()` 뒤의 코드가 **조용히 버려진다.**
- ★★ 세 자리의 문구가 **같다** — `return`·`throw`·`TODO()` 는 컴파일러에게 같은 부류(`Nothing`)의 식이다.

### 6. ★★★ `6 / 9` — `finally` 가 `return`·`throw` 로 끝난 여섯 행이 `false` · `-Wextra` 진단 0줄 · `tryval.kt` 는 `finally(42)` → `A 42` → `finally(x)` → `B -1` → `C 1` · 「`expression is unused.`」 경고 둘

**출력**

```kotlin
// fgrid.kt
fun cell(t: Char, f: Char): String {
    try {
        when (t) {
            'N' -> {}
            'R' -> return "T-return"
            else -> throw IllegalStateException("T-throw")
        }
    } finally {
        when (f) {
            'N' -> {}
            'R' -> return "F-return"
            else -> throw IllegalArgumentException("F-throw")
        }
    }
    return "after-try"
}

fun outcome(block: () -> String): String =
    try { "value " + block() } catch (e: Exception) { "exception " + e.message }

fun main() {
    val alone = mapOf('N' to "value after-try", 'R' to "value T-return", 'T' to "exception T-throw")
    var lost = 0
    for (f in "NRT") for (t in "NRT") {
        val got = outcome { cell(t, f) }
        val same = got == alone[t]
        if (!same) lost++
        println("try=$t finally=$f -> $got ; same as try alone: $same")
    }
    println("cells where the try outcome differs: $lost / 9")
}
```

```text
===== kotlinc -Wextra fgrid.kt -d o34f =====
(exit 0)
===== java -cp o34f:kotlin-stdlib.jar FgridKt =====
try=N finally=N -> value after-try ; same as try alone: true
try=R finally=N -> value T-return ; same as try alone: true
try=T finally=N -> exception T-throw ; same as try alone: true
try=N finally=R -> value F-return ; same as try alone: false
try=R finally=R -> value F-return ; same as try alone: false
try=T finally=R -> value F-return ; same as try alone: false
try=N finally=T -> exception F-throw ; same as try alone: false
try=R finally=T -> exception F-throw ; same as try alone: false
try=T finally=T -> exception F-throw ; same as try alone: false
cells where the try outcome differs: 6 / 9
(exit 0)
```

```kotlin
// tryval.kt
fun parse(s: String): Int = try {
    s.toInt()
} catch (e: NumberFormatException) {
    -1
} finally {
    println("  finally($s)")
    999
}

fun main() {
    println("A ${parse("42")}")
    println("B ${parse("x")}")
    val v = try { 1 } finally { 2 }
    println("C $v")
}
```

```text
===== kotlinc tryval.kt -d o34v =====
tryval.kt:7:5: warning: expression is unused.
    999
    ^^^
tryval.kt:13:33: warning: expression is unused.
    val v = try { 1 } finally { 2 }
                                ^
(exit 0)
===== java -cp o34v:kotlin-stdlib.jar TryvalKt =====
  finally(42)
A 42
  finally(x)
B -1
C 1
(exit 0)
```

**왜 그런가**

- ★★★ `finally` 는 `try` 가 어떻게 끝나든 돈다. 그 `finally` 가 **자기 `return`·`throw` 로 끝나면** 그것이 식 전체의 끝이 된다 — `try=T finally=R` 에서 **예외가 사라지고** `F-return` 이 값이 된다.
- ★★ `finally` 가 **정상 종료**하면 마지막 식은 **값에 안 들어간다** — `999`·`2` 가 버려지고, 컴파일러가 「`expression is unused.`」로 그것을 말한다.
- ★ `finally(42)` 가 `A 42` 보다 먼저인 것 — `finally` 는 값이 **호출자에게 넘어가기 전에** 돈다.

### 7. `KotlinNothingValueException` 이 난다 — 명령은 **kotlinc 가 호출자 쪽에** 심었다

**출력**

```kotlin
// stopper.kt
interface Stopper {
    fun stop(): Nothing
}
```

```java
// JStop.java
public class JStop implements Stopper {
    @Override
    public Void stop() {
        return null;
    }
}
```

```kotlin
// usestop.kt
fun halt(s: Stopper): Int {
    s.stop()
}

fun main() {
    println("A " + runCatching { halt(JStop()) }.exceptionOrNull())
}
```

```text
===== kotlinc stopper.kt -d o34s =====
(exit 0)
===== javac -cp o34s -d o34s JStop.java =====
(exit 0)
===== kotlinc -cp o34s usestop.kt -d o34s =====
(exit 0)
===== java -cp o34s:kotlin-stdlib.jar UsestopKt =====
A kotlin.KotlinNothingValueException
(exit 0)
===== javap -c -p o34s/UsestopKt.class | awk '/ halt\(/,/^$/' =====
  public static final int halt(Stopper);
    Code:
       0: aload_0
       1: ldc           #9                  // String s
       3: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_0
       7: invokeinterface #21,  1           // InterfaceMethod Stopper.stop:()Ljava/lang/Void;
      12: pop
      13: new           #23                 // class kotlin/KotlinNothingValueException
      16: dup
      17: invokespecial #27                 // Method kotlin/KotlinNothingValueException."<init>":()V
      20: athrow
(exit 0)
```

**왜 그런가**

- ★★ Java 에게 `stop()` 은 `Void` 를 돌려주는 **평범한 메서드**라 `return null;` 이 합법이다. Kotlin 호출자 `halt` 의 **`13: new KotlinNothingValueException`** 이 돌아온 흐름을 막았다.
- ★ `halt` 는 `return` 없이도 컴파일됐다 — `Nothing` 뒤는 도달 불가라서다. 검문이 없으면 **반환값 없는 흐름**이 흘러나갈 자리다.

### 8. 「`overload resolution ambiguity`」 — `Nothing` 이 여섯 `plus` 에 **전부 맞는다**

**출력**

```kotlin
// amb.kt
fun sum(x: Int): Int {
    val y = x + TODO()
    return y
}
```

```text
===== kotlinc amb.kt -d o34a =====
amb.kt:2:15: error: overload resolution ambiguity between candidates:
fun plus(other: Byte): Int
fun plus(other: Short): Int
fun plus(other: Int): Int
fun plus(other: Long): Long
fun plus(other: Float): Float
fun plus(other: Double): Double
    val y = x + TODO()
              ^
(exit 1)
```

**왜 그런가**

- ★★ 타입이 **안 맞는** 것이 아니라 **너무 잘 맞는** 것이다. 바닥 타입은 `Byte`·`Short`·`Int`·`Long`·`Float`·`Double` 어디에나 대입되므로 후보를 가를 수 없다.
- ★ 기대 타입이 하나인 자리(`fun f(): Int = TODO()`)에서는 모호성이 없다.

### 9. `@Throws` 는 **`Exceptions:` 속성 한 줄**을 만든다 — Kotlin 호출자에게는 **아무 차이 없음**, Java 호출자에게는 **잡을 수 있게 되는 동시에 잡아야 하게** 된다

**왜 그런가**

- ★★ 2번의 `javap` — `declared() throws java.io.IOException` + `Exceptions:`. `plain()` 에는 없다.
- ★★ Kotlin 쪽 규칙은 1번 그대로다 — `@Throws` 는 **Kotlin 컴파일러의 검사를 켜지 않는다.**
- ★ 공개 API 에 **나중에** 달면 기존 Java 호출자가 「`unreported exception`」으로 **깨진다**(2번 `b()`). 반대로 떼면 기존 `catch` 가 「`is never thrown`」으로 깨진다. 어느 쪽이든 **Java 에게는 소스 비호환 변경**이다.

### 10. `javac` 는 **기본으로는 조용하고** `-Xlint:finally` 에서 「`finally clause cannot complete normally`」 · JS 도 **`6 / 9`**

**출력**

```java
// FinJ.java
public class FinJ {
    static String f() {
        try {
            throw new IllegalStateException("T-throw");
        } finally {
            return "F-return";
        }
    }
    public static void main(String[] args) {
        System.out.println("A " + f());
    }
}
```

```text
===== javac -d o34fj FinJ.java =====
(exit 0)
===== javac -Xlint:finally -d o34fj2 FinJ.java =====
FinJ.java:7: warning: [finally] finally clause cannot complete normally
        }
        ^
1 warning
(exit 0)
===== java -cp o34fj FinJ =====
A F-return
(exit 0)
```

**왜 그런가**

- ★★ 세 언어 모두 **`finally` 의 완료가 `try` 의 완료를 덮는다** — Java `A F-return`, Kotlin `6 / 9`, JS `6 / 9`([JS 32번](../../../js/syntax/32-error-handling-and-error/)).
- ★ 차이는 **알려 주느냐**다 — `javac` 는 린트 옵션으로 경고하고, `kotlinc` 는 `-Wextra` 로도 **말하지 않았다**(6번의 컴파일 줄).

### 11. 셋 다 **「돌아오지 않는 식」의 바닥 타입**이다 — Go 는 오류를 **반환값**으로 돌려 이 자리가 비지 않는다

**왜 그런가**

- ★★ Kotlin `Nothing` · Rust `!` · TS `never` 는 **값이 없고 어디에나 대입되는** 타입이다. `match`·`if`·`?:` 의 한쪽이 발산해도 **다른 쪽 타입이 결과**가 된다 — 4번의 `p1`·`p5` 와 같은 규칙이다([Rust 06번](../../../rust/syntax/06-functions-and-never-type/) · [TS 04번](../../../ts/syntax/04-any-unknown-never-void/)).
- ★ Go 는 실패를 `error` **값**으로 돌려주므로([Go 23번](../../../go/syntax/23-error-interface-and-errors-as-values/)) 「실패 경로가 식의 타입을 어떻게 하나」라는 질문 자체가 작아진다. 대신 **돌려받은 값을 확인하는 규율**이 사람 몫이다.

### 12. 컴파일러가 **「이 호출은 어떤 이유로 실패할 수 있나」를 알려 주지 않는다** — `runCatching`·`Result` 는 **강제되지 않는 관용구**라 그 자리를 못 메운다

**왜 그런가**

- ★★★ 1번이 증거다 — `noCatch()` 는 `IOException` 을 흘리는데 **컴파일러는 아무 말도 안 했다.** 실패 경로는 이제 **문서와 설계의 문제**다.
- ★★ `runCatching` 은 호출자가 **골라 써야** 효과가 있다. 안 써도 컴파일된다 — 검사 예외와 달리 **누락을 잡아 주는 쪽이 없다.** 논지는 [`../../언어-특성/README.md`](../../언어-특성/README.md) §8 이 정본이다.

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
===== ls "$(dirname "$(readlink -f "$(command -v kotlinc)")")/../lib" | grep -E '^kotlin-(reflect|test|stdlib)\.jar$' =====
kotlin-reflect.jar
kotlin-stdlib.jar
kotlin-test.jar
(exit 0)
```

★ **흔들리는 칸과 안 흔들리는 칸**

| 흔들린다 | 안 흔들린다 |
|---|---|
| **없다** — 해시코드·주소·시간을 찍지 않았다 | 실행 출력 · 예외 메시지 · `javap` 출력 |
| | `javac`·`kotlinc` 진단의 **문구·`파일:줄:칸`·캐럿** · 「물은 N · 줄 M」 |
| | 모든 **종료 코드** |

> 근거 — 캡처 스크립트를 처음부터 다시 돌려 **블록 전체를 바이트 단위로 대조**했다.
>
> 실측 — `capture.sh blocks` 와 `capture.sh blocks-recheck` 를 처음부터 따로 돌려 `normalize-shaky.py` 로 대조했다 —\
> **블록 103개 · 동일 103 · 흔들린 칸 0 · ★고칠 것 0**(34\~37 네 주제를 한 캡처로 받았다). `diff -rq` 도 차이 0 이다.\
> ★ **정규화 규칙은 하나도 안 썼다** — 기본 넷(주소·PID·스레드 id·시간)에 걸리는 칸이 애초에 없었다.

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `JIo.java` · `CallJ.java` · `callj.kt` | ★★★ 같은 검사 예외 메서드 — Java 에러 · Kotlin 통과 | `javac`(실패가 결과) → `javac` → `kotlinc` → `java` |
| `kio.kt` · `UseK1.java` · `UseK2.java` | ★★★ `@Throws` 없을 때 Java `catch` 거부 · 있을 때 의무 | `kotlinc` → `javac`(실패가 결과) → `javac` → `java` · `javap -v`(필터) |
| `nothing.kt` | ★★ `Nothing` — `Void` · `KotlinNothingValueException` | `kotlinc -cp kotlin-test.jar` → `java` · `javap -c`(필터) |
| `infer.kt` | ★★ 추론 타입 — 물은 8 · 에러 7 | `kotlinc`(실패가 결과) · 세기 |
| `unr.kt` | ★ 도달 불가 — 기본 0 · `-Wextra` 3 | `kotlinc` · `kotlinc -Wextra` · 세기 |
| `stopper.kt` · `JStop.java` · `usestop.kt` | ★★ 돌아온 `Nothing` | `kotlinc` → `javac` → `kotlinc` → `java` · `javap -c`(필터) |
| `tryval.kt` · `fgrid.kt` | ★★★ `try` 식 · `finally` 격자 `6 / 9` | `kotlinc`(경고) → `java` · `kotlinc -Wextra` → `java` |
| `FinJ.java` | Java 의 `finally` 린트 | `javac` · `javac -Xlint:finally` → `java` |
| `amb.kt` | `x + TODO()` 모호성 | `kotlinc`(실패가 결과) |
| `form34.kt` | 형태 한 벌 | `kotlinc` → `java` |

**구현 의존 항목** — `Nothing` 의 `Void` 내림 · `KotlinNothingValueException` 검문 · `Exceptions:` 속성 · `TODO()` 의 인라인 펼침 · ★ **도달 불가 경고의 등급(`-Wextra`)** · 진단 문구 — 이 컴파일러·판의 산출물이다.\
반면 **「예외는 전부 비검사」「`throw` 는 `Nothing` 식」「`Nothing` 은 모든 타입의 하위 타입」「`finally` 는 값을 안 바꾼다」** 는 **언어의 계약**이다.

**★ 던져 봤더니 예상과 달랐던 것 — 세 건**

1. ★★★ **「`TODO()` 뒤의 코드는 도달 불가 경고」가 기본 빌드에서는 안 나왔다**(5번). `-Wextra` 를 줘야 세 자리가 전부 잡힌다 — 브리핑은 경고가 나온다고 전제했다.
2. ★★ **`Nothing` 호출 뒤에 kotlinc 가 `KotlinNothingValueException` 을 심는다**(3·7번). Java 가 `Nothing` 멤버를 구현하면 **실제로 터진다.**
3. ★ **`x + TODO()` 는 타입 불일치가 아니라 오버로드 모호성**이었다(8번) — 바닥 타입은 「안 맞아서」가 아니라 「다 맞아서」 문제를 낸다.
