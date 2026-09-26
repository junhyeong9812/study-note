# kotlin/syntax/42 — 변환 연산 — `map`/`flatMap`/`associate`/`zip` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `java` 에서 실제로 얻었다.
> ★★ 아래 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적은 자리가 없다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ `Set`·`Array`·`Map` 의 `map` 은 전부 **`List`** · `Sequence` 는 대부분 **`Sequence`** · `Map` 에는 **`map`·`mapNotNull`·`flatMap`·`mapValues`** 만 있다

**출력**

```kotlin
// type42.kt
fun t(x: Nothing?) {}

fun main() {
    val l: List<Int> = listOf(1, 2, 3)
    val s: Set<Int> = setOf(1, 2, 3)
    val m: Map<String, Int> = mapOf("a" to 1, "b" to 2)
    val q: Sequence<Int> = sequenceOf(1, 2, 3)
    val a: Array<Int> = arrayOf(1, 2, 3)

    t(l.map { it })                              // map List
    t(s.map { it })                              // map Set
    t(m.map { it.value })                        // map Map
    t(q.map { it })                              // map Sequence
    t(a.map { it })                              // map Array

    t(l.mapNotNull { it })                       // mapNotNull List
    t(s.mapNotNull { it })                       // mapNotNull Set
    t(m.mapNotNull { it.value })                 // mapNotNull Map
    t(q.mapNotNull { it })                       // mapNotNull Sequence
    t(a.mapNotNull { it })                       // mapNotNull Array

    t(l.flatMap { listOf(it) })                  // flatMap List
    t(s.flatMap { listOf(it) })                  // flatMap Set
    t(m.flatMap { listOf(it.value) })            // flatMap Map
    t(q.flatMap { listOf(it) })                  // flatMap Sequence
    t(a.flatMap { listOf(it) })                  // flatMap Array

    t(l.flatMap { sequenceOf(it) })              // flatMap{seq} List
    t(s.flatMap { sequenceOf(it) })              // flatMap{seq} Set
    t(m.flatMap { sequenceOf(it.value) })        // flatMap{seq} Map
    t(q.flatMap { sequenceOf(it) })              // flatMap{seq} Sequence
    t(a.flatMap { sequenceOf(it) })              // flatMap{seq} Array

    t(listOf(l, l).flatten())                    // flatten List
    t(setOf(s, s).flatten())                     // flatten Set
    t(mapOf("a" to l).flatten())                 // flatten Map
    t(sequenceOf(q, q).flatten())                // flatten Sequence
    t(arrayOf(a, a).flatten())                   // flatten Array

    t(l.associate { it to it })                  // associate List
    t(s.associate { it to it })                  // associate Set
    t(m.associate { it.value to it.key })        // associate Map
    t(q.associate { it to it })                  // associate Sequence
    t(a.associate { it to it })                  // associate Array

    t(l.associateBy { it })                      // associateBy List
    t(s.associateBy { it })                      // associateBy Set
    t(m.associateBy { it.value })                // associateBy Map
    t(q.associateBy { it })                      // associateBy Sequence
    t(a.associateBy { it })                      // associateBy Array

    t(l.associateWith { it })                    // associateWith List
    t(s.associateWith { it })                    // associateWith Set
    t(m.associateWith { it.value })              // associateWith Map
    t(q.associateWith { it })                    // associateWith Sequence
    t(a.associateWith { it })                    // associateWith Array

    t(l.zip(l))                                  // zip List
    t(s.zip(s))                                  // zip Set
    t(m.zip(m))                                  // zip Map
    t(q.zip(q))                                  // zip Sequence
    t(a.zip(a))                                  // zip Array

    t(l.map { it to "x" }.unzip())               // unzip List
    t(s.map { it to "x" }.toSet().unzip())       // unzip Set
    t(mapOf(1 to "x").unzip())                   // unzip Map
    t(q.map { it to "x" }.unzip())               // unzip Sequence
    t(a.map { it to "x" }.toTypedArray().unzip()) // unzip Array

    t(l.withIndex())                             // withIndex List
    t(s.withIndex())                             // withIndex Set
    t(m.withIndex())                             // withIndex Map
    t(q.withIndex())                             // withIndex Sequence
    t(a.withIndex())                             // withIndex Array

    t(l.mapIndexed { i, v -> i + v })            // mapIndexed List
    t(s.mapIndexed { i, v -> i + v })            // mapIndexed Set
    t(m.mapIndexed { i, e -> i + e.value })      // mapIndexed Map
    t(q.mapIndexed { i, v -> i + v })            // mapIndexed Sequence
    t(a.mapIndexed { i, v -> i + v })            // mapIndexed Array

    t(l.mapValues { it })                        // mapValues List
    t(s.mapValues { it })                        // mapValues Set
    t(m.mapValues { it.value })                  // mapValues Map
    t(q.mapValues { it })                        // mapValues Sequence
    t(a.mapValues { it })                        // mapValues Array
}
```

```python
# grid42.py
import re
import subprocess

SRC = "type42.kt"
INPUTS = ["List", "Set", "Map", "Sequence", "Array"]

cells = {}
order = []
for n, line in enumerate(open(SRC, encoding="utf-8"), 1):
    m = re.search(r"// (\S+) (\S+)$", line.rstrip("\n"))
    if m:
        op, inp = m.groups()
        cells[n] = (op, inp)
        if op not in order:
            order.append(op)

run = subprocess.run(["kotlinc", SRC, "-d", "o42t"], capture_output=True, text=True)
if run.returncode != 1:
    raise SystemExit("expected exit 1, got %d" % run.returncode)

first = {}
for line in (run.stdout + run.stderr).splitlines():
    m = re.match(r"type42\.kt:(\d+):\d+: error: (.*)$", line)
    if m and int(m.group(1)) not in first:
        first[int(m.group(1))] = m.group(2)

result = {}
for n, (op, inp) in cells.items():
    msg = first.get(n)
    if msg is None:
        raise SystemExit("no diagnostic on line %d" % n)
    m = re.match(r"argument type mismatch: actual type is '(.*)', but 'Nothing\?' was expected\.$", msg)
    if m:
        result[(op, inp)] = m.group(1)
    elif msg.startswith("unresolved reference '"):
        result[(op, inp)] = "-"
    else:
        raise SystemExit("unexpected diagnostic on line %d: %s" % (n, msg))

print("\t".join(["op"] + INPUTS))
exists = changed = 0
for op in order:
    row = [result[(op, i)] for i in INPUTS]
    if len(row) != len(INPUTS):
        raise SystemExit("cell count mismatch: " + op)
    print("\t".join([op] + row))
    for inp, typ in zip(INPUTS, row):
        if typ == "-":
            continue
        exists += 1
        if typ.split("<")[0] != inp:
            changed += 1
print("cells whose result container differs from the input: %d / %d" % (changed, exists))
```

```text
===== kotlinc type42.kt -d o42raw | sed -n '1,6p' =====
type42.kt:10:7: error: argument type mismatch: actual type is 'List<Int>', but 'Nothing?' was expected.
    t(l.map { it })                              // map List
      ^^^^^^^^^^^^
type42.kt:11:7: error: argument type mismatch: actual type is 'List<Int>', but 'Nothing?' was expected.
    t(s.map { it })                              // map Set
      ^^^^^^^^^^^^
(exit 1)
```

```text
===== python3 grid42.py =====
op	List	Set	Map	Sequence	Array
map	List<Int>	List<Int>	List<Int>	Sequence<Int>	List<Int>
mapNotNull	List<Int>	List<Int>	List<Int>	Sequence<Int>	List<Int>
flatMap	List<Int>	List<Int>	List<Int>	Sequence<Int>	List<Int>
flatMap{seq}	List<Int>	List<Int>	List<Int>	Sequence<Int>	List<Int>
flatten	List<Int>	List<Int>	-	Sequence<Int>	List<Int>
associate	Map<Int, Int>	Map<Int, Int>	-	Map<Int, Int>	Map<Int, Int>
associateBy	Map<Int, Int>	Map<Int, Int>	-	Map<Int, Int>	Map<Int, Int>
associateWith	Map<Int, Int>	Map<Int, Int>	-	Map<Int, Int>	Map<Int, Int>
zip	List<Pair<Int, Int>>	List<Pair<Int, Int>>	-	Sequence<Pair<Int, Int>>	List<Pair<Int, Int>>
unzip	Pair<List<Int>, List<String>>	Pair<List<Int>, List<String>>	-	Pair<List<Int>, List<String>>	Pair<List<Int>, List<String>>
withIndex	Iterable<IndexedValue<Int>>	Iterable<IndexedValue<Int>>	-	Sequence<IndexedValue<Int>>	Iterable<IndexedValue<Int>>
mapIndexed	List<Int>	List<Int>	-	Sequence<Int>	List<Int>
mapValues	-	-	Map<String, Int>	-	-
cells whose result container differs from the input: 37 / 53
(exit 0)
```

**왜 그런가**

- ★★★ 결과 그릇은 **서명이 적는다** — `Iterable<T>.map(…): List<R>` 하나를 `List`·`Set` 이 같이 쓰니 `Set` 도 `List` 를 받는다. `Array` 도 `List` 로 돌아온다.
- ★★ `Map` 은 `Iterable` 이 아니다 — 그래서 `flatten`·`associate*`·`zip`·`unzip`·`withIndex`·`mapIndexed` 가 **`unresolved reference … on receiver of type 'Map<String, Int>'`** 로 나온다. `mapValues` 는 반대로 `Map` 에만 있다.
- ★ `withIndex()` 는 `List` 가 아니라 **`Iterable<IndexedValue<Int>>`** · `unzip()` 은 **`Pair<List<Int>, List<String>>`** 다.

### 2. **16 / 53 칸만 지킨다** — `List` 열 7칸 · **`Sequence` 열 8칸** · `Map.mapValues` 1칸 · `Sequence` 열에서 **`associate*` 셋(`Map`)과 `unzip`(`Pair<List, List>`)** 이 그릇을 바꾼다

**출력** — 1번 격자의 마지막 줄이 「바꾼 칸」을 셌다: **`37 / 53`**. 지킨 칸은 그 나머지다.

**왜 그런가**

- ★★★ `Set` 열에는 `Set` 이 **한 칸도 없고**, `Array` 열에는 `Array` 가 **한 칸도 없다** — 두 열은 전부 「바꾼 칸」이다.
- ★★ `Sequence` 는 `map`·`mapNotNull`·`flatMap`·`flatMap{seq}`·`flatten`·`zip`·`withIndex`·`mapIndexed` 에서 `Sequence` 로 남는다. **`unzip`** 은 두 리스트를 **채워야** 하므로 거기서 끝난다.
- ★ `List` 열의 `zip` 은 `List<Pair<…>>` 라 「지킨 칸」으로 셌다(바깥 그릇이 `List`). `withIndex` 는 `Iterable` 이라 「바꾼 칸」이다.

### 3. ★★★ **`1 [1, 0, 1, 0]  size 4`**(중복이 산다) · **`3 {a=avocado, b=blueberry, c=cherry}  size 5 -> 3`**(마지막이 이긴다) · `zip` 은 **두 쌍**

**출력**

```kotlin
// shape42.kt
fun main() {
    val s = setOf(1, 2, 3, 4)
    val parity = s.map { it % 2 }
    println("1 $parity  size ${parity.size}")
    println("2 ${s.mapTo(mutableSetOf()) { it % 2 }}")

    val words = listOf("apple", "avocado", "banana", "blueberry", "cherry")
    val byFirst = words.associateBy { w -> w.first().also { println("   key ${it} <- $w") } }
    println("3 $byFirst  size ${words.size} -> ${byFirst.size}")
    println("4 ${words.groupBy { it.first() }}")

    println("5 ${listOf(1, 2, 3).zip(listOf("a", "b"))}")
    println("6 ${listOf(1, 2).zip(listOf("a", "b", "c")) { n, t -> "$t$n" }}")

    val prices = mapOf("tea" to 3, "cake" to 5)
    val m1 = prices.map { (k, v) -> "$k=${v * 2}" }
    val m2 = prices.mapValues { (_, v) -> v * 2 }
    println("7 $m1  ${m1::class.java.name}")
    println("8 $m2  ${m2::class.java.name}")

    val fs = listOf(1, 2).flatMap { n -> sequenceOf(n, n * 10) }
    println("9 $fs  ${fs::class.java.name}")
}
```

```text
===== kotlinc shape42.kt -d o42s =====
(exit 0)
===== java -cp o42s:kotlin-stdlib.jar Shape42Kt =====
1 [1, 0, 1, 0]  size 4
2 [1, 0]
   key a <- apple
   key a <- avocado
   key b <- banana
   key b <- blueberry
   key c <- cherry
3 {a=avocado, b=blueberry, c=cherry}  size 5 -> 3
4 {a=[apple, avocado], b=[banana, blueberry], c=[cherry]}
5 [(1, a), (2, b)]
6 [a1, b2]
7 [tea=6, cake=10]  java.util.ArrayList
8 {tea=6, cake=10}  java.util.LinkedHashMap
9 [1, 10, 2, 20]  java.util.ArrayList
(exit 0)
```

**왜 그런가**

- ★★★ `Set.map` 의 결과는 `List` 라 `it % 2` 가 만든 `1, 0, 1, 0` 이 **다 남는다.** 세트 그릇을 원하면 `mapTo(mutableSetOf())` 로 **그릇을 직접 준다**(`2 [1, 0]`).
- ★★★ `associateBy` 는 로그대로 **다섯 번 키를 뽑았고**, `a`·`b` 가 두 번씩 나와 **나중 것이 앞의 것을 덮었다.** 전부 남기는 것은 `groupBy`(`4`).
- ★★ `zip` 은 **짧은 쪽**(2개)에서 멈춘다 — `3` 은 버려진다. `6` 은 반대로 `"c"` 가 버려진다.
- ★★ `Map.map` 은 `List`(`java.util.ArrayList`) · `mapValues` 는 `Map`(`java.util.LinkedHashMap`) — **키를 지키는 쪽은 `mapValues`** 다.
- ★ `flatMap { sequenceOf(…) }` 도 리스트 쪽 `flatMap` 이라 결과는 **`ArrayList`** 다(`9`).

### 4. **`byUser   {kim=3, lee=2}`** — `kim` 의 값은 **3번 주문**이다(1번 주문이 덮였다)

**출력**

```kotlin
// form42.kt
data class Order(val id: Int, val user: String, val items: List<String>)

fun main() {
    val orders = listOf(
        Order(1, "kim", listOf("tea", "cake")),
        Order(2, "lee", listOf("tea")),
        Order(3, "kim", listOf("coffee")),
    )
    val ids: List<Int> = orders.map { it.id }
    val allItems: List<String> = orders.flatMap { it.items }
    val byId: Map<Int, Order> = orders.associateBy { it.id }
    val lastByUser: Map<String, Order> = orders.associateBy { it.user }
    val labeled: List<Pair<Int, String>> = ids.zip(listOf("a", "b", "c"))
    println("ids      $ids")
    println("items    $allItems")
    println("byId     ${byId.keys}")
    println("byUser   ${lastByUser.mapValues { it.value.id }}")
    println("labeled  $labeled")
}
```

```text
===== kotlinc form42.kt -d o42z =====
(exit 0)
===== java -cp o42z:kotlin-stdlib.jar Form42Kt =====
ids      [1, 2, 3]
items    [tea, cake, tea, coffee]
byId     [1, 2, 3]
byUser   {kim=3, lee=2}
labeled  [(1, a), (2, b), (3, c)]
(exit 0)
```

**왜 그런가**

- ★★ `associateBy { it.user }` 에서 `kim` 이 **두 번**(1번·3번 주문) 나왔고 **마지막(3번)** 만 남았다. `byId` 는 id 가 유일해 셋이 다 남았다.
- ★ 「사용자별 주문 전부」가 목적이었다면 `groupBy { it.user }` 가 맞다 — [44번 주제](../44-aggregation-grouping-fold-reduce/).

### 5. **넷**(격자 행으로는 다섯 — `flatMap` 이 두 꼴) — `map`·`mapNotNull`·`flatMap`·`mapValues` · 없는 칸은 **`unresolved reference '<이름>' on receiver of type 'Map<…>'.`**

**출력** — 1번 격자의 `Map` 열과 그 원본 진단(1번의 `kotlinc` 출력을 스크립트가 줄마다 읽었다).

**왜 그런가**

- ★★ `Map` 의 변환은 **`Map.Entry` 를 원소로 보는** `map`·`mapNotNull`·`flatMap` 과 **값만 바꾸는** `mapValues` 뿐이다(`flatMap` 은 람다가 `List` 를 돌려주는 꼴과 `Sequence` 를 돌려주는 꼴 두 행).
- ★ 나머지는 `Iterable` 확장이라 `Map` 이 받지 못한다 — 쓰려면 `m.entries` 나 `m.toList()` 로 **먼저 `Iterable` 로 바꾼다.** 그 꼴은 이 문서가 **던지지 않았다.**

### 6. 서명이 **`Iterable<T>.map(transform: (T) -> R): List<R>`** 이라 — `Set` 은 그 확장을 받을 뿐이고 `Set` 전용 `map` 은 없다

**왜 그런가**

- ★★★ 2-summary (3)의 발췌 — `1744:public inline fun <T, R> Iterable<T>.map(transform: (T) -> R): List<R> {`. 반환 타입 칸에 **`List<R>`** 가 적혀 있다.
- ★★ 세트의 「중복 없음」은 **그릇의 성질**이다. 그릇이 `List` 로 바뀌면 그 성질도 따라오지 않는다 — 그래서 **중복이 살아난다.**

### 7. **계약이다** — KDoc 이 「`the last one gets added to the map`」이라고 **약속한다** · 구현은 원소마다 `destination.put`

**왜 그런가**

- ★★★ 2-summary (3)의 발췌 — `associateBy` 의 KDoc 1372행과 `associateByTo` 의 `destination.put(keySelector(element), element)`.
- ★★ 그래서 「언젠가 예외를 던지게 고쳐질 것」을 기대하면 안 된다 — **키가 유일한지는 부르는 쪽이 보장**한다. 확인하려면 결과 `size` 를 입력 `size` 와 견준다(3번의 `size 5 -> 3`).

### 8. `toMap` 은 **`IllegalStateException: Duplicate key …`** 를 던진다 — `associateBy` 로 옮기면 **그 예외(=중복 검출)** 를 잃는다

**왜 그런가**

- ★★ [Java 47번](../../../java/syntax/47-collectors-basics/)이 실측했다 — 같은 입력에서 Java 는 던지고 Kotlin 은 **조용히 하나를 남긴다.** 이 문서는 Java 쪽을 **다시 돌리지 않았다.**
- ★ Java 코드가 그 예외로 「중복이면 실패」를 표현하고 있었다면, 옮긴 Kotlin 코드는 **잘못된 데이터를 통과시킨다.** 중복 검사를 따로 둔다(`groupBy` 후 크기 확인 등).

### 9. **타입 인자는 런타임에 지워진다** — 실행으로는 `List<Int>` 의 `<Int>` 도, `List` 와 `Iterable` 의 차이도 못 본다 · 이 창은 **정적 타입만** 보고 **런타임 클래스는 못 본다**

**왜 그런가**

- ★★ 컴파일러는 소스에서 **정적 타입**을 계산해 두고 있으므로, 맞지 않는 자리에 넣으면 **그 타입을 글자로** 적는다. 지어낼 수 없다.
- ★ 반대로 런타임 클래스(`ArrayList`·`LinkedHashMap`)는 이 창에 안 나온다 — 3번처럼 **실행 창**으로 따로 물었다. 둘은 **다른 질문**이다.

### 10. **말할 수 없다** — 1번은 「**결과 타입이 `Sequence` 로 남는다**」는 컴파일 사실뿐이다 · 빠른지는 **중간 컬렉션 수와 시간을 재야** 안다

**왜 그런가**

- ★★ `Sequence` 가 지연 평가라는 것, 중간 리스트를 안 만든다는 것, 그래서 **언제 이득이고 언제 손해인지**는 목록의 **47번 주제**의 몫이다. 이 문서는 시간도 할당도 **재지 않았다.**
- ★ 게다가 `unzip`·`associate*` 에서는 `Sequence` 가 **끝난다**(2번) — 「사슬 전체가 지연」이라는 가정부터 틀릴 수 있다.

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

★ **흔들리는 칸과 안 흔들리는 칸**

| 흔들린다 | 안 흔들린다 |
|---|---|
| **없다** — 해시코드·주소·시간을 찍지 않았다 | 격자 13행 × 5열 · 갈린 칸 수 · 실행 출력 |
| | stdlib 소스 발췌(줄 번호째) |
| | 진단의 **문구·`파일:줄:칸`·캐럿** · 모든 **종료 코드** |

> 근거 — 캡처 스크립트를 처음부터 다시 돌려 **블록 전체를 대조**했다.
>
> 실측 — `capture.sh blocks` 와 `capture.sh blocks-recheck` 를 처음부터 따로 돌려 `normalize-shaky.py` 로 대조했다 —\
> **블록 60개 · 동일 59 · 흔들린 칸 1 · ★고칠 것 0**(42\~45 네 주제를 한 캡처로 받았다). 흔들린 1블록은 44번의 Rust 패닉 블록(`a44-rs`)이고, 원문 차이는 **패닉 첫 줄의 스레드 id** 하나였다 — 기본 정규화 규칙(스레드 id)이 그것을 지웠다.\
> ★ 추가한 정규화 규칙은 **없다**.

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `type42.kt` · `grid42.py` | ★★★ 결과 타입 격자 — 13연산 × 5입력 | 스크립트가 `kotlinc` 를 부르고 진단을 줄마다 읽는다(실패가 결과) |
| `type42.kt` | 진단 원문 앞 6줄 | `kotlinc` → `sed -n '1,6p'`(캡처는 전부 받은 뒤 거른다) |
| `shape42.kt` | ★★ `Set.map` · `associateBy` 충돌 로그 · `zip` · `Map.map` 대 `mapValues` · `flatMap{seq}` | `kotlinc` → `java` |
| `_Collections.kt` · `_Maps.kt` · `Maps.kt`(stdlib 소스 jar) | `map`·`withIndex`·`Map.map`·`mapValues` 서명 · `associateBy` KDoc · `zip` KDoc · `flatMap{seq}` 선언 | `unzip` → `grep`·`sed -n` |
| `form42.kt` | 형태 한 벌 | `kotlinc` → `java` |

**구현 의존 항목** — 결과의 **런타임 클래스**(`ArrayList`·`LinkedHashMap`) · 덮어쓰기가 `put` 한 줄에서 나는 것 · 진단 문구 — 이 stdlib·컴파일러 판의 산출물이다.\
반면 **결과 타입(서명)** · **`associateBy` 의 마지막이 이긴다** · **`zip` 의 짧은 쪽** 은 **API 계약**이다.

**★ 던져 봤더니 예상과 달랐던 것 — 세 건**

1. ★★ **`Map` 에는 `associate`·`associateBy`·`associateWith` 가 없었다** — 맵에서 맵을 새로 짜는 일은 `mapValues`·`mapKeys` 나 `entries` 를 거쳐야 한다(1번·5번).
2. ★★ **`withIndex()` 가 `List` 가 아니었다** — `Iterable<IndexedValue<…>>` 라 인덱스 접근이 안 된다(1번).
3. ★ **`Sequence.unzip()` 이 `Sequence` 가 아니었다** — 지연 사슬이 거기서 끝난다(2번).
