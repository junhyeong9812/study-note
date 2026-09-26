# kotlin/syntax/35 — 애너테이션과 use-site target (`@field:`·`@get:`·`@param:`) — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [16번 주제](../16-properties-backing-field-lateinit-const/)다 — 프로퍼티 하나가 **필드·게터·(생성자) 매개변수**로 쪼개지는 것을 거기서 봤다. 이 주제는 **애너테이션이 그 조각 중 어디에 붙나**다.
> 문항 11개 중 코드블록이 붙는 예측형은 6개다.
> 이 주제의 모든 답은 **kotlinc 2.4.20 · Temurin JDK 21.0.5** 에서 실제로 던져 받은 것이다(C# 은 **.NET SDK 10.0.401**). ★ 이 주제는 **언어 판에 따라 답이 바뀐다** — 판을 밝히지 않은 답은 반쪽이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ target 을 적지 않은 것과 적은 것 — 어느 멤버에 붙나 (예측)

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

- 기본 옵션(2.4.20)으로 컴파일하고 `java Where J0 J1 J2 J3 K0 K1 K2 K3 K4` 를 돌리면 아홉 줄은 각각 무엇인가?
- ★ `J0` 과 `K0` 은 **같은 모양**(target 없음)인데 답이 같은가?

### 2. ★★★ 같은 소스를 옛 기본 규칙으로 컴파일하면 (예측)

- 1번을 `-Xannotation-default-target=first-only` 로 다시 컴파일해 두 결과를 칸마다 견주면(`grid35.py`), **몇 칸 중 몇 칸**이 달라지는가? 어느 칸인가?
- `-language-version 2.1` 로 컴파일한 것은 `first-only` 와 몇 칸이 다른가?

### 3. ★★★ 필드만 읽는 검증기에 넘기면 (예측)

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

- 기본 옵션으로 컴파일했을 때 `A`·`B`·`C` 는? `-Xannotation-default-target=first-only` 로 컴파일했을 때는?
- 어느 경우가 **에러도 경고도 없이 검증을 건너뛰는가**?

### 4. ★★ `@property:` 는 클래스 파일의 어디에 (예측)

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

- 1번의 `K4` 를 `javap -v` 로 보면 `KT` 는 어느 멤버에 붙어 있는가? 그 멤버의 `flags` 는?
- `kotlin-reflect` 로 `show(…)` 를 돌리면 네 줄은 각각 무엇인가?

### 5. ★★ `@all:` 과 값 클래스 (예측)

```kotlin
// allsite.kt
class A0(@all:KT val v: Int)
class A1(@all:JT val v: Int)
```

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

- `allsite.kt` 를 **플래그 없이** 컴파일하면 되는가? `-Xannotation-target-all` 을 주면 무엇이라고 하는가? `A0`·`A1` 은 어디에 붙는가?
- `Acc` 의 게터 두 개에 `JT` 가 붙는가? `VcLook` 은 무엇을 찍는가?

### 6. ★ 붙일 수 없는 target (예측)

```kotlin
// propj.kt
class X(@property:JT val v: Int)
class Y(@setparam:JT val v: Int)
```

- 두 줄은 각각 컴파일되는가? 안 되면 무엇이라고 말하는가?

### 7. 2.3 에서만 나오는 경고 (왜)

- `-language-version 2.3` 으로 `sites.kt` 를 컴파일하면 경고가 나오고 `2.1` 은 조용하다. 그 경고는 **무엇을 예고**하는가? 왜 `J0` 과 `K0` 의 문구가 다른가(`field` 대 `property`)?

### 8. 문서의 기본 규칙과 컴파일러의 기본 규칙 (경계)

- 공식 문서가 적는 「param → property → field」 순서와 `kotlinc -X` 가 적는 `param-property` 는 같은 규칙인가? 무엇이 **언어 규칙**이고 무엇이 **JVM 백엔드의 결과**인가?

### 9. C# 의 `[property:]`·`[field:]` (연결)

- C# `record R0([Tag] string Name)` 의 `Tag` 는 어디에 붙는가? 1번의 어느 판과 같은 함정인가?

### 10. 문서의 「Java 에서 안 보인다」 (왜)

- 공식 문서는 `@property:` 를 「not visible to Java」라고 적는다. 1번·4번의 출력과 모순인가?

### 11. 필드 기반 프레임워크와 언어 판 (왜)

- 3번의 결과로 보아, 이 판에서 target 없이 붙인 애너테이션을 필드 기반 도구가 못 보는 경우가 남아 있는가? 판과 무관하게 막는 쓰는 법은?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
