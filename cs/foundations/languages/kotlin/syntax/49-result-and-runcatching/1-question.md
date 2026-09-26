# kotlin/syntax/49 — `Result` 와 `runCatching` — 예외를 값으로 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [34번 주제](../34-exceptions-nothing-and-try-expression/)(검사 예외 없음·`Nothing`·`try` 식)다.
> 문항 10개 중 예측형은 6개이고, 그중 코드블록이 붙는 것은 5개다.
> 이 주제의 모든 답은 **kotlinc 2.4.20 · Temurin JDK 21.0.5** 에서 실제로 던져 받은 것이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ `Result` 를 쓰는 열한 자리 × 다섯 판 (예측)

```kotlin
// ret49.kt
fun p1(): Result<Int> = runCatching { 1 }                                  // return
val p2: Result<Int> = runCatching { 2 }                                    // property
fun p3(): Result<Int>? = null                                              // nullable-return
fun p4(): List<Result<Int>> = listOf(runCatching { 4 })                    // list-element
fun p5(r: Result<Int>): Int = r.getOrThrow()                               // parameter
fun p6(r: Result<Int>?): Int? = r?.getOrNull()                             // safe-call
fun p7(r: Result<Int>?): Result<Int> = r!!                                 // not-null-assert
fun p8(r: Result<Int>?): Result<Int> = r ?: runCatching { 8 }              // elvis
interface P9 { fun get(): Result<Int> }                                    // abstract-member
suspend fun p10(): Result<Int> = runCatching { 10 }                        // suspend-return
lateinit var p11: Result<Int>                                              // lateinit
```

```python
# grid49.py
import re
import subprocess

SRC = "ret49.kt"
VERSIONS = ["2.0", "2.1", "2.2", "2.3", "2.4"]
CONTROL = "lateinit"

probes = {}
order = []
for n, line in enumerate(open(SRC, encoding="utf-8"), 1):
    m = re.search(r"// (\S+)$", line.rstrip("\n"))
    if m:
        probes[n] = m.group(1)
        order.append(m.group(1))

result = {}
for v in VERSIONS:
    run = subprocess.run(["kotlinc", "-language-version", v, SRC, "-d", "o49v" + v.replace(".", "")],
                         capture_output=True, text=True)
    first = {}
    for line in (run.stdout + run.stderr).splitlines():
        m = re.match(r"ret49\.kt:(\d+):\d+: error: (.*)$", line)
        if m and int(m.group(1)) not in first:
            first[int(m.group(1))] = m.group(2)
    for n, name in probes.items():
        result[(name, v)] = "error: " + first[n] if n in first else "ok"
    result[("exit", v)] = str(run.returncode)

print("\t".join(["probe"] + VERSIONS))
blocked = cells = 0
for name in order + ["exit"]:
    row = [result[(name, v)] for v in VERSIONS]
    if len(row) != len(VERSIONS):
        raise SystemExit("cell count mismatch: " + name)
    print("\t".join([name] + row))
    if name in (CONTROL, "exit"):
        continue
    for cell in row:
        cells += 1
        if cell != "ok":
            blocked += 1
print("blocked cells outside the control row: %d / %d" % (blocked, cells))
```

- 각 칸은 `ok` 인가 진단인가? 판마다의 종료 코드와 마지막 줄의 `N / M` 은?

### 2. ★★ 2.0 아래 판 (예측)

- 같은 파일을 `kotlinc -language-version 1.9 ret49.kt -d o49x` 로 던지면 무엇이 나오나?

### 3. ★★ JVM 에서의 이름과 타입 (예측)

```kotlin
// val49.kt
@JvmInline
value class Id(val raw: Int)

fun make(): Result<Int> = runCatching { 1 }

fun take(r: Result<Int>): Int = r.getOrThrow()

fun takeId(i: Id): Int = i.raw

fun makeId(): Id = Id(7)

val kept: Result<Int> = make()

fun many(): List<Result<Int>> = listOf(make())

fun main() {
    println("${make()} ${take(make())} $kept ${many()} ${takeId(makeId())}")
}
```

- `javap -p Val49Kt.class` 에서 `make`·`take`·`takeId`·`makeId`·`kept`·`many` 의 서명은 각각 어떻게 보이나? `box-impl` 은 어느 함수에 있나?

### 4. ★★★ 다섯 가지 던지기 × 두 가지 잡기 (예측)

```kotlin
// catch49.kt
import java.util.concurrent.CancellationException

val throwers: List<Pair<String, () -> Int>> = listOf(
    "error(\"x\")" to { error("x") },
    "\"x\".toInt()" to { "x".toInt() },
    "TODO()" to { TODO() },
    "throw AssertionError()" to { throw AssertionError("a") },
    "throw CancellationException()" to { throw CancellationException("c") },
)

fun byRunCatching(f: () -> Int): String =
    runCatching(f).exceptionOrNull()?.let { "failure " + it::class.simpleName } ?: "success"

fun byCatchException(f: () -> Int): String =
    try { f(); "success" } catch (e: Exception) { "caught " + e::class.simpleName } catch (e: Throwable) { "escaped " + e::class.simpleName }

fun main() {
    println(listOf("thrower", "runCatching", "catch (e: Exception)", "is Exception").joinToString("\t"))
    var onlyRunCatching = 0
    for ((name, f) in throwers) {
        val a = byRunCatching(f)
        val b = byCatchException(f)
        val kind = runCatching(f).exceptionOrNull() is Exception
        val row = listOf(name, a, b, "$kind")
        check(row.size == 4)
        println(row.joinToString("\t"))
        if (a.startsWith("failure") && b.startsWith("escaped")) onlyRunCatching++
    }
    println("rows held by runCatching but not by catch (e: Exception): $onlyRunCatching / ${throwers.size}")
}
```

- 각 행의 `runCatching` 열·`catch (e: Exception)` 열·`is Exception` 열은? 마지막 줄의 `N / M` 은?

### 5. ★★ 상자를 열고 바꾸기 (예측)

```kotlin
// chain49.kt
fun main() {
    val ok: Result<Int> = runCatching { 21 }
    val bad: Result<Int> = runCatching { "x".toInt() }
    println("1 $ok | $bad")
    println("2 ${ok.getOrNull()} | ${bad.getOrNull()} | ${bad.exceptionOrNull()?.message}")
    println("3 ${ok.getOrElse { -1 }} | ${bad.getOrElse { -1 }} | ${bad.getOrDefault(0)}")
    println("4 ${ok.map { it * 2 }} | ${bad.map { it * 2 }}")
    println("5 ${ok.fold({ "v=$it" }, { "e=${it::class.simpleName}" })} | ${bad.fold({ "v=$it" }, { "e=${it::class.simpleName}" })}")
    println("6 ${bad.recover { 0 }} | ${ok.recover { 0 }}")
    println("7 ${ok.mapCatching { check(it > 100) { "too small" }; it }}")
    try {
        println("8 ${ok.map { check(it > 100) { "too small" }; it }}")
    } catch (e: IllegalStateException) {
        println("8 -> ${e::class.simpleName}: ${e.message}")
    }
    try {
        println("9 ${bad.getOrThrow()}")
    } catch (e: NumberFormatException) {
        println("9 -> ${e::class.simpleName}: ${e.message}")
    }
}
```

- `1`\~`9` 줄은 각각 무엇인가? `8` 줄은 어느 쪽 갈래가 찍나?

### 6. ★ 포트 파싱 (예측)

```kotlin
// form49.kt
fun parsePort(s: String): Result<Int> = runCatching {
    val n = s.trim().toInt()
    require(n in 1..65535) { "port out of range: $n" }
    n
}

fun main() {
    for (input in listOf("8080", " 443 ", "http", "70000")) {
        val text = parsePort(input).fold(
            onSuccess = { "ok $it" },
            onFailure = { "fail ${it::class.simpleName}: ${it.message}" },
        )
        println("[$input] $text")
    }
    val ports = listOf("80", "x", "22").map { parsePort(it) }
    println("all    $ports")
    println("valid  ${ports.mapNotNull { it.getOrNull() }}")
}
```

- 여섯 줄의 출력은 무엇인가?

### 7. 옛 제한의 흔적은 어디에 있나 (경계)

- 이 판에서 1.4 로 컴파일해 볼 수 없는데, 「반환 타입 제한이 몇 판에서 풀렸나」를 무엇으로 확인할 수 있나? 그 창이 **못 보는** 것은?

### 8. `runCatching` 이 잡는 범위는 누가 정했나 (경계)

- 4번의 결과는 KDoc 계약인가 구현인가? `TODO()` 가 `runCatching` 안에 있으면 무엇이 조용히 일어나나?

### 9. `map` 대 `mapCatching` (왜)

- `Result` 를 돌려주는 사슬인데도 `map` 안의 예외가 밖으로 새는 이유는 무엇인가? KDoc 은 이것을 어떻게 적나?

### 10. Rust `Result<T, E>` · Go `(값, error)` 와 (연결)

- [Rust 22번](../../../rust/syntax/22-result-question-mark-and-from/)·[Go 23번](../../../go/syntax/23-error-interface-and-errors-as-values/)의 오류 값과 Kotlin `Result<T>` 는 **서명이 말해 주는 것**과 **컴파일러가 강제하는 것**에서 어떻게 다른가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
