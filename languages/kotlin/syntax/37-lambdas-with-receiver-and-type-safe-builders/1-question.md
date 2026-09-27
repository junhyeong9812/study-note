# kotlin/syntax/37 — 리시버 지정 람다와 type-safe builder (DSL) — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [14번 주제](../14-scope-functions/)(`apply`·`with` 가 수신자 람다를 받는 것)와 [36번 주제](../36-function-types-fun-interface-and-sam-conversion/)(함수 타입이 `Function1` 인 것)다.
> 문항 11개 중 코드블록이 붙는 예측형은 6개다.
> 바이트코드를 묻는 문항은 **`kotlinc` 기본 `-jvm-target`(1.8)** 기준이다.
> 이 주제의 모든 답은 **kotlinc 2.4.20 · Temurin JDK 21.0.5** 에서 실제로 던져 받은 것이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 중첩된 빌더 — 로그와 트리 (예측)

```kotlin
// dsl.kt
open class Tag(val name: String) {
    val kids = mutableListOf<Tag>()
    protected fun <T : Tag> add(t: T, init: T.() -> Unit): T {
        println("  ${t.name}() on receiver ${this.name}")
        t.init()
        kids += t
        return t
    }
    fun dump(pad: String = ""): String = pad + name + "\n" + kids.joinToString("") { it.dump("$pad  ") }
}

class Html : Tag("html") {
    fun head(init: Head.() -> Unit) = add(Head(), init)
    fun body(init: Body.() -> Unit) = add(Body(), init)
}
class Head : Tag("head")
class Body : Tag("body") {
    fun p(init: P.() -> Unit) = add(P(), init)
}
class P : Tag("p")

fun html(init: Html.() -> Unit): Html {
    val h = Html()
    h.init()
    return h
}

fun main() {
    val doc = html {
        body {
            println("  [in body] name=$name this.name=${this.name} this@html.name=${this@html.name}")
            p { }
            head { }
        }
    }
    print(doc.dump())
}
```

- 컴파일되는가? 돌리면 로그 네 줄은 각각 무엇인가? 마지막 트리는 어떤 모양인가?

### 2. ★★★ 같은 빌더에 `@DslMarker` 를 달면 (예측)

```kotlin
// dslm.kt
@DslMarker
annotation class HtmlDsl

@HtmlDsl
open class Tag(val name: String) {
    val kids = mutableListOf<Tag>()
    protected fun <T : Tag> add(t: T, init: T.() -> Unit): T {
        println("  ${t.name}() on receiver ${this.name}")
        t.init()
        kids += t
        return t
    }
    fun dump(pad: String = ""): String = pad + name + "\n" + kids.joinToString("") { it.dump("$pad  ") }
}

class Html : Tag("html") {
    fun head(init: Head.() -> Unit) = add(Head(), init)
    fun body(init: Body.() -> Unit) = add(Body(), init)
}
class Head : Tag("head")
class Body : Tag("body") {
    fun p(init: P.() -> Unit) = add(P(), init)
}
class P : Tag("p")

fun html(init: Html.() -> Unit): Html {
    val h = Html()
    h.init()
    return h
}

fun main() {
    val doc = html {
        body {
            println("  [in body] name=$name this.name=${this.name} this@html.name=${this@html.name}")
            p { }
            head { }
        }
    }
    print(doc.dump())
}
```

- 컴파일되는가? 안 되면 **몇 번째 줄**에서 무엇이라고 말하는가? `[in body]` 줄의 `name`·`this.name`·`this@html.name` 은 막히는가?

### 3. ★★ `this@html` 라벨 (예측)

```kotlin
// dslm2.kt
@DslMarker
annotation class HtmlDsl

@HtmlDsl
open class Tag(val name: String) {
    val kids = mutableListOf<Tag>()
    protected fun <T : Tag> add(t: T, init: T.() -> Unit): T {
        println("  ${t.name}() on receiver ${this.name}")
        t.init()
        kids += t
        return t
    }
    fun dump(pad: String = ""): String = pad + name + "\n" + kids.joinToString("") { it.dump("$pad  ") }
}

class Html : Tag("html") {
    fun head(init: Head.() -> Unit) = add(Head(), init)
    fun body(init: Body.() -> Unit) = add(Body(), init)
}
class Head : Tag("head")
class Body : Tag("body") {
    fun p(init: P.() -> Unit) = add(P(), init)
}
class P : Tag("p")

fun html(init: Html.() -> Unit): Html {
    val h = Html()
    h.init()
    return h
}

fun main() {
    val doc = html {
        body {
            println("  [in body] name=$name this.name=${this.name} this@html.name=${this@html.name}")
            p { }
            this@html.head { }
        }
    }
    print(doc.dump())
}
```

- `dslm.kt` 의 37번째 줄 하나만 바꾼 파일이다. 컴파일되는가? 출력은 1번과 무엇이 다른가?

### 4. ★★ 수신자 람다를 부르는 다섯 가지 방법 (예측)

```kotlin
// recv37.kt
class A(val name: String)

fun callA(a: A, block: A.() -> Unit) { a.block() }
fun callB(a: A, block: A.() -> Unit) { block(a) }
fun callC(a: A, block: (A) -> Unit) { block(a) }

fun main() {
    val ext: A.() -> Unit = { println("  ext   this.name=${this.name}") }
    val plain: (A) -> Unit = { println("  plain it.name=${it.name}") }
    callA(A("x"), ext)
    callA(A("y"), plain)
    callC(A("z"), ext)
    ext(A("w"))
    A("v").ext()
}
```

- 컴파일되는가? 다섯 줄은 각각 무엇인가? 특히 `callA(A("y"), plain)` 과 `callC(A("z"), ext)` 는?

### 5. ★★★ `callA`·`callB`·`callC` 의 바이트코드 (예측)

- 4번의 세 함수를 `javap -c` 로 보면 몸통은 어디가 다른가? `javap -v` 에서 `ExtensionFunctionType` 이라는 글자는 **어디에** 나오는가?

### 6. ★★ 막히는 쪽과 Java 쪽 (예측)

```kotlin
// recvbad.kt
class B(val name: String)

fun callB(b: B, block: B.() -> Unit) { b.block() }

fun main() {
    callB(B("x")) { println(it.name) }
    val plain: (B) -> Unit = { println(it.name) }
    B("y").plain()
}
```

```java
// JRecv.java
import kotlin.Unit;

public class JRecv {
    public static void main(String[] args) {
        Recv37Kt.callA(new A("java"), a -> {
            System.out.println("  from Java: first argument name=" + a.getName());
            return Unit.INSTANCE;
        });
    }
}
```

- `recvbad.kt` 의 두 호출은 각각 컴파일되는가? `JRecv.java` 는 컴파일되는가 — 돌리면 무엇이 찍히는가?

### 7. 트리의 순서 (왜)

- 1번 트리에서 `head` 와 `body` 는 **소스에 적힌 순서와** 같은 순서로 붙었는가? 그 순서를 만든 줄은 `add` 의 어디인가?

### 8. `@DslMarker` 가 막는 것의 정확한 범위 (경계)

- `@DslMarker` 가 막는 것은 「바깥 수신자의 멤버」 전부인가? **암묵 수신자**와 **명시 수신자**, 그리고 **가장 안쪽 수신자**는 각각 어떻게 되는가?

### 9. JS 의 `this` 와 Kotlin 의 수신자 (연결)

- JS 의 `this` 는 호출 방식이 정한다([`../../../js/syntax/07-this-binding-four-rules/`](../../../js/syntax/07-this-binding-four-rules/)). Kotlin 수신자 람다 안의 `this` 는 **무엇이** 정하는가? 4번의 다섯 줄로 설명하면?

### 10. `apply { }` 와 `html { }` (연결)

- [14번 주제](../14-scope-functions/)의 `apply` 와 1번의 `html` 은 **같은 장치**를 쓴다. 그 장치는 무엇이고, 둘의 차이는 무엇인가?

### 11. 「DSL 은 비용이 없다」 (왜)

- 이 문서가 그 말을 **뒷받침할 수 있는가**? 5번 바이트코드가 보여 주는 것과 보여 주지 않는 것을 가르면?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
