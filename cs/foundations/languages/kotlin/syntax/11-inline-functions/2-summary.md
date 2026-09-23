# kotlin/syntax/11 — 인라인 함수: `noinline`/`crossinline`·비지역 `return` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Inline functions](https://kotlinlang.org/docs/inline-functions.html) · [Returns and jumps](https://kotlinlang.org/docs/returns.html) · [Higher-order functions and lambdas](https://kotlinlang.org/docs/lambdas.html) · [Visibility modifiers](https://kotlinlang.org/docs/visibility-modifiers.html).
> **실행 검증** — 모든 출력·에러·경고·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javap` 에서 실제로 얻었다.\
> `kotlinc` 19회 · `javac` 1회 · `java` 4회 · `javap` 14회 · `ls -l` 2회. 컴파일 실패 시나리오 **7벌**, 경고 시나리오 **3벌**.
> ⚠️ **`-jvm-target` 을 밝히지 않은 바이트코드 주장은 반쪽이다.** 이 문서의 역어셈블은 **기본값 1.8**(`major version: 52`)이다.\
> ★ 다만 이 주제의 결론은 **타깃에 안 흔들렸다** — 같은 두 파일을 `-jvm-target 21`(`major version: 65`)로 다시 찍어\
> `javap -c -p` 출력을 `diff` 했더니 **한 글자도 다르지 않았다**((9)).
> **버전** — `inline`·`noinline`·`crossinline`·비지역 `return` 은 전부 **1.0**. `@PublishedApi` 는 **1.2**.\
> 인라인 람다 안에서 **바깥 루프를 `break`/`continue` 로 빠져나오는 것**은 **2.2.0** 부터다 — [07번 주제](../07-loops-ranges-and-labels/)가 정본이다.
> ★★ **성능은 한 번도 재지 않았다.** `javap` 로 본 것은 **객체 생성·박싱·호출 명령의 유무**까지이고,\
> 따로 잰 것은 **코드 크기**(바이트 수와 명령 줄 수)뿐이다((8)). **「그래서 어느 쪽이 빠르다」는 이 문서가 하지 않은 주장이다.**
> **경계** — 람다가 **무엇이 되는가**(`invokedynamic`·`Function1`·박싱·객체 동일성)는 [10번 주제](../10-lambdas-and-higher-order-functions/)가 정본이다.\
> `reified` 는 [12번 주제](../12-reified-type-parameters/)가 정본이다 — 여기서는 **`inline` 이 왜 그 전제인가**까지만 짚는다.\
> 라벨과 `break`/`continue` 의 정본은 [07번 주제](../07-loops-ranges-and-labels/), `$default` 합성 메서드는 [08번 주제](../08-function-declaration-default-and-named-args/)다.\
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**`inline` 은 "이 함수를 부르지 말고, 몸통을 부르는 자리에 그대로 베껴 넣어라" 는 지시다.**

여기까지는 누구나 아는 이야기고, **거의 모두가 이유를 틀리게 안다.**\
「함수 호출이 비싸니까 호출을 없애는 것」이 아니다. **컴파일러가 직접 아니라고 말한다** —\
람다를 안 받는 함수에 `inline` 을 붙이면 이런 경고가 나온다.

```text
===== 소스: warn0.kt =====
inline fun noLambda(x: Int): Int = x + 1
===== kotlinc warn0.kt =====
warn0.kt:1:1: warning: expected performance impact from inlining is insignificant. Inlining works best for functions with parameters of function types.
inline fun noLambda(x: Int): Int = x + 1
^^^^^^
(exit 0)
```

그러니 `inline` 이 사는 이유는 둘뿐이다.

1. **람다가 객체가 되는 것**을 없앤다 — 고차 함수를 부를 때마다 `Function1` 객체 하나와 박싱이 생기는 것([10번 주제](../10-lambdas-and-higher-order-functions/)).
2. **비지역 `return`** 을 가능하게 한다 — `forEach` 안에서 **바깥 함수**를 빠져나오는 것.

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 전화를 걸어 "그 일 좀 해 줘" 하고 기다리기 | 보통의 고차 함수 호출 — `Function1` 객체를 만들어 넘긴다 |
| 그 사람의 작업 지시서를 **내 서류에 복사해 붙이기** | `inline` — 람다 몸통이 호출자 안으로 들어온다 |
| 복사해 붙였으니 **내 서류에 적힌 "여기서 끝"** 이 내 일을 끝낸다 | 비지역 `return` — 호출자의 `areturn` 이 된다 |
| "이 지시서는 베끼지 말고 그냥 넘겨라" | `noinline` — 그 람다만 다시 객체가 된다 |
| "베끼되, **남의 서류에** 베껴 넣을 테니 거기서 '내 일 끝' 이라고 쓰지 마라" | `crossinline` — 펼치기는 하지만 비지역 `return` 금지 |
| 베껴 붙인 자리가 늘수록 서류가 두꺼워진다 | 코드 크기 증가 — 이 문서가 유일하게 **잰** 대가 |

```text
   보통 고차 함수                         inline 고차 함수
   +-------------------------------+      +-------------------------------+
   | caller()                      |      | caller()                      |
   |   invokedynamic -> Function1  |      |   iload / iconst_1 / iadd     |
   |   invokestatic  twice(...)    |      |   iload / iconst_1 / iadd     |
   +-------------------------------+      +-------------------------------+
   | twice(int, Function1)         |      | twice(int, Function1)         |
   |   Integer.valueOf   <- 박싱   |      |   (남아 있다 — Java 용)       |
   |   invoke(Object)              |      |                               |
   +-------------------------------+      +-------------------------------+
   | caller$lambda$0(int)  <- 몸통 |      |   (없다)                      |
   +-------------------------------+      +-------------------------------+
```

**한 글자(`inline`)만 다른 두 파일을 찍어 나란히 놓은 것**이 이 문서의 뼈대다((2)).

## 이 주제가 답하려는 질문

1. `inline` 은 **무엇을 없애는가** — 호출인가, 객체인가. 그리고 **컴파일러는 무엇이라고 말하는가**.
2. 비지역 `return` 이 **왜 인라인 함수에서만 되는가** — 바이트코드의 어느 자리가 그 차이인가.
3. `noinline` 과 `crossinline` 은 각각 **무엇을 되돌리는가**, 그 대가로 무엇이 금지되는가.
4. 그래서 `inline` 을 **언제 쓰면 안 되는가** — 잰 것과 안 잰 것을 갈라서.

## 동작 방식

### (1) ★★ `inline` 은 「호출 비용」이 아니다 — **컴파일러가 직접 그렇게 말한다**

**언제 쓰나** — "함수 호출이 비싸니까 `inline` 을 붙인다" 고 생각할 때.

람다를 **안 받는** 함수, 그리고 람다를 받지만 **`noinline` 이라 펼칠 수 없는** 함수에 `inline` 을 붙여 던졌다.

**출력** (`kotlinc warn2.kt`)

```text
===== 소스: warn2.kt =====
inline fun noLambda(x: Int): Int = x + 1

inline fun onlyNoinline(x: Int, noinline f: (Int) -> Int): Int = f(x)

inline fun ok(x: Int, f: (Int) -> Int): Int = f(x)
===== kotlinc warn2.kt =====
warn2.kt:1:1: warning: expected performance impact from inlining is insignificant. Inlining works best for functions with parameters of function types.
inline fun noLambda(x: Int): Int = x + 1
^^^^^^
warn2.kt:3:1: warning: expected performance impact from inlining is insignificant. Inlining works best for functions with parameters of function types.
inline fun onlyNoinline(x: Int, noinline f: (Int) -> Int): Int = f(x)
^^^^^^
(exit 0)
```

```text
   inline fun noLambda(x: Int)                  -> 경고 ★
   inline fun onlyNoinline(x, noinline f)       -> 경고 ★★  (람다는 있는데 못 펼친다)
   inline fun ok(x, f)                          -> 조용하다
                                    ^
                          펼칠 수 있는 람다가 하나라도 있나?
```

그림 해설:

- ★★ **`onlyNoinline` 이 결정적이다.** 함수 타입 파라미터가 **있는데도** 경고가 났다 —\
  `noinline` 이라 펼칠 수 없기 때문이다. 즉 컴파일러가 보는 기준은 "함수 타입 파라미터가 있나" 가 아니라\
  **"펼칠 수 있는 람다가 있나"** 다. 그 하나만 있으면 `inline` 이 값을 하고, 없으면 "의미 없다" 고 말한다.
- 그래서 `inline` 의 목적은 **람다 객체를 없애는 것**이라고 컴파일러 스스로가 적어 둔 셈이다.
- ★ **경고를 보려면 에러가 없어야 한다.** 같은 파일에 컴파일 에러를 하나라도 섞었더니 **이 경고들이 통째로 안 나왔다**\
  (에러 시나리오 `warn.kt` 에서는 경고 0줄). **경고 시나리오와 에러 시나리오를 갈라서 던져야 보인다.**

비용 — 경고뿐, 컴파일은 통과한다(`exit 0`).

### (2) ★★ 한 글자 차이 — 두 클래스 파일을 나란히 놓는다

**언제 쓰나** — "`inline` 이 실제로 무엇을 바꾸나" 를 눈으로 확인할 때.

소스는 **`inline` 이라는 한 낱말만** 다르다.

```kotlin
// noinl.kt
fun twice(x: Int, f: (Int) -> Int): Int = f(f(x))

fun caller(): Int = twice(10) { it + 1 }
```

```kotlin
// inl.kt
inline fun twice(x: Int, f: (Int) -> Int): Int = f(f(x))

fun caller(): Int = twice(10) { it + 1 }
```

**출력** (`javap -c -p outno/NoinlKt.class`)

```text
Compiled from "noinl.kt"
public final class NoinlKt {
  public static final int twice(int, kotlin.jvm.functions.Function1<? super java.lang.Integer, java.lang.Integer>);
    Code:
       0: aload_1
       1: ldc           #10                 // String f
       3: invokestatic  #16                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_1
       7: aload_1
       8: iload_0
       9: invokestatic  #22                 // Method java/lang/Integer.valueOf:(I)Ljava/lang/Integer;
      12: invokeinterface #28,  2           // InterfaceMethod kotlin/jvm/functions/Function1.invoke:(Ljava/lang/Object;)Ljava/lang/Object;
      17: invokeinterface #28,  2           // InterfaceMethod kotlin/jvm/functions/Function1.invoke:(Ljava/lang/Object;)Ljava/lang/Object;
      22: checkcast     #30                 // class java/lang/Number
      25: invokevirtual #34                 // Method java/lang/Number.intValue:()I
      28: ireturn

  public static final int caller();
    Code:
       0: bipush        10
       2: invokedynamic #56,  0             // InvokeDynamic #0:invoke:()Lkotlin/jvm/functions/Function1;
       7: invokestatic  #58                 // Method twice:(ILkotlin/jvm/functions/Function1;)I
      10: ireturn

  private static final int caller$lambda$0(int);
    Code:
       0: iload_0
       1: iconst_1
       2: iadd
       3: ireturn
}
```

**출력** (`javap -c -p outin/InlKt.class`)

```text
Compiled from "inl.kt"
public final class InlKt {
  public static final int twice(int, kotlin.jvm.functions.Function1<? super java.lang.Integer, java.lang.Integer>);
    Code:
       0: aload_1
       1: ldc           #10                 // String f
       3: invokestatic  #16                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: iconst_0
       7: istore_2
       8: aload_1
       9: aload_1
      10: iload_0
      11: invokestatic  #22                 // Method java/lang/Integer.valueOf:(I)Ljava/lang/Integer;
      14: invokeinterface #28,  2           // InterfaceMethod kotlin/jvm/functions/Function1.invoke:(Ljava/lang/Object;)Ljava/lang/Object;
      19: invokeinterface #28,  2           // InterfaceMethod kotlin/jvm/functions/Function1.invoke:(Ljava/lang/Object;)Ljava/lang/Object;
      24: checkcast     #30                 // class java/lang/Number
      27: invokevirtual #34                 // Method java/lang/Number.intValue:()I
      30: ireturn

  public static final int caller();
    Code:
       0: bipush        10
       2: istore_0
       3: iconst_0
       4: istore_1
       5: iload_0
       6: istore_2
       7: iconst_0
       8: istore_3
       9: iload_2
      10: iconst_1
      11: iadd
      12: istore_2
      13: iconst_0
      14: istore_3
      15: iload_2
      16: iconst_1
      17: iadd
      18: nop
      19: ireturn
}
```

```text
   caller() — 비인라인                       caller() — 인라인
   +------------------------------------+    +---------------------------+
   | bipush 10                          |    | bipush 10                 |
   | invokedynamic -> Function1  ★객체  |    | istore / iload            |
   | invokestatic  twice(I, Function1)  |    | iconst_1 / iadd  ★람다 몸통|
   +------------------------------------+    | iconst_1 / iadd  ★두 번째 |
   | 그리고 twice 안에서                |    | ireturn                   |
   |   Integer.valueOf      ★박싱       |    +---------------------------+
   |   invoke(Object) 2회   ★호출       |     객체 0 · 박싱 0 · 호출 0
   |   checkcast + intValue ★언박싱     |
   +------------------------------------+
   | caller$lambda$0(int)   ★별도 메서드|    | (그런 메서드가 없다)      |
   +------------------------------------+    +---------------------------+
```

그림 해설:

- ★★ **인라인 쪽 `caller()` 에는 `invoke` 도, `valueOf` 도, `Function1` 도 없다.** `iadd` 두 번이 전부다 —\
  람다 몸통 `it + 1` 이 **두 번 베껴져** 들어갔다(`f(f(x))` 이므로).
- ★★ **`caller$lambda$0` 이 아예 사라졌다.** 비인라인 쪽에서는 람다 몸통이 그 별도 메서드에 살아 있다.\
  **이 한 줄이 (4)의 비지역 `return` 을 통째로 설명한다** — 몸통이 다른 메서드에 살면 거기서 `return` 해 봐야 그 메서드만 끝난다.
- ★ **`twice(int, Function1)` 본체는 양쪽 다 그대로 있다.** 인라인해도 함수가 **사라지지 않는다**((3)).
- 인라인 쪽 `twice` 안에 `iconst_0 / istore_2` 가 한 쌍 더 있는데, 이것은 인라인 경로용 표식(`$i$f$twice` 류의 지역 변수)이다 —\
  **동작에는 영향이 없고**, 인라인 쪽 코드에 일관되게 끼어 있다(`caller()` 안의 `iconst_0 / istore_1`·`istore_3` 도 같은 것이다).
- `bipush 10 -> istore_0 -> iload_0` 처럼 **값을 한 번 지역 변수에 넣었다 빼는** 모양이 남는다.\
  인라인은 "몸통을 붙여 넣는" 변환이지 **최적화가 아니다** — 다듬는 일은 JIT 의 몫이고 **이 문서는 그것을 재지 않았다.**

비용 — 호출 자리마다 몸통이 한 벌씩 늘어난다((8)에서 쟀다).

### (3) ★ 인라인인데도 **함수 본체가 남는다** — 누가 그것을 쓰나

**언제 쓰나** — "펼쳐 넣었는데 왜 메서드가 남아 있나" 가 궁금할 때.

(2)에서 본 것처럼 인라인해도 `twice(int, Function1)` 이 `public static final` 로 남는다.\
**그 본체를 쓰는 쪽이 실제로 있다 — Java 다.**

```kotlin
// api.kt
inline fun <reified T> isA(x: Any): Boolean = x is T
inline fun plain(x: Int, f: (Int) -> Int): Int = f(x)
fun normal(x: Int): Int = x + 1
```

**출력** (`javap -v -p oapi/ApiKt.class | grep -E 'public static final|  flags:'`)

```text
  flags: (0x0031) ACC_PUBLIC, ACC_FINAL, ACC_SUPER
  public static final <T extends java.lang.Object> boolean isA(java.lang.Object);
    flags: (0x1019) ACC_PUBLIC, ACC_STATIC, ACC_FINAL, ACC_SYNTHETIC
  public static final int plain(int, kotlin.jvm.functions.Function1<? super java.lang.Integer, java.lang.Integer>);
    flags: (0x0019) ACC_PUBLIC, ACC_STATIC, ACC_FINAL
  public static final int normal(int);
    flags: (0x0019) ACC_PUBLIC, ACC_STATIC, ACC_FINAL
```

```java
// UsePlain.java
import kotlin.jvm.functions.Function1;

public class UsePlain {
    public static void main(String[] a) {
        Function1<Integer, Integer> f = x -> x + 1;
        System.out.println("M Java calls inline plain(10) : " + ApiKt.plain(10, f));
        System.out.println("N Java calls normal(10)       : " + ApiKt.normal(10));
    }
}
```

**출력** (`javac -cp oapi:kotlin-stdlib.jar UsePlain.java` → `java UsePlain`)

```text
M Java calls inline plain(10) : 11
N Java calls normal(10)       : 11
```

그림 해설:

- ★ **평범한 `inline fun` 은 Java 에서 그냥 보이고 그냥 불린다.** 플래그가 `ACC_PUBLIC, ACC_STATIC, ACC_FINAL` 로\
  `normal` 과 **똑같다**. Java 쪽에서는 당연히 **인라인이 일어나지 않는다** — `Function1` 객체를 직접 만들어 넘겼다.
- 즉 **`inline` 은 Kotlin 컴파일러의 변환이지 클래스 파일의 성질이 아니다.** 남아 있는 본체가 그 증거다.
- ★ **`reified` 가 붙으면 달라진다** — `isA` 만 `ACC_SYNTHETIC` 이 붙어 `javac` 가 **못 본다**.\
  그것이 [12번 주제](../12-reified-type-parameters/)의 핵심이고, 여기서는 **"인라인 본체는 남지만 `reified` 인라인 본체는 Java 에게 감춰진다"** 까지만 적는다.

비용 — 없다. 본체가 남는 것은 상호운용을 위한 것이고, 호출자가 Kotlin 이면 그 본체를 안 거친다.

### (4) ★★ 비지역 `return` — **호출자 메서드의 `areturn` 그 자체**가 된다

**언제 쓰나** — `forEach` 안에서 바깥 함수를 빠져나오고 싶을 때, 그리고 그게 왜 되는지 물을 때.

`kotlin.collections.forEach` 는 stdlib 의 **인라인 함수**다. 그래서 이렇게 쓸 수 있다.

```kotlin
// nlr.kt
fun hasNeg(xs: List<Int>): String {
    xs.forEach { if (it < 0) return "neg" }
    return "none"
}

fun hasNegLabel(xs: List<Int>): String {
    xs.forEach { if (it < 0) return@forEach }
    return "none"
}

fun main() {
    println("A hasNeg([1,-2,3])      : ${hasNeg(listOf(1, -2, 3))}")
    println("B hasNeg([1,2,3])       : ${hasNeg(listOf(1, 2, 3))}")
    println("C hasNegLabel([1,-2,3]) : ${hasNegLabel(listOf(1, -2, 3))}")
}
```

**출력** (`java NlrKt`)

```text
A hasNeg([1,-2,3])      : neg
B hasNeg([1,2,3])       : none
C hasNegLabel([1,-2,3]) : none
```

**출력** (`javap -c -p outnlr/NlrKt.class` — 두 함수만 발췌)

```text
  public static final java.lang.String hasNeg(java.util.List<java.lang.Integer>);
    Code:
       0: aload_0
       1: ldc           #10                 // String xs
       3: invokestatic  #16                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_0
       7: checkcast     #18                 // class java/lang/Iterable
      10: astore_1
      11: iconst_0
      12: istore_2
      13: aload_1
      14: invokeinterface #22,  1           // InterfaceMethod java/lang/Iterable.iterator:()Ljava/util/Iterator;
      19: astore_3
      20: aload_3
      21: invokeinterface #28,  1           // InterfaceMethod java/util/Iterator.hasNext:()Z
      26: ifeq          62
      29: aload_3
      30: invokeinterface #32,  1           // InterfaceMethod java/util/Iterator.next:()Ljava/lang/Object;
      35: astore        4
      37: aload         4
      39: checkcast     #34                 // class java/lang/Number
      42: invokevirtual #38                 // Method java/lang/Number.intValue:()I
      45: istore        5
      47: iconst_0
      48: istore        6
      50: iload         5
      52: ifge          58
      55: ldc           #40                 // String neg
      57: areturn
      58: nop
      59: goto          20
      62: nop
      63: ldc           #42                 // String none
      65: areturn

  public static final java.lang.String hasNegLabel(java.util.List<java.lang.Integer>);
    Code:
       0: aload_0
       1: ldc           #10                 // String xs
       3: invokestatic  #16                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_0
       7: checkcast     #18                 // class java/lang/Iterable
      10: astore_1
      11: iconst_0
      12: istore_2
      13: aload_1
      14: invokeinterface #22,  1           // InterfaceMethod java/lang/Iterable.iterator:()Ljava/util/Iterator;
      19: astore_3
      20: aload_3
      21: invokeinterface #28,  1           // InterfaceMethod java/util/Iterator.hasNext:()Z
      26: ifeq          59
      29: aload_3
      30: invokeinterface #32,  1           // InterfaceMethod java/util/Iterator.next:()Ljava/lang/Object;
      35: astore        4
      37: aload         4
      39: checkcast     #34                 // class java/lang/Number
      42: invokevirtual #38                 // Method java/lang/Number.intValue:()I
      45: istore        5
      47: iconst_0
      48: istore        6
      50: iload         5
      52: ifge          55
      55: nop
      56: goto          20
      59: nop
      60: ldc           #42                 // String none
      62: areturn
```

```text
   비지역 return                          return@forEach
   +---------------------------------+    +---------------------------------+
   | 52: ifge  58                    |    | 52: ifge  55                    |
   | 55: ldc   "neg"                 |    | 55: nop        <- 바로 다음 줄  |
   | 57: areturn   ★ hasNeg 가 끝난다|    | 56: goto  20   <- 다음 바퀴     |
   | 58: nop                         |    | 59: nop                         |
   | 59: goto  20                    |    | 60: ldc   "none"                |
   | 63: ldc   "none"                |    | 62: areturn                     |
   +---------------------------------+    +---------------------------------+
     areturn 이 두 개                       areturn 이 하나
```

그림 해설:

- ★★ **`hasNeg` 안에 `areturn` 이 두 개다.** 57번 자리의 `areturn` 은 **람다 안에 적은 `return "neg"`** 이고,\
  그것이 **`hasNeg` 자신의 반환 명령**으로 박혀 있다. 람다라는 경계가 바이트코드에 **남아 있지 않다.**
- ★ `hasNegLabel` 의 `return@forEach` 는 `areturn` 이 **아니다.** `ifge 55 / 55: nop / 56: goto 20` —\
  **조건이 참이면 아무것도 안 하고 다음 바퀴로 간다.** 그래서 `C` 가 `none` 이다.\
  라벨 붙은 `return` 은 **`continue` 에 가깝고**, 라벨 없는 `return` 은 **바깥 함수를 끝낸다.**
- ★ `Function1` 이 **한 번도 안 나온다.** `forEach` 자체가 인라인이라 `iterator()` 루프째 `hasNeg` 안으로 들어왔다.

**그래서 인라인이 아니면 왜 안 되나** — (2)의 비인라인 쪽 그림을 보면 답이 이미 있다.\
람다 몸통이 **`caller$lambda$0` 이라는 다른 메서드**에 산다. 거기서 `ireturn` 을 해 봐야 **그 메서드만 끝난다** —\
`caller()` 를 끝낼 방법이 없다. 그래서 컴파일러는 아예 **거부한다.**

```text
===== 소스: bad0.kt =====
fun runIt(f: (Int) -> Int): Int = f(1)

fun outer(): Int {
    runIt { return 5 }
    return 0
}
===== kotlinc bad0.kt =====
bad0.kt:4:13: error: 'return' is prohibited here.
    runIt { return 5 }
            ^^^^^^
(exit 1)
```

비용 — 없다. 비지역 `return` 은 인라인이 이미 만든 구조를 **쓰는** 것이지 추가 비용이 아니다.

### (5) `noinline` — **그 람다 하나만** 다시 객체로 되돌린다

**언제 쓰나** — 인라인 함수가 받은 람다를 **값으로 저장하거나 반환해야** 할 때.

```kotlin
// noin.kt
inline fun both(x: Int, f: (Int) -> Int, noinline g: (Int) -> Int): Int = g(f(x))

fun store(g: (Int) -> Int): (Int) -> Int = g

fun caller(): Int = both(10, { it + 1 }, { it * 2 })
```

**출력** (`javap -c -p outnoin/NoinKt.class` — `caller` 와 합성 메서드만 발췌)

```text
  public static final int caller();
    Code:
       0: bipush        10
       2: istore_0
       3: invokedynamic #62,  0             // InvokeDynamic #0:invoke:()Lkotlin/jvm/functions/Function1;
       8: astore_1
       9: iconst_0
      10: istore_2
      11: aload_1
      12: iload_0
      13: istore_3
      14: astore        5
      16: iconst_0
      17: istore        4
      19: iload_3
      20: iconst_1
      21: iadd
      22: invokestatic  #24                 // Method java/lang/Integer.valueOf:(I)Ljava/lang/Integer;
      25: aload         5
      27: swap
      28: invokeinterface #30,  2           // InterfaceMethod kotlin/jvm/functions/Function1.invoke:(Ljava/lang/Object;)Ljava/lang/Object;
      33: checkcast     #32                 // class java/lang/Number
      36: invokevirtual #36                 // Method java/lang/Number.intValue:()I
      39: ireturn

  private static final int caller$lambda$1(int);
    Code:
       0: iload_0
       1: iconst_2
       2: imul
       3: ireturn
}
```

```text
   both(10, { it + 1 }, { it * 2 })
             ~~~~~~~~    ~~~~~~~~
             f: inline   g: noinline
                |            |
                v            v
          iconst_1 / iadd   invokedynamic -> Function1 객체
          (펼쳐졌다)         invoke(Object) + 박싱/언박싱
```

그림 해설:

- ★ **`invokedynamic` 이 딱 하나**다 — `noinline` 인 `g` 쪽만 객체가 됐다. `f` 는 `iconst_1 / iadd` 로 펼쳐졌다.
- ★★ **합성 메서드 이름이 `caller$lambda$1` 로 1번부터 시작한다.** 0번은 `f` 의 몫이었는데 **펼쳐져 사라졌다** —\
  **번호에 빈칸이 남은 것이 "여기 람다가 하나 있었다" 는 자국**이다.
- `g` 쪽에는 `Integer.valueOf` → `invoke(Object)` → `checkcast Number` → `intValue` 가 그대로 살아 있다.\
  **`noinline` 은 박싱까지 함께 되돌린다.**
- `store(g)` 처럼 **람다를 값으로 내보내야 하면** `noinline` 이 필수다 — 안 붙이면 (7)의 첫 번째 에러가 난다.

비용 — `noinline` 붙은 람다 하나당 객체 하나 + 박싱 왕복.

### (6) ★★ `crossinline` — 펼치기는 한다. 문제는 **어디에** 펼치느냐다

**언제 쓰나** — 인라인 함수가 받은 람다를 **다른 객체 안에서** 실행해야 할 때.

```kotlin
// cross.kt
inline fun guard(crossinline f: (Int) -> Int): Int {
    val r = Runnable { f(1) }
    r.run()
    return f(2)
}

fun caller(): Int = guard { it + 1 }
```

**출력** (`find ocross -name '*.class' | sort`)

```text
ocross/CrossKt$caller$$inlined$guard$1.class
ocross/CrossKt$guard$r$1.class
ocross/CrossKt.class
```

**출력** (`javap -c -p ocross/CrossKt.class` — `caller` 만 발췌)

```text
  public static final int caller();
    Code:
       0: iconst_0
       1: istore_0
       2: new           #54                 // class CrossKt$caller$$inlined$guard$1
       5: dup
       6: invokespecial #56                 // Method CrossKt$caller$$inlined$guard$1."<init>":()V
       9: checkcast     #24                 // class java/lang/Runnable
      12: astore_1
      13: aload_1
      14: invokeinterface #28,  1           // InterfaceMethod java/lang/Runnable.run:()V
      19: iconst_2
      20: istore_2
      21: iconst_0
      22: istore_3
      23: iload_2
      24: iconst_1
      25: iadd
      26: nop
      27: ireturn
}
```

**출력** (`javap -c -p 'ocross/CrossKt$caller$$inlined$guard$1.class'`)

```text
Compiled from "cross.kt"
public final class CrossKt$caller$$inlined$guard$1 implements java.lang.Runnable {
  public CrossKt$caller$$inlined$guard$1();
    Code:
       0: aload_0
       1: invokespecial #15                 // Method java/lang/Object."<init>":()V
       4: return

  public final void run();
    Code:
       0: iconst_1
       1: istore_1
       2: iconst_0
       3: istore_2
       4: iload_1
       5: iconst_1
       6: iadd
       7: pop
       8: return
}
```

**출력** (`javap -c -p 'ocross/CrossKt$guard$r$1.class'`)

```text
Compiled from "cross.kt"
public final class CrossKt$guard$r$1 implements java.lang.Runnable {
  final kotlin.jvm.functions.Function1<java.lang.Integer, java.lang.Integer> $f;

  public CrossKt$guard$r$1(kotlin.jvm.functions.Function1<? super java.lang.Integer, java.lang.Integer>);
    Code:
       0: aload_0
       1: aload_1
       2: putfield      #13                 // Field $f:Lkotlin/jvm/functions/Function1;
       5: aload_0
       6: invokespecial #16                 // Method java/lang/Object."<init>":()V
       9: return

  public final void run();
    Code:
       0: aload_0
       1: getfield      #13                 // Field $f:Lkotlin/jvm/functions/Function1;
       4: iconst_1
       5: invokestatic  #25                 // Method java/lang/Integer.valueOf:(I)Ljava/lang/Integer;
       8: invokeinterface #31,  2           // InterfaceMethod kotlin/jvm/functions/Function1.invoke:(Ljava/lang/Object;)Ljava/lang/Object;
      13: pop
      14: return
}
```

```text
   caller() 안                              그 Runnable 안
   +---------------------------------+      +-----------------------------+
   | return f(2) 자리                |      | run() {                     |
   |   iconst_2 / iconst_1 / iadd    |      |   iconst_1 / iconst_1 / iadd|
   |   ← 람다 몸통이 펼쳐졌다        |      |   ← 여기에도 펼쳐졌다       |
   |                                 |      |   return   ← run() 만 끝낸다|
   | ireturn  ← caller() 를 끝낸다   |      | }                           |
   +---------------------------------+      +-----------------------------+
                                             이 return 으로는 caller() 를 못 끝낸다
                                                     ↑
                                          그래서 crossinline 은 비지역 return 을 금지한다
```

그림 해설:

- ★★ **`crossinline` 도 펼치기는 한다.** `return f(2)` 자리는 `iconst_2 / iconst_1 / iadd` 로 몸통이 들어갔고 객체가 없다.
- ★★ **그런데 클래스가 두 개 생겼다.** 그리고 **역할이 다르다.**
  - `CrossKt$guard$r$1` — **선언 쪽**의 본체용. `$f` 라는 `Function1` **필드**를 들고 `invoke(Object)` 를 부른다.\
    (3)에서 본 "Java 용으로 남는 본체" 와 같은 성격이다.
  - `CrossKt$caller$$inlined$guard$1` — ★ **호출 자리별 전용.** 이름에 `caller` 가 박혀 있다.\
    **필드가 없고** `run()` 안에 람다 몸통이 `iadd` 로 **직접 박혀 있다.**
  - 즉 **호출 자리가 늘면 이 클래스도 자리마다 하나씩 는다** — 선언당 하나가 아니다.
- ★★ **금지의 이유가 그림에 다 나와 있다.** 람다 몸통이 `run()` 안으로 들어갔는데,\
  `run()` 의 `return` 은 `run()` 만 끝낸다. **`caller()` 를 끝낼 방법이 없다.**\
  그래서 `crossinline` 은 "펼쳐는 주되 **비지역 `return` 은 쓰지 마라**" 는 약속이다.
- 그 약속을 안 하면 컴파일러가 (7)의 두 번째 에러로 **`crossinline` 을 붙이라고 이름까지 말해 준다.**

비용 — 호출 자리마다 클래스 파일 하나 + 그 객체 하나. **`noinline` 과 달리 박싱은 안 생긴다**(몸통이 안에 박혀 있다).

### (7) `inline` 이 거부하는 것들 — **에러가 고치는 법을 이름으로 말해 준다**

**언제 쓰나** — `inline` 을 붙였는데 컴파일이 깨질 때.

**출력** (`kotlinc bad1.kt`)

```text
===== 소스: bad1.kt =====
inline fun keep(f: (Int) -> Int): (Int) -> Int = f

inline fun later(f: (Int) -> Int): Runnable = Runnable { f(1) }
===== kotlinc bad1.kt =====
bad1.kt:1:50: error: illegal usage of inline parameter 'f: (Int) -> Int'. Add 'noinline' modifier to the parameter declaration.
inline fun keep(f: (Int) -> Int): (Int) -> Int = f
                                                 ^
bad1.kt:3:58: error: cannot inline 'f: (Int) -> Int' here: it might contain non-local returns. Add 'crossinline' modifier to parameter declaration 'f: (Int) -> Int'.
inline fun later(f: (Int) -> Int): Runnable = Runnable { f(1) }
                                                         ^
(exit 1)
```

**출력** (`kotlinc bad4.kt`)

```text
===== 소스: bad4.kt =====
private fun secret(x: Int): Int = x * 2

inline fun exposed(x: Int): Int = secret(x)

internal inline fun internalOk(x: Int): Int = secret(x)
===== kotlinc bad4.kt =====
bad4.kt:3:35: error: public-API inline function cannot access non-public-API function.
inline fun exposed(x: Int): Int = secret(x)
                                  ^^^^^^
(exit 1)
```

**출력** (`kotlinc pub.kt`)

```text
===== 소스: pub.kt =====
@PublishedApi
internal fun secret(x: Int): Int = x * 2

inline fun exposed(x: Int): Int = secret(x)
===== kotlinc pub.kt =====
pub.kt:4:1: warning: expected performance impact from inlining is insignificant. Inlining works best for functions with parameters of function types.
inline fun exposed(x: Int): Int = secret(x)
^^^^^^
(exit 0)
```

**출력** (`kotlinc bad5.kt`)

```text
===== 소스: bad5.kt =====
inline fun countDown(n: Int, f: (Int) -> Unit) {
    if (n <= 0) return
    f(n)
    countDown(n - 1, f)
}
===== kotlinc bad5.kt =====
bad5.kt:4:5: error: inline function 'fun countDown(n: Int, f: (Int) -> Unit): Unit' cannot be recursive.
    countDown(n - 1, f)
    ^^^^^^^^^
(exit 1)
```

**출력** (`kotlinc warn.kt`)

```text
===== 소스: warn.kt =====
inline fun noLambda(x: Int): Int = x + 1

inline fun onlyNoinline(x: Int, noinline f: (Int) -> Int): Int = f(x)

inline fun nullableLambda(x: Int, f: ((Int) -> Int)?): Int = f?.invoke(x) ?: x

inline fun ok(x: Int, f: (Int) -> Int): Int = f(x)
===== kotlinc warn.kt =====
warn.kt:5:35: error: inline parameter 'f: ((Int) -> Int)?' of 'fun nullableLambda(x: Int, f: ((Int) -> Int)?): Int' cannot be nullable. Add 'noinline' modifier to the parameter declaration or make its type not nullable.
inline fun nullableLambda(x: Int, f: ((Int) -> Int)?): Int = f?.invoke(x) ?: x
                                  ^^^^^^^^^^^^^^^^^^
(exit 1)
```

그림 해설:

- ★ **네 에러 중 셋이 고치는 법을 문장에 담고 있다** — `Add 'noinline' modifier` · `Add 'crossinline' modifier` ·\
  `Add 'noinline' modifier ... or make its type not nullable`. **에러 메시지가 교재인 언어**의 전형이다.
- ★★ **`internal inline fun internalOk` 는 에러가 안 났다.** 같은 `private` 함수를 부르는데도.\
  막히는 것은 **공개 API 인 인라인 함수**뿐이다 — 몸통이 **남의 모듈 안으로 복사돼 들어가기** 때문이다.\
  그쪽에서는 `private` 선언이 안 보인다.
- 고치는 법은 `@PublishedApi internal` 이다 — "이 선언은 **바이너리로는 공개**" 라는 표시다. `pub.kt` 가 통과했다.
- ★ **인라인 파라미터는 nullable 일 수 없다.** 펼치려면 "그 자리에 람다가 **있다**" 가 보장돼야 하는데 `null` 이면 그게 깨진다.
- ★ **인라인 함수는 재귀일 수 없다.** 펼치기가 끝나지 않기 때문이다 — **컴파일러가 그 말을 그대로 한다.**

비용 — 컴파일 실패. 고치는 법이 전부 메시지 안에 있다.

### (8) ★ 대가는 **코드 크기**다 — 성능이 아니라 크기를 쟀다

**언제 쓰나** — "그럼 전부 `inline` 붙이면 되지 않나" 고 생각할 때.

같은 소스를 `inline` 만 붙였다 뗐다 하며 **다섯 자리에서 호출**했다.

```kotlin
// sizeN.kt  (sizeI.kt 는 첫 줄이 'inline fun twice' 인 것만 다르다)
fun twice(x: Int, f: (Int) -> Int): Int = f(f(x))

fun c1(): Int = twice(1) { it + 1 }
fun c2(): Int = twice(2) { it + 1 }
fun c3(): Int = twice(3) { it + 1 }
fun c4(): Int = twice(4) { it + 1 }
fun c5(): Int = twice(5) { it + 1 }
```

```kotlin
// bigN.kt  (bigI.kt 는 첫 줄이 'inline fun heavy' 인 것만 다르다)
fun heavy(x: Int, f: (Int) -> Int): Int {
    var a = f(x); a += f(a); a += f(a); a += f(a); a += f(a)
    a += f(a); a += f(a); a += f(a); a += f(a); a += f(a)
    return a
}

fun c1(): Int = heavy(1) { it + 1 }
fun c2(): Int = heavy(2) { it + 1 }
fun c3(): Int = heavy(3) { it + 1 }
fun c4(): Int = heavy(4) { it + 1 }
fun c5(): Int = heavy(5) { it + 1 }
```

**출력** (`ls -l` 의 바이트 칸 · `javap -c -p <클래스> | grep -cE '^[[:space:]]+[0-9]+:'`)

```text
===== ls -l outsn/SizeNKt.class outsi/SizeIKt.class =====
2599 outsi/SizeIKt.class
2338 outsn/SizeNKt.class
===== ls -l outbn/BigNKt.class outbi/BigIKt.class =====
4868 outbi/BigIKt.class
2525 outbn/BigNKt.class
===== javap -c -p <클래스> | grep -cE '^[[:space:]]+[0-9]+:' =====
outsn/SizeNKt.class    52
outsi/SizeIKt.class    109
outbn/BigNKt.class     133
outbi/BigIKt.class     795
===== c1() 한 메서드만 =====
outbn/BigNKt.class     4
outbi/BigIKt.class     140
```

| 몸통 | 잰 것 | 비인라인 | 인라인 | 배수 |
|---|---|---|---|---|
| 작은 몸통 `f(f(x))` · 5호출 | 클래스 파일 바이트 | 2,338 | 2,599 | 1.11배 |
| 〃 | 역어셈블 명령 줄 | 52 | 109 | 2.10배 |
| 큰 몸통 `f` 10회 · 5호출 | 클래스 파일 바이트 | 2,525 | 4,868 | 1.93배 |
| 〃 | 역어셈블 명령 줄 | 133 | 795 | 5.98배 |
| 〃 | ★ `c1()` **한 메서드** | 4 | 140 | 35배 |

그림 해설:

- ★★ **`c1()` 한 메서드가 명령 4줄에서 140줄이 됐다.** 비인라인 쪽 `c1()` 은 `invokedynamic` + `invokestatic` + 상수 + `ireturn`\
  넷이면 끝인데, 인라인 쪽은 `heavy` 의 몸통 열 번 호출이 통째로 들어왔다.
- **몸통이 클수록, 호출 자리가 많을수록 곱해진다.** 위 표에서 몸통만 키웠는데 배수가 2.1 → 6.0 으로 올랐다.
- ★★ **여기서 잰 것은 크기뿐이다.** 실행 시간·JIT 인라인 한계·아이캐시 같은 것은 **한 번도 재지 않았다.**\
  "코드가 커지면 느려질 수 있다" 는 **이 문서가 하지 않은 주장**이다. 컴파일러가 하는 말((1)의 경고)까지가 근거의 끝이다.

비용 — 위 표 그대로. 그리고 [10번 주제](../10-lambdas-and-higher-order-functions/)가 재는 쪽(객체 생성)의 대가와 **맞바꾸는 관계**다.

### (9) 타깃을 21 로 올려도 **한 글자도 안 바뀌었다**

**언제 쓰나** — "이 결론이 `-jvm-target` 에 흔들리나" 를 확인해야 할 때.

Kotlin 문법 주제에서 바이트코드 주장은 **타깃을 밝혀야** 성립한다.\
그래서 (2)의 두 파일을 `-jvm-target 21` 로 다시 찍어 `diff` 했다.

**출력**

```text
=== major ===
  major version: 65
===== 21 에서 전체 diff (1.8 대비) =====
noinl: 1.8 과 21 이 같다
inl: 1.8 과 21 이 같다
```

그림 해설:

- `major version` 만 **52 → 65** 로 바뀌고 `javap -c -p` 출력은 **한 글자도 다르지 않았다.**
- ★ **그러니 이 주제의 결론은 타깃에 안 걸린다** — 인라인 전개·`invokedynamic` 유무·비지역 `return` 의 `areturn` 전부.\
  다만 **"같았다" 는 관찰이지 보장이 아니다**(두 타깃만 봤다). 보장으로 적은 것은 언어 문서에 있는 것뿐이다.
- 이 주제가 **`-jvm-target` 에 안 흔들린 이유**는, 인라인이 **프런트엔드 변환**이라 클래스 파일 버전이 고르는\
  `invokedynamic`·문자열 연결 전략 같은 **백엔드 선택지와 겹치지 않기** 때문이다(이 설명은 관찰의 해석이다).

비용 — 없다. 확인 한 번.

## 문법 — 형태와 규칙

```kotlin
// 1) 기본형 — 펼칠 수 있는 람다가 하나라도 있어야 값을 한다
inline fun <T> measureAndRun(tag: String, body: () -> T): T = body()

// 2) noinline — 그 람다만 객체로. 저장·반환·값으로 넘길 때 필수
inline fun both(f: (Int) -> Int, noinline g: (Int) -> Int): (Int) -> Int {
    f(1)
    return g            // noinline 이 아니면 에러
}

// 3) crossinline — 다른 객체 몸통 안에서 부를 때. 비지역 return 금지
inline fun later(crossinline f: () -> Unit): Runnable = Runnable { f() }

// 4) 비지역 return — 인라인 람다 안에서 바깥 함수를 끝낸다
fun firstNeg(xs: List<Int>): Int? {
    xs.forEach { if (it < 0) return it }   // firstNeg 가 끝난다
    return null
}

// 5) 라벨 붙은 return — 람다만 끝낸다(다음 바퀴로 간다)
fun countPos(xs: List<Int>): Int {
    var n = 0
    xs.forEach { if (it < 0) return@forEach; n++ }
    return n
}

// 6) 공개 API 인라인 함수가 internal 선언을 봐야 할 때
@PublishedApi
internal fun helper(x: Int): Int = x * 2
inline fun exposed(x: Int): Int = helper(x)
```

규칙 불릿.

- **`inline` 은 선언에 붙이고 호출자에 효과가 난다.** 호출자마다 몸통이 한 벌씩 복사된다.
- **함수 본체는 그래도 남는다** — Java 가 부를 수 있다((3)).
- **`noinline` 파라미터만 값처럼 다룰 수 있다.** 저장·반환·다른 함수에 넘기기 전부 그렇다.
- **다른 객체 몸통 안에서 부르려면 `crossinline`.** 그 대가가 비지역 `return` 금지다.
- **인라인 파라미터는 nullable 일 수 없다.** `noinline` 을 붙이거나 타입에서 `?` 를 뺀다.
- **인라인 함수는 재귀일 수 없다.**
- **공개 API 인라인 함수는 `private`·`internal` 선언을 못 본다.** `@PublishedApi internal` 로 연다.
- **`return` 은 바깥 함수를, `return@이름` 은 람다를 끝낸다.** 인라인이 아니면 앞엣것이 **에러**다.

## 어디서 틀리나

| 틀리는 형태 | 무슨 일이 일어나나 | 고치는 법 |
|---|---|---|
| "호출이 비싸니까 `inline`" | 컴파일러가 **`expected performance impact from inlining is insignificant`** 로 경고한다 | 람다를 받는 함수에만 붙인다 |
| 람다를 받으면 무조건 값이 있다고 봄 | **`noinline` 뿐이면 그래도 경고가 난다**((1)) | 「펼칠 수 있는 람다가 있나」로 판단한다 |
| 인라인 람다를 변수에 담거나 반환 | `illegal usage of inline parameter … Add 'noinline' modifier …` | `noinline` 을 붙인다 |
| 인라인 람다를 `Runnable`·`object` 안에서 호출 | `cannot inline … it might contain non-local returns. Add 'crossinline' …` | `crossinline` 을 붙인다 |
| `crossinline` 인데 비지역 `return` 을 씀 | `'return' is prohibited here.` | `return@라벨` 로 바꾸거나 설계를 바꾼다 |
| `noinline` 인데 비지역 `return` 을 씀 | **같은 문구** `'return' is prohibited here.` | 〃 |
| 비인라인 고차 함수에 `return` 을 씀 | **또 같은 문구** — 셋을 구분할 단서가 메시지에 없다 | 선언 쪽의 `inline`/`noinline`/`crossinline` 을 본다 |
| `crossinline` 이면 객체가 안 생긴다고 봄 | ★ **호출 자리마다 클래스가 하나씩 생긴다**((6)) | 자리 수를 세어 본다 |
| 공개 인라인 함수에서 `private` 헬퍼 호출 | `public-API inline function cannot access non-public-API function.` | `@PublishedApi internal` 또는 `internal inline` |
| `internal inline` 도 막힐 거라고 봄 | ★ **안 막힌다** — 공개 API 만 막힌다 | 가시성을 확인한다 |
| 인라인 파라미터를 `((Int) -> Int)?` 로 선언 | `inline parameter … cannot be nullable.` | `noinline` 을 붙이거나 `?` 를 뺀다 |
| 인라인 함수를 재귀로 씀 | `inline function … cannot be recursive.` | `inline` 을 떼거나 루프로 바꾼다 |
| `return@forEach` 가 루프를 끊는다고 봄 | ★ **다음 바퀴로 간다**(`goto`) — `continue` 쪽이다 | 끊으려면 비지역 `return` 이나 `break`([07번 주제](../07-loops-ranges-and-labels/)) |
| 인라인이 함수를 **없앤다**고 봄 | 본체가 `public static final` 로 남아 Java 가 부른다 | (3) |
| 전부 `inline` 을 붙임 | ★ 큰 몸통 다섯 자리에서 `c1()` 이 **명령 4줄 → 140줄**((8)) | 람다를 받는 작은 함수에만 |

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 | 근거 |
|---|---|---|
| 인라인 람다 안에서 비지역 `return` 이 되는 것 | **언어** | 문서 + 실행 |
| 비인라인·`noinline`·`crossinline` 람다에서 비지역 `return` 이 금지되는 것 | **언어** | 컴파일 에러 3벌 |
| `return@라벨` 이 람다만 끝내는 것 | **언어** | 실행(`C none` — (4)) |
| 인라인 파라미터를 값으로 다루려면 `noinline` 이 필요한 것 | **언어** | 컴파일 에러 |
| 다른 객체 몸통에서 부르려면 `crossinline` 이 필요한 것 | **언어** | 컴파일 에러 |
| 인라인 파라미터가 nullable 일 수 없는 것 | **언어** | 컴파일 에러 |
| 인라인 함수가 재귀일 수 없는 것 | **언어** | 컴파일 에러 |
| 공개 API 인라인이 비공개 선언을 못 보는 것 | **언어** | 컴파일 에러 + 문서 |
| `@PublishedApi internal` 이 그것을 여는 것 | **언어** | 컴파일 통과 |
| **인라인이 `invokedynamic` 을 없애는 것** | **구현** ★★ | `javap` (2) |
| **비지역 `return` 이 호출자의 `areturn` 이 되는 것** | **구현** ★★ | `javap` (4) |
| **`return@라벨` 이 `goto` 가 되는 것** | **구현** | `javap` (4) |
| **`noinline` 쪽에 `caller$lambda$1` 이 남고 0번이 비는 것** | **구현** | `javap` (5) |
| **`crossinline` 이 호출 자리별 클래스를 만드는 것** | **구현** ★★ | 클래스 파일 목록 + `javap` (6) |
| **인라인 함수 본체가 클래스 파일에 남는 것** | **구현(+상호운용 계약)** | `javap` + Java 호출 성공 (3) |
| **`reified` 인라인만 `ACC_SYNTHETIC` 인 것** | **구현** | `javap -v` — 정본은 [12번 주제](../12-reified-type-parameters/) |
| **코드 크기 배수** | **이 머신의 측정값** | `ls -l` · `javap` 줄 수 (8) |
| **`-jvm-target 21` 에서도 같았던 것** | **관찰(두 타깃)** | `diff` (9) |

★ **가장 중요한 구분 한 줄** — **"비지역 `return` 이 된다" 는 언어 보장이고,\
"그것이 `areturn` 으로 박힌다" 는 `javap` 로 본 구현이다.** 그리고 **"그래서 빠르다" 는 둘 다 아니다** — 재지 않았다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 람다를 받는 작은 유틸(`forEach`·`let`·`use` 류) | `inline` | 객체와 박싱이 사라지고 비지역 `return` 이 열린다 |
| 람다 안에서 바깥 함수를 빠져나와야 할 때 | `inline` | 그것이 **인라인이 아니면 불가능**하다 |
| `reified` 타입 파라미터가 필요할 때 | `inline` | 선택이 아니라 **전제**다([12번 주제](../12-reified-type-parameters/)) |
| 람다를 필드·리스트에 저장해야 할 때 | `noinline` | 값이 있어야 저장한다 |
| 람다를 `Runnable`·콜백 객체 안에서 실행할 때 | `crossinline` | 그 자리엔 펼칠 수 있지만 `return` 이 성립 안 한다 |
| 람다를 **안 받는** 함수 | `inline` **안 쓴다** | 컴파일러가 의미 없다고 경고한다 |
| 몸통이 크고 호출 자리가 많을 때 | `inline` **안 쓴다** | 코드 크기가 곱해진다((8)) |
| 공개 라이브러리 API | 신중히 | 몸통이 **남의 모듈에 복사**돼 들어간다 — 바꾸면 재컴파일 전까지 옛 몸통이 산다 |
| Java 에서도 쓸 API | `inline` 의 값이 없다 | Java 쪽은 본체를 부르고 인라인이 안 된다((3)) |
| 성능 때문에 붙이고 싶을 때 | **먼저 재라** | 이 문서는 **재지 않았다**. 근거 없이 붙이는 것은 크기만 늘린다 |

판단 규칙 두 줄.

- **`inline` 은 「람다를 받나」로 정한다.** 안 받으면 컴파일러가 직접 아니라고 말한다.
- **`noinline` 은 「그 람다를 값으로 쓰나」, `crossinline` 은 「그 람다를 남의 몸통 안에서 부르나」로 정한다.**

## 핵심 문장

- ★★ **`inline` 은 호출 비용을 위한 것이 아니다.** 람다를 안 받으면 컴파일러가\
  `expected performance impact from inlining is insignificant` 라고 **직접 말한다**.
- ★ 그 기준은 "함수 타입 파라미터가 있나" 가 아니라 **"펼칠 수 있는 람다가 있나"** 다 —\
  `noinline` 뿐인 함수도 같은 경고를 받는다.
- 한 낱말 차이로 `caller()` 가 **`invokedynamic` + `Function1` + 박싱**에서 **`iadd` 두 번**으로 바뀐다.
- ★ 인라인하면 **람다 몸통 메서드(`caller$lambda$0`)가 사라진다.** 그런데 **함수 본체는 남는다** — Java 가 그것을 부른다.
- ★★ **비지역 `return` 은 호출자 메서드의 `areturn` 그 자체다.** 람다 경계가 바이트코드에 없다.
- ★★ **인라인이 아니면 람다 몸통이 다른 메서드에 산다** — 그래서 `return` 이 바깥을 못 끝내고,\
  컴파일러가 `'return' is prohibited here.` 로 **거부한다**.
- `return@라벨` 은 `areturn` 이 아니라 **`goto`** 다 — `continue` 쪽이다.
- `noinline` 은 **그 람다만** 객체로 되돌린다. 박싱도 함께 돌아온다. 합성 메서드 번호에 **빈칸**이 남는다.
- ★★ **`crossinline` 도 펼친다.** 다만 **남의 객체 몸통 안으로** 펼치고, 그래서 **호출 자리마다 클래스가 하나 생긴다**.\
  그 `run()` 의 `return` 으로는 호출자를 못 끝내므로 **비지역 `return` 을 금지**한다.
- 공개 API 인라인은 비공개 선언을 못 본다 — 몸통이 **남의 모듈로 복사**되기 때문이다. `internal inline` 은 안 막힌다.
- ★ **잰 대가는 코드 크기뿐이다.** 큰 몸통 다섯 자리에서 `c1()` 이 **명령 4줄 → 140줄**이 됐다.\
  **「그래서 어느 쪽이 빠르다」는 이 문서가 하지 않은 주장이다.**

## 관련 자료

- [`../README.md`](../README.md) — Kotlin 문법·API 주제 목록(이 주제는 11번)
- [10번 주제](../10-lambdas-and-higher-order-functions/) — **직접 선행.** 람다가 `invokedynamic` + `Function1` 이 되는 것,\
  박싱이 어디서 생기는지, 객체가 몇 개인지가 **거기가 정본**이다. 여기는 **그것을 없애는 쪽**만 다뤘다
- [12번 주제](../12-reified-type-parameters/) — **직접 후행.** `reified` 는 이 주제의 전개 위에 선다 —\
  타입 인자가 **호출 자리에 박히는** 것이 인라인 덕분이다. `ACC_SYNTHETIC` 도 거기가 정본이다
- [07번 주제](../07-loops-ranges-and-labels/) — **라벨과 비지역 `break`/`continue` 의 정본.**\
  거기는 **루프를 빠져나오는 것**(2.2.0), 여기는 **함수를 빠져나오는 것**(1.0)이다
- [09번 주제](../09-varargs-spread-local-and-infix-functions/) — 로컬 함수는 **객체를 안 만든다**는 대비.\
  같은 "객체를 안 만든다" 를 로컬 함수는 **선언 방식**으로, 인라인은 **전개**로 얻는다
- [08번 주제](../08-function-declaration-default-and-named-args/) — `$default` 합성 메서드. 같은 "컴파일러가 몰래 메서드를 만든다" 집안
- [03번 주제](../03-null-safe-types/) — `Intrinsics.checkNotNullParameter` 의 정본. 이 문서의 역어셈블에 계속 나온다
- [`../../../java/syntax/31-functional-interfaces/`](../../../java/syntax/31-functional-interfaces/) — **Java 쪽 대비.**\
  Java 는 박싱을 피하려고 **인터페이스를 43개 만들었고**(`IntUnaryOperator` 등), Kotlin 은 **`inline` 으로 푼다**
- [`../../../java/syntax/29-lambda-expressions/`](../../../java/syntax/29-lambda-expressions/) — Java 람다와 `invokedynamic` 의 정본
- [`../../언어-특성/README.md`](../../언어-특성/README.md) — 이 언어를 왜 고르나. **비용을 실제로 잰 곳**은 거기다(이 문서는 안 쟀다)
- 목록의 **14번 주제**(scope function) — `let`/`run`/`with`/`apply`/`also` 가 **전부 인라인 함수**다. 이 주제의 대표 사용처
- 목록의 **36번 주제**(함수 타입·`fun interface`·SAM 변환) — 람다를 객체로 받는 **다른 길**
- 목록의 **47번 주제**(`Sequence`) — 인라인이 **안 되는** 고차 함수 사슬의 대표

## 용어 풀이

- **인라인(inline)** — 함수를 부르지 않고 **몸통을 호출 자리에 복사해 넣는** 컴파일러 변환.
- **고차 함수(higher-order function)** — 함수를 인자로 받거나 함수를 돌려주는 함수.
- **람다(lambda)** — 이름 없는 함수 리터럴. `{ it + 1 }`.
- **비지역 `return`(non-local return)** — 람다 안에 적었는데 **람다를 감싼 바깥 함수**를 끝내는 `return`.
- **라벨 붙은 `return`(`return@이름`)** — 그 람다(또는 그 이름의 블록)만 끝내는 `return`.
- **`noinline`** — 인라인 함수의 파라미터 중 **이 람다는 펼치지 말라**는 표시. 값으로 다룰 수 있게 된다.
- **`crossinline`** — 펼치되 **비지역 `return` 은 금지**한다는 표시. 다른 객체 몸통 안에서 부를 때 쓴다.
- **`@PublishedApi`** — `internal` 선언을 **바이너리로는 공개**로 표시해, 공개 인라인 함수가 쓸 수 있게 하는 애너테이션.
- **`invokedynamic`** — 호출 대상을 실행 시점에 묶는 JVM 명령. 람다가 이것으로 만들어진다([10번 주제](../10-lambdas-and-higher-order-functions/)).
- **`Function1`** — 인자 1개짜리 Kotlin 함수 타입의 런타임 인터페이스. `invoke(Object): Object` 하나를 가진다.
- **박싱(boxing)** — `int` 같은 원시 값을 `Integer` 객체로 감싸는 것. `Integer.valueOf` 가 그것이다.
- **`areturn`** — 참조 값을 반환하는 JVM 명령. **어느 메서드의 `areturn` 인가**가 이 주제의 핵심이다.
- **`goto`** — 같은 메서드 안에서 다른 자리로 뛰는 JVM 명령.
- **`ACC_SYNTHETIC`** — "컴파일러가 만든 것이라 소스에는 없다" 는 클래스 파일 플래그. `javac` 가 그 멤버를 안 본다.
- **합성 메서드(synthetic method)** — 소스에 없는데 컴파일러가 만든 메서드. `caller$lambda$0` 같은 것.

---

## 더 들어가면

- **stdlib 의 인라인 함수는 생각보다 많다.** (4)의 `hasNeg` 에는 `Function1` 이 한 번도 안 나오는데,\
  `forEach` 가 인라인이라 **`iterator()` 루프째 호출자 안으로 들어왔기** 때문이다.\
  같은 이유로 `map`·`filter`·`let`·`run`·`use` 를 써도 람다 객체가 안 생긴다 —\
  ★ **그래서 "람다가 무엇이 되나" 를 실측하려면 stdlib 가 아니라 자기가 만든 비인라인 고차 함수로 재야 한다**\
  ([10번 주제](../10-lambdas-and-higher-order-functions/)가 그 함정을 다룬다).
- **`crossinline` 의 클래스 이름이 호출 경로를 말해 준다.** `CrossKt$caller$$inlined$guard$1` 에서\
  `caller` 는 **호출한 함수**, `guard` 는 **인라인된 함수**, `$$inlined$` 는 **전개해서 만든 것**이라는 표시다.\
  선언 쪽 본체용 클래스는 `CrossKt$guard$r$1` 로 **`caller` 가 없다** — 둘을 이름만으로 가를 수 있다.
- **에러가 하나라도 있으면 경고가 통째로 안 보인다.** (1)의 경고 두 줄은 `warn2.kt`(에러 없음)에서만 나왔고,\
  같은 선언에 nullable 인라인 파라미터 에러를 하나 섞은 `warn.kt` 에서는 **경고가 0줄**이었다.\
  ★ **경고를 근거로 쓰려면 에러 시나리오와 갈라서 던져야 한다.**
- **`'return' is prohibited here.` 는 세 원인이 같은 문구를 쓴다** — 비인라인·`noinline`·`crossinline`.\
  메시지만으로는 무엇이 원인인지 **알 수 없다.** 선언 쪽을 봐야 한다.
- 인라인 전개에 딸려 오는 `iconst_0 / istore_N` 쌍은 **디버거·프로파일러용 표식 변수**(`$i$f$함수이름` 류)다.\
  이 문서에서는 `javap -c` 만 찍어 **이름까지는 확인하지 않았다** — `javap -l` 로 지역 변수표를 보면 이름이 나온다\
  (**안 찍어 봤다**).
- 이 문서에서 **실행 시간은 한 번도 재지 않았다.** `javap` 로 본 것은 **객체 생성·박싱·호출 명령의 유무**,\
  따로 잰 것은 **코드 크기**뿐이다.
