# kotlin/syntax/12 — `reified` 타입 파라미터: 소거를 뚫는 방법 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> ★★ **선행은 [11번 주제](../11-inline-functions/)다** — `inline` 이 몸통을 호출 자리에 복사한다는 것을 모르면
> 이 주제는 통째로 외우기가 된다. [10번 주제](../10-lambdas-and-higher-order-functions/)도 같이 본다.
> ★ **소거 자체의 정본은 [`../../../java/syntax/19-type-erasure/`](../../../java/syntax/19-type-erasure/)** 다.
> 문항 12개 중 코드블록이 붙는 예측형은 6개다.
> 바이트코드를 묻는 문항은 **`kotlinc` 기본 `-jvm-target`(1.8)** 기준이다 — 12번만 타깃을 따로 묻는다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ 이 넷 중 컴파일되는 것은 무엇인가 (예측)

```kotlin
fun <reified T> a(x: Any): Boolean = x is T                 // [A]
fun <T> b(x: Any): Boolean = x is T                         // [B]
class Box<reified T>(val x: T)                              // [C]
inline fun <reified T> d(x: Any): Boolean = x is T          // [D]
```

- 넷 중 통과하는 것은 무엇인가?
- 안 되는 것들의 **에러 문구가 서로 같은가 다른가** — `[A]` 와 `[C]` 는?
- `[B]` 의 에러는 `[A]` 와 **무엇을 다르게 말하는가**?
- 이 두 문구를 붙여 읽으면 `reified` 의 정의가 나온다 — 어떻게 나오는가?

### 2. ★★ 같은 함수에 타입 인자가 붙은 타입을 넘기면 (예측)

```kotlin
inline fun <reified T> isA(x: Any): Boolean = x is T

fun main() {
    println("A : ${isA<String>("hi")}")
    println("B : ${isA<String>(1)}")
    println("C : ${isA<List<String>>(listOf(1))}")
}
```

- 세 줄은 각각 무엇을 찍는가?
- `C` 에서 컴파일러가 **경고를 내는가**?
- `javap` 로 보면 `C` 의 호출 자리에는 **무엇이 박혀 있는가**?
- 그래서 "`reified` 를 쓰면 제네릭이 런타임에 살아난다" 는 문장의 **정확한 범위**는 어디까지인가?

### 3. ★★ 같은 `T` 를 세 가지로 물으면 (예측)

```kotlin
import kotlin.reflect.typeOf

inline fun <reified T> nameOf(): String = T::class.java.name
inline fun <reified T> simpleOf(): String = T::class.simpleName ?: "?"
inline fun <reified T> typeText(): String = typeOf<T>().toString()

fun main() {
    println("D : ${nameOf<Int>()}")
    println("F : ${simpleOf<Int>()}")
    println("G : ${typeText<List<String>>()}")
}
```

- 세 줄은 각각 무엇을 찍는가?
- `D` 와 `F` 가 갈리는 이유는 무엇인가?
- `G` 를 **두 번 돌렸는데 출력이 달랐다면** 무엇을 바꾼 것인가?
- `T::class.java` 로는 절대 구분할 수 없는데 `typeOf<T>()` 로는 구분되는 두 호출을 하나 대 보라.

### 4. ★★ Java 쪽에서 이 함수를 부르면 (예측)

```kotlin
// api.kt
inline fun <reified T> isA(x: Any): Boolean = x is T
inline fun plain(x: Int, f: (Int) -> Int): Int = f(x)
fun normal(x: Int): Int = x + 1
```

```java
// UseReified.java
System.out.println(ApiKt.normal(10));
System.out.println(ApiKt.isA("hi"));
```

- `javac` 는 무엇을 말하는가 — 그 문구를 그대로 대 보라.
- `javap -v` 로 보면 세 메서드의 **플래그 중 하나만 다르다**. 무엇이 다른가?
- `getDeclaredMethod` 로 **찾을 수는 있는가**? 찾았다면 `invoke` 하면 어떻게 되는가?
- 그래서 Java 와 나눠 쓸 API 는 어떤 모양으로 내야 하는가?

### 5. ★ 타입을 아는데 인스턴스를 만들면 (예측)

```kotlin
inline fun <reified T> make(): T = T()
```

```kotlin
inline fun <reified T : Any> mk(): T = T::class.java.getDeclaredConstructor().newInstance()

class NoArg
class NeedsArg(val n: Int)
// mk<NoArg>()  ·  mk<NeedsArg>()
```

- 첫 줄은 컴파일되는가 — 안 되면 **에러 문구가 무엇을 이유로 대는가**?
- 그 이유는 "소거 때문" 인가, 다른 것인가?
- 둘째 블록은 컴파일되는가? `mk<NoArg>()` 와 `mk<NeedsArg>()` 는 각각 어떻게 되는가?
- 검사를 컴파일 타임에 되돌리려면 시그니처를 어떻게 바꾸는가?

### 6. ★★ 같은 캐스트를 `reified` 있이·없이 하면 (예측)

```kotlin
inline fun <reified T> castR(x: Any): T = x as T

@Suppress("UNCHECKED_CAST")
fun <T> castE(x: Any): T = x as T

fun main() {
    val a: Any = castE<String>(1)
    println("Q : $a (${a::class.java.name})")
    val b = runCatching { castR<String>(1) }
    println("R : ${b.exceptionOrNull()?.let { it::class.java.name }}")
}
```

- 두 줄은 각각 무엇을 찍는가?
- `castE` 쪽에서 **아무 일도 안 일어난다면** 그 검사는 어디로 밀린 것인가?
- 결과를 `val a: String` 으로 받으면 무엇이 달라지는가?
- 이 대비가 `reified` 의 실무 값어치를 한 줄로 말하면 무엇인가?

### 7. ★★ `inline` 이 왜 `reified` 의 전제인가 (왜)

- 인라인이 하는 일을 한 문장으로 말하면 무엇이고, 그 문장의 **어느 낱말**이 `reified` 를 가능하게 하는가?
- `isA<String>(x)` 의 호출 자리에는 `invokestatic isA` 가 남는가, 남지 않는가?
- 「런타임에 타입 정보가 생긴다」와 「컴파일 타임에 타입이 박힌다」 중 어느 쪽이 맞는가?
- [11번 주제](../11-inline-functions/)가 댄 `inline` 의 용도 둘에 이 주제가 **세 번째**로 무엇을 더하는가?

### 8. ★ 인라인됐는데 선언 쪽 본체에 남아 있는 것 (왜)

- `reified` 인라인 함수의 본체는 클래스 파일에 **남는가**?
- 그 본체 안에서 `x is T` 자리에는 무엇이 들어 있는가 — 함수 이름 하나를 대 보라.
- 그 다음 줄은 어떤 명령이고, 그것을 그대로 실행하면 왜 위험한가?
- Kotlin 이 그 위험을 막으려고 세운 **방어선 두 개**는 각각 무엇인가?

### 9. `reified` 가 전염되는가 (경계)

```kotlin
inline fun <reified T> outer(x: Any): Boolean = inner<T>(x)

fun <T> inner(x: Any): Boolean = x is T
```

- 이 코드는 컴파일되는가? 에러가 난다면 **어느 줄을 가리키는가**?
- 그 사실이 뜻하는 것을 한 문장으로 말하면 무엇인가?
- `reified` 인라인 함수를 **재귀**로 쓰면 무엇이 나오는가?
- `noinline`·`crossinline` 은 `reified` 와 어떤 관계인가?

### 10. 람다를 하나도 안 받는 인라인 함수의 경고 (경계)

- [11번 주제](../11-inline-functions/)에서 람다를 안 받는 `inline` 함수는 무엇을 받았는가?
- `inline fun <reified T> isA(x: Any)` 는 람다를 안 받는데 그 경고가 나는가?
- 그렇다면 컴파일러가 `inline` 을 정당하다고 보는 기준은 **몇 가지**인가?
- `inline fun <T> plainGeneric(x: T): T = x` 는 어떻게 되는가?

### 11. 소거된 `T` 로 배열을 만들면 (경계)

- `fun <T> pack(xs: List<T>): Array<T> = Array(xs.size) { xs[it] }` 는 통과하는가?
- 에러가 난다면 그 문구는 **어떤 낱말**을 쓰는가 — 그 낱말이 알려 주는 사실은 무엇인가?
- `inline fun <reified T> pack(vararg xs: T): Array<T> = arrayOf(*xs)` 로 만든 배열의 런타임 클래스는 무엇인가?
- 그것이 `Array<Any?>` 가 아니어야 하는 이유는 무엇인가?

### 12. 이 주제가 기대는 환경과 다른 주제와의 이음새 (연결)

- `typeOf<T>()` 의 `toString()` 출력이 **환경에 따라 달라진다** — 무엇을 클래스패스에 넣고 빼면 달라지는가?
- 이 주제의 바이트코드 결론은 `-jvm-target` 을 21 로 올리면 달라지는가 — 확인한 방법은 무엇인가?
- `List<Int>.describe()` 와 `List<String>.describe()` 를 같이 선언하면 나는 에러는 무엇이고, 그 정본은 어느 주제인가?
- "무엇이 지워지는가" 의 정본은 어느 문서인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
