# kotlin/syntax/55 — `Flow` — 콜드 스트림·연산자·`collect` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — **`kotlinx-coroutines-core-jvm` 1.11.0 의 소스 jar**(`Flow.kt` 의 KDoc — 「cold flow」·「Context preservation」 · `Builders.kt` 의 `flow { }` · `operators/Limit.kt` 의 `take` · `internal/FlowExceptions.kt` · `internal/SafeCollector*.kt` 의 두 에러 문구)와 **stdlib 소스 jar 2.4.20**(`SequenceBuilder.kt` · `Continuation.kt` 의 `@RestrictsSuspension`). ★ 공식 문서 페이지는 **이 작업에서 열지 못했다**(외부 네트워크를 쓰지 않았다) — 인용은 전부 소스 jar 의 KDoc 이다.
> **실행 검증** — 이 문서의 모든 출력·에러는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `java` 에서 실제로 얻었다.\
> `kotlinc` 9회 · `java` 8회 + 순서가 걸린 셋(`grid55` · `take55` · `ctx55`)을 다섯 판씩 되풀이한 15회 · 소스 jar 발췌 9곳.\
> ★★★ **라이브러리 판 — `kotlinx-coroutines-core-jvm` 1.11.0**(이 머신의 gradle 캐시에 있던 판 중 가장 새 것 · 매니페스트 `Implementation-Version: 1.11.0`). `Flow`·`flow { }`·`map`·`take`·`flowOn`·`StateFlow` 는 **전부 이 라이브러리의 것**이다 — 언어 기능이 아니다.\
> ★★ 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적지 않았다. **「갈린 칸 N / M」은 격자 프로그램이 스스로 센 것**이다.
> **버전** — `@RestrictsSuspension`·`SequenceScope` 는 stdlib 소스에 **`@SinceKotlin("1.3")`**((4)). `Flow` 쪽의 도입 판은 **이 판의 소스에서 확인하지 않았다** — 1.11.0 에서 돌렸다는 것만 말한다.
> **경계** — ★★★ **같은 「끝 연산 전에는 아무 일도 안 한다」의 동기판**(`Sequence` — 호출 수 격자 · 단계별 대 원소별 · 두 번 돌기)은 [47번 주제](../47-sequences-lazy-evaluation/)가 정본이다 — 여기서는 **같은 사슬을 `Flow` 열과 함께 한 격자로** 다시 센다. **`suspend` 호출 규칙**(어디서 부르면 막히나 — 진단 두 종)은 [52번 주제](../52-coroutine-basics-suspend-scope-launch-async/), **취소가 `CancellationException` 이라는 것과 그것을 삼키면 생기는 일**은 [53번 주제](../53-structured-concurrency-job-cancellation-exceptions/), **디스패처와 `withContext`** 는 [54번 주제](../54-coroutine-context-dispatchers-and-withcontext/)가 정본이다.\
> 교차 갈래 — **Python 제너레이터**의 「한 번 소진하면 끝」은 [Python 17번](../../../python/syntax/17-generators-yield/) · **JS 제너레이터**의 「불러도 본문은 안 돈다」는 [JS 20번](../../../js/syntax/20-generators/) · **비동기 이터레이터**(`for await`)는 [JS 40번](../../../js/syntax/40-async-iteration-and-for-await/) · **Java `Stream`** 의 지연과 한 번 쓰기는 [Java 44번](../../../java/syntax/44-stream-creation/)·[Java 45번](../../../java/syntax/45-intermediate-operations/) 이 쟀다 — 이 문서는 그것들을 **다시 돌리지 않았다.**
> 이 본문은 Claude 작성이다(원고 없음).

★★★ **본체는 둘째 창이다** — 「**호출 수 격자 — 사슬 넷 × (`List` · `Sequence` · `Flow`) → 람다 호출 수 · 로그 순서(단계별/원소별)**」. 첫째 창(콜드 증거 — 만들기만 하면 0줄 · 두 번 모으면 두 번)은 그 격자가 서는 **전제**다. 「빠르다·가볍다」는 **재지 않았다** — 이 문서의 수는 호출 수와 로그 순서뿐이다.

## 이 주제가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **언어 보장** | 컴파일러가 하는 것 | ★★ `sequence { }` 안에서 `delay` 가 **컴파일 에러** — 수신자 `SequenceScope` 에 붙은 **`@RestrictsSuspension`**(stdlib 선언 · 컴파일러가 강제)((4)) · `collect` 가 `suspend` 라서 코루틴 밖에서 못 부른다([52번 주제](../52-coroutine-basics-suspend-scope-launch-async/)) |
| **라이브러리 계약(kotlinx-coroutines)** | 라이브러리 KDoc 이 약속한 것 | ★★★ 「`Intermediate operations do not execute any code in the flow`」(콜드) · 「`the original flow is cancelled`」(`take`) · 「`Context preservation`」과 「`only one way to change the context of a flow: the flowOn`」 · `flow { }` 안 `withContext` 는 「`Will fail with ISE`」 — ★ **언어가 아니다** |
| **이 판의 관찰** | kotlinc 2.4.20 + kotlinx-coroutines 1.11.0 에서 이번에 본 것 | 격자의 수 · 로그 순서 · 예외 클래스 이름 `AbortFlowException` · 에러 문구 전문 · 스레드 이름의 앞머리 |

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
| **흔들린다 — 프로그램이 가려 찍었다** | ★ 에러 문구 안의 **객체 해시**(`@1a2b3c` 꼴) | `ctx55.kt` 가 `@[0-9a-f]+` 를 **`@<hash>`** 로 바꿔 찍는다 — 소스에 그 줄이 보인다. 정규화 규칙(`--rule`)은 **더하지 않았다** |
| **흔들린다 — 칸으로 안 만들었다** | ★ 스레드 이름 끝의 번호(`DefaultDispatcher-worker-N` 의 `N`) | `-worker` 앞만 찍는다 — 대조할 것은 「`main` 인가, 디스패처 스레드인가」다 |
| 안 흔들린다 | ★★ 격자 12행 · 호출 수 · 순서 칸 · 갈린 칸 수 | 람다 호출 횟수는 입력과 사슬만으로 정해진다 · `runBlocking` 한 스레드 위 |
| 안 흔들린다 | 콜드 로그 · `take` 로그 · 삼키기 로그 · 핫 스트림 값 | 단일 스레드 · 고정 입력 — 순서가 걸린 셋은 **다섯 판 되풀이**에서도 해시가 안 갈렸다((3) 끝) |
| 안 흔들린다 | 소스 발췌(줄 번호째) · 진단 문구 · 모든 종료 코드 | jar·컴파일러가 같으면 같다 |
| ★ **판에 매인다** | 라이브러리 **1.11.0** 의 동작 전부 — 특히 `AbortFlowException` 이라는 **내부 클래스 이름**과 에러 문구 | 판이 바뀌면 다시 돌려라 |

★ 근거 — 캡처 스크립트를 처음부터 두 번 돌려 **블록 전체를 대조**했다(수치는 3-answer 의 「실행 검증」).

## 한눈에 — 쉽게 말하면

**`Flow` 는 「주문을 받아야 요리를 시작하는 식당의 레시피」다.** 레시피(`flow { }`)를 적고 곁들임(`map`·`filter`)을 덧붙여도 **부엌은 조용하다.** 손님이 앉아 주문하는 순간(`collect`)에야 요리가 시작되고, **손님이 둘이면 요리도 두 번** 한다.
요리는 **접시 하나씩** 나간다 — 하나가 곁들임까지 다 거쳐 손님 앞에 놓인 뒤에야 다음 접시를 만든다(`Sequence` 와 같다). 손님이 「두 접시면 됐어요」(`take(2)`)라고 하면 **부엌에 「그만」 쪽지가 날아가고**(예외), 부엌은 그 쪽지를 받고 **정리(`finally`)** 를 한다.
그리고 이 식당은 **요리사가 부엌을 몰래 바꾸는 것**(`withContext`)을 금지한다 — 바꾸려면 **간판에 적어야**(`flowOn`) 한다.

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 레시피만 적으면 부엌은 조용 | `flow { }`·`map` 만으로는 몸통 0줄 | (1) ★ |
| 손님이 둘이면 두 번 요리 | `collect` 두 번이면 몸통도 두 번 | (1) ★ |
| 접시 하나씩 끝까지 | 원소별 — `Sequence` 와 같은 호출 수 | (2) ★ |
| 「그만」 쪽지 | `take` 가 상류에 **`AbortFlowException`** 을 던진다 | (3) ★ |
| 쪽지를 구겨 버리면 | 상류가 잡아 삼키면 **에러가 안쪽에서 사라진다** | (3) |
| 요리 중 기다릴 수 있다 | `emit` 사이 `delay` — `Sequence` 는 컴파일 에러 | (4) |
| 부엌을 몰래 바꾸면 안 된다 | `withContext` 안 `emit` → `Flow invariant is violated` | (5) ★ |
| 간판에 적으면 된다 | `flowOn` — **위쪽만** 옮긴다 | (5) |
| 뷔페(손님 없어도 차려짐) | `StateFlow`·`SharedFlow` — 핫 스트림 | (6) |

```text
   val g = flow { … emit(1) … }.map { … }        g.collect { … }            g.collect { … }
            │                                     │                          │
            ▼                                     ▼                          ▼
   (아무것도 안 돈다 — 만드는 법만 쥔다)     몸통 시작 → emit → map        몸통 다시 시작 → emit → map
                                             → 모으는 람다 → 몸통 계속     → 모으는 람다 → 몸통 계속
                                             (첫 번째 요리)                (두 번째 요리 — 처음부터)
```

## 이 주제가 답하려는 질문

1. `Flow` 는 **왜 `collect` 전에는 아무 일도 안 하나** — 그리고 두 번 모으면 무엇이 두 번 도나.
2. 연산자 사슬에서 **람다가 몇 번, 어떤 순서로** 불리나 — `List`·`Sequence` 와 무엇이 같고 무엇이 다른가.
3. `Flow` 가 `Sequence`·Java `Stream` 과 **실제로 다른 자리**는 어디인가 — 중단(`delay`) · 상류 취소 · 실행 문맥.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★ **콜드 증거(실행 로그)** | 만들기만 하면 0줄 · 두 번 모으면 두 번((1)) | 격자의 전제 |
| ★★★ **호출 수 격자(실행 · 결정적)** | 사슬 × 모양(`List`·`Sequence`·`Flow`) → 호출 수 · 순서((2)) | ★ **본체 창** — [47번 주제](../47-sequences-lazy-evaluation/) (1)(2)와 같은 창 |
| ★★ **상류 로그(`try`/`catch`/`finally`)** | `take`·`first` 가 상류에 무엇을 던지나((3)) | — |
| ★★ **컴파일러 진단** | `sequence { }` 와 `flow { }` 안의 `delay`((4)) | 언어 층의 유일한 근거 |
| ★★ **예외 문구 전문** | `flow { }` 안 `withContext` · 삼킨 뒤 다시 `emit`((3)(5)) | — |
| ★★ **소스 jar 발췌** | 콜드 · 문맥 보존 KDoc · `take` 구현 · 두 에러 문구가 적힌 줄((1)(3)(5)) | 이 편이 처음 연 파일들 |
| **인용 — 다시 안 잰다** | `Sequence` 의 두 번 돌기 · Python 제너레이터의 소진 | [47번 주제](../47-sequences-lazy-evaluation/) (5) · [Python 17번](../../../python/syntax/17-generators-yield/) |
| ★ **제5의 상태 — 창을 바꿔 물었다** | 「`take` 가 상류를 **취소**하나」를 `Job` 상태가 아니라 **상류 몸통 안에서 잡은 예외 클래스와 `finally` 로그**로 물었다 | (3) — 이 창은 **예외가 상류를 지나갔다**는 것만 보인다. 상류가 **다른 코루틴**(`channelFlow`·`buffer`)이면 그 코루틴의 취소는 이 창에 안 보인다 — 재지 않았다 |
| **부적용 — 실행 시간·메모리** | ★★★ 「`Flow` 가 `Sequence` 보다 느리다/무겁다」는 **재지 않았다** | — |

### (1) ★★ 콜드 증거 — 만들기만 하면 0줄, 두 번 모으면 두 번

**언제 쓰나** — `flow { }` 를 만들어 두고 「이미 돌고 있다」고 믿으려 할 때.

```kotlin
// cold55.kt
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.runBlocking

fun main() = runBlocking {
    println("[1] build")
    val f = flow {
        println("  body starts")
        emit(1)
        println("  body after emit")
    }
    val g = f.map { println("  map $it"); it * 10 }
    println("[2] built, not collected yet")
    println("[3] first collect")
    g.collect { println("  got $it") }
    println("[4] second collect")
    g.collect { println("  got $it") }
    println("[5] end")
}
```

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

- ★★★ **`[1]` 과 `[3]` 사이에 몸통 줄이 하나도 없다** — `flow { }` 와 `.map { }` 는 **만드는 법만 쥔 객체**를 돌려줬다. 몸통은 `collect` 가 불린 뒤에야 시작한다.
- ★★★ **`collect` 두 번이면 `body starts` 도 두 번** — 두 번째는 첫 번째 결과를 재사용하지 않고 **몸통을 처음부터 다시 돈다.** `sequence { }` 가 두 번 돌며 **두 번 계산**하던 것([47번 주제](../47-sequences-lazy-evaluation/) (5))과 같다.
- ★★ **`got 10` 이 `body after emit` 보다 먼저다** — `emit(1)` 은 값을 어디 쌓아 두는 것이 아니라 **하류(`map` → 모으는 람다)를 그 자리에서 부른다.** 모으는 람다가 끝나야 `emit` 이 돌아와 몸통이 다음 줄로 간다.
- ★ **대비** — Python 제너레이터는 만들기만 하면 몸통 0줄인 것까지 같지만 **객체가 한 번 소진되면 두 번째 반복이 `[]`** 다([Python 17번](../../../python/syntax/17-generators-yield/)). `Flow` 는 **값이 아니라 만드는 법**이라 소진이 없다. JS 제너레이터의 「불러도 본문은 안 돈다」는 [JS 20번](../../../js/syntax/20-generators/) (1).

```text
===== unzip -o -q kotlinx-coroutines-core-jvm-1.11.0-sources.jar commonMain/flow/Flow.kt commonMain/flow/Builders.kt commonMain/flow/operators/Limit.kt jvmMain/flow/internal/FlowExceptions.kt commonMain/flow/internal/SafeCollector.common.kt jvmMain/flow/internal/SafeCollector.kt =====
(exit 0)
```

```text
===== sed -n '8,14p;37,40p' commonMain/flow/Flow.kt =====
 * An asynchronous data stream that sequentially emits values and completes normally or with an exception.
 *
 * _Intermediate operators_ on the flow such as [map], [filter], [take], [zip], etc are functions that are
 * applied to the _upstream_ flow or flows and return a _downstream_ flow where further operators can be applied to.
 * Intermediate operations do not execute any code in the flow and are not suspending functions themselves.
 * They only set up a chain of operations for future execution and quickly return.
 * This is known as a _cold flow_ property.
 * The `Flow` interface does not carry information whether a flow is a _cold_ stream that can be collected repeatedly and
 * triggers execution of the same code every time it is collected, or if it is a _hot_ stream that emits different
 * values from the same running source on each collection. Usually flows represent _cold_ streams, but
 * there is a [SharedFlow] subtype that represents _hot_ streams. In addition to that, any flow can be turned
(exit 0)
```

- ★★★ **콜드는 라이브러리 KDoc 의 약속이다** — 「`Intermediate operations do not execute any code in the flow and are not suspending functions themselves. They only set up a chain of operations for future execution and quickly return. This is known as a _cold flow_ property.`」
- ★★ **「두 번 모으면 같은 코드를 또 돈다」도 KDoc 이 말한다** — 「`a _cold_ stream that can be collected repeatedly and triggers execution of the same code every time it is collected`」. ★ 다만 **「`The Flow interface does not carry information whether a flow is a _cold_ stream … or … _hot_`」** — 타입만 보고는 콜드인지 모른다((6)).

### (2) ★★★ 호출 수 격자 — `List` · `Sequence` · `Flow`

**언제 쓰나** — `Flow` 사슬에 부작용(로그·외부 호출)을 넣을 때, 그리고 `Flow` 를 「비동기 `List`」로 읽으려 할 때.

방법 — 입력 `1..6` 에 같은 사슬 넷을 세 모양으로 건다. 람다 `m`(×10)·`f`(`> 15`)·`p`(`onEach`)는 부를 때마다 센다. `order` 는 로그가 **한 단계가 원소를 다 지난 뒤 다음 단계로 가면 `by-stage`**, 아니면 `by-element` 다. 마지막 네 줄은 **`Flow` 열이 다른 모양과 갈린 사슬 수**다.

```kotlin
// grid55.kt
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.runBlocking

// 한 사슬을 세 모양(List · Sequence · Flow)으로 돌려 람다 호출 수와 로그 순서를 센다.
val log = mutableListOf<String>()
val calls = linkedMapOf<String, Int>()
fun hit(stage: String, x: Int) { log += "$stage$x"; calls[stage] = (calls[stage] ?: 0) + 1 }

fun mapF(x: Int): Int { hit("m", x); return x * 10 }
fun keepF(x: Int): Boolean { hit("f", x); return x > 15 }
fun peekF(x: Int) { hit("p", x) }

val input = (1..6).toList()

fun onList(chain: String): List<Int> = when (chain) {
    "map>filter>take2"     -> input.map(::mapF).filter(::keepF).take(2)
    "onEach>map>toList"    -> input.onEach(::peekF).map(::mapF)
    "filter>take2>map"     -> input.filter { keepF(it * 10) }.take(2).map(::mapF)
    "map>onEach>filter>first" -> listOf(input.map(::mapF).onEach(::peekF).filter(::keepF).first())
    else -> error(chain)
}

fun onSeq(chain: String): List<Int> = input.asSequence().let { s ->
    when (chain) {
        "map>filter>take2"     -> s.map(::mapF).filter(::keepF).take(2).toList()
        "onEach>map>toList"    -> s.onEach(::peekF).map(::mapF).toList()
        "filter>take2>map"     -> s.filter { keepF(it * 10) }.take(2).map(::mapF).toList()
        "map>onEach>filter>first" -> listOf(s.map(::mapF).onEach(::peekF).filter(::keepF).first())
        else -> error(chain)
    }
}

fun onFlow(chain: String): List<Int> = runBlocking {
    val f = input.asFlow()
    when (chain) {
        "map>filter>take2"     -> f.map { mapF(it) }.filter { keepF(it) }.take(2).toList()
        "onEach>map>toList"    -> f.onEach { peekF(it) }.map { mapF(it) }.toList()
        "filter>take2>map"     -> f.filter { keepF(it * 10) }.take(2).map { mapF(it) }.toList()
        "map>onEach>filter>first" -> listOf(f.map { mapF(it) }.onEach { peekF(it) }.filter { keepF(it) }.first())
        else -> error(chain)
    }
}

// 로그가 「단계별」(한 단계가 원소를 다 지난 뒤 다음 단계)인가 「원소별」인가
fun order(): String {
    val stages = log.map { it.take(1) }
    val runs = stages.zipWithNext().count { (a, b) -> a != b } + 1
    return if (runs == stages.distinct().size) "by-stage" else "by-element"
}

fun main() {
    val chains = listOf("map>filter>take2", "onEach>map>toList", "filter>take2>map", "map>onEach>filter>first")
    val shapes = listOf("List" to ::onList, "Sequence" to ::onSeq, "Flow" to ::onFlow)
    println("chain\tshape\tresult\tcalls\torder")
    val counts = mutableMapOf<Pair<String, String>, String>()
    val orders = mutableMapOf<Pair<String, String>, String>()
    for (c in chains) for ((name, run) in shapes) {
        log.clear(); calls.clear()
        val r = run(c)
        val cs = calls.entries.joinToString(" ") { "${it.key}=${it.value}" }
        val o = order()
        counts[c to name] = cs
        orders[c to name] = o
        val row = listOf(c, name, r.toString(), cs, o)
        check(row.size == 5)
        println(row.joinToString("\t"))
    }
    val m = chains.size
    val flowVsList = chains.count { counts[it to "Flow"] != counts[it to "List"] }
    val flowVsSeq = chains.count { counts[it to "Flow"] != counts[it to "Sequence"] }
    println("chains where Flow and List differ in calls: $flowVsList / $m")
    println("chains where Flow and Sequence differ in calls: $flowVsSeq / $m")
    val oList = chains.count { orders[it to "Flow"] != orders[it to "List"] }
    val oSeq = chains.count { orders[it to "Flow"] != orders[it to "Sequence"] }
    println("chains where Flow and List differ in order: $oList / $m")
    println("chains where Flow and Sequence differ in order: $oSeq / $m")
}
```

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

- ★★★ **`Flow` 와 `Sequence` 는 호출 수도 순서도 갈린 칸이 `0 / 4`** — 네 사슬 전부 같은 수 · 같은 `by-element` 다. `Flow` 도 **원소 하나가 사슬 끝까지 간 뒤** 다음 원소가 올라온다.
- ★★★ **`Flow` 와 `List` 는 호출 수가 `3 / 4` 에서 갈렸다** — 끝이 `take(2)`·`first()` 인 셋이다. `map>filter>take2` 는 `List` 가 `m=6 f=6`, `Flow` 는 **`m=3 f=3`** — 두 번째 합격(`30`)에서 멈췄다.
- ★★ **안 갈린 한 칸은 `onEach>map>toList`** — 끝이 전부를 모으면 **모든 원소가 모든 단계를 지난다**(`p=6 m=6`). [47번 주제](../47-sequences-lazy-evaluation/) (1)에서 `toList` 끝이 호출을 못 줄이던 것과 같은 모양이다. **순서는 `4 / 4` 전부 갈렸다** — `List` 는 늘 `by-stage` 다.
- ★ `filter>take2>map` 의 `m=2` — `take` **뒤**의 단계는 세 모양 모두 두 번뿐이다. 줄어드는 것은 `take` **앞**이다.

### (3) ★★ `take` 는 상류를 어떻게 멈추나 — 예외다

**언제 쓰나** — 상류가 파일·연결을 열어 두는 `Flow` 에 `take`·`first` 를 걸 때.

```kotlin
// take55.kt
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.runBlocking

val up = flow {
    try {
        for (i in 1..5) {
            println("  emit $i")
            emit(i)
        }
        println("  loop finished")
    } catch (e: Throwable) {
        println("  caught in upstream: ${e::class.java.name}")
        println("  message: ${e.message}")
        println("  is CancellationException: ${e is CancellationException}")
        throw e
    } finally {
        println("  upstream finally")
    }
}

fun main() = runBlocking {
    println("[a] take(2).toList()")
    println("  result ${up.take(2).toList()}")
    println("[b] first()")
    println("  result ${up.first()}")
    println("[c] toList()")
    println("  result ${up.toList()}")
}
```

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

- ★★★ **`take(2)` 는 두 번째 값을 내준 뒤 상류의 `emit` 안으로 예외를 던졌다** — `kotlinx.coroutines.flow.internal.AbortFlowException` · 메시지 `Flow was aborted, no more elements needed` · **`CancellationException` 이다.** 그래서 `emit 3` 이 안 찍혔고 `loop finished` 도 없으며 **`upstream finally` 는 돈다.**
- ★★ **`first()` 도 같은 예외로 멈춘다** — `emit 1` 하나 뒤 같은 세 줄. 끝까지 모으는 `toList()` 는 예외 없이 `loop finished` → `upstream finally`.
- ★★ **`Sequence` 와 다른 자리** — `Sequence` 의 `take` 는 반복자를 **더 당기지 않을 뿐**이다([47번 주제](../47-sequences-lazy-evaluation/) (2) — 로그가 그냥 끝난다). `Flow` 는 값을 **밀어 넣는**(push) 쪽이라 「그만」을 알리려면 **상류 호출 스택을 거슬러 던질 수밖에 없다.** (1)의 「`emit` 이 하류를 그 자리에서 부른다」의 뒷면이다.

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

- ★★★ **KDoc 「`When [count] elements are consumed, the original flow is cancelled.`」** — 계약은 「취소된다」까지다. **그 수단이 `AbortFlowException` 이라는 것은 구현**이다(`internal` 클래스 · `emitAbort` 가 값을 내준 **뒤** `throw`).
- ★★ `ownershipMarker` — `take` 가 **자기가 던진 예외만** 잡는다(`checkOwnership`). 사슬에 `take` 가 여럿이어도 서로의 「그만」을 가로채지 않는다.

**상류가 그 예외를 잡아 삼키면**

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

- ★★★ **바깥에는 예외가 하나도 안 나왔다 — 결과는 `[1]`** 이다. 안에서는 두 번 잡혔다 — 첫 번째는 `AbortFlowException`, 두 번째는 **다시 `emit` 한 순간 라이브러리가 던진 `IllegalStateException`**(「`Flow exception transparency is violated`」 · 「`Emissions from 'catch' blocks are prohibited`」). **그것마저 같은 `catch` 가 삼켰다.**
- ★★ 그래서 **`catch (e: Throwable)` 로 `emit` 을 감싸는 상류는 규칙 위반을 스스로 지운다** — 에러 문구가 권하는 것은 `Flow.catch` 연산자다. `CancellationException` 을 삼키는 일반론은 [53번 주제](../53-structured-concurrency-job-cancellation-exceptions/)다.

### (4) ★★ `Flow` 는 중단할 수 있다 — `Sequence` 는 컴파일이 막는다

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

- ★★★ **`flow { }` 안의 `delay` 는 된다** — `[1, 2]`. `flow { }` 의 람다가 `suspend FlowCollector<T>.() -> Unit` 이라 **아무 `suspend` 함수나** 부를 수 있다.
- ★★★ **`sequence { }` 안의 `delay` 는 컴파일 에러다** — 「`restricted suspending functions can invoke member or extension suspending functions only on their restricted coroutine scope.`」 ★ **52번 주제의 호출 규칙 진단 두 종(「코루틴이나 다른 `suspend` 함수 안에서만」 · 「코루틴 몸통 안에서만」)과 다른 세 번째 문구**다 — `sequence { }` 의 람다도 `suspend` 이지만 **제한된** `suspend` 다.

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

- ★★★ **제한의 출처는 `SequenceScope` 에 붙은 `@RestrictsSuspension`** — 「`These suspend extensions can only invoke other member or extension suspend functions on this particular receiver and are restricted from calling arbitrary suspension functions.`」 `yield` 는 `SequenceScope` 의 멤버라 되고 `delay` 는 아니라서 막힌다. **컴파일러가 강제하는 언어 층**이다.
- ★ 그래서 「`Sequence` 는 동기, `Flow` 는 비동기」의 실체는 「**`Sequence` 의 몸통은 제 반복자 말고는 멈출 곳이 없다**」는 것이다.

### (5) ★★ 실행 문맥 보존 — `withContext` 대신 `flowOn`

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

- ★★★ **`flow { }` 안에서 `withContext(Dispatchers.IO) { emit(1) }` 는 `IllegalStateException`** — 「`Flow invariant is violated: … Flow was collected in [BlockingCoroutine{Active}@<hash>, BlockingEventLoop@<hash>], but emission happened in [DispatchedCoroutine{Active}@<hash>, Dispatchers.IO]. Please refer to 'flow' documentation or use 'flowOn' instead`」. ★ **`got` 줄이 없다** — 값은 하류에 닿기 전에 막혔다.
- ★★★ **`flowOn(Dispatchers.IO)` 는 그 위쪽만 옮긴다** — `emit`·`map1` 은 디스패처 스레드(`DefaultDispatcher`)에서, `flowOn` **아래**의 `map2` 와 `collect` 는 **`main`** 에서 돌았다. 모으는 쪽의 문맥은 끝까지 안 바뀐다.

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

- ★★★ **「문맥 보존」은 라이브러리 KDoc 의 속성이다** — 「`it encapsulates its own execution context and never propagates or leaks it downstream`」 · 「`There is only one way to change the context of a flow: the [flowOn] operator that changes the upstream context`」. `flow { }` 의 KDoc 이 바로 이 예(「`emit(2) // Will fail with ISE`」)를 싣는다.
- ★★ **검사하는 자리는 `SafeCollector`** — `emit` 마다 **모으는 쪽 문맥과 지금 문맥의 원소 수**를 견주어 다르면 `error(...)`(`IllegalStateException`)를 부른다. **컴파일러는 이것을 못 막는다** — 컴파일은 통과했고(`exit 0`) 실행에서 터졌다. 디스패처 자체의 규칙은 [54번 주제](../54-coroutine-context-dispatchers-and-withcontext/)다.

### (6) ★ 핫 스트림 — 모으는 쪽이 없어도 값이 있다

```kotlin
// hot55.kt
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.runBlocking

fun main() = runBlocking {
    var runs = 0
    val cold = flow { runs++; emit(1) }
    println("cold: body runs with no collector = $runs")

    val state = MutableStateFlow(0)
    state.value = 1
    state.value = 2
    println("state: value with no collector = ${state.value}, subscribers = ${state.subscriptionCount.value}")
    println("state: a collector arriving now first sees ${state.first()}")

    val shared = MutableSharedFlow<Int>()
    println("shared: tryEmit with no collector returns ${shared.tryEmit(7)}")
    println("shared: replayCache after that = ${shared.replayCache}")

    cold.collect { }
    println("cold: body runs after one collect = $runs")
}
```

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

- ★★ **콜드(`flow { }`)는 모으는 쪽이 없으면 몸통 0회, 한 번 모으면 1회**다. **`MutableStateFlow` 는 모으는 쪽이 0인데도 `value` 가 `2`** — 값이 흐름 **바깥에** 산다. 나중에 온 수집자는 **지금 값**(`2`)부터 본다.
- ★ `MutableSharedFlow()`(재생 0)는 모으는 쪽 없이 `tryEmit` 이 `true` 를 돌려주고 **`replayCache` 가 `[]`** — 보낸 값은 **아무에게도 안 닿고 사라졌다.** 핫 스트림의 자세한 규칙(재생·버퍼·`stateIn`)은 이 문서가 재지 않았다.

## 문법 — 형태와 규칙

**형태** — 만들기(`flowOf`·`asFlow`·`flow { }`) · 중간 연산 · 끝 연산(`toList`·`collect`·`count`·`reduce`).

```kotlin
// form55.kt
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.runBlocking

fun main() = runBlocking {
    println(flowOf(1, 2, 3, 4).map { it * it }.filter { it > 1 }.toList())
    (1..3).asFlow().onEach { print("<$it>") }.collect { print(" $it ") }
    println()
    val squares = flow { for (i in 1..Int.MAX_VALUE) emit(i * i) }
    println(squares.take(4).toList())
    println(flowOf("a", "b", "c").count())
    println(flowOf(1, 2, 3).reduce { acc, x -> acc + x })
}
```

```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar form55.kt -d o55f =====
(exit 0)
===== java -cp o55f:kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar Form55Kt =====
[4, 9, 16]
<1> 1 <2> 2 <3> 3 
[1, 4, 9, 16]
3
6
(exit 0)
```

**규칙 불릿**

- **`Flow` 는 끝 연산이 있어야 돈다** — 끝 연산(`collect`·`toList`·`first`·`count`·`reduce`)은 전부 **`suspend`** 라 코루틴 안에서만 부른다((1) · [52번 주제](../52-coroutine-basics-suspend-scope-launch-async/)).
- **원소별로 흐르고 호출 수는 `Sequence` 와 같다**((2)) — `take`·`first` 로 끝나면 앞쪽이 줄고, `toList` 로 끝나면 안 준다.
- **두 번 모으면 두 번 돈다** — 결과를 여러 번 쓰려면 한 번 `toList()` 로 굳히거나 핫 스트림으로 바꾼다((1)(6)).
- **`take`·`first` 는 상류에 `CancellationException` 을 던져 멈춘다** — 상류의 `try`/`finally` 는 돌지만 **`catch` 로 삼키면 안 된다**((3)).
- **`flow { }` 안에서 문맥을 바꾸지 마라 — `flowOn` 을 써라**((5)).

## 어디서 틀리나

1. ★★★ **`flow { }` 를 만들어 두면 뒤에서 돌고 있다고 믿는다.** 아무것도 안 돈다 — 몸통 0줄((1)).
2. ★★★ **`collect` 를 두 번 부르고 한 번 계산된다고 믿는다.** 몸통이 두 번 돈다 — 네트워크를 부르면 두 번 부른다((1)).
3. ★★ **`Flow` 사슬이 `List` 처럼 단계별로 돈다고 본다.** 원소별이다 — 부작용 순서가 `List` 와 `4 / 4` 갈렸다((2)).
4. ★★ **`take` 가 상류를 「그냥 안 당긴다」고 본다.** 예외를 던진다 — 그래서 상류의 `catch (e: Throwable)` 이 그것을 잡는다((3)).
5. ★★ **상류에서 `emit` 을 `try`/`catch` 로 감싼다.** 「그만」과 규칙 위반 에러를 **둘 다 삼켜 조용히 끝난다**((3)).
6. ★★ **`flow { }` 안에서 `withContext(IO)` 로 `emit` 한다.** 컴파일은 되고 실행에서 `IllegalStateException`((5)).
7. ★ **`flowOn` 이 사슬 전체를 옮긴다고 본다.** 위쪽만 — 아래의 `map` 과 `collect` 는 원래 문맥이다((5)).
8. ★ **`sequence { }` 안에서 `delay` 를 부르려 한다.** `@RestrictsSuspension` 이 막는다 — `flow { }` 를 쓴다((4)).

## 구현 세부사항 대 언어 보장

| 항목 | 어느 쪽인가 | 근거 |
|---|---|---|
| `sequence { }` 안에서 멤버 아닌 `suspend` 함수 금지 | ★★★ **언어 보장** — `@RestrictsSuspension` 을 컴파일러가 강제 | (4) |
| 끝 연산이 `suspend` 라 코루틴 안에서만 | ★★ **언어 보장**(호출 규칙) — `Flow` 가 그 규칙 위에 서 있다 | [52번 주제](../52-coroutine-basics-suspend-scope-launch-async/) |
| 중간 연산은 코드를 안 돌린다(콜드) · 두 번 모으면 같은 코드를 또 돈다 | ★★★ **라이브러리 계약(KDoc)** | (1) |
| `take` 가 원래 흐름을 취소한다 | ★★ **라이브러리 계약(KDoc)** | (3) |
| 그 수단이 `AbortFlowException`(`CancellationException` 자손) | ★ **라이브러리 구현** — `internal` 클래스 | (3) |
| 문맥 보존 · 바꾸는 길은 `flowOn` 하나 | ★★★ **라이브러리 계약(KDoc)** — 컴파일러는 모른다 | (5) |
| 위반 검사와 두 에러 문구 | ★ **라이브러리 구현**(`SafeCollector`) — 문구는 판에 매인다 | (3)(5) |
| 호출 수가 `Sequence` 와 같다 · 원소별 | ★★ **관찰 — 그러나 결정적** — `emit` 이 하류를 그 자리에서 부르는 구조에서 따라 나온다 | (1)(2) |
| 「`Flow` 가 느리다/가볍다」 | **재지 않았다** | — |

★★ **가장 조심할 자리** — `Flow` 의 규칙 중 **컴파일러가 막는 것은 「`suspend` 를 어디서 부르나」뿐**이다. 콜드 · 문맥 보존 · 예외 투명성은 **실행에서 라이브러리가 검사하거나, 검사조차 없는 약속**이다 — (3)의 삼키기는 **에러가 났는데도 바깥으로 안 나왔다.**

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 값이 **시간에 걸쳐** 오고 사이에 기다림(`delay`·I/O)이 있다 | ★ `Flow` | (4) — `Sequence` 몸통은 기다릴 수 없다 |
| 기다림 없는 계산 사슬 | `Sequence` 또는 `List` | (2) — 호출 수가 같고 코루틴이 필요 없다 |
| 결과를 여러 번 읽는다 | 한 번 `toList()` · 또는 `StateFlow`/`SharedFlow` | (1)(6) — 콜드는 모을 때마다 다시 돈다 |
| 상류를 다른 디스패처에서 돌려야 한다 | `flowOn` | (5) — `withContext` 는 실행에서 터진다 |
| 상류의 예외를 처리하고 싶다 | `Flow.catch` 연산자 | (3) — `emit` 을 `try`/`catch` 로 감싸면 「그만」까지 삼킨다 |
| 모으는 쪽이 없어도 **현재 값**이 있어야 한다 | `StateFlow` | (6) |

## 핵심 문장

1. `Flow` 는 **만드는 법**이다 — `collect` 전에는 몸통 0줄, 두 번 모으면 **두 번** 돈다.
2. `emit` 은 하류를 **그 자리에서** 부른다 — 그래서 원소별이고, 호출 수가 `Sequence` 와 `0 / 4` 로 같으며, `List` 와는 `3 / 4` 에서 갈린다.
3. `take`·`first` 는 상류의 `emit` 안으로 **`CancellationException`(`AbortFlowException`)** 을 던져 멈춘다 — 상류 `finally` 는 돌고, `catch` 로 삼키면 규칙 위반까지 조용히 사라진다.
4. `Flow` 몸통은 **아무 `suspend` 함수나** 부른다 — `sequence { }` 는 `@RestrictsSuspension` 때문에 컴파일이 막는다.
5. 실행 문맥은 **`flowOn` 으로만** 바꾼다 — `flow { }` 안 `withContext` 는 컴파일은 되고 실행에서 `Flow invariant is violated`.

## 관련 자료

- [47번 주제](../47-sequences-lazy-evaluation/) — ★★★ **짝.** `Sequence` 의 호출 수 격자 · 단계별 대 원소별 · 두 번 돌기. 그쪽은 **동기 지연**, 여기는 **중단 가능한 지연** — 호출 수는 같고 **멈추는 법(반복자를 안 당김 대 예외)** 과 **몸통이 기다릴 수 있나**가 다르다.
- [52번 주제](../52-coroutine-basics-suspend-scope-launch-async/) — `suspend` 호출 규칙(끝 연산이 `suspend` 인 까닭) · [53번 주제](../53-structured-concurrency-job-cancellation-exceptions/) — 취소와 `CancellationException` 삼키기 · [54번 주제](../54-coroutine-context-dispatchers-and-withcontext/) — 디스패처와 `withContext`(그쪽은 **코루틴의 문맥 전환**, 여기는 **`Flow` 안에서 그것이 금지되는 이유**).
- [Python 17번](../../../python/syntax/17-generators-yield/) — 제너레이터는 만들기만 하면 0줄인 것까지 같고 **한 번 소진하면 끝**이다 — `Flow` 는 소진이 없다.
- [JS 20번](../../../js/syntax/20-generators/) · [JS 40번](../../../js/syntax/40-async-iteration-and-for-await/) — 제너레이터와 비동기 이터레이터. JS 는 **소비자가 당기는**(pull — `next()`) 쪽이고, `Flow` 는 **생산자가 하류를 부르는**(push — `emit`) 쪽이다.
- [Java 44번](../../../java/syntax/44-stream-creation/) · [Java 45번](../../../java/syntax/45-intermediate-operations/) — `Stream` 의 지연과 원소별 처리. `Stream` 은 **한 번 흐르면 끝**이고, `Flow` 는 **모을 때마다 새로** 흐른다.
- [C# 32번](../../../csharp/syntax/32-yield-return-iterators-and-deferred-execution/) — 지연 실행과 「두 번 열거하면 두 번 돈다」 — 콜드의 동기판. 비동기판(`IAsyncEnumerable`)은 C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **42번**이다.

## 용어 풀이

> **콜드 스트림(cold stream)** — 모으는 쪽이 생길 때마다 **처음부터 새로** 값을 만드는 흐름. 모으는 쪽이 없으면 아무 일도 안 한다.\
> 예: `flow { println("x"); emit(1) }` 은 `collect` 전에는 `x` 를 안 찍는다.

> **핫 스트림(hot stream)** — 모으는 쪽과 **상관없이** 값이 있거나 흐르는 것. `StateFlow`·`SharedFlow`.

> **상류 / 하류(upstream / downstream)** — 사슬에서 값이 오는 쪽 / 가는 쪽. `a.map { }.filter { }` 에서 `map` 은 `filter` 의 상류다.

> **수집(collect)** — `Flow` 의 끝 연산. 몸통을 돌리고 값을 하나씩 받는다. `suspend` 함수다.

> **`emit`** — `flow { }` 몸통에서 값을 하류로 보내는 함수. **하류가 그 값을 다 처리한 뒤에야** 돌아온다.

> **`flowOn`** — 사슬에서 **자기보다 위쪽**이 도는 실행 문맥(디스패처)을 바꾸는 연산자.

> **문맥 보존(context preservation)** — `Flow` 가 모으는 쪽의 문맥에서 돌고, 몸통이 그 문맥을 몰래 바꾸지 못하게 하는 라이브러리의 속성.

> **`@RestrictsSuspension`** — 이것이 붙은 수신자 위의 `suspend` 람다가 **그 수신자의 멤버·확장 `suspend` 함수만** 부르게 하는 stdlib 어노테이션. `sequence { }` 가 쓴다.

## 더 들어가면

- **`buffer`·`conflate`·`channelFlow`** — 상류와 하류를 **다른 코루틴**으로 떼어 원소별 흐름을 깨는 연산자. (2)의 격자가 달라질 자리 — **돌리지 않았다.**
- **`Flow.catch` 와 예외 투명성** — (3)의 에러 문구가 권하는 길. 하류의 예외는 안 잡고 상류의 것만 잡는다고 알려져 있지만 **이 판에서 재지 않았다.**
- **`stateIn`·`shareIn`** — 콜드를 핫으로 바꾸는 연산자. 몸통이 **몇 번** 도는지를 (1)의 로그 방식으로 세 볼 자리 — 돌리지 않았다.
