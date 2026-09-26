# kotlin/syntax/55 — `Flow` — 콜드 스트림·연산자·`collect` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러는 **kotlinc 2.4.20 (JRE 21.0.5)** · Temurin **JDK 21.0.5** · **kotlinx-coroutines 1.11.0** 에서 실제로 얻었다.
> ★★ 아래 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적은 자리가 없다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ `[1]`\~`[3]` 사이는 **비었다** · `collect` 마다 **몸통 네 줄이 다시** · **`got 10` 이 먼저**

**출력**

```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar cold55.kt -d o55c =====
(exit 0)
===== java -cp o55c:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Cold55Kt =====
[1] build
[2] built, not collected yet
[3] first collect
  body starts
  map 1
  got 10
  body after emit
[4] second collect
  body starts
  map 1
  got 10
  body after emit
[5] end
(exit 0)
```

**왜 그런가**

- ★★★ `flow { }` 와 `.map { }` 는 **만드는 법을 쥔 객체**만 돌려준다 — 몸통은 `collect` 가 불려야 돈다. 그래서 `[1]`·`[2]`·`[3]` 이 붙어서 찍혔다.
- ★★★ 두 번째 `collect` 는 **몸통을 처음부터 다시** 돈다(`body starts` 두 번) — 결과를 기억해 두지 않는다.
- ★★ `emit(1)` 은 **하류(`map` → 모으는 람다)를 그 자리에서 부르고**, 그것이 끝나야 돌아온다 — 그래서 `got 10` 뒤에 `body after emit`.

### 2. ★★★ 호출 수 — **`Flow` 와 `Sequence` 는 `0 / 4` 로 같고, `List` 와는 `3 / 4` 에서 갈렸다** · 순서 — `List` 만 `by-stage`, 나머지는 전부 `by-element`(갈린 칸 `4 / 4` · `0 / 4`)

**출력**

```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar grid55.kt -d o55g =====
(exit 0)
===== java -cp o55g:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Grid55Kt =====
chain	shape	result	calls	order
map>filter>take2	List	[20, 30]	m=6 f=6	by-stage
map>filter>take2	Sequence	[20, 30]	m=3 f=3	by-element
map>filter>take2	Flow	[20, 30]	m=3 f=3	by-element
onEach>map>toList	List	[10, 20, 30, 40, 50, 60]	p=6 m=6	by-stage
onEach>map>toList	Sequence	[10, 20, 30, 40, 50, 60]	p=6 m=6	by-element
onEach>map>toList	Flow	[10, 20, 30, 40, 50, 60]	p=6 m=6	by-element
filter>take2>map	List	[20, 30]	f=6 m=2	by-stage
filter>take2>map	Sequence	[20, 30]	f=3 m=2	by-element
filter>take2>map	Flow	[20, 30]	f=3 m=2	by-element
map>onEach>filter>first	List	[20]	m=6 p=6 f=6	by-stage
map>onEach>filter>first	Sequence	[20]	m=2 p=2 f=2	by-element
map>onEach>filter>first	Flow	[20]	m=2 p=2 f=2	by-element
chains where Flow and List differ in calls: 3 / 4
chains where Flow and Sequence differ in calls: 0 / 4
chains where Flow and List differ in order: 4 / 4
chains where Flow and Sequence differ in order: 0 / 4
(exit 0)
```

**왜 그런가**

- ★★★ `Flow` 도 **원소 하나를 사슬 끝까지** 보낸 뒤 다음 원소를 낸다 — `emit` 이 하류를 그 자리에서 부르기 때문이다(1번). 그래서 `take(2)`·`first()` 에서 **앞쪽이 줄고**(`m=3 f=3` · `m=2 p=2 f=2`), 수가 `Sequence` 와 한 칸도 안 갈린다.
- ★★ `onEach>map>toList` 는 끝이 전부를 모으므로 **세 모양 모두 `p=6 m=6`** — 호출 수로는 안 갈린 유일한 사슬이다. 그래도 **순서는 갈린다**(`List` 는 `p` 여섯 뒤 `m` 여섯).
- ★ `List` 는 단계마다 리스트를 다 만든 뒤 다음 단계로 가므로 늘 `by-stage` 다([47번 주제](../47-sequences-lazy-evaluation/) (2)).

### 3. ★★ `[a]` 는 `emit 1`·`emit 2` 뒤 **`AbortFlowException` 이 잡히고** `upstream finally` · `[b]` 는 `emit 1` 하나 뒤 같은 모양 · `[c]` 는 다섯 번 `emit` 뒤 `loop finished`·`upstream finally`(잡힌 것 없음)

**출력**

```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar take55.kt -d o55t =====
(exit 0)
===== java -cp o55t:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Take55Kt =====
[a] take(2).toList()
  emit 1
  emit 2
  caught in upstream: kotlinx.coroutines.flow.internal.AbortFlowException
  message: Flow was aborted, no more elements needed
  is CancellationException: true
  upstream finally
  result [1, 2]
[b] first()
  emit 1
  caught in upstream: kotlinx.coroutines.flow.internal.AbortFlowException
  message: Flow was aborted, no more elements needed
  is CancellationException: true
  upstream finally
  result 1
[c] toList()
  emit 1
  emit 2
  emit 3
  emit 4
  emit 5
  loop finished
  upstream finally
  result [1, 2, 3, 4, 5]
(exit 0)
```

**왜 그런가**

- ★★★ `take(2)` 는 두 번째 값을 하류에 내준 **직후** 상류의 `emit` 안으로 `AbortFlowException` 을 던진다 — 메시지 `Flow was aborted, no more elements needed` · `CancellationException` 이다. 그래서 `emit 3` 과 `loop finished` 가 없고 **`finally` 는 돈다.**
- ★★ `first()` 도 같은 수단으로 멈춘다. `toList()` 는 멈출 까닭이 없어 몸통이 끝까지 돈다.
- ★ 이 예외 클래스는 **`internal`** 이다 — 라이브러리 계약은 KDoc 의 「`the original flow is cancelled`」까지다(2-summary (3)).

### 4. ★★ `fdelay55.kt` 는 **`[1, 2]`** · `sdelay55.kt` 는 **컴파일 에러**(「`restricted suspending functions can invoke member or extension suspending functions only on their restricted coroutine scope.`」 · `5:5` · `exit 1`)

**출력**

```kotlin
// fdelay55.kt
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.runBlocking

val f = flow {
    emit(1)
    delay(10)
    emit(2)
}

fun main() = runBlocking {
    println(f.toList())
}
```

```kotlin
// sdelay55.kt
import kotlinx.coroutines.delay

val s = sequence {
    yield(1)
    delay(10)
    yield(2)
}

fun main() {
    println(s.toList())
}
```

```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar fdelay55.kt -d o55d =====
(exit 0)
===== java -cp o55d:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Fdelay55Kt =====
[1, 2]
(exit 0)
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar sdelay55.kt -d o55s =====
sdelay55.kt:5:5: error: restricted suspending functions can invoke member or extension suspending functions only on their restricted coroutine scope.
    delay(10)
    ^^^^^
(exit 1)
```

**왜 그런가**

- ★★★ `flow { }` 의 람다는 **보통의 `suspend` 람다**라 `delay` 를 부를 수 있다.
- ★★★ `sequence { }` 의 수신자 `SequenceScope` 에는 **`@RestrictsSuspension`** 이 붙어 있어, 그 안에서는 `yield` 같은 **`SequenceScope` 의 멤버·확장 `suspend` 함수만** 부를 수 있다. ★ 이 문구는 [52번 주제](../52-coroutine-basics-suspend-scope-launch-async/)가 찍은 호출 규칙 진단 두 종과 **다른 세 번째 진단**이다 — 「`suspend` 가 아닌 곳에서 불렀다」가 아니라 「**제한된** `suspend` 안에서 불렀다」.

### 5. ★★ `[a]` 는 **`java.lang.IllegalStateException: Flow invariant is violated: …`**(`got` 줄 없음) · `[b]` 는 **`emit`·`map1` 이 `DefaultDispatcher`, `map2`·`collect` 가 `main`**

**출력**

```kotlin
// ctx55.kt
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*

fun tn(): String = Thread.currentThread().name.substringBefore("-worker")
// 찍는 글자 안의 객체 해시(@16진수)는 실행마다 바뀐다 — 그 칸만 가려 찍는다.
fun hideHash(m: String): String = m.replace(Regex("@[0-9a-f]+"), "@<hash>")

fun main() = runBlocking {
    println("[a] withContext inside flow { }")
    val fa = flow {
        withContext(Dispatchers.IO) { emit(1) }
    }
    try {
        fa.collect { println("  got $it") }
    } catch (e: Throwable) {
        println(hideHash("${e::class.java.name}: ${e.message}"))
    }

    println("[b] flowOn(Dispatchers.IO)")
    flow { emit("emit on ${tn()}") }
        .map { "$it | map1 on ${tn()}" }
        .flowOn(Dispatchers.IO)
        .map { "$it | map2 on ${tn()}" }
        .collect { println("  $it | collect on ${tn()}") }
}
```

```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar ctx55.kt -d o55x =====
(exit 0)
===== java -cp o55x:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Ctx55Kt =====
[a] withContext inside flow { }
java.lang.IllegalStateException: Flow invariant is violated:
		Flow was collected in [BlockingCoroutine{Active}@<hash>, BlockingEventLoop@<hash>],
		but emission happened in [DispatchedCoroutine{Active}@<hash>, Dispatchers.IO].
		Please refer to 'flow' documentation or use 'flowOn' instead
[b] flowOn(Dispatchers.IO)
  emit on DefaultDispatcher | map1 on DefaultDispatcher | map2 on main | collect on main
(exit 0)
```

**왜 그런가**

- ★★★ `Flow` 는 **모으는 쪽의 문맥에서 돈다**는 속성(문맥 보존)을 라이브러리가 `emit` 마다 검사한다. `withContext(Dispatchers.IO)` 안의 `emit` 은 문맥이 달라 `IllegalStateException` — 문구가 스스로 「`use 'flowOn' instead`」라고 권한다.
- ★★★ `flowOn(Dispatchers.IO)` 는 **자기 위쪽**(`flow { }`·`map1`)만 옮긴다. 아래쪽(`map2`·`collect`)은 `runBlocking` 의 `main` 에 남는다.
- ★ 문구 안의 `@<hash>` 는 프로그램이 가린 칸이다 — 실행마다 바뀌는 객체 해시다.

### 6. ★ `0` · `2, 0` · `2` · `true` · `[]` · `1`

**출력**

```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar hot55.kt -d o55h =====
(exit 0)
===== java -cp o55h:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Hot55Kt =====
cold: body runs with no collector = 0
state: value with no collector = 2, subscribers = 0
state: a collector arriving now first sees 2
shared: tryEmit with no collector returns true
shared: replayCache after that = []
cold: body runs after one collect = 1
(exit 0)
```

**왜 그런가**

- ★★ 콜드(`flow { }`)는 모으는 쪽이 없으면 몸통 **0회**, 한 번 모은 뒤에야 **1회**다.
- ★★ `MutableStateFlow` 는 모으는 쪽이 0(`subscribers = 0`)이어도 **값 `2` 를 쥐고 있고**, 나중에 온 수집자는 그 값부터 본다 — **값이 흐름 바깥에 산다**(핫).
- ★ `MutableSharedFlow()`(재생 0)의 `tryEmit` 은 `true` 를 돌려주지만 `replayCache` 가 `[]` — 받을 쪽이 없어 **값이 그대로 사라졌다.**

### 7. KDoc 「`Intermediate operations do not execute any code in the flow … This is known as a _cold flow_ property.`」 · 두 번째 `collect` 는 「`can be collected repeatedly and triggers execution of the same code every time it is collected`」

- ★★★ 중간 연산은 **사슬을 세우고 곧바로 돌아올 뿐**이라고 KDoc 이 적는다 — 1번의 `[1]`\~`[3]` 사이가 빈 것이 그 관찰이다.
- ★★ 「모을 때마다 같은 코드를 실행한다」가 콜드 스트림의 정의이므로 두 번째 `collect` 가 몸통을 다시 도는 것이 맞다. ★ 다만 같은 KDoc 이 「`The Flow interface does not carry information whether a flow is a _cold_ stream … or … _hot_`」 — **타입으로는 구분되지 않는다**(6번의 `StateFlow` 도 `Flow` 다).
- ★ 이것은 **라이브러리 계약**이다 — 컴파일러가 보장하는 것이 아니다.

### 8. `Flow` 는 **생산자가 하류를 부르는(push) 구조**라 멈출 권한이 상류에 있다 — 그래서 **`emit` 안으로 `CancellationException`(`AbortFlowException`)을 던져** 상류 호출 스택을 거슬러 빠져나온다

- ★★★ `Sequence` 는 **소비자가 반복자를 당기는(pull)** 쪽이라 `take` 가 더 안 당기면 그만이다. `Flow` 는 상류의 루프가 `emit` 을 부르고, `emit` 이 하류를 부르는 구조다(1번의 `got 10` → `body after emit` 순서). 하류는 **상류 루프 한가운데에서** 불리고 있으므로, 멈추려면 그 호출을 **예외로 끊는** 수밖에 없다.
- ★★ 그 예외가 `CancellationException` 이라 상류의 `finally` 는 돌고(3번), **보통의 예외 처리에서는 「취소」로 취급**된다.

```text
===== sed -n '42,72p' commonMain/flow/operators/Limit.kt =====
/**
 * Returns a flow that contains first [count] elements.
 * When [count] elements are consumed, the original flow is cancelled.
 * Throws [IllegalArgumentException] if [count] is not positive.
 */
public fun <T> Flow<T>.take(count: Int): Flow<T> {
    require(count > 0) { "Requested element count $count should be positive" }
    return flow {
        val ownershipMarker = Any()
        var consumed = 0
        try {
            collect { value ->
                // Note: this for take is not written via collectWhile on purpose.
                // It checks condition first and then makes a tail-call to either emit or emitAbort.
                // This way normal execution does not require a state machine, only a termination (emitAbort).
                // See "TakeBenchmark" for comparision of different approaches.
                if (++consumed < count) {
                    return@collect emit(value)
                } else {
                    return@collect emitAbort(value, ownershipMarker)
                }
            }
        } catch (e: AbortFlowException) {
            e.checkOwnership(owner = ownershipMarker)
        }
    }
}

private suspend fun <T> FlowCollector<T>.emitAbort(value: T, ownershipMarker: Any) {
    emit(value)
    throw AbortFlowException(ownershipMarker)
(exit 0)
===== sed -n '9,11p' jvmMain/flow/internal/FlowExceptions.kt =====
internal actual class AbortFlowException actual constructor(
    @JvmField @Transient actual val owner: Any
) : CancellationException("Flow was aborted, no more elements needed") {
(exit 0)
```

### 9. 모으는 쪽에는 **예외가 아무것도 안 나오고 `[1]`** — 안에서는 `AbortFlowException` 과 **「`Flow exception transparency is violated`」 `IllegalStateException`** 이 둘 다 상류의 `catch` 에 **삼켜졌다**

**출력**

```kotlin
// swallow55.kt
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.runBlocking

// 상류가 emit 이 던진 것을 잡고 다음 값을 계속 내보낸다
val upB = flow {
    for (i in 1..2) {
        try {
            emit(i)
        } catch (e: Throwable) {
            println("  upstream caught ${e::class.simpleName}")
            println("    message: ${e.message}")
        }
    }
}

fun main() = runBlocking {
    try {
        println("  result ${upB.take(1).toList()}")
    } catch (e: IllegalStateException) {
        println(e::class.java.name)
        println(e.message)
    }
}
```

```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar swallow55.kt -d o55w =====
(exit 0)
===== java -cp o55w:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Swallow55Kt =====
  upstream caught AbortFlowException
    message: Flow was aborted, no more elements needed
  upstream caught IllegalStateException
    message: Flow exception transparency is violated:
    Previous 'emit' call has thrown exception kotlinx.coroutines.flow.internal.AbortFlowException: Flow was aborted, no more elements needed, but then emission attempt of value '2' has been detected.
    Emissions from 'catch' blocks are prohibited in order to avoid unspecified behaviour, 'Flow.catch' operator can be used instead.
    For a more detailed explanation, please refer to Flow documentation.
  result [1]
(exit 0)
```

**왜 그런가**

- ★★★ 첫 번째 `catch` 는 `take` 의 「그만」(`AbortFlowException`)을 잡았다. 상류가 이어서 `emit(2)` 하자 라이브러리가 **「`Emissions from 'catch' blocks are prohibited`」** 라며 `IllegalStateException` 을 던졌는데, 그것도 **같은 `catch`** 가 잡았다. 루프가 끝나 몸통이 정상 종료했고 결과는 `[1]`.
- ★★ **규칙 위반이 났는데 바깥에 아무 흔적이 없다** — 무음 실패다. 상류가 연결을 들고 있었다면 「그만」 뒤에도 계속 일했을 것이다. 에러 문구가 권하는 길은 `Flow.catch` 연산자다. `CancellationException` 을 잡아 삼키는 일반론은 [53번 주제](../53-structured-concurrency-job-cancellation-exceptions/).

### 10. 4번은 **컴파일 시점에 컴파일러**(`@RestrictsSuspension` · `exit 1`)가 · 5번은 **실행 시점에 라이브러리**(`SafeCollector` 의 검사 · 컴파일은 `exit 0`)가 정했다

- ★★★ 4번의 잘못은 **빌드가 깨져** 배포 전에 드러난다. 5번의 잘못은 컴파일을 통과하고 **그 `emit` 이 실제로 불린 순간** 드러난다 — 그 경로를 안 타는 테스트로는 못 잡는다.
- ★★ 그래서 `Flow` 의 규칙 중 **언어가 지키는 것은 「`suspend` 를 어디서 부르나」 한 갈래뿐**이다. 콜드·문맥 보존·예외 투명성은 **라이브러리 계약**이고, 9번처럼 검사가 있어도 **삼켜지면 안 보인다.**

```text
===== unzip -o -q kotlin-stdlib-sources.jar commonMain/kotlin/collections/SequenceBuilder.kt commonMain/kotlin/coroutines/Continuation.kt =====
(exit 0)
===== sed -n '43p;87,89p' commonMain/kotlin/collections/SequenceBuilder.kt =====
public fun <T> sequence(@BuilderInference block: suspend SequenceScope<T>.() -> Unit): Sequence<T> = Sequence { iterator(block) }
@RestrictsSuspension
@SinceKotlin("1.3")
public abstract class SequenceScope<in T> internal constructor() {
(exit 0)
===== sed -n '29,37p' commonMain/kotlin/coroutines/Continuation.kt =====
/**
 * Classes and interfaces marked with this annotation are restricted when used as receivers for extension
 * `suspend` functions. These `suspend` extensions can only invoke other member or extension `suspend` functions on this particular
 * receiver and are restricted from calling arbitrary suspension functions.
 */
@SinceKotlin("1.3")
@Target(AnnotationTarget.CLASS)
@Retention(AnnotationRetention.BINARY)
public annotation class RestrictsSuspension
(exit 0)
```

```text
===== sed -n '68,75p' commonMain/flow/Flow.kt =====
 * ### Context preservation
 *
 * The flow has a context preservation property: it encapsulates its own execution context and never propagates or leaks
 * it downstream, thus making reasoning about the execution context of particular transformations or terminal
 * operations trivial.
 *
 * There is only one way to change the context of a flow: the [flowOn][Flow.flowOn] operator
 * that changes the upstream context ("everything above the `flowOn` operator").
(exit 0)
===== sed -n '40,52p' commonMain/flow/Builders.kt =====
 *
 * ```
 * flow {
 *     emit(1) // Ok
 *     withContext(Dispatcher.IO) {
 *         emit(2) // Will fail with ISE
 *     }
 * }
 * ```
 *
 * If you want to switch the context of execution of a flow, use the [flowOn] operator.
 */
public fun <T> flow(block: suspend FlowCollector<T>.() -> Unit): Flow<T> = SafeFlow(block)
(exit 0)
===== sed -n '82,88p' commonMain/flow/internal/SafeCollector.common.kt =====
    if (result != collectContextSize) {
        error(
            "Flow invariant is violated:\n" +
                    "\t\tFlow was collected in $collectContext,\n" +
                    "\t\tbut emission happened in $currentContext.\n" +
                    "\t\tPlease refer to 'flow' documentation or use 'flowOn' instead"
        )
(exit 0)
===== sed -n '160,166p' jvmMain/flow/internal/SafeCollector.kt =====
         */
        error("""
            Flow exception transparency is violated:
                Previous 'emit' call has thrown exception ${exception.e}, but then emission attempt of value '$value' has been detected.
                Emissions from 'catch' blocks are prohibited in order to avoid unspecified behaviour, 'Flow.catch' operator can be used instead.
                For a more detailed explanation, please refer to Flow documentation.
            """.trimIndent())
(exit 0)
```

### 11. 호출 수와 순서는 **`Sequence` 와 같다**(2번의 `0 / 4`) · 두 번째로 모으면 **`Flow` 는 몸통을 다시 돌고**, Python 제너레이터 **객체는 `[]`**(소진), Java `Stream` 은 **다시 못 쓴다**

- ★★★ `Sequence` 도 원소별이고 끝 연산이 앞쪽을 줄인다([47번 주제](../47-sequences-lazy-evaluation/) (1)(2)) — `Flow` 는 같은 모양에 **중단(`delay`)과 실행 문맥**을 더했다(4번·5번). 멈추는 법은 다르다(8번).
- ★★ **두 번째로 모을 때** — `Flow` 는 **만드는 법**이라 처음부터 다시 돈다(1번). Python 제너레이터는 **상태를 가진 객체**라 한 번 소진되면 두 번째 반복이 빈다([Python 17번](../../../python/syntax/17-generators-yield/)). Java `Stream` 은 한 번 흐르면 끝이다([Java 44번](../../../java/syntax/44-stream-creation/)). ★ `sequence { }` 는 `Flow` 와 같이 **다시 돈다**([47번 주제](../47-sequences-lazy-evaluation/) (5)).

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
```

★ **흔들리는 칸과 안 흔들리는 칸**

| 흔들린다 | 안 흔들린다 |
|---|---|
| ★ 에러 문구 안의 **객체 해시** — `ctx55.kt` 가 `@<hash>` 로 가려 찍는다(정규화 규칙은 더하지 않았다) | 격자 12행 · 호출 수 · 순서 칸 · 갈린 칸 수 |
| ★ 스레드 이름 끝의 번호 — `-worker` 앞만 찍는다 | 콜드 · `take` · 삼키기 · 핫 스트림 로그 — 순서가 걸린 셋은 다섯 판 되풀이에서 해시가 안 갈렸다 |
| ★ **라이브러리 판** — 1.11.0 이 아니면 다시 돌려라 | 소스 발췌(줄 번호째) · 진단 문구 · 모든 **종료 코드** |

```text
===== for i in 1 2 3 4 5; do java -cp o55g:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Grid55Kt | md5sum; java -cp o55t:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Take55Kt | md5sum; java -cp o55x:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Ctx55Kt | md5sum; done | sort | uniq -c =====
      5 199b1b92f1b1163739c3a0c3db08c5d8  -
      5 3a4563030b0e9e4926fb05c1b3e4adbd  -
      5 bc4dc775d8f9ac585a8264154d5373af  -
(exit 0)
```

- ★ 순서 로그 셋(`grid55` · `take55` · `ctx55`)을 다섯 판씩 돌려 **출력 전체의 해시**를 센 것이다 — 서로 다른 해시가 **셋**, 각각 **`5`** 번. `ctx55` 는 디스패처 스레드를 타는데도 갈리지 않았다(스레드 번호를 안 찍기 때문이다).

> 근거 — 캡처 스크립트를 처음부터 다시 돌려 **블록 전체를 대조**했다.
>
> 실측 — `capture.sh blocks` 와 `capture.sh blocks-re` 를 처음부터 따로 돌려 `normalize-shaky.py` 로 대조했다 — **블록 109개 · 동일 109 · 흔들린 칸 0 · ★고칠 것 0**(54\~58 다섯 주제를 한 캡처로 받았다 — 이 주제 몫은 출력 14 · 소스 9 · 환경 5). 추가한 정규화 규칙은 없다.

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `cold55.kt` | ★★ 콜드 — 만들기만 하면 0줄 · 두 번 모으면 두 번 · `emit` 과 하류의 순서 | `kotlinc` → `java` |
| `grid55.kt` | ★★★ 호출 수 격자 — 사슬 4 × 모양 3 | `kotlinc` → `java` (칸 수 검사·갈린 칸 수는 프로그램이 센다) + 다섯 판 되풀이 |
| `take55.kt` | ★★ `take`·`first`·`toList` 에서 상류가 받는 것 | `kotlinc` → `java` + 다섯 판 되풀이 |
| `swallow55.kt` | ★★ 상류가 삼키면 | `kotlinc` → `java` |
| `fdelay55.kt` · `sdelay55.kt` | ★★ 두 몸통 안의 `delay` | `kotlinc` → `java` · `kotlinc`(에러) |
| `ctx55.kt` | ★★ `withContext` 위반 · `flowOn` 의 범위 | `kotlinc` → `java` + 다섯 판 되풀이 |
| `hot55.kt` | ★ 콜드 대 `StateFlow`·`SharedFlow` | `kotlinc` → `java` |
| 코루틴 소스 jar(`Flow.kt` · `Builders.kt` · `Limit.kt` · `FlowExceptions.kt` · `SafeCollector*.kt`) · stdlib 소스 jar(`SequenceBuilder.kt` · `Continuation.kt`) | 콜드 · 문맥 보존 KDoc · `take` 구현 · 두 에러 문구 · `@RestrictsSuspension` | `unzip` → `sed -n` |
| `form55.kt` | 형태 한 벌 | `kotlinc` → `java` |

**구현 의존 항목** — `AbortFlowException` 이라는 클래스 이름과 메시지 · `emitAbort` 가 값을 내준 **뒤** 던지는 것 · `SafeCollector` 의 두 에러 문구 · `DispatchedCoroutine`·`BlockingEventLoop` 같은 문맥 원소 이름 — 이 라이브러리 판의 산출물이다.\
반면 **콜드 · 문맥 보존 · `take` 가 원래 흐름을 취소한다**는 **라이브러리 계약(KDoc)** 이고, `sequence { }` 안 `delay` 금지는 **언어(컴파일러)** 다.

**★ 던져 봤더니 예상과 달랐던 것 — 세 건**

1. ★★★ **`sequence { }` 안 `delay` 의 진단은 52번 주제의 호출 규칙 진단이 아니었다** — `@RestrictsSuspension` 에서 오는 **세 번째 문구**(「`restricted suspending functions …`」)였다.
2. ★★ **상류가 `catch (e: Throwable)` 로 삼키면 예외 투명성 위반마저 바깥에 안 나왔다** — 라이브러리가 `IllegalStateException` 을 던지는 것까지는 예상대로였지만, 그것이 **같은 `catch` 로 다시 들어가** 흔적 없이 `[1]` 로 끝났다.
3. ★ **`Flow` 와 `Sequence` 는 호출 수만이 아니라 순서까지 `0 / 4`** — 비동기라는 이름과 달리 이 격자(단일 스레드 `runBlocking`)에서는 **한 글자도 다르지 않았다.**
