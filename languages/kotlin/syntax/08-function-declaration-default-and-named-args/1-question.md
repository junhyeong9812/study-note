# kotlin/syntax/08 — 함수 선언: 기본 인자·이름 붙인 인자·단일 표현식 함수 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [01번 주제](../01-val-var-and-basic-types/)다. 이 주제는 [09번](../09-varargs-spread-local-and-infix-functions/)의 뿌리다.
> Java 쪽 짝은 [`../../../java/syntax/08-method-declaration-overloading/`](../../../java/syntax/08-method-declaration-overloading/),
> 기본값 평가 시점의 반대편은 [`../../../python/syntax/20-mutable-default-args/`](../../../python/syntax/20-mutable-default-args/)다.
> 문항 11개 중 코드블록이 붙는 예측형은 6개다.
> 바이트코드를 묻는 문항은 **`kotlinc` 기본 `-jvm-target`(1.8)** 기준이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ 이 선언이 만드는 메서드는 몇 개인가 (예측)

```kotlin
fun greet(name: String, greeting: String = "안녕", punct: String = "!"): String =
    "$greeting, $name$punct"
```

- `javap -s -p` 로 찍으면 메서드가 **몇 개** 보이는가? 이름은 무엇인가?
- 기본값을 가진 파라미터가 둘인데 오버로드가 셋 생기는가?
- 합성 메서드의 **추가 파라미터 둘**은 각각 무엇을 하는가?
- 기본값 문자열(`"안녕"`·`"!"`)은 **어느 메서드 안**에 들어 있는가?

### 2. ★★ 이 세 호출이 부르는 것과 넘기는 숫자는 (예측)

```kotlin
fun callIt(): String = greet("준")
fun callAll(): String = greet("준", "야", "?")
fun callMiddle(): String = greet("준", punct = "?")
```

- 셋 중 **합성 메서드를 안 거치는 것**은 무엇인가?
- 나머지 둘이 넘기는 정수는 각각 무엇이고, 그 숫자를 이진수로 읽으면 무슨 뜻인가?
- 생략된 자리에는 무엇이 밀려 들어가는가?
- 이 사실이 "기본 인자의 비용" 에 대해 말해 주는 것은 무엇인가?

### 3. ★ 파라미터가 32개·33개·65개이면 (경계)

파라미터가 32개·33개·65개인 함수를 만들어 **전부 기본값**을 주고 **인자 없이** 불렀다고 하자
(`f32`·`f33`·`f65`, 모든 파라미터는 `Int`).

- 세 합성 메서드의 **`int` 파라미터 개수**는 각각 몇인가?
- 무엇이 몇 개마다 하나씩 늘어나는가?
- `callBig` 이 넘기는 마스크 값들은 무엇인가 — `iconst_m1` 은 무슨 뜻인가?
- `$default` 의 전체 인자 수를 식으로 적으면 무엇인가?

### 4. ★★ 이 프로그램의 출력은 (예측)

```kotlin
var counter = 0
fun nextId(): Int { counter++; return counter }
fun useDefault(id: Int = nextId()): Int = id

fun collect(x: Int, bag: MutableList<Int> = mutableListOf()): MutableList<Int> {
    bag.add(x); return bag
}

println(useDefault()); println(useDefault()); println(useDefault())
println(useDefault(99)); println(counter)
val a = collect(1); val b = collect(2)
println("$a $b ${a === b}")
```

- 앞의 네 줄은 각각 무엇을 찍는가?
- 마지막 `counter` 는 얼마인가 — `useDefault(99)` 가 그것을 늘렸는가?
- `a` 와 `b` 는 같은 리스트인가?
- 같은 코드를 Python 으로 옮기면 어디가 달라지는가?

### 5. ★ 이 다섯 호출 중 컴파일되는 것은 (예측)

```kotlin
fun f(a: Int, b: Int, c: Int): Int = a * 100 + b * 10 + c

f(1, b = 2, c = 3)      // [A]
f(a = 1, b = 2, c = 3)  // [B]
f(1, c = 3, b = 2)      // [C]
f(b = 2, 1, c = 3)      // [D]
f(c = 3, 1, 2)          // [E]
```

- 다섯 중 통과하는 것은 무엇인가?
- 안 되는 것의 **에러 문구**는 무엇이며, 규칙을 한 문장으로 옮기면 무엇인가?
- 에러가 한 호출에 **두 종류**로 나오는 이유는 무엇인가?
- `rect(h = 9, w = 2)` 처럼 **전부 이름**이면 순서가 자유인가?

### 6. ★ 이 둘은 컴파일되는가 (예측)

```kotlin
fun fact(n: Int) = if (n <= 1) 1 else n * fact(n - 1)   // [A]
fun blockNoType(x: Int) { return x }                     // [B]
```

- 둘 다 되는가, 하나만 되는가?
- `[A]` 의 에러 문구는 무엇이고 **고치는 법이 메시지에 들어 있는가**?
- `[B]` 가 기대하는 반환 타입은 무엇이며 왜 그런가?
- 그래서 `= expr` 와 `{ }` 는 **무엇이 다른가**?

### 7. `Unit` 은 Java 의 `void` 와 같은가 (경계)

- `println(f())` 에서 `f(): Unit` 이면 무엇이 찍히는가?
- `val u: Unit = Unit` 이 되는가? `Unit === Unit` 은?
- `Unit` 과 `Nothing` 은 무엇이 다른가?
- 함수 타입 `(Int) -> Unit` 이 성립하는 이유는 무엇인가?

### 8. ★★ Java 에서 이 둘을 부르면 (예측)

```kotlin
fun greet(name: String, greeting: String = "안녕", punct: String = "!"): String = "$greeting, $name$punct"

@JvmOverloads
fun hello(name: String, greeting: String = "안녕", punct: String = "!"): String = "$greeting, $name$punct"
```

```java
KKt.hello("준");
KKt.hello("준", "야");
KKt.greet("준");       // ?
```

- `javap -s` 로 보면 두 함수가 만드는 **Java 표면**은 각각 무엇인가?
- `KKt.greet("준")` 은 되는가 — 안 되면 `javac` 의 문구는 무엇인가?
- `$default` 가 Java 에게 안 보이는 이유는 무엇인가(플래그 이름까지)?
- `@JvmOverloads` 가 만드는 오버로드는 **왼쪽부터** 떼는가 **오른쪽부터** 떼는가?

### 9. `@JvmOverloads` 로도 못 살리는 것은 (경계)

- Java 에서 `punct` 만 바꿔 부를 수 있는가?
- 그 이유를 시그니처로 설명하면 무엇인가?
- Kotlin 쪽에서는 그 호출이 어떻게 적히는가?
- 그래서 Kotlin API 를 Java 에 내놓을 때 잃는 것 하나는 무엇인가?

### 10. 기본 인자가 오버로딩을 대신할 때 생기는 새 계약은 (왜)

- Java 오버로드 사슬에서 사라지는 것 셋은 무엇인가?
- 대신 **새로 계약이 되는 것** 둘은 무엇인가?
- 파라미터 **이름을 바꾸는 리팩터링**이 왜 위험해지는가?
- 기본 인자가 **줄이지 못하는** 종류의 오버로드는 무엇인가?

### 11. 다른 주제와 잇기 (연결)

- `vararg`·spread·로컬 함수·`infix` 의 정본은 어느 주제인가?
- 생성자의 기본 인자는 어떤 마커 타입을 쓰며, 클래스 선언의 정본은 어느 주제인가?
- `@JvmStatic`·`@JvmName` 까지 포함한 상호운용 애너테이션 전체의 정본은 어느 주제인가?
- `data class` 의 어느 멤버가 기본 인자의 대표 사례인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
