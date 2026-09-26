# kotlin/syntax/41 — 컬렉션 생성 — `listOf`/`mutableListOf`/`buildList`/`toList` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Constructing collections](https://kotlinlang.org/docs/constructing-collections.html)(요소로 만들기 `listOf`·`mutableListOf` · 빌더 함수 `buildList` · 복사 `toList()`·`toMutableList()` · 빈 컬렉션 `emptyList()`) — 이 문서는 그 페이지의 **목록**을 따르되, 문장은 인용하지 않고 **이 판의 stdlib 소스 jar**(`kotlin-stdlib-sources.jar` 2.4.20)를 근거로 삼는다((2)).
> **실행 검증** — 이 문서의 모든 출력·에러는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `java` 에서 실제로 얻었다.\
> `kotlinc` 6회(컴파일 실패 1벌) · `java` 4회 + 격자 스크립트 안에서 1회 · stdlib 소스 jar 에서 4곳.\
> ★★ 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적지 않았다. **「복사된 칸 N / M」은 스크립트가 스스로 센 것**이다.
> **버전** — `listOf`·`mutableListOf`·`toList`·`emptyList` 는 **1.0**. `buildList` 는 stdlib 소스에 **`@SinceKotlin("1.6")`**((2)) — ★ 그 전 판에서 실험 API 였는지는 **이 판에서 잴 수 없다**(컴파일러가 2.4.20 하나뿐이고 `-api-version` 격자는 돌리지 않았다).
> **경계** — ★★★ **런타임 클래스는 [`../../언어-특성/README.md`](../../언어-특성/README.md) §5 가 정본이다** — `listOf()`·`listOf("a")`·`listOf("a","b")`·`mutableListOf` 의 클래스는 거기 표에 있다. 여기 격자의 「런타임 클래스」 칸은 **짧게** 두고, 새로 잰 것은 **`===` 와 「원본을 고치면 따라 바뀌나」** 두 칸이다.\
> `List` 가 읽기 전용 **뷰**라는 것, `as MutableList` 로 뚫리는 것은 [40번 주제](../40-read-only-collections-and-runtime-types/)가 정본이다. `*arr`(spread)가 **`Arrays.copyOf` 로 복사**한다는 것은 [09번 주제](../09-varargs-spread-local-and-infix-functions/) (2)가 바이트코드로 쟀다 — 여기서는 인용한다. `buildList` 가 받는 **수신자 람다**(`MutableList<E>.() -> Unit`)는 [37번 주제](../37-lambdas-with-receiver-and-type-safe-builders/)다.
> 이 본문은 Claude 작성이다(원고 없음).

★★★ **본체는 첫째 창이다** — 「**복사 격자 — 만드는 꼴마다 원본과 같은 객체인가 · 원본을 고치면 따라 바뀌나**」. 복사 여부는 **타입에 안 나온다** — 전부 `List<Int>` 다. 실행해서 **원본을 고쳐 봐야** 보인다.

## 이 주제가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **언어 보장 / API 계약** | 문서·서명이 약속한 것 | ★★ 반환 **타입**이 가변성을 정한다(`List` 대 `MutableList`) · `toList()`·`toMutableList()` 는 「**새**」 리스트 · `buildList` 는 람다 안에서 `MutableList`, 결과는 `List` |
| **구현(stdlib · 백엔드)** | 이 판의 stdlib·kotlinc 가 실제로 하는 것 | ★ `*arr` 가 **새 배열**(09 — `Arrays.copyOf`) · ★★★ **`toList()` 가 원소 수로 클래스를 고른다**(0개 `EmptyList` · 1개 `SingletonList` · 그 이상 `ArrayList`) · `listOf(vararg)` 가 **`asList()`**(감싸기) · `buildList` 결과가 **빌더 객체 그 자체**(`ListBuilder`) · `emptyList()` 가 **싱글턴** |
| **이 판의 관찰** | kotlinc 2.4.20 에서 이번에 본 것 | ★ `buildList` 의 `this` 를 밖에 담으려 하면 **추론 에러**((3)) · 진단 문구 |

## 이 판

```text
===== kotlinc -version =====
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | (이 주제에는 없다) | 해시코드·`identityHashCode` 를 찍지 않았다 — 같은 객체인지는 **`===`** 로만 물었다 |
| 안 흔들린다 | 격자 15행 · 복사 수 · 런타임 클래스 이름 | 결정적이다 |
| 안 흔들린다 | stdlib 소스 발췌(줄 번호째) | jar 가 같으면 같다 |
| 안 흔들린다 | 진단 문구·`파일:줄:칸` · 종료 코드 | 결정적이다 |

★ 근거 — 캡처 스크립트를 처음부터 두 번 돌려 **블록 전체를 바이트 단위로 대조**했다(수치는 3-answer 의 「실행 검증」).

## 한눈에 — 쉽게 말하면

**리스트를 만드는 함수는 「복사기로 뜨느냐, 원본에 창을 내느냐」가 갈린다.** `src.toList()` 는 **복사기**다 — 뜬 뒤 원본을 고쳐도 사본은 그대로다. `arr.asList()` 는 **창**이다 — 원본 배열을 고치면 창으로 그대로 보인다. 둘 다 이름만 보면 「리스트로 만든다」다.
★ 그리고 **복사가 어디서 일어나는지**도 겉보기와 다르다. `listOf(*arr)` 에서 복사하는 것은 `listOf` 가 **아니라** 호출 자리의 `*` 다([09번 주제](../09-varargs-spread-local-and-infix-functions/)) — `listOf` 자신은 받은 배열에 **창을 낼 뿐**이다.
`buildList { }` 는 **공사장**이다 — 안에서는 마음대로 짓고, 문을 닫고 나오면 **같은 건물이 잠긴다**(복사 없이).

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 복사기로 뜬다 | `toList()` · `toMutableList()` · `ArrayList(src)` · `List(n) { }` | (1) |
| 원본에 창을 낸다 | `arr.asList()` · `val ro: List<Int> = src` | (1) · [40번 주제](../40-read-only-collections-and-runtime-types/) |
| 복사는 호출 자리의 `*` 가 한다 | `listOf(*arr)` = `Arrays.copyOf` + `asList()` | (1)(2) · [09번 주제](../09-varargs-spread-local-and-infix-functions/) |
| 원소 수에 따라 다른 복사기 | `toList()` — 0 · 1 · 그 이상 | (2) ★ |
| 공사장 — 나오면 같은 건물이 잠긴다 | `buildList { }` — 빌더 객체가 그대로 결과 | (3) ★ |
| 모두가 쓰는 빈 방 하나 | `emptyList()` — 싱글턴 | (4) |

```text
   만드는 꼴                          원본                결과 객체                     원본을 고치면
   val ro: List<Int> = src            src ─────────────> 같은 객체                      따라 바뀐다
   src.toList()                       src ──복사──>       새 ArrayList (원소 2개 이상)    안 바뀐다
   buildList { addAll(src) }          src ──addAll──>     빌더(ListBuilder) → 잠금       안 바뀐다
   listOf(*arr)                       arr ──* 가 복사──>   새 배열 ──asList()──> 창       안 바뀐다 (사본의 창)
   arr.asList()                       arr ─────────────> 창 (Arrays$ArrayList)          따라 바뀐다

   src.toList() 의 결과 클래스          원소 0개 → EmptyList (싱글턴)
                                      원소 1개 → Collections$SingletonList
                                      원소 2개 이상 → java.util.ArrayList
```

## 이 주제가 답하려는 질문

1. 리스트를 만드는 꼴마다 **복사가 일어나나** — 일어나면 **어디서**.
2. `toList()` 는 **무엇을** 돌려주나 — 원소 수에 따라.
3. `buildList` 의 「안에서만 가변」은 **누가** 지키나 — 타입인가, 객체인가.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **복사 격자(`===` + 원본 변경)** | 꼴마다 같은 객체인가 · 따라 바뀌나((1)) | ★ **본체 창** |
| ★★ **stdlib 소스 jar 발췌** | `toList`·`listOf`·`emptyList`·`buildList` 가 **실제로 하는 일**((2)(3)) | [28번 주제](../28-generics-variance-in-out-star-where/) (3)과 같은 창 |
| ★★ **원소 수 격자** | `toList()` 결과 클래스가 0·1·2·3 에서 무엇인가((2)) | — |
| ★ **캐스트해 고치기** | 「나오면 읽기 전용」을 **객체가** 지키나((2)(3)) | [40번 주제](../40-read-only-collections-and-runtime-types/) (1)의 창 |
| ★ **컴파일 에러** | 빌더의 `this` 를 밖에 담으려 할 때((3)) | 이 갈래의 기본 창 |
| **인용 — 다시 안 잰다** | `listOf(…)`·`mutableListOf` 의 런타임 클래스 · `*` 의 `Arrays.copyOf` | [`../../언어-특성/README.md`](../../언어-특성/README.md) §5 · [09번 주제](../09-varargs-spread-local-and-infix-functions/) (2) |
| **부적용 — 실행 시간·할당** | 「`buildList` 가 빠르다」·「`toList` 는 비싸다」는 **재지 않았다** — 이 문서는 **복사가 일어나느냐**만 본다 | — |

### (1) ★★★ 복사 격자 — 원본과 같은가, 따라 바뀌나

**언제 쓰나** — 받은 리스트를 **보관**하거나 **밖에 내줄** 때, 「이것은 사본인가」를 가려야 할 때.

칸마다 **새 원본**(`mutableListOf(1, 2, 3)` 또는 `arrayOf(1, 2, 3)`)을 만들고, 결과를 만든 **뒤에** 원본의 0번을 `99` 로 고친다. 결과의 0번이 `99` 가 되면 「따라 바뀐다」다.

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

```python
# grid41.py
import subprocess
import sys

d = sys.argv[1]
out = subprocess.run(["java", "-cp", d + ":kotlin-stdlib.jar", "Make41Kt"],
                     capture_output=True, text=True, check=True).stdout
print("\t".join(["form", "runtime class", "=== src", "follows src[0]=99", "copied?"]))
copied = total = 0
for line in out.splitlines():
    cells = line.split("\t")
    if len(cells) != 4:
        raise SystemExit("cell count mismatch: " + line)
    name, klass, same, follows = cells
    if follows == "-":
        verdict = "(no source)"
    else:
        total += 1
        if same != "true" and follows == "false":
            copied += 1
            verdict = "copy"
        else:
            verdict = "shares"
    print("\t".join([name, klass, same, follows, verdict]))
print(f"cells that copied: {copied} / {total}")
```

```text
===== kotlinc make41.kt -d o41m =====
(exit 0)
```

```text
===== python3 grid41.py o41m =====
form	runtime class	=== src	follows src[0]=99	copied?
val ro: List<Int> = src	java.util.ArrayList	true	true	shares
src.toList()	java.util.ArrayList	false	false	copy
src.toMutableList()	java.util.ArrayList	false	false	copy
buildList { addAll(src) }	kotlin.collections.builders.ListBuilder	false	false	copy
List(src.size) { src[it] }	java.util.ArrayList	false	false	copy
ArrayList(src)	java.util.ArrayList	false	false	copy
listOf(*arr)	java.util.Arrays$ArrayList	-	false	copy
mutableListOf(*arr)	java.util.ArrayList	-	false	copy
arrayListOf(*arr)	java.util.ArrayList	-	false	copy
arr.asList()	java.util.Arrays$ArrayList	-	true	shares
arr.toList()	java.util.Arrays$ArrayList	-	false	copy
listOf(1, 2, 3)	java.util.Arrays$ArrayList	-	-	(no source)
listOf(1)	java.util.Collections$SingletonList	-	-	(no source)
emptyList()	kotlin.collections.EmptyList	-	-	(no source)
mutableListOf()	java.util.ArrayList	-	-	(no source)
cells that copied: 9 / 11
(exit 0)
```

- ★★★ **원본이 있는 11칸 중 9칸이 복사**다. 복사가 아닌 두 칸은 **`val ro: List<Int> = src`**(같은 객체 — 40번 주제의 뷰)와 **`arr.asList()`**(배열의 창)다.
- ★★★ **`listOf(*arr)` 는 복사**다 — 그런데 결과 클래스가 **`arr.asList()` 와 같은 `Arrays$ArrayList`** 다. 클래스로는 못 가른다. 가르는 것은 **`*` 가 호출 자리에서 배열을 복사한 것**이다((2) · [09번 주제](../09-varargs-spread-local-and-infix-functions/) (2)).
- ★★ **`src.toList()` 의 결과가 `java.util.ArrayList`** 다 — 원소가 셋이라서다((2)). 사본이지만 **가변 클래스**다.
- ★★ **`buildList { addAll(src) }` 는 복사** — 원소를 **`addAll` 로 옮겨 담았으니** 당연하다. 결과 클래스는 **`ListBuilder`**((3)).
- ★ **`arr.toList()` 도 `Arrays$ArrayList`** 인데 **복사**다 — 역시 클래스로는 `asList()` 와 못 가른다.
- ★ 원본이 없는 네 칸(`listOf(1, 2, 3)` · `listOf(1)` · `emptyList()` · `mutableListOf()`)은 클래스만 적었다 — §5 표와 같다.

### (2) ★★★ `toList()` 는 원소 수로 클래스를 고른다

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

```text
===== kotlinc tolist41.kt -d o41t =====
(exit 0)
===== java -cp o41t:kotlin-stdlib.jar Tolist41Kt =====
list n=0  kotlin.collections.EmptyList  === src: false
list n=1  java.util.Collections$SingletonList  === src: false
list n=2  java.util.ArrayList  === src: false
list n=3  java.util.ArrayList  === src: false
set n=2   java.util.ArrayList
seq n=2   java.util.ArrayList
cast add: [1, 2, 3]
cast add n=1: java.lang.UnsupportedOperationException
toList of toList === : false
(exit 0)
```

```text
===== unzip -o -q kotlin-stdlib-sources.jar commonMain/kotlin/collections/Collections.kt commonMain/generated/_Collections.kt jvmMain/kotlin/collections/CollectionsJVM.kt =====
(exit 0)
===== grep -n -E '^public (fun <T> emptyList|fun <T> listOf\(vararg|actual fun <T> listOf\(element)' commonMain/kotlin/collections/Collections.kt jvmMain/kotlin/collections/CollectionsJVM.kt =====
commonMain/kotlin/collections/Collections.kt:75:public fun <T> emptyList(): List<T> = EmptyList
commonMain/kotlin/collections/Collections.kt:81:public fun <T> listOf(vararg elements: T): List<T> = if (elements.size > 0) elements.asList() else emptyList()
jvmMain/kotlin/collections/CollectionsJVM.kt:21:public actual fun <T> listOf(element: T): List<T> = java.util.Collections.singletonList(element)
(exit 0)
===== sed -n '1501,1510p' commonMain/generated/_Collections.kt =====
public fun <T> Iterable<T>.toList(): List<T> {
    if (this is Collection) {
        return when (size) {
            0 -> emptyList()
            1 -> listOf(if (this is List) get(0) else iterator().next())
            else -> this.toMutableList()
        }
    }
    return this.toMutableList().optimizeReadOnlyList()
}
(exit 0)
===== sed -n '183,186p' commonMain/kotlin/collections/Collections.kt =====
@SinceKotlin("1.6")
@kotlin.internal.InlineOnly
@Suppress("LEAKED_IN_PLACE_LAMBDA", "WRONG_INVOCATION_KIND", "DEPRECATION")
public inline fun <E> buildList(@BuilderInference builderAction: MutableList<E>.() -> Unit): List<E> {
(exit 0)
```

```text
   Iterable<T>.toList()          (stdlib 소스 _Collections.kt 1501~1510행)
     Collection 인가?
       ├─ size 0  → emptyList()                 → EmptyList (싱글턴 — 복사할 것이 없다)
       ├─ size 1  → listOf(원소)                → Collections.singletonList(원소)
       └─ 그 이상 → this.toMutableList()         → ArrayList(원소 복사)   ★ 가변 클래스
     아니면(Sequence 등) → toMutableList().optimizeReadOnlyList()
```

- ★★★ **0 → `EmptyList` · 1 → `Collections$SingletonList` · 2·3 → `java.util.ArrayList`** — 소스의 `when (size)` 세 갈래 그대로다. `Set` 도 `Sequence` 도 원소 둘이면 `ArrayList` 다.
- ★★★ **`toList()` 의 결과를 캐스트하면 원소 수에 따라 갈린다** — 둘일 때는 **`add` 가 통과**해 `[1, 2, 3]`, 하나일 때는 **`UnsupportedOperationException`**. 같은 함수의 결과가 **원소 수에 따라** 가변이기도 하고 아니기도 하다. 원본은 어느 쪽이든 안 바뀐다(사본이므로).
- ★★ **`toList()` 의 `toList()` 도 새 객체**다(`=== false`) — 「이미 읽기 전용이면 그대로 돌려준다」가 **아니다**(Java `List.copyOf` 는 이미 불변이면 복사하지 않는다 — [Java 40번](../../../java/syntax/40-list-set-and-immutable-factories/)). 원소가 둘 이상이면 **매번 복사**한다. ★ **빈 리스트만 예외**다((4)의 `3`).
- ★★ **`listOf(vararg)` 는 `elements.asList()`** — 받은 배열을 **감쌀 뿐 복사하지 않는다.** `listOf(1, 2, 3)` 처럼 쓰면 그 배열은 **호출 자리가 새로 만든 것**이라 문제가 없고, `listOf(*arr)` 면 **`*` 가 복사**한다. 어느 쪽이든 복사는 `listOf` 밖에서 일어난다.
- ★ **`listOf(element)` 하나짜리는 JVM 에서 `Collections.singletonList`** — `jvmMain` 쪽 `actual` 이다(플랫폼 구현).
- ★ 이 세 갈래는 **stdlib 구현**이다 — `toList()` 의 계약은 「새 읽기 전용 리스트」까지이고, **어느 클래스인지는 약속하지 않는다.**

### (3) ★★ `buildList` — 안에서만 가변, 나오면 **같은 객체가** 잠긴다

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

```text
===== kotlinc build41.kt -d o41b =====
(exit 0)
===== java -cp o41b:kotlin-stdlib.jar Build41Kt =====
inside: kotlin.collections.builders.ListBuilder
built: kotlin.collections.builders.ListBuilder  is MutableList: true
same object: true
cast add: java.lang.UnsupportedOperationException
leaked add: java.lang.UnsupportedOperationException
built: [1, 2]
(exit 0)
```

- ★★★ **`inside === built` 가 `true`** — 람다 안의 `this`(`ListBuilder`)가 **그대로 결과**다. `buildList` 는 **나올 때 복사하지 않는다.**
- ★★★ **나온 뒤에는 객체가 거부한다** — 캐스트한 `add` 도, 밖에 빼 둔 `this` 로 한 `add` 도 **`UnsupportedOperationException`**. `built` 는 끝까지 `[1, 2]`. `toList()`((2))와 달리 **「나오면 읽기 전용」을 타입이 아니라 객체가 지킨다.**
- ★★ **`is MutableList` 는 `true`** — `ListBuilder` 는 `MutableList` 를 구현한 클래스다. [40번 주제](../40-read-only-collections-and-runtime-types/) (1)의 결론대로 **`true` 는 「고칠 수 있다」가 아니다.**

**타입 인자를 안 쓰고 `this` 를 밖에 담으면**

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

```text
===== kotlinc leak41.kt -d o41l =====
leak41.kt:3:17: error: type mismatch: inferred type is 'CapturedType(out MutableList<Int>)#2', but 'CapturedType(out MutableList<Int>)#1' was expected.
    val built = buildList {
                ^^^^^^^^^^^
(exit 1)
```

- ★★ **`buildList<Int> { … }` 가 아니면 컴파일이 안 됐다** — 「`type mismatch: inferred type is 'CapturedType(out MutableList<Int>)#2', but 'CapturedType(out MutableList<Int>)#1' was expected.`」. 원소 타입을 **람다 몸통에서 추론**하는 중에 `this` 를 바깥 `var` 에 담으면 추론이 꼬인다(빌더 추론 — 소스의 `@BuilderInference`). 문구가 무엇을 말하는지는 **이 판의 관찰**로만 적는다.
- ★ 두 파일은 **`<Int>` 하나만** 다르다 — `build41.kt` 3번째 줄이 `buildList<Int> {`, `leak41.kt` 는 `buildList {`.

### (4) ★ `emptyList()` 는 싱글턴이다

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

```text
===== kotlinc empty41.kt -d o41e =====
(exit 0)
===== java -cp o41e:kotlin-stdlib.jar Empty41Kt =====
1 true
2 true
3 true
4 false
5 true  true
6 kotlin.collections.EmptyList
(exit 0)
```

- ★★ **`emptyList<String>() === emptyList<Int>()` 가 `true`** — 타입 인자가 달라도 **같은 객체**다. 소스가 `= EmptyList`(`object`)다((2)). 제네릭은 소거되므로 하나로 충분하다.
- ★★ **`listOf<Int>()` 도, 빈 리스트의 `toList()` 도 그 객체**다(`2`·`3`) — 빈 것은 **복사할 것이 없다.**
- ★ **`mutableListOf<Int>()` 는 매번 새것**이다(`4 false`) — 가변이면 공유할 수 없다.
- ★ **`==` 는 내용 비교**라 빈 읽기 전용과 빈 가변이 **같다**(`5 true true`) — [32번 주제](../32-equality-and-equals-contract/)의 `==` 가 `equals` 인 것.

## 문법 — 형태와 규칙

**형태** — 내부 가변 리스트를 **뷰로** 내주는 것과 **사본으로** 내주는 것, 그리고 `buildList`.

```kotlin
// form41.kt
class Cart {
    private val lines = mutableListOf<String>()
    fun add(item: String) { lines += item }
    fun view(): List<String> = lines
    fun snapshot(): List<String> = lines.toList()
}

fun main() {
    val cart = Cart()
    cart.add("apple")
    val v = cart.view()
    val s = cart.snapshot()
    cart.add("pear")
    println("view: $v")
    println("snapshot: $s")
    val header = buildList {
        add("#")
        addAll(cart.view())
    }
    println("built: $header")
}
```

```text
===== kotlinc form41.kt -d o41z =====
(exit 0)
===== java -cp o41z:kotlin-stdlib.jar Form41Kt =====
view: [apple, pear]
snapshot: [apple]
built: [#, apple, pear]
(exit 0)
```

**규칙 불릿**

- **만드는 순간 가변성을 고른다** — `listOf`·`buildList`·`toList` 는 `List`, `mutableListOf`·`toMutableList`·`arrayListOf` 는 `MutableList`((1)).
- **복사가 일어나는 자리** — `toList()`·`toMutableList()`·`ArrayList(src)`·`List(n) { }`·`buildList { addAll(…) }` 는 **복사**, `val ro: List = src`·`arr.asList()` 는 **공유**((1)).
- `listOf(*arr)` 의 복사는 **`*` 가** 한다 — `listOf` 는 감쌀 뿐이다((2)).
- `toList()` 의 **클래스는 원소 수**가 정한다 — 0·1·그 이상((2)).
- `buildList` — 람다 안의 `this` 가 결과이고, **나오면 객체가 잠긴다**((3)).
- `emptyList()` — **하나**다((4)).

## 어디서 틀리나

1. ★★★ **`toList()` 결과는 캐스트해도 못 고친다고 믿는다.** 원소 둘 이상이면 **`ArrayList`** 라 캐스트한 `add` 가 통과한다((2)) — 원본은 안전하지만 **사본을 받은 쪽끼리** 공유하면 샌다.
2. ★★★ **`arr.asList()` 를 사본으로 쓴다.** 창이다 — 배열을 고치면 따라 바뀐다((1)).
3. ★★ **`listOf(*arr)` 와 `arr.asList()` 를 같은 것으로 본다.** 클래스는 같고 **복사 여부가 반대**다((1)).
4. ★★ **`toList()` 가 이미 읽기 전용인 것은 그대로 돌려준다고 믿는다.** 원소가 둘 이상이면 **매번 복사**한다((2)) — Java `List.copyOf` 와 다르다.
5. ★★ **`buildList` 의 결과를 캐스트해 고칠 수 있다고 본다.** 객체가 거부한다((3)) — `toList()` 와 반대다.
6. ★ **`buildList` 안의 `this` 를 밖에 빼 두고 나중에 쓴다.** 나온 뒤에는 `UnsupportedOperationException` 이고, 타입 인자가 없으면 **컴파일부터 안 된다**((3)).
7. ★ **빈 리스트를 `===` 로 가린다.** 전부 같은 객체다((4)).

## 구현 세부사항 대 언어 보장

| 항목 | 어느 쪽인가 | 근거 |
|---|---|---|
| 반환 **타입**이 가변성을 정한다(`List` 대 `MutableList`) | ★★★ **언어 보장**(서명) | (1) |
| `toList()`·`toMutableList()` 가 **새** 리스트 | **API 의 뜻**(「복사」 함수) — 이 판에서 `===` 로 확인. 함수 주석은 **싣지 않았다** | (1)(2) |
| `*arr` 가 새 배열 | **JVM 백엔드 구현**(`Arrays.copyOf`) — 이 문서는 언어 명세 문장을 확인하지 않았다 | [09번 주제](../09-varargs-spread-local-and-infix-functions/) (2) |
| `toList()` 가 **원소 수로 클래스**를 고른다 | ★★★ **stdlib 구현** | (2) — 소스 `when (size)` |
| `listOf(vararg)` = `asList()` · `listOf(e)` = `singletonList` | ★★ **stdlib 구현** | (2) |
| `buildList` 결과가 **빌더 객체 그 자체** · 나오면 객체가 거부 | ★★ **stdlib 구현** | (3) |
| `emptyList()` 가 싱글턴 | ★ **stdlib 구현**(`object EmptyList`) | (2)(4) |
| `buildList` 의 `@SinceKotlin("1.6")` | **stdlib 판의 사실** — 그 전 실험 여부는 **못 쟀다** | (2) |
| 빌더 추론 에러 문구 | **이 판의 관찰** | (3) |

★★ **가장 조심할 자리** — 「`toList()` 는 읽기 전용 사본을 준다」까지가 계약이다. 「**캐스트해도 못 고친다**」는 계약이 아니고, 이 판에서는 **원소 수에 따라 참이기도 거짓이기도** 하다((2)). 방어 복사의 목적(원본 보호)은 지켜지지만 **사본 자체가 잠긴다고 믿으면 틀린다.**

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 원소를 알고 있고 안 바꾼다 | `listOf(…)` | (1) — `List` 타입 |
| 원소를 알고 있고 **나중에 더한다** | `mutableListOf(…)` | (1) — `MutableList` 타입 |
| 조건·반복으로 **지은 뒤 잠근다** | ★ `buildList { }` | (3) — 나오면 **객체가** 거부 · 나올 때 복사 없음 |
| 받은 리스트를 **보관**하거나 **밖에 내준다**(방어 복사) | ★ `toList()` | (1)(2) — 원본과 끊긴다 |
| 사본을 **고쳐 쓸** 것이다 | `toMutableList()` | (1) — 타입으로 가변임을 밝힌다 |
| 배열을 리스트로 **보기만** 한다(원본 추적) | `arr.asList()` | (1) — 창 |
| 배열을 리스트로 **떼어 낸다** | `arr.toList()` · `listOf(*arr)` | (1) — 복사 |
| 빈 리스트를 돌려준다 | `emptyList()` | (4) — 하나를 공유 |

## 핵심 문장

1. 복사 여부는 **타입에 안 나온다** — 원본이 있는 11꼴 중 9꼴이 복사, `val ro: List = src` 와 `arr.asList()` 만 **공유**다.
2. `listOf(*arr)` 의 복사는 **`*` 가** 한다 — `listOf` 는 받은 배열을 `asList()` 로 **감쌀 뿐**이다.
3. `toList()` 는 **원소 수로 클래스를 고른다** — 0개 `EmptyList` · 1개 `SingletonList` · 그 이상 `ArrayList`. 그래서 **캐스트한 `add` 가 원소 수에 따라** 통과하기도 한다.
4. `buildList` 는 **빌더 객체를 그대로** 돌려주고, 나온 뒤에는 **객체가** 고치기를 거부한다.
5. `emptyList()` 는 **싱글턴**이다 — 타입 인자가 달라도, `listOf()` 여도, 빈 것의 `toList()` 여도 같은 객체다.

## 관련 자료

- [40번 주제](../40-read-only-collections-and-runtime-types/) — ★★★ **선행.** `List` 는 뷰 · `as MutableList` 로 뚫린다 · `is MutableList` 가 Java 클래스를 못 가린다. 그쪽은 「**받은 것**이 무엇인가」, 여기는 「**만들 때** 무엇을 고르나 · 어디서 복사되나」.
- [`../../언어-특성/README.md`](../../언어-특성/README.md) §5 — 런타임 클래스 실측표 · 방어 복사의 필요.
- [09번 주제](../09-varargs-spread-local-and-infix-functions/) (2) — `*` 가 `Arrays.copyOf` 로 복사한다.
- [37번 주제](../37-lambdas-with-receiver-and-type-safe-builders/) — `buildList` 가 받는 수신자 람다.
- [32번 주제](../32-equality-and-equals-contract/) — `==` 와 `===`.
- [Java 40번](../../../java/syntax/40-list-set-and-immutable-factories/) — `List.copyOf` 는 이미 불변이면 복사하지 않는다(여기 `toList()` 와 대비).
- [목록의 **42번 주제**](../42-transformations-map-flatmap-associate-zip/) — 변환 연산(`map`·`flatMap`·`associate`). [목록의 **43번 주제**](../43-filter-search-and-empty-collections/) — 빈 컬렉션에서의 동작.

## 용어 풀이

> **방어 복사(defensive copy)** — 받은 것·내줄 것을 **사본으로** 바꿔 원본과 끊는 것.\
> 예: `fun snapshot(): List<String> = lines.toList()`.

> **`buildList`** — 수신자 람다 안에서 `MutableList` 로 짓고, 결과를 `List` 로 돌려주는 stdlib 함수.

> **`ListBuilder`** — `buildList` 가 JVM 에서 쓰는 빌더 클래스. 짓는 동안은 가변이고 **끝나면 스스로 잠긴다.**

> **`SingletonList`** — 원소 하나짜리 `java.util.Collections.singletonList` 의 클래스. 고치는 메서드가 전부 거부한다.

> **싱글턴(singleton)** — 프로그램 전체에 **하나뿐인** 객체. `emptyList()` 의 `EmptyList` 가 그것이다.

> **빌더 추론(builder inference)** — `buildList { add(1) }` 처럼 **람다 몸통에서** 타입 인자를 추론하는 것. 소스에 `@BuilderInference` 로 표시돼 있다.

## 더 들어가면

- **`Set`·`Map` 쪽** — `toSet()`·`buildMap`·`emptyMap()` 이 같은 모양인지 이 문서는 **던지지 않았다.** `toList()` 의 세 갈래와 같은 `when (size)` 가 있을 것으로 보이지만 소스를 **열지 않았다.**
- **`optimizeReadOnlyList()`** — `Collection` 이 아닌 입력(`Sequence`)의 `toList()` 가 거치는 길이다((2)의 그림). 원소 둘에서 `ArrayList` 였다 — 0·1 에서 무엇이 되는지는 **던지지 않았다.**
- **복사 비용** — 이 문서는 「복사가 일어나느냐」만 봤다. 원소 수에 따른 시간·할당은 **재지 않았다.**
