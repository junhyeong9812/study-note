# kotlin/syntax/56 — `Channel`·`Mutex` — 공유 가변 상태 다루기 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** · Temurin **JDK 21.0.5** 의 `java`·`javap` · **kotlinx-coroutines 1.11.0** 에서 실제로 얻었다. C# 은 .NET SDK 10.0.401 의 `csc` 다.
> ★★ 아래 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적은 자리가 없다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **1 / 6** — 한 판이라도 잃은 것은 **보호 없음 하나** · `synchronized`·`Mutex.withLock`·`AtomicInteger`·한 스레드 한정·`Channel` 액터는 20판 모두 100000

**출력**

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

**왜 그런가**

- ★★★ `plain++` 은 읽기·더하기·쓰기 셋이고 `Dispatchers.Default` 는 스레드가 여럿이다 — 두 코루틴이 **같은 값을 읽어 같은 값을 쓰면** 한 번이 사라진다.
- ★★★ **`synchronized` 도 값은 지켰다** — 자물쇠 안에 중단점이 없어서다. 이 주제의 「쓰면 안 된다」는 **값을 잃어서가 아니다**(2\~4번).
- ★★ 한 스레드 한정과 액터는 자물쇠 없이 **만지는 쪽을 하나로** 만든다(10번).
- ★ `false` 는 「20판에서 한 번도 안 잃었다」이다 — 안 잃는다는 **증명**은 자물쇠·원자 연산의 계약이 한다. 보호 없음이 한 판도 안 잃는 머신이 있어도 안전하지 않다.

### 2. ★★★ **막힌 탐침 4 / 8** — `synchronized` 안의 `delay`·`yield`·직접 만든 `suspend` 호출 · `ReentrantLock.withLock` 안의 `delay` · 진단은 「`the '<이름>' suspension point is inside a critical section.`」

**출력**

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

**왜 그런가**

- ★★★ `synchronized { }` 와 `kotlin.concurrent.withLock { }` 의 람다 몸통은 **그 자물쇠 구간 안에서** 돈다 — 거기 중단점이 있으면 **자물쇠를 쥔 채 코루틴이 멈추고, 다른 스레드에서 이어질 수 있다.** 컴파일러가 그것을 막는다.
- ★★ **직접 만든 `suspend fun step()` 도 막힌다** — 이름이 무엇이든 중단점이면 막힌다(진단의 `'step'`).
- ★★ 통과한 넷 — `lock()+delay+unlock()`(자물쇠는 같은데 **함수 이름이 다르다** — 8번) · `Mutex.withLock+delay`(중단으로 기다리는 자물쇠) · `synchronized+launch`(새 코루틴의 중단점은 자물쇠 밖) · `synchronized+Thread.sleep`(중단점이 아니다 — 스레드를 막을 뿐, 3번).

### 3. ★★ `sync` 는 **`sync-1=TIMED_WAITING, sync-2=BLOCKED`** · `false` — `mutex` 는 **`mutex-1=WAITING, mutex-2=WAITING`** · `true`

**출력**

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

**왜 그런가**

- ★★★ `synchronized` 판 — 첫째가 `Thread.sleep` 으로 스레드째 자고(`TIMED_WAITING`), 둘째는 모니터 앞에서 **스레드째** 선다(`BLOCKED`). 풀의 두 스레드가 다 묶여 셋째가 **첫째가 끝날 때까지** 못 돌았다.
- ★★★ `Mutex` 판 — 첫째는 `delay` 로, 둘째는 `lock` 에서 **코루틴만** 멈췄다. 두 스레드는 일감을 기다리며 놀고(`WAITING`), 셋째가 **바로** 돌았다.
- ★ 이 블록은 50ms 간격의 걸음에 기댄다 — 세 판 되풀이에서 출력 해시가 **1가지**였다(2-summary (3)).

### 4. ★★★ 구간 1 은 **`inside now = [x, y]` · `holdCount = 2`**(둘 다 들어갔다) · 구간 2 는 **`[x]` 뒤 `[y]`** · 구간 3 은 **`caught: java.lang.IllegalMonitorStateException`**

**출력**

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

**왜 그런가**

- ★★★ `ReentrantLock` 의 주인은 **스레드**다. 두 코루틴이 같은 `thread-A` 에서 돌면 자물쇠에게는 **같은 주인의 재진입**이라 둘 다 받아 준다 — 상호 배제가 깨지는데 **예외도 경고도 없다.**
- ★★★ `Mutex` 는 주인이 스레드가 아니라서 같은 스레드여도 하나만 들인다.
- ★★★ 구간 3 — `withContext(other)` 가 코루틴을 `thread-B` 로 옮겼다. `thread-B` 는 그 자물쇠를 쥐지 않았으니 `unlock()` 이 던진다. 여러 스레드 디스패처에서는 **`delay` 뒤에 다른 스레드에서 이어지는 것**이 보통이다 — 이 구간은 그것을 결정적으로 만든 판이다.

### 5. ★★ `A` 는 **`inner block ran`** · `B` 는 안쪽이 **안 찍히고 `TimeoutCancellationException: Timed out waiting for 500 ms`** · `after B` 는 **`isLocked = false`** · `C` 는 **`IllegalStateException: This mutex is already locked by the specified owner: job-1`**

**출력**

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

**왜 그런가**

- ★★★ `synchronized` 는 **재진입**된다 — 같은 스레드가 자기 모니터에 다시 들어간다.
- ★★★ `Mutex` 는 KDoc 이 「`non-reentrant`」라 적는다 — 같은 코루틴이 다시 `lock` 하면 **자기 자신을 기다린다.** `withTimeout` 이 없으면 끝나지 않는다.
- ★★ 타임아웃의 취소가 바깥 `withLock` 의 `finally` 를 지나며 `unlock` 해서 `isLocked = false` 다.
- ★ `owner` 를 주면 같은 `owner` 의 두 번째 `lock` 이 **교착 대신 즉시 던진다** — 디버깅용 표지다.

### 6. ★★ **`Channel()`·`RENDEZVOUS` → `0 · true`** · **`Channel(2)` → `2 · true`** · **`BUFFERED`·`UNLIMITED` → `5 · false`** · **`CONFLATED` → `5 · false · [5]`** · **`Channel(2, DROP_OLDEST)` → `5 · false · [4, 5]`** · 끝 두 줄은 **`64`** 와 **`70`**

**출력**

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

**왜 그런가**

- ★★★ 버퍼가 0 이면 `send` 는 받는 쪽이 올 때까지 멈춘다 — 받기 전 끝난 보내기가 0 이고 보내는 쪽이 살아 있다(`true`). 기본 생성자가 `RENDEZVOUS` 다.
- ★★★ `Channel(2)` 는 두 칸이 차면 멈춘다. `BUFFERED` 의 기본 용량은 **64** — 다섯은 다 들어가고, 70 을 보내면 64 에서 멈췄다가 받는 쪽이 비우자 70 이 다 건너갔다.
- ★★ `CONFLATED`·`DROP_OLDEST` 는 **멈추지 않는 대신 버린다** — 넷째 칸이 줄었다.

### 7. ★★★ 자물쇠를 쥔 채 **코루틴이 스레드를 바꾸는 것** — 4번의 구간 3(다른 스레드에서 못 푼다)과 구간 1(같은 스레드의 코루틴 둘을 못 가른다)

**왜 그런가**

- ★★★ `synchronized` 의 주인은 **스레드**이고, 코루틴은 중단점에서 멈췄다가 **다른 스레드에서** 이어질 수 있다. 자물쇠 구간 안에 중단점이 있으면 ① 다른 스레드에서 풀려고 해 실패하거나(구간 3) ② 멈춘 사이 같은 스레드의 다른 코루틴이 **재진입으로 들어온다**(구간 1).
- ★★ 게다가 기다리는 쪽은 **스레드째** 막힌다(3번) — 값은 안 잃어도(1번) 디스패처의 스레드를 먹는다.
- ★ 그래서 이 진단은 **성능 경고가 아니라 의미 오류**를 막는다 — 에러이지 경고가 아니다.

### 8. ★★★ **어긋나는 것은 `lock()+delay+unlock()`**(통과하지만 4번의 두 사고가 난다) — 검사기는 **`kotlin.synchronized` 와 `kotlin.concurrent.withLock` 두 이름**만 알아본다 · `synchronized+Thread.sleep` 도 통과하지만 스레드를 막는다

**출력**

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

**왜 그런가**

- ★★★ 검사기 클래스의 상수 풀에 `kotlin` + `synchronized`, `kotlin.concurrent` + `withLock` 네 문자열이 있다 — **함수 이름의 짝**으로 자물쇠 구간을 알아본다. `lock()`·`unlock()` 을 따로 부르면 **구간이 어디서 시작하고 끝나는지** 컴파일러가 모른다.
- ★★ `synchronized` 안의 `Thread.sleep` 은 **중단점이 아니라** 대상이 아니다 — 하지만 3번처럼 스레드를 막는다.
- ★ 이 이름 목록은 **이 판 컴파일러의 구현**이다 — 명세로 읽지 마라.

### 9. ★★ `send` 는 **`ClosedSendChannelException: Channel was closed`** · `trySend` 는 **던지지 않고 `Closed(…)`** · `receive` 두 번은 **`1`·`2`** · 다시 `receive` 는 **`ClosedReceiveChannelException: Channel was closed`** · `receiveCatching` 은 **`Closed(null)`**

**출력**

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

**왜 그런가**

- ★★★ `close` 는 「**더 안 보낸다**」다 — 닫은 즉시 `isClosedForSend = true` 지만 `isClosedForReceive` 는 **남은 둘을 다 받은 뒤에야** `true` 다.
- ★★ `send` 는 예외로, `trySend`·`receiveCatching` 은 **결과 값**으로 닫힘을 알린다 — 던지지 않는 쪽을 고를 수 있다.

### 10. ★★ **만지는 쪽이 한 번에 하나**라서 — 한 스레드 한정은 **한 스레드에서만**, 액터는 **한 코루틴의 지역 변수로** · `CONFLATED` 로 바꾸면 **메시지를 버려 수를 잃는다**

**왜 그런가**

- ★★★ 경쟁은 **둘 이상이 동시에 읽고 쓸 때** 난다. 한 스레드 한정은 `withContext(single)` 로 증가를 **한 스레드에 줄 세우고**, 액터는 변수를 **받는 코루틴 하나만** 본다 — 자물쇠가 지키는 것을 **구조가** 지킨다.
- ★★ 액터의 채널이 `CONFLATED` 면 받는 쪽이 늦을 때 **앞 메시지를 덮어** 버린다(6번의 `[5]`) — 증가 메시지가 사라지니 카운터가 **모자란다.** 이 문서는 그 판을 **돌리지 않았다** — 6번의 채널 동작에서 따라 나오는 추론이다.

### 11. ★★ C# 은 **`lock` 몸통 안의 `await` 를 `CS1996` 컴파일 에러로 막는다** — Kotlin 의 「`suspension point is inside a critical section`」과 같은 자리 · 가상 스레드의 고정도 3번처럼 **자물쇠 앞에서 스레드(캐리어)째 묶이는** 모양이다

**출력**

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

**왜 그런가**

- ★★★ C# 의 `lock`(`Monitor`)도 **주인이 스레드**이고, `await` 뒤에는 **다른 스레드에서** 이어질 수 있다 — Kotlin 과 같은 이유로 **컴파일에서** 막는다.
- ★★ [Java 56번](../../../java/syntax/56-virtual-threads/)은 JDK 21 에서 `synchronized` 안의 블로킹이 가상 스레드를 **캐리어에 붙잡는** 것을 쟀다 — 기다리는 동안 **밑의 플랫폼 스레드를 못 돌려준다**는 점이 3번의 `BLOCKED` 와 같은 모양이다. 그쪽은 JEP 491(JDK 24) 이후 달라졌다고 적었다 — 이 문서는 21 에서만 돌렸다.

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
===== python3 --version =====
Python 3.12.3
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

★ **흔들리는 칸과 안 흔들리는 칸**

| 흔들린다 | 안 흔들린다 |
|---|---|
| ★★ 보호 없음 칸의 **최종 값 · 잃은 판 수** — 칸으로 안 만들었다(불리언만) | 보호 다섯 칸의 `false` · `1 / 6` |
| ★ **머신에 매인다** — 보호 없음이 `true` 인 것(24코어 · 세 판 되풀이에서 해시 1가지) | 진단 격자 · 진단 전문 · 검사기 `javap` · C# 진단 |
| ★ **라이브러리 판** — 1.11.0 이 아니면 다시 돌려라 | 스레드 상태 로그(세 판 되풀이에서 해시 1가지) · 소유·재진입·채널·닫기 로그(단일 스레드) · 모든 **종료 코드** |

> 근거 — 캡처 스크립트를 처음부터 다시 돌려 **블록 전체를 대조**했다.
>
> 실측 — `capture.sh blocks` 와 `capture.sh blocks-re` 를 처음부터 따로 돌려 `normalize-shaky.py` 로 대조했다 — **블록 109개 · 동일 109 · 흔들린 칸 0 · ★고칠 것 0**(54\~58 다섯 주제를 한 캡처로 받았다 — 이 주제 몫은 출력 16 · 소스 10 · 환경 5). 추가한 정규화 규칙은 없다.

```text
===== for i in 1 2 3; do java -cp o56g:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Grid56Kt | md5sum; done | sort | uniq -c =====
      3 9390405aebdb04fa0ea8ff86095a7719  -
(exit 0)
```

```text
===== for i in 1 2 3; do java -cp o56b:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Block56Kt | md5sum; done | sort | uniq -c =====
      3 909ea04141b240e8741ef74122ad4784  -
(exit 0)
```

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `grid56.kt` | ★★★ 공유 상태 격자 — 방법 6 × 20판 | `kotlinc` → `java`(칸 수 검사·잃은 칸 수는 프로그램이 센다) + 세 판 되풀이 해시 |
| `crit56.kt` · `gridc56.py` | ★★★ 중단점 진단 8탐침 | 스크립트가 컴파일 · 진단을 줄마다 읽는다 + 에러 전문 |
| `kotlin-compiler.jar` | ★★ 검사기가 알아보는 이름 | `unzip` → `javap -c -p`(전부 받은 뒤 `grep`) |
| `block56.kt` | ★★ 기다리는 동안의 스레드 상태 | `kotlinc` → `java` + 세 판 되풀이 해시 |
| `own56.kt` | ★★★ 스레드가 주인인 자물쇠 × 코루틴 둘 · 스레드 갈아타기 | `kotlinc` → `java`(단일 스레드 풀 둘) |
| `nest56.kt` | ★ 재진입 · `withTimeout` · `owner` | `kotlinc` → `java` |
| `chan56.kt` · `close56.kt` | ★★ 용량 격자 · 닫은 뒤 | `kotlinc` → `java` |
| 라이브러리 소스 jar | `Mutex` KDoc · `withLock` · 용량 상수 | `unzip` → `sed -n` |
| `lock56.cs` | ★ C# `CS1996` | `csc`(Roslyn · .NET SDK 10.0.401) |
| `form56.kt` | 형태 한 벌 | `kotlinc` → `java` |

**구현 의존 항목** — 검사기가 이름 두 개를 본다는 것 · 예외 메시지 문구 · 기다리는 풀 스레드의 상태 이름 — 이 컴파일러·라이브러리·JDK 판의 산출물이다.\
반면 **`synchronized`·`withLock` 안 중단점의 컴파일 에러**는 **언어(컴파일러 진단)**, **`Mutex` 재진입 불가·`Channel` 용량 동작**은 **라이브러리 계약(KDoc)**, **`synchronized`·`ReentrantLock` 의 스레드 소유와 재진입**은 **JVM·JDK 의 계약**이다.

**★ 던져 봤더니 예상과 달랐던 것 — 세 건**

1. ★★★ **`kotlin.concurrent.withLock` 안의 `delay` 도 막혔다** — `synchronized` 만 막힐 것으로 예상했다. 그런데 **같은 자물쇠를 `lock()`/`unlock()` 으로 풀어 쓰면 통과했다** — 검사기가 자물쇠가 아니라 **함수 이름**을 본다(8번).
2. ★★★ **`ReentrantLock` 이 같은 스레드의 코루틴 둘을 동시에 들였다**(`holdCount = 2`) — 「스레드를 갈아타면 못 푼다」만 예상했는데, **스레드를 안 갈아타도** 깨지는 자리가 있었다(4번 구간 1).
3. ★★ **`synchronized` 는 격자에서 값을 한 번도 안 잃었다** — 「코루틴에서 `synchronized` 는 틀린다」가 아니라 「**중단점과 섞으면** 틀리고, 안 섞어도 **스레드를 막는다**」였다(1·3번).
