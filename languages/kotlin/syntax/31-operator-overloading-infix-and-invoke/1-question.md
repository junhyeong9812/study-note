# kotlin/syntax/31 — 연산자 오버로딩·중위 함수·`invoke` 규약 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [13번 주제](../13-extension-functions-and-properties/)다 — 확장 함수가 **정적 호출**이라는 것을 거기서 봤다. `infix` 의 우선순위는 [09번 주제](../09-varargs-spread-local-and-infix-functions/)가 정본이다.
> 문항 10개 중 코드블록이 붙는 예측형은 5개다.
> 바이트코드를 묻는 문항은 **`kotlinc` 기본 `-jvm-target`(1.8)** 기준이다.
> 이 주제의 모든 답은 **kotlinc 2.4.20 · JRE 21.0.5** 에서 실제로 던져 받은 것이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 기호마다 함수 하나 — 그 바이트코드 (예측)

```kotlin
// opgrid.kt
class V(val n: Int) {
    operator fun plus(o: V) = V(n + o.n)
    operator fun minus(o: V) = V(n - o.n)
    operator fun times(o: V) = V(n * o.n)
    operator fun div(o: V) = V(n / o.n)
    operator fun rem(o: V) = V(n % o.n)
    operator fun unaryMinus() = V(-n)
    operator fun not() = V(n.inv())
    operator fun inc() = V(n + 1)
    operator fun get(i: Int) = n + i
    operator fun set(i: Int, v: Int) { println("set $i $v") }
    operator fun invoke(x: Int) = n * x
    operator fun contains(x: Int) = x == n
    operator fun rangeTo(o: V) = n..o.n
    operator fun rangeUntil(o: V) = n..<o.n
    operator fun compareTo(o: V) = n.compareTo(o.n)
}

class Acc(var n: Int) {
    operator fun plusAssign(o: Int) { n += o }
}

fun s01(a: V, b: V) = a + b
fun s02(a: V, b: V) = a - b
fun s03(a: V, b: V) = a * b
fun s04(a: V, b: V) = a / b
fun s05(a: V, b: V) = a % b
fun s06(a: V) = -a
fun s07(a: V) = !a
fun s08(a: V): V { var x = a; x++; return x }
fun s09(a: V) = a[2]
fun s10(a: V) { a[1] = 5 }
fun s11(a: V) = a(3)
fun s12(a: V) = 4 in a
fun s13(a: V) = 4 !in a
fun s14(a: V, b: V) = a..b
fun s15(a: V, b: V) = a..<b
fun s16(a: V, b: V) = a < b
fun s17(a: Acc) { a += 2 }
fun s18(a: V, b: V) = a == b
fun s19(a: V, b: V) = a.plus(b)

fun main() {
    val a = V(6); val b = V(4)
    println("${s01(a, b).n} ${s02(a, b).n} ${s03(a, b).n} ${s04(a, b).n} ${s05(a, b).n}")
    println("${s06(a).n} ${s07(a).n} ${s08(a).n} ${s09(a)} ${s11(a)}")
    s10(a)
    println("${s12(a)} ${s13(a)} ${s14(a, b)} ${s15(b, a)} ${s16(a, b)} ${s18(a, b)}")
    val acc = Acc(1); s17(acc); println(acc.n)
}
```

- 실행하면 다섯 줄에 무엇이 찍히는가?
- `javap -c -p` 로 `s01`\~`s19` 를 보면, **`V`·`Acc` 의 메서드를 부르지 않는 함수**가 있는가? 있다면 무엇을 부르는가?
- `s13`(`!in`)과 `s16`(`<`)은 각각 **어느 메서드**를 부르고, 부정·비교는 누가 하는가?
- `s01` 과 `s19` 의 바이트코드는 어떻게 다른가?

### 2. ★★★ `plus` 와 `plusAssign` 이 둘 다 있으면 (예측)

```kotlin
// assignbad.kt
class Both(val n: Int) {
    operator fun plus(o: Int) = Both(n + o)
    operator fun plusAssign(o: Int) { println("plusAssign $o") }
}

class Bare(val n: Int) {
    fun plus(o: Int) = Bare(n + o)
}

fun main() {
    var a = Both(1)
    a += 2
    val c = Bare(1) + 4
}
```

- 12번째 줄과 13번째 줄은 각각 컴파일되는가? 막힌다면 컴파일러는 **무엇을** 말하는가?

### 3. ★★ 같은 `+=` 를 세 좌변에 (예측)

```kotlin
// assignok.kt
class Both(val n: Int) {
    operator fun plus(o: Int) = Both(n + o)
    operator fun plusAssign(o: Int) { println("A plusAssign $o") }
}

fun main() {
    val b = Both(1)
    b += 3
    var ml = mutableListOf(1)
    val m0 = ml
    ml += 2
    println("B $ml $m0 ${ml === m0}")
    var rl: List<Int> = listOf(1)
    val r0 = rl
    rl += 2
    println("C $rl $r0 ${rl === r0}")
}
```

- 컴파일되는가? `A`\~`C` 에 무엇이 찍히는가?
- `B` 와 `C` 의 마지막 칸(`===`)이 다르다면 그 이유는? 바이트코드에서 각각 무엇이 불리는가?

### 4. ★★ `equals` 에 `operator` 를 붙이면 (예측)

```kotlin
// eqop.kt
class Q(val n: Int) {
    operator fun equals(other: Q): Boolean = n == other.n
}

operator fun Q.equals(other: Any?): Boolean = true
```

- 두 선언은 각각 컴파일되는가? 막힌다면 무엇이라고 말하는가?

### 5. ★★ 확장 연산자·`invoke`·수신자를 고치는 `plus` (예측)

```kotlin
// ext31.kt
operator fun String.times(k: Int): String = repeat(k)
operator fun StringBuilder.plusAssign(s: String) { append(s) }

class Money(val cents: Long) {
    operator fun plus(o: Money) = Money(cents + o.cents)
    override fun toString() = "Money($cents)"
}

class Bag(val items: MutableList<String>) {
    operator fun plus(s: String): Bag { items.add(s); return this }
    override fun toString() = "Bag$items"
}

fun main() {
    println("A " + "ab" * 3)
    val sb = StringBuilder("x"); sb += "y"; println("B $sb")
    val a = Bag(mutableListOf("p"))
    val b = a + "q"
    println("C a=$a b=$b ${a === b}")
    val price = Money(100)
    val total = price + Money(50)
    println("D price=$price total=$total")
    more()
}

class Check(private val min: Int) {
    operator fun invoke(s: String) = s.length >= min
}

fun more() {
    val longEnough = Check(3)
    println("E ${longEnough("ab")} ${longEnough("abc")} ${listOf("a", "abcd").filter(longEnough::invoke)}")
}
```

- `A`\~`E` 에 무엇이 찍히는가? 컴파일러는 경고를 내는가?
- `"ab" * 3` 은 바이트코드에서 `invokevirtual` 인가 `invokestatic` 인가?

### 6. `operator` 가 없으면 (왜)

- 2번의 `Bare` 처럼 `fun plus` 가 **있는데도** `+` 가 막히는 이유는? 이 도장이 없으면 어떤 사고가 생기겠는가?

### 7. `+=` 의 모호성 규칙 (경계)

- 문서의 세 조건은 무엇인가? 3번의 `var ml: MutableList<Int>` 는 왜 **모호하지 않은가**?

### 8. 「연산자 오버로딩은 비용이 없다」 (경계)

- 이 문장을 이 문서의 근거로 쓸 수 있는가? 이 문서가 **실제로 보인 것**은 무엇이고, 런타임 비용을 「잴 것이 없다」고 적는 이유는?

### 9. `infix` 와 연산자 (연결)

- `infix fun Vec.dot(o: Vec)` 는 연산자 오버로딩인가? `1 shl 2 + 3` 은 몇이 되는가 — 이 답의 정본은 어느 주제인가?

### 10. Rust 의 `a + b` (연결)

- Rust 에서 `a + b` 뒤에 `a` 를 다시 쓸 수 없는 경우가 있는 이유는? Kotlin 에서는 왜 그런 일이 없는가?
- 남의 타입에 연산자를 다는 방법이 두 언어에서 어떻게 다른가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
