# kotlin/syntax/42 — 변환 연산 — `map`/`flatMap`/`associate`/`zip` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Collection transformation operations](https://kotlinlang.org/docs/collection-transformations.html)(매핑 `map`·`mapNotNull`·`mapIndexed` · 지퍼 `zip`·`unzip` · 연관 `associateWith`·`associateBy`·`associate` · 평탄화 `flatten`·`flatMap`) — 이 문서는 그 페이지의 **목록**을 따르되, 문장은 인용하지 않고 **이 판의 stdlib 소스 jar**(`kotlin-stdlib-sources.jar` 2.4.20)의 KDoc 과 선언을 근거로 삼는다((3)).
> **실행 검증** — 이 문서의 모든 출력·에러는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `java` 에서 실제로 얻었다.\
> `kotlinc` 4회(같은 파일의 컴파일 실패 2벌 — 그 실패가 결과다) · `java` 2회 · stdlib 소스 jar 에서 4곳.\
> ★★ 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적지 않았다. **「갈린 칸 N / M」은 스크립트가 스스로 센 것**이다.
> **버전** — `map`·`flatMap`·`associate`·`associateBy`·`zip` 의 기본형은 **1.0** — 이 판의 소스에서 선언 위에 `@SinceKotlin` 이 **없다**(확인만 했고 발췌하지 않았다). `flatMap` 에 **`Sequence` 를 돌려주는 람다**를 받는 오버로드는 stdlib 소스에 **`@SinceKotlin("1.4")`**((3)) — ★ 그 전 판에서 어땠는지는 **이 판에서 잴 수 없다**(`-api-version` 은 2.0 미만을 안 받는다 — [43번 주제](../43-filter-search-and-empty-collections/) (4)).
> **경계** — 결과가 **새 리스트인가**(원본과 `===` 가 아닌가)는 [40번 주제](../40-read-only-collections-and-runtime-types/) (4)가 이미 쟀다 — `map`·`filter` 는 `=== src` 가 `false`. 여기서는 다시 재지 않고 **「어떤 모양(타입)으로 바꾸나」** 만 본다.\
> 만든 결과가 **복사인가 창인가**는 [41번 주제](../41-collection-creation-and-copying/)가 정본이다. `Sequence` 가 **즉시 평가가 아니라 지연 평가**라는 것과 그 비용은 [목록의 **47번 주제**](../47-sequences-lazy-evaluation/)다 — 여기 격자의 `Sequence` 열은 **컴파일러가 붙인 타입**만 말한다.
> 이 본문은 Claude 작성이다(원고 없음).

★★★ **본체는 첫째 창이다** — 「**결과 타입 격자 — 연산 × 입력 모양 → 컴파일러가 붙인 반환 타입**」. 타입은 **실행해서 찍으면 지워진다**(`List<Int>` 의 `<Int>` 는 런타임에 없다). 그래서 **일부러 타입이 안 맞는 자리에 넣고 컴파일러가 뭐라고 우기는지** 읽는다.

## 이 주제가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **언어 보장 / API 계약** | 서명·KDoc 이 약속한 것 | ★★★ **반환 타입**(서명) — `Iterable<T>.map` 은 `List<R>` · `Map.map` 은 `List<R>` · `mapValues` 는 `Map<K, R>` · ★★ KDoc 「**the last one gets added to the map**」(`associateBy`) · 「**length of the shortest collection**」(`zip`) |
| **구현(stdlib)** | 이 판의 stdlib 가 실제로 하는 것 | ★ `associateByTo` 가 **`destination.put`** 을 원소마다 부른다 — 덮어쓰기가 거기서 난다 · 결과 맵이 `LinkedHashMap` |
| **이 판의 관찰** | kotlinc 2.4.20 에서 이번에 본 것 | 진단 문구(`argument type mismatch: actual type is …`) · 없는 칸의 `unresolved reference` |

## 이 판

```text
===== kotlinc -version =====
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | (이 주제에는 없다) | 해시코드·주소·시간을 찍지 않았다 |
| 안 흔들린다 | 격자 13행 × 5열 · 갈린 칸 수 | 컴파일러 진단은 결정적이다 |
| 안 흔들린다 | 실행 출력(`Set.map` · `associateBy` 로그 · `zip`) | 단일 스레드 · 입력 순서가 고정된 `setOf`·`listOf`·`mapOf` 만 썼다 |
| 안 흔들린다 | stdlib 소스 발췌(줄 번호째) · 진단의 `파일:줄:칸` · 종료 코드 | jar·컴파일러가 같으면 같다 |

★ 근거 — 캡처 스크립트를 처음부터 두 번 돌려 **블록 전체를 대조**했다(수치는 3-answer 의 「실행 검증」).

## 한눈에 — 쉽게 말하면

**변환 연산은 「같은 물건을 다른 그릇에 옮겨 담는 일」이다 — 그런데 그릇은 대부분 연산이 정하지 입력이 정하지 않는다.** 세트(중복 없는 바구니)에 `map` 을 하면 결과는 **세트가 아니라 리스트**(줄 선 쟁반)다. 그래서 `setOf(1, 2, 3, 4).map { it % 2 }` 는 `[1, 0, 1, 0]` — 바구니였다면 사라졌을 중복이 **쟁반 위에서는 살아남는다.**
★ 반대로 **서랍장(`Map`)에 번호표를 붙여 넣는** `associateBy` 는 같은 번호표가 두 번 오면 **먼저 넣은 것을 말없이 꺼내 버린다.** 예외도 경고도 없다.

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 그릇은 연산이 정한다 | `Set.map` · `Array.map` · `Map.map` → 전부 `List` | (1) ★ |
| 지연 컨베이어는 컨베이어로 | `Sequence.map`·`filter`·`zip` → `Sequence` | (1) |
| 줄 선 쟁반 — 중복이 산다 | `Set.map { it % 2 }` → `[1, 0, 1, 0]` | (2) ★ |
| 번호표 서랍 — 같은 번호면 덮는다 | `associateBy` 키 충돌 → **마지막이 이긴다** | (2)(3) ★ |
| 두 줄을 지퍼로 — 짧은 쪽에서 멈춘다 | `zip` → 짧은 길이 | (2)(3) |
| 서랍장은 서랍장으로 | `mapValues` → `Map` (그러나 `map` 은 `List`) | (1)(2) |

```text
   입력 그릇                     연산                     결과 그릇 (컴파일러가 붙인 타입)
   List<Int>    ── map ──────────────────────────────>  List<Int>
   Set<Int>     ── map ──────────────────────────────>  List<Int>         ← 세트가 아니다 (중복이 산다)
   Array<Int>   ── map ──────────────────────────────>  List<Int>         ← 배열이 아니다
   Map<K,V>     ── map ──────────────────────────────>  List<R>           ← 맵이 아니다
   Map<K,V>     ── mapValues ────────────────────────>  Map<K,R>          ← 맵은 이쪽
   Sequence<T>  ── map ──────────────────────────────>  Sequence<T>       ← 지연은 지연으로
   Sequence<T>  ── unzip ────────────────────────────>  Pair<List,List>   ← 여기서 끝난다

   ["apple","avocado","banana"] ── associateBy { it.first() } ──> {a=avocado, b=banana}
                                     key a <- apple     (put)
                                     key a <- avocado   (put — apple 을 덮는다, 말없이)
```

## 이 주제가 답하려는 질문

1. 연산마다 결과 **그릇(타입)** 은 무엇인가 — 입력 모양을 **지키는** 칸과 **바꾸는** 칸은 어디인가.
2. 모양이 바뀔 때 **무엇이 조용히 달라지나** — 중복이 살아나고, 키 충돌이 덮이고, 긴 쪽이 잘린다.
3. 그 조용한 동작은 **계약(KDoc)** 인가 구현인가.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **결과 타입 격자(의도적 타입 불일치 진단)** | 연산 × 입력 → 컴파일러가 붙인 반환 타입 · 없는 칸((1)) | ★ **본체 창** |
| ★★ **실행 + 로그** | 중복이 사는가 · 키 충돌이 덮나 · 짧은 쪽에서 멈추나((2)) | — |
| ★★ **stdlib 소스 jar 발췌** | 그 동작이 **KDoc 계약**인가, 구현 한 줄인가((3)) | [41번 주제](../41-collection-creation-and-copying/) (2)와 같은 창 |
| **인용 — 다시 안 잰다** | 결과가 원본과 `===` 가 아닌 새 리스트다 | [40번 주제](../40-read-only-collections-and-runtime-types/) (4) |
| ★ **제5의 상태 — 창을 바꿔 물었다** | 「결과 타입이 무엇인가」를 **실행 창**으로는 못 묻는다(소거) — **컴파일 에러 창**으로 물었다 | (1) — 이 창은 **정적 타입**만 보고 런타임 클래스는 못 본다 |
| **부적용 — 실행 시간·할당** | 「`Sequence` 가 빠르다」·「`associateBy` 가 `groupBy` 보다 싸다」는 **재지 않았다** | — |

### (1) ★★★ 결과 타입 격자 — 컴파일러에게 타입을 말하게 한다

**언제 쓰나** — 연산 사슬 중간에서 「지금 손에 든 것이 `List` 인가 `Set` 인가 `Sequence` 인가」가 헷갈릴 때.

방법 — `fun t(x: Nothing?)` 는 **`null` 말고는 아무것도 못 받는다.** 거기에 변환 결과를 넘기면 컴파일러가 `argument type mismatch: actual type is '…'` 로 **실제 타입을 적어 준다.** 그런 연산이 **없으면** `unresolved reference` 가 난다. 각 줄 끝 주석이 격자 칸의 이름이다.

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

- ★★★ **입력 그릇을 지키는 칸은 53칸 중 16칸뿐이다** — `List` 가 `List` 로(7칸) · **`Sequence` 가 `Sequence` 로(8칸)** · `Map.mapValues` 가 `Map` 으로(1칸). 나머지 37칸은 **연산이 그릇을 정했다.**
- ★★★ **`Set` 열에 `Set` 은 한 칸도 없다** — `map`·`mapNotNull`·`flatMap`·`flatten`·`mapIndexed`·`zip` 이 모두 `List` 다. 서명이 `Iterable<T>.map(…): List<R>` 이라 `Set` 도 그 확장을 받는다((3)).
- ★★ **`Array` 열도 배열로 안 돌아온다** — `a.map { it }` 은 `Array<Int>` 가 아니라 `List<Int>` 다.
- ★★ **`Map` 열은 넷만 있다** — `map`·`mapNotNull`·`flatMap`·`flatMap{seq}` 은 전부 **`List`**, `mapValues` 만 `Map` 이다. `Map` 은 `Iterable` 이 아니라서 `flatten`·`associate*`·`zip`·`unzip`·`withIndex`·`mapIndexed` 가 **`unresolved reference`** 다.
- ★★ **`flatMap` 에 `Sequence` 를 돌려주는 람다(`flatMap{seq}`)도 컴파일된다** — `List`·`Set`·`Map`·`Array` 에서 결과는 **`List`** 다. 람다가 무엇을 돌려주든 **받는 쪽 그릇이 결과를 정한다.**
- ★ **`withIndex()` 는 `List` 가 아니라 `Iterable<IndexedValue<Int>>`** 다(`List`·`Set`·`Array` 모두) — 인덱스로 `[i]` 접근을 못 한다. `Sequence` 는 `Sequence<IndexedValue<Int>>`.
- ★ **`Sequence.unzip()` 은 `Pair<List, List>`** — 격자의 `Sequence` 열에서 **유일하게 `Sequence` 가 아닌 결과**다. 지연 컨베이어가 여기서 **끝난다**(두 리스트를 채워야 하므로).
- ★ `associate`·`associateBy`·`associateWith` 는 입력이 무엇이든 **`Map`** 이다(`Sequence` 도).

### (2) ★★ 모양이 바뀔 때 조용히 달라지는 것

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

- ★★★ **`Set.map { it % 2 }` 는 `[1, 0, 1, 0]`**(`size 4`) — 세트에서 출발했지만 결과가 `List` 라 **중복이 살아난다.** 세트로 받고 싶으면 `mapTo(mutableSetOf())` 처럼 **그릇을 직접 준다**(`2 [1, 0]`).
- ★★★ **`associateBy` 는 키가 겹치면 마지막이 이긴다** — 로그에 `key a` 가 두 번(`apple`·`avocado`), `key b` 가 두 번 찍혔고 결과는 `{a=avocado, b=blueberry, c=cherry}`, **5개가 3개**가 됐다. 예외도 경고도 없다. ★ 전부 남기려면 **`groupBy`**(`4`) — 그쪽은 [44번 주제](../44-aggregation-grouping-fold-reduce/)의 몫이다.
- ★★ **`zip` 은 짧은 쪽에서 멈춘다** — 3개와 2개를 묶으면 `[(1, a), (2, b)]` 두 쌍이다. `3` 은 **말없이 버려졌다.** 변환 람다를 주는 꼴(`6`)도 같다.
- ★★ **`Map.map` 은 `List`(`java.util.ArrayList`), `mapValues` 는 `Map`(`java.util.LinkedHashMap`)** — 이름은 비슷한데 **그릇이 다르다.** 키를 지키려면 `mapValues`.
- ★ **`flatMap { sequenceOf(…) }` 의 결과는 `[1, 10, 2, 20]` 인 `ArrayList`** — 람다가 `Sequence` 를 돌려줘도 **리스트 쪽 `flatMap` 이 다 펼쳐 담는다.**

### (3) ★★ 그 동작은 계약인가 — stdlib 소스

```text
===== unzip -o -q kotlin-stdlib-sources.jar commonMain/generated/_Collections.kt commonMain/generated/_Maps.kt commonMain/kotlin/collections/Maps.kt commonMain/kotlin/collections/SlidingWindow.kt jvmMain/generated/_CollectionsJvm.kt =====
(exit 0)
```

```text
===== grep -n -E '^public inline fun <T, R> Iterable<T>\.map\(|^public fun <T> Iterable<T>\.withIndex\(' commonMain/generated/_Collections.kt =====
1744:public inline fun <T, R> Iterable<T>.map(transform: (T) -> R): List<R> {
1829:public fun <T> Iterable<T>.withIndex(): Iterable<IndexedValue<T>> {
(exit 0)
===== grep -n -E '^public inline fun <K, V, R> Map<out K, V>\.map\(' commonMain/generated/_Maps.kt =====
128:public inline fun <K, V, R> Map<out K, V>.map(transform: (Map.Entry<K, V>) -> R): List<R> {
(exit 0)
===== grep -n -E '^public inline fun <K, V, R> Map<out K, V>\.mapValues\(' commonMain/kotlin/collections/Maps.kt =====
609:public inline fun <K, V, R> Map<out K, V>.mapValues(transform: (Map.Entry<K, V>) -> R): Map<K, R> {
(exit 0)
===== sed -n '1372p;1407,1412p' commonMain/generated/_Collections.kt =====
 * If any two elements would have the same key returned by [keySelector] the last one gets added to the map.
public inline fun <T, K, M : MutableMap<in K, in T>> Iterable<T>.associateByTo(destination: M, keySelector: (T) -> K): M {
    for (element in this) {
        destination.put(keySelector(element), element)
    }
    return destination
}
(exit 0)
===== sed -n '3857,3858p;3862,3864p' commonMain/generated/_Collections.kt =====
 * Returns a list of pairs built from the elements of `this` collection and [other] collection with the same index.
 * The returned list has length of the shortest collection.
public infix fun <T, R> Iterable<T>.zip(other: Iterable<R>): List<Pair<T, R>> {
    return zip(other) { t1, t2 -> t1 to t2 }
}
(exit 0)
===== sed -n '1558,1562p' commonMain/generated/_Collections.kt =====
@SinceKotlin("1.4")
@OptIn(kotlin.experimental.ExperimentalTypeInference::class)
@OverloadResolutionByLambdaReturnType
@kotlin.jvm.JvmName("flatMapSequence")
public inline fun <T, R> Iterable<T>.flatMap(transform: (T) -> Sequence<R>): List<R> {
(exit 0)
```

- ★★★ **`associateBy` 의 덮어쓰기는 KDoc 계약이다** — 「`If any two elements would have the same key returned by [keySelector] the last one gets added to the map.`」. 구현은 `associateByTo` 가 **원소마다 `destination.put`** 을 부르는 것이고, `put` 은 같은 키면 값을 **바꾼다.** 조용한 것은 **버그가 아니라 약속된 동작**이다.
- ★★ **`zip` 의 「짧은 쪽」도 KDoc 계약이다** — 「`The returned list has length of the shortest collection.`」.
- ★★ **`Set.map` 이 `List` 인 이유는 서명**이다 — `public inline fun <T, R> Iterable<T>.map(transform: (T) -> R): List<R>`. `Set` 전용 `map` 은 **없다.** `Map` 쪽도 `Map<out K, V>.map(…): List<R>` · `mapValues(…): Map<K, R>` 로 **서명이 그릇을 적는다.**
- ★ `withIndex` 의 서명도 `Iterable<IndexedValue<T>>` 를 적는다 — 격자와 같다.
- ★ **`flatMap` 의 `Sequence` 오버로드**는 `@SinceKotlin("1.4")` · `@OverloadResolutionByLambdaReturnType` · `@JvmName("flatMapSequence")` 를 달고 있다 — 람다의 **반환 타입으로** 오버로드를 고르고, JVM 에서는 **이름을 바꿔** 두 `flatMap` 이 충돌하지 않게 한 것이다.

```text
   결과 그릇을 누가 정하나                    근거
   ─────────────────────────────────────────────────────────────────────────────
   Iterable<T>.map(...)        : List<R>      서명 — Set 도 이 줄을 탄다
   Map<out K, V>.map(...)      : List<R>      서명
   Map<out K, V>.mapValues(...): Map<K, R>    서명
   Sequence<T>.map(...)        : Sequence<R>  (1) 격자 — 이 문서는 선언을 싣지 않았다
   associateBy 의 키 충돌      : 마지막이 이긴다   KDoc 계약 + put 구현
   zip 의 길이                 : 짧은 쪽           KDoc 계약
```

## 문법 — 형태와 규칙

**형태** — 주문 목록 하나로 네 가지 변환을 한 번씩.

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

**규칙 불릿**

- **결과 그릇은 대개 연산이 정한다** — `map`·`mapNotNull`·`flatMap`·`flatten`·`mapIndexed`·`zip` 은 `List`, `associate*` 는 `Map`, `unzip` 은 `Pair<List, List>`((1)).
- **`Sequence` 는 `Sequence` 로 남는다** — 단 `unzip`·`associate*` 는 거기서 끝난다((1)).
- **`Map` 을 `Map` 으로 바꾸려면 `mapValues`**(또는 `mapKeys`) — `map` 은 `List` 다((1)(2)).
- **`associateBy` 는 키가 겹치면 마지막 값만 남는다** — 전부 남기려면 `groupBy`((2)(3)). `byUser` 줄이 `{kim=3, lee=2}` 인 이유 — `kim` 의 1번 주문이 3번에 **덮였다.**
- **`zip` 은 짧은 쪽 길이**((2)(3)).

## 어디서 틀리나

1. ★★★ **`Set` 에 `map` 하면 `Set` 이 나온다고 믿는다.** `List` 다 — 중복이 살아난다((1)(2)). `.toSet()` 을 붙이거나 `mapTo(mutableSetOf())`.
2. ★★★ **`associateBy` 로 「id → 객체」 맵을 만들며 id 가 유일하다고 가정한다.** 겹치면 **조용히 하나만 남는다**((2)). Java `Collectors.toMap` 은 같은 자리에서 **`IllegalStateException`** 을 던진다([Java 47번](../../../java/syntax/47-collectors-basics/)) — Java 에서 옮겨 온 코드가 여기서 **예외를 잃는다.**
3. ★★ **`Map.map { }` 의 결과를 맵으로 쓴다.** `List` 다 — `mapValues`((1)(2)).
4. ★★ **길이가 다른 두 리스트를 `zip` 하고 결과 길이를 확인하지 않는다.** 긴 쪽 꼬리가 **말없이** 버려진다((2)).
5. ★ **`withIndex()` 의 결과에 `[i]` 를 쓴다.** `Iterable` 이다((1)).
6. ★ **`Sequence` 사슬 중간에 `unzip` 을 넣고 지연이 이어진다고 본다.** `Pair<List, List>` — 거기서 다 당겨진다((1)).
7. ★ **`Array.map` 이 배열을 돌려준다고 본다.** `List` 다((1)).

## 구현 세부사항 대 언어 보장

| 항목 | 어느 쪽인가 | 근거 |
|---|---|---|
| 연산마다 결과 **타입**(`Set.map` → `List` 등) | ★★★ **API 계약(서명)** | (1)(3) |
| `associateBy` 키 충돌 → 마지막이 이긴다 | ★★★ **API 계약(KDoc)** | (3) |
| `zip` → 짧은 쪽 길이 | ★★ **API 계약(KDoc)** | (3) |
| 덮어쓰기가 `put` 한 줄에서 난다 | ★ **stdlib 구현** | (3) |
| `mapValues` 결과가 `LinkedHashMap` · `Map.map` 결과가 `ArrayList` | ★ **stdlib 구현**(런타임 클래스) — 계약은 `Map`·`List` 까지 | (2) |
| `flatMap{seq}` 오버로드의 `@SinceKotlin("1.4")` | **stdlib 판의 사실** — 그 전 판에서는 **못 쟀다** | (3) |
| 진단 문구(`argument type mismatch: …`) | **이 판의 관찰** — 격자 스크립트가 문구 모양에 기대므로 **판이 오르면 다시 돌린다** | (1) |

★★ **가장 조심할 자리** — 「`associateBy` 가 조용히 덮는다」는 **구현 사고가 아니라 계약**이다. 그래서 「언젠가 고쳐지겠지」가 아니다 — 유일성은 **부르는 쪽이 보장**해야 한다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 원소마다 하나씩 바꾼다 | `map` | (1) — `List` |
| 바꾸다 `null` 인 것은 버린다 | `mapNotNull` | (1) |
| 원소마다 여러 개 → 한 줄로 | `flatMap` | (1) — 람다가 `Sequence` 를 돌려줘도 된다 |
| **유일한** 키로 찾는 맵 | `associateBy` | (2) — ★ 유일하지 않으면 **덮인다** |
| 키가 겹칠 수 있다 | ★ `groupBy` | (2) — 44번 주제 |
| 원소 → 값 맵 | `associateWith` | (1) |
| 맵의 값만 바꾼다 | `mapValues` | (1)(2) — `Map` 을 지킨다 |
| 두 줄을 짝짓는다 | `zip` | (2) — ★ 길이를 먼저 맞춘다 |
| 세트로 받고 싶다 | `mapTo(mutableSetOf())` 또는 `.toSet()` | (2) |

## 핵심 문장

1. 변환 연산의 결과 그릇은 **대개 연산이 정한다** — 53칸 중 37칸이 입력 모양을 바꿨고, 지킨 16칸은 `List`→`List` · `Sequence`→`Sequence` · `Map.mapValues` 뿐이다.
2. **`Set.map` 은 `List`** 다 — 중복이 살아난다.
3. **`associateBy` 는 키가 겹치면 마지막이 이긴다** — KDoc 이 약속한 **조용한 덮어쓰기**다.
4. **`zip` 은 짧은 쪽 길이**다 — 긴 쪽 꼬리는 말없이 버려진다.
5. **`Map.map` 은 `List`, `mapValues` 는 `Map`** 이다.

## 관련 자료

- [41번 주제](../41-collection-creation-and-copying/) — ★★★ **선행.** 그쪽은 「**만들 때** 무엇을 고르나 · 어디서 복사되나」, 여기는 「**있는 것을** 어떤 모양으로 바꾸나」.
- [40번 주제](../40-read-only-collections-and-runtime-types/) (4) — `map`·`filter` 결과가 **새 리스트**(`=== src` 가 `false`)다. 여기서 다시 재지 않았다.
- [28번 주제](../28-generics-variance-in-out-star-where/) — `Map<out K, V>` 의 `out`.
- [Java 47번](../../../java/syntax/47-collectors-basics/) — `Collectors.toMap` 은 키가 겹치면 **`IllegalStateException`** — 여기 `associateBy` 와 반대다.
- [44번 주제](../44-aggregation-grouping-fold-reduce/) — `groupBy`(겹치는 키를 전부 남긴다). [목록의 **47번 주제**](../47-sequences-lazy-evaluation/) — `Sequence` 의 지연 평가와 그 비용.

## 용어 풀이

> **변환 연산(transformation)** — 컬렉션에서 **새 컬렉션**을 만드는 연산. 원본은 안 바뀐다([40번 주제](../40-read-only-collections-and-runtime-types/) (4)).\
> 예: `listOf(1, 2).map { it * 10 }` → `[10, 20]`.

> **`associateBy`** — 원소에서 **키**를 뽑아 `Map<키, 원소>` 를 만든다. 키가 겹치면 **마지막 원소**가 남는다.

> **`associateWith`** — 원소를 **키**로, 람다 결과를 **값**으로 하는 `Map` 을 만든다.

> **`zip`** — 두 줄을 같은 인덱스끼리 `Pair` 로 묶는다. 길이는 **짧은 쪽**.

> **`unzip`** — `Pair` 의 줄을 **두 리스트**로 가른다. 결과는 `Pair<List, List>`.

> **`IndexedValue`** — `withIndex()` 가 원소마다 만드는 `(index, value)` 묶음.

> **의도적 타입 불일치** — 결과를 **맞지 않는 타입 자리**(`Nothing?`)에 넣어 컴파일러가 실제 타입을 에러 문구로 말하게 하는 기법. 이 문서가 붙인 이름이다.

## 더 들어가면

- **`Array` 전용 확장** — 격자는 `Array.map` 이 `List` 임을 보였을 뿐, `Array<T>.map` 선언이 `_Arrays.kt` 에 따로 있는지는 **소스를 열지 않았다.**
- **`Sequence` 쪽 선언** — `Sequence.map` 이 `Sequence<R>` 인 것은 격자로만 봤다. `_Sequences.kt` 는 **열지 않았다.**
- **`associate` 의 키 충돌** — `associateBy` 와 같은 KDoc 문장이 있을 것으로 보이지만 **발췌하지 않았다.**
