# kotlin/syntax/53 — 구조적 동시성 — `Job`·취소 전파·예외 전파·`supervisorScope` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [52번 주제](../52-coroutine-basics-suspend-scope-launch-async/)(코루틴 기초)다.
> 문항 10개 중 예측형은 5개이고, 5개 모두 코드블록이 붙는다.
> 이 주제의 모든 답은 **kotlinc 2.4.20 · Temurin JDK 21.0.5 · kotlinx-coroutines 1.11.0** 에서 실제로 던져 받은 것이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 구조 셋 × 사건 셋 × 빌더 둘 (예측)

```kotlin
// grid53.kt
import kotlinx.coroutines.*

const val STEPS = 4

class Cell {
    val state = linkedMapOf("A" to "-", "B" to "-", "C" to "-")
    val steps = mutableMapOf("A" to 0, "B" to 0, "C" to 0)
    var seen = "-"
    var handled = "-"
    var aStepsWhenSeen = -1
}

fun describe(e: Throwable): String =
    if (e is CancellationException) "CancellationException" else "${e::class.simpleName}(${e.message})"

suspend fun walker(name: String, cell: Cell) {
    try {
        repeat(STEPS) {
            yield()
            cell.steps[name] = cell.steps.getValue(name) + 1
        }
        cell.state[name] = "completed"
    } catch (e: CancellationException) {
        cell.state[name] = "cancelled"
        throw e
    }
}

suspend fun raiser(cell: Cell) {
    yield()
    cell.state["B"] = "raised"
    throw IllegalStateException("b")
}

fun CoroutineScope.children(cell: Cell, event: String, builder: String) {
    fun start(block: suspend () -> Unit): Job =
        if (builder == "launch") launch { block() } else async { block() }
    start { walker("A", cell) }
    val b = start { if (event == "one raises") raiser(cell) else walker("B", cell) }
    start { walker("C", cell) }
    if (event == "one child cancelled") launch { yield(); b.cancel() }
}

suspend fun structure(kind: String, cell: Cell, event: String, builder: String) {
    when (kind) {
        "coroutineScope" -> coroutineScope { children(cell, event, builder) }
        "supervisorScope" -> supervisorScope { children(cell, event, builder) }
        "launch(SupervisorJob())" -> coroutineScope { launch(SupervisorJob()) { children(cell, event, builder) } }
    }
}

fun runCell(kind: String, event: String, builder: String): Cell {
    val cell = Cell()
    val handler = CoroutineExceptionHandler { _, e -> cell.handled = describe(e) }
    runBlocking {
        val outer = launch(handler) {
            try {
                structure(kind, cell, event, builder)
                cell.seen = "returned normally"
            } catch (e: Throwable) {
                cell.seen = describe(e)
            }
            cell.aStepsWhenSeen = cell.steps.getValue("A")
        }
        if (event == "outer cancelled") {
            repeat(2) { yield() }
            outer.cancel()
        }
        repeat(3 * STEPS) { yield() }
        outer.join()
    }
    return cell
}

fun main() {
    val kinds = listOf("coroutineScope", "supervisorScope", "launch(SupervisorJob())")
    val events = listOf("one raises", "one child cancelled", "outer cancelled")
    val builders = listOf("launch", "async")
    val header = listOf("structure", "event", "builder", "A", "B", "C", "caller saw", "handler saw", "A steps then")
    println(header.joinToString("\t"))
    val table = mutableMapOf<Triple<String, String, String>, List<String>>()
    for (event in events) for (builder in builders) for (kind in kinds) {
        val c = runCell(kind, event, builder)
        val row = listOf(kind, event, builder, c.state.getValue("A"), c.state.getValue("B"), c.state.getValue("C"),
            c.seen, c.handled, "${c.aStepsWhenSeen}")
        check(row.size == header.size) { "cell count mismatch" }
        println(row.joinToString("\t"))
        table[Triple(kind, event, builder)] = row
    }
    fun differ(k1: String, k2: String): Pair<Int, Int> {
        var d = 0; var n = 0
        for (event in events) for (builder in builders) {
            val r1 = table.getValue(Triple(k1, event, builder))
            val r2 = table.getValue(Triple(k2, event, builder))
            for (i in listOf(3, 5, 6, 7)) { n++; if (r1[i] != r2[i]) d++ }
        }
        return d to n
    }
    val (d1, n1) = differ("coroutineScope", "supervisorScope")
    println("coroutineScope vs supervisorScope, cells that differ (A, C, caller, handler x 3 events x 2 builders): $d1 / $n1")
    val (d2, n2) = differ("supervisorScope", "launch(SupervisorJob())")
    println("supervisorScope vs launch(SupervisorJob()), cells that differ (same columns): $d2 / $n2")
}
```

- 컴파일은 조용한가? 열여덟 행의 A·B·C · `caller saw` · `handler saw` · `A steps then` 은? 마지막 두 줄의 `N / M` 은?

### 2. ★★★ 취소 뒤에 몇 걸음 (예측)

```kotlin
// swallow53.kt
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.yield

fun trial(label: String, step: suspend () -> Unit) = runBlocking {
    var stepsAfterCancel = 0
    var cancelled = false
    val job = launch {
        repeat(6) {
            step()
            if (cancelled) stepsAfterCancel++
        }
    }
    repeat(2) { yield() }
    job.cancel()
    cancelled = true
    job.join()
    println("$label\tsteps after cancel=$stepsAfterCancel\tjob.isCancelled=${job.isCancelled}")
}

fun main() {
    trial("yield()") { yield() }
    trial("runCatching { yield() }") { runCatching { yield() } }
    trial("try { yield() } catch (e: Exception) { }") { try { yield() } catch (e: Exception) { } }
    trial("runCatching { yield() }; ensureActive()") {
        runCatching { yield() }
        currentCoroutineContext().ensureActive()
    }
}
```

- 네 줄의 `steps after cancel` 과 `job.isCancelled` 는?

### 3. ★★ 다섯 가지 루프 (예측)

```kotlin
// coop53.kt
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.cancel
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.yield

fun trial(label: String, check: suspend CoroutineScope.() -> Boolean) = runBlocking {
    var done = 0
    var outcome = "-"
    val job = launch {
        try {
            while (done < 5) {
                done++
                if (done == 2) cancel()
                if (!check()) break
            }
            outcome = "loop ended"
        } catch (e: CancellationException) {
            outcome = "CancellationException"
        }
    }
    job.join()
    println("$label\tsteps=$done\t$outcome\tisCancelled=${job.isCancelled}")
}

fun main() {
    trial("no check") { true }
    trial("Thread.sleep(1)") { Thread.sleep(1); true }
    trial("isActive") { isActive }
    trial("yield()") { yield(); true }
    trial("ensureActive()") { ensureActive(); true }
}
```

- 다섯 줄의 `steps` · 끝난 모양 · `isCancelled` 는?

### 4. ★★ 정리 코드와 시간 제한 (예측)

```kotlin
// final53.kt
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.TimeoutCancellationException
import kotlinx.coroutines.awaitCancellation
import kotlinx.coroutines.cancelAndJoin
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeout
import kotlinx.coroutines.withTimeoutOrNull
import kotlinx.coroutines.yield

fun main() = runBlocking {
    val log = mutableListOf<String>()
    val a = launch {
        try {
            awaitCancellation()
        } finally {
            log += "a: finally entered"
            try {
                delay(1)
                log += "a: after delay"
            } catch (e: CancellationException) {
                log += "a: delay threw ${e::class.simpleName}"
            }
        }
    }
    val b = launch {
        try {
            awaitCancellation()
        } finally {
            withContext(NonCancellable) {
                delay(1)
                log += "b: after delay inside withContext(NonCancellable)"
            }
        }
    }
    yield()
    a.cancelAndJoin()
    b.cancelAndJoin()
    try {
        withTimeout(20) { delay(1000) }
    } catch (e: TimeoutCancellationException) {
        log += "withTimeout: ${e::class.simpleName}, is CancellationException=${e is CancellationException}, message=${e.message}"
    }
    log += "withTimeoutOrNull: ${withTimeoutOrNull(20) { delay(1000); "done" }}"
    log.forEach(::println)
}
```

- 컴파일러는 무엇이라도 말하나? 다섯 줄의 로그는 무엇인가?

### 5. ★ 셋 중 하나가 실패하는 적재 (예측)

```kotlin
// form53.kt
import kotlinx.coroutines.CoroutineExceptionHandler
import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.supervisorScope
import kotlinx.coroutines.withContext

suspend fun load(id: Int): String {
    delay(10L * id)
    check(id != 2) { "item $id failed" }
    return "item-$id"
}

suspend fun allOrNothing(ids: List<Int>): List<String> = coroutineScope {
    ids.map { async { load(it) } }.map { it.await() }
}

suspend fun bestEffort(ids: List<Int>): List<String> = supervisorScope {
    ids.map { async { load(it) } }.map { d ->
        try {
            d.await()
        } catch (e: IllegalStateException) {
            "failed(${e.message})"
        }
    }
}

fun main() = runBlocking {
    val ids = listOf(1, 2, 3)
    try {
        println("allOrNothing -> ${allOrNothing(ids)}")
    } catch (e: IllegalStateException) {
        println("allOrNothing -> ${e::class.simpleName}: ${e.message}")
    }
    println("bestEffort   -> ${bestEffort(ids)}")
    val handler = CoroutineExceptionHandler { _, e -> println("handler got ${e::class.simpleName}: ${e.message}") }
    withContext(handler) {
        supervisorScope {
            launch { load(2) }
            launch { println("sibling finished: ${load(3)}") }
        }
    }
    println("after the supervised block")
}
```

- 다섯 줄의 출력은 무엇인가?

### 6. `supervisorScope` 의 `async` 실패는 어디로 갔나 (왜)

- 1번의 `supervisorScope · one raises · async` 행에서 호출자도 핸들러도 예외를 못 봤다. 예외는 어디에 있고, 누가 꺼내야 하나?

### 7. `launch(SupervisorJob())` 의 두 가지 어긋남 (왜)

- 1번에서 이 구조가 `supervisorScope` 와 갈린 칸들을 **두 가지 성질**로 설명하면? 1.10.2 로 같은 격자를 돌리면 무엇이 같고 무엇이 다른가?

### 8. 취소는 실패인가 (경계)

- 1번의 `one child cancelled` 여섯 행에서 형제와 호출자는 어떻게 됐나? `coroutineScope` 가 이 사건을 「실패」로 치지 않는 것은 누구의 약속인가(언어인가 라이브러리인가)?

### 9. Python 52 의 격자와 한 쌍으로 (연결)

- [Python 52번](../../../python/syntax/52-asyncio-concurrency-structure/)의 `gather`·`TaskGroup` 과 Kotlin 의 `coroutineScope`·`supervisorScope` 를 짝지으면 어느 것이 어느 것과 가깝나? **기다리던 쪽이 받는 것**은 어디서 갈리나?

### 10. 운영 패턴과의 경계 (경계)

- [`ops-patterns/19`](../../../../../ops-patterns/19-graceful-shutdown/)(graceful shutdown)에 쓸 것과 이 주제에 쓸 것을 한 줄씩 가르면? 3번의 결과는 종료 처리에서 무엇을 뜻하나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
