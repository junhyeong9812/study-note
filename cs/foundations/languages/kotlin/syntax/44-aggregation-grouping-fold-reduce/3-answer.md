# kotlin/syntax/44 — 집계·그룹핑 — `groupBy`/`partition`/`fold`/`reduce`/`sumOf` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `java`, 대비는 **rustc 1.92.0** · **Python 3.12.3** 에서 실제로 얻었다.
> ★★ 아래 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적은 자리가 없다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 빈 입력 12칸 — **값 7 · `null` 2 · `NaN` 1 · 예외 2**(`reduce{+}` 와 `maxBy{it}`) · 원소가 있는 24칸은 **한 칸도 안 던졌다**

**출력**

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

**왜 그런가**

- ★★★ `reduce{+}` 는 **`UnsupportedOperationException: Empty collection can't be reduced.`**, `maxBy{it}` 는 **`NoSuchElementException`**(메시지 `null`)이다 — **두 예외의 클래스가 다르다.**
- ★★★ `fold(0){+}` 은 빈 입력에서 **`0`**(초기값), `average()` 는 **`NaN`** — 둘 다 예외가 아니다.
- ★★ `null` 두 칸은 `reduceOrNull{+}` 과 `maxByOrNull{it}` — 이름의 `OrNull` 이 약속한다.
- ★ 값 7칸 — `0` 셋(`fold`·`sumOf`·`sum`) · `{}` · `([], [])` · `[0]` · `[]`.

### 2. ★★★ **`1` 과 `2` 는 `-2147483648`**(감겼다) · **`3` 과 `4` 는 `2147483648`** · `5` 는 `1.073741824E9` · `6` 은 **`java.lang.ArithmeticException | integer overflow`** — `1` 과 `3` 은 **다르다**

**출력**

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

**왜 그런가**

- ★★★ `sumOf { it }` 은 셀렉터가 `Int` 를 돌려주므로 **`Int` 판 `sumOf`** 가 골라진다 — 누산기가 `var sum: Int` 라 `Int.MAX_VALUE + 1` 이 **감긴다**(2-summary (4)).
- ★★ `sumOf { it.toLong() }` 은 **`Long` 판**이 골라져 누산기가 `Long` 이다. `fold(0L)` 도 초기값이 `Long` 이라 같다.
- ★ `Math.addExact` 는 넘치면 **던지는** JDK 덧셈이다 — 넘침을 **실패로** 만들고 싶을 때 쓴다.

### 3. ★★ `1 {1=[3, 1, 1, 5], 0=[4]}  java.util.LinkedHashMap  java.util.ArrayList` · `2 ([4], [3, 1, 1, 5])  kotlin.Pair …` · `3 {}  java.util.LinkedHashMap  get(0)=null` · `4 evens=[]  odds=[]`

**출력**

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

**왜 그런가**

- ★★ `groupBy` 의 키 순서는 **처음 나온 순서**다 — 첫 원소 `3` 이 홀수라 `1` 이 먼저, `4` 에서 `0` 이 생긴다. 실체가 `LinkedHashMap` 이라 삽입 순서를 지킨다.
- ★★ `partition` 의 `first` 는 **조건을 만족한 쪽**(`[4]`), `second` 는 나머지다.
- ★ 빈 `groupBy` 결과에 `0` 을 물으면 **`null`** — 칸이 **아예 없다.** `partition` 은 빈 입력에서도 두 칸(`[]`·`[]`)이 있다.

### 4. ★★ `7` 줄 — 기본 빌드는 **`attempt to add with overflow` 패닉(`exit 101`, `7` 줄이 안 찍힌다)** · `-O` 는 **`7 sum of big   = -2147483648`** · `1` 은 두 판 다 **`None`**, `4` 는 **`0`**

**출력**

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

**왜 그런가**

- ★★★ Rust `Iterator::reduce` 는 **`Option`** 을 돌려준다 — 빈 입력은 `None`. **타입으로 「없을 수 있음」을 적는다**(Kotlin 의 `reduceOrNull` 자리).
- ★★ `sum` 의 넘침은 **빌드가 결정한다** — 이 판의 `rustc` 기본(최적화 끔)은 넘침 검사가 켜져 **패닉**, `-O` 는 감긴다. **같은 소스**다.
- ★ `try_fold` + `checked_add` 는 넘치면 **`None`** 이다(`6`) — Kotlin 의 `Math.addExact`(2번 `6`)와 같은 역할을 **예외 대신 값**으로 한다.

### 5. `runningFold(0){+}` — `empty` **`[0]`** · `one` **`[0, 5]`** · `runningReduce{+}` — `empty` **`[]`** · `one` **`[5]`**

**출력** — 1번 격자의 `runningFold(0){+}`·`runningReduce{+}` 행.

**왜 그런가**

- ★★ `runningFold` 는 **초기값을 첫 원소로** 싣는다 — 원소가 없어도 초기값 하나는 있다.
- ★★ `runningReduce` 는 `reduce` 와 달리 **안 던진다** — 결과가 리스트라 「없음」을 `[]` 로 쓸 수 있다.

### 6. **`fold(initial: R, …)` 는 시작값을 부르는 쪽이 준다** · **`reduce(…): S` 는 첫 원소가 시작값**이다 — 원소가 없으면 `reduce` 만 시작할 것이 없다

**왜 그런가**

- ★★★ 2-summary (3)의 발췌 — `fold` 는 `var accumulator = initial` 로 시작하고, `reduce` 는 `var accumulator: S = iterator.next()` 로 시작한다. 그 **한 줄 앞**에서 `reduce` 는 `hasNext()` 를 보고 던진다.
- ★ 원소가 하나 이상이면 `fold(0)` 의 첫 걸음 `0 + x` 가 `x` 와 같으니 두 결과가 같다 — **덧셈의 항등원이 `0`** 이기 때문이다. 항등원이 아닌 초기값(`fold(100)`)이면 원소가 있어도 달라진다(이 문서는 **던지지 않았다**).

### 7. **「던진다」까지는 KDoc 계약** — 「`Throws an exception if this collection is empty.`」 · **클래스와 문장은 약속하지 않는다**(구현)

**왜 그런가**

- ★★ 2-summary (3)의 발췌 — KDoc 은 「예외를 던진다 · 비어 있을 수 있으면 `reduceOrNull`」까지 적고, 클래스 이름은 **구현 한 줄**(`throw UnsupportedOperationException("Empty collection can't be reduced.")`)에만 있다.
- ★ 그래서 `catch (e: UnsupportedOperationException)` 에 기대기보다 **`reduceOrNull`** 로 바꾸는 쪽이 계약에 맞다.

### 8. **`NaN`** — 0으로 나눈 부산물이 **아니다** · stdlib 가 `if (count == 0) Double.NaN else sum / count` 로 **일부러** 고른다

**왜 그런가**

- ★★ 2-summary (4)의 발췌 — 빈 입력은 나눗셈까지 **가지도 않는다.** `NaN` 은 명시적 분기의 결과다.
- ★ 이 문서는 `average()` 의 KDoc 이 그 동작을 **약속하는지는 발췌하지 않았다** — 「구현의 명시적 선택」까지다.

### 9. Kotlin **던짐**(`UnsupportedOperationException`) · Rust **`None`** · Python **`TypeError`** · JS **`TypeError`** · Java **`Optional.empty`** — Kotlin 에서 Rust·Java 모양은 **`reduceOrNull`**

**왜 그런가**

- ★★ Kotlin·Rust 는 이 문서가 돌렸다(1번 · 4번). Python 은 [45번](../../../python/syntax/45-functools/) (6)이 `TypeError: reduce() of empty iterable with no initial value`, JS 는 [25번](../../../js/syntax/25-array-non-mutating-and-copy-methods/)이 `TypeError 「Reduce of empty array with no initial value」`, Java 는 [46번](../../../java/syntax/46-terminal-operations/)이 `Optional` 을 실측했다 — **다시 돌리지 않았다.**
- ★ 다섯 다 「초기값 없는 접기의 빈 입력」을 **특별 취급**한다. 갈리는 것은 **던지느냐(Kotlin·Python·JS) 타입으로 적느냐(Rust·Java)** 다.

### 10. **말할 수 없다** — 소스는 「`sumOf` 가 무엇을 하나」를 말할 뿐이다 · 빠르다고 하려면 **같은 입력에서 둘의 시간을 반복 측정**해야 한다

**왜 그런가**

- ★★ `sumOf` 는 `inline` 이고 `fold` 도 `inline` 이다(2-summary (3)(4)의 서명) — 둘 다 호출 자리에 **루프로 펼쳐질** 것으로 보이지만, 그 바이트코드도 시간도 이 문서는 **재지 않았다.**
- ★ 두 함수의 차이로 확인된 것은 **누산기 타입이 어떻게 정해지나**(2번)뿐이다.

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
===== rustc --version =====
rustc 1.92.0 (ded5c06cf 2025-12-08)
(exit 0)
```

```text
===== python3 --version =====
Python 3.12.3
(exit 0)
```

★ **흔들리는 칸과 안 흔들리는 칸**

| 흔들린다 | 안 흔들린다 |
|---|---|
| Rust 패닉 첫 줄의 **스레드 id** | 격자 12행 × 3열 · 마지막 줄의 칸 수 · 오버플로 값 · `groupBy` 키 순서 |
| | 패닉의 메시지·위치(`accum.rs:204:1`) · stdlib 소스 발췌 |
| | 모든 **종료 코드**(`101` 포함) |

> 근거 — 캡처 스크립트를 처음부터 다시 돌려 **블록 전체를 대조**했다.
>
> 실측 — `capture.sh blocks` 와 `capture.sh blocks-recheck` 를 처음부터 따로 돌려 `normalize-shaky.py` 로 대조했다 —\
> **블록 60개 · 동일 59 · 흔들린 칸 1 · ★고칠 것 0**(42\~45 네 주제를 한 캡처로 받았다). 흔들린 1블록은 44번의 Rust 패닉 블록(`a44-rs`)이고, 원문 차이는 **패닉 첫 줄의 스레드 id** 하나였다 — 기본 정규화 규칙(스레드 id)이 그것을 지웠다.\
> ★ 추가한 정규화 규칙은 **없다**.

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `agg44.kt` · `grid44.py` | ★★★ 빈 입력 갈림 격자 — 12연산 × 3입력 | `kotlinc` → 스크립트가 `java` |
| `over44.kt` | ★★ `sumOf` 오버플로 · `Long` 셀렉터 · `Math.addExact` | `kotlinc` → `java` |
| `shape44.kt` | `groupBy`·`partition` 의 런타임 클래스 · 빈 입력 | `kotlinc` → `java` |
| `_Collections.kt`(stdlib 소스 jar) | `reduce`·`fold` KDoc 과 구현 · `@SinceKotlin` 다섯 · `sumOf`·`sum`·`average` 누산기 | `unzip` → `sed -n` |
| `red44.rs` | Rust `reduce`·`fold`·`sum` · 넘침 — 최적화 끔/켬 | `rustc` → 실행 · `rustc -O` → 실행 |
| `red44.py` | Python `sum`·`math.fsum`·`max` 의 빈 입력 · 넘침 없음 | `python3` |
| `form44.kt` | 형태 한 벌 | `kotlinc` → `java` |

**구현 의존 항목** — `reduce` 의 예외 **클래스와 문장** · `average()` 의 `NaN` 분기 · `sumOf { Int }` 의 `Int` 누산기 · `groupBy` 의 `LinkedHashMap` — 이 stdlib 판의 산출물이다. Rust 의 패닉/감김은 **rustc 빌드 설정**이다.\
반면 **`fold` 의 초기값 반환** · **`reduce` 가 빈 입력에서 던진다** 는 **KDoc 계약**, `Int` 덧셈이 감기는 것은 **언어 규칙**이다.

**★ 던져 봤더니 예상과 달랐던 것 — 세 건**

1. ★★ **`maxBy` 의 빈 입력 예외는 `reduce` 와 클래스가 달랐다** — `NoSuchElementException`(메시지 `null`) 대 `UnsupportedOperationException`. 「빈 입력 예외」가 한 종류가 아니다(1번).
2. ★★ **`runningReduce` 는 빈 입력에서 안 던졌다** — `reduce` 의 이름을 달고도 `[]` 다(5번).
3. ★ **Rust `sum` 은 같은 소스가 빌드에 따라 패닉하기도 감기기도 했다** — Kotlin 은 한 빌드에서 감겼다(4번).
