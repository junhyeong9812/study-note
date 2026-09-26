# kotlin/syntax/38 — context parameters — 2.2 실험 → 2.4.0 Stable — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javac`·`java`·`javap` 에서 실제로 얻었다.\
> 역어셈블은 **기본 `-jvm-target`(1.8)** 이 정본이다.
> ★★ 아래 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적은 자리가 없다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 2.4 기본은 **통과**(`[A] work 3` · `6`) · 2.3 플래그 없음은 **실패**(「`only available since language version 2.4`」) · 2.3 + `-Xcontext-parameters` 는 **통과**

**출력**

```kotlin
// ctxp.kt
class Logger(val tag: String) { fun log(m: String) = println("[$tag] $m") }

context(log: Logger)
fun work(x: Int): Int { log.log("work $x"); return x * 2 }

fun main() {
    with(Logger("A")) { println(work(3)) }
}
```

```text
===== kotlinc ctxp.kt -d o38p =====
(exit 0)
===== java -cp o38p:kotlin-stdlib.jar CtxpKt =====
[A] work 3
6
(exit 0)
===== kotlinc -Xcontext-parameters ctxp.kt -d o38p2 =====
warning: the argument '-Xcontext-parameters' is redundant for the current language version 2.4.
(exit 0)
===== kotlinc -language-version 2.3 ctxp.kt -d o38p3 =====
ctxp.kt:3:1: error: the feature "context parameters" is only available since language version 2.4
context(log: Logger)
^^^^^^^^^^^^^^^^^^^^
ctxp.kt:7:33: error: to call contextual declarations, specify the '-Xcontext-parameters' compiler option.
    with(Logger("A")) { println(work(3)) }
                                ^^^^
(exit 1)
===== kotlinc -language-version 2.3 -Xcontext-parameters ctxp.kt -d o38p4 =====
(exit 0)
```

**왜 그런가**

- ★★★ **컴파일러 스스로 경계를 2.4 라고 말한다** — 「`the feature "context parameters" is only available since language version 2.4`」. 2.4 가 Stable 이 된 판이라 플래그가 필요 없다.
- ★★ 2.3 은 **플래그로 켜진다** — 호출 자리의 에러도 「`specify the '-Xcontext-parameters' compiler option.`」로 그 길을 가리킨다.
- ★ 스크립트가 센 전체 격자는 **통과 5 / 24** 이고 통과는 전부 새 문법이다.

```text
===== python3 grid38.py =====
file	lv	flag	exit	warnings	errors
ctxp.kt	2.1	(none)	1	1	the feature "context parameters" is only available since language version 2.4 + to call contextual declarations, specify the '-Xcontext-parameters' compiler option.
ctxp.kt	2.1	-Xcontext-parameters	0	1	-
ctxp.kt	2.1	-Xcontext-receivers	1	1	experimental context receivers are superseded by context parameters.
ctxp.kt	2.2	(none)	1	0	the feature "context parameters" is only available since language version 2.4 + to call contextual declarations, specify the '-Xcontext-parameters' compiler option.
ctxp.kt	2.2	-Xcontext-parameters	0	0	-
ctxp.kt	2.2	-Xcontext-receivers	1	0	experimental context receivers are superseded by context parameters.
ctxp.kt	2.3	(none)	1	0	the feature "context parameters" is only available since language version 2.4 + to call contextual declarations, specify the '-Xcontext-parameters' compiler option.
ctxp.kt	2.3	-Xcontext-parameters	0	0	-
ctxp.kt	2.3	-Xcontext-receivers	1	0	experimental context receivers are superseded by context parameters.
ctxp.kt	2.4	(none)	0	0	-
ctxp.kt	2.4	-Xcontext-parameters	0	1	-
ctxp.kt	2.4	-Xcontext-receivers	1	0	experimental context receivers are superseded by context parameters.
ctxr.kt	2.1	(none)	1	1	experimental context receivers are superseded by context parameters. + the feature "context parameters" is only available since language version 2.4 + unresolved reference 'log'. + to call contextual declarations, specify the '-Xcontext-parameters' compiler option.
ctxr.kt	2.1	-Xcontext-parameters	1	1	context parameters must be named. Use '_' to declare an anonymous context parameter. + unresolved reference 'log'.
ctxr.kt	2.1	-Xcontext-receivers	1	1	experimental context receivers are superseded by context parameters. + experimental context receivers are superseded by context parameters. + unresolved reference 'log'.
ctxr.kt	2.2	(none)	1	0	experimental context receivers are superseded by context parameters. + the feature "context parameters" is only available since language version 2.4 + unresolved reference 'log'. + to call contextual declarations, specify the '-Xcontext-parameters' compiler option.
ctxr.kt	2.2	-Xcontext-parameters	1	0	context parameters must be named. Use '_' to declare an anonymous context parameter. + unresolved reference 'log'.
ctxr.kt	2.2	-Xcontext-receivers	1	0	experimental context receivers are superseded by context parameters. + experimental context receivers are superseded by context parameters. + unresolved reference 'log'.
ctxr.kt	2.3	(none)	1	0	experimental context receivers are superseded by context parameters. + the feature "context parameters" is only available since language version 2.4 + unresolved reference 'log'. + to call contextual declarations, specify the '-Xcontext-parameters' compiler option.
ctxr.kt	2.3	-Xcontext-parameters	1	0	context parameters must be named. Use '_' to declare an anonymous context parameter. + unresolved reference 'log'.
ctxr.kt	2.3	-Xcontext-receivers	1	0	experimental context receivers are superseded by context parameters. + experimental context receivers are superseded by context parameters. + unresolved reference 'log'.
ctxr.kt	2.4	(none)	1	0	context parameters must be named. Use '_' to declare an anonymous context parameter. + unresolved reference 'log'.
ctxr.kt	2.4	-Xcontext-parameters	1	1	context parameters must be named. Use '_' to declare an anonymous context parameter. + unresolved reference 'log'.
ctxr.kt	2.4	-Xcontext-receivers	1	0	experimental context receivers are superseded by context parameters. + context parameters must be named. Use '_' to declare an anonymous context parameter. + unresolved reference 'log'.
cells that compiled: 5 / 24
(exit 0)
```

### 2. ★★★ **둘 다 실패** — 2.4 기본은 3번째 줄 「`context parameters must be named. Use '_' to declare an anonymous context parameter.`」 + 4번째 줄 「`unresolved reference 'log'.`」 · `-Xcontext-receivers` 는 그 위에 「`experimental context receivers are superseded by context parameters.`」

**출력**

```kotlin
// ctxr.kt
class Logger(val tag: String) { fun log(m: String) = println("[$tag] $m") }

context(Logger)
fun work(x: Int): Int { log("work $x"); return x * 2 }

fun main() {
    with(Logger("A")) { println(work(3)) }
}
```

```text
===== kotlinc ctxr.kt -d o38r =====
ctxr.kt:3:9: error: context parameters must be named. Use '_' to declare an anonymous context parameter.
context(Logger)
        ^^^^^^
ctxr.kt:4:25: error: unresolved reference 'log'.
fun work(x: Int): Int { log("work $x"); return x * 2 }
                        ^^^
(exit 1)
===== kotlinc -Xcontext-receivers ctxr.kt -d o38r2 =====
error: experimental context receivers are superseded by context parameters.
Remove the '-Xcontext-receivers' compiler argument and migrate to the new syntax.

See the context parameters proposal for more details: https://kotl.in/context-parameters
ctxr.kt:3:9: error: context parameters must be named. Use '_' to declare an anonymous context parameter.
context(Logger)
        ^^^^^^
ctxr.kt:4:25: error: unresolved reference 'log'.
fun work(x: Int): Int { log("work $x"); return x * 2 }
                        ^^^
(exit 1)
```

**왜 그런가**

- ★★★ 2.4 는 `context(Logger)` 를 **새 문법으로 읽는다** — 그러니 「이름이 없다」가 되고, `Logger` 가 **암묵 수신자로 안 열려** `log(…)` 도 unresolved 다.
- ★★ `-Xcontext-receivers` 는 **플래그 자체가 거부**된다 — 이주 안내(「`Remove the '-Xcontext-receivers' compiler argument and migrate to the new syntax.`」)까지 찍는다. 옛 문법은 **격자 12칸 전부** 실패였다.

### 3. ★★ `[A] ctx1 1`·`1` · `[A] ext1 2`·`2` · `s3 tag=A tx=7` · `A` · **`[B] ctx1 4`**·`4` — 안쪽 `with` 의 `B` 가 건네졌다

**출력**

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

```text
===== kotlinc ctxsig.kt -d o38s =====
(exit 0)
===== java -cp o38s:kotlin-stdlib.jar CtxsigKt =====
[A] ctx1 1
1
[A] ext1 2
2
s3 tag=A tx=7
A
[B] ctx1 4
4
(exit 0)
```

**왜 그런가**

- ★★★ 호출 자리에서 컴파일러가 **`Logger` 타입의 값**을 스코프에서 찾아 건넨다 — `with` 가 연 암묵 수신자가 그 값이다.
- ★★ **가까운 층이 이긴다** — `A` 와 `B` 는 **다른 층**이라 모호하지 않고 안쪽 `B` 가 골라졌다.
- ★ `both` 는 `Logger`(바깥 층)와 `Tx`(안쪽 층)를 **타입마다 따로** 찾았다. `anon` 은 `_` 로 받아 `contextOf<Logger>()` 로 꺼냈다.

### 4. ★★★ `ctx1(Logger, int)` · `ext1(Logger, int)` · `both(Logger, Tx, String, int)` · `anon(Logger)` — **context parameter 가 맨 앞**이고, `ctx1` 과 `ext1` 의 디스크립터는 **한 글자도 같다**(`(LLogger;I)I`)

**출력**

```text
===== javap -s -p o38s/CtxsigKt.class =====
Compiled from "ctxsig.kt"
public final class CtxsigKt {
  public static final int ctx1(Logger, int);
    descriptor: (LLogger;I)I

  public static final int ext1(Logger, int);
    descriptor: (LLogger;I)I

  public static final java.lang.String both(Logger, Tx, java.lang.String, int);
    descriptor: (LLogger;LTx;Ljava/lang/String;I)Ljava/lang/String;

  public static final java.lang.String anon(Logger);
    descriptor: (LLogger;)Ljava/lang/String;

  public static final void main();
    descriptor: ()V

  public static void main(java.lang.String[]);
    descriptor: ([Ljava/lang/String;)V
}
(exit 0)
```

**왜 그런가**

- ★★★ JVM 백엔드는 context parameter 를 **평범한 첫 매개변수**로 내린다. 확장 함수의 수신자도 첫 매개변수이므로([13번 주제](../13-extension-functions-and-properties/)) 모양이 같아진다.
- ★★ `both` 는 **context 둘 → 확장 수신자 → 일반 인자** 순이다. 선언에 적힌 순서 그대로다.
- ★ 이것은 **구현**이다 — 문서가 매개변수 순서를 약속하지 않는다.

### 5. ★★★ **6·9·12·17·20·22번째 줄**이 막힌다 — `log("c1")`·`tag` 는 「`unresolved reference`」 · `this.tag` 는 「`'this' is not defined in this context.`」 · `g1` 은 「`no context argument for 'lg: Logger' found.`」 · `g2` 는 「`multiple potential context arguments for 'lg: Logger' in scope.`」 · `g3` 은 「`no context argument for 'context: A' found.`」 · **3번째 줄 `r1` 은 통과**

**출력**

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

```text
===== kotlinc ctxbad.kt -d o38b =====
ctxbad.kt:6:12: error: unresolved reference 'log'.
fun c1() { log("c1") }
           ^^^
ctxbad.kt:9:20: error: unresolved reference 'tag'.
fun c2() { println(tag) }
                   ^^^
ctxbad.kt:12:20: error: 'this' is not defined in this context.
fun c3() { println(this.tag) }
                   ^^^^
ctxbad.kt:12:25: error: unresolved reference 'tag'.
fun c3() { println(this.tag) }
                        ^^^
ctxbad.kt:17:20: error: no context argument for 'lg: Logger' found.
fun g1(): String = c4()
                   ^^
ctxbad.kt:20:20: error: multiple potential context arguments for 'lg: Logger' in scope.
fun g2(): String = c4()
                   ^^
ctxbad.kt:22:20: error: no context argument for 'context: A' found.
fun g3(): Logger = contextOf<Logger>()
                   ^^^^^^^^^
(exit 1)
```

**왜 그런가**

- ★★★ **context parameter 는 암묵 수신자가 아니다** — 몸통에서 `this` 가 없고 멤버를 이름만으로 못 부른다. `lg.log(…)` 처럼 **이름으로** 써야 한다.
- ★★★ `r1` 은 **확장 함수**라 `Logger` 가 **수신자**다 — 같은 세 가지(`log(…)`·`tag`·`this.tag`)가 전부 된다. 이 대조가 곧 「수신자와의 차이」다.
- ★★ 호출 자리는 **타입으로** 찾는다 — 없으면 `no context argument`, 같은 층에 둘(`a`·`b`)이면 `multiple potential`.

### 6. ★ **통과** — `[J] ctx1 5`·`5` · `[J] ext1 6`·`6` · `s9 tag=J tx=8`

**출력**

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

```text
===== javac -cp o38s -d o38s JCtx.java =====
(exit 0)
===== java -cp o38s:kotlin-stdlib.jar JCtx =====
[J] ctx1 5
5
[J] ext1 6
6
s9 tag=J tx=8
(exit 0)
```

**왜 그런가**

- ★★ Java 에게 `ctx1` 은 `(Logger, int)` 일 뿐이다(4번). **「스코프에서 찾아 건넨다」는 Kotlin 컴파일러의 일**이라 Java 에는 없고, Java 는 **첫 인자로 직접** 넘긴다.

### 7. **컴파일러 판이 하나뿐이라 확인할 수 없다** — 격자는 **2.4.20 컴파일러가 흉내 낸 언어 판**을 보여 줄 뿐이다 · 확인할 수 있는 것은 상태표(「Available since 2.2.0」)와 stdlib 의 `@SinceKotlin("2.2")`(11번), 그리고 도움말의 「experimental」 문구다

**왜 그런가**

- ★★★ 「2.2.0 에 실험으로 들어왔다」는 **2.2.0 이라는 컴파일러를 받았을 때** 무엇이 됐나의 이야기다. 이 머신의 `-language-version 2.1` + 플래그가 통과한 것은 **2.4.20 이 그 판을 흉내 내면서 기능을 켜 준 것**이지, 2.1 컴파일러의 동작이 아니다.
- ★ 그래서 이 문서는 그것을 **제5의 상태**로 적었다 — 같은 질문을 **다른 창**(상태표·`@SinceKotlin`·도움말 문구)으로 물었다. 그 창들은 「2.2.0 컴파일러가 무엇을 경고했나」를 **못 본다.**

```text
===== kotlinc -X | grep -E '^  -X(context-parameters|context-receivers|explicit-context-arguments) ' =====
  -Xcontext-parameters       Enable experimental context parameters.
  -Xcontext-receivers        Enable experimental context receivers.
  -Xexplicit-context-arguments Enable explicit passing of context arguments using named argument syntax.
(exit 0)
```

### 8. 3번은 **다른 층**이라 모호하지 않고 **가까운 쪽(`B`)** 이 골라졌다 · 5번의 `g2` 는 `a`·`b` 가 **같은 층**(한 선언의 context 목록)이라 「`multiple potential context arguments`」로 막혔다

**왜 그런가**

- ★★ 문서의 규칙은 「**same scope level**」에서의 모호성이다. 중첩 `with` 는 층이 둘이라 안쪽이 이기고, 한 `context(a: Logger, b: Logger)` 목록은 **한 층**이라 고를 수 없다.
- ★ 그래서 같은 타입 둘이 필요하면 **명시 인자**로 받는다.

### 9. **Kotlin 컴파일러**가 가른다 — JVM 서명은 같지만 **몸통 안에서 `this` 가 되느냐**가 다르다 · 확장 함수(수신자)는 멤버를 이름만으로 부르고, context parameter 는 **이름으로만** 쓴다

**왜 그런가**

- ★★★ 4번에서 `ctx1` 과 `ext1` 의 디스크립터가 같았다 — **바이트코드로는 못 가른다.** 차이는 5번의 에러에서만 드러난다(`r1` 통과 · `c1`\~`c3` 실패).
- ★★ [37번 주제](../37-lambdas-with-receiver-and-type-safe-builders/) (4)가 「수신자 있음」이 **메타데이터에만** 있다고 보였다. context parameter 도 같은 구조일 것으로 보이지만 **이 문서는 메타데이터를 재지 않았다** — 여기서 확인한 것은 디스크립터가 같다는 데까지다.

### 10. 몸통의 `log("work $x")` 가 **「`unresolved reference 'log'.`」** 가 된다 — 이름을 붙인 `log` 는 **값**일 뿐, `Logger` 를 암묵 수신자로 열지 않기 때문이다

**왜 그런가**

- ★★★ 옛 context receivers 는 `Logger` 를 **수신자로** 열어 멤버 `log(…)` 를 이름 없이 부르게 했다. 새 문법은 그 성질을 **버렸다** — 2번의 2.4 출력에 그 흔적이 그대로 있다(이름 에러 + `log` unresolved).
- ★ 5번의 `c1` 이 바로 그 꼴이다(`context(lg: Logger) fun c1() { log("c1") }`). 이주는 **이름 붙이기 + 몸통의 모든 암묵 호출을 `이름.` 으로** 고치는 일이다.

### 11. **아니다** — `contextOf` 는 **context parameter 하나를 받아 그대로 돌려주는 `inline` 함수**다 · `context: A` 는 **`contextOf` 자신의 context parameter** 다

**출력**

```text
===== unzip -o -q kotlin-stdlib-sources.jar commonMain/kotlin/contextParameters/ContextOf.kt =====
(exit 0)
===== grep -n -B2 'fun <A> contextOf' commonMain/kotlin/contextParameters/ContextOf.kt =====
27-@SinceKotlin("2.2")
28-context(context: @NoInfer A)
29:public inline fun <A> contextOf(): @NoInfer A = context
(exit 0)
```

**왜 그런가**

- ★★ 선언이 `context(context: @NoInfer A)` · `= context` 다. 같은 규칙(호출 자리에서 타입으로 찾기)을 쓰는 **평범한 stdlib 함수**라, 찾을 것이 없으면 **자기 매개변수 이름**(`context: A`)으로 에러가 난다.
- ★ `@SinceKotlin("2.2")` — 상태표의 「2.2.0 도입」과 맞는다(7번).

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

```text
===== javap -version =====
21.0.5
(exit 0)
```

★ **흔들리는 칸과 안 흔들리는 칸**

| 흔들린다 | 안 흔들린다 |
|---|---|
| **없다** — 해시코드·주소·시간을 찍지 않았다 | 판 격자 24칸 · 통과 수 · 실행 출력 · `javap` 출력 |
| | 진단의 **문구·`파일:줄:칸`·캐럿** |
| | 모든 **종료 코드** |

> 근거 — 캡처 스크립트를 처음부터 다시 돌려 **블록 전체를 바이트 단위로 대조**했다.
>
> 실측 — `capture.sh blocks` 와 `capture.sh blocks-recheck` 를 처음부터 따로 돌려 `normalize-shaky.py` 로 대조했다 —\
> **블록 80개 · 동일 80 · 흔들린 칸 0 · ★고칠 것 0**(38\~41 네 주제를 한 캡처로 받았다). `diff -rq` 도 차이 0 이다.\
> ★ **정규화 규칙은 하나도 안 썼다** — 기본 넷(주소·PID·스레드 id·시간)에 걸리는 칸이 애초에 없었다.

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `ctxp.kt` · `ctxr.kt` · `grid38.py` | ★★★ 판 격자 — 두 문법 × 네 판 × 플래그 셋 | 스크립트가 `kotlinc` 24회 |
| `ctxp.kt` | 대표 칸 넷의 전문 · 실행 | `kotlinc` 4회 → `java` |
| `ctxr.kt` | 옛 문법 — 2.4 기본 · `-Xcontext-receivers` | `kotlinc` 2회(실패가 결과) |
| `ctxsig.kt` | ★★ 호출 자리 해소 · 가까운 층 · `javap -s` | `kotlinc` → `java` · `javap -s -p` |
| `JCtx.java` | Java 쪽 — 첫 인자로 직접 | `javac` → `java` |
| `ctxbad.kt` | ★★★ 이름으로만 · 없을 때 · 둘일 때 | `kotlinc`(실패가 결과) |
| `ContextOf.kt`(stdlib 소스 jar) | `contextOf` 의 선언 | `unzip` → `grep` |
| `ctxfn.kt` | context 를 받는 함수 타입 한 벌 | `kotlinc` → `java` |
| `form38.kt` | 형태 한 벌 | `kotlinc` → `java` |

**구현 의존 항목** — context parameter 가 **맨 앞 매개변수**인 것 · 확장 함수와 디스크립터가 같은 것 · `-language-version 2.1` 에서 플래그로 켜지는 것 · 도움말 문구 · 진단 문구 — 이 컴파일러·판의 산출물이다.\
반면 **「이름으로만 쓴다」「호출 자리에서 타입으로 찾는다」「같은 층에 둘이면 모호성」「context receivers 폐기」** 는 **언어의 계약**이다.

**★ 던져 봤더니 예상과 달랐던 것 — 세 건**

1. ★★★ **`-language-version 2.1` 에서도 플래그로 켜졌다** — 「2.2 실험」을 판 격자로 확인할 수 있으리라는 전제가 틀렸다. 격자의 축은 **컴파일러 판이 아니라 흉내 내는 언어 판**이다(7번).
2. ★★ **도움말이 아직 「`Enable experimental context parameters.`」** — Stable 이 된 판의 도움말인데도 그렇다(7번).
3. ★ **`contextOf` 의 에러 문구에 `context: A` 가 나왔다** — 특별 장치가 아니라 **context parameter 를 받는 평범한 함수**라서다(11번).
