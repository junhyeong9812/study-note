# kotlin/syntax/20 — 인터페이스: 기본 구현·프로퍼티 선언·충돌 해소(`super<T>`) — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [19번 주제](../19-inheritance-open-final-override/)다. 이 주제는 [21번 주제](../21-class-delegation-by/)의 뿌리다.
> ★ **backing field 는 [16번 주제](../16-properties-backing-field-lateinit-const/)**, `open`/`override` 의 기본값은 [19번 주제](../19-inheritance-open-final-override/),
> `sealed interface` 와 `when` 완결성은 목록의 **23번 주제**, `fun interface` 는 목록의 **36번 주제**가 정본이다.
> 문항 12개 중 코드블록이 붙는 예측형은 6개다.
> ★★ 바이트코드를 묻는 문항은 **`kotlinc` 기본 `-jvm-target`(1.8)** 과 **기본 `-jvm-default`** 기준이다 — 뒤엣것을 안 밝히면 답이 셋으로 갈린다.
> 이 주제의 모든 답은 **kotlinc 2.4.20 · JRE 21.0.5** 에서 실제로 던져 받은 것이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★ 두 구현 클래스가 각각 무엇을 물려받나 (예측)

```kotlin
// greet.kt
interface Greeter {
    val name: String
    val shout: String
        get() = name.uppercase()

    fun greet(): String = "안녕, $name"
    fun mustImplement(): Int
}

class Korean(override val name: String) : Greeter {
    override fun mustImplement() = name.length
}

class Loud(override val name: String) : Greeter {
    override fun greet(): String = "${super.greet()}!!!"
    override fun mustImplement() = -1
}

fun main() {
    val k = Korean("준")
    println("A ${k.greet()} / ${k.shout} / ${k.mustImplement()}")
    val l = Loud("jun")
    println("B ${l.greet()} / ${l.shout} / ${l.mustImplement()}")
}
```

- `A`·`B` 두 줄에 각각 무엇이 찍히는가?
- `Korean` 은 `greet()` 와 `shout` 를 안 적었는데 왜 컴파일되는가?
- `Loud` 의 `super.greet()` 는 무엇을 부르는가 — 꺾쇠가 왜 필요 없는가?
- `shout` 는 값을 어디에 저장하는가?

### 2. ★★ 인터페이스에 값을 넣으려 하면 (예측)

```kotlin
// ifacebad.kt
interface Config {
    val url: String = "https://example.com"

    init {
        println("인터페이스 init")
    }

    constructor(x: Int)
}
```

```kotlin
// ifacefield.kt
interface Counter {
    var count: Int
        get() = field
        set(v) { field = v }
}
```

- 에러는 각각 몇 건이고 문구는 무엇인가?
- 이 넷이 **한 덩어리**인 이유를 한 문장으로 말해 보라.
- 그럼 인터페이스 프로퍼티는 어떤 형태만 가능한가?

### 3. ★★★ 같은 시그니처를 둘에서 물려받으면 (예측)

```kotlin
// diamond.kt
interface Walker {
    fun move() = "걷는다"
}

interface Swimmer {
    fun move() = "헤엄친다"
}

class Duck : Walker, Swimmer

fun main() {
    println(Duck().move())
}
```

- 컴파일되는가? 된다면 무엇이 찍히고, 안 된다면 문구는 무엇인가?
- 컴파일러가 **하나를 골라 주지 않는** 이유는 무엇인가?
- 고치는 문법은 무엇인가?

### 4. ★★ `super<T>` 로 고쳤을 때 (예측)

```kotlin
// diamondfix.kt
interface Walker {
    fun move() = "걷는다"
    fun legs(): Int = 2
}

interface Swimmer {
    fun move() = "헤엄친다"
}

class Duck : Walker, Swimmer {
    override fun move() = "${super<Walker>.move()} / ${super<Swimmer>.move()}"
}

class Fish : Swimmer

fun main() {
    println("A ${Duck().move()}")
    println("B ${Duck().legs()}")
    println("C ${Fish().move()}")
    val w: Walker = Duck()
    val s: Swimmer = Duck()
    println("D ${w.move()} / ${s.move()}")
}
```

- `A`\~`D` 네 줄에 각각 무엇이 찍히는가?
- `legs()` 는 왜 아무것도 안 적어도 되는가?
- `D` 줄에서 `Walker` 타입으로 보는 것과 `Swimmer` 타입으로 보는 것이 갈리는가?

### 5. ★★★ 상위 클래스와 인터페이스가 같은 메서드를 가지면 (예측)

```kotlin
// clsiface.kt
open class Animal {
    open fun move() = "클래스 : 네 발로 간다"
}

interface Walker {
    fun move() = "인터페이스 : 걷는다"
}

class Dog : Animal(), Walker

fun main() {
    println(Dog().move())
}
```

- 컴파일되는가? Java 에서 같은 모양은 어떻게 되는가?
- 에러라면 3번과 **같은 문구**인가?
- 「클래스가 이긴다」는 규칙이 이 언어에 있는가?

### 6. ★★★ `javap` 로 본 인터페이스 — 기본 구현은 무엇이 되나 (예측)

- `ogreet` 디렉토리에 클래스 파일이 **몇 개** 생기는가? 이름은?
- `javap -p Greeter.class` 에서 `greet()` 는 `abstract` 인가 `default` 인가?
- 구현 클래스 `Korean` 에 `greet()` 가 **있는가**?
- `access$greet$jd` 는 무엇인가?

### 7. `-jvm-default` 세 값이 무엇을 바꾸는가 (경계)

- `enable`(기본)·`no-compatibility`·`disable` 에서 **인터페이스·`DefaultImpls`·구현 클래스** 세 자리가 각각 어떻게 달라지는가?
- 포워딩 메서드가 `invokespecial` 을 쓰는 판과 `invokestatic` 을 쓰는 판은 각각 어느 것인가?
- 「`DefaultImpls` 가 생긴다」는 지식은 지금도 맞는가?

### 8. ★★ Java 클래스가 이 인터페이스를 구현하면 (경계)

```java
// JavaGreeter.java
public class JavaGreeter implements Greeter {
    public String getName() { return "java"; }
    public int mustImplement() { return 0; }

    public static void main(String[] args) {
        JavaGreeter g = new JavaGreeter();
        System.out.println("A " + g.greet());
        System.out.println("B " + g.getShout());
    }
}
```

- 기본값으로 컴파일한 인터페이스에 대해 `javac` 는 통과하는가?
- `-jvm-default=disable` 로 컴파일한 인터페이스에 대해서는?
- Java 파일은 **한 글자도 안 바뀌었는데** 결과가 갈린다면, 갈린 것은 무엇인가?

### 9. 인터페이스가 상태를 못 가지는 이유는 무엇인가 (왜)

- 「저장할 자리」와 「채울 시점」의 관계를 한 문장으로 적어 보라.
- 한 클래스가 인터페이스를 셋 구현하면 **생성자가 몇 번** 돌아야 하는가?
- 그래서 [16번 주제](../16-properties-backing-field-lateinit-const/)의 축(필드 유무)에서 인터페이스 프로퍼티는 어느 칸인가?

### 10. 인터페이스 멤버의 기본값은 무엇인가 (경계)

- 인터페이스 멤버에 `open` 을 적어야 하는가?
- [19번 주제](../19-inheritance-open-final-override/)의 클래스 멤버와 비교하면 어느 쪽이 기본으로 열려 있는가?
- 인터페이스 멤버를 `final` 로 잠글 수 있는가?

### 11. ★ 인터페이스에 둘 수 있는 것과 없는 것 (경계)

```kotlin
// form20.kt
interface Named {
    val name: String
    val upper: String
        get() = name.uppercase()

    fun hello(): String = "hi " + decorate(name)
    fun must(): Int

    private fun decorate(s: String) = "<$s>"

    companion object {
        const val TAG = "Named"
    }
}

class Impl(override val name: String) : Named {
    override fun must() = name.length
}

fun main() {
    val i = Impl("kim")
    println("Z ${i.hello()} ${i.upper} ${i.must()} ${Named.TAG}")
}
```

- `private fun decorate` 는 되는가?
- `companion object` 는 되는가?
- 이 둘이 되는데 `init` 이 안 되는 이유는 무엇인가?

### 12. 확장 함수·위임과 어떻게 갈라 쓰나 (연결)

- [13번 주제](../13-extension-functions-and-properties/)의 확장 함수로 4번의 `D` 줄을 대신하면 무엇이 달라지는가?
- [21번 주제](../21-class-delegation-by/)의 위임은 이 주제의 무엇을 대신해 주는가?
- 「인터페이스 / 추상 클래스 / 확장 함수 / 위임」 네 갈래를 고르는 기준을 한 줄씩 적어 보라.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
