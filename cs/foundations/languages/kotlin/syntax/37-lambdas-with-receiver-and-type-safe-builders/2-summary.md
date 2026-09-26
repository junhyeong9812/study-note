# kotlin/syntax/37 — 리시버 지정 람다와 type-safe builder (DSL) — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Type-safe builders](https://kotlinlang.org/docs/type-safe-builders.html)(「The type of the function is `HTML.() -> Unit`, which is a function type with receiver」 · Scope control: `@DslMarker` — 「a member of outer receiver」 호출을 에러로 · 「`this@html.head { }` // possible」) · [Function literals with receiver](https://kotlinlang.org/docs/lambdas.html#function-literals-with-receiver).
> **실행 검증** — 이 문서의 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javac`·`java`·`javap` 에서 실제로 얻었다.\
> `kotlinc` 6회(컴파일 실패 2벌) · `javac` 1회 · `java` 5회 · `javap` 2회.\
> ★★ 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적지 않았다. **「수신자가 누구인가」는 전부 프로그램이 스스로 찍은 로그**다.
> **버전** — 수신자 있는 함수 타입·type-safe builder 는 1.0, `@DslMarker` 의 **도입 판은 확인하지 않았다**(이 판은 `-language-version 2.0` 미만을 거부해 잴 수도 없다 — [36번 주제](../36-function-types-fun-interface-and-sam-conversion/) (6)). ★ `@DslMarker` 의 진단 문구는 **이 판(K2)의 것**이다((2)).
> **경계** — ★★ **`T.() -> R` 과 `(T) -> R` 이 JVM 에서 둘 다 `Function1` 이고 디스크립터가 같다**는 것은 [14번 주제](../14-scope-functions/) (2)가 stdlib 의 `run`/`with` 로 이미 보였고, 「수신자가 **첫 파라미터**로 내려간다」는 [10번 주제](../10-lambdas-and-higher-order-functions/) (1)이 `fRecv` 로 보였다 — 여기서는 **다시 재지 않고**, **호출 자리**(`a.block()` 대 `block(a)`)와 **Java 쪽**만 더한다((4)(5)).\
> 확장 함수의 정적 디스패치는 [13번 주제](../13-extension-functions-and-properties/)가, `apply`/`with` 의 고르는 법은 [14번 주제](../14-scope-functions/)가, 함수 타입과 `Function1` 은 [36번 주제](../36-function-types-fun-interface-and-sam-conversion/)가 정본이다. **DSL 이 왜 Kotlin 의 강점인가**라는 논지는 [`../../언어-특성/README.md`](../../언어-특성/README.md) §7 이다. 암묵 인자를 **타입으로** 넘기는 다음 단계(context parameters)는 목록의 **38번 주제**다.\
> ★ **대비** — JS 의 `this` 는 **호출 방식**이 정한다([`../../../js/syntax/07-this-binding-four-rules/`](../../../js/syntax/07-this-binding-four-rules/)) — Kotlin 수신자는 **타입과 호출자가 넘긴 값**이 정한다((4)).
> 이 본문은 Claude 작성이다(원고 없음).

★★★ **본체는 첫째 창이다** — 「**빌더가 스스로 찍은 로그 — `head()` 가 어느 수신자 위에서 불렸나**」. 중첩 DSL 의 사고는 **컴파일도 되고 예외도 안 나서** 출력의 **트리 모양**으로만 드러난다. 둘째 창(`@DslMarker` 의 컴파일 에러)이 그것을 **막는 장치**다.

## 이 주제가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **언어 보장** | 명세·공식 문서가 약속한 것 | ★★★ `A.() -> Unit` 안에서 **`this` 는 넘겨받은 `A`** · 암묵 수신자는 **안쪽부터** 찾는다 · ★★ **바깥 수신자의 멤버도 부를 수 있다**(그래서 사고가 난다) · `@DslMarker` 는 **표시된 수신자끼리** 바깥 것을 암묵으로 못 부르게 한다 · `this@라벨` |
| **구현(JVM 백엔드)** | kotlinc 가 JVM 으로 내리는 방식 | `A.() -> Unit` → **`Function1<? super A, Unit>`** · `a.block()` 과 `block(a)` 가 **같은 명령** · 「수신자가 있다」는 사실은 **메타데이터의 `ExtensionFunctionType`** 에만 |
| **이 판의 관찰** | kotlinc 2.4.20 에서 이번에 본 것 | ★ `@DslMarker` 진단 문구(「`cannot be called in this context with an implicit receiver`」) |

## 이 판

```text
===== kotlinc -version =====
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | (이 주제에는 없다) | 해시코드·주소를 찍지 않았다 — 수신자는 **`name` 문자열**로 가렸다 |
| 안 흔들린다 | 빌더 로그 · 트리 | 순서가 **호출 순서**로 정해진다(단일 스레드) |
| 안 흔들린다 | `javap` 출력 · 진단 문구·`파일:줄:칸` | 결정적이다 |

★ 근거 — 캡처 스크립트를 처음부터 두 번 돌려 **블록 전체를 바이트 단위로 대조**했다(수치는 3-answer 의 「실행 검증」).

## 한눈에 — 쉽게 말하면

**수신자 람다는 「어느 방 안에서 하는 말인가」를 정해 둔 지시서다.** `body { p { } }` 는 「body 방에 들어가서 p 를 놓아라」다. 방 안에서 **이름만 부르면**(`p()`) 그 방의 물건이 먼저 대답한다.
★ 그런데 **방은 복도로 이어져 있다** — 지금 방(body)에 `head` 가 없으면 컴파일러는 **바깥 방(html)의 `head`** 를 찾아 준다. 소리 없이. 그래서 body 안에 쓴 `head { }` 가 **html 에 붙는다.**
**`@DslMarker` 는 방문을 잠그는 것이다** — 표시된 방끼리는 **바깥 방의 물건을 이름만으로** 못 부른다. 꼭 부르려면 **방 이름을 대고**(`this@html.head { }`) 부른다.

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 어느 방 안에서 하는 말인가 | 수신자 있는 함수 타입 `Body.() -> Unit` | (1) |
| 이름만 부르면 지금 방이 먼저 | 암묵 수신자 — **안쪽부터** | (1) |
| 복도로 이어진 바깥 방 | 바깥 암묵 수신자 — **여전히 보인다** | (1) ★ |
| 방문 잠그기 | `@DslMarker` | (2) |
| 방 이름을 대고 부르기 | `this@html` | (3) |
| 지시서의 정체 | `Function1<Body, Unit>` — **첫 인자가 방** | (4)(5) |

```text
   html {                         암묵 수신자 목록(안쪽이 위)       head() 를 찾는 순서
     body {                       +-----------------+
       p { }                      | Body   ← this   |   1. Body 에 head 가 있나?  없다
       head { }   ───────────────>| Html   ← this@html| 2. Html 에 head 가 있나?  있다 ★ → Html.head
     }                            +-----------------+
   }                                                       → 「head() on receiver html」

   @DslMarker 를 두 클래스(의 공통 조상)에 달면
                                  | Body   ← this   |   1. Body 에 없다
                                  | Html   ← (잠김) |   2. 표시된 바깥 수신자는 암묵으로 안 본다
                                                           → 컴파일 에러 · this@html.head { } 는 허용
```

## 이 주제가 답하려는 질문

1. `A.() -> Unit` 람다 안에서 **`this` 와 이름만 부른 호출은 어느 객체로** 가나 — 중첩되면.
2. 중첩 DSL 에서 **바깥 수신자의 메서드가 안쪽에서 불리는 사고**는 어떻게 생기고, `@DslMarker` 는 **정확히 무엇을** 막나.
3. `A.() -> Unit` 은 **JVM 에서 무엇**이고, `(A) -> Unit` 과 **어디가** 다른가.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **빌더의 자기 로그 + 트리** | 어느 수신자 위에서 불렸나 · 무엇이 **어디에 붙었나**((1)(3)) | ★ **본체 창** |
| ★★ **컴파일 에러** | `@DslMarker` 가 막은 줄((2)) · 수신자 람다와 일반 람다의 경계((5)) | 이 갈래의 기본 창 |
| ★★ **`javap -c` — 세 호출 몸통 대조** | `a.block()` · `block(a)` · `(A) -> Unit` 이 **같은 명령**((4)) | 이 갈래의 기본 창 |
| ★ **`javap -v` 의 메타데이터 문자열** | 「수신자가 있다」가 **어디에만** 남나((4)) | [14번 주제](../14-scope-functions/) (2)의 결론을 호출 자리에서 |
| ★ **Java 에서 던지기** | Java 람다의 **첫 매개변수**가 수신자((5)) | [36번 주제](../36-function-types-fun-interface-and-sam-conversion/) (2)의 창 |
| **부적용 — 실행 시간** | 「DSL 은 비용이 없다」·「빌더가 느리다」는 **재지 않았다** | — |
| **부적용 — 할당 계수** | 빌더가 만드는 람다·노드 객체 수는 이 주제의 질문이 아니다 | — |

### (1) ★★★ 중첩 빌더 — `head()` 는 어느 수신자로 갔나

**언제 쓰나** — HTML·설정·테스트 DSL 에서 **블록을 잘못 닫았거나 잘못된 블록 안에** 썼을 때.

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

```text
===== kotlinc dsl.kt -d o37d =====
(exit 0)
===== java -cp o37d:kotlin-stdlib.jar DslKt =====
  body() on receiver html
  [in body] name=body this.name=body this@html.name=html
  p() on receiver body
  head() on receiver html
html
  head
  body
    p
(exit 0)
```

- ★★★ **`head() on receiver html`** — `body { … }` **안에서** 쓴 `head { }` 가 **`Html` 의 `head`** 로 갔다. `Body` 에는 `head` 가 없으니 컴파일러가 **바깥 암묵 수신자** `Html` 에서 찾았다. **컴파일 에러도 경고도 없다**(`kotlinc … (exit 0)`).
- ★★★ **트리가 그 사실을 드러낸다** — `head` 가 `body` 의 자식이 아니라 **`html` 의 자식**이고, 게다가 **`body` 보다 앞**이다. 소스의 모양(`body` 안의 `head`)과 결과가 **둘 다** 다르다.
- ★★ **`p() on receiver body`** — `p` 는 `Body` 에 있으니 **안쪽**이 대답했다. 암묵 수신자는 **안쪽부터** 찾는다.
- ★★ **`[in body] name=body this.name=body this@html.name=html`** — 이름만 쓴 `name` 도 **안쪽**(`Body`)이다. `this` 는 **가장 안쪽 수신자**이고, 바깥은 **`this@html`**(람다를 받은 함수 이름이 라벨)로 부른다.
- ★ **왜 `head` 가 `body` 보다 앞인가** — `add` 가 **`t.init()` 을 먼저 돌리고 `kids += t` 를 나중에** 한다. `body` 의 블록이 도는 **도중에** `head` 가 `html.kids` 에 먼저 들어갔고, `body` 는 블록이 **끝난 뒤** 들어갔다.

### (2) ★★★ `@DslMarker` — 바깥 수신자를 암묵으로 못 부르게

**언제 쓰나** — (1)의 사고를 **컴파일 시점에** 막고 싶을 때. 바뀐 것은 파일 첫머리의 애너테이션 선언과 `Tag` 위의 `@HtmlDsl` 한 줄뿐이다.

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

```text
===== kotlinc dslm.kt -d o37m =====
dslm.kt:37:13: error: 'fun head(init: Head.() -> Unit): Head' cannot be called in this context with an implicit receiver. Use an explicit receiver if necessary.
            head { }
            ^^^^
(exit 1)
```

- ★★★ **「`'fun head(init: Head.() -> Unit): Head' cannot be called in this context with an implicit receiver. Use an explicit receiver if necessary.`」** — 37번째 줄 `head { }` 하나만 막혔다.
- ★★ **같은 블록의 `name`·`this.name`·`this@html.name`(35번째 줄)은 안 막혔다.** `name` 은 **가장 안쪽 수신자**(`Body`)의 것이고, `this@html.name` 은 **명시 수신자**다. `@DslMarker` 가 막는 것은 「**표시된 바깥 수신자를 암묵으로**」 쓰는 것 하나다.
- ★★ **`Tag` 한 곳에 달았는데 네 클래스 전부가 표시됐다** — 마커는 **상위 타입에서 상속**된다. 공통 조상 하나에 다는 것이 관용이다.
- ★ 브리핑의 문구 「`can't be called in this context by implicit receiver`」는 **이 판의 문구가 아니다** — 2.4.20 은 「`cannot be called in this context with an implicit receiver`」다. 진단 문구는 판에 매인다.

### (3) ★★ `this@html` — 바깥 수신자를 **명시해서** 부르기

(2)의 37번째 줄 하나만 `this@html.head { }` 로 바꿨다.

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

```text
===== kotlinc dslm2.kt -d o37l =====
(exit 0)
===== java -cp o37l:kotlin-stdlib.jar Dslm2Kt =====
  body() on receiver html
  [in body] name=body this.name=body this@html.name=html
  p() on receiver body
  head() on receiver html
html
  head
  body
    p
(exit 0)
```

- ★★★ **컴파일되고, 출력이 (1)과 한 글자도 같다** — `head() on receiver html` · 트리도 같다. `@DslMarker` 는 **동작을 바꾸지 않는다** — 암묵 호출을 **명시 호출로 적게** 만들 뿐이다.
- ★ 그러니 `@DslMarker` 로 막은 뒤 `this@html.` 을 붙여 **그냥 통과시키면** 사고는 그대로다. 에러가 말하는 것은 「**여기서 `head` 를 부르는 게 맞나**」라는 질문이다.

### (4) ★★ `A.() -> Unit` 의 정체 — 호출 자리와 JVM

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

```text
===== kotlinc recv37.kt -d o37r =====
(exit 0)
===== java -cp o37r:kotlin-stdlib.jar Recv37Kt =====
  ext   this.name=x
  plain it.name=y
  ext   this.name=z
  ext   this.name=w
  ext   this.name=v
(exit 0)
```

```text
===== javap -c -p o37r/Recv37Kt.class | awk '/ call[ABC]\(/,/^$/' =====
  public static final void callA(A, kotlin.jvm.functions.Function1<? super A, kotlin.Unit>);
    Code:
       0: aload_0
       1: ldc           #10                 // String a
       3: invokestatic  #16                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_1
       7: ldc           #18                 // String block
       9: invokestatic  #16                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
      12: aload_1
      13: aload_0
      14: invokeinterface #24,  2           // InterfaceMethod kotlin/jvm/functions/Function1.invoke:(Ljava/lang/Object;)Ljava/lang/Object;
      19: pop
      20: return

  public static final void callB(A, kotlin.jvm.functions.Function1<? super A, kotlin.Unit>);
    Code:
       0: aload_0
       1: ldc           #10                 // String a
       3: invokestatic  #16                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_1
       7: ldc           #18                 // String block
       9: invokestatic  #16                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
      12: aload_1
      13: aload_0
      14: invokeinterface #24,  2           // InterfaceMethod kotlin/jvm/functions/Function1.invoke:(Ljava/lang/Object;)Ljava/lang/Object;
      19: pop
      20: return

  public static final void callC(A, kotlin.jvm.functions.Function1<? super A, kotlin.Unit>);
    Code:
       0: aload_0
       1: ldc           #10                 // String a
       3: invokestatic  #16                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_1
       7: ldc           #18                 // String block
       9: invokestatic  #16                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
      12: aload_1
      13: aload_0
      14: invokeinterface #24,  2           // InterfaceMethod kotlin/jvm/functions/Function1.invoke:(Ljava/lang/Object;)Ljava/lang/Object;
      19: pop
      20: return
(exit 0)
```

```text
===== javap -v -p o37r/Recv37Kt.class | grep -E 'ExtensionFunctionType' =====
  #134 = Utf8               Lkotlin/ExtensionFunctionType;
      d2=["callA","","a","LA;","block","Lkotlin/Function1;","Lkotlin/ExtensionFunctionType;","callB","callC","main"]
(exit 0)
```

```text
   Kotlin 소스            번역                    JVM
   a.block()       ───>   block.invoke(a)   ───>  aload block ; aload a ; invokeinterface Function1.invoke
   block(a)        ───>   block.invoke(a)   ───>  (한 글자도 같다)
   Java a -> {…}   ───>   Function1<A, Unit> 를 구현하는 람다 — a 가 첫 매개변수 · Unit.INSTANCE 반환
   「수신자가 있다」 ───>  명령에도 디스크립터에도 없다 — 메타데이터 d2 의 ExtensionFunctionType 한 칸
```

- ★★★ **`callA`(`a.block()`) · `callB`(`block(a)`) · `callC`(`(A) -> Unit` 을 `block(a)`)의 몸통이 한 글자도 같다** — `12: aload_1`(블록) · `13: aload_0`(**`a`**) · `14: invokeinterface Function1.invoke`. **수신자는 `invoke` 의 첫 인자**다. 서명도 셋 다 `Function1<? super A, kotlin.Unit>`.
- ★★ **「수신자가 있다」는 사실은 메타데이터 문자열에만 있다** — `d2=[…,"Lkotlin/ExtensionFunctionType;",…]`. 명령에도 디스크립터에도 없다. [14번 주제](../14-scope-functions/) (2)가 stdlib 의 `run`/`with` 로 본 결론을 **내 함수의 호출 자리**에서 다시 확인한 것이다.
- ★★ **다섯 줄이 전부 돈다** — `ext` 를 `callA`(수신자 자리)에도 `callC`(일반 자리)에도 넘길 수 있고, `plain`(일반)을 `callA`(수신자 자리)에 넘길 수도 있다. **값끼리는 서로 대입된다.** `ext(A("w"))` 와 `A("v").ext()` 도 같다.
- ★ 그래서 **`this` 를 정하는 것은 호출자가 넘긴 값**이다 — `callA(A("x"), ext)` 에서 `this.name=x`, `callC(A("z"), ext)` 에서 `z`. JS 처럼 **호출 문법**(`obj.f()` 대 `f()`)이 `this` 를 바꾸는 것이 아니라, **첫 인자로 무엇이 들어갔나**가 정한다((1)의 `this` 는 빌더가 `h.init()` 으로 넘긴 `h` 다).

### (5) ★★ 경계 — 막히는 쪽과 Java 쪽

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

```text
===== kotlinc recvbad.kt -d o37b =====
recvbad.kt:6:29: error: unresolved reference 'it'.
    callB(B("x")) { println(it.name) }
                            ^^
recvbad.kt:8:12: error: unresolved reference 'plain' on receiver of type 'B'.
    B("y").plain()
           ^^^^^
(exit 1)
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

```text
===== javac -cp o37r:kotlin-stdlib.jar -d o37r JRecv.java =====
(exit 0)
===== java -cp o37r:kotlin-stdlib.jar JRecv =====
  from Java: first argument name=java
(exit 0)
```

- ★★★ **람다 리터럴에서는 두 형태가 갈린다** — 수신자 자리의 람다에서 `it` 은 「`unresolved reference 'it'.`」 **값끼리는 대입되지만((4)), 리터럴 안에서는 `this` 와 `it` 이 다른 이름**이다.
- ★★ **`B("y").plain()` 도 막힌다** — 「`unresolved reference 'plain' on receiver of type 'B'.`」 일반 함수 타입 값은 **수신자 문법으로 부를 수 없다.** (4)의 `A("v").ext()` 와 대칭이 아니다.
- ★★ **Java 는 첫 매개변수로 받는다** — `a -> { … a.getName() …; return Unit.INSTANCE; }`. Java 에게 `A.() -> Unit` 은 **`Function1<A, Unit>`** 일 뿐이라 수신자가 **평범한 첫 인자**다. `Unit` 을 돌려주는 것까지 적어야 한다.

## 문법 — 형태와 규칙

**형태** — `@DslMarker` 를 단 두 단계 빌더의 최소 예제다.

```kotlin
// form37.kt
@DslMarker
annotation class MenuDsl

@MenuDsl
class Group(val title: String) {
    val items = mutableListOf<String>()
    fun item(name: String) { items += name }
}

@MenuDsl
class Menu {
    val lines = mutableListOf<String>()
    fun item(name: String) { lines += name }
    fun group(title: String, init: Group.() -> Unit) {
        val g = Group(title).apply(init)
        lines += "${g.title}: ${g.items}"
    }
}

fun menu(init: Menu.() -> Unit): Menu = Menu().apply(init)

fun main() {
    val m = menu {
        item("open")
        group("recent") {
            item("a.txt")
            item("b.txt")
        }
    }
    println(m.lines)
}
```

```text
===== kotlinc form37.kt -d o37z =====
(exit 0)
===== java -cp o37z:kotlin-stdlib.jar Form37Kt =====
[open, recent: [a.txt, b.txt]]
(exit 0)
```

**규칙 불릿**

- 수신자 있는 함수 타입 **`A.() -> R`** — 람다 안에서 `this` 는 `A`, `A` 의 멤버를 **이름만으로** 부른다((1)).
- 부르는 쪽은 **`a.block()`** 또는 **`block(a)`** — 같은 호출이다((4)).
- 암묵 수신자는 **안쪽부터** 찾고, 없으면 **바깥 수신자**로 넘어간다 — ★ 사고의 원천((1)).
- **`@DslMarker`** 를 단 애너테이션을 빌더 클래스(또는 공통 조상)에 달면, **표시된 바깥 수신자를 암묵으로** 못 부른다((2)).
- 바깥 수신자는 **`this@라벨`** — 라벨은 람다를 받은 **함수 이름**이다((1)(3)).
- `A.() -> R` 값과 `(A) -> R` 값은 **서로 대입된다** — 리터럴 안의 `this`/`it` 과 **수신자 호출 문법**은 갈린다((4)(5)).

## 어디서 틀리나

1. ★★★ **중첩 블록 안의 호출이 그 블록에 붙는다고 믿는다.** 안쪽에 없으면 **바깥 것이 조용히** 불린다((1)) — 트리를 찍어 봐야 보인다.
2. ★★★ **DSL 을 만들면서 `@DslMarker` 를 안 단다.** (1)의 사고가 컴파일을 통과한다.
3. ★★ **에러가 나면 `this@바깥.` 을 붙여 끝낸다.** 동작이 (1)과 **같아진다**((3)) — 에러는 「그 자리가 맞나」를 물은 것이다.
4. ★★ **`@DslMarker` 가 바깥의 것을 전부 막는다고 믿는다.** 막는 것은 **표시된 수신자의 암묵 호출**뿐이다 — 명시 수신자와 가장 안쪽 수신자는 그대로다((2)).
5. ★ **수신자 람다 안에서 `it` 을 쓴다.** `this` 다((5)).
6. ★ **일반 함수 타입 값을 `x.f()` 로 부른다.** 수신자 타입이라야 한다((5)).
7. ★ **Java 에서 부를 때 `Unit` 을 안 돌려준다.** `return Unit.INSTANCE;` 가 필요하다((5)).

## 구현 세부사항 대 언어 보장

| 항목 | 어느 쪽인가 | 근거 |
|---|---|---|
| `A.() -> R` 안의 `this` 가 넘겨받은 `A` | ★★★ **언어 보장** | 문서 · (1)(4) |
| 암묵 수신자를 **안쪽부터** 찾는 것 · 바깥 수신자도 보이는 것 | ★★★ **언어 보장**(이름 해석 규칙) | (1) |
| `@DslMarker` 가 표시된 바깥 수신자의 **암묵** 호출을 막는 것 | **언어 보장** | 문서 · (2) |
| 마커가 **상위 타입에서 상속**되는 것 | **언어 보장** | (2) — `Tag` 한 곳 |
| `this@라벨` | **언어 보장** | (1)(3) |
| `A.() -> R` 값과 `(A) -> R` 값이 서로 대입되는 것 | **언어 보장** | (4) |
| `A.() -> Unit` → **`Function1<? super A, Unit>`** · 수신자가 **첫 인자** | ★★ **JVM 백엔드의 구현** | (4)(5) · [10번 주제](../10-lambdas-and-higher-order-functions/) (1) |
| 「수신자 있음」이 **메타데이터에만** 있는 것 | ★ **JVM 백엔드의 구현** | (4) · [14번 주제](../14-scope-functions/) (2) |
| `@DslMarker` 진단 문구 | **이 판의 산출물** | (2) |

★★ **가장 조심할 자리** — 「DSL 은 비용이 없다」는 이 문서가 **뒷받침하지 않는다.** (4)가 보인 것은 「수신자 람다 **호출**이 일반 람다 호출과 **같은 명령**이다」라는 구조 사실이다. 빌더 함수가 `inline` 이 아니면 **람다 객체**가 생기고(`invokedynamic` — [36번 주제](../36-function-types-fun-interface-and-sam-conversion/) (3)), 노드 객체도 생긴다. **시간도 개수도 재지 않았다.**

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 계층 구조를 코드 모양대로 짓는다(HTML·설정·UI) | ★ 수신자 람다 빌더 | (1) — 블록 안에서 이름만으로 |
| 그 빌더를 만든다 | ★★ **`@DslMarker` 를 공통 조상에** | (2) — (1)의 사고를 컴파일 에러로 |
| 객체 하나를 만들고 필드를 채운다 | `apply { }` | [14번 주제](../14-scope-functions/) — 같은 장치의 가장 작은 판 |
| 바깥 블록의 멤버를 **일부러** 부른다 | `this@라벨.멤버` | (3) — 뜻을 코드에 남긴다 |
| Java 사용자도 쓸 빌더 | 수신자 람다는 Java 에게 `Function1<A, Unit>` | (5) — Java 쪽은 `Unit.INSTANCE` 반환 |
| 수신자가 둘 이상 필요하다(`Logger` 와 `Tx` 를 함께) | 목록의 **38번 주제**(context parameters) | 수신자는 하나뿐이다 |

## 핵심 문장

1. `A.() -> Unit` 은 「이 블록 안에서 `this` 는 `A`」라는 타입이다 — 이름만 부르면 **가장 안쪽 수신자부터** 찾는다.
2. ★ 안쪽에 없으면 **바깥 수신자로 조용히 넘어간다** — `body { head { } }` 가 **에러 없이** `html` 에 `head` 를 붙였다.
3. `@DslMarker` 는 **표시된 바깥 수신자를 암묵으로** 못 부르게 한다 — 동작을 바꾸는 게 아니라 **명시하게** 만든다.
4. JVM 에서 `A.() -> Unit` 은 `Function1<A, Unit>` 이고 **수신자는 첫 인자**다 — `a.block()` 과 `block(a)` 는 같은 명령이다.
5. 「수신자가 있다」는 사실은 **Kotlin 메타데이터에만** 있다 — Java 에게는 평범한 첫 매개변수다.

## 관련 자료

- [14번 주제](../14-scope-functions/) — ★★ **선행.** `apply`/`with`/`run` 이 수신자 람다를 받는 것, `run`/`with` 의 디스크립터가 같은 것. 그쪽은 「다섯을 어떻게 고르나」까지, 여기는 「**수신자 람다를 중첩하면 무엇이 헷갈리나**」부터.
- [36번 주제](../36-function-types-fun-interface-and-sam-conversion/) — ★★ **선행.** 함수 타입이 `Function1` 이고 람다가 `invokedynamic` 이 되는 것.
- [10번 주제](../10-lambdas-and-higher-order-functions/) (1) — `Int.() -> String` 의 수신자가 첫 파라미터인 것(`fRecv`).
- [13번 주제](../13-extension-functions-and-properties/) — 확장 함수. 수신자 람다는 「**익명 확장 함수**」다.
- [`../../언어-특성/README.md`](../../언어-특성/README.md) §7 — DSL 이 되는 이유와 `@DslMarker` 의 논지.
- 목록의 **38번 주제** — context parameters. 수신자 하나로 부족할 때.
- [`../../../js/syntax/07-this-binding-four-rules/`](../../../js/syntax/07-this-binding-four-rules/) — JS `this` 네 규칙. 대비.

## 용어 풀이

> **수신자(receiver)** — `a.f()` 의 `a`. 함수 안에서 `this` 가 가리키는 객체.

> **수신자 있는 함수 타입(function type with receiver)** — `A.() -> R`. 그 람다 안에서 `this` 가 `A` 다.\
> 예: `fun html(init: Html.() -> Unit)`.

> **암묵 수신자(implicit receiver)** — `this.` 를 안 적어도 멤버를 찾아 주는 수신자. 중첩되면 **여럿**이 되고 안쪽부터 찾는다.

> **type-safe builder** — 수신자 람다를 중첩해 **계층 구조를 코드 모양대로** 짓는 패턴. 부를 수 있는 이름이 타입으로 제한된다.

> **`@DslMarker`** — 이것을 붙인 애너테이션으로 빌더 클래스를 표시하면, 표시된 **바깥** 수신자의 멤버를 **암묵으로** 부를 수 없게 된다.

> **`this@라벨`** — 바깥 수신자를 명시해 부르는 꼴. 라벨은 람다를 받은 함수 이름(`this@html`).

> **`ExtensionFunctionType`** — 함수 타입에 「수신자가 있다」는 표시. JVM 에서는 **메타데이터 문자열**에 남는다.

## 더 들어가면

- **왜 바깥 수신자가 보이게 설계됐나** — 수신자 람다는 **익명 확장 함수**이고, 확장 함수 안에서도 바깥 스코프의 `this` 들이 보인다. 이것은 `apply { }` 안에서 **바깥 클래스의 멤버를 이름만으로** 부르는 편리함의 근원이다 — 같은 규칙이 DSL 에서는 사고가 된다. 그래서 Kotlin 은 규칙을 바꾸지 않고 **DSL 작성자가 켜는 스위치**(`@DslMarker`)를 따로 뒀다.
- **`@DslMarker` 가 모르는 것** — 문서는 마커가 **표시된 타입의 수신자**에 대해 동작한다고 적는다. 빌더 안에 **표시 안 된 수신자**(예: `with(someList) { … }`)를 끼웠을 때 어디까지 막히는지는 이 문서가 **던지지 않았다** — 다음에 격자로 재 볼 자리다.
