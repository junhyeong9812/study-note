# kotlin/syntax/42 — 변환 연산 — `map`/`flatMap`/`associate`/`zip` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [41번 주제](../41-collection-creation-and-copying/)(만드는 꼴마다 복사가 일어나는 자리)다.
> 문항 10개 중 예측형은 5개이고, 그중 코드블록이 붙는 것은 3개다.
> 이 주제의 모든 답은 **kotlinc 2.4.20 · Temurin JDK 21.0.5** 에서 실제로 던져 받은 것이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 변환 연산 격자 — 컴파일러가 적는 타입 (예측)

```kotlin
// type42.kt
fun t(x: Nothing?) {}

fun main() {
    val l: List<Int> = listOf(1, 2, 3)
    val s: Set<Int> = setOf(1, 2, 3)
    val m: Map<String, Int> = mapOf("a" to 1, "b" to 2)
    val q: Sequence<Int> = sequenceOf(1, 2, 3)
    val a: Array<Int> = arrayOf(1, 2, 3)

    t(l.map { it })                              // map List
    t(s.map { it })                              // map Set
    t(m.map { it.value })                        // map Map
    t(q.map { it })                              // map Sequence
    t(a.map { it })                              // map Array

    t(l.mapNotNull { it })                       // mapNotNull List
    t(s.mapNotNull { it })                       // mapNotNull Set
    t(m.mapNotNull { it.value })                 // mapNotNull Map
    t(q.mapNotNull { it })                       // mapNotNull Sequence
    t(a.mapNotNull { it })                       // mapNotNull Array

    t(l.flatMap { listOf(it) })                  // flatMap List
    t(s.flatMap { listOf(it) })                  // flatMap Set
    t(m.flatMap { listOf(it.value) })            // flatMap Map
    t(q.flatMap { listOf(it) })                  // flatMap Sequence
    t(a.flatMap { listOf(it) })                  // flatMap Array

    t(l.flatMap { sequenceOf(it) })              // flatMap{seq} List
    t(s.flatMap { sequenceOf(it) })              // flatMap{seq} Set
    t(m.flatMap { sequenceOf(it.value) })        // flatMap{seq} Map
    t(q.flatMap { sequenceOf(it) })              // flatMap{seq} Sequence
    t(a.flatMap { sequenceOf(it) })              // flatMap{seq} Array

    t(listOf(l, l).flatten())                    // flatten List
    t(setOf(s, s).flatten())                     // flatten Set
    t(mapOf("a" to l).flatten())                 // flatten Map
    t(sequenceOf(q, q).flatten())                // flatten Sequence
    t(arrayOf(a, a).flatten())                   // flatten Array

    t(l.associate { it to it })                  // associate List
    t(s.associate { it to it })                  // associate Set
    t(m.associate { it.value to it.key })        // associate Map
    t(q.associate { it to it })                  // associate Sequence
    t(a.associate { it to it })                  // associate Array

    t(l.associateBy { it })                      // associateBy List
    t(s.associateBy { it })                      // associateBy Set
    t(m.associateBy { it.value })                // associateBy Map
    t(q.associateBy { it })                      // associateBy Sequence
    t(a.associateBy { it })                      // associateBy Array

    t(l.associateWith { it })                    // associateWith List
    t(s.associateWith { it })                    // associateWith Set
    t(m.associateWith { it.value })              // associateWith Map
    t(q.associateWith { it })                    // associateWith Sequence
    t(a.associateWith { it })                    // associateWith Array

    t(l.zip(l))                                  // zip List
    t(s.zip(s))                                  // zip Set
    t(m.zip(m))                                  // zip Map
    t(q.zip(q))                                  // zip Sequence
    t(a.zip(a))                                  // zip Array

    t(l.map { it to "x" }.unzip())               // unzip List
    t(s.map { it to "x" }.toSet().unzip())       // unzip Set
    t(mapOf(1 to "x").unzip())                   // unzip Map
    t(q.map { it to "x" }.unzip())               // unzip Sequence
    t(a.map { it to "x" }.toTypedArray().unzip()) // unzip Array

    t(l.withIndex())                             // withIndex List
    t(s.withIndex())                             // withIndex Set
    t(m.withIndex())                             // withIndex Map
    t(q.withIndex())                             // withIndex Sequence
    t(a.withIndex())                             // withIndex Array

    t(l.mapIndexed { i, v -> i + v })            // mapIndexed List
    t(s.mapIndexed { i, v -> i + v })            // mapIndexed Set
    t(m.mapIndexed { i, e -> i + e.value })      // mapIndexed Map
    t(q.mapIndexed { i, v -> i + v })            // mapIndexed Sequence
    t(a.mapIndexed { i, v -> i + v })            // mapIndexed Array

    t(l.mapValues { it })                        // mapValues List
    t(s.mapValues { it })                        // mapValues Set
    t(m.mapValues { it.value })                  // mapValues Map
    t(q.mapValues { it })                        // mapValues Sequence
    t(a.mapValues { it })                        // mapValues Array
}
```

- `fun t(x: Nothing?)` 에 변환 결과를 넘겨 컴파일하면 줄마다 진단이 난다. 각 칸에서 컴파일러가 적는 **실제 타입**은 무엇인가? 그런 연산이 **없는** 칸은 어디인가?

### 2. ★★ 입력 모양을 지키는 칸 (예측)

- 1번 격자에서 결과의 바깥 그릇(`List`·`Set`·`Map`·`Sequence`·`Pair`·`Iterable`)이 **입력과 같은** 칸은 어느 열의 어느 연산인가? `Sequence` 열에서 `Sequence` 가 **아닌** 결과는?

### 3. ★★★ 세트 · 번호표 · 지퍼 · 맵 (예측)

```kotlin
// shape42.kt
fun main() {
    val s = setOf(1, 2, 3, 4)
    val parity = s.map { it % 2 }
    println("1 $parity  size ${parity.size}")
    println("2 ${s.mapTo(mutableSetOf()) { it % 2 }}")

    val words = listOf("apple", "avocado", "banana", "blueberry", "cherry")
    val byFirst = words.associateBy { w -> w.first().also { println("   key ${it} <- $w") } }
    println("3 $byFirst  size ${words.size} -> ${byFirst.size}")
    println("4 ${words.groupBy { it.first() }}")

    println("5 ${listOf(1, 2, 3).zip(listOf("a", "b"))}")
    println("6 ${listOf(1, 2).zip(listOf("a", "b", "c")) { n, t -> "$t$n" }}")

    val prices = mapOf("tea" to 3, "cake" to 5)
    val m1 = prices.map { (k, v) -> "$k=${v * 2}" }
    val m2 = prices.mapValues { (_, v) -> v * 2 }
    println("7 $m1  ${m1::class.java.name}")
    println("8 $m2  ${m2::class.java.name}")

    val fs = listOf(1, 2).flatMap { n -> sequenceOf(n, n * 10) }
    println("9 $fs  ${fs::class.java.name}")
}
```

- 돌리면 `1`\~`9` 줄(과 그 사이의 `key` 로그)은 각각 무엇인가? 특히 `1` 의 크기와 `3` 의 맵은?

### 4. ★ 주문 목록 (예측)

```kotlin
// form42.kt
data class Order(val id: Int, val user: String, val items: List<String>)

fun main() {
    val orders = listOf(
        Order(1, "kim", listOf("tea", "cake")),
        Order(2, "lee", listOf("tea")),
        Order(3, "kim", listOf("coffee")),
    )
    val ids: List<Int> = orders.map { it.id }
    val allItems: List<String> = orders.flatMap { it.items }
    val byId: Map<Int, Order> = orders.associateBy { it.id }
    val lastByUser: Map<String, Order> = orders.associateBy { it.user }
    val labeled: List<Pair<Int, String>> = ids.zip(listOf("a", "b", "c"))
    println("ids      $ids")
    println("items    $allItems")
    println("byId     ${byId.keys}")
    println("byUser   ${lastByUser.mapValues { it.value.id }}")
    println("labeled  $labeled")
}
```

- `byUser` 줄은 무엇인가? `kim` 의 값은 몇 번 주문의 id 인가?

### 5. ★ `Map` 에서 없는 연산 (예측)

- 1번에서 `Map` 열에 **있는** 연산은 몇 개이고 무엇인가? 없는 칸의 진단은 어떤 모양인가?

### 6. `Set.map` 의 결과 그릇은 누가 정하나 (왜)

- stdlib 에서 `map` 의 서명은 무엇이고, 그 서명이 `Set` 입력의 결과를 어떻게 정하나?

### 7. `associateBy` 의 키 충돌 동작은 누가 정하나 (경계)

- 3번의 `3` 줄이 보인 결과는 stdlib 의 **계약**인가, 구현이 우연히 그런 것인가? 근거는 어디에 있나?

### 8. Java `Collectors.toMap` 과 (연결)

- [Java 47번](../../../java/syntax/47-collectors-basics/)의 `toMap` 은 키가 겹치면 어떻게 하나? Java 코드를 `associateBy` 로 옮기면 무엇을 잃나?

### 9. 결과 타입을 실행으로 찍으면 (왜)

- 1번 격자를 `println(x::class)` 같은 **실행**으로 만들지 않고 컴파일 에러로 만든 이유는 무엇인가? 이 창이 **못 보는** 것은?

### 10. 「`Sequence` 로 바꾸면 빠르다」 (왜)

- 1번 격자의 `Sequence` 열로 **「`Sequence` 로 바꾸면 빠르다」** 를 말할 수 있는가? 무엇이 더 필요하나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
