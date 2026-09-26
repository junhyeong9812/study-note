# kotlin/syntax/28 — 제네릭: 선언 지점 변성 `in`/`out`·star projection·`where` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javap`·`javac` 에서 실제로 얻었다.\
> C# 블록은 **.NET SDK 10.0.401** 의 `csc` 다([C# 03번](../../../csharp/syntax/03-boxing-and-unboxing/) 머리말의 셸 함수).
> ★★ 아래 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적은 자리가 없다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 세 줄 — `push` 의 `T`(`in` 위치) · `peek` 의 `T`(`out` 위치) · `var item: T`(`invariant` 위치)

**출력**

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

**왜 그런가**

- ★★★ 위치 이름 셋 — **`in`**(파라미터) · **`out`**(반환) · **`invariant`**(`var` — 게터와 세터 둘 다).
- 캐럿은 **`T` 한 글자**를 가리킨다. 문제는 메서드가 아니라 **그 자리에 나타난 타입 파라미터**다.
- `val item: T` 였다면 게터뿐이라 **통과**한다.

### 2. ★★ 7번째 줄(`addOne`)만 막힌다 — `List<out E>` 대 `MutableList<E>`

**출력**

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

**왜 그런가**

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

- ★★★ stdlib 소스 218번째 줄 **`List<out E>`** — 공변이라 `List<Int>` 가 `List<Number>` 다.
  313번째 줄 **`MutableList<E>`** — 무공변이라 **아니다.** `add(E)` 가 `in` 위치에 `E` 를 쓰기 때문이다.
- 같은 `ints` 가 **읽기 전용 자리에는 들어가고 가변 자리에는 못 들어간다.**

### 3. ★★ 여섯 줄 — `add("x")` · `add(null)` · `arr[0] = 1` · `longest(1, 2)` 셋 — 읽기 두 줄은 통과

**출력**

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

**왜 그런가**

- ★★★ 투영은 **반대쪽 멤버를 잘라 낸다** — `MutableList<*>` 는 `add` 가, `Array<out Any>` 는 `set` 이 막힌다. 문구가 **막힌 멤버의 서명**을 보여 준다.
- ★★ `add(null)` — 원래 타입이 `MutableList<Int>` 처럼 **null 불가**였을 수 있다. 진단은 그 모르는 타입을 **`CapturedType(*)`** 이라 부른다.
- 2번째 줄(`xs[0]` 을 `Any?` 로)·8번째 줄(`arr[0]` 을 `Any` 로) **읽기는 에러가 없다.**
- `longest(1, 2)` — `Int` 는 `CharSequence` 가 아니라 `where` 경계를 못 채운다. `T` 추론 실패 + 인자 둘의 mismatch.

### 4. ★★★ `b`(`protected`)·`c`(`internal`)만 막힌다 — `private` 과 `@UnsafeVariance` 는 통과

**출력**

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

**왜 그런가**

- ★★★ **네 곳을 물었고 두 곳이 답했다.** 에러가 없는 `a`·`d` 가 이 문항의 답이다.
- 풀리는 가시성은 **`private` 하나**다. `protected`·`internal` 은 **밖에서 다른 타입 인자로** 부를 길이 있어 검사한다.

### 5. ★★ 안 된다 — 「`private/*private to this*/`」 · `reset` 은 통과

**출력**

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

**왜 그런가**

- ★★★ 변성이 걸린 `private` 멤버는 **`private to this`** 다 — **`this` 를 통해서만** 부른다. `other.set(...)` 은 같은 클래스 안이어도 막힌다.
- 막지 않으면 `Cell<Int>` 를 `Cell<Any>` 로 올려(공변이라 된다) 문자열을 넣을 수 있다 — **변성 검사를 풀어 준 대가를 인스턴스 경계로 치른 것**이다.
- `reset(x: @UnsafeVariance T)` 는 에러 줄에 **없다** — `this.set(x)` 로 부르므로 통과했다.

### 6. ★★★ Java 는 에러 3 개, Kotlin 은 통과 — Java `? extends` 3 곳 대 Kotlin `out` 1 곳

**출력**

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

```text
===== echo "Java 와일드카드: $(grep -o -E '\? (extends|super)' Pecs28Ok.java | wc -l) 곳 · Kotlin 변성 표기: $(grep -o -E '<(out|in) ' ktpecs.kt | wc -l) 곳" =====
Java 와일드카드: 3 곳 · Kotlin 변성 표기: 1 곳
(exit 0)
```

**왜 그런가**

- ★★★ Java 는 선언에 변성을 **못 적으므로** 받는 함수마다 `? extends` 를 적는다 — 함수가 늘면 표기도 는다.
- ★★ Kotlin 은 `interface KSource<out T>` **한 곳**이다. `List` 는 stdlib 이 이미 `out` 이라 **0 곳**이다.
- 출력은 두 언어가 **같다**(`3.0` · `7` · `14.0`).

### 7. 꺼내기만 하면 하위 타입을 상위로 읽어도 되고, 넣기만 하면 상위를 받는 쪽이 하위도 받는다 — 무공변이 막는 것은 **이종 삽입**

- `Source<Int>` 에서 꺼낸 `Int` 는 `Number` 로 써도 안전하다(같은 방향). `Sink<Any>` 는 `Int` 를 넣어도 받는다(뒤집힌 방향).
- `MutableList<Int>` 가 `MutableList<Number>` 라면 그 참조로 **`2.5` 를 넣을 수 있고**, 원래 참조로 꺼내면 `Int` 가 아니다 — 2번의 `addOne` 이 막힌 이유다.

### 8. **`@UnsafeVariance`** — 저장하지 않고 비교만 하니 안전하다

- 2번 블록의 223번째 줄 `contains(element: @UnsafeVariance E)` — `in` 위치의 `out E` 를 **선언한 쪽이 책임지고** 허용했다.
- 안전한 이유 — `contains` 는 받은 것을 **컬렉션에 넣지 않는다.** 안전하지 않게 되는 경우 — 같은 표시로 **받은 것을 저장하면** 5번이 막은 구멍이 그대로 열린다.

### 9. ★★ `sumAll(List<? extends Number>)` · `List<Number> makeList()` — descriptor 에는 없고 `Signature` 에만 있다

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
===== javap -s -p o28w/VarwildKt.class | sed -n '3,4p' =====
  public static final double sumAll(java.util.List<? extends java.lang.Number>);
    descriptor: (Ljava/util/List;)D
(exit 0)
===== javap -v -p o28w/VarwildKt.class | grep -m1 -E '^    Signature: .*List<\+' =====
    Signature: #7                           // (Ljava/util/List<+Ljava/lang/Number;>;)D
(exit 0)
```

- ★★ **파라미터에는 `? extends`, 반환에는 없음.** 공식 문서 — 반환에 붙이면 「Java clients will have to deal with them」.
- ★★★ descriptor `(Ljava/util/List;)D` 에는 **타입 인자도 변성도 없다.** `? extends` 는 **`Signature` 속성**(`List<+Ljava/lang/Number;>`)에 산다 — javac 가 읽는 정보다.

### 10. `sumAll` 은 되고 `noWild` 는 막힌다

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

- 에러가 **`noWild` 한 줄뿐**이다 — `sumAll(ints)` 는 `? extends` 덕에 `List<Integer>` 를 받았다.
- `@JvmSuppressWildcards` 는 번역을 끄므로 Java 에서 **무공변으로 되돌아간다.**

### 11. PECS 는 **선언 한 곳**으로 갔다 — 사용 지점은 **무공변 타입을 다룰 때만** · 에러는 **만드는 쪽**으로 옮겨 갔다

- 「생산자는 extends」가 `interface Source<out T>` 로, 「소비자는 super」가 `in T` 로 **타입에 붙었다.** 쓰는 쪽은 아무것도 안 적는다(6번).
- 사용 지점 투영(`Array<out T>`·`MutableList<in T>`)은 **무공변으로 선언된 타입을 한 함수에서 한쪽으로만 쓸 때** 여전히 필요하다 — Java 와 같은 판단이다.
- 에러 자리 — Java 는 **호출하는 줄**(6번의 `17`·`18`·`19`)에서, Kotlin 은 선언이 틀렸으면 **선언한 줄**(1번의 `3:17`)에서 막힌다.

### 12. C# 는 **클래스에 못 붙인다** — Kotlin 은 클래스에도 붙는다 · TS 17번은 메서드 이변성과 함께

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

- `ISource<out T>`·`ISink<in T>` 는 통과, `class Box<out T>` 는 **CS1960**(「Only interface and delegate type parameters can be specified as variant.」). 위반 검사(CS1961)는 Kotlin 의 「`in` 위치」와 같은 원리다.
- [TS 17번](../../../ts/syntax/17-variance-and-parameter-compatibility/)은 4.7 의 `in`/`out` 을 **메서드 문법의 bivariance·`strictFunctionTypes`** 와 함께 다룬다 — TS 는 구조적 타입이라 변성 표기가 **검사를 돕는 힌트**에 가깝다.

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

```text
===== javac -version =====
javac 21.0.5
(exit 0)
```

★ **흔들리는 칸과 안 흔들리는 칸**

| 흔들린다 | 안 흔들린다 |
|---|---|
| **없다** — 해시코드·주소를 찍지 않았다 | 컴파일 에러의 **문구·`파일:줄:칸`**(kotlinc·javac·csc) |
| | `javap` 의 제네릭 서명·descriptor · stdlib 소스의 **줄 번호**(이 판의 jar) |
| | 모든 **종료 코드** · 출력 · 스크립트가 센 표기 개수 |

> 근거 — 캡처 스크립트를 처음부터 다시 돌려 **블록 전체를 바이트 단위로 대조**했다.
>
> 실측 — `capture.sh blocks` 와 `capture.sh blocks-recheck` 를 처음부터 따로 돌려 `normalize-shaky.py` 로 대조했다 —\
> **블록 101개 · 동일 101 · 흔들린 칸 0 · ★고칠 것 0**(26\~29 네 주제를 한 캡처로 받았다). `diff -rq` 도 차이 0 이다.\
> ★ **정규화 규칙은 하나도 안 썼다** — 기본 넷(주소·PID·스레드 id·시간)에 걸리는 칸이 애초에 없었다.

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `varuse.kt` | ★★ 선언 지점 공변·반공변 · 사용 지점 투영 · `*` 읽기 · `where` | `kotlinc` → `java` |
| `varbad.kt` | ★★★ 위반 세 종류(`in`·`out`·`invariant` 위치) | `kotlinc`(실패가 결과) |
| `kotlin-stdlib-sources.jar` | ★★ `List<out E>`·`MutableList<E>`·`@UnsafeVariance` 의 **실제 선언** | `unzip -p` → `grep`(필터를 배너에 적었다) |
| `varinv.kt` | 같은 값이 `List` 에는 되고 `MutableList` 에는 막힘 | `kotlinc`(실패가 결과) |
| `varstar.kt` | 투영·`*`·`where` 가 막는 것 | `kotlinc`(실패가 결과) |
| `varvis.kt` · `varthis.kt` | ★★★ `private` 에서 풀리는 검사 · **private to this** | `kotlinc`(실패가 결과) |
| `Pecs28.java` · `Pecs28Ok.java` · `ktpecs.kt` | ★★★ **같은 API 의 표기 개수** — Java 3 대 Kotlin 1 | `javac`(실패 1벌) → `java` · `kotlinc` → `java` · `grep -o` 로 셈 |
| `varwild.kt` + `UseWild.java` | ★★ `? extends`/`? super` 번역 · descriptor 대 `Signature` · Java 호출 | `kotlinc` → `javap -p`·`-s`·`-v`(필터) → `javac`(실패가 결과) |
| `variance28.cs` | C# 의 클래스 변성 금지 | `csc`(실패가 결과) |
| `form28.kt` | 형태 한 벌(`Z`·`Y`·`X`) | `kotlinc` → `java` |

**구현 의존 항목** — `? extends`/`? super` 로의 **번역 규칙**(공식 문서에 적힌 상호운용 계약)과 `final` 타입 생략, `Array<in T>` 가 `Object[]` 가 되는 것, stdlib 소스의 줄 번호, 진단 문구 — 이 컴파일러·판의 산출물이다.\
반면 **「`out` 은 `in` 위치에 못 나온다」「투영은 반대쪽 멤버를 막는다」「`*` 는 쓰기 금지」「변성 걸린 `private` 은 private to this」** 는 **언어의 계약**이다.

**★ 던져 봤더니 예상과 달랐던 것 — 세 건**

1. ★★★ **`private` 이 「풀린다」가 아니라 「private to this 로 바뀐다」였다.** 변성 검사가 `private` 에서 꺼지는 것을 확인하려고 구멍을 파는 코드(`poison`)를 짰더니, **컴파일러가 가시성을 인스턴스 단위로 좁혀** 막았다(5번). 「`private` 이면 검사가 없다」로만 알면 **왜 안전한지**를 못 설명한다.
2. ★★ **`protected`·`internal` 은 안 풀렸다**(4번). 「외부에서 안 보이면 풀린다」로 짐작하면 틀린다 — **`private` 하나**다.
3. ★ **`final` 인 `Integer` 에도 `? super` 가 붙었다**(9번의 `feed`). 공식 문서의 「final 이면 와일드카드를 생략」을 **`? super` 에까지** 일반화하면 틀린다.
