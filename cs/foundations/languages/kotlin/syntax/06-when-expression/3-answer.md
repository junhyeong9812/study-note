# kotlin/syntax/06 — `when` 식: 주체 있는/없는 형태·완전성·guard (2.2+) — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러·경고·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javap` 에서 실제로 얻었다.\
> 역어셈블은 **기본 `-jvm-target`(1.8 · `major version: 52`)** 이 정본이고, 5번만 `-jvm-target 21` 을 따로 찍었다.\
> 2번의 분리 컴파일은 `kotlinc` 를 **두 번 나눠 돌려** 실제로 재현한 것이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★ 통과하는 것은 `[A]` 하나뿐 — 기준은 문/식이 아니라 **주체 타입**이다

**출력** (`kotlinc bad1.kt` — `[A]`·`[B]`)

```text
bad1.kt:8:36: error: 'when' expression must be exhaustive. Add an 'else' branch.
fun asExpression(x: Int): String = when (x) {
                                   ^^^^
```

**출력** (`kotlinc bad6.kt` — `[C]` 및 `Boolean?`)

```text
bad6.kt:2:5: error: 'when' expression must be exhaustive. Add the 'false' branch or an 'else' branch.
    when (b) {
    ^^^^
bad6.kt:20:5: error: 'when' expression must be exhaustive. Add the 'null' branch or an 'else' branch.
    when (b) {
    ^^^^
```

**출력** (`kotlinc bad5.kt` — `[D]` 및 `sealed`)

```text
bad5.kt:8:5: error: 'when' expression must be exhaustive. Add the 'BLUE' branch or an 'else' branch.
    when (c) {
    ^^^^
bad5.kt:15:5: error: 'when' expression must be exhaustive. Add the 'is Square' branch or an 'else' branch.
    when (s) {
    ^^^^
```

**왜 그런가**

| | 형태 | 결과 |
|---|---|---|
| `[A]` | 문 · `Int` 주체 · 가지 하나 | **통과** — 에러도 경고도 없다 |
| `[B]` | 식 · `Int` 주체 | 에러 — `Add an 'else' branch.` |
| `[C]` | 문 · `Boolean` 주체 | 에러 — **`Add the 'false' branch` or an 'else' branch.** |
| `[D]` | 문 · `enum` 주체 | 에러 — **`Add the 'BLUE' branch` or an 'else' branch.** |

```text
                 주체 타입이 유한한가?
                 (enum · sealed · Boolean · 그 nullable)
                         │
            ┌────────────┴────────────┐
           예                         아니오 (Int · String · Any …)
            │                              │
   문이든 식이든 완전해야 한다     ┌────────┴────────┐
            │                    식              문
            ▼                    ▼                ▼
      [C] [D] 가 여기서 죽음    [B] 죽음       [A] 통과
```

- ★ **"문으로 쓰면 `else` 가 필요 없다" 는 절반만 맞다.** 그 말이 참인 범위는 **무한 주체**(`Int`·`String`·`Any`)뿐이다.
- **에러 문구가 두 갈래인 것이 결정적 단서다.**\
  무한 주체는 `Add an 'else' branch.` — 컴파일러가 댈 수 있는 이름이 없다.\
  유한 주체는 **빠진 가지 이름을 대 준다**(`'false'`·`'BLUE'`·`'is Square'`).
- 문 쪽에서도 메시지가 **`'when' expression must be exhaustive`** 다 —\
  컴파일러는 문/식을 구분해 말하지 않는다. 유한 주체에서는 그냥 **식으로 취급**한다.
- `Boolean?` 은 가지가 **셋**이다 — `true`·`false`·`null`. 메시지가 `Add the 'null' branch` 라고 정확히 말해 준다.

### 2. ★★ 터진다 — `kotlin.NoWhenBranchMatchedException`, `message = null`

**출력** (`kotlinc color.kt lib.kt -d outC/` → `kotlinc color.kt -d outC/` → `java LibKt`)

```text
(1) 상수 둘 — else 없이 컴파일 통과)
(2) enum 만 재컴파일)
--- RUN ---
RED  -> 빨강
BLUE -> kotlin.NoWhenBranchMatchedException / message=null
```

**왜 그런가**

```text
   컴파일 시점                     실행 시점
   +----------------------+        +-------------------------+
   | Color = {RED, GREEN} |        | Color = {RED,GREEN,BLUE}|
   | when 이 둘을 다 덮음  |        | LibKt.class 는 그대로   |
   | -> else 불필요        |        | -> BLUE 가 default 로   |
   +----------------------+        +-------------------------+
                                        │
                                        ▼
                         kotlin.NoWhenBranchMatchedException
```

- 가능성이 남아 있는 자리는 **`default` 가지**다. (4)·(5)의 `javap` 에 그대로 보인다.

```text
      52: new           #64                 // class kotlin/NoWhenBranchMatchedException
      55: dup
      56: invokespecial #68                 // Method kotlin/NoWhenBranchMatchedException."<init>":()V
      59: athrow
```

- ★ **완전하다고 판정된 `when` 에도 컴파일러가 `athrow` 를 남긴다.** 죽은 코드가 아니었다 — **실제로 걸렸다.**
- `message` 가 `null` 이다. [03번 주제](../03-null-safe-types/)의 `!!`(`Intrinsics.checkNotNull`)와 같은 모양이라,\
  **어느 `when` 이 터졌는지는 스택 트레이스의 줄 번호로만** 안다.
- ★ **그래서 "`sealed`/`enum` 을 쓰면 컴파일이 깨져 안전하다" 는 「같이 다시 컴파일할 때」만 참이다.**\
  라이브러리만 갈아 끼우면 **컴파일러는 아무 말도 안 하고** 런타임 예외가 된다.

### 3. ★★ `tableswitch` / `lookupswitch` / 두 단 비교 / `switch` 아님

**출력** (`javap -c -p out/IcodeKt.class`)

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

**왜 그런가**

| 주체 | 명령 | 고른 이유 |
|---|---|---|
| `Int` · 1·2·3 | `tableswitch` | 값이 **촘촘**해 점프 표를 배열로 둘 수 있다 |
| `Int` · 1·100·10000 | `lookupswitch` | 값이 **흩어져** 배열을 만들면 낭비다 |
| `String` | `hashCode` → `tableswitch` → `equals` | JVM 의 `switch` 는 `int` 키만 받는다 |
| `Long` | `lcmp` 비교 사슬 | JVM 에 `long` 을 받는 `switch` 명령이 **없다** |

```text
   tableswitch  (값이 촘촘할 때)        lookupswitch (값이 흩어질 때)
   +---------------------------+       +---------------------------+
   | 1 -> 28                   |       | (1, 36)                   |
   | 2 -> 33   ← 인덱스 계산   |       | (100, 41)  ← 키를 찾는다  |
   | 3 -> 38     한 번이면 끝  |       | (10000, 46)               |
   +---------------------------+       +---------------------------+
```

- ★ **가른 것은 `when` 문법이 아니라 가지 값들의 분포다.** 소스는 형태가 똑같다.
- `String` 은 **두 단**이다 — 해시로 후보를 좁히고 `equals` 로 확인한다.\
  해시가 같아도 문자열이 같은 건 아니라서 확인이 꼭 필요하다.\
  여기서는 `"a"`·`"b"`·`"c"` 의 해시가 97·98·99 로 촘촘해 **해시 쪽에도 `tableswitch`** 가 쓰였다.
- `Long` 은 **명령이 없어서** 사슬이 된 것이다. `when` 이 느려진 게 아니다.
- 맨 앞의 `checkNotNullParameter` 는 `when` 과 무관하다([03번](../03-null-safe-types/)).

### 4. ★ 소스에 없던 `IcodeKt$WhenMappings` 가 생긴다

**출력** (`ls out/` — 이 파일에는 `sealed` 예제도 같이 들어 있었다)

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

**왜 그런가**

```text
   Color.GREEN
        │ ordinal()   ← 지금 이 순간의 Color 클래스가 답한다
        ▼
       [1]
        │  $EnumSwitchMapping$0 로 갈아 끼운다
        ▼
       [2]            ← 이 소스가 적은 「가지 번호」
        │
        ▼
   tableswitch { 1,2,3 }
```

- **`ordinal()` 을 바로 `switch` 하지 않는 이유는 분리 컴파일이다.**\
  상수 순서가 바뀌어도 `WhenMappings` 의 `static {}` 이 **클래스 로드 시점에 다시 만들어진다** —\
  `Color.values()` 와 각 상수의 `ordinal()` 을 **그때 읽는다.**
- ★ `static {}` 이 상수마다 **`NoSuchFieldError` 를 따로 잡는다.**\
  상수 하나가 사라져도 **그 칸만 0으로 남고** 초기화 전체가 죽지 않는다.
- 가지를 다 적었는데도 `default` 에 **`NoWhenBranchMatchedException` 을 던지는 코드가 남았다** — 2번의 그 자리다.
- Java `switch` 도 같은 구조(`$SwitchMap`)를 쓴다 —\
  정본은 [`../../../java/syntax/21-switch-statement-and-expression/`](../../../java/syntax/21-switch-statement-and-expression/).

### 5. ★★ 다르다 — 경계는 **정확히 21**, `SwitchBootstraps.typeSwitch` 가 등장한다

**출력** (기본 타깃 · `javap -c -p out/IcodeKt.class`)

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

**출력** (`-jvm-target 21` · `javap -c -p out21/IcodeKt.class`)

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

**출력** (`javap -v -p out21/IcodeKt.class`)

```text
BootstrapMethods:
  0: #84 REF_invokeStatic java/lang/runtime/SwitchBootstraps.typeSwitch:(Ljava/lang/invoke/MethodHandles$Lookup;Ljava/lang/String;Ljava/lang/invoke/MethodType;[Ljava/lang/Object;)Ljava/lang/invoke/CallSite;
    Method arguments:
      #73 Circle
      #75 Square
      #77 Tri
```

**출력** (타깃 17·20·21 의 `onSealed` 에서 `invokedynamic` 을 센 것)

```text
target 17 : 0 (invokedynamic 개수)
target 20 : 0 (invokedynamic 개수)
target 21 : 1 (invokedynamic 개수)
```

**왜 그런가**

```text
   -jvm-target 1.8 / 17 / 20            -jvm-target 21
   +--------------------------+         +----------------------------+
   | instanceof Circle ?      |         | invokedynamic typeSwitch   |
   | instanceof Square ?      |         |   -> 인덱스 0/1/2 를 받아   |
   | instanceof Tri ?         |         | tableswitch 로 한 번에 점프 |
   +--------------------------+         +----------------------------+
```

- **경계는 정확히 21 이다.** 17·20 에서는 `invokedynamic` 이 0개였고 21 에서 1개가 됐다.
- 부트스트랩의 소유 클래스는 **`java.lang.runtime.SwitchBootstraps`** —\
  **Java 21 의 패턴 `switch` 가 쓰는 바로 그것**이다. 두 언어의 분기가 같은 JVM 기계 위에서 만난다.
- 인자로 후보 타입 목록(`Circle`·`Square`·`Tri`)이 **상수 풀에 그대로 실린다.**
- ★ **그래서 "`sealed when` 은 `instanceof` 사슬이다" 는 타깃을 안 밝히면 틀린 문장이다.**\
  이 저장소의 Kotlin 문서가 기본 타깃을 정본으로 잡고 갈리는 자리만 따로 표시하는 이유다.

### 6. ★ `"양수"` · `"천 단위"` · `"모름"` · `"작은 Int"`

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

**왜 그런가**

| | 식 | 값 |
|---|---|---|
| `[A]` | `firstMatch(500)` | `"양수"` — `x > 0` 이 먼저 걸린다 |
| `[B]` | `kinds(1000)` | `"천 단위"` — 쉼표 가지 |
| `[C]` | `kinds(3.14)` | `"모름"` — `Double` 은 어느 가지에도 안 걸린다 |
| `[D]` | `guarded(7)` | `"작은 Int"` — guard 가 거짓이라 다음 `is Int` 로 |

```text
   when (x) {                 x = 500
     x > 0    ────────────>   참  → "양수" 를 내고 끝
     x > 100                  ← 영원히 안 온다
     else
   }
   ★ 컴파일러는 이것을 경고하지 않았다 (실측)
```

- ★ **`[A]` 에 경고가 붙지 않았다.** `when { }` 의 조건은 임의의 `Boolean` 식이라\
  컴파일러가 `x > 0` 과 `x > 100` 의 포함 관계를 **모른다.** **순서가 곧 의미다.**
- `is String` 가지 안에서 `x.length` 가 되는 것은 **스마트 캐스트**다 — 정본은 [04번 주제](../04-smart-casts/).
- `in 1..9` 는 **`contains` 규약**이고, `1000, 2000` 의 쉼표는 **or** 다.\
  쉼표는 Java `switch` 의 **폴스루가 아니다** — 가지는 여전히 하나이고 실행 후 끝난다.
- guard(`is Int if x > 100`)는 **2.2.0** 이다(10번).

### 7. 둘 다 **경고**다 — 그리고 "경고가 사라지는 것" 이 신호다

**출력** (`kotlinc bad4.kt`)

```text
bad4.kt:3:5: warning: duplicate branch condition in 'when'.
    1 -> "b"
    ^
bad4.kt:10:5: warning: 'when' is exhaustive so 'else' is redundant here.
    else -> "?"
    ^^^^
```

**왜 그런가**

- 중복 가지는 **에러가 아니라 경고**이고, **위엣것이 이기고 아랫것이 죽는다**(6번의 첫 일치 규칙).
- `Boolean` 주체에 `true`·`false`·`else` 를 다 적으면 `'when' is exhaustive so 'else' is redundant here.` 가 나온다 —\
  **`Boolean` 이 유한 주체라는 증거**이기도 하다.
- `sealed` 주체에 `else` 를 달아 두면 하위 타입이 늘어도 **컴파일이 안 깨진다.**\
  새 타입은 조용히 `else` 로 떨어진다 — 9번에서 이어 본다.
- ★ **"경고가 사라진 것" 이 신호인 경우** — `sealed` 주체에 `else` 를 적어 두면\
  가지가 다 있는 동안은 `redundant` 경고가 뜨지만, **누군가 하위 타입을 늘리는 순간 그 경고가 사라진다.**\
  에러가 나는 게 아니라 **경고가 없어지는 것**이 변화의 유일한 흔적이다.

### 8. 한 번만 불린다 · `v` 는 그 `when` 안에서만 산다

**출력** (`ex.kt`)

```text
--- 1. 주체를 변수에 담기 ---
  subject() 호출됨
결과=중간 v=7, subject() 호출 횟수=1
```

**출력** (`kotlinc bad7.kt`)

```text
bad7.kt:22:12: error: unresolved reference 'v'.
    return v
           ^
```

**왜 그런가**

- 가지 셋이 전부 `v` 를 봐도 `subject()` 호출은 **1회**다. `when` 의 주체는 **한 번 평가돼 지역 변수에 담긴다.**\
  (3)의 `onString` 바이트코드에서 `7: astore_1` 이 그 자리다.
- `v` 를 `when` 밖에서 쓰면 `unresolved reference` 다 — **수명이 그 `when` 으로 좁혀져 있다.**
- 이 형태가 없으면 `val v = subject()` 를 **`when` 바깥에 적어야** 하고, 그러면 `v` 가 함수 끝까지 산다.\
  **이름이 새어 나가지 않는 것**이 이 문법의 값어치다.
- 막는 사고 — 주체가 부수효과를 가진 함수일 때, 가지마다 `f()` 를 다시 적으면 **호출이 가지 수만큼 늘어난다.**

### 9. `else` 를 적으면 **"타입이 늘었다" 는 신호가 사라진다**

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

**왜 그런가**

- `else` 를 적으면 없어지는 것은 **이 에러**다. 새 타입이 조용히 `else` 로 떨어진다.
- 에러가 알려 주는 것은 **"어디를 고쳐야 하나"** 다 —\
  하위 타입 하나를 늘리면 **그 타입을 분기하던 모든 `when` 이 전수로 튀어나온다.**\
  `is Triangle` 이라는 **이름까지 대 준다.**
- 그럼에도 `else` 를 적어야 하는 상황 —\
  ① **바깥 모듈에서 오는 값**이라 하위 타입이 내 손 밖에서 늘 수 있을 때,\
  ② 가지가 수십 개인데 대부분이 같은 기본 동작일 때,\
  ③ `enum`/`sealed` 가 아닌 **무한 주체**일 때(그때는 선택이 아니라 필수다).
- 다만 ①의 경우에도 **2번의 런타임 예외 시나리오는 그대로 남는다** — `else` 는 그 예외를 없애 주는 대신\
  **잘못된 값이 조용히 기본 동작으로 흘러가게** 만든다. 둘 중 어느 실패를 고를지의 문제다.

### 10. 주체 없는 `when` 에는 못 쓴다 · **2.2.0** 부터

**출력** (`kotlinc bad7.kt`)

```text
bad7.kt:16:11: error: guard statements are only allowed in 'when' with subject.
    x > 0 if x < 10 -> "a"
          ^^^^^^^^^
```

**출력** (`kotlinc -language-version 2.1 lv.kt` — 컴파일러에게 직접 물은 것)

```text
warning: language version 2.1 is deprecated and its support will be removed in a future version of Kotlin. Update the version to 2.2.
lv.kt:4:57: error: the feature "break continue in inline lambdas" is only available since language version 2.2
    for (i in 1..3) { listOf(1,2).forEach { if (i == 2) break; sb.append(i) } }
                                                        ^^^^^
lv.kt:7:43: error: the feature "when guards" is only available since language version 2.2
fun c(x: Any): String = when (x) { is Int if x > 5 -> "big"; else -> "n" }
                                          ^^^^^^^^
```

**왜 그런가**

- ★ **버전 경계를 문서가 아니라 컴파일러에게 물었다.** `-language-version 2.1` 을 주면\
  `the feature "when guards" is only available since language version 2.2` 가 나온다.\
  같은 명령이 07번의 비지역 `break`/`continue` 도 **같은 2.2 경계**로 대답했다.
- 주체 **없는** `when { }` 에는 못 쓴다 — 거기서는 가지 자체가 이미 `Boolean` 식이라 `&&` 로 적으면 된다.
- guard 가 없던 시절에는 **가지 안에 `when` 을 또 중첩**해 풀었다.\
  중첩하면 **바깥 `when` 의 완전성과 안쪽의 완전성이 따로 놀아** 실수가 나기 쉬웠다.
- guard 가 있는 가지는 **완전성 계산에 넣어 주지 않는다** —\
  조건이 거짓일 수 있으므로 `is Int if x > 100` 만으로는 `Int` 를 덮었다고 볼 수 없다.\
  그래서 6번의 예제는 `is Int` 가지를 **하나 더** 두었다.

### 11. Kotlin `when` 에 없는 것은 **폴스루**다

- **폴스루(fall-through)가 없다.** Kotlin 문법에는 `case` 를 끝내는 `break` 가 **개념째 없다.**\
  여러 값을 한 가지로 묶는 것은 **쉼표**(`1000, 2000`)로 적는다 — Java 21 의 `case 1, 2 ->` 와 같은 모양이다.\
  루프가 아닌 곳에 `break` 를 적으면 이렇게 대답한다.

```text
bad2.kt:6:66: error: 'break' and 'continue' are only allowed inside loops.
fun breakInMap(xs: List<Int>): List<Int> = xs.map { if (it == 2) break else it }
                                                                 ^^^^^
```

- **Java 쪽 정본 → [`../../../java/syntax/21-switch-statement-and-expression/`](../../../java/syntax/21-switch-statement-and-expression/)** 다.\
  거기는 **폴스루가 바이트코드에서 `goto` 의 유무**라는 것, 화살표 문법, `yield`, `MatchException` 이 정본이다.\
  제어문 일반은 [`../../../java/syntax/20-control-flow-statements/`](../../../java/syntax/20-control-flow-statements/).
- **`sealed` 계층 설계 → [목록의 23번 주제](../23-sealed-classes-and-when-exhaustiveness/)**(`sealed class`/`sealed interface` 와 `when` 완결성)가 정본이다.\
  `enum` 과 `sealed` 중 무엇을 고르나는 [목록의 **24번 주제**](../24-enum-class-vs-sealed/).\
  설계 논증 쪽은 [`../../언어-특성/README.md`](../../언어-특성/README.md) §3.
- **가지가 `throw` 일 때의 타입 추론 → [목록의 34번 주제](../34-exceptions-nothing-and-try-expression/)**(예외·`Nothing` 타입)가 정본이다.\
  `Nothing` 은 모든 타입의 하위 타입이라 **그 가지는 결과 타입을 넓히지 않는다.**
- `in` 가지가 쓰는 `contains` 규약의 정본은 [목록의 **31번 주제**](../31-operator-overloading-infix-and-invoke/), range 자체는 [07번 주제](../07-loops-ranges-and-labels/).

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
| `icode.kt` | `Int`(촘촘/흩어짐)·`String`·`Long`·`enum`·`sealed`·주체 없는 `when` 의 바이트코드 | `kotlinc` → `javap -c -p out/IcodeKt.class` |
| `icode.kt` (`WhenMappings`) | `$EnumSwitchMapping$0` 의 `static {}` 과 `NoSuchFieldError` 예외 표 | `javap -c -p 'out/IcodeKt$WhenMappings.class'` |
| `icode.kt` (타깃 3벌) | `sealed` 가 **17·20 에서 `instanceof`, 21 에서 `invokedynamic`** 인 것 | `kotlinc -jvm-target {17,20,21}` → `javap -c -p` 로 세기 |
| `icode.kt` (타깃 21) | `SwitchBootstraps.typeSwitch` 와 후보 타입 목록 | `javap -v -p out21/IcodeKt.class` |
| `bad1.kt` | 문/식 · `Int` 주체의 완전성 갈림 | `kotlinc` (컴파일 실패가 결과) |
| `bad4.kt` | 중복 가지 경고 · 남는 `else` 경고 | `kotlinc` (경고 2건) |
| `bad5.kt` | **문**인데도 `enum`·`sealed` 는 완전해야 하는 것 | `kotlinc` (컴파일 실패가 결과) |
| `bad6.kt` | `Boolean`·`Boolean?` 은 에러, `Int`·`String` 은 통과 | `kotlinc` (에러 2건 · 통과 2건) |
| `bad7.kt` | nullable `sealed` 의 `null` 가지 · guard 위치 제약 · `when (val v)` 의 수명 | `kotlinc` (에러 3건) |
| `lv.kt` | guard 가 **2.2 부터**인 것을 컴파일러에게 물음 | `kotlinc -language-version {2.0,2.1,2.2,2.3}` |
| `ex.kt` | 첫 일치·`is`/`in`/쉼표·guard·주체 변수 호출 횟수·폴스루 없음 | `kotlinc` → `java` |
| `sealed/` 2벌 | 하위 타입을 늘렸을 때 **컴파일이 깨지는 것** | `kotlinc` 2회 + `java` 1회 |
| `sep/` 2벌 | enum 만 재컴파일했을 때 **런타임에 터지는 것** | `kotlinc` 2회 + `java` 1회 |

**구현 의존 항목** — `javap` 의 명령 이름·상수 풀 번호, `tableswitch`/`lookupswitch` 의 선택,
`$EnumSwitchMapping$0` 이라는 이름과 `WhenMappings` 라는 클래스, `NoWhenBranchMatchedException` 의 위치,
`-jvm-target 21` 에서의 `invokedynamic typeSwitch` — 전부 **이 컴파일러 버전 + 그 타깃의 산출물**이다.\
반면 "`when` 이 식" · "완전성 요구" · "첫 일치" · "폴스루 없음" · "guard 는 2.2 · 주체 있는 형태 전용" 은
**언어 규칙**이라 타깃과 무관하다.

**★ 던져 봤더니 예상과 달랐던 것 — 세 건**

1. **"문으로 쓰면 `else` 가 필요 없다" 가 틀렸다.**\
   `Boolean`·`Boolean?`·`enum`·`sealed` 주체는 **문에서도 에러**다(`bad5.kt`·`bad6.kt`).\
   기준은 문/식이 아니라 **주체 타입이 유한한가**였다.
2. **`sealed` 의 `when` 이 `instanceof` 사슬이라는 것도 반쪽이었다.**\
   `-jvm-target 21` 에서 **`invokedynamic` + `SwitchBootstraps.typeSwitch`** 로 통째로 바뀐다.\
   경계는 정확히 21 이고, 17·20 은 사슬 그대로였다.
3. **"완전하면 런타임 검사가 없다" 도 틀렸다.**\
   가지를 다 적은 `when` 에도 `NoWhenBranchMatchedException` 을 던지는 `default` 가 남고,\
   분리 컴파일에서 **실제로 그 자리가 걸렸다**(`message=null`).

**안 걸린 것도 출력이다** — `firstMatch` 의 `x > 100` 가지는 `x > 0` 때문에 **영원히 실행되지 않는데
컴파일러가 아무 말도 하지 않았다.** 중복 가지(`1 -> …` 두 번)에는 경고가 나오므로,
**"경고가 없다" 가 "닿을 수 있다" 를 뜻하지 않는다.**
