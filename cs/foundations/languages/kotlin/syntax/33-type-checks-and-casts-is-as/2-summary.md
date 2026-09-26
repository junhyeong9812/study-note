# kotlin/syntax/33 — 타입 검사·캐스트: `is`/`as`/`as?` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Type checks and casts](https://kotlinlang.org/docs/typecasts.html)(`as` 실패는 `ClassCastException` · `as?` 는 `null` · `as String?` 도 실패하면 예외 · 스마트 캐스트의 전제 표) · [Generics — Type erasure and generic type checks](https://kotlinlang.org/docs/generics.html#type-erasure).
> **실행 검증** — 이 문서의 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javac`·`javap` 에서 실제로 얻었다. C# 은 **.NET SDK 10.0.401** 의 Roslyn `csc` 를 직접 불렀다.\
> `kotlinc` 11회(에러 줄을 세는 2회 포함 · 컴파일 실패 3벌 · 경고 2벌) · `java` 5회 · `javac` 1회 · `javap` 3회 · `csc` 2회(실패 1벌) · `dotnet` 1회.\
> ★★ 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적지 않았다. 소스 펜스의 첫 줄 배너도 캡처가 찍었다.
> **버전** — `is`/`as`/`as?` 와 스마트 캐스트는 1.0. 이 문서의 **스마트 캐스트 통과 범위와 진단 문구는 K2(2.4.20)** 의 것이다.
> **경계** — ★★ **스마트 캐스트가 깨지는 자리 아홉**(`null` 검사 기준)은 [04번 주제](../04-smart-casts/) (2)가 정본이다 — 여기는 **`is` 로 물었을 때 같은 자리가 어떻게 답하나**와 `as` 뒤·`||` 같은 **새 자리**만 더한다((5)).\
> 소거를 **뚫는** 방법(`reified`)은 [12번 주제](../12-reified-type-parameters/)가, 플랫폼 타입 일반은 [05번 주제](../05-platform-types/)가, 별칭이 새 타입이 아니라는 것은 [29번 주제](../29-type-aliases-and-nested-type-aliases/)가 정본이다.
> **대비** — Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **22번**([`22-instanceof-type-patterns/`](../../../java/syntax/22-instanceof-type-patterns/)) — `instanceof` 패턴 변수가 Kotlin 스마트 캐스트의 **Java 쪽 짝**이다.\
> C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **21번**(패턴 매칭)은 아직 폴더가 없다 — ★ C# 의 `is`/`as` 는 **이 문서가 직접 던졌다**((8)).
> 이 본문은 Claude 작성이다(원고 없음).

★ **본체는 첫째 창이다** — 「**`javap -c` 가 `is`·`as`·`as?` 자리에 박은 명령**」(`instanceof`·`checkcast`·`Intrinsics.checkNotNull`). 세 연산자의 **실패 방식이 다른 이유**가 명령 몇 줄에 다 있다.

## 이 주제가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **언어 보장** | 명세·공식 문서가 약속한 것 | ★★★ `is` 는 검사 · `as` 는 실패하면 **예외** · `as?` 는 실패하면 **`null`** · **소거된 타입 인자는 검사 못 한다** · 스마트 캐스트의 전제(안정 값) |
| **구현(JVM 백엔드)** | kotlinc 가 JVM 으로 내리는 방식 | `is` → **`instanceof`** · `as` → **`checkcast`** · ★★ `null as String` 이 **`NullPointerException`** 인 것((1)) · 별칭 검사가 `instanceof String` 인 것 |
| **이 판의 관찰** | kotlinc 2.4.20 에서 이번에 본 것 | 진단 문구 · 「`cast is redundant`」 · ★ `is` 로 물었을 때의 스마트 캐스트 **통과·차단 목록**((5)) |

## 이 판

```text
===== kotlinc -version =====
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | (이 주제에는 없다) | 해시코드·주소·시간을 **하나도 안 찍었다** — 예외는 `toString()` 과 **클래스 이름**만 찍었다 |
| 안 흔들린다 | 출력 — 예외 **메시지 전문** 포함(`… are in module java.base of loader 'bootstrap')`) | JDK 판이 같으면 같다. ★ 메시지 **문구**는 JDK 판에 매인다 |
| 안 흔들린다 | `javap` 출력 · 진단의 **문구·`파일:줄:칸`·캐럿** · 「물은 함수 N · error 줄 M」 | 결정적이다 |
| 안 흔들린다 | `csc` 진단 `CS0077` · `dotnet` 출력 | 결정적이다 |

★ 근거 — 캡처 스크립트를 처음부터 두 번 돌려 **블록 전체를 바이트 단위로 대조**했다(수치는 3-answer 의 「실행 검증」).

## 한눈에 — 쉽게 말하면

**`is` 는 「신분증을 보는 것」, `as` 는 「이 사람은 ○○다」라고 선언하고 들여보내는 것, `as?` 는 「○○면 들여보내고 아니면 빈자리」다.**
선언이 틀리면 `as` 는 **그 자리에서 경보**(`ClassCastException`)를 울리고, `as?` 는 **조용히 `null`** 을 준다.

그리고 **캐스트는 변환이 아니다** — `1` 을 `Long` 이라고 선언해도 `1L` 이 되지 않는다. 경보가 울릴 뿐이다.

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 신분증 보기 | `x is String` → `instanceof` | (1) |
| 선언하고 들여보내기 | `x as String` → `checkcast` · 틀리면 `ClassCastException` | (1) |
| 빈손으로 선언 | ★ `null as String` → **`NullPointerException`** | (1) |
| ○○면 들여보내고 아니면 빈자리 | `x as? String` → `instanceof` 후 `null` | (1) |
| 신분증의 **국적란이 지워져 있다** | 소거 — `is List<String>` 을 **못 한다** | (2) |
| 선언을 **믿고** 들여보냈는데 안에서 문제 | 비검사 캐스트 — **쓰는 자리**에서 터진다 | (3) |
| 원화를 달러라고 선언하기 | `1 as Long` — **변환이 아니라 경보** | (4) |
| 확인한 뒤 다시 안 묻기 | 스마트 캐스트 · 안 되는 자리 | (5) |

```text
   x is String         aload x ; instanceof String                        -> true/false
   x as? String        instanceof String ; ifeq -> null ; checkcast String -> String 또는 null
   x as String?        checkcast String                                   -> null 은 통과, 딴 타입은 CCE
   x as String         Intrinsics.checkNotNull(x, "null cannot be cast …") ; checkcast String
                         null   -> NullPointerException
                         딴 타입 -> ClassCastException
```

## 이 주제가 답하려는 질문

1. `is`·`as`·`as?` 는 **무엇으로 번역되고**, 실패하면 각각 **무엇이** 나오나 — `null` 일 때는.
2. **무엇을 검사할 수 없나** — 제네릭 타입 인자, 그리고 그것을 억지로 캐스트하면 **어디서** 터지나.
3. `is` 뒤의 스마트 캐스트는 **어디서 안 되나** — 04번이 `null` 로 본 자리를 `is` 로 물으면.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **`javap -c`** | `instanceof`·`checkcast`·`checkNotNull` — 실패 방식의 **정체**((1)(6)(7)) | ★ **본체 창** |
| ★★ **실행 출력 — 예외 전문** | 어느 예외가 **어떤 메시지로** 나오나((1)(3)(4)(6)) | 이 갈래의 기본 창 |
| ★★ **컴파일 진단 + 세기** | 소거 검사·스마트 캐스트 차단 — 「**물은 함수 N · error 줄 M**」을 스크립트가 센다((2)(5)) | 이 갈래의 기본 창 · 규칙 18-A |
| ★ **모듈 나눠 컴파일** | 다른 모듈의 프로퍼티((5)) | [04번 주제](../04-smart-casts/)의 창 |
| ★ **C# 로 같은 모양** | `as` 가 **Kotlin `as?` 와 같은** 언어((8)) | ★ 이 주제의 고유 창 |
| **부적용 — 실행 시간** | 「`as?` 가 `as` 보다 느리다」는 주장은 **범위 밖**이다 — 명령 **개수**만 센다((1)) | — |

★★ **「물은 곳 N · 답한 곳 M」을 스크립트가 찍는다** — 스마트 캐스트 절((5))은 **통과한 함수가 결론의 절반**이다. 에러 목록만 보면 **안 물어본 것과 물었는데 통과한 것**이 구분되지 않으므로 `grep -c` 로 **물은 함수 수**와 **에러 줄 수**를 같이 찍었다.

### (1) ★★★ 네 연산자의 번역 — 그리고 `null` 이 들어올 때

**언제 쓰나** — 「`as` 와 `as?` 는 무엇이 다른가」를 **명령**으로 볼 때.

```kotlin
// castforms.kt
fun c1(x: Any?) = x is String
fun c2(x: Any?) = x !is String
fun c3(x: Any?) = x as String
fun c4(x: Any?) = x as? String
fun c5(x: Any?) = x as String?
fun c6(x: Any?) = if (x is String) x.length else -1

fun main() {
    println("A ${c1("s")} ${c1(null)} ${c2(1)}")
    println("B ${c4(1)} ${c5(null)} ${c6("abc")}")
    println("C " + runCatching { c3(1) }.exceptionOrNull())
    println("D " + runCatching { c3(null) }.exceptionOrNull())
}
```

```text
===== kotlinc castforms.kt -d o33c =====
(exit 0)
===== java -cp o33c:kotlin-stdlib.jar CastformsKt =====
A true false true
B null null 3
C java.lang.ClassCastException: class java.lang.Integer cannot be cast to class java.lang.String (java.lang.Integer and java.lang.String are in module java.base of loader 'bootstrap')
D java.lang.NullPointerException: null cannot be cast to non-null type kotlin.String
(exit 0)
```

```text
===== javap -c -p o33c/CastformsKt.class | awk '/ c[0-9]\(/,/^$/' =====
  public static final boolean c1(java.lang.Object);
    Code:
       0: aload_0
       1: instanceof    #9                  // class java/lang/String
       4: ireturn

  public static final boolean c2(java.lang.Object);
    Code:
       0: aload_0
       1: instanceof    #9                  // class java/lang/String
       4: ifne          11
       7: iconst_1
       8: goto          12
      11: iconst_0
      12: ireturn

  public static final java.lang.String c3(java.lang.Object);
    Code:
       0: aload_0
       1: ldc           #17                 // String null cannot be cast to non-null type kotlin.String
       3: invokestatic  #23                 // Method kotlin/jvm/internal/Intrinsics.checkNotNull:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_0
       7: checkcast     #9                  // class java/lang/String
      10: areturn

  public static final java.lang.String c4(java.lang.Object);
    Code:
       0: aload_0
       1: instanceof    #9                  // class java/lang/String
       4: ifeq          14
       7: aload_0
       8: checkcast     #9                  // class java/lang/String
      11: goto          15
      14: aconst_null
      15: areturn

  public static final java.lang.String c5(java.lang.Object);
    Code:
       0: aload_0
       1: checkcast     #9                  // class java/lang/String
       4: areturn

  public static final int c6(java.lang.Object);
    Code:
       0: aload_0
       1: instanceof    #9                  // class java/lang/String
       4: ifeq          17
       7: aload_0
       8: checkcast     #9                  // class java/lang/String
      11: invokevirtual #31                 // Method java/lang/String.length:()I
      14: goto          18
      17: iconst_m1
      18: ireturn
(exit 0)
```

| 함수 | 식 | 명령 | 실패하면 |
|---|---|---|---|
| `c1` | `x is String` | ★ **`instanceof` 하나** | `false`(`null` 도 `false`) |
| `c2` | `x !is String` | `instanceof` + `ifne` | — |
| `c3` | `x as String` | ★★ **`Intrinsics.checkNotNull` + `checkcast`** | 딴 타입 → **`ClassCastException`** · ★★ `null` → **`NullPointerException`** |
| `c4` | `x as? String` | ★★ **`instanceof` → `ifeq` → `aconst_null`** · 맞으면 `checkcast` | **`null`** |
| `c5` | `x as String?` | ★ **`checkcast` 하나** | `null` 은 통과 · 딴 타입은 `ClassCastException` |
| `c6` | `if (x is String) x.length` | `instanceof` → `checkcast` → `String.length` | — |

- ★★★ **`D java.lang.NullPointerException: null cannot be cast to non-null type kotlin.String`** — `null as String` 은 **`ClassCastException` 이 아니다.** JVM 의 `checkcast` 는 **`null` 을 그냥 통과시키므로**, kotlinc 가 그 앞에 **`Intrinsics.checkNotNull(x, "null cannot be cast …")`** 을 따로 심었다(`c3` 의 1·3번 오프셋). 메시지 문자열이 **상수 풀에 그대로** 있다.
- ★★ `c5`(`as String?`)에는 그 검사가 **없다** — `null` 을 허용하는 타입이니 `checkcast` 만 남았다. 출력 `B` 의 둘째 칸 `null` 이 그것이다.
- ★★ `c4`(`as?`)는 **먼저 `instanceof` 로 묻고** 아니면 `aconst_null` 이다 — 예외 경로가 **아예 없다.** `B` 의 첫 칸 `null` 이 `c4(1)` 이다.
- ★ `c6` — `is` 뒤 스마트 캐스트도 바이트코드에서는 **`checkcast` 한 번**이다. 「캐스트를 안 적어도 된다」는 것이지 **캐스트가 없어지는 것은 아니다.**
- ★ `C` 줄의 메시지 전문(`class java.lang.Integer cannot be cast to class java.lang.String (… loader 'bootstrap')`)은 **JVM 이 만든 문장**이다 — Kotlin 이 아니다.

### (2) ★★ 소거된 제네릭 — 물을 수 없는 것

**언제 쓰나** — `x is List<String>` 을 쓰고 싶을 때.

```kotlin
// erase.kt
fun f1(x: Any) = x is List<String>
fun f2(x: Any) = x is List<*>
fun f3(x: List<Any>) = x is List<String>
fun f4(x: Collection<String>) = x is List<String>
fun <T> f5(x: Any) = x is T
```

```text
===== kotlinc erase.kt -d o33e =====
erase.kt:1:23: error: cannot check for instance of erased type 'List<String>'.
fun f1(x: Any) = x is List<String>
                      ^^^^^^^^^^^^
erase.kt:3:29: error: cannot check for instance of erased type 'List<String>'.
fun f3(x: List<Any>) = x is List<String>
                            ^^^^^^^^^^^^
erase.kt:5:27: error: cannot check for instance of erased type 'T (of fun <T> f5)'.
fun <T> f5(x: Any) = x is T
                          ^
(exit 1)
===== echo "물은 함수 $(grep -c '^fun ' erase.kt) · error 줄 $(kotlinc erase.kt -d o33e2 2>&1 | grep -c ': error:')" =====
물은 함수 5 · error 줄 3
(exit 0)
```

- ★★★ **물은 함수 5 · 에러 줄 3.** 막힌 셋은 전부 「`cannot check for instance of erased type …`」 — `f1`(`Any is List<String>`) · `f3`(`List<Any> is List<String>`) · `f5`(`is T`).
- ★★ **통과한 둘이 결론의 절반이다** — `f2` 의 **`is List<*>`**(타입 인자를 **묻지 않는다**)와 `f4` 의 **`Collection<String> is List<String>`**. 뒤쪽은 **정적 타입이 이미 `String` 을 알려 주므로** 남은 질문이 「`List` 인가」뿐이라 된다.
- ★ `f5` 의 `is T` 는 [12번 주제](../12-reified-type-parameters/) (1)이 같은 문구로 봤다 — 그것을 푸는 것이 **`inline` + `reified`** 다.

### (3) ★★ 비검사 캐스트 — **쓰는 자리**에서 터진다

**언제 쓰나** — `raw as List<String>` 처럼 소거된 타입으로 **캐스트**할 때.

```kotlin
// unchk.kt
fun main() {
    val raw: Any = listOf(1, 2)
    val xs = raw as List<String>
    println("A ${xs.size}")
    println("B " + runCatching { xs[0].length }.exceptionOrNull())
    val n: Any = 1
    println("C " + runCatching { n as Long }.exceptionOrNull())
    println("D ${(n as Int).toLong()}")
    val m = 1
    println("E " + runCatching { m as Long }.exceptionOrNull())
}
```

```text
===== kotlinc unchk.kt -d o33u =====
unchk.kt:3:18: warning: unchecked cast of 'Any' to 'List<String>'.
    val xs = raw as List<String>
                 ^^^^^^^^^^^^^^^
unchk.kt:10:36: warning: this cast can never succeed. Use 'toLong' to perform numeric conversion.
    println("E " + runCatching { m as Long }.exceptionOrNull())
                                   ^^^^^^^
(exit 0)
===== java -cp o33u:kotlin-stdlib.jar UnchkKt =====
A 2
B java.lang.ClassCastException: class java.lang.Integer cannot be cast to class java.lang.String (java.lang.Integer and java.lang.String are in module java.base of loader 'bootstrap')
C java.lang.ClassCastException: class java.lang.Integer cannot be cast to class java.lang.Long (java.lang.Integer and java.lang.Long are in module java.base of loader 'bootstrap')
D 1
E java.lang.ClassCastException: class java.lang.Integer cannot be cast to class java.lang.Long (java.lang.Integer and java.lang.Long are in module java.base of loader 'bootstrap')
(exit 0)
```

- ★★★ **3번째 줄은 경고**(「`unchecked cast of 'Any' to 'List<String>'.`」)**뿐이고 실행도 통과한다** — `A 2`. 런타임 `checkcast` 는 **`List` 까지만** 확인할 수 있다.
- ★★★ **터진 것은 5번째 줄**이다 — `xs[0].length` 에서 `Integer cannot be cast to String`. 캐스트한 **자리가 아니라** 원소를 `String` 으로 **꺼내 쓰는 자리**다. 둘 사이가 멀수록 원인을 찾기 어렵다.

### (4) ★★ 캐스트는 변환이 아니다 — `1 as Long`

같은 파일의 `C`·`D`·`E` 줄이다.

- ★★★ **`C`** — `Any` 에 담긴 `1` 을 `as Long` 하니 **`Integer cannot be cast to class java.lang.Long`**. 박스 안의 것은 **`Integer`** 이고, 캐스트는 **상자의 종류를 바꾸지 않는다.**
- ★★ **`E`** — 정적 타입이 `Int` 이면 컴파일러가 먼저 말한다: 「`this cast can never succeed. Use 'toLong' to perform numeric conversion.`」(10번째 줄). `Any` 인 `C` 에는 **경고가 없다** — 정적 타입이 답을 모르기 때문이다.
- ★ **`D 1`** — 변환은 **`toLong()`** 이다. `(n as Int).toLong()` 처럼 **캐스트로 꺼내고 함수로 바꾼다.** 「암묵 수치 변환이 없다」는 [01번 주제](../01-val-var-and-basic-types/)와 같은 뿌리다.

### (5) ★★★ `is` 뒤 스마트 캐스트 — 되는 자리와 안 되는 자리

**언제 쓰나** — `if (x is String)` 안에서 `x.length` 가 거부될 때. [04번 주제](../04-smart-casts/) (2)가 **`!= null`** 로 아홉 자리를 봤다. 여기서는 **`is`** 로 묻고, `as` 뒤·`||` 같은 자리를 더했다.

```kotlin
// scast.kt
class H1 { var v: Any = "x" }
class H2 { val v: Any get() = "x" }
open class H3 { open val v: Any = "x" }
class H4 { val v: Any = "x" }

fun t1(h: H1) { if (h.v is String) println(h.v.length) }
fun t2(h: H2) { if (h.v is String) println(h.v.length) }
fun t3(h: H3) { if (h.v is String) println(h.v.length) }
fun t4(h: H4) { if (h.v is String) println(h.v.length) }
fun t5(x: Any) { var y = x; val r = { y = 1 }; if (y is String) println(y.length); r() }
fun t6(x: Any) { if (x is String) println(x.length) }
fun t7(x: Any) { x as String; println(x.length) }
fun t8(x: Any) { if (x !is String) return; println(x.length) }
fun t9(x: Any) = when (x) { is String -> x.length; is Int -> x + 1; else -> 0 }
fun t10(x: Any) { if (x is String && x.length > 0) println(x.length) }
fun t11(x: Any) { if (x is String || x.length > 0) println(0) }
```

```text
===== kotlinc scast.kt -d o33s =====
scast.kt:6:44: error: smart cast to 'String' is impossible, because 'v' is a mutable property that could be mutated concurrently.
fun t1(h: H1) { if (h.v is String) println(h.v.length) }
                                           ^^^
scast.kt:7:44: error: smart cast to 'String' is impossible, because 'v' is a property that has an open or custom getter.
fun t2(h: H2) { if (h.v is String) println(h.v.length) }
                                           ^^^
scast.kt:8:44: error: smart cast to 'String' is impossible, because 'v' is a property that has an open or custom getter.
fun t3(h: H3) { if (h.v is String) println(h.v.length) }
                                           ^^^
scast.kt:10:75: error: unresolved reference 'length' on receiver of type 'Any'.
fun t5(x: Any) { var y = x; val r = { y = 1 }; if (y is String) println(y.length); r() }
                                                                          ^^^^^^
scast.kt:16:40: error: unresolved reference 'length' on receiver of type 'Any'.
fun t11(x: Any) { if (x is String || x.length > 0) println(0) }
                                       ^^^^^^
(exit 1)
===== echo "물은 함수 $(grep -c '^fun t' scast.kt) · error 줄 $(kotlinc scast.kt -d o33s2 2>&1 | grep -c ': error:')" =====
물은 함수 11 · error 줄 5
(exit 0)
```

**다른 모듈** — `lib33.kt` 를 따로 컴파일하고 그 결과를 클래스패스로 준 채 `use33.kt` 를 컴파일했다.

```kotlin
// lib33.kt
class Far { val v: Any = "x" }
open class FarOpen { open val v: Any = "x" }
```

```kotlin
// use33.kt
fun u1(f: Far) { if (f.v is String) println(f.v.length) }
fun u2(f: FarOpen) { if (f.v is String) println(f.v.length) }
```

```text
===== kotlinc mA/lib33.kt -d o33mA =====
(exit 0)
===== kotlinc -cp o33mA mB/use33.kt -d o33mB =====
mB/use33.kt:1:45: error: smart cast to 'String' is impossible, because 'v' is a public API property declared in different module.
fun u1(f: Far) { if (f.v is String) println(f.v.length) }
                                            ^^^
mB/use33.kt:2:49: error: smart cast to 'String' is impossible, because 'v' is a property that has an open or custom getter.
fun u2(f: FarOpen) { if (f.v is String) println(f.v.length) }
                                                ^^^
(exit 1)
```

```text
   if (x is String) { … x.length … }
                          |
            컴파일러가 묻는 것 하나 — 「검사한 x 와 지금의 x 가 같은 값인가」
                          |
     예  로컬 val · 매개변수 · 같은 모듈의 val(getter 없음)        -> String 으로 좁힌다
         as 가 성공한 다음 줄 · !is 후 return 한 다음 · && 오른쪽
     아니오  var 프로퍼티 · 커스텀 getter · open · 다른 모듈         -> 이유를 말하는 문구
            람다가 고치는 지역 var · || 오른쪽                     -> Any 로 본 결과만 말한다
```

- ★★★ **물은 함수 11 · 에러 줄 5**(같은 모듈) + **다른 모듈 2 · 2.**

| 함수 | 자리 | 결과 | 문구 |
|---|---|---|---|
| `t1` | `var` 멤버 프로퍼티 | ★ **막힘** | 「`is a mutable property that could be mutated concurrently.`」 |
| `t2` | 커스텀 getter `val` | ★ **막힘** | 「`is a property that has an open or custom getter.`」 |
| `t3` | `open val` | ★ **막힘** | 같은 문구 |
| `t4` | 같은 모듈의 `val`(getter 없음) | 통과 | — |
| `t5` | ★ **람다가 고쳐 쓰는 지역 `var`** | ★★ **막힘** | ★★ 「`unresolved reference 'length' on receiver of type 'Any'.`」 — **이유를 안 말한다** |
| `t6` | 매개변수 `if (x is String)` | 통과 | — |
| `t7` | ★ **`x as String` 한 줄 뒤** | ★★ **통과** | — (`as` 가 성공했으면 그다음 줄부터 `String`) |
| `t8` | `if (x !is String) return` 뒤 | 통과 | — |
| `t9` | `when (x) { is String -> … }` | 통과 | — |
| `t10` | `x is String && x.length > 0` | 통과 | — |
| `t11` | ★ `x is String \|\| x.length > 0` | ★★ **막힘** | 「`unresolved reference 'length' on receiver of type 'Any'.`」 |
| `u1` | **다른 모듈**의 public `val` | ★ **막힘** | 「`is a public API property declared in different module.`」 |
| `u2` | 다른 모듈의 `open val` | ★ **막힘** | 「`… open or custom getter.`」 |

- ★★ **04번과 같은 문구가 같은 자리에서 나왔다**(`t1`·`t2`·`t3`·`u1`·`u2`) — 스마트 캐스트는 **`null` 검사든 `is` 든 같은 「안정 값」 판정**을 쓴다.
- ★★ **`t5` 는 04번의 9번 자리와 같은 모양**이다 — 이유를 말하는 문구가 아니라 **일반 문구**(04번은 「`only safe (?.) … calls are allowed`」, 여기는 「`unresolved reference … on receiver of type 'Any'`」)가 나온다. 둘 다 「좁혀지지 않았으니 원래 타입으로 봤다」의 결과다.
- ★★ **새 자리 둘** — `t7`(`as` 뒤)은 **통과**한다: 캐스트가 성공해야 다음 줄에 오므로 컴파일러가 그 사실을 쓴다. `t11`(`||`)은 **막힌다**: 오른쪽은 **왼쪽이 거짓일 때** 도므로 `x` 는 `String` 이 **아닐 때** 평가된다.
- ★ Java 로 치면 `t6` 은 `if (x instanceof String s)` 의 **패턴 변수** 자리다 — Java 는 **새 이름**(`s`)을 만들고, Kotlin 은 **같은 이름을 좁힌다**([Java 22번](../../../java/syntax/22-instanceof-type-patterns/)).

### (6) ★★ 플랫폼 타입의 `as` — Java 에서 온 `null`

**언제 쓰나** — Java 메서드가 준 값(`String!`)을 `as String` 으로 「확정」하려 할 때.

```java
// Jsrc.java
public class Jsrc {
    public static String name() { return null; }
    public static Object any() { return 42; }
}
```

```kotlin
// plat.kt
fun main() {
    println("A " + runCatching { Jsrc.name() as String }.exceptionOrNull())
    println("B ${Jsrc.name() as String?} ${Jsrc.name() as? String}")
    println("C " + runCatching { val s: String = Jsrc.name(); s }.exceptionOrNull())
    println("D " + runCatching { Jsrc.any() as String }.exceptionOrNull()?.javaClass?.simpleName)
}
```

```text
===== javac -d o33p Jsrc.java =====
(exit 0)
===== kotlinc -cp o33p plat.kt -d o33p =====
plat.kt:3:30: warning: cast is redundant.
    println("B ${Jsrc.name() as String?} ${Jsrc.name() as? String}")
                             ^^^^^^^^^^
plat.kt:3:56: warning: cast is redundant.
    println("B ${Jsrc.name() as String?} ${Jsrc.name() as? String}")
                                                       ^^^^^^^^^^
(exit 0)
===== java -cp o33p:kotlin-stdlib.jar PlatKt =====
A java.lang.NullPointerException: null cannot be cast to non-null type kotlin.String
B null null
C java.lang.NullPointerException: name(...) must not be null
D ClassCastException
(exit 0)
```

```text
===== javap -c -p o33p/PlatKt.class | grep -E 'instanceof|checkcast|Intrinsics' =====
      26: invokestatic  #39                 // Method kotlin/jvm/internal/Intrinsics.checkNotNull:(Ljava/lang/Object;Ljava/lang/String;)V
      96: instanceof    #78                 // class java/lang/String
     147: invokestatic  #85                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullExpressionValue:(Ljava/lang/Object;Ljava/lang/String;)V
     219: invokestatic  #39                 // Method kotlin/jvm/internal/Intrinsics.checkNotNull:(Ljava/lang/Object;Ljava/lang/String;)V
     222: checkcast     #78                 // class java/lang/String
(exit 0)
```

- ★★★ **`A`** — `Jsrc.name() as String` 은 **`NullPointerException: null cannot be cast to non-null type kotlin.String`**. 바이트코드에는 **`checkcast` 가 없다**(26번 오프셋은 `checkNotNull` 뿐) — `String!` 은 이미 `String` 이니 **남은 일은 `null` 검사 하나**다.
- ★★ **경고 둘** — `as String?` 와 `as? String` 에 「`cast is redundant.`」 플랫폼 타입은 **`String` 과 `String?` 둘 다로** 읽히므로 컴파일러 눈에는 **할 일이 없는 캐스트**다. 그래도 `as? String` 은 **`instanceof`**(96번)를 남겼다.
- ★★ **`C`** — 캐스트 없이 `val s: String = Jsrc.name()` 으로 받으면 **다른 NPE**다: 「`name(...) must not be null`」(`checkNotNullExpressionValue`, 147번). [05번 주제](../05-platform-types/)가 이 검사의 정본이다. **같은 `null` 이 쓴 모양에 따라 다른 메시지**로 터진다.
- ★ **`D ClassCastException`** — `Object` 를 주는 Java 메서드(`any()`)는 `checkNotNull` **+ `checkcast`**(219·222번)이고, `42` 는 `String` 이 아니라 CCE 다.

### (7) ★ 별칭으로 검사하면 — `is UserId` 는 `is String` 이다

```kotlin
// aliascheck.kt
typealias UserId = String

fun isUser(x: Any) = x is UserId
fun isStr(x: Any) = x is String

fun main() {
    println("A ${isUser("u-1")} ${isUser(7)} ${isStr("u-1")}")
}
```

```text
===== kotlinc aliascheck.kt -d o33a =====
(exit 0)
===== java -cp o33a:kotlin-stdlib.jar AliascheckKt =====
A true false true
(exit 0)
===== javap -c -p o33a/AliascheckKt.class | awk '/ is(User|Str)\(/,/^$/' =====
  public static final boolean isUser(java.lang.Object);
    Code:
       0: aload_0
       1: ldc           #9                  // String x
       3: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_0
       7: instanceof    #17                 // class java/lang/String
      10: ireturn

  public static final boolean isStr(java.lang.Object);
    Code:
       0: aload_0
       1: ldc           #9                  // String x
       3: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_0
       7: instanceof    #17                 // class java/lang/String
      10: ireturn
(exit 0)
```

- ★★ **`isUser` 와 `isStr` 의 바이트코드가 한 글자도 같다** — 둘 다 `instanceof java/lang/String`. `A true false true` — `UserId` 로 검사해도 **아무 `String` 이나** 통과한다.
- ★ 별칭이 새 타입이 아니라는 것은 [29번 주제](../29-type-aliases-and-nested-type-aliases/) (1)이 정본이다. 검사로 가르고 싶으면 **`value class`**([26번 주제](../26-value-class-and-boxing/))다.

### (8) ★★ C# — `as` 가 곧 Kotlin 의 `as?` 다

```csharp
// cast33.cs
object o = 42;
var s = o as string;
System.Console.WriteLine($"A {s == null}");
int? n = o as int?;
System.Console.WriteLine($"B {n}");
System.Console.WriteLine($"C {o is string} {o is int k && k > 0}");
try { string t = (string)o; } catch (System.InvalidCastException e) { System.Console.WriteLine("D " + e.GetType().Name); }
```

```csharp
// cast33bad.cs
object o = 42;
int bad = o as int;
```

```text
===== csc -out:cast33.dll cast33.cs =====
(exit 0)
===== dotnet cast33.dll =====
A True
B 42
C False True
D InvalidCastException
(exit 0)
===== csc -out:cast33bad.dll cast33bad.cs =====
cast33bad.cs(2,11): error CS0077: The as operator must be used with a reference type or nullable type ('int' is a non-nullable value type)
(exit 1)
```

| 하는 일 | Kotlin | C# |
|---|---|---|
| 검사 | `x is String` | `o is string` |
| 실패하면 예외인 캐스트 | ★ **`x as String`** | ★ **`(string)o`** — `InvalidCastException`(`D`) |
| 실패하면 `null` 인 캐스트 | ★ **`x as? String`** | ★ **`o as string`** — `A True` |
| 값 타입으로 「없으면 null」 | `x as? Int` (박싱된 `Int?`) | `o as int?` — `B 42` |
| 값 타입에 그냥 `as` | (구분 없음 — `Int` 도 참조로 다룬다) | ★★ **`CS0077`** — 「`The as operator must be used with a reference type or nullable type ('int' is a non-nullable value type)`」 |
| 검사 + 새 이름 | 스마트 캐스트(같은 이름) | `o is int k && k > 0` — 패턴 변수 |

- ★★★ **이름이 어긋난다** — C# 의 `as` 는 **Kotlin 의 `as?`** 이고, Kotlin 의 `as` 는 **C# 의 괄호 캐스트**다. 두 언어를 오가면 `as` 라는 **같은 낱말이 반대 실패 방식**을 뜻한다.
- ★★ `CS0077` — C# 은 `int` 가 **`null` 을 못 담으므로** `as int` 를 **거부**한다. Kotlin 은 `as? Int` 의 결과가 `Int?` 라 **박싱으로** 해결한다.

## 문법 — 형태와 규칙

**형태** — `when` 의 `is` 가지·`as?`·`as` 가 한 프로그램에서 도는 최소 예제다.

```kotlin
// form33.kt
sealed interface Shape
data class Circle(val r: Double) : Shape
data class Rect(val w: Double, val h: Double) : Shape

fun area(s: Any): Double = when (s) {
    is Circle -> 3.0 * s.r * s.r
    is Rect -> s.w * s.h
    else -> -1.0
}

fun main() {
    val xs: List<Any> = listOf(Circle(1.0), Rect(2.0, 3.0), "none")
    println("Z ${xs.map(::area)} ${xs[2] as? Shape} ${(xs[1] as Rect).w}")
}
```

```text
===== kotlinc form33.kt -d o33z =====
(exit 0)
===== java -cp o33z:kotlin-stdlib.jar Form33Kt =====
Z [3.0, 6.0, -1.0] null 2.0
(exit 0)
```

**규칙 불릿**

- `x is T` → `instanceof` · **`null` 은 `false`**((1)).
- `x as T` → 실패하면 **예외** — 딴 타입은 `ClassCastException`, **`null` 은 `NullPointerException`**(JVM 구현)((1)).
- `x as T?` → `null` 은 통과, 딴 타입은 예외((1)).
- `x as? T` → 실패하면 **`null`** — 결과 타입은 `T?`((1)).
- **소거된 타입 인자는 검사 못 한다** — `is List<*>` 로 묻거나 `reified` 로 푼다((2)).
- 소거된 타입으로의 캐스트는 **경고 + 나중에 터진다**((3)).
- **캐스트는 변환이 아니다** — 수는 `toLong()` 등((4)).
- `is` 뒤·`as` 뒤·`!is … return` 뒤·`&&` 오른쪽·`when` 가지에서 **스마트 캐스트**. `var` 프로퍼티·커스텀 getter·`open`·다른 모듈·람다가 고치는 지역 `var`·`||` 오른쪽에서는 **안 된다**((5)).

## 어디서 틀리나

1. ★★★ **`null as String` 이 `ClassCastException` 이라고 믿는다.** 이 판에서는 **`NullPointerException`**((1)) — `catch (e: ClassCastException)` 이 **못 잡는다.**
2. ★★★ **`as` 로 수를 바꾼다.** `1 as Long` 은 **`ClassCastException`**((4)).
3. ★★ **`is List<String>` 을 쓴다.** 「`cannot check for instance of erased type`」((2)).
4. ★★ **비검사 캐스트 경고를 무시한다.** 캐스트한 줄은 통과하고 **원소를 쓰는 줄**에서 터진다((3)).
5. ★★ **`as? ` 로 실패를 삼키고 `null` 을 그냥 흘려보낸다.** 원인이 사라진다 — `?: error(…)` 로 **실패를 되살려라**.
6. ★★ **`x is String || x.length > 0`** 을 쓴다. 오른쪽에서는 **`String` 이 아닐 때** 평가된다((5)).
7. ★ **Java 에서 온 값을 `as String` 으로 「확정」한다.** `null` 이면 NPE 이고, 컴파일러는 `as String?` 을 **redundant** 라 한다((6)).
8. ★ **`is UserId` 로 ID 를 가른다고 믿는다.** `is String` 과 **같은 명령**이다((7)).
9. ★ **C# 습관으로 `as` 를 「실패하면 null」로 쓴다.** Kotlin 에서는 **`as?`** 다((8)).

## 구현 세부사항 대 언어 보장

| 항목 | 어느 쪽인가 | 근거 |
|---|---|---|
| `as` 실패는 **예외**, `as?` 실패는 **`null`** | ★★★ **언어 보장** | (1) |
| 소거된 타입 인자를 **검사할 수 없는** 것 · 비검사 캐스트 **경고** | **언어 보장** | (2)(3) |
| 스마트 캐스트의 **전제**(안정 값) | **언어 보장**(문서의 표) | (5) |
| `is` → `instanceof` · `as` → `checkcast` · `as?` → `instanceof` + `aconst_null` | **JVM 백엔드의 구현** | (1) |
| ★★ `null as String` 이 **`NullPointerException`**(`Intrinsics.checkNotNull`) | ★ **JVM 백엔드의 구현** — `checkcast` 가 `null` 을 통과시키므로 따로 심은 것 | (1)(6) |
| 예외 **메시지 전문**(`… loader 'bootstrap'`) | **JDK 구현** | (1)(3)(4) |
| 별칭 검사가 `instanceof String` 인 것 | **JVM 백엔드의 구현**(별칭이 JVM 에 없다) | (7) |
| `is` 스마트 캐스트의 **통과·차단 목록**과 문구 | **이 판(K2 2.4.20)의 관찰** | (5) |
| 「`cast is redundant`」 · 「`this cast can never succeed`」 | **이 판의 산출물** | (4)(6) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 타입마다 다른 처리 | ★ `when (x) { is A -> … }` | (5) — 가지마다 스마트 캐스트 |
| 「이 타입이 **아니면 버그**다」 | `as` | 실패가 **예외로** 드러난다 |
| 「이 타입이 아닐 수도 있다」 | `as?` + `?:` | (1) — `null` 을 **그 자리에서** 처리 |
| 제네릭 컨테이너의 원소 타입 확인 | `is List<*>` + 원소 검사 · 또는 `reified` | (2) · [12번 주제](../12-reified-type-parameters/) |
| 수 타입을 바꾼다 | ★ `toLong()`·`toInt()` | (4) — 캐스트가 아니다 |
| Java 에서 온 `null` 가능 값 | `?: error(…)` · `requireNotNull` | (6) — `as String` 의 NPE 메시지는 원인을 말하지 않는다 |
| ID 를 타입으로 가른다 | `value class` | (7) — 별칭은 검사로도 못 가른다 |

## 핵심 문장

1. `is` 는 `instanceof`, `as` 는 `checkcast`, `as?` 는 `instanceof` 뒤 **`null`** 이다 — 실패 방식의 차이가 명령에 있다.
2. `null as String` 은 이 판에서 **`NullPointerException`** 이다 — `checkcast` 가 `null` 을 통과시키므로 kotlinc 가 **`checkNotNull` 을 따로 심었다.**
3. 소거된 타입 인자는 **물을 수 없다** — 억지로 캐스트하면 **경고 한 줄**이고 **쓰는 자리**에서 터진다.
4. **캐스트는 변환이 아니다** — `1 as Long` 은 `ClassCastException` 이고 변환은 `toLong()` 이다.
5. `is` 뒤 스마트 캐스트는 04번과 **같은 안정 값 판정**을 쓴다 — `as` 뒤는 되고, `||` 오른쪽은 안 된다.
6. C# 의 `as` 는 **Kotlin 의 `as?`** 다 — 같은 낱말이 반대 실패 방식을 뜻한다.

## 관련 자료

- [04번 주제](../04-smart-casts/) — ★★ **선행.** 스마트 캐스트가 깨지는 **아홉 자리**(`null` 검사 기준)와 `var` 프로퍼티의 실제 경쟁.
- [12번 주제](../12-reified-type-parameters/) — 소거를 **뚫는** `reified`. (2)의 `is T` 를 푸는 곳.
- [05번 주제](../05-platform-types/) — 플랫폼 타입. (6)의 `C` 줄 NPE 의 정본.
- [29번 주제](../29-type-aliases-and-nested-type-aliases/) — 별칭은 새 타입이 아니다. (7).
- [26번 주제](../26-value-class-and-boxing/) — 검사로 가를 수 있는 **새 타입**.
- [01번 주제](../01-val-var-and-basic-types/) — 암묵 수치 변환 없음. (4)의 뿌리.
- [`../../../java/syntax/22-instanceof-type-patterns/`](../../../java/syntax/22-instanceof-type-patterns/) — Java `instanceof` 패턴 변수. 스마트 캐스트의 Java 쪽 짝.

## 용어 풀이

> **타입 검사(type check)** — `is`/`!is`. 값이 그 타입인가를 묻는다. JVM 의 `instanceof`.

> **안전하지 않은 캐스트(unsafe cast)** — `as`. 실패하면 예외.\
> 예: `x as String`.

> **안전한 캐스트(safe cast)** — `as?`. 실패하면 `null`. 결과 타입은 `T?`.\
> 예: `x as? String`.

> **소거(type erasure)** — 컴파일 뒤 제네릭 타입 인자가 사라지는 것. 그래서 `is List<String>` 을 못 한다.

> **비검사 캐스트(unchecked cast)** — 런타임이 **끝까지 확인할 수 없는** 캐스트. 경고가 나고, 틀리면 **나중에** 터진다.

> **스마트 캐스트(smart cast)** — 검사를 통과한 뒤 컴파일러가 그 변수를 좁은 타입으로 **자동 취급**하는 것. [04번 주제](../04-smart-casts/)가 정본.

> **`checkcast`** — JVM 의 캐스트 명령. 틀리면 `ClassCastException`, ★ **`null` 은 통과**시킨다.

## 더 들어가면

- **왜 `null as String` 에 검사를 따로 심었나** — JVM 에서 `null` 은 **모든 참조 타입의 값**이라 `checkcast String` 은 `null` 을 **합격**시킨다. 그대로 두면 `x as String` 의 결과가 `String`(null 불가)인데 **실제로는 `null`** 인 값이 흘러나가 **먼 자리에서** NPE 가 난다. kotlinc 는 그 틈을 **캐스트 자리에서** 막으려고 `checkNotNull` 을 앞에 둔다 — 대가로 예외 종류가 `ClassCastException` 이 아니라 **`NullPointerException`** 이 된다. `catch` 를 CCE 로만 걸어 둔 코드는 이 경우를 **못 잡는다.**
- **`as?` 를 기본으로 쓰면 안 되는 이유** — `as?` 는 실패를 **`null` 로 바꿔 버린다.** 「이 타입이 아니면 버그다」인 자리에서 `as?` 를 쓰면 버그가 **`null` 이라는 정상 값**으로 위장해 흐른다. 실패의 뜻이 「버그」면 `as`, 「있을 수 있는 경우」면 `as?` 다 — 연산자를 고르는 기준은 성능이 아니라 **실패의 뜻**이다.
