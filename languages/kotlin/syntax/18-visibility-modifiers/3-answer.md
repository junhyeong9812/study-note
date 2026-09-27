# kotlin/syntax/18 — 가시성 수식어: `internal` 이 Java 에 없는 이유 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javap` 에서 실제로 얻었다.\
> 역어셈블은 **기본 `-jvm-target`(1.8 · `major version: 52`)** 이 정본이다.
> ★★ 아래 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적은 자리가 없다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★ 울타리가 넷으로 갈린다 — 파일 · 클래스 · 하위 클래스 · 바깥

**출력**

```text
===== 소스: vis.kt =====
public fun topPublic() = "topPublic"
internal fun topInternal() = "topInternal"
private fun topPrivate() = "topPrivate"

private val topPrivateVal = "topPrivateVal"

open class Box(private val secret: String) {
    public val open1 = "public 멤버"
    internal val open2 = "internal 멤버"
    protected val open3 = "protected 멤버"
    private val open4 = "private 멤버"

    fun peek() = "$open1 / $open2 / $open3 / $open4 / $secret"
}

class SubBox : Box("상위의 private") {
    fun fromSub() = "하위가 보는 것 : $open3"
}

fun main() {
    println("A ${topPublic()} / ${topInternal()} / ${topPrivate()} / $topPrivateVal")
    println("B ${Box("s").peek()}")
    println("C ${SubBox().fromSub()}")
    val b = Box("s")
    println("D 바깥에서 보이는 것 : ${b.open1} / ${b.open2}")
}
===== kotlinc vis.kt -d ovis =====
(exit 0)
===== java -cp ovis:kotlin-stdlib.jar VisKt =====
A topPublic / topInternal / topPrivate / topPrivateVal
B public 멤버 / internal 멤버 / protected 멤버 / private 멤버 / s
C 하위가 보는 것 : protected 멤버
D 바깥에서 보이는 것 : public 멤버 / internal 멤버
(exit 0)
```

**왜 그런가**

- `A` — `main()` 은 **같은 파일**이므로 `private` 최상위 선언까지 전부 보인다. 최상위 `private` 의 울타리는 클래스가 아니라 **파일**이다.
- `B` — `peek()` 는 **`Box` 자기 안**이므로 `private val open4` 도, 주 생성자의 `private val secret` 도 읽는다.
- `C` — `SubBox` 는 **하위 클래스**라 `protected` 인 `open3` 까지만 본다. `open4` 를 부르면 컴파일 에러다.
- `D` — 바깥에서는 `public`·`internal` 둘뿐이다. 같은 모듈이라 `internal` 이 보이는 것이다(다른 모듈이면 4번처럼 막힌다).
- ★ `fun peek()`·`class SubBox` 에 아무 수식어도 없는데 컴파일된다 — **기본값이 `public` 이라는 증거**다. Java 는 안 적으면 package-private 이라 정반대다.

### 2. ★★ 에러 1건 — 「접근할 수 없다」가 아니라 「그 자리에 쓸 수 없다」

**출력**

```text
===== 소스: toplevel.kt =====
protected fun topProtected() = "안 된다"

class Holder {
    protected fun m() = "클래스 안에서는 된다"
}
===== kotlinc toplevel.kt -d otop =====
toplevel.kt:1:1: error: modifier 'protected' is not applicable to 'top level function'.
protected fun topProtected() = "안 된다"
^^^^^^^^^
(exit 1)
```

**왜 그런가**

- 문구가 `cannot access` 가 아니라 「`modifier 'protected' is not applicable to 'top level function'`」이다.\
  **접근을 시도하다 막힌 것이 아니라 선언 자체가 성립하지 않는다.**
- 최상위 선언에는 「하위 클래스」가 없다. `protected` 는 **상속 계층 위에서만 뜻이 있는 낱말**이라 계층이 없는 자리에서는 적용 대상이 아니다.
- ★ **에러가 1건뿐이다.** 같은 파일의 `class Holder` 안에 있는 `protected fun m()` 은 통과했다 — **같은 낱말이 자리에 따라 되고 안 되고가 갈린다.**
- ★ Java 의 `protected` 는 **같은 패키지에서도 보인다.** Kotlin 의 `protected` 에는 그 패키지 항이 없다(11번).

### 3. ★★ `private` 은 막히고 `internal` 은 통과한다 — 울타리가 「파일」이다

**출력**

```text
===== 소스: priv1.kt =====
private fun onlyInThisFile() = "priv1.kt 안에서만 보인다"

internal fun sameModule() = "같은 모듈이면 보인다"

fun callItHere() = onlyInThisFile()
===== 소스: priv2.kt =====
fun probe(): String {
    println(sameModule())
    println(onlyInThisFile())
    return "끝"
}
===== kotlinc priv1.kt priv2.kt -d opriv =====
priv2.kt:3:13: error: cannot access 'fun onlyInThisFile(): String': it is private in file.
    println(onlyInThisFile())
            ^^^^^^^^^^^^^^
(exit 1)
```

**왜 그런가**

- **한 번에 컴파일했는데도** 막혔다. `private` 의 울타리는 컴파일 단위가 아니라 **파일**이기 때문이다.
- 통과한 쪽을 보라 — `sameModule()` 은 `internal` 이라 **같은 컴파일이면 보인다.** 에러가 1건뿐인 것이 그 증거다.
- 에러 문구의 「`it is private in file.`」에서 `in file` 자리에, 클래스 멤버였다면 **클래스 이름**이 온다(10번의 `it is private in 'Box2'`).
- ★ Java 의 package-private 과 다르다 — **같은 폴더의 다른 파일은 남**이다(9번).

### 4. ★★★ 모듈은 **`kotlinc` 한 번**이다 — 소스는 한 글자도 안 바꿨다

**출력** — 따로 컴파일한 판

```text
===== 소스: moda.kt =====
public fun modaOpen() = "moda 의 public — 안에서 internal 을 부른다 : " + modaSecret()

internal fun modaSecret() = "moda 의 internal"

class Tool {
    internal fun helper() = "Tool.helper (internal 멤버)"
    fun use() = "같은 모듈 안에서는 : " + helper()
}
===== 소스: modb.kt =====
fun main() {
    println("A " + modaOpen())
    println("B " + Tool().use())
    println("C " + modaSecret())
    println("D " + Tool().helper())
}
===== kotlinc moda.kt -module-name moda -d omoda =====
(exit 0)
===== kotlinc modb.kt -module-name modb -cp omoda -d omodb =====
modb.kt:4:20: error: cannot access 'fun modaSecret(): String': it is internal in file.
    println("C " + modaSecret())
                   ^^^^^^^^^^
modb.kt:5:27: error: cannot access 'fun helper(): String': it is internal in 'Tool'.
    println("D " + Tool().helper())
                          ^^^^^^
(exit 1)
```

**출력** — 같은 두 파일을 한 번에 컴파일한 판

```text
===== kotlinc moda.kt modb.kt -module-name onemod -d oone =====
(exit 0)
===== java -cp oone:kotlin-stdlib.jar ModbKt =====
A moda 의 public — 안에서 internal 을 부른다 : moda 의 internal
B 같은 모듈 안에서는 : Tool.helper (internal 멤버)
C moda 의 internal
D Tool.helper (internal 멤버)
(exit 0)
```

**왜 그런가**

- ★★★ **소스는 동일하다.** 바뀐 것은 `kotlinc` 를 두 번 부르느냐 한 번 부르느냐뿐인데, 한쪽은 에러 2건이고 한쪽은 `A`\~`D` 가 전부 찍힌다.\
  그러므로 **모듈 = 한 번의 컴파일**이다. 패키지도 폴더도 파일도 아니다.
- 에러 문구가 둘로 갈린다 — 최상위는 「`it is internal in file.`」, 클래스 멤버는 「`it is internal in 'Tool'.`」.\
  ★ 앞엣것이 3번의 `private` 과 **같은 `in file` 문구**를 쓴다는 것에 속지 마라. 울타리의 **크기**는 전혀 다르다(파일 대 모듈).
- `modaOpen()` 은 `public` 이므로 모듈 밖에서 보이고, **그 몸통 안에서는 `internal` 을 마음껏 부른다.**\
  이것이 `internal` 의 쓸모다 — **공개 표면은 좁게, 내부는 모듈 안에서 자유롭게.**
- ★ Gradle 에서 「모듈」이 소스 세트 하나인 것도 같은 이유다. **Gradle 이 `kotlinc` 를 소스 세트마다 한 번씩 부르기 때문**이지, Gradle 에 특별한 규칙이 있어서가 아니다.

### 5. ★★★ 바이트코드에서 `internal` 은 **`public` + 이름 뒤에 `$모듈명`** 이다

**출력**

```text
===== 소스: mangle.kt =====
internal class Hidden {
    internal fun onlyHere() = "Hidden.onlyHere"
}

open class Named {
    internal fun plain() = "plain"

    @JvmName("renamed")
    internal fun withJvmName() = "withJvmName"

    protected fun prot() = "prot"
    private fun priv() = "priv"
    fun use() = priv()
}
===== kotlinc mangle.kt -module-name moda -d omangle =====
(exit 0)
===== javap -p omangle/Hidden.class omangle/Named.class =====
Compiled from "mangle.kt"
public final class Hidden {
  public Hidden();
  public final java.lang.String onlyHere$moda();
}
Compiled from "mangle.kt"
public class Named {
  public Named();
  public final java.lang.String plain$moda();
  public final java.lang.String renamed();
  protected final java.lang.String prot();
  private final java.lang.String priv();
  public final java.lang.String use();
}
(exit 0)
```

**출력** — `-module-name` 을 안 주면

```text
===== kotlinc mangle.kt -d odefault =====
(exit 0)
===== javap -p odefault/Named.class =====
Compiled from "mangle.kt"
public class Named {
  public Named();
  public final java.lang.String plain$main();
  public final java.lang.String renamed();
  protected final java.lang.String prot();
  private final java.lang.String priv();
  public final java.lang.String use();
}
(exit 0)
```

**출력** — 최상위 `internal` 함수는 어떻게 되나 (4번에서 만든 `omoda` 를 그대로 찍었다)

```text
===== javap -p omoda/ModaKt.class omoda/Tool.class =====
Compiled from "moda.kt"
public final class ModaKt {
  public static final java.lang.String modaOpen();
  public static final java.lang.String modaSecret();
}
Compiled from "moda.kt"
public final class Tool {
  public Tool();
  public final java.lang.String helper$moda();
  public final java.lang.String use();
}
(exit 0)
```

**왜 그런가**

- ★★★ **`internal class Hidden` 이 `public final class Hidden` 이다.** JVM 에는 `internal` 에 해당하는 접근 플래그가 **없다** — `ACC_PUBLIC`·`ACC_PROTECTED`·`ACC_PRIVATE`·(플래그 없음=package-private) 넷뿐이다.
- 그래서 컴파일러는 **접근 제어 대신 이름을 바꾼다.** `helper()` 가 `helper$moda()` 가 되면 다른 모듈에서 **부를 이름이 안 맞는다.**
- ★★ **그 `moda` 는 `-module-name` 플래그 값 그 자체다.** 플래그를 빼면 `plain$main` 이 된다 — 기본 모듈 이름이 `main` 이다.\
  **모듈 이름이 컴파일러 인자라는 것**이 「모듈 = 컴파일 한 번」의 두 번째 증거다.
- ★★ **최상위 `internal` 함수는 안 뭉개진다.** `ModaKt.modaSecret()` 은 이름이 그대로이고 `public static final` 이다.\
  「`internal` 은 항상 `$모듈명` 이 붙는다」는 **거짓**이다 — 붙는 것은 **클래스 멤버**뿐이다.
- ★ **`internal class` 의 이름도 안 뭉개진다.** 뭉개지는 것은 멤버 이름이다.
- ★ **`@JvmName("renamed")` 을 붙이면 `renamed()` 로 나오고 접미가 없다**(7번).
- `protected`·`private` 은 JVM 에 같은 이름의 플래그가 있으므로 **그대로 내려간다** — `protected final`·`private final`.

### 6. ★★ Java 는 전부 본다 — 경고도 없다

**출력**

```text
===== 소스: UseInternal.java =====
public class UseInternal {
    public static void main(String[] args) {
        System.out.println("A " + ModaKt.modaOpen());
        System.out.println("B " + ModaKt.modaSecret());
        System.out.println("C " + new Tool().helper$moda());
    }
}
===== javac -cp omoda:kotlin-stdlib.jar -d ojava UseInternal.java =====
(exit 0)
===== java -cp ojava:omoda:kotlin-stdlib.jar UseInternal =====
A moda 의 public — 안에서 internal 을 부른다 : moda 의 internal
B moda 의 internal
C Tool.helper (internal 멤버)
(exit 0)
```

**출력** — 같은 이름을 Kotlin 쪽에서 부르면

```text
===== 소스: modc.kt =====
fun probe() {
    println(Tool().`helper$moda`())
}
===== kotlinc modc.kt -module-name modc -cp omoda -d omodc =====
modc.kt:2:20: error: unresolved reference 'helper$moda' on receiver of type 'Tool'.
    println(Tool().`helper$moda`())
                   ^^^^^^^^^^^^^
(exit 1)
```

**왜 그런가**

- `javac` 가 **경고 한 줄 없이 `exit 0`** 이고 실행도 된다. Java 입장에서 `modaSecret()` 과 `helper$moda()` 는 **그냥 public 메서드**다.
- ★★ **Kotlin 쪽에서는 백틱으로 감싸도 못 부른다** — `unresolved reference 'helper$moda'`. Kotlin 컴파일러는 **뭉개진 이름을 소스에 노출하지 않는다.**

```text
                            modaSecret()   Tool().helper()   Tool().`helper$moda`()
   Kotlin (다른 모듈)          에러            에러                 에러
   Java                         OK             OK (helper$moda)     —
```

- ★★★ 그래서 **막는 것은 Kotlin 컴파일러이지 JVM 이 아니다.** 컴파일러를 안 거치는 경로는 전부 뚫려 있다(8번).
- ★ 정확한 표현은 「안 보인다」가 아니라 「**Kotlin 으로는 부를 이름이 없다**」이다.

### 7. 뭉개기는 「막는 장치」가 아니라 「이름을 어긋나게 하는 장치」다

**왜 그런가**

- 뭉개기가 하는 일은 **접근 거부가 아니라 이름 불일치**다. 다른 모듈이 `helper()` 라고 적으면 그런 메서드가 없으니 **못 찾는다.**\
  같은 장치가 부수적으로 **충돌도 막는다** — 두 모듈이 같은 시그니처의 `internal` 멤버를 상속 계층에 넣어도 이름이 달라 안 부딪친다.
- `@JvmName("renamed")` 은 컴파일러에게 「**이 메서드의 JVM 이름은 내가 정한다**」고 말하는 것이다.\
  컴파일러가 이름을 정하지 않으니 **접미를 붙일 자리도 사라진다**(5번의 `renamed()`).
- ★ 그 결과 **모듈 울타리의 마지막 흔적까지 없어진다.** Java 에서 편히 부르라고 붙인 애너테이션이 「실수로 부르기 어렵게」라는 유일한 방어선을 지운다.
- ★ 애초에 방어선이 얇았다는 것이 요점이다 — **뭉개기가 있어도 Java 는 부를 수 있었다**(6번의 `helper$moda()`).

### 8. 못 쓴다 — 「실수 방지」이지 「보안 경계」가 아니다

**왜 그런가**

- 가르는 기준은 이것이다 — **악의적인 상대가 우회할 수 있으면 보안 경계가 아니다.**\
  `internal` 은 **철자를 맞게 적기만 하면** 뚫린다(6번의 Java).
- Kotlin 컴파일러를 안 거치는 경로 —
  1. **Java 소스**(6번에서 실제로 뚫었다),
  2. **리플렉션** — `getDeclaredMethod("helper$moda")` 는 `public` 메서드를 그냥 찾는다,
  3. **다른 JVM 언어**(Groovy·Scala·Clojure),
  4. **바이트코드를 직접 만드는 도구**(ASM·바이트버디), 그리고 5. **같은 이름의 모듈로 다시 컴파일**하는 것.
- 진짜로 막으려면 **언어 밖의 장치**가 필요하다 — 아티팩트 분리, **JPMS** 의 `exports` 제한, 클래스로더 격리, 서명 검증.
- ★ `internal` 의 값어치는 「**공개 API 표면을 줄여 리팩토링을 싸게 만드는 것**」이지 보호가 아니다.

### 9. 울타리의 축이 다르다 — 하나는 **파일**, 하나는 **패키지**

**왜 그런가**

- 최상위 `private` — **같은 폴더의 다른 파일에서 안 보인다**(3번에서 실제로 막혔다).
- **같은 `package a.b` 선언을 쓴 다른 파일에서도 안 보인다.** Kotlin 의 `private` 은 패키지를 **아예 보지 않는다.**
- Java 의 package-private — 같은 패키지면 **파일이 달라도 보인다.** 그래서 「패키지 안의 협력 클래스들」이라는 설계가 성립했다.
- ★ 헷갈리면 버그가 아니라 **불편**이 생긴다 — 컴파일이 안 되므로 조용히 새지 않는다.\
  Kotlin 에서 그 자리를 메우는 것은 `internal` 이고, 울타리가 **패키지보다 넓다**(모듈 전체).
- ★ 그래서 Kotlin 에는 「패키지 단위로 숨기기」가 **없다.** 이것이 두 언어의 실질적인 빈칸이다(11번).

### 10. ★ 에러 3건 — 앞의 둘은 **누출**, 마지막은 **접근**이다

**출력**

```text
===== 소스: forbid18.kt =====
private class Secret(val v: Int)

fun leak(): Secret = Secret(1)

internal class Half(val v: Int)

public fun half(): Half = Half(1)

class Box2 {
    private val hidden = 1
}

fun outside(b: Box2) = b.hidden
===== kotlinc forbid18.kt -d oforbid =====
forbid18.kt:3:5: error: 'public' function exposes its 'private-in-file' return type 'Secret'.
fun leak(): Secret = Secret(1)
    ^^^^
forbid18.kt:7:12: error: 'public' function exposes its 'internal' return type 'Half'.
public fun half(): Half = Half(1)
           ^^^^
forbid18.kt:13:26: error: cannot access 'val hidden: Int': it is private in 'Box2'.
fun outside(b: Box2) = b.hidden
                         ^^^^^^
(exit 1)
```

**왜 그런가**

- ★★ 앞의 둘은 「**좁은 타입을 넓은 자리에 내놓는 것**」을 막는다.\
  `public fun leak(): Secret` 이 허용되면 **호출자가 이름조차 부를 수 없는 타입의 값**을 받게 된다 — 받아 놓고 아무것도 못 한다.
- 문구가 울타리 이름을 그대로 말한다 — `private-in-file` 과 `internal`. **최상위 `private` 이 「파일」이라는 것이 에러 메시지에 박혀 있다.**
- 세 번째는 성격이 다르다 — **선언이 아니라 접근**이다(`cannot access ... it is private in 'Box2'`).\
  3번의 `it is private in file.` 과 나란히 놓으면 **울타리 이름이 자리에 따라 바뀐다**는 것이 보인다.
- ★ 이 규칙은 「가시성은 시그니처에 전염된다」로 외우면 된다 — **반환 타입·파라미터 타입·상위 타입이 전부 대상**이다.

### 11. 빈칸은 **양쪽에 하나씩**이다

| Java | Kotlin | 짝이 맞나 |
|---|---|---|
| `public` | `public` | 맞는다(단 Kotlin 은 **기본값**, Java 는 명시해야 한다) |
| `protected` | `protected` | ★ **안 맞는다** — Java 는 「하위 클래스 **+ 같은 패키지**」, Kotlin 은 「하위 클래스」만 |
| package-private (수식어 없음) | **없다** | ★ Kotlin 쪽 빈칸 |
| `private` | `private` | 클래스 멤버에서는 같다. 최상위에서는 Kotlin 이 「**파일**」이라는 뜻을 하나 더 갖는다 |
| **없다** | `internal` | ★ Java 쪽 빈칸 |

**왜 그런가**

- ★ 짝이 없는 칸은 **양쪽에 하나씩**이다 — Kotlin 에 package-private 이 없고, Java 에 `internal` 이 없다.
- Kotlin 의 `protected` 가 좁은 이유는 **패키지 항을 뺐기 때문**이다. Java 의 `protected` 는 사실상 「`protected` **또는** package-private」이라는 합집합이었다.
- ★ 그래서 Java 코드를 Kotlin 으로 옮길 때 **package-private 은 `internal` 로 가되 울타리가 넓어진다**(패키지 → 모듈). 이것은 변환이 아니라 **양보**다.
- ★ 반대로 Kotlin API 를 Java 에서 쓰면 `internal` 이 **`public` 으로 넓어진다**(5번·6번). **양쪽 방향 모두 넓어지는 쪽으로만 새는 것**이 이 대응표의 결론이다.

### 12. **넓히는 것은 되고 좁히는 것은 안 된다**

**출력** — 넓히면

```text
===== 소스: widen18.kt =====
open class Base {
    protected open fun f() = "Base.f"
    open val tag: String
        get() = "Base"
}

class Sub : Base() {
    public override fun f() = "Sub.f (protected -> public 로 넓혔다)"
    override val tag: String
        get() = "Sub"
}

fun main() {
    val s = Sub()
    println("A ${s.f()}")
    println("B ${s.tag}")
}
===== kotlinc widen18.kt -d owiden =====
(exit 0)
===== java -cp owiden:kotlin-stdlib.jar Widen18Kt =====
A Sub.f (protected -> public 로 넓혔다)
B Sub
(exit 0)
```

**출력** — 좁히려 하면

```text
===== 소스: narrow18.kt =====
open class Base {
    open fun f() = "Base.f"
}

class Sub : Base() {
    private override fun f() = "Sub.f"
}
===== kotlinc narrow18.kt -d onarrow =====
narrow18.kt:6:5: error: cannot weaken access privilege private for 'f' in 'Base'.
    private override fun f() = "Sub.f"
    ^^^^^^^
narrow18.kt:6:5: error: modifier 'private' is incompatible with 'override'.
    private override fun f() = "Sub.f"
    ^^^^^^^
narrow18.kt:6:13: error: modifier 'override' is incompatible with 'private'.
    private override fun f() = "Sub.f"
            ^^^^^^^^
(exit 1)
```

**왜 그런가**

- 에러 세 건이 전부 같은 줄을 가리킨다 — 「`cannot weaken access privilege private for 'f' in 'Base'`」가 첫째다.\
  ★ **좁히면 리스코프 치환이 깨진다.** `Base` 타입으로 들고 있는 호출자가 `f()` 를 부를 수 있어야 하는데, 하위 타입이 그것을 막으면 **그 호출이 어디서 깨질지 알 수 없다.**
- 넓히는 것은 된다 — `protected open fun f()` 를 하위에서 `public override fun f()` 로 적으면 **통과하고 바깥에서 부를 수 있다**(`A` 줄).\
  넓히는 쪽은 상위 타입으로 부르는 호출자에게 아무 영향이 없다.
- ★ 아무것도 안 적으면 **상위의 가시성을 그대로 물려받는다.** [19번 주제](../19-inheritance-open-final-override/)에서 `override` 가 자동으로 `open` 인 것과 같은 성격이다 — **오버라이드는 기본적으로 상위의 성질을 잇는다.**
- ★ 에러가 3건인 것에 주목하라 — `private` 과 `override` 가 **서로 양립할 수 없다**는 것을 컴파일러가 양방향으로 한 번씩 더 말한다.

## 실행 검증

```text
===== kotlinc -version =====
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
(exit 0)
===== java -version =====
openjdk version "21.0.5" 2024-10-15 LTS
OpenJDK Runtime Environment Temurin-21.0.5+11 (build 21.0.5+11-LTS)
OpenJDK 64-Bit Server VM Temurin-21.0.5+11 (build 21.0.5+11-LTS, mixed mode, sharing)
(exit 0)
===== javac -version =====
javac 21.0.5
(exit 0)
```

★ **흔들리는 칸과 안 흔들리는 칸**(제출 전 재대조에서 「고칠 것」과 「설계상 다른 것」을 가르는 선언이다)

| 흔들린다 | 안 흔들린다 |
|---|---|
| **없다** — 이 주제에는 해시코드·시간·스레드 순서를 싣지 않았다 | 컴파일 에러의 **문구·`파일:줄:칸`·캐럿 줄** |
| | `javap` 출력 **전체**(수식어·이름·`$모듈명` 접미·선언 순서) |
| | 모든 **종료 코드** · `println` 출력 |

> 근거 — 캡처 스크립트를 처음부터 두 번 돌려 **블록 95개(실행 52 + 소스 43)를 바이트 단위로 대조**했고, **달라진 파일은 0개**였다.

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `vis.kt` | `A`\~`D` — 네 수식어의 울타리 넷 | `kotlinc` → `java` |
| `toplevel.kt` | 최상위 `protected` 가 **적용 대상이 아닌 것** | `kotlinc` (컴파일 실패가 결과) |
| `priv1.kt` · `priv2.kt` | 최상위 `private` 이 **파일** 울타리인 것 | `kotlinc` 1회 (두 파일 한 번에) |
| `moda.kt` · `modb.kt` | ★★ **모듈 경계** — 따로 컴파일 대 같이 컴파일 | `kotlinc` 3회 · `java` 1회 |
| `mangle.kt` | `internal`→`public` · `$모듈명` · `@JvmName` · 기본 모듈 이름 `main` | `kotlinc` 2회 · `javap` 2회 |
| `omoda/ModaKt.class` | **최상위 `internal` 은 안 뭉개진다** | `javap` |
| `UseInternal.java` | Java 에서 `internal` 이 **경고 없이 보이는 것** | `javac` → `java` |
| `modc.kt` | 같은 이름을 **Kotlin 에서는 못 부르는 것** | `kotlinc` (컴파일 실패가 결과) |
| `form18.kt` | 네 수식어 + `private constructor` 가 실제로 컴파일·실행되는 것(`Z`) | `kotlinc` → `java` |
| `forbid18.kt` | **누출 2건 + 접근 1건** | `kotlinc` (컴파일 실패가 결과) |
| `widen18.kt` · `narrow18.kt` | 오버라이드에서 **넓히기는 되고 좁히기는 안 되는 것** | `kotlinc` 2회 → `java` 1회 |

**구현 의존 항목** — `$모듈명` 이라는 접미 형태, 기본 모듈 이름이 `main` 인 것, 최상위 `internal` 이 안 뭉개지는 것,
`internal class` 가 `public` 으로 나오는 것, `@JvmName` 이 뭉개기를 끄는 것 — **전부 이 컴파일러 판의 산출물**이다.\
반면 **「안 적으면 `public`」·「최상위 `private` 은 파일」·「최상위에 `protected` 는 없다」·
「`internal` 은 같은 모듈」·「모듈은 한 번의 컴파일」·「가시성은 오버라이드에서 넓히는 쪽으로만 움직인다」**
는 **언어의 계약**이다.

**★ 던져 봤더니 예상과 달랐던 것 — 두 건**

1. ★★★ **「`internal` 멤버는 `이름$모듈명` 으로 뭉개진다」가 절반만 맞았다.** 최상위 `internal` 함수(`modaSecret()`)는
   **이름이 한 글자도 안 바뀐다**(5번의 `18-topmangle`). 뭉개기는 **클래스 멤버에만** 붙는다.
   이것을 모르고 Java 쪽에서 `modaSecret$moda()` 를 찾으면 영원히 못 찾는다.
2. ★★ **`@JvmName` 이 뭉개기를 그냥 끈다.** 「이름을 바꿔 줄 뿐 접미는 남겠지」라고 예상했는데
   `renamed()` 로 **접미 없이** 나왔다. 상호운용 편의를 위해 붙인 애너테이션 하나가 모듈 울타리의
   **유일한 흔적을 지운다** — `javap` 로 찍어 보지 않으면 모른다.

**안 터진 것도 출력이다** — `javac` 가 `internal` 멤버를 부르는데 **경고를 한 건도 내지 않았다**(6번, `exit 0`).
Kotlin 쪽에서 아무 표시도 안 붙여 두었기 때문이다. 「경고가 없으니 괜찮다」가 성립하지 않는 대표적인 자리다.
