# kotlin/syntax/04 — 스마트 캐스트와 그것이 깨지는 자리 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [03번 주제](../03-null-safe-types/)다. 이 주제는 **에러 메시지 자체가 답**인 문항이 많다.
> 문항 11개 중 코드블록이 붙는 예측형은 6개다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ 이 여덟 함수 중 컴파일되는 것은 무엇인가 (예측)

```kotlin
class VarProp { var s: String? = "가" }
class ValProp { val s: String? = "가" }
class CustomGetter { val s: String? get() = if (System.nanoTime() % 2 == 0L) "가" else null }
interface Iface { val s: String? }
class Delegated { val s: String? by lazy { "가" } }
var topLevel: String? = "가"

fun f1(o: VarProp)      { if (o.s != null) println(o.s.length) }
fun f2(o: ValProp)      { if (o.s != null) println(o.s.length) }
fun f3(o: CustomGetter) { if (o.s != null) println(o.s.length) }
fun f4(o: Iface)        { if (o.s != null) println(o.s.length) }
fun f6(s: String?)      { var v = s; if (v != null) println(v.length) }
fun f7()                { if (topLevel != null) println(topLevel.length) }
fun f8(o: Delegated)    { if (o.s != null) println(o.s.length) }
```

- 일곱 중 통과하는 것은 무엇인가?
- 안 되는 것들의 **에러 메시지가 몇 종류**이고 각각 무엇인가?
- `f2` 와 `f1` 을 가르는 것은 무엇인가?
- `f6` 은 지역 `var` 인데 왜 통과하는가?

### 2. ★★ 이 둘은 어떤 에러를 내는가 — 그리고 왜 메시지가 다른가 (예측)

```kotlin
fun b(s: String?) {
    var v = s
    val writer = { v = null }      // 람다가 v 를 고친다
    if (v != null) println(v.length)
    writer()
}
fun c(s: String?) {
    var v = s
    val reader = { v?.length }     // 람다가 v 를 읽기만 한다
    if (v != null) println(v.length)
}
fun d() {
    if (f() != null) println(f().length)   // fun f(): String?
}
```

- 셋 중 통과하는 것은 무엇인가?
- 안 되는 것들의 에러 메시지는 1번의 메시지들과 같은가 다른가?
- **메시지가 다른 이유**를 한 문장으로 말하면 무엇인가?
- 그 메시지는 어느 문서의 어느 문항에서 이미 본 것인가?

### 3. ★★ 모듈을 나눠 컴파일하면 무엇이 달라지는가 (예측)

```kotlin
// 모듈 A
package lib
class Box(val s: String?)
open class OpenBox { open val s: String? = "가" }

// 모듈 B  (kotlinc modB/use.kt -cp outA)
fun g1(b: Box)     { if (b.s != null) println(b.s.length) }
fun g2(b: OpenBox) { if (b.s != null) println(b.s.length) }
```

- 두 함수는 통과하는가?
- 에러 메시지는 각각 무엇인가?
- `Box.s` 는 `val` 인데 왜 거부되는가 — 같은 모듈이었다면 어땠는가?
- 이 거부가 막으려는 사고는 무엇인가?

### 4. ★ `@Volatile` 을 붙이면 풀리는가 (예측)

```kotlin
class V { @Volatile var s: String? = "가" }
fun a(o: V) { if (o.s != null) println(o.s.length) }
```

- 통과하는가?
- 에러 메시지는 무엇인가?
- `@Volatile` 이 보장하는 것과 스마트 캐스트가 요구하는 것은 각각 무엇인가?
- `synchronized` 블록으로 감싸면 되는가?

### 5. ★★ 커스텀 getter 에 `!!` 를 붙이면 무슨 일이 일어나는가 (예측)

```kotlin
class Flaky {
    private var n = 0
    val s: String? get() { n++; return if (n % 2 == 1) "가" else null }
}
val g = Flaky()
if (g.s != null) println(g.s!!.length)
```

- `g.s` 를 네 번 연달아 찍으면 무엇이 나오는가?
- 위 두 줄은 무사히 도는가?
- 스레드가 하나뿐인데도 문제가 생기는 이유는 무엇인가?
- `if` 의 `g.s` 와 본문의 `g.s` 는 몇 번의 호출인가?

### 6. ★★ `var` 프로퍼티에 `!!` 를 쓰면 실제로 얼마나 터지는가 (예측)

```kotlin
class Mutable { var s: String? = "가" }
val m = Mutable()
Thread { repeat(200000) { m.s = if (it % 2 == 0) null else "가" } }.start()
repeat(200000) { try { if (m.s != null) m.s!!.length } catch (e: Throwable) { crashed++ } }

// 그리고 같은 조건에서
repeat(200000) { val snap = m2.s; if (snap != null) snap.length }
```

- 첫 실험에서 `crashed` 는 0인가 아닌가?
- 다섯 판을 돌리면 값이 같은가?
- 둘째 실험의 결과는 무엇이고, 그 수치의 **근거는 관찰인가 논증인가**?
- 이 실험이 컴파일러 에러에 대해 말해 주는 것은 무엇인가?

### 7. 깨졌을 때 푸는 법 넷은 무엇인가 (왜)

- 로컬 `val`·엘비스 조기 반환·`?.let`·`?.` 네 가지는 각각 어떤 형태인가?
- 네 해법의 **공통점**을 한 문장으로 말하면 무엇인가?
- `?.let { }` 의 `it` 이 자동으로 풀리는 이유는 무엇인가?
- `!!` 가 해법이 아닌 이유는 5·6번에서 무엇으로 증명되는가?

### 8. K2 는 어디까지 따라오는가 (경계)

- `val isStr = x is String; if (isStr) x.length` 는 통과하는가?
- `if (x !is String || x.length == 0) return` 의 `||` 오른쪽은 좁혀지는가?
- 좁혀진 값을 람다가 **읽기만** 하면 람다 안에서도 좁혀지는가?
- `-language-version 1.9` 로 K1 과 비교할 수 있는가?

### 9. 어느 것이 언어 규칙이고 어느 것이 컴파일러 능력인가 (경계)

- "안정 값이면 좁힌다" 는 어느 쪽인가?
- "`val isStr = x is String` 을 거쳐도 좁힌다" 는 어느 쪽인가?
- 에러 메시지 문구는 어느 쪽인가?
- "이건 원래 안 되는 것" 이라고 외우면 안 되는 이유는 무엇인가?

### 10. 통과하는 다섯 자리는 어디인가 (경계)

- 같은 모듈의 `val` 프로퍼티는 통과하는가 — 조건이 있는가?
- 지역 `var` 은 언제 통과하고 언제 안 되는가?
- 인라인 람다(`run { }`) 안에서는 어떤가?
- 제네릭 프로퍼티(`class G<T>(val t: T)` 의 `g.t`)는 어떤가?

### 11. 다른 주제와 잇기 (연결)

- 이 주제의 에러 중 하나가 [03번](../03-null-safe-types/)의 어느 문항과 같은 문구인가?
- Java 의 `instanceof` 패턴은 같은 문제를 어떻게 피했는가 — 정본은 어디인가?
- `require(x is String)` 이 좁혀 주는 근거는 무엇이고 정본은 어느 주제인가?
- 플랫폼 타입([05번](../05-platform-types/))에는 왜 이 문제가 안 생기고, 그것이 왜 더 위험한가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
