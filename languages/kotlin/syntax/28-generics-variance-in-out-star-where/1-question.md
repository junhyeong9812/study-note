# kotlin/syntax/28 — 제네릭: 선언 지점 변성 `in`/`out`·star projection·`where` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [20번 주제](../20-interfaces-default-impl-and-super/)다. [12번 주제](../12-reified-type-parameters/)(소거)를 먼저 보면 9·10번이 쉽다.
> ★★★ Java 쪽 짝은 [`../../../java/syntax/18-wildcards-pecs/`](../../../java/syntax/18-wildcards-pecs/)다 — 같은 변성을 **쓰는 쪽**(Java)과 **선언하는 쪽**(Kotlin).
> 문항 12개 중 코드블록이 붙는 예측형은 6개다.
> ★ 이 주제의 본체는 **컴파일 진단**이다 — 예측형 대부분이 「무엇이 몇 줄 막히나」를 묻는다.
> 이 주제의 모든 답은 **kotlinc 2.4.20 · JDK 21.0.5** 에서 실제로 던져 받은 것이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 세 선언 중 어디서 막히나 (예측)

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

- 에러가 **몇 줄**인가? 각각 **어느 줄의 무엇**을 가리키는가?
- ★★ 진단이 위치에 붙이는 **이름 셋**은 무엇인가?

### 2. ★★ 같은 `ints` 를 두 함수에 넘기면 (예측)

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

- 6번째 줄과 7번째 줄 중 **어느 쪽이** 막히는가? 둘 다인가?
- ★ 그 차이를 stdlib 의 **어떤 선언**이 만드는가?

### 3. ★★ 투영·`*`·`where` 가 막는 것 (예측)

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

- 에러가 **몇 줄**인가? 2번째 줄과 8번째 줄(읽기)은 막히는가?
- ★★ `xs.add(null)` 은 왜 막히는가? 진단이 그 모르는 타입을 **무엇이라고** 부르는가?

### 4. ★★★ 네 멤버 중 통과하는 것 (예측)

```kotlin
// varvis.kt
open class P<out T>(t: T) {
    private fun a(x: T) {}
    protected fun b(x: T) {}
    internal fun c(x: T) {}
    fun d(x: @UnsafeVariance T) {}
}
```

- `a`·`b`·`c`·`d` 중 에러가 나는 것은 어느 것인가?

### 5. ★★ 같은 클래스 안에서 다른 인스턴스의 `private` (예측)

```kotlin
// varthis.kt
class Cell<out T>(private var item: T) {
    private fun set(x: T) { item = x }
    fun get(): T = item
    fun reset(x: @UnsafeVariance T) { set(x) }
    fun poison(other: Cell<Any>) { other.set("문자열") }
}
```

- 컴파일되는가? 안 된다면 진단 문구에 들어 있는 **주석 한 조각**은 무엇인가?
- `reset` 은 막히는가?

### 6. ★★★ 같은 API 를 두 언어로 (예측)

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

- `Pecs28.java` 는 에러가 **몇 개**인가? `ktpecs.kt` 는 컴파일되는가?
- Java 를 고치려면 `? extends` 를 **몇 곳**에 적어야 하는가? Kotlin 의 변성 표기는 **몇 곳**인가?

### 7. `out` 은 생산자, `in` 은 소비자 (왜)

- `Source<Int>` 가 `Source<Number>` 인 것은 왜 안전한가? `Sink<Any>` 가 `Sink<Int>` 인 것은?
- `MutableList<Int>` 가 `MutableList<Number>` 라면 **무엇이** 깨지는가?

### 8. `List<out E>` 인데 `contains(element: E)` 는 어떻게 있나 (경계)

- `contains` 의 파라미터는 **`in` 위치**다. stdlib 은 무엇으로 이것을 통과시켰는가?
- 그 표시가 **안전한 이유**와 **안전하지 않게 되는 경우**는?

### 9. ★★ JVM 에서 변성은 무엇이 되나 (경계)

- `fun sumAll(xs: List<Number>)` 을 `javap -p` 로 보면 서명이 어떻게 보이는가? `fun makeList(): List<Number>` 는?
- ★ descriptor 에는 변성이 있는가? 없다면 `? extends` 는 **어디에** 사는가?

### 10. Java 에서 부르면 (경계)

- Java 에서 `VarwildKt.sumAll(List<Integer>)` 는 되는가? `@JvmSuppressWildcards` 를 붙인 `noWild(List<Integer>)` 는?

### 11. 선언 지점으로 옮기면 무엇이 줄어드나 (연결)

- [Java 18번](../../../java/syntax/18-wildcards-pecs/)의 PECS 규칙은 Kotlin 에서 **어디로** 갔나? 사용 지점 투영이 여전히 필요한 경우는?
- 에러가 **드러나는 자리**는 어떻게 옮겨 갔나?

### 12. 다른 언어의 `in`/`out` (연결)

- C# 도 `out T`·`in T` 를 쓴다. **어디에는 못 붙이는가?** Kotlin 과 무엇이 다른가?
- TS 4.7 의 `in`/`out` 은 [TS 17번](../../../ts/syntax/17-variance-and-parameter-compatibility/)에서 무엇과 함께 다뤄지는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
