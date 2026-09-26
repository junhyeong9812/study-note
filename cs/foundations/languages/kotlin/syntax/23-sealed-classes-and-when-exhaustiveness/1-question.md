# kotlin/syntax/23 — `sealed class`/`sealed interface` 와 `when` 완결성 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [6번 주제](../06-when-expression/)·[20번 주제](../20-interfaces-default-impl-and-super/)·[22번 주제](../22-data-class-generated-members/)다. 이 주제는 [24번 주제](../24-enum-class-vs-sealed/)의 뿌리다.
> ★ **`when` 의 가지 형태·guard·바이트코드 분기·런타임 예외는 [6번 주제](../06-when-expression/)가 정본**이라 여기서는 **결론만** 묻는다.
> 문항 11개 중 코드블록이 붙는 예측형은 6개다.
> 바이트코드를 묻는 문항은 **기본 `-jvm-target`(1.8)과 `-jvm-target 17` 을 나란히** 묻는다 — 이 주제에서 **그 둘이 다르다**.
> 이 주제의 모든 답은 **kotlinc 2.4.20 · JRE 21.0.5** 에서 실제로 던져 받은 것이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ `when` 을 **문으로** 쓰고 가지 하나를 빼면 (예측)

```kotlin
// sealstmt.kt
sealed interface Ev
data class Click(val x: Int) : Ev
data object Key : Ev

fun stmtOverSealed(e: Ev) {
    when (e) {
        is Click -> println("click")
    }
}

fun stmtOverInt(n: Int) {
    when (n) {
        1 -> println("one")
    }
}

fun stmtOverBoolean(b: Boolean) {
    when (b) {
        true -> println("t")
    }
}

fun exprOverInt(n: Int): String = when (n) {
    1 -> "one"
}
```

- 컴파일되는가? 에러라면 **몇 줄**이고 어느 함수에서 나는가?
- 네 함수 중 **통과하는 것이 있다면 어느 것**이고 왜인가?
- ★★ 에러 문구가 `'when' expression must be exhaustive.` 인데, 그 낱말을 곧이곧대로 읽으면 무엇을 오해하게 되는가?

### 2. ★★ `sealed class` 와 `sealed interface` 를 한 파일에 (예측)

```kotlin
// sealkinds.kt
sealed class Expr {
    data class Num(val v: Int) : Expr()
    data class Add(val l: Expr, val r: Expr) : Expr()
    data object Zero : Expr()
}

sealed interface Json
data class JStr(val s: String) : Json
data class JNum(val n: Int) : Json
data object JNull : Json
class JList(val xs: List<Json>) : Json, Comparable<JList> {
    override fun compareTo(other: JList) = xs.size - other.xs.size
}

fun eval(e: Expr): Int = when (e) {
    is Expr.Num -> e.v
    is Expr.Add -> eval(e.l) + eval(e.r)
    Expr.Zero -> 0
}

fun render(j: Json): String = when (j) {
    is JStr -> "\"${j.s}\""
    is JNum -> j.n.toString()
    JNull -> "null"
    is JList -> j.xs.joinToString(",", "[", "]") { render(it) }
}

fun main() {
    println("A ${eval(Expr.Add(Expr.Num(2), Expr.Add(Expr.Num(3), Expr.Zero)))}")
    println("B ${render(JList(listOf(JStr("a"), JNum(1), JNull)))}")
    println("C ${Expr.Zero === Expr.Zero}")
}
```

- `A`·`B`·`C` 에 각각 무엇이 찍히는가?
- 두 `when` 에 `else` 가 없는데 컴파일되는 이유는?
- ★ `JList` 가 `Json` 이면서 동시에 `Comparable<JList>` 다. 이것이 `sealed class` 로는 왜 곤란한가?

### 3. ★★★ 변형을 **하나** 늘리면 몇 곳이 깨지나 (예측)

```kotlin
// addnoelse3.kt
sealed interface Ev
data class Click(val x: Int) : Ev
data class Key(val c: Char) : Ev
data object Scroll : Ev

fun label(e: Ev): String = when (e) {
    is Click -> "클릭"
    is Key -> "키"
    Scroll -> "스크롤"
}

fun code(e: Ev): Int = when (e) {
    is Click -> 1
    is Key -> 2
    Scroll -> 3
}

fun isKey(e: Ev): Boolean = when (e) {
    is Key -> true
    is Click -> false
    Scroll -> false
}

fun log(e: Ev) {
    when (e) {
        is Click -> println("  click ${e.x}")
        is Key -> println("  key ${e.c}")
        Scroll -> println("  scroll")
    }
}

fun chain(e: Ev): String =
    if (e is Click) "클릭"
    else if (e is Key) "키"
    else "그 밖"

fun noSubject(e: Ev): String = when {
    e is Click -> "클릭"
    e is Key -> "키"
    else -> "그 밖"
}

fun main() {
    val all: List<Ev> = listOf(Click(1), Key('a'), Scroll)
    for (e in all) println("${label(e)} ${code(e)} ${isKey(e)} ${chain(e)} ${noSubject(e)}")
    for (e in all) log(e)
}
```

- 이 파일은 통과한다. 여기에 `data class Drag(val dx: Int, val dy: Int) : Ev` **한 줄만** 더하고 `when` 은 한 글자도 안 고치면 — **에러가 몇 곳**에서 나는가?
- 여섯 함수 중 **안 깨지는 것이 몇 개**인가? 어느 것들인가?
- `log` 는 값을 안 내는 `when` **문**이다. 깨지는가?

### 4. ★★★ 같은 실험을 `else` 판에서 하면 (예측)

```kotlin
// addelse4.kt
sealed interface Ev
data class Click(val x: Int) : Ev
data class Key(val c: Char) : Ev
data object Scroll : Ev
data class Drag(val dx: Int, val dy: Int) : Ev

fun label(e: Ev): String = when (e) {
    is Click -> "클릭"
    is Key -> "키"
    else -> "스크롤"
}

fun code(e: Ev): Int = when (e) {
    is Click -> 1
    is Key -> 2
    else -> 3
}

fun isKey(e: Ev): Boolean = when (e) {
    is Key -> true
    is Click -> false
    else -> false
}

fun log(e: Ev) {
    when (e) {
        is Click -> println("  click ${e.x}")
        is Key -> println("  key ${e.c}")
        else -> println("  scroll")
    }
}

fun chain(e: Ev): String =
    if (e is Click) "클릭"
    else if (e is Key) "키"
    else "그 밖"

fun noSubject(e: Ev): String = when {
    e is Click -> "클릭"
    e is Key -> "키"
    else -> "그 밖"
}

fun main() {
    val all: List<Ev> = listOf(Click(1), Key('a'), Scroll, Drag(3, 4))
    for (e in all) println("${label(e)} ${code(e)} ${isKey(e)} ${chain(e)} ${noSubject(e)}")
    for (e in all) log(e)
}
```

- 컴파일되는가? **에러 몇 건, 경고 몇 건**인가?
- 출력에서 `Drag(3, 4)` 줄은 어떻게 찍히는가?
- 3번과 이 문항의 수치를 격자로 적어 보라 — 그 격자가 말하는 것은 무엇인가?

### 5. ★★ 앞줄 **한 줄**에 따라 통과와 에러가 갈린다 (예측)

```kotlin
// sealflow.kt
sealed interface Ev
data class Click(val x: Int) : Ev
data class Key(val c: Char) : Ev
data object Scroll : Ev

fun render(e: Ev): String {
    if (e is Scroll) return "scroll"
    return when (e) {
        is Click -> "click ${e.x}"
        is Key -> "key ${e.c}"
    }
}

fun flag(b: Boolean): String = when (b) {
    true -> "켜짐"
    false -> "꺼짐"
}

fun main() {
    println("A ${render(Click(7))}")
    println("B ${render(Scroll)}")
    println("C ${flag(true)} ${flag(false)}")
}
```

- `A`·`B`·`C` 에 각각 무엇이 찍히는가?
- `render` 의 `when` 에 `Scroll` 가지가 없는데 통과하는 이유는 무엇인가?
- ★★ `if (e is Scroll) return "scroll"` 을 **지우면** 무슨 일이 생기는가?
- `flag(b)` 가 `else` 없이 통과하는 것은 같은 규칙인가 다른 규칙인가?

### 6. ★ 하위 타입을 **다른 패키지**에 두면 (예측)

```kotlin
// sealpkg.kt
package shapes

sealed interface Shape
```

```kotlin
// sealpkgb.kt
package intruders

import shapes.Shape

class Triangle : Shape
```

- 컴파일되는가? 에러 문구는 무엇인가?
- 조건은 「같은 파일」인가, 「같은 패키지」인가, 「같은 모듈」인가?
- 이 제약이 없으면 완결성 검사가 왜 성립하지 않는가?

### 7. ★★ `javap` 로 보면 `-jvm-target` 이 무엇을 바꾸는가 (경계)

```kotlin
// sealbyte.kt
sealed class Shape

class Circle(val r: Double) : Shape()

class Rect(val w: Double, val h: Double) : Shape()
```

- 기본 `-jvm-target`(1.8)에서 `Shape` 는 **어떤 클래스**가 되는가? 생성자는 몇 개이고 접근자는 무엇인가?
- `-jvm-target 17` 로 바꾸면 클래스 파일에 **무엇이 더 생기는가**?
- ★★ 「sealed 는 `PermittedSubclasses` 로 컴파일된다」는 말은 어느 조건에서 참인가?

### 8. ★★ Java 쪽에서 상속을 시도하면 (경계)

```java
// Intruder.java
public class Intruder extends Shape {
    public Intruder() { super(null); }
}
```

- 1.8 로 컴파일한 `Shape` 에 대해 `javac` 가 에러를 **몇 건** 내는가?
- 17 로 컴파일한 `Shape` 에 대해서는 **몇 건**인가? 늘어난 한 건은 무엇인가?
- 1.8 판에서도 막히기는 한다 — **막는 근거**가 17 판과 어떻게 다른가?

### 9. 왜 `else` 가 안전망을 없애는가 (왜)

- `else` 를 적는 순간 컴파일러가 **무엇을 그만두는가**?
- 그런데도 `else` 가 **옳은 자리**가 있다. 어디인가 — 기준을 한 줄로 적어 보라.
- `else` 대신 쓸 수 있는 중간 답은 무엇인가?

### 10. `when` 을 `if` 사슬로 바꾸면 (경계)

- 3번의 `chain`·`noSubject` 두 함수는 변형이 늘었을 때 깨졌는가?
- 「주체 없는 `when`」(`when { 조건 -> ... }`)은 완결성 검사를 받는가?
- 리팩토링으로 `when` 을 `if` 로 바꿀 때 잃는 것을 한 줄로 적어 보라.

### 11. Rust 의 `_` · Java 21 의 `switch` 와 대비 (연결)

- [`../../../rust/syntax/18-match-and-exhaustiveness/`](../../../rust/syntax/18-match-and-exhaustiveness/)의 같은 실험에서 `_` 판은 에러 몇 건, 경고 몇 건이었는가? Kotlin 과 무엇이 다른가?
- Rust 의 `match` 에는 「문이라 검사 안 되는 자리」가 있는가?
- [`../../../java/syntax/23-switch-pattern-matching/`](../../../java/syntax/23-switch-pattern-matching/)에서 명단이 뒤에 늘면 런타임에 무엇이 나는가? Kotlin 쪽 대응물은?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
