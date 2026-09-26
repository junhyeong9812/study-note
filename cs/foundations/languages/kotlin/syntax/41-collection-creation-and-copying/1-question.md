# kotlin/syntax/41 — 컬렉션 생성 — `listOf`/`mutableListOf`/`buildList`/`toList` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [40번 주제](../40-read-only-collections-and-runtime-types/)(`List` 는 읽기 전용 뷰 · `as MutableList` 로 뚫린다)다.
> 문항 10개 중 예측형은 5개이고, 그중 코드블록이 붙는 것은 5개다.
> 이 주제의 모든 답은 **kotlinc 2.4.20 · Temurin JDK 21.0.5** 에서 실제로 던져 받은 것이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 열다섯 가지 꼴 (예측)

```kotlin
// make41.kt
fun cls(x: Any): String = x::class.java.name

fun fromList(name: String, make: (MutableList<Int>) -> List<Int>) {
    val src = mutableListOf(1, 2, 3)
    val made = make(src)
    val same = made === src
    src[0] = 99
    println(listOf(name, cls(made), same.toString(), (made[0] == 99).toString()).joinToString("\t"))
}

fun fromArray(name: String, make: (Array<Int>) -> List<Int>) {
    val arr = arrayOf(1, 2, 3)
    val made = make(arr)
    arr[0] = 99
    println(listOf(name, cls(made), "-", (made[0] == 99).toString()).joinToString("\t"))
}

fun noSource(name: String, made: List<Int>) {
    println(listOf(name, cls(made), "-", "-").joinToString("\t"))
}

fun main() {
    fromList("val ro: List<Int> = src") { it }
    fromList("src.toList()") { it.toList() }
    fromList("src.toMutableList()") { it.toMutableList() }
    fromList("buildList { addAll(src) }") { s -> buildList { addAll(s) } }
    fromList("List(src.size) { src[it] }") { s -> List(s.size) { s[it] } }
    fromList("ArrayList(src)") { ArrayList(it) }
    fromArray("listOf(*arr)") { listOf(*it) }
    fromArray("mutableListOf(*arr)") { mutableListOf(*it) }
    fromArray("arrayListOf(*arr)") { arrayListOf(*it) }
    fromArray("arr.asList()") { it.asList() }
    fromArray("arr.toList()") { it.toList() }
    noSource("listOf(1, 2, 3)", listOf(1, 2, 3))
    noSource("listOf(1)", listOf(1))
    noSource("emptyList()", emptyList())
    noSource("mutableListOf()", mutableListOf())
}
```

- 원본이 있는 11꼴 각각에서 **`=== src`** 와 **「원본의 0번을 `99` 로 고친 뒤 결과의 0번이 `99` 인가」** 는 무엇인가? 복사가 **아닌** 꼴은 어느 것인가?

### 2. ★★★ `toList()` 와 원소 수 (예측)

```kotlin
// tolist41.kt
fun cls(x: Any): String = x::class.java.name

fun main() {
    for (n in 0..3) {
        val src = MutableList(n) { it }
        val t = src.toList()
        println("list n=$n  ${cls(t)}  === src: ${t === src}")
    }
    println("set n=2   ${cls(setOf(1, 2).toList())}")
    println("seq n=2   ${cls(sequenceOf(1, 2).toList())}")
    val t2 = mutableListOf(1, 2).toList()
    try { (t2 as MutableList<Int>).add(3); println("cast add: $t2") } catch (e: Exception) { println("cast add: ${e::class.java.name}") }
    val t1 = mutableListOf(1).toList()
    try { (t1 as MutableList<Int>).add(3); println("cast add n=1: $t1") } catch (e: Exception) { println("cast add n=1: ${e::class.java.name}") }
    val again = t2.toList()
    println("toList of toList === : ${again === t2}")
}
```

- 돌리면 각 줄에 어떤 클래스와 결과가 찍히는가? 특히 `cast add:` 두 줄은?

### 3. ★★ `buildList` 의 안과 밖 (예측)

```kotlin
// build41.kt
fun main() {
    var inside: MutableList<Int>? = null
    val built = buildList<Int> {
        add(1)
        add(2)
        inside = this
        println("inside: ${this::class.java.name}")
    }
    println("built: ${built::class.java.name}  is MutableList: ${built is MutableList<*>}")
    println("same object: ${inside === built}")
    try { (built as MutableList<Int>).add(3); println("cast add: $built") } catch (e: Exception) { println("cast add: ${e::class.java.name}") }
    try { inside!!.add(4); println("leaked add: $built") } catch (e: Exception) { println("leaked add: ${e::class.java.name}") }
    println("built: $built")
}
```

- 돌리면 여섯 줄은 각각 무엇인가? `same object:` 는?

### 4. ★ 타입 인자 하나를 뺀 판 (예측)

```kotlin
// leak41.kt
fun main() {
    var inside: MutableList<Int>? = null
    val built = buildList {
        add(1)
        add(2)
        inside = this
        println("inside: ${this::class.java.name}")
    }
    println("built: ${built::class.java.name}  is MutableList: ${built is MutableList<*>}")
    println("same object: ${inside === built}")
    try { (built as MutableList<Int>).add(3); println("cast add: $built") } catch (e: Exception) { println("cast add: ${e::class.java.name}") }
    try { inside!!.add(4); println("leaked add: $built") } catch (e: Exception) { println("leaked add: ${e::class.java.name}") }
    println("built: $built")
}
```

- 3번 파일에서 3번째 줄의 `<Int>` 만 뺐다. 컴파일되는가?

### 5. ★★ 빈 리스트 여섯 줄 (예측)

```kotlin
// empty41.kt
fun main() {
    val a = emptyList<String>()
    val b = emptyList<Int>()
    println("1 ${a === b}")
    println("2 ${listOf<Int>() === b}")
    println("3 ${b.toList() === b}")
    println("4 ${mutableListOf<Int>() === mutableListOf<Int>()}")
    println("5 ${a == b}  ${a == mutableListOf<Int>()}")
    println("6 ${a::class.java.name}")
}
```

- `1`\~`6` 줄은 각각 무엇인가?

### 6. `listOf(*arr)` 의 복사는 누가 하나 (왜)

- 1번에서 `listOf(*arr)` 와 `arr.asList()` 는 결과 클래스가 같은데 한쪽은 복사다. stdlib 의 `listOf(vararg)` 가 하는 일은 무엇이고, 복사는 **어디서** 일어나는가?

### 7. `toList()` 의 사본은 잠겼나 (경계)

- 「`toList()` 는 읽기 전용 사본을 준다」는 **어디까지** 참인가? 2번의 두 `cast add:` 줄로 설명하면?

### 8. `buildList` 와 `toList()` — 「나오면 읽기 전용」을 누가 지키나 (연결)

- 3번의 `cast add:` 와 2번의 `cast add:`(원소 둘)는 결과가 반대다. 각각 **타입**이 지키나, **객체**가 지키나?

### 9. `toList()` 의 `toList()` 와 Java `List.copyOf` (연결)

- 2번의 마지막 줄은 무엇을 말하는가? [Java 40번](../../../java/syntax/40-list-set-and-immutable-factories/)의 `List.copyOf` 는 이미 불변인 것을 받으면 어떻게 하는가 — 둘은 무엇이 다른가?

### 10. 「`buildList` 가 빠르다」 (왜)

- 3번이 보인 「나올 때 복사하지 않는다」로 **「`buildList` 가 `mutableListOf` + `toList()` 보다 빠르다」** 를 주장할 수 있는가? 무엇을 재야 하나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
