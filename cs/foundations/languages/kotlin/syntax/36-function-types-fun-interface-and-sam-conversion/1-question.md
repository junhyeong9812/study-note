# kotlin/syntax/36 — 함수 타입·`fun interface`·SAM 변환 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [10번 주제](../10-lambdas-and-higher-order-functions/)다 — 함수 타입이 `FunctionN` 이라는 것, 람다가 `invokedynamic` 이 되는 것, SAM 변환이 **박싱을 없애는 자리**를 거기서 봤다. [31번 주제](../31-operator-overloading-infix-and-invoke/)의 `invoke` 규약도 이어진다.
> 문항 12개 중 코드블록이 붙는 예측형은 6개다.
> 바이트코드를 묻는 문항은 **`kotlinc` 기본 `-jvm-target`(1.8)** 기준이다.
> 이 주제의 모든 답은 **kotlinc 2.4.20 · Temurin JDK 21.0.5** 에서 실제로 던져 받은 것이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 세 인터페이스 × 일곱 가지 넘기는 법 (예측)

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

- 스물한 함수 중 컴파일되는 것은 어느 것인가? 안 되는 것은 무엇이라고 말하는가?
- ★ `j2` 와 `k2` 는 **같은 Java 메서드 모양**(`JHost.use…`)인데 결과가 같은가?

### 2. ★★ Java 쪽에서 Kotlin 인터페이스에 람다를 넘기면 (예측)

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

- `fnid.kt` 의 컴파일 진단과 `A`\~`D` 는? `JCall.java` 는 컴파일되는가 — 특히 `A` 줄은? 돌리면 무엇이 찍히는가?

### 3. ★★ 네 람다는 무엇으로 번역되나 (예측)

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

- 기본 옵션에서 `viaFn`·`viaJava`·`viaFunIface`·`viaValue` 의 첫 명령은 각각 무엇인가? `invokedynamic` 이면 **무슨 타입**을 만드는가?
- `viaValue` 에는 `invokedynamic` 이 몇 번 나오는가? 왜?

### 4. ★★★ `-Xlambdas=class` 와 `-Xsam-conversions=class` (예측)

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

- 3번을 `-Xlambdas=class` · `-Xsam-conversions=class` · 둘 다로 각각 컴파일하면, 기본과 견줘 **12칸 중 몇 칸**이 갈리는가? 어느 플래그가 어느 함수를 움직이는가?

### 5. ★ `fun interface` 로 선언할 수 없는 것 (예측)

```kotlin
// funbad.kt
fun interface Two { fun a(); fun b() }
fun interface Zero
fun interface WithProp { val p: Int; fun a() }
fun interface Gen { fun <T> a(x: T): T }
fun interface Ok { fun a(x: Int): Int; fun b(): Int = 0 }
```

- 다섯 선언 중 막히는 것은 어느 것이고, 각각 무엇이라고 말하는가?

### 6. ★ `suspend` 가 붙은 함수 타입의 JVM 서명 (예측)

```kotlin
// susp36.kt
fun plainType(f: (Int) -> Int) {}
fun suspendType(f: suspend (Int) -> Int) {}
```

- `javap -s` 로 보면 두 함수의 매개변수 타입은 각각 무엇인가?

### 7. Kotlin 인터페이스에 람다를 넘기는 규칙의 주인 (왜)

- 1번의 `k` 일곱 줄과 2번 `JCall` 의 `A` 줄을 견주면 결과가 어떻게 갈리는가? 그 차이는 **누가** 정한 규칙인가?

### 8. 인자 자리가 아닌 곳의 SAM 변환 (경계)

- 1번 `j7`·`k7`·`f7` 은 **변수 초기화**다. 세 줄의 결과를 가른 조건은 무엇인가? SAM 변환을 일으키는 것은 「인자 자리」인가 「기대 타입」인가?

### 9. `f(1)` 과 `f.invoke(1)` (연결)

- 2번 `C` 줄의 두 칸을 [31번 주제](../31-operator-overloading-infix-and-invoke/)의 `invoke` 규약과 `Function1` 으로 설명하면? `A` 줄과 `B` 줄의 결과와는 어떻게 이어지는가?

### 10. `fun interface` 와 함수 타입 별칭 (왜)

- `typealias Rule = (String) -> Boolean` 대신 `fun interface Rule` 을 고르는 이유는 무엇인가? 반대는?

### 11. 「기본값이 `indy`」라는 말의 범위 (경계)

- `-X` 도움말은 `-Xlambdas` 의 기본값이 「언어 판 2.0+ 이면 `indy`, 아니면 `class`」라고 적는다. 이 판에서 그 「아니면」을 **직접 확인할 수 있는가**?

### 12. Java 의 함수형 인터페이스와 견주면 (연결)

- Java 는 함수 타입이 없고 함수형 인터페이스만 있다([`../../../java/syntax/31-functional-interfaces/`](../../../java/syntax/31-functional-interfaces/)). Kotlin 이 **둘 다** 가진 대가는 1번 격자의 어디에 나타나는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
