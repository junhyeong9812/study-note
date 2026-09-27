# kotlin/syntax/50 — `kotlin.time` — `Duration`·시간 측정 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — **이 판의 stdlib 소스 jar**(`kotlin-stdlib-sources.jar` 2.4.20)의 KDoc 과 선언(`Duration.kt`·`Instant.kt`·`Clock.kt`·`MonoTimeSource.kt`)((5)). ★ 공식 문서 페이지([Time measurement](https://kotlinlang.org/docs/time-measurement.html))는 **이 작업에서 열지 못했다**(외부 네트워크를 쓰지 않았다) — 문장을 인용하지 않는다.
> **실행 검증** — 이 문서의 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `java`·`javap` 에서 실제로 얻었다.\
> `kotlinc` 17회(단위 격자 스크립트 안의 2회 · 판 격자 스크립트 안의 10회 포함) · `java` 5회 · `javap` 2회 · stdlib 소스 jar 발췌 5곳 · JDK `src.zip` 발췌 1곳.\
> ★ 단위 격자의 `delay` 두 칸만 **kotlinx-coroutines 1.11.0** 을 쓴다(gradle 캐시에 있던 판 — [목록의 **54번 주제**](../54-coroutine-context-dispatchers-and-withcontext/)까지 이 판을 쓴다). 그 밖은 stdlib 만 쓴다.\
> ★★ 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적지 않았다. **「막은 칸 N / M」은 스크립트가 스스로 센 것**이다.
> **버전** — `Duration` 은 stdlib 소스에 **`@SinceKotlin("1.6")`** · 단조 시계 `MonotonicTimeSource` 는 **`@SinceKotlin("1.3")`**((5)). ★★★ **`kotlin.time.Instant`·`Clock` 은 소스에 `@SinceKotlin("2.3")` + `@WasExperimental(ExperimentalTime::class)`** 이다 — README 의 「2.1.0 도입」은 **이 소스에서 안 보인다**(4).
> **경계** — `Int` 를 `Long` 에 그냥 못 넣는 **암묵 변환 없음**은 [01번 주제](../01-val-var-and-basic-types/)가 정본이다. `value class` 의 박싱·이름 뭉개기 규칙은 [26번 주제](../26-value-class-and-boxing/)가 정본이다 — 여기서는 **`Duration` 이 그 규칙대로 도는지**만 본다. 코루틴의 `delay` 는 [52번 주제](../52-coroutine-basics-suspend-scope-launch-async/)의 몫이다 — 여기서는 **인자의 단위**만 본다.\
> ★ **대비** — 단조 시계가 벽시계 값 **안에** 숨어 있는 Go(`m=`)는 [Go 48번](../../../go/syntax/48-time-monotonic-clock-duration-timer-and-ticker/)이 정본이다.
> 이 본문은 Claude 작성이다(원고 없음).

★★★ **본체는 첫째 창이다** — 「**단위 실수 격자 — 단위를 `Long` 으로 받는 API 와 `Duration` 으로 받는 API 에 같은 실수를 던져 → 컴파일되나 · 값**」. 이 주제의 결론은 값이 아니라 **「어느 칸에서 컴파일러가 막았나」** 다.

## 이 주제가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **언어 보장 / API 계약** | 서명·KDoc 이 약속한 것 | ★★★ `Duration` 은 **`@JvmInline value class`**(선언) · KDoc 「**±146 years with nanosecond precision** … **±146 million years with millisecond precision** … 넘치면 **infinite**」 · `Clock.now()` KDoc 「**not guaranteed to return a larger [Instant]**」 |
| **구현(컴파일러·stdlib)** | 이 판이 실제로 하는 것 | ★★ `Duration` 의 알맹이는 `private val rawValue: Long` · JVM 단조 시계는 **`System.nanoTime()`** · 이름 뭉개기(`pauseFor-LRDsOJo(long)`) |
| **이 판의 관찰** | kotlinc 2.4.20 에서 이번에 본 것 | 격자 값 · 진단 문구 · `javap` 이름 · 시간은 **참/거짓**으로만 |

## 이 판

```text
===== kotlinc -version =====
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다 — 칸으로 안 만들었다** | ★★★ **걸린 시간의 절댓값** | 전부 **참/거짓**(「`>= 100ms`」)이나 **넓은 구간 이름**(`under 5ms` · `5ms..1s` · `1s or more`)으로만 찍었다 — 규칙 24 |
| 안 흔들린다 | 단위 격자 25행 · 막은 칸 수 · 진단 문구 · `Duration` 의 `toString()` | 컴파일러 진단과 `Duration` 산술은 결정적이다 |
| 안 흔들린다 | ★ 「`5ms..1s`」 구간 이름 | 5ms 를 재우고 **1초 미만**인지를 묻는다 — 폭이 200배라 이 머신에서 두 번 다 같았다. ★ **부하가 큰 머신이면 이 칸이 움직일 수 있다**(구간을 넘는 지연) |
| 안 흔들린다 | `javap` 출력 — 뭉개진 이름의 해시 글자(`-LRDsOJo`)까지 | 같은 소스·같은 판이면 같다. ★ 해시 글자는 **판이 바뀌면 달라질 수 있어** 모양(`이름-해시`)만 근거로 쓴다([26번 주제](../26-value-class-and-boxing/)와 같은 선언) |
| 안 흔들린다 | `Instant` 판 격자 2행 × 5판 · 고정 시각(`fromEpochSeconds(0)` 등)의 출력 | `now()` 는 **「2026-01-01 뒤인가」 참/거짓**으로만 찍었다 |

★ 근거 — 캡처 스크립트를 처음부터 두 번 돌려 **블록 전체를 대조**했다(수치는 3-answer 의 「실행 검증」).

## 한눈에 — 쉽게 말하면

**`Long` 으로 시간을 넘기는 것은 「숫자만 적힌 쪽지」를 건네는 것이다** — `5` 라고만 적혀 있으면 받는 사람은 5초인지 5밀리초인지 **자기 습관대로** 읽는다. `Thread.sleep(5)` 는 밀리초로 읽고, 내가 만든 `pauseMs(5)` 도 이름을 안 보면 모른다. **`Duration` 은 「단위가 인쇄된 쪽지」다** — `5.seconds` 는 쪽지에 「5초」가 박혀 있고, 숫자만 적힌 쪽지(`5`·`5000L`)는 **받는 창구에서 아예 안 받는다**(컴파일 에러).
★ 그런데 쪽지를 봉투에 넣어 JVM 으로 보내면 봉투는 벗겨지고 **다시 숫자(`long`)만** 간다 — 단위는 **컴파일할 때만** 지켜진다.

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 숫자만 적힌 쪽지 | `Long` 밀리초 인자 — `Thread.sleep(5)` · `pauseMs(5)` | (1) ★ |
| 단위가 인쇄된 쪽지 | `Duration` — `5.seconds` · `300.milliseconds` | (1) ★ |
| 숫자 쪽지를 안 받는 창구 | `pauseFor(d: Duration)` 에 `5` → **컴파일 에러** | (1) ★★★ |
| 봉투를 벗기면 숫자 | `value class` — JVM 서명이 **`long`** | (2) |
| 초시계 | `TimeSource.Monotonic` — **`System.nanoTime()`** | (3) |
| 벽시계 | `Clock.System.now()` → `Instant` — 뒤로 갈 수 있다 | (4) |

```text
   같은 실수 「5 라고만 쓴다」 를 두 창구에 던지면

   받는 쪽 서명                  pauseMs(5)            pauseFor(5)
   ──────────────────────────  ────────────────────  ─────────────────────────────
   fun pauseMs(ms: Long)        통과 — 5 ms 로 읽힌다    (해당 없음)
   fun pauseFor(d: Duration)    (해당 없음)             컴파일러가 막는다
                                                        actual type is 'Int', but 'Duration' was expected
   JVM 에서                     pauseMs(long)          pauseFor-LRDsOJo(long)    ← 둘 다 long
```

## 이 주제가 답하려는 질문

1. **`Long` 을 받는 API 와 `Duration` 을 받는 API** 에 같은 단위 실수를 던지면 어느 칸에서 컴파일러가 막나 — 그리고 **막지 못하는 칸**은 어디인가.
2. `Duration` 의 산술(`+`·`*`·`/`)과 **무한·넘침**은 어떻게 도나 — 「넘치면 포화」는 언제 참인가.
3. **시간을 재는 법**(`measureTime` · `markNow()`/`elapsedNow()`)과 **시각을 읽는 법**(`Clock.System.now()` → `kotlin.time.Instant`)은 무엇이 다른가 — `Instant` 는 **몇 판부터 opt-in 없이** 되나.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **단위 격자(컴파일 → 남은 칸만 실행)** | 컴파일되나 · 값((1)) | ★ **본체 창** — 막힌 줄을 지운 사본을 다시 컴파일해 **나머지 칸의 값**까지 한 블록에 받는다 |
| ★★ **`javap -p`** | `Duration` 이 `long` 으로 다니나 · 이름이 뭉개지나((2)) | [26번 주제](../26-value-class-and-boxing/)와 같은 창 |
| ★★ **참/거짓 측정 로그** | `measureTime` · 단조 마크((3)) | 절대 시간은 **안 찍는다** |
| ★★ **판 격자(`-language-version`·`-api-version` × 파일)** | `Instant` 가 opt-in 을 요구하나((4)) | 49편의 판 격자와 같은 꼴 |
| ★★ **stdlib 소스 jar 발췌** | 선언·KDoc 계약((5)) | — |
| ★ **제5의 상태** | 「`Instant` 가 **2.1 에 들어왔나**」를 **2.1 로 컴파일해 물으면** 답이 안 나온다 — `@WasExperimental` 때문에 2.0 도 2.1 도 같은 진단이다. **소스의 주석(annotation)** 으로 창을 바꿨다((4)(5)) | 그 창은 「**언제 Stable 이 됐나**」(2.3)만 말하고 「**언제 들어왔나**」는 **못 본다** |
| **인용 — 다시 안 잰다** | `Int`→`Long` 암묵 변환 없음 | [01번 주제](../01-val-var-and-basic-types/) |
| **부적용 — 실행 시간 비교** | 「`Duration` 은 비용 0」은 **재지 않았다** — `javap` 의 `long` 까지만 말한다 | (2) |

### (1) ★★★ 단위 실수 격자 — 컴파일러가 막는 칸

**언제 쓰나** — 타임아웃·재시도 간격을 인자로 받는 함수를 설계할 때. `Long` 으로 받을지 `Duration` 으로 받을지.

방법 — 단위를 **`Long` 밀리초로 받는 함수**(`pauseMs`) · **`Duration` 으로 받는 함수**(`pauseFor`) · JDK 의 `Thread.sleep` · 코루틴의 `delay` 에 같은 실수를 던진다. 한 줄 = 한 칸. 스크립트가 첫 컴파일의 진단을 줄마다 읽고, **막힌 줄을 뺀 사본**을 다시 컴파일해 남은 칸을 실행한다. 잠드는 칸은 걸린 시간을 **구간 이름**으로만 찍는다.

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

```python
# grid50.py
import os
import re
import subprocess

SRC = "unit50.kt"
OK_SRC = "unit50ok.kt"
CP = os.environ["CP50"]

lines = open(SRC, encoding="utf-8").read().split("\n")
probe_line = {}
for n, line in enumerate(lines, 1):
    m = re.match(r'\s*"([^"]+)" to \{', line)
    if m:
        probe_line[m.group(1)] = n

run = subprocess.run(["kotlinc", "-cp", CP, SRC, "-d", "o50u"], capture_output=True, text=True)
first = {}
for line in (run.stdout + run.stderr).splitlines():
    m = re.match(r"unit50\.kt:(\d+):\d+: error: (.*)$", line)
    if m and int(m.group(1)) not in first:
        first[int(m.group(1))] = m.group(2)

kept = [l for n, l in enumerate(lines, 1) if n not in first]
open(OK_SRC, "w", encoding="utf-8").write("\n".join(kept))
build = subprocess.run(["kotlinc", "-cp", CP, OK_SRC, "-d", "o50k"], capture_output=True, text=True)
if build.returncode != 0:
    raise SystemExit("second compile failed:\n" + build.stderr)
out = subprocess.run(["java", "-cp", "o50k:" + CP, "Unit50okKt"], capture_output=True, text=True, check=True)
value = dict(l.split("\t", 1) for l in out.stdout.splitlines())

print("\t".join(["probe", "compile", "value"]))
blocked = 0
for name, n in probe_line.items():
    if n in first:
        row = [name, "error: " + first[n], "-"]
        blocked += 1
    else:
        row = [name, "ok", value[name]]
    if len(row) != 3:
        raise SystemExit("cell count mismatch: " + name)
    print("\t".join(row))
print("first compile exit %d" % run.returncode)
print("cells the compiler blocked: %d / %d" % (blocked, len(probe_line)))
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

- ★★★ **컴파일러가 막은 칸은 25칸 중 6칸이다** — 전부 **`Duration` 을 받는 자리에 맨 숫자를 넣은 칸**(`pauseFor(5)` · `pauseFor(5000L)` · `5.seconds + 300` · `5.seconds > 3000L`)이거나 **`Long` 을 받는 자리에 `Duration` 을 넣은 칸**(`pauseMs(5.seconds)` · `Thread.sleep(5.seconds)`)이다.
- ★★★ **막지 못한 칸** — `pauseMs(5)` 는 **`pauses 5 ms`** 로 통과한다. 쓴 사람이 5초를 뜻했어도 **컴파일러는 알 길이 없다** — 단위가 **타입이 아니라 이름(`ms`)** 에만 있기 때문이다. `Thread.sleep(5)` 도 같다 — 걸린 시간이 **`5ms..1s`** 구간이다(5초가 아니다).
- ★★ **`delay(5)` 도 밀리초다** — `delay(5)` 와 `delay(5.milliseconds)` 가 같은 구간이다. `delay` 에는 **`Long` 판과 `Duration` 판이 둘 다** 있어서 둘 다 통과한다 — 맨 숫자를 쓰면 **밀리초로 읽힌다.**
- ★★ **`Duration` 끼리의 산술은 단위를 맞춰 준다** — `5.seconds + 300.milliseconds` = **`5.3s`** · `5.seconds / 2.seconds` = **`2.5`**(단위가 지워진 `Double`) · 비교 `5.seconds > 3000.milliseconds` = `true`.
- ★★ **`toString()` 은 사람이 읽는 꼴**(`1m 30s`), **`toIsoString()` 은 ISO-8601**(`PT1M30S`).
- ★★★ **무한과 넘침** — `Duration.INFINITE + 1.days` = `Infinity` · `INFINITE - INFINITE` 는 **`IllegalArgumentException`**(「`Summing infinite durations of different signs yields an undefined result.`」) · ★ **`Long.MAX_VALUE.nanoseconds * 2` 는 포화하지 않는다** — `213503d 23h 34m 33.708s` 가 나온다(프로그램이 `inWholeDays / 365` 로 세면 **584**). ★ 그 전에 **`Long.MAX_VALUE.nanoseconds` 자체가 이미 `106751d 23h 47m 16.854s`**(같은 셈으로 292) — 끝자리가 **밀리초(`.854s`)** 에서 끊긴다. 나노초 정밀도의 한계(±146년)를 넘자 **밀리초 정밀도로 옮겨 탄 것**이다((5)의 KDoc). 밀리초 정밀도의 한계를 넘기는 `(Long.MAX_VALUE / 2).milliseconds * 3` 에서야 **`Infinity`** 로 포화한다.

에러 전문 — 같은 파일의 첫 컴파일(스크립트가 읽은 그 출력)이다.

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

- ★★★ **`Thread.sleep(5.seconds)` 의 진단은 후보 둘을 댄다** — `sleep(p0: Long)` 과 **`sleep(p0: Duration!)`** — 뒤쪽은 **`java.time.Duration`** 이다(JDK `src.zip` 의 `@since 19` — 아래 블록). 「`kotlin.time.Duration` 이지 `java.time.Duration` 이 아니다」가 진단 안에 그대로 있다. 그래서 `5.milliseconds.toJavaDuration()` 으로 바꿔 주면 통과한다(격자 3행).
```text
===== unzip -o -q "$JAVA_HOME/lib/src.zip" java.base/java/lang/Thread.java =====
(exit 0)
===== sed -n '579,581p' java.base/java/lang/Thread.java =====
     * @since 19
     */
    public static void sleep(Duration duration) throws InterruptedException {
(exit 0)
```

- ★ 진단은 전부 **`argument type mismatch: actual type is 'X', but 'Y' was expected.`** 한 꼴이다 — 단위 실수가 **타입 불일치로 번역**됐다. `Int` 와 `Long` 이 서로 안 바뀌는 것([01번 주제](../01-val-var-and-basic-types/))과 같은 성질이 한 층 위에서 한 번 더 일한다.

### (2) ★★ `Duration` 은 JVM 에서 `long` 이다 — 그리고 이름이 뭉개진다

```kotlin
// dur50.kt
import kotlin.time.Duration
import kotlin.time.Duration.Companion.seconds
import kotlin.time.TimeSource

fun pauseFor(d: Duration): String = "pauses $d"

fun pauseMs(ms: Long): String = "pauses $ms ms"

fun makeTimeout(): Duration = 5.seconds

fun maybe(d: Duration?): Duration? = d

fun many(): List<Duration> = listOf(5.seconds)

fun mark(): TimeSource.Monotonic.ValueTimeMark = TimeSource.Monotonic.markNow()

fun main() {
    println("${pauseFor(makeTimeout())} | ${pauseMs(5000)} | ${maybe(null)} | ${many()}")
    println(mark() < mark())
}
```

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

- ★★★ **`pauseFor(d: Duration)` 는 `pauseFor-LRDsOJo(long)`** — 알맹이 `long` 을 받고 이름이 뭉개졌다. `pauseMs(ms: Long)` 는 **`pauseMs(long)`** — **JVM 서명의 인자 타입은 둘이 같다.** 그래서 이름을 안 뭉개면 두 함수를 오버로드로 가를 수가 없다 — [26번 주제](../26-value-class-and-boxing/) (1)의 규칙 그대로다.
- ★★ **`makeTimeout(): Duration` 은 `long makeTimeout()`** — 반환에는 해시가 안 붙는다(26번 주제와 같은 관찰). **`TimeSource.Monotonic.markNow()` 가 돌려주는 `ValueTimeMark` 도 `long`**(`long mark()`)이다 — 마크도 `value class` 다.
- ★★ **박싱되는 자리** — `Duration?` 을 받는 `maybe-BwNAW2A(kotlin.time.Duration)` 과 `List<Duration>` 은 **`kotlin.time.Duration` 객체**다. 26번 주제의 「널 가능 · 제네릭이면 포장이 산다」와 같다.
- ★ `kotlin.time.Duration` 클래스에는 `private final long rawValue` 하나와 `box-impl(long)` · `unbox-impl()` 이 있다.
- ★★ **「비용 0」이라고 적지 않는다** — 이 창이 보여 주는 것은 **서명에 `long` 이 다닌다**는 것까지다. 실행 시간은 재지 않았다(규칙 4).

### (3) ★★ 시간 재기 — 단조 시계와 참/거짓 로그

```kotlin
// measure50.kt
import kotlin.time.Duration.Companion.hours
import kotlin.time.Duration.Companion.milliseconds
import kotlin.time.TimeSource
import kotlin.time.measureTime
import kotlin.time.measureTimedValue

fun main() {
    val took = measureTime { Thread.sleep(100) }
    println("1 measureTime >= 100ms: ${took >= 100.milliseconds}")

    val (value, took2) = measureTimedValue { Thread.sleep(100); 42 }
    println("2 measureTimedValue value=$value, >= 100ms: ${took2 >= 100.milliseconds}")

    val mark = TimeSource.Monotonic.markNow()
    Thread.sleep(100)
    println("3 mark.elapsedNow() >= 100ms: ${mark.elapsedNow() >= 100.milliseconds}")

    val later = TimeSource.Monotonic.markNow()
    println("4 later > mark: ${later > mark}, later - mark >= 100ms: ${later - mark >= 100.milliseconds}")

    val deadline = mark + 1.hours
    println("5 deadline.hasPassedNow(): ${deadline.hasPassedNow()}, hasNotPassedNow(): ${deadline.hasNotPassedNow()}")

    println("6 TimeSource.Monotonic.toString() -> ${TimeSource.Monotonic}")
}
```

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

- ★★ **`measureTime { }` 은 `Duration` 을 돌려준다** — 100ms 를 재운 블록이 `>= 100ms` 다. **`measureTimedValue { }`** 는 값과 시간을 짝으로 준다(`value=42`).
- ★★ **`markNow()` → `elapsedNow()`** — 마크를 찍고 나중에 「그 뒤로 얼마나」를 묻는다. 두 마크는 **비교(`>`)·뺄셈(`-`)** 이 된다 · 마크에 `Duration` 을 더하면 **마감 시각**이 되고 `hasPassedNow()`·`hasNotPassedNow()` 로 묻는다.
- ★★★ **이 시계가 무엇인지 스스로 말한다** — `TimeSource.Monotonic.toString()` 이 **`TimeSource(System.nanoTime())`**. JVM 의 **단조 시계**다 — 벽시계를 사람이 고쳐도 뒤로 안 간다.
- ★★ **Go 와의 대비** — Go 는 `time.Now()` 한 값 **안에** 벽시계와 단조 시계를 같이 넣고(`m=`), 어떤 연산 뒤에는 단조 쪽이 **조용히 벗겨진다**([Go 48번](../../../go/syntax/48-time-monotonic-clock-duration-timer-and-ticker/)). Kotlin 은 **처음부터 타입이 둘**이다 — 재기는 `TimeMark`(단조), 시각은 `Instant`(벽시계). 벗겨질 것이 없다.

### (4) ★★★ `kotlin.time.Instant` — 몇 판부터 opt-in 없이 되나

같은 프로그램을 두 벌 둔다 — 그대로인 `inst50.kt` 와, 첫 줄에 `@file:OptIn(kotlin.time.ExperimentalTime::class)` 만 더한 `inst50o.kt`. 판마다 `-language-version` 과 `-api-version` 을 같이 바꾼다.

```kotlin
// inst50.kt
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

```python
# grid50i.py
import re
import subprocess

VERSIONS = ["2.0", "2.1", "2.2", "2.3", "2.4"]
FILES = ["inst50.kt", "inst50o.kt"]

print("\t".join(["file"] + VERSIONS))
blocked = cells = 0
for src in FILES:
    row = []
    for v in VERSIONS:
        out = "o50i-" + src[:-3] + "-" + v.replace(".", "")
        run = subprocess.run(["kotlinc", "-language-version", v, "-api-version", v, src, "-d", out],
                             capture_output=True, text=True)
        errors = [l for l in (run.stdout + run.stderr).splitlines() if re.match(r"\S+\.kt:\d+:\d+: error: ", l)]
        if run.returncode == 0:
            cell = "ok"
        else:
            first = re.sub(r"^\S+\.kt:\d+:\d+: error: ", "", errors[0]) if errors else "exit %d" % run.returncode
            cell = "%d errors, first: %s" % (len(errors), first)
            blocked += 1
        cells += 1
        row.append(cell)
    if len(row) != len(VERSIONS):
        raise SystemExit("cell count mismatch: " + src)
    print("\t".join([src] + row))
print("blocked cells: %d / %d" % (blocked, cells))
```

```text
===== python3 grid50i.py =====
file	2.0	2.1	2.2	2.3	2.4
inst50.kt	21 errors, first: this declaration needs opt-in. Its usage must be marked with '@kotlin.time.ExperimentalTime' or '@OptIn(kotlin.time.ExperimentalTime::class)'	21 errors, first: this declaration needs opt-in. Its usage must be marked with '@kotlin.time.ExperimentalTime' or '@OptIn(kotlin.time.ExperimentalTime::class)'	21 errors, first: this declaration needs opt-in. Its usage must be marked with '@kotlin.time.ExperimentalTime' or '@OptIn(kotlin.time.ExperimentalTime::class)'	ok	ok
inst50o.kt	ok	ok	ok	ok	ok
blocked cells: 3 / 10
(exit 0)
```

- ★★★ **opt-in 없는 파일은 2.0·2.1·2.2 에서 막히고 2.3·2.4 에서 통과한다** — 막힌 칸의 진단은 **「없다」가 아니라 「opt-in 이 필요하다」**(`this declaration needs opt-in. Its usage must be marked with '@kotlin.time.ExperimentalTime' …`) 다.
- ★★★ **opt-in 을 단 파일은 다섯 판 모두 통과한다** — **2.0 에서도**. 그래서 「2.1.0 에 들어왔다」는 이 격자로는 **안 보인다**. `@WasExperimental(ExperimentalTime::class)` 가 붙은 선언은 **Stable 이 된 판(2.3) 이전의 `-api-version` 에서 「실험적」으로 보일 뿐 「없음」으로 보이지 않는다** — 그 판 경계는 이 창 밖이다(제5의 상태).
- ★ 막힌 칸의 **오류 개수가 21** 인 것은 `Instant`·`Clock`·`toJavaInstant`·`toKotlinInstant` 를 쓰는 **자리마다** 진단이 나서다 — 한 파일이 한 번 막히는 것이 아니다.

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

- ★★ **`kotlin.time.Instant` ↔ `java.time.Instant`** — `toJavaInstant()` 는 **`java.time.Instant`** 를 돌려주고(`2`), `toKotlinInstant()` 는 그 반대다(`3`). 둘 다 `jvmMain/jdk8` 쪽에 있다 — JVM 전용 변환이다.
- ★★ **`Instant` 끼리 빼면 `Duration`**(`5` — `1h 30m`) · 오프셋이 붙은 문자열을 `parse` 하면 **UTC 로 정규화**된다(`6` — `+09:00` 의 21시가 `12:00:00Z`).
- ★ `now()` 는 참/거짓으로만 찍었다(`4`). ★★ **`Clock.now()` 의 KDoc 은 「나중에 부르면 더 큰 `Instant` 를 준다」를 보장하지 않는다**((5)) — 그래서 **경과 시간은 `Instant` 뺄셈이 아니라 (3)의 단조 마크**로 잰다.

### (5) ★★ stdlib 소스 — 선언과 계약

```text
===== unzip -o -q kotlin-stdlib-sources.jar 'commonMain/kotlin/time/*' 'jvmMain/kotlin/time/*' 'jvmMain/jdk8/kotlin/time/*' commonMain/kotlin/util/Preconditions.kt commonMain/kotlin/util/Standard.kt jvmMain/kotlin/util/AssertionsJVM.kt commonMain/kotlin/contracts/ContractBuilder.kt commonMain/kotlin/coroutines/intrinsics/Intrinsics.kt jvmMain/kotlin/coroutines/cancellation/CancellationException.kt =====
(exit 0)
===== unzip -o -q kotlinx-coroutines-core-jvm-1.11.0-sources.jar commonMain/CoroutineScope.kt commonMain/Supervisor.kt commonMain/Guidance.kt commonMain/CoroutineExceptionHandler.kt commonMain/Yield.kt commonMain/NonCancellable.kt -d kxs =====
(exit 0)
```

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

- ★★★ **범위 계약** — 「`The type can store duration values up to ±146 years with nanosecond precision, and up to ±146 million years with millisecond precision.`」 · 「`… doesn't fit into the above range, the returned Duration is infinite.`」 — (1)의 「584년이 무한이 아니다」가 이 두 줄이다(나노초 범위는 넘었지만 밀리초 범위 안이다).
- ★★ **선언** — `@SinceKotlin("1.6")` · `@JvmInline` · `value class Duration` · 알맹이 `rawValue: Long`(생성자는 `@Deprecated(level = ERROR)` 로 막혀 있다 — 직접 못 만든다).
- ★★ **단조 시계의 실체** — `MonotonicTimeSource` 가 **`System.nanoTime()`** 을 읽는다(`@SinceKotlin("1.3")`).
- ★★★ **`Instant`·`Clock` 은 `@SinceKotlin("2.3")` + `@WasExperimental(ExperimentalTime::class)`** — (4)의 격자가 **2.3 에서 갈린 이유**다.
- ★★ **`Clock` KDoc 은 두 가지를 말한다** — 구현 안에서 `Clock.System` 을 직접 부르지 말고 **`Clock` 을 넘기라**(테스트를 결정적으로) · `now()` 를 나중에 불러도 **더 큰 `Instant` 를 보장하지 않는다.**
- ★★ **아직 `@ExperimentalTime` 이 붙은 것은 두 자리뿐**이다 — `Duration.convert(value, sourceUnit, targetUnit)` 와 `TimeSources.kt` 의 `AbstractDoubleTimeSource`(이쪽은 `@Deprecated` 가 바로 뒤따른다). `Duration`·`measureTime`·`TimeSource.Monotonic`·`Instant`·`Clock` 은 **opt-in 이 필요 없다**(이 판).

## 문법 — 형태와 규칙

**형태** — 재시도 정책을 `Duration` 으로 받고, 문자열에서 읽고, 단조 마크로 마감까지 돈다.

```kotlin
// form50.kt
import kotlin.time.Duration
import kotlin.time.Duration.Companion.milliseconds
import kotlin.time.Duration.Companion.seconds
import kotlin.time.TimeSource

data class RetryPolicy(val timeout: Duration, val backoff: Duration, val attempts: Int)

fun parsePolicy(timeout: String, backoff: String): RetryPolicy =
    RetryPolicy(Duration.parse(timeout), Duration.parse(backoff), attempts = 3)

fun main() {
    val p = parsePolicy("1m 30s", "PT0.25S")
    println(p)
    println("total backoff ${p.backoff * p.attempts} | timeout in ms ${p.timeout.inWholeMilliseconds}")
    println("fits in 2 minutes: ${p.timeout + p.backoff * p.attempts <= 2.seconds * 60}")
    val start = TimeSource.Monotonic.markNow()
    val deadline = start + 250.milliseconds
    var polls = 0
    while (deadline.hasNotPassedNow()) {
        polls++
        Thread.sleep(50)
    }
    println("polled until the deadline: ${polls >= 1}, elapsed >= 250ms: ${start.elapsedNow() >= 250.milliseconds}")
}
```

```text
===== kotlinc form50.kt -d o50f =====
(exit 0)
===== java -cp o50f:kotlin-stdlib.jar Form50Kt =====
RetryPolicy(timeout=1m 30s, backoff=250ms, attempts=3)
total backoff 750ms | timeout in ms 90000
fits in 2 minutes: true
polled until the deadline: true, elapsed >= 250ms: true
(exit 0)
```

**규칙 불릿**

- **만들기** — `5.seconds` · `300.milliseconds` · `1.days`(`Duration.Companion` 의 확장 프로퍼티 — `import kotlin.time.Duration.Companion.seconds`) · `Duration.parse("1m 30s")` · `Duration.parse("PT0.25S")`((1) · 형태).
- **꺼내기** — `inWholeMilliseconds` · `inWholeSeconds` 등은 `Long` 을 준다 — **여기서 단위가 다시 이름으로 돌아간다**((1)의 `pauseMs(5.seconds.inWholeMilliseconds)`).
- **산술** — `Duration ± Duration` · `Duration * Int` · `Duration / Duration`(→ `Double`) · 비교 — **맨 숫자와 섞으면 컴파일 에러**((1)).
- **무한** — `Duration.INFINITE` · 부호 다른 무한끼리 더하면 `IllegalArgumentException` · 표현 범위를 넘기면 **무한으로 포화**(단, 나노초 → 밀리초로 옮겨 탈 수 있는 동안은 아니다)((1)(5)).
- **재기** — `measureTime { }` · `measureTimedValue { }` · `TimeSource.Monotonic.markNow()` → `elapsedNow()` · 마크 + `Duration` = 마감((3)).
- **시각** — `Clock.System.now(): kotlin.time.Instant`(2.3+ opt-in 없음) · `toJavaInstant()`/`toKotlinInstant()`((4)).

## 어디서 틀리나

1. ★★★ **`Long` 인자에 단위를 이름으로만 적어 두고 안심한다.** `pauseMs(5)` 는 5초를 뜻했어도 통과한다 — `Duration` 으로 받아야 컴파일러가 막는다((1)).
2. ★★★ **`Thread.sleep(5)` · `delay(5)` 를 초로 읽는다.** 둘 다 밀리초다((1)).
3. ★★ **`Thread.sleep(5.seconds)` 가 될 것이라 본다.** JDK 가 받는 것은 `java.time.Duration` 이다 — `toJavaDuration()` 을 거쳐야 한다((1)).
4. ★★ **`Duration` 은 넘치면 곧바로 포화한다고 본다.** 나노초 정밀도를 넘으면 **밀리초 정밀도로 옮겨 타고**, 그 범위까지 넘어야 무한이다((1)(5)).
5. ★★ **경과 시간을 `Instant` 뺄셈으로 잰다.** 벽시계는 뒤로 갈 수 있다 — KDoc 이 「더 큰 값」을 보장하지 않는다. 재기는 단조 마크로((3)(4)).
6. ★★ **`kotlin.time.Instant` 는 아직 실험적이라 본다.** 2.3 부터 opt-in 이 필요 없다 — 다만 **`-api-version` 을 2.2 이하로 두면 다시 opt-in 이 필요하다**((4)).
7. ★ **`Duration` 을 쓰면 비용이 0 이라고 적는다.** `javap` 가 보여 주는 것은 서명의 `long` 까지 — 널 가능·컬렉션 자리에서는 **객체로 박싱**된다((2)).

## 구현 세부사항 대 언어 보장

| 항목 | 어느 쪽인가 | 근거 |
|---|---|---|
| `Duration` 에 맨 숫자를 못 넣는다 | ★★★ **언어 규칙** — 타입이 다르면 인자가 안 맞는다(암묵 변환 없음) | (1) · [01번 주제](../01-val-var-and-basic-types/) |
| `Thread.sleep(Long)` · `delay(Long)` 이 밀리초 | ★★ **API 계약**(JDK · kotlinx-coroutines) — 언어가 아니다 | (1) |
| 범위 ±146년(나노초) · ±146백만 년(밀리초) · 넘치면 무한 | ★★★ **API 계약(KDoc)** | (5) |
| `Duration` 이 `value class` | ★★ **API 계약(선언)** | (5) |
| JVM 서명이 `long` · 이름 뭉개기 해시 | ★ **JVM 백엔드 구현** — 이 판의 관찰 | (2) |
| 단조 시계가 `System.nanoTime()` | ★ **stdlib 구현**(JVM) | (3)(5) |
| `Instant`·`Clock` Stable 2.3 · 그 전 판은 opt-in | ★★ **stdlib 선언의 주석**(`@SinceKotlin` + `@WasExperimental`) — 컴파일러가 `-api-version` 으로 읽는다 | (4)(5) |
| 「`Duration` 은 비용 0」 | **재지 않았다** | — |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 내 API 가 타임아웃·간격을 받는다 | ★ **`Duration` 인자** | (1) — 맨 숫자를 컴파일러가 막는다 |
| JDK·옛 API 가 `Long` 밀리초만 받는다 | 경계에서 `inWholeMilliseconds` · `toJavaDuration()` | (1) — 변환 자리를 **한 곳**으로 |
| 설정 파일에서 읽는다 | `Duration.parse("1m 30s")` · ISO(`PT0.25S`) | 형태 블록 |
| 경과 시간·마감 | `measureTime` · `markNow()` + `hasNotPassedNow()` | (3) — 단조 |
| 기록·전송할 시각 | `Clock.System.now()` → `Instant`(2.3+) | (4) — 벽시계 |
| 테스트에서 시각을 고정 | `Clock` 을 **인자로 넘긴다** | (5) — `Clock` KDoc 「`Instead, you can pass a [Clock] explicitly to the necessary functions or classes.`」 |

## 핵심 문장

1. **단위가 이름에 있으면 컴파일러는 모른다** — `pauseMs(5)` 는 통과하고, **`Duration` 을 받는 자리의 맨 숫자는 막힌다**(이 격자에서 25칸 중 6칸).
2. `Thread.sleep(5)` · `delay(5)` 는 **밀리초**다. `Thread.sleep` 이 받는 `Duration` 은 **`java.time.Duration`** 이다.
3. `Duration` 은 **넘치면 먼저 밀리초 정밀도로 옮겨 타고**, 그 범위까지 넘어야 **무한으로 포화**한다.
4. `Duration` 은 JVM 에서 **`long`** 이다 — 받는 함수는 이름이 뭉개진다(`-해시`). 널 가능·제네릭 자리에서는 박싱된다.
5. **재기는 단조 마크**(`System.nanoTime()`), **시각은 `Instant`**(2.3 부터 opt-in 없음 · `-api-version` 2.2 이하는 opt-in).

## 관련 자료

- [01번 주제](../01-val-var-and-basic-types/) — ★ **선행.** 암묵 수치 변환이 없다 — (1)의 진단이 같은 성질이다. 그쪽은 **`Int`·`Long` 사이**, 여기는 **`Long`·`Duration` 사이**.
- [26번 주제](../26-value-class-and-boxing/) — `value class` 의 이름 뭉개기·박싱. 여기의 (2)는 그 규칙을 `Duration` 에 대 본 것이다.
- [Go 48번](../../../go/syntax/48-time-monotonic-clock-duration-timer-and-ticker/) — 단조 시계가 `time.Time` **안에** 있는 설계(`m=`). 그쪽은 **한 값에 두 시계**, 여기는 **두 타입에 두 시계**.
- [52번 주제](../52-coroutine-basics-suspend-scope-launch-async/)(`delay` 가 스레드를 안 막는 것) · [53번 주제](../53-structured-concurrency-job-cancellation-exceptions/)(`withTimeout`).

## 용어 풀이

> **`Duration`** — 시간의 길이. 단위를 타입 안에 품은 `value class`.\
> 예: `5.seconds + 300.milliseconds` → `5.3s`.

> **단조 시계(monotonic clock)** — 뒤로 가지 않는 시계. 벽시계 조정에 흔들리지 않아 **경과 시간**을 잴 때 쓴다. JVM 에서는 `System.nanoTime()`.

> **벽시계(wall clock)** — 달력의 시각. 사람이·NTP 가 고칠 수 있어 **뒤로 갈 수 있다.** `Clock.System.now()`.

> **`TimeMark`** — `markNow()` 로 찍은 한 순간. 나중에 `elapsedNow()` 로 「그 뒤로 얼마나」를 묻는다.

> **`Instant`** — 에포크(1970-01-01T00:00:00Z)로부터의 한 시각. `kotlin.time.Instant` 는 2.3 에서 Stable.

> **`@WasExperimental`** — 「예전에는 실험적이었다」는 표지. 그 판보다 낮은 `-api-version` 에서는 **opt-in 을 요구**하게 만든다.

> **ISO-8601 기간 표기** — `PT1M30S` 처럼 `P`(기간)·`T`(시각 부분) 뒤에 단위 글자를 붙이는 표준 꼴.

## 더 들어가면

- **`Duration` 의 알맹이 한 비트** — `rawValue` 의 **맨 아래 비트가 단위(나노초/밀리초)를 가른다**(`unitDiscriminator` — 소스 41행). (1)의 「밀리초로 옮겨 탄다」의 실체일 것이다 — **돌려서 확인하지는 않았다.**
- **`TestTimeSource`** — 테스트에서 시간을 손으로 흘리는 `TimeSource`. 이 판의 소스에 있으나 돌리지 않았다.
- **`kotlinx-datetime`** — 달력 계산(날짜·시간대)은 stdlib 밖 라이브러리의 몫이다. 이 머신에 없어 보지 않았다.
