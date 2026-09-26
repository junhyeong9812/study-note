# kotlin/syntax/58 — null 처리 관용구 — `?.let`·`requireNotNull`·엘비스 + `return` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [03번 주제](../03-null-safe-types/)(`?.`·`?:`·`!!` 의 문법)와 [51번 주제](../51-preconditions-require-check-error-todo/)(`require`/`check`/`error` 가 던지는 것)다.
> 문항 11개 중 예측형은 6개이고, 그중 다섯에 코드블록이 붙는다(3번은 2번의 소스를 그대로 다시 컴파일한다).
> 이 주제의 모든 답은 **kotlinc 2.4.20 · Temurin JDK 21.0.5** 에서 실제로 던져 받은 것이다.
> ★ 소스 펜스의 첫 줄(파일명 주석)은 실파일에 없다 — 줄 번호는 그 다음 줄을 1 로 센다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 경계 넷 × 수단 여섯 (예측)

```kotlin
// grid58.kt
// 경계 넷 × 수단 여섯 — 값이 null 일 때 무엇이 어디서 드러나나.
val means = listOf("?: return", "?.let", "requireNotNull", "checkNotNull", "!!", "?: error()")

// (1) 외부 입력 파싱 — 숫자가 아닌 문자열
fun parseLayer(m: String, raw: String): Int? {
    val v: Int? = raw.toIntOrNull()
    return when (m) {
        "?: return" -> { val n = v ?: return null; n * 2 }
        "?.let" -> v?.let { it * 2 }
        "requireNotNull" -> requireNotNull(v) { "not a number: $raw" } * 2
        "checkNotNull" -> checkNotNull(v) { "not a number: $raw" } * 2
        "!!" -> v!! * 2
        else -> (v ?: error("not a number: $raw")) * 2
    }
}

// (2) 공개 API 인자 — 호출한 쪽이 null 을 넘겼다
fun apiLayer(m: String, name: String?): Int? {
    return when (m) {
        "?: return" -> { val n = name ?: return null; n.length }
        "?.let" -> name?.let { it.length }
        "requireNotNull" -> requireNotNull(name) { "name is required" }.length
        "checkNotNull" -> checkNotNull(name) { "name is required" }.length
        "!!" -> name!!.length
        else -> (name ?: error("name is required")).length
    }
}

// (3) 내부 불변식 — 있어야 할 키가 맵에 없다
val prices = mapOf("apple" to 3)
fun coreLayer(m: String, key: String): Int? {
    val p: Int? = prices[key]
    return when (m) {
        "?: return" -> { val n = p ?: return null; n * 10 }
        "?.let" -> p?.let { it * 10 }
        "requireNotNull" -> requireNotNull(p) { "no price for $key" } * 10
        "checkNotNull" -> checkNotNull(p) { "no price for $key" } * 10
        "!!" -> p!! * 10
        else -> (p ?: error("no price for $key")) * 10
    }
}

// (4) 표시 계층 — 선택 항목(별명)이 비어 있다
class Profile(val nickname: String?)
fun viewLayer(m: String, u: Profile): Int? {
    val nick = u.nickname
    return when (m) {
        "?: return" -> { val n = nick ?: return null; n.length }
        "?.let" -> nick?.let { it.length }
        "requireNotNull" -> requireNotNull(nick) { "nickname missing" }.length
        "checkNotNull" -> checkNotNull(nick) { "nickname missing" }.length
        "!!" -> nick!!.length
        else -> (nick ?: error("nickname missing")).length
    }
}

val layers: List<Pair<String, (String) -> Int?>> = listOf(
    "parse" to { m -> parseLayer(m, "12x") },
    "api" to { m -> apiLayer(m, null) },
    "core" to { m -> coreLayer(m, "pear") },
    "view" to { m -> viewLayer(m, Profile(null)) },
)

fun main() {
    println(listOf("layer", "means", "thrown", "message", "first frame", "caller got").joinToString("\t"))
    val kinds = linkedMapOf<String, Int>()
    val byMeans = linkedMapOf<String, MutableSet<String>>()
    var cells = 0
    for ((layer, call) in layers) for (m in means) {
        cells++
        val row = try {
            val r = call(m)
            kinds.merge("none", 1, Int::plus)
            byMeans.getOrPut(m) { mutableSetOf() } += "none"
            listOf(layer, m, "-", "-", "-", "$r")
        } catch (e: Exception) {
            val k = e.javaClass.simpleName
            kinds.merge(k, 1, Int::plus)
            byMeans.getOrPut(m) { mutableSetOf() } += k
            val f = e.stackTrace[0]
            listOf(layer, m, k, "${e.message}", "${f.methodName}:${f.lineNumber}", "(exception)")
        }
        check(row.size == 6) { "column count" }
        println(row.joinToString("\t"))
    }
    println("thrown kinds: " + kinds.entries.joinToString(" · ") { "${it.key} ${it.value}" } + " (of $cells)")
    println("means whose outcome differs between layers: ${byMeans.values.count { it.size > 1 }} / ${byMeans.size}")
    println("cells with no exception: ${kinds["none"] ?: 0} / $cells")
}
```

- 24행 각각의 `thrown`·`message`·`first frame`·`caller got` 은 무엇인가? 마지막 세 줄의 수는?

### 2. ★★★ Java 가 준 `null` 의 네 갈래 (예측)

```java
// Store58.java
import java.util.HashMap;
import java.util.Map;

public class Store58 {
    private static final Map<String, String> names = new HashMap<>();
    static { names.put("u1", "kim"); }

    public static String findName(String id) {
        return names.get(id);
    }
}
```

```kotlin
// plat58.kt
// Java 가 준 null 이 어디서 터지나 — 태어난 줄과 터진 줄
fun here(): Int = Throwable().stackTrace[1].lineNumber

fun greet(name: String): String = "hi " + name
fun firstLength(names: List<String>): Int = names[0].length

fun probe(label: String, block: () -> Int) {
    try {
        block()
        println("$label -> no exception")
    } catch (e: Exception) {
        val f = e.stackTrace[0]
        println("$label -> ${e.javaClass.simpleName}: ${e.message}")
        println("    first frame ${f.methodName}:${f.lineNumber}")
    }
}

fun main() {
    var born = 0
    probe("A") {
        born = here(); val n = Store58.findName("u9")!!
        n.length
    }
    println("    null born at line $born")
    probe("B") {
        val n = Store58.findName("u9"); born = here()
        greet(n).length
    }
    println("    null born at line $born")
    probe("C") {
        val n = Store58.findName("u9"); born = here()
        val names = listOf(n)
        firstLength(names)
    }
    println("    null born at line $born")
    probe("D") {
        val n = Store58.findName("u9"); born = here()
        val names: List<String> = listOf(n)
        names.size
    }
    println("    null born at line $born")
}
```

- `A`\~`D` 각각 무엇이 찍히나? 첫 프레임은 어느 함수의 몇째 줄이고, `null born at line` 과 얼마나 떨어져 있나?

### 3. ★★ 같은 소스를 `-Xno-call-assertions` 로 컴파일하면 (예측)

- 2번의 `plat58.kt` 를 `kotlinc -Xno-call-assertions` 로 다시 컴파일해 돌리면 `A`\~`D` 중 어느 줄이 바뀌고, 무엇으로 바뀌나?

### 4. ★★ 보내기 두 벌과 상태 다섯 줄 (예측)

```kotlin
// let58.kt
class User(val id: String, val email: String?)

val users = listOf(
    User("u1", "a@x"), User("u2", null), User("u3", "c@x"), User("u4", null), User("u5", "e@x"),
)
val sent = mutableListOf<String>()
fun send(to: String) { sent += to }

// 1) ?.let 로 보낸다
fun notifyA(u: User) {
    u.email?.let { send(it) }
}

// 2) ?: 로 멈춘다
fun notifyB(u: User) {
    val to = u.email ?: run { System.err.println("skip ${u.id}"); return }
    send(to)
}

// 3) ?.let { } ?: 대안
fun lookup(email: String): String? = if (email.startsWith("a")) null else "ok"
fun statusOf(u: User): String = u.email?.let { lookup(it) } ?: "no email"

fun main() {
    users.forEach(::notifyA)
    println("A sent ${sent.size} of ${users.size}: $sent")
    sent.clear()
    users.forEach(::notifyB)
    println("B sent ${sent.size} of ${users.size}: $sent")
    for (u in users) println("status ${u.id} = ${statusOf(u)}")
}
```

- 표준 출력과 표준 오류에 각각 무엇이 찍히나? `status` 다섯 줄은 무엇인가?

### 5. ★★ 네 함수를 컴파일하면 (예측)

```kotlin
// smart58.kt
class Form(var name: String?, val code: String?)

fun a(f: Form): Int {
    if (f.name != null) return f.name.length
    return 0
}

fun b(f: Form): Int {
    if (f.code != null) return f.code.length
    return 0
}

fun c(f: Form): Int = f.name?.let { it.length } ?: 0

fun d(f: Form): Int {
    val n = f.name ?: return 0
    return n.length
}

fun main() {
    val f = Form("kim", "k1")
    println(listOf(a(f), b(f), c(f), d(f)))
}
```

- 이 파일을 컴파일하면 진단이 몇 개, 어느 함수에서 나오나? 문구는 무엇인가?

### 6. ★ 한 요청이 네 계층을 지나면 (예측)

```kotlin
// form58.kt
// 한 요청이 네 계층을 지난다 — 계층마다 다른 수단
class Order(val item: String, val qty: Int, val note: String?)

val stock = mapOf("apple" to 3, "pear" to 5)

// 외부 입력: 실패를 값으로 돌려준다
fun parse(line: String): Order? {
    val parts = line.split(",")
    val item = parts.getOrNull(0)?.takeIf { it.isNotBlank() } ?: return null
    val qty = parts.getOrNull(1)?.toIntOrNull() ?: return null
    return Order(item, qty, parts.getOrNull(2))
}

// 공개 API: 인자 계약
fun place(item: String?, qty: Int): Int {
    val name = requireNotNull(item) { "item is required" }
    require(qty > 0) { "qty must be positive: $qty" }
    return reserve(name, qty)
}

// 내부: 있어야 할 것
private fun reserve(item: String, qty: Int): Int {
    val left = checkNotNull(stock[item]) { "unknown item passed validation: $item" }
    return left - qty
}

// 표시: 없어도 되는 것
fun render(o: Order, left: Int): String =
    "${o.item} x${o.qty}" + (o.note?.let { " ($it)" } ?: "") + " left=$left"

fun handle(line: String) {
    val o = parse(line) ?: run { println("rejected: '$line'"); return }
    try {
        println(render(o, place(o.item, o.qty)))
    } catch (e: IllegalArgumentException) {
        println("caller error: ${e.message}")
    } catch (e: IllegalStateException) {
        println("bug: ${e.message}")
    }
}

fun main() {
    listOf("apple,2", "pear,1,gift", "apple,x", ",3", "kiwi,1", "pear,0").forEach(::handle)
}
```

- 여섯 줄의 출력은 무엇인가?

### 7. `?: return` 과 `?.let` 은 1번에서 같은 결과인데 (왜)

- 부른 쪽이 받은 것이 같은데도 「여기서 멈춘다」를 `?: return` 으로 적는 편이 나은 이유는 무엇인가? 4번의 표준 오류는 그 차이의 어느 쪽을 보여 주나?

### 8. 내부 맵 조회에 `requireNotNull` 을 두면 (왜)

- 1번의 `coreLayer` 에서 `requireNotNull` 과 `checkNotNull` 은 어떤 예외를 던지나? 로그를 보는 사람에게 그 차이가 왜 중요한가?

### 9. `?.let { … } ?: 대안` 은 `if-else` 인가 (경계)

- 4번의 `statusOf` 가 `u1` 에 대해 낸 값의 까닭은 무엇인가? 같은 뜻을 안전하게 쓰려면 어떻게 바꾸나?

### 10. 관찰과 권고 (경계)

- 2-summary (5)의 「계층 → 수단」 표에서 **실행으로 증명된 것**과 **이 문서의 판단**은 각각 무엇인가? 1번의 `0 / 6` 이 그 경계를 어떻게 긋나?

### 11. 스택의 맨 위 줄을 원인으로 읽어도 되나 (연결)

- [03번 주제](../03-null-safe-types/)의 `!!` 와 [05번 주제](../05-platform-types/)의 A/B/C, 그리고 2번의 `A`\~`D` 중 **첫 프레임이 곧 원인 줄**인 것과 **아닌 것**은 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
