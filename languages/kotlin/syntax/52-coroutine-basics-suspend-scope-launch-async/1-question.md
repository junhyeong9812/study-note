# kotlin/syntax/52 — 코루틴 기초 — `suspend`·`CoroutineScope`·`launch`/`async`/`await` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [10번 주제](../10-lambdas-and-higher-order-functions/)(람다와 고차 함수)와 [34번 주제](../34-exceptions-nothing-and-try-expression/)(예외)다.
> 문항 10개 중 예측형은 6개이고, 6개 모두 코드블록이 붙는다.
> 이 주제의 모든 답은 **kotlinc 2.4.20 · Temurin JDK 21.0.5 · kotlinx-coroutines 1.11.0** 에서 실제로 던져 받은 것이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 세 함수의 JVM 모양 (예측)

```kotlin
// cps52.kt
import kotlinx.coroutines.delay

suspend fun twice(x: Int): Int {
    delay(1)
    val y = x * 2
    delay(1)
    return y
}

suspend fun plain(x: Int): Int = x + 1

fun normal(x: Int): Int = x + 1
```

- `kotlinc` 가 만드는 `.class` 파일은 몇 개이고 이름은? `javap -p` 로 본 세 함수의 서명은? 생긴 클래스가 있다면 그 필드는? `twice` 의 `tableswitch` 는 몇부터 몇까지인가?

### 2. ★★★ 아홉 자리에서 부르기 (예측)

```kotlin
// call52.kt
import kotlinx.coroutines.runBlocking

suspend fun f(x: Int): Int = x

fun p1() { f(1) }                                                        // plain-function
suspend fun p2() { f(1) }                                                // suspend-function
suspend fun p3() { listOf(1).forEach { f(it) } }                         // inline-lambda
suspend fun p4() { val g: () -> Unit = { f(1) } }                        // plain-lambda-type
suspend fun p5() { val g: suspend () -> Unit = { f(1) } }                // suspend-lambda-type
fun p6() { runBlocking { f(1) } }                                        // runBlocking-block
fun p7() { Thread { f(1) } }                                             // Thread-lambda
suspend fun p8() { listOf(1).asSequence().map { f(it) }.toList() }       // Sequence-map-lambda
fun p9() { p2() }                                                        // plain-calls-suspend-fun
```

```python
# grid52.py
import os
import re
import subprocess

SRC = "call52.kt"
CP = os.environ["CP52"]

probes = {}
for n, line in enumerate(open(SRC, encoding="utf-8"), 1):
    m = re.search(r"// (\S+)$", line.rstrip("\n"))
    if m:
        probes[n] = m.group(1)

run = subprocess.run(["kotlinc", "-cp", CP, SRC, "-d", "o52g"], capture_output=True, text=True)
first = {}
for line in (run.stdout + run.stderr).splitlines():
    m = re.match(r"call52\.kt:(\d+):\d+: error: (.*)$", line)
    if m:
        first.setdefault(int(m.group(1)), m.group(2))

print("\t".join(["probe", "compile"]))
blocked = 0
for n, name in probes.items():
    cell = "ok" if n not in first else "error: " + first[n]
    blocked += n in first
    print("\t".join([name, cell]))
print("exit %d" % run.returncode)
print("blocked probes: %d / %d" % (blocked, len(probes)))
```

- 각 탐침은 `ok` 인가 진단인가? 진단의 문구는 몇 종이고 각각 무엇인가? 마지막 줄의 `N / M` 은?

### 3. ★★ 10만 개와 100개 (예측)

```kotlin
// threads52.kt
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.yield
import java.util.concurrent.ConcurrentHashMap
import kotlin.concurrent.thread

fun main() {
    val before = Thread.activeCount()
    val ids = ConcurrentHashMap.newKeySet<Long>()
    var during = 0
    runBlocking {
        repeat(100_000) {
            launch {
                ids.add(Thread.currentThread().threadId())
                delay(100)
                ids.add(Thread.currentThread().threadId())
            }
        }
        yield()
        during = Thread.activeCount()
    }
    println("coroutines: 100000 launched and finished")
    println("coroutines: distinct thread ids seen = ${ids.size}")
    println("coroutines: activeCount before=$before during=$during after=${Thread.activeCount()}")

    val threads = List(100) { thread { Thread.sleep(500) } }
    val duringThreads = Thread.activeCount()
    threads.forEach { it.join() }
    println("threads: 100 started, activeCount during=$duringThreads after=${Thread.activeCount()}")
}
```

- 네 줄의 출력은 무엇인가?

### 4. ★★ 세 가지 쉬기 (예측)

```kotlin
// interleave52.kt
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.yield

fun trace(pause: suspend () -> Unit): String {
    val log = mutableListOf<String>()
    runBlocking {
        for (name in listOf("A", "B")) {
            launch {
                repeat(3) { i ->
                    log += "$name$i"
                    pause()
                }
            }
        }
    }
    return log.joinToString(" ")
}

fun main() {
    println("delay(10)        " + trace { delay(10) })
    println("Thread.sleep(10) " + trace { Thread.sleep(10) })
    println("yield()          " + trace { yield() })
}
```

- 세 줄의 출력은 무엇인가?

### 5. ★★★ 부른 순간 (예측)

```kotlin
// order52.kt
import kotlinx.coroutines.CoroutineStart
import kotlinx.coroutines.delay
import kotlinx.coroutines.joinAll
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking

val log = mutableListOf<String>()

suspend fun work(tag: String): Int {
    log += "$tag: body starts"
    delay(1)
    log += "$tag: after delay"
    return 1
}

fun main() {
    runBlocking {
        log += "1 before the call"
        work("call")
        log += "2 after the call"
        val j = launch { work("launch") }
        log += "3 after launch { }"
        val u = launch(start = CoroutineStart.UNDISPATCHED) { work("undispatched") }
        log += "4 after launch(UNDISPATCHED) { }"
        joinAll(j, u)
        log += "5 after joinAll"
    }
    log.forEach(::println)
}
```

- 열한 줄은 어떤 순서로 찍히나?

### 6. ★★★ `await` 에서 잡은 뒤 (예측)

```kotlin
// await52.kt
import kotlinx.coroutines.Deferred
import kotlinx.coroutines.Job
import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.yield

fun main() = runBlocking {
    val log = mutableListOf<String>()
    try {
        coroutineScope {
            val other: Job = launch {
                repeat(3) { yield(); log += "other step $it" }
            }
            val d: Deferred<Int> = async {
                yield()
                throw IllegalStateException("boom")
            }
            try {
                d.await()
            } catch (e: IllegalStateException) {
                log += "caught at await: ${e.message}"
            }
            log += "after await: isActive=$isActive, other.isCancelled=${other.isCancelled}"
            yield()
            log += "after yield"
        }
    } catch (e: Exception) {
        log += "outside the scope: ${e::class.simpleName}: ${e.message}"
    }
    log.forEach(::println)
}
```

- 몇 줄이 찍히고 각각 무엇인가? `after yield` 는 찍히나?

### 7. 반환 타입이 `Object` 인 까닭 (왜)

- 1번의 `twice` 는 소스에서 `Int` 를 돌려주는데 JVM 서명은 `Object` 다. stdlib 의 어느 값이 그 자리에 올 수 있기 때문인가?

### 8. `runBlocking` 은 스레드를 막나 (경계)

```kotlin
// block52.kt
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlin.concurrent.thread

fun main() {
    val main = Thread.currentThread()
    var seen: Thread.State? = null
    val watcher = thread { Thread.sleep(150); seen = main.state }
    println("1 before runBlocking on ${Thread.currentThread().name}")
    runBlocking {
        launch { delay(300); println("3 child done on ${Thread.currentThread().name}") }
        println("2 inside runBlocking on ${Thread.currentThread().name}")
    }
    println("4 after runBlocking")
    watcher.join()
    println("5 main thread state seen by another thread at 150ms: $seen")
}
```

- 이 프로그램의 `5` 줄은 무엇을 확인하려는 것인가? `runBlocking` 은 어디에 두고 어디에 두지 말아야 하나?

### 9. 세 언어 — 부르기만 하면 무엇이 도나 (연결)

- [Python 51번](../../../python/syntax/51-asyncio-coroutine-basics/)의 코루틴 함수와 Kotlin 의 `suspend` 함수는 **부르기만 했을 때** 무엇이 다른가? 그리고 **부르는 쪽이 일반 함수일 때** 둘은 어떻게 갈리나?

### 10. 언어와 라이브러리의 경계 (경계)

- 이 주제에서 본 것 중 **컴파일러가 하는 것**과 **kotlinx-coroutines 가 하는 것**을 가르면? [`../../언어-특성/README.md`](../../언어-특성/README.md) §6 의 어느 문장이 그 경계를 말하나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
