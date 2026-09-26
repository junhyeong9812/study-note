# kotlin/syntax/54 — `CoroutineContext` 와 디스패처 · `withContext` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — **`kotlinx-coroutines-core-jvm` 1.11.0 의 소스 jar**(같은 판)의 KDoc — `Dispatchers.Default`·`Dispatchers.Unconfined`(`Dispatchers.common.kt`) · `Dispatchers.IO`(`jvmMain/Dispatchers.kt`) · `limitedParallelism` 과 디스패처 `+` 의 폐기 선언(`CoroutineDispatcher.kt`) · `withContext`(`Builders.common.kt`)((5)). ★ 공식 문서 페이지는 **이 작업에서 열지 못했다**(외부 네트워크를 쓰지 않았다) — 설계 논거는 [`../../언어-특성/README.md`](../../언어-특성/README.md) §6 이 원고째 인용한다.
> **실행 검증** — 이 문서의 모든 출력·에러는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `java` 에서 실제로 얻었다.\
> `kotlinc` 7회 · `java` 6회 + 순서 로그 셋을 세 판씩 되풀이한 9회 · 코루틴 소스 jar 발췌 8곳.\
> ★★★ **라이브러리 판 — `kotlinx-coroutines-core-jvm` 1.11.0**(이 머신의 gradle 캐시에 있던 판 중 가장 새 것 · 매니페스트 `Implementation-Version: 1.11.0`). 디스패처·`withContext`·`CoroutineName` 은 전부 **이 라이브러리의 것**이고 언어에는 `CoroutineContext`·`ContinuationInterceptor` **인터페이스만** 있다.\
> ★★ 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적지 않았다. **「줄을 선 칸 N / M」은 격자 프로그램이 스스로 센 것**이다.
> **버전** — `limitedParallelism(parallelism, name)` 의 `name` 인자 판은 이 판의 소스에 있다(도입 판은 **확인하지 않았다**). `Dispatchers.IO` 의 기본 상한은 KDoc 에 「64 또는 코어 수 중 큰 쪽」((5)).
> **경계** — ★★★ 「코루틴은 스레드가 아니라 컴파일러 변환」이라는 **논지**와 「JDBC 는 결국 `withContext(IO)` 로 격리된다 · 가상 스레드와의 대비」는 [`../../언어-특성/README.md`](../../언어-특성/README.md) §6 이 정본이다. **`suspend` 호출 규칙 · `runBlocking` 이 스레드 하나로 돈다 · `delay` 대 `Thread.sleep` 끼어들기**는 [52번 주제](../52-coroutine-basics-suspend-scope-launch-async/)가 쟀다 — 여기서는 인용만 한다. **`Job` 트리에서 취소·예외가 번지는 규칙**은 [53번 주제](../53-structured-concurrency-job-cancellation-exceptions/)다. 공유 가변 상태(`Mutex`·단일 스레드 한정)는 [56번 주제](../56-channel-mutex-and-shared-mutable-state/)다. 스레드 개념은 [`cs/foundations/process-thread/`](../../../../process-thread/) 가 정본이다.
> 이 본문은 Claude 작성이다(원고 없음).

★★★ **본체는 첫째 창이다** — 「**디스패처 격자 — 디스패처 일곱 가지 × 블로킹 호출(`Thread.sleep(200)`) N 개 동시 → 스레드 이름이 하나뿐인가 · 전부 main 인가 · 가장 많이 겹친 순간 몇 개였나(구간 겹침) · 줄을 섰나**」. 시간은 **절댓값을 찍지 않는다** — 각 호출의 시작·끝 시각으로 **겹침 수**만 센다.

## 이 주제가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **언어 보장(stdlib)** | 컴파일러·stdlib 가 하는 것 | `CoroutineContext` 는 **키로 찾는 원소 집합**(`get`·`plus`·`minusKey`·`fold`) · `ContinuationInterceptor` 키 · ★ **`Thread.sleep` 을 `suspend` 함수 안에서 불러도 진단이 없다**((1)의 컴파일 줄) · 폐기 선언 `level = ERROR` 를 **에러로 만드는 것**은 컴파일러다((3)) |
| **라이브러리 계약(kotlinx-coroutines KDoc)** | 라이브러리 문서가 약속한 것 | `Default` 는 「코어 수, 최소 2」 · `IO` 는 「64 또는 코어 수 중 큰 쪽」 · `Unconfined` 는 「중단 뒤 그 함수가 쓴 스레드에서 재개」 · `limitedParallelism` 은 「같은 스레드라는 보장은 없다 · mutex 가 아니다」 · `withContext` 는 「**새 lexically scoped 자식 코루틴**」 · ★ **언어가 아니다** |
| **이 판의 관찰** | 1.11.0 + 이 머신에서 이번에 본 것 | 격자의 참/거짓 · `withContext` 안의 `Job` 클래스 이름(`DispatchedCoroutine` 등) · 스레드 이름(`kotlinx.coroutines.DefaultExecutor` · `DefaultDispatcher-worker-#`) · `BlockingEventLoop` |

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
```

```text
===== kotlinc cores54.kt -d o54n =====
(exit 0)
===== java -cp o54n:kotlin-stdlib.jar Cores54Kt =====
availableProcessors = 24
(exit 0)
```

- ★★ **코어 수는 머신에 매인다** — 격자는 이 수를 **직접 찍지 않고** `N = cores + 1` 처럼 **코어 수에서 유도한 크기**로 돌아서, 칸 값이 「`cores`」·「`all N`」 같은 **이름**으로 나온다. KDoc 대로라면 코어가 2\~63 개인 머신에서 같은 칸이 나온다(`IO` 의 `cores+1` 행은 `cores + 1 ≤ 64` 일 때만 「`all N`」이다 — **다른 머신에서는 돌리지 않았다**).

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다 — 머신에 매인다** | ★ `availableProcessors = 24` | 머신마다 다르다 — 그래서 격자가 이 수를 칸에 안 쓴다 |
| **흔들린다 — 칸으로 안 만들었다** | 걸린 시간 · 스레드 이름의 숫자 | 시간은 **겹침 수**로만 · 이름의 숫자는 **`#` 로 가려** 찍었다(`unconf54.kt` 의 `tn54`) |
| 안 흔들린다(이 머신) | ★★ 격자 8행 · 줄을 선 칸 수 | 200ms 블로킹이라 겹침 판정에 여유가 크다 — **격자를 여덟 판 돌려 출력 해시가 하나**였고(탐침), 캡처 두 벌도 같았다 |
| ★ **관찰일 뿐** | `Default.limitedParallelism(1)` 행의 「`one thread` = `true`」 | KDoc 이 **「같은 스레드라는 보장은 없다」** 고 적는다((5)) — 이 판·이 부하에서 **본 것**이지 약속이 아니다 |
| 안 흔들린다 | 순서 로그(`within54` · `compose54` · `unconf54`) | 부모가 자식의 끝을 기다린 뒤 다음 줄로 간다 — **세 판 되풀이 해시가 셋, 각 3번**((4) 끝의 블록) |
| 안 흔들린다 | 소스 발췌 · 진단 문구 · 종료 코드 | 같은 판이면 같다 |
| ★ **판에 매인다** | 라이브러리 **1.11.0** 의 동작 전부 · 내부 클래스 이름 | 판이 바뀌면 다시 돌려라 |

★ 근거 — 캡처 스크립트를 처음부터 두 번 돌려 **블록 전체를 대조**했다(수치는 3-answer 의 「실행 검증」).

## 한눈에 — 쉽게 말하면

**디스패처는 「어느 주방에서 요리할지」를 정하는 배정표다.** `Default` 주방에는 **화구가 코어 수만큼** 있다 — 요리사가 냄비 앞에서 **멍하니 기다리면(블로킹)** 그 화구가 막혀 다음 손님이 줄을 선다. `IO` 주방은 **기다리기 전용 화구가 64개**(또는 코어 수)라 기다리는 요리를 거기로 옮기면 겹쳐서 돈다. `withContext(IO)` 는 **같은 주문서를 들고 옆 주방에 잠깐 다녀오는 것**이다 — 요리가 끝나면 결과를 들고 원래 주방으로 돌아온다. 주문서(`CoroutineContext`)에는 **주방 · 주문 번호(`Job`) · 이름표(`CoroutineName`)** 가 칸별로 적혀 있고, `+` 는 **같은 칸을 덮어쓴다.**

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 화구가 코어 수만큼 | `Dispatchers.Default` — 동시 실행 최대 `cores` | (1) ★ |
| 멍하니 기다리면 화구가 막힌다 | `Thread.sleep` 은 스레드를 쥔 채 잔다 — 줄을 선다 | (1) ★ |
| 기다리기 전용 화구 64개 | `Dispatchers.IO` — 상한 `max(64, cores)` | (1)(5) ★ |
| 옆 주방에 다녀온다 | `withContext(IO) { }` — 결과를 들고 원래 디스패처로 | (2) ★ |
| 주문서의 칸 | `CoroutineContext[Job]`·`[CoroutineName]`·`[ContinuationInterceptor]` | (3) |
| `+` 는 같은 칸 덮어쓰기 | `ctx + CoroutineName("b")` — 원소 수 그대로 · 이름만 바뀜 | (3) |
| 아무 주방이나 | `Dispatchers.Unconfined` — 중단 뒤 **깨운 쪽 스레드**에서 계속 | (4) |

```text
   launch(Dispatchers.Default) { Thread.sleep(200) }  × (cores + 1)      (이 머신: 코어 24)

   화구 1  ■■■■■■■■■■                      ← 스레드를 쥐고 잔다
   화구 2  ■■■■■■■■■■
   …       …
   화구 24 ■■■■■■■■■■
   (25번째)           ■■■■■■■■■■           ← 화구가 빌 때까지 줄을 선다
                                             most at once = cores

   launch(Dispatchers.Default) { withContext(Dispatchers.IO) { Thread.sleep(200) } }

   IO 1..25 ■■■■■■■■■■                     ← 전부 겹친다   most at once = all N
```

## 이 주제가 답하려는 질문

1. **블로킹 호출을 디스패처마다 N 개 동시에 걸면** 몇 개가 겹쳐 도나 — 어느 디스패처가 줄을 세우나.
2. **`withContext` 는 무엇을 만드나** — 같은 코루틴인가 새 코루틴인가, 결과·예외·취소는 어디로 가나.
3. **`CoroutineContext` 는 무엇으로 이루어졌고 `+` 는 무엇을 하나** — 자식은 무엇을 물려받나.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **디스패처 격자(실행 · 구간 겹침)** | 디스패처 × 블로킹 N 개 → 스레드 하나인가 · main 인가 · 가장 많이 겹친 수 · 줄을 섰나((1)) | ★ **본체 창** |
| ★★ **`withContext` 로그** | 안쪽 `Job` 이 바깥 `Job` 의 자식인가 · 결과 · 예외 · 취소 · 경로마다 `Job` 클래스((2)) | — |
| ★★ **문맥 합성 로그** | `+`·`minusKey`·`fold` 로 원소 수와 값((3)) | — |
| ★★ **컴파일러 진단** | 디스패처 `+` 디스패처 → 폐기 에러 전문((3)) · `Thread.sleep` 은 **진단 0줄**((1)) | — |
| ★ **스레드 이름 로그** | `Unconfined` 가 중단 뒤 어디서 재개하나((4)) | — |
| ★★ **코루틴 소스 jar 발췌** | 디스패처 KDoc 의 상한 · `withContext` 의 세 갈래 경로((5)) | — |
| **인용 — 다시 안 잰다** | `runBlocking` 은 스레드 하나 · `delay` 는 끼어들고 `Thread.sleep` 은 안 끼어든다 · `suspend` 호출 규칙 | [52번 주제](../52-coroutine-basics-suspend-scope-launch-async/) |
| ★ **제5의 상태 — 창을 바꿔 물었다** | 「스레드 풀이 막혔나」를 **풀 내부 계측**(큐 길이·활성 스레드 수)이 아니라 **각 호출의 시작·끝 시각의 겹침 수**로 물었다 | (1) — 이 창은 **스레드가 몇 개 만들어졌는지는 못 본다**(이름 집합 크기가 1 인가만 본다) |
| **부적용 — 실행 시간 · 처리량** | ★★★ 「`IO` 가 빠르다」·「`Default` 가 느리다」는 **재지 않았다** — 이 문서가 말하는 것은 **겹쳤나 줄을 섰나**뿐이다 | — |
| **부적용 — IDE 경고** | 「부적절한 블로킹 호출」 경고는 **IDE 검사**다 — `kotlinc` 에는 없다((1)) · IDE 는 **돌리지 않았다** | — |

### (1) ★★★ 디스패처 격자 — 블로킹 N 개를 걸면

**언제 쓰나** — 코루틴 안에서 JDBC·파일·옛 HTTP 클라이언트처럼 **스레드를 쥐고 기다리는** API 를 부를 때.

방법 — 행마다 코루틴 N 개를 `launch` 하고 각 코루틴이 `Thread.sleep(200)` 한다. 호출마다 **스레드 이름과 시작·끝 시각**을 모아 — 이름 집합 크기가 1 인가(`one thread`) · 전부 `main` 인가(`all on main`) · **가장 많이 겹친 순간의 수**(`most at once` — `N` 이면 `all N`, 코어 수면 `cores`, `IO` 상한이면 `ioLimit`) · 그 수가 N 보다 작은가(`queued`)를 찍는다. 마지막 줄은 **줄을 선 행 수**다. ★ N 은 코어 수에서 유도했다(`cores + 1` · `ioLimit + 1`).

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

```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar grid54.kt -d o54g =====
(exit 0)
===== java -cp o54g:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Grid54Kt 2>/dev/null =====
dispatcher	N	one thread	all on main	most at once	queued
runBlocking (no dispatcher)	cores+1	true	true	1	true
Dispatchers.Unconfined	cores+1	true	true	1	true
newSingleThreadContext	cores+1	true	false	1	true
Default.limitedParallelism(1)	cores+1	true	false	1	true
Dispatchers.Default	cores+1	false	false	cores	true
Default -> withContext(IO)	cores+1	false	false	all N	false
Dispatchers.IO	cores+1	false	false	all N	false
Dispatchers.IO	ioLimit+1	false	false	ioLimit	true
rows where blocking calls queued: 6 / 8
(exit 0)
```

- ★★★ **8행 중 6행이 줄을 섰다** — 겹친 것은 **`Dispatchers.IO` 에 `cores + 1` 개**와 **`Default` 에서 `withContext(IO)` 로 옮긴 것** 둘뿐이다.
- ★★★ **`Dispatchers.Default` 는 `cores` 개까지만 겹쳤다** — `cores + 1` 번째는 **앞의 하나가 끝나야** 시작했다. `Default` 의 스레드 수는 코어 수이고((5) KDoc), `Thread.sleep` 은 **스레드를 쥔 채** 자므로 그 스레드에서는 다른 코루틴이 못 돈다.
- ★★★ **`withContext(Dispatchers.IO)` 로 감싸면 `Default` 에서 걸어도 전부 겹친다** — 블로킹 구간만 `IO` 로 옮겨졌다. `IO` 도 **상한이 있다** — `ioLimit + 1` 개를 걸자 `most at once` 가 **`ioLimit`**(이 머신에서 64)이었다. 「`IO` 는 무한」이 아니다.
- ★★ **한 스레드짜리 넷(`runBlocking` · `Unconfined` · `newSingleThreadContext` · `limitedParallelism(1)`)은 전부 `1`** — 하나씩 차례로 잤다. `runBlocking` 과 `Unconfined` 는 **main 에서**, 나머지 둘은 **다른 스레드 하나에서** 돌았다.
- ★★ **`Unconfined` 는 한 줄도 안 겹쳤다** — `launch(Unconfined)` 는 **부른 자리(main)에서 첫 중단점까지 바로** 돌고((4)), `Thread.sleep` 에는 중단점이 없으니 **`launch` 호출이 200ms 씩 막혔다.**
- ★ **`limitedParallelism(1)` 의 `one thread = true` 는 관찰이다** — KDoc 은 「`no guarantee that the underlying system thread will always be the same`」라고 적는다((5)). 보장되는 것은 **동시에 둘이 안 돈다(`most at once = 1`)** 쪽이다.
- ★★ **컴파일 줄이 비었다** — 코루틴 안에서 `Thread.sleep` 을 부르는 소스인데 **`kotlinc` 는 진단 0줄 · `exit 0`** 이다. 「이 호출은 스레드를 막는다」는 **컴파일러가 모르는 사실**이다 — 고르는 것은 사람이다.

### (2) ★★★ `withContext` — 새 자식 `Job` 을 만들고, 끝날 때까지 기다리고, 결과를 돌려준다

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

```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar within54.kt -d o54w =====
(exit 0)
===== java -cp o54w:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Within54Kt 2>/dev/null =====
1 inner Job === outer Job: false
2 inner Job is a child of outer Job: true
3 CoroutineName inside: CoroutineName(outer54)
4 dispatcher inside: Dispatchers.IO
5 running on main: false
6 value returned: 42 · back on main: true
7 withContext(IO): Job class = DispatchedCoroutine · on main = false
7 withContext(CoroutineName only): Job class = UndispatchedCoroutine · on main = true
7 withContext(EmptyCoroutineContext): Job class = ScopeCoroutine · on main = true
8 caught at the withContext call: thrown inside · outer Job active: true
10 finally inside withContext · on main = false
12 caller caught JobCancellationException · on main = true
13 launched job isCancelled: true
(exit 0)
```

- ★★★ **안쪽 `Job` 은 바깥 `Job` 이 아니다 — 그 자식이다**(`1 … false` · `2 … true`). KDoc 도 「`creates a new *lexically scoped child coroutine*`」라고 적는다((5)). 「같은 코루틴의 문맥만 바꾼다」는 **반만 맞다** — 코드는 한 흐름으로 이어지지만(`launch` 와 달리 **부른 쪽이 끝날 때까지 멈춘다**), 라이브러리는 **새 자식 `Job`** 을 만든다.
- ★★★ **물려받는 것과 바뀌는 것** — `CoroutineName(outer54)` 은 그대로(`3`), 디스패처만 `Dispatchers.IO` 로 바뀌었다(`4`·`5`). 끝나면 **`42` 를 돌려주고 main 으로 돌아왔다**(`6`).
- ★★★ **경로가 셋이다(`7`)** — 디스패처가 바뀌면 `DispatchedCoroutine`(다른 스레드) · 이름만 바뀌면 `UndispatchedCoroutine`(**같은 스레드 · 디스패치 없음**) · 아무것도 안 바뀌면 `ScopeCoroutine`. 소스의 **FAST PATH #1 · #2 · SLOW PATH** 그대로다((5)). ★ 클래스 이름은 **내부 구현**이다 — 외울 것은 「디스패처가 같으면 스레드를 안 바꾼다」다.
- ★★★ **예외는 부른 자리로 다시 던져지고 바깥은 살아 있다**(`8 … thrown inside · outer Job active: true`) — KDoc 「`the failure of the [Job] will not affect the parent [Job]. Instead, the exception … will be rethrown to the caller`」. 같은 실패가 `launch` 자식에서 났으면 부모가 취소된다([53번 주제](../53-structured-concurrency-job-cancellation-exceptions/)).
- ★★★ **취소는 안으로 번진다** — 바깥 `job.cancel()` 에 `withContext` 안의 `delay` 가 끊겨 `9`·`11` 은 **안 찍히고**, 안쪽 `finally` 가 **IO 스레드에서**(`10 … on main = false`), 이어서 부른 쪽이 `JobCancellationException` 을 **main 에서** 받았다(`12`).

### (3) ★★ `CoroutineContext` — 키로 찾는 원소 집합, `+` 는 같은 키를 덮어쓴다

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

```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar compose54.kt -d o54c =====
(exit 0)
===== java -cp o54c:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Compose54Kt 2>/dev/null =====
1 elements: 3
2 [CoroutineName] = CoroutineName(a54)
3 [ContinuationInterceptor] = Dispatchers.IO
4 [Job] present: true
5 after + CoroutineName(b54): elements 3 · name CoroutineName(b54)
6 Default + IO: elements 1 · Dispatchers.IO
7 minusKey(CoroutineName): elements 2 · name null
8 runBlocking dispatcher class: BlockingEventLoop
9 child without name sees: CoroutineName(parent54)
10 child with + sees: CoroutineName(child54) · Dispatchers.IO
11 a running child is in parent.children: true
(exit 0)
```

- ★★★ **`Job() + Dispatchers.IO + CoroutineName("a54")` 는 원소 셋**이고 **키로 꺼낸다** — `ctx[CoroutineName]` · `ctx[ContinuationInterceptor]` · `ctx[Job]`. 디스패처의 키가 `ContinuationInterceptor` 라는 것이 핵심이다 — **stdlib 의 `kotlin.coroutines` 에 있는 키**이고, 디스패처는 그 **라이브러리 구현**이다.
- ★★★ **`+` 는 같은 키를 오른쪽으로 덮어쓴다** — `+ CoroutineName("b54")` 뒤에도 원소는 **셋** · 이름만 `b54`(`5`). 디스패처 둘을 `CoroutineContext` 로 더하면 **원소 하나 · 오른쪽 `IO`**(`6`). `minusKey` 는 그 칸을 뺀다(`7`).
- ★★ **자식은 부모의 문맥을 물려받고 `launch(…)` 인자가 덮는다** — 이름 없는 자식은 `parent54` 를 보고(`9`), `Dispatchers.IO + CoroutineName("child54")` 를 준 자식은 둘 다 바뀌었다(`10`). 도는 동안은 **부모 `Job` 의 `children` 에 있다**(`11`). ★ `runBlocking` 의 디스패처는 `BlockingEventLoop`(`8`) — [52번 주제](../52-coroutine-basics-suspend-scope-launch-async/)가 잰 「스레드 하나」의 정체다.

```kotlin
// dplus54.kt
import kotlinx.coroutines.*

val both54 = Dispatchers.Default + Dispatchers.IO
```

```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar dplus54.kt -d o54p =====
dplus54.kt:3:34: error: 'fun plus(other: CoroutineDispatcher): CoroutineDispatcher' is deprecated. Operator '+' on two CoroutineDispatcher objects is meaningless. CoroutineDispatcher is a coroutine context element and `+` is a set-sum operator for coroutine contexts. The dispatcher to the right of `+` just replaces the dispatcher to the left.
val both54 = Dispatchers.Default + Dispatchers.IO
                                 ^
(exit 1)
```

- ★★★ **디스패처 둘을 그대로 `+` 하면 컴파일 에러다** — 「`` Operator '+' on two CoroutineDispatcher objects is meaningless. … The dispatcher to the right of `+` just replaces the dispatcher to the left. ``」 **언어 규칙이 아니라** 라이브러리가 `plus(CoroutineDispatcher)` 를 **`@Deprecated(level = ERROR)`** 로 막아 둔 것이고((5)), 그것을 **에러로 만드는 것이 컴파일러**다. 위 `compose54.kt` 가 `as CoroutineContext` 로 올려 더한 것은 **이 오버로드를 피하려고**다 — 결과는 메시지 그대로 **오른쪽이 이긴다**(`6`).

### (4) ★★ `Unconfined` — 첫 중단점까지는 부른 자리, 그 뒤는 깨운 쪽 스레드

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

```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar unconf54.kt -d o54u =====
(exit 0)
===== java -cp o54u:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Unconf54Kt 2>/dev/null =====
U1 before delay: main
M1 line after launch(Unconfined): main
U2 after delay: kotlinx.coroutines.DefaultExecutor
U3 inside withContext(IO): DefaultDispatcher-worker-#
U4 after withContext(IO): DefaultDispatcher-worker-#
M2 line after launch: main
C1 before delay: main
C2 after delay: main
C3 inside withContext(IO): DefaultDispatcher-worker-#
C4 after withContext(IO): main
(exit 0)
```

- ★★★ **`Unconfined` 는 `launch` 자리에서 바로 돈다** — `U1` 이 `M1` 보다 먼저, **main** 에서. 기본 `launch` 는 줄을 세우므로 `M2` 가 `C1` 보다 먼저다([52번 주제](../52-coroutine-basics-suspend-scope-launch-async/)가 잰 「`launch { }` 는 몸통을 바로 안 돌린다」).
- ★★★ **중단 뒤에는 다른 스레드다** — `delay` 뒤 `U2` 는 **`kotlinx.coroutines.DefaultExecutor`**(지연을 깨우는 스레드), `withContext(IO)` 뒤 `U4` 는 **IO 워커 그대로** 남았다. KDoc 「`lets the coroutine resume in whatever thread that is used by the corresponding suspending function`」.
- ★★ **대조 — `runBlocking` 안 기본 `launch` 는 늘 main 으로 돌아온다**(`C2`·`C4`) — `withContext` 의 결과가 **원래 디스패처(`BlockingEventLoop`)로 다시 디스패치**되기 때문이다((5) SLOW PATH).
- ★ 스레드 이름은 **내부 구현**이다 — 숫자는 `#` 로 가렸고, `DefaultExecutor` 라는 이름도 이 판의 것이다.

```text
===== for i in 1 2 3; do java -cp o54w:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Within54Kt | md5sum; java -cp o54c:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Compose54Kt | md5sum; java -cp o54u:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Unconf54Kt | md5sum; done | sort | uniq -c =====
      3 1fe7d5f5cbb3ae2f8605094cf2e8bb4c  -
      3 bcbd6a2cebeb2a4a01f4d21cb652babf  -
      3 e9436d2d1e16ed519b856ee1c4738a5b  -
(exit 0)
```

- ★ **순서 로그 셋(`within54` · `compose54` · `unconf54`)을 세 판씩 돌려 출력 전체의 해시를 센 것**이다 — 서로 다른 해시가 **셋**이고 각각 **`3`** 번이다(규칙 11 — 「가짓수」를 찍는다).

### (5) ★★ 코루틴 소스 jar — 상한 · 재개 스레드 · `withContext` 의 세 경로

```text
===== unzip -o -q kotlinx-coroutines-core-jvm-1.11.0-sources.jar commonMain/Dispatchers.common.kt jvmMain/Dispatchers.kt commonMain/Builders.common.kt commonMain/CoroutineDispatcher.kt =====
(exit 0)
```

```text
===== sed -n '9,17p' commonMain/Dispatchers.common.kt =====
    /**
     * The default [CoroutineDispatcher] that is used by all standard builders like
     * [launch][CoroutineScope.launch], [async][CoroutineScope.async], etc.
     * if neither a dispatcher nor any other [ContinuationInterceptor] is specified in their context.
     *
     * It is backed by a shared pool of threads on JVM and Native. By default, the maximum number of threads used
     * by this dispatcher is equal to the number of CPU cores, but is at least two.
     */
    public val Default: CoroutineDispatcher
(exit 0)
===== sed -n '40,46p' commonMain/Dispatchers.common.kt =====
    /**
     * A coroutine dispatcher that is not confined to any specific thread.
     * It executes the initial continuation of a coroutine in the current call-frame
     * and lets the coroutine resume in whatever thread that is used by the corresponding suspending function, without
     * mandating any specific threading policy. Nested coroutines launched in this dispatcher form an event-loop to avoid
     * stack overflows.
     *
(exit 0)
===== sed -n '25,30p' jvmMain/Dispatchers.kt =====
     * The [CoroutineDispatcher] that is designed for offloading blocking IO tasks to a shared pool of threads.
     *
     * Additional threads in this pool are created and are shutdown on demand.
     * The number of threads doing IO work in parallel is limited by the value of
     * "`kotlinx.coroutines.io.parallelism`" ([IO_PARALLELISM_PROPERTY_NAME]) system property.
     * It defaults to the limit of 64 threads or the number of cores (whichever is larger).
(exit 0)
```

- ★★★ **`Default`** — 「`the maximum number of threads used by this dispatcher is equal to the number of CPU cores, but is at least two`」. (1)의 `cores` 칸이 이것이다.
- ★★★ **`IO`** — 「`It defaults to the limit of 64 threads or the number of cores (whichever is larger)`」 · 상한은 시스템 속성 `kotlinx.coroutines.io.parallelism` 으로 바꾼다. (1)의 `ioLimit` 칸이 이것이다. [`../../언어-특성/README.md`](../../언어-특성/README.md) §6 의 「64스레드 상한」이 **이 판에서도 같은 문장**이다.
- ★★ **`Unconfined`** — 「`executes the initial continuation of a coroutine in the current call-frame and lets the coroutine resume in whatever thread …`」 — (4)의 `U1` 과 `U2`·`U4`.

```text
===== sed -n '155,160p' commonMain/CoroutineDispatcher.kt =====
     * Note that there is no guarantee that the underlying system thread will always be the same.
     *
     * #### It is not a mutex!
     *
     * **Pitfall**: [limitedParallelism] limits how many threads can execute some code in parallel,
     * but does not limit how many coroutines execute concurrently!
(exit 0)
===== sed -n '298,303p' commonMain/CoroutineDispatcher.kt =====
    @Deprecated(
        message = "Operator '+' on two CoroutineDispatcher objects is meaningless. " +
            "CoroutineDispatcher is a coroutine context element and `+` is a set-sum operator for coroutine contexts. " +
            "The dispatcher to the right of `+` just replaces the dispatcher to the left.",
        level = DeprecationLevel.ERROR
    )
(exit 0)
```

- ★★★ **`limitedParallelism` 은 「같은 스레드」를 약속하지 않고 「mutex 가 아니다」** — 동시에 **둘이 안 돈다**는 것만 보장하고, 중단점에서 **다른 코루틴이 끼어든다.** 공유 상태를 지키는 도구로 쓸 때의 경계는 [56번 주제](../56-channel-mutex-and-shared-mutable-state/)다.
- ★★ 디스패처 `+` 의 에러는 **이 `@Deprecated(… level = DeprecationLevel.ERROR)`** 에서 온다 — (3)의 진단 문구와 한 글자도 같다.

```text
===== sed -n '321,323p;333,340p' commonMain/Builders.common.kt =====
/**
 * Calls the specified suspending [block] with an updated coroutine context, suspends until it completes, and returns
 * the result.
 * ## Structured Concurrency
 *
 * The behavior of [withContext] is similar to [coroutineScope], as it, too,
 * creates a new *lexically scoped child coroutine*.
 * Refer to the documentation of that function for details.
 *
 * The difference is that [withContext] does not simply call the [block] in a new coroutine
 * but updates the [currentCoroutineContext] used for running it.
(exit 0)
===== sed -n '347,355p' commonMain/Builders.common.kt =====
 * - Then, the [Job] in the [currentCoroutineContext], if any, is used as the *parent* of the new scope,
 *   unless overridden.
 *   Overriding the [Job] is forbidden with the notable exception of [NonCancellable];
 *   see a separate subsection below for details.
 *   The new scope's [Job] is added to the resulting context.
 *
 * The [Job] of the new scope is not a normal child of the caller coroutine but a **lexically scoped** one,
 * meaning that the failure of the [Job] will not affect the parent [Job].
 * Instead, the exception leading to the failure will be rethrown to the caller of this function.
(exit 0)
===== sed -n '484,503p' commonMain/Builders.common.kt =====
        // always check for cancellation of new context
        newContext.ensureActive()
        // FAST PATH #1 -- new context is the same as the old one
        if (newContext === oldContext) {
            val coroutine = ScopeCoroutine(newContext, uCont)
            return@sc coroutine.startUndispatchedOrReturn(coroutine, block)
        }
        // FAST PATH #2 -- the new dispatcher is the same as the old one (something else changed)
        // `equals` is used by design (see equals implementation is wrapper context like ExecutorCoroutineDispatcher)
        if (newContext[ContinuationInterceptor] == oldContext[ContinuationInterceptor]) {
            val coroutine = UndispatchedCoroutine(newContext, uCont)
            // There are changes in the context, so this thread needs to be updated
            withCoroutineContext(coroutine.context, null) {
                return@sc coroutine.startUndispatchedOrReturn(coroutine, block)
            }
        }
        // SLOW PATH -- use new dispatcher
        val coroutine = DispatchedCoroutine(newContext, uCont)
        block.startCoroutineCancellable(coroutine, coroutine)
        coroutine.getResult()
(exit 0)
```

- ★★★ **`withContext` 는 「새 lexically scoped 자식 코루틴」** — `coroutineScope` 와 같은 부류이고, 차이는 **문맥을 바꿔 돌린다**는 것뿐이다. 바깥 `Job` 이 부모가 되고, 실패는 부모를 취소하지 않고 **부른 자리로 다시 던져진다**((2)의 `2`·`8`).
- ★★★ **세 갈래 경로** — 문맥이 같으면 `ScopeCoroutine`, **디스패처가 같으면 `UndispatchedCoroutine`(디스패치 없이 그 자리에서)**, 디스패처가 다르면 `DispatchedCoroutine` 을 만들어 **새 디스패처에 보낸다.** 들어가기 전 `ensureActive()` 로 **취소부터 확인**한다.

## 문법 — 형태와 규칙

**형태** — 블로킹 API 를 감싸는 함수가 디스패처를 고른다 · 결과를 받는 `withContext` · 이름을 얹은 문맥.

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

```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar form54.kt -d o54f =====
(exit 0)
===== java -cp o54f:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Form54Kt 2>/dev/null =====
[value-of-a, value-of-b, value-of-c]
CoroutineName(form54)
(55, CoroutineName(cpu54))
(exit 0)
```

**규칙 불릿**

- **블로킹 호출은 그것을 감싸는 `suspend` 함수 안에서 `withContext(Dispatchers.IO)` 로 옮긴다** — 부르는 쪽이 디스패처를 몰라도 된다((1)).
- **`Default` 는 코어 수만큼만 겹친다 · `IO` 는 `max(64, cores)` 까지** — 둘 다 상한이 있다((1)(5)).
- **`withContext` 는 결과를 돌려주고, 끝날 때까지 부른 쪽을 멈추며, 예외를 부른 자리로 던진다** — `launch` 와 다르다((2)).
- **문맥의 `+` 는 같은 키를 덮어쓴다** — 디스패처끼리 직접 `+` 는 에러다((3)).
- **`Unconfined` 는 재개 스레드를 고르지 않는다** — 중단 뒤 어느 스레드에 있을지 모른다((4)).
- **스레드가 하나인 디스패처라도 중단점 사이에는 다른 코루틴이 낀다** — `limitedParallelism(1)` 은 mutex 가 아니다((5)).

## 어디서 틀리나

1. ★★★ **`Dispatchers.Default` 에서 `Thread.sleep`·JDBC 를 그냥 부른다.** 코어 수를 넘으면 줄을 선다 — 그동안 **CPU 일을 하려던 다른 코루틴도** 그 스레드를 못 쓴다((1)).
2. ★★★ **컴파일러가 블로킹 호출을 잡아 줄 거라고 본다.** `kotlinc` 는 진단 0줄이다((1)) — 경고는 IDE 검사의 몫이고 이 문서는 IDE 를 안 돌렸다.
3. ★★★ **「`IO` 는 스레드가 무한」으로 본다.** `max(64, cores)` 에서 줄을 선다((1)(5)).
4. ★★ **`withContext` 가 `launch` 처럼 따로 돈다고 본다.** 부른 쪽이 멈추고 결과를 받는다 — 동시 실행이 필요하면 `async`((2)).
5. ★★ **`withContext` 안의 예외가 부모를 죽인다고 본다.** 부른 자리로 던져지고 `try` 로 잡힌다((2) `8`) — 부모를 죽이는 것은 `launch` 자식의 실패다([53번 주제](../53-structured-concurrency-job-cancellation-exceptions/)).
6. ★★ **`Dispatchers.Default + Dispatchers.IO` 로 「둘 다」를 쓰려 한다.** 컴파일 에러다 — 문맥에 디스패처 칸은 하나다((3)).
7. ★★ **`Unconfined` 를 「가장 가벼운 디스패처」로 쓴다.** 중단 뒤 `DefaultExecutor`·IO 워커에 남는다((4)) — 그 뒤의 블로킹이 **엉뚱한 스레드를 막는다.**
8. ★ **`limitedParallelism(1)` 을 락으로 쓴다.** 중단점에서 끼어든다((5)).

## 구현 세부사항 대 언어 보장

| 항목 | 어느 쪽인가 | 근거 |
|---|---|---|
| `CoroutineContext` 의 `get`·`plus`·`minusKey`·`fold` · `ContinuationInterceptor` 키 | ★★★ **언어(stdlib `kotlin.coroutines`)** | (3) |
| `Thread.sleep` 을 코루틴 안에서 불러도 진단 없음 | ★★ **컴파일러의 성질(이 판)** | (1) |
| 디스패처 `+` 디스패처가 에러 | ★★ **라이브러리 선언(`@Deprecated ERROR`)** — 에러로 만드는 것은 컴파일러 | (3)(5) |
| `Default` = 코어 수(최소 2) · `IO` = `max(64, cores)` | ★★★ **라이브러리 계약(KDoc)** | (5) |
| `withContext` 가 새 lexically scoped 자식을 만들고 예외를 부른 자리로 던진다 | ★★★ **라이브러리 계약(KDoc)** | (2)(5) |
| `Unconfined` 가 깨운 쪽 스레드에서 재개 | ★★ **라이브러리 계약(KDoc)** — 어느 스레드인지(`DefaultExecutor`)는 **구현** | (4)(5) |
| `limitedParallelism(1)` 이 한 스레드에서만 돌았다 | ★ **이 판의 관찰** — KDoc 은 보장하지 않는다 | (1)(5) |
| `DispatchedCoroutine`·`UndispatchedCoroutine`·`ScopeCoroutine`·`BlockingEventLoop` · 스레드 이름 | ★ **라이브러리 구현(1.11.0)** | (2)(3)(4) |
| 「`IO` 가 빠르다」 | **재지 않았다** | — |

★★ **가장 조심할 자리** — 「`Default` 는 코어 수」·「`IO` 는 64」는 **언어가 아니라 라이브러리 KDoc** 이다. 판이 바뀌거나 시스템 속성을 주면 달라진다 — 격자를 다시 돌려라.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| JDBC·파일·블로킹 HTTP 를 코루틴에서 | ★ `withContext(Dispatchers.IO) { }` 로 감싼 `suspend` 함수 | (1) — 겹쳐 돈다 · `Default` 를 안 막는다 |
| CPU 계산(정렬·파싱·암호) | `Dispatchers.Default` | (5) — 코어 수만큼 |
| 블로킹 대상마다 따로 상한(연결 풀 크기) | `Dispatchers.IO.limitedParallelism(n)` | (5) KDoc — `IO` 는 뷰의 합이 상한에 안 묶인다(**재지 않았다**) |
| 한 스레드에서만 만져야 하는 상태 | `limitedParallelism(1)` · 단일 스레드 디스패처 — 단 **중단점 사이만** 보호 | (1)(5) · [56번 주제](../56-channel-mutex-and-shared-mutable-state/) |
| `main` 함수·테스트의 경계 | `runBlocking` | [52번 주제](../52-coroutine-basics-suspend-scope-launch-async/) |
| 「어느 스레드든 상관없다」가 **증명된** 짧은 코드 | `Unconfined` — 거의 쓸 일이 없다 | (4) |
| 이름표로 로그 가르기 | `CoroutineName("…")` 을 `+` 로 | (3) |

## 핵심 문장

1. **디스패처는 코루틴이 도는 스레드를 고르고, 블로킹 호출은 그 스레드를 쥔 채 잔다** — `Default` 에서는 코어 수를 넘으면 줄을 선다(8행 중 6행이 줄을 섰다).
2. **`withContext(Dispatchers.IO)` 로 블로킹 구간만 옮기면 겹친다** — 그러나 `IO` 도 `max(64, cores)` 에서 멈춘다.
3. **`withContext` 는 새 lexically scoped 자식 `Job` 을 만들어 끝날 때까지 기다리고, 결과를 돌려주며, 예외는 부른 자리로 던진다** — 취소는 안으로 번진다.
4. **`CoroutineContext` 는 키로 찾는 원소 집합이고 `+` 는 같은 키를 덮어쓴다** — 디스패처끼리 `+` 는 라이브러리가 막아 둔 에러다.
5. **`Default`·`IO` 의 스레드 수와 `Unconfined` 의 재개 규칙은 언어가 아니라 kotlinx-coroutines 의 KDoc 이다.**

## 관련 자료

- [52번 주제](../52-coroutine-basics-suspend-scope-launch-async/) — ★★★ **선행.** `suspend` 호출 규칙 · `runBlocking` 이 스레드 하나 · `delay` 대 `Thread.sleep` 끼어들기. 그쪽은 **한 스레드 위의 순서**, 여기는 **여러 스레드를 고르는 규칙**.
- [53번 주제](../53-structured-concurrency-job-cancellation-exceptions/) — `Job` 트리의 취소·예외 전파. (2)의 `withContext` 가 「부모를 안 죽이는 자식」인 이유가 거기서 서는 규칙이다.
- [55번 주제](../55-flow-cold-streams-operators-and-collect/) — `Flow` 의 `flowOn` 은 이 디스패처를 **상류에만** 바꾼다. [56번 주제](../56-channel-mutex-and-shared-mutable-state/) — 단일 스레드 한정과 `Mutex`.
- [`../../언어-특성/README.md`](../../언어-특성/README.md) §6 — ★ **정본.** 「JDBC 는 `withContext(IO)` 로 격리될 뿐」·가상 스레드와의 대비. 그쪽은 **이 언어를 고를 것인가**, 여기는 **그래서 어느 디스패처로 옮기나**.
- [Java 54번](../../../java/syntax/54-executorservice-and-future/) — 스레드 풀과 `Future`. 디스패처는 **그 풀에 코루틴을 올리는 층**이다. [Java 56번](../../../java/syntax/56-virtual-threads/) — 블로킹을 **런타임이 흡수**하는 반대 해법.
- [Python 52번](../../../python/syntax/52-asyncio-concurrency-structure/) (4) — 「블로킹 호출은 루프를 멈춘다」와 `asyncio.to_thread`. 같은 문제를 **스레드로 떠넘기는** 같은 모양 — Kotlin 은 떠넘길 풀을 **디스패처로 고른다.**
- [`cs/foundations/process-thread/`](../../../../process-thread/) — 스레드·스레드 풀 개념의 정본.

## 용어 풀이

> **`CoroutineContext`** — 코루틴에 붙은 원소 집합. 원소마다 **키**가 있고 `ctx[키]` 로 꺼낸다(`Job` · `ContinuationInterceptor` · `CoroutineName`).\
> 예: `(Job() + Dispatchers.IO)[ContinuationInterceptor]` 는 `Dispatchers.IO`.

> **디스패처(`CoroutineDispatcher`)** — 코루틴을 **어느 스레드에서 돌릴지** 정하는 문맥 원소. 키는 `ContinuationInterceptor`.

> **블로킹 호출** — 끝날 때까지 **스레드를 쥔 채 기다리는** 호출(`Thread.sleep` · JDBC · `InputStream.read`). 중단점이 아니다.

> **`withContext(ctx) { }`** — 문맥을 바꿔 블록을 돌리고, 끝날 때까지 부른 쪽을 멈춘 뒤 **결과를 돌려주는** `suspend` 함수.

> **lexically scoped 자식** — 블록이 끝나면 함께 끝나는 자식 `Job`. 실패가 부모를 취소하지 않고 **부른 자리로 던져진다**(`coroutineScope`·`withContext`).

> **`Dispatchers.Unconfined`** — 첫 중단점까지는 부른 자리에서, 그 뒤로는 **깨운 쪽 스레드**에서 도는 디스패처.

> **`limitedParallelism(n)`** — 원래 디스패처 위에서 **동시에 n 개까지만** 돌게 하는 뷰.

## 더 들어가면

- **`IO.limitedParallelism(n)` 의 탄력성** — KDoc 은 「뷰의 합이 `IO` 의 상한에 안 묶인다」고 적는다((5) 밖). 64 를 넘는 뷰 둘을 동시에 채우는 격자로 볼 수 있다 — **돌리지 않았다.**
- **`kotlinx.coroutines.io.parallelism` 시스템 속성** — 바꾸면 (1)의 `ioLimit` 칸이 따라 움직여야 한다. **돌리지 않았다.**
- **`Default` 와 `IO` 의 스레드 공유** — KDoc 은 「`IO` 와 그 뷰는 `Default` 와 스레드를 공유해 `withContext` 가 실제로는 스레드를 안 바꾸는 경우가 있다」고 적는다. (2)의 `5`(`on main = false`)는 **main 에서 들어갔기 때문**이고, `Default` 에서 들어가 같은 스레드에 남는지는 **재지 않았다.**
- **`ThreadContextElement`** — MDC·trace 처럼 `ThreadLocal` 을 문맥에 실어 스레드를 옮겨도 따라가게 하는 원소. [`../../언어-특성/README.md`](../../언어-특성/README.md) §6 의 「MDC·trace 유실」이 이것으로 푼다 — **돌리지 않았다.**
