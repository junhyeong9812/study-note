# kotlin/syntax/09 — 가변 인자·spread 연산자·로컬 함수·중위 함수 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Functions](https://kotlinlang.org/docs/functions.html)(varargs · infix notation · local functions) · [Calling Kotlin from Java](https://kotlinlang.org/docs/java-to-kotlin-interop.html).
> **실행 검증** — 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javap` 에서 실제로 얻었다.\
> `kotlinc` 11회 · `java` 4회 · `javap` 5회. 컴파일 실패 시나리오 4벌.
> ⚠️ **`-jvm-target` 을 밝히지 않은 바이트코드 주장은 반쪽이다.** 이 문서의 역어셈블은 **기본값 1.8**(`major version: 52`)이다.
> **버전** — `vararg`·spread·로컬 함수·`infix` 는 전부 1.0.
> ★ **문서와 컴파일러가 어긋나는 자리를 하나 찾았다** — `infix` 의 「기본값 금지」 조항이다((8)).
> **경계** — 기본 인자·이름 붙인 인자·`@JvmOverloads` 의 정본은 [08번 주제](../08-function-declaration-default-and-named-args/)다.\
> 연산자 오버로딩 **전체**(`plus`·`get`·`invoke`·`iterator` 등 규약 표)는 목록의 **31번 주제**가 정본이다 —\
> 여기서는 `infix` 라는 **호출 형태**만 다룬다. 람다·클로저 일반은 [목록의 **10번 주제**](../10-lambdas-and-higher-order-functions/).\
> **Java 쪽 정본은 [`../../../java/syntax/08-method-declaration-overloading/`](../../../java/syntax/08-method-declaration-overloading/)** 다(가변 인자가 거기 있다).
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**`vararg` 는 문법이 아니라 「배열을 만들어 주는 설탕」이다.**

호출부에서 `sum(1, 2, 3)` 이라고 적으면 컴파일러가 **그 자리에서 배열을 하나 만든다.**\
이미 배열을 들고 있으면 `*` 를 붙여 넘기는데, **그때도 배열이 하나 더 만들어진다**(복사한다).

> **spread 연산자(`*`)** — 이미 있는 배열을 "낱개 인자들인 것처럼" 펼쳐 넘기는 연산자.\
> 예: `sum(*arr)` 은 `sum(arr[0], arr[1], …)` 처럼 동작한다.

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 낱개로 받아 봉지에 담아 준다 | `vararg` — 호출부가 배열을 만든다 |
| 봉지째 주면 **새 봉지에 옮겨 담는다** | spread(`*`) — `Arrays.copyOf` |
| 낱개와 봉지를 섞어 주면 큰 봉지를 짠다 | `IntSpreadBuilder` |
| 봉지 뒤에 또 물건을 놓으려면 이름표가 필요 | `vararg` 뒤 파라미터는 이름 붙인 인자로만 |
| 함수 안에만 사는 쪽지 | 로컬 함수 |
| 쪽지가 바깥 값을 쓰면 그 값을 **같이 적어 준다** | 캡처가 **파라미터로** 들어간다 |
| 바깥 값을 고쳐야 하면 상자에 담아 준다 | `Ref$IntRef` |
| 괄호를 뺀 호출 | `infix` |

```text
   sum(1, 2, 3)                  sum(*arr)
   ┌──────────────────┐          ┌───────────────────────────┐
   │ newarray int[3]  │          │ Arrays.copyOf(arr, len) ★ │
   │ [0]=1 [1]=2 [2]=3│          │  -> 새 배열                │
   │ sum(배열)         │          │ sum(새 배열)               │
   └──────────────────┘          └───────────────────────────┘
      배열 1개                       배열 1개 (원본은 그대로)
```

**똑같은 구조다** — 어느 쪽이든 **호출 한 번에 배열 한 개**가 새로 생긴다.

## 이 주제가 답하려는 질문

1. `vararg` 는 무엇이 되는가 — 그리고 `*` 는 **복사를 만드는가.**
2. 로컬 함수는 **클래스를 만드는가** — 바깥 지역 변수를 어떻게 잡는가.
3. `infix` 를 쓸 수 있는 조건은 무엇이고, **괄호가 필요해지는 자리**는 어디인가.

## 동작 방식

### (1) `vararg` 는 배열 파라미터다 — Java 의 `int...` 와 같은 것

**언제 쓰나** — `vararg xs: Int` 안에서 `xs` 로 무엇을 할 수 있는지 물을 때.

```kotlin
fun sum(vararg xs: Int): Int { var s = 0; for (x in xs) s += x; return s }
fun join(vararg parts: String): String = parts.joinToString("-")
fun takesArray(xs: Array<out String>): Int = xs.size
```

**출력** (`javap -s -p out/IcodeKt.class`)

```text
Compiled from "icode.kt"
public final class IcodeKt {
  public static final int sum(int...);
    descriptor: ([I)I

  public static final java.lang.String join(java.lang.String...);
    descriptor: ([Ljava/lang/String;)Ljava/lang/String;

  public static final int callLiteral();
    descriptor: ()I

  public static final int callSpread(int[]);
    descriptor: ([I)I

  public static final int callSpreadMixed(int[]);
    descriptor: ([I)I

  public static final int callEmpty();
    descriptor: ()I

  public static final java.lang.String callStrSpread(java.lang.String[]);
    descriptor: ([Ljava/lang/String;)Ljava/lang/String;

  public static final int takesArray(java.lang.String[]);
    descriptor: ([Ljava/lang/String;)I
}
```

```text
   fun sum(vararg xs: Int)        ──>  int sum(int... )      디스크립터 ([I)I
   fun join(vararg p: String)     ──>  String join(String...) 디스크립터 ([Ljava/lang/String;)…
   fun takesArray(xs: Array<out String>) ──> int (String[])   ★ 디스크립터가 같다
```

그림 해설:

- **`vararg` 는 배열 파라미터**다. `javap` 가 `int...` 로 찍는 것은 **`ACC_VARARGS` 플래그**가 붙어서다.
- ★ **`vararg parts: String` 과 `xs: Array<out String>` 의 디스크립터가 똑같다**(`[Ljava/lang/String;`).\
  차이는 **호출부 문법**뿐이다 — `vararg` 는 낱개로 받을 수 있고, `Array` 는 배열을 직접 받는다.
- 함수 안에서 `xs` 는 그냥 배열이다 — `size`·`for`·인덱싱이 다 된다.

**출력** (`ex.kt`)

```text
=== 1. vararg 는 배열이다 ===
개수=3, 타입=Array, 내용=가, 나, 다
개수=0, 타입=Array, 내용=
```

- **인자를 하나도 안 넘기면 빈 배열**이다. `null` 이 아니다.

비용 — 호출마다 배열 하나. `vararg` 를 안 쓴 호출도 **빈 배열 하나**를 만든다.

### (2) ★★ 호출부가 배열을 만든다 — 그리고 **`*` 는 복사를 만든다**

**언제 쓰나** — "이미 배열이 있으니 `*` 로 넘기면 공짜겠지" 라고 생각할 때.

```kotlin
fun callLiteral(): Int = sum(1, 2, 3)
fun callSpread(a: IntArray): Int = sum(*a)
fun callEmpty(): Int = sum()
fun callStrSpread(a: Array<String>): String = join(*a)
```

**출력** (`javap -c -p out/IcodeKt.class`)

```text
  public static final int callLiteral();
    Code:
       0: iconst_3
       1: newarray       int
       3: astore_0
       4: aload_0
       5: iconst_0
       6: iconst_1
       7: iastore
       8: aload_0
       9: iconst_1
      10: iconst_2
      11: iastore
      12: aload_0
      13: iconst_2
      14: iconst_3
      15: iastore
      16: aload_0
      17: invokestatic  #38                 // Method sum:([I)I
      20: ireturn

  public static final int callSpread(int[]);
    Code:
       0: aload_0
       1: ldc           #41                 // String a
       3: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_0
       7: aload_0
       8: arraylength
       9: invokestatic  #47                 // Method java/util/Arrays.copyOf:([II)[I
      12: invokestatic  #38                 // Method sum:([I)I
      15: ireturn
```

```text
  public static final int callEmpty();
    Code:
       0: iconst_0
       1: newarray       int
       3: invokestatic  #38                 // Method sum:([I)I
       6: ireturn

  public static final java.lang.String callStrSpread(java.lang.String[]);
    Code:
       0: aload_0
       1: ldc           #41                 // String a
       3: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_0
       7: aload_0
       8: arraylength
       9: invokestatic  #70                 // Method java/util/Arrays.copyOf:([Ljava/lang/Object;I)[Ljava/lang/Object;
      12: checkcast     #71                 // class "[Ljava/lang/String;"
      15: invokestatic  #73                 // Method join:([Ljava/lang/String;)Ljava/lang/String;
      18: areturn
```

```text
   sum(1, 2, 3)   ──> newarray int[3] ; iastore ×3 ; sum(배열)
   sum()          ──> newarray int[0] ; sum(빈 배열)     ← 빈 배열도 만든다
   sum(*a)        ──> Arrays.copyOf(a, a.length) ★ ; sum(사본)
   join(*a)       ──> Arrays.copyOf(a, len) + checkcast ; join(사본)
```

- ★★ **`*` 는 `java.util.Arrays.copyOf` 를 부른다. 복사를 만든다.**\
  `sum(*a)` 는 `a` 를 그대로 넘기지 않는다 — **얕은 복사본**을 만들어 넘긴다.
- 그래서 **함수가 배열을 고쳐도 호출자의 배열은 안 바뀐다.** 실행으로도 확인된다.

**출력** (`ex.kt`)

```text
=== 2. spread 는 복사를 만드나 ===
호출 전 src = 1, 2, 3
함수 안에서 본 것: [1, 2, 3] -> [-999, 2, 3]
호출 후 src = 1, 2, 3   <- 원본이 바뀌었나?
sameRef(*src) === src ? false
sameRef(*direct) === direct ? false
```

- 함수 안에서 `xs[0] = -999` 로 고쳤는데 **호출자의 `src` 는 `1, 2, 3` 그대로**다.
- `vararg` 파라미터를 그대로 돌려받아 `===` 로 비교해도 **`false`** 다 — 같은 객체가 아니다.
- ★ **이것이 "언어 보장" 인지 "최적화가 안 된 것" 인지는 갈라 적어야 한다.**\
  `Arrays.copyOf` 는 **`javap` 에서 본 구현**이고, 언어가 약속하는 것은 **"호출자의 배열이 안 바뀐다"** 쪽이다.
- **성능은 재지 않았다.** "복사가 일어난다" 는 관찰이고 "그래서 느리다" 는 이 문서가 하지 않은 주장이다.

비용 — 배열 하나의 얕은 복사. 낱개 호출도 배열 하나.

### (3) 낱개와 spread 를 섞으면 `IntSpreadBuilder` 가 나온다

**언제 쓰나** — `sum(0, *a, 9)` 처럼 섞어 쓸 때.

```kotlin
fun callSpreadMixed(a: IntArray): Int = sum(0, *a, 9)
```

**출력** (`javap -c -p out/IcodeKt.class`)

```text
  public static final int callSpreadMixed(int[]);
    Code:
       0: aload_0
       1: ldc           #41                 // String a
       3: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: new           #50                 // class kotlin/jvm/internal/IntSpreadBuilder
       9: dup
      10: iconst_3
      11: invokespecial #54                 // Method kotlin/jvm/internal/IntSpreadBuilder."<init>":(I)V
      14: astore_1
      15: aload_1
      16: iconst_0
      17: invokevirtual #57                 // Method kotlin/jvm/internal/IntSpreadBuilder.add:(I)V
      20: aload_1
      21: aload_0
      22: invokevirtual #61                 // Method kotlin/jvm/internal/IntSpreadBuilder.addSpread:(Ljava/lang/Object;)V
      25: aload_1
      26: bipush        9
      28: invokevirtual #57                 // Method kotlin/jvm/internal/IntSpreadBuilder.add:(I)V
      31: aload_1
      32: invokevirtual #65                 // Method kotlin/jvm/internal/IntSpreadBuilder.toArray:()[I
      35: invokestatic  #38                 // Method sum:([I)I
      38: ireturn
```

```text
   sum(0, *a, 9)
        │
        ├─ new IntSpreadBuilder(3)   ← 3 은 「조각 수」(0 · *a · 9)
        ├─ add(0)
        ├─ addSpread(a)              ← 배열째 이어 붙인다
        ├─ add(9)
        └─ toArray()  ──> sum(배열)
```

- 낱개만이면 `newarray`, 배열 하나만이면 `Arrays.copyOf`, **섞이면 빌더**다 — 세 갈래다.
- 생성자에 넘기는 `3` 은 **길이가 아니라 조각 수**다. 실제 길이는 `a.size + 2` 라 컴파일 시점에 모른다.
- 객체가 **둘** 생긴다(빌더 + 결과 배열).

비용 — 빌더 하나 + 배열 하나.

### (4) `vararg` 는 마지막이 아니어도 된다 — 대신 **뒤는 이름 붙인 인자만**

**언제 쓰나** — `vararg` 뒤에 옵션 파라미터를 두고 싶을 때.

```kotlin
fun mid(a: Int, vararg xs: Int, b: Int): Int = a + xs.size + b
fun two(vararg a: Int, vararg b: Int): Int = a.size + b.size

fun callMidNamed(): Int = mid(1, 2, 3, b = 9)
fun callMidPositional(): Int = mid(1, 2, 3, 9)
```

**출력** (`kotlinc bad1.kt`)

```text
bad1.kt:2:9: error: multiple vararg parameters are prohibited.
fun two(vararg a: Int, vararg b: Int): Int = a.size + b.size
        ^^^^^^
bad1.kt:2:24: error: multiple vararg parameters are prohibited.
fun two(vararg a: Int, vararg b: Int): Int = a.size + b.size
                       ^^^^^^
bad1.kt:5:32: error: no value passed for parameter 'b'.
fun callMidPositional(): Int = mid(1, 2, 3, 9)
                               ^^^
```

```text
   fun mid(a: Int, vararg xs: Int, b: Int)

   mid(1, 2, 3, b = 9)    O   ← b 는 이름으로만 닿는다
   mid(1, 2, 3, 9)        X   ← 9 가 xs 로 빨려 들어가고 b 가 빈다
                              "no value passed for parameter 'b'."

   fun two(vararg a, vararg b)   X   "multiple vararg parameters are prohibited."
```

- ★ **`vararg` 가 마지막이 아니어도 선언은 통과한다.** 문제는 **호출부**다 —\
  뒤 파라미터는 **이름 붙인 인자로만** 닿을 수 있다.
- 위치로 넘기면 그 값이 `vararg` 에 빨려 들어가고 뒤 파라미터가 빈다.\
  에러가 `no value passed for parameter 'b'` 라 **원인이 「이름을 안 썼다」라고 말해 주지 않는다.**
- **`vararg` 는 한 함수에 하나뿐**이다.

**출력** (`ex.kt`)

```text
=== 3. vararg 가 마지막이 아닐 때 ===
<[a|b|c]>
```

**★ `vararg` 에 기본값도 줄 수 있다** — 던져서 확인했다.

```kotlin
fun varargDefault(vararg xs: Int = intArrayOf(1, 2)): String = xs.joinToString()
```

**출력** (`vd2.kt`)

```text
varargDefault()      = [1, 2]
varargDefault(7,8,9) = [7, 8, 9]
```

- `vararg` 도 [08번 주제](../08-function-declaration-default-and-named-args/)의 `$default` 를 그대로 쓴다.
- **이름 붙인 인자로 배열을 직접 넘길 수도 있다** — `tag(classes = arrayOf("a", "b"), id = "y")` 가 통과했다.

비용 — (2)와 같다.

### (5) ★★ 로컬 함수는 **클래스를 안 만든다** — `private static` 메서드가 된다

**언제 쓰나** — "로컬 함수는 람다처럼 객체를 만들겠지" 라고 생각할 때.

```kotlin
fun outerNoCapture(n: Int): Int {
    fun twice(x: Int) = x * 2
    return twice(n)
}
fun outerCaptureVal(n: Int): Int {
    val base = n * 10
    fun add(x: Int) = base + x
    return add(1) + add(2)
}
fun outerCaptureVar(n: Int): Int {
    var acc = 0
    fun bump(x: Int) { acc += x }
    bump(n); bump(n)
    return acc
}
```

**출력** (`ls outl/` — 클래스 파일이 하나뿐이다)

```text
LocalKt.class
META-INF
```

**출력** (`javap -s -p outl/LocalKt.class`)

```text
Compiled from "local.kt"
public final class LocalKt {
  public static final int outerNoCapture(int);
    descriptor: (I)I

  public static final int outerCaptureVal(int);
    descriptor: (I)I

  public static final int outerCaptureVar(int);
    descriptor: (I)I

  private static final int outerNoCapture$twice(int);
    descriptor: (I)I

  private static final int outerCaptureVal$add(int, int);
    descriptor: (II)I

  private static final void outerCaptureVar$bump(kotlin.jvm.internal.Ref$IntRef, int);
    descriptor: (Lkotlin/jvm/internal/Ref$IntRef;I)V
}
```

```text
   fun outerCaptureVal(n) {          private static int outerCaptureVal$add(int base, int x)
       val base = n * 10       ──>                                 ▲
       fun add(x) = base + x                                       │
   }                                  ★ 캡처한 값이 「앞에 붙은 파라미터」가 된다
```

- ★★ **합성 클래스가 안 생긴다.** 클래스 파일은 `LocalKt.class` 하나뿐이다.\
  로컬 함수는 **`바깥함수$로컬함수` 라는 이름의 `private static` 메서드**로 펴진다.
- ★ **캡처한 `val` 은 파라미터가 된다.** `add(x)` 가 `add(int base, int x)` 로 **인자 하나가 늘었다.**\
  클로저가 "환경을 담은 객체" 가 아니라 **"인자를 더 받는 함수"** 로 구현됐다.

**출력** (`javap -c -p outl/LocalKt.class`)

```text
  public static final int outerCaptureVal(int);
    Code:
       0: iload_0
       1: bipush        10
       3: imul
       4: istore_1
       5: iload_1
       6: iconst_1
       7: invokestatic  #16                 // Method outerCaptureVal$add:(II)I
      10: iload_1
      11: iconst_2
      12: invokestatic  #16                 // Method outerCaptureVal$add:(II)I
      15: iadd
      16: ireturn
```

비용 — 객체 0. 정적 호출 한 번.

### (6) 바깥 `var` 를 고쳐 쓰면 **`Ref$IntRef` 상자**가 생긴다

**언제 쓰나** — 로컬 함수가 바깥 카운터를 늘릴 때.

**출력** (`javap -c -p outl/LocalKt.class`)

```text
  public static final int outerCaptureVar(int);
    Code:
       0: new           #20                 // class kotlin/jvm/internal/Ref$IntRef
       3: dup
       4: invokespecial #24                 // Method kotlin/jvm/internal/Ref$IntRef."<init>":()V
       7: astore_1
       8: aload_1
       9: iload_0
      10: invokestatic  #28                 // Method outerCaptureVar$bump:(Lkotlin/jvm/internal/Ref$IntRef;I)V
      13: aload_1
      14: iload_0
      15: invokestatic  #28                 // Method outerCaptureVar$bump:(Lkotlin/jvm/internal/Ref$IntRef;I)V
      18: aload_1
      19: getfield      #31                 // Field kotlin/jvm/internal/Ref$IntRef.element:I
      22: ireturn

  private static final void outerCaptureVar$bump(kotlin.jvm.internal.Ref$IntRef, int);
    Code:
       0: aload_0
       1: aload_0
       2: getfield      #31                 // Field kotlin/jvm/internal/Ref$IntRef.element:I
       5: iload_1
       6: iadd
       7: putfield      #31                 // Field kotlin/jvm/internal/Ref$IntRef.element:I
      10: return
```

```text
   캡처한 것이 val 이면            캡처한 것이 var 이면
   +---------------------+         +--------------------------------+
   | 값을 그대로 넘긴다  |         | new Ref$IntRef  ← 상자 1개     |
   | add(base, x)        |         | bump(상자, x)                  |
   | 객체 0개            |         | 상자.element 를 읽고 쓴다      |
   +---------------------+         +--------------------------------+
```

- ★ **`var` 를 고쳐 쓰려면 "같은 칸" 을 공유해야 하므로 상자가 필요하다.**\
  `int` 를 그냥 넘기면 **사본**이라 바깥이 안 바뀐다.
- 바깥 함수도 결과를 **`상자.element` 에서 읽는다**(`getfield … Ref$IntRef.element`).
- Java 의 람다·익명 클래스가 **`effectively final` 만 잡을 수 있는 것**과 대비되는 자리다 —\
  Kotlin 은 **상자를 만들어서** 그 제약을 없앴다. 람다 쪽의 정본은 [목록의 **10번 주제**](../10-lambdas-and-higher-order-functions/).

**출력** (`ex.kt`)

```text
=== 4. 로컬 함수의 클로저 ===
outer(4) = 10
```

비용 — 캡처한 `var` 하나당 상자 하나.

### (7) 로컬 함수 ↔ 람다 — 같은 일을 시켜도 코드가 다르다

**언제 쓰나** — 둘 중 무엇을 쓸지 고를 때.

```kotlin
fun withLocalFun(n: Int): Int {
    val base = n * 10
    fun add(x: Int) = base + x
    return add(1)
}
fun withLambda(n: Int): Int {
    val base = n * 10
    val add: (Int) -> Int = { x -> base + x }
    return add(1)
}
```

**출력** (`javap -c -p outlam/LamKt.class`)

```text
  public static final int withLambda(int);
    Code:
       0: iload_0
       1: bipush        10
       3: imul
       4: istore_1
       5: iload_1
       6: invokedynamic #33,  0             // InvokeDynamic #0:invoke:(I)Lkotlin/jvm/functions/Function1;
      11: astore_2
      12: aload_2
      13: iconst_1
      14: invokestatic  #39                 // Method java/lang/Integer.valueOf:(I)Ljava/lang/Integer;
      17: invokeinterface #43,  2           // InterfaceMethod kotlin/jvm/functions/Function1.invoke:(Ljava/lang/Object;)Ljava/lang/Object;
      22: checkcast     #45                 // class java/lang/Number
      25: invokevirtual #49                 // Method java/lang/Number.intValue:()I
      28: ireturn
```

```text
   로컬 함수                           람다를 변수에 담은 것
   +-----------------------------+     +----------------------------------+
   | invokestatic  …$add:(II)I   |     | invokedynamic -> Function1 객체  |
   | int 를 int 로 주고받는다    |     | Integer.valueOf  ← 박싱          |
   | 객체 0개                    |     | invoke(Object)                   |
   |                             |     | checkcast + intValue ← 언박싱    |
   +-----------------------------+     +----------------------------------+
```

- ★ **람다 쪽은 `Function1` 객체가 생기고 `Int` 가 박싱된다.** `invoke(Object)` 라는 **지워진 시그니처**로 불리기 때문이다.
- 로컬 함수 쪽은 **`int` 그대로** 정적 호출이다.
- 이 파일에서는 람다도 **별도 클래스 파일을 만들지 않았다** — `invokedynamic` 으로 처리됐다\
  (기본 타깃 1.8 에서도 그렇다. 람다 생성 전략의 정본은 [목록의 **10번 주제**](../10-lambdas-and-higher-order-functions/)).
- **성능은 재지 않았다.** 관찰된 것은 **박싱과 객체 생성의 유무**까지다.

비용 — 표의 오른쪽 칸 그대로.

### (8) ★ `infix` 의 조건 — **셋 중 하나는 컴파일러가 안 지킨다**

**언제 쓰나** — `a plus b` 처럼 쓰고 싶을 때.

```kotlin
class Box(val v: Int) {
    infix fun plus(o: Box) = Box(v + o.v)
    infix fun bad1(vararg o: Box) = this
    infix fun bad2(o: Box = Box(0)) = this
    infix fun bad3(a: Box, b: Box) = this
    infix fun bad4() = this
}
infix fun Int.times2(o: Int) = this * o
infix fun top(a: Int, b: Int) = a + b
```

**출력** (`kotlinc bad2.kt`)

```text
bad2.kt:3:5: error: 'infix' modifier is inapplicable to this function.
    infix fun bad1(vararg o: Box) = this
    ^^^^^
bad2.kt:5:5: error: 'infix' modifier is inapplicable to this function.
    infix fun bad3(a: Box, b: Box) = this
    ^^^^^
bad2.kt:6:5: error: 'infix' modifier is inapplicable to this function.
    infix fun bad4() = this
    ^^^^^
bad2.kt:9:1: error: 'infix' modifier is inapplicable to this function.
infix fun top(a: Int, b: Int) = a + b
^^^^^
```

```text
   infix 의 조건 (공식 문서)              kotlinc 2.4.20 이 실제로 거부한 것
   +----------------------------------+   +----------------------------------+
   | ① 멤버 함수 또는 확장 함수       |   | ① 최상위 함수 -> 거부 O          |
   | ② 파라미터 1개                   |   | ② 0개·2개 -> 거부 O              |
   | ③ vararg 아님                    |   | ③ vararg -> 거부 O               |
   | ④ 기본값 없음                    |   | ④ 기본값 -> ★ 거부 안 함        |
   +----------------------------------+   +----------------------------------+
```

- ★★ **`bad2`(기본값 있는 파라미터)에 에러가 안 났다.** 공식 문서는\
  *"The parameter must not accept a variable number of arguments (`vararg`) and must have no default value"* 라고 적는데,\
  **kotlinc 2.4.20 은 받아 준다.** 통과만 하는 게 아니라 **돌아간다.**

**출력** (`inf.kt`)

```text
중위로 호출: Box(3)
기본값으로 호출: Box(101)
```

- 중위 호출(`a withDefault Box(2)`)도 되고, 일반 호출로 **기본값을 쓰는 것**(`a.withDefault()`)도 됐다.
- 다만 **중위 형태로 인자를 생략할 수는 없다** — 문법상 오른쪽 피연산자가 반드시 있어야 한다.

```text
inf2.kt:3:32: error: syntax error: Expecting an element.
fun bad(a: Box) = a withDefault
                               ^
```

- ★ **그래서 「금지」의 실질은 「중위 호출에서는 어차피 못 쓴다」에 가깝다.**\
  **문서가 말하는 것과 이 컴파일러가 하는 것을 갈라 적어야 한다** — 다음 버전에서 막힐 수 있다.

**출력** (`ex.kt`)

```text
=== 5. 중위 호출 ===
Money(1000) plus Money(500) = 1500원
5 won "원" = 5원
```

비용 — 0. `infix` 는 **호출 표기**만 바꾼다. 바이트코드는 보통 호출과 같다.

### (9) ★ 중위 호출의 우선순위는 **산술보다 낮고 비교보다 높다**

**언제 쓰나** — 괄호를 어디에 쳐야 할지 고를 때.

```kotlin
infix fun Int.x(o: Int) = this * o
```

**출력** (`prec.kt`)

```text
2 x 3 + 1      = 8
(2 x 3) + 1    = 7
1..3 step 2    = [1, 3]
null ?: 1 to 2 = (1, 2)
a ?: 2 x 3     = 6
1 x 2 == 2     = true
```

**출력** (`ex.kt`)

```text
=== 6. 중위 호출의 우선순위 ===
1 + 2 shl 3  = 24      (산술이 먼저 — (1+2) shl 3)
1 + (2 shl 3)= 17
1 shl 2 + 3  = 32      (1 shl (2+3))
true && 1 == 1 = true
(1 to 2).toString() = (1, 2)
```

```text
   묶는 힘이 센 것 (위)
   ┌───────────────────────────────┐
   │ 곱셈·나눗셈   *  /  %          │
   │ 덧셈·뺄셈     +  -             │
   │ 범위          ..  ..<          │
   │ 중위 함수     x  shl  to  step │ ★ 여기
   │ 엘비스        ?:               │
   │ 비교          <  >  <=  >=     │
   │ 동등          ==  !=           │
   │ 논리곱        &&               │
   │ 논리합        ||               │
   └───────────────────────────────┘
   묶는 힘이 약한 것 (아래)
```

- ★ **`2 x 3 + 1` 이 `8`** 이다 — `2 x (3 + 1)`. **`+` 가 중위 함수보다 세게 묶는다.**\
  `(2 x 3) + 1 = 7` 과 갈린다. **괄호가 필요한 자리가 정확히 여기다.**
- `1 + 2 shl 3 = 24` 도 같은 규칙이다 — `(1 + 2) shl 3`.\
  Java 에서 `<<` 는 `+` 보다 **약한** 연산자라 결과가 같아 보이지만, **Kotlin 에서는 `shl` 이 함수**라서 규칙이 다르다.
- `1..3 step 2` 가 `(1..3) step 2` 인 것은 **범위가 중위 함수보다 세기** 때문이다.
- `a ?: 2 x 3` 이 `a ?: (2 x 3)` 인 것은 **엘비스가 더 약하기** 때문이다.
- 접두 연산자는 중위보다 세다 — `!b x n` 은 `(!b) x n` 으로 읽혀 수신자 타입이 안 맞는다.

```text
prec3.kt:9:39: error: candidate 'fun Int.x(o: Int): Int' is inapplicable because of a receiver type mismatch.
fun unaryNot(b: Boolean, n: Int) = !b x n
                                      ^
```

비용 — 0. 파싱 규칙이다.

## 문법 — 형태와 규칙

```kotlin
// 1) vararg
fun sum(vararg xs: Int): Int = xs.sum()
fun log(tag: String, vararg args: Any?, level: Int = 0) { }   // vararg 가 마지막이 아니어도 된다
sum(1, 2, 3)              // 호출부가 배열을 만든다
sum(*intArrayOf(1, 2))    // spread — 복사본을 만든다
sum(0, *a, 9)             // 섞으면 IntSpreadBuilder
sum()                     // 빈 배열
log("t", "a", level = 1)  // vararg 뒤는 이름 붙인 인자로만

// 2) 배열로 받기 — 호출 문법만 다르다
fun takesArray(xs: Array<out String>): Int = xs.size
takesArray(arrayOf("a", "b"))

// 3) 로컬 함수
fun outer(n: Int): Int {
    var acc = 0
    fun bump(x: Int) { acc += x }   // 바깥 var 를 고쳐 쓸 수 있다
    for (i in 1..n) bump(i)
    return acc
}

// 4) 중위 함수
class Money(val won: Int) {
    infix fun plus(o: Money) = Money(won + o.won)   // 멤버
}
infix fun Int.won(unit: String) = "$this$unit"      // 확장
Money(1000) plus Money(500)
5 won "원"
// infix 조건: 멤버 또는 확장 · 파라미터 1개 · vararg 아님 (+ 문서상 기본값 없음 — (8) 참고)
```

규칙 불릿.

- **`vararg` 는 한 함수에 하나**다. 마지막이 아니어도 되지만 **뒤 파라미터는 이름으로만** 닿는다.
- **`*` 는 복사를 만든다.** 원본은 안 바뀐다.
- **낱개 + spread 를 섞으면 `SpreadBuilder` 가 쓰인다.**
- **로컬 함수는 클래스를 안 만든다.** 캡처는 **파라미터**가 되고, `var` 캡처는 **`Ref` 상자**가 된다.
- **`infix` 는 멤버 또는 확장 · 파라미터 1개.** 우선순위는 **산술보다 낮고 비교보다 높다.**

## 어디서 틀리나

| 틀리는 형태 | 무슨 일이 일어나나 | 고치는 법 |
|---|---|---|
| 배열을 그냥 넘김 (`sum(a)`) | 타입 불일치 — `Int` 자리에 `IntArray` | `sum(*a)` |
| `*` 가 공짜라고 생각 | `Arrays.copyOf` 로 **복사**가 생긴다 | 필요하면 배열 파라미터(`Array<out T>`)로 받는다 |
| `vararg` 배열을 고치면 원본도 바뀔 줄 앎 | 사본이라 **안 바뀐다** | 돌려줄 값은 반환으로 넘긴다 |
| `vararg` 뒤 파라미터를 위치로 넘김 | `no value passed for parameter 'b'` — **원인을 안 알려 준다** | 이름 붙인 인자로 넘긴다 |
| `vararg` 를 두 개 선언 | `multiple vararg parameters are prohibited.` | 하나로 합치거나 리스트로 받는다 |
| 로컬 함수가 객체를 만든다고 생각 | **안 만든다.** `private static` 메서드다 | 람다와 구분해 기억한다 |
| 바깥 `var` 캡처의 비용을 0으로 봄 | `Ref$IntRef` 상자가 하나 생긴다 | 필요 없으면 반환값으로 바꾼다 |
| 로컬 함수를 람다로 바꿔 씀 | **박싱과 `Function1` 객체**가 생긴다 | 이름 있는 재사용이면 로컬 함수 |
| `infix` 를 최상위 함수에 붙임 | `'infix' modifier is inapplicable to this function.` | 멤버나 확장으로 만든다 |
| `a x b + c` 를 `(a x b) + c` 로 읽음 | 실제로는 **`a x (b + c)`** 다 | 괄호를 친다 |
| `infix` 기본값이 금지라고 외움 | **이 컴파일러는 받아 준다**((8)) | 문서와 구현을 갈라 기억한다 |
| `infix` 를 중위로 쓰며 인자 생략 | `syntax error: Expecting an element.` | 일반 호출로 바꾼다 |

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 | 근거 |
|---|---|---|
| `vararg` 가 함수 안에서 배열인 것 | **언어** | 명세 + 실행 |
| 인자 0개면 빈 배열인 것 | **언어** | 실행 |
| `vararg` 가 하나뿐인 것 | **언어** | 컴파일 에러 |
| `vararg` 뒤 파라미터가 이름 전용인 것 | **언어** | 컴파일 에러 + 문서 |
| **호출자의 배열이 spread 로 안 바뀌는 것** | **언어** | 실행(`src` 그대로) |
| 로컬 함수가 바깥 `var` 를 고쳐 쓸 수 있는 것 | **언어** | 실행 |
| `infix` 가 멤버/확장·1개 파라미터여야 하는 것 | **언어** | 컴파일 에러 |
| 중위 호출의 우선순위 | **언어(문법)** | 실행 결과 |
| **`vararg` 가 `ACC_VARARGS` 배열 파라미터인 것** | **구현** | `javap -s` |
| **`*` 가 `Arrays.copyOf` 인 것** | **구현** ★ | `javap` |
| **섞으면 `IntSpreadBuilder` 인 것** | **구현** | `javap` |
| **로컬 함수가 `바깥$안` 정적 메서드인 것** | **구현** ★ | `javap` + 클래스 파일 목록 |
| **캡처가 앞에 붙는 파라미터가 되는 것** | **구현** | `javap` |
| **`var` 캡처가 `Ref$IntRef` 인 것** | **구현** | `javap` |
| **람다가 `invokedynamic` + `Function1` 인 것** | **구현(+타깃 의존)** | `javap` |
| **`infix` 에 기본값이 허용되는 것** | **구현 — 문서와 어긋난다** ★★ | 컴파일 + 실행 |

★ **가장 중요한 구분 한 줄** — **"spread 는 복사를 만든다" 는 `javap` 로 본 구현이고,\
언어가 약속하는 것은 "호출자의 배열이 안 바뀐다" 쪽이다.**\
그리고 **`infix` 의 「기본값 금지」는 문서에만 있고 이 컴파일러에는 없다** — 둘을 같은 것으로 적으면 틀린다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 인자 개수가 호출마다 다를 때 | `vararg` | 호출부가 짧다 |
| 이미 컬렉션이 있을 때 | `List<T>` 파라미터 | spread 도 배열 변환도 필요 없다 |
| 배열을 그대로 받아야 할 때 | `Array<out T>` | 복사가 안 생긴다 |
| `vararg` 뒤에 옵션이 필요할 때 | `vararg` + 이름 전용 파라미터 | 순서를 안 바꿔도 된다 |
| 함수 안에서만 두세 번 쓰는 보조 로직 | 로컬 함수 | 이름이 밖으로 안 샌다. 객체도 안 생긴다 |
| 그 보조 로직을 값으로 넘겨야 할 때 | 람다 | 로컬 함수는 값이 아니다(`::` 참조는 가능) |
| 바깥 `var` 를 고쳐야 할 때 | 로컬 함수 | Java 의 `effectively final` 제약이 없다 |
| 읽기가 **정말** 좋아질 때만 | `infix` | 우선순위가 직관과 어긋나 괄호가 늘어난다 |
| DSL 을 만들 때 | `infix` | 의도된 용법이다 |
| 기호 연산자를 만들고 싶을 때 | `operator` | 목록의 **31번 주제**가 정본이다 |

판단 규칙 두 줄.

- **`vararg` 를 쓸지 `List` 를 쓸지는 「호출자가 무엇을 들고 있나」로 정한다.** 이미 컬렉션이면 `List` 가 항상 싸다.
- **`infix` 는 「괄호를 빼도 뜻이 안 흔들리는가」로 판단한다.** 산술과 섞이는 자리에는 쓰지 않는다.

## 핵심 문장

- `vararg` 는 **배열 파라미터**다. `vararg p: String` 과 `p: Array<out String>` 은 **디스크립터가 같다**.
- 호출부가 배열을 만든다 — 낱개는 `newarray`, **인자 0개도 빈 배열**을 만든다.
- ★ **spread(`*`)는 `java.util.Arrays.copyOf` 로 복사를 만든다.** 그래서 호출자의 배열이 안 바뀐다.
- 낱개와 spread 를 섞으면 **`IntSpreadBuilder`** 가 쓰인다 — 객체가 둘 생긴다.
- `vararg` 는 **마지막이 아니어도 되지만** 뒤 파라미터는 **이름 붙인 인자로만** 닿는다. 한 함수에 **하나뿐**이다.
- ★★ **로컬 함수는 합성 클래스를 안 만든다.** `바깥$안` 이라는 **`private static` 메서드**가 되고\
  **캡처한 값은 앞에 붙는 파라미터**가 된다.
- ★ **바깥 `var` 를 고쳐 쓰면 `Ref$IntRef` 상자가 하나 생긴다.**
- 같은 일을 람다로 시키면 **`Function1` 객체 + 박싱**이 생긴다 — 로컬 함수는 `int` 그대로 정적 호출이다.
- `infix` 는 **멤버 또는 확장 · 파라미터 1개 · `vararg` 아님**. ★ **기본값 금지는 문서에만 있고 이 컴파일러는 받아 준다.**
- ★ **중위 호출은 산술보다 약하게 묶는다** — `2 x 3 + 1` 은 **8**(`2 x (3+1)`)이다.

## 관련 자료

- [`../README.md`](../README.md) — Kotlin 문법·API 주제 목록(이 주제는 09번)
- [08번 주제](../08-function-declaration-default-and-named-args/) — **직접 선행.** 기본 인자·이름 붙인 인자·`@JvmOverloads` 가 정본이고,\
  이 문서의 `vararg` 기본값과 `vararg` 뒤 이름 전용 파라미터가 그것 위에 서 있다
- [`../../../java/syntax/08-method-declaration-overloading/`](../../../java/syntax/08-method-declaration-overloading/) — **Java 쪽 정본.**\
  가변 인자와 오버로드 해소가 거기 있다. 여기는 **spread 와 `SpreadBuilder`**
- [07번 주제](../07-loops-ranges-and-labels/) — `for` 로 `vararg` 배열을 도는 것, `step`·`downTo` 가 **중위 함수**인 것
- [03번 주제](../03-null-safe-types/) — `checkNotNullParameter` 의 정본
- [목록의 **10번 주제**](../10-lambdas-and-higher-order-functions/)(람다와 고차 함수 — `it`·마지막 인자 람다·클로저) — **람다가 바깥 `var` 를 잡는 것**의 정본.\
  이 문서의 (6)·(7)은 **로컬 함수 쪽**만 다뤘다
- [목록의 **11번 주제**](../11-inline-functions/)(인라인 함수) — 람다의 객체 생성이 사라지는 조건
- [목록의 **13번 주제**](../13-extension-functions-and-properties/)(확장 함수) — `infix` 확장 함수의 수신자 규칙
- 목록의 **31번 주제**(연산자 오버로딩·중위 함수·`invoke` 규약) — **규약 표 전체의 정본.**\
  여기는 `infix` 라는 **호출 형태**와 그 우선순위만 다뤘다
- 목록의 **39번 주제**(Java 상호운용 애너테이션) — `vararg` 가 Java 에서 `T...` 로 보이는 것
- 목록의 **41번 주제**(컬렉션 생성) — `listOf(vararg elements: T)` 가 이 문법의 대표 사용처다

## 용어 풀이

- **`vararg`** — 인자를 개수 제한 없이 받는 파라미터. 함수 안에서는 **배열**이다.
- **spread 연산자(`*`)** — 배열을 낱개 인자처럼 펼쳐 넘기는 연산자. 얕은 복사본을 만든다.
- **얕은 복사(shallow copy)** — 배열 칸만 새로 만들고 안의 객체는 그대로 공유하는 복사.
- **`Arrays.copyOf`** — JDK 의 배열 복사 함수. spread 가 부른다.
- **`IntSpreadBuilder`** — 낱개와 배열을 섞어 넘길 때 컴파일러가 쓰는 kotlin-stdlib 내부 빌더. `add`/`addSpread`/`toArray`.
- **`ACC_VARARGS`** — "마지막 배열 파라미터를 낱개로 받을 수 있다" 는 클래스 파일 플래그. `javap` 가 `int...` 로 찍게 만든다.
- **로컬 함수(local function)** — 함수 몸통 안에 선언하는 함수. 바깥의 지역 변수를 쓸 수 있다.
- **클로저(closure)** — 함수가 선언된 자리의 지역 변수를 함께 들고 다니는 것.
- **캡처(capture)** — 클로저가 바깥 변수를 잡는 것. Kotlin 의 로컬 함수에서는 **파라미터**로 구현된다.
- **`Ref$IntRef`** — kotlin-stdlib 내부의 `int` 한 칸짜리 상자. 캡처한 `var` 를 공유하려고 쓴다.
- **`Function1`** — 인자 1개짜리 함수 타입의 런타임 인터페이스. `invoke(Object): Object` 하나를 가진다.
- **중위 함수(infix function)** — 점과 괄호 없이 `a f b` 로 부를 수 있는 함수. `infix` 수식어가 필요하다.
- **우선순위(precedence)** — 괄호가 없을 때 어느 연산이 먼저 묶이는지의 순서.

---

## 더 들어가면

- **stdlib 호출에서도 08번의 비트마스크가 그대로 보인다.** `xs.joinToString()` 한 줄이 이렇게 내려간다.

```text
       6: aload_0
       7: aconst_null
       8: aconst_null
       9: aconst_null
      10: iconst_0
      11: aconst_null
      12: aconst_null
      13: bipush        63
      15: aconst_null
      16: invokestatic  #21                 // Method kotlin/collections/ArraysKt.joinToString$default:([ILjava/lang/CharSequence;Ljava/lang/CharSequence;Ljava/lang/CharSequence;ILjava/lang/CharSequence;Lkotlin/jvm/functions/Function1;ILjava/lang/Object;)Ljava/lang/String;
```

  `bipush 63` = `0b111111` — **파라미터 여섯 개를 전부 생략**했다는 뜻이다([08번 주제](../08-function-declaration-default-and-named-args/)의 (1)).
- `Array<out String>` 의 `out` 은 **변성**이다. `vararg` 파라미터의 타입도 실제로는 `Array<out T>` 라\
  `Array<String>` 을 `Array<Any>` 자리에 넘길 수 있다. 변성의 정본은 목록의 **28번 주제**.
- `IntSpreadBuilder` 말고 참조 타입용 `SpreadBuilder` 도 있다 — 원시 타입마다 따로 있는 구조다\
  (**이 문서에서는 `Int` 판만 찍어 봤다**).
- **중위 호출은 새 줄로 이어 쓸 수 있다.** `2 x` 다음 줄에 `3` 을 적어도 컴파일된다 — 던져서 확인했다\
  (`prec3.kt` 가 그 줄에서는 에러를 내지 않았다). 다만 **왼쪽 피연산자로 줄을 끝내면** 다른 뜻이 된다.
- 이 문서에서 **성능은 한 번도 재지 않았다.** `javap` 로 본 것은 **복사·할당·박싱의 유무**까지이고,\
  "그래서 어느 쪽이 빠르다" 는 하지 않은 주장이다.
