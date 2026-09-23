# kotlin/syntax/10 — 람다와 고차 함수: `it`·마지막 인자 람다·클로저 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [08번 주제](../08-function-declaration-default-and-named-args/)이고,
> [09번 주제](../09-varargs-spread-local-and-infix-functions/)의 **로컬 함수**와 나란히 놓고 보면 대비가 선다.
> 이 주제는 [11번 주제](../11-inline-functions/)·[12번 주제](../12-reified-type-parameters/)·
> [13번 주제](../13-extension-functions-and-properties/)와 목록의 **14번 주제**·**36번 주제**의 뿌리다.
> Java 쪽 짝은 [`../../../java/syntax/29-lambda-expressions/`](../../../java/syntax/29-lambda-expressions/)·
> [`../../../java/syntax/31-functional-interfaces/`](../../../java/syntax/31-functional-interfaces/)다.
> 문항 11개 중 코드블록이 붙는 예측형은 6개다.
> 바이트코드를 묻는 문항은 **`kotlinc` 기본 `-jvm-target`(1.8)** 기준이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ 이 파일을 컴파일하면 클래스 파일이 몇 개 나오는가 (예측)

```kotlin
// icode.kt
fun apply1(f: (Int) -> Int, x: Int): Int = f(x)

fun useLiteral(): Int = apply1({ n -> n + 1 }, 10)

fun useCapture(base: Int): Int = apply1({ it + base }, 10)

fun makeTwice(): Int = apply1({ it + 1 }, 1) + apply1({ it + 1 }, 2)
```

- `find out -name '*.class'` 는 무엇을 찍는가?
- 람다 몸통은 그럼 **어디에** 있는가 — 이름 규칙이 무엇인가?
- 그 몸통의 시그니처에 **박싱이 들어 있는가**?
- 봉투(`Function1` 객체)는 누가 언제 만드는가 — `javap -v` 의 어느 절이 그것을 말하는가?

### 2. ★★ 이 일곱 줄은 각각 무엇을 찍는가 (예측)

```kotlin
fun makeNoCapture(): (Int) -> Int = { it + 1 }
fun makeCapture(base: Int): (Int) -> Int = { it + base }

// A: makeNoCapture() === makeNoCapture()
// B: makeCapture(1) === makeCapture(1)
```

```kotlin
fun twoSites(): Boolean {
    val p: (Int) -> Int = { n -> n + 1 }
    val q: (Int) -> Int = { n -> n + 1 }
    return p === q                       // H
}

fun inLoop(): Boolean {
    val seen = ArrayList<(Int) -> Int>()
    for (i in 1..3) seen.add({ n -> n + 1 })
    return seen[0] === seen[1] && seen[1] === seen[2]   // I
}

fun inLoopCapture(): Boolean {
    val seen = ArrayList<(Int) -> Int>()
    for (i in 1..3) seen.add({ n -> n + i })
    return seen[0] === seen[1]           // J
}
```

- `A`·`B`·`H`·`I`·`J` 는 각각 `true` 인가 `false` 인가?
- 객체 개수를 정하는 것은 **무엇인가** — 글자인가, 다른 것인가?
- `H` 와 `I` 의 답이 갈리는 이유를 `javap` 의 어느 숫자로 설명하는가?
- 위 다섯 값 중 **「언어가 약속한 것」은 몇 개인가**?

### 3. ★★ 람다와 `::` 참조 중 어느 쪽이 클래스 파일을 만드는가 (예측)

```kotlin
// refs2.kt
class Box(val size: Int)

fun square(n: Int): Int = n * n

fun apply1(f: (Int) -> Int, x: Int): Int = f(x)
fun applyBox(f: (Box) -> Int, b: Box): Int = f(b)
fun makeBox(f: (Int) -> Box, n: Int): Box = f(n)

fun viaLambda(): Int = apply1({ square(it) }, 3)
fun viaFunRef(): Int = apply1(::square, 3)
fun viaPropRef(): Int = applyBox(Box::size, Box(4))
fun viaCtorRef(): Box = makeBox(::Box, 5)
```

- `find outrefs2 -name '*.class'` 는 몇 줄을 찍는가 — 그 이름들은 무엇인가?
- 호출부에서 람다 쪽과 참조 쪽은 **각각 어떤 JVM 명령**이 되는가?
- 그 참조 클래스는 무엇을 상속하고, 생성자에 무엇을 넘기는가?
- 그 클래스 안에서 **박싱의 양끝**을 어떻게 볼 수 있는가?

### 4. ★★ `map(::square)` 를 `javap` 로 열면 (예측)

```kotlin
fun square(n: Int): Int = n * n

fun useFunRef(): Int = listOf(1, 2, 3).map(::square).sum()
```

```bash
javap -c -p outrefs/RefsKt.class \
  | awk '/public static final int useFunRef\(\);/,/^$/' \
  | grep -cE 'invokedynamic|Function1'
```

- 이 `grep -c` 는 무엇을 찍는가?
- 그 자리에 대신 무엇이 들어 있는가?
- 왜 그런가 — `map` 의 어떤 성질 때문인가?
- 그래서 「람다가 객체가 된다」를 실측하려면 **무엇으로** 재야 하는가?

### 5. ★ 람다 안에서 그냥 `return` 을 적으면 (예측)

```kotlin
// bad1.kt
fun runIt(f: (Int) -> Int): Int = f(1)

fun outer(): Int {
    runIt { return 5 }
    return 0
}
```

```kotlin
fun anonInForEach(xs: List<Int>): String {
    val hit = StringBuilder()
    xs.forEach(fun(x: Int) {
        if (x < 0) return
        hit.append(x)
    })
    return hit.toString()
}
// N: anonInForEach(listOf(1, -2, 3))
```

- 첫 블록은 컴파일되는가 — 안 되면 **에러 문구를 그대로** 대 보라.
- 왜 그런가 — 람다 몸통이 **어디에 사는지**로 설명하라.
- `N` 은 무엇을 찍는가?
- 익명 함수의 `return` 과 `return@라벨` 과 라벨 없는 `return` 은 각각 **무엇을 끝내는가**?

### 6. ★★ 같은 코드를 Java 로 옮기면 (예측)

```kotlin
fun countUp(n: Int): Int {
    var acc = 0
    val add: (Int) -> Int = { x -> acc += x; acc }
    for (i in 1..n) add(i)
    return acc
}
// AA: countUp(4)
```

```java
public static int countUp(int n) {
    int acc = 0;
    IntUnaryOperator add = x -> { acc += x; return acc; };
    for (int i = 1; i <= n; i++) add.applyAsInt(i);
    return acc;
}
```

- `AA` 는 무엇을 찍는가?
- Java 쪽은 컴파일되는가 — 안 되면 **에러 문구를 그대로** 대 보라.
- Kotlin 쪽 바이트코드에는 Java 에 없는 **무엇이 하나 더** 생기는가?
- 그 상자는 어떻게 람다에게 전달되는가?

### 7. ★★ 박싱은 정확히 어디서 나는가 (왜)

- `(Int) -> Int` 를 쓰면 `Integer.valueOf` 가 어디에 생기는가 — 람다 몸통인가, 다른 곳인가?
- 그 원인이 되는 **메서드 하나의 시그니처**를 적어 보라.
- 개봉하는 쪽은 어떤 명령 둘인가?
- Java 는 같은 문제를 어떻게 풀었고 Kotlin 은 어떻게 풀었는가 — 둘의 정본은 각각 어느 문서인가?

### 8. ★ 함수 타입은 JVM 에서 무엇인가 (경계)

- `(Int) -> String` 의 실제 타입 이름은 무엇인가?
- 파라미터가 **23개**가 되면 무엇이 달라지는가 — 22개일 때와 이름을 갈라 대 보라.
- `Int.() -> String` 과 `((Int) -> String)?` 는 `(Int) -> String` 과 **디스크립터가 같은가 다른가**?
- 그 사실이 만드는 **컴파일 에러** 하나를 대 보라.

### 9. ★ SAM 변환이 없애는 것과 안 없애는 것 (경계)

- Java 인터페이스 `interface JInt { int apply(int x); }` 에 Kotlin 람다를 넘기면 호출 명령이 무엇인가?
- 거기에 `Integer.valueOf` 가 몇 번 나오는가?
- 객체는 생기는가 안 생기는가 — 두 번 적으면 같은 객체인가?
- Kotlin 쪽에서 같은 것을 얻으려면 무엇을 쓰고, 그것은 몇 버전부터인가?

### 10. `it` 과 마지막 인자 람다의 경계 (경계)

- `it` 은 언제 생기고 언제 안 생기는가 — 파라미터가 둘일 때 `it` 을 쓰면 무엇이 나오는가?
- 괄호 밖으로 나갈 수 있는 람다는 **몇 개**이고 **어느 자리**인가?
- 람다를 중첩하고 양쪽 다 `it` 을 쓰면 무슨 일이 일어나는가?
- 인자가 람다 하나뿐이면 무엇이 더 생략되는가?

### 11. 어디부터 다른 주제인가 (연결)

- 비지역 `return` 의 정본은 어느 주제인가?
- 로컬 함수가 **객체를 안 만드는 것**의 정본은 어느 주제인가 — 이 주제와 무엇이 다른가?
- `let`/`run`/`apply`/`also` 가 전부 무엇인가, 그 정본은 어디인가?
- `invoke(Object)Object` 라는 시그니처가 왜 그 모양인지의 정본은 어느 문서인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
