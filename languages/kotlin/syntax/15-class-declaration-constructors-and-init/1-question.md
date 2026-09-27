# kotlin/syntax/15 — 클래스 선언: 주 생성자·부 생성자·`init` 블록 순서 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [01번 주제](../01-val-var-and-basic-types/)다.
> ★ **널 불가 타입의 보장 자체는 [03번 주제](../03-null-safe-types/)가 정본**이고,
> `open`/`final` 기본값은 [목록의 **19번 주제**](../19-inheritance-open-final-override/), backing field·`lateinit` 은 [16번 주제](../16-properties-backing-field-lateinit-const/)가 정본이다.
> 여기는 **한 객체가 만들어질 때 무엇이 어느 순서로 도는가**를 묻는다.
> 이 주제는 [16번 주제](../16-properties-backing-field-lateinit-const/)·[목록의 **18번 주제**](../18-visibility-modifiers/)·**19번 주제**·**22번 주제**·**25번 주제**·**27번 주제**의 뿌리다.
> Java 쪽 짝은 [`../../../java/syntax/06-initialization-order/`](../../../java/syntax/06-initialization-order/)와
> [`../../../java/syntax/07-constructors/`](../../../java/syntax/07-constructors/)다.
> 문항 11개 중 코드블록이 붙는 예측형은 6개다.
> 바이트코드를 묻는 문항은 **`kotlinc` 기본 `-jvm-target`(1.8)** 기준이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ 다섯 자리에 번호를 매겨 두면 (예측)

```kotlin
// order.kt
class Box(val tag: String) {
    val first = say("1 프로퍼티 first")

    init {
        say("2 init 블록 A")
    }

    val second = say("3 프로퍼티 second")

    init {
        say("4 init 블록 B")
    }

    constructor(n: Int) : this("from-int-$n") {
        say("5 부 생성자 본문")
    }

    private fun say(s: String): String {
        println("   $s   (tag=$tag)")
        return s
    }
}

fun main() {
    println("A 주 생성자로 만들 때")
    Box("P")
    println("B 부 생성자로 만들 때")
    Box(7)
}
```

- `A` 아래에는 번호가 **어떤 순서로** 찍히는가?
- `B` 아래에는 어떻게 찍히는가 — `A` 와 무엇이 다른가?
- `B` 에서 `tag=` 에 찍히는 값은 **처음부터** 무엇인가 — 그것이 뜻하는 순서는?
- 「필드를 다 채운 뒤 `init` 을 돈다」는 맞는 말인가?

### 2. ★★★ 생성자가 **몇 개** 생기고 그 안에 무엇이 오는가 (예측)

```kotlin
// icode.kt
class Box(val tag: String) {
    val first: Int = 1

    init {
        println("init A")
    }

    val second: Int = first + 1

    init {
        println("init B")
    }
}
```

- `javap -c -p -s` 로 보면 **메서드가 몇 개** 보이는가 — `init` 블록은 메서드가 되는가?
- `<init>` 안의 명령을 순서대로 읊어 보라 — `putfield` 와 `println` 이 어떻게 배치되는가?
- `Intrinsics.checkNotNullParameter` 는 `super.<init>()` **앞인가 뒤인가**?
- `second` 가 `first` 를 읽는 것은 어느 명령으로 나오는가?

### 3. ★★ 두 입구가 있을 때 각각 무엇을 하는가 (예측)

```kotlin
// sec.kt
class Box(val tag: String) {
    var extra: Int = 0

    init {
        println("init 블록")
    }

    constructor(n: Int) : this("int-$n") {
        extra = n
        println("부 생성자 본문")
    }
}
```

- `Box(int)` 의 바이트코드 **첫 명령 묶음**은 무엇인가?
- `super.<init>()`·`putfield tag`·`init` 블록은 **어느 생성자 안에** 있는가?
- `constructor(n: Int) { … }` 로 `: this(…)` 를 **빼면** 어떻게 되는가 — 에러 문구를 그대로 대 보라.
- 그 점에서 Java 의 `super()` 와 무엇이 다른가?

### 4. ★ 본 창구가 없으면 (예측)

```kotlin
// noprimary.kt
class Box {
    val a: String = say("1 프로퍼티 a")

    init {
        say("2 init 블록")
    }

    constructor(n: Int) {
        say("3 부 생성자(Int)")
    }

    constructor(s: String) : this(s.length) {
        say("4 부 생성자(String)")
    }

    private fun say(s: String): String {
        println("   $s")
        return s
    }
}

fun main() {
    println("F Box(7)")
    Box(7)
    println("G Box(\"abcd\")")
    Box("abcd")
}
```

- `F`·`G` 아래에 각각 어떤 번호들이 찍히는가?
- `G` 에서 `1`·`2` 는 **몇 번** 찍히는가 — 왜인가?
- 바이트코드로 보면 `putfield a` 와 `init` 블록은 **어느 생성자들에** 들어 있는가?
- 위임하지 않는 부 생성자가 **둘**이면 어떻게 되는가?

### 5. ★★ 창구에서 받아 적은 칸은 어디까지 보이는가 (예측)

```kotlin
// param.kt
class User(name: String, val age: Int) {
    val upper: String = name.uppercase()

    init {
        println("init 에서 name : $name")
    }

    fun greet(): String = "hi $name"
}
```

```kotlin
// capture.kt
class User(name: String) {
    val shout: String get() = name.uppercase() + "!"
}
```

- 두 파일은 각각 컴파일되는가 — **어느 줄**이 막히는가?
- `javap -p -s` 로 필드 목록을 보면 **무엇이 있고 무엇이 없는가**?
- 그 필드 목록이 에러를 어떻게 설명하는가?
- `val f: () -> String = { name.uppercase() }` 는 통과하는가 — 그때 `name` 은 **어디에** 살아남는가?

### 6. ★★★ 상급 기관이 먼저 서류를 달라고 하면 (예측)

```kotlin
// leak.kt
open class Base {
    init {
        println("   Base.init — open 함수를 부른다 : ${describe()}")
    }
    open fun describe(): String = "Base"
}

class Child(val label: String) : Base() {
    val len: Int = label.length
    override fun describe(): String = "Child(label=$label, len=$len)"
}

fun main() {
    println("D 생성 중에 무엇이 찍히나")
    val c = Child("hello")
    println("E 다 만든 뒤       : ${c.describe()}")
}
```

- `D` 아래에는 무엇이 찍히는가 — `label` 과 `len` 은 각각 무엇인가?
- `label` 의 타입은 `String`(널 불가)인데 그 값이 나오는 것이 어떻게 가능한가?
- 컴파일러는 **경고를 내는가**?
- `describe()` 를 `"len=${label.length}"` 로 바꾸면 무슨 일이 일어나는가 — 스택 트레이스의 **호출 순서**는?

### 7. `init` 을 맨 위에 두면 (경계)

- `init { println(later) }` 를 `val later` **위에** 두면 어떻게 되는가 — 에러 문구를 그대로 대 보라.
- 6번과 이것은 무엇이 다른가 — 왜 한쪽만 잡히는가?
- 그래서 `init` 의 자리는 어떻게 정해야 하는가?
- 반대로 **아래 프로퍼티가 위 프로퍼티를 읽는 것**은 되는가?

### 8. `val` 을 안 붙인 파라미터가 필드가 아닌 이유 (왜)

- `class User(name: String, val age: Int)` 에서 필드는 몇 개인가?
- 게터는 각각 무엇이 생기는가?
- 그 사실이 5번의 에러를 **문법 제약**이 아니라 무엇으로 만드는가?
- `data class` 가 주 생성자 프로퍼티만 보는 것과 이 사실은 무슨 관계인가?

### 9. `javap` 로 순서를 셀 때 빠지는 필드 (경계)

- `var extra: Int = 0` 을 둔 클래스의 `<init>` 에 `putfield extra` 가 있는가?
- `= 99` 로 바꾸면 어떻게 달라지는가?
- 왜 그런가 — 이것은 언어 보장인가 최적화인가?
- 초기화 순서를 바이트코드로 세려면 어떻게 값을 골라야 하는가?

### 10. 「모든 생성은 주 생성자를 지난다」의 예외 (경계)

- 주 생성자가 **있는** 클래스에서 그 문장은 참인가?
- 주 생성자가 **없는** 클래스에서는 어떻게 되는가?
- 그때 초기화 코드는 물리적으로 어디에 있는가?
- 그래서 주 생성자를 두는 편이 나은 이유는 무엇인가?

### 11. Java 초기화 순서와 무엇이 같고 무엇이 다른가 (연결)

- Kotlin 의 `init` 블록은 Java 의 무엇과 같은 자리인가?
- Java 는 `super()` 를 생략하면 어떻게 되고 Kotlin 은 어떻게 되는가?
- Java 에도 6번과 같은 함정이 있는가 — Kotlin 은 **무엇으로** 그 구멍을 좁혔는가?
- Kotlin 에만 있는 것은 무엇인가 — 「주 생성자」라는 개념이 무엇을 바꾸는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
