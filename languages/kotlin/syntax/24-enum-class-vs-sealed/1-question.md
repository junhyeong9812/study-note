# kotlin/syntax/24 — `enum class` 와 `sealed` 선택 기준 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [23번 주제](../23-sealed-classes-and-when-exhaustiveness/)다. [6번 주제](../06-when-expression/)·[22번 주제](../22-data-class-generated-members/)도 먼저 보면 좋다.
> ★ **`sealed` 의 완결성 규칙 자체는 [23번 주제](../23-sealed-classes-and-when-exhaustiveness/)**, **`when` 의 `enum` 주체 바이트코드는 [6번 주제](../06-when-expression/)** 가 정본이라 여기서는 **결론만** 묻는다.
> 문항 11개 중 코드블록이 붙는 예측형은 6개다.
> 바이트코드를 묻는 문항은 **`kotlinc` 기본 `-jvm-target`(1.8)** 기준이다.
> ★★ 리플렉션 문항의 **목록 순서**는 답이 아니다 — **집합과 개수**로 답하라.
> 이 주제의 모든 답은 **kotlinc 2.4.20 · JRE 21.0.5** 에서 실제로 던져 받은 것이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ `entries` 와 `values()` 를 나란히 부르면 (예측)

```kotlin
// enumdata.kt
enum class Color(val hex: String) {
    RED("#f00"), GREEN("#0f0"), BLUE("#00f");

    fun bright() = "$name($hex)"
}

fun main() {
    println("A ${Color.entries}")
    println("B ${Color.entries.size} ${Color.values().size}")
    println("C ${Color.values() === Color.values()}")
    println("D ${Color.entries === Color.entries}")
    println("E ${Color.RED === Color.valueOf("RED")}")
    println("F ${Color.BLUE.ordinal} ${Color.BLUE.name} ${Color.BLUE.bright()}")
    println("G ${Color.entries.javaClass.name}")
    println("H ${Color.values().javaClass.name}")
    val arr = Color.values()
    arr[0] = Color.BLUE
    println("I ${Color.values()[0]} ${arr[0]}")
}
```

- `A`\~`I` 에 각각 무엇이 찍히는가?
- `C` 와 `D` 가 갈리는 이유는 무엇인가?
- ★ `I` 줄 — 내가 받은 배열의 0번을 덮었는데 왜 다음 `values()[0]` 은 멀쩡한가?

### 2. ★ `javap -p` 로 보면 `enum` 은 무엇인가 (경계)

- 1번의 `Color` 는 무엇을 **상속**하고 있는가?
- 상수 `RED`·`GREEN`·`BLUE` 는 클래스 파일에서 **무엇**인가?
- 생성자의 **접근자**는 무엇인가? 그것이 막는 것은?
- `$VALUES` 와 `$ENTRIES` 가 **둘 다** 있는 이유는?

### 3. ★★★ 같은 문제를 `enum` 으로 모델링하면 (예측)

```kotlin
// modelenum.kt
enum class PayState { SUCCESS, FAILURE, PENDING }

data class PayResult(
    val state: PayState,
    val amount: Int? = null,
    val reason: String? = null,
)

fun describe(r: PayResult): String = when (r.state) {
    PayState.SUCCESS -> "${r.amount!!}원 결제"
    PayState.FAILURE -> "실패: ${r.reason!!}"
    PayState.PENDING -> "대기"
}

fun main() {
    println("A ${describe(PayResult(PayState.SUCCESS, amount = 1000))}")
    val impossible = PayResult(PayState.SUCCESS, reason = "카드 거절")
    println("B $impossible")
    println("C ${PayState.SUCCESS === PayState.SUCCESS}")
    println("D ${PayState.entries.size}")
    println("E ${runCatching { describe(impossible) }.exceptionOrNull()?.javaClass?.name}")
}
```

- `A`\~`E` 에 각각 무엇이 찍히는가?
- ★★ `B` 줄에 담긴 객체는 **말이 되는 값**인가? 컴파일 경고가 나오는가?
- `E` 가 그렇게 나오는 근본 원인은 어디에 있는가 — `describe` 인가 `PayResult` 인가?

### 4. ★★ 같은 문제를 `sealed` 로 모델링하면 (예측)

```kotlin
// modelsealed.kt
sealed interface Pay
data class Success(val amount: Int) : Pay
data class Failure(val reason: String) : Pay
data object Pending : Pay

fun describe(p: Pay): String = when (p) {
    is Success -> "${p.amount}원 결제"
    is Failure -> "실패: ${p.reason}"
    Pending -> "대기"
}

fun main() {
    println("A ${describe(Success(1000))}")
    println("B ${describe(Failure("카드 거절"))}")
    println("C ${describe(Pending)}")
    println("D ${Success(1000) === Success(1000)} ${Success(1000) == Success(1000)}")
    println("E ${Pending === Pending}")
    val many = listOf(Success(1000), Success(2000), Success(3000))
    println("F ${many.size} ${many.distinct().size}")
}
```

- `A`\~`F` 에 각각 무엇이 찍히는가?
- `describe` 에 `!!` 가 **몇 개** 있는가? 3번과 비교해 보라.
- `D` 와 `E` 가 다른 이유는 무엇인가?

### 5. ★★ `sealed` 판에서 불가능한 상태를 만들려 하면 (예측)

```kotlin
// modelbad.kt
sealed interface Pay
data class Success(val amount: Int) : Pay
data class Failure(val reason: String) : Pay
data object Pending : Pay

fun main() {
    val impossible = Success(reason = "카드 거절")
    println(impossible)
    val p: Pay = Pending
    println(p.amount)
}
```

- 컴파일되는가? 에러가 **몇 줄**이고 각각 무엇을 말하는가?
- 3번의 `PayResult` 로 같은 값을 만들면 컴파일되는가?
- 「불가능한 상태를 표현할 수 없게 만든다」를 이 두 결과로 설명해 보라.

### 6. ★ 명단을 프로그램에서 세면 (경계)

```kotlin
// enumref.kt
import kotlin.reflect.KClass

enum class Color { RED, GREEN, BLUE }

sealed interface Shape
data class Circle(val r: Double) : Shape
data class Rect(val w: Double, val h: Double) : Shape
data object Empty : Shape

fun main() {
    println("A ${Color.entries.map { it.name }}")
    val subs: List<KClass<out Shape>> = Shape::class.sealedSubclasses
    println("B ${subs.mapNotNull { it.simpleName }.sorted()}")
    println("C ${subs.size}")
    println("D ${Color::class.java.isEnum} ${Shape::class.java.isEnum}")
    println("E ${Circle(1.0) === Circle(1.0)} ${Circle(1.0) == Circle(1.0)}")
    println("F ${Empty === Empty}")
    println("G ${Color.entries.map { it === Color.valueOf(it.name) }}")
}
```

- `A`\~`G` 에 각각 무엇이 찍히는가?
- `B` 를 정렬해서 찍은 이유는 무엇인가?
- `entries` 와 `sealedSubclasses` 중 **테스트에서 모든 변형을 돌리기**에 편한 쪽은 어디이고 왜인가?

### 7. ★ `enum` 주체의 `when` 에서 가지를 빼면 (경계)

```kotlin
// enumwhen.kt
enum class Status { NEW, PENDING, DONE }

fun label(s: Status): String = when (s) {
    Status.NEW -> "새로 만듦"
    Status.DONE -> "끝남"
}
```

- 컴파일되는가? 문구는 무엇인가?
- [23번 주제](../23-sealed-classes-and-when-exhaustiveness/)의 `sealed` 에서 본 문구와 같은가 다른가?
- 그렇다면 **완결성은 둘을 가르는 기준이 될 수 있는가**?
- ★ 덧붙여 — `enum class` 에 `data` 나 `sealed` 를 붙일 수 있는가? `enum` 을 상속할 수 있는가? `equals` 를 오버라이드할 수 있는가?

### 8. ★★ 바깥 문자열로 `valueOf` 를 부르면 (예측)

```kotlin
// enumfail.kt
enum class Status { NEW, DONE }

fun main() {
    System.err.println("--- Status.valueOf(\"PENDING\") 을 부른다 ---")
    Status.valueOf("PENDING")
}
```

- 예외 **타입과 메시지**는 무엇인가?
- 마커를 `println` 이 아니라 `System.err.println` 으로 찍은 이유는?
- 스택트레이스에서 **근거로 써도 되는 줄**과 **쓰면 안 되는 줄**을 갈라 보라.

### 9. ★★★ 상수를 **가운데**에 하나 끼우고 저장해 둔 값을 읽으면 (예측)

```kotlin
// ordv1.kt
import java.io.*

enum class Status { NEW, DONE }

fun main() {
    println("A ${Status.entries.map { "${it.ordinal}:${it.name}" }}")
    val bos = ByteArrayOutputStream()
    ObjectOutputStream(bos).use { it.writeObject(Status.DONE) }
    File("status.bin").writeBytes(bos.toByteArray())
    File("status.ordinal").writeText(Status.DONE.ordinal.toString())
    val printable = String(bos.toByteArray(), Charsets.ISO_8859_1)
        .map { if (it.code in 32..126) it else '.' }.joinToString("")
    println("B $printable")
    println("C 저장한 ordinal = ${Status.DONE.ordinal}")
}
```

```kotlin
// ordv2.kt
import java.io.*

enum class Status { NEW, PENDING, DONE }

fun main() {
    println("A ${Status.entries.map { "${it.ordinal}:${it.name}" }}")
    val back = ObjectInputStream(ByteArrayInputStream(File("status.bin").readBytes())).readObject() as Status
    println("B $back ${back.ordinal} ${back === Status.DONE}")
    val savedOrdinal = File("status.ordinal").readText().toInt()
    println("C 저장했던 ordinal $savedOrdinal 로 읽으면 = ${Status.entries[savedOrdinal]}")
}
```

- `ordv1` 의 `A`·`B`·`C` 에 각각 무엇이 찍히는가?
- ★★ `ordv2` 의 `B`·`C` 에 각각 무엇이 찍히는가? 둘 중 **조용히 틀린 값**이 나오는 쪽은 어디인가?
- 직렬화 바이트 안에 무엇이 들어 있길래 `B` 가 버티는가?

### 10. `enum` 에 데이터가 붙는 순간 무엇이 부족해지는가 (왜)

- `enum` 도 생성자 인자로 데이터를 들 수 있다. 그런데도 3번에서 부족했던 이유는?
- 「상수당 한 벌 고정」과 「호출마다 다른 값」의 차이를 예로 설명해 보라.
- 부족함이 코드에서 **무엇의 개수**로 드러나는가?

### 11. Java 쪽 두 주제와 대비 (연결)

- [`../../../java/syntax/13-enum-classes/`](../../../java/syntax/13-enum-classes/)가 센 「싱글턴을 지키는 잠금 넷」은 무엇이었는가?
- `EnumSet`·`EnumMap` 을 `sealed` 로 옮기면 무엇이 달라지는가?
- [`../../../java/syntax/15-sealed-classes/`](../../../java/syntax/15-sealed-classes/)와 견주면, Kotlin `sealed` 와 Java `sealed` 는 **명단을 어디에 적는가**?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
