# kotlin/syntax/55 — `Flow` — 콜드 스트림·연산자·`collect` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [53번 주제](../53-structured-concurrency-job-cancellation-exceptions/)(구조적 동시성 — 취소와 예외 전파)이고, 짝은 [47번 주제](../47-sequences-lazy-evaluation/)(`Sequence` — 같은 지연 평가의 동기판)다.
> 문항 11개 중 예측형은 6개이고, 여섯 모두 코드블록이 붙는다.
> 이 주제의 모든 답은 **kotlinc 2.4.20 · Temurin JDK 21.0.5 · kotlinx-coroutines 1.11.0** 에서 실제로 던져 받은 것이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 만들고 두 번 모으기 (예측)

```kotlin
// cold55.kt
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.runBlocking

fun main() = runBlocking {
    println("[1] build")
    val f = flow {
        println("  body starts")
        emit(1)
        println("  body after emit")
    }
    val g = f.map { println("  map $it"); it * 10 }
    println("[2] built, not collected yet")
    println("[3] first collect")
    g.collect { println("  got $it") }
    println("[4] second collect")
    g.collect { println("  got $it") }
    println("[5] end")
}
```

- `[1]`\~`[5]` 사이에 각각 무엇이 어떤 순서로 찍히나? `got 10` 과 `body after emit` 중 무엇이 먼저인가?

### 2. ★★★ 사슬 넷 × 세 모양 (예측)

```kotlin
// grid55.kt
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.runBlocking

// 한 사슬을 세 모양(List · Sequence · Flow)으로 돌려 람다 호출 수와 로그 순서를 센다.
val log = mutableListOf<String>()
val calls = linkedMapOf<String, Int>()
fun hit(stage: String, x: Int) { log += "$stage$x"; calls[stage] = (calls[stage] ?: 0) + 1 }

fun mapF(x: Int): Int { hit("m", x); return x * 10 }
fun keepF(x: Int): Boolean { hit("f", x); return x > 15 }
fun peekF(x: Int) { hit("p", x) }

val input = (1..6).toList()

fun onList(chain: String): List<Int> = when (chain) {
    "map>filter>take2"     -> input.map(::mapF).filter(::keepF).take(2)
    "onEach>map>toList"    -> input.onEach(::peekF).map(::mapF)
    "filter>take2>map"     -> input.filter { keepF(it * 10) }.take(2).map(::mapF)
    "map>onEach>filter>first" -> listOf(input.map(::mapF).onEach(::peekF).filter(::keepF).first())
    else -> error(chain)
}

fun onSeq(chain: String): List<Int> = input.asSequence().let { s ->
    when (chain) {
        "map>filter>take2"     -> s.map(::mapF).filter(::keepF).take(2).toList()
        "onEach>map>toList"    -> s.onEach(::peekF).map(::mapF).toList()
        "filter>take2>map"     -> s.filter { keepF(it * 10) }.take(2).map(::mapF).toList()
        "map>onEach>filter>first" -> listOf(s.map(::mapF).onEach(::peekF).filter(::keepF).first())
        else -> error(chain)
    }
}

fun onFlow(chain: String): List<Int> = runBlocking {
    val f = input.asFlow()
    when (chain) {
        "map>filter>take2"     -> f.map { mapF(it) }.filter { keepF(it) }.take(2).toList()
        "onEach>map>toList"    -> f.onEach { peekF(it) }.map { mapF(it) }.toList()
        "filter>take2>map"     -> f.filter { keepF(it * 10) }.take(2).map { mapF(it) }.toList()
        "map>onEach>filter>first" -> listOf(f.map { mapF(it) }.onEach { peekF(it) }.filter { keepF(it) }.first())
        else -> error(chain)
    }
}

// 로그가 「단계별」(한 단계가 원소를 다 지난 뒤 다음 단계)인가 「원소별」인가
fun order(): String {
    val stages = log.map { it.take(1) }
    val runs = stages.zipWithNext().count { (a, b) -> a != b } + 1
    return if (runs == stages.distinct().size) "by-stage" else "by-element"
}

fun main() {
    val chains = listOf("map>filter>take2", "onEach>map>toList", "filter>take2>map", "map>onEach>filter>first")
    val shapes = listOf("List" to ::onList, "Sequence" to ::onSeq, "Flow" to ::onFlow)
    println("chain\tshape\tresult\tcalls\torder")
    val counts = mutableMapOf<Pair<String, String>, String>()
    val orders = mutableMapOf<Pair<String, String>, String>()
    for (c in chains) for ((name, run) in shapes) {
        log.clear(); calls.clear()
        val r = run(c)
        val cs = calls.entries.joinToString(" ") { "${it.key}=${it.value}" }
        val o = order()
        counts[c to name] = cs
        orders[c to name] = o
        val row = listOf(c, name, r.toString(), cs, o)
        check(row.size == 5)
        println(row.joinToString("\t"))
    }
    val m = chains.size
    val flowVsList = chains.count { counts[it to "Flow"] != counts[it to "List"] }
    val flowVsSeq = chains.count { counts[it to "Flow"] != counts[it to "Sequence"] }
    println("chains where Flow and List differ in calls: $flowVsList / $m")
    println("chains where Flow and Sequence differ in calls: $flowVsSeq / $m")
    val oList = chains.count { orders[it to "Flow"] != orders[it to "List"] }
    val oSeq = chains.count { orders[it to "Flow"] != orders[it to "Sequence"] }
    println("chains where Flow and List differ in order: $oList / $m")
    println("chains where Flow and Sequence differ in order: $oSeq / $m")
}
```

- 각 행의 `calls` 와 `order` 는 무엇인가? 마지막 네 줄의 `N / M` 은?

### 3. ★★ 앞 몇 개만 가져가면 상류에서는 (예측)

```kotlin
// take55.kt
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.runBlocking

val up = flow {
    try {
        for (i in 1..5) {
            println("  emit $i")
            emit(i)
        }
        println("  loop finished")
    } catch (e: Throwable) {
        println("  caught in upstream: ${e::class.java.name}")
        println("  message: ${e.message}")
        println("  is CancellationException: ${e is CancellationException}")
        throw e
    } finally {
        println("  upstream finally")
    }
}

fun main() = runBlocking {
    println("[a] take(2).toList()")
    println("  result ${up.take(2).toList()}")
    println("[b] first()")
    println("  result ${up.first()}")
    println("[c] toList()")
    println("  result ${up.toList()}")
}
```

- `[a]`·`[b]`·`[c]` 각각에서 상류 몸통의 어느 줄이 찍히나? 잡힌 것이 있다면 그 클래스는?

### 4. ★★ 두 몸통 안의 `delay` (예측)

```kotlin
// fdelay55.kt
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.runBlocking

val f = flow {
    emit(1)
    delay(10)
    emit(2)
}

fun main() = runBlocking {
    println(f.toList())
}
```

```kotlin
// sdelay55.kt
import kotlinx.coroutines.delay

val s = sequence {
    yield(1)
    delay(10)
    yield(2)
}

fun main() {
    println(s.toList())
}
```

- 두 파일을 각각 컴파일해 돌리면 무엇이 나오나?

### 5. ★★ 흐름 안에서 디스패처 바꾸기 (예측)

```kotlin
// ctx55.kt
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*

fun tn(): String = Thread.currentThread().name.substringBefore("-worker")
// 찍는 글자 안의 객체 해시(@16진수)는 실행마다 바뀐다 — 그 칸만 가려 찍는다.
fun hideHash(m: String): String = m.replace(Regex("@[0-9a-f]+"), "@<hash>")

fun main() = runBlocking {
    println("[a] withContext inside flow { }")
    val fa = flow {
        withContext(Dispatchers.IO) { emit(1) }
    }
    try {
        fa.collect { println("  got $it") }
    } catch (e: Throwable) {
        println(hideHash("${e::class.java.name}: ${e.message}"))
    }

    println("[b] flowOn(Dispatchers.IO)")
    flow { emit("emit on ${tn()}") }
        .map { "$it | map1 on ${tn()}" }
        .flowOn(Dispatchers.IO)
        .map { "$it | map2 on ${tn()}" }
        .collect { println("  $it | collect on ${tn()}") }
}
```

- `[a]` 와 `[b]` 에 각각 무엇이 찍히나? `[b]` 의 네 단계는 각각 어느 스레드에서 도나?

### 6. ★ 모으는 쪽이 없을 때 (예측)

```kotlin
// hot55.kt
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.runBlocking

fun main() = runBlocking {
    var runs = 0
    val cold = flow { runs++; emit(1) }
    println("cold: body runs with no collector = $runs")

    val state = MutableStateFlow(0)
    state.value = 1
    state.value = 2
    println("state: value with no collector = ${state.value}, subscribers = ${state.subscriptionCount.value}")
    println("state: a collector arriving now first sees ${state.first()}")

    val shared = MutableSharedFlow<Int>()
    println("shared: tryEmit with no collector returns ${shared.tryEmit(7)}")
    println("shared: replayCache after that = ${shared.replayCache}")

    cold.collect { }
    println("cold: body runs after one collect = $runs")
}
```

- 여섯 줄에 찍히는 값은 무엇인가?

### 7. `collect` 전에는 아무 일도 안 하는 이유 (왜)

- 라이브러리 KDoc 은 중간 연산에 대해 무엇이라고 적나? 1번에서 두 번째 `collect` 가 첫 번째 결과를 재사용하지 않는 것은 KDoc 의 어느 문장과 맞나?

### 8. `take` 가 「그만」을 알리는 방법 (왜)

- `Sequence` 의 `take` 는 반복자를 더 안 당기면 끝난다. `Flow` 의 `take` 가 그렇게 할 수 없는 이유는 무엇이고, 그래서 어떤 수단을 쓰나? 1번의 줄 순서와 어떻게 이어지나?

### 9. 상류가 `emit` 을 `try`/`catch` 로 감싸면 (경계)

- 상류가 `emit` 을 `try { … } catch (e: Throwable) { … }` 로 감싸고 다음 값을 계속 내보내게 한 뒤 `take(1)` 로 모으면, 모으는 쪽에는 무엇이 나오나? 그것이 왜 위험한가?

### 10. 두 결과를 정한 주체 (경계)

- 4번과 5번의 결과는 각각 **언제**(컴파일 / 실행) **누가**(컴파일러 / 라이브러리) 정한 것인가? 그 차이가 잘못을 발견하는 시점에 무엇을 바꾸나?

### 11. `Sequence`·Python 제너레이터·Java `Stream` 과 (연결)

- 호출 수와 순서에서 `Flow` 는 [47번 주제](../47-sequences-lazy-evaluation/)의 `Sequence` 와 무엇이 같은가? 두 번째로 모을 때 `Flow` 와 Python 제너레이터 객체·Java `Stream` 은 각각 어떻게 되나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
