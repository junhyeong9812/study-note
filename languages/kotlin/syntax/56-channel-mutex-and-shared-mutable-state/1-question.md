# kotlin/syntax/56 — `Channel`·`Mutex` — 공유 가변 상태 다루기 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [54번 주제](../54-coroutine-context-dispatchers-and-withcontext/)(디스패처 · `withContext`)와 [52번 주제](../52-coroutine-basics-suspend-scope-launch-async/)(`suspend` 호출 규칙)다.
> 문항 11개 중 예측형은 6개이고, 여섯 모두 코드블록이 붙는다.
> 이 주제의 모든 답은 **kotlinc 2.4.20 · Temurin JDK 21.0.5 · kotlinx-coroutines 1.11.0** 에서 실제로 던져 받은 것이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 방법 여섯 × 20판 (예측)

```kotlin
// grid56.kt
import kotlinx.coroutines.*
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import java.util.concurrent.atomic.AtomicInteger

const val COROUTINES = 1000
const val STEPS = 100
const val ROUNDS = 20
val EXPECTED = COROUTINES * STEPS

var plain = 0
val monitor = Any()
val mutex = Mutex()
val atomic = AtomicInteger()

@OptIn(ExperimentalCoroutinesApi::class)
val single = Dispatchers.Default.limitedParallelism(1)

suspend fun spread(body: suspend () -> Unit) = coroutineScope {
    repeat(COROUTINES) { launch(Dispatchers.Default) { repeat(STEPS) { body() } } }
}

suspend fun viaNone(): Int { plain = 0; spread { plain++ }; return plain }
suspend fun viaSynchronized(): Int { plain = 0; spread { synchronized(monitor) { plain++ } }; return plain }
suspend fun viaMutex(): Int { plain = 0; spread { mutex.withLock { plain++ } }; return plain }
suspend fun viaAtomic(): Int { atomic.set(0); spread { atomic.incrementAndGet() }; return atomic.get() }
suspend fun viaConfinement(): Int { plain = 0; spread { withContext(single) { plain++ } }; return plain }
suspend fun viaActor(): Int = coroutineScope {
    val inbox = Channel<Unit>(Channel.UNLIMITED)
    val owner = async { var n = 0; for (m in inbox) n++; n }
    spread { inbox.send(Unit) }
    inbox.close()
    owner.await()
}

fun main() = runBlocking {
    val ways = listOf<Pair<String, suspend () -> Int>>(
        "none" to ::viaNone,
        "synchronized" to ::viaSynchronized,
        "Mutex.withLock" to ::viaMutex,
        "AtomicInteger" to ::viaAtomic,
        "confined to one thread" to ::viaConfinement,
        "Channel actor" to ::viaActor,
    )
    println("expected per round = $EXPECTED · rounds = $ROUNDS · dispatcher = Dispatchers.Default")
    println("way\tany round below expected?")
    var lost = 0
    for ((name, run) in ways) {
        var bad = 0
        repeat(ROUNDS) { if (run() != EXPECTED) bad++ }
        val row = "$name\t${bad > 0}"
        check(row.split('\t').size == 2)
        println(row)
        if (bad > 0) lost++
    }
    println("ways that lost updates in at least one round: $lost / ${ways.size}")
}
```

- 각 행의 참/거짓은 무엇인가? 마지막 줄의 `N / M` 은?

### 2. ★★★ `synchronized` 류 안에서 부르면 (예측)

```kotlin
// crit56.kt
import kotlinx.coroutines.*
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import java.util.concurrent.locks.ReentrantLock
import kotlin.concurrent.withLock as withJLock

val monitor = Any()
val mutex = Mutex()
val jlock = ReentrantLock()
suspend fun step() = delay(1)

suspend fun c1() { synchronized(monitor) { delay(1) } }                    // synchronized+delay
suspend fun c2() { synchronized(monitor) { yield() } }                     // synchronized+yield
suspend fun c3() { synchronized(monitor) { step() } }                      // synchronized+own-suspend-fun
suspend fun c4() { jlock.withJLock { delay(1) } }                          // ReentrantLock.withLock+delay
suspend fun c5() { jlock.lock(); delay(1); jlock.unlock() }                // lock()+delay+unlock()
suspend fun c6() { mutex.withLock { delay(1) } }                           // Mutex.withLock+delay
suspend fun c7() = coroutineScope { synchronized(monitor) { launch { delay(1) } } } // synchronized+launch
suspend fun c8() { synchronized(monitor) { Thread.sleep(1) } }             // synchronized+Thread.sleep
```

```python
# gridc56.py
import os
import re
import subprocess

SRC = "crit56.kt"
CP = os.environ["CP56"]

probes = {}
for n, line in enumerate(open(SRC, encoding="utf-8"), 1):
    m = re.search(r"// (\S+)$", line.rstrip("\n"))
    if m:
        probes[n] = m.group(1)

run = subprocess.run(["kotlinc", "-cp", CP, SRC, "-d", "o56c"], capture_output=True, text=True)
first = {}
for line in (run.stdout + run.stderr).splitlines():
    m = re.match(r"crit56\.kt:(\d+):\d+: error: (.*)$", line)
    if m:
        first.setdefault(int(m.group(1)), m.group(2))

print("\t".join(["probe", "compile"]))
blocked = 0
for n, name in probes.items():
    cell = "ok" if n not in first else "error: " + first[n]
    blocked += n in first
    row = "\t".join([name, cell])
    assert len(row.split("\t")) == 2
    print(row)
print("exit %d" % run.returncode)
print("blocked probes: %d / %d" % (blocked, len(probes)))
```

- 여덟 탐침 중 어느 것이 컴파일에서 막히나? 막힌 탐침의 진단 문구는 무엇인가?

### 3. ★★ 자물쇠를 기다리는 동안 풀 스레드는 (예측)

```kotlin
// block56.kt
import kotlinx.coroutines.*
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import java.util.concurrent.Executors

val monitor = Any()
val mutex = Mutex()

// 스레드 두 개짜리 풀. 이름이 고정이라 상태를 이름으로 읽는다.
fun pool(tag: String): Pair<ExecutorCoroutineDispatcher, List<Thread>> {
    val made = mutableListOf<Thread>()
    var i = 0
    val ex = Executors.newFixedThreadPool(2) { r -> Thread(r, "$tag-${++i}").also { made += it } }
    return ex.asCoroutineDispatcher() to made
}

suspend fun trial(title: String, holdAndWait: suspend () -> Unit, waitOnly: suspend () -> Unit) {
    val (d, threads) = pool(title)
    println("-- $title")
    val t0 = System.nanoTime()
    fun ms() = (System.nanoTime() - t0) / 1_000_000
    var holderDoneAt = -1L
    var thirdStartedAt = -1L
    coroutineScope {
        launch(d) { holdAndWait(); holderDoneAt = ms() }   // 첫째 — 잡고 300ms 쥔다
        delay(50)
        launch(d) { waitOnly() }                           // 둘째 — 같은 자물쇠를 기다린다
        delay(50)
        launch(d) { thirdStartedAt = ms() }                // 셋째 — 자물쇠와 무관한 일
        delay(50)
        val states = threads.sortedBy { it.name }.map { "${it.name}=${it.state}" }
        println("at ~150ms pool threads: $states")
    }
    println("third started before holder finished: ${thirdStartedAt < holderDoneAt}")
    d.close()
}

fun main() = runBlocking {
    trial("sync",
        { synchronized(monitor) { Thread.sleep(300) } },
        { synchronized(monitor) { } })
    trial("mutex",
        { mutex.withLock { delay(300) } },
        { mutex.withLock { } })
}
```

- 두 판 각각에서 150ms 쯤 풀 스레드 둘의 상태는 무엇이고, 마지막 줄은 `true` 인가 `false` 인가?

### 4. ★★★ 스레드가 주인인 자물쇠와 코루틴 둘 (예측)

```kotlin
// own56.kt
import kotlinx.coroutines.*
import kotlinx.coroutines.sync.Mutex
import java.util.concurrent.Executors
import java.util.concurrent.locks.ReentrantLock

fun log(s: String) = println(s)

fun main() {
    val poolA = Executors.newSingleThreadExecutor { Thread(it, "thread-A") }
    val poolB = Executors.newSingleThreadExecutor { Thread(it, "thread-B") }
    val one = poolA.asCoroutineDispatcher()
    val other = poolB.asCoroutineDispatcher()

    runBlocking {
        log("-- 1 ReentrantLock, two coroutines, one thread")
        val jlock = ReentrantLock()
        val inside = mutableListOf<String>()
        coroutineScope {
            for (name in listOf("x", "y")) launch(one) {
                jlock.lock()
                inside += name
                log("$name holds the lock · inside now = $inside · holdCount = ${jlock.holdCount}")
                delay(50)
                inside -= name
                jlock.unlock()
            }
        }

        log("-- 2 Mutex, two coroutines, one thread")
        val mutex = Mutex()
        coroutineScope {
            for (name in listOf("x", "y")) launch(one) {
                mutex.lock()
                inside += name
                log("$name holds the lock · inside now = $inside")
                delay(50)
                inside -= name
                mutex.unlock()
            }
        }

        log("-- 3 ReentrantLock locked on one thread, unlocked after moving")
        try {
            withContext(one) {
                jlock.lock()
                log("locked on ${Thread.currentThread().name}")
                withContext(other) {
                    log("unlocking on ${Thread.currentThread().name}")
                    jlock.unlock()
                }
            }
        } catch (e: Exception) {
            log("caught: $e")
        }
    }
    poolA.shutdown(); poolB.shutdown()
}
```

- 세 구간에서 각각 무엇이 찍히나? 구간 1 의 `inside now` 와 `holdCount` 는? 구간 3 은 어떻게 끝나나?

### 5. ★★ 안쪽에서 한 번 더 잡으면 (예측)

```kotlin
// nest56.kt
import kotlinx.coroutines.*
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock

val monitor = Any()

fun main() = runBlocking {
    println("-- A synchronized inside synchronized")
    synchronized(monitor) { synchronized(monitor) { println("inner block ran") } }

    println("-- B Mutex.withLock inside Mutex.withLock")
    val m = Mutex()
    try {
        withTimeout(500) {
            m.withLock {
                println("outer holds · isLocked = ${m.isLocked}")
                m.withLock { println("inner block ran") }
            }
        }
    } catch (e: TimeoutCancellationException) {
        println("caught: $e")
    }
    println("after B · isLocked = ${m.isLocked}")

    println("-- C lock(owner) twice with the same owner")
    val m2 = Mutex()
    m2.lock("job-1")
    try {
        m2.lock("job-1")
        println("second lock returned")
    } catch (e: IllegalStateException) {
        println("caught: $e")
    }
    println("holdsLock(job-1) = ${m2.holdsLock("job-1")}")
}
```

- `A`·`B`·`C` 에서 각각 무엇이 찍히나? `after B` 의 `isLocked` 는?

### 6. ★★ 용량 일곱 가지 (예측)

```kotlin
// chan56.kt
import kotlinx.coroutines.*
import kotlinx.coroutines.channels.BufferOverflow
import kotlinx.coroutines.channels.Channel

const val ITEMS = 5

fun main() = runBlocking {
    val kinds = listOf<Pair<String, () -> Channel<Int>>>(
        "Channel()" to { Channel() },
        "Channel(RENDEZVOUS)" to { Channel(Channel.RENDEZVOUS) },
        "Channel(2)" to { Channel(2) },
        "Channel(BUFFERED)" to { Channel(Channel.BUFFERED) },
        "Channel(UNLIMITED)" to { Channel(Channel.UNLIMITED) },
        "Channel(CONFLATED)" to { Channel(Channel.CONFLATED) },
        "Channel(2, DROP_OLDEST)" to { Channel(2, BufferOverflow.DROP_OLDEST) },
    )
    println("channel\tsends finished before any receive\tsender still active?\treceived")
    for ((name, make) in kinds) {
        val ch = make()
        var sent = 0
        val sender = launch { repeat(ITEMS) { ch.send(it + 1); sent++ }; ch.close() }
        repeat(10) { yield() }          // 받는 쪽 없이 보내는 쪽에게 걸음을 준다
        val before = sent
        val active = sender.isActive
        val got = mutableListOf<Int>()
        for (x in ch) got += x
        val row = "$name\t$before\t$active\t$got"
        check(row.split('\t').size == 4)
        println(row)
    }
    val big = Channel<Int>(Channel.BUFFERED)
    var bigSent = 0
    val bigSender = launch { repeat(70) { big.send(it); bigSent++ }; big.close() }
    repeat(200) { yield() }
    println("Channel(BUFFERED) with 70 items: sends finished before any receive = $bigSent")
    var drained = 0
    for (x in big) drained++
    bigSender.join()
    println("received after draining = $drained")
}
```

- 각 행의 둘째·셋째·넷째 칸은 무엇인가? 끝의 두 줄은?

### 7. 컴파일러가 `synchronized` 안의 중단점을 막는 까닭 (왜)

- 2번의 진단이 막으려는 사고는 무엇인가? 4번의 어느 구간이 그 사고를 보여 주나?

### 8. 컴파일러가 보는 것 (경계)

- 2번의 여덟 탐침 가운데 컴파일러의 판정과 실제 위험이 어긋나는 것이 있나? 있다면 왜 어긋나나 — 검사기는 무엇을 알아보나?

### 9. 닫은 채널 (경계)

- `Channel(BUFFERED)` 에 둘을 보내고 `close()` 한 뒤 `send` · `trySend` · `receive` 두 번 · 다시 `receive` · `receiveCatching` 은 각각 무엇을 하나?

### 10. 자물쇠 없이 지키는 두 방법 (왜)

- 1번의 「한 스레드 한정」과 「`Channel` 액터」는 자물쇠가 없는데 왜 값을 안 잃나? 액터의 채널 용량을 `CONFLATED` 로 바꾸면 무엇이 달라지나?

### 11. C# 의 `lock` 과 `await` · 가상 스레드 (연결)

- C# 은 `lock` 몸통 안의 `await` 를 어떻게 다루나? [Java 56번](../../../java/syntax/56-virtual-threads/)의 「`synchronized` 가 캐리어를 붙잡는다」와 3번은 어떻게 같은 모양인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
