# kotlin/syntax/49 — `Result` 와 `runCatching` — 예외를 값으로 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Exceptions](https://kotlinlang.org/docs/exceptions.html) · [kotlin.Result API](https://kotlinlang.org/api/core/kotlin-stdlib/kotlin/-result/) — 이 문서는 그 목록을 따르되, 문장은 인용하지 않고 **이 판의 stdlib 소스 jar**(`kotlin-stdlib-sources.jar` 2.4.20)의 KDoc 과 구현, 그리고 **이 판의 컴파일러 jar**(`kotlin-compiler.jar`)에 남은 진단 문구·언어 기능 표를 근거로 삼는다((2)(5)).
> ★★ **KEEP 문서와 1.5 릴리스 노트는 이 작업에서 열지 못했다**(외부 네트워크를 쓰지 않았다) — 「왜 제한했었나」의 **설계 논거**는 이 문서에 없다. 대신 **컴파일러가 스스로 남긴 기록**을 읽었다((2)).
> **실행 검증** — 이 문서의 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `java`·`javap` 에서 실제로 얻었다.\
> `kotlinc` 10회(격자 스크립트 안의 5회 포함 · 5회 모두 대조용 칸 하나 때문에 실패 — 그 실패가 결과다 · `-language-version 1.9` 거부 1회) · `java` 4회 · `javap` 5회(컴파일러 클래스 3 · 이 문서의 클래스 2) + stdlib `kotlin.Result` 1회 · stdlib 소스 jar 에서 발췌 3곳.\
> ★★ 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적지 않았다. **「막힌 칸 N / M」·「runCatching 만 잡은 행 N / M」은 스크립트·프로그램이 스스로 센 것**이다.
> **버전** — `Result`·`runCatching`·`map`·`mapCatching`·`recover`·`fold`·`getOrThrow` 는 stdlib 소스에 **`@SinceKotlin("1.3")`**((5)). ★★★ **「`Result` 를 반환 타입으로 못 쓴다」는 제한은 1.5 에서 풀렸다** — 이 판의 컴파일러가 그 기능을 **`LanguageVersion.KOTLIN_1_5`** 로 적어 두었다((2)). 그 전 판에서 막히는 것은 **이 판에서 잴 수 없다** — `-language-version 1.9` 부터 거부한다((1)).
> **경계** — ★★★ **검사 예외가 없다는 것**(그래서 `Result` 도 컴파일러가 강제하지 않는 관용구라는 것)은 [34번 주제](../34-exceptions-nothing-and-try-expression/)와 [`../../언어-특성/README.md`](../../언어-특성/README.md) §8 이 정본이다. `value class` 의 박싱·이름 뭉개기 규칙은 [26번 주제](../26-value-class-and-boxing/)가 정본이다 — 여기서는 **`Result` 가 그 규칙에서 벗어나는 한 자리**만 본다.\
> 코루틴의 취소(`CancellationException`)가 **왜** 문제인지는 [목록의 **53번 주제**](../53-structured-concurrency-job-cancellation-exceptions/)(구조적 동시성)의 몫이다 — 여기서는 **`runCatching` 이 무엇을 잡는가**만 본다. `require`/`check`/`error`/`TODO` 가 던지는 것은 [목록의 **51번 주제**](../51-preconditions-require-check-error-todo/)다.\
> ★ **대비** — 오류를 **타입이** 말하는 Rust `Result<T, E>` 는 [Rust 22번](../../../rust/syntax/22-result-question-mark-and-from/), 오류를 **다중 반환 값**으로 돌려주는 Go 는 [Go 23번](../../../go/syntax/23-error-interface-and-errors-as-values/)이 정본이다.
> 이 본문은 Claude 작성이다(원고 없음).

★★★ **본체는 첫째 창이다** — 「**반환 타입 판별 격자 — `Result` 를 쓰는 자리 열 곳 × `-language-version` 2.0\~2.4 → 컴파일되나 · 진단**」. README 의 학습 목표는 「**왜 제한되는지**」인데, **이 판에서는 한 칸도 막히지 않는다.** 그래서 이 주제의 첫 결론은 「제한이 **지금은 없다**」이고, 「왜 있었나」는 **컴파일러에 남은 흔적**으로만 읽는다.

## 이 주제가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **언어 보장 / API 계약** | 서명·KDoc 이 약속한 것 | ★★★ `runCatching` KDoc 「**catching any [Throwable] exception**」 · `map` KDoc 「**rethrows any [Throwable] exception thrown by [transform]**」 · `mapCatching` 「**catches any [Throwable] exception thrown by [transform]**」 · `Result` 는 **`@JvmInline value class`**(선언) |
| **구현(컴파일러·stdlib)** | 이 판이 실제로 하는 것 | ★★ 컴파일러 jar 의 **옛 진단 문구 두 개**와 **1.4·1.5 기능 게이트** · `Result` 를 받는 함수가 **이름이 안 뭉개진다**(`take(java.lang.Object)`) · `runCatching` 이 `try … catch (e: Throwable)` 한 덩어리 |
| **이 판의 관찰** | kotlinc 2.4.20 에서 이번에 본 것 | 격자 값 · 진단 문구 · `javap` 의 이름 |

## 이 판

```text
===== kotlinc -version =====
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | (이 주제에는 없다) | 해시코드·주소·시간을 찍지 않았다 · 스택 트레이스를 찍지 않았다 |
| 안 흔들린다 | 판별 격자 11행 × 5판 · 막힌 칸 수 · 진단 문구 | 컴파일러 진단은 결정적이다 |
| 안 흔들린다 | `javap` 출력 — 뭉개진 이름의 해시 글자(`-tmnojjU`)까지 | 같은 소스·같은 판이면 같다. ★ 해시 글자는 **판이 바뀌면 달라질 수 있는** 칸이라 **모양**(`이름-해시`)만 근거로 쓴다([26번 주제](../26-value-class-and-boxing/)와 같은 선언) |
| 안 흔들린다 | 컴파일러 클래스의 `javap` 발췌(오프셋·상수 풀 번호째) · 종료 코드 | 같은 `kotlin-compiler.jar` 면 같다 |

★ 근거 — 캡처 스크립트를 처음부터 두 번 돌려 **블록 전체를 대조**했다(수치는 3-answer 의 「실행 검증」).

## 한눈에 — 쉽게 말하면

**`Result` 는 「택배 상자」다 — 안에 물건(값)이 들었거나, 「배송 실패」 쪽지(예외)가 들었다.** 받은 사람은 상자를 **열어 봐야**(`fold`·`getOrElse`) 어느 쪽인지 안다. `runCatching { … }` 은 일을 시켜 보고 **무슨 일이 터지든** 상자에 담아 준다 — 사소한 실수(`Exception`)도, 「아직 안 만들었다」(`TODO()` 의 `NotImplementedError`)나 「있어서는 안 될 상태」(`AssertionError`) 같은 **`Error`** 도.
★ 한때는 이 상자를 **함수의 반환값으로 내보내는 것**이 금지였다. 지금(1.5 이후)은 된다 — 이 판의 컴파일러에는 **그 금지 조항의 문구만** 남아 있다.

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 상자를 반환값으로 내보내기 | `fun f(): Result<Int>` — 이 판에서 **된다** | (1) ★ |
| 옛 금지 조항 문구 | 컴파일러 jar 의 `'kotlin.Result' cannot be used as a return type` · 게이트 `KOTLIN_1_5` | (2) ★ |
| 상자는 포장만 있다 | `value class` — JVM 에서 **`Object`** 로 다닌다 | (3) |
| 무엇이 터지든 담는다 | `runCatching` 은 **`Throwable` 전부** — `Error` 까지 | (4) ★ |
| 상자 안에서 또 터지면 | `map` 은 **밖으로 던지고**, `mapCatching` 은 **다시 담는다** | (5) ★ |

```text
   runCatching { 일 }                        catch (e: Exception)
   ────────────────────────────────────────────────────────────────
   IllegalStateException      → Failure      잡힌다
   NumberFormatException      → Failure      잡힌다
   NotImplementedError (Error)→ Failure      못 잡는다 — 밖으로 샌다
   AssertionError      (Error)→ Failure      못 잡는다 — 밖으로 샌다
   CancellationException      → Failure      잡힌다  (Exception 의 자손)
```

## 이 주제가 답하려는 질문

1. `Result` 를 **반환 타입·프로퍼티·널 가능 타입·컬렉션 원소·인자**로 쓸 수 있나 — 이 판에서 막히는 자리가 있나, 있었다면 **어디에 흔적이 있나.**
2. `Result` 는 JVM 에서 **무엇으로** 다니나 — `value class` 규칙대로인가.
3. `runCatching` 은 **무엇까지** 잡나 — 그리고 상자 안에서 다시 터지면(`map`) 어떻게 되나.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **판별 격자(컴파일 · `-language-version` × 자리)** | 컴파일되나 · 진단((1)) | ★ **본체 창** — 대조 칸 하나(`lateinit`)를 **일부러 막히게** 넣어 「격자가 막힘을 볼 수 있다」를 같은 블록에서 보인다 |
| ★★★ **컴파일러 jar 의 `javap`** | 옛 제한의 **진단 문구**와 **기능 게이트 판**((2)) | ★ **제5의 상태** — 「1.4 에서 막혔나」를 **1.4 로 컴파일해서** 묻지 못해(1.9 부터 거부) **컴파일러가 남긴 표**로 물었다. 이 창은 **K1 계열 클래스**만 본다 — K2 가 같은 검사를 어디에 두는지는 **못 봤다** |
| ★★ **`javap -p`** | `Result` 가 `Object` 로 다니나 · 이름이 뭉개지나((3)) | [26번 주제](../26-value-class-and-boxing/)와 같은 창 |
| ★★ **잡기 격자(실행)** | 던진 것 × (`runCatching` · `catch (e: Exception)`)((4)) | — |
| ★★ **stdlib 소스 jar 발췌** | `runCatching`·`map`·`mapCatching` 의 KDoc 계약((5)) | — |
| **인용 — 다시 안 잰다** | 검사 예외 없음 · `@Throws` · `Nothing` | [34번 주제](../34-exceptions-nothing-and-try-expression/) |
| **못 잰 것** | 1.4 이하의 실제 거부 · KEEP 의 설계 논거 | (1)(2) — 판이 없고, 문서를 열지 못했다 |
| **부적용 — 실행 시간** | 「`Result` 가 예외보다 싸다」는 **재지 않았다** | — |

### (1) ★★★ 반환 타입 판별 격자 — 이 판에서 막히는 자리

**언제 쓰나** — 「`Result` 를 반환하지 마라」는 옛 규칙을 코드 리뷰에서 만났을 때.

방법 — `Result` 를 쓰는 자리 열 곳과 **대조 칸 하나**(`lateinit` — `value class` 타입에는 원래 금지)를 한 파일에 두고, 판마다 `kotlinc -language-version` 을 바꿔 컴파일한다. 줄마다 첫 진단을 읽고, 없으면 `ok`. 마지막 줄은 **대조 칸을 뺀** 막힌 칸을 센다.

```kotlin
// ret49.kt
fun p1(): Result<Int> = runCatching { 1 }                                  // return
val p2: Result<Int> = runCatching { 2 }                                    // property
fun p3(): Result<Int>? = null                                              // nullable-return
fun p4(): List<Result<Int>> = listOf(runCatching { 4 })                    // list-element
fun p5(r: Result<Int>): Int = r.getOrThrow()                               // parameter
fun p6(r: Result<Int>?): Int? = r?.getOrNull()                             // safe-call
fun p7(r: Result<Int>?): Result<Int> = r!!                                 // not-null-assert
fun p8(r: Result<Int>?): Result<Int> = r ?: runCatching { 8 }              // elvis
interface P9 { fun get(): Result<Int> }                                    // abstract-member
suspend fun p10(): Result<Int> = runCatching { 10 }                        // suspend-return
lateinit var p11: Result<Int>                                              // lateinit
```

```python
# grid49.py
import re
import subprocess

SRC = "ret49.kt"
VERSIONS = ["2.0", "2.1", "2.2", "2.3", "2.4"]
CONTROL = "lateinit"

probes = {}
order = []
for n, line in enumerate(open(SRC, encoding="utf-8"), 1):
    m = re.search(r"// (\S+)$", line.rstrip("\n"))
    if m:
        probes[n] = m.group(1)
        order.append(m.group(1))

result = {}
for v in VERSIONS:
    run = subprocess.run(["kotlinc", "-language-version", v, SRC, "-d", "o49v" + v.replace(".", "")],
                         capture_output=True, text=True)
    first = {}
    for line in (run.stdout + run.stderr).splitlines():
        m = re.match(r"ret49\.kt:(\d+):\d+: error: (.*)$", line)
        if m and int(m.group(1)) not in first:
            first[int(m.group(1))] = m.group(2)
    for n, name in probes.items():
        result[(name, v)] = "error: " + first[n] if n in first else "ok"
    result[("exit", v)] = str(run.returncode)

print("\t".join(["probe"] + VERSIONS))
blocked = cells = 0
for name in order + ["exit"]:
    row = [result[(name, v)] for v in VERSIONS]
    if len(row) != len(VERSIONS):
        raise SystemExit("cell count mismatch: " + name)
    print("\t".join([name] + row))
    if name in (CONTROL, "exit"):
        continue
    for cell in row:
        cells += 1
        if cell != "ok":
            blocked += 1
print("blocked cells outside the control row: %d / %d" % (blocked, cells))
```

```text
===== kotlinc -language-version 1.9 ret49.kt -d o49x =====
error: language version 1.9 is no longer supported; use version 2.0 or greater instead.
(exit 1)
```

```text
===== python3 grid49.py =====
probe	2.0	2.1	2.2	2.3	2.4
return	ok	ok	ok	ok	ok
property	ok	ok	ok	ok	ok
nullable-return	ok	ok	ok	ok	ok
list-element	ok	ok	ok	ok	ok
parameter	ok	ok	ok	ok	ok
safe-call	ok	ok	ok	ok	ok
not-null-assert	ok	ok	ok	ok	ok
elvis	ok	ok	ok	ok	ok
abstract-member	ok	ok	ok	ok	ok
suspend-return	ok	ok	ok	ok	ok
lateinit	error: 'lateinit' modifier is not allowed on properties of inline class types.	error: 'lateinit' modifier is not allowed on properties of inline class types.	error: 'lateinit' modifier is not allowed on properties of inline class types.	error: 'lateinit' modifier is not allowed on properties of inline class types.	error: 'lateinit' modifier is not allowed on properties of inline class types.
exit	1	1	1	1	1
blocked cells outside the control row: 0 / 50
(exit 0)
```

- ★★★ **막힌 칸은 50칸 중 0칸이다** — 반환 타입(`return`) · 프로퍼티(`property`) · `Result<Int>?` 반환 · `List<Result<Int>>` · 인자 · `?.` · `!!` · `?:` · 인터페이스의 추상 멤버 · `suspend` 반환 — **2.0 부터 2.4 까지 전부 컴파일된다.**
- ★★★ **대조 칸은 다섯 판 모두 막혔다** — `'lateinit' modifier is not allowed on properties of inline class types.` 그래서 **「0」은 격자가 눈이 먼 결과가 아니다**(규칙 22) — 같은 컴파일에서 막힘을 **본** 칸이 있다. 종료 코드가 판마다 `1` 인 것도 이 칸 하나 때문이다.
- ★★ **2.0 아래는 이 판에서 잴 수 없다** — `language version 1.9 is no longer supported`. 제한이 **있던** 판(1.4 이하)을 직접 던져 보는 길은 막혀 있다 — 그래서 (2)로 창을 바꾼다.

### (2) ★★★ 제한의 흔적 — 컴파일러가 남긴 표

```text
===== unzip -o -q "$KOTLIN_HOME/lib/kotlin-compiler.jar" org/jetbrains/kotlin/config/LanguageFeature.class org/jetbrains/kotlin/diagnostics/rendering/DefaultErrorMessages.class org/jetbrains/kotlin/resolve/checkers/ResultClassInReturnTypeChecker.class -d kc =====
(exit 0)
===== javap -c -p -cp kc org.jetbrains.kotlin.config.LanguageFeature | grep -A2 -E 'String AllowNullOperatorsForResult(AndResultReturnTypeByDefault)?$' =====
    1897: ldc           #32                 // String AllowNullOperatorsForResult
    1899: bipush        85
    1901: getstatic     #1195               // Field org/jetbrains/kotlin/config/LanguageVersion.KOTLIN_1_4:Lorg/jetbrains/kotlin/config/LanguageVersion;
--
    2490: ldc           #33                 // String AllowNullOperatorsForResultAndResultReturnTypeByDefault
    2492: bipush        112
    2494: getstatic     #1196               // Field org/jetbrains/kotlin/config/LanguageVersion.KOTLIN_1_5:Lorg/jetbrains/kotlin/config/LanguageVersion;
(exit 0)
===== javap -c -p -cp kc org.jetbrains.kotlin.diagnostics.rendering.DefaultErrorMessages | grep -E 'String .*kotlin\.Result' =====
    8171: ldc           #89                 // String \'kotlin.Result\' cannot be used as a return type
    8182: ldc_w         #312                // String Expression of type \'\'kotlin.Result\'\' cannot be used as a left operand of \'\'{0}\'\'
(exit 0)
===== javap -c -p -cp kc org.jetbrains.kotlin.resolve.checkers.ResultClassInReturnTypeChecker | grep -E 'LanguageFeature\.|Errors\.' =====
      26: getstatic     #36                 // Field org/jetbrains/kotlin/config/LanguageFeature.AllowNullOperatorsForResultAndResultReturnTypeByDefault:Lorg/jetbrains/kotlin/config/LanguageFeature;
     122: getstatic     #38                 // Field org/jetbrains/kotlin/diagnostics/Errors.RESULT_CLASS_IN_RETURN_TYPE:Lorg/jetbrains/kotlin/diagnostics/DiagnosticFactory0;
(exit 0)
```

- ★★★ **컴파일러 안에 옛 진단 문구가 둘 있다** — `'kotlin.Result' cannot be used as a return type` 과 `Expression of type ''kotlin.Result'' cannot be used as a left operand of ''{0}''`(자리 `{0}` 에 연산자가 들어간다). 앞쪽이 **반환 타입 제한**, 뒤쪽이 **`?.`·`?:` 같은 널 연산자의 왼쪽에 `Result` 를 두는 제한**이다.
- ★★★ **두 제한을 푸는 기능이 판으로 적혀 있다** — `AllowNullOperatorsForResult` 는 **`KOTLIN_1_4`**, `AllowNullOperatorsForResultAndResultReturnTypeByDefault` 는 **`KOTLIN_1_5`**. 검사기 `ResultClassInReturnTypeChecker` 는 **뒤쪽 기능을 먼저 묻고**, 없을 때만 `RESULT_CLASS_IN_RETURN_TYPE` 을 낸다.
- ★★ 그래서 이 판에서 읽을 수 있는 「왜 막혔었나」는 여기까지다 — **1.3 에 `Result` 가 들어올 때 반환 타입과 널 연산자 자리를 막아 두었고, 널 연산자는 1.4 부터, 반환 타입은 1.5 부터 기본으로 풀었다.** 막아 둔 **이유**(설계 논의)는 KEEP 문서에 있으나 **이 작업에서 열지 못했다.**
- ★ 이 세 클래스는 `org.jetbrains.kotlin.resolve`·`diagnostics` 아래의 **K1 계열**이다 — 2.4.20 의 기본 프런트엔드(K2)가 같은 검사를 따로 두는지는 **확인하지 않았다.** (1)의 격자가 보인 것은 **K2 가 2.0\~2.4 에서 막지 않는다**는 것뿐이다.

### (3) ★★ `Result` 는 JVM 에서 `Object` 로 다닌다 — 그런데 이름은 안 뭉개진다

```kotlin
// val49.kt
@JvmInline
value class Id(val raw: Int)

fun make(): Result<Int> = runCatching { 1 }

fun take(r: Result<Int>): Int = r.getOrThrow()

fun takeId(i: Id): Int = i.raw

fun makeId(): Id = Id(7)

val kept: Result<Int> = make()

fun many(): List<Result<Int>> = listOf(make())

fun main() {
    println("${make()} ${take(make())} $kept ${many()} ${takeId(makeId())}")
}
```

```text
===== kotlinc val49.kt -d o49v =====
(exit 0)
===== java -cp o49v:kotlin-stdlib.jar Val49Kt =====
Success(1) 1 Success(1) [Success(1)] 7
(exit 0)
===== javap -p o49v/Val49Kt.class =====
Compiled from "val49.kt"
public final class Val49Kt {
  private static final java.lang.Object kept;
  public static final java.lang.Object make();
  public static final int take(java.lang.Object);
  public static final int takeId-tmnojjU(int);
  public static final int makeId();
  public static final java.lang.Object getKept();
  public static final java.util.List<kotlin.Result<java.lang.Integer>> many();
  public static final void main();
  public static void main(java.lang.String[]);
  static {};
}
(exit 0)
===== javap -c -p o49v/Val49Kt.class | grep -E 'public static|box-impl' =====
  public static final java.lang.Object make();
  public static final int take(java.lang.Object);
  public static final int takeId-tmnojjU(int);
  public static final int makeId();
  public static final java.lang.Object getKept();
  public static final java.util.List<kotlin.Result<java.lang.Integer>> many();
       3: invokestatic  #68                 // Method kotlin/Result."box-impl":(Ljava/lang/Object;)Lkotlin/Result;
  public static final void main();
  public static void main(java.lang.String[]);
(exit 0)
```

```text
===== javap -p -cp kotlin-stdlib.jar kotlin.Result | grep -E 'class|box-impl|unbox-impl|value;' =====
public final class kotlin.Result<T> implements java.io.Serializable {
  private final java.lang.Object value;
  public static final kotlin.Result box-impl(java.lang.Object);
  public final java.lang.Object unbox-impl();
(exit 0)
```

- ★★★ **`make()` 의 반환 타입은 `java.lang.Object`**, 프로퍼티 `kept` 도 `Object` 필드와 `getKept(): Object` — `value class` 라 **알맹이(`value: Any?`)만** 다닌다. 성공이면 값 자체, 실패면 `Result.Failure` 객체다((5)).
- ★★★ **`take(r: Result<Int>)` 는 `take(java.lang.Object)` — 이름이 뭉개지지 않았다.** 같은 파일의 사용자 `value class Id` 를 받는 `takeId` 는 **`takeId-tmnojjU(int)`** 로 뭉개졌다. [26번 주제](../26-value-class-and-boxing/) (1)의 규칙(「`value class` 를 받으면 이름이 뭉개진다」)에서 **`Result` 만 벗어난다** — 이 판의 관찰이고, 까닭은 **확인하지 않았다.**
- ★★ **`List<Result<Int>>` 에 넣을 때는 박싱된다** — `many()` 본문에 `Result."box-impl"` 이 있고, 서명에는 `List<kotlin.Result<java.lang.Integer>>` 가 그대로 남는다. 제네릭 자리에서는 **포장이 실제 객체**가 된다(26번 주제의 규칙 그대로).
- ★ `kotlin.Result` 클래스 자체에는 `private final Object value` 하나와 `box-impl`·`unbox-impl` 이 있다 — 박싱될 때 쓰는 그 한 겹이다.

### (4) ★★★ `runCatching` 은 무엇까지 잡나

```kotlin
// catch49.kt
import java.util.concurrent.CancellationException

val throwers: List<Pair<String, () -> Int>> = listOf(
    "error(\"x\")" to { error("x") },
    "\"x\".toInt()" to { "x".toInt() },
    "TODO()" to { TODO() },
    "throw AssertionError()" to { throw AssertionError("a") },
    "throw CancellationException()" to { throw CancellationException("c") },
)

fun byRunCatching(f: () -> Int): String =
    runCatching(f).exceptionOrNull()?.let { "failure " + it::class.simpleName } ?: "success"

fun byCatchException(f: () -> Int): String =
    try { f(); "success" } catch (e: Exception) { "caught " + e::class.simpleName } catch (e: Throwable) { "escaped " + e::class.simpleName }

fun main() {
    println(listOf("thrower", "runCatching", "catch (e: Exception)", "is Exception").joinToString("\t"))
    var onlyRunCatching = 0
    for ((name, f) in throwers) {
        val a = byRunCatching(f)
        val b = byCatchException(f)
        val kind = runCatching(f).exceptionOrNull() is Exception
        val row = listOf(name, a, b, "$kind")
        check(row.size == 4)
        println(row.joinToString("\t"))
        if (a.startsWith("failure") && b.startsWith("escaped")) onlyRunCatching++
    }
    println("rows held by runCatching but not by catch (e: Exception): $onlyRunCatching / ${throwers.size}")
}
```

```text
===== kotlinc catch49.kt -d o49c =====
(exit 0)
===== java -cp o49c:kotlin-stdlib.jar Catch49Kt =====
thrower	runCatching	catch (e: Exception)	is Exception
error("x")	failure IllegalStateException	caught IllegalStateException	true
"x".toInt()	failure NumberFormatException	caught NumberFormatException	true
TODO()	failure NotImplementedError	escaped NotImplementedError	false
throw AssertionError()	failure AssertionError	escaped AssertionError	false
throw CancellationException()	failure CancellationException	caught CancellationException	true
rows held by runCatching but not by catch (e: Exception): 2 / 5
(exit 0)
```

- ★★★ **`runCatching` 은 다섯 다 잡았다 — `catch (e: Exception)` 은 둘을 놓쳤다**(`NotImplementedError`·`AssertionError`). 둘 다 **`Error` 의 자손**이다(`is Exception` 이 `false`).
- ★★★ `TODO()` 가 던지는 `NotImplementedError` 도 `runCatching` 안에서는 **실패 값**이 된다 — 「아직 안 만든 코드」가 **조용히 `Failure`** 로 흘러갈 수 있다.
- ★★ **`CancellationException` 은 두 쪽 다 잡는다** — JVM 에서 그것은 **`Exception`** 의 자손이다(`is Exception` 이 `true`). 그러니 「`runCatching` 이 취소를 삼킨다」는 **`catch (e: Exception)` 도 똑같이** 삼킨다. 취소가 삼켜지면 **무엇이 깨지나**는 [목록의 **53번 주제**](../53-structured-concurrency-job-cancellation-exceptions/)다.

### (5) ★★ 상자 안에서 다시 터지면 — `map` 대 `mapCatching`

```kotlin
// chain49.kt
fun main() {
    val ok: Result<Int> = runCatching { 21 }
    val bad: Result<Int> = runCatching { "x".toInt() }
    println("1 $ok | $bad")
    println("2 ${ok.getOrNull()} | ${bad.getOrNull()} | ${bad.exceptionOrNull()?.message}")
    println("3 ${ok.getOrElse { -1 }} | ${bad.getOrElse { -1 }} | ${bad.getOrDefault(0)}")
    println("4 ${ok.map { it * 2 }} | ${bad.map { it * 2 }}")
    println("5 ${ok.fold({ "v=$it" }, { "e=${it::class.simpleName}" })} | ${bad.fold({ "v=$it" }, { "e=${it::class.simpleName}" })}")
    println("6 ${bad.recover { 0 }} | ${ok.recover { 0 }}")
    println("7 ${ok.mapCatching { check(it > 100) { "too small" }; it }}")
    try {
        println("8 ${ok.map { check(it > 100) { "too small" }; it }}")
    } catch (e: IllegalStateException) {
        println("8 -> ${e::class.simpleName}: ${e.message}")
    }
    try {
        println("9 ${bad.getOrThrow()}")
    } catch (e: NumberFormatException) {
        println("9 -> ${e::class.simpleName}: ${e.message}")
    }
}
```

```text
===== kotlinc chain49.kt -d o49h =====
(exit 0)
===== java -cp o49h:kotlin-stdlib.jar Chain49Kt =====
1 Success(21) | Failure(java.lang.NumberFormatException: For input string: "x")
2 21 | null | For input string: "x"
3 21 | -1 | 0
4 Success(42) | Failure(java.lang.NumberFormatException: For input string: "x")
5 v=21 | e=NumberFormatException
6 Success(0) | Success(21)
7 Failure(java.lang.IllegalStateException: too small)
8 -> IllegalStateException: too small
9 -> NumberFormatException: For input string: "x"
(exit 0)
```

- ★★★ **`map` 안에서 던지면 밖으로 나온다**(`8 -> IllegalStateException: too small`) — `Result` 를 돌려주는 함수인데 **예외가 샌다.** `mapCatching` 은 같은 예외를 **`Failure`** 로 다시 담는다(`7`).
- ★★ **`getOrThrow` 는 담긴 예외를 원래 타입 그대로** 던진다(`9 -> NumberFormatException`) — 감싸지 않는다.
- ★★ `map` 은 실패를 그대로 통과시킨다(`4` 오른쪽) · `recover` 는 실패만 바꾼다(`6`) · `fold` 는 두 갈래를 한 값으로 접는다(`5`) · `getOrElse`·`getOrDefault`·`getOrNull` 은 상자를 연다(`2`·`3`).

```text
===== unzip -o -q kotlin-stdlib-sources.jar commonMain/kotlin/collections/Maps.kt commonMain/kotlin/collections/MapWithDefault.kt jvmMain/kotlin/collections/MapsJVM.kt jvmMain/kotlin/Collections.kt commonMain/generated/_Sequences.kt commonMain/generated/_Collections.kt commonMain/kotlin/collections/Sequence.kt commonMain/kotlin/collections/Sequences.kt jvmMain/kotlin/collections/SequencesJVM.kt commonMain/kotlin/text/Strings.kt jvmMain/kotlin/text/CharJVM.kt jvmMain/kotlin/text/regex/Regex.kt commonMain/kotlin/util/Result.kt commonMain/kotlin/collections/SequenceBuilder.kt =====
(exit 0)
```

```text
===== sed -n '16,24p' commonMain/kotlin/util/Result.kt =====
/**
 * A discriminated union that encapsulates a successful outcome with a value of type [T]
 * or a failure with an arbitrary [Throwable] exception.
 */
@SinceKotlin("1.3")
@JvmInline
public value class Result<out T> @PublishedApi internal constructor(
    @PublishedApi
    internal val value: Any?
(exit 0)
===== sed -n '136,148p' commonMain/kotlin/util/Result.kt =====
 * Calls the specified function [block] and returns its encapsulated result if invocation was successful,
 * catching any [Throwable] exception that was thrown from the [block] function execution and encapsulating it as a failure.
 */
@InlineOnly
@SinceKotlin("1.3")
public inline fun <R> runCatching(block: () -> R): Result<R> {
    return try {
        Result.success(block())
    } catch (e: Throwable) {
        Result.failure(e)
    }
}
(exit 0)
===== sed -n '240,241p;260p' commonMain/kotlin/util/Result.kt =====
 * Note, that this function rethrows any [Throwable] exception thrown by [transform] function.
 * See [mapCatching] for an alternative that encapsulates exceptions.
 * This function catches any [Throwable] exception thrown by [transform] function and encapsulates it as a failure.
(exit 0)
```

- ★★★ **「무엇이든 잡는다」는 KDoc 계약이다** — `runCatching` 「`catching any [Throwable] exception that was thrown from the [block] function execution`」, 구현도 `catch (e: Throwable)` 한 줄이다.
- ★★★ **`map` 이 던지는 것도 계약이다** — 「`Note, that this function rethrows any [Throwable] exception thrown by [transform] function. See [mapCatching] for an alternative that encapsulates exceptions.`」 · `mapCatching` 「`This function catches any [Throwable] exception thrown by [transform] function and encapsulates it as a failure.`」.
- ★ `Result` 선언 — `@SinceKotlin("1.3")` · `@JvmInline` · `value class Result<out T>` · 알맹이는 `internal val value: Any?`.

## 문법 — 형태와 규칙

**형태** — 포트 번호 파싱을 `Result` 로 돌려주고 `fold` 로 접는다.

```kotlin
// form49.kt
fun parsePort(s: String): Result<Int> = runCatching {
    val n = s.trim().toInt()
    require(n in 1..65535) { "port out of range: $n" }
    n
}

fun main() {
    for (input in listOf("8080", " 443 ", "http", "70000")) {
        val text = parsePort(input).fold(
            onSuccess = { "ok $it" },
            onFailure = { "fail ${it::class.simpleName}: ${it.message}" },
        )
        println("[$input] $text")
    }
    val ports = listOf("80", "x", "22").map { parsePort(it) }
    println("all    $ports")
    println("valid  ${ports.mapNotNull { it.getOrNull() }}")
}
```

```text
===== kotlinc form49.kt -d o49z =====
(exit 0)
===== java -cp o49z:kotlin-stdlib.jar Form49Kt =====
[8080] ok 8080
[ 443 ] ok 443
[http] fail NumberFormatException: For input string: "http"
[70000] fail IllegalArgumentException: port out of range: 70000
all    [Success(80), Failure(java.lang.NumberFormatException: For input string: "x"), Success(22)]
valid  [80, 22]
(exit 0)
```

**규칙 불릿**

- **`Result` 는 반환 타입·프로퍼티·인자·컬렉션 원소 어디든 된다**(1.5+ — 이 판에서 50칸 전부)((1)(2)).
- **`runCatching` 은 `Throwable` 전부를 잡는다** — `Error`(`TODO()`·`AssertionError`)까지((4)).
- **`map`·`recover`·`fold` 의 람다에서 던지면 밖으로 샌다** — 담으려면 `mapCatching`·`recoverCatching`((5)).
- **꺼내기** — `getOrThrow`(원래 예외를 던짐) · `getOrElse { }` · `getOrDefault(v)` · `getOrNull()` · `exceptionOrNull()`((5)).
- **컴파일러는 `Result` 를 열어 보라고 강제하지 않는다** — 검사 예외가 없는 것과 같은 자리다([34번 주제](../34-exceptions-nothing-and-try-expression/)).

## 어디서 틀리나

1. ★★★ **「`Result` 는 반환 타입으로 못 쓴다」를 지금 규칙으로 안다.** 1.5 부터 된다 — 이 판에서는 50칸 중 0칸이 막혔다((1)(2)).
2. ★★★ **`runCatching` 을 `try { } catch (e: Exception)` 과 같은 것으로 본다.** `Error` 까지 잡는다 — `TODO()` 가 실패 값으로 조용히 흘러간다((4)).
3. ★★ **`Result` 를 돌려주는 함수는 절대 안 던진다고 본다.** `map`·`recover`·`fold` 의 람다가 던지면 **밖으로 나온다**((5)).
4. ★★ **`runCatching` 만 취소를 삼킨다고 본다.** JVM 의 `CancellationException` 은 `Exception` 이라 **`catch (e: Exception)` 도 삼킨다**((4)).
5. ★ **`Result` 를 받는 함수 이름이 다른 `value class` 처럼 뭉개진다고 본다.** 이 판에서 `take(java.lang.Object)` — 안 뭉개졌다((3)).
6. ★ **`Result` 가 에러의 타입을 말해 준다고 본다.** 실패는 언제나 `Throwable` 이다 — Rust `Result<T, E>` 의 `E` 가 없다(아래 대비).

## 구현 세부사항 대 언어 보장

| 항목 | 어느 쪽인가 | 근거 |
|---|---|---|
| 1.5+ 에서 `Result` 를 반환 타입으로 쓸 수 있다 | ★★★ **언어 판의 규칙** — 이 판의 컴파일러가 게이트를 `KOTLIN_1_5` 로 적는다 | (1)(2) |
| 옛 진단 문구 · 검사기 클래스 이름 | ★ **컴파일러 구현** — K1 계열 클래스 | (2) |
| `runCatching` 은 `Throwable` 전부 | ★★★ **API 계약(KDoc)** | (4)(5) |
| `map` 은 람다 예외를 다시 던진다 · `mapCatching` 은 담는다 | ★★★ **API 계약(KDoc)** | (5) |
| `Result` 가 `value class` | ★★ **API 계약(선언)** | (5) |
| `Object` 로 다닌다 · `take(Object)` 가 안 뭉개진다 · `box-impl` | ★ **JVM 백엔드 구현** — 이 판의 관찰 | (3) |
| `CancellationException` 이 `Exception` 의 자손 | ★ **플랫폼(JVM) 사실** — `java.util.concurrent` 의 클래스 · 이 판에서 `is Exception` 으로 확인 | (4) |
| 「`Result` 가 예외보다 싸다」 | **재지 않았다** | — |

★★ **가장 조심할 자리** — README 의 학습 목표(「왜 제한되는지」)는 **1.5 이전의 전제**다. 지금 설명할 수 있어야 하는 것은 「**제한은 풀렸고, 남은 것은 `runCatching` 이 너무 많이 잡는다는 것**」이다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 실패를 값으로 모아 나중에 가른다(여러 입력 검사) | `runCatching` + `fold`/`getOrNull` | (5) · 형태 블록 |
| 예상한 예외만 잡는다 | ★ `try { } catch (e: 특정예외)` | (4) — `runCatching` 은 `Error` 까지 먹는다 |
| 코루틴 안 | `runCatching` 을 피하거나 `CancellationException` 을 **다시 던진다** | (4) · [목록의 **53번 주제**](../53-structured-concurrency-job-cancellation-exceptions/) |
| 변환 중 예외도 실패로 | `mapCatching` · `recoverCatching` | (5) |
| 실패 원인을 **타입으로** 구분해야 한다 | `sealed` 결과 타입을 직접 만든다 | (4) — `Result` 의 실패는 `Throwable` 하나다 |
| 공개 API 의 반환 타입 | 된다(1.5+) — 다만 Java 호출자는 **`Object`** 를 받는다 | (3) |

## 핵심 문장

1. **`Result` 를 반환 타입으로 두는 제한은 1.5 에서 풀렸다** — 이 판에서는 쓰는 자리 열 곳 × 다섯 판, **50칸 중 0칸**이 막혔다.
2. 그 제한의 흔적은 **컴파일러 안에** 있다 — 진단 문구 두 개와 게이트 `KOTLIN_1_4`(널 연산자) · `KOTLIN_1_5`(반환 타입).
3. **`runCatching` 은 `Throwable` 전부를 잡는다** — `catch (e: Exception)` 이 놓치는 `Error` 둘(`TODO()`·`AssertionError`)까지.
4. **`map` 안의 예외는 밖으로 샌다** — 담으려면 `mapCatching`.
5. `Result` 는 JVM 에서 **`Object`** 로 다니고, 받는 함수의 이름은 **뭉개지지 않는다**(이 판의 관찰).

## 관련 자료

- [34번 주제](../34-exceptions-nothing-and-try-expression/) — ★★★ **선행.** 검사 예외 없음 · `@Throws` · `Nothing`. 그쪽은 **예외를 던지는 문법**, 여기는 **예외를 값으로 싸는 API**.
- [`../../언어-특성/README.md`](../../언어-특성/README.md) §8 — 「`kotlin.Result`·`runCatching` 도 같은 자리를 노리지만 **컴파일러가 강제하지 않는 관용구**」. 논지는 거기다.
- [26번 주제](../26-value-class-and-boxing/) — `value class` 의 이름 뭉개기·박싱. 여기의 (3)은 그 규칙에서 `Result` 가 벗어나는 자리다.
- [Rust 22번](../../../rust/syntax/22-result-question-mark-and-from/) — `Result<T, E>` — **에러의 타입이 서명에 적히고** `?` 로 전파한다. Kotlin `Result<T>` 에는 `E` 가 없다.
- [Go 23번](../../../go/syntax/23-error-interface-and-errors-as-values/) — `(값, error)` 다중 반환 — 호출자가 **매번 `if err != nil`** 로 연다. Kotlin 은 상자를 열지 않아도 컴파일된다.
- [목록의 **51번 주제**](../51-preconditions-require-check-error-todo/)(`require`/`check`/`error`/`TODO`) · **53번 주제**(구조적 동시성 — 취소가 삼켜지면).

## 용어 풀이

> **`Result<T>`** — 성공 값 `T` 또는 실패 `Throwable` 하나를 담는 `value class`.\
> 예: `runCatching { "x".toInt() }` → `Failure(java.lang.NumberFormatException: For input string: "x")`.

> **`runCatching`** — 블록을 실행하고, 무엇이 던져지든(`Throwable`) `Result` 로 돌려주는 함수.

> **`Error` 대 `Exception`** — JVM 의 `Throwable` 아래 두 갈래. `Error` 는 「보통 잡지 않는 심각한 상태」로 분류된다(`AssertionError`·`OutOfMemoryError`·Kotlin 의 `NotImplementedError`).

> **`mapCatching`** — `map` 과 같되 변환 람다의 예외를 **실패로 담는다.**

> **언어 기능 게이트** — 컴파일러가 기능마다 「몇 판부터 켜지나」를 적어 둔 표(`LanguageFeature`). `-language-version` 이 그 표를 고른다.

> **이름 뭉개기(mangling)** — `value class` 를 받는 함수의 JVM 이름에 `-해시` 를 붙여 겹침을 피하는 것([26번 주제](../26-value-class-and-boxing/)).

## 더 들어가면

- **`Result` 가 이름 뭉개기에서 빠지는 까닭** — stdlib 쪽 표지인지 컴파일러의 특별 취급인지 **확인하지 않았다.** `javap -v` 로 메타데이터를 읽으면 단서가 있을 수 있다.
- **K2 의 `Result` 검사** — `org.jetbrains.kotlin.fir` 아래에 같은 진단이 있는지 컴파일러 jar 를 더 뒤지면 알 수 있다. 이 판에서는 K1 계열 셋만 읽었다.
- **`recoverCatching`·`onSuccess`·`onFailure`** — 선언은 읽었고 돌리지 않았다.
