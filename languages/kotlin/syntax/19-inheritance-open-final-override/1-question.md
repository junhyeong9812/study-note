# kotlin/syntax/19 — 상속: `open`/`final` 기본값 뒤집기·`override` 강제 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [15번 주제](../15-class-declaration-constructors-and-init/)다. 이 주제는 [20번 주제](../20-interfaces-default-impl-and-super/)·[21번 주제](../21-class-delegation-by/)의 뿌리다.
> ★ **`init` 순서와 「상위 생성자에서 `open` 멤버를 부르는 구멍」은 [15번 주제](../15-class-declaration-constructors-and-init/)가 정본**이라 여기서는 **결론만** 묻는다.
> 가시성은 [18번 주제](../18-visibility-modifiers/), 인터페이스의 충돌 해소는 [20번 주제](../20-interfaces-default-impl-and-super/)가 정본이다.
> 문항 12개 중 코드블록이 붙는 예측형은 6개다.
> 바이트코드를 묻는 문항은 **`kotlinc` 기본 `-jvm-target`(1.8)** 기준이다.
> 이 주제의 모든 답은 **kotlinc 2.4.20 · JRE 21.0.5** 에서 실제로 던져 받은 것이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★ 수식어를 하나도 안 붙인 클래스를 상속하면 (예측)

```kotlin
// finaldef.kt
class Account(val owner: String)

class Savings(owner: String) : Account(owner)
```

- 컴파일되는가? 에러라면 문구는 무엇인가?
- Java 에서 같은 코드를 쓰면 어떻게 되는가?
- 고치려면 어느 줄에 무엇을 적는가?

### 2. ★★ 클래스는 열었는데 멤버에 아무것도 안 적으면 (예측)

```kotlin
// finalmem.kt
open class Account(val owner: String) {
    fun describe() = "Account($owner)"
}

class Savings(owner: String) : Account(owner) {
    override fun describe() = "Savings($owner)"
}
```

- 컴파일되는가? 1번과 **같은 에러**인가 다른 에러인가?
- 「자물쇠가 둘」이라는 말을 이 두 에러로 설명해 보라.
- 고치려면 어느 줄에 무엇을 적는가?

### 3. ★★★ `override` 를 빠뜨리면 (예측)

```kotlin
// nomodifier.kt
open class Account(val owner: String) {
    open fun describe() = "Account($owner)"
}

class Savings(owner: String) : Account(owner) {
    fun describe() = "Savings($owner)"
}
```

- 컴파일되는가? 에러 문구에서 「**가린다(hides)**」는 낱말이 뜻하는 것은 무엇인가?
- Java 의 `@Override` 를 빠뜨렸을 때와 무엇이 다른가?
- 이 규칙이 막는 실패는 「오타」인가 다른 것인가?

### 4. ★★★ 3단 계층에서 `override` 와 `final override` (예측)

```kotlin
// chain.kt
open class A {
    open fun f() = "A.f"
    open fun g() = "A.g"
}

open class B : A() {
    override fun f() = "B.f"
    final override fun g() = "B.g"
}

class C : B() {
    override fun f() = "C.f"
}

fun main() {
    val list: List<A> = listOf(A(), B(), C())
    for (x in list) println("${x::class.simpleName} : ${x.f()} / ${x.g()}")
}
```

- 세 줄에 각각 무엇이 찍히는가?
- `C` 가 `f()` 를 다시 오버라이드할 수 있는 이유는 무엇인가 — `B` 에 `open` 을 안 적었는데?
- `C` 의 `g()` 는 어디 것이 불리는가?

### 5. ★ `abstract` 가 세 층에 걸쳐 있으면 (예측)

```kotlin
// abstr.kt
abstract class Shape {
    abstract val name: String
    abstract fun area(): Double
    open fun describe() = "$name 의 넓이 = ${area()}"
}

class Square(val side: Double) : Shape() {
    override val name = "Square"
    override fun area() = side * side
}

abstract class Rounded : Shape() {
    override fun area() = 0.0
}

class Dot : Rounded() {
    override val name = "Dot"
}

fun main() {
    println("A ${Square(3.0).describe()}")
    println("B ${Dot().describe()}")
    val shapes: List<Shape> = listOf(Square(2.0), Dot())
    println("C ${shapes.map { it.area() }}")
}
```

- `A`·`B`·`C` 에 각각 무엇이 찍히는가?
- `abstract fun area()` 에 `open` 을 안 적었는데 오버라이드되는 이유는?
- `Rounded` 는 왜 `abstract` 여야 하는가?

### 6. ★★ `open` 을 하나도 안 적은 클래스가 세 메서드를 오버라이드한다 (예측)

```kotlin
// anyover.kt
class Point(val x: Int, val y: Int) {
    override fun equals(other: Any?): Boolean = other is Point && other.x == x && other.y == y
    override fun hashCode(): Int = x * 31 + y
    override fun toString(): String = "Point($x, $y)"
}

class Plain(val x: Int)

fun main() {
    println("A ${Point(1, 2)}")
    println("B ${Point(1, 2) == Point(1, 2)} / ${Point(1, 2) === Point(1, 2)}")
    println("C ${Point(1, 2).hashCode()} ${Point(1, 2).hashCode()}")
    println("D ${Plain(1) == Plain(1)} / ${Plain(1).javaClass.name}")
}
```

- `A`\~`D` 에 각각 무엇이 찍히는가?
- `Point` 는 아무것도 상속하지 않은 것처럼 보이는데 무엇을 오버라이드하고 있는가?
- `D` 줄의 `Plain(1) == Plain(1)` 이 그렇게 나오는 이유는?

### 7. ★ `override` 없이 `fun toString()` 이라고만 적으면 (경계)

```kotlin
// anybad.kt
class Point(val x: Int, val y: Int) {
    fun toString(): String = "Point($x, $y)"
}
```

- 3번과 같은 에러인가?
- 에러 문구의 `supertype` 자리에 무엇이 오는가?
- 이것이 「아무것도 상속 안 한 클래스는 없다」는 말과 어떻게 이어지는가?

### 8. `override` 를 문법으로 강제해서 막는 실패는 무엇인가 (왜)

- 상위 클래스가 **나중에** 메서드를 추가하는 시나리오를 써 보라.
- Java 에서는 그때 무슨 일이 일어나는가?
- Kotlin 에서는 무슨 일이 일어나는가 — 그 차이가 왜 값어치가 있는가?

### 9. ★ `javap` 로 보면 `final` 이 어디에 붙는가 (경계)

```kotlin
// flags.kt
class Locked {
    fun m() = "Locked.m"
}

open class Openish {
    fun stillFinal() = "stillFinal"
    open fun overridable() = "overridable"
}

class Sub : Openish() {
    override fun overridable() = "Sub.overridable"
}

abstract class Abs {
    abstract fun must(): String
}
```

- `Locked`·`Openish`·`Sub`·`Abs` 네 클래스에 `final` 이 붙는가?
- `stillFinal()` 과 `overridable()` 중 어느 쪽에 `ACC_FINAL` 이 붙는가?
- ★★ `Sub` 의 `override fun overridable()` 에는 `ACC_FINAL` 이 붙는가 — 왜 그런가?
- 이것은 [18번 주제](../18-visibility-modifiers/)의 `internal` 과 어떻게 다른가?

### 10. 한 번 잠근 것을 다시 열 수 있는가 (경계)

```kotlin
// chainbad.kt
open class A {
    open fun g() = "A.g"
}

open class B : A() {
    final override fun g() = "B.g"
}

class C : B() {
    override fun g() = "C.g"
}
```

- 컴파일되는가? 에러라면 1\~3번 중 어느 것과 같은 문구인가?
- 「기본값은 닫힘」이라는 이 언어의 규칙이 **지켜지지 않는 자리**가 어디인가?
- 그 자리에서 닫으려면 무엇을 적어야 하는가?

### 11. 확장 함수와 무엇이 다른가 (연결)

- [13번 주제](../13-extension-functions-and-properties/)의 확장 함수는 어느 타입을 보고 구현을 고르는가?
- `List<Shape>` 를 돌며 `area()` 를 부르는 5번의 `C` 줄을 **확장 함수로 바꾸면** 무엇이 달라지는가?
- 「상속 계층을 늘릴 것인가, 확장 함수로 끝낼 것인가」를 가르는 기준을 한 줄로 적어 보라.

### 12. 기본값이 [15번 주제](../15-class-declaration-constructors-and-init/)의 구멍을 어떻게 좁히는가 (연결)

- 상위 클래스 `init` 에서 `open` 함수를 부르면 무엇이 보이는가(결론만)?
- 그 구멍이 Java 에서 **더 넓은** 이유는 무엇인가?
- Kotlin 에서 그 구멍에 빠지려면 프로그래머가 무엇을 **먼저 적어야** 하는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
