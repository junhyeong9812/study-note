# kotlin/syntax/32 — 동등성: `==`/`===`·`equals` 규약·`data class` 와의 관계 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Equality](https://kotlinlang.org/docs/equality.html)(`a == b` 는 **`a?.equals(b) ?: (b === null)`** · 부동소수점은 **정적 타입**에 따라 IEEE 754 와 `equals` 가 갈린다 · 배열은 `contentEquals`) · [Operator overloading — Equality and inequality operators](https://kotlinlang.org/docs/operator-overloading.html) · [`Any.equals`](https://kotlinlang.org/api/core/kotlin-stdlib/kotlin/-any/equals.html).
> **실행 검증** — 이 문서의 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javac`·`javap` 에서 실제로 얻었다.\
> `kotlinc` 11회(경고 줄을 세는 1회 포함 · 컴파일 실패 1벌 · 경고 3벌) · `java` 10회(`-XX:AutoBoxCacheMax` 1판 포함) · `javac` 1회 · `javap` 5회 · `unzip` 1회.\
> ★★ 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적지 않았다. 소스 펜스의 첫 줄 배너도 캡처가 찍었다.
> **버전** — `==`/`===` 의 의미는 1.0 부터다. 이 문서의 **진단 문구와 경고의 유무는 K2(2.4.20)** 의 것이다.
> **경계** — ★★ **해시 자료구조의 원리**(버킷·충돌·왜 `hashCode` 가 먼저인가)는 [`cs/data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/)이 정본이다 — 여기는 「**Kotlin 의 `==` 가 무엇으로 번역되고, 규약을 어기면 JVM 컬렉션이 무엇을 잃나**」까지다.\
> `data class` 가 **`equals` 를 만든다는 것**과 「본문 프로퍼티는 빠진다」의 첫 실측은 [22번 주제](../22-data-class-generated-members/) (2)·(7)이 정본이다. `value class` 의 **`===` 금지**는 [26번 주제](../26-value-class-and-boxing/)가 정본이다. `==` 가 연산자 번역표에 **없다**는 것은 [31번 주제](../31-operator-overloading-infix-and-invoke/) (5)에서 넘겨받았다.
> **대비** — ★★★ Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **27번**([`27-equals-hashcode-contract/`](../../../java/syntax/27-equals-hashcode-contract/)) — Java 는 **`==` 가 참조 비교**다. 같은 모양을 `javac` 로 던져 나란히 놓았다((2)).\
> Python 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **30번**([`30-repr-eq-hash-contracts/`](../../../python/syntax/30-repr-eq-hash-contracts/)) · Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **28번**([`28-partialeq-eq-partialord-ord-and-hash-contracts/`](../../../rust/syntax/28-partialeq-eq-partialord-ord-and-hash-contracts/)) — **같은 규약 위반 실험**을 한 형제다((9)).
> 이 본문은 Claude 작성이다(원고 없음).

★ **본체는 둘째 창이다** — 「**규약을 하나씩 깬 키를 `HashSet` 과 `ArrayList` 에 넣고, 둘이 갈린 칸을 스크립트가 센 격자**」.
첫째 창(`javap`)은 `==` 가 **무엇으로 번역되는지**를 보여 주고, 둘째 창은 그 번역 위에서 **규약을 어기면 무엇을 잃는지**를 보여 준다.

## 이 주제가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **언어 보장** | 명세·공식 문서가 약속한 것 | ★★★ `a == b` 는 **`a?.equals(b) ?: (b === null)`** · `===` 는 **동일성** · 부동소수점 `==` 는 **정적 타입이 `Double`/`Float` 이면 IEEE 754** · `equals` 규약(반사·대칭·추이·일관·`null`) |
| **구현(JVM 백엔드·JDK)** | kotlinc 가 내리는 방식 · JDK 컬렉션의 코드 | `==` → **`Intrinsics.areEqual`** · 원시 `Int` → **`if_icmpne`** · ★★ **`Integer` 캐시(-128..127)** · ★ `HashMap` 이 **`==` 를 먼저 보는 것**((4)) |
| **이 판의 관찰** | kotlinc 2.4.20 에서 이번에 본 것 | ★ `equals` 만 재정의해도 **경고 0줄**((6)) · 배열 `==` 경고 · `Int?` 의 `===` 가 **경고**(에러 아님) |

## 이 판

```text
===== kotlinc -version =====
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | (값으로는 없다) — **`hashCode()` 값을 한 번도 찍지 않았다** | `Object.hashCode` 는 실행마다 바뀐다. 이 문서는 **「같나 다르나」와 그 결과(`size`·`contains`)만** 찍는다 |
| 원리상 흔들릴 수 있다 | ★ 격자 `R2` 줄의 **`size=2`** | `R2` 는 `hashCode` 를 안 고쳐 **두 객체의 기본 해시가 우연히 같으면** 답이 바뀐다. 두 캡처에서 같았다 — 그러나 **보장이 아니다** |
| 안 흔들린다 | 격자의 나머지 칸 · 「갈린 칸 N / M」 줄 | 해시를 직접 정했거나(`R1`·`R4`·`R5`) `data class` 가 값으로 정한다(`R3`·`R6`) |
| 안 흔들린다 | ★ `Int?` 의 `127`/`128` 줄 | **같은 JVM·같은 옵션**이면 같다 — 옵션을 바꾸면 바뀐다((3)이 그것을 보인다) |
| 안 흔들린다 | `javap` 출력 · 진단의 **문구·`파일:줄:칸`** · 모든 **종료 코드** | 결정적이다 |

★ 근거 — 캡처 스크립트를 처음부터 두 번 돌려 **블록 전체를 바이트 단위로 대조**했다(수치는 3-answer 의 「실행 검증」).

## 한눈에 — 쉽게 말하면

**`==` 는 「내용이 같은가」를, `===` 는 「같은 물건인가」를 묻는다.** 쌍둥이 둘은 `==` 이지만 `===` 가 아니다.

Java 를 아는 사람에게는 **이름이 뒤집혔다** — Java 의 `==` 가 Kotlin 의 `===` 이고, Java 의 `equals` 가 Kotlin 의 `==` 다. 그리고 Kotlin 의 `==` 는 **`null` 을 먼저 봐 준다** — 왼쪽이 `null` 이어도 터지지 않는다.

그런데 「내용이 같은가」의 **판정은 그 클래스의 `equals` 가 한다.** 그 `equals` 가 약속(규약)을 어기면 **`HashSet` 이 물건을 잃는다** — 컴파일러는 대부분 **아무 말도 안 한다.**

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 「내용이 같은가」 | `==` → `Intrinsics.areEqual` → `equals` | (1) |
| 「같은 물건인가」 | `===` → `if_acmpne` | (1)(2) |
| 빈손이어도 묻는다 | `null == x` 가 터지지 않는다 | (1) |
| 판정관 | 그 클래스의 `equals` | (4) |
| 판정관이 약속을 어김 | 반사·대칭·추이 위반 · `hashCode` 누락 · 넣은 뒤 변경 | (4) |
| 번호표 창구 | `HashSet` — **`hashCode` 로 칸을 먼저 고른다** | (4) |
| 줄 서서 하나씩 묻기 | `ArrayList.contains` — **`equals` 만** 쓴다 | (4) |
| 같은 번호표를 가진 사람은 공짜 통과 | ★ `HashMap` 이 **`===` 를 먼저** 본다(JDK 구현) | (4) |

```text
   a == b                            a === b
     |                                 |
     v                                 v
   Intrinsics.areEqual(a, b)         if_acmpne   (같은 참조인가)
     a == null ?  b == null
               :  a.equals(b)   <- 판정은 그 클래스의 equals
                        |
             규약을 지키나? ---- 안 지키면 ---> HashSet 이 잃는다 (4)
```

## 이 주제가 답하려는 질문

1. Kotlin 의 `==` 는 **무엇으로 번역되나** — `null`·원시 타입·`Double` 에서 각각.
2. `===` 의 답은 **누가 정하나** — 언어인가 JVM 인가.
3. `equals` 규약을 어기면 **`HashSet` 과 `ArrayList` 가 각각 무엇을 잃나** — 컴파일러는 막아 주나.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★ **`javap -c`** | `==` 가 `areEqual`·`if_icmpne`·`dcmpg`·`ifnonnull` 중 **무엇이 되나**((1)) · Java 와 나란히((2)) | 이 갈래의 기본 창 |
| ★★★ **규약 위반 × 자료구조 격자** | 깬 규약마다 `HashSet`·`ArrayList` 의 답 · **갈린 칸 N / M** 을 프로그램이 센다((4)) | ★ **본체 창** |
| ★★ **JVM 옵션 바꾸기** | `-XX:AutoBoxCacheMax` 로 **`===` 의 답이 바뀌나**((3)) — 층을 가르는 창 | ★ 이 주제의 고유 창 |
| ★★ **컴파일 진단 — 침묵 포함** | `equals` 만 재정의 · 배열 `==` · 호환 안 되는 `==`((6)(8)) | 이 갈래의 기본 창 |
| ★ **stdlib 소스** | `areEqual` 의 **한 줄**((1)) | ★ 이 주제의 고유 창 |
| **부적용 — 실행 시간** | ★★★ 「`data class` 의 `equals` 는 느리다」 같은 주장은 **이 문서의 범위 밖**이다. **호출 개수**(`areEqual` 하나 → `equals` 하나)만 세고 **시간은 안 쟀다** | — |
| **부적용 — `hashCode` 값** | ★ 값을 **찍지 않는다**. 흔들리는 칸이므로 「같나 다르나」로 바꿔 물었다 | — |

★★ **제5의 상태 — 「같은 질문을 다른 창으로 물었다」.** 「`127`/`128` 의 차이는 **언어의 약속인가**」를 문서로 읽지 않고 **JVM 옵션을 바꿔** 물었다((3)). 옵션 하나로 답이 바뀌면 **언어가 정한 것이 아니다.**
★ 바꾼 창의 한계 — `-XX:AutoBoxCacheMax` 는 **HotSpot 의 옵션**이다. 다른 JVM 에서 같은 옵션이 있는지는 **안 던졌다.**

### (1) ★★★ `==` 는 무엇으로 번역되나 — 여덟 모양

**언제 쓰나** — 「Kotlin `==` 는 `equals` 다」를 **어디까지 믿어도 되는지** 볼 때.

```kotlin
// eqforms.kt
data class Pt(val x: Int)

fun e1(a: String?, b: String?) = a == b
fun e2(a: Int, b: Int) = a == b
fun e3(a: Int?, b: Int?) = a == b
fun e4(a: Pt?, b: Pt?) = a === b
fun e5(a: Pt, b: Pt?) = a.equals(b)
fun e6(a: Pt?) = a == null
fun e7(a: Double, b: Double) = a == b
fun e8(a: Any?, b: Any?) = a == b

fun main() {
    println("A ${e1(null, null)} ${e1("k", null)} ${e1(String(charArrayOf('k')), "k")}")
    println("B ${e2(1, 1)} ${e3(1000, 1000)} ${e4(Pt(1), Pt(1))} ${e5(Pt(1), Pt(1))} ${e6(null)}")
}
```

```text
===== kotlinc eqforms.kt -d o32e =====
(exit 0)
===== java -cp o32e:kotlin-stdlib.jar EqformsKt =====
A true false true
B true true false true true
(exit 0)
```

```text
===== javap -c -p o32e/EqformsKt.class | awk '/ e[0-9]\(/,/^$/' =====
  public static final boolean e1(java.lang.String, java.lang.String);
    Code:
       0: aload_0
       1: aload_1
       2: invokestatic  #13                 // Method kotlin/jvm/internal/Intrinsics.areEqual:(Ljava/lang/Object;Ljava/lang/Object;)Z
       5: ireturn

  public static final boolean e2(int, int);
    Code:
       0: iload_0
       1: iload_1
       2: if_icmpne     9
       5: iconst_1
       6: goto          10
       9: iconst_0
      10: ireturn

  public static final boolean e3(java.lang.Integer, java.lang.Integer);
    Code:
       0: aload_0
       1: aload_1
       2: invokestatic  #13                 // Method kotlin/jvm/internal/Intrinsics.areEqual:(Ljava/lang/Object;Ljava/lang/Object;)Z
       5: ireturn

  public static final boolean e4(Pt, Pt);
    Code:
       0: aload_0
       1: aload_1
       2: if_acmpne     9
       5: iconst_1
       6: goto          10
       9: iconst_0
      10: ireturn

  public static final boolean e5(Pt, Pt);
    Code:
       0: aload_0
       1: ldc           #28                 // String a
       3: invokestatic  #32                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_0
       7: aload_1
       8: invokevirtual #38                 // Method Pt.equals:(Ljava/lang/Object;)Z
      11: ireturn

  public static final boolean e6(Pt);
    Code:
       0: aload_0
       1: ifnonnull     8
       4: iconst_1
       5: goto          9
       8: iconst_0
       9: ireturn

  public static final boolean e7(double, double);
    Code:
       0: dload_0
       1: dload_2
       2: dcmpg
       3: ifne          10
       6: iconst_1
       7: goto          11
      10: iconst_0
      11: ireturn

  public static final boolean e8(java.lang.Object, java.lang.Object);
    Code:
       0: aload_0
       1: aload_1
       2: invokestatic  #13                 // Method kotlin/jvm/internal/Intrinsics.areEqual:(Ljava/lang/Object;Ljava/lang/Object;)Z
       5: ireturn
(exit 0)
```

| 함수 | 식 | 번역 | 읽는 법 |
|---|---|---|---|
| `e1` | `String? == String?` | ★★ **`invokestatic Intrinsics.areEqual`** | `null` 처리를 **정적 메서드 하나**에 맡긴다 |
| `e2` | `Int == Int` | ★ **`if_icmpne`** | 원시 `int` 두 개 — `equals` 를 **안 부른다** |
| `e3` | `Int? == Int?` | `Intrinsics.areEqual` | 박싱된 `Integer` — 참조 타입 경로 |
| `e4` | `Pt? === Pt?` | ★★ **`if_acmpne`** | 참조 비교 명령 그대로 |
| `e5` | `a.equals(b)` | `invokevirtual Pt.equals` | 이름으로 부르면 **`null` 처리가 없다**(`a` 에 `checkNotNullParameter`) |
| `e6` | `Pt? == null` | ★ **`ifnonnull`** | `null` 과의 비교는 **`equals` 를 아예 안 부른다** |
| `e7` | `Double == Double` | ★★ **`dcmpg` + `ifne`** | IEEE 754 비교((7)) |
| `e8` | `Any? == Any?` | `Intrinsics.areEqual` | `e1` 과 같다 |

- ★★★ **`A true false true`** — `e1(null, null)` 이 `true`, `e1("k", null)` 이 `false` 이고 **예외가 없다.** 새로 만든 `"k"`(`String(charArrayOf('k'))`)와 리터럴 `"k"` 는 **`==` 로 같다.**
- ★★ **`B … false true …`** — `e4(Pt(1), Pt(1))`(`===`)은 `false`, `e5`(`equals`)는 `true`. 같은 값의 **다른 두 객체**다.

**`Intrinsics.areEqual` 은 무엇인가**

```text
===== unzip -p kotlin-stdlib-sources.jar jvmMain/kotlin/jvm/internal/Intrinsics.java | grep -n -A2 'boolean areEqual(Object first' =====
168:    public static boolean areEqual(Object first, Object second) {
169-        return first == null ? second == null : first.equals(second);
170-    }
(exit 0)
===== javap -c -p -cp kotlin-stdlib.jar kotlin.jvm.internal.Intrinsics | awk '/boolean areEqual\(java.lang.Object, java.lang.Object\)/,/^$/' =====
  public static boolean areEqual(java.lang.Object, java.lang.Object);
    Code:
       0: aload_0
       1: ifnonnull     16
       4: aload_1
       5: ifnonnull     12
       8: iconst_1
       9: goto          21
      12: iconst_0
      13: goto          21
      16: aload_0
      17: aload_1
      18: invokevirtual #46                 // Method java/lang/Object.equals:(Ljava/lang/Object;)Z
      21: ireturn
(exit 0)
```

- ★★★ **한 줄이다** — `first == null ? second == null : first.equals(second)`. 문서의 **`a?.equals(b) ?: (b === null)`** 이 **stdlib 의 Java 코드 한 줄**로 있다. **`null` 안전의 정체가 이것이다.**
- ★ 바이트코드에서도 `ifnonnull` 두 번과 `Object.equals` 하나다. 이 문서는 **호출 개수**만 센다 — 시간은 안 쟀다.

### (2) ★★★ Java 와 나란히 — 이름이 뒤집혔다

**언제 쓰나** — Java 코드를 Kotlin 으로 옮기면서 `==` 를 그대로 둘 때.

```java
// Eq32.java
import java.util.Objects;

public class Eq32 {
    static boolean j1(String a, String b) { return a == b; }
    static boolean j2(String a, String b) { return a.equals(b); }
    static boolean j3(String a, String b) { return Objects.equals(a, b); }

    public static void main(String[] args) {
        String a = new String("k");
        String b = "k";
        System.out.println("A " + j1(a, b) + " " + j2(a, b) + " " + j3(a, b));
        System.out.println("B " + j3(null, null));
        try { j2(null, b); } catch (NullPointerException e) { System.out.println("C NPE"); }
    }
}
```

```kotlin
// eqk32.kt
fun k1(a: String?, b: String?) = a == b
fun k2(a: String?, b: String?) = a === b

fun main() {
    val a = String(charArrayOf('k'))
    val b = "k"
    println("A ${k1(a, b)} ${k2(a, b)}")
    println("B ${k1(null, null)} ${k1(null, b)}")
}
```

```text
===== javac -d o32j Eq32.java =====
(exit 0)
===== java -cp o32j Eq32 =====
A false true true
B true
C NPE
(exit 0)
===== javap -c -p o32j/Eq32.class | awk '/static boolean j[0-9]/,/^$/' =====
  static boolean j1(java.lang.String, java.lang.String);
    Code:
       0: aload_0
       1: aload_1
       2: if_acmpne     9
       5: iconst_1
       6: goto          10
       9: iconst_0
      10: ireturn

  static boolean j2(java.lang.String, java.lang.String);
    Code:
       0: aload_0
       1: aload_1
       2: invokevirtual #7                  // Method java/lang/String.equals:(Ljava/lang/Object;)Z
       5: ireturn

  static boolean j3(java.lang.String, java.lang.String);
    Code:
       0: aload_0
       1: aload_1
       2: invokestatic  #13                 // Method java/util/Objects.equals:(Ljava/lang/Object;Ljava/lang/Object;)Z
       5: ireturn
(exit 0)
```

```text
===== kotlinc eqk32.kt -d o32k =====
(exit 0)
===== java -cp o32k:kotlin-stdlib.jar Eqk32Kt =====
A true false
B true false
(exit 0)
===== javap -c -p o32k/Eqk32Kt.class | awk '/ k[0-9]\(/,/^$/' =====
  public static final boolean k1(java.lang.String, java.lang.String);
    Code:
       0: aload_0
       1: aload_1
       2: invokestatic  #13                 // Method kotlin/jvm/internal/Intrinsics.areEqual:(Ljava/lang/Object;Ljava/lang/Object;)Z
       5: ireturn

  public static final boolean k2(java.lang.String, java.lang.String);
    Code:
       0: aload_0
       1: aload_1
       2: if_acmpne     9
       5: iconst_1
       6: goto          10
       9: iconst_0
      10: ireturn
(exit 0)
```

```text
   Java                                   Kotlin
   ---------------------------------      ---------------------------------
   a == b        if_acmpne         ====   a === b       if_acmpne
   a.equals(b)   invokevirtual            (null 이면 NPE — Java C 줄)
   Objects.equals(a, b)  invokestatic  ≈  a == b        Intrinsics.areEqual
```

- ★★★ **Java `j1`(`==`)과 Kotlin `k2`(`===`)는 명령이 한 글자도 같다** — `aload_0 · aload_1 · if_acmpne 9 · …`. Java 의 `==` 는 Kotlin 의 **`===`** 다.
- ★★ Java 는 `A false true true` — `new String("k") == "k"` 가 **`false`**. Kotlin 은 `A true false` — `==` 가 **`true`**. **같은 두 문자열**에 두 언어의 `==` 가 **반대 답**을 낸다.
- ★ Java `C NPE` — `a.equals(b)` 는 `a` 가 `null` 이면 터진다. Kotlin `==` 는 **`Objects.equals` 에 가깝다**(둘 다 `null` 을 먼저 본다) — 다른 것은 **정적 메서드가 어느 라이브러리 것이냐**뿐이다.

### (3) ★★ `===` 와 `Integer` 캐시 — **언어가 아니라 JVM 이 정한 답**

**언제 쓰나** — `Int?` 두 개를 `===` 로 비교해 「`127` 은 같은데 `128` 은 다르다」를 봤을 때.

```kotlin
// cache.kt
fun main() {
    val a: Int? = 127
    val b: Int? = 127
    val c: Int? = 128
    val d: Int? = 128
    println("A ${a === b} ${c === d}")
    println("B ${a == b} ${c == d}")
}
```

```text
===== kotlinc cache.kt -d o32c =====
cache.kt:6:18: warning: identity equality for arguments of types 'Int?' and 'Int?' is prohibited.
    println("A ${a === b} ${c === d}")
                 ^^^^^^^
cache.kt:6:29: warning: identity equality for arguments of types 'Int?' and 'Int?' is prohibited.
    println("A ${a === b} ${c === d}")
                            ^^^^^^^
(exit 0)
===== java -cp o32c:kotlin-stdlib.jar CacheKt =====
A true false
B true true
(exit 0)
===== java -XX:AutoBoxCacheMax=1000 -cp o32c:kotlin-stdlib.jar CacheKt =====
A true true
B true true
(exit 0)
```

- ★★ **컴파일러가 먼저 말한다** — 「`identity equality for arguments of types 'Int?' and 'Int?' is prohibited.`」 그런데 **`warning:`** 이고 **`exit 0`** 이다. [26번 주제](../26-value-class-and-boxing/)의 `value class` 에서 같은 문구가 **`error:`** 였던 것과 다르다 — `Int?` 는 **막지 않고 경고만** 한다.
- ★★ 기본 판 — **`A true false`**. `127` 은 같은 객체, `128` 은 다른 객체.
- ★★★ **`-XX:AutoBoxCacheMax=1000`** 을 준 판 — **`A true true`**. **소스도 클래스 파일도 그대로인데** JVM 옵션 하나로 `128` 의 답이 바뀌었다.
- ★★★ **층을 긋는다** — 언어가 정한 것은 「**`===` 는 동일성이다**」뿐이다. 「`-128..127` 은 같은 객체」는 **JVM(`Integer.valueOf` 의 캐시)의 구현**이고, 그 상한은 **옵션으로 움직인다.** 그러니 `Int?` 의 `===` 결과를 **근거로 코드를 짜면 안 된다** — 컴파일러가 경고한 이유다.
- ★ `B true true` — `==` 는 **두 옵션 모두 같다.** 값으로 비교하기 때문이다.

### (4) ★★★ 규약 위반 × 자료구조 격자 — 본체

**언제 쓰나** — 「`equals` 를 대충 써도 어디선가 터지겠지」라고 생각할 때. **안 터진다.**

`equals` 규약은 넷(+`null`)이고, 짝이 되는 `hashCode` 규약은 「**`equals` 가 같으면 해시도 같다**」다. 하나씩 깬 키를 만들었다.

| 키 | 깬 것 | 어떻게 |
|---|---|---|
| `R1` | **반사성** — `a == a` | `equals` 가 **늘 `false`** · 해시는 정직(`v`) |
| `R2` | **`hashCode` 규약** | `equals` 만 값으로 재정의 · `hashCode` 는 **`Object` 것 그대로** |
| `R3` | **넣은 뒤 변경**(일관성) | `data class R3(var v: Int)` — 넣고 나서 `v` 를 바꾼다 |
| `R4` | **추이성** | 「차이 1 이하면 같다」 — 1\~2, 2\~3 은 같은데 1\~3 은 다르다 · 해시는 **전부 `0`**(규약은 지킨다) |
| `R5` | **대칭성** | `R5("A").equals("a")` 는 `true`, `"a".equals(R5("A"))` 는 `false` |
| `R6` | (대조군) | 평범한 `data class` |

```kotlin
// vgrid.kt
class R1(val v: Int) {
    override fun equals(other: Any?) = false
    override fun hashCode() = v
}

class R2(val v: Int) {
    override fun equals(other: Any?) = other is R2 && other.v == v
}

data class R3(var v: Int)

class R4(val v: Int) {
    override fun equals(other: Any?) = other is R4 && kotlin.math.abs(other.v - v) <= 1
    override fun hashCode() = 0
}

class R5(val s: String) {
    override fun equals(other: Any?) = when (other) {
        is R5 -> other.s.equals(s, ignoreCase = true)
        is String -> other.equals(s, ignoreCase = true)
        else -> false
    }
    override fun hashCode() = s.lowercase().hashCode()
}

data class R6(val v: Int)

var split = 0
var cells = 0

fun row(name: String, make: () -> Any, mutate: (Any) -> Unit = {}) {
    val k = make()
    val set = HashSet<Any>()
    set.add(k)
    set.add(make())
    mutate(k)
    val list = arrayListOf<Any>(k)
    val sk = set.contains(k); val sn = set.contains(make())
    val lk = list.contains(k); val ln = list.contains(make())
    cells += 2
    if (sk != lk) split++
    if (sn != ln) split++
    println("%-3s | size=%d | set.contains(k)=%-5s | set.contains(new)=%-5s | list.contains(k)=%-5s | list.contains(new)=%-5s".format(name, set.size, sk, sn, lk, ln))
}

fun main() {
    row("R1", { R1(1) })
    row("R2", { R2(1) })
    row("R3", { R3(1) }, { (it as R3).v = 2 })
    row("R6", { R6(1) })
    println("set 과 list 가 갈린 칸 $split / $cells")
    val a = HashSet<Any>(); for (v in listOf(1, 3, 2)) a.add(R4(v))
    val b = HashSet<Any>(); for (v in listOf(2, 1, 3)) b.add(R4(v))
    println("R4 | order 1,3,2 -> size=${a.size} | order 2,1,3 -> size=${b.size}")
    val s1 = HashSet<Any>(listOf(R5("A")))
    val s2 = HashSet<Any>(listOf("a"))
    println("R5 | {R5(A)}.contains(\"a\")=${s1.contains("a")} | {\"a\"}.contains(R5(A))=${s2.contains(R5("A"))}")
    println("R5 | R5(A).equals(\"a\")=${R5("A").equals("a")} | \"a\".equals(R5(A))=${"a".equals(R5("A"))}")
}
```

```text
===== kotlinc vgrid.kt -d o32g =====
(exit 0)
===== java -cp o32g:kotlin-stdlib.jar VgridKt =====
R1  | size=2 | set.contains(k)=true  | set.contains(new)=false | list.contains(k)=false | list.contains(new)=false
R2  | size=2 | set.contains(k)=true  | set.contains(new)=false | list.contains(k)=true  | list.contains(new)=true 
R3  | size=1 | set.contains(k)=false | set.contains(new)=false | list.contains(k)=true  | list.contains(new)=false
R6  | size=1 | set.contains(k)=true  | set.contains(new)=true  | list.contains(k)=true  | list.contains(new)=true 
set 과 list 가 갈린 칸 3 / 8
R4 | order 1,3,2 -> size=2 | order 2,1,3 -> size=1
R5 | {R5(A)}.contains("a")=false | {"a"}.contains(R5(A))=true
R5 | R5(A).equals("a")=true | "a".equals(R5(A))=false
(exit 0)
```

**격자** — `k` 는 넣은 그 객체, `new` 는 **같은 값으로 새로 만든** 객체다.

| 키 | `size`(두 번 넣음) | `set.contains(k)` | `set.contains(new)` | `list.contains(k)` | `list.contains(new)` | 무엇을 잃었나 |
|---|---|---|---|---|---|---|
| `R1` 반사성 | **2** | ★★ **`true`** | `false` | ★★ **`false`** | `false` | 같은 값이 **둘** · 새 객체로는 **영영 못 찾는다** |
| `R2` 해시 누락 | **2** | `true` | ★★★ **`false`** | `true` | ★★★ **`true`** | 리스트는 찾고 **셋은 못 찾는다** |
| `R3` 넣은 뒤 변경 | 1 | ★★★ **`false`** | `false` | ★★ **`true`** | `false` | ★ **넣은 그 객체도 못 찾는다** — 셋 안에 있는데 |
| `R6` 대조군 | 1 | `true` | `true` | `true` | `true` | — |

- ★★★ 마지막 줄 **「`set 과 list 가 갈린 칸 3 / 8`」** — 네 키 × 두 질문 중 **셋**에서 `HashSet` 과 `ArrayList` 가 **다른 답**을 냈다. 대조군(`R6`)은 **0** 이다.
- ★★★ **`R2`** — 규약을 깬 것은 **`hashCode` 하나**인데, `HashSet` 은 **해시로 칸을 먼저 고르고** 거기서만 `equals` 를 부른다. 새 객체는 **다른 칸**을 보므로 `equals` 가 **불리지도 않는다.** `ArrayList` 는 해시를 안 쓰니 **멀쩡하다.** 두 컬렉션이 갈리는 것이 이 사고의 서명이다.
- ★★★ **`R3`** — `v` 를 바꾸자 `hashCode` 가 바뀌어 **넣을 때와 다른 칸**을 본다. **셋 안에 들어 있는데** `contains(k)` 가 `false` 다. `ArrayList` 는 찾는다.
- ★★ **`R1` — 넣은 그 객체(`k`)는 셋이 찾고(`true`) 리스트가 못 찾는다(`false`).** 셋의 `true` 는 **`equals` 덕이 아니다** — JDK `HashMap` 이 **해시가 같으면 `==`(동일성)를 먼저** 보고 맞으면 `equals` 를 **건너뛴다.** `ArrayList.contains` 는 `o.equals(e)` 만 부르므로 `false` 다. ★ 이것은 **JDK 의 구현**이지 Kotlin·Java 언어의 약속이 아니다 — 원리는 [`cs/data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/)의 몫이다.

**추이성·대칭성 — 크기와 방향이 흔들린다**

- ★★★ **`R4`** — 같은 세 값 `1`·`2`·`3` 을 **넣는 순서만 바꿨는데** `size=2` 와 `size=1` 로 갈렸다. `1,3,2` 순이면 `1`·`3` 이 서로 달라 둘 다 들어가고 `2` 는 `1` 과 「같다」며 튕긴다. `2,1,3` 순이면 `2` 가 먼저 앉아 `1`·`3` 을 **둘 다** 튕긴다. **추이성이 없으면 「몇 개인가」가 넣는 순서의 함수**가 된다.
- ★★ **`R5`** — `{R5(A)}.contains("a")` 는 `false`, `{"a"}.contains(R5(A))` 는 `true`. `HashSet.contains(x)` 는 **`x.equals(원소)`** 를 부르므로 **누가 인자로 오느냐**에 따라 답이 뒤집힌다. 두 방향의 `equals` 를 직접 찍은 마지막 줄이 그 원인이다(`true` / `false`).
- ★ 다섯 사고 **모두 예외가 없다** — `(exit 0)`. 증상은 **조용한 오답**뿐이다.

### (5) ★★ `data class` 와의 관계 — 본문 프로퍼티는 **`HashSet` 에서 지워진다**

**언제 쓰나** — `data class` 본문에 부수 상태(`note`)를 얹고 그 객체를 **셋·맵의 키**로 쓸 때.

[22번 주제](../22-data-class-generated-members/) (2)가 「본문의 `var` 는 `equals` 에서 빠진다」를 **`a == b` 가 `true`** 로 보였다. 여기서는 그 결과가 **자료구조에서 무엇이 되는지**를 본다.

```kotlin
// body.kt
data class Tag(val id: Int) {
    var note: String = ""
}

fun main() {
    val a = Tag(1).apply { note = "first" }
    val b = Tag(1).apply { note = "second" }
    val set = hashSetOf(a, b)
    println("A ${set.size} ${set.first().note}")
    val map = hashMapOf(a to "va")
    map[b] = "vb"
    println("B ${map.size} ${map.keys.first().note} ${map[a]}")
}
```

```text
===== kotlinc body.kt -d o32b =====
(exit 0)
===== java -cp o32b:kotlin-stdlib.jar BodyKt =====
A 1 first
B 1 first vb
(exit 0)
```

- ★★★ **「같은데 다르다」** — `note` 가 `first`/`second` 로 **다른 두 객체**를 넣었는데 `size` 가 **1** 이고 남은 것은 `first` 다. **`second` 의 `note` 는 셋에서 사라졌다.** 두 객체는 `equals` 가 보는 칸(`id`)에서 **같기** 때문이다.
- ★★ 맵은 더 얄궂다 — `map[b] = "vb"` 가 **값은 `vb` 로 덮고 키는 `a`(`note=first`) 그대로** 둔다. `HashMap.put` 은 같은 키를 찾으면 **값만 바꾸고 키 객체는 안 바꾼다**(JDK 구현).
- ★ 이 사고는 **규약 위반이 아니다** — `data class` 의 `equals`/`hashCode` 는 **서로 일관**하다. 틀린 것은 「`note` 도 신원의 일부」라는 **사람의 기대**다. 그래서 컴파일러도, 격자((4))도 못 잡는다.

### (6) ★★ `equals` 만 재정의하고 `hashCode` 를 안 하면 — **컴파일러가 경고하나**

**언제 쓰나** — (4)의 `R2` 를 **컴파일 단계에서** 잡을 수 있는지 물을 때. 파이썬은 `__eq__` 만 정의하면 **`__hash__` 가 `None` 이 된다**([Python 30번](../../../python/syntax/30-repr-eq-hash-contracts/) 동작 2).

```kotlin
// eqonly.kt
class OnlyEq(val v: Int) {
    override fun equals(other: Any?) = other is OnlyEq && other.v == v
}

data class WithArr(val xs: IntArray)

fun main() {
    val a = arrayOf(1, 2)
    val b = arrayOf(1, 2)
    println("A ${a == b} ${a.contentEquals(b)} ${a.equals(b)}")
    println("B ${WithArr(intArrayOf(1)) == WithArr(intArrayOf(1))}")
    println("C ${listOf(1, 2) == listOf(1, 2)} ${OnlyEq(1) == OnlyEq(1)}")
}
```

```text
===== kotlinc eqonly.kt -d o32w =====
eqonly.kt:10:20: warning: '==' on arrays compares only references. Replace '==' with 'contentEquals' to compare the arrays' contents or use '===' to remove the warning.
    println("A ${a == b} ${a.contentEquals(b)} ${a.equals(b)}")
                   ^^
(exit 0)
===== kotlinc -Wextra eqonly.kt -d o32w2 =====
eqonly.kt:10:20: warning: '==' on arrays compares only references. Replace '==' with 'contentEquals' to compare the arrays' contents or use '===' to remove the warning.
    println("A ${a == b} ${a.contentEquals(b)} ${a.equals(b)}")
                   ^^
(exit 0)
===== echo "물은 자리 3 · warning 줄 $(kotlinc -Wextra eqonly.kt -d o32w3 2>&1 | grep -c ': warning:')" =====
물은 자리 3 · warning 줄 1
(exit 0)
===== java -cp o32w:kotlin-stdlib.jar EqonlyKt =====
A false true false
B false
C true true
(exit 0)
```

- ★★★ **물은 자리 3 · 경고 1줄** — `OnlyEq`(equals 만 재정의)와 `WithArr`(배열 컴포넌트를 가진 `data class`)에는 **경고가 없다.** `-Wextra`(K2 의 추가 검사기)를 켜도 **같다.** 침묵이 이 절의 결론이다.
- ★★ 경고가 난 한 곳은 **배열의 `==`** 다 — 「`'==' on arrays compares only references. Replace '==' with 'contentEquals'`」. `A false true false` — `==`·`equals` 는 **참조 비교**, `contentEquals` 만 `true`.
- ★★ `B false` — **배열을 가진 `data class`** 는 같은 내용이어도 다르다. `data class` 의 `equals` 가 컴포넌트의 `equals`(배열은 참조 비교)에 **위임**하기 때문이다([22번 주제](../22-data-class-generated-members/) (7)). **여기에는 경고가 없다** — 경고는 `==` 라는 **식의 자리**에만 붙었다.
- ★ `C true true` — `List` 는 **내용 비교**다. `OnlyEq(1) == OnlyEq(1)` 도 `true` — `equals` 는 멀쩡하고 **셋에 넣을 때만** 깨진다((4)의 `R2`).

### (7) ★★ `Double.NaN == Double.NaN` — **정적 타입이 답을 가른다**

**언제 쓰나** — 같은 `NaN` 이 한 자리에서는 같고 다른 자리에서는 다를 때.

```kotlin
// nan.kt
data class Box(val d: Double)

fun main() {
    val x = Double.NaN
    val y: Any = Double.NaN
    val z: Double? = Double.NaN
    println("A ${x == x} ${y == y} ${z == z}")
    val p = 0.0
    val q = -0.0
    val pa: Any = 0.0
    val qa: Any = -0.0
    println("B ${p == q} ${pa == qa}")
    println("C ${listOf(Double.NaN).contains(Double.NaN)} ${x.equals(x)}")
    println("D ${x < 1.0} ${x > 1.0} ${x.compareTo(1.0)}")
    println("E ${Box(Double.NaN) == Box(Double.NaN)} ${Box(0.0) == Box(-0.0)}")
}
```

```text
===== kotlinc nan.kt -d o32n =====
(exit 0)
===== java -cp o32n:kotlin-stdlib.jar NanKt =====
A false true false
B true false
C true true
D false false 1
E true false
(exit 0)
===== javap -c -p o32n/Box.class | grep -E 'Double\.compare' =====
      29: invokestatic  #60                 // Method java/lang/Double.compare:(DD)I
(exit 0)
```

| 식 | 정적 타입 | 답 | 규칙 |
|---|---|---|---|
| `x == x` | `Double` | ★★ **`false`** | IEEE 754 — `NaN` 은 자신과도 다르다 |
| `y == y` | `Any` | ★★ **`true`** | `equals` — `NaN` 은 자신과 같다 |
| `z == z` | `Double?` | **`false`** | ★ **nullable 도 부동소수점 타입**이라 IEEE 쪽 |
| `p == q`(`0.0`·`-0.0`) | `Double` | `true` | IEEE — 부호 무시 |
| `pa == qa` | `Any` | ★ **`false`** | `equals` — `-0.0` 과 `0.0` 은 다르다 |
| `listOf(NaN).contains(NaN)` | (컬렉션 안) | **`true`** | 컬렉션은 **`equals`** 를 쓴다 |
| `x.equals(x)` | 이름 호출 | `true` | `equals` |
| `x.compareTo(1.0)` | — | `1` | ★ `compareTo` 에서 `NaN` 은 **가장 크다** |

- ★★★ **같은 값에 같은 기호인데 답이 갈린다** — 문서의 규칙 그대로다: 「정적 타입이 `Float`/`Double`(nullable 포함)이면 IEEE 754, 아니면 `equals`(NaN 은 자신과 같고, `-0.0` 은 `0.0` 과 다르다)」. (1)의 `e7` 이 `dcmpg` 였던 것이 앞쪽이다.
- ★★ **`E true false`** — `Double` 필드를 가진 `data class` 는 **`equals` 쪽 규칙**을 따른다. `Box(NaN) == Box(NaN)` 이 **`true`**, `Box(0.0) == Box(-0.0)` 이 **`false`** — 필드는 `Double` 인데 `data class` 가 만든 `equals` 가 **`Double.compare`** 를 부른다(블록의 마지막 명령). 겉의 `==` 는 `Box` 끼리라 IEEE 규칙이 안 걸린다.
- ★ `D false false 1` — `NaN < 1.0` 도 `NaN > 1.0` 도 거짓(IEEE)인데 `compareTo` 는 `1`. **비교 기호와 `compareTo` 도 갈린다.**

### (8) ★ 호환되지 않는 `==` — 막히는 것과 안 막히는 것

```kotlin
// eqbad.kt
class Cat
class Dog

fun main() {
    println("a" == 1)
    println(Cat() == Dog())
    val x: Any = 1
    println(x == "a")
    println(1 == 1L)
}
```

```text
===== kotlinc eqbad.kt -d o32x =====
eqbad.kt:5:13: error: operator '==' cannot be applied to 'String' and 'Int'.
    println("a" == 1)
            ^^^^^^^^
eqbad.kt:9:13: error: operator '==' cannot be applied to 'Int' and 'Long'.
    println(1 == 1L)
            ^^^^^^^
(exit 1)
```

- ★★ **물은 곳 넷 · 막힌 곳 둘** — `"a" == 1`(5번째 줄)과 **`1 == 1L`**(9번째 줄)은 「`operator '==' cannot be applied to …`」.
- ★★ **`Cat() == Dog()`(6번째 줄)은 통과한다** — 서로 무관한 두 `final` 클래스인데도 **에러도 경고도 없다.** 막는 것은 **내장 타입끼리의 명백한 불일치**뿐이다.
- ★ `x == "a"`(`Any` 와 `String`)은 당연히 통과한다 — `x` 가 `String` 일 수 있다.
- ★ `1 == 1L` 이 막히는 것은 [01번 주제](../01-val-var-and-basic-types/)의 「암묵 수치 변환이 없다」와 같은 뿌리다 — Java 는 이항 수치 승격으로 비교를 받아 준다(Java 갈래의 **02번**, 여기서는 `javac` 로 안 던졌다).

### (9) ★★ Python 30 · Rust 28 · Java 27 과 — 같은 실험, 다른 방어선

★ 아래 표의 Python·Rust·Java 칸은 **그 갈래 문서를 직접 읽고** 옮긴 것이다(여기서 던지지 않았다). Kotlin 칸만 이 문서의 실측이다.

| 축 | Kotlin(이 문서) | Java(27번) | Python(30번) | Rust(28번) |
|---|---|---|---|---|
| 「내용이 같은가」 기호 | `==` → `equals` + **`null` 먼저** | `equals` — `null` 이면 NPE | `==` → `__eq__` | `==` → `PartialEq::eq` |
| 「같은 물건인가」 | `===` | `==` | `is` | (참조 주소 비교 — 기호 없음) |
| ★ `equals` 만 고치면 | ★★ **경고 0줄 · 셋에서 `size=2`**((4)(6)) | 같다 — `HashSet size 2` | ★ **`__hash__` 가 `None`** — 셋에 넣으면 `TypeError` | 키가 `Eq + Hash` 를 **타입으로 요구** — 컴파일에서 걸린다 |
| 반사성을 깬 키, **넣은 그 객체**로 찾기 | ★ **찾는다** — `HashMap` 의 동일성 지름길(JDK) | (그 실험 없음) | ★ **찾는다** — CPython 의 정체 지름길 | 딴 객체로 물어 `None` |
| 반사성을 깬 키, 리스트로 찾기 | ★★ **못 찾는다** — `ArrayList` 는 지름길이 **없다** | — | ★ **찾는다** — `list` 의 `in` 도 지름길 | `Vec` 는 해시를 안 쓴다 |
| 부동소수점 `NaN` | ★★ **정적 타입에 따라 갈린다**((7)) | (이 표에서는 안 옮긴다) | `float` 를 키로 쓰는 사고를 따로 다룬다(30번 (13)) | `f64` 는 **`Eq` 가 아니다** — 키가 못 된다 |
| 컴파일러가 막아 주나 | 배열 `==` 경고 · 호환 안 되는 내장 타입 | ✘ | ✘(런타임 스위치) | ✔(짝의 **존재**만) |

- ★★★ **Kotlin 은 Java 와 방어선이 같다** — JVM 의 `Object.hashCode` 가 **그냥 남으므로** `equals` 만 고친 키는 **아무 신호 없이** 셋에서 둘이 된다. 파이썬은 **런타임에**, Rust 는 **컴파일에** 짝을 요구한다.
- ★★ **리스트 칸에서 파이썬과 갈렸다** — 반사성을 깬 키를 **넣은 그 객체로** 리스트에서 찾으면 파이썬은 **찾고**(정체 지름길), Kotlin(`ArrayList`)은 **못 찾는다.** 셋에서는 **둘 다 찾는다.** 「지름길이 있는가」는 **컬렉션 구현마다** 다르다 — 언어 보장이 아니다.
- ★ 공통 결론 — **넷 다 규약의 내용은 사람 몫**이다. 컴파일러가 보는 것은 기껏해야 **짝이 있느냐**다.

## 문법 — 형태와 규칙

**형태** — `==`·`===`·`null` 비교·셋·배열이 한 줄에서 도는 최소 예제다.

```kotlin
// form32.kt
data class Key(val id: Int, val tag: String)

fun main() {
    val a = Key(1, "x")
    val b = Key(1, "x")
    val n: Key? = null
    println("Z ${a == b} ${a === b} ${n == null} ${a == n} ${hashSetOf(a, b).size} ${intArrayOf(1) contentEquals intArrayOf(1)}")
}
```

```text
===== kotlinc form32.kt -d o32z =====
(exit 0)
===== java -cp o32z:kotlin-stdlib.jar Form32Kt =====
Z true false true false 1 true
(exit 0)
```

**규칙 불릿**

- `a == b` 는 **`a?.equals(b) ?: (b === null)`** 이다 — JVM 에서 **`Intrinsics.areEqual`** 한 번((1)).
- `a === b` 는 **동일성** — Java 의 `==` 와 **같은 명령**(`if_acmpne`)((2)).
- 원시 `Int`·`Double` 의 `==` 는 **`equals` 를 안 부른다** — `if_icmpne`·`dcmpg`((1)).
- `==` 를 바꾸려면 **`override fun equals(other: Any?)`** — 오버로드가 아니다([31번 주제](../31-operator-overloading-infix-and-invoke/) (5)).
- `equals` 를 고치면 **`hashCode` 도 같이** — 컴파일러는 **알려 주지 않는다**((6)).
- `data class` 는 **주 생성자 프로퍼티만으로** 둘을 만든다 — 본문 프로퍼티는 **신원이 아니다**((5)).
- 배열은 **`contentEquals`**((6)). 부동소수점은 **정적 타입**이 규칙을 고른다((7)).
- `Int?`·`value class` 에 `===` 를 쓰지 마라 — 앞쪽은 경고, 뒤쪽은 에러다((3)).

## 어디서 틀리나

1. ★★★ **Java 습관대로 `==` 를 참조 비교로 읽는다.** Kotlin `==` 는 **내용**이다 — 참조는 `===`((2)).
2. ★★★ **`equals` 만 재정의한다.** 경고 0줄, 셋에서 **같은 값이 둘**, 새 객체로 **못 찾는다**((4)(6)).
3. ★★★ **셋에 넣은 뒤 키를 고친다.** 셋 안에 있는데 **`contains` 가 `false`**((4)의 `R3`).
4. ★★ **「`127 === 127` 이 `true` 니 `Int?` 의 `===` 는 믿을 만하다」.** JVM 옵션 하나로 `128` 의 답이 바뀐다((3)).
5. ★★ **`data class` 본문 프로퍼티를 신원으로 믿는다.** 셋·맵에서 **조용히 지워진다**((5)).
6. ★★ **배열을 `==` 로 비교한다 · `data class` 에 배열을 넣는다.** 앞쪽만 경고가 난다((6)).
7. ★★ **`NaN` 비교를 한 규칙으로 외운다.** 정적 타입이 `Double` 이냐 `Any` 냐로 갈린다((7)).
8. ★ **추이성을 깬 「근사 같음」을 `equals` 로 쓴다.** 셋의 크기가 **넣는 순서**에 달린다((4)의 `R4`).
9. ★ **대칭성을 깬 `equals` 로 다른 타입과 같다고 답한다.** `contains` 의 답이 **인자 방향**에 달린다((4)의 `R5`).
10. ★ **「무관한 두 클래스를 `==` 하면 컴파일러가 막겠지」.** `Cat() == Dog()` 은 **통과**한다((8)).

## 구현 세부사항 대 언어 보장

| 항목 | 어느 쪽인가 | 근거 |
|---|---|---|
| `a == b` = `a?.equals(b) ?: (b === null)` | ★★★ **언어 보장** | (1) |
| `===` 가 **동일성** | **언어 보장** | (1)(2) |
| 부동소수점 `==` 가 **정적 타입으로 IEEE/`equals` 를 고르는** 것 | **언어 보장**(문서가 명시) | (7) |
| `equals` 규약(반사·대칭·추이·일관·`null`) | **언어 보장** — 단 **검사는 안 한다** | (4) |
| `==` → **`Intrinsics.areEqual`** · `Int` → `if_icmpne` · `Double` → `dcmpg` | **JVM 백엔드의 구현** | (1) |
| ★★ `Int?` 의 `===` 가 **`-128..127` 에서 `true`** | ★★★ **JVM(`Integer` 캐시)의 구현** — 옵션으로 움직인다 | (3) |
| `HashMap` 이 **해시 → `==` → `equals`** 순으로 보는 것 | **JDK 구현** | (4) |
| `ArrayList.contains` 에 동일성 지름길이 **없는** 것 | **JDK 구현** | (4) |
| `equals` 만 재정의해도 **경고가 없는** 것 · 배열 `==` 경고 · `Int?` `===` 가 경고 | **이 판(2.4.20)의 관찰** | (3)(6) |
| 진단 **문구 그 자체** | **이 판의 산출물** | 전부 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 값이 같은가 | `==` | `null` 도 안전하다((1)) |
| 같은 객체인가(캐시·싱글턴·식별) | `===` | 동일성((2)) — **박싱된 수에는 쓰지 마라**((3)) |
| 값 클래스를 **직접** 쓴다 | `data class`(자동) | 두 메서드가 **서로 일관**하게 만들어진다 |
| `equals` 를 손으로 쓴다 | ★ **`hashCode` 도 같이**, 같은 필드로 | (4)(6) — 컴파일러는 안 알려 준다 |
| 셋·맵의 키 | ★ **불변** 값 | (4)의 `R3` |
| 부수 상태를 가진 `data class` 를 키로 | ★ **그 상태를 빼거나 키를 따로 둔다** | (5) |
| 배열 비교 | `contentEquals` · 컴포넌트면 `List` | (6) |
| 부동소수점 근사 비교 | ★ **`equals` 가 아니라** 별도 함수(`abs(a - b) < eps`) | (4)의 `R4` — 근사는 추이적이지 않다 |

## 핵심 문장

1. Kotlin 의 `==` 는 **`equals` + `null` 처리**이고, JVM 에서 **`Intrinsics.areEqual` 한 줄**(`first == null ? second == null : first.equals(second)`)이다.
2. **Java 의 `==` 는 Kotlin 의 `===`** 다 — 명령이 한 글자도 같다.
3. `Int?` 의 `===` 가 `127` 에서 같고 `128` 에서 다른 것은 **JVM 의 `Integer` 캐시**다 — 옵션 하나로 바뀌므로 **언어의 약속이 아니다.**
4. 규약을 어긴 `equals` 는 **예외 없이** 셋에서 값을 잃는다 — `hashCode` 누락·넣은 뒤 변경은 **`HashSet` 과 `ArrayList` 가 다른 답**을 내는 것이 서명이다.
5. `equals` 만 재정의해도 kotlinc 2.4.20 은 **경고 0줄**이다(`-Wextra` 도). 방어선은 **Java 와 같은 자리**에 있다.
6. 부동소수점 `==` 는 **정적 타입**이 IEEE 와 `equals` 중 하나를 고른다 — 같은 `NaN` 이 `Double` 로는 다르고 `Any` 로는 같다.

## 관련 자료

- [`cs/data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/) — ★★★ **해시 원리의 정본.** 이 문서는 「왜 칸을 먼저 고르나」를 거기에 맡기고, **Kotlin 의 `==` 와 규약 위반의 증상**까지만 썼다.
- [22번 주제](../22-data-class-generated-members/) — ★★ **선행.** `data class` 가 `equals` 를 만드는 범위(주 생성자만)와 위임 규칙.
- [26번 주제](../26-value-class-and-boxing/) — `value class` 의 **`===` 금지**(에러). (3)의 `Int?` 경고와 대비된다.
- [31번 주제](../31-operator-overloading-infix-and-invoke/) — `==` 가 연산자 번역표에 **없는** 이유.
- [01번 주제](../01-val-var-and-basic-types/) — 암묵 수치 변환 없음. `1 == 1L` 이 막히는 뿌리.
- [`../../../java/syntax/27-equals-hashcode-contract/`](../../../java/syntax/27-equals-hashcode-contract/) — Java 의 계약 다섯 조항과 위반 증상.
- [`../../../python/syntax/30-repr-eq-hash-contracts/`](../../../python/syntax/30-repr-eq-hash-contracts/) — `__eq__` 만 정의하면 `__hash__` 가 꺼지는 쪽.
- [`../../../rust/syntax/28-partialeq-eq-partialord-ord-and-hash-contracts/`](../../../rust/syntax/28-partialeq-eq-partialord-ord-and-hash-contracts/) — 키가 `Eq + Hash` 를 **타입으로** 요구하는 쪽.

## 용어 풀이

> **구조적 동등성(structural equality)** — `==`. 내용이 같은가. `equals` 로 판정한다.

> **참조 동등성(referential equality)** — `===`. 같은 객체인가. JVM 의 `if_acmpne`.

> **`Intrinsics.areEqual`** — Kotlin `==` 가 참조 타입에서 번역되는 stdlib 의 정적 메서드. `null` 을 먼저 본다.

> **`equals` 규약** — 반사성(`a == a`) · 대칭성(`a == b` ⇔ `b == a`) · 추이성 · 일관성 · `a == null` 은 거짓. **컴파일러는 검사하지 않는다.**

> **`Integer` 캐시** — `Integer.valueOf` 가 `-128..127` 의 상자를 **미리 만들어 재사용**하는 것. HotSpot 은 `-XX:AutoBoxCacheMax` 로 상한을 올린다.

> **IEEE 754** — 부동소수점 표준. `NaN` 은 자신과도 다르고 `-0.0 == 0.0` 이다.

> **동일성 지름길** — 컬렉션이 `equals` 전에 **`==`(같은 객체인가)** 를 먼저 보는 것. JDK `HashMap` 에는 있고 `ArrayList.contains` 에는 없다(이 판의 관찰).

## 더 들어가면

- **왜 `==` 에 `null` 처리를 붙였나** — Java 에서 `a.equals(b)` 의 가장 흔한 사고가 **`a` 가 `null`** 인 것이었다((2)의 `C NPE`). `Objects.equals` 가 나중에 들어와 그 사고를 덜었는데, Kotlin 은 **기호의 기본 뜻**으로 삼았다. 대가는 없다시피 하다 — 정적 메서드 하나에 `null` 검사 두 번이다(시간은 안 쟀다).
- **왜 `Int?` 의 `===` 는 경고이고 `value class` 는 에러인가** — `Int?` 는 JVM 에서 **진짜 `Integer` 객체**라 동일성이 **정의는 된다**(답이 구현에 달릴 뿐). `value class` 는 [26번 주제](../26-value-class-and-boxing/)에서 봤듯 **자리마다 상자가 생겼다 사라지므로** 동일성이라는 질문 자체가 **성립하지 않는다.** 「답이 불안정하다」(경고)와 「질문이 없다」(에러)의 차이다.
