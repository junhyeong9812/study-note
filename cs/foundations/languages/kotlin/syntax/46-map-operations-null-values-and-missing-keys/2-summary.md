# kotlin/syntax/46 — `Map` 조작 — `getOrPut`/`getOrElse`/`mapValues`/`filterKeys` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Map-specific operations](https://kotlinlang.org/docs/map-operations.html)(키·값으로 꺼내기 `get`·`getValue`·`getOrElse`·`getOrDefault` · 거르기 `filterKeys`·`filterValues` · 쓰기) — 이 문서는 그 페이지의 **목록**을 따르되, 문장은 인용하지 않고 **이 판의 stdlib 소스 jar**(`kotlin-stdlib-sources.jar` 2.4.20)의 KDoc 과 구현을 근거로 삼는다((2)(3)(4)(5)).
> **실행 검증** — 이 문서의 모든 출력·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `java`·`javap` 에서 실제로 얻었다.\
> `kotlinc` 4회 · `java` 4회 · `javap` 1회 · stdlib 소스 jar 에서 발췌 10곳.\
> ★★ 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적지 않았다. **「결과가 같은 행 N / M」은 격자 프로그램이 스스로 센 것**이다.
> **버전** — `getOrPut`·`getOrElse`·`filterKeys`·`filterValues`·`mapValues` 는 **1.0** — 이 판의 소스에서 선언 위에 `@SinceKotlin` 이 **없다**. `getValue` 는 **`@SinceKotlin("1.1")`**((3)) · `Map.getOrDefault` 는 **`@SinceKotlin("1.1")` + `@PlatformDependent`**(JDK 8 의 `Map.getOrDefault` 를 그대로 드러낸 것 — (2)).\
> ★★★ **`getOrElseIfNull`·`getOrElseIfMissing`·`getOrPutIfNull`·`getOrPutIfMissing` 넷은 `@SinceKotlin("2.4")` + `@ExperimentalStdlibApi`**((4)) — 이 판에서 처음 들어온 **옵트인 API** 다. 격자는 `@file:OptIn(ExperimentalStdlibApi::class)` 로 불렀다.
> **경계** — ★★★ **해시 테이블의 원리**(버킷·충돌·재해시)는 [`cs/data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/) 이 정본이다 — 여기는 **stdlib 함수가 「키 없음」과 「값이 `null`」을 어떻게 다루나**만 본다.\
> **Java 쪽 같은 격자**(`get`·`getOrDefault`·`putIfAbsent`·`computeIfAbsent`·`merge` × 세 상태)는 [Java 41번](../../../java/syntax/41-map-api-merge-compute/)이 이미 쟀다 — 여기서는 `getOrDefault` 한 행만 겹친다.\
> `mapValues` 결과가 `LinkedHashMap` 이고 `Map.map` 이 `List` 라는 것은 [42번 주제](../42-transformations-map-flatmap-associate-zip/) (1)(2)가 쟀다 — 다시 재지 않는다. 결과가 **복사인가 창인가**는 [41번 주제](../41-collection-creation-and-copying/)가 정본이다.
> 이 본문은 Claude 작성이다(원고 없음).

★★★ **본체는 첫째 창이다** — 「**null 대 키 없음 격자 — 함수 13개 × 맵 상태 셋(키 없음 · 키가 있고 값이 `null` · 값이 있음) → 돌려준 값 · 맵이 바뀌었나 · 람다 호출 수**」. 두 상태는 `m["k"]` 로 보면 **둘 다 `null`** 이다. 함수마다 둘을 가르는지는 **맵을 셋 다 만들어 넣어 봐야** 보인다.

## 이 주제가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **언어 보장 / API 계약** | 서명·KDoc 이 약속한 것 | ★★★ `getOrPut` KDoc 「``is not in this map or is mapped to a `null` ``… is put into the map」 · `getOrElse` KDoc 「``present and not `null` ``」 · `getOrDefault` KDoc 「**if such a key is not present**」 · `withDefault` KDoc 「**obtained with [Map.getValue]**」 · `ConcurrentMap.getOrPut` KDoc 「**may be invoked even if the key is already in the map**」 |
| **구현(stdlib)** | 이 판의 stdlib 가 실제로 하는 것 | `getOrPut` 이 `get` → `== null` → `put` 세 줄 · `getOrImplicitDefault` 가 **`getOrElseIfMissing`** 을 부른다 · `filterKeys` 가 **새 `LinkedHashMap`** 에 담는다 · 예외 문장 `Key b is missing in the map.` |
| **이 판의 관찰** | kotlinc 2.4.20 에서 이번에 본 것 | 어느 오버로드가 붙었나(`javap` 의 `putIfAbsent` 대 `put`) · 격자 값 |

## 이 판

```text
===== kotlinc -version =====
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | (이 주제에는 없다) | 해시코드·주소·시간을 찍지 않았다 · 동시성 경쟁은 **재지 않았다**((5)) |
| 안 흔들린다 | 격자 13행 × 3열 · 결과가 같은 행 수 · 람다 호출 수 | 단일 스레드 · 맵은 칸마다 새로 만든다 |
| 안 흔들린다 | 맵 출력 순서(`{a=100, b=2, c=3}`) | `mutableMapOf`·`mapOf` 는 `LinkedHashMap` 이라 **넣은 순서**다(구현 — [42번 주제](../42-transformations-map-flatmap-associate-zip/) (2)) |
| 안 흔들린다 | stdlib 소스 발췌 · `javap` 의 명령 이름과 상수 풀 번호 · 종료 코드 | jar·컴파일러가 같으면 같다 |

★ 근거 — 캡처 스크립트를 처음부터 두 번 돌려 **블록 전체를 대조**했다(수치는 3-answer 의 「실행 검증」).

## 한눈에 — 쉽게 말하면

**맵의 칸 하나는 「사물함」이다 — 그런데 「사물함이 없다」와 「사물함은 있는데 비어 있다」가 문을 열어 보면 똑같이 보인다.** `m["k"]` 는 두 경우 모두 `null` 을 준다. 함수마다 이 둘을 **가르는 것과 못 가르는 것**이 있고, 못 가르는 함수는 「비어 있는 사물함」을 「없는 사물함」처럼 다룬다.
★ 가장 조용한 것은 `getOrPut` 이다 — 비어 있는 사물함을 보면 **없는 줄 알고 새로 채워 넣는다.** 캐시의 값이 `null` 이면 캐시는 **매번 다시 계산한다.**

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 사물함이 없다 | 키 없음(`{}`) | (1) |
| 사물함은 있는데 비었다 | 키가 있고 값이 `null`(`{k=null}`) | (1) ★ |
| 빈 사물함을 없는 것으로 본다 | `getOrPut` · `getOrElse` · `?:` · `m["k"]` | (1)(2) ★ |
| 빈 사물함을 빈 것으로 본다 | `getOrDefault` · `containsKey` · `getOrElseIfMissing` | (1)(2) |
| 관리인에게 물을 때만 나오는 예비 열쇠 | `withDefault` — **`getValue` 에만** 먹는다 | (3) ★ |
| 사물함 목록을 새 종이에 옮겨 적기 | `filterKeys`·`filterValues` — 새 맵 | (4) |

```text
   맵 상태             m["k"]      getOrPut("k"){9}          getOrDefault("k", 9)
   ─────────────────────────────────────────────────────────────────────────────
   {}      키 없음      null        9  넣는다 -> {k=9}         9
   {k=null} 값이 null   null        9  넣는다 -> {k=9}   <-    null   <- 둘이 반대
   {k=1}   값이 있음    1           1  그대로                  1
                        │
                        └ 두 상태가 같은 글자로 보인다 — 여기서부터 함수가 갈린다
```

## 이 주제가 답하려는 질문

1. 「키 없음」과 「값이 `null`」을 **가르는 함수와 못 가르는 함수**는 무엇인가 — 못 가르면 무엇이 조용히 일어나나.
2. `withDefault` 의 기본값은 **어느 읽기에 먹고 어느 읽기에 안 먹나.**
3. 그 동작은 **KDoc 계약**인가 구현인가 — 그리고 `ConcurrentHashMap` 에서 `getOrPut` 은 무엇을 약속하나.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **null 대 키 없음 격자(실행)** | 함수 × 세 상태 → 값 · 호출 뒤 맵 · 람다 호출 수((1)) | ★ **본체 창** |
| ★★ **람다 호출 로그** | `getOrPut` 이 `null` 을 넣은 키에서 **몇 번 다시 계산하나**((2)) | — |
| ★★ **stdlib 소스 jar 발췌** | 그 동작이 **KDoc 계약**인가, 구현 한 줄인가((2)(3)(4)(5)) | [41번 주제](../41-collection-creation-and-copying/) (2)와 같은 창 |
| ★★ **`javap -c`** | `ConcurrentHashMap` 에 붙은 `getOrPut` 이 **`putIfAbsent`** 를 부르나 **`put`** 을 부르나((5)) | — |
| **인용 — 다시 안 잰다** | `mapValues` 결과가 `LinkedHashMap` · Java `Map` 다섯 메서드의 격자 | [42번 주제](../42-transformations-map-flatmap-associate-zip/) (2) · [Java 41번](../../../java/syntax/41-map-api-merge-compute/) (1) |
| ★ **제5의 상태 — 창을 바꿔 물었다** | 「`ConcurrentHashMap.getOrPut` 이 경쟁에서 안전한가」를 **동시 실행**으로 묻지 않고 **바이트코드 + KDoc** 으로 물었다 | (5) — 이 창은 **어느 호출이 붙었나**만 보고 **경쟁 중 몇 번 불리나**는 못 본다 |
| **부적용 — 실행 시간·할당** | 「`getOrPut` 이 `get`+`put` 보다 싸다」는 **재지 않았다** | — |

### (1) ★★★ null 대 키 없음 격자

**언제 쓰나** — 값에 `null` 이 들어갈 수 있는 맵(`Map<K, V?>`)에서 「없으면 …」을 쓸 때. 캐시·설정·집계 맵.

방법 — 칸마다 **맵을 새로 만들고**(`fresh`), 함수를 한 번 부르고, **돌려준 값 · 호출 뒤 맵 · 람다(`nine`)가 불린 횟수**를 `·` 로 이어 찍는다. 던지면 예외 클래스를 찍는다. 마지막 줄은 **「키 없음」 열과 「값이 `null`」 열의 결과(첫 칸)가 같은 행**을 프로그램이 센다.

```kotlin
// grid46.kt
@file:OptIn(ExperimentalStdlibApi::class)

var calls = 0
fun nine(): Int? { calls++; return 9 }

val states = listOf("absent", "null-value", "present")

fun fresh(state: String): MutableMap<String, Int?> = when (state) {
    "absent" -> mutableMapOf()
    "null-value" -> mutableMapOf("k" to null)
    else -> mutableMapOf("k" to 1)
}

val probes: List<Pair<String, (MutableMap<String, Int?>) -> Any?>> = listOf(
    "m[\"k\"]" to { m -> m["k"] },
    "m.get(\"k\")" to { m -> m.get("k") },
    "m.getValue(\"k\")" to { m -> m.getValue("k") },
    "m.getOrElse(\"k\") { 9 }" to { m -> m.getOrElse("k") { nine() } },
    "m.getOrDefault(\"k\", 9)" to { m -> m.getOrDefault("k", 9) },
    "m.getOrPut(\"k\") { 9 }" to { m -> m.getOrPut("k") { nine() } },
    "m.containsKey(\"k\")" to { m -> m.containsKey("k") },
    "m[\"k\"] ?: 9" to { m -> m["k"] ?: nine() },
    "m.withDefault { 9 }.getValue(\"k\")" to { m -> m.withDefault { nine() }.getValue("k") },
    "m.withDefault { 9 }[\"k\"]" to { m -> m.withDefault { nine() }["k"] },
    "m.getOrElseIfMissing(\"k\") { 9 }" to { m -> m.getOrElseIfMissing("k") { nine() } },
    "m.getOrPutIfMissing(\"k\") { 9 }" to { m -> m.getOrPutIfMissing("k") { nine() } },
    "m.getOrPutIfNull(\"k\") { 9 }" to { m -> m.getOrPutIfNull("k") { nine() } },
)

fun run(state: String, f: (MutableMap<String, Int?>) -> Any?): Pair<String, String> {
    val m = fresh(state)
    calls = 0
    val r = try { f(m).toString() } catch (e: Exception) { "throws " + e::class.simpleName }
    return r to "$r · $m · λ$calls"
}

fun main() {
    println((listOf("form") + states).joinToString("\t"))
    var same = 0
    for ((name, f) in probes) {
        val cells = states.map { run(it, f) }
        val row = listOf(name) + cells.map { it.second }
        check(row.size == 1 + states.size)
        println(row.joinToString("\t"))
        if (cells[0].first == cells[1].first) same++
    }
    println("rows where the absent and null-value results are the same: $same / ${probes.size}")
}
```

```text
===== kotlinc grid46.kt -d o46g =====
(exit 0)
===== java -cp o46g:kotlin-stdlib.jar Grid46Kt =====
form	absent	null-value	present
m["k"]	null · {} · λ0	null · {k=null} · λ0	1 · {k=1} · λ0
m.get("k")	null · {} · λ0	null · {k=null} · λ0	1 · {k=1} · λ0
m.getValue("k")	throws NoSuchElementException · {} · λ0	null · {k=null} · λ0	1 · {k=1} · λ0
m.getOrElse("k") { 9 }	9 · {} · λ1	9 · {k=null} · λ1	1 · {k=1} · λ0
m.getOrDefault("k", 9)	9 · {} · λ0	null · {k=null} · λ0	1 · {k=1} · λ0
m.getOrPut("k") { 9 }	9 · {k=9} · λ1	9 · {k=9} · λ1	1 · {k=1} · λ0
m.containsKey("k")	false · {} · λ0	true · {k=null} · λ0	true · {k=1} · λ0
m["k"] ?: 9	9 · {} · λ1	9 · {k=null} · λ1	1 · {k=1} · λ0
m.withDefault { 9 }.getValue("k")	9 · {} · λ1	null · {k=null} · λ0	1 · {k=1} · λ0
m.withDefault { 9 }["k"]	null · {} · λ0	null · {k=null} · λ0	1 · {k=1} · λ0
m.getOrElseIfMissing("k") { 9 }	9 · {} · λ1	null · {k=null} · λ0	1 · {k=1} · λ0
m.getOrPutIfMissing("k") { 9 }	9 · {k=9} · λ1	null · {k=null} · λ0	1 · {k=1} · λ0
m.getOrPutIfNull("k") { 9 }	9 · {k=9} · λ1	9 · {k=9} · λ1	1 · {k=1} · λ0
rows where the absent and null-value results are the same: 7 / 13
(exit 0)
```

- ★★★ **13행 중 7행이 두 상태를 같은 결과로 답한다** — `m["k"]`·`get` 은 둘 다 `null` · `getOrElse`·`?:` 는 둘 다 `9` · **`getOrPut` 과 `getOrPutIfNull` 은 둘 다 `9` 를 넣는다** · `withDefault { 9 }["k"]` 는 둘 다 `null`.
- ★★★ **`getOrPut` 은 값이 `null` 인 키를 없는 키처럼 다룬다** — `{k=null}` 이 호출 뒤 **`{k=9}`** 로 바뀌었고 람다가 **1번** 불렸다. 「있는 키는 안 건드린다」가 아니다.
- ★★★ **`getOrDefault` 와 `getOrElse` 가 `{k=null}` 칸에서 반대다** — `getOrDefault` 는 **`null`**(키가 있으니 그 값), `getOrElse` 는 **`9`**(값이 `null` 이니 기본값). 이름은 비슷한데 **보는 것이 다르다** — 앞쪽은 키, 뒤쪽은 값((2)).
- ★★ **`getValue` 는 키가 없을 때만 던진다** — `{}` 에서 `NoSuchElementException`, **`{k=null}` 에서는 `null` 을 돌려준다.** 「`getValue` 는 절대 `null` 을 안 준다」가 아니다(`V` 가 `Int?` 이면 `null` 도 값이다).
- ★★ **`withDefault { 9 }` 는 `getValue` 에만 먹는다** — `[]` 로 읽으면 `{}` 에서도 `null` 이다(람다 `λ0`). 그리고 `getValue` 로 읽어도 **`{k=null}` 에서는 기본값이 아니라 `null`** 이다 — 키가 있기 때문이다((3)).
- ★ **2.4 의 새 함수 셋이 두 갈래를 이름으로 가른다** — `…IfMissing` 은 키만 본다(`{k=null}` 을 그대로 둔다), `…IfNull` 은 옛 `getOrPut` 과 같다.
- ★ `containsKey` 는 두 상태를 가르는 **유일한 읽기 전용 옛 함수**다(`false` 대 `true`).

### (2) ★★★ `getOrPut` 은 값이 `null` 이면 다시 넣는다 — 로그와 계약

```kotlin
// shape46.kt
fun main() {
    val cache = mutableMapOf<String, String?>()
    repeat(3) { i ->
        val v = cache.getOrPut("u") { println("   compute #$i"); null }
        println("1 round $i -> $v  $cache")
    }

    val d = mapOf("a" to 1).withDefault { 0 }
    println("2 d[\"b\"]              = ${d["b"]}")
    println("3 d.getValue(\"b\")     = ${d.getValue("b")}")
    println("4 d.getOrDefault(\"b\", -1) = ${d.getOrDefault("b", -1)}")
    println("5 d                   = $d")
    val derived = d.filterKeys { true }
    try {
        println("6 derived.getValue(\"b\") = ${derived.getValue("b")}")
    } catch (e: Exception) {
        println("6 derived.getValue(\"b\") -> ${e::class.simpleName}: ${e.message}")
    }

    val src = mutableMapOf("a" to 1, "b" to 2, "c" to 3)
    val fk = src.filterKeys { it != "b" }
    val fv = src.filterValues { it > 1 }
    src["a"] = 100
    println("7 src=$src  fk=$fk  fv=$fv")
    println("8 fk === src: ${fk === src}  ${fk::class.java.name}")
}
```

```text
===== kotlinc shape46.kt -d o46s =====
(exit 0)
===== java -cp o46s:kotlin-stdlib.jar Shape46Kt =====
   compute #0
1 round 0 -> null  {u=null}
   compute #1
1 round 1 -> null  {u=null}
   compute #2
1 round 2 -> null  {u=null}
2 d["b"]              = null
3 d.getValue("b")     = 0
4 d.getOrDefault("b", -1) = -1
5 d                   = {a=1}
6 derived.getValue("b") -> NoSuchElementException: Key b is missing in the map.
7 src={a=100, b=2, c=3}  fk={a=1, c=3}  fv={b=2, c=3}
8 fk === src: false  java.util.LinkedHashMap
(exit 0)
```

- ★★★ **`compute` 가 세 번 다 불렸다**(`#0`·`#1`·`#2`) — 첫 호출이 `null` 을 넣었고(`{u=null}`), 다음 호출은 그 `null` 을 보고 **「없다」로 판단해 다시 계산했다.** 「계산 결과가 `null`」인 키는 **캐시가 영영 안 맞는다.**
- 줄 `2`\~`8` 은 (3)(4)에서 읽는다.

```text
===== unzip -o -q kotlin-stdlib-sources.jar commonMain/kotlin/collections/Maps.kt commonMain/kotlin/collections/MapWithDefault.kt jvmMain/kotlin/collections/MapsJVM.kt jvmMain/kotlin/Collections.kt commonMain/generated/_Sequences.kt commonMain/generated/_Collections.kt commonMain/kotlin/collections/Sequence.kt commonMain/kotlin/collections/Sequences.kt jvmMain/kotlin/collections/SequencesJVM.kt commonMain/kotlin/text/Strings.kt jvmMain/kotlin/text/CharJVM.kt jvmMain/kotlin/text/regex/Regex.kt commonMain/kotlin/util/Result.kt commonMain/kotlin/collections/SequenceBuilder.kt =====
(exit 0)
```

```text
===== sed -n '440,442p;448,449p;452p;459,468p' commonMain/kotlin/collections/Maps.kt =====
 * Returns the value for the given [key] if the value is present and not `null`.
 * Otherwise, calls the [defaultValue] function,
 * puts its result into the map under the given key, and returns the call result.
 * When the given [key] is not in this map or is mapped to a `null`, the result of [defaultValue],
 * even if `null`, is put into the map under the key.
 * Note that the operation is not guaranteed to be atomic if the map is being modified concurrently.
public inline fun <K, V> MutableMap<K, V>.getOrPut(key: K, defaultValue: () -> V): V {
    val value = get(key)
    return if (value == null) {
        val answer = defaultValue()
        put(key, answer)
        answer
    } else {
        value
    }
}
(exit 0)
```

- ★★★ **계약이다** — KDoc 이 「``When the given [key] is not in this map or is mapped to a `null`, the result of [defaultValue], even if `null`, is put into the map under the key.``」라고 **약속한다.** 구현도 `get(key)` 를 받아 **`== null` 하나로** 가른다 — `containsKey` 를 부르지 않는다.
- ★★ 같은 KDoc 에 「**not recommended** … if the map is expected to contain `null` values」가 있다 — 그리고 2.4 부터 **`getOrPutIfNull`/`getOrPutIfMissing` 을 쓰라**고 가리킨다((4)).

```text
===== sed -n '361,362p;364,366p;371p;375p' commonMain/kotlin/collections/Maps.kt =====
 * Returns the value for the given [key] if the value is present and not `null`.
 * Otherwise, returns the result of the [defaultValue] function.
 * Note: it's not recommended to use this function if the map is expected to contain `null` values.
 * Use either [getOrElseIfNull], or [getOrElseIfMissing] instead to express the intent
 * what to return when the key is mapped to `null` value more clearly.
public inline fun <K, V> Map<K, V>.getOrElse(key: K, defaultValue: () -> V): V {
    return get(key) ?: defaultValue()
(exit 0)
===== sed -n '608p;612,614p' jvmMain/kotlin/Collections.kt =====
     * Returns the value corresponding to the given [key], or [defaultValue] if such a key is not present in the map.
    @SinceKotlin("1.1")
    @PlatformDependent
    public fun getOrDefault(key: K, defaultValue: @UnsafeVariance V): V {
(exit 0)
```

- ★★★ **두 KDoc 이 다른 것을 약속한다** — `getOrElse` 는 「``present and not `null` ``」이 아니면 기본값, `getOrDefault` 는 「`if such a key is not present`」일 때만 기본값. 구현도 그대로다 — `getOrElse` 는 **`get(key) ?: defaultValue()`** 한 줄이다(그래서 `m["k"] ?: 9` 와 **같은 행**이 나왔다).
- ★★ `getOrDefault` 는 **Kotlin 이 만든 함수가 아니다** — `@PlatformDependent` 가 붙은 **JDK 8 `Map.getOrDefault`** 이고, Java 쪽 같은 칸이 `null / {k=null}` 인 것은 [Java 41번](../../../java/syntax/41-map-api-merge-compute/) (3)이 쟀다.

### (3) ★★ `withDefault` — 관리인에게 물을 때만

(2)의 줄 `2`\~`6` 이 이 절의 출력이다.

- ★★★ **`d["b"]` 는 `null`, `d.getValue("b")` 는 `0`** — 같은 맵에서 **읽는 함수에 따라** 기본값이 나오고 안 나온다. `withDefault` 는 **에러도 경고도 없이** `[]` 에는 아무 일도 안 한다.
- ★★ **`d.getOrDefault("b", -1)` 은 `-1`** — `withDefault` 의 `0` 이 아니다. 그 호출은 Java 의 `getOrDefault` 이고 감싼 객체가 그것을 넘겨받지 않았다.
- ★★ **`d` 를 찍으면 `{a=1}`** — 기본값이 있다는 흔적이 `toString` 에 없다.
- ★★ **`filterKeys { true }` 로 만든 맵은 기본값을 잃는다** — `derived.getValue("b")` 가 **`NoSuchElementException: Key b is missing in the map.`** 을 던졌다. 새 맵은 **새 `LinkedHashMap`** 이라 감싼 껍데기가 따라오지 않는다((4)).

```text
===== sed -n '425,428p;437p' commonMain/kotlin/collections/Maps.kt =====
 * Returns the value for the given [key] or throws an exception if there is no such key in the map.
 *
 * If the map was created by [withDefault], resorts to its `defaultValue` provider function
 * instead of throwing an exception.
public fun <K, V> Map<K, V>.getValue(key: K): V = getOrImplicitDefault(key)
(exit 0)
===== sed -n '29,32p;39p' commonMain/kotlin/collections/MapWithDefault.kt =====
 * Returns a wrapper of this read-only map, having the implicit default value provided with the specified function [defaultValue].
 *
 * This implicit default value is used when the original map doesn't contain a value for the key specified
 * and a value is obtained with [Map.getValue] function, for example when properties are delegated to the map.
public fun <K, V> Map<K, V>.withDefault(defaultValue: (key: K) -> V): Map<K, V> =
(exit 0)
===== sed -n '20,25p' commonMain/kotlin/collections/MapWithDefault.kt =====
internal fun <K, V> Map<K, V>.getOrImplicitDefault(key: K): V {
    if (this is MapWithDefault)
        return this.getOrImplicitDefault(key)

    @OptIn(ExperimentalStdlibApi::class)
    return getOrElseIfMissing(key, { throw NoSuchElementException("Key $key is missing in the map.") })
(exit 0)
```

- ★★★ **「`getValue` 에만」은 KDoc 계약이다** — `withDefault` 의 KDoc 이 「`a value is obtained with [Map.getValue] function`」라고 **범위를 적는다.** `getValue` 는 `getOrImplicitDefault` 로 가고, 감싼 맵(`MapWithDefault`)이면 기본값 함수를, 아니면 예외를 부른다.
- ★★ **이 판의 `getOrImplicitDefault` 는 `getOrElseIfMissing` 을 부른다** — 그래서 **`{k=null}` 의 `getValue` 는 던지지도 기본값을 주지도 않고 `null`** 이다((1)). 이것은 **구현 관찰**이다 — `getValue` 의 KDoc 은 「`if there is no such key`」만 말한다.

### (4) ★ `filterKeys`·`filterValues` 는 새 맵 — 그리고 2.4 의 새 이름

(2)의 줄 `7`·`8` 이 이 절의 출력이다.

- ★★ **원본을 고쳐도 결과는 안 바뀐다** — `src["a"] = 100` 뒤에도 `fk={a=1, c=3}` 이다. `fk === src` 는 `false`, 클래스는 **`java.util.LinkedHashMap`**.
- ★ 순서는 원본의 넣은 순서를 따른다(`{a=1, c=3}` · `{b=2, c=3}`).

```text
===== sed -n '629,641p' commonMain/kotlin/collections/Maps.kt =====
 * Returns a map containing all key-value pairs with keys matching the given [predicate].
 *
 * The returned map preserves the entry iteration order of the original map.
 * @sample samples.collections.Maps.Filtering.filterKeys
 */
public inline fun <K, V> Map<out K, V>.filterKeys(predicate: (K) -> Boolean): Map<K, V> {
    val result = LinkedHashMap<K, V>()
    for (entry in this) {
        if (predicate(entry.key)) {
            result.put(entry.key, entry.value)
        }
    }
    return result
(exit 0)
```

- ★★ **「원본 순서를 지킨다」는 KDoc 계약**이다 — 「`The returned map preserves the entry iteration order of the original map.`」. `LinkedHashMap` 이라는 **클래스**는 구현이다(서명은 `Map<K, V>` 까지).

```text
===== grep -n -A4 '^@SinceKotlin("2.4")' commonMain/kotlin/collections/Maps.kt | grep 'public inline fun' =====
390-public inline fun <K, V> Map<K, V>.getOrElseIfNull(key: K, defaultValue: () -> V): V {
411-public inline fun <K, V> Map<K, V>.getOrElseIfMissing(key: K, defaultValue: () -> V): V {
493-public inline fun <K, V> MutableMap<K, V>.getOrPutIfNull(key: K, crossinline defaultValue: () -> V): V {
522-public inline fun <K, V> MutableMap<K, V>.getOrPutIfMissing(key: K, crossinline defaultValue: () -> V): V {
(exit 0)
===== sed -n '415,417p' commonMain/kotlin/collections/Maps.kt =====
    val value = get(key)
    if (value == null && !containsKey(key)) {
        return defaultValue()
(exit 0)
```

- ★★★ **2.4 의 새 함수 넷**(`ConcurrentMap` 판은 `MapsJVM.kt` 에 따로 있다) — 옛 `getOrElse`/`getOrPut` 이 **한 이름에 두 뜻**을 싣고 있던 것을 **`IfNull`(값을 본다) · `IfMissing`(키를 본다)** 로 가른 것이다. `…IfMissing` 의 구현은 `value == null && !containsKey(key)` — **`containsKey` 를 한 번 더 묻는다.**
- ★ 전부 `@ExperimentalStdlibApi` 라 **옵트인 없이는 컴파일되지 않는다**(격자 첫 줄의 `@file:OptIn`).

### (5) ★★ `ConcurrentHashMap` 에 붙는 `getOrPut` — 어느 쪽이 불리나

```kotlin
// conc46.kt
import java.util.concurrent.ConcurrentHashMap

fun viaConcurrent(m: ConcurrentHashMap<String, Int>): Int = m.getOrPut("k") { 1 }

fun viaMutable(m: MutableMap<String, Int>): Int = m.getOrPut("k") { 1 }

fun main() {
    val c = ConcurrentHashMap<String, Int>()
    println("${viaConcurrent(c)} ${viaMutable(c)} $c")
}
```

```text
===== kotlinc conc46.kt -d o46c =====
(exit 0)
===== java -cp o46c:kotlin-stdlib.jar Conc46Kt =====
1 1 {k=1}
(exit 0)
===== javap -c -p o46c/Conc46Kt.class | grep -E 'public static final int|Map\.(get|put|putIfAbsent):' =====
  public static final int viaConcurrent(java.util.concurrent.ConcurrentHashMap<java.lang.String, java.lang.Integer>);
      18: invokeinterface #24,  2           // InterfaceMethod java/util/concurrent/ConcurrentMap.get:(Ljava/lang/Object;)Ljava/lang/Object;
      44: invokeinterface #34,  3           // InterfaceMethod java/util/concurrent/ConcurrentMap.putIfAbsent:(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;
  public static final int viaMutable(java.util.Map<java.lang.String, java.lang.Integer>);
      15: invokeinterface #65,  2           // InterfaceMethod java/util/Map.get:(Ljava/lang/Object;)Ljava/lang/Object;
      40: invokeinterface #68,  3           // InterfaceMethod java/util/Map.put:(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;
(exit 0)
```

- ★★★ **정적 타입이 오버로드를 정한다** — `ConcurrentHashMap` 으로 받은 `viaConcurrent` 에는 **`ConcurrentMap.putIfAbsent`** 가, `MutableMap` 으로 받은 `viaMutable` 에는 **`Map.put`** 이 박혔다. **같은 객체 `c`** 를 넘겼는데 부른 코드가 다르다. 둘 다 `inline` 이라 호출한 함수 안에 풀려 있다.
- ★★ 그래서 `ConcurrentHashMap` 을 **`MutableMap` 타입으로 들고 다니면** 동시성용 판이 **조용히 빠진다.**

```text
===== sed -n '106,107p;111,115p' jvmMain/kotlin/collections/MapsJVM.kt =====
 * This method guarantees not to put the value into the map if the key is already there,
 * but the [defaultValue] function may be invoked even if the key is already in the map.
public inline fun <K, V> ConcurrentMap<K, V>.getOrPut(key: K, defaultValue: () -> V): V {
    // Do not use computeIfAbsent on JVM8 as it would change locking behavior
    return this.get(key)
            ?: defaultValue().let { default -> this.putIfAbsent(key, default) ?: default }
(exit 0)
```

- ★★★ **`ConcurrentMap.getOrPut` 의 약속은 「원자적」이 아니다** — 「`This method guarantees not to put the value into the map if the key is already there, but the [defaultValue] function may be invoked even if the key is already in the map.`」. **넣기는 한 번**(`putIfAbsent`)이지만 **람다는 여러 스레드에서 여러 번 불릴 수 있다.** 람다에 부작용이 있으면 그 부작용은 여러 번 일어난다.
- ★★ `MutableMap` 판의 KDoc 은 더 약하다 — 「`not guaranteed to be atomic`」((2) 발췌). `get` 과 `put` 사이에 다른 스레드가 끼면 **덮어쓴다.**
- ★ **경쟁 중 람다가 실제로 몇 번 불리는지는 재지 않았다** — 판마다 흔들리는 칸이라 한 판의 결과로 말할 수 없다(18-B 의 「못 잰 것」). 람다를 **정확히 한 번** 부르려면 JDK 의 `computeIfAbsent` 쪽이다([Java 41번](../../../java/syntax/41-map-api-merge-compute/)).

## 문법 — 형태와 규칙

**형태** — 단어 세기 · 길이별 묶기 · 값 바꾸기 · 키·값 거르기.

```kotlin
// form46.kt
fun main() {
    val words = listOf("tea", "cake", "tea", "coffee", "cake", "tea")

    val counts = mutableMapOf<String, Int>()
    for (w in words) counts[w] = counts.getOrElse(w) { 0 } + 1

    val byLength = mutableMapOf<Int, MutableList<String>>()
    for (w in words.distinct()) byLength.getOrPut(w.length) { mutableListOf() }.add(w)

    val price = mapOf("tea" to 3, "cake" to 5, "coffee" to 4)
    val doubled: Map<String, Int> = price.mapValues { (_, v) -> v * 2 }
    val short: Map<String, Int> = price.filterKeys { it.length <= 4 }
    val cheap: Map<String, Int> = price.filterValues { it < 5 }

    println("counts   $counts")
    println("byLength $byLength")
    println("doubled  $doubled")
    println("short    $short")
    println("cheap    $cheap")
    println("missing  ${price["juice"] ?: 0}")
}
```

```text
===== kotlinc form46.kt -d o46z =====
(exit 0)
===== java -cp o46z:kotlin-stdlib.jar Form46Kt =====
counts   {tea=3, cake=2, coffee=1}
byLength {3=[tea], 4=[cake], 6=[coffee]}
doubled  {tea=6, cake=10, coffee=8}
short    {tea=3, cake=5}
cheap    {tea=3, coffee=4}
missing  0
(exit 0)
```

**규칙 불릿**

- **「값이 `null` 이면 기본값」** — `getOrElse`·`?:`·`getOrPut` 이 이 뜻이다((1)(2)).
- **「키가 없을 때만 기본값」** — `getOrDefault`·`containsKey` 로 가른다. 2.4 옵트인이면 `getOrElseIfMissing`·`getOrPutIfMissing`((1)(4)).
- **`getOrPut` 은 기본값을 맵에 넣고 돌려준다** — 값이 `null` 이면 **매번** 다시 넣는다((2)).
- **`withDefault` 는 `getValue` 에만** — `[]`·`get`·`getOrDefault` 에는 없고, `filterKeys` 등으로 **새 맵을 만들면 사라진다**((3)).
- **`filterKeys`·`filterValues`·`mapValues` 는 새 맵** — 원본을 고쳐도 안 따라온다((4) · [42번 주제](../42-transformations-map-flatmap-associate-zip/) (2)).
- **`ConcurrentHashMap` 은 그 타입으로 받아야** `putIfAbsent` 판이 붙는다((5)).

## 어디서 틀리나

1. ★★★ **`cache.getOrPut(k) { compute() }` 에서 `compute()` 가 `null` 을 돌려줄 수 있는데 캐시가 된다고 믿는다.** 매번 다시 계산한다((2)). 「계산했는데 없음」을 캐시하려면 `getOrPutIfMissing`(2.4 옵트인)이나 **`null` 대신 표지 값**을 쓴다.
2. ★★★ **`getOrDefault` 와 `getOrElse` 를 같은 것으로 본다.** `{k=null}` 에서 `null` 대 기본값으로 **반대**다((1)).
3. ★★ **`withDefault` 를 걸고 `m[k]` 로 읽는다.** 기본값이 안 나온다 — 에러도 없다((3)).
4. ★★ **`withDefault` 맵을 `filterKeys`·`mapValues` 로 바꾼 뒤에도 기본값이 있다고 본다.** 새 맵에는 없다 — `getValue` 가 던진다((3)).
5. ★★ **`getValue` 는 `null` 을 안 준다고 본다.** 키가 있고 값이 `null` 이면 `null` 이다((1)).
6. ★★ **`ConcurrentHashMap` 을 `MutableMap` 으로 넘겨 `getOrPut` 한다.** `put` 판이 붙는다 — 경쟁 중 덮어쓸 수 있다((5)).
7. ★ **`ConcurrentHashMap.getOrPut` 이면 람다가 한 번만 불린다고 본다.** KDoc 은 **넣기**만 한 번을 약속한다((5)).

## 구현 세부사항 대 언어 보장

| 항목 | 어느 쪽인가 | 근거 |
|---|---|---|
| `getOrPut` 이 `null` 값인 키에 다시 넣는다 | ★★★ **API 계약(KDoc)** | (2) |
| `getOrElse` = 값이 `null` 이면 기본값 · `getOrDefault` = 키가 없으면 기본값 | ★★★ **API 계약(KDoc)** — `getOrDefault` 는 **JDK 의 계약** | (2) |
| `withDefault` 는 `getValue` 로 읽을 때만 | ★★ **API 계약(KDoc)** | (3) |
| `filterKeys` 가 원본 순서를 지킨다 | ★★ **API 계약(KDoc)** | (4) |
| `ConcurrentMap.getOrPut` — 넣기는 한 번, 람다는 여러 번일 수 있다 | ★★ **API 계약(KDoc)** | (5) |
| `{k=null}` 의 `getValue` 가 `null` | ★ **stdlib 구현**(`getOrImplicitDefault` → `getOrElseIfMissing`) — KDoc 은 이 칸을 적지 않는다 | (1)(3) |
| `filterKeys` 결과가 `LinkedHashMap` · 예외 문장 `Key b is missing in the map.` | ★ **stdlib 구현** | (3)(4) |
| 어느 `getOrPut` 오버로드가 붙나 | **언어 규칙(오버로드 해소 — 더 구체적인 수신자)** + 이 판의 바이트코드 관찰 | (5) |
| `…IfNull`/`…IfMissing` 넷 | **2.4 실험 API** — 이름·존재가 바뀔 수 있다 | (4) |

★★ **가장 조심할 자리** — `getOrPut` 의 재삽입은 **버그가 아니라 약속**이다. 그래서 「언젠가 고쳐지겠지」가 아니고, 2.4 는 고치는 대신 **새 이름을 옆에 세웠다.**

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 값에 `null` 이 없다(`Map<K, V>`) | `getOrElse` · `getOrPut` · `?:` | (1) — 두 상태가 안 생긴다 |
| 값에 `null` 이 있다 · 「키 없음」만 기본값 | `getOrDefault` · `containsKey` · (2.4 옵트인) `getOrElseIfMissing` | (1) |
| 없으면 만들어 넣는다 · 값이 `null` 일 수 있다 | (2.4 옵트인) `getOrPutIfMissing` 또는 표지 값 | (2)(4) |
| 위임 프로퍼티처럼 **`getValue` 로만** 읽는다 | `withDefault` | (3) |
| 여러 스레드가 넣는다 | `ConcurrentHashMap` **타입으로** 받고 `getOrPut` · 람다를 한 번만 → `computeIfAbsent` | (5) |
| 키·값으로 거른 **새 맵** | `filterKeys`·`filterValues` | (4) |
| 값만 바꾼 새 맵 | `mapValues` | [42번 주제](../42-transformations-map-flatmap-associate-zip/) |

## 핵심 문장

1. `m["k"]` 는 「키 없음」과 「값이 `null`」을 **같은 `null`** 로 준다 — 13개 함수 중 7개가 두 상태를 같은 결과로 답했다.
2. **`getOrPut` 은 값이 `null` 이면 키가 있어도 다시 넣는다** — KDoc 이 약속한 동작이고, 그래서 `null` 을 캐시하지 못한다.
3. **`getOrDefault` 는 키를, `getOrElse` 는 값을 본다** — `{k=null}` 에서 둘이 반대다.
4. **`withDefault` 는 `getValue` 에만 먹는다** — `[]` 는 모르고, 새로 만든 맵은 잃는다.
5. `ConcurrentHashMap.getOrPut` 은 **그 타입으로 받을 때만** `putIfAbsent` 판이고, 그래도 **람다는 여러 번** 불릴 수 있다.

## 관련 자료

- [41번 주제](../41-collection-creation-and-copying/) — ★★★ **선행.** 그쪽은 「**만들 때** 무엇을 고르나 · 어디서 복사되나」, 여기는 「**있는 맵에서** 어떻게 꺼내고 넣나」.
- [42번 주제](../42-transformations-map-flatmap-associate-zip/) — `mapValues` 는 `LinkedHashMap` · `Map.map` 은 `List` · `Map` 에는 `associate*` 가 없다. 여기서 다시 재지 않았다.
- [Java 41번](../../../java/syntax/41-map-api-merge-compute/) — Java `Map` 의 같은 세 상태 격자(`putIfAbsent`·`computeIfAbsent`·`merge`). **Java 쪽 정본**이다.
- [`cs/data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/) — 해시 테이블 원리. 그쪽은 **구조**, 여기는 **stdlib 함수의 경계 동작**이다.
- [03번 주제](../03-null-safe-types/) — `?:`(엘비스) 자체.

## 용어 풀이

> **키 없음 / 값이 `null`** — 맵에 그 키의 칸이 **아예 없는** 것과, 칸은 있는데 **값이 `null`** 인 것. `containsKey` 만 둘을 가른다(옛 함수 중).\
> 예: `mutableMapOf<String, Int?>()` 와 `mutableMapOf<String, Int?>("k" to null)`.

> **`getOrPut`** — 값이 있고 `null` 이 아니면 그 값, 아니면 람다를 불러 **넣고** 돌려준다(`MutableMap` 확장).

> **`getOrElse`** — 값이 있고 `null` 이 아니면 그 값, 아니면 람다 결과. **넣지 않는다.**

> **`getOrDefault`** — JDK 8 `Map` 의 메서드. **키가 없을 때만** 기본값.

> **`withDefault`** — 맵을 감싸 **`getValue` 로 읽을 때만** 쓰이는 기본값 함수를 단다.

> **`@ExperimentalStdlibApi`** — 쓰려면 `@OptIn` 이 필요한 stdlib 실험 API 표지.

> **오버로드 해소** — 같은 이름의 함수가 여럿일 때 컴파일러가 **정적 타입**으로 하나를 고르는 일. 더 구체적인 수신자(`ConcurrentMap`)가 이긴다.

## 더 들어가면

- **`ConcurrentMap.getOrPutIfNull`/`…IfMissing`** — `MapsJVM.kt` 에 있고 `computeIfAbsent`·`putIfAbsent` 를 쓴다(소스를 읽었고 **돌리지 않았다**).
- **위임 프로퍼티 `val name: String by map`** — `withDefault` 의 원래 자리다. [17번 주제](../17-delegated-properties/)가 `Map` 위임을 다룬다(이 문서는 돌리지 않았다).
- **경쟁 중 람다 호출 수** — 여러 스레드로 N판을 돌려 「몇 판 중 몇 판에서 2번 이상」을 세면 성질로 말할 수 있다. 이 판은 **재지 않았다.**
