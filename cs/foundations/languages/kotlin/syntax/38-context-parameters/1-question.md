# kotlin/syntax/38 — context parameters — 2.2 실험 → 2.4.0 Stable — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [37번 주제](../37-lambdas-with-receiver-and-type-safe-builders/)(수신자 람다 — 수신자가 `Function1` 의 첫 인자)다.
> 문항 11개 중 예측형은 6개이고, 그중 코드블록이 붙는 것은 5개다.
> 바이트코드를 묻는 문항은 **`kotlinc` 기본 `-jvm-target`(1.8)** 기준이다.
> 이 주제의 모든 답은 **kotlinc 2.4.20 · Temurin JDK 21.0.5** 에서 실제로 던져 받은 것이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 새 문법을 세 가지로 컴파일하면 (예측)

```kotlin
// ctxp.kt
class Logger(val tag: String) { fun log(m: String) = println("[$tag] $m") }

context(log: Logger)
fun work(x: Int): Int { log.log("work $x"); return x * 2 }

fun main() {
    with(Logger("A")) { println(work(3)) }
}
```

- `kotlinc ctxp.kt` · `kotlinc -language-version 2.3 ctxp.kt` · `kotlinc -language-version 2.3 -Xcontext-parameters ctxp.kt` 는 각각 통과하는가? 막히면 무엇이라고 말하는가? 통과하면 돌렸을 때 무엇이 찍히는가?

### 2. ★★★ 옛 문법 (예측)

```kotlin
// ctxr.kt
class Logger(val tag: String) { fun log(m: String) = println("[$tag] $m") }

context(Logger)
fun work(x: Int): Int { log("work $x"); return x * 2 }

fun main() {
    with(Logger("A")) { println(work(3)) }
}
```

- `kotlinc ctxr.kt`(2.4 기본)는 통과하는가? `-Xcontext-receivers` 를 붙이면? 막히면 **몇 번째 줄**에서 무엇이라고 말하는가?

### 3. ★★ 어느 `Logger` 가 건네지나 (예측)

```kotlin
// ctxsig.kt
class Logger(val tag: String) { fun log(m: String) = println("[$tag] $m") }
class Tx(val id: Int)

context(lg: Logger)
fun ctx1(x: Int): Int { lg.log("ctx1 $x"); return x }

fun Logger.ext1(x: Int): Int { log("ext1 $x"); return x }

context(lg: Logger, tx: Tx)
fun String.both(n: Int): String = "$this$n tag=${lg.tag} tx=${tx.id}"

context(_: Logger)
fun anon(): String = contextOf<Logger>().tag

fun main() {
    with(Logger("A")) {
        println(ctx1(1))
        println(ext1(2))
        with(Tx(7)) { println("s".both(3)) }
        println(anon())
        with(Logger("B")) { println(ctx1(4)) }
    }
}
```

- 돌리면 무엇이 찍히는가? 특히 `with(Logger("B")) { println(ctx1(4)) }` 줄은 `A` 인가 `B` 인가?

### 4. ★★★ `javap -s` 로 본 네 함수 (예측)

- 3번 파일의 `ctx1` · `ext1` · `both` · `anon` 은 JVM 에서 **어떤 매개변수 목록**이 되는가? `ctx1` 과 `ext1` 의 디스크립터는 어떻게 다른가?

### 5. ★★★ 몸통 안과 호출 자리 (예측)

```kotlin
// ctxbad.kt
class Logger(val tag: String) { fun log(m: String) = println("[$tag] $m") }

fun Logger.r1() { log("r1"); println(tag); println(this.tag) }

context(lg: Logger)
fun c1() { log("c1") }

context(lg: Logger)
fun c2() { println(tag) }

context(lg: Logger)
fun c3() { println(this.tag) }

context(lg: Logger)
fun c4(): String = lg.tag

fun g1(): String = c4()

context(a: Logger, b: Logger)
fun g2(): String = c4()

fun g3(): Logger = contextOf<Logger>()
```

- 에러가 나는 줄은 어디이고 각각 무엇이라고 말하는가? 3번째 줄 `r1` 은?

### 6. ★ Java 에서 부르기 (예측)

```java
// JCtx.java
public class JCtx {
    public static void main(String[] args) {
        Logger j = new Logger("J");
        System.out.println(CtxsigKt.ctx1(j, 5));
        System.out.println(CtxsigKt.ext1(j, 6));
        System.out.println(CtxsigKt.both(j, new Tx(8), "s", 9));
    }
}
```

- `javac` 가 통과하는가? 돌리면 무엇이 찍히는가?

### 7. 「2.2 실험」을 이 격자로 확인할 수 있나 (왜)

- 1번 방식으로 `-language-version 2.1` 에 `-Xcontext-parameters` 를 주면 통과한다. 그렇다면 「2.2.0 에서 실험으로 들어왔다」는 이 머신에서 **무엇으로** 확인할 수 있고 무엇으로는 못 하는가?

### 8. 같은 타입의 context 가 둘일 때 (경계)

- 「같은 층에 같은 타입이 둘이면 모호성」이라는 규칙은 3번의 중첩 `with` 와 5번의 `g2` 에서 각각 어떻게 드러났는가?

### 9. 수신자와 context parameter — JVM 은 같은데 (연결)

- [37번 주제](../37-lambdas-with-receiver-and-type-safe-builders/)는 「수신자 = 첫 인자」를 보였다. 4번에서 context parameter 도 같은 자리라면, **둘을 가르는 것은 무엇**이고 그 차이는 어디서 드러나는가?

### 10. 옛 코드에 이름만 붙이면 (왜)

- `context(Logger)` 를 `context(log: Logger)` 로만 고치고 몸통의 `log("work $x")` 를 그대로 두면 무엇이 되는가 — 왜 그런가?

### 11. `contextOf<T>()` 의 정체 (경계)

- `contextOf` 는 언어가 따로 마련한 특별한 장치인가? 5번의 22번째 줄 문구 속 `context: A` 는 무엇을 가리키는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
