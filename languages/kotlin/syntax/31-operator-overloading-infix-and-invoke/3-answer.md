# kotlin/syntax/31 — 연산자 오버로딩·중위 함수·`invoke` 규약 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javap` 에서 실제로 얻었다.\
> 역어셈블은 **기본 `-jvm-target`(1.8 · `major version: 52`)** 이 정본이다.
> ★★ 아래 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적은 자리가 없다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 한 칸만 `V` 로 안 간다 — `s18 a == b` 는 **`Intrinsics.areEqual`** · `!in`·`<` 는 `contains`·`compareTo` 뒤의 **`ifne`·`ifge`** · `s01` 과 `s19` 는 **같다**

**출력**

```kotlin
// opgrid.kt
class V(val n: Int) {
    operator fun plus(o: V) = V(n + o.n)
    operator fun minus(o: V) = V(n - o.n)
    operator fun times(o: V) = V(n * o.n)
    operator fun div(o: V) = V(n / o.n)
    operator fun rem(o: V) = V(n % o.n)
    operator fun unaryMinus() = V(-n)
    operator fun not() = V(n.inv())
    operator fun inc() = V(n + 1)
    operator fun get(i: Int) = n + i
    operator fun set(i: Int, v: Int) { println("set $i $v") }
    operator fun invoke(x: Int) = n * x
    operator fun contains(x: Int) = x == n
    operator fun rangeTo(o: V) = n..o.n
    operator fun rangeUntil(o: V) = n..<o.n
    operator fun compareTo(o: V) = n.compareTo(o.n)
}

class Acc(var n: Int) {
    operator fun plusAssign(o: Int) { n += o }
}

fun s01(a: V, b: V) = a + b
fun s02(a: V, b: V) = a - b
fun s03(a: V, b: V) = a * b
fun s04(a: V, b: V) = a / b
fun s05(a: V, b: V) = a % b
fun s06(a: V) = -a
fun s07(a: V) = !a
fun s08(a: V): V { var x = a; x++; return x }
fun s09(a: V) = a[2]
fun s10(a: V) { a[1] = 5 }
fun s11(a: V) = a(3)
fun s12(a: V) = 4 in a
fun s13(a: V) = 4 !in a
fun s14(a: V, b: V) = a..b
fun s15(a: V, b: V) = a..<b
fun s16(a: V, b: V) = a < b
fun s17(a: Acc) { a += 2 }
fun s18(a: V, b: V) = a == b
fun s19(a: V, b: V) = a.plus(b)

fun main() {
    val a = V(6); val b = V(4)
    println("${s01(a, b).n} ${s02(a, b).n} ${s03(a, b).n} ${s04(a, b).n} ${s05(a, b).n}")
    println("${s06(a).n} ${s07(a).n} ${s08(a).n} ${s09(a)} ${s11(a)}")
    s10(a)
    println("${s12(a)} ${s13(a)} ${s14(a, b)} ${s15(b, a)} ${s16(a, b)} ${s18(a, b)}")
    val acc = Acc(1); s17(acc); println(acc.n)
}
```

```text
===== kotlinc opgrid.kt -d o31g =====
(exit 0)
===== java -cp o31g:kotlin-stdlib.jar OpgridKt =====
10 2 24 1 2
-6 -7 7 8 18
set 1 5
false true 6..4 4..5 false false
3
(exit 0)
```

```text
===== javap -c -p o31g/OpgridKt.class | python3 grid31.py opgrid.kt =====
s01  a + b                  -> V.plus
s02  a - b                  -> V.minus
s03  a * b                  -> V.times
s04  a / b                  -> V.div
s05  a % b                  -> V.rem
s06  -a                     -> V.unaryMinus
s07  !a                     -> V.not
s08  var x = a; x++; return x -> V.inc
s09  a[2]                   -> V.get
s10  a[1] = 5               -> V.set
s11  a(3)                   -> V.invoke
s12  4 in a                 -> V.contains
s13  4 !in a                -> V.contains
s14  a..b                   -> V.rangeTo
s15  a..<b                  -> V.rangeUntil
s16  a < b                  -> V.compareTo
s17  a += 2                 -> Acc.plusAssign
s18  a == b                 -> Intrinsics.areEqual
s19  a.plus(b)              -> V.plus
V·Acc 의 메서드 호출로 풀린 칸 18 / 19
(exit 0)
```

```text
===== javap -c -p o31g/OpgridKt.class | awk '/ s(01|13|16|18|19)\(/,/^$/' =====
  public static final V s01(V, V);
    Code:
       0: aload_0
       1: ldc           #9                  // String a
       3: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_1
       7: ldc           #17                 // String b
       9: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
      12: aload_0
      13: aload_1
      14: invokevirtual #23                 // Method V.plus:(LV;)LV;
      17: areturn

  public static final boolean s13(V);
    Code:
       0: aload_0
       1: ldc           #9                  // String a
       3: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_0
       7: iconst_4
       8: invokevirtual #76                 // Method V.contains:(I)Z
      11: ifne          18
      14: iconst_1
      15: goto          19
      18: iconst_0
      19: ireturn

  public static final boolean s16(V, V);
    Code:
       0: aload_0
       1: ldc           #9                  // String a
       3: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_1
       7: ldc           #17                 // String b
       9: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
      12: aload_0
      13: aload_1
      14: invokevirtual #92                 // Method V.compareTo:(LV;)I
      17: ifge          24
      20: iconst_1
      21: goto          25
      24: iconst_0
      25: ireturn

  public static final boolean s18(V, V);
    Code:
       0: aload_0
       1: ldc           #9                  // String a
       3: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_1
       7: ldc           #17                 // String b
       9: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
      12: aload_0
      13: aload_1
      14: invokestatic  #106                // Method kotlin/jvm/internal/Intrinsics.areEqual:(Ljava/lang/Object;Ljava/lang/Object;)Z
      17: ireturn

  public static final V s19(V, V);
    Code:
       0: aload_0
       1: ldc           #9                  // String a
       3: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_1
       7: ldc           #17                 // String b
       9: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
      12: aload_0
      13: aload_1
      14: invokevirtual #23                 // Method V.plus:(LV;)LV;
      17: areturn
(exit 0)
```

**왜 그런가**

- ★★★ 기호는 **정해진 이름의 메서드 호출 하나**로 번역된다 — 격자 마지막 줄 「**풀린 칸 18 / 19**」. 빠진 한 칸은 `==` 다. `==` 는 번역표에 **없고**, `null` 을 먼저 처리하는 `Intrinsics.areEqual` 로 간다([32번 주제](../32-equality-and-equals-contract/)).
- ★★ `!in` 이라는 메서드는 없다 — **`contains` 뒤 `ifne`**. `<` 도 **`compareTo` 뒤 `ifge`**. 비교 넷(`<`·`>`·`<=`·`>=`)이 `compareTo` 하나를 나눠 쓴다.
- ★★ `s01`(`a + b`)과 `s19`(`a.plus(b)`)는 **명령·오프셋이 한 글자도 같다** — 기호는 이름 호출의 **다른 표기**다.
- ★ 출력 둘째 줄의 `7` — `x++` 가 `x = x.inc()` 로 번역되어 **새 `V(7)`** 을 받았다. `inc` 는 수신자를 고치지 않는다.

### 2. ★★★ 둘 다 막힌다 — 12번째 줄은 「`ambiguity between assign operator candidates:`」 · 13번째 줄은 「`'operator' modifier is required`」

**출력**

```kotlin
// assignbad.kt
class Both(val n: Int) {
    operator fun plus(o: Int) = Both(n + o)
    operator fun plusAssign(o: Int) { println("plusAssign $o") }
}

class Bare(val n: Int) {
    fun plus(o: Int) = Bare(n + o)
}

fun main() {
    var a = Both(1)
    a += 2
    val c = Bare(1) + 4
}
```

```text
===== kotlinc assignbad.kt -d o31b =====
assignbad.kt:12:7: error: ambiguity between assign operator candidates:
fun plus(o: Int): Both
fun plusAssign(o: Int): Unit
    a += 2
      ^^
assignbad.kt:13:21: error: 'operator' modifier is required on 'fun plus(o: Int): Bare' defined in 'Bare'.
    val c = Bare(1) + 4
                    ^
(exit 1)
```

**왜 그런가**

- ★★★ `var a: Both` 에서 `a += 2` 는 **두 갈래가 다 선다** — `a.plusAssign(2)` 도 되고, `a = a.plus(2)` 도 된다(`plus` 의 반환이 `Both`). 컴파일러는 **고르지 않고** 후보 둘을 전문으로 댄다.
- ★ `Bare.plus` 에는 `operator` 가 없다 — 이름만으로는 번역하지 않는다.

### 3. ★★ 통과 — `A plusAssign 3` · `B [1, 2] [1, 2] true` · `C [1, 2] [1] false`

**출력**

```kotlin
// assignok.kt
class Both(val n: Int) {
    operator fun plus(o: Int) = Both(n + o)
    operator fun plusAssign(o: Int) { println("A plusAssign $o") }
}

fun main() {
    val b = Both(1)
    b += 3
    var ml = mutableListOf(1)
    val m0 = ml
    ml += 2
    println("B $ml $m0 ${ml === m0}")
    var rl: List<Int> = listOf(1)
    val r0 = rl
    rl += 2
    println("C $rl $r0 ${rl === r0}")
}
```

```text
===== kotlinc assignok.kt -d o31a =====
(exit 0)
===== java -cp o31a:kotlin-stdlib.jar AssignokKt =====
A plusAssign 3
B [1, 2] [1, 2] true
C [1, 2] [1] false
(exit 0)
```

```text
===== javap -c -p o31a/AssignokKt.class | grep -E 'Both\.plus|Collection\.add|CollectionsKt\.plus' =====
      11: invokevirtual #15                 // Method Both.plusAssign:(I)V
      41: invokeinterface #33,  2           // InterfaceMethod java/util/Collection.add:(Ljava/lang/Object;)Z
     119: invokestatic  #76                 // Method kotlin/collections/CollectionsKt.plus:(Ljava/util/Collection;Ljava/lang/Object;)Ljava/util/List;
(exit 0)
```

**왜 그런가**

- ★★★ **좌변의 선언 타입이 갈래를 고른다.** `val b` 는 재대입이 안 되니 `plusAssign` 뿐 · `var ml: MutableList<Int>` 는 `plus` 가 **`List`** 를 돌려줘 좌변에 **못 들어가니** `plusAssign`(→ `Collection.add` 인라인) · `var rl: List<Int>` 는 `plusAssign` 이 **없으니** `rl = rl + 2`(→ `CollectionsKt.plus`).
- ★★ 그래서 `B` 는 **같은 객체를 고쳤고**(`true`), `C` 는 **새 리스트를 재대입**했다(`false`, 옛 참조 `r0` 는 `[1]` 그대로).
- ★ 출력의 **앞 두 칸만 보면 `B`·`C` 가 같다** — `===` 를 물어야 갈린다.

### 4. ★★ 둘 다 막힌다 — 「`must override 'equals()' in Any.`」 · 「`must be a member function.`」

**출력**

```kotlin
// eqop.kt
class Q(val n: Int) {
    operator fun equals(other: Q): Boolean = n == other.n
}

operator fun Q.equals(other: Any?): Boolean = true
```

```text
===== kotlinc eqop.kt -d o31q =====
eqop.kt:2:5: error: 'operator' modifier is not applicable to function: must override 'equals()' in Any.
    operator fun equals(other: Q): Boolean = n == other.n
    ^^^^^^^^
eqop.kt:5:1: error: 'operator' modifier is not applicable to function: must be a member function.
operator fun Q.equals(other: Any?): Boolean = true
^^^^^^^^
(exit 1)
```

**왜 그런가**

- ★★★ `==` 는 **오버로드 대상이 아니다.** 참가하는 길은 **`override fun equals(other: Any?)`** 하나뿐이다 — 타입별 `equals(Q)` 는 도장을 받을 수 없다.
- ★ 확장으로도 못 바꾼다 — 남의 타입의 `==` 는 그 타입의 **멤버** `equals` 가 정한다.

### 5. ★★ `A ababab` · `B xy` · `C a=Bag[p, q] b=Bag[p, q] true` · `D price=Money(100) total=Money(150)` · `E false true [abcd]` — 경고 **0줄** · `times` 는 **`invokestatic`**

**출력**

```kotlin
// ext31.kt
operator fun String.times(k: Int): String = repeat(k)
operator fun StringBuilder.plusAssign(s: String) { append(s) }

class Money(val cents: Long) {
    operator fun plus(o: Money) = Money(cents + o.cents)
    override fun toString() = "Money($cents)"
}

class Bag(val items: MutableList<String>) {
    operator fun plus(s: String): Bag { items.add(s); return this }
    override fun toString() = "Bag$items"
}

fun main() {
    println("A " + "ab" * 3)
    val sb = StringBuilder("x"); sb += "y"; println("B $sb")
    val a = Bag(mutableListOf("p"))
    val b = a + "q"
    println("C a=$a b=$b ${a === b}")
    val price = Money(100)
    val total = price + Money(50)
    println("D price=$price total=$total")
    more()
}

class Check(private val min: Int) {
    operator fun invoke(s: String) = s.length >= min
}

fun more() {
    val longEnough = Check(3)
    println("E ${longEnough("ab")} ${longEnough("abc")} ${listOf("a", "abcd").filter(longEnough::invoke)}")
}
```

```text
===== kotlinc ext31.kt -d o31e =====
(exit 0)
===== java -cp o31e:kotlin-stdlib.jar Ext31Kt =====
A ababab
B xy
C a=Bag[p, q] b=Bag[p, q] true
D price=Money(100) total=Money(150)
E false true [abcd]
(exit 0)
```

```text
===== javap -c -p o31e/Ext31Kt.class | grep -E 'Method (times|plusAssign|Bag\.plus|Money\.plus|Check\.invoke)' =====
      15: invokestatic  #50                 // Method times:(Ljava/lang/String;I)Ljava/lang/String;
      44: invokestatic  #75                 // Method plusAssign:(Ljava/lang/StringBuilder;Ljava/lang/String;)V
      98: invokevirtual #101                // Method Bag.plus:(Ljava/lang/String;)LBag;
     177: invokevirtual #123                // Method Money.plus:(LMoney;)LMoney;
      24: invokevirtual #148                // Method Check.invoke:(Ljava/lang/String;)Z
      38: invokevirtual #148                // Method Check.invoke:(Ljava/lang/String;)Z
     133: invokevirtual #148                // Method Check.invoke:(Ljava/lang/String;)Z
(exit 0)
```

**왜 그런가**

- ★★★ `C` — `Bag.plus` 가 **수신자를 고치고 자기를 돌려준다.** `val b = a + "q"` 가 `a` 를 바꿨다. 컴파일러는 **침묵**한다 — 규약이 보는 것은 **이름과 `operator`** 뿐이다.
- ★★ `String.times`·`StringBuilder.plusAssign` 은 **확장**이라 `invokestatic`, `Bag.plus`·`Money.plus`·`Check.invoke` 는 **멤버**라 `invokevirtual` 이다.
- ★ `E` — `invoke` 로 객체를 **함수처럼** 부르고, `longEnough::invoke` 로 **함수 참조**로도 넘겼다.

### 6. 흔한 이름이 **뜻하지 않게** 기호가 되는 것을 막는 도장이다

- `plus`·`get`·`contains` 는 **기호와 무관하게** 지을 수 있는 이름이다. 도장 없이 번역하면 **그 기호의 뜻을 따를 생각이 없던 메서드**가 `+`·`[]`·`in` 이 된다.
- ★ `operator` 는 「이 함수는 이 기호의 **뜻**을 따른다」는 선언이다 — [30번 주제](../30-destructuring-declarations-and-componentn/)의 `component1` 도 같은 문구로 막혔다.

### 7. **둘 다 있고 · 좌변이 `var` 이고 · `plus` 의 반환이 좌변 타입의 하위 타입** — `MutableList` 는 셋째 조건이 **거짓**이다

- `var ml: MutableList<Int>` 에서 `ml + 2` 는 **`List<Int>`** 를 돌려준다. `List<Int>` 는 `MutableList<Int>` 가 **아니므로** `ml = ml + 2` 갈래가 **서지 않는다** — 남은 `plusAssign` 으로 정해진다(3번).
- ★★ 「`var MutableList` 의 `+=` 는 모호하다」는 설명이 **이 판에서는 틀렸다.** 규칙에 그대로 맞는 `Both`(2번)만 모호했다.

### 8. **못 쓴다** — 보인 것은 「기호 호출 = 같은 이름의 메서드 호출 하나」까지다

- ★★ 이 문서는 **시간을 안 쟀다.** 보인 것은 `s01`(`a + b`)과 `s19`(`a.plus(b)`)가 **바이트코드째 같다**는 것이다(1번).
- ★ 「잴 것이 없다」(제4의 상태) — 기호를 쓴 코드와 이름을 쓴 코드는 **같은 클래스 파일**이 되므로 비교할 두 대상이 **애초에 하나**다. 그 메서드 **본문의 비용**은 기호와 무관하게 그 본문의 것이다.

### 9. **아니다** — `infix` 는 호출 **형태**다 · `1 shl 2 + 3` 은 **32** · 정본은 [09번 주제](../09-varargs-spread-local-and-infix-functions/) (9)

```kotlin
// form31.kt
data class Vec(val x: Int, val y: Int) {
    operator fun plus(o: Vec) = Vec(x + o.x, y + o.y)
    operator fun unaryMinus() = Vec(-x, -y)
    operator fun get(i: Int) = if (i == 0) x else y
}

infix fun Vec.dot(o: Vec) = x * o.x + y * o.y

fun main() {
    val a = Vec(1, 2)
    val b = Vec(3, 4)
    println("Z ${a + b} ${-a} ${a[1]} ${a dot b}")
}
```

```text
===== kotlinc form31.kt -d o31z =====
(exit 0)
===== java -cp o31z:kotlin-stdlib.jar Form31Kt =====
Z Vec(x=4, y=6) Vec(x=-1, y=-2) 2 11
(exit 0)
```

- `a dot b` 는 `a.dot(b)` 를 **괄호 없이** 쓴 것일 뿐, 번역표(1번)의 기호가 아니다. `operator` 도 필요 없다.
- ★ 중위 호출은 **산술보다 낮고 비교보다 높다** — `1 shl 2 + 3` 은 `1 shl (2 + 3)`. 이 값은 09번이 실행으로 재 두었고 **여기서는 다시 재지 않았다.**

### 10. Rust 의 `Add::add` 는 **`self` 를 값으로 받아** 옮긴다 · Kotlin 은 **참조를 넘긴다** · 남의 타입은 Kotlin **확장 연산자** 대 Rust **고아 규칙**

- ★★ Rust 30번 (1) — `a + b` 는 `a.add(b)` 이고 `add(self, …)` 가 **소유권을 가져간다.** `Copy` 가 아니면 `a` 를 다시 못 쓴다. Kotlin 의 `plus` 는 JVM 참조를 넘길 뿐이라 `a` 가 **그대로 남는다**(5번의 `price`).
- ★ 대신 Kotlin 은 `plus` 가 **수신자를 고치는 것**을 막지 못한다(5번의 `Bag`) — Rust 는 `&mut` 이 없으면 고칠 수 없다.
- ★ 남의 타입 — Kotlin 은 `operator fun String.times` 처럼 **확장**으로 단다(5번 `A`). Rust 는 **트레이트와 타입 중 하나는 내 것**이어야 한다(고아 규칙). 이 칸의 Rust 쪽은 **그 갈래 문서를 읽고** 옮긴 것이다.

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
===== javap -version =====
21.0.5
(exit 0)
```

★ **흔들리는 칸과 안 흔들리는 칸**

| 흔들린다 | 안 흔들린다 |
|---|---|
| **없다** — 해시코드·주소·시간을 찍지 않았다 | 출력 · `javap` 출력 · ★ 격자 스크립트의 출력과 「풀린 칸」 줄 |
| | 컴파일 진단의 **문구·`파일:줄:칸`·캐럿** |
| | 모든 **종료 코드** |

> 근거 — 캡처 스크립트를 처음부터 다시 돌려 **블록 전체를 바이트 단위로 대조**했다.
>
> 실측 — `capture.sh blocks` 와 `capture.sh blocks-recheck` 를 처음부터 따로 돌려 `normalize-shaky.py` 로 대조했다 —\
> **블록 104개 · 동일 104 · 흔들린 칸 0 · ★고칠 것 0**(30\~33 네 주제를 한 캡처로 받았다). `diff -rq` 도 차이 0 이다.\
> ★ **정규화 규칙은 하나도 안 썼다** — 기본 넷(주소·PID·스레드 id·시간)에 걸리는 칸이 애초에 없었다.

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `opgrid.kt` + `grid31.py` | ★★★ **이름 → 기호 격자** 19칸 · `!in`·`<`·`==` 의 명령 · 기호 대 이름 호출 | `kotlinc` → `java` · `javap -c -p`(격자 스크립트 · `awk` 필터) |
| `assignbad.kt` | ★★ `+=` **모호성** · `operator` 누락 | `kotlinc`(실패가 결과) |
| `assignok.kt` | `+=` 세 좌변 — 제자리 대 재대입 | `kotlinc` → `java` · `javap`(필터) |
| `eqop.kt` | `equals` 에 `operator` — 멤버·확장 | `kotlinc`(실패가 결과) |
| `ext31.kt` | 확장 연산자 · `invoke` · 수신자를 고치는 `plus` | `kotlinc` → `java` · `javap`(필터) |
| `form31.kt` | 형태 한 벌(`operator` 셋 + `infix`) | `kotlinc` → `java` |

**구현 의존 항목** — 기호가 `invokevirtual` 하나로 내려가는 것, `ifne`/`ifge` 가 붙는 것, 확장 연산자가 `invokestatic` 인 것, `MutableList` 의 `+=` 가 `Collection.add` 로 인라인되는 것, 진단 문구 — 이 컴파일러·판의 산출물이다.\
반면 **「기호 → 이름 대응표」「`operator` 요구」「`+=` 모호성 규칙의 세 조건」「`==` 는 `equals` 재정의뿐」** 은 **언어의 계약**이다.

**★ 던져 봤더니 예상과 달랐던 것 — 두 건**

1. ★★★ **`var` 인 `MutableList` 의 `+=` 가 모호하지 않았다**(3·7번). 흔한 설명을 그대로 확인하려 던졌는데 `Collection.add` 로 **조용히 정해졌다.** 문서의 셋째 조건(「`plus` 의 반환이 좌변 타입의 하위 타입」)을 적용하면 **그렇게 되는 것이 맞다** — 모호성은 `Both` 처럼 **`plus` 가 자기 타입을 돌려줄 때**만 난다.
2. ★ **`==` 가 격자에서 유일하게 `V` 로 가지 않았다**(1번). `V` 는 `equals` 를 재정의하지 않았는데도 `V.equals` 가 아니라 `Intrinsics.areEqual` 이 불렸다 — `==` 는 **타입을 보고 번역하는 기호가 아니라 `null` 처리가 붙은 고정 번역**이다.
