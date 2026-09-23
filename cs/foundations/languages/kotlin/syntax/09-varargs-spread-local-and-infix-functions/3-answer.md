# kotlin/syntax/09 — 가변 인자·spread 연산자·로컬 함수·중위 함수 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javap` 에서 실제로 얻었다.\
> 역어셈블은 **기본 `-jvm-target`(1.8 · `major version: 52`)** 이다.\
> ★ 7번은 **공식 문서와 이 컴파일러가 어긋나는 자리**다 — 둘을 갈라 적었다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★ `newarray` · `Arrays.copyOf` · `IntSpreadBuilder` · 빈 배열

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

  public static final int callEmpty();
    Code:
       0: iconst_0
       1: newarray       int
       3: invokestatic  #38                 // Method sum:([I)I
       6: ireturn
```

**왜 그런가**

| | 호출 | 무엇이 생기나 |
|---|---|---|
| `[A]` | `sum(1, 2, 3)` | `newarray int[3]` + `iastore` 세 번 |
| `[B]` | `sum(*a)` | **`java.util.Arrays.copyOf(a, a.length)`** |
| `[C]` | `sum(0, *a, 9)` | **`kotlin.jvm.internal.IntSpreadBuilder`** + 결과 배열 |
| `[D]` | `sum()` | `newarray int[0]` — **빈 배열도 만든다** |

```text
   sum(1, 2, 3)   ──> newarray int[3] ; iastore ×3 ; sum(배열)
   sum()          ──> newarray int[0] ; sum(빈 배열)     ← 아무것도 안 만드는 게 아니다
   sum(*a)        ──> Arrays.copyOf(a, a.length) ★ ; sum(사본)
   sum(0, *a, 9)  ──> IntSpreadBuilder(3) ; add ; addSpread ; add ; toArray()
```

- `[B]` 가 부르는 JDK 메서드는 **`java.util.Arrays.copyOf`** 다. 참조 타입이면 `([Ljava/lang/Object;I)` 판이 쓰이고\
  뒤에 `checkcast` 가 붙는다(2번 참고).
- `[C]` 의 클래스는 **`kotlin/jvm/internal/IntSpreadBuilder`**.\
  생성자에 넘기는 `3` 은 **길이가 아니라 조각 수**(`0` · `*a` · `9`)다. 실제 길이는 `a.size + 2` 라 컴파일 시점에 모른다.
- ★ `[D]` 도 **빈 배열을 만든다.** "인자를 안 넘기면 공짜" 가 아니다.

### 2. ★★ `1, 2, 3` 그대로 · `false` — **spread 는 복사본을 넘긴다**

**출력** (`ex.kt`)

```text
=== 2. spread 는 복사를 만드나 ===
호출 전 src = 1, 2, 3
함수 안에서 본 것: [1, 2, 3] -> [-999, 2, 3]
호출 후 src = 1, 2, 3   <- 원본이 바뀌었나?
sameRef(*src) === src ? false
sameRef(*direct) === direct ? false
```

**왜 그런가**

```text
   호출 전         src = [1, 2, 3]
                    │
                    │ sum(*src)
                    ▼
              Arrays.copyOf ──> 사본 [1, 2, 3]
                                  │
                                  │ 함수 안에서 xs[0] = -999
                                  ▼
                               사본 [-999, 2, 3]

   호출 후         src = [1, 2, 3]   ← 안 바뀌었다
```

- `[A]` = **`1, 2, 3`** — 함수 안에서 `xs[0]` 을 고쳤는데 원본은 그대로다.
- `[B]` = **`false`** — `vararg` 파라미터를 그대로 돌려받아 비교해도 **같은 객체가 아니다.**
- 근거가 되는 바이트코드 한 줄 —

```text
       9: invokestatic  #47                 // Method java/util/Arrays.copyOf:([II)[I
```

- ★ **갈라 적어야 하는 것** —\
  **언어 보장** = "호출자의 배열이 안 바뀐다" (실행으로 확인).\
  **구현** = "그 방법이 `java.util.Arrays.copyOf` 다" (`javap` 로 확인).\
  다음 버전이 다른 방법을 써도 앞 문장은 남고 뒤 문장은 바뀔 수 있다.
- **얕은 복사**다 — 배열 칸만 새로 만들고 안의 객체는 공유한다.\
  `Array<StringBuilder>` 를 spread 로 넘기고 그 안의 `StringBuilder` 를 고치면 **원본에도 보인다**\
  (이 문서에서는 `IntArray`·`Array<String>` 만 던져 봤다).
- **성능은 재지 않았다.** "복사가 생긴다" 는 관찰이고 "그래서 느리다" 는 이 문서가 하지 않은 주장이다.

### 3. 디스크립터는 **같다** — 다른 것은 호출 문법뿐이다

**출력** (`javap -s -p out/IcodeKt.class`)

```text
  public static final java.lang.String join(java.lang.String...);
    descriptor: (Ljava/lang/String;)Ljava/lang/String;
```

```text
  public static final int takesArray(java.lang.String[]);
    descriptor: ([Ljava/lang/String;)I
```

**왜 그런가**

```text
   fun join(vararg p: String)            ──>  ([Ljava/lang/String;)Ljava/lang/String;
   fun takesArray(xs: Array<out String>) ──>  ([Ljava/lang/String;)I
                                               └──── 파라미터 타입이 같다 ★
```

| | 선언 | 낱개 호출 | 배열 호출 |
|---|---|---|---|
| `vararg` | `vararg p: String` | `join("a", "b")` — 된다 | `join(*arr)` — **`*` 가 필요하다** |
| 배열 | `xs: Array<out String>` | 불가 | `takesArray(arr)` — 그대로 |

- **디스크립터는 같다.** 파라미터 타입은 둘 다 `[Ljava/lang/String;` 다.
- 실제로 다른 것은 **호출부 문법**과 **클래스 파일 플래그** 둘이다.
- `javap` 가 `String...` 으로 찍는 이유는 **`ACC_VARARGS` 플래그**가 붙어서다.\
  그 플래그가 있으면 **Java 쪽에서도 낱개로 부를 수 있다.**
- 그래서 **배열을 이미 들고 있는 호출자에게는 `Array<out T>` 파라미터가 복사 없이 싸다**(2번).

### 4. ★ 선언은 통과 · `[A]` 만 되고 `[C]` 는 거부

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

**출력** (`ex.kt` — `[A]` 형태가 실제로 도는 것)

```text
=== 3. vararg 가 마지막이 아닐 때 ===
<[a|b|c]>
```

**왜 그런가**

```text
   fun mid(a: Int, vararg xs: Int, b: Int)

   mid(1, 2, 3, b = 9)    O   ← b 는 이름으로만 닿는다
   mid(1, 2, 3, 9)        X   ← 9 가 xs 로 빨려 들어가고 b 가 빈다
                              "no value passed for parameter 'b'."

   fun two(vararg a, vararg b)   X   "multiple vararg parameters are prohibited."
```

- ★ **선언 `mid` 자체는 통과한다.** `vararg` 가 마지막이 아니어도 된다.
- `[A]`(`b = 9`)만 되고 `[B]`(위치로 `9`)는 안 된다 — **뒤 파라미터는 이름 붙인 인자로만** 닿는다.
- ★ **에러 문구가 진짜 원인을 말해 주지 않는다.** `no value passed for parameter 'b'` 는 **결과**이고,\
  원인은 "`9` 가 `vararg` 로 빨려 들어갔다" 는 것이다. 이 에러를 보면 **이름을 빠뜨린 건 아닌지** 먼저 본다.
- `[C]` — **`multiple vararg parameters are prohibited.`** 가 **두 파라미터 자리에 각각** 나온다.

### 5. ★★ 클래스 파일은 **하나**다 — 로컬 함수는 `private static` 메서드가 된다

**출력** (`ls outl/`)

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

**왜 그런가**

```text
   fun outerCaptureVal(n) {          private static int outerCaptureVal$add(int base, int x)
       val base = n * 10       ──>                                 ▲
       fun add(x) = base + x                                       │
   }                                  ★ 캡처한 값이 「앞에 붙은 파라미터」가 된다

   캡처한 것이 val 이면            캡처한 것이 var 이면
   +---------------------+         +--------------------------------+
   | 값을 그대로 넘긴다  |         | new Ref$IntRef  ← 상자 1개     |
   | add(base, x)        |         | bump(상자, x)                  |
   | 객체 0개            |         | 상자.element 를 읽고 쓴다      |
   +---------------------+         +--------------------------------+
```

- ★★ **클래스 파일은 `LocalKt.class` 하나뿐이다.** 합성 클래스가 **안 생긴다.**
- 숨은 메서드 이름은 **`바깥함수$로컬함수`** 다 —\
  `outerNoCapture$twice` · `outerCaptureVal$add` · `outerCaptureVar$bump`. 전부 `private static final`.
- ★ **`add` 의 파라미터가 둘인 이유** — 캡처한 `base` 가 **앞에 붙는 파라미터**가 됐다.\
  클로저가 "환경을 담은 객체" 가 아니라 **"인자를 더 받는 함수"** 로 구현된 것이다.
- ★ **`bump` 의 첫 파라미터는 `kotlin.jvm.internal.Ref$IntRef`** 다.\
  `acc` 가 **`var`** 이라 로컬 함수가 **고쳐 써야** 하는데, `int` 를 그냥 넘기면 **사본**이라 바깥이 안 바뀐다.\
  그래서 **같은 칸을 공유할 상자**가 필요하다. 바깥 함수도 결과를 `상자.element` 에서 읽는다.
- Java 의 람다·익명 클래스가 `effectively final` 만 잡을 수 있는 것과 대비되는 자리다 —\
  Kotlin 은 **상자를 만들어** 그 제약을 없앴다.

### 6. `invokestatic` 대 `invokedynamic` + 박싱

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

**출력** (`ls outlam/`)

```text
LamKt.class
META-INF
```

**왜 그런가**

```text
   로컬 함수                           람다를 변수에 담은 것
   +-----------------------------+     +----------------------------------+
   | invokestatic  …$add:(II)I   |     | invokedynamic -> Function1 객체  |
   | int 를 int 로 주고받는다    |     | Integer.valueOf  ← 박싱          |
   | 객체 0개                    |     | invoke(Object)                   |
   |                             |     | checkcast + intValue ← 언박싱    |
   +-----------------------------+     +----------------------------------+
```

- 로컬 함수 쪽은 **`invokestatic outerCaptureVal$add:(II)I`** — `int` 를 `int` 로 주고받는다.
- 람다 쪽은 **`invokedynamic`** 으로 `Function1` 객체를 만들고, 부를 때 **`Integer.valueOf`(박싱)** →\
  `invoke(Object)` → **`checkcast` + `intValue`(언박싱)** 을 지난다.\
  박싱 두 곳은 **인자 넣을 때(`valueOf`)와 결과 꺼낼 때(`intValue`)** 다.
- ★ **람다도 별도 클래스 파일을 안 만들었다** — 클래스 파일은 `LamKt.class` 하나다.\
  `invokedynamic` + `LambdaMetafactory` 로 런타임에 만든다.\
  람다 생성 전략의 정본은 [목록의 **10번 주제**](../10-lambdas-and-higher-order-functions/).
- 고르는 기준 — **이름을 붙여 두세 번 부를 보조 로직이면 로컬 함수**(객체도 박싱도 없다),\
  **값으로 넘겨야 하면 람다**다. 로컬 함수는 값이 아니다(`::이름` 으로 참조할 수는 있다).
- **성능은 재지 않았다.** 관찰된 것은 **박싱과 객체 생성의 유무**까지다.

### 7. ★★ 네 개가 거부된다 — 그리고 **`[C]` 는 문서와 달리 통과한다**

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

**출력** (`inf.kt` — `[C]` 를 따로 떼어 컴파일하고 실행한 것)

```text
중위로 호출: Box(3)
기본값으로 호출: Box(101)
```

**출력** (`kotlinc inf2.kt` — 중위 형태로 인자를 생략해 본 것)

```text
inf2.kt:3:32: error: syntax error: Expecting an element.
fun bad(a: Box) = a withDefault
                               ^
```

**왜 그런가**

```text
   infix 의 조건 (공식 문서)              kotlinc 2.4.20 이 실제로 거부한 것
   +----------------------------------+   +----------------------------------+
   | ① 멤버 함수 또는 확장 함수       |   | [F] 최상위 함수 -> 거부 O        |
   | ② 파라미터 1개                   |   | [D] 2개 · [E] 0개 -> 거부 O      |
   | ③ vararg 아님                    |   | [B] vararg -> 거부 O             |
   | ④ 기본값 없음                    |   | [C] 기본값 -> ★ 거부 안 함      |
   +----------------------------------+   +----------------------------------+
```

- 에러는 **네 개**(`[B]`·`[D]`·`[E]`·`[F]`)이고 문구는 **전부 같다** — `'infix' modifier is inapplicable to this function.`\
  **어느 조건을 어겼는지는 안 알려 준다.** 조건이 넷이라 눈으로 짚어야 한다.
- ★★ **`[C]`(기본값 있는 파라미터)에는 에러가 안 났다.**\
  공식 문서는 *"The parameter must not accept a variable number of arguments (`vararg`) and must have no default value"* 라고 적는데,\
  **kotlinc 2.4.20 은 받아 준다.** 통과만 하는 게 아니라 **중위 호출도 되고 기본값도 실제로 쓰인다.**
- 다만 **중위 형태로 인자를 생략할 수는 없다** — `a withDefault` 는 **파서 단계에서** 죽는다.\
  그래서 "금지" 의 실질은 **"중위 호출에서는 어차피 못 쓴다"** 에 가깝다.
- ★ **문서가 말하는 것과 이 컴파일러가 하는 것을 갈라 적어야 한다.**\
  명세가 금지한 것을 구현이 받아 주는 자리라, **다음 버전에서 막혀도 이상하지 않다.**

### 8. ★ `8` · `24` · `32` · `[1, 3]`

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

**왜 그런가**

| | 식 | 값 | 괄호로 다시 적으면 |
|---|---|---|---|
| `[A]` | `2 x 3 + 1` | **`8`** | `2 x (3 + 1)` |
| `[B]` | `1 + 2 shl 3` | **`24`** | `(1 + 2) shl 3` |
| `[C]` | `1 shl 2 + 3` | **`32`** | `1 shl (2 + 3)` |
| `[D]` | `(1..3 step 2).toList()` | **`[1, 3]`** | `((1..3) step 2)` |

```text
   묶는 힘이 센 것 (위)
   ┌───────────────────────────────┐
   │ 접두            !  -  +        │
   │ 곱셈·나눗셈     *  /  %        │
   │ 덧셈·뺄셈       +  -           │
   │ 범위            ..  ..<        │
   │ 중위 함수       x  shl  to  step │ ★ 여기
   │ 엘비스          ?:             │
   │ 비교            <  >  <=  >=   │
   │ 동등            ==  !=         │
   │ 논리곱          &&             │
   │ 논리합          ||             │
   └───────────────────────────────┘
   묶는 힘이 약한 것 (아래)
```

- **중위 함수는 산술(`+`·`*`)과 범위(`..`)보다 약하고, 엘비스(`?:`)·비교·동등·논리보다 세다.**
- 그래서 `2 x 3 + 1` 이 **`2 x (3 + 1) = 8`** 이다 — `(2 x 3) + 1 = 7` 과 갈린다.\
  **괄호가 필요한 자리가 정확히 여기**다.
- `1..3 step 2` 가 `(1..3) step 2` 인 것도 같은 표에서 나온다 — **범위가 중위 함수보다 세다.**
- `a ?: 2 x 3` 이 `a ?: (2 x 3)` 인 것은 **엘비스가 더 약하기** 때문이다.
- `!b x n` 이 안 되는 이유 — **접두 `!` 가 중위보다 세게 묶여** `(!b) x n` 으로 읽힌다.\
  그러면 수신자가 `Boolean` 이라 `Int.x` 의 수신자 타입과 안 맞는다.

```text
prec3.kt:9:39: error: candidate 'fun Int.x(o: Int): Int' is inapplicable because of a receiver type mismatch.
fun unaryNot(b: Boolean, n: Int) = !b x n
                                      ^
```

### 9. 된다 — 그리고 [08번](../08-function-declaration-default-and-named-args/)의 `$default` 를 그대로 쓴다

**출력** (`vd2.kt`)

```text
varargDefault()      = [1, 2]
varargDefault(7,8,9) = [7, 8, 9]
```

**출력** (`javap -c -p outvd2/Vd2Kt.class` — 앞부분)

```text
Compiled from "vd2.kt"
public final class Vd2Kt {
  public static final java.lang.String varargDefault(int...);
    Code:
       0: aload_0
       1: ldc           #9                  // String xs
       3: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
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
      19: areturn

  public static java.lang.String varargDefault$default(int[], int, java.lang.Object);
    Code:
       0: iload_1
       1: iconst_1
       2: iand
       3: ifeq          20
       6: iconst_2
       7: newarray       int
       9: astore_3
      10: aload_3
      11: iconst_0
```

**출력** (`vd.kt` — 이름으로 배열을 직접 넘긴 것)

```text
<div class='' id=''>
<p class='a b' id=''>
<p class='a b' id='x'>
<div class='a b' id='y'>
```

**왜 그런가**

- **컴파일된다.** `f()` 는 기본값 `[1, 2]` 를, `f(7, 8, 9)` 는 넘긴 값을 본다.
- 기본값은 **`varargDefault$default` 안**에 들어간다 — `iand` 로 비트를 보고 `newarray int[2]` 를 만든다.\
  [08번 주제](../08-function-declaration-default-and-named-args/)의 (1)과 **똑같은 기계**다.
- ★ **이름으로 배열을 직접 넘기는 것도 된다** — `tag(classes = arrayOf("a", "b"), id = "y")` 가 `<div class='a b' id='y'>` 를 냈다.\
  이 형태에서는 `*` 가 없어도 된다.
- 곁들여 — 같은 출력에 **`bipush 63`**(= `0b111111`)이 보인다.\
  `xs.joinToString()` 이 **파라미터 여섯 개를 전부 생략한 호출**이라는 뜻이다. stdlib 도 같은 기계를 쓴다.

### 10. `List` 가 싸다 · 배열이면 spread 의 대가는 **복사 한 번**

**왜 그런가**

```text
   호출자가 들고 있는 것      vararg 파라미터        List 파라미터      Array 파라미터
   +----------------------+  +------------------+  +---------------+  +---------------+
   | List                 |  | toTypedArray() + |  | 그대로 ★      |  | toTypedArray()|
   |                      |  | copyOf           |  |               |  |               |
   | 배열                 |  | *arr -> copyOf ★ |  | toList()      |  | 그대로 ★      |
   | 낱개 값들            |  | f(a, b, c) ★     |  | listOf(a,b,c) |  | arrayOf(a,b,c)|
   +----------------------+  +------------------+  +---------------+  +---------------+
```

- 호출자가 **이미 `List`** 면 `List<T>` 파라미터가 항상 싸다 — 변환도 복사도 없다.\
  `vararg` 로 받으면 **배열로 바꾸고 다시 복사**까지 두 번 지난다.
- 호출자가 **이미 배열**이면 `vararg` 의 대가는 **`Arrays.copyOf` 한 번**이다(1번·2번).
- 그 대가를 피하려면 시그니처를 **`xs: Array<out T>`** 로 바꾼다 — 디스크립터가 같아서(3번) **호출부만 달라진다.**\
  대신 낱개로 부르는 편의는 잃는다.
- ★ **이 문서가 재지 않은 것 — 시간이다.** 위 표는 전부 **`javap` 에 보이는 복사·할당의 유무**이고,\
  "어느 쪽이 얼마나 빠른가" 는 한 번도 측정하지 않았다.

### 11. 다른 주제와 잇기

- **기본 인자·이름 붙인 인자·`@JvmOverloads` → [08번 주제](../08-function-declaration-default-and-named-args/)** 가 정본이다.\
  이 문서 9번의 `vararg$default` 와 `bipush 63` 이 거기서 온 기계다.
- **연산자 규약 표 전체 → 목록의 31번 주제**(연산자 오버로딩·중위 함수·`invoke` 규약)가 정본이다.\
  `plus`·`get`·`invoke`·`iterator`·`contains` 가 각각 어떤 기호·문법으로 풀리는지가 거기 있다.\
  여기는 **`infix` 라는 호출 형태와 그 우선순위**만 다뤘다.
- **람다가 바깥 `var` 를 잡는 것 → [목록의 10번 주제](../10-lambdas-and-higher-order-functions/)**(람다와 고차 함수 — `it`·마지막 인자 람다·클로저)가 정본이다.\
  이 문서 5번·6번은 **로컬 함수 쪽**만 실측했다. 람다에서도 `Ref` 상자가 쓰이는지는 거기서 확인한다.
- **`step`·`downTo` 가 중위 함수인 것 → [07번 주제](../07-loops-ranges-and-labels/)** 에서 쓰였다.\
  `1..10 step 2` 가 `(1..10) step 2` 로 읽히는 근거가 이 문서 8번의 우선순위 표다.

---

## 실행 검증

**환경**

```text
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
openjdk version "21.0.5" 2024-10-15 LTS
OpenJDK Runtime Environment Temurin-21.0.5+11 (build 21.0.5+11-LTS)
OpenJDK 64-Bit Server VM Temurin-21.0.5+11 (build 21.0.5+11-LTS, mixed mode, sharing)
```

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `icode.kt` | `vararg` 디스크립터·낱개/spread/혼합/빈 호출의 바이트코드 | `kotlinc` → `javap -s -p`·`javap -c -p` |
| `ex.kt` | spread 가 원본을 안 바꾸는 것·`===` 비교·`vararg` 중간 배치·로컬 함수 클로저·중위 호출·우선순위 | `kotlinc` → `java` |
| `bad1.kt` | `vararg` 가 둘이면 거부 · 뒤 파라미터를 위치로 넘기면 거부 | `kotlinc` (에러 3줄) |
| `local.kt` | 로컬 함수가 **클래스를 안 만드는 것** · 캡처가 파라미터가 되는 것 · `Ref$IntRef` | `kotlinc` → `ls` → `javap -s -p`·`javap -c -p` |
| `lam.kt` | 로컬 함수 대 람다 — `invokestatic` 대 `invokedynamic` + 박싱 | `kotlinc` → `ls` → `javap -c -p` |
| `bad2.kt` | `infix` 조건 넷 중 셋이 거부되고 **기본값만 통과하는 것** | `kotlinc` (에러 4건) |
| `inf.kt` | 기본값 있는 `infix` 가 **중위로도 일반으로도 도는 것** | `kotlinc` → `java` |
| `inf2.kt` | 중위 형태로 인자를 생략하면 **파서가 죽는 것** | `kotlinc` (에러 1건) |
| `prec.kt` · `prec3.kt` | 중위 우선순위 6식 · 접두 연산자와의 충돌 | `kotlinc` → `java` · `kotlinc` (에러 1건) |
| `vd.kt` · `vd2.kt` | `vararg` + 기본값 · 이름으로 배열 넘기기 · `$default` 안의 기본값 | `kotlinc` → `java` → `javap -c -p` |

**구현 의존 항목** — `Arrays.copyOf` 라는 선택, `IntSpreadBuilder` 라는 클래스 이름과 `add`/`addSpread`/`toArray`,
`바깥$안` 이라는 로컬 함수 이름과 `private static`, 캡처가 앞에 붙는 파라미터가 되는 것,
`Ref$IntRef` 라는 상자 이름, 람다가 `invokedynamic` + `Function1` 인 것, `ACC_VARARGS` 플래그 —
전부 **이 컴파일러 버전 + 기본 타깃의 산출물**이다.\
반면 "`vararg` 는 함수 안에서 배열" · "인자 0개면 빈 배열" · "`vararg` 는 하나뿐" ·
"뒤 파라미터는 이름 전용" · "호출자의 배열이 안 바뀐다" · "`infix` 는 멤버/확장·파라미터 1개" ·
"중위 호출의 우선순위" 는 **언어 규칙**이라 타깃과 무관하다.

**★ 던져 봤더니 예상과 달랐던 것 — 세 건**

1. ★★ **로컬 함수가 합성 클래스를 안 만든다.**\
   "람다처럼 클래스가 하나 생기겠지" 라고 예상하고 `ls` 를 찍었는데 **`LocalKt.class` 하나뿐**이었다.\
   캡처한 값은 **객체의 필드가 아니라 메서드의 파라미터**가 됐다.
2. ★★ **`infix` 파라미터에 기본값을 줄 수 있다.**\
   공식 문서가 명시적으로 금지하는 조항인데 **kotlinc 2.4.20 은 에러도 경고도 내지 않았고 실제로 돌았다.**\
   같은 파일에서 `vararg`·파라미터 개수·최상위 함수는 **전부 거부**돼서, 조건 넷 중 **하나만** 안 지켜진다.
3. **`vararg` 에도 기본값을 줄 수 있다.**\
   `vararg xs: Int = intArrayOf(1, 2)` 가 통과했고 `$default` 안에서 `newarray` 로 만들어졌다.

**안 잰 것 · 못 잰 것**

- **성능은 한 번도 재지 않았다.** `javap` 로 본 것은 **복사·할당·박싱의 유무**까지다.
- **얕은 복사의 경계를 끝까지 던지지 않았다** — `IntArray`·`Array<String>` 만 spread 해 봤고,
  **가변 객체를 담은 배열**(`Array<StringBuilder>`)로 "안의 객체는 공유된다" 를 보이지는 않았다.
- `SpreadBuilder` 는 **`Int` 판만** 찍었다. 참조 타입용·다른 원시 타입용 판은 이름만 짚었다.
