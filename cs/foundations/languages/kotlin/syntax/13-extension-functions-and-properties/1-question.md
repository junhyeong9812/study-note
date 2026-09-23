# kotlin/syntax/13 — 확장 함수·확장 프로퍼티: 정적 디스패치 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [08번 주제](../08-function-declaration-default-and-named-args/)다.
> ★ **「정적 디스패치라는 천장」의 *의미* 는 [`../../언어-특성/README.md`](../../언어-특성/README.md) §7 이 정본**이고,
> 여기는 **선언 문법·해소 순서·멤버 충돌 규칙**을 묻는다.
> 이 주제는 목록의 **14번 주제**·**31번 주제**·**37번 주제**의 뿌리다.
> Java 쪽 짝은 [`../../../java/syntax/11-interfaces-default-methods/`](../../../java/syntax/11-interfaces-default-methods/)다.
> 문항 11개 중 코드블록이 붙는 예측형은 6개다.
> 바이트코드를 묻는 문항은 **`kotlinc` 기본 `-jvm-target`(1.8)** 기준이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ `m.doubled()` 는 무엇으로 컴파일되는가 (예측)

```kotlin
// icode.kt
class Money(val won: Int)

fun Money.doubled(): Money = Money(won * 2)

val Money.label: String get() = "${won}원"

fun String?.orNone(): String = this ?: "none"

fun use(m: Money): String = m.doubled().label
```

- `doubled` 는 어느 클래스 파일 안에 들어가는가 — `Money.class` 인가, 다른 곳인가?
- 그 메서드의 **디스크립터**는 무엇인가 — 인자를 하나도 안 적었는데 파라미터가 몇 개인가?
- `Intrinsics.checkNotNullParameter` 에 넘어가는 **이름**은 무엇인가?
- 확장 프로퍼티 `label` 은 무엇이 되는가?

### 2. ★★ 같은 객체를 두 변수에 담으면 (예측)

```kotlin
open class Animal {
    open fun speakMember(): String = "Animal(member)"
}
class Dog : Animal() {
    override fun speakMember(): String = "Dog(member)"
}

fun Animal.speakExt(): String = "Animal(ext)"
fun Dog.speakExt(): String = "Dog(ext)"

fun main() {
    val asDog: Dog = Dog()
    val asAnimal: Animal = Dog()
    println("A : ${asDog.speakMember()}")
    println("B : ${asAnimal.speakMember()}")
    println("C : ${asDog.speakExt()}")
    println("D : ${asAnimal.speakExt()}")
    println("E : ${asDog.javaClass == asAnimal.javaClass}")
}
```

- `A`\~`E` 는 각각 무엇을 찍는가?
- 멤버 쪽과 확장 쪽에 각각 **어떤 JVM 명령**이 박히는가?
- 그 두 명령의 차이를 한 문장으로 말하면 무엇인가?
- `speakExt` 두 개는 JVM 에서 **어떤 관계**인가 — 이름이 같은데 왜 공존하는가?

### 3. ★★ 멤버와 확장의 이름이 겹치면 (예측)

```kotlin
class Cup {
    fun pour(): String = "member"
    fun pour(n: Int): String = "member($n)"
}

fun Cup.pour(): String = "extension"
fun Cup.pour(s: String): String = "extension($s)"

fun main() {
    val c = Cup()
    println("F : ${c.pour()}")
    println("G : ${c.pour(1)}")
    println("H : ${c.pour("x")}")
}
```

- 이 파일은 **컴파일되는가** — 에러인가 경고인가, 몇 건인가?
- `F`·`G`·`H` 는 각각 무엇을 찍는가?
- 경고는 **어느 선언에** 붙고 어느 선언에는 안 붙는가 — 그 기준은?
- 이 상황이 이 갈래에서 유난히 잘 놓치는 이유는 무엇인가?

### 4. ★★ 더 좁은 타입에 확장을 달면 이기는가 (예측)

```kotlin
open class Base { fun tag(): String = "Base.member" }
class Derived : Base()

fun Derived.tag(): String = "Derived.extension"
// Q : Derived().tag()
```

```kotlin
class Cup { val size: Int = 1 }
val Cup.size: Int get() = 99

fun Any.kind(): String = "Any"
fun String.kind(): String = "String"

fun main() {
    println("T : ${Cup().size}")
    val s: Any = "hi"
    println("U : ${s.kind()}")
    println("V : ${"hi".kind()}")
}
```

- `Q`·`T`·`U`·`V` 는 각각 무엇을 찍는가?
- 경고 문구는 **어느 클래스**를 지목하는가?
- 확장 **프로퍼티**도 멤버 프로퍼티에 지는가?
- `U` 와 `V` 가 갈리는 규칙은 2번과 같은 것인가 다른 것인가?

### 5. ★★ 클래스 **안에** 확장을 선언하면 (예측)

```kotlin
open class Animal
class Dog : Animal()

open class Printer {
    open fun Animal.render(): String = "Printer/Animal"
    open fun Dog.render(): String = "Printer/Dog"
    fun show(a: Animal): String = a.render()
}

class LoudPrinter : Printer() {
    override fun Animal.render(): String = "LoudPrinter/Animal"
    override fun Dog.render(): String = "LoudPrinter/Dog"
}

fun main() {
    val dogAsAnimal: Animal = Dog()
    println("R : ${Printer().show(dogAsAnimal)}")
    println("S : ${LoudPrinter().show(dogAsAnimal)}")
}
```

- `open`/`override` 가 붙었는데 컴파일되는가 — 경고는?
- `R` 과 `S` 는 각각 무엇을 찍는가?
- `javap` 로 보면 `render` 는 `static` 인가 인스턴스 메서드인가?
- `show` 안의 **한 명령어**에 두 성질이 같이 들어 있다 — 무엇과 무엇인가?

### 6. ★ 수신자가 `null` 이어도 되는 확장 (예측)

```kotlin
fun String?.orNone(): String = if (this == null) "none" else this
fun String.shout(): String = this + "!"

fun main() {
    val s: String? = null
    println("K : ${s.orNone()}")
    println("L : ${"hi".orNone()}")
    println("M : '${s.orEmpty()}'")
    println("N : ${s.toString()}")
}
```

- `K`\~`N` 은 각각 무엇을 찍는가?
- `orNone` 과 `shout` 의 **디스크립터**를 비교하면 무엇이 다른가?
- 그럼 무엇이 둘을 가르는가 — `javap` 에서 한 줄을 짚어 보라.
- `fun call(s: String?) = s.shout()` 은 무엇이 나오는가?

### 7. 확장이 못 하는 것 둘 (경계)

- `val Cup.cups: Int = ml / 200` 은 통과하는가 — 에러가 **몇 줄** 나오는가?
- 그중 **진짜 원인**은 몇째 줄인가, 첫 줄은 무엇인가?
- `fun Cup.peek(): Int = secret`(`secret` 은 `private`)은 어떻게 되는가?
- 그 두 제약은 1번의 어떤 사실에서 곧바로 따라 나오는가?

### 8. 임포트가 필요한 것이 왜 장점인가 (경계)

- 다른 패키지의 확장을 임포트 없이 쓰면 무슨 에러가 나는가 — **문구를 그대로** 대 보라.
- 그 문구는 「그런 이름이 없다」와 **어떻게 다르게** 말하는가?
- 임포트가 필요하다는 것이 확장에 어떤 성질을 주는가?
- 같은 이름의 확장이 두 라이브러리에 있으면 무엇이 결정하는가?

### 9. 타입 인자만 다른 확장 둘 (경계)

```kotlin
fun List<Int>.describe(): String = "ints"
fun List<String>.describe(): String = "strings"
```

- 이 둘은 공존하는가 — 안 되면 **에러 이름**은 무엇인가?
- 에러가 대는 **JVM 시그니처**를 적어 보라.
- 왜 그런가 — 1번·2번의 어느 사실이 합쳐진 결과인가?
- 고치는 법은 무엇이고, 고친 뒤 **Kotlin 쪽 호출 이름**은 바뀌는가?

### 10. 최상위 확장과 Java 쪽에서 보이는 모양 (경계)

- `open fun Animal.speak()` / `override fun Dog.speak()` 는 어떻게 되는가 — **문구를 그대로** 대 보라.
- 「확장은 오버라이드되지 않는다」보다 **더 정확한 문장**은 무엇인가?
- Java 에서 Kotlin 확장을 부르려면 어떻게 적는가?
- 그때 파일 클래스 이름은 무엇이고 무엇으로 바꿀 수 있는가?

### 11. Java `default` 메서드와 어디가 반대인가 (연결)

- 둘 다 「남의 타입에 메서드 추가」인데 **호출 명령**이 각각 무엇인가?
- **디스패치**가 각각 무엇인가, 하위 타입이 바꿀 수 있는가?
- 원 타입을 고쳐야 하는 쪽은 어디인가?
- `let`/`run`/`apply`/`also` 는 이 주제와 무슨 관계이고 정본은 어디인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
