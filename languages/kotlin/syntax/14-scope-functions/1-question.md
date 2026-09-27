# kotlin/syntax/14 — scope function 5종: `let`/`run`/`with`/`apply`/`also` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [10번 주제](../10-lambdas-and-higher-order-functions/)와 [13번 주제](../13-extension-functions-and-properties/)다.
> ★ **`inline` 이 무엇을 없애고 무엇을 제약하는지는 [11번 주제](../11-inline-functions/)가 정본**이고,
> 다섯이 전부 **확장 함수**라는 사실은 [13번 주제](../13-extension-functions-and-properties/)가 정본이다.
> 여기는 **다섯을 어떻게 갈라서 고르나**를 묻는다.
> 이 주제는 [목록의 **37번 주제**](../37-lambdas-with-receiver-and-type-safe-builders/)·**58번 주제**의 뿌리다.
> Java 에는 대응이 **없다** — [`../../../java/syntax/README.md`](../../../java/syntax/README.md) 목록의 59\~60 관용구 편이 같은 자리를 다른 방식으로 메운다.
> 문항 11개 중 코드블록이 붙는 예측형은 6개다.
> 바이트코드를 묻는 문항은 **`kotlinc` 기본 `-jvm-target`(1.8)** 기준이고, 람다 전략 플래그를 따로 밝힌다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ 같은 객체에 다섯을 각각 걸면 (예측)

```kotlin
// scope.kt
class Cup(var ml: Int) {
    fun label(): String = "Cup(${ml}ml)"
}

fun main() {
    val a = Cup(100).let { it.ml = 1; it.label() }
    val b = Cup(100).run { ml = 2; label() }
    val c = with(Cup(100)) { ml = 3; label() }
    val d = Cup(100).apply { ml = 4 }
    val e = Cup(100).also { it.ml = 5 }

    println("A let   : $a   (타입 ${a::class.simpleName})")
    println("B run   : $b   (타입 ${b::class.simpleName})")
    println("C with  : $c   (타입 ${c::class.simpleName})")
    println("D apply : ${d.label()}   (타입 ${d::class.simpleName})")
    println("E also  : ${e.label()}   (타입 ${e::class.simpleName})")

    val cup = Cup(100)
    println("F apply 가 돌려준 것이 그 객체인가 : ${cup.apply { ml = 9 } === cup}")
    println("G also  가 돌려준 것이 그 객체인가 : ${cup.also { it.ml = 9 } === cup}")
}
```

- `A`\~`E` 의 **값과 타입**은 각각 무엇인가?
- 다섯을 가르는 **축이 몇 개**이고 각각 무엇인가?
- `F`·`G` 는 무엇을 찍는가 — 그것이 뜻하는 바는?
- 다섯을 그 축으로 칸에 넣으면 **칸이 몇 개** 차는가?

### 2. ★ 수신자를 다른 이름으로 부르면 (예측)

```kotlin
// badrecv.kt
class Cup(var ml: Int)

fun main() {
    val cup = Cup(100)
    cup.apply { it.ml = 1 }
    cup.let { ml = 2 }
}
```

- 이 파일은 컴파일되는가 — 에러인가 경고인가, **몇 건**인가?
- 에러 문구를 그대로 대 보라 — 무엇을 지목하는가?
- 다섯 중 이 에러가 나는 조합과 안 나는 조합은 어떻게 갈리는가?
- 이 축 말고 **나머지 축**은 컴파일러가 막아 주는가?

### 3. ★★ 널이 끼면 어디서 갈리나 (예측)

```kotlin
// nullsafe.kt
fun oldWay(s: String?): String {
    if (s != null) {
        return "len=${s.length}"
    }
    return "none"
}

fun newWay(s: String?): String = s?.let { "len=${it.length}" } ?: "none"

fun letWithoutQ(s: String?): String = s.let { if (it == null) "none" else "len=${it.length}" }

fun runQ(s: String?): String = s?.run { "len=$length" } ?: "none"

fun main() {
    println("H oldWay(null)        : ${oldWay(null)}")
    println("I newWay(null)        : ${newWay(null)}")
    println("J newWay(\"abc\")       : ${newWay("abc")}")
    println("K letWithoutQ(null)   : ${letWithoutQ(null)}")
    println("L runQ(null)          : ${runQ(null)}")

    var count = 0
    val s: String? = "abc"
    s?.let { count++ }
    val t: String? = null
    t?.let { count++ }
    println("M 람다가 몇 번 돌았나  : $count")
}
```

- `H`\~`M` 은 각각 무엇을 찍는가?
- `K` 가 **컴파일이 되는 것 자체**가 무엇을 말하는가?
- 널 검사를 실제로 하는 것은 `let` 인가 다른 무엇인가 — `M` 이 그 근거가 되는가?
- `H` 와 `I` 의 출력이 같다면, 바꿔 쓸 때 **실제로 바뀌는 것**은 무엇인가?

### 4. ★★ 엘비스가 언제 도나 (예측)

```kotlin
// trap.kt
class Row(val id: Int, val name: String?)

fun lookup(r: Row?): String =
    r?.let { it.name } ?: "FALLBACK"

fun main() {
    println("U 널 행         : ${lookup(null)}")
    println("V 이름 있는 행   : ${lookup(Row(1, "kim"))}")
    println("W 이름이 널인 행 : ${lookup(Row(2, null))}")

    val sb = StringBuilder()
    val got = sb.apply { append("x") ; length }
    println("X apply 가 돌려준 것 : ${got::class.simpleName}")

    var side = 0
    val v = 10.also { side = it * 2 }
    println("Y also 의 값 : $v   side : $side")
}
```

- `U`·`V`·`W` 는 각각 무엇을 찍는가?
- `W` 에서 `r` 은 널이 아닌데 왜 그 결과가 나오는가 — `?:` 가 보는 것은 무엇인가?
- `X` 는 무엇을 찍는가 — 람다 마지막에 `length` 를 뒀는데도 그렇다면 그 이유는?
- `Y` 의 두 값은 각각 무엇인가?

### 5. ★ 두 겹으로 쌓으면 (예측)

```kotlin
// nest.kt
class Outer(val name: String) { fun who(): String = "Outer($name)" }
class Inner(val name: String) { fun who(): String = "Inner($name)" }

fun main() {
    val o = Outer("O")
    val i = Inner("I")

    o.apply {
        println("P 바깥 apply 의 this : ${who()}")
        i.apply {
            println("Q 안쪽 apply 의 this : ${who()}")
            println("R this@apply 는      : ${this@apply.who()}")
        }
    }

    o.apply outer@ {
        i.apply {
            println("S this@outer 는      : ${this@outer.who()}")
        }
    }

    "AB".let {
        "CD".let {
            println("T 안쪽 it 은         : $it")
        }
    }
}
```

- 이 파일은 경고가 **몇 건** 나오는가 — 어느 줄에 붙는가?
- `P`\~`T` 는 각각 무엇을 찍는가?
- `R` 과 `S` 가 갈리는 이유는 무엇인가?
- `T` 쪽에는 왜 경고가 없는가 — 그것이 실무에서 왜 더 나쁜가?

### 6. ★★★ 다섯이 클래스 파일에 남는가 (예측)

```kotlin
// inl.kt
class Cup(var ml: Int)

fun five(cup: Cup): Int {
    val a = cup.let { it.ml + 1 }
    val b = cup.run { ml + 2 }
    val c = with(cup) { ml + 3 }
    val d = cup.apply { ml += 4 }.ml
    val e = cup.also { it.ml += 5 }.ml
    return a + b + c + d + e
}
```

```kotlin
// noninl.kt
class Cup(var ml: Int)

fun <T, R> myLet(x: T, f: (T) -> R): R = f(x)

fun five(cup: Cup): Int {
    val a = myLet(cup) { it.ml + 1 }
    val b = myLet(cup) { it.ml + 2 }
    return a + b
}
```

- 두 파일을 각각 컴파일하면 **클래스 파일이 몇 개씩** 나오는가?
- `-Xlambdas=class` 를 주면 그 개수가 어떻게 바뀌는가 — 두 파일에서 다르게 바뀌는가?
- `javap -v` 로 `Function1` 이라는 글자를 세면 각각 **몇 회**인가?
- 그 람다 메서드들에 `ACC_SYNTHETIC` 이 붙는가?

### 7. `it` 을 안 쓰면 컴파일러가 뭐라 하나 (경계)

- `cup.also { println("…") }` 처럼 `it` 을 한 번도 안 쓰면 **경고가 나는가**?
- `let`·`apply` 는 어떤가 — 셋이 다른가?
- 「경고가 없다」는 것을 어떻게 읽어야 하는가?
- 그럴 때는 무엇으로 바꿔 쓰는 편이 나은가?

### 8. 다섯 중 하나만 `?.` 를 못 붙인다 (경계)

- `fun f(s: String?): Int = with(s) { length }` 는 통과하는가 — 에러 문구를 그대로 대 보라.
- 그 에러는 **어느 이름**을 지목하는가 — 왜 그 자리인가?
- `run` 으로 바꾸면 되는가, 안 되는가 — 무엇이 둘을 가르는가?
- 이것이 「같은 칸에 있는 둘」을 실제로 가르는 기준인가?

### 9. 칸이 넷인데 함수는 다섯이다 (왜)

- 겹치는 두 함수는 무엇인가?
- `kotlin-stdlib` 을 역어셈블하면 그 둘의 **디스크립터**가 어떻게 보이는가?
- 그런데도 Kotlin 에서 뜻이 갈리는 이유는 무엇인가 — 그 정보는 어디에 있는가?
- 그럼 **Java 에서** 그 둘을 구분할 수 있는가?

### 10. stdlib 선언에 붙어 있는 표시 둘 (경계)

- 다섯은 stdlib 클래스 파일에서 `public` 인가 `private` 인가 — 왜 그런가?
- `kotlin.internal.InlineOnly` 는 무엇을 뜻하는가?
- `kotlin.IgnorableReturnValue` 는 무엇을 뜻하고 다섯 중 어디에 붙어 있는가?
- `LocalVariableTable` 의 0번 슬롯 이름은 무엇이고 그것이 무슨 사실의 증거인가?

### 11. 11번·13번과 어떻게 이어지나 (연결)

- 다섯이 **확장 함수**라는 사실에서 곧바로 따라 나오는 성질은 무엇인가?
- 다섯이 **`inline`** 이라는 사실에서 따라 나오는 성질은 무엇인가?
- 「인라인이라 빠르다」는 이 주제가 증명한 것인가 — 증명한 것은 정확히 무엇인가?
- 수신자 지정 람다를 **깊게** 쌓는 것(DSL)은 어느 주제가 정본인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
