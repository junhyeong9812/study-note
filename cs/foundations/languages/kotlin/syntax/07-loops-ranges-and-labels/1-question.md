# kotlin/syntax/07 — 반복문·`range`·progression·라벨·비지역 `break`/`continue` (2.2+) — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [01번 주제](../01-val-var-and-basic-types/)와 [06번 주제](../06-when-expression/)다.
> 비지역 `return` 의 **원리**는 [목록의 **11번 주제**](../11-inline-functions/)가 정본이다 — 여기서는 현상까지만 묻는다.
> Java 쪽 짝은 [`../../../java/syntax/20-control-flow-statements/`](../../../java/syntax/20-control-flow-statements/)다.
> 문항 11개 중 코드블록이 붙는 예측형은 6개다.
> 바이트코드를 묻는 문항은 **`kotlinc` 기본 `-jvm-target`(1.8)** 기준이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ 이 루프는 몇 개의 객체를 만드는가 (예측)

```kotlin
fun literal(): Int {
    var s = 0
    for (i in 1..10) s += i
    return s
}
```

- `javap -c` 로 찍으면 `IntRange` 가 보이는가? `Iterator` 는?
- 끝값 비교에 쓰인 상수는 무엇인가 — 10 인가 다른 값인가?
- 같은 일을 하는 Java 의 `for (int i = 1; i <= 10; i++)` 과 명령이 다른가?
- 그래서 "Kotlin 의 range 는 객체라 느리다" 는 말은 이 형태에서 참인가?

### 2. ★★ 범위를 변수에 담으면 달라지는가 (예측)

```kotlin
fun inVariable(): Int {
    val r = 1..10
    var s = 0
    for (i in r) s += i
    return s
}
```

- 1번과 비교해 **새로 생기는 것**은 무엇인가?
- 이번에는 `iterator()` 가 불리는가?
- 컴파일러가 `r` 에서 **읽어 가는 메서드 둘**은 무엇인가?
- 반복 조건의 형태가 1번과 다른데, 그 차이가 막는 것은 무엇인가?

### 3. ★ 네 형태 중 stdlib 함수를 부르는 것은 (예측)

```kotlin
for (i in 1..10) { }
for (i in 0 until 10) { }
for (i in 0..<10) { }
for (i in 10 downTo 1) { }
for (i in 1..10 step 2) { }
```

- 다섯 중 **함수 호출이 생기는 것**은 무엇이고, 그 함수 이름은 무엇인가?
- `until` 과 `..<` 의 바이트코드는 얼마나 다른가?
- `downTo` 는 무엇으로 방향을 바꾸는가?
- 그 stdlib 함수가 필요한 이유는 무엇인가?

### 4. ★ 이 다섯 줄은 각각 무엇을 내는가 (예측)

```kotlin
(1..9 step 3).toList()          // [A]
(1..9 step 3).last              // [B]
(5..1).toList()                 // [C]
(9 downTo 1 step 3).toList()    // [D]
(1..9 step -1).toList()         // [E]
```

- 다섯의 결과는 각각 무엇인가?
- `[B]` 가 9 가 아니라면 그 이유는 무엇인가?
- `[C]` 는 예외인가 빈 리스트인가 — `for` 에 넣으면 몇 번 도는가?
- `[E]` 에서 무엇이 일어나고 메시지는 무엇인가?

### 5. `for` 가 받아 주는 것과 거부하는 것 (경계)

```kotlin
class Countdown(val from: Int) {
    operator fun iterator(): Iterator<Int> = TODO()
}
for (x in Countdown(3)) { }     // [A]
for (x in 1.0..2.0) { }         // [B]
1.5 in 1.0..2.0                 // [C]
```

- `[A]` 가 되려면 정확히 어떤 이름의 함수가 있어야 하는가?
- `[B]` 는 무엇을 말하며, `[C]` 는 되는가?
- `1.0..2.0` 의 런타임 타입은 무엇인가?
- `String`·`IntArray` 를 `for` 에 넣으면 `Iterator` 가 생기는가?

### 6. ★★ 이 두 함수는 무엇을 반환하는가 (예측)

```kotlin
fun findFirstEven(xs: List<Int>): Int? {
    xs.forEach { if (it % 2 == 0) return it }
    return null
}
fun localReturn(xs: List<Int>): String {
    val sb = StringBuilder()
    xs.forEach {
        if (it % 2 == 0) return@forEach
        sb.append(it)
    }
    return sb.toString()
}

findFirstEven(listOf(1, 3, 4, 6))   // [A]
localReturn(listOf(1, 2, 3, 4, 5))  // [B]
```

- 두 값은 각각 무엇인가?
- `return` 과 `return@forEach` 는 **어디까지** 빠져나가는가?
- 람다를 `val f: (Int) -> Unit = { … return }` 로 담으면 무엇이 나오는가?
- 이것이 되고 안 되고를 가르는 성질은 무엇이며, 그 정본은 어느 주제인가?

### 7. ★ 이 셋은 컴파일되는가 (예측)

```kotlin
fun a(xs: List<Int>) = xs.map { if (it == 2) break else it }          // [A]
fun b(): String {                                                     // [B]
    val sb = StringBuilder()
    for (i in 1..5) {
        listOf(10, 20).forEach { v -> if (i == 3) break; sb.append("$i:$v ") }
    }
    return sb.toString()
}
fun c(n: Int): Int { val a = while (n > 0) { break }; return 0 }       // [C]
```

- 셋 중 컴파일되는 것은 무엇인가?
- 안 되는 것들의 **에러 문구**는 각각 무엇인가?
- `[B]` 가 된다면 언제부터 되는가, 그리고 그 버전을 **컴파일러에게 물어보는 방법**은 무엇인가?
- `[B]` 가 되면 출력은 무엇인가?

### 8. 라벨이 정하는 범위는 (경계)

- `break` 와 `break@loop` 은 각각 어디까지 나가는가?
- 라벨을 붙이는 문법과 쓰는 문법은 각각 무엇인가 — Java 와 다른 점은?
- `continue@outer` 는 무엇을 건너뛰는가?
- `return@forEach` 는 `continue` 와 같은가?

### 9. `run` 라벨로 `continue` 를 흉내낼 때 다른 점은 (경계)

- `for (x in xs) { run skip@{ … return@skip … } }` 에서 `return@skip` 이 끝내는 것은 무엇인가?
- 진짜 `continue` 와 **다른 점** 하나는 무엇인가?
- `run` 이 객체를 만드는가?
- 이 관용구의 정본(scope function)은 어느 주제인가?

### 10. 반복은 식인가 (왜)

- `val a = while (…) { }` 는 무엇이 나오는가?
- `if`·`when` 과 갈리는 이유를 한 문장으로 말하면 무엇인가?
- 반복의 결과를 값으로 얻으려면 무엇을 쓰는가?
- `for (i in 1..3) { i = i + 1 }` 은 되는가?

### 11. 다른 주제와 잇기 (연결)

- 비지역 `return` 이 **왜** 인라인 람다에서만 되는지의 정본은 어느 주제인가?
- `for ((i, v) in xs.withIndex())` 의 구조 분해 정본은 어느 주제인가?
- `iterator()`·`contains` 같은 규약 전체의 정본은 어느 주제인가?
- Java 쪽 레이블 `break`/`continue` 의 정본은 어느 문서인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
