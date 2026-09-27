# kotlin/syntax/03 — null 안전 타입: `?`·`?.`·`?:`·`!!` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [01번 주제](../01-val-var-and-basic-types/)다. 이 주제는 [04번](../04-smart-casts/)·[05번](../05-platform-types/)의 뿌리다.
> 문항 11개 중 코드블록이 붙는 예측형은 6개다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★ 이 네 줄은 각각 어떤 에러를 내는가 (예측)

```kotlin
val s: String? = "가"
val t: String = s        // [A]
println(s.length)        // [B]
val u: String = null     // [C]
val v: String? = "나"     // [D]
val w: String? = v       // [E]
```

- 다섯 중 통과하는 것은 무엇인가?
- 안 되는 셋의 **에러 문구가 서로 다르다** — 각각 무엇인가?
- `[B]` 의 메시지는 고치는 법까지 알려 주는가?
- `String` 을 `String?` 에 넣는 것은 왜 되는가?

### 2. ★★ `?.` 와 `?:` 는 무엇으로 컴파일되는가 (예측)

```kotlin
fun safeCall(s: String?): Int? = s?.length
fun elvis(s: String?): Int = s?.length ?: -1
```

- `javap -c` 로 찍으면 각각 어떤 JVM 명령이 보이는가?
- 두 함수의 **반환 타입 디스크립터**는 각각 무엇인가?
- `elvis` 에는 `Integer.valueOf` 가 있는가, 없다면 왜인가?
- 그래서 `s?.length ?: -1` 은 중간에 `Int?` 를 거치는가?

### 3. ★★ `!!` 는 무엇으로 컴파일되고 터지면 어떤 메시지를 내는가 (예측)

```kotlin
fun bang(s: String?): Int = s!!.length
bang(null)
```

- `javap -c` 에 보이는 호출은 무엇이고 **인자가 몇 개**인가?
- 던져지는 예외의 클래스와 `message` 는 각각 무엇인가?
- 스택 트레이스의 맨 위는 무엇을 가리키는가?
- 그래서 `!!` 대신 쓸 것은 무엇인가?

### 4. ★★ 이 함수에서 컴파일러가 심는 검사는 무엇이고 누가 걸리는가 (예측)

```kotlin
fun nonNullParam(s: String, t: String?): Int = s.length + (t?.length ?: 0)

// 그리고 Java 에서
KKt.greet(null);   // fun greet(name: String): String
```

- `javap -c` 로 보면 함수 첫 줄에 무엇이 들어 있는가?
- 파라미터 `s` 와 `t` 중 검사를 받는 것은 무엇이고 왜인가?
- Java 가 `null` 을 넘기면 어떤 예외와 **어떤 메시지**가 나오는가?
- 그 메시지가 3번의 `!!` 메시지와 다른 이유는 무엇인가?

### 5. ★★ 이 다섯 함수 중 `checkNotNullParameter` 가 안 붙는 것은 (예측)

```kotlin
public fun pub(s: String) = s.length
internal fun intl(s: String) = s.length
private fun priv(s: String) = s.length
class C {
    fun m(s: String) = s.length
    private fun p(s: String) = s.length
}
val lambda = { t: String -> t.length }
```

- 여섯 중 검사가 안 붙는 것은 무엇인가?
- 그 규칙을 한 문장으로 말하면 무엇인가?
- 람다에는 붙는가? 붙는다면 왜인가?
- 이 사실이 "이 검사의 목적" 에 대해 말해 주는 것은 무엇인가?

### 6. ★★ 어느 검사는 플래그로 끌 수 있고 어느 것은 못 끄는가 (예측)

```bash
kotlinc -Xno-param-assertions icode2.kt
kotlinc -Xno-call-assertions -Xno-param-assertions -Xno-receiver-assertions icode2.kt
```

- 첫 명령 뒤 `nonNullParam` 의 바이트코드에서 무엇이 사라지는가?
- 둘째 명령을 줘도 `bang`(즉 `!!`)의 바이트코드에 남아 있는 것은 무엇인가?
- `?.` 의 `ifnull` 은 사라지는가?
- 이 실험이 "언어 의미" 와 "컴파일러 방어" 를 어떻게 가르는가?

### 7. `?.` 사슬이 중간에 끊기면 (경계)

- `user.addr?.city?.length` 에서 `addr` 이 `null` 일 때와 `city` 가 `null` 일 때의 결과는 각각 무엇인가?
- 결과만 보고 어디서 끊겼는지 알 수 있는가?
- 사슬의 결과 타입은 무엇인가 — 끝이 non-null 이어도 그런가?
- 어디서 끊겼는지 알아야 하면 무엇을 하는가?

### 8. `?:` 오른쪽에 `return`/`throw` 가 들어가는 이유는 (왜)

- `val city = u?.addr?.city ?: return "없음"` 에서 `city` 의 타입은 무엇인가?
- `return` 과 `throw` 의 타입은 무엇인가?
- 그 타입의 어떤 성질이 이 관용구를 성립시키는가?
- 이 관용구가 `!!` 보다 나은 점 하나는 무엇인가?

### 9. `s.toString()` 과 `s?.toString()` 은 어떻게 다른가 (경계)

- `val s: String? = null` 일 때 두 식의 값은 각각 무엇인가?
- `s.isNullOrEmpty()` 가 `?.` 없이 컴파일되는 이유는 무엇인가?
- 멤버 함수는 왜 같은 일을 못 하는가?
- `s?.toString()` 에 붙는 컴파일러 경고는 무엇인가?

### 10. 어느 것이 언어 보장이고 어느 것이 컴파일러 구현인가 (경계)

- "`?.` 가 `null` 이면 `null` 을 낸다" 는 어느 쪽인가?
- "`!!` 의 NPE 에 메시지가 없다" 는 어느 쪽인가?
- "non-null 파라미터에 런타임 검사가 심긴다" 는 어느 쪽인가?
- "Kotlin 은 런타임에도 null 을 막는다" 는 문장은 조건 없이 참인가?

### 11. 다른 주제와 잇기 (연결)

- null 검사 뒤에도 컴파일러가 `?.` 를 요구하는 자리의 정본은 어느 주제인가?
- Java 경계에서 이 보장이 사라지는 것의 정본은 어느 주제인가?
- Java 쪽이 같은 문제를 어떻게 푸는지의 정본은 어느 문서인가?
- `requireNotNull` 의 정본은 어느 주제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
