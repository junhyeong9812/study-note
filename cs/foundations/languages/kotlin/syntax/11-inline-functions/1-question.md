# kotlin/syntax/11 — 인라인 함수: `noinline`/`crossinline`·비지역 `return` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> ★★ **선행은 [10번 주제](../10-lambdas-and-higher-order-functions/)다** — 람다가 `Function1` 객체가 되고
> 박싱이 어디서 나는지를 모르면 이 주제는 「무엇을 없애는지」가 안 보인다.
> 이 주제는 [12번 주제](../12-reified-type-parameters/)의 **전제**이고, [목록의 **14번 주제**](../14-scope-functions/)의 뿌리다.
> 라벨과 비지역 `break`/`continue` 는 [07번 주제](../07-loops-ranges-and-labels/)가 정본이다.
> 문항 11개 중 코드블록이 붙는 예측형은 6개다.
> 바이트코드를 묻는 문항은 **`kotlinc` 기본 `-jvm-target`(1.8)** 기준이다 — 10번만 타깃을 따로 묻는다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ 이 셋 중 컴파일러가 말을 거는 것은 몇 개인가 (예측)

```kotlin
// warn2.kt
inline fun noLambda(x: Int): Int = x + 1

inline fun onlyNoinline(x: Int, noinline f: (Int) -> Int): Int = f(x)

inline fun ok(x: Int, f: (Int) -> Int): Int = f(x)
```

- 셋 중 무엇이 무엇을 받는가 — 에러인가 경고인가, `exit` 코드는?
- 그 문구를 그대로 대 보라.
- ★ 둘째 줄이 결정적이다. **함수 타입 파라미터가 있는데도** 말을 거는 이유는 무엇인가?
- 그렇다면 컴파일러가 보는 기준을 한 문장으로 적으면 무엇인가?

### 2. ★★ `inline` 한 낱말만 다른 두 파일 (예측)

```kotlin
// noinl.kt
fun twice(x: Int, f: (Int) -> Int): Int = f(f(x))
fun caller(): Int = twice(10) { it + 1 }
```

```kotlin
// inl.kt
inline fun twice(x: Int, f: (Int) -> Int): Int = f(f(x))
fun caller(): Int = twice(10) { it + 1 }
```

- 두 `caller()` 의 바이트코드에서 **사라지는 것 셋**을 대 보라.
- 두 클래스 파일에서 **메서드 목록이 어떻게 달라지는가**?
- `twice` 라는 메서드 자체는 인라인 쪽에서 **사라지는가**?
- 인라인 쪽에 `iconst_0 / istore_N` 쌍이 끼어 있다 — 무엇인가?

### 3. ★★ `forEach` 안의 두 `return` (예측)

```kotlin
// nlr.kt
fun hasNeg(xs: List<Int>): String {
    xs.forEach { if (it < 0) return "neg" }
    return "none"
}

fun hasNegLabel(xs: List<Int>): String {
    xs.forEach { if (it < 0) return@forEach }
    return "none"
}
// A: hasNeg(listOf(1, -2, 3))   B: hasNeg(listOf(1, 2, 3))   C: hasNegLabel(listOf(1, -2, 3))
```

- `A`·`B`·`C` 는 각각 무엇을 찍는가?
- `hasNeg` 의 바이트코드에 `areturn` 이 **몇 개** 있는가?
- `return@forEach` 는 어떤 명령이 되는가 — `areturn` 인가 다른 것인가?
- `hasNeg` 안에 `Function1` 이 몇 번 나오는가, 왜 그런가?

### 4. ★ `noinline` 을 하나만 붙이면 (예측)

```kotlin
// noin.kt
inline fun both(x: Int, f: (Int) -> Int, noinline g: (Int) -> Int): Int = g(f(x))

fun store(g: (Int) -> Int): (Int) -> Int = g

fun caller(): Int = both(10, { it + 1 }, { it * 2 })
```

- `caller()` 안에 `invokedynamic` 이 **몇 개** 있는가?
- 남은 합성 메서드의 **이름**은 무엇인가 — 번호가 몇 번부터 시작하는가?
- 그 번호가 알려 주는 사실은 무엇인가?
- `noinline` 은 객체만 되돌리는가, 더 되돌리는 것이 있는가?

### 5. ★★ `crossinline` 은 클래스 파일을 몇 개 만드는가 (예측)

```kotlin
// cross.kt
inline fun guard(crossinline f: (Int) -> Int): Int {
    val r = Runnable { f(1) }
    r.run()
    return f(2)
}

fun caller(): Int = guard { it + 1 }
```

- `find ocross -name '*.class'` 는 몇 줄을 찍는가 — 그 이름들은 무엇인가?
- 그 클래스 둘의 **역할이 어떻게 다른가** — 한쪽에만 있는 필드는 무엇인가?
- `return f(2)` 자리는 펼쳐지는가, 객체가 되는가?
- 그래서 `crossinline` 이 비지역 `return` 을 금지하는 이유를 한 문장으로 적으면?

### 6. ★★ `inline` 이 거부하는 네 가지 (예측)

```kotlin
inline fun keep(f: (Int) -> Int): (Int) -> Int = f                              // [A]
inline fun later(f: (Int) -> Int): Runnable = Runnable { f(1) }                 // [B]
inline fun nullableLambda(x: Int, f: ((Int) -> Int)?): Int = f?.invoke(x) ?: x  // [C]
inline fun countDown(n: Int, f: (Int) -> Unit) {                                // [D]
    if (n <= 0) return
    f(n)
    countDown(n - 1, f)
}
```

```kotlin
private fun secret(x: Int): Int = x * 2
inline fun exposed(x: Int): Int = secret(x)                 // [E]
internal inline fun internalOk(x: Int): Int = secret(x)     // [F]
```

- 여섯 중 통과하는 것은 무엇인가?
- 넷의 에러 문구 중 **고치는 법을 이름으로 말해 주는 것**은 몇 개인가?
- `[E]` 는 막히는데 `[F]` 는 막히는가 — 갈리는 기준은 무엇인가?
- `[E]` 를 통과시키는 애너테이션은 무엇이고 그때 무엇이 대신 나오는가?

### 7. ★ 대가는 얼마인가 (경계)

- 이 주제가 **실제로 잰 것**은 무엇이고 **재지 않은 것**은 무엇인가?
- 같은 몸통·다섯 호출에서 클래스 파일 바이트가 몇 배가 됐는가?
- 몸통을 열 배로 키우면 배수가 어떻게 되는가?
- `c1()` **한 메서드**만 보면 명령 줄 수가 몇에서 몇으로 가는가?

### 8. ★★ 인라인이 아니면 왜 비지역 `return` 이 불가능한가 (왜)

- 비인라인 람다의 몸통은 **어디에 사는가** — 그 이름은 무엇인가?
- 거기서 `return` 하면 무엇이 끝나는가?
- 그래서 컴파일러는 무엇을 하는가 — 그 문구를 대 보라.
- 그 문구가 **세 가지 다른 원인**에서 똑같이 나온다. 셋은 무엇이고 어떻게 구분하는가?

### 9. 공개 API 와 인라인 (경계)

- 공개 `inline fun` 이 `private` 헬퍼를 부르면 무엇이 나오는가?
- 왜 막는가 — 몸통이 어디로 가기 때문인가?
- `internal inline fun` 은 왜 안 막히는가?
- 라이브러리로 내놓은 인라인 함수의 몸통을 고치면 사용자 쪽에서 언제 반영되는가?

### 10. 이 결론이 `-jvm-target` 에 흔들리는가 (경계)

- 확인한 방법은 무엇인가?
- `major version` 은 1.8 과 21 에서 각각 몇인가?
- 결과가 같았다면 그것은 **보장인가 관찰인가**?
- 왜 이 주제는 타깃에 안 걸린다고 설명했는가 — 그 설명은 근거인가 해석인가?

### 11. 어디부터 다른 주제인가 (연결)

- `reified` 에게 `inline` 은 선택인가 전제인가 — 정본은 어느 주제인가?
- 람다가 `invokedynamic` + `Function1` 이 되는 것의 정본은 어느 주제인가?
- 인라인 람다 안에서 **바깥 루프**를 `break` 하는 것은 몇 버전부터이고 정본은 어디인가?
- `let`/`run`/`with`/`apply`/`also` 는 이 주제와 무슨 관계인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
