# kotlin/syntax/23 — `sealed class`/`sealed interface` 와 `when` 완결성 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javap`·`javac` 에서 실제로 얻었다.\
> ⚠️ 이 주제의 역어셈블은 **두 판**이다 — 기본 `-jvm-target`(1.8 · `major version: 52`)과 **`-jvm-target 17`**(`major version: 61`). **둘이 다르다는 것이 7번의 답**이다.
> ★★ 아래 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적은 자리가 없다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **문도 검사한다** — 에러 세 줄, 통과하는 것은 `Int` 주체의 문 하나뿐

**출력**

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

**왜 그런가**

| 함수 | 주체 | 식/문 | 결과 |
|---|---|---|---|
| `stmtOverSealed` | `sealed` | 문 | ★ **에러** |
| `stmtOverInt` | `Int` | 문 | **통과** |
| `stmtOverBoolean` | `Boolean` | 문 | ★ **에러** |
| `exprOverInt` | `Int` | 식 | **에러**(`else` 필요) |

- ★★★ **완결성을 정하는 것은 「식이냐 문이냐」가 아니라 「주체 타입」이다.** `sealed`·`enum`·`Boolean` 은 **셀 수 있는 값 공간**이므로 문에서도 검사한다.
- 식일 때는 **주체 타입과 무관하게** 완결이 요구된다 — 값을 돌려줘야 하는데 안 맞는 가지가 오면 돌려줄 것이 없기 때문이다. 그래서 `Int` **식**은 `else` 가 필요하다.
- ★★ 에러 문구가 **문인데도 `'when' expression must be exhaustive.`** 라고 말한다. 문구만 읽으면 「식일 때만 그런가 보다」로 오해한다 — **문구가 아니라 몇 번째 줄에서 났는지를 보라.** `sealstmt.kt:6:5` 는 `stmtOverSealed` 의 `when` 문이다.
- ★ 이 규칙의 정본은 [6번 주제](../06-when-expression/)다. 여기서는 결론과 실측만 쓴다.

### 2. ★ `A 5` · `B ["a",1,null]` · `C true`

**출력**

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

**왜 그런가**

- `A 5` — `Add(Num(2), Add(Num(3), Zero))` 를 재귀로 접으면 `2 + (3 + 0) = 5` 다.
- `B ["a",1,null]` — `JList` 가 원소마다 `render` 를 다시 부른다.
- `C true` — `data object Zero` 는 **싱글턴**이라 `===` 가 참이다([22번 주제](../22-data-class-generated-members/)).
- 두 `when` 에 `else` 가 없는데 통과하는 이유는 **주체가 `sealed`** 이고 **하위 타입을 전부 적었기** 때문이다. 명단이 닫혀 있으니 셀 수 있다.
- ★ `JList` 가 `Json` 이면서 `Comparable<JList>` 인 것이 **`sealed interface` 가 1.5 에 들어온 이유**다. `sealed class Json` 이었다면 `JList` 의 **상속 자리 하나를 `Json` 이 이미 써 버려** 다른 클래스를 상속할 수 없다(인터페이스는 여럿 되지만 클래스는 하나다 — [19번 주제](../19-inheritance-open-final-override/)).
- ★ 가지에 `is Expr.Num` 과 `Expr.Zero` 가 섞여 있다 — 앞은 **타입 검사**, 뒤는 **싱글턴 객체와의 동등 비교**다. `data object` 에는 `is` 를 안 써도 된다.

### 3. ★★★ **정확히 4곳**이 깨진다 — 그리고 **2곳은 안 깨진다**

**출력** — 추가 전(통과한다)

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

**출력** — `Drag` 한 줄만 더한 diff

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

**출력** — 그 파일을 컴파일하면

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

**왜 그런가**

| 함수 | 형태 | 변형 추가 후 |
|---|---|---|
| `label` | `when` **식** (String) | ★ **에러** |
| `code` | `when` **식** (Int) | ★ **에러** |
| `isKey` | `when` **식** (Boolean) | ★ **에러** |
| `log` | `when` **문** | ★ **에러** |
| `chain` | `if` 사슬 | **아무 말 없음** |
| `noSubject` | 주체 없는 `when` | **아무 말 없음** |

- ★★★ **깨진 자리 4곳, 안 깨진 자리 2곳.** `log` 가 `when` **문**인데도 깨진 것이 1번의 규칙이 그대로 적용된 결과다.
- diff 를 보면 바뀐 것은 **변형 선언 한 줄과 `main` 의 리스트 한 줄**뿐이다. `when` 은 **한 글자도 안 고쳤는데** 네 곳이 깨졌다 — 이것이 `sealed` 를 쓰는 이유의 전부다.
- ★ `chain`·`noSubject` 가 안 깨지는 이유는 **완결성 검사의 대상이 아니기** 때문이다(10번).
- ★ 에러 문구가 친절하다 — 「`Add the 'is Drag' branch or an 'else' branch.`」. **빠진 것의 이름을 대 준다.**

### 4. ★★★ **에러 0건, 경고 0건** — 그리고 `Drag` 가 `Scroll` 인 척 찍힌다

**출력**

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

**왜 그런가**

```text
   출력 3·4번째 줄
   스크롤 3 false 그 밖 그 밖      <- Scroll
   스크롤 3 false 그 밖 그 밖      <- Drag  (구분이 안 된다)
     scroll
     scroll                        <- log 도 마찬가지
```

- ★★★ **컴파일이 통과하고 프로그램이 돈다.** 아무도 `Drag` 를 처리하지 않았는데 **에러도 경고도 없다.**
- 출력에서 `Drag(3, 4)` 가 **`Scroll` 과 한 글자도 같게** 찍힌다. **틀린 답이 조용히 나온 것**이 이 실험의 결론이다.

**격자**

| 판 | 검사되는 `when` 자리 | 검사 안 되는 자리 | 변형 추가 전 | 추가 후 **에러** | 추가 후 **경고** |
|---|---|---|---|---|---|
| `else` 없음 | **4곳**(식 3 + 문 1) | `if` 사슬 1 · 주체 없는 `when` 1 | 통과 | **4** | 0 |
| `else` 있음 | 4곳(전부 `else` 포함) | 같은 2곳 | 통과 | **0** | **0** |

- ★★ 격자가 말하는 것 — `else` 는 「짧게 쓰는 법」이 아니라 「**안전망을 끄는 스위치**」다. 같은 코드에서 깨지는 자리가 **4에서 0으로** 간다.
- ★ 그래서 `else` 를 적을 때는 「이 자리에서 **미래의 변형을 조용히 삼켜도 되는가**」를 한 번 묻고 적어야 한다(9번).

### 5. ★★ `A click 7` · `B scroll` · `C 켜짐 꺼짐` — 앞줄이 판정을 바꾼다

**출력**

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

**출력** — 조기 반환만 뺀 판

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

**왜 그런가**

```text
   fun render(e: Ev): String {
       if (e is Scroll) return "scroll"    <- 이 줄이 있으면
       return when (e) {                      그 뒤의 e 는 Scroll 일 수 없다
           is Click -> ...                    컴파일러가 그것을 알고 완결로 친다
           is Key   -> ...
       }
   }
       이 줄을 지우면 -> error: 'when' expression must be exhaustive.
                                Add the 'Scroll' branch or an 'else' branch.
```

- ★★ **같은 `when`, 같은 가지인데 앞줄 하나에 따라 통과와 에러가 갈린다.** 완결성 판정이 **가지 목록만 보는 것이 아니라 그 지점까지의 데이터 흐름을 본다**는 뜻이다.
- `flag(b)` 는 **다른 규칙이 아니라 같은 갈래**다 — `Boolean` 의 값 공간이 `true`/`false` **둘뿐**이라는 것을 컴파일러가 알고, 둘을 덮었으니 `else` 없이 통과한다.
- ★★ **판 확인** — Kotlin 목록([`../README.md`](../README.md))의 판 이력표가 「23 `when` 완결성 — 데이터 흐름 기반 검사 = Stable **2.3.0**(2.2.20 도입)」이라 적어 뒀고, **2.4.20 에서 경고 한 줄 없이 통과**하는 것을 직접 던져 확인했다.\
  ★ 다만 증명된 것은 「**2.4.20 에서는 된다**」뿐이다. 「2.2 이전에는 안 됐다」는 **이 환경에서 못 잰다** — 2.4.20 이 옛 `-language-version` 을 거부하기 때문이다(Kotlin 목록 머리말의 「못 잰 것」).

### 6. ★ 막힌다 — 조건은 「**같은 모듈 + 같은 패키지**」다

**출력**

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

**출력** — 같은 패키지의 **다른 파일**에 두면

```text
===== 소스: sealpkgok.kt =====
package shapes

class Square(val side: Int) : Shape
===== kotlinc sealpkg.kt sealpkgok.kt -d o23pok =====
(exit 0)
```

**왜 그런가**

- 문구가 그대로 답이다 — 「`a class can only extend a sealed class or interface declared in the same package.`」
- ★ **같은 파일일 필요는 없다.** 같은 `package shapes` 의 다른 파일에 `class Square(val side: Int) : Shape` 를 두면 **exit 0 으로 통과**한다 — 위 두 블록이 그 대비다.\
  ★ **1.5 이전에는 같은 파일이어야 했다** — 이것은 이 환경에서 **못 잰 것**이고(2.4.20 에서 옛 판을 되살릴 수 없다) [공식 문서](https://kotlinlang.org/docs/sealed-classes.html)에서 읽은 것이다.
- ★★ 제약이 없으면 **완결성 검사가 성립하지 않는다.** 누구든 아무 데서나 하위 타입을 더할 수 있으면 컴파일러가 명단을 **셀 수가 없다.** 「같은 모듈」이 「한 번에 같이 컴파일되는 단위」라서 그때만 셈이 성립한다.
- ★ 그래서 완결성은 **컴파일 시점의 판정**이다 — 다른 모듈이 나중에 다시 컴파일되면 어긋날 수 있고, 그때 나는 것이 `NoWhenBranchMatchedException` 이다([6번 주제](../06-when-expression/)가 실측 정본이다).

### 7. ★★ 기본값에서는 **평범한 추상 클래스**, 17 부터 **`PermittedSubclasses` 가 박힌다**

**출력** — 기본 `-jvm-target`(1.8)

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

**출력** — `-jvm-target 17`

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

**왜 그런가**

| | 기본(1.8) | `-jvm-target 17` |
|---|---|---|
| `major version` | **52** | **61** |
| 클래스 플래그 | `ACC_PUBLIC, ACC_SUPER, ACC_ABSTRACT` | **같다** |
| `PermittedSubclasses` | **없다** | **있다** — `Circle`·`Rect` |
| 무엇이 sealed 를 지키나 | **`private` 생성자** | 위 + **JVM 의 sealed 규칙** |

- `javap -p` 로 보면 두 판 모두 생성자가 **둘**이다 — `private Shape();` 과 `public Shape(DefaultConstructorMarker);`. 뒤엣것은 **합성 생성자**로, 하위 클래스가 상위 생성자를 부르려고 컴파일러가 만든 것이다.
- ★★★ **「sealed 는 `PermittedSubclasses` 로 컴파일된다」는 `-jvm-target 17` 이상에서만 참**이다. `kotlinc` 의 기본값은 **1.8** 이므로 **플래그를 안 밝힌 이 주장은 기본 설정에서 거짓**이다.
- ★ 클래스 플래그가 **두 판에서 같다**는 것도 봐 둘 만하다 — JVM 에는 `ACC_SEALED` 같은 비트가 **없고** 별도 속성(`PermittedSubclasses`)으로 표현한다. [19번 주제](../19-inheritance-open-final-override/)의 `ACC_FINAL` 과 대비되는 자리다.

### 8. ★★ 에러가 **1건 대 2건** — 막는 층이 다르다

**출력** — 1.8 로 컴파일한 `Shape` 에 대해

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

**출력** — 17 로 컴파일한 `Shape` 에 대해

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

**왜 그런가**

```text
   1.8 판                                  17 판
   ------------------------------------    ------------------------------------
   에러 1건                                 에러 2건
   constructor Shape ... cannot be          class is not allowed to extend
   applied to given types;                  sealed class: Shape (as it is not
     required: no arguments                 listed in its 'permits' clause)
     found:    <null>                     + 위와 같은 생성자 에러
        |                                        |
        v                                        v
   막는 것은 private 생성자                 막는 것은 JVM 의 sealed 규칙
   (Kotlin 컴파일러가 남긴 흔적)            (클래스 파일의 PermittedSubclasses)
```

- ★★ **늘어난 한 건이 정확히 sealed 규칙**이다. 1.8 판에서는 `javac` 가 「이 클래스는 sealed 다」라는 것을 **알 방법이 없다.**
- 1.8 판에서도 막히기는 한다 — 하지만 근거가 **우연에 가깝다.** `private Shape()` 은 접근 불가이고, 합성 생성자 `Shape(DefaultConstructorMarker)` 는 **`ACC_SYNTHETIC` 이라 `javac` 가 아예 안 본다**(그래서 「`required: no arguments`」라고 말한다 — javac 눈에는 인자 없는 생성자 하나뿐이다).
- ★★★ 정확히 적으면 — 「**같은 규칙을 두 층이 각각 다른 방식으로 막고, 어느 층이 도는지는 `-jvm-target` 이 정한다**」.
- ★ [`../../../java/syntax/15-sealed-classes/`](../../../java/syntax/15-sealed-classes/)가 `PermittedSubclasses` 속성의 정본이다. 여기서는 **Kotlin 이 어느 판에서 그것을 내보내는지**까지만 본다.

### 9. `else` 는 컴파일러에게 「**이제 세지 마라**」고 말하는 것이다

**왜 그런가**

- `else` 가 있으면 **모든 값이 어딘가에 걸린다는 것이 자명**해지므로 컴파일러는 **명단을 셀 이유가 없어진다.** 그 순간 4번의 격자가 4에서 0으로 간다.
- ★ **그런데도 `else` 가 옳은 자리**가 있다. 기준 한 줄 — 「**그 명단의 소유자가 나인가**」.
  - **내 모듈의 `sealed`** → `else` 를 빼라. 변형을 늘리는 것은 내가 하는 일이고, 그때 깨져야 고칠 자리를 찾는다.
  - **남의 라이브러리 `sealed`** → `else` 가 **오히려 옳다.** 그쪽이 변형을 늘렸을 때 내 코드가 **컴파일조차 안 되는 것**이 더 나쁘다.
  - **주체가 `Int`·`String`** → 셀 수 없는 값 공간이라 선택의 여지가 없다.
- ★★ **중간 답은 쉼표 나열**이다 — `Scroll, Drag -> "그 밖"` 이라고 적으면 지금은 `else` 처럼 동작하고, **변형이 늘면 다시 깨진다.** 안전망을 끄지 않으면서 가지를 줄이는 유일한 방법이다.
- ★ Rust 에는 이 경계를 **선언으로** 만든 `#[non_exhaustive]` 가 있는데([`../../../rust/syntax/18-match-and-exhaustiveness/`](../../../rust/syntax/18-match-and-exhaustiveness/)) **Kotlin 에는 대응하는 표시가 없다.** 사람이 판단해야 한다.

### 10. **둘 다 안 깨졌다** — 검사의 대상이 아니기 때문이다

**왜 그런가**

```text
   검사받는 것                        검사 안 받는 것
   -----------------------------      ---------------------------------
   when (e) { ... }                   when { e is Click -> ... }
   ^^^^^^^^                                ^^^^^ 주체가 없다
   주체가 있고 그 타입이 셀 수 있다

                                      if (e is Click) ... else if ... else ...
                                      ^^ 애초에 when 이 아니다
```

- 3번의 `chain`(`if` 사슬)과 `noSubject`(주체 없는 `when`)는 변형이 늘어도 **에러도 경고도 없었다.**
- ★★ **주체 없는 `when` 은 완결성 검사를 안 받는다.** 「`when` 을 썼으니 안전하겠지」가 여기서 거짓이 된다 — 낱말만 같고 **다른 문법**이다.
- ★★ 리팩토링으로 잃는 것 한 줄 — 「**`when (x)` 를 `if` 나 주체 없는 `when` 으로 바꾸면 그 자리의 점호가 사라진다.**」 코드 모양이 거의 같아서 리뷰에서도 잘 안 보인다.
- ★ 반대로 `if` 사슬을 `when (x)` 로 바꾸는 것은 **안전망을 켜는 리팩토링**이다 — 그리고 그때 컴파일이 깨지면 **원래 처리가 빠져 있던 것**이다.

### 11. Rust 는 **경고라도 하나 줬고**, Kotlin 은 **아무 말도 안 한다**

**왜 그런가**

| | Rust `match` | Kotlin `when` |
|---|---|---|
| 전부 나열한 판에 변형 추가 | **에러 4건**(E0004 × 4) | **에러 4건** |
| `_` / `else` 판에 변형 추가 | **에러 0 · 경고 1건**(``variant `Drag` is never constructed``) | **에러 0 · 경고 0건** |
| 문(statement) 형태 | **없다** — `match` 는 언제나 식이다 | **있다. 그리고 검사한다**(1번) |
| 「명단이 열릴 수 있다」는 선언 | `#[non_exhaustive]` | **없다** |

- ★★ 격자의 **왼쪽 절반이 완전히 겹친다** — 두 언어가 같은 실험에서 같은 수치를 냈다([`../../../rust/syntax/18-match-and-exhaustiveness/`](../../../rust/syntax/18-match-and-exhaustiveness/)).
- ★★★ **오른쪽에서 갈린다.** Rust 는 `_` 판에서도 ``warning: variant `Drag` is never constructed`` 를 냈다 — 쓸모는 적지만(「안 쓰였다」이지 「안 처리했다」가 아니다) **무언가는 말했다.** Kotlin 은 **경고도 0건**이라 이 실험에서 **더 조용하다.**
- Rust 의 `match` 는 언제나 식이라 「문이라 검사 안 되는 자리」가 **없다.** Kotlin 은 문도 검사하므로(1번) 결과적으로 **깨지는 자리 수가 같아졌다.**
- Java 21 쪽은 명단이 뒤에 늘면 **런타임에 `MatchException`** 이다([`../../../java/syntax/23-switch-pattern-matching/`](../../../java/syntax/23-switch-pattern-matching/)). Kotlin 의 대응물은 **`NoWhenBranchMatchedException`** 이고, 그것을 실제로 던지게 만든 실측은 [6번 주제](../06-when-expression/)에 있다.

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

★ **흔들리는 칸과 안 흔들리는 칸**(제출 전 재대조에서 「고칠 것」과 「설계상 다른 것」을 가르는 선언이다)

| 흔들린다 | 안 흔들린다 |
|---|---|
| **없다** — 해시코드·시간·주소를 **하나도 찍지 않았다** | 컴파일 에러의 **문구·`파일:줄:칸`·캐럿 줄·개수** |
| | `javap` 출력 **전체**(`major version`·플래그·`PermittedSubclasses` 목록) |
| | `javac` 에러의 **문구와 개수** |
| | 모든 **종료 코드** · `println` 출력 |

> 근거 — 캡처 스크립트를 처음부터 다시 돌려 **블록 전체를 바이트 단위로 대조**했고, 이 주제에서 **달라진 파일은 0개**였다.

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `sealstmt.kt` | ★★★ **`when` 문도 검사한다** — 주체 타입이 정한다 | `kotlinc` (컴파일 실패가 결과) |
| `sealkinds.kt` | `sealed class` 와 `sealed interface` · `data object` 싱글턴 | `kotlinc` → `java` |
| `addnoelse3.kt` → `addnoelse4.kt` | ★★★ **변형 추가 실험** — 깨지는 자리 **4곳** | `kotlinc` → `java` · `diff` · `kotlinc`(실패) |
| `addelse3.kt` → `addelse4.kt` | ★★★ 같은 실험의 `else` 판 — **에러 0 · 경고 0** | `kotlinc` → `java` ×2 |
| `sealflow.kt` / `sealflowbad.kt` | ★★ **데이터 흐름 기반 완결성**(2.3.0 Stable)을 2.4.20 에서 확인 | `kotlinc` → `java` · `kotlinc`(실패) |
| `sealpkg.kt` + `sealpkgb.kt` | **같은 패키지 제약** — 다른 패키지면 막힌다 | `kotlinc` (컴파일 실패가 결과) |
| `sealpkg.kt` + `sealpkgok.kt` | ★ **같은 패키지의 다른 파일이면 통과하는 것** | `kotlinc` |
| `sealbyte.kt` | ★★ `-jvm-target` 이 **`PermittedSubclasses` 유무를 가르는 것** | `kotlinc` ×2 → `javap -p` ×2 → `javap -v` ×2 |
| `Intruder.java` | ★★ Java 쪽 에러가 **1건 대 2건**인 것 | `javac` ×2 (둘 다 실패가 결과) |
| `form23.kt` | `sealed`·`when` 식·`when` 문이 한 프로그램에서 도는 것(`Z`) | `kotlinc` → `java` |

**구현 의존 항목** — 에러 메시지의 **문구 그 자체**, 합성 생성자의 **이름과 시그니처**(`DefaultConstructorMarker`), `javap` 의 표시 형식, `javac` 가 에러를 내는 **순서** — 전부 이 컴파일러·JDK 판의 산출물이다.\
**`PermittedSubclasses` 유무**는 **구현이 아니라 타깃 플래그의 산출물**이라 따로 적는다 — 같은 컴파일러가 플래그에 따라 둘 다 낸다.\
반면 **「주체 타입이 완결성을 정한다」·「`else` 가 검사를 끈다」·「같은 모듈·같은 패키지」·「데이터 흐름이 판정에 반영된다」** 는 **언어의 계약**이다.

**★ 못 잰 것** — 「`sealed interface` 는 1.5 부터」·「데이터 흐름 완결성은 2.3.0 Stable」·「1.5 이전에는 같은 파일」은 **이 환경에서 잴 수 없다.**
2.4.20 이 옛 `-language-version` 을 거부하므로 **옛 판의 동작을 되살릴 방법이 없다.**
확인한 것은 전부 「**2.4.20 에서 어떻게 되는가**」이고, 「언제부터인가」는 [공식 상태표](https://kotlinlang.org/docs/kotlin-language-features-and-proposals.html)와 Kotlin 목록의 판 이력표를 인용한 것이다. **둘을 섞어 읽으면 안 된다.**

**★ 던져 봤더니 예상과 달랐던 것 — 두 건**

1. ★★★ **`when` 문도 완결성을 요구한다.** 「식일 때만 강제된다」는 전제를 갖고 던졌는데 `stmtOverSealed`·`stmtOverBoolean` 이 **둘 다 에러**였다(1번). 통과한 것은 `Int` 주체의 문 하나뿐이다. **에러 문구가 문에서도 `'when' expression'` 이라고 말해서** 이 오해가 잘 안 풀린다 — 문구가 아니라 **어느 줄에서 났는지**를 봐야 한다.
2. ★★ **1.8 판에서도 Java 쪽 상속이 막혔다.** 「`PermittedSubclasses` 가 없으니 Java 에서는 뚫릴 것」이라고 예상하고 `super(null)` 로 합성 생성자를 노렸는데, **`ACC_SYNTHETIC` 이라 `javac` 가 그 생성자를 아예 안 봤다**(8번). 막히기는 하되 **막는 근거가 sealed 규칙이 아니라 접근 제어**라는 것이 실제 모습이다.

**안 터진 것도 출력이다** — 4번의 `else` 판은 **경고 한 줄 없이** 컴파일되고 돌면서 `Drag` 를 `Scroll` 로 취급했다.
Rust 는 같은 자리에서 **경고를 하나는 냈다**(11번). 「아무 말 없음」이 이 주제에서 가장 중요한 관찰이고, 그것을 수치로 만든 것이 4번의 격자다.
