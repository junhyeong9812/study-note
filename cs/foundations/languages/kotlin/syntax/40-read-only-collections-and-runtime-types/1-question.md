# kotlin/syntax/40 — 컬렉션 — 읽기 전용 인터페이스와 실제 런타임 타입 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [01번 주제](../01-val-var-and-basic-types/)(`val` 은 참조만 잠근다)다. 런타임 클래스 실측표는 [`../../언어-특성/README.md`](../../언어-특성/README.md) §5 에 있다 — 이 파일은 그 표를 **외웠는지** 묻지 않는다.
> 문항 11개 중 예측형은 6개이고, 그중 코드블록이 붙는 것은 4개다.
> 이 주제의 모든 답은 **kotlinc 2.4.20 · Temurin JDK 21.0.5** 에서 실제로 던져 받은 것이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ `List<Int>` 로 받은 것 (예측)

```kotlin
// hole40.kt
fun total(xs: List<Int>): Int {
    (xs as MutableList<Int>).add(100)
    return xs.sum()
}

fun main() {
    val src = mutableListOf(1, 2, 3)
    val ro: List<Int> = src
    println("1 ro === src: ${ro === src}")
    src.add(4)
    println("2 ro: $ro")
    println("3 total(ro): ${total(ro)}")
    println("4 src: $src")

    val lo = listOf(1, 2)
    println("5 lo is MutableList: ${lo is MutableList<*>}")
    println("6 listOf(1) is MutableList: ${listOf(1) is MutableList<*>}")
    println("7 emptyList() is MutableList: ${emptyList<Int>() is MutableList<*>}")
    try { (lo as MutableList<Int>).add(3); println("8 lo: $lo") } catch (e: Exception) { println("8 ${e::class.java.name}") }
    try { (lo as MutableList<Int>)[0] = 9; println("9 lo: $lo") } catch (e: Exception) { println("9 ${e::class.java.name}") }
    try { (emptyList<Int>() as MutableList<Int>).add(1); println("10 ok") } catch (e: Exception) { println("10 ${e::class.java.name}") }
}
```

- 컴파일되는가? 돌리면 `1`\~`4` 줄은 각각 무엇인가? 특히 `4 src:` 줄에 무엇이 찍히는가?

### 2. ★★★ 같은 파일의 `5`\~`10` 줄 (예측)

- 1번 파일에서 `is MutableList<*>` 세 줄(`5`·`6`·`7`)과 캐스트 세 줄(`8`·`9`·`10`)은 각각 무엇을 찍는가?

### 3. ★★ `is`/`as MutableList` 는 무엇으로 컴파일되나 (예측)

- 1번 파일을 `javap -c` 로 보면 `is MutableList<*>` 와 `as MutableList<Int>` 는 각각 **어떤 메서드 호출**이 되는가? 그 메서드는 무엇을 보고 판정하는가?

### 4. ★★ 타입이 막는 줄 (예측)

```kotlin
// bad40.kt
fun main() {
    val ro: List<Int> = mutableListOf(3, 1, 2)
    ro.add(4)
    ro[0] = 9
    ro.sort()
    val ml: MutableList<Any> = mutableListOf<Int>(1)
}
```

- 에러가 나는 줄은 어디이고 각각 무엇이라고 말하는가?

### 5. ★★★ Java 가 받으면 (예측)

```kotlin
// repo40.kt
class Repo {
    private val items = mutableListOf("a")
    fun items(): List<String> = items
    fun fixed(): List<String> = listOf("x", "y")
    fun dump(): String = items.toString()
}
```

```java
// JRepo.java
import java.util.List;

public class JRepo {
    public static void main(String[] args) {
        Repo repo = new Repo();
        repo.items().add("J");
        System.out.println("1 dump: " + repo.dump());
        List<String> f = repo.fixed();
        try { f.add("J"); System.out.println("2 " + f); } catch (RuntimeException e) { System.out.println("2 " + e.getClass().getName()); }
        try { f.set(0, "J"); System.out.println("3 " + f); } catch (RuntimeException e) { System.out.println("3 " + e.getClass().getName()); }
        List<String> jf = List.of("x", "y");
        try { jf.set(0, "J"); System.out.println("4 " + jf); } catch (RuntimeException e) { System.out.println("4 " + e.getClass().getName()); }
    }
}
```

- `javac` 는 통과하는가? 돌리면 `1`\~`4` 줄은 각각 무엇인가?

### 6. ★★ 연산 API 여덟 줄 (예측)

```kotlin
// ops40.kt
fun main() {
    val src = mutableListOf(3, 1, 2)
    val m = src.map { it }
    val f = src.filter { true }
    println("1 map === src: ${m === src}  filter === src: ${f === src}")
    val rv = src.asReversed()
    val rd = src.reversed()
    val so = src.sorted()
    val p = src + 9
    src.add(0)
    println("2 asReversed: $rv")
    println("3 reversed: $rd")
    println("4 sorted: $so")
    println("5 plus: $p")
    println("6 src: $src")
    src.sort()
    println("7 src after sort(): $src  rv: $rv")
    val wide: List<Any> = src
    println("8 wide === src: ${wide === src}")
}
```

- `1`\~`8` 줄은 각각 무엇인가? 특히 `2` 와 `7` 의 `rv` 는?

### 7. `is MutableList` 가 `true` 인데 `add` 는 실패하는 이유 (왜)

- 2번에서 `listOf(1, 2)` 는 `is MutableList` 가 `true` 였는데 캐스트한 `add` 는 실패했다. `true` 는 무엇을 뜻하고 무엇을 뜻하지 않는가?

### 8. 읽기 전용과 불변 (경계)

- 「`List` 는 읽기 전용이다」와 「`List` 는 불변이다」는 **누가** 보장하는 말인가? 내부 상태를 밖에 내주면서 밖이 **절대** 못 고치게 하려면 무엇을 내줘야 하나?

### 9. Kotlin `listOf` 와 Java `List.of` (연결)

- 5번의 `3` 줄과 `4` 줄은 왜 다른가? [Java 40번](../../../java/syntax/40-list-set-and-immutable-factories/)의 말로 둘을 부르면?

### 10. `asReversed()` 와 `reversed()` (왜)

- 이름이 한 글자 차이인 두 함수를 원본이 **나중에 바뀌는** 코드에서 바꿔 쓰면 무엇이 달라지는가?

### 11. C#·Rust·Python 의 같은 자리 (연결)

- `IReadOnlyList<int>` 를 `List<int>` 로 캐스트해 `Add` 하면? Rust 에서 `&Vec<i32>` 로 받은 함수가 `push` 하면? Python 에서 `Sequence[int]` 힌트를 단 함수가 `list` 에 `append` 하면? 셋 중 **Kotlin 과 같은 구멍**은 어느 것인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
