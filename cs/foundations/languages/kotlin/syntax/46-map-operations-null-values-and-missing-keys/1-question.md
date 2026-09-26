# kotlin/syntax/46 — `Map` 조작 — `getOrPut`/`getOrElse`/`mapValues`/`filterKeys` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [41번 주제](../41-collection-creation-and-copying/)(만드는 꼴과 복사)다.
> 문항 10개 중 예측형은 5개이고, 그중 코드블록이 붙는 것은 4개다.
> 이 주제의 모든 답은 **kotlinc 2.4.20 · Temurin JDK 21.0.5** 에서 실제로 던져 받은 것이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 세 가지 맵 상태 × 열세 가지 읽기·넣기 (예측)

```kotlin
// grid46.kt
@file:OptIn(ExperimentalStdlibApi::class)

var calls = 0
fun nine(): Int? { calls++; return 9 }

val states = listOf("absent", "null-value", "present")

fun fresh(state: String): MutableMap<String, Int?> = when (state) {
    "absent" -> mutableMapOf()
    "null-value" -> mutableMapOf("k" to null)
    else -> mutableMapOf("k" to 1)
}

val probes: List<Pair<String, (MutableMap<String, Int?>) -> Any?>> = listOf(
    "m[\"k\"]" to { m -> m["k"] },
    "m.get(\"k\")" to { m -> m.get("k") },
    "m.getValue(\"k\")" to { m -> m.getValue("k") },
    "m.getOrElse(\"k\") { 9 }" to { m -> m.getOrElse("k") { nine() } },
    "m.getOrDefault(\"k\", 9)" to { m -> m.getOrDefault("k", 9) },
    "m.getOrPut(\"k\") { 9 }" to { m -> m.getOrPut("k") { nine() } },
    "m.containsKey(\"k\")" to { m -> m.containsKey("k") },
    "m[\"k\"] ?: 9" to { m -> m["k"] ?: nine() },
    "m.withDefault { 9 }.getValue(\"k\")" to { m -> m.withDefault { nine() }.getValue("k") },
    "m.withDefault { 9 }[\"k\"]" to { m -> m.withDefault { nine() }["k"] },
    "m.getOrElseIfMissing(\"k\") { 9 }" to { m -> m.getOrElseIfMissing("k") { nine() } },
    "m.getOrPutIfMissing(\"k\") { 9 }" to { m -> m.getOrPutIfMissing("k") { nine() } },
    "m.getOrPutIfNull(\"k\") { 9 }" to { m -> m.getOrPutIfNull("k") { nine() } },
)

fun run(state: String, f: (MutableMap<String, Int?>) -> Any?): Pair<String, String> {
    val m = fresh(state)
    calls = 0
    val r = try { f(m).toString() } catch (e: Exception) { "throws " + e::class.simpleName }
    return r to "$r · $m · λ$calls"
}

fun main() {
    println((listOf("form") + states).joinToString("\t"))
    var same = 0
    for ((name, f) in probes) {
        val cells = states.map { run(it, f) }
        val row = listOf(name) + cells.map { it.second }
        check(row.size == 1 + states.size)
        println(row.joinToString("\t"))
        if (cells[0].first == cells[1].first) same++
    }
    println("rows where the absent and null-value results are the same: $same / ${probes.size}")
}
```

- 각 칸(함수 × `absent`·`null-value`·`present`)에서 **돌려준 값 · 호출 뒤 맵 · 람다 호출 수**는 무엇인가? 던지는 칸은 어디인가?

### 2. ★★ 두 상태를 같은 결과로 답하는 행 (예측)

- 1번에서 `absent` 열과 `null-value` 열의 **돌려준 값**이 같은 행은 어느 것들인가? 마지막 줄의 `N / M` 은?

### 3. ★★★ 캐시 · 기본값 감싸기 · 거른 맵 (예측)

```kotlin
// shape46.kt
fun main() {
    val cache = mutableMapOf<String, String?>()
    repeat(3) { i ->
        val v = cache.getOrPut("u") { println("   compute #$i"); null }
        println("1 round $i -> $v  $cache")
    }

    val d = mapOf("a" to 1).withDefault { 0 }
    println("2 d[\"b\"]              = ${d["b"]}")
    println("3 d.getValue(\"b\")     = ${d.getValue("b")}")
    println("4 d.getOrDefault(\"b\", -1) = ${d.getOrDefault("b", -1)}")
    println("5 d                   = $d")
    val derived = d.filterKeys { true }
    try {
        println("6 derived.getValue(\"b\") = ${derived.getValue("b")}")
    } catch (e: Exception) {
        println("6 derived.getValue(\"b\") -> ${e::class.simpleName}: ${e.message}")
    }

    val src = mutableMapOf("a" to 1, "b" to 2, "c" to 3)
    val fk = src.filterKeys { it != "b" }
    val fv = src.filterValues { it > 1 }
    src["a"] = 100
    println("7 src=$src  fk=$fk  fv=$fv")
    println("8 fk === src: ${fk === src}  ${fk::class.java.name}")
}
```

- 돌리면 `1`\~`8` 줄(과 그 사이의 `compute` 로그)은 각각 무엇인가? `compute` 로그는 몇 줄인가?

### 4. ★★ 같은 객체, 두 가지 받는 타입 (예측)

```kotlin
// conc46.kt
import java.util.concurrent.ConcurrentHashMap

fun viaConcurrent(m: ConcurrentHashMap<String, Int>): Int = m.getOrPut("k") { 1 }

fun viaMutable(m: MutableMap<String, Int>): Int = m.getOrPut("k") { 1 }

fun main() {
    val c = ConcurrentHashMap<String, Int>()
    println("${viaConcurrent(c)} ${viaMutable(c)} $c")
}
```

- `javap -c` 로 두 함수를 보면 각각 어떤 `Map` 메서드 호출이 박혀 있나?

### 5. ★ 단어 세기와 묶기 (예측)

```kotlin
// form46.kt
fun main() {
    val words = listOf("tea", "cake", "tea", "coffee", "cake", "tea")

    val counts = mutableMapOf<String, Int>()
    for (w in words) counts[w] = counts.getOrElse(w) { 0 } + 1

    val byLength = mutableMapOf<Int, MutableList<String>>()
    for (w in words.distinct()) byLength.getOrPut(w.length) { mutableListOf() }.add(w)

    val price = mapOf("tea" to 3, "cake" to 5, "coffee" to 4)
    val doubled: Map<String, Int> = price.mapValues { (_, v) -> v * 2 }
    val short: Map<String, Int> = price.filterKeys { it.length <= 4 }
    val cheap: Map<String, Int> = price.filterValues { it < 5 }

    println("counts   $counts")
    println("byLength $byLength")
    println("doubled  $doubled")
    println("short    $short")
    println("cheap    $cheap")
    println("missing  ${price["juice"] ?: 0}")
}
```

- 여섯 줄의 출력은 무엇인가?

### 6. `getOrPut` 이 `{k=null}` 을 바꾸는 것은 누가 정했나 (경계)

- 1번의 `getOrPut` 행이 보인 동작은 stdlib 의 **계약**인가, 구현이 우연히 그런 것인가? 구현은 무엇으로 「없음」을 판단하나?

### 7. `getOrDefault` 와 `getOrElse` 는 무엇을 보나 (왜)

- `{k=null}` 칸에서 두 함수가 갈리는 이유는 무엇인가? `getOrDefault` 는 어디서 온 함수인가?

### 8. `withDefault` 의 기본값이 닿는 범위 (경계)

- `withDefault` 로 감싼 맵에서 기본값이 **나오는** 읽기와 **안 나오는** 읽기는 무엇인가? KDoc 은 그 범위를 어떻게 적나?

### 9. `ConcurrentHashMap.getOrPut` 의 약속 (왜)

- `ConcurrentMap` 판 `getOrPut` 의 KDoc 은 무엇을 약속하고 무엇을 약속하지 **않나**? 이 문서가 경쟁 실행으로 재지 않은 이유는?

### 10. Java `computeIfAbsent` 와 (연결)

- [Java 41번](../../../java/syntax/41-map-api-merge-compute/)의 격자에서 `putIfAbsent`·`computeIfAbsent` 는 `{k=null}` 칸을 어떻게 다루나? Kotlin 의 어느 함수와 같은 편인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
