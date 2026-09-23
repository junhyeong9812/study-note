# kotlin/syntax/10 — 람다와 고차 함수: `it`·마지막 인자 람다·클로저 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러·경고·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javap` 에서 실제로 얻었다.\
> 역어셈블은 **기본 `-jvm-target`(1.8 · `major version: 52`)** 이 정본이다 —\
> **람다가 `invokedynamic` 이 되는 것은 그 타깃에서의 선택이지 언어의 약속이 아니다.**\
> ★ 런타임 클래스 이름(`ExKt$$Lambda/0x…`)은 **판마다 다르다** — 세 판을 돌려 대조했다(2번).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★ **클래스 파일은 한 개다** — 람다는 `invokedynamic` + 숨은 정적 메서드가 된다

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

**왜 그런가**

- ★★ **람다가 넷인데 클래스 파일은 하나다.** "람다마다 `.class` 가 생긴다" 는 **익명 클래스 시대의 기억**이다.
- **몸통은 `이름$lambda$N` 이라는 `private static` 메서드**가 되고 **`(int)int`** 다 — **박싱이 없다**.
  캡처가 있으면 **캡처한 값이 앞 파라미터로 붙는다**(`useCapture$lambda$0(int, int)` 에서 `iload_0` 이 `base`).
- **봉투는 실행 중에 `LambdaMetafactory` 가 만든다.** `javap -v` 의 `BootstrapMethods` 절이 그것을 말한다.

```text
BootstrapMethods:
  0: #53 REF_invokeStatic java/lang/invoke/LambdaMetafactory.metafactory:(Ljava/lang/invoke/MethodHandles$Lookup;Ljava/lang/String;Ljava/lang/invoke/MethodType;Ljava/lang/invoke/MethodType;Ljava/lang/invoke/MethodHandle;Ljava/lang/invoke/MethodType;)Ljava/lang/invoke/CallSite;
    Method arguments:
      #39 (Ljava/lang/Object;)Ljava/lang/Object;
      #44 REF_invokeStatic IcodeKt.useLiteral$lambda$0:(I)I
      #46 (Ljava/lang/Integer;)Ljava/lang/Integer;
```

- ★ 세 번째 인자 `(Ljava/lang/Integer;)Ljava/lang/Integer;` 가 **어댑터 시그니처**다 —
  `(I)I` 인 몸통과 `(Object)Object` 인 인터페이스 사이를 메우는 자리이고, **박싱이 사는 곳**이다(7번).

### 2. ★★ `A true` · `B false` · `H false` · `I true` · `J false` — **자리가 정한다**

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

**출력** (`java -cp "outex2:$KSTD" Ex2Kt`)

```text
H two identical lambda literals : false
I same literal, 3 loop rounds   : true
J captures loop var, 3 rounds   : false
```

**왜 그런가**

```text
   글자가 같아도 자리가 다르면 다른 객체        자리가 같으면 몇 바퀴를 돌아도 한 객체
   +---------------------------------+         +---------------------------------+
   | val p = { n -> n + 1 }  자리 ①  |         | for (i in 1..3)                 |
   | val q = { n -> n + 1 }  자리 ②  |         |   seen.add({ n -> n + 1 })  자리 ①|
   | p === q  ->  false              |         | seen[0] === seen[1] -> true     |
   +---------------------------------+         +---------------------------------+
```

- ★★ **개수를 정하는 것은 「같은 글자인가」가 아니라 「같은 `invokedynamic` 자리인가」다.**
- **캡처가 없으면 그 자리의 싱글턴**(`A`·`I` 가 `true`) — `CallSite` 가 같은 인스턴스를 계속 돌려준다.
  **캡처가 있으면 호출마다 새 객체**(`B`·`J` 가 `false`) — 캡처값이 indy 의 인자로 들어가니 같은 것을 줄 수가 없다.
- **`H` 와 `I` 가 갈리는 근거는 1번의 `InvokeDynamic #2` 와 `#3`** 이다.
  `makeTwice` 는 글자가 똑같은 람다 둘인데 **indy 번호가 둘로 갈렸고 몸통 메서드도 `$lambda$0`·`$lambda$1` 둘**이다 —
  컴파일러가 **같은 글자라고 합치지 않는다.**
- ★★ **다섯 값 중 「언어가 약속한 것」은 0개다.** 전부 **이 컴파일러와 이 JVM 의 동작**이다.
  `C`·`D` 의 16진수가 **판마다 달랐다**는 것이 그 성격을 보여 준다 — **관찰은 관찰로 적는다.**

### 3. ★★ **참조가 만든다** — 클래스 파일 셋, 람다는 0개

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

**왜 그런가**

- ★ **`::` 참조 셋이 클래스 파일 셋을 만들었다.** 람다는 하나도 안 만들었는데 참조는 만든다.
- **호출 명령이 갈린다** — 람다는 `invokedynamic`, 참조는 **`getstatic … INSTANCE`** 다.
  참조는 **캡처가 없으면 클래스 하나당 객체 하나**(싱글턴)다.
- **`FunctionReferenceImpl` 을 상속**하고 생성자에 `class Refs2Kt`·`"square"`·`"square(I)I"` 를 넘긴다 —
  **자기가 무엇을 가리키는지 기억해야** 하기 때문이고, 그래서 `.name` 같은 리플렉션이 된다
  (`refs.kt` 실행에서 `.name` 이 `square` 였고 호출부는 `invokeinterface kotlin/reflect/KFunction.getName` 이었다).
- ★★ **박싱의 양끝이 이 한 클래스에 있다** — `invoke(int)` 가 `Integer.valueOf` 로 포장하고,
  `invoke(Object)` 가 `checkcast Number` + `intValue()` 로 개봉한다.

### 4. ★★ **0 이다** — `map` 이 `inline` 이라 아무것도 안 남는다

**출력** (`javap -c -p outrefs/RefsKt.class` 의 `useFunRef` 안에서 세어 본 것)

```text
$ javap -c -p outrefs/RefsKt.class | awk '/public static final int useFunRef\(\);/,/^$/' | grep -cE 'invokedynamic|Function1'
0
$ javap -c -p outrefs/RefsKt.class | awk '/public static final int useFunRef\(\);/,/^$/' | grep -nE 'square|Function1|invokedynamic'
57:     103: invokestatic  #57                 // Method square:(I)I
```

**왜 그런가**

- ★★ **`Function1` 도 `invokedynamic` 도 0회**다. 대신 **루프가 통째로 펼쳐져 있고** `invokestatic square:(I)I` 하나가 있다.
- **`map` 은 stdlib 의 `inline` 함수**라 루프도 람다도 **호출부에 그대로 들어온다** — 객체가 안 남는다.
  왜 펼쳐지고 그 대가가 무엇인지는 [11번 주제](../11-inline-functions/)가 정본이다.
- ★ **그래서 실측하려면 「내가 만든 비인라인 고차 함수」로 재야 한다.** 이 문서가 `apply1` 을 직접 만든 이유다.
- ★ **실무 결론 하나가 여기서 나온다** — **컬렉션 연산에 람다를 쓰는 것은 대개 객체를 안 만든다.**
  객체가 생기는 쪽은 **내가 만든 고차 함수에 람다를 넘길 때**다.

### 5. ★ `'return' is prohibited here.` — 몸통이 **다른 메서드**에 살기 때문이다

**출력** (`kotlinc bad1.kt`)

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

**출력** (`java -cp "outanon:$KSTD" AnonKt`)

```text
K anonymous fun    : 101
L return@runIt     : 101
M return@lam       : 101
N anon fun in forEach over [1,-2,3] : 13
```

**왜 그런가**

- **비인라인 람다의 몸통은 `이름$lambda$N` 이라는 다른 메서드**다(1번). 거기서 `return` 해 봐야 **그 메서드만 끝난다** —
  바깥 함수를 끝낼 방법이 없어 **컴파일러가 아예 거부한다.**
- **`N` 이 `13` 인 것이 익명 함수의 성질을 증명한다** — `-2` 에서 `return` 했는데 `forEach` 는 계속 돌아 `3` 까지 붙었다.
  **익명 함수의 `return` 은 자기 자신만 끝낸다.**

| 형태 | 무엇을 끝내나 |
|---|---|
| 람다 안의 맨 `return` | **컴파일 거부**(비인라인일 때) |
| `return@runIt` · `return@lam` | **그 람다만** |
| 익명 함수 `fun(x: Int) { return }` | **그 익명 함수만** |
| 인라인 함수에 넘긴 람다의 맨 `return` | **바깥 함수** — 정본은 [11번 주제](../11-inline-functions/) |

- 라벨을 안 붙이면 **자기를 받는 함수 이름**이 기본 라벨이 된다(`return@forEach`).

### 6. ★★ `AA` 는 `10`, Java 는 **컴파일이 안 된다**

**출력** (`java -cp "outclo:$KSTD" CloKt`)

```text
AA countUp(4) = 10
AB seen after two calls = 7
```

**출력** (`javac Clo.java`)

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

**왜 그런가**

Kotlin 쪽 바이트코드에 **Java 에 없는 상자가 하나 생긴다**.

```text
  public static final int countUp(int);
    Code:
       0: new           #41                 // class kotlin/jvm/internal/Ref$IntRef
       3: dup
       4: invokespecial #45                 // Method kotlin/jvm/internal/Ref$IntRef."<init>":()V
       7: astore_1
       8: aload_1
       9: invokedynamic #63,  0             // InvokeDynamic #0:invoke:(Lkotlin/jvm/internal/Ref$IntRef;)Lkotlin/jvm/functions/Function1;
      ...
      44: aload_1
      45: getfield      #66                 // Field kotlin/jvm/internal/Ref$IntRef.element:I
      48: ireturn
```

- ★ **`Ref$IntRef` 라는 한 칸짜리 상자**를 만들어 **바깥과 람다가 같은 칸을 보게** 한다.
- **상자는 `invokedynamic` 의 캡처 인자로 넘어간다**(`(Lkotlin/jvm/internal/Ref$IntRef;)Lkotlin/jvm/functions/Function1;`).
  람다 몸통은 그 상자의 `element` 를 `getfield`/`putfield` 로 읽고 쓰고, **바깥 함수도 같은 칸에서 읽는다.**
- ★★ **「`var` 를 고칠 수 있다」는 언어 규칙이고 「상자가 `Ref$IntRef` 다」는 구현이다.** 둘을 같이 적으면 안 된다.
- **캡처가 있으므로 봉투도 호출마다 새로** 생긴다(2번의 `B`).

### 7. ★★ 박싱은 **람다 몸통이 아니라 `Function1` 경계**에서 난다

**왜 그런가**

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

- ★★ **원인이 되는 시그니처는 `Function1.invoke(Object): Object`** 다. 제네릭이 소거된 결과다.
  **몸통(`useLiteral$lambda$0(int): int`)에는 박싱이 없다** — 포장·개봉은 전부 **경계**에서 일어난다.
- **개봉은 `checkcast Number` + `invokevirtual Number.intValue()`** 두 명령이다.
- **Java 는 인터페이스를 43개 만들어 풀었다**(`IntUnaryOperator` 는 `int applyAsInt(int)` 다) —
  정본은 [`../../../java/syntax/31-functional-interfaces/`](../../../java/syntax/31-functional-interfaces/).
  **Kotlin 은 `FunctionN` 하나로 두고 `inline`([11번 주제](../11-inline-functions/))과 `fun interface`(9번)로 푼다.**
  `invoke(Object)Object` 가 왜 그 모양인지는 [`../../../java/syntax/19-type-erasure/`](../../../java/syntax/19-type-erasure/)가 정본이다.
- ★ **이 문서는 그 비용을 재지 않았다.** `javap` 로 본 것은 **명령의 유무**까지다.

### 8. ★ `FunctionN` 인터페이스 — **22 와 23 사이에 경계가 있다**

**출력** (`javap -s -p outft/FtypesKt.class` — 발췌)

```text
  public static final java.lang.String f1(kotlin.jvm.functions.Function1<? super java.lang.Integer, java.lang.String>);
    descriptor: (Lkotlin/jvm/functions/Function1;)Ljava/lang/String;

  public static final java.lang.String fRecv(kotlin.jvm.functions.Function1<? super java.lang.Integer, java.lang.String>);
    descriptor: (Lkotlin/jvm/functions/Function1;)Ljava/lang/String;

  public static final java.lang.String fNullable(kotlin.jvm.functions.Function1<? super java.lang.Integer, java.lang.String>);
    descriptor: (Lkotlin/jvm/functions/Function1;)Ljava/lang/String;

  public static final java.lang.String f22(kotlin.jvm.functions.Function22<? super java.lang.Integer, ? super java.lang.Integer, ? super java.lang.Integer, ? super java.lang.Integer, ? super java.lang.Integer, ? super java.lang.Integer, ? super java.lang.Integer, ? super java.lang.Integer, ? super java.lang.Integer, ? super java.lang.Integer, ? super java.lang.Integer, ? super java.lang.Integer, ? super java.lang.Integer, ? super java.lang.Integer, ? super java.lang.Integer, ? super java.lang.Integer, ? super java.lang.Integer, ? super java.lang.Integer, ? super java.lang.Integer, ? super java.lang.Integer, ? super java.lang.Integer, ? super java.lang.Integer, java.lang.String>);
    descriptor: (Lkotlin/jvm/functions/Function22;)Ljava/lang/String;

  public static final java.lang.String f23(kotlin.jvm.functions.FunctionN<java.lang.String>);
    descriptor: (Lkotlin/jvm/functions/FunctionN;)Ljava/lang/String;
```

**왜 그런가**

- **`(Int) -> String` 은 `kotlin.jvm.functions.Function1`** 이다. 문법 설탕이 아니라 **인터페이스 이름의 별칭**이다.
- ★ **`Function0`\~`Function22` 까지 스물셋이 전용 타입이고, 파라미터가 23개가 되면 `FunctionN` 하나로 몰린다.**
  「22 가 한계」가 아니라 **22 까지만 전용 타입이 있다**는 뜻이다.
- ★★ **`Int.() -> String`·`((Int) -> String)?` 는 `(Int) -> String` 과 디스크립터가 같다.**
  수신자는 **첫 파라미터**로 내려가고([13번 주제](../13-extension-functions-and-properties/)와 같은 자리),
  nullable 여부는 디스크립터에 **안 남는다**.
- ★ **그래서 나는 컴파일 에러** — `(Int) -> String` 과 `Int.() -> String` 으로 오버로드하면
  **`conflicting overloads`** 다. 이름을 다르게 지어야 한다.
- 제네릭 인자가 `? super Integer` 로 보이는 것은 함수 타입 파라미터가 **반변**이기 때문이다(목록의 **28번 주제**).

### 9. ★ SAM 변환은 **포장을 없앤다 — 객체는 그대로 생긴다**

**출력** (`javap -c -p outsam/SamKt.class` — 발췌)

```text
  public static final int useSam();
    Code:
       0: invokedynamic #23,  0             // InvokeDynamic #0:apply:()LJInt;
       5: astore_0
       6: aload_0
       7: bipush        10
       9: invokeinterface #27,  2           // InterfaceMethod JInt.apply:(I)I
      14: ireturn

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

**왜 그런가**

- ★★ **호출 명령은 `invokeinterface JInt.apply:(I)I`** 이고 **`Integer.valueOf` 가 한 번도 안 나온다**(0회).
  인터페이스 메서드가 **`int` 를 받는다고 적혀 있기** 때문이다.
- **객체는 그대로 생긴다** — `invokedynamic … ()LJInt;`, 런타임 클래스는 `SamKt$$Lambda/0x…`(`Z`).
  두 번 적으면 **자리가 둘이라 다른 객체**다(`Y` 가 `false`, 2번과 같은 규칙).
  **없어지는 것은 객체가 아니라 포장이다.**
- **Kotlin 쪽에서 같은 것을 얻으려면 `fun interface`** 이고 **1.4 부터**다. 바이트코드도 같다(`KInt.apply:(I)I`).
- ★ 그래서 **박싱을 피하는 길은 둘**이다 — ① 시그니처가 원시 타입인 **SAM·`fun interface`**,
  ② 객체 자체를 안 만드는 **`inline`**([11번 주제](../11-inline-functions/)).
  **Kotlin 의 함수 타입만 쓰면 두 길 다 안 탄다.** SAM 전체의 정본은 목록의 **36번 주제**다.

### 10. `it` 은 하나일 때만, 괄호 밖은 마지막 하나만

**출력** (`java -cp "oform:$KSTD" FormKt`)

```text
AC 괄호 안              : 11
AD 괄호 밖(마지막 인자) : 11
AE 인자가 람다뿐        : 42
AF 두 람다 중 하나만 밖 : 22
AG 중첩 람다의 it        : n=7
AH 인자를 안 쓸 때 _    : 99
```

**왜 그런가**

- **`it` 은 파라미터가 정확히 하나일 때만 생긴다.** 이름을 적으면 `it` 은 없어지고,
  둘 이상이면 **`unresolved reference 'it'`** + 타입 불일치가 같이 난다.
- **괄호 밖으로 나갈 수 있는 것은 마지막 인자 하나뿐이다**(`AF` 에서 앞의 람다는 괄호 안에 남았다).
  마지막이 아닌 자리에 쓰면 **마지막 파라미터에 매칭돼** 진단이 줄줄이 난다(실측에서 한 호출에 3건).
- ★ **중첩하면 안쪽 `it` 이 바깥 `it` 을 가린다** — `AG` 에서 안쪽 `it` 은 `"n="` 이고
  바깥 파라미터는 이름 `a` 로 받았다. **이름을 붙이는 것이 중첩의 정답이다.**
- **인자가 람다 하나뿐이면 괄호가 통째로 사라진다**(`run { 40 + 2 }` → `AE`).
- `_` 는 **안 쓰는 파라미터**의 이름이다(`AH`).

### 11. 정본이 어디인지

- **비지역 `return`** — [11번 주제](../11-inline-functions/). 여기서는 「비인라인 람다에서는 맨 `return` 이 거부된다」까지만 다뤘다.
  [07번 주제](../07-loops-ranges-and-labels/)가 라벨을 여기로 넘겼고, 여기서 다시 11로 넘긴다.
- **로컬 함수** — [09번 주제](../09-varargs-spread-local-and-infix-functions/).
  ★ 로컬 함수는 **합성 클래스를 아예 안 만들고** `invokestatic` + `Ref$IntRef` 로 끝난다.
  **같은 「상자」를 쓰는데 이쪽은 `invokedynamic`, 저쪽은 `invokestatic`** 이라는 것이 대비의 핵심이다.
- **`let`/`run`/`with`/`apply`/`also`** — 전부 **`inline` 고차 함수**이고 정본은 [목록의 **14번 주제**](../14-scope-functions/)다.
  그래서 scope function 을 써도 **람다 객체가 안 생긴다**(4번과 같은 이유).
- **`invoke(Object)Object` 의 모양** — [`../../../java/syntax/19-type-erasure/`](../../../java/syntax/19-type-erasure/)가 정본이고,
  Kotlin 이 그것을 **뚫는 방법**은 [12번 주제](../12-reified-type-parameters/)다.

## 실행 검증

```text
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
openjdk version "21.0.5" 2024-10-15 LTS
OpenJDK Runtime Environment Temurin-21.0.5+11 (build 21.0.5+11-LTS)
OpenJDK 64-Bit Server VM Temurin-21.0.5+11 (build 21.0.5+11-LTS, mixed mode, sharing)
```

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `ftypes.kt` | `Function0`\~`Function22` 와 **23부터 `FunctionN`** · 수신자·nullable 의 디스크립터 | `kotlinc` → `javap -s -p` |
| `icode.kt` | 람다가 `invokedynamic` 이 되고 **클래스 파일이 안 느는 것** · 몸통 이름 · 박싱 자리 | `kotlinc` → `find` · `javap -c -p` · `javap -v -p` |
| `ex.kt` | `A`\~`G` — 캡처 유무로 갈리는 객체 동일성 · 런타임 클래스 이름 | `kotlinc`(경고 1건) → `java` **3판** |
| `ex2.kt` | `H`·`I`·`J` — 같은 글자 두 자리 · 루프 3바퀴 · 루프 변수 캡처 | `kotlinc` → `java` |
| `refs2.kt` | `::` 참조가 **클래스 파일을 만드는 것** · `FunctionReferenceImpl` · `INSTANCE` | `kotlinc` → `find` · `javap -c -p` 2벌 |
| `refs.kt` | `map(::square)` 에 `Function1` 이 **0회**인 것 · `.name` · 바운드 참조 클래스 | `kotlinc` → `javap` + `awk`/`grep` · `java` |
| `sam.kt` + `JInt.java` | SAM·`fun interface` 가 **`apply:(I)I`** 로 박싱을 없애는 것 | `javac` → `kotlinc` → `javap -c -p` · `java` |
| `clo.kt` + `Clo.java` | 캡처한 `var` 가 **`Ref$IntRef`** 가 되는 것 · Java 는 **거부**하는 것 | `kotlinc` → `javap -c -p` · `java` · `javac`(실패가 결과) |
| `bad1.kt` | 비인라인 람다의 맨 `return` 이 거부되는 것 | `kotlinc` (컴파일 실패가 결과) |
| `anon.kt` | `K`\~`N` — 익명 함수·라벨 반환이 **무엇을 끝내나** | `kotlinc` → `java` |
| `form.kt` | `AC`\~`AH` — 괄호 위치·중첩 `it`·`_` | `kotlinc` → `java` |
| 진단 4벌 | 2인자 람다의 `it` · 괄호 밖 위치 오류 · 람다 인자 개수 · `conflicting overloads` | `kotlinc` (컴파일 실패가 결과) |

**구현 의존 항목** — `javap` 의 명령 이름·상수 풀 번호, `invokedynamic`/`LambdaMetafactory` 전략,
`이름$lambda$N` 이라는 합성 메서드 이름, `Ref$IntRef` 라는 상자 이름, `FunctionReferenceImpl`·`INSTANCE`,
`ExKt$$Lambda/0x…` 라는 런타임 클래스 이름, `map` 이 `inline` 이라는 stdlib 의 선택 —
**전부 이 컴파일러 버전 + 기본 타깃(1.8)의 산출물**이다.\
반면 **「함수 타입이 `FunctionN` 이다」·「`it` 은 하나일 때만」·「마지막 인자 람다」·
「비인라인 람다의 맨 `return` 금지」·「익명 함수의 `return` 은 자기만 끝낸다」·「람다가 바깥 `var` 를 고칠 수 있다」**
는 **언어 규칙**이라 타깃과 무관하다.

**★ 던져 봤더니 예상과 달랐던 것 — 세 건**

1. **「람다마다 `.class` 가 생긴다」가 틀렸다.** 람다 넷짜리 파일에서 클래스 파일은 **하나**였다.
   익명 클래스가 생기는 쪽은 **`::` 참조**이고, 그쪽은 셋을 만들었다 — **예상이 정확히 뒤집혔다.**
2. **`map`·`forEach` 로는 아무것도 못 본다.** 「람다가 객체가 된다」를 확인하려고 컬렉션 연산을 찍으면
   `Function1` 이 **0회** 나온다 — stdlib 이 `inline` 이기 때문이다.
   **실측 대상을 직접 만들지 않으면 결론이 통째로 반대로 나올 뻔했다.**
3. **같은 글자 람다가 같은 객체가 아니었다**(`H` 가 `false`). 합쳐지는 단위는 **글자가 아니라 `invokedynamic` 자리**였고,
   `makeTwice` 의 `$lambda$0`·`$lambda$1` 이 그 증거였다.

**안 걸린 것도 출력이다** — `ex.kt` 에서 `A`\~`G` 는 **세 판이 한 글자도 같았는데** `C`·`D` 의 16진수만 판마다 달랐다.
**「세 판이 같았다」가 「보장된다」를 뜻하지 않는다** — 그래서 런타임 클래스 이름은 **관찰**로만 적었다.
