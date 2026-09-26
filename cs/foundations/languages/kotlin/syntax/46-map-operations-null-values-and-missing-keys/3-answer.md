# kotlin/syntax/46 — `Map` 조작 — `getOrPut`/`getOrElse`/`mapValues`/`filterKeys` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `java`·`javap` 에서 실제로 얻었다.
> ★★ 아래 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적은 자리가 없다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ `getOrPut` 은 **`{k=null}` 을 `{k=9}` 로 바꾸고** · `getOrDefault` 는 `{k=null}` 에서 **`null`** · `getValue` 는 **`{}` 에서만 던진다** · `withDefault { 9 }["k"]` 는 **`{}` 에서도 `null`**

**출력**

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

**왜 그런가**

- ★★★ `getOrPut`·`getOrElse`·`?:`·`getOrPutIfNull` 은 **값이 `null` 이냐**만 본다 — `{}` 와 `{k=null}` 이 같은 칸이 되고, 넣는 쪽(`getOrPut`·`getOrPutIfNull`)은 `{k=null}` 을 **`{k=9}` 로 덮는다**(람다 `λ1`).
- ★★★ `getOrDefault`·`containsKey`·`getOrElseIfMissing`·`getOrPutIfMissing` 은 **키가 있느냐**를 본다 — `{k=null}` 에서 `null`(또는 `true`)을 주고 맵을 그대로 둔다(`λ0`).
- ★★ `getValue` 는 `{}` 에서 `NoSuchElementException`, `{k=null}` 에서 `null`. `withDefault { 9 }` 는 `getValue` 로 읽을 때만 `{}` 에서 `9` 를 주고, `[]` 로 읽으면 `null` 이다.

### 2. **7 / 13** — `m["k"]` · `get` · `getOrElse` · `getOrPut` · `?:` · `withDefault[…]` · `getOrPutIfNull`

**출력** — 1번 격자의 마지막 줄 `rows where the absent and null-value results are the same: 7 / 13`.

**왜 그런가**

- ★★ 옛 함수 중 두 상태를 **가르는 것**은 `getValue`(던짐 대 `null`)·`getOrDefault`(`9` 대 `null`)·`containsKey`(`false` 대 `true`)·`withDefault{…}.getValue`(`9` 대 `null`) 넷이다. 2.4 의 `…IfMissing` 둘이 여기에 더해진다.
- ★ 「같은 결과」는 **돌려준 값**만 견줬다 — 맵이 바뀌었는지까지 견주면 `getOrPut` 은 두 칸이 **맵까지** 같다(`{k=9}`).

### 3. ★★★ **`compute` 로그가 세 줄**(`#0`·`#1`·`#2`) · `d["b"]` 는 **`null`** · `d.getValue("b")` 는 **`0`** · `getOrDefault` 는 **`-1`** · 거른 맵의 `getValue` 는 **`NoSuchElementException`**

**출력**

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

**왜 그런가**

- ★★★ 람다가 `null` 을 돌려주니 `getOrPut` 이 `{u=null}` 을 넣고, 다음 호출은 그 `null` 을 「없음」으로 읽어 **다시 부른다.** 세 번 부르면 세 번 계산한다.
- ★★★ `withDefault` 는 KDoc 이 적은 대로 **`getValue` 에만** 먹는다 — `[]` 는 `null`, `getOrDefault` 는 JDK 메서드라 인자의 `-1`.
- ★★ `filterKeys { true }` 는 **새 `LinkedHashMap`** 을 만든다 — 감싼 껍데기가 없으니 `getValue("b")` 가 `Key b is missing in the map.` 으로 던진다.
- ★ `src["a"] = 100` 뒤에도 `fk`·`fv` 는 그대로다 — 새 맵이다(`fk === src: false`).

### 4. ★★ `viaConcurrent` 에는 **`ConcurrentMap.get` + `ConcurrentMap.putIfAbsent`** · `viaMutable` 에는 **`Map.get` + `Map.put`**

**출력**

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

**왜 그런가**

- ★★★ 확장 함수는 **정적 타입**으로 고른다 — `ConcurrentHashMap` 은 `ConcurrentMap` 이라 더 구체적인 `ConcurrentMap<K, V>.getOrPut` 이 이긴다. `MutableMap` 으로 받으면 그 판을 **볼 수 없다.**
- ★ 둘 다 `inline` 이라 `javap` 에 **stdlib 함수 호출이 아니라 풀린 본문**(`get`·`putIfAbsent`/`put`)이 보인다. 실행 결과는 같은 `1 1 {k=1}` 이다 — **차이는 경쟁이 있을 때만** 드러난다.

### 5. ★ **`counts {tea=3, cake=2, coffee=1}`** · `byLength {3=[tea], 4=[cake], 6=[coffee]}` · `missing 0`

**출력**

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

**왜 그런가**

- ★ `Map<String, Int>` 에는 `null` 값이 없으니 `getOrElse`·`getOrPut` 의 두 뜻이 **겹치지 않는다** — 이 주제의 함정은 값 타입이 `V?` 일 때만 난다.
- ★ `short` 는 키 길이 4 이하(`tea`·`cake`), `cheap` 은 값 5 미만(`tea`·`coffee`) — 둘 다 원본 순서다.

### 6. **계약이다** — KDoc 「``is not in this map or is mapped to a `null` ``… is put into the map」 · 구현은 `get(key)` 를 받아 **`== null`** 하나로 가른다

**왜 그런가**

- ★★★ 2-summary (2)의 발췌 — `getOrPut` 은 `val value = get(key)` → `if (value == null)` → `put(key, answer)`. **`containsKey` 를 부르지 않는다** — 부르지 않으니 두 상태를 가를 재료가 없다.
- ★★ 같은 KDoc 이 「`null` 값이 있을 맵에는 **권하지 않는다**」고 적고 2.4 의 `getOrPutIfNull`/`getOrPutIfMissing` 을 가리킨다 — 고치는 대신 **이름을 나눴다.**

### 7. `getOrDefault` 는 **키**를, `getOrElse` 는 **값**을 본다 — `getOrDefault` 는 **JDK 8 `Map` 의 메서드**다

**왜 그런가**

- ★★★ 2-summary (2)의 발췌 — `getOrElse` 는 `get(key) ?: defaultValue()`(값이 `null` 이면 기본값), `getOrDefault` 의 KDoc 은 「`if such a key is not present`」.
- ★★ `getOrDefault` 에는 `@PlatformDependent` 가 붙어 있다 — Kotlin 의 `Map` 인터페이스가 **JDK 의 메서드를 그대로 드러낸 것**이고, Java 쪽 같은 칸이 `null` 인 것은 [Java 41번](../../../java/syntax/41-map-api-merge-compute/)이 쟀다.

### 8. **`getValue` 로 읽을 때만** 나온다 — `[]`·`get`·`getOrDefault` 에는 안 나오고, `filterKeys` 등으로 **새로 만든 맵**에는 없다

**왜 그런가**

- ★★★ KDoc — 「`This implicit default value is used when the original map doesn't contain a value for the key specified and a value is obtained with [Map.getValue] function`」. 범위가 **글자로** 적혀 있다.
- ★★ 그리고 `getValue` 로 읽어도 **키가 있고 값이 `null`** 이면 기본값이 아니라 `null` 이다(1번 격자) — 이 판의 `getOrImplicitDefault` 가 `getOrElseIfMissing` 을 부르기 때문이다(구현 관찰).

### 9. **넣기는 한 번**(`putIfAbsent`)을 약속하고 **람다가 한 번만 불린다**는 약속하지 **않는다** — 경쟁 결과는 판마다 흔들리는 칸이다

**왜 그런가**

- ★★★ 2-summary (5)의 발췌 — 「`This method guarantees not to put the value into the map if the key is already there, but the [defaultValue] function may be invoked even if the key is already in the map.`」.
- ★★ 「경쟁 중 몇 번 불리나」는 한 판에서 0번 겹쳐도 **안전하다는 근거가 아니다** — 이 문서는 동시 실행 대신 **어느 호출이 붙었나(바이트코드)와 KDoc** 으로 물었다(제5의 상태).

### 10. `putIfAbsent`·`computeIfAbsent` 는 **`{k=null}` 을 없는 키처럼** 다룬다 — Kotlin 의 **`getOrPut`(=`getOrPutIfNull`)** 과 같은 편이다

**왜 그런가**

- ★★ [Java 41번](../../../java/syntax/41-map-api-merge-compute/) (1)의 격자 — `putIfAbsent("k", 5)` 는 `{k=null}` 에서 `null / {k=5}`, `computeIfAbsent` 는 `5 / {k=5}`. 둘 다 **값이 `null` 이면 넣는다.** 이 문서는 Java 쪽을 **다시 돌리지 않았다.**
- ★ 반대로 `getOrDefault` 는 두 언어에서 같은 메서드라 같은 칸(`null`)이다. 키만 보고 넣는 Java 메서드는 그 격자에 **없다** — Kotlin 2.4 의 `getOrPutIfMissing` 이 그 빈칸을 채운다.

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
| **없다** — 해시코드·주소·시간을 찍지 않았고 동시 실행을 하지 않았다 | 격자 13행 × 3열 · 같은 결과 행 수 · 람다 호출 수 · 실행 출력 |
| | stdlib 소스 발췌(줄 번호째) · `javap` 의 명령·상수 풀 번호 |
| | 모든 **종료 코드** |

> 근거 — 캡처 스크립트를 처음부터 다시 돌려 **블록 전체를 대조**했다.
>
> 실측 — `capture.sh blocks` 와 `capture.sh blocks-recheck` 를 처음부터 따로 돌려 `normalize-shaky.py` 로 대조했다 —\
> **블록 71개 · 동일 71 · 흔들린 칸 0 · ★고칠 것 0**(46\~49 네 주제를 한 캡처로 받았다). 추가한 정규화 규칙은 **없다**.

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `grid46.kt` | ★★★ null 대 키 없음 격자 — 13함수 × 3상태 | `kotlinc` → `java` (칸 수 검사·같은 행 수는 프로그램이 센다) |
| `shape46.kt` | ★★ `getOrPut` 재계산 로그 · `withDefault` 의 범위 · 거른 맵 | `kotlinc` → `java` |
| `conc46.kt` | ★★ 붙은 오버로드(`putIfAbsent` 대 `put`) | `kotlinc` → `java` → `javap -c -p`(전부 받은 뒤 `grep`) |
| `Maps.kt` · `MapWithDefault.kt` · `MapsJVM.kt` · `Collections.kt`(stdlib 소스 jar) | `getOrPut`·`getOrElse`·`getOrDefault`·`getValue`·`withDefault`·`filterKeys` KDoc 과 구현 · 2.4 새 함수 · `ConcurrentMap.getOrPut` | `unzip` → `grep`·`sed -n` |
| `form46.kt` | 형태 한 벌 | `kotlinc` → `java` |

**구현 의존 항목** — `{k=null}` 의 `getValue` 가 `null` 인 것 · 결과 맵의 클래스(`LinkedHashMap`) · 예외 문장 — 이 stdlib 판의 산출물이다.\
반면 **`getOrPut` 의 재삽입** · **`getOrDefault` 는 키를 본다** · **`withDefault` 는 `getValue` 에만** · **`ConcurrentMap.getOrPut` 의 한 번 넣기** 는 **API 계약(KDoc)** 이다.

**★ 던져 봤더니 예상과 달랐던 것 — 세 건**

1. ★★★ **2.4 stdlib 에 `getOrElseIfNull`·`getOrElseIfMissing`·`getOrPutIfNull`·`getOrPutIfMissing` 이 실험 API 로 들어와 있었다** — 옛 `getOrPut` KDoc 이 이제 그쪽을 쓰라고 가리킨다.
2. ★★ **`ConcurrentHashMap.getOrPut` 은 「원자적이지 않다」가 아니라 「넣기는 한 번, 람다는 여러 번일 수 있다」였다** — 그리고 그 약속은 **`ConcurrentHashMap` 타입으로 받을 때만** 붙는다(`MutableMap` 이면 `put` 판).
3. ★ **`getValue` 가 `{k=null}` 에서 던지지 않고 `null` 을 줬다** — 「`getValue` 는 값이 없으면 던진다」의 「없으면」은 **키**다.
