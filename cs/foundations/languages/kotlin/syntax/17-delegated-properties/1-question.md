# kotlin/syntax/17 — 위임 프로퍼티: `by lazy`·`observable`·`Map` 위임 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [16번 주제](../16-properties-backing-field-lateinit-const/)다.
> ★ **backing field 와 `lateinit` 은 [16번 주제](../16-properties-backing-field-lateinit-const/)가 정본**이고,
> `inline` 은 [11번 주제](../11-inline-functions/), 연산자 규약 전반은 목록의 **31번 주제**,
> **클래스** 위임(`class A : B by b`)은 목록의 **21번 주제**가 정본이다.
> 여기는 **프로퍼티** 위임만 묻는다.
> 이 주제는 목록의 **21번 주제**·**31번 주제**·**35번 주제**의 뿌리다.
> 문항 11개 중 코드블록이 붙는 예측형은 6개다.
> 바이트코드를 묻는 문항은 **`kotlinc` 기본 `-jvm-target`(1.8)** 기준이다.
> ⚠️ 8번은 **되풀이 돌리면 답이 달라지는** 문항이다 — 외울 것은 숫자가 아니라 성질이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ 인터페이스를 하나도 구현하지 않은 객체를 `by` 뒤에 두면 (예측)

```kotlin
// custom.kt
import kotlin.reflect.KProperty

class Loud(private var stored: String) {
    operator fun getValue(thisRef: Any?, property: KProperty<*>): String {
        println("   getValue  — thisRef=${thisRef?.let { it::class.simpleName }}, property.name=${property.name}")
        return stored
    }

    operator fun setValue(thisRef: Any?, property: KProperty<*>, value: String) {
        println("   setValue  — property.name=${property.name}, value=$value")
        stored = value
    }
}

class Screen {
    var title: String by Loud("처음")
}

fun main() {
    val s = Screen()
    println("A 읽는다")
    println("   결과 : ${s.title}")
    println("B 쓴다")
    s.title = "바뀜"
    println("C 다시 읽는다")
    println("   결과 : ${s.title}")
}
```

- 컴파일되는가 — `Loud` 는 무엇을 구현했는가?
- `A`·`B`·`C` 아래에 각각 무엇이 찍히는가?
- `thisRef` 에는 무엇이 들어오는가 — 최상위 프로퍼티면 어떻게 되는가?
- `property.name` 은 무엇이고 그것이 어디에 쓰이는가?

### 2. ★★★ 위임 둘을 둔 클래스의 필드와 정적 배열 (예측)

```kotlin
// dcode.kt
import kotlin.properties.Delegates

class Conf {
    val url: String by lazy { "http://x" }
    var level: Int by Delegates.observable(0) { _, old, new ->
        println("   level $old -> $new")
    }
}
```

- `javap -p -s` 로 보면 **필드가 몇 개**이고 이름이 무엇인가?
- `$$delegatedProperties` 배열의 **길이**는 얼마인가 — 위임이 둘인데 왜 그런가?
- `getUrl()` 과 `getLevel()` 이 위임 객체를 부르는 모양이 어떻게 다른가?
- 그 배열은 **언제** 만들어지는가?

### 3. ★★ 인자 없는 `lazy { }` 는 어느 모드인가 (예측)

```kotlin
// lazymode.kt
class Conf {
    val d: String by lazy { "default" }
    val s: String by lazy(LazyThreadSafetyMode.SYNCHRONIZED) { "sync" }
    val p: String by lazy(LazyThreadSafetyMode.PUBLICATION) { "pub" }
    val n: String by lazy(LazyThreadSafetyMode.NONE) { "none" }
}

fun main() {
    val c = Conf()
    for (name in listOf("d", "s", "p", "n")) {
        val f = Conf::class.java.getDeclaredField("$name\$delegate")
        f.isAccessible = true
        println("A $name 의 위임 객체 클래스 : ${f.get(c)::class.qualifiedName}")
    }
    println("B 기본과 SYNCHRONIZED 가 같은 클래스인가 : " +
        (Conf::class.java.getDeclaredField("d\$delegate").also { it.isAccessible = true }.get(c)::class ==
         Conf::class.java.getDeclaredField("s\$delegate").also { it.isAccessible = true }.get(c)::class))
}
```

- 네 프로퍼티의 위임 객체 **클래스 이름**은 각각 무엇인가?
- `B` 는 무엇을 찍는가?
- 이 프로그램이 필드 이름을 `"$name\$delegate"` 로 만드는 근거는 2번의 무엇인가?
- 문서를 안 읽고 이렇게 확인하는 것이 왜 더 강한 근거인가?

### 4. ★ 두 콜백이 도는 시점 (예측)

```kotlin
// obs.kt
import kotlin.properties.Delegates

class Form {
    var name: String by Delegates.observable("빈칸") { prop, old, new ->
        println("   observable — ${prop.name}: '$old' -> '$new'")
    }

    var age: Int by Delegates.vetoable(0) { prop, old, new ->
        println("   vetoable   — ${prop.name}: $old -> $new  (통과? ${new >= 0})")
        new >= 0
    }

    var required: String by Delegates.notNull<String>()
}

fun main() {
    val f = Form()
    println("A name 에 대입")
    f.name = "kim"
    println("   지금 값 : ${f.name}")

    println("B age 에 10")
    f.age = 10
    println("   지금 값 : ${f.age}")

    println("C age 에 -1 (거부된다)")
    f.age = -1
    println("   지금 값 : ${f.age}")

    println("D notNull 을 대입 전에 읽으면")
    try {
        f.required
    } catch (e: Throwable) {
        println("   ${e::class.qualifiedName} : ${e.message}")
    }
}
```

- `A`\~`D` 아래에 각각 무엇이 찍히는가?
- `C` 에서 콜백은 **도는가 안 도는가**, 값은 어떻게 되는가?
- 두 콜백이 값 대입의 **앞인가 뒤인가** — 각각 말해 보라.
- `D` 의 예외 타입은 무엇인가 — `lateinit` 의 그것과 같은가?

### 5. ★ 맵이 잘못돼 있으면 언제 터지는가 (예측)

```kotlin
// mapdel.kt
class User(val src: Map<String, Any?>) {
    val name: String by src
    val age: Int by src
}

class MutUser(val src: MutableMap<String, Any?>) {
    var name: String by src
}

fun main() {
    val u = User(mapOf("name" to "kim", "age" to 30))
    println("E name : ${u.name}   age : ${u.age}")

    val m = mutableMapOf<String, Any?>("name" to "lee")
    val mu = MutUser(m)
    println("F 처음 : ${mu.name}")
    mu.name = "park"
    println("G 대입 뒤 프로퍼티 : ${mu.name}")
    println("H 대입 뒤 맵 자체   : $m")

    println("I 키가 없으면")
    val bad = User(mapOf("age" to 1))
    try {
        bad.name
    } catch (e: Throwable) {
        println("   ${e::class.qualifiedName} : ${e.message}")
    }

    println("J 타입이 다르면")
    val wrong = User(mapOf("name" to "kim", "age" to "서른"))
    try {
        wrong.age
    } catch (e: Throwable) {
        println("   ${e::class.qualifiedName} : ${e.message}")
    }
}
```

- `E`\~`H` 는 각각 무엇을 찍는가 — 대입이 맵 자체를 바꾸는가?
- `val bad = User(mapOf("age" to 1))` 이라는 **줄 자체**는 성공하는가?
- `I`·`J` 의 예외 타입과 메시지는 각각 무엇인가?
- `J` 의 메시지가 `Int` 가 아니라 다른 타입을 말한다면 그 이유는 2번의 무엇인가?

### 6. ★ 함수 안에서도 되는가 (예측)

```kotlin
// local.kt
fun expensive(): String {
    println("   초기화 람다가 돌았다")
    return "값"
}

fun main() {
    println("K 지역 변수에 by lazy 를 건다")
    val v: String by lazy { expensive() }
    println("   선언만 했을 때 — 위에 아무 줄도 안 찍혔어야 한다")
    println("   첫 번째 읽기 : $v")
    println("   두 번째 읽기 : $v")
}
```

- 출력은 어떤 순서로 나오는가 — 초기화 람다는 **몇 번** 도는가?
- `javap -c -p` 로 `main()` 을 보면 `$$delegatedProperties` 가 있는가?
- `kotlin/LazyKt.lazy` 는 **실제 호출로 남는가** — 그것이 뜻하는 바는?
- 이 사실은 [11번 주제](../11-inline-functions/)·[14번 주제](../14-scope-functions/)와 어떻게 대비되는가?

### 7. 규약을 안 지킨 객체를 `by` 뒤에 두면 (경계)

- `class Plain(var stored: String)` 을 `var title: String by Plain("x")` 에 쓰면 에러가 **몇 건**인가?
- 에러 문구를 그대로 대 보라 — 무엇이 유난히 친절한가?
- `getValue` 만 있고 `setValue` 가 없으면 어떻게 되는가?
- `operator` 를 빼면 어떤 종류의 에러로 보이는가?

### 8. ⚠️ 여덟 스레드가 동시에 읽으면 (예측)

- 세 모드에서 **초기화 람다가 몇 번** 도는가?
- 세 모드에서 **스레드들이 본 객체가 몇 개**인가?
- 이 실험을 열두 번 돌리면 **어느 칸이 흔들리고 어느 칸이 안 흔들리는가**?
- 그래서 외울 것은 숫자인가 성질인가 — 성질을 세 줄로 적어 보라.

### 9. 세 구현이 무엇으로 갈리는가 (왜)

- `SynchronizedLazyImpl`·`SafePublicationLazyImpl`·`UnsafeLazyImpl` 의 **필드**는 각각 무엇인가?
- 세 `getValue()` 안에 `monitorenter` 와 CAS 가 각각 몇 개씩 있는가?
- 그 구조에서 8번의 성질이 어떻게 따라 나오는가?
- 「`NONE` 이 빠르다」는 이 근거로 말할 수 있는가?

### 10. `by lazy` 만 `KProperty` 를 안 받는다 (경계)

- 2번에서 배열 길이가 `1` 이었던 이유를 한 문장으로 말해 보라.
- 직접 만든 위임(1번)은 `KProperty` 를 받았는가?
- 이것은 언어 규칙인가 최적화인가?
- 그럼 `by lazy` 에서 `property.name` 을 쓸 방법이 있는가?

### 11. 16번의 「서랍」과 어떻게 이어지는가 (연결)

- [16번 주제](../16-properties-backing-field-lateinit-const/)의 축(필드 유무)으로 보면 위임 프로퍼티는 어느 칸인가?
- 그 필드에는 무엇이 들어 있는가 — 값인가?
- `lateinit` 과 `Delegates.notNull()` 은 각각 어느 타입에 쓰는가, 예외는 어떻게 다른가?
- `class A : B by b` 는 이 주제인가 다른 주제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
