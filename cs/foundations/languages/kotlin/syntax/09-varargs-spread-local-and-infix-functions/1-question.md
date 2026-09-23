# kotlin/syntax/09 — 가변 인자·spread 연산자·로컬 함수·중위 함수 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [08번 주제](../08-function-declaration-default-and-named-args/)다.
> 연산자 오버로딩 **전체**는 목록의 **31번 주제**, 람다·클로저 일반은 목록의 **10번 주제**가 정본이다.
> Java 쪽 짝은 [`../../../java/syntax/08-method-declaration-overloading/`](../../../java/syntax/08-method-declaration-overloading/)다.
> 문항 11개 중 코드블록이 붙는 예측형은 6개다.
> 바이트코드를 묻는 문항은 **`kotlinc` 기본 `-jvm-target`(1.8)** 기준이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ 이 네 호출은 각각 무엇을 만드는가 (예측)

```kotlin
fun sum(vararg xs: Int): Int = xs.sum()

fun callLiteral(): Int = sum(1, 2, 3)        // [A]
fun callSpread(a: IntArray): Int = sum(*a)   // [B]
fun callSpreadMixed(a: IntArray): Int = sum(0, *a, 9)  // [C]
fun callEmpty(): Int = sum()                 // [D]
```

- `javap -c` 로 찍으면 넷이 각각 어떤 명령·호출로 시작하는가?
- `[B]` 가 부르는 **JDK 메서드 이름**은 무엇인가?
- `[C]` 가 만드는 **stdlib 내부 클래스**의 이름은 무엇이고, 생성자에 넘기는 숫자는 무엇을 뜻하는가?
- `[D]` 는 아무것도 안 만드는가?

### 2. ★★ 이 프로그램의 출력은 (예측)

```kotlin
fun mutate(vararg xs: Int): String {
    val before = xs.joinToString()
    if (xs.isNotEmpty()) xs[0] = -999
    return "함수 안에서 본 것: [$before] -> [${xs.joinToString()}]"
}
fun sameRef(vararg xs: Int): IntArray = xs

val src = intArrayOf(1, 2, 3)
println(mutate(*src))
println(src.joinToString())          // [A]
println(sameRef(*src) === src)       // [B]
```

- `[A]` 는 무엇을 찍는가 — 원본이 바뀌었는가?
- `[B]` 는 무엇인가?
- 그 근거가 되는 바이트코드 한 줄은 무엇인가?
- 이 사실 중 **언어 보장**인 것과 **구현**인 것을 갈라 적으면 각각 무엇인가?

### 3. `vararg` 파라미터와 배열 파라미터는 무엇이 다른가 (경계)

```kotlin
fun join(vararg parts: String): String = parts.joinToString("-")
fun takesArray(xs: Array<out String>): Int = xs.size
```

- 둘의 **JVM 디스크립터**는 같은가 다른가?
- 그러면 실제로 다른 것은 무엇인가?
- `join` 을 배열로 부르려면 무엇이 필요하고, `takesArray` 를 낱개로 부를 수 있는가?
- `javap` 가 `String...` 이라고 찍는 이유는 무엇인가?

### 4. ★ `vararg` 가 마지막이 아닐 때 이 둘은 (예측)

```kotlin
fun mid(a: Int, vararg xs: Int, b: Int): Int = a + xs.size + b
fun two(vararg a: Int, vararg b: Int): Int = a.size + b.size   // [C]

mid(1, 2, 3, b = 9)   // [A]
mid(1, 2, 3, 9)       // [B]
```

- 선언 `mid` 자체는 통과하는가?
- `[A]`·`[B]` 중 되는 것은 무엇이고, 안 되는 쪽의 에러 문구는 무엇인가?
- 그 에러 문구가 **진짜 원인을 말해 주는가**?
- `[C]` 는 무엇이 나오는가?

### 5. ★★ 로컬 함수는 클래스를 만드는가 (예측)

```kotlin
fun outerNoCapture(n: Int): Int {
    fun twice(x: Int) = x * 2
    return twice(n)
}
fun outerCaptureVal(n: Int): Int {
    val base = n * 10
    fun add(x: Int) = base + x
    return add(1) + add(2)
}
fun outerCaptureVar(n: Int): Int {
    var acc = 0
    fun bump(x: Int) { acc += x }
    bump(n); bump(n)
    return acc
}
```

- 컴파일하면 **클래스 파일이 몇 개** 나오는가?
- `javap -s -p` 에 보이는 **세 개의 숨은 메서드 이름**은 각각 무엇인가?
- `add` 의 파라미터가 **둘**인 이유는 무엇인가?
- `bump` 의 첫 파라미터 타입은 무엇이고 왜 그것이 필요한가?

### 6. 같은 일을 로컬 함수로 할 때와 람다로 할 때 (경계)

```kotlin
fun withLocalFun(n: Int): Int {
    val base = n * 10
    fun add(x: Int) = base + x
    return add(1)
}
fun withLambda(n: Int): Int {
    val base = n * 10
    val add: (Int) -> Int = { x -> base + x }
    return add(1)
}
```

- 두 함수의 호출 명령은 각각 무엇인가?
- 람다 쪽에만 나타나는 **박싱 두 곳**은 어디인가?
- 람다는 별도 클래스 파일을 만드는가?
- 그래서 둘 중 무엇을 언제 고르는가?

### 7. ★ 이 여섯 중 `infix` 가 거부되는 것은 (예측)

```kotlin
class Box(val v: Int) {
    infix fun plus(o: Box) = Box(v + o.v)        // [A]
    infix fun bad1(vararg o: Box) = this          // [B]
    infix fun bad2(o: Box = Box(0)) = this        // [C]
    infix fun bad3(a: Box, b: Box) = this         // [D]
    infix fun bad4() = this                       // [E]
}
infix fun top(a: Int, b: Int) = a + b             // [F]
```

- 여섯 중 에러가 나는 것은 몇 개이고 무엇인가?
- 에러 문구는 하나인가 여럿인가?
- **공식 문서가 금지한다고 적었는데 컴파일러가 받아 주는 것**이 있는가?
- 있다면 그것을 실제로 **중위로 호출**할 수 있는가?

### 8. ★ 이 네 식의 값은 (예측)

```kotlin
infix fun Int.x(o: Int) = this * o

2 x 3 + 1          // [A]
1 + 2 shl 3        // [B]
1 shl 2 + 3        // [C]
(1..3 step 2).toList()  // [D]
```

- 넷의 값은 각각 무엇인가?
- `[A]` 가 그렇게 되는 이유를 괄호로 다시 적으면 무엇인가?
- 중위 함수는 산술·비교·엘비스 중 **무엇보다 세고 무엇보다 약한가**?
- `!b x n` 은 왜 컴파일이 안 되는가?

### 9. `vararg` 에 기본값을 줄 수 있는가 (경계)

- `fun f(vararg xs: Int = intArrayOf(1, 2))` 는 컴파일되는가?
- 된다면 `f()` 와 `f(7, 8, 9)` 는 각각 무엇을 보는가?
- 그 기본값은 어느 메서드 안에 들어가는가?
- `tag(classes = arrayOf("a", "b"))` 처럼 **이름으로 배열을 직접** 넘길 수 있는가?

### 10. 언제 `vararg` 를 쓰고 언제 안 쓰는가 (왜)

- 호출자가 **이미 `List` 를 들고 있으면** 무엇이 더 싼가?
- 호출자가 **이미 배열을 들고 있으면** `vararg` 의 대가는 무엇인가?
- 그 대가를 피하려면 시그니처를 어떻게 바꾸는가?
- 이 문서가 **재지 않은 것**은 무엇인가?

### 11. 다른 주제와 잇기 (연결)

- 기본 인자·`@JvmOverloads` 의 정본은 어느 주제인가?
- 연산자 규약 표 전체(`plus`·`get`·`invoke`·`iterator`)의 정본은 어느 주제인가?
- 람다가 바깥 `var` 를 잡는 것의 정본은 어느 주제인가?
- `step`·`downTo` 가 중위 함수라는 것은 어느 주제에서 쓰였는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
