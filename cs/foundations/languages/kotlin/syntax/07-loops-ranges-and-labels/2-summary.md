# kotlin/syntax/07 — 반복문·`range`·progression·라벨·비지역 `break`/`continue` (2.2+) — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Conditions and loops](https://kotlinlang.org/docs/control-flow.html) · [Ranges and progressions](https://kotlinlang.org/docs/ranges.html) · [Returns and jumps](https://kotlinlang.org/docs/returns.html) · [언어 기능·제안 상태표](https://kotlinlang.org/docs/kotlin-language-features-and-proposals.html).
> **실행 검증** — 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javap` 에서 실제로 얻었다.\
> `kotlinc` 12회 · `java` 2회 · `javap` 2회. 컴파일 실패 시나리오 4벌.
> ⚠️ **`-jvm-target` 을 밝히지 않은 바이트코드 주장은 반쪽이다.** 이 문서의 역어셈블은 **기본값 1.8**(`major version: 52`)이다.
> **버전** — `for`/`while`/라벨은 1.0. **`..<`(rangeUntil)는 1.7.20 도입 · 1.8.0 Stable**(stdlib 의 open-ended range API 는 1.9.0).\
> **비지역 `break`/`continue` 는 2.2.0** — 이 환경에서 `-language-version 2.1` 이 **거부하는 것을 실측**했다.\
> ★ **못 잰 것** — kotlinc 2.4.20 은 `-language-version 1.9` 이하를 거부하므로 **`..<` 의 도입 경계는 이 환경에서 못 쟀다.**\
> 그 값(1.7.20 도입 / 1.8.0 Stable)은 **공식 릴리스 노트를 열어 확인한 것**이지 실측이 아니다.
> **경계** — 비지역 `return` 이 **왜 인라인 람다에서만 되는가**의 정본은 [목록의 **11번 주제**](../11-inline-functions/)(인라인 함수)다.\
> 여기서는 **현상까지만** 쓰고 원리는 넘긴다. 컬렉션 연산(`forEach`·`map`)의 계약은 목록의 **40번 주제**부터가 정본이다.\
> **Java 쪽 정본은 [`../../../java/syntax/20-control-flow-statements/`](../../../java/syntax/20-control-flow-statements/)** 다.
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**Kotlin 의 `for` 는 「숫자를 세는 문법」이 아니라 「`iterator()` 를 가진 것이면 뭐든 도는 문법」이다.**

그런데 `1..10` 같은 **숫자 범위만은 컴파일러가 특별히 알아본다.**\
`Iterator` 객체를 만드는 대신 **Java 의 `for (int i = 1; i <= 10; i++)` 과 한 글자도 다르지 않은 바이트코드**로 편다.

> **규약(convention)** — "이 이름의 함수가 있으면 이 문법이 동작한다" 는 약속.\
> 예: `iterator()` 라는 이름의 연산자 함수가 있으면 그 타입은 `for` 에 넣을 수 있다.

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| "번호표를 뽑아 한 장씩 부른다" | `for (x in c)` — `iterator()` 규약 |
| "그냥 1부터 10까지 센다" | `for (i in 1..10)` — 컴파일러가 세는 코드로 편다 |
| 눈금이 있는 자 | `IntRange` — 시작·끝 |
| 눈금 간격이 있는 자 | `IntProgression` — 시작·끝·**간격** |
| 자를 손에 들면 무거워진다 | `IntRange` 를 **변수에 담으면** 객체가 생긴다 |
| 방 하나 나가기 / 건물 나가기 | `break` / `break@라벨` |
| 이 방만 건너뛰기 | `continue` / `return@forEach` |
| 건물 자체를 나가기 | 비지역 `return` (인라인 람다에서만) |

```text
   for (i in 1..10)           for (x in 리스트)
   ┌──────────────────┐        ┌──────────────────────┐
   │ i = 1            │        │ it = 리스트.iterator()│
   │ while (i <= 10)  │        │ while (it.hasNext()) │
   │   … ; i++        │        │   x = it.next(); …   │
   └──────────────────┘        └──────────────────────┘
     객체 0개                    Iterator 객체 1개
```

**똑같은 구조로** 두 `for` 가 컴파일된다 — 소스는 같은 모양인데 **나오는 코드가 다르다.**

## 이 주제가 답하려는 질문

1. `for (i in 1..10)` 이 **`Iterator` 를 만드는가** — 안 만든다면 무엇이 되고, **언제 만드는가.**
2. `until`·`downTo`·`step`·`..<` 이 만드는 것은 **같은 타입인가** — `last` 는 내가 적은 끝값인가.
3. 람다 안에서 **루프를 어떻게 빠져나가는가** — `break` 는 되는가, `return` 은 어디로 돌아가는가.

## 동작 방식

### (1) ★★ `for (i in 1..10)` 은 `Iterator` 를 안 만든다 — **객체가 0개**다

**언제 쓰나** — "Kotlin 의 range 는 객체라 느리다" 는 말을 검증할 때.

```kotlin
fun literal(): Int {
    var s = 0
    for (i in 1..10) s += i
    return s
}
```

**출력** (`javap -c -p out/IcodeKt.class`)

```text
  public static final int literal();
    Code:
       0: iconst_0
       1: istore_0
       2: iconst_1
       3: istore_1
       4: iload_1
       5: bipush        11
       7: if_icmpge     20
      10: iload_0
      11: iload_1
      12: iadd
      13: istore_0
      14: iinc          1, 1
      17: goto          4
      20: iload_0
      21: ireturn
```

```text
   소스                          바이트코드
   for (i in 1..10)      ──>     i = 1
       s += i                    while (i < 11) { s += i; i++ }

   new IntRange(1,10)    ──>     (없다)
   .iterator()           ──>     (없다)
   .hasNext() / .next()  ──>     (없다)
```

그림 해설:

- ★ **`IntRange` 도 `Iterator` 도 안 만들어진다.** `iconst_1`·`iinc`·`if_icmpge` 뿐이다.
- 끝값 비교가 **`bipush 11`** 이다 — 컴파일러가 `10 + 1` 을 **컴파일 시점에 계산해 넣었다.**
- 그래서 `for (i in 1..10)` 은 Java 의 `for (int i = 1; i <= 10; i++)` 과 **비용이 같다.**\
  범위 문법이 `Iterator` 를 만든다는 말은 이 형태에서는 **거짓**이다.

**그런데 끝값이 `Int.MAX_VALUE` 면 모양이 달라진다.**

```kotlin
fun toMax(): Int {
    var c = 0
    for (i in Int.MAX_VALUE - 2..Int.MAX_VALUE) c++
    return c
}
```

**출력** (`javap -c -p out2/Icode2Kt.class`)

```text
  public static final int toMax();
    Code:
       0: iconst_0
       1: istore_0
       2: ldc           #7                  // int 2147483645
       4: istore_1
       5: iinc          0, 1
       8: iload_1
       9: ldc           #8                  // int 2147483647
      11: if_icmpeq     20
      14: iinc          1, 1
      17: goto          5
      20: iload_0
      21: ireturn
```

- ★ **`if_icmpge last+1` 을 못 쓰니까 `if_icmpeq last` 로 바꾸고 검사를 몸통 뒤로 옮겼다.**\
  `MAX_VALUE + 1` 은 음수로 넘쳐서 루프가 아예 안 돌게 되기 때문이다.
- 즉 **컴파일러는 오버플로를 알고 형태를 바꾼다.** 이것은 언어 보장이 아니라 **컴파일러가 해 주는 일**이다.

비용 — 객체 0. 비교 한 번 + 증가 한 번.

### (2) ★★ 같은 범위를 **변수에 담으면** 달라진다 — 그래도 `Iterator` 는 안 생긴다

**언제 쓰나** — `val r = 1..10` 처럼 범위를 이름 붙여 쓸 때.

```kotlin
fun inVariable(): Int {
    val r = 1..10
    var s = 0
    for (i in r) s += i
    return s
}
```

**출력** (`javap -c -p out/IcodeKt.class`)

```text
  public static final int inVariable();
    Code:
       0: new           #12                 // class kotlin/ranges/IntRange
       3: dup
       4: iconst_1
       5: bipush        10
       7: invokespecial #16                 // Method kotlin/ranges/IntRange."<init>":(II)V
      10: astore_0
      11: iconst_0
      12: istore_1
      13: aload_0
      14: invokevirtual #19                 // Method kotlin/ranges/IntRange.getFirst:()I
      17: istore_2
      18: aload_0
      19: invokevirtual #22                 // Method kotlin/ranges/IntRange.getLast:()I
      22: istore_3
      23: iload_2
      24: iload_3
      25: if_icmpgt     43
      28: iload_1
      29: iload_2
      30: iadd
      31: istore_1
      32: iload_2
      33: iload_3
      34: if_icmpeq     43
      37: iinc          2, 1
      40: goto          28
      43: iload_1
      44: ireturn
```

```text
   for (i in 1..10)                for (i in r)   ← r: IntRange
   +----------------------+        +--------------------------------+
   | 객체 0개             |        | new IntRange  ← 객체 1개       |
   | bipush 11 로 비교    |        | getFirst() / getLast() 를 읽고 |
   |                      |        | 그 뒤로는 똑같이 센다           |
   +----------------------+        +--------------------------------+
        iterator() 없음                  iterator() 여전히 없음 ★
```

- ★ **`IntRange` 객체는 생겼는데 `iterator()` 는 여전히 안 불린다.**\
  컴파일러가 **`getFirst()`·`getLast()` 만 읽어 내고** 그 뒤는 (1)과 같은 세는 루프다.
- 검사 형태가 (1)과 다르다 — **`if_icmpgt` 로 빈 범위를 먼저 걸러 내고**, 몸통 뒤에서 `if_icmpeq` 로 끝을 본다.\
  `last` 가 `Int.MAX_VALUE` 일 수 있으므로 (1)의 `toMax` 와 같은 대비다.
- **`indices` 는 아예 객체조차 안 만든다.**

**출력** (`javap -c -p out/IcodeKt.class`)

```text
  public static final int overIndices(java.util.List<java.lang.Integer>);
    Code:
       0: aload_0
       1: ldc           #40                 // String xs
       3: invokestatic  #46                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: iconst_0
       7: istore_1
       8: iconst_0
       9: istore_2
      10: aload_0
      11: checkcast     #72                 // class java/util/Collection
      14: invokeinterface #75,  1           // InterfaceMethod java/util/Collection.size:()I
      19: istore_3
      20: iload_2
      21: iload_3
      22: if_icmpge     47
      25: iload_1
      26: aload_0
      27: iload_2
      28: invokeinterface #79,  2           // InterfaceMethod java/util/List.get:(I)Ljava/lang/Object;
      33: checkcast     #64                 // class java/lang/Number
      36: invokevirtual #67                 // Method java/lang/Number.intValue:()I
      39: iadd
      40: istore_1
      41: iinc          2, 1
      44: goto          20
      47: iload_1
      48: ireturn
```

- `xs.indices` 가 만들 법한 `IntRange` 가 **없다.** `size()` 를 한 번 읽고 그대로 센다.

비용 — 변수에 담으면 객체 하나. 그 외에는 (1)과 같다.

### (3) `step` 은 stdlib 함수를 한 번 부른다 — `downTo`·`until`·`..<` 는 안 부른다

**언제 쓰나** — 네 형태의 비용이 같은지 물을 때.

**출력** (`javap -c -p out/IcodeKt.class` — `for (i in 1..10 step 2)`)

```text
  public static final int withStep();
    Code:
       0: iconst_0
       1: istore_0
       2: iconst_1
       3: istore_1
       4: iconst_1
       5: bipush        10
       7: iconst_2
       8: invokestatic  #31                 // Method kotlin/internal/ProgressionUtilKt.getProgressionLastElement:(III)I
      11: istore_2
      12: iload_1
      13: iload_2
      14: if_icmpgt     32
      17: iload_0
      18: iload_1
      19: iadd
      20: istore_0
      21: iload_1
      22: iload_2
      23: if_icmpeq     32
      26: iinc          1, 2
      29: goto          17
      32: iload_0
      33: ireturn
```

**출력** (같은 파일 — `for (i in 10 downTo 1)`)

```text
  public static final int downTo();
    Code:
       0: iconst_0
       1: istore_0
       2: bipush        10
       4: istore_1
       5: iconst_0
       6: iload_1
       7: if_icmpge     20
      10: iload_0
      11: iload_1
      12: iadd
      13: istore_0
      14: iinc          1, -1
      17: goto          5
      20: iload_0
      21: ireturn
```

**출력** (같은 파일 — `for (i in 0 until 10)` 과 `for (i in 0..<10)`)

```text
  public static final int until();
    Code:
       0: iconst_0
       1: istore_0
       2: iconst_0
       3: istore_1
       4: iload_1
       5: bipush        10
       7: if_icmpge     20
      10: iload_0
      11: iload_1
      12: iadd
      13: istore_0
      14: iinc          1, 1
      17: goto          4
      20: iload_0
      21: ireturn

  public static final int rangeUntil();
    Code:
       0: iconst_0
       1: istore_0
       2: iconst_0
       3: istore_1
       4: iload_1
       5: bipush        10
       7: if_icmpge     20
      10: iload_0
      11: iload_1
      12: iadd
      13: istore_0
      14: iinc          1, 1
      17: goto          4
      20: iload_0
      21: ireturn
```

```text
   1..10        ──> iinc +1,  끝값을 컴파일러가 계산
   0 until 10   ──> iinc +1,  위와 명령이 같다
   0..<10       ──> iinc +1,  until 과 바이트 단위로 같다 ★
   10 downTo 1  ──> iinc -1,  객체 없음
   1..10 step 2 ──> getProgressionLastElement() 한 번 + iinc +2 ★
```

- ★ **`until` 과 `..<` 은 명령이 한 글자도 다르지 않다.** 같은 것의 다른 표기다.
- ★ **`step` 만 stdlib 호출이 하나 생긴다** — `ProgressionUtilKt.getProgressionLastElement(first, last, step)`.\
  왜냐면 **실제로 도달하는 마지막 값이 내가 적은 끝값이 아닐 수 있기** 때문이다((4)).
- `downTo` 는 `iinc 1, -1` 뿐이다 — 내려가는 것도 공짜다.

비용 — `step` 만 함수 호출 한 번. 나머지는 0.

### (4) ★ `step` 이 붙으면 `last` 가 **내가 적은 끝값이 아니다**

**언제 쓰나** — `progression` 의 `last` 를 상한으로 착각할 때.

**출력** (`ex2.kt`)

```text
--- progression 의 last 는 상한이 아니다 ---
1..9 step 3 = [1, 4, 7]   first=1 last=7 step=3
1..10 step 3 = [1, 4, 7, 10]  first=1 last=10 step=3
(1..9 step 3) == (1..10 step 3) ? false
```

```text
   1..9 step 3        1 ──3──> 4 ──3──> 7 ──✗──> 10 은 9 를 넘는다
                      last = 7   (내가 적은 9 가 아니다)

   1..10 step 3       1 ──3──> 4 ──3──> 7 ──3──> 10
                      last = 10  (딱 맞았다)
```

- ★ **`last` 는 「실제로 도달하는 마지막 값」이다.** (3)의 `getProgressionLastElement` 가 그것을 계산한다.
- `step` 은 **항상 양수**여야 한다 — `downTo` 에서도 그렇다.

**출력** (`ex2.kt`)

```text
--- step 에 0 이나 음수를 주면 ---
IllegalArgumentException: Step must be positive, was: 0.
IllegalArgumentException: Step must be positive, was: -1.
--- downTo 에 step 은 양수다 ---
(9 downTo 1 step 3) = [9, 6, 3]
```

- **빈 범위는 예외가 아니다 — 그냥 0회 돈다.**

**출력** (`ex2.kt`)

```text
--- 빈 범위 ---
(5..1).isEmpty()=true  (1 until 1).isEmpty()=true  (1 downTo 5).isEmpty()=true
for (i in 5..1) 의 반복 횟수 = 0
```

- ★ **`for (i in 5..1)` 은 에러가 아니라 0회다.** 거꾸로 돌고 싶으면 `downTo` 를 써야 한다 —\
  **조용히 아무 일도 안 일어나는** 자리라 눈으로는 안 잡힌다.

**타입도 갈린다.**

**출력** (`ex.kt`)

```text
타입 — (1..5)=IntRange, (1..10 step 3)=IntProgression, (1 until 5)=IntRange
```

- `step` 을 붙이면 **`IntRange` 가 아니라 `IntProgression`** 이 된다. `IntRange` 는 `IntProgression` 의 하위 타입이다.
- `..<` 과 `until` 은 **둘 다 `IntRange`** 다(끝값이 하나 작을 뿐이다).

비용 — 0. 전부 값의 성질이다.

### (5) `for` 는 `iterator()` **규약**으로 돈다 — 없으면 컴파일이 거부한다

**언제 쓰나** — 내가 만든 타입을 `for` 에 넣고 싶을 때.

```kotlin
class Countdown(val from: Int) {
    operator fun iterator(): Iterator<Int> = object : Iterator<Int> {
        var cur = from
        override fun hasNext() = cur > 0
        override fun next() = cur--
    }
}
fun custom(c: Countdown): Int { var s = 0; for (x in c) s += x; return s }
```

**출력** (`javap -c -p out2/Icode2Kt.class`)

```text
  public static final int custom(Countdown);
    Code:
       0: aload_0
       1: ldc           #15                 // String c
       3: invokestatic  #21                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: iconst_0
       7: istore_1
       8: aload_0
       9: invokevirtual #27                 // Method Countdown.iterator:()Ljava/util/Iterator;
      12: astore_2
      13: aload_2
      14: invokeinterface #33,  1           // InterfaceMethod java/util/Iterator.hasNext:()Z
      19: ifeq          42
      22: aload_2
      23: invokeinterface #37,  1           // InterfaceMethod java/util/Iterator.next:()Ljava/lang/Object;
      28: checkcast     #39                 // class java/lang/Number
      31: invokevirtual #42                 // Method java/lang/Number.intValue:()I
      34: istore_3
      35: iload_1
      36: iload_3
      37: iadd
      38: istore_1
      39: goto          13
      42: iload_1
      43: ireturn
```

```text
   for (x in c)
        │
        ├─ c.iterator()      ← operator fun 이름이 정확히 이것이어야 한다
        │
        └─ while (it.hasNext()) { x = it.next(); … }
```

- **Kotlin 의 `Iterator` 가 바이트코드에서는 `java.util.Iterator` 다.** 같은 인터페이스에 매핑된다.
- `iterator()` 가 없으면 **컴파일이 거부한다.**

**출력** (`kotlinc badf.kt` — 실수 범위를 `for` 에 넣은 것)

```text
badf.kt:1:21: error: for-loop range must have an 'iterator()' method.
fun f() { for (x in 1.0..2.0) println(x) }
                    ^^^^^^^^
```

- ★ **`1.0..2.0` 은 만들어지지만 `for` 에는 못 넣는다.** `in` 검사는 되는데 순회가 안 된다.

**출력** (`ex2.kt`)

```text
--- 실수 범위는 for 가 안 된다 ---
1.0..2.0 의 타입 = ClosedDoubleRange, 1.5 in 1.0..2.0 = true
```

- 규약 이름만 짚고 넘어간다 — **연산자 오버로딩 전체의 정본은 목록의 31번 주제**다.
- `String`·`IntArray` 는 `Iterator` 없이 **인덱스로 편다**(`charAt`·`iaload`) — 아래 표에 정리했다.

| `for` 대상 | 무엇이 되나 | 객체 |
|---|---|---|
| `1..10` 리터럴 | `iinc` 세는 루프 | 0 |
| `IntRange` 변수 | `getFirst`/`getLast` + 세는 루프 | `IntRange` 1개 |
| `xs.indices` | `size()` + 세는 루프 | 0 |
| `List<T>` | `java.util.Iterator` | `Iterator` 1개 |
| `String` | `length()` + `charAt(i)` | 0 |
| `IntArray` | `arraylength` + `iaload` | 0 |
| 내 타입 + `operator fun iterator()` | 그 `iterator()` 호출 | 그 구현이 만드는 것 |

비용 — 표의 오른쪽 칸 그대로.

### (6) 인덱스가 필요할 때 — `indices`·`withIndex`·`repeat`

**언제 쓰나** — Java 의 `for (int i = 0; i < n; i++)` 을 옮길 때.

**출력** (`ex.kt`)

```text
=== 2. 인덱스 ===
indices = [0, 1, 2]
[0]=가 [1]=나 [2]=다 
(0,가) (1,나) (2,다) 
lastIndex=2
repeat#0 repeat#1 repeat#2 
```

```text
   for (i in xs.indices)       i 만 필요할 때
   for ((i, v) in xs.withIndex())   i 와 v 가 둘 다 필요할 때
   repeat(3) { … }             i 가 필요 없고 횟수만 필요할 때 (it 로 받을 수는 있다)
```

- `withIndex()` 는 **구조 분해**로 받는다 — `(i, v)`. 구조 분해의 정본은 목록의 **30번 주제**다.
- `repeat(n) { }` 은 **stdlib 의 인라인 함수**다. 문법이 아니다.
- `Map` 도 구조 분해로 돈다.

**출력** (`ex2.kt`)

```text
--- Map 순회와 구조 분해 ---
가=1 나=2 
```

비용 — `indices` 는 0(위 (2)), `withIndex` 는 항목마다 `IndexedValue` 하나.

### (7) 라벨 — `break` 가 나가는 범위를 이름으로 정한다

**언제 쓰나** — 중첩 루프에서 바깥까지 빠져야 할 때.

**출력** (`ex.kt`)

```text
=== 3. 라벨 ===
--- 라벨 없는 break: 안쪽만 빠진다 ---
(1,1) (2,1) (3,1) 
--- 라벨 break: 바깥까지 빠진다 ---
(1,1) (1,2) (1,3) (2,1) 
--- continue@loop ---
(1,1) (2,1) (3,1) 
```

```text
   loop@ for (i in 1..3) {        ← 라벨은 루프 앞에 「이름@」
       for (j in 1..3) {
           break        ─────────> 안쪽 for 만 나간다
           break@loop   ─────────> 바깥 for 까지 나간다
           continue@loop ────────> 바깥 for 의 다음 i 로
       }
   }
```

- 라벨 이름은 **`이름@`** 로 붙이고 **`break@이름`** 으로 쓴다. Java 와 달리 `@` 가 붙는다.
- `break@loop` 의 출력을 보면 `i == 2 && j == 2` 에서 멈춰 **`(2,1)` 까지만** 찍혔다.
- `continue@loop` 은 안쪽을 버리고 **바깥의 다음 회차**로 간다 — 라벨 없는 `break` 와 같은 출력이 나온 것은 우연이다\
  (`j == 2` 에서 떠나는 시점이 같아서다).

비용 — `goto` 하나. 라벨은 바이트코드에 남지 않는다.

### (8) ★★ 람다 안에서는 `break` 가 아니라 `return` 이 나간다 — 그리고 라벨이 범위를 정한다

**언제 쓰나** — `forEach` 안에서 순회를 끊고 싶을 때.

```kotlin
fun findFirstEven(xs: List<Int>): Int? {
    xs.forEach {
        if (it % 2 == 0) return it     // 비지역 return — 함수 자체를 빠져나간다
    }
    return null
}

fun localReturn(xs: List<Int>): String {
    val sb = StringBuilder()
    xs.forEach {
        if (it % 2 == 0) return@forEach   // 이 람다 한 번만 건너뛴다
        sb.append(it)
    }
    return sb.toString()
}
```

**출력** (`ex.kt`)

```text
=== 4. 비지역 return ===
findFirstEven([1,3,4,6]) = 4
findFirstEven([1,3,5])   = null
localReturn([1,2,3,4,5]) = 135
```

```text
   xs.forEach { … return it … }        xs.forEach { … return@forEach … }
   +-------------------------+          +----------------------------+
   | 람다를 빠져나가고        |          | 람다 한 번만 끝낸다        |
   | forEach 도 빠져나가고    |          | forEach 는 계속 돈다       |
   | 바깥 함수까지 반환한다 ★ |          | = continue 와 같은 효과    |
   +-------------------------+          +----------------------------+
```

- ★ **`return` 은 「가장 가까운 `fun`」으로 돌아간다.** 람다가 아니라 **바깥 함수**다.\
  그래서 `findFirstEven` 이 `4` 에서 **함수째 반환**했다.
- **`return@라벨`** 을 쓰면 그 람다만 끝난다 — `continue` 와 같은 효과다.
- 이것이 되는 이유는 **`forEach` 가 인라인 함수이기 때문**이다. 인라인이 아니면 거부된다.

**출력** (`kotlinc bad2.kt`)

```text
bad2.kt:2:47: error: 'return' is prohibited here.
    val f: (Int) -> Unit = { x -> if (x == 2) return }
                                              ^^^^^^
```

- ★ **람다를 변수에 담는 순간 비지역 `return` 이 금지된다.** 그 람다는 인라인되지 않기 때문이다.
- **왜 인라인이면 되고 아니면 안 되는지의 정본은 [목록의 11번 주제](../11-inline-functions/)**(인라인 함수 — `noinline`/`crossinline`·비지역 반환)다.\
  여기서는 **현상까지만** 적는다.

비용 — 인라인된 람다에서는 `goto`·`areturn` 수준. 객체 없음.

### (9) `break`/`continue` 는 **루프 전용**이다 — 그리고 2.2 부터 람다를 뚫는다

**언제 쓰나** — `map` 안에서 `break` 를 적어 보고 싶을 때.

**출력** (`kotlinc bad2.kt`)

```text
bad2.kt:6:66: error: 'break' and 'continue' are only allowed inside loops.
fun breakInMap(xs: List<Int>): List<Int> = xs.map { if (it == 2) break else it }
                                                                 ^^^^^
```

- **루프가 없는 자리의 `break` 는 문법 에러**다. `when` 가지에서도 마찬가지다([06번 주제](../06-when-expression/)).

그런데 **루프 안의 인라인 람다**라면 2.2.0 부터 된다.

```kotlin
fun nonLocalBreak(): String {
    val sb = StringBuilder()
    for (i in 1..5) {
        listOf(10, 20, 30).forEach { v ->
            if (i == 3) break          // 2.2+ : 바깥 for 를 빠져나간다
            sb.append("$i:$v ")
        }
    }
    return sb.toString()
}
```

**출력** (`ex.kt`)

```text
=== 6. 비지역 break (2.2+) ===
nonLocalBreak() = 1:10 1:20 1:30 2:10 2:20 2:30
```

**출력** (`kotlinc -language-version 2.1 lv.kt`)

```text
warning: language version 2.1 is deprecated and its support will be removed in a future version of Kotlin. Update the version to 2.2.
lv.kt:4:57: error: the feature "break continue in inline lambdas" is only available since language version 2.2
    for (i in 1..3) { listOf(1,2).forEach { if (i == 2) break; sb.append(i) } }
                                                        ^^^^^
```

- ★ **버전 경계를 컴파일러에게 직접 물었다.** 2.0·2.1 은 거부, 2.2·2.3 은 통과다.
- 2.1 이하에서는 같은 일을 **`run` 라벨** 이나 **플래그 변수**로 풀어야 했다.

비용 — `goto` 하나(인라인된 뒤라 루프 바깥으로 그냥 뛴다).

### (10) `run` 라벨로 `continue` 흉내내기

**언제 쓰나** — 람다 안이 아니라 **블록 하나만** 건너뛰고 싶을 때.

```kotlin
fun runAsContinue(xs: List<Int>): String {
    val sb = StringBuilder()
    for (x in xs) {
        run skip@{
            if (x == 3) return@skip
            sb.append(x)
        }
    }
    return sb.toString()
}
```

**출력** (`ex.kt`)

```text
=== 5. run 라벨로 continue 흉내 ===
runAsContinue([1,2,3,4]) = 124
```

```text
   for (x in xs) {
       run skip@{
           if (…) return@skip   ──> 이 블록만 끝난다 (= continue)
           …
       }
       ← 여기는 항상 실행된다     ← 진짜 continue 와 다른 점 ★
   }
```

- ★ **`continue` 와 완전히 같지는 않다.** `run` 블록 뒤에 코드가 더 있으면 **그건 실행된다.**
- `run` 은 인라인 함수라 객체가 안 생긴다. scope function 의 정본은 [목록의 **14번 주제**](../14-scope-functions/)다.

비용 — 0(인라인).

### (11) `while`/`do-while`/`for` 는 **식이 아니다**

**언제 쓰나** — `if`·`when` 이 식인 것과 헷갈릴 때.

```kotlin
fun notExpr(n: Int): Int {
    val a = while (n > 0) { break }
    val b = do { } while (false)
    val c = for (i in 1..3) { }
    return 0
}
```

**출력** (`kotlinc bad1.kt`)

```text
bad1.kt:2:13: error: only expressions are allowed here.
    val a = while (n > 0) { break }
            ^^^^^^^^^^^^^^^^^^^^^^^
bad1.kt:3:13: error: only expressions are allowed here.
    val b = do { } while (false)
            ^^^^^^^^^^^^^^^^^^^^
bad1.kt:4:13: error: only expressions are allowed here.
    val c = for (i in 1..3) { }
            ^^^^^^^^^^^^^^^^^^^
```

```text
   식이다 (값이 나온다)          식이 아니다 (값이 없다)
   +----------------------+      +----------------------+
   | if / else            |      | for                  |
   | when                 |      | while                |
   | try / catch          |      | do-while             |
   +----------------------+      +----------------------+
     ← 대입·반환·보간 가능         ← 대입하면 에러
```

- ★ **Kotlin 이 「전부 식」인 언어는 아니다.** 분기는 식이고 **반복은 문**이다.
- 반복의 결과를 값으로 얻고 싶으면 **컬렉션 연산**(`map`·`filter`·`fold`)을 쓴다 — 그쪽은 식이다.\
  정본은 목록의 **42번 주제**부터.
- `if`·`when` 이 식인 것은 [06번 주제](../06-when-expression/)가 정본이다.

비용 — 0. 컴파일 타임이다.

## 문법 — 형태와 규칙

```kotlin
// 1) 범위와 progression
1..10            // IntRange       — 1,2,…,10
1 until 10       // IntRange       — 1,2,…,9
1..<10           // IntRange       — until 과 같다 (1.8.0 Stable)
10 downTo 1      // IntProgression — 10,9,…,1
1..10 step 2     // IntProgression — 1,3,5,7,9
'a'..'e'         // CharRange
5..1             // 빈 범위 — 0회 돈다 (에러 아님)

// 2) for
for (x in xs) { }
for (i in xs.indices) { }
for ((i, v) in xs.withIndex()) { }
for ((k, v) in map) { }
repeat(3) { i -> }               // 문법이 아니라 stdlib 인라인 함수

// 3) while — 식이 아니다
while (cond) { }
do { } while (cond)

// 4) 라벨
loop@ for (i in 1..3) {
    for (j in 1..3) {
        break@loop
        continue@loop
    }
}

// 5) 람다에서 나가기
xs.forEach { if (…) return       }   // 바깥 fun 까지 (인라인 람다에서만)
xs.forEach { if (…) return@forEach }  // 이 람다만 (= continue)
for (x in xs) { xs2.forEach { if (…) break } }   // 2.2.0+

// 6) 내 타입을 for 에 넣기
operator fun iterator(): Iterator<T>
```

규칙 불릿.

- **`for` 는 `iterator()` 규약으로 돈다.** 없으면 `for-loop range must have an 'iterator()' method.`
- **숫자 범위 리터럴은 객체를 안 만든다.** 변수에 담으면 객체가 하나 생기지만 **그래도 `Iterator` 는 아니다.**
- **`step` 은 항상 양수다.** `downTo` 에서도 그렇다.
- **`last` 는 실제로 도달하는 마지막 값**이다. 내가 적은 끝값이 아닐 수 있다.
- **빈 범위는 에러가 아니라 0회**다.
- **`break`/`continue` 는 루프 안에서만.** 2.2.0 부터 그 안의 인라인 람다까지 뚫는다.
- **`return` 은 가장 가까운 `fun` 으로 간다.** 람다만 끝내려면 `return@라벨`.
- **`for`/`while`/`do-while` 은 식이 아니다.**

## 어디서 틀리나

| 틀리는 형태 | 무슨 일이 일어나나 | 고치는 법 |
|---|---|---|
| `for (i in 10..1)` 로 내려가려 함 | **에러 없이 0회** 돈다 | `10 downTo 1` |
| `10 downTo 1 step -1` | `IllegalArgumentException: Step must be positive, was: -1.` | `step` 은 양수, 방향은 `downTo` 가 정한다 |
| `(1..9 step 3).last` 를 9 로 봄 | 실제 값은 **7** 이다 | `last` 는 도달하는 마지막 값이다 |
| `until` 과 `..` 을 헷갈림 | 끝값이 하나 차이 난다 — 흔한 off-by-one | 인덱스는 `indices` 나 `..<` 를 쓴다 |
| `forEach` 안에서 `break` (2.1 이하) | 컴파일 에러 | 2.2+ 로 올리거나 `return@forEach`/`run` 라벨 |
| `forEach` 안의 `return` 이 `continue` 인 줄 앎 | **함수째 반환된다** | `return@forEach` 를 쓴다 |
| 람다를 변수에 담고 `return` | `'return' is prohibited here.` | 인라인 람다 자리에서 직접 쓴다 |
| `map` 안에서 `break` | `'break' and 'continue' are only allowed inside loops.` | `takeWhile`·`firstOrNull` 로 바꾼다 |
| `val x = while (…) {}` | `only expressions are allowed here.` | 반복은 식이 아니다 — 컬렉션 연산을 쓴다 |
| `for (x in 1.0..2.0)` | `for-loop range must have an 'iterator()' method.` | 실수는 `in` 검사만 된다 |
| 범위를 `val` 에 담아 놓고 "객체 없다" 고 믿음 | `new IntRange` 가 실제로 생긴다 | 핫 루프면 리터럴로 적는다 |
| `run { }` 을 `continue` 로 믿음 | **블록 뒤 코드는 실행된다** | 진짜 `continue` 를 쓴다 |

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 | 근거 |
|---|---|---|
| `for` 가 `iterator()` 규약으로 돈다 | **언어** | 컴파일 에러 메시지 |
| `until` 과 `..<` 이 같은 범위다 | **언어** | 명세 + 실행 결과 |
| `step` 이 양수여야 한다 | **언어(stdlib 계약)** | `IllegalArgumentException` |
| `last` 가 도달하는 마지막 값이다 | **언어(stdlib 계약)** | 실행 |
| 빈 범위가 0회 도는 것 | **언어** | 실행 |
| `return` 이 가장 가까운 `fun` 으로 가는 것 | **언어** | 명세 + 실행 |
| 비지역 `break`/`continue` 가 2.2 부터인 것 | **언어(버전)** | `-language-version 2.1` 의 거부 메시지 |
| `for`/`while` 이 식이 아닌 것 | **언어** | 컴파일 에러 |
| **`for (i in 1..10)` 에 객체가 0개인 것** | **구현** ★ | `javap` |
| **끝값을 `bipush 11` 로 미리 계산하는 것** | **구현** | `javap` |
| **`MAX_VALUE` 일 때 비교를 뒤로 옮기는 것** | **구현** | `javap` |
| **`IntRange` 변수에서 `getFirst`/`getLast` 만 읽는 것** | **구현** | `javap` |
| **`indices` 가 객체를 안 만드는 것** | **구현** | `javap` |
| **`until` 과 `..<` 의 바이트코드가 같은 것** | **구현** | `javap` |
| **`step` 이 `getProgressionLastElement` 를 부르는 것** | **구현** | `javap` |
| **`String`/`IntArray` 가 인덱스로 펴지는 것** | **구현** | `javap` |

★ **가장 중요한 구분 한 줄** — **"`for (i in 1..10)` 은 공짜다" 는 언어 보장이 아니라 최적화다.**\
언어가 보장하는 것은 **"1부터 10까지 돈다" 뿐**이고, `Iterator` 를 안 만드는 것은 **이 컴파일러가 해 주는 일**이다.\
그래서 **범위를 변수에 담으면 그 최적화의 일부가 사라진다** — 그것도 `javap` 로만 보인다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 0부터 n-1 까지 | `for (i in 0..<n)` | off-by-one 이 눈에 보인다 |
| 컬렉션의 인덱스 | `for (i in xs.indices)` | 객체가 안 생기고 `size` 와 안 어긋난다 |
| 인덱스와 값이 둘 다 | `for ((i, v) in xs.withIndex())` | 이름이 붙는다 |
| 횟수만 필요 | `repeat(n) { }` | 쓰지 않을 변수를 안 만든다 |
| 조건을 만나면 멈춰야 할 때 | `for` + `break` | 람다보다 단순하다 |
| 변환해서 값을 얻고 싶을 때 | `map`/`filter`/`fold` | 반복은 식이 아니다 |
| 첫 번째만 필요할 때 | `firstOrNull { }` | 비지역 `return` 을 안 써도 된다 |
| 중첩 루프에서 바깥까지 | `break@라벨` | 플래그 변수가 안 생긴다 |
| 람다 안에서 다음 항목으로 | `return@forEach` | `continue` 와 같은 효과 |
| **범위를 변수로 재사용** | 핫 루프가 아니면 OK | 객체 하나가 생긴다((2)) |

판단 규칙 두 줄.

- **람다 안에서 흐름 제어가 필요해지면 그 자리는 대개 루프여야 하는 자리다.** `forEach` + `return@` 보다 `for` 가 읽기 쉽다.
- **`until`·`..<`·`indices` 중 하나로 통일한다.** 셋이 섞이면 off-by-one 이 어느 줄에서 났는지 못 찾는다.

## 핵심 문장

- ★ **`for (i in 1..10)` 은 `Iterator` 도 `IntRange` 도 안 만든다** — `iinc` 로 세는 루프다.
- ★ **범위를 변수에 담으면 `IntRange` 객체가 생긴다.** 그래도 `iterator()` 는 안 불리고 `getFirst`/`getLast` 만 읽는다.
- **`until` 과 `..<` 은 바이트코드가 한 글자도 다르지 않다.** `step` 만 stdlib 호출(`getProgressionLastElement`)이 하나 생긴다.
- **`step` 이 붙으면 `last` 가 내가 적은 끝값이 아니다**(`1..9 step 3` → `last = 7`).
- **빈 범위는 에러가 아니라 0회**다 — `for (i in 5..1)` 은 조용히 아무 일도 안 한다.
- `for` 는 **`iterator()` 규약**으로 돈다. 없으면 `for-loop range must have an 'iterator()' method.`
- **람다 안의 `return` 은 바깥 `fun` 까지 나간다.** 람다만 끝내려면 `return@라벨`.
- **비지역 `break`/`continue` 는 2.2.0** — `-language-version 2.1` 이 거부하는 것으로 확인했다.
- **`for`/`while`/`do-while` 은 식이 아니다.** `if`·`when` 과 갈리는 자리다.

## 관련 자료

- [`../README.md`](../README.md) — Kotlin 문법·API 주제 목록(이 주제는 07번)
- [`../../../java/syntax/20-control-flow-statements/`](../../../java/syntax/20-control-flow-statements/) — **Java 제어문의 정본.**\
  향상된 `for` 와 레이블 `break`/`continue` 가 거기 있다. 여기는 **range·progression 과 람다를 뚫는 흐름 제어**
- [`../../../java/syntax/21-switch-statement-and-expression/`](../../../java/syntax/21-switch-statement-and-expression/) — Java `switch`. `break` 가 루프 말고 **거기서도** 쓰이던 것의 정본
- [06번 주제](../06-when-expression/) — `if`·`when` 이 **식**인 것의 정본. 이 문서의 (11)과 짝이다. `in` 가지도 거기 있다
- [03번 주제](../03-null-safe-types/) — 바이트코드에 섞여 보이는 `checkNotNullParameter` 의 정본
- [목록의 **11번 주제**](../11-inline-functions/)(인라인 함수 — `noinline`/`crossinline`·비지역 반환) — **비지역 `return` 이 왜 인라인에서만 되는가**의 정본. 이 문서는 현상까지만 적었다
- [목록의 **10번 주제**](../10-lambdas-and-higher-order-functions/)(람다와 고차 함수) — 람다 자체의 정본
- [목록의 **14번 주제**](../14-scope-functions/)(scope function) — `run`·`let` 의 정본. (10)의 `run skip@{ }` 이 그것이다
- 목록의 **30번 주제**(구조 분해 선언) — `for ((i, v) in …)` 의 정본
- 목록의 **31번 주제**(연산자 오버로딩·중위 함수·`invoke` 규약) — `iterator()`·`contains` 규약의 정본
- 목록의 **42번 주제**부터(컬렉션 변환·필터·집계) — "반복의 결과를 값으로" 쪽의 정본
- 목록의 **45번 주제**(`take`/`drop`/`chunked`/`windowed`) — `for` 로 쓰던 패턴이 이미 함수로 있는 것

## 용어 풀이

- **range(범위)** — 시작과 끝을 가진 값의 집합. `1..10`·`'a'..'e'`. 타입은 `IntRange`·`CharRange` 등.
- **progression(수열)** — range 에 **간격(step)** 이 붙은 것. `IntProgression`. `IntRange` 는 step 이 1인 progression 이다.
- **`last`** — progression 이 **실제로 도달하는 마지막 값**. 내가 적은 끝값(`endInclusive`)과 다를 수 있다.
- **`until` / `..<`** — 끝값을 **제외**하는 범위. 둘은 같은 것의 다른 표기다.
- **`downTo`** — 내려가는 progression 을 만드는 중위 함수.
- **`step`** — 간격을 바꾸는 중위 함수. **항상 양수**여야 한다.
- **`indices`** — 컬렉션의 유효한 인덱스 범위(`0..<size`)를 주는 확장 프로퍼티.
- **`withIndex()`** — 항목마다 `(인덱스, 값)` 쌍을 주는 확장 함수.
- **규약(convention)** — 특정 이름의 `operator` 함수가 있으면 특정 문법이 동작하는 약속. `for` 는 `iterator()` 를 본다.
- **라벨(label)** — `이름@` 로 루프·람다에 붙이는 표시. `break@이름`·`continue@이름`·`return@이름` 으로 범위를 지정한다.
- **비지역 `return`** — 람다 안에서 **람다가 아니라 바깥 함수**를 반환시키는 `return`. 인라인 람다에서만 된다.
- **비지역 `break`/`continue`** — 루프 안의 인라인 람다에서 **그 루프**를 제어하는 것. 2.2.0 부터.
- **식(expression) / 문(statement)** — 값을 내느냐 안 내느냐. Kotlin 에서 분기는 식, 반복은 문이다.
- **`iinc`** — 지역 변수를 상수만큼 증감시키는 JVM 명령. 세는 루프의 정체.
- **`getProgressionLastElement`** — `first`·`last`·`step` 으로 **실제 마지막 값**을 계산하는 stdlib 내부 함수.

---

## 더 들어가면

- `Long` 범위(`1L..10L`)와 `Char` 범위(`'a'..'z'`)도 같은 방식으로 펴진다.\
  다만 `Long` 은 [06번 주제](../06-when-expression/)의 `when` 과 마찬가지로 **JVM 에 `long` 전용 분기 명령이 없어** 비교 명령이 달라진다.
- `for (i in 1..10)` 의 `i` 는 **`val` 이다.** 몸통 안에서 대입하면 컴파일이 거부한다.

```text
badi.kt:1:29: error: 'val' cannot be reassigned.
fun f() { for (i in 1..3) { i = i + 1; println(i) } }
                            ^
```

  Java 의 `for (int i = …)` 와 다른 점이다. 세는 변수를 바꿔 루프를 조작하는 관용구가 **문법 층에서 막혀 있다.**
- `repeat` 은 `public inline fun repeat(times: Int, action: (Int) -> Unit)` 이다.\
  **인라인이라 그 안에서 비지역 `return` 이 된다** — (8)의 `forEach` 와 같은 성질이다.
- `withIndex()` 는 항목마다 `IndexedValue` 를 만든다. 핫 루프에서 인덱스만 필요하면 `indices` 쪽이 할당이 없다\
  (**다만 이 문서에서 속도는 재지 않았다** — `javap` 로 보이는 것은 **할당의 유무**까지다).
- 이 문서에서 **못 잰 것 두 가지** —\
  ① `..<` 의 도입·Stable 버전은 **공식 릴리스 노트를 읽은 것**이다. kotlinc 2.4.20 이 `-language-version 1.9` 이하를 거부해\
  **컴파일러에게 물을 수가 없었다**(`language version 1.9 is no longer supported; use version 2.0 or greater instead.`).\
  ② **성능은 재지 않았다.** 이 문서의 비용 주장은 전부 **`javap` 에 보이는 명령과 할당의 유무**까지다.
