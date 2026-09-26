# kotlin/syntax/41 — 컬렉션 생성 — `listOf`/`mutableListOf`/`buildList`/`toList` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `java` 에서 실제로 얻었다.
> ★★ 아래 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적은 자리가 없다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **복사 9 / 11** — 복사가 아닌 것은 **`val ro: List<Int> = src`**(`=== true` · 따라 바뀜)와 **`arr.asList()`**(따라 바뀜) 둘뿐이다

**출력**

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

**왜 그런가**

- ★★★ 앞의 것은 **같은 객체**([40번 주제](../40-read-only-collections-and-runtime-types/)의 뷰), 뒤의 것은 **배열의 창**이다. 나머지는 원소를 새 저장소로 **옮겨 담는다.**
- ★★ `listOf(*arr)`·`arr.toList()`·`arr.asList()` 가 **전부 `Arrays$ArrayList`** 다 — 클래스로는 복사 여부를 못 가른다(6번).

### 2. ★★★ 0 → `EmptyList` · 1 → `Collections$SingletonList` · 2·3 → `java.util.ArrayList` · `set`·`seq` 도 `ArrayList` · **`cast add: [1, 2, 3]`**(원소 둘 — 통과) · **`cast add n=1: UnsupportedOperationException`** · `toList of toList === : false`

**출력**

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

**왜 그런가**

- ★★★ 소스의 `when (size)` 가 **0 → `emptyList()` · 1 → `listOf(원소)` · 그 이상 → `toMutableList()`** 다. 셋째 갈래가 `ArrayList` 를 **그대로** 돌려준다 — 그래서 캐스트한 `add` 가 통과한다.
- ★★ 원소 하나면 `singletonList` 라 **객체가** `add` 를 거부한다. 같은 함수가 원소 수에 따라 **다른 성질의 객체**를 준다.

### 3. ★★ `inside: …ListBuilder` · `built: …ListBuilder  is MutableList: true` · **`same object: true`** · `cast add: UnsupportedOperationException` · `leaked add: UnsupportedOperationException` · `built: [1, 2]`

**출력**

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

**왜 그런가**

- ★★★ **람다 안의 `this` 가 그대로 결과**다 — `buildList` 는 나올 때 **복사하지 않고 같은 객체를 잠근다.**
- ★★ 잠근 뒤에는 **어느 참조로 고쳐도** 객체가 거부한다 — 캐스트한 참조도, 밖에 빼 둔 `this` 도.
- ★ `is MutableList` 가 `true` 인 것은 [40번 주제](../40-read-only-collections-and-runtime-types/)의 결론 그대로 — 「고칠 수 있다」가 아니다.

### 4. ★ **컴파일 안 된다** — 3번째 줄 「`type mismatch: inferred type is 'CapturedType(out MutableList<Int>)#2', but 'CapturedType(out MutableList<Int>)#1' was expected.`」

**출력**

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

**왜 그런가**

- ★★ `buildList` 는 타입 인자를 **람다 몸통에서 추론**한다(빌더 추론). 그 몸통에서 `this` 를 바깥 `MutableList<Int>?` 변수에 담자 추론이 두 「포획 타입」을 못 맞췄다. `<Int>` 를 적으면 추론할 것이 없어져 통과한다(3번).
- ★ 문구의 뜻을 **해설할 근거는 없다** — 이 판의 관찰로만 적는다.

### 5. ★★ `1 true` · `2 true` · `3 true` · `4 false` · `5 true  true` · `6 kotlin.collections.EmptyList`

**출력**

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

**왜 그런가**

- ★★ `emptyList()` 는 **`= EmptyList`**(2번 소스 발췌) — `object` 하나다. 타입 인자가 달라도, `listOf()` 여도, 빈 것의 `toList()`(`size 0 → emptyList()`)여도 **그 하나**다.
- ★ `mutableListOf()` 는 가변이라 **매번 새것**(`4`). `==` 는 내용 비교라 빈 것끼리 같다(`5`).

### 6. `listOf(vararg)` 는 **`elements.asList()`** — 받은 배열을 **감쌀 뿐**이다 · 복사는 **호출 자리의 `*`** 가 한다(`Arrays.copyOf` — [09번 주제](../09-varargs-spread-local-and-infix-functions/) (2))

**왜 그런가**

- ★★★ 2번의 소스 발췌 81행이 `= if (elements.size > 0) elements.asList() else emptyList()` 다. `listOf` 안에는 복사가 **없다.**
- ★★ 그래서 `listOf(*arr)` 는 「**`*` 가 만든 사본**의 창」이고, `arr.asList()` 는 「**원본**의 창」이다 — 클래스가 같고 복사 여부가 반대인 이유다.

### 7. 「**원본과 끊긴 사본**」까지는 참이다 — 「**사본 자체가 잠겼다**」는 원소 수에 따라 **참이기도 거짓이기도** 하다

**왜 그런가**

- ★★★ 원소 둘이면 사본이 `ArrayList` 라 캐스트한 `add` 가 **통과**했고(`[1, 2, 3]`), 하나면 `singletonList` 라 **거부**했다.
- ★ 방어 복사의 목적(원본 보호)은 어느 쪽이든 지켜진다. 그러나 그 사본을 **여러 곳이 공유**하면 한 곳의 캐스트가 나머지에 비친다.

### 8. `buildList` 는 **객체**가 지킨다(나오면 `ListBuilder` 가 스스로 잠긴다) · `toList()`(원소 둘 이상)는 **타입만** 지킨다(객체는 평범한 `ArrayList`)

**왜 그런가**

- ★★ [40번 주제](../40-read-only-collections-and-runtime-types/)의 말로 — `toList()` 의 결과는 「창문(타입)만 있는 방」이고, `buildList` 의 결과는 「방 쪽이 거부하는 방」이다. 둘 다 반환 타입은 `List` 다.
- ★ 이 차이는 **stdlib 구현**이다 — 두 함수 모두 계약은 「`List` 를 돌려준다」까지다.

### 9. `toList()` 는 이미 읽기 전용이어도 **매번 새 객체**를 만든다(`=== false`) · Java `List.copyOf` 는 **이미 불변이면 복사하지 않는다** — `toList()` 는 「읽기 전용인가」를 **가리지 않는다**

**왜 그런가**

- ★★ `toList()` 의 결과가 원소 둘 이상이면 `ArrayList` 라, 다시 `toList()` 해도 「이미 불변」으로 가릴 표시가 **없다** — 소스는 크기만 보고 `toMutableList()` 로 간다.
- ★ Java 는 `ImmutableCollections` 라는 **불변 클래스**가 있어 그것을 알아본다([Java 40번](../../../java/syntax/40-list-set-and-immutable-factories/)의 「`copyOf` 는 이미 불변이면 복사하지 않는다」). 예외는 **빈 리스트**뿐이다(5번의 `3`).

### 10. **주장할 수 없다** — 3번이 보인 것은 「결과를 만들 때 **추가 복사가 없다**」는 구조 사실뿐이다 · 빠르다고 하려면 **시간과 할당을 따로** 재야 한다

**왜 그런가**

- ★★ `ListBuilder` 가 짓는 동안 저장소를 어떻게 키우는지, 잠글 때 무엇을 하는지는 이 문서가 **재지 않았다.** `mutableListOf` + `toList()` 쪽의 복사 한 번이 실제로 얼마인지도 **재지 않았다.**
- ★ 「복사 한 번이 없다」에서 「빠르다」로 가려면 JMH 같은 도구로 **원소 수를 바꿔 가며** 재야 한다 — 그 전에는 **구조 사실**로만 적는다.

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
| **없다** — 해시코드·`identityHashCode` 를 찍지 않았다(같은 객체는 `===`) | 격자 15행 · 복사 수 · 실행 출력 · 클래스 이름 |
| | stdlib 소스 발췌(줄 번호째) |
| | 진단의 **문구·`파일:줄:칸`·캐럿** · 모든 **종료 코드** |

> 근거 — 캡처 스크립트를 처음부터 다시 돌려 **블록 전체를 바이트 단위로 대조**했다.
>
> 실측 — `capture.sh blocks` 와 `capture.sh blocks-recheck` 를 처음부터 따로 돌려 `normalize-shaky.py` 로 대조했다 —\
> **블록 80개 · 동일 80 · 흔들린 칸 0 · ★고칠 것 0**(38\~41 네 주제를 한 캡처로 받았다). `diff -rq` 도 차이 0 이다.\
> ★ **정규화 규칙은 하나도 안 썼다** — 기본 넷(주소·PID·스레드 id·시간)에 걸리는 칸이 애초에 없었다.

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `make41.kt` · `grid41.py` | ★★★ 복사 격자 — 15꼴 × `===`·원본 변경 | `kotlinc` → 스크립트가 `java` |
| `tolist41.kt` | ★★ `toList()` 원소 수별 클래스 · 캐스트한 `add` | `kotlinc` → `java` |
| `Collections.kt` · `CollectionsJVM.kt` · `_Collections.kt`(stdlib 소스 jar) | `emptyList`·`listOf`·`toList`·`buildList` 선언 | `unzip` → `grep`·`sed -n` |
| `build41.kt` | ★★ `buildList` — 같은 객체 · 나오면 잠김 | `kotlinc` → `java` |
| `leak41.kt` | 빌더 추론 에러 | `kotlinc`(실패가 결과) |
| `empty41.kt` | `emptyList()` 싱글턴 | `kotlinc` → `java` |
| `form41.kt` | 형태 한 벌(뷰 대 사본) | `kotlinc` → `java` |

**구현 의존 항목** — `toList()` 의 세 갈래와 결과 클래스 · `listOf(vararg)` 의 `asList()` · `ListBuilder` 가 결과이자 잠기는 것 · `EmptyList` 싱글턴 · 빌더 추론 에러 문구 — 이 stdlib·컴파일러 판의 산출물이다.\
반면 **「반환 타입이 가변성을 정한다」「`toList()`·`toMutableList()` 는 원본과 끊긴 새 리스트」** 는 **API 의 뜻**이다.

**★ 던져 봤더니 예상과 달랐던 것 — 세 건**

1. ★★★ **`toList()` 의 사본이 캐스트로 고쳐졌다**(원소 둘 이상) — 「읽기 전용 사본」이 **객체까지 잠긴 것**은 아니었다(2번·7번).
2. ★★ **`buildList` 가 나올 때 복사하지 않았다** — `inside === built`. 「안에서 짓고 사본을 준다」가 아니라 「**같은 것을 잠근다**」였다(3번).
3. ★ **`buildList` 안의 `this` 를 밖에 담으려 하자 타입 추론이 깨졌다** — 누수를 **실행에서** 보려다 **컴파일에서** 먼저 막혔다. `<Int>` 를 적어야 실행까지 갔다(4번).
