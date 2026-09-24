# kotlin/syntax/25 — `object` 선언·`companion object`·`object` 식 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [15번 주제](../15-class-declaration-constructors-and-init/)다. [13번 주제](../13-extension-functions-and-properties/)·[16번 주제](../16-properties-backing-field-lateinit-const/)도 먼저 보면 좋다.
> ★ **`const val` 이 호출부에 박히는 것의 파급은 [16번 주제](../16-properties-backing-field-lateinit-const/)**, **상호운용 애너테이션 전부**는 목록의 **39번 주제**가 정본이라 여기서는 **결론만** 묻는다.
> 문항 11개 중 코드블록이 붙는 예측형은 6개다.
> 바이트코드를 묻는 문항은 **`kotlinc` 기본 `-jvm-target`(1.8)** 기준이다.
> ★★ 이 주제는 **Java 를 섞어 던진다** — `@JvmStatic` 은 Kotlin 쪽에서만 보면 아무것도 안 바뀐 것처럼 보이기 때문이다.
> 이 주제의 모든 답은 **kotlinc 2.4.20 · JRE 21.0.5** 에서 실제로 던져 받은 것이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 초기화 메시지가 **어느 줄 사이에** 끼는가 (예측)

```kotlin
// objinit.kt
object Registry {
    init { println("  <Registry 가 초기화된다>") }
    val name = "reg"
    fun ping() = "pong"
}

class Service {
    companion object {
        init { println("  <Service.Companion 이 초기화된다>") }
        const val VERSION = "1.0"
        val tag = "svc"
        @JvmStatic fun boot() = "booted"
    }
}

class Named {
    companion object Factory {
        fun make() = "made"
    }
}

fun main() {
    println("A 시작 — 아직 아무것도 안 건드렸다")
    println("B ${Service.VERSION}")
    println("C ${Registry.ping()}")
    println("D ${Service.tag}")
    println("E ${Service.boot()}")
    println("F ${Named.Factory.make()} ${Named.make()}")
    println("G ${Registry === Registry}")
}
```

- 출력 **전체**를 순서대로 적어 보라 — `A`\~`G` 사이 어디에 두 초기화 메시지가 끼는가?
- ★★ `B` 를 찍는 데 `Service.VERSION` 을 읽었는데 왜 그 앞뒤에 `Service.Companion` 초기화가 안 나오는가?
- `F` 에서 `Named.Factory.make()` 와 `Named.make()` 가 같은 것인가?

### 2. ★★ `javap -p` 로 보면 `object` 와 `companion` 은 무엇인가 (경계)

- `object Registry` 는 클래스 파일에서 **무엇**이 되는가? 필드 이름은?
- 생성자의 **접근자**는 무엇인가? 그렇다면 인스턴스는 누가 만드는가?
- `companion object` 에 **이름을 안 주면** 필드 이름이 무엇이 되는가? 주면?
- ★ 이중 검사 잠금 코드가 **안 보이는** 이유는 무엇인가?

### 3. ★ `const val` 과 companion 의 `val` 은 **각각 어디에 사는가** (경계)

- 1번의 `Service` 를 `javap -v` 로 보면 `VERSION` 에 무슨 **속성**이 붙어 있는가?
- companion 의 `tag` 는 **어느 클래스의** 필드인가? 그 접근자는 어디 있는가?
- `access$getTag$cp()` 는 무엇을 하려고 생긴 것인가?

### 4. ★★ `object` 식의 타입은 어디까지 보이는가 (예측)

```kotlin
// objexpr.kt
interface Greeter { fun greet(): String }

class Holder {
    private fun priv() = object { val extra = "priv-extra" }
    fun usePriv(): String = priv().extra
}

fun localScope(): String {
    val anon = object : Greeter {
        val extra = "local-extra"
        override fun greet() = "hi"
    }
    return "${anon.greet()}/${anon.extra}"
}

fun declared(): Greeter = object : Greeter {
    val extra = "안 보인다"
    override fun greet() = "hi2"
}

fun counterFactory(): Greeter {
    var n = 0
    return object : Greeter {
        override fun greet(): String { n++; return "호출 $n 번째" }
    }
}

fun main() {
    println("A ${localScope()}")
    println("B ${Holder().usePriv()}")
    println("C ${declared().greet()}")
    val c = counterFactory()
    println("D ${c.greet()} ${c.greet()}")
    println("E ${counterFactory().greet()}")
    println("F ${c === counterFactory()}")
    println("G ${declared().javaClass.name}")
}
```

- `A`\~`G` 에 각각 무엇이 찍히는가?
- `B` 는 `private` 함수가 돌려준 익명 객체의 멤버다. 왜 읽을 수 있는가?
- ★★ `D`·`E`·`F` 를 묶어서 — `object` 식이 만드는 인스턴스는 **몇 개**인가?
- `G` 의 이름은 어떤 규칙으로 붙는가?

### 5. ★★ 공개 함수가 익명 객체를 돌려주면 (예측)

```kotlin
// objexprbad.kt
class Holder {
    fun pub() = object { val extra = "pub-extra" }
}

interface Greeter { fun greet(): String }

fun declared(): Greeter = object : Greeter {
    val extra = "x"
    override fun greet() = "hi"
}

fun main() {
    println(Holder().pub().extra)
    println(declared().extra)
}
```

- 컴파일되는가? 에러가 **몇 줄**인가?
- 두 에러의 `receiver of type ...` 자리에 각각 무엇이 오는가? **왜 서로 다른가**?
- 「익명 타입은 어디까지 산다」를 한 줄로 적어 보라.

### 6. ★ `object` 에 붙일 수 없는 것 (예측)

```kotlin
// objforbid.kt
object Box<T> {
    fun get(): T? = null
}

class Outer {
    inner companion object
}

class Two {
    companion object A
    companion object B
}

object WithCtor(val x: Int)
```

- 에러가 **몇 줄**이고 각각 무엇을 말하는가?
- ★ `object` 가 타입 파라미터를 못 받는 이유를 「인스턴스가 하나」와 엮어 설명해 보라.
- 제네릭이 필요하면 어떻게 우회하는가?

### 7. ★★ Java 에서 부르면 (예측)

```kotlin
// objjava.kt
object Single {
    const val TAG = "single"
    fun hello() = "obj-hello"
    @JvmStatic fun staticHello() = "obj-static-hello"
}

class Svc {
    companion object {
        const val VERSION = "9.9"
        val tag = "svc-tag"
        fun plain() = "companion-plain"
        @JvmStatic fun jvmStatic() = "companion-jvmstatic"
    }
}
```

```java
// UseIt.java
public class UseIt {
    public static void main(String[] args) {
        System.out.println("A " + Single.INSTANCE.hello());
        System.out.println("B " + Single.staticHello());
        System.out.println("C " + Single.TAG);
        System.out.println("D " + Svc.Companion.plain());
        System.out.println("E " + Svc.jvmStatic());
        System.out.println("F " + Svc.VERSION);
        System.out.println("G " + Svc.Companion.getTag());
    }
}
```

- `javac` 가 통과하는가? 통과한다면 `A`\~`G` 에 각각 무엇이 찍히는가?
- `Single.INSTANCE.hello()` 와 `Single.staticHello()` 는 **무엇이 다른가**?
- `Svc.Companion.plain()` 과 `Svc.jvmStatic()` 은 **무엇이 다른가**?

### 8. ★★ Java 에서 **못** 부르는 것 (예측)

```java
// BadUse.java
public class BadUse {
    public static void main(String[] args) {
        System.out.println(Single.hello());
        System.out.println(Svc.plain());
        System.out.println(Svc.getTag());
    }
}
```

- `javac` 에러가 **몇 줄**인가?
- ★★ 세 줄의 문구가 **둘로 갈린다.** 어떻게 갈리고, 그 차이가 무엇을 말하는가?
- 이것을 고치려면 Kotlin 쪽에 무엇을 적는가?

### 9. `companion object` 가 `static` 이 **아닌** 것이 무엇을 가능하게 하나 (왜)

- `static` 멤버로는 할 수 없는데 `companion object` 로는 되는 것을 **셋** 대 보라.
- 그 대가는 무엇인가 — 7번·8번의 결과로 답해 보라.
- `@JvmStatic` 은 그 대가를 어떻게 되사는가?

### 10. `object` 안의 가변 상태 (경계)

- `object` 에 `var` 를 두면 그 값을 **누가 공유**하는가?
- 테스트 사이에 상태가 남는 문제는 이것과 어떻게 이어지는가?
- 「싱글턴이라 편하다」와 「전역이라 위험하다」가 왜 같은 사실인가?

### 11. `enum` 상수·`data object` 와 같은 집안인 것 (연결)

- [24번 주제](../24-enum-class-vs-sealed/)의 `enum` 상수는 클래스 파일에서 무엇이었는가? `object` 와 무엇이 같은가?
- [22번 주제](../22-data-class-generated-members/)의 `data object` 는 그냥 `object` 에 **무엇**을 더한 것인가?
- [`../../../java/syntax/12-nested-classes/`](../../../java/syntax/12-nested-classes/)의 정적 중첩 클래스와 `Outer$Companion` 은 어떤 관계인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
