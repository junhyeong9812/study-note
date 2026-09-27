# kotlin/syntax/30 — 구조 분해 선언: `componentN` 과 그 한계 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Destructuring declarations](https://kotlinlang.org/docs/destructuring-declarations.html)(`operator` 요구·`_` 는 `componentN` 을 **안 부른다**·람다 괄호의 차이·이름 기반 분해가 **Experimental**) · [Data classes](https://kotlinlang.org/docs/data-classes.html).
> **실행 검증** — 이 문서의 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javac`·`javap` 에서 실제로 얻었다.\
> `kotlinc` 21회(컴파일 실패 4벌 · 경고 2벌) · `java` 15회 · `javac` 2회 · `javap` 5회 · `unzip` 1회.\
> ★★ 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적지 않았다. 소스 펜스의 첫 줄 배너도 캡처가 찍었다.
> **버전** — 구조 분해 선언 자체는 1.0 부터다. ★★ **이름 기반 분해는 이 판에서 실험 플래그 `-Xname-based-destructuring` 뒤에 있고, 새 문법은 「language version 2.5」부터라고 컴파일러가 스스로 말했다**((6)).\
> README 의 「뺀 것」 표는 이것을 **2.3.20 실험 기능**으로 적었다 — 도입 판(2.3.20)은 **이 문서가 직접 재지 않았다**(그 판의 컴파일러가 없다).
> **경계** — `data class` 가 `componentN` 을 **만든다는 것**과 「선언 쪽 순서를 바꾸면 뒤집힌다」의 **한 파일 실측**은 [22번 주제](../22-data-class-generated-members/) (4)가 정본이다.\
> 여기는 그 결론에서 출발해 **같은 호출부를 두 판의 선언에 붙여** 돌리고((1)), **호출부를 다시 컴파일하지 않은 경우**((3))와 **이름 기반 분해가 그것을 막는가**((6))까지 간다.\
> `operator` 규약 일반은 [31번 주제](../31-operator-overloading-infix-and-invoke/), `==` 는 [32번 주제](../32-equality-and-equals-contract/)가 정본이다.
> **대비** — Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **24번**([`24-record-patterns/`](../../../java/syntax/24-record-patterns/)) — ★ **Java 의 record 패턴도 위치 기반이다.** 같은 실험을 `javac` 로 던졌다((7)).
> 이 본문은 Claude 작성이다(원고 없음).

★ **본체는 첫째 창이다** — 「**같은 호출부를 두 판의 선언에 붙여 돌린 실행 출력**」.
위치 기반 분해가 위험하다는 것은 **에러가 안 나는 것**으로 드러난다. 그래서 가장 강한 근거는 **`(exit 0)` 두 번과 뒤바뀐 한 줄**이다.

## 이 주제가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **언어 보장** | 명세·공식 문서가 약속한 것 | ★★★ 짧은 꼴 `val (a, b) = x` 는 **`component1()`·`component2()` 를 순서대로** 부른다 · 번호는 **주 생성자 선언 순서** · `_` 는 그 번호를 **안 부른다** |
| **구현(JVM 백엔드)** | kotlinc 가 JVM 으로 내리는 방식 | `componentN` 이 **`getfield` 한 번짜리 메서드**라는 것 · `Map.Entry` 의 분해가 **`getKey` 로 인라인**되는 것((5)) |
| **이 판의 관찰** | kotlinc 2.4.20 에서 이번에 본 것 | ★★ `-Xname-based-destructuring` 의 세 모드와 그 문구((6)) · 진단 문구 |

## 이 판

```text
===== kotlinc -version =====
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | (이 주제에는 없다) | 해시코드·주소·시간을 **하나도 안 찍었다** |
| 안 흔들린다 | ★★★ 출력 — 특히 **`A Lovelace Ada`** 줄 | 이 주제의 답 자체다 |
| 안 흔들린다 | `javap` 출력 — 명령·서명·`Field first`/`Field last` | 같은 소스·같은 판이면 같다. 상수 풀 **번호**(`#23`)는 소스가 바뀌면 움직이므로 근거로는 **이름만** 읽는다 |
| 안 흔들린다 | 컴파일 진단의 **문구·`파일:줄:칸`·캐럿** | 결정적이다 |
| 안 흔들린다 | 모든 **종료 코드** | 이 주제는 **`(exit 0)` 이 곧 결론**인 칸이 많다 |

★ 근거 — 캡처 스크립트를 처음부터 두 번 돌려 **블록 전체를 바이트 단위로 대조**했다(수치는 3-answer 의 「실행 검증」).

## 한눈에 — 쉽게 말하면

**구조 분해는 「번호표 순서대로 짐을 나눠 받는 것」이다.** 받는 사람이 봉투에 적은 이름(`first`, `last`)은 **아무도 안 읽는다.**
`val (first, last) = p` 는 「1번 짐은 `first` 봉투에, 2번 짐은 `last` 봉투에」라는 뜻이다.

그러니 **짐을 싸는 쪽이 순서를 바꾸면**(선언 순서 변경) 받는 쪽 코드는 **한 글자도 안 바뀐 채** 짐이 뒤바뀐다.
타입이 같으면(둘 다 `String`) 검사원(컴파일러)도 **아무것도 못 잡는다.**

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 번호표 | `component1()` · `component2()` | (2) |
| 번호를 붙이는 쪽 | **주 생성자에 적은 순서** | (2) |
| 봉투에 적은 이름 | `val (first, last)` 의 변수 이름 — **안 읽힌다** | (1) |
| 짐 싸는 순서가 바뀜 | `data class P(val last, val first)` | (1)(3) |
| 받는 쪽을 다시 안 봐도 | **호출부를 다시 컴파일하지 않아도** 뒤바뀐다 | (3) |
| 이름표로 받기 | `p.first` · `p.last` — **안 뒤바뀐다** | (1)의 `B` |
| 봉투 이름을 읽는 새 규칙 | ★ 이름 기반 분해 — 이 판에서는 **실험 플래그** | (6) |

```text
   판 1  data class P(val first, val last)        판 2  data class P(val last, val first)
            component1 = first                           component1 = last
            component2 = last                            component2 = first

   호출부 (한 글자도 같다)   val (first, last) = p
            = val first = p.component1()               = val first = p.component1()  -> last 값
              val last  = p.component2()                 val last  = p.component2()  -> first 값

   출력     A Ada Lovelace                              A Lovelace Ada        <- 에러 0, 경고 0
```

## 이 주제가 답하려는 질문

1. `val (a, b) = x` 는 **무엇으로 풀리나** — 변수 이름은 어디에 쓰이나.
2. 선언 쪽 순서를 바꾸면 **어디서 무엇이 잡히나** — 다시 컴파일할 때, 안 할 때.
3. 이름 기반 분해는 **이 판에서 무엇을 해 주나** — 무엇을 경고하고 무엇을 고치나.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **실행 출력 — 두 판 나란히** | 같은 호출부가 **판 1 에서 맞고 판 2 에서 뒤바뀐다**((1)) | ★ **본체 창** |
| ★★ **`javap -c` 의 `getfield`** | `component1` 이 **어느 필드**를 읽나 — 번호가 선언 순서에서 온다((2)) | [26번 주제](../26-value-class-and-boxing/)의 창 |
| ★★ **따로 컴파일한 클래스패스 바꾸기** | 호출부 `.class` 를 **그대로 두고** 라이브러리만 갈아 끼운다((3)) | ★ 이 주제의 고유 창 |
| ★ **컴파일 진단** | 괄호 하나 차이·번호 부족·`operator` 누락((4)) | 이 갈래의 기본 창 |
| ★★ **`-Xname-based-destructuring` 세 모드** | 컴파일러에게 **이름을 읽게 하면** 무엇이 바뀌나((6)) | ★ 이 주제의 고유 창 |
| ★ **`javac` 로 같은 모양** | Java record 패턴도 위치 기반인가((7)) | 교차 갈래 |
| **부적용 — 컴파일 진단(판 2)** | ★★★ **잴 것이 없다.** 판 2 의 기본 컴파일은 **진단이 0줄**이다 — 「봤더니 조용했다」가 아니라 **이 창이 원리상 이 사고를 못 본다** | — |

★★ **제4의 상태 — 「잴 것이 없다」.** 판 2 에서 **진단 창은 부적용**이다. 두 필드가 **둘 다 `String`** 이므로 타입 검사가 가를 근거가 애초에 없다.\
★★ **제5의 상태 — 「같은 질문을 다른 창으로 물었다」.** 「이 뒤바뀜을 컴파일러가 알 수 있나」를 **기본 진단 대신 `-Xname-based-destructuring=name-mismatch` 로** 물었고, **경고 두 줄**이 답했다((6)).\
★ 바꾼 창의 한계 — 그 모드는 **`data class` 의 짧은 꼴**만 본다(경고 문구가 「positional destructuring of **data classes**」라고 말한다). 일반 클래스의 `operator fun componentN` 은 **이름이 없으므로** 대조할 것이 없다((4)).

### (1) ★★★ 필드 순서만 바꾸면 — 컴파일 에러 0, 값이 뒤바뀐다

**언제 쓰나** — 남이 쓴 `data class` 의 필드 순서를 「보기 좋게」 바꿀 때. 또는 그 클래스를 **분해해서 쓰는** 코드를 읽을 때.

판 1 과 판 2 는 **주 생성자의 두 줄 순서만** 다르다. `sample()` 은 **이름 붙인 인자**로 만들므로 두 판이 **같은 객체**(`first=Ada`, `last=Lovelace`)를 만든다.

```kotlin
// person1.kt
data class P(val first: String, val last: String) {
    companion object {
        fun sample() = P(first = "Ada", last = "Lovelace")
    }
}
```

```kotlin
// person2.kt
data class P(val last: String, val first: String) {
    companion object {
        fun sample() = P(first = "Ada", last = "Lovelace")
    }
}
```

호출부는 **하나**다 — 두 판에 똑같이 붙인다.

```kotlin
// readp.kt
fun main() {
    val p = P.sample()
    val (first, last) = p
    println("A $first $last")
    println("B ${p.first} ${p.last}")
}
```

```text
===== kotlinc person1.kt readp.kt -d o30a =====
(exit 0)
===== java -cp o30a:kotlin-stdlib.jar ReadpKt =====
A Ada Lovelace
B Ada Lovelace
(exit 0)
```

```text
===== kotlinc person2.kt readp.kt -d o30b =====
(exit 0)
===== java -cp o30b:kotlin-stdlib.jar ReadpKt =====
A Lovelace Ada
B Ada Lovelace
(exit 0)
```

- ★★★ **`A Lovelace Ada`** — 호출부를 **한 글자도 안 고쳤는데** `first` 에 `Lovelace` 가 들어갔다. `kotlinc … (exit 0)`, 경고도 **0줄**이다.
- ★★★ **`B Ada Lovelace` 는 두 판이 같다** — `p.first`·`p.last` 는 **이름으로** 읽으므로 선언 순서와 무관하다. 같은 호출부 안에서 **위치로 읽은 줄만** 뒤집혔다.
- ★★ 이것이 [README](../README.md) 가 이 주제에 건 과녁이다 — 「**위치 기반 분해가 왜 위험한가**」. 두 필드의 **타입이 같은 순간** 사고는 전부 조용해진다.
- ★ [22번 주제](../22-data-class-generated-members/) (4)는 **한 파일 안에서** `Coord(y, x)` 로 같은 결론을 봤다. 여기서는 **호출부 파일을 고정**하고 선언 파일만 갈아 끼웠다 — 실무에서 사고가 나는 모양이 이쪽이다(선언과 호출부가 **다른 파일, 다른 사람**이다).

**두 필드의 타입이 다르면 잡히나** — `String` 과 `Int` 로 같은 실험을 했다.

```kotlin
// mix1.kt
data class M(val name: String, val age: Int) {
    companion object {
        fun sample() = M(name = "Ada", age = 36)
    }
}
```

```kotlin
// mix2.kt
data class M(val age: Int, val name: String) {
    companion object {
        fun sample() = M(name = "Ada", age = 36)
    }
}
```

```kotlin
// readm.kt
fun main() {
    val (name, age) = M.sample()
    println("A $name $age")
}
```

```kotlin
// readm2.kt
fun useIt(m: M) {
    val (name, age) = m
    println(name.uppercase() + (age + 1))
}
```

```text
===== kotlinc mix1.kt readm.kt -d o30m1 =====
(exit 0)
===== java -cp o30m1:kotlin-stdlib.jar ReadmKt =====
A Ada 36
(exit 0)
===== kotlinc mix2.kt readm.kt -d o30m2 =====
(exit 0)
===== java -cp o30m2:kotlin-stdlib.jar ReadmKt =====
A 36 Ada
(exit 0)
===== kotlinc mix1.kt readm2.kt -d o30m3 =====
(exit 0)
===== kotlinc mix2.kt readm2.kt -d o30m4 =====
readm2.kt:3:18: error: unresolved reference 'uppercase' on receiver of type 'Int'.
    println(name.uppercase() + (age + 1))
                 ^^^^^^^^^
(exit 1)
```

- ★★★ **타입이 달라도 `readm.kt` 는 조용하다** — `A 36 Ada`. 분해한 변수는 **타입을 적지 않았으므로** `name` 이 `Int` 로, `age` 가 `String` 으로 **추론이 따라 바뀌고**, 문자열 템플릿은 무엇이든 받는다.
- ★★ `readm2.kt` 에서야 잡혔다 — 그런데 **에러는 한 줄뿐**이다(「`unresolved reference 'uppercase' on receiver of type 'Int'.`」). `age + 1` 은 `age` 가 `String` 이 되자 **`String.plus(Any?)`** 로 풀려 **통과했다**([31번 주제](../31-operator-overloading-infix-and-invoke/)의 `plus` 규약).
- ★ 그러니 「타입이 다르면 컴파일러가 잡는다」는 **변수를 그 타입으로 쓰는 줄이 있을 때만** 맞다. 잡느냐는 **분해 자리가 아니라 쓰는 자리**가 정한다.

### (2) ★★ 번호는 선언 순서에서 온다 — `javap` 가 가리키는 필드

**언제 쓰나** — 「`component1` 은 무엇을 돌려주나」를 외우지 말고 확인할 때.

```text
===== javap -c -p o30a/P.class o30b/P.class | awk '/^public final class/{print} /component[12]\(\);/{f=1; print} f && /getfield/{print; f=0}' =====
public final class P {
  public final java.lang.String component1();
       1: getfield      #23                 // Field first:Ljava/lang/String;
  public final java.lang.String component2();
       1: getfield      #25                 // Field last:Ljava/lang/String;
public final class P {
  public final java.lang.String component1();
       1: getfield      #23                 // Field last:Ljava/lang/String;
  public final java.lang.String component2();
       1: getfield      #25                 // Field first:Ljava/lang/String;
(exit 0)
```

- ★★★ **판 1 의 `component1` 은 `Field first`, 판 2 의 `component1` 은 `Field last`** 를 읽는다. 메서드 이름은 같고 **읽는 필드만** 바뀌었다.
- ★ 번호를 붙이는 규칙은 **언어**다 — 「주 생성자에 적은 순서대로 1, 2, …」. `getfield` 한 번짜리 메서드로 내리는 것은 **JVM 백엔드의 구현**이다.

```text
===== javap -c -p o30b/ReadpKt.class | grep -E 'invoke.*Method P\.' =====
       8: invokevirtual #22                 // Method P.component1:()Ljava/lang/String;
      13: invokevirtual #25                 // Method P.component2:()Ljava/lang/String;
      65: invokevirtual #59                 // Method P.getFirst:()Ljava/lang/String;
      77: invokevirtual #62                 // Method P.getLast:()Ljava/lang/String;
(exit 0)
```

- ★★ 호출부는 **`P.component1` → `P.component2`** 를 부르고(8·13번 오프셋), `B` 줄은 **`P.getFirst` → `P.getLast`** 를 부른다(65·77번). 두 줄의 차이가 바이트코드에 그대로 있다 — **위치로 읽는 줄과 이름으로 읽는 줄**이다.

### (3) ★★ 호출부를 다시 컴파일하지 않아도 — 여전히 뒤바뀐다

**언제 쓰나** — 라이브러리만 새 판으로 올리고 **앱은 다시 빌드하지 않을 때**(바이너리 호환).

```text
===== kotlinc person1.kt -d lib30v1 =====
(exit 0)
===== kotlinc -cp lib30v1 readp.kt -d app30 =====
(exit 0)
===== kotlinc person2.kt -d lib30v2 =====
(exit 0)
===== java -cp app30:lib30v1:kotlin-stdlib.jar ReadpKt =====
A Ada Lovelace
B Ada Lovelace
(exit 0)
===== java -cp app30:lib30v2:kotlin-stdlib.jar ReadpKt =====
A Lovelace Ada
B Ada Lovelace
(exit 0)
```

```text
   app30/ReadpKt.class  (판 1 에 대고 컴파일 — 다시 안 만든다)
        invokevirtual P.component1:()Ljava/lang/String;   <- 이름 + 서명만 들고 있다
                 |
       클래스패스  lib30v1/P.class                 lib30v2/P.class
                 component1() { getfield first }    component1() { getfield last }
                 |                                   |
       A 줄      Ada Lovelace                        Lovelace Ada     <- 링크 에러 없음
```

- ★★★ `app30` 의 `ReadpKt.class` 는 **판 1 에 대고 컴파일한 그대로**다. 클래스패스에서 `lib30v1` 을 `lib30v2` 로 **바꾸기만** 했더니 `A Lovelace Ada` 가 됐다.
- ★★ 왜 링크 에러가 안 나나 — 호출부가 부르는 것은 **`component1:()Ljava/lang/String;`** 이라는 **이름과 서명**이다((2)). 판 2 에도 **정확히 그 서명**이 있다. JVM 은 **「어느 필드를 읽는 메서드인가」를 묻지 않는다.**
- ★ 그래서 이 사고는 **다시 컴파일해도, 안 해도** 같다. 「다시 빌드하면 잡히겠지」가 틀린 이유가 (1)이고, 「빌드를 안 했으니 옛 동작이겠지」가 틀린 이유가 여기다.

### (4) ★ 괄호 하나 차이 · 번호가 모자랄 때 · 일반 클래스

**언제 쓰나** — 람다에서 분해할 때, 그리고 `data class` 가 아닌 타입을 분해하고 싶을 때.

```kotlin
// dsforms.kt
data class Pt(val x: Int, val y: Int)

fun main() {
    val pts = listOf(Pt(1, 2), Pt(3, 4))
    println("A " + pts.map { (a, b) -> a * 10 + b })
    val m = mapOf("k1" to 1, "k2" to 2)
    println("B " + m.map { (k, v) -> "$k=$v" })
    val (_, y) = Pt(7, 8)
    println("C $y")
    for ((i, p) in pts.withIndex()) println("D $i $p")
    val f: (Pt, Pt) -> Int = { a, b -> a.x + b.x }
    println("E " + f(Pt(1, 0), Pt(2, 0)))
}
```

```text
===== kotlinc dsforms.kt -d o30f =====
(exit 0)
===== java -cp o30f:kotlin-stdlib.jar DsformsKt =====
A [12, 34]
B [k1=1, k2=2]
C 8
D 0 Pt(x=1, y=2)
D 1 Pt(x=3, y=4)
E 3
(exit 0)
```

- `A [12, 34]` — `{ (a, b) -> … }` 는 **매개변수 하나**를 받아 그 자리에서 분해한다.
- `B [k1=1, k2=2]` — `Map` 의 원소(`Map.Entry`)도 같은 꼴로 분해된다((5)).
- `C 8` — `val (_, y)` 는 **첫 칸을 버린다.**
- `D 0 …` — `withIndex()` 가 주는 `IndexedValue` 도 분해된다.
- `E 3` — `{ a, b -> … }` 는 **매개변수 둘**이다. 분해가 아니다.

```text
===== javap -c -p o30f/DsformsKt.class | grep -E 'Method Pt\.(component|get)' =====
     121: invokevirtual #59                 // Method Pt.component1:()I
     128: invokevirtual #62                 // Method Pt.component2:()I
     398: invokevirtual #62                 // Method Pt.component2:()I
      13: invokevirtual #220                // Method Pt.getX:()I
      17: invokevirtual #220                // Method Pt.getX:()I
(exit 0)
```

- ★★ **`_` 는 `component1` 을 아예 안 부른다** — `C` 줄(398번)에는 **`Pt.component2` 하나뿐**이다. 문서의 「skipped 칸의 `componentN` 은 호출되지 않는다」가 바이트코드로 보인다.
- ★ `E` 줄의 람다는 `Pt.getX` 를 두 번 부른다 — **두 매개변수**로 받아 이름으로 읽었기 때문이다.

**괄호를 잘못 치면**

```kotlin
// dsbad.kt
data class Pt(val x: Int, val y: Int)

fun main() {
    val pts = listOf(Pt(1, 2), Pt(3, 4))
    println(pts.map { a, b -> a + b })
    val g: (Pt, Pt) -> Int = { (a, b) -> a + b }
    val (p, q, r) = Pt(1, 2)
}
```

```text
===== kotlinc dsbad.kt -d o30x =====
dsbad.kt:5:17: error: cannot infer type for type parameter 'R'. Specify it explicitly.
    println(pts.map { a, b -> a + b })
                ^^^
dsbad.kt:5:21: error: argument type mismatch: actual type is '(Pt, ??? (Unknown type for value parameter b)) -> uninferred R (of fun <T, R> Iterable<T>.map)', but '(Pt) -> uninferred R (of fun <T, R> Iterable<T>.map)' was expected.
    println(pts.map { a, b -> a + b })
                    ^^^^^^^^^^^^^^^^^
dsbad.kt:5:26: error: cannot infer type for value parameter 'b'. Specify it explicitly.
    println(pts.map { a, b -> a + b })
                         ^
dsbad.kt:5:33: error: unresolved reference 'plus' for operator '+' on receiver of type 'Pt'.
    println(pts.map { a, b -> a + b })
                                ^
dsbad.kt:6:28: error: initializer type mismatch: expected '(Pt, Pt) -> Int', actual '(Pt) -> Int'.
    val g: (Pt, Pt) -> Int = { (a, b) -> a + b }
                           ^
dsbad.kt:7:21: error: destructuring of type 'Pt' requires operator function 'component3()'.
    val (p, q, r) = Pt(1, 2)
                    ^^^^^^^^
(exit 1)
```

- ★★ **5번째 줄 `{ a, b -> }` 를 `map` 에 넘기면 에러가 넷**이다. 핵심은 둘째 줄 — 「`actual type is '(Pt, ???) -> …', but '(Pt) -> …' was expected`」. **괄호가 없으면 매개변수가 둘**이라 `map` 이 요구하는 **한 개짜리 함수**와 안 맞는다.
- ★★ **6번째 줄은 반대 방향**이다 — 두 개짜리 함수 자리에 `{ (a, b) -> }` 를 넣으니 「`expected '(Pt, Pt) -> Int', actual '(Pt) -> Int'`」. **괄호 한 쌍이 매개변수 개수를 바꾼다.**
- ★ 7번째 줄 — 「`destructuring of type 'Pt' requires operator function 'component3()'.`」 **번호가 모자라면** 컴파일러가 **없는 번호의 이름**을 댄다.

**일반 클래스에 `componentN` 을 달면**

```kotlin
// regok.kt
class Span(val lo: Int, val hi: Int) {
    operator fun component1() = lo
    operator fun component2() = hi
}

fun main() {
    val (lo, hi) = Span(3, 9)
    println("A $lo $hi")
}
```

```kotlin
// regbad.kt
class Solo(val a: Int) {
    fun component1() = a
}

fun main() {
    val (a) = Solo(1)
    println(a)
}
```

```text
===== kotlinc regok.kt -d o30r =====
(exit 0)
===== java -cp o30r:kotlin-stdlib.jar RegokKt =====
A 3 9
(exit 0)
===== kotlinc regbad.kt -d o30r2 =====
regbad.kt:6:10: error: 'operator' modifier is required on 'fun component1(): Int' defined in 'Solo'.
    val (a) = Solo(1)
         ^
(exit 1)
```

- `Span` 은 `data class` 가 아닌데 **분해된다** — 규약은 「`operator fun componentN()` 이 있다」뿐이다.
- ★★ `Solo` 는 `component1` 이 **있는데도** 막힌다 — 「`'operator' modifier is required on 'fun component1(): Int'`」. 이름만 맞으면 안 되고 **`operator` 로 규약 참가를 선언**해야 한다([31번 주제](../31-operator-overloading-infix-and-invoke/)의 규칙과 같다).

### (5) ★ `Map.Entry` 의 분해 — 표준 라이브러리의 **확장** `componentN`

**언제 쓰나** — `for ((k, v) in map)` 이 왜 되는지, 그 비용이 무엇인지 볼 때.

```kotlin
// entry30.kt
fun main() {
    val m = mapOf("a" to 1)
    for ((k, v) in m) println("A $k $v")
}
```

```text
===== kotlinc entry30.kt -d o30m =====
(exit 0)
===== java -cp o30m:kotlin-stdlib.jar Entry30Kt =====
A a 1
(exit 0)
===== unzip -p kotlin-stdlib-sources.jar commonMain/kotlin/collections/Maps.kt | grep -n -E 'operator fun <K, V> Map.Entry<K, V>.component[12]' =====
312:public inline operator fun <K, V> Map.Entry<K, V>.component1(): K = key
325:public inline operator fun <K, V> Map.Entry<K, V>.component2(): V = value
(exit 0)
```

```text
===== javap -c -p o30m/Entry30Kt.class | grep -E 'Entry\.|component' =====
      45: invokeinterface #53,  1           // InterfaceMethod java/util/Map$Entry.getKey:()Ljava/lang/Object;
      55: invokeinterface #58,  1           // InterfaceMethod java/util/Map$Entry.getValue:()Ljava/lang/Object;
(exit 0)
```

- ★★ `Map.Entry` 는 Java 인터페이스라 `component1` 이 **없다.** 표준 라이브러리가 **`inline operator fun <K, V> Map.Entry<K, V>.component1(): K = key`** 라는 **확장 함수**로 규약을 붙였다(312번 줄) — [13번 주제](../13-extension-functions-and-properties/)의 확장이다.
- ★ `inline` 이라 바이트코드에는 `component1` 호출이 **없고** `Map$Entry.getKey` 가 바로 박혔다. 호출 수는 **이름으로 읽을 때와 같다** — 시간은 **안 쟀다.**

### (6) ★★★ 이름 기반 분해 — 이 판에서는 무엇을 해 주나

**언제 쓰나** — 「이름으로 받으면 (1)의 사고가 안 날 텐데」를 **이 판에서 확인**할 때.

먼저 **컴파일러에게 그런 기능이 있는지** 물었다.

```text
===== kotlinc -X | grep -e 'name-based-destructuring' =====
  -Xname-based-destructuring=only-syntax|name-mismatch|complete
                             -Xname-based-destructuring=only-syntax:   Enables syntax for positional destructuring with square brackets and the full form of name-based destructuring with parentheses;
                             -Xname-based-destructuring=name-mismatch: Reports warnings when short form positional destructuring of data classes uses names that don't match the property names;
                             -Xname-based-destructuring=complete:      Enables short-form name-based destructuring with parentheses;
(exit 0)
```

- ★★ **`-X` 목록에 있다** — 즉 **실험 기능**이다. 모드가 셋이다: `only-syntax`(새 문법만) · `name-mismatch`(이름이 안 맞으면 경고) · `complete`(짧은 꼴을 **이름 기반으로**).

**경고 모드** — (1)의 판 2 를 그대로 다시 던졌다.

```text
===== kotlinc -Xname-based-destructuring=name-mismatch person2.kt readp.kt -d o30c =====
readp.kt:3:10: warning: variable name 'first' differs from accessed property name 'last'. This syntax will be used for name-based destructuring in a future release, and this code will change its meaning.
Use the full name-based destructuring syntax '(val first = last, ...)', the new positional destructuring syntax '[first, ...]', or align the names to prepare for the transition.
See https://kotl.in/name-based-destructuring for more information.
    val (first, last) = p
         ^^^^^
readp.kt:3:17: warning: variable name 'last' differs from accessed property name 'first'. This syntax will be used for name-based destructuring in a future release, and this code will change its meaning.
Use the full name-based destructuring syntax '(val last = first, ...)', the new positional destructuring syntax '[last, ...]', or align the names to prepare for the transition.
See https://kotl.in/name-based-destructuring for more information.
    val (first, last) = p
                ^^^^
(exit 0)
```

- ★★★ **판 2 의 사고를 컴파일러가 처음으로 말했다** — 「`variable name 'first' differs from accessed property name 'last'.`」 두 칸 모두다.
- ★★ 경고의 둘째 문장이 **이 기능의 앞날**을 말한다 — 「`This syntax will be used for name-based destructuring in a future release, and this code will change its meaning.`」 같은 소스의 **뜻이 바뀔 예정**이라는 예고다.
- ★ 이 모드도 **`(exit 0)`** 이다. 막지는 않는다.

**완전 모드** — 짧은 꼴을 이름으로 읽게 했다.

```text
===== kotlinc -Xname-based-destructuring=complete person2.kt readp.kt -d o30d =====
(exit 0)
===== java -cp o30d:kotlin-stdlib.jar ReadpKt =====
A Ada Lovelace
B Ada Lovelace
(exit 0)
```

```text
===== javap -c -p o30d/ReadpKt.class | grep -E 'invoke.*Method P\.' =====
       8: invokevirtual #22                 // Method P.getFirst:()Ljava/lang/String;
      13: invokevirtual #25                 // Method P.getLast:()Ljava/lang/String;
      65: invokevirtual #22                 // Method P.getFirst:()Ljava/lang/String;
      77: invokevirtual #25                 // Method P.getLast:()Ljava/lang/String;
(exit 0)
```

- ★★★ **`A Ada Lovelace`** — 판 2 인데 **맞는 값**이 나왔다. 바이트코드는 `component1`/`component2` 가 아니라 **`P.getFirst` → `P.getLast`** 를 부른다(8·13번). 같은 소스가 **플래그 하나로 다른 메서드를 부른다.**
- ★★ 그러니 (1)의 `A` 줄은 **플래그에 따라 답이 갈리는 소스**다 — 판 1 에서는 두 모드가 같은 답을 내고, **판 2 에서만** 갈린다.

**판을 올려 보면**

```text
===== kotlinc -language-version 2.5 person2.kt readp.kt -d o30e =====
warning: language version 2.5 is experimental, there are no backwards compatibility guarantees for new language and library features. Use the stable version 2.4 instead.
(exit 0)
===== java -cp o30e:kotlin-stdlib.jar ReadpKt =====
A Lovelace Ada
B Ada Lovelace
(exit 0)
```

- ★★ `-language-version 2.5` 는 「`language version 2.5 is experimental`」 경고와 함께 **통과하지만 여전히 `A Lovelace Ada`** 다. 2.5 에서도 짧은 꼴은 **위치 기반 그대로**였다(`complete` 를 켜야 이름이 된다).

**새 문법**

```kotlin
// newform.kt
data class Q(val last: String, val first: String)

fun main() {
    val q = Q(first = "Ada", last = "Lovelace")
    val [a, b] = q
    println("A $a $b")
    (val f = first, val l = last) = q
    println("B $f $l")
}
```

```text
===== kotlinc newform.kt -d o30n =====
newform.kt:5:9: error: the feature "name based destructuring" is only available since language version 2.5
    val [a, b] = q
        ^
newform.kt:7:6: error: the feature "name based destructuring" is only available since language version 2.5
    (val f = first, val l = last) = q
     ^^^
newform.kt:7:21: error: the feature "name based destructuring" is only available since language version 2.5
    (val f = first, val l = last) = q
                    ^^^
(exit 1)
===== kotlinc -Xname-based-destructuring=only-syntax newform.kt -d o30n2 =====
(exit 0)
===== java -cp o30n2:kotlin-stdlib.jar NewformKt =====
A Lovelace Ada
B Ada Lovelace
(exit 0)
```

- ★★★ 플래그 없이 던지면 「`the feature "name based destructuring" is only available since language version 2.5`」 — **컴파일러가 판 경계를 스스로 말했다.** 대괄호 `[a, b]` 가 **새 위치 기반** 꼴이고, `(val f = first, …)` 가 **이름 기반의 온전한 꼴**이다.
- ★ `only-syntax` 를 켜면 통과한다 — `A Lovelace Ada`(대괄호 = **위치**), `B Ada Lovelace`(이름). **같은 객체에서 두 꼴이 다른 답을 낸다.**
- ★ 이 판은 **2.4.20** 이다 — `-language-version 2.5` 는 **이 컴파일러가 흉내 낸 앞 판**이지 진짜 2.5 컴파일러가 아니다.

| 던진 형태 | 결과 | 읽는 법 |
|---|---|---|
| 기본 | 판 2 에서 **조용히 뒤바뀜** | 짧은 꼴 = 위치 |
| `-Xname-based-destructuring=name-mismatch` | ★ **경고 두 줄** · `exit 0` | 사고를 **말해 주지만 막지 않는다** |
| `-Xname-based-destructuring=complete` | ★★ **맞는 값** · `getFirst`/`getLast` 호출 | 짧은 꼴 = **이름** |
| `-language-version 2.5` | 실험 경고 · **여전히 뒤바뀜** | 2.5 흉내에서도 짧은 꼴은 위치 |
| 새 문법(`[a, b]` · `(val f = first)`) 기본 | 「only available since language version 2.5」 | 판 경계 |

### (7) ★ Java 의 record 패턴 — 같은 사고, 같은 침묵

**언제 쓰나** — 「Java 는 이름으로 분해하니 안전하겠지」라고 생각할 때.

```java
// RecA.java
record JP(String first, String last) {
    static JP sample() { return new JP("Ada", "Lovelace"); }
}
```

```java
// RecB.java
record JP(String last, String first) {
    static JP sample() { return new JP("Lovelace", "Ada"); }
}
```

```java
// ReadJ.java
public class ReadJ {
    public static void main(String[] args) {
        Object o = JP.sample();
        if (o instanceof JP(var first, var last)) {
            System.out.println("A " + first + " " + last);
        }
        JP p = (JP) o;
        System.out.println("B " + p.first() + " " + p.last());
    }
}
```

```text
===== javac -d o30j1 RecA.java ReadJ.java =====
(exit 0)
===== java -cp o30j1 ReadJ =====
A Ada Lovelace
B Ada Lovelace
(exit 0)
===== javac -d o30j2 RecB.java ReadJ.java =====
(exit 0)
===== java -cp o30j2 ReadJ =====
A Lovelace Ada
B Ada Lovelace
(exit 0)
```

- ★★★ **`javac` 도 경고 0줄에 `A Lovelace Ada`** 다. `instanceof JP(var first, var last)` 의 `first`·`last` 도 **패턴 변수 이름일 뿐** 컴포넌트 이름과 대조되지 않는다 — Java record 패턴은 **위치 기반**이다([Java 24번](../../../java/syntax/24-record-patterns/)이 정본).
- ★ `B` 줄(`p.first()`)은 두 판이 같다 — Kotlin 과 **완전히 같은 모양**이다.
- ★ 차이는 하나 — Java 쪽 `RecB` 의 `sample()` 은 **위치로 생성**해야 해서 `new JP("Lovelace", "Ada")` 로 **손으로 맞췄다.** Kotlin 은 **이름 붙인 인자**가 있어 생성 쪽은 안 뒤바뀐다. 사고가 **읽는 쪽에만** 남는 것은 두 언어가 같다.

## 문법 — 형태와 규칙

**형태** — 짧은 꼴·`_`·람다 분해가 한 프로그램에서 전부 도는 최소 예제다.

```kotlin
// form30.kt
data class Item(val sku: String, val qty: Int)

fun main() {
    val (sku, qty) = Item("s-1", 3)
    val (_, onlyQty) = Item("s-2", 5)
    val totals = mapOf("s-1" to 3, "s-2" to 5).map { (k, v) -> "$k:$v" }
    println("Z $sku $qty $onlyQty $totals")
}
```

```text
===== kotlinc form30.kt -d o30z =====
(exit 0)
===== java -cp o30z:kotlin-stdlib.jar Form30Kt =====
Z s-1 3 5 [s-1:3, s-2:5]
(exit 0)
```

**규칙 불릿**

- `val (a, b) = x` 는 **`val a = x.component1(); val b = x.component2()`** 다 — 이름은 **안 읽는다**((1)(2)).
- `componentN` 은 **`operator fun`** 이어야 한다. `data class` 는 **주 생성자 순서대로** 자동으로 만든다([22번 주제](../22-data-class-generated-members/)).
- 번호가 모자라면 「`requires operator function 'componentN()'`」((4)).
- **`_`** 는 그 칸의 `componentN` 을 **부르지 않는다**((4)).
- 람다 — `{ (a, b) -> }` 는 **매개변수 하나를 분해**, `{ a, b -> }` 는 **매개변수 둘**((4)).
- `for ((k, v) in map)` 은 표준 라이브러리의 **`inline` 확장 `componentN`** 이 해 준다((5)).
- ★ **이름 기반 분해는 이 판(2.4.20)에서 실험**이다 — `-Xname-based-destructuring`, 새 문법은 「language version 2.5」부터((6)).

## 어디서 틀리나

1. ★★★ **변수 이름이 맞춰 줄 거라 믿는다.** 안 읽는다((1)). 판 2 에서 `first` 에 `Lovelace` 가 들어갔다.
2. ★★★ **`data class` 필드 순서를 「보기 좋게」 바꾼다.** 분해하는 호출부가 **에러 0, 경고 0** 으로 뒤바뀐다((1)).
3. ★★ **「타입이 다르면 컴파일러가 잡는다」고 믿는다.** 분해 변수는 타입을 추론하므로 **쓰는 줄이 그 타입을 요구할 때만** 잡힌다 — `age + 1` 은 `String` 이 돼도 통과했다((1)).
4. ★★ **「다시 빌드하면 잡힌다」거나 「빌드를 안 했으니 옛 동작이다」라고 믿는다.** 둘 다 틀렸다((1)(3)) — 서명이 같다.
5. ★★ **람다에서 괄호를 빠뜨리거나 더한다.** 매개변수 **개수가 바뀐다**((4)).
6. ★ **`component1` 만 있으면 된다고 믿는다.** `operator` 가 없으면 막힌다((4)).
7. ★ **`_` 로 건너뛴 칸도 계산된다고 믿는다.** 호출 자체가 없다((4)) — 부작용이 있는 `componentN` 이면 차이가 난다.
8. ★★ **이름 기반 분해를 기본 기능으로 안다.** 이 판에서는 **실험 플래그 뒤**다((6)). 그리고 경고가 말하듯 **켜면 기존 코드의 뜻이 바뀐다.**
9. ★ **「Java 는 record 패턴이 있으니 안전하다」.** 거기도 **위치**다((7)).

## 구현 세부사항 대 언어 보장

| 항목 | 어느 쪽인가 | 근거 |
|---|---|---|
| 짧은 꼴이 **`componentN` 을 순서대로** 부르는 것 | ★★★ **언어 보장** | (1)(2) |
| `data class` 의 번호가 **주 생성자 선언 순서**인 것 | **언어 보장** | (2) |
| `componentN` 에 **`operator` 가 필요한** 것 | **언어 보장** | (4) |
| `_` 가 그 칸의 `componentN` 을 **안 부르는** 것 | **언어 보장**(문서가 명시) | (4) |
| 람다 괄호가 **매개변수 개수**를 가르는 것 | **언어 보장** | (4) |
| `componentN` 이 **`getfield` 한 번**으로 내려가는 것 | **JVM 백엔드의 구현** | (2) |
| 라이브러리만 바꿔도 **링크가 되는** 것 | **JVM 의 링크 규칙**(이름 + 서명) | (3) |
| `Map.Entry` 분해가 **`getKey` 로 인라인**되는 것 | **표준 라이브러리의 구현**(`@InlineOnly`) | (5) |
| 이름 기반 분해의 **세 모드와 그 문구** · 「2.5 부터」 | ★ **이 판(2.4.20)의 실험 상태** — 바뀔 수 있다 | (6) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| `Pair`·`Triple`·`Map.Entry`·`IndexedValue` — **위치가 곧 뜻**인 타입 | 구조 분해 | 첫째·둘째 말고 **다른 이름이 없다** |
| 내가 소유하고 **순서가 안 바뀔** 작은 `data class` 둘 | 구조 분해 | 짧다 — 단, 순서를 바꾸면 (1) |
| ★★ **남의 `data class`**, 필드가 **같은 타입 둘 이상** | ★ **이름으로 읽기**(`p.first`) | (1)(3) — 순서가 바뀌면 조용하다 |
| 필드 **셋 이상** | 이름으로 읽기 | 번호와 뜻을 맞추는 비용이 커진다 |
| 람다에서 원소 하나를 풀기 | `{ (a, b) -> }` | (4) — 괄호를 **빠뜨리지 마라** |
| 이름 기반 분해가 필요하다 | ★ **아직 기다린다** | (6) — 이 판에서 실험, 켜면 뜻이 바뀐다 |

## 핵심 문장

1. 구조 분해의 짧은 꼴은 **`componentN` 을 순서대로** 부르고, **변수 이름은 읽지 않는다.**
2. `data class` 의 번호는 **주 생성자 선언 순서**다 — 순서를 바꾸면 같은 서명의 `component1` 이 **다른 필드**를 읽는다.
3. 그래서 필드 순서 변경은 **컴파일 에러 0 · 경고 0 · 값이 뒤바뀜**이고, **호출부를 다시 컴파일하지 않아도** 똑같다.
4. `_` 는 그 칸을 **호출조차 안 하고**, 람다의 괄호 한 쌍은 **매개변수 개수**를 바꾼다.
5. 이름 기반 분해는 이 판에서 **실험**이다 — 켜면 경고가 사고를 **말해 주고**, `complete` 모드는 **getter 를 부르게** 바꾼다.

## 관련 자료

- [22번 주제](../22-data-class-generated-members/) — ★★ **선행.** `componentN` 이 **생성된다는 것**과 한 파일 안의 순서 뒤집기(4)가 거기다. 여기는 **두 판·바이너리·이름 기반**까지.
- [31번 주제](../31-operator-overloading-infix-and-invoke/) — `operator` 규약 일반. `componentN` 은 그 규약의 한 이름이다.
- [13번 주제](../13-extension-functions-and-properties/) — 확장 함수. `Map.Entry.component1` 이 **확장**인 이유.
- [11번 주제](../11-inline-functions/) — 인라인. `getKey` 가 바로 박히는 이유.
- [`../../../java/syntax/24-record-patterns/`](../../../java/syntax/24-record-patterns/) — Java record 패턴. **같은 위치 기반**의 정본.

## 용어 풀이

> **구조 분해 선언(destructuring declaration)** — 객체 하나를 변수 여럿으로 한 번에 푸는 선언.\
> 예: `val (a, b) = pair`.

> **`componentN`** — 구조 분해가 부르는 `operator` 함수. **번호가 곧 위치**다.\
> 예: `component1()` 은 첫째 칸.

> **위치 기반(positional)** — 변수를 **순서로** 맞추는 방식. Kotlin 짧은 꼴·Java record 패턴이 이쪽이다.

> **이름 기반(name-based) 분해** — 변수를 **프로퍼티 이름으로** 맞추는 방식. 이 판에서는 실험(`-Xname-based-destructuring`).\
> 예: `(val f = first, val l = last) = q`.

> **바이너리 호환(binary compatibility)** — 호출부를 **다시 컴파일하지 않고** 라이브러리만 바꿔도 링크·실행이 되는 성질. 뜻까지 같다는 보장은 **아니다**((3)).

> **`IndexedValue`** — `withIndex()` 가 주는 `data class`. `(index, value)` 로 분해된다.

## 더 들어가면

- **왜 처음부터 위치 기반이었나** — `componentN` 은 **`Pair`·`Triple`·`Map.Entry` 처럼 위치가 곧 뜻인 타입**을 위해 규약 하나로 모든 타입에 열어 둔 것이다. 이름이 없는 타입(일반 클래스의 `operator fun component1`)에도 되려면 **이름이 아니라 번호**여야 했다. 그 대가가 (1)이다 — **이름이 있는 `data class` 에서도 이름을 버린다.**
- **이름 기반으로 옮겨 가는 길** — 경고 문구가 세 갈래를 권한다: `(val first = last, …)`(온전한 이름 꼴) · `[first, …]`(새 위치 꼴) · **이름을 맞추기.** 짧은 꼴의 뜻이 **위치 → 이름**으로 바뀌는 것이므로, 지금 짧은 꼴을 **이름과 다르게** 쓰는 코드는 전환 때 **조용히 다른 값**을 받게 된다 — 「`this code will change its meaning`」이 그 예고다. 이 문서는 전환이 **언제 기본값이 되는지**는 모른다(재지 않았다).
