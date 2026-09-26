# kotlin/syntax/39 — Java 상호운용 애너테이션 — `@JvmStatic`/`@JvmOverloads`/`@JvmName`/`@JvmField`/`@Throws` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Calling Kotlin from Java](https://kotlinlang.org/docs/java-to-kotlin-interop.html)(`@JvmOverloads` — 「For every parameter with a default value, this generates one additional overload, which has this parameter and all parameters to the right of it in the parameter list removed.」 · `@JvmField` 를 달 수 있는 조건 — 「has a backing field · is not private · does not have `open`, `override` or `const` modifiers · is not a delegated property」 · `@JvmStatic` — 이름 있는 `object` 에서는 「doesn't generate a separate instance method」, `companion object` 에서는 바깥 클래스의 정적 메서드와 **동반 객체의 인스턴스 메서드를 둘 다** · 파일 facade 의 `@JvmName` · `@Throws`).
> **실행 검증** — 이 문서의 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javac`·`java`·`javap` 에서 실제로 얻었다.\
> `kotlinc` 6회(컴파일 실패 1벌) · `javac` 4회(실패가 결과인 것 2벌) + 격자 스크립트 안에서 2회 · `java` 3회 · `javap` 3회.\
> ★★ 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적지 않았다. **「갈린 칸 N / M」은 스크립트가 스스로 센 것**이다.
> **버전** — 다섯 애너테이션 전부 **1.0** 부터 있다. 이 판에서 버전에 갈리는 칸은 **없다**(격자는 한 판만 돌렸다).
> **경계** — ★★★ **이미 잰 것은 다시 재지 않는다** —\
> `@Throws` 는 [34번 주제](../34-exceptions-nothing-and-try-expression/) (2)가 쟀다 — 없으면 Java `catch` 가 「`exception IOException is never thrown in body`」로 막히고, 달면 `javap -v` 에 **`Exceptions:` 속성**이 생기며 이번엔 **안 잡으면** 「`unreported exception`」이다. 여기서는 **인용만** 한다.\
> `value class` 를 받는 함수의 **뭉개진 이름을 `@JvmName` 으로 풀면** Java 가 `long` 을 직접 넘겨 `init` 의 `require` 가 **한 번도 안 도는 것**(`named#-1`)은 [26번 주제](../26-value-class-and-boxing/) (5)가 쟀다.\
> `object` 가 `INSTANCE` 필드가 되고 `companion object` 가 `Outer$Companion` 클래스가 되는 것, Java 에서 부를 때의 `javac` 에러 두 종은 [25번 주제](../25-object-declaration-companion-and-object-expression/) (1)(3)이 정본이다 — 여기서는 그것을 **격자의 한 행**으로만 다시 놓는다.\
> 애너테이션이 필드·게터·매개변수 중 **어디에 붙나**는 [35번 주제](../35-annotations-and-use-site-targets/)다.\
> 상호운용의 **실제 비용**(JUnit5 `@MethodSource` 가 정적 팩토리를 요구하는 마찰 등)은 [`../../언어-특성/README.md`](../../언어-특성/README.md) §9 가, **Spring 맥락**(final 클래스와 all-open)은 [`history/spring/kotlin-and-spring.md`](../../../../../../history/spring/kotlin-and-spring.md) 가 정본이다. 여기는 **애너테이션 하나하나가 바이트코드에서 무엇을 바꾸나**다.
> 이 본문은 Claude 작성이다(원고 없음).

★★★ **본체는 첫째 창이다** — 「**Java 에서 부르기 격자 — 같은 Java 소스를 애너테이션 없는 판 / 있는 판에 `javac` 로 던진다**」. 이 애너테이션들은 **Kotlin 쪽에서는 아무것도 안 바꾼다** — 차이는 **Java 가 컴파일되느냐**로만 보인다. 둘째 창(`javap -p`)이 **왜** 갈렸는지를 보인다.

## 이 주제가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **언어 보장(애너테이션의 계약)** | 문서가 약속한 것 | ★★ `@JvmStatic` — 정적 메서드를 만든다(동반 객체면 **인스턴스 메서드도 남는다**) · `@JvmOverloads` — 기본값마다 오버로드 · `@JvmField` — 게터 대신 **필드를 공개** · `@JvmName` — **JVM 이름**을 바꾼다 · `@JvmField`·`@JvmStatic`·`@JvmOverloads` 를 **달 수 없는 자리** |
| **구현(JVM 백엔드)** | kotlinc 가 JVM 으로 내리는 방식 | ★★ 기본값의 **`greet$default`** 합성 메서드 · 파일 facade 기본 이름 **`FacadeKt`** · 오버로드가 **어느 매개변수를 빼는가**의 실제 모양 |
| **이 판의 관찰** | kotlinc 2.4.20 · javac 21 에서 본 것 | ★ 진단 문구 · ★ **가운데만 기본값인 함수의 오버로드 모양**(문서 문장과 다르다 — (3)) |

★★ **`javap` 서명은 백엔드 구현이면서 동시에 애너테이션의 계약이다** — `@JvmStatic` 을 달았는데 정적 메서드가 안 생기면 계약 위반이다. 그래서 이 주제의 `javap` 는 「구현의 우연」이 아니라 **계약을 확인하는 창**으로 읽는다. 다만 **합성 메서드의 이름·모양**(`greet$default`)은 계약 밖이다.

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
| **흔들린다** | (이 주제에는 없다) | 해시코드·주소·시간을 찍지 않았다 |
| 안 흔들린다 | 격자 10행 · 갈린 수 | 같은 소스·같은 컴파일러면 결정적이다 |
| 안 흔들린다 | `javap -p` 출력(멤버 순서까지) · `javac`·`kotlinc` 진단 문구·줄 번호 · 종료 코드 | 결정적이다 |

★ 근거 — 캡처 스크립트를 처음부터 두 번 돌려 **블록 전체를 바이트 단위로 대조**했다(수치는 3-answer 의 「실행 검증」).

## 한눈에 — 쉽게 말하면

**Kotlin 클래스를 Java 에게 내보내는 것은 「외국어 안내판을 다는 일」이다.** Kotlin 사람끼리는 `Box.make()`·`box.size`·`greet("a")` 로 통하지만, Java 가 읽는 것은 **클래스 파일에 실제로 있는 이름과 서명**이다. 안내판이 없으면 Java 는 `Box.Companion.make()`·`box.getSize()`·`greet("a", 1, "c")` 처럼 **긴 길**로 돌아가야 한다.
애너테이션은 **안내판을 하나 더 다는 것**이다 — `@JvmStatic` 은 정문에 창구를, `@JvmOverloads` 는 짧은 문을, `@JvmField` 는 **복도 대신 방문 자체를 연다.**
★ 그런데 **어떤 안내판은 옛 길을 없앤다** — `@JvmField` 를 달면 `getSize()` 가, `@JvmName` 을 달면 옛 이름이 **사라진다.** 이미 옛 길로 다니던 Java 코드는 컴파일이 깨진다.

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 긴 길(관리실을 거쳐 간다) | `Box.Companion.make()` · `Reg.INSTANCE.ping()` | (1) · [25번 주제](../25-object-declaration-companion-and-object-expression/) |
| 정문에 창구를 하나 더 | `@JvmStatic` — 정적 메서드 **추가** | (1)(2) |
| 짧은 문을 기본값마다 | `@JvmOverloads` | (1)(3) |
| 복도 대신 방문을 연다 | `@JvmField` — 필드 공개, **게터 없음** | (1)(2) ★ |
| 문패를 바꿔 단다 | `@JvmName` — 옛 이름 **없음** | (1)(2) ★ |
| 반입 신고서 | `@Throws` → `Exceptions:` | [34번 주제](../34-exceptions-nothing-and-try-expression/) (2) |

```text
   Kotlin 선언                    애너테이션 없음 (Java 가 쓰는 모양)   붙이면 (Java 가 쓰는 모양)
   companion { fun make() }       Box.Companion.make()                Box.make()  + Box.Companion.make()  둘 다
   object Reg { fun ping() }      Reg.INSTANCE.ping()                 Reg.ping()  (INSTANCE 경유도 컴파일된다)
   fun greet(a, b = 1, c = "c")   greet(a, b, c) 하나                  greet(a) · greet(a, b) · greet(a, b, c)
   val size: Int = 3              box.getSize()                       box.size     ★ getSize() 는 사라진다
   fun original()                 Api.original()                      Api.renamed() ★ original() 은 사라진다
```

## 이 주제가 답하려는 질문

1. 애너테이션을 **안 달면** Java 는 Kotlin API 를 어떤 모양으로 불러야 하나 — **달면** 무엇이 새로 되고, **무엇이 안 되게** 되나.
2. `@JvmOverloads` 는 오버로드를 **몇 개**, **어떤 모양**으로 만드나 — 기본값이 가운데에만 있으면.
3. 각 애너테이션을 **달 수 없는 자리**는 어디인가.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **Java 에서 부르기 격자(`javac`)** | 같은 Java 소스 10줄이 **두 판**에서 각각 컴파일되나((1)) | ★ **본체 창** |
| ★★ **`javap -p` 두 판 대조** | 무엇이 **생기고 사라졌나**((2)) | 이 갈래의 기본 창 |
| ★★ **`javap -p` — 오버로드 세기** | 기본값 위치에 따라 몇 개 · 어떤 모양((3)) | — |
| ★ **`kotlinc` 에러** | 달 수 없는 자리((4)) | 이 갈래의 기본 창 |
| ★ **실행** | 만들어진 오버로드·정적 메서드가 **실제로 돈다**((2)(3)) | — |
| **인용 — 다시 안 잰다** | `@Throws` 의 `Exceptions:` · `@JvmName` 이 value class 의 `init` 을 건너뛰는 것 | [34번 주제](../34-exceptions-nothing-and-try-expression/) (2) · [26번 주제](../26-value-class-and-boxing/) (5) |
| **부적용 — 실행 시간·할당** | 정적 메서드가 `Companion` 경유보다 빠르다 같은 주장은 **재지 않았다** | — |

### (1) ★★★ Java 에서 부르기 격자 — 같은 Java 소스, 두 판

**언제 쓰나** — Kotlin 으로 만든 라이브러리를 Java 모듈이 쓸 때, 또는 **이미 Java 가 쓰는 API 에 애너테이션을 더할 때**.

두 Kotlin 파일은 **애너테이션만** 다르다 — 클래스 이름·멤버 이름은 같다. ★ 두 파일 모두 첫 줄에 `@file:JvmName("Api")` 를 둬 **최상위 함수가 사는 클래스 이름을 같게** 만들었다(그래야 한 Java 소스로 두 판을 잰다 — 이 애너테이션 자체는 (2)에서 따로 본다).

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

Java 쪽은 **짧은 모양과 긴 모양을 한 줄씩** 부른다.

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

**애너테이션 없는 판에 던지면**

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

**붙인 판에 던지면**

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

격자 스크립트 — 두 판에 `javac` 를 각각 부르고 `Calls.java:N: error:` 줄로 **줄마다** 판정한다.

```python
# grid39.py
import re
import subprocess
import sys

LABELS = {
    3: ("companion fn", "Box.make()"),
    4: ("companion fn", "Box.Companion.make()"),
    5: ("object fn", "Reg.ping()"),
    6: ("object fn", "Reg.INSTANCE.ping()"),
    7: ("default args", "greet(\"a\")"),
    8: ("default args", "greet(\"a\", 1, \"c\")"),
    9: ("property", "box.size"),
    10: ("property", "box.getSize()"),
    11: ("@JvmName fn", "Api.renamed()"),
    12: ("@JvmName fn", "Api.original()"),
}
ERR = re.compile(r"^Calls\.java:(\d+): error: (.*)$")


def compile_against(d):
    p = subprocess.run(["javac", "-cp", d, "-d", d + "-calls", "Calls.java"],
                       capture_output=True, text=True)
    bad = {}
    for line in (p.stdout + p.stderr).splitlines():
        m = ERR.match(line)
        if m:
            bad[int(m.group(1))] = m.group(2)
    return bad


a_dir, b_dir = sys.argv[1], sys.argv[2]
a, b = compile_against(a_dir), compile_against(b_dir)
print("\t".join(["subject", "Java call", a_dir, b_dir, ""]))
diff = total = 0
for ln, (subj, call) in LABELS.items():
    ca = "error: " + a[ln] if ln in a else "ok"
    cb = "error: " + b[ln] if ln in b else "ok"
    total += 1
    mark = ""
    if (ln in a) != (ln in b):
        diff += 1
        mark = "<-"
    row = [subj, call, ca, cb, mark]
    if len(row) != 5 or any("\t" in c for c in row):
        raise SystemExit("cell count mismatch: " + repr(row))
    print("\t".join(row))
print(f"calls whose result differs: {diff} / {total}")
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

- ★★★ **갈린 줄 7 / 10.** 짧은 모양 다섯은 **없는 판에서 전부 막히고 붙인 판에서 전부 통과**한다. 에러는 **네 종류**로 갈린다 — 이름째 없음(「`cannot find symbol`」 — `make`·`renamed`) · 있는데 정적이 아님(「`non-static method ping() cannot be referenced from a static context`」) · 인자 수 불일치(「`actual and formal argument lists differ in length`」) · 접근 불가(「`size has private access in Box`」).
- ★★★ **긴 모양 다섯 중 둘은 붙인 판에서 막힌다** — `box.getSize()`(`@JvmField`)와 `Api.original()`(`@JvmName`). **이 둘은 추가가 아니라 교체**다. 이미 긴 모양으로 부르던 Java 코드가 있으면 **애너테이션 하나가 그 코드를 깨뜨린다.**
- ★★ **나머지 셋은 추가다** — `Box.Companion.make()`·`Reg.INSTANCE.ping()`·`greet("a", 1, "c")` 는 붙인 판에서도 **그대로 통과**한다.

### (2) ★★ `javap -p` — 무엇이 생기고, 무엇이 사라졌나

**애너테이션 없음**

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

**붙임**

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

```text
   애너테이션         없음                                   붙임                                          추가 / 교체
   @JvmStatic         Box$Companion.make()  (인스턴스)          Box$Companion.make()  (인스턴스)  ← 남는다        추가
    (companion)                                              Box.make()  public static final   ← 새로 생김
   @JvmStatic         Reg.ping()  (인스턴스)                    Reg.ping()  public static final   ← 바뀜          (인스턴스 판 없음)
    (object)
   @JvmOverloads      greet(String,int,String) + greet$default  + greet(String,int) + greet(String)           추가
   @JvmField          private final int size + getSize()      public final int size  (게터 없음)             교체
   @JvmName           Api.original()                          Api.renamed()                                교체
```

- ★★★ **동반 객체의 `@JvmStatic` 은 메서드를 둘로 만든다** — `Box$Companion` 의 **인스턴스 메서드 `make()` 가 남고**, 바깥 `Box` 에 **`public static final make()`** 가 더 생긴다. 그래서 `Box.Companion.make()` 가 계속 된다([25번 주제](../25-object-declaration-companion-and-object-expression/) (3)의 결론과 같다).
- ★★★ **`object` 의 `@JvmStatic` 은 하나뿐이다** — `Reg.ping()` 이 **인스턴스 메서드에서 정적 메서드로 바뀌었다.** 인스턴스 판은 **남지 않는다**(문서: 「doesn't generate a separate instance method」). 그런데도 `Reg.INSTANCE.ping()` 이 컴파일되는 것은 **Java 가 인스턴스 식으로 정적 메서드를 부르는 것을 허용**하기 때문이다(`javac` 의 규칙이지 Kotlin 이 남긴 것이 아니다).
- ★★★ **`@JvmField` 는 게터를 없애고 필드를 공개한다** — `private final int size` + `getSize()` 가 **`public final int size` 하나**가 됐다. 공개 **여부**만 바뀐 것이 아니라 **메서드 하나가 사라졌다.** 필드의 `final` 은 그대로다(`val` 이므로).
- ★★ **`@JvmName` 은 이름을 바꿀 뿐 별칭을 남기지 않는다** — `Api` 에 `renamed()` 만 있다.
- ★★ **`@JvmOverloads` 를 달아도 `greet$default` 는 그대로 있다** — 기본값을 채우는 실제 일은 그 합성 메서드가 하고, 새 오버로드는 그것을 부르는 **입구**다(몸통은 재지 않았다 — 개수와 서명만 봤다).
- ★ `Use39` 가 붙인 판의 **짧은 모양과 긴 모양을 전부** 불러 같은 값을 얻었다(`make make` · `ping ping`).

**파일 facade 의 기본 이름** — `@file:JvmName` 이 없으면.

```kotlin
// facade.kt
fun hello(): String = "hello"
```

```text
===== kotlinc facade.kt -d o39f =====
(exit 0)
===== ls o39f | grep -v META-INF =====
FacadeKt.class
(exit 0)
```

- ★ **`facade.kt` → `FacadeKt`** — 파일 이름 + `Kt`. (1)의 `Api` 는 `@file:JvmName("Api")` 가 바꾼 이름이다. **파일 이름을 바꾸면 Java 쪽 클래스 이름이 바뀐다**는 뜻이기도 하다.

### (3) ★★ `@JvmOverloads` — 몇 개, 어떤 모양

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

| 함수 | 기본값 | 원래 + `$default` | 더 생긴 오버로드 | 모양 |
|---|---|---|---|---|
| `tail2(a, b = 1, c = "c")` | 뒤쪽 둘 | 1 + 1 | **2** | `(String, int)` · `(String)` |
| `all3(a = …, b = …, c = …)` | 셋 전부 | 1 + 1 | **3** | `(String, int)` · `(String)` · `()` |
| `mid(a, b = 1, c)` | ★ 가운데 하나 | 1 + 1 | **1** | ★ **`(String, String)`** |
| `none(…)` — 애너테이션 없음 | 뒤쪽 둘 | 1 + 1 | **0** | — |

- ★★★ **기본값 수만큼 더 생긴다** — 2 · 3 · 1 · (없으면) 0. 뒤에서부터 **하나씩** 뗀 모양이다.
- ★★★ **가운데만 기본값이면 `mid(String, String)`** — `b` 만 빠지고 **기본값 없는 `c` 는 남는다.** Java 에서 `JovKt.mid("a", "z")` 가 `a1z` 를 돌려줬다.
  ★ **문서 문장과 글자대로는 안 맞는다** — 문서는 「this parameter and **all parameters to the right of it** … removed」라고 적는데, 글자대로면 `mid(String)` 이어야 한다. 실제는 **기본값 있는 매개변수만** 뺐다. 문장을 「그 오른쪽의 **기본값 있는** 매개변수」로 읽어야 이 판의 결과와 맞는다(**이 판의 관찰**).
- ★★ **애너테이션이 없으면 `none` 도 `none$default` 는 있다** — Java 는 그것을 부를 수 없는 것이 아니라 **부르면 안 되는 것**(합성 메서드 · 비트마스크 인자)이고, Java 가 쓸 입구는 **3인자 판 하나뿐**이다((1)의 `greet("a")` 에러).

### (4) ★ 달 수 없는 자리

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

- ★★★ **`val` + 커스텀 게터** — 「`this annotation is not applicable to target 'member property without backing field or delegate'. Applicable targets: field`」. 게터만 있고 **필드가 없으니** 공개할 필드가 없다. `@JvmField` 의 대상이 **필드**라는 것이 문구에 그대로 있다.
- ★★ **`var` + 커스텀 세터** — 필드는 있지만 「`jvmField cannot be applied to a property with a custom accessor.`」. 필드를 공개하면 **세터를 우회**하므로 막는다.
- ★★ **`private`** — 「`jvmField has no effect on a private property.`」 · **`open`** — 「`jvmField can only be applied to final property.`」(문서의 조건 목록과 한 줄씩 대응한다).
- ★ **일반 클래스 멤버의 `@JvmStatic`** — 「`only members in named objects and companion objects can be annotated with '@JvmStatic'.`」 — 정적으로 만들 **싱글턴 인스턴스**가 없다.
- ★ **인터페이스 메서드의 `@JvmOverloads`** — 「`'@JvmOverloads' annotation cannot be used on interface methods.`」.

## 문법 — 형태와 규칙

**형태** — Java 에서도 쓸 값 타입 하나.

```kotlin
// form39.kt
@file:JvmName("Money")

class Won(@JvmField val amount: Long) {
    companion object {
        @JvmStatic fun of(amount: Long): Won = Won(amount)
    }
    @JvmOverloads
    fun format(sep: String = ",", unit: String = "원"): String =
        amount.toString().reversed().chunked(3).joinToString(sep).reversed() + unit
}

@JvmName("sumAll")
fun sum(xs: List<Won>): Won = Won(xs.sumOf { it.amount })

fun main() {
    val w = sum(listOf(Won.of(1200), Won.of(34000)))
    println(w.format())
    println(w.format("_"))
}
```

```text
===== kotlinc form39.kt -d o39z =====
(exit 0)
===== java -cp o39z:kotlin-stdlib.jar Money =====
35,200원
35_200원
(exit 0)
```

**규칙 불릿**

- **`@JvmStatic`** — `object`·`companion object` 멤버에만. 동반 객체면 **정적 + 인스턴스 둘**, `object` 면 **정적 하나**((2)(4)).
- **`@JvmOverloads`** — 기본값 수만큼 오버로드. **인터페이스 메서드는 안 된다**((3)(4)).
- **`@JvmField`** — 백킹 필드가 있고 `private`·`open`·커스텀 접근자가 아닌 프로퍼티에만. **게터·세터가 사라진다**((2)(4)).
- **`@JvmName("…")`** — 함수·접근자의 JVM 이름을 바꾼다. **옛 이름은 안 남는다**((2)). 파일 첫 줄의 **`@file:JvmName`** 은 facade 클래스 이름((2)).
- **`@Throws(X::class)`** — Java 에게 검사 예외를 알린다 → [34번 주제](../34-exceptions-nothing-and-try-expression/) (2).
- ★ **Kotlin 호출자에게는 다섯 다 아무 효과가 없다** — 바뀌는 것은 **Java 가 보는 클래스 파일**뿐이다.

## 어디서 틀리나

1. ★★★ **이미 Java 가 쓰는 프로퍼티에 `@JvmField` 를 더한다.** `getX()` 가 **사라져** Java 호출자가 「`cannot find symbol`」로 깨진다((1)(2)).
2. ★★★ **이미 Java 가 쓰는 함수에 `@JvmName` 을 더한다.** 옛 이름이 **사라진다**((1)(2)).
3. ★★ **`@JvmStatic` 을 달면 `Companion` 경유가 사라진다고 믿는다.** 동반 객체면 **남는다**((2)) — 그리고 `object` 면 인스턴스 판이 **정말 없다**(Java 의 `INSTANCE.ping()` 은 javac 가 허용할 뿐이다).
4. ★★ **`@JvmOverloads` 가 모든 조합을 만든다고 믿는다.** 기본값마다 **하나씩**, 뒤에서부터다((3)) — `greet(a, c)` 같은 건너뛴 조합은 없다.
5. ★★ **가운데 기본값의 오버로드를 문서 문장대로 예측한다.** 이 판은 `mid(String, String)` 이다((3)).
6. ★ **`@JvmField` 로 계산 프로퍼티를 공개하려 한다.** 필드가 없어 막힌다((4)).
7. ★ **value class 를 받는 함수에 `@JvmName` 을 달고 안심한다.** Java 가 알맹이를 직접 넘겨 **`init` 검사를 건너뛴다** — [26번 주제](../26-value-class-and-boxing/) (5).

## 구현 세부사항 대 언어 보장

| 항목 | 어느 쪽인가 | 근거 |
|---|---|---|
| `@JvmStatic` 이 정적 메서드를 만든다 · 동반 객체면 인스턴스 판이 남는다 · `object` 면 안 남는다 | ★★ **애너테이션의 계약**(문서) | (2) |
| `@JvmOverloads` 가 기본값마다 오버로드를 만든다 | ★★ **애너테이션의 계약** | (3) |
| ★ 가운데 기본값에서 **어느 매개변수를 빼나** | **이 판의 관찰** — 문서 문장과 글자대로는 다르다 | (3) |
| `@JvmField` 가 필드를 공개하고 접근자를 없앤다 · 달 수 있는 조건 | ★★ **애너테이션의 계약** | (2)(4) |
| `@JvmName` 이 JVM 이름을 바꾼다 | **애너테이션의 계약** | (2) |
| 파일 facade 기본 이름 `<파일>Kt` | **JVM 백엔드의 구현**(상호운용 문서에 적혀 있다) | (2) |
| `greet$default` 합성 메서드와 그 서명 | ★ **JVM 백엔드의 구현** — 계약 밖 | (2)(3) |
| `Reg.INSTANCE.ping()` 이 정적 메서드인데도 컴파일되는 것 | **Java 언어의 규칙**(Kotlin 과 무관) | (1)(2) |
| 진단 문구 | **이 판(kotlinc 2.4.20 · javac 21)의 산출물** | (1)(4) |

★★ **가장 조심할 자리** — 「애너테이션을 달면 Java 쪽이 **편해진다**」는 반만 맞다. `@JvmStatic`·`@JvmOverloads` 는 **추가**라 기존 Java 코드가 안 깨지지만, **`@JvmField`·`@JvmName` 은 교체**라 깨진다((1)의 7 / 10 중 둘). 공개 API 에서는 **처음 낼 때** 정하는 것이 싸다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| Java 가 `Foo.create()` 처럼 정적으로 부를 팩토리 | ★ `companion object` + `@JvmStatic` | (2) — `Companion` 경유도 남아 기존 코드가 안 깨진다 |
| JUnit5 `@MethodSource` 처럼 **정적**을 요구하는 도구 | `@JvmStatic` | [`../../언어-특성/README.md`](../../언어-특성/README.md) §9 의 형태 A |
| 기본값 많은 함수를 Java 도 부른다 | ★ `@JvmOverloads` | (3) — 없으면 Java 는 전부 넘겨야 한다 |
| 상수·DTO 필드를 Java 가 필드로 읽어야 한다(직렬화기 등) | `@JvmField`(상수면 `const`) | (2) — ★ **처음부터** 달아야 한다 |
| 이미 Java 가 `getX()` 로 쓰는 프로퍼티 | **달지 않는다** | (1) — 교체라 깨진다 |
| JVM 서명이 충돌한다(제네릭 소거 등) · value class 로 이름이 뭉개진다 | `@JvmName` | [26번 주제](../26-value-class-and-boxing/) (5) — ★ 방어선이 열리는 것까지 알고 |
| Java 가 잡아야 할 검사 예외 | `@Throws` | [34번 주제](../34-exceptions-nothing-and-try-expression/) (2) |
| Spring 이 클래스를 `open` 으로 요구한다 | 애너테이션이 아니라 **컴파일러 플러그인**(all-open) | [`history/spring/kotlin-and-spring.md`](../../../../../../history/spring/kotlin-and-spring.md) · [`../../언어-특성/README.md`](../../언어-특성/README.md) §9 |

## 핵심 문장

1. 이 애너테이션들은 **Kotlin 호출자에게는 아무것도 안 바꾼다** — Java 가 보는 **클래스 파일의 이름과 서명**만 바꾼다.
2. 같은 Java 10줄을 두 판에 던지면 **7줄이 갈린다** — 짧은 모양 다섯이 새로 되고, 긴 모양 중 **`getSize()`·`original()` 둘이 사라진다.**
3. `@JvmStatic`·`@JvmOverloads` 는 **추가**, `@JvmField`·`@JvmName` 은 **교체**다 — 뒤의 둘은 기존 Java 코드를 깨뜨린다.
4. 동반 객체의 `@JvmStatic` 은 **메서드 둘**(정적 + 인스턴스), `object` 의 `@JvmStatic` 은 **하나**(정적)다.
5. `@JvmOverloads` 는 기본값마다 **하나씩** 만든다 — 가운데만 기본값이면 **그것만 빼고 뒤의 필수 인자는 남긴다**(`mid(String, String)`).

## 관련 자료

- [25번 주제](../25-object-declaration-companion-and-object-expression/) — ★★ **선행.** `object` 가 `INSTANCE`, `companion object` 가 `Outer$Companion` 인 것 · Java 에서 부를 때의 두 에러. 그쪽은 「`object` 를 Java 에서 부르는 데 필요한 만큼」까지, 여기는 **다섯 애너테이션을 한 격자에서**.
- [34번 주제](../34-exceptions-nothing-and-try-expression/) — ★★ **선행.** `@Throws` 는 거기서 쟀다.
- [26번 주제](../26-value-class-and-boxing/) (5) — `@JvmName` 이 value class 의 방어선을 여는 것.
- [35번 주제](../35-annotations-and-use-site-targets/) — 애너테이션이 **어디에** 붙나(`@field:`·`@get:`).
- [08번 주제](../08-function-declaration-default-and-named-args/) — 기본 인자가 Java 에서 사라지는 것.
- [`../../언어-특성/README.md`](../../언어-특성/README.md) §9 — 상호운용의 **실제 비용** · 그쪽은 「왜 마찰이 생기나」, 여기는 「애너테이션 하나가 서명을 어떻게 바꾸나」.
- [`history/spring/kotlin-and-spring.md`](../../../../../../history/spring/kotlin-and-spring.md) — Spring 과 쓸 때의 맥락(all-open · 혼용).

## 용어 풀이

> **`@JvmStatic`** — `object`·`companion object` 의 멤버를 **JVM 정적 메서드**로도 내는 애너테이션.

> **`@JvmOverloads`** — 기본값 있는 함수에 **Java 용 오버로드**를 만들어 주는 애너테이션.

> **`@JvmField`** — 프로퍼티를 게터·세터 없이 **공개 필드**로 내는 애너테이션.

> **`@JvmName`** — 함수·접근자·파일 facade 의 **JVM 이름**을 바꾸는 애너테이션.\
> 예: `@file:JvmName("Money")` · `@JvmName("sumAll") fun sum(…)`.

> **파일 facade** — 최상위 함수·프로퍼티가 모이는 JVM 클래스. 기본 이름은 `<파일이름>Kt`.

> **`$default` 합성 메서드** — 기본 인자를 채워 부르기 위해 컴파일러가 만드는 메서드. 어느 인자가 생략됐는지를 **비트마스크 `int`** 로 받는다.

> **추가 / 교체** — 이 문서의 말. 애너테이션이 **옛 모양을 남기고 새 모양을 더하나**(추가), **옛 모양을 없애나**(교체).

## 더 들어가면

- **`@JvmOverloads` 오버로드의 몸통** — 새 오버로드가 `$default` 를 부르는지, 값을 직접 채워 원래 메서드를 부르는지는 `javap -c` 로 **재지 않았다.** 개수와 서명만 봤다.
- **`@JvmName` 으로 게터 이름 바꾸기**(`@get:JvmName("isOpen")`) · **`@JvmMultifileClass`** — 문서가 적는 형태다. 이 문서는 **던지지 않았다.**
- **생성자의 `@JvmOverloads`**(`class A @JvmOverloads constructor(…)`) — 같은 규칙일 것으로 보이지만 **던지지 않았다.**
