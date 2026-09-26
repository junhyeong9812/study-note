# kotlin/syntax/29 — 타입 별칭·중첩 타입 별칭 (2.2+) — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [26번 주제](../26-value-class-and-boxing/)다 — ★★ **짝이다.** 거기는 새 타입을 **만드는** 쪽, 여기는 **안 만드는** 쪽.
> 문항 10개 중 코드블록이 붙는 예측형은 6개다.
> 바이트코드를 묻는 문항은 **`kotlinc` 기본 `-jvm-target`(1.8)** 기준이다.
> 이 주제의 모든 답은 **kotlinc 2.4.20 · JRE 21.0.5** 에서 실제로 던져 받은 것이다(Go·TS 는 **go1.27.1 · tsc 7.0.2**).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 두 ID 를 뒤바꿔 넣으면 (예측)

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

- 컴파일되는가? 된다면 `A`\~`D` 에 무엇이 찍히는가?

### 2. ★★ 별칭 타입과 원래 타입으로 오버로드하면 (예측)

```kotlin
// taclash.kt
typealias UserId = String

fun f(x: UserId) = "UserId"
fun f(x: String) = "String"
```

- 컴파일되는가? 에러가 몇 줄이고, ★★ 첫 에러 목록의 **둘째 줄**에는 `f` 의 서명이 **어떻게** 적히는가?

### 3. ★ 제네릭·함수 타입·중첩 별칭 (예측)

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

- `A`\~`C` 에 무엇이 찍히는가?
- `javap -p Router.class` 로 보면 `routes` 필드의 타입에 `Route`·`Handler` 라는 이름이 남는가?

### 4. ★★★ 판을 낮춰 던지면 (예측)

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

- 기본(2.4.20)으로 컴파일하면? 옵트인이 필요한가?
- `-language-version 2.2` 로는? 거기에 `-Xnested-type-aliases` 를 더하면?

### 5. ★ 제네릭 클래스 안의 별칭 (예측)

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

- 세 별칭 중 막히는 것은 어느 것이고, 각각 무엇이라고 말하는가?

### 6. ★★ 별칭 쪽과 값 클래스 쪽을 똑같이 뒤바꾸면 (예측)

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

- 에러는 **어느 줄**에서 나는가? 13번째 줄은?
- 올바르게 부르는 판(`tavsok.kt`)을 `javap -s -p` 로 보면 `cancelA` 와 `cancelV` 의 descriptor 는 같은가?

### 7. 별칭은 클래스 파일 어디에 남나 (경계)

- 1번의 `cancel` 의 descriptor 에 `UserId` 가 있는가?
- ★★ 「`javap` 에 별칭은 흔적도 없다」는 맞는 문장인가? 상수 풀과 `kotlin.Metadata` 를 근거로 답해 보라.

### 8. 왜 별칭에 검사를 안 붙였나 (왜)

- 별칭의 **본래 용도**는 무엇이고, 검사가 붙으면 그 용도가 어떻게 망가지는가?
- 런타임 비용을 「재 봤더니 같았다」가 아니라 「**잴 것이 없다**」고 적는 이유는?

### 9. Go 의 두 꼴 (연결)

- Go 의 `type AliasID = string` 과 `type NewID string` 에 `string` 변수를 넘기면 각각 어떻게 되는가?
- Kotlin 에서 이 두 꼴에 대응하는 문법은 각각 무엇인가? 런타임 표현은 어떻게 다른가?

### 10. TS 의 `type` 과 브랜드 (연결)

- TS 의 `type UserId = string` 은 새 타입을 만드는가? 막으려면 무엇을 하는가?
- Kotlin 에서 같은 일을 하는 것은 무엇이고, 무엇이 **흉내가 아닌가**?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
