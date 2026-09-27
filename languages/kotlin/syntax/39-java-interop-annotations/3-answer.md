# kotlin/syntax/39 — Java 상호운용 애너테이션 — `@JvmStatic`/`@JvmOverloads`/`@JvmName`/`@JvmField`/`@Throws` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javac`·`java`·`javap` 에서 실제로 얻었다.
> ★★ 아래 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적은 자리가 없다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **실패 — 3·5·7·9·11번째 줄**(짧은 모양 다섯) · 긴 모양 다섯은 통과

**출력**

```kotlin
// api0.kt
@file:JvmName("Api")

class Box {
    companion object { fun make(): String = "make" }
    val size: Int = 3
    fun greet(a: String, b: Int = 1, c: String = "c"): String = "$a$b$c"
}

object Reg { fun ping(): String = "ping" }

fun original(): String = "orig"
```

```java
// Calls.java
public class Calls {
    static void run() {
        String r1 = Box.make();
        String r2 = Box.Companion.make();
        String r3 = Reg.ping();
        String r4 = Reg.INSTANCE.ping();
        String r5 = new Box().greet("a");
        String r6 = new Box().greet("a", 1, "c");
        int r7 = new Box().size;
        int r8 = new Box().getSize();
        String r9 = Api.renamed();
        String r10 = Api.original();
    }
}
```

```text
===== kotlinc api0.kt -d o39a =====
(exit 0)
===== kotlinc api1.kt -d o39b =====
(exit 0)
```

```text
===== javac -cp o39a -d o39a-x Calls.java =====
Calls.java:3: error: cannot find symbol
        String r1 = Box.make();
                       ^
  symbol:   method make()
  location: class Box
Calls.java:5: error: non-static method ping() cannot be referenced from a static context
        String r3 = Reg.ping();
                       ^
Calls.java:7: error: method greet in class Box cannot be applied to given types;
        String r5 = new Box().greet("a");
                             ^
  required: String,int,String
  found:    String
  reason: actual and formal argument lists differ in length
Calls.java:9: error: size has private access in Box
        int r7 = new Box().size;
                          ^
Calls.java:11: error: cannot find symbol
        String r9 = Api.renamed();
                       ^
  symbol:   method renamed()
  location: class Api
5 errors
(exit 1)
```

**왜 그런가**

- ★★★ 애너테이션이 없으면 Java 가 보는 모양은 **긴 모양뿐**이다 — `Box.Companion.make()` · `Reg.INSTANCE.ping()` · `greet(a, b, c)` · `getSize()` · `original()`.
- ★★ 에러 네 종류가 **이유**를 말한다 — `Box.make()`·`Api.renamed()` 는 **이름째 없음**, `Reg.ping()` 은 **있는데 인스턴스 메서드**, `greet("a")` 는 **3인자 하나뿐**, `size` 는 **`private` 필드**.

### 2. ★★★ **10·12번째 줄만 실패** — `getSize()` 와 `Api.original()` 이 「`cannot find symbol`」 · 1번에서 통과했던 이 둘이 **새로 막혔다**

**출력**

```kotlin
// api1.kt
@file:JvmName("Api")

class Box {
    companion object { @JvmStatic fun make(): String = "make" }
    @JvmField val size: Int = 3
    @JvmOverloads fun greet(a: String, b: Int = 1, c: String = "c"): String = "$a$b$c"
}

object Reg { @JvmStatic fun ping(): String = "ping" }

@JvmName("renamed") fun original(): String = "orig"
```

```text
===== javac -cp o39b -d o39b-x Calls.java =====
Calls.java:10: error: cannot find symbol
        int r8 = new Box().getSize();
                          ^
  symbol:   method getSize()
  location: class Box
Calls.java:12: error: cannot find symbol
        String r10 = Api.original();
                        ^
  symbol:   method original()
  location: class Api
2 errors
(exit 1)
```

```text
===== python3 grid39.py o39a o39b =====
subject	Java call	o39a	o39b	
companion fn	Box.make()	error: cannot find symbol	ok	<-
companion fn	Box.Companion.make()	ok	ok	
object fn	Reg.ping()	error: non-static method ping() cannot be referenced from a static context	ok	<-
object fn	Reg.INSTANCE.ping()	ok	ok	
default args	greet("a")	error: method greet in class Box cannot be applied to given types;	ok	<-
default args	greet("a", 1, "c")	ok	ok	
property	box.size	error: size has private access in Box	ok	<-
property	box.getSize()	ok	error: cannot find symbol	<-
@JvmName fn	Api.renamed()	error: cannot find symbol	ok	<-
@JvmName fn	Api.original()	ok	error: cannot find symbol	<-
calls whose result differs: 7 / 10
(exit 0)
```

**왜 그런가**

- ★★★ 짧은 모양 다섯은 전부 통과하고, 긴 모양 중 **`@JvmField` 와 `@JvmName` 의 것만** 사라졌다 — 스크립트가 센 **갈린 줄 7 / 10**.
- ★★ `Box.Companion.make()`·`Reg.INSTANCE.ping()`·`greet("a", 1, "c")` 는 계속 된다 — 그 애너테이션들은 **추가**다(6번).

### 3. ★★★ `@JvmStatic`(동반 객체) — `make()` **둘**(`Box$Companion` 인스턴스 + `Box` 정적) · `@JvmStatic`(`object`) — `ping()` **하나**(인스턴스 → **정적으로 바뀜**) · `@JvmOverloads` — `greet` 가 **셋 + `$default`** · `@JvmField` — `private` 필드 + `getSize()` → **`public` 필드, 게터 없음** · `@JvmName` — `original()` → **`renamed()`**

**출력**

```text
===== javap -p o39a/Box.class 'o39a/Box$Companion.class' o39a/Reg.class o39a/Api.class =====
Compiled from "api0.kt"
public final class Box {
  public static final Box$Companion Companion;
  private final int size;
  public Box();
  public final int getSize();
  public final java.lang.String greet(java.lang.String, int, java.lang.String);
  public static java.lang.String greet$default(Box, java.lang.String, int, java.lang.String, int, java.lang.Object);
  static {};
}
Compiled from "api0.kt"
public final class Box$Companion {
  private Box$Companion();
  public final java.lang.String make();
  public Box$Companion(kotlin.jvm.internal.DefaultConstructorMarker);
}
Compiled from "api0.kt"
public final class Reg {
  public static final Reg INSTANCE;
  private Reg();
  public final java.lang.String ping();
  static {};
}
Compiled from "api0.kt"
public final class Api {
  public static final java.lang.String original();
}
(exit 0)
```

```text
===== javap -p o39b/Box.class 'o39b/Box$Companion.class' o39b/Reg.class o39b/Api.class =====
Compiled from "api1.kt"
public final class Box {
  public static final Box$Companion Companion;
  public final int size;
  public Box();
  public final java.lang.String greet(java.lang.String, int, java.lang.String);
  public static java.lang.String greet$default(Box, java.lang.String, int, java.lang.String, int, java.lang.Object);
  public final java.lang.String greet(java.lang.String, int);
  public final java.lang.String greet(java.lang.String);
  public static final java.lang.String make();
  static {};
}
Compiled from "api1.kt"
public final class Box$Companion {
  private Box$Companion();
  public final java.lang.String make();
  public Box$Companion(kotlin.jvm.internal.DefaultConstructorMarker);
}
Compiled from "api1.kt"
public final class Reg {
  public static final Reg INSTANCE;
  private Reg();
  public static final java.lang.String ping();
  static {};
}
Compiled from "api1.kt"
public final class Api {
  public static final java.lang.String renamed();
}
(exit 0)
```

```text
===== javac -cp o39b -d o39u Use39.java =====
(exit 0)
===== java -cp o39u:o39b:kotlin-stdlib.jar Use39 =====
make make
ping ping
a1c a2c a2z
3
orig
(exit 0)
```

**왜 그런가**

- ★★★ 문서의 계약 그대로다 — 동반 객체면 「정적 메서드 + 동반 객체의 인스턴스 메서드」, 이름 있는 `object` 면 「별도 인스턴스 메서드를 만들지 않는다」.
- ★★ `@JvmField` 는 **메서드 하나를 없앤다** — 공개 범위만 바뀌는 게 아니다. `final` 은 `val` 이라 그대로다.

### 4. ★★ `tail2` +2(`(String, int)` · `(String)`) · `all3` +3(… · `()`) · **`mid` +1 — `(String, String)`** · `none` +0 · 넷 다 `$default` 는 있다 · `JMid` 는 통과 — `a1z` · `a1c` · `x5c`

**출력**

```kotlin
// jov.kt
@JvmOverloads fun tail2(a: String, b: Int = 1, c: String = "c"): String = "$a$b$c"
@JvmOverloads fun all3(a: String = "a", b: Int = 1, c: String = "c"): String = "$a$b$c"
@JvmOverloads fun mid(a: String, b: Int = 1, c: String): String = "$a$b$c"
fun none(a: String, b: Int = 1, c: String = "c"): String = "$a$b$c"
```

```java
// JMid.java
public class JMid {
    public static void main(String[] args) {
        System.out.println(JovKt.mid("a", "z"));
        System.out.println(JovKt.all3());
        System.out.println(JovKt.all3("x", 5));
    }
}
```

```text
===== kotlinc jov.kt -d o39o =====
(exit 0)
===== javap -p o39o/JovKt.class =====
Compiled from "jov.kt"
public final class JovKt {
  public static final java.lang.String tail2(java.lang.String, int, java.lang.String);
  public static java.lang.String tail2$default(java.lang.String, int, java.lang.String, int, java.lang.Object);
  public static final java.lang.String all3(java.lang.String, int, java.lang.String);
  public static java.lang.String all3$default(java.lang.String, int, java.lang.String, int, java.lang.Object);
  public static final java.lang.String mid(java.lang.String, int, java.lang.String);
  public static java.lang.String mid$default(java.lang.String, int, java.lang.String, int, java.lang.Object);
  public static final java.lang.String none(java.lang.String, int, java.lang.String);
  public static java.lang.String none$default(java.lang.String, int, java.lang.String, int, java.lang.Object);
  public static final java.lang.String tail2(java.lang.String, int);
  public static final java.lang.String tail2(java.lang.String);
  public static final java.lang.String all3(java.lang.String, int);
  public static final java.lang.String all3(java.lang.String);
  public static final java.lang.String all3();
  public static final java.lang.String mid(java.lang.String, java.lang.String);
}
(exit 0)
===== javac -cp o39o -d o39o JMid.java =====
(exit 0)
===== java -cp o39o:kotlin-stdlib.jar JMid =====
a1z
a1c
x5c
(exit 0)
```

**왜 그런가**

- ★★★ **기본값 수만큼**, 뒤에서부터 **하나씩** 뗀 판이 생긴다.
- ★★★ `mid` 는 기본값이 `b` 하나라 **하나만** 생기고, 기본값 없는 `c` 는 **남는다** — `mid("a", "z")` 가 `a1z`.
- ★ `$default` 는 애너테이션과 **무관하게** 있다 — 기본 인자를 채우는 합성 메서드다. Java 가 쓸 입구가 아니다.

### 5. ★★ **2·3·4·5·8·9번째 줄 전부** — 「`not applicable to target 'member property without backing field or delegate'`」 · 「`jvmField has no effect on a private property.`」 · 「`only members in named objects and companion objects can be annotated with '@JvmStatic'.`」 · 「`jvmField cannot be applied to a property with a custom accessor.`」 · 「`jvmField can only be applied to final property.`」 · 「`'@JvmOverloads' annotation cannot be used on interface methods.`」

**출력**

```kotlin
// bad39.kt
class C1 {
    @JvmField val a: Int get() = 1
    @JvmField private val b: Int = 2
    @JvmStatic fun s(): Int = 3
    @JvmField var c: Int = 4
        set(v) { field = v }
}
open class C2 { @JvmField open val d: Int = 5 }
interface I3 { @JvmOverloads fun f(x: Int = 1): Int }
```

```text
===== kotlinc bad39.kt -d o39x =====
bad39.kt:2:5: error: this annotation is not applicable to target 'member property without backing field or delegate'. Applicable targets: field
    @JvmField val a: Int get() = 1
    ^^^^^^^^^
bad39.kt:3:5: error: jvmField has no effect on a private property.
    @JvmField private val b: Int = 2
    ^^^^^^^^^
bad39.kt:4:5: error: only members in named objects and companion objects can be annotated with '@JvmStatic'.
    @JvmStatic fun s(): Int = 3
    ^^^^^^^^^^
bad39.kt:5:5: error: jvmField cannot be applied to a property with a custom accessor.
    @JvmField var c: Int = 4
    ^^^^^^^^^
bad39.kt:8:17: error: jvmField can only be applied to final property.
open class C2 { @JvmField open val d: Int = 5 }
                ^^^^^^^^^
bad39.kt:9:16: error: '@JvmOverloads' annotation cannot be used on interface methods.
interface I3 { @JvmOverloads fun f(x: Int = 1): Int }
               ^^^^^^^^^^^^^
(exit 1)
```

**왜 그런가**

- ★★ `@JvmField` 의 네 에러는 문서의 조건 목록(백킹 필드 · `private` 아님 · `open` 아님 · 접근자 없음)과 **한 줄씩** 맞는다.
- ★ `@JvmStatic` 은 정적으로 만들 **싱글턴**이 있는 자리(`object`·`companion`)에만 뜻이 있다.

### 6. **추가**(`@JvmStatic`·`@JvmOverloads`)는 **옛 모양을 남기고** 새 모양을 더하므로 기존 Java 코드가 **안 깨진다** · **교체**(`@JvmField`·`@JvmName`)는 **옛 모양을 없애므로** 기존 Java 코드가 「`cannot find symbol`」로 **깨진다**

**왜 그런가**

- ★★★ 2번의 두 실패가 그것이다 — 1번에서 통과하던 `getSize()`·`original()` 이 2번에서 막혔다.
- ★ 그래서 공개 API 에서 `@JvmField`·`@JvmName` 은 **처음 낼 때** 정하는 것이 싸다. 나중에 달면 **소스 호환이 깨지는 변경**이다.

### 7. **Java 언어의 규칙** — Java 는 **인스턴스를 가리키는 식으로 정적 메서드를 부르는 것**을 허용한다(`Reg.INSTANCE` 의 타입 `Reg` 의 정적 메서드 `ping()` 으로 풀린다)

**왜 그런가**

- ★★ 3번 `javap` 의 붙인 판 `Reg` 에는 **`public static final java.lang.String ping();` 하나**뿐이다. Kotlin 이 인스턴스 판을 **남긴 것이 아니다.**
- ★ 그러니 「`object` 의 `@JvmStatic` 은 옛 모양을 남긴다」로 읽으면 틀린다 — **동반 객체**와 대칭이 아니다.

### 8. 글자대로면 **`mid(String)`**(b 와 그 오른쪽 전부를 뗀다) · 실제는 **`mid(String, String)`**(b 만 뗐다)

**왜 그런가**

- ★★ 이 판은 **기본값 있는 매개변수만** 뗀다 — 기본값 없는 `c` 를 떼면 그 값을 채울 방법이 없으니 당연한 결과이지만, 문서 문장은 그렇게 적혀 있지 않다.
- ★ 문장을 「그 오른쪽의 **기본값 있는** 매개변수까지」로 읽어야 맞는다 — 이것은 **이 판의 관찰**이고, 문장의 뜻을 보장으로 옮기지는 않는다.

### 9. 없으면 Java `catch (IOException e)` 가 「`exception IOException is never thrown in body of corresponding try statement`」로 **컴파일 안 되고**, 달면 클래스 파일에 **`Exceptions:` 속성**이 생겨 이번엔 **안 잡으면** 「`unreported exception`」이다

**왜 그런가**

- ★★ 34번 주제가 `javac` 와 `javap -v` 로 **이미 잰** 것이다 — 이 배치는 그 결론을 인용만 하고 재지 않았다([34번 주제](../34-exceptions-nothing-and-try-expression/) (2)).
- ★ 「추가 / 교체」로 읽으면 `@Throws` 는 **의무를 더하는** 쪽이다 — 공개 API 에 나중에 달면 **안 잡던 Java 호출자가 깨진다.**

### 10. **`init` 의 `require` 검사**가 사라졌다 — Java 가 `long` 을 직접 넘겨 `constructor-impl` 을 안 거치므로 `named#-1` 이 찍혔다 · 이 문서의 「교체」는 **이름**이 사라지는 것이고, 거기는 **타입의 방어선**이 사라지는 것이다

**왜 그런가**

- ★★ [26번 주제](../26-value-class-and-boxing/) (5)의 실측이다. `@JvmName` 은 뭉개진 이름(`lookup-Bu7z9Ig`)을 Java 가 부를 수 있는 이름으로 **풀어 줄 뿐**, 값 클래스의 검사를 **Java 쪽에 옮겨 주지 않는다.**
- ★ 그래서 `@JvmName` 은 「이름을 바꾸는 도구」로만 읽으면 부족하다 — **무엇을 Java 에 여는가**까지 봐야 한다.

### 11. **백킹 필드가 있느냐**다 — 2번째 줄(`val` + 게터만)은 **필드가 없어** 「대상이 아님」, 5번째 줄(`var` + 세터, `field` 를 씀)은 필드는 있지만 **접근자를 우회하게 되므로** 「커스텀 접근자에는 못 단다」

**왜 그런가**

- ★★ 2번째 줄의 문구가 「`Applicable targets: field`」로 끝난다 — `@JvmField` 는 **필드에 붙는 애너테이션**이고, 게터만 있는 `val` 에는 붙을 필드가 없다([35번 주제](../35-annotations-and-use-site-targets/)의 「어디에 붙나」와 같은 축).
- ★ 5번째 줄은 필드가 있으니 **대상은 맞지만 규칙이 막는다** — 필드를 공개하면 세터의 몸통(`field = v`)을 Java 가 건너뛸 수 있기 때문이다.

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
| **없다** — 해시코드·주소·시간을 찍지 않았다 | 격자 10행 · 갈린 수 · 실행 출력 · `javap` 출력 |
| | `javac`·`kotlinc` 진단의 **문구·줄 번호** |
| | 모든 **종료 코드** |

> 근거 — 캡처 스크립트를 처음부터 다시 돌려 **블록 전체를 바이트 단위로 대조**했다.
>
> 실측 — `capture.sh blocks` 와 `capture.sh blocks-recheck` 를 처음부터 따로 돌려 `normalize-shaky.py` 로 대조했다 —\
> **블록 80개 · 동일 80 · 흔들린 칸 0 · ★고칠 것 0**(38\~41 네 주제를 한 캡처로 받았다). `diff -rq` 도 차이 0 이다.\
> ★ **정규화 규칙은 하나도 안 썼다** — 기본 넷(주소·PID·스레드 id·시간)에 걸리는 칸이 애초에 없었다.

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `api0.kt` · `api1.kt` · `Calls.java` · `grid39.py` | ★★★ Java 에서 부르기 격자 — 같은 Java 소스, 두 판 | `kotlinc` 2회 → `javac` 2회(실패가 결과) · 스크립트가 `javac` 2회 |
| 같은 두 판 | ★★ 무엇이 생기고 사라졌나 | `javap -p` 2회 |
| `Use39.java` | 붙인 판의 짧은·긴 모양이 실제로 돈다 | `javac` → `java` |
| `jov.kt` · `JMid.java` | ★★ 오버로드 개수 · 가운데 기본값 | `kotlinc` → `javap -p` → `javac` → `java` |
| `bad39.kt` | 달 수 없는 자리 여섯 | `kotlinc`(실패가 결과) |
| `facade.kt` | 파일 facade 기본 이름 | `kotlinc` → `ls` |
| `form39.kt` | 형태 한 벌 | `kotlinc` → `java` |

**구현 의존 항목** — `$default` 합성 메서드와 그 서명 · 파일 facade 기본 이름 · 가운데 기본값에서 뗀 매개변수 · 진단 문구 — 이 컴파일러·판의 산출물이다.\
반면 **「`@JvmStatic` 이 정적 메서드를 만든다(동반 객체면 인스턴스 판도)」「`@JvmOverloads` 가 기본값마다 오버로드를 만든다」「`@JvmField` 가 필드를 공개한다」「`@JvmName` 이 JVM 이름을 바꾼다」** 는 **애너테이션의 계약**이다.

**★ 던져 봤더니 예상과 달랐던 것 — 세 건**

1. ★★★ **`object` 의 `@JvmStatic` 은 인스턴스 메서드를 남기지 않았다** — 「`@JvmStatic` 은 메서드를 둘 만든다」는 **동반 객체**에만 맞다(3번). 그런데도 `Reg.INSTANCE.ping()` 이 통과해 **격자만 보면 「남았다」로 오해할 뻔했다**(7번).
2. ★★ **가운데 기본값의 오버로드가 문서 문장과 달랐다** — `mid(String)` 이 아니라 `mid(String, String)`(8번).
3. ★ **`@JvmField` 의 「`val` + 게터」 에러가 「적용 대상이 아니다」였다** — 「커스텀 접근자에는 못 단다」가 나올 줄 알았는데 그 문구는 **필드가 있는** `var` + 세터 쪽에서 나왔다(11번).
