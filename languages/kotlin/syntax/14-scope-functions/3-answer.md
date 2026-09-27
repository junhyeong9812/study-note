# kotlin/syntax/14 — scope function 5종: `let`/`run`/`with`/`apply`/`also` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러·경고·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javap` 에서 실제로 얻었다.\
> 역어셈블은 **기본 `-jvm-target`(1.8 · `major version: 52`)** 이 정본이고, 람다 전략은 **기본값과 `-Xlambdas=class` 둘 다** 찍었다.\
> **stdlib 쪽 출력은 `kotlin-stdlib.jar` 를 풀어 직접 역어셈블한 것**이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★ 셋은 `String`, 둘은 `Cup` — 축은 둘이고 칸은 **넷**이다

**출력** (`java -cp oscope:kotlin-stdlib.jar ScopeKt`)

```text
A let   : Cup(1ml)   (타입 String)
B run   : Cup(2ml)   (타입 String)
C with  : Cup(3ml)   (타입 String)
D apply : Cup(4ml)   (타입 Cup)
E also  : Cup(5ml)   (타입 Cup)
F apply 가 돌려준 것이 그 객체인가 : true
G also  가 돌려준 것이 그 객체인가 : true
```

**왜 그런가**

- **축 ①은 수신자 형태다.** `let`·`also` 는 `it` 이라는 **인자**로 받고, `run`·`with`·`apply` 는 **`this`** 로 받는다.\
  소스에서 `it.ml` 과 그냥 `ml` 로 갈려 있는 것이 그 표시다.
- **축 ②는 반환값이다.** `let`·`run`·`with` 는 **람다의 마지막 식**을 돌려주고(`String`),\
  `apply`·`also` 는 **수신자 자체**를 돌려준다(`Cup`).
- `F`·`G` 가 `true` 인 것은 `apply`/`also` 가 **새 객체를 만들지 않는다**는 뜻이다 — 받은 참조를 그대로 낸다.
- 축 둘이면 칸은 넷인데 함수는 다섯이다. **`run` 과 `with` 가 같은 칸**이다(9번).

| | 수신자를 `this` 로 | 수신자를 `it` 으로 |
|---|---|---|
| **람다 결과**를 돌려준다 | `run` · `with` | `let` |
| **수신자**를 돌려준다 | `apply` | `also` |

### 2. ★ 에러 **2건** — 둘 다 `unresolved reference`

**출력** (`kotlinc badrecv.kt -d obad`)

```text
===== 소스: badrecv.kt =====
class Cup(var ml: Int)

fun main() {
    val cup = Cup(100)
    cup.apply { it.ml = 1 }
    cup.let { ml = 2 }
}
===== kotlinc badrecv.kt =====
badrecv.kt:5:17: error: unresolved reference 'it'.
    cup.apply { it.ml = 1 }
                ^^
badrecv.kt:6:15: error: unresolved reference 'ml'.
    cup.let { ml = 2 }
              ^^
(exit 1)
```

**왜 그런가**

- `apply` 의 람다는 **수신자 지정 람다**(`Cup.() -> Unit`)라 **파라미터가 없다.** 그래서 `it` 이라는 이름이 아예 없다.
- `let` 의 람다는 **보통 람다**(`(Cup) -> R`)라 수신자가 `this` 가 아니다. 그래서 `ml` 을 바로 못 쓴다.
- ★ **컴파일러가 확실히 막아 주는 축은 이 「수신자 이름」 하나뿐**이다.\
  반환값 축은 **타입이 안 맞을 때만** 걸리고, 타입이 우연히 맞으면 조용히 통과한다(4번 `X`).

### 3. ★★ `none`·`none`·`len=3`·`none`·`none`·`1` — 검사하는 것은 **`?.`** 다

**출력** (`java -cp onull:kotlin-stdlib.jar NullsafeKt`)

```text
H oldWay(null)        : none
I newWay(null)        : none
J newWay("abc")       : len=3
K letWithoutQ(null)   : none
L runQ(null)          : none
M 람다가 몇 번 돌았나  : 1
```

**왜 그런가**

- ★★ **`K` 가 컴파일된다는 것 자체가 답이다.** `s.let { … }` 는 `?.` 가 없으므로 **`s` 가 null 이어도 람다가 돈다.**\
  그래서 람다 안에서 `it == null` 을 직접 검사해야 했다 — `let` 은 널을 모른다.
- ★ **`M` 이 `1`** 이다. `?.let` 을 두 번 걸었는데 람다는 **널이 아닌 쪽에서만** 돌았다.\
  막은 것은 `?.` 이고 `let` 은 그냥 불렸을 뿐이다.
- `let` 안의 `it` 은 **비-null 타입**이다. `?.` 를 통과했다는 사실이 타입에 반영되므로 `it.length` 에 `?.` 가 필요 없다.
- `L` 이 되는 것은 **`run` 이 확장 함수**여서다 — `s?.run { }` 처럼 점을 찍을 수 있다. `with` 는 안 된다(8번).
- ★ **`H` 와 `I` 의 출력이 같다.** 바꿔 써서 얻는 것은 동작이 아니라 **문장이 식이 되는 것**이다 —\
  단일식 함수로 줄고, `val x = …` 의 오른쪽에 그대로 놓을 수 있다.

### 4. ★★ `FALLBACK`·`kim`·**`FALLBACK`** — `?:` 는 「수신자가 널인가」를 안 본다

**출력** (`java -cp otrap:kotlin-stdlib.jar TrapKt`)

```text
U 널 행         : FALLBACK
V 이름 있는 행   : kim
W 이름이 널인 행 : FALLBACK
X apply 가 돌려준 것 : StringBuilder
Y also 의 값 : 10   side : 20
```

**왜 그런가**

- ★★ `W` 의 `r` 은 **널이 아니다.** `Row(2, null)` 이다. 그런데 `FALLBACK` 이 나왔다.\
  `?:` 가 보는 것은 **`r?.let { it.name }` 이라는 식 전체의 결과**이고, 그 결과가 `null` 이기 때문이다.
- 그래서 `?.let { } ?: 기본값` 은 **조건이 둘**이다 — ① 수신자가 널이거나 ② **람다가 널을 돌려주거나.**\
  ①만 원하면 `if`/`when` 으로 적어야 한다.
- ★ `X` 가 `StringBuilder` 인 것은 **`apply` 의 람다 반환 타입이 `Unit`** 이기 때문이다.\
  람다 마지막에 `length` 를 뒀지만 **아무도 안 받는다.** 값이 필요하면 `run` 이다.
- `Y` 에서 값은 `10` 그대로 흐르고 `side` 만 `20` 이 됐다 — `also` 가 **부수 효과 전용**인 모양 그대로다.

### 5. ★ 경고는 **1건**뿐 — `it` 이 가려지는 쪽은 조용하다

**출력** (`kotlinc nest.kt -d onest`)

```text
===== 소스: nest.kt =====
class Outer(val name: String) { fun who(): String = "Outer($name)" }
class Inner(val name: String) { fun who(): String = "Inner($name)" }

fun main() {
    val o = Outer("O")
    val i = Inner("I")

    o.apply {
        println("P 바깥 apply 의 this : ${who()}")
        i.apply {
            println("Q 안쪽 apply 의 this : ${who()}")
            println("R this@apply 는      : ${this@apply.who()}")
        }
    }

    o.apply outer@ {
        i.apply {
            println("S this@outer 는      : ${this@outer.who()}")
        }
    }

    "AB".let {
        "CD".let {
            println("T 안쪽 it 은         : $it")
        }
    }
}
===== kotlinc nest.kt =====
nest.kt:12:50: warning: there is more than one label with such a name in this scope.
            println("R this@apply 는      : ${this@apply.who()}")
                                                 ^^^^^^
(exit 0)
```

**출력** (`java -cp onest:kotlin-stdlib.jar NestKt`)

```text
P 바깥 apply 의 this : Outer(O)
Q 안쪽 apply 의 this : Inner(I)
R this@apply 는      : Inner(I)
S this@outer 는      : Outer(O)
T 안쪽 it 은         : CD
```

**왜 그런가**

- 안쪽 `apply` 의 `this` 가 바깥 `this` 를 **가린다.** 그래서 `Q` 가 `Inner(I)` 다.
- ★★ **`R` 도 `Inner(I)` 다.** 암묵 라벨은 **람다를 받는 함수 이름**에서 오므로 `apply` 를 중첩하면 **라벨이 이름째 겹친다.**\
  컴파일러는 「이 스코프에 그 이름의 라벨이 둘 이상」이라고 경고하지만 **에러가 아니다** — `exit 0` 으로 통과한다.
- ★ 고치는 법은 **람다에 라벨을 직접 다는 것**이다(`o.apply outer@ { … }`). 그러면 `this@outer` 가 바깥에 닿는다(`S`).
- ★★ **`T` 쪽은 경고가 없다.** 안쪽 `it` 이 바깥 `it` 을 조용히 가렸고 이 파일의 경고는 `this@apply` **한 건뿐**이었다.\
  **더 나쁜 쪽이 경고가 없다** — 그래서 중첩할 때는 `let { row -> … }` 처럼 **이름을 준다.**

### 6. ★★★ 인라인 쪽은 `Function1` 이 **0회** — 개수만 세면 못 가른다

**출력** (클래스 파일 개수 · `Function1` 등장 횟수 · 플래그)

```text
$ find oinl -name "*.class" | sort          # 기본값 — scope function 5종
oinl/Cup.class
oinl/InlKt.class
$ find oinlc -name "*.class" | sort         # 같은 파일을 -Xlambdas=class 로
oinlc/Cup.class
oinlc/InlKt.class
$ find ononinl -name "*.class" | sort       # 기본값 — 인라인 아닌 고차 함수
ononinl/Cup.class
ononinl/NoninlKt.class
$ find ononinlc -name "*.class" | sort      # 같은 파일을 -Xlambdas=class 로
ononinlc/Cup.class
ononinlc/NoninlKt$five$a$1.class
ononinlc/NoninlKt$five$b$1.class
ononinlc/NoninlKt.class
$ javap -v -p oinl/InlKt.class | grep -c Function1
0
$ javap -v -p ononinl/NoninlKt.class | grep -c Function1
23
$ javap -v -p ononinl/NoninlKt.class | grep -c ACC_SYNTHETIC
0
$ javap -v -p oinl/InlKt.class | grep -E "major version"
  major version: 52
```

**출력** (`javap -v -p ononinl/NoninlKt.class` — 람다 메서드의 플래그)

```text
  private static final int five$lambda$0(Cup);
    descriptor: (LCup;)I
    flags: (0x001a) ACC_PRIVATE, ACC_STATIC, ACC_FINAL
    Code:
```

**출력** (`javap -c -p oinl/InlKt.class`)

```text
Compiled from "inl.kt"
public final class InlKt {
  public static final int five(Cup);
    Code:
       0: aload_0
       1: ldc           #9                  // String cup
       3: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_0
       7: astore_3
       8: iconst_0
       9: istore        4
      11: aload_3
      12: invokevirtual #21                 // Method Cup.getMl:()I
      15: iconst_1
      16: iadd
      17: nop
      18: istore_1
      19: aload_0
      20: astore        4
      22: iconst_0
      23: istore        5
      25: aload         4
      27: invokevirtual #21                 // Method Cup.getMl:()I
      30: iconst_2
      31: iadd
      32: nop
      33: istore_2
      34: aload_0
      35: astore        4
      37: iconst_0
      38: istore        5
      40: aload         4
      42: invokevirtual #21                 // Method Cup.getMl:()I
      45: iconst_3
      46: iadd
      47: nop
      48: istore_3
      49: aload_0
      50: astore        5
      52: aload         5
      54: astore        6
      56: iconst_0
      57: istore        7
      59: aload         6
      61: aload         6
      63: invokevirtual #21                 // Method Cup.getMl:()I
      66: iconst_4
      67: iadd
      68: invokevirtual #25                 // Method Cup.setMl:(I)V
      71: aload         5
      73: invokevirtual #21                 // Method Cup.getMl:()I
      76: istore        4
      78: aload_0
      79: astore        6
      81: aload         6
      83: astore        7
      85: iconst_0
      86: istore        8
      88: aload         7
      90: aload         7
      92: invokevirtual #21                 // Method Cup.getMl:()I
      95: iconst_5
      96: iadd
      97: invokevirtual #25                 // Method Cup.setMl:(I)V
     100: aload         6
     102: invokevirtual #21                 // Method Cup.getMl:()I
     105: istore        5
     107: iload_1
     108: iload_2
     109: iadd
     110: iload_3
     111: iadd
     112: iload         4
     114: iadd
     115: iload         5
     117: iadd
     118: ireturn
}
```

**출력** (`javap -c -p ononinl/NoninlKt.class`)

```text
Compiled from "noninl.kt"
public final class NoninlKt {
  public static final <T, R> R myLet(T, kotlin.jvm.functions.Function1<? super T, ? extends R>);
    Code:
       0: aload_1
       1: ldc           #10                 // String f
       3: invokestatic  #16                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_1
       7: aload_0
       8: invokeinterface #22,  2           // InterfaceMethod kotlin/jvm/functions/Function1.invoke:(Ljava/lang/Object;)Ljava/lang/Object;
      13: areturn

  public static final int five(Cup);
    Code:
       0: aload_0
       1: ldc           #29                 // String cup
       3: invokestatic  #16                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_0
       7: invokedynamic #46,  0             // InvokeDynamic #0:invoke:()Lkotlin/jvm/functions/Function1;
      12: invokestatic  #48                 // Method myLet:(Ljava/lang/Object;Lkotlin/jvm/functions/Function1;)Ljava/lang/Object;
      15: checkcast     #50                 // class java/lang/Number
      18: invokevirtual #54                 // Method java/lang/Number.intValue:()I
      21: istore_1
      22: aload_0
      23: invokedynamic #59,  0             // InvokeDynamic #1:invoke:()Lkotlin/jvm/functions/Function1;
      28: invokestatic  #48                 // Method myLet:(Ljava/lang/Object;Lkotlin/jvm/functions/Function1;)Ljava/lang/Object;
      31: checkcast     #50                 // class java/lang/Number
      34: invokevirtual #54                 // Method java/lang/Number.intValue:()I
      37: istore_2
      38: iload_1
      39: iload_2
      40: iadd
      41: ireturn

  private static final int five$lambda$0(Cup);
    Code:
       0: aload_0
       1: ldc           #65                 // String it
       3: invokestatic  #16                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_0
       7: invokevirtual #70                 // Method Cup.getMl:()I
      10: iconst_1
      11: iadd
      12: ireturn

  private static final int five$lambda$1(Cup);
    Code:
       0: aload_0
       1: ldc           #65                 // String it
       3: invokestatic  #16                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_0
       7: invokevirtual #70                 // Method Cup.getMl:()I
      10: iconst_2
      11: iadd
      12: ireturn
}
```

**왜 그런가**

- ★★★ **결정적인 숫자는 개수가 아니라 `Function1` 등장 횟수다.** 인라인 쪽 0회, 인라인 아닌 쪽 23회.\
  상수 풀까지 포함한 숫자이므로 **함수 타입의 흔적이 클래스 파일 어디에도 없다**는 뜻이다.
- ★ **기본값에서는 둘 다 2개**다. Kotlin 2.x 의 기본 람다 전략이 **`invokedynamic`** 이라\
  람다가 **클래스가 아니라 `private static final` 메서드 + `LambdaMetafactory`** 로 내려가기 때문이다.\
  **그래서 「클래스 파일이 안 늘었으니 인라인됐다」는 틀린 추론이다.**
- ★★ **`-Xlambdas=class` 를 주면 갈린다** — `inl.kt` 는 2개 그대로, `noninl.kt` 는 **4개**(`NoninlKt$five$a$1`·`$b$1`).\
  만들 람다 객체가 애초에 없는 쪽과 있는 쪽의 차이가 여기서 눈에 보인다.
- ★ **`ACC_SYNTHETIC` 은 0건이다.** `five$lambda$0` 의 플래그는 `(0x001a) ACC_PRIVATE, ACC_STATIC, ACC_FINAL` 이다 —\
  **이 판의 관찰**이고 언어 보장이 아니다.
- 인라인 쪽 본문에는 **`Cup.getMl`·`Cup.setMl` 말고 호출이 없다.** 다섯 함수 이름이 한 번도 안 나온다.\
  중간의 `nop`·`iconst_0; istore` 는 **인라인된 구간 표시**이지 계산이 아니다.
- 인라인 아닌 쪽은 람다마다 `invokedynamic` → `invokestatic myLet` → **`checkcast Number` → `intValue`** 가 반복된다.\
  제네릭 `R` 가 `Object` 로 소거돼 **`Int` 가 박싱됐다 풀리는 것**이다([12번 주제](../12-reified-type-parameters/)).
- ★ **이 문서는 속도를 재지 않았다.** 보인 것은 **명령이 있느냐 없느냐**라는 구조뿐이다.

### 7. ★ 경고가 **안 난다** — 셋 다 조용하다

**출력** (`kotlinc unusedit.kt` 와 실행)

```text
===== 소스: unusedit.kt =====
class Cup(var ml: Int)

fun main() {
    val cup = Cup(100)
    cup.also { println("also 안인데 it 을 안 쓴다") }
    cup.let { println("let 안인데 it 을 안 쓴다") }
    cup.apply { println("apply 안") }
    val n: Int = cup.let { 7 }
    println("N : $n")
}
===== kotlinc unusedit.kt =====
(exit 0)
===== java -cp ounused:kotlin-stdlib.jar UnuseditKt =====
also 안인데 it 을 안 쓴다
let 안인데 it 을 안 쓴다
apply 안
N : 7
```

**왜 그런가**

- **경고 0건에 `exit 0`** 이다. `also`·`let`·`apply` 어느 쪽도 「`it` 을 안 썼다」고 말하지 않는다.
- ★ 「안 걸린 것도 출력이다」 — **컴파일러가 안 막아 준다**는 사실이지 **그렇게 써도 된다**는 뜻이 아니다.
- `it` 을 안 쓰는 `also` 는 **값이 흐르는 자리에 문장을 끼워 넣은 것**이라, 값이 안 필요하면 그냥 문장으로,\
  블록이 필요하면 **수신자 없는 `run { }`** 으로 적는 편이 읽기 낫다.
- `N : 7` 은 `let` 의 반환 타입 `R` 가 수신자와 무관한 자유 타입 파라미터라는 것이다.

### 8. `with` 만 확장이 아니다 — 에러는 **`length`** 를 지목한다

**출력** (`kotlinc badwith.kt -d obw`)

```text
===== 소스: badwith.kt =====
fun f(s: String?): Int = with(s) { length }
===== kotlinc badwith.kt =====
badwith.kt:1:36: error: only safe (?.) or non-null asserted (!!.) calls are allowed on a nullable receiver of type 'String?'.
fun f(s: String?): Int = with(s) { length }
                                   ^^^^^^
(exit 1)
```

**왜 그런가**

- ★★ 에러가 `with` 가 아니라 **람다 안의 `length`** 에 붙는다. `with(s)` 호출 자체는 통과했고,\
  **`T` 가 `String?` 로 추론돼 람다 안의 `this` 가 nullable** 이 된 것이 문제다.\
  그래서 **원인과 증상의 자리가 다르다** — 이 에러가 안 읽히는 이유다.
- `run` 은 **확장 함수**(`fun <T, R> T.run(...)`)라 **`s?.run { … }`** 으로 쓸 수 있다(3번 `L`).\
  `with` 는 **최상위 함수**(`fun <T, R> with(receiver: T, ...)`)라 **점을 찍을 자리가 없다.**
- ★ 같은 칸에 있는 둘을 실제로 가르는 기준이 이것이다 — **「널일 수 있나」와 「체인 중간에 끼나」.**\
  둘 다 아니면 **아무거나 써도 결과가 같다.**

### 9. ★★ `run` 과 `with` — 디스크립터가 **한 글자도 같다**

**출력** (`javap -p -s kotlin/StandardKt__StandardKt.class` — 다섯 부분만)

```text
  private static final <R> R run(kotlin.jvm.functions.Function0<? extends R>);
    descriptor: (Lkotlin/jvm/functions/Function0;)Ljava/lang/Object;

  private static final <T, R> R run(T, kotlin.jvm.functions.Function1<? super T, ? extends R>);
    descriptor: (Ljava/lang/Object;Lkotlin/jvm/functions/Function1;)Ljava/lang/Object;

  private static final <T, R> R with(T, kotlin.jvm.functions.Function1<? super T, ? extends R>);
    descriptor: (Ljava/lang/Object;Lkotlin/jvm/functions/Function1;)Ljava/lang/Object;

  private static final <T> T apply(T, kotlin.jvm.functions.Function1<? super T, kotlin.Unit>);
    descriptor: (Ljava/lang/Object;Lkotlin/jvm/functions/Function1;)Ljava/lang/Object;

  private static final <T> T also(T, kotlin.jvm.functions.Function1<? super T, kotlin.Unit>);
    descriptor: (Ljava/lang/Object;Lkotlin/jvm/functions/Function1;)Ljava/lang/Object;

  private static final <T, R> R let(T, kotlin.jvm.functions.Function1<? super T, ? extends R>);
    descriptor: (Ljava/lang/Object;Lkotlin/jvm/functions/Function1;)Ljava/lang/Object;
```

**왜 그런가**

- `run(T, Function1)` 과 `with(T, Function1)` 이 둘 다 `(Ljava/lang/Object;Lkotlin/jvm/functions/Function1;)Ljava/lang/Object;` 다.\
  **`let` 까지 합치면 셋이 같다.**
- ★★ Kotlin 에서 뜻이 갈리는 이유는 **`T.() -> R` 와 `(T) -> R` 의 구분이 JVM 디스크립터에 없기 때문**이다.\
  그 구분은 **`kotlin.Metadata` 와 `@kotlin.ExtensionFunctionType` 이라는 타입 애너테이션**에만 있다.
- ★ 그래서 **Java 에서는 그 둘을 구분할 수단이 없다.** 애초에 다섯은 `@InlineOnly` 라 **Java 에서 부를 수도 없다**(10번).
- `run` 의 오버로드가 둘인 것도 보인다 — `run(Function0)` 은 **수신자 없는 형태**(`run { … }`)다.

### 10. `private` 이고 `@InlineOnly` 다 — 0번 슬롯 이름이 `$this$apply`

**출력** (`javap -v -p kotlin/StandardKt__StandardKt.class` — `apply` 부분만)

```text
  private static final <T extends java.lang.Object> T apply(T, kotlin.jvm.functions.Function1<? super T, kotlin.Unit>);
    descriptor: (Ljava/lang/Object;Lkotlin/jvm/functions/Function1;)Ljava/lang/Object;
    flags: (0x001a) ACC_PRIVATE, ACC_STATIC, ACC_FINAL
    Code:
      stack=2, locals=2, args_size=2
         0: aload_1
         1: ldc           #47                 // String block
         3: invokestatic  #22                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
         6: aload_1
         7: aload_0
         8: invokeinterface #61,  2           // InterfaceMethod kotlin/jvm/functions/Function1.invoke:(Ljava/lang/Object;)Ljava/lang/Object;
        13: pop
        14: aload_0
        15: areturn
      LineNumberTable:
        line 87: 6
        line 88: 14
      LocalVariableTable:
        Start  Length  Slot  Name   Signature
            0      16     0 $this$apply   Ljava/lang/Object;
            0      16     1 block   Lkotlin/jvm/functions/Function1;
    Signature: #68                          // <T:Ljava/lang/Object;>(TT;Lkotlin/jvm/functions/Function1<-TT;Lkotlin/Unit;>;)TT;
    RuntimeVisibleAnnotations:
      0: #45()
        kotlin.IgnorableReturnValue
    RuntimeInvisibleAnnotations:
      0: #7()
        kotlin.internal.InlineOnly
```

**왜 그런가**

- ★ **`flags: (0x001a) ACC_PRIVATE, ACC_STATIC, ACC_FINAL`** 이다. `public` 이 아니다.\
  `kotlin.internal.InlineOnly` 가 「**인라인으로만 존재한다**」는 표시이고, 그래서 **Java 가 못 본다.**
- **`kotlin.IgnorableReturnValue`** 는 「반환값을 안 써도 경고하지 않는다」는 표시다.\
  다섯에 전부 붙어 있고 `takeIf`·`takeUnless` 에는 없다 — 그쪽은 결과를 버리면 의미가 없기 때문이다.
- ★ **`LocalVariableTable` 의 0번 슬롯이 `$this$apply`** 다. **수신자가 0번 파라미터**라는\
  [13번 주제](../13-extension-functions-and-properties/)의 사실이 stdlib 쪽에서도 그대로 보인다.
- 본문은 세 명령이 전부다 — `block.invoke(this)` · `pop` · `this` 반환. `apply` 의 정의가 바이트코드로 적혀 있다.

### 11. 확장이라서 `?.` 가 되고, 인라인이라서 **아무것도 안 남는다**

**왜 그런가**

| 사실 | 따라 나오는 성질 | 정본 |
|---|---|---|
| 다섯이 **확장 함수**다(`with` 만 예외) | `?.` 를 붙일 수 있다 · 수신자가 0번 파라미터다 · 임포트 없이 쓴다(`kotlin` 패키지) | [13번 주제](../13-extension-functions-and-properties/) |
| 다섯이 **`inline`** 이다 | 함수 객체가 안 생긴다 · 람다 안에서 비지역 `return` 이 된다 · `Function1` 이 0회다 | [11번 주제](../11-inline-functions/) |
| 다섯이 **수신자 지정 람다**를 받는다(셋) | 중첩하면 `this` 가 가려진다 · DSL 의 재료가 된다 | [10번 주제](../10-lambdas-and-higher-order-functions/) |

- ★ **「인라인이라 빠르다」는 이 주제가 증명한 것이 아니다.** 증명한 것은 「**`Function1` 이 클래스 파일에 0회 나온다**」는 구조 사실이다.\
  속도는 재지 않았고, 인라인의 대가(코드 크기·제약)는 [11번 주제](../11-inline-functions/)가 정본이다.
- 수신자 지정 람다를 **깊게 쌓아 DSL** 을 만드는 법은 [목록의 **37번 주제**](../37-lambdas-with-receiver-and-type-safe-builders/),\
  null 처리 관용구를 계층별로 고르는 법은 [목록의 **58번 주제**](../58-null-handling-idioms-let-requirenotnull-and-elvis-return/)가 정본이다.

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
| **없다** — 이 문서의 블록은 전부 결정적이다(스레드·시간·해시코드·순서 미정 출력을 싣지 않았다) | `javap` 출력 **전체**(오프셋·상수 풀 번호 포함) · 클래스 파일 목록 · `grep -c` 수치 · 경고·에러 문구 · 종료 코드 · 실행 출력 전체 |

> 근거 — **캡처 스크립트를 두 번 돌려 블록 82개를 바이트 단위로 대조**했고, 이 주제의 블록은 한 글자도 안 갈렸다.

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `scope.kt` | `A`\~`G` — 두 축과 **칸이 넷**이라는 것 · `apply`/`also` 가 같은 객체를 낸다는 것 | `kotlinc` → `java` |
| `badrecv.kt` | 수신자 이름을 바꿔 쓰면 **에러 2건** | `kotlinc` (컴파일 실패가 결과) |
| `nullsafe.kt` | `H`\~`M` — **널 검사를 하는 것이 `?.`** 라는 것 · 람다가 돈 횟수 | `kotlinc` → `java` |
| `trap.kt` | `U`\~`Y` — 엘비스의 **조건이 둘**인 것 · `apply` 가 값을 버리는 것 | `kotlinc` → `java` |
| `nest.kt` | `P`\~`T` — 라벨 겹침 경고 1건 · **`it` 가림에는 경고가 없는 것** | `kotlinc`(경고 1건) → `java` |
| `inl.kt` · `noninl.kt` | 클래스 파일 개수 · **`Function1` 0회 대 23회** · `ACC_SYNTHETIC` 0건 | `kotlinc` 4회(플래그 2벌) → `javap -c -p` · `javap -v -p` |
| `unusedit.kt` | `it` 미사용에 **경고가 없는 것**(`exit 0`) | `kotlinc` → `java` |
| `badwith.kt` | `with` 에 nullable 을 넘기면 **`length` 가 지목되는 것** | `kotlinc` (컴파일 실패가 결과) |
| `kotlin-stdlib.jar` | 다섯의 **디스크립터가 겹치는 것** · `@InlineOnly` · `$this$apply` | `unzip` → `javap -p -s` · `javap -v -p` |

**구현 의존 항목** — 클래스 파일 **개수**, 람다 메서드 이름(`five$lambda$0`)과 그 플래그,
`invokedynamic`/`LambdaMetafactory` 를 쓰는 것, 인라인 자리의 `nop`·`iconst_0`, 상수 풀 번호,
`Function1` 등장 횟수 23, 경고·에러 문구 — **전부 이 컴파일러 버전과 플래그의 산출물**이다.\
반면 **「수신자 형태와 반환값이 다섯을 가른다」·「`run`/`with` 가 같은 칸이다」·「`?.` 가 널을 막는다」·
「`apply`/`also` 가 수신자를 돌려준다」·「다섯이 `inline` 이다」·「`with` 만 확장이 아니다」**
는 **언어·stdlib 의 계약**이라 타깃·플래그와 무관하다.

**★ 던져 봤더니 예상과 달랐던 것 — 세 건**

1. ★★★ **클래스 파일 개수만으로는 인라인 여부를 못 가른다.** 「인라인이 아니면 `Function1` 클래스가 생긴다」는
   **Kotlin 2.4.20 기본값에서 재현되지 않았다** — 기본 람다 전략이 `invokedynamic` 이라 클래스 대신
   **`private static final` 메서드**가 생긴다. **`-Xlambdas=class` 를 줘야** 클래스 파일 개수가 갈렸고(2개 대 4개),
   플래그 없이 가르는 것은 **`Function1` 등장 횟수**(0회 대 23회)였다.
2. ★★ **그 람다 메서드는 `ACC_SYNTHETIC` 이 아니었다.** `NoninlKt` 전체에서 `ACC_SYNTHETIC` 이 **0건**이고
   플래그는 `ACC_PRIVATE, ACC_STATIC, ACC_FINAL` 이다. `-Xlambdas=class` 로 생긴 클래스도
   `final class … extends kotlin.jvm.internal.Lambda` 일 뿐 합성 표시가 없다.
3. ★ **중첩 `let` 의 `it` 가림에 경고가 안 났다.** 라벨이 겹치는 `this@apply` 쪽만 경고가 났고,
   **더 헷갈리는 `it` 쪽이 조용했다** — 이 파일의 경고는 통틀어 **1건**이었다.

**안 걸린 것도 출력이다** — `unusedit.kt` 는 `also`/`let`/`apply` 안에서 `it` 을 한 번도 안 썼는데
**경고도 에러도 없이 `exit 0`** 이었다. 컴파일러가 침묵한다는 것이 「그 코드가 읽기 쉽다」를 뜻하지 않는다.
