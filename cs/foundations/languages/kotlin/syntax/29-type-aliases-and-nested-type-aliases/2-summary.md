# kotlin/syntax/29 — 타입 별칭·중첩 타입 별칭 (2.2+) — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Type aliases](https://kotlinlang.org/docs/type-aliases.html) · [What's new in Kotlin 2.2.0](https://kotlinlang.org/docs/whatsnew22.html)(중첩 타입 별칭 도입) · [What's new in Kotlin 2.3.0](https://kotlinlang.org/docs/whatsnew23.html)(Stable).
> **실행 검증** — 이 문서의 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javap` 에서 실제로 얻었다.\
> `kotlinc` 10회(컴파일 실패 4벌 — `-language-version 2.2` 1벌 포함) · `java` 5회 · `javap` 4회 · `go build` 1회 · `tsc` 1회(둘 다 실패가 결과).\
> ★★ 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적지 않았다. 소스 펜스의 첫 줄 배너도 캡처가 찍었다.
> **버전** — 최상위 `typealias` 는 **1.1** 부터다. ★★ **중첩 타입 별칭은 2.2.0 도입 · 2.3.0 Stable** 이다([README](../README.md) 버전표) — (5)에서 **이 판의 컴파일러에게 직접 물어** 확인했다.
> **경계** — 새 타입을 **만드는** 쪽은 [26번 주제](../26-value-class-and-boxing/)(`value class`)가 정본이고, 여기는 **안 만드는** 쪽이다 — ★ **둘이 짝이다**((7)).\
> 함수 타입 자체는 목록의 **36번 주제**, 제네릭 변성은 [28번 주제](../28-generics-variance-in-out-star-where/)가 정본이다.
> **대비** — Go 갈래 목록([`go/syntax/README.md`](../../../go/syntax/README.md))의 **22번**([`22-type-assertion-any-and-comparable/`](../../../go/syntax/22-type-assertion-any-and-comparable/)) — `any` 가 `interface{}` 의 **별칭**이라는 것을 거기서 봤다. Go 는 **`type A = B`(별칭)와 `type A B`(새 타입)가 두 꼴로 갈린다** — 이 문서가 직접 던졌다((8)).\
> TS 갈래 목록([`ts/syntax/README.md`](../../../ts/syntax/README.md))의 **5번**([`05-structural-typing/`](../../../ts/syntax/05-structural-typing/))·**8번**([`08-interface-vs-type/`](../../../ts/syntax/08-interface-vs-type/)) — TS 의 `type` 도 **새 타입을 안 만든다.** 브랜드 타입은 5번이 정본이다.
> 이 본문은 Claude 작성이다(원고 없음).

★ **본체는 첫째 창이다** — 「**섞어 넣었는데 대입이 된다**」를 실행 출력으로 보는 창.
별칭이 새 타입을 안 만든다는 것은 **에러가 안 나는 것**으로 드러난다. 그래서 이 주제의 가장 강한 근거는 **통과한 컴파일과 뒤바뀐 출력**이다.

## 이 주제가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **언어 보장** | 명세·공식 문서가 약속한 것 | ★★★ 별칭은 **새 타입을 안 만든다** — 대입이 된다 · 같은 서명의 오버로드는 **충돌한다** |
| **구현(JVM 백엔드)** | kotlinc 가 JVM 으로 내리는 방식 | descriptor 에 별칭이 **없다** · ★ **Kotlin 메타데이터에는 이름이 남는다**((3)) |
| **이 판의 관찰** | kotlinc 2.4.20 에서 이번에 본 것 | 판 경계를 **`-language-version` 으로 물은 답**((5)) · 진단 문구 |

## 이 판

```text
===== kotlinc -version =====
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | (이 주제에는 없다) | 해시코드·주소를 **하나도 안 찍었다** |
| 안 흔들린다 | ★★★ 출력 — 특히 **뒤바뀐 인자가 그대로 찍힌 줄** | 이 주제의 답 자체다 |
| 안 흔들린다 | `javap` 출력 — descriptor · 상수 풀 **번호**(`#112`) · 메타데이터 `d2` | 같은 소스·같은 판이면 같다. ★ 상수 풀 **번호**는 소스가 바뀌면 움직이므로 근거로는 **이름이 있다**만 읽는다 |
| 안 흔들린다 | 컴파일 에러의 **문구·`파일:줄:칸`** — `go`·`tsc` 포함 | 결정적이다 |
| 안 흔들린다 | `-language-version` 게이트 문구 | 컴파일러가 판마다 정한 문장이다 |

★ 근거 — 캡처 스크립트를 처음부터 두 번 돌려 **블록 전체를 바이트 단위로 대조**했다(수치는 3-answer 의 「실행 검증」).

## 한눈에 — 쉽게 말하면

**`typealias` 는 「긴 이름에 붙이는 별명」이다.** 별명을 부르면 **본명의 그 사람**이 온다 — 다른 사람이 생기지 않는다.

`typealias UserId = String` 이라고 적으면 **`UserId` 는 `String` 의 다른 이름**일 뿐이다.\
그래서 **아무 `String` 이나 `UserId` 자리에 들어가고**, `OrderId`(역시 `String`)와 **서로 섞여도 컴파일러가 모른다.**

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 본명 | 원래 타입 `String` · `(String) -> Int` | (1) |
| 별명 | `typealias UserId = String` | (1) |
| 별명으로 불러도 **같은 사람** | 대입이 된다 · `UserId` 자리에 `OrderId` 가 들어간다 | (1) |
| 같은 사람을 두 번 등록 | 「`conflicting overloads`」 | (2) |
| 주민등록부에는 **본명만** | JVM descriptor 에는 `String` 만 | (3) |
| 동네 수첩에는 별명도 적혀 있다 | ★ **Kotlin 메타데이터**에는 `UserId` 가 남는다 | (3) |
| 부서 안에서만 쓰는 별명 | ★★ **중첩 타입 별칭** `class Router { typealias Route = … }` — 2.2 도입·2.3 Stable | (4)(5) |
| 진짜로 **다른 사람을 세우기** | `value class` — [26번 주제](../26-value-class-and-boxing/) | (7) |

```text
   typealias UserId  = String            @JvmInline value class ValUser(val raw: String)
   typealias OrderId = String            @JvmInline value class ValOrder(val raw: String)

   cancel(o, u)       <- 뒤바꿔 넣어도       cancelV(ov, uv)   <- 뒤바꿔 넣으면
                         컴파일된다                               에러 둘
   JVM: cancel(String, String)             JVM: cancelV-xSLm8gY(String, String)
         ^^^^^^^^^^^^^^ 둘 다 String 두 개를 받는다 — 비용은 같고 검사만 다르다
```

## 이 주제가 답하려는 질문

1. 별칭은 **새 타입인가** — 섞어 넣으면, 같은 서명으로 오버로드하면 어떻게 되나.
2. 별칭은 컴파일 뒤에 **어디에 남나** — JVM 서명에? 아니면 다른 곳에?
3. 중첩 별칭은 **이 판에서 되나** — 판 경계는 어디이고, 무엇을 못 하나.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **실행 출력** | **뒤바꿔 넣은 인자가 그대로 찍힌다**((1)) — 에러가 없었다는 것의 결과 | ★ **본체 창** |
| ★★ **컴파일 진단** | 오버로드 충돌 — ★ **진단이 별칭을 풀어서 말한다**((2)) · 중첩 별칭의 제약((6)) | 이 갈래의 기본 창 |
| ★ **`javap -s -p` 의 descriptor** | 별칭이 **한 글자도 없다**((3)) | [26번 주제](../26-value-class-and-boxing/)의 창 |
| ★★ **`javap -v` 의 상수 풀·메타데이터** | ★ **별칭 이름이 남아 있다**((3)) | ★ 이 주제의 고유 창 |
| ★★ **`-language-version` 을 낮춰 다시 던지기** | 판 경계를 **컴파일러가 직접 말하게** 한다((5)) | [Go 22번](../../../go/syntax/22-type-assertion-any-and-comparable/) (7)의 `go.mod` 창과 같은 발상 |
| ★ **Go·TS 로 같은 모양 던지기** | 별칭과 새 타입이 **다른 언어에서 어떻게 갈리나**((8)) | ★ 이 주제의 고유 창 |
| **부적용 — 런타임 비용** | ★★★ **잴 것이 없다.** 별칭을 쓴 코드와 원래 타입을 쓴 코드의 **descriptor 가 같다**((3)) — 「재 봤더니 같았다」가 아니다 | — |

★★ **제4의 상태 — 「잴 것이 없다」.** 런타임 비용 창은 **부적용**이다. 별칭은 JVM 이 메서드를 가르는 descriptor 에 **흔적이 없으므로** 비교할 두 대상이 **애초에 하나**다.\
★★ **그러나 「`javap` 에 흔적도 없다」는 틀렸다** — (3)에서 **상수 풀과 `kotlin.Metadata` 에 `UserId` 가 남았다.** 흔적이 없는 것은 **JVM 이 쓰는 층**(descriptor)이고, **Kotlin 컴파일러가 읽는 층**(메타데이터)에는 있다.\
★★ **제5의 상태 — 「같은 질문을 다른 창으로 물었다」.** 「중첩 별칭은 언제부터인가」를 릴리스 노트로 옮겨 적지 않고 **`-language-version 2.2` 로 낮춰 컴파일러에게 물었다**((5)).
★ 바꾼 창의 한계 — `-language-version` 은 **2.4.20 컴파일러가 흉내 낸 옛 판**이다. 진짜 2.2.0 컴파일러를 돌린 것이 **아니다.**

### (1) ★★★ 새 타입이 아니다 — 뒤바꿔 넣어도 **컴파일된다**

**언제 쓰나** — `typealias UserId = String` 으로 **ID 를 안전하게** 만들었다고 믿을 때.

```kotlin
// taassign.kt
typealias UserId = String
typealias OrderId = String

fun cancel(user: UserId, order: OrderId) = "user=$user order=$order"

fun main() {
    val u: UserId = "u-1"
    val o: OrderId = "o-77"
    println("A ${cancel(u, o)}")
    println("B ${cancel(o, u)}")
    println("C ${cancel("아무", "문자열")}")
    val s: String = u
    println("D ${s == u} ${u::class.simpleName}")
}
```

```text
===== kotlinc taassign.kt -d o29a =====
(exit 0)
===== java -cp o29a:kotlin-stdlib.jar TaassignKt =====
A user=u-1 order=o-77
B user=o-77 order=u-1
C user=아무 order=문자열
D true String
(exit 0)
```

- ★★★ **`B user=o-77 order=u-1`** — `cancel(o, u)` 로 **주문 ID 와 사용자 ID 를 뒤바꿔 넣었는데 컴파일도 실행도 됐다.** 에러가 **한 줄도 없었다**(`kotlinc … (exit 0)`).
- ★★ `C user=아무 order=문자열` — **아무 `String` 리터럴**도 들어간다. `UserId` 라는 이름은 **읽는 사람에게 주는 힌트**일 뿐이다.
- ★ `D true String` — `UserId` 를 `String` 변수에 담는 것도, 런타임 클래스를 물어보는 것도 **`String`** 이다. `u::class.simpleName` 은 **별칭을 모른다.**
- ★★★ [README](../README.md) 가 이 주제에 건 과녁이 이것이다 — 「**타입 안전성 없음**」. 뒤바꾸기를 막으려면 (7)의 `value class` 로 간다.

### (2) ★★ 같은 서명으로 오버로드하면 — **충돌한다**

**언제 쓰나** — 별칭 타입과 원래 타입으로 **같은 이름의 함수를 둘** 만들려 할 때.

```kotlin
// taclash.kt
typealias UserId = String

fun f(x: UserId) = "UserId"
fun f(x: String) = "String"
```

```text
===== kotlinc taclash.kt -d o29c =====
taclash.kt:3:1: error: conflicting overloads:
fun f(x: String): String
fun f(x: UserId) = "UserId"
^^^^^^^^^^^^^^^^
taclash.kt:4:1: error: conflicting overloads:
fun f(x: String): String
fun f(x: String) = "String"
^^^^^^^^^^^^^^^^
(exit 1)
```

- ★★★ **두 선언이 서로를 가리키며 막힌다** — 「`conflicting overloads:`」가 두 번.
- ★★★ **진단 둘째 줄이 결정적이다** — `fun f(x: UserId)` 쪽 에러의 목록에 **`fun f(x: String): String`** 이 적혔다. 컴파일러가 **별칭을 풀어서** 말한다 — 컴파일러 눈에 **처음부터 `String` 이었다.**
- ★★ [26번 주제](../26-value-class-and-boxing/) (1)의 `lookup(UserId)`·`lookup(Long)` 은 **공존했다**(이름을 뭉개서 갈랐다). 같은 모양이 여기서는 막힌다 — **새 타입을 만드느냐의 차이가 오버로드에서 가장 먼저** 드러난다.

### (3) ★★ 컴파일 뒤에 어디에 남나 — descriptor 에는 없고, 메타데이터에는 있다

**언제 쓰나** — 「별칭은 런타임에 아무것도 아니다」를 **확인할** 때. 그리고 그 문장이 **어디까지 맞는지** 볼 때.

```text
===== javap -s -p o29a/TaassignKt.class =====
Compiled from "taassign.kt"
public final class TaassignKt {
  public static final java.lang.String cancel(java.lang.String, java.lang.String);
    descriptor: (Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

  public static final void main();
    descriptor: ()V

  public static void main(java.lang.String[]);
    descriptor: ([Ljava/lang/String;)V
}
(exit 0)
```

- ★★★ **`cancel(java.lang.String, java.lang.String)` — descriptor 가 `(Ljava/lang/String;Ljava/lang/String;)…`** 다. `UserId`·`OrderId` 는 **어디에도 없다.** JVM 이 메서드를 찾고 부르는 층에는 **별칭이 없다.**
- 그러니 런타임 비용은 **잴 것이 없다**((0)) — 별칭을 쓴 `cancel` 과 `String` 으로 쓴 `cancel` 은 **같은 메서드**다.

**그런데 상수 풀을 뒤지면**

```text
===== javap -v o29a/TaassignKt.class | grep -n -E 'Utf8 +(UserId|OrderId)$|d2=' =====
124:  #112 = Utf8               UserId
126:  #114 = Utf8               OrderId
282:      d2=["UserId","","OrderId","cancel","user","order","main",""]
(exit 0)
```

- ★★★ **`UserId`·`OrderId` 가 상수 풀에 `Utf8` 로 있고, `kotlin.Metadata` 의 `d2` 배열에도 있다.** 「`javap` 에 흔적도 없다」는 **틀렸다.**
- ★★ 이것은 **Kotlin 컴파일러가 다른 모듈에서 이 파일을 읽을 때** 쓰는 정보다 — 다른 모듈의 Kotlin 코드가 `UserId` 라는 이름을 **import 해 쓸 수 있는 것**이 이 메타데이터 덕이다(이 문서는 **다른 모듈에서 부르는 데까지는 안 던졌다**).
- ★ 그래서 정확한 문장은 — 「**JVM 에게는 없고 Kotlin 에게는 있다.**」 Java 에서 보면 `cancel(String, String)` 일 뿐이다.

### (4) ★ 제네릭 별칭·함수 타입 별칭·중첩 별칭 — 긴 이름을 줄이는 본래 용도

**언제 쓰나** — `MutableMap<K, MutableList<String>>` · `(String) -> Int` 처럼 **길고 반복되는 타입**에 이름을 줄 때. **이것이 별칭의 본래 자리**다.

```kotlin
// tagen.kt
typealias Table<K> = MutableMap<K, MutableList<String>>
typealias Handler = (String) -> Int
typealias Pred<T> = (T) -> Boolean

class Router {
    typealias Route = Pair<String, Handler>

    val routes = mutableListOf<Route>()
    fun add(path: String, h: Handler) { routes += path to h }
}

fun main() {
    val t: Table<Int> = mutableMapOf(1 to mutableListOf("a"))
    println("A $t")
    val h: Handler = { it.length }
    val p: Pred<String> = { it.isEmpty() }
    println("B ${h("abcd")} ${p("")}")
    val r = Router()
    r.add("/x") { it.length * 10 }
    val route: Router.Route = r.routes[0]
    println("C ${route.first} ${route.second("ab")}")
}
```

```text
===== kotlinc tagen.kt -d o29g =====
(exit 0)
===== java -cp o29g:kotlin-stdlib.jar TagenKt =====
A {1=[a]}
B 4 true
C /x 20
(exit 0)
```

- `Table<K>` — **타입 파라미터를 받는 별칭**이다. `Table<Int>` 가 `MutableMap<Int, MutableList<String>>` 으로 풀린다.
- `Handler`·`Pred<T>` — **함수 타입에 이름**을 준다. `val h: Handler = { it.length }` 처럼 람다를 그대로 담는다.
- ★★ **`Router.Route`** — 클래스 **안에** 선언한 별칭이다(중첩 타입 별칭). 밖에서는 **`Router.Route`** 로 부른다. 판 경계는 (5)다.

```text
===== javap -p o29g/Router.class o29g/TagenKt.class =====
Compiled from "tagen.kt"
public final class Router {
  private final java.util.List<kotlin.Pair<java.lang.String, kotlin.jvm.functions.Function1<java.lang.String, java.lang.Integer>>> routes;
  public Router();
  public final java.util.List<kotlin.Pair<java.lang.String, kotlin.jvm.functions.Function1<java.lang.String, java.lang.Integer>>> getRoutes();
  public final void add(java.lang.String, kotlin.jvm.functions.Function1<? super java.lang.String, java.lang.Integer>);
}
Compiled from "tagen.kt"
public final class TagenKt {
  public static final void main();
  public static void main(java.lang.String[]);
  private static final int main$lambda$0(java.lang.String);
  private static final boolean main$lambda$1(java.lang.String);
  private static final int main$lambda$2(java.lang.String);
}
(exit 0)
```

- ★★ **`Route`·`Handler` 는 흔적이 없다** — `routes` 가 `List<Pair<String, Function1<String, Integer>>>` 로 **통째로 풀렸다.**
- ★ `add(String, Function1<? super String, Integer>)` — 함수 타입 `(String) -> Int` 의 파라미터 쪽에 **`? super`** 가 붙었다. `Function1<in P, out R>` 이 **반공변 파라미터**를 가졌기 때문이다([28번 주제](../28-generics-variance-in-out-star-where/) (9)).
- ★ 람다 셋의 본문은 `main$lambda$0` 류의 `private static` 메서드로 내려갔다 — 여기에도 `Handler`·`Pred` 라는 이름은 없다.

### (5) ★★★ 중첩 별칭의 판 경계 — 컴파일러에게 **직접 물었다**

**언제 쓰나** — 「이 코드가 옛 판에서도 도나」를 확인할 때. [README](../README.md) 의 버전표는 **2.2.0 도입 · 2.3.0 Stable** 이다.

```kotlin
// tagate.kt
class Api {
    typealias Headers = Map<String, String>

    fun send(h: Headers) = h.size
}

fun main() {
    println(Api().send(mapOf("a" to "1")))
}
```

```text
===== kotlinc tagate.kt -d o29n =====
(exit 0)
===== java -cp o29n:kotlin-stdlib.jar TagateKt =====
1
(exit 0)
===== kotlinc -language-version 2.2 tagate.kt -d o29n22 =====
tagate.kt:2:5: error: the feature "nested type aliases" is only available since language version 2.3
    typealias Headers = Map<String, String>
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
(exit 1)
===== kotlinc -language-version 2.2 -Xnested-type-aliases tagate.kt -d o29n22x =====
(exit 0)
```

| 던진 판 | 결과 | 읽는 법 |
|---|---|---|
| **기본**(2.4.20) | 통과 · `1` | 옵트인 **없이** 된다 — ★ **이 판에서는 Stable** 이다 |
| `-language-version 2.2` | 「`the feature "nested type aliases" is only available since language version 2.3`」 | ★★ **Stable 경계가 2.3** 이라고 **컴파일러가 스스로 말했다** |
| `-language-version 2.2 -Xnested-type-aliases` | 통과 | ★★ 2.2 에서는 **플래그를 켜야** 됐다 — 「도입(실험)」의 모습이다 |

- ★★★ **옵트인은 필요 없다**(2.4.20). 2.2 판으로 낮추면 **플래그 하나(`-Xnested-type-aliases`)로** 켜진다 — README 의 「2.2.0 도입 / 2.3.0 Stable」이 **컴파일러의 두 대답과 맞는다.**
- ★ `-language-version 2.2` 는 **이 컴파일러가 흉내 낸 2.2** 다((0)의 한계). 진짜 2.2.0 컴파일러가 같은 문장을 내는지는 **안 던졌다.**

### (6) ★ 중첩 별칭이 **못 하는 것** — 바깥의 타입 파라미터를 잡지 못한다

**언제 쓰나** — 제네릭 클래스 안에서 그 클래스의 `T` 로 별칭을 만들려 할 때.

```kotlin
// tacap.kt
class Holder<T> {
    typealias Items = List<T>

    inner class In {
        typealias X = Int
    }

    fun f() {
        typealias Local = Int
    }
}
```

```text
===== kotlinc tacap.kt -d o29p =====
tacap.kt:2:28: error: unresolved reference 'T'.
    typealias Items = List<T>
                           ^
tacap.kt:9:9: error: the feature "local type aliases" is experimental and should be enabled explicitly. This can be done by supplying the compiler argument '-Xlocal-type-aliases', but note that no stability guarantees are provided.
        typealias Local = Int
        ^^^^^^^^^^^^^^^^^^^^^
(exit 1)
```

- ★★★ `typealias Items = List<T>`(2번째 줄) — 「`unresolved reference 'T'.`」. 중첩 별칭은 **바깥 클래스의 타입 파라미터를 못 본다.** README 가 「**비캡처**(non-capturing) 타입 별칭」이라고 부르는 이유다.
- ★ 필요하면 **별칭이 자기 파라미터를 받게** 한다 — `typealias Items<X> = List<X>`.
- ★★ **`inner class In` 안의 별칭**(5번째 줄)은 **에러가 없다** — 세 곳을 물었고 두 곳이 답했다. 중첩 별칭은 `inner` 안에도 둘 수 있다.
- ★ **지역(함수 안) 별칭**(9번째 줄)은 「`the feature "local type aliases" is experimental and should be enabled explicitly.`」 — **이 판에서도 실험**이다(`-Xlocal-type-aliases`). 중첩과 지역은 **다른 기능**이다.

### (7) ★★★ `value class` 와의 대비 한 장 — 안전성 대 비용

**언제 쓰나** — 「ID 에 이름을 붙이고 싶다 — 별칭이냐 값 클래스냐」를 고를 때. [26번 주제](../26-value-class-and-boxing/)와 **짝**이다.

```kotlin
// tavs.kt
typealias AliasUser = String
typealias AliasOrder = String

@JvmInline value class ValUser(val raw: String)
@JvmInline value class ValOrder(val raw: String)

fun cancelA(user: AliasUser, order: AliasOrder) = "$user/$order"
fun cancelV(user: ValUser, order: ValOrder) = "${user.raw}/${order.raw}"

fun main() {
    val ua: AliasUser = "u"
    val oa: AliasOrder = "o"
    println(cancelA(oa, ua))
    val uv = ValUser("u")
    val ov = ValOrder("o")
    println(cancelV(ov, uv))
}
```

```text
===== kotlinc tavs.kt -d o29v =====
tavs.kt:16:21: error: argument type mismatch: actual type is 'ValOrder', but 'ValUser' was expected.
    println(cancelV(ov, uv))
                    ^^
tavs.kt:16:25: error: argument type mismatch: actual type is 'ValUser', but 'ValOrder' was expected.
    println(cancelV(ov, uv))
                        ^^
(exit 1)
```

- ★★★ **에러가 `cancelV(ov, uv)` 줄에만 있다**(16번째 줄 두 칸). 13번째 줄 `cancelA(oa, ua)` — 별칭 쪽의 **같은 뒤바꾸기는 통과**했다.

```kotlin
// tavsok.kt
typealias AliasUser = String
typealias AliasOrder = String

@JvmInline value class ValUser(val raw: String)
@JvmInline value class ValOrder(val raw: String)

fun cancelA(user: AliasUser, order: AliasOrder) = "$user/$order"
fun cancelV(user: ValUser, order: ValOrder) = "${user.raw}/${order.raw}"

fun main() {
    println(cancelA("u", "o"))
    println(cancelV(ValUser("u"), ValOrder("o")))
}
```

```text
===== kotlinc tavsok.kt -d o29o =====
(exit 0)
===== java -cp o29o:kotlin-stdlib.jar TavsokKt =====
u/o
u/o
(exit 0)
===== javap -s -p o29o/TavsokKt.class | grep -A1 cancel =====
  public static final java.lang.String cancelA(java.lang.String, java.lang.String);
    descriptor: (Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
--
  public static final java.lang.String cancelV-xSLm8gY(java.lang.String, java.lang.String);
    descriptor: (Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
(exit 0)
```

```text
                          typealias                         value class
   ---------------------  --------------------------------  -----------------------------------
   섞어 넣으면             통과한다 ((1)·위 13번째 줄)        에러 ((7) 16번째 줄)
   오버로드                충돌한다 ((2))                    공존한다 (26번 (1))
   JVM 서명                cancelA(String, String)           cancelV-xSLm8gY(String, String)
   이 호출의 박싱           없음                              없음 — 알맹이 String 을 받는다
   다른 자리의 박싱         없음 — 원래 타입 그대로           제네릭·Any·인터페이스에서 box-impl (26번 (2))
   Java 에서               그냥 String                       뭉개진 이름이라 못 부른다 (26번 (5))
   init 검사               없다                              있다 (26번 (4))
```

- ★★★ **이 호출에서는 비용이 같다** — 둘 다 **`String` 두 개**를 받는다(descriptor 가 같다). 다른 것은 **컴파일러가 검사하느냐**와 **이름이 뭉개지느냐**뿐이다.
- ★★ `value class` 의 비용은 **다른 자리**에서 온다 — 제네릭·`Any`·인터페이스에서 `box-impl`([26번 주제](../26-value-class-and-boxing/) (2)), 그리고 Java 에서 못 부르는 이름. 별칭은 **그 비용이 전혀 없고, 대신 검사도 전혀 없다.**
- ★ 이 문서는 **시간을 안 쟀다** — 「같다」는 **descriptor 가 같다**는 뜻이지 속도를 잰 것이 아니다.

### (8) ★★ Go 와 TS — 두 꼴이 **문법으로** 갈리는 언어, 브랜드로 흉내 내는 언어

**Go — `type A = B` 는 별칭, `type A B` 는 새 타입**

```go
// main.go
package main

import "fmt"

type AliasID = string
type NewID string

func takeAlias(x AliasID) string { return "alias " + x }
func takeNew(x NewID) string     { return "new " + string(x) }

func main() {
	s := "raw"
	fmt.Println(takeAlias(s))
	fmt.Println(takeNew(s))
}
```

```text
===== 소스: go.mod =====
module goal

go 1.27
===== go version =====
go version go1.27.1 linux/amd64
(exit 0)
===== cd goal && go build -o /dev/null . =====
# goal
./main.go:14:22: cannot use s (variable of type string) as NewID value in argument to takeNew
(exit 1)
```

- ★★★ **에러가 14번째 줄(`takeNew(s)`) 하나뿐**이다. 13번째 줄 `takeAlias(s)` — **`=` 가 있는 별칭은 `string` 을 그대로 받았다.**
- ★★ Go 는 **`=` 한 글자로** 두 기능을 가른다 — `type AliasID = string` 은 Kotlin 의 `typealias`, `type NewID string` 은 **새 타입**(정의된 타입)이다. Kotlin 은 두 번째를 **`value class` 라는 별도 문법**으로 만든다.
- ★ Go 의 새 타입은 **박싱이 없다** — 값 타입 그대로다. Kotlin `value class` 가 **JVM 위에서 흉내 내느라** 박싱 자리가 생긴 것과 다르다([26번 주제](../26-value-class-and-boxing/)의 「더 들어가면」).
- ★ `go.mod` 의 `go 1.27` 줄도 같이 실었다 — 설정 파일이 결과를 바꿀 수 있는 입력이기 때문이다.

**TS — `type` 은 별칭이다, 새 타입이 필요하면 브랜드를 붙인다**

```ts
// alias29.ts
type UserId = string;
type BrandedId = string & { readonly __brand: "UserId" };

function load(id: UserId): string { return "user:" + id; }
function loadB(id: BrandedId): string { return "user:" + id; }

const order = "o-77";
console.log(load(order));
console.log(loadB(order));
```

```text
===== tsc -v =====
Version 7.0.2
(exit 0)
===== tsc --noEmit --strict --target es2022 alias29.ts =====
alias29.ts(9,19): error TS2345: Argument of type 'string' is not assignable to parameter of type 'BrandedId'.
  Type 'string' is not assignable to type '{ readonly __brand: "UserId"; }'.
(exit 1)
```

- ★★ **에러가 9번째 줄(`loadB(order)`) 하나뿐**이다 — `type UserId = string` 인 `load` 는 **아무 `string`** 을 받았다. TS 도 **구조적 타입**이라 별칭이 새 타입을 안 만든다.
- ★ `BrandedId` 는 **존재하지 않는 프로퍼티를 교차 타입으로 붙여** 명목 타입을 흉내 낸 것이다([TS 05번](../../../ts/syntax/05-structural-typing/) (5)가 정본). Kotlin 은 그 흉내가 필요 없다 — **`value class` 가 진짜 명목 타입**이다.

| 언어 | 별칭(새 타입 아님) | 새 타입 | 새 타입의 런타임 |
|---|---|---|---|
| Kotlin | `typealias A = B` | `@JvmInline value class A(val b: B)` | **알맹이**(자리에 따라 박싱) |
| Go | `type A = B` | `type A B` | **값 그대로** |
| TS | `type A = B` | 브랜드 `B & { __brand: … }` | **아무것도 없다**(타입은 지워진다) |

## 문법 — 형태와 규칙

**형태** — 제네릭 없는 별칭·함수 타입 별칭·중첩 별칭이 한 프로그램에서 전부 도는 최소 예제다.

```kotlin
// form29.kt
typealias Json = Map<String, Any?>
typealias Validator<T> = (T) -> List<String>

class Form {
    typealias Field = Pair<String, String>

    val fields = mutableListOf<Field>()
}

val notBlank: Validator<String> = { if (it.isBlank()) listOf("비었다") else emptyList() }

fun main() {
    val j: Json = mapOf("id" to 1, "tag" to null)
    println("Z $j")
    println("Y ${notBlank("")} ${notBlank("x")}")
    val f = Form()
    f.fields += "name" to "kim"
    println("X ${f.fields}")
}
```

```text
===== kotlinc form29.kt -d o29f =====
(exit 0)
===== java -cp o29f:kotlin-stdlib.jar Form29Kt =====
Z {id=1, tag=null}
Y [비었다] []
X [(name, kim)]
(exit 0)
```

**규칙 불릿**

- **`typealias 이름 = 타입`** — 최상위에 둔다. **타입 파라미터**를 받을 수 있다(`typealias Table<K> = …`)((4)).
- 별칭은 **새 타입이 아니다** — 원래 타입과 **서로 대입**되고, 같은 원래 타입의 별칭끼리도 섞인다((1)).
- 원래 타입으로 풀어서 **같은 서명이면 충돌**한다((2)).
- JVM descriptor 에는 **원래 타입만** 남는다. 이름은 **Kotlin 메타데이터**에만 있다((3)).
- ★★ **클래스 안에 둘 수 있다**(중첩 타입 별칭) — **2.3.0 Stable**, 2.2 에서는 `-Xnested-type-aliases`((5)). 밖에서는 `바깥.별칭` 으로 부른다.
- 중첩 별칭은 **바깥의 타입 파라미터를 못 잡는다**((6)). **함수 안(지역) 별칭은 이 판에서도 실험**이다((6)).
- 섞이면 안 되는 값이면 별칭이 아니라 **`value class`**((7)).

## 어디서 틀리나

1. ★★★ **`typealias UserId = String` 으로 ID 가 안전해졌다고 믿는다.** **뒤바꿔 넣어도 컴파일된다**((1)의 `B`). 막으려면 `value class`((7)).
2. ★★ **별칭 타입으로 오버로드를 하나 더 만든다.** 「`conflicting overloads`」((2)) — 컴파일러 눈에 **같은 `String`** 이다.
3. ★★ **런타임에 별칭을 물어보려 한다.** `u::class.simpleName` 은 **`String`** 이다((1)의 `D`).
4. ★★ **「별칭은 클래스 파일에 흔적이 없다」고 단정한다.** descriptor 에는 없지만 **메타데이터에는 이름이 있다**((3)).
5. ★ **옛 판에서 중첩 별칭을 쓴다.** 2.2 는 「`only available since language version 2.3`」((5)).
6. ★ **제네릭 클래스 안에서 `T` 로 중첩 별칭을 만든다.** 「`unresolved reference 'T'.`」((6)).
7. ★ **함수 안에 별칭을 둔다.** 이 판에서도 **실험**이다((6)).

## 구현 세부사항 대 언어 보장

| 항목 | 어느 쪽인가 | 근거 |
|---|---|---|
| 별칭이 **새 타입을 안 만드는 것** — 대입·섞임 | ★★★ **언어 보장** | (1) |
| 같은 서명 오버로드의 **충돌** | **언어 보장** | (2) |
| 중첩 별칭이 **바깥 타입 파라미터를 못 잡는 것** | **언어 보장**(2.3 Stable 의 규칙) | (6) |
| 중첩 별칭 **2.2 도입 · 2.3 Stable** | **언어 판의 경계** — 이 컴파일러가 스스로 말했다 | (5) |
| 지역 별칭이 **실험** | **이 판(2.4.20)의 상태** | (6) |
| descriptor 에 별칭이 **없는 것** | **JVM 백엔드의 구현**(별칭이 JVM 개념이 아니므로) | (3) |
| **메타데이터에 이름이 남는 것** | **Kotlin 컴파일러의 구현**(모듈 간 사용을 위해) | (3) |
| 함수 타입 별칭의 파라미터에 **`? super`** 가 붙는 것 | **JVM 백엔드의 상호운용 규칙**([28번 주제](../28-generics-variance-in-out-star-where/)) | (4) |
| 진단 **문구 그 자체** · 상수 풀 번호 | **이 판의 산출물** | 전부 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 길고 반복되는 **제네릭 타입**(`Map<K, List<String>>`) | `typealias` | (4) — 이것이 본래 자리다 |
| **함수 타입**에 이름(`(String) -> Int`) | `typealias` | (4) — 단, 구현이 필요하면 목록의 **36번 주제** `fun interface` |
| 한 클래스 안에서만 쓰는 긴 타입 | **중첩** `typealias`(2.3+) | (5) — 이름 공간이 그 클래스다 |
| **섞이면 안 되는** ID·단위 | ★★★ **`value class`** | (7) — 별칭은 검사가 없다 |
| 이름 충돌을 피하려는 **import 별명** | `import a.b.C as D` | 별칭 선언이 필요 없다 |
| Java 에서 쓸 API 의 타입 | 어느 쪽이든 Java 는 **원래 타입**을 본다 | (3) |

## 핵심 문장

1. **`typealias` 는 새 타입을 만들지 않는다** — `UserId` 와 `OrderId` 를 뒤바꿔 넣어도 컴파일된다.
2. 원래 타입으로 풀어 **같은 서명이면 오버로드가 충돌**한다 — 진단이 별칭을 **풀어서** 말한다.
3. JVM descriptor 에는 **흔적이 없다**(런타임 비용은 **잴 것이 없다**) — 그러나 **Kotlin 메타데이터에는 이름이 남는다.**
4. 중첩 타입 별칭은 **2.2 도입 · 2.3 Stable** — 2.4.20 에서는 **옵트인 없이** 되고, 2.2 판으로 낮추면 컴파일러가 그 경계를 말한다.
5. 중첩 별칭은 **바깥의 타입 파라미터를 못 잡는다.** 지역 별칭은 **아직 실험**이다.
6. **안전이 필요하면 `value class`, 이름만 필요하면 `typealias`** — 이 호출에서의 JVM 서명은 **같고**, 다른 것은 **검사**다.

## 관련 자료

- [26번 주제](../26-value-class-and-boxing/) — ★★★ **짝.** 새 타입을 **만드는** 쪽. 이름 뭉개기·박싱 자리·`init` 검사가 거기다.
- [28번 주제](../28-generics-variance-in-out-star-where/) — 변성. 함수 타입 별칭에 `? super` 가 붙는 이유가 거기다.
- 목록의 **36번 주제** — 함수 타입·`fun interface`. 함수 타입에 **이름**만 줄지 **인터페이스**를 만들지가 거기다.
- [`../../../go/syntax/22-type-assertion-any-and-comparable/`](../../../go/syntax/22-type-assertion-any-and-comparable/) — Go 의 `any` 가 `interface{}` 의 **별칭**이라는 것.
- [`../../../ts/syntax/05-structural-typing/`](../../../ts/syntax/05-structural-typing/) — 구조적 타입과 **브랜드 타입**의 정본.
- [`../../../ts/syntax/08-interface-vs-type/`](../../../ts/syntax/08-interface-vs-type/) — TS 의 `type` 별칭과 `interface` 의 차이.

## 용어 풀이

> **타입 별칭(type alias)** — 기존 타입에 **다른 이름**을 주는 선언. 새 타입이 **아니다.**\
> 예: `typealias UserId = String`.

> **중첩 타입 별칭(nested type alias)** — 클래스·인터페이스 **안에** 선언한 별칭. 2.2 도입, 2.3 Stable.\
> 예: `class Router { typealias Route = Pair<String, Handler> }` → `Router.Route`.

> **비캡처(non-capturing)** — 중첩 별칭이 **바깥 클래스의 타입 파라미터를 잡지 않는다**는 제약.

> **지역 타입 별칭(local type alias)** — 함수 **안에** 선언한 별칭. 이 판(2.4.20)에서도 **실험**이다(`-Xlocal-type-aliases`).

> **`-language-version`** — 컴파일러가 **옛 언어 판의 규칙**으로 검사하게 하는 옵션. 판 경계를 물을 때 쓴다.

> **Kotlin 메타데이터(`kotlin.Metadata`)** — Kotlin 전용 정보를 클래스 파일에 담는 애너테이션. `javap -v` 의 `d1`·`d2` 로 보인다. Java 와 JVM 은 안 읽는다.

> **정의된 타입(defined type)** — Go 의 `type A B`. **새 타입**을 만든다. `type A = B`(별칭)와 `=` 한 글자로 갈린다.

> **브랜드 타입(branded type)** — TS 에서 **가짜 프로퍼티를 교차 타입으로 붙여** 명목 타입을 흉내 내는 관용구.

## 더 들어가면

- **왜 별칭에 검사를 안 붙였나** — 별칭의 본래 목적은 **긴 타입을 줄이는 것**((4))이다. `Table<Int>` 가 `MutableMap<Int, MutableList<String>>` 과 **대입되지 않으면** 별칭을 쓰는 코드와 안 쓰는 코드가 섞일 때마다 변환이 필요해진다. 「이름만 바꾼다」는 약속이 있어야 **아무 비용 없이** 도입할 수 있다 — 검사가 필요한 자리는 **다른 도구**(`value class`)의 몫으로 떼어 냈다.
- **Go 와의 차이가 말하는 것** — Go 는 1.9 에서 별칭(`type A = B`)을 들이며 **기존의 새 타입 문법과 `=` 로** 갈랐고, 두 꼴 모두 런타임 표현이 같다. Kotlin 은 JVM 이 **값 타입을 따로 갖지 않으므로** 「새 타입인데 비용은 없는 것」을 만들려면 `value class` 라는 **따로 된 장치**와 그 대가(박싱 자리·이름 뭉개기)가 필요했다. **두 꼴이 한 문법으로 갈리느냐, 두 문법으로 갈리느냐**는 런타임이 무엇을 주느냐에 달렸다.
