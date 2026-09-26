# kotlin/syntax/40 — 컬렉션 — 읽기 전용 인터페이스와 실제 런타임 타입 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javac`·`java`·`javap` 에서 실제로 얻었다. 대비는 .NET 10.0.401 · rustc 1.92.0 · Python 3.12.3.\
> 역어셈블은 **기본 `-jvm-target`(1.8)** 이 정본이다.
> ★★ 아래 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적은 자리가 없다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 컴파일된다 · `ro === src: true` · `[1, 2, 3, 4]` · `110` · **`4 src: [1, 2, 3, 4, 100]`** — `List` 로 받은 함수가 **호출한 쪽의 원본을 고쳤다**

**출력**

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

**왜 그런가**

- ★★★ `val ro: List<Int> = src` 는 **복사가 아니라 같은 객체**다. 원본이 바뀌면 비치고(2), `as MutableList` 로 타입만 벗기면 **고칠 수 있다**(3·4).
- ★★ 캐스트에 **경고도 없다**(`kotlinc … (exit 0)`). 읽기 전용은 **타입의 사양**이지 객체의 거부가 아니다.

### 2. ★★★ `5 true` · `6 true` · `7 false` · `8 UnsupportedOperationException` · **`9 lo: [9, 2]`** · `10 ClassCastException`

**출력** — 1번 블록의 `5`\~`10` 줄이다.

**왜 그런가**

- ★★★ `listOf(1, 2)`·`listOf(1)` 은 **Java 클래스**(§5 표 — `Arrays$ArrayList`·`SingletonList`)라 `is MutableList` 가 가리지 못하고 `true` 다. `emptyList()` 는 **Kotlin 클래스**라 가려진다(3번).
- ★★ 캐스트가 통과해도 **고칠 수 있는지는 객체가 정한다** — `Arrays$ArrayList` 는 `add` 를 거부하고 `set` 은 받는다. 그래서 `lo` 가 `[9, 2]` 로 **바뀌었다.**
- ★ `emptyList()` 는 **캐스트 단계에서** 막힌다 — 고치기도 전이다.

### 3. ★★ `is` → **`TypeIntrinsics.isMutableList`** · `as` → **`TypeIntrinsics.asMutableList`** — `java.util.List` 인지 본 뒤 **`KMappedMarker`**(Kotlin 컬렉션 표시)가 있으면 **`KMutableList`** 인지 보고, 표시가 **없으면 통과**시킨다

**출력**

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

**왜 그런가**

- ★★★ JVM 에서 `List` 와 `MutableList` 는 **같은 `java.util.List`** 다. 그래서 컴파일러는 `instanceof` 하나로 못 끝내고 stdlib 보조 메서드를 부른다.
- ★★ **Kotlin 이 만든 클래스만** 표시(`KMappedMarker`)를 단다 — `EmptyList` 의 `implements` 목록에 그것이 있다. 표시가 없는 Java 클래스는 「**못 가린다 → 통과**」다.
- ★ 이 판정 방식은 **구현**이다 — 언어는 「`List` 에 고치는 멤버가 없다」까지만 약속한다.

### 4. ★★ **3·4·5·6번째 줄 전부** — `add`·`sort` 는 「`unresolved reference … on receiver of type 'List<Int>'.`」 · `ro[0] = 9` 는 「`no 'set' operator method providing array access.`」 · `MutableList<Any>` 는 「`initializer type mismatch`」

**출력**

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

**왜 그런가**

- ★★★ `ro` 의 **실체는 `mutableListOf`** 인데도 막힌다 — 판정은 **타입**(`List<Int>`)으로만 한다.
- ★★ `MutableList<E>` 는 **무공변**이라 `MutableList<Int>` 가 `MutableList<Any>` 자리에 못 들어간다. `List<out E>` 는 들어간다(6번의 `8`) — [28번 주제](../28-generics-variance-in-out-star-where/) (3).

### 5. ★★★ `javac` 통과 · **`1 dump: [a, J]`** · `2 UnsupportedOperationException` · **`3 [J, y]`** · `4 UnsupportedOperationException`

**출력**

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

**왜 그런가**

- ★★★ Java 에게 `items()` 의 반환 타입은 **`java.util.List<String>`** 이고 `add` 가 **있다**. 객체는 `ArrayList` 라 거부하지 않는다 — `private val items` 가 **밖에서 고쳐졌다.**
- ★★ `listOf("x","y")` 는 **`add` 는 거부하고 `set` 은 받는다**(§5 표 그대로). Java `List.of` 는 **둘 다** 거부한다.

### 6. ★★ `1 false false` · **`2 [0, 2, 1, 3]`** · `3 [2, 1, 3]` · `4 [1, 2, 3]` · `5 [3, 1, 2, 9]` · `6 [3, 1, 2, 0]` · **`7 [0, 1, 2, 3]  rv: [3, 2, 1, 0]`** · `8 true`

**출력**

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

```text
===== unzip -o -q kotlin-stdlib-sources.jar commonMain/kotlin/collections/ReversedViews.kt =====
(exit 0)
===== grep -n 'fun <T> .*asReversed' commonMain/kotlin/collections/ReversedViews.kt =====
77:public fun <T> List<T>.asReversed(): List<T> = ReversedListReadOnly(this)
85:public fun <T> MutableList<T>.asReversed(): MutableList<T> = ReversedList(this)
(exit 0)
```

**왜 그런가**

- ★★★ **`asReversed()` 는 뷰**다 — 소스가 `ReversedListReadOnly(this)`·`ReversedList(this)` 로 **원본을 감쌀 뿐**이다. 그래서 `src.add(0)`(2)도 `src.sort()`(7)도 따라왔다.
- ★★ `map`·`filter`·`reversed`·`sorted`·`plus` 는 **새 리스트**다 — `src` 에 `0` 이 더해진 뒤에도 그대로다.
- ★ `8` — `List<Any>` 로 넓혀 받아도 **같은 객체**다. 변성은 복사하지 않는다.

### 7. `true` 는 「**이 객체가 가변이 아니라고 가릴 수 없다**」는 뜻이다 — 「고칠 수 있다」는 뜻이 **아니다**

**왜 그런가**

- ★★★ 3번의 판정은 **Kotlin 표시가 없으면 통과**다. `Arrays$ArrayList` 는 표시가 없으니 `true` 가 나오지만, 그 객체의 `add` 는 **객체 스스로** `UnsupportedOperationException` 을 던진다.
- ★ 그래서 `is MutableList` 로 「고쳐도 되나」를 가리는 코드는 **Java 클래스에서 거짓말**을 한다.

### 8. 「읽기 전용」은 **타입(언어)** 이 보장하고, 「불변」은 **객체(구현)** 가 정한다 — Kotlin `List` 타입은 불변을 보장하지 **않는다** · 밖이 절대 못 고치게 하려면 **사본**(`toList()`)을 내준다

**왜 그런가**

- ★★★ 1번(캐스트)과 5번(Java)이 **타입만으로는 못 막는다**는 증거다 — 같은 객체를 가변으로 볼 길이 있으면 뚫린다.
- ★★ 사본은 원본과 **다른 객체**라 사본이 고쳐져도 원본은 안 바뀐다 — 복사가 일어나는 자리는 [41번 주제](../41-collection-creation-and-copying/)가 잰다. 실시간으로 보여 줘야 하면 **객체가 거부하는 뷰**(`Collections.unmodifiableList`)를 쓴다 — [Java 40번](../../../java/syntax/40-list-set-and-immutable-factories/) (3).

### 9. `3` 은 Kotlin `listOf` 의 결과(`Arrays$ArrayList` — **`set` 을 받는다**)이고 `4` 는 Java `List.of` 의 결과(**전부 거부**)다 · Java 40번의 말로 — `List.of` 는 「**진짜 불변 객체**」, `listOf` 는 **그것이 아니다**(배열을 감싼 고정 길이 리스트)

**왜 그런가**

- ★★ §5 표가 이미 말한 것을 **Java 쪽에서 한 줄씩** 다시 본 것이다 — `listOf` 는 원소가 둘 이상이면 **`Arrays.asList` 로 내려간다**(표의 결론).
- ★ 이름이 비슷해 「같은 불변 팩토리」로 외우면 `set` 한 칸에서 틀린다.

### 10. `asReversed()` 는 **원본을 따라 바뀌고**(뷰), `reversed()` 는 **만든 순간의 사본**이다 — 원본이 나중에 바뀌는 코드에서 둘을 바꿔 쓰면 **결과가 달라진다**

**왜 그런가**

- ★★ 6번의 `2`·`7` 과 `3` 이 그 대조다. 뷰는 **원본의 수명과 변경에 묶인다** — 원본을 정렬하면 뷰도 정렬된 순서로 보인다.
- ★ 비용 차이는 **재지 않았다** — 「뷰가 싸다」는 이 문서가 뒷받침하지 않는다.

### 11. C# 은 **원본이 바뀐다**(`2 src: 1,2,3,4`) · Rust 는 **컴파일 에러**(`E0596`) · Python 은 **원본이 바뀐다**(`[1, 2, 3, 100]` — 힌트는 런타임에 아무것도 안 한다) · **Kotlin 과 같은 구멍은 C#** 이다

**출력**

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

**왜 그런가**

- ★★ **C# `IReadOnlyList<T>` 도 인터페이스(뷰)** 라 캐스트 한 줄에 뚫린다 — Kotlin 과 구조가 같다. Python 은 **컴파일 단계조차 없어서** 뚫리는 것이라 성격이 다르다(Kotlin 은 적어도 4번처럼 컴파일에서 막는다).
- ★★ **Rust 는 참조의 종류**(`&` 대 `&mut`)로 막고 **벗길 캐스트가 없다.** Python `tuple` 은 **객체가 거부**한다(`2`·`3`).

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
===== rustc --version =====
rustc 1.92.0 (ded5c06cf 2025-12-08)
(exit 0)
```

```text
===== python3 --version =====
Python 3.12.3
(exit 0)
```

★ **흔들리는 칸과 안 흔들리는 칸**

| 흔들린다 | 안 흔들린다 |
|---|---|
| **없다** — 해시코드·주소를 찍지 않았다(같은 객체는 `===` · C# 은 `ReferenceEquals`) | 실행 출력 · 예외 클래스 이름 · `javap` 출력 |
| | 진단의 **문구·`파일:줄:칸`·캐럿** |
| | 모든 **종료 코드** |

> 근거 — 캡처 스크립트를 처음부터 다시 돌려 **블록 전체를 바이트 단위로 대조**했다.
>
> 실측 — `capture.sh blocks` 와 `capture.sh blocks-recheck` 를 처음부터 따로 돌려 `normalize-shaky.py` 로 대조했다 —\
> **블록 80개 · 동일 80 · 흔들린 칸 0 · ★고칠 것 0**(38\~41 네 주제를 한 캡처로 받았다). `diff -rq` 도 차이 0 이다.\
> ★ **정규화 규칙은 하나도 안 썼다** — 기본 넷(주소·PID·스레드 id·시간)에 걸리는 칸이 애초에 없었다.

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `hole40.kt` | ★★★ 뷰 구멍 · `is`/`as MutableList` | `kotlinc` → `java` · `javap -c`(필터) |
| `TypeIntrinsics` · `EmptyList`(stdlib jar) | 판정이 무엇을 보나 | `javap -c`(필터) · `javap`(필터) |
| `bad40.kt` | 타입이 막는 줄 | `kotlinc`(실패가 결과) |
| `repo40.kt` · `JRepo.java` | ★★★ Java 가 고친다 · `listOf` 대 `List.of` | `kotlinc` → `javac` → `java` |
| `ops40.kt` · `ReversedViews.kt`(stdlib 소스 jar) | 연산 API — 새 리스트인가 뷰인가 | `kotlinc` → `java` · `unzip` → `grep` |
| `RoCs.cs` | C# 의 같은 구멍 | `csc` → `dotnet` |
| `borrow40.rs` | Rust 의 컴파일 거부 | `rustc`(실패가 결과) |
| `hint40.py` | Python 힌트와 `tuple` | `python3` |

**구현 의존 항목** — `listOf` 의 실제 클래스와 그 `add`/`set` 동작(§5) · `TypeIntrinsics` 판정 · `KMappedMarker` · `asReversed` 의 구현 클래스 · 진단 문구 — 이 컴파일러·stdlib 판의 산출물이다.\
반면 **「`List<E>` 에 고치는 멤버가 없다」「`List` 타입은 객체를 바꾸지 않는다(뷰)」「`List<out E>`」** 는 **언어의 계약**이다.

**★ 던져 봤더니 예상과 달랐던 것 — 세 건**

1. ★★★ **`listOf(1, 2) is MutableList` 가 `true` 였다** — 「읽기 전용 팩토리의 결과는 `MutableList` 가 아니다」라는 직관이 틀렸다. 판정기가 **Java 클래스를 못 가린다**(3번).
2. ★★ **캐스트한 `listOf(1, 2)` 의 `set` 이 원본을 바꿨다** — §5 표의 「Java 에서 `set` 성공」이 **Kotlin 안에서도** 캐스트 한 줄로 같다(2번).
3. ★ **`emptyList()` 만 캐스트에서 막혔다** — 같은 `listOf` 계열인데 원소 수에 따라 **막히는 단계**(캐스트 대 `add`)가 다르다(2번).
