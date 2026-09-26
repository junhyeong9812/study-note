# kotlin/syntax/53 — 구조적 동시성 — `Job`·취소 전파·예외 전파·`supervisorScope` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·경고는 **kotlinc 2.4.20 (JRE 21.0.5)** · Temurin **JDK 21.0.5** · **kotlinx-coroutines-core-jvm 1.11.0** 에서 실제로 얻었다.
> ★★ 아래 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적은 자리가 없다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 컴파일은 **경고 하나**(`launch(SupervisorJob())` deprecated) · **`coroutineScope` 대 `supervisorScope` 7 / 24**(전부 `one raises`) · **`supervisorScope` 대 `launch(SupervisorJob())` 11 / 24**

**출력**

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


```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar grid53.kt -d o53g =====
grid53.kt:48:55: warning: 'fun CoroutineScope.launch(context: Job, start: CoroutineStart = ..., block: suspend CoroutineScope.() -> Unit): Job' is deprecated. Passing a Job to coroutine builders breaks structured concurrency, leading to hard-to-diagnose errors. This pattern should be avoided. This overload will be deprecated with an error in the future.
        "launch(SupervisorJob())" -> coroutineScope { launch(SupervisorJob()) { children(cell, event, builder) } }
                                                      ^^^^^^
(exit 0)
```

```text
===== java -cp o53g:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Grid53Kt =====
structure	event	builder	A	B	C	caller saw	handler saw	A steps then
coroutineScope	one raises	launch	cancelled	raised	cancelled	IllegalStateException(b)	-	1
supervisorScope	one raises	launch	completed	raised	completed	returned normally	IllegalStateException(b)	4
launch(SupervisorJob())	one raises	launch	cancelled	raised	cancelled	returned normally	IllegalStateException(b)	0
coroutineScope	one raises	async	cancelled	raised	cancelled	IllegalStateException(b)	-	1
supervisorScope	one raises	async	completed	raised	completed	returned normally	-	4
launch(SupervisorJob())	one raises	async	cancelled	raised	cancelled	returned normally	IllegalStateException(b)	0
coroutineScope	one child cancelled	launch	completed	cancelled	completed	returned normally	-	4
supervisorScope	one child cancelled	launch	completed	cancelled	completed	returned normally	-	4
launch(SupervisorJob())	one child cancelled	launch	completed	cancelled	completed	returned normally	-	0
coroutineScope	one child cancelled	async	completed	cancelled	completed	returned normally	-	4
supervisorScope	one child cancelled	async	completed	cancelled	completed	returned normally	-	4
launch(SupervisorJob())	one child cancelled	async	completed	cancelled	completed	returned normally	-	0
coroutineScope	outer cancelled	launch	cancelled	cancelled	cancelled	CancellationException	-	0
supervisorScope	outer cancelled	launch	cancelled	cancelled	cancelled	CancellationException	-	0
launch(SupervisorJob())	outer cancelled	launch	completed	completed	completed	returned normally	-	0
coroutineScope	outer cancelled	async	cancelled	cancelled	cancelled	CancellationException	-	0
supervisorScope	outer cancelled	async	cancelled	cancelled	cancelled	CancellationException	-	0
launch(SupervisorJob())	outer cancelled	async	completed	completed	completed	returned normally	-	0
coroutineScope vs supervisorScope, cells that differ (A, C, caller, handler x 3 events x 2 builders): 7 / 24
supervisorScope vs launch(SupervisorJob()), cells that differ (same columns): 11 / 24
(exit 0)
```

**왜 그런가**

- ★★★ `coroutineScope` — B 가 던지면 **A·C 취소 · 호출자가 원래 예외**를 받는다(A 1걸음). `supervisorScope` — **A·C 끝까지 · 호출자 정상** · `launch` 실패는 **핸들러로**, `async` 실패는 **아무 데도**(6번).
- ★★ `one child cancelled` 는 여섯 행 모두 형제 `completed` · 호출자 정상(8번) · `outer cancelled` 는 두 scope 모두 **전부 취소**.
- ★★★ `launch(SupervisorJob())` 는 7번.

### 2. `yield()` **0** · `runCatching { yield() }` **5** · `try … catch (e: Exception)` **5** · `…; ensureActive()` **0** — `job.isCancelled` 는 **네 줄 모두 `true`**

**출력**

```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar swallow53.kt -d o53s =====
(exit 0)
===== java -cp o53s:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Swallow53Kt =====
yield()	steps after cancel=0	job.isCancelled=true
runCatching { yield() }	steps after cancel=5	job.isCancelled=true
try { yield() } catch (e: Exception) { }	steps after cancel=5	job.isCancelled=true
runCatching { yield() }; ensureActive()	steps after cancel=0	job.isCancelled=true
(exit 0)
```

**왜 그런가**

- ★★★ 취소된 코루틴의 `yield()` 는 `CancellationException` 을 던진다 — 그것을 `runCatching`·`catch (e: Exception)` 이 **삼키면** 루프가 모른다. [49번 주제](../49-result-and-runcatching/) (4) — JVM 의 `CancellationException` 은 `Exception` 이다.
- ★★ `isCancelled` 가 `true` 여도 **몸은 돈다** — 상태 표시와 실제 멈춤은 다른 것이다.
- ★★ `ensureActive()` 가 취소된 상태면 **다시 던져** 루프를 끊는다.

### 3. `no check` **5 · loop ended** · `Thread.sleep(1)` **5 · loop ended** · `isActive` **2 · loop ended** · `yield()` **2 · CancellationException** · `ensureActive()` **2 · CancellationException** — `isCancelled` 는 전부 `true`

**출력**

```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar coop53.kt -d o53c =====
(exit 0)
===== java -cp o53c:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Coop53Kt =====
no check	steps=5	loop ended	isCancelled=true
Thread.sleep(1)	steps=5	loop ended	isCancelled=true
isActive	steps=2	loop ended	isCancelled=true
yield()	steps=2	CancellationException	isCancelled=true
ensureActive()	steps=2	CancellationException	isCancelled=true
(exit 0)
```

**왜 그런가**

- ★★★ 취소는 **요청**이다 — `Job` 을 보는 자리를 안 지나면 끝까지 간다. `Thread.sleep` 은 `Job` 을 안 본다.
- ★★ `isActive` 는 **스스로 빠지는**(예외 없는) 길 · `yield()`·`ensureActive()` 는 **던져서** 빠지는 길이다.

### 4. **경고 하나**(「`check for instance is always 'true'.`」) · `a: finally entered` · **`a: delay threw JobCancellationException`** · `b: after delay inside withContext(NonCancellable)` · `withTimeout: TimeoutCancellationException, is CancellationException=true, message=Timed out waiting for 20 ms` · `withTimeoutOrNull: null`

**출력**

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


```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar final53.kt -d o53f =====
final53.kt:45:81: warning: check for instance is always 'true'.
        log += "withTimeout: ${e::class.simpleName}, is CancellationException=${e is CancellationException}, message=${e.message}"
                                                                                ^^^^^^^^^^^^^^^^^^^^^^^^^^
(exit 0)
===== java -cp o53f:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Final53Kt =====
a: finally entered
a: delay threw JobCancellationException
b: after delay inside withContext(NonCancellable)
withTimeout: TimeoutCancellationException, is CancellationException=true, message=Timed out waiting for 20 ms
withTimeoutOrNull: null
(exit 0)
```

**왜 그런가**

- ★★★ `finally` 에 들어와도 코루틴은 **여전히 취소된 상태**다 — `delay` 가 곧바로 던진다. `withContext(NonCancellable)` 안에서만 `suspend` 정리가 돈다.
- ★★ `TimeoutCancellationException` 은 `CancellationException` 의 자손이라 컴파일러가 `is` 검사를 **늘 참**이라 알려 준다 — 타입으로 정해진 사실이다.
- ★ `JobCancellationException` 은 라이브러리 내부 클래스 이름이다 — 이름은 판에 매이고, 근거로 쓰는 것은 「**던졌다**」는 사실이다.

### 5. `allOrNothing -> IllegalStateException: item 2 failed` · `bestEffort   -> [item-1, failed(item 2 failed), item-3]` · `handler got IllegalStateException: item 2 failed` · `sibling finished: item-3` · `after the supervised block`

**출력**

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


```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar form53.kt -d o53z =====
(exit 0)
===== java -cp o53z:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Form53Kt =====
allOrNothing -> IllegalStateException: item 2 failed
bestEffort   -> [item-1, failed(item 2 failed), item-3]
handler got IllegalStateException: item 2 failed
sibling finished: item-3
after the supervised block
(exit 0)
```

**왜 그런가**

- ★★ `allOrNothing` 은 `coroutineScope` — 2번이 실패하자 3번이 취소되고 **원래 예외**가 올라왔다.
- ★★ `bestEffort` 는 `supervisorScope` — 형제가 끝까지 가고, 실패는 **`await` 의 `try`** 에서 값으로 바뀌었다(`catch` 를 `IllegalStateException` 으로 좁혀 **취소는 삼키지 않는다**).
- ★★ 핸들러를 `withContext(handler)` 로 **감독 영역 바깥에** 두면 `launch` 자식의 실패를 받는다 — `supervisorScope` KDoc 이 권하는 꼴이다.

### 6. **`Deferred` 안에** 보관돼 있다 — **`await()` 를 부르는 쪽**이 꺼내야 한다 · `CoroutineExceptionHandler` 는 `async` 에 **안 불린다**

**왜 그런가**

```text
===== sed -n '14,24p' kxs/commonMain/Supervisor.kt =====
 * Creates a _supervisor_ job object in an active state.
 * Children of a supervisor job can fail independently of each other.
 *
 * A failure or cancellation of a child does not cause the supervisor job to fail and does not affect its other children,
 * so a supervisor can implement a custom policy for handling failures of its children:
 *
 * - A failure of a child job that was created using [launch][CoroutineScope.launch] can be handled via [CoroutineExceptionHandler] in the context.
 * - A failure of a child job that was created using [async][CoroutineScope.async] can be handled via [Deferred.await] on the resulting deferred value.
 *
 * If a [parent] job is specified, then this supervisor job becomes a child job of the [parent] and is cancelled when the
 * parent fails or is cancelled. All this supervisor's children are cancelled in this case, too.
(exit 0)
===== sed -n '179,188p' kxs/commonMain/Guidance.kt =====
@Deprecated(
    "Passing a Job to coroutine builders breaks structured concurrency, leading to hard-to-diagnose errors. " +
        "This pattern should be avoided. " +
        "This overload will be deprecated with an error in the future.",
    level = DeprecationLevel.WARNING)
public fun CoroutineScope.launch(
    context: Job,
    start: CoroutineStart = CoroutineStart.DEFAULT,
    block: suspend CoroutineScope.() -> Unit
): Job = launch(context as CoroutineContext, start, block)
(exit 0)
===== sed -n '270,281p' kxs/commonMain/CoroutineExceptionHandler.kt =====
 *
 * Similarly, this [CoroutineExceptionHandler] is redundant and will never be invoked:
 *
 * ```
 * GlobalScope.async(CoroutineExceptionHandler { ctx, e ->
 *     println("This line will not be printed!")
 * }) {
 *     error("Error")
 * }
 * ```
 *
 * The caller of [async] is responsible for handling the exceptions in the returned [Deferred] value.
(exit 0)
```

- ★★★ `SupervisorJob` KDoc — 「`A failure of a child job that was created using [async] can be handled via [Deferred.await]`」 · `CoroutineExceptionHandler` KDoc — 「`The caller of [async] is responsible for handling the exceptions in the returned [Deferred] value.`」
- ★★ 그래서 `supervisorScope` 안에서 `async` 를 띄우고 `await` 을 안 부르면 **실패가 조용히 사라진다**(1번 격자의 그 행).

### 7. ① **감독이 한 층 위에 걸린다** — 새 코루틴의 `Job` 은 보통 `Job` 이라 **A·B·C 는 서로 같이 죽는다** · ② **바깥 scope 의 자식이 아니게 된다** — 호출자가 **안 기다리고**(A 0걸음에 반환) **바깥 취소가 안 닿는다**(A·B·C `completed`) · 1.10.2 — **출력은 바이트까지 같고, 경고만 없다**

**왜 그런가**

```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.10.2.jar grid53.kt -d o53o =====
(exit 0)
===== java -cp o53g:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Grid53Kt > g53-new.txt =====
(exit 0)
===== java -cp o53o:kotlinx-coroutines-core-jvm-1.10.2.jar:kotlin-stdlib.jar Grid53Kt > g53-old.txt =====
(exit 0)
===== cmp g53-new.txt g53-old.txt && echo 'same bytes' =====
same bytes
(exit 0)
```

- ★★★ 11칸의 내역 — `one raises` 에서 A·C(`launch` 행 2 · `async` 행 2) + `async` 행의 핸들러 1 · `outer cancelled` 에서 A·C·호출자(두 행 × 3). `one child cancelled` 는 한 칸도 안 갈렸다.
- ★★ 경고 문구는 1.11.0 의 선언(`Guidance.kt` 의 `@Deprecated(level = WARNING)`)에서 온다 — **동작이 바뀐 것이 아니라 경고가 새로 붙은 것**이다.

### 8. 형제는 **전부 `completed`**, 호출자는 **정상 반환** · **라이브러리(kotlinx-coroutines)의 약속**이다

**왜 그런가**

- ★★ `coroutineScope` KDoc 이 형제를 취소하는 조건을 「`fails with an exception`」으로 적는다(2-summary (6)) — 취소는 그 「실패」에 들지 않는다.
- ★★ 언어는 `suspend` 변환만 준다([52번](../52-coroutine-basics-suspend-scope-launch-async/)) — 누가 누구를 취소하나는 **전부 라이브러리의 규칙**이다(흔들리는 칸 표의 「판에 매인다」).

### 9. **`coroutineScope` ≈ `TaskGroup`**(형제 취소 · 다 멈춘 뒤 올림) · **`supervisorScope` ≈ `gather` 는 형제 쪽만** — 기다리던 쪽은 `gather` 가 **예외를 곧바로** 받고, `supervisorScope` 는 **아무것도 안 받는다**

**왜 그런가**

- ★★★ 2-summary (3)의 표 — 봉투도 다르다: `TaskGroup` 은 `ExceptionGroup`, `coroutineScope` 는 **원래 예외 하나**.
- ★★ 「자식 하나가 취소」 칸에서 `gather` 만 기다리던 쪽에 `CancelledError` 를 던진다 — Kotlin 은 두 구조 모두 정상이다.

### 10. **ops-patterns/19** — 종료 신호 · 드레인 · 타임아웃 예산 · 순서 · **이 주제** — 취소가 `Job` 나무를 어떻게 타고 내려가나 · 3번은 **「종료 신호로 취소를 걸어도, 확인 자리가 없는 작업은 끝까지 돈다」** — 종료 시간 예산이 그 작업의 길이에 묶인다

**왜 그런가**

- ★★ graceful shutdown 의 「기다렸다가 끊는다」는 운영 설계라 [`ops-patterns/19`](../../../../../ops-patterns/19-graceful-shutdown/) 가 정본이다. 이 주제가 보탤 것은 **취소가 도달하는 조건**(확인 자리 · 삼키지 않기 · `NonCancellable` 정리)뿐이다.
- ★ 2번의 결과도 같은 뜻이다 — 취소를 삼키는 루프가 있으면 **종료가 그 루프만큼 늦어진다.**

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
===== unzip -p kotlinx-coroutines-core-jvm-1.11.0.jar META-INF/MANIFEST.MF | grep -E '^Implementation-(Title|Version)' =====
Implementation-Title: kotlinx-coroutines-core
Implementation-Version: 1.11.0
(exit 0)
===== javap -v -cp kotlinx-coroutines-core-jvm-1.11.0.jar kotlinx.coroutines.Job | grep -E '^ +mv=' =====
      mv=[2,2,0]
(exit 0)
===== javap -v -cp kotlinx-coroutines-core-jvm-1.10.2.jar kotlinx.coroutines.Job | grep -E '^ +mv=' =====
      mv=[2,1,0]
(exit 0)
```

```text
===== for i in 1 2 3 4 5; do java -cp o53g:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Grid53Kt | md5sum; java -cp o53s:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Swallow53Kt | md5sum; java -cp o53c:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Coop53Kt | md5sum; done | sort | uniq -c =====
      5 b43b51a7f5f2b7116b14833719762110  -
      5 c693a744911e858d9f9457ed70a28f12  -
      5 ffd3491a9af3ae75ecbb49f8d201e0fe  -
(exit 0)
```

★ **흔들리는 칸과 안 흔들리는 칸**

| 흔들린다 | 안 흔들린다 |
|---|---|
| **없다** — 시간은 칸으로 안 만들었다 · 단일 스레드 + `yield()` 걸음 | 전파 격자 18행 · 갈린 칸 수 · 걸음 수 — 다섯 판 되풀이에서 해시 하나 |
| ★ **판에 매인다** — 1.11.0 의 동작과 경고(1.10.2 는 경고가 없다) | 삼키기 쌍 · 협조적 취소 · `finally`·`withTimeout` 로그 · 소스 발췌 · 모든 **종료 코드** |

> 근거 — 캡처 스크립트를 처음부터 다시 돌려 **블록 전체를 대조**했다.
>
> 실측 — `capture.sh blocks` 와 `capture.sh blocks-recheck` 를 처음부터 따로 돌려 `normalize-shaky.py` 로 대조했다 —\
> **블록 74개 · 동일 74 · 흔들린 칸 0 · ★고칠 것 0**(50\~53 네 주제를 한 캡처로 받았다). 추가한 정규화 규칙은 **없다**.

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `grid53.kt` | ★★★ 구조 3 × 사건 3 × 빌더 2 · 갈린 칸 수 | `kotlinc`(경고 포함) → `java` + 다섯 판 되풀이 해시 |
| `grid53.kt`(1.10.2) | ★★ 라이브러리 판 대조 | 1.10.2 로 컴파일 → 두 출력을 `cmp` |
| `swallow53.kt` | ★★★ `runCatching`·`catch (e: Exception)` 이 취소를 삼키는 쌍 · `ensureActive` 복구 | `kotlinc` → `java` |
| `coop53.kt` | ★★ 협조적 취소 다섯 가지 | `kotlinc` → `java` |
| `final53.kt` | ★★ `finally` 안 `delay` · `NonCancellable` · `withTimeout` | `kotlinc`(경고 포함) → `java` |
| kotlinx-coroutines 소스 jar | `coroutineScope`·`supervisorScope`·`SupervisorJob`·`launch(Job)`·핸들러·`yield`·`NonCancellable` KDoc | `unzip` → `sed -n` |
| `form53.kt` | 형태 한 벌 | `kotlinc` → `java` |

**구현 의존 항목** — 걸음 수 · `JobCancellationException` 이라는 내부 이름 · 경고의 유무 — 라이브러리 판의 산출물이다.\
반면 **전파 규칙**(형제 취소 · 감독 · `async` 는 `await` · 취소는 실패가 아님 · `cancellable`) 은 **라이브러리 문서의 계약**이다 — 언어의 보장은 아니다.

**★ 던져 봤더니 예상과 달랐던 것 — 세 건**

1. ★★★ **`launch(SupervisorJob())` 는 「효과가 없는」 정도가 아니었다** — 형제 감독은 없고 **바깥 취소까지 끊겼다**(`outer cancelled` 에서 A·B·C `completed`).
2. ★★ **라이브러리 판을 바꾸니 동작은 같고 경고만 달랐다** — 1.11.0 이 그 꼴을 deprecated 로 선언했다.
3. ★★ **`supervisorScope` 안 `async` 의 실패는 핸들러에도 안 갔다** — `await` 을 안 부르면 흔적이 없다.
