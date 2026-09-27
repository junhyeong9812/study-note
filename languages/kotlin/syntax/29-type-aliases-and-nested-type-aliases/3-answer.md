# kotlin/syntax/29 — 타입 별칭·중첩 타입 별칭 (2.2+) — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javap` 에서 실제로 얻었다(Go·TS 는 **go1.27.1 · tsc 7.0.2**).\
> 역어셈블은 **기본 `-jvm-target`(1.8 · `major version: 52`)** 이 정본이다.
> ★★ 아래 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적은 자리가 없다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 컴파일된다 — `B` 줄에 **뒤바뀐 값이 그대로** 찍힌다

**출력**

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

**왜 그런가**

- ★★★ `UserId`·`OrderId` 는 둘 다 **`String` 의 다른 이름**이다. `cancel(o, u)` 는 `cancel(String, String)` 에 `String` 둘을 넘긴 것이라 **막을 근거가 없다.**
- `C` — 리터럴도 들어간다. `D` — 런타임 클래스는 **`String`**.

### 2. ★★ 에러 두 줄 — 둘째 줄에 **`fun f(x: String): String`** 이 적힌다

**출력**

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

**왜 그런가**

- ★★★ `f(x: UserId)` 쪽 에러의 목록에 **`String`** 이 적혔다 — 컴파일러가 별칭을 **풀어서** 본다. 두 선언은 **같은 함수의 두 벌**이다.
- [26번 주제](../26-value-class-and-boxing/) (1)의 `lookup(UserId)`·`lookup(Long)` 은 **공존했다** — 새 타입이라 이름을 뭉개 갈랐다.

### 3. ★ `A {1=[a]}` · `B 4 true` · `C /x 20` — 필드 타입에 별칭 이름은 **없다**

**출력**

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

**왜 그런가**

- ★★ `routes` 는 `List<Pair<String, Function1<String, Integer>>>` 로 **통째로 풀렸다.** `Route`·`Handler` 는 JVM 서명에 없다.
- ★ `add` 의 파라미터에는 `Function1<? super String, Integer>` — `Function1` 의 반공변 파라미터가 `? super` 로 번역됐다([28번 주제](../28-generics-variance-in-out-star-where/) (9)).

### 4. ★★★ 기본은 **옵트인 없이 통과** · 2.2 는 「only available since 2.3」 · 2.2 + `-Xnested-type-aliases` 는 통과

**출력**

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

**왜 그런가**

- ★★★ 컴파일러의 두 대답이 README 의 「**2.2.0 도입 · 2.3.0 Stable**」과 맞는다 — 2.2 에서는 **플래그로 켜는 기능**이었고, 2.3 부터 **기본**이다.
- ★ `-language-version 2.2` 는 **2.4.20 이 흉내 낸 2.2** 다. 진짜 2.2.0 컴파일러를 돌린 것은 아니다.

### 5. ★ `Items = List<T>` 는 「`unresolved reference 'T'.`」 · 지역 별칭은 「experimental」 · `inner` 안은 통과

**출력**

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

**왜 그런가**

- ★★ 중첩 별칭은 **비캡처** — 바깥 클래스의 `T` 를 못 본다. 자기 타입 파라미터를 받게 하면 된다(`typealias Items<X> = List<X>`).
- `inner class In` 안의 `X`(5번째 줄)는 **에러 줄에 없다.** 지역 별칭(9번째 줄)은 **이 판에서도 실험**이다 — 중첩과 다른 기능이다.

### 6. ★★ 에러는 **16번째 줄에만** — 13번째 줄(별칭)은 통과 · descriptor 는 **같다**(이름만 뭉개졌다)

**출력**

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

**왜 그런가**

- ★★★ 같은 뒤바꾸기가 **별칭 쪽은 통과, 값 클래스 쪽은 에러 둘**이다.
- ★★ descriptor 는 **둘 다 `(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;`** — 이 호출에서 JVM 이 받는 것은 **같다.** 다른 것은 **이름**(`cancelV-xSLm8gY`)과 **컴파일러의 검사**다.
- ★ 값 클래스의 비용은 **다른 자리**(제네릭·`Any`·인터페이스의 `box-impl` — [26번 주제](../26-value-class-and-boxing/) (2))에서 온다. 이 문서는 시간을 **안 쟀다.**

### 7. descriptor 에는 없다 — 그러나 「흔적도 없다」는 **틀렸다**: 상수 풀과 `d2` 에 이름이 있다

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

```text
===== javap -v o29a/TaassignKt.class | grep -n -E 'Utf8 +(UserId|OrderId)$|d2=' =====
124:  #112 = Utf8               UserId
126:  #114 = Utf8               OrderId
282:      d2=["UserId","","OrderId","cancel","user","order","main",""]
(exit 0)
```

- ★★ descriptor `(Ljava/lang/String;Ljava/lang/String;)…` 에는 별칭이 **없다** — JVM 이 쓰는 층이다.
- ★★★ **상수 풀에 `Utf8 UserId`·`Utf8 OrderId` 가 있고 `kotlin.Metadata` 의 `d2` 에도 있다** — Kotlin 컴파일러가 읽는 층이다. 정확한 문장은 「**JVM 에게는 없고 Kotlin 에게는 있다**」.
- 그 블록의 소스는 1번의 `taassign.kt` 다.

### 8. 본래 용도는 **긴 타입 줄이기** — 검사가 붙으면 별칭과 원래 타입 사이에 변환이 필요해진다 · 비교할 대상이 **하나뿐**이라 잴 것이 없다

- `Table<Int>` 와 `MutableMap<Int, MutableList<String>>` 이 대입되지 않으면, 별칭을 쓴 코드와 안 쓴 코드가 만날 때마다 **변환**해야 한다. 「이름만 바꾼다」는 약속이 **비용 0 의 도입**을 가능하게 한다.
- descriptor 가 **같으므로** 별칭을 쓴 메서드와 원래 타입으로 쓴 메서드는 **같은 메서드**다. 「재 봤더니 같았다」는 **두 대상을 쟀다**는 말이 되는데, 여기는 **대상이 애초에 하나**다(제4의 상태).

### 9. 별칭은 **통과**, 새 타입은 **에러** — Kotlin 은 `typealias` 와 `value class` 로 **문법이 둘로** 갈린다

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

- ★★ 에러가 **14번째 줄(`takeNew`) 하나뿐** — `=` 가 있는 별칭은 `string` 을 그대로 받았다.
- Kotlin 대응 — `type A = B` ↔ **`typealias`**, `type A B` ↔ **`@JvmInline value class`**. Go 의 새 타입은 **값 그대로**이고, Kotlin 의 값 클래스는 **자리에 따라 박싱**된다(JVM 이 값 타입을 따로 안 주기 때문).

### 10. 안 만든다 — 브랜드를 붙인다 · Kotlin 은 `value class` 가 **진짜 명목 타입**이다

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

- ★ 에러가 **9번째 줄(`loadB`) 하나뿐** — `load(order)` 는 통과했다. TS 의 `type` 은 **구조적 별칭**이다.
- 브랜드는 **없는 프로퍼티를 교차 타입으로 붙인 흉내**다([TS 05번](../../../ts/syntax/05-structural-typing/) (5)). Kotlin 의 `value class` 는 **컴파일러가 이름으로 가르는 타입**이라 흉내가 아니다 — 대신 JVM 위에서 박싱 자리라는 대가가 있다.

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
===== javap -version =====
21.0.5
(exit 0)
```

★ **흔들리는 칸과 안 흔들리는 칸**

| 흔들린다 | 안 흔들린다 |
|---|---|
| **없다** — 해시코드·주소를 찍지 않았다 | 출력 · `javap` 출력(descriptor·상수 풀·`d2`) |
| | 컴파일 에러의 **문구·`파일:줄:칸`**(kotlinc·go·tsc) · `-language-version` 게이트 문구 |
| | 모든 **종료 코드** |

> 근거 — 캡처 스크립트를 처음부터 다시 돌려 **블록 전체를 바이트 단위로 대조**했다.
>
> 실측 — `capture.sh blocks` 와 `capture.sh blocks-recheck` 를 처음부터 따로 돌려 `normalize-shaky.py` 로 대조했다 —\
> **블록 101개 · 동일 101 · 흔들린 칸 0 · ★고칠 것 0**(26\~29 네 주제를 한 캡처로 받았다). `diff -rq` 도 차이 0 이다.\
> ★ **정규화 규칙은 하나도 안 썼다** — 기본 넷(주소·PID·스레드 id·시간)에 걸리는 칸이 애초에 없었다.

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `taassign.kt` | ★★★ **뒤바꿔도 통과** · descriptor 에 없음 · ★ **메타데이터에 있음** | `kotlinc` → `java` → `javap -s -p` · `javap -v`(필터) |
| `taclash.kt` | ★★ 오버로드 **충돌** — 진단이 별칭을 풀어 말함 | `kotlinc`(실패가 결과) |
| `tagen.kt` | 제네릭·함수 타입·중첩 별칭 · JVM 서명에서 풀림 | `kotlinc` → `java` → `javap -p` |
| `tagate.kt` | ★★★ **판 경계** — 기본 · `-language-version 2.2` · `+ -Xnested-type-aliases` | `kotlinc` 세 판 → `java` |
| `tacap.kt` | 비캡처 제약 · `inner` 안의 별칭 · 지역 별칭 실험 | `kotlinc`(실패가 결과) |
| `tavs.kt` · `tavsok.kt` | ★★★ **별칭 대 값 클래스** — 검사와 descriptor | `kotlinc`(실패 1벌) · `kotlinc` → `java` → `javap -s -p`(필터) |
| `goal/main.go` + `go.mod` | Go 의 **두 꼴** | `go build`(실패가 결과) |
| `alias29.ts` | TS 의 별칭과 **브랜드** | `tsc --noEmit --strict`(실패가 결과) |
| `form29.kt` | 형태 한 벌(`Z`·`Y`·`X`) | `kotlinc` → `java` |

**구현 의존 항목** — descriptor 에서 별칭이 **풀리는 것**, **메타데이터에 이름이 남는 것**, 상수 풀 번호, 함수 타입 별칭에 `? super` 가 붙는 것, 진단 문구 — 이 컴파일러·판의 산출물이다. 지역 별칭의 **실험** 상태도 이 판(2.4.20)의 것이다.\
반면 **「별칭은 새 타입이 아니다」「같은 서명이면 충돌한다」「중첩 별칭은 바깥 타입 파라미터를 못 잡는다」「중첩 별칭 2.3 Stable」** 은 **언어의 계약**이다.

**★ 던져 봤더니 예상과 달랐던 것 — 두 건**

1. ★★★ **별칭 이름이 클래스 파일에 남아 있었다.** 「`javap` 에 흔적도 없다 — 잴 것이 없다」를 확인하려고 `-v` 로 상수 풀을 뒤졌더니 **`UserId`·`OrderId` 가 `Utf8` 로, 그리고 `kotlin.Metadata` 의 `d2` 에** 있었다(7번). 흔적이 없는 것은 **descriptor** 이지 클래스 파일 전체가 아니다.
2. ★★ **`inner class` 안의 별칭은 막히지 않았다**(5번). 「비캡처」를 「바깥에 기대는 자리에는 못 둔다」로 넓게 읽으면 틀린다 — 막히는 것은 **바깥의 타입 파라미터를 쓰는 것**이다.
