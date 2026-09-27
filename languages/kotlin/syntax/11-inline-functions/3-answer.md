# kotlin/syntax/11 — 인라인 함수: `noinline`/`crossinline`·비지역 `return` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러·경고·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javap` 에서 실제로 얻었다.\
> 역어셈블은 **기본 `-jvm-target`(1.8 · `major version: 52`)** 이 정본이고, 10번에서 `-jvm-target 21` 을 따로 찍어 `diff` 했다.\
> ★★ **성능은 한 번도 재지 않았다.** 잰 것은 **코드 크기**(바이트 수와 명령 줄 수)뿐이다(7번).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★ 둘이 경고를 받는다 — 기준은 **「펼칠 수 있는 람다가 있나」**

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

**왜 그런가**

| 선언 | 결과 |
|---|---|
| `noLambda` — 람다를 안 받음 | **경고** |
| `onlyNoinline` — 람다를 받지만 `noinline` | **경고** ★ |
| `ok` — 펼칠 수 있는 람다가 있음 | 조용하다 |

- **에러가 아니라 경고**이고 `exit 0` 이다 — **컴파일은 통과한다.**
- ★★ **`onlyNoinline` 이 결정적이다.** 함수 타입 파라미터가 **있는데도** 경고가 난다 —
  `noinline` 이라 **펼칠 수 없기** 때문이다.
- **그래서 기준은 「함수 타입 파라미터가 있나」가 아니라 「펼칠 수 있는 람다가 있나」다.**
  즉 **`inline` 의 목적은 람다 객체를 없애는 것**이라고 컴파일러 스스로 적어 둔 셈이다.
  (★ [12번 주제](../12-reified-type-parameters/)에서 이 기준에 **「`reified` 가 있나」가 하나 더 붙는다.**)
- ★ **경고를 보려면 에러가 없어야 한다.** 같은 선언에 nullable 인라인 파라미터 에러를 하나 섞은 파일에서는
  **이 경고가 0줄**이었다(6번의 `warn.kt`).

### 2. ★★ 사라지는 것은 **`invokedynamic`·박싱·합성 메서드** 셋이다

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

**왜 그런가**

- ★★ **사라지는 셋** — ① `invokedynamic`(= `Function1` 객체) ② `Integer.valueOf`/`checkcast`+`intValue`(= 박싱 왕복)
  ③ **`caller$lambda$0` 이라는 합성 메서드**. 인라인 쪽 `caller()` 에는 **`iadd` 두 번**이 전부다
  (`f(f(x))` 이므로 몸통이 두 벌 들어갔다).
- **메서드 목록이 달라진다** — 비인라인 쪽은 `twice`·`caller`·`caller$lambda$0` 셋,
  인라인 쪽은 `twice`·`caller` 둘이다. ★ **`caller$lambda$0` 이 아예 없는 것**이 8번을 통째로 설명한다.
- ★ **`twice` 자체는 안 사라진다.** 양쪽 다 `public static final` 로 남아 있다 — **Java 가 그것을 부른다.**

```text
===== 소스: api.kt =====
inline fun <reified T> isA(x: Any): Boolean = x is T
inline fun plain(x: Int, f: (Int) -> Int): Int = f(x)
fun normal(x: Int): Int = x + 1
===== 소스: UsePlain.java =====
import kotlin.jvm.functions.Function1;

public class UsePlain {
    public static void main(String[] a) {
        Function1<Integer, Integer> f = x -> x + 1;
        System.out.println("M Java calls inline plain(10) : " + ApiKt.plain(10, f));
        System.out.println("N Java calls normal(10)       : " + ApiKt.normal(10));
    }
}
===== javac -cp oapi:kotlin-stdlib.jar UsePlain.java -d oj → java -cp "oj:oapi:kotlin-stdlib.jar" UsePlain =====
M Java calls inline plain(10) : 11
N Java calls normal(10)       : 11
```

- **`iconst_0 / istore_N` 쌍**은 인라인 경로용 **표식 지역 변수**(`$i$f$함수이름` 류)다. 동작에는 영향이 없다.
  ★ **이 문서는 `javap -c` 만 찍어 그 변수 이름까지는 확인하지 않았다**(`javap -l` 로 보면 나올 것이나 **안 찍어 봤다**).
- `bipush 10 -> istore_0 -> iload_0` 처럼 값을 한 번 넣었다 빼는 모양이 남는다 —
  **인라인은 붙여 넣기이지 최적화가 아니다.** 다듬는 것은 JIT 의 몫이고 **이 문서는 그것을 재지 않았다.**

### 3. ★★ `neg` · `none` · `none` — `areturn` 이 **두 개** 대 **하나**

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
       ...
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
       ...
      50: iload         5
      52: ifge          55
      55: nop
      56: goto          20
      59: nop
      60: ldc           #42                 // String none
      62: areturn
```

**왜 그런가**

- ★★ **`hasNeg` 안에 `areturn` 이 두 개다.** 57번 자리의 `areturn` 은 **람다 안에 적은 `return "neg"`** 이고,
  그것이 **`hasNeg` 자신의 반환 명령**으로 박혀 있다 — **람다라는 경계가 바이트코드에 남아 있지 않다.**
- ★ **`return@forEach` 는 `areturn` 이 아니다.** `ifge 55 / 55: nop / 56: goto 20` —
  조건이 참이면 아무것도 안 하고 **다음 바퀴로 간다.** 그래서 `C` 가 `none` 이다.
  **라벨 붙은 `return` 은 `continue` 쪽이고, 라벨 없는 `return` 은 바깥 함수를 끝낸다.**
- ★ **`Function1` 이 한 번도 안 나온다.** `forEach` 자체가 인라인이라 **`iterator()` 루프째 `hasNeg` 안으로 들어왔다**
  (같은 이유로 `map`·`filter`·`let`·`run`·`use` 도 람다 객체를 안 만든다 —
  [10번 주제](../10-lambdas-and-higher-order-functions/)가 그 함정을 다룬다).

### 4. ★ `invokedynamic` 은 **하나**, 합성 메서드는 **`caller$lambda$1`**

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

**왜 그런가**

- ★ **`invokedynamic` 이 딱 하나**다 — `noinline` 인 `g` 쪽만 객체가 됐다. `f` 는 `iconst_1 / iadd` 로 펼쳐졌다.
- ★★ **이름이 `caller$lambda$1` 로 1번부터 시작한다.** 0번은 `f` 의 몫이었는데 **펼쳐져 사라졌다** —
  **번호에 빈칸이 남은 것이 「여기 람다가 하나 있었다」는 자국**이다.
- **`noinline` 은 객체만 되돌리는 것이 아니다** — `Integer.valueOf` → `invoke(Object)` → `checkcast Number` → `intValue` 가
  그대로 살아 있다. **박싱까지 함께 돌아온다.**
- `store(g)` 처럼 **람다를 값으로 내보내야 하면** `noinline` 이 필수다 — 안 붙이면 6번의 `[A]` 에러다.

### 5. ★★ 클래스 파일 **셋** — 그중 둘이 `Runnable` 이고 **역할이 다르다**

**출력** (`find ocross -name '*.class' | sort`)

```text
ocross/CrossKt$caller$$inlined$guard$1.class
ocross/CrossKt$guard$r$1.class
ocross/CrossKt.class
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

**왜 그런가**

- **역할이 다르다.**

| 클래스 | 누구 것인가 | 필드 | `run()` 안 |
|---|---|---|---|
| `CrossKt$guard$r$1` | **선언 쪽 본체용**(Java 가 부를 때) | `$f: Function1` 있음 | `invoke(Object)` + 박싱 |
| `CrossKt$caller$$inlined$guard$1` | ★ **호출 자리 전용** — 이름에 `caller` 가 박혔다 | **없다** | 람다 몸통이 `iadd` 로 직접 |

- ★ **이름이 호출 경로를 말해 준다** — `caller` 는 **호출한 함수**, `guard` 는 **인라인된 함수**,
  `$$inlined$` 는 **전개해서 만든 것**이라는 표시다. **호출 자리가 늘면 이 클래스도 자리마다 하나씩 는다.**
- **`return f(2)` 자리는 펼쳐진다** — `caller()` 안이 `iconst_2 / iconst_1 / iadd` 이고 객체가 없다.
- ★★ **금지의 이유** — **람다 몸통이 `run()` 안으로 들어가는데 `run()` 의 `return` 은 `run()` 만 끝내므로,
  거기서 `caller()` 를 끝낼 방법이 없다.** 그래서 `crossinline` 은 "펼쳐는 주되 비지역 `return` 은 쓰지 마라" 는 약속이다.

### 6. ★★ 통과하는 것은 `[F]` 하나 — 셋이 **고치는 법을 이름으로** 말해 준다

**출력** (`kotlinc bad1.kt` — `[A]`·`[B]`)

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

**출력** (`kotlinc warn.kt` — `[C]`)

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

**출력** (`kotlinc bad5.kt` — `[D]`)

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

**출력** (`kotlinc bad4.kt` — `[E]`·`[F]`)

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

**출력** (`kotlinc pub.kt` — `@PublishedApi` 로 연 것)

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

**왜 그런가**

- **통과하는 것은 `[F]`(`internal inline fun internalOk`) 하나**다. 나머지 다섯은 에러다.
- ★ **고치는 법을 이름으로 말해 주는 것은 셋** — `Add 'noinline' modifier` · `Add 'crossinline' modifier` ·
  `Add 'noinline' modifier … or make its type not nullable`. **에러 메시지가 교재인 언어**의 전형이다.
- ★★ **`[E]` 와 `[F]` 를 가르는 것은 가시성**이다. 막히는 것은 **공개 API 인 인라인 함수**뿐이다 —
  몸통이 **남의 모듈 안으로 복사돼 들어가기** 때문이고, 그쪽에서는 `private` 선언이 안 보인다.
  `internal inline` 은 같은 모듈 안에서만 복사되므로 막을 이유가 없다.
- **여는 애너테이션은 `@PublishedApi`**(1.2+)이고, 그러면 **에러 대신 1번의 경고**가 나온다
  (`exposed` 가 람다를 안 받으니 당연하다).

### 7. ★ 잰 것은 **크기뿐**이다 — 한 메서드가 **4줄에서 140줄**

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

**왜 그런가**

- ★★ **잰 것은 코드 크기뿐이다.** 실행 시간·JIT 인라인 한계·아이캐시는 **한 번도 재지 않았다.**
  **「코드가 커지면 느려질 수 있다」는 이 문서가 하지 않은 주장**이고, 근거의 끝은 1번의 컴파일러 경고다.
- **작은 몸통 다섯 호출에서 바이트는 1.11배**(2,338 → 2,599)뿐이다 — 클래스 파일에는 상수 풀 등이 같이 들어 있어
  **바이트 배수가 명령 배수보다 작게 나온다.**
- **몸통을 키우면 배수가 오른다** — 명령 줄 수 기준 **2.10배 → 5.98배**.
- ★ **`c1()` 한 메서드는 4줄에서 140줄**이 됐다. 비인라인 쪽은 `invokedynamic` + 상수 + `invokestatic` + `ireturn` 넷이면 끝인데,
  인라인 쪽은 `heavy` 의 몸통이 통째로 들어왔다.
- **이 대가는 [10번 주제](../10-lambdas-and-higher-order-functions/)가 센 객체 생성과 맞바꾸는 관계**다.

### 8. ★★ 몸통이 **다른 메서드**에 살기 때문이다

**왜 그런가**

- 비인라인 람다의 몸통은 **`caller$lambda$0` 이라는 별도 메서드**다(2번의 비인라인 쪽).
  거기서 `ireturn` 을 해 봐야 **그 메서드만 끝난다** — `caller()` 를 끝낼 방법이 없다.
- **그래서 컴파일러가 아예 거부한다.**

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

- **인라인하면 그 별도 메서드가 사라지고**(2번) 람다 몸통이 호출자 안에 들어오므로,
  거기 적은 `return` 이 **호출자 자신의 `areturn`** 이 된다(3번).
- ★ **같은 문구가 세 원인에서 나온다** — ① **비인라인** 고차 함수 ② **`noinline`** 파라미터 ③ **`crossinline`** 파라미터.
  셋 다 `'return' is prohibited here.` 이고 **메시지만으로는 구분할 단서가 없다.**
  **선언 쪽의 `inline`/`noinline`/`crossinline` 을 봐야 한다.**

### 9. 공개 API 인라인은 **몸통이 남의 모듈로 복사**되기 때문에 막힌다

**왜 그런가**

- **에러는 `public-API inline function cannot access non-public-API function.`** 다(6번의 `bad4.kt`).
- **몸통이 호출자 쪽 모듈에 복사돼 들어가는데**, 그쪽에서는 `private` 선언이 **보이지 않는다.**
  그래서 컴파일러가 **선언 시점에** 막는다.
- **`internal inline` 은 안 막힌다** — 복사가 **같은 모듈 안에서만** 일어나므로 `private` 선언이 보인다.
  (실측: 같은 파일에서 `exposed` 는 에러, `internalOk` 는 **아무 말도 없었다**.)
- **라이브러리 인라인 함수의 몸통을 고치면** 사용자 쪽에는 **이미 복사된 옛 몸통이 남아 있고
  사용자가 재컴파일해야 반영된다** — ★ **이 문서는 그것을 실측하지 않았다.**
  재현하려면 **같은 라이브러리의 두 판본**이 필요하다. 근거는 「몸통이 복사된다」는 위의 사실뿐이다.

### 10. 같았다 — 다만 **관찰이지 보장이 아니다**

**출력**

```text
=== major ===
  major version: 65
===== 21 에서 전체 diff (1.8 대비) =====
noinl: 1.8 과 21 이 같다
inl: 1.8 과 21 이 같다
```

**왜 그런가**

- **확인한 방법** — 2번의 두 파일을 `-jvm-target 21` 로 다시 컴파일해 `javap -c -p` 출력을 `diff` 했다.
- **`major version` 은 1.8 에서 52, 21 에서 65** 다. 그것만 바뀌고 **역어셈블은 한 글자도 다르지 않았다.**
- ★ **관찰이다.** **두 타깃만 봤다** — 「모든 타깃에서 같다」는 하지 않은 주장이다.
- **「인라인이 프런트엔드 변환이라 백엔드 선택지와 안 겹친다」는 설명은 근거가 아니라 해석**이다.
  근거는 `diff` 결과 한 줄뿐이다.

### 11. 정본이 어디인지

- **`reified`** — [12번 주제](../12-reified-type-parameters/)가 정본이고, 거기서 `inline` 은 **선택이 아니라 전제**다.
  `reified` 없이 붙인 `inline` 은 성능 이야기지만, `reified` 는 **`inline` 이 없으면 문법 자체가 성립하지 않는다.**
  (이 주제의 (3)에서 본 `ACC_SYNTHETIC` 도 거기가 정본이다.)
- **람다가 `invokedynamic` + `Function1` 이 되는 것** — [10번 주제](../10-lambdas-and-higher-order-functions/).
  객체가 몇 개 생기는지, 박싱이 어디서 나는지가 거기다. **여기는 그것을 없애는 쪽만 다뤘다.**
- **인라인 람다 안에서 바깥 루프를 `break`/`continue`** — **2.2.0** 부터이고 정본은 [07번 주제](../07-loops-ranges-and-labels/)다.
  거기는 **루프를 빠져나오는 것**, 여기는 **함수를 빠져나오는 것**(1.0)이다.
- **`let`/`run`/`with`/`apply`/`also`** — **전부 인라인 함수**다. 이 주제의 대표 사용처이고 정본은 [목록의 **14번 주제**](../14-scope-functions/)다.

## 실행 검증

```text
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
openjdk version "21.0.5" 2024-10-15 LTS
OpenJDK Runtime Environment Temurin-21.0.5+11 (build 21.0.5+11-LTS)
OpenJDK 64-Bit Server VM Temurin-21.0.5+11 (build 21.0.5+11-LTS, mixed mode, sharing)
```

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `warn0.kt` · `warn2.kt` | 「의미 없다」 경고 · **`noinline` 뿐이어도 경고가 나는 것** | `kotlinc` (경고 1건 · 2건 · `exit 0`) |
| `noinl.kt` / `inl.kt` | `inline` 한 낱말 차이 — 객체·박싱·합성 메서드가 사라지는 것 | `kotlinc` 2회 → `javap -c -p` 2회 |
| `noinl.kt` / `inl.kt` (타깃 21) | 결론이 `-jvm-target` 에 안 흔들리는 것 | `kotlinc -jvm-target 21` → `javap` → `diff` |
| `api.kt` + `UsePlain.java` | 인라인 함수 본체가 남아 **Java 가 부르는 것** · `reified` 만 `ACC_SYNTHETIC` | `kotlinc` → `javap -v -p` → `javac` → `java` |
| `nlr.kt` | `A`·`B`·`C` · **`areturn` 두 개 대 하나** · `Function1` 0회 | `kotlinc` → `java` → `javap -c -p` |
| `bad0.kt` | 비인라인 람다의 맨 `return` 이 거부되는 것 | `kotlinc` (컴파일 실패가 결과) |
| `noin.kt` | `noinline` 이 **그 람다만** 객체로 되돌리는 것 · `$lambda$1` 의 빈 번호 | `kotlinc` → `javap -c -p` |
| `cross.kt` | `crossinline` 이 **호출 자리별 클래스**를 만드는 것 · 두 클래스의 역할 차이 | `kotlinc` → `find` → `javap -c -p` 3회 |
| `bad1.kt` | `noinline`/`crossinline` 을 요구하는 에러 둘 | `kotlinc` (컴파일 실패가 결과) |
| `bad4.kt` · `pub.kt` | 공개 API 인라인의 가시성 제약 · `internal inline` 은 통과 · `@PublishedApi` | `kotlinc` 2회 (실패 1 · 통과 1) |
| `bad5.kt` | 인라인 함수의 재귀 금지 | `kotlinc` (컴파일 실패가 결과) |
| `warn.kt` | nullable 인라인 파라미터 금지 · **에러가 있으면 경고가 통째로 안 보이는 것** | `kotlinc` (컴파일 실패가 결과) |
| `sizeN/I.kt` · `bigN/I.kt` | 코드 크기 배수(바이트·명령 줄 수·`c1()` 한 메서드) | `kotlinc` 4회 → `ls -l` 2회 → `javap` + `grep -c` |
| 진단 2벌 | `crossinline`·`noinline` 람다의 맨 `return` 도 **같은 문구**인 것 | `kotlinc` (컴파일 실패가 결과) |

**구현 의존 항목** — `javap` 의 명령 이름·상수 풀 번호, 인라인 전개가 남기는 `iconst_0 / istore_N` 표식,
`caller$lambda$N` 이라는 합성 메서드 이름과 그 번호, `CrossKt$caller$$inlined$guard$1` 이라는 클래스 이름,
비지역 `return` 이 `areturn` 으로·라벨 반환이 `goto` 로 박히는 것, 코드 크기 수치 —
**전부 이 컴파일러 버전 + 기본 타깃(1.8) + 이 머신의 산출물**이다.\
반면 **「비지역 `return` 이 된다/안 된다」·「`noinline` 이 있어야 값으로 다룬다」·「`crossinline` 이 필요한 자리」·
「nullable 인라인 파라미터 금지」·「재귀 금지」·「공개 API 가시성 제약」** 은 **언어 규칙**이라 타깃과 무관하다.

**★ 던져 봤더니 예상과 달랐던 것 — 세 건**

1. ★★ **「`inline` 은 호출 비용을 줄이는 것」이 틀렸다.** 컴파일러가 직접
   `expected performance impact from inlining is insignificant.` 라고 말한다.
   게다가 기준이 「함수 타입 파라미터가 있나」가 아니라 「**펼칠 수 있는 람다가 있나**」였다 —
   `noinline` 뿐인 함수도 **같은 경고**를 받는다.
2. ★★ **`crossinline` 이 객체를 안 만들 거라고 본 것이 틀렸다.** 펼치기는 하는데
   **호출 자리마다 클래스가 하나씩 생긴다**(`CrossKt$caller$$inlined$guard$1`).
   선언당 하나가 아니라 **자리당 하나**다.
3. ★ **`internal inline` 도 막힐 줄 알았는데 안 막혔다.** 같은 `private` 함수를 부르는데
   **공개 API 쪽만** 에러였다 — 기준은 「인라인인가」가 아니라 「**공개인가**」였다.

**안 걸린 것도 출력이다** — 같은 선언들에 nullable 인라인 파라미터 에러를 하나 섞었더니
**1번의 경고 두 줄이 통째로 사라졌다**(`warn.kt` 에서 경고 0줄).
**「경고가 안 나왔다」가 「경고할 것이 없다」를 뜻하지 않는다** — 경고를 근거로 쓰려면
**에러 시나리오와 갈라서 던져야 한다.**
