# kotlin/syntax/50 — `kotlin.time` — `Duration`·시간 측정 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `java`·`javap` 에서 실제로 얻었다.
> ★★ 아래 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적은 자리가 없다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **막힌 칸 6 / 25** — `Duration` 자리의 맨 숫자 넷과 `Long` 자리의 `Duration` 둘 · `pauseMs(5)` 는 **통과**(`pauses 5 ms`) · `Thread.sleep(5)`·`delay(5)` 는 **밀리초** · `Long.MAX_VALUE.nanoseconds * 2` 는 **포화하지 않는다**

**출력**

```kotlin
// unit50.kt
import kotlin.time.Duration
import kotlin.time.Duration.Companion.days
import kotlin.time.Duration.Companion.milliseconds
import kotlin.time.Duration.Companion.nanoseconds
import kotlin.time.Duration.Companion.seconds
import kotlin.time.measureTime
import kotlin.time.toJavaDuration
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking

fun pauseMs(ms: Long): String = "pauses $ms ms"

fun pauseFor(d: Duration): String = "pauses $d"

fun bucket(d: Duration): String = when {
    d < 5.milliseconds -> "under 5ms"
    d < 1.seconds -> "5ms..1s"
    else -> "1s or more"
}

val probes: List<Pair<String, () -> Any?>> = listOf(
    "Thread.sleep(5)" to { bucket(measureTime { Thread.sleep(5) }) },
    "Thread.sleep(5.seconds)" to { bucket(measureTime { Thread.sleep(5.seconds) }) },
    "Thread.sleep(5.milliseconds.toJavaDuration())" to { bucket(measureTime { Thread.sleep(5.milliseconds.toJavaDuration()) }) },
    "delay(5)" to { bucket(measureTime { runBlocking { delay(5) } }) },
    "delay(5.milliseconds)" to { bucket(measureTime { runBlocking { delay(5.milliseconds) } }) },
    "pauseMs(5)" to { pauseMs(5) },
    "pauseMs(5.seconds)" to { pauseMs(5.seconds) },
    "pauseMs(5.seconds.inWholeMilliseconds)" to { pauseMs(5.seconds.inWholeMilliseconds) },
    "pauseFor(5)" to { pauseFor(5) },
    "pauseFor(5000L)" to { pauseFor(5000L) },
    "pauseFor(5.seconds)" to { pauseFor(5.seconds) },
    "5.seconds + 300" to { 5.seconds + 300 },
    "5.seconds + 300.milliseconds" to { 5.seconds + 300.milliseconds },
    "5.seconds > 3000L" to { 5.seconds > 3000L },
    "5.seconds > 3000.milliseconds" to { 5.seconds > 3000.milliseconds },
    "5.seconds / 2.seconds" to { 5.seconds / 2.seconds },
    "90.seconds.toString()" to { 90.seconds.toString() },
    "90.seconds.toIsoString()" to { 90.seconds.toIsoString() },
    "Duration.INFINITE + 1.days" to { Duration.INFINITE + 1.days },
    "Duration.INFINITE - Duration.INFINITE" to { Duration.INFINITE - Duration.INFINITE },
    "Long.MAX_VALUE.nanoseconds" to { Long.MAX_VALUE.nanoseconds },
    "Long.MAX_VALUE.nanoseconds.inWholeDays / 365" to { Long.MAX_VALUE.nanoseconds.inWholeDays / 365 },
    "Long.MAX_VALUE.nanoseconds * 2" to { Long.MAX_VALUE.nanoseconds * 2 },
    "(Long.MAX_VALUE.nanoseconds * 2).inWholeDays / 365" to { (Long.MAX_VALUE.nanoseconds * 2).inWholeDays / 365 },
    "(Long.MAX_VALUE / 2).milliseconds * 3" to { (Long.MAX_VALUE / 2).milliseconds * 3 },
)

fun main() {
    for ((name, f) in probes) {
        val v = runCatching(f).fold({ "$it" }, { "${it::class.simpleName}: ${it.message}" })
        println("$name\t$v")
    }
}
```


```text
===== CP50=kotlinx-coroutines-core-jvm-1.11.0.jar:kotlin-stdlib.jar python3 grid50.py =====
probe	compile	value
Thread.sleep(5)	ok	5ms..1s
Thread.sleep(5.seconds)	error: none of the following candidates is applicable:	-
Thread.sleep(5.milliseconds.toJavaDuration())	ok	5ms..1s
delay(5)	ok	5ms..1s
delay(5.milliseconds)	ok	5ms..1s
pauseMs(5)	ok	pauses 5 ms
pauseMs(5.seconds)	error: argument type mismatch: actual type is 'Duration', but 'Long' was expected.	-
pauseMs(5.seconds.inWholeMilliseconds)	ok	pauses 5000 ms
pauseFor(5)	error: argument type mismatch: actual type is 'Int', but 'Duration' was expected.	-
pauseFor(5000L)	error: argument type mismatch: actual type is 'Long', but 'Duration' was expected.	-
pauseFor(5.seconds)	ok	pauses 5s
5.seconds + 300	error: argument type mismatch: actual type is 'Int', but 'Duration' was expected.	-
5.seconds + 300.milliseconds	ok	5.3s
5.seconds > 3000L	error: argument type mismatch: actual type is 'Long', but 'Duration' was expected.	-
5.seconds > 3000.milliseconds	ok	true
5.seconds / 2.seconds	ok	2.5
90.seconds.toString()	ok	1m 30s
90.seconds.toIsoString()	ok	PT1M30S
Duration.INFINITE + 1.days	ok	Infinity
Duration.INFINITE - Duration.INFINITE	ok	IllegalArgumentException: Summing infinite durations of different signs yields an undefined result.
Long.MAX_VALUE.nanoseconds	ok	106751d 23h 47m 16.854s
Long.MAX_VALUE.nanoseconds.inWholeDays / 365	ok	292
Long.MAX_VALUE.nanoseconds * 2	ok	213503d 23h 34m 33.708s
(Long.MAX_VALUE.nanoseconds * 2).inWholeDays / 365	ok	584
(Long.MAX_VALUE / 2).milliseconds * 3	ok	Infinity
first compile exit 1
cells the compiler blocked: 6 / 25
(exit 0)
```

```text
===== kotlinc -cp kotlinx-coroutines-core-jvm-1.11.0.jar unit50.kt -d o50e =====
unit50.kt:23:64: error: none of the following candidates is applicable:

static fun sleep(p0: Long): Unit:
  Argument type mismatch: actual type is 'Duration', but 'Long' was expected.

static fun sleep(p0: Duration!): Unit:
  Argument type mismatch: actual type is 'kotlin.time.Duration', but 'java.time.Duration!' was expected.
    "Thread.sleep(5.seconds)" to { bucket(measureTime { Thread.sleep(5.seconds) }) },
                                                               ^^^^^
unit50.kt:28:39: error: argument type mismatch: actual type is 'Duration', but 'Long' was expected.
    "pauseMs(5.seconds)" to { pauseMs(5.seconds) },
                                      ^^^^^^^^^
unit50.kt:30:33: error: argument type mismatch: actual type is 'Int', but 'Duration' was expected.
    "pauseFor(5)" to { pauseFor(5) },
                                ^
unit50.kt:31:37: error: argument type mismatch: actual type is 'Long', but 'Duration' was expected.
    "pauseFor(5000L)" to { pauseFor(5000L) },
                                    ^^^^^
unit50.kt:33:40: error: argument type mismatch: actual type is 'Int', but 'Duration' was expected.
    "5.seconds + 300" to { 5.seconds + 300 },
                                       ^^^
unit50.kt:35:42: error: argument type mismatch: actual type is 'Long', but 'Duration' was expected.
    "5.seconds > 3000L" to { 5.seconds > 3000L },
                                         ^^^^^
(exit 1)
```

**왜 그런가**

- ★★★ **단위가 타입에 있으면 컴파일러가 막고, 이름에 있으면 못 막는다** — `pauseFor(5)` 는 `actual type is 'Int', but 'Duration' was expected.` 로 막히지만 `pauseMs(5)` 는 `ms` 라는 **이름**만 있어 통과한다.
- ★★ `Thread.sleep(5)` 와 `delay(5)` 가 `5ms..1s` 구간 — 둘 다 **밀리초 `Long`** 을 받는다. `delay` 는 `Duration` 판도 있어 `delay(5.milliseconds)` 도 된다.
- ★★ 무한·넘침은 2번.

### 2. KDoc 「**±146 years with nanosecond precision** … **±146 million years with millisecond precision** … doesn't fit … **infinite**」 — 584년(1번의 셈)은 나노초 범위를 넘고 **밀리초 범위 안**이다

**왜 그런가**

```text
===== sed -n '17,20p;32,37p' commonMain/kotlin/time/Duration.kt =====
 * The type can store duration values up to ±146 years with nanosecond precision,
 * and up to ±146 million years with millisecond precision.
 * If a duration-returning operation provided in `kotlin.time` produces a duration value that doesn't fit into the above range,
 * the returned `Duration` is infinite.
@SinceKotlin("1.6")
@JvmInline
public value class Duration
// A temporary workaround for KT-81995, the constructor has to be private once the issue is resolved.
@Deprecated("Don't call this constructor directly.", level = DeprecationLevel.ERROR)
internal constructor(private val rawValue: Long) :
(exit 0)
===== sed -n '10,13p' jvmMain/kotlin/time/MonoTimeSource.kt =====
@SinceKotlin("1.3")
internal actual object MonotonicTimeSource : TimeSource.WithComparableMarks {
    private val zero: Long = System.nanoTime()
    private fun read(): Long = System.nanoTime() - zero
(exit 0)
```

- ★★★ 1번의 셈 — `Long.MAX_VALUE.nanoseconds` 가 **292**, 두 배가 **584**(`inWholeDays / 365`). 둘 다 ±146년을 넘으니 **나노초로는 못 담지만 밀리초로는 담긴다.** 그래서 `106751d 23h 47m 16.854s` · `213503d 23h 34m 33.708s` 처럼 **끝자리가 밀리초에서 끊긴 값**이 나온다.
- ★★ `(Long.MAX_VALUE / 2).milliseconds * 3` 은 밀리초 범위까지 넘는다 — 그제야 **`Infinity`** 로 포화한다.
- ★ 「넘치면 포화」는 **맞지만 반쪽**이다 — 먼저 정밀도를 바꿔 **버틴다.**

### 3. **`pauseFor-LRDsOJo(long)`** · `pauseMs(long)` · **`long makeTimeout()`** · `kotlin.time.Duration maybe-BwNAW2A(kotlin.time.Duration)` · `List<kotlin.time.Duration> many()` · **`long mark()`**

**출력**

```text
===== kotlinc dur50.kt -d o50d =====
(exit 0)
===== java -cp o50d:kotlin-stdlib.jar Dur50Kt =====
pauses 5s | pauses 5000 ms | null | [5s]
true
(exit 0)
===== javap -p o50d/Dur50Kt.class =====
Compiled from "dur50.kt"
public final class Dur50Kt {
  public static final java.lang.String pauseFor-LRDsOJo(long);
  public static final java.lang.String pauseMs(long);
  public static final long makeTimeout();
  public static final kotlin.time.Duration maybe-BwNAW2A(kotlin.time.Duration);
  public static final java.util.List<kotlin.time.Duration> many();
  public static final long mark();
  public static final void main();
  public static void main(java.lang.String[]);
}
(exit 0)
===== javap -p -cp kotlin-stdlib.jar kotlin.time.Duration | grep -E 'class|rawValue;|box-impl|unbox-impl' =====
public final class kotlin.time.Duration implements java.lang.Comparable<kotlin.time.Duration> {
  private final long rawValue;
  public static final kotlin.time.Duration box-impl(long);
  public final long unbox-impl();
(exit 0)
```

**왜 그런가**

- ★★★ `Duration` 은 `value class` 라 **알맹이 `long`** 이 다닌다 — 받는 쪽은 이름이 뭉개지고(`-LRDsOJo`), 반환은 이름이 안 뭉개진다([26번 주제](../26-value-class-and-boxing/)).
- ★★ **`pauseFor-LRDsOJo(long)` 와 `pauseMs(long)` 의 인자 타입이 같다** — 이름을 뭉개지 않으면 JVM 에서 두 함수가 구별이 안 된다.
- ★★ **널 가능(`Duration?`) · 제네릭(`List<Duration>`)** 자리에서는 `kotlin.time.Duration` **객체**가 된다 — 박싱이 산다.
- ★ `ValueTimeMark` 도 `value class` 라 **`long mark()`** 다.

### 4. 전부 **`true`** · `5` 는 `false`/`true` · `6` 은 **`TimeSource(System.nanoTime())`**

**출력**

```text
===== kotlinc measure50.kt -d o50m =====
(exit 0)
===== java -cp o50m:kotlin-stdlib.jar Measure50Kt =====
1 measureTime >= 100ms: true
2 measureTimedValue value=42, >= 100ms: true
3 mark.elapsedNow() >= 100ms: true
4 later > mark: true, later - mark >= 100ms: true
5 deadline.hasPassedNow(): false, hasNotPassedNow(): true
6 TimeSource.Monotonic.toString() -> TimeSource(System.nanoTime())
(exit 0)
```

**왜 그런가**

- ★★ 100ms 를 재운 뒤라 `>= 100ms` 는 전부 참이다 — **절대값은 안 찍었다**(흔들리는 칸).
- ★★ `mark + 1.hours` 는 **한 시간 뒤의 마감**이라 아직 안 지났다(`hasPassedNow()` 가 `false`).
- ★★★ `6` — 이 판의 단조 시계가 **`System.nanoTime()`** 이다. 벽시계와 무관하다.

### 5. ★★★ **막힌 칸 3 / 10** — opt-in 없는 파일만 **2.0·2.1·2.2** 에서 「`this declaration needs opt-in`」(21건) · opt-in 을 단 파일은 **다섯 판 모두 `ok`**

**출력**

```kotlin
// inst50o.kt
@file:OptIn(kotlin.time.ExperimentalTime::class)

import kotlin.time.Clock
import kotlin.time.Instant
import kotlin.time.toJavaInstant
import kotlin.time.toKotlinInstant

fun main() {
    val epoch = Instant.fromEpochSeconds(0)
    println("1 $epoch")
    println("2 ${epoch.toJavaInstant()} ${epoch.toJavaInstant()::class.qualifiedName}")
    println("3 ${java.time.Instant.ofEpochSecond(90).toKotlinInstant()}")
    println("4 now after 2026-01-01: ${Clock.System.now() > Instant.parse("2026-01-01T00:00:00Z")}")
    println("5 ${Instant.parse("2026-09-26T12:00:00Z") - Instant.parse("2026-09-26T10:30:00Z")}")
    println("6 ${Instant.parse("2026-09-26T21:00:00+09:00")}")
}
```

```text
===== python3 grid50i.py =====
file	2.0	2.1	2.2	2.3	2.4
inst50.kt	21 errors, first: this declaration needs opt-in. Its usage must be marked with '@kotlin.time.ExperimentalTime' or '@OptIn(kotlin.time.ExperimentalTime::class)'	21 errors, first: this declaration needs opt-in. Its usage must be marked with '@kotlin.time.ExperimentalTime' or '@OptIn(kotlin.time.ExperimentalTime::class)'	21 errors, first: this declaration needs opt-in. Its usage must be marked with '@kotlin.time.ExperimentalTime' or '@OptIn(kotlin.time.ExperimentalTime::class)'	ok	ok
inst50o.kt	ok	ok	ok	ok	ok
blocked cells: 3 / 10
(exit 0)
```

**왜 그런가**

```text
===== sed -n '105,107p' commonMain/kotlin/time/Instant.kt =====
@SinceKotlin("2.3")
@WasExperimental(ExperimentalTime::class)
public class Instant internal constructor(
(exit 0)
===== sed -n '13,16p;18,20p;24p' commonMain/kotlin/time/Clock.kt =====
 * It is not recommended to use [Clock.System] directly in the implementation. Instead, you can pass a
 * [Clock] explicitly to the necessary functions or classes.
 * This way, tests can be written deterministically by providing custom [Clock] implementations
 * to the system under test.
@SinceKotlin("2.3")
@WasExperimental(ExperimentalTime::class)
public interface Clock {
     * Calling [now] later is not guaranteed to return a larger [Instant].
(exit 0)
===== grep -rlE '^ *@ExperimentalTime$' commonMain/kotlin/time jvmMain/kotlin/time jvmMain/jdk8/kotlin/time =====
commonMain/kotlin/time/Duration.kt
commonMain/kotlin/time/TimeSources.kt
(exit 0)
===== grep -n -A1 -E '^ *@ExperimentalTime$' commonMain/kotlin/time/Duration.kt =====
72:        @ExperimentalTime
73-        public fun convert(value: Double, sourceUnit: DurationUnit, targetUnit: DurationUnit): Double =
(exit 0)
===== grep -n -A1 -E '^ *@ExperimentalTime$' commonMain/kotlin/time/TimeSources.kt =====
96:@ExperimentalTime
97-@Deprecated(
(exit 0)
```

- ★★★ `Instant`·`Clock` 이 **`@SinceKotlin("2.3")` + `@WasExperimental(ExperimentalTime::class)`** — `-api-version` 이 2.3 보다 낮으면 **「실험적」으로 보여** opt-in 을 요구하고, 2.3 이상이면 Stable 이다.
- ★★ 진단이 **「없다」가 아니다** — 2.0 에서도 opt-in 만 달면 통과한다(8번).

### 6. `1970-01-01T00:00:00Z` · `1970-01-01T00:00:00Z java.time.Instant` · `1970-01-01T00:01:30Z` · `now after 2026-01-01: true` · `1h 30m` · `2026-09-26T12:00:00Z`

**출력**

```text
===== kotlinc inst50.kt -d o50n =====
(exit 0)
===== java -cp o50n:kotlin-stdlib.jar Inst50Kt =====
1 1970-01-01T00:00:00Z
2 1970-01-01T00:00:00Z java.time.Instant
3 1970-01-01T00:01:30Z
4 now after 2026-01-01: true
5 1h 30m
6 2026-09-26T12:00:00Z
(exit 0)
```

**왜 그런가**

- ★★ `toJavaInstant()` 는 **`java.time.Instant`** 를 돌려준다 · `toKotlinInstant()` 는 반대 방향이다.
- ★★ `Instant - Instant` 는 **`Duration`** · 오프셋 붙은 문자열은 **UTC 로** 정규화된다.
- ★ `now()` 는 참/거짓으로만 찍었다.

### 7. 두 번째 후보는 **`sleep(p0: Duration!)` — `java.time.Duration`**(JDK 19+) · **`toJavaDuration()`** 을 거친다

**왜 그런가**

```text
===== unzip -o -q "$JAVA_HOME/lib/src.zip" java.base/java/lang/Thread.java =====
(exit 0)
===== sed -n '579,581p' java.base/java/lang/Thread.java =====
     * @since 19
     */
    public static void sleep(Duration duration) throws InterruptedException {
(exit 0)
```

- ★★★ JDK 에는 `Thread.sleep(long)` 과 `Thread.sleep(java.time.Duration)` 이 있다 — **`kotlin.time.Duration` 을 받는 판은 없다.** 진단이 그 차이를 **두 타입 이름째**(`'kotlin.time.Duration'` · `'java.time.Duration!'`) 말한다.
- ★★ `5.milliseconds.toJavaDuration()` 을 넘기면 통과한다(1번 격자 3행 — `5ms..1s`).

### 8. **확인할 수 없다** — `@WasExperimental` 때문에 2.0 과 2.1 이 **같은 진단**을 낸다 · 이 판의 소스에는 `@SinceKotlin("2.3")` 만 있다

**왜 그런가**

- ★★★ 격자가 말하는 것은 「**2.3 에서 Stable**」까지다. 「언제 **들어왔나**」는 `@WasExperimental` 선언에 판이 적혀 있지 않아 **이 창 밖**이다 — README 의 「2.1.0 도입」은 이 문서가 **확인하지 못한** 사실이다(제5의 상태 — 소스로 창을 바꿨지만 그 창도 못 봤다).
- ★ 확인하려면 2.1 판 **stdlib** 이나 릴리스 노트가 필요하다 — 이 머신에 없고 네트워크를 쓰지 않았다.

### 9. **타입이 둘이다** — 재기는 `TimeMark`(단조 · `System.nanoTime()`), 시각은 `Instant`(벽시계) · 그래서 **「어떤 연산 뒤에 단조 값이 조용히 벗겨지는」** 사고가 안 난다

**왜 그런가**

- ★★ Go 는 `time.Now()` 한 값에 두 시계를 넣고 `Round(0)`·`In()` 같은 연산이 단조 값을 벗긴다([Go 48번](../../../go/syntax/48-time-monotonic-clock-duration-timer-and-ticker/)). Kotlin 의 `Instant` 에는 **처음부터 단조 값이 없고**, `TimeMark` 에는 **달력 시각이 없다.**
- ★ 대신 Kotlin 에서는 **`Instant` 뺄셈으로 경과 시간을 재는** 실수가 생긴다 — `Clock.now()` KDoc 이 「더 큰 값」을 보장하지 않는다(5번 발췌).

### 10. 말할 수 있는 것 — **서명에 `long` 이 다닌다 · 널 가능·제네릭 자리에서는 객체다** · 말할 수 없는 것 — **실행 시간·할당 수**

**왜 그런가**

- ★★ `javap -p` 는 서명만 본다 — 이 문서는 시간도 할당도 **재지 않았다**(규칙 4). 「비용 0」은 **근거 없는 주장**이다.
- ★ 박싱 자리를 세는 법(`box-impl` 호출 세기)은 [26번 주제](../26-value-class-and-boxing/) (2)가 정본이다.

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
| ★★★ **걸린 시간의 절댓값** — 칸으로 안 만들었다(참/거짓 · 구간 이름만) | 단위 격자 25행 · 막은 칸 수 · 진단 문구 · `Duration` 산술·`toString()` |
| ★ 구간 이름 `5ms..1s` — 부하가 아주 큰 머신이면 움직일 수 있다(이번 두 판은 같았다) | `javap` 출력 — 해시 글자까지(판이 바뀌면 달라질 수 있어 **모양**만 근거로 쓴다) |
| | `Instant` 판 격자 · 고정 시각 출력 · 소스 발췌 · 모든 **종료 코드** |

> 근거 — 캡처 스크립트를 처음부터 다시 돌려 **블록 전체를 대조**했다.
>
> 실측 — `capture.sh blocks` 와 `capture.sh blocks-recheck` 를 처음부터 따로 돌려 `normalize-shaky.py` 로 대조했다 —\
> **블록 74개 · 동일 74 · 흔들린 칸 0 · ★고칠 것 0**(50\~53 네 주제를 한 캡처로 받았다). 추가한 정규화 규칙은 **없다**.

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `unit50.kt` · `grid50.py` | ★★★ 단위 실수 25칸 — 막혔나 · 값 | 스크립트가 컴파일 → 막힌 줄을 뺀 사본을 다시 컴파일 → 실행 |
| `unit50.kt` | 에러 전문 | `kotlinc` 한 번(격자가 읽은 그 출력) |
| `dur50.kt` · `kotlin.time.Duration` | ★★ `long` 서명 · 이름 뭉개기 · 박싱 자리 | `kotlinc` → `java` → `javap -p` |
| `measure50.kt` | ★★ `measureTime` · 단조 마크 | `kotlinc` → `java`(참/거짓) |
| `inst50.kt` · `inst50o.kt` · `grid50i.py` | ★★★ `Instant` opt-in × `-language-version`/`-api-version` 2.0\~2.4 | 스크립트가 판마다 컴파일 |
| `inst50.kt` | `Instant` 변환·뺄셈·정규화 | `kotlinc` → `java` |
| stdlib 소스 jar · JDK `src.zip` | 범위 계약 · 선언 · 단조 시계 · `@SinceKotlin`/`@WasExperimental` · `@ExperimentalTime` 잔여 · `Thread.sleep(Duration)` 의 `@since` | `unzip` → `sed -n`/`grep` |
| `form50.kt` | 형태 한 벌 | `kotlinc` → `java` |

**구현 의존 항목** — 이름 뭉개기 해시 · 단조 시계가 `System.nanoTime()` 인 것 · 진단 문구 — 이 판의 산출물이다.\
반면 **맨 숫자가 `Duration` 자리에 못 들어가는 것**(타입 규칙) · **범위와 포화**(KDoc) · **`Instant` 가 2.3 에서 Stable**(선언) 은 **계약**이다.

**★ 던져 봤더니 예상과 달랐던 것 — 세 건**

1. ★★★ **`Long.MAX_VALUE.nanoseconds * 2` 가 포화하지 않았다** — 밀리초 정밀도로 옮겨 타 584년(`inWholeDays / 365`)이 나왔다. `Long.MAX_VALUE.nanoseconds` 자체도 이미 밀리초 정밀도였다. 포화를 보려면 밀리초 범위까지 넘겨야 했다.
2. ★★ **`Thread.sleep` 에 `Duration` 판이 있었다** — 다만 `java.time.Duration` 이다. 진단이 두 후보를 다 보여 줬다.
3. ★★ **`Instant` 의 「2.1 도입」은 판 격자로 안 보였다** — 2.0 에서도 opt-in 만 달면 컴파일된다(`@WasExperimental`).
