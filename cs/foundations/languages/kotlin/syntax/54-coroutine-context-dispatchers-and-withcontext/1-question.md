# kotlin/syntax/54 — `CoroutineContext` 와 디스패처 · `withContext` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [52번 주제](../52-coroutine-basics-suspend-scope-launch-async/)(코루틴 기초 — `suspend` 호출 규칙 · `runBlocking` · `delay` 대 `Thread.sleep`)다.
> 문항 10개 중 예측형은 6개이고, 여섯 모두 코드블록이 붙는다.
> 이 주제의 모든 답은 **kotlinc 2.4.20 · Temurin JDK 21.0.5 · kotlinx-coroutines-core-jvm 1.11.0** 에서 실제로 던져 받은 것이다(이 머신은 코어 24개).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 디스패처 여덟 행 × 블로킹 N 개 (예측)

```kotlin
// grid54.kt
import kotlinx.coroutines.*
import java.util.concurrent.ConcurrentLinkedQueue
import kotlin.coroutines.CoroutineContext
import kotlin.coroutines.EmptyCoroutineContext

class Span54(val thread: String, val start: Long, val end: Long)

fun blockingCall54(spans: ConcurrentLinkedQueue<Span54>) {
    val t0 = System.nanoTime()
    Thread.sleep(200)
    spans += Span54(Thread.currentThread().name, t0, System.nanoTime())
}

// 가장 많이 겹친 순간에 몇 개가 동시에 돌고 있었나(끝과 시작이 같은 시각이면 끝을 먼저 센다)
fun maxAtOnce54(spans: Collection<Span54>): Int {
    val events = spans.flatMap { listOf(it.start to 1, it.end to -1) }
        .sortedWith(compareBy({ it.first }, { it.second }))
    var now = 0; var best = 0
    for ((_, d) in events) { now += d; best = maxOf(best, now) }
    return best
}

val cores54 = Runtime.getRuntime().availableProcessors()
val ioLimit54 = maxOf(64, cores54)

class Row54(val label: String, val nLabel: String, val n: Int, val run: suspend CoroutineScope.(Int, ConcurrentLinkedQueue<Span54>) -> Unit)

fun launchAll54(ctx: CoroutineContext): suspend CoroutineScope.(Int, ConcurrentLinkedQueue<Span54>) -> Unit = { n, spans ->
    coroutineScope { repeat(n) { launch(ctx) { blockingCall54(spans) } } }
}

@OptIn(ExperimentalCoroutinesApi::class, DelicateCoroutinesApi::class)
fun main() = runBlocking {
    val single = newSingleThreadContext("single54")
    val rows = listOf(
        Row54("runBlocking (no dispatcher)", "cores+1", cores54 + 1, launchAll54(EmptyCoroutineContext)),
        Row54("Dispatchers.Unconfined", "cores+1", cores54 + 1, launchAll54(Dispatchers.Unconfined)),
        Row54("newSingleThreadContext", "cores+1", cores54 + 1, launchAll54(single)),
        Row54("Default.limitedParallelism(1)", "cores+1", cores54 + 1, launchAll54(Dispatchers.Default.limitedParallelism(1))),
        Row54("Dispatchers.Default", "cores+1", cores54 + 1, launchAll54(Dispatchers.Default)),
        Row54("Default -> withContext(IO)", "cores+1", cores54 + 1) { n, spans ->
            coroutineScope { repeat(n) { launch(Dispatchers.Default) { withContext(Dispatchers.IO) { blockingCall54(spans) } } } }
        },
        Row54("Dispatchers.IO", "cores+1", cores54 + 1, launchAll54(Dispatchers.IO)),
        Row54("Dispatchers.IO", "ioLimit+1", ioLimit54 + 1, launchAll54(Dispatchers.IO)),
    )
    println(listOf("dispatcher", "N", "one thread", "all on main", "most at once", "queued").joinToString("\t"))
    var queued = 0
    for (r in rows) {
        val spans = ConcurrentLinkedQueue<Span54>()
        r.run(this, r.n, spans)
        check(spans.size == r.n)
        val names = spans.map { it.thread }.toSet()
        val most = maxAtOnce54(spans)
        val mostLabel = when (most) {
            r.n -> "all N"
            1 -> "1"
            cores54 -> "cores"
            ioLimit54 -> "ioLimit"
            else -> "other"
        }
        val q = most < r.n
        if (q) queued++
        val cells = listOf(r.label, r.nLabel, (names.size == 1).toString(), names.all { it == "main" }.toString(), mostLabel, q.toString())
        check(cells.size == 6)
        println(cells.joinToString("\t"))
    }
    single.close()
    println("rows where blocking calls queued: $queued / ${rows.size}")
}
```

- 각 행의 `one thread`·`all on main`·`most at once`·`queued` 는 무엇인가? 마지막 줄의 `N / M` 은? `kotlinc` 는 무엇을 찍나?

### 2. ★★★ `withContext` 의 안과 밖 (예측)

```kotlin
// within54.kt
import kotlinx.coroutines.*
import kotlin.coroutines.ContinuationInterceptor
import kotlin.coroutines.EmptyCoroutineContext

fun onMain54() = Thread.currentThread().name == "main"

fun main() = runBlocking(CoroutineName("outer54")) {
    val outerJob = coroutineContext[Job]!!

    val r = withContext(Dispatchers.IO) {
        val inner = coroutineContext[Job]!!
        println("1 inner Job === outer Job: ${inner === outerJob}")
        println("2 inner Job is a child of outer Job: ${outerJob.children.any { it === inner }}")
        println("3 CoroutineName inside: ${coroutineContext[CoroutineName]}")
        println("4 dispatcher inside: ${coroutineContext[ContinuationInterceptor]}")
        println("5 running on main: ${onMain54()}")
        42
    }
    println("6 value returned: $r · back on main: ${onMain54()}")

    for ((label, ctx) in listOf(
        "IO" to Dispatchers.IO,
        "CoroutineName only" to CoroutineName("renamed54"),
        "EmptyCoroutineContext" to EmptyCoroutineContext,
    )) {
        withContext(ctx) {
            println("7 withContext($label): Job class = ${coroutineContext[Job]!!::class.java.simpleName} · on main = ${onMain54()}")
        }
    }

    val caught = try {
        withContext(Dispatchers.IO) { error("thrown inside") }
    } catch (e: IllegalStateException) {
        e.message
    }
    println("8 caught at the withContext call: $caught · outer Job active: ${outerJob.isActive}")

    val started = CompletableDeferred<Unit>()
    val job = launch {
        try {
            withContext(Dispatchers.IO) {
                try {
                    started.complete(Unit)
                    delay(10_000)
                    println("9 after delay inside withContext")
                } finally {
                    println("10 finally inside withContext · on main = ${onMain54()}")
                }
            }
            println("11 line after withContext")
        } catch (e: CancellationException) {
            println("12 caller caught ${e::class.java.simpleName} · on main = ${onMain54()}")
        }
    }
    started.await()
    job.cancel()
    job.join()
    println("13 launched job isCancelled: ${job.isCancelled}")
}
```

- `1`\~`13` 중 찍히는 줄과 그 값은 무엇인가? `7` 의 세 줄에 나오는 클래스 이름은?

### 3. ★★ 문맥을 더하고 빼면 (예측)

```kotlin
// compose54.kt
import kotlinx.coroutines.*
import kotlin.coroutines.ContinuationInterceptor
import kotlin.coroutines.CoroutineContext

fun count54(ctx: CoroutineContext) = ctx.fold(0) { n, _ -> n + 1 }

fun main() {
    val ctx = Job() + Dispatchers.IO + CoroutineName("a54")
    println("1 elements: ${count54(ctx)}")
    println("2 [CoroutineName] = ${ctx[CoroutineName]}")
    println("3 [ContinuationInterceptor] = ${ctx[ContinuationInterceptor]}")
    println("4 [Job] present: ${ctx[Job] != null}")

    val renamed = ctx + CoroutineName("b54")
    println("5 after + CoroutineName(b54): elements ${count54(renamed)} · name ${renamed[CoroutineName]}")

    val twoDispatchers = (Dispatchers.Default as CoroutineContext) + Dispatchers.IO
    println("6 Default + IO: elements ${count54(twoDispatchers)} · ${twoDispatchers[ContinuationInterceptor]}")

    val removed = ctx.minusKey(CoroutineName)
    println("7 minusKey(CoroutineName): elements ${count54(removed)} · name ${removed[CoroutineName]}")

    runBlocking(CoroutineName("parent54")) {
        val parentJob = coroutineContext[Job]!!
        println("8 runBlocking dispatcher class: ${coroutineContext[ContinuationInterceptor]!!::class.java.simpleName}")
        val a = launch { println("9 child without name sees: ${coroutineContext[CoroutineName]}") }
        a.join()
        val b = launch(Dispatchers.IO + CoroutineName("child54")) {
            println("10 child with + sees: ${coroutineContext[CoroutineName]} · ${coroutineContext[ContinuationInterceptor]}")
        }
        b.join()
        val c = launch(Dispatchers.IO) { delay(50) }
        println("11 a running child is in parent.children: ${parentJob.children.any { it === c }}")
        c.join()
    }
}
```

- `1`\~`11` 의 원소 수와 값은 무엇인가? `8` 에 찍히는 클래스 이름은?

### 4. ★★ 중단 뒤 어느 스레드인가 (예측)

```kotlin
// unconf54.kt
import kotlinx.coroutines.*

// 스레드 이름의 숫자는 판마다 다를 수 있어 # 로 가린다
fun tn54() = Thread.currentThread().name.replace(Regex("[0-9]+"), "#")

fun main() = runBlocking {
    val u = launch(Dispatchers.Unconfined) {
        println("U1 before delay: ${tn54()}")
        delay(50)
        println("U2 after delay: ${tn54()}")
        withContext(Dispatchers.IO) { println("U3 inside withContext(IO): ${tn54()}") }
        println("U4 after withContext(IO): ${tn54()}")
    }
    println("M1 line after launch(Unconfined): ${tn54()}")
    u.join()
    val c = launch {
        println("C1 before delay: ${tn54()}")
        delay(50)
        println("C2 after delay: ${tn54()}")
        withContext(Dispatchers.IO) { println("C3 inside withContext(IO): ${tn54()}") }
        println("C4 after withContext(IO): ${tn54()}")
    }
    println("M2 line after launch: ${tn54()}")
    c.join()
}
```

- `U1`\~`U4`·`M1`·`M2`·`C1`\~`C4` 는 어떤 순서로, 어느 스레드 이름으로 찍히나?

### 5. ★★ 디스패처 둘을 더하면 (예측)

```kotlin
// dplus54.kt
import kotlinx.coroutines.*

val both54 = Dispatchers.Default + Dispatchers.IO
```

- 컴파일되나? 안 되면 진단은 무엇이고, 그 진단은 언어·라이브러리 중 어디서 오나?

### 6. ★ 블로킹 API 를 감싸는 형태 (예측)

```kotlin
// form54.kt
import kotlinx.coroutines.*

// 블로킹 API 를 감싸는 쪽이 디스패처를 고른다 — 부르는 쪽은 그냥 suspend 함수로 부른다
fun legacyRead54(key: String): String {
    Thread.sleep(20)
    return "value-of-$key"
}

suspend fun read54(key: String): String = withContext(Dispatchers.IO) { legacyRead54(key) }

fun main() = runBlocking(CoroutineName("form54")) {
    val values = listOf("a", "b", "c").map { k -> async { read54(k) } }.awaitAll()
    println(values)
    println(coroutineContext[CoroutineName])
    val r = withContext(Dispatchers.Default + CoroutineName("cpu54")) {
        (1..10).sum() to coroutineContext[CoroutineName]
    }
    println(r)
}
```

- 세 줄의 출력은 무엇인가?

### 7. `Default` 에서 블로킹 호출이 줄을 서는 이유 (왜)

- 1번의 `Dispatchers.Default` 행이 `all N` 이 아닌 이유는 무엇인가? KDoc 은 `Default` 의 스레드 수를 어떻게 적나? 같은 호출이 `delay` 였다면 무엇이 달라지나?

### 8. `withContext` 는 새 코루틴인가 (경계)

- 2번의 `1`·`2`·`7` 은 「같은 코루틴의 문맥만 바꾼다」는 설명과 어디서 맞고 어디서 어긋나나? KDoc 은 그것을 무엇이라 부르나?

### 9. 한 스레드만 쓰는 디스패처의 약속 (경계)

- 1번에서 `limitedParallelism(1)` 행의 `one thread` 가 `true` 였다 — 이것은 약속인가 관찰인가? 그 디스패처가 **보장하는 것**과 **보장하지 않는 것**은 무엇인가?

### 10. 블로킹을 누가 흡수하나 (연결)

- [Python 52번](../../../python/syntax/52-asyncio-concurrency-structure/)의 `asyncio.to_thread` 와 `withContext(Dispatchers.IO)` 는 어떻게 같은가? [Java 56번](../../../java/syntax/56-virtual-threads/)의 가상 스레드는 같은 문제를 어느 층에서 푸나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
