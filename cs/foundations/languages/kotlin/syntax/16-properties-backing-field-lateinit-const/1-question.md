# kotlin/syntax/16 — 프로퍼티: backing field·커스텀 접근자·`lateinit`·`const` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [15번 주제](../15-class-declaration-constructors-and-init/)다.
> ★ **초기화가 언제 도는지는 [15번 주제](../15-class-declaration-constructors-and-init/)가 정본**이고,
> 위임(`by lazy`·`observable`)은 [17번 주제](../17-delegated-properties/), 확장 프로퍼티는 [13번 주제](../13-extension-functions-and-properties/)가 정본이다.
> 여기는 **프로퍼티 하나가 필드와 접근자로 어떻게 쪼개지나**를 묻는다.
> 이 주제는 [17번 주제](../17-delegated-properties/)·[목록의 **35번 주제**](../35-annotations-and-use-site-targets/)·**39번 주제**의 뿌리다.
> Java 쪽 짝은 [`../../../java/syntax/06-initialization-order/`](../../../java/syntax/06-initialization-order/)의 「컴파일 타임 상수」 절이다.
> 문항 11개 중 코드블록이 붙는 예측형은 6개다.
> 바이트코드를 묻는 문항은 **`kotlinc` 기본 `-jvm-target`(1.8)** 기준이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 프로퍼티 일곱 개에 필드가 몇 개 생기는가 (예측)

```kotlin
// fields.kt
class Person(val first: String, val last: String) {
    // ① 기본 접근자 — 저장한다
    var age: Int = 0

    // ② 커스텀 게터에서 field 를 안 쓴다 — 계산만 한다
    val full: String
        get() = "$first $last"

    // ③ 커스텀 게터에서 field 를 쓴다 — 저장한다
    var nickname: String = "none"
        get() = field.uppercase()
        set(value) {
            field = value.trim()
        }

    // ④ 세터만 커스텀이고 게터는 기본 — 저장한다
    var note: String = ""
        set(value) {
            field = "[$value]"
        }

    // ⑤ 계산 프로퍼티인데 var — 게터·세터 둘 다 field 를 안 쓴다
    var initial: String
        get() = first.take(1)
        set(value) {
            println("   버린다: $value")
        }
}
```

- `javap -p -s` 로 보면 **필드가 몇 개**이고 **어느 것들**인가?
- 접근자는 몇 개 생기는가 — 필드가 없는 프로퍼티에도 접근자가 있는가?
- `initial` 은 `var` 인데 필드가 있는가 — 컴파일러가 뭐라고 하는가?
- 필드가 생기는 기준을 **한 문장**으로 말하면 무엇인가?

### 2. ★★ `lateinit` 을 여섯 자리에 붙이면 (예측)

```kotlin
// badlateinit.kt
class Holder {
    lateinit var n: Int
    lateinit var s: String?
    lateinit val v: String
}
```

```kotlin
// badlateinit2.kt
class Holder<T> {
    lateinit var d: Double
    lateinit var b: Boolean
    lateinit var init: String = "a"
    lateinit var t: T
    lateinit var acc: String
        get() = "x"
}
```

- 에러는 각각 **몇 건**이고 문구는 **몇 종류**인가 — 전문을 대 보라.
- `T` 는 왜 거부되는가 — 무엇으로 바꾸면 통과하는가?
- 제약이 그렇게 정해진 **이유**는 무엇인가 — 구현을 떠올려 보라.
- `lateinit` 은 클래스 프로퍼티에만 붙는가?

### 3. ★★ 대입 전에 읽으면 무엇이 나오는가 (예측)

```kotlin
// late.kt
class Service {
    lateinit var conn: String

    fun status(): String = if (::conn.isInitialized) "초기화됨: $conn" else "아직"

    fun use(): Int = conn.length
}

fun main() {
    val s = Service()
    println("A 초기화 전 status() : ${s.status()}")
    try {
        s.use()
    } catch (e: Throwable) {
        println("B 잡힌 예외 : ${e::class.qualifiedName}")
        println("C 메시지    : ${e.message}")
    }
    s.conn = "jdbc:...";
    println("D 대입 후 status()   : ${s.status()}")
    println("E use()              : ${s.use()}")
}
```

- `A`\~`E` 는 각각 무엇을 찍는가?
- 그 예외의 **완전한 이름**은 무엇인가 — `NullPointerException` 인가?
- `javap -p` 로 보면 `conn` 필드의 **가시성**은 무엇인가 — 다른 프로퍼티와 다른가?
- `::conn.isInitialized` 는 무슨 명령으로 내려가는가 — 리플렉션인가?

### 4. ★★★ 라이브러리만 다시 빌드하면 (예측)

```kotlin
// lib.kt
object Config {
    const val VERSION: String = "1.0"
    val BUILD: String = "1.0"
}
```

```kotlin
// app.kt
fun main() {
    println("F const val VERSION : ${Config.VERSION}")
    println("G      val BUILD    : ${Config.BUILD}")
}
```

- `lib.kt` 와 `app.kt` 를 따로 컴파일한 뒤 `javap -c -p` 로 `AppKt` 를 보면 `F` 줄과 `G` 줄이 어떻게 다른가?
- `lib.kt` 를 `"2.0"` 으로 고쳐 **라이브러리만** 다시 컴파일하고 실행하면 `F`·`G` 는 각각 무엇을 찍는가?
- 그 차이를 허용하는 **클래스 파일 속성**의 이름은 무엇인가?
- 그래서 무엇에 `const` 를 쓰면 안 되는가?

### 5. ★ `const` 를 붙일 수 없는 세 자리 (예측)

```kotlin
// badconst.kt
class Holder {
    const val inClass: Int = 1
}

const val listConst: List<Int> = listOf(1)
const val computed: Int get() = 1
```

- 에러는 몇 건이고 문구는 각각 무엇인가?
- 셋의 공통점을 한 문장으로 말하면 무엇인가?
- `const val` 을 쓸 수 있는 자리는 어디어디인가?
- `const val` 과 일반 `val` 은 **필드 가시성**이 어떻게 다른가?

### 6. ★ `field = …` 절이 이 판에서 되는가 (예측)

```kotlin
// ebf.kt
class Holder {
    val items: List<String>
        field = mutableListOf<String>()

    fun add(s: String) {
        items.add(s)
    }
}

fun main() {
    val h = Holder()
    h.add("a")
    println("H 바깥에서 본 타입 : ${h.items::class.simpleName}, 값 ${h.items}")
}
```

- `kotlinc 2.4.20` 에서 **플래그 없이** 컴파일되는가 — 경고는?
- `-language-version 2.3` 으로 던지면 무엇이 나오는가 — 문구를 그대로 대 보라.
- `H` 는 무엇을 찍는가 — 게터의 선언 타입과 런타임 클래스가 같은가?
- 이 문법이 대체한 **예전 관용구**는 무엇인가?

### 7. `field` 는 어디에 있는 이름인가 (경계)

- 메서드 안에서 `field` 를 쓰면 어떻게 되는가 — 문구를 그대로 대 보라.
- 세터 안에서 `field` 대신 프로퍼티 이름을 쓰면 무슨 일이 생기는가?
- 커스텀 게터가 있는 프로퍼티에 `= "x"` 를 붙이면 무엇이 나오는가?
- 그 에러 문구는 1번의 답을 어떻게 다시 말하는가?

### 8. `isInitialized` 를 부를 수 있는 자리 (경계)

- `lateinit` 이 **아닌** 프로퍼티에 `::x.isInitialized` 를 쓰면 어떻게 되는가?
- 클래스 **밖에서** `s::conn.isInitialized` 를 쓰면 어떻게 되는가 — 문구를 그대로 대 보라.
- 뒤쪽 에러가 말하는 「접근할 수 없다」는 무엇에 대한 접근인가?
- 그럼 바깥에서 「초기화됐나」를 알려면 무엇을 만들어야 하는가?

### 9. `lateinit` 의 제약이 전부 한 곳에서 나온다 (왜)

- `lateinit` 프로퍼티의 게터 바이트코드는 어떤 모양인가?
- 그 모양에서 「원시 타입 금지」가 어떻게 따라 나오는가?
- 「nullable 금지」는 어떻게 따라 나오는가?
- 「커스텀 접근자 금지」는 1번의 어느 사실과 이어지는가?

### 10. 저장하지 않는 프로퍼티의 대가 (경계)

- 커스텀 게터만 있는 프로퍼티는 읽을 때마다 무엇을 하는가?
- 그것이 문제가 되는 상황은 어떤 것인가?
- 「한 번만 계산하고 저장」하려면 무엇을 쓰는가 — 정본은 어느 주제인가?
- 원시 타입인데 「나중에 주입」해야 하면 무엇을 쓰는가?

### 11. 확장 프로퍼티는 이 축의 어디에 놓이는가 (연결)

- `val Cup.cups: Int = ml / 200` 은 어떤 에러가 나는가 — 1번·7번의 어느 에러와 같은가?
- 확장 프로퍼티는 무엇으로 컴파일되는가 — 정본은 어느 주제인가?
- 이 주제의 축(필드 유무)으로 보면 확장 프로퍼티는 어느 칸인가?
- 위임 프로퍼티(`by`)의 필드에는 무엇이 들어 있는가 — 정본은 어느 주제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
