# kotlin/syntax/18 — 가시성 수식어: `internal` 이 Java 에 없는 이유 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Visibility modifiers](https://kotlinlang.org/docs/visibility-modifiers.html) · [Calling Kotlin from Java — Name mangling](https://kotlinlang.org/docs/java-to-kotlin-interop.html) · [Kotlin compiler options](https://kotlinlang.org/docs/compiler-reference.html).
> **실행 검증** — 이 문서의 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 에서 실제로 얻었다.\
> `kotlinc` 13회(컴파일 실패 6벌) · `javac` 1회 · `java` 5회 · `javap` 3회.\
> ★★ 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적지 않았다.
> ⚠️ **`-jvm-target` 을 밝히지 않은 바이트코드 주장은 반쪽이다.** 이 문서의 역어셈블은 전부 **기본값 1.8**(`major version: 52`)이다.
> **버전** — `public`·`private`·`protected`·`internal` 네 수식어와 이름 뭉개기는 전부 **1.0** 이다. 그 뒤로 바뀐 적이 없다.
> **경계** — 클래스 선언·생성자는 [15번 주제](../15-class-declaration-constructors-and-init/), 프로퍼티의 backing field 는 [16번 주제](../16-properties-backing-field-lateinit-const/),\
> `open`/`override` 는 [19번 주제](../19-inheritance-open-final-override/), Java 상호운용 애너테이션 전반은 목록의 **39번 주제**가 정본이다.\
> Java 쪽 짝은 [`../../../java/syntax/10-access-modifiers/`](../../../java/syntax/10-access-modifiers/) — 거기는 **네 단계(`public`/`protected`/package-private/`private`)**, 여기는 **그 자리에 `internal` 을 끼운 결과**다.
> 이 본문은 Claude 작성이다(원고 없음).

★ **흔들리는 칸 / 안 흔들리는 칸** — 제출 전 재대조에서 「고칠 것」과 「설계상 다른 것」을 가르는 선언이다.

| 흔들린다 | 안 흔들린다 |
|---|---|
| (이 주제에는 없다 — 해시코드·시간·순서를 싣지 않았다) | 컴파일 에러의 **타입·문구·파일:줄:칸** |
| | `javap` 출력 **전체**(수식어·메서드 이름·`$모듈명` 접미) |
| | 모든 **종료 코드** · `println` 출력 |

> 근거 — 캡처 스크립트를 두 번 돌려 **블록 95개(실행 52 + 소스 43)를 바이트 단위로 대조**했다(전체 결과는 3-answer 의 「실행 검증」).

## 한눈에 — 쉽게 말하면

**가시성 수식어는 「이 이름을 어디까지 부를 수 있나」를 적는 울타리다.**

Java 는 울타리가 넷이었다 — 온 세상 / 하위 클래스 / **같은 패키지** / 나 혼자.\
Kotlin 은 그중 「같은 패키지」를 빼고 「**같은 모듈**」을 넣었다.

> **모듈(module)** — 한 번에 같이 컴파일되는 코드 덩어리.\
> 예: Gradle 의 소스 세트 하나, Maven 프로젝트 하나, 또는 `kotlinc` 를 한 번 실행한 것.

비유는 문서 끝까지 이것 하나로 고정한다 — **사무실 건물**이다.

| 비유 | 실체 |
|---|---|
| 정문이 열려 있어 누구나 들어온다 | `public` — 기본값 |
| 사원증이 있어야 들어오는 층 | `internal` — 같은 모듈 |
| 부서 방 — 그 부서와 산하 팀만 | `protected` — 그 클래스와 하위 클래스 |
| 내 책상 서랍 | `private` |
| 건물을 통째로 새로 짓는 것 | 컴파일을 한 번 더 하는 것 = **새 모듈** |
| 사원증 리더기를 떼어 버린 옆 건물 | Java — 사원증 검사가 아예 없다 |

```text
   최상위 선언(파일에 바로)              클래스 멤버
   +-----------------------------+      +------------------------------+
   | public    어디서나          |      | public    어디서나           |
   | internal  같은 모듈         |      | internal  같은 모듈          |
   | private   같은 파일     <-- |      | private   같은 클래스    <-- |
   | protected 쓸 수 없다    <-- |      | protected 그 클래스+하위 <-- |
   +-----------------------------+      +------------------------------+
        같은 낱말인데 뜻이 다른 두 칸이 있다
```

「**같은 낱말, 다른 뜻**」이 이 주제의 절반이고, 나머지 절반은 「**JVM 에는 `internal` 이라는 것이 없다**」이다.

## 이 주제가 답하려는 질문

1. **모듈 경계는 무엇으로 정의되나** — 패키지인가, 폴더인가, 컴파일 한 번인가.
2. `internal` 은 **JVM 바이트코드에서 무엇이 되나** — JVM 에 없는 접근 수준을 어떻게 흉내 내나.
3. 그래서 **Java 에서는 보이나** — 안 보인다면 무엇이 막나, 보인다면 무엇이 샌 것인가.

## 동작 방식

### (1) 기본값은 `public` 이다 — 네 수식어가 한 파일에서 도는 모습

**언제 쓰나** — 새 선언을 하나 만들 때마다. 아무것도 안 적으면 `public` 이다(Java 의 package-private 과 정반대 기본값).

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

```text
   vis.kt (한 파일 = private 의 울타리)
   +--------------------------------------------------+
   | topPublic()    public    -> 어디서나              |
   | topInternal()  internal  -> 같은 모듈             |
   | topPrivate()   private   -> 이 파일 안            |
   |                                                  |
   |  class Box                                       |
   |  +--------------------------------------------+  |
   |  | open1 public | open2 internal               |  |
   |  | open3 protected  <- Box 와 SubBox 만        |  |
   |  | open4 private    <- Box 안에서만            |  |
   |  +--------------------------------------------+  |
   +--------------------------------------------------+
        main() 은 같은 파일이므로 A 줄의 넷을 전부 부른다
```

- `A` 는 **같은 파일 안**이라 `private` 최상위 함수·프로퍼티까지 전부 보인다.
- `B` 는 **클래스 자기 안**이라 `private` 멤버와 생성자의 `private val secret` 까지 보인다.
- `C` 는 **하위 클래스**라 `protected` 만 보인다 — `open4` 는 안 보인다((2) 참조).
- `D` 는 **바깥**이라 `public`·`internal` 둘뿐이다.
- ★ 아무 수식어도 안 쓴 `fun peek()`·`class SubBox` 가 컴파일되는 것이 곧 **기본값이 `public` 이라는 증거**다.

### (2) ★★ 최상위와 클래스 멤버에서 **뜻이 갈리는 두 낱말**

**언제 쓰나** — 파일 단위로 무언가를 숨기고 싶을 때, 그리고 최상위에 `protected` 를 쓰려다 막힐 때.

**`private` — 최상위에서는 「이 파일」이다.**

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

- `sameModule()` 은 통과하고 `onlyInThisFile()` 만 막혔다. **같은 모듈·같은 컴파일인데도** 막힌다.
- 에러 문구가 뜻을 그대로 말한다 — 「**it is private in file.**」. 클래스 멤버였다면 `private in 'Box'` 처럼 **클래스 이름**이 온다.
- ★ Java 의 package-private 과 헷갈리기 쉽다. **같은 폴더의 다른 파일은 남**이다.

**`protected` — 최상위에는 아예 없다.**

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

- 최상위 선언에는 「하위 클래스」라는 개념이 없으니 **수식어 자체가 적용 대상이 아니다**(`is not applicable to`).
- 같은 파일의 `class Holder` 안에서는 **같은 낱말이 통과한다** — 에러가 1건뿐인 것이 그 증거다.
- ★ Java 의 `protected` 는 **같은 패키지에서도 보인다.** Kotlin 의 `protected` 는 **그 클래스와 하위 클래스뿐**이다 — 패키지가 빠졌다.

### (3) ★★★ 모듈 경계는 **컴파일 한 번**이다 — 패키지도 폴더도 아니다

**언제 쓰나** — `internal` 을 쓸지 말지 정할 때. 「모듈」이 무엇인지 모르면 이 수식어는 쓸 수 없다.

같은 두 파일을 **따로 컴파일**한 판과 **같이 컴파일**한 판을 나란히 던진다.

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

```text
   kotlinc moda.kt -module-name moda -d omoda
   +--------------- 모듈 moda ----------------+
   | public   fun modaOpen()                  |
   | internal fun modaSecret()                |
   | class Tool { internal fun helper() }     |
   +------------------------------------------+
                    |  -cp omoda
                    v
   kotlinc modb.kt -module-name modb -cp omoda
   +--------------- 모듈 modb ----------------+
   | A modaOpen()      -> 보인다              |
   | C modaSecret()    -> 컴파일 에러         |
   | D Tool().helper() -> 컴파일 에러         |
   +------------------------------------------+
```

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

- **소스 한 글자도 안 바꿨다.** 바뀐 것은 `kotlinc` 를 **두 번 부르느냐 한 번 부르느냐**뿐인데 한쪽은 에러 2건, 한쪽은 `A`\~`D` 가 전부 찍힌다.
- 그래서 모듈은 **패키지가 아니고 폴더도 아니다** — 「한 번에 같이 컴파일되는 것」이다.
- ★ `modaOpen()` 은 **모듈 밖에서도 보이는데 그 몸통은 `internal` 을 부른다.** 이것이 `internal` 의 쓸모다 — 공개 API 는 좁게 두고 내부 구현은 모듈 안에서 마음껏 나눈다.
- 에러 문구가 둘로 갈린다 — 최상위는 「`it is internal in file.`」, 멤버는 「`it is internal in 'Tool'.`」.

**그 「한 번」에 이름이 붙는다.**

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

- 같은 `mangle.kt` 를 `-module-name` 없이 컴파일했더니 `plain$main` 이 나왔다. 기본 모듈 이름이 **`main`** 이다.
- (4)에서 `-module-name moda` 로 컴파일한 것과 대조하면 **접미가 `$moda` 에서 `$main` 으로 바뀐다** — 모듈 이름은 **컴파일러 플래그 값 그 자체**다.

### (4) ★★ JVM 에는 `internal` 이 없다 — `public` + **이름 뭉개기**로 흉내 낸다

**언제 쓰나** — `internal` 선언을 리플렉션·Java·다른 JVM 언어가 건드릴 때. 그리고 「보호된다」고 믿기 전에.

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

```text
   Kotlin 이 보는 것                JVM 이 보는 것 (javap)
   -----------------------------    ---------------------------------------
   internal class Hidden        ->  public final class Hidden
   internal fun Hidden.onlyHere ->  public final String onlyHere$moda()
   internal fun Named.plain     ->  public final String plain$moda()
   @JvmName("renamed") internal ->  public final String renamed()      <-- 뭉개기 없음
   protected fun prot()         ->  protected final String prot()
   private fun priv()           ->  private final String priv()
```

- ★★★ **`internal` 은 바이트코드에서 `public` 이다.** 접근 제어가 아니라 **이름 뭉개기**(name mangling)로 「실수로 부르기 어렵게」만 만든다.

> **이름 뭉개기(name mangling)** — 컴파일러가 메서드 이름 뒤에 `$모듈명` 을 붙여 바꿔 적는 것.\
> 예: `helper()` 가 클래스 파일에는 `helper$moda()` 로 들어간다. **다른 모듈이 실수로 부를 이름이 안 맞게 된다.**

- ★★ **뭉개기는 클래스 멤버에만 붙는다.** (3)의 `javap` 에서 최상위 `modaSecret()` 은 **이름이 그대로**였다 — 「`internal` 은 항상 뭉개진다」는 거짓이다.
- ★ **`internal class` 는 통째로 `public` 이다.** 클래스 이름은 뭉개지지 않는다 — 뭉개지는 것은 **멤버 이름**뿐이다.
- ★ **`@JvmName` 이 뭉개기를 끈다.** 이름을 직접 정하면 접미가 안 붙는다 — Java 에서 부르라고 내놓는 셈이다.
- `protected`·`private` 은 JVM 에 **같은 이름의 접근 플래그가 있으므로 그대로 내려간다.**

### (5) ★★ Java 에서는 전부 보인다 — 비대칭이 여기서 생긴다

**언제 쓰나** — 한 프로젝트에 Java 와 Kotlin 이 섞여 있을 때. Spring 프로젝트가 대표적이다.

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

- `javac` 가 **경고 한 줄 없이 통과**했고 실행도 된다. Java 는 `modaSecret()` 도 `helper$moda()` 도 **그냥 public 메서드**로 본다.
- ★★ **Kotlin 쪽에서는 같은 이름을 못 부른다** — 백틱으로 감싸도 안 된다.

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

```text
                 modaSecret()   Tool().helper()   Tool().`helper$moda`()
   Kotlin(다른 모듈)   에러           에러                에러
   Java                 OK            OK(helper$moda)      —
```

- **막는 것은 컴파일러이지 JVM 이 아니다.** 그래서 「Kotlin 컴파일러를 안 거치는 모든 경로」가 뚫린다 — Java, 리플렉션, 다른 JVM 언어, 수동으로 만든 바이트코드.
- ★ 「보이지 않는다」가 아니라 「**Kotlin 으로는 부를 이름이 없다**」가 정확한 표현이다.

## 문법 — 형태와 규칙

**형태** — 네 수식어와 생성자 수식어가 한 파일에서 전부 도는 최소 예제다.

```text
===== 소스: form18.kt =====
public fun a() = "a"
internal fun b() = "b"
private fun c() = "c"

open class Sample private constructor(val tag: String) {
    public val p = "p"
    internal val q = "q"
    protected val r = "r"
    private val s = "s"

    fun all() = "$tag $p $q $r $s"

    companion object {
        fun of(tag: String) = Sample(tag)
    }
}

fun main() {
    println("Z ${a()} ${b()} ${c()} ${Sample.of("t").all()}")
}
===== kotlinc form18.kt -d oform =====
(exit 0)
===== java -cp oform:kotlin-stdlib.jar Form18Kt =====
Z a b c t p q r s
(exit 0)
```

**금지 사례** — 「좁은 타입을 넓은 자리에 내놓는 것」이 이 갈래의 에러다.

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

**규칙 불릿**

- 수식어를 **안 적으면 `public`** 이다. Java 의 「안 적으면 package-private」과 정반대다.
- 최상위에서 `private` 은 **파일**, 클래스 멤버에서 `private` 은 **클래스**다.
- 최상위에 `protected` 는 **없다.**
- **오버라이드한 멤버는 상위의 가시성을 물려받는다** — 좁히려면 명시해야 하고 넓히는 것은 된다([19번 주제](../19-inheritance-open-final-override/)).
- `internal` 은 **모듈**이고, 모듈은 **컴파일 단위**다.
- 생성자도 수식어를 받는다 — `class C private constructor(val x: Int)` 형태로 `class` 와 `constructor` 사이에 적는다.

## 어디서 틀리나

1. ★★★ 「**`internal` 이면 안전하다**」 — 바이트코드는 `public` 이다((4)). Java·리플렉션·다른 JVM 언어에서 전부 부를 수 있다((5)). 보안 경계로 쓰면 안 된다.
2. ★★ **모듈을 패키지로 착각한다.** 같은 패키지라도 **다른 컴파일이면 남**이고, 다른 패키지라도 **같은 컴파일이면 식구**다((3)).
3. ★★ **최상위 `private` 을 package-private 으로 착각한다.** 같은 폴더의 다른 파일에서 안 보인다((2)).
4. ★ **Java 의 `protected` 습관.** Java 는 같은 패키지에서도 보이지만 Kotlin 은 아니다.
5. ★ 「**`internal` 은 항상 `$모듈명` 이 붙는다**」 — 최상위 함수는 안 붙는다((4)). Java 에서 부르려다 이름을 못 찾으면 `javap` 로 **실제 이름을 확인**하라.
6. ★ **`@JvmName` 을 붙이면 뭉개기가 사라진다**((4)). 「Java 에서 편하게 부르려고」 붙인 것이 **모듈 울타리의 마지막 흔적까지 지우는** 셈이다.
7. ★ **테스트 소스 세트는 보통 다른 모듈이 아니다.** Gradle 의 `test` 소스 세트는 `main` 의 `internal` 을 볼 수 있게 설정돼 있다 — 이것은 **빌드 도구의 설정**이지 언어 규칙이 아니다.

## 구현 세부사항 대 언어 보장

| 항목 | 어느 쪽인가 | 근거 |
|---|---|---|
| 네 수식어의 이름과 뜻 | **언어 보장** | 공식 레퍼런스 |
| 최상위 `private` = 파일 · 최상위에 `protected` 없음 | **언어 보장** | (2)의 에러 |
| `internal` = 같은 모듈 | **언어 보장** | (3) |
| 「모듈 = 한 번의 컴파일」 | **언어 보장**(정의 자체) | (3) |
| `internal` 이 바이트코드에서 `public` 인 것 | **JVM 백엔드의 구현** | (4)의 `javap` |
| 접미 형태가 `이름$모듈명` 인 것 | **구현 세부** | (4) |
| 기본 모듈 이름이 `main` 인 것 | **구현 세부**(컴파일러 기본값) | (3)의 `plain$main` |
| 최상위 `internal` 이 안 뭉개지는 것 | **구현 세부** | (4) |
| `@JvmName` 이 뭉개기를 끄는 것 | **구현 세부** | (4) |
| Java 에서 보이는 것 | **위 구현의 따름 결과** | (5) |

★ **이 표의 아래 다섯 줄은 컴파일러 판이 바뀌면 바뀔 수 있다.** 위 네 줄은 안 바뀐다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 라이브러리가 밖에 내놓는 API | `public` | 그것이 계약이다 |
| 모듈 안에서만 쓰는 도우미 | `internal` | 공개 API 표면을 줄인다 |
| 한 파일 안에서만 쓰는 도우미 | 최상위 `private` | 모듈 안에서도 안 보인다 — 가장 좁은 최상위 울타리 |
| 하위 클래스가 쓸 확장점 | `protected` | 단 `open` 과 함께여야 뜻이 산다([19번 주제](../19-inheritance-open-final-override/)) |
| 불변식을 지키는 상태 | `private` + 공개 접근자 | [16번 주제](../16-properties-backing-field-lateinit-const/) |
| **보안 경계** | 가시성 수식어로는 **안 된다** | (4)·(5) — 모듈 분리·클래스로더·서명이 필요하다 |

## 핵심 문장

1. **안 적으면 `public` 이다** — Java 와 기본값이 정반대다.
2. 최상위에서 `private` 은 **파일**, 클래스 안에서는 **클래스**다. 같은 낱말이 두 뜻이다.
3. 최상위에 **`protected` 는 없다.**
4. **모듈은 한 번의 컴파일**이다 — 패키지도 폴더도 아니다.
5. **JVM 에 `internal` 은 없다.** `public` + 이름 뭉개기로 흉내 내고, **Java 에서는 그대로 보인다.**

## 관련 자료

- [15번 주제](../15-class-declaration-constructors-and-init/) — 클래스·생성자 선언. **생성자에 수식어를 붙이는 형태**는 거기, 그 수식어의 뜻은 여기.
- [16번 주제](../16-properties-backing-field-lateinit-const/) — 프로퍼티. **게터·세터에 따로 수식어를 붙이는 것**은 거기, 수식어 자체의 뜻은 여기.
- [19번 주제](../19-inheritance-open-final-override/) — `open`/`override`. **가시성과 오버라이드의 상호작용**(좁힐 수 있나)은 거기가 정본이다.
- [`../../../java/syntax/10-access-modifiers/`](../../../java/syntax/10-access-modifiers/) — Java 의 네 단계. **package-private 이 무엇을 하고 있었는지**는 거기.
- 목록의 **39번 주제** — `@JvmName`·`@JvmStatic` 등 상호운용 애너테이션이 바이트코드에서 무엇을 바꾸나. 여기서는 **뭉개기를 끈다는 사실 하나**만 쓴다.
- [`../../언어-특성/README.md`](../../언어-특성/README.md) §9 — Kotlin/Java 상호운용의 실제 비용.

## 용어 풀이

> **가시성(visibility)** — 어떤 이름을 어디서 부를 수 있는지를 정하는 규칙.\
> 예: `private` 이면 그 울타리 밖에서는 이름 자체가 안 보인다.

> **모듈(module)** — 한 번에 같이 컴파일되는 Kotlin 코드 덩어리.\
> 예: `kotlinc a.kt b.kt` 한 번이 모듈 하나다. Gradle 에서는 소스 세트 하나가 대개 모듈 하나다.

> **이름 뭉개기(name mangling)** — 컴파일러가 이름 뒤에 `$모듈명` 을 붙여 바꿔 적는 것.\
> 예: `helper()` 가 클래스 파일에는 `helper$moda()` 로 들어가 다른 모듈이 실수로 부르기 어려워진다.

> **package-private** — Java 에서 수식어를 안 적었을 때의 기본 가시성. 같은 패키지에서만 보인다.\
> 예: Kotlin 에는 이 단계가 **없다.**

> **접근 플래그(access flag)** — 클래스 파일이 메서드·필드마다 들고 있는 비트. `ACC_PUBLIC`·`ACC_PRIVATE` 같은 것.\
> 예: `javap -v` 로 볼 수 있다. **`ACC_INTERNAL` 같은 것은 없다.**

> **소스 세트(source set)** — Gradle 이 나눠 놓은 소스 묶음(`main`·`test`).\
> 예: `test` 에서 `main` 의 `internal` 이 보이는 것은 **빌드 도구가 그렇게 설정해 둔 것**이다.

> **플랫폼 선언(platform declaration)** — Java 쪽에서 본 Kotlin 선언.\
> 예: Java 가 보는 `helper$moda()` 가 그것이다. [5번 주제](../05-platform-types/)의 플랫폼 **타입**과는 다른 말이다.

## 더 들어가면

- **`internal` 을 Java 에서 못 부르게 하고 싶다면** 가시성으로는 안 된다. 모듈을 **JPMS(Java Platform Module System)** 로 나누거나, 아티팩트를 아예 분리하거나, `@RequiresOptIn` 으로 「**부르면 경고·에러가 나는 표식**」을 붙이는 쪽이 현실적이다.
- **뭉개기가 하는 진짜 일은 「충돌 방지」에 가깝다.** 두 모듈이 같은 시그니처의 `internal` 멤버를 각각 상속 계층에 넣어도 이름이 달라 안 부딪친다.
- **가시성은 오버라이드에서 한 방향으로만 움직인다** — 상위의 `protected` 를 하위에서 `public` 으로 넓히는 것은 되고, `public` 을 `protected` 로 좁히는 것은 안 된다(자세한 것은 [19번 주제](../19-inheritance-open-final-override/)).
