# kotlin/syntax/36 — 함수 타입·`fun interface`·SAM 변환 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러·경고·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javac`·`java`·`javap` 에서 실제로 얻었다.\
> 역어셈블은 **기본 `-jvm-target`(1.8)** 이 정본이다.
> ★★ 아래 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적은 자리가 없다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **compiled 14 / 21** — 막힌 일곱이 **전부 `KPlain`** · `j2` 는 통과, `k2` 는 막힘

**출력**

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
===== kotlinc -cp o36 samgrid.kt -d o36g =====
samgrid.kt:11:18: error: argument type mismatch: actual type is '() -> ??? (Unknown lambda return type)', but 'KPlain' was expected.
fun k1() = takeK { it + 1 }
                 ^^^^^^^^^^
samgrid.kt:11:20: error: unresolved reference 'it'.
fun k1() = takeK { it + 1 }
                   ^^
samgrid.kt:12:23: error: argument type mismatch: actual type is '() -> ??? (Unknown lambda return type)', but 'KPlain!' was expected.
fun k2() = JHost.useK { it + 1 }
                      ^^^^^^^^^^
samgrid.kt:12:25: error: unresolved reference 'it'.
fun k2() = JHost.useK { it + 1 }
                        ^^
samgrid.kt:13:18: error: interface 'interface KPlain : Any' does not have constructors.
fun k3() = takeK(KPlain { it + 1 })
                 ^^^^^^
samgrid.kt:13:27: error: unresolved reference 'it'.
fun k3() = takeK(KPlain { it + 1 })
                          ^^
samgrid.kt:14:18: error: argument type mismatch: actual type is '(Int) -> Int', but 'KPlain' was expected.
fun k4() = takeK(g)
                 ^
samgrid.kt:15:23: error: argument type mismatch: actual type is '(Int) -> Int', but 'KPlain!' was expected.
fun k5() = JHost.useK(g)
                      ^
samgrid.kt:16:20: error: inapplicable candidate(s): fun inc(x: Int): Int
fun k6() = takeK(::inc)
                   ^^^
samgrid.kt:17:26: error: initializer type mismatch: expected 'KPlain', actual '(Int) -> Int'.
fun k7() { val x: KPlain = { it: Int -> it + 1 } }
                         ^
(exit 1)
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

**왜 그런가**

- ★★★ SAM 변환은 **Java 인터페이스와 `fun interface`** 에만 걸린다. `KPlain` 은 모양(추상 메서드 하나)이 맞아도 **도장이 없어** 어느 모양으로도 안 된다 — SAM 생성자조차 「`does not have constructors`」.
- ★★ `j2`/`k2` — 같은 `JHost` 의 Java 메서드인데 갈렸다. 변환 여부는 **받는 메서드가 아니라 인터페이스의 출신**이 정한다.
- ★★ 4·5·6(값·참조)과 7(변수 초기화)도 `JSam`·`KFun` 에서는 통과했다 — **기대 타입이 SAM 이면** 어디서나 변환된다.

### 2. ★★ `fnid.kt` — 경고 둘(「`check for instance is always 'true'.`」) · `A true true` · `B false false` · `C 2 2` · `D 11` / `JCall` — ★ **컴파일된다** · `A 20` · `B 30` · `C 40`

**출력**

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

**왜 그런가**

- ★★★ **Java 는 `KPlain` 에도 람다를 넣었다**(`A 20`). Java 의 함수형 인터페이스 규칙은 「추상 메서드 하나」뿐이고, `fun` 도장은 **Kotlin 컴파일러만** 읽는다.
- ★★ `C 40` — Java 에게 `(Int) -> Int` 는 `Function1` 인터페이스라 Java 람다가 그것을 구현한다.
- ★ `B false false` — `fun interface` 인스턴스는 `Function1` 이 아니다. 새 타입이다.

### 3. ★★ 넷 다 **`invokedynamic`** 으로 시작 — `Function1` · `JSam` · `KFun` · `Function1` · ★ `viaValue` 는 **둘**

**출력**

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

**왜 그런가**

- ★★★ SAM 변환된 람다는 `Function1` 을 거치지 않고 **바로 그 인터페이스**(`()LJSam;`·`()LKFun;`)가 된다.
- ★★ `viaValue` — 첫 `invokedynamic` 이 람다를 `Function1` 으로, 둘째가 그것을 받아 **`JSam` 으로 감싼다**(`(Lkotlin/jvm/functions/Function1;)LJSam;`). 함수 타입 **값**을 SAM 에 넘기면 어댑터가 하나 더 생긴다.

### 4. ★★★ **differ 9 / 12** — `-Xlambdas=class` 는 `viaFn`·`viaValue` 의 **람다 조각**만, `-Xsam-conversions=class` 는 `viaJava`·`viaFunIface`·`viaValue` 의 **어댑터 조각**만

**출력**

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

**왜 그런가**

- ★★★ 도움말이 두 옵션을 **따로** 적는다 — 「code generation scheme for lambdas」와 「… for SAM conversions」. 격자가 그대로 보였다: `-Xlambdas=class` 아래에서도 `viaJava` 는 **`indy->JSam`** 이다.
- ★★ `viaValue` 는 조각마다 다른 플래그를 따른다 — `$viaValue$f$1`(람다) 과 `$sam$JSam$0`(어댑터).
- ★ 네 판의 출력은 `A 11 12 13 14` 로 같다 — 전략은 **값을 안 바꾼다.**

### 5. ★ 막힌 넷 — `Two`·`Zero`(「`exactly one abstract function`」) · `WithProp`(「`cannot have abstract properties`」) · `Gen`(「`… abstract method with type parameters`」) · 통과 `Ok`

**출력**

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

**왜 그런가**

- ★★ 람다 하나는 **추상 함수 하나**만 구현할 수 있고, **타입 매개변수를 가질 수 없다.** 추상 프로퍼티도 람다로 못 채운다.
- ★ 기본 구현 있는 멤버(`Ok.b`)는 세지 않는다.

### 6. ★ `plainType` 은 **`Function1<? super Integer, Integer>`** · `suspendType` 은 **`Function2<? super Integer, ? super Continuation<? super Integer>, ? extends Object>`**

**출력**

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

**왜 그런가**

- ★★ `suspend` 는 **`Continuation` 매개변수 하나**를 더하고 반환을 `Object` 로 만든다 — 그래서 **다른 `FunctionN`** 이다. 그 이유는 코루틴 주제가 정본이다.

### 7. Kotlin 에서는 `k` 일곱 줄이 **전부 막히고**, Java 에서는 `A 20` 으로 **통과**한다 — Kotlin 쪽은 **Kotlin 언어의 규칙**(`fun` 도장), Java 쪽은 **Java 언어의 규칙**(추상 메서드 하나)이다

**왜 그런가**

- ★★ 두 컴파일러가 **같은 클래스 파일**을 다른 규칙으로 읽는다. `KPlain` 은 JVM 에서 추상 메서드 하나짜리 인터페이스일 뿐이고, 「`fun` 도장이 없다」는 사실은 **Kotlin 메타데이터**에만 있다.
- ★ 라이브러리 작성자에게의 뜻 — Java 사용자만 보고 「람다로 잘 넘어간다」고 판단하면 **Kotlin 사용자는 막힌다.**

### 8. **기대 타입이 SAM 인가**가 조건이다 — `j7`·`f7` 은 통과, `k7` 은 「`initializer type mismatch: expected 'KPlain', actual '(Int) -> Int'.`」

**왜 그런가**

- ★★ 인자 자리·SAM 생성자·변수 초기화 모두 **「이 자리의 타입은 `JSam`」이라는 기대 타입**을 준다. 그 타입이 변환 대상(Java SAM·`fun interface`)이면 람다가 변환된다.
- ★ `k7` 은 기대 타입이 `KPlain` 이지만 **변환 대상이 아니라** 람다가 그냥 `(Int) -> Int` 로 남아 불일치가 났다.

### 9. `f(1)` 은 **`invoke` 규약**으로 `f.invoke(1)` 이 된다 — 둘 다 `Function1.invoke` 호출이다 · `A` 는 함수 타입이 `Function1` 이라는 것, `B` 는 `fun interface` 가 **`Function1` 이 아니라서** 이 설탕을 못 받는다는 것

**왜 그런가**

- ★★ `Function1` 의 `invoke` 에는 `operator` 가 붙어 있어 `f(1)` 이 `f.invoke(1)` 로 풀린다([31번 주제](../31-operator-overloading-infix-and-invoke/)). 3번 `viaFn` 의 `invokeinterface … Function1.invoke` 가 그 호출이다.
- ★ `fun interface` 인스턴스는 `k.apply(1)` 로 불러야 한다 — `k(1)` 을 쓰려면 `operator fun invoke` 를 따로 두거나 `k::apply` 로 함수 타입으로 되돌린다(`D 11`).

### 10. **이름 있는 계약**(새 타입 · 기본 메서드 · 확장 · 다른 인터페이스 구현)이 필요하면 `fun interface`, **모양만** 필요하면 함수 타입 별칭

**왜 그런가**

- ★★ 별칭은 **새 타입이 아니다**([29번 주제](../29-type-aliases-and-nested-type-aliases/)) — 같은 모양의 다른 함수도 그 자리에 들어간다. `fun interface` 는 **`is Function1` 이 `false`** 인 별개 타입이라 섞이지 않는다(2번 `B`).
- ★ 박싱 없는 원시 시그니처가 필요할 때도 `fun interface` 다(3번의 `apply:(I)I`). 반대로 **호출자가 아무 람다·함수 참조나** 넘기게 하려면 함수 타입이 가장 가볍다.

### 11. **확인할 수 없다** — 이 판은 `-language-version 1.9` 이하를 「`is no longer supported`」로 거부한다 — ★ **못 잰 것**이다

**출력**

```text
===== kotlinc -language-version 1.9 funbad.kt -d o36lv =====
error: language version 1.9 is no longer supported; use version 2.0 or greater instead.
(exit 1)
===== kotlinc -language-version 2.0 susp36.kt -d o36lv2 =====
warning: language version 2.0 is deprecated and its support will be removed in a future version of Kotlin. Update the version to 2.2.
(exit 0)
```

**왜 그런가**

- ★★ 「2.0 미만이면 `class`」는 **도움말의 말**이고, 그 판을 돌릴 수 없으니 **실측이 없다.** `fun interface` 의 1.4 경계도 같은 이유로 문서를 근거로 적었다.
- ★ 이 판에서 잴 수 있는 것은 **2.0 이상에서 기본이 `indy`** 라는 것뿐이다(3번).

### 12. Kotlin 은 **함수 타입과 SAM 인터페이스 두 세계**를 가져서, 람다가 **어느 쪽으로 가나**를 컴파일러가 가려야 한다 — 그 가름이 1번 격자의 `KPlain` 줄이다

**왜 그런가**

- ★★ Java 는 함수 타입이 없으므로 「단일 추상 메서드 인터페이스면 람다」 하나로 끝난다([Java 31번](../../../java/syntax/31-functional-interfaces/)). Kotlin 은 함수 타입이 있어 **인터페이스 쪽 변환을 도장으로 제한**했고, 그 대가로 **같은 인터페이스를 두 언어가 다르게** 받는다(7번).
- ★ 두 세계를 잇는 비용도 있다 — 함수 타입 값을 SAM 에 넘기면 **어댑터가 하나 더** 생긴다(3번 `viaValue`).

## 실행 검증

```text
===== kotlinc -version =====
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
(exit 0)
```

```text
===== java -version =====
openjdk version "21.0.5" 2024-10-15 LTS
OpenJDK Runtime Environment Temurin-21.0.5+11 (build 21.0.5+11-LTS)
OpenJDK 64-Bit Server VM Temurin-21.0.5+11 (build 21.0.5+11-LTS, mixed mode, sharing)
(exit 0)
```

```text
===== javac -version =====
javac 21.0.5
(exit 0)
```

```text
===== javap -version =====
21.0.5
(exit 0)
```

★ **흔들리는 칸과 안 흔들리는 칸**

| 흔들린다 | 안 흔들린다 |
|---|---|
| **없다** — 람다 객체의 `toString()`·런타임 클래스 이름을 찍지 않았다 | 실행 출력 · `javap` 출력 · 격자 스크립트가 뽑은 명령 종류 |
| | 진단의 **문구·`파일:줄:칸`·캐럿** · 「compiled 14 / 21」·「differ 9 / 12」 |
| | 모든 **종료 코드** |

> 근거 — 캡처 스크립트를 처음부터 다시 돌려 **블록 전체를 바이트 단위로 대조**했다.
>
> 실측 — `capture.sh blocks` 와 `capture.sh blocks-recheck` 를 처음부터 따로 돌려 `normalize-shaky.py` 로 대조했다 —\
> **블록 103개 · 동일 103 · 흔들린 칸 0 · ★고칠 것 0**(34\~37 네 주제를 한 캡처로 받았다). `diff -rq` 도 차이 0 이다.\
> ★ **정규화 규칙은 하나도 안 썼다** — 기본 넷(주소·PID·스레드 id·시간)에 걸리는 칸이 애초에 없었다.

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `JSam.java` · `ifaces.kt` · `JHost.java` · `samgrid.kt` | ★★★ SAM 격자 `14 / 21` | `javac` → `kotlinc` → `javac` → `kotlinc`(실패가 결과) · 스크립트 |
| `fnid.kt` · `JCall.java` | ★★ Java 쪽 비대칭 · `Function1` 정체 | `kotlinc`(경고) → `java` · `javac` → `java` |
| `lam36.kt` | ★★ 네 람다의 첫 명령 | `kotlinc` → `java` · `javap -c`(필터) |
| `lamgrid36.py` | ★★★ 판 격자 `9 / 12` | `kotlinc` 세 벌(`-Xlambdas`·`-Xsam-conversions`·둘 다) → `java` → 스크립트(내부에서 `javap` 4회) |
| `funbad.kt` | `fun interface` 의 제약 | `kotlinc`(실패가 결과) |
| `funbad.kt` · `susp36.kt`(판) | `-language-version 1.9` 거부 · 2.0 경고 | `kotlinc` 두 벌 |
| `susp36.kt` | `suspend` 함수 타입 서명 | `kotlinc` → `javap -s` |
| `form36.kt` | 형태 한 벌 | `kotlinc` → `java` |

**구현 의존 항목** — 람다를 `invokedynamic` 으로 내리는 것 · ★★ **두 플래그가 따로 움직이는 것** · 값의 SAM 변환이 만드는 어댑터 · `suspend` 의 `Continuation` 매개변수 · 합성 클래스 이름 · 진단 문구 — 이 컴파일러·판의 산출물이다.\
반면 **「함수 타입은 `FunctionN`」「SAM 변환은 Java 인터페이스·`fun interface` 에만」「`fun interface` 는 추상 함수 하나」** 는 **언어의 계약**이다.

**★ 던져 봤더니 예상과 달랐던 것 — 세 건**

1. ★★★ **`-Xlambdas=class` 가 SAM 람다를 움직이지 않았다**(4번) — 그것은 **`-Xsam-conversions`** 라는 **다른 옵션**의 몫이었다. 브리핑은 `-Xlambdas` 하나로 판 격자를 짰다.
2. ★★ **`val x: JSam = { … }` 가 통과했다**(1번 `j7`·`f7`) — SAM 변환은 인자 자리만이 아니라 **기대 타입이 있는 자리** 어디서나 걸렸다.
3. ★★ **Java 는 Kotlin 일반 인터페이스에 람다를 넣었다**(2번 `A`) — 같은 인터페이스가 Kotlin 에서는 **7칸 전부** 막혔다.
