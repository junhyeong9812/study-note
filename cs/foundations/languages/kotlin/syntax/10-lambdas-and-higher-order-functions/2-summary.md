# kotlin/syntax/10 — 람다와 고차 함수: `it`·마지막 인자 람다·클로저 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Lambdas and higher-order functions](https://kotlinlang.org/docs/lambdas.html) · [Function types](https://kotlinlang.org/docs/lambdas.html#function-types) · [Reflection — callable references](https://kotlinlang.org/docs/reflection.html#callable-references) · [SAM conversions](https://kotlinlang.org/docs/java-interop.html#sam-conversions) · [kotlin.Function API](https://kotlinlang.org/api/core/kotlin-stdlib/kotlin/-function/).
> **실행 검증** — 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javap` 에서 실제로 얻었다.\
> `kotlinc` 13회 · `javac` 2회 · `java` 8회 · `javap` 9회. 컴파일 실패 시나리오 5벌.\
> ★ **런타임 클래스 이름이 실행마다 바뀌는 항목이 있어 `ex.kt` 는 세 판을 돌려 대조했다**((4) 참고).
> ⚠️ **`-jvm-target` 을 밝히지 않은 바이트코드 주장은 반쪽이다.** 이 문서의 역어셈블은 **기본값 1.8**(`major version: 52`)이다 —\
> 그래서 문자열 보간이 `StringBuilder` 로 보인다([02번 주제](../02-string-templates-and-raw-strings/)).\
> **람다가 `invokedynamic` 이 되는 것도 타깃에 걸린 선택이다** — 「언어가 그렇게 약속한다」가 아니다.
> **버전** — 람다·고차 함수·`it`·마지막 인자 람다·`::` 참조·SAM 변환은 전부 1.0. `fun interface` 는 **1.4**.
> **경계** — `vararg`·로컬 함수·`infix` 는 [09번 주제](../09-varargs-spread-local-and-infix-functions/)가, 기본 인자·이름 붙인 인자는 [08번 주제](../08-function-declaration-default-and-named-args/)가 정본이다.\
> ★★ **비지역 `return` 과 `inline` 의 정본은 [11번 주제](../11-inline-functions/)** 다 — 여기서는 「비인라인 람다에서는 맨 `return` 이 거부된다」까지만 적는다.\
> `fun interface`·SAM 변환 **전체**는 [목록의 **36번 주제**](../36-function-types-fun-interface-and-sam-conversion/), 확장 함수는 [13번 주제](../13-extension-functions-and-properties/), scope function 은 [목록의 **14번 주제**](../14-scope-functions/)가 정본이다.\
> **Java 쪽 짝은 [`../../../java/syntax/29-lambda-expressions/`](../../../java/syntax/29-lambda-expressions/) · [`../../../java/syntax/30-method-references/`](../../../java/syntax/30-method-references/) · [`../../../java/syntax/31-functional-interfaces/`](../../../java/syntax/31-functional-interfaces/)** 다.
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**JVM 에는 "함수" 라는 값이 없다. 객체만 있다.**\
그래서 Kotlin 이 `{ it + 1 }` 을 값처럼 넘기려면 **그 일을 담을 봉투가 하나 필요하다** — 그게 `Function1` 이라는 인터페이스다.

그런데 그 봉투는 **`Object` 만 들어가는 규격 봉투**다.\
`Int` 를 넣으려면 **상자에 한 번 포장**해야 하고(`Integer.valueOf`), 꺼낼 때 **개봉**해야 한다(`intValue`).

> **박싱(boxing)** — `int` 같은 원시 값을 `Integer` 객체로 감싸는 것.\
> 예: `Function1.invoke` 가 `Object` 만 받으니 `1` 을 넘기려면 `Integer.valueOf(1)` 로 포장해야 한다.

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 쪽지에 적은 "할 일" | 람다 몸통 — `useLiteral$lambda$0` 이라는 `private static` 메서드 |
| 그 쪽지를 담는 규격 봉투 | `Function1` 인터페이스 |
| 봉투 입구가 `Object` 크기뿐 | `invoke(Object): Object` — 지워진 시그니처 |
| 넣을 때 포장, 꺼낼 때 개봉 | `Integer.valueOf` / `checkcast Number` + `intValue` |
| 봉투를 **그 창구에서** 만든다 | `invokedynamic` — 호출 자리마다 하나 |
| 빈 봉투는 창구가 **한 장만 만들어 계속 쓴다** | 캡처 없는 람다 = 그 자리의 싱글턴 |
| 이름을 적어야 하는 봉투는 매번 새로 | 캡처하는 람다 = 호출마다 새 객체 |
| 여럿이 같이 고쳐 쓰는 공용 상자 | `Ref$IntRef` — 캡처한 `var` 를 담는 칸 |
| 상대가 규격을 정해 준 전용 봉투 | SAM 변환 — `int` 를 **포장 없이** 받는다 |

```text
   Kotlin 소스                          바이트코드 (기본 -jvm-target 1.8)
   +---------------------------+        +-----------------------------------+
   | apply1({ it + 1 }, 10)    |  --->  | invokedynamic -> Function1 객체   |
   +---------------------------+        | invokestatic apply1(Function1, I) |
                                        +-----------------------------------+
                                                      |
                                                      v
                                        +-----------------------------------+
                                        | private static                    |
                                        |   useLiteral$lambda$0(int) : int  |
                                        |   ← 여기에는 박싱이 없다          |
                                        +-----------------------------------+
```

**클래스 파일은 안 생긴다.** 람다 몸통은 그냥 같은 파일 안의 숨은 정적 메서드가 되고,\
봉투는 **실행 중에** `LambdaMetafactory` 가 만든다.

## 이 주제가 답하려는 질문

1. `(Int) -> String` 이라는 **타입이 JVM 에서 무엇인가** — 그리고 그 타입이 **박싱을 어디에 만드나**.
2. 람다 하나가 **객체를 몇 개 만드나** — 글자 수가 정하나, 호출 자리가 정하나.
3. `::` 참조·SAM 변환·익명 함수는 람다와 **무엇이 다른가** — 특히 `return` 이 어디로 가나.

## 동작 방식

### (1) ★★ 함수 타입은 `FunctionN` 인터페이스다 — 그리고 **23번째에서 이름이 바뀐다**

**언제 쓰나** — `(Int) -> String` 이 "특별한 타입" 이라고 생각할 때.

```kotlin
fun f0(f: () -> String): String = f()
fun f1(f: (Int) -> String): String = f(1)
fun f2(f: (Int, Int) -> String): String = f(1, 2)
fun fRecv(f: Int.() -> String): String = 1.f()
fun fNullable(f: ((Int) -> String)?): String = f?.invoke(1) ?: "none"
fun f22(f: (Int, Int, Int, Int, Int, Int, Int, Int, Int, Int, Int, Int, Int, Int, Int, Int, Int, Int, Int, Int, Int, Int) -> String): String = f(1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1)
fun f23(f: (Int, Int, Int, Int, Int, Int, Int, Int, Int, Int, Int, Int, Int, Int, Int, Int, Int, Int, Int, Int, Int, Int, Int) -> String): String = f(1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1)
```

**출력** (`javap -s -p outft/FtypesKt.class`)

```text
Compiled from "ftypes.kt"
public final class FtypesKt {
  public static final java.lang.String f0(kotlin.jvm.functions.Function0<java.lang.String>);
    descriptor: (Lkotlin/jvm/functions/Function0;)Ljava/lang/String;

  public static final java.lang.String f1(kotlin.jvm.functions.Function1<? super java.lang.Integer, java.lang.String>);
    descriptor: (Lkotlin/jvm/functions/Function1;)Ljava/lang/String;

  public static final java.lang.String f2(kotlin.jvm.functions.Function2<? super java.lang.Integer, ? super java.lang.Integer, java.lang.String>);
    descriptor: (Lkotlin/jvm/functions/Function2;)Ljava/lang/String;

  public static final java.lang.String fRecv(kotlin.jvm.functions.Function1<? super java.lang.Integer, java.lang.String>);
    descriptor: (Lkotlin/jvm/functions/Function1;)Ljava/lang/String;

  public static final java.lang.String fNullable(kotlin.jvm.functions.Function1<? super java.lang.Integer, java.lang.String>);
    descriptor: (Lkotlin/jvm/functions/Function1;)Ljava/lang/String;

  public static final java.lang.String f22(kotlin.jvm.functions.Function22<? super java.lang.Integer, ? super java.lang.Integer, ? super java.lang.Integer, ? super java.lang.Integer, ? super java.lang.Integer, ? super java.lang.Integer, ? super java.lang.Integer, ? super java.lang.Integer, ? super java.lang.Integer, ? super java.lang.Integer, ? super java.lang.Integer, ? super java.lang.Integer, ? super java.lang.Integer, ? super java.lang.Integer, ? super java.lang.Integer, ? super java.lang.Integer, ? super java.lang.Integer, ? super java.lang.Integer, ? super java.lang.Integer, ? super java.lang.Integer, ? super java.lang.Integer, ? super java.lang.Integer, java.lang.String>);
    descriptor: (Lkotlin/jvm/functions/Function22;)Ljava/lang/String;

  public static final java.lang.String f23(kotlin.jvm.functions.FunctionN<java.lang.String>);
    descriptor: (Lkotlin/jvm/functions/FunctionN;)Ljava/lang/String;
}
```

```text
   파라미터 개수        타입
   0  ───────────────>  Function0<R>
   1  ───────────────>  Function1<P1, R>
   ...
   22 ───────────────>  Function22<P1..P22, R>
   23 ───────────────>  FunctionN<R>     ← 이름이 바뀐다 ★
```

그림 해설:

- **`(Int) -> String` 은 `kotlin.jvm.functions.Function1` 이다.** 문법 설탕이 아니라 **인터페이스 이름의 별칭**이다.
- ★ **인터페이스는 `Function0`\~`Function22` 까지 스물셋이고, 23개부터는 `FunctionN` 하나로 몰린다.**\
  「22 가 Kotlin 의 한계」가 아니라 **22 까지만 전용 타입이 있다**는 뜻이다.
- ★★ **`Int.() -> String` 과 `(Int) -> String` 은 디스크립터가 같다.** 수신자는 **첫 파라미터**로 내려간다\
  (확장 함수와 같은 자리 — [13번 주제](../13-extension-functions-and-properties/)).
- ★ **`((Int) -> String)?` 도 같은 `Function1`** 이다. nullable 여부는 디스크립터에 안 남는다.
- 제네릭 인자가 `? super Integer` 로 보이는 것은 **함수 타입의 파라미터가 반변**이기 때문이다([목록의 **28번 주제**](../28-generics-variance-in-out-star-where/)).

비용 — 타입 하나당 인터페이스 하나. 추가 객체는 (2) 에서 생긴다.

### (2) ★★ 람다는 `invokedynamic` 이 된다 — **클래스 파일이 안 생긴다**

**언제 쓰나** — "람다는 익명 클래스니까 `.class` 파일이 늘어나겠지" 라고 생각할 때.

```kotlin
fun apply1(f: (Int) -> Int, x: Int): Int = f(x)

fun useLiteral(): Int = apply1({ n -> n + 1 }, 10)

fun useCapture(base: Int): Int = apply1({ it + base }, 10)

fun makeTwice(): Int = apply1({ it + 1 }, 1) + apply1({ it + 1 }, 2)
```

**출력** (`kotlinc icode.kt -d out` 뒤 `find out -name '*.class' | sort`)

```text
out/IcodeKt.class
```

**출력** (`javap -c -p out/IcodeKt.class`)

```text
Compiled from "icode.kt"
public final class IcodeKt {
  public static final int apply1(kotlin.jvm.functions.Function1<? super java.lang.Integer, java.lang.Integer>, int);
    Code:
       0: aload_0
       1: ldc           #10                 // String f
       3: invokestatic  #16                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_0
       7: iload_1
       8: invokestatic  #22                 // Method java/lang/Integer.valueOf:(I)Ljava/lang/Integer;
      11: invokeinterface #28,  2           // InterfaceMethod kotlin/jvm/functions/Function1.invoke:(Ljava/lang/Object;)Ljava/lang/Object;
      16: checkcast     #30                 // class java/lang/Number
      19: invokevirtual #34                 // Method java/lang/Number.intValue:()I
      22: ireturn

  public static final int useLiteral();
    Code:
       0: invokedynamic #56,  0             // InvokeDynamic #0:invoke:()Lkotlin/jvm/functions/Function1;
       5: bipush        10
       7: invokestatic  #58                 // Method apply1:(Lkotlin/jvm/functions/Function1;I)I
      10: ireturn

  public static final int useCapture(int);
    Code:
       0: iload_0
       1: invokedynamic #67,  0             // InvokeDynamic #1:invoke:(I)Lkotlin/jvm/functions/Function1;
       6: bipush        10
       8: invokestatic  #58                 // Method apply1:(Lkotlin/jvm/functions/Function1;I)I
      11: ireturn

  public static final int makeTwice();
    Code:
       0: invokedynamic #74,  0             // InvokeDynamic #2:invoke:()Lkotlin/jvm/functions/Function1;
       5: iconst_1
       6: invokestatic  #58                 // Method apply1:(Lkotlin/jvm/functions/Function1;I)I
       9: invokedynamic #79,  0             // InvokeDynamic #3:invoke:()Lkotlin/jvm/functions/Function1;
      14: iconst_2
      15: invokestatic  #58                 // Method apply1:(Lkotlin/jvm/functions/Function1;I)I
      18: iadd
      19: ireturn

  private static final int useLiteral$lambda$0(int);
    Code:
       0: iload_0
       1: iconst_1
       2: iadd
       3: ireturn

  private static final int useCapture$lambda$0(int, int);
    Code:
       0: iload_1
       1: iload_0
       2: iadd
       3: ireturn

  private static final int makeTwice$lambda$0(int);
    Code:
       0: iload_0
       1: iconst_1
       2: iadd
       3: ireturn

  private static final int makeTwice$lambda$1(int);
    Code:
       0: iload_0
       1: iconst_1
       2: iadd
       3: ireturn
}
```

**출력** (`javap -v -p out/IcodeKt.class` 의 `BootstrapMethods` 절)

```text
BootstrapMethods:
  0: #53 REF_invokeStatic java/lang/invoke/LambdaMetafactory.metafactory:(Ljava/lang/invoke/MethodHandles$Lookup;Ljava/lang/String;Ljava/lang/invoke/MethodType;Ljava/lang/invoke/MethodType;Ljava/lang/invoke/MethodHandle;Ljava/lang/invoke/MethodType;)Ljava/lang/invoke/CallSite;
    Method arguments:
      #39 (Ljava/lang/Object;)Ljava/lang/Object;
      #44 REF_invokeStatic IcodeKt.useLiteral$lambda$0:(I)I
      #46 (Ljava/lang/Integer;)Ljava/lang/Integer;
  1: #53 REF_invokeStatic java/lang/invoke/LambdaMetafactory.metafactory:(Ljava/lang/invoke/MethodHandles$Lookup;Ljava/lang/String;Ljava/lang/invoke/MethodType;Ljava/lang/invoke/MethodType;Ljava/lang/invoke/MethodHandle;Ljava/lang/invoke/MethodType;)Ljava/lang/invoke/CallSite;
    Method arguments:
      #39 (Ljava/lang/Object;)Ljava/lang/Object;
      #64 REF_invokeStatic IcodeKt.useCapture$lambda$0:(II)I
      #46 (Ljava/lang/Integer;)Ljava/lang/Integer;
  2: #53 REF_invokeStatic java/lang/invoke/LambdaMetafactory.metafactory:(Ljava/lang/invoke/MethodHandles$Lookup;Ljava/lang/String;Ljava/lang/invoke/MethodType;Ljava/lang/invoke/MethodType;Ljava/lang/invoke/MethodHandle;Ljava/lang/invoke/MethodType;)Ljava/lang/invoke/CallSite;
    Method arguments:
      #39 (Ljava/lang/Object;)Ljava/lang/Object;
      #73 REF_invokeStatic IcodeKt.makeTwice$lambda$0:(I)I
      #46 (Ljava/lang/Integer;)Ljava/lang/Integer;
  3: #53 REF_invokeStatic java/lang/invoke/LambdaMetafactory.metafactory:(Ljava/lang/invoke/MethodHandles$Lookup;Ljava/lang/String;Ljava/lang/invoke/MethodType;Ljava/lang/invoke/MethodType;Ljava/lang/invoke/MethodHandle;Ljava/lang/invoke/MethodType;)Ljava/lang/invoke/CallSite;
    Method arguments:
      #39 (Ljava/lang/Object;)Ljava/lang/Object;
      #78 REF_invokeStatic IcodeKt.makeTwice$lambda$1:(I)I
      #46 (Ljava/lang/Integer;)Ljava/lang/Integer;
```

```text
   람다 하나가 갈라지는 두 조각

   { n -> n + 1 }
        |
        +--- 몸통 ---> private static useLiteral$lambda$0(int) : int
        |               같은 클래스 파일 안. 박싱 없음.
        |
        +--- 봉투 ---> invokedynamic #0
                        BootstrapMethods[0] = LambdaMetafactory
                        실행 중에 숨은 클래스를 만들어 Function1 을 돌려준다
```

그림 해설:

- ★★ **람다 넷이 있는데 클래스 파일은 하나뿐이다.** `.class` 파일이 람다 수만큼 늘어나지 않는다.
- 몸통은 **`이름$lambda$N` 이라는 `private static` 메서드**가 되고, **`int` 를 `int` 로 주고받는다** — 여기엔 박싱이 없다.
- `useCapture$lambda$0(int, int)` 는 파라미터가 **둘**이다. **캡처한 값이 앞에 붙는다**\
  (로컬 함수와 같은 방식 — [09번 주제](../09-varargs-spread-local-and-infix-functions/)).
- ★ 캡처가 없으면 `invokedynamic … ()Lkotlin/jvm/functions/Function1;` — **인자가 없다**.\
  캡처가 있으면 `… (I)Lkotlin/jvm/functions/Function1;` — **캡처한 값이 인자로 들어간다**. 이 차이가 (4) 의 원인이다.
- `BootstrapMethods` 의 세 번째 인자 `(Ljava/lang/Integer;)Ljava/lang/Integer;` 가 **어댑터의 시그니처**다.\
  `(I)I` 인 몸통과 `(Object)Object` 인 인터페이스 사이를 **`LambdaMetafactory` 가 메워 준다** — 그 자리가 박싱이 사는 곳이다.
- ★ **이것은 기본 타깃 1.8 에서의 선택이다.** 다른 `-jvm-target`·다른 컴파일러 플래그에서 같다는 보장이 아니다.

비용 — 클래스 파일 0개 증가, 숨은 정적 메서드 1개, 런타임 호출 자리 1개.

### (3) ★★ 박싱은 람다 몸통이 아니라 **경계**에서 난다

**언제 쓰나** — `(Int) -> Int` 가 어디서 `Integer` 를 거치는지 짚을 때.

(2) 의 `apply1` 다섯 줄만 다시 읽는다.

```text
       6: aload_0
       7: iload_1
       8: invokestatic  #22                 // Method java/lang/Integer.valueOf:(I)Ljava/lang/Integer;
      11: invokeinterface #28,  2           // InterfaceMethod kotlin/jvm/functions/Function1.invoke:(Ljava/lang/Object;)Ljava/lang/Object;
      16: checkcast     #30                 // class java/lang/Number
      19: invokevirtual #34                 // Method java/lang/Number.intValue:()I
```

```text
   int 10
     |  Integer.valueOf(10)            ← 포장
     v
   Function1.invoke(Object) : Object   ← 규격 봉투. 지워진 시그니처.
     |  checkcast Number + intValue()  ← 개봉
     v
   int 11
```

그림 해설:

- ★★ **박싱은 람다를 써서 생기는 것이 아니라 `Function1` 을 통과해서 생긴다.**\
  몸통(`useLiteral$lambda$0(int) : int`)은 원시 값 그대로다.
- **`invoke` 의 시그니처가 `(Object)Object` 인 것**이 원인이다 — 제네릭이 소거된 결과다\
  ([`../../../java/syntax/19-type-erasure/`](../../../java/syntax/19-type-erasure/) 가 정본).
- ★ Java 는 이 문제를 **인터페이스를 43개 만들어서** 풀었다(`IntUnaryOperator` 는 `int applyAsInt(int)` 다 — [`../../../java/syntax/31-functional-interfaces/`](../../../java/syntax/31-functional-interfaces/)).\
  **Kotlin 은 `FunctionN` 하나로 두고 다른 길을 냈다** — (7) 의 SAM 변환과 [11번 주제](../11-inline-functions/)의 `inline` 이다.
- **성능은 재지 않았다.** `javap` 로 본 것은 **포장·개봉 명령의 유무**까지다.

비용 — 호출 한 번마다 `Integer` 객체 하나(`valueOf` 캐시 범위 밖이면). **이 문서는 그 비용을 재지 않았다.**

### (4) ★★ 객체는 몇 개 생기나 — **글자가 아니라 「호출 자리」가 정한다**

**언제 쓰나** — "같은 람다를 두 번 쓰면 객체도 둘이겠지" 라고 짐작할 때.

```kotlin
fun makeNoCapture(): (Int) -> Int = { it + 1 }
fun makeCapture(base: Int): (Int) -> Int = { it + base }

val topLevel: (Int) -> Int = { it + 1 }

fun main() {
    val a = makeNoCapture()
    val b = makeNoCapture()
    println("A same call site, no capture : ${a === b}")

    val c = makeCapture(1)
    val d = makeCapture(1)
    println("B same call site, capture    : ${c === d}")

    println("C class of no-capture : ${a.javaClass.name}")
    println("D class of capture    : ${c.javaClass.name}")
    println("E a is Function1      : ${a is kotlin.jvm.functions.Function1<*, *>}")
    println("F topLevel === topLevel: ${topLevel === topLevel}")
    println("G invoke(10)          : ${a.invoke(10)} ${a(10)}")
}
```

**출력** (`kotlinc ex.kt -d outex` — 경고 1건이 같이 나온다)

```text
ex.kt:17:45: warning: this class is not recommended for use in Kotlin. Use 'kotlin.Function1' instead.
    println("E a is Function1      : ${a is kotlin.jvm.functions.Function1<*, *>}")
                                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
```

**출력** (`java -cp "outex:$KSTD" ExKt` — **세 판**)

```text
--- run1 ---
A same call site, no capture : true
B same call site, capture    : false
C class of no-capture : ExKt$$Lambda/0x00007d78e8001800
D class of capture    : ExKt$$Lambda/0x00007d78e8001a10
E a is Function1      : true
F topLevel === topLevel: true
G invoke(10)          : 11 11
--- run2 ---
A same call site, no capture : true
B same call site, capture    : false
C class of no-capture : ExKt$$Lambda/0x0000737868001800
D class of capture    : ExKt$$Lambda/0x0000737868001a10
E a is Function1      : true
F topLevel === topLevel: true
G invoke(10)          : 11 11
--- run3 ---
A same call site, no capture : true
B same call site, capture    : false
C class of no-capture : ExKt$$Lambda/0x000079b82c001800
D class of capture    : ExKt$$Lambda/0x000079b82c001a10
E a is Function1      : true
F topLevel === topLevel: true
G invoke(10)          : 11 11
```

★ **`A`\~`G` 의 값은 세 판이 같고, `C`·`D` 의 16진수만 판마다 다르다.**\
**이름의 숫자는 관찰이지 보장이 아니다** — 런타임이 만드는 숨은 클래스라 주소가 그때그때 붙는다.

```kotlin
fun twoSites(): Boolean {
    val p: (Int) -> Int = { n -> n + 1 }
    val q: (Int) -> Int = { n -> n + 1 }
    return p === q
}

fun inLoop(): Boolean {
    val seen = ArrayList<(Int) -> Int>()
    for (i in 1..3) seen.add({ n -> n + 1 })
    return seen[0] === seen[1] && seen[1] === seen[2]
}

fun inLoopCapture(): Boolean {
    val seen = ArrayList<(Int) -> Int>()
    for (i in 1..3) seen.add({ n -> n + i })
    return seen[0] === seen[1]
}
```

**출력** (`java -cp "outex2:$KSTD" Ex2Kt`)

```text
H two identical lambda literals : false
I same literal, 3 loop rounds   : true
J captures loop var, 3 rounds   : false
```

```text
   글자가 같아도 자리가 다르면 다른 객체        자리가 같으면 몇 바퀴를 돌아도 한 객체
   +---------------------------------+         +---------------------------------+
   | val p = { n -> n + 1 }  자리 ①  |         | for (i in 1..3)                 |
   | val q = { n -> n + 1 }  자리 ②  |         |   seen.add({ n -> n + 1 })  자리 ①|
   | p === q  ->  false              |         | seen[0] === seen[1] -> true     |
   +---------------------------------+         +---------------------------------+
     indy 자리가 둘이라 봉투도 둘              그 자리의 CallSite 가 한 장을 계속 돌려준다
```

그림 해설:

- ★★ **개수를 정하는 것은 "같은 글자인가" 가 아니라 "같은 `invokedynamic` 자리인가" 다.**\
  (2) 의 `makeTwice` 가 `InvokeDynamic #2` 와 `#3` 으로 **둘로 갈린 것**이 그 근거다.
- **캡처가 없으면 한 자리가 한 객체만 만든다**(`A`·`I` 가 `true`). `LambdaMetafactory` 가 만든 `CallSite` 가 **같은 인스턴스를 계속 돌려준다**.
- **캡처가 있으면 매번 새 객체다**(`B`·`J` 가 `false`). 캡처한 값이 인자로 들어가니 **같은 것을 돌려줄 수가 없다**.
- ★ `J` 가 `false` 인 것은 Java 의 "루프 변수 캡처" 함정과 같은 뿌리다 — **바퀴마다 `i` 가 다르니 봉투도 달라야 한다**.
- `E` 가 `true` 인 것으로 **런타임 타입이 정말 `Function1`** 임이 확인된다. 다만 경고가 말하듯 **그 이름을 소스에 쓰는 것은 권장되지 않는다**(Kotlin 쪽 이름은 `kotlin.Function1`).
- ★ **위의 어느 것도 "언어가 약속한 것" 이 아니다.** 이 컴파일러와 이 JVM 의 동작이다.

비용 — 캡처 없는 람다는 **자리당 객체 1개**, 캡처 있는 람다는 **호출당 1개**.

### (5) ★ `::` 참조는 람다와 **다른 것으로** 컴파일된다

**언제 쓰나** — `{ square(it) }` 와 `::square` 가 같은 것이라고 생각할 때.

```kotlin
class Box(val size: Int)

fun square(n: Int): Int = n * n

fun apply1(f: (Int) -> Int, x: Int): Int = f(x)
fun applyBox(f: (Box) -> Int, b: Box): Int = f(b)
fun makeBox(f: (Int) -> Box, n: Int): Box = f(n)

fun viaLambda(): Int = apply1({ square(it) }, 3)
fun viaFunRef(): Int = apply1(::square, 3)
fun viaPropRef(): Int = applyBox(Box::size, Box(4))
fun viaCtorRef(): Box = makeBox(::Box, 5)
```

**출력** (`kotlinc refs2.kt -d outrefs2` 뒤 `find outrefs2 -name '*.class' | sort`)

```text
outrefs2/Box.class
outrefs2/Refs2Kt$viaCtorRef$1.class
outrefs2/Refs2Kt$viaFunRef$1.class
outrefs2/Refs2Kt$viaPropRef$1.class
outrefs2/Refs2Kt.class
```

**출력** (`javap -c -p outrefs2/Refs2Kt.class` — 호출부만 발췌)

```text
  public static final int viaLambda();
    Code:
       0: invokedynamic #69,  0             // InvokeDynamic #0:invoke:()Lkotlin/jvm/functions/Function1;
       5: iconst_3
       6: invokestatic  #71                 // Method apply1:(Lkotlin/jvm/functions/Function1;I)I
       9: ireturn

  public static final int viaFunRef();
    Code:
       0: getstatic     #78                 // Field Refs2Kt$viaFunRef$1.INSTANCE:LRefs2Kt$viaFunRef$1;
       3: checkcast     #28                 // class kotlin/jvm/functions/Function1
       6: iconst_3
       7: invokestatic  #71                 // Method apply1:(Lkotlin/jvm/functions/Function1;I)I
      10: ireturn

  public static final int viaPropRef();
    Code:
       0: getstatic     #84                 // Field Refs2Kt$viaPropRef$1.INSTANCE:LRefs2Kt$viaPropRef$1;
       3: checkcast     #28                 // class kotlin/jvm/functions/Function1
       6: new           #51                 // class Box
       9: dup
      10: iconst_4
      11: invokespecial #88                 // Method Box."<init>":(I)V
      14: invokestatic  #90                 // Method applyBox:(Lkotlin/jvm/functions/Function1;LBox;)I
      17: ireturn

  public static final Box viaCtorRef();
    Code:
       0: getstatic     #97                 // Field Refs2Kt$viaCtorRef$1.INSTANCE:LRefs2Kt$viaCtorRef$1;
       3: checkcast     #28                 // class kotlin/jvm/functions/Function1
       6: iconst_5
       7: invokestatic  #99                 // Method makeBox:(Lkotlin/jvm/functions/Function1;I)LBox;
      10: areturn

  private static final int viaLambda$lambda$0(int);
    Code:
       0: iload_0
       1: invokestatic  #101                // Method square:(I)I
       4: ireturn
}
```

**출력** (`javap -c -p 'outrefs2/Refs2Kt$viaFunRef$1.class'`)

```text
Compiled from "refs2.kt"
final class Refs2Kt$viaFunRef$1 extends kotlin.jvm.internal.FunctionReferenceImpl implements kotlin.jvm.functions.Function1<java.lang.Integer, java.lang.Integer> {
  public static final Refs2Kt$viaFunRef$1 INSTANCE;

  Refs2Kt$viaFunRef$1();
    Code:
       0: aload_0
       1: iconst_1
       2: ldc           #11                 // class Refs2Kt
       4: ldc           #13                 // String square
       6: ldc           #15                 // String square(I)I
       8: iconst_1
       9: invokespecial #18                 // Method kotlin/jvm/internal/FunctionReferenceImpl."<init>":(ILjava/lang/Class;Ljava/lang/String;Ljava/lang/String;I)V
      12: return

  public final java.lang.Integer invoke(int);
    Code:
       0: iload_1
       1: invokestatic  #25                 // Method Refs2Kt.square:(I)I
       4: invokestatic  #30                 // Method java/lang/Integer.valueOf:(I)Ljava/lang/Integer;
       7: areturn

  public java.lang.Object invoke(java.lang.Object);
    Code:
       0: aload_0
       1: aload_1
       2: checkcast     #35                 // class java/lang/Number
       5: invokevirtual #39                 // Method java/lang/Number.intValue:()I
       8: invokevirtual #41                 // Method invoke:(I)Ljava/lang/Integer;
      11: areturn

  static {};
    Code:
       0: new           #2                  // class Refs2Kt$viaFunRef$1
       3: dup
       4: invokespecial #46                 // Method "<init>":()V
       7: putstatic     #49                 // Field INSTANCE:LRefs2Kt$viaFunRef$1;
      10: return
}
```

```text
   { square(it) }                       ::square
   +--------------------------+         +-------------------------------------+
   | invokedynamic            |         | Refs2Kt$viaFunRef$1.class  ← 파일!  |
   | 클래스 파일 0개          |         | getstatic INSTANCE  ← 싱글턴        |
   | 몸통 = $lambda$0(int)int |         | FunctionReferenceImpl 상속          |
   |                          |         | 이름·시그니처를 들고 있다           |
   +--------------------------+         +-------------------------------------+
```

그림 해설:

- ★ **`::` 참조 셋이 클래스 파일 셋을 만들었다.** 람다는 하나도 안 만들었는데 참조는 만든다.
- 그 클래스는 **`FunctionReferenceImpl` 을 상속**하고 생성자에서 `class Refs2Kt`·`"square"`·`"square(I)I"` 를 넘긴다.\
  **참조는 자기가 무엇을 가리키는지 기억해야 하기 때문이다** — 그래서 `.name` 같은 리플렉션이 된다.
- **`INSTANCE` 정적 필드**를 `getstatic` 으로 읽는다 — 캡처가 없는 참조는 **클래스 하나당 객체 하나**다.
- ★★ **박싱의 양끝이 이 한 클래스에서 보인다** — `invoke(int)` 는 `Integer.valueOf` 로 포장하고,\
  `invoke(Object)` 는 `checkcast Number` + `intValue()` 로 개봉한다. (3) 의 그림이 실물로 있는 자리다.
- 실행 쪽에서도 확인된다(`refs.kt`): `::square` 를 두 번 적으면 `S … false`, 클래스 이름은 `RefsKt$main$r1$1`, `.name` 은 `square` 다.

비용 — 참조 하나당 클래스 파일 하나 + 싱글턴 객체 하나.

### (6) ★★ `map(::square)` 로는 **아무것도 못 본다** — stdlib 가 `inline` 이라서

**언제 쓰나** — "람다가 객체가 된다" 를 `javap` 로 확인하려고 `map`·`filter`·`forEach` 를 쓸 때.

```kotlin
fun square(n: Int): Int = n * n

fun useFunRef(): Int = listOf(1, 2, 3).map(::square).sum()
```

**출력** (`javap -c -p outrefs/RefsKt.class` 의 `useFunRef` 안에서 세어 본 것)

```text
$ javap -c -p outrefs/RefsKt.class | awk '/public static final int useFunRef\(\);/,/^$/' | grep -cE 'invokedynamic|Function1'
0
$ javap -c -p outrefs/RefsKt.class | awk '/public static final int useFunRef\(\);/,/^$/' | grep -nE 'square|Function1|invokedynamic'
57:     103: invokestatic  #57                 // Method square:(I)I
```

```text
   기대한 것                              실제
   +---------------------------+          +---------------------------+
   | invokedynamic -> Function1|          | 루프가 통째로 펼쳐져 있고 |
   | invokeinterface invoke    |          | invokestatic square:(I)I  |
   +---------------------------+          | Function1 은 0회 등장     |
                                          +---------------------------+
```

그림 해설:

- ★★ **`map` 은 stdlib 의 `inline` 함수다.** 그래서 루프도 람다도 **호출부에 통째로 펼쳐지고**,\
  `Function1` 객체가 **하나도 안 남는다**.
- 「람다가 객체가 된다」를 보려면 **내가 쓴 비인라인 고차 함수**가 필요하다 — 이 문서가 `apply1` 을 직접 쓴 이유다.
- ★ 이 사실은 실무 결론 하나를 만든다 — **컬렉션 연산에 람다를 쓰는 것은 대개 객체를 안 만든다.**\
  객체가 생기는 쪽은 **내가 만든 고차 함수에 람다를 넘길 때**다.
- 왜 펼쳐지는지, 그 대가가 무엇인지는 [11번 주제](../11-inline-functions/)가 정본이다.

비용 — 여기서는 객체 0개. 대신 **호출부 코드가 늘어난다**([11번 주제](../11-inline-functions/)가 잰다).

### (7) ★ SAM 변환 — **박싱이 사라지는 자리**

**언제 쓰나** — Java 라이브러리의 콜백에 Kotlin 람다를 넘길 때, 그리고 박싱을 피할 길을 찾을 때.

```java
public interface JInt {
    int apply(int x);
}
```

```kotlin
fun useSam(): Int {
    val j = JInt { x -> x + 1 }
    return j.apply(10)
}

fun callJava(f: JInt): Int = f.apply(10)
fun passLambdaToJava(): Int = callJava { x -> x * 2 }

fun interface KInt { fun apply(x: Int): Int }
fun callKotlinFun(f: KInt): Int = f.apply(10)
fun passLambdaToKotlinFun(): Int = callKotlinFun { x -> x * 3 }
```

**출력** (`javap -c -p outsam/SamKt.class` — 앞 네 메서드)

```text
Compiled from "sam.kt"
public final class SamKt {
  public static final int useSam();
    Code:
       0: invokedynamic #23,  0             // InvokeDynamic #0:apply:()LJInt;
       5: astore_0
       6: aload_0
       7: bipush        10
       9: invokeinterface #27,  2           // InterfaceMethod JInt.apply:(I)I
      14: ireturn

  public static final int callJava(JInt);
    Code:
       0: aload_0
       1: ldc           #34                 // String f
       3: invokestatic  #40                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_0
       7: bipush        10
       9: invokeinterface #27,  2           // InterfaceMethod JInt.apply:(I)I
      14: ireturn

  public static final int passLambdaToJava();
    Code:
       0: invokedynamic #46,  0             // InvokeDynamic #1:apply:()LJInt;
       5: invokestatic  #48                 // Method callJava:(LJInt;)I
       8: ireturn

  public static final int callKotlinFun(KInt);
    Code:
       0: aload_0
       1: ldc           #34                 // String f
       3: invokestatic  #40                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_0
       7: bipush        10
       9: invokeinterface #53,  2           // InterfaceMethod KInt.apply:(I)I
      14: ireturn
```

**출력** (`java -cp "outsam:$KSTD" SamKt`)

```text
V Java SAM object      : 11
W lambda -> Java SAM   : 20
X lambda -> fun interface : 30
Y two SAM instances === : false
Z SAM class            : SamKt$$Lambda/0x00007c5760001ac0
```

```text
   함수 타입 (Int) -> Int              SAM / fun interface
   +-------------------------------+   +-------------------------------+
   | Integer.valueOf(10)           |   | (포장 없음)                   |
   | invoke(Object) : Object       |   | apply(I)I                     |
   | checkcast Number + intValue() |   | (개봉 없음)                   |
   +-------------------------------+   +-------------------------------+
     지워진 시그니처라 Object 만       인터페이스가 int 라고 적혀 있다
```

그림 해설:

- ★★ **`invokeinterface JInt.apply:(I)I` — 박싱이 한 번도 안 나온다.** 인터페이스 메서드가 `int` 를 받기 때문이다.
- Kotlin 의 `fun interface KInt` 도 똑같다(`KInt.apply:(I)I`). **`fun interface` 는 1.4 부터**다.
- 객체는 여전히 생긴다 — `invokedynamic … ()LJInt;`, 런타임 클래스는 `SamKt$$Lambda/0x…`.\
  **없어지는 것은 객체가 아니라 포장이다.**
- `Y` 가 `false` 인 이유는 (4) 와 같다 — **자리가 둘이라 봉투도 둘**이다.
- ★ **그래서 박싱을 피하는 길은 둘이다** — ① 시그니처가 원시 타입인 **SAM·`fun interface`**,\
  ② 객체 자체를 안 만드는 **`inline`**([11번 주제](../11-inline-functions/)).\
  **Kotlin 의 함수 타입만 쓰면 두 길 다 안 탄다.**
- SAM 변환·`fun interface` **전체**는 [목록의 **36번 주제**](../36-function-types-fun-interface-and-sam-conversion/)가 정본이다. 여기는 **박싱이 갈리는 자리**만 다뤘다.

비용 — 객체 1개(자리당), 포장 0개.

### (8) ★ 람다가 바깥 `var` 를 고친다 — Java 가 막는 자리

**언제 쓰나** — 람다 안에서 바깥 카운터를 늘릴 때.

```kotlin
fun countUp(n: Int): Int {
    var acc = 0
    val add: (Int) -> Int = { x -> acc += x; acc }
    for (i in 1..n) add(i)
    return acc
}
```

**출력** (`javap -c -p outclo/CloKt.class` — `countUp` 과 람다 몸통)

```text
  public static final int countUp(int);
    Code:
       0: new           #41                 // class kotlin/jvm/internal/Ref$IntRef
       3: dup
       4: invokespecial #45                 // Method kotlin/jvm/internal/Ref$IntRef."<init>":()V
       7: astore_1
       8: aload_1
       9: invokedynamic #63,  0             // InvokeDynamic #0:invoke:(Lkotlin/jvm/internal/Ref$IntRef;)Lkotlin/jvm/functions/Function1;
      14: astore_2
      15: iconst_1
      16: istore_3
      17: iload_3
      18: iload_0
      19: if_icmpgt     44
      22: aload_2
      23: iload_3
      24: invokestatic  #22                 // Method java/lang/Integer.valueOf:(I)Ljava/lang/Integer;
      27: invokeinterface #28,  2           // InterfaceMethod kotlin/jvm/functions/Function1.invoke:(Ljava/lang/Object;)Ljava/lang/Object;
      32: pop
      33: iload_3
      34: iload_0
      35: if_icmpeq     44
      38: iinc          3, 1
      41: goto          22
      44: aload_1
      45: getfield      #66                 // Field kotlin/jvm/internal/Ref$IntRef.element:I
      48: ireturn
```

```text
  private static final int countUp$lambda$0(kotlin.jvm.internal.Ref$IntRef, int);
    Code:
       0: aload_0
       1: aload_0
       2: getfield      #66                 // Field kotlin/jvm/internal/Ref$IntRef.element:I
       5: iload_1
       6: iadd
       7: putfield      #66                 // Field kotlin/jvm/internal/Ref$IntRef.element:I
      10: aload_0
      11: getfield      #66                 // Field kotlin/jvm/internal/Ref$IntRef.element:I
      14: ireturn
```

**출력** (`java -cp "outclo:$KSTD" CloKt`)

```text
AA countUp(4) = 10
AB seen after two calls = 7
```

같은 코드를 Java 로 옮기면 **컴파일이 안 된다.**

```text
===== 소스: Clo.java =====
import java.util.function.IntUnaryOperator;

public class Clo {
    public static int countUp(int n) {
        int acc = 0;
        IntUnaryOperator add = x -> { acc += x; return acc; };
        for (int i = 1; i <= n; i++) add.applyAsInt(i);
        return acc;
    }
}
===== javac Clo.java =====
Clo.java:6: error: local variables referenced from a lambda expression must be final or effectively final
        IntUnaryOperator add = x -> { acc += x; return acc; };
                                      ^
Clo.java:6: error: local variables referenced from a lambda expression must be final or effectively final
        IntUnaryOperator add = x -> { acc += x; return acc; };
                                                       ^
2 errors
```

```text
   Java                                  Kotlin
   +---------------------------+         +-------------------------------------+
   | acc 는 지역 변수 한 칸    |         | new Ref$IntRef   ← 상자 1개         |
   | 람다는 그 칸을 공유 못 함 |         | indy 의 캡처 인자로 상자를 넘긴다   |
   | -> 컴파일 거부            |         | 람다는 상자.element 를 읽고 쓴다    |
   +---------------------------+         | 바깥도 상자.element 에서 읽는다     |
                                         +-------------------------------------+
```

그림 해설:

- ★ **Kotlin 은 `Ref$IntRef` 라는 한 칸짜리 상자를 만들어** 바깥과 람다가 **같은 칸**을 보게 한다.
- 상자는 `invokedynamic` 의 **캡처 인자**로 넘어간다(`(Lkotlin/jvm/internal/Ref$IntRef;)Lkotlin/jvm/functions/Function1;`).
- 바깥 함수도 결과를 **`상자.element` 에서 읽는다**(`getfield … Ref$IntRef.element`).
- ★★ **"`var` 를 고칠 수 있다" 는 언어 규칙이고, "상자가 `Ref$IntRef` 다" 는 구현이다.** 둘을 같이 적지 마라.
- **로컬 함수 쪽의 정본은 [09번 주제](../09-varargs-spread-local-and-infix-functions/)** 다(거기는 `invokestatic` + 상자, 여기는 `invokedynamic` + 상자).\
  **람다 쪽은 이 문서가 정본이다.**

비용 — 캡처한 `var` 하나당 상자 하나. 캡처가 있으므로 **봉투도 호출마다 새로** 생긴다((4)).

### (9) 람다 대 익명 함수 — `return` 이 어디로 가나

**언제 쓰나** — 람다 안에서 그냥 `return` 을 적고 싶을 때.

```text
===== 소스: bad1.kt =====
fun runIt(f: (Int) -> Int): Int = f(1)

fun outer(): Int {
    runIt { return 5 }
    return 0
}
===== kotlinc bad1.kt =====
bad1.kt:4:13: error: 'return' is prohibited here.
    runIt { return 5 }
            ^^^^^^
```

```kotlin
fun runIt(f: (Int) -> Int): Int = f(1)

fun withAnon(): Int {
    val r = runIt(fun(x: Int): Int { return x + 100 })
    return r
}

fun withLabel(): Int {
    val r = runIt { x -> return@runIt x + 100 }
    return r
}

fun withImplicitLabel(): Int {
    val r = runIt lam@{ x -> return@lam x + 100 }
    return r
}

fun anonInForEach(xs: List<Int>): String {
    val hit = StringBuilder()
    xs.forEach(fun(x: Int) {
        if (x < 0) return          // returns from the anonymous function only
        hit.append(x)
    })
    return hit.toString()
}
```

**출력** (`java -cp "outanon:$KSTD" AnonKt`)

```text
K anonymous fun    : 101
L return@runIt     : 101
M return@lam       : 101
N anon fun in forEach over [1,-2,3] : 13
```

```text
   람다 { ... }                         익명 함수 fun(x: Int) { ... }
   +-----------------------------+      +-----------------------------+
   | 맨 return  -> 컴파일 거부   |      | 맨 return  -> 자기만 빠져나감|
   | return@라벨 -> 람다만 끝낸다|      | 라벨 없이 그냥 쓴다          |
   | 마지막 식이 값이 된다       |      | 반환을 직접 적어야 한다      |
   +-----------------------------+      +-----------------------------+
```

그림 해설:

- **비인라인 람다 안에서 맨 `return` 은 거부된다** — `'return' is prohibited here.`\
  람다 몸통은 **다른 메서드**((2) 의 `$lambda$0`)라서 바깥 메서드를 끝낼 방법이 없기 때문이다.
- **익명 함수의 `return` 은 자기 자신만 끝낸다.** `N` 이 `13` 인 것이 근거다 —\
  `-2` 에서 `return` 했는데 `forEach` 는 계속 돌아 `3` 까지 붙었다.
- `return@runIt`·`return@lam` 은 **람다에 이름을 붙여 거기까지만 나가는 것**이다.\
  라벨을 안 붙이면 **자기를 받는 함수 이름**이 기본 라벨이 된다.
- ★★ **`inline` 함수에 넘긴 람다만 바깥 함수까지 나갈 수 있다**(비지역 `return`).\
  그 정본은 [11번 주제](../11-inline-functions/)다 — [07번 주제](../07-loops-ranges-and-labels/)가 여기로 넘겼고, 여기서 다시 11로 넘긴다.

비용 — 없음. 형태의 차이다.

### (10) 형태 — `it`·마지막 인자 람다·`_`

**언제 쓰나** — 괄호를 어디까지 생략할 수 있는지 헷갈릴 때.

```kotlin
fun apply1(f: (Int) -> Int, x: Int): Int = f(x)
fun withTrailing(x: Int, f: (Int) -> Int): Int = f(x)
fun twoLambdas(x: Int, f: (Int) -> Int, g: (Int) -> Int): Int = g(f(x))

fun nested(): String {
    val outer: (Int) -> String = { a ->
        val inner: (String) -> String = { it + a }
        inner("n=")
    }
    return outer(7)
}
```

**출력** (`java -cp "oform:$KSTD" FormKt`)

```text
AC 괄호 안              : 11
AD 괄호 밖(마지막 인자) : 11
AE 인자가 람다뿐        : 42
AF 두 람다 중 하나만 밖 : 22
AG 중첩 람다의 it        : n=7
AH 인자를 안 쓸 때 _    : 99
```

```text
   withTrailing(10, { it + 1 })      ← 괄호 안
   withTrailing(10) { it + 1 }       ← 마지막 인자만 밖으로
   run { 40 + 2 }                    ← 인자가 람다 하나뿐이면 괄호가 통째로 사라진다
   twoLambdas(10, { it + 1 }) { ... }← 밖으로 나갈 수 있는 건 마지막 하나뿐
```

그림 해설:

- **`it` 은 파라미터가 정확히 하나일 때만 생긴다.** 이름을 적으면 `it` 은 없어진다.
- ★ **중첩하면 안쪽 `it` 이 바깥 `it` 을 가린다** — `AG` 에서 안쪽 `it` 은 `"n="` 이고 바깥 파라미터는 이름 `a` 로 받았다.\
  **이름을 붙이는 것이 중첩의 정답이다.**
- **괄호 밖으로 나갈 수 있는 것은 마지막 인자 하나뿐이다.** `AF` 에서 앞의 람다는 괄호 안에 남았다.
- `_` 는 **안 쓰는 파라미터**의 이름이다.

비용 — 없음. 읽기의 문제다.

## 문법 — 형태와 규칙

```kotlin
// 1) 함수 타입
val f: (Int) -> String = { "n=$it" }
val g: () -> Unit = { }
val h: Int.() -> String = { "recv=$this" }     // 수신자 지정 — 14·37번 주제
val n: ((Int) -> String)? = null               // nullable 함수 타입

// 2) 람다
{ x: Int -> x + 1 }        // 파라미터 명시
{ it + 1 }                 // 파라미터 1개면 it
{ _ -> 99 }                // 안 쓰면 _
{ a, b -> a + b }          // 2개 이상이면 it 없음

// 3) 호출 형태
apply1({ it + 1 }, 10)     // 괄호 안
withTrailing(10) { it + 1 }// 마지막 인자만 밖
run { 40 + 2 }             // 인자가 람다뿐이면 괄호 생략

// 4) 익명 함수 — 반환 타입을 적을 수 있고 return 이 자기만 끝낸다
runIt(fun(x: Int): Int { return x + 100 })

// 5) 라벨 반환
runIt { x -> return@runIt x + 100 }
runIt lam@{ x -> return@lam x + 100 }

// 6) 호출 가능 참조
::square          // 최상위 함수
Box::size         // 프로퍼티 (Box) -> Int
::Box             // 생성자 (Int) -> Box
b::size           // 바운드 참조 () -> Int

// 7) SAM 변환 — Java 인터페이스 / fun interface
JInt { x -> x + 1 }
fun interface KInt { fun apply(x: Int): Int }
```

규칙 불릿.

- **`(A) -> B` 는 `FunctionN` 인터페이스다.** 0\~22 는 전용 타입, **23개부터 `FunctionN`**.
- **`it` 은 파라미터가 하나일 때만.** 둘 이상이면 `unresolved reference 'it'` 이다.
- **괄호 밖으로 나가는 것은 마지막 인자 하나.** 마지막이 아닌 자리에 쓰면 타입 불일치로 거부된다.
- **비인라인 람다에서 맨 `return` 은 금지.** 라벨 반환이나 익명 함수를 쓴다.
- **`::` 참조는 클래스 파일을 만든다.** 람다는 안 만든다.
- **함수 타입은 `Object` 로 주고받는다** — 원시 타입이면 박싱이 붙는다.

## 어디서 틀리나

| 틀리는 형태 | 무슨 일이 일어나나 | 고치는 법 |
|---|---|---|
| "람다마다 `.class` 파일이 생긴다" | **안 생긴다.** `invokedynamic` + 숨은 정적 메서드다 | `find out -name '*.class'` 로 세어 본다 |
| "같은 글자 람다면 객체도 하나" | **자리가 다르면 다르다**(`H false`) | 개수를 정하는 것은 `invokedynamic` 자리다 |
| "람다는 부를 때마다 새 객체" | **캡처가 없으면 그 자리의 싱글턴**(`A`·`I` 가 true) | 캡처 유무로 갈라 기억한다 |
| `(Int) -> Int` 가 박싱을 안 한다고 봄 | `Integer.valueOf` → `invoke(Object)` → `intValue` | 원시 타입이면 `fun interface` 또는 `inline` |
| 박싱이 람다 몸통에 있다고 봄 | 몸통은 `(int)int` 다. 박싱은 **경계**에 있다 | `javap` 로 몸통과 `apply1` 을 나눠 본다 |
| `map`·`forEach` 로 객체 생성을 확인하려 함 | stdlib 가 `inline` 이라 **객체가 0개**다 | 비인라인 고차 함수를 직접 만든다 |
| `::square` 를 람다와 같다고 봄 | **클래스 파일 + `INSTANCE` 싱글턴**이 생긴다 | 둘을 갈라 기억한다 |
| 람다 안에서 그냥 `return` | `'return' is prohibited here.` | `return@라벨` 또는 익명 함수 또는 `inline` |
| 익명 함수의 `return` 이 바깥을 끝낼 줄 앎 | **자기만** 끝낸다(`N` 이 `13`) | 바깥을 끝내려면 [11번 주제](../11-inline-functions/) |
| 2인자 람다에서 `it` | `unresolved reference 'it'` + 타입 불일치 | 이름을 붙인다 |
| 마지막이 아닌 자리에 괄호 밖 람다 | 마지막 파라미터에 매칭돼 타입 불일치 3건 | 순서를 바꾸거나 괄호 안에 넣는다 |
| 람다 인자 개수를 틀림 | `cannot infer type for value parameter 'b'` | 시그니처를 다시 본다 |
| `(Int)->String` 과 `Int.()->String` 오버로드 | `conflicting overloads` — **디스크립터가 같다** | 이름을 다르게 짓는다 |
| 중첩 람다에서 `it` 을 둘 다 씀 | 안쪽이 바깥을 가린다 | 바깥에 이름을 붙인다 |
| 캡처한 `var` 비용을 0으로 봄 | `Ref$IntRef` 상자 1개 + 호출마다 새 봉투 | 반환값으로 바꿀 수 있으면 바꾼다 |

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 | 근거 |
|---|---|---|
| `(A) -> B` 가 `FunctionN` 인 것 | **언어**(stdlib 타입) | `javap -s` + 문서 |
| 22 까지 전용 타입, 23부터 `FunctionN` | **언어**(stdlib 에 그만큼만 있다) | `javap -s` |
| `Int.() -> B` 의 수신자가 첫 파라미터인 것 | **언어** | `javap -s` + 문서 |
| `it` 이 파라미터 1개일 때만 생기는 것 | **언어** | 컴파일 에러 |
| 마지막 인자 람다를 괄호 밖에 쓰는 것 | **언어** | 문법 |
| 비인라인 람다에서 맨 `return` 이 금지인 것 | **언어** | 컴파일 에러 |
| 익명 함수의 `return` 이 자기만 끝내는 것 | **언어** | 실행(`N` = `13`) |
| 람다가 바깥 `var` 를 고칠 수 있는 것 | **언어** | 실행 |
| SAM 변환이 되는 것 | **언어** | 실행 |
| **람다가 `invokedynamic` + `LambdaMetafactory` 인 것** | **구현(+타깃 의존)** ★★ | `javap -c`·`javap -v` |
| **클래스 파일이 안 생기는 것** | **구현** ★ | `find … -name '*.class'` |
| **몸통이 `이름$lambda$N` 정적 메서드인 것** | **구현** | `javap -c` |
| **캡처 없는 람다가 자리당 싱글턴인 것** | **구현** ★★ | 실행(`A`·`I` 가 `true`) |
| **런타임 클래스 이름이 `ExKt$$Lambda/0x…` 인 것** | **구현 — 판마다 다르다** ★ | 세 판 실행 |
| **`::` 참조가 `FunctionReferenceImpl` 하위 클래스인 것** | **구현** ★ | `javap -c` |
| **`::` 참조가 `INSTANCE` 싱글턴인 것** | **구현** | `javap -c` |
| **`Ref$IntRef` 라는 상자 이름** | **구현** | `javap -c` |
| **`Integer.valueOf`/`intValue` 자리** | **구현** | `javap -c` |
| **`map` 이 `inline` 이라 객체가 0개인 것** | **구현(stdlib 선택)** ★ | `javap -c` + `grep -c` |

★ **가장 중요한 구분 한 줄** — **"함수 타입은 `Function1` 이다" 는 stdlib 가 약속한 것이고,\
"그 `Function1` 을 `invokedynamic` 으로 만든다" 는 이 컴파일러가 이 타깃에서 고른 것이다.**\
앞엣것은 API 문서에 있고, 뒤엣것은 `javap` 에만 있다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 한 번 쓰고 버리는 짧은 동작 | 람다 | 가장 짧고 클래스 파일도 안 는다 |
| 이미 있는 함수를 그대로 넘길 때 | `::` 참조 | 몸통을 다시 안 적는다. 다만 클래스가 하나 는다 |
| 이름이 필요한 재사용 로직 | 로컬 함수 | 객체가 아예 안 생긴다([09번 주제](../09-varargs-spread-local-and-infix-functions/)) |
| 람다 안에서 바깥 함수를 끝내야 할 때 | `inline` + 비지역 `return` | 그것만이 되는 길이다([11번 주제](../11-inline-functions/)) |
| 자기 자신만 끝내고 싶을 때 | 익명 함수 또는 `return@라벨` | 의도가 드러난다 |
| 원시 타입 콜백이 뜨거운 경로에 있을 때 | `fun interface` 또는 `inline` | 박싱이 사라진다(**이 문서는 비용을 재지 않았다**) |
| Java 인터페이스 콜백 | 람다 그대로 | SAM 변환이 알아서 된다 |
| 파라미터가 23개 넘는 함수 타입 | **설계를 다시 본다** | `FunctionN` 으로 떨어지고 읽을 수도 없다 |
| 중첩 람다 | `it` 대신 이름 | 안쪽이 바깥을 가린다 |
| 바깥 `var` 를 고쳐야 할 때 | 람다도 되고 로컬 함수도 된다 | Java 의 `effectively final` 제약이 없다 |

판단 규칙 두 줄.

- **람다를 쓸지 참조를 쓸지는 「몸통을 새로 적나」로 정한다.** 새로 적으면 람다, 있는 것을 가리키면 `::`.
- ★ **객체가 생길지 말지를 알고 싶으면 「내가 만든 고차 함수인가, stdlib 인가」부터 본다.** stdlib 의 컬렉션 연산은 대개 `inline` 이다.

## 핵심 문장

- 함수 타입 `(Int) -> String` 은 **`kotlin.jvm.functions.Function1` 인터페이스**다. 0\~22 는 전용 타입, **23개부터 `FunctionN`** 하나로 몰린다.
- `Int.() -> String` 과 `((Int) -> String)?` 는 **`(Int) -> String` 과 디스크립터가 같다** — 수신자는 첫 파라미터, nullable 은 안 남는다.
- ★★ **람다는 `invokedynamic` + `LambdaMetafactory` 가 된다 — 클래스 파일이 안 생긴다.**\
  몸통은 `이름$lambda$N` 이라는 `private static` 메서드이고 **거기엔 박싱이 없다**.
- ★★ **박싱은 `Function1.invoke(Object)Object` 라는 경계에서 난다** — `Integer.valueOf` → `invokeinterface` → `checkcast Number` → `intValue`.
- ★★ **객체 개수는 글자가 아니라 「호출 자리」가 정한다.** 캡처가 없으면 그 자리의 **싱글턴**(루프 3바퀴도 하나),\
  캡처가 있으면 **호출마다 새 객체**, 같은 글자라도 **자리가 둘이면 객체도 둘**이다.
- ★ **`::` 참조는 람다와 다르다** — `FunctionReferenceImpl` 을 상속한 **진짜 클래스 파일**이 생기고 `INSTANCE` 싱글턴으로 불린다.\
  그 클래스 안에 **`invoke(int)` 와 `invoke(Object)` 가 같이 있어 박싱의 양끝이 보인다**.
- ★★ **`map(::square)` 로는 아무것도 못 본다** — `map` 이 `inline` 이라 `Function1` 이 **0회** 등장한다.\
  람다가 객체가 되는 것을 보려면 **비인라인 고차 함수**가 필요하다.
- ★ **SAM 변환·`fun interface` 는 박싱을 없앤다**(`apply:(I)I`). 객체는 여전히 생긴다 — **없어지는 것은 포장이다**.
- 람다가 바깥 `var` 를 고치면 **`Ref$IntRef` 상자**가 생기고 `invokedynamic` 의 캡처 인자로 넘어간다.\
  **같은 코드가 Java 에서는 `must be final or effectively final` 로 거부된다**.
- **비인라인 람다의 맨 `return` 은 `'return' is prohibited here.`** 다. 익명 함수의 `return` 은 **자기만** 끝낸다.\
  바깥 함수까지 나가는 것은 [11번 주제](../11-inline-functions/)의 일이다.

## 관련 자료

- [`../README.md`](../README.md) — Kotlin 문법·API 주제 목록(이 주제는 10번)
- [08번 주제](../08-function-declaration-default-and-named-args/) — **직접 선행.** 함수 선언·기본 인자·`$default` 가 정본이다
- [09번 주제](../09-varargs-spread-local-and-infix-functions/) — **로컬 함수 쪽 정본.**\
  거기는 로컬 함수가 **클래스를 안 만드는 것**과 `Ref$IntRef`, 여기는 **람다 쪽**의 같은 자리
- [07번 주제](../07-loops-ranges-and-labels/) — 라벨과 `break`/`continue`. **비지역 `return` 을 여기로 넘겼고**, 여기서 다시 11로 넘긴다
- [11번 주제](../11-inline-functions/) — **직접 후행.** 이 문서가 센 **객체와 박싱을 없애는 방법**과 **비지역 `return`** 의 정본
- [12번 주제](../12-reified-type-parameters/) — `inline` 이 있어야 가능한 또 하나
- [13번 주제](../13-extension-functions-and-properties/) — 수신자가 첫 파라미터가 되는 것의 정본
- [03번 주제](../03-null-safe-types/) — `Intrinsics.checkNotNullParameter` 의 정본
- [`../../../java/syntax/29-lambda-expressions/`](../../../java/syntax/29-lambda-expressions/) — **Java 쪽 람다 정본.** `effectively final` 규칙이 거기 있다
- [`../../../java/syntax/30-method-references/`](../../../java/syntax/30-method-references/) — Java 쪽 `::` 정본. **Java 는 참조도 indy 다** — Kotlin 이 클래스를 만드는 것과 갈린다
- [`../../../java/syntax/31-functional-interfaces/`](../../../java/syntax/31-functional-interfaces/) — **박싱 대비의 정본.**\
  Java 는 원시 타입 전용 인터페이스를 43개 만들어 풀었고, Kotlin 은 `FunctionN` 하나로 두고 `inline` 으로 풀었다
- [`../../../java/syntax/19-type-erasure/`](../../../java/syntax/19-type-erasure/) — `invoke(Object)Object` 가 왜 그 모양인지
- [목록의 **14번 주제**](../14-scope-functions/)(scope function) — `let`/`run`/`apply` 가 **전부 `inline` 고차 함수**다
- [목록의 **36번 주제**](../36-function-types-fun-interface-and-sam-conversion/)(함수 타입·`fun interface`·SAM 변환) — **SAM 전체의 정본.** 여기는 박싱이 갈리는 자리만
- [목록의 **37번 주제**](../37-lambdas-with-receiver-and-type-safe-builders/)(리시버 지정 람다와 DSL) — `A.() -> Unit` 의 정본
- [목록의 **28번 주제**](../28-generics-variance-in-out-star-where/)(선언 지점 변성) — `? super Integer` 가 보이는 이유
- 목록의 **47번 주제**(`Sequence`) — 지연 평가에서 람다가 어떻게 쌓이나

## 용어 풀이

- **고차 함수(higher-order function)** — 함수를 인자로 받거나 함수를 돌려주는 함수.
- **람다(lambda)** — 이름 없이 `{ ... }` 로 적는 함수 리터럴. 마지막 식이 반환값이다.
- **익명 함수(anonymous function)** — `fun(x: Int): Int { ... }` 형태. 반환 타입을 적을 수 있고 `return` 이 자기만 끝낸다.
- **함수 타입(function type)** — `(A) -> B`. JVM 에서는 `FunctionN` 인터페이스다.
- **`Function1`** — 인자 1개짜리 함수 타입의 런타임 인터페이스. `invoke(Object): Object` 하나를 가진다.
- **`FunctionN`** — 파라미터가 23개 이상일 때 쓰이는 가변 항수 인터페이스.
- **`invokedynamic`(indy)** — 호출 자리를 실행 중에 **한 번만** 이어 붙이는 JVM 명령.
- **`LambdaMetafactory`** — 그 이어 붙이기를 해 주는 JDK 클래스. 숨은 클래스를 만들어 인터페이스 구현체를 돌려준다.
- **`CallSite`** — `invokedynamic` 자리 하나. 이어 붙인 결과를 들고 있어서 두 번째부터는 다시 안 만든다.
- **박싱(boxing) / 언박싱(unboxing)** — 원시 값을 객체로 감싸는 것 / 꺼내는 것.
- **캡처(capture)** — 람다가 바깥의 변수를 잡는 것. 잡힌 값은 indy 의 인자가 된다.
- **클로저(closure)** — 캡처한 변수를 함께 들고 다니는 함수.
- **`Ref$IntRef`** — kotlin-stdlib 내부의 `int` 한 칸짜리 상자. 캡처한 `var` 를 공유하려고 쓴다.
- **호출 가능 참조(callable reference)** — `::name` 형태로 이미 있는 함수·프로퍼티·생성자를 값으로 만드는 것.
- **바운드 참조(bound reference)** — `b::size` 처럼 수신자가 이미 정해진 참조.
- **`FunctionReferenceImpl`** — `::` 참조가 상속하는 stdlib 내부 클래스. 가리키는 대상의 이름·시그니처를 들고 있다.
- **SAM(Single Abstract Method) 변환** — 추상 메서드가 하나인 인터페이스 자리에 람다를 넘기는 것.
- **`fun interface`** — SAM 변환을 허용하는 Kotlin 인터페이스(1.4+).
- **마지막 인자 람다(trailing lambda)** — 마지막 인자가 람다일 때 괄호 밖에 적는 관용.
- **`it`** — 파라미터가 하나인 람다에서 그 파라미터의 기본 이름.

---

## 더 들어가면

- ★ **`makeTwice` 의 `$lambda$0`·`$lambda$1` 번호가 증거다.** 글자가 똑같은 람다 둘인데 **몸통 메서드도 둘**이다.\
  컴파일러가 "같은 글자니까 합치자" 를 **하지 않는다**는 뜻이다. 합치는 것은 `CallSite` 단위이고, 자리가 다르면 합쳐지지 않는다.
- **캡처한 값의 순서는 몸통 파라미터의 앞이다** — `useCapture$lambda$0(int, int)` 에서 `iload_1` 이 람다 파라미터,\
  `iload_0` 이 캡처한 `base` 다. 로컬 함수와 **같은 규칙**이다([09번 주제](../09-varargs-spread-local-and-infix-functions/)).
- **`::` 참조도 캡처하면 싱글턴이 아니다.** 바운드 참조 `b::size` 는 `refs.kt` 에서 `RefsKt$useBoundRef$1` 이라는 클래스가 생겼다\
  — **이 문서는 그 클래스의 내부는 찍지 않았다**(인스턴스가 수신자를 필드로 들고 있을 것이나, 확인하지 않았다).
- **`.name` 이 되는 것은 참조뿐이다.** `refs.kt` 의 `U` 가 `square` 를 돌려준 것은 `FunctionReferenceImpl` 이 이름을 들고 있기 때문이고,\
  호출부는 `invokeinterface kotlin/reflect/KFunction.getName` 이었다. **람다에는 그런 이름이 없다.**
- **`kotlin.jvm.functions.Function1` 이라는 이름을 소스에 쓰면 경고가 난다** —\
  `this class is not recommended for use in Kotlin. Use 'kotlin.Function1' instead.`\
  **경고도 출력이다.** Kotlin 쪽 정식 이름은 `kotlin.Function1` 이다.
- 이 문서에서 **성능은 한 번도 재지 않았다.** `javap` 로 본 것은 **객체 생성·박싱·클래스 파일의 유무**까지이고,\
  "그래서 어느 쪽이 빠르다" 는 하지 않은 주장이다.
- **못 잰 것** — `-jvm-target` 을 바꿔 가며 람다 생성 전략이 달라지는지는 **찍지 않았다**.\
  `-Xlambdas=class` 같은 플래그로 익명 클래스 전략을 강제할 수 있다고 알려져 있으나 **이 문서는 던져 보지 않았다.**
