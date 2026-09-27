# kotlin/syntax/23 — `sealed class`/`sealed interface` 와 `when` 완결성 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Sealed classes and interfaces](https://kotlinlang.org/docs/sealed-classes.html) · [Conditions and loops — `when`](https://kotlinlang.org/docs/control-flow.html) · [언어 기능·제안 상태표](https://kotlinlang.org/docs/kotlin-language-features-and-proposals.html).
> **실행 검증** — 이 문서의 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 에서 실제로 얻었다.\
> `kotlinc` 12회(컴파일 실패 5벌 · 그중 1벌은 `-jvm-target 17`) · `java` 5회 · `javac` 2회(둘 다 실패가 결과) · `javap` 4회.\
> ★★ 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적지 않았다.
> ⚠️ **`-jvm-target` 을 밝히지 않은 바이트코드 주장은 반쪽이다.** 이 주제는 **기본값 1.8 과 `-jvm-target 17` 이 서로 다른 클래스 파일을 낸다** — (6)이 그것이다.
> **버전** — `sealed class` 는 **1.0**, **`sealed interface` 는 1.5**, **데이터 흐름 기반 완결성 검사는 2.3.0 Stable**(2.2.20 도입)이다. 뒤의 둘은 이 판에서 직접 던져 확인했다((2)·(5)).
> **경계** — `when` 의 가지 형태·guard·바이트코드 분기는 [6번 주제](../06-when-expression/)가 정본이다. **거기는 「`when` 이 무엇으로 컴파일되나」까지, 여기는 「하위 타입을 늘렸을 때 어디가 깨지나」부터**다.\
> 인터페이스의 기본 구현·충돌 해소는 [20번 주제](../20-interfaces-default-impl-and-super/), `data class` 가 변형이 되는 것은 [22번 주제](../22-data-class-generated-members/)가 정본이다.\
> Java 쪽 짝은 [`../../../java/syntax/15-sealed-classes/`](../../../java/syntax/15-sealed-classes/)와 [`../../../java/syntax/23-switch-pattern-matching/`](../../../java/syntax/23-switch-pattern-matching/) — **Kotlin 이 먼저 한 것을 Java 가 어떻게 따라왔나**가 대비 축이다.\
> Rust 쪽 짝은 [`../../../rust/syntax/18-match-and-exhaustiveness/`](../../../rust/syntax/18-match-and-exhaustiveness/) — **같은 실험을 같은 격자로** 했다((3)).
> 이 본문은 Claude 작성이다(원고 없음).

★ **흔들리는 칸 / 안 흔들리는 칸** — 제출 전 재대조에서 「고칠 것」과 「설계상 다른 것」을 가르는 선언이다.

| 흔들린다 | 안 흔들린다 |
|---|---|
| (이 주제에는 없다 — 해시코드·시간·주소를 **하나도 찍지 않았다**) | 컴파일 에러의 **문구·`파일:줄:칸`·캐럿 줄·에러 개수** |
| | `javap` 출력 **전체**(`major version`·플래그·`PermittedSubclasses`) |
| | `javac` 에러의 **문구와 개수** |
| | 모든 **종료 코드** · `println` 출력 |

> ★ 이 주제의 근거는 **거의 전부 컴파일 에러**다. 그래서 「몇 곳이 깨졌나」를 **세는 것**이 그대로 수치가 된다((3)).
>
> 근거 — 캡처 스크립트를 두 번 돌려 블록 전체를 바이트 단위로 대조했다(수치는 3-answer 의 「실행 검증」).

## 한눈에 — 쉽게 말하면

**`sealed` 는 「이 타입의 하위 타입은 이것들이 전부다」를 컴파일러에게 알리는 선언이다.**

그 결과 `when` 이 **점호**가 된다 — 명단을 다 부르지 않으면 컴파일이 안 된다. 그리고 **명단이 늘어나면 점호하는 자리가 전부 깨진다.** 그것이 이 문법을 쓰는 유일한 이유다.

비유는 문서 끝까지 이것 하나로 고정한다 — **출입자 명단이 붙은 방**이다.

| 비유 | 실체 |
|---|---|
| 문에 붙은 **출입자 명단** | `sealed` 타입의 직접 하위 타입 집합 |
| 명단은 **같은 건물(패키지) 안에서만** 적을 수 있다 | 하위 타입은 **같은 패키지·같은 모듈**에 있어야 한다 |
| 방에 들어온 사람 **점호** | `when (x) { ... }` |
| 「한 명이 빠졌습니다」 | `'when' expression must be exhaustive.` |
| 명단에 한 사람 추가 | 하위 타입 한 줄 추가 |
| 그 순간 **모든 점호표를 다시 써야 한다** | 하위 타입을 늘리면 `when` 이 전부 깨진다 |
| 「나머지는 다 그 밖으로 치세요」 | `else` — **점호를 그만두는 선언** |
| 점호 대신 **눈대중으로 세기** | `if` 사슬 · 주체 없는 `when` — **검사 자체가 없다** |

```text
   sealed interface Ev            <- 명단이 닫혀 있다
     +-- Click                       (같은 패키지·같은 모듈에만 적을 수 있다)
     +-- Key
     +-- Scroll

   when (e) {                     <- 점호
       is Click -> ...
       is Key   -> ...
       Scroll   -> ...            <- 셋을 다 불렀으니 통과
   }

   ... 명단에 Drag 를 한 줄 더하면 ...

   when (e) {                     error: 'when' expression must be exhaustive.
       is Click -> ...                   Add the 'is Drag' branch or an 'else' branch.
       is Key   -> ...
       Scroll   -> ...            <- 점호표를 안 고쳤으니 깨진다
   }
```

**`sealed` 의 값어치는 「닫는 것」이 아니라 「셀 수 있게 되는 것」이다.** 그리고 그 셈을 **끄는 스위치가 `else`** 다.

## 이 주제가 답하려는 질문

1. **완결성은 언제 요구되나** — 식일 때만인가, 문일 때도인가. 무엇이 그것을 정하나.
2. **하위 타입을 늘리면 어디가 깨지고 어디가 안 깨지나** — 세어 볼 수 있나.
3. `sealed` 는 **JVM 에서 무엇이 되나** — 그 규칙이 Java 쪽에도 있나.

## 동작 방식

### (1) `sealed class` 와 `sealed interface` — 고르는 기준은 「상태를 줄 것인가」다

**언제 쓰나** — 닫힌 계층을 처음 세울 때.

```text
===== 소스: sealkinds.kt =====
sealed class Expr {
    data class Num(val v: Int) : Expr()
    data class Add(val l: Expr, val r: Expr) : Expr()
    data object Zero : Expr()
}

sealed interface Json
data class JStr(val s: String) : Json
data class JNum(val n: Int) : Json
data object JNull : Json
class JList(val xs: List<Json>) : Json, Comparable<JList> {
    override fun compareTo(other: JList) = xs.size - other.xs.size
}

fun eval(e: Expr): Int = when (e) {
    is Expr.Num -> e.v
    is Expr.Add -> eval(e.l) + eval(e.r)
    Expr.Zero -> 0
}

fun render(j: Json): String = when (j) {
    is JStr -> "\"${j.s}\""
    is JNum -> j.n.toString()
    JNull -> "null"
    is JList -> j.xs.joinToString(",", "[", "]") { render(it) }
}

fun main() {
    println("A ${eval(Expr.Add(Expr.Num(2), Expr.Add(Expr.Num(3), Expr.Zero)))}")
    println("B ${render(JList(listOf(JStr("a"), JNum(1), JNull)))}")
    println("C ${Expr.Zero === Expr.Zero}")
}
===== kotlinc sealkinds.kt -d o23k =====
(exit 0)
===== java -cp o23k:kotlin-stdlib.jar SealkindsKt =====
A 5
B ["a",1,null]
C true
(exit 0)
```

```text
   sealed class Expr                       sealed interface Json
     - 생성자가 있다(상태를 줄 수 있다)       - 생성자가 없다
     - 하위는 하나만 고를 수 있다             - 하위가 여럿을 섞을 수 있다
     - 중첩해서 Expr.Num 처럼 쓸 수 있다       (JList 는 Json 이면서 Comparable 이다)
     - 1.0 부터                               - 1.5 부터
```

- `A 5` · `B ["a",1,null]` — 두 형태 모두 `when` 이 **`else` 없이** 완결로 인정된다.
- `C true` — `data object Zero` 는 싱글턴이므로 `===` 가 참이다([22번 주제](../22-data-class-generated-members/)).
- ★ **`sealed interface` 가 1.5 에 들어온 이유**가 `JList` 에 보인다 — `Json` 이면서 동시에 `Comparable<JList>` 다. `sealed class` 였다면 **상속 자리 하나를 이미 써 버려** 이 조합이 안 된다.
- ★ 중첩 선언(`Expr.Num`)과 최상위 선언(`JStr`)은 **완결성 판정에 차이가 없다.** 다른 것은 이름 짓는 방식뿐이다.
- ★ 가지에서 `is Expr.Num` 처럼 **`is` 를 쓰는 것**과 `Expr.Zero` 처럼 **값을 그대로 적는 것**이 섞여 있다 — 앞엣것은 **타입**, 뒤엣것은 **싱글턴 객체**라서 그렇다.

### (2) ★★★ 완결성을 정하는 것은 「식이냐 문이냐」가 **아니다** — 주체 타입이다

**언제 쓰나** — 「`when` 을 문으로 쓰면 안전망이 없겠지」라고 믿을 때. **전제가 뒤집히는 자리다.**

```text
===== 소스: sealstmt.kt =====
sealed interface Ev
data class Click(val x: Int) : Ev
data object Key : Ev

fun stmtOverSealed(e: Ev) {
    when (e) {
        is Click -> println("click")
    }
}

fun stmtOverInt(n: Int) {
    when (n) {
        1 -> println("one")
    }
}

fun stmtOverBoolean(b: Boolean) {
    when (b) {
        true -> println("t")
    }
}

fun exprOverInt(n: Int): String = when (n) {
    1 -> "one"
}
===== kotlinc sealstmt.kt -d o23s =====
sealstmt.kt:6:5: error: 'when' expression must be exhaustive. Add the 'Key' branch or an 'else' branch.
    when (e) {
    ^^^^
sealstmt.kt:18:5: error: 'when' expression must be exhaustive. Add the 'false' branch or an 'else' branch.
    when (b) {
    ^^^^
sealstmt.kt:23:35: error: 'when' expression must be exhaustive. Add an 'else' branch.
fun exprOverInt(n: Int): String = when (n) {
                                  ^^^^
(exit 1)
```

```text
   주체 타입      식(expression)              문(statement)
   ------------   -------------------------   -------------------------
   sealed         완결 요구 (에러)             ★ 완결 요구 (에러)
   enum           완결 요구                    ★ 완결 요구
   Boolean        완결 요구                    ★ 완결 요구 (에러)
   Int·String 등  완결 요구 → else 필요        요구 없음 (통과)
```

- 던져 보니 에러가 **세 줄**이다 — `sealed` **문**, `Boolean` **문**, `Int` **식**.
- ★★★ **`Int` 를 주체로 한 `when` 문만 통과했다.** 즉 「문이니까 안 본다」가 아니라 「**주체 타입이 셀 수 있는 것이면 문에서도 센다**」가 규칙이다.
- ★★ 에러 문구가 `'when' expression must be exhaustive.` 로 **문인데도 `expression` 이라고 말한다.** 문구를 그대로 읽으면 「식일 때만 그런가 보다」로 오해하기 쉽다 — **문구가 아니라 어느 줄에서 났는지를 보라.**
- ★ 식일 때는 **주체 타입과 무관하게** 완결이 요구된다(`Int` 식도 `else` 가 필요하다). 값을 내야 하는데 안 맞는 가지가 오면 돌려줄 것이 없기 때문이다.
- ★ 이 규칙의 정본은 [6번 주제](../06-when-expression/)다. 여기서는 **결론과 실측만** 쓴다.

> **완결성(exhaustiveness)** — 「가지들이 가능한 값을 빠짐없이 덮었나」를 컴파일러가 검사하는 것.\
> 예: `sealed` 하위 타입 셋 중 둘만 적으면 「`Add the 'Key' branch or an 'else' branch.`」가 난다.

### (3) ★★★ 변형을 하나 늘렸을 때 깨지는 자리 **전수** — 세어 보면 수치가 된다

**언제 쓰나** — 「`else` 를 쓰면 왜 안 되나」에 말이 아니라 **숫자**로 답할 때.

**① `else` 가 하나도 없는 판 — 변형 셋.** 통과한다.

```text
===== 소스: addnoelse3.kt =====
sealed interface Ev
data class Click(val x: Int) : Ev
data class Key(val c: Char) : Ev
data object Scroll : Ev

fun label(e: Ev): String = when (e) {
    is Click -> "클릭"
    is Key -> "키"
    Scroll -> "스크롤"
}

fun code(e: Ev): Int = when (e) {
    is Click -> 1
    is Key -> 2
    Scroll -> 3
}

fun isKey(e: Ev): Boolean = when (e) {
    is Key -> true
    is Click -> false
    Scroll -> false
}

fun log(e: Ev) {
    when (e) {
        is Click -> println("  click ${e.x}")
        is Key -> println("  key ${e.c}")
        Scroll -> println("  scroll")
    }
}

fun chain(e: Ev): String =
    if (e is Click) "클릭"
    else if (e is Key) "키"
    else "그 밖"

fun noSubject(e: Ev): String = when {
    e is Click -> "클릭"
    e is Key -> "키"
    else -> "그 밖"
}

fun main() {
    val all: List<Ev> = listOf(Click(1), Key('a'), Scroll)
    for (e in all) println("${label(e)} ${code(e)} ${isKey(e)} ${chain(e)} ${noSubject(e)}")
    for (e in all) log(e)
}
===== kotlinc addnoelse3.kt -d o23a3 =====
(exit 0)
===== java -cp o23a3:kotlin-stdlib.jar Addnoelse3Kt =====
클릭 1 false 클릭 클릭
키 2 true 키 키
스크롤 3 false 그 밖 그 밖
  click 1
  key a
  scroll
(exit 0)
```

**② 같은 파일에 변형 `Drag` 한 줄만 더했다.** `when` 은 한 글자도 안 고쳤다.

```text
===== diff addnoelse3.kt addnoelse4.kt =====
4a5
> data class Drag(val dx: Int, val dy: Int) : Ev
44c45
<     val all: List<Ev> = listOf(Click(1), Key('a'), Scroll)
---
>     val all: List<Ev> = listOf(Click(1), Key('a'), Scroll, Drag(3, 4))
(exit 1)
```

```text
===== 소스: addnoelse4.kt =====
sealed interface Ev
data class Click(val x: Int) : Ev
data class Key(val c: Char) : Ev
data object Scroll : Ev
data class Drag(val dx: Int, val dy: Int) : Ev

fun label(e: Ev): String = when (e) {
    is Click -> "클릭"
    is Key -> "키"
    Scroll -> "스크롤"
}

fun code(e: Ev): Int = when (e) {
    is Click -> 1
    is Key -> 2
    Scroll -> 3
}

fun isKey(e: Ev): Boolean = when (e) {
    is Key -> true
    is Click -> false
    Scroll -> false
}

fun log(e: Ev) {
    when (e) {
        is Click -> println("  click ${e.x}")
        is Key -> println("  key ${e.c}")
        Scroll -> println("  scroll")
    }
}

fun chain(e: Ev): String =
    if (e is Click) "클릭"
    else if (e is Key) "키"
    else "그 밖"

fun noSubject(e: Ev): String = when {
    e is Click -> "클릭"
    e is Key -> "키"
    else -> "그 밖"
}

fun main() {
    val all: List<Ev> = listOf(Click(1), Key('a'), Scroll, Drag(3, 4))
    for (e in all) println("${label(e)} ${code(e)} ${isKey(e)} ${chain(e)} ${noSubject(e)}")
    for (e in all) log(e)
}
===== kotlinc addnoelse4.kt -d o23a4 =====
addnoelse4.kt:7:28: error: 'when' expression must be exhaustive. Add the 'is Drag' branch or an 'else' branch.
fun label(e: Ev): String = when (e) {
                           ^^^^
addnoelse4.kt:13:24: error: 'when' expression must be exhaustive. Add the 'is Drag' branch or an 'else' branch.
fun code(e: Ev): Int = when (e) {
                       ^^^^
addnoelse4.kt:19:29: error: 'when' expression must be exhaustive. Add the 'is Drag' branch or an 'else' branch.
fun isKey(e: Ev): Boolean = when (e) {
                            ^^^^
addnoelse4.kt:26:5: error: 'when' expression must be exhaustive. Add the 'is Drag' branch or an 'else' branch.
    when (e) {
    ^^^^
(exit 1)
```

- ★★ **에러가 정확히 4곳**이다 — `label`·`code`·`isKey`·`log`. **`log` 는 `when` 문**인데도 깨졌다((2)).
- ★ **안 깨진 자리도 그 파일 안에 있다** — `chain`(`if` 사슬)과 `noSubject`(주체 없는 `when`)는 **아무 말도 없다.** 컴파일러는 이 둘을 **셀 수 있는 것으로 보지 않는다.**

**③ 같은 코드에서 네 자리의 마지막 가지만 `else` 로 바꾼 판 — 변형 셋.** 역시 통과한다.

```text
===== 소스: addelse3.kt =====
sealed interface Ev
data class Click(val x: Int) : Ev
data class Key(val c: Char) : Ev
data object Scroll : Ev

fun label(e: Ev): String = when (e) {
    is Click -> "클릭"
    is Key -> "키"
    else -> "스크롤"
}

fun code(e: Ev): Int = when (e) {
    is Click -> 1
    is Key -> 2
    else -> 3
}

fun isKey(e: Ev): Boolean = when (e) {
    is Key -> true
    is Click -> false
    else -> false
}

fun log(e: Ev) {
    when (e) {
        is Click -> println("  click ${e.x}")
        is Key -> println("  key ${e.c}")
        else -> println("  scroll")
    }
}

fun chain(e: Ev): String =
    if (e is Click) "클릭"
    else if (e is Key) "키"
    else "그 밖"

fun noSubject(e: Ev): String = when {
    e is Click -> "클릭"
    e is Key -> "키"
    else -> "그 밖"
}

fun main() {
    val all: List<Ev> = listOf(Click(1), Key('a'), Scroll)
    for (e in all) println("${label(e)} ${code(e)} ${isKey(e)} ${chain(e)} ${noSubject(e)}")
    for (e in all) log(e)
}
===== kotlinc addelse3.kt -d o23e3 =====
(exit 0)
===== java -cp o23e3:kotlin-stdlib.jar Addelse3Kt =====
클릭 1 false 클릭 클릭
키 2 true 키 키
스크롤 3 false 그 밖 그 밖
  click 1
  key a
  scroll
(exit 0)
```

**④ `else` 판에 `Drag` 를 더했다.** 역시 `when` 은 한 글자도 안 고쳤다.

```text
===== 소스: addelse4.kt =====
sealed interface Ev
data class Click(val x: Int) : Ev
data class Key(val c: Char) : Ev
data object Scroll : Ev
data class Drag(val dx: Int, val dy: Int) : Ev

fun label(e: Ev): String = when (e) {
    is Click -> "클릭"
    is Key -> "키"
    else -> "스크롤"
}

fun code(e: Ev): Int = when (e) {
    is Click -> 1
    is Key -> 2
    else -> 3
}

fun isKey(e: Ev): Boolean = when (e) {
    is Key -> true
    is Click -> false
    else -> false
}

fun log(e: Ev) {
    when (e) {
        is Click -> println("  click ${e.x}")
        is Key -> println("  key ${e.c}")
        else -> println("  scroll")
    }
}

fun chain(e: Ev): String =
    if (e is Click) "클릭"
    else if (e is Key) "키"
    else "그 밖"

fun noSubject(e: Ev): String = when {
    e is Click -> "클릭"
    e is Key -> "키"
    else -> "그 밖"
}

fun main() {
    val all: List<Ev> = listOf(Click(1), Key('a'), Scroll, Drag(3, 4))
    for (e in all) println("${label(e)} ${code(e)} ${isKey(e)} ${chain(e)} ${noSubject(e)}")
    for (e in all) log(e)
}
===== kotlinc addelse4.kt -d o23e4 =====
(exit 0)
===== java -cp o23e4:kotlin-stdlib.jar Addelse4Kt =====
클릭 1 false 클릭 클릭
키 2 true 키 키
스크롤 3 false 그 밖 그 밖
스크롤 3 false 그 밖 그 밖
  click 1
  key a
  scroll
  scroll
(exit 0)
```

- ★★★ **에러 0건, 경고 0건.** 컴파일이 통과하고 프로그램이 돈다 — `Drag` 는 **아무도 처리하지 않은 채 `else` 로 흘러간다.**
- 출력에서 `Drag(3, 4)` 줄이 **`Scroll` 과 똑같이 `스크롤 3 false`** 로 찍힌다. **틀린 답이 조용히 나온 것**이고, 이것이 이 실험의 결론이다.

**격자로 세면 이렇다.**

| 판 | 검사되는 `when` 자리 | 검사 안 되는 자리 | 변형 추가 전 | 변형 추가 후 **에러** | 변형 추가 후 **경고** |
|---|---|---|---|---|---|
| `else` 없음 | **4곳**(식 3 + 문 1) | `if` 사슬 1 · 주체 없는 `when` 1 | 통과 | **4** | 0 |
| `else` 있음 | 4곳(전부 `else` 포함) | 같은 2곳 | 통과 | **0** | **0** |

- ★★ **Rust 18 편과 나란히 놓으면** ([`../../../rust/syntax/18-match-and-exhaustiveness/`](../../../rust/syntax/18-match-and-exhaustiveness/)) 격자가 거의 겹친다 — 거기도 `_` 없는 4곳이 **4건**, `_` 있는 판이 **0건**이었다.
- ★★★ **다른 점이 둘 있다.**
  - Rust 쪽은 `_` 판에서 ``warning: variant `Drag` is never constructed`` 라는 **경고가 1건** 나왔다(「안 쓰였다」이지 「안 처리했다」가 아니라서 쓸모는 없지만 **무언가는 말했다**). **Kotlin 은 경고도 0건**이다 — 이 실험에서 **Kotlin 쪽이 더 조용하다.**
  - Rust 의 `match` 는 **언제나 식**이라 「문이라 안 검사되는 자리」가 없다. **Kotlin 은 문도 검사한다**((2)) — 그래서 깨지는 자리가 Rust 와 같은 4곳이 됐다.
- ★ `else` 는 「짧게 쓰는 법」이 아니라 「**안전망을 끄는 선택**」이다. 쓸 자리는 있다 — **그 타입이 내 손 밖에 있을 때**(라이브러리의 `sealed`)와 **주체가 셀 수 없는 타입일 때**(`Int`·`String`).
- ★ 내 계층에는 `else` 대신 **남은 변형을 쉼표로 나열**한다(`Scroll, Drag -> ...`). 그러면 다음에 늘었을 때 **다시 깨진다.**

### (4) ★ 깨지지 않는 자리 둘 — `if` 사슬과 주체 없는 `when`

**언제 쓰나** — 리팩토링으로 `when` 을 `if` 로 바꾸려 할 때. **안전망이 거기서 끊긴다.**

```text
   fun chain(e: Ev): String =            fun noSubject(e: Ev): String = when {
       if (e is Click) "클릭"                e is Click -> "클릭"
       else if (e is Key) "키"               e is Key   -> "키"
       else "그 밖"                          else       -> "그 밖"
                                          }
        |                                      |
        v                                      v
   변형을 늘려도 아무 말 없다            변형을 늘려도 아무 말 없다
   (마지막 else 가 전부 받는다)          (주체가 없으니 셀 대상이 없다)
```

- 둘 다 (3)의 ②에서 **에러도 경고도 안 났다.**
- ★★ **주체 없는 `when`**(`when { 조건 -> ... }`)은 **`when` 이라는 낱말만 같을 뿐 완결성 검사와 무관**하다. 「`when` 을 썼으니 안전하겠지」가 여기서 거짓이 된다.
- ★ `if` 사슬은 **마지막 `else` 가 문법적으로 필요**하므로(식일 때) 사실상 (3)의 `else` 판과 같다.
- ★ 그래서 가르는 기준 한 줄 — 「**주체가 있는 `when` 인가**」. 그것만이 점호다.

### (5) ★★ 데이터 흐름 기반 완결성 검사 — **2.3.0 Stable 을 2.4.20 에서 확인했다**

**언제 쓰나** — 앞에서 조기 반환으로 한 변형을 걸러 냈을 때.

```text
===== 소스: sealflow.kt =====
sealed interface Ev
data class Click(val x: Int) : Ev
data class Key(val c: Char) : Ev
data object Scroll : Ev

fun render(e: Ev): String {
    if (e is Scroll) return "scroll"
    return when (e) {
        is Click -> "click ${e.x}"
        is Key -> "key ${e.c}"
    }
}

fun flag(b: Boolean): String = when (b) {
    true -> "켜짐"
    false -> "꺼짐"
}

fun main() {
    println("A ${render(Click(7))}")
    println("B ${render(Scroll)}")
    println("C ${flag(true)} ${flag(false)}")
}
===== kotlinc sealflow.kt -d o23f =====
(exit 0)
===== java -cp o23f:kotlin-stdlib.jar SealflowKt =====
A click 7
B scroll
C 켜짐 꺼짐
(exit 0)
```

**같은 코드에서 조기 반환만 뺐다.**

```text
===== 소스: sealflowbad.kt =====
sealed interface Ev
data class Click(val x: Int) : Ev
data class Key(val c: Char) : Ev
data object Scroll : Ev

fun render(e: Ev): String {
    return when (e) {
        is Click -> "click ${e.x}"
        is Key -> "key ${e.c}"
    }
}
===== kotlinc sealflowbad.kt -d o23fb =====
sealflowbad.kt:7:12: error: 'when' expression must be exhaustive. Add the 'Scroll' branch or an 'else' branch.
    return when (e) {
           ^^^^
(exit 1)
```

```text
   fun render(e: Ev): String {
       if (e is Scroll) return "scroll"      <- 여기서 Scroll 이 빠져나간다
       return when (e) {                        컴파일러가 그것을 기억한다
           is Click -> ...
           is Key   -> ...                   <- Scroll 가지가 없어도 통과
       }
   }

   조기 반환을 빼면 ->  error: 'when' expression must be exhaustive.
                               Add the 'Scroll' branch or an 'else' branch.
```

- ★★ **같은 `when`, 같은 가지인데 앞줄 한 줄에 따라 통과와 에러가 갈린다.** 완결성 판정이 **가지 목록만 보는 것이 아니라 그 지점까지의 데이터 흐름을 본다**는 뜻이다.
- ★ `Boolean` 주체도 같은 갈래다 — `flag(b)` 는 `true`/`false` **둘만 덮고 `else` 가 없는데** 통과한다(`C 켜짐 꺼짐`). **`Boolean` 의 값 공간이 둘뿐이라는 것을 컴파일러가 안다.**
- ★★ **판 확인** — Kotlin 목록의 판 이력표가 「23 `when` 완결성 — 데이터 흐름 기반 검사 = Stable **2.3.0**(2.2.20 도입)」이라고 적어 뒀고, **2.4.20 에서 경고 한 줄 없이 통과**하는 것을 직접 던져 확인했다.\
  ★ 다만 이 실행이 증명한 것은 「**2.4.20 에서는 된다**」뿐이다. 「2.2 이전에는 안 됐다」는 **이 환경에서 못 잰다** — `-language-version` 으로 옛 판을 되살리는 길이 2.4.20 에서 막혀 있기 때문이다(Kotlin 목록 머리말).

### (6) ★★ 같은 모듈·같은 패키지 제약 — 그리고 JVM 에서 무엇이 되나

**언제 쓰나** — 하위 타입을 다른 패키지로 옮기려 할 때, 그리고 「이 규칙이 Java 쪽에도 있나」를 물을 때.

```text
===== 소스: sealpkg.kt =====
package shapes

sealed interface Shape
===== 소스: sealpkgb.kt =====
package intruders

import shapes.Shape

class Triangle : Shape
===== kotlinc sealpkg.kt sealpkgb.kt -d o23p =====
sealpkgb.kt:5:18: error: a class can only extend a sealed class or interface declared in the same package.
class Triangle : Shape
                 ^^^^^
(exit 1)
```

**같은 패키지의 다른 파일에 두면**

```text
===== 소스: sealpkgok.kt =====
package shapes

class Square(val side: Int) : Shape
===== kotlinc sealpkg.kt sealpkgok.kt -d o23pok =====
(exit 0)
```

- 문구가 정확하다 — 「`a class can only extend a sealed class or interface declared in the same package.`」\
  **같은 모듈 + 같은 패키지**가 조건이다. **같은 파일일 필요는 없다** — 바로 위 블록이 그것을 보인 것이다.
- ★ 「1.5 이전에는 같은 파일이어야 했다」는 **이 환경에서 못 잰 것**이다 — 2.4.20 이 옛 `-language-version` 을 거부한다. [공식 문서](https://kotlinlang.org/docs/sealed-classes.html)에서 읽은 것이고 **실측이 아니다.**

**바이트코드 — 기본 `-jvm-target`(1.8)**

```text
===== 소스: sealbyte.kt =====
sealed class Shape

class Circle(val r: Double) : Shape()

class Rect(val w: Double, val h: Double) : Shape()
===== kotlinc sealbyte.kt -d o23b8 =====
(exit 0)
===== javap -p o23b8/Shape.class =====
Compiled from "sealbyte.kt"
public abstract class Shape {
  private Shape();
  public Shape(kotlin.jvm.internal.DefaultConstructorMarker);
}
(exit 0)
```

```text
===== javap -v -p o23b8/Shape.class | grep -E 'major version|^  flags:|^PermittedSubclasses:|^  (Circle|Rect)$' =====
  major version: 52
  flags: (0x0421) ACC_PUBLIC, ACC_SUPER, ACC_ABSTRACT
(exit 0)
```

**같은 소스를 `-jvm-target 17` 로**

```text
===== kotlinc -jvm-target 17 sealbyte.kt -d o23b17 =====
(exit 0)
===== javap -p o23b17/Shape.class =====
Compiled from "sealbyte.kt"
public abstract class Shape {
  private Shape();
  public Shape(kotlin.jvm.internal.DefaultConstructorMarker);
}
(exit 0)
```

```text
===== javap -v -p o23b17/Shape.class | grep -E 'major version|^  flags:|^PermittedSubclasses:|^  (Circle|Rect)$' =====
  major version: 61
  flags: (0x0421) ACC_PUBLIC, ACC_SUPER, ACC_ABSTRACT
PermittedSubclasses:
  Circle
  Rect
(exit 0)
```

```text
   -jvm-target 1.8 (기본)                 -jvm-target 17
   ----------------------------------     ----------------------------------
   major version: 52                      major version: 61
   ACC_PUBLIC, ACC_SUPER, ACC_ABSTRACT    ACC_PUBLIC, ACC_SUPER, ACC_ABSTRACT
   (PermittedSubclasses 없음)             PermittedSubclasses:
                                            Circle
                                            Rect
   -> 명단이 클래스 파일에 없다            -> 명단이 클래스 파일에 박힌다
      Kotlin 컴파일러만 안다                  JVM 과 javac 도 안다
```

- ★★★ **같은 소스가 플래그 하나로 다른 클래스 파일이 된다.** 「sealed 는 `PermittedSubclasses` 로 컴파일된다」를 플래그 없이 말하면 **기본값에서는 틀린 말**이다.
- 1.8 판에서 sealed 를 지키는 것은 **`private` 생성자** 하나다. `javap -p` 를 보면 `private Shape();` 과 합성 생성자 하나뿐이다.

**Java 쪽에서 상속을 시도하면**

```text
===== 소스: Intruder.java =====
public class Intruder extends Shape {
    public Intruder() { super(null); }
}
===== javac -cp o23b8:kotlin-stdlib.jar -d o23b8 Intruder.java =====
Intruder.java:2: error: constructor Shape in class Shape cannot be applied to given types;
    public Intruder() { super(null); }
                        ^
  required: no arguments
  found:    <null>
  reason: actual and formal argument lists differ in length
1 error
(exit 1)
```

```text
===== javac -cp o23b17:kotlin-stdlib.jar -d o23b17 Intruder.java =====
Intruder.java:1: error: class is not allowed to extend sealed class: Shape (as it is not listed in its 'permits' clause)
public class Intruder extends Shape {
       ^
Intruder.java:2: error: constructor Shape in class Shape cannot be applied to given types;
    public Intruder() { super(null); }
                        ^
  required: no arguments
  found:    <null>
  reason: actual and formal argument lists differ in length
2 errors
(exit 1)
```

- ★★ **1.8 판에서는 에러가 1건, 17 판에서는 2건**이다. 늘어난 한 줄이 바로 「`class is not allowed to extend sealed class: Shape (as it is not listed in its 'permits' clause)`」 — **JVM 층의 규칙**이다.
- 1.8 판에서도 막히기는 한다. 다만 막는 근거가 다르다 — **`private` 생성자**에 걸려 「`constructor Shape in class Shape cannot be applied to given types;`」가 난다. 합성 생성자(`Shape(DefaultConstructorMarker)`)는 `ACC_SYNTHETIC` 이라 **javac 가 아예 안 본다.**
- ★ 그래서 정확히 적으면 — 「**같은 규칙을 두 층이 각각 다른 방식으로 막는다**」이고, 어느 층이 도는지는 **`-jvm-target` 이 정한다.**
- ★ [`../../../java/syntax/15-sealed-classes/`](../../../java/syntax/15-sealed-classes/)와 겹치는 것이 `PermittedSubclasses` 다. **Java 쪽이 그 속성의 정본**이고 여기서는 **Kotlin 이 어느 판에서 그것을 내보내는지**까지만 본다.

## 문법 — 형태와 규칙

**형태** — `sealed interface`·`sealed class`·`when` 식·`when` 문이 한 프로그램에서 전부 도는 최소 예제다.

```text
===== 소스: form23.kt =====
sealed interface Result
data class Ok(val body: String) : Result
data class Err(val code: Int) : Result
data object Empty : Result

sealed class Node {
    class Leaf(val v: Int) : Node()
    class Branch(val l: Node, val r: Node) : Node()
}

fun show(r: Result): String = when (r) {
    is Ok -> "ok:${r.body}"
    is Err -> "err:${r.code}"
    Empty -> "empty"
}

fun sum(n: Node): Int = when (n) {
    is Node.Leaf -> n.v
    is Node.Branch -> sum(n.l) + sum(n.r)
}

fun report(r: Result) {
    when (r) {
        is Ok -> println("  본문 ${r.body.length}자")
        is Err -> println("  코드 ${r.code}")
        Empty -> println("  비었다")
    }
}

fun main() {
    val all: List<Result> = listOf(Ok("hi"), Err(404), Empty)
    println("Z ${all.map { show(it) }} ${sum(Node.Branch(Node.Leaf(1), Node.Leaf(2)))}")
    all.forEach { report(it) }
}
===== kotlinc form23.kt -d o23form =====
(exit 0)
===== java -cp o23form:kotlin-stdlib.jar Form23Kt =====
Z [ok:hi, err:404, empty] 3
  본문 2자
  코드 404
  비었다
(exit 0)
```

**규칙 불릿**

- `sealed` 는 **클래스와 인터페이스 둘 다**에 붙는다(인터페이스는 **1.5** 부터 — **문서 인용이지 실측이 아니다**).
- 하위 타입은 **같은 모듈 + 같은 패키지**에 있어야 한다((6)). **같은 파일일 필요는 없다.**
- `sealed` 클래스 자신은 **추상**이고 직접 인스턴스를 만들 수 없다.
- **완결성을 요구하는 주체 타입** — `sealed` · `enum` · `Boolean`. 이 셋은 **문에서도 요구된다**((2)).
- **식으로 쓰면 주체 타입과 무관하게** 완결이 요구된다.
- `else` 를 쓰면 **그 자리의 완결성 검사가 꺼진다**((3)).
- **주체 없는 `when`**(`when { ... }`)과 `if` 사슬은 **검사 대상이 아니다**((4)).
- 완결성은 **컴파일 시점의 판정**이다 — 따로 컴파일한 모듈의 명단이 뒤에 늘면 런타임에 `NoWhenBranchMatchedException` 이 난다([6번 주제](../06-when-expression/)가 정본이다).
- 데이터 흐름으로 좁혀진 타입은 **완결 판정에 반영된다**(**2.3.0 Stable**, (5)).

## 어디서 틀리나

1. ★★★ **「`when` 문은 검사 안 한다」고 믿는다.** `sealed`·`enum`·`Boolean` 주체면 **문도 검사한다**((2)). 에러 문구가 `expression` 이라고 말해서 더 헷갈린다.
2. ★★★ **`else` 를 습관으로 붙인다.** 그 순간 (3)의 격자가 **4에서 0으로** 바뀐다 — 변형을 늘려도 아무도 안 알려 준다.
3. ★★ **`when` 을 `if` 사슬이나 주체 없는 `when` 으로 리팩토링한다.** 겉모습은 비슷한데 **안전망이 사라진다**((4)).
4. ★★ **`sealed` 를 「상속 금지」로 읽는다.** 금지가 아니라 **명단**이다 — 같은 패키지 안에서는 얼마든지 늘릴 수 있고, **늘리는 것이 정상적인 설계 행위**다.
5. ★ **하위 타입을 다른 패키지로 옮긴다.** 「`can only extend ... in the same package.`」로 막힌다((6)).
6. ★ **`PermittedSubclasses` 가 항상 나온다고 믿는다.** 기본 `-jvm-target`(1.8)에서는 **안 나온다**((6)).
7. ★ **완결성을 런타임 보장으로 읽는다.** 컴파일 시점의 판정일 뿐이다 — 별도 모듈이면 뒤에 어긋날 수 있다([6번 주제](../06-when-expression/)).
8. ★ **`sealed class` 로 시작했다가 하위가 다른 인터페이스도 구현해야 해서 막힌다.** 상태를 안 줄 거면 **`sealed interface` 로 시작**하는 편이 되돌리기 쉽다((1)).

## 구현 세부사항 대 언어 보장

| 항목 | 어느 쪽인가 | 근거 |
|---|---|---|
| `sealed` 하위 타입이 **같은 모듈·같은 패키지** | **언어 보장** | (6) |
| `sealed`·`enum`·`Boolean` 주체는 **문에서도 완결 요구** | **언어 보장** | (2) |
| **식이면 주체 타입과 무관하게** 완결 요구 | **언어 보장** | (2) |
| `else` 가 완결성 검사를 끄는 것 | **언어 보장** | (3) |
| 주체 없는 `when`·`if` 사슬이 **검사 대상이 아닌 것** | **언어 보장** | (4) |
| 데이터 흐름으로 좁힌 타입이 완결에 반영되는 것 | **언어 보장**(2.3.0 Stable) | (5) |
| `PermittedSubclasses` 가 **`-jvm-target 17` 부터** 나오는 것 | **JVM 백엔드의 구현 + 타깃 플래그** | (6) |
| 1.8 판에서 `private` 생성자 + 합성 생성자로 막는 것 | **JVM 백엔드의 구현** | (6)의 `javap -p` |
| `javac` 에러가 1건이냐 2건이냐 | **위 구현의 따름 결과** | (6) |
| 에러 메시지의 **문구 그 자체** | **컴파일러 판의 산출물** | 전부 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 변형마다 **다른 데이터**를 들고 다닌다 | `sealed` | [24번 주제](../24-enum-class-vs-sealed/) — `enum` 은 못 한다 |
| 변형이 **고정된 상수 집합**이고 데이터가 없다 | `enum` | [24번 주제](../24-enum-class-vs-sealed/) — `entries`·`valueOf` 가 공짜다 |
| 하위가 **다른 인터페이스도 구현**해야 한다 | `sealed interface` | (1) — 상속 자리를 안 쓴다 |
| 하위가 **공통 상태·생성자**를 나눠 가진다 | `sealed class` | (1) |
| 데이터 없는 변형 하나 | `data object` | [22번 주제](../22-data-class-generated-members/) — `toString` 이 이름으로 나온다 |
| 남의 라이브러리 `sealed` 를 받는다 | `when` + **`else`** | 내가 못 고치는 명단이라 (3)의 안전망이 무의미하다 |
| 주체가 `Int`·`String` 이다 | `when` + `else` | 셀 수 없는 값 공간이다 |
| 명단을 **열어 두고** 싶다 | 그냥 `interface` | `sealed` 를 쓸 이유가 없다 |

## 핵심 문장

1. `sealed` 의 값어치는 **닫는 것이 아니라 셀 수 있게 되는 것**이다 — 변형을 늘렸을 때 **깨지는 자리가 그 증거**다.
2. 완결성을 정하는 것은 **식이냐 문이냐가 아니라 주체 타입**이다. `sealed`·`enum`·`Boolean` 은 **문에서도** 요구된다.
3. 변형 하나를 늘리면 `else` 없는 판은 **4곳이 깨지고**, `else` 판은 **에러도 경고도 0건**이다.
4. **`if` 사슬과 주체 없는 `when` 은 점호가 아니다** — 모양이 비슷해도 검사가 없다.
5. 완결성은 **가지 목록만 보지 않는다** — 데이터 흐름으로 좁힌 타입도 본다(2.3.0 Stable).
6. `sealed` 는 **`-jvm-target 17` 부터만** `PermittedSubclasses` 로 내려간다. 기본값에서는 **`private` 생성자**가 유일한 방어선이다.

## 관련 자료

- [6번 주제](../06-when-expression/) — `when` 식. **가지의 형태·guard·바이트코드 분기와 런타임 예외**가 거기가 정본이고, 여기는 **하위 타입을 늘렸을 때의 파급**부터다.
- [20번 주제](../20-interfaces-default-impl-and-super/) — 인터페이스. `sealed interface` 가 그 위에 선다.
- [22번 주제](../22-data-class-generated-members/) — `data class`·`data object`. **변형을 무엇으로 만들 것인가**가 거기다.
- [24번 주제](../24-enum-class-vs-sealed/) — `enum` 과의 선택 기준. **완결성은 둘 다 되고, 갈리는 것은 데이터와 인스턴스 수**다.
- [`../../../rust/syntax/18-match-and-exhaustiveness/`](../../../rust/syntax/18-match-and-exhaustiveness/) — **같은 격자로 같은 실험**을 한 편. (3)의 대비가 거기서 나왔다.
- [`../../../java/syntax/15-sealed-classes/`](../../../java/syntax/15-sealed-classes/) — Java `sealed`. **`PermittedSubclasses` 속성의 정본**이 거기다.
- [`../../../java/syntax/23-switch-pattern-matching/`](../../../java/syntax/23-switch-pattern-matching/) — Java 21 패턴 `switch`. **Java 가 같은 자리에 도착한 방식**이 거기다.
- [`../../언어-특성/README.md`](../../언어-특성/README.md) §3 — 「상태를 늘리면 컴파일이 깨진다」는 **설계 논지**. 여기는 **어느 조건에서 깨지고 어느 조건에서 조용히 통과하는가**다.

## 용어 풀이

> **`sealed`** — 「이 타입의 직접 하위 타입은 여기 적힌 것이 전부다」를 컴파일러에게 알리는 수식어.\
> 예: `sealed interface Ev` 아래 `Click`·`Key`·`Scroll` 셋만 두면 `when` 이 셋만 덮고도 통과한다.

> **완결성(exhaustiveness)** — 가지들이 가능한 값을 빠짐없이 덮었는지 컴파일러가 검사하는 것.\
> 예: 하나를 빼면 「`Add the 'Key' branch or an 'else' branch.`」.

> **주체 없는 `when`** — `when (x)` 가 아니라 `when { 조건 -> ... }` 형태.\
> 예: 완결성 검사와 **무관**하다((4)).

> **데이터 흐름 기반 완결성 검사** — 앞선 코드가 값의 범위를 좁혔으면 그것을 완결 판정에 반영하는 것(2.3.0 Stable).\
> 예: `if (e is Scroll) return ...` 뒤의 `when` 은 `Scroll` 가지가 없어도 통과한다.

> **`PermittedSubclasses`** — 클래스 파일의 속성 하나. 허용된 하위 클래스 이름이 들어간다.\
> 예: `javap -v` 로만 보이고, Kotlin 은 **`-jvm-target 17` 이상**에서만 내보낸다.

> **합성 생성자(synthetic constructor)** — 컴파일러가 만들어 넣는, 소스에 없는 생성자.\
> 예: `Shape(DefaultConstructorMarker)` — `ACC_SYNTHETIC` 이라 `javac` 가 안 본다.

## 더 들어가면

- **「`else` 를 쓰지 마라」는 반쪽이다.** 기준은 **명단의 소유자가 누구냐**다. 내 모듈의 `sealed` 면 `else` 를 빼서 안전망을 켜고, 남의 라이브러리 `sealed` 면 **`else` 가 오히려 옳다** — 그쪽이 변형을 늘려도 나는 컴파일조차 안 깨지는 편이 낫기 때문이다. Rust 의 `#[non_exhaustive]` 가 바로 그 경계를 **선언으로** 만든 것이고([`../../../rust/syntax/18-match-and-exhaustiveness/`](../../../rust/syntax/18-match-and-exhaustiveness/)), Kotlin 에는 **대응하는 표시가 없다.**
- **`else` 대신 쉼표 나열**이 중간 답이다 — `Scroll, Drag -> "그 밖"` 이라고 적으면 지금은 `else` 처럼 동작하고, 변형이 늘면 **다시 깨진다.** 안전망을 끄지 않으면서 가지를 줄이는 유일한 방법이다.
- **완결성은 컴파일 시점의 계약**이라는 것을 Java 쪽이 더 아프게 보여 준다 — Java 21 은 명단이 뒤에 늘면 런타임에 `MatchException` 을 던진다([`../../../java/syntax/23-switch-pattern-matching/`](../../../java/syntax/23-switch-pattern-matching/)). Kotlin 도 같은 성질이고 예외 이름만 다르다(`NoWhenBranchMatchedException` — [6번 주제](../06-when-expression/)).
