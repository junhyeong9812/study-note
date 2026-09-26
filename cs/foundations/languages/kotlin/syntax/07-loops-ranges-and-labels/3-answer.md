# kotlin/syntax/07 — 반복문·`range`·progression·라벨·비지역 `break`/`continue` (2.2+) — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javap` 에서 실제로 얻었다.\
> 역어셈블은 **기본 `-jvm-target`(1.8 · `major version: 52`)** 이다.\
> `..<` 의 도입·Stable 버전만 **실측이 아니라 공식 릴리스 노트를 읽은 것**이다(아래 「실행 검증」의 못 잰 것).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★ 객체는 **0개**다 — `IntRange` 도 `Iterator` 도 없다

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

**왜 그런가**

```text
   소스                          바이트코드
   for (i in 1..10)      ──>     i = 1
       s += i                    while (i < 11) { s += i; i++ }

   new IntRange(1,10)    ──>     (없다)
   .iterator()           ──>     (없다)
   .hasNext() / .next()  ──>     (없다)
```

- **`new` 가 한 번도 안 나온다.** `iconst_1`(초기값)·`iinc 1, 1`(증가)·`if_icmpge`(끝 검사)뿐이다.
- 끝값 비교 상수는 **10 이 아니라 `bipush 11`** 이다 — 컴파일러가 `last + 1` 을 **컴파일 시점에** 계산했다.\
  덕분에 `i <= 10` 이 `i < 11` 한 번의 비교가 된다.
- Java 의 `for (int i = 1; i <= 10; i++)` 과 **같은 모양**이다.
- 그래서 "range 는 객체라 느리다" 는 **이 형태에서는 거짓**이다.\
  다만 **범위를 변수에 담으면 사정이 달라진다**(2번) — 그래서 이 말은 "형태에 따라 참" 이다.

### 2. ★★ `IntRange` 객체가 하나 생긴다 — 그래도 `iterator()` 는 안 불린다

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

**왜 그런가**

```text
   for (i in 1..10)                for (i in r)   ← r: IntRange
   +----------------------+        +--------------------------------+
   | 객체 0개             |        | new IntRange  ← 객체 1개       |
   | bipush 11 로 비교    |        | getFirst() / getLast() 를 읽고 |
   |                      |        | 그 뒤로는 똑같이 센다           |
   +----------------------+        +--------------------------------+
        iterator() 없음                  iterator() 여전히 없음 ★
```

- 새로 생기는 것은 **`new kotlin/ranges/IntRange`** 하나다.
- ★ **그래도 `iterator()` 는 안 불린다.** 컴파일러가 읽어 가는 것은 **`getFirst()`·`getLast()`** 둘뿐이다.
- 반복 조건의 형태가 1번과 다르다 — **`if_icmpgt` 로 빈 범위를 먼저 거르고**, 몸통 **뒤에서** `if_icmpeq` 로 끝을 본다.\
  1번처럼 `last + 1` 을 미리 만들 수가 없기 때문이다. `last` 가 `Int.MAX_VALUE` 이면 **`+1` 이 음수로 넘쳐** 루프가 아예 안 돈다.
- 같은 대비를 리터럴 쪽에서도 볼 수 있다 — 끝값이 상수 `Int.MAX_VALUE` 면 컴파일러가 형태를 바꾼다.

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

- `if_icmpge last+1` 이 사라지고 **`if_icmpeq last`** 가 몸통 뒤로 옮겨 갔다. **오버플로를 막은 것**이다.

### 3. ★ `step` 만 부른다 — `ProgressionUtilKt.getProgressionLastElement`

**출력** (`javap -c -p out/IcodeKt.class` — `step`)

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

**출력** (같은 파일 — `until` 과 `..<`)

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

**출력** (같은 파일 — `downTo`)

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

**왜 그런가**

```text
   1..10        ──> iinc +1,  끝값을 컴파일러가 계산 (bipush 11)
   0 until 10   ──> iinc +1
   0..<10       ──> iinc +1   ← until 과 바이트 단위로 같다 ★
   10 downTo 1  ──> iinc -1   ← 부호만 바뀐다
   1..10 step 2 ──> getProgressionLastElement() 한 번 + iinc +2 ★
```

- ★ **`until` 과 `..<` 은 명령이 한 글자도 다르지 않다.** 두 함수 본문을 나란히 놓으면 오프셋까지 같다.
- ★ **함수 호출이 생기는 것은 `step` 하나**다 — `kotlin/internal/ProgressionUtilKt.getProgressionLastElement:(III)I`.
- `downTo` 는 **`iinc 1, -1`** 로 방향을 바꾼다. 객체도 호출도 없다.
- 그 stdlib 함수가 필요한 이유 — **`step` 이 붙으면 실제로 도달하는 마지막 값이 내가 적은 끝값이 아닐 수 있다**(4번).\
  `(first, last, step)` 로 **진짜 마지막 값**을 계산해 두고, 루프는 그 값과 `if_icmpeq` 로 비교한다.

### 4. ★ `[1,4,7]` · `7` · `[]` · `[9,6,3]` · 예외

**출력** (`ex2.kt`)

```text
--- progression 의 last 는 상한이 아니다 ---
1..9 step 3 = [1, 4, 7]   first=1 last=7 step=3
1..10 step 3 = [1, 4, 7, 10]  first=1 last=10 step=3
(1..9 step 3) == (1..10 step 3) ? false
--- step 에 0 이나 음수를 주면 ---
IllegalArgumentException: Step must be positive, was: 0.
IllegalArgumentException: Step must be positive, was: -1.
--- downTo 에 step 은 양수다 ---
(9 downTo 1 step 3) = [9, 6, 3]
--- 빈 범위 ---
(5..1).isEmpty()=true  (1 until 1).isEmpty()=true  (1 downTo 5).isEmpty()=true
for (i in 5..1) 의 반복 횟수 = 0
```

**왜 그런가**

| | 식 | 값 |
|---|---|---|
| `[A]` | `(1..9 step 3).toList()` | `[1, 4, 7]` |
| `[B]` | `(1..9 step 3).last` | **`7`** |
| `[C]` | `(5..1).toList()` | `[]` — `for` 에 넣으면 **0회** |
| `[D]` | `(9 downTo 1 step 3).toList()` | `[9, 6, 3]` |
| `[E]` | `(1..9 step -1)` | `IllegalArgumentException: Step must be positive, was: -1.` |

```text
   1..9 step 3        1 ──3──> 4 ──3──> 7 ──✗──> 10 은 9 를 넘는다
                      last = 7   (내가 적은 9 가 아니다)

   1..10 step 3       1 ──3──> 4 ──3──> 7 ──3──> 10
                      last = 10  (딱 맞았다)
```

- `[B]` 가 9 가 아닌 이유는 `last` 가 「**실제로 도달하는 마지막 값**」이기 때문이다.\
  3번의 `getProgressionLastElement` 가 계산하는 값이 정확히 이것이다.
- `[C]` 는 **예외가 아니라 빈 범위**다. `for (i in 5..1)` 은 **에러 없이 0회** 돈다 —\
  내려가려면 `downTo` 를 써야 한다. **조용히 아무 일도 안 일어나는** 자리라 눈으로는 안 잡힌다.
- `[E]` 는 `step` 자체가 거부한다. **방향은 `downTo` 가 정하고 `step` 은 크기만 정한다** —\
  그래서 `9 downTo 1 step 3` 의 step 도 **양수 3** 이다.

타입도 갈린다.

```text
타입 — (1..5)=IntRange, (1..10 step 3)=IntProgression, (1 until 5)=IntRange
```

- `step` 을 붙이면 **`IntProgression`** 이 되고, `until`·`..<` 은 **`IntRange`** 그대로다.

### 5. `operator fun iterator()` 가 있으면 된다 — 실수 범위는 거부된다

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

**출력** (`kotlinc badf.kt`)

```text
badf.kt:1:21: error: for-loop range must have an 'iterator()' method.
fun f() { for (x in 1.0..2.0) println(x) }
                    ^^^^^^^^
```

**출력** (`ex2.kt`)

```text
--- 실수 범위는 for 가 안 된다 ---
1.0..2.0 의 타입 = ClosedDoubleRange, 1.5 in 1.0..2.0 = true
```

**왜 그런가**

```text
   for (x in c)
        │
        ├─ c.iterator()      ← operator fun 이름이 정확히 이것이어야 한다
        │
        └─ while (it.hasNext()) { x = it.next(); … }
```

- `[A]` 가 되려면 **`operator fun iterator(): Iterator<T>`** 가 있어야 한다. 이름이 정확히 `iterator` 여야 한다.\
  Kotlin 의 `Iterator` 는 바이트코드에서 **`java.util.Iterator`** 로 내려간다.
- `[B]` 는 `for-loop range must have an 'iterator()' method.` 다 — **`ClosedDoubleRange` 에는 `iterator()` 가 없다.**\
  연속인 값에는 "다음 값" 이 정의되지 않기 때문이다.
- `[C]` 는 **된다.** `in` 은 `contains` 규약이고 그것은 있다. **만들어지지만 순회가 안 되는** 타입이다.
- `String`·`IntArray` 는 `Iterator` 가 **안 생긴다** — 인덱스로 펴진다.

| `for` 대상 | 무엇이 되나 | 객체 |
|---|---|---|
| `1..10` 리터럴 | `iinc` 세는 루프 | 0 |
| `IntRange` 변수 | `getFirst`/`getLast` + 세는 루프 | `IntRange` 1개 |
| `xs.indices` | `size()` + 세는 루프 | 0 |
| `List<T>` | `java.util.Iterator` | `Iterator` 1개 |
| `String` | `length()` + `charAt(i)` | 0 |
| `IntArray` | `arraylength` + `iaload` | 0 |
| 내 타입 + `operator fun iterator()` | 그 `iterator()` 호출 | 그 구현이 만드는 것 |

### 6. ★★ `4` 와 `"135"` — `return` 은 **함수째** 나간다

**출력** (`ex.kt`)

```text
=== 4. 비지역 return ===
findFirstEven([1,3,4,6]) = 4
findFirstEven([1,3,5])   = null
localReturn([1,2,3,4,5]) = 135
```

**출력** (`kotlinc bad2.kt`)

```text
bad2.kt:2:47: error: 'return' is prohibited here.
    val f: (Int) -> Unit = { x -> if (x == 2) return }
                                              ^^^^^^
```

**왜 그런가**

```text
   xs.forEach { … return it … }        xs.forEach { … return@forEach … }
   +-------------------------+          +----------------------------+
   | 람다를 빠져나가고        |          | 람다 한 번만 끝낸다        |
   | forEach 도 빠져나가고    |          | forEach 는 계속 돈다       |
   | 바깥 함수까지 반환한다 ★ |          | = continue 와 같은 효과    |
   +-------------------------+          +----------------------------+
```

- `[A]` = **`4`** — 첫 짝수를 만난 자리에서 **`findFirstEven` 자체가 반환**됐다. `6` 은 보지도 않았다.
- `[B]` = **`"135"`** — `return@forEach` 는 그 람다 한 회차만 끝내므로 짝수만 건너뛰고 홀수가 다 붙었다.
- ★ **`return` 은 「가장 가까운 `fun`」으로 간다.** 람다는 `fun` 이 아니다.\
  그래서 람다 안에서 무심코 `return` 을 적으면 **의도한 `continue` 가 아니라 함수 종료**가 된다.
- 람다를 변수에 담으면 **`'return' is prohibited here.`** 다.
- 가르는 성질은 **그 람다가 인라인되느냐**다. `forEach` 는 인라인 함수라 람다 몸통이 호출부에 펴지므로\
  그 `return` 이 바깥 함수의 `return` 이 될 수 있다. 변수에 담은 람다는 **진짜 객체**라 그럴 수가 없다.\
  **원리의 정본은 [목록의 11번 주제](../11-inline-functions/)**(인라인 함수 — 비지역 반환)다. 여기서는 현상까지다.

### 7. ★ `[B]` 만 된다 — `[A]`·`[C]` 는 에러

**출력** (`kotlinc bad2.kt` — `[A]`)

```text
bad2.kt:6:66: error: 'break' and 'continue' are only allowed inside loops.
fun breakInMap(xs: List<Int>): List<Int> = xs.map { if (it == 2) break else it }
                                                                 ^^^^^
```

**출력** (`kotlinc bad1.kt` — `[C]`)

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

**출력** (`ex.kt` — `[B]`)

```text
=== 6. 비지역 break (2.2+) ===
nonLocalBreak() = 1:10 1:20 1:30 2:10 2:20 2:30
```

**출력** (`kotlinc -language-version 2.1 lv.kt` — 버전을 컴파일러에게 물은 것)

```text
warning: language version 2.1 is deprecated and its support will be removed in a future version of Kotlin. Update the version to 2.2.
lv.kt:4:57: error: the feature "break continue in inline lambdas" is only available since language version 2.2
    for (i in 1..3) { listOf(1,2).forEach { if (i == 2) break; sb.append(i) } }
                                                        ^^^^^
lv.kt:7:43: error: the feature "when guards" is only available since language version 2.2
fun c(x: Any): String = when (x) { is Int if x > 5 -> "big"; else -> "n" }
                                          ^^^^^^^^
```

**왜 그런가**

- `[A]` — `map` 안에는 **루프가 없다.** `break`/`continue` 는 **루프 전용 문법**이다.
- `[B]` — 바깥에 `for` 가 있고 `forEach` 는 **인라인 람다**라 2.2.0 부터 그 `for` 를 제어할 수 있다.\
  `i == 3` 에서 **바깥 `for` 까지** 빠져나가 `3:`·`4:`·`5:` 가 아예 안 찍혔다.
- `[C]` — 반복은 식이 아니다(10번).
- ★ **버전은 문서가 아니라 컴파일러에게 물었다.** `-language-version` 을 2.0·2.1·2.2·2.3 으로 네 번 돌려\
  **2.2 부터 통과**하는 것을 확인했다. 같은 명령이 06번의 `when` guard 도 같은 경계로 대답했다.

### 8. `break` 는 가장 안쪽, `break@라벨` 은 그 라벨이 붙은 루프

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

**왜 그런가**

```text
   loop@ for (i in 1..3) {        ← 라벨은 루프 앞에 「이름@」
       for (j in 1..3) {
           break        ─────────> 안쪽 for 만 나간다
           break@loop   ─────────> 바깥 for 까지 나간다
           continue@loop ────────> 바깥 for 의 다음 i 로
       }
   }
```

- 라벨 없는 `break` 는 `j == 2` 에서 안쪽만 끊었으므로 **`(1,1) (2,1) (3,1)`** — 바깥은 세 바퀴 다 돌았다.
- `break@loop` 은 `i == 2 && j == 2` 에서 **둘 다** 끊었으므로 `(2,1)` 까지만 찍혔다.
- 문법은 **`이름@` 로 붙이고 `break@이름` 으로 쓴다.**\
  Java 는 `loop:` / `break loop;` 라 **`@` 의 위치와 콜론 여부**가 다르다.\
  Java 쪽 정본은 [`../../../java/syntax/20-control-flow-statements/`](../../../java/syntax/20-control-flow-statements/).
- `continue@outer` 는 **안쪽 루프의 남은 회차를 버리고** 바깥 루프의 다음 회차로 간다.
- `return@forEach` 는 **효과가 `continue` 와 같다**(6번의 `"135"`). 다만 이름이 `return` 인 이유는\
  거기가 루프가 아니라 **람다**이기 때문이다 — 끝내는 것은 회차가 아니라 **람다 호출 한 번**이다.

### 9. `run` 블록만 끝난다 — 블록 **뒤** 코드는 실행된다

**출력** (`ex.kt`)

```text
=== 5. run 라벨로 continue 흉내 ===
runAsContinue([1,2,3,4]) = 124
```

**왜 그런가**

```text
   for (x in xs) {
       run skip@{
           if (…) return@skip   ──> 이 블록만 끝난다 (= continue)
           …
       }
       ← 여기는 항상 실행된다     ← 진짜 continue 와 다른 점 ★
   }
```

- `return@skip` 이 끝내는 것은 **`run` 람다 한 번**이다. 바깥 `for` 는 계속 돈다 —\
  그래서 `3` 만 빠지고 `"124"` 가 나왔다.
- ★ **진짜 `continue` 와 다른 점** — `run { }` **뒤에 코드가 더 있으면 그것은 실행된다.**\
  `continue` 는 회차 자체를 끝내지만 `return@skip` 은 **블록 하나만** 끝낸다.
- `run` 은 **인라인 함수**라 객체가 안 생긴다(6번의 `forEach` 와 같은 성질이다).
- scope function 의 정본은 [목록의 **14번 주제**](../14-scope-functions/)다.

### 10. 반복은 **문**이다 — `only expressions are allowed here.`

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

**출력** (`kotlinc badi.kt`)

```text
badi.kt:1:29: error: 'val' cannot be reassigned.
fun f() { for (i in 1..3) { i = i + 1; println(i) } }
                            ^
```

**왜 그런가**

```text
   식이다 (값이 나온다)          식이 아니다 (값이 없다)
   +----------------------+      +----------------------+
   | if / else            |      | for                  |
   | when                 |      | while                |
   | try / catch          |      | do-while             |
   +----------------------+      +----------------------+
     ← 대입·반환·보간 가능         ← 대입하면 에러
```

- 한 문장으로 — **분기는 「어느 값을 고를까」라서 값이 나오고, 반복은 「몇 번 할까」라서 낼 값이 없다.**
- 반복의 결과를 값으로 얻으려면 **컬렉션 연산**(`map`·`filter`·`fold`)을 쓴다. 그쪽은 식이다 —\
  정본은 목록의 **42번 주제**부터.
- ★ **`for (i in 1..3) { i = i + 1 }` 도 안 된다.** 루프 변수는 **`val`** 이다.\
  Java 의 `for (int i = …)` 와 다른 점으로, 세는 변수를 바꿔 루프를 조작하는 관용구가 **문법 층에서 막혀 있다.**

### 11. 다른 주제와 잇기

- **비지역 `return` 이 왜 인라인에서만 되는가 → [목록의 11번 주제](../11-inline-functions/)**(인라인 함수 — `noinline`/`crossinline`·비지역 반환)가 정본이다.\
  이 문서는 **현상**(`'return' is prohibited here.` 와 `forEach` 의 함수째 반환)까지만 적었다.\
  람다 자체는 [목록의 **10번 주제**](../10-lambdas-and-higher-order-functions/).
- **구조 분해(`for ((i, v) in xs.withIndex())`) → [목록의 30번 주제](../30-destructuring-declarations-and-componentn/)**(구조 분해 선언 — `componentN` 과 그 한계)가 정본이다.\
  `Map` 을 `for ((k, v) in m)` 으로 도는 것도 같은 문법이다.
- **규약 전체 → [목록의 31번 주제](../31-operator-overloading-infix-and-invoke/)**(연산자 오버로딩·중위 함수·`invoke` 규약)가 정본이다.\
  `iterator()`(이 문서 5번)·`contains`(`in`)·`rangeTo`(`..`)·`step`/`downTo`(중위 함수)가 전부 거기 속한다.
- **Java 레이블 `break`/`continue` → [`../../../java/syntax/20-control-flow-statements/`](../../../java/syntax/20-control-flow-statements/)** 가 정본이다.\
  `switch` 안의 `break` 는 [`../../../java/syntax/21-switch-statement-and-expression/`](../../../java/syntax/21-switch-statement-and-expression/) 쪽이다 —\
  **Kotlin 에는 그 자리의 `break` 가 아예 없다**([06번 주제](../06-when-expression/)).

---

## 실행 검증

**환경**

```text
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
openjdk version "21.0.5" 2024-10-15 LTS
OpenJDK Runtime Environment Temurin-21.0.5+11 (build 21.0.5+11-LTS)
OpenJDK 64-Bit Server VM Temurin-21.0.5+11 (build 21.0.5+11-LTS, mixed mode, sharing)
```

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `icode.kt` | `1..10` 리터럴·`IntRange` 변수·`step`·`downTo`·`until`·`..<`·`List`·`indices` 의 바이트코드 | `kotlinc` → `javap -c -p out/IcodeKt.class` |
| `icode2.kt` | `Int.MAX_VALUE` 경계·커스텀 `iterator()`·`String`·`IntArray` 의 바이트코드 | `kotlinc` → `javap -c -p out2/Icode2Kt.class` |
| `ex.kt` | range/progression 목록·인덱스 3형태·라벨 3형태·비지역 `return`·`run` 라벨·비지역 `break` | `kotlinc` → `java` |
| `ex2.kt` | `last` 가 상한이 아닌 것·`step` 0/음수 예외·빈 범위 0회·`Map` 구조 분해·실수 범위 타입 | `kotlinc` → `java` |
| `bad1.kt` | `while`/`do-while`/`for` 가 식이 아닌 것 | `kotlinc` (컴파일 실패가 결과) |
| `bad2.kt` | 비인라인 람다의 `return` 금지 · `map` 안의 `break` 금지 | `kotlinc` (에러 2건) |
| `badf.kt` | 실수 범위에 `iterator()` 가 없는 것 | `kotlinc` (에러 1건) |
| `badi.kt` | 루프 변수가 `val` 인 것 | `kotlinc` (에러 1건) |
| `lv.kt` | 비지역 `break`/`continue` 가 **2.2 부터**인 것 | `kotlinc -language-version {1.9,2.0,2.1,2.2,2.3}` |

**구현 의존 항목** — `javap` 의 명령 이름·상수 풀 번호, `bipush 11` 이라는 미리 계산된 끝값,
`getFirst`/`getLast` 만 읽는 형태, `MAX_VALUE` 에서 비교를 뒤로 옮기는 것,
`indices` 가 객체를 안 만드는 것, `until` 과 `..<` 의 동일 바이트코드,
`ProgressionUtilKt.getProgressionLastElement` 라는 이름 — 전부 **이 컴파일러 버전 + 기본 타깃의 산출물**이다.\
반면 "`for` 가 `iterator()` 규약으로 돈다" · "`step` 은 양수" · "`last` 는 도달하는 마지막 값" ·
"빈 범위는 0회" · "`return` 은 가장 가까운 `fun` 으로" · "반복은 식이 아니다" 는 **언어 규칙**이라 타깃과 무관하다.

**★ 던져 봤더니 예상과 달랐던 것 — 세 건**

1. **`for (i in 1..10)` 이 `IntRange` 조차 안 만든다.**\
   "`Iterator` 는 안 만들어도 `IntRange` 는 만들겠지" 라고 예상했는데 **`new` 가 한 번도 안 나왔다.**\
   반대로 **변수에 담으면 `IntRange` 가 생긴다** — 같은 소스가 아닌데 같은 것으로 취급하면 틀린다.
2. **`until` 과 `..<` 이 바이트 단위로 같았다.** 새 연산자라 뭔가 다른 게 있을 줄 알았는데 **오프셋까지 같았다.**
3. **끝값이 `Int.MAX_VALUE` 면 루프 형태 자체가 바뀐다.**\
   `if_icmpge last+1` 이 `if_icmpeq last` 로 바뀌고 검사가 몸통 뒤로 간다 — **오버플로 대비를 컴파일러가 한다.**

**★ 못 잰 것** — `..<`(rangeUntil)의 도입·Stable 버전은 **이 환경에서 측정할 수 없었다.**
kotlinc 2.4.20 이 `-language-version 1.9` 이하를 거부하기 때문이다.

```text
===== -language-version 1.9 =====
error: language version 1.9 is no longer supported; use version 2.0 or greater instead.
```

그래서 **1.7.20 도입 / 1.8.0 Stable** 이라는 값은 **공식 릴리스 노트를 열어 읽은 것**이지 실측이 아니다.
측정으로 말할 수 있는 것은 **"2.0 에서 이미 쓸 수 있었다"** 까지다.

**★ 성능은 재지 않았다** — 이 문서의 「비용」 칸은 전부 **`javap` 에 보이는 명령과 할당의 유무**를 말한 것이고,
실행 시간은 한 번도 측정하지 않았다. "객체가 0개다" 는 관찰이고 "그래서 빠르다" 는 이 문서가 하지 않은 주장이다.
