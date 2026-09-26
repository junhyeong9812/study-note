# kotlin/syntax/12 — `reified` 타입 파라미터: 소거를 뚫는 방법 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Inline functions — Reified type parameters](https://kotlinlang.org/docs/inline-functions.html#reified-type-parameters) · [Generics](https://kotlinlang.org/docs/generics.html) · [Type checks and casts](https://kotlinlang.org/docs/typecasts.html) · [Reflection](https://kotlinlang.org/docs/reflection.html) · [kotlin.reflect.typeOf API](https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.reflect/type-of.html).
> **실행 검증** — 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javap` 에서 실제로 얻었다.\
> **Java 쪽은 같은 JDK 의 `javac` 로 컴파일해 실제로 섞어 돌렸다**((4)).\
> `kotlinc` 17회 · `javac` 2회 · `java` 8회 · `javap` 6회. 컴파일 실패 시나리오 **7벌** · 경고 시나리오 1벌.
> ⚠️ **`-jvm-target` 을 밝히지 않은 바이트코드 주장은 반쪽이다.** 이 문서의 역어셈블은 **기본값 1.8**(`major version: 52`)이다.\
> ★ 다만 이 주제의 결론은 타깃에 안 흔들렸다 — 같은 파일을 `-jvm-target 21`(`major version: 65`)로 다시 찍어 `diff` 했더니 **한 글자도 다르지 않았다**((10)).
> ⚠️ **`typeOf<T>()` 의 출력은 클래스패스에 `kotlin-reflect.jar` 가 있느냐로 통째로 달라진다**((6)) — 이 문서는 **양쪽을 다 찍었다**.
> **버전** — `inline`·`reified` 는 **1.0**. `typeOf<T>()` 는 **1.6**(1.3 실험).
> **경계** — ★★ **`inline` 이 왜 이 주제의 전제인지, 인라인이 무엇을 펼치는지는 [11번 주제](../11-inline-functions/)가 정본이다.**\
> **소거가 무엇을 지우는지의 정본은 [`../../../java/syntax/19-type-erasure/`](../../../java/syntax/19-type-erasure/)** 다 — 여기서는 **그 결론만 받아 쓴다**.\
> 람다가 객체가 되는 것은 [10번 주제](../10-lambdas-and-higher-order-functions/), `is`/`as` 자체의 문법은 [목록의 **33번 주제**](../33-type-checks-and-casts-is-as/),\
> 변성·star projection 은 [목록의 **28번 주제**](../28-generics-variance-in-out-star-where/), `kotlin-reflect` API 전체는 목록의 **35번 주제**가 정본이다.
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**제네릭 함수 안에서는 `T` 가 무엇이었는지 알 수 없다.** 컴파일이 끝나면 지워지기 때문이다.

> **타입 소거(type erasure)** — 컴파일이 끝나면 타입 인자가 사라지는 것.\
> 예: `List<String>` 도 `List<Int>` 도 클래스 파일에서는 그냥 `java.util.List` 다.

그래서 `fun <T> isA(x: Any) = x is T` 는 **컴파일러가 거부한다** — 런타임에 비교할 대상이 없다.

**`reified` 는 그 규칙을 이기는 것이 아니라 피해 가는 것이다.**\
`inline` 이 함수 몸통을 **호출 자리에 복사해 넣는데**([11번 주제](../11-inline-functions/)),\
복사해 넣는 **바로 그 순간에는 컴파일러가 `T` 가 무엇인지 알고 있다.** 그래서 그 자리에서 글자를 채워 넣는다.

| 비유 | 실체 |
|---|---|
| 빈칸이 있는 양식(「\_\_\_ 님께」) | 제네릭 함수 — `T` 가 빈칸이다 |
| 양식을 그대로 우편으로 보내기 | 보통 호출 — 받는 쪽은 빈칸이 무엇이었는지 모른다(소거) |
| 양식을 **내 편지지에 베껴 쓰면서 이름을 적어 넣기** | `inline` + `reified` — 복사하는 자리에서 글자를 채운다 |
| 베껴 쓸 때만 되는 일이라 「부칠 수는 없다」 | Java 에서 호출 불가 — `ACC_SYNTHETIC` |
| 빈 양식 원본에 남겨 둔 「여기 채워 넣을 것」 도장 | `Intrinsics.reifiedOperationMarker` — 그냥 부르면 터진다 |
| 채워 넣는 것은 **이름 한 칸**뿐 | `T::class` 는 **raw class** 만 준다 — 타입 인자는 여전히 소거된다 |
| 주소까지 통째로 베낀 봉투 | `typeOf<T>()` — 타입 인자·null 가능성까지 살아남는다 |

```text
   보통 제네릭                             inline + reified
   +-------------------------------+      +-------------------------------+
   | fun <T> isA(x: Any) = x is T  |      | inline fun <reified T> isA(   |
   |   → 컴파일 에러               |      |   x: Any) = x is T            |
   |   cannot check for instance   |      +-------------------------------+
   |   of erased type 'T'          |                   |
   +-------------------------------+                   | 호출 자리에 복사
                                                       v
                                        isA<String>(x)  →  instanceof java/lang/String
                                        isA<Int>(x)     →  instanceof java/lang/Integer
                                            ★ 자리마다 다른 글자가 박힌다
```

**그래서 `reified` 는 「런타임에 타입을 되살리는 기능」이 아니다.**\
**컴파일 타임에 타입을 박아 넣는 기능**이고, 그 대가와 한계가 전부 거기서 나온다.

## 이 주제가 답하려는 질문

1. `reified` 는 **왜 `inline` 없이는 존재할 수 없는가** — 컴파일러가 뭐라고 말하는가.
2. `is T`·`T::class`·`typeOf<T>()` 는 **호출 자리에서 각각 무엇으로 펼쳐지는가**.
3. `reified` 가 **못 하는 것**은 무엇인가 — `T()` 와 타입 인자와 Java 호출.

## 동작 방식

### (1) ★★ `inline` 이 없으면 `reified` 가 **아예 문법으로 거부된다**

**언제 쓰나** — "`reified` 를 붙이면 제네릭이 런타임에 살아남는다" 로 외우려 할 때.

두 방향을 다 던져 본다. **`reified` 만 쓴 것**과 **`reified` 없이 `is T` 를 쓴 것**이다.

```text
===== 소스: bad1.kt =====
fun <reified T> isA(x: Any): Boolean = x is T
===== kotlinc bad1.kt =====
bad1.kt:1:6: error: only type parameters of inline functions can be reified.
fun <reified T> isA(x: Any): Boolean = x is T
     ^^^^^^^
(exit 1)
```

```text
===== 소스: bad2.kt =====
fun <T> isA(x: Any): Boolean = x is T
===== kotlinc bad2.kt =====
bad2.kt:1:37: error: cannot check for instance of erased type 'T (of fun <T> isA)'.
fun <T> isA(x: Any): Boolean = x is T
                                    ^
(exit 1)
```

```text
   두 에러가 이 주제의 좌표를 만든다

   fun <T> ...  x is T        ──▶  cannot check for instance of erased type 'T'
        │                            "런타임에 T 가 없다"
        │
        └─ reified 를 붙이면?  ──▶  only type parameters of inline functions can be reified.
                                     "그건 inline 함수에서만 되는 낱말이다"
                                              │
                                              └─ inline 을 같이 붙여야 비로소 통과한다
```

그림 해설:

- ★★ **에러 두 개가 서로를 가리킨다.** 앞엣것은 **「없다」**, 뒤엣것은 **「그 낱말은 인라인 전용이다」** 다.\
  `reified` 의 정의가 이 두 문장 사이에 있다 — **인라인이 펼쳐 주는 덕에 타입 인자가 살아남는 것**이지,\
  런타임에 타입 정보가 새로 생기는 것이 아니다.
- ★ **`class Box<reified T>` 도 같은 에러다** — 클래스는 인라인될 수 없으므로.

```text
===== 소스: bad4.kt =====
class Box<reified T>(val x: T)
===== kotlinc bad4.kt =====
bad4.kt:1:11: error: only type parameters of inline functions can be reified.
class Box<reified T>(val x: T)
          ^^^^^^^
(exit 1)
```

- ★ **선행이 11번인 이유가 여기 있다.** [11번 주제](../11-inline-functions/)에서 `inline` 은 **람다 객체를 없애는 것**과\
  **비지역 `return`** 을 위해 쓰는 것이었는데, `reified` 는 **선택이 아니라 전제**로 `inline` 을 요구하는 **세 번째 용도**다.

비용 — 컴파일 실패. 고치는 법이 메시지 안에 있다(`inline` 을 붙여라).

### (2) ★★ 호출 자리에 **타입이 글자로 박힌다**

**언제 쓰나** — "`reified` 가 실제로 무엇으로 컴파일되나" 를 눈으로 확인할 때. **이 주제의 심장이다.**

```kotlin
// icode.kt
import kotlin.reflect.typeOf

inline fun <reified T> isA(x: Any): Boolean = x is T
inline fun <reified T> nameOf(): String = T::class.java.name
inline fun <reified T> typeText(): String = typeOf<T>().toString()

fun callIsAString(x: Any): Boolean = isA<String>(x)
fun callIsAList(x: Any): Boolean = isA<List<String>>(x)
fun callNameOfInt(): String = nameOf<Int>()
fun callTypeOfListString(): String = typeText<List<String>>()
```

**출력** (`kotlinc icode.kt -d out` 뒤 `find out -name '*.class' | sort`)

```text
out/IcodeKt.class
```

**출력** (`javap -c -p out/IcodeKt.class` — 호출부 네 개만 발췌)

```text
  public static final boolean callIsAString(java.lang.Object);
    Code:
       0: aload_0
       1: ldc           #9                  // String x
       3: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_0
       7: astore_1
       8: iconst_0
       9: istore_2
      10: aload_1
      11: instanceof    #39                 // class java/lang/String
      14: ireturn

  public static final boolean callIsAList(java.lang.Object);
    Code:
       0: aload_0
       1: ldc           #9                  // String x
       3: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_0
       7: astore_1
       8: iconst_0
       9: istore_2
      10: aload_1
      11: instanceof    #51                 // class java/util/List
      14: ireturn

  public static final java.lang.String callNameOfInt();
    Code:
       0: iconst_0
       1: istore_0
       2: ldc           #54                 // class java/lang/Integer
       4: invokevirtual #32                 // Method java/lang/Class.getName:()Ljava/lang/String;
       7: dup
       8: ldc           #34                 // String getName(...)
      10: invokestatic  #37                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullExpressionValue:(Ljava/lang/Object;Ljava/lang/String;)V
      13: areturn

  public static final java.lang.String callTypeOfListString();
    Code:
       0: iconst_0
       1: istore_0
       2: ldc           #51                 // class java/util/List
       4: ldc           #39                 // class java/lang/String
       6: invokestatic  #61                 // Method kotlin/jvm/internal/Reflection.typeOf:(Ljava/lang/Class;)Lkotlin/reflect/KType;
       9: invokestatic  #67                 // Method kotlin/reflect/KTypeProjection.invariant:(Lkotlin/reflect/KType;)Lkotlin/reflect/KTypeProjection;
      12: invokestatic  #70                 // Method kotlin/jvm/internal/Reflection.typeOf:(Ljava/lang/Class;Lkotlin/reflect/KTypeProjection;)Lkotlin/reflect/KType;
      15: invokevirtual #44                 // Method java/lang/Object.toString:()Ljava/lang/String;
      18: areturn
```

```text
   소스가 적은 것              호출 자리에 남은 것
   +----------------------+    +--------------------------------------------------+
   | isA<String>(x)       | ─▶ | instanceof java/lang/String        ← 글자가 박혔다|
   | isA<List<String>>(x) | ─▶ | instanceof java/util/List          ← ★ raw 다     |
   | nameOf<Int>()        | ─▶ | ldc class java/lang/Integer        ← ★ 박싱된 것  |
   | typeText<List<Str>>()| ─▶ | Reflection.typeOf(List, invariant( ← ★ 인자까지   |
   |                      |    |                   typeOf(String)))               |
   +----------------------+    +--------------------------------------------------+
```

그림 해설:

- ★★ **`isA<String>` 은 `invokestatic isA` 가 아니다.** 호출이 통째로 사라지고 **`instanceof java/lang/String` 한 줄**이 남았다.\
  타입 인자가 **상수 풀의 클래스 참조**로 굳은 것이다 — **그래서 「런타임에 T 를 안다」가 성립한다**.
- ★★ **`isA<List<String>>` 은 `instanceof java/util/List` 다.** `String` 이라는 글자가 **아무 데도 없다** —\
  **`reified` 는 타입 인자까지 되살리지 못한다**((5)에서 실행으로 확인한다).
- ★ **`nameOf<Int>()` 가 `java/lang/Integer` 다.** `Int` 가 아니라 **박싱된 클래스**다 — `T::class.java` 는\
  타입 파라미터 자리에 온 `Int` 를 **참조 타입으로** 본다((6)).
- ★ **`typeOf<T>()` 만 구조를 통째로 만든다.** `List` 와 `String` 두 클래스가 **둘 다** 상수로 박히고,\
  `KTypeProjection.invariant` 로 **타입 인자로 조립**된다. `is T` 와 결정적으로 갈리는 자리다.
- **클래스 파일은 하나뿐이다.** `reified` 는 객체도 클래스도 만들지 않는다 —\
  만드는 것이 아니라 **호출 자리에 글자를 박는** 변환이기 때문이다.

비용 — 호출 자리마다 몸통 한 벌([11번 주제](../11-inline-functions/)의 (8)이 그 크기를 쟀다). 객체는 0개.

### (3) ★ 남아 있는 본체에는 **지뢰가 들어 있다** — `reifiedOperationMarker`

**언제 쓰나** — "인라인해도 본체는 남는다"([11번 주제](../11-inline-functions/)의 (3))를 `reified` 에 적용할 때.

같은 `javap` 출력의 **앞쪽**, 즉 선언 쪽 본체를 읽는다.

**출력** (`javap -c -p out/IcodeKt.class` — 선언 쪽 본체 셋)

```text
  public static final <T> boolean isA(java.lang.Object);
    Code:
       0: aload_0
       1: ldc           #9                  // String x
       3: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: iconst_0
       7: istore_1
       8: aload_0
       9: iconst_3
      10: ldc           #17                 // String T
      12: invokestatic  #21                 // Method kotlin/jvm/internal/Intrinsics.reifiedOperationMarker:(ILjava/lang/String;)V
      15: instanceof    #4                  // class java/lang/Object
      18: ireturn

  public static final <T> java.lang.String nameOf();
    Code:
       0: iconst_0
       1: istore_0
       2: iconst_4
       3: ldc           #17                 // String T
       5: invokestatic  #21                 // Method kotlin/jvm/internal/Intrinsics.reifiedOperationMarker:(ILjava/lang/String;)V
       8: ldc           #4                  // class java/lang/Object
      10: checkcast     #29                 // class java/lang/Class
      13: invokevirtual #32                 // Method java/lang/Class.getName:()Ljava/lang/String;
      16: dup
      17: ldc           #34                 // String getName(...)
      19: invokestatic  #37                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullExpressionValue:(Ljava/lang/Object;Ljava/lang/String;)V
      22: checkcast     #39                 // class java/lang/String
      25: areturn

  public static final <T> java.lang.String typeText();
    Code:
       0: iconst_0
       1: istore_0
       2: bipush        6
       4: ldc           #17                 // String T
       6: invokestatic  #21                 // Method kotlin/jvm/internal/Intrinsics.reifiedOperationMarker:(ILjava/lang/String;)V
       9: aconst_null
      10: invokevirtual #44                 // Method java/lang/Object.toString:()Ljava/lang/String;
      13: areturn
```

```text
   선언 쪽 본체 = 「아직 안 채운 양식」

   isA      :  reifiedOperationMarker(3, "T")  →  instanceof java/lang/Object   ← 의미 없는 자리표
   nameOf   :  reifiedOperationMarker(4, "T")  →  ldc class java/lang/Object    ← 〃
   typeText :  reifiedOperationMarker(6, "T")  →  aconst_null                   ← 〃
                                        ^
                       인라인할 때 컴파일러가 이 표식을 보고 뒷줄을 바꿔치기한다
```

그림 해설:

- ★★ **`Intrinsics.reifiedOperationMarker(int, "T")` 가 「여기를 채워 넣어라」는 도장이다.**\
  그 **바로 다음 줄**이 자리표(placeholder)이고 — `instanceof Object`·`ldc Object`·`aconst_null` —\
  인라인할 때 그 줄이 (2)에서 본 실제 타입으로 **바꿔치기된다**.
- ★ **정수 코드가 연산 종류를 가른다** — `3`=`is`, `4`=`T::class`, `6`=`typeOf`. **이것은 관찰이지 문서화된 계약이 아니다.**
- ★★ **그래서 본체를 그냥 부르면 안 된다.** 자리표가 그대로라 `isA` 는 `x is Any` 가 되고 `typeText` 는 `null.toString()` 이 된다.\
  Kotlin 은 그것을 막으려고 **두 겹의 방어선**을 세워 뒀다 — (4)에서 둘 다 던져 본다.

비용 — 없다. 본체는 남지만 Kotlin 호출자는 그 본체를 거치지 않는다.

### (4) ★★ Java 는 이 함수를 **못 부른다** — 그리고 억지로 부르면 터진다

**언제 쓰나** — Kotlin 유틸을 Java 모듈에서 쓰려 할 때.

```kotlin
// api.kt
inline fun <reified T> isA(x: Any): Boolean = x is T
inline fun plain(x: Int, f: (Int) -> Int): Int = f(x)
fun normal(x: Int): Int = x + 1
```

**출력** (`javap -v -p oapi/ApiKt.class | grep -E 'public static final|  flags:'`)

```text
  flags: (0x0031) ACC_PUBLIC, ACC_FINAL, ACC_SUPER
  public static final <T extends java.lang.Object> boolean isA(java.lang.Object);
    flags: (0x1019) ACC_PUBLIC, ACC_STATIC, ACC_FINAL, ACC_SYNTHETIC
  public static final int plain(int, kotlin.jvm.functions.Function1<? super java.lang.Integer, java.lang.Integer>);
    flags: (0x0019) ACC_PUBLIC, ACC_STATIC, ACC_FINAL
  public static final int normal(int);
    flags: (0x0019) ACC_PUBLIC, ACC_STATIC, ACC_FINAL
```

**첫 번째 방어선 — `javac` 가 못 본다.**

```text
===== 소스: UseReified.java =====
public class UseReified {
    public static void main(String[] a) {
        System.out.println("J Java calls normal(10) : " + ApiKt.normal(10));
        System.out.println("K Java calls isA(\"hi\")  : " + ApiKt.isA("hi"));
    }
}
===== javac -cp oapi:kotlin-stdlib.jar UseReified.java -d oj =====
UseReified.java:4: error: cannot find symbol
        System.out.println("K Java calls isA(\"hi\")  : " + ApiKt.isA("hi"));
                                                                 ^
  symbol:   method isA(String)
  location: class ApiKt
1 error
(exit 1)
```

**두 번째 방어선 — 리플렉션으로 억지로 불러도 터진다.**

```java
// UseRefl.java
import java.lang.reflect.Method;

public class UseRefl {
    public static void main(String[] a) throws Exception {
        Method m = ApiKt.class.getDeclaredMethod("isA", Object.class);
        System.out.println("L reflective lookup ok : " + m);
        System.out.println("M isSynthetic()        : " + m.isSynthetic());
        try {
            Object r = m.invoke(null, "hi");
            System.out.println("N invoke returned      : " + r);
        } catch (java.lang.reflect.InvocationTargetException e) {
            System.out.println("N invoke threw         : " + e.getCause());
        }
    }
}
```

**출력** (`java -cp "oj:oapi:kotlin-stdlib.jar" UseRefl`)

```text
L reflective lookup ok : public static final boolean ApiKt.isA(java.lang.Object)
M isSynthetic()        : true
N invoke threw         : java.lang.UnsupportedOperationException: This function has a reified type parameter and thus can only be inlined at compilation time, not called directly.
```

```text
   ApiKt.class 안의 세 메서드

   normal   ACC_PUBLIC ACC_STATIC ACC_FINAL                 → Java 가 부른다 ✓
   plain    ACC_PUBLIC ACC_STATIC ACC_FINAL                 → Java 가 부른다 ✓ (인라인은 안 된다)
   isA      ACC_PUBLIC ACC_STATIC ACC_FINAL ACC_SYNTHETIC ★ → javac 가 안 본다
                                                              리플렉션으로 뚫으면
                                                              UnsupportedOperationException
```

그림 해설:

- ★★ **`reified` 인라인 함수만 `ACC_SYNTHETIC` 이다.** 같은 파일의 평범한 `inline fun plain` 은 안 붙는다 —\
  **「인라인이라서」가 아니라 「`reified` 라서」** 붙는 플래그다([11번 주제](../11-inline-functions/)의 (3)이 그 대비를 먼저 보여 줬다).
- **`ACC_SYNTHETIC` 은 「컴파일러가 만든 것이라 소스에는 없다」는 표시**이고, `javac` 는 그런 멤버를 **해석 대상에서 뺀다.**\
  그래서 `cannot find symbol` 이다 — **「없다」가 아니라 「안 보인다」**. `javap` 로는 **버젓이 보인다**.
- ★★ **리플렉션은 보인다**(`getDeclaredMethod` 성공, `isSynthetic()` 이 `true`). 그런데 **부르면 런타임 예외**다.\
  자리표를 그대로 실행하지 않도록 **`reifiedOperationMarker` 가 던지는 것**이다((3)).\
  메시지가 이 주제의 한 줄 요약이다 — *can only be inlined at compilation time, not called directly*.
- ★ 그래서 **Java 에서도 쓸 API 에는 `reified` 를 쓰지 않는다.** 대신 `Class<T>` 를 인자로 받는 짝을 같이 낸다((8)).

비용 — Java 상호운용을 통째로 잃는다. 그것이 `reified` 의 가장 큰 대가다.

### (5) ★★ `reified` 가 **되살리는 것과 못 되살리는 것**

**언제 쓰나** — `isA<List<String>>` 처럼 타입 인자가 붙은 타입을 넘길 때. **가장 조용히 틀리는 자리다.**

```kotlin
// ex.kt
import kotlin.reflect.typeOf

inline fun <reified T> isA(x: Any): Boolean = x is T
inline fun <reified T> nameOf(): String = T::class.java.name
inline fun <reified T> simpleOf(): String = T::class.simpleName ?: "?"
inline fun <reified T> typeText(): String = typeOf<T>().toString()

fun main() {
    println("A isA<String>(\"hi\")            : ${isA<String>("hi")}")
    println("B isA<String>(1)               : ${isA<String>(1)}")
    println("C isA<List<String>>(listOf(1)) : ${isA<List<String>>(listOf(1))}")
    println("D nameOf<Int>()                : ${nameOf<Int>()}")
    println("E nameOf<String>()             : ${nameOf<String>()}")
    println("F simpleOf<Int>()              : ${simpleOf<Int>()}")
    println("G typeText<List<String>>()     : ${typeText<List<String>>()}")
    println("H typeText<Int>()              : ${typeText<Int>()}")
    println("I typeText<String?>()          : ${typeText<String?>()}")
}
```

**출력** (`kotlinc ex.kt -d outex` — **경고도 에러도 없다**)

```text
(exit 0)
```

**출력** (`java -cp "outex:kotlin-stdlib.jar" ExKt`)

```text
A isA<String>("hi")            : true
B isA<String>(1)               : false
C isA<List<String>>(listOf(1)) : true
D nameOf<Int>()                : java.lang.Integer
E nameOf<String>()             : java.lang.String
F simpleOf<Int>()              : Int
G typeText<List<String>>()     : java.util.List<java.lang.String> (Kotlin reflection is not available)
H typeText<Int>()              : int (Kotlin reflection is not available)
I typeText<String?>()          : java.lang.String? (Kotlin reflection is not available)
```

```text
   isA<List<String>>( listOf(1) )   ← Int 가 든 리스트인데
                │
                ▼
   instanceof java.util.List        ← 검사는 여기까지만 한다
                │
                ▼
              true                  ← ★ 통과한다. 경고도 없다.
```

그림 해설:

- ★★ **`C` 가 `true` 다.** `List<String>` 인지 물었는데 **`Int` 가 든 리스트가 통과했다.**\
  (2)의 `instanceof java/util/List` 가 그 이유다 — **타입 인자는 `reified` 로도 안 살아난다.**
- ★★ **컴파일러가 아무 말도 안 했다**(`exit 0`, 경고 0줄). 같은 코드를 `reified` 없이 쓰면 **에러**인데((1)),\
  `reified` 를 붙이면 **조용히 반쪽짜리 검사**가 된다. **에러가 경고도 없는 오답으로 바뀌는 교환**이다.
- ★ **null 가능성은 다르다 — 그쪽은 살아남는다**((7)의 앞부분).
- **`D`·`F` 가 갈린다.** 같은 `Int` 인데 `T::class.java.name` 은 **`java.lang.Integer`**, `T::class.simpleName` 은 **`Int`** 다.\
  ★ **`T::class` 는 `KClass` 이고 `.java` 를 붙이는 순간 JVM 클래스로 내려간다** — 그때 원시 타입이 박싱된다.
- `G`\~`I` 는 `typeOf` 가 타입 인자(`<java.lang.String>`)와 null 가능성(`?`)을 **다 들고 있다**는 것을 보여 준다.\
  다만 그 출력의 **모양이 클래스패스에 달려 있다** — (6).

비용 — `is T` 는 **raw class 검사 한 줄**이라 싸고, 그만큼 **덜 검사한다**.

### (6) ★ `T::class` 와 `typeOf<T>()` 는 **다른 것을 준다** — 그리고 클래스패스가 답을 바꾼다

**언제 쓰나** — `fromJson<List<User>>` 처럼 중첩 제네릭을 다루는 API 를 만들 때.

```kotlin
// use.kt
import kotlin.reflect.typeOf

// 소거 시대의 API — 호출자가 Class 를 손으로 들고 온다
fun <T : Any> decodeOld(text: String, type: Class<T>): T = type.cast(
    when (type) {
        Int::class.javaObjectType -> text.trim().toInt()
        String::class.java -> text.trim()
        else -> error("unsupported: ${type.name}")
    }
)

// reified 시대의 API — 타입 인자가 곧 Class 다
inline fun <reified T : Any> decode(text: String): T = decodeOld(text, T::class.javaObjectType)

// 중첩 제네릭까지 보려면 KClass 가 아니라 KType 이 필요하다
inline fun <reified T> describe(): String = "class=${T::class.java.name} ktype=${typeOf<T>()}"

fun main() {
    println("S decodeOld(\"42\", Integer.class) : ${decodeOld("42", Int::class.javaObjectType)}")
    println("T decode<Int>(\"42\")              : ${decode<Int>("42")}")
    println("U decode<String>(\" hi \")         : '${decode<String>(" hi ")}'")
    println("V describe<List<Int>>()          : ${describe<List<Int>>()}")
    println("W describe<List<String>>()       : ${describe<List<String>>()}")
}
```

**출력** (`java -cp "ouse:kotlin-stdlib.jar" UseKt` — **`kotlin-reflect.jar` 없이**)

```text
S decodeOld("42", Integer.class) : 42
T decode<Int>("42")              : 42
U decode<String>(" hi ")         : 'hi'
V describe<List<Int>>()          : class=java.util.List ktype=java.util.List<java.lang.Integer> (Kotlin reflection is not available)
W describe<List<String>>()       : class=java.util.List ktype=java.util.List<java.lang.String> (Kotlin reflection is not available)
```

**출력** (`java -cp "ouse:kotlin-stdlib.jar:kotlin-reflect.jar" UseKt` — **같은 클래스 파일, 클래스패스만 다르다**)

```text
S decodeOld("42", Integer.class) : 42
T decode<Int>("42")              : 42
U decode<String>(" hi ")         : 'hi'
V describe<List<Int>>()          : class=java.util.List ktype=kotlin.collections.List<kotlin.Int>
W describe<List<String>>()       : class=java.util.List ktype=kotlin.collections.List<kotlin.String>
```

```text
                    describe<List<Int>>()   describe<List<String>>()
   T::class.java  → java.util.List          java.util.List        ← ★ 같다. 구분 못 한다
   typeOf<T>()    → List<Int>               List<String>          ← ★ 갈린다
```

그림 해설:

- ★★ **`T::class.java` 는 두 호출을 구분하지 못한다.** 둘 다 `java.util.List` 다.\
  **JSON 라이브러리가 `TypeToken` 같은 것을 요구하는 이유가 정확히 이것**이고, Kotlin 쪽 답이 `typeOf<T>()` 다.
- ★★ **같은 클래스 파일인데 출력이 달라졌다** — `kotlin-reflect.jar` 가 없으면 `KType.toString()` 이\
  **JVM 이름으로 퇴화하고 `(Kotlin reflection is not available)` 를 덧붙인다.** 있으면 `kotlin.collections.List<kotlin.Int>` 다.\
  **환경을 안 밝히면 이 절의 출력은 검증 불가**가 된다 — 그래서 양쪽을 다 실었다.
- ★ **`typeOf<T>()` 가 만드는 것은 `KType` 이지 `Class` 가 아니다.** 그 값을 실제로 쓰려면 라이브러리가 그것을 받아야 한다.\
  `kotlinx.serialization` 의 `serializer(typeOf<T>())` 가 그 형태다 — **이 문서는 그 라이브러리를 돌려 보지 않았다.**
- **`decodeOld` 와 `decode` 를 나란히 둔 것이 실무 형태다.** 안쪽은 `Class<T>` 를 받는 평범한 함수로 두고,\
  **바깥에 `inline fun <reified T>` 한 줄을 씌운다.** 그러면 Java 는 `decodeOld` 를, Kotlin 은 `decode` 를 쓴다((4)).

비용 — `typeOf<T>()` 는 호출 자리에서 `Reflection.typeOf(...)` **객체를 조립**한다((2)). `T::class` 는 상수 하나다.

### (7) ★★ `reified` 가 **못 하는 것** — `T()` 는 문법에서 거부된다

**언제 쓰나** — "타입을 아니까 인스턴스도 만들 수 있겠지" 라고 생각할 때.

먼저 null 가능성은 **살아남는다**는 것부터 확인한다 — (5)의 타입 인자와 대비된다.

```kotlin
// nul2.kt
inline fun <reified T> isA(x: Any?): Boolean = x is T

fun callNullableString(x: Any?): Boolean = isA<String?>(x)
fun callString(x: Any?): Boolean = isA<String>(x)

fun main() {
    val n: Any? = null
    println("J isA<String?>(null) : ${isA<String?>(n)}")
    println("K isA<String>(null)  : ${isA<String>(n)}")
    println("L isA<String?>(\"hi\") : ${isA<String?>("hi")}")
}
```

**출력** (`java -cp "onul2:kotlin-stdlib.jar" Nul2Kt`)

```text
J isA<String?>(null) : true
K isA<String>(null)  : false
L isA<String?>("hi") : true
```

**출력** (`javap -c -p onul2/Nul2Kt.class` — 두 호출부)

```text
  public static final boolean callNullableString(java.lang.Object);
    Code:
       0: aload_0
       1: astore_1
       2: iconst_0
       3: istore_2
       4: aload_1
       5: dup
       6: ifnull        15
       9: instanceof    #23                 // class java/lang/String
      12: goto          17
      15: pop
      16: iconst_1
      17: ireturn

  public static final boolean callString(java.lang.Object);
    Code:
       0: aload_0
       1: astore_1
       2: iconst_0
       3: istore_2
       4: aload_1
       5: instanceof    #23                 // class java/lang/String
       8: ireturn
```

이제 **생성자**를 부른다.

```text
===== 소스: bad3.kt =====
inline fun <reified T> make(): T = T()
===== kotlinc bad3.kt =====
bad3.kt:1:36: error: type parameter 'T' is not an expression.
inline fun <reified T> make(): T = T()
                                   ^
(exit 1)
```

우회로는 **리플렉션**뿐이고, 그 대가는 **컴파일 타임 보장의 상실**이다.

```kotlin
// mk.kt
inline fun <reified T : Any> mk(): T = T::class.java.getDeclaredConstructor().newInstance()

class NoArg { override fun toString(): String = "NoArg()" }
class NeedsArg(val n: Int)

fun main() {
    println("M mk<NoArg>()   : ${mk<NoArg>()}")
    try {
        println("N mk<NeedsArg>(): ${mk<NeedsArg>()}")
    } catch (e: Throwable) {
        println("N mk<NeedsArg>(): threw ${e::class.java.name}: ${e.message}")
    }
}
```

**출력** (`kotlinc mk.kt -d omk` → `java -cp "omk:kotlin-stdlib.jar" MkKt`)

```text
M mk<NoArg>()   : NoArg()
N mk<NeedsArg>(): threw java.lang.NoSuchMethodException: NeedsArg.<init>()
```

```text
   reified 가 되살리는 것             reified 도 못 되살리는 것
   +---------------------------+     +-----------------------------------+
   | 클래스(raw class)         |     | 타입 인자 <String>       ((5) C)  |
   | null 가능성 `?`           |     | 생성자 T()               (bad3)   |
   | 원시/참조 구분은 박싱 쪽  |     | Java 에서의 호출         ((4))    |
   +---------------------------+     +-----------------------------------+
```

그림 해설:

- ★★ **null 가능성은 살아남고 타입 인자는 안 살아난다.** `isA<String?>` 은 `ifnull → true`,\
  `isA<String>` 은 **`instanceof` 하나**뿐이다. 둘은 바이트코드가 다르다 — **컴파일러가 `?` 를 기억한 것**이다.\
  같은 `reified` 인데 `<String>` 의 `?` 는 기억하고 `List<String>` 의 `String` 은 못 기억한다 —\
  **전자는 검사 코드로 표현되고 후자는 `instanceof` 로 표현될 수 없기 때문이다.**
- ★★ **`T()` 는 「소거 때문에」 안 되는 것이 아니다.** 에러 문구가 `type parameter 'T' is not an expression.` —\
  **「`T` 는 식이 아니다」**, 즉 **어느 생성자를 부를지가 타입 이름만으로는 정해지지 않는다**는 문법 차원의 거부다.
- ★ **우회로는 컴파일 타임 보장을 버린다.** `mk<NeedsArg>()` 는 **컴파일을 통과하고 런타임에 `NoSuchMethodException`** 이다.\
  **에러가 실행 시점으로 밀린 것**이므로, 「`reified` 로 풀었다」가 아니라 「리플렉션으로 바꿨다」가 맞다.
- ★ 진짜 답은 **생성 함수를 인자로 받는 것**이다 — `inline fun <reified T> mk(factory: () -> T): T = factory()`.\
  그러면 **타입 검사가 컴파일 타임에 돌아온다.**

비용 — 리플렉션 우회는 런타임 예외 가능성을 산다.

### (8) `reified` 가 열어 주는 것 — **타입이 살아 있는 배열**

**언제 쓰나** — 제네릭 함수 안에서 `Array<T>` 를 만들어야 할 때.

```text
===== 소스: bad8.kt =====
fun <T> packDirect(xs: List<T>): Array<T> = Array(xs.size) { xs[it] }
===== kotlinc bad8.kt =====
bad8.kt:1:45: error: cannot use 'T' as reified type parameter. Use a class instead.
fun <T> packDirect(xs: List<T>): Array<T> = Array(xs.size) { xs[it] }
                                            ^^^^^
(exit 1)
```

```kotlin
// arr.kt
inline fun <reified T> pack(vararg xs: T): Array<T> = arrayOf(*xs)
inline fun <reified T> empty(n: Int): Array<T?> = arrayOfNulls<T>(n)

fun main() {
    val a = pack("a", "b")
    println("P pack(\"a\",\"b\").javaClass : ${a.javaClass.name}")
    val b = pack(1, 2)
    println("Q pack(1,2).javaClass     : ${b.javaClass.name}")
    val c = empty<String>(2)
    println("R empty<String>(2)        : ${c.javaClass.name} ${c.toList()}")
}
```

**출력** (`java -cp "oarr:kotlin-stdlib.jar" ArrKt`)

```text
P pack("a","b").javaClass : [Ljava.lang.String;
Q pack(1,2).javaClass     : [Ljava.lang.Integer;
R empty<String>(2)        : [Ljava.lang.String; [null, null]
```

그림 해설:

- ★ **에러 문구가 자백한다** — `cannot use 'T' as reified type parameter`.\
  **`Array(n) { }` 생성자 자체가 `reified` 를 요구하는 인라인 함수**라서, 소거된 `T` 로는 부를 수가 없다.
- ★★ **JVM 배열은 원소 타입을 런타임에 들고 있다**(`[Ljava.lang.String;`). 그래서 **소거된 `T` 로는 만들 수가 없고**,\
  `reified` 가 그 구멍을 메운다. **제네릭 배열은 Kotlin 에서 `reified` 의 대표 사용처**다\
  (Java 쪽 사정은 [`../../../java/syntax/19-type-erasure/`](../../../java/syntax/19-type-erasure/)가 정본이다).
- **`pack(1, 2)` 가 `[Ljava.lang.Integer;` 인 것**은 (5)의 `D` 와 같은 이유다 — 타입 파라미터 자리의 `Int` 는 참조 타입이다.

비용 — 없다. 배열은 어차피 만들어야 한다.

### (9) ★ `reified` 는 11의 경고를 **끄고**, 11의 제약은 **그대로 물려받는다**

**언제 쓰나** — "람다를 안 받는 `inline` 은 의미 없다"([11번 주제](../11-inline-functions/)의 (1))를 `reified` 에 적용할 때.

```text
===== 소스: warn1.kt =====
inline fun <reified T> isA(x: Any): Boolean = x is T

inline fun <T> plainGeneric(x: T): T = x
===== kotlinc warn1.kt =====
warn1.kt:3:1: warning: expected performance impact from inlining is insignificant. Inlining works best for functions with parameters of function types.
inline fun <T> plainGeneric(x: T): T = x
^^^^^^
(exit 0)
```

제약 쪽은 그대로다.

```text
===== 소스: bad5.kt =====
inline fun <reified T> peel(depth: Int): String {
    if (depth == 0) return T::class.java.name
    return peel<T>(depth - 1)
}
===== kotlinc bad5.kt =====
bad5.kt:3:12: error: inline function 'fun <reified T> peel(depth: Int): String' cannot be recursive.
    return peel<T>(depth - 1)
           ^^^^
(exit 1)
```

```text
===== 소스: bad6.kt =====
inline fun <reified T> outer(x: Any): Boolean = inner<T>(x)

fun <T> inner(x: Any): Boolean = x is T
===== kotlinc bad6.kt =====
bad6.kt:3:39: error: cannot check for instance of erased type 'T (of fun <T> inner)'.
fun <T> inner(x: Any): Boolean = x is T
                                      ^
(exit 1)
```

그림 해설:

- ★★ **`reified` 가 있으면 「의미 없다」 경고가 안 난다.** 람다를 하나도 안 받는데도 조용하다 —\
  같은 파일의 `inline fun <T> plainGeneric` 은 **경고를 받는다**. 컴파일러가 **`reified` 를 정당한 인라인 사유로 인정**하는 것이다.\
  [11번 주제](../11-inline-functions/)에서 본 판단 기준(「펼칠 수 있는 람다가 있나」)에 **「`reified` 가 있나」가 더 붙는다**.
- ★ **재귀는 여전히 금지다.** 11의 제약이 그대로 적용된다 — 펼치기가 끝나지 않기 때문이다.
- ★★ **`reified` 는 전염되지 않는다.** `outer` 가 `reified` 여도, 그것이 부르는 `inner` 는 **자기 `T` 가 소거된 채**다.\
  ★ **에러가 가리키는 곳이 `inner` 쪽이라는 것이 단서다** — 호출 사슬 전체를 `inline`·`reified` 로 만들어야 이어진다.
- **`noinline`·`crossinline` 은 파라미터 쪽 낱말이라 `reified` 와 직교한다** — 이 문서는 그 조합을 따로 던지지 않았다.

비용 — 없다. 아는 것의 문제다.

### (10) 타깃을 21 로 올려도 **한 글자도 안 바뀌었다**

**언제 쓰나** — "이 결론이 `-jvm-target` 에 흔들리나" 를 확인해야 할 때.

**출력** (`javap -v -p` 의 `major version` · `javap -c -p` 전체 `diff`)

```text
=== major ===
  major version: 65        (out21 — -jvm-target 21)
  major version: 52        (out   — 기본값 1.8)
===== 21 에서 전체 diff (1.8 대비) =====
icode: 1.8 과 21 이 같다
```

그림 해설:

- `major version` 만 **52 → 65** 로 바뀌고 `javap -c -p` 출력은 **한 글자도 다르지 않았다.**
- ★ `instanceof`·`ldc class`·`reifiedOperationMarker` 는 **JVM 1.0 시절부터 있는 명령과 stdlib 호출**이라\
  타깃이 고르는 백엔드 전략(`invokedynamic` 문자열 연결 등)과 **겹칠 자리가 없다**(이 설명은 관찰의 해석이다).
- ★ **「같았다」는 관찰이지 보장이 아니다** — 두 타깃만 봤다.

비용 — 없다. 확인 한 번.

## 문법 — 형태와 규칙

```kotlin
// 1) 기본형 — inline 과 reified 는 한 몸이다
inline fun <reified T> isA(x: Any?): Boolean = x is T

// 2) 쓸 수 있는 세 가지
inline fun <reified T> a(x: Any) = x is T                 // 타입 검사 → instanceof
inline fun <reified T : Any> b() = T::class               // KClass  → ldc class
inline fun <reified T : Any> c() = T::class.java          // Class   → 원시 타입은 박싱된다
inline fun <reified T> d() = kotlin.reflect.typeOf<T>()   // KType   → 타입 인자·? 까지 산다

// 3) 캐스트
inline fun <reified T> e(x: Any): T = x as T              // checkcast 가 그 자리에 박힌다

// 4) 배열 — reified 가 없으면 못 만든다
inline fun <reified T> pack(vararg xs: T): Array<T> = arrayOf(*xs)
inline fun <reified T> empty(n: Int): Array<T?> = arrayOfNulls<T>(n)

// 5) 실무 형태 — 소거 시대의 API 에 한 줄을 씌운다
fun <T : Any> decodeOld(text: String, type: Class<T>): T = TODO()
inline fun <reified T : Any> decode(text: String): T = decodeOld(text, T::class.javaObjectType)

// 6) 여러 개도 된다
inline fun <reified A, reified B> pair(x: Any): String = "${A::class.simpleName}/${B::class.simpleName}"
```

금지 사례(에러가 나는 형태).

```kotlin
fun <reified T> a(x: Any) = x is T       // ERROR: only type parameters of inline functions can be reified.
fun <T> b(x: Any) = x is T               // ERROR: cannot check for instance of erased type 'T (of fun <T> b)'.
class Box<reified T>(val x: T)           // ERROR: only type parameters of inline functions can be reified.
inline fun <reified T> c(): T = T()      // ERROR: type parameter 'T' is not an expression.
inline fun <reified T> d(n: Int): String = d<T>(n - 1)   // ERROR: … cannot be recursive.
fun <T> e(xs: List<T>): Array<T> = Array(xs.size) { xs[it] }  // ERROR: cannot use 'T' as reified type parameter.
inline fun <reified T> f(): String = T::class.javaObjectType.name  // ERROR: 수신자 타입 불일치 — T : Any 가 필요하다
```

규칙 불릿.

- **`reified` 는 `inline fun` 의 타입 파라미터에만 붙는다.** 클래스·프로퍼티·보통 함수에는 못 붙는다.
- **`is T`·`as T`·`T::class`·`typeOf<T>()` 가 열린다.** 각각 `instanceof`·`checkcast`·`ldc class`·`Reflection.typeOf` 가 된다.
- ★ **되살아나는 것은 raw class 와 null 가능성뿐이다.** 타입 인자는 **여전히 소거된다** — 경고도 없다.
- **`T::class` 는 `T : Any` 를 요구하는 자리가 있다**(`javaObjectType` 등). nullable 을 허용하려면 `T::class.java` 만 쓴다.
- **`T()` 는 못 쓴다.** 생성이 필요하면 **`() -> T` 팩토리를 인자로 받는다.**
- **Java 에서 못 부른다**(`ACC_SYNTHETIC`). Java 와 나눠 쓸 API 는 `Class<T>` 를 받는 짝을 따로 둔다.
- **재귀 불가·비공개 선언 접근 불가 등 `inline` 의 제약을 그대로 물려받는다**([11번 주제](../11-inline-functions/)).
- **`reified` 는 전염되지 않는다.** 호출 사슬 전체가 `inline`+`reified` 여야 이어진다.

## 어디서 틀리나

| 틀리는 형태 | 무슨 일이 일어나나 | 고치는 법 |
|---|---|---|
| `fun <reified T>` 만 씀 | `only type parameters of inline functions can be reified.` | `inline` 을 같이 붙인다 |
| `class Box<reified T>` | **같은 에러** — 클래스는 인라인될 수 없다 | 생성자에 `Class<T>` 를 받는다 |
| `reified` 없이 `x is T` | `cannot check for instance of erased type 'T (of fun <T> …)'` | `inline fun <reified T>` |
| ★★ `isA<List<String>>` 로 타입 인자를 검사한다고 봄 | **`instanceof java.util.List` 뿐이다. `Int` 리스트가 `true` 로 통과하고 경고도 없다** | 원소를 직접 확인하거나 `typeOf<T>()` |
| `T::class.java` 가 중첩 제네릭을 구분한다고 봄 | `List<Int>` 와 `List<String>` 이 **둘 다 `java.util.List`** | `typeOf<T>()` 를 쓴다 |
| `nameOf<Int>()` 가 `int` 일 것이라고 봄 | **`java.lang.Integer`** — `.java` 를 붙이면 박싱된다 | `T::class.simpleName` 은 `Int` 다 |
| `typeOf<T>()` 출력이 어디서나 같다고 봄 | ★ `kotlin-reflect.jar` 가 없으면 **JVM 이름 + `(Kotlin reflection is not available)`** | 클래스패스를 밝히고 싣는다 |
| `T()` 로 인스턴스를 만들려 함 | `type parameter 'T' is not an expression.` | `() -> T` 팩토리를 인자로 받는다 |
| 리플렉션 우회를 「같은 것」으로 봄 | 컴파일은 통과하고 **런타임에 `NoSuchMethodException`** | 컴파일 타임 검사를 잃는다는 것을 안다 |
| Java 에서 `reified` 함수를 부름 | `cannot find symbol` — **`ACC_SYNTHETIC` 이라 `javac` 가 안 본다** | `Class<T>` 를 받는 짝을 따로 낸다 |
| 리플렉션으로 억지로 부름 | `UnsupportedOperationException: … can only be inlined at compilation time` | 〃 |
| `reified` 함수가 부르는 함수도 타입을 안다고 봄 | ★ **전염되지 않는다** — 안쪽에서 `cannot check for instance of erased type` | 사슬 전체를 `inline`+`reified` 로 |
| `reified` 인라인을 재귀로 씀 | `inline function … cannot be recursive.` | 루프로 바꾼다 |
| 소거된 `T` 로 `Array(n) { }` | `cannot use 'T' as reified type parameter. Use a class instead.` | 함수를 `inline`+`reified` 로 |
| `as T` 가 소거돼도 터질 것이라고 봄 | ★ `reified` 없이는 **그 자리에서 안 터지고** 호출자 쪽 `checkcast` 까지 밀린다 | 「더 들어가면」 참고 |
| 람다 없는 `inline` 경고가 날 것이라고 봄 | ★ **`reified` 가 있으면 안 난다** | `reified` 도 정당한 인라인 사유다 |

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 | 근거 |
|---|---|---|
| `reified` 가 `inline` 함수의 타입 파라미터에만 붙는 것 | **언어** | 컴파일 에러 (1)·(bad4) |
| `reified` 없이 `is T` 가 거부되는 것 | **언어** | 컴파일 에러 (1) |
| `is T`·`as T`·`T::class`·`typeOf<T>()` 가 열리는 것 | **언어** | 문서 + 실행 |
| **타입 인자가 `reified` 로도 안 살아나는 것** | **언어(JVM 타깃)** ★★ | 실행(`C` 가 `true`) |
| null 가능성은 살아나는 것 | **언어** | 실행(`J`/`K`) + `javap` (7) |
| `T()` 가 거부되는 것 | **언어** | 컴파일 에러 (7) |
| `reified` 인라인 함수가 재귀일 수 없는 것 | **언어** | 컴파일 에러 (9) |
| `reified` 가 비인라인 함수로 전염되지 않는 것 | **언어** | 컴파일 에러 (9) |
| 소거된 `T` 로 `Array(n) { }` 를 못 만드는 것 | **언어** | 컴파일 에러 (8) |
| Java 에서 `reified` 함수를 못 부르는 것 | **언어(상호운용 계약)** | `javac` 에러 (4) |
| `T::class.java` 가 원시 타입을 박싱하는 것 | **언어** | 실행(`D`/`F`) |
| **`is T` 가 `instanceof <그 클래스>` 로 박히는 것** | **구현** ★★ | `javap` (2) |
| **`T::class` 가 `ldc class <그 클래스>` 인 것** | **구현** | `javap` (2) |
| **`typeOf<T>()` 가 `Reflection.typeOf` + `KTypeProjection.invariant` 조립인 것** | **구현** ★ | `javap` (2) |
| **선언 쪽 본체에 `Intrinsics.reifiedOperationMarker` 가 남는 것** | **구현** ★★ | `javap` (3) |
| **그 마커의 정수 코드 3/4/6 이 `is`/`T::class`/`typeOf` 인 것** | **구현 — 문서화된 계약 아님** ★ | `javap` (3) |
| **`ACC_SYNTHETIC` 이 붙는 것** | **구현(+상호운용 계약)** ★★ | `javap -v` (4) |
| **리플렉션 호출이 `UnsupportedOperationException` 인 것** | **구현** ★ | Java 실행 (4) |
| **`KType.toString()` 이 `kotlin-reflect` 유무로 달라지는 것** | **구현(런타임 의존)** ★★ | 실행 두 벌 (6) |
| **클래스 파일이 하나도 안 느는 것** | **구현** | `find … -name '*.class'` (2) |
| **`-jvm-target 21` 에서도 같았던 것** | **관찰(두 타깃)** | `diff` (10) |

★ **가장 중요한 구분 한 줄** — **「`is T` 를 쓸 수 있다」는 언어 보장이고,\
「그것이 `instanceof java/lang/String` 으로 박힌다」는 `javap` 로 본 구현이다.**\
그리고 **「그러니 런타임에 제네릭이 살아난다」는 둘 다 아니다** — 타입 인자는 여전히 소거된다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| `Class<T>` 인자를 받던 API 를 Kotlin 답게 감쌀 때 | `inline fun <reified T>` 한 줄 | 호출부에서 `T::class.java` 가 사라진다((6)) |
| 제네릭 함수 안에서 `Array<T>` 를 만들 때 | `reified` | 그것 말고는 방법이 없다((8)) |
| 타입으로 분기하는 짧은 유틸(`x is T`) | `reified` | 검사 한 줄로 펼쳐진다 |
| **중첩 제네릭을 구분해야 할 때** | `typeOf<T>()` | `T::class` 로는 **구분이 안 된다**((6)) |
| 인스턴스를 만들어야 할 때 | `() -> T` 팩토리 인자 | `T()` 는 문법에서 거부된다((7)) |
| **Java 에서도 부를 API** | `reified` **안 쓴다** | `ACC_SYNTHETIC` 이라 안 보인다((4)) |
| 몸통이 크거나 호출 자리가 많을 때 | 신중히 | 인라인의 코드 크기 대가를 그대로 진다([11번 주제](../11-inline-functions/) (8)) |
| 공개 라이브러리 API | 신중히 | 몸통이 남의 모듈로 복사된다([11번 주제](../11-inline-functions/)) |
| 재귀가 필요한 타입 탐색 | `reified` **안 된다** | 인라인은 재귀 불가((9)) — `KType` 을 값으로 넘겨 푼다 |
| 타입 인자까지 검사해야 할 때 | 원소를 직접 확인한다 | `is T` 는 **raw class 까지만** 본다((5)) |

판단 규칙 두 줄.

- **「호출자가 타입 인자를 글자로 적어 주나」로 정한다.** 적어 주면 `reified` 가 그 글자를 가져갈 수 있고,\
  값으로만 흘러오면(`Class<T>` 를 변수로 들고 있으면) `reified` 는 할 일이 없다.
- ★ **「그 타입을 얼마나 정밀하게 알아야 하나」로 도구를 고른다** — 클래스까지면 `T::class`, **인자까지면 `typeOf<T>()`**.

## 핵심 문장

- ★★ **`reified` 는 소거를 없애지 않는다. 소거되기 전에 글자를 박아 넣는 것**이다 —\
  그래서 **`inline` 이 선택이 아니라 전제**다(`only type parameters of inline functions can be reified.`).
- `reified` 없이 `x is T` 를 쓰면 **`cannot check for instance of erased type 'T (of fun <T> …)'`** 다.\
  두 에러가 이 주제의 좌표를 만든다.
- ★★ **호출 자리에서 `isA<String>(x)` 는 `instanceof java/lang/String` 한 줄이 된다.** 호출 자체가 사라진다.
- ★★ **되살아나는 것은 raw class 와 null 가능성뿐이다.**\
  `isA<List<String>>(listOf(1))` 이 **`true`** 이고 **경고도 안 난다** — `instanceof java/util/List` 까지만 보기 때문이다.
- ★ **`T::class.java` 와 `typeOf<T>()` 는 다른 것을 준다.** `List<Int>` 와 `List<String>` 이 전자에서는 **둘 다 `java.util.List`**,\
  후자에서는 **갈린다**. 그리고 후자의 출력은 **`kotlin-reflect.jar` 가 클래스패스에 있느냐로 통째로 달라진다.**
- ★ **선언 쪽 본체는 남지만 지뢰다** — `Intrinsics.reifiedOperationMarker(3, "T")` 다음 줄이 자리표(`instanceof Object` 등)이고,\
  인라인할 때 그것이 실제 타입으로 바꿔치기된다.
- ★★ **Java 는 이 함수를 못 부른다.** `ACC_SYNTHETIC` 이라 `javac` 가 **`cannot find symbol`** 이라고 하고,\
  리플렉션으로 뚫으면 **`UnsupportedOperationException: … can only be inlined at compilation time, not called directly.`** 다.
- ★ **`T()` 는 「소거 때문에」가 아니라 「`T` 가 식이 아니어서」 거부된다**(`type parameter 'T' is not an expression.`).\
  리플렉션 우회는 컴파일 통과 + **런타임 `NoSuchMethodException`** 이다 — 검사를 실행 시점으로 민 것이다.
- **소거된 `T` 로는 `Array(n) { }` 를 못 만든다**(`cannot use 'T' as reified type parameter.`) — 제네릭 배열이 대표 사용처다.
- ★ **`reified` 는 11의 「의미 없다」 경고를 끄지만 11의 제약(재귀 금지 등)은 그대로 물려받고, 전염되지는 않는다.**

## 관련 자료

- [`../README.md`](../README.md) — Kotlin 문법·API 주제 목록(이 주제는 12번)
- ★★ [11번 주제](../11-inline-functions/) — **직접 선행이자 전제.** 인라인이 **몸통을 호출 자리에 복사한다**는 것,\
  그 대가가 **코드 크기**라는 것, **본체가 남아 Java 가 부른다**는 것이 전부 거기가 정본이다.\
  **거기는 `reified` 를 「인라인의 세 번째 용도」로 넘겼고, 여기가 받는다**
- [10번 주제](../10-lambdas-and-higher-order-functions/) — 람다가 `Function1` 객체가 되는 것과 **`invoke(Object)Object` 라는 소거된 시그니처**.\
  이 주제가 뚫는 그 소거를 **처음 만나는 자리**다
- ★ [`../../../java/syntax/19-type-erasure/`](../../../java/syntax/19-type-erasure/) — **소거의 정본.**\
  **무엇이 지워지는가·제네릭 배열이 왜 안 되는가·브리지 메서드**는 거기까지, 여기는 **Kotlin 이 그것을 우회하는 방법**부터다
- [13번 주제](../13-extension-functions-and-properties/) — `List<Int>.describe()` 와 `List<String>.describe()` 가\
  **`platform declaration clash`** 로 충돌하는 것. **같은 소거가 확장 함수 쪽에서 내는 증상**이다
- [03번 주제](../03-null-safe-types/) — `Intrinsics.checkNotNullParameter`·`checkNotNullExpressionValue` 의 정본.\
  이 문서의 역어셈블에 계속 나온다
- [04번 주제](../04-smart-casts/) — `is` 가 성공한 뒤 타입이 좁혀지는 것
- [목록의 **28번 주제**](../28-generics-variance-in-out-star-where/)(제네릭 — 변성·star projection) — `*` 와 `in`/`out` 의 정본. **여기서는 타입 인자를 안 다뤘다**
- [목록의 **33번 주제**](../33-type-checks-and-casts-is-as/)(`is`/`as`/`as?`) — 타입 검사·캐스트 문법 자체의 정본
- 목록의 **35번 주제**(애너테이션과 use-site target) — `kotlin-reflect` 를 **프레임워크가 읽는** 자리
- 목록의 **39번 주제**(Java 상호운용 애너테이션) — Java 에서 볼 이름을 다루는 도구들.\
  **`reified` 는 그 도구로도 안 열린다**((4))

## 용어 풀이

- **타입 소거(type erasure)** — 컴파일이 끝나면 타입 인자가 사라지는 것. `List<Int>` 가 `java.util.List` 가 된다.
- **`reified`** — 인라인 함수의 타입 파라미터에 붙여 **호출 자리에서 실제 타입으로 치환**되게 하는 수식어.
- **인라인(inline)** — 함수를 부르지 않고 몸통을 호출 자리에 복사해 넣는 컴파일러 변환([11번 주제](../11-inline-functions/)).
- **타입 파라미터 / 타입 인자** — 선언 쪽의 `T` / 호출 쪽에 실제로 적는 `String`.
- **raw class** — 타입 인자를 뗀 클래스. `List<String>` 의 raw class 는 `java.util.List`.
- **`instanceof`** — 객체가 어떤 클래스인지 검사하는 JVM 명령. `is T` 가 이것이 된다.
- **`checkcast`** — 형 변환을 검사하는 JVM 명령. `as T` 가 이것이 된다.
- **`ldc class …`** — 클래스 리터럴을 상수 풀에서 밀어 넣는 JVM 명령. `T::class` 가 이것이 된다.
- **`KClass`** — Kotlin 의 클래스 표현(`T::class`). `.java` 로 JVM `Class` 로 내려간다.
- **`KType`** — Kotlin 의 **타입** 표현(`typeOf<T>()`). 타입 인자와 null 가능성까지 들고 있다.
- **`kotlin-reflect.jar`** — Kotlin 리플렉션 구현. **stdlib 와 별도 아티팩트**이고 없으면 `KType` 출력이 퇴화한다.
- **`Intrinsics.reifiedOperationMarker`** — 인라인 전 본체에 남는 자리표 마커. 직접 부르면 예외를 던진다.
- **`ACC_SYNTHETIC`** — "컴파일러가 만든 것이라 소스에는 없다" 는 클래스 파일 플래그. `javac` 가 그 멤버를 안 본다.
- **박싱(boxing)** — 원시 값을 객체로 감싸는 것. 타입 파라미터 자리의 `Int` 는 `java.lang.Integer` 다.

---

## 더 들어가면

- ★★ **`as T` 는 `reified` 유무로 「어디서 터지나」가 달라진다.** 던져서 확인했다.

```kotlin
// cast2.kt
inline fun <reified T> castR(x: Any): T = x as T

@Suppress("UNCHECKED_CAST")
fun <T> castE(x: Any): T = x as T

fun main() {
    val a: Any = castE<String>(1)          // 결과를 Any 로만 받는다
    println("Q castE<String>(1) 를 Any 로 받기 : $a (${a::class.java.name})")
    val b = runCatching { castR<String>(1) }
    println("R castR<String>(1) 를 Any 로 받기 : ${b.exceptionOrNull()?.let { it::class.java.name }}")
}
```

  **출력** (`java -cp "ocast2:kotlin-stdlib.jar" Cast2Kt`)

```text
Q castE<String>(1) 를 Any 로 받기 : 1 (java.lang.Integer)
R castR<String>(1) 를 Any 로 받기 : java.lang.ClassCastException
```

  ★ **`castE` 는 아무 일도 안 일어났다** — `String` 으로 받기로 한 값이 `Integer` 인 채 흘러간다.\
  소거된 `as T` 는 **바이트코드에 아무것도 안 남기고**, 검사는 호출자가 결과를 **구체 타입으로 받을 때**로 밀린다.\
  `Any` 로만 받으면 그 검사조차 안 온다. **`reified` 를 붙이면 그 자리에서 `checkcast` 가 돌아 즉시 터진다.**\
  ★ 「무음 실패를 에러로 바꾼다」가 `reified` 의 값어치 중 가장 실무적인 것이다.
- **`reifiedOperationMarker` 의 정수 코드**는 `3`(`is`)·`4`(`T::class`)·`6`(`typeOf`) 로 관찰됐다.\
  **다른 코드가 무엇인지는 안 찍어 봤다** — stdlib 소스를 읽으면 나오겠지만 **이 문서는 읽지 않았다.**
- **`javap` 로 본 본체의 자리표가 서로 다르다** — `isA` 는 `instanceof java/lang/Object`,\
  `nameOf` 는 `ldc class java/lang/Object`, `typeText` 는 `aconst_null` 이다.\
  ★ **`typeText` 의 자리표가 `null` 이라는 것**이 (4)의 방어선이 왜 필요한지를 말해 준다 — 마커가 안 막으면 `NullPointerException` 이다.
- **`simpleOf<Int>()` 가 `Int` 인데 `nameOf<Int>()` 가 `java.lang.Integer` 인 것**은 `KClass` 가 **Kotlin 이름을 따로 들고 있기** 때문이다.\
  단 `simpleName` 은 `kotlin-reflect` 없이도 나왔다 — **`toString()` 과 달리 이름 정도는 stdlib 가 답한다.**\
  ★ **어디까지가 stdlib 이고 어디부터 `kotlin-reflect` 인지는 이 문서가 경계를 다 긋지 않았다**(두 함수만 확인했다).
- **이 문서에서 성능은 한 번도 재지 않았다.** `javap` 로 본 것은 **어떤 명령이 남느냐**까지이고,\
  "`is T` 가 `Class.isInstance` 보다 빠르다" 같은 것은 **하지 않은 주장**이다.
- **못 잰 것** — `kotlinx.serialization` 의 `serializer(typeOf<T>())` 처럼 **`KType` 을 실제로 소비하는 라이브러리**는\
  stdlib 밖이라 이 환경에 없다. **`typeOf<T>()` 가 그 라이브러리에서 무엇을 하는지는 돌려 보지 않았다.**
