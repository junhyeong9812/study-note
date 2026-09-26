# kotlin/syntax/35 — 애너테이션과 use-site target (`@field:`·`@get:`·`@param:`) — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Annotations — use-site targets](https://kotlinlang.org/docs/annotations.html#annotation-use-site-targets)(대상 목록 `file`·`field`·`property`·`get`·`set`·`all`·`receiver`·`param`·`setparam`·`delegate` · 「`property` (annotations with this target are not visible to Java)」 · 기본 규칙 「param → property → field(property 가 안 될 때)」) · [What's new in Kotlin 2.2.0](https://kotlinlang.org/docs/whatsnew22.html)(새 기본 규칙과 `@all` 이 **미리보기**로 들어온 판 · `-Xannotation-default-target=param-property`) · [What's new in Kotlin 2.4.0](https://kotlinlang.org/docs/whatsnew24.html)(「`@all` meta-target for properties」·「New defaulting rules for use-site annotation targets」가 **Stable**).
> **실행 검증** — 이 문서의 모든 출력·에러·경고·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javac`·`java`·`javap` 에서 실제로 얻었다. C# 은 **.NET SDK 10.0.401** 의 Roslyn `csc` 를 직접 불렀다.\
> `kotlinc` 14회(`-X` 도움말 1회 · 실패 1벌) · `javac` 10회 · `java` 7회 + 격자 스크립트 안에서 4회 · `javap` 3회 · `csc` 1회 · `dotnet` 1회.\
> ★★ 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적지 않았다. 격자의 「갈린 칸 N / M」도 **스크립트가 세어 마지막 줄로 찍었다.**
> **버전** — ★★★ **이 주제의 답은 언어 판에 매인다.** target 없는 애너테이션의 기본 규칙이 **2.1 이하 `first-only` → 2.2·2.3 `first-only-warn` → 2.4 이상 `param-property`** 로 바뀌었다(`kotlinc -X` 의 문구 · (2)(6)). `@all:` 은 2.2 미리보기 → **2.4 Stable**((5)).
> **경계** — 프로퍼티가 **필드·게터·매개변수로 쪼개지는 것 자체**는 [16번 주제](../16-properties-backing-field-lateinit-const/)가, 값 클래스의 **이름 뭉개기**는 [26번 주제](../26-value-class-and-boxing/)가, `@delegate:` 가 붙는 위임 필드는 [17번 주제](../17-delegated-properties/)가 정본이다.\
> `@JvmField`·`@JvmName`·`@Throws` 같은 **상호운용 애너테이션**은 목록의 **39번 주제**다 — 여기는 「어디에 붙나」를 **아무 애너테이션에 대해** 다룬다.\
> ★ **대비** — C# 의 특성(attribute) 대상 지정자(`[field:]`·`[property:]`)는 C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **53번**이 정본인데 아직 폴더가 없다 — 이 문서가 **직접 던졌다**((7)).
> 이 본문은 Claude 작성이다(원고 없음).

★★★ **본체는 넷째 창이다** — 「**`javap -v` 의 `RuntimeVisibleAnnotations`/`RuntimeVisibleParameterAnnotations` 가 어느 멤버 아래에 있나**」. 애너테이션은 실행 결과를 바꾸지 않으므로 출력으로는 안 보이고, **클래스 파일의 자리**가 곧 답이다. 그 자리를 **Java 리플렉션으로 칸마다 물어 격자**로 만들었다((1)(2)).

## 이 주제가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **언어 보장** | 명세·공식 문서가 약속한 것 | ★★★ use-site target 목록과 뜻 · **target 없을 때의 선택 순서**(param → property → field) · 그 순서가 **언어 판마다** 하나만 고르나(`first-only`) 둘을 고르나(`param-property`) |
| **구현(JVM 백엔드)** | kotlinc 가 JVM 으로 내리는 방식 | ★★ `param` → **생성자의 `RuntimeVisibleParameterAnnotations`** · `field` → **필드** · `get` → **게터 메서드** · ★ `property` → **합성 메서드 `getV$annotations()`** · 값 클래스 게터의 **뭉개진 이름** |
| **이 판의 관찰** | kotlinc 2.4.20 에서 이번에 본 것 | 경고·에러 문구 · `-X` 도움말 문구 · `-Xannotation-target-all` 이 「redundant」라는 경고 |

★★★ **이 주제에서 층이 가장 헷갈리는 자리** — 「target 을 안 적으면 **어느 target** 이 고라지나」는 **언어 규칙**이다(판마다 다르다). 「그 target 이 **JVM 의 어느 멤버**가 되나」는 **백엔드의 구현**이다. `@property:` 가 `getV$annotations()` 라는 메서드가 되는 것은 후자다 — 언어는 「프로퍼티에 붙는다」만 약속한다.

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
| **흔들린다** | (이 주제에는 없다) | 해시코드·주소·시간을 **하나도 안 찍었다** |
| 안 흔들린다 | ★ 리플렉션 출력 — 멤버를 **이름으로 직접** 물었다 | `getDeclaredMethods()` 의 **순서**는 보장이 없으므로, 순서에 기대는 출력은 **한 줄로 모았다**(합성 메서드는 이름으로 골랐다) |
| 안 흔들린다 | `javap` 출력 · 뭉개진 이름의 해시 글자(`-DyZRee4`) | 같은 소스·같은 판이면 같다. ★ 해시 글자는 **판이 바뀌면 달라질 수 있어** 모양만 근거로 쓴다([26번 주제](../26-value-class-and-boxing/)) |
| 안 흔들린다 | 진단 문구 · 격자의 「갈린 칸 N / M」 | 결정적이다 |

★ 근거 — 캡처 스크립트를 처음부터 두 번 돌려 **블록 전체를 바이트 단위로 대조**했다(수치는 3-answer 의 「실행 검증」).

## 한눈에 — 쉽게 말하면

**Kotlin 의 프로퍼티 하나는 JVM 에서 「방 세 개」로 쪼개진다** — 생성자의 **매개변수**(현관), 값이 사는 **필드**(금고), 값을 꺼내 주는 **게터**(창구). 여기에 Kotlin 만 보는 **프로퍼티 자체**(등기부)가 하나 더 있다.
애너테이션은 **스티커**다. `@field:`·`@get:`·`@param:` 은 「**어느 방에 붙여라**」는 지시이고, **지시가 없으면 컴파일러가 방을 고른다.**
★ 그 **고르는 규칙이 판마다 달랐다** — 옛 판은 **현관 하나에만** 붙였고, 2.4 는 **현관 + (등기부 또는 금고)** 에 붙인다. 금고만 뒤지는 검사관(필드 기반 프레임워크)은 **현관에만 붙은 스티커를 못 본다** — 이것이 「오동작의 단골」이다.

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 현관 | 생성자 매개변수 — `@param:` | (1) |
| 금고 | backing field — `@field:` | (1) |
| 창구 | 게터 메서드 — `@get:` | (1) |
| 등기부 | Kotlin 프로퍼티 — `@property:` → ★ 합성 메서드 `getV$annotations()` | (3) |
| 지시 없는 스티커 | target 없음 — **판마다 다른 규칙** | (1)(2) |
| 금고만 뒤지는 검사관 | 필드만 읽는 검증기 | (4) |
| 모든 방에 붙이기 | `@all:` — 2.4 Stable | (5) |

```text
   class J0(@JT val v: Int)          ← Java 애너테이션 (FIELD·METHOD·PARAMETER 만 허용 — PROPERTY 가 없다)
   class K0(@KT val v: Int)          ← Kotlin 애너테이션 (PROPERTY 를 허용한다)

                         현관(param)   금고(field)   창구(getter)   등기부(getV$annotations)
   2.4 기본  J0              JT           JT ★            -                -
             K0              KT           -   ★            -               KT ★
   2.1/first J0              JT           -               -                -
             K0              KT           -               -                -

   ★ 2.4 규칙 = 「param 에 붙이고, 추가로 property 또는 field 중 첫째에도」
       J0 은 property 가 허용 안 되니 field 로 · K0 은 property 가 허용되니 property 로 — 금고는 여전히 비었다
```

## 이 주제가 답하려는 질문

1. target 을 적지 않은 애너테이션은 **어느 JVM 멤버**에 붙나 — 그리고 그 답이 **언어 판**에 따라 어떻게 바뀌었나.
2. `@field:`·`@get:`·`@param:`·`@property:`·`@all:` 은 각각 **클래스 파일의 어디**가 되나.
3. 「프레임워크가 애너테이션을 못 본다」는 사고는 **어느 칸에서** 나고, 이 판에서도 여전히 나나.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **`javap -v` 의 `RuntimeVisible…Annotations` 자리** | 애너테이션이 **어느 멤버 아래**에 기록됐나((1)(3)(5)) | ★ **본체 창** |
| ★★★ **Java 리플렉션 격자 — 판 두 벌을 칸마다 대조** | 매개변수·필드·게터·합성 메서드 **네 자리 × 아홉 클래스** — 「갈린 칸 N / 36」을 스크립트가 센다((2)) | 규칙 22 의 격자 |
| ★★ **필드만 읽는 검증기** | 「단골」 오동작이 **에러 없이 통과**하는 모양((4)) | 이 주제의 고유 창 |
| ★ **`kotlin-reflect`** | `@property:` 를 **Kotlin 쪽에서** 읽기((3)) | ★ 제5의 상태 — 같은 질문을 **다른 창으로** 물었다 |
| ★ **컴파일 경고** | 2.2·2.3 이 **바뀔 것을 예고**한 문구((6)) | 이 갈래의 기본 창 |
| ★ **C# 로 같은 모양** | `record` 위치 매개변수의 같은 함정((7)) | 대비 창 |
| **부적용 — 실행 출력** | 애너테이션은 **값을 바꾸지 않는다** — 붙은 자리를 묻지 않으면 출력에 아무 흔적이 없다 | — |
| **부적용 — 실행 시간** | 리플렉션 비용은 이 주제의 질문이 아니다 | — |

★★ **「`@property:` 는 Java 에서 안 보인다」를 브리핑은 「`kotlin-reflect` 가 없으면 못 잰 것」으로 예상했다.** 실제로는 ① `kotlin-reflect.jar` 가 `kotlinc` 배포본 `lib/` 에 **있었고**(3-answer 의 환경 블록), ② 그보다 먼저 **Java 리플렉션이 합성 메서드로 찾았다**((3)). 「못 잰 것」이 아니라 **두 창이 같은 답**을 냈다.

### (1) ★★★ 아홉 모양 — 어느 멤버에 붙나 (2.4.20 기본)

**언제 쓰나** — `@JsonProperty`·`@NotBlank`·`@Column` 을 주 생성자 `val` 에 붙이기 전에.

```java
// JT.java
import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

@Retention(RetentionPolicy.RUNTIME)
@Target({ElementType.FIELD, ElementType.METHOD, ElementType.PARAMETER})
public @interface JT {}
```

```kotlin
// sites.kt
@Target(
    AnnotationTarget.VALUE_PARAMETER, AnnotationTarget.PROPERTY,
    AnnotationTarget.FIELD, AnnotationTarget.PROPERTY_GETTER,
)
annotation class KT

class J0(@JT val v: Int)
class J1(@field:JT val v: Int)
class J2(@get:JT val v: Int)
class J3(@param:JT val v: Int)

class K0(@KT val v: Int)
class K1(@field:KT val v: Int)
class K2(@get:KT val v: Int)
class K3(@param:KT val v: Int)
class K4(@property:KT val v: Int)
```

```java
// Where.java
import java.lang.annotation.Annotation;
import java.lang.reflect.Method;

public class Where {
    static String mark(Annotation[] as) {
        StringBuilder sb = new StringBuilder();
        for (Annotation a : as) {
            String n = a.annotationType().getSimpleName();
            if (!n.equals("Metadata")) sb.append(n);
        }
        return sb.length() == 0 ? "-" : sb.toString();
    }

    public static void main(String[] args) throws Exception {
        for (String name : args) {
            Class<?> c = Class.forName(name);
            String param = mark(c.getDeclaredConstructors()[0].getParameterAnnotations()[0]);
            String field = mark(c.getDeclaredField("v").getDeclaredAnnotations());
            String getter = mark(c.getDeclaredMethod("getV").getDeclaredAnnotations());
            String extra = "-";
            for (Method m : c.getDeclaredMethods()) {
                if (m.getName().contains("$annotations")) extra = m.getName() + ":" + mark(m.getDeclaredAnnotations());
            }
            System.out.println(name + ";param=" + param + ";field=" + field + ";getter=" + getter + ";synthetic=" + extra);
        }
    }
}
```

```text
===== javac -d o35d JT.java =====
(exit 0)
===== kotlinc -cp o35d sites.kt -d o35d =====
(exit 0)
===== javac -d o35d Where.java =====
(exit 0)
===== java -cp o35d:kotlin-stdlib.jar Where J0 J1 J2 J3 K0 K1 K2 K3 K4 =====
J0;param=JT;field=JT;getter=-;synthetic=-
J1;param=-;field=JT;getter=-;synthetic=-
J2;param=-;field=-;getter=JT;synthetic=-
J3;param=JT;field=-;getter=-;synthetic=-
K0;param=KT;field=-;getter=-;synthetic=getV$annotations:KT
K1;param=-;field=KT;getter=-;synthetic=-
K2;param=-;field=-;getter=KT;synthetic=-
K3;param=KT;field=-;getter=-;synthetic=-
K4;param=-;field=-;getter=-;synthetic=getV$annotations:KT
(exit 0)
```

```text
===== javap -v -p o35d/J0.class o35d/K0.class o35d/K4.class | grep -E '^public final class|^  [a-z].*;$|^ +RuntimeVisible|^ +parameter [0-9]|^ +(JT|KT)$' =====
public final class J0
  private final int v;
    RuntimeVisibleAnnotations:
        JT
  public J0(int);
    RuntimeVisibleParameterAnnotations:
      parameter 0:
          JT
  public final int getV();
public final class K0
  private final int v;
  public K0(int);
    RuntimeVisibleParameterAnnotations:
      parameter 0:
          KT
  public final int getV();
  public static void getV$annotations();
    RuntimeVisibleAnnotations:
        KT
public final class K4
  private final int v;
  public K4(int);
  public final int getV();
  public static void getV$annotations();
    RuntimeVisibleAnnotations:
        KT
(exit 0)
```

```text
   소스(주 생성자 val)        JVM 멤버                                  javap -v 에서 애너테이션이 있는 자리
   @param:X    val v          생성자 매개변수 0 — public K(int);           RuntimeVisibleParameterAnnotations / parameter 0
   @field:X    val v          필드 — private final int v;                  필드 아래 RuntimeVisibleAnnotations
   @get:X      val v          게터 — public final int getV();              메서드 아래 RuntimeVisibleAnnotations
   @property:X val v          합성 — public static void getV$annotations(); 합성 메서드 아래 RuntimeVisibleAnnotations
   @all:X      val v          위 네 자리 중 X 의 @Target 이 허용하는 전부
   X           val v          판마다 다르다 — 2.1 이하 param 하나 · 2.4 는 param + (property 또는 field)
```

- ★★★ **`J0`(target 없음 · Java 애너테이션)은 매개변수 + 필드**다. `J0` 의 `javap` 에서 `JT` 가 **`private final int v;` 아래**(필드)와 **`public J0(int);` 의 `parameter 0:`**(생성자 매개변수) 두 곳에 있다. 게터에는 없다.
- ★★★ **`K0`(target 없음 · Kotlin 애너테이션)은 매개변수 + 합성 메서드**다. **필드에는 없다.** `KT` 가 `PROPERTY` 를 허용하므로 「property 또는 field 중 첫째」가 **property** 가 됐고, property 는 JVM 에서 **`getV$annotations()`** 라는 메서드에 기록된다.
- ★★ **같은 모양인데 답이 다르다** — 갈라 놓은 것은 소스가 아니라 **애너테이션 선언의 `@Target`** 이다. Java 애너테이션에는 `PROPERTY` 라는 대상이 **아예 없다**(Java 에 프로퍼티가 없으므로).
- ★ `J1`/`K1`(`@field:`) → 필드 하나 · `J2`/`K2`(`@get:`) → 게터 하나 · `J3`/`K3`(`@param:`) → 매개변수 하나 · `K4`(`@property:`) → 합성 메서드 하나. **target 을 적으면 판과 무관하게 한 자리**다((2)에서 확인).

### (2) ★★★ 판 격자 — 옛 기본 규칙과 칸마다 견주기

**언제 쓰나** — 「Kotlin 을 올렸더니 검증이 켜졌다/꺼졌다」를 설명할 때.

```text
===== kotlinc -X | awk '/^  -Xannotation-default-target/{f=6} f-->0; /^  -Xannotation-target-all/' =====
  -Xannotation-default-target=first-only|first-only-warn|param-property
                             Change the default annotation targets for constructor properties:
                             -Xannotation-default-target=first-only:      use the first of the following allowed targets: '@param:', '@property:', '@field:';
                             -Xannotation-default-target=first-only-warn: same as first-only, and raise warnings when both '@param:' and either '@property:' or '@field:' are allowed;
                             -Xannotation-default-target=param-property:  use '@param:' target if applicable, and also use the first of either '@property:' or '@field:';
                             default: 'param-property' in language version 2.4+, 'first-only-warn' in language versions 2.2 & 2.3, 'first-only' in version 2.1 and before.
  -Xannotation-target-all    Enable experimental language support for @all: annotation use-site target.
(exit 0)
```

```text
===== javac -d o35f JT.java =====
(exit 0)
===== kotlinc -Xannotation-default-target=first-only -cp o35f sites.kt -d o35f =====
warning: the argument '-Xannotation-default-target=first-only' disables a stable language feature for the current language version 2.4. Future support for this mode is not guaranteed.
(exit 0)
===== javac -d o35f Where.java =====
(exit 0)
===== python3 grid35.py o35d o35f =====
class place     o35d                        o35f
J0    param     JT                          JT
J0    field     JT                          -                             <-
J0    getter    -                           -
J0    synthetic -                           -
J1    param     -                           -
J1    field     JT                          JT
J1    getter    -                           -
J1    synthetic -                           -
J2    param     -                           -
J2    field     -                           -
J2    getter    JT                          JT
J2    synthetic -                           -
J3    param     JT                          JT
J3    field     -                           -
J3    getter    -                           -
J3    synthetic -                           -
K0    param     KT                          KT
K0    field     -                           -
K0    getter    -                           -
K0    synthetic getV$annotations:KT         -                             <-
K1    param     -                           -
K1    field     KT                          KT
K1    getter    -                           -
K1    synthetic -                           -
K2    param     -                           -
K2    field     -                           -
K2    getter    KT                          KT
K2    synthetic -                           -
K3    param     KT                          KT
K3    field     -                           -
K3    getter    -                           -
K3    synthetic -                           -
K4    param     -                           -
K4    field     -                           -
K4    getter    -                           -
K4    synthetic getV$annotations:KT         getV$annotations:KT
cells that differ: 2 / 36
(exit 0)
```

```python
# grid35.py
import subprocess
import sys

CLASSES = ["J0", "J1", "J2", "J3", "K0", "K1", "K2", "K3", "K4"]
PLACES = ["param", "field", "getter", "synthetic"]


def read(d):
    out = subprocess.run(["java", "-cp", d + ":kotlin-stdlib.jar", "Where", *CLASSES],
                         capture_output=True, text=True, check=True).stdout
    rows = {}
    for line in out.splitlines():
        cells = line.split(";")
        if len(cells) != 1 + len(PLACES):
            sys.exit("cell count mismatch: " + line)
        rows[cells[0]] = dict(c.split("=", 1) for c in cells[1:])
    return rows


a_dir, b_dir = sys.argv[1], sys.argv[2]
a, b = read(a_dir), read(b_dir)
print(f"{'class':<6}{'place':<10}{a_dir:<28}{b_dir}")
diff = total = 0
for c in CLASSES:
    for p in PLACES:
        total += 1
        mark = ""
        if a[c][p] != b[c][p]:
            diff += 1
            mark = "  <-"
        print(f"{c:<6}{p:<10}{a[c][p]:<28}{b[c][p]:<28}{mark}".rstrip())
print(f"cells that differ: {diff} / {total}")
```

- ★★★ **갈린 칸 2 / 36** — `J0 field`(2.4 에서 **새로 붙음**)와 `K0 synthetic`(2.4 에서 **새로 붙음**). 나머지 34칸은 **target 을 적은 일곱 클래스 전부 + 두 클래스의 나머지 칸**이다.
- ★★★ **옛 규칙(`first-only`)은 「param · property · field 중 첫째 하나」** 라 주 생성자 `val` 이면 **언제나 매개변수 하나**였다. 2.4 규칙(`param-property`)은 **매개변수에 더해** property/field 중 하나에도 붙인다 — `-X` 도움말이 「`use '@param:' target if applicable, and also use the first of either '@property:' or '@field:'`」로 적는다.
- ★★ **`-Xannotation-default-target=first-only` 에 경고가 붙는다** — 「`disables a stable language feature for the current language version 2.4.`」 옛 규칙은 이제 **언어 기능을 끄는 옵션**이다.
- ★ 격자 스크립트는 **행마다 칸 수를 세어 어긋나면 멈춘다**(규칙 32). 구분자는 데이터에 안 나오는 `;` 다.

**`-language-version 2.1` 도 같은가** — 옛 판을 직접 불렀다.

```text
===== javac -d o35l JT.java =====
(exit 0)
===== kotlinc -language-version 2.1 -cp o35l sites.kt -d o35l =====
warning: language version 2.1 is deprecated and its support will be removed in a future version of Kotlin. Update the version to 2.2.
(exit 0)
===== javac -d o35l Where.java =====
(exit 0)
===== python3 grid35.py o35f o35l =====
class place     o35f                        o35l
J0    param     JT                          JT
J0    field     -                           -
J0    getter    -                           -
J0    synthetic -                           -
J1    param     -                           -
J1    field     JT                          JT
J1    getter    -                           -
J1    synthetic -                           -
J2    param     -                           -
J2    field     -                           -
J2    getter    JT                          JT
J2    synthetic -                           -
J3    param     JT                          JT
J3    field     -                           -
J3    getter    -                           -
J3    synthetic -                           -
K0    param     KT                          KT
K0    field     -                           -
K0    getter    -                           -
K0    synthetic -                           -
K1    param     -                           -
K1    field     KT                          KT
K1    getter    -                           -
K1    synthetic -                           -
K2    param     -                           -
K2    field     -                           -
K2    getter    KT                          KT
K2    synthetic -                           -
K3    param     KT                          KT
K3    field     -                           -
K3    getter    -                           -
K3    synthetic -                           -
K4    param     -                           -
K4    field     -                           -
K4    getter    -                           -
K4    synthetic getV$annotations:KT         getV$annotations:KT
cells that differ: 0 / 36
(exit 0)
```

- ★★ **`first-only` 와 `-language-version 2.1` 은 0 / 36** — 도움말의 「`'first-only' in version 2.1 and before`」가 칸 단위로 맞았다.

### (3) ★★ `@property:` — 합성 메서드 `getV$annotations()`

**언제 쓰나** — 「`@property:` 는 Java 에서 안 보인다」를 **정확히** 알고 싶을 때.

```text
===== javap -v -p o35d/K4.class | grep -A9 'getV\$annotations();' =====
  public static void getV$annotations();
    descriptor: ()V
    flags: (0x1009) ACC_PUBLIC, ACC_STATIC, ACC_SYNTHETIC
    Code:
      stack=0, locals=0, args_size=0
         0: return
    Deprecated: true
    RuntimeVisibleAnnotations:
      0: #19()
        KT
(exit 0)
```

```kotlin
// kref.kt
import kotlin.reflect.full.memberProperties
import kotlin.reflect.jvm.javaField
import kotlin.reflect.jvm.javaGetter

fun show(name: String, k: kotlin.reflect.KClass<*>) {
    val p = k.memberProperties.single()
    val prop = p.annotations.map { it.annotationClass.simpleName }
    val field = p.javaField?.annotations?.map { it.annotationClass.simpleName }
    val getter = p.javaGetter?.annotations?.map { it.annotationClass.simpleName }
    println("$name property=$prop javaField=$field javaGetter=$getter")
}

fun main() {
    show("J0", J0::class)
    show("K0", K0::class)
    show("K1", K1::class)
    show("K4", K4::class)
}
```

```text
===== kotlinc -cp o35d:kotlin-reflect.jar kref.kt sites.kt -d o35r =====
(exit 0)
===== java -cp o35r:o35d:kotlin-stdlib.jar:kotlin-reflect.jar KrefKt =====
J0 property=[] javaField=[JT] javaGetter=[]
K0 property=[KT] javaField=[] javaGetter=[]
K1 property=[] javaField=[KT] javaGetter=[]
K4 property=[KT] javaField=[] javaGetter=[]
(exit 0)
```

- ★★★ **`public static void getV$annotations();` · `ACC_PUBLIC, ACC_STATIC, ACC_SYNTHETIC` · `Deprecated: true` · 몸통은 `return` 하나.** 애너테이션을 **걸어 둘 자리가 필요해서 만든 빈 메서드**다. `ACC_SYNTHETIC` 이라 **`javac` 소스에서는 부를 수 없고**, `Deprecated` 라 보이더라도 쓰지 말라는 표시다.
- ★★ 그래서 공식 문서의 「not visible to Java」는 **Java 소스·Java 프레임워크의 일반 경로**(필드·게터·매개변수 조회)에서 안 보인다는 뜻이다 — **리플렉션으로 메서드를 전수 훑으면 찾을 수 있다**((1)의 `synthetic=` 칸). 모순이 아니라 **층이 다른 말**이다.
- ★★ **`kotlin-reflect` 로는 정식으로 보인다** — `K0 property=[KT]` · `K4 property=[KT]`. `KProperty.annotations` 는 **property target 만** 돌려준다: `J0 property=[]` · `javaField=[JT]` 가 그것이다. 같은 프로퍼티라도 **어느 창으로 묻느냐**가 답을 가른다.
- ★ `kotlin-reflect.jar` 는 **`kotlinc` 배포본 `lib/` 에 들어 있다**(3-answer 의 환경 블록) — 별도 설치 없이 `-cp` 로 줬다.

### (4) ★★★ 「단골」 오동작 — 필드만 읽는 검증기

**언제 쓰나** — Bean Validation·JPA·Jackson 처럼 **필드를 리플렉션으로 읽는** 도구에 Kotlin 클래스를 넘길 때. 여기는 그 도구들을 쓰지 않고 **같은 모양의 작은 검증기**를 직접 짰다.

```java
// NotBlankJ.java
import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

@Retention(RetentionPolicy.RUNTIME)
@Target({ElementType.FIELD, ElementType.PARAMETER})
public @interface NotBlankJ {}
```

```java
// Check.java
import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.List;

// 필드에 붙은 애너테이션만 읽는 작은 검증기 — 필드 기반 프레임워크의 모양
public class Check {
    public static List<String> violations(Object o) throws IllegalAccessException {
        List<String> out = new ArrayList<>();
        for (Field f : o.getClass().getDeclaredFields()) {
            boolean marked = false;
            for (var a : f.getDeclaredAnnotations()) {
                if (a.annotationType().getSimpleName().startsWith("NotBlank")) marked = true;
            }
            if (!marked) continue;
            f.setAccessible(true);
            Object v = f.get(o);
            if (v instanceof String s && s.isBlank()) out.add(f.getName() + " is blank");
        }
        return out;
    }
}
```

```kotlin
// signup.kt
@Target(AnnotationTarget.VALUE_PARAMETER, AnnotationTarget.PROPERTY, AnnotationTarget.FIELD)
annotation class NotBlankK

class SignupJ(@NotBlankJ val name: String)
class SignupK(@NotBlankK val name: String)
class SignupKF(@field:NotBlankK val name: String)

fun main() {
    println("A SignupJ  -> " + Check.violations(SignupJ(" ")))
    println("B SignupK  -> " + Check.violations(SignupK(" ")))
    println("C SignupKF -> " + Check.violations(SignupKF(" ")))
}
```

```text
===== javac -d o35s NotBlankJ.java Check.java =====
(exit 0)
===== kotlinc -cp o35s signup.kt -d o35s =====
(exit 0)
===== java -cp o35s:kotlin-stdlib.jar SignupKt =====
A SignupJ  -> [name is blank]
B SignupK  -> []
C SignupKF -> [name is blank]
(exit 0)
===== javac -d o35s2 NotBlankJ.java Check.java =====
(exit 0)
===== kotlinc -Xannotation-default-target=first-only -cp o35s2 signup.kt -d o35s2 =====
warning: the argument '-Xannotation-default-target=first-only' disables a stable language feature for the current language version 2.4. Future support for this mode is not guaranteed.
(exit 0)
===== java -cp o35s2:kotlin-stdlib.jar SignupKt =====
A SignupJ  -> []
B SignupK  -> []
C SignupKF -> [name is blank]
(exit 0)
```

| 클래스 | 2.4.20 기본 | `first-only`(= 2.1 이하) |
|---|---|---|
| `SignupJ`(Java 애너테이션 · target 없음) | ★ `[name is blank]` — **잡힌다** | ★★ **`[]` — 검증을 건너뛴다** |
| `SignupK`(Kotlin 애너테이션 · `PROPERTY` 허용 · target 없음) | ★★★ **`[]` — 이 판에서도 건너뛴다** | `[]` |
| `SignupKF`(`@field:`) | `[name is blank]` | `[name is blank]` |

- ★★★ **「단골」의 정체** — 옛 판에서 `@NotBlankJ val name` 은 **매개변수에만** 붙었고, 필드를 읽는 검증기는 **아무것도 못 찾아 `[]`** 를 돌려준다. **에러도 경고도 없이 「통과」다**(규칙 3 — 통과도 출력이다).
- ★★★ **2.4 가 이 사고를 절반만 없앴다** — Java 애너테이션(`PROPERTY` 가 없다)은 이제 필드에도 붙지만, **`PROPERTY` 를 허용하는 Kotlin 애너테이션은 property 로 가서 필드가 여전히 비었다**(`B`). 규칙이 「property 또는 field **중 첫째**」이기 때문이다.
- ★★ **판과 무관하게 맞는 쓰는 법은 `@field:`** 다(`C` — 두 판 모두 잡힌다). 필드를 읽는 도구에는 **target 을 적어라.**

### (5) ★★ `@all:` 과 값 클래스

```kotlin
// allsite.kt
class A0(@all:KT val v: Int)
class A1(@all:JT val v: Int)
```

```text
===== kotlinc -cp o35d sites.kt allsite.kt -d o35a =====
(exit 0)
===== kotlinc -Xannotation-target-all -cp o35d sites.kt allsite.kt -d o35a2 =====
warning: the argument '-Xannotation-target-all' is redundant for the current language version 2.4.
(exit 0)
===== java -cp o35a:o35d:kotlin-stdlib.jar Where A0 A1 =====
A0;param=KT;field=KT;getter=KT;synthetic=getV$annotations:KT
A1;param=JT;field=JT;getter=JT;synthetic=-
(exit 0)
```

- ★★ **`@all:` 은 플래그 없이 컴파일된다** — `-Xannotation-target-all` 을 주면 「`is redundant for the current language version 2.4.`」 도움말에는 아직 「experimental」로 적혀 있지만((2)의 도움말), **2.4 에서 Stable** 이다(whatsnew24). 도움말 문구가 판보다 **늦게** 따라온 자리다.
- ★★ **`A0`(Kotlin) → 네 자리 전부** · **`A1`(Java) → 합성 메서드만 빼고 세 자리**. `@all:` 도 **애너테이션이 허용하는 자리에만** 붙는다.

```kotlin
// vcsite.kt
@JvmInline
value class Uid(val raw: Long)

class Acc(@get:JT val id: Uid, @get:JT val n: Long)
```

```java
// VcLook.java
public class VcLook {
    public static void main(String[] args) {
        for (var m : Acc.class.getDeclaredMethods()) {
            if (m.getName().startsWith("get")) {
                System.out.println("A " + m.getName() + " annotations=" + m.getDeclaredAnnotations().length);
            }
        }
        try {
            Acc.class.getDeclaredMethod("getId");
            System.out.println("B found");
        } catch (NoSuchMethodException e) {
            System.out.println("B " + e);
        }
    }
}
```

```text
===== kotlinc -cp o35d vcsite.kt -d o35v =====
(exit 0)
===== javap -v -p o35v/Acc.class | grep -E '^  [a-z].*;$|^ +RuntimeVisible|^ +JT$' =====
  private final long id;
  private final long n;
  private Acc(long, long);
  public final long getId-DyZRee4();
    RuntimeVisibleAnnotations:
        JT
  public final long getN();
    RuntimeVisibleAnnotations:
        JT
  public Acc(long, long, kotlin.jvm.internal.DefaultConstructorMarker);
(exit 0)
===== javac -cp o35v:o35d:kotlin-stdlib.jar -d o35v VcLook.java =====
(exit 0)
===== java -cp o35v:o35d:kotlin-stdlib.jar VcLook =====
A getId-DyZRee4 annotations=1
A getN annotations=1
B java.lang.NoSuchMethodException: Acc.getId()
(exit 0)
```

- ★★ **값 클래스 게터는 `getId-DyZRee4()` 이고 `JT` 는 그 뭉개진 이름에 붙었다.** 일반 `Long` 게터는 `getN()` 그대로다. 뭉개기의 이유(서명 충돌 회피)는 [26번 주제](../26-value-class-and-boxing/)가 정본이다.
- ★★ **`B java.lang.NoSuchMethodException: Acc.getId()`** — 게터를 **이름으로 찾는 도구**는 애너테이션 이전에 **메서드 자체를 못 찾는다.** 스티커는 붙었는데 **방 번호가 바뀌었다.**
- ★ 주 생성자도 `private Acc(long, long)` + 합성 생성자로 갈렸다 — 생성자 매개변수를 읽는 도구도 같은 문제를 겪을 자리다(이 문서는 **던지지 않았다**).

### (6) ★ 붙일 수 없는 자리 · 판이 바뀔 것을 예고한 경고

```kotlin
// propj.kt
class X(@property:JT val v: Int)
class Y(@setparam:JT val v: Int)
```

```text
===== kotlinc -cp o35d propj.kt -d o35b =====
propj.kt:1:9: error: this annotation is not applicable to target 'value parameter' and use-site target '@property'. Applicable targets: field, value parameter, function, getter, setter, expression
class X(@property:JT val v: Int)
        ^^^^^^^^^^^^
propj.kt:2:9: error: '@setparam:' annotations can only be applied to mutable properties.
class Y(@setparam:JT val v: Int)
        ^^^^^^^^^^^^
(exit 1)
```

- ★★ **Java 애너테이션에 `@property:`** — 「`this annotation is not applicable to target 'value parameter' and use-site target '@property'. Applicable targets: …`」 (1)의 `J0` 이 property 로 못 간 이유가 이 문구에 있다.
- ★ `@setparam:` 은 `var` 에만 — 「`can only be applied to mutable properties.`」

```text
===== javac -d o35w JT.java =====
(exit 0)
===== kotlinc -language-version 2.3 -cp o35w sites.kt -d o35w =====
sites.kt:7:10: warning: this annotation is currently applied to the value parameter only, but in the future it will also be applied to field.
- To opt in to applying to both value parameter and field, add '-Xannotation-default-target=param-property' to your compiler arguments.
- To keep applying to the value parameter only, use the '@param:' annotation target.

See https://youtrack.jetbrains.com/issue/KT-73255 for more details.
class J0(@JT val v: Int)
         ^^^
sites.kt:12:10: warning: this annotation is currently applied to the value parameter only, but in the future it will also be applied to property.
- To opt in to applying to both value parameter and property, add '-Xannotation-default-target=param-property' to your compiler arguments.
- To keep applying to the value parameter only, use the '@param:' annotation target.

See https://youtrack.jetbrains.com/issue/KT-73255 for more details.
class K0(@KT val v: Int)
         ^^^
(exit 0)
===== kotlinc -language-version 2.1 -cp o35w sites.kt -d o35w2 =====
warning: language version 2.1 is deprecated and its support will be removed in a future version of Kotlin. Update the version to 2.2.
(exit 0)
```

- ★★ **`-language-version 2.3` 은 경고를 낸다** — 「`this annotation is currently applied to the value parameter only, but in the future it will also be applied to field.`」(`J0`) · 「`… also be applied to property.`」(`K0`). 경고가 **2.4 의 답을 정확히 예고**했다 — `J0` 은 field, `K0` 은 property.
- ★ `2.1` 은 **조용하다**(판 경고만) — 옛 규칙 그대로라 예고할 것이 없다.

### (7) ★ C# — 같은 함정의 C# 판

```csharp
// attr35.cs
using System;
using System.Linq;
using System.Reflection;

[AttributeUsage(AttributeTargets.All)]
class TagAttribute : Attribute {}

record R0([Tag] string Name);
record R1([property: Tag] string Name);
class C0 { [Tag] public string Name { get; set; } = ""; }
class C1 { [field: Tag] public string Name { get; set; } = ""; }

static class P {
    static string M(MemberInfo m) => m.GetCustomAttributes(typeof(TagAttribute), false).Any() ? "Tag" : "-";
    static string M(ParameterInfo p) => p.GetCustomAttributes(typeof(TagAttribute), false).Any() ? "Tag" : "-";
    static void Show(Type t) {
        const BindingFlags all = BindingFlags.Instance | BindingFlags.NonPublic | BindingFlags.Public;
        var ctor = t.GetConstructors().FirstOrDefault(c => c.GetParameters().Length == 1 && c.GetParameters()[0].ParameterType == typeof(string));
        var param = ctor == null ? "(none)" : M(ctor.GetParameters()[0]);
        var prop = M(t.GetProperty("Name")!);
        var field = M(t.GetField("<Name>k__BackingField", all)!);
        Console.WriteLine($"{t.Name};param={param};property={prop};backingField={field}");
    }
    static void Main() { foreach (var t in new[] { typeof(R0), typeof(R1), typeof(C0), typeof(C1) }) Show(t); }
}
```

```text
===== csc -out:attr35.dll attr35.cs =====
(exit 0)
===== dotnet attr35.dll =====
R0;param=Tag;property=-;backingField=-
R1;param=-;property=Tag;backingField=-
C0;param=(none);property=Tag;backingField=-
C1;param=(none);property=-;backingField=Tag
(exit 0)
```

- ★★★ **`R0`(`record` 위치 매개변수 · 대상 지정 없음)은 `param=Tag` 뿐이다** — 프로퍼티에도 backing field 에도 없다. **Kotlin 2.1 이하의 `J0` 과 같은 모양**이다. C# 도 주 생성자 매개변수가 **프로퍼티로 번역되는** 자리에서 같은 함정을 가진다.
- ★★ **`R1`(`[property: Tag]`) → 프로퍼티** · **`C1`(`[field: Tag]` 자동 프로퍼티) → backing field `<Name>k__BackingField`** · `C0`(대상 없음 · 일반 프로퍼티) → 프로퍼티. 대상 지정자의 **문법 모양이 Kotlin 과 같다**(`[field:]` ↔ `@field:`).
- ★ C# 쪽 기본 규칙이 **판에 따라 바뀌었는지**는 이 문서가 **재지 않았다**(한 판만 던졌다).

## 문법 — 형태와 규칙

**형태** — 필드와 게터에 **target 을 적어** 붙이고, Java 리플렉션으로 확인하는 최소 예제다.

```kotlin
// form35.kt
@Target(AnnotationTarget.FIELD, AnnotationTarget.PROPERTY_GETTER, AnnotationTarget.VALUE_PARAMETER)
annotation class Col(val name: String)

class Row(@field:Col("id") val id: Long, @get:Col("nm") val name: String)

fun main() {
    val c = Row::class.java
    println("A " + c.getDeclaredField("id").getAnnotation(Col::class.java)?.name)
    println("B " + c.getDeclaredMethod("getName").getAnnotation(Col::class.java)?.name)
    println("C " + c.getDeclaredField("name").getAnnotation(Col::class.java)?.name)
}
```

```text
===== kotlinc form35.kt -d o35z =====
(exit 0)
===== java -cp o35z:kotlin-stdlib.jar Form35Kt =====
A id
B nm
C null
(exit 0)
```

**규칙 불릿**

- 쓰는 꼴: **`@<target>:<애너테이션>`** — `@field:Col("id")`·`@get:JsonProperty`·`@param:Inject`.
- target 을 적으면 **그 한 자리**에만 붙는다 — 판과 무관하다((1)(2)).
- target 을 안 적으면 **판마다 규칙이 다르다** — 2.1 이하 매개변수 하나, **2.4 이상 매개변수 + (property 또는 field 중 첫째)**((2)).
- `@property:` 는 JVM 에서 **`get<이름>$annotations()` 합성 메서드**에 기록된다 — Java 도구의 일반 경로에서는 안 보인다((3)).
- `@all:` — 허용되는 모든 자리. **2.4 Stable**((5)).
- 애너테이션 선언의 **`@Target` 이 허용 안 하는 target** 은 컴파일 에러다((6)).
- 값 클래스 프로퍼티의 게터는 **이름이 뭉개진다** — 애너테이션도 그 이름에 붙는다((5)).

## 어디서 틀리나

1. ★★★ **주 생성자 `val` 에 target 없이 붙이고 필드 기반 도구가 읽을 거라 믿는다.** 2.1 이하에서는 **매개변수에만** 붙어 **조용히 검증이 꺼진다**((4)).
2. ★★★ **「2.4 에서 고쳐졌다」고 믿는다.** Kotlin 으로 선언한 애너테이션이 `PROPERTY` 를 허용하면 **여전히 필드에 안 간다**((4) `B`).
3. ★★ **판을 올리면서 애너테이션 동작이 바뀔 수 있다는 것을 모른다.** 2.3 → 2.4 에서 `J0` 의 필드 칸이 **새로 생겼다**((2)) — 검증이 **갑자기 켜지는** 쪽의 변화다.
4. ★★ **`@property:` 로 붙이고 Java 프레임워크가 읽을 거라 믿는다.** 합성 메서드라 일반 경로에서는 안 보인다((3)).
5. ★ **값 클래스 프로퍼티를 이름으로 찾는다.** `getId` 가 아니라 `getId-DyZRee4` 다((5)).
6. ★ **`first-only` 옵션으로 옛 동작을 고정한다.** 「stable language feature 를 끈다」는 경고가 붙는 옵션이다 — 오래 기댈 자리가 아니다((2)).

## 구현 세부사항 대 언어 보장

| 항목 | 어느 쪽인가 | 근거 |
|---|---|---|
| use-site target 목록과 뜻 | ★★★ **언어 보장** | 문서 · (1) |
| target 없을 때의 **선택 순서**(param → property → field) | ★★★ **언어 보장** | 문서 · (1) |
| 그 순서로 **하나만** 고르나 **둘을** 고르나 — `first-only` / `param-property` | ★★★ **언어 판의 규칙**(2.4 Stable) | whatsnew24 · `-X` 도움말 · (2) |
| `param` → 생성자 매개변수 · `field` → 필드 · `get` → 게터 | ★ **JVM 백엔드의 구현**(언어의 target 을 JVM 멤버로 옮긴 것) | (1) `javap` |
| ★★ `property` → **`getV$annotations()` 합성 메서드** | ★★ **JVM 백엔드의 구현** | (3) `javap` |
| 값 클래스 게터의 **뭉개진 이름** | ★ **JVM 백엔드의 구현** | (5) · [26번 주제](../26-value-class-and-boxing/) |
| Java 애너테이션에 `PROPERTY` 대상이 없는 것 | **Java 언어의 사실** | (1)(6) |
| 경고·에러 문구 · 「redundant」 경고 · 도움말의 「experimental」 | **이 판의 산출물** | (2)(5)(6) |

★★★ **공식 문서 본문(`annotations.html`)의 기본 규칙 문단은 「param → property → field 중 하나」로 적혀 있다** — 이 판의 기본값(`param-property`)과 **표현이 어긋난다.** 2.4 가 Stable 로 바꾼 것은 whatsnew24 가 적고, 칸 단위 증거는 (2)의 격자다. **문서를 읽었다고 이 판을 확인한 것이 아니다**(규칙 3).

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 필드를 읽는 도구(검증·ORM·직렬화) | ★★ **`@field:`** | (4) — 판과 무관하게 필드 |
| 게터를 읽는 도구 | `@get:` | (1) |
| 생성자 주입·생성자 매개변수를 읽는 도구 | `@param:` | (1) |
| Kotlin 리플렉션만 쓰는 도구 | target 없음 또는 `@property:` | (3) — `KProperty.annotations` |
| 어디서 읽을지 모르는 공용 애너테이션 | `@all:`(2.4+) | (5) — 허용되는 모든 자리 |
| 값 클래스를 프레임워크 엔티티에 | **피하거나 도구의 지원을 확인** | (5) — 이름이 뭉개진다 |

## 핵심 문장

1. 주 생성자 `val` 은 JVM 에서 **매개변수·필드·게터**(+ Kotlin 만 보는 프로퍼티)로 쪼개지고, use-site target 은 **그중 어디에 붙일지**를 정한다.
2. target 을 안 적으면 **판마다 규칙이 다르다** — 2.1 이하는 **매개변수 하나**, 2.4 는 **매개변수 + (property 또는 field 중 첫째)** 다. 격자에서 **36칸 중 2칸**이 갈렸다.
3. 「필드 기반 프레임워크가 애너테이션을 못 본다」는 **에러 없이 검증이 꺼지는** 사고이고, 2.4 에서도 **`PROPERTY` 를 허용하는 Kotlin 애너테이션**에서는 그대로 난다.
4. `@property:` 는 JVM 에서 **`getV$annotations()` 라는 빈 합성 메서드**에 붙는다 — Java 도구의 일반 경로에는 안 보이고 `kotlin-reflect` 로는 보인다.
5. 필드를 읽는 도구에는 **`@field:` 를 적는 것**이 판과 무관한 답이다.

## 관련 자료

- [16번 주제](../16-properties-backing-field-lateinit-const/) — ★★ **선행.** 프로퍼티가 필드·접근자로 쪼개지는 것. 그쪽은 「무엇으로 쪼개지나」까지, 여기는 「**애너테이션이 그중 어디에 붙나**」부터.
- [26번 주제](../26-value-class-and-boxing/) — 값 클래스의 이름 뭉개기. (5)의 `getId-DyZRee4`.
- [17번 주제](../17-delegated-properties/) — `@delegate:` 가 붙는 위임 필드.
- [15번 주제](../15-class-declaration-constructors-and-init/) — 주 생성자와 `constructor` 낱말.
- 목록의 **39번 주제** — `@JvmField`·`@JvmName` 같은 상호운용 애너테이션 하나하나.
- C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **53번**(특성) — 아직 폴더가 없다. (7)이 C# 쪽을 직접 던졌다.

## 용어 풀이

> **애너테이션(annotation)** — 선언에 붙이는 메타데이터. 값을 바꾸지 않고, **읽는 쪽**(컴파일러·리플렉션·프레임워크)이 의미를 준다.

> **use-site target** — 애너테이션을 **어느 조각에 붙일지** 적는 접두어. `@field:`·`@get:`·`@set:`·`@param:`·`@setparam:`·`@property:`·`@delegate:`·`@receiver:`·`@file:`·`@all:`.\
> 예: `class Row(@field:Col("id") val id: Long)`.

> **`@Target`** — 애너테이션 **선언** 쪽에서 「어디에 붙을 수 있나」를 정하는 메타 애너테이션. use-site target 과 방향이 반대다.

> **`RuntimeVisibleAnnotations`** — 클래스 파일에서 멤버(필드·메서드·클래스)에 붙은 **실행 시 보이는** 애너테이션을 담는 속성. 매개변수용은 `RuntimeVisibleParameterAnnotations`.

> **합성 메서드(synthetic method)** — 컴파일러가 만들고 소스에는 없는 메서드. `ACC_SYNTHETIC` 이 붙고 `javac` 소스에서 부를 수 없다.

> **`first-only` / `param-property`** — target 없는 애너테이션의 기본 규칙 두 가지. 앞은 「첫째 하나」, 뒤는 「매개변수 + 둘째 자리 하나」. 2.4 부터 뒤쪽이 기본.

## 더 들어가면

- **왜 `property` 는 메서드가 되나** — JVM 에는 「프로퍼티」라는 멤버가 없다. 필드·메서드·클래스·매개변수에만 애너테이션을 걸 수 있으므로, **Kotlin 프로퍼티에만 속한 애너테이션**을 담으려면 걸 자리를 **새로 만들어야** 한다. 그 자리가 몸통이 `return` 하나뿐인 `static` 합성 메서드다. `kotlin-reflect` 는 Kotlin 메타데이터로 프로퍼티를 찾은 뒤 **그 메서드의 애너테이션을 읽어** `KProperty.annotations` 로 돌려준다 — 그래서 (3)의 두 창이 같은 답을 냈다.
- **2.4 가 규칙을 「둘을 고른다」로 바꾼 이유** — 옛 규칙에서 주 생성자 `val` 은 **거의 언제나 매개변수 하나**로 끝나, 필드·프로퍼티를 기대한 사용자가 (4)의 사고를 반복했다. 2.2·2.3 의 경고((6))가 그 전환의 예고였고, 경고 문구가 가리키는 이슈(`KT-73255`)가 논의의 자리다 — 이 문서는 그 이슈를 **열어 보지 않았다.**
