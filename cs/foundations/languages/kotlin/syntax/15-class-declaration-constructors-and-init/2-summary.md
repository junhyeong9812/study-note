# kotlin/syntax/15 — 클래스 선언: 주 생성자·부 생성자·`init` 블록 순서 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Classes](https://kotlinlang.org/docs/classes.html) · [Properties](https://kotlinlang.org/docs/properties.html) · [Inheritance](https://kotlinlang.org/docs/inheritance.html) · [Null safety](https://kotlinlang.org/docs/null-safety.html).
> **실행 검증** — 이 문서의 모든 출력·에러·예외·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javap` 에서 실제로 얻었다.\
> `kotlinc` 11회(컴파일 실패 3벌) · `java` 6회(런타임 예외 1벌) · `javap` 6회.
> ⚠️ **`-jvm-target` 을 밝히지 않은 바이트코드 주장은 반쪽이다.** 이 문서의 역어셈블은 전부 **기본값 1.8**(`major version: 52`)이다 —\
> 그래서 문자열 보간이 `StringBuilder` 로 보인다([02번 주제](../02-string-templates-and-raw-strings/)).
> ⚠️ **다시 돌리면 달라지는 블록은 없다** — 싣는 스택 트레이스도 사용자 프레임뿐이다. 재대조 근거는 3-answer 의 「흔들리는 칸」 표다.
> **버전** — 주 생성자·부 생성자·`init` 의 규칙은 **1.0** 이래 같다. 이 문서에 버전으로 갈리는 항목은 없다.
> **경계** — `open`/`final` 기본값과 `override` 규칙은 목록의 **19번 주제**, backing field·`lateinit`·`const` 는 [16번 주제](../16-properties-backing-field-lateinit-const/),\
> `data class` 가 무엇을 만들어 주는지는 목록의 **22번 주제**, 기본 인자·이름 붙인 인자는 [08번 주제](../08-function-declaration-default-and-named-args/)가 정본이다.\
> 여기는 **한 객체가 만들어질 때 무엇이 어느 순서로 도는가**만 다룬다.\
> Java 쪽 짝은 [`../../../java/syntax/06-initialization-order/`](../../../java/syntax/06-initialization-order/)(순서)와\
> [`../../../java/syntax/07-constructors/`](../../../java/syntax/07-constructors/)(`this()`/`super()`)다.
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**Kotlin 에서 클래스 이름 옆 괄호는 「파라미터 목록」이 아니라 생성자 그 자체다.**

그리고 **클래스 몸통에 흩어져 있는 프로퍼티 초기화식과 `init` 블록은 그 괄호에 이어 붙는 한 줄기의 코드**다.\
흩어져 보이지만 **컴파일되면 생성자 하나 안에 선언 순서대로 줄줄이 들어간다.**

> **주 생성자(primary constructor)** — 클래스 이름 바로 뒤 괄호. 몸통이 없고, 몸통 대신 `init` 블록을 쓴다.\
> **부 생성자(secondary constructor)** — 몸통 안의 `constructor(…)`. 몸통이 있고, **반드시 주 생성자를 거쳐야 한다.**\
> **`init` 블록** — 주 생성자에 딸린 코드 조각. 여러 개 쓸 수 있고 **선언한 자리 순서대로** 돈다.

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 서류 접수 창구 한 곳 | 주 생성자 — 모든 생성이 여기를 지난다 |
| 창구에서 받아 적는 칸 | 주 생성자 파라미터 |
| 받아 적자마자 서류철에 꽂는 칸 | `val`/`var` 를 붙인 파라미터 — 필드가 된다 |
| 받아 적고 처리만 하고 안 남기는 칸 | `val`/`var` 없는 파라미터 — 필드가 **안** 된다 |
| 접수 후 처리 단계가 적힌 순서지 | 프로퍼티 초기화식 + `init` 블록 — **적힌 순서대로** |
| 간이 창구 | 부 생성자 — 본 창구를 **반드시 거친 뒤** 자기 일을 한다 |
| 본 창구가 없으면 간이 창구마다 순서지를 복사해 붙인다 | 주 생성자가 없으면 초기화가 **각 부 생성자에 복사된다** |
| 아직 서류철에 안 꽂았는데 상급 기관이 서류를 달라고 한다 | 상위 클래스 `init` 이 `open` 함수를 부른다 — **빈 칸을 읽는다** |

```text
   class Box(val tag: String) {        ← ① 주 생성자. 여기가 유일한 입구
       val first = f()                 ← ②
       init { … }                      ← ③
       val second = g()                ← ④
       init { … }                      ← ⑤
       constructor(n: Int) : this(…) { ← ⑥ 부 생성자는 ①을 거친 뒤
           …                           ←    자기 몸통을 돈다
       }
   }

   Box("P") : ① → ② → ③ → ④ → ⑤
   Box(7)   : ⑥의 this(…) → ① → ② → ③ → ④ → ⑤ → ⑥의 몸통
                                                     ↑
                                          부 생성자 몸통은 언제나 맨 나중
```

## 이 주제가 답하려는 질문

1. 프로퍼티 초기화식과 `init` 블록이 **어느 순서로** 도는가 — 그리고 그것이 **하나의 생성자**인가.
2. 부 생성자는 **언제** 자기 몸통을 도는가 — 주 생성자가 없으면 무엇이 달라지는가.
3. 주 생성자 파라미터는 **어디까지 보이는가** — 그리고 아직 안 채워진 프로퍼티를 읽을 수 있는 구멍은 어디인가.

## 동작 방식

### (1) ★★ 몸통은 **선언 순서대로 한 줄기**다 — `init` 과 프로퍼티가 섞인다

**언제 쓰나** — `init` 블록을 어디에 둘지 고민할 때. **자리가 곧 순서다.**

```text
===== 소스: order.kt =====
class Box(val tag: String) {
    val first = say("1 프로퍼티 first")

    init {
        say("2 init 블록 A")
    }

    val second = say("3 프로퍼티 second")

    init {
        say("4 init 블록 B")
    }

    constructor(n: Int) : this("from-int-$n") {
        say("5 부 생성자 본문")
    }

    private fun say(s: String): String {
        println("   $s   (tag=$tag)")
        return s
    }
}

fun main() {
    println("A 주 생성자로 만들 때")
    Box("P")
    println("B 부 생성자로 만들 때")
    Box(7)
}
```

**출력** (`java -cp oorder:kotlin-stdlib.jar OrderKt`)

```text
A 주 생성자로 만들 때
   1 프로퍼티 first   (tag=P)
   2 init 블록 A   (tag=P)
   3 프로퍼티 second   (tag=P)
   4 init 블록 B   (tag=P)
B 부 생성자로 만들 때
   1 프로퍼티 first   (tag=from-int-7)
   2 init 블록 A   (tag=from-int-7)
   3 프로퍼티 second   (tag=from-int-7)
   4 init 블록 B   (tag=from-int-7)
   5 부 생성자 본문   (tag=from-int-7)
```

```text
   선언한 자리                     도는 순서
   ────────────────────────       ──────────
   val first = say("1 …")    ──▶  1
   init { say("2 …") }       ──▶  2
   val second = say("3 …")   ──▶  3
   init { say("4 …") }       ──▶  4
   constructor(n: Int) { 5 } ──▶  5   ← 부 생성자 몸통은 언제나 맨 나중
```

그림 해설:

- ★★ **프로퍼티 초기화식과 `init` 블록은 따로 놀지 않는다.** 「필드 먼저, `init` 나중」이 아니라\
  **소스에 적힌 순서대로 번갈아 돈다.** `1 → 2 → 3 → 4` 가 그 증거다.
- ★ **부 생성자로 만들어도 앞의 넷은 똑같이 돈다**(`B`). 그리고 **부 생성자 몸통은 맨 나중**이다.
- ★ `tag=from-int-7` 이 처음부터 찍힌다 — `this("from-int-$n")` 로 **주 생성자를 먼저 완주한 뒤** 부 생성자 몸통이 시작된다는 뜻이다.
- **`init` 을 여러 개 쓸 수 있다.** 그리고 그 사이에 프로퍼티를 끼워 넣을 수 있다 — **그래서 자리가 의미를 갖는다.**

### (2) ★★★ `<init>` 하나에 **전부 들어간다** — 명령 순서를 전수로 본다

**언제 쓰나** — (1)의 순서가 「언어 규칙」인지 「컴파일러 기분」인지 알고 싶을 때. **이 주제의 네 번째 창이다.**

```text
===== 소스: icode.kt =====
class Box(val tag: String) {
    val first: Int = 1

    init {
        println("init A")
    }

    val second: Int = first + 1

    init {
        println("init B")
    }
}
```

**출력** (`javap -c -p -s oicode/Box.class`)

```text
Compiled from "icode.kt"
public final class Box {
  private final java.lang.String tag;
    descriptor: Ljava/lang/String;

  private final int first;
    descriptor: I

  private final int second;
    descriptor: I

  public Box(java.lang.String);
    descriptor: (Ljava/lang/String;)V
    Code:
       0: aload_1
       1: ldc           #9                  // String tag
       3: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_0
       7: invokespecial #18                 // Method java/lang/Object."<init>":()V
      10: aload_0
      11: aload_1
      12: putfield      #21                 // Field tag:Ljava/lang/String;
      15: aload_0
      16: iconst_1
      17: putfield      #25                 // Field first:I
      20: nop
      21: ldc           #27                 // String init A
      23: getstatic     #33                 // Field java/lang/System.out:Ljava/io/PrintStream;
      26: swap
      27: invokevirtual #39                 // Method java/io/PrintStream.println:(Ljava/lang/Object;)V
      30: nop
      31: aload_0
      32: aload_0
      33: getfield      #25                 // Field first:I
      36: iconst_1
      37: iadd
      38: putfield      #42                 // Field second:I
      41: nop
      42: ldc           #44                 // String init B
      44: getstatic     #33                 // Field java/lang/System.out:Ljava/io/PrintStream;
      47: swap
      48: invokevirtual #39                 // Method java/io/PrintStream.println:(Ljava/lang/Object;)V
      51: nop
      52: return

  public final java.lang.String getTag();
    descriptor: ()Ljava/lang/String;
    Code:
       0: aload_0
       1: getfield      #21                 // Field tag:Ljava/lang/String;
       4: areturn

  public final int getFirst();
    descriptor: ()I
    Code:
       0: aload_0
       1: getfield      #25                 // Field first:I
       4: ireturn

  public final int getSecond();
    descriptor: ()I
    Code:
       0: aload_0
       1: getfield      #42                 // Field second:I
       4: ireturn
}
```

```text
   public Box(java.lang.String);   ← 생성자는 이것 하나뿐이다
   ┌──────────────────────────────────────────────────────────┐
   │  0  checkNotNullParameter(tag, "tag")   ← 널 검사가 먼저   │
   │  7  super.<init>()                      ← Object 생성자    │
   │ 12  putfield tag                        ← 주 생성자 프로퍼티│
   │ 17  putfield first                      ← ② val first      │
   │ 21  println("init A")                   ← ③ init 블록      │
   │ 38  putfield second                     ← ④ val second     │
   │ 42  println("init B")                   ← ⑤ init 블록      │
   │ 52  return                                                │
   └──────────────────────────────────────────────────────────┘
```

그림 해설:

- ★★★ **`putfield` 와 `println` 이 번갈아 나온다.** (1)에서 본 순서가 **명령 배치 그대로**다.\
  「필드를 먼저 다 채우고 `init` 을 돈다」가 **아니라는 것**이 이 한 장에 들어 있다.
- ★ **생성자가 하나뿐이다.** `init` 블록은 **별도의 메서드가 아니다** — 호출도 없고 이름도 없다.\
  Java 의 인스턴스 초기화 블록과 같은 자리이고, 같은 방식으로 **생성자 안으로 복사된다**\
  ([`../../../java/syntax/06-initialization-order/`](../../../java/syntax/06-initialization-order/)).
- ★★ **`checkNotNullParameter` 가 `super.<init>()` 보다 먼저**다(오프셋 3 대 7).\
  Kotlin 은 널 검사를 **상위 생성자 호출 앞**에 심는다 — 「`super()` 는 무조건 첫 문장」이라는 Java 의 규칙과 보이는 모양이 다르다.\
  (검증기가 이 배치를 통과시킨다는 것은 같은 모양의 `order.kt` 가 **실제로 로드돼 돌았다**는 사실로 확인된다.)
- ★ `getfield first` 가 `putfield second` 직전에 있다 — **아래 프로퍼티가 위 프로퍼티를 읽는 것은 된다.**\
  반대는 안 된다(7번 절).
- `nop` 은 **인라인·초기화 구간 표시**이지 계산이 아니다.

### (3) ★★ 부 생성자는 **반드시 주 생성자를 거친다**

**언제 쓰나** — 생성 경로를 여럿 만들 때.

```text
===== 소스: sec.kt =====
class Box(val tag: String) {
    var extra: Int = 0

    init {
        println("init 블록")
    }

    constructor(n: Int) : this("int-$n") {
        extra = n
        println("부 생성자 본문")
    }
}
```

**출력** (`javap -c -p osec/Box.class`)

```text
Compiled from "sec.kt"
public final class Box {
  private final java.lang.String tag;

  private int extra;

  public Box(java.lang.String);
    Code:
       0: aload_1
       1: ldc           #9                  // String tag
       3: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_0
       7: invokespecial #18                 // Method java/lang/Object."<init>":()V
      10: aload_0
      11: aload_1
      12: putfield      #21                 // Field tag:Ljava/lang/String;
      15: nop
      16: ldc           #23                 // String init 블록
      18: getstatic     #29                 // Field java/lang/System.out:Ljava/io/PrintStream;
      21: swap
      22: invokevirtual #35                 // Method java/io/PrintStream.println:(Ljava/lang/Object;)V
      25: nop
      26: return

  public final java.lang.String getTag();
    Code:
       0: aload_0
       1: getfield      #21                 // Field tag:Ljava/lang/String;
       4: areturn

  public final int getExtra();
    Code:
       0: aload_0
       1: getfield      #45                 // Field extra:I
       4: ireturn

  public final void setExtra(int);
    Code:
       0: aload_0
       1: iload_1
       2: putfield      #45                 // Field extra:I
       5: return

  public Box(int);
    Code:
       0: aload_0
       1: new           #50                 // class java/lang/StringBuilder
       4: dup
       5: invokespecial #51                 // Method java/lang/StringBuilder."<init>":()V
       8: ldc           #53                 // String int-
      10: invokevirtual #57                 // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
      13: iload_1
      14: invokevirtual #60                 // Method java/lang/StringBuilder.append:(I)Ljava/lang/StringBuilder;
      17: invokevirtual #63                 // Method java/lang/StringBuilder.toString:()Ljava/lang/String;
      20: invokespecial #65                 // Method "<init>":(Ljava/lang/String;)V
      23: aload_0
      24: iload_1
      25: putfield      #45                 // Field extra:I
      28: ldc           #67                 // String 부 생성자 본문
      30: getstatic     #29                 // Field java/lang/System.out:Ljava/io/PrintStream;
      33: swap
      34: invokevirtual #35                 // Method java/io/PrintStream.println:(Ljava/lang/Object;)V
      37: return
}
```

```text
   Box(int)                         Box(String)  ← 주 생성자
   ┌───────────────────────┐        ┌────────────────────────┐
   │ StringBuilder 로       │        │ checkNotNullParameter  │
   │  "int-$n" 만들기       │        │ super.<init>()         │
   │ invokespecial <init>(  │──────▶ │ putfield tag           │
   │   Ljava/lang/String;)V │        │ println("init 블록")    │
   │ putfield extra         │        │ return                 │
   │ println("부 생성자 …")  │◀──────  └────────────────────────┘
   │ return                 │   돌아와서 자기 몸통
   └───────────────────────┘
```

그림 해설:

- ★★ `Box(int)` 의 **첫 일이 `invokespecial "<init>":(Ljava/lang/String;)V`** 다 — `this("int-$n")` 가 이것이다.\
  **`super.<init>()` 도, `putfield tag` 도, `init` 블록도 `Box(int)` 안에는 없다.** 전부 주 생성자 쪽에 있다.
- ★ 그래서 **초기화 코드가 중복되지 않는다.** 경로가 몇 개든 **실제 초기화는 한 군데**다.
- ★★ 위임을 **빼면 컴파일이 안 된다.**

```text
===== 소스: nodelegate.kt =====
class Box(val tag: String) {
    constructor(n: Int) {
        println("부 생성자")
    }
}
===== kotlinc nodelegate.kt =====
nodelegate.kt:2:5: error: primary constructor call expected.
    constructor(n: Int) {
    ^^^^^^^^^^^^^^^^^^^
(exit 1)
```

- 에러가 `constructor` 선언 전체를 지목하고 「**주 생성자 호출이 필요하다**」고 말한다.\
  Java 는 `super()` 를 생략하면 **컴파일러가 암묵으로 넣어 주지만**, Kotlin 은 주 생성자가 있으면 **명시를 요구한다.**

### (4) ★ 주 생성자가 **없으면** 초기화가 생성자마다 **복사된다**

**언제 쓰나** — 주 생성자를 안 쓰고 부 생성자만 여럿 둘 때.

```text
===== 소스: noprimary.kt =====
class Box {
    val a: String = say("1 프로퍼티 a")

    init {
        say("2 init 블록")
    }

    constructor(n: Int) {
        say("3 부 생성자(Int)")
    }

    constructor(s: String) : this(s.length) {
        say("4 부 생성자(String)")
    }

    private fun say(s: String): String {
        println("   $s")
        return s
    }
}

fun main() {
    println("F Box(7)")
    Box(7)
    println("G Box(\"abcd\")")
    Box("abcd")
}
```

**출력** (`java -cp onp:kotlin-stdlib.jar NoprimaryKt`)

```text
F Box(7)
   1 프로퍼티 a
   2 init 블록
   3 부 생성자(Int)
G Box("abcd")
   1 프로퍼티 a
   2 init 블록
   3 부 생성자(Int)
   4 부 생성자(String)
```

**출력** (`javap -c -p onp/Box.class` — 생성자 둘)

```text
$ javap -c -p onp/Box.class    # 생성자 둘만
  public Box(int);
    Code:
       0: aload_0
       1: invokespecial #18                 // Method java/lang/Object."<init>":()V
       4: aload_0
       5: aload_0
       6: ldc           #20                 // String 1 프로퍼티 a
       8: invokespecial #24                 // Method say:(Ljava/lang/String;)Ljava/lang/String;
      11: putfield      #11                 // Field a:Ljava/lang/String;
      14: nop
      15: aload_0
      16: ldc           #26                 // String 2 init 블록
      18: invokespecial #24                 // Method say:(Ljava/lang/String;)Ljava/lang/String;
      21: pop
      22: nop
      23: aload_0
      24: ldc           #28                 // String 3 부 생성자(Int)
      26: invokespecial #24                 // Method say:(Ljava/lang/String;)Ljava/lang/String;
      29: pop
      30: return

  public Box(java.lang.String);
    Code:
       0: aload_1
       1: ldc           #33                 // String s
       3: invokestatic  #39                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_0
       7: aload_1
       8: invokevirtual #45                 // Method java/lang/String.length:()I
      11: invokespecial #47                 // Method "<init>":(I)V
      14: aload_0
      15: ldc           #49                 // String 4 부 생성자(String)
      17: invokespecial #24                 // Method say:(Ljava/lang/String;)Ljava/lang/String;
      20: pop
      21: return

```

그림 해설:

- ★★ **`Box(int)` 안에 `putfield a` 와 `init` 블록이 통째로 들어가 있다.** 주 생성자가 없으니\
  **그 코드를 얹을 자리가 없어서 각 생성자에 복사된 것**이다.
- ★ **`Box(String)` 에는 없다.** `this(s.length)` 로 **같은 클래스의 다른 생성자에 위임**했기 때문이다 —\
  위임하면 복사본을 안 받는다. 그래서 `G` 에서 `1 → 2` 가 **한 번만** 찍혔다.
- ★★ 위임을 **안 하는 부 생성자가 둘이면 복사본도 둘**이다.

```text
===== 소스: twosec.kt =====
class Box {
    val a: String = say("프로퍼티 a")
    init { say("init 블록") }
    constructor(n: Int) { say("부 생성자(Int)") }
    constructor(d: Double) { say("부 생성자(Double)") }
    private fun say(s: String): String { println("   $s"); return s }
}

fun main() {
    println("H Box(1)");   Box(1)
    println("I Box(1.0)"); Box(1.0)
}
```

**출력** (`java -cp ots:kotlin-stdlib.jar TwosecKt`)

```text
H Box(1)
   프로퍼티 a
   init 블록
   부 생성자(Int)
I Box(1.0)
   프로퍼티 a
   init 블록
   부 생성자(Double)
```

- `H`·`I` 모두 `프로퍼티 a → init 블록` 을 거친다. **같은 코드가 두 벌 존재하는 것**이다.
- ★ 그래서 **주 생성자를 두는 편이 기본**이다 — 초기화가 한 군데로 모이고 복사가 사라진다.

### (5) ★★ 주 생성자 파라미터가 **보이는 범위**

**언제 쓰나** — `val` 을 붙일지 말지 정할 때. **범위가 곧 필드 유무다.**

```text
===== 소스: param.kt =====
class User(name: String, val age: Int) {
    val upper: String = name.uppercase()

    init {
        println("init 에서 name : $name")
    }

    fun greet(): String = "hi $name"
}
===== kotlinc param.kt =====
param.kt:8:32: error: unresolved reference 'name'.
    fun greet(): String = "hi $name"
                               ^^^^
(exit 1)
```

- ★★ **`init` 과 프로퍼티 초기화식에서는 되는데 메서드에서는 안 된다.**\
  `val upper: String = name.uppercase()` 는 통과했고 `fun greet() = "hi $name"` 만 막혔다.
- ★ **커스텀 게터도 메서드다** — 그래서 똑같이 막힌다.

```text
===== 소스: capture.kt =====
class User(name: String) {
    val shout: String get() = name.uppercase() + "!"
}
===== kotlinc capture.kt =====
capture.kt:2:31: error: unresolved reference 'name'.
    val shout: String get() = name.uppercase() + "!"
                              ^^^^
(exit 1)
```

- ★★ 이유는 바이트코드에 있다. `val` 을 안 붙인 파라미터는 **필드가 되지 않는다.**

```text
===== 소스: param2.kt =====
class User(name: String, val age: Int) {
    val upper: String = name.uppercase()

    init {
        println("init 에서 name : $name")
    }

    fun greet(): String = "hi $upper"
}
```

**출력** (`javap -p -s oparam2/User.class`)

```text
Compiled from "param2.kt"
public final class User {
  private final int age;
    descriptor: I
  private final java.lang.String upper;
    descriptor: Ljava/lang/String;
  public User(java.lang.String, int);
    descriptor: (Ljava/lang/String;I)V

  public final int getAge();
    descriptor: ()I

  public final java.lang.String getUpper();
    descriptor: ()Ljava/lang/String;

  public final java.lang.String greet();
    descriptor: ()Ljava/lang/String;
}
```

```text
   class User(name: String, val age: Int) { … }

   필드 목록          age      ← val 을 붙였다 → 필드 + 게터
                      upper    ← 몸통의 프로퍼티 → 필드 + 게터
                      (name 없음) ★ 생성자가 끝나면 사라진다
```

- ★★ **`name` 이라는 필드가 없다.** 생성자 지역 변수로만 존재하고 **`<init>` 이 끝나면 사라진다.**\
  그러니 나중에 부르는 메서드가 볼 수 있을 리가 없다 — 에러가 「문법 제약」이 아니라 **물리적 사실**이다.
- ★ **예외가 하나 있다 — 람다가 잡아 가면 살아남는다.**

```text
===== 소스: capture2.kt =====
class User(name: String) {
    val f: () -> String = { name.uppercase() + "!" }
}

fun main() {
    println("C : ${User("kim").f()}")
}
```

**출력** (`javap -p -s ocap2/User.class` 와 실행)

```text
Compiled from "capture2.kt"
public final class User {
  private final kotlin.jvm.functions.Function0<java.lang.String> f;
    descriptor: Lkotlin/jvm/functions/Function0;
  public User(java.lang.String);
    descriptor: (Ljava/lang/String;)V

  public final kotlin.jvm.functions.Function0<java.lang.String> getF();
    descriptor: ()Lkotlin/jvm/functions/Function0;

  private static final java.lang.String f$lambda$0(java.lang.String);
    descriptor: (Ljava/lang/String;)Ljava/lang/String;
}
$ java -cp ocap2:kotlin-stdlib.jar Capture2Kt
C : KIM!
```

- ★ 이때도 **`name` 필드는 안 생긴다.** 람다를 만드는 `invokedynamic` 의 인자로 값이 넘어가고,\
  살아남는 것은 **`Function0` 객체 안**이다(`f` 필드). `f$lambda$0(String)` 이 그 람다 본문이다.
- ★ 정리하면 **「클래스 몸통의 초기화 구간」에서만 보인다.** 그 구간이 곧 `<init>` 이다.

### (6) ★★★ 상속이 끼면 **아직 안 채운 칸을 읽는다** — 타입이 non-null 이어도

**언제 쓰나** — 상위 클래스 `init` 이나 생성자에서 `open` 함수·프로퍼티를 부를 때. **이 갈래 최악의 함정이다.**

```text
===== 소스: leak.kt =====
open class Base {
    init {
        println("   Base.init — open 함수를 부른다 : ${describe()}")
    }
    open fun describe(): String = "Base"
}

class Child(val label: String) : Base() {
    val len: Int = label.length
    override fun describe(): String = "Child(label=$label, len=$len)"
}

fun main() {
    println("D 생성 중에 무엇이 찍히나")
    val c = Child("hello")
    println("E 다 만든 뒤       : ${c.describe()}")
}
```

**출력** (`java -cp oleak:kotlin-stdlib.jar LeakKt`)

```text
D 생성 중에 무엇이 찍히나
   Base.init — open 함수를 부른다 : Child(label=null, len=0)
E 다 만든 뒤       : Child(label=hello, len=5)
```

```text
   Child("hello") 를 만들 때 실제 순서

   Child.<init>
     └─▶ super.<init>  = Base.<init>
            └─▶ init { describe() }
                   └─▶ Child.describe()   ★ 여기가 문제
                         label → 아직 putfield 전 → null
                         len   → 아직 putfield 전 → 0
     ◀── 돌아와서
     putfield label = "hello"
     putfield len   = 5
```

그림 해설:

- ★★★ **`label` 의 타입은 `String`(널 불가)인데 `null` 이 찍혔다.** `len` 은 `Int` 인데 `0` 이다.\
  **아직 `putfield` 를 안 했으니 JVM 의 기본값이 그대로 보이는 것**이다.
- ★★ **컴파일러가 아무 말도 안 했다** — 경고도 에러도 없이 `exit 0` 이다.\
  「널 불가 타입에는 널이 안 들어온다」는 보장이 **이 한 자리에서 뚫린다.**
- ★ (2)에서 본 순서 그대로다 — `super.<init>` 이 **필드 대입보다 앞**이기 때문에 생기는 일이다.
- ★★ 운이 나쁘면 값이 아니라 **예외**로 나온다.

```text
===== 소스: leak2.kt =====
open class Base {
    init {
        println("   Base.init : ${describe()}")
    }
    open fun describe(): String = "Base"
}

class Child(val label: String) : Base() {
    override fun describe(): String = "len=${label.length}"
}

fun main() {
    Child("hello")
}
===== java -cp oleak2:kotlin-stdlib.jar Leak2Kt =====
Exception in thread "main" java.lang.NullPointerException: Cannot invoke "String.length()" because "this.label" is null
	at Child.describe(leak2.kt:9)
	at Base.<init>(leak2.kt:3)
	at Child.<init>(leak2.kt:8)
	at Leak2Kt.main(leak2.kt:13)
	at Leak2Kt.main(leak2.kt)
(exit 1)
```

- 스택 트레이스가 경로를 그대로 보여 준다 — `Leak2Kt.main` → `Child.<init>` → `Base.<init>` → `Child.describe`.
- ★ **JVM 의 「도움 되는 NPE」 메시지가 원인을 지목한다** — `because "this.label" is null`.
- ★ 막는 법은 **상위 클래스 생성자·`init` 에서 `open` 멤버를 부르지 않는 것**뿐이다.\
  꼭 필요하면 `open` 대신 `final`(Kotlin 기본값) 로 두거나, 초기화를 생성 후 별도 메서드로 미룬다.\
  Kotlin 이 **클래스와 멤버를 기본 `final` 로 둔 것**이 바로 이 구멍을 좁히는 장치다(목록의 **19번 주제**).

### (7) 선언 순서를 어기면 — **이쪽은 컴파일러가 잡는다**

**언제 쓰나** — `init` 을 클래스 맨 위에 두고 싶을 때.

```text
===== 소스: forward.kt =====
class Box {
    init {
        println(later)
    }
    val later: String = "늦게 선언한 것"
}
===== kotlinc forward.kt =====
forward.kt:3:17: error: variable 'later' must be initialized.
        println(later)
                ^^^^^
(exit 1)
```

- ★ 「**변수가 초기화되어야 한다**」로 막는다. (6)과 정확히 대비된다 —\
  **같은 클래스 안에서 앞뒤가 뒤집힌 것은 컴파일러가 보고, 상속을 거쳐 뒤집힌 것은 못 본다.**
- 그래서 **`init` 은 읽을 프로퍼티보다 아래에 둔다.** 자리가 곧 순서라는 (1)의 규칙이 여기서 강제된다.

### (8) `= 0` 은 바이트코드에 **안 나온다** — 숫자를 근거로 쓸 때 조심할 자리

**언제 쓰나** — `javap` 로 초기화 순서를 세면서 「왜 이 필드만 없지?」 할 때.

(3)의 `sec.kt` 에는 `var extra: Int = 0` 이 있는데 **주 생성자에 `putfield extra` 가 없다.**\
`99` 로만 바꿔 다시 찍으면 나타난다.

```text
$ javap -c -p osec99/Box.class   # var extra: Int = 99 로만 바꾼 판
  public Box(java.lang.String);
    Code:
       0: aload_1
       1: ldc           #9                  // String tag
       3: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_0
       7: invokespecial #18                 // Method java/lang/Object."<init>":()V
      10: aload_0
      11: aload_1
      12: putfield      #21                 // Field tag:Ljava/lang/String;
      15: aload_0
      16: bipush        99
      18: putfield      #25                 // Field extra:I
      21: nop
      22: ldc           #27                 // String init 블록
      24: getstatic     #33                 // Field java/lang/System.out:Ljava/io/PrintStream;
      27: swap
      28: invokevirtual #39                 // Method java/io/PrintStream.println:(Ljava/lang/Object;)V
      31: nop
      32: return

```

- ★ **JVM 이 필드를 0/`null` 로 초기화해 주므로 컴파일러가 대입을 생략한 것**이다.\
  `bipush 99` 가 들어간 판과 비교하면 **그 자리만 다르다.**
- ★★ **이것은 언어 보장이 아니라 최적화다.** 「`init` 순서」를 `putfield` 개수로 세면 **0 으로 초기화한 필드에서 어긋난다.**\
  세려면 **0 이 아닌 값**으로 두고 찍어야 한다.

## 문법 — 형태와 규칙

```kotlin
// 형태 ① 주 생성자만
class A(val x: Int, y: String) {           // x 는 필드, y 는 아니다
    val z = y.length                       // 초기화식에서는 y 가 보인다
    init { require(x > 0) }                // init 에서도 보인다
}

// 형태 ② 주 생성자 + 부 생성자
class B(val tag: String) {
    constructor(n: Int) : this("n$n") { }  // ← this(...) 필수
}

// 형태 ③ 주 생성자 없음 (부 생성자만)
class C {
    val a = 1                              // 각 부 생성자에 복사된다
    constructor(n: Int) { }
    constructor(s: String) : this(s.length) { }   // 위임하면 복사본을 안 받는다
}

// 형태 ④ 애너테이션·가시성이 붙으면 constructor 낱말이 필요하다
class D private constructor(val x: Int)
```

- **`init` 은 여러 개** 쓸 수 있고 **적힌 순서대로** 돈다. 프로퍼티 초기화식과 **같은 줄기**에 있다.
- **부 생성자는 `this(…)` 또는 `super(…)` 로 시작**한다. 주 생성자가 있으면 **`this(…)` 만** 된다.
- **주 생성자 파라미터는 초기화 구간에서만 보인다.** 메서드·커스텀 게터에서는 안 보인다.
- **`val`/`var` 를 붙이면 필드가 되고 안 붙이면 안 된다.** 그것이 가시성의 이유다.
- 주 생성자에는 **몸통이 없다.** 코드가 필요하면 `init` 을 쓴다.
- 기본 인자를 쓰면 생성자 오버로드가 아니라 **합성 생성자 + 비트마스크**가 된다 — 정본은 [08번 주제](../08-function-declaration-default-and-named-args/)다.

## 어디서 틀리나

1. ★★★ **상위 클래스 `init`/생성자에서 `open` 멤버를 부른다.** 하위 필드가 **아직 안 채워져 있다**((6)).\
   널 불가 타입에 `null` 이 들어오고 **경고조차 없다.**
2. ★★ **`init` 을 클래스 맨 위에 둔다.** 아래 프로퍼티를 읽으면 컴파일 에러((7)). 자리가 곧 순서다.
3. ★ **부 생성자 몸통에서 초기화를 한다.** 주 생성자 → 프로퍼티·`init` → **부 생성자 몸통** 순이라\
   `init` 은 이미 **옛 값**을 보고 지나갔다.
4. ★ **주 생성자 없이 부 생성자를 여럿 둔다.** 초기화가 **복사돼 두 벌 존재한다**((4)).
5. ★ **`val` 을 안 붙인 파라미터를 메서드에서 쓰려 한다.** 필드가 없어서 **원리적으로 불가능**하다((5)).
6. ★ **`javap` 로 순서를 세면서 `= 0` 필드를 빠뜨린다.** 대입이 생략돼 있다((8)).
7. **`init` 에서 예외를 던지면** 객체는 안 만들어지지만, 이미 등록한 리스너·열어 둔 자원은 그대로 남는다 —\
   `init` 은 트랜잭션이 아니다.

## 구현 세부사항 대 언어 보장

| 사실 | 어느 층인가 | 근거 |
|---|---|---|
| 프로퍼티 초기화식과 `init` 이 **선언 순서대로** 돈다 | **언어 보장** | 공식 문서 · (1) 실행 |
| 부 생성자가 **주 생성자를 반드시 거친다** | **언어 보장** | (3) — 안 거치면 컴파일 에러 |
| 부 생성자 몸통이 **맨 나중** | **언어 보장** | (1)(3) |
| 주 생성자 파라미터가 **초기화 구간에서만** 보인다 | **언어 보장** | (5) — 에러 |
| `val` 없는 파라미터에 **필드가 없다** | **언어 보장의 결과** | (5) — 필드 목록 |
| 상속 경유로 **미초기화 필드를 읽을 수 있다** | **언어 보장의 구멍**(JVM 생성 순서에서 옴) | (6) — 실행·NPE |
| 초기화가 **`<init>` 하나에 들어간다** | **JVM 구현** — `init` 은 메서드가 아니다 | (2) |
| `checkNotNullParameter` 가 `super.<init>` **앞**에 있는 것 | ★ **이 판의 관찰** | (2) |
| 주 생성자 없을 때 **각 생성자에 복사**되는 것 | **JVM 구현** — 언어 규칙(순서)의 구현 방식 | (4) |
| **`= 0` 이 생략**되는 것 | ★ **이 컴파일러의 최적화** | (8) |
| `nop`·상수 풀 번호·오프셋 | ★ **이 판의 산출물** | 전부 |

- ★★ **가장 조심할 자리**: (6)은 **버그가 아니라 규칙의 결과**다. JVM 이 `super.<init>` 을 먼저 돌리도록 정해 놓았고,\
  Kotlin 의 널 불가 타입은 **컴파일 타임 보장**이라 **이 구간을 볼 수가 없다.**\
  그래서 「널 불가 타입에는 절대 널이 없다」는 **이 한 구간에서 틀린 말**이 된다 — 정본은 [03번 주제](../03-null-safe-types/)이고,\
  여기서는 **그 보장이 끝나는 또 하나의 자리**로만 읽는다([05번 주제](../05-platform-types/)가 다른 자리다).

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 생성 경로가 하나다 | 주 생성자만 | 초기화가 한 군데로 모인다 |
| 인자 조합이 여러 가지다 | 주 생성자 + **기본 인자** | 부 생성자보다 조합이 싸다([08번 주제](../08-function-declaration-default-and-named-args/)) |
| 다른 타입에서 변환해 만든다 | 부 생성자 `: this(…)` | 변환 코드가 몸통에 들어간다 |
| 검증이 필요하다 | `init { require(…) }` | 프로퍼티가 채워진 뒤 도는 자리에 둔다 |
| 계산해서 채울 프로퍼티가 있다 | 프로퍼티 초기화식 | `init` 에 넣으면 `val` 을 못 쓴다 |
| 상속을 열어야 한다 | **`open` 멤버를 생성자에서 부르지 않는다** | (6)의 구멍 |
| 객체 생성 후에만 알 수 있는 값이 있다 | `lateinit`/`by lazy` | [16번 주제](../16-properties-backing-field-lateinit-const/) · [17번 주제](../17-delegated-properties/) |

## 핵심 문장

1. **클래스 이름 옆 괄호가 생성자다.** 몸통이 없고, 몸통 대신 `init` 을 쓴다.
2. **프로퍼티 초기화식과 `init` 블록은 한 줄기다** — 선언한 자리 순서대로 번갈아 돈다.
3. **모든 생성은 주 생성자를 지난다.** 부 생성자는 `this(…)` 로 그리로 가고, **자기 몸통은 맨 나중**이다.
4. **주 생성자가 없으면 초기화가 각 생성자에 복사된다** — 위임한 생성자만 면제다.
5. **`val`/`var` 없는 파라미터는 필드가 아니다.** 그래서 초기화 구간에서만 보인다.
6. ★ **상위 클래스 생성자에서 `open` 멤버를 부르면 하위 필드는 아직 비어 있다** — 널 불가 타입이 `null` 을 낸다.
7. ★ **같은 클래스 안의 전방 참조는 컴파일러가 잡고, 상속을 거친 것은 못 잡는다.**

## 관련 자료

- [`../../../java/syntax/06-initialization-order/`](../../../java/syntax/06-initialization-order/) — **그쪽은 `static` 초기화까지 포함한 9단계가 정본, 여기는 Kotlin 의 주/부 생성자 구조부터.**
- [`../../../java/syntax/07-constructors/`](../../../java/syntax/07-constructors/) — **그쪽은 `super()`/`this()` 한 줄의 앞뒤 규칙이 정본, 여기는 Kotlin 이 그 규칙을 어떻게 다시 적었나.**
- [16번 주제 — 프로퍼티](../16-properties-backing-field-lateinit-const/) — **그쪽은 backing field·`lateinit`·`const` 가 정본, 여기는 그 필드가 언제 채워지나.**
- [17번 주제 — 위임 프로퍼티](../17-delegated-properties/) — 초기화를 **첫 사용까지 미루는** 방법.
- [03번 주제 — null 안전 타입](../03-null-safe-types/) — **그쪽이 널 불가 보장의 정본**, 여기는 (6)이 그 보장이 끝나는 자리라는 것만.
- [05번 주제 — 플랫폼 타입](../05-platform-types/) — 널 불가 보장이 끝나는 **다른** 자리.
- [08번 주제 — 함수 선언·기본 인자](../08-function-declaration-default-and-named-args/) — 생성자 오버로드를 대체하는 기본 인자.
- [02번 주제 — 문자열 템플릿](../02-string-templates-and-raw-strings/) — 역어셈블에 `StringBuilder` 가 보이는 이유.
- 목록의 **19번 주제** — `open`/`final` 기본값이 (6)의 구멍을 왜 좁히나.
- 목록의 **22번 주제** — `data class` 가 주 생성자만 보는 이유.
- 목록의 **25번 주제** — `companion object` 와 `static` 초기화의 자리.

## 용어 풀이

- **주 생성자** — 클래스 이름 뒤 괄호. 몸통이 없다.
- **부 생성자** — 몸통 안 `constructor(…)`. 반드시 다른 생성자에 위임한다.
- **`init` 블록** — 주 생성자에 딸린 코드 조각. 여러 개 가능, 선언 순서대로 돈다.
- **초기화 구간** — 프로퍼티 초기화식 + `init` 블록을 합쳐 부르는 말. 컴파일되면 `<init>` 안이다.
- **`<init>`** — JVM 이 생성자에 붙이는 이름.
- **`putfield`** — 인스턴스 필드에 값을 넣는 JVM 명령.
- **`invokespecial`** — 생성자·`private`·`super` 호출에 쓰는 JVM 명령. 디스패치되지 않는다.
- **전방 참조(forward reference)** — 아직 선언·초기화되지 않은 것을 먼저 읽는 것.
- **`checkNotNullParameter`** — 널 불가 파라미터에 널이 들어왔는지 보는 런타임 검사([03번 주제](../03-null-safe-types/)).

## 더 들어가면

- **`data class` 의 `copy`·`equals`·`componentN` 은 주 생성자 프로퍼티만 본다.** 몸통에 선언한 프로퍼티는 빠진다 —\
  (5)에서 본 「주 생성자 칸이 특별하다」의 또 다른 결과다. 정본은 목록의 **22번 주제**.
- **`companion object` 의 초기화**는 인스턴스 초기화와 다른 시점이다(클래스 초기화). 정본은 목록의 **25번 주제**.
- ★ **(6)을 정적으로 잡는 검사기**는 IDE 검사(`Calling non-final function in constructor`)로는 존재하지만\
  **`kotlinc` 자체는 이 문서의 두 프로그램에서 아무 경고도 내지 않았다.** 「IDE 가 잡아 주니 괜찮다」는 근거가 컴파일러에는 없다.
- ★ **이 문서는 `-jvm-target` 을 바꿔 찍어 보지 않았다.** (2)의 명령 순서가 21 타깃에서도 같은지는 **확인하지 않았다** —\
  `StringBuilder` 가 `invokedynamic` 으로 바뀌는 것만큼은 [02번 주제](../02-string-templates-and-raw-strings/)에서 이미 확인된 사실이다.
