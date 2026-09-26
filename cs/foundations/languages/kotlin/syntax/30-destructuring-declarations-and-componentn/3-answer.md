# kotlin/syntax/30 — 구조 분해 선언: `componentN` 과 그 한계 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javac`·`javap` 에서 실제로 얻었다.\
> 역어셈블은 **기본 `-jvm-target`(1.8 · `major version: 52`)** 이 정본이다.
> ★★ 아래 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적은 자리가 없다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 둘 다 **에러 0 · 경고 0** — 판 2 의 `A` 줄만 `Lovelace Ada` 로 뒤바뀐다

**출력**

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

**왜 그런가**

- ★★★ `val (first, last) = p` 는 **`p.component1()`·`p.component2()`** 다. 판 2 에서 `component1` 은 **`last`** 를 돌려준다 — 변수 이름 `first` 는 **아무도 안 읽는다.**
- ★★ `B` 줄은 **이름**(`p.first`)으로 읽으므로 두 판이 같다. 두 필드가 **둘 다 `String`** 이라 타입 검사도 가를 근거가 없다.

### 2. ★★ 죽지 않는다 — `A Lovelace Ada`

**출력**

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

**왜 그런가**

- ★★★ 호출부가 부르는 것은 **`P.component1:()Ljava/lang/String;`** 이라는 **이름과 서명**뿐이다. 판 2 에도 정확히 그 서명이 있으니 **링크가 된다** — 그 메서드가 **어느 필드를 읽는지**는 JVM 이 묻지 않는다.
- ★ 그래서 이 사고는 **다시 컴파일해도(1번), 안 해도(2번)** 같다.

### 3. ★ `A [12, 34]` · `B [k1=1, k2=2]` · `C 8` · `D 0 …`·`D 1 …` · `E 3` — `_` 칸은 **호출조차 없다**

**출력**

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

```text
===== javap -c -p o30f/DsformsKt.class | grep -E 'Method Pt\.(component|get)' =====
     121: invokevirtual #59                 // Method Pt.component1:()I
     128: invokevirtual #62                 // Method Pt.component2:()I
     398: invokevirtual #62                 // Method Pt.component2:()I
      13: invokevirtual #220                // Method Pt.getX:()I
      17: invokevirtual #220                // Method Pt.getX:()I
(exit 0)
```

**왜 그런가**

- ★★ `C` 줄(398번 오프셋)에는 **`Pt.component2` 하나뿐**이다 — 문서가 말하는 「건너뛴 칸의 `componentN` 은 호출되지 않는다」가 바이트코드로 보인다.
- `{ (a, b) -> }` 는 **매개변수 하나를 분해**(121·128번의 `component1`·`component2`), `{ a, b -> }` 는 **매개변수 둘**(`Pt.getX` 두 번)이다.

### 4. ★★ 셋 다 막힌다 — 5번째 줄은 「두 개짜리를 한 개짜리 자리에」, 6번째 줄은 그 반대, 7번째 줄은 `component3()` 가 없다

**출력**

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

**왜 그런가**

- ★★★ **괄호 한 쌍이 매개변수 개수를 바꾼다.** 5번째 줄의 에러 둘째 줄이 「`actual type is '(Pt, ???) -> …', but '(Pt) -> …' was expected`」, 6번째 줄이 「`expected '(Pt, Pt) -> Int', actual '(Pt) -> Int'`」 — 정확히 **거울상**이다.
- ★ 5번째 줄은 에러가 **넷**으로 번졌다 — `b` 의 타입을 못 정하고, 그 여파로 `a + b` 를 `Pt.plus` 로 찾다가 「`unresolved reference 'plus' for operator '+'`」까지 간다.
- 7번째 줄 — 컴파일러가 **없는 번호의 이름**(`component3()`)을 댄다.

### 5. ★ `regok.kt` 는 통과해 `A 3 9` · `regbad.kt` 는 「`'operator' modifier is required`」

**출력**

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

**왜 그런가**

- ★★ 분해의 규약은 「**`operator fun componentN()` 이 있다**」 하나다 — `data class` 일 필요는 없다.
- ★ 이름만 맞는 `component1` 은 **규약 참가가 아니다.** 에러가 분해 자리(6번째 줄 10칸)를 가리키며 **정의 쪽의 누락**을 말한다.

### 6. ★★★ 경고 모드는 **경고 두 줄 + 여전히 뒤바뀜** · 완전 모드는 **맞는 값** · 2.5 흉내는 **뒤바뀜 그대로** · 새 문법은 「2.5 부터」

**출력**

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

```text
===== kotlinc -language-version 2.5 person2.kt readp.kt -d o30e =====
warning: language version 2.5 is experimental, there are no backwards compatibility guarantees for new language and library features. Use the stable version 2.4 instead.
(exit 0)
===== java -cp o30e:kotlin-stdlib.jar ReadpKt =====
A Lovelace Ada
B Ada Lovelace
(exit 0)
```

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

**왜 그런가**

- ★★★ `name-mismatch` 는 **1번의 사고를 처음으로 말해 준다**(「`variable name 'first' differs from accessed property name 'last'.`」). 그러나 `exit 0` — **막지 않는다.** 경고의 둘째 문장이 「이 문법은 앞으로 **이름 기반**이 되고 **뜻이 바뀐다**」고 예고한다.
- ★★★ `complete` 는 짧은 꼴을 **이름으로 읽게** 한다 — 바이트코드가 `component1`/`component2` 대신 **`getFirst`/`getLast`** 를 부른다.
- ★★ `-language-version 2.5` 는 실험 경고와 함께 통과하지만 **여전히 위치 기반**이다.
- ★★ 새 문법은 「`only available since language version 2.5`」 — 컴파일러가 **판 경계를 스스로** 말한다. `only-syntax` 로는 **대괄호가 위치**(`A Lovelace Ada`), **`(val f = first)` 가 이름**(`B Ada Lovelace`)이다.
- ★ 모두 **실험 플래그 뒤**다. `-language-version 2.5` 는 **2.4.20 이 흉내 낸 앞 판**이지 진짜 2.5 컴파일러가 아니다.

### 7. 판 1 은 `Field first`, 판 2 는 `Field last` — 번호는 **언어 규칙**, `getfield` 로 내리는 것은 **구현**

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

- ★★ 메서드 이름·서명(`component1()`·`String`)은 같고 **읽는 필드만** 다르다 — 2번의 링크가 되는 이유가 이것이다.
- ★ 「주 생성자 선언 순서대로 1, 2, …」는 **언어**가 정한다. 그 메서드가 `getfield` 한 번이라는 것은 **JVM 백엔드**의 모양이다.
- 그 블록의 소스는 1번의 `person1.kt`·`person2.kt` 다.

### 8. 표준 라이브러리의 **`inline operator` 확장**이 규약을 붙였다 — 바이트코드에는 **`getKey`/`getValue`** 만 남는다

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

- ★★ `Maps.kt` 312·325번 줄 — **`public inline operator fun <K, V> Map.Entry<K, V>.component1(): K = key`**. 남의 타입(Java 인터페이스)에 규약을 다는 방법이 **확장 함수**다([13번 주제](../13-extension-functions-and-properties/)).
- ★ `inline` 이라 호출 자리에 `Map$Entry.getKey` 가 **바로 박혔다** — `component1` 이라는 이름은 바이트코드에 없다.

### 9. `javac` 도 **경고 0줄 · 값이 뒤바뀐다** — 읽는 쪽은 같고, 생성 쪽은 Java 가 더 약하다

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

- ★★★ record 패턴의 `var first` 도 **패턴 변수 이름일 뿐**이다 — 컴포넌트 이름과 대조하지 않는다. Java record 패턴은 **위치 기반**이다([Java 24번](../../../java/syntax/24-record-patterns/)).
- ★★ 생성 쪽 — Kotlin 은 **이름 붙인 인자**(`P(first = …, last = …)`)가 있어 순서를 바꿔도 **같은 객체**가 된다. Java 는 `new JP(…)` 가 위치뿐이라 `RecB` 에서 **손으로 뒤집어** 맞췄다. 사고가 **읽는 쪽에만** 남는 것은 두 언어가 같다.

### 10. 타입이 **같으면** 가를 근거가 없다 — **달라도** 변수를 그 타입으로 **쓰는 줄**이 있어야 잡힌다 · 진단 창은 원리상 이 사고를 못 본다

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

- ★★★ 분해한 변수에는 **타입을 적지 않았으므로** 선언이 바뀌면 **추론이 따라 바뀐다.** `String`/`Int` 로 바꿔도 `readm.kt`(문자열 템플릿만 씀)는 **조용히 `A 36 Ada`** 를 찍었다.
- ★★ `readm2.kt` 는 `name.uppercase()` 에서야 막혔고, `age + 1` 은 **`String + Int`** 로 풀려 **통과했다** — 에러는 **한 줄뿐**이다.
- ★ 「잴 것이 없다」(제4의 상태) — 두 필드가 같은 타입이면 판 2 의 소스는 **타입 검사가 볼 차이를 하나도 갖지 않는다.** 「봤더니 조용했다」로 적으면 **다른 설정이면 보일 수도 있다**는 뜻이 되는데, 기본 진단은 **원리상** 못 본다. 그 질문은 **다른 창**(`name-mismatch` 경고)으로 물어야 답이 나온다(제5의 상태 — 6번).

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
| **없다** — 해시코드·주소·시간을 찍지 않았다 | 출력 · `javap` 출력(명령·서명·필드 이름) |
| | 컴파일 진단의 **문구·`파일:줄:칸`·캐럿** · `-X` 도움말 |
| | 모든 **종료 코드** |

> 근거 — 캡처 스크립트를 처음부터 다시 돌려 **블록 전체를 바이트 단위로 대조**했다.
>
> 실측 — `capture.sh blocks` 와 `capture.sh blocks-recheck` 를 처음부터 따로 돌려 `normalize-shaky.py` 로 대조했다 —\
> **블록 104개 · 동일 104 · 흔들린 칸 0 · ★고칠 것 0**(30\~33 네 주제를 한 캡처로 받았다). `diff -rq` 도 차이 0 이다.\
> ★ **정규화 규칙은 하나도 안 썼다** — 기본 넷(주소·PID·스레드 id·시간)에 걸리는 칸이 애초에 없었다.

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `person1.kt` · `person2.kt` · `readp.kt` | ★★★ **두 판 나란히** — 에러 0, 뒤바뀜 · 필드 · 호출 | `kotlinc` → `java`(두 판) · `javap -c -p`(필터) |
| 같은 세 파일 | ★★ **바이너리** — 호출부를 다시 컴파일하지 않음 | `kotlinc` 세 번 → `java` 두 판 |
| `mix1.kt` · `mix2.kt` · `readm.kt` · `readm2.kt` | 타입이 **다를 때** | `kotlinc` 네 판(실패 1벌) → `java` |
| 같은 세 파일 + 플래그 | ★★★ **이름 기반 분해** — `name-mismatch` · `complete` · `-language-version 2.5` | `kotlinc -X`(필터) · `kotlinc` 세 판 → `java` · `javap`(필터) |
| `newform.kt` | 새 문법의 **판 경계** | `kotlinc` 두 판(실패 1벌) → `java` |
| `dsforms.kt` · `dsbad.kt` | 람다 괄호 · `_` · 번호 부족 | `kotlinc`(실패 1벌) → `java` · `javap`(필터) |
| `regok.kt` · `regbad.kt` | 일반 클래스 · `operator` 누락 | `kotlinc`(실패 1벌) → `java` |
| `entry30.kt` | `Map.Entry` 의 확장 `componentN` | `kotlinc` → `java` · `unzip`(필터) · `javap`(필터) |
| `RecA.java` · `RecB.java` · `ReadJ.java` | Java record 패턴의 **같은 실험** | `javac` 두 판 → `java` |
| `form30.kt` | 형태 한 벌 | `kotlinc` → `java` |

**구현 의존 항목** — `componentN` 이 `getfield` 한 번인 것, `Map.Entry` 분해가 인라인되는 것, 진단 문구, ★ **`-Xname-based-destructuring` 의 모드·문구와 「2.5 부터」** 는 이 컴파일러·판의 산출물이다.\
반면 **「짧은 꼴은 `componentN` 을 순서대로 부른다」「번호는 주 생성자 순서」「`_` 는 호출하지 않는다」「`operator` 가 필요하다」** 는 **언어의 계약**이다.

**★ 던져 봤더니 예상과 달랐던 것 — 세 건**

1. ★★★ **이 판에 이름 기반 분해가 이미 들어와 있었다**(6번). README 는 「뺀 것」으로 적어 두었는데, `kotlinc -X` 가 세 모드를 보여 주었고 **`complete` 모드는 1번의 사고를 실제로 고쳤다**(`getFirst`/`getLast` 호출).
2. ★★ **`-language-version 2.5` 가 받아졌다.** 앞 판을 흉내 내는 옵션이 **뒤 판**도 흉내 낸다 — 다만 그 판에서도 짧은 꼴은 **아직 위치 기반**이었다.
3. ★★ **타입을 `String`/`Int` 로 갈라도 잡히지 않는 줄이 있었다**(10번). 「타입이 다르면 컴파일러가 잡는다」는 **쓰는 줄의 연산**에 달렸고, `age + 1` 은 `String.plus` 로 **통과**했다.
