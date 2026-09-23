# kotlin/syntax/12 — `reified` 타입 파라미터: 소거를 뚫는 방법 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javap` 에서 실제로 얻었다.\
> 역어셈블은 **기본 `-jvm-target`(1.8 · `major version: 52`)** 이 정본이고, 12번에서만 `-jvm-target 21` 을 따로 찍었다.\
> ★ **`typeOf<T>()` 를 쓰는 출력은 클래스패스에 `kotlin-reflect.jar` 가 있느냐로 달라진다** — 3번·12번에 양쪽을 다 실었다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★ 통과하는 것은 `[D]` 하나뿐 — 에러 둘이 `reified` 의 정의를 만든다

**출력** (`kotlinc bad1.kt` — `[A]`)

```text
===== 소스: bad1.kt =====
fun <reified T> isA(x: Any): Boolean = x is T
===== kotlinc bad1.kt =====
bad1.kt:1:6: error: only type parameters of inline functions can be reified.
fun <reified T> isA(x: Any): Boolean = x is T
     ^^^^^^^
(exit 1)
```

**출력** (`kotlinc bad2.kt` — `[B]`)

```text
===== 소스: bad2.kt =====
fun <T> isA(x: Any): Boolean = x is T
===== kotlinc bad2.kt =====
bad2.kt:1:37: error: cannot check for instance of erased type 'T (of fun <T> isA)'.
fun <T> isA(x: Any): Boolean = x is T
                                    ^
(exit 1)
```

**출력** (`kotlinc bad4.kt` — `[C]`)

```text
===== 소스: bad4.kt =====
class Box<reified T>(val x: T)
===== kotlinc bad4.kt =====
bad4.kt:1:11: error: only type parameters of inline functions can be reified.
class Box<reified T>(val x: T)
          ^^^^^^^
(exit 1)
```

**왜 그런가**

| | 형태 | 결과 |
|---|---|---|
| `[A]` | `reified` 만 | 에러 — `only type parameters of inline functions can be reified.` |
| `[B]` | 둘 다 없음 | 에러 — `cannot check for instance of erased type 'T (of fun <T> isA)'.` |
| `[C]` | 클래스의 타입 파라미터 | 에러 — **`[A]` 와 글자 하나 안 다르다** |
| `[D]` | `inline` + `reified` | **통과** |

- ★ **`[A]` 와 `[C]` 의 문구가 같다.** 컴파일러는 「클래스라서」라고 말하지 않고
  **「인라인 함수의 타입 파라미터에만 붙는다」** 는 **같은 규칙 한 줄**을 댄다.
  클래스는 인라인될 수가 없으니 그 규칙에 자동으로 걸린다.
- ★★ **두 문구를 붙여 읽으면 정의가 나온다.**
  `[B]` 가 **「런타임에 `T` 가 없다」**(소거), `[A]` 가 **「그 낱말은 인라인 전용이다」**.
  합치면 — **`reified` 는 소거를 없애는 것이 아니라, 인라인이 몸통을 복사해 넣는 그 순간에 타입을 박아 넣는 것**이다.

```text
   x is T  ──▶ cannot check for instance of erased type 'T'   ← 런타임에 없다
      │
      └─ reified ──▶ only type parameters of inline functions can be reified.
                          │
                          └─ inline 을 같이 붙여야 통과 = 복사할 자리가 있어야 채워 넣는다
```

### 2. ★★ `A true` · `B false` · **`C` 도 `true`** — 타입 인자는 안 살아난다

**출력** (`java -cp "outex:kotlin-stdlib.jar" ExKt` 의 앞 세 줄)

```text
A isA<String>("hi")            : true
B isA<String>(1)               : false
C isA<List<String>>(listOf(1)) : true
```

**출력** (`kotlinc ex.kt -d outex`)

```text
(exit 0)
```

**왜 그런가**

`javap` 가 이유를 한 줄로 말한다.

```text
  public static final boolean callIsAList(java.lang.Object);
    Code:
       ...
      10: aload_1
      11: instanceof    #51                 // class java/util/List
      14: ireturn
```

- ★★ **`String` 이라는 글자가 바이트코드 어디에도 없다.** 검사는 `instanceof java/util/List` 까지다.
  그래서 `Int` 가 든 리스트가 **`List<String>` 인지 물었는데 `true`** 로 통과한다.
- ★★ **컴파일러가 아무 말도 안 했다**(`exit 0`, 경고 0줄). 같은 검사를 `reified` 없이 쓰면 **에러**인데,
  `reified` 를 붙이면 **조용히 반쪽짜리 검사**가 된다 — **에러가 무음 오답으로 바뀌는 교환**이다.
- **그래서 정확한 범위는 이렇다** — `reified` 가 되살리는 것은 **raw class 와 null 가능성**이고,
  **타입 인자는 여전히 소거된다.** 「제네릭이 런타임에 살아난다」는 틀린 요약이다.
- 원소까지 확인하려면 **원소를 직접 보거나**(`xs.all { it is String }`), 타입을 값으로 들고 다녀야 한다(`typeOf<T>()`, 3번).

### 3. ★★ `java.lang.Integer` · `Int` · **클래스패스에 따라 달라지는 것**

**출력** (`java -cp "outex:kotlin-stdlib.jar" ExKt` — `kotlin-reflect.jar` **없이**)

```text
D nameOf<Int>()                : java.lang.Integer
E nameOf<String>()             : java.lang.String
F simpleOf<Int>()              : Int
G typeText<List<String>>()     : java.util.List<java.lang.String> (Kotlin reflection is not available)
H typeText<Int>()              : int (Kotlin reflection is not available)
I typeText<String?>()          : java.lang.String? (Kotlin reflection is not available)
```

**출력** (`java -cp "outex:kotlin-stdlib.jar:kotlin-reflect.jar" ExKt` — **같은 클래스 파일**)

```text
G typeText<List<String>>()     : kotlin.collections.List<kotlin.String>
H typeText<Int>()              : kotlin.Int
I typeText<String?>()          : kotlin.String?
```

**왜 그런가**

- ★ **`D` 와 `F` 가 갈리는 이유** — `T::class` 는 **`KClass`** 이고 `simpleName` 은 **Kotlin 이름**(`Int`)을 답한다.
  거기에 `.java` 를 붙이는 순간 **JVM `Class` 로 내려가고**, 타입 파라미터 자리의 `Int` 는 **참조 타입이라 박싱**된다 →
  `java.lang.Integer`. 호출 자리의 바이트코드가 그대로 보여 준다 — `ldc class java/lang/Integer`.
- ★★ **`G` 가 두 번 달랐다면 바꾼 것은 클래스패스다.** `kotlin-reflect.jar` 가 없으면 `KType.toString()` 이
  **JVM 이름으로 퇴화하고 `(Kotlin reflection is not available)` 를 덧붙인다.**
  **같은 클래스 파일, 같은 JVM 인데 출력이 다르다** — 이 절을 싣는 문서는 **환경을 밝혀야 검증이 성립한다.**
- ★ **`T::class.java` 로 구분 못 하는데 `typeOf<T>()` 로 구분되는 짝** — `List<Int>` 와 `List<String>` 이다.

```text
                     describe<List<Int>>()   describe<List<String>>()
   T::class.java  →  java.util.List          java.util.List     ← 같다
   typeOf<T>()    →  List<Int>               List<String>       ← 갈린다
```

  JSON 라이브러리가 `TypeToken` 류를 요구하는 이유가 정확히 이것이고, Kotlin 쪽 답이 `typeOf<T>()` 다.

### 4. ★★ `javac` 는 **`cannot find symbol`**, 리플렉션은 찾지만 **부르면 터진다**

**출력** (`javac -cp oapi:kotlin-stdlib.jar UseReified.java -d oj`)

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

**출력** (`java -cp "oj:oapi:kotlin-stdlib.jar" UseRefl`)

```text
L reflective lookup ok : public static final boolean ApiKt.isA(java.lang.Object)
M isSynthetic()        : true
N invoke threw         : java.lang.UnsupportedOperationException: This function has a reified type parameter and thus can only be inlined at compilation time, not called directly.
```

**왜 그런가**

- ★★ **다른 플래그는 `ACC_SYNTHETIC` 하나다.** 같은 파일의 평범한 `inline fun plain` 에는 안 붙는다 —
  **「인라인이라서」가 아니라 「`reified` 라서」** 붙는다.
- `ACC_SYNTHETIC` 은 「**컴파일러가 만든 것이라 소스에는 없다**」는 표시이고, `javac` 는 그런 멤버를 **해석에서 뺀다.**
  그래서 **「없다」가 아니라 「안 보인다」** — `javap` 로는 버젓이 보인다.
- ★★ **리플렉션은 찾는다**(`getDeclaredMethod` 성공, `isSynthetic()` 이 `true`). 그런데 부르면 **런타임 예외**다.
  8번의 자리표를 그대로 실행하지 않도록 **`reifiedOperationMarker` 가 던지는 것**이고,
  그 메시지가 이 주제의 한 줄 요약이다 — *can only be inlined at compilation time, not called directly.*
- **그래서 Java 와 나눠 쓸 API 는 두 겹으로 낸다.**

```kotlin
fun <T : Any> decodeOld(text: String, type: Class<T>): T = ...          // Java 가 부른다
inline fun <reified T : Any> decode(text: String): T =                   // Kotlin 이 부른다
    decodeOld(text, T::class.javaObjectType)
```

### 5. ★ `T()` 는 「**T 는 식이 아니다**」로 거부된다 — 소거 때문이 아니다

**출력** (`kotlinc bad3.kt`)

```text
===== 소스: bad3.kt =====
inline fun <reified T> make(): T = T()
===== kotlinc bad3.kt =====
bad3.kt:1:36: error: type parameter 'T' is not an expression.
inline fun <reified T> make(): T = T()
                                   ^
(exit 1)
```

**출력** (`kotlinc mk.kt -d omk` → `java -cp "omk:kotlin-stdlib.jar" MkKt`)

```text
M mk<NoArg>()   : NoArg()
N mk<NeedsArg>(): threw java.lang.NoSuchMethodException: NeedsArg.<init>()
```

**왜 그런가**

- ★★ **에러가 대는 이유가 소거가 아니다.** `type parameter 'T' is not an expression.` —
  **`T` 라는 이름만으로는 어느 생성자를 부를지 정해지지 않는다**는 **문법 차원의 거부**다.
  `reified` 로 클래스를 알아도 **생성자 시그니처는 타입 이름에 안 들어 있다.**
- **리플렉션 우회는 컴파일된다.** 그런데 `mk<NeedsArg>()` 는 **컴파일 통과 + 런타임 `NoSuchMethodException`** 이다.
  ★ **에러를 실행 시점으로 민 것**이지 푼 것이 아니다.
- **검사를 컴파일 타임으로 되돌리는 법은 팩토리를 인자로 받는 것**이다.

```kotlin
inline fun <reified T> mk(factory: () -> T): T = factory()
// mk { NeedsArg(1) }  ← 생성자 인자를 컴파일러가 검사한다
```

  그러면 `reified` 는 **타입 이름이 필요한 일**(`is T`·`T::class`)에만 쓰고, **생성은 람다가 맡는다.**

### 6. ★★ `castE` 는 **아무 일도 안 일어나고**, `castR` 은 그 자리에서 터진다

**출력** (`java -cp "ocast2:kotlin-stdlib.jar" Cast2Kt`)

```text
Q castE<String>(1) 를 Any 로 받기 : 1 (java.lang.Integer)
R castR<String>(1) 를 Any 로 받기 : java.lang.ClassCastException
```

**왜 그런가**

```text
  public static final java.lang.String callCastR(java.lang.Object);   ← reified
       ...
      10: aload_1
      11: checkcast     #30                 // class java/lang/String   ★ 함수 안에서 검사
      14: areturn

  public static final java.lang.String callCastE(java.lang.Object);   ← 소거
       ...
       6: aload_0
       7: invokestatic  #34                 // Method castE:(Ljava/lang/Object;)Ljava/lang/Object;
      10: checkcast     #30                 // class java/lang/String   ★ 돌아온 뒤에 검사
      13: areturn
```

- ★★ **소거된 `as T` 는 바이트코드에 아무것도 안 남긴다.** 검사는 **호출자가 결과를 구체 타입으로 받을 때**로 밀린다.
  `Any` 로만 받으면 **그 검사조차 안 온다** — `String` 이라고 선언한 값이 `Integer` 인 채 흘러간다(`Q`).
- **`val a: String` 으로 받으면 달라진다** — 돌아온 자리에 `checkcast` 가 생겨 **거기서** `ClassCastException` 이 난다.
  **터지기는 하지만 「누가 틀렸나」가 한 칸 멀어진다.**

**출력** (`java -cp "ocast3:kotlin-stdlib.jar" Cast3Kt`)

```text
S val a: String 로 받기 : java.lang.ClassCastException
```

- ★ **한 줄 요약** — **`reified` 는 무음 실패를 그 자리의 에러로 바꾼다.** 그것이 실무에서 가장 큰 값어치다.

### 7. ★★ 인라인이 **몸통을 호출 자리에 복사**하기 때문에, 그 자리에서 `T` 를 안다

**왜 그런가**

- **인라인의 한 문장** — 「함수를 부르지 말고 **몸통을 호출 자리에 복사해 넣어라**」([11번 주제](../11-inline-functions/)).
  그 문장의 「**호출 자리**」가 열쇠다. 호출 자리에서는 `isA<String>` 이라고 **글자로 적혀 있으므로**
  컴파일러가 `T` 가 `String` 임을 **그 순간에 알고 있다.** 복사하면서 그 글자를 채워 넣으면 된다.
- **`invokestatic isA` 는 남지 않는다.** 호출이 통째로 사라지고 `instanceof java/lang/String` 한 줄이 된다(2번).

```text
  public static final boolean callIsAString(java.lang.Object);
       ...
      10: aload_1
      11: instanceof    #39                 // class java/lang/String
      14: ireturn
```

- ★★ **맞는 쪽은 「컴파일 타임에 타입이 박힌다」다.** 런타임에 타입 정보가 새로 생기는 것이 아니다 —
  그래서 **호출 자리마다 다른 글자**가 박히고, **호출 자리가 없는 본체**에는 아무것도 못 박는다(8번).
- **세 번째 용도** — [11번 주제](../11-inline-functions/)는 `inline` 의 용도로 ① 람다 객체 제거 ② 비지역 `return` 둘을 댔다.
  여기에 ③ **`reified`** 가 붙는다. ①②는 **선택**이지만 ③은 **전제**다 — `reified` 를 쓰려면 `inline` 이 **반드시** 있어야 한다.

### 8. ★ 본체는 남고, 그 안에는 **`reifiedOperationMarker` 와 자리표**가 들어 있다

**출력** (`javap -c -p out/IcodeKt.class` — 선언 쪽 본체)

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
```

**왜 그런가**

- **본체는 남는다.** [11번 주제](../11-inline-functions/)의 (3)이 「인라인해도 함수는 사라지지 않는다」를 보여 준 그대로다.
- ★ **`x is T` 자리에 들어 있는 함수 이름은 `Intrinsics.reifiedOperationMarker`** 다.
  인자는 `(3, "T")` — **정수가 연산 종류**(`3`=`is`, `4`=`T::class`, `6`=`typeOf`)이고 **문자열이 어느 타입 파라미터인가**다.
  (★ 이 정수 대응은 **관찰이지 문서화된 계약이 아니다.**)
- ★★ **그 다음 줄이 자리표다** — 여기서는 `instanceof java/lang/Object`.
  **인라인할 때 컴파일러가 이 줄을 실제 타입으로 바꿔치기한다.**
  바꿔치기 안 된 채로 실행하면 `x is Any` 가 되어 **무엇이든 `true`** 다. `typeOf` 쪽 자리표는 **`aconst_null`** 이라 더 나쁘다 —
  `null.toString()` 이 된다.
- ★★ **방어선 두 개**
  1. **`ACC_SYNTHETIC`** — `javac` 가 그 멤버를 아예 안 본다(4번).
  2. **`reifiedOperationMarker` 의 런타임 예외** — 리플렉션으로 뚫어도
     `UnsupportedOperationException: … can only be inlined at compilation time, not called directly.`

### 9. ★ **전염되지 않는다** — 에러가 `inner` 쪽을 가리킨다

**출력** (`kotlinc bad6.kt`)

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

**출력** (`kotlinc bad5.kt` — 재귀)

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

**왜 그런가**

- ★★ **에러가 3행, 즉 `inner` 의 선언 줄을 가리킨다.** `outer` 는 멀쩡하다.
  `outer` 가 펼쳐질 때 `T` 를 알아도, 그것이 부르는 `inner` 는 **평범한 호출**이라 타입 인자를 못 받는다.
  **한 문장으로 — `reified` 는 「그 함수의 몸통 안」에서만 유효하고, 호출 사슬을 타고 내려가지 않는다.**
  이어 가려면 `inner` 도 `inline fun <reified T>` 여야 한다.
- **재귀는 금지다** — `inline function … cannot be recursive.` 펼치기가 끝나지 않기 때문이고,
  [11번 주제](../11-inline-functions/)의 제약이 그대로 적용된다.
- **`noinline`·`crossinline` 은 파라미터 쪽 낱말**이고 `reified` 는 **타입 파라미터 쪽 낱말**이라 **직교한다.**
  ★ 다만 **이 문서는 그 조합을 따로 던져 보지 않았다.**

### 10. ★ `reified` 가 있으면 **그 경고가 안 난다**

**출력** (`kotlinc warn1.kt`)

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

**왜 그런가**

- [11번 주제](../11-inline-functions/)에서 람다를 안 받는 `inline` 함수는
  **`expected performance impact from inlining is insignificant.`** 경고를 받았다.
- ★★ **`isA` 는 람다를 하나도 안 받는데 조용하다.** 같은 파일의 `plainGeneric` 은 **경고를 받는다** —
  둘의 차이는 **`reified` 하나**뿐이다.
- **그래서 컴파일러가 `inline` 을 정당하다고 보는 기준은 둘이다** —
  ① **펼칠 수 있는 람다가 있나**(11번의 결론) ② **`reified` 타입 파라미터가 있나**.
  둘 중 **하나라도** 있으면 조용하고, 없으면 「의미 없다」고 말한다.

### 11. ★ `cannot use 'T' as reified type parameter` — `Array` 생성자 자체가 `reified` 다

**출력** (`kotlinc bad8.kt -d o8`)

```text
===== 소스: bad8.kt =====
fun <T> packDirect(xs: List<T>): Array<T> = Array(xs.size) { xs[it] }
===== kotlinc bad8.kt =====
bad8.kt:1:45: error: cannot use 'T' as reified type parameter. Use a class instead.
fun <T> packDirect(xs: List<T>): Array<T> = Array(xs.size) { xs[it] }
                                            ^^^^^
(exit 1)
```

**출력** (`java -cp "oarr:kotlin-stdlib.jar" ArrKt`)

```text
P pack("a","b").javaClass : [Ljava.lang.String;
Q pack(1,2).javaClass     : [Ljava.lang.Integer;
R empty<String>(2)        : [Ljava.lang.String; [null, null]
```

**왜 그런가**

- ★ **문구가 쓰는 낱말은 `reified type parameter` 다.** 즉 **`Array(n) { }` 생성자 자체가 `reified` 타입 파라미터를 요구하는 인라인 함수**이고,
  소거된 `T` 를 그 자리에 넘길 수 없다는 뜻이다. **에러가 그 사실을 알려 준다.**
- **런타임 클래스는 `[Ljava.lang.String;`·`[Ljava.lang.Integer;`** 로 **원소 타입이 박혀 있다.**
- ★★ **`Array<Any?>` 를 만들어 두고 나중에 속이는 것은 안 된다** — 던져서 확인했다.

```kotlin
// arr2.kt
@Suppress("UNCHECKED_CAST")
fun main() {
    val anyArr: Array<Any?> = arrayOfNulls<Any>(2)
    val r = runCatching { val asStr = anyArr as Array<String?>; asStr.size }
    println("T Array<Any?> 를 Array<String?> 로 캐스트 : ${r.exceptionOrNull()?.message ?: "ok"}")
    val strArr: Array<String?> = arrayOfNulls<String>(2)
    println("U arrayOfNulls<String>(2).javaClass       : ${strArr.javaClass.name}")
}
```

  **출력** (`java -cp "oarr2:kotlin-stdlib.jar" Arr2Kt`)

```text
T Array<Any?> 를 Array<String?> 로 캐스트 : class [Ljava.lang.Object; cannot be cast to class [Ljava.lang.String; ([Ljava.lang.Object; and [Ljava.lang.String; are in module java.base of loader 'bootstrap')
U arrayOfNulls<String>(2).javaClass       : [Ljava.lang.String;
```

  ★ **배열은 원소 타입이 런타임 클래스 자체**(`[Ljava.lang.String;`)라서 **나중에 캐스트로 속일 수가 없다.**
  `as` 를 썼는데도 **그 자리에서 `ClassCastException`** 이다. 그래서 **만드는 시점에 진짜 타입을 알아야 하고**,
  그것이 `reified` 의 가장 오래된 사용처다
  (Java 쪽 사정은 [`../../../java/syntax/19-type-erasure/`](../../../java/syntax/19-type-erasure/)가 정본이다).

### 12. 환경은 `kotlin-reflect.jar`, 타깃은 21 에서도 같았다

**출력** (`javap -v -p` 의 `major version` · `javap -c -p` 전체 `diff`)

```text
=== major ===
  major version: 65        (out21 — -jvm-target 21)
  major version: 52        (out   — 기본값 1.8)
===== 21 에서 전체 diff (1.8 대비) =====
icode: 1.8 과 21 이 같다
```

**왜 그런가**

- **클래스패스에서 `kotlin-reflect.jar` 를 넣고 빼면** `typeOf<T>().toString()` 이 달라진다(3번).
  `T::class.simpleName` 은 **없어도 나왔다** — ★ **어디까지가 stdlib 이고 어디부터 리플렉션 아티팩트인지
  이 문서는 두 함수만 확인했고 경계를 다 긋지 않았다.**
- **확인한 방법** — 같은 소스를 `-jvm-target 21` 로 다시 컴파일해 `javap -c -p` 출력을 `diff` 했다.
  `major version` 만 52 → 65 로 바뀌고 **한 글자도 다르지 않았다.**
  ★ **「같았다」는 관찰이지 보장이 아니다** — 두 타깃만 봤다.
- **`List<Int>.describe()` 와 `List<String>.describe()`** 를 같이 선언하면
  **`platform declaration clash`** 다(둘의 JVM 시그니처가 `describe(Ljava/util/List;)Ljava/lang/String;` 로 같다).
  그 정본은 [13번 주제](../13-extension-functions-and-properties/)의 (9)이고, 거기서도 고치는 법은 `@JvmName` 이다.
  **`reified` 로는 못 고친다** — 선언 쪽 시그니처의 문제이지 호출 쪽의 문제가 아니기 때문이다.
- **「무엇이 지워지는가」의 정본은 [`../../../java/syntax/19-type-erasure/`](../../../java/syntax/19-type-erasure/)** 다.

## 실행 검증

```text
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
openjdk version "21.0.5" 2024-10-15 LTS
OpenJDK Runtime Environment Temurin-21.0.5+11 (build 21.0.5+11-LTS)
OpenJDK 64-Bit Server VM Temurin-21.0.5+11 (build 21.0.5+11-LTS, mixed mode, sharing)
```

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `bad1.kt` | `reified` 만 쓰면 나는 에러 | `kotlinc` (컴파일 실패가 결과) |
| `bad2.kt` | `reified` 없이 `x is T` 가 나는 에러 | `kotlinc` (컴파일 실패가 결과) |
| `bad4.kt` | 클래스의 타입 파라미터에 `reified` — **`bad1` 과 같은 문구** | `kotlinc` (컴파일 실패가 결과) |
| `bad3.kt` | `T()` 가 **식이 아니라서** 거부되는 것 | `kotlinc` (컴파일 실패가 결과) |
| `bad5.kt` | `reified` 인라인의 재귀 금지 | `kotlinc` (컴파일 실패가 결과) |
| `bad6.kt` | `reified` 가 **전염되지 않는 것** — 에러가 안쪽을 가리킨다 | `kotlinc` (컴파일 실패가 결과) |
| `bad8.kt` | 소거된 `T` 로 `Array(n) { }` 를 못 만드는 것 | `kotlinc` (컴파일 실패가 결과) |
| `warn1.kt` | `reified` 가 「의미 없다」 경고를 **끄는 것** | `kotlinc` (경고 1건 · `exit 0`) |
| `icode.kt` | `is T`·`T::class`·`typeOf<T>()` 가 호출 자리에서 펼쳐지는 것 + 선언 쪽 자리표 | `kotlinc` → `javap -c -p` |
| `icode.kt` (타깃 21) | 결론이 `-jvm-target` 에 안 흔들리는 것 | `kotlinc -jvm-target 21` → `javap -c -p` → `diff` |
| `ex.kt` | `A`\~`I` — 타입 인자가 안 살아나는 것·박싱·`typeOf` | `kotlinc` → `java` **2벌**(reflect 유·무) |
| `nul2.kt` | null 가능성은 **살아나는 것**(`ifnull` 대 `instanceof`) | `kotlinc` → `java` + `javap -c -p` |
| `api.kt` + `UseReified.java` | `javac` 가 `reified` 함수를 **못 보는 것** | `kotlinc` → `javac` (컴파일 실패가 결과) |
| `api.kt` + `UseRefl.java` | 리플렉션으로 찾을 수는 있으나 **부르면 예외** | `javac` → `java` |
| `mk.kt` | 리플렉션 우회가 **런타임으로 밀리는 것** | `kotlinc` → `java` |
| `arr.kt` | `reified` 로 만든 배열의 **런타임 원소 타입** | `kotlinc` → `java` |
| `use.kt` | `T::class` 와 `typeOf<T>()` 가 갈리는 지점 · 실무 2단 API | `kotlinc` → `java` **2벌**(reflect 유·무) |
| `cast2.kt` · `cast3.kt` | 소거된 `as T` 가 **무음 통과**하는 것과 검사가 밀리는 자리 | `kotlinc` → `java` + `javap -c -p` |
| `arr2.kt` | `Array<Any?>` 를 `Array<String?>` 로 **못 속이는 것** | `kotlinc` → `java` |

**구현 의존 항목** — `javap` 의 명령 이름·상수 풀 번호, `Intrinsics.reifiedOperationMarker` 라는 이름과 그 정수 코드(3/4/6),
자리표가 `instanceof Object`·`ldc Object`·`aconst_null` 인 것, `ACC_SYNTHETIC` 플래그,
`UnsupportedOperationException` 의 메시지 문구, `KType.toString()` 의 두 가지 모양 — 전부 **이 컴파일러·이 런타임의 산출물**이다.\
반면 **「`reified` 는 `inline` 에만 붙는다」·「`is T`/`as T`/`T::class`/`typeOf<T>()` 가 열린다」·「타입 인자는 안 살아난다」·
「`T()` 는 못 쓴다」·「Java 에서 못 부른다」·「재귀 불가」·「전염되지 않는다」** 는 **언어 규칙**이라 타깃과 무관하다.

**★ 던져 봤더니 예상과 달랐던 것 — 네 건**

1. ★★ **`isA<List<String>>(listOf(1))` 이 `true` 인데 경고가 한 줄도 없다.**
   `reified` 없이 같은 것을 쓰면 **에러**인데, `reified` 를 붙이면 **조용한 반쪽 검사**가 된다.
   **에러를 무음 오답과 맞바꾼 셈**이라, 이 주제에서 가장 위험한 자리가 여기다.
2. ★ **`T()` 가 거부되는 이유가 소거가 아니었다.** `type parameter 'T' is not an expression.` —
   **문법 차원의 거부**다. 「소거 때문에 생성자를 못 부른다」고 적었으면 틀릴 뻔했다.
3. ★★ **같은 클래스 파일이 클래스패스에 따라 다른 답을 냈다.** `typeOf<T>().toString()` 이
   `kotlin-reflect.jar` 유무로 `kotlin.collections.List<kotlin.Int>` ↔
   `java.util.List<java.lang.Integer> (Kotlin reflection is not available)` 로 갈린다.
   **환경을 안 밝히면 이 절은 통째로 검증 불가**였다.
4. ★ **`reified` 가 11번의 「의미 없다」 경고를 끈다.** 람다를 안 받는데도 조용하다 —
   컴파일러가 보는 인라인의 정당한 사유가 **하나가 아니라 둘**이었다.

**안 걸린 것도 출력이다** — `mk<NeedsArg>()` 는 **컴파일러가 아무 말도 하지 않는다.**
생성자가 없다는 사실은 **실행해야만** `NoSuchMethodException` 으로 드러난다.
**「컴파일이 통과했다」가 「타입이 맞다」를 뜻하지 않는** 전형적인 자리다.
