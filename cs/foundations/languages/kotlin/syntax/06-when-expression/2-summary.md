# kotlin/syntax/06 — `when` 식: 주체 있는/없는 형태·완전성·guard (2.2+) — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Conditions and loops](https://kotlinlang.org/docs/control-flow.html) · [Sealed classes and interfaces](https://kotlinlang.org/docs/sealed-classes.html) · [언어 기능·제안 상태표](https://kotlinlang.org/docs/kotlin-language-features-and-proposals.html)(guard 조건의 Stable 버전 확인).
> **실행 검증** — 모든 출력·에러·경고·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javap` 에서 실제로 얻었다.\
> `kotlinc` 18회 · `java` 3회 · `javap` 9회. 컴파일 실패 시나리오 7벌 + 분리 컴파일 시나리오 2벌.
> ⚠️ **`-jvm-target` 을 밝히지 않은 바이트코드 주장은 반쪽이다.** `kotlinc` 의 기본값은 **1.8**(`major version: 52`)이고,\
> 이 문서의 역어셈블은 **기본값**이 정본이다. **`-jvm-target 21` 에서 `sealed` 쪽 한 자리가 통째로 달라진다** — 그 자리를 (6)에 따로 세웠다.
> **버전** — `when` 자체는 1.0. **guard 조건(`is T if …`)은 2.2.0** — 이 환경에서 `-language-version 2.1` 로 **거부되는 것을 실측**했다.
> **경계** — `sealed` 계층을 **어떻게 설계하나**의 정본은 [목록의 **23번 주제**](../23-sealed-classes-and-when-exhaustiveness/)(`sealed`+완결성)와 [`../../언어-특성/README.md`](../../언어-특성/README.md) §3 이다.\
> 여기는 **「`when` 이 언제 `else` 를 요구하고 그것이 JVM 에서 무엇으로 내려앉나」** 만 다룬다.\
> **Java `switch` 쪽 정본은 [`../../../java/syntax/21-switch-statement-and-expression/`](../../../java/syntax/21-switch-statement-and-expression/)** 다.
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**Java 의 `switch` 는 「어디로 뛰어들지 정하는 표지판」이고, Kotlin 의 `when` 은 「값을 하나 내놓는 자판기」다.**

자판기는 **버튼이 뭐든 반드시 뭔가를 내놓아야** 한다.\
그래서 `when` 을 **값으로 쓰는 순간** 컴파일러가 묻는다 — "이 입력에는 뭘 내놓을 건데?"\
그 질문이 바로 **완전성(exhaustiveness)** 이다.

> **완전성(exhaustiveness)** — 있을 수 있는 모든 입력에 대해 갈 가지가 하나는 있다는 것.\
> 예: `Boolean` 에 `true` 가지만 적으면 `false` 일 때 내놓을 값이 없다 — 완전하지 않다.

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 자판기 — 반드시 뭘 내놓는다 | `when` 을 **식**으로 쓴 것 (값이 필요하다) |
| 표지판 — 그냥 길을 가리킨다 | `when` 을 **문**으로 쓴 것 (값이 필요 없다) |
| "버튼이 몇 개인지 세어 볼 수 있는" 자판기 | 유한한 주체 타입 — `enum`·`sealed`·`Boolean` |
| "버튼이 무한한" 자판기 | 무한한 주체 타입 — `Int`·`String`·`Any` |
| 품절 버튼 | 빠뜨린 가지 |
| 「아무거나」 버튼 | `else` |
| 자판기 안쪽의 번호판 | `tableswitch` / `lookupswitch` |
| 재고표가 바뀌었는데 자판기는 그대로 | 분리 컴파일 — `NoWhenBranchMatchedException` |

```text
                      when (x) { ... }
                            │
              ┌─────────────┴──────────────┐
              │                            │
        값이 필요한가?                값이 필요 없나?
        (식 — 대입·반환·보간)          (문 — 그냥 실행)
              │                            │
              ▼                            ▼
        반드시 완전해야 한다          주체가 유한하면 그래도 완전해야 한다 ★
                                     주체가 무한하면 아무 가지나 좋다
```

★ 표시한 칸이 이 주제에서 **가장 자주 틀리는 자리**다.\
"식이면 `else` 필수, 문이면 자유" 라고 외우면 **절반만 맞다** — 아래 (2)에서 실측으로 뒤집는다.

## 이 주제가 답하려는 질문

1. `when` 에 `else` 가 **언제 필수이고 언제 아닌가** — 기준은 「식이냐 문이냐」인가, 「주체 타입이 뭐냐」인가.
2. `sealed`·`enum` 의 완전성은 **누가 언제 검사하나** — 컴파일 타임뿐인가, 런타임에도 뭔가 남나.
3. `when` 은 **무엇으로 컴파일되나** — `switch` 명령인가 `if` 사슬인가. **주체 타입에 따라 갈리나.**

## 동작 방식

### (1) `when` 은 문이 아니라 식이다 — 그래서 값이 나온다

**언제 쓰나** — Java 의 `switch` 로 변수를 채우려고 `String result;` 를 먼저 선언하던 습관을 버릴 때.

```kotlin
fun noSubject(x: Int): String = when {
    x < 0 -> "neg"
    x == 0 -> "zero"
    else -> "pos"
}
```

**출력** (`javap -c -p out/IcodeKt.class`)

```text
  public static final java.lang.String noSubject(int);
    Code:
       0: nop
       1: iload_0
       2: ifge          10
       5: ldc           #83                 // String neg
       7: goto          21
      10: iload_0
      11: ifne          19
      14: ldc           #85                 // String zero
      16: goto          21
      19: ldc           #87                 // String pos
      21: areturn
```

```text
   주체 없는 when { }            주체 있는 when (x) { }
   +-----------------------+     +--------------------------+
   | 조건 -> 값            |     | 값  -> 값                |
   | 조건 -> 값            |     | 값  -> 값                |
   | 각 조건이 Boolean     |     | 각 가지를 x 와 비교       |
   +-----------------------+     +--------------------------+
      = if / else if 사슬          = 비교 또는 switch 명령
```

그림 해설:

- 주체 없는 `when { }` 은 **`if`/`else if` 사슬 그대로**다 — `ifge`·`ifne` 두 분기뿐이고 객체가 없다.
- **값을 내는 자리에 바로 쓸 수 있다** — 위 함수는 `= when { … }` 이 통째로 반환값이다.
- 가지 몸통이 여러 줄이면 `{ }` 로 감싸고 **마지막 식이 그 가지의 값**이 된다.

비용 — 분기 몇 번. 객체 할당 0.

### (2) ★★ 완전성을 정하는 것은 「식이냐 문이냐」가 아니라 **주체 타입**이다

**언제 쓰나** — "`when` 을 문으로 쓰면 `else` 안 써도 된다" 를 검증할 때.

무한한 주체(`Int`)에서는 통설이 맞다.

```kotlin
fun asStatement(x: Int) {
    when (x) {
        1 -> println("one")
        2 -> println("two")
    }
}

fun asExpression(x: Int): String = when (x) {
    1 -> "one"
    2 -> "two"
}
```

**출력** (`kotlinc bad1.kt`)

```text
bad1.kt:8:36: error: 'when' expression must be exhaustive. Add an 'else' branch.
fun asExpression(x: Int): String = when (x) {
                                   ^^^^
```

`asStatement` 는 **에러도 경고도 없다.** 에러는 식 쪽 하나뿐이다.

그런데 주체를 `Boolean`·`enum`·`sealed` 로 바꾸면 **문에서도 에러가 난다.**

```kotlin
fun stmtBool(b: Boolean) {
    when (b) { true -> println("t") }
}
fun stmtNullableBool(b: Boolean?) {
    when (b) { true -> println("t"); false -> println("f") }
}
```

**출력** (`kotlinc bad6.kt` — `Int`·`String` 주체의 같은 형태는 이 파일에서 **통과했다**)

```text
bad6.kt:2:5: error: 'when' expression must be exhaustive. Add the 'false' branch or an 'else' branch.
    when (b) {
    ^^^^
bad6.kt:20:5: error: 'when' expression must be exhaustive. Add the 'null' branch or an 'else' branch.
    when (b) {
    ^^^^
```

**출력** (`kotlinc bad5.kt` — `enum`·`sealed` 주체, **둘 다 문**)

```text
bad5.kt:8:5: error: 'when' expression must be exhaustive. Add the 'BLUE' branch or an 'else' branch.
    when (c) {
    ^^^^
bad5.kt:15:5: error: 'when' expression must be exhaustive. Add the 'is Square' branch or an 'else' branch.
    when (s) {
    ^^^^
```

```text
                 주체 타입이 유한한가?
                 (enum · sealed · Boolean · 그 nullable)
                         │
            ┌────────────┴────────────┐
           예                         아니오 (Int · String · Any …)
            │                              │
   문이든 식이든 완전해야 한다     ┌────────┴────────┐
   (가지를 다 적거나 else)        식              문
            │                    │                │
            ▼                    ▼                ▼
      가지 누락 = 에러        else 필수       아무거나 좋다
```

- ★ **에러 문구가 두 갈래다.** 무한 주체는 `Add an 'else' branch.` 이고,\
  유한 주체는 **`Add the 'BLUE' branch or an 'else' branch.`** — **빠진 가지 이름을 대 준다.**\
  이 한 낱말 차이가 "이 타입은 셀 수 있다" 는 컴파일러의 선언이다.
- ★ 에러 메시지가 문 쪽에서도 **`'when' expression must be exhaustive`** 라고 말한다 —\
  컴파일러는 문/식을 구분해 말하지 않는다. **유한 주체에서는 `when` 을 그냥 「식」으로 취급**한다.
- `Boolean?` 은 가지가 셋이다(`true`·`false`·`null`). nullable 이 붙으면 **`null` 가지가 하나 늘어난다.**

비용 — 0. 전부 컴파일 타임이다.

### (3) ★★ 주체 타입마다 다른 명령으로 내려간다 — `tableswitch`·`lookupswitch`·`if` 사슬

**언제 쓰나** — "`when` 은 `switch` 보다 느리다" 같은 말을 검증할 때.

**출력** (`javap -c -p out/IcodeKt.class` — 촘촘한 `Int` 주체)

```text
  public static final java.lang.String onInt(int);
    Code:
       0: iload_0
       1: tableswitch   { // 1 to 3
                     1: 28
                     2: 33
                     3: 38
               default: 43
          }
      28: ldc           #9                  // String one
      30: goto          45
      33: ldc           #11                 // String two
      35: goto          45
      38: ldc           #13                 // String three
      40: goto          45
      43: ldc           #15                 // String many
      45: areturn
```

**출력** (같은 파일 — 값이 흩어진 `Int` 주체: `1`·`100`·`10000`)

```text
  public static final java.lang.String onIntSparse(int);
    Code:
       0: iload_0
       1: lookupswitch  { // 3
                     1: 36
                   100: 41
                 10000: 46
               default: 51
          }
      36: ldc           #9                  // String one
      38: goto          53
      41: ldc           #22                 // String hundred
      43: goto          53
      46: ldc           #24                 // String myriad
      48: goto          53
      51: ldc           #15                 // String many
      53: areturn
```

```text
   tableswitch  (값이 촘촘할 때)        lookupswitch (값이 흩어질 때)
   +---------------------------+       +---------------------------+
   | 1 -> 28                   |       | (1, 36)                   |
   | 2 -> 33   ← 인덱스 계산   |       | (100, 41)  ← 키를 찾는다  |
   | 3 -> 38     한 번이면 끝  |       | (10000, 46)               |
   +---------------------------+       +---------------------------+
     점프 표를 배열로 만든다             정렬된 쌍 목록을 이진 탐색
```

- ★ **같은 `Int` 주체인데 명령이 갈렸다.** 고른 것은 `when` 문법이 아니라 **가지 값들의 분포**다.
- 이것은 Java `switch` 가 오래전부터 하던 것과 **같은 선택**이다 — 정본은 [`../../../java/syntax/21-switch-statement-and-expression/`](../../../java/syntax/21-switch-statement-and-expression/).
- ★ **`Long` 주체에서는 `switch` 명령이 아예 안 나온다.**

**출력** (같은 파일 — `Long` 주체)

```text
  public static final java.lang.String onLong(long);
    Code:
       0: lload_0
       1: lstore_2
       2: lload_2
       3: lconst_1
       4: lcmp
       5: ifne          13
       8: ldc           #9                  // String one
      10: goto          28
      13: lload_2
      14: ldc2_w        #90                 // long 2l
      17: lcmp
      18: ifne          26
      21: ldc           #11                 // String two
      23: goto          28
      26: ldc           #15                 // String many
      28: areturn
```

- **JVM 의 `tableswitch`/`lookupswitch` 는 `int` 키만 받는다.** 그래서 `Long` 은 `lcmp` 비교 사슬이 된다.\
  `when` 이 느려진 게 아니라 **JVM 에 그 명령이 없는 것**이다.

비용 — `tableswitch` 는 가지 수와 무관하게 점프 한 번. `lookupswitch` 는 가지 수의 로그. `if` 사슬은 가지 수에 비례.

### (4) `String` 주체는 두 단으로 비교한다 — `hashCode` 로 좁히고 `equals` 로 확인한다

**언제 쓰나** — 문자열 `when` 의 비용을 따질 때.

**출력** (`javap -c -p out/IcodeKt.class`)

```text
  public static final int onString(java.lang.String);
    Code:
       0: aload_0
       1: ldc           #28                 // String s
       3: invokestatic  #34                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_0
       7: astore_1
       8: aload_1
       9: invokevirtual #38                 // Method java/lang/String.hashCode:()I
      12: tableswitch   { // 97 to 99
                    97: 40
                    98: 52
                    99: 64
               default: 88
          }
      40: aload_1
      41: ldc           #40                 // String a
      43: invokevirtual #44                 // Method java/lang/String.equals:(Ljava/lang/Object;)Z
      46: ifne          76
      49: goto          88
      52: aload_1
      53: ldc           #46                 // String b
      55: invokevirtual #44                 // Method java/lang/String.equals:(Ljava/lang/Object;)Z
      58: ifne          80
      61: goto          88
      64: aload_1
      65: ldc           #48                 // String c
      67: invokevirtual #44                 // Method java/lang/String.equals:(Ljava/lang/Object;)Z
      70: ifne          84
      73: goto          88
      76: iconst_1
      77: goto          89
      80: iconst_2
      81: goto          89
      84: iconst_3
      85: goto          89
      88: iconst_0
      89: ireturn
```

```text
   "b" ──> hashCode() = 98
            │
            ▼
   tableswitch { 97 -> ..., 98 -> ..., 99 -> ... }
            │
            ▼ (해시가 같다고 문자열이 같은 건 아니다)
   equals("b") ──> true ──> 2 번 가지
                └─ false ─> default
```

- **해시로 후보를 하나로 좁힌 뒤 `equals` 로 확인한다.** 해시 충돌이 있어도 `equals` 가 걸러 준다.
- 여기서는 `"a"`·`"b"`·`"c"` 의 해시가 97·98·99 로 촘촘해 `tableswitch` 가 나왔다 —\
  **(3)의 분포 규칙이 해시값에 그대로 다시 적용된 것**이다.
- 맨 앞의 `checkNotNullParameter` 는 `when` 과 무관하다 — [03번 주제](../03-null-safe-types/)의 그 검사다.

비용 — `hashCode` 한 번 + `equals` 한 번.

### (5) ★★ `enum` 주체는 `ordinal` 을 한 번 갈아 끼운다 — `$EnumSwitchMapping`

**언제 쓰나** — `enum` 의 `when` 이 왜 클래스를 하나 더 만드는지 물을 때.

```kotlin
fun onEnum(c: Color): Int = when (c) {
    Color.RED -> 1
    Color.GREEN -> 2
    Color.BLUE -> 3
}
```

**출력** (`ls out/` — 소스에 없던 클래스가 하나 생겼다)

```text
Circle.class
Color.class
IcodeKt$WhenMappings.class
IcodeKt.class
META-INF
Shape.class
Square.class
Tri.class
```

**출력** (`javap -c -p out/IcodeKt.class`)

```text
  public static final int onEnum(Color);
    Code:
       0: aload_0
       1: ldc           #48                 // String c
       3: invokestatic  #34                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_0
       7: getstatic     #57                 // Field IcodeKt$WhenMappings.$EnumSwitchMapping$0:[I
      10: swap
      11: invokevirtual #62                 // Method Color.ordinal:()I
      14: iaload
      15: tableswitch   { // 1 to 3
                     1: 40
                     2: 44
                     3: 48
               default: 52
          }
      40: iconst_1
      41: goto          60
      44: iconst_2
      45: goto          60
      48: iconst_3
      49: goto          60
      52: new           #64                 // class kotlin/NoWhenBranchMatchedException
      55: dup
      56: invokespecial #68                 // Method kotlin/NoWhenBranchMatchedException."<init>":()V
      59: athrow
      60: ireturn
```

**출력** (`javap -c -p 'out/IcodeKt$WhenMappings.class'`)

```text
Compiled from "icode.kt"
public final class IcodeKt$WhenMappings {
  public static final int[] $EnumSwitchMapping$0;

  static {};
    Code:
       0: invokestatic  #14                 // Method Color.values:()[LColor;
       3: arraylength
       4: newarray       int
       6: astore_0
       7: nop
       8: aload_0
       9: getstatic     #18                 // Field Color.RED:LColor;
      12: invokevirtual #22                 // Method Color.ordinal:()I
      15: iconst_1
      16: iastore
      17: goto          21
      20: astore_1
      21: nop
      22: aload_0
      23: getstatic     #25                 // Field Color.GREEN:LColor;
      26: invokevirtual #22                 // Method Color.ordinal:()I
      29: iconst_2
      30: iastore
      31: goto          35
      34: astore_1
      35: nop
      36: aload_0
      37: getstatic     #28                 // Field Color.BLUE:LColor;
      40: invokevirtual #22                 // Method Color.ordinal:()I
      43: iconst_3
      44: iastore
      45: goto          49
      48: astore_1
      49: aload_0
      50: putstatic     #32                 // Field $EnumSwitchMapping$0:[I
      53: return
    Exception table:
       from    to  target type
           7    17    20   Class java/lang/NoSuchFieldError
          21    31    34   Class java/lang/NoSuchFieldError
          35    45    48   Class java/lang/NoSuchFieldError
}
```

```text
   Color.GREEN
        │ ordinal()   ← 지금 이 순간의 Color 클래스가 답한다
        ▼
       [1]                  ← 컴파일 시점의 순서가 아니다
        │
        │  $EnumSwitchMapping$0 = [?, 1, 2, 3] 중 인덱스 1
        ▼
       [2]                  ← 이 소스가 적은 「가지 번호」
        │
        ▼
   tableswitch { 1,2,3 }
```

- ★ **`ordinal()` 을 바로 `switch` 하지 않는다.** 한 겹을 더 둔 이유는 **분리 컴파일**이다 —\
  `enum` 의 상수 순서가 바뀌어도 `WhenMappings` 의 `static {}` 이 **로드 시점에 다시 만들어진다.**
- `static {}` 이 상수마다 **`NoSuchFieldError` 를 따로 잡는다** — 상수가 사라져도 그 칸만 0으로 남고 통째로 죽지 않는다.
- ★ **가지를 다 적었는데도 `default` 에 `NoWhenBranchMatchedException` 을 던지는 코드가 남았다.** 왜인지는 (7)에서 실측한다.
- 같은 구조를 Java `switch` 도 쓴다(`$SwitchMap`) — [`../../../java/syntax/21-switch-statement-and-expression/`](../../../java/syntax/21-switch-statement-and-expression/)에 그 대응이 있다.

비용 — 배열 읽기 한 번 + 점프 한 번. 클래스 파일이 하나 는다.

### (6) ★★ `sealed` 주체는 `-jvm-target` 에 따라 **완전히 다른 코드**가 된다

**언제 쓰나** — 바이트코드를 근거로 뭔가를 주장하기 직전.

```kotlin
sealed interface Shape
class Circle : Shape
class Square : Shape
class Tri : Shape

fun onSealed(s: Shape): Int = when (s) {
    is Circle -> 1
    is Square -> 2
    is Tri -> 3
}
```

**출력** (`kotlinc icode.kt -d out/` — 기본 `-jvm-target 1.8` · `javap -c -p`)

```text
  public static final int onSealed(Shape);
    Code:
       0: aload_0
       1: ldc           #28                 // String s
       3: invokestatic  #34                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_0
       7: astore_1
       8: aload_1
       9: instanceof    #73                 // class Circle
      12: ifeq          19
      15: iconst_1
      16: goto          49
      19: aload_1
      20: instanceof    #75                 // class Square
      23: ifeq          30
      26: iconst_2
      27: goto          49
      30: aload_1
      31: instanceof    #77                 // class Tri
      34: ifeq          41
      37: iconst_3
      38: goto          49
      41: new           #64                 // class kotlin/NoWhenBranchMatchedException
      44: dup
      45: invokespecial #68                 // Method kotlin/NoWhenBranchMatchedException."<init>":()V
      48: athrow
      49: ireturn
```

**출력** (`kotlinc icode.kt -jvm-target 21 -d out21/` · `javap -c -p`)

```text
  public static final int onSealed(Shape);
    Code:
       0: aload_0
       1: ldc           #28                 // String s
       3: invokestatic  #34                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_0
       7: iconst_0
       8: invokedynamic #87,  0             // InvokeDynamic #0:typeSwitch:(Ljava/lang/Object;I)I
      13: tableswitch   { // 0 to 2
                     0: 40
                     1: 44
                     2: 48
               default: 52
          }
      40: iconst_1
      41: goto          60
      44: iconst_2
      45: goto          60
      48: iconst_3
      49: goto          60
      52: new           #64                 // class kotlin/NoWhenBranchMatchedException
      55: dup
      56: invokespecial #68                 // Method kotlin/NoWhenBranchMatchedException."<init>":()V
      59: athrow
      60: ireturn
```

**출력** (`javap -v -p out21/IcodeKt.class` 의 부트스트랩 표)

```text
BootstrapMethods:
  0: #84 REF_invokeStatic java/lang/runtime/SwitchBootstraps.typeSwitch:(Ljava/lang/invoke/MethodHandles$Lookup;Ljava/lang/String;Ljava/lang/invoke/MethodType;[Ljava/lang/Object;)Ljava/lang/invoke/CallSite;
    Method arguments:
      #73 Circle
      #75 Square
      #77 Tri
```

```text
   -jvm-target 1.8 / 17 / 20            -jvm-target 21
   +--------------------------+         +----------------------------+
   | instanceof Circle ?      |         | invokedynamic typeSwitch   |
   | instanceof Square ?      |         |   -> 인덱스 0/1/2 를 받아   |
   | instanceof Tri ?         |         | tableswitch 로 한 번에 점프 |
   +--------------------------+         +----------------------------+
     가지 수에 비례하는 검사              JDK 21 의 SwitchBootstraps
```

- ★★ **같은 소스가 타깃 하나 때문에 「`instanceof` 사슬」과 「`invokedynamic`」으로 갈린다.**\
  경계는 정확히 **21** 이다 — 17·20 에서는 `invokedynamic` 이 **0개**, 21 에서 **1개**였다(세 타깃을 다 찍어 세었다).
- ★ `java.lang.runtime.SwitchBootstraps.typeSwitch` 는 **Java 21 의 패턴 `switch` 가 쓰는 바로 그 부트스트랩**이다.\
  Kotlin 의 `when` 과 Java 의 패턴 `switch` 가 **같은 JVM 기계 위에서 만난다.**
- 그래서 **「Kotlin 의 `sealed when` 은 `instanceof` 사슬이다」는 플래그를 안 밝히면 틀린 문장**이 된다.

비용 — 타깃 1.8 에서는 가지 수에 비례하는 `instanceof`. 타깃 21 에서는 첫 호출에 call site 를 엮고 그 뒤로는 점프 한 번.

### (7) ★★ 완전성은 **컴파일 시점의 약속**이다 — 런타임에는 깨질 수 있다

**언제 쓰나** — (5)·(6)의 `default` 에 남아 있는 `NoWhenBranchMatchedException` 이 왜 필요한지 물을 때.

`enum` 상수가 둘일 때 `else` 없이 컴파일한다.

```kotlin
// color.kt
enum class Color { RED, GREEN }

// lib.kt
fun name(c: Color): String = when (c) {
    Color.RED -> "빨강"
    Color.GREEN -> "초록"
}
fun main() {
    println("RED  -> " + name(Color.RED))
    val unknown = Color.valueOf("BLUE")
    println("BLUE -> " + try { name(unknown) } catch (e: Throwable) { "${e::class.qualifiedName} / message=${e.message}" })
}
```

그다음 **`enum` 만** 상수 셋으로 다시 컴파일하고 `lib.class` 는 그대로 둔다.

**출력** (`kotlinc color.kt lib.kt` → `kotlinc color.kt` 재컴파일 → `java LibKt`)

```text
(1) 상수 둘 — else 없이 컴파일 통과)
(2) enum 만 재컴파일)
--- RUN ---
RED  -> 빨강
BLUE -> kotlin.NoWhenBranchMatchedException / message=null
```

```text
   컴파일 시점                     실행 시점
   +----------------------+        +------------------------+
   | Color = {RED, GREEN} |        | Color = {RED,GREEN,BLUE}|
   | when 이 둘을 다 덮음  |        | lib.class 는 안 고쳐짐  |
   | -> else 불필요        |        | -> BLUE 가 default 로   |
   +----------------------+        +------------------------+
                                        │
                                        ▼
                         kotlin.NoWhenBranchMatchedException
```

- ★ **컴파일러가 "완전하다" 고 판정한 `when` 이 런타임에 어느 가지에도 안 걸렸다.**\
  그래서 `default` 의 `athrow` 가 **죽은 코드가 아니다.**
- 메시지는 **`null` 이다** — [03번 주제](../03-null-safe-types/)의 `!!` 와 같은 모양이다.\
  어느 `when` 이 터졌는지는 **스택 트레이스의 줄 번호로만** 안다.
- 이것이 **「`sealed` 를 쓰면 컴파일이 깨져서 안전하다」의 정확한 범위**다 —\
  깨지는 것은 **같이 다시 컴파일했을 때**다. 라이브러리를 갈아 끼우면 런타임 예외가 된다.
- `sealed` 쪽도 같은 검사가 붙어 있다((6)의 `41: new … NoWhenBranchMatchedException`).

**같이 컴파일하면 정말 깨지나** — 깨진다.

**출력** (하위 타입 둘로 컴파일 → 셋으로 늘려 재컴파일)

```text
===== 1) 두 하위 타입 — else 없이 컴파일 =====
(컴파일 성공 — 출력 없음)
원
사각형
===== 2) 하위 타입 하나 추가 후 재컴파일 =====
use.kt:1:30: error: 'when' expression must be exhaustive. Add the 'is Triangle' branch or an 'else' branch.
fun name(s: Shape): String = when (s) {
                             ^^^^
```

- ★ **이 에러가 `sealed` 의 값어치 그 자체다.** 타입을 늘리면 **고쳐야 할 자리를 컴파일러가 전수로 찾아 준다.**\
  `else` 를 적어 두면 **이 에러가 안 난다** — 그래서 `sealed` 주체에는 `else` 를 안 쓰는 것이 관용이다.
- 계층 설계 쪽 정본은 [목록의 **23번 주제**](../23-sealed-classes-and-when-exhaustiveness/)와 [`../../언어-특성/README.md`](../../언어-특성/README.md) §3 이다.

비용 — 런타임 검사 0(가지에 걸리면 그냥 점프). 안 걸릴 때만 객체 하나와 예외.

### (8) 가지의 형태 — `is`·`in`·쉼표·guard, 그리고 **첫 일치가 이긴다**

**언제 쓰나** — `when` 한 덩어리로 분기를 다 적을 때.

```kotlin
fun kinds(x: Any): String = when (x) {
    is String -> "문자열 길이=${x.length}"
    in 1..9 -> "한 자리 수"
    1000, 2000 -> "천 단위"
    is Int -> "그 외 Int"
    else -> "모름"
}

fun guarded(x: Any): String = when (x) {
    is Int if x > 100 -> "큰 Int"
    is Int -> "작은 Int"
    else -> "Int 아님"
}

fun firstMatch(x: Int): String = when {
    x > 0 -> "양수"
    x > 100 -> "백 초과"
    else -> "그 외"
}
```

**출력** (`ex.kt`)

```text
--- 2. 첫 일치가 이긴다 ---
firstMatch(500) = 양수
--- 3. is / in / 콤마 ---
kinds(가나) = 문자열 길이=2
kinds(5) = 한 자리 수
kinds(1000) = 천 단위
kinds(42) = 그 외 Int
kinds(3.14) = 모름
--- 4. guard (2.2+) ---
guarded(500) = 큰 Int
guarded(7) = 작은 Int
guarded(x) = Int 아님
```

```text
   when (x) {                 x = 500
     x > 0    ────────────>   참  → "양수" 를 내고 끝
     x > 100                  ← 여기는 영원히 안 온다
     else
   }
   ★ 컴파일러는 이것을 경고하지 않았다 (실측)
```

- **위에서 아래로 첫 일치**다. `firstMatch(500)` 이 `"백 초과"` 가 아니라 `"양수"` 인 이유다.
- ★ **닿을 수 없는 가지에 경고가 안 붙었다** — `when { }` 의 조건은 임의의 식이라 컴파일러가 포함 관계를 모른다.\
  **순서가 곧 의미**다.
- `is String` 가지 안에서 `x.length` 가 된다 — **스마트 캐스트**다([04번 주제](../04-smart-casts/)가 정본).
- `in 1..9` 는 **`contains` 규약**이고, 쉼표는 **or** 다(`1000, 2000`).
- **guard(`is Int if x > 100`)는 2.2.0** 이고 **주체 있는 `when` 에서만** 된다.

**출력** (`kotlinc bad7.kt` — 주체 없는 `when` 에 guard 를 달면)

```text
bad7.kt:16:11: error: guard statements are only allowed in 'when' with subject.
    x > 0 if x < 10 -> "a"
          ^^^^^^^^^
```

**출력** (`kotlinc -language-version 2.1 lv.kt` — 버전 경계를 컴파일러에게 직접 물었다)

```text
warning: language version 2.1 is deprecated and its support will be removed in a future version of Kotlin. Update the version to 2.2.
lv.kt:4:57: error: the feature "break continue in inline lambdas" is only available since language version 2.2
    for (i in 1..3) { listOf(1,2).forEach { if (i == 2) break; sb.append(i) } }
                                                        ^^^^^
lv.kt:7:43: error: the feature "when guards" is only available since language version 2.2
fun c(x: Any): String = when (x) { is Int if x > 5 -> "big"; else -> "n" }
                                          ^^^^^^^^
```

비용 — 가지 형태에 따라 (3)\~(6) 중 하나.

### (9) 중복 가지는 경고, 남는 `else` 도 경고

**언제 쓰나** — 큰 `when` 을 리팩터링한 직후.

```kotlin
fun dup(x: Int): String = when (x) {
    1 -> "a"
    1 -> "b"
    else -> "c"
}

fun dupBool(x: Boolean): String = when (x) {
    true -> "t"
    false -> "f"
    else -> "?"
}
```

**출력** (`kotlinc bad4.kt`)

```text
bad4.kt:3:5: warning: duplicate branch condition in 'when'.
    1 -> "b"
    ^
bad4.kt:10:5: warning: 'when' is exhaustive so 'else' is redundant here.
    else -> "?"
    ^^^^
```

- **둘 다 경고다 — 컴파일은 통과한다.** 중복 가지는 **위엣것이 이기고 아랫것이 죽는다.**
- 뒤엣것(`'when' is exhaustive so 'else' is redundant`)이 특히 값어치가 있다 —\
  **`sealed` 주체에 `else` 를 달면 이 경고가 「지금은」 뜨지만, 하위 타입이 늘면 경고가 조용히 사라진다.**\
  즉 **경고가 사라지는 것이 곧 컴파일 안전망이 꺼진 신호**다.

### (10) 주체를 변수에 담기 — `when (val v = f())`

**언제 쓰나** — 주체가 함수 호출이고 가지 안에서 그 값을 다시 써야 할 때.

```kotlin
val r = when (val v = subject()) {
    in 0..5 -> "작다 v=$v"
    in 6..10 -> "중간 v=$v"
    else -> "크다 v=$v"
}
```

**출력** (`ex.kt`)

```text
--- 1. 주체를 변수에 담기 ---
  subject() 호출됨
결과=중간 v=7, subject() 호출 횟수=1
```

- ★ **`subject()` 는 한 번만 불린다.** 가지 셋이 전부 `v` 를 봐도 호출은 1회다.
- `v` 의 수명은 **그 `when` 안뿐**이다.

**출력** (`kotlinc bad7.kt` — `when` 밖에서 `v` 를 쓰면)

```text
bad7.kt:22:12: error: unresolved reference 'v'.
    return v
           ^
```

비용 — 지역 변수 한 칸.

## 문법 — 형태와 규칙

```kotlin
// 1) 주체 있는 when — 식
val s = when (x) {
    1, 2 -> "하나나 둘"          // 쉼표 = or
    in 3..9 -> "3~9"             // in = contains 규약
    !in 10..99 -> "두 자리 아님"
    is String -> x.length        // is = 타입 검사 + 스마트 캐스트
    else -> "그 외"
}

// 2) 주체 없는 when — if/else if 사슬
val t = when {
    x < 0 -> "음수"
    x == 0 -> "영"
    else -> "양수"
}

// 3) 주체를 변수에 담기 (변수는 when 안에서만 산다)
when (val v = compute()) { ... }

// 4) guard — 2.2.0, 주체 있는 형태에서만
when (x) {
    is Int if x > 100 -> "큰 Int"
    is Int -> "작은 Int"
    else -> "Int 아님"
}

// 5) 가지 몸통이 여러 줄이면 마지막 식이 값이다
val u = when (x) {
    1 -> { log("one"); "하나" }   // 값은 "하나"
    else -> "그 외"
}
```

규칙 불릿.

- **위에서 아래로 첫 일치.** 겹치는 가지는 순서가 의미를 정한다.
- **폴스루가 없다.** 한 가지를 실행하면 끝이다 — `break` 라는 개념 자체가 없다.
- **`when` 은 식이다.** 대입·반환·문자열 보간 안에 바로 들어간다.
- **완전성은 주체 타입이 정한다.** 유한 타입(`enum`·`sealed`·`Boolean`·그 nullable)은 **문에서도** 완전해야 한다.
- **guard 는 주체 있는 형태 전용**이고 **2.2.0** 부터다.
- `when (val v = …)` 의 `v` 는 **그 `when` 지역**이다.

## 어디서 틀리나

| 틀리는 형태 | 무슨 일이 일어나나 | 고치는 법 |
|---|---|---|
| "문이니까 `else` 안 써도 된다" | 주체가 `enum`·`sealed`·`Boolean` 이면 **문에서도 에러** | 가지를 다 적는다 |
| `sealed` 주체에 `else` 를 달아 둠 | 하위 타입이 늘어도 **컴파일이 안 깨진다.** 안전망이 꺼진다 | `else` 를 빼고 가지를 다 적는다 |
| `else` 를 지웠더니 경고가 사라짐 | **경고가 사라진 것이 신호다** — 누가 하위 타입을 늘렸다는 뜻 | 늘어난 타입의 가지를 적는다 |
| 넓은 조건을 위에, 좁은 조건을 아래에 | 아래 가지가 **영원히 안 돈다.** 경고도 없다 | 좁은 조건을 위로 올린다 |
| 라이브러리만 갈아 끼움 | 컴파일은 안 깨지고 **런타임에 `NoWhenBranchMatchedException`** | 같이 다시 컴파일한다 |
| `when` 주체를 함수 호출로 두고 가지마다 또 부름 | 호출이 가지 수만큼 늘어난다 | `when (val v = f())` |
| 주체 없는 `when` 에 guard | `guard statements are only allowed in 'when' with subject.` | 주체 있는 형태로 바꾸거나 `&&` 로 적는다 |
| 중복 가지 | 경고만 나고 **아랫것이 죽는다** | 경고를 읽는다 |
| Java 처럼 `break` 를 적음 | 루프가 아니면 `'break' and 'continue' are only allowed inside loops.` | 지운다 — 폴스루가 없다 |
| `Long` 주체에 `switch` 성능을 기대 | `tableswitch` 가 아니라 `lcmp` 사슬이다 | 기대를 고친다(또는 `Int` 로 좁힌다) |
| "바이트코드가 `instanceof` 사슬이다" 라고 적음 | **`-jvm-target 21` 에서는 `invokedynamic` 이다** | 타깃을 밝힌다 |

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 | 근거 |
|---|---|---|
| `when` 이 값을 내는 식이다 | **언어** | 명세 + 컴파일 통과 |
| 식으로 쓰면 완전해야 한다 | **언어** | 컴파일 에러 |
| **유한 주체는 문에서도 완전해야 한다** | **언어** ★ | 컴파일 에러 — `bad5.kt`·`bad6.kt` |
| 폴스루가 없다 | **언어** | 문법에 `break` 자리가 없다 |
| 위에서 아래로 첫 일치 | **언어** | 명세 + 실측 |
| guard 가 2.2.0 부터인 것 | **언어(버전)** | `-language-version 2.1` 의 거부 메시지 |
| `when (val v = …)` 의 `v` 가 지역인 것 | **언어** | `unresolved reference 'v'` |
| **촘촘한 `Int` → `tableswitch`** | **구현** | `javap` |
| **흩어진 `Int` → `lookupswitch`** | **구현** | `javap` |
| **`Long` → `lcmp` 사슬** | **구현** | `javap` |
| **`String` → `hashCode` + `equals` 두 단** | **구현** | `javap` |
| **`enum` → `$EnumSwitchMapping$0` 배열** | **구현** | `javap` + 클래스 파일 목록 |
| **`sealed` → `instanceof` 사슬 (타깃 ≤20)** | **구현 + 플래그 의존** ★ | `javap` |
| **`sealed` → `invokedynamic typeSwitch` (타깃 21)** | **구현 + 플래그 의존** ★ | `javap -v` 의 BootstrapMethods |
| **완전한 `when` 에도 `NoWhenBranchMatchedException` 이 남는 것** | **구현** | `javap` |
| **그 예외가 실제로 던져질 수 있는 것** | **언어의 한계** ★ | 분리 컴파일 실측 |
| 그 예외의 `message` 가 `null` 인 것 | **구현** | 실행 |

★ **가장 중요한 구분 한 줄** — **완전성은 「컴파일 단위 하나 안에서의 약속」이다.**\
같이 컴파일하면 컴파일러가 막아 주고, 따로 컴파일하면 **런타임 예외로 미뤄진다.**\
"`sealed` 를 쓰면 타입이 늘 때 컴파일이 깨진다" 는 **재컴파일을 전제로만 참인 문장**이다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 값 하나를 조건으로 골라야 할 때 | `when` 식 | 임시 변수와 대입이 사라진다 |
| 주체 하나를 여러 값과 견줄 때 | `when (x)` | 주체를 한 번만 적는다 |
| 조건들이 서로 다른 것을 볼 때 | `when { }` | `if`/`else if` 사슬의 정렬된 형태 |
| 상태 집합이 닫혀 있을 때 | `sealed`·`enum` 주체 + **`else` 없이** | 타입이 늘면 컴파일이 깨진다 |
| 열린 입력(외부 문자열·코드값) | `when (s)` + `else` | 모르는 값이 반드시 온다 |
| 같은 타입인데 조건이 더 필요할 때 | guard(`is T if …`) | 중첩 `when` 이 안 생긴다 |
| 주체가 비싼 호출일 때 | `when (val v = f())` | 한 번만 부른다 |
| 가지가 둘뿐일 때 | `if` | `when` 이 오히려 길다 |
| 가지 몸통이 열 줄씩일 때 | 함수로 뽑고 `when` 은 이름만 | `when` 이 지도 역할을 한다 |

판단 규칙 두 줄.

- **`else` 를 적는 순간 「모르는 값이 올 수 있다」고 선언한 것**이다. 닫힌 집합에는 적지 않는다.
- **`when` 이 길어지면 문제는 `when` 이 아니라 타입이다** — 가지가 열 개면 그 열 개가 `sealed` 가 될 후보다.

## 핵심 문장

- `when` 은 **식**이다 — 값을 내므로 "이 입력에는 뭘 내놓을 건가" 를 컴파일러가 묻는다.
- **완전성을 정하는 것은 문/식이 아니라 주체 타입이다.** `enum`·`sealed`·`Boolean` 은 **문에서도** 완전해야 한다.
- 에러 문구가 두 갈래다 — 무한 주체는 `Add an 'else' branch.`, 유한 주체는 **빠진 가지 이름을 대 준다.**
- 주체 타입마다 다른 명령이 된다 — 촘촘한 `Int` 는 `tableswitch`, 흩어지면 `lookupswitch`, `Long` 은 **`switch` 조차 아니다.**
- `String` 은 **`hashCode` 로 좁히고 `equals` 로 확인**하는 두 단이다.
- `enum` 은 `$EnumSwitchMapping$0` 배열을 한 겹 끼운다 — **분리 컴파일 때문**이고 `NoSuchFieldError` 를 상수마다 잡는다.
- ★ **`sealed` 는 `-jvm-target 21` 에서 `invokedynamic typeSwitch` 가 된다** — Java 21 패턴 `switch` 와 **같은 부트스트랩**이다.
- ★ **완전한 `when` 에도 `NoWhenBranchMatchedException` 이 남는다.** 분리 컴파일에서 **실제로 던져지는 것을 실측했다.**
- 폴스루가 없다 — Java `switch` 의 `break` 가 Kotlin 에는 개념째 없다.

## 관련 자료

- [`../README.md`](../README.md) — Kotlin 문법·API 주제 목록(이 주제는 06번)
- [`../../../java/syntax/21-switch-statement-and-expression/`](../../../java/syntax/21-switch-statement-and-expression/) — **Java `switch` 의 정본.**\
  거기는 **폴스루가 바이트코드에서 `goto` 의 유무**라는 것과 화살표 문법이 정본이고, 여기는 **완전성과 주체 타입별 컴파일 결과**다
- [`../../../java/syntax/20-control-flow-statements/`](../../../java/syntax/20-control-flow-statements/) — Java 의 `if`/루프·레이블. `when` 이 대체한 `if`/`else if` 사슬이 거기 있다
- [03번 주제](../03-null-safe-types/) — 바이트코드에 섞여 보이는 `checkNotNullParameter` 와 `message = null` 예외의 정본
- [04번 주제](../04-smart-casts/) — `is` 가지 안에서 캐스트 없이 멤버를 쓰는 것의 정본
- [07번 주제](../07-loops-ranges-and-labels/) — `in 1..9` 가지가 쓰는 range 의 정본. `break`/`continue` 의 정본이기도 하다
- [목록의 **23번 주제**](../23-sealed-classes-and-when-exhaustiveness/)(`sealed class`/`sealed interface` 와 `when` 완결성) — **계층 설계**가 거기 정본이다. 여기는 그 완결성의 **에러·바이트코드**까지
- [목록의 **24번 주제**](../24-enum-class-vs-sealed/)(`enum class` 와 `sealed` 선택 기준) — 어느 쪽을 고르나
- [목록의 **33번 주제**](../33-type-checks-and-casts-is-as/)(`is`/`as`/`as?`) — 타입 검사 연산자의 정본
- [목록의 **34번 주제**](../34-exceptions-nothing-and-try-expression/)(예외·`Nothing`·`try` 가 식이라는 것) — `when` 가지에 `throw` 를 놓는 관용구의 근거
- 목록의 **57번 주제**(Java 코드를 Kotlin 답게) — `if`/`when` 을 식으로 쓰는 관용구
- [`../../언어-특성/README.md`](../../언어-특성/README.md) §3 — **"상태를 늘리면 컴파일이 깨진다" 는 설계 논지가 거기 정본**이다

## 용어 풀이

- **식(expression)** — 값을 내는 것. 대입·반환·보간 안에 들어갈 수 있다. Kotlin 의 `when`·`if`·`try` 가 전부 식이다.
- **문(statement)** — 실행만 하고 값을 안 내는 것. Kotlin 의 `for`·`while`·대입이 그렇다.
- **완전성(exhaustiveness)** — 있을 수 있는 모든 입력에 대해 갈 가지가 하나는 있다는 것.
- **유한 주체** — 값을 셀 수 있는 타입. `enum`·`sealed` 계층·`Boolean`(그리고 그 nullable — `null` 가지가 하나 는다).
- **guard(가드) 조건** — 가지의 패턴 뒤에 붙이는 추가 조건. `is Int if x > 100` 형태. **2.2.0** 부터.
- **`tableswitch`** — 키가 촘촘할 때 쓰는 JVM 분기 명령. 점프 표를 배열로 두고 인덱스로 한 번에 간다.
- **`lookupswitch`** — 키가 흩어졌을 때 쓰는 JVM 분기 명령. 정렬된 (키, 주소) 쌍을 찾는다.
- **`invokedynamic`** — 첫 실행 때 "무엇을 부를지" 를 부트스트랩 메서드에게 묻고, 그 뒤로는 그 결과를 재사용하는 JVM 명령.
- **`SwitchBootstraps.typeSwitch`** — JDK 21 이 타입 패턴 분기를 위해 제공하는 부트스트랩. 후보 타입 목록을 받아 **맞는 인덱스**를 돌려준다.
- **`$EnumSwitchMapping$0`** — `enum` 의 `ordinal` 을 "이 `when` 의 가지 번호" 로 바꿔 주는 `int[]`. 컴파일러가 만든다.
- **`NoWhenBranchMatchedException`** — 완전하다고 판정된 `when` 이 런타임에 어느 가지에도 안 걸렸을 때 던져지는 예외.
- **분리 컴파일(separate compilation)** — 의존하는 쪽과 의존되는 쪽을 따로 컴파일하는 것. 그 사이에 정의가 어긋날 수 있다.
- **폴스루(fall-through)** — 한 가지가 끝나도 멈추지 않고 다음 가지로 이어 실행되는 것. Kotlin 에는 없다.

---

## 더 들어가면

- `when` 의 `in` 가지는 **`contains` 연산자 규약**으로 풀린다. 그래서 `in` 뒤에 올 수 있는 것은 range 만이 아니다 —\
  `contains` 를 가진 것이면 다 된다(`Set`·`List`·`String`). 규약 자체의 정본은 [목록의 **31번 주제**](../31-operator-overloading-infix-and-invoke/)다.
- `when` 의 가지 값이 `Nothing`(즉 `throw`·`return`)이면 그 가지는 **타입 추론에 아무 영향을 안 준다.**\
  `Nothing` 의 정본은 [목록의 **34번 주제**](../34-exceptions-nothing-and-try-expression/)다.
- 타깃 21 의 `typeSwitch` 가 받는 세 번째 인자(`iconst_0`)는 **restart index** 다 —\
  guard 가 실패했을 때 그 다음 후보부터 다시 찾기 위한 자리다. 이 문서의 예제에는 guard 가 없어 0 으로 고정돼 있다.
- **`-jvm-target` 을 바꾸면 `when` 말고도 갈리는 것이 있다** — [02번 주제](../02-string-templates-and-raw-strings/)의 문자열 보간이\
  1.8 에서 `StringBuilder`, 그 위에서는 `invokedynamic` 이 되는 것이 같은 성격이다.\
  **이 저장소의 Kotlin 문서는 전부 기본 타깃(1.8)을 정본으로 적고 갈리는 자리만 따로 표시한다.**
- 이 문서에서 **못 잰 것** — `-language-version 1.9` 이하는 kotlinc 2.4.20 이 거부한다\
  (`language version 1.9 is no longer supported; use version 2.0 or greater instead.`).\
  그래서 **K1 컴파일러의 `when` 바이트코드와는 비교하지 못했다.**
