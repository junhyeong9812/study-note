# kotlin/syntax/30 — 구조 분해 선언: `componentN` 과 그 한계 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [22번 주제](../22-data-class-generated-members/)다 — `componentN` 이 **만들어진다는 것**은 거기서 봤다.
> 문항 10개 중 코드블록이 붙는 예측형은 6개다.
> 바이트코드를 묻는 문항은 **`kotlinc` 기본 `-jvm-target`(1.8)** 기준이다.
> 이 주제의 모든 답은 **kotlinc 2.4.20 · JRE 21.0.5**(Java 쪽은 **javac 21.0.5**)에서 실제로 던져 받은 것이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 같은 호출부를 두 판의 선언에 붙이면 (예측)

```kotlin
// person1.kt
data class P(val first: String, val last: String) {
    companion object {
        fun sample() = P(first = "Ada", last = "Lovelace")
    }
}
```

```kotlin
// person2.kt
data class P(val last: String, val first: String) {
    companion object {
        fun sample() = P(first = "Ada", last = "Lovelace")
    }
}
```

```kotlin
// readp.kt
fun main() {
    val p = P.sample()
    val (first, last) = p
    println("A $first $last")
    println("B ${p.first} ${p.last}")
}
```

- `kotlinc person1.kt readp.kt` 와 `kotlinc person2.kt readp.kt` 는 각각 컴파일되는가? 에러나 경고가 나는가?
- 두 판에서 `A` 줄과 `B` 줄에 각각 무엇이 찍히는가?

### 2. ★★ 호출부를 다시 컴파일하지 않으면 (예측)

1번의 세 파일로 이렇게 던졌다 —

```text
kotlinc person1.kt -d lib30v1
kotlinc -cp lib30v1 readp.kt -d app30
kotlinc person2.kt -d lib30v2
java -cp app30:lib30v1:kotlin-stdlib.jar ReadpKt
java -cp app30:lib30v2:kotlin-stdlib.jar ReadpKt
```

- 마지막 줄은 링크 에러(`NoSuchMethodError` 등)로 죽는가? 죽지 않는다면 `A` 줄에 무엇이 찍히는가?

### 3. ★ 괄호·밑줄·`withIndex` (예측)

```kotlin
// dsforms.kt
data class Pt(val x: Int, val y: Int)

fun main() {
    val pts = listOf(Pt(1, 2), Pt(3, 4))
    println("A " + pts.map { (a, b) -> a * 10 + b })
    val m = mapOf("k1" to 1, "k2" to 2)
    println("B " + m.map { (k, v) -> "$k=$v" })
    val (_, y) = Pt(7, 8)
    println("C $y")
    for ((i, p) in pts.withIndex()) println("D $i $p")
    val f: (Pt, Pt) -> Int = { a, b -> a.x + b.x }
    println("E " + f(Pt(1, 0), Pt(2, 0)))
}
```

- `A`\~`E` 에 무엇이 찍히는가?
- `C` 줄의 `val (_, y)` 는 바이트코드에서 `Pt.component1` 을 부르는가?

### 4. ★★ 괄호를 잘못 치면 (예측)

```kotlin
// dsbad.kt
data class Pt(val x: Int, val y: Int)

fun main() {
    val pts = listOf(Pt(1, 2), Pt(3, 4))
    println(pts.map { a, b -> a + b })
    val g: (Pt, Pt) -> Int = { (a, b) -> a + b }
    val (p, q, r) = Pt(1, 2)
}
```

- 5·6·7번째 줄은 각각 컴파일되는가? 막힌다면 컴파일러는 **무엇이 몇 개짜리 함수**라고 말하는가?

### 5. ★ 일반 클래스의 `component1` (예측)

```kotlin
// regok.kt
class Span(val lo: Int, val hi: Int) {
    operator fun component1() = lo
    operator fun component2() = hi
}

fun main() {
    val (lo, hi) = Span(3, 9)
    println("A $lo $hi")
}
```

```kotlin
// regbad.kt
class Solo(val a: Int) {
    fun component1() = a
}

fun main() {
    val (a) = Solo(1)
    println(a)
}
```

- 두 파일은 각각 컴파일되는가? `regok.kt` 는 무엇을 찍는가?

### 6. ★★★ 컴파일러에게 이름을 읽게 하면 (예측)

1번의 `person2.kt readp.kt` 를 다음 세 형태로 다시 던졌다.

```text
kotlinc -Xname-based-destructuring=name-mismatch person2.kt readp.kt -d o30c
kotlinc -Xname-based-destructuring=complete      person2.kt readp.kt -d o30d
kotlinc -language-version 2.5                    person2.kt readp.kt -d o30e
```

- 각각 진단이 나오는가? 실행하면 `A` 줄에 무엇이 찍히는가?

```kotlin
// newform.kt
data class Q(val last: String, val first: String)

fun main() {
    val q = Q(first = "Ada", last = "Lovelace")
    val [a, b] = q
    println("A $a $b")
    (val f = first, val l = last) = q
    println("B $f $l")
}
```

- 이 파일을 플래그 없이 던지면? `-Xname-based-destructuring=only-syntax` 로 던지면 `A`·`B` 에 무엇이 찍히는가?

### 7. `component1` 이 읽는 필드 (경계)

- 1번의 두 판에서 `javap -c -p P.class` 로 `component1()` 을 보면 **어느 필드**를 `getfield` 하는가?
- 번호를 정하는 것은 언어인가, JVM 백엔드인가?

### 8. `Map.Entry` 는 Java 인터페이스인데 (왜)

- `for ((k, v) in map)` 이 되는 이유는? `java.util.Map.Entry` 에는 `component1` 이 없다.
- 그 루프의 바이트코드에 `component1` 호출이 남는가?

### 9. Java record 패턴 (연결)

- Java 의 `if (o instanceof JP(var first, var last))` 에서 `JP` 의 컴포넌트 순서를 바꾸면 `javac` 가 알아채는가?
- Kotlin 과 무엇이 같고 무엇이 다른가 — 생성 쪽과 읽는 쪽을 갈라서 답해 보라.

### 10. 두 필드가 같은 타입이면 (왜)

- 1번의 사고를 기본 컴파일러가 못 잡는 이유는? 두 필드가 `String` 과 `Int` 였다면 어떻게 달라지는가?
- 이 사고에서 진단 창을 「재 봤더니 조용했다」가 아니라 「**잴 것이 없다**」로 적는 이유는?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
