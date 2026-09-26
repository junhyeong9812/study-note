# kotlin/syntax/48 — 문자열 API — `split`/`trim*`/`pad*`/`Regex` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [02번 주제](../02-string-templates-and-raw-strings/)(문자열 템플릿 — `$` 가 글자인 조건)다.
> 문항 10개 중 예측형은 6개이고, 여섯 모두 코드블록이 붙는다.
> 이 주제의 모든 답은 **kotlinc 2.4.20 · Temurin JDK 21.0.5** 에서 실제로 던져 받은 것이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 다섯 입력 × 다섯 쪼개는 꼴 (예측)

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

- 각 칸의 원소 수와 원소는 무엇인가? 마지막 두 줄의 `N / M` 은?

### 2. ★★★ 앞뒤에 둔 글자 일곱 × 세 `trim` (예측)

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

- 각 행에서 세 `trim` 이 남기는 코드포인트는 무엇인가? 두 `isWhitespace` 열은? 마지막 두 줄의 `N / M` 은?

### 3. ★★ `"a.b"` 를 점으로 — 두 언어 (예측)

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

- 다섯 줄의 원소 수와 원소는 무엇인가?

### 4. ★★ 정규식 열두 줄 (예측)

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

- `1`\~`12` 줄은 각각 무엇인가? 특히 `9` 와 `10` 은?

### 5. ★ 채우기 (예측)

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

- `1`\~`6` 줄은 무엇인가?

### 6. ★★ Java 에서 부르면 (예측)

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

- `javap -c` 로 `cut`·`pad`·`clean` 을 보면 어떤 메서드 호출이 박혀 있나? `Call48` 의 출력은?

### 7. Kotlin `split` 이 끝 빈 조각을 남기는 것은 누가 정했나 (경계)

- 1번의 `"a,b,,"` 행이 보인 양쪽 동작은 각각 **계약**인가 구현인가? 근거 문장은 어디에 있나?

### 8. Kotlin `trim` 과 Java `strip` 이 갈리는 한 글자 (왜)

- 2번에서 두 함수가 갈린 행은 어느 글자이고, 왜 갈리나? Kotlin 쪽 정의의 어느 부분이 **JVM 구현**인가?

### 9. 치환 문자열의 `$` 와 템플릿 (경계)

- `"$2:$1"` 에 `\` 가 필요 없는 이유와 `"${name}"` 에는 필요한 이유는 무엇인가? 빠뜨리면 무엇이 일어나나?

### 10. CSV 열 수 검증 (연결)

- [Java 35번](../../../java/syntax/35-string/)의 「`split` 결과 길이를 믿는다」 함정은 Kotlin 으로 옮기면 어떻게 바뀌나? 어느 쪽으로 옮길 때 무엇이 조용히 달라지나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
