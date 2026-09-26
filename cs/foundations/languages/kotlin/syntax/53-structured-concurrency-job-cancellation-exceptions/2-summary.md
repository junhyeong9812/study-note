# kotlin/syntax/53 — 구조적 동시성 — `Job`·취소 전파·예외 전파·`supervisorScope` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — **`kotlinx-coroutines-core-jvm` 1.11.0 의 소스 jar**(`CoroutineScope.kt`·`Supervisor.kt`·`Guidance.kt`·`CoroutineExceptionHandler.kt`·`Yield.kt`·`NonCancellable.kt`)의 KDoc((6)). ★ 공식 문서 페이지는 **이 작업에서 열지 못했다**(외부 네트워크를 쓰지 않았다) — [`../../언어-특성/README.md`](../../언어-특성/README.md) §6 이 [Coroutines basics](https://kotlinlang.org/docs/coroutines-basics.html)·[Cancellation](https://kotlinlang.org/docs/coroutines-cancellation.html) 을 원고째 인용한다.
> **실행 검증** — 이 문서의 모든 출력·경고는 **kotlinc 2.4.20 (JRE 21.0.5)** · Temurin **JDK 21.0.5** · **kotlinx-coroutines-core-jvm 1.11.0** 에서 실제로 얻었다.\
> `kotlinc` 6회(대조용 1.10.2 로 1회 포함) · `java` 6회 + 대조 2회 + 되풀이 15회 · 소스 jar 발췌 7곳.\
> ★★★ **라이브러리 판** — 이 주제의 규칙은 **전부 kotlinx-coroutines 의 문서 계약**이다(언어가 아니다). 판을 바꿔 본 대조 — 같은 격자를 **1.10.2**(gradle 배포본에 들어 있던 판 · 메타데이터 `mv=[2,1,0]`)로 컴파일·실행하니 **출력이 바이트까지 같았고, 경고만 달랐다**((1)).\
> ★★ 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적지 않았다. **「갈린 칸 N / M」은 프로그램이 스스로 센 것**이다.
> **경계** — ★★★ `suspend`·`launch`·`async`·`await` 의 기초와 「`async` 예외는 `await` 에서 나오지만 부모는 이미 취소됐다」는 [52번 주제](../52-coroutine-basics-suspend-scope-launch-async/)가 정본이다. **서버를 멈출 때 요청을 어떻게 흘려 보내나**(운영 패턴)는 [`cs/ops-patterns/19-graceful-shutdown/`](../../../../../ops-patterns/19-graceful-shutdown/) 가 정본이다 — 여기는 **`Job` 트리에서 취소·예외가 번지는 규칙**만 본다. `runCatching` 이 `CancellationException` 까지 잡는다는 것 자체는 [49번 주제](../49-result-and-runcatching/) (4)가 쟀다 — 여기서는 **그래서 무엇이 깨지나**를 본다.\
> ★ **대비** — 같은 축의 Python 격자(`gather` 대 `TaskGroup`)는 [Python 52번](../../../python/syntax/52-asyncio-concurrency-structure/), Go 의 `context` 취소 나무는 [Go 34번](../../../go/syntax/34-context-cancellation-deadlines-and-values/), JS 의 `AbortSignal` 은 [JS 41번](../../../js/syntax/41-cancellation-and-timeouts/)이 정본이다.
> 이 본문은 Claude 작성이다(원고 없음).

★★★ **본체는 첫째 창이다** — 「**전파 격자 — 구조 셋(`coroutineScope` · `supervisorScope` · `launch(SupervisorJob())`) × 사건 셋(자식 하나가 예외 · 자식 하나가 `cancel()` · 바깥이 취소) × 빌더 둘(`launch` · `async`) → 형제 A·C · 호출자가 본 것 · 핸들러가 본 것**」. 단일 스레드에서 `yield()` 걸음으로 **결정적으로** 만들었다(Python 52 의 `sleep(0)` 걸음과 같은 꾀).

## 이 주제가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **언어 보장** | 컴파일러가 하는 것 | ★ **거의 없다** — `suspend` 변환([52번](../52-coroutine-basics-suspend-scope-launch-async/))과 `CancellationException` 이 `java.util.concurrent.CancellationException` 의 별칭이라는 것뿐이다 |
| **라이브러리 계약(kotlinx-coroutines KDoc)** | 문서가 약속한 것 | ★★★ `coroutineScope` 「**any child coroutine in this scope fails … cancelling all the other children**」 · `supervisorScope` 「**will not affect the other children**」 · `SupervisorJob` 「`launch` 실패는 **`CoroutineExceptionHandler`**, `async` 실패는 **`await`**」 · `yield` 「**cancellable**」 · `NonCancellable` 「**designed for [withContext]**」 · `launch(Job)` **deprecated** |
| **이 판의 관찰** | 1.11.0 에서 이번에 본 것 | 격자 값 · 걸음 수 · 로그 · 경고 문구 |

## 이 판

```text
===== kotlinc -version =====
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
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

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| 안 흔들린다 | ★★★ 전파 격자 18행 × 9칸 · 갈린 칸 수 · 「A steps then」 걸음 수 | **단일 스레드 + `yield()` 걸음** — 시간을 안 쓴다. 다섯 판 되풀이에서 출력 해시가 하나였다((3) 끝) |
| 안 흔들린다 | 삼키기 쌍 · 협조적 취소 로그 | 같은 꾀(자기 자신에게 `cancel()` · `yield()` 걸음) |
| 안 흔들린다 | `withTimeout` 의 결과 클래스·메시지 | 20ms 로 끊는 1000ms `delay` — 폭이 50배라 결과는 늘 같다. ★ 걸린 시간은 **안 찍었다** |
| ★ **판에 매인다** | 라이브러리 **1.11.0** 의 동작 · **경고** | 1.10.2 에서는 출력이 같고 **`launch(SupervisorJob())` 경고가 없다**((1)) |

★ 근거 — 캡처 스크립트를 처음부터 두 번 돌려 **블록 전체를 대조**했다(수치는 3-answer 의 「실행 검증」).

## 한눈에 — 쉽게 말하면

**`coroutineScope` 는 「한 팀이 한 배를 탄 것」이다** — 한 명이 물에 빠지면(예외) **배를 돌려 모두 철수**하고(형제 취소), 선장(호출자)에게 **빠진 사연 그대로**(원래 예외) 보고한다. **`supervisorScope` 는 「각자 자기 보트」다** — 한 명이 빠져도 나머지는 **끝까지 노를 젓는다.** 빠진 사연은 선장이 아니라 **구조대(`CoroutineExceptionHandler`)** 에게 가고, `async` 보트라면 **누가 찾으러 갈 때(`await`)까지 아무도 모른다.**
★ **`launch(SupervisorJob())` 는 「보트를 사서 배 밖에 띄운 것」이다** — 자기 보트라 생각했지만 그 보트 **안의 사람들은 여전히 한 배**(보통 `Job`)라 한 명이 빠지면 같이 철수하고, 게다가 보트가 **본선의 줄에서 풀려**(구조적 동시성이 끊겨) 본선이 멈춰도(바깥 취소) 보트는 **계속 떠 간다.**
★ 그리고 **취소는 「그만하라는 쪽지」일 뿐**이다 — 쪽지를 읽는 자리(`yield`·`delay`·`isActive`)를 안 지나면 계속 일하고, 쪽지를 **구겨 버리면**(`runCatching` 으로 `CancellationException` 삼키기) 영영 모른다.

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 한 배 · 한 명이 빠지면 모두 철수 | `coroutineScope` — 형제 취소 · 원래 예외를 호출자에게 | (1) ★★★ |
| 각자 자기 보트 | `supervisorScope` — 형제 무사 · 예외는 핸들러로 | (1) ★★★ |
| 찾으러 가야 안다 | `supervisorScope` 안 `async` 실패 — **아무 데도 안 나온다**(`await` 전까지) | (1) ★★ |
| 배 밖에 띄운 보트 | `launch(SupervisorJob())` — 효과 없음 + 줄이 풀림 | (1) ★★★ · (2) |
| 쪽지를 구겨 버린다 | `runCatching { … }` 이 `CancellationException` 을 삼킨다 | (4) ★★★ |
| 쪽지를 읽는 자리 | `yield()` · `ensureActive()` · `isActive` | (5) ★★ |
| 철수 중에도 할 일 | `finally` + `withContext(NonCancellable)` | (6) |

```text
   자식 B 가 IllegalStateException 을 던지면 (빌더 launch)

   coroutineScope          supervisorScope           launch(SupervisorJob())
   ┌────────────┐          ┌────────────┐            coroutineScope ─ (끊김) ─ SupervisorJob
   │ A  B✗  C   │          │ A  B✗  C   │                                        └ 보통 Job
   └────────────┘          └────────────┘                                            A  B✗  C
   A·C cancelled           A·C completed             A·C cancelled
   호출자: ISE(b)            호출자: 정상 반환            호출자: 정상 반환 (A 가 0걸음일 때 — 안 기다렸다)
   핸들러: -                핸들러: ISE(b)              핸들러: ISE(b)
```

## 이 주제가 답하려는 질문

1. 자식 하나가 **실패하거나 취소되면** 형제 A·C 와 부모(호출자)는 어떻게 되나 — `coroutineScope` 와 `supervisorScope` 는 **몇 칸에서** 갈리나, 예외는 **어디로** 가나(호출자 `catch` · 핸들러 · 아무 데도).
2. `SupervisorJob()` 을 `launch` 인자로 넘기면 `supervisorScope` 와 **같은가.**
3. 취소는 **무엇이 있어야** 멈추나 — `runCatching` 으로 감싸면 · 바쁜 루프면 · `finally` 안에서 `delay` 하면.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **전파 격자(실행 · 단일 스레드 · `yield` 걸음)** | 형제 상태 · 호출자가 본 것 · 핸들러가 본 것 · 그때 A 의 걸음 수((1)) | ★ **본체 창** — 갈린 칸을 프로그램이 센다 |
| ★★ **컴파일 경고** | `launch(SupervisorJob())` 가 deprecated 인가((1)(2)) | ★ 라이브러리 판을 바꾸면 **경고만** 달라진다 |
| ★★ **판 대조(1.11.0 대 1.10.2)** | 같은 격자의 출력이 같은가((1)) | `cmp` |
| ★★ **걸음 계수 로그** | 취소 뒤에 몇 걸음 더 갔나((4)(5)) | 자기 자신에게 `cancel()` 을 걸어 결정적으로 |
| ★★ **소스 jar 발췌** | KDoc 계약((6)) | — |
| **인용 — 다시 안 잰다** | `runCatching`·`catch (e: Exception)` 이 `CancellationException` 을 잡는다 · `async` 예외는 `await` 에서 | [49번](../49-result-and-runcatching/) (4) · [52번](../52-coroutine-basics-suspend-scope-launch-async/) (4) |
| **부적용 — 운영 패턴** | 종료 신호 · 드레인 · 타임아웃 예산 | [`ops-patterns/19`](../../../../../ops-patterns/19-graceful-shutdown/) |
| **부적용 — 멀티스레드 경쟁** | 여러 스레드에서 누가 먼저 취소를 받나 | 이 문서는 **단일 스레드로만** 돌렸다 — [목록의 **54번 주제**](../54-coroutine-context-dispatchers-and-withcontext/)(디스패처) |

### (1) ★★★ 전파 격자 — 구조 3 × 사건 3 × 빌더 2

**언제 쓰나** — 요청 하나에서 여러 하위 작업을 띄울 때. 「하나가 실패하면 나머지를 멈출까, 끝까지 둘까」를 고르는 자리.

방법 — 칸마다 새 자식 A·B·C 를 띄운다. A·C 는 **`yield()` 네 걸음**을 걷고 끝나는 일꾼이고, B 는 사건에 따라 다르다(첫 걸음에서 `IllegalStateException("b")` · 한 걸음 뒤 누군가 `b.cancel()` · 일꾼인데 두 걸음 뒤 **바깥 코루틴**을 `cancel()`). 바깥 코루틴에는 `CoroutineExceptionHandler` 를 달고, 구조가 끝난 뒤에도 **열두 걸음을 더** 기다려 남은 자식이 끝까지 가나 본다.

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

- ★★★ **`coroutineScope` 대 `supervisorScope` — 갈린 칸 7 / 24, 일곱 칸 전부 `one raises` 에 있다**(`launch` 행 4칸 · `async` 행 3칸).
  `coroutineScope` 는 **A·C 를 `cancelled`**, 호출자가 **`IllegalStateException(b)`** 를 받는다(그때 A 는 **1걸음**). `supervisorScope` 는 **A·C 가 `completed`**, 호출자는 **정상 반환**(A 가 4걸음 — 다 기다렸다).
  `launch` 행의 넷째 칸은 **핸들러** — `supervisorScope` 의 `launch` 실패는 **핸들러가 받았고**(`IllegalStateException(b)`), `coroutineScope` 에서는 핸들러가 **안 불렸다**(예외가 호출자에게 갔으니까).
- ★★★ **`supervisorScope` 안의 `async` 실패는 아무 데도 안 나온다** — 호출자 `returned normally` · 핸들러 `-`. 예외는 `Deferred` 안에 들어 있고, **`await` 을 부르지 않았으니** 누구도 못 봤다. KDoc 대로다 — 「`async` 실패는 `await` 으로 다룬다」((6)).
- ★★ **`one child cancelled` — 여섯 칸 모두 형제 `completed` · 호출자 정상** — **취소는 실패가 아니다.** B 만 `cancelled` 이고 아무 데도 안 번진다.
- ★★ **`outer cancelled` — `coroutineScope`·`supervisorScope` 둘 다 A·B·C 전부 `cancelled`**, 호출자는 `CancellationException`. 부모의 취소는 **어느 구조든 아래로** 번진다(KDoc 「`whenever the caller gets cancelled, so does the new scope`」).
- ★★★ **`supervisorScope` 대 `launch(SupervisorJob())` — 갈린 칸 11 / 24.** 이름이 비슷한데 **거의 반이 다르다** — (2).

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

- ★★ **라이브러리 판을 바꿔도 격자는 바이트까지 같다**(1.10.2 · `same bytes`). 달라진 것은 **컴파일 경고 하나** — 1.11.0 은 `launch(SupervisorJob())` 에 「`Passing a Job to coroutine builders breaks structured concurrency, leading to hard-to-diagnose errors.`」를 내고, **1.10.2 는 아무 말이 없다**(`(exit 0)` 뿐인 블록).

### (2) ★★★ `SupervisorJob()` 을 `launch` 인자로 — 흔한 오해

격자의 셋째 구조만 떼어 읽는다.

- ★★★ **`one raises` 에서 A·C 가 `cancelled`** — `supervisorScope` 라면 살았을 형제가 죽었다. `launch(SupervisorJob()) { … }` 로 만든 코루틴의 **자기 `Job` 은 보통 `Job`** 이고 A·B·C 는 **그 보통 `Job` 의 자식**이다. `SupervisorJob` 은 **그 코루틴의 부모**가 됐을 뿐 — 감독하는 대상이 **그 코루틴 하나**다.
- ★★★ **호출자가 `returned normally` 를 A 가 0걸음일 때 받았다** — `coroutineScope` 가 **기다리지 않았다.** 그 코루틴의 부모가 `SupervisorJob` 으로 바뀌어 **바깥 scope 의 자식이 아니게** 됐기 때문이다.
- ★★★ **`outer cancelled` 에서 A·B·C 가 `completed`** — 바깥을 취소했는데 **안이 끝까지 돌았다.** 줄이 풀린 보트다. 이것이 경고가 말하는 「**breaks structured concurrency**」의 실체다.
- ★★ 실패는 **핸들러로** 갔다(`handler saw IllegalStateException(b)`) — 부모 `SupervisorJob` 이 실패를 안 받으니, 그 코루틴이 **뿌리처럼** 제 핸들러를 부른 것이다.
- ★ 처방 — 형제를 서로 지키려면 **`supervisorScope { }`** 를 쓴다. `SupervisorJob()` 은 **직접 만드는 `CoroutineScope(SupervisorJob() + …)`** 의 뿌리 자리에 둔다.

### (3) ★★ Python 52 의 `gather` 대 `TaskGroup` 과 한 쌍으로

같은 축(자식 하나가 예외 · 자식 하나가 취소 · 바깥이 취소)을 [Python 52번](../../../python/syntax/52-asyncio-concurrency-structure/)이 `gather`·`TaskGroup` 으로 쟀다(그쪽 「갈린 칸 4 / 9」). 두 격자의 출력을 **사건별로 나란히** 옮기면 이렇다(Kotlin 은 빌더 `launch` 행).

| 사건 | Python `gather`(기본) | Python `TaskGroup` | Kotlin `coroutineScope` | Kotlin `supervisorScope` |
|---|---|---|---|---|
| 자식 하나가 예외 — 형제 | **finished** | cancelled | cancelled | **completed** |
| 〃 — 기다리던 쪽이 받은 것 | `ValueError` 를 **곧바로**(A 3걸음) | `ExceptionGroup[ValueError]`(A 2걸음) | `IllegalStateException` **그대로**(A 1걸음) | **정상 반환** — 예외는 핸들러로 |
| 자식 하나가 취소 — 형제 | finished | finished | completed | completed |
| 〃 — 기다리던 쪽 | **`CancelledError` 를 받는다** | 정상 | 정상 | 정상 |
| 바깥이 취소 | 전부 cancelled | 전부 cancelled | 전부 cancelled | 전부 cancelled |

- ★★★ **`coroutineScope` 는 `TaskGroup` 쪽이다** — 형제를 취소하고 **다 멈춘 뒤** 올린다. 다른 점은 **봉투가 없다**는 것 — Kotlin 은 `ExceptionGroup` 이 아니라 **원래 예외 하나**를 다시 던진다.
- ★★★ **`supervisorScope` 는 `gather` 와 형제 쪽만 같다** — 둘 다 형제를 끝까지 둔다. 그러나 `gather` 는 **기다리던 쪽에 예외를 곧바로** 넘기고, `supervisorScope` 는 **기다리던 쪽에 아무것도 안 넘긴다**(`launch` 는 핸들러로, `async` 는 `await` 할 때까지 보관).
- ★★ **자식 하나가 취소된 칸** — `gather` 만 기다리던 쪽에 `CancelledError` 를 던진다(Python 52 가 「함정」이라 부른 칸). Kotlin 은 두 구조 모두 **정상**이다 — 취소는 실패로 안 친다.
- ★ 이 표는 **두 문서의 출력을 옮긴 것**이다 — 걸음 수는 두 격자의 걸음 정의(Python 은 `sleep(0)` 4걸음 · Kotlin 은 `yield()` 4걸음)가 같은 꼴이지만 **스케줄러가 달라** 수를 맞대어 비교하지 않는다.

```text
===== for i in 1 2 3 4 5; do java -cp o53g:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Grid53Kt | md5sum; java -cp o53s:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Swallow53Kt | md5sum; java -cp o53c:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Coop53Kt | md5sum; done | sort | uniq -c =====
      5 b43b51a7f5f2b7116b14833719762110  -
      5 c693a744911e858d9f9457ed70a28f12  -
      5 ffd3491a9af3ae75ecbb49f8d201e0fe  -
(exit 0)
```

- ★ 전파 격자 · (4) · (5)의 프로그램을 다섯 판씩 돌린 **출력 해시가 셋, 각 5번** — 한 판도 안 흔들렸다.

### (4) ★★★ `runCatching` 이 취소를 삼키면 — 한 쌍

**언제 쓰나** — 코루틴 안의 반복 작업에서 「실패해도 다음 것을 계속」 하려고 `runCatching` 으로 감쌀 때.

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

- ★★★ **`runCatching { yield() }` 은 취소된 뒤에도 다섯 걸음을 더 갔다** — `yield()` 가 던진 `CancellationException` 을 `runCatching` 이 **실패 값으로 담아 버려** 루프가 모른다. `job.isCancelled` 는 `true` 인데 **몸은 계속 돈다.** `yield()` 만 쓴 줄은 **0걸음**이다.
- ★★★ **`try { } catch (e: Exception) { }` 도 똑같이 다섯 걸음** — [49번 주제](../49-result-and-runcatching/) (4)에서 본 대로 JVM 의 `CancellationException` 은 `Exception` 이다. **`runCatching` 만의 문제가 아니다.**
- ★★★ **복구 — `runCatching` 뒤에 `ensureActive()`** — 0걸음으로 돌아온다. 취소된 상태면 `ensureActive()` 가 `CancellationException` 을 **다시** 던진다. (또는 `catch` 에서 `CancellationException` 을 **다시 던진다.**)
- ★★ `job.join()` 이 돌아온 시점이 곧 「루프가 끝난 시점」이다 — 삼킨 쪽은 취소를 요청한 뒤에도 **다섯 걸음을 다 기다려야** `join` 이 풀렸다.

### (5) ★★ 협조적 취소 — 바쁜 루프는 멈추지 않는다

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

- ★★★ **확인하는 자리가 없는 루프는 취소돼도 끝까지 돈다**(`no check` · 5걸음 · `loop ended`). `Thread.sleep(1)` 도 **확인하는 자리가 아니다** — 스레드를 재울 뿐 `Job` 을 안 본다(5걸음).
- ★★ **멈추는 법 셋** — `isActive` 를 보고 **스스로 빠진다**(2걸음 · `loop ended` — 예외 없이) · `yield()`·`ensureActive()` 는 **`CancellationException` 을 던져** 빠진다(2걸음).
- ★ 결정적으로 만들려고 **둘째 걸음에서 자기 자신에게 `cancel()`** 을 걸었다 — 다른 스레드에서 거는 취소도 **요청일 뿐**이라는 점은 같다(KDoc 「`cancellable`」 — (6)).

### (6) ★★ `finally` · `NonCancellable` · `withTimeout`

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

- ★★★ **취소된 코루틴의 `finally` 안에서 `delay` 는 곧바로 던진다** — `a: delay threw JobCancellationException` · `a: after delay` 는 **안 찍혔다.** `finally` 에 들어왔다고 취소가 풀리지 않는다.
- ★★★ **`withContext(NonCancellable) { }` 안에서는 된다** — `b: after delay inside withContext(NonCancellable)`. 정리 코드(연결 닫기·로그 쓰기)가 `suspend` 를 불러야 하면 이렇게 감싼다.
- ★★ **`withTimeout` 은 `TimeoutCancellationException`** 을 던진다 — **`CancellationException` 의 자손**이고(컴파일러가 「`check for instance is always 'true'.`」 경고를 낼 만큼 타입이 그렇게 정해져 있다), 메시지는 `Timed out waiting for 20 ms`. **`withTimeoutOrNull`** 은 `null` 을 돌려준다.
- ★ 그래서 `withTimeout` 을 `runCatching` 으로 감싸면 (4)와 같은 자리에서 **시간 초과와 진짜 취소가 한데 섞인다** — 「시간 초과만」 다루려면 `withTimeoutOrNull` 이나 `catch (e: TimeoutCancellationException)` 으로 좁힌다.

```text
===== unzip -o -q kotlin-stdlib-sources.jar 'commonMain/kotlin/time/*' 'jvmMain/kotlin/time/*' 'jvmMain/jdk8/kotlin/time/*' commonMain/kotlin/util/Preconditions.kt commonMain/kotlin/util/Standard.kt jvmMain/kotlin/util/AssertionsJVM.kt commonMain/kotlin/contracts/ContractBuilder.kt commonMain/kotlin/coroutines/intrinsics/Intrinsics.kt jvmMain/kotlin/coroutines/cancellation/CancellationException.kt =====
(exit 0)
===== unzip -o -q kotlinx-coroutines-core-jvm-1.11.0-sources.jar commonMain/CoroutineScope.kt commonMain/Supervisor.kt commonMain/Guidance.kt commonMain/CoroutineExceptionHandler.kt commonMain/Yield.kt commonMain/NonCancellable.kt -d kxs =====
(exit 0)
```

```text
===== sed -n '741,759p' kxs/commonMain/CoroutineScope.kt =====
/**
 * Runs the given [block] in-place in a new [CoroutineScope] based on the caller coroutine context,
 * returning its result.
 *
 * The lifecycle of the new [Job] begins with starting the [block] and completes when both the [block] and
 * all the coroutines launched in the scope complete.
 * Only then can the [coroutineScope] call return a value.
 *
 * The context of the new scope is obtained by combining the [currentCoroutineContext] with a new [Job]
 * whose parent is the [Job] of the caller [currentCoroutineContext] (if any).
 * This parent-child relationship ensures that whenever the caller gets cancelled, so does the new scope.
 *
 * The [Job] of the new scope is not a normal child of the caller coroutine but a **lexically scoped** one,
 * meaning that the failure of the [Job] will not affect the parent [Job].
 * Instead, the exception leading to the failure will be rethrown to the caller of this function.
 *
 * If [block] or any child coroutine in this scope fails with an exception,
 * the scope fails, cancelling all the other children and its own [block].
 * See [supervisorScope] for a similar function that allows child coroutines to fail independently.
(exit 0)
===== sed -n '36,51p' kxs/commonMain/Supervisor.kt =====
 * Runs the given [block] in-place in a new [CoroutineScope] that contains a [SupervisorJob]
 * and is based on the caller coroutine context. The result of [block] is returned.
 *
 * The lifecycle of the new [SupervisorJob] begins with starting the [block] and completes when both the [block] and
 * all the coroutines launched in the scope complete.
 *
 * The context of the new scope is obtained by combining the [currentCoroutineContext] with a new [SupervisorJob]
 * whose parent is the [Job] of the caller [currentCoroutineContext] (if any).
 * This parent-child relationship ensures that whenever the caller gets cancelled, so does the new scope.
 *
 * The [SupervisorJob] of the new scope is not a normal child of the caller coroutine but a **lexically scoped** one,
 * meaning that the failure of the [SupervisorJob] will not affect the parent [Job].
 * Instead, the exception leading to the failure will be rethrown to the caller of this function.
 *
 * If a child coroutine launched in the new scope fails, it will not affect the other children of the scope.
 * However, if the [block] finishes with an exception, it will cancel the scope and all its children.
(exit 0)
```

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

```text
===== sed -n '44,45p' kxs/commonMain/Yield.kt =====
 * This suspending function is cancellable: if the [Job] of the current coroutine is cancelled while
 * [yield] is invoked or while waiting for dispatch, it immediately resumes with [CancellationException].
(exit 0)
===== sed -n '9,21p' kxs/commonMain/NonCancellable.kt =====
 * A non-cancelable job that is always [active][Job.isActive]. It is designed for [withContext] function
 * to prevent cancellation of code blocks that need to be executed without cancellation.
 *
 * Use it like this:
 * ```
 * withContext(NonCancellable) {
 *     // this code will not be cancelled
 * }
 * ```
 *
 * **WARNING**: This object is not designed to be used with [launch], [async], and other coroutine builders.
 * if you write `launch(NonCancellable) { ... }` then not only the newly launched job will not be cancelled
 * when the parent is cancelled, the whole parent-child relation between parent and child is severed.
(exit 0)
```

- ★★★ **`coroutineScope` KDoc** — 「`If [block] or any child coroutine in this scope fails with an exception, the scope fails, cancelling all the other children and its own [block].`」 · 「`the exception leading to the failure will be rethrown to the caller of this function.`」 — (1)의 `coroutineScope` 행 그대로다.
- ★★★ **`supervisorScope` KDoc** — 「`If a child coroutine launched in the new scope fails, it will not affect the other children of the scope.`」 · 단 「`if the [block] finishes with an exception, it will cancel the scope and all its children.`」 — **블록 자체**가 던지면 감독도 소용없다.
- ★★★ **`SupervisorJob` KDoc** — 「`launch` 실패는 `CoroutineExceptionHandler` 로, `async` 실패는 `Deferred.await` 로」 — (1)의 핸들러 칸과 `async` 칸이 이 두 줄이다.
- ★★ **`launch(context: Job)` 는 `@Deprecated(level = WARNING)`**(`Guidance.kt`) — 1.11.0 의 선언이다((1)의 경고).
- ★★ **`CoroutineExceptionHandler` KDoc** — `async` 에 단 핸들러는 「`redundant and will never be invoked`」 · 「`The caller of [async] is responsible for handling the exceptions in the returned [Deferred] value.`」
- ★★ **`yield` KDoc** — 「`This suspending function is cancellable`」 · **`NonCancellable`** — 「`designed for [withContext]`」, `launch(NonCancellable)` 은 「`the whole parent-child relation between parent and child is severed`」 — (2)와 같은 부류의 경고다.

## 문법 — 형태와 규칙

**형태** — 전부 성공해야 하는 일은 `coroutineScope`, 되는 만큼 받는 일은 `supervisorScope` + `await` 의 `try`, 핸들러는 `withContext` 로 **바깥에** 둔다(KDoc 이 권하는 꼴).

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

**규칙 불릿**

- **하나라도 실패하면 전부 멈춘다** → `coroutineScope { }` — 형제 취소 · 원래 예외를 호출자에게((1)).
- **서로 독립** → `supervisorScope { }` — `launch` 자식의 실패는 **컨텍스트의 `CoroutineExceptionHandler`**, `async` 자식은 **`await` 에서** 다룬다((1)(6)).
- **`launch(SupervisorJob())` · `launch(NonCancellable)` 은 쓰지 않는다** — 부모 관계가 끊긴다((2)(6)).
- **취소는 실패가 아니다** — 형제에게 안 번진다((1)).
- **`CancellationException` 을 삼키지 마라** — `runCatching`·`catch (e: Exception)` 뒤에는 `ensureActive()` 또는 다시 던지기((4)).
- **오래 도는 계산에는 확인 자리를** — `isActive` · `ensureActive()` · `yield()`((5)).
- **정리 코드의 `suspend` 는 `withContext(NonCancellable)`** 안에서((6)).
- **시간 제한** — `withTimeout`(→ `TimeoutCancellationException`) · `withTimeoutOrNull`(→ `null`)((6)).

## 어디서 틀리나

1. ★★★ **`supervisorScope` 면 예외가 호출자에게 온다고 본다.** 안 온다 — `launch` 는 핸들러로, `async` 는 `await` 할 때까지 **아무 데도**((1)).
2. ★★★ **`launch(SupervisorJob())` 가 자식들을 감독한다고 본다.** 형제는 여전히 같이 죽고, 바깥 취소도 안 닿는다 — 11 / 24 칸이 `supervisorScope` 와 달랐다((2)).
3. ★★★ **코루틴 안에서 `runCatching` 으로 감싸 「안전하게」 만든다.** 취소를 삼켜 **취소된 코루틴이 계속 돈다**((4)).
4. ★★ **취소하면 곧바로 멈춘다고 본다.** 확인 자리를 안 지나면 끝까지 돈다 — `Thread.sleep` 도 확인 자리가 아니다((5)).
5. ★★ **`finally` 안의 `delay`·네트워크 호출이 돈다고 본다.** 취소된 코루틴에서는 곧바로 던진다 — `NonCancellable` 로 감싸라((6)).
6. ★★ **자식 하나를 `cancel()` 하면 형제도 멈춘다고 본다.** 취소는 실패가 아니다 — 형제는 끝까지 간다((1)).
7. ★ **`async` 에 `CoroutineExceptionHandler` 를 단다.** 안 불린다((6)).

## 구현 세부사항 대 언어 보장

| 항목 | 어느 쪽인가 | 근거 |
|---|---|---|
| `coroutineScope` 가 형제를 취소하고 원래 예외를 다시 던진다 | ★★★ **라이브러리 계약(KDoc)** — 언어가 아니다 | (1)(6) |
| `supervisorScope` 가 형제를 지킨다 · `launch` 실패는 핸들러 · `async` 는 `await` | ★★★ **라이브러리 계약(KDoc)** | (1)(6) |
| `launch(Job)` 이 구조를 끊는다 | ★★ **라이브러리 계약(KDoc · 1.11.0 은 deprecated 선언)** — 동작은 1.10.2 와 같았다 | (1)(2) |
| `yield`·`delay` 가 취소에 응한다 · 바쁜 루프는 안 응한다 | ★★ **라이브러리 계약(KDoc 「`cancellable`」)** — 「협조적 취소」는 **설계**다 | (5)(6) |
| `CancellationException` 이 `Exception` 이다 | ★ **플랫폼(JVM) 사실** — stdlib 의 타입 별칭 | [52번](../52-coroutine-basics-suspend-scope-launch-async/) (5) |
| 걸음 수(`A steps then` 1 · 4 · 0) · 핸들러가 불린 시점 | ★ **이 판의 관찰**(단일 스레드 스케줄) | (1) |
| 「취소가 빠르다」·「구조적 동시성의 비용」 | **재지 않았다** | — |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 여러 조각을 모아 **한 결과**를 만든다 | `coroutineScope` + `async`/`await` | (1) · 형태 `allOrNothing` |
| 조각마다 **따로** 성공·실패를 받는다 | `supervisorScope` + `async` + `await` 의 `try` | (1) · 형태 `bestEffort` |
| 불붙이고 잊는 자식들, 실패는 로그로 | `withContext(handler) { supervisorScope { launch … } }` | (6) KDoc 의 꼴 |
| 앱 수명의 뿌리 scope | `CoroutineScope(SupervisorJob() + …)` — **빌더 인자가 아니라 뿌리에** | (2) |
| 루프 안에서 실패를 삼키고 계속 | `try { } catch (e: 특정예외)` — `CancellationException` 은 **다시 던진다** | (4) |
| 정리 코드에서 `suspend` 호출 | `withContext(NonCancellable)` | (6) |
| 서버 종료 시 진행 중 요청을 흘려 보내기 | 운영 패턴 | [`ops-patterns/19`](../../../../../ops-patterns/19-graceful-shutdown/) |

## 핵심 문장

1. **`coroutineScope` 는 한 자식의 실패로 형제를 취소하고 원래 예외를 호출자에게 다시 던진다** — `supervisorScope` 와 **24칸 중 7칸**이 갈렸다.
2. **`supervisorScope` 의 실패는 호출자에게 안 온다** — `launch` 는 핸들러로, `async` 는 `await` 전까지 **아무 데도.**
3. **`launch(SupervisorJob())` 는 `supervisorScope` 가 아니다** — 형제는 같이 죽고 바깥 취소는 안 닿는다(24칸 중 11칸이 달랐다 · 1.11.0 은 경고한다).
4. **취소는 실패가 아니고, 요청일 뿐이다** — 확인 자리(`yield`·`ensureActive`·`isActive`)를 지나야 멈춘다.
5. **`runCatching`·`catch (e: Exception)` 은 취소를 삼킨다** — 취소된 코루틴이 계속 돈다. `ensureActive()` 로 되살린다.

## 관련 자료

- [52번 주제](../52-coroutine-basics-suspend-scope-launch-async/) — ★★★ **선행.** `suspend`·`launch`·`async`·`await` · 「`await` 에서 잡았는데 부모는 이미 취소됐다」.
- [49번 주제](../49-result-and-runcatching/) — `runCatching` 이 `CancellationException` 까지 잡는다(5 중 5). 여기의 (4)가 **그래서 무엇이 깨지나**다.
- [`cs/ops-patterns/19-graceful-shutdown/`](../../../../../ops-patterns/19-graceful-shutdown/) — 운영 패턴. 그쪽은 **종료 신호를 받은 서버가 무엇을 하나**, 여기는 **그때 `Job` 트리에서 취소가 어떻게 번지나**.
- [`../../언어-특성/README.md`](../../언어-특성/README.md) §6 — 「구조적 동시성 — 이 모델의 진짜 값」 · 「취소는 보장이 아니라 규약이다」. 논지는 거기다.
- [Python 52번](../../../python/syntax/52-asyncio-concurrency-structure/) — ★ **한 쌍.** `gather` 대 `TaskGroup` 격자((3)의 표).
- [Go 34번](../../../go/syntax/34-context-cancellation-deadlines-and-values/) — `context` 의 취소 나무. Go 는 **`Done()` 을 읽어야** 멈춘다 — (5)와 같은 「협조적」 성질.
- [JS 41번](../../../js/syntax/41-cancellation-and-timeouts/) — `AbortSignal` — 「읽는 쪽이 멈춘다」.

## 용어 풀이

> **구조적 동시성(structured concurrency)** — 코루틴을 **부모-자식 나무**로 묶어, 부모가 자식을 기다리고 부모가 취소되면 자식도 취소되게 하는 방식.\
> 예: `coroutineScope { launch { … } }` 는 안의 `launch` 가 끝나야 돌아온다.

> **`Job`** — 코루틴 하나의 수명 손잡이. 부모 `Job` 과 자식 `Job` 이 나무를 이룬다.

> **`SupervisorJob`** — 자식의 실패가 **자기와 다른 자식에게** 번지지 않는 `Job`.

> **`CoroutineExceptionHandler`** — 뿌리 코루틴(또는 감독 아래의 `launch`)에서 **잡히지 않은 예외**를 받는 컨텍스트 요소. `async` 에는 안 불린다.

> **협조적 취소(cooperative cancellation)** — 취소가 **강제로 멈추는 것이 아니라** 「그만하라」는 표시이고, 코드가 확인 자리에서 스스로 멈추는 방식.

> **`NonCancellable`** — 언제나 활성인 `Job`. `withContext(NonCancellable)` 안의 코드는 취소되지 않는다.

> **`TimeoutCancellationException`** — `withTimeout` 이 시간 초과 때 던지는 `CancellationException` 의 자손.

## 더 들어가면

- **여러 자식이 동시에 실패하면** — 첫 예외 외의 것은 `suppressed` 로 붙는다고 알려져 있다. 이 문서는 **확인하지 않았다**(격자는 한 자식만 실패시켰다).
- **`CoroutineStart.LAZY`·`ATOMIC`** — 시작 전에 취소되면 몸통이 도나. 돌리지 않았다.
- **멀티스레드 디스패처에서의 격자** — 걸음 수가 흔들릴 것이다. [목록의 **54번 주제**](../54-coroutine-context-dispatchers-and-withcontext/)의 몫이다.
