# kotlin/syntax/51 — 계약 함수 — `require`/`check`/`error`/`TODO` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [34번 주제](../34-exceptions-nothing-and-try-expression/)(검사 예외 없음·`Nothing`·`try` 식)다.
> 문항 10개 중 예측형은 5개이고, 5개 모두 코드블록이 붙는다.
> 이 주제의 모든 답은 **kotlinc 2.4.20 · Temurin JDK 21.0.5** 에서 실제로 던져 받은 것이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 열한 가지 던지기 × JVM 두 벌 (예측)

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

- 각 행의 클래스와 메시지는 `java` 와 `java -ea` 에서 각각 무엇인가? 끝의 두 줄(클래스별 개수 · `N / M`)은?

### 2. ★★ `assert` 네 모드 × 두 벌 (예측)

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

- 여덟 칸은 각각 무엇을 찍나? 끝의 두 줄 `N / M` 은?

### 3. ★★★ 검사 뒤의 `s.length` (예측)

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

- 아홉 탐침은 각각 `ok` 인가 진단인가(진단이면 몇 개 · 첫 문구)? 마지막 줄의 `N / M` 은?

### 4. ★★ 메시지를 몇 번 만드나 (예측)

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

- 세 줄의 출력은 무엇인가? `javap -c` 로 `viaRequire` 를 보면 `Function0` 이 나오나?

### 5. ★ 계좌 (예측)

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

- 여덟 줄의 출력은 무엇인가?

### 6. 인자 검사 대 상태 검사 (왜)

- `withdraw` 가 `amount > 0` 은 `require` 로, `!closed` 는 `check` 로 검사하는 까닭은 무엇인가? 로그에서 클래스만 보고 무엇을 알 수 있나?

### 7. `requireNotNull` 과 `checkNotNull` 가르기 (경계)

- 1번에서 두 함수의 메시지를 보고 둘을 가를 수 있나? 무엇으로 갈라야 하나?

### 8. 계약이 필요한 까닭 (왜)

- 3번의 `ownCheck` 와 `ownCheckC` 는 몸통이 같다. 컴파일러는 왜 한쪽에서만 `s` 를 `String` 으로 좁히나? 이 판에서 계약을 쓰는 데 무엇이 더 필요한가?

### 9. `assert` 를 운영 검사로 쓰면 (경계)

- 2번의 기본 모드(`legacy`)에서 조건식에 부수 효과(로그 쓰기·카운터 증가)가 있으면 `-ea` 없는 운영 JVM 에서 무슨 일이 일어나나? `assert` 뒤에서 스마트 캐스트가 안 되는 것(3번)과 어떻게 이어지나?

### 10. `error()` 와 `TODO()` 의 반환 타입 (연결)

- `val t = s ?: TODO()` 가 3번에서 통과한 까닭을 [34번 주제](../34-exceptions-nothing-and-try-expression/)의 어느 성질로 설명하나? `TODO()` 가 `catch (e: Exception)` 을 빠져나가는 것은 [49번 주제](../49-result-and-runcatching/)의 어느 격자에서 이미 봤나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
