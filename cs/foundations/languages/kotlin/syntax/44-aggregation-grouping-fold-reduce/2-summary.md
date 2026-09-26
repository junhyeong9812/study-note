# kotlin/syntax/44 — 집계·그룹핑 — `groupBy`/`partition`/`fold`/`reduce`/`sumOf` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Aggregate operations](https://kotlinlang.org/docs/collection-aggregate.html)(`sum`·`average`·`sumOf`·`maxBy` · `fold`·`reduce` · `runningFold`·`runningReduce` · `…OrNull`) · [Grouping](https://kotlinlang.org/docs/collection-grouping.html)(`groupBy`) · [Filtering](https://kotlinlang.org/docs/collection-filtering.html)(`partition`) — 이 문서는 그 페이지들의 **목록**을 따르되, 문장은 인용하지 않고 **이 판의 stdlib 소스 jar**(`kotlin-stdlib-sources.jar` 2.4.20)의 KDoc 과 구현을 근거로 삼는다((3)(4)).
> **실행 검증** — 이 문서의 모든 출력·에러는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `java` 에서 실제로 얻었다. 대비 둘은 **rustc 1.92.0** · **Python 3.12.3** 이다.\
> `kotlinc` 4회 · `java` 3회 + 격자 스크립트 안에서 1회 · stdlib 소스 jar 에서 5곳 · `rustc` 2회(최적화 끔/켬) + 실행 2회 · `python3` 1회.\
> ★★ 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적지 않았다. **격자 마지막 줄의 칸 수는 스크립트가 스스로 센 것**이다.
> **버전** — `fold`·`reduce`·`groupBy`·`partition`·`sum`·`average` 는 **1.0** — 이 판의 소스에서 선언 위에 `@SinceKotlin` 이 **없다**(확인만 했고 발췌하지 않았다). `reduceOrNull`·`runningFold`·`runningReduce`·`maxByOrNull` 은 stdlib 소스에 **`@SinceKotlin("1.4")`**((3)) · `sumOf` 도 **1.4**((4)). ★ **새 `maxBy` 는 `@SinceKotlin("1.7")` · `@JvmName("maxByOrThrow")`**((3)) — [43번 주제](../43-filter-search-and-empty-collections/) (4)의 `max()` 와 같은 모양이다(옛 `maxBy` 의 애너테이션은 **발췌하지 않았다**).
> **경계** — 빈 입력에서 **검색 연산**(`first`·`single`·`max`)이 던지는 것은 [43번 주제](../43-filter-search-and-empty-collections/)가 정본이다. 여기는 **접기(fold)와 묶기(group)** 다. `Int` 덧셈이 넘치면 **감긴다**는 언어 규칙은 [01번 주제](../01-val-var-and-basic-types/)가 정본이다 — 여기서는 `sumOf` 가 그 규칙을 **그대로 물려받는다**는 것만 본다. `partition` 결과를 `val (a, b) =` 로 받는 것은 [30번 주제](../30-destructuring-declarations-and-componentn/)다.
> 이 본문은 Claude 작성이다(원고 없음).

★★★ **본체는 첫째 창이다** — 「**빈 입력 갈림 격자 — 집계 12연산 × (빈 · 하나 · 여럿) → 값 / 예외**」. `fold` 와 `reduce` 는 원소가 있을 때 **같은 답**을 준다(`5`·`10`). 둘이 갈리는 것은 **빈 입력 한 칸**이다 — 거기를 넣어 봐야 보인다.

## 이 주제가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **언어 보장 / API 계약** | 서명·KDoc 이 약속한 것 | ★★★ `fold` KDoc 「빈 컬렉션이면 **`initial`** 을 돌려준다」 · `reduce` KDoc 「빈 컬렉션이면 **던진다** — `reduceOrNull` 을 써라」 · `partition` 은 **`Pair<List<T>, List<T>>`** · ★ `Int` 덧셈은 **감긴다**(언어 — 01) |
| **구현(stdlib)** | 이 판의 stdlib 가 실제로 하는 것 | ★★ `reduce` 가 **`UnsupportedOperationException`** 을 고른 것과 그 문장 · `average()` 가 빈 입력에서 **`Double.NaN`** 을 돌려주는 `if` 한 줄 · `sumOf { Int }` 가 **`Int` 누산기**로 더하는 것 · `groupBy` 결과가 `LinkedHashMap` |
| **이 판의 관찰** | 이번 실행에서 본 것 | ★ Rust `sum` 은 최적화 **끔**에서 패닉, **켬**에서 감김 |

## 이 판

```text
===== kotlinc -version =====
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
(exit 0)
```

```text
===== rustc --version =====
rustc 1.92.0 (ded5c06cf 2025-12-08)
(exit 0)
```

```text
===== python3 --version =====
Python 3.12.3
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | Rust 패닉 첫 줄의 **스레드 id**(`thread 'main' (NNN) panicked`) | 실행마다 바뀐다 — 재대조기가 정규화한다 |
| 안 흔들린다 | 격자 12행 × 3열 · 마지막 줄의 칸 수 | 결정적이다 |
| 안 흔들린다 | 오버플로 값(`-2147483648`) · `groupBy` 의 키 순서 | 2의 보수 · `LinkedHashMap` 삽입 순서 |
| 안 흔들린다 | stdlib 소스 발췌 · Rust 패닉의 **메시지·위치**(`accum.rs:204:1`) · 모든 종료 코드 | 판이 같으면 같다 |

★ 근거 — 캡처 스크립트를 처음부터 두 번 돌려 **블록 전체를 대조**했다(수치는 3-answer 의 「실행 검증」).

## 한눈에 — 쉽게 말하면

**`fold` 는 「빈 바구니로 시작하는 계산원」이고 `reduce` 는 「첫 물건을 바구니 삼는 계산원」이다.** 물건이 하나라도 있으면 둘의 영수증이 같다. 물건이 **하나도 없으면** `fold` 계산원은 빈 바구니(초기값 `0`)를 그대로 내밀고, `reduce` 계산원은 **바구니로 쓸 첫 물건이 없어서 멈춘다**(예외).
★ 그리고 **계산원의 주판에는 자릿수 한계가 있다** — `Int` 로 더하면 `Int.MAX_VALUE + 1` 이 **경고 없이 음수**가 된다. `sumOf { it }` 도 그 주판을 쓴다.

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 빈 바구니로 시작 | `fold(0) { … }` — 빈 입력 → `0` | (1)(3) |
| 첫 물건을 바구니로 | `reduce { … }` — 빈 입력 → `UnsupportedOperationException` | (1)(3) ★ |
| 「없으면 쪽지」 계산원 | `reduceOrNull` · `maxByOrNull` — 빈 입력 → `null` | (1) |
| 0으로 나누는 평균 | `average()` — 빈 입력 → **`NaN`**(예외 아님) | (1)(4) ★ |
| 자릿수가 모자란 주판 | `sumOf { it }` — `Int` 합이 **조용히 감긴다** | (2) ★ |
| 이름표별 상자 | `groupBy` → `LinkedHashMap<키, List>` | (5) |
| 두 상자로 가르기 | `partition` → `Pair<List, List>` | (5) |

```text
   입력           fold(0) { a, x -> a + x }          reduce { a, x -> a + x }
   ─────────────────────────────────────────────────────────────────────────────
   [1, 2, 3, 4]   0 → 0+1 → 1+2 → 3+3 → 6+4 = 10      1 → 1+2 → 3+3 → 6+4 = 10    (같다)
   [5]            0 → 0+5 = 5                         5                           (같다 — 연산을 안 부른다)
   []             0  (initial 을 그대로)               ✗ UnsupportedOperationException
                                                        「Empty collection can't be reduced.」
                   ↑ 시작값이 있다                       ↑ 시작값으로 쓸 첫 원소가 없다
```

## 이 주제가 답하려는 질문

1. 집계 연산은 빈 입력에서 **무엇을 돌려주나** — 예외 · `null` · `NaN` · 정해진 값 중 어느 것인가.
2. `fold` 와 `reduce` 는 **정확히 어디서** 갈리나 — 그리고 그것은 계약인가.
3. `sumOf` 의 합이 넘치면 **무엇이 일어나나** — 다른 언어는 어떻게 하나.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **빈 입력 갈림 격자(실행 + `try`)** | 12연산 × 3입력 → 값 / 예외((1)) | ★ **본체 창** |
| ★★ **오버플로 로그** | `sumOf { it }` 대 `sumOf { it.toLong() }` 대 `Math.addExact`((2)) | — |
| ★★ **stdlib 소스 jar 발췌** | `fold`·`reduce` 의 KDoc 계약 · `sumOf`·`sum`·`average` 의 누산기((3)(4)) | [41번 주제](../41-collection-creation-and-copying/) (2)와 같은 창 |
| ★ **런타임 클래스** | `groupBy` 결과 · `partition` 결과의 실체((5)) | [40번 주제](../40-read-only-collections-and-runtime-types/)의 창 |
| ★ **다른 언어 둘** | Rust `reduce` 는 `Option` · Rust `sum` 은 최적화에 따라 **패닉/감김** · Python `sum` 은 **안 넘친다**((6)) | 대비 |
| **인용 — 다시 안 잰다** | Python `functools.reduce` 의 빈 입력 `TypeError` · JS `[].reduce(f)` 의 `TypeError` · Java 스트림 `reduce` 의 `Optional` | [Python 45번](../../../python/syntax/45-functools/) · [JS 25번](../../../js/syntax/25-array-non-mutating-and-copy-methods/) · [Java 46번](../../../java/syntax/46-terminal-operations/) |
| **부적용 — 실행 시간** | 「`sumOf` 가 `fold` 보다 빠르다」·「`groupBy` 가 비싸다」는 **재지 않았다** | — |

### (1) ★★★ 빈 입력 갈림 격자 — `fold` 와 `reduce` 가 갈리는 한 칸

**언제 쓰나** — 입력이 비어 있을 **수도** 있는 자리에서 합계·최댓값·그룹을 낼 때.

입력 셋 — `empty=[]` · `one=[5]` · `many=[1, 2, 3, 4]`. 칸마다 `try` 로 감싸 **값(`= …`)** 이나 **예외(`! 클래스: 메시지`)** 를 적고, 스크립트가 **빈 입력 열의 결과 꼴**을 센다.

```kotlin
// agg44.kt
val inputs = listOf(
    "empty" to listOf<Int>(),
    "one" to listOf(5),
    "many" to listOf(1, 2, 3, 4),
)

val ops: List<Pair<String, (List<Int>) -> Any?>> = listOf(
    "fold(0){+}" to { xs -> xs.fold(0) { acc, x -> acc + x } },
    "reduce{+}" to { xs -> xs.reduce { acc, x -> acc + x } },
    "reduceOrNull{+}" to { xs -> xs.reduceOrNull { acc, x -> acc + x } },
    "sumOf{it}" to { xs -> xs.sumOf { it } },
    "sum()" to { xs -> xs.sum() },
    "average()" to { xs -> xs.average() },
    "groupBy{it%2}" to { xs -> xs.groupBy { it % 2 } },
    "partition{even}" to { xs -> xs.partition { it % 2 == 0 } },
    "maxBy{it}" to { xs -> xs.maxBy { it } },
    "maxByOrNull{it}" to { xs -> xs.maxByOrNull { it } },
    "runningFold(0){+}" to { xs -> xs.runningFold(0) { acc, x -> acc + x } },
    "runningReduce{+}" to { xs -> xs.runningReduce { acc, x -> acc + x } },
)

fun main() {
    for ((opName, op) in ops) {
        for ((inName, xs) in inputs) {
            val cell = try {
                "= " + op(xs)
            } catch (e: Exception) {
                "! " + e::class.java.simpleName + ": " + e.message
            }
            println(listOf(opName, inName, cell).joinToString("\t"))
        }
    }
}
```

```python
# grid44.py
import subprocess
import sys

d = sys.argv[1]
out = subprocess.run(["java", "-cp", d + ":kotlin-stdlib.jar", "Agg44Kt"],
                     capture_output=True, text=True, check=True).stdout
cols = ["empty", "one", "many"]
rows = {}
order = []
for line in out.splitlines():
    cells = line.split("\t")
    if len(cells) != 3:
        raise SystemExit("cell count mismatch: " + line)
    op, inp, cell = cells
    if op not in rows:
        rows[op] = {}
        order.append(op)
    rows[op][inp] = cell
print("inputs: empty=[] one=[5] many=[1, 2, 3, 4]")
print("\t".join(["op"] + cols))
threw = {c: 0 for c in cols}
kinds = {"threw": 0, "null": 0, "NaN": 0, "value": 0}
for op in order:
    if sorted(rows[op]) != sorted(cols):
        raise SystemExit("missing column: " + op)
    print("\t".join([op] + [rows[op][c] for c in cols]))
    for c in cols:
        if rows[op][c].startswith("! "):
            threw[c] += 1
    e = rows[op]["empty"]
    kinds["threw" if e.startswith("! ") else "null" if e == "= null" else "NaN" if e == "= NaN" else "value"] += 1
n = len(order)
print("on empty (%d ops): threw %d · null %d · NaN %d · value %d | threw on one or many: %d / %d"
      % (n, kinds["threw"], kinds["null"], kinds["NaN"], kinds["value"], threw["one"] + threw["many"], 2 * n))
```

```text
===== kotlinc agg44.kt -d o44a =====
(exit 0)
```

```text
===== python3 grid44.py o44a =====
inputs: empty=[] one=[5] many=[1, 2, 3, 4]
op	empty	one	many
fold(0){+}	= 0	= 5	= 10
reduce{+}	! UnsupportedOperationException: Empty collection can't be reduced.	= 5	= 10
reduceOrNull{+}	= null	= 5	= 10
sumOf{it}	= 0	= 5	= 10
sum()	= 0	= 5	= 10
average()	= NaN	= 5.0	= 2.5
groupBy{it%2}	= {}	= {1=[5]}	= {1=[1, 3], 0=[2, 4]}
partition{even}	= ([], [])	= ([], [5])	= ([2, 4], [1, 3])
maxBy{it}	! NoSuchElementException: null	= 5	= 4
maxByOrNull{it}	= null	= 5	= 4
runningFold(0){+}	= [0]	= [0, 5]	= [0, 1, 3, 6, 10]
runningReduce{+}	= []	= [5]	= [1, 3, 6, 10]
on empty (12 ops): threw 2 · null 2 · NaN 1 · value 7 | threw on one or many: 0 / 24
(exit 0)
```

- ★★★ **던진 것은 빈 입력의 두 칸뿐이다** — `reduce{+}`(`UnsupportedOperationException: Empty collection can't be reduced.`)와 `maxBy{it}`(`NoSuchElementException`, 메시지 `null`). 원소가 하나라도 있는 24칸은 **한 칸도 안 던졌다.**
- ★★★ **`fold(0)` 은 빈 입력에서 `0`** — 초기값을 그대로 돌려준다. 원소가 있는 두 칸(`5`·`10`)은 `reduce` 와 **같다.** 둘이 갈리는 곳은 **빈 입력 한 칸**이다.
- ★★★ **`average()` 는 빈 입력에서 `NaN`** — 예외가 아니다. 「평균을 못 낸다」가 **값으로** 온다. 비교(`== NaN`)로는 못 잡는다 — `isNaN()`.
- ★★ **빈 입력 12칸의 꼴** — 던짐 2 · `null` 2(`reduceOrNull` · `maxByOrNull`) · `NaN` 1 · 값 7. 「값」 7칸도 **서로 다른 값**이다 — `0`(`fold`·`sumOf`·`sum`) · `{}` · `([], [])` · `[0]`(`runningFold` — **초기값 하나가 든 리스트**) · `[]`(`runningReduce`).
- ★★ **`runningFold` 와 `runningReduce` 는 빈 입력에서도 안 던진다** — 같은 `fold`/`reduce` 짝인데 **리스트를 돌려주니** 「비어 있음」을 `[]` 로 표현할 수 있다. `runningFold` 는 **초기값을 첫 원소로** 싣는다(`[0, 5]` · `[0, 1, 3, 6, 10]`).
- ★ **원소가 하나면 `reduce` 는 연산을 안 부른다** — `[5]` 가 그대로 `5` 다(그림). [Python 45번](../../../python/syntax/45-functools/) (6)의 `reduce(add, [7])` 「호출 0」과 같은 자리다.

### (2) ★★ `sumOf` 의 합은 조용히 넘친다

```kotlin
// over44.kt
fun main() {
    val xs = listOf(Int.MAX_VALUE, 1)
    println("1 sumOf { it }          = ${xs.sumOf { it }}")
    println("2 sum()                 = ${xs.sum()}")
    println("3 sumOf { it.toLong() } = ${xs.sumOf { it.toLong() }}")
    println("4 fold(0L) { a, x -> a + x } = ${xs.fold(0L) { a, x -> a + x }}")
    println("5 average()             = ${xs.average()}")
    try {
        println("6 fold(0) { a, x -> Math.addExact(a, x) } = ${xs.fold(0) { a, x -> Math.addExact(a, x) }}")
    } catch (e: ArithmeticException) {
        println("6 ${e::class.java.name} | ${e.message}")
    }
}
```

```text
===== kotlinc over44.kt -d o44o =====
(exit 0)
===== java -cp o44o:kotlin-stdlib.jar Over44Kt =====
1 sumOf { it }          = -2147483648
2 sum()                 = -2147483648
3 sumOf { it.toLong() } = 2147483648
4 fold(0L) { a, x -> a + x } = 2147483648
5 average()             = 1.073741824E9
6 java.lang.ArithmeticException | integer overflow
(exit 0)
```

- ★★★ **`[Int.MAX_VALUE, 1].sumOf { it }` 은 `-2147483648`** — 예외도 경고도 없다. `sum()` 도 같다.
- ★★★ **`sumOf { it.toLong() }` 이면 `2147483648`** — 셀렉터가 `Long` 을 돌려주면 **`Long` 판 `sumOf`** 가 골라지고 누산기도 `Long` 이 된다((4)). 초기값이 `0L` 인 `fold` 도 같다(`4`).
- ★★ **넘치면 실패하게 하려면 `Math.addExact`** — `java.lang.ArithmeticException | integer overflow`. Kotlin stdlib 의 `sumOf` 에는 **검사하는 판이 없다**((4)).
- ★ `average()` 는 **`Double` 누산기**라 안 넘친다(`1.073741824E9`)((4)).

### (3) ★★ `fold` 와 `reduce` 의 계약 — stdlib 소스

```text
===== unzip -o -q kotlin-stdlib-sources.jar commonMain/generated/_Collections.kt commonMain/generated/_Maps.kt commonMain/kotlin/collections/Maps.kt commonMain/kotlin/collections/SlidingWindow.kt jvmMain/generated/_CollectionsJvm.kt =====
(exit 0)
```

```text
===== sed -n '3104,3105p;3112,3118p' commonMain/generated/_Collections.kt =====
 * Throws an exception if this collection is empty. If the collection can be empty in an expected way,
 * please use [reduceOrNull] instead. It returns `null` when its receiver is empty.
public inline fun <S, T : S> Iterable<T>.reduce(operation: (acc: S, T) -> S): S {
    val iterator = this.iterator()
    if (!iterator.hasNext()) throw UnsupportedOperationException("Empty collection can't be reduced.")
    var accumulator: S = iterator.next()
    while (iterator.hasNext()) {
        accumulator = operation(accumulator, iterator.next())
    }
(exit 0)
===== sed -n '2128p;2132,2136p' commonMain/generated/_Collections.kt =====
 * Returns the specified [initial] value if the collection is empty.
public inline fun <T, R> Iterable<T>.fold(initial: R, operation: (acc: R, T) -> R): R {
    var accumulator = initial
    for (element in this) accumulator = operation(accumulator, element)
    return accumulator
}
(exit 0)
```

```text
===== sed -n '2295,2298p;2327,2328p;3179,3180p;3295,3296p;3345,3346p' commonMain/generated/_Collections.kt =====
@SinceKotlin("1.7")
@kotlin.jvm.JvmName("maxByOrThrow")
@Suppress("CONFLICTING_OVERLOADS")
public inline fun <T, R : Comparable<R>> Iterable<T>.maxBy(selector: (T) -> R): T {
@SinceKotlin("1.4")
public inline fun <T, R : Comparable<R>> Iterable<T>.maxByOrNull(selector: (T) -> R): T? {
@SinceKotlin("1.4")
public inline fun <S, T : S> Iterable<T>.reduceOrNull(operation: (acc: S, T) -> S): S? {
@SinceKotlin("1.4")
public inline fun <T, R> Iterable<T>.runningFold(initial: R, operation: (acc: R, T) -> R): List<R> {
@SinceKotlin("1.4")
public inline fun <S, T : S> Iterable<T>.runningReduce(operation: (acc: S, T) -> S): List<S> {
(exit 0)
```

- ★★★ **`reduce` 의 빈 입력 예외는 KDoc 이 예고한다** — 「`Throws an exception if this collection is empty. If the collection can be empty in an expected way, please use [reduceOrNull] instead.`」. 구현은 이터레이터가 비었으면 **첫 줄에서** `UnsupportedOperationException("Empty collection can't be reduced.")`.
- ★★★ **`fold` 의 빈 입력 동작도 KDoc 계약이다** — 「`Returns the specified [initial] value if the collection is empty.`」. 구현은 `accumulator = initial` 로 시작해 **원소가 없으면 루프를 한 번도 안 돈다.**
- ★★ KDoc 은 「**예외를 던진다**」까지 약속하고 **어느 클래스인지는 적지 않는다** — `UnsupportedOperationException` 과 그 문장은 **구현**이다. [43번 주제](../43-filter-search-and-empty-collections/)의 `first()`(`NoSuchElementException`)와 **클래스가 다르다**는 것도 눈여겨 둔다.
- ★ 두 서명의 차이가 곧 이 갈림이다 — `fold(initial: R, …)`: **결과 타입 `R` 의 값을 부르는 쪽이 준다.** `reduce(…): S` 는 `T : S` 라 **원소가 곧 시작값**이다.

### (4) ★★ `sumOf`·`sum`·`average` 의 누산기 — stdlib 소스

```text
===== sed -n '3462,3471p;4087,4093p' commonMain/generated/_Collections.kt =====
@SinceKotlin("1.4")
@kotlin.jvm.JvmName("sumOfInt")
@kotlin.internal.InlineOnly
public inline fun <T> Iterable<T>.sumOf(selector: (T) -> Int): Int {
    var sum: Int = 0.toInt()
    for (element in this) {
        sum += selector(element)
    }
    return sum
}
public fun Iterable<Int>.sum(): Int {
    var sum: Int = 0
    for (element in this) {
        sum += element
    }
    return sum
}
(exit 0)
===== sed -n '4007,4015p' commonMain/generated/_Collections.kt =====
public fun Iterable<Int>.average(): Double {
    var sum: Double = 0.0
    var count: Int = 0
    for (element in this) {
        sum += element
        checkCountOverflow(++count)
    }
    return if (count == 0) Double.NaN else sum / count
}
(exit 0)
```

- ★★★ **`sumOf { Int }` 와 `sum()` 은 `var sum: Int` 에 `+=`** 한다 — 넘침 검사가 없으니 [01번 주제](../01-val-var-and-basic-types/)의 「`Int` 오버플로는 감긴다」를 **그대로** 물려받는다.
- ★★ **`average()` 는 `var sum: Double` 과 원소 수를 세고, 끝에 `if (count == 0) Double.NaN else sum / count`** — 빈 입력의 `NaN` 이 **명시적인 한 줄**이다(0으로 나눈 부산물이 아니다).
- ★ `checkCountOverflow(++count)` — **원소 수**는 넘침을 검사한다. 합은 `Double` 이라 검사하지 않는다.

### (5) ★ `groupBy` 와 `partition` 의 결과

```kotlin
// shape44.kt
fun main() {
    val g = listOf(3, 1, 4, 1, 5).groupBy { it % 2 }
    println("1 $g  ${g::class.java.name}  ${g.getValue(1)::class.java.name}")
    val p = listOf(3, 1, 4, 1, 5).partition { it % 2 == 0 }
    println("2 $p  ${p::class.java.name}  first=${p.first}  second=${p.second}")
    val e = emptyList<Int>().groupBy { it % 2 }
    println("3 $e  ${e::class.java.name}  get(0)=${e[0]}")
    val (evens, odds) = emptyList<Int>().partition { it % 2 == 0 }
    println("4 evens=$evens  odds=$odds")
}
```

```text
===== kotlinc shape44.kt -d o44s =====
(exit 0)
===== java -cp o44s:kotlin-stdlib.jar Shape44Kt =====
1 {1=[3, 1, 1, 5], 0=[4]}  java.util.LinkedHashMap  java.util.ArrayList
2 ([4], [3, 1, 1, 5])  kotlin.Pair  first=[4]  second=[3, 1, 1, 5]
3 {}  java.util.LinkedHashMap  get(0)=null
4 evens=[]  odds=[]
(exit 0)
```

- ★★ **`groupBy` 는 `java.util.LinkedHashMap`, 값은 `java.util.ArrayList`** — 키는 **처음 나온 순서**(`3` 이 홀수라 `1` 이 먼저, `4` 가 나중에 `0`). 계약은 `Map<K, List<T>>` 까지다.
- ★★ **`partition` 은 `kotlin.Pair`** — `first` 가 **조건을 만족한 쪽**, `second` 가 나머지. 빈 입력이면 `([], [])` 이고 `val (evens, odds) =` 로 받으면 둘 다 `[]`.
- ★ **빈 `groupBy` 결과에 없는 키를 물으면 `null`** 이다(`get(0)=null`) — 「키 0 의 목록이 빈 리스트」가 **아니다.** `partition` 은 언제나 두 칸이 있지만 `groupBy` 는 **나온 키의 칸만** 있다([Java 48번](../../../java/syntax/48-collectors-grouping/)의 `groupingBy` 대 `partitioningBy` 와 같은 갈림).

### (6) ★ 다른 언어의 같은 자리 — 빈 입력과 넘침

**Rust — `reduce` 는 `Option`, `sum` 의 넘침은 빌드에 달렸다**

```rust
// red44.rs
fn main() {
    let empty: Vec<i32> = Vec::new();
    let many = vec![1, 2, 3, 4];
    eprintln!("1 reduce empty = {:?}", empty.iter().copied().reduce(|a, x| a + x));
    eprintln!("2 reduce many  = {:?}", many.iter().copied().reduce(|a, x| a + x));
    eprintln!("3 fold empty   = {}", empty.iter().fold(0, |a, x| a + x));
    eprintln!("4 sum empty    = {}", empty.iter().sum::<i32>());
    eprintln!("5 max empty    = {:?}", empty.iter().max());
    let big = vec![i32::MAX, 1];
    eprintln!("6 try_fold     = {:?}", big.iter().try_fold(0i32, |a, &x| a.checked_add(x)));
    eprintln!("7 sum of big   = {}", big.iter().sum::<i32>());
}
```

```text
===== rustc --edition 2021 red44.rs -o red44 =====
(exit 0)
===== ./red44 =====
1 reduce empty = None
2 reduce many  = Some(10)
3 fold empty   = 0
4 sum empty    = 0
5 max empty    = None
6 try_fold     = None

thread 'main' (1848735) panicked at /rustc/ded5c06cf21d2b93bffd5d884aa6e96934ee4234/library/core/src/iter/traits/accum.rs:204:1:
attempt to add with overflow
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
(exit 101)
```

```text
===== rustc --edition 2021 -O red44.rs -o red44o =====
(exit 0)
===== ./red44o =====
1 reduce empty = None
2 reduce many  = Some(10)
3 fold empty   = 0
4 sum empty    = 0
5 max empty    = None
6 try_fold     = None
7 sum of big   = -2147483648
(exit 0)
```

**Python — `sum` 은 넘치지 않는다**

```python
// red44.rs
fn main() {
    let empty: Vec<i32> = Vec::new();
    let many = vec![1, 2, 3, 4];
    eprintln!("1 reduce empty = {:?}", empty.iter().copied().reduce(|a, x| a + x));
    eprintln!("2 reduce many  = {:?}", many.iter().copied().reduce(|a, x| a + x));
    eprintln!("3 fold empty   = {}", empty.iter().fold(0, |a, x| a + x));
    eprintln!("4 sum empty    = {}", empty.iter().sum::<i32>());
    eprintln!("5 max empty    = {:?}", empty.iter().max());
    let big = vec![i32::MAX, 1];
    eprintln!("6 try_fold     = {:?}", big.iter().try_fold(0i32, |a, &x| a.checked_add(x)));
    eprintln!("7 sum of big   = {}", big.iter().sum::<i32>());
}
```

```text
===== python3 red44.py =====
1 sum([])          = 0
2 sum([2**31-1, 1]) = 2147483648
3 math.fsum([])     = 0.0
4 max([])          -> ValueError: max() iterable argument is empty
(exit 0)
```

| 자리 | Kotlin | Rust | Python | JS | Java 스트림 |
|---|---|---|---|---|---|
| 초기값 없는 접기 · 빈 입력 | ★ **던진다**(`UnsupportedOperationException`) | `None`(`Option`) | `TypeError`([45번](../../../python/syntax/45-functools/) (6)) | `TypeError`([25번](../../../js/syntax/25-array-non-mutating-and-copy-methods/)) | `Optional.empty`([46번](../../../java/syntax/46-terminal-operations/)) |
| 초기값 있는 접기 · 빈 입력 | 초기값 | 초기값(`fold` → `0`) | 초기값 | 초기값 | 항등원 |
| 정수 합 · 빈 입력 | `0` | `0` | `0` | — | — |
| 정수 합 · 넘침 | ★ **조용히 감긴다** | 최적화 끔 **패닉** · 켬 **감긴다** | 안 넘친다(`2147483648`) | — | — |

- ★★★ **「초기값 없는 접기」는 다섯 언어 모두 빈 입력을 특별 취급한다** — 던지거나(Kotlin·Python·JS) **타입으로 비움을 표시**하거나(Rust `Option` · Java `Optional`). Kotlin 은 **`reduceOrNull`** 로 Rust·Java 쪽 모양을 **따로** 준다.
- ★★ **Rust 의 넘침은 같은 소스인데 빌드가 결과를 바꾼다** — `rustc` 기본(디버그)은 `attempt to add with overflow` 패닉(`exit 101`), `-O` 는 `-2147483648`. Kotlin 은 이 문서의 빌드에서 **감겼다** — Kotlin 쪽 컴파일 옵션을 **바꿔 보지는 않았다.**
- ★ JS·Java 칸의 「—」는 **이 문서가 던지지 않은 칸**이다.

## 문법 — 형태와 규칙

**형태** — 매출 목록에서 합계·가게별 합계·두 갈래·빈 입력.

```kotlin
// form44.kt
data class Sale(val shop: String, val amount: Long)

fun main() {
    val sales = listOf(Sale("a", 300), Sale("b", 200), Sale("a", 500))
    val total: Long = sales.sumOf { it.amount }
    val byShop: Map<String, Long> = sales.groupBy { it.shop }.mapValues { (_, v) -> v.sumOf { it.amount } }
    val (big, small) = sales.partition { it.amount >= 300 }
    val maxOrNull = emptyList<Sale>().maxByOrNull { it.amount }
    val folded = emptyList<Sale>().fold(0L) { acc, s -> acc + s.amount }
    println("total    $total")
    println("byShop   $byShop")
    println("big      ${big.map { it.amount }}  small ${small.map { it.amount }}")
    println("empty    max=$maxOrNull  fold=$folded")
}
```

```text
===== kotlinc form44.kt -d o44z =====
(exit 0)
===== java -cp o44z:kotlin-stdlib.jar Form44Kt =====
total    1000
byShop   {a=800, b=200}
big      [300, 500]  small [200]
empty    max=null  fold=0
(exit 0)
```

**규칙 불릿**

- **빈 입력이 가능하면 `fold`(초기값) 또는 `reduceOrNull`** — `reduce` 는 던진다((1)(3)).
- **합은 `sumOf`** — 금액처럼 넘칠 수 있으면 **`Long` 을 돌려주는 셀렉터**(`it.amount` 가 `Long`)((2)(4)).
- **평균은 빈 입력에서 `NaN`** — 예외를 기대하지 마라((1)(4)).
- **그룹별 합은 `groupBy { }.mapValues { }`** — `byShop` 줄((5)).
- **두 갈래는 `partition`** — `val (big, small) =` 로 받는다((5)).
- **최댓값은 `maxByOrNull`** — 빈 입력이면 `null`((1)).

## 어디서 틀리나

1. ★★★ **`reduce` 로 합계를 내고 빈 입력을 생각 안 한다.** `UnsupportedOperationException` 이다((1)) — 「주문 0건인 날」에 터진다.
2. ★★★ **`sumOf { it }` 의 합이 넘치면 예외가 날 거라고 믿는다.** 조용히 감긴다((2)) — 합계가 **음수**가 되어 나온다.
3. ★★ **`average()` 가 빈 입력에서 던진다고 본다.** `NaN` 이다((1)) — 그 `NaN` 이 화면·DB 까지 흘러간다.
4. ★★ **`fold` 의 초기값을 결과 타입과 다르게 준다.** `fold(0)` 이면 누산기가 `Int` 라 **넘친다** — `fold(0L)` 이어야 `Long`((2)).
5. ★★ **`groupBy` 결과에서 없는 키를 빈 리스트로 기대한다.** `null` 이다((5)) — `getOrElse(k) { emptyList() }`.
6. ★ **`maxBy` 를 옛 뜻(`null` 을 주던 시절)으로 읽는다.** 1.7 부터 던진다 — 빈 입력은 `maxByOrNull`((1) · [43번 주제](../43-filter-search-and-empty-collections/) (4)).
7. ★ **`runningReduce` 도 빈 입력에서 던진다고 본다.** `[]` 다((1)).

## 구현 세부사항 대 언어 보장

| 항목 | 어느 쪽인가 | 근거 |
|---|---|---|
| `fold` 가 빈 입력에서 `initial` | ★★★ **API 계약(KDoc)** | (3) |
| `reduce` 가 빈 입력에서 던진다 | ★★★ **API 계약(KDoc — 「Throws an exception」)** | (3) |
| 그 예외가 `UnsupportedOperationException` · 문장 | ★★ **stdlib 구현** | (3) |
| `average()` 가 빈 입력에서 `NaN` | ★★ **stdlib 구현**(명시적 `if`) — 이 문서는 `average` 의 KDoc 에 그 말이 있는지 **발췌하지 않았다** | (4) |
| `sumOf { Int }` 가 감긴다 | ★★ **언어(`Int` 덧셈) + stdlib 구현(`Int` 누산기)** | (2)(4) · [01번 주제](../01-val-var-and-basic-types/) |
| `groupBy` 가 `LinkedHashMap` · 삽입 순서 | ★ **stdlib 구현**(런타임 클래스) | (5) |
| `partition` 이 `Pair<List, List>` | ★★ **API 계약(서명)** | (5) |
| Rust `sum` 이 디버그에서 패닉 | **rustc 빌드 설정의 관찰** — 이 판에서 두 번 돌렸다 | (6) |

★★ **가장 조심할 자리** — `average()` 의 `NaN` 과 `sumOf` 의 감김은 **둘 다 예외가 없다.** 격자의 「던진 칸」에 안 잡히는 실패가 이 주제의 절반이다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 빈 입력이 가능한 합·곱 | `fold(초기값)` · `sumOf` | (1)(3) |
| 초기값이 없고 빈 입력이 가능 | `reduceOrNull` | (1) — `null` |
| 비면 버그다 | `reduce` | (1)(3) — 던져서 드러낸다 |
| 넘칠 수 있는 합 | `sumOf { it.toLong() }` · `fold(0L)` | (2) |
| 넘치면 실패해야 한다 | `fold(0) { a, x -> Math.addExact(a, x) }` | (2) |
| 누계(prefix sum) | `runningFold(0)` | (1) — 초기값이 첫 원소 |
| 키별 묶음 | `groupBy` | (5) |
| 조건으로 둘 | `partition` | (5) |

## 핵심 문장

1. `fold` 와 `reduce` 는 원소가 있으면 같고 **빈 입력에서만 갈린다** — `fold` 는 초기값, `reduce` 는 **`UnsupportedOperationException("Empty collection can't be reduced.")`**.
2. 집계 12연산의 빈 입력 칸 — **던짐 2 · `null` 2 · `NaN` 1 · 값 7**, 원소가 있는 24칸은 **던짐 0** 이다.
3. **`average()` 는 빈 입력에서 `NaN`** 이다 — 예외가 아니다.
4. **`sumOf { it }` 의 `Int` 합은 조용히 감긴다** — `Long` 을 돌려주는 셀렉터라야 `Long` 누산기가 골라진다.
5. `groupBy` 는 **`LinkedHashMap`**(처음 나온 키 순서), `partition` 은 **`Pair<List, List>`** 다.

## 관련 자료

- [42번 주제](../42-transformations-map-flatmap-associate-zip/) — ★★★ **선행.** `associateBy` 는 키가 겹치면 **덮고**, 여기 `groupBy` 는 **전부 남긴다.**
- [43번 주제](../43-filter-search-and-empty-collections/) — 검색 연산의 빈 입력 · `max()`/`maxBy` 의 판 이력.
- [01번 주제](../01-val-var-and-basic-types/) — `Int` 오버플로는 감긴다.
- [30번 주제](../30-destructuring-declarations-and-componentn/) — `val (a, b) = pair`.
- [Python 45번](../../../python/syntax/45-functools/) (6) — `reduce(add, [])` 는 `TypeError: reduce() of empty iterable with no initial value`.
- [JS 25번](../../../js/syntax/25-array-non-mutating-and-copy-methods/) — `[].reduce(f)` 는 `TypeError 「Reduce of empty array with no initial value」`.
- [Java 46번](../../../java/syntax/46-terminal-operations/) — 스트림 `reduce(BinaryOperator)` 는 `Optional`. [Java 48번](../../../java/syntax/48-collectors-grouping/) — `groupingBy` 대 `partitioningBy`.
- [Rust 36번](../../../rust/syntax/36-iterator-adapters-laziness-and-collect/) — 소비자 `sum`·`fold`.

## 용어 풀이

> **접기(fold)** — 누산기에 원소를 하나씩 더해 **값 하나**로 만드는 것. `fold` 는 부르는 쪽이 **초기값**을 준다.\
> 예: `listOf(1, 2, 3).fold(0) { a, x -> a + x }` → `6`.

> **`reduce`** — 초기값 없이 **첫 원소를 누산기로** 시작하는 접기. 빈 입력에서는 시작할 것이 없어 던진다.

> **누산기(accumulator)** — 접는 동안 중간 결과를 담는 변수. 그 **타입**이 넘침을 정한다(`Int` 면 감긴다).

> **`NaN`(Not a Number)** — `Double` 의 「숫자가 아님」 값. `NaN == NaN` 도 `false` 라 `isNaN()` 으로 확인한다.

> **감김(wrap-around)** — 정수가 최댓값을 넘으면 **최솟값 쪽으로 돌아가는** 것. `Int.MAX_VALUE + 1` → `-2147483648`.

> **`runningFold`** — `fold` 의 **중간 결과를 전부** 리스트로 남긴다. 누계(prefix sum)다.

## 더 들어가면

- **`groupingBy { }.eachCount()`·`fold`** — 중간 리스트 없이 그룹별로 접는 `Grouping` API 는 **던지지 않았다.**
- **`sumOf` 의 `Double`·`BigDecimal` 판** — 이 문서는 `Int`·`Long` 만 봤다.
- **Kotlin 쪽 넘침 검사 옵션** — Kotlin 에 Rust 의 디버그 넘침 검사 같은 컴파일 옵션이 있는지 **찾아보지 않았다.** 바이트코드(`javap`)도 **찍지 않았다.**
