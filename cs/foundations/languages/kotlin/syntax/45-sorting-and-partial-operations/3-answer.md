# kotlin/syntax/45 — 정렬·부분 연산 — `sortedBy`/`take`/`drop`/`chunked`/`windowed` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `java` 에서 실제로 얻었다.
> ★★ 아래 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적은 자리가 없다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 동사 원형(`sort`·`sortBy`·`sortDescending`·`reverse`·`shuffle`)은 **`Unit`**, `-ed` 꼴(`sorted`·`sortedBy`·`reversed`·`shuffled`)은 **`List<Int>`** · 없는 칸은 **`List` 의 동사 원형 다섯**과 **`Array.shuffled`** — 27칸 중 6칸

**출력**

```kotlin
// sig45.kt
import kotlin.random.Random

fun t(x: Nothing?) {}

fun main() {
    val ml: MutableList<Int> = mutableListOf(3, 1, 2)
    val ro: List<Int> = listOf(3, 1, 2)
    val ar: Array<Int> = arrayOf(3, 1, 2)

    t(ml.sort())                    // sort MutableList
    t(ro.sort())                    // sort List
    t(ar.sort())                    // sort Array
    t(ml.sorted())                  // sorted MutableList
    t(ro.sorted())                  // sorted List
    t(ar.sorted())                  // sorted Array
    t(ml.sortBy { it })             // sortBy MutableList
    t(ro.sortBy { it })             // sortBy List
    t(ar.sortBy { it })             // sortBy Array
    t(ml.sortedBy { it })           // sortedBy MutableList
    t(ro.sortedBy { it })           // sortedBy List
    t(ar.sortedBy { it })           // sortedBy Array
    t(ml.sortDescending())          // sortDescending MutableList
    t(ro.sortDescending())          // sortDescending List
    t(ar.sortDescending())          // sortDescending Array
    t(ml.reverse())                 // reverse MutableList
    t(ro.reverse())                 // reverse List
    t(ar.reverse())                 // reverse Array
    t(ml.reversed())                // reversed MutableList
    t(ro.reversed())                // reversed List
    t(ar.reversed())                // reversed Array
    t(ml.shuffle(Random(7)))        // shuffle MutableList
    t(ro.shuffle(Random(7)))        // shuffle List
    t(ar.shuffle(Random(7)))        // shuffle Array
    t(ml.shuffled(Random(7)))       // shuffled MutableList
    t(ro.shuffled(Random(7)))       // shuffled List
    t(ar.shuffled(Random(7)))       // shuffled Array
}
```

```text
===== kotlinc sig45.kt -d o45raw | grep -A2 'unresolved reference' =====
sig45.kt:11:10: error: unresolved reference 'sort' on receiver of type 'List<Int>'.
    t(ro.sort())                    // sort List
         ^^^^
--
sig45.kt:17:10: error: unresolved reference 'sortBy' on receiver of type 'List<Int>'.
    t(ro.sortBy { it })             // sortBy List
         ^^^^^^
sig45.kt:17:19: error: unresolved reference 'it'.
    t(ro.sortBy { it })             // sortBy List
                  ^^
--
sig45.kt:23:10: error: unresolved reference 'sortDescending' on receiver of type 'List<Int>'.
    t(ro.sortDescending())          // sortDescending List
         ^^^^^^^^^^^^^^
--
sig45.kt:26:10: error: unresolved reference 'reverse' on receiver of type 'List<Int>'.
    t(ro.reverse())                 // reverse List
         ^^^^^^^
--
sig45.kt:32:10: error: unresolved reference 'shuffle' on receiver of type 'List<Int>'.
    t(ro.shuffle(Random(7)))        // shuffle List
         ^^^^^^^
--
sig45.kt:36:10: error: unresolved reference 'shuffled' on receiver of type 'Array<Int>'.
    t(ar.shuffled(Random(7)))       // shuffled Array
         ^^^^^^^^
(exit 1)
```

**왜 그런가**

- ★★★ 제자리 연산은 돌려줄 것이 없어 **`Unit`** 이고, 새 리스트 연산은 **`List<Int>`** 다 — `Array` 에서도 `sorted()` 는 `Array` 가 아니라 **`List<Int>`** 다.
- ★★ `List`(읽기 전용)에는 **고치는 확장이 없다** — `sort`·`sortBy`·`sortDescending`·`reverse`·`shuffle` 이 `unresolved reference … on receiver of type 'List<Int>'` 다([40번 주제](../40-read-only-collections-and-runtime-types/) (2)와 같은 이유).
- ★ `Array.shuffled` 는 이름 규칙과 무관하게 **stdlib 에 없는** 칸이다.

### 2. ★★★ **제자리 10 / 21** — 원본이 바뀐 10칸이 정확히 1번의 **`Unit`** 칸이다 · `List<Int>` 칸 11개는 원본이 `[3, 1, 2]` 그대로

**출력**

```kotlin
// run45.kt
import kotlin.random.Random

fun onList(op: String, f: (MutableList<Int>) -> Any?) {
    val src = mutableListOf(3, 1, 2)
    val r = f(src)
    println(listOf(op, "MutableList", src.toString(), r.toString()).joinToString("\t"))
}

fun onReadOnly(op: String, f: (List<Int>) -> Any?) {
    val src: List<Int> = listOf(3, 1, 2)
    val r = f(src)
    println(listOf(op, "List", src.toString(), r.toString()).joinToString("\t"))
}

fun onArray(op: String, f: (Array<Int>) -> Any?) {
    val src = arrayOf(3, 1, 2)
    val r = f(src)
    println(listOf(op, "Array", src.contentToString(), r.toString()).joinToString("\t"))
}

fun main() {
    onList("sort") { it.sort() }
    onArray("sort") { it.sort() }
    onList("sorted") { it.sorted() }
    onReadOnly("sorted") { it.sorted() }
    onArray("sorted") { it.sorted() }
    onList("sortBy") { it.sortBy { x -> x } }
    onArray("sortBy") { it.sortBy { x -> x } }
    onList("sortedBy") { it.sortedBy { x -> x } }
    onReadOnly("sortedBy") { it.sortedBy { x -> x } }
    onArray("sortedBy") { it.sortedBy { x -> x } }
    onList("sortDescending") { it.sortDescending() }
    onArray("sortDescending") { it.sortDescending() }
    onList("reverse") { it.reverse() }
    onArray("reverse") { it.reverse() }
    onList("reversed") { it.reversed() }
    onReadOnly("reversed") { it.reversed() }
    onArray("reversed") { it.reversed() }
    onList("shuffle") { it.shuffle(Random(7)) }
    onArray("shuffle") { it.shuffle(Random(7)) }
    onList("shuffled") { it.shuffled(Random(7)) }
    onReadOnly("shuffled") { it.shuffled(Random(7)) }
}
```

```python
# grid45.py
import re
import subprocess
import sys

d = sys.argv[1]
SRC = "sig45.kt"
RECV = ["MutableList", "List", "Array"]

cells = {}
order = []
for n, line in enumerate(open(SRC, encoding="utf-8"), 1):
    m = re.search(r"// (\S+) (\S+)$", line.rstrip("\n"))
    if m:
        cells[n] = m.groups()
        if m.group(1) not in order:
            order.append(m.group(1))

comp = subprocess.run(["kotlinc", SRC, "-d", "o45g"], capture_output=True, text=True)
if comp.returncode != 1:
    raise SystemExit("expected exit 1, got %d" % comp.returncode)
first = {}
for line in (comp.stdout + comp.stderr).splitlines():
    m = re.match(r"sig45\.kt:(\d+):\d+: error: (.*)$", line)
    if m and int(m.group(1)) not in first:
        first[int(m.group(1))] = m.group(2)
rtype = {}
for n, key in cells.items():
    msg = first[n]
    m = re.match(r"argument type mismatch: actual type is '(.*)', but 'Nothing\?' was expected\.$", msg)
    if m:
        rtype[key] = m.group(1)
    elif msg.startswith("unresolved reference '"):
        rtype[key] = None
    else:
        raise SystemExit("unexpected diagnostic on line %d: %s" % (n, msg))

out = subprocess.run(["java", "-cp", d + ":kotlin-stdlib.jar", "Run45Kt"],
                     capture_output=True, text=True, check=True).stdout
after = {}
for line in out.splitlines():
    c = line.split("\t")
    if len(c) != 4:
        raise SystemExit("cell count mismatch: " + line)
    after[(c[0], c[1])] = (c[2], c[3])

print("source before every call: [3, 1, 2]")
print("\t".join(["op", "receiver", "compiles", "return type", "source after", "returned", "in place?"]))
inplace = compiled = 0
for op in order:
    for r in RECV:
        t = rtype[(op, r)]
        if t is None:
            if (op, r) in after:
                raise SystemExit("ran a cell that does not compile: %s %s" % (op, r))
            print("\t".join([op, r, "no", "-", "-", "-", "-"]))
            continue
        compiled += 1
        src_after, returned = after[(op, r)]
        moved = src_after != "[3, 1, 2]"
        inplace += moved
        print("\t".join([op, r, "yes", t, src_after, returned, "yes" if moved else "no"]))
print("in-place cells: %d / %d compiled (of %d)" % (inplace, compiled, len(cells)))
```

```text
===== kotlinc run45.kt -d o45r =====
(exit 0)
```

```text
===== python3 grid45.py o45r =====
source before every call: [3, 1, 2]
op	receiver	compiles	return type	source after	returned	in place?
sort	MutableList	yes	Unit	[1, 2, 3]	kotlin.Unit	yes
sort	List	no	-	-	-	-
sort	Array	yes	Unit	[1, 2, 3]	kotlin.Unit	yes
sorted	MutableList	yes	List<Int>	[3, 1, 2]	[1, 2, 3]	no
sorted	List	yes	List<Int>	[3, 1, 2]	[1, 2, 3]	no
sorted	Array	yes	List<Int>	[3, 1, 2]	[1, 2, 3]	no
sortBy	MutableList	yes	Unit	[1, 2, 3]	kotlin.Unit	yes
sortBy	List	no	-	-	-	-
sortBy	Array	yes	Unit	[1, 2, 3]	kotlin.Unit	yes
sortedBy	MutableList	yes	List<Int>	[3, 1, 2]	[1, 2, 3]	no
sortedBy	List	yes	List<Int>	[3, 1, 2]	[1, 2, 3]	no
sortedBy	Array	yes	List<Int>	[3, 1, 2]	[1, 2, 3]	no
sortDescending	MutableList	yes	Unit	[3, 2, 1]	kotlin.Unit	yes
sortDescending	List	no	-	-	-	-
sortDescending	Array	yes	Unit	[3, 2, 1]	kotlin.Unit	yes
reverse	MutableList	yes	Unit	[2, 1, 3]	kotlin.Unit	yes
reverse	List	no	-	-	-	-
reverse	Array	yes	Unit	[2, 1, 3]	kotlin.Unit	yes
reversed	MutableList	yes	List<Int>	[3, 1, 2]	[2, 1, 3]	no
reversed	List	yes	List<Int>	[3, 1, 2]	[2, 1, 3]	no
reversed	Array	yes	List<Int>	[3, 1, 2]	[2, 1, 3]	no
shuffle	MutableList	yes	Unit	[1, 3, 2]	kotlin.Unit	yes
shuffle	List	no	-	-	-	-
shuffle	Array	yes	Unit	[1, 3, 2]	kotlin.Unit	yes
shuffled	MutableList	yes	List<Int>	[3, 1, 2]	[1, 3, 2]	no
shuffled	List	yes	List<Int>	[3, 1, 2]	[1, 3, 2]	no
shuffled	Array	no	-	-	-	-
in-place cells: 10 / 21 compiled (of 27)
(exit 0)
```

**왜 그런가**

- ★★★ 격자 스크립트가 1번의 서명(`sig45.kt`)과 실행(`run45.kt`)을 **합쳐** 셌다 — `Unit` 이면 「in place? yes」, `List<Int>` 면 「no」. **어긋난 칸이 없다.**
- ★★ `shuffle(Random(7))` 은 원본을 `[1, 3, 2]` 로, `shuffled(Random(7))` 은 원본을 둔 채 `[1, 3, 2]` 를 돌려줬다 — 씨앗이 같으니 **같은 순열**이다.
- ★ 제자리 칸이 돌려준 것은 `kotlin.Unit` 이다 — 결과를 변수에 담아도 **정렬된 리스트가 아니다.**

### 3. ★★ `1 bcead` · `2 adbce` · `3 daecb` · `4 bcead` · `5 java.util.Arrays$ArrayList` — **`2` 와 `3` 은 다르다**

**출력**

```kotlin
// stable45.kt
fun main() {
    val rows = listOf("b" to 1, "a" to 2, "c" to 1, "d" to 2, "e" to 1)
    fun names(xs: List<Pair<String, Int>>) = xs.joinToString("") { it.first }
    println("input                         ${names(rows)}")
    println("1 sortedBy { second }         ${names(rows.sortedBy { it.second })}")
    println("2 sortedByDescending { second } ${names(rows.sortedByDescending { it.second })}")
    println("3 sortedBy { second }.reversed() ${names(rows.sortedBy { it.second }.reversed())}")
    val m = rows.toMutableList()
    m.sortBy { it.second }
    println("4 sortBy { second }            ${names(m)}")
    val s = listOf(3, 1, 2).sorted()
    println("5 sorted() class               ${s::class.java.name}")
}
```

```text
===== kotlinc stable45.kt -d o45s =====
(exit 0)
===== java -cp o45s:kotlin-stdlib.jar Stable45Kt =====
input                         bacde
1 sortedBy { second }         bcead
2 sortedByDescending { second } adbce
3 sortedBy { second }.reversed() daecb
4 sortBy { second }            bcead
5 sorted() class               java.util.Arrays$ArrayList
(exit 0)
```

**왜 그런가**

- ★★★ `sortedBy` 는 **안정**이다 — 키 `1` 인 `b`·`c`·`e` 가 입력 순서대로 남는다(`bce`), 키 `2` 인 `a`·`d` 도(`ad`).
- ★★★ `sortedByDescending`(`2`)도 안정이라 **같은 키 안에서는 입력 순서**(`ad` · `bce`)다. `sortedBy{}.reversed()`(`3`)는 리스트를 통째로 뒤집어 **같은 키 안의 순서까지 반대**(`da` · `ecb`)다.
- ★★ 제자리 `sortBy`(`4`)도 같은 안정 정렬이다.
- ★ `sorted()` 의 결과는 `Arrays$ArrayList` — 소스가 배열에 정렬한 뒤 `asList()` 로 감싼다(2-summary (2)).

### 4. ★★★ `4 take(-1)` · `6 drop(-1)` 은 **`IllegalArgumentException: Requested element count -1 is less than zero.`** · `12 windowed(3)` 은 **창 5개**(끝의 `[6, 7]`·`[7]` 없음) · `13` 은 **7개** · `15 windowed(3, step = 3)` 은 `[7]` 을 **버리고** · `16` 은 남긴다 · `18 windowed(0)` 은 **`Both size 0 and step 1 must be greater than zero.`** · `20 chunked(0)` 은 **`size 0 must be greater than zero.`**

**출력**

```kotlin
// part45.kt
fun probe(label: String, f: () -> Any?) {
    val r = try {
        "= " + f()
    } catch (e: Exception) {
        "! " + e::class.java.simpleName + ": " + e.message
    }
    println("$label  $r")
}

fun main() {
    val xs = (1..7).toList()
    println("xs = $xs")
    probe("1  take(3)          ") { xs.take(3) }
    probe("2  take(100)        ") { xs.take(100) }
    probe("3  take(0)          ") { xs.take(0) }
    probe("4  take(-1)         ") { xs.take(-1) }
    probe("5  drop(100)        ") { xs.drop(100) }
    probe("6  drop(-1)         ") { xs.drop(-1) }
    probe("7  takeLast(2)      ") { xs.takeLast(2) }
    probe("8  takeWhile { <3 } ") { xs.takeWhile { it < 3 } }
    probe("9  takeWhile { >3 } ") { xs.takeWhile { it > 3 } }
    probe("10 dropWhile { <3 } ") { xs.dropWhile { it < 3 } }
    probe("11 chunked(3)       ") { xs.chunked(3) }
    probe("12 windowed(3)      ") { xs.windowed(3) }
    probe("13 windowed(3, partialWindows = true)") { xs.windowed(3, partialWindows = true) }
    probe("14 windowed(3, step = 2)") { xs.windowed(3, step = 2) }
    probe("15 windowed(3, step = 3)") { xs.windowed(3, step = 3) }
    probe("16 windowed(3, 3, true) ") { xs.windowed(3, 3, true) }
    probe("17 windowed(10)     ") { xs.windowed(10) }
    probe("18 windowed(0)      ") { xs.windowed(0) }
    probe("19 windowed(3, step = 0)") { xs.windowed(3, step = 0) }
    probe("20 chunked(0)       ") { xs.chunked(0) }
    probe("21 zipWithNext()    ") { xs.zipWithNext() }
}
```

```text
===== kotlinc part45.kt -d o45p =====
(exit 0)
===== java -cp o45p:kotlin-stdlib.jar Part45Kt =====
xs = [1, 2, 3, 4, 5, 6, 7]
1  take(3)            = [1, 2, 3]
2  take(100)          = [1, 2, 3, 4, 5, 6, 7]
3  take(0)            = []
4  take(-1)           ! IllegalArgumentException: Requested element count -1 is less than zero.
5  drop(100)          = []
6  drop(-1)           ! IllegalArgumentException: Requested element count -1 is less than zero.
7  takeLast(2)        = [6, 7]
8  takeWhile { <3 }   = [1, 2]
9  takeWhile { >3 }   = []
10 dropWhile { <3 }   = [3, 4, 5, 6, 7]
11 chunked(3)         = [[1, 2, 3], [4, 5, 6], [7]]
12 windowed(3)        = [[1, 2, 3], [2, 3, 4], [3, 4, 5], [4, 5, 6], [5, 6, 7]]
13 windowed(3, partialWindows = true)  = [[1, 2, 3], [2, 3, 4], [3, 4, 5], [4, 5, 6], [5, 6, 7], [6, 7], [7]]
14 windowed(3, step = 2)  = [[1, 2, 3], [3, 4, 5], [5, 6, 7]]
15 windowed(3, step = 3)  = [[1, 2, 3], [4, 5, 6]]
16 windowed(3, 3, true)   = [[1, 2, 3], [4, 5, 6], [7]]
17 windowed(10)       = []
18 windowed(0)        ! IllegalArgumentException: Both size 0 and step 1 must be greater than zero.
19 windowed(3, step = 0)  ! IllegalArgumentException: Both size 3 and step 0 must be greater than zero.
20 chunked(0)         ! IllegalArgumentException: size 0 must be greater than zero.
21 zipWithNext()      = [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7)]
(exit 0)
```

**왜 그런가**

- ★★★ `take`·`drop` 은 **음수만** 던진다 — `take(100)` 은 7개 전부, `drop(100)` 은 `[]`, `take(0)` 은 `[]`.
- ★★★ `windowed` 는 기본(`partialWindows = false`)이 **끝의 모자란 창을 버리는** 것이고, `chunked(n)` 은 소스가 `windowed(n, n, partialWindows = true)` 라 **남긴다**(8번).
- ★★ `windowed(0)`·`windowed(3, step = 0)`·`chunked(0)` 은 **같은 검사 함수**(`checkWindowSizeStep`)에서 던진다 — `size != step` 이면 「`Both size … and step …`」, 같으면 「`size …`」 문장이다.
- ★ `takeWhile { >3 }` 은 `[]` — 첫 원소 `1` 에서 멈춘다. `windowed(10)` 은 `[]` — 던지지 않는다.

### 5. **`ordered  [call, lunch, mail, docs]`** · **`work     [mail, docs, call, lunch]`** · **`tasks    [mail, call, docs, lunch]`**(원래 순서 그대로)

**출력**

```kotlin
// form45.kt
data class Task(val name: String, val priority: Int)

fun main() {
    val tasks = listOf(Task("mail", 2), Task("call", 1), Task("docs", 2), Task("lunch", 1))
    val ordered = tasks.sortedBy { it.priority }
    val work = tasks.toMutableList()
    work.sortByDescending { it.priority }
    println("ordered  ${ordered.map { it.name }}")
    println("work     ${work.map { it.name }}")
    println("tasks    ${tasks.map { it.name }}")
    println("top2     ${ordered.take(2).map { it.name }}")
    println("pages    ${tasks.chunked(3).map { page -> page.map { it.name } }}")
    println("pairs    ${tasks.windowed(2).map { (a, b) -> a.priority - b.priority }}")
}
```

```text
===== kotlinc form45.kt -d o45z =====
(exit 0)
===== java -cp o45z:kotlin-stdlib.jar Form45Kt =====
ordered  [call, lunch, mail, docs]
work     [mail, docs, call, lunch]
tasks    [mail, call, docs, lunch]
top2     [call, lunch]
pages    [[mail, call, docs], [lunch]]
pairs    [1, -1, 1]
(exit 0)
```

**왜 그런가**

- ★★ `ordered` 는 우선순위 `1`(`call`·`lunch`) → `2`(`mail`·`docs`), 같은 우선순위 안에서는 **입력 순서**다(안정).
- ★★ `work` 는 사본(`toMutableList()`)을 **제자리** `sortByDescending` 했다 — `2` 가 먼저, 같은 키 안은 입력 순서(`mail`·`docs` · `call`·`lunch`).
- ★ `tasks` 는 **어느 쪽에서도 안 바뀌었다** — `sortedBy` 는 새 리스트, `sortByDescending` 은 사본을 고쳤다.

### 6. **반환 타입이 `Unit` 인가**로 확인한다 — 그것은 **서명**이다 · 「이름의 꼴」은 이 판 27칸에서 **예외가 없었던 관례**다

**왜 그런가**

- ★★★ 2번에서 「원본이 바뀐 칸 = `Unit` 칸」이 **10 / 10** 이었다. 제자리 연산은 돌려줄 것이 없으니 서명이 `Unit` 을 적는다.
- ★★ 이름 규칙(동사 원형 대 `-ed`)은 stdlib 의 **명명 관례**다 — 새 확장이 그것을 지킨다는 보장은 이 문서가 확인하지 않았다. 헷갈리면 **서명을 본다.**

### 7. **stdlib 가 약속한다** — `sortedBy`·`sortBy` 의 KDoc 이 「``The sort is _stable_.``」이라고 적는다

**왜 그런가**

- ★★★ 2-summary (2)의 발췌 — `sortBy` 는 1174행, `sortedBy` 는 1221행에 같은 문장이 있다(「``…elements for which [selector] returned equal values preserve their order relative to each other after sorting.``」).
- ★ 그 안정성을 **실제로 누가 주는지**(`sortWith` 아래의 JVM 정렬)는 따라가지 않았다 — 약속은 KDoc, 관찰은 3번이다.

### 8. **다르다** — `chunked(3)` 은 `[[1, 2, 3], [4, 5, 6], [7]]`, `windowed(3, step = 3)` 은 `[7]` 을 **버린다** · `chunked` 는 **`windowed(size, size, partialWindows = true)`** 한 줄이다

**왜 그런가**

- ★★ 2-summary (4)의 `grep` — `3556-    return windowed(size, size, partialWindows = true)`. 그래서 `chunked(3)` 과 **같은 답**은 `windowed(3, 3, true)`(4번의 `16`)다.
- ★ 차이는 **`partialWindows` 한 인자**다 — 기본 `false`.

### 9. **같은 것** — 「이웃 n개를 한 창으로 본다」는 모양 · **다른 것** — `windowed` 는 **창마다 새 리스트**를 만들고 끝의 부분 창 처리를 인자로 정한다 · 알고리즘은 창을 밀며 **값을 갱신**한다 · **재지 않은 것** — 그 비용 차이

**왜 그런가**

- ★★ 알고리즘 쪽은 [`cs/algorithm/09-sliding-window/`](../../../../../algorithm/09-sliding-window/)가 정본이다 — 창이 한 칸 밀릴 때 **들어온 것과 나간 것만** 반영하는 기법이다. 이 문서는 그 기법을 **다시 쓰지 않는다.**
- ★ `windowed` 가 창마다 리스트를 만든다는 것은 결과 모양(4번)에서 보일 뿐, 그것이 **시간·할당에서 얼마인지는 재지 않았다.**

### 10. **말할 수 없다** — 확인된 것은 「`sortBy` 는 **원본을 고치고** `sortedBy` 는 **새 리스트**」라는 구조뿐이다 · 싸다고 하려면 **원소 수를 바꿔 가며 시간과 할당을 반복 측정**해야 한다

**왜 그런가**

- ★★ 2-summary (2)의 `sorted()` 구현은 **배열에 복사한 뒤** 정렬한다 — 새 리스트 쪽이 복사를 한 번 더 할 것으로 **보이지만**, 제자리 `sortWith` 도 JVM 안에서 무엇을 복사하는지는 **따라가지 않았다.**
- ★ [JS 25번](../../../js/syntax/25-array-non-mutating-and-copy-methods/)도 같은 이유로 「`toSorted` 는 복사라서 느리다」를 **한 줄도 쓰지 않았다** — 거기도 시간·메모리를 재지 않았다.

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

★ **흔들리는 칸과 안 흔들리는 칸**

| 흔들린다 | 안 흔들린다 |
|---|---|
| **없다** — `shuffle`·`shuffled` 는 `Random(7)` 로 고정했다 | 격자 27행 · 제자리 칸 수 · 실행 출력(`Random(7)` 의 순열 포함 — 이 판에서) |
| | 경계 출력 · 예외 문장 · stdlib 소스 발췌 |
| | 진단의 **문구·`파일:줄:칸`·캐럿** · 모든 **종료 코드** |

> 근거 — 캡처 스크립트를 처음부터 다시 돌려 **블록 전체를 대조**했다.
>
> 실측 — `capture.sh blocks` 와 `capture.sh blocks-recheck` 를 처음부터 따로 돌려 `normalize-shaky.py` 로 대조했다 —\
> **블록 60개 · 동일 59 · 흔들린 칸 1 · ★고칠 것 0**(42\~45 네 주제를 한 캡처로 받았다). 흔들린 1블록은 44번의 Rust 패닉 블록(`a44-rs`)이고, 원문 차이는 **패닉 첫 줄의 스레드 id** 하나였다 — 기본 정규화 규칙(스레드 id)이 그것을 지웠다.\
> ★ 추가한 정규화 규칙은 **없다**.

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `sig45.kt` | ★★★ 9연산 × 3받는 쪽의 반환 타입 · 없는 칸 | 격자 스크립트 안에서 `kotlinc`(실패가 결과) · 밖에서 한 번 더 → `grep -A2 'unresolved reference'` |
| `run45.kt` · `grid45.py` | ★★★ 컴파일되는 21칸의 원본 변화 · 제자리 칸 수 | `kotlinc` → 스크립트가 `kotlinc`(`sig45.kt`)와 `java` |
| `stable45.kt` | ★★ 안정 정렬 · 내림차순 대 뒤집기 · `sorted()` 결과 클래스 | `kotlinc` → `java` |
| `_Collections.kt`(stdlib 소스 jar) | `sortBy`·`sortedBy` KDoc · `sorted()` 구현 · `chunked` · `take` · `windowed` KDoc | `unzip` → `grep`·`sed -n` |
| `SlidingWindow.kt`(stdlib 소스 jar) | `checkWindowSizeStep` 의 두 문장 | `sed -n` |
| `part45.kt` | ★★ `take`·`drop`·`takeWhile`·`chunked`·`windowed` 경계 21줄 | `kotlinc` → `java` |
| `form45.kt` | 형태 한 벌 | `kotlinc` → `java` |

**구현 의존 항목** — `sorted()` 결과의 `Arrays$ArrayList` · `chunked` 의 한 줄 위임 · 예외 **문장** 전부 · `Random(7)` 의 순열 — 이 stdlib 판의 산출물이다.\
반면 **제자리 = `Unit` · 새 리스트 = `List`**(서명) · **안정 정렬**(KDoc) · **`take` 의 음수 `IllegalArgumentException`**(KDoc) · **`partialWindows` 기본 `false`**(KDoc) 는 **API 계약**이다.

**★ 던져 봤더니 예상과 달랐던 것 — 세 건**

1. ★★ **`Array.shuffled` 가 없었다** — `Array` 는 제자리 다섯을 다 갖는데 새 리스트 쪽 `shuffled` 만 빠졌다(1번).
2. ★★ **`sorted()` 의 결과가 `Arrays$ArrayList` 였다** — 「새 리스트」가 크기 고정 리스트다(3번).
3. ★ **`windowed(0)` 과 `chunked(0)` 의 문장이 달랐다** — 같은 검사 함수가 `size != step` 으로 문장을 고른다(4번).
