# kotlin/syntax/28 — 제네릭: 선언 지점 변성 `in`/`out`·star projection·`where` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Generics: in, out, where](https://kotlinlang.org/docs/generics.html) · [Java 에서 Kotlin 호출하기 — Variant generics](https://kotlinlang.org/docs/java-to-kotlin-interop.html#variant-generics) · kotlin-stdlib **2.4.20 소스**(`kotlin-stdlib-sources.jar` 의 `commonMain/kotlin/Collections.kt` — (3)에서 직접 뽑았다).
> **실행 검증** — 이 문서의 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javac`·`javap` 에서 실제로 얻었다.\
> `kotlinc` 9회(컴파일 실패 5벌) · `javac` 3회(실패 2벌) · `java` 4회 · `javap` 3회 · `unzip` 1회 · `csc` 1회(실패가 결과).\
> ★★ 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적지 않았다. 소스 펜스의 첫 줄 배너도 캡처가 찍었다.
> ★ C# 블록의 `csc` 는 [C# 03번](../../../csharp/syntax/03-boxing-and-unboxing/) 머리말의 셸 함수와 같다(`.NET SDK 10.0.401` · `-preferreduilang:en-US`).
> **버전** — `in`/`out`·`*`·`where`·`@UnsafeVariance` 는 전부 **1.0** 이다. 이 문서에 버전으로 갈리는 항목은 없다.
> **경계** — `reified` 와 소거는 [12번 주제](../12-reified-type-parameters/)가 정본이다(여기는 **경계만** — 변성은 런타임에 아무것도 아니라는 것까지).\
> 인터페이스 선언 자체는 [20번 주제](../20-interfaces-default-impl-and-super/), 컬렉션의 읽기 전용 뷰는 [목록의 **40번 주제**](../40-read-only-collections-and-runtime-types/)가 정본이다.
> **대비** — ★★★ Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **18번**([`18-wildcards-pecs/`](../../../java/syntax/18-wildcards-pecs/)) — [README](../README.md) 가 짝으로 지정했다. **같은 변성을 쓰는 쪽(Java)과 선언하는 쪽(Kotlin)** 이다.\
> TS 갈래 목록([`ts/syntax/README.md`](../../../ts/syntax/README.md))의 **17번**([`17-variance-and-parameter-compatibility/`](../../../ts/syntax/17-variance-and-parameter-compatibility/)) — TS 4.7 도 **`in`/`out`** 을 쓴다. C# 는 이 문서가 직접 던졌다((10)).
> 이 본문은 Claude 작성이다(원고 없음).

★ **본체는 둘째 창이다** — 「**변성 위반을 컴파일러가 말하게** 하는 창」.
변성은 **컴파일 타임에만 있는 규칙**이다. 런타임에는 타입 인자가 지워지므로((9)) 실행 출력으로는 **원리상 못 본다** — 에러 문구가 곧 교재다.

## 이 주제가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **언어 보장** | 명세·공식 문서가 약속한 것 | ★★★ **`out` 은 `in` 위치에 못 나온다** 등 변성 검사 전부 — **컴파일 에러로** 확인된다 |
| **구현(JVM 백엔드)** | kotlinc 가 JVM 으로 내리는 방식 | ★★ 선언 지점 변성이 **`? extends`·`? super`** 로 번역되는 것 · 그것이 **`Signature` 속성에만** 사는 것 |
| **이 판의 관찰** | kotlinc 2.4.20 · JDK 21.0.5 에서 이번에 본 것 | 진단 문구 · stdlib 소스의 줄 번호 |

## 이 판

```text
===== kotlinc -version =====
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
(exit 0)
```

```text
===== javac -version =====
javac 21.0.5
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | (이 주제에는 없다) | 해시코드·주소를 **하나도 안 찍었다** |
| 안 흔들린다 | ★★★ 컴파일 에러의 **문구·`파일:줄:칸`** — `javac`·`csc` 포함 | 이 주제의 답 자체다 |
| 안 흔들린다 | `javap` 의 **제네릭 서명**(`? extends`)과 descriptor | 같은 소스·같은 판이면 같다 |
| 안 흔들린다 | stdlib 소스를 뽑은 **줄 번호** | ★ **이 판(2.4.20)의 소스 jar** 에 매인다 — 판이 바뀌면 줄 번호가 움직일 수 있다 |
| 안 흔들린다 | 종료 코드 · 출력 · 스크립트가 센 **표기 개수** | 결정적이다 |

★ 근거 — 캡처 스크립트를 처음부터 두 번 돌려 **블록 전체를 바이트 단위로 대조**했다(수치는 3-answer 의 「실행 검증」).

## 한눈에 — 쉽게 말하면

**변성은 「상자에 든 것의 타입 관계가 상자의 타입 관계로 옮겨 가느냐」다.**

`Int` 는 `Number` 다. 그러면 **「`Int` 가 든 상자」는 「`Number` 가 든 상자」인가?**\
**꺼내기만 하는 상자**라면 그렇다 — `Int` 를 꺼내 `Number` 로 써도 아무 일 없다.\
**넣을 수도 있는 상자**라면 아니다 — `Number` 상자라고 믿고 `Double` 을 넣으면, 원래 `Int` 상자였던 것이 깨진다.

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| **꺼내기만** 하는 자판기 | `out T` — **생산자**(producer). `List<out E>` | (1)(3) |
| **넣기만** 하는 수거함 | `in T` — **소비자**(consumer). `Comparable<in T>` | (1) |
| 넣고 꺼내는 창고 | 무공변(invariant) `T` — `MutableList<E>` | (3) |
| 「자판기」라고 **만든 사람이 한 번** 적어 둔다 | ★★ **선언 지점 변성** — `interface Source<out T>` | (1) |
| 「이번엔 꺼내기만 할게」라고 **쓰는 사람이 매번** 적는다 | ★★ **사용 지점 변성** — `Array<out Number>` · Java `? extends` | (4)(8) |
| 뭐가 들었는지 모르는 상자 | `List<*>` — star projection | (5) |
| 조건을 여러 개 단 채용 공고 | `where T : A, T : B` | (6) |

```text
   생산자 out T — 화살표가 같은 방향                 소비자 in T — 화살표가 뒤집힌다

        Int  ──is a──▶  Number                           Int  ──is a──▶  Number
         │                │                               │                │
   Source<Int> ──is a──▶ Source<Number>             Sink<Int> ◀──is a── Sink<Number>
         │                                                                   │
         └─ next(): Int 를 Number 로 받아도 안전      Number 를 받는 수거함에 Int 를 넣어도 안전 ─┘

   무공변 T — 어느 쪽으로도 안 간다
   MutableList<Int>  ✗──▶  MutableList<Number>      (Double 을 넣으면 Int 목록이 깨진다)
   MutableList<Int>  ◀──✗  MutableList<Number>      (꺼낸 것이 Int 라는 보장이 없다)
```

**Java 는 이것을 매번 쓰는 쪽에서 적고(`? extends`), Kotlin 은 한 번 선언하는 쪽에서 적는다(`out`).** 그 차이가 (8)에서 **개수로** 드러난다.

## 이 주제가 답하려는 질문

1. `out`/`in` 을 선언하면 **무엇을 할 수 있게 되고, 무엇이 금지되나** — 컴파일러는 그 금지를 어떤 말로 하나.
2. 선언 지점과 사용 지점은 **무엇이 다른가** — Java 와일드카드를 선언 지점으로 옮기면 **무엇이 줄어드나**.
3. 변성은 **JVM 에서 무엇이 되나** — Java 가 그 Kotlin API 를 부르면 어떻게 보이나.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| **실행 출력** | 선언 지점 변성 덕에 **통과한 호출이 제대로 돈다**((1)) | 이 갈래의 기본 창 |
| ★★★ **컴파일 진단** | 변성 위반 **세 종류**(`in`·`out`·`invariant` 위치) · projection 이 막는 멤버 · `private to this` | ★ **본체 창** |
| ★★ **stdlib 소스 뽑기** | `List<out E>` 와 `MutableList<E>` 의 **실제 선언** | ★ 이 주제의 고유 창 |
| ★★ **javac 로 같은 모양 던지기** | Java 는 **사용 지점마다** `?` 가 필요하다((8)) | [Java 18번](../../../java/syntax/18-wildcards-pecs/)의 창 |
| ★ **스크립트로 표기 세기** | Java `?` 몇 곳 대 Kotlin `out` 몇 곳 — 사람이 안 센다 | ★ 이 주제의 고유 창 |
| ★★ **`javap` 의 제네릭 서명 대 descriptor** | 변성이 **`Signature` 속성에만** 남는 것((9)) | [26번 주제](../26-value-class-and-boxing/)에서 쓰던 `javap -s` |
| **부적용 — 런타임 값** | 변성은 **실행 중에 아무것도 아니다** — 타입 인자가 지워진다. 「재 봤더니 같았다」가 아니라 **「잴 것이 없다」** | [12번 주제](../12-reified-type-parameters/) |

★★ **제4의 상태 — 「잴 것이 없다」.** (9)에서 descriptor 가 **`(Ljava/util/List;)D` 로 변성과 무관**하게 나온다. JVM 이 메서드를 가르고 부르는 데 **변성은 한 글자도 안 쓰인다** — 그것 자체가 「변성은 컴파일러의 규칙이다」의 증명이다.

### (1) ★★★ `out` = 생산자, `in` = 소비자 — 선언 한 번이면 쓰는 쪽은 아무것도 안 적는다

**언제 쓰나** — `List<Number>` 를 받는 함수에 `List<Int>` 를 넘기고 싶을 때.

```kotlin
// varuse.kt
interface Source<out T> { fun next(): T }
interface Sink<in T> { fun put(x: T) }

fun sumAll(xs: List<Number>): Double = xs.sumOf { it.toDouble() }
fun take(src: Source<Number>): Number = src.next()
fun feedInt(sink: Sink<Int>) = sink.put(42)

fun copyInto(from: Array<out Number>, to: Array<in Number>) {
    for (i in from.indices) to[i] = from[i]
}

fun describe(xs: List<*>): String = "size=${xs.size} first=${xs.firstOrNull()}"

fun <T> longest(a: T, b: T): T where T : CharSequence, T : Comparable<T> =
    if (a.length != b.length) (if (a.length > b.length) a else b) else maxOf(a, b)

fun main() {
    val ints: List<Int> = listOf(1, 2, 3)
    println("A ${sumAll(ints)}")
    val intSource: Source<Int> = object : Source<Int> { override fun next() = 7 }
    println("B ${take(intSource)}")
    val anySink: Sink<Any> = object : Sink<Any> { override fun put(x: Any) = println("C put $x") }
    feedInt(anySink)
    val src: Array<Int> = arrayOf(1, 2)
    val dst: Array<Any> = arrayOf("x", "y", "z")
    copyInto(src, dst)
    println("D ${dst.toList()}")
    println("E ${describe(listOf("a", 1, null))} ${describe(emptyList<Int>())}")
    println("F ${longest("ab", "abc")} ${longest("ab", "ba")}")
}
```

```text
===== kotlinc varuse.kt -d o28u =====
(exit 0)
===== java -cp o28u:kotlin-stdlib.jar VaruseKt =====
A 6.0
B 7
C put 42
D [1, 2, z]
E size=3 first=a size=0 first=null
F abc ba
(exit 0)
```

- ★★★ `A 6.0` — `sumAll(xs: List<Number>)` 에 **`List<Int>` 가 그냥 들어갔다.** 함수 쪽에도 호출 쪽에도 `out` 을 안 적었다 — **`List` 가 `out E` 로 선언돼 있기 때문**이다((3)).
- ★★ `B 7` — 내가 만든 `Source<out T>` 도 같다. **`Source<Int>` 가 `Source<Number>` 자리에** 들어갔다(생산자 — 같은 방향).
- ★★ `C put 42` — `Sink<in T>` 는 **반대 방향**이다. `Sink<Int>` 를 받는 `feedInt` 에 **`Sink<Any>` 가** 들어갔다. `Any` 를 받는 수거함은 `Int` 도 받는다.
- `D`·`E`·`F` 는 (4)·(5)·(6)에서 읽는다.

### (2) ★★★ 변성 위반 — 컴파일러가 **어느 위치**였는지 말한다

**언제 쓰나** — `out T` 로 선언한 인터페이스에 `T` 를 받는 메서드를 더하고 싶어질 때.

```kotlin
// varbad.kt
interface Source<out T> {
    fun next(): T
    fun push(x: T)
}

interface Sink<in T> {
    fun put(x: T)
    fun peek(): T
}

class Box<out T>(var item: T)
```

```text
===== kotlinc varbad.kt -d o28b =====
varbad.kt:3:17: error: type parameter 'T' is declared as 'out' but occurs in 'in' position in type 'T (of interface Source<out T>)'.
    fun push(x: T)
                ^
varbad.kt:8:17: error: type parameter 'T' is declared as 'in' but occurs in 'out' position in type 'T (of interface Sink<in T>)'.
    fun peek(): T
                ^
varbad.kt:11:28: error: type parameter 'T' is declared as 'out' but occurs in 'invariant' position in type 'T (of class Box<out T>)'.
class Box<out T>(var item: T)
                           ^
(exit 1)
```

| 선언 | 쓴 꼴 | 위치 | 진단(전문) |
|---|---|---|---|
| `Source<out T>` | `fun push(x: T)` | 파라미터 = **`in` 위치** | 「`type parameter 'T' is declared as 'out' but occurs in 'in' position in type 'T (of interface Source<out T>)'.`」 |
| `Sink<in T>` | `fun peek(): T` | 반환 = **`out` 위치** | 「`type parameter 'T' is declared as 'in' but occurs in 'out' position in type 'T (of interface Sink<in T>)'.`」 |
| `Box<out T>` | `var item: T` | 게터+세터 = **`invariant` 위치** | 「`type parameter 'T' is declared as 'out' but occurs in 'invariant' position in type 'T (of class Box<out T>)'.`」 |

- ★★★ **컴파일러가 위치에 이름을 붙인다** — `in` · `out` · `invariant`. 파라미터는 `in`, 반환은 `out`, **`var` 는 둘 다라서 `invariant`** 다.
- ★★ 캐럿이 가리키는 곳이 **`T` 한 글자**다(`3:17`·`8:17`·`11:28`) — 메서드 전체가 아니라 **그 위치에 나타난 타입 파라미터**가 문제다.
- ★ `val item: T` 였다면 게터뿐이라 `out` 위치다 — **`val` 은 되고 `var` 는 안 된다.**

### (3) ★★ 표준 라이브러리 선언 — `List<out E>` 와 `MutableList<E>`

**언제 쓰나** — 「왜 `List` 는 되고 `MutableList` 는 안 되나」를 **소스로** 답할 때. 기억이 아니라 **이 판의 stdlib 소스 jar** 에서 뽑았다.

```text
===== unzip -p kotlin-stdlib-sources.jar commonMain/kotlin/Collections.kt | grep -n -E '^public expect interface|UnsafeVariance' =====
14:public expect interface Iterable<out T> {
26:public expect interface MutableIterable<out T> : Iterable<T> {
58:public expect interface Collection<out E> : Iterable<E> {
83:    public operator fun contains(element: @UnsafeVariance E): Boolean
93:    public fun containsAll(elements: Collection<@UnsafeVariance E>): Boolean
117:public expect interface MutableCollection<E> : Collection<E>, MutableIterable<E> {
218:public expect interface List<out E> : Collection<E> {
223:    override fun contains(element: @UnsafeVariance E): Boolean
227:    override fun containsAll(elements: Collection<@UnsafeVariance E>): Boolean
248:    public fun indexOf(element: @UnsafeVariance E): Int
258:    public fun lastIndexOf(element: @UnsafeVariance E): Int
313:public expect interface MutableList<E> : List<E>, MutableCollection<E> {
458:public expect interface Set<out E> : Collection<E> {
463:    override fun contains(element: @UnsafeVariance E): Boolean
468:    override fun containsAll(elements: Collection<@UnsafeVariance E>): Boolean
487:public expect interface MutableSet<E> : Set<E>, MutableCollection<E> {
555:public expect interface Map<K, out V> {
587:    public fun containsValue(value: @UnsafeVariance V): Boolean
672:public expect interface MutableMap<K, V> : Map<K, V> {
(exit 0)
```

```text
   읽기 전용 쪽 — out                        가변 쪽 — 무공변
   ---------------------------------------   ---------------------------------------------------
   218: interface List<out E>                313: interface MutableList<E> : List<E>, ...
   458: interface Set<out E>                 487: interface MutableSet<E>  : Set<E>, ...
   555: interface Map<K, out V>              672: interface MutableMap<K, V> : Map<K, V>
          ^ 키는 무공변 · 값만 out
   223: contains(element: @UnsafeVariance E)   <- in 위치인데 out E 를 쓴다 — 허가를 받았다
```

- ★★★ **읽기 전용 인터페이스는 `out`, 가변 인터페이스는 무공변**이다. 가변 쪽은 `add(E)` 가 있어 **`in` 위치에도 `E` 가 나오므로** `out` 을 달 수 없다.
- ★★ **`Map<K, out V>`** — 값만 `out` 이다. 키는 `get(key: K)` 로 **받는** 쪽이라 공변으로 못 만든다.
- ★★ **`contains(element: @UnsafeVariance E)`** — 파라미터(`in` 위치)인데 `out E` 를 쓴다. `contains` 는 **받은 것을 저장하지 않고 비교만** 하므로 안전하다고 **선언한 쪽이 책임지고** (2)의 검사를 끈 것이다((7)).

**그래서 `MutableList` 에서는 막힌다**

```kotlin
// varinv.kt
fun sumAll(xs: List<Number>): Double = xs.sumOf { it.toDouble() }
fun addOne(xs: MutableList<Number>) { xs.add(1) }

fun main() {
    val ints: MutableList<Int> = mutableListOf(1, 2)
    println(sumAll(ints))
    addOne(ints)
}
```

```text
===== kotlinc varinv.kt -d o28i =====
varinv.kt:7:12: error: argument type mismatch: actual type is 'MutableList<Int>', but 'MutableList<Number>' was expected.
    addOne(ints)
           ^^^^
(exit 1)
```

- ★★ **에러는 `addOne(ints)` 한 줄뿐**이다 — 6줄의 `sumAll(ints)`(`List<Number>`)는 **통과했다.** 같은 `ints` 가 `List` 자리에는 들어가고 `MutableList` 자리에는 못 들어간다.
- 들어갔다면 `addOne` 이 `Int` 목록에 **`Number` 를 넣을 수 있었다** — 무공변이 막는 것이 그것이다.

### (4) ★★ 사용 지점 변성 — `Array<out Number>` 는 Java `? extends` 와 1:1

**언제 쓰나** — **무공변으로 선언된 타입**(`Array`·`MutableList`)을 한 함수 안에서만 생산자·소비자로 쓰고 싶을 때.

(1)의 `copyInto(from: Array<out Number>, to: Array<in Number>)` 가 그것이다 —
`D [1, 2, z]` 는 **`Array<Int>` 에서 꺼내 `Array<Any>` 에 넣었다.** `Array<T>` 는 무공변인데, **이 함수의 파라미터에서만** `out`·`in` 으로 **투영(projection)** 했다.

**투영하면 반대쪽 멤버가 막힌다**

```kotlin
// varstar.kt
fun addTo(xs: MutableList<*>) {
    val a: Any? = xs[0]
    xs.add("x")
    xs.add(null)
}

fun overwrite(arr: Array<out Any>) {
    val first: Any = arr[0]
    arr[0] = 1
}

fun <T> longest(a: T, b: T): T where T : CharSequence, T : Comparable<T> = a

fun main() {
    longest(1, 2)
}
```

```text
===== kotlinc varstar.kt -d o28s =====
varstar.kt:3:12: error: receiver type 'MutableList<*>' contains star projection which prohibits the use of 'fun add(element: E): Boolean'.
    xs.add("x")
           ^^^
varstar.kt:4:12: error: null cannot be a value of a non-null type 'CapturedType(*)'.
    xs.add(null)
           ^^^^
varstar.kt:9:14: error: receiver type 'Array<out Any>' contains out projection which prohibits the use of 'fun set(index: Int, value: T): Unit'.
    arr[0] = 1
             ^
varstar.kt:15:5: error: cannot infer type for type parameter 'T'. Specify it explicitly.
    longest(1, 2)
    ^^^^^^^
varstar.kt:15:13: error: argument type mismatch: actual type is 'Int', but 'CharSequence' was expected.
    longest(1, 2)
            ^
varstar.kt:15:16: error: argument type mismatch: actual type is 'Int', but 'CharSequence' was expected.
    longest(1, 2)
               ^
(exit 1)
```

- ★★★ `arr[0] = 1`(9번째 줄) — 「`receiver type 'Array<out Any>' contains out projection which prohibits the use of 'fun set(index: Int, value: T): Unit'.`」. **`out` 으로 투영한 배열은 `set` 이 금지**된다 — 읽기(`arr[0]`, 8번째 줄)는 통과했다.
- ★★ 문구가 **「막힌 멤버의 서명」** 을 통째로 보여 준다(`fun set(index: Int, value: T): Unit`). **`T` 가 `in` 위치에 있는 멤버**가 잘려 나간 것이다.

| Kotlin 사용 지점 | Java | 읽기 | 쓰기 |
|---|---|---|---|
| `Array<out Number>` · `MutableList<out Number>` | `? extends Number` | **`Number` 로 읽힌다** | ★ **막힌다** |
| `Array<in Number>` · `MutableList<in Number>` | `? super Number` | `Any?` 로만 읽힌다 | **`Number` 를 넣는다** |
| `MutableList<*>` | `?` | `Any?` 로 읽힌다 | ★ **막힌다**(`null` 도) |

- ★ 이 셋이 [Java 18번](../../../java/syntax/18-wildcards-pecs/)의 `? extends`·`? super`·`?` 와 **뜻이 같다.** 다른 것은 **Kotlin 은 이것이 「예외적으로 쓰는 쪽」** 이라는 점이다 — 대부분의 경우는 (1)처럼 **선언 지점에서 끝난다.**

### (5) ★ star projection — `List<*>` 에서 읽을 수 있는 것, 쓸 수 없는 것

**언제 쓰나** — 원소 타입을 **모르거나 상관없을 때**(크기·출력·`null` 검사).

- ★ (1)의 `E size=3 first=a size=0 first=null` — `describe(xs: List<*>)` 는 **아무 원소 타입의 `List`** 를 받고, 꺼낸 것은 **`Any?`** 로 쓴다.
- ★★★ (4)의 블록 3·4번째 줄 — `MutableList<*>` 에 `add("x")` 는
  「`receiver type 'MutableList<*>' contains star projection which prohibits the use of 'fun add(element: E): Boolean'.`」,
  `add(null)` 은 「`null cannot be a value of a non-null type 'CapturedType(*)'.`」.
- ★★ **`null` 조차 못 넣는다** — 원래 타입이 `MutableList<Int>`(null 불가)였을 수 있기 때문이다. 진단이 그 모르는 타입을 **`CapturedType(*)`** 이라고 부른다 — Java 의 **캡처 변환**([Java 18번](../../../java/syntax/18-wildcards-pecs/) (6))과 같은 개념이다.
- ★ 읽기(`val a: Any? = xs[0]`, 2번째 줄)는 **에러가 없다.** `*` 는 「**`out Any?` 처럼 읽고 `in Nothing` 처럼 쓴다**」로 요약된다.

### (6) ★ `where` — 경계가 둘 이상일 때

**언제 쓰나** — 타입 파라미터에 **상위 타입을 둘 이상** 걸어야 할 때(`<T : A>` 는 하나만 된다).

- (1)의 `F abc ba` — `longest` 는 `T : CharSequence` 이면서 `T : Comparable<T>` 여야 한다. `String` 은 둘 다라 통과했다(`length` 로 비교하고, 같으면 `maxOf`).
- ★★ (4)의 블록 마지막 세 줄 — `longest(1, 2)` 는 `Int` 가 **`CharSequence` 가 아니라** 인자 둘 다 「`argument type mismatch: actual type is 'Int', but 'CharSequence' was expected.`」이고, 그 위에 「`cannot infer type for type parameter 'T'. Specify it explicitly.`」가 먼저 나온다. **경계를 만족하는 `T` 를 못 찾았다**는 뜻이다.
- ★ `reified` 와 경계를 **같이** 쓰는 것은 [12번 주제](../12-reified-type-parameters/)가 정본이다 — 여기는 경계까지다.

### (7) ★★ 변성 검사가 **풀리는** 두 자리 — `private` 과 `@UnsafeVariance`

**언제 쓰나** — `out T` 클래스 안에서 **내부적으로만** `T` 를 받는 도우미가 필요할 때. **유명하지 않은 규칙**이다.

```kotlin
// varvis.kt
open class P<out T>(t: T) {
    private fun a(x: T) {}
    protected fun b(x: T) {}
    internal fun c(x: T) {}
    fun d(x: @UnsafeVariance T) {}
}
```

```text
===== kotlinc varvis.kt -d o28v =====
varvis.kt:3:24: error: type parameter 'T' is declared as 'out' but occurs in 'in' position in type 'T (of class P<out T>)'.
    protected fun b(x: T) {}
                       ^
varvis.kt:4:23: error: type parameter 'T' is declared as 'out' but occurs in 'in' position in type 'T (of class P<out T>)'.
    internal fun c(x: T) {}
                      ^
(exit 1)
```

```text
   out T 클래스 안에서 T 를 받는 멤버     결과
   -----------------------------------   -------------------------------------
   private   fun a(x: T)                  통과       <- ★ 에러 없음
   protected fun b(x: T)                  in 위치 에러 (3:24)
   internal  fun c(x: T)                  in 위치 에러 (4:23)
   fun d(x: @UnsafeVariance T)            통과       <- 선언한 쪽이 책임진다
```

- ★★★ **에러가 두 줄뿐**이다. 네 멤버를 던졌는데 **`private` 과 `@UnsafeVariance` 는 답하지 않았다** — 물은 곳 4 · 답한 곳 2.
- ★★ **`protected`·`internal` 은 안 풀린다.** 풀리는 것은 **`private` 하나**다.

**왜 `private` 만 안전한가 — 「private to this」**

```kotlin
// varthis.kt
class Cell<out T>(private var item: T) {
    private fun set(x: T) { item = x }
    fun get(): T = item
    fun reset(x: @UnsafeVariance T) { set(x) }
    fun poison(other: Cell<Any>) { other.set("문자열") }
}
```

```text
===== kotlinc varthis.kt -d o28t =====
varthis.kt:5:42: error: cannot access 'fun set(x: Any): Unit': it is private/*private to this*/ in 'Cell'.
    fun poison(other: Cell<Any>) { other.set("문자열") }
                                         ^^^
(exit 1)
```

- ★★★ **답이 진단 안에 있다** — 「`cannot access 'fun set(x: Any): Unit': it is private/*private to this*/ in 'Cell'.`」.
  `out T` 클래스에서 `T` 를 받는 `private` 멤버는 **`private` 이 아니라 「`private to this`」** — **`this` 를 통해서만** 부를 수 있다.
- ★★ 그래서 `poison` 처럼 **다른 인스턴스**(`other: Cell<Any>` — 실제로는 `Cell<Int>` 였을 수 있다)의 `set` 은 **같은 클래스 안인데도 막힌다.** 이것이 막히지 않으면 `Int` 셀에 문자열이 들어간다.
- ★ `reset(x: @UnsafeVariance T)` 는 **통과했다**(에러 줄에 없다). `@UnsafeVariance` 는 **그 구멍을 알고 연다**는 표시이고, 안전은 **선언한 쪽이 책임진다** — (3)의 `contains` 가 그 예다.

### (8) ★★★ Java PECS 와 대비 — 같은 모양을 javac 로 던지면

**언제 쓰나** — 「선언 지점으로 옮기면 **무엇이 줄어드나**」를 **개수로** 답할 때. 같은 API(생산자 인터페이스 + 그것을 받는 함수 셋)를 두 언어로 짰다.

**Java — 와일드카드 없이 쓰면**

```java
// Pecs28.java
import java.util.List;

interface JSource<T> { T next(); }

public class Pecs28 {
    static double sumAll(List<Number> xs) {
        double s = 0;
        for (Number n : xs) s += n.doubleValue();
        return s;
    }
    static Number take(JSource<Number> src) { return src.next(); }
    static double takeTwice(JSource<Number> src) { return src.next().doubleValue() * 2; }

    public static void main(String[] args) {
        List<Integer> ints = List.of(1, 2);
        JSource<Integer> si = () -> 7;
        System.out.println(sumAll(ints));
        System.out.println(take(si));
        System.out.println(takeTwice(si));
    }
}
```

```text
===== javac -d o28j Pecs28.java =====
Pecs28.java:17: error: incompatible types: List<Integer> cannot be converted to List<Number>
        System.out.println(sumAll(ints));
                                  ^
Pecs28.java:18: error: incompatible types: JSource<Integer> cannot be converted to JSource<Number>
        System.out.println(take(si));
                                ^
Pecs28.java:19: error: incompatible types: JSource<Integer> cannot be converted to JSource<Number>
        System.out.println(takeTwice(si));
                                     ^
Note: Some messages have been simplified; recompile with -Xdiags:verbose to get full output
3 errors
(exit 1)
```

- ★★★ **호출 세 곳이 전부 막힌다**(`17`·`18`·`19` 줄). Java 제네릭은 **기본이 무공변**이고, 선언 쪽(`interface JSource<T>`)에서 변성을 적을 방법이 **없다.**

**Java — 받는 함수마다 `? extends` 를 적으면**

```java
// Pecs28Ok.java
import java.util.List;

interface JSource2<T> { T next(); }

public class Pecs28Ok {
    static double sumAll(List<? extends Number> xs) {
        double s = 0;
        for (Number n : xs) s += n.doubleValue();
        return s;
    }
    static Number take(JSource2<? extends Number> src) { return src.next(); }
    static double takeTwice(JSource2<? extends Number> src) { return src.next().doubleValue() * 2; }

    public static void main(String[] args) {
        List<Integer> ints = List.of(1, 2);
        JSource2<Integer> si = () -> 7;
        System.out.println(sumAll(ints));
        System.out.println(take(si));
        System.out.println(takeTwice(si));
    }
}
```

```text
===== javac -d o28j Pecs28Ok.java =====
(exit 0)
===== java -cp o28j Pecs28Ok =====
3.0
7
14.0
(exit 0)
```

**Kotlin — 인터페이스에 `out` 한 번**

```kotlin
// ktpecs.kt
interface KSource<out T> { fun next(): T }

fun sumAll(xs: List<Number>): Double = xs.sumOf { it.toDouble() }
fun take(src: KSource<Number>): Number = src.next()
fun takeTwice(src: KSource<Number>): Double = src.next().toDouble() * 2

fun main() {
    val ints: List<Int> = listOf(1, 2)
    val si: KSource<Int> = object : KSource<Int> { override fun next() = 7 }
    println(sumAll(ints))
    println(take(si))
    println(takeTwice(si))
}
```

```text
===== kotlinc ktpecs.kt -d o28k =====
(exit 0)
===== java -cp o28k:kotlin-stdlib.jar KtpecsKt =====
3.0
7
14.0
(exit 0)
```

**표기 개수 — 스크립트가 센다**

```text
===== echo "Java 와일드카드: $(grep -o -E '\? (extends|super)' Pecs28Ok.java | wc -l) 곳 · Kotlin 변성 표기: $(grep -o -E '<(out|in) ' ktpecs.kt | wc -l) 곳" =====
Java 와일드카드: 3 곳 · Kotlin 변성 표기: 1 곳
(exit 0)
```

```text
   Java  (쓰는 쪽에 적는다)                   Kotlin (선언하는 쪽에 적는다)
   ----------------------------------------   ----------------------------------------
   interface JSource2<T>                      interface KSource<out T>      <- 1 곳
   sumAll(List<? extends Number>)   <- 1       sumAll(List<Number>)
   take(JSource2<? extends Number>) <- 2       take(KSource<Number>)
   takeTwice(JSource2<? extends ..>)<- 3       takeTwice(KSource<Number>)
                                               받는 함수가 늘어도 1 곳 그대로
```

- ★★★ **같은 출력(`3.0` · `7` · `14.0`)에 Java 는 3 곳, Kotlin 은 1 곳**이다. Java 는 **받는 함수가 하나 늘 때마다** `? extends` 가 하나 는다. Kotlin 은 **인터페이스의 성질**로 한 번 적고 끝난다.
- ★★ `List` 쪽은 Kotlin 이 **0 곳**이다 — stdlib 이 이미 `List<out E>` 로 선언했으니((3)). Java 는 `List<? extends Number>` 를 **직접** 적었다.
- ★ 에러 위치도 다르다 — Java 는 **호출하는 줄**(`17`·`18`·`19`)에서 막히고, Kotlin 은 선언이 틀렸다면 **선언한 줄**에서 막힌다((2)의 `3:17`). **실수가 드러나는 자리가 쓰는 쪽에서 만드는 쪽으로** 옮겨 갔다.
- ★ Java 가 이것을 못 하는 이유 — 「`List<? extends Number>` 로 **읽기만 하는 타입**」이 Java 에는 **따로 없다.** `java.util.List` 는 `add` 를 가진 하나뿐이라 선언 지점 공변이 **불가능**하다([Java 18번](../../../java/syntax/18-wildcards-pecs/)).

### (9) ★★ JVM 에서 변성이 무엇이 되나 — `? extends` 가 생긴다, 그러나 서명의 **장식**으로만

**언제 쓰나** — Kotlin API 를 Java 에서 쓸 때, 그리고 「변성이 런타임에 뭔가를 하나」를 물을 때.

```kotlin
// varwild.kt
interface WSource<out T> { fun next(): T }
interface WSink<in T> { fun put(x: T) }

fun sumAll(xs: List<Number>): Double = xs.sumOf { it.toDouble() }
fun names(xs: List<String>): Int = xs.size
fun fill(dst: MutableList<Number>) { dst.add(1) }
fun feed(s: WSink<Int>) = s.put(1)
fun take(s: WSource<Number>): Number = s.next()
fun makeList(): List<Number> = listOf(1, 2.5)
fun copyUse(from: Array<out Number>, to: Array<in Number>) { to[0] = from[0] }
fun noWild(xs: @JvmSuppressWildcards List<Number>) = xs.size
fun yesWild(): List<@JvmWildcard Number> = listOf(1)
```

```text
===== kotlinc varwild.kt -d o28w =====
(exit 0)
===== javap -p o28w/VarwildKt.class =====
Compiled from "varwild.kt"
public final class VarwildKt {
  public static final double sumAll(java.util.List<? extends java.lang.Number>);
  public static final int names(java.util.List<java.lang.String>);
  public static final void fill(java.util.List<java.lang.Number>);
  public static final void feed(WSink<? super java.lang.Integer>);
  public static final java.lang.Number take(WSource<? extends java.lang.Number>);
  public static final java.util.List<java.lang.Number> makeList();
  public static final void copyUse(java.lang.Number[], java.lang.Object[]);
  public static final int noWild(java.util.List<java.lang.Number>);
  public static final java.util.List<? extends java.lang.Number> yesWild();
}
(exit 0)
```

```text
   Kotlin 선언                               Java 가 보는 서명
   ---------------------------------------   --------------------------------------------------
   sumAll(xs: List<Number>)                  sumAll(List<? extends Number>)   <- 파라미터 + out = extends
   names(xs: List<String>)                   names(List<String>)              <- String 은 final — 생략
   fill(dst: MutableList<Number>)            fill(List<Number>)               <- 무공변 — 없음
   feed(s: WSink<Int>)                       feed(WSink<? super Integer>)     <- 파라미터 + in = super
   makeList(): List<Number>                  List<Number> makeList()          <- ★ 반환에는 안 붙인다
   copyUse(Array<out Number>, Array<in ..>)  copyUse(Number[], Object[])      <- 배열은 Java 배열로
   noWild(@JvmSuppressWildcards List<..>)    noWild(List<Number>)             <- 끈다
   yesWild(): List<@JvmWildcard Number>      List<? extends Number> yesWild() <- 켠다
```

- ★★★ **선언 지점 변성이 파라미터 자리에서 `? extends`/`? super` 로 번역된다** — Java 호출자가 `List<Integer>` 를 넘길 수 있게 하려는 것이다.
- ★★ **반환 자리에는 안 붙인다**(`makeList`). 공식 문서 — 「When it's a return value, wildcards are not generated, because otherwise Java clients will have to deal with them」. 필요하면 **`@JvmWildcard`** 로 켠다(`yesWild`).
- ★ `names(List<String>)` — `String` 은 **`final`** 이라 생략됐다. 공식 문서 — 「When the argument type is final, there's usually no point in generating the wildcard」.
  ★ 다만 `feed(WSink<? super Integer>)` 는 `Integer` 도 `final` 인데 **`? super` 가 붙었다** — 생략 규칙은 **`? extends` 쪽에서 본** 것이다(이 판의 관찰).
- ★ `copyUse` — `Array<in Number>` 는 **`Object[]`** 가 됐다. Java 배열은 원래 공변이라 **변성을 표현할 자리가 없다** — 받을 수 있는 가장 넓은 배열로 내렸다.

**Java 에서 불러 보면**

```java
// UseWild.java
import java.util.List;

public class UseWild {
    public static void main(String[] args) {
        List<Integer> ints = List.of(1, 2);
        System.out.println(VarwildKt.sumAll(ints));
        System.out.println(VarwildKt.noWild(ints));
    }
}
```

```text
===== javac -cp o28w:kotlin-stdlib.jar -d o28w UseWild.java =====
UseWild.java:7: error: incompatible types: List<Integer> cannot be converted to List<Number>
        System.out.println(VarwildKt.noWild(ints));
                                            ^
Note: Some messages have been simplified; recompile with -Xdiags:verbose to get full output
1 error
(exit 1)
```

- ★★ **에러는 `noWild` 한 줄뿐**이다 — `sumAll(ints)`(6번째 줄)는 `List<Integer>` 로 **통과했다.** `@JvmSuppressWildcards` 로 와일드카드를 끄면 Java 쪽에서 **무공변으로 되돌아간다.**

**그리고 JVM 은 그것을 쓰지 않는다**

```text
===== javap -s -p o28w/VarwildKt.class | sed -n '3,4p' =====
  public static final double sumAll(java.util.List<? extends java.lang.Number>);
    descriptor: (Ljava/util/List;)D
(exit 0)
===== javap -v -p o28w/VarwildKt.class | grep -m1 -E '^    Signature: .*List<\+' =====
    Signature: #7                           // (Ljava/util/List<+Ljava/lang/Number;>;)D
(exit 0)
```

- ★★★ **descriptor 는 `(Ljava/util/List;)D` 다** — 타입 인자도 변성도 **없다.** JVM 이 메서드를 찾고 부르는 데 쓰는 것은 이쪽이다.
- ★★ `? extends` 는 **`Signature` 속성**(`(Ljava/util/List<+Ljava/lang/Number;>;)D`)에만 있다 — `+` 가 `? extends` 다. 이것은 **javac 가 읽는 정보**이지 실행에 쓰이는 것이 아니다.
- ★ 그래서 (0)의 「**잴 것이 없다**」 — 변성은 **컴파일러(Kotlin 과 Java 둘 다)끼리의 약속**이다. 소거는 [12번 주제](../12-reified-type-parameters/)가 정본이다.

### (10) ★ C# 도 선언 지점 — 단 **인터페이스·델리게이트만**

**언제 쓰나** — 「선언 지점 변성은 Kotlin 만의 것인가」를 물을 때.

```cs
// variance28.cs
interface ISource<out T> { T Next(); }
interface ISink<in T> { void Put(T x); }
interface IBad<out T> { void Push(T x); }
class Box<out T> { }
```

```text
===== csc -target:library variance28.cs =====
variance28.cs(4,11): error CS1960: Invalid variance modifier. Only interface and delegate type parameters can be specified as variant.
variance28.cs(3,35): error CS1961: Invalid variance: The type parameter 'T' must be contravariantly valid on 'IBad<T>.Push(T)'. 'T' is covariant.
(exit 1)
```

- ★★ C# 는 `ISource<out T>`·`ISink<in T>` 를 **받았다**(1·2번째 줄은 에러가 없다). 문법도 **같은 `out`/`in`** 이다.
- ★★ 그러나 **클래스에는 못 붙인다** — 「`Invalid variance modifier. Only interface and delegate type parameters can be specified as variant.`」(CS1960). Kotlin 은 (7)의 `open class P<out T>`·(2)의 `class Box<out T>` 처럼 **클래스에도** 붙는다.
- ★ 위반 검사는 같은 원리다 — 「`must be contravariantly valid ... 'T' is covariant.`」(CS1961)는 (2)의 「`declared as 'out' but occurs in 'in' position`」과 **같은 말**을 다르게 한 것이다.

## 문법 — 형태와 규칙

**형태** — 생산자·소비자를 선언하고, 그 둘을 잇는 제네릭 함수에 **서로 다른 타입 인자의 것**을 넘기는 최소 예제다.

```kotlin
// form28.kt
interface Producer<out T> { fun produce(): T }
interface Consumer<in T> { fun consume(x: T): String }

class Fruit(val name: String) {
    override fun toString() = name
}

fun <T> pipe(p: Producer<T>, c: Consumer<T>): String = c.consume(p.produce())

fun main() {
    val apple: Producer<Fruit> = object : Producer<Fruit> { override fun produce() = Fruit("apple") }
    val printAny: Consumer<Any> = object : Consumer<Any> { override fun consume(x: Any) = "got $x" }
    println("Z ${pipe(apple, printAny)}")
    val ps: Producer<Any> = apple
    println("Y ${ps.produce()}")
    val cs: Consumer<Fruit> = printAny
    println("X ${cs.consume(Fruit("pear"))}")
}
```

```text
===== kotlinc form28.kt -d o28f =====
(exit 0)
===== java -cp o28f:kotlin-stdlib.jar Form28Kt =====
Z got apple
Y apple
X got pear
(exit 0)
```

- `Z got apple` — `pipe(p: Producer<T>, c: Consumer<T>)` 에 `Producer<Fruit>` 와 **`Consumer<Any>`** 를 넘겼다. `Consumer<Any>` 가 `Consumer<Fruit>` 이므로 `T = Fruit` 로 맞는다.
- `Y` — `Producer<Fruit>` 을 `Producer<Any>` 에 담았다(공변). `X` — `Consumer<Any>` 를 `Consumer<Fruit>` 에 담았다(반공변).

**규칙 불릿**

- **`out T`** — `T` 를 **반환 위치에만** 쓴다. 그러면 `C<Sub>` 가 `C<Super>` 다((1)(2)).
- **`in T`** — `T` 를 **파라미터 위치에만** 쓴다. 그러면 `C<Super>` 가 `C<Sub>` 다((1)(2)).
- `var` 프로퍼티는 **`invariant` 위치**라 `out`·`in` 어느 쪽과도 못 산다((2)).
- **선언 지점**(`interface C<out T>`)은 한 번 적고 모든 사용이 따른다. **사용 지점**(`Array<out T>`)은 그 파라미터에서만 투영한다((4)).
- **`*`** — 모르는 타입. 읽기는 `Any?`, 쓰기는 금지(`null` 포함)((5)).
- **`where T : A, T : B`** — 경계가 둘 이상일 때((6)).
- `private` 멤버(= **private to this**)와 **`@UnsafeVariance`** 에서는 변성 검사가 풀린다((7)).
- JVM 에서는 **파라미터의 공변/반공변이 `? extends`/`? super`** 로 번역되고, 반환에는 안 붙는다. `@JvmSuppressWildcards`·`@JvmWildcard` 로 조절한다((9)).

## 어디서 틀리나

1. ★★★ **`MutableList<Number>` 파라미터에 `MutableList<Int>` 를 넘긴다.** 무공변이다((3)). 읽기만 하면 **`List<Number>`**, 투영이 필요하면 **`MutableList<out Number>`**.
2. ★★★ **`out T` 인터페이스에 `T` 를 받는 메서드를 더한다.** 「`declared as 'out' but occurs in 'in' position`」((2)). 받아야 하면 무공변으로 바꾸거나, **저장하지 않는다는 확신이 있을 때만** `@UnsafeVariance`.
3. ★★ **`out` 클래스에 `var` 프로퍼티를 둔다.** `invariant` 위치다((2)). `val` 이면 된다.
4. ★★ **Java 습관대로 받는 함수마다 `out` 을 적는다.** 선언이 이미 `out` 이면 **필요 없다**((8)) — Kotlin 에서 사용 지점 투영은 **무공변 타입을 다룰 때만**이다.
5. ★★ **`List<*>` 에 `null` 은 넣을 수 있다고 믿는다.** `CapturedType(*)` 은 null 불가였을 수 있다((5)).
6. ★ **`private` 이면 아무 인스턴스에서나 부를 수 있다고 믿는다.** 변성이 걸린 `private` 은 **private to this** 다((7)).
7. ★ **변성이 런타임에 뭔가를 막아 준다고 믿는다.** descriptor 에는 흔적이 없다((9)) — 막는 것은 **컴파일러**다.
8. ★ **Java 에서 부를 API 의 반환을 공변으로 기대한다.** 반환에는 와일드카드가 **안 붙는다**((9)) — `@JvmWildcard`.

## 구현 세부사항 대 언어 보장

| 항목 | 어느 쪽인가 | 근거 |
|---|---|---|
| `out`/`in` 의 **위치 검사**(`in`·`out`·`invariant` 위치) | ★★★ **언어 보장** | (2) |
| 선언 지점 변성으로 `C<Sub>` 가 `C<Super>` 가 되는 것 | **언어 보장** | (1) |
| 사용 지점 투영이 **반대쪽 멤버를 막는 것** · `*` 의 읽기/쓰기 규칙 | **언어 보장** | (4)(5) |
| `private` 멤버의 **private to this** · `@UnsafeVariance` | **언어 보장** | (7) |
| `List<out E>` · `MutableList<E>` · `Map<K, out V>` | **stdlib 의 선언**(API 계약) | (3) |
| 파라미터에 **`? extends`/`? super`** 가 붙는 것 · 반환에는 안 붙는 것 | ★★ **JVM 백엔드의 상호운용 규칙**(공식 문서에 적혀 있다) | (9) |
| `final` 타입(`String`)에서 `? extends` 를 **생략**하는 것 | **상호운용 규칙**(공식 문서) · `? super Integer` 는 남은 것은 **이 판의 관찰** | (9) |
| 변성이 **descriptor 에 없고 `Signature` 에만** 있는 것 | **JVM 의 성질**(소거) | (9) |
| C# 의 변성이 인터페이스·델리게이트 **한정**인 것 | **C# 언어 규칙** | (10) |
| 진단 **문구 그 자체** · stdlib 소스의 줄 번호 | **이 판의 산출물** | 전부 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| **꺼내기만** 하는 타입(소스·공급자·읽기 전용 뷰) | 선언에 **`out T`** | 쓰는 쪽이 아무것도 안 적는다((1)(8)) |
| **넣기만** 하는 타입(싱크·비교기·핸들러) | 선언에 **`in T`** | (1) — `Comparable<in T>` 모양 |
| 넣고 꺼내는 타입 | **무공변 `T`** | (3) — `MutableList<E>` |
| 무공변 타입을 **한 함수에서만** 한쪽으로 쓴다 | **사용 지점** `out`/`in` | (4) — `Array<out T>` |
| 원소 타입이 **상관없다**(크기·출력) | **`*`** | (5) |
| 경계가 **둘 이상** | **`where`** | (6) |
| 비교만 하고 **저장하지 않는** `in` 위치 사용 | `@UnsafeVariance` — **드물게** | (3)의 `contains`. 저장하면 구멍이다 |
| **Java 에서 부를** API | 기본 번역을 믿되 필요하면 `@JvmSuppressWildcards`/`@JvmWildcard` | (9) |

## 핵심 문장

1. **`out` = 생산자(반환에만), `in` = 소비자(파라미터에만).** 컴파일러가 **위치에 이름을 붙여**(`in`·`out`·`invariant`) 위반을 말한다.
2. **선언 지점 변성은 만드는 쪽이 한 번 적고, 쓰는 쪽은 아무것도 안 적는다** — Java 에서 3 곳이던 `? extends` 가 Kotlin 에서 1 곳이 됐다.
3. **`List<out E>` 는 공변, `MutableList<E>` 는 무공변** — stdlib 소스가 그렇게 선언한다. `add` 가 `in` 위치에 `E` 를 쓰기 때문이다.
4. **사용 지점 `Array<out T>` 는 Java `? extends T` 와 같다** — 반대쪽 멤버(`set`)가 막힌다. `*` 는 읽기만 `Any?` 로 된다.
5. **`private` 멤버에서는 변성 검사가 풀린다 — 대신 private to this 가 된다.** 다른 인스턴스로는 못 부른다.
6. JVM 에서 변성은 **파라미터의 `? extends`/`? super`** 가 되지만 **descriptor 에는 없다** — 런타임에는 **잴 것이 없다.**

## 관련 자료

- [`../../../java/syntax/18-wildcards-pecs/`](../../../java/syntax/18-wildcards-pecs/) — ★★★ **짝.** PECS·캡처 변환·배열 공변성의 정본. 여기는 **그것을 선언 지점으로 옮기면 무엇이 줄어드나**다.
- [`../../../java/syntax/17-generic-declarations/`](../../../java/syntax/17-generic-declarations/) · [`19-type-erasure/`](../../../java/syntax/19-type-erasure/) — 제네릭 선언과 소거(Java 쪽).
- [12번 주제](../12-reified-type-parameters/) — `reified`·소거. 여기는 **경계까지**다.
- [20번 주제](../20-interfaces-default-impl-and-super/) — 인터페이스 선언. 변성은 그 위에 얹는 표기다.
- [26번 주제](../26-value-class-and-boxing/) — `javap -s` 로 서명을 읽는 창. 제네릭 자리가 **박싱 자리**이기도 하다.
- [목록의 **40번 주제**](../40-read-only-collections-and-runtime-types/) — 읽기 전용 컬렉션이 **불변이 아니라 뷰**라는 것. `List<out E>` 의 뜻이 거기서 이어진다.
- [`../../../ts/syntax/17-variance-and-parameter-compatibility/`](../../../ts/syntax/17-variance-and-parameter-compatibility/) — TS 4.7 의 `in`/`out` 과 메서드 이변성(bivariance).

## 용어 풀이

> **변성(variance)** — `A` 가 `B` 의 하위 타입일 때 `C<A>` 와 `C<B>` 의 관계가 **어떻게 정해지는가.** 공변·반공변·무공변 셋이다.

> **공변(covariant) · `out`** — `C<Sub>` 가 `C<Super>` 인 것. 꺼내기만 하는 타입.\
> 예: `List<Int>` 는 `List<Number>` 다.

> **반공변(contravariant) · `in`** — `C<Super>` 가 `C<Sub>` 인 것. 넣기만 하는 타입.\
> 예: `Sink<Any>` 는 `Sink<Int>` 다.

> **무공변(invariant)** — 어느 쪽으로도 안 되는 것. 넣고 꺼내는 타입.\
> 예: `MutableList<Int>` 는 `MutableList<Number>` 가 **아니다.**

> **선언 지점 변성(declaration-site variance)** — 타입을 **선언할 때** 변성을 적는 것. `interface Source<out T>`.

> **사용 지점 변성(use-site variance) · 투영(projection)** — 타입을 **쓸 때** 변성을 적는 것. `Array<out Number>` · Java `? extends`.

> **star projection(`*`)** — 타입 인자를 **모를 때** 쓰는 투영. 읽기는 `Any?`, 쓰기는 금지.

> **`@UnsafeVariance`** — 변성 검사를 **그 자리에서 끄는** 애너테이션. 안전은 선언한 쪽이 책임진다.

> **private to this** — 변성이 걸린 `private` 멤버의 실제 가시성. **`this` 를 통해서만** 부를 수 있다.

> **`Signature` 속성** — 클래스 파일에 제네릭 정보를 남기는 자리. javac 가 읽는다. **descriptor** 와 달리 JVM 실행에는 안 쓰인다.

## 더 들어가면

- **「PECS」가 Kotlin 에서 사라지지 않은 자리** — Kotlin 에도 사용 지점 투영이 있는 이유는 **`Array` 와 `Mutable*` 이 무공변**이기 때문이다. 그런 타입을 받아 **한쪽으로만** 쓰는 함수(`copy(from, to)`)에서는 여전히 Java 와 **같은 판단**을 한다 — 다른 것은 **그런 함수가 드물어졌다**는 것이다((8)의 개수).
- **왜 반환에는 와일드카드를 안 붙이나** — Java 호출자가 `List<? extends Number>` 를 받으면 **그 변수에 아무것도 못 넣고, 자기 API 에 다시 넘기기도 불편해진다.** 파라미터에는 붙여 **받는 폭을 넓히고**, 반환에는 안 붙여 **쓰는 쪽의 타입을 깨끗하게** 둔다 — 공식 문서의 번역 규칙이 그 균형이다((9)).
- **private to this 가 막은 구멍** — (7)의 `poison` 이 통과했다면, `Cell<Int>` 를 `Cell<Any>` 로 올려(공변이라 된다) 문자열을 넣고, 원래 참조로 `Int` 를 꺼내다 **`ClassCastException`** 이 났을 것이다. 컴파일러는 `private` 을 **인스턴스 단위**로 좁혀 그 길을 막는다 — 이 문서는 그 예외를 **실제로 내지는 않았다**(컴파일이 막혀 낼 수 없다).
