# kotlin/syntax/45 — 정렬·부분 연산 — `sortedBy`/`take`/`drop`/`chunked`/`windowed` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Ordering](https://kotlinlang.org/docs/collection-ordering.html)(`sorted`·`sortedBy`·`reversed`·`shuffled`) · [List-specific operations — Sort](https://kotlinlang.org/docs/list-operations.html)(제자리 `sort`·`sortBy`·`reverse`·`shuffle`) · [Retrieve collection parts](https://kotlinlang.org/docs/collection-parts.html)(`take`·`drop`·`chunked`·`windowed`·`zipWithNext`) — 이 문서는 그 페이지들의 **목록**을 따르되, 문장은 인용하지 않고 **이 판의 stdlib 소스 jar**(`kotlin-stdlib-sources.jar` 2.4.20)의 KDoc 과 구현을 근거로 삼는다((2)(3)(4)).
> **실행 검증** — 이 문서의 모든 출력·에러는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `java` 에서 실제로 얻었다.\
> `kotlinc` 6회(컴파일 실패 2벌 — 같은 서명 탐침을 격자 스크립트 안과 밖에서, 실패가 결과다) · `java` 3회 + 격자 스크립트 안에서 1회 · stdlib 소스 jar 에서 3곳.\
> ★★ 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적지 않았다. **「제자리 칸 N / M」은 스크립트가 스스로 센 것**이다.
> **버전** — `sort`·`sorted`·`sortBy`·`sortedBy`·`reverse`·`reversed`·`take`·`drop`·`takeLast`·`takeWhile` 은 **1.0** — 이 판의 소스에서 선언 위에 `@SinceKotlin` 이 **없다**(확인만 했고 발췌하지 않았다). `chunked`·`windowed` 는 **1.2**, `shuffle(random)`·`shuffled(random)` 은 **1.3** — 소스의 `@SinceKotlin` 을 읽었고 **발췌하지 않았다**.
> **경계** — ★★★ **슬라이딩 윈도우 알고리즘은 [`cs/algorithm/09-sliding-window/`](../../../../../algorithm/09-sliding-window/) 가 정본이다** — 창을 밀며 합을 갱신하는 기법·시간 복잡도는 거기다. 여기는 **「stdlib 가 그 패턴을 이미 함수로 갖고 있다는 것과 그 경계 동작」** 뿐이다.\
> **`sorted()`·`reversed()` 가 새 리스트**이고 **`sort()` 는 `MutableList` 에만 있어 `List` 에서 컴파일 에러**라는 것은 [40번 주제](../40-read-only-collections-and-runtime-types/) (2)(4)가 이미 쟀다 — 여기서는 그 한 쌍을 **아홉 연산 × 세 받는 쪽**으로 넓힌다.
> 이 본문은 Claude 작성이다(원고 없음).

★★★ **본체는 첫째 창이다** — 「**제자리 대 새 리스트 격자 — 정렬 9연산 × (`MutableList` · `List` · `Array`) → 컴파일되나 · 반환 타입 · 원본이 바뀌나**」. 제자리인지는 **이름의 꼴**(`sort` 대 `sorted`)로 갈리는데, 그 규칙이 **정말 예외가 없는지**는 스물일곱 칸을 다 던져 봐야 안다.

## 이 주제가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **언어 보장 / API 계약** | 서명·KDoc 이 약속한 것 | ★★★ **반환 타입**(서명) — 제자리 연산은 **`Unit`**, 새 리스트 연산은 **`List<T>`** · 제자리 연산은 **`MutableList`·`Array` 에만** 있다 · ★★★ `sortedBy`·`sortBy` KDoc 「**The sort is _stable_**」 · `take` KDoc `@throws IllegalArgumentException if [n] is negative` |
| **구현(stdlib)** | 이 판의 stdlib 가 실제로 하는 것 | ★★ `sorted()` 결과가 **`java.util.Arrays$ArrayList`**(배열에 정렬 후 `asList()`) · `chunked(n)` 이 **`windowed(n, n, partialWindows = true)`** 한 줄 · 예외 **문장**(`Requested element count -1 is less than zero.` · `Both size 0 and step 1 must be greater than zero.`) |
| **이 판의 관찰** | kotlinc 2.4.20 에서 이번에 본 것 | 진단 문구 · `Random(7)` 이 만든 순열 |

## 이 판

```text
===== kotlinc -version =====
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | (이 주제에는 없다) | ★ `shuffle`·`shuffled` 는 **`Random(7)`** 로 씨앗을 고정했다 — 칸마다 새 `Random(7)` |
| 안 흔들린다 | 격자 27행 · 제자리 칸 수 | 컴파일러 진단과 실행 출력이 결정적이다 |
| 안 흔들린다 | ★ `Random(7)` 이 만든 순열(`[1, 3, 2]`) | **이 판의 `kotlin.random` 구현**에서 결정적 — 판이 오르면 바뀔 수 있다(아래 「구현 세부사항」) |
| 안 흔들린다 | 경계 출력(`take`·`windowed`) · 예외 문장 · stdlib 발췌 · 종료 코드 | 결정적이다 |

★ 근거 — 캡처 스크립트를 처음부터 두 번 돌려 **블록 전체를 대조**했다(수치는 3-answer 의 「실행 검증」).

## 한눈에 — 쉽게 말하면

**`sort` 는 「책장을 직접 다시 꽂는 것」이고 `sorted` 는 「정렬된 목록을 새 종이에 적어 주는 것」이다.** 책장을 다시 꽂으면 돌려줄 것이 없다(`Unit`). 새 종이는 돌려준다(`List`). 그래서 **과거분사(`-ed`) 꼴이면 새 리스트, 동사 원형이면 제자리** — 그리고 제자리는 **책장을 고칠 권한**(`MutableList`·`Array`)이 있어야 한다.
★ 줄 세우기에는 약속이 하나 더 있다 — **같은 키끼리는 원래 순서를 지킨다**(안정 정렬). 그런데 「정렬한 뒤 뒤집기」는 그 약속을 **뒤집는다.**

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 책장을 직접 다시 꽂는다 | `sort`·`sortBy`·`sortDescending`·`reverse`·`shuffle` → `Unit` · 원본이 바뀐다 | (1) ★ |
| 새 종이에 적어 준다 | `sorted`·`sortedBy`·`reversed`·`shuffled` → `List` · 원본 그대로 | (1) |
| 열람실 책장(읽기 전용) | `List` 에는 제자리 연산이 **없다** — 컴파일 에러 | (1) |
| 같은 키는 원래 순서대로 | `sortedBy`·`sortBy` — 안정 정렬 | (2) ★ |
| 정렬 후 뒤집으면 같은 키도 뒤집힌다 | `sortedBy{}.reversed()` ≠ `sortedByDescending{}` | (2) ★ |
| 창문 틀로 훑기 — 끝의 반쪽 창은 버린다 | `windowed(3)` · `partialWindows = true` | (4) ★ |

```text
   이름의 꼴 → 받는 쪽 → 결과                       (원본 [3, 1, 2])
   ─────────────────────────────────────────────────────────────────────────────
   sort  sortBy  sortDescending  reverse  shuffle          (동사 원형)
        MutableList · Array  →  Unit      원본이 바뀐다   [1, 2, 3] · [3, 2, 1] · [2, 1, 3] · …
        List(읽기 전용)       →  ✗ 컴파일 에러 「unresolved reference 'sort' …」
   sorted  sortedBy  reversed  shuffled                     (-ed 꼴)
        MutableList · List · Array  →  List<Int>   원본 그대로 [3, 1, 2]
        (단 Array.shuffled 는 없다 ✗)

   안정 정렬 — 키: b1 a2 c1 d2 e1
     sortedBy { key }                 b c e | a d      같은 키는 원래 순서
     sortedByDescending { key }       a d | b c e      같은 키는 원래 순서
     sortedBy { key }.reversed()      d a | e c b      ★ 같은 키끼리 순서까지 뒤집힌다
```

## 이 주제가 답하려는 질문

1. 정렬 연산은 **원본을 고치나, 새 리스트를 주나** — 이름으로 가를 수 있나, 예외는 없나.
2. `sortedBy` 는 **같은 키의 원래 순서**를 지키나 — 그것은 약속인가.
3. `take`·`drop`·`chunked`·`windowed` 는 **경계(음수·너무 큰 수·끝의 반쪽)** 에서 무엇을 하나.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **제자리 격자(서명 진단 + 실행)** | 9연산 × 3받는 쪽 → 컴파일되나 · 반환 타입 · 원본 변화((1)) | ★ **본체 창** — [42번 주제](../42-transformations-map-flatmap-associate-zip/) (1)의 「의도적 타입 불일치」 창 + 실행 창 |
| ★★ **안정성 관찰 + KDoc** | 같은 키의 순서 · 「The sort is _stable_」((2)) | — |
| ★★ **stdlib 소스 jar 발췌** | `sorted()` 의 구현 · `chunked` 가 `windowed` 인 것 · 예외 문장의 출처((2)(3)(4)) | [41번 주제](../41-collection-creation-and-copying/) (2)와 같은 창 |
| ★ **경계 탐침** | `take(-1)`·`take(100)`·`windowed(0)`·`partialWindows`((3)(4)) | — |
| **인용 — 다시 안 잰다** | `sorted` 가 새 리스트(`=== false` 가 아니라 **원본 불변**으로 쟀다) · `List.sort()` 컴파일 에러 전문 | [40번 주제](../40-read-only-collections-and-runtime-types/) (2)(4) |
| **인용 — 다른 갈래** | 슬라이딩 윈도우 **알고리즘** · JS `toSorted` 대 `sort` · Python `sort` 대 `sorted` 와 안정성 | [`algorithm/09`](../../../../../algorithm/09-sliding-window/) · [JS 25번](../../../js/syntax/25-array-non-mutating-and-copy-methods/) · [Python 10번](../../../python/syntax/10-list-methods-and-sort-key/) |
| **부적용 — 실행 시간·할당** | ★★★ 「`sortBy` 가 `sortedBy` 보다 싸다」·「제자리가 빠르다」는 **재지 않았다** — 이 문서는 **원본이 바뀌느냐**만 본다 | — |

### (1) ★★★ 제자리 대 새 리스트 격자

**언제 쓰나** — 받은 리스트를 정렬하려는데 **원본을 건드려도 되는지** 가려야 할 때.

두 파일을 쓴다. `sig45.kt` 는 [42번 주제](../42-transformations-map-flatmap-associate-zip/) (1)처럼 결과를 `fun t(x: Nothing?)` 에 넘겨 **컴파일러가 반환 타입(또는 「없음」)을 말하게** 한다. `run45.kt` 는 **컴파일되는 칸만** 실제로 돌려, 매번 새 `[3, 1, 2]` 에 연산을 부른 뒤 **원본이 어떻게 됐나**를 찍는다. 격자 스크립트가 둘을 합친다.

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

- ★★★ **제자리 칸은 컴파일되는 21칸 중 10칸이고, 그 10칸이 정확히 반환 타입 `Unit` 인 칸이다** — `Unit` 이면 원본이 바뀌었고, `List<Int>` 면 원본이 `[3, 1, 2]` 그대로다. **예외가 없다.**
- ★★★ **이름으로 가른다** — 동사 원형(`sort`·`sortBy`·`sortDescending`·`reverse`·`shuffle`)은 제자리 · `-ed` 꼴(`sorted`·`sortedBy`·`reversed`·`shuffled`)은 새 리스트.
- ★★★ **`List`(읽기 전용)에서 제자리 다섯은 컴파일이 안 된다** — `unresolved reference 'sort' on receiver of type 'List<Int>'.` 꼴이다(아래 `grep` 블록). `ro.sort()` 한 줄의 진단은 [40번 주제](../40-read-only-collections-and-runtime-types/) (2)의 `bad40.kt` 가 먼저 실었다.
- ★★ **`Array` 도 제자리 다섯을 다 갖는다** — `ar.sort()`·`ar.reverse()` 가 배열을 **직접** 고친다. 반면 **`Array.sorted()` 는 `Array` 가 아니라 `List<Int>`** 다(배열로 받으려면 `sortedArray()` — 이 문서는 던지지 않았다).
- ★★ **`Array.shuffled` 는 없다** — `unresolved reference 'shuffled' on receiver of type 'Array<Int>'.`. 27칸 중 **이름 규칙 밖에서 빠진 칸**은 이것 하나다.
- ★ `sortDescending` 은 제자리 · 새 리스트 쪽 짝은 `sortedDescending`(격자 밖).

### (2) ★★ 안정 정렬 — 같은 키는 원래 순서를 지킨다

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

```text
===== unzip -o -q kotlin-stdlib-sources.jar commonMain/generated/_Collections.kt commonMain/generated/_Maps.kt commonMain/kotlin/collections/Maps.kt commonMain/kotlin/collections/SlidingWindow.kt jvmMain/generated/_CollectionsJvm.kt =====
(exit 0)
```

```text
===== sed -n '1172,1175p;1179,1180p' commonMain/generated/_Collections.kt =====
 * Sorts elements in the list in-place according to natural sort order of the value returned by specified [selector] function.
 * 
 * The sort is _stable_. It means that elements for which [selector] returned equal values preserve their order
 * relative to each other after sorting.
public inline fun <T, R : Comparable<R>> MutableList<T>.sortBy(crossinline selector: (T) -> R?): Unit {
    if (size > 1) sortWith(compareBy(selector))
(exit 0)
===== sed -n '1219,1222p;1226,1227p' commonMain/generated/_Collections.kt =====
 * Returns a list of all elements sorted according to natural sort order of the value returned by specified [selector] function.
 * 
 * The sort is _stable_. It means that elements for which [selector] returned equal values preserve their order
 * relative to each other after sorting.
public inline fun <T, R : Comparable<R>> Iterable<T>.sortedBy(crossinline selector: (T) -> R?): List<T> {
    return sortedWith(compareBy(selector))
(exit 0)
```

```text
===== sed -n '1209,1216p' commonMain/generated/_Collections.kt =====
public fun <T : Comparable<T>> Iterable<T>.sorted(): List<T> {
    if (this is Collection) {
        if (size <= 1) return this.toList()
        @Suppress("UNCHECKED_CAST")
        return (toTypedArray<Comparable<T>>() as Array<T>).apply { sort() }.asList()
    }
    return toMutableList().apply { sort() }
}
(exit 0)
```

- ★★★ **`sortedBy { second }` 는 `bcead`** — 키 `1` 인 `b`·`c`·`e` 가 **입력 순서대로**, 키 `2` 인 `a`·`d` 가 입력 순서대로다. KDoc 이 「``The sort is _stable_. It means that elements for which [selector] returned equal values preserve their order relative to each other after sorting.``」라고 **약속한다**(`sortBy` 도 같은 문장).
- ★★★ **`sortedByDescending` 은 `adbce`, `sortedBy{}.reversed()` 는 `daecb`** — 키의 큰 순서는 같지만 **같은 키 안의 순서가 반대**다. 내림차순 정렬은 안정성을 지키고, **뒤집기는 같은 키끼리도 뒤집는다.** [Python 10번](../../../python/syntax/10-list-methods-and-sort-key/)의 `reverse=True` 대 「뒤집기」와 같은 자리다.
- ★★ **제자리 `sortBy` 도 `bcead`** — 제자리이냐 아니냐는 안정성과 **무관**하다.
- ★★ **`sorted()` 의 결과는 `java.util.Arrays$ArrayList`** — 소스가 원소를 **배열에 복사해 `sort()` 한 뒤 `asList()`** 로 감싼다(원소가 둘 이상인 `Collection` 일 때). [41번 주제](../41-collection-creation-and-copying/) (1)의 `listOf(1, 2, 3)` 와 **같은 클래스**다 — 크기가 고정된 리스트다.
- ★ 「안정」은 **KDoc 계약**이고, 그 안정성을 **실제로 누가 주는지**(`sortWith` → JVM 의 어느 정렬인가)는 이 문서가 **따라가지 않았다.**

### (3) ★★ `take`·`drop` 의 경계

한 프로그램(`part45.kt`)이 (3)과 (4)의 경계를 전부 던진다 — `1`\~`10` 줄이 (3), `11`\~`21` 줄이 (4)다.

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

- ★★★ **`take(-1)` 은 `IllegalArgumentException: Requested element count -1 is less than zero.`** — `drop(-1)` 도 **같은 문장**이다. KDoc 의 `@throws IllegalArgumentException if [n] is negative` 그대로다((4)의 발췌 `require(n >= 0)`).
- ★★★ **`take(100)` 은 7개 전부** — 모자라면 **있는 만큼** 준다(예외 아님). `drop(100)` 은 `[]`.
- ★★ **`take(0)` 은 `[]`** — 음수만 던진다.
- ★★ **`takeWhile { >3 }` 은 `[]`** — 조건이 **첫 원소에서** 거짓이면 거기서 멈춘다. 뒤쪽의 `4`·`5`·`6`·`7` 은 조건을 만족하지만 **보지도 않는다.** `filter` 와 다르다.
- ★ `takeLast(2)` 는 `[6, 7]` · `dropWhile { <3 }` 은 `[3, 4, 5, 6, 7]`.

### (4) ★★★ `chunked`·`windowed` 의 경계 — 끝의 반쪽을 버리나

실행 출력은 (3)의 `11`\~`21` 줄이다. 그 동작을 정하는 소스 —

```text
===== grep -n -A2 '^public fun <T> Iterable<T>\.chunked(size: Int): List<List<T>>' commonMain/generated/_Collections.kt =====
3555:public fun <T> Iterable<T>.chunked(size: Int): List<List<T>> {
3556-    return windowed(size, size, partialWindows = true)
3557-}
(exit 0)
===== sed -n '8,15p' commonMain/kotlin/collections/SlidingWindow.kt =====
internal fun checkWindowSizeStep(size: Int, step: Int) {
    require(size > 0 && step > 0) {
        if (size != step)
            "Both size $size and step $step must be greater than zero."
        else
            "size $size must be greater than zero."
    }
}
(exit 0)
===== sed -n '901p;905,906p' commonMain/generated/_Collections.kt =====
 * @throws IllegalArgumentException if [n] is negative.
public fun <T> Iterable<T>.take(n: Int): List<T> {
    require(n >= 0) { "Requested element count $n is less than zero." }
(exit 0)
===== sed -n '3755p;3758,3759p' commonMain/generated/_Collections.kt =====
 * Both [size] and [step] must be positive and can be greater than the number of elements in this collection.
 * @param partialWindows controls whether or not to keep partial windows in the end if any,
 * by default `false` which means partial windows won't be preserved
(exit 0)
```

```text
   xs = 1 2 3 4 5 6 7                         결과
   ─────────────────────────────────────────────────────────────────────
   chunked(3)                    [1 2 3] [4 5 6] [7]            ← 마지막 짧은 덩어리를 남긴다
   windowed(3)                   [1 2 3] [2 3 4] … [5 6 7]      ← 5개. 끝의 [6 7] [7] 은 버린다
   windowed(3, partialWindows = true)   … [5 6 7] [6 7] [7]     ← 7개
   windowed(3, step = 2)         [1 2 3] [3 4 5] [5 6 7]        ← 딱 맞아 버릴 것이 없다
   windowed(3, step = 3)         [1 2 3] [4 5 6]                ← [7] 을 버린다
   windowed(3, 3, true)          [1 2 3] [4 5 6] [7]            ← = chunked(3)
   windowed(10)                  (없음)                          ← 창이 입력보다 크면 빈 리스트
```

- ★★★ **`windowed(3)` 은 끝의 반쪽 창을 버린다** — 7개에서 창 5개, `[6, 7]`·`[7]` 이 없다. KDoc 의 `partialWindows` 설명 「``by default `false` which means partial windows won't be preserved``」 그대로다(위 발췌 3759행).
- ★★★ **`chunked(3)` 은 마지막 `[7]` 을 남긴다** — 소스가 `windowed(size, size, partialWindows = true)` **한 줄**이다. 그래서 `windowed(3, 3, true)`(`16`)와 **같은 답**이다. `windowed(3, step = 3)`(`15`)는 `[7]` 을 **버린다** — `chunked` 와 **한 인자** 차이다.
- ★★ **`windowed(0)` 은 `IllegalArgumentException: Both size 0 and step 1 must be greater than zero.`** · **`chunked(0)` 은 `size 0 must be greater than zero.`** — 같은 검사 함수(`checkWindowSizeStep`)가 **`size != step` 이냐로 문장을 고른다.** `chunked` 는 `size == step` 이라 짧은 문장이다.
- ★★ **`windowed(10)` 은 `[]`** — 창이 입력보다 커도 **던지지 않는다.** KDoc 도 「``Both [size] and [step] must be positive and can be greater than the number of elements in this collection.``」이라고 한다(위 발췌 3755행).
- ★ **`zipWithNext()` 는 `windowed(2)` 의 `Pair` 판**이다 — 여섯 쌍.
- ★ **여기까지가 이 문서의 몫이다** — 창을 밀며 합을 **O(1) 로 갱신하는** 슬라이딩 윈도우 기법은 [`cs/algorithm/09-sliding-window/`](../../../../../algorithm/09-sliding-window/) 다. `windowed` 는 **창마다 새 리스트**를 만든다 — 그것이 그 기법과 같은 비용인지는 **재지 않았다.**

## 문법 — 형태와 규칙

**형태** — 우선순위로 정렬(새 리스트와 제자리), 앞에서 둘, 세 개씩 쪽 나누기, 이웃끼리 비교.

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

**규칙 불릿**

- **`-ed` 꼴은 새 리스트, 동사 원형은 제자리**((1)) — `tasks` 줄이 원래 순서 그대로인 것은 `sortedBy` 가 새 리스트이고 `sortByDescending` 은 **사본**(`toMutableList()`)을 고쳤기 때문이다.
- **제자리는 `MutableList`·`Array` 에서만** — `List` 는 컴파일 에러((1)).
- **`sortedBy`·`sortBy` 는 안정 정렬** — `ordered` 줄에서 우선순위 `1` 인 `call`·`lunch` 가 **입력 순서대로**, `2` 인 `mail`·`docs` 도 입력 순서대로다((2)).
- **`sortByDescending` 도 안정** — `work` 줄의 `mail`·`docs` 순서를 보라((2)).
- **`take(n)` 은 모자라면 있는 만큼, 음수면 던진다**((3)).
- **`chunked(n)` 은 마지막 짧은 덩어리를 남기고, `windowed(n)` 은 버린다**((4)).

## 어디서 틀리나

1. ★★★ **`list.sorted()` 를 부르고 `list` 가 정렬됐다고 믿는다.** 새 리스트다 — 원본은 그대로다((1)). 결과를 받지 않으면 **아무 일도 안 한 것**이다.
2. ★★★ **`sortedBy{}.reversed()` 를 `sortedByDescending{}` 과 같다고 본다.** 같은 키끼리의 순서가 **반대**다((2)).
3. ★★ **`windowed(n)` 이 끝까지 다 훑는다고 본다.** 끝의 반쪽 창을 **버린다** — `partialWindows = true`((4)).
4. ★★ **`windowed(n, step = n)` 을 `chunked(n)` 과 같다고 본다.** 마지막 짧은 덩어리를 **버린다**((4)).
5. ★★ **`take(n)` 이 원소가 모자라면 던진다고 본다.** 있는 만큼 준다. 던지는 것은 **음수**뿐이다((3)).
6. ★ **`takeWhile` 을 `filter` 처럼 쓴다.** 첫 거짓에서 **멈춘다**((3)).
7. ★ **`Array.sorted()` 가 배열을 준다고 본다.** `List` 다((1)).
8. ★ **`sorted()` 결과를 캐스트해 `add` 한다.** 결과는 `Arrays$ArrayList`(크기 고정)다((2)) — `add` 는 거부될 것이다(이 문서는 **던지지 않았다** — [41번 주제](../41-collection-creation-and-copying/) (1)·[40번 주제](../40-read-only-collections-and-runtime-types/)의 같은 클래스 관찰을 보라).

## 구현 세부사항 대 언어 보장

| 항목 | 어느 쪽인가 | 근거 |
|---|---|---|
| 제자리 연산이 `Unit` · 새 리스트 연산이 `List` | ★★★ **API 계약(서명)** | (1) |
| 제자리 연산이 `List` 에 없다 | ★★★ **API 계약(`MutableList`·`Array` 확장)** | (1) · [40번 주제](../40-read-only-collections-and-runtime-types/) (2) |
| `sortedBy`·`sortBy` 가 안정 | ★★★ **API 계약(KDoc)** | (2) |
| `take` 가 음수에서 `IllegalArgumentException` | ★★ **API 계약(KDoc `@throws`)** — 문장은 구현 | (3)(4) |
| `windowed` 의 부분 창 버림 · `partialWindows` | ★★ **API 계약(KDoc — 기본값 설명)** | (4) |
| `sorted()` 결과가 `Arrays$ArrayList` | ★★ **stdlib 구현** | (2) |
| `chunked` = `windowed(n, n, true)` | ★ **stdlib 구현**(한 줄 위임) — 결과가 같은 것은 관찰 | (4) |
| 예외 **문장** 전부 · `size != step` 으로 문장 고르기 | ★ **stdlib 구현** | (3)(4) |
| `Random(7)` 이 만드는 순열 | ★ **`kotlin.random` 구현** — 씨앗이 같으면 같은 순서는 **이 판의 관찰**. 판을 넘는 보장은 확인하지 않았다 | (1) |

★★ **가장 조심할 자리** — 「이름으로 가른다」는 **이 판의 27칸에서 예외가 없었다**는 관찰이지, 새 확장 함수가 그 관례를 지킨다는 보장은 아니다. **반환 타입이 `Unit` 인가**를 보는 쪽이 서명으로 확인되는 근거다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 받은 리스트를 정렬해 **새로** 쓴다 | `sorted()` · `sortedBy {}` | (1) — 원본을 안 건드린다 |
| 내 `MutableList` 를 정렬해 둔다 | `sort()` · `sortBy {}` | (1) — 제자리 · `Unit` |
| 내림차순 + 같은 키는 원래 순서 | `sortedByDescending {}` | (2) — ★ `reversed()` 가 아니다 |
| 앞에서 n개(모자라면 있는 만큼) | `take(n)` | (3) |
| 조건이 참인 **앞부분**만 | `takeWhile {}` | (3) — 전부면 `filter` |
| 쪽 나누기(마지막 쪽이 짧아도 된다) | `chunked(n)` | (4) |
| 이웃 n개씩 훑기(끝의 반쪽은 버린다) | `windowed(n)` | (4) |
| 이웃 둘씩 | `zipWithNext()` | (4) |
| JS 의 `toSorted` 처럼 **복사해서 정렬** | `sorted()` | [JS 25번](../../../js/syntax/25-array-non-mutating-and-copy-methods/) — JS 는 `sort` 가 제자리이고 복사판 `toSorted` 가 ES2023 에 들어왔다. Kotlin 은 **처음부터 이름이 둘**이다 |

## 핵심 문장

1. 정렬 9연산 × 3받는 쪽 27칸에서 **컴파일되는 21칸 중 제자리는 10칸**이고, 그 10칸이 정확히 **반환 타입 `Unit`** 인 칸이다.
2. **동사 원형은 제자리, `-ed` 꼴은 새 리스트** — 제자리는 `MutableList`·`Array` 에만 있고 `List` 에서는 컴파일 에러다.
3. **`sortedBy` 는 안정 정렬**이다(KDoc) — 그러나 **`sortedBy{}.reversed()` 는 같은 키끼리의 순서까지 뒤집는다.**
4. **`take(n)` 은 모자라면 있는 만큼**, 음수면 `IllegalArgumentException("Requested element count -1 is less than zero.")`.
5. **`windowed(n)` 은 끝의 반쪽 창을 버리고, `chunked(n)`(= `windowed(n, n, true)`)은 남긴다.**

## 관련 자료

- [41번 주제](../41-collection-creation-and-copying/) — ★★★ **선행.** `sorted()` 결과의 `Arrays$ArrayList` 는 `listOf(1, 2, 3)` 와 같은 클래스다.
- [40번 주제](../40-read-only-collections-and-runtime-types/) (2)(4) — `sorted` 는 새 리스트 · `sort` 는 `MutableList` 에만 · `List.sort()` 의 진단 전문.
- [42번 주제](../42-transformations-map-flatmap-associate-zip/) (1) — 「의도적 타입 불일치」 창.
- [`cs/algorithm/09-sliding-window/`](../../../../../algorithm/09-sliding-window/) — ★★ **슬라이딩 윈도우 알고리즘은 거기.** 그쪽은 「창을 밀며 무엇을 갱신하나」, 여기는 「stdlib 의 `windowed` 가 끝에서 무엇을 버리나」.
- [JS 25번](../../../js/syntax/25-array-non-mutating-and-copy-methods/) — `toSorted` 대 `sort`. [JS 24번](../../../js/syntax/24-array-mutating-methods/) — 제자리 메서드.
- [Python 10번](../../../python/syntax/10-list-methods-and-sort-key/) — `list.sort()` 대 `sorted()` · 안정 정렬이 「언어 보장」인 것.

## 용어 풀이

> **제자리(in-place)** — 새 컬렉션을 만들지 않고 **원본을 고치는** 연산. Kotlin 에서는 반환 타입이 `Unit` 이다.\
> 예: `ml.sort()` 뒤 `ml` 이 `[1, 2, 3]`.

> **안정 정렬(stable sort)** — 키가 같은 원소끼리 **원래 순서**를 지키는 정렬.

> **`partialWindows`** — `windowed` 가 끝의 **원소가 모자란 창**을 남길지 정하는 인자. 기본 `false`(버린다).

> **`step`** — `windowed` 가 창을 **몇 칸씩** 밀지. 기본 `1`.

> **`chunked`** — 겹치지 않게 n개씩 자른다. 마지막 덩어리는 짧을 수 있다.

> **`takeWhile`** — 앞에서부터 조건이 참인 동안만 가져오고, **처음 거짓에서 멈춘다.**

## 더 들어가면

- **`sortedArray()`·`sortedDescending()`·`sortWith`** — 격자에 넣지 않았다.
- **`sortWith` 가 JVM 에서 무엇을 부르나** — 안정성을 실제로 주는 정렬 알고리즘을 **따라가지 않았다.**
- **`windowed` 의 `transform` 판** — 창마다 리스트를 만들지 않고 변환하는 오버로드가 있다(소스 3804행). 던지지 않았다.
