# kotlin/syntax/35 — 애너테이션과 use-site target (`@field:`·`@get:`·`@param:`) — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러·경고·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javac`·`java`·`javap` 에서 실제로 얻었다(C# 은 **.NET SDK 10.0.401** 의 `csc`).\
> ★★★ 답은 **언어 판에 매인다** — 판을 밝히지 않은 칸은 기본값(2.4)이다.
> ★★ 아래 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적은 자리가 없다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ `J0` 은 **매개변수 + 필드**, `K0` 은 **매개변수 + 합성 메서드 `getV$annotations`** — 같은 모양인데 **다르다** · target 을 적은 일곱은 **적은 한 자리**

**출력**

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

**왜 그런가**

- ★★★ 2.4 의 기본 규칙은 「**`param` 이 되면 붙이고, 추가로 `property` 또는 `field` 중 첫째에도**」다. `JT`(Java)는 `PROPERTY` 대상이 없어 **field** 로, `KT`(Kotlin)는 `PROPERTY` 를 허용해 **property** 로 갔다.
- ★★ `property` 의 JVM 자리는 **합성 메서드 `getV$annotations()`** 다 — `K0` 과 `K4` 의 `javap` 에 같은 모양으로 있다.
- ★ 게터(`getV`)에는 target 없는 애너테이션이 **어느 경우에도** 안 간다 — 게터는 기본 선택 순서에 **없다.**

### 2. ★★★ **2 / 36** — `J0 field` 와 `K0 synthetic` · `-language-version 2.1` 은 `first-only` 와 **0 / 36**

**출력**

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

**왜 그런가**

- ★★★ `first-only` 는 「param · property · field 중 **첫째 하나**」라 주 생성자 `val` 이면 **매개변수 하나**로 끝난다. 2.4 의 `param-property` 는 거기에 **둘째 자리를 하나 더** 얹는다 — 갈린 두 칸이 정확히 그 둘째 자리다.
- ★★ target 을 적은 일곱 클래스(28칸)는 **한 칸도 안 움직였다.** 판이 바꾼 것은 **적지 않은 경우의 규칙**뿐이다.
- ★ `-X` 도움말의 「`'first-only' in version 2.1 and before`」가 0 / 36 으로 맞았다.

### 3. ★★★ 기본 — `A [name is blank]` · `B []` · `C [name is blank]` / `first-only` — `A []` · `B []` · `C [name is blank]` — ★ **`[]` 가 검증을 건너뛴 칸**

**출력**

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

**왜 그런가**

- ★★★ 검증기는 **필드만** 읽는다. 옛 규칙에서 `SignupJ` 의 애너테이션은 **매개변수에만** 있어 `[]` — **에러도 경고도 없이 통과**다.
- ★★★ `SignupK` 는 **두 판 모두 `[]`** 다. `NotBlankK` 가 `PROPERTY` 를 허용해서 2.4 규칙의 둘째 자리가 **property** 가 됐고, 필드는 여전히 비었다.
- ★★ `@field:` 를 적은 `SignupKF` 만 **두 판 모두** 잡혔다.

### 4. ★★ `KT` 는 **`public static void getV$annotations();`** 에 — `ACC_PUBLIC, ACC_STATIC, ACC_SYNTHETIC` · `Deprecated: true` · `kotlin-reflect` 는 `J0 property=[] javaField=[JT]` · `K0 property=[KT]` · `K1 javaField=[KT]` · `K4 property=[KT]`

**출력**

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

**왜 그런가**

- ★★ JVM 에 「프로퍼티」 멤버가 없으므로 **애너테이션을 걸 빈 메서드**를 만들었다. 합성이라 `javac` 소스에서 못 부르고, 리플렉션으로 **메서드를 전수 훑어야** 보인다.
- ★★ `KProperty.annotations` 는 **property target 만** 돌려준다 — `J0` 의 `JT` 는 필드에 있으므로 `javaField` 로만 보인다. 같은 프로퍼티가 **창마다 다른 답**을 낸다.

### 5. ★★ `@all:` 은 **플래그 없이 통과** — 플래그를 주면 「`is redundant for the current language version 2.4.`」 · `A0` 은 네 자리 전부, `A1` 은 합성 메서드만 빼고 세 자리 · 값 클래스 게터는 **`getId-DyZRee4`** 에 `JT` · `VcLook` 은 `NoSuchMethodException: Acc.getId()`

**출력**

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

```kotlin
// vcsite.kt
@JvmInline
value class Uid(val raw: Long)

class Acc(@get:JT val id: Uid, @get:JT val n: Long)
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

**왜 그런가**

- ★★ `@all:` 은 2.2 미리보기 → **2.4 Stable** 이다. 그래도 **애너테이션이 허용하는 자리에만** 붙는다 — Java 애너테이션은 property 로 못 간다.
- ★★ 값 클래스 프로퍼티의 게터는 **이름이 뭉개진다.** 애너테이션은 제대로 붙었지만, 게터를 **`getId` 라는 이름으로 찾는 도구**는 메서드부터 못 찾는다.

### 6. ★ 둘 다 에러 — Java 애너테이션에 `@property:` 는 「`not applicable to target 'value parameter' and use-site target '@property'`」 · `val` 에 `@setparam:` 은 「`can only be applied to mutable properties.`」

**출력**

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

**왜 그런가**

- ★★ 첫 에러의 「`Applicable targets: …`」 목록에 **`property` 가 없다** — 1번에서 `J0` 이 property 대신 field 로 간 이유가 그 목록이다.
- ★ `@setparam:` 은 **세터의 매개변수**다. `val` 에는 세터가 없다.

### 7. 「2.4 부터는 **매개변수 말고 한 자리에 더** 붙는다」를 예고한다 — 더 붙는 자리가 애너테이션마다 다르다(`JT` → field · `KT` → property)

**출력**

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

**왜 그런가**

- ★★ 2.2·2.3 의 기본값이 **`first-only-warn`** 이다 — 동작은 옛 규칙 그대로이고, **둘째 자리가 있는 칸에만** 경고를 붙인다. 경고의 `field`/`property` 가 2번 격자의 갈린 두 칸과 **정확히 같다.**
- ★ 2.1 은 경고 없이 옛 규칙 — 예고할 것이 없다.

### 8. **선택 순서**(param → property → field)는 같은 언어 규칙이고, 그 순서로 **하나를 고르나 둘을 고르나**가 판마다 다르다 — 고른 target 이 **어느 JVM 멤버가 되나**는 백엔드의 구현이다

**왜 그런가**

- ★★★ 공식 문서 본문(`annotations.html`)은 순서만 적고 「하나/둘」을 **이 판의 기본값과 다르게** 읽히게 적는다. 2.4 가 무엇을 Stable 로 바꿨는지는 whatsnew24 와 `-X` 도움말이 적고, **칸 단위 증거는 2번 격자**다.
- ★★ 「`property` → `getV$annotations()`」·「`param` → 생성자 매개변수」는 JVM 백엔드가 **언어의 target 을 JVM 멤버로 옮긴 결과**다 — 다른 백엔드는 다르게 옮길 수 있다(재지 않았다).

### 9. **매개변수에만** 붙는다 — Kotlin 2.1 이하(`first-only`)의 `J0` 과 같은 함정

**출력**

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

**왜 그런가**

- ★★ C# `record` 의 위치 매개변수는 **프로퍼티로 번역되는 매개변수**다 — Kotlin 주 생성자 `val` 과 같은 자리다. 대상을 안 적으면 **매개변수**가 이긴다(`R0`).
- ★ 고치는 법도 같은 모양이다 — `[property: Tag]`(`R1`) · `[field: Tag]`(`C1`).

### 10. 모순이 아니다 — 문서의 「안 보인다」는 **Java 소스와 일반 조회 경로**의 말이고, 합성 메서드는 **리플렉션 전수 훑기**에서만 보인다

**왜 그런가**

- ★★ `ACC_SYNTHETIC` 이라 **`javac` 가 이름을 부를 수 없고**, 필드·게터·매개변수를 보는 **보통의 프레임워크 조회**에도 안 걸린다. 1번의 `Where` 는 **메서드 이름에 `$annotations` 가 든 것을 일부러** 찾았다.
- ★ 실무의 뜻은 문서와 같다 — **Java 도구에 보여야 하면 `@property:` 를 쓰지 마라.**

### 11. **`PROPERTY` 를 허용하는 Kotlin 애너테이션**을 target 없이 붙이면 이 판에서도 필드가 빈다 — **`@field:` 를 적는 것**이 판과 무관한 답이다

**왜 그런가**

- ★★★ 3번 `SignupK` 가 증거다 — 2.4 규칙의 둘째 자리는 「property **또는** field 중 **첫째**」라 property 가 되면 field 는 비는다.
- ★★ Java 로 선언된 애너테이션(대부분의 Java 프레임워크 애너테이션)은 2.4 에서 필드에도 간다 — 그래서 **판을 올리면 조용히 켜지는** 쪽의 변화가 생긴다(3번 `A`). 어느 쪽이든 **판에 기대지 않으려면 target 을 적어라.**

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

```text
===== dotnet --version =====
10.0.401
(exit 0)
```

```text
===== ls "$(dirname "$(readlink -f "$(command -v kotlinc)")")/../lib" | grep -E '^kotlin-(reflect|test|stdlib)\.jar$' =====
kotlin-reflect.jar
kotlin-stdlib.jar
kotlin-test.jar
(exit 0)
```

★ **흔들리는 칸과 안 흔들리는 칸**

| 흔들린다 | 안 흔들린다 |
|---|---|
| **없다** — 해시코드·주소·시간을 찍지 않았다 | 리플렉션 출력(멤버를 **이름으로** 물었다) · `javap` 출력 · 뭉개진 이름의 해시 글자(같은 판) |
| | 진단·경고의 **문구·`파일:줄:칸`·캐럿** · 격자의 「갈린 칸 N / 36」 · `dotnet` 출력 |
| | 모든 **종료 코드** |

> 근거 — 캡처 스크립트를 처음부터 다시 돌려 **블록 전체를 바이트 단위로 대조**했다.
>
> 실측 — `capture.sh blocks` 와 `capture.sh blocks-recheck` 를 처음부터 따로 돌려 `normalize-shaky.py` 로 대조했다 —\
> **블록 103개 · 동일 103 · 흔들린 칸 0 · ★고칠 것 0**(34\~37 네 주제를 한 캡처로 받았다). `diff -rq` 도 차이 0 이다.\
> ★ **정규화 규칙은 하나도 안 썼다** — 기본 넷(주소·PID·스레드 id·시간)에 걸리는 칸이 애초에 없었다.

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `JT.java` · `sites.kt` · `Where.java` | ★★★ 아홉 모양 × 네 자리 | `javac` → `kotlinc` → `javac` → `java` · `javap -v`(필터) |
| `grid35.py` | ★★★ 판 격자 `2 / 36` · `0 / 36` | `kotlinc -Xannotation-default-target=first-only` · `kotlinc -language-version 2.1` → 스크립트(내부에서 `java` 4회) |
| `NotBlankJ.java` · `Check.java` · `signup.kt` | ★★★ 필드 기반 검증기의 「단골」 | 기본 · `first-only` 두 벌 |
| `kref.kt` | `kotlin-reflect` 로 본 property | `kotlinc -cp kotlin-reflect.jar` → `java` |
| `allsite.kt` | `@all:` — 2.4 Stable | `kotlinc` · `kotlinc -Xannotation-target-all`(경고) → `java` |
| `vcsite.kt` · `VcLook.java` | 값 클래스 게터의 뭉개진 이름 | `kotlinc` → `javap -v`(필터) → `javac` → `java` |
| `propj.kt` | 붙일 수 없는 target | `kotlinc`(실패가 결과) |
| `sites.kt`(판 두 벌) | 2.3 의 예고 경고 · 2.1 의 침묵 | `kotlinc -language-version 2.3` · `2.1` |
| `attr35.cs` | C# `record` 의 같은 함정 | `csc` → `dotnet` |
| `form35.kt` | 형태 한 벌 | `kotlinc` → `java` |

**구현 의존 항목** — target → JVM 멤버의 대응, ★★ **`getV$annotations()` 합성 메서드**, 값 클래스 게터의 뭉개진 이름, 경고·에러 문구 — 이 컴파일러·판의 산출물이다.\
반면 **use-site target 의 목록·선택 순서·「2.4 는 둘째 자리까지」** 는 **언어의 규칙**이다(마지막 것은 **판에 매인 규칙**이다).

**★ 던져 봤더니 예상과 달랐던 것 — 네 건**

1. ★★★ **「target 없이 붙이면 `field.getAnnotation` 이 `null`」이 이 판에서는 Java 애너테이션에 대해 틀렸다**(1·2번) — 2.4 가 필드에도 붙인다. 브리핑의 「단골」은 **2.1 이하**(또는 `first-only`)의 모습이고, 2.4 에서는 **`PROPERTY` 를 허용하는 Kotlin 애너테이션**으로 자리를 옮겨 남아 있다(3번 `B`).
2. ★★ **`@property:` 가 「Kotlin 메타데이터에만」 있지 않았다** — **합성 메서드 `getV$annotations()`** 의 `RuntimeVisibleAnnotations` 에 있고, Java 리플렉션이 그것을 찾았다(4번).
3. ★★ **`kotlin-reflect` 는 없는 도구가 아니었다** — `kotlinc` 배포본 `lib/` 에 있다(환경 블록). 「못 잰 것」으로 적을 자리가 아니었다.
4. ★ **`@all:` 은 실험 플래그가 필요 없었다** — 2.4 에서 Stable 이라 플래그를 주면 「redundant」 경고가 난다. `-X` 도움말은 여전히 「experimental」이라 적는다(5번).
