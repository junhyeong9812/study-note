# kotlin/syntax/15 — 클래스 선언: 주 생성자·부 생성자·`init` 블록 순서 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러·예외·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javap` 에서 실제로 얻었다.\
> 역어셈블은 **기본 `-jvm-target`(1.8 · `major version: 52`)** 이 정본이다 —\
> 그래서 문자열 보간이 `StringBuilder` 로 보인다([02번 주제](../02-string-templates-and-raw-strings/)).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★ `1 → 2 → 3 → 4` — **선언한 자리 순서대로**, 부 생성자 몸통은 맨 나중

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

**왜 그런가**

- ★★ **프로퍼티 초기화식과 `init` 블록은 한 줄기다.** 「필드를 다 채운 뒤 `init`」이 **아니라**\
  소스에 적힌 순서대로 번갈아 돈다 — `1`(프로퍼티) → `2`(init) → `3`(프로퍼티) → `4`(init).
- ★ 부 생성자로 만들어도 **앞의 넷이 똑같이 먼저** 돌고 `5` 가 맨 나중이다.
- ★ `B` 에서 **처음부터 `tag=from-int-7`** 이 찍힌다. `this("from-int-$n")` 가 **주 생성자를 완주시킨 뒤**\
  부 생성자 몸통으로 돌아오기 때문이다. `tag` 는 그때 이미 채워져 있다.
- 그래서 **`init` 의 자리가 의미를 갖는다** — 위로 올리면 아래 프로퍼티를 못 읽는다(7번).

### 2. ★★★ 메서드는 생성자 하나 + 게터 셋 — `init` 은 **메서드가 아니다**

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

**왜 그런가**

- ★★★ **`<init>` 안에서 `putfield` 와 `println` 이 번갈아 나온다.**\
  `putfield first`(17) → `println "init A"`(21\~27) → `putfield second`(38) → `println "init B"`(42\~48).\
  **1번의 실행 순서가 명령 배치 그대로**다. 언어 규칙이지 우연이 아니다.
- ★ **`init` 블록은 별도 메서드가 아니다.** 호출도 이름도 없고 **생성자 안으로 복사**돼 있다 —\
  Java 의 인스턴스 초기화 블록과 같은 방식이다([`../../../java/syntax/06-initialization-order/`](../../../java/syntax/06-initialization-order/)).
- ★★ **`checkNotNullParameter` 가 `super.<init>()` 보다 앞**이다 — 오프셋 3 대 7.\
  널 검사가 **상위 생성자 호출 앞**에 온다. 같은 모양의 `order.kt` 가 실제로 로드돼 돌았으므로 검증기가 이 배치를 통과시킨다.
- `second = first + 1` 은 `aload_0; getfield first; iconst_1; iadd; putfield second`(32\~38)다 —\
  **위 프로퍼티를 읽는 것은 된다.**
- `nop` 은 초기화 구간 표시이지 계산이 아니다.

### 3. ★★ `Box(int)` 의 첫 일은 **`this("int-$n")`** — 안 쓰면 컴파일 에러

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

**왜 그런가**

- ★★ `Box(int)` 는 **`StringBuilder` 로 `"int-$n"` 을 만들고 곧바로 `invokespecial "<init>":(Ljava/lang/String;)V`** 를 부른다.\
  그 뒤에야 `putfield extra` 와 자기 `println` 이 온다.
- ★★ **`super.<init>()`·`putfield tag`·`init` 블록은 `Box(int)` 안에 없다.** 전부 `Box(String)` 쪽이다.\
  **초기화 코드가 한 군데뿐**이라는 뜻이다.
- 위임을 빼면 막힌다.

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

- ★ Java 는 `super()` 를 생략하면 **컴파일러가 암묵으로 넣어 준다.** Kotlin 은 주 생성자가 있으면\
  **`this(…)` 를 명시하라고 요구한다** — 「모든 생성이 주 생성자를 지난다」를 문법으로 강제하는 장치다.

### 4. ★ `F` 는 `1 → 2 → 3`, `G` 는 `1 → 2 → 3 → 4` — `1`·`2` 는 **한 번만**

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

**왜 그런가**

- ★★ **`Box(int)` 안에 `putfield a` 와 `init` 블록이 통째로 들어 있다.** 주 생성자가 없으니\
  초기화 코드를 얹을 자리가 없어 **각 생성자에 복사된 것**이다.
- ★ **`Box(String)` 에는 없다.** `this(s.length)` 로 위임했기 때문에 복사본을 안 받는다 —\
  그래서 `G` 에서도 `1`·`2` 가 **한 번만** 찍혔다.
- ★★ 위임하지 않는 부 생성자가 **둘이면 복사본도 둘**이다.

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

- `H`·`I` 가 각각 `프로퍼티 a → init 블록` 을 거친다. **같은 코드가 두 벌 존재한다.**\
  그래서 **주 생성자를 두는 편이 기본**이다(10번).

### 5. ★★ `init`·프로퍼티 초기화식에서는 보이고 **메서드·커스텀 게터에서는 안 보인다**

**출력** (`kotlinc param.kt -d oparam`)

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

**출력** (`kotlinc capture.kt -d ocap`)

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

**왜 그런가**

- ★★ **필드 목록에 `name` 이 없다.** `age`(`val` 을 붙였다)와 `upper`(몸통 프로퍼티)만 있다.\
  `name` 은 **`<init>` 의 지역 변수**이고 생성자가 끝나면 사라진다.
- ★ 그러니 나중에 부르는 `greet()` 가 볼 수 있을 리가 없다 — 에러는 **문법 제약이 아니라 물리적 사실**이다.
- ★ **커스텀 게터도 메서드다.** `val shout: String get() = name…` 이 똑같이 막힌 이유가 이것이다.
- ★ **람다가 잡아 가면 살아남는다.**

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

- 이때도 **`name` 필드는 안 생긴다.** 값은 `invokedynamic` 의 인자로 넘어가 **`Function0` 객체 안**에 남고,\
  클래스에는 그 객체를 담는 `f` 필드만 생긴다. `f$lambda$0(String)` 이 람다 본문이다.

### 6. ★★★ `label=null` · `len=0` — 널 불가 타입에 **널이 들어 있다**

**출력** (`java -cp oleak:kotlin-stdlib.jar LeakKt`)

```text
D 생성 중에 무엇이 찍히나
   Base.init — open 함수를 부른다 : Child(label=null, len=0)
E 다 만든 뒤       : Child(label=hello, len=5)
```

**왜 그런가**

- ★★★ `Child.<init>` 은 **`super.<init>()` 을 먼저** 부른다(2번에서 본 배치). 그 안에서 `Base` 의 `init` 이 돌고,\
  거기서 부른 `describe()` 는 **오버라이드된 `Child.describe()`** 다 — 그런데 **`putfield label` 은 아직 안 일어났다.**\
  그래서 JVM 기본값인 `null` 과 `0` 이 그대로 보인다.
- ★★ **컴파일러가 아무 말도 안 했다** — 경고도 에러도 없이 `exit 0` 이다.\
  「널 불가 타입에는 널이 없다」는 보장이 **이 한 구간에서 뚫린다**([03번 주제](../03-null-safe-types/)가 정본, 여기는 그 보장이 끝나는 자리).
- `E` 는 생성이 끝난 뒤라 정상이다 — **같은 함수가 시점에 따라 다른 답을 낸다.**
- ★ 값이 아니라 **예외**로 터지기도 한다.

**출력** (`java -cp oleak2:kotlin-stdlib.jar Leak2Kt`)

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

- 스택 트레이스가 경로를 그대로 보여 준다 — `Leak2Kt.main` → `Child.<init>` → `Base.<init>` → `Child.describe`.\
  **하위 생성자가 상위 생성자를 부르고, 상위가 하위 메서드를 다시 부른** 모양이다.
- ★ JVM 의 도움 되는 NPE 메시지가 원인을 지목한다 — `because "this.label" is null`.
- ★ 막는 법은 **상위 생성자·`init` 에서 `open` 멤버를 부르지 않는 것**이다.\
  Kotlin 이 클래스·멤버를 기본 `final` 로 둔 것이 이 구멍을 좁히는 장치다(목록의 **19번 주제**).

### 7. `variable 'later' must be initialized` — 이쪽은 **컴파일러가 잡는다**

**출력** (`kotlinc forward.kt -d ofw`)

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

**왜 그런가**

- ★★ **6번과 정확히 대비된다.** 같은 클래스 안에서 앞뒤가 뒤집힌 것은 컴파일러가 보고,\
  **상속을 거쳐 뒤집힌 것은 못 본다.** 후자는 하위 클래스가 무엇을 오버라이드할지 알 수 없기 때문이다.
- 그래서 **`init` 은 읽을 프로퍼티보다 아래에 둔다.** 자리가 곧 순서다(1번).
- ★ **반대 방향은 된다** — 아래 프로퍼티가 위 프로퍼티를 읽는 것은 정상이다(2번의 `second = first + 1`).

### 8. 필드는 **둘**(`age`·`upper`) — 그래서 에러가 물리적 사실이다

**왜 그런가**

- `javap -p -s` 기준 필드는 `private final int age` 와 `private final String upper` **둘**이다.\
  게터는 `getAge()`·`getUpper()` 가 생기고 **`name` 에 대응하는 것은 아무것도 없다.**
- ★ **`val`/`var` 를 붙이는 것이 「필드를 만들라」는 지시**다. 안 붙이면 **생성자 파라미터일 뿐**이다.
- ★ 그래서 5번의 에러는 「Kotlin 이 금지해서」가 아니라 「**저장한 곳이 없어서**」다.
- ★★ `data class` 의 `copy`·`equals`·`componentN` 이 **주 생성자 프로퍼티만 보는 것**도 같은 뿌리다 —\
  주 생성자 칸이 **그 클래스의 「값」을 정의하는 자리**이기 때문이다(정본은 목록의 **22번 주제**).

### 9. `= 0` 은 `putfield` 가 **안 나온다** — 최적화지 언어 보장이 아니다

**출력** (`javap -c -p osec99/Box.class` — `= 99` 로만 바꾼 판)

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

**왜 그런가**

- 3번의 `sec.kt`(`= 0`)에는 주 생성자에 **`putfield extra` 가 없다.** `99` 로 바꾼 이 판에는\
  `15: aload_0 / 16: bipush 99 / 18: putfield extra:I` 가 나타난다.
- ★ **JVM 이 필드를 0/`null` 로 초기화해 주므로 컴파일러가 대입을 생략**한 것이다.
- ★★ 그래서 **초기화 순서를 `putfield` 개수로 세면 0 으로 초기화한 필드에서 어긋난다.**\
  세려면 **0 이 아닌 값**으로 두고 찍어야 한다 — 이 문서의 `icode.kt` 가 `1`·`first + 1` 을 쓴 이유다.
- 이것은 **이 컴파일러의 최적화**이고 언어가 약속한 바가 아니다.

### 10. 주 생성자가 있으면 참, 없으면 **그런 것이 아예 없다**

**왜 그런가**

| 경우 | 「모든 생성이 주 생성자를 지난다」 | 초기화 코드의 물리적 위치 |
|---|---|---|
| 주 생성자 있음 | **참** — 부 생성자는 `this(…)` 강제 | 주 생성자 `<init>` **한 군데** |
| 주 생성자 없음 | 성립하지 않는다(지날 것이 없다) | **위임 안 한 부 생성자마다 한 벌씩** |

- ★ 주 생성자가 없으면 **초기화 코드가 복사돼 여러 벌 존재한다**(4번).\
  코드가 커질수록 클래스 파일이 커지고, **한쪽만 고치는 실수**가 생긴다.
- ★ 그래서 기본은 **주 생성자를 두고 변형은 부 생성자나 기본 인자로 얹는 것**이다\
  (기본 인자 쪽이 더 싼 경우가 많다 — [08번 주제](../08-function-declaration-default-and-named-args/)).

### 11. `init` = Java 인스턴스 초기화 블록 · 다른 것은 **주 생성자라는 칸**

**왜 그런가**

| | Java | Kotlin |
|---|---|---|
| 필드 초기화식 + 초기화 블록 | 선언 순서대로, **생성자 안으로 복사** | 같다 — `init` 이 그 자리 |
| 생성자 위임 | `this(…)` / `super(…)` · **`super()` 는 암묵 삽입** | 주 생성자가 있으면 **`this(…)` 명시 강제** |
| 「입구가 하나」라는 개념 | 없다 — 생성자마다 독립 | **주 생성자**가 유일한 입구 |
| 생성 중 오버라이드 호출 함정 | 있다 | **있다** — 게다가 널 불가 타입이 널을 낸다 |
| 그 함정을 좁히는 장치 | 없음(관례로 피한다) | **클래스·멤버가 기본 `final`**(목록의 **19번 주제**) |

- ★ Kotlin 이 더한 것은 **「주 생성자」라는 칸 하나**다. 그 칸이 ① 초기화를 한 군데로 모으고\
  ② `val`/`var` 한 글자로 필드를 만들고 ③ `data class` 의 「값」 범위를 정한다.
- ★ **더한 것이 아니라 그대로 물려받은 것도 있다** — 6번의 함정이다. JVM 의 생성 순서에서 오는 것이라\
  **언어가 문법으로 없앨 수 없다.** Kotlin 은 **기본값을 `final` 로 두어 표면을 줄였을 뿐**이다.
- 정본 대비는 [`../../../java/syntax/06-initialization-order/`](../../../java/syntax/06-initialization-order/)(순서)와\
  [`../../../java/syntax/07-constructors/`](../../../java/syntax/07-constructors/)(`super()` 한 줄의 앞뒤)다.

## 실행 검증

```text
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
openjdk version "21.0.5" 2024-10-15 LTS
OpenJDK Runtime Environment Temurin-21.0.5+11 (build 21.0.5+11-LTS)
OpenJDK 64-Bit Server VM Temurin-21.0.5+11 (build 21.0.5+11-LTS, mixed mode, sharing)
```

★ **흔들리는 칸과 안 흔들리는 칸**(제출 전 재대조에서 「고칠 것」과 「설계상 다른 것」을 가르는 선언이다)

| 흔들린다 | 안 흔들린다 |
|---|---|
| **없다** — 이 문서의 블록은 전부 결정적이다 | `javap` 출력 **전체** · `leak2.kt` 스택 트레이스의 **프레임 다섯 줄 전부**(전부 사용자 프레임이라 JVM 내부 프레임·해시코드가 섞이지 않았다) · 예외 타입과 메시지 본문 · 에러 문구 · 종료 코드 |

> 근거 — **캡처 스크립트를 두 번 돌려 블록 82개를 바이트 단위로 대조**했고, 이 주제의 블록은 한 글자도 안 갈렸다.\
> ★ 스택 트레이스를 싣는 블록에서는 보통 **JVM 내부 프레임과 객체 해시코드**가 흔들리는데,
> `leak2.kt` 는 `main` 에서 생성자 하나만 부르므로 그 둘이 **애초에 안 나온다.**

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `order.kt` | `A`·`B` — **선언 순서대로** 도는 것 · 부 생성자 몸통이 맨 나중인 것 | `kotlinc` → `java` |
| `icode.kt` | `<init>` **하나**에 `putfield`·`println` 이 번갈아 박히는 것 · 널 검사가 `super` 앞인 것 | `kotlinc` → `javap -c -p -s` |
| `sec.kt` | 부 생성자의 첫 일이 `this(…)` 인 것 · 초기화가 **주 생성자에만** 있는 것 | `kotlinc` → `javap -c -p` |
| `sec99.kt` | **`= 0` 이 생략되고 `= 99` 는 나오는 것** | `kotlinc` → `javap -c -p` |
| `nodelegate.kt` | 위임을 빼면 **`primary constructor call expected`** | `kotlinc` (컴파일 실패가 결과) |
| `noprimary.kt` | `F`·`G` — 주 생성자가 없으면 **각 생성자에 복사**되는 것 | `kotlinc` → `java` · `javap -c -p` |
| `twosec.kt` | `H`·`I` — 위임 안 한 생성자가 둘이면 **복사본도 둘** | `kotlinc` → `java` |
| `param.kt` · `capture.kt` | 주 생성자 파라미터가 **메서드·커스텀 게터에서 안 보이는 것**(에러 각 1건) | `kotlinc` 2회 (컴파일 실패가 결과) |
| `param2.kt` | 필드 목록에 **`name` 이 없는 것** | `kotlinc` → `javap -p -s` |
| `capture2.kt` | 람다가 잡으면 **`Function0` 안에** 남는 것(`C`) | `kotlinc` → `javap -p -s` · `java` |
| `leak.kt` | `D`·`E` — **널 불가 타입이 `null`**, `Int` 가 `0` · **경고 0건** | `kotlinc` → `java` |
| `leak2.kt` | 같은 구멍이 **NPE 로 터지는 것**과 그 스택 트레이스 | `kotlinc` → `java` (`exit 1` 이 결과) |
| `forward.kt` | 같은 클래스 안 전방 참조는 **컴파일러가 잡는 것** | `kotlinc` (컴파일 실패가 결과) |

**구현 의존 항목** — 오프셋·상수 풀 번호, `nop` 의 자리, `checkNotNullParameter` 가 `super.<init>` 앞이라는 배치,
`= 0` 대입 생략, 람다가 `invokedynamic`/`Function0` 로 내려가는 것, `f$lambda$0` 이라는 이름,
에러·예외 문구 — **전부 이 컴파일러·JDK 버전의 산출물**이다.\
반면 **「선언 순서대로 돈다」·「부 생성자는 주 생성자를 거친다」·「부 생성자 몸통이 맨 나중이다」·
「`val` 없는 파라미터는 필드가 아니다」·「주 생성자 파라미터는 초기화 구간에서만 보인다」·
「상위 생성자가 하위 필드보다 먼저 돈다」** 는 **언어·JVM 규칙**이라 타깃과 무관하다.

**★ 던져 봤더니 예상과 달랐던 것 — 세 건**

1. ★★★ **`checkNotNullParameter` 가 `super.<init>()` 보다 앞에 있었다.** 「`super()` 는 생성자의 첫 문장」이라는
   Java 의 상식대로면 널 검사가 뒤에 와야 하는데, 오프셋 3 에 검사가 있고 7 에 `super` 가 있다.
   `this` 를 안 건드리는 명령이라 검증기가 통과시킨다 — **같은 모양이 실제로 로드돼 돌았다.**
2. ★★ **`var extra: Int = 0` 이 바이트코드에서 통째로 사라졌다.** 「초기화식을 쓰면 `putfield` 가 나온다」가
   **0 에서는 거짓**이었다. `99` 로 바꾸니 나타났다 — **순서를 명령 개수로 세려던 계획이 여기서 깨질 뻔했다.**
3. ★ **전방 참조는 잡히는데 상속 경유는 안 잡힌다.** 같은 「초기화 전에 읽기」인데
   `forward.kt` 는 컴파일 에러이고 `leak.kt` 는 **경고조차 없이 통과**했다.
   컴파일러가 못 보는 것은 **하위 클래스가 무엇을 오버라이드할지**이지 순서 자체가 아니다.

**안 걸린 것도 출력이다** — `leak.kt` 는 널 불가 프로퍼티에서 `null` 을 꺼내 찍는데도
**경고 0건 · `exit 0`** 이었다. 이 갈래에서 「컴파일이 됐다」가 가장 약한 근거인 자리다.
