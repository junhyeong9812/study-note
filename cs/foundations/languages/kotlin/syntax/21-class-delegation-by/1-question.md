# kotlin/syntax/21 — 클래스 위임 (`by`): 상속 대신 합성 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [20번 주제](../20-interfaces-default-impl-and-super/)다.
> ★★ **`by` 라는 낱말이 두 곳에 쓰인다** — **프로퍼티 위임**(`by lazy`)은 [17번 주제](../17-delegated-properties/)가 정본이고 여기서는 묻지 않는다.
> 여기는 **클래스 위임**(`class A : B by b`)만 묻는다.
> 인터페이스와 기본 구현은 [20번 주제](../20-interfaces-default-impl-and-super/), `open`/`override` 는 [19번 주제](../19-inheritance-open-final-override/)가 정본이다.
> 문항 11개 중 코드블록이 붙는 예측형은 3개다(2·4번은 코드블록 없이 1·3번의 소스를 다시 본다).
> 바이트코드를 묻는 문항은 **`kotlinc` 기본 `-jvm-target`(1.8)** 기준이다.
> 이 주제의 모든 답은 **kotlinc 2.4.20 · JRE 21.0.5** 에서 실제로 던져 받은 것이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 오버라이드한 메서드를 위임 대상이 부르면 (예측)

```kotlin
// deleg.kt
interface Printer {
    fun printMessage()
    fun printTwice() {
        printMessage()
        printMessage()
    }
}

class BasePrinter(private val x: Int) : Printer {
    override fun printMessage() {
        println("   BasePrinter : $x")
    }
}

class Derived(base: Printer) : Printer by base {
    override fun printMessage() {
        println("   Derived : 내가 가로챘다")
    }
}

fun main() {
    val base = BasePrinter(10)
    println("A base.printTwice()")
    base.printTwice()
    println("B Derived.printMessage()")
    Derived(base).printMessage()
    println("C Derived.printTwice()  ← 함정")
    Derived(base).printTwice()
}
```

- `A`·`B`·`C` 세 구간에 각각 무엇이 찍히는가?
- `C` 가 그렇게 나오는 이유를 `this` 라는 낱말로 설명해 보라.
- 상속이었다면 `C` 는 어떻게 나왔겠는가?

### 2. ★★ `javap` 로 보면 `Derived` 는 무엇을 갖고 있나 (예측)

- 필드는 **몇 개**이고 이름은 무엇인가?
- 메서드는 몇 개이고 그중 컴파일러가 만든 것은 어느 것인가?
- `printTwice()` 의 몸통은 **몇 줄**인가 — 어떤 명령인가?
- `Derived` 는 `BasePrinter` 를 상속하는가?

### 3. ★★★ 인터페이스에 기본 구현이 있는 멤버는 포워딩되는가 (예측)

```kotlin
// count.kt
interface Repo {
    val size: Int
    var label: String
    fun add(item: String)
    fun find(key: String): String?
    fun clear()
    fun addAll(items: List<String>) {
        for (i in items) add(i)
    }
}

class MemoryRepo : Repo {
    private val items = mutableListOf<String>()
    override val size get() = items.size
    override var label = "memory"
    override fun add(item: String) { items += item }
    override fun find(key: String) = items.firstOrNull { it == key }
    override fun clear() = items.clear()
}

class LoggingRepo(private val inner: Repo) : Repo by inner {
    override fun add(item: String) {
        println("   [log] add($item)")
        inner.add(item)
    }
}

fun main() {
    val r = LoggingRepo(MemoryRepo())
    println("A 하나 넣는다")
    r.add("a")
    println("B addAll 로 둘 넣는다")
    r.addAll(listOf("b", "c"))
    println("C size=${r.size} / find(\"b\")=${r.find("b")} / label=${r.label}")
}
```

- `A`·`B`·`C` 에 각각 무엇이 찍히는가?
- `B` 줄에서 `[log]` 가 **몇 번** 찍히는가 — 왜 그런가?
- `C` 줄의 `size` 는 몇인가 — 그러면 무엇이 빠진 것인가?

### 4. ★★ 포워딩 메서드는 몇 개 생기나 (예측)

- `javap` 로 본 `Repo` 인터페이스의 멤버는 **몇 개**인가 — `val size` 와 `var label` 은 각각 몇으로 세는가?
- `LoggingRepo` 의 메서드는 몇 개이고, 그중 포워딩은 몇 개인가?
- 위임 필드의 이름은 `$$delegate_0` 인가?

### 5. ★★★ 위임 대상을 `var` 로 받아 바꾸면 (예측)

```kotlin
// fixed.kt
interface Printer {
    fun printMessage()
}

class Named(private val label: String) : Printer {
    override fun printMessage() {
        println("   Named($label)")
    }
}

class Swappable(var target: Printer) : Printer by target

fun main() {
    val first = Named("첫 번째")
    val second = Named("두 번째")
    val s = Swappable(first)
    println("A 처음")
    s.printMessage()
    s.target = second
    println("B target 을 바꾼 뒤")
    s.printMessage()
    println("C target 자체는 바뀌었나 : ${s.target === second}")
}
```

- `A`·`B`·`C` 에 각각 무엇이 찍히는가?
- 컴파일 경고는 몇 건인가?
- `javap` 로 보면 필드가 몇 개인가 — 왜 그런가?

### 6. ★ 위임 대상을 받는 방식에 따라 필드가 어떻게 달라지나 (경계)

```kotlin
// fields.kt
interface Printer {
    fun printMessage()
}

class PlainParam(base: Printer) : Printer by base
class ValParam(val base: Printer) : Printer by base
class PrivateValParam(private val base: Printer) : Printer by base
class VarParam(var base: Printer) : Printer by base
class NewEachTime : Printer by Named("현장에서 만든 것")

class Named(private val label: String) : Printer {
    override fun printMessage() = println("   Named($label)")
}
```

- 다섯 클래스에 각각 어떤 필드가 생기는가?
- `$$delegate_0` 이 **안 생기는** 경우는 언제인가?
- 어느 경우든 위임 필드에 공통으로 붙는 수식어는 무엇인가?

### 7. 인터페이스 여럿에 위임할 수 있는가 (경계)

- 필드 이름은 어떻게 되는가?
- 이것이 상속으로는 왜 안 되는가?
- 두 인터페이스에 **같은 시그니처**가 있으면 어떻게 되는가([20번 주제](../20-interfaces-default-impl-and-super/))?

### 8. 위임을 쓰면 안 되는 상황은 언제인가 (경계)

- 1번의 함정이 나는 조건을 한 문장으로 적어 보라.
- 그 조건이 성립할 때 고를 수 있는 길을 셋 대 보라.
- 이 함정이 **조용한** 이유는 무엇인가 — 예외는? 경고는? 결과값은?

### 9. `by` 가 클래스에도 되는가 (경계)

```kotlin
// forbid21.kt
open class Machine {
    open fun run() = "machine"
}

class Robot(m: Machine) : Machine by m

interface Engine {
    fun start(): String
}

class NotEngine

class Car(n: NotEngine) : Engine by n
```

- 에러는 몇 건이고 문구는 무엇인가?
- 왜 클래스에는 안 되는지 **포워딩**이라는 낱말로 설명해 보라.
- `by` 뒤의 식에는 어떤 타입만 올 수 있는가?

### 10. [17번 주제](../17-delegated-properties/)의 `by` 와 무엇이 다른가 (연결)

- 프로퍼티 위임은 무엇으로 풀리는가 — 인터페이스인가 규약인가?
- 클래스 위임은 무엇으로 풀리는가?
- 두 문법의 공통점은 무엇인가 — 낱말뿐인가, 기계도 같은가?

### 11. 상속·인터페이스·확장 함수와 어떻게 갈라 쓰나 (연결)

- [19번 주제](../19-inheritance-open-final-override/)의 상속으로 1번을 다시 쓰면 무엇이 달라지는가?
- [13번 주제](../13-extension-functions-and-properties/)의 확장 함수로 3번의 `addAll` 을 빼면 함정이 사라지는가?
- 「계층을 만들 것인가, 가질 것인가」를 가르는 기준을 한 줄로 적어 보라.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
