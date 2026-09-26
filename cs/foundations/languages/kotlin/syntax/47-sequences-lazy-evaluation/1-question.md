# kotlin/syntax/47 — `Sequence` — 지연 평가, 언제 `List` 보다 싼가 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [42번 주제](../42-transformations-map-flatmap-associate-zip/)(변환 연산의 결과 타입 — `Sequence` 열)다.
> 문항 10개 중 예측형은 6개이고, 여섯 모두 코드블록이 붙는다.
> 이 주제의 모든 답은 **kotlinc 2.4.20 · Temurin JDK 21.0.5** 에서 실제로 던져 받은 것이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 사슬 다섯 × 두 모양 × 두 크기 (예측)

```kotlin
// grid47.kt
@file:Suppress("UNCHECKED_CAST")

var mc = 0
var fc = 0
val mf: (Int) -> Int = { mc++; it * 2 }
val ff: (Int) -> Boolean = { fc++; it > 5 }

fun stage(name: String, x: Any): Any = when (x) {
    is Sequence<*> -> {
        val s = x as Sequence<Int>
        when (name) {
            "map" -> s.map(mf)
            "filter" -> s.filter(ff)
            "sorted" -> s.sorted()
            "distinct" -> s.distinct()
            "take3" -> s.take(3)
            "first" -> s.first()
            "toList" -> s.toList()
            else -> error(name)
        }
    }
    else -> {
        val l = x as List<Int>
        when (name) {
            "map" -> l.map(mf)
            "filter" -> l.filter(ff)
            "sorted" -> l.sorted()
            "distinct" -> l.distinct()
            "take3" -> l.take(3)
            "first" -> l.first()
            "toList" -> l
            else -> error(name)
        }
    }
}

val chains = listOf(
    listOf("map", "filter", "first"),
    listOf("map", "filter", "toList"),
    listOf("map", "sorted", "filter", "first"),
    listOf("map", "distinct", "filter", "first"),
    listOf("map", "filter", "take3", "toList"),
)

class Cell(val calls: Int, val text: String)

fun run(chain: List<String>, n: Int, lazy: Boolean): Cell {
    mc = 0; fc = 0
    var x: Any = if (lazy) (0 until n).toList().asSequence() else (0 until n).toList()
    var collections = 0
    for ((i, name) in chain.withIndex()) {
        x = stage(name, x)
        if (i < chain.lastIndex && x is Collection<*>) collections++
    }
    return Cell(mc + fc, "map=$mc filter=$fc coll=$collections")
}

fun main() {
    println(listOf("chain", "n", "List", "Sequence").joinToString("\t"))
    var fewer = 0
    var cells = 0
    for (chain in chains) {
        for (n in listOf(10, 1000)) {
            val a = run(chain, n, lazy = false)
            val b = run(chain, n, lazy = true)
            val row = listOf(chain.joinToString(">"), "$n", a.text, b.text)
            check(row.size == 4)
            println(row.joinToString("\t"))
            cells++
            if (b.calls < a.calls) fewer++
        }
    }
    println("cells where the Sequence column made fewer lambda calls: $fewer / $cells")
}
```

- 각 칸의 `map=`·`filter=`·`coll=` 은 무엇인가? 마지막 줄의 `N / M` 은?

### 2. ★★★ 로그의 순서 (예측)

```kotlin
// order47.kt
fun main() {
    val src = listOf(3, 1, 2)
    println("-- A")
    src.map { println("  map $it"); it * 10 }
        .filter { println("  filter $it"); it > 10 }
        .also { println("  result $it") }
    println("-- B")
    src.asSequence()
        .map { println("  map $it"); it * 10 }
        .filter { println("  filter $it"); it > 10 }
        .toList()
        .also { println("  result $it") }
    println("-- C")
    src.asSequence()
        .map { println("  map $it"); it * 10 }
        .sorted()
        .filter { println("  filter $it"); it > 10 }
        .first()
        .also { println("  result $it") }
    println("-- D")
    listOf(3, 3, 1, 2).asSequence()
        .map { println("  map $it"); it * 10 }
        .distinct()
        .filter { println("  filter $it"); it < 25 }
        .first()
        .also { println("  result $it") }
    println("-- E")
    val pending = src.asSequence().map { println("  map $it"); it * 10 }
    println("-- F")
    println("  ${pending::class.java.name}")
}
```

- `-- A`\~`-- F` 사이에 각각 무엇이 어떤 순서로 찍히나? `C` 와 `D` 에서 `map` 은 몇 번 찍히나?

### 3. ★★ 단계마다 만들어지는 것 (예측)

```kotlin
// kinds47.kt
fun main() {
    val l = (0 until 10).toList()
    val a1 = l.map { it * 2 }
    val a2 = a1.filter { it > 5 }
    println("List      ${l::class.java.name} > ${a1::class.java.name} > ${a2::class.java.name}")
    val s0 = l.asSequence()
    val s1 = s0.map { it * 2 }
    val s2 = s1.filter { it > 5 }
    val s3 = s2.toList()
    println("Sequence  ${s0::class.java.name} > ${s1::class.java.name} > ${s2::class.java.name} > ${s3::class.java.name}")
    val t = s2.sorted()
    println("sorted    ${t::class.java.name}")
    val u = s2.distinct()
    println("distinct  ${u::class.java.name}")
}
```

- 네 줄에 찍히는 클래스 이름은 무엇인가? 리스트는 어느 자리에 있나?

### 4. ★★ 두 번 돌리면 (예측)

```kotlin
// once47.kt
fun twice(label: String, s: Sequence<Int>) {
    for (round in 1..2) {
        try {
            println("$label  round $round -> ${s.toList()}")
        } catch (e: IllegalStateException) {
            println("$label  round $round -> ${e::class.simpleName}: ${e.message}")
        }
    }
}

fun main() {
    twice("1 sequenceOf              ", sequenceOf(1, 2, 3))
    twice("2 List.asSequence()       ", listOf(1, 2, 3).asSequence())
    twice("3 generateSequence(seed)  ", generateSequence(1) { if (it < 3) it + 1 else null })
    var i = 0
    twice("4 generateSequence { }    ", generateSequence { if (i < 3) ++i else null })
    twice("5 sequence { }            ", sequence { println("   block starts"); yield(1); yield(2) })
    twice("6 Iterator.asSequence()   ", listOf(1, 2, 3).iterator().asSequence())
    twice("7 Sequence { iterator }   ", Sequence { listOf(1, 2).iterator() })
}
```

- 일곱 가지 각각의 `round 1`·`round 2` 는 무엇인가? `block starts` 는 몇 번 찍히나?

### 5. ★★ 바이트코드에 박힌 리스트 (예측)

```kotlin
// code47.kt
fun viaList(l: List<Int>): Int = l.map { it * 2 }.filter { it > 5 }.first()

fun viaSequence(l: List<Int>): Int = l.asSequence().map { it * 2 }.filter { it > 5 }.first()

fun main() {
    println("${viaList(listOf(1, 2, 3, 4))} ${viaSequence(listOf(1, 2, 3, 4))}")
}
```

- `javap -c` 로 두 함수를 보면 `new java/util/ArrayList` 는 각각 몇 번 나오나? `viaSequence` 에는 무엇이 대신 있나?

### 6. ★ 무한 수열과 앞 몇 개 (예측)

```kotlin
// form47.kt
fun main() {
    val powers = generateSequence(1) { it * 2 }.takeWhile { it < 100 }.toList()
    println("powers  $powers")

    val lines = listOf("# head", "a=1", "", "b=2", "# note", "c=3", "d=4")
    val firstTwo = lines.asSequence()
        .filter { it.isNotBlank() && !it.startsWith("#") }
        .map { it.substringBefore("=") }
        .take(2)
        .toList()
    println("keys    $firstTwo")

    val fib = sequence {
        var a = 0
        var b = 1
        while (true) {
            yield(a)
            val next = a + b
            a = b
            b = next
        }
    }
    println("fib     ${fib.take(8).toList()}")
}
```

- 세 줄의 출력은 무엇인가?

### 7. `sorted` 와 `distinct` 는 둘 다 「상태 있음」인데 (왜)

- 2번에서 두 사슬이 앞쪽을 당기는 방식이 다른 이유는 무엇인가? stdlib 는 각각 무엇을 쥐나?

### 8. `Sequence` 가 손해인 경우 (경계)

- 1번에서 호출을 못 줄인 칸의 사슬은 무엇이고, 그 사슬에서 `Sequence` 가 **더** 만드는 것은 무엇인가? 이 문서가 그 손해를 시간으로 말하지 않는 이유는?

### 9. 두 번 돌 수 있는지는 누가 정하나 (경계)

- `Sequence` 인터페이스의 KDoc 은 두 번 도는 것에 대해 무엇을 말하나? 한 번 제한은 어떻게 구현돼 있나?

### 10. Java `Stream` 과 (연결)

- [Java 45번](../../../java/syntax/45-intermediate-operations/)의 `Stream` 처리 순서와 2번의 `B`·`C` 는 어떻게 같은가? Kotlin 이 지연으로 **넘어가는 방식**은 Java 와 무엇이 다른가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
