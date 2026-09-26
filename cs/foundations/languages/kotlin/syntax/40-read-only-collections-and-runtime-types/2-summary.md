# kotlin/syntax/40 — 컬렉션 — 읽기 전용 인터페이스와 실제 런타임 타입 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Collections overview](https://kotlinlang.org/docs/collections-overview.html)(읽기 전용 인터페이스와 가변 인터페이스의 분리 · 「Write operations with a mutable collection are still possible even if it is assigned to a `val`」) · [Collections in Java and Kotlin](https://kotlinlang.org/docs/java-to-kotlin-collections-guide.html) — 둘 다 [`../../언어-특성/README.md`](../../언어-특성/README.md) §5 가 인용한 문장을 거기서 **다시 옮기지 않고** 가리킨다.
> **실행 검증** — 이 문서의 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javac`·`java`·`javap` 에서 실제로 얻었다. 대비 셋은 **.NET 10.0.401 의 csc** · **rustc 1.92.0** · **Python 3.12.3** 이다.\
> `kotlinc` 4회(컴파일 실패 1벌) · `javac` 1회 · `java` 3회 · `javap` 3회 · stdlib 소스 jar 1곳 · `csc`·`dotnet` 1회씩 · `rustc` 1회(실패가 결과) · `python3` 1회.\
> ★★ 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적지 않았다.
> **버전** — 읽기 전용/가변 인터페이스 분리는 **1.0**. 이 판에서 버전에 갈리는 칸은 없다.
> **경계** — ★★★ **런타임 클래스 실측표는 [`../../언어-특성/README.md`](../../언어-특성/README.md) §5 에 있다 — 여기서 다시 재지 않는다.** 그 표가 이미 말한 것: `listOf()` → `EmptyList` · `listOf("a")` → `Collections$SingletonList` · `listOf("a","b")` → `Arrays$ArrayList`(Java 에서 `add` 예외 · **`set` 성공**) · `mutableListOf(…)` 를 `List` 로 노출 → `java.util.ArrayList`(Java 에서 `add`·`set` **성공**) · Java `List.of` → `ImmutableCollections$List12`(둘 다 예외).\
> 여기는 그 표 위에서 **「구멍을 코드로 재현하고, 연산 API 를 고르는 법」** 이다 — `언어-특성/README.md` 의 목록 표가 이 주제에 준 지시 그대로다.\
> `List<out E>` 와 `MutableList<E>` 의 **stdlib 선언**은 [28번 주제](../28-generics-variance-in-out-star-where/) (3)이 소스 jar 에서 뽑았다. `as` 캐스트의 일반 규칙은 [33번 주제](../33-type-checks-and-casts-is-as/), `val` 이 참조만 잠그는 것은 [01번 주제](../01-val-var-and-basic-types/)가 정본이다. 자료구조 내부는 [`cs/data-structure/`](../../../../../data-structure/) 다.
> ★ **짝 — Java 갈래 [40번](../../../java/syntax/40-list-set-and-immutable-factories/)**(`List.of`·`unmodifiableList`·`Arrays.asList`) — 「읽기 전용 **뷰**」(Kotlin)와 「진짜 불변 **객체**」(Java `List.of`)의 차이.
> 이 본문은 Claude 작성이다(원고 없음).

★★★ **본체는 첫째 창이다** — 「**뷰 구멍 재현 — `List` 로 받은 것을 고쳐서 원본이 바뀌나**」. 읽기 전용은 **타입의 성질**이라 컴파일러가 `add` 를 막아 주지만, 그 **밑의 객체**는 여전히 가변이다. 그 사실은 **실행으로만** 보인다 — 컴파일 에러 창(둘째)은 「막아 준 쪽」만 보여 준다.

## 이 주제가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **언어 보장(타입 규칙)** | 명세·공식 문서가 약속한 것 | ★★★ `List<E>` 에는 **고치는 멤버가 없다** — 그래서 `add`·`set`·`sort` 가 **컴파일 에러** · `List<out E>` 라 `List<Int>` 가 `List<Any>` 자리에 들어간다 · ★★★ 그러나 **`List` 타입은 「이 객체는 안 바뀐다」를 약속하지 않는다**(뷰) |
| **구현(stdlib · JVM 백엔드)** | kotlinc·stdlib 가 실제로 만드는 것 | ★★ `listOf(…)` 가 돌려주는 **실제 클래스**(§5 표) · `is MutableList`·`as MutableList` 가 **`TypeIntrinsics`** 를 부르고 **`KMappedMarker`** 로 가르는 것 · `asReversed` 가 **뷰**인 것 |
| **이 판의 관찰** | kotlinc 2.4.20 · stdlib 2.4.20 에서 본 것 | ★ `listOf(1, 2) is MutableList` 가 **`true`** · 진단 문구 |

★★★ **「읽기 전용 = 뷰」는 언어(타입) 규칙이고, 실제 런타임 클래스는 stdlib 구현이다.** 둘을 섞으면 「`listOf` 는 불변이다」라는 틀린 문장이 나온다 — 타입이 말하는 것은 「**이 참조로는** 못 고친다」뿐이고, 객체가 실제로 막는지는 **그 판의 stdlib 가 어떤 클래스를 돌려주느냐**에 달렸다.

## 이 판

```text
===== kotlinc -version =====
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | (이 주제에는 없다) | 해시코드·주소를 찍지 않았다 — 같은 객체인지는 **`===`** 로만 물었다 |
| 안 흔들린다 | 실행 출력 · 예외 클래스 이름 | 단일 스레드 · 결정적 |
| 안 흔들린다 | `javap` 출력 · 진단 문구·`파일:줄:칸` · 종료 코드 | 결정적이다 |

★ 근거 — 캡처 스크립트를 처음부터 두 번 돌려 **블록 전체를 바이트 단위로 대조**했다(수치는 3-answer 의 「실행 검증」).

## 한눈에 — 쉽게 말하면

**`List` 는 「창문」이고 `MutableList` 는 「문」이다 — 그런데 둘 다 같은 방을 본다.** `val ro: List<Int> = src` 는 **방을 복사한 것이 아니라** 방에 창문을 하나 더 낸 것이다. 창문으로는 물건을 못 넣지만, **문을 가진 사람이 넣으면 창문으로 그대로 보인다.**
★ 게다가 창문은 **유리가 아니라 커튼**이다 — `ro as MutableList<Int>` 한 줄이면 창문이 **문으로 바뀐다**. 방이 진짜로 잠긴 것(`java.util.List.of`)은 **방 쪽이 거부**하는 것이고, Kotlin `List` 는 **창문 쪽이 사양**하는 것이다.

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 같은 방 | 같은 객체 — `ro === src` 가 `true` | (1) |
| 창문 — 물건을 못 넣는다 | `List<E>` — `add`·`set`·`sort` 가 **컴파일 에러** | (2) |
| 문 가진 사람이 넣으면 보인다 | 원본 `src.add` 가 `ro` 에 비친다 | (1) |
| 커튼을 걷으면 문 | `as MutableList` 로 캐스트해 고친다 | (1) ★ |
| 옆집(Java)은 커튼을 모른다 | Java 는 `List` 를 **처음부터 문으로** 본다 | (3) |
| 방이 진짜 잠긴 것 | Java `List.of` · `listOf` 결과의 `add` | (1)(3) |

```text
                               src ──────────────┐
   val src = mutableListOf(1,2,3)                 v
   val ro: List<Int> = src      ro ──────>  [ java.util.ArrayList : 1 2 3 ]   ← 객체는 하나 (ro === src)
                                                  ^
   src.add(4)                   문으로 넣는다 ──────┘   ro 로 읽으면 [1, 2, 3, 4]
   ro.add(5)                    ✗ 컴파일 에러  「unresolved reference 'add'」       ← 타입이 막는다
   (ro as MutableList).add(100) ✓ 통과 — 객체는 원래 ArrayList                       ← 타입만 벗기면 끝
   Java: repo.items().add("J")  ✓ 통과 — Java 에게 List 는 처음부터 java.util.List   ← 타입이 아예 없다

   listOf(1, 2)          ──>  [ Arrays$ArrayList ]   add ✗ UnsupportedOperationException · set ✓   (객체가 반쯤 막는다)
   emptyList()           ──>  [ EmptyList ]          as MutableList 부터 ✗ ClassCastException
   Java List.of("x","y") ──>  [ ImmutableCollections$List12 ]   add ✗ · set ✗                    (객체가 전부 막는다)
```

## 이 주제가 답하려는 질문

1. `List` 로 받은 것은 **정말 안 바뀌나** — 누가, 어떤 경로로 바꿀 수 있나.
2. `listOf` 의 결과와 Java `List.of` 의 결과는 **무엇이 다른가**.
3. 연산 API(`map`·`filter`·`asReversed`·`reversed`·`sorted`·`sort`·`plus`)는 **새 리스트를 주나, 원본을 보나, 원본을 고치나**.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **뷰 구멍 재현(실행 + `===`)** | 같은 객체인가 · 캐스트로 고치면 원본이 바뀌나((1)) | ★ **본체 창** |
| ★★ **`javap` — 캐스트·타입 검사가 부르는 것** | `is`/`as MutableList` 가 **무엇으로** 판정하나((1)) | [33번 주제](../33-type-checks-and-casts-is-as/)의 창을 컬렉션에 |
| ★★ **컴파일 에러** | 타입이 막아 주는 것((2)) | 이 갈래의 기본 창 |
| ★★ **Java 에서 던지기** | Java 는 `List` 를 고친다 · Java `List.of` 와 대비((3)) | [Java 40번](../../../java/syntax/40-list-set-and-immutable-factories/)의 창 |
| ★ **연산 API 의 `===`·뒤늦은 변경** | 새 리스트인가 뷰인가((4)) | — |
| ★ **다른 언어 셋** | 같은 구멍(C#) · 컴파일러가 막음(Rust) · 진짜 불변(Python `tuple`)((5)) | 대비 |
| **인용 — 다시 안 잰다** | 런타임 클래스 실측표 | [`../../언어-특성/README.md`](../../언어-특성/README.md) §5 |
| **부적용 — 실행 시간·할당** | 「`asReversed` 가 싸다」·「`toList` 가 비싸다」는 **재지 않았다** | — |

### (1) ★★★ 구멍 재현 — `List` 로 받아 캐스트해 고친다

**언제 쓰나** — 「`List` 로 받았으니 안전하다」고 믿는 함수, 또는 **내부 가변 리스트를 `List` 로 내주는** 클래스를 읽을 때.

```kotlin
// hole40.kt
fun total(xs: List<Int>): Int {
    (xs as MutableList<Int>).add(100)
    return xs.sum()
}

fun main() {
    val src = mutableListOf(1, 2, 3)
    val ro: List<Int> = src
    println("1 ro === src: ${ro === src}")
    src.add(4)
    println("2 ro: $ro")
    println("3 total(ro): ${total(ro)}")
    println("4 src: $src")

    val lo = listOf(1, 2)
    println("5 lo is MutableList: ${lo is MutableList<*>}")
    println("6 listOf(1) is MutableList: ${listOf(1) is MutableList<*>}")
    println("7 emptyList() is MutableList: ${emptyList<Int>() is MutableList<*>}")
    try { (lo as MutableList<Int>).add(3); println("8 lo: $lo") } catch (e: Exception) { println("8 ${e::class.java.name}") }
    try { (lo as MutableList<Int>)[0] = 9; println("9 lo: $lo") } catch (e: Exception) { println("9 ${e::class.java.name}") }
    try { (emptyList<Int>() as MutableList<Int>).add(1); println("10 ok") } catch (e: Exception) { println("10 ${e::class.java.name}") }
}
```

```text
===== kotlinc hole40.kt -d o40h =====
(exit 0)
===== java -cp o40h:kotlin-stdlib.jar Hole40Kt =====
1 ro === src: true
2 ro: [1, 2, 3, 4]
3 total(ro): 110
4 src: [1, 2, 3, 4, 100]
5 lo is MutableList: true
6 listOf(1) is MutableList: true
7 emptyList() is MutableList: false
8 java.lang.UnsupportedOperationException
9 lo: [9, 2]
10 java.lang.ClassCastException
(exit 0)
```

- ★★★ **`ro === src` 가 `true`** — `List<Int>` 로 받은 것은 **같은 객체**다. 복사가 없다. 그래서 `src.add(4)` 가 `ro` 로 **그대로 보인다**(2).
- ★★★ **`total(ro)` 가 원본을 고쳤다** — `total` 은 `List<Int>` 를 받는 함수인데 안에서 `as MutableList<Int>` 로 캐스트해 `add(100)` 했다. 결과 `110`, 그리고 **호출한 쪽의 `src` 가 `[1, 2, 3, 4, 100]`**. **컴파일 경고도 없다.** 읽기 전용은 **타입의 사양**이지 객체의 거부가 아니다.
- ★★★ **`listOf(1, 2) is MutableList` 가 `true`** — `listOf(1)` 도 `true`. 「`listOf` 결과는 `MutableList` 가 아니다」라는 직관과 반대다. **`emptyList()` 만 `false`**.
- ★★ **그런데 캐스트한 `listOf(1, 2)` 에 `add` 하면 `UnsupportedOperationException`**(8), **`set` 은 통과해 `lo` 가 `[9, 2]`**(9) — §5 표의 「Java 에서 `set` 성공」을 **Kotlin 쪽 캐스트로** 같은 자리에서 다시 본 것이다(런타임 클래스는 재지 않았다 — 표가 `Arrays$ArrayList` 라 적는다).
- ★★ **`emptyList()` 는 캐스트부터 `ClassCastException`**(10) — 고치기 전에 막힌다.

**왜 셋이 갈리나 — 캐스트와 타입 검사가 부르는 것**

```text
===== javap -c -p o40h/Hole40Kt.class | grep -E 'TypeIntrinsics' =====
       7: invokestatic  #22                 // Method kotlin/jvm/internal/TypeIntrinsics.asMutableList:(Ljava/lang/Object;)Ljava/util/List;
     197: invokestatic  #103                // Method kotlin/jvm/internal/TypeIntrinsics.isMutableList:(Ljava/lang/Object;)Z
     232: invokestatic  #103                // Method kotlin/jvm/internal/TypeIntrinsics.isMutableList:(Ljava/lang/Object;)Z
     263: invokestatic  #103                // Method kotlin/jvm/internal/TypeIntrinsics.isMutableList:(Ljava/lang/Object;)Z
     287: invokestatic  #22                 // Method kotlin/jvm/internal/TypeIntrinsics.asMutableList:(Ljava/lang/Object;)Ljava/util/List;
     370: invokestatic  #22                 // Method kotlin/jvm/internal/TypeIntrinsics.asMutableList:(Ljava/lang/Object;)Ljava/util/List;
     457: invokestatic  #22                 // Method kotlin/jvm/internal/TypeIntrinsics.asMutableList:(Ljava/lang/Object;)Ljava/util/List;
(exit 0)
```

```text
===== javap -cp kotlin-stdlib.jar -c kotlin.jvm.internal.TypeIntrinsics | awk '/boolean isMutableList\(java.lang.Object\);/,/ireturn/; /java.util.List asMutableList\(java.lang.Object\);/,/areturn/' =====
  public static boolean isMutableList(java.lang.Object);
    Code:
       0: aload_0
       1: instanceof    #35                 // class java/util/List
       4: ifeq          25
       7: aload_0
       8: instanceof    #18                 // class kotlin/jvm/internal/markers/KMappedMarker
      11: ifeq          21
      14: aload_0
      15: instanceof    #36                 // class kotlin/jvm/internal/markers/KMutableList
      18: ifeq          25
      21: iconst_1
      22: goto          26
      25: iconst_0
      26: ireturn
  public static java.util.List asMutableList(java.lang.Object);
    Code:
       0: aload_0
       1: instanceof    #18                 // class kotlin/jvm/internal/markers/KMappedMarker
       4: ifeq          20
       7: aload_0
       8: instanceof    #36                 // class kotlin/jvm/internal/markers/KMutableList
      11: ifne          20
      14: aload_0
      15: ldc           #37                 // String kotlin.collections.MutableList
      17: invokestatic  #21                 // Method throwCce:(Ljava/lang/Object;Ljava/lang/String;)V
      20: aload_0
      21: invokestatic  #38                 // Method castToList:(Ljava/lang/Object;)Ljava/util/List;
      24: areturn
(exit 0)
===== javap -cp kotlin-stdlib.jar kotlin.collections.EmptyList | grep -E '^public' =====
public final class kotlin.collections.EmptyList implements java.util.List,java.io.Serializable,java.util.RandomAccess,kotlin.jvm.internal.markers.KMappedMarker {
(exit 0)
```

```text
   Kotlin 소스                 컴파일 결과                          판정 (TypeIntrinsics)
   x is MutableList<*>   ───>  TypeIntrinsics.isMutableList(x)      java.util.List 인가?
                                                                    ├─ KMappedMarker 가 아니면  → true   (Java 클래스 — 판정 불가라 통과)
                                                                    └─ KMappedMarker 면        → KMutableList 인가?
   x as MutableList<Int> ───>  TypeIntrinsics.asMutableList(x)      KMappedMarker 인데 KMutableList 가 아니면 → ClassCastException

   listOf(1, 2)   = Arrays$ArrayList      (Java 클래스)                 is → true  · as → 통과 · add 는 객체가 거부 · set 은 통과
   listOf(1)      = Collections$SingletonList (Java 클래스)             is → true
   emptyList()    = kotlin EmptyList      implements … KMappedMarker    is → false · as → ClassCastException
```

- ★★★ **JVM 에는 `List` 와 `MutableList` 의 구분이 없다** — 둘 다 `java.util.List` 다. 그래서 `is MutableList` 는 **Kotlin 이 만든 클래스에만** 붙는 표시(`KMappedMarker` = 「Kotlin 읽기 전용 인터페이스로 매핑된 클래스」 · `KMutableList` = 「그중 가변」)로 가른다.
- ★★ **표시가 없는 Java 클래스는 「가변일 수 있다」로 통과**시킨다 — `Arrays$ArrayList`·`SingletonList` 가 `true` 인 이유다. **`true` 는 「고칠 수 있다」가 아니라 「못 가린다」** 다(8번 줄의 `add` 가 실패했다).
- ★ `EmptyList` 는 **Kotlin 클래스**라 `KMappedMarker` 를 달고 있고 `KMutableList` 는 없다 — 그래서 `false` 이고 캐스트가 **`throwCce`** 로 막힌다.
- ★ 이 판정 방식은 **stdlib·백엔드의 구현**이다. 언어가 약속하는 것은 「`List` 에 고치는 멤버가 없다」까지다.

### (2) ★★ 타입이 막아 주는 것

```kotlin
// bad40.kt
fun main() {
    val ro: List<Int> = mutableListOf(3, 1, 2)
    ro.add(4)
    ro[0] = 9
    ro.sort()
    val ml: MutableList<Any> = mutableListOf<Int>(1)
}
```

```text
===== kotlinc bad40.kt -d o40b =====
bad40.kt:3:8: error: unresolved reference 'add' on receiver of type 'List<Int>'.
    ro.add(4)
       ^^^
bad40.kt:4:7: error: no 'set' operator method providing array access.
    ro[0] = 9
      ^^^
bad40.kt:5:8: error: unresolved reference 'sort' on receiver of type 'List<Int>'.
    ro.sort()
       ^^^^
bad40.kt:6:30: error: initializer type mismatch: expected 'MutableList<Any>', actual 'MutableList<Int>'.
    val ml: MutableList<Any> = mutableListOf<Int>(1)
                             ^
(exit 1)
```

- ★★★ **`ro.add(4)` · `ro[0] = 9` · `ro.sort()` 가 전부 컴파일 에러** — 「`unresolved reference 'add' on receiver of type 'List<Int>'.`」 · 「`no 'set' operator method providing array access.`」 · 「`unresolved reference 'sort' on receiver of type 'List<Int>'.`」. **`ro` 의 실체가 `mutableListOf` 인데도** 막힌다 — 타입이 막는다.
- ★★ **`sort()` 는 `MutableList` 에만 있는 확장**이다 — `List` 에는 새 리스트를 돌려주는 `sorted()` 뿐이다((4)).
- ★★ **`MutableList<Int>` 는 `MutableList<Any>` 자리에 못 들어간다**(「`initializer type mismatch`」) — 무공변이다. 반대로 `List<Int>` 는 `List<Any>` 자리에 **들어간다**((4)의 8) — `List<out E>` 이기 때문이다([28번 주제](../28-generics-variance-in-out-star-where/) (3)이 stdlib 선언을 뽑았다).

### (3) ★★ Java 로 넘기면 — Java 는 커튼을 모른다

**언제 쓰나** — Kotlin 클래스의 `fun items(): List<String>` 을 **Java 모듈이** 부를 때.

```kotlin
// repo40.kt
class Repo {
    private val items = mutableListOf("a")
    fun items(): List<String> = items
    fun fixed(): List<String> = listOf("x", "y")
    fun dump(): String = items.toString()
}
```

```java
// JRepo.java
import java.util.List;

public class JRepo {
    public static void main(String[] args) {
        Repo repo = new Repo();
        repo.items().add("J");
        System.out.println("1 dump: " + repo.dump());
        List<String> f = repo.fixed();
        try { f.add("J"); System.out.println("2 " + f); } catch (RuntimeException e) { System.out.println("2 " + e.getClass().getName()); }
        try { f.set(0, "J"); System.out.println("3 " + f); } catch (RuntimeException e) { System.out.println("3 " + e.getClass().getName()); }
        List<String> jf = List.of("x", "y");
        try { jf.set(0, "J"); System.out.println("4 " + jf); } catch (RuntimeException e) { System.out.println("4 " + e.getClass().getName()); }
    }
}
```

```text
===== kotlinc repo40.kt -d o40r =====
(exit 0)
===== javac -cp o40r -d o40r JRepo.java =====
(exit 0)
===== java -cp o40r:kotlin-stdlib.jar JRepo =====
1 dump: [a, J]
2 java.lang.UnsupportedOperationException
3 [J, y]
4 java.lang.UnsupportedOperationException
(exit 0)
```

- ★★★ **`repo.items().add("J")` 가 통과하고 `dump` 가 `[a, J]`** — 내부 `private val items` 가 **Java 에게 고쳐졌다.** `javac` 도 경고 없이 통과한다. Java 에게 Kotlin `List<String>` 은 **`java.util.List<String>`** 이고, 그 인터페이스에는 `add` 가 **있다**. Kotlin 이 준 「읽기 전용」은 **Kotlin 컴파일러 안에서만** 산다.
- ★★ **`listOf("x","y")` 에는 `add` 가 `UnsupportedOperationException`(2), `set` 은 통과해 `[J, y]`(3)** — **객체가 반쯤만** 막는다. §5 표의 두 칸 그대로다.
- ★★★ **Java `List.of("x","y")` 는 `set` 도 `UnsupportedOperationException`(4)** — **객체가 전부** 막는다. 이것이 [Java 40번](../../../java/syntax/40-list-set-and-immutable-factories/) (2)의 「진짜 불변 객체」다. Kotlin `listOf` 는 **이름이 비슷할 뿐 그것이 아니다.**

### (4) ★ 연산 API 고르기 — 새 리스트인가, 뷰인가, 원본을 고치나

```kotlin
// ops40.kt
fun main() {
    val src = mutableListOf(3, 1, 2)
    val m = src.map { it }
    val f = src.filter { true }
    println("1 map === src: ${m === src}  filter === src: ${f === src}")
    val rv = src.asReversed()
    val rd = src.reversed()
    val so = src.sorted()
    val p = src + 9
    src.add(0)
    println("2 asReversed: $rv")
    println("3 reversed: $rd")
    println("4 sorted: $so")
    println("5 plus: $p")
    println("6 src: $src")
    src.sort()
    println("7 src after sort(): $src  rv: $rv")
    val wide: List<Any> = src
    println("8 wide === src: ${wide === src}")
}
```

```text
===== kotlinc ops40.kt -d o40o =====
(exit 0)
===== java -cp o40o:kotlin-stdlib.jar Ops40Kt =====
1 map === src: false  filter === src: false
2 asReversed: [0, 2, 1, 3]
3 reversed: [2, 1, 3]
4 sorted: [1, 2, 3]
5 plus: [3, 1, 2, 9]
6 src: [3, 1, 2, 0]
7 src after sort(): [0, 1, 2, 3]  rv: [3, 2, 1, 0]
8 wide === src: true
(exit 0)
```

| API | 받는 쪽 | 돌려주는 것 | 원본을 나중에 고치면 | 근거 |
|---|---|---|---|---|
| `map { }` · `filter { }` | `List` | **새 리스트**(`=== src` 가 `false`) — 걸러진 게 없어도 새것 | 안 따라온다 | 1 |
| `asReversed()` | `List` · `MutableList` 둘 다(아래 소스) | ★ **뷰** | ★ **따라온다** — `add` 도 `sort()` 도 | 2 · 7 |
| `reversed()` · `sorted()` | `List` | **새 리스트** | 안 따라온다 | 3 · 4 |
| `plus`(`+`) | `List` | **새 리스트** | 안 따라온다 | 5 |
| `sort()` | ★ **`MutableList` 만** | `Unit` — **원본을 고친다** | — | 7 · (2) |
| `List<Int>` → `List<Any>` 대입 | — | **같은 객체**(`=== src` 가 `true`) | 따라온다 | 8 |

```text
===== unzip -o -q kotlin-stdlib-sources.jar commonMain/kotlin/collections/ReversedViews.kt =====
(exit 0)
===== grep -n 'fun <T> .*asReversed' commonMain/kotlin/collections/ReversedViews.kt =====
77:public fun <T> List<T>.asReversed(): List<T> = ReversedListReadOnly(this)
85:public fun <T> MutableList<T>.asReversed(): MutableList<T> = ReversedList(this)
(exit 0)
```

- ★★★ **`asReversed()` 만 뷰다** — `src.add(0)` 뒤 `rv` 가 `[0, 2, 1, 3]` 이 됐고, `src.sort()` 뒤에는 `[3, 2, 1, 0]` 이 됐다. 이름이 `reversed()` 와 한 글자 차이인데 **복사 여부가 정반대**다.
- ★★ **`map`·`filter`·`sorted`·`reversed`·`plus` 는 전부 새 리스트** — 원본이 뒤에 바뀌어도(`src` 에 `0` 추가) 결과는 그대로다.
- ★★ **`sorted` 대 `sort`** — `sorted()` 는 `List` 에 있고 새것을 주며, `sort()` 는 `MutableList` 에만 있고 **제자리에서** 고친다. `List` 로 받은 쪽은 `sort()` 를 **부를 수조차 없다**((2)).
- ★ **`List<Any>` 로 넓혀 받아도 같은 객체**다 — 변성은 **타입만** 넓히고 복사하지 않는다.
- ★ 이 표의 「새 리스트」는 **`===` 로 확인한 것**이지 복사 비용이 아니다. 비용은 재지 않았다.

### (5) ★ 다른 언어의 같은 자리 — 같은 구멍 · 컴파일러가 막음 · 진짜 불변

**C# — `IReadOnlyList<T>` 도 뷰다(같은 구멍)**

```csharp
// RoCs.cs
using System;
using System.Collections.Generic;

class RoCs {
    static void Main() {
        var src = new List<int> { 1, 2, 3 };
        IReadOnlyList<int> ro = src;
        Console.WriteLine("1 same: " + ReferenceEquals(ro, src));
        ((List<int>)ro).Add(4);
        Console.WriteLine("2 src: " + string.Join(",", src));
        var real = src.AsReadOnly();
        Console.WriteLine("3 is IList<int>: " + (real is IList<int>));
        try { ((IList<int>)real).Add(5); } catch (Exception e) { Console.WriteLine("4 " + e.GetType().FullName); }
    }
}
```

```text
===== csc -out:rocs.dll RoCs.cs =====
(exit 0)
===== dotnet rocs.dll =====
1 same: True
2 src: 1,2,3,4
3 is IList<int>: True
4 System.NotSupportedException
(exit 0)
```

- ★★ **`((List<int>)ro).Add(4)` 가 원본을 고쳤다** — Kotlin (1)의 `as MutableList` 와 **같은 구멍**이다. `IReadOnlyList<T>` 도 **인터페이스(창문)** 이고 객체는 `List<int>` 다.
- ★ `AsReadOnly()` 는 **래퍼 객체**를 만든다 — 그것도 `IList<int>` 를 구현하지만 `Add` 가 `NotSupportedException`. Java `unmodifiableList` 와 같은 「객체가 거부하는 뷰」다. 변성 쪽은 [C# 26번](../../../csharp/syntax/26-covariance-and-contravariance-out-in/)(`IReadOnlyList<out T>`)이다.

**Rust — `&Vec` 는 컴파일러가 막는다**

```rust
// borrow40.rs
fn total(xs: &Vec<i32>) -> i32 {
    xs.push(100);
    xs.iter().sum()
}

fn main() {
    let mut src = vec![1, 2, 3];
    println!("{}", total(&src));
    src.push(4);
}
```

```text
===== rustc --edition 2021 borrow40.rs -o borrow40 =====
error[E0596]: cannot borrow `*xs` as mutable, as it is behind a `&` reference
 --> borrow40.rs:2:5
  |
2 |     xs.push(100);
  |     ^^ `xs` is a `&` reference, so the data it refers to cannot be borrowed as mutable
  |
help: consider changing this to be a mutable reference
  |
1 | fn total(xs: &mut Vec<i32>) -> i32 {
  |               +++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0596`.
(exit 1)
```

- ★★★ **`&Vec<i32>` 로 받은 쪽은 `push` 를 못 한다 — 캐스트로 벗길 길이 없다**(「`` cannot borrow `*xs` as mutable, as it is behind a `&` reference ``」). Rust 의 읽기 전용은 **타입이 아니라 참조의 종류**(`&` 대 `&mut`)이고, 컴파일러가 **빌림 규칙**으로 강제한다([Rust 10번](../../../rust/syntax/10-borrowing-and-aliasing-rules/)).

**Python — `tuple` 은 진짜 불변, `Sequence` 힌트는 아무것도 안 막는다**

```python
# hint40.py
from collections.abc import Sequence


def total(xs: Sequence[int]) -> int:
    xs.append(100)
    return sum(xs)


src = [1, 2, 3]
print("1", total(src), src)
t = (1, 2, 3)
try:
    total(t)
except AttributeError as e:
    print("2", type(e).__name__, e)
try:
    t[0] = 9
except TypeError as e:
    print("3", type(e).__name__, e)
```

```text
===== python3 hint40.py =====
1 106 [1, 2, 3, 100]
2 AttributeError 'tuple' object has no attribute 'append'
3 TypeError 'tuple' object does not support item assignment
(exit 0)
```

- ★★ **`Sequence[int]` 라고 적은 함수가 `list` 에 `append` 했고 원본이 바뀌었다**(1) — 타입 힌트는 **런타임에 아무것도 안 한다**(Kotlin 은 적어도 컴파일에서 막는다). **`tuple` 은 객체가 거부한다**(2·3) — `append` 가 없고 항목 대입이 `TypeError`. `tuple` 은 [Python 11번](../../../python/syntax/11-tuple-and-unpacking/)이다.

## 문법 — 형태와 규칙

**형태** — 내부 가변 리스트를 읽기 전용으로 내주는 두 방법(뷰 · 사본). 여기서는 표로만 두고, **사본을 만드는 자리**는 [41번 주제](../41-collection-creation-and-copying/)가 캡처로 잰다.

| 내주는 꼴 | 밖에서 `List` 로 고칠 수 있나 | 원본 변경이 보이나 | 근거 |
|---|---|---|---|
| `fun items(): List<T> = items` | ★ **Kotlin 은 캐스트로 · Java 는 그냥** | 보인다 | (1)(3) |
| `fun items(): List<T> = items.toList()` | 사본을 고칠 뿐 **원본은 안 바뀐다** | 안 보인다 | [41번 주제](../41-collection-creation-and-copying/) |

**규칙 불릿**

- `List<E>` 에는 **고치는 멤버가 없다** — `add`·`set`·`sort` 는 컴파일 에러((2)).
- `List` 타입은 **객체가 안 바뀐다는 약속이 아니다** — 같은 객체를 `MutableList` 로 든 쪽이 고칠 수 있다((1)).
- `as MutableList` 는 **Java 클래스면 통과**한다 — 고칠 수 있는지는 **객체**가 정한다((1)).
- Java 에게 Kotlin `List` 는 **`java.util.List`** — 고치는 메서드가 전부 보인다((3)).
- `map`·`filter`·`sorted`·`reversed`·`plus` 는 **새 리스트**, `asReversed` 는 **뷰**, `sort` 는 **제자리**((4)).
- `List<out E>` — `List<Int>` 를 `List<Any>` 로 받을 수 있다(같은 객체)((2)(4)).

## 어디서 틀리나

1. ★★★ **`List` 로 받았으니 안 바뀐다고 믿는다.** 원본 참조를 든 쪽이 고치면 **그대로 비친다**((1)).
2. ★★★ **`List` 로 내주면 밖에서 못 고친다고 믿는다.** Kotlin 은 캐스트 한 줄, **Java 는 그냥** 고친다((1)(3)).
3. ★★★ **`listOf` 가 Java `List.of` 와 같다고 믿는다.** `set` 이 **통과한다**((3)) — §5 표.
4. ★★ **`is MutableList` 로 가변 여부를 가린다.** Java 클래스는 `true` 로 **통과**한다((1)) — 「고칠 수 있다」가 아니다.
5. ★★ **`asReversed()` 를 `reversed()` 처럼 쓴다.** 뷰라서 원본을 따라 바뀐다((4)).
6. ★ **`List` 에서 `sort()` 를 찾는다.** `sorted()` 다((2)(4)).
7. ★ **`filter` 가 걸러진 게 없으면 원본을 돌려준다고 믿는다.** 항상 새 리스트다((4)).

## 구현 세부사항 대 언어 보장

| 항목 | 어느 쪽인가 | 근거 |
|---|---|---|
| `List<E>` 에 고치는 멤버가 없다 · `add`·`sort` 가 컴파일 에러 | ★★★ **언어 보장**(타입 규칙) | (2) |
| `List` 는 **뷰**다 — 같은 객체를 가변 참조로 고칠 수 있다 | ★★★ **언어 보장**(타입이 객체를 바꾸지 않는다) · 문서 | (1) |
| `List<out E>` · `MutableList<E>` 무공변 | **언어 보장**(stdlib 선언) | (2) · [28번 주제](../28-generics-variance-in-out-star-where/) (3) |
| `listOf(…)` 의 **실제 클래스**와 그 `add`/`set` 동작 | ★★ **stdlib 구현** | [`../../언어-특성/README.md`](../../언어-특성/README.md) §5 · (1)(3) |
| `is`/`as MutableList` 가 `TypeIntrinsics` 와 `KMappedMarker` 로 판정 | ★★ **JVM 백엔드·stdlib 구현** | (1) |
| `listOf(1, 2) is MutableList` 가 `true` | ★ **이 판의 관찰**(위 두 구현의 결과) | (1) |
| `map`·`filter`·`sorted` 가 새 리스트 · `asReversed` 가 뷰 | **stdlib 구현** — 이 판에서 `===` 와 소스(`ReversedListReadOnly`·`ReversedList`)로 확인. API 문서는 **열어 보지 않았다** | (4) |
| Java 가 `List` 를 고칠 수 있다 | **JVM 매핑의 결과**(Kotlin 컬렉션 인터페이스가 `java.util` 로 매핑) | (3) |

★★ **가장 조심할 자리** — 「`listOf` 는 불변이다」라고 적으면 **언어 보장과 stdlib 구현을 한 문장에 섞은 것**이다. 타입은 「읽기 전용 참조」만 약속하고, 객체가 무엇을 거부하는지는 **`listOf` 가 이 판에서 어떤 클래스를 돌려주느냐**다 — 그 표는 §5 에 있고 **판이 바뀌면 다시 재야** 한다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 함수가 리스트를 **읽기만** 한다 | ★ `List<T>` 로 받는다 | (2) — 실수로 고치는 것을 컴파일에서 막는다 |
| 내부 상태를 밖에 내주는데 **밖이 못 고치게** 해야 한다 | ★ **사본**(`toList()`) — 뷰로 내주지 않는다 | (1)(3) — 캐스트·Java 로 뚫린다 · [41번 주제](../41-collection-creation-and-copying/) |
| 내부 상태를 **실시간으로 보여 주되** 밖이 못 고친다 | `java.util.Collections.unmodifiableList(items)` | 객체가 거부하는 뷰 — [Java 40번](../../../java/syntax/40-list-set-and-immutable-factories/) (3) |
| 뒤집어 **읽기만** 한다 · 원본을 따라가야 한다 | `asReversed()` | (4) — 뷰 |
| 뒤집은 **결과를 따로** 둔다 | `reversed()` | (4) — 새 리스트 |
| 정렬 결과가 필요하다 · 원본은 그대로 | `sorted()` | (4) |
| 가변 리스트를 제자리에서 정렬 | `sort()` | (4) — `MutableList` 만 |
| 가변 여부를 런타임에 가리고 싶다 | ✗ `is MutableList` — Java 클래스를 못 가린다 | (1) |

## 핵심 문장

1. Kotlin `List` 는 **불변이 아니라 읽기 전용 뷰**다 — `val ro: List<Int> = src` 는 복사가 아니고 `ro === src` 다.
2. 읽기 전용은 **타입이 사양하는 것**이라 `as MutableList` 한 줄, 또는 **Java 호출자**가 그냥 뚫는다 — 원본이 바뀐다.
3. `listOf` 의 결과는 Java `List.of` 가 **아니다** — `add` 는 막지만 `set` 은 통과한다(§5 표 · 여기서 Kotlin 캐스트와 Java 양쪽으로 다시 봤다).
4. `is MutableList` 는 Java 클래스를 **못 가린다** — `listOf(1, 2) is MutableList` 가 `true` 다.
5. 연산 API 는 대부분 **새 리스트**를 주고, `asReversed` 는 **뷰**, `sort` 는 **제자리**다.

## 관련 자료

- [`../../언어-특성/README.md`](../../언어-특성/README.md) §5 — ★★★ **정본.** 런타임 클래스 실측표 · 「읽기 전용은 불변이 아니다 — 공식 문서가 이 말을 흐린다」 · 방어 복사와 `kotlinx.collections.immutable`. 그쪽은 **왜 구멍인가와 실측표**, 여기는 **구멍을 코드로 재현하고 API 를 고르는 법**.
- [Java 40번](../../../java/syntax/40-list-set-and-immutable-factories/) — ★★ **짝.** `List.of`(진짜 불변 객체) · `unmodifiableList`(객체가 거부하는 뷰) · `Arrays.asList`(배열의 뷰).
- [28번 주제](../28-generics-variance-in-out-star-where/) (3) — `List<out E>`·`MutableList<E>` 선언.
- [33번 주제](../33-type-checks-and-casts-is-as/) — `is`/`as`/`as?` 의 일반 규칙.
- [01번 주제](../01-val-var-and-basic-types/) — `val` 은 참조만 잠근다.
- [41번 주제](../41-collection-creation-and-copying/) — 만드는 자리에서 가변성을 정하고 **복사가 일어나는 자리**.
- [`cs/data-structure/`](../../../../../data-structure/) — 배열 리스트의 내부.
- 대비 — [C# 26번](../../../csharp/syntax/26-covariance-and-contravariance-out-in/) · [Rust 10번](../../../rust/syntax/10-borrowing-and-aliasing-rules/) · [Python 11번](../../../python/syntax/11-tuple-and-unpacking/).

## 용어 풀이

> **읽기 전용(read-only)** — **이 참조로는** 못 고친다는 타입의 성질. 객체가 안 바뀐다는 뜻이 아니다.

> **불변(immutable)** — **객체 자체가** 바뀌지 않는 성질. 누구의 참조로도 못 고친다.\
> 예: Java `List.of("a")` · Python `tuple`.

> **뷰(view)** — 원본을 복사하지 않고 **원본을 보여 주는** 객체·참조. 원본이 바뀌면 따라 바뀐다.\
> 예: `val ro: List<Int> = src` · `src.asReversed()`.

> **`KMappedMarker`** — Kotlin stdlib 가 **자기 컬렉션 클래스**에 다는 표시 인터페이스. 「Kotlin 읽기 전용 인터페이스로 매핑된 클래스」라는 뜻이다(가변이면 `KMutableList` 등이 더 붙는다).

> **`TypeIntrinsics`** — `is MutableList`·`as MutableList` 처럼 **JVM 에 없는 구분**을 판정하려고 컴파일러가 부르는 stdlib 보조 클래스.

> **`UnsupportedOperationException`** — 고치는 메서드가 **지원되지 않을 때** 객체가 던지는 예외. 타입이 아니라 **객체가 거부한** 흔적이다.

## 더 들어가면

- **Set·Map 도 같은가** — 이 문서는 `List` 만 던졌다. `setOf`·`mapOf` 의 런타임 클래스는 §5 표에도 없다 — 같은 창((1)의 `is`/`as` + Java 쪽)으로 재 볼 다음 자리다.
- **진짜 불변 컬렉션** — `kotlinx.collections.immutable` 은 stdlib 밖이고 Alpha 라는 것이 §5 의 결론이다. 이 문서는 **설치하지 않았다.**
- **`asReversed` 에 대한 쓰기** — `MutableList.asReversed()` 는 **`MutableList`** 를 돌려준다(소스). 그 뷰에 **쓰면** 원본이 어떻게 되는지는 이 문서가 **던지지 않았다** — 읽기 쪽만 봤다.
