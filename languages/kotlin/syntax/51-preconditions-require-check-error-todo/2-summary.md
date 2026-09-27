# kotlin/syntax/51 — 계약 함수 — `require`/`check`/`error`/`TODO` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — **이 판의 stdlib 소스 jar**(`kotlin-stdlib-sources.jar` 2.4.20)의 `Preconditions.kt`·`Standard.kt`·`AssertionsJVM.kt`·`ContractBuilder.kt` — KDoc 과 구현((5)). ★ 공식 문서 페이지는 **이 작업에서 열지 못했다**(외부 네트워크를 쓰지 않았다).
> **실행 검증** — 이 문서의 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `java`·`javap` 에서 실제로 얻었다.\
> `kotlinc` 9회(`-Xassertions` 격자 스크립트 안의 4회 · 계약 격자 스크립트 안의 1회 포함) · `java` 12회(두 격자 스크립트 안의 10회 포함) · `javap` 1회 · stdlib 소스 jar 발췌 6곳.\
> ★★ 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적지 않았다. **「갈린 행 N / M」·「던진 칸 N / M」·「막힌 탐침 N / M」은 스크립트가 스스로 센 것**이다.
> **버전** — 이 판의 소스에서 `require`·`check`·`error`·`TODO` 는 `@kotlin.internal.InlineOnly` 인 **`inline fun`** 이고, 계약 표지 `ExperimentalContracts` 는 **`@SinceKotlin("1.3")` + `@RequiresOptIn`** 이다((5)) — ★★★ **2.4.20 에서도 직접 계약을 쓰려면 opt-in 이 필요하다**((3)).
> **경계** — ★★★ **`Nothing` 타입**(`error()`·`TODO()` 가 돌아오지 않는다는 것 · `?:` 뒤에 쓸 수 있는 까닭)과 검사 예외가 없다는 것은 [34번 주제](../34-exceptions-nothing-and-try-expression/)가 정본이다. **`TODO()` 의 `NotImplementedError` 가 `catch (e: Exception)` 을 빠져나간다**는 것은 [49번 주제](../49-result-and-runcatching/) (4)가 이미 쟀다(다섯 중 둘이 `Error`) — 여기서는 다시 안 잰다.
> 이 본문은 Claude 작성이다(원고 없음).

★★★ **본체는 첫째 창이다** — 「**던지는 예외 격자 — 계약 함수 열한 가지 × JVM 두 벌(`java` · `java -ea`) → 예외 클래스 · 기본 메시지**」. 이 주제는 **계약·규약형**이라(§2-1 규칙 6) 「어기면 무엇이 출력되나」를 전수로 찍는 것이 본체다.

## 이 주제가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **언어 보장 / API 계약** | 서명·KDoc 이 약속한 것 | ★★★ `require` KDoc 「**Throws an [IllegalArgumentException]**」 · `check` 는 **`IllegalStateException`** · `error` 는 **`IllegalStateException`** 을 던지고 반환 타입 **`Nothing`** · `assert` KDoc 「**runtime assertions have been enabled on the JVM using the -ea JVM option**」 · 계약 `returns() implies value` |
| **구현(컴파일러·stdlib)** | 이 판이 실제로 하는 것 | ★★ 기본 메시지 문자열(`Failed requirement.` · `Check failed.` · `Required value was null.` · `An operation is not implemented.`) · 전부 `inline` 이라 **메시지 람다가 객체로 안 생긴다** · `-Xassertions` 의 네 모드 |
| **이 판의 관찰** | kotlinc 2.4.20 에서 이번에 본 것 | 격자 값 · 진단 문구 · `javap` 발췌 |

## 이 판

```text
===== kotlinc -version =====
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | (이 주제에는 없다) | 해시코드·주소·시간·스택 트레이스를 찍지 않았다 |
| 안 흔들린다 | 던지기 격자 11행 × 2벌 · 예외 클래스 · 메시지 · 갈린 행 수 | stdlib 의 상수 문자열과 JVM 플래그로 정해진다 |
| 안 흔들린다 | `-Xassertions` 4모드 × 2벌 · 조건이 평가됐나 | 컴파일 모드와 `-ea` 로 정해진다 |
| 안 흔들린다 | 계약 격자 9탐침 · 진단 문구 · `javap` 발췌(오프셋·상수 풀 번호째) · 종료 코드 | 같은 판이면 같다 |

★ 근거 — 캡처 스크립트를 처음부터 두 번 돌려 **블록 전체를 대조**했다(수치는 3-answer 의 「실행 검증」).

## 한눈에 — 쉽게 말하면

**`require` 는 「접수 창구의 서류 검사」이고 `check` 는 「기계의 상태 점검」이다.** 창구에서 서류가 틀리면 **손님(호출자)의 잘못**이다 — `IllegalArgumentException`. 기계가 멈춰 있는데 돌리라고 하면 **서류는 맞아도 지금 상태가 안 된다** — `IllegalStateException`. `error("…")` 는 「있을 수 없는 일」을 외치는 비상벨이고(역시 `IllegalStateException`), `TODO()` 는 「공사 중」 팻말이다 — 이건 **예외(`Exception`)가 아니라 `Error`** 라서 보통의 그물을 빠져나간다.
★ `assert` 는 **스위치를 켜야**(`-ea`) 울리는 경보기다 — 꺼져 있으면 조용하다.

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 서류 검사(손님 잘못) | `require` · `requireNotNull` → `IllegalArgumentException` | (1) ★★★ |
| 상태 점검(지금은 안 됨) | `check` · `checkNotNull` · `error` → `IllegalStateException` | (1) ★★★ |
| 공사 중 팻말 | `TODO()` → `NotImplementedError`(**`Error`**) | (1) · [49번 주제](../49-result-and-runcatching/) |
| 스위치로 켜는 경보기 | `assert` — `-ea` · `-Xassertions` | (2) ★ |
| 검사를 통과했으니 믿어도 된다 | 계약 `returns() implies (x != null)` → 스마트 캐스트 | (3) ★★ |

```text
   누구의 잘못인가 → 무엇을 던지나

   require(인자 조건)        ── 거짓 ──▶  IllegalArgumentException   "Failed requirement."
   requireNotNull(인자)      ── null ──▶  IllegalArgumentException   "Required value was null."
   check(상태 조건)          ── 거짓 ──▶  IllegalStateException      "Check failed."
   checkNotNull(상태)        ── null ──▶  IllegalStateException      "Required value was null."
   error("m")                ─────────▶  IllegalStateException      "m"            반환 타입 Nothing
   TODO()                    ─────────▶  NotImplementedError(Error) "An operation is not implemented."
   assert(조건)              ── 거짓 ──▶  -ea 일 때만 AssertionError(Error)
```

## 이 주제가 답하려는 질문

1. 계약 함수마다 **어느 예외 클래스를 어떤 기본 메시지로** 던지나 — 그리고 **어느 것이 JVM 플래그에 따라 갈리나.**
2. `require(x != null)` 뒤에서 `x.length` 가 되는 것은 **무엇 덕분**인가 — 내가 만든 검증 함수는 왜 안 되고, **어떻게 하면** 되나(이 판에서 아직 실험적인가).
3. 메시지 람다는 **언제** 만들어지나 — 통과할 때도 비용을 내나.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **던지기 격자(실행 × JVM 두 벌)** | 예외 클래스 · 메시지((1)) | ★ **본체 창** — 스크립트가 같은 클래스를 `java`·`java -ea` 로 두 번 돌려 합친다 |
| ★★ **`-Xassertions` 판 격자** | 컴파일 모드 × `-ea` → 던졌나 · **조건을 평가했나**((2)) | 조건 함수가 부를 때마다 계수를 올린다 |
| ★★ **계약 판별 격자(컴파일)** | 스마트 캐스트가 되나 · 진단((3)) | 49편의 격자와 같은 꼴 |
| ★★ **계수 로그 + `javap -c`** | 메시지를 몇 번 만들었나 · 람다가 객체가 되나((4)) | — |
| ★★ **stdlib 소스 jar 발췌** | KDoc 계약 · 기본 메시지 · 계약 선언((5)) | — |
| **인용 — 다시 안 잰다** | `Nothing` 타입 · `?:` 뒤 `error()` · `TODO()` 가 `catch (e: Exception)` 을 빠져나감 | [34번](../34-exceptions-nothing-and-try-expression/) · [49번](../49-result-and-runcatching/) |
| **부적용 — 실행 시간** | 「`require` 는 공짜」는 **재지 않았다** — (4)는 **메시지 생성 횟수**만 센다 | — |

### (1) ★★★ 던지는 예외 격자 — 열한 가지 × JVM 두 벌

**언제 쓰나** — 함수 첫머리에 검사를 넣을 때, 그리고 로그에서 예외 클래스를 보고 **누구의 잘못인지** 가를 때.

```kotlin
// throw51.kt
val none: String? = null

val throwers: List<Pair<String, () -> Unit>> = listOf(
    "require(false)" to { require(false) },
    "require(false) { \"m\" }" to { require(false) { "m" } },
    "requireNotNull(none)" to { requireNotNull(none) },
    "check(false)" to { check(false) },
    "check(false) { \"m\" }" to { check(false) { "m" } },
    "checkNotNull(none)" to { checkNotNull(none) },
    "error(\"m\")" to { error("m") },
    "TODO()" to { TODO() },
    "TODO(\"m\")" to { TODO("m") },
    "assert(false)" to { assert(false) },
    "assert(false) { \"m\" }" to { assert(false) { "m" } },
)

fun main() {
    for ((name, f) in throwers) {
        val e = runCatching(f).exceptionOrNull()
        val row = listOf(name, e?.let { it::class.qualifiedName } ?: "(nothing thrown)", e?.message ?: "-")
        println(row.joinToString("\t"))
    }
}
```

```python
# grid51.py
import collections
import subprocess

CP = "o51t:kotlin-stdlib.jar"
MODES = [("java", []), ("java -ea", ["-ea"])]

runs = {}
for label, flags in MODES:
    out = subprocess.run(["java"] + flags + ["-cp", CP, "Throw51Kt"], capture_output=True, text=True, check=True)
    runs[label] = [line.split("\t") for line in out.stdout.splitlines()]

print("\t".join(["thrower", "java: class", "java: message", "java -ea: class", "java -ea: message"]))
differ = 0
rows = len(runs["java"])
for a, b in zip(runs["java"], runs["java -ea"]):
    if len(a) != 3 or len(b) != 3 or a[0] != b[0]:
        raise SystemExit("cell count mismatch: %r %r" % (a, b))
    print("\t".join([a[0], a[1], a[2], b[1], b[2]]))
    if a[1:] != b[1:]:
        differ += 1
count = collections.Counter(r[1].rsplit(".", 1)[-1] for r in runs["java -ea"])
print("classes under java -ea: " + " · ".join("%s %d" % kv for kv in sorted(count.items())))
print("rows that differ between java and java -ea: %d / %d" % (differ, rows))
```

```text
===== kotlinc throw51.kt -d o51t =====
(exit 0)
```

```text
===== python3 grid51.py =====
thrower	java: class	java: message	java -ea: class	java -ea: message
require(false)	java.lang.IllegalArgumentException	Failed requirement.	java.lang.IllegalArgumentException	Failed requirement.
require(false) { "m" }	java.lang.IllegalArgumentException	m	java.lang.IllegalArgumentException	m
requireNotNull(none)	java.lang.IllegalArgumentException	Required value was null.	java.lang.IllegalArgumentException	Required value was null.
check(false)	java.lang.IllegalStateException	Check failed.	java.lang.IllegalStateException	Check failed.
check(false) { "m" }	java.lang.IllegalStateException	m	java.lang.IllegalStateException	m
checkNotNull(none)	java.lang.IllegalStateException	Required value was null.	java.lang.IllegalStateException	Required value was null.
error("m")	java.lang.IllegalStateException	m	java.lang.IllegalStateException	m
TODO()	kotlin.NotImplementedError	An operation is not implemented.	kotlin.NotImplementedError	An operation is not implemented.
TODO("m")	kotlin.NotImplementedError	An operation is not implemented: m	kotlin.NotImplementedError	An operation is not implemented: m
assert(false)	(nothing thrown)	-	java.lang.AssertionError	Assertion failed
assert(false) { "m" }	(nothing thrown)	-	java.lang.AssertionError	m
classes under java -ea: AssertionError 2 · IllegalArgumentException 3 · IllegalStateException 4 · NotImplementedError 2
rows that differ between java and java -ea: 2 / 11
(exit 0)
```

- ★★★ **`require` 계열 3행은 전부 `IllegalArgumentException`**, **`check` 계열 3행과 `error` 는 전부 `IllegalStateException`** 이다 — 클래스가 곧 「인자가 틀렸다」와 「상태가 틀렸다」의 구분이다.
- ★★★ **기본 메시지** — `require(false)` 는 **`Failed requirement.`** · `check(false)` 는 **`Check failed.`** · `requireNotNull`·`checkNotNull` 은 **둘 다 `Required value was null.`**(클래스만 다르다) · `TODO()` 는 **`An operation is not implemented.`** · `TODO("m")` 은 **`An operation is not implemented: m`** · `assert(false)` 는 (`-ea` 일 때) **`Assertion failed`**(마침표 없음).
- ★★★ **갈린 행은 11행 중 2행** — `assert` 둘뿐이다. `java` 에서는 **아무것도 안 던지고**(`(nothing thrown)`), `java -ea` 에서야 `java.lang.AssertionError` 다. 나머지 아홉은 JVM 플래그와 무관하다.
- ★★ **`TODO` 의 클래스는 `kotlin.NotImplementedError`** — `java.lang` 이 아니라 **Kotlin stdlib 의 클래스**이고, `Error` 를 상속한다((5)). 그래서 `catch (e: Exception)` 을 빠져나간다 — [49번 주제](../49-result-and-runcatching/) (4)의 「다섯 중 둘」 중 하나다.

### (2) ★★ `assert` 는 무엇이 켜나 — `-Xassertions` × `-ea`

```kotlin
// assert51.kt
var evaluated = 0

fun condition(): Boolean {
    evaluated++
    return false
}

fun main() {
    val e = runCatching { assert(condition()) { "m" } }.exceptionOrNull()
    println("${e?.let { it::class.simpleName } ?: "nothing thrown"}\tcondition evaluated $evaluated")
}
```

```python
# grid51a.py
import subprocess

MODES = ["legacy", "jvm", "always-enable", "always-disable"]
JVM = [("java", []), ("java -ea", ["-ea"])]

print("\t".join(["-Xassertions", "java", "java -ea"]))
threw = evaluated = cells = 0
for mode in MODES:
    out_dir = "o51a-" + mode
    subprocess.run(["kotlinc", "-Xassertions=" + mode, "assert51.kt", "-d", out_dir],
                   capture_output=True, text=True, check=True)
    row = []
    for _, flags in JVM:
        r = subprocess.run(["java"] + flags + ["-cp", out_dir + ":kotlin-stdlib.jar", "Assert51Kt"],
                           capture_output=True, text=True, check=True)
        cell = r.stdout.strip()
        row.append(cell)
        cells += 1
        threw += not cell.startswith("nothing thrown")
        evaluated += cell.endswith("evaluated 1")
    if len(row) != len(JVM):
        raise SystemExit("cell count mismatch: " + mode)
    print("\t".join([mode] + row))
print("cells that threw: %d / %d" % (threw, cells))
print("cells that evaluated the condition: %d / %d" % (evaluated, cells))
```

```text
===== python3 grid51a.py =====
-Xassertions	java	java -ea
legacy	nothing thrown	condition evaluated 1	AssertionError	condition evaluated 1
jvm	nothing thrown	condition evaluated 0	AssertionError	condition evaluated 1
always-enable	AssertionError	condition evaluated 1	AssertionError	condition evaluated 1
always-disable	nothing thrown	condition evaluated 0	nothing thrown	condition evaluated 0
cells that threw: 4 / 8
cells that evaluated the condition: 5 / 8
(exit 0)
```

- ★★★ **기본(`legacy`)에서는 `-ea` 없이 던지지 않지만 조건은 평가한다**(`condition evaluated 1`) — 조건식에 부수 효과가 있으면 **운영에서도 그 효과가 난다.** `assert` 가 보통의 `inline fun` 이라 인자(`condition()`)가 **부르기 전에** 계산되기 때문이다((5)의 선언).
- ★★★ **`-Xassertions=jvm` 은 Java 의 `assert` 처럼 컴파일한다** — `-ea` 가 없으면 **조건도 평가하지 않는다**(`condition evaluated 0`), `-ea` 면 던진다.
- ★★ `always-enable` 은 `-ea` 와 무관하게 던지고 · `always-disable` 은 무관하게 조용하며 조건도 안 본다.
- ★ 그래서 셈은 **던진 칸 4 / 8 · 조건을 평가한 칸 5 / 8** — `legacy` 의 `java` 칸이 「안 던졌는데 평가했다」는 **유일한 칸**이다.

### (3) ★★★ 계약 — `require(x != null)` 뒤의 스마트 캐스트

**언제 쓰나** — 검증 함수를 직접 만들 때. 표준 함수처럼 **통과한 뒤 널이 벗겨지게** 하고 싶을 때.

```kotlin
// contract51.kt
import kotlin.contracts.ExperimentalContracts
import kotlin.contracts.contract

fun ownCheck(ok: Boolean) {
    if (!ok) throw IllegalArgumentException("ownCheck")
}

@OptIn(ExperimentalContracts::class)
fun ownCheckC(ok: Boolean) {
    contract { returns() implies ok }
    if (!ok) throw IllegalArgumentException("ownCheckC")
}

fun ownCheckNoOptIn(ok: Boolean) {
    contract { returns() implies ok }                                        // contract-without-opt-in
    if (!ok) throw IllegalArgumentException("ownCheckNoOptIn")
}

fun p1(s: String?): Int { require(s != null); return s.length }             // require
fun p2(s: String?): Int { check(s != null); return s.length }               // check
fun p3(s: String?): Int { requireNotNull(s); return s.length }              // requireNotNull
fun p4(s: String?): Int { assert(s != null); return s.length }              // assert
fun p5(s: String?): Int { if (s == null) error("none"); return s.length }   // if-error
fun p6(s: String?): Int { ownCheck(s != null); return s.length }            // own-no-contract
fun p7(s: String?): Int { ownCheckC(s != null); return s.length }           // own-with-contract
fun p8(s: String?): Int { val t = s ?: TODO(); return t.length }            // elvis-TODO
```

```python
# grid51c.py
import re
import subprocess

SRC = "contract51.kt"

probes = {}
for n, line in enumerate(open(SRC, encoding="utf-8"), 1):
    m = re.search(r"// (\S+)$", line.rstrip("\n"))
    if m:
        probes[n] = m.group(1)

run = subprocess.run(["kotlinc", SRC, "-d", "o51c"], capture_output=True, text=True)
first = {}
count = {}
for line in (run.stdout + run.stderr).splitlines():
    m = re.match(r"contract51\.kt:(\d+):\d+: error: (.*)$", line)
    if m:
        n = int(m.group(1))
        count[n] = count.get(n, 0) + 1
        first.setdefault(n, m.group(2))

print("\t".join(["probe", "compile"]))
blocked = 0
for n, name in probes.items():
    cell = "ok" if n not in first else "%d error(s), first: %s" % (count[n], first[n])
    blocked += n in first
    print("\t".join([name, cell]))
print("exit %d" % run.returncode)
print("blocked probes: %d / %d" % (blocked, len(probes)))
```

```text
===== python3 grid51c.py =====
probe	compile
contract-without-opt-in	3 error(s), first: this declaration needs opt-in. Its usage must be marked with '@kotlin.contracts.ExperimentalContracts' or '@OptIn(kotlin.contracts.ExperimentalContracts::class)'
require	ok
check	ok
requireNotNull	ok
assert	1 error(s), first: only safe (?.) or non-null asserted (!!.) calls are allowed on a nullable receiver of type 'String?'.
if-error	ok
own-no-contract	1 error(s), first: only safe (?.) or non-null asserted (!!.) calls are allowed on a nullable receiver of type 'String?'.
own-with-contract	ok
elvis-TODO	ok
exit 1
blocked probes: 3 / 9
(exit 0)
===== kotlinc contract51.kt -d o51c2 =====
contract51.kt:15:5: error: this declaration needs opt-in. Its usage must be marked with '@kotlin.contracts.ExperimentalContracts' or '@OptIn(kotlin.contracts.ExperimentalContracts::class)'
    contract { returns() implies ok }                                        // contract-without-opt-in
    ^^^^^^^^
contract51.kt:15:16: error: this declaration needs opt-in. Its usage must be marked with '@kotlin.contracts.ExperimentalContracts' or '@OptIn(kotlin.contracts.ExperimentalContracts::class)'
    contract { returns() implies ok }                                        // contract-without-opt-in
               ^^^^^^^
contract51.kt:15:26: error: this declaration needs opt-in. Its usage must be marked with '@kotlin.contracts.ExperimentalContracts' or '@OptIn(kotlin.contracts.ExperimentalContracts::class)'
    contract { returns() implies ok }                                        // contract-without-opt-in
                         ^^^^^^^
contract51.kt:22:54: error: only safe (?.) or non-null asserted (!!.) calls are allowed on a nullable receiver of type 'String?'.
fun p4(s: String?): Int { assert(s != null); return s.length }              // assert
                                                     ^
contract51.kt:24:56: error: only safe (?.) or non-null asserted (!!.) calls are allowed on a nullable receiver of type 'String?'.
fun p6(s: String?): Int { ownCheck(s != null); return s.length }            // own-no-contract
                                                       ^
(exit 1)
```

- ★★★ **표준 `require`·`check`·`requireNotNull` 뒤에서는 `s.length` 가 된다** — 셋 다 `contract { returns() implies … }` 를 달고 있다((5)). 컴파일러가 「이 함수가 정상으로 돌아왔다면 조건이 참이다」를 알고 `s` 를 `String` 으로 좁힌다.
- ★★★ **직접 만든 `ownCheck` 는 계약이 없어 막힌다** — 「`only safe (?.) or non-null asserted (!!.) calls are allowed on a nullable receiver of type 'String?'.`」 **몸통이 똑같이 `throw` 해도** 컴파일러는 함수 **밖에서 안을 들여다보지 않는다.**
- ★★★ **같은 몸통에 계약을 달면(`ownCheckC`) 통과한다** — 다만 **`@OptIn(ExperimentalContracts::class)` 가 있어야 한다.** 빼면(`ownCheckNoOptIn`) `contract`·`returns`·`implies` **세 자리 모두** 「`this declaration needs opt-in`」이다. **2.4.20 에서도 계약은 아직 실험적**이다.
- ★★ **`assert` 에는 계약이 없다** — `assert(s != null)` 뒤는 막힌다. (2)에서 봤듯 `assert` 는 **돌아와도 조건이 참이라는 보장이 없으니**(꺼져 있으면 그냥 돌아온다) 계약을 달 수가 없는 것이 맞다.
- ★ `if (s == null) error("none")` 과 `s ?: TODO()` 는 계약이 아니라 **`Nothing`** 덕분에 통과한다 — [34번 주제](../34-exceptions-nothing-and-try-expression/) (3)(4).
- ★ 셈 — **막힌 탐침 3 / 9**(계약을 opt-in 없이 쓴 칸 · `assert` · 계약 없는 직접 함수).

### (4) ★★ 메시지 람다는 실패할 때만 — 그리고 객체가 안 생긴다

```kotlin
// lazy51.kt
var built = 0

fun expensive(x: Int): String {
    built++
    return "bad value $x"
}

fun requireEager(ok: Boolean, message: String) {
    if (!ok) throw IllegalArgumentException(message)
}

fun viaRequire(x: Int) = require(x > 0) { expensive(x) }

fun viaEager(x: Int) = requireEager(x > 0, expensive(x))

fun main() {
    val inputs = listOf(1, 2, 3, -1)
    for (x in inputs) runCatching { viaRequire(x) }
    println("require { }      messages built: $built for ${inputs.size} calls")
    built = 0
    for (x in inputs) runCatching { viaEager(x) }
    println("requireEager(..) messages built: $built for ${inputs.size} calls")
    println(runCatching { viaRequire(-7) }.exceptionOrNull())
}
```

```text
===== kotlinc lazy51.kt -d o51l =====
(exit 0)
===== java -cp o51l:kotlin-stdlib.jar Lazy51Kt =====
require { }      messages built: 1 for 4 calls
requireEager(..) messages built: 4 for 4 calls
java.lang.IllegalArgumentException: bad value -7
(exit 0)
===== javap -c -p o51l/Lazy51Kt.class | grep -E 'public static final|IllegalArgumentException."<init>"|Method expensive|Function0' =====
  public static final int getBuilt();
  public static final void setBuilt(int);
  public static final java.lang.String expensive(int);
  public static final void requireEager(boolean, java.lang.String);
      15: invokespecial #51                 // Method java/lang/IllegalArgumentException."<init>":(Ljava/lang/String;)V
  public static final void viaRequire(int);
      15: invokestatic  #57                 // Method expensive:(I)Ljava/lang/String;
      27: invokespecial #51                 // Method java/lang/IllegalArgumentException."<init>":(Ljava/lang/String;)V
  public static final void viaEager(int);
      10: invokestatic  #57                 // Method expensive:(I)Ljava/lang/String;
  public static final void main();
(exit 0)
```

- ★★★ **`require(x > 0) { expensive(x) }` 는 네 번 불러 한 번만 메시지를 만들었다** — 통과한 세 번은 람다를 안 부른다. 같은 검사를 **문자열 인자로 받는 함수**(`requireEager`)로 하면 **네 번 다** 만든다.
- ★★ **람다가 객체로 안 생긴다** — `viaRequire` 의 바이트코드에 **`expensive` 호출과 `IllegalArgumentException` 생성이 직접** 들어 있고, 필터에 넣은 `Function0` 은 **한 줄도 안 걸렸다.** `require` 가 `inline` 이라 람다 몸통이 펼쳐졌다.
- ★ 이것은 **메시지를 몇 번 만들었나**의 계수다 — 시간은 재지 않았다.

### (5) ★★ stdlib 소스 — 계약과 기본 메시지

```text
===== unzip -o -q kotlin-stdlib-sources.jar 'commonMain/kotlin/time/*' 'jvmMain/kotlin/time/*' 'jvmMain/jdk8/kotlin/time/*' commonMain/kotlin/util/Preconditions.kt commonMain/kotlin/util/Standard.kt jvmMain/kotlin/util/AssertionsJVM.kt commonMain/kotlin/contracts/ContractBuilder.kt commonMain/kotlin/coroutines/intrinsics/Intrinsics.kt jvmMain/kotlin/coroutines/cancellation/CancellationException.kt =====
(exit 0)
===== unzip -o -q kotlinx-coroutines-core-jvm-1.11.0-sources.jar commonMain/CoroutineScope.kt commonMain/Supervisor.kt commonMain/Guidance.kt commonMain/CoroutineExceptionHandler.kt commonMain/Yield.kt commonMain/NonCancellable.kt -d kxs =====
(exit 0)
```

```text
===== sed -n '13,39p' commonMain/kotlin/util/Preconditions.kt =====
/**
 * Throws an [IllegalArgumentException] if the [value] is false.
 *
 * @sample samples.misc.Preconditions.failRequireWithoutLazyMessage
 */
@kotlin.internal.InlineOnly
public inline fun require(value: Boolean): Unit {
    contract {
        returns() implies value
    }
    require(value) { "Failed requirement." }
}

/**
 * Throws an [IllegalArgumentException] with the result of calling [lazyMessage] if the [value] is false.
 *
 * @sample samples.misc.Preconditions.failRequireWithLazyMessage
 */
@kotlin.internal.InlineOnly
public inline fun require(value: Boolean, lazyMessage: () -> Any): Unit {
    contract {
        returns() implies value
    }
    if (!value) {
        val message = lazyMessage()
        throw IllegalArgumentException(message.toString())
    }
(exit 0)
===== sed -n '42,52p' commonMain/kotlin/util/Preconditions.kt =====
/**
 * Throws an [IllegalArgumentException] if the [value] is null. Otherwise returns the not null value.
 */
@kotlin.internal.InlineOnly
@IgnorableReturnValue
public inline fun <T : Any> requireNotNull(value: T?): T {
    contract {
        returns() implies (value != null)
    }
    return requireNotNull(value) { "Required value was null." }
}
(exit 0)
===== sed -n '81,88p;149p' commonMain/kotlin/util/Preconditions.kt =====
public inline fun check(value: Boolean): Unit {
    contract {
        returns() implies value
    }
    if (!value) {
        throw IllegalStateException("Check failed.")
    }
}
public inline fun error(message: Any): Nothing = throw IllegalStateException(message.toString())
(exit 0)
===== sed -n '15p;22p;30p' commonMain/kotlin/util/Standard.kt =====
public class NotImplementedError(message: String = "An operation is not implemented.") : Error(message)
public inline fun TODO(): Nothing = throw NotImplementedError()
public inline fun TODO(reason: String): Nothing = throw NotImplementedError("An operation is not implemented: $reason")
(exit 0)
===== sed -n '26,38p' jvmMain/kotlin/util/AssertionsJVM.kt =====
/**
 * Throws an [AssertionError] calculated by [lazyMessage] if the [value] is false
 * and runtime assertions have been enabled on the JVM using the *-ea* JVM option.
 */
@kotlin.internal.InlineOnly
public inline fun assert(value: Boolean, lazyMessage: () -> Any) {
    if (_Assertions.ENABLED) {
        if (!value) {
            val message = lazyMessage()
            throw AssertionError(message)
        }
    }
}
(exit 0)
===== sed -n '19,23p;34,37p' commonMain/kotlin/contracts/ContractBuilder.kt =====
@Retention(AnnotationRetention.BINARY)
@SinceKotlin("1.3")
@RequiresOptIn
@MustBeDocumented
public annotation class ExperimentalContracts
@SinceKotlin("2.2")
@RequiresOptIn
@MustBeDocumented
public annotation class ExperimentalExtendedContracts
(exit 0)
```

- ★★★ **KDoc 이 예외 클래스를 적는다** — `require` 「`Throws an [IllegalArgumentException] if the [value] is false.`」, `check` 와 `error` 는 구현이 `IllegalStateException` 이다. **클래스는 계약이다.**
- ★★★ **계약 블록** — `contract { returns() implies value }` · `requireNotNull` 은 `returns() implies (value != null)` 이고 **널이 벗겨진 값(`T`)을 돌려준다**(KDoc 「`Otherwise returns the not null value.`」). (3)의 스마트 캐스트가 이 한 줄이다.
- ★★ **`require(value)` 는 `require(value) { "Failed requirement." }` 로 넘긴다** — 기본 메시지는 **stdlib 의 상수**다.
- ★★ **`NotImplementedError(…) : Error(message)`** · `TODO()` 는 `inline fun TODO(): Nothing` — [34번 주제](../34-exceptions-nothing-and-try-expression/) (3)이 이것을 `new NotImplementedError … athrow` 로 봤다.
- ★★ **`assert` 는 `_Assertions.ENABLED` 를 본다** — KDoc 「`runtime assertions have been enabled on the JVM using the *-ea* JVM option`」. 값(`value`)은 **인자라 먼저 계산된다** — (2)의 `legacy` 칸이 그것이다.
- ★ `ExperimentalContracts` 는 `@RequiresOptIn` — (3)의 진단이 요구한 그 표지다. 같은 파일에 **`ExperimentalExtendedContracts`**(`@SinceKotlin("2.2")` + `@RequiresOptIn`)가 하나 더 있다.

## 문법 — 형태와 규칙

**형태** — 생성자의 인자 검사는 `require`, 메서드의 상태 검사는 `check`, 도달하면 안 되는 가지는 `error`.

```kotlin
// form51.kt
class Account(val id: String, initial: Long) {
    var balance: Long = initial
        private set
    private var closed = false

    init {
        require(id.isNotBlank()) { "id must not be blank" }
        require(initial >= 0) { "initial must be >= 0, was $initial" }
    }

    fun withdraw(amount: Long) {
        require(amount > 0) { "amount must be > 0, was $amount" }
        check(!closed) { "account $id is closed" }
        check(balance >= amount) { "insufficient balance: $balance < $amount" }
        balance -= amount
    }

    fun close() {
        closed = true
    }
}

fun fee(kind: String): Int = when (kind) {
    "basic" -> 0
    "premium" -> 5
    else -> error("unknown kind: $kind")
}

fun show(label: String, block: () -> Any?) {
    val text = runCatching(block).fold({ "ok $it" }, { "${it::class.simpleName}: ${it.message}" })
    println("$label -> $text")
}

fun main() {
    val acc = Account("a1", 100)
    show("new Account(\" \", 1)") { Account(" ", 1) }
    show("new Account(\"a2\", -5)") { Account("a2", -5) }
    show("withdraw(30)") { acc.withdraw(30); acc.balance }
    show("withdraw(0)") { acc.withdraw(0) }
    show("withdraw(500)") { acc.withdraw(500) }
    acc.close()
    show("withdraw(10) after close") { acc.withdraw(10) }
    show("fee(\"premium\")") { fee("premium") }
    show("fee(\"gold\")") { fee("gold") }
}
```

```text
===== kotlinc form51.kt -d o51f =====
(exit 0)
===== java -cp o51f:kotlin-stdlib.jar Form51Kt =====
new Account(" ", 1) -> IllegalArgumentException: id must not be blank
new Account("a2", -5) -> IllegalArgumentException: initial must be >= 0, was -5
withdraw(30) -> ok 70
withdraw(0) -> IllegalArgumentException: amount must be > 0, was 0
withdraw(500) -> IllegalStateException: insufficient balance: 70 < 500
withdraw(10) after close -> IllegalStateException: account a1 is closed
fee("premium") -> ok 5
fee("gold") -> IllegalStateException: unknown kind: gold
(exit 0)
```

**규칙 불릿**

- **인자가 틀렸다** → `require(cond) { "…" }` · `requireNotNull(x) { "…" }` — `IllegalArgumentException`((1)).
- **지금 상태가 안 된다** → `check(cond) { "…" }` · `checkNotNull(x) { "…" }` — `IllegalStateException`((1)).
- **있을 수 없는 가지** → `error("…")` — `IllegalStateException` · 반환 타입 `Nothing`((1) · [34번](../34-exceptions-nothing-and-try-expression/)).
- **아직 안 만들었다** → `TODO()` / `TODO("이유")` — `NotImplementedError`(**`Error`**)((1)).
- **개발 중 확인** → `assert(cond)` — 기본은 `-ea` 가 있어야 던지고, **조건은 늘 평가된다**(`-Xassertions=jvm` 이 아니면)((2)).
- **메시지는 람다로** — 실패할 때만 만든다((4)).
- **직접 만든 검증 함수가 스마트 캐스트를 주려면** `@OptIn(ExperimentalContracts::class)` + `contract { returns() implies … }`((3)).

## 어디서 틀리나

1. ★★★ **`require` 와 `check` 를 섞어 쓴다.** 로그의 예외 클래스가 **누구의 잘못인지**를 잘못 말하게 된다 — 인자는 `require`, 상태는 `check`((1)).
2. ★★★ **`assert` 를 운영 검사로 쓴다.** `-ea` 없이는 **안 던진다** — 그런데 기본 모드에서는 **조건식의 부수 효과는 난다**((2)).
3. ★★ **직접 만든 검증 함수 뒤에서 스마트 캐스트를 기대한다.** 계약이 없으면 안 된다 — 달려면 opt-in 이 필요하다(2.4.20)((3)).
4. ★★ **`requireNotNull` 과 `checkNotNull` 의 메시지로 둘을 가른다.** 둘 다 `Required value was null.` — **클래스로만** 갈린다((1)).
5. ★★ **`catch (e: Exception)` 으로 `TODO()` 를 잡는다고 본다.** `Error` 라 빠져나간다([49번](../49-result-and-runcatching/) (4)).
6. ★ **메시지를 문자열로 미리 만들어 넘긴다.** 통과할 때도 만든다 — 람다로 넘겨라((4)).

## 구현 세부사항 대 언어 보장

| 항목 | 어느 쪽인가 | 근거 |
|---|---|---|
| `require` → `IllegalArgumentException` · `check`·`error` → `IllegalStateException` | ★★★ **API 계약(KDoc · 선언)** | (1)(5) |
| 기본 메시지 문자열 | ★ **stdlib 구현의 상수** — KDoc 은 클래스만 약속한다 | (1)(5) |
| `TODO()` 가 `Error` | ★★ **API 계약(선언)** — `NotImplementedError : Error` | (5) |
| `assert` 가 `-ea` 에 따른다 | ★★ **API 계약(KDoc)** · 조건 평가 여부는 **컴파일러 모드**(`-Xassertions`) | (2)(5) |
| 계약이 있으면 스마트 캐스트 | ★★★ **언어 기능 — 실험적**(`@RequiresOptIn`) | (3) |
| 메시지 람다가 실패할 때만 불린다 | ★★ **선언**(`if (!value) { val message = lazyMessage() … }`) | (4)(5) |
| 람다가 객체로 안 생긴다 | ★ **`inline` 의 결과** — 이 판의 바이트코드 관찰 | (4) |
| `Nothing` · `?:` 뒤 `error()` | **인용** | [34번 주제](../34-exceptions-nothing-and-try-expression/) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 공개 함수·생성자의 인자 검사 | `require` · `requireNotNull` | (1) — `IllegalArgumentException` |
| 객체가 그 동작을 할 수 있는 상태인가 | `check` · `checkNotNull` | (1) — `IllegalStateException` |
| `when` 의 나머지·불가능한 가지 | `error("…")` | (1) · `Nothing` |
| 아직 안 만든 몸통 | `TODO("이유")` — **몸통 전체**에 | [34번 주제](../34-exceptions-nothing-and-try-expression/) (8) |
| 개발 중에만 켜는 불변식 | `assert` — 조건에 부수 효과를 넣지 마라 | (2) |
| 검증 헬퍼를 여러 곳에서 쓴다 | 계약을 단 `inline` 함수 — 또는 **그냥 `require` 를 부른다** | (3) — 계약은 opt-in 이 든다 |
| 결과를 값으로 모아야 한다 | `runCatching` 과 함께 | [49번 주제](../49-result-and-runcatching/) |

## 핵심 문장

1. **`require` 는 `IllegalArgumentException`(인자), `check`·`error` 는 `IllegalStateException`(상태)** — 클래스가 곧 누구의 잘못인지다.
2. 기본 메시지는 `Failed requirement.` · `Check failed.` · `Required value was null.`(두 `NotNull` 이 같다) · `An operation is not implemented.` 이다.
3. **`assert` 는 `-ea` 가 없으면 안 던진다** — 그런데 기본 모드에서는 **조건을 평가한다**(`-Xassertions=jvm` 이면 안 한다).
4. **`require(x != null)` 뒤의 스마트 캐스트는 계약 덕분**이다 — 직접 만든 함수는 계약이 없으면 안 되고, 계약은 **2.4.20 에서도 opt-in** 이다.
5. **메시지 람다는 실패할 때만** 불리고 `inline` 이라 **객체도 안 생긴다.**

## 관련 자료

- [34번 주제](../34-exceptions-nothing-and-try-expression/) — ★★★ **선행.** `Nothing` 타입 · `TODO()` 가 `athrow` 로 펼쳐지는 것 · `?:` 뒤 `error()`. 그쪽은 **돌아오지 않는 식의 타입**, 여기는 **어느 예외를 던지나**.
- [49번 주제](../49-result-and-runcatching/) — `TODO()`·`AssertionError` 가 `catch (e: Exception)` 을 빠져나가고 `runCatching` 에는 잡힌다(5 중 2).
- [`../../언어-특성/README.md`](../../언어-특성/README.md) §8 — 검사 예외 폐지가 무엇을 규율로 떠넘겼나. 논지는 거기다 — `require`/`check` 는 그 규율의 도구다.
- [53번 주제](../53-structured-concurrency-job-cancellation-exceptions/) — 코루틴 안에서 `check` 가 던진 예외가 형제·부모로 어떻게 번지나.

## 용어 풀이

> **사전 조건(precondition)** — 함수가 **일을 시작하기 전에** 참이어야 하는 조건. 인자 검사가 대표다.\
> 예: `require(amount > 0) { "amount must be > 0, was $amount" }`.

> **`IllegalArgumentException` 대 `IllegalStateException`** — 앞쪽은 「**받은 값**이 틀렸다」, 뒤쪽은 「**지금 상태**에서는 그 호출이 안 된다」.

> **`NotImplementedError`** — `TODO()` 가 던지는 Kotlin stdlib 의 `Error`.

> **계약(contract)** — 함수가 컴파일러에게 「내가 정상으로 돌아오면 이 조건이 참이다」 같은 사실을 알려 주는 선언. `contract { returns() implies (x != null) }`.

> **스마트 캐스트(smart cast)** — 검사한 뒤 컴파일러가 변수의 타입을 **좁혀 주는 것**. `String?` → `String`.

> **opt-in** — 실험적 API 를 쓰겠다고 **명시**하는 것. `@OptIn(X::class)` 또는 `-opt-in=X`.

> **`-ea`** — JVM 의 단언(assertion)을 켜는 옵션(`-enableassertions`).

## 더 들어가면

- **`callsInPlace` 계약** — `run { }`·`let { }` 이 람다를 「정확히 한 번 부른다」를 알려 `val` 초기화를 허용하는 계약. 이 판에서 돌리지 않았다.
- **`ExperimentalExtendedContracts`** — (5)의 발췌에 선언만 있다. 무엇을 여는 표지인지(어느 계약 꼴이 그 뒤에 있나)는 **돌려 보지 않았다.**
- **`-Xassertions` 가 바꾸는 바이트코드** — (2)는 행동만 봤다. `javap -c` 로 `legacy` 와 `jvm` 의 차이(`$assertionsDisabled` 필드 여부)를 보면 원인이 보일 것이다 — **확인하지 않았다.**
