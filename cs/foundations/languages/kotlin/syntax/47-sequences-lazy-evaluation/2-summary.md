# kotlin/syntax/47 — `Sequence` — 지연 평가, 언제 `List` 보다 싼가 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Sequences](https://kotlinlang.org/docs/sequences.html)(만들기 `sequenceOf`·`asSequence`·`generateSequence`·`sequence { }` · 연산의 **상태 없음/상태 있음 · 중간/끝** 분류 · 처리 순서) — 이 문서는 그 페이지의 **목록**을 따르되, 문장은 인용하지 않고 **이 판의 stdlib 소스 jar**(`kotlin-stdlib-sources.jar` 2.4.20)의 KDoc 과 구현을 근거로 삼는다((3)(5)).
> **실행 검증** — 이 문서의 모든 출력·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `java`·`javap` 에서 실제로 얻었다.\
> `kotlinc` 6회 · `java` 6회 · `javap` 1회 · stdlib 소스 jar 에서 발췌 16곳.\
> ★★ 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적지 않았다. **「호출을 줄인 칸 N / M」은 격자 프로그램이 스스로 센 것**이다.
> **버전** — `Sequence`·`asSequence`·`generateSequence`·`constrainOnce` 는 **1.0**. `sequence { }` 빌더는 stdlib 소스에 **`@SinceKotlin("1.3")`**(이 판에서 읽었고 **발췌는 선언 한 줄만** — (5)).
> **경계** — ★★ **결과 타입**(`Sequence` 의 연산이 대부분 `Sequence` 로 남고 `unzip`·`associate*` 에서 끝난다)은 [42번 주제](../42-transformations-map-flatmap-associate-zip/) (1)이 격자로 쟀다 — 여기서는 인용만 한다. `List.sorted()` 가 `Arrays$ArrayList` 인 것은 [45번 주제](../45-sorting-and-partial-operations/) (1), `toList()` 가 원소 수로 클래스를 고르는 것은 [41번 주제](../41-collection-creation-and-copying/) (2)가 정본이다.\
> ★★ **같은 지연 평가의 Java 판**(`Stream` — 원소별 처리 · `sorted` 에서 막힘)은 [Java 45번](../../../java/syntax/45-intermediate-operations/)이, 만들기와 「한 번만 쓸 수 있다」는 [Java 44번](../../../java/syntax/44-stream-creation/)이, 끝 연산은 [Java 46번](../../../java/syntax/46-terminal-operations/)이 정본이다. **C# 의 지연 실행과 「두 번 열거하면 두 번 돈다」** 는 [C# 32번](../../../csharp/syntax/32-yield-return-iterators-and-deferred-execution/)이 쟀다.
> 이 본문은 Claude 작성이다(원고 없음).

★★★ **본체는 첫째 창이다** — 「**호출 수 격자 — 사슬 다섯 × (`List` · `asSequence()`) × 입력 크기(10 · 1000) → 람다 호출 수 · 끝 단계 앞에서 만들어진 컬렉션 수**」. 「싸다」를 **시간으로 재지 않는다** — 시간은 판을 타고, **호출 수와 컬렉션 수는 결정적**이다.

## 이 주제가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **언어 보장 / API 계약** | 서명·KDoc 이 약속한 것 | ★★ KDoc 의 분류 「`_intermediate_ and _stateless_`」(`map`·`filter`) · 「`_intermediate_ and _stateful_`」(`sorted`·`distinct`) · ★★ `Sequence` KDoc 「`Sequences can be iterated multiple times, however some … constrain themselves to be iterated only once`」 · `generateSequence(nextFunction)` 「`constrained to be iterated only once`」 |
| **구현(stdlib)** | 이 판의 stdlib 가 실제로 하는 것 | `Iterable.map` 이 **`ArrayList(collectionSizeOrDefault(10))`** · `filter` 가 **`ArrayList()`** · `Sequence.sorted` 가 **`toMutableList()` 후 `sort()`** · `distinct` 가 **`HashSet` 을 쥐고 원소마다** 흘린다 · 한 번 제한이 **`AtomicReference.getAndSet(null)`** · 래퍼 클래스 이름(`TransformingSequence`·`FilteringSequence`) |
| **이 판의 관찰** | kotlinc 2.4.20 에서 이번에 본 것 | 격자의 수 · `javap` 에 박힌 `new java/util/ArrayList` 개수 · 로그 순서 |

## 이 판

```text
===== kotlinc -version =====
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | (이 주제에는 없다) | ★★ **실행 시간을 찍지 않았다** — 한 판 시간은 근거가 아니고(규칙 24) 판 격자도 돌리지 않았다 |
| 안 흔들린다 | 격자 10행 · 호출 수 · 컬렉션 수 · 줄인 칸 수 | 람다 호출 횟수는 입력과 사슬만으로 정해진다 |
| 안 흔들린다 | 순서 로그 · 두 번 돌기 결과 · 래퍼 클래스 이름 | 단일 스레드 · 고정 입력 |
| 안 흔들린다 | stdlib 소스 발췌 · `javap` 의 명령·상수 풀 번호 · 종료 코드 | jar·컴파일러가 같으면 같다 |

★ 근거 — 캡처 스크립트를 처음부터 두 번 돌려 **블록 전체를 대조**했다(수치는 3-answer 의 「실행 검증」).

## 한눈에 — 쉽게 말하면

**`List` 사슬은 「공정마다 쟁반을 꽉 채워 다음 공정에 넘기는 공장」이고, `Sequence` 사슬은 「부품 하나가 끝까지 컨베이어를 탄 뒤 다음 부품이 올라오는 공장」이다.** 앞 공장은 쟁반(중간 리스트)이 공정 수만큼 생기고 **모든 부품이 모든 공정을 지난다.** 뒤 공장은 쟁반이 없고, 끝에서 「하나만 필요해」(`first`)라고 하면 **거기서 컨베이어가 멈춘다.**
★ 그러나 끝이 「전부 담아 줘」(`toList`)면 뒤 공장도 **모든 부품이 모든 공정을 지난다** — 컨베이어 설비(래퍼 객체)만 더 있을 뿐이다. 그리고 **「줄 세우기」(`sorted`) 공정은 부품을 전부 모아야** 시작할 수 있다.

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 공정마다 쟁반을 채운다 | `List.map` → `ArrayList` → `filter` → `ArrayList` | (1)(3) ★ |
| 부품 하나가 끝까지 간다 | `Sequence` 는 **원소별**로 `map` → `filter` | (2) ★ |
| 하나만 필요하면 멈춘다 | `first()`·`take(n)` 끝 — 호출이 줄었다 | (1) ★ |
| 전부 담으면 절약이 없다 | `map→filter→toList` — 호출 수가 **같다** | (1)(4) ★ |
| 줄 세우기는 다 모아야 | `sorted` 는 **첫 원소 전에 전부** 당긴다 | (2)(3) |
| 중복 검사는 모으지 않는다 | `distinct` 는 **본 것만 기억**하며 흘린다 | (2)(3) |
| 한 번 쓰고 버리는 컨베이어 | `generateSequence { }` · `Iterator.asSequence()` | (5) |

```text
   listOf(3, 1, 2)                         listOf(3, 1, 2).asSequence()
   .map { … }  .filter { … }               .map { … }  .filter { … }  .toList()

   map 3 ─┐                                map 3 → filter 30
   map 1  │ 쟁반 [30, 10, 20]              map 1 → filter 10
   map 2 ─┘                                map 2 → filter 20
   filter 30 ─┐                                        │
   filter 10  │ 쟁반 [30, 20]              쟁반은 끝의 toList 하나
   filter 20 ─┘
   (단계별 — 공정 순)                       (원소별 — 부품 순)
```

## 이 주제가 답하려는 질문

1. 사슬마다 **람다가 몇 번 불리고 중간 컬렉션이 몇 개 생기나** — `Sequence` 로 바꾸면 무엇이 줄고 무엇이 안 주나.
2. **순서가 어떻게 다른가** — 그리고 `sorted`·`distinct` 처럼 **상태를 쥐는** 단계는 그 순서를 어떻게 바꾸나.
3. `Sequence` 는 **두 번 돌 수 있나** — 누가 그것을 정하나.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **호출 수 격자(실행 · 결정적)** | 사슬 × 모양 × 크기 → 람다 호출 수 · 끝 단계 앞 컬렉션 수((1)) | ★ **본체 창** |
| ★★ **순서 로그** | 단계별 대 원소별 · `sorted`·`distinct` 가 끼면((2)) | — |
| ★★ **stdlib 소스 jar 발췌** | 중간 컬렉션을 **누가 어디서** 만드나 · 상태 있음/없음 분류((3)) | [41번 주제](../41-collection-creation-and-copying/) (2)와 같은 창 |
| ★★ **`javap -c`** | `List` 사슬 본문에 박힌 **`new java/util/ArrayList`** 개수((3)) | — |
| ★ **런타임 클래스** | 단계마다 무엇이 만들어지나 — 리스트인가 래퍼인가((4)) | — |
| **인용 — 다시 안 잰다** | `Sequence` 연산의 결과 **타입** | [42번 주제](../42-transformations-map-flatmap-associate-zip/) (1) |
| ★ **제5의 상태 — 창을 바꿔 물었다** | 「중간 컬렉션이 몇 개인가」를 **할당 계측**이 아니라 **단계 출력의 클래스 + 소스 발췌 + 바이트코드**로 물었다 | (1)(3) — 이 창은 **단계 안에 숨은** 컬렉션(`sorted` 의 내부 리스트·`distinct` 의 `HashSet`)을 **못 센다** — 그것은 소스 창이 맡는다 |
| **부적용 — 실행 시간** | ★★★ 「`Sequence` 가 빠르다/느리다」는 **재지 않았다** — 이 문서의 「싸다」는 **호출 수와 객체 수**뿐이다 | — |

### (1) ★★★ 호출 수 격자 — `Sequence` 가 무엇을 줄이나

**언제 쓰나** — `asSequence()` 를 넣을지 말지 정할 때.

방법 — 단계 이름(`map`·`filter`·`sorted`·`distinct`·`take3`·`first`·`toList`)을 받아 **받은 것이 `Sequence` 면 `Sequence` 연산을, 아니면 `List` 연산을** 부른다. 람다 `mf`(×2)·`ff`(`> 5`)는 부를 때마다 센다. `coll` 은 **끝 단계 앞에서 단계 출력이 `Collection` 이었던 횟수**다. ★ `List` 열의 `toList` 는 이미 리스트이므로 **받은 것을 그대로 돌려준다**(새로 만들지 않는다). 마지막 줄은 **`Sequence` 열의 호출 수 합이 더 작은 칸**을 센다.

```kotlin
// grid47.kt
@file:Suppress("UNCHECKED_CAST")

var mc = 0
var fc = 0
val mf: (Int) -> Int = { mc++; it * 2 }
val ff: (Int) -> Boolean = { fc++; it > 5 }

fun stage(name: String, x: Any): Any = when (x) {
    is Sequence<*> -> {
        val s = x as Sequence<Int>
        when (name) {
            "map" -> s.map(mf)
            "filter" -> s.filter(ff)
            "sorted" -> s.sorted()
            "distinct" -> s.distinct()
            "take3" -> s.take(3)
            "first" -> s.first()
            "toList" -> s.toList()
            else -> error(name)
        }
    }
    else -> {
        val l = x as List<Int>
        when (name) {
            "map" -> l.map(mf)
            "filter" -> l.filter(ff)
            "sorted" -> l.sorted()
            "distinct" -> l.distinct()
            "take3" -> l.take(3)
            "first" -> l.first()
            "toList" -> l
            else -> error(name)
        }
    }
}

val chains = listOf(
    listOf("map", "filter", "first"),
    listOf("map", "filter", "toList"),
    listOf("map", "sorted", "filter", "first"),
    listOf("map", "distinct", "filter", "first"),
    listOf("map", "filter", "take3", "toList"),
)

class Cell(val calls: Int, val text: String)

fun run(chain: List<String>, n: Int, lazy: Boolean): Cell {
    mc = 0; fc = 0
    var x: Any = if (lazy) (0 until n).toList().asSequence() else (0 until n).toList()
    var collections = 0
    for ((i, name) in chain.withIndex()) {
        x = stage(name, x)
        if (i < chain.lastIndex && x is Collection<*>) collections++
    }
    return Cell(mc + fc, "map=$mc filter=$fc coll=$collections")
}

fun main() {
    println(listOf("chain", "n", "List", "Sequence").joinToString("\t"))
    var fewer = 0
    var cells = 0
    for (chain in chains) {
        for (n in listOf(10, 1000)) {
            val a = run(chain, n, lazy = false)
            val b = run(chain, n, lazy = true)
            val row = listOf(chain.joinToString(">"), "$n", a.text, b.text)
            check(row.size == 4)
            println(row.joinToString("\t"))
            cells++
            if (b.calls < a.calls) fewer++
        }
    }
    println("cells where the Sequence column made fewer lambda calls: $fewer / $cells")
}
```

```text
===== kotlinc grid47.kt -d o47g =====
(exit 0)
===== java -cp o47g:kotlin-stdlib.jar Grid47Kt =====
chain	n	List	Sequence
map>filter>first	10	map=10 filter=10 coll=2	map=4 filter=4 coll=0
map>filter>first	1000	map=1000 filter=1000 coll=2	map=4 filter=4 coll=0
map>filter>toList	10	map=10 filter=10 coll=2	map=10 filter=10 coll=0
map>filter>toList	1000	map=1000 filter=1000 coll=2	map=1000 filter=1000 coll=0
map>sorted>filter>first	10	map=10 filter=10 coll=3	map=10 filter=4 coll=0
map>sorted>filter>first	1000	map=1000 filter=1000 coll=3	map=1000 filter=4 coll=0
map>distinct>filter>first	10	map=10 filter=10 coll=3	map=4 filter=4 coll=0
map>distinct>filter>first	1000	map=1000 filter=1000 coll=3	map=4 filter=4 coll=0
map>filter>take3>toList	10	map=10 filter=10 coll=3	map=6 filter=6 coll=0
map>filter>take3>toList	1000	map=1000 filter=1000 coll=3	map=6 filter=6 coll=0
cells where the Sequence column made fewer lambda calls: 8 / 10
(exit 0)
```

- ★★★ **10칸 중 8칸에서 `Sequence` 가 호출을 줄였다** — 끝이 `first()`·`take(3)` 인 사슬이다. `map>filter>first` 는 `List` 가 `1000 + 1000` 번, `Sequence` 는 **`4 + 4` 번** — 입력이 10 이든 1000 이든 **같다**(첫 합격 원소가 네 번째라서).
- ★★★ **줄이지 못한 두 칸은 `map>filter>toList`** — 크기 10 에서도 1000 에서도 **호출 수가 같다.** 끝이 전부를 요구하면 모든 원소가 모든 단계를 지난다.
- ★★ **`sorted` 가 끼면 `map` 은 전부 불린다** — `map>sorted>filter>first` 의 `Sequence` 열은 `map=1000`·`filter=4`. `sorted` **앞**은 전부, **뒤**만 줄었다.
- ★★ **`distinct` 가 끼어도 `map` 이 줄었다** — `map=4 filter=4`. `distinct` 는 상태를 쥐지만 **전부 모으지는 않는다**((2)(3)).
- ★★ **`List` 열은 단계마다 컬렉션을 만든다** — `coll=2`(map·filter) · `sorted`·`distinct`·`take3` 가 끼면 `coll=3`. **`Sequence` 열은 전부 `coll=0`** — 단계 출력이 전부 래퍼다((4)).
- ★ `coll=0` 은 「컬렉션이 **하나도** 없다」가 아니다 — `sorted` 는 안에서 리스트를, `distinct` 는 `HashSet` 을, 끝의 `toList` 는 `ArrayList` 를 만든다((3)). 이 창은 **단계 출력**만 본다.

### (2) ★★★ 순서 — 단계별 대 원소별

```kotlin
// order47.kt
fun main() {
    val src = listOf(3, 1, 2)
    println("-- A")
    src.map { println("  map $it"); it * 10 }
        .filter { println("  filter $it"); it > 10 }
        .also { println("  result $it") }
    println("-- B")
    src.asSequence()
        .map { println("  map $it"); it * 10 }
        .filter { println("  filter $it"); it > 10 }
        .toList()
        .also { println("  result $it") }
    println("-- C")
    src.asSequence()
        .map { println("  map $it"); it * 10 }
        .sorted()
        .filter { println("  filter $it"); it > 10 }
        .first()
        .also { println("  result $it") }
    println("-- D")
    listOf(3, 3, 1, 2).asSequence()
        .map { println("  map $it"); it * 10 }
        .distinct()
        .filter { println("  filter $it"); it < 25 }
        .first()
        .also { println("  result $it") }
    println("-- E")
    val pending = src.asSequence().map { println("  map $it"); it * 10 }
    println("-- F")
    println("  ${pending::class.java.name}")
}
```

```text
===== kotlinc order47.kt -d o47o =====
(exit 0)
===== java -cp o47o:kotlin-stdlib.jar Order47Kt =====
-- A
  map 3
  map 1
  map 2
  filter 30
  filter 10
  filter 20
  result [30, 20]
-- B
  map 3
  filter 30
  map 1
  filter 10
  map 2
  filter 20
  result [30, 20]
-- C
  map 3
  map 1
  map 2
  filter 10
  filter 20
  result 20
-- D
  map 3
  filter 30
  map 3
  map 1
  filter 10
  result 10
-- E
-- F
  kotlin.sequences.TransformingSequence
(exit 0)
```

- ★★★ **`A`(`List`)는 단계별** — `map 3·1·2` 가 다 끝난 뒤 `filter 30·10·20`. **`B`(`Sequence`)는 원소별** — `map 3 → filter 30 → map 1 → filter 10 …`. 결과는 둘 다 `[30, 20]` 이다 — **값이 아니라 순서가 다르다.**
- ★★★ **`C`(`sorted` 낀 `Sequence`)는 `map` 셋이 먼저 다 돈다** — 정렬하려면 전부 봐야 하므로 **첫 원소를 내기 전에 앞쪽을 끝까지 당긴다.** 그 뒤는 다시 원소별이라 `filter` 는 `10`·`20` 두 번에서 멈췄다(`first`).
- ★★ **`D`(`distinct` 낀 `Sequence`)는 원소별로 흐른다** — `map 3 → filter 30`(탈락) → `map 3`(중복이라 **`filter` 까지 안 간다**) → `map 1 → filter 10`(합격, 멈춤). **`distinct` 는 전부 끌어오지 않는다.**
- ★★ **`E`\~`F` 사이에 아무것도 없다** — 끝 연산이 없는 `Sequence` 는 **람다를 한 번도 안 부른다.** `pending` 은 `TransformingSequence` 라는 **「만드는 방법」** 일 뿐이다.
- ★ 같은 모양이 Java `Stream` 에도 있다 — 원소별 처리와 `sorted` 에서 막히는 것은 [Java 45번](../../../java/syntax/45-intermediate-operations/)이 쟀다(이 문서는 Java 를 다시 돌리지 않았다).

### (3) ★★ 중간 컬렉션은 누가 만드나 — stdlib 소스와 바이트코드

```text
===== unzip -o -q kotlin-stdlib-sources.jar commonMain/kotlin/collections/Maps.kt commonMain/kotlin/collections/MapWithDefault.kt jvmMain/kotlin/collections/MapsJVM.kt jvmMain/kotlin/Collections.kt commonMain/generated/_Sequences.kt commonMain/generated/_Collections.kt commonMain/kotlin/collections/Sequence.kt commonMain/kotlin/collections/Sequences.kt jvmMain/kotlin/collections/SequencesJVM.kt commonMain/kotlin/text/Strings.kt jvmMain/kotlin/text/CharJVM.kt jvmMain/kotlin/text/regex/Regex.kt commonMain/kotlin/util/Result.kt commonMain/kotlin/collections/SequenceBuilder.kt =====
(exit 0)
```

```text
===== sed -n '1744,1746p' commonMain/generated/_Collections.kt =====
public inline fun <T, R> Iterable<T>.map(transform: (T) -> R): List<R> {
    return mapTo(ArrayList<R>(collectionSizeOrDefault(10)), transform)
}
(exit 0)
===== sed -n '776,778p' commonMain/generated/_Collections.kt =====
public inline fun <T> Iterable<T>.filter(predicate: (T) -> Boolean): List<T> {
    return filterTo(ArrayList<T>(), predicate)
}
(exit 0)
===== sed -n '1209,1216p' commonMain/generated/_Collections.kt =====
public fun <T : Comparable<T>> Iterable<T>.sorted(): List<T> {
    if (this is Collection) {
        if (size <= 1) return this.toList()
        @Suppress("UNCHECKED_CAST")
        return (toTypedArray<Comparable<T>>() as Array<T>).apply { sort() }.asList()
    }
    return toMutableList().apply { sort() }
}
(exit 0)
===== sed -n '1841,1843p' commonMain/generated/_Collections.kt =====
public fun <T> Iterable<T>.distinct(): List<T> {
    return this.toMutableSet().toList()
}
(exit 0)
===== sed -n '995,1006p' commonMain/generated/_Sequences.kt =====
public fun <T> Sequence<T>.toList(): List<T> {
    val it = iterator()
    if (!it.hasNext())
        return emptyList()
    val element = it.next()
    if (!it.hasNext())
        return listOf(element)
    val dst = ArrayList<T>()
    dst.add(element)
    while (it.hasNext()) dst.add(it.next())
    return dst
}
(exit 0)
```

- ★★★ **`Iterable.map` 은 `ArrayList(collectionSizeOrDefault(10))`, `filter` 는 `ArrayList()`** 에 담는다 — 단계 하나 = 새 리스트 하나. `sorted` 는 원소를 **배열로 복사해 정렬한 뒤 `asList()`**, `distinct` 는 **`toMutableSet().toList()`** — 두 번 옮긴다.
- ★★ **`Sequence.toList` 는 `ArrayList<T>()`**(크기 없이) — 원소가 몇 개인지 **미리 모르기 때문**이다. 원소 0·1 개면 `emptyList()`·`listOf(element)`([41번 주제](../41-collection-creation-and-copying/) (2)의 클래스들).

```text
===== sed -n '1259p;1263,1265p' commonMain/generated/_Sequences.kt =====
 * The operation is _intermediate_ and _stateless_.
public fun <T, R> Sequence<T>.map(transform: (T) -> R): Sequence<R> {
    return TransformingSequence(this, transform)
}
(exit 0)
===== sed -n '431p;435,437p' commonMain/generated/_Sequences.kt =====
 * The operation is _intermediate_ and _stateless_.
public fun <T> Sequence<T>.filter(predicate: (T) -> Boolean): Sequence<T> {
    return FilteringSequence(this, true, predicate)
}
(exit 0)
===== sed -n '760,770p' commonMain/generated/_Sequences.kt =====
 * The operation is _intermediate_ and _stateful_.
 */
public fun <T : Comparable<T>> Sequence<T>.sorted(): Sequence<T> {
    return object : Sequence<T> {
        override fun iterator(): Iterator<T> {
            val sortedList = this@sorted.toMutableList()
            sortedList.sort()
            return sortedList.iterator()
        }
    }
}
(exit 0)
===== sed -n '1374p;1378,1380p' commonMain/generated/_Sequences.kt =====
 * The operation is _intermediate_ and _stateful_.
public fun <T> Sequence<T>.distinct(): Sequence<T> {
    return this.distinctBy { it }
}
(exit 0)
===== sed -n '617,618p;625,628p' commonMain/kotlin/collections/Sequences.kt =====
private class DistinctIterator<T, K>(private val source: Iterator<T>, private val keySelector: (T) -> K) : AbstractIterator<T>() {
    private val observed = HashSet<K>()
            if (observed.add(key)) {
                setNext(next)
                return
            }
(exit 0)
```

- ★★★ **`map`·`filter` 는 「`_intermediate_ and _stateless_`」, `sorted`·`distinct` 는 「`_intermediate_ and _stateful_`」** — KDoc 이 분류를 **글자로** 적는다. 구현은 `TransformingSequence`·`FilteringSequence` **래퍼를 돌려줄 뿐** 아무것도 돌지 않는다.
- ★★★ **「상태 있음」의 뜻이 둘이다** — `sorted` 는 `iterator()` 를 부르는 순간 **`toMutableList()` 로 전부 모은다.** `distinct` 는 **`HashSet` 하나(`observed`)** 를 쥐고 **원소마다** `add` 가 참이면 내보낸다. 둘 다 「상태 있음」이지만 **앞쪽을 끝까지 당기는 것은 `sorted` 뿐**이다((2)의 `C` 대 `D`).

```kotlin
// code47.kt
fun viaList(l: List<Int>): Int = l.map { it * 2 }.filter { it > 5 }.first()

fun viaSequence(l: List<Int>): Int = l.asSequence().map { it * 2 }.filter { it > 5 }.first()

fun main() {
    println("${viaList(listOf(1, 2, 3, 4))} ${viaSequence(listOf(1, 2, 3, 4))}")
}
```

```text
===== kotlinc code47.kt -d o47c =====
(exit 0)
===== java -cp o47c:kotlin-stdlib.jar Code47Kt =====
6 6
(exit 0)
===== javap -c -p o47c/Code47Kt.class | grep -E 'public static final int|new .*ArrayList|SequencesKt|CollectionsKt' =====
  public static final int viaList(java.util.List<java.lang.Integer>);
      15: new           #20                 // class java/util/ArrayList
      22: invokestatic  #26                 // Method kotlin/collections/CollectionsKt.collectionSizeOrDefault:(Ljava/lang/Iterable;I)I
     114: new           #20                 // class java/util/ArrayList
     202: invokestatic  #71                 // Method kotlin/collections/CollectionsKt.first:(Ljava/util/List;)Ljava/lang/Object;
  public static final int viaSequence(java.util.List<java.lang.Integer>);
      10: invokestatic  #95                 // Method kotlin/collections/CollectionsKt.asSequence:(Ljava/lang/Iterable;)Lkotlin/sequences/Sequence;
      18: invokestatic  #121                // Method kotlin/sequences/SequencesKt.map:(Lkotlin/sequences/Sequence;Lkotlin/jvm/functions/Function1;)Lkotlin/sequences/Sequence;
      26: invokestatic  #132                // Method kotlin/sequences/SequencesKt.filter:(Lkotlin/sequences/Sequence;Lkotlin/jvm/functions/Function1;)Lkotlin/sequences/Sequence;
      29: invokestatic  #135                // Method kotlin/sequences/SequencesKt.first:(Lkotlin/sequences/Sequence;)Ljava/lang/Object;
      41: invokestatic  #143                // Method kotlin/collections/CollectionsKt.listOf:([Ljava/lang/Object;)Ljava/util/List;
      89: invokestatic  #143                // Method kotlin/collections/CollectionsKt.listOf:([Ljava/lang/Object;)Ljava/util/List;
(exit 0)
```

- ★★ **`viaList` 의 본문에 `new java/util/ArrayList` 가 두 번** — `map`·`filter` 가 `inline` 이라 **리스트를 만드는 코드가 호출한 함수 안에 풀려 있다.** `viaSequence` 에는 **하나도 없고** `SequencesKt.map`·`filter`·`first` 호출만 있다.

### (4) ★★ 손해인 경우 — 호출은 같고 객체만 는다

```kotlin
// kinds47.kt
fun main() {
    val l = (0 until 10).toList()
    val a1 = l.map { it * 2 }
    val a2 = a1.filter { it > 5 }
    println("List      ${l::class.java.name} > ${a1::class.java.name} > ${a2::class.java.name}")
    val s0 = l.asSequence()
    val s1 = s0.map { it * 2 }
    val s2 = s1.filter { it > 5 }
    val s3 = s2.toList()
    println("Sequence  ${s0::class.java.name} > ${s1::class.java.name} > ${s2::class.java.name} > ${s3::class.java.name}")
    val t = s2.sorted()
    println("sorted    ${t::class.java.name}")
    val u = s2.distinct()
    println("distinct  ${u::class.java.name}")
}
```

```text
===== kotlinc kinds47.kt -d o47k =====
(exit 0)
===== java -cp o47k:kotlin-stdlib.jar Kinds47Kt =====
List      java.util.ArrayList > java.util.ArrayList > java.util.ArrayList
Sequence  kotlin.collections.CollectionsKt___CollectionsKt$asSequence$$inlined$Sequence$1 > kotlin.sequences.TransformingSequence > kotlin.sequences.FilteringSequence > java.util.ArrayList
sorted    kotlin.sequences.SequencesKt___SequencesKt$sorted$1
distinct  kotlin.sequences.DistinctSequence
(exit 0)
```

- ★★★ **`map>filter>toList` 에서 `Sequence` 는 호출을 하나도 못 줄였고**((1)의 두 칸), 대신 **래퍼 셋**(`asSequence` 가 만든 익명 `Sequence` → `TransformingSequence` → `FilteringSequence`)과 **그 각각의 반복자**를 더 만든다. 끝에는 결국 `ArrayList` 하나를 만든다 — `List` 사슬의 **마지막 리스트와 같은 몫**이다.
- ★★ 그러니 **사슬이 짧고 끝이 `toList` 면** `Sequence` 가 아끼는 것은 **중간 리스트 하나**(여기서는 `map` 의 것)이고, 더 드는 것은 **래퍼·반복자 객체**다. ★ **그 저울이 시간으로 어느 쪽인지는 이 문서가 재지 않았다** — N판 판 격자 없이는 말하지 않는다.
- ★ `Sequence.toList` 는 크기를 모른 채 `ArrayList` 를 키운다((3)) — `List.map` 은 입력 크기로 **미리 잡는다.** 재할당이 몇 번인지는 **재지 않았다.**
- ★ `sorted` 의 결과는 `SequencesKt___SequencesKt$sorted$1`(익명 객체), `distinct` 는 `DistinctSequence` — 둘 다 **아직 아무것도 모으지 않은 래퍼**다. 모으는 것은 반복을 시작할 때다((3)).

### (5) ★★ 두 번 돌 수 있나 — `constrainOnce`

```kotlin
// once47.kt
fun twice(label: String, s: Sequence<Int>) {
    for (round in 1..2) {
        try {
            println("$label  round $round -> ${s.toList()}")
        } catch (e: IllegalStateException) {
            println("$label  round $round -> ${e::class.simpleName}: ${e.message}")
        }
    }
}

fun main() {
    twice("1 sequenceOf              ", sequenceOf(1, 2, 3))
    twice("2 List.asSequence()       ", listOf(1, 2, 3).asSequence())
    twice("3 generateSequence(seed)  ", generateSequence(1) { if (it < 3) it + 1 else null })
    var i = 0
    twice("4 generateSequence { }    ", generateSequence { if (i < 3) ++i else null })
    twice("5 sequence { }            ", sequence { println("   block starts"); yield(1); yield(2) })
    twice("6 Iterator.asSequence()   ", listOf(1, 2, 3).iterator().asSequence())
    twice("7 Sequence { iterator }   ", Sequence { listOf(1, 2).iterator() })
}
```

```text
===== kotlinc once47.kt -d o47n =====
(exit 0)
===== java -cp o47n:kotlin-stdlib.jar Once47Kt =====
1 sequenceOf                round 1 -> [1, 2, 3]
1 sequenceOf                round 2 -> [1, 2, 3]
2 List.asSequence()         round 1 -> [1, 2, 3]
2 List.asSequence()         round 2 -> [1, 2, 3]
3 generateSequence(seed)    round 1 -> [1, 2, 3]
3 generateSequence(seed)    round 2 -> [1, 2, 3]
4 generateSequence { }      round 1 -> [1, 2, 3]
4 generateSequence { }      round 2 -> IllegalStateException: This sequence can be consumed only once.
   block starts
5 sequence { }              round 1 -> [1, 2]
   block starts
5 sequence { }              round 2 -> [1, 2]
6 Iterator.asSequence()     round 1 -> [1, 2, 3]
6 Iterator.asSequence()     round 2 -> IllegalStateException: This sequence can be consumed only once.
7 Sequence { iterator }     round 1 -> [1, 2]
7 Sequence { iterator }     round 2 -> [1, 2]
(exit 0)
```

- ★★★ **두 번째에 던진 것은 `generateSequence { }`(씨앗 없는 꼴)와 `Iterator.asSequence()` 둘** — `IllegalStateException: This sequence can be consumed only once.` 나머지 다섯은 두 번 다 같은 원소를 줬다.
- ★★★ **`sequence { }` 는 두 번 돌고, 돌 때마다 블록을 처음부터 다시 실행한다** — `block starts` 가 **두 번** 찍혔다. 「한 번만 돈다」가 아니라 「**두 번 계산한다**」 — 블록이 파일·네트워크를 읽으면 두 번 읽는다(C# 의 같은 성질은 [C# 32번](../../../csharp/syntax/32-yield-return-iterators-and-deferred-execution/) (7)).
- ★★ **`generateSequence(1) { … }`(씨앗 있는 꼴)은 두 번 돈다** — 같은 이름인데 **오버로드마다 약속이 다르다.**

```text
===== sed -n '8,9p;12,14p' commonMain/kotlin/collections/Sequence.kt =====
/**
 * A sequence that returns values through its iterator. The values are evaluated lazily, and the sequence
 * Sequences can be iterated multiple times, however some sequence implementations might constrain themselves
 * to be iterated only once. That is mentioned specifically in their documentation (e.g. [generateSequence] overload).
 * The latter sequences throw an exception on an attempt to iterate them the second time.
(exit 0)
===== sed -n '27p;31p' commonMain/kotlin/collections/Sequences.kt =====
 * Creates a sequence that returns all elements from this iterator. The sequence is constrained to be iterated only once.
public fun <T> Iterator<T>.asSequence(): Sequence<T> = Sequence { this }.constrainOnce()
(exit 0)
===== sed -n '684p;691,693p' commonMain/kotlin/collections/Sequences.kt =====
 * The returned sequence is constrained to be iterated only once.
public fun <T : Any> generateSequence(nextFunction: () -> T?): Sequence<T> {
    return GeneratorSequence(nextFunction, { nextFunction() }).constrainOnce()
}
(exit 0)
===== sed -n '702p;709p' commonMain/kotlin/collections/Sequences.kt =====
 * The sequence can be iterated multiple times, each time starting with [seed].
public fun <T : Any> generateSequence(seed: T?, nextFunction: (T) -> T?): Sequence<T> =
(exit 0)
===== sed -n '43p' commonMain/kotlin/collections/SequenceBuilder.kt =====
public fun <T> sequence(@BuilderInference block: suspend SequenceScope<T>.() -> Unit): Sequence<T> = Sequence { iterator(block) }
(exit 0)
===== sed -n '19,25p' jvmMain/kotlin/collections/SequencesJVM.kt =====
internal actual class ConstrainedOnceSequence<T> actual constructor(sequence: Sequence<T>) : Sequence<T> {
    private val sequenceRef = java.util.concurrent.atomic.AtomicReference(sequence)

    actual override fun iterator(): Iterator<T> {
        val sequence = sequenceRef.getAndSet(null) ?: throw IllegalStateException("This sequence can be consumed only once.")
        return sequence.iterator()
    }
(exit 0)
```

- ★★★ **「두 번 돌 수 있다」가 기본이고 한 번 제한은 문서에 적힌 것만** — `Sequence` KDoc 「`Sequences can be iterated multiple times, however some sequence implementations might constrain themselves to be iterated only once. That is mentioned specifically in their documentation`」. 씨앗 없는 `generateSequence` 와 `Iterator.asSequence` 의 KDoc 에 「`constrained to be iterated only once`」가 있고, 씨앗 있는 꼴에는 「`can be iterated multiple times, each time starting with [seed]`」가 있다.
- ★★ **한 번 제한의 구현은 `AtomicReference.getAndSet(null)`** — 첫 `iterator()` 가 원본을 꺼내며 `null` 로 바꾸고, 두 번째는 `null` 을 보고 던진다. 스레드 둘이 동시에 불러도 **한쪽만** 원본을 받는다.
- ★ `sequence { }` 는 `Sequence { iterator(block) }` — `iterator()` 를 부를 때마다 **새 반복자(새 블록 실행)** 를 만든다. 그래서 두 번 돌고 두 번 계산한다.

## 문법 — 형태와 규칙

**형태** — 무한 수열을 잘라 쓰기 · 파일 줄처럼 앞에서 몇 개만 · `sequence { yield }`.

```kotlin
// form47.kt
fun main() {
    val powers = generateSequence(1) { it * 2 }.takeWhile { it < 100 }.toList()
    println("powers  $powers")

    val lines = listOf("# head", "a=1", "", "b=2", "# note", "c=3", "d=4")
    val firstTwo = lines.asSequence()
        .filter { it.isNotBlank() && !it.startsWith("#") }
        .map { it.substringBefore("=") }
        .take(2)
        .toList()
    println("keys    $firstTwo")

    val fib = sequence {
        var a = 0
        var b = 1
        while (true) {
            yield(a)
            val next = a + b
            a = b
            b = next
        }
    }
    println("fib     ${fib.take(8).toList()}")
}
```

```text
===== kotlinc form47.kt -d o47z =====
(exit 0)
===== java -cp o47z:kotlin-stdlib.jar Form47Kt =====
powers  [1, 2, 4, 8, 16, 32, 64]
keys    [a, b]
fib     [0, 1, 1, 2, 3, 5, 8, 13]
(exit 0)
```

**규칙 불릿**

- **`Sequence` 는 끝 연산이 있어야 돈다** — 없으면 람다 0번((2) `E`\~`F`).
- **원소별로 흐른다** — 그래서 `first`·`take`·`takeWhile`·`any` 로 끝나면 **뒤를 안 본다**((1)(2)).
- **`sorted`(와 `sortedBy` 류)는 앞쪽을 전부 당긴다 · `distinct` 는 안 당긴다**((2)(3)).
- **끝이 `toList` 인 짧은 사슬은 호출 수가 같다** — 아끼는 것은 중간 리스트, 더 드는 것은 래퍼 객체((1)(4)).
- **두 번 돌 수 있는지는 만든 함수가 정한다** — KDoc 에 「`only once`」가 있으면 두 번째에 던진다((5)).
- **결과 타입은 대부분 `Sequence` 로 남는다** — 끝나는 자리는 [42번 주제](../42-transformations-map-flatmap-associate-zip/) (1).

## 어디서 틀리나

1. ★★★ **「`Sequence` 가 `List` 보다 빠르다」를 규칙으로 쓴다.** 이 문서가 말할 수 있는 것은 **호출 수**다 — 끝이 `toList` 면 같고((1)), 래퍼 객체는 더 든다((4)). 시간은 재야 안다.
2. ★★★ **`Sequence` 사슬에 `sorted` 를 넣고 `first` 가 앞쪽을 조금만 본다고 믿는다.** `sorted` 앞은 전부 돈다((1)(2)).
3. ★★ **`distinct` 도 `sorted` 처럼 전부 모은다고 본다.** 원소별로 흐른다 — `HashSet` 만 쥔다((2)(3)).
4. ★★ **`List` 와 `Sequence` 의 부작용 순서가 같다고 본다.** 단계별 대 원소별이다 — 로그·외부 호출 순서가 바뀐다((2)).
5. ★★ **끝 연산 없이 `Sequence` 를 만들어 두고 일이 끝났다고 본다.** 아무것도 안 돌았다((2)).
6. ★★ **`sequence { }` 를 두 번 돌리고 한 번 계산된다고 본다.** 블록이 **다시** 돈다((5)).
7. ★ **`Iterator.asSequence()`·씨앗 없는 `generateSequence { }` 를 두 번 돈다.** 두 번째에 `IllegalStateException`((5)).

## 구현 세부사항 대 언어 보장

| 항목 | 어느 쪽인가 | 근거 |
|---|---|---|
| `Sequence` 연산이 지연이고 원소별로 흐른다 | ★★★ **API 계약** — 「`_intermediate_`」 분류와 「`evaluated lazily`」 | (2)(3) |
| `sorted`·`distinct` 가 「상태 있음」 | ★★ **API 계약(KDoc 분류)** | (3) |
| `sorted` 가 첫 원소 전에 전부 모은다 · `distinct` 는 안 모은다 | ★ **stdlib 구현**(`toMutableList()` · `HashSet` + 원소별) — 분류는 둘을 **같은 칸**에 둔다 | (2)(3) |
| 두 번 돌 수 있는가 | ★★★ **API 계약(KDoc)** — 만든 함수마다 적힌다 | (5) |
| 한 번 제한이 `AtomicReference` 로 · 메시지 `This sequence can be consumed only once.` | ★ **stdlib 구현** | (5) |
| `List.map` 이 `ArrayList` 를 입력 크기로 · 래퍼 클래스 이름 | ★ **stdlib 구현** — 계약은 `List<R>`·`Sequence<R>` 까지 | (3)(4) |
| 람다 호출 수 | ★★ **관찰 — 그러나 결정적** — 위 두 계약(지연·원소별)에서 따라 나온다 | (1) |
| 「`Sequence` 가 빠르다/느리다」 | **재지 않았다** | — |

★★ **가장 조심할 자리** — 「상태 있음」이라는 **같은 분류 안에서** `sorted` 와 `distinct` 의 당기는 방식이 다르다. 분류만 외우면 `distinct` 를 잘못 피한다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 끝이 `first`·`take(n)`·`any`·`find` — 앞 몇 개면 된다 | ★ `asSequence()` | (1) — 호출이 입력 크기와 무관해진다 |
| 무한하거나 끝을 모른다(`generateSequence`·`sequence { }`) | `Sequence` | (5) — `List` 로는 못 만든다 |
| 사슬이 짧고 끝이 `toList` | **`List` 그대로** | (1)(4) — 호출이 같고 래퍼만 는다 |
| 사슬에 `sorted` 가 앞쪽에 있다 | 어느 쪽이든 앞쪽은 전부 돈다 | (1)(2) |
| 결과를 **여러 번** 읽는다 | 한 번 `toList()` 로 굳힌다 | (5) — `sequence { }` 는 다시 돌고, 일부는 던진다 |
| 단계 사이 부작용 순서가 중요하다 | 순서를 정한 쪽을 **명시적으로** 고른다 | (2) |

## 핵심 문장

1. `Sequence` 는 **원소별**로, `List` 사슬은 **단계별**로 흐른다 — 값은 같고 순서가 다르다.
2. 끝이 `first`·`take` 면 `Sequence` 가 호출을 줄인다(10칸 중 8칸) — **끝이 `toList` 면 호출 수가 같다.**
3. `List` 사슬은 **단계마다 리스트를 하나씩** 만들고, `Sequence` 는 대신 **래퍼 객체**를 만든다 — 손해인 쪽은 짧은 `toList` 사슬이다.
4. **`sorted` 는 첫 원소 전에 앞쪽을 전부 당기고, `distinct` 는 안 당긴다** — 둘 다 「상태 있음」이다.
5. 두 번 돌 수 있는지는 **만든 함수의 KDoc** 이 정한다 — `sequence { }` 는 두 번 돌며 **두 번 계산**하고, `Iterator.asSequence()` 는 두 번째에 던진다.

## 관련 자료

- [42번 주제](../42-transformations-map-flatmap-associate-zip/) — ★★★ **선행.** `Sequence` 연산의 **결과 타입** 격자(`Sequence`→`Sequence` 8칸 · `unzip`·`associate*` 에서 끝남). 그쪽은 **타입**, 여기는 **평가 시점과 비용**.
- [41번 주제](../41-collection-creation-and-copying/) (2) — `toList()` 가 원소 수로 클래스를 고른다. [45번 주제](../45-sorting-and-partial-operations/) (1) — `List.sorted()` 의 `Arrays$ArrayList`.
- [Java 44번](../../../java/syntax/44-stream-creation/) · [Java 45번](../../../java/syntax/45-intermediate-operations/) · [Java 46번](../../../java/syntax/46-terminal-operations/) — `Stream` 의 같은 지연 평가. Kotlin 은 컬렉션 연산이 **기본 즉시**라 `asSequence()` 로 **명시적으로** 넘어가고, Java 는 `stream()` 이 곧 지연이다.
- [C# 32번](../../../csharp/syntax/32-yield-return-iterators-and-deferred-execution/) — `yield return` 과 LINQ 의 지연 실행 · 두 번 열거하면 두 번 돈다.
- [C# 33번](../../../csharp/syntax/33-linq-method-syntax-and-deferred-execution/) — LINQ 메서드 구문의 지연 실행. ★ 같은 시기에 다른 배치가 쓰고 있어 이 문서는 그 내용을 **인용하지 않았다.**
- [목록의 **55번 주제**](../55-flow-cold-streams-operators-and-collect/) — `Flow`(콜드 스트림) — 같은 「끝 연산 전에는 아무 일도 안 한다」의 코루틴 판.

## 용어 풀이

> **지연 평가(lazy evaluation)** — 값을 **필요해질 때** 계산하는 것. `Sequence` 의 중간 연산은 끝 연산이 원소를 달라고 할 때 돈다.\
> 예: `listOf(1, 2).asSequence().map { println(it); it }` 만으로는 아무것도 안 찍힌다.

> **중간 연산 / 끝 연산(intermediate / terminal)** — 새 `Sequence` 를 돌려주는 연산(`map`·`filter`) / 원소를 실제로 당겨 결과를 내는 연산(`toList`·`first`·`sum`).

> **상태 없음 / 상태 있음(stateless / stateful)** — 원소 하나만 보고 결정하는 연산 / 앞서 본 원소를 기억해야 하는 연산(`sorted`·`distinct`).

> **중간 컬렉션** — 사슬의 단계 사이에 만들어졌다 버려지는 리스트. `List` 사슬은 단계마다 하나.

> **래퍼 객체** — `Sequence` 연산이 돌려주는 「만드는 방법」 객체(`TransformingSequence` 등). 원소를 담지 않는다.

> **`constrainOnce`** — `Sequence` 를 감싸 **두 번째 반복에서 `IllegalStateException`** 을 던지게 하는 함수.

## 더 들어가면

- **할당 바이트** — 래퍼·반복자·중간 리스트의 바이트를 JFR 이나 할당 계수기로 세면 (4)의 저울을 수치로 볼 수 있다. 이 판은 **재지 않았다.**
- **`sortedBy`·`sortedDescending` 의 `Sequence` 판** — 같은 `_stateful_` 이고 같은 방식으로 모을 것으로 보이지만 **발췌하지 않았다.**
- **`Sequence.chunked`·`windowed`** — 상태 있음이면서 **창 크기만큼만** 모은다. [45번 주제](../45-sorting-and-partial-operations/)의 `List` 판과 견줄 자리 — 돌리지 않았다.
