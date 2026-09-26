# kotlin/syntax/45 — 정렬·부분 연산 — `sortedBy`/`take`/`drop`/`chunked`/`windowed` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [41번 주제](../41-collection-creation-and-copying/)(만드는 꼴과 복사)다. [40번 주제](../40-read-only-collections-and-runtime-types/)의 `sorted` 대 `sort` 한 쌍을 넓힌다.
> 문항 10개 중 예측형은 5개이고, 그중 코드블록이 붙는 것은 4개다.
> 이 주제의 모든 답은 **kotlinc 2.4.20 · Temurin JDK 21.0.5** 에서 실제로 던져 받은 것이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 정렬 연산 × 받는 쪽 — 서명 (예측)

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

- 각 줄에서 컴파일러가 적는 결과 타입은 무엇인가? 그런 연산이 **없는** 칸은 어디인가?

### 2. ★★★ 원본은 어떻게 되나 (예측)

- 1번에서 **컴파일되는 칸마다** 새 `[3, 1, 2]` 를 만들어 그 연산을 부르면, 원본은 각각 어떻게 되나(`Random(7)` 칸은 순서만 바뀌었는지)? 원본이 바뀌는 칸은 1번의 어떤 결과 타입과 짝이 되나?

### 3. ★★ 키가 겹치는 다섯 행 (예측)

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

- 돌리면 `1`\~`5` 줄은 각각 무엇인가? `2` 와 `3` 은 같은가?

### 4. ★★★ 일곱 개를 자르고 훑기 (예측)

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

- 돌리면 `1`\~`21` 줄은 각각 무엇인가? 특히 `4`·`12`·`13`·`15`·`16`·`18`·`20` 은?

### 5. ★ 우선순위 목록 (예측)

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

- `ordered`·`work`·`tasks` 세 줄은 각각 무엇인가?

### 6. 이름으로 가르는 규칙의 근거 (왜)

- 1번과 2번을 합치면 「원본이 바뀌나」를 **이름 말고 무엇으로** 확인할 수 있나? 그 근거는 서명인가, 관례인가?

### 7. `sortedBy` 가 같은 키를 다루는 방식은 누가 정하나 (경계)

- 3번의 `1` 줄에서 키가 같은 원소들의 순서는 stdlib 가 **약속**하는 것인가? 근거는 어디에 있나?

### 8. `chunked(3)` 과 `windowed(3, step = 3)` (경계)

- 4번에서 두 호출의 결과는 같은가? stdlib 소스에서 `chunked` 는 무엇으로 구현돼 있나?

### 9. 슬라이딩 윈도우 알고리즘과 `windowed` (연결)

- [`cs/algorithm/09-sliding-window/`](../../../../../algorithm/09-sliding-window/)의 기법과 stdlib `windowed` 는 무엇이 같고 무엇이 다른가? 이 문서는 그 차이 중 무엇을 **재지 않았나**?

### 10. 「`sortBy` 가 `sortedBy` 보다 싸다」 (왜)

- 제자리 정렬은 새 리스트를 안 만든다. 이것으로 **「`sortBy` 가 `sortedBy` 보다 싸다」** 를 말할 수 있는가? JS 의 `sort` 대 `toSorted`([JS 25번](../../../js/syntax/25-array-non-mutating-and-copy-methods/))에서도 같은 질문이 선다 — 무엇을 재야 하나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
