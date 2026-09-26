# kotlin/syntax/50 — `kotlin.time` — `Duration`·시간 측정 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [01번 주제](../01-val-var-and-basic-types/)(`val`/`var` 와 기본 타입 — 암묵 수치 변환이 없다)다.
> 문항 10개 중 예측형은 5개이고, 그중 코드블록이 붙는 것은 4개다.
> 이 주제의 모든 답은 **kotlinc 2.4.20 · Temurin JDK 21.0.5** 에서 실제로 던져 받은 것이다(`delay` 두 칸만 kotlinx-coroutines 1.11.0).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 스물다섯 줄의 시간 인자 (예측)

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

- 각 행의 `compile` 칸은 `ok` 인가 진단인가? `ok` 인 행의 `value` 는? 마지막 줄의 `N / M` 은?

### 2. ★★ 넘치는 두 곱셈 (왜)

- 1번의 `Long.MAX_VALUE.nanoseconds * 2` 행과 `(Long.MAX_VALUE / 2).milliseconds * 3` 행의 `value` 를 stdlib KDoc 의 어느 문장으로 설명하나?

### 3. ★★ JVM 에서의 서명 (예측)

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

- `javap -p Dur50Kt.class` 에서 `pauseFor`·`pauseMs`·`makeTimeout`·`maybe`·`many`·`mark` 의 서명은 각각 어떻게 보이나?

### 4. ★★ 재기 여섯 줄 (예측)

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

- 여섯 줄의 출력은 무엇인가? `6` 줄은 무엇을 드러내나?

### 5. ★★★ `Instant` 두 파일 × 다섯 판 (예측)

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

- `inst50o.kt` 는 위 파일의 **첫 줄에 `@file:OptIn(kotlin.time.ExperimentalTime::class)` 한 줄**과 빈 줄을 더한 것이다. 열 칸은 각각 `ok` 인가 진단인가? 마지막 줄의 `N / M` 은?

### 6. ★ `Instant` 여섯 줄 (예측)

- 5번의 `inst50.kt` 를 2.4 기본값으로 돌리면 여섯 줄은 무엇인가?

### 7. `Thread.sleep` 과 `kotlin.time.Duration` (경계)

- 1번의 `Thread.sleep(5.seconds)` 칸을 JDK 쪽 `Thread.sleep` 의 오버로드로 설명하면? `kotlin.time.Duration` 을 `Thread.sleep` 에 넘기려면 무엇을 한 번 거쳐야 하나?

### 8. 「2.1.0 도입」은 어디에 보이나 (경계)

- 5번의 격자로 「`kotlin.time.Instant` 가 2.1 에 들어왔다」를 확인할 수 있나? 없다면 무엇이 그 경계를 가리나?

### 9. 재기와 시각 — Go 의 `m=` 와 (연결)

- [Go 48번](../../../go/syntax/48-time-monotonic-clock-duration-timer-and-ticker/)은 단조 시계를 `time.Time` 값 **안에** 두었다. Kotlin 은 경과 시간과 시각을 **무엇으로 가르나**? 그래서 Go 에서 나던 어떤 사고가 여기서는 안 나나?

### 10. 「`Duration` 은 비용이 없다」 (경계)

- 3번의 `javap` 로 말할 수 있는 것과 **말할 수 없는 것**은 각각 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
