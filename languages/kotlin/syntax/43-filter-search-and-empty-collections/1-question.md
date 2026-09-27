# kotlin/syntax/43 — 필터·검색 — `filter`/`find`/`first`/`any`/`all`/`none` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [41번 주제](../41-collection-creation-and-copying/)(`emptyList()` 는 싱글턴 `EmptyList`)다.
> 문항 10개 중 예측형은 5개이고, 그중 코드블록이 붙는 것은 3개다.
> 이 주제의 모든 답은 **kotlinc 2.4.20 · Temurin JDK 21.0.5** 에서 실제로 던져 받은 것이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 검색 연산 격자 — 네 가지 입력 (예측)

```kotlin
// empty43.kt
import kotlin.random.Random

val inputs = listOf(
    "empty" to listOf<Int>(),
    "one" to listOf(7),
    "no-match" to listOf(1, 2),
    "two-match" to listOf(6, 8),
)

val ops: List<Pair<String, (List<Int>) -> Any?>> = listOf(
    "first()" to { xs -> xs.first() },
    "first{}" to { xs -> xs.first { it > 5 } },
    "firstOrNull()" to { xs -> xs.firstOrNull() },
    "last()" to { xs -> xs.last() },
    "single()" to { xs -> xs.single() },
    "single{}" to { xs -> xs.single { it > 5 } },
    "singleOrNull()" to { xs -> xs.singleOrNull() },
    "find{}" to { xs -> xs.find { it > 5 } },
    "any()" to { xs -> xs.any() },
    "any{}" to { xs -> xs.any { it > 5 } },
    "all{}" to { xs -> xs.all { it > 5 } },
    "none{}" to { xs -> xs.none { it > 5 } },
    "filter{}" to { xs -> xs.filter { it > 5 } },
    "elementAt(0)" to { xs -> xs.elementAt(0) },
    "max()" to { xs -> xs.max() },
    "maxOrNull()" to { xs -> xs.maxOrNull() },
    "random(seed)" to { xs -> xs.random(Random(42)) },
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

- 술어는 `it > 5`, 입력은 `[]` · `[7]` · `[1, 2]` · `[6, 8]` 이다. 각 칸은 값(`= …`)인가, 예외(`! 클래스: 메시지`)인가? 예외라면 **클래스**는 무엇인가?

### 2. ★★★ `all{}` · `any{}` · `none{}` 의 빈 입력 칸 (예측)

- 1번에서 세 연산의 `empty` 칸은 각각 무엇인가? 세 칸 중 **같은 값**을 내는 둘은?

### 3. ★★ `single()` 의 네 칸 (예측)

- 1번에서 `single()` 과 `singleOrNull()` 의 `no-match`·`two-match` 칸은 각각 무엇인가? `single()` 이 던진다면 빈 입력과 **같은 클래스**인가?

### 4. ★★ 받는 쪽만 바꾼 아홉 줄 (예측)

```kotlin
// msg43.kt
fun probe(label: String, f: () -> Any?) {
    val r = try {
        "= " + f()
    } catch (e: Exception) {
        "! " + e::class.java.name + " | " + e.message
    }
    println("$label  $r")
}

fun main() {
    val ro: List<Int> = listOf()
    val ml: List<Int> = mutableListOf()
    val st: Set<Int> = setOf()
    val sq: Sequence<Int> = emptySequence()
    probe("1 listOf().first()       ") { ro.first() }
    probe("2 mutableListOf().first()") { ml.first() }
    probe("3 setOf().first()        ") { st.first() }
    probe("4 emptySequence().first()") { sq.first() }
    probe("5 listOf().elementAt(0)       ") { ro.elementAt(0) }
    probe("6 mutableListOf().elementAt(0)") { ml.elementAt(0) }
    probe("7 setOf().elementAt(0)        ") { st.elementAt(0) }
    probe("8 listOf()[0]                 ") { ro[0] }
    probe("9 mutableListOf()[0]          ") { ml[0] }
}
```

- 돌리면 `1`\~`9` 줄의 예외 **클래스**와 **메시지**는 각각 무엇인가? 줄마다 달라지는 것은 어느 쪽인가?

### 5. ★ `max()` 를 부르면 무엇이 불리나 (예측)

```kotlin
// mx43.kt
fun main() {
    println(listOf(3, 1, 2).max())
}
```

- 이 호출은 JVM 바이트코드에서 `CollectionsKt` 의 **어떤 이름**을 부르는가? 빈 리스트였다면 무엇이 나오나?

### 6. `all{}` 의 빈 입력 칸은 계약인가 (왜)

- 2번의 답은 stdlib 의 **KDoc** 이 약속하는 것인가, 구현이 우연히 그런 것인가? 그 논리의 이름은?

### 7. `singleOrNull()` 의 `null` (경계)

- `singleOrNull()` 이 `null` 을 돌려줬을 때, 그것만으로 「원소가 없었다」고 말할 수 있는가?

### 8. 예외 메시지로 분기하기 (경계)

- 4번을 근거로, `catch (e: NoSuchElementException)` 대신 `e.message == "List is empty."` 로 분기하면 어디서 깨지나?

### 9. `max()` 의 옛 판 (연결)

- 5번의 `max()` 는 1.4 이전에는 빈 입력에서 무엇을 돌려줬나? 1.4\~1.6 에는 무슨 일이 있었나 — 이 문서는 그것을 **어떻게** 확인했고, 무엇을 확인하지 못했나?

### 10. Java 스트림의 `findFirst` 와 (연결)

- [Java 46번](../../../java/syntax/46-terminal-operations/)의 `findFirst()`·`max()` 는 빈 스트림에서 무엇을 돌려주나? Kotlin 의 어느 쪽(`first()` 인가 `firstOrNull()` 인가)과 같은 자리인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
