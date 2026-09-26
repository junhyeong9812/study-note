# kotlin/syntax/56 — `Channel`·`Mutex` — 공유 가변 상태 다루기 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — **`kotlinx-coroutines-core-jvm` 1.11.0 의 소스 jar** — `commonMain/sync/Mutex.kt`(`Mutex` KDoc · `withLock`) · `commonMain/channels/Channel.kt`(용량 상수와 그 KDoc) · **kotlinc 2.4.20 의 `kotlin-compiler.jar`** 안의 검사기 클래스 하나(`javap`). ★ 공식 문서 페이지(「Shared mutable state and concurrency」·「Channels」)는 **이 작업에서 열지 못했다**(외부 네트워크를 쓰지 않았다) — 문장은 인용하지 않는다.
> **실행 검증** — 이 문서의 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `java`·`javap` 에서 실제로 얻었다.\
> `kotlinc` 9회(진단 격자 스크립트 안의 1회 포함) · `java` 7회 + 격자와 스레드 상태 로그를 세 판씩 되풀이한 6회 · `javap` 1회(검사기) · 라이브러리 소스 jar 발췌 2곳 · C# `csc` 1회(.NET SDK 10.0.401).\
> ★★★ **라이브러리 판 — `kotlinx-coroutines-core-jvm` 1.11.0**(이 머신의 gradle 캐시에 있던 판 중 가장 새 것 · 매니페스트 `Implementation-Version: 1.11.0`). `Mutex`·`Channel`·`withTimeout`·`limitedParallelism` 은 **이 라이브러리의 것**이다 — 언어가 아니다.\
> ★★ 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적지 않았다. **「잃은 칸 N / M」·「막힌 탐침 N / M」은 프로그램이 스스로 센 것**이다.
> **버전** — `synchronized` 안의 중단점을 막는 진단이 **어느 판부터인지는 확인하지 못했다**(옛 컴파일러 판이 이 머신에 없다). `Mutex`·`Channel` 도 **1.11.0 한 판에서만** 쟀다.
> **경계** — ★★★ 「코루틴은 스레드가 아니라 컴파일러 변환이다」라는 **논지**는 [`../../언어-특성/README.md`](../../언어-특성/README.md) §6 이 정본이다. `suspend` 함수를 **어디서 부를 수 있나**는 [52번 주제](../52-coroutine-basics-suspend-scope-launch-async/), 취소·예외가 부모와 형제로 번지는 규칙은 [53번 주제](../53-structured-concurrency-job-cancellation-exceptions/), 디스패처와 `limitedParallelism` 자체는 [54번 주제](../54-coroutine-context-dispatchers-and-withcontext/)가 정본이다 — 여기서는 **공유 상태를 지키는 수단의 선택**만 본다.\
> 스레드 쪽 원리 — **`int++` 이 왜 깨지나 · `synchronized` 의 재진입**은 [Java 33번](../../../java/syntax/33-synchronized-and-volatile/)이, **`AtomicInteger`** 는 [Java 55번](../../../java/syntax/55-atomics-and-concurrent-collections/)이, **`synchronized` 가 가상 스레드를 캐리어에 묶는 것(JDK 21)** 은 [Java 56번](../../../java/syntax/56-virtual-threads/)이 정본이다. **Go 의 채널과 뮤텍스**는 [Go 29번](../../../go/syntax/29-channels-buffering-direction-close-range-and-nil/)·[Go 32번](../../../go/syntax/32-sync-mutex-rwmutex-waitgroup-once/)이 쟀다.
> 이 본문은 Claude 작성이다(원고 없음).

★★★ **본체는 첫째 창이다** — 「**공유 상태 격자 — 카운터 `plain++` 을 코루틴 1000개 × 100번 × 방법 여섯 × `Dispatchers.Default` × 20판 → 한 판이라도 잃었나**」. 둘째 본체는 **중단점 진단 격자**(`synchronized` 안에서 무엇을 부르면 컴파일이 막히나)다. 「쓰면 안 되는 이유」는 **컴파일러 진단 + 스레드 상태 로그 + 소유 로그** 세 창으로 말한다 — 느리다·빠르다는 재지 않았다.

## 이 주제가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **언어(컴파일러 진단)** | kotlinc 가 거부하는 것 | ★★★ **`synchronized { }` 와 `kotlin.concurrent.withLock { }` 안의 중단점은 컴파일 에러** — 「`the 'delay' suspension point is inside a critical section.`」 · 검사기가 그 두 함수를 **이름으로** 알아본다(`javap`) |
| **라이브러리 계약(kotlinx-coroutines)** | 라이브러리 KDoc 이 약속한 것 | `Mutex` 는 「`non-reentrant`」·「`fair`」 · `Channel` 용량 상수(`RENDEZVOUS = 0` · `CONFLATED = -1` · `BUFFERED = -2` · `UNLIMITED = Int.MAX_VALUE`)와 그 동작 · 기본 버퍼 64 — ★ **언어가 아니다** |
| **이 판의 관찰** | 이 머신·이 판에서 이번에 본 것 | 격자의 참/거짓 · 스레드 상태(`BLOCKED`·`WAITING`) · 로그 순서 · 예외 메시지 |

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

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다 — 칸으로 안 만들었다** | ★★ 보호 없음 칸의 **최종 값 · 잃은 판 수** | 판마다 다르다 — 그래서 격자는 **「한 판이라도 기대값 아래였나」** 불리언만 찍는다 |
| ★ **머신에 매인다** | 보호 없음 칸이 `true` 인 것 자체 | ★★ **관찰이다** — 24코어 머신에서 20판 중 한 판이라도 잃었다는 것. 세 판 되풀이(해시 1가지)에서 같았지만 **잃지 않는 머신이 있어도 「안전하다」가 되지 않는다**(규칙 3) |
| 안 흔들린다 | 보호 다섯 칸의 `false` · `1 / 6` | 보호가 맞으면 **판마다 정확히** 100000 이다 |
| 안 흔들린다 | ★ 스레드 상태 로그(`block56`) | 50ms 간격으로 걸음을 뗐다 — 쥐는 쪽이 300ms 를 쥐므로 **여유가 100ms 이상**. 세 판 되풀이에서 해시 1가지 |
| 안 흔들린다 | 소유 로그 · 재진입 로그 · 채널 격자 · 닫기 로그 | **단일 스레드**(`runBlocking` · 단일 스레드 풀) 위에서 `yield()`·`delay` 로 걸음을 맞췄다 |
| 안 흔들린다 | 진단 격자 · 진단 전문 · 검사기 `javap` · 소스 발췌 · C# 진단 | 같은 판이면 같다 |
| ★ **판에 매인다** | 라이브러리 **1.11.0** 의 동작 전부 · 예외 메시지 문구 | 판이 바뀌면 다시 돌려라 |

★ 근거 — 캡처 스크립트를 처음부터 두 번 돌려 **블록 전체를 대조**했다(수치는 3-answer 의 「실행 검증」).

## 한눈에 — 쉽게 말하면

**`synchronized` 는 「사람(스레드)에게 채우는 수갑」이고 `Mutex` 는 「일감(코루틴)에게 주는 번호표」다.** 수갑을 찬 사람은 자물쇠가 풀릴 때까지 **아무 일도 못 하고 서 있다**(스레드가 막힌다). 번호표를 받은 일감은 **옆으로 치워지고, 사람은 다른 일감을 집는다**(코루틴만 멈춘다).
★ 그리고 코루틴은 **중간에 사람을 갈아탈 수 있다** — 수갑은 사람에게 채워졌는데 일감이 다른 사람 손으로 넘어가면, **풀 수 있는 사람이 없다.** 그래서 컴파일러가 `synchronized` 안에서 **일감을 내려놓는 동작**(중단점)을 막는다.

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 사람에게 채우는 수갑 | `synchronized` · `ReentrantLock` — **스레드**가 주인 | (3)(4) ★ |
| 기다리는 사람이 서 있다 | 기다리는 스레드가 `BLOCKED` · 다른 일을 못 받는다 | (3) ★ |
| 일감에게 주는 번호표 | `Mutex` — **코루틴**이 기다리고 스레드는 논다(`WAITING`) | (3) ★ |
| 같은 사람이면 수갑이 또 들어간다 | `ReentrantLock` 은 같은 스레드의 두 코루틴을 **둘 다** 들인다 | (4) ★ |
| 수갑 찬 채 사람을 갈아탄다 | 다른 스레드에서 `unlock()` → `IllegalMonitorStateException` | (4) ★ |
| 번호표는 같은 일감에게도 두 장 안 준다 | `Mutex` 는 재진입 불가 — 안에서 다시 잡으면 영원히 기다린다 | (5) |
| 한 사람만 만지게 한다 | 한 스레드 한정 · `Channel` 로 액터 — 자물쇠가 없다 | (1)(7) |
| 우편함 크기 | `Channel` 용량 — 0 이면 손에서 손으로, 차면 보내는 쪽이 멈춘다 | (6) |

```text
   synchronized 로 기다리면                      Mutex 로 기다리면

   스레드1  [첫째: 쥐고 300ms 잠]                스레드1  (놀고 있다)      ← 첫째는 delay 로 스레드를 놓았다
   스레드2  [둘째: 들어가려다 BLOCKED]           스레드2  (놀고 있다)      ← 둘째는 코루틴만 멈췄다
   셋째     줄을 서서 못 돈다                    셋째     빈 스레드에서 바로 돈다
```

## 이 주제가 답하려는 질문

1. 여러 코루틴이 한 변수를 고칠 때 **무엇이 값을 잃고 무엇이 안 잃나** — 자물쇠 둘 · 원자 변수 · 한 스레드 한정 · 액터.
2. **코루틴에서 `synchronized` 를 쓰면 안 되는 이유**는 무엇인가 — 컴파일러가 무엇을 막고, 무엇을 못 막나.
3. `Channel` 의 **용량은 보내는 쪽을 언제 멈추게 하나** — 닫은 뒤에는 무엇이 나오나.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **공유 상태 격자(실행)** | 방법 여섯 × 20판 → 한 판이라도 잃었나((1)) | ★ **본체 창** |
| ★★★ **중단점 진단 격자(컴파일)** | `synchronized` 류 안에서 부른 것 여덟 가지 → 막히나((2)) | ★ **둘째 본체** — 언어 층 |
| ★★ **컴파일러 jar `javap`** | 검사기가 **무엇을 알아보나** — 함수 이름 두 개((2)) | kt46b 의 컴파일러 jar 창과 같은 방식 |
| ★★ **스레드 상태 로그** | 기다리는 동안 풀 스레드가 `BLOCKED` 인가 `WAITING` 인가((3)) | — |
| ★★ **소유 로그** | 스레드가 주인인 자물쇠를 코루틴 둘이 잡으면 · 스레드를 갈아타 풀면((4)) | — |
| ★ **재진입 로그** | `synchronized` 안의 `synchronized` · `Mutex` 안의 `Mutex`((5)) | — |
| ★★ **채널 용량 격자** | 용량 일곱 가지 → 받기 전에 끝난 보내기 수 · 받은 것((6)) | — |
| ★ **라이브러리 소스 jar 발췌** | `Mutex` KDoc · 용량 상수((5)(6)) | — |
| ★ **교차 갈래 — C# `csc`** | `lock` 안의 `await` 를 C# 은 어떻게 막나((2)) | C# 갈래에 이 주제 폴더가 없어 **직접 던졌다** |
| ★ **제5의 상태 — 창을 바꿔 물었다** | 「교착했나」를 교착 감지기가 아니라 **`withTimeout(500)` 이 끝났나**로 물었다((5)) | 이 창은 「500ms 안에 안 풀렸다」만 본다 — **영원히 안 풀리는지**는 KDoc 이 말한다 |
| **부적용 — 실행 시간** | ★★★ 「`Mutex` 가 `synchronized` 보다 느리다/빠르다」는 **재지 않았다** — 이 문서의 비교는 **값을 잃었나 · 스레드가 막혔나**뿐이다 | — |

### (1) ★★★ 공유 상태 격자 — 무엇이 값을 잃나

**언제 쓰나** — 코루틴 여럿이 한 카운터·맵·잔액을 고칠 때, 수단을 고르기 전에.

방법 — 코루틴 1000개를 `Dispatchers.Default` 에 띄우고 각각 100번 더한다(기대값 100000). 방법마다 20판을 돌려 **기대값보다 작은 판이 하나라도 있었나**만 찍는다. 최종 값은 **찍지 않는다** — 잃는 쪽은 판마다 수가 달라 근거가 못 된다. 마지막 줄은 한 판이라도 잃은 방법의 수다.

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

```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar grid56.kt -d o56g =====
(exit 0)
===== java -cp o56g:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Grid56Kt 2>/dev/null =====
expected per round = 100000 · rounds = 20 · dispatcher = Dispatchers.Default
way	any round below expected?
none	true
synchronized	false
Mutex.withLock	false
AtomicInteger	false
confined to one thread	false
Channel actor	false
ways that lost updates in at least one round: 1 / 6
(exit 0)
```

```text
===== for i in 1 2 3; do java -cp o56g:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Grid56Kt | md5sum; done | sort | uniq -c =====
      3 9390405aebdb04fa0ea8ff86095a7719  -
(exit 0)
```

- ★★★ **잃은 칸 1 / 6 — 보호 없음 하나뿐이다.** `plain++` 은 읽기·더하기·쓰기 셋이고, `Default` 는 **스레드 여럿**이라 두 코루틴이 같은 값을 읽고 같은 값을 쓴다([Java 33번](../../../java/syntax/33-synchronized-and-volatile/) (2)가 바이트코드로 쪼갰다).
- ★★★ **`synchronized` 도 값을 안 잃었다** — 이 격자에서 `synchronized` 는 **틀리지 않는다.** 자물쇠 안에 **중단점이 없기** 때문이다(`plain++` 한 줄). 「쓰면 안 된다」의 이유는 **값이 아니라** (2)(3)(4)에 있다.
- ★★ **한 스레드 한정**(`limitedParallelism(1)` 로 `withContext`)과 **`Channel` 액터**는 자물쇠가 **없다** — 변수를 만지는 쪽이 **한 번에 하나**라서 경쟁 자체가 없다. 액터는 변수를 **한 코루틴의 지역 변수**로 가둔다.
- ★★ 되풀이 블록 — 격자 프로그램을 세 번 더 돌려 출력 전체의 해시를 센 것이다. **해시가 1가지**다(세 판 모두 같은 표).
- ★ **「`false`」는 「20판에서 한 번도 안 잃었다」이지 「안 잃는다」의 증명이 아니다** — 증명은 자물쇠·원자 연산의 **계약**이 한다. 반대로 보호 없음이 이 머신에서 한 판도 안 잃었더라도 **안전하다는 뜻이 아니다**(규칙 3).

### (2) ★★★ `synchronized` 안의 중단점 — 컴파일러가 막는 것과 못 막는 것

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

```text
===== CP56=kotlinx-coroutines-core-jvm-1.11.0.jar python3 gridc56.py =====
probe	compile
synchronized+delay	error: the 'delay' suspension point is inside a critical section.
synchronized+yield	error: the 'yield' suspension point is inside a critical section.
synchronized+own-suspend-fun	error: the 'step' suspension point is inside a critical section.
ReentrantLock.withLock+delay	error: the 'delay' suspension point is inside a critical section.
lock()+delay+unlock()	ok
Mutex.withLock+delay	ok
synchronized+launch	ok
synchronized+Thread.sleep	ok
exit 1
blocked probes: 4 / 8
(exit 0)
```

```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar crit56.kt -d o56c2 =====
crit56.kt:12:44: error: the 'delay' suspension point is inside a critical section.
suspend fun c1() { synchronized(monitor) { delay(1) } }                    // synchronized+delay
                                           ^^^^^
crit56.kt:13:44: error: the 'yield' suspension point is inside a critical section.
suspend fun c2() { synchronized(monitor) { yield() } }                     // synchronized+yield
                                           ^^^^^
crit56.kt:14:44: error: the 'step' suspension point is inside a critical section.
suspend fun c3() { synchronized(monitor) { step() } }                      // synchronized+own-suspend-fun
                                           ^^^^
crit56.kt:15:38: error: the 'delay' suspension point is inside a critical section.
suspend fun c4() { jlock.withJLock { delay(1) } }                          // ReentrantLock.withLock+delay
                                     ^^^^^
(exit 1)
```

- ★★★ **막힌 탐침 4 / 8 · 진단은 한 종이다** — 「`the 'delay' suspension point is inside a critical section.`」. 이름 자리에 **부른 함수가 그대로** 들어간다(`'yield'`·`'step'`). **직접 만든 `suspend fun step()` 도 막힌다** — 라이브러리 함수만의 특별 대우가 아니라 **중단점이면 전부**다.
- ★★★ **`kotlin.concurrent.withLock`(`ReentrantLock`)도 막힌다** — `synchronized` 만이 아니다. 그런데 **같은 자물쇠를 `lock()` … `unlock()` 으로 풀어 쓰면 통과한다**(`lock()+delay+unlock()` · `ok`). 컴파일러가 보는 것은 **자물쇠가 아니라 함수 이름**이다 — 아래 `javap`.
- ★★ **`Mutex.withLock { delay }` 는 된다** — 기다림이 **중단**이라 자물쇠를 쥔 채 스레드를 놓아도 되는 자물쇠다((3)).
- ★★ **`synchronized` 안의 `launch { delay }` 는 된다** — `launch` 의 람다는 **따로 도는 새 코루틴**이라 그 중단점은 자물쇠 밖이다. **`synchronized` 안의 `Thread.sleep` 도 된다** — 중단점이 아니라 **스레드를 재우는 일반 호출**이다. 둘 다 컴파일러가 **말하지 않는** 자리다.

```text
===== unzip -o -q "$KOTLIN_HOME/lib/kotlin-compiler.jar" 'org/jetbrains/kotlin/fir/analysis/jvm/checkers/expression/FirJvmSuspensionPointInsideMutexLockChecker.class' -d kc56 =====
(exit 0)
===== javap -c -p -cp kc56 org.jetbrains.kotlin.fir.analysis.jvm.checkers.expression.FirJvmSuspensionPointInsideMutexLockChecker | grep -E '^public|// String (kotlin|synchronized|kotlin\.concurrent|withLock)$' =====
public final class org.jetbrains.kotlin.fir.analysis.jvm.checkers.expression.FirJvmSuspensionPointInsideMutexLockChecker extends org.jetbrains.kotlin.fir.analysis.checkers.expression.FirExpressionChecker<org.jetbrains.kotlin.fir.expressions.FirFunctionCall> {
      18: ldc           #10                 // String kotlin
      23: ldc           #13                 // String synchronized
      48: ldc           #11                 // String kotlin.concurrent
      53: ldc           #14                 // String withLock
(exit 0)
```

- ★★★ **검사기 이름이 `SuspensionPointInsideMutexLockChecker` 이고, 상수 풀에 `kotlin` + `synchronized` · `kotlin.concurrent` + `withLock` 네 문자열이 있다** — 패키지와 함수 이름의 짝 둘을 알아보는 검사다. 그래서 `lock()`/`unlock()` 을 직접 부르는 코드는 **검사 대상이 아니다.** ★ 이것은 **이 판 컴파일러의 구현**이다 — 「이름 두 개만 본다」를 언어 명세로 읽지 마라.

**C# 은 같은 자리를 어떻게 막나**

```csharp
// lock56.cs
using System.Threading.Tasks;

class Lock56
{
    static readonly object Gate = new object();

    static async Task Main()
    {
        lock (Gate)
        {
            await Task.Delay(1);
        }
    }
}
```

```text
===== "$DOTNET_ROOT/dotnet" --version =====
10.0.401
(exit 0)
===== csc -out:lock56.exe lock56.cs =====
lock56.cs(11,13): error CS1996: Cannot await in the body of a lock statement
(exit 1)
```

- ★★ **C# 도 `lock` 몸통 안의 `await` 를 컴파일 에러로 막는다** — `CS1996`「`Cannot await in the body of a lock statement`」. 이유가 같다 — `lock`(`Monitor`)은 **스레드가 주인**인데 `await` 뒤에는 **다른 스레드에서 이어질 수 있다.** 두 언어가 **같은 모양의 구멍을 같은 자리(컴파일)에서** 막았다.
- ★ C# 쪽 주제 폴더는 아직 없다 — C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **40번**(`async`/`await`)이 서면 이 대비를 거기서 잇는다.

### (3) ★★ 기다리는 동안 스레드는 — `synchronized` 는 막고 `Mutex` 는 놓는다

**언제 쓰나** — 자물쇠 안이 **길 때**(I/O·긴 계산) 무엇이 같이 멈추는지 가늠할 때.

방법 — **스레드 두 개짜리 풀**에서 첫째가 자물쇠를 잡고 300ms 쥔다(`synchronized` 판은 `Thread.sleep` · `Mutex` 판은 `delay`). 50ms 뒤 둘째가 같은 자물쇠를 기다리고, 다시 50ms 뒤 **자물쇠와 무관한** 셋째를 띄운다. 150ms 쯤에 풀 스레드 둘의 상태를 찍는다.

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

```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar block56.kt -d o56b =====
(exit 0)
===== java -cp o56b:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Block56Kt 2>/dev/null =====
-- sync
at ~150ms pool threads: [sync-1=TIMED_WAITING, sync-2=BLOCKED]
third started before holder finished: false
-- mutex
at ~150ms pool threads: [mutex-1=WAITING, mutex-2=WAITING]
third started before holder finished: true
(exit 0)
```

```text
===== for i in 1 2 3; do java -cp o56b:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Block56Kt | md5sum; done | sort | uniq -c =====
      3 909ea04141b240e8741ef74122ad4784  -
(exit 0)
```

- ★★★ **`synchronized` 판 — `sync-2=BLOCKED`** — 둘째가 **스레드째** 자물쇠 앞에 서 있다. 첫째(`sync-1`)는 `TIMED_WAITING`(잠). 풀의 스레드 **둘 다** 묶였으니 셋째는 **첫째가 끝날 때까지 시작도 못 했다**(`false`).
- ★★★ **`Mutex` 판 — 두 스레드 다 `WAITING`**(풀에서 일감을 기다리며 논다) — 첫째는 `delay` 로, 둘째는 `lock` 에서 **코루틴만** 멈췄다. 셋째는 빈 스레드에서 **바로** 돌았다(`true`).
- ★★ 이것이 「`synchronized` 를 쓰면 안 되는」 둘째 이유다 — 값은 안 잃어도(1) **디스패처의 스레드를 먹는다.** 디스패처의 스레드는 유한하므로 **기다리는 코루틴 수만큼 쓸 수 있는 스레드가 준다**(디스패처마다 스레드가 몇 개인지는 [54번 주제](../54-coroutine-context-dispatchers-and-withcontext/)).
- ★ 같은 모양이 가상 스레드에도 있다 — JDK 21 에서 `synchronized` 안의 블로킹이 **캐리어를 붙잡는다**([Java 56번](../../../java/syntax/56-virtual-threads/)). 위 블록은 가상 스레드가 아니라 **플랫폼 스레드 풀**에서 돌렸다(JDK 21.0.5).

### (4) ★★★ 주인이 스레드인 자물쇠 — 코루틴 둘을 못 가르고, 갈아타면 못 푼다

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

```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar own56.kt -d o56o =====
(exit 0)
===== java -cp o56o:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Own56Kt 2>/dev/null =====
-- 1 ReentrantLock, two coroutines, one thread
x holds the lock · inside now = [x] · holdCount = 1
y holds the lock · inside now = [x, y] · holdCount = 2
-- 2 Mutex, two coroutines, one thread
x holds the lock · inside now = [x]
y holds the lock · inside now = [y]
-- 3 ReentrantLock locked on one thread, unlocked after moving
locked on thread-A
unlocking on thread-B
caught: java.lang.IllegalMonitorStateException
(exit 0)
```

- ★★★ **구간 1 — `ReentrantLock` 이 코루틴 둘을 동시에 들였다**(`inside now = [x, y]` · `holdCount = 2`). 스레드 하나(`thread-A`)에서 도는 두 코루틴은 자물쇠가 보기에 **같은 주인**이다 — 재진입으로 받아 준다. **상호 배제가 깨졌는데 예외도 경고도 없다.** (2)에서 `lock()`/`unlock()` 을 풀어 쓴 탐침이 **통과한 것**이 바로 이 코드다.
- ★★★ **구간 2 — `Mutex` 는 같은 스레드여도 하나만 들인다**(`[x]` 뒤 `[y]`) — 주인이 **스레드가 아니다.**
- ★★★ **구간 3 — 한 스레드에서 잡고 다른 스레드로 옮겨 풀면 `java.lang.IllegalMonitorStateException`** — `withContext(other)` 가 코루틴을 `thread-B` 로 옮겼고, `thread-B` 는 그 자물쇠의 주인이 아니다. `Default` 처럼 스레드가 여럿인 디스패처에서는 **`delay` 뒤에 다른 스레드에서 이어지는 것이 보통**이다 — 이 구간은 그것을 결정적으로 만든 판이다.
- ★★ 그래서 컴파일러가 막는 이유는 「느려서」가 아니라 「**의미가 깨져서**」이다 — 스레드를 주인으로 삼는 자물쇠와, 스레드를 갈아타는 코루틴은 **한 구간 안에서 섞이면 안 된다.** 컴파일러는 그 섞임을 `synchronized`·`withLock` 두 이름에서만 잡는다((2)).

### (5) ★ 안에서 한 번 더 잡으면 — 재진입

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

```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar nest56.kt -d o56n =====
(exit 0)
===== java -cp o56n:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Nest56Kt 2>/dev/null =====
-- A synchronized inside synchronized
inner block ran
-- B Mutex.withLock inside Mutex.withLock
outer holds · isLocked = true
caught: kotlinx.coroutines.TimeoutCancellationException: Timed out waiting for 500 ms
after B · isLocked = false
-- C lock(owner) twice with the same owner
caught: java.lang.IllegalStateException: This mutex is already locked by the specified owner: job-1
holdsLock(job-1) = true
(exit 0)
```

```text
===== unzip -o -q kotlinx-coroutines-core-jvm-1.11.0-sources.jar commonMain/sync/Mutex.kt commonMain/channels/Channel.kt =====
(exit 0)
```

```text
===== sed -n '11,16p;100p;117,127p' commonMain/sync/Mutex.kt =====
/**
 * Mutual exclusion for coroutines.
 *
 * Mutex has two states: _locked_ and _unlocked_.
 * It is **non-reentrant**, that is invoking [lock] even from the same thread/coroutine that currently holds
 * the lock still suspends the invoker.
 * The mutex created is fair: lock is granted in first come, first served order.
public suspend inline fun <T> Mutex.withLock(owner: Any? = null, action: () -> T): T {
    contract {
        callsInPlace(action, InvocationKind.EXACTLY_ONCE)
    }
    lock(owner)
    return try {
        action()
    } finally {
        unlock(owner)
    }
}
(exit 0)
```

- ★★★ **`synchronized` 안의 `synchronized` 는 들어간다**(`inner block ran`) — 같은 스레드는 자기 모니터에 **다시 들어간다**([Java 33번](../../../java/syntax/33-synchronized-and-volatile/) (6)).
- ★★★ **`Mutex.withLock` 안의 `withLock` 은 영원히 기다린다** — 안쪽 줄이 **안 찍히고** `withTimeout(500)` 이 `TimeoutCancellationException: Timed out waiting for 500 ms` 로 끊었다. KDoc 「`It is **non-reentrant**, that is invoking [lock] even from the same thread/coroutine that currently holds the lock still suspends the invoker.`」 — **라이브러리 계약**이다.
- ★★ 끊긴 뒤 `isLocked = false` — 취소가 바깥 `withLock` 의 `finally { unlock(owner) }` 를 지나 자물쇠를 **풀었다**(발췌의 `withLock` 몸통). 타임아웃이 없었으면 **이 코루틴과, 이 자물쇠를 기다리는 모든 코루틴이** 멈춘 채 남는다.
- ★★ **`owner` 를 주면 교착 대신 예외** — 같은 `owner` 로 두 번 `lock` 하면 `IllegalStateException: This mutex is already locked by the specified owner: job-1`. KDoc 은 `owner` 를 「`Optional owner token for debugging`」이라 부른다 — **디버깅용 표지**다.
- ★ `fair` — 「`lock is granted in first come, first served order`」. 기다린 순서대로 받는다(이 문서는 순서를 **재지 않았다**).

### (6) ★★ `Channel` 용량 — 보내는 쪽은 언제 멈추나

방법 — `runBlocking` 스레드 하나에서, 보내는 코루틴이 1\~5 를 보내고 닫는다. 받는 쪽은 **`yield()` 열 번** 동안 아무것도 안 받은 뒤 그때까지 끝난 `send` 수와 보내는 쪽이 아직 살아 있나를 찍고, 그다음 전부 받는다.

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

```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar chan56.kt -d o56h =====
(exit 0)
===== java -cp o56h:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Chan56Kt 2>/dev/null =====
channel	sends finished before any receive	sender still active?	received
Channel()	0	true	[1, 2, 3, 4, 5]
Channel(RENDEZVOUS)	0	true	[1, 2, 3, 4, 5]
Channel(2)	2	true	[1, 2, 3, 4, 5]
Channel(BUFFERED)	5	false	[1, 2, 3, 4, 5]
Channel(UNLIMITED)	5	false	[1, 2, 3, 4, 5]
Channel(CONFLATED)	5	false	[5]
Channel(2, DROP_OLDEST)	5	false	[4, 5]
Channel(BUFFERED) with 70 items: sends finished before any receive = 64
received after draining = 70
(exit 0)
```

```text
===== sed -n '1178,1185p;1189p;1299p;1333p;1359p;1365,1366p;1391p;1409p' commonMain/channels/Channel.kt =====
 * - [Channel.RENDEZVOUS] (or 0) creates a _rendezvous_ channel, which does not have a buffer at all.
 *   Instead, the sender and the receiver must rendezvous (meet):
 *   [SendChannel.send] suspends until another coroutine invokes [ReceiveChannel.receive], and vice versa.
 * - [Channel.CONFLATED] creates a buffer for a single element and automatically changes the
 *   [buffer overflow strategy][BufferOverflow] to [BufferOverflow.DROP_OLDEST].
 * - [Channel.UNLIMITED] creates a channel with an unlimited buffer, which never suspends the sender.
 * - [Channel.BUFFERED] creates a channel with a buffer whose size depends on
 *   the [buffer overflow strategy][BufferOverflow].
 * If the capacity is positive but less than [Channel.UNLIMITED], the channel has a buffer with the specified capacity.
        public const val UNLIMITED: Int = Int.MAX_VALUE
        public const val RENDEZVOUS: Int = 0
        public const val CONFLATED: Int = -1
         * For [BufferOverflow.SUSPEND] (the default buffer overflow strategy), the default capacity is 64,
         * but on the JVM it can be overridden by setting the [DEFAULT_BUFFER_PROPERTY_NAME] system property.
        public const val BUFFERED: Int = -2
        public const val DEFAULT_BUFFER_PROPERTY_NAME: String = "kotlinx.coroutines.channels.defaultBuffer"
(exit 0)
```

- ★★★ **`Channel()` 과 `RENDEZVOUS` 는 받기 전에 끝난 `send` 가 0** — 버퍼가 없어 **첫 `send` 부터** 받는 쪽이 올 때까지 멈춘다(보내는 쪽이 `true` — 아직 살아 있다). 기본 생성자가 곧 `RENDEZVOUS` 다(두 행이 같다). KDoc 「`[SendChannel.send] suspends until another coroutine invokes [ReceiveChannel.receive]`」.
- ★★★ **`Channel(2)` 는 2 개까지 끝나고 멈춘다.** `BUFFERED` 는 5 개가 다 들어갔다 — **기본 버퍼가 64** 이기 때문이고(KDoc 「`the default capacity is 64`」), 70 개를 보내면 **64 에서 멈춘다**(블록 끝 두 줄).
- ★★ **`CONFLATED` 는 멈추지 않고 마지막 하나만 남긴다**(`[5]`) — 「`creates a buffer for a single element and automatically changes the [buffer overflow strategy] to [BufferOverflow.DROP_OLDEST]`」. `Channel(2, DROP_OLDEST)` 는 **마지막 둘**(`[4, 5]`)이다. **값을 조용히 버리는 용량**이다 — 카운터 액터에 쓰면 (1)의 보호 없음처럼 **수를 잃는다.**
- ★ 상수는 **특별한 음수**다 — `CONFLATED = -1` · `BUFFERED = -2`. 용량 칸에 `-1` 을 넣어도 크기 −1 짜리 버퍼가 아니다.

### (7) ★ 닫은 뒤 — `send` 는 던지고, 남은 것은 받힌다

```kotlin
// close56.kt
import kotlinx.coroutines.*
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.channels.ClosedReceiveChannelException
import kotlinx.coroutines.channels.ClosedSendChannelException

@OptIn(DelicateCoroutinesApi::class)
fun main() = runBlocking {
    val ch = Channel<Int>(Channel.BUFFERED)
    ch.send(1); ch.send(2)
    ch.close()
    println("isClosedForSend = ${ch.isClosedForSend} · isClosedForReceive = ${ch.isClosedForReceive}")

    try { ch.send(3) } catch (e: ClosedSendChannelException) { println("send after close: $e") }
    println("trySend after close: ${ch.trySend(4)}")

    println("receive: ${ch.receive()}")
    println("receive: ${ch.receive()}")
    println("isClosedForReceive = ${ch.isClosedForReceive}")
    try { ch.receive() } catch (e: ClosedReceiveChannelException) { println("receive after drain: $e") }
    println("receiveCatching: ${ch.receiveCatching()}")
}
```

```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar close56.kt -d o56x =====
(exit 0)
===== java -cp o56x:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Close56Kt 2>/dev/null =====
isClosedForSend = true · isClosedForReceive = false
send after close: kotlinx.coroutines.channels.ClosedSendChannelException: Channel was closed
trySend after close: Closed(kotlinx.coroutines.channels.ClosedSendChannelException: Channel was closed)
receive: 1
receive: 2
isClosedForReceive = true
receive after drain: kotlinx.coroutines.channels.ClosedReceiveChannelException: Channel was closed
receiveCatching: Closed(null)
(exit 0)
```

- ★★★ **닫은 뒤 `send` 는 `kotlinx.coroutines.channels.ClosedSendChannelException: Channel was closed`** · **`trySend` 는 던지지 않고 `Closed(…)` 결과를 돌려준다.**
- ★★ **버퍼에 남은 것은 닫은 뒤에도 받힌다**(`1`·`2`) — `close` 는 「**더 안 보낸다**」이지 「버린다」가 아니다. 다 비운 뒤에야 `isClosedForReceive = true` 이고, 그때 `receive` 는 `ClosedReceiveChannelException`, `receiveCatching` 은 `Closed(null)` 이다.
- ★ Go 는 닫힌 채널에 보내면 **패닉**이다 — 받기 쪽 동작과 함께 [Go 29번](../../../go/syntax/29-channels-buffering-direction-close-range-and-nil/) (4)가 쟀다.

## 문법 — 형태와 규칙

**형태** — 자물쇠로 감싼 클래스 · `Channel` 로 만든 액터(변수는 액터 코루틴의 지역 변수).

```kotlin
// form56.kt
import kotlinx.coroutines.*
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock

class Account {
    private val mutex = Mutex()
    private var balance = 0
    suspend fun deposit(n: Int) = mutex.withLock { balance += n }
    suspend fun read(): Int = mutex.withLock { balance }
}

sealed interface Msg
data class Add(val n: Int) : Msg
class Get(val reply: CompletableDeferred<Int>) : Msg

fun CoroutineScope.counter(inbox: Channel<Msg>) = launch {
    var total = 0                        // 이 코루틴만 만진다
    for (m in inbox) when (m) {
        is Add -> total += m.n
        is Get -> m.reply.complete(total)
    }
}

fun main() = runBlocking {
    val acc = Account()
    coroutineScope { repeat(100) { launch(Dispatchers.Default) { acc.deposit(1) } } }
    println("account = ${acc.read()}")

    val inbox = Channel<Msg>()
    val job = counter(inbox)
    coroutineScope { repeat(100) { launch(Dispatchers.Default) { inbox.send(Add(1)) } } }
    val reply = CompletableDeferred<Int>()
    inbox.send(Get(reply))
    println("counter = ${reply.await()}")
    inbox.close(); job.join()
}
```

```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar form56.kt -d o56f =====
(exit 0)
===== java -cp o56f:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Form56Kt 2>/dev/null =====
account = 100
counter = 100
(exit 0)
```

**컴파일이 막히는 꼴**(진단 전문은 (2))

| 쓴 꼴 | 결과 | 어느 층 |
|---|---|---|
| `synchronized(x) { delay(1) }` · `{ yield() }` · `{ 직접 만든 suspend 호출 }` | error — 「`the '<이름>' suspension point is inside a critical section.`」 | 언어(컴파일러) |
| `lock.withLock { delay(1) }`(`kotlin.concurrent`) | 같은 error | 언어(컴파일러) |
| `lock.lock(); delay(1); lock.unlock()` | **통과** — 그러나 (4)의 두 사고가 난다 | 컴파일러가 못 보는 자리 |

**규칙 불릿**

- **자물쇠 안에 중단점이 있으면 `Mutex`** — `synchronized`·`withLock` 은 컴파일러가 막는다((2)).
- **자물쇠 안이 짧고 중단점이 없으면 `synchronized` 도 값은 안 잃는다**((1)) — 그러나 기다리는 동안 **스레드를 막는다**((3)).
- **`Mutex` 는 재진입하지 않는다** — 안에서 다시 잡지 마라((5)).
- **자물쇠 대신 소유를 한 곳에** — 한 스레드 한정 · 액터((1)).
- **`Channel` 용량은 「멈출 때」와 「버릴 때」를 정한다** — `CONFLATED`·`DROP_*` 는 값을 버린다((6)).
- **`close` 뒤 `send` 는 던진다 · 남은 것은 받힌다**((7)).

## 어디서 틀리나

1. ★★★ **「`synchronized` 는 코루틴에서 값을 잃는다」로 외운다.** 격자에서 **안 잃었다**((1)) — 문제는 중단점과 스레드다((2)(3)(4)).
2. ★★★ **`ReentrantLock` 의 `lock()`/`unlock()` 으로 바꾸면 컴파일이 되니 괜찮다고 본다.** 같은 스레드의 두 코루틴이 **동시에 들어가고**, 스레드를 갈아타면 **못 푼다**((4)).
3. ★★ **`synchronized` 안의 `Thread.sleep` 은 컴파일러가 말을 안 하니 괜찮다고 본다.** 스레드째 막는다((3)) — 디스패처의 스레드가 준다.
4. ★★ **`Mutex` 를 `synchronized` 처럼 재진입된다고 본다.** 안에서 다시 잡으면 **멈춘 채 남는다**((5)).
5. ★★ **`Channel()` 에 버퍼가 있다고 본다.** 기본은 `RENDEZVOUS`(0)이다((6)).
6. ★★ **`CONFLATED` 로 이벤트를 세거나 누적한다.** 마지막 것만 남는다((6)).
7. ★ **`close()` 가 남은 원소를 버린다고 본다.** 남은 것은 다 받힌다((7)).
8. ★ **20판 통과를 「안전하다」의 근거로 쓴다.** 근거는 자물쇠·원자 연산의 **계약**이다((1)).

## 구현 세부사항 대 언어 보장

| 항목 | 어느 쪽인가 | 근거 |
|---|---|---|
| `synchronized`·`withLock` 안의 중단점이 에러 | ★★★ **언어(컴파일러 진단)** | (2) |
| 검사기가 **두 함수 이름**을 알아본다 · `lock()`/`unlock()` 은 안 본다 | ★ **이 판 컴파일러의 구현**(`javap`) | (2) |
| `synchronized`·`ReentrantLock` 의 주인이 스레드 · 재진입 | ★★ **JVM·JDK 의 계약** — Kotlin 이 아니다 | (4)(5) |
| `Mutex` 재진입 불가 · 공정 · `owner` 가 디버깅용 | ★★ **라이브러리 계약(KDoc)** | (5) |
| `Channel` 용량 상수와 동작 · 기본 64 | ★★ **라이브러리 계약(KDoc)** — 64 는 JVM 시스템 속성으로 바뀐다 | (6) |
| 예외 메시지 문구(`Channel was closed` 등) | ★ **라이브러리 구현** | (5)(7) |
| 보호 없음이 값을 잃었다 | **관찰** — 머신·판에 매인다 | (1) |
| 기다리는 스레드의 상태(`BLOCKED`·`WAITING`) | **관찰** — 풀 구현(`Executors.newFixedThreadPool`)에 매인다 | (3) |
| 「`Mutex` 가 느리다/빠르다」 | **재지 않았다** | — |

★★ **가장 조심할 자리** — 컴파일러가 막는 것은 **이름 두 개**다. 「컴파일이 됐다」는 「자물쇠와 코루틴이 안 섞였다」가 아니다((2)(4)).

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 자물쇠 안에서 `suspend` 함수를 불러야 한다 | ★ `Mutex.withLock` | (2)(3) — 스레드를 놓고 기다린다 |
| 수 하나를 더하고 읽는다 | `AtomicInteger`·`AtomicLong` | (1) — 자물쇠가 없다 |
| 상태 여러 개를 한꺼번에 고친다 | 한 스레드 한정(`limitedParallelism(1)`) 또는 액터 | (1) — 만지는 쪽이 하나 |
| 자물쇠 안이 짧고 중단점이 없다 | `synchronized` 도 된다 | (1) — 단 기다림이 길면 (3) |
| 생산자가 소비자보다 빠르면 멈추게 하고 싶다 | 유한 용량 `Channel(n)` | (6) |
| 최신 값만 필요하다(화면 갱신 등) | `CONFLATED` | (6) — 버린다는 것을 알고 |
| 이미 `synchronized` 로 된 Java 코드를 코루틴에서 부른다 | `withContext(Dispatchers.IO)` 로 옮겨 스레드를 따로 막는다 | (3) — 디스패처 선택은 [54번 주제](../54-coroutine-context-dispatchers-and-withcontext/) |

## 핵심 문장

1. 코루틴 1000개 × 100번 격자에서 **값을 잃은 것은 보호 없음 하나뿐**이다(1 / 6) — `synchronized` 도 값은 지켰다.
2. `synchronized`·`withLock` 안의 중단점은 **컴파일 에러**다 — 「`suspension point is inside a critical section`」. 검사기는 **그 두 이름**만 본다.
3. 스레드가 주인인 자물쇠는 **같은 스레드의 코루틴 둘을 못 가르고**, 코루틴이 스레드를 갈아타면 **못 푼다**(`IllegalMonitorStateException`).
4. 기다리는 동안 `synchronized` 는 **스레드를 막고**(`BLOCKED`), `Mutex` 는 **코루틴만 멈춘다** — 그 대신 `Mutex` 는 **재진입하지 않는다.**
5. `Channel` 용량은 보내는 쪽이 **언제 멈추고 무엇을 버리나**를 정한다 — 기본은 0, `BUFFERED` 는 64, `CONFLATED` 는 마지막 하나.

## 관련 자료

- [`../../언어-특성/README.md`](../../언어-특성/README.md) §6 — 코루틴이 스레드가 아니라 컴파일러 변환이라는 **논지** · `Dispatchers.IO` 로 격리한다는 운영 판단. 그쪽은 **왜 이 모델인가**, 여기는 **공유 상태를 지키는 수단의 선택**.
- [52번 주제](../52-coroutine-basics-suspend-scope-launch-async/) — `suspend` 함수의 호출 규칙(어디서 부르면 막히나). (2)의 진단은 그 규칙의 **반대쪽**이다 — 「어디서 부르면 안 되나」.
- [53번 주제](../53-structured-concurrency-job-cancellation-exceptions/) — 취소 전파. (5)의 `withTimeout` 이 바깥 `withLock` 의 `finally` 를 지나 자물쇠를 푼 것이 그 규칙의 사례다.
- [54번 주제](../54-coroutine-context-dispatchers-and-withcontext/) — 디스패처 · `limitedParallelism` · `withContext`. (1)의 한 스레드 한정과 (3)의 스레드 수.
- [55번 주제](../55-flow-cold-streams-operators-and-collect/) — `Flow`. `Channel` 은 **핫**(받는 쪽이 없어도 보낸다), `Flow` 는 **콜드**다.
- [Java 33번](../../../java/syntax/33-synchronized-and-volatile/) — `int++` 이 왜 깨지나 · 재진입 · 잠금 대상. [Java 55번](../../../java/syntax/55-atomics-and-concurrent-collections/) — 원자 변수. [Java 56번](../../../java/syntax/56-virtual-threads/) — `synchronized` 와 고정(pinning).
- [Go 29번](../../../go/syntax/29-channels-buffering-direction-close-range-and-nil/) — 버퍼 · 닫힌 채널 × 연산. [Go 32번](../../../go/syntax/32-sync-mutex-rwmutex-waitgroup-once/) — 뮤텍스.
- C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **40번**(`async`/`await`) — (2)의 `CS1996` 대비가 이어질 자리.
- [`cs/foundations/process-thread/`](../../../../process-thread/) — 스레드·경쟁 조건의 개념.

## 용어 풀이

> **공유 가변 상태(shared mutable state)** — 여러 실행 흐름이 **같이 읽고 고치는** 변수. 고치는 동작이 한 번에 끝나지 않으면 값을 잃는다.\
> 예: `plain++` 은 읽기·더하기·쓰기 셋이다.

> **임계 구역(critical section)** — 한 번에 하나만 들어가야 하는 코드 구간. 진단 문구의 `critical section` 이 이것이다.

> **중단점(suspension point)** — `suspend` 함수를 부르는 자리. 코루틴이 거기서 멈췄다가 **다른 스레드에서** 이어질 수 있다.

> **재진입(reentrant)** — 자물쇠를 쥔 주인이 같은 자물쇠를 **다시 잡을 수 있는** 성질. `synchronized`·`ReentrantLock` 은 되고 `Mutex` 는 안 된다.

> **`BLOCKED` / `WAITING`** — JVM 스레드 상태. 모니터(`synchronized`) 앞에서 기다리면 `BLOCKED`, 풀에서 일감을 기다리며 놀면 `WAITING`((3)에서 본 두 상태).

> **한 스레드 한정(thread confinement)** — 상태를 **한 스레드에서만** 만지게 해서 자물쇠를 없애는 방법. 코루틴에서는 `limitedParallelism(1)` 디스패처로 옮겨 만진다.

> **액터(actor)** — 상태를 **한 코루틴이 소유**하고, 다른 코루틴은 `Channel` 로 **메시지만** 보내는 구조.

> **랑데부(rendezvous)** — 버퍼 0 인 채널. 보내는 쪽과 받는 쪽이 **만나야** 한 원소가 건너간다.

> **`CONFLATED`** — 버퍼 한 칸에 **새 값이 옛 값을 덮는** 채널. 보내는 쪽이 멈추지 않는 대신 값을 버린다.

## 더 들어가면

- **`Semaphore`**(`kotlinx.coroutines.sync`) — 한 번에 N 개까지. `Mutex` 의 일반화다 — 돌리지 않았다.
- **`select`** — 채널 여럿 중 먼저 되는 것 하나. 이 문서는 **다루지 않았다.**
- **`produce { }`·`actor { }` 빌더** — 채널 생산자·액터를 한 줄로 만든다. 이 판에서 **선언의 표지(실험적 등)를 확인하지 않았다** — 그래서 (문법)의 형태는 `Channel` + `launch` 로만 썼다.
- **성능 비교** — `Mutex`·`synchronized`·`AtomicInteger`·액터의 처리량은 **JMH 판 격자**가 있어야 말할 수 있다(규칙 24). 이 문서는 재지 않았다.
- **`-Dkotlinx.coroutines.channels.defaultBuffer`** — `BUFFERED` 의 64 를 바꾸는 JVM 속성((6) 발췌 마지막 줄의 `DEFAULT_BUFFER_PROPERTY_NAME`). 바꿔 돌리지 않았다.
