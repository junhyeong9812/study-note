# kotlin/syntax/44 — 집계·그룹핑 — `groupBy`/`partition`/`fold`/`reduce`/`sumOf` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [42번 주제](../42-transformations-map-flatmap-associate-zip/)(`associateBy` 는 키가 겹치면 덮는다)다.
> 문항 10개 중 예측형은 5개이고, 그중 코드블록이 붙는 것은 4개다.
> 이 주제의 모든 답은 **kotlinc 2.4.20 · Temurin JDK 21.0.5**(대비 **rustc 1.92.0 · Python 3.12.3**)에서 실제로 던져 받은 것이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 집계 연산 격자 — 빈 · 하나 · 여럿 (예측)

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

- 입력은 `[]` · `[5]` · `[1, 2, 3, 4]` 이다. 각 칸은 값(`= …`)인가, 예외(`! 클래스: 메시지`)인가? `empty` 열에서 값·`null`·`NaN`·예외는 각각 몇 칸인가?

### 2. ★★★ 두 원소의 합 (예측)

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

- 돌리면 `1`\~`6` 줄은 각각 무엇인가? `1` 과 `3` 은 같은 값인가?

### 3. ★★ 홀짝으로 묶고 가르기 (예측)

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

- 네 줄은 각각 무엇인가? `1` 의 키 순서와 두 런타임 클래스, `3` 의 `get(0)` 은?

### 4. ★★ Rust 의 같은 자리 (예측)

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

- `rustc --edition 2021 red44.rs` 로 만든 것과 `-O` 를 붙여 만든 것을 각각 돌리면 `7` 줄(과 종료 코드)은 각각 무엇인가? `1` 과 `4` 는?

### 5. ★ 누계 두 가지 (예측)

- 1번에서 `runningFold(0){+}` 과 `runningReduce{+}` 의 `empty`·`one` 칸은 각각 무엇인가?

### 6. `fold` 와 `reduce` 가 갈리는 자리 (왜)

- 1번에서 두 연산은 `one`·`many` 칸이 같다. **빈 입력에서만** 갈리는 이유를 두 함수의 **서명**으로 설명하면?

### 7. `reduce` 의 KDoc 이 약속하는 것 (경계)

- `reduce` 가 빈 입력에서 하는 일은 KDoc 이 약속하는가? 예외라면 **클래스와 문장**까지 약속하는가?

### 8. `average()` 의 빈 입력 (경계)

- 1번의 `average()` 빈 칸은 무엇이고, 그것은 「0으로 나눈 부산물」인가, stdlib 가 **일부러** 고른 것인가?

### 9. 다섯 언어의 「초기값 없는 접기」 (연결)

- Kotlin `reduce` · Rust `Iterator::reduce` · Python `functools.reduce` · JS `Array.prototype.reduce` · Java 스트림 `reduce(BinaryOperator)` 는 빈 입력에서 각각 무엇을 하나? Kotlin 에서 Rust·Java 쪽 모양을 내는 함수는?

### 10. 「`sumOf` 가 `fold` 보다 빠르다」 (왜)

- stdlib 소스에서 `sumOf { Int }` 는 `for` 루프 하나다. 이것으로 **「`sumOf` 가 `fold` 보다 빠르다」** 를 말할 수 있는가? 무엇을 재야 하나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
