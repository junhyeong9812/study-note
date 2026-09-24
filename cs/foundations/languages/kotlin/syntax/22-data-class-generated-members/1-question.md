# kotlin/syntax/22 — `data class`: 무엇이 생성되고 무엇이 안 되나 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [15번 주제](../15-class-declaration-constructors-and-init/)다. 이 주제는 [23번 주제](../23-sealed-classes-and-when-exhaustiveness/)·목록의 **26번 주제**와 목록의 **30번 주제**의 뿌리다.
> ★ **backing field 와 `const` 는 [16번 주제](../16-properties-backing-field-lateinit-const/)**, **`final` 기본값은 [19번 주제](../19-inheritance-open-final-override/)** 가 정본이라 여기서는 **결론만** 묻는다.
> 문항 11개 중 코드블록이 붙는 예측형은 6개다.
> 바이트코드를 묻는 문항은 **`kotlinc` 기본 `-jvm-target`(1.8)** 기준이다.
> ★★ 이 주제의 `hashCode` 는 **값이 아니라 「같나 다르나」로만** 묻는다 — 값은 실행마다 바뀌기 때문이다.
> 이 주제의 모든 답은 **kotlinc 2.4.20 · JRE 21.0.5** 에서 실제로 던져 받은 것이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ 본문에 선언한 `var` 를 서로 다르게 채운 두 객체를 비교하면 (예측)

```kotlin
// dcgen.kt
data class User(val id: Int, val name: String) {
    var note: String = ""
    val upper: String get() = name.uppercase()
}

fun main() {
    val a = User(1, "kim")
    val b = User(1, "kim")
    a.note = "A 쪽 메모"
    b.note = "B 쪽 메모"
    println("A ${a == b}")
    println("B ${a.hashCode() == b.hashCode()}")
    println("C $a")
    println("D ${a.note} / ${b.note}")
    println("E ${a.component1()} ${a.component2()}")
    println("F ${a.copy().note == ""}")
}
```

- `A`\~`F` 에 각각 무엇이 찍히는가?
- `B` 에서 해시코드의 **값**을 안 묻고 「같나」만 묻는 이유는 무엇인가?
- `F` 가 그렇게 나오는 이유를 `copy` 의 시그니처로 설명해 보라.

### 2. ★★ `javap -p` 로 세면 멤버가 몇 종인가 (경계)

- 1번의 `User` 를 `javap -p` 로 보면 **필드가 몇 개**인가 — `note` 는 있는가 없는가?
- `copy` 의 **파라미터가 몇 개**인가? 그 수가 말해 주는 것은 무엇인가?
- `copy$default` 는 무엇을 하려고 생긴 것인가?
- `data` 가 **안 만들어 주는 것**을 셋만 대 보라.

### 3. ★★ `copy()` 가 돌려주는 것 (예측)

```kotlin
// dccopy.kt
data class Cart(val owner: String, val items: MutableList<String>) {
    var coupon: String? = "WELCOME"
}

fun main() {
    val a = Cart("kim", mutableListOf("사과"))
    val b = a.copy()
    b.items.add("배")
    println("A ${a.items}")
    println("B ${b.items}")
    println("C ${a.items === b.items}")
    println("D ${a == b}")
    a.coupon = null
    val c = a.copy(owner = "lee")
    println("E ${c.owner} ${c.coupon}")
    println("F ${a.coupon}")
}
```

- `A`\~`F` 에 각각 무엇이 찍히는가?
- `C` 가 그렇게 나오는 것을 무엇이라 부르는가?
- ★★ `a.coupon` 을 `null` 로 바꾼 **뒤에** 복사했는데 `E` 가 그렇게 나오는 이유는?

### 4. ★★ 구조 분해에서 이름만 바꿔 받으면 (예측)

```kotlin
// dcorder.kt
data class Point(val x: Int, val y: Int)

fun main() {
    val p = Point(x = 10, y = 20)
    val (x, y) = p
    println("A x=$x y=$y")
    val (y2, x2) = p
    println("B x=$x2 y=$y2")
    println("C ${p.component1()} ${p.component2()}")
}
```

- `A`·`B`·`C` 에 각각 무엇이 찍히는가?
- 컴파일 경고가 나오는가?
- 컴파일러는 `x`·`y` 라는 **이름**을 보는가, 보지 않는가?

### 5. ★★ 읽는 코드를 안 고쳤는데 선언 순서가 바뀌면 (예측)

```kotlin
// dcorder2.kt
data class Coord(val y: Int, val x: Int)

fun readIt(c: Coord) {
    val (x, y) = c
    println("A x=$x y=$y")
}

fun main() {
    readIt(Coord(y = 20, x = 10))
    println("B ${Coord(20, 10)}")
}
```

- `A`·`B` 에 각각 무엇이 찍히는가?
- 두 필드의 **타입이 같다**는 사실이 이 상황에서 왜 결정적인가?
- 이것을 막으려면 읽는 쪽을 어떻게 고쳐야 하는가?

### 6. ★ `data object` 와 그냥 `object` (예측)

```kotlin
// dcobject.kt
object Plain
data object Marked

fun main() {
    println("A ${Plain.toString().substringBefore('@')} / @ 붙음=${'@' in Plain.toString()}")
    println("B $Marked / @ 붙음=${'@' in Marked.toString()}")
    println("C ${Plain == Plain} ${Marked == Marked}")
    println("D ${Marked.hashCode() == Marked.hashCode()}")
    println("E ${Plain === Plain} ${Marked === Marked}")
}
```

- `A`\~`E` 에 각각 무엇이 찍히는가?
- `javap -p` 로 보면 두 클래스의 **멤버 목록이 몇 개 차이**나는가?
- `data object` 에는 `copy`·`componentN` 이 생기는가 — 왜 그런가?

### 7. ★★ `data class` 에 붙일 수 없는 것들 (예측)

```kotlin
// dcforbid.kt
open class Base(val tag: String)

open data class Bad1(val x: Int)

data class Ok1(val x: Int) : Base("b")

class Sub : Ok1(1)

data class Bad3()

data class Bad4(x: Int)

data class Bad5(val x: Int) {
    fun component1() = 99
}
```

- 에러가 **몇 줄** 나는가? 각각 무엇을 말하는가?
- ★★ 이 중 **에러가 안 나는 선언이 하나** 있다. 어느 것인가?
- `data class Bad3()` 가 막히는 이유를 `data object` 와 엮어 설명해 보라.

### 8. ★ 컴포넌트가 평범한 클래스면 (경계)

```kotlin
// dchash.kt
class Plain(val v: Int)

data class Wrap(val p: Plain)
data class Flat(val v: Int)

fun main() {
    val w1 = Wrap(Plain(1))
    val w2 = Wrap(Plain(1))
    println("A ${w1 == w2}")
    println("B ${w1.hashCode() == w2.hashCode()}")
    val f1 = Flat(1)
    val f2 = Flat(1)
    println("C ${f1 == f2}")
    println("D ${f1.hashCode() == f2.hashCode()}")
    println("E ${w1.toString().substringBefore('@')}")
}
```

- `A`\~`D` 에 각각 무엇이 찍히는가?
- `data` 를 붙였는데 `A` 가 그렇게 나오는 이유는?
- `E` 가 `@` 앞에서 잘려 있는 이유는 무엇인가?

### 9. 왜 주 생성자 프로퍼티만 읽게 만들었나 (왜)

- 본문 프로퍼티까지 읽으려 하면 `copy` 의 **시그니처**에 무슨 일이 생기는가?
- 계산 프로퍼티(`val upper get() = ...`)를 `copy` 의 인자로 받을 수 있는가?
- 이 규칙이 준 것과 남긴 위험을 한 줄씩 적어 보라.

### 10. `data class` 와 상속의 **두 방향** (경계)

- `data class` 가 **다른 클래스를 상속**할 수 있는가?
- `data class` 를 **누가 상속**할 수 있는가?
- 두 답이 다르다면 그 차이는 [19번 주제](../19-inheritance-open-final-override/)의 어느 규칙에서 오는가?

### 11. Java `record` 와 어디서 갈리나 (연결)

- [`../../../java/syntax/14-records/`](../../../java/syntax/14-records/)의 `record` 는 본문에 **인스턴스 필드**를 둘 수 있는가?
- 그 차이가 1번의 사고를 Java 쪽에서 어떻게 바꾸는가?
- 「방어선의 위치가 다르다」를 두 언어의 문법으로 각각 설명해 보라.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
