# kotlin/syntax/06 — `when` 식: 주체 있는/없는 형태·완전성·guard (2.2+) — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [01번 주제](../01-val-var-and-basic-types/)·[03번 주제](../03-null-safe-types/)·[04번 주제](../04-smart-casts/)다.
> 이 주제는 [07번](../07-loops-ranges-and-labels/)과 목록의 **23번 주제**·**34번 주제**의 뿌리다.
> Java 쪽 짝은 [`../../../java/syntax/21-switch-statement-and-expression/`](../../../java/syntax/21-switch-statement-and-expression/)다.
> 문항 11개 중 코드블록이 붙는 예측형은 6개다.
> 바이트코드를 묻는 문항은 **`kotlinc` 기본 `-jvm-target`(1.8)** 기준이다 — 5번만 타깃을 따로 묻는다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ 이 넷 중 컴파일이 안 되는 것은 몇 개인가 (예측)

```kotlin
fun a(x: Int) {                                  // [A] 문 · Int 주체
    when (x) { 1 -> println("one") }
}
fun b(x: Int): String = when (x) {               // [B] 식 · Int 주체
    1 -> "one"
    2 -> "two"
}
fun c(b: Boolean) {                              // [C] 문 · Boolean 주체
    when (b) { true -> println("t") }
}
enum class Color { RED, GREEN, BLUE }
fun d(c: Color) {                                // [D] 문 · enum 주체
    when (c) { Color.RED -> println("r"); Color.GREEN -> println("g") }
}
```

- 넷 중 통과하는 것은 무엇인가?
- 안 되는 것들의 **에러 문구가 서로 같은가 다른가** — 다르다면 어디가 다른가?
- 그래서 `else` 를 요구하는 기준은 「식이냐 문이냐」인가, 다른 것인가?
- `Boolean?` 이면 가지가 몇 개가 되는가?

### 2. ★★ `else` 없이 통과한 `when` 이 런타임에 터질 수 있는가 (예측)

```kotlin
// color.kt  — 먼저 이렇게 컴파일한다
enum class Color { RED, GREEN }
// lib.kt
fun name(c: Color): String = when (c) {
    Color.RED -> "빨강"
    Color.GREEN -> "초록"
}
```

그다음 **`color.kt` 만** `enum class Color { RED, GREEN, BLUE }` 로 다시 컴파일하고
`lib.class` 는 그대로 둔 채 `name(Color.valueOf("BLUE"))` 를 부른다.

- 무엇이 일어나는가 — 통과하는가, 무엇이 던져지는가?
- 그 예외의 클래스 이름과 `message` 는 각각 무엇인가?
- `javap` 로 보면 이 가능성이 **어디에 남아 있는가**?
- 그래서 "`sealed`/`enum` 을 쓰면 컴파일이 깨져서 안전하다" 는 문장의 **정확한 범위**는 무엇인가?

### 3. ★★ 이 네 주체는 각각 어떤 JVM 명령이 되는가 (예측)

```kotlin
fun onInt(x: Int) = when (x) { 1 -> "a"; 2 -> "b"; 3 -> "c"; else -> "z" }
fun onIntSparse(x: Int) = when (x) { 1 -> "a"; 100 -> "b"; 10000 -> "c"; else -> "z" }
fun onString(s: String) = when (s) { "a" -> 1; "b" -> 2; "c" -> 3; else -> 0 }
fun onLong(x: Long) = when (x) { 1L -> "a"; 2L -> "b"; else -> "z" }
```

- 넷 중 `tableswitch` 가 나오는 것과 `lookupswitch` 가 나오는 것은?
- 무엇이 그 둘을 가르는가 — 문법인가 값인가?
- `String` 주체는 **몇 단**으로 비교하는가?
- `Long` 주체에 `switch` 명령이 안 나온다면 그 이유는 무엇인가?

### 4. ★ 이 파일을 컴파일하면 무엇이 나오는가 (예측)

```kotlin
enum class Color { RED, GREEN, BLUE }
fun onEnum(c: Color): Int = when (c) {
    Color.RED -> 1
    Color.GREEN -> 2
    Color.BLUE -> 3
}
```

- 컴파일하면 **클래스 파일이 몇 개** 나오는가? 소스에 없는 이름이 있는가?
- 그 안에 무엇이 들어 있고, `ordinal()` 을 바로 `switch` 하지 않는 이유는 무엇인가?
- 그 초기화 블록이 **잡는 예외**는 무엇이고 왜 잡는가?
- 가지를 다 적었는데 `default` 자리에 무엇이 남아 있는가?

### 5. ★★ 이 두 컴파일의 바이트코드를 견주면 (예측)

```kotlin
sealed interface Shape
class Circle : Shape
class Square : Shape
class Tri : Shape
fun onSealed(s: Shape): Int = when (s) { is Circle -> 1; is Square -> 2; is Tri -> 3 }
```

```bash
kotlinc icode.kt -d out/                  # 기본 타깃
kotlinc icode.kt -jvm-target 21 -d out21/
```

- 두 결과의 **바이트코드가 같은가 다른가**?
- 다르다면 각각 무엇으로 컴파일되는가?
- 갈리기 시작하는 타깃 번호는 정확히 몇인가?
- 그때 불리는 부트스트랩 메서드의 **소유 클래스**는 무엇이고, 그것이 Java 의 무엇과 같은 것인가?

### 6. ★ 이 세 호출은 무엇을 내는가 (예측)

```kotlin
fun firstMatch(x: Int): String = when {
    x > 0 -> "양수"
    x > 100 -> "백 초과"
    else -> "그 외"
}
fun kinds(x: Any): String = when (x) {
    is String -> "문자열 길이=${x.length}"
    in 1..9 -> "한 자리 수"
    1000, 2000 -> "천 단위"
    is Int -> "그 외 Int"
    else -> "모름"
}
fun guarded(x: Any): String = when (x) {
    is Int if x > 100 -> "큰 Int"
    is Int -> "작은 Int"
    else -> "Int 아님"
}

firstMatch(500)      // [A]
kinds(1000)          // [B]
kinds(3.14)          // [C]
guarded(7)           // [D]
```

- 넷의 값은 각각 무엇인가?
- `[A]` 에 **경고가 붙는가** — 붙지 않는다면 그 사실이 무엇을 뜻하는가?
- `is String` 가지 안에서 `x.length` 가 되는 근거는 무엇이고, 그 정본은 어느 주제인가?
- `in 1..9` 와 `1000, 2000` 은 각각 무슨 뜻인가?

### 7. 중복 가지와 남는 `else` 는 무엇을 내는가 (경계)

- 같은 조건을 두 번 적으면 에러인가 경고인가 — 어느 쪽이 실행되는가?
- `Boolean` 주체에 `true`·`false`·`else` 를 다 적으면 무엇이 나오는가?
- `sealed` 주체에 `else` 를 달아 두면 하위 타입이 늘었을 때 무엇이 일어나는가?
- **"경고가 사라진 것"** 이 신호가 되는 경우는 언제인가?

### 8. `when (val v = f())` 의 호출 횟수와 `v` 의 수명은 (경계)

- 가지 셋이 전부 `v` 를 보면 `f()` 는 몇 번 불리는가?
- `v` 를 `when` 밖에서 쓰면 무엇이 나오는가?
- 이 형태를 안 쓰고 같은 일을 하려면 무엇을 적어야 하는가?
- 주체가 부수효과를 가진 함수일 때 이 형태가 막는 사고는 무엇인가?

### 9. `sealed` 주체에 `else` 를 안 쓰는 것이 관용인 이유는 (왜)

- `else` 를 적으면 **없어지는 것**은 무엇인가?
- 하위 타입을 하나 늘리면 어떤 에러가 어디서 나는가?
- 그 에러가 알려 주는 것은 "무엇이 틀렸나" 인가 "어디를 고쳐야 하나" 인가?
- 그럼에도 `else` 를 적어야 하는 상황은 무엇인가?

### 10. guard 는 어디에 못 쓰고 언제부터 쓸 수 있는가 (경계)

- 주체 **없는** `when { }` 에 guard 를 달면 무엇이 나오는가?
- guard 가 Stable 이 된 버전은 무엇이고, 그것을 **컴파일러에게 직접 물어** 확인하는 방법은 무엇인가?
- guard 가 없던 시절에는 같은 것을 어떻게 적었는가?
- guard 가 있는 가지도 완전성 계산에 들어가는가?

### 11. Java `switch` 와 다른 자리·다른 주제와 잇기 (연결)

- Kotlin `when` 에 **없는 Java `switch` 의 개념** 하나를 대면 무엇인가?
- 그 Java 쪽 정본은 어느 문서인가?
- `sealed` 계층을 **어떻게 설계하나**의 정본은 어느 주제인가?
- `when` 가지가 `throw` 일 때 타입 추론이 어떻게 되는지의 정본은 어느 주제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
