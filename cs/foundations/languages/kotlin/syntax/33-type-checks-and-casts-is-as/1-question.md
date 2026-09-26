# kotlin/syntax/33 — 타입 검사·캐스트: `is`/`as`/`as?` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [04번 주제](../04-smart-casts/)다 — 스마트 캐스트가 깨지는 자리를 **`null` 검사**로 거기서 봤다.
> 문항 11개 중 코드블록이 붙는 예측형은 6개다.
> 바이트코드를 묻는 문항은 **`kotlinc` 기본 `-jvm-target`(1.8)** 기준이다.
> 이 주제의 모든 답은 **kotlinc 2.4.20 · JRE 21.0.5** 에서 실제로 던져 받은 것이다(C# 은 **.NET SDK 10.0.401**).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ `is`·`!is`·`as`·`as?`·`as String?` (예측)

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

- `A`\~`D` 에 무엇이 찍히는가? ★ `D` 줄의 예외 **클래스 이름**은?
- `c3`·`c4`·`c5` 는 각각 어떤 명령들로 번역되는가?

### 2. ★★ 제네릭 타입을 `is` 로 물으면 (예측)

```kotlin
// erase.kt
fun f1(x: Any) = x is List<String>
fun f2(x: Any) = x is List<*>
fun f3(x: List<Any>) = x is List<String>
fun f4(x: Collection<String>) = x is List<String>
fun <T> f5(x: Any) = x is T
```

- 다섯 함수 중 컴파일되는 것은 어느 것이고, 막히는 것은 무엇이라고 말하는가?

### 3. ★★ 비검사 캐스트와 수 캐스트 (예측)

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

- 컴파일 진단은 **몇 번째 줄에 무엇이** 나오는가? `A`\~`E` 에 무엇이 찍히는가?
- 3번째 줄의 캐스트가 틀렸다면, 예외는 **몇 번째 줄**에서 나는가?

### 4. ★★★ `is` 뒤 스마트 캐스트 — 같은 모듈 (예측)

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

- `t1`\~`t11` 중 막히는 것은 어느 것이고, 각각 무엇이라고 말하는가? 이유를 **말하지 않는** 문구가 나오는 것은?

### 5. ★ 다른 모듈의 프로퍼티 (예측)

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

- `lib33.kt` 를 따로 컴파일한 뒤 그것을 클래스패스로 주고 `use33.kt` 를 컴파일하면 `u1`·`u2` 는 각각 어떻게 되는가?

### 6. ★★ Java 가 준 `null` 을 캐스트하면 (예측)

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

- 컴파일 진단이 나오는가? `A`\~`D` 에 무엇이 찍히는가?
- `A` 와 `C` 는 같은 예외 클래스인가? 메시지는 같은가?

### 7. `null as String` 의 예외 (왜)

- JVM 의 `checkcast` 는 `null` 을 어떻게 다루는가? 그래서 kotlinc 는 무엇을 더 심었고, 그 결과 예외 종류가 어떻게 되는가?
- `catch (e: ClassCastException)` 으로 이 경우를 잡을 수 있는가?

### 8. `1 as Long` (경계)

- 캐스트는 무엇을 바꾸고 무엇을 안 바꾸는가? 정적 타입이 `Int` 일 때와 `Any` 일 때 컴파일러의 반응은 어떻게 다른가?

### 9. `is UserId` (연결)

- `typealias UserId = String` 일 때 `x is UserId` 의 바이트코드는? [29번 주제](../29-type-aliases-and-nested-type-aliases/)의 결론과 어떻게 이어지는가?

### 10. C# 의 `as` (연결)

- C# 의 `o as string` 과 `(string)o` 는 각각 Kotlin 의 무엇에 해당하는가? C# 이 `o as int` 를 거부하는 이유는?

### 11. `as` 와 `as?` 를 고르는 기준 (왜)

- 「`as?` 가 더 안전하니 늘 `as?` 를 쓴다」는 무엇을 잃는가? 두 연산자를 고르는 기준은 무엇이어야 하는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
