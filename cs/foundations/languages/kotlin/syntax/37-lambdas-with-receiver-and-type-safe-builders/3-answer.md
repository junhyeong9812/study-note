# kotlin/syntax/37 — 리시버 지정 람다와 type-safe builder (DSL) — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javac`·`java`·`javap` 에서 실제로 얻었다.\
> 역어셈블은 **기본 `-jvm-target`(1.8)** 이 정본이다.
> ★★ 아래 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적은 자리가 없다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 컴파일된다 · ★ **`head() on receiver html`** — `body` 안에 쓴 `head` 가 **`html` 에** 붙고, 트리에서 **`body` 보다 앞**이다

**출력**

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

**왜 그런가**

- ★★★ 암묵 수신자는 **안쪽(`Body`)부터** 찾는다. `Body` 에 `head` 가 없으니 **바깥 암묵 수신자(`Html`)** 의 `head` 가 불렸다 — 에러도 경고도 없다.
- ★★ `p()` 와 `name` 은 `Body` 에 있으니 안쪽이 대답했다(`p() on receiver body` · `name=body`). 바깥은 `this@html` 로 부른다.
- ★ 트리 순서는 7번.

### 2. ★★★ 컴파일 **실패** — 37번째 줄 「`'fun head(init: Head.() -> Unit): Head' cannot be called in this context with an implicit receiver. Use an explicit receiver if necessary.`」 · `[in body]` 줄은 **안 막힌다**

**출력**

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

**왜 그런가**

- ★★★ `@HtmlDsl` 이 표시된 수신자(`Tag` 의 하위 전부)끼리는 **바깥 수신자의 멤버를 암묵으로** 못 부른다. `head` 가 바로 그 경우다.
- ★★ `name` 은 **가장 안쪽 수신자**의 것, `this.name` 도 가장 안쪽, `this@html.name` 은 **명시 수신자**라 전부 허용이다.

### 3. ★★ 컴파일된다 · 출력이 1번과 **한 글자도 같다**

**출력**

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

**왜 그런가**

- ★★ `@DslMarker` 는 **동작을 안 바꾼다** — 바깥 수신자 호출을 **명시로 적게** 만들 뿐이다. 명시하면 1번과 같은 곳(`html`)에 붙는다.

### 4. ★★ 컴파일된다 · `x` · `plain it.name=y` · `z` · `w` · `v` — 다섯 줄 전부 돈다

**출력**

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

**왜 그런가**

- ★★ `A.() -> Unit` **값**과 `(A) -> Unit` **값**은 서로 대입된다 — `callA(…, plain)` 과 `callC(…, ext)` 가 둘 다 통과했다. JVM 에서 둘 다 `Function1<A, Unit>` 이기 때문이고(5번), 언어도 그 대입을 허락한다.
- ★ `ext(A("w"))` 와 `A("v").ext()` — 수신자 타입 값은 **두 문법**으로 다 부를 수 있다.

### 5. ★★★ 세 몸통이 **한 글자도 같다** — `aload_1`(블록) · `aload_0`(`a`) · `invokeinterface Function1.invoke` · `ExtensionFunctionType` 은 **상수 풀과 메타데이터 `d2` 문자열**에만

**출력**

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

**왜 그런가**

- ★★★ **수신자는 `invoke` 의 첫 인자**다. `a.block()` 은 `block.invoke(a)` 로 번역되고, 그것은 `block(a)` 와 같다.
- ★★ 「이 `Function1` 은 수신자가 있다」는 사실은 **명령·디스크립터 어디에도 없고** 메타데이터에만 있다 — Kotlin 컴파일러가 **다음 컴파일에서** 그 함수를 `A.() -> Unit` 으로 읽게 하려는 표시다([14번 주제](../14-scope-functions/) (2)와 같은 결론).

### 6. ★★ `recvbad.kt` — **둘 다 막힌다**(「`unresolved reference 'it'.`」 · 「`unresolved reference 'plain' on receiver of type 'B'.`」) · `JRecv.java` 는 **컴파일되고** `from Java: first argument name=java`

**출력**

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

**왜 그런가**

- ★★ **값끼리는 대입되지만 문법은 갈린다** — 수신자 자리의 람다 **리터럴** 안에는 `it` 이 없고(`this` 다), 일반 함수 타입 값은 **`x.f()` 문법**으로 못 부른다.
- ★★ Java 에게 `callA` 는 `(A, Function1<? super A, Unit>)` 일 뿐이다 — 수신자는 **람다의 첫 매개변수**이고 `Unit.INSTANCE` 를 돌려줘야 한다.

### 7. **아니다** — 소스는 `body` 안에 `head` 인데 트리는 `html` 아래 **`head` → `body`** 순서다 · `add` 가 **`t.init()` 을 먼저, `kids += t` 를 나중에** 하기 때문이다

**왜 그런가**

- ★★ `body` 를 붙이는 `add` 가 `body` 의 블록을 **도는 도중에** `head` 의 `add` 가 불렸고, 그것이 **`html.kids` 에 먼저** 들어갔다. `body` 는 블록이 **끝난 뒤** 들어갔다.
- ★ 그래서 이 사고는 **자리도 순서도** 틀리게 만든다 — 테스트가 「`head` 가 있나」만 보면 통과한다.

### 8. **아니다** — 막히는 것은 「**표시된 바깥 수신자의 멤버를 암묵으로**」 부르는 것뿐이다 · 명시 수신자(`this@html.…`)와 **가장 안쪽 수신자**의 멤버는 그대로다

**왜 그런가**

- ★★ 2번의 35번째 줄(`name`·`this.name`·`this@html.name`)이 **안 막혔고** 37번째 줄(`head`)만 막혔다. 3번은 명시 수신자로 **통과**했다.
- ★ 마커는 `Tag` 한 곳에 달았는데 네 하위 클래스 전부에 걸렸다 — **상위 타입에서 상속**된다.

### 9. **호출자가 수신자 자리에 넘긴 값**이 정한다 — 그 자리는 타입(`A`)으로 고정되고, 문법(`a.block()` 대 `block(a)`)은 아무것도 바꾸지 않는다

**왜 그런가**

- ★★ 4번 — `callA(A("x"), ext)` 에서 `x`, `callC(A("z"), ext)` 에서 `z`, `ext(A("w"))` 에서 `w`, `A("v").ext()` 에서 `v`. 매번 **넘긴 `A`** 가 `this` 다. 5번이 보이듯 그것은 `invoke` 의 **첫 인자**일 뿐이다.
- ★ JS 는 같은 함수를 `obj.f()` 로 부르냐 `f()` 로 부르냐에 따라 `this` 가 바뀐다([JS 07번](../../../js/syntax/07-this-binding-four-rules/)). Kotlin 에서는 **수신자가 인자이므로** 호출 문법이 바꿀 여지가 없고, **타입이 안 맞는 수신자는 컴파일에서** 막힌다.

### 10. 장치는 **수신자 있는 함수 타입**(`T.() -> Unit`)이다 — `apply` 는 **수신자 하나를 돌려주는** 가장 작은 판이고, `html` 은 그것을 **중첩해 트리를 짓는** 판이다

**왜 그런가**

- ★★ `apply` 의 매개변수는 `T.() -> Unit`([14번 주제](../14-scope-functions/) (2) — `Function1<? super T, kotlin.Unit>`)이고, `html` 의 매개변수는 `Html.() -> Unit` 이다. 형태가 같다.
- ★ 차이는 **중첩**이다 — `apply` 하나로는 암묵 수신자가 하나라 1번의 사고가 날 자리가 없다. 빌더는 수신자를 **겹겹이** 쌓으므로 `@DslMarker` 가 필요해진다.

### 11. **뒷받침하지 못한다** — 5번이 보인 것은 「수신자 람다 호출이 일반 람다 호출과 **같은 명령**」이라는 구조 사실뿐이다

**왜 그런가**

- ★★ 빌더 함수(`html`·`body`)는 `inline` 이 아니므로 호출마다 **람다 객체**가 생기고([36번 주제](../36-function-types-fun-interface-and-sam-conversion/) (3)의 `invokedynamic`), 노드 객체도 생긴다. 그 **개수도 시간도 재지 않았다.**
- ★ 「비용이 없다」를 주장하려면 `inline` 여부를 바꿔 **명령 수·할당 수·시간**을 따로 재야 한다([11번 주제](../11-inline-functions/)).

## 실행 검증

```text
===== kotlinc -version =====
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
(exit 0)
```

```text
===== java -version =====
openjdk version "21.0.5" 2024-10-15 LTS
OpenJDK Runtime Environment Temurin-21.0.5+11 (build 21.0.5+11-LTS)
OpenJDK 64-Bit Server VM Temurin-21.0.5+11 (build 21.0.5+11-LTS, mixed mode, sharing)
(exit 0)
```

```text
===== javac -version =====
javac 21.0.5
(exit 0)
```

```text
===== javap -version =====
21.0.5
(exit 0)
```

★ **흔들리는 칸과 안 흔들리는 칸**

| 흔들린다 | 안 흔들린다 |
|---|---|
| **없다** — 해시코드·주소를 찍지 않았다 | 빌더 로그 · 트리 · 실행 출력 · `javap` 출력 |
| | 진단의 **문구·`파일:줄:칸`·캐럿** |
| | 모든 **종료 코드** |

> 근거 — 캡처 스크립트를 처음부터 다시 돌려 **블록 전체를 바이트 단위로 대조**했다.
>
> 실측 — `capture.sh blocks` 와 `capture.sh blocks-recheck` 를 처음부터 따로 돌려 `normalize-shaky.py` 로 대조했다 —\
> **블록 103개 · 동일 103 · 흔들린 칸 0 · ★고칠 것 0**(34\~37 네 주제를 한 캡처로 받았다). `diff -rq` 도 차이 0 이다.\
> ★ **정규화 규칙은 하나도 안 썼다** — 기본 넷(주소·PID·스레드 id·시간)에 걸리는 칸이 애초에 없었다.

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `dsl.kt` | ★★★ 중첩 DSL 사고 — `head()` 가 `html` 에 | `kotlinc` → `java` |
| `dslm.kt` | ★★★ `@DslMarker` 에러 | `kotlinc`(실패가 결과) |
| `dslm2.kt` | `this@html` 명시 — 출력이 1번과 같다 | `kotlinc` → `java` |
| `recv37.kt` | ★★ 다섯 가지 호출 · 세 몸통이 같은 명령 · 메타데이터 | `kotlinc` → `java` · `javap -c`(필터) · `javap -v`(필터) |
| `recvbad.kt` | 리터럴의 `it` · 일반 값의 수신자 문법 | `kotlinc`(실패가 결과) |
| `JRecv.java` | Java 쪽 — 수신자가 첫 매개변수 | `javac` → `java` |
| `form37.kt` | 형태 한 벌 | `kotlinc` → `java` |

**구현 의존 항목** — `A.() -> Unit` 이 `Function1` 이 되는 것 · 수신자가 첫 인자인 것 · 「수신자 있음」이 메타데이터에만 있는 것 · 진단 문구 — 이 컴파일러·판의 산출물이다.\
반면 **「`this` 는 넘겨받은 수신자」「암묵 수신자는 안쪽부터, 바깥도 보인다」「`@DslMarker` 는 표시된 바깥 수신자의 암묵 호출을 막는다」** 는 **언어의 계약**이다.

**★ 던져 봤더니 예상과 달랐던 것 — 두 건**

1. ★★ **`@DslMarker` 의 에러 문구가 브리핑과 달랐다** — 「`can't be called in this context by implicit receiver`」가 아니라 **「`cannot be called in this context with an implicit receiver. Use an explicit receiver if necessary.`」**(2번). 진단 문구는 판에 매인다.
2. ★ **사고가 자리만이 아니라 순서까지 바꿨다**(7번) — `head` 가 `html` 에 붙는 것은 예상했지만, **`body` 보다 앞**에 온 것은 `add` 의 한 줄 순서 때문이었다.
