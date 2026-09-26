# kotlin/syntax/58 — null 처리 관용구 — `?.let`·`requireNotNull`·엘비스 + `return` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — 공식 문서 페이지([Null safety](https://kotlinlang.org/docs/null-safety.html) · [Coding conventions](https://kotlinlang.org/docs/coding-conventions.html))는 **이 작업에서 열지 못했다**(외부 네트워크를 쓰지 않았다). ★★ 그래서 「계층마다 무엇을 쓰라」는 권고의 **공식 출처는 확인 못 함**이다 — 이 문서의 권고는 전부 **이 문서의 판단**이고 그렇게 표시한다((5)). `requireNotNull`·`checkNotNull` 이 무엇을 던진다는 **계약(KDoc)** 은 [51번 주제](../51-preconditions-require-check-error-todo/)가 stdlib 소스 jar 에서 발췌했다 — 여기서는 인용만 한다.
> **실행 검증** — 이 문서의 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `java`·`javac`·`javap` 에서 실제로 얻었다.\
> `kotlinc` 6회 · `javac` 1회 · `java` 6회(`let58` 은 표준 출력·표준 오류를 따로 받아 2회) · `javap` 1회.\
> ★★ 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적지 않았다. **「경계에 따라 결과가 갈린 수단 N / M」·「예외 없이 지나간 칸 N / M」은 격자 프로그램이 스스로 센 것**이다.
> **버전** — `?.`·`?:`·`!!`·`let`·`requireNotNull`·`checkNotNull`·`error` 는 전부 **1.0** 부터 있다(판 경계가 없는 주제다). `requireNotNull`·`checkNotNull` 뒤의 스마트 캐스트를 만드는 **계약**(`contract { returns() implies … }`)은 [51번 주제](../51-preconditions-require-check-error-todo/) (3)이 정본이다.
> **경계** — ★★ `?`·`?.`·`?:`·`!!` 의 **문법과 바이트코드**(`!!` = `Intrinsics.checkNotNull` · 메시지 없음 · `?:` 오른쪽의 `return`/`throw`)는 [03번 주제](../03-null-safe-types/) (3)(7)이, **스마트 캐스트가 깨지는 자리 아홉**은 [04번 주제](../04-smart-casts/) (2)가, **플랫폼 타입의 세 경우(A 쓰는 줄 · B 대입하는 줄 · C 안 터짐)** 는 [05번 주제](../05-platform-types/) (2)가, **`let` 이 무엇을 돌려주나**는 [14번 주제](../14-scope-functions/)가, `return`·`throw` 가 `Nothing` 이라 `?:` 오른쪽에 들어가는 것은 [34번 주제](../34-exceptions-nothing-and-try-expression/) (3)이, **어느 예외가 무엇을 뜻하나**(`require`=인자 · `check`=상태)는 [51번 주제](../51-preconditions-require-check-error-todo/) (1)이 정본이다. **여기는 「그 수단들을 어느 계층에 둘 것인가」와 「실패가 어디서 드러나나」만** 다룬다.\
> 「경계에서 즉시 검증해 non-null 도메인 타입으로 바꾼다」는 **설계 논지**는 [`../../언어-특성/README.md`](../../언어-특성/README.md) §2 가 원고째 적는다 — 여기서는 그 논지가 코드에서 어떤 모양인지만 본다. Java 쪽 방어(`Objects.requireNonNull`·`Optional`)는 [Java 60번](../../../java/syntax/60-null-handling/) · [Java 38번](../../../java/syntax/38-optional/)이, C# 의 같은 연산자들은 [C# 07번](../../../csharp/syntax/07-null-operators/)이 정본이다.
> 이 본문은 Claude 작성이다(원고 없음).

★★★ **본체는 첫째 창이다** — 「**판별 격자 — 경계 넷(외부 입력 파싱 · 공개 API 인자 · 내부 불변식 · 표시 계층) × 수단 여섯(`?: return` · `?.let` · `requireNotNull` · `checkNotNull` · `!!` · `?: error()`) → 던진 예외 · 메시지 · 스택 첫 프레임의 줄 · 부른 쪽이 받은 것**」. 둘째 본체는 **Java 가 준 `null` 이 「태어난 줄」과 「터진 줄」**(javac 한 쌍)이다.

## 이 주제가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **언어 보장 / API 계약** | 컴파일러와 KDoc 이 약속한 것 | ★ `!!` 는 `null` 이면 NPE([03번 주제](../03-null-safe-types/) (3)) · `?.` 는 `null` 이면 **오른쪽을 평가하지 않고** `null` · 스마트 캐스트 거부 진단((4)) · `requireNotNull` → `IllegalArgumentException` · `checkNotNull`·`error` → `IllegalStateException`(KDoc — [51번 주제](../51-preconditions-require-check-error-todo/)) |
| **이 판의 관찰** | kotlinc 2.4.20 + JDK 21.0.5 에서 이번에 본 것 | 격자의 예외·메시지·첫 프레임 줄 · 플랫폼 값을 non-null 인자로 넘길 때 **호출하는 줄에 박힌 `Intrinsics.checkNotNull`**(`javap`) · JVM 의 helpful NPE 문구 |
| ★★ **설계 권고** | 「어느 계층에 무엇을 두라」 | ★★★ **이 문서의 판단이다** — 공식 규약 문서는 열지 못했다. 권고는 (5)의 표 **한 곳에만** 모았고, 관찰 칸과 섞지 않는다 |

## 이 판

```text
===== kotlinc -version =====
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
(exit 0)
```

```text
===== javac -version =====
javac 21.0.5
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | (이 주제에는 없다) | 시간·주소·스레드를 찍지 않았다 — 단일 스레드 · 고정 입력 |
| 안 흔들린다 | 격자 24행 · 예외 클래스 · 메시지 · 첫 프레임의 **메서드 이름과 줄 번호** · 세는 줄 | 스택의 줄 번호는 클래스 파일의 `LineNumberTable` 에서 온다 — 소스와 컴파일러가 같으면 같다 |
| 안 흔들린다 | helpful NPE 문구(`Cannot invoke … because …`) | JDK 판에 매인다 — **21.0.5** 에서 본 것 |
| 안 흔들린다 | `javap` 의 명령·상수 풀 번호 · 진단 문구와 `줄:칸` · 종료 코드 | 같은 판이면 같다 |

★ 근거 — 캡처 스크립트를 처음부터 두 번 돌려 **블록 전체를 대조**했다(수치는 3-answer 의 「실행 검증」).

★ **줄 번호를 읽는 법** — 소스 펜스의 첫 줄(`// grid58.kt` 같은 파일명)은 **캡처가 붙인 것이라 실파일에 없다.** 스택의 `:21` 은 **그 다음 줄을 1 로 센** 번호다.

## 한눈에 — 쉽게 말하면

**`null` 은 「빈 상자」다. 빈 상자를 어느 창구에서 돌려보내느냐가 이 주제다.** 정문 접수처(외부 입력)는 「양식이 틀렸습니다」 하고 **돌려보내면** 되고, 담당 부서 창구(공개 API)는 「서류를 안 가져오셨네요 — **당신 잘못**」이라고 **도장 찍어** 돌려보내며, 금고실(내부)에서 빈 상자가 나오면 그건 **우리 쪽 사고**라 경보를 울린다. 진열대(표시)는 빈 상자면 **그 칸만 비워 두고** 넘어간다.
★ 그런데 어느 창구에서 어떤 도장을 찍든 **도장 자체는 창구를 모른다** — `requireNotNull` 은 어느 계층에 두어도 똑같이 `IllegalArgumentException` 을 던진다((1)). **창구에 맞는 도장을 고르는 것은 사람**이다.

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 조용히 돌려보낸다 | `?: return` · `?.let` — 예외 없음, 부른 쪽은 `null` 을 받는다 | (1) ★ |
| 「당신 잘못」 도장 | `requireNotNull` → `IllegalArgumentException` | (1) |
| 「우리 사고」 경보 | `checkNotNull` · `?: error()` → `IllegalStateException` | (1) |
| 이름 없는 경보 | `!!` → 메시지 없는 NPE | (1) · [03번 주제](../03-null-safe-types/) (3) |
| 남이 준 상자는 열어 봐야 안다 | Java 가 준 `null` — **쓰는 줄**에서, 또는 **한참 뒤 다른 함수**에서 터진다 | (2) ★★ |
| 진열대의 빈 칸이 아무 말도 안 한다 | `?.let { }` 이 건너뛴 원소는 **로그가 0줄** | (3) ★ |

```text
   외부 입력 ─▶ 공개 API ─▶ 내부 ─▶ 표시
   "12x"        name=null    prices["pear"]   nickname=null
     │             │            │               │
     ▼             ▼            ▼               ▼
   같은 수단이면 네 계층의 결과가 똑같다 — 수단이 결과를 정한다   (1)
     ?: return / ?.let  → 예외 없음, 부른 쪽은 null
     requireNotNull     → IllegalArgumentException, 그 줄
     checkNotNull       → IllegalStateException,   그 줄
     !!                 → NullPointerException (메시지 없음), 그 줄
     ?: error()         → IllegalStateException,   그 줄
   ── 그러니 「계층 → 수단」 짝짓기는 설계 판단이다   (5)
```

## 이 주제가 답하려는 질문

1. 수단마다 **실패가 어디서 어떤 모양으로 드러나나** — 예외 종류 · 메시지 · 첫 프레임 · 아예 안 드러나나.
2. **Java 가 준 `null`** 은 언제 터지나 — `!!` 와 플랫폼 타입의 차이는 「태어난 줄」과 「터진 줄」의 거리다.
3. 그래서 **계층마다 무엇을 둘 것인가** — 무엇이 관찰이고 무엇이 판단인가.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **판별 격자(실행)** | 경계 × 수단 → 예외 · 메시지 · 첫 프레임 · 부른 쪽이 받은 것((1)) | ★ **본체 창** |
| ★★★ **태어난 줄 대 터진 줄(javac 한 쌍)** | Java 가 준 `null` 이 어느 줄 어느 함수에서 터지나((2)) | ★ 둘째 본체 |
| ★★ **`javap -c`** | 플랫폼 값을 non-null 인자로 넘기는 줄에 **컴파일러가 심은 검사**((2)) | [03번 주제](../03-null-safe-types/) (4)(5)와 같은 창 |
| ★★ **표준 출력 / 표준 오류 가르기** | `?.let` 이 건너뛴 원소가 **아무 흔적도 안 남기는지**((3)) | — |
| ★ **컴파일 진단** | 스마트 캐스트가 안 되는 자리((4)) | 전수는 [04번 주제](../04-smart-casts/) (2) |
| **인용 — 다시 안 잰다** | `!!` 의 바이트코드 · 플랫폼 타입 A/B/C · 계약 함수의 기본 메시지와 KDoc | [03번 주제](../03-null-safe-types/) · [05번 주제](../05-platform-types/) · [51번 주제](../51-preconditions-require-check-error-todo/) |
| **부적용 — 계층** | ★★★ 「어느 계층인가」는 **실행이 모른다** — 격자에서 계층은 결과를 하나도 안 바꿨다((1)의 `0 / 6`) | 그래서 계층 판단은 (5)의 **권고층**으로 뺐다 |
| **부적용 — 비용** | 수단마다의 실행 시간은 **재지 않았다** — 전부 분기 한 번 또는 호출 한 번이고, 이 주제의 값은 **진단 정보**다 | — |

### (1) ★★★ 판별 격자 — 수단이 결과를 정한다

**언제 쓰나** — `null` 이 올 수 있는 자리에 무엇을 적을지 고를 때, 그리고 로그의 예외를 보고 **어느 층의 무엇이 막았는지** 거꾸로 짚을 때.

방법 — 네 계층 함수가 **각자 다른 `null`**(숫자가 아닌 문자열 · 넘겨받은 `null` 인자 · 맵에 없는 키 · 비어 있는 선택 항목)을 만나고, `when (m)` 의 가지마다 **수단 하나씩**으로 처리한다. 가지가 한 줄씩이라 **첫 프레임의 줄 번호가 곧 그 수단이 적힌 줄**이다. 마지막 세 줄은 프로그램이 센다 — 예외 종류별 칸 수 · **같은 수단인데 계층에 따라 결과가 갈린 수단의 수** · 예외 없이 지나간 칸 수.

```kotlin
// grid58.kt
// 경계 넷 × 수단 여섯 — 값이 null 일 때 무엇이 어디서 드러나나.
val means = listOf("?: return", "?.let", "requireNotNull", "checkNotNull", "!!", "?: error()")

// (1) 외부 입력 파싱 — 숫자가 아닌 문자열
fun parseLayer(m: String, raw: String): Int? {
    val v: Int? = raw.toIntOrNull()
    return when (m) {
        "?: return" -> { val n = v ?: return null; n * 2 }
        "?.let" -> v?.let { it * 2 }
        "requireNotNull" -> requireNotNull(v) { "not a number: $raw" } * 2
        "checkNotNull" -> checkNotNull(v) { "not a number: $raw" } * 2
        "!!" -> v!! * 2
        else -> (v ?: error("not a number: $raw")) * 2
    }
}

// (2) 공개 API 인자 — 호출한 쪽이 null 을 넘겼다
fun apiLayer(m: String, name: String?): Int? {
    return when (m) {
        "?: return" -> { val n = name ?: return null; n.length }
        "?.let" -> name?.let { it.length }
        "requireNotNull" -> requireNotNull(name) { "name is required" }.length
        "checkNotNull" -> checkNotNull(name) { "name is required" }.length
        "!!" -> name!!.length
        else -> (name ?: error("name is required")).length
    }
}

// (3) 내부 불변식 — 있어야 할 키가 맵에 없다
val prices = mapOf("apple" to 3)
fun coreLayer(m: String, key: String): Int? {
    val p: Int? = prices[key]
    return when (m) {
        "?: return" -> { val n = p ?: return null; n * 10 }
        "?.let" -> p?.let { it * 10 }
        "requireNotNull" -> requireNotNull(p) { "no price for $key" } * 10
        "checkNotNull" -> checkNotNull(p) { "no price for $key" } * 10
        "!!" -> p!! * 10
        else -> (p ?: error("no price for $key")) * 10
    }
}

// (4) 표시 계층 — 선택 항목(별명)이 비어 있다
class Profile(val nickname: String?)
fun viewLayer(m: String, u: Profile): Int? {
    val nick = u.nickname
    return when (m) {
        "?: return" -> { val n = nick ?: return null; n.length }
        "?.let" -> nick?.let { it.length }
        "requireNotNull" -> requireNotNull(nick) { "nickname missing" }.length
        "checkNotNull" -> checkNotNull(nick) { "nickname missing" }.length
        "!!" -> nick!!.length
        else -> (nick ?: error("nickname missing")).length
    }
}

val layers: List<Pair<String, (String) -> Int?>> = listOf(
    "parse" to { m -> parseLayer(m, "12x") },
    "api" to { m -> apiLayer(m, null) },
    "core" to { m -> coreLayer(m, "pear") },
    "view" to { m -> viewLayer(m, Profile(null)) },
)

fun main() {
    println(listOf("layer", "means", "thrown", "message", "first frame", "caller got").joinToString("\t"))
    val kinds = linkedMapOf<String, Int>()
    val byMeans = linkedMapOf<String, MutableSet<String>>()
    var cells = 0
    for ((layer, call) in layers) for (m in means) {
        cells++
        val row = try {
            val r = call(m)
            kinds.merge("none", 1, Int::plus)
            byMeans.getOrPut(m) { mutableSetOf() } += "none"
            listOf(layer, m, "-", "-", "-", "$r")
        } catch (e: Exception) {
            val k = e.javaClass.simpleName
            kinds.merge(k, 1, Int::plus)
            byMeans.getOrPut(m) { mutableSetOf() } += k
            val f = e.stackTrace[0]
            listOf(layer, m, k, "${e.message}", "${f.methodName}:${f.lineNumber}", "(exception)")
        }
        check(row.size == 6) { "column count" }
        println(row.joinToString("\t"))
    }
    println("thrown kinds: " + kinds.entries.joinToString(" · ") { "${it.key} ${it.value}" } + " (of $cells)")
    println("means whose outcome differs between layers: ${byMeans.values.count { it.size > 1 }} / ${byMeans.size}")
    println("cells with no exception: ${kinds["none"] ?: 0} / $cells")
}
```

```text
===== kotlinc grid58.kt -d o58g =====
(exit 0)
===== java -cp o58g:kotlin-stdlib.jar Grid58Kt =====
layer	means	thrown	message	first frame	caller got
parse	?: return	-	-	-	null
parse	?.let	-	-	-	null
parse	requireNotNull	IllegalArgumentException	not a number: 12x	parseLayer:10	(exception)
parse	checkNotNull	IllegalStateException	not a number: 12x	parseLayer:11	(exception)
parse	!!	NullPointerException	null	parseLayer:12	(exception)
parse	?: error()	IllegalStateException	not a number: 12x	parseLayer:13	(exception)
api	?: return	-	-	-	null
api	?.let	-	-	-	null
api	requireNotNull	IllegalArgumentException	name is required	apiLayer:22	(exception)
api	checkNotNull	IllegalStateException	name is required	apiLayer:23	(exception)
api	!!	NullPointerException	null	apiLayer:24	(exception)
api	?: error()	IllegalStateException	name is required	apiLayer:25	(exception)
core	?: return	-	-	-	null
core	?.let	-	-	-	null
core	requireNotNull	IllegalArgumentException	no price for pear	coreLayer:36	(exception)
core	checkNotNull	IllegalStateException	no price for pear	coreLayer:37	(exception)
core	!!	NullPointerException	null	coreLayer:38	(exception)
core	?: error()	IllegalStateException	no price for pear	coreLayer:39	(exception)
view	?: return	-	-	-	null
view	?.let	-	-	-	null
view	requireNotNull	IllegalArgumentException	nickname missing	viewLayer:50	(exception)
view	checkNotNull	IllegalStateException	nickname missing	viewLayer:51	(exception)
view	!!	NullPointerException	null	viewLayer:52	(exception)
view	?: error()	IllegalStateException	nickname missing	viewLayer:53	(exception)
thrown kinds: none 8 · IllegalArgumentException 4 · IllegalStateException 8 · NullPointerException 4 (of 24)
means whose outcome differs between layers: 0 / 6
cells with no exception: 8 / 24
(exit 0)
```

- ★★★ **계층은 결과를 하나도 안 바꿨다 — `0 / 6`.** 같은 수단이면 네 계층에서 **같은 예외 클래스**가 나왔다. 메시지만 각자 적은 글자다. **`requireNotNull` 은 자기가 인자 검사 자리에 있는지 모른다** — 내부 맵 조회(`coreLayer:36`)에 두어도 「인자가 틀렸다」는 `IllegalArgumentException` 을 던진다.
- ★★★ **예외 없이 지나간 칸 `8 / 24`** — `?: return` 과 `?.let` 두 수단 × 네 계층이다. 부른 쪽이 받은 것은 **둘 다 `null`** — 이 격자로는 두 수단이 **구별되지 않는다.** 차이는 코드에만 있다(「여기서 멈춘다」가 `return` 으로 **보이느냐**, `?.` 안에 **묻히느냐**).
- ★★ **첫 프레임은 언제나 수단이 적힌 그 줄**이다(`parseLayer:10`·`11`·`12`·`13` …) — `requireNotNull`·`checkNotNull`·`error` 는 `inline` 이라 **stdlib 안의 프레임이 스택에 안 남고**, 부른 함수의 그 줄이 맨 위다.
- ★★ **`!!` 만 메시지가 `null`** — 네 칸 전부. 줄 번호는 알려 주지만 **무엇이 없었는지는** 안 알려 준다([03번 주제](../03-null-safe-types/) (3)이 바이트코드로 본 까닭 — `checkNotNull(Object)` 에 메시지 자리가 없다).
- ★ `IllegalStateException` 이 `IllegalArgumentException` 의 두 배(8 대 4)인 것은 **수단 둘(`checkNotNull`·`?: error()`)이 같은 클래스**이기 때문이다 — 로그에서 **둘은 클래스로 못 가른다**(메시지로만).

### (2) ★★★ Java 가 준 `null` — 태어난 줄과 터진 줄

**언제 쓰나** — NPE 스택의 맨 위 줄을 보고 「여기가 원인이다」라고 읽으려 할 때.

```java
// Store58.java
import java.util.HashMap;
import java.util.Map;

public class Store58 {
    private static final Map<String, String> names = new HashMap<>();
    static { names.put("u1", "kim"); }

    public static String findName(String id) {
        return names.get(id);
    }
}
```

```kotlin
// plat58.kt
// Java 가 준 null 이 어디서 터지나 — 태어난 줄과 터진 줄
fun here(): Int = Throwable().stackTrace[1].lineNumber

fun greet(name: String): String = "hi " + name
fun firstLength(names: List<String>): Int = names[0].length

fun probe(label: String, block: () -> Int) {
    try {
        block()
        println("$label -> no exception")
    } catch (e: Exception) {
        val f = e.stackTrace[0]
        println("$label -> ${e.javaClass.simpleName}: ${e.message}")
        println("    first frame ${f.methodName}:${f.lineNumber}")
    }
}

fun main() {
    var born = 0
    probe("A") {
        born = here(); val n = Store58.findName("u9")!!
        n.length
    }
    println("    null born at line $born")
    probe("B") {
        val n = Store58.findName("u9"); born = here()
        greet(n).length
    }
    println("    null born at line $born")
    probe("C") {
        val n = Store58.findName("u9"); born = here()
        val names = listOf(n)
        firstLength(names)
    }
    println("    null born at line $born")
    probe("D") {
        val n = Store58.findName("u9"); born = here()
        val names: List<String> = listOf(n)
        names.size
    }
    println("    null born at line $born")
}
```

```text
===== javac -d o58j Store58.java =====
(exit 0)
===== kotlinc -cp o58j plat58.kt -d o58p =====
(exit 0)
===== java -cp o58p:o58j:kotlin-stdlib.jar Plat58Kt =====
A -> NullPointerException: null
    first frame main$lambda$0:21
    null born at line 21
B -> NullPointerException: null
    first frame main$lambda$1:27
    null born at line 26
C -> NullPointerException: Cannot invoke "String.length()" because the return value of "java.util.List.get(int)" is null
    first frame firstLength:5
    null born at line 31
D -> no exception
    null born at line 37
(exit 0)
```

- ★★★ **`A`(`!!`)와 `B`(non-null 인자로 넘김)는 태어난 줄 근처에서 터졌다** — `A` 는 **같은 줄**(21 = 21), `B` 는 **바로 다음 줄**(26 → 27, `greet(n)` 을 부르는 줄). 둘 다 메시지가 `null` 이다.
- ★★★ **`C`(리스트에 담아 넘김)는 다른 함수에서 터졌다** — 태어난 줄은 31 인데 첫 프레임은 **`firstLength:5`**. 메시지도 Kotlin 것이 아니라 **JVM 의 helpful NPE**(`because the return value of "java.util.List.get(int)" is null`)라 **`Store58.findName` 이라는 말이 어디에도 없다.** 스택만 보면 원인이 `firstLength` 로 보인다.
- ★★★ **`D` 는 안 터졌다** — `val names: List<String> = listOf(n)` 는 **타입을 적었는데도** 검사가 없다. `List<String>` 의 원소 타입은 **안까지 들여다보지 않는다** — `null` 이 「non-null 리스트」 안에 앉은 채 흘러간다. 터지는 것은 누군가 **원소를 꺼내 쓰는 날**이다(`C`).
- ★ [05번 주제](../05-platform-types/) (2)가 `val b: String = J.giveNull()`(대입하는 줄)과 `a.length`(쓰는 줄)를 쟀다 — 여기는 그 사이의 두 경우(**인자로 넘기는 줄 · 컬렉션에 담아 멀리 보내는 경우**)를 더했다.

```text
===== javap -c -p -cp o58p Plat58Kt | grep -E 'private static final int main\$lambda|Store58\.findName|Intrinsics\.checkNotNull:|Method greet|Method firstLength|listOf' =====
  private static final int main$lambda$0(kotlin.jvm.internal.Ref$IntRef);
       9: invokestatic  #194                // Method Store58.findName:(Ljava/lang/String;)Ljava/lang/String;
      13: invokestatic  #197                // Method kotlin/jvm/internal/Intrinsics.checkNotNull:(Ljava/lang/Object;)V
  private static final int main$lambda$1(kotlin.jvm.internal.Ref$IntRef);
       2: invokestatic  #194                // Method Store58.findName:(Ljava/lang/String;)Ljava/lang/String;
      14: invokestatic  #197                // Method kotlin/jvm/internal/Intrinsics.checkNotNull:(Ljava/lang/Object;)V
      18: invokestatic  #201                // Method greet:(Ljava/lang/String;)Ljava/lang/String;
  private static final int main$lambda$2(kotlin.jvm.internal.Ref$IntRef);
       2: invokestatic  #194                // Method Store58.findName:(Ljava/lang/String;)Ljava/lang/String;
      14: invokestatic  #207                // Method kotlin/collections/CollectionsKt.listOf:(Ljava/lang/Object;)Ljava/util/List;
      19: invokestatic  #209                // Method firstLength:(Ljava/util/List;)I
  private static final int main$lambda$3(kotlin.jvm.internal.Ref$IntRef);
       2: invokestatic  #194                // Method Store58.findName:(Ljava/lang/String;)Ljava/lang/String;
      14: invokestatic  #207                // Method kotlin/collections/CollectionsKt.listOf:(Ljava/lang/Object;)Ljava/util/List;
(exit 0)
```

- ★★★ **`B` 의 검사는 `greet` 안이 아니라 부르는 쪽에 박혔다** — `main$lambda$1` 에서 `Store58.findName` 뒤, `Method greet` **앞**에 `Intrinsics.checkNotNull`. 그래서 `greet` 가 가진 `checkNotNullParameter`([03번 주제](../03-null-safe-types/) (4) — 「`Parameter specified as non-null is null`」)까지 **가지도 않고** 메시지 없는 NPE 가 났다.
- ★★ **`C`·`D`(`main$lambda$2`·`$3`)에는 `checkNotNull` 이 없다** — `listOf` 에 플랫폼 값을 넣을 때 컴파일러는 **아무것도 심지 않았다.** 이것이 「늦게 터진다」의 바이트코드 쪽 근거다.
- ★ `A`(`main$lambda$0`)의 `checkNotNull` 은 `!!` 가 **요청한** 것이고, `B` 의 것은 컴파일러가 **알아서 넣은** 것이다 — 명령은 한 글자도 같다.

★ **부르는 쪽 검사를 끄면 `B` 가 어디로 가나** — 같은 소스를 `-Xno-call-assertions` 로 다시 컴파일했다.

```text
===== kotlinc -Xno-call-assertions -cp o58j plat58.kt -d o58q =====
(exit 0)
===== java -cp o58q:o58j:kotlin-stdlib.jar Plat58Kt =====
A -> NullPointerException: null
    first frame main$lambda$0:21
    null born at line 21
B -> NullPointerException: Parameter specified as non-null is null: method Plat58Kt.greet, parameter name
    first frame greet:-1
    null born at line 26
C -> NullPointerException: Cannot invoke "String.length()" because the return value of "java.util.List.get(int)" is null
    first frame firstLength:5
    null born at line 31
D -> no exception
    null born at line 37
(exit 0)
```

- ★★ **`B` 만 바뀌었다** — 검사가 `greet` **안**으로 한 칸 밀려 들어가 「`Parameter specified as non-null is null: method Plat58Kt.greet, parameter name`」이 됐다. **메시지는 좋아졌는데 첫 프레임의 줄 번호가 `-1`** 이다 — 함수 첫머리의 인자 검사에는 줄 번호가 안 붙었다(이 판의 관찰).
- ★ `A`(`!!`)는 그대로다 — `!!` 는 **요청**이라 플래그가 못 끈다([03번 주제](../03-null-safe-types/) (5)와 같은 결론). `C`·`D` 는 애초에 검사가 없었으니 그대로다.

```text
   태어난 줄                          터진 줄                 거리
   ────────────────────────────────  ─────────────────────   ─────────────
   A  findName(…)!!            (21)  main$lambda$0:21         같은 줄
   B  val n = findName(…)      (26)  main$lambda$1:27         다음 줄 (넘기는 줄)
   C  val n = findName(…)      (31)  firstLength:5            ★ 다른 함수
   D  val n = findName(…)      (37)  (안 터짐)                ★ 무한 — 꺼낼 때까지
```

### (3) ★★ `?.let` 은 조용히 건너뛴다 — 그리고 `?: 대안` 과 붙으면

```kotlin
// let58.kt
class User(val id: String, val email: String?)

val users = listOf(
    User("u1", "a@x"), User("u2", null), User("u3", "c@x"), User("u4", null), User("u5", "e@x"),
)
val sent = mutableListOf<String>()
fun send(to: String) { sent += to }

// 1) ?.let 로 보낸다
fun notifyA(u: User) {
    u.email?.let { send(it) }
}

// 2) ?: 로 멈춘다
fun notifyB(u: User) {
    val to = u.email ?: run { System.err.println("skip ${u.id}"); return }
    send(to)
}

// 3) ?.let { } ?: 대안
fun lookup(email: String): String? = if (email.startsWith("a")) null else "ok"
fun statusOf(u: User): String = u.email?.let { lookup(it) } ?: "no email"

fun main() {
    users.forEach(::notifyA)
    println("A sent ${sent.size} of ${users.size}: $sent")
    sent.clear()
    users.forEach(::notifyB)
    println("B sent ${sent.size} of ${users.size}: $sent")
    for (u in users) println("status ${u.id} = ${statusOf(u)}")
}
```

```text
===== kotlinc let58.kt -d o58l =====
(exit 0)
===== java -cp o58l:kotlin-stdlib.jar Let58Kt 2>/dev/null =====
A sent 3 of 5: [a@x, c@x, e@x]
B sent 3 of 5: [a@x, c@x, e@x]
status u1 = no email
status u2 = no email
status u3 = ok
status u4 = no email
status u5 = ok
(exit 0)
===== java -cp o58l:kotlin-stdlib.jar Let58Kt >/dev/null =====
skip u2
skip u4
(exit 0)
```

- ★★★ **`A`(`?.let`)와 `B`(`?: run { …; return }`)는 보낸 결과가 똑같다(`3 of 5`)** — 차이는 **표준 오류**에 있다. `B` 만 `skip u2`·`skip u4` 를 남겼고, `A` 는 건너뛴 두 사람에 대해 **아무 줄도 안 남겼다.** 「안 보냈다」가 버그인지 정상인지 **나중에 가릴 방법이 없다** — 무음 실패의 모양이 이것이다.
- ★★★ **`status u1 = no email`** — `u1` 은 이메일이 **있는데** 대안이 나왔다. `?.let { lookup(it) }` 의 **블록이 `null` 을 돌려주면**(`lookup` 이 `a` 로 시작하면 `null`) `?:` 는 그것을 「수신자가 `null`」과 **구별하지 못한다.** `?.let { } ?: X` 는 「`if (x != null) … else X`」가 **아니다** — 블록의 결과가 `null` 이어도 `X` 로 간다.
- ★ `let` 이 **블록의 마지막 값**을 돌려준다는 것은 [14번 주제](../14-scope-functions/)가 정본이다 — 여기서 새로 본 것은 그 성질이 `?:` 와 만났을 때의 모양이다.

### (4) ★ 스마트 캐스트가 안 되는 자리 — 그래서 지역 `val` 로 받는다

```kotlin
// smart58.kt
class Form(var name: String?, val code: String?)

fun a(f: Form): Int {
    if (f.name != null) return f.name.length
    return 0
}

fun b(f: Form): Int {
    if (f.code != null) return f.code.length
    return 0
}

fun c(f: Form): Int = f.name?.let { it.length } ?: 0

fun d(f: Form): Int {
    val n = f.name ?: return 0
    return n.length
}

fun main() {
    val f = Form("kim", "k1")
    println(listOf(a(f), b(f), c(f), d(f)))
}
```

```text
===== kotlinc smart58.kt -d o58s =====
smart58.kt:4:32: error: smart cast to 'String' is impossible, because 'name' is a mutable property that could be mutated concurrently.
    if (f.name != null) return f.name.length
                               ^^^^^^
(exit 1)
```

- ★★ **막힌 것은 `a` 하나** — `var name` 은 검사와 사용 사이에 **다른 스레드가 바꿀 수 있어서** 「`is a mutable property that could be mutated concurrently`」. `val code` 인 `b` 는 통과했다(kotlinc 는 한 번에 **모든** 에러를 내므로 진단이 하나뿐이면 `b`·`c`·`d` 는 통과한 것이다).
- ★★ **`c`(`?.let { it }`)와 `d`(`?: return` 으로 지역 `val`)는 같은 문제를 푼다** — 둘 다 프로퍼티를 **한 번만 읽어** 안정된 값에 담는다. `d` 쪽이 뒤 코드를 **들여쓰기 없이** 이어 쓴다.
- ★ 「다른 모듈의 공개 프로퍼티」·「커스텀 getter」·「위임 프로퍼티」까지 **아홉 자리 전수**는 [04번 주제](../04-smart-casts/) (2)가 쟀다 — 이 문서는 다시 재지 않는다.

### (5) ★★ 설계 권고층 — 계층마다 무엇을 둘 것인가

★★★ **이 절은 판단이다.** (1)이 보인 것은 「수단이 결과를 정하고 계층은 결과를 안 바꾼다」까지다 — 그러니 **어느 계층에 어느 수단**은 관찰에서 나오지 않는다. 공식 규약 문서([Coding conventions](https://kotlinlang.org/docs/coding-conventions.html))는 **열지 못했으므로 출처 확인 못 함**이다. 아래 표의 근거 칸은 전부 **이 문서의 관찰에서 끌어낸 이유**다.

| 계층 | 권고(판단) | 관찰 쪽 근거 |
|---|---|---|
| **외부 입력 파싱** | ★ `?: return null`(또는 실패를 값으로 — [49번 주제](../49-result-and-runcatching/)) — 예외로 만들지 않는다 | 입력이 틀린 것은 **예상된 일**이다 · (1)에서 `?: return` 은 예외 없이 `null` 을 돌려준다 |
| **공개 API 인자** | ★ 먼저 **타입을 non-null 로** — 받아야 한다면 `requireNotNull(x) { "…" }` | `IllegalArgumentException` = 「부른 쪽 잘못」(KDoc — [51번 주제](../51-preconditions-require-check-error-todo/)) · 메시지가 남는다((1)) |
| **내부 불변식** | `checkNotNull(x) { "…" }` · `?: error("…")` | `IllegalStateException` = 「내 상태가 틀렸다」 · 첫 프레임이 그 줄((1)) |
| **표시 계층** | `?.let { }` · `?: ""` — 없어도 되는 것 | 건너뛰는 것이 **정상**인 자리 — 단 **정상이 아닐 수도 있으면 로그를 남긴다**((3)) |
| **Java 경계** | 받는 **그 줄에서** 타입을 적거나 검사한다(`?: return`·`requireNotNull`) | 안 적으면 **다른 함수에서** JVM 문구로 터지거나(`C`) 아예 안 터진다(`D`)((2)) |
| **어디에도** | `!!` 는 테스트·프로토타입 밖에서 쓰지 않는다 | 메시지가 `null` — 네 칸 전부((1)) |

★ 권고를 코드로 옮긴 한 벌 —

```kotlin
// form58.kt
// 한 요청이 네 계층을 지난다 — 계층마다 다른 수단
class Order(val item: String, val qty: Int, val note: String?)

val stock = mapOf("apple" to 3, "pear" to 5)

// 외부 입력: 실패를 값으로 돌려준다
fun parse(line: String): Order? {
    val parts = line.split(",")
    val item = parts.getOrNull(0)?.takeIf { it.isNotBlank() } ?: return null
    val qty = parts.getOrNull(1)?.toIntOrNull() ?: return null
    return Order(item, qty, parts.getOrNull(2))
}

// 공개 API: 인자 계약
fun place(item: String?, qty: Int): Int {
    val name = requireNotNull(item) { "item is required" }
    require(qty > 0) { "qty must be positive: $qty" }
    return reserve(name, qty)
}

// 내부: 있어야 할 것
private fun reserve(item: String, qty: Int): Int {
    val left = checkNotNull(stock[item]) { "unknown item passed validation: $item" }
    return left - qty
}

// 표시: 없어도 되는 것
fun render(o: Order, left: Int): String =
    "${o.item} x${o.qty}" + (o.note?.let { " ($it)" } ?: "") + " left=$left"

fun handle(line: String) {
    val o = parse(line) ?: run { println("rejected: '$line'"); return }
    try {
        println(render(o, place(o.item, o.qty)))
    } catch (e: IllegalArgumentException) {
        println("caller error: ${e.message}")
    } catch (e: IllegalStateException) {
        println("bug: ${e.message}")
    }
}

fun main() {
    listOf("apple,2", "pear,1,gift", "apple,x", ",3", "kiwi,1", "pear,0").forEach(::handle)
}
```

```text
===== kotlinc form58.kt -d o58f =====
(exit 0)
===== java -cp o58f:kotlin-stdlib.jar Form58Kt =====
apple x2 left=1
pear x1 (gift) left=4
rejected: 'apple,x'
rejected: ',3'
bug: unknown item passed validation: kiwi
caller error: qty must be positive: 0
(exit 0)
```

- ★★ **실패가 층마다 다른 이름으로 나온다** — 입력이 틀리면 `rejected:` · 인자 계약을 어기면 `caller error:`(`IllegalArgumentException`) · 검증을 통과했는데 내부에 없으면 `bug:`(`IllegalStateException`). **예외 클래스가 곧 「누구 잘못인가」의 분류**가 되도록 수단을 골랐다 — 이 분류가 옳다는 것은 **판단**이고, 클래스가 그렇게 나온다는 것은 **관찰**이다.
- ★ `"pear,0"` 은 `null` 이 아니지만 같은 `require` 로 막았다 — 인자 계약은 `null` 만의 일이 아니다([51번 주제](../51-preconditions-require-check-error-todo/)).

## 문법 — 형태와 규칙

**형태** — (5)의 `form58.kt` 한 벌이 여섯 수단을 **제자리에** 쓴 모양이다.

**금지·주의 사례** — 컴파일은 되지만 뜻이 어긋나는 것(표로 적는다 — 전부 (1)\~(4)에서 돌렸다).

| 쓴 꼴 | 무엇이 일어나나 | 어디서 |
|---|---|---|
| `x?.let { f(it) } ?: y` | `f` 가 `null` 을 돌려줘도 `y` | (3) |
| `x?.let { send(it) }` (로그 없음) | 건너뛴 것이 흔적 없이 사라진다 | (3) |
| `requireNotNull(map[key])` (내부 조회) | 「부른 쪽 잘못」 클래스가 내부 사고에 붙는다 | (1) |
| `val xs: List<String> = listOf(javaValue)` | 원소는 검사하지 않는다 — `null` 이 담긴다 | (2) `D` |
| `if (obj.varProp != null) obj.varProp.length` | 컴파일 에러 — 지역 `val` 로 받는다 | (4) |

**규칙 불릿**

- **수단이 예외 클래스를 정한다 — 계층이 아니다**((1) `0 / 6`).
- **`?: return` 과 `?.let` 은 부른 쪽에서 구별되지 않는다** — 멈춘다는 사실을 **코드에 드러내려면 `return`** 쪽((1)(3)).
- **`!!`·`requireNotNull`·`checkNotNull`·`error` 는 전부 그 줄에서 터진다** — 메시지가 있는 것은 `!!` 를 뺀 셋((1)).
- **Java 값은 받는 줄에서 타입을 정한다** — non-null 인자로 넘기면 **넘기는 줄**에서, 컬렉션에 담으면 **꺼내는 날** 다른 함수에서((2)).
- **`?.let { } ?: X` 의 `X` 는 「블록이 `null` 일 때」도 돈다**((3)).

## 어디서 틀리나

1. ★★★ **NPE 스택의 맨 위 줄을 원인으로 읽는다.** Java 가 준 `null` 을 컬렉션에 담아 보냈으면 맨 위는 **꺼내 쓴 함수**다(`firstLength:5` — 태어난 곳은 31)((2)).
2. ★★★ **`?.let { … } ?: 대안` 을 `if-else` 로 읽는다.** 블록이 `null` 이면 대안이 돈다 — `u1` 이 이메일이 있는데 `no email`((3)).
3. ★★ **`?.let` 으로 건너뛰고 끝낸다.** 결과는 같아 보이지만(`3 of 5`) 건너뛴 사실이 **어디에도 없다**((3)).
4. ★★ **`requireNotNull` 을 아무 데나 쓴다.** 내부 조회에 두어도 `IllegalArgumentException` — 로그를 보는 사람이 **호출자를 의심**한다((1)).
5. ★★ **`List<String>` 이라고 적었으니 원소가 안전하다고 본다.** 플랫폼 값은 **원소 자리에서 검사되지 않는다**((2) `D`).
6. ★ **`!!` 로 「여기서 터지니 원인을 안다」고 본다.** 줄은 알지만 메시지가 `null` 이라 **무엇이 없었는지** 모른다((1)).
7. ★ **`var` 프로퍼티에 `!= null` 검사 뒤 바로 쓴다.** 스마트 캐스트가 거부된다 — 지역 `val` 로 받는다((4)).

## 구현 세부사항 대 언어 보장

| 항목 | 어느 쪽인가 | 근거 |
|---|---|---|
| `?.` 가 `null` 이면 오른쪽을 안 돌리고 `null` · `!!` 가 `null` 이면 NPE | ★★★ **언어 보장** | (1) · [03번 주제](../03-null-safe-types/) |
| `requireNotNull` → `IllegalArgumentException` · `checkNotNull`·`error` → `IllegalStateException` | ★★ **API 계약(KDoc)** | (1) · [51번 주제](../51-preconditions-require-check-error-todo/) |
| 스마트 캐스트가 `var` 프로퍼티에서 거부된다 | ★★ **언어 규칙(컴파일러 진단)** | (4) |
| 플랫폼 값을 non-null 인자로 넘기면 **부르는 줄**에 `Intrinsics.checkNotNull` | ★ **Kotlin/JVM 컴파일러의 구현** — `-Xno-call-assertions` 로 꺼진다(그러면 `greet` 안의 인자 검사가 대신 걸린다) | (2) `javap` · 플래그 대조 |
| `listOf(플랫폼 값)` 에 검사가 없다 | ★ **이 판의 관찰** — 플랫폼 타입은 「검사가 유예된 구간」이라는 설계와 맞다([`../../언어-특성/README.md`](../../언어-특성/README.md) §2) | (2) `D` |
| helpful NPE 문구(`because the return value of …`) | ★ **JVM(14+)의 구현** — Kotlin 이 만든 문구가 아니다 | (2) `C` · [05번 주제](../05-platform-types/) (2) |
| 첫 프레임이 수단이 적힌 줄 | ★ **관찰** — `inline` 함수는 호출한 줄 번호로 남았다 | (1) |
| 「계층마다 이 수단을」 | ★★★ **설계 권고 — 이 문서의 판단** · 공식 출처 확인 못 함 | (5) |

★★ **가장 조심할 자리** — (5)의 표를 「Kotlin 이 정한 규칙」으로 읽는 것. **언어가 정한 것은 수단의 의미까지**이고((1)), 수단을 계층에 짝짓는 것은 팀의 규약이다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 없는 것이 **예상된 일**이고 여기서 멈추면 된다 | `?: return` | (1) — 예외 없이 멈추고, 멈춘다는 것이 코드에 보인다 |
| 없는 것이 **정상**이고 그 칸만 비우면 된다 | `?.let { }` · `?: 기본값` | (3) — 단 **블록이 `null` 을 낼 수 있으면 `?:` 와 붙이지 않는다** |
| 없으면 **부른 쪽 잘못** | `requireNotNull(x) { "…" }` | (1) — `IllegalArgumentException` + 메시지 |
| 없으면 **내 쪽 버그** | `checkNotNull(x) { "…" }` · `?: error("…")` | (1) — `IllegalStateException` + 메시지 |
| Java 가 준 값 | **받는 줄**에서 타입을 적거나 위 넷 중 하나 | (2) — 안 그러면 다른 함수에서 터진다 |
| 건너뛴 것을 나중에 세야 한다 | `?: run { log(…); return }` | (3) — `?.let` 은 흔적이 없다 |
| `!!` | 테스트·일회성 코드 | (1) — 메시지 없음 |

## 핵심 문장

1. **수단이 결과를 정하고 계층은 결과를 안 바꾼다**(`0 / 6`) — 계층에 수단을 짝짓는 것은 판단이다.
2. `?: return`·`?.let` 은 예외 없이 `null` 을 돌려주고(`8 / 24`), 나머지 넷은 **그 줄에서** 던진다 — 메시지가 없는 것은 `!!` 뿐이다.
3. Java 가 준 `null` 은 `!!`·non-null 인자면 **그 근처에서**, 컬렉션에 담아 보내면 **다른 함수에서 JVM 문구로** 터지고, 꺼내지 않으면 **안 터진다.**
4. `?.let` 은 건너뛴 것을 **아무 데도 안 남기고**, `?.let { } ?: X` 는 **블록이 `null` 이어도** `X` 로 간다.
5. 예외 클래스를 「누구 잘못인가」로 쓰려면 **인자는 `require`, 상태는 `check`** — 그 분류가 로그에서 곧 원인 분류가 된다.

## 관련 자료

- [03번 주제](../03-null-safe-types/) — ★★★ **선행.** `?`·`?.`·`?:`·`!!` 의 문법과 바이트코드. 그쪽은 **각 연산자가 무엇인가**, 여기는 **어느 계층에 무엇을 두나**.
- [51번 주제](../51-preconditions-require-check-error-todo/) — ★★★ **선행.** `require`/`check`/`error`/`TODO` 의 예외 격자·기본 메시지·계약. 그쪽은 **무엇을 던지나**, 여기는 **어디에 두나**.
- [04번 주제](../04-smart-casts/) — 스마트 캐스트가 깨지는 자리 전수. [05번 주제](../05-platform-types/) — 플랫폼 타입의 A/B/C. [14번 주제](../14-scope-functions/) — `let` 의 반환값. [34번 주제](../34-exceptions-nothing-and-try-expression/) — `Nothing`. [49번 주제](../49-result-and-runcatching/) — 실패를 값으로.
- [57번 주제](../57-kotlin-idioms-for-java-code-if-when-expressions-and-elvis-return/) — Java 코드를 Kotlin 답게(`?: return` 조기 반환의 Java 원본 대비).
- [`../../언어-특성/README.md`](../../언어-특성/README.md) §2 — 「플랫폼 타입은 경계에서 즉시 검증」이라는 설계 논지. 그쪽은 **왜**, 여기는 **코드의 모양과 터지는 줄**.
- [Java 60번](../../../java/syntax/60-null-handling/) · [Java 38번](../../../java/syntax/38-optional/) — Java 는 `Objects.requireNonNull`·`Optional` 로 푼다. [C# 07번](../../../csharp/syntax/07-null-operators/) — `?.`·`??`·`!` 의 C# 판.

## 용어 풀이

> **계층(layer)** — 요청이 지나는 코드의 층. 이 문서는 넷으로 나눈다 — 외부 입력 파싱 · 공개 API · 내부 · 표시.\
> 예: `"12x"` 를 숫자로 바꾸는 곳이 외부 입력 파싱, `place(item, qty)` 가 공개 API.

> **첫 프레임(top frame)** — 예외 스택 트레이스의 맨 위 줄. **예외가 만들어진 자리**다(원인이 태어난 자리가 아닐 수 있다).

> **무음 실패(silent failure)** — 실패했는데 예외도 로그도 없이 지나가는 것. `?.let` 이 건너뛴 원소가 그렇다.

> **플랫폼 타입(`T!`)** — Java 선언에서 온 값의 타입. null 여부를 모르는 채로 검사가 **유예된다**([05번 주제](../05-platform-types/)).

> **helpful NPE** — JDK 14+ 가 NPE 메시지에 「무엇이 `null` 이었나」를 적어 주는 기능(`Cannot invoke … because …`).

> **설계 권고층** — 이 문서에서 「관찰」과 갈라 적은 판단. 실행으로 증명되지 않는다.

## 더 들어가면

- **`Result`·봉인 클래스로 실패를 값으로** — 외부 입력 계층에서 `null` 대신 이유를 돌려주기. [49번 주제](../49-result-and-runcatching/)가 정본이다.
- **JSpecify 가 붙은 Java 라이브러리** — 2.1.0 부터 위반이 오류라 (2)의 구멍이 그 표면에서 거의 닫힌다([`../../언어-특성/README.md`](../../언어-특성/README.md) §2 · [05번 주제](../05-platform-types/) (5)). 이 문서는 **애너테이션 없는** Java 만 돌렸다.
- **`-Xno-param-assertions` 까지 함께 끄면** — (2) `B` 가 `greet` 안에서도 안 걸리고 `name.length` 를 쓰는 자리까지 흘러갈 것으로 보이지만 **이 문서는 돌리지 않았다**(두 플래그를 함께 끈 바이트코드는 [03번 주제](../03-null-safe-types/) (5)가 찍었다).
