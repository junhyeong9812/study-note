# kotlin/syntax/48 — 문자열 API — `split`/`trim*`/`pad*`/`Regex` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Strings](https://kotlinlang.org/docs/strings.html) · [kotlin.text 패키지 API](https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.text/)(`split`·`trim`·`padStart`·`Regex`) — 이 문서는 그 목록을 따르되, 문장은 인용하지 않고 **이 판의 stdlib 소스 jar**(`kotlin-stdlib-sources.jar` 2.4.20)의 KDoc 과 구현, 그리고 **JDK 21.0.5 의 `src.zip`**(`String.java`)의 javadoc 을 근거로 삼는다((3)(6)).
> **실행 검증** — 이 문서의 모든 출력·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javac`·`java`·`javap` 에서 실제로 얻었다.\
> `kotlinc` 7회 · `javac` 3회 · `java` 8회 · `javap` 3회 · stdlib 소스 jar 에서 발췌 6곳 · JDK `src.zip` 에서 2곳.\
> ★★ 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적지 않았다. **「갈린 행 N / M」은 격자 프로그램이 스스로 센 것**이다.
> ★★ 입력에 공백·제어문자·전각 공백이 들어가므로 격자는 **보이는 표기**로 찍는다 — 따옴표 안에서 `!`\~`~`(0x21\~0x7E) 밖의 글자는 전부 `<U+XXXX>`, `trim` 격자는 **코드포인트 덤프**(`U+0061` 꼴)다. 이 문서의 어떤 블록에도 **U+3000·U+00A0 글자 자체는 없다.**
> **버전** — `split`·`trim`·`padStart`·`padEnd`·`Regex` 는 **1.0** — 이 판의 소스에서 선언 위에 `@SinceKotlin` 이 **없다**(확인만 했고 발췌하지 않았다). Java `String.strip()` 은 **Java 11**.
> **경계** — ★★★ **문자열 매칭 알고리즘**(KMP·보이어-무어·정규식 엔진의 동작)은 [`cs/algorithm/25-string-matching/`](../../../../../algorithm/25-string-matching/) 이 정본이다 — 여기는 **stdlib 함수의 경계 동작**(빈 조각 · 공백의 정의 · 전체 일치 대 부분 일치)만 본다.\
> **Java 쪽 `split` 함정**(`"a,b,,c,,".split(",")` · `split(".")`)은 [Java 35번](../../../java/syntax/35-string/)이, **정규식 문법**은 [Java 37번](../../../java/syntax/37-regex/)이 정본이다 — 여기서는 **같은 입력을 Kotlin 과 한 쌍으로** 던진다.\
> **`$` 가 템플릿이 되는 조건**과 `trimIndent`/`trimMargin` 은 [02번 주제](../02-string-templates-and-raw-strings/) (1)(6)이 정본이다 — 여기서는 `Regex.replace` 의 그룹 참조와 부딪히는 자리만 본다. 확장 함수가 **정적 메서드**로 풀린다는 논지는 [`../../언어-특성/README.md`](../../언어-특성/README.md) §7 이다.
> 이 본문은 Claude 작성이다(원고 없음).

★★★ **본체는 첫째 창이다** — 「**Java 와 갈리는 격자 — 입력 다섯 × 쪼개는 꼴 다섯(Kotlin `split(d)` · Java `split(d)` · Kotlin `split(Regex(d))` · Kotlin `split(d, limit = 2)` · Java `split(d, -1)`) → 원소 수 · 원소**」. 두 언어 모두 `split` 이라는 **같은 이름**이 컴파일되고 에러도 없다 — 원소 수가 갈리는지는 **같은 입력을 양쪽에 넣어 봐야** 보인다.

## 이 주제가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **언어 보장 / API 계약** | 서명·KDoc·javadoc 이 약속한 것 | ★★★ Kotlin `split` KDoc 「**the resulting list will end with an empty string**」 · Java `split` javadoc 「**Trailing empty strings are therefore not included**」 · Java `trim` 「**less than or equal to `'U+0020'`**」 · `Regex.matches` 「**matches the entire [input]**」 · `replace` KDoc 의 **`${name}`·`$index`** |
| **구현(stdlib)** | 이 판의 stdlib 가 실제로 하는 것 | ★★ `Char.isWhitespace()` = **`Character.isWhitespace(c) \|\| Character.isSpaceChar(c)`** · `String.trim()` 이 **`@InlineOnly`**(클래스 파일에 없다) · 확장 함수들이 **`kotlin.text.StringsKt`** 의 정적 메서드 · 예외 문장 `Desired length -1 is less than zero.` |
| **이 판의 관찰** | 이번에 본 것 | 격자 값 · `javap` 에 박힌 `StringsKt.split$default` |

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
| **흔들린다** | (이 주제에는 없다) | 해시코드·주소·시간을 찍지 않았다 |
| 안 흔들린다 | `split` 격자 5행 × 5열 · `trim` 격자 7행 · 갈린 행 수 | 결정적 문자열 함수 |
| 안 흔들린다 | 정규식 출력 · `pad` 출력 · 예외 문장 | 같은 JDK·stdlib 이면 같다 |
| 안 흔들린다 | stdlib·JDK 소스 발췌(줄 번호째) · `javap` 의 명령·상수 풀 번호 · 종료 코드 | jar·`src.zip`·컴파일러가 같으면 같다 |

★ 근거 — 캡처 스크립트를 처음부터 두 번 돌려 **블록 전체를 대조**했다(수치는 3-answer 의 「실행 검증」).

## 한눈에 — 쉽게 말하면

**Kotlin 의 문자열 함수는 Java `String` 에 「덧붙인 도구 상자」다 — 같은 이름의 도구가 양쪽에 있는데, 날의 모양이 다르다.** `split` 이라는 가위로 `"a,b,,"` 를 자르면 Kotlin 가위는 **끝의 빈 조각 둘을 남기고**, Java 가위는 **털어 버린다.** `"."` 를 주면 Kotlin 은 **점 글자**로 자르고, Java 는 「**아무 글자나**」라는 정규식으로 읽어 전부 잘라 **빈 배열**을 준다.
★ `trim` 도 「공백」의 정의가 다르다 — Java `trim` 은 **코드가 `0x20` 이하인 글자**, Kotlin `trim` 은 **유니코드의 공백**이다. 그래서 전각 공백(U+3000)은 Kotlin 만 깎고, 제어문자 U+0001 은 Java 만 깎는다.

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 끝 빈 조각을 남기는 가위 | Kotlin `split(",")` → `4 ["a", "b", "", ""]` | (1) ★ |
| 끝 빈 조각을 터는 가위 | Java `split(",")` → `2 ["a", "b"]` · `","` → **`0 []`** | (1) ★ |
| 점을 점으로 읽는 가위 | Kotlin `split(".")` → `[a, b]` | (2) ★ |
| 점을 「아무 글자」로 읽는 가위 | Java `split(".")` → **`0 []`** | (2) ★ |
| 공백 목록이 다른 두 빗자루 | Kotlin `trim` = 유니코드 공백 · Java `trim` = `<= 0x20` | (3) ★ |
| 도구 상자 = 정적 메서드 모음 | `"a".split(",")` → `StringsKt.split$default(…)` | (6) |

```text
   "a,b,,".split(",")

   Kotlin        [ "a" | "b" | "" | "" ]    4개   ← 구분자 뒤마다 조각 하나
   Java          [ "a" | "b" ]              2개   ← 끝의 빈 조각을 지운다(limit 0)
   Java  (-1)    [ "a" | "b" | "" | "" ]    4개   ← Kotlin 과 같아진다

   "a.b".split(".")
   Kotlin        [ "a" | "b" ]              "." 는 글자
   Java          [ ]                        "." 는 정규식 — 세 글자 전부가 구분자, 남은 빈 조각은 전부 끝 조각
```

## 이 주제가 답하려는 질문

1. 같은 이름 `split`·`trim` 이 **Java 와 어디서 갈리나** — 끝 빈 조각 · 구분자가 글자인가 정규식인가 · 공백의 정의.
2. `Regex` 의 **전체 일치와 부분 일치**는 어느 함수인가 — 그리고 치환 문자열의 `$` 가 Kotlin 템플릿과 **어디서 부딪히나.**
3. 이 확장 함수들은 **Java 에서 어떤 모양으로** 보이나.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **Java 대비 격자(실행)** | 입력 × 쪼개는 꼴 → 원소 수 · 원소((1)) | ★ **본체 창** — Java 열은 `javac` 로 만든 `JSplit` 이 **진짜 `String.split`** 을 부른다 |
| ★★ **`trim` 코드포인트 격자** | 앞뒤에 둔 글자 × 세 `trim` → 남은 코드포인트((3)) | — |
| ★★ **한 쌍 실행** | `split(".")` Java 대 Kotlin((2)) | [Java 35번](../../../java/syntax/35-string/)과 같은 입력 |
| ★★ **stdlib·JDK 소스 발췌** | 그 동작이 **KDoc/javadoc 계약**인가((1)(3)(4)) | — |
| ★★ **`javap`** | 확장 함수가 **`StringsKt`** 의 정적 메서드인 것 · Java 에서 부르는 모양((6)) | [26번 주제](../26-value-class-and-boxing/)·[39번 주제](../39-java-interop-annotations/)와 같은 창 |
| **인용 — 다시 안 잰다** | `trimIndent`/`trimMargin` 의 기준 · `$` 가 글자인 조건 | [02번 주제](../02-string-templates-and-raw-strings/) (1)(6) |
| **부적용 — 실행 시간** | 「`Regex` 를 미리 만들면 빠르다」·「Kotlin `split` 이 빠르다」는 **재지 않았다** | — |

### (1) ★★★ Java 와 갈리는 격자 — `split`

**언제 쓰나** — CSV 한 줄·경로·키 목록을 쪼갤 때. 특히 **Java 코드를 옮길 때.**

방법 — `JSplit.java` 는 `String.split(d)`·`split(d, limit)` 을 **그대로 부르는** Java 클래스다. Kotlin 격자가 같은 입력으로 Kotlin 꼴 셋과 Java 꼴 둘을 부르고, 원소 수와 원소를 **보이는 표기**로 찍는다. 마지막 두 줄은 **Kotlin `split(d)` 가 Java 두 꼴과 원소째 다른 행**을 센다.

```java
// JSplit.java
public class JSplit {
    public static String[] split(String s, String d) { return s.split(d); }
    public static String[] split(String s, String d, int limit) { return s.split(d, limit); }
    public static String trim(String s) { return s.trim(); }
    public static String strip(String s) { return s.strip(); }
    public static boolean isWhitespace(char c) { return Character.isWhitespace(c); }
}
```

```kotlin
// grid48.kt
fun show(s: String): String = buildString {
    append('"')
    for (c in s) {
        if (c.code in 0x21..0x7e && c != '"') append(c)
        else append("<U+" + c.code.toString(16).uppercase().padStart(4, '0') + ">")
    }
    append('"')
}

fun list(xs: List<String>): String = "${xs.size} " + xs.joinToString(", ", "[", "]") { show(it) }

val rows = listOf(
    "a,b,," to ",",
    ",a" to ",",
    "" to ",",
    "," to ",",
    "a  b" to " ",
)

fun main() {
    println(listOf("input", "delim", "kt split(d)", "java split(d)", "kt split(Regex(d))", "kt split(d, limit=2)", "java split(d, -1)").joinToString("\t"))
    var differ = 0
    var differNeg = 0
    for ((s, d) in rows) {
        val kt = s.split(d)
        val java = JSplit.split(s, d).toList()
        val javaNeg = JSplit.split(s, d, -1).toList()
        val row = listOf(show(s), show(d), list(kt), list(java), list(s.split(Regex(d))), list(s.split(d, limit = 2)), list(javaNeg))
        check(row.size == 7)
        println(row.joinToString("\t"))
        if (kt != javaNeg) differNeg++
        if (kt != java) differ++
    }
    println("rows where kt split(d) and java split(d, -1) differ: $differNeg / ${rows.size}")
    println("rows where kt split(d) and java split(d) differ: $differ / ${rows.size}")
}
```

```text
===== javac -d o48j JSplit.java =====
(exit 0)
===== kotlinc -cp o48j grid48.kt -d o48g =====
(exit 0)
```

```text
===== java -cp o48g:o48j:kotlin-stdlib.jar Grid48Kt =====
input	delim	kt split(d)	java split(d)	kt split(Regex(d))	kt split(d, limit=2)	java split(d, -1)
"a,b,,"	","	4 ["a", "b", "", ""]	2 ["a", "b"]	4 ["a", "b", "", ""]	2 ["a", "b,,"]	4 ["a", "b", "", ""]
",a"	","	2 ["", "a"]	2 ["", "a"]	2 ["", "a"]	2 ["", "a"]	2 ["", "a"]
""	","	1 [""]	1 [""]	1 [""]	1 [""]	1 [""]
","	","	2 ["", ""]	0 []	2 ["", ""]	2 ["", ""]	2 ["", ""]
"a<U+0020><U+0020>b"	"<U+0020>"	3 ["a", "", "b"]	3 ["a", "", "b"]	3 ["a", "", "b"]	2 ["a", "<U+0020>b"]	3 ["a", "", "b"]
rows where kt split(d) and java split(d, -1) differ: 0 / 5
rows where kt split(d) and java split(d) differ: 2 / 5
(exit 0)
```

- ★★★ **Java `split(d)` 와 갈린 행은 5행 중 2행** — `"a,b,,"`(Kotlin **4개** · Java **2개**)와 `","`(Kotlin **`["", ""]`** · Java **`0 []`**). Java 는 **끝의 빈 조각을 지우고**, `","` 처럼 조각이 **전부 빈 것이면 배열이 통째로 빈다.**
- ★★★ **Java `split(d, -1)` 과는 한 행도 안 갈린다(0 / 5)** — Kotlin `split` 은 Java 의 `-1`(끝 조각을 지우지 않는 꼴)과 **같은 원소**를 준다.
- ★★ **`""` 는 둘 다 `1 [""]`** — 빈 문자열을 쪼개면 **빈 조각 하나**다(0개가 아니다).
- ★★ **`",a"` 는 둘 다 `["", "a"]`** — Java 도 **앞의** 빈 조각은 지우지 않는다. 지우는 것은 **끝**뿐이다.
- ★ **`limit = 2` 는 「조각을 최대 둘로」** — `"a,b,,"` 는 `["a", "b,,"]`, 나머지는 **통째로 마지막 조각**에 남는다. `"a<U+0020><U+0020>b"` 를 `" "` 로 쪼개면 가운데 빈 조각이 **양쪽 다** 남는다.
- ★ Kotlin `split(Regex(d))` 도 Kotlin `split(d)` 와 같은 원소다 — **정규식을 주어도 끝 조각을 지우지 않는다.** 갈림은 「글자냐 정규식이냐」가 아니라 **Java `split` 의 limit 0 규칙**에서 나온다.

```text
===== unzip -o -q kotlin-stdlib-sources.jar commonMain/kotlin/collections/Maps.kt commonMain/kotlin/collections/MapWithDefault.kt jvmMain/kotlin/collections/MapsJVM.kt jvmMain/kotlin/Collections.kt commonMain/generated/_Sequences.kt commonMain/generated/_Collections.kt commonMain/kotlin/collections/Sequence.kt commonMain/kotlin/collections/Sequences.kt jvmMain/kotlin/collections/SequencesJVM.kt commonMain/kotlin/text/Strings.kt jvmMain/kotlin/text/CharJVM.kt jvmMain/kotlin/text/regex/Regex.kt commonMain/kotlin/util/Result.kt commonMain/kotlin/collections/SequenceBuilder.kt =====
(exit 0)
```

```text
===== sed -n '1408,1414p;1426p' commonMain/kotlin/text/Strings.kt =====
 *
 * The last element of the resulting list corresponds to a subsequence starting right after the last
 * delimiter occurrence (or at the beginning of this char sequence if there were no such occurrences)
 * and ending at the end of this char sequence. That implies that if this char sequence does not
 * contain [delimiters], the resulting list will contain a single element corresponding to
 * the whole char sequence. It also implies that for char sequences ending with one of [delimiters],
 * the resulting list will end with an empty string.
public fun CharSequence.split(vararg delimiters: String, ignoreCase: Boolean = false, limit: Int = 0): List<String> {
(exit 0)
===== sed -n '175p;181p' commonMain/kotlin/text/Strings.kt =====
public fun CharSequence.trim(): CharSequence = trim(Char::isWhitespace)
public inline fun String.trim(): String = (this as CharSequence).trim().toString()
(exit 0)
===== sed -n '103p' jvmMain/kotlin/text/CharJVM.kt =====
public actual fun Char.isWhitespace(): Boolean = Character.isWhitespace(this) || Character.isSpaceChar(this)
(exit 0)
===== sed -n '215,219p' commonMain/kotlin/text/Strings.kt =====
public fun CharSequence.padStart(length: Int, padChar: Char = ' '): CharSequence {
    if (length < 0)
        throw IllegalArgumentException("Desired length $length is less than zero.")
    if (length <= this.length)
        return this.subSequence(0, this.length)
(exit 0)
```

```text
===== unzip -o -q "$JAVA_HOME/lib/src.zip" java.base/java/lang/String.java =====
(exit 0)
===== sed -n '3408,3411p;3446p' java.base/java/lang/String.java =====
     * <p> This method works as if by invoking the two-argument {@link
     * #split(String, int) split} method with the given expression and a limit
     * argument of zero.  Trailing empty strings are therefore not included in
     * the resulting array.
    public String[] split(String regex) {
(exit 0)
===== sed -n '3747,3750p;3785,3787p' java.base/java/lang/String.java =====
     * Returns a string whose value is this string, with all leading
     * and trailing space removed, where space is defined
     * as any character whose codepoint is less than or equal to
     * {@code 'U+0020'} (the space character).
     * Returns a string whose value is this string, with all leading
     * and trailing {@linkplain Character#isWhitespace(int) white space}
     * removed.
(exit 0)
```

- ★★★ **두 동작이 전부 계약이다** — Kotlin KDoc 「`for char sequences ending with one of [delimiters], the resulting list will end with an empty string`」, Java javadoc 「`Trailing empty strings are therefore not included in the resulting array.`」. **둘 다 약속대로 하고 있고, 약속이 반대다.**
- ★ Kotlin `split(vararg delimiters: String, …)` 의 구분자는 **`String`** — 정규식이 아니다. Java `split(String regex)` 는 인자 이름부터 `regex` 다.

### (2) ★★ `split(".")` — 가장 흔한 사고의 한 쌍

```java
// Dot48.java
import java.util.Arrays;

public class Dot48 {
    public static void main(String[] args) {
        String[] a = "a.b".split(".");
        String[] b = "a.b".split("\\.");
        System.out.println("java split(\".\")    " + a.length + " " + Arrays.toString(a));
        System.out.println("java split(\"\\\\.\")  " + b.length + " " + Arrays.toString(b));
    }
}
```

```text
===== javac -d o48d Dot48.java =====
(exit 0)
===== java -cp o48d Dot48 =====
java split(".")    0 []
java split("\\.")  2 [a, b]
(exit 0)
```

```kotlin
// dot48.kt
fun main() {
    val a = "a.b".split(".")
    val b = "a.b".split(Regex("."))
    val c = "a.b".split(Regex("\\."))
    println("kt split(\".\")         ${a.size} $a")
    println("kt split(Regex(\".\"))  ${b.size} $b")
    println("kt split(Regex(\"\\\\.\")) ${c.size} $c")
}
```

```text
===== kotlinc dot48.kt -d o48k =====
(exit 0)
===== java -cp o48k:kotlin-stdlib.jar Dot48Kt =====
kt split(".")         2 [a, b]
kt split(Regex("."))  4 [, , , ]
kt split(Regex("\\.")) 2 [a, b]
(exit 0)
```

- ★★★ **Java `"a.b".split(".")` 은 `0 []`** — `.` 이 「아무 글자」라 **세 글자 전부가 구분자**가 되고, 조각은 전부 빈 문자열이라 **끝 조각 규칙이 전부 지운다.** 점으로 자르려면 `"\\."`.
- ★★★ **Kotlin `"a.b".split(".")` 은 `[a, b]`** — 구분자가 **글자 그대로**다. 같은 코드를 Java 에서 Kotlin 으로 옮기면 **조용히 고쳐지고**, 반대로 옮기면 **조용히 깨진다.**
- ★★ **Kotlin `split(Regex("."))` 는 `4 [, , , ]`** — 정규식으로 주면 Java 와 같은 쪼개기를 하되 **끝 조각을 남겨** 빈 문자열 넷이다. 「0 개」가 아니다.

### (3) ★★ `trim` — 「공백」의 정의가 셋

**언제 쓰나** — 사용자 입력·복사해 붙인 문자열·일본어/한국어 문서(전각 공백)를 다듬을 때.

방법 — 글자 `c` 하나를 `"${c}a$c"` 의 **앞뒤**에 두고 Kotlin `trim()` · Java `trim()` · Java `strip()` 을 부른다. 결과는 **코드포인트 덤프**로 찍는다(`U+0061` 만 남으면 양쪽을 다 깎은 것). `isWhitespace` 두 열은 그 글자에 대한 판정이다.

```kotlin
// trim48.kt
fun dump(s: String): String = if (s.isEmpty()) "(empty)" else s.map { "U+" + it.code.toString(16).uppercase().padStart(4, '0') }.joinToString(" ")

val pads = listOf(0x20, 0x09, 0x3000, 0x00A0, 0x2003, 0x0001, 0x200B)

fun main() {
    println(listOf("pad", "kt isWhitespace", "java isWhitespace", "kt trim()", "java trim()", "java strip()").joinToString("\t"))
    var differ = 0
    var differStrip = 0
    for (code in pads) {
        val c = Char(code)
        val s = "${c}a$c"
        val kt = s.trim()
        val jt = JSplit.trim(s)
        val js = JSplit.strip(s)
        val row = listOf(dump(c.toString()), "${c.isWhitespace()}", "${JSplit.isWhitespace(c)}", dump(kt), dump(jt), dump(js))
        check(row.size == 6)
        println(row.joinToString("\t"))
        if (kt != js) differStrip++
        if (kt != jt) differ++
    }
    println("rows where kt trim() and java strip() differ: $differStrip / ${pads.size}")
    println("rows where kt trim() and java trim() differ: $differ / ${pads.size}")
}
```

```text
===== kotlinc -cp o48j trim48.kt -d o48t =====
(exit 0)
===== java -cp o48t:o48j:kotlin-stdlib.jar Trim48Kt =====
pad	kt isWhitespace	java isWhitespace	kt trim()	java trim()	java strip()
U+0020	true	true	U+0061	U+0061	U+0061
U+0009	true	true	U+0061	U+0061	U+0061
U+3000	true	true	U+0061	U+3000 U+0061 U+3000	U+0061
U+00A0	true	false	U+0061	U+00A0 U+0061 U+00A0	U+00A0 U+0061 U+00A0
U+2003	true	true	U+0061	U+2003 U+0061 U+2003	U+0061
U+0001	false	false	U+0001 U+0061 U+0001	U+0061	U+0001 U+0061 U+0001
U+200B	false	false	U+200B U+0061 U+200B	U+200B U+0061 U+200B	U+200B U+0061 U+200B
rows where kt trim() and java strip() differ: 1 / 7
rows where kt trim() and java trim() differ: 4 / 7
(exit 0)
```

- ★★★ **Kotlin `trim()` 과 Java `trim()` 은 7행 중 4행에서 갈린다** — U+3000(전각 공백) · U+00A0(줄바꿈 없는 공백) · U+2003(em 공백)은 **Kotlin 만** 깎고, U+0001(제어문자)은 **Java 만** 깎는다.
- ★★★ **Java `strip()` 과는 1행만 갈린다 — U+00A0** — `strip()` 은 `Character.isWhitespace` 를 쓰는데 그 판정이 U+00A0 에서 `false` 다(「줄바꿈 없는」 공백은 제외). Kotlin 은 거기에 **`isSpaceChar`** 를 더해 U+00A0 까지 깎는다.
- ★★ **U+200B(폭 없는 공백)는 셋 다 안 깎는다** — 이름에 「공백」이 있어도 유니코드 분류가 공백이 아니다(`isWhitespace` 둘 다 `false`).
- ★ 공백 U+0020 과 탭 U+0009 는 **셋 다** 깎는다 — 갈림은 ASCII 밖과 제어문자에서만 난다.

(1)의 두 발췌(stdlib · JDK `src.zip`)에 Kotlin 쪽과 Java 쪽 정의가 있다.

- ★★★ **Java `trim` 의 공백은 javadoc 계약** — 「`any character whose codepoint is less than or equal to {@code 'U+0020'}`」. 그래서 **제어문자 U+0001 도 공백**이다. `strip` 은 「`{@linkplain Character#isWhitespace(int) white space}`」.
- ★★ **Kotlin `trim` 은 `Char::isWhitespace`** 이고, JVM 판 `isWhitespace` 는 **`Character.isWhitespace(this) || Character.isSpaceChar(this)`** — 합집합이다. 그 한 줄은 **JVM 구현**이다(KDoc 은 「`Returns true if the character is whitespace.`」까지만 말한다).
- ★ `String.trim()` 은 **`@InlineOnly`** — `(this as CharSequence).trim().toString()` 로 풀린다. 그래서 (6)의 `javap` 에 `trim(String)` 이 아니라 **`trim(CharSequence)`** 가 박힌다.

### (4) ★★ `Regex` — 전체 일치 대 부분 일치 · `$` 그룹 참조

```kotlin
// regex48.kt
fun main() {
    val digits = Regex("[0-9]+")
    val s = "ab12cd345"
    println("1 matches(s)          ${digits.matches(s)}")
    println("2 containsMatchIn(s)  ${digits.containsMatchIn(s)}")
    println("3 find(s)             ${digits.find(s)?.value} ${digits.find(s)?.range}")
    println("4 findAll(s)          ${digits.findAll(s).map { it.value }.toList()}")
    println("5 matchEntire(s)      ${digits.matchEntire(s)}")
    println("6 matches(\"345\")      ${digits.matches("345")}")

    val mail = Regex("(\\w+)@(\\w+)")
    println("7 ${mail.replace("kim@host", "$2:$1")}")
    println("8 ${mail.replace("kim@host", "\$2:\$1")}")
    val user = "lee"
    val named = Regex("(?<user>\\w+)@(?<host>\\w+)")
    println("9 ${named.replace("kim@host", "\${host}:\${user}")}")
    println("10 ${named.replace("kim@host", "\${host}:${user}")}")
    println("11 ${mail.replace("kim@host") { it.groupValues[2] + ":" + it.groupValues[1] }}")
    println("12 ${"a.b.c".replace(".", "-")}  ${"a.b.c".replace(Regex("."), "-")}")
}
```

```text
===== kotlinc regex48.kt -d o48r =====
(exit 0)
===== java -cp o48r:kotlin-stdlib.jar Regex48Kt =====
1 matches(s)          false
2 containsMatchIn(s)  true
3 find(s)             12 2..3
4 findAll(s)          [12, 345]
5 matchEntire(s)      null
6 matches("345")      true
7 host:kim
8 host:kim
9 host:kim
10 host:lee
11 host:kim
12 a-b-c  -----
(exit 0)
```

- ★★★ **`matches` 는 전체 일치다** — `"ab12cd345"` 에 `[0-9]+` 는 `false`, `"345"` 는 `true`. 부분 일치는 **`containsMatchIn`**(`true`)·`find`(첫 일치 `12`, 범위 `2..3`)·`findAll`(`[12, 345]`). `matchEntire` 는 전체 일치가 아니면 **`null`**.
- ★★★ **`"$2:$1"` 은 그대로 그룹 참조가 된다**(`7`·`8` 이 같다) — `$` 뒤가 **숫자**면 Kotlin 템플릿이 아니다([02번 주제](../02-string-templates-and-raw-strings/) (1)). **`\$` 는 여기서 필요 없다.**
- ★★★ **부딪히는 것은 이름 있는 그룹 `${name}`** — `"\${host}:\${user}"`(`9`)는 `host:kim` 인데, `\` 를 하나 빠뜨린 `"\${host}:${user}"`(`10`)는 **`host:lee`** — 바깥의 `val user = "lee"` 가 **템플릿으로 먼저 끼어들었다.** 컴파일 에러도 경고도 없다.
- ★★ **람다를 받는 `replace`**(`11`)는 `$` 해석이 **아예 없다** — 그룹을 `groupValues` 로 꺼내 문자열을 직접 만든다.
- ★★ **`String.replace(".", "-")` 는 글자 그대로**(`a-b-c`) · `replace(Regex("."), "-")` 는 정규식(`-----`) — Java 의 `replace`(글자)·`replaceAll`(정규식) 두 이름이 Kotlin 에서는 **인자 타입**으로 갈린다.

```text
===== sed -n '107,111p' jvmMain/kotlin/text/regex/Regex.kt =====
    /** Indicates whether the regular expression matches the entire [input]. */
    public actual infix fun matches(input: CharSequence): Boolean = nativePattern.matcher(input).matches()

    /** Indicates whether the regular expression can find at least one match in the specified [input]. */
    public actual fun containsMatchIn(input: CharSequence): Boolean = nativePattern.matcher(input).find()
(exit 0)
===== sed -n '160,161p;168,169p;180p' jvmMain/kotlin/text/regex/Regex.kt =====
     * The replacement string may contain references to the captured groups during a match. Occurrences of `${name}` or `$index`
     * in the replacement string will be substituted with the subsequences corresponding to the captured groups with the specified name or index.
     * Backslash character '\' can be used to include the succeeding character as a literal in the replacement string, e.g, `\$` or `\\`.
     * [Regex.escapeReplacement] can be used if [replacement] have to be treated as a literal string.
    public actual fun replace(input: CharSequence, replacement: String): String = nativePattern.matcher(input).replaceAll(replacement)
(exit 0)
```

- ★★★ `matches` 의 KDoc 「`matches the entire [input]`」 · `containsMatchIn` 「`can find at least one match`」 — 구현도 각각 JDK `Matcher.matches()` 와 `find()` 다.
- ★★ `replace` 의 KDoc 이 **`${name}`·`$index`** 를 그룹 참조로 적고, 글자 `$` 는 **`\$`**(정규식 치환 문자열 안의 역슬래시)로 쓰라고 한다 — Kotlin 소스에서는 그 역슬래시도 이스케이프해야 하니 `"\\$"`, 또는 **`Regex.escapeReplacement`**.

### (5) ★ `padStart`·`padEnd` — 이미 길면 그대로

```kotlin
// pad48.kt
fun main() {
    println("1 [${"7".padStart(3, '0')}]")
    println("2 [${"12345".padStart(3, '0')}]")
    println("3 [${"ab".padEnd(5, '.')}]")
    println("4 [${"ab".padStart(4)}]")
    println("5 [${"%03d".format(7)}]")
    try {
        println("6 [${"ab".padStart(-1)}]")
    } catch (e: IllegalArgumentException) {
        println("6 ${e::class.simpleName}: ${e.message}")
    }
}
```

```text
===== kotlinc pad48.kt -d o48p =====
(exit 0)
===== java -cp o48p:kotlin-stdlib.jar Pad48Kt =====
1 [007]
2 [12345]
3 [ab...]
4 [  ab]
5 [007]
6 IllegalArgumentException: Desired length -1 is less than zero.
(exit 0)
```

- ★★ **`"12345".padStart(3, '0')` 는 `12345`** — 자르지 않는다. 「길이를 **최소** N 으로」이지 「정확히 N」이 아니다.
- ★ 음수 길이는 `IllegalArgumentException: Desired length -1 is less than zero.` — (1)의 stdlib 발췌에 그 `throw` 와 `length <= this.length` 면 **원본을 그대로** 돌려주는 줄이 있다.
- ★ Java 에는 `padStart` 가 없다 — 숫자는 `"%03d".format(7)`(`007`) 같은 서식 문자열로 한다.

### (6) ★★ 확장 함수는 `StringsKt` 의 정적 메서드 — Java 에서 부르면

```kotlin
// call48.kt
fun cut(s: String): List<String> = s.split(",")

fun pad(s: String): String = s.padStart(3, '0')

fun clean(s: String): String = s.trim()

fun main() {
    println("${cut("a,b,,")} [${pad("7")}] [${clean("  x ")}]")
}
```

```java
// Call48.java
import java.util.List;
import kotlin.text.StringsKt;

public class Call48 {
    public static void main(String[] args) {
        String padded = StringsKt.padStart("7", 3, '0');
        List<String> parts = StringsKt.split("a,b,,", new String[] {","}, false, 0);
        System.out.println(padded + " " + parts + " " + parts.size());
    }
}
```

```text
===== kotlinc call48.kt -d o48c =====
(exit 0)
===== java -cp o48c:kotlin-stdlib.jar Call48Kt =====
[a, b, , ] [007] [x]
(exit 0)
===== javap -c -p o48c/Call48Kt.class | grep -E 'public static final|StringsKt' =====
  public static final java.util.List<java.lang.String> cut(java.lang.String);
      26: invokestatic  #28                 // Method kotlin/text/StringsKt.split$default:(Ljava/lang/CharSequence;[Ljava/lang/String;ZIILjava/lang/Object;)Ljava/util/List;
  public static final java.lang.String pad(java.lang.String);
      10: invokestatic  #35                 // Method kotlin/text/StringsKt.padStart:(Ljava/lang/String;IC)Ljava/lang/String;
  public static final java.lang.String clean(java.lang.String);
      10: invokestatic  #40                 // Method kotlin/text/StringsKt.trim:(Ljava/lang/CharSequence;)Ljava/lang/CharSequence;
  public static final void main();
(exit 0)
===== javap -cp kotlin-stdlib.jar kotlin.text.StringsKt =====
public final class kotlin.text.StringsKt extends kotlin.text.StringsKt___StringsKt {
}
(exit 0)
===== javap -cp kotlin-stdlib.jar kotlin.text.StringsKt__StringsKt | grep -E '^public|^final|^class| (split|padStart|trim)\(java.lang.(CharSequence|String), (java.lang.String|int)' =====
class kotlin.text.StringsKt__StringsKt extends kotlin.text.StringsKt__StringsJVMKt {
  public static final java.lang.CharSequence padStart(java.lang.CharSequence, int, char);
  public static final java.lang.String padStart(java.lang.String, int, char);
  public static final java.util.List<java.lang.String> split(java.lang.CharSequence, java.lang.String[], boolean, int);
(exit 0)
===== javac -cp kotlin-stdlib.jar -d o48c Call48.java =====
(exit 0)
===== java -cp o48c:kotlin-stdlib.jar Call48 =====
007 [a, b, , ] 4
(exit 0)
```

- ★★★ **`s.split(",")` 은 `StringsKt.split$default(CharSequence, String[], boolean, int, int, Object)`** 로 컴파일된다 — 수신자가 **첫 인자**, `vararg` 는 **배열**, 기본값은 **`$default` 다리 메서드**가 채운다. `String` 에 메서드가 **붙은 것이 아니다.**
- ★★ **`kotlin.text.StringsKt` 는 몸통이 빈 클래스**이고 `StringsKt___StringsKt` 를 상속한다 — 여러 파일(`Strings.kt`·`StringsJVM.kt` …)의 최상위 함수를 **한 이름 아래 모은 파사드**다. 실제 선언은 `StringsKt__StringsKt` 에 있다.
- ★★ **Java 에서는 `StringsKt.padStart("7", 3, '0')`·`StringsKt.split("a,b,,", new String[] {","}, false, 0)`** 로 부른다 — 기본값이 없으니 **인자를 전부** 준다. 결과 `[a, b, , ]` 는 **4개**(Kotlin 규칙 그대로).
- ★ `trim(String)` 은 `StringsKt__StringsKt` 에 **없다**(`@InlineOnly`) — Java 에서 `trim` 을 부르려면 `trim(CharSequence)` 꼴이다.

## 문법 — 형태와 규칙

**형태** — CSV 한 줄 다듬기 · 0 채우기 · 날짜 그룹.

```kotlin
// form48.kt
fun main() {
    val line = "  kim, 42 ,seoul,,  "
    val fields = line.trim().split(",").map { it.trim() }
    println("fields  ${fields.size} $fields")

    val ids = listOf(7, 42, 1234).map { it.toString().padStart(4, '0') }
    println("ids     $ids")

    val date = Regex("(\\d{4})-(\\d{2})-(\\d{2})")
    val m = date.find("due 2026-09-26 done")
    println("date    ${m?.groupValues}")
    println("swap    ${date.replace("2026-09-26", "$3/$2/$1")}")
}
```

```text
===== kotlinc form48.kt -d o48z =====
(exit 0)
===== java -cp o48z:kotlin-stdlib.jar Form48Kt =====
fields  5 [kim, 42, seoul, , ]
ids     [0007, 0042, 1234]
date    [2026-09-26, 2026, 09, 26]
swap    26/09/2026
(exit 0)
```

**규칙 불릿**

- **Kotlin `split(String)` 은 글자 구분자 · 끝 빈 조각을 남긴다** — Java `split(regex, -1)` 과 같은 원소((1)(2)). 빈 조각을 버리려면 `.filter { it.isNotEmpty() }`.
- **정규식으로 쪼개려면 `Regex` 를 준다** — `split(Regex("\\s+"))` · `split(".".toRegex())` 는 「아무 글자」((2)).
- **Kotlin `trim()` 은 유니코드 공백** — Java `trim()` 과 다르고 `strip()` 과는 U+00A0 하나가 다르다((3)).
- **`matches` 는 전체 · `containsMatchIn`/`find` 는 부분**((4)).
- **치환 문자열의 `$1` 은 그대로 · `${name}` 은 `\${name}`** — 또는 람다 `replace`((4)).
- **`padStart(n)` 은 최소 길이** — 길면 그대로((5)).
- **Java 에서는 `StringsKt.함수(수신자, …)` 로 부른다** — 기본값 없이 전부((6)).

## 어디서 틀리나

1. ★★★ **CSV 한 줄을 Java `split(",")` 으로 쪼개던 코드를 Kotlin 으로 옮기고 열 수 검증을 그대로 둔다.** Kotlin 은 끝 빈 칸을 **남긴다** — 열 수가 **늘어난다**((1)). 반대로 옮기면 줄어든다([Java 35번](../../../java/syntax/35-string/)).
2. ★★★ **Java 에서 `split(".")` 을 쓴다 — 또는 Kotlin 에서 `split(".".toRegex())` 를 쓴다.** 빈 배열 · 빈 문자열 넷이다((2)).
3. ★★ **`trim()` 이 전각 공백·NBSP 를 깎는다고(또는 안 깎는다고) 가정한다.** 언어마다 다르다 — Java `trim` 은 둘 다 안 깎고, `strip` 은 전각만, Kotlin 은 둘 다((3)).
4. ★★ **`Regex.matches` 로 「포함하나」를 묻는다.** 전체 일치다 — `containsMatchIn`((4)).
5. ★★ **치환 문자열에 `"${name}"` 을 그대로 쓴다.** Kotlin 템플릿이 먼저 먹는다 — 같은 이름 변수가 있으면 **조용히 틀린다**((4)).
6. ★ **`padStart` 가 긴 문자열을 자른다고 본다.** 안 자른다((5)).
7. ★ **Java 에서 `"x".split(…)` 가 Kotlin 판을 부른다고 본다.** Java 의 `String.split` 은 Java 것이다 — Kotlin 판은 `StringsKt.split` 이다((6)).

## 구현 세부사항 대 언어 보장

| 항목 | 어느 쪽인가 | 근거 |
|---|---|---|
| Kotlin `split` 이 끝 빈 조각을 남긴다 | ★★★ **API 계약(KDoc)** | (1) |
| Java `split` 이 끝 빈 조각을 지운다 · `trim` 은 `<= U+0020` | ★★★ **JDK 계약(javadoc)** | (1)(3) |
| Kotlin `split(String)` 의 구분자는 글자 | ★★ **API 계약(서명)** — 매개변수 타입이 `String`·`Char`·`Regex` 로 갈린다 | (1)(2) |
| Kotlin `trim` 은 `Char::isWhitespace` | ★★ **API 계약(선언)** | (3) |
| JVM `isWhitespace` = `Character.isWhitespace \|\| isSpaceChar` | ★ **stdlib JVM 구현** — 다른 플랫폼(JS·Native)은 **재지 않았다** | (3) |
| `matches` = 전체 · `containsMatchIn` = 부분 | ★★ **API 계약(KDoc)** | (4) |
| `$` 뒤가 숫자면 템플릿이 아니다 · `${…}` 는 템플릿 | ★★★ **언어 규칙** | (4) · [02번 주제](../02-string-templates-and-raw-strings/) |
| `StringsKt` 파사드 · `split$default` · `@InlineOnly` 의 부재 | ★ **컴파일러·stdlib 판의 산출물** | (6) |

★★ **가장 조심할 자리** — `split` 의 갈림은 **두 언어가 각자의 계약을 지킨 결과**다. 「버그」가 아니므로 어느 쪽도 고쳐지지 않는다 — 옮길 때 **사람이** 맞춰야 한다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 고정 구분자로 쪼갠다 · 빈 칸도 열이다 | Kotlin `split(",")` | (1) |
| 빈 조각을 버린다 | `split(",").filter { it.isNotEmpty() }` | (1) |
| 공백 여러 개로 쪼갠다 | `split(Regex("\\s+"))` · `trim()` 먼저 | (1)(3) |
| 사용자 입력 앞뒤 공백 | Kotlin `trim()` — 유니코드 공백까지 | (3) |
| 전체가 형식에 맞나 | `Regex.matches` · `matchEntire` | (4) |
| 어딘가에 들어 있나 · 첫 위치 | `containsMatchIn` · `find` | (4) |
| 그룹을 바꿔 끼운다 | `replace(input, "$2-$1")` 또는 람다 `replace` | (4) |
| 고정 폭 번호 | `padStart(n, '0')` | (5) |

## 핵심 문장

1. **Kotlin `split` 은 끝 빈 조각을 남기고, Java `split` 은 지운다** — 5행 중 2행이 갈렸고, Java `split(d, -1)` 과는 0행이다.
2. **Kotlin `split(".")` 은 점 글자, Java `split(".")` 은 「아무 글자」** — Java 쪽은 빈 배열이다.
3. **`trim` 의 공백은 셋** — Java `trim` 은 `<= U+0020`, `strip` 은 `isWhitespace`, Kotlin 은 `isWhitespace ∪ isSpaceChar`(JVM).
4. **`matches` 는 전체 일치**, 부분은 `containsMatchIn`·`find` — 치환의 **`${name}` 만** Kotlin 템플릿과 부딪힌다.
5. 이 함수들은 **`StringsKt` 의 정적 메서드**다 — Java 에서는 수신자를 첫 인자로 넘긴다.

## 관련 자료

- [02번 주제](../02-string-templates-and-raw-strings/) — ★★★ **선행.** `$` 가 템플릿이 되는 조건(`$` 뒤가 식별자·`{`) · `trimIndent`/`trimMargin`. 그쪽은 **문자열을 만드는 문법**, 여기는 **만든 문자열을 다루는 API**.
- [Java 35번](../../../java/syntax/35-string/) — Java `split` 의 세 함정. [Java 37번](../../../java/syntax/37-regex/) — 정규식 문법·`Matcher`. **Java 쪽 정본**이다.
- [`cs/algorithm/25-string-matching/`](../../../../../algorithm/25-string-matching/) — 매칭 **알고리즘**. 그쪽은 「어떻게 찾나」, 여기는 「stdlib 함수가 경계에서 무엇을 돌려주나」.
- [`../../언어-특성/README.md`](../../언어-특성/README.md) §7 — 확장 함수가 정적 디스패치라는 것.
- [39번 주제](../39-java-interop-annotations/) — `@JvmName`·`@file:JvmName` 으로 파사드 이름(`StringsKt`)이 정해지는 원리.

## 용어 풀이

> **끝 빈 조각(trailing empty string)** — 구분자로 끝나는 문자열을 쪼갤 때 마지막 구분자 뒤에 생기는 빈 문자열.\
> 예: `"a,b,"` → Kotlin `["a", "b", ""]` · Java `["a", "b"]`.

> **`limit`** — 쪼갠 조각의 **최대 개수**. Kotlin `0` = 제한 없음. Java `0` = 제한 없음 **+ 끝 빈 조각 제거**, `-1` = 제한 없음 · 제거 없음.

> **`isWhitespace` / `isSpaceChar`** — JDK 의 두 공백 판정. 앞쪽은 줄바꿈 없는 공백(U+00A0 등)을 **뺀다**, 뒤쪽은 유니코드 **공백 분류**(Zs·Zl·Zp) 전부.

> **전체 일치 / 부분 일치** — 정규식이 입력 **전체**와 맞아야 참인 것(`matches`) / 입력 **어딘가**에 맞는 곳이 있으면 참인 것(`containsMatchIn`).

> **그룹 참조** — 치환 문자열 안의 `$1`·`${name}` — 일치한 괄호 그룹의 글자로 바뀐다.

> **파사드 클래스** — 여러 소스 파일의 최상위 함수를 **한 JVM 클래스 이름** 아래 모은 것(`@file:JvmMultifileClass`).

## 더 들어가면

- **`split` 의 `ignoreCase`** — 구분자를 대소문자 무시로 찾는다. 돌리지 않았다.
- **`lines()`·`lineSequence()`** — 줄 끝 규칙과 [47번 주제](../47-sequences-lazy-evaluation/)의 `Sequence` 가 이어지는 자리. 돌리지 않았다.
- **JS·Native 의 `isWhitespace`** — 플랫폼별 `actual` 이 따로 있다. 이 문서는 JVM 만 쟀다.
