# kotlin/syntax/52 — 코루틴 기초 — `suspend`·`CoroutineScope`·`launch`/`async`/`await` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `java`·`javap`, 그리고 **kotlinx-coroutines-core-jvm 1.11.0** 에서 실제로 얻었다.
> ★★ 아래 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적은 자리가 없다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 클래스 **둘**(`Cps52Kt` · `Cps52Kt$twice$1`) · `twice`·`plain` 은 **`(int, Continuation): Object`**, `normal` 은 `int normal(int)` · 상태 기계에 **`label` · `I$0` · `I$1` · `result`** · `tableswitch` 는 **0 to 2**

**출력**

```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar cps52.kt -d o52c =====
(exit 0)
===== ls o52c =====
Cps52Kt$twice$1.class
Cps52Kt.class
META-INF
(exit 0)
===== javap -p o52c/Cps52Kt.class =====
Compiled from "cps52.kt"
public final class Cps52Kt {
  public static final java.lang.Object twice(int, kotlin.coroutines.Continuation<? super java.lang.Integer>);
  public static final java.lang.Object plain(int, kotlin.coroutines.Continuation<? super java.lang.Integer>);
  public static final int normal(int);
}
(exit 0)
===== javap -p 'o52c/Cps52Kt$twice$1.class' =====
Compiled from "cps52.kt"
final class Cps52Kt$twice$1 extends kotlin.coroutines.jvm.internal.ContinuationImpl {
  int I$0;
  int I$1;
  java.lang.Object result;
  int label;
  Cps52Kt$twice$1(kotlin.coroutines.Continuation<? super Cps52Kt$twice$1>);
  public final java.lang.Object invokeSuspend(java.lang.Object);
}
(exit 0)
===== javap -c -p o52c/Cps52Kt.class | grep -E 'public static final|COROUTINE_SUSPENDED|tableswitch|Field Cps52Kt\$twice\$1\.(label|I\$[0-9])' =====
  public static final java.lang.Object twice(int, kotlin.coroutines.Continuation<? super java.lang.Integer>);
      15: getfield      #15                 // Field Cps52Kt$twice$1.label:I
      27: getfield      #15                 // Field Cps52Kt$twice$1.label:I
      33: putfield      #15                 // Field Cps52Kt$twice$1.label:I
      55: invokestatic  #30                 // Method kotlin/coroutines/intrinsics/IntrinsicsKt.getCOROUTINE_SUSPENDED:()Ljava/lang/Object;
      62: getfield      #15                 // Field Cps52Kt$twice$1.label:I
      65: tableswitch   { // 0 to 2
     102: putfield      #39                 // Field Cps52Kt$twice$1.I$0:I
     108: putfield      #15                 // Field Cps52Kt$twice$1.label:I
     125: getfield      #39                 // Field Cps52Kt$twice$1.I$0:I
     145: putfield      #39                 // Field Cps52Kt$twice$1.I$0:I
     151: putfield      #48                 // Field Cps52Kt$twice$1.I$1:I
     157: putfield      #15                 // Field Cps52Kt$twice$1.label:I
     174: getfield      #48                 // Field Cps52Kt$twice$1.I$1:I
     180: getfield      #39                 // Field Cps52Kt$twice$1.I$0:I
  public static final java.lang.Object plain(int, kotlin.coroutines.Continuation<? super java.lang.Integer>);
  public static final int normal(int);
(exit 0)
```

**왜 그런가**

- ★★★ `suspend` 함수는 **`Continuation` 을 마지막 인자로 더 받고 `Object` 를 돌려준다**(CPS) — 중단점 유무와 무관하게 **서명은 늘 바뀐다**(`plain`).
- ★★★ 중단점이 있는 `twice` 만 상태 기계 클래스가 생겼다 — 지역 변수 `x`·`y` 가 **필드 `I$0`·`I$1`** 로 옮겨졌고, 중단점 둘 → 들어올 자리 셋 → **`tableswitch` 0\~2**.

### 2. ★★★ **막힌 탐침 5 / 9 · 문구 두 종** — 일반 함수 몸통(`plain-function` · `Thread-lambda` · `plain-calls-suspend-fun`)은 「`suspend function '…' can only be called from a coroutine or another suspend function.`」 · 일반 람다(`plain-lambda-type` · `Sequence-map-lambda`)는 「`suspension functions can only be called within coroutine body.`」

**출력**

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


```text
===== CP52=kotlinx-coroutines-core-jvm-1.11.0.jar python3 grid52.py =====
probe	compile
plain-function	error: suspend function 'suspend fun f(x: Int): Int' can only be called from a coroutine or another suspend function.
suspend-function	ok
inline-lambda	ok
plain-lambda-type	error: suspension functions can only be called within coroutine body.
suspend-lambda-type	ok
runBlocking-block	ok
Thread-lambda	error: suspend function 'suspend fun f(x: Int): Int' can only be called from a coroutine or another suspend function.
Sequence-map-lambda	error: suspension functions can only be called within coroutine body.
plain-calls-suspend-fun	error: suspend function 'suspend fun p2(): Unit' can only be called from a coroutine or another suspend function.
exit 1
blocked probes: 5 / 9
(exit 0)
```

```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar call52.kt -d o52e =====
call52.kt:5:12: error: suspend function 'suspend fun f(x: Int): Int' can only be called from a coroutine or another suspend function.
fun p1() { f(1) }                                                        // plain-function
           ^
call52.kt:8:42: error: suspension functions can only be called within coroutine body.
suspend fun p4() { val g: () -> Unit = { f(1) } }                        // plain-lambda-type
                                         ^
call52.kt:11:21: error: suspend function 'suspend fun f(x: Int): Int' can only be called from a coroutine or another suspend function.
fun p7() { Thread { f(1) } }                                             // Thread-lambda
                    ^
call52.kt:12:49: error: suspension functions can only be called within coroutine body.
suspend fun p8() { listOf(1).asSequence().map { f(it) }.toList() }       // Sequence-map-lambda
                                                ^
call52.kt:13:12: error: suspend function 'suspend fun p2(): Unit' can only be called from a coroutine or another suspend function.
fun p9() { p2() }                                                        // plain-calls-suspend-fun
           ^^
(exit 1)
```

**왜 그런가**

- ★★★ `inline` 람다(`forEach`)는 바깥 `suspend` 함수에 펼쳐지니 **된다** · `suspend` 람다 타입도 **된다** · `runBlocking { }` 은 람다가 `suspend` 수신자 람다라 **된다.**
- ★★ `Sequence.map` 의 람다는 `inline` 이 아니다 — 같은 `suspend` 함수 안이어도 막힌다.
- ★ `suspend` 는 **전염된다** — `p2` 를 부르는 `p9` 도 막혔다.

### 3. `100000 launched and finished` · **`distinct thread ids seen = 1`** · **`activeCount before=1 during=1 after=1`** · 스레드 쪽 **`during=101 after=1`**

**출력**

```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar threads52.kt -d o52t =====
(exit 0)
===== java -cp o52t:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Threads52Kt =====
coroutines: 100000 launched and finished
coroutines: distinct thread ids seen = 1
coroutines: activeCount before=1 during=1 after=1
threads: 100 started, activeCount during=101 after=1
(exit 0)
```

**왜 그런가**

- ★★★ `runBlocking` 은 부른 스레드 하나로 이벤트 루프를 돌린다 — 10만 개가 `delay` 마다 **그 스레드를 놓고** 다시 받는다.
- ★★ 플랫폼 스레드는 하나 만들 때마다 `activeCount` 가 하나 는다(main + 100).
- ★ 이것은 **개수**다 — 시간·메모리는 안 쟀다.

### 4. `delay(10)` · `yield()` 는 **`A0 B0 A1 B1 A2 B2`** · `Thread.sleep(10)` 은 **`A0 A1 A2 B0 B1 B2`**

**출력**

```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar interleave52.kt -d o52i =====
(exit 0)
===== java -cp o52i:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Interleave52Kt =====
delay(10)        A0 B0 A1 B1 A2 B2
Thread.sleep(10) A0 A1 A2 B0 B1 B2
yield()          A0 B0 A1 B1 A2 B2
(exit 0)
```

**왜 그런가**

- ★★★ `delay`·`yield` 는 **중단점**이라 스레드를 놓는다 — 같은 스레드의 B 가 그 틈에 돈다.
- ★★★ `Thread.sleep` 은 **스레드째 재운다** — B 는 A 가 세 걸음을 다 갈 때까지 못 돈다.

### 5. `1` → **`call` 몸통 전체** → `2` → `3` → **`undispatched: body starts`** → `4` → `launch: body starts` → `undispatched: after delay` → `launch: after delay` → `5`

**출력**

```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar order52.kt -d o52o =====
(exit 0)
===== java -cp o52o:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Order52Kt =====
1 before the call
call: body starts
call: after delay
2 after the call
3 after launch { }
undispatched: body starts
4 after launch(UNDISPATCHED) { }
launch: body starts
undispatched: after delay
launch: after delay
5 after joinAll
(exit 0)
```

**왜 그런가**

- ★★★ `suspend` 함수를 그냥 부르면 **보통 호출** — 끝날 때까지 `2` 로 안 온다.
- ★★★ `launch { }` 는 **줄만 세운다** — 몸통은 부모가 멈춘 뒤(`joinAll`)에 돈다. `UNDISPATCHED` 는 **첫 중단점까지 그 자리에서** 돈다.
- ★ `undispatched` 가 `launch` 보다 먼저 `delay` 에 들어갔으니 먼저 깨어난다(같은 1ms).

### 6. **네 줄** — `other step 0` · `caught at await: boom` · `after await: isActive=false, other.isCancelled=true` · `outside the scope: IllegalStateException: boom` — **`after yield` 는 안 찍힌다**

**출력**

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


```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar await52.kt -d o52a =====
(exit 0)
===== java -cp o52a:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Await52Kt =====
other step 0
caught at await: boom
after await: isActive=false, other.isCancelled=true
outside the scope: IllegalStateException: boom
(exit 0)
```

```text
===== for i in 1 2 3 4 5; do java -cp o52i:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Interleave52Kt | md5sum; java -cp o52o:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Order52Kt | md5sum; java -cp o52a:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Await52Kt | md5sum; done | sort | uniq -c =====
      5 46faf74adab9b9ba1f1b7076d0b2c8eb  -
      5 bf1dfe503ce4c52d261de86189c00c35  -
      5 e98a75e77bd305b1c7ba80f26b487496  -
(exit 0)
```

**왜 그런가**

- ★★★ `async` 의 예외는 `await()` 에서 **값처럼** 나온다 — 그러나 자식이 실패한 순간 **부모 scope 가 취소됐고**(`isActive=false`), 형제도 취소됐다.
- ★★ 취소된 코루틴에서 `yield()` 는 곧바로 `CancellationException` 을 던진다 — 블록이 멈추고, scope 는 **원래 예외**를 밖으로 다시 던진다. 규칙은 [53번 주제](../53-structured-concurrency-job-cancellation-exceptions/).
- ★ 둘째 블록 — 순서 로그 셋을 다섯 판씩 돌린 **출력 해시가 셋, 각 5번** — 순서가 한 번도 안 흔들렸다.

### 7. **`COROUTINE_SUSPENDED`** — 「멈췄다 · 결과는 나중에」 표지가 진짜 값(`Integer`) 대신 올 수 있어서

**왜 그런가**

```text
===== sed -n '19,22p;57p' commonMain/kotlin/coroutines/intrinsics/Intrinsics.kt =====
 * If the [block] returns the special [COROUTINE_SUSPENDED] value, it means that suspend function did suspend the execution and will
 * not return any result immediately. In this case, the [Continuation] provided to the [block] shall be
 * resumed by invoking [Continuation.resumeWith] at some moment in the
 * future when the result becomes available to resume the computation.
public val COROUTINE_SUSPENDED: Any get() = CoroutineSingletons.COROUTINE_SUSPENDED
(exit 0)
===== sed -n '11p' jvmMain/kotlin/coroutines/cancellation/CancellationException.kt =====
public actual typealias CancellationException = java.util.concurrent.CancellationException
(exit 0)
```

- ★★★ KDoc — 「`If the [block] returns the special [COROUTINE_SUSPENDED] value, it means that suspend function did suspend the execution and will not return any result immediately.`」 `Int` 로는 이 표지를 담을 수 없다.
- ★★ 1번의 `getCOROUTINE_SUSPENDED` 호출 줄이 그 비교 자리다.

### 8. **main 스레드가 `runBlocking` 동안 막혀 있는지**를 **다른 스레드가** 본다 — `TIMED_WAITING` · `runBlocking` 은 **`main`·테스트 같은 경계**에만

**출력**

```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar block52.kt -d o52b =====
(exit 0)
===== java -cp o52b:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Block52Kt =====
1 before runBlocking on main
2 inside runBlocking on main
3 child done on main
4 after runBlocking
5 main thread state seen by another thread at 150ms: TIMED_WAITING
(exit 0)
```

**왜 그런가**

- ★★★ `4 after runBlocking` 은 자식의 `delay(300)` 이 끝난 **뒤에** 나온다 — 그 사이 main 은 **잠든(`TIMED_WAITING`)** 상태였다. `runBlocking` 은 스레드를 **막는** 다리다.
- ★★ 그래서 이미 코루틴 안(요청 처리 스레드 · 다른 코루틴)에서 부르면 **그 스레드를 막는다** — 거기서는 `suspend` 를 그대로 쓴다.
- ★ main 이 자기 상태를 스스로 물을 수는 없다(막혀 있으니까) — **감시 스레드로 창을 바꿨다**(제5의 상태).

### 9. Python 은 **몸통 0줄**(코루틴 객체만) · Kotlin 은 코루틴 안에서 부르면 **몸통이 끝까지 도는 보통 호출** · 부르는 쪽이 일반 함수면 Python 은 **부를 수는 있고**(객체가 나온다) Kotlin 은 **컴파일이 안 된다**

**왜 그런가**

- ★★ [Python 51번](../../../python/syntax/51-asyncio-coroutine-basics/) — 부르면 주문서(코루틴 객체)만 나오고 `await` 해야 돈다. 버리면 `never awaited` 경고.
- ★★★ Kotlin 은 그 「버리기」가 **원리상 안 생긴다** — `suspend` 를 부를 수 있는 자리가 이미 코루틴 안이고, 부르면 끝까지 기다린다(5번). 「따로 돌리기」는 **라이브러리의 `launch`** 가 한다.
- ★ C# 은 이 문서가 재지 않았다 — C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **40번**이 서면 대조한다.

### 10. **컴파일러** — 호출 규칙(2번) · CPS 서명과 상태 기계(1번) · **라이브러리** — `launch`·`async`·`runBlocking`·`delay`·`yield`·`coroutineScope`(3\~6번) · §6 「**Kotlin은 언어에 최소만 넣고 나머지를 라이브러리(`kotlinx.coroutines`)에 남겼고**」

**왜 그런가**

- ★★ stdlib 에 있는 것은 `Continuation`·`COROUTINE_SUSPENDED` 같은 **바닥 부품**뿐이다(7번의 발췌). 스레드에 올리고 줄 세우고 취소하는 것은 **kotlinx-coroutines 1.11.0 의 구현**이다 — 판이 바뀌면 3\~6번은 다시 돌려야 한다.
- ★ 그래서 이 문서는 로그 순서를 **언어 보장으로 적지 않았다.**

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
===== javap -v -cp kotlinx-coroutines-core-jvm-1.10.2.jar kotlinx.coroutines.Job | grep -E '^ +mv=' =====
      mv=[2,1,0]
(exit 0)
```

★ **흔들리는 칸과 안 흔들리는 칸**

| 흔들린다 | 안 흔들린다 |
|---|---|
| ★ **걸린 시간** — 칸으로 안 만들었다(`form52` 의 참/거짓만) | `javap` 출력 · 호출 규칙 격자 · 진단 문구 |
| ★ **라이브러리 판** — 1.11.0 이 아니면 다시 돌려라 | 순서 로그 — 단일 스레드 · 셋은 다섯 판 되풀이에서도 해시가 안 갈렸다 |
| | 스레드 수 · `Thread.State` · 모든 **종료 코드** |

> 근거 — 캡처 스크립트를 처음부터 다시 돌려 **블록 전체를 대조**했다.
>
> 실측 — `capture.sh blocks` 와 `capture.sh blocks-recheck` 를 처음부터 따로 돌려 `normalize-shaky.py` 로 대조했다 —\
> **블록 74개 · 동일 74 · 흔들린 칸 0 · ★고칠 것 0**(50\~53 네 주제를 한 캡처로 받았다). 추가한 정규화 규칙은 **없다**.

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `cps52.kt` | ★★★ CPS 서명 · 상태 기계 클래스 · `label` · `tableswitch` · `COROUTINE_SUSPENDED` | `kotlinc` → `ls` → `javap -p` · `javap -c`(전부 받은 뒤 `grep`) |
| `call52.kt` · `grid52.py` | ★★★ 호출 규칙 9탐침 | 스크립트가 컴파일 · 진단을 줄마다 읽는다 + 에러 전문 |
| `threads52.kt` | ★★ 스레드 id 집합 크기 · `activeCount` | `kotlinc` → `java` |
| `interleave52.kt` · `order52.kt` · `await52.kt` | ★★ 끼어들기 · 부른 순간 · `await` 뒤 | `kotlinc` → `java` + 다섯 판 되풀이 해시 |
| `block52.kt` | ★★ `runBlocking` 중 main 의 상태 | 감시 스레드가 150ms 에 `main.state` 를 읽는다 |
| stdlib 소스 jar | `COROUTINE_SUSPENDED` · `CancellationException` 별칭 | `unzip` → `sed -n` |
| `form52.kt` | 형태 한 벌(시간은 참/거짓) | `kotlinc` → `java` |

**구현 의존 항목** — 상태 기계 클래스·필드 이름 · 로그 순서 · 스레드 수 — 이 컴파일러 판과 **라이브러리 판**의 산출물이다.\
반면 **호출 규칙**(언어) · **`Continuation` 인자와 `COROUTINE_SUSPENDED`**(stdlib 계약) 은 **계약**이다.

**★ 던져 봤더니 예상과 달랐던 것 — 네 건**

1. ★★★ **호출 규칙의 진단이 한 종이 아니라 두 종이었다** — 일반 함수 몸통과 일반 람다가 문구가 다르다. 문구도 「`should be called only from`」이 아니라 「**`can only be called from`**」이고, 함수 이름 자리에 **서명 전체**(`'suspend fun f(x: Int): Int'`)가 들어간다.
2. ★★ **중단점이 없는 `suspend` 함수도 서명이 바뀐다** — 상태 기계 클래스만 안 생긴다.
3. ★★ **`launch { }` 는 몸통을 바로 안 돌린다** — 부모가 멈출 때까지 0줄. `UNDISPATCHED` 라야 그 자리에서 돈다.
4. ★ **gradle 배포본의 1.10.2 보다 새 판(1.11.0)이 gradle 캐시에 있었다** — 그 판을 썼다(53번 주제가 1.10.2 로 한 번 대조한다).
