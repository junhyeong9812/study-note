# kotlin/syntax/36 — 함수 타입·`fun interface`·SAM 변환 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Functional (SAM) interfaces](https://kotlinlang.org/docs/fun-interfaces.html)(「An interface with only one abstract member function is called a functional interface, or a Single Abstract Method (SAM) interface」 · SAM 변환 · 「You can also use SAM conversions for Java interfaces」 · 함수 타입 별칭과의 비교표) · [Java interop — SAM conversions](https://kotlinlang.org/docs/java-interop.html#sam-conversions).
> **실행 검증** — 이 문서의 모든 출력·에러·경고·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javac`·`java`·`javap` 에서 실제로 얻었다.\
> `kotlinc` 14회(`-X` 도움말 1회 · 실패 4벌 — 격자 2벌 포함) · `javac` 3회 · `java` 5회 · `javap` 2회 + 격자 스크립트 안에서 4회.\
> ★★ 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다. 격자 두 장의 「N / M」은 **스크립트가 세어 마지막 줄로 찍었다.**
> ⚠️ **바이트코드는 기본 `-jvm-target`(1.8)** 이다. ★★★ **람다를 무엇으로 내리나는 클래스 파일 개수로 가르지 않았다** — Kotlin 2.x 는 `invokedynamic` 이 기본이라 개수가 말해 주지 않는다([14번 주제](../14-scope-functions/) (6)). **`javap -c` 의 명령과 그 명령이 만드는 타입**으로 갈랐다.
> **버전** — 함수 타입·람다·Java 인터페이스 SAM 변환은 1.0. **`fun interface` 는 1.4.** 기본 람다 전략 `indy` 는 **언어 판 2.0+**(`-X` 도움말) — ★ 이 판은 `-language-version 1.9` 이하를 **거부**하므로 그 경계는 **못 잰 것**이다((6)).
> **경계** — ★★ **`(Int) -> Int` 가 `Function1` 이라는 것 · 22 → `FunctionN` · 람다가 `invokedynamic` 이 되는 것 · SAM 변환이 박싱을 없애는 자리**는 [10번 주제](../10-lambdas-and-higher-order-functions/) (1)(2)(7)이 정본이다 — 여기서는 **다시 재지 않고 인용**한다.\
> `a(x)` 가 `a.invoke(x)` 로 풀리는 규약은 [31번 주제](../31-operator-overloading-infix-and-invoke/)가, 수신자 있는 함수 타입(`A.() -> Unit`)은 [목록의 **37번 주제**](../37-lambdas-with-receiver-and-type-safe-builders/)가, `suspend` 함수 타입의 의미는 코루틴 주제가 정본이다 — `suspend` 는 **서명 한 줄만** 경계로 본다((7)).\
> **Java 쪽 짝** — [`../../../java/syntax/31-functional-interfaces/`](../../../java/syntax/31-functional-interfaces/)(함수형 인터페이스 지도) · [`../../../java/syntax/29-lambda-expressions/`](../../../java/syntax/29-lambda-expressions/)(Java 람다의 `invokedynamic`).
> 이 본문은 Claude 작성이다(원고 없음).

★★★ **본체는 둘째 창이다** — 「**세 인터페이스 × 일곱 가지 넘기는 법, 컴파일이 되나**」(21칸 격자). SAM 변환은 **실행이 아니라 컴파일러가 람다를 받아 주느냐**로 갈린다. 셋째 창(`javap -c`)이 받아 준 람다가 **무엇이 됐나**를, 넷째 창(판 격자)이 그것을 **어느 플래그가 움직이나**를 본다.

## 이 주제가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **언어 보장** | 명세·공식 문서가 약속한 것 | ★★★ 함수 타입은 `FunctionN` · **SAM 변환은 Java 인터페이스와 `fun interface` 에만** · `fun interface` 는 **추상 멤버 함수가 정확히 하나** |
| **구현(JVM 백엔드)** | kotlinc 가 JVM 으로 내리는 방식 | ★★ 람다 → **`invokedynamic` + `LambdaMetafactory`** 또는 **클래스** · ★ 그 선택이 **플래그 둘**(`-Xlambdas`·`-Xsam-conversions`)로 **따로** 움직이는 것 · `suspend` 가 `Continuation` 매개변수 하나를 더하는 것 |
| **이 판의 관찰** | kotlinc 2.4.20 에서 이번에 본 것 | 진단 문구(「`() -> ??? (Unknown lambda return type)`」) · 격자의 통과 목록 · `-X` 도움말 |

## 이 판

```text
===== kotlinc -version =====
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
(exit 0)
```

```text
===== javac -version =====
javac 21.0.5
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | (이 주제에는 없다) | 람다 객체의 `toString()`·런타임 클래스 이름(`…$$Lambda/0x…`)을 **안 찍었다** — 그것은 실행마다 바뀐다([10번 주제](../10-lambdas-and-higher-order-functions/) (4)) |
| 안 흔들린다 | `javap -c` 출력 · 격자 스크립트가 뽑은 **명령 종류와 대상 타입** | 같은 소스·같은 판이면 같다 |
| 안 흔들린다 | 진단 문구·`파일:줄:칸` · 「compiled N / 21」·「differ N / 12」 | 결정적이다 |

★ 근거 — 캡처 스크립트를 처음부터 두 번 돌려 **블록 전체를 바이트 단위로 대조**했다(수치는 3-answer 의 「실행 검증」).

## 한눈에 — 쉽게 말하면

**함수 타입 `(Int) -> Int` 는 「누구나 끼울 수 있는 표준 콘센트」다. 인터페이스는 「그 가게 전용 콘센트」다.**
람다는 표준 플러그라서 표준 콘센트에는 그냥 들어간다. 전용 콘센트에 끼우려면 **어댑터**(SAM 변환)가 필요한데, Kotlin 컴파일러는 **어댑터를 두 종류의 전용 콘센트에만** 만들어 준다 — **Java 가 만든 것**(단일 추상 메서드 인터페이스)과 **`fun` 도장이 찍힌 Kotlin 것**(`fun interface`).
**도장 없는 Kotlin 인터페이스에는 어댑터가 없다** — 모양이 맞아도 안 들어간다. 그런데 **Java 쪽 컴파일러는 그 도장을 모른다** — Java 에게는 추상 메서드 하나짜리 인터페이스면 전부 전용 콘센트다.

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 표준 콘센트 | 함수 타입 `(Int) -> Int` = `Function1` | (3) · [10번 주제](../10-lambdas-and-higher-order-functions/) (1) |
| 전용 콘센트 | 단일 추상 메서드 인터페이스 | (1) |
| 어댑터 | SAM 변환 | (1)(2) |
| `fun` 도장 | `fun interface` — 1.4 | (1)(5) |
| 도장 없는 전용 콘센트 | 일반 Kotlin 인터페이스 — Kotlin 에서는 **0 / 7** | (1) |
| 도장을 모르는 다른 나라 전기공 | Java 컴파일러 — Kotlin 일반 인터페이스에도 람다를 넣는다 | (2) |
| 어댑터를 공장에서 찍나, 현장에서 만드나 | `-Xsam-conversions=class` / `indy` | (4) |

```text
                             Kotlin 소스에서 람다를 넘기면        Java 소스에서 람다를 넘기면
   JSam   (Java 인터페이스)     ok  — SAM 변환                     ok
   KPlain (Kotlin interface)   ERROR — 「… but 'KPlain' was expected」  ok ★ (javac 는 fun 도장을 안 본다)
   KFun   (fun interface)      ok  — SAM 변환                     ok
   (Int) -> Int                ok  — 그냥 Function1               ok — Function1 을 구현하는 람다
```

## 이 주제가 답하려는 질문

1. 람다를 **어떤 인터페이스에 어떤 모양으로** 넘기면 컴파일되나 — Java 인터페이스 · Kotlin 일반 인터페이스 · `fun interface` × 넘기는 법 일곱.
2. 받아 준 람다는 **JVM 에서 무엇이 되나** — `invokedynamic` 이 **무슨 타입**을 만드나, 그리고 그것을 **어느 플래그**가 바꾸나.
3. 함수 타입과 `fun interface` 는 **언제 무엇**을 고르나 — `fun interface` 로 선언할 수 없는 것은.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **SAM 격자 — 21칸 컴파일** | 어느 인터페이스 × 어느 넘기는 법이 **받아지나**((1)) — 「compiled N / 21」을 스크립트가 센다 | ★ **본체 창** · 규칙 18-A |
| ★★ **Java 에서 던지기** | 같은 인터페이스를 **Java 컴파일러**가 어떻게 받나((2)) | [25번 주제](../25-object-declaration-companion-and-object-expression/)의 창 |
| ★★ **`javap -c` — 첫 명령과 만드는 타입** | `invokedynamic … ()LJSam;` 처럼 **무엇을 만드나**((3)) | 이 갈래의 기본 창 |
| ★★★ **판 격자 — `-Xlambdas` × `-Xsam-conversions`** | 12칸 중 몇 칸이 움직이나((4)) | 규칙 24 |
| ★ **진단 문구** | `fun interface` 의 제약((5)) | 이 갈래의 기본 창 |
| **부적용 — 실행 시간** | 「`invokedynamic` 이 빠르다」·「클래스가 느리다」는 **재지 않았다** — 명령 **종류**만 본다 | — |
| **부적용 — 클래스 파일 개수** | ★ 개수로 전략을 가르지 않는다(머리말) | [14번 주제](../14-scope-functions/) (6) |

### (1) ★★★ SAM 격자 — 세 인터페이스 × 일곱 가지 넘기는 법

**언제 쓰나** — 「이 콜백에 람다를 그냥 넘겨도 되나」를 판단할 때.

```java
// JSam.java
@FunctionalInterface
public interface JSam {
    int apply(int x);
}
```

```kotlin
// ifaces.kt
interface KPlain { fun apply(x: Int): Int }
fun interface KFun { fun apply(x: Int): Int }

fun takeJ(f: JSam): Int = f.apply(10)
fun takeK(f: KPlain): Int = f.apply(10)
fun takeF(f: KFun): Int = f.apply(10)
fun inc(x: Int): Int = x + 1
```

```java
// JHost.java
public class JHost {
    public static int useJ(JSam f) { return f.apply(10); }
    public static int useK(KPlain f) { return f.apply(10); }
    public static int useF(KFun f) { return f.apply(10); }
}
```

```kotlin
// samgrid.kt
val g: (Int) -> Int = { it + 1 }

fun j1() = takeJ { it + 1 }
fun j2() = JHost.useJ { it + 1 }
fun j3() = takeJ(JSam { it + 1 })
fun j4() = takeJ(g)
fun j5() = JHost.useJ(g)
fun j6() = takeJ(::inc)
fun j7() { val x: JSam = { it: Int -> it + 1 } }

fun k1() = takeK { it + 1 }
fun k2() = JHost.useK { it + 1 }
fun k3() = takeK(KPlain { it + 1 })
fun k4() = takeK(g)
fun k5() = JHost.useK(g)
fun k6() = takeK(::inc)
fun k7() { val x: KPlain = { it: Int -> it + 1 } }

fun f1() = takeF { it + 1 }
fun f2() = JHost.useF { it + 1 }
fun f3() = takeF(KFun { it + 1 })
fun f4() = takeF(g)
fun f5() = JHost.useF(g)
fun f6() = takeF(::inc)
fun f7() { val x: KFun = { it: Int -> it + 1 } }
```

```text
===== javac -d o36 JSam.java =====
(exit 0)
===== kotlinc -cp o36 ifaces.kt -d o36 =====
(exit 0)
===== javac -cp o36 -d o36 JHost.java =====
(exit 0)
```

```text
===== kotlinc -cp o36 samgrid.kt -d o36g2 | python3 samgrid36.py samgrid.kt =====
j1  ok
j2  ok
j3  ok
j4  ok
j5  ok
j6  ok
j7  ok
k1  ERROR  argument type mismatch: actual type is '() -> ??? (Unknown lambda return type)', but 'KPlain' was expected.
k2  ERROR  argument type mismatch: actual type is '() -> ??? (Unknown lambda return type)', but 'KPlain!' was expected.
k3  ERROR  interface 'interface KPlain : Any' does not have constructors.
k4  ERROR  argument type mismatch: actual type is '(Int) -> Int', but 'KPlain' was expected.
k5  ERROR  argument type mismatch: actual type is '(Int) -> Int', but 'KPlain!' was expected.
k6  ERROR  inapplicable candidate(s): fun inc(x: Int): Int
k7  ERROR  initializer type mismatch: expected 'KPlain', actual '(Int) -> Int'.
f1  ok
f2  ok
f3  ok
f4  ok
f5  ok
f6  ok
f7  ok
compiled: 14 / 21
(exit 1)
```

```python
# samgrid36.py
import re
import sys

src = open(sys.argv[1]).read().splitlines()
names = {}
for i, line in enumerate(src, 1):
    m = re.match(r"fun (\w+)\(\)", line)
    if m:
        names[i] = m.group(1)

first_error = {}
for line in sys.stdin:
    m = re.match(r"samgrid\.kt:(\d+):\d+: error: (.*)", line.rstrip("\n"))
    if m and int(m.group(1)) in names:
        first_error.setdefault(names[int(m.group(1))], m.group(2))

ok = 0
for i in sorted(names):
    n = names[i]
    if n in first_error:
        print(f"{n}  ERROR  {first_error[n]}")
    else:
        ok += 1
        print(f"{n}  ok")
print(f"compiled: {ok} / {len(names)}")
```

| 넘기는 법 | `JSam`(Java) | `KPlain`(Kotlin `interface`) | `KFun`(`fun interface`) |
|---|---|---|---|
| 1 Kotlin 함수에 람다 | ok | ★ **ERROR** | ok |
| 2 Java 메서드에 람다 | ok | ★ **ERROR** | ok |
| 3 SAM 생성자 `I { … }` | ok | ★ **ERROR** — 「`does not have constructors`」 | ok |
| 4 함수 타입 **값**을 Kotlin 함수에 | ok | ERROR | ok |
| 5 함수 타입 값을 Java 메서드에 | ok | ERROR | ok |
| 6 함수 참조 `::inc` | ok | ERROR | ok |
| 7 변수 초기화 `val x: I = { … }` | ★ ok | ERROR | ★ ok |

- ★★★ **compiled 14 / 21 — 막힌 7칸이 전부 `KPlain` 줄이다.** 도장 없는 Kotlin 인터페이스에는 **어느 모양으로도** 람다가 안 들어간다. SAM 변환은 **Java 인터페이스와 `fun interface` 에만** 걸린다.
- ★★ **`k2` 도 막혔다** — Java 메서드 `JHost.useK(KPlain)` 에 넘겨도 안 된다(「`… but 'KPlain!' was expected.`」의 `!` 는 Java 에서 온 플랫폼 타입 표시). **변환 여부는 받는 메서드가 아니라 인터페이스의 출신**이 정한다.
- ★★ **4·5·6 도 통과했다**(`JSam`·`KFun`) — 람다 **리터럴**만이 아니라 **함수 타입 값**(`g`)과 **함수 참조**도 SAM 으로 변환된다. `viaValue` 의 바이트코드가 그 어댑터다((3)).
- ★★ **7 이 통과했다** — 인자 자리가 아니라 **기대 타입이 SAM 인 자리**면 변환이 걸린다. `k7` 은 같은 모양으로 「`initializer type mismatch: expected 'KPlain', actual '(Int) -> Int'.`」
- ★ `k1`·`k2` 의 문구는 「`() -> ??? (Unknown lambda return type)`」 — **기대 타입에서 매개변수 수를 못 얻어** 람다를 `it` 없는 0인자로 읽었다(그래서 뒤이어 「`unresolved reference 'it'`」). 원인은 첫 줄이다.

### (2) ★★ 반대 방향 — Java 가 Kotlin 인터페이스에 람다를 넘기면

```kotlin
// fnid.kt
fun applyFn(f: (Int) -> Int): Int = f(10)

fun main() {
    val f: (Int) -> Int = { it + 1 }
    val k: KFun = KFun { it + 1 }
    println("A ${f is Function1<*, *>} ${f is Function<*>}")
    println("B ${(k as Any) is Function1<*, *>} ${(k as Any) is Function<*>}")
    println("C ${f.invoke(1)} ${f(1)}")
    println("D ${applyFn(k::apply)}")
}
```

```java
// JCall.java
import kotlin.Unit;

public class JCall {
    public static void main(String[] args) {
        System.out.println("A " + IfacesKt.takeK(x -> x * 2));
        System.out.println("B " + IfacesKt.takeF(x -> x * 3));
        System.out.println("C " + FnidKt.applyFn(x -> x * 4));
    }
}
```

```text
===== kotlinc -cp o36 fnid.kt -d o36f =====
fnid.kt:6:18: warning: check for instance is always 'true'.
    println("A ${f is Function1<*, *>} ${f is Function<*>}")
                 ^^^^^^^^^^^^^^^^^^^^
fnid.kt:6:42: warning: check for instance is always 'true'.
    println("A ${f is Function1<*, *>} ${f is Function<*>}")
                                         ^^^^^^^^^^^^^^^^
(exit 0)
===== java -cp o36f:o36:kotlin-stdlib.jar FnidKt =====
A true true
B false false
C 2 2
D 11
(exit 0)
===== javac -cp o36f:o36:kotlin-stdlib.jar -d o36f JCall.java =====
(exit 0)
===== java -cp o36f:o36:kotlin-stdlib.jar JCall =====
A 20
B 30
C 40
(exit 0)
```

- ★★★ **`JCall` 의 `A 20` — Java 는 `KPlain` 에 람다를 넘겼다.** (1)에서 Kotlin 이 **일곱 모양 전부 막힌** 그 인터페이스다. Java 의 규칙은 「추상 메서드 하나짜리 인터페이스면 함수형 인터페이스」이고, **`fun` 도장은 Kotlin 컴파일러만** 읽는다.
- ★★ **`C 40`** — Java 에게 Kotlin 함수 타입 `(Int) -> Int` 는 **`Function1` 이라는 평범한 인터페이스**라 Java 람다가 그것을 구현한다. `x -> x * 4` 가 `Function1<Integer, Integer>` 가 됐다([10번 주제](../10-lambdas-and-higher-order-functions/) (1)).
- ★★ **`A true true` · `B false false`** — 함수 타입 값은 `Function1` 이자 `Function` 이고, **`fun interface` 인스턴스는 둘 다 아니다.** `fun interface` 는 함수 타입의 별명이 아니라 **새 타입**이다. 컴파일러가 `A` 에 「`check for instance is always 'true'.`」 경고를 붙인 것도 같은 사실의 정적 판이다.
- ★ **`C 2 2`** — `f(1)` 과 `f.invoke(1)` 은 같다. `invoke` 규약이 `Function1.invoke` 를 연산자로 만든다([31번 주제](../31-operator-overloading-infix-and-invoke/)). **`D 11`** — `k::apply` 로 `fun interface` 를 **함수 타입으로 되돌릴** 수 있다.

### (3) ★★ 받아 준 람다는 무엇이 되나 — `javap -c`

```kotlin
// lam36.kt
fun viaFn(): Int {
    val f: (Int) -> Int = { it + 1 }
    return f(10)
}
fun viaJava(): Int = takeJ { it + 2 }
fun viaFunIface(): Int = takeF { it + 3 }
fun viaValue(): Int {
    val f: (Int) -> Int = { it + 4 }
    return takeJ(f)
}

fun main() {
    println("A ${viaFn()} ${viaJava()} ${viaFunIface()} ${viaValue()}")
}
```

```text
===== kotlinc -cp o36 lam36.kt -d o36d =====
(exit 0)
===== java -cp o36d:o36:kotlin-stdlib.jar Lam36Kt =====
A 11 12 13 14
(exit 0)
===== javap -c -p o36d/Lam36Kt.class | awk '/ (viaFn|viaJava|viaFunIface|viaValue)\(\);/,/^$/' =====
  public static final int viaFn();
    Code:
       0: invokedynamic #26,  0             // InvokeDynamic #0:invoke:()Lkotlin/jvm/functions/Function1;
       5: astore_0
       6: aload_0
       7: bipush        10
       9: invokestatic  #32                 // Method java/lang/Integer.valueOf:(I)Ljava/lang/Integer;
      12: invokeinterface #36,  2           // InterfaceMethod kotlin/jvm/functions/Function1.invoke:(Ljava/lang/Object;)Ljava/lang/Object;
      17: checkcast     #38                 // class java/lang/Number
      20: invokevirtual #41                 // Method java/lang/Number.intValue:()I
      23: ireturn

  public static final int viaJava();
    Code:
       0: invokedynamic #53,  0             // InvokeDynamic #1:apply:()LJSam;
       5: invokestatic  #59                 // Method IfacesKt.takeJ:(LJSam;)I
       8: ireturn

  public static final int viaFunIface();
    Code:
       0: invokedynamic #67,  0             // InvokeDynamic #2:apply:()LKFun;
       5: invokestatic  #71                 // Method IfacesKt.takeF:(LKFun;)I
       8: ireturn

  public static final int viaValue();
    Code:
       0: invokedynamic #77,  0             // InvokeDynamic #3:invoke:()Lkotlin/jvm/functions/Function1;
       5: astore_0
       6: aload_0
       7: invokedynamic #85,  0             // InvokeDynamic #4:apply:(Lkotlin/jvm/functions/Function1;)LJSam;
      12: invokestatic  #59                 // Method IfacesKt.takeJ:(LJSam;)I
      15: ireturn
(exit 0)
```

- ★★★ **네 함수 전부 `invokedynamic` 으로 시작한다** — 차이는 **만드는 타입**이다: `viaFn` → `()Lkotlin/jvm/functions/Function1;` · `viaJava` → `()LJSam;` · `viaFunIface` → `()LKFun;`. SAM 변환된 람다는 **`Function1` 을 거치지 않고 바로 그 인터페이스**가 된다.
- ★★ **`viaValue` 에는 `invokedynamic` 이 둘이다** — `#3` 이 람다를 `Function1` 으로 만들고, `#4` 가 그 `Function1` 을 받아 **`JSam` 으로 감싼다**(`(Lkotlin/jvm/functions/Function1;)LJSam;`). 함수 타입 **값**의 SAM 변환은 **어댑터 객체 하나를 더** 만든다.
- ★ `viaFn` 의 `Integer.valueOf` → `Function1.invoke` → `checkcast Number` → `intValue` 는 [10번 주제](../10-lambdas-and-higher-order-functions/) (7)이 본 박싱 경계 그대로다. `JSam`/`KFun` 쪽은 `apply:(I)I` 라 박싱이 없다.

### (4) ★★★ 판 격자 — 플래그 둘이 **따로** 움직인다

```text
===== kotlinc -X | awk '/^  -Xlambdas=/{f=5} /^  -Xsam-conversions=/{f=4} f-->0' =====
  -Xlambdas={class|indy}     Select the code generation scheme for lambdas.
                             -Xlambdas=indy                  Generate lambdas using 'invokedynamic' with 'LambdaMetafactory.metafactory'.
                                                             A lambda object created using 'LambdaMetafactory.metafactory' will have a different 'toString()'.
                             -Xlambdas=class                 Generate lambdas as explicit classes.
                             The default value is 'indy' if language version is 2.0+, and 'class' otherwise.
  -Xsam-conversions={class|indy} Select the code generation scheme for SAM conversions.
                             -Xsam-conversions=indy          Generate SAM conversions using 'invokedynamic' with 'LambdaMetafactory.metafactory'.
                             -Xsam-conversions=class         Generate SAM conversions as explicit classes.
                             The default value is 'indy'.
(exit 0)
```

```python
# lamgrid36.py
import re
import subprocess
import sys

FUNS = ["viaFn", "viaJava", "viaFunIface", "viaValue"]


def kinds(d):
    out = subprocess.run(["javap", "-c", "-p", d + "/Lam36Kt.class"],
                         capture_output=True, text=True, check=True).stdout
    found, cur = {}, None
    for line in out.splitlines():
        m = re.match(r"  public static final int (\w+)\(\);", line)
        if m:
            cur = m.group(1)
            found[cur] = []
            continue
        if not line.strip():
            cur = None
        if cur is None:
            continue
        m = re.search(r"invokedynamic .*\)L([\w/$]+);", line)
        if m:
            found[cur].append("indy->" + m.group(1).split("/")[-1])
        m = re.search(r"(?:getstatic|new) .*(?:class |Field )(Lam36Kt\$[\w$]+)", line)
        if m:
            found[cur].append("class " + m.group(1))
    return {f: "+".join(found[f]) for f in FUNS}


dirs = sys.argv[1:]
grid = [kinds(d) for d in dirs]
for i, d in enumerate(dirs):
    print(f"== {d}")
    for f in FUNS:
        print(f"  {f:<12} {grid[i][f]}")
diff = sum(1 for g in grid[1:] for f in FUNS if g[f] != grid[0][f])
print(f"cells that differ from {dirs[0]}: {diff} / {len(FUNS) * (len(dirs) - 1)}")
```

```text
===== kotlinc -Xlambdas=class -cp o36 lam36.kt -d o36l =====
(exit 0)
===== kotlinc -Xsam-conversions=class -cp o36 lam36.kt -d o36s =====
(exit 0)
===== kotlinc -Xlambdas=class -Xsam-conversions=class -cp o36 lam36.kt -d o36b2 =====
(exit 0)
===== java -cp o36b2:o36:kotlin-stdlib.jar Lam36Kt =====
A 11 12 13 14
(exit 0)
===== python3 lamgrid36.py o36d o36l o36s o36b2 =====
== o36d
  viaFn        indy->Function1
  viaJava      indy->JSam
  viaFunIface  indy->KFun
  viaValue     indy->Function1+indy->JSam
== o36l
  viaFn        class Lam36Kt$viaFn$f$1
  viaJava      indy->JSam
  viaFunIface  indy->KFun
  viaValue     class Lam36Kt$viaValue$f$1+indy->JSam
== o36s
  viaFn        indy->Function1
  viaJava      class Lam36Kt$viaJava$1
  viaFunIface  class Lam36Kt$viaFunIface$1
  viaValue     indy->Function1+class Lam36Kt$sam$JSam$0
== o36b2
  viaFn        class Lam36Kt$viaFn$f$1
  viaJava      class Lam36Kt$viaJava$1
  viaFunIface  class Lam36Kt$viaFunIface$1
  viaValue     class Lam36Kt$viaValue$f$1+class Lam36Kt$sam$JSam$0
cells that differ from o36d: 9 / 12
(exit 0)
```

```text
   람다가 무엇으로 받아지나                    어느 플래그가 정하나
   (Int) -> Int 로 받는 람다          ─────>   -Xlambdas           indy(기본) | class
   JSam · KFun 으로 받는 람다         ─────>   -Xsam-conversions   indy(기본) | class
   (Int) -> Int 값을 JSam 자리에      ─────>   두 조각 — 람다 조각은 -Xlambdas, 감싸는 조각은 -Xsam-conversions
```

| 함수 | 기본 | `-Xlambdas=class` | `-Xsam-conversions=class` | 둘 다 |
|---|---|---|---|---|
| `viaFn`(함수 타입 람다) | indy | ★ **class** | indy | class |
| `viaJava`(Java SAM) | indy | ★ **indy 그대로** | ★ **class** | class |
| `viaFunIface`(`fun interface`) | indy | indy 그대로 | class | class |
| `viaValue`(값 → SAM) | indy + indy | **class** + indy | indy + **class** | class + class |

- ★★★ **differ 9 / 12.** `-Xlambdas` 는 **함수 타입 람다**만, `-Xsam-conversions` 는 **SAM 변환**만 움직인다. `-Xlambdas=class` 를 줘도 `viaJava` 는 `indy->JSam` 그대로다 — 「람다를 클래스로」라는 옵션이 **SAM 람다에는 안 걸린다.**
- ★★ **`viaValue` 는 두 조각이 각각 다른 플래그를 따른다** — 람다 조각(`$viaValue$f$1`)은 `-Xlambdas`, 어댑터 조각(`$sam$JSam$0`)은 `-Xsam-conversions`.
- ★ **클래스 이름에서 출신이 보인다** — `Lam36Kt$viaJava$1`(람다 자체가 SAM 구현) 대 `Lam36Kt$sam$JSam$0`(함수 타입 값을 감싼 어댑터).
- ★ **`A 11 12 13 14`** — 네 판 모두 **값은 같다.** 전략은 **관찰 가능한 결과를 안 바꾼다**(바뀌는 것은 람다 객체의 `toString()` — 도움말이 스스로 적는다).

### (5) ★ `fun interface` 로 선언할 수 없는 것

```kotlin
// funbad.kt
fun interface Two { fun a(); fun b() }
fun interface Zero
fun interface WithProp { val p: Int; fun a() }
fun interface Gen { fun <T> a(x: T): T }
fun interface Ok { fun a(x: Int): Int; fun b(): Int = 0 }
```

```text
===== kotlinc funbad.kt -d o36b =====
funbad.kt:1:1: error: functional interface must have exactly one abstract function.
fun interface Two { fun a(); fun b() }
^^^
funbad.kt:2:1: error: functional interface must have exactly one abstract function.
fun interface Zero
^^^
funbad.kt:3:26: error: functional interface cannot have abstract properties.
fun interface WithProp { val p: Int; fun a() }
                         ^^^
funbad.kt:4:25: error: functional interface cannot have an abstract method with type parameters.
fun interface Gen { fun <T> a(x: T): T }
                        ^^^
(exit 1)
```

- ★★ **막힌 넷 · 통과 하나(`Ok`)**. 「`exactly one abstract function`」이 **추상 멤버 둘**(`Two`)과 **영**(`Zero`)을 같은 문구로 막는다.
- ★★ **추상 프로퍼티**(`WithProp`)와 **제네릭 추상 메서드**(`Gen`)도 안 된다 — 람다는 **타입 매개변수를 가질 수 없고**, 프로퍼티는 람다 하나로 구현할 수 없기 때문이다.
- ★ **`Ok`** — 기본 구현이 있는 멤버(`fun b(): Int = 0`)는 **몇 개든** 된다. 세는 것은 **추상** 멤버다.

### (6) ★ 판 경계 — 못 잰 것

```text
===== kotlinc -language-version 1.9 funbad.kt -d o36lv =====
error: language version 1.9 is no longer supported; use version 2.0 or greater instead.
(exit 1)
===== kotlinc -language-version 2.0 susp36.kt -d o36lv2 =====
warning: language version 2.0 is deprecated and its support will be removed in a future version of Kotlin. Update the version to 2.2.
(exit 0)
```

- ★★ **`-language-version 1.9` 는 「`is no longer supported; use version 2.0 or greater`」로 거부**된다. 그래서 **`fun interface` 의 1.4 경계**도, **`-Xlambdas` 의 「2.0 미만이면 `class`」** 도 이 판에서는 **못 잰 것**이다(규칙 3 — 제3의 상태). 판 경계는 문서와 도움말을 근거로 적는다.
- ★ `2.0` 은 받되 「`deprecated`」 경고가 붙는다 — 이 판이 재현할 수 있는 가장 오래된 언어 판이다.

### (7) ★ 경계 — `suspend` 함수 타입의 서명 한 줄

```kotlin
// susp36.kt
fun plainType(f: (Int) -> Int) {}
fun suspendType(f: suspend (Int) -> Int) {}
```

```text
===== kotlinc susp36.kt -d o36p =====
(exit 0)
===== javap -s -p o36p/Susp36Kt.class =====
Compiled from "susp36.kt"
public final class Susp36Kt {
  public static final void plainType(kotlin.jvm.functions.Function1<? super java.lang.Integer, java.lang.Integer>);
    descriptor: (Lkotlin/jvm/functions/Function1;)V

  public static final void suspendType(kotlin.jvm.functions.Function2<? super java.lang.Integer, ? super kotlin.coroutines.Continuation<? super java.lang.Integer>, ? extends java.lang.Object>);
    descriptor: (Lkotlin/jvm/functions/Function2;)V
}
(exit 0)
```

- ★★ **`suspend (Int) -> Int` 는 `Function2<Integer, Continuation<? super Integer>, Object>`** 다 — 매개변수가 **하나 늘고**(`Continuation`) 반환이 **`Object`** 가 된다. 같은 모양의 일반 함수 타입은 `Function1` 이다.
- ★ 그 `Continuation`·`Object` 반환이 **무엇을 위한 것인지**는 코루틴 주제가 정본이다 — 여기서는 「`suspend` 가 붙으면 **다른 `FunctionN`** 이 된다」까지만 본다.

## 문법 — 형태와 규칙

**형태** — `fun interface` 선언 · SAM 생성자 · 인자 자리의 람다 · Java `Runnable` · 함수 참조 값이 한 프로그램에서 도는 최소 예제다.

```kotlin
// form36.kt
fun interface Rule { fun ok(s: String): Boolean }

fun check(s: String, r: Rule): Boolean = r.ok(s)

fun main() {
    val notEmpty = Rule { it.isNotEmpty() }
    println("A ${check("x", notEmpty)} ${check("", { it.isNotEmpty() })}")
    val t = Thread { println("B from a Runnable lambda") }
    t.start()
    t.join()
    val f: (String) -> Boolean = String::isNotEmpty
    println("C ${check("y", f)}")
}
```

```text
===== kotlinc form36.kt -d o36z =====
(exit 0)
===== java -cp o36z:kotlin-stdlib.jar Form36Kt =====
A true false
B from a Runnable lambda
C true
(exit 0)
```

**규칙 불릿**

- 함수 타입 `(A) -> B` 는 `FunctionN` 인터페이스 — 람다·함수 참조·익명 함수가 그 값이다([10번 주제](../10-lambdas-and-higher-order-functions/)).
- **SAM 변환**은 **Java 인터페이스**와 **`fun interface`** 에만 — 일반 Kotlin 인터페이스는 **`object : I { … }`** 로 구현한다((1)).
- 변환은 **기대 타입이 SAM 인 자리** 어디서나 — 인자·SAM 생성자·변수 초기화((1)).
- 람다 리터럴뿐 아니라 **함수 타입 값·함수 참조**도 변환된다 — 값은 **어댑터 객체**가 하나 더 생긴다((1)(3)).
- `fun interface` 는 **추상 멤버 함수 정확히 하나** · 추상 프로퍼티·제네릭 추상 메서드 금지((5)).
- `fun interface` 인스턴스는 **`Function1` 이 아니다** — 필요하면 `x::apply` 로 되돌린다((2)).

## 어디서 틀리나

1. ★★★ **Kotlin `interface` 하나짜리에 람다를 넘긴다.** 「`… but 'KPlain' was expected`」 — `fun` 을 붙여라((1)).
2. ★★ **「Java 메서드에 넘기면 되겠지」.** 인터페이스가 Kotlin 출신이면 Java 메서드 인자여도 막힌다((1) `k2`).
3. ★★ **Java 에서 되니까 Kotlin 에서도 된다고 믿는다.** Java 는 `fun` 도장을 안 본다((2)) — 라이브러리 작성자는 **Kotlin 사용자 쪽**을 따로 확인해야 한다.
4. ★★ **`-Xlambdas=class` 로 모든 람다가 클래스가 된다고 믿는다.** SAM 람다는 **`-Xsam-conversions`** 가 따로 정한다((4)).
5. ★★ **클래스 파일 개수로 람다 전략·인라인 여부를 가른다.** 기본이 `invokedynamic` 이라 개수는 말해 주지 않는다 — **명령**을 봐라((3)).
6. ★ **`fun interface` 를 함수 타입의 별명으로 여긴다.** `is Function1` 이 `false` 다((2)).
7. ★ **함수 타입 값을 SAM 에 넘기면 공짜라고 믿는다.** 어댑터 `invokedynamic` 이 하나 더 있다((3)) — 비용은 **재지 않았다.**

## 구현 세부사항 대 언어 보장

| 항목 | 어느 쪽인가 | 근거 |
|---|---|---|
| 함수 타입이 `FunctionN` | ★★★ **언어 보장**(stdlib 타입) | [10번 주제](../10-lambdas-and-higher-order-functions/) (1) · (2) |
| SAM 변환이 Java 인터페이스·`fun interface` 에만 | ★★★ **언어 보장** | 문서 · (1) |
| `fun interface` 의 제약(추상 함수 하나 등) | **언어 보장** | (5) |
| `fun interface` 인스턴스가 `Function1` 이 아닌 것 | **언어 보장**(새 타입) | 문서의 비교표 · (2) |
| Java 가 Kotlin 일반 인터페이스에 람다를 넣는 것 | ★★ **Java 언어의 규칙** — Kotlin 이 아니다 | (2) |
| 람다 → `invokedynamic` + `LambdaMetafactory` | ★★ **JVM 백엔드의 구현**(기본값) | (3) |
| ★★ 그 전략이 **`-Xlambdas`·`-Xsam-conversions` 로 따로** 바뀌는 것 | ★★ **이 컴파일러의 옵션** | (4) — `9 / 12` |
| 함수 타입 값의 SAM 변환이 **어댑터 하나를 더** 만드는 것 | ★ **JVM 백엔드의 구현** | (3) |
| `suspend` 가 `Continuation` 매개변수를 더하는 것 | ★ **JVM 백엔드의 구현**(CPS 변환) | (7) |
| 진단 문구 · 합성 클래스 이름(`$sam$JSam$0`) | **이 판의 산출물** | (1)(4) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 콜백 하나 — 이름·계약이 따로 필요 없다 | ★ 함수 타입 `(A) -> B` 또는 `typealias` | 문서의 비교표 — 별칭은 **새 타입이 아니다** |
| 이름 있는 계약 · 기본 메서드 · 다른 인터페이스 확장 | ★ `fun interface` | (5) — 추상 하나 + 기본 여럿 |
| 박싱을 피하고 싶다(원시 타입 시그니처) | `fun interface` 또는 Java SAM | (3) — `apply:(I)I` |
| Java 사용자도 람다로 넘기게 | Java SAM · `fun interface` · 일반 인터페이스 **모두** 된다 | (2) — 단 **Kotlin 사용자**는 `fun interface` 라야 한다 |
| 추상 멤버가 둘 이상 | 일반 `interface` + `object : I { … }` | (5) |
| 람다 전략을 바꿔야 한다(도구 호환 등) | `-Xlambdas` · `-Xsam-conversions` **둘 다** 확인 | (4) |

## 핵심 문장

1. SAM 변환은 **Java 인터페이스와 `fun interface` 에만** 걸린다 — 도장 없는 Kotlin 인터페이스는 격자에서 **7칸 전부** 막혔다.
2. 변환 여부는 **받는 메서드가 아니라 인터페이스의 출신**이 정하고, **기대 타입이 SAM 인 자리** 어디서나(인자·생성자·변수 초기화) 걸린다.
3. **Java 컴파일러는 `fun` 도장을 모른다** — Kotlin 이 못 넘기는 인터페이스에 Java 는 람다를 넘긴다.
4. 받아 준 람다는 기본으로 **`invokedynamic`** 이고, 만드는 타입이 **`Function1` 이냐 그 인터페이스냐**가 갈린다. 함수 타입 **값**을 넘기면 어댑터가 하나 더 생긴다.
5. `-Xlambdas` 는 함수 타입 람다만, `-Xsam-conversions` 는 SAM 변환만 움직인다 — **12칸 중 9칸**이 플래그에 따라 갈렸다.

## 관련 자료

- [10번 주제](../10-lambdas-and-higher-order-functions/) — ★★ **선행.** `FunctionN` · `invokedynamic` · SAM 변환의 **박싱** 면. 그쪽은 「함수 타입이 무엇이고 람다가 몇 개 생기나」까지, 여기는 「**어느 인터페이스가 람다를 받아 주나**」부터.
- [31번 주제](../31-operator-overloading-infix-and-invoke/) — `invoke` 규약. (2)의 `C 2 2`.
- [14번 주제](../14-scope-functions/) — 클래스 파일 개수로 인라인을 가르지 말 것 (6).
- [목록의 **37번 주제**](../37-lambdas-with-receiver-and-type-safe-builders/) — 수신자 있는 함수 타입 `A.() -> Unit`. 이 주제의 `Function1` 이 그대로 이어진다.
- [`../../../java/syntax/31-functional-interfaces/`](../../../java/syntax/31-functional-interfaces/) · [`../../../java/syntax/29-lambda-expressions/`](../../../java/syntax/29-lambda-expressions/) — Java 쪽 짝.

## 용어 풀이

> **함수 타입(function type)** — `(Int) -> Int` 처럼 매개변수와 반환만으로 적는 타입. JVM 에서 `kotlin.jvm.functions.FunctionN`.

> **SAM(single abstract method)** — 추상 메서드가 **하나뿐인** 인터페이스. 람다 하나로 구현할 수 있다.

> **SAM 변환(SAM conversion)** — 람다를 SAM 인터페이스의 구현으로 **자동 변환**하는 것. Kotlin 은 Java 인터페이스와 `fun interface` 에만 한다.\
> 예: `takeJ { it + 1 }` · `JSam { it + 1 }`.

> **`fun interface`** — SAM 변환을 허락한다고 **도장을 찍은** Kotlin 인터페이스. 1.4 부터.

> **SAM 생성자** — `JSam { … }` 처럼 인터페이스 이름 뒤에 람다를 붙여 **인스턴스를 만드는** 꼴.

> **`invokedynamic` / `LambdaMetafactory`** — 람다 객체를 **실행 중에** 만드는 JVM 명령과 그 공장. 클래스 파일이 따로 안 생긴다.

> **`-Xlambdas` / `-Xsam-conversions`** — 함수 타입 람다와 SAM 변환을 각각 `indy`/`class` 중 무엇으로 내릴지 고르는 kotlinc 옵션.

## 더 들어가면

- **왜 Kotlin 은 일반 인터페이스에 SAM 변환을 안 하나** — Kotlin 에는 함수 타입이 있으므로, 「람다를 받고 싶다」는 뜻은 함수 타입으로 적으면 된다. 모든 단일 메서드 인터페이스에 변환을 허락하면 **인터페이스에 메서드를 하나 더하는 순간** 호출자의 람다가 전부 깨진다 — `fun` 도장은 「이 인터페이스는 **앞으로도 추상 메서드 하나**를 유지한다」는 **작성자의 약속**이다((5)의 제약이 그 약속을 컴파일러가 지키게 한다). Java 는 함수 타입이 없어 그 구분을 할 수 없었다.
- **`viaValue` 의 어댑터** — 함수 타입 값 `f` 를 `JSam` 이 필요한 자리에 넘기면, kotlinc 는 `f` 를 필드로 쥔 **감싸는 객체**를 만든다(`-Xsam-conversions=class` 에서 `Lam36Kt$sam$JSam$0` 이라는 이름으로 드러났다). 같은 `f` 를 두 번 넘기면 감싸는 객체도 두 번 생길 수 있다 — 이 문서는 **개수를 세지 않았다.**
