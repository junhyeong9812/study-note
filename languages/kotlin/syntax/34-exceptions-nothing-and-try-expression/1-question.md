# kotlin/syntax/34 — 예외: 검사 예외 없음·`Nothing` 타입·`try` 가 식이라는 것 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [06번 주제](../06-when-expression/)다 — `when` 이 식일 때 가지에 `throw` 를 놓는 자리를 거기서 봤다.
> 문항 12개 중 코드블록이 붙는 예측형은 6개다.
> 바이트코드를 묻는 문항은 **`kotlinc` 기본 `-jvm-target`(1.8)** 기준이다.
> 이 주제의 모든 답은 **kotlinc 2.4.20 · Temurin JDK 21.0.5(`javac`·`java`·`javap`)** 에서 실제로 던져 받은 것이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 같은 Java 메서드를 Java 와 Kotlin 에서 부르면 (예측)

```java
// JIo.java
import java.io.IOException;

public class JIo {
    public static String read() throws IOException {
        throw new IOException("disk");
    }
}
```

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

- `javac JIo.java CallJ.java` 는 어떻게 되는가? `callj.kt` 는 컴파일되는가 — 특히 `noCatch()` 는?
- `callj.kt` 를 돌리면 `A`·`B` 에 무엇이 찍히는가?

### 2. ★★★ Kotlin 이 던지는 것을 Java 가 잡으려 하면 (예측)

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

- `UseK1.java` 의 `a()`·`b()` 는 각각 컴파일되는가? 안 되면 무엇이라고 말하는가?
- `UseK2.java` 는 컴파일되는가? 돌리면 `A`·`B` 에 무엇이 찍히는가?
- `javap -v` 로 보면 `plain()` 과 `declared()` 의 메서드 정보는 어디가 다른가?

### 3. ★★ `Nothing` 을 돌려주는 호출들 (예측)

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

- 컴파일 진단이 나오는가? `A`\~`E` 에 무엇이 찍히는가?
- `die` 의 JVM 반환 타입은 무엇인가? `n2` 의 바이트코드에서 `die` 호출 **바로 뒤**에는 무엇이 있는가? `n4` 의 `return 4` 는?

### 4. ★★ 일부러 틀린 타입을 적어 추론 결과를 말하게 하면 (예측)

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

- 함수마다 에러가 나는가? 나면 **`actual '…'`** 자리에 무슨 타입이 적히는가?

### 5. ★★ `return`·`throw`·`TODO()` 뒤의 코드 (예측)

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

- 그냥 `kotlinc unr.kt` 로 컴파일하면 진단이 나오는가? `-Wextra` 를 붙이면?

### 6. ★★★ `finally` 가 `return`·`throw` 로 끝나면 (예측)

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

- `fgrid.kt` 의 마지막 줄은 몇 칸을 세는가? 어느 행이 `false` 인가? `-Wextra` 컴파일에 진단이 나오는가?
- `tryval.kt` 의 `A`·`B`·`C` 와 그 앞의 `finally(…)` 줄은 어떤 순서로 무엇이 찍히는가? 컴파일 진단은?

### 7. Java 가 `Nothing` 을 「구현」하면 (경계)

- Kotlin 인터페이스의 `fun stop(): Nothing` 을 Java 가 `public Void stop() { return null; }` 로 구현했다. Kotlin 이 `s.stop()` 을 부르면 무슨 일이 생기는가? 그 일을 하는 명령은 누가 심었나?

### 8. `x + TODO()` (왜)

- `val y = x + TODO()`(`x: Int`)가 컴파일되지 않는다. 왜 **「타입 불일치」가 아니라 다른 문구**가 나오는가?

### 9. `@Throws` 가 바꾸는 것과 안 바꾸는 것 (경계)

- `@Throws(IOException::class)` 는 클래스 파일의 어디를 바꾸는가? Kotlin 호출자와 Java 호출자 각각에게 무엇이 달라지는가?

### 10. `finally` 의 `return` — Java·JS 와 견주면 (연결)

- 같은 모양을 `javac` 는 어떻게 다루는가(`-Xlint:finally`)? JS 의 같은 격자([`../../../js/syntax/32-error-handling-and-error/`](../../../js/syntax/32-error-handling-and-error/))와 칸 수가 같은가?

### 11. 바닥 타입의 이웃들 (연결)

- Kotlin `Nothing` · Rust `!` · TS `never` 는 무엇을 공유하는가? Go 는 왜 이 자리에 대응물이 필요 없는가?

### 12. 검사 예외가 사라진 자리 (왜)

- 검사 예외가 없어서 **컴파일러가 더 이상 해 주지 않는 일**은 무엇인가? `runCatching`·`Result` 가 그 자리를 메우는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
