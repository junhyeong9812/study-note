# kotlin/syntax/49 — `Result` 와 `runCatching` — 예외를 값으로 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `java`·`javap` 에서 실제로 얻었다.
> ★★ 아래 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적은 자리가 없다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **열 자리 × 다섯 판이 전부 `ok` — 0 / 50** · 대조 칸 `lateinit` 만 다섯 판 모두 `'lateinit' modifier is not allowed on properties of inline class types.` · 종료 코드는 판마다 **1**(그 칸 때문)

**출력**

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

**왜 그런가**

- ★★★ 반환 타입·프로퍼티·널 가능·컬렉션 원소·인자·`?.`·`!!`·`?:`·추상 멤버·`suspend` — 1.5 에서 풀린 제한이 2.0\~2.4 어디에도 없다.
- ★★ 대조 칸이 막혔다는 것이 **격자가 막힘을 볼 수 있다**는 증거다 — `lateinit` 금지는 `Result` 가 아니라 **`value class` 타입 전체**의 규칙이다.

### 2. **`error: language version 1.9 is no longer supported; use version 2.0 or greater instead.`** (`exit 1`)

**출력**

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

```text
===== kotlinc -language-version 1.9 ret49.kt -d o49x =====
error: language version 1.9 is no longer supported; use version 2.0 or greater instead.
(exit 1)
```

**왜 그런가**

- ★★ 이 판의 컴파일러는 2.0 아래 **언어 판을 흉내 내지 않는다** — 제한이 있던 판(1.3·1.4)을 직접 던지는 길이 없다. 그래서 7번의 창으로 바꾼다.

### 3. ★★ `make()`·`getKept()` 는 **`java.lang.Object`** · **`take(java.lang.Object)`**(안 뭉개짐) · **`takeId-tmnojjU(int)`**(뭉개짐) · `makeId()` 는 `int` · `many()` 는 `List<kotlin.Result<java.lang.Integer>>` · `box-impl` 은 **`many`** 에

**출력**

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

**왜 그런가**

- ★★★ `Result` 는 `value class` 라 알맹이(`Object`)만 다닌다 — 반환·필드·인자 모두 `Object`.
- ★★★ 그런데 **사용자 `value class` 를 받는 `takeId` 만 이름이 뭉개졌다** — `Result` 를 받는 `take` 는 그대로다. [26번 주제](../26-value-class-and-boxing/)의 규칙에서 `Result` 가 빠진다(이 판의 관찰 · 까닭은 확인하지 않았다).
- ★ 제네릭 자리(`List<Result<Int>>`)에 넣으면 `box-impl` 로 **포장 객체**가 생긴다.

### 4. ★★★ `runCatching` 은 **다섯 다 `failure`** · `catch (e: Exception)` 은 **`TODO()`·`AssertionError` 를 놓친다(`escaped`)** · `is Exception` 은 그 둘만 `false` · **2 / 5**

**출력**

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

**왜 그런가**

- ★★★ `runCatching` 은 `catch (e: Throwable)` — `Error` 까지 잡는다. `NotImplementedError`·`AssertionError` 는 `Error` 쪽이라 `catch (e: Exception)` 을 지나 **밖으로 샌다.**
- ★★ `CancellationException` 은 `Exception` 이라 두 쪽 다 잡는다 — 「`runCatching` 만의 문제」가 아니다.

### 5. ★★ `1 Success(21) | Failure(…NumberFormatException…)` · `4 Success(42) | Failure(…)` · `6 Success(0) | Success(21)` · `7 Failure(…IllegalStateException: too small)` · ★★★ **`8 -> IllegalStateException: too small`**(밖으로 샜다) · `9 -> NumberFormatException`

**출력**

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

**왜 그런가**

- ★★★ `8` 은 `try` 바깥의 `catch` 갈래가 찍었다 — `map` 은 람다의 예외를 **다시 던진다.** 같은 람다를 `mapCatching` 에 주면 `7` 처럼 **`Failure`** 가 된다.
- ★★ `getOrThrow` 는 담긴 예외를 **원래 타입 그대로** 던진다(`9`). `recover` 는 실패만 바꾸고 성공은 그대로 둔다(`6`).

### 6. ★ `[8080] ok 8080` · `[ 443 ] ok 443` · `[http] fail NumberFormatException: …` · `[70000] fail IllegalArgumentException: port out of range: 70000` · `all [Success(80), Failure(…), Success(22)]` · `valid [80, 22]`

**출력**

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

**왜 그런가**

- ★ `require` 가 던진 `IllegalArgumentException` 도 `runCatching` 이 담았다 — 검사 실패와 파싱 실패가 **같은 `Failure`** 로 온다. 둘을 **타입으로** 가르려면 `exceptionOrNull()` 의 클래스를 봐야 한다.
- ★ `List<Result<Int>>` 를 `mapNotNull { it.getOrNull() }` 로 걸러 성공만 모았다.

### 7. **컴파일러 jar 의 `LanguageFeature` 표** — `AllowNullOperatorsForResultAndResultReturnTypeByDefault` 가 **`KOTLIN_1_5`** · 널 연산자만 푸는 `AllowNullOperatorsForResult` 가 **`KOTLIN_1_4`** · 옛 진단 문구 둘 · ★ 못 보는 것 — **설계 이유**와 **K2 쪽 검사**

**출력**

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

**왜 그런가**

- ★★★ 컴파일러는 기능마다 「몇 판부터」를 **표로** 들고 있고 `-language-version` 이 그 표를 고른다 — 그 표를 `javap` 로 읽으면 1.4 컴파일러 없이도 **판 경계**가 보인다. 검사기 `ResultClassInReturnTypeChecker` 는 그 기능을 묻고 없을 때 `RESULT_CLASS_IN_RETURN_TYPE` 을 낸다.
- ★★ 이 창은 **「무엇이 몇 판에 풀렸나」** 까지다 — 「왜 막아 두었나」의 논의는 KEEP 에 있고 **열지 못했다.** 그리고 읽은 셋은 K1 계열 클래스다 — K2 가 같은 검사를 어디에 두는지는 못 봤다.

### 8. **KDoc 계약이다** — 「`catching any [Throwable] exception`」 · `TODO()` 의 `NotImplementedError` 가 **`Failure` 로 조용히 흘러간다**

**왜 그런가**

- ★★★ 2-summary (5)의 발췌 — KDoc 이 `Throwable` 을 적고, 구현도 `catch (e: Throwable)` 하나다.
- ★★ 「아직 안 만든 코드」는 원래 **크게 터져야** 할 자리다. `runCatching` 안에서는 `fold` 의 실패 갈래로 가서 **기본값이 찍히고 끝날** 수 있다.

### 9. `map` 은 **변환만** 하는 함수라 람다를 **`try` 로 감싸지 않는다** — KDoc 「`Note, that this function rethrows any [Throwable] exception thrown by [transform] function. See [mapCatching] for an alternative that encapsulates exceptions.`」

**왜 그런가**

- ★★ `Result` 사슬이라는 이유로 「모든 예외가 담긴다」고 기대하면 틀린다 — 담는 것은 `runCatching` 과 **`…Catching` 꼴**뿐이다. `recover`·`fold` 의 람다도 같은 규칙이다(KDoc 「`rethrows`」).

### 10. Rust 는 **서명이 에러 타입 `E` 를 말한다** · Go 는 **서명이 `error` 를 말하고** 호출자가 매번 연다 · Kotlin `Result<T>` 는 **실패가 언제나 `Throwable`** 이고 **열지 않아도** 컴파일된다

**왜 그런가**

- ★★ [Rust 22번](../../../rust/syntax/22-result-question-mark-and-from/)과 [Go 23번](../../../go/syntax/23-error-interface-and-errors-as-values/)이 각 언어의 정본이다 — 이 문서는 두 언어를 **다시 돌리지 않았다.**
- ★★ Kotlin 은 검사 예외도 없고([34번 주제](../34-exceptions-nothing-and-try-expression/)) `Result` 를 열라는 강제도 없다 — [`../../언어-특성/README.md`](../../언어-특성/README.md) §8 의 「**컴파일러가 강제하지 않는 관용구**」가 이 뜻이다.

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
===== python3 --version =====
Python 3.12.3
(exit 0)
```

★ **흔들리는 칸과 안 흔들리는 칸**

| 흔들린다 | 안 흔들린다 |
|---|---|
| **없다** — 해시코드·주소·시간·스택 트레이스를 찍지 않았다 | 판별 격자 11행 × 5판 · 막힌 칸 수 · 진단 문구 · 실행 출력 |
| | `javap` 출력 — 뭉개진 이름의 해시 글자까지(판이 바뀌면 달라질 수 있어 **모양**만 근거로 쓴다) |
| | 컴파일러·stdlib 소스 발췌 · 모든 **종료 코드** |

> 근거 — 캡처 스크립트를 처음부터 다시 돌려 **블록 전체를 대조**했다.
>
> 실측 — `capture.sh blocks` 와 `capture.sh blocks-recheck` 를 처음부터 따로 돌려 `normalize-shaky.py` 로 대조했다 —\
> **블록 71개 · 동일 71 · 흔들린 칸 0 · ★고칠 것 0**(46\~49 네 주제를 한 캡처로 받았다). 추가한 정규화 규칙은 **없다**.

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `ret49.kt` · `grid49.py` | ★★★ 반환 타입 판별 — 자리 10 + 대조 1 × 판 5 | 스크립트가 `kotlinc -language-version` 을 판마다 부르고 진단을 줄마다 읽는다 |
| `ret49.kt` | 2.0 아래 판 | `kotlinc -language-version 1.9`(거부가 결과) |
| `kotlin-compiler.jar` 의 세 클래스 | ★★★ 옛 진단 문구 · 기능 게이트 판 · 검사기 | `unzip` → `javap -c -p`(전부 받은 뒤 `grep`) |
| `val49.kt` · `kotlin.Result` | ★★ `Object` 로 다니기 · 이름 뭉개기 · `box-impl` | `kotlinc` → `java` → `javap -p`·`javap -c -p` |
| `catch49.kt` | ★★★ 잡기 격자 — 던지기 5 × 잡기 2 | `kotlinc` → `java` |
| `chain49.kt` | ★★ `map` 대 `mapCatching` · `recover` · `fold` · `getOrThrow` | `kotlinc` → `java` |
| `Result.kt`(stdlib 소스 jar) | 선언 · `runCatching` · `map`·`mapCatching` KDoc | `unzip` → `sed -n` |
| `form49.kt` | 형태 한 벌 | `kotlinc` → `java` |

**구현 의존 항목** — 진단 문구 · 검사기 클래스 · `take(Object)` 가 안 뭉개지는 것 · `box-impl` 위치 — 이 컴파일러 판의 산출물이다.\
반면 **1.5+ 의 반환 타입 허용**(언어 판 규칙) · **`runCatching` 의 `Throwable`** · **`map` 의 재던짐** 은 **계약**이다.

**★ 던져 봤더니 예상과 달랐던 것 — 세 건**

1. ★★★ **`Result` 를 받는 함수 이름이 뭉개지지 않았다** — 같은 파일의 사용자 `value class` 는 `-tmnojjU` 가 붙었다. `Result` 는 이름 뭉개기 규칙의 **예외**다.
2. ★★ **컴파일러 jar 에 옛 제한의 문구와 판 게이트가 그대로 남아 있었다** — 1.4 컴파일러 없이 판 경계를 읽을 수 있었다.
3. ★ **`CancellationException` 은 `catch (e: Exception)` 도 잡았다** — 「`runCatching` 이 취소를 삼킨다」의 진짜 대비는 `Exception` 이 아니라 **「취소는 다시 던져야 한다」는 규칙** 쪽이다(53번 주제).
