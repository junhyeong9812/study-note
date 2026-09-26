# kotlin/syntax/32 — 동등성: `==`/`===`·`equals` 규약·`data class` 와의 관계 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javac`·`javap` 에서 실제로 얻었다.\
> 역어셈블은 **기본 `-jvm-target`(1.8 · `major version: 52`)** 이 정본이다.
> ★★ 아래 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적은 자리가 없다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ `A true false true` · `B true true false true true` — 참조 타입의 `==` 는 **`Intrinsics.areEqual`**, `equals` 를 안 부르는 것은 `e2`·`e4`·`e6`·`e7`

**출력**

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

**왜 그런가**

- ★★★ `e1`·`e3`·`e8` — **`invokestatic Intrinsics.areEqual`**. 그 메서드는 **`first == null ? second == null : first.equals(second)`** 한 줄이다 — 문서의 `a?.equals(b) ?: (b === null)` 그대로다.
- ★★ `equals` 를 **안 부르는** 넷 — `e2`(`Int`) **`if_icmpne`** · `e4`(`===`) **`if_acmpne`** · `e6`(`== null`) **`ifnonnull`** · `e7`(`Double`) **`dcmpg`**.
- ★ `e5`(`a.equals(b)`)는 `invokevirtual Pt.equals` 이고 **`null` 처리가 없다** — 그래서 `a` 에 `checkNotNullParameter` 가 붙었다.

### 2. ★★ Java `A false true true` · `B true` · `C NPE` / Kotlin `A true false` · `B true false` — `k1` ≈ `j3`, **`k2` = `j1`**

**출력**

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

**왜 그런가**

- ★★★ **Java 의 `==`(`j1`)와 Kotlin 의 `===`(`k2`)는 명령이 한 글자도 같다** — `if_acmpne`. 이름이 **뒤집혔다.**
- ★★ Kotlin `==`(`k1`)는 `Intrinsics.areEqual`, Java `Objects.equals`(`j3`)는 `Objects.equals` — **둘 다 `null` 을 먼저 보는 정적 메서드**다. `j2`(`a.equals(b)`)는 `a` 가 `null` 이면 **NPE**(`C` 줄).

### 3. ★★ 컴파일된다 — **경고 두 줄**(「`identity equality … is prohibited.`」) · 기본은 `A true false` · 옵션을 주면 `A true true` · `B` 는 둘 다 `true true`

**출력**

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

**왜 그런가**

- ★★★ `127` 은 `Integer.valueOf` 의 **캐시**에서 같은 상자를 받고, `128` 은 **새 상자**를 받는다. `-XX:AutoBoxCacheMax=1000` 이 캐시 상한을 올리자 `128` 도 같은 상자가 됐다 — **소스도 클래스 파일도 그대로인데** 답이 바뀌었다.
- ★ `==` 는 값 비교라 옵션과 무관하다.

### 4. ★★★ 「`set 과 list 가 갈린 칸 3 / 8`」 — `R2`·`R3` 는 **셋만** 틀리고, `R1` 은 **넣은 그 객체**로 셋은 찾고 리스트는 못 찾는다 · `R4` 는 **2 와 1** · `R5` 는 **방향에 따라 뒤집힌다**

**출력**

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

**왜 그런가**

- ★★★ **`R2`**(`hashCode` 누락) — 같은 값 둘이 **다른 칸**에 앉아 `size=2`, 새 객체는 **다른 칸을 보니** `contains(new)` 가 `false`. 리스트는 해시를 안 써서 `true`.
- ★★★ **`R3`**(넣은 뒤 변경) — `v` 를 바꾸자 해시가 바뀌어 **넣은 그 객체도** 셋에서 못 찾는다. 리스트는 찾는다.
- ★★ **`R1`**(반사성) — 셋의 `contains(k)` 가 `true` 인 것은 **`HashMap` 의 동일성 지름길**(9번) 덕이다. 리스트는 `equals` 만 부르니 `false`.
- ★★ **`R4`**(추이성) — `1,3,2` 순이면 `size=2`, `2,1,3` 순이면 `size=1`. **크기가 넣는 순서의 함수**가 됐다.
- ★★ **`R5`**(대칭성) — `HashSet.contains(x)` 는 `x.equals(원소)` 를 부르므로 **누가 인자냐**에 따라 답이 뒤집힌다. `R5(A).equals("a")` 는 `true`, `"a".equals(R5(A))` 는 `false`.
- ★ **다섯 모두 예외가 없다** — 증상은 조용한 오답뿐이다.

### 5. ★★ `A 1 first` · `B 1 first vb` — `second` 의 `note` 는 **셋에서도 맵의 키에서도 사라졌다**

**출력**

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

**왜 그런가**

- ★★★ `data class` 의 `equals`/`hashCode` 는 **주 생성자의 `id` 만** 본다([22번 주제](../22-data-class-generated-members/) (2)). 두 객체는 셋 입장에서 **같은 키**라 둘째가 들어가지 못했다.
- ★★ 맵의 `map[b] = "vb"` 는 **값만 덮고 키 객체는 `a` 그대로** 둔다 — `keys.first().note` 가 `first` 다.
- ★ 이 사고는 **규약 위반이 아니다**(두 메서드는 일관하다). 틀린 것은 「`note` 도 신원」이라는 기대다.

### 6. ★★ `A false true false` · `B true false` · `C true true` · `D false false 1` · `E true false`

**출력**

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

**왜 그런가**

- ★★★ **정적 타입이 `Double`(또는 `Double?`)이면 IEEE 754, 아니면 `equals`** — 같은 `NaN` 이 `x == x` 로는 `false`, `Any` 로 받은 `y == y` 로는 `true` 다. `-0.0` 도 거꾸로 갈린다(`B`).
- ★★ `Double?` 인 `z` 도 **`false`** — nullable 도 부동소수점 타입으로 본다.
- ★★ `E` — `data class Box(val d: Double)` 의 생성 `equals` 는 **`Double.compare`** 를 부른다(블록의 마지막 명령). 그래서 `Box(NaN) == Box(NaN)` 은 `true`, `Box(0.0) == Box(-0.0)` 은 `false` — **`equals` 쪽 규칙**이다.
- ★ `C` — 컬렉션은 `equals` 를 쓰므로 `NaN` 을 **찾는다.** `D` — 비교 기호는 IEEE(둘 다 거짓), `compareTo` 는 `NaN` 을 **가장 크게**(`1`) 본다.

### 7. **경고 0줄** — `-Wextra` 로도 · 경고가 나는 곳은 **배열의 `==`** 한 곳 · 배열을 가진 `data class` 에는 **없다**

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

- ★★★ **물은 자리 3 · 경고 1줄**(블록의 `echo` 줄) — `OnlyEq` 와 `WithArr` 는 조용하다. 방어선이 **Java 와 같은 자리**(없음)에 있다.
- ★★ 경고는 `==` 라는 **식의 자리**에만 붙었다 — 「`'==' on arrays compares only references.`」 `data class` 가 생성한 `equals` 안의 배열 비교(`B false`)에는 **아무 말이 없다.**

### 8. `HashSet` 은 **해시로 칸을 먼저 고른다** — 다른 칸이면 `equals` 가 **불리지도 않는다**

- `R2` 의 두 객체는 `equals` 로는 같지만 `Object.hashCode` 가 **다르다.** 새 객체로 `contains` 하면 셋은 **그 해시의 칸만** 보고, 거기에는 아무것도 없다.
- `ArrayList.contains` 는 해시를 안 쓰고 **원소마다 `equals`** 를 부르므로 찾는다. **두 컬렉션이 다른 답을 내는 것**이 `hashCode` 누락의 서명이다.
- 칸을 먼저 고르는 **이유**(버킷·충돌)는 [`cs/data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/)이 정본이다.

### 9. JDK `HashMap` 이 해시가 같으면 **`==`(동일성)를 먼저** 보고 맞으면 `equals` 를 건너뛴다 — **언어의 약속이 아니다** · `ArrayList` 는 그 지름길이 **없다** · 파이썬 `list` 는 **있다**

- `R1` 은 해시가 정직(`v`)하므로 `k` 로 찾으면 **같은 칸**에 가고, 거기 앉은 것이 **바로 `k`** 라 동일성 비교에서 끝난다 — `equals` 는 불리지 않는다.
- `ArrayList.contains(k)` 는 `k.equals(원소)` 만 부른다 → **`false`**.
- ★★ [Python 30번](../../../python/syntax/30-repr-eq-hash-contracts/) 동작 5 는 **`list` 의 `in` 도 정체를 먼저 본다**고 적었다. 같은 실험에서 **리스트 칸만 두 언어가 갈린다** — 지름길은 **컬렉션 구현**의 성질이다.

### 10. **구현**(JVM 의 `Integer` 캐시)이다 — 옵션 하나로 `128` 의 답이 바뀌었다 · `Int?` 는 **답이 불안정**하고, `value class` 는 **질문이 성립하지 않는다**

- ★★★ 언어가 정한 것은 「`===` 는 동일성」뿐이다. 3번의 두 번째 실행이 **같은 클래스 파일**로 다른 답을 냈으므로 경계는 **JVM 이 정한다.**
- ★★ `Int?` 는 JVM 에서 **진짜 `Integer` 객체** — 동일성이 **정의는 되지만** 답이 캐시에 달린다(경고). `value class` 는 [26번 주제](../26-value-class-and-boxing/)에서 봤듯 **상자가 자리마다 생겼다 사라지므로** 「같은 객체인가」가 **물음이 안 된다**(에러).

### 11. 막히는 것은 **`"a" == 1`** 과 **`1 == 1L`** 둘 — `Cat() == Dog()` 은 **통과**한다

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

- ★★ 「`operator '==' cannot be applied to 'String' and 'Int'.`」·「`… 'Int' and 'Long'.`」 — **내장 타입끼리의 명백한 불일치**만 막는다.
- ★★ 서로 무관한 두 `final` 클래스(`Cat`·`Dog`)는 **에러도 경고도 없이** 컴파일된다(6번째 줄이 에러 목록에 없다).

### 12. Kotlin **안 막음** · Python **런타임**(`__hash__` 가 `None`) · Rust **컴파일**(`Eq + Hash` 경계)

- ★★ Kotlin — 7번 그대로, 경고 0줄에 셋에서 `size=2`. **Java 와 같다**(`Object.hashCode` 가 그냥 남는다).
- ★ Python — `__eq__` 만 정의하면 **`__hash__` 가 꺼져** 셋에 넣는 순간 `TypeError`([30번](../../../python/syntax/30-repr-eq-hash-contracts/) 동작 2).
- ★ Rust — `HashMap` 의 키가 **타입 수준에서** `Eq + Hash` 를 요구한다([28번](../../../rust/syntax/28-partialeq-eq-partialord-ord-and-hash-contracts/)).
- ★ 셋 다 **내용이 맞는지**는 안 본다 — 짝이 있느냐만 본다. Python·Rust 칸은 **그 갈래 문서를 읽고** 옮긴 것이다.

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
| **값으로는 없다** — `hashCode()` 값을 찍지 않았다 | 출력 · `javap` 출력 · stdlib 소스 줄 |
| ★ 원리상 — 격자 `R2` 의 `size=2`(기본 해시가 **우연히 같으면** 바뀐다) | 격자의 나머지 칸과 「갈린 칸」 줄 |
| | `Int?` 의 `127`/`128` — **같은 JVM·같은 옵션**이면 |
| | 컴파일 진단의 **문구·`파일:줄:칸`·캐럿** · 모든 **종료 코드** |

> 근거 — 캡처 스크립트를 처음부터 다시 돌려 **블록 전체를 바이트 단위로 대조**했다.
>
> 실측 — `capture.sh blocks` 와 `capture.sh blocks-recheck` 를 처음부터 따로 돌려 `normalize-shaky.py` 로 대조했다 —\
> **블록 104개 · 동일 104 · 흔들린 칸 0 · ★고칠 것 0**(30\~33 네 주제를 한 캡처로 받았다). `diff -rq` 도 차이 0 이다.\
> ★ **정규화 규칙은 하나도 안 썼다** — 기본 넷(주소·PID·스레드 id·시간)에 걸리는 칸이 애초에 없었다.

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `eqforms.kt` | ★★★ `==` 여덟 모양의 번역 | `kotlinc` → `java` · `javap -c -p`(`awk` 필터) |
| (stdlib) | `Intrinsics.areEqual` 의 소스 한 줄과 바이트코드 | `unzip -p`(필터) · `javap -c -p`(필터) |
| `Eq32.java` · `eqk32.kt` | ★★★ Java `==` = Kotlin `===` | `javac`·`kotlinc` → `java` · `javap`(필터) |
| `cache.kt` | ★★ `Int?` 의 `===` — 기본 판과 **`-XX:AutoBoxCacheMax=1000`** 판 | `kotlinc`(경고) → `java` 두 판 |
| `vgrid.kt` | ★★★ **규약 위반 × 자료구조 격자** | `kotlinc` → `java` |
| `body.kt` | `data class` 본문 프로퍼티가 셋·맵에서 | `kotlinc` → `java` |
| `nan.kt` | 부동소수점과 정적 타입 · `data class` 의 `Double.compare` | `kotlinc` → `java` · `javap`(필터) |
| `eqonly.kt` | `equals` 만 재정의 · 배열 — **경고의 유무** | `kotlinc` · `kotlinc -Wextra` · 경고 줄 세기 · `java` |
| `eqbad.kt` | 호환되지 않는 `==` | `kotlinc`(실패가 결과) |
| `form32.kt` | 형태 한 벌 | `kotlinc` → `java` |

**구현 의존 항목** — `Intrinsics.areEqual`·`if_icmpne`·`dcmpg` 로의 번역, ★★ **`Integer` 캐시의 범위**, `HashMap` 의 동일성 지름길과 `ArrayList` 의 부재, `HashMap.put` 이 키 객체를 안 바꾸는 것, 경고의 유무와 문구 — 이 컴파일러·JVM·JDK 의 산출물이다.\
반면 **「`a == b` = `a?.equals(b) ?: (b === null)`」「`===` 는 동일성」「부동소수점은 정적 타입이 규칙을 고른다」** 는 **언어의 계약**이다.

**★ 던져 봤더니 예상과 달랐던 것 — 세 건**

1. ★★★ **반사성을 깬 키를 넣은 그 객체로 찾으면 셋은 찾고 리스트는 못 찾았다**(4·9번). 파이썬 형제 문서에서는 **리스트도 찾았다** — 같은 실험의 **리스트 칸만** 두 언어가 갈렸다.
2. ★★ **`Int?` 의 `===` 가 에러가 아니라 경고였다**(3번). 같은 문구(「`identity equality … is prohibited.`」)가 [26번 주제](../26-value-class-and-boxing/)의 `value class` 에서는 **에러**였다.
3. ★★ **서로 무관한 두 `final` 클래스의 `==` 가 조용히 통과했다**(11번). 막힌 것은 `String`/`Int`·`Int`/`Long` 처럼 **내장 타입끼리**뿐이었다.
