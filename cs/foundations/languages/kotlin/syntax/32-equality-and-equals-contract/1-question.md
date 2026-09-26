# kotlin/syntax/32 — 동등성: `==`/`===`·`equals` 규약·`data class` 와의 관계 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [22번 주제](../22-data-class-generated-members/)다 — `data class` 의 `equals` 가 **무엇을 보는지**는 거기서 봤다. 해시 원리는 [`cs/data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/)이 정본이다.
> 문항 12개 중 코드블록이 붙는 예측형은 6개다.
> 바이트코드를 묻는 문항은 **`kotlinc` 기본 `-jvm-target`(1.8)** 기준이다.
> 이 주제의 모든 답은 **kotlinc 2.4.20 · JRE 21.0.5**(Java 쪽은 **javac 21.0.5**)에서 실제로 던져 받은 것이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ `==`·`===`·`equals` 를 모양별로 — 바이트코드 (예측)

```kotlin
// eqforms.kt
data class Pt(val x: Int)

fun e1(a: String?, b: String?) = a == b
fun e2(a: Int, b: Int) = a == b
fun e3(a: Int?, b: Int?) = a == b
fun e4(a: Pt?, b: Pt?) = a === b
fun e5(a: Pt, b: Pt?) = a.equals(b)
fun e6(a: Pt?) = a == null
fun e7(a: Double, b: Double) = a == b
fun e8(a: Any?, b: Any?) = a == b

fun main() {
    println("A ${e1(null, null)} ${e1("k", null)} ${e1(String(charArrayOf('k')), "k")}")
    println("B ${e2(1, 1)} ${e3(1000, 1000)} ${e4(Pt(1), Pt(1))} ${e5(Pt(1), Pt(1))} ${e6(null)}")
}
```

- `A`·`B` 에 무엇이 찍히는가?
- `e1`\~`e8` 은 각각 어떤 명령(또는 어떤 메서드 호출)으로 번역되는가? `equals` 를 **부르지 않는** 함수는 어느 것인가?

### 2. ★★ Java 와 Kotlin 에 같은 두 문자열 (예측)

```java
// Eq32.java
import java.util.Objects;

public class Eq32 {
    static boolean j1(String a, String b) { return a == b; }
    static boolean j2(String a, String b) { return a.equals(b); }
    static boolean j3(String a, String b) { return Objects.equals(a, b); }

    public static void main(String[] args) {
        String a = new String("k");
        String b = "k";
        System.out.println("A " + j1(a, b) + " " + j2(a, b) + " " + j3(a, b));
        System.out.println("B " + j3(null, null));
        try { j2(null, b); } catch (NullPointerException e) { System.out.println("C NPE"); }
    }
}
```

```kotlin
// eqk32.kt
fun k1(a: String?, b: String?) = a == b
fun k2(a: String?, b: String?) = a === b

fun main() {
    val a = String(charArrayOf('k'))
    val b = "k"
    println("A ${k1(a, b)} ${k2(a, b)}")
    println("B ${k1(null, null)} ${k1(null, b)}")
}
```

- 두 프로그램은 각각 무엇을 찍는가?
- Java 의 `j1`·`j2`·`j3` 중 Kotlin 의 `k1` 과 가까운 것, `k2` 와 **바이트코드가 같은** 것은 각각 어느 것인가?

### 3. ★★ 박싱된 `127` 과 `128` (예측)

```kotlin
// cache.kt
fun main() {
    val a: Int? = 127
    val b: Int? = 127
    val c: Int? = 128
    val d: Int? = 128
    println("A ${a === b} ${c === d}")
    println("B ${a == b} ${c == d}")
}
```

- 컴파일되는가? 진단이 나온다면 에러인가 경고인가?
- `java` 로 돌리면 `A`·`B` 에? `java -XX:AutoBoxCacheMax=1000` 으로 돌리면?

### 4. ★★★ 규약을 하나씩 깬 키를 셋과 리스트에 (예측)

```kotlin
// vgrid.kt
class R1(val v: Int) {
    override fun equals(other: Any?) = false
    override fun hashCode() = v
}

class R2(val v: Int) {
    override fun equals(other: Any?) = other is R2 && other.v == v
}

data class R3(var v: Int)

class R4(val v: Int) {
    override fun equals(other: Any?) = other is R4 && kotlin.math.abs(other.v - v) <= 1
    override fun hashCode() = 0
}

class R5(val s: String) {
    override fun equals(other: Any?) = when (other) {
        is R5 -> other.s.equals(s, ignoreCase = true)
        is String -> other.equals(s, ignoreCase = true)
        else -> false
    }
    override fun hashCode() = s.lowercase().hashCode()
}

data class R6(val v: Int)

var split = 0
var cells = 0

fun row(name: String, make: () -> Any, mutate: (Any) -> Unit = {}) {
    val k = make()
    val set = HashSet<Any>()
    set.add(k)
    set.add(make())
    mutate(k)
    val list = arrayListOf<Any>(k)
    val sk = set.contains(k); val sn = set.contains(make())
    val lk = list.contains(k); val ln = list.contains(make())
    cells += 2
    if (sk != lk) split++
    if (sn != ln) split++
    println("%-3s | size=%d | set.contains(k)=%-5s | set.contains(new)=%-5s | list.contains(k)=%-5s | list.contains(new)=%-5s".format(name, set.size, sk, sn, lk, ln))
}

fun main() {
    row("R1", { R1(1) })
    row("R2", { R2(1) })
    row("R3", { R3(1) }, { (it as R3).v = 2 })
    row("R6", { R6(1) })
    println("set 과 list 가 갈린 칸 $split / $cells")
    val a = HashSet<Any>(); for (v in listOf(1, 3, 2)) a.add(R4(v))
    val b = HashSet<Any>(); for (v in listOf(2, 1, 3)) b.add(R4(v))
    println("R4 | order 1,3,2 -> size=${a.size} | order 2,1,3 -> size=${b.size}")
    val s1 = HashSet<Any>(listOf(R5("A")))
    val s2 = HashSet<Any>(listOf("a"))
    println("R5 | {R5(A)}.contains(\"a\")=${s1.contains("a")} | {\"a\"}.contains(R5(A))=${s2.contains(R5("A"))}")
    println("R5 | R5(A).equals(\"a\")=${R5("A").equals("a")} | \"a\".equals(R5(A))=${"a".equals(R5("A"))}")
}
```

- `R1`·`R2`·`R3`·`R6` 줄의 `size` 와 네 `contains` 는 각각 무엇인가? 마지막에 찍히는 「갈린 칸」은?
- `R4` 의 두 `size`, `R5` 의 두 `contains` 와 두 `equals` 는?

### 5. ★★ 본문 프로퍼티를 가진 `data class` 를 셋과 맵에 (예측)

```kotlin
// body.kt
data class Tag(val id: Int) {
    var note: String = ""
}

fun main() {
    val a = Tag(1).apply { note = "first" }
    val b = Tag(1).apply { note = "second" }
    val set = hashSetOf(a, b)
    println("A ${set.size} ${set.first().note}")
    val map = hashMapOf(a to "va")
    map[b] = "vb"
    println("B ${map.size} ${map.keys.first().note} ${map[a]}")
}
```

- `A`·`B` 에 무엇이 찍히는가? `second` 의 `note` 는 어디로 갔는가?

### 6. ★★ 부동소수점과 정적 타입 (예측)

```kotlin
// nan.kt
data class Box(val d: Double)

fun main() {
    val x = Double.NaN
    val y: Any = Double.NaN
    val z: Double? = Double.NaN
    println("A ${x == x} ${y == y} ${z == z}")
    val p = 0.0
    val q = -0.0
    val pa: Any = 0.0
    val qa: Any = -0.0
    println("B ${p == q} ${pa == qa}")
    println("C ${listOf(Double.NaN).contains(Double.NaN)} ${x.equals(x)}")
    println("D ${x < 1.0} ${x > 1.0} ${x.compareTo(1.0)}")
    println("E ${Box(Double.NaN) == Box(Double.NaN)} ${Box(0.0) == Box(-0.0)}")
}
```

- `A`\~`E` 에 무엇이 찍히는가?

### 7. `equals` 만 재정의하면 (경계)

- `equals` 만 재정의하고 `hashCode` 를 안 고친 클래스에 kotlinc 2.4.20 은 경고를 내는가? `-Wextra` 로는?
- 같은 컴파일에서 경고가 **나는** 자리는 어디인가? 배열을 가진 `data class` 에는?

### 8. `R2` 에서 셋과 리스트가 갈리는 이유 (왜)

- `equals` 는 멀쩡한데 `HashSet.contains(new)` 만 `false` 인 이유는? `ArrayList` 는 왜 멀쩡한가?

### 9. `R1` 을 넣은 그 객체로 찾으면 (왜)

- `equals` 가 늘 `false` 인데 `set.contains(k)` 가 `true` 인 이유는? 이것은 언어의 약속인가?
- `list.contains(k)` 는 왜 다른 답인가? 파이썬의 `list` 와는 무엇이 다른가?

### 10. `127`/`128` 의 층 (경계)

- 「`-128..127` 에서 `===` 가 `true`」는 언어 보장인가, 구현인가? 3번의 두 번째 실행이 그것을 어떻게 가르는가?
- `Int?` 의 `===` 는 경고이고 `value class` 의 `===` 는 에러인 이유는?

### 11. 호환되지 않는 `==` (경계)

- `"a" == 1` · `Cat() == Dog()` · `x == "a"`(`x: Any`) · `1 == 1L` 중 컴파일러가 막는 것은 어느 것인가?

### 12. Python·Rust 와의 방어선 (연결)

- `equals` 만 고친 키를 해시 셋에 넣는 사고를 **Kotlin·Python·Rust** 는 각각 언제(컴파일·런타임·안 막음) 잡는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
