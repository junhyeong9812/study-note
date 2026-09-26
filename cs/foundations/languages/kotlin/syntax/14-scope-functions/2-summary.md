# kotlin/syntax/14 — scope function 5종: `let`/`run`/`with`/`apply`/`also` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Scope functions](https://kotlinlang.org/docs/scope-functions.html) · [kotlin-stdlib `kotlin` 패키지](https://kotlinlang.org/api/core/kotlin-stdlib/kotlin/) · [Null safety](https://kotlinlang.org/docs/null-safety.html) · [Inline functions](https://kotlinlang.org/docs/inline-functions.html).
> **실행 검증** — 이 문서의 모든 출력·에러·경고·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javap` 에서 실제로 얻었다.\
> `kotlinc` 10회(컴파일 실패 2벌 · 경고 1벌) · `java` 5회 · `javap` 6회. **stdlib 쪽은 `kotlin-stdlib.jar` 를 풀어 직접 역어셈블했다** — 내 코드만 찍은 것이 아니다.
> ⚠️ **`-jvm-target` 을 밝히지 않은 바이트코드 주장은 반쪽이다.** 이 문서의 역어셈블은 전부 **기본값 1.8**(`major version: 52`)이다.\
> 람다를 어떻게 내릴지도 플래그에 달렸다 — 기본은 `invokedynamic` 이고 `-Xlambdas=class` 를 주면 클래스 파일이 따로 생긴다. **둘 다 찍어서 실었다.**
> ⚠️ **다시 돌리면 달라지는 블록은 없다** — 스레드·시간·해시코드·순서 미정 출력을 싣지 않았다. 재대조 근거는 3-answer 의 「흔들리는 칸」 표다.
> **버전** — `let`·`run`·`with`·`apply` 는 **1.0**, `also` 만 **1.1** 이다(`@SinceKotlin("1.1")` 이 바이트코드에 남아 있다). 그 뒤로 시그니처가 바뀐 적이 없다.
> **경계** — 람다 문법·클로저·마지막 인자 람다는 [10번 주제](../10-lambdas-and-higher-order-functions/)가, `inline` 이 무엇을 없애고 무엇을 제약하는지는 [11번 주제](../11-inline-functions/)가,\
> 다섯이 전부 **확장 함수**라는 사실과 그 디스패치는 [13번 주제](../13-extension-functions-and-properties/)가 정본이다.\
> 여기는 **다섯을 어떻게 갈라서 고르나**만 다룬다. 수신자 지정 람다로 DSL 을 짜는 것은 목록의 **37번 주제**,\
> `?.`·`?:` 자체의 의미는 [03번 주제](../03-null-safe-types/), null 처리 관용구 전체는 목록의 **58번 주제**다.
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**다섯은 기능이 다섯 가지인 게 아니다. 질문 두 개에 예/아니오로 답한 조합이 다섯일 뿐이다.**

질문 둘은 이것이다.

1. 람다 안에서 그 객체를 **뭐라고 부르나** — 이름 없이 `this` 인가, `it` 이라는 인자인가.
2. 그 호출이 **무엇을 돌려주나** — 람다가 마지막에 만든 값인가, 원래 객체 그대로인가.

> **수신자(receiver)** — 점 앞에 오는 그 객체. `cup.let { … }` 에서 `cup` 이다.\
> **수신자 지정 람다** — 람다 안에서 그 객체가 `this` 가 되어 **점 없이** 멤버를 부를 수 있는 람다.\
> 타입으로 적으면 `Cup.() -> R` 이고, 보통 람다 `(Cup) -> R` 와 겉모양이 다르다.

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 물건을 작업대에 잠깐 올려놓는다 | scope function 을 건다 |
| 작업대에 올린 뒤 **이름을 안 부르고** 바로 손댄다 | 수신자가 `this` — `run`·`with`·`apply` |
| 작업대에 올린 뒤 **「그거」라고 부르며** 손댄다 | 수신자가 `it` — `let`·`also` |
| 작업 **결과물**을 들고 나온다 | 람다 결과를 돌려준다 — `let`·`run`·`with` |
| **물건 자체**를 다시 들고 나온다 | 수신자를 돌려준다 — `apply`·`also` |
| 작업대를 두 번 겹쳐 놓으면 위엣것만 보인다 | 중첩하면 안쪽 `this`/`it` 이 바깥을 가린다 |
| 작업대는 공정이 끝나면 치운다 | 전부 `inline` 이라 바이트코드에 남지 않는다 |

```text
                    무엇을 돌려주나?
                 람다 결과          수신자 그 자체
              +-----------------+-------------------+
   수신자를   |                 |                   |
   this 로    |  run            |  apply            |
   받는다     |  with  ← 겹친다 |                   |
              +-----------------+-------------------+
   수신자를   |                 |                   |
   it 으로    |  let            |  also             |
   받는다     |                 |                   |
              +-----------------+-------------------+

   run 과 with 는 같은 칸이다. 갈리는 것은 「확장이냐」 하나뿐 —
   run 은 x.run { }, with 는 with(x) { }.
```

**칸이 넷인데 함수가 다섯이라는 것이 이 주제의 첫 번째 사실이다.**

## 이 주제가 답하려는 질문

1. 다섯을 **무엇으로 가르나** — 그리고 왜 칸은 넷인데 함수는 다섯인가.
2. `?.let` 은 `if (x != null)` 을 **무엇으로 바꾸나** — 그리고 그때 새로 생기는 함정은 무엇인가.
3. 다섯을 쓰면 **런타임에 무엇이 생기나** — 객체인가, 아무것도 아닌가.

## 동작 방식

### (1) ★★ 축은 둘뿐이다 — 수신자 형태 × 반환값

**언제 쓰나** — 다섯을 외우려 할 때. 외울 것은 다섯이 아니라 축 둘이다.

```text
===== 소스: scope.kt =====
class Cup(var ml: Int) {
    fun label(): String = "Cup(${ml}ml)"
}

fun main() {
    val a = Cup(100).let { it.ml = 1; it.label() }
    val b = Cup(100).run { ml = 2; label() }
    val c = with(Cup(100)) { ml = 3; label() }
    val d = Cup(100).apply { ml = 4 }
    val e = Cup(100).also { it.ml = 5 }

    println("A let   : $a   (타입 ${a::class.simpleName})")
    println("B run   : $b   (타입 ${b::class.simpleName})")
    println("C with  : $c   (타입 ${c::class.simpleName})")
    println("D apply : ${d.label()}   (타입 ${d::class.simpleName})")
    println("E also  : ${e.label()}   (타입 ${e::class.simpleName})")

    val cup = Cup(100)
    println("F apply 가 돌려준 것이 그 객체인가 : ${cup.apply { ml = 9 } === cup}")
    println("G also  가 돌려준 것이 그 객체인가 : ${cup.also { it.ml = 9 } === cup}")
}
```

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

```text
   같은 객체 Cup(100) 에 다섯을 각각 걸었을 때

   cup.let  { it.ml = 1; it.label() }  ──▶ "Cup(1ml)"   타입 String  ← 람다 결과
   cup.run  {    ml = 2;    label() }  ──▶ "Cup(2ml)"   타입 String  ← 람다 결과
   with(cup){    ml = 3;    label() }  ──▶ "Cup(3ml)"   타입 String  ← 람다 결과
   cup.apply{    ml = 4            }  ──▶  Cup          타입 Cup     ← 수신자
   cup.also { it.ml = 5            }  ──▶  Cup          타입 Cup     ← 수신자
                └┬┘                         └┬┘
          이름을 뭐라 부르나            무엇이 나오나
```

그림 해설:

- ★★ **`A`·`B`·`C` 의 타입이 `String` 이고 `D`·`E` 의 타입이 `Cup` 이다.** 이 한 줄이 두 번째 축 전부다.\
  `${a::class.simpleName}` 로 **런타임 타입을 직접 찍었다** — 컴파일러의 추론을 믿고 적은 것이 아니다.
- ★ **`F`·`G` 가 `true`** 라는 것은 `apply`/`also` 가 **새 객체를 만들지 않고 받은 그것을 그대로 돌려준다**는 뜻이다.\
  `===` 가 참조 동일성이라는 것의 정본은 [목록의 **32번 주제**](../32-equality-and-equals-contract/)다.
- ★ `let`/`also` 안에서는 `it.ml`, `run`/`with`/`apply` 안에서는 그냥 `ml` 로 적었다.\
  **이름을 바꿔 적으면 컴파일이 안 된다** — (7)에서 에러 전문을 본다.

### (2) ★★ 겹치는 칸 — `run` 과 `with` 는 stdlib 에서도 **시그니처가 같다**

**언제 쓰나** — "`run` 과 `with` 는 뭐가 달라?" 에서 막힐 때.

`kotlin-stdlib.jar` 를 풀어 다섯이 선언된 클래스를 직접 역어셈블했다.

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

- ★★ **`run(T, Function1)` 과 `with(T, Function1)` 의 디스크립터가 한 글자도 같다.**\
  `(Ljava/lang/Object;Lkotlin/jvm/functions/Function1;)Ljava/lang/Object;` 둘 다다.\
  같은 칸이라는 것이 **JVM 수준에서 그대로 보인다.**
- ★ **`run` 은 오버로드가 둘**이다. 위의 `run(Function0)` 은 **수신자가 없는 형태**(`run { … }`)라\
  「지역 블록을 식으로 쓰는」 용도다. 이것 때문에 함수 이름은 다섯인데 선언은 여섯이 된다.
- ★★ **`let`·`run`·`with` 세 개도 디스크립터가 전부 같다.** 그런데도 Kotlin 에서 뜻이 다른 이유는\
  **Kotlin 쪽 타입이 `T.(…) -> R` 인지 `(T) -> R` 인지를 JVM 디스크립터가 표현하지 않기 때문**이다.\
  그 구분은 디스크립터가 아니라 **`@kotlin.ExtensionFunctionType` 이라는 타입 애너테이션과 Kotlin 메타데이터**에 들어 있다.\
  → 「구현 세부사항 대 언어 보장」 절에서 다시 본다.
- **`apply`·`also` 도 서로 디스크립터가 같다**(`Function1<? super T, kotlin.Unit>`). 반환 타입이 `T` 인 것이 앞 셋과 다르다.

`apply` 한 개를 자세히 찍으면 세 가지가 더 보인다.

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

- ★★ **`kotlin.internal.InlineOnly`** — "이 함수는 **인라인으로만 존재한다**" 는 표시다.\
  그래서 `ACC_PRIVATE` 다. **Java 에서는 부를 수 없고**, 호출부에 펼쳐지는 것 말고는 존재 방식이 없다.
- ★ **`LocalVariableTable` 의 첫 슬롯 이름이 `$this$apply`** 다. 수신자가 **0번 파라미터**라는 [13번 주제](../13-extension-functions-and-properties/)의 사실이 여기서도 그대로다.
- ★ **`kotlin.IgnorableReturnValue`** — 반환값을 안 써도 된다는 표시다. 다섯 중 `takeIf`·`takeUnless` 를 뺀 것들에 붙어 있다.\
  「반환값을 버리면 경고」 계열 검사가 이 표시를 본다.
- **본문이 세 줄이다** — `block.invoke(this)` 하고 `pop` 하고 `this` 를 돌려준다. `apply` 의 정의가 그대로 보인다.

### (3) ★★ `?.let` — 널 검사가 **문장에서 식으로** 바뀐다

**언제 쓰나** — `if (x != null) { … }` 를 쓰려다 손이 멈출 때.

```text
===== 소스: nullsafe.kt =====
fun oldWay(s: String?): String {
    if (s != null) {
        return "len=${s.length}"
    }
    return "none"
}

fun newWay(s: String?): String = s?.let { "len=${it.length}" } ?: "none"

fun letWithoutQ(s: String?): String = s.let { if (it == null) "none" else "len=${it.length}" }

fun runQ(s: String?): String = s?.run { "len=$length" } ?: "none"

fun main() {
    println("H oldWay(null)        : ${oldWay(null)}")
    println("I newWay(null)        : ${newWay(null)}")
    println("J newWay(\"abc\")       : ${newWay("abc")}")
    println("K letWithoutQ(null)   : ${letWithoutQ(null)}")
    println("L runQ(null)          : ${runQ(null)}")

    var count = 0
    val s: String? = "abc"
    s?.let { count++ }
    val t: String? = null
    t?.let { count++ }
    println("M 람다가 몇 번 돌았나  : $count")
}
```

**출력** (`java -cp onull:kotlin-stdlib.jar NullsafeKt`)

```text
H oldWay(null)        : none
I newWay(null)        : none
J newWay("abc")       : len=3
K letWithoutQ(null)   : none
L runQ(null)          : none
M 람다가 몇 번 돌았나  : 1
```

```text
   s?.let { … } ?: "none"

        s        s?.       let { … }           ?: "none"
     +------+   +--------+  +-------------+   +-----------+
     | null | → | 건너뜀 | → (람다 안 돎)  → | "none"    |
     +------+   +--------+  +-------------+   +-----------+
     +------+   +--------+  +-------------+
     |"abc" | → |  통과  | → it = "abc"    → "len=3"
     +------+   +--------+  +-------------+
                   ↑
          여기서 갈린다 — 람다가 아니라 ?. 가 막는다
```

그림 해설:

- ★★ **널 검사를 하는 것은 `let` 이 아니라 `?.` 다.** `let` 은 그냥 람다를 부를 뿐이다.\
  근거가 `K` 다 — `?.` 없이 `s.let { … }` 로 부르면 **`s` 가 null 이어도 람다가 돈다.**\
  그래서 `let` 안에서 직접 `if (it == null)` 을 써야 했다.
- ★ **`M` 이 `1` 이다.** `?.let` 두 번 중 **널이 아닌 쪽에서만 람다가 돌았다** — 세어서 확인한 것이다.
- ★ `let` 은 **`it` 을 스마트 캐스트된 비-null 타입으로 받는다.** `it.length` 에 `?.` 를 안 붙여도 된다.
- **`?.run` 도 똑같이 된다**(`L`). `run` 은 확장이라 `?.` 를 붙일 수 있다 — (8)의 `with` 와 갈리는 지점이다.
- ★ 「그래서 `?.let` 이 `if` 보다 낫다」는 뜻이 아니다. **`H` 와 `I` 의 출력이 같다.** 바뀌는 것은 **문장이냐 식이냐**다 —\
  식이면 `val x = …` 의 오른쪽에 바로 놓을 수 있고 함수 본문 하나로 줄어든다.

### (4) ★ 엘비스와 만나면 **조건이 하나 늘어난다** — 이 갈래 최대의 함정

**언제 쓰나** — `?.let { … } ?: 기본값` 을 습관처럼 쓸 때.

```text
===== 소스: trap.kt =====
class Row(val id: Int, val name: String?)

fun lookup(r: Row?): String =
    r?.let { it.name } ?: "FALLBACK"

fun main() {
    println("U 널 행         : ${lookup(null)}")
    println("V 이름 있는 행   : ${lookup(Row(1, "kim"))}")
    println("W 이름이 널인 행 : ${lookup(Row(2, null))}")

    val sb = StringBuilder()
    val got = sb.apply { append("x") ; length }
    println("X apply 가 돌려준 것 : ${got::class.simpleName}")

    var side = 0
    val v = 10.also { side = it * 2 }
    println("Y also 의 값 : $v   side : $side")
}
```

**출력** (`java -cp otrap:kotlin-stdlib.jar TrapKt`)

```text
U 널 행         : FALLBACK
V 이름 있는 행   : kim
W 이름이 널인 행 : FALLBACK
X apply 가 돌려준 것 : StringBuilder
Y also 의 값 : 10   side : 20
```

- ★★ **`W` 를 보라.** `Row(2, null)` 은 **null 이 아닌데** `FALLBACK` 이 나왔다.\
  `?:` 가 보는 것은 「`r` 이 null 인가」가 아니라 「**`r?.let { … }` 전체의 결과가 null 인가**」다.\
  **람다가 null 을 돌려주면 그것도 엘비스에 걸린다.**
- ★ 그래서 `?.let { } ?: 기본값` 은 조건이 **둘**이다 — 수신자가 null 이거나, **람다 결과가 null 이거나.**\
  둘을 갈라야 하면 `let` 이 아니라 `if` 나 `when` 을 쓴다.
- ★ **`X` 는 `apply` 가 마지막 식을 버린다는 것**이다. 람다 안에서 `length` 를 마지막에 뒀는데도 `StringBuilder` 가 나왔다.\
  `apply`/`also` 의 람다 반환 타입이 `Unit` 이라 **값을 계산해도 아무도 안 받는다.**
- **`Y` 는 `also` 가 부수 효과 전용**이라는 것이다. 값은 `10` 그대로 흐르고 `side` 만 바뀌었다.

### (5) ★ 중첩하면 **안쪽이 바깥을 가린다** — 그리고 라벨이 겹친다

**언제 쓰나** — `apply` 안에 `apply`, `let` 안에 `let` 을 쓸 때.

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

```text
   o.apply {            ← 바깥: this = Outer
       i.apply {        ← 안쪽: this = Inner   (바깥 this 가 가려진다)
           who()        → Inner(I)
           this@apply   → Inner(I)   ★ 라벨이 둘 다 @apply 라 안쪽을 가리킨다
       }
   }

   o.apply outer@ {     ← 라벨을 직접 달면
       i.apply {
           this@outer   → Outer(O)   ★ 바깥에 닿는다
       }
   }
```

그림 해설:

- ★★ **`this@apply` 가 바깥이 아니라 안쪽을 가리켰다**(`R : Inner(I)`). 암묵 라벨은 **함수 이름**에서 오므로\
  같은 함수를 중첩하면 **라벨이 이름째 겹친다.** 컴파일러는 경고 한 줄을 내지만 **에러가 아니다.**
- ★ 고치는 법은 **람다에 직접 라벨을 다는 것**이다 — `o.apply outer@ { … }` 하면 `this@outer` 로 바깥에 닿는다(`S`).
- ★★ **`it` 쪽은 경고조차 없다.** `"AB".let { "CD".let { … } }` 에서 안쪽 `it` 이 바깥 `it` 을 조용히 가렸고(`T : CD`),\
  이 파일의 경고는 **`this@apply` 한 건뿐**이었다. **가려지는 쪽이 `it` 이면 컴파일러는 아무 말도 하지 않는다.**
- 그래서 실무 규칙은 **중첩할 때는 `it` 에 이름을 준다**(`let { row -> … }`). 이름을 주면 가려질 일이 없다.

### (6) ★★★ 다섯은 **바이트코드에 남지 않는다** — 클래스 파일 개수로 센다

**언제 쓰나** — "scope function 을 남발하면 객체가 생기지 않나?" 라는 의심이 들 때. **이 주제의 네 번째 창이다.**

같은 모양의 함수를 두 벌 만들었다. 하나는 scope function 다섯을 쓰고, 하나는 **내가 만든 인라인 아닌 고차 함수**를 쓴다.

```text
===== 소스: inl.kt =====
class Cup(var ml: Int)

fun five(cup: Cup): Int {
    val a = cup.let { it.ml + 1 }
    val b = cup.run { ml + 2 }
    val c = with(cup) { ml + 3 }
    val d = cup.apply { ml += 4 }.ml
    val e = cup.also { it.ml += 5 }.ml
    return a + b + c + d + e
}
```

```text
===== 소스: noninl.kt =====
class Cup(var ml: Int)

fun <T, R> myLet(x: T, f: (T) -> R): R = f(x)

fun five(cup: Cup): Int {
    val a = myLet(cup) { it.ml + 1 }
    val b = myLet(cup) { it.ml + 2 }
    return a + b
}
```

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

```text
   inl.kt (scope function 5종)          noninl.kt (내가 만든 고차 함수 2회)
   +-----------------------------+      +----------------------------------+
   | 기본값     : 2개             |      | 기본값     : 2개                  |
   | -Xlambdas=class : 2개        |      | -Xlambdas=class : 4개 ★           |
   |                             |      |   NoninlKt$five$a$1.class         |
   |                             |      |   NoninlKt$five$b$1.class         |
   +-----------------------------+      +----------------------------------+
   | Function1 등장 : 0회 ★★      |      | Function1 등장 : 23회             |
   +-----------------------------+      +----------------------------------+
```

그림 해설:

- ★★★ **`InlKt.class` 안에 `Function1` 이라는 글자가 0회 나온다.** 상수 풀까지 훑은 숫자다(`javap -v`).\
  다섯을 썼는데 **함수 타입의 흔적이 클래스 파일 어디에도 없다.**
- ★★ **`-Xlambdas=class` 를 줘도 `inl.kt` 는 클래스 파일이 2개 그대로다.** 만들 람다 객체가 애초에 없기 때문이다.\
  같은 플래그로 `noninl.kt` 는 **4개**가 된다 — 람다 하나에 클래스 하나씩 생겼다.
- ★ **기본값(플래그 없음)에서는 둘 다 2개다.** 개수만 세면 구분이 안 된다 —\
  **Kotlin 2.x 의 기본 람다 전략이 `invokedynamic`** 이라 클래스 대신 **`private static final` 메서드 + `LambdaMetafactory`** 로 내려가기 때문이다.\
  그래서 **개수 하나만 보고 「인라인됐다」고 말하면 틀린다.** `Function1` 등장 횟수가 갈라 준다.
- ★ **그 메서드들은 `ACC_SYNTHETIC` 이 아니다.** 세어 봤더니 `NoninlKt` 전체에 `ACC_SYNTHETIC` 이 **0건**이었고,\
  `five$lambda$0` 의 플래그는 `(0x001a) ACC_PRIVATE, ACC_STATIC, ACC_FINAL` 이었다.

```text
  private static final int five$lambda$0(Cup);
    descriptor: (LCup;)I
    flags: (0x001a) ACC_PRIVATE, ACC_STATIC, ACC_FINAL
    Code:
```

호출부를 펼쳐 보면 차이가 더 분명하다.

**출력** (`javap -c -p oinl/InlKt.class` — scope function 다섯을 쓴 쪽)

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

**출력** (`javap -c -p ononinl/NoninlKt.class` — 인라인 아닌 고차 함수를 쓴 쪽)

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

- ★★ 인라인 쪽에는 **호출 명령이 `Cup.getMl`·`Cup.setMl` 뿐**이다. `let`·`run`·`with`·`apply`·`also` 라는 이름이 **한 번도 안 나온다.**\
  람다 본문이 `five` 안에 그대로 펼쳐졌고 **수신자는 지역 슬롯 이동**(`astore`/`aload`)이 됐다.
- ★ 중간중간 `nop` 과 `iconst_0; istore` 가 보이는 것은 **인라인된 자리를 표시하는 흔적**이다(디버거가 이 자리를 「인라인 함수 안」으로 읽는다).\
  **의미 있는 연산이 아니다.**
- ★★ 인라인 아닌 쪽은 `invokedynamic … Function1` → `invokestatic myLet` → `checkcast Number` → `intValue` 가 람다마다 반복된다.\
  **`Int` 가 `Integer` 로 박싱됐다 다시 풀린다** — 제네릭 `R` 가 `Object` 로 소거되기 때문이다([12번 주제](../12-reified-type-parameters/)).
- ★ 비용 이야기는 **여기까지만** 한다. 「그래서 얼마나 빠르냐」는 **이 문서에서 재지 않았다.**\
  잰 것은 **명령이 있느냐 없느냐**이고, 그것은 숫자가 아니라 구조다.

### (7) 수신자 이름을 바꿔 적으면 — **에러다**

**언제 쓰나** — `apply` 안에서 `it` 을 쓰거나 `let` 안에서 멤버를 바로 부를 때.

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

- ★ **둘 다 `unresolved reference`** 다. 「이 자리에서 `it` 은 없는 이름」, 「이 자리에서 `ml` 은 없는 이름」이라고 말한다.
- ★ 이것이 **컴파일 타임에 잡히는 유일한 축**이다. 반환값 축은 타입이 안 맞을 때만 걸리고,\
  **타입이 우연히 맞으면 조용히 통과한다** — (4)의 `X` 가 그 경우다.

### (8) ★ `with` 만 확장이 아니다 — 그래서 `?.` 를 못 붙인다

**언제 쓰나** — nullable 객체에 `with` 를 쓰려 할 때.

```text
===== 소스: badwith.kt =====
fun f(s: String?): Int = with(s) { length }
===== kotlinc badwith.kt =====
badwith.kt:1:36: error: only safe (?.) or non-null asserted (!!.) calls are allowed on a nullable receiver of type 'String?'.
fun f(s: String?): Int = with(s) { length }
                                   ^^^^^^
(exit 1)
```

- ★★ 에러가 `with` 를 지목하지 않는다. **`length` 를 지목한다** — 「nullable 수신자에는 `?.` 나 `!!.` 만 허용된다」.\
  `with(s)` 자체는 통과했고 **람다 안의 `this` 가 `String?` 가 된 것**이 문제다.
- ★ `run` 은 확장 함수(`T.run`)라 **`s?.run { … }`** 로 쓸 수 있다((3)의 `L`). `with` 는 **최상위 함수**(`with(T, …)`)라\
  점을 찍을 자리가 없으므로 **`?.` 를 붙일 문법 자리 자체가 없다.**
- ★ 이것이 **같은 칸에 있는 둘을 실제로 가르는 유일한 기준**이다 — 「널일 수 있나」와 「체인 중간에 끼나」.

### (9) `it` 을 안 써도 **경고가 없다**

**언제 쓰나** — `also { println("…") }` 처럼 `it` 없이 쓰고 찜찜할 때.

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

- ★ **경고 0건, `exit 0` 이다.** `also`·`let`·`apply` 어느 쪽도 「`it` 을 안 썼다」는 말을 하지 않는다.
- ★ 「**안 걸린 것도 출력이다**」 — 이것은 「그렇게 써도 된다」는 뜻이 아니라 **컴파일러가 안 막아 준다**는 뜻이다.\
  `it` 을 안 쓰는 `also` 는 **`run { }` 이나 그냥 문장**으로 쓰는 편이 읽기 낫다.
- `N : 7` 은 `let` 의 람다가 수신자와 무관한 값을 돌려줘도 된다는 것이다 — `let` 의 `R` 는 자유 타입 파라미터다.

## 문법 — 형태와 규칙

```kotlin
// 형태
x.let  { it -> R }   // 확장 · it · 람다 결과
x.run  { this -> R } // 확장 · this · 람다 결과
with(x){ this -> R } // 최상위 · this · 람다 결과
x.apply{ this -> Unit } // 확장 · this · 수신자
x.also { it -> Unit }   // 확장 · it · 수신자

run { R }            // 수신자 없는 여섯 번째 오버로드 — 지역 블록을 식으로
```

- **`it` 은 이름을 바꿀 수 있다** — `let { row -> … }`. **`this` 는 못 바꾼다**(라벨만 붙일 수 있다).
- **`apply`/`also` 의 람다 반환 타입은 `Unit`** 이다. 마지막 식을 써도 버려진다.
- **`?.` 를 붙일 수 있는 것은 확장인 넷**(`let`·`run`·`apply`·`also`)뿐이다.
- 다섯은 전부 **`public inline`** 이고 stdlib 안에서는 `@InlineOnly` 라 **Java 에서 못 부른다.**
- `this` 를 명시적으로 쓸 수도 있다 — `apply { this.ml = 1 }`. **생략이 기본일 뿐 금지가 아니다.**

## 어디서 틀리나

1. ★★ **`?.let { } ?: 기본값` 의 조건이 둘이다.** 람다가 null 을 돌려줘도 기본값이 나간다((4) `W`).\
   「수신자가 null 일 때만」을 원하면 `if`/`when` 을 쓴다.
2. ★★ **`apply` 로 값을 계산하고 받으려 한다.** 마지막 식이 버려진다((4) `X`). 값을 받고 싶으면 `run` 이다.
3. ★ **중첩에서 `it`/`this` 가 가려진다.** `it` 쪽은 **경고조차 없다**((5) `T`). 중첩하면 이름을 준다.
4. ★ **`with` 에 nullable 을 넘긴다.** 에러가 `with` 가 아니라 **람다 안 멤버**를 지목해서 원인이 안 보인다((8)).
5. ★ **`also` 에서 `it` 을 안 쓴다.** 컴파일러가 안 막아 준다((9)). 읽는 사람만 손해다.
6. **`apply` 로 초기화하면서 예외가 나면** 반쯤 만들어진 객체가 그대로 흘러간다 — `apply` 는 트랜잭션이 아니다.
7. ★ **체인이 길어지면 `this` 가 어디인지 사람이 못 따라간다.** 컴파일은 되고 읽기만 안 된다 — (5)의 경고 없는 쪽과 같은 성격이다.

## 구현 세부사항 대 언어 보장

| 사실 | 어느 층인가 | 근거 |
|---|---|---|
| 다섯의 수신자 형태와 반환값 | **언어 보장** — stdlib 시그니처 | 공식 API 문서 · (1) 실행 |
| 다섯이 `inline` 이라는 것 | **언어 보장** — 선언에 `inline` 이 있다 | `@InlineOnly` · (2) |
| `Function1` 객체가 **안 생긴다** | **언어 보장의 결과**(인라인의 정의) | (6) — `Function1` 0회 |
| `run`/`with` 의 **디스크립터가 같다** | **JVM 구현** — Kotlin 타입이 소거된 결과 | (2) |
| 기본 람다 전략이 `invokedynamic` 인 것 | ★ **이 판의 관찰 · 플래그에 달렸다** | (6) — `-Xlambdas=class` 로 바뀐다 |
| 클래스 파일이 2개라는 숫자 | ★ **이 판의 관찰** | (6) — 플래그마다 다르다 |
| 인라인 자리의 `nop`·`iconst_0` | ★ **이 컴파일러의 산출물** | (6) |
| 람다 메서드가 `ACC_SYNTHETIC` **이 아닌** 것 | ★ **이 판의 관찰** | (6) — 0건 |
| `it` 미사용에 경고가 없는 것 | ★ **이 판의 관찰** | (9) — 판이 바뀌면 붙을 수 있다 |

- ★★ **가장 조심할 자리**: 「`T.() -> R` 와 `(T) -> R` 는 다른 타입이다」는 **언어 보장**이지만,\
  **JVM 에서는 둘 다 `Function1` 이고 디스크립터도 같다**((2)). 구분은 **Kotlin 메타데이터**에만 있다.\
  그래서 **Java 에서 보면 `run` 과 `with` 를 구분할 방법이 없고**, 애초에 `@InlineOnly` 라 부를 수도 없다.
- ★ **「인라인이라 빠르다」는 이 문서가 뒷받침하지 않는다.** 이 문서가 보인 것은 **명령이 없다**는 구조 사실이고,\
  속도는 **재지 않았다.** 인라인의 비용·제약은 [11번 주제](../11-inline-functions/)가 정본이다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| null 이 아닐 때만 뭔가 계산해서 값을 얻는다 | `?.let` | 확장이라 `?.` 가 붙고, 결과를 값으로 받는다 |
| 객체를 만들고 필드를 여럿 채운 뒤 **그 객체**가 필요하다 | `apply` | 수신자를 돌려주고 `this` 라 이름이 안 반복된다 |
| 흐르는 값에 **로그·검증만** 끼운다 | `also` | 값이 그대로 흐르고, `it` 이라 무엇을 보는지 드러난다 |
| 이미 있는 객체로 **여러 줄 계산**해서 값을 낸다 | `run` / `with` | 널 가능성·체인이면 `run`, 아니면 `with` |
| 지역 블록을 식으로 묶는다 | `run { }`(수신자 없는 오버로드) | 이름 없는 스코프가 생긴다 |
| **조건이 「수신자 null」 하나뿐**이어야 한다 | `if` / `when` | `?.let ?: `는 조건이 둘이다 |
| 중첩이 두 겹을 넘어간다 | 쓰지 않는다(지역 변수로 푼다) | `this`/`it` 이 가려지고 경고가 안 난다 |

## 핵심 문장

1. **다섯은 질문 둘의 조합이다** — 수신자를 `this` 로 받나 `it` 으로 받나, 람다 결과를 주나 수신자를 주나.
2. **칸은 넷인데 함수는 다섯이다.** `run` 과 `with` 가 같은 칸이고, **갈리는 것은 확장이냐 하나뿐**이다.
3. **널 검사를 하는 것은 `let` 이 아니라 `?.` 다.** `let` 은 람다를 부를 뿐이다.
4. **`?.let { } ?: 기본값` 은 조건이 둘이다** — 수신자가 null 이거나 람다 결과가 null 이거나.
5. **`apply`/`also` 는 람다의 마지막 식을 버린다.** 값이 필요하면 `run` 이다.
6. **다섯은 바이트코드에 남지 않는다** — `Function1` 이 상수 풀에서 0회다.
7. ★ **컴파일러가 막아 주는 축은 「수신자 이름」 하나뿐**이다. 나머지는 전부 사람이 지켜야 한다.

## 관련 자료

- [10번 주제 — 람다와 고차 함수](../10-lambdas-and-higher-order-functions/) — **그쪽은 람다 문법·`it`·클로저까지, 여기는 그 위에 선 다섯 함수부터.**
- [11번 주제 — 인라인 함수](../11-inline-functions/) — **그쪽은 `inline` 이 없애는 비용과 제약이 정본, 여기는 「그래서 다섯이 안 남는다」는 결과만.**
- [13번 주제 — 확장 함수·확장 프로퍼티](../13-extension-functions-and-properties/) — **그쪽은 확장이 정적 메서드라는 것이 정본, 여기는 다섯이 그 문법 위에 서 있다는 사실만.**
- [03번 주제 — null 안전 타입](../03-null-safe-types/) — **그쪽은 `?.`·`?:`·`!!` 의 의미가 정본, 여기는 `?.` 와 `let` 의 역할 분담만.**
- [12번 주제 — `reified` 타입 파라미터](../12-reified-type-parameters/) — (6)에서 본 박싱과 소거의 정본.
- 목록의 **37번 주제** — 수신자 지정 람다로 DSL 을 짜는 법.
- 목록의 **58번 주제** — null 처리 관용구를 계층별로 고르는 법.
- [목록의 **32번 주제**](../32-equality-and-equals-contract/) — `===` 와 `==` 의 의미.
- [`../../언어-특성/README.md`](../../언어-특성/README.md) — 왜 이 언어를 고르나(설계 논지).

## 용어 풀이

- **수신자(receiver)** — 점 앞에 오는 객체. `cup.let { }` 의 `cup`.
- **수신자 지정 람다** — 람다 안에서 수신자가 `this` 가 되는 람다. 타입은 `Cup.() -> R`.
- **`it`** — 파라미터가 하나인 람다에서 그 파라미터의 기본 이름.
- **인라인 함수** — 호출부에 본문이 펼쳐지는 함수. 함수 객체가 안 생긴다.
- **`@InlineOnly`** — stdlib 내부 표시. 인라인으로만 쓸 수 있고 Java 에서 못 부른다.
- **디스크립터(descriptor)** — JVM 이 보는 메서드 시그니처 문자열. Kotlin 의 타입 정보 일부가 여기서 사라진다.
- **`invokedynamic`** — 호출 방법을 실행 시점에 결정하는 JVM 명령. Kotlin 2.x 의 기본 람다 전략이 이것을 쓴다.
- **`LambdaMetafactory`** — `invokedynamic` 이 람다 구현체를 만들어 내는 JDK 부트스트랩.
- **암묵 라벨** — 람다에 자동으로 붙는 이름. 그 람다를 받는 **함수 이름**이 된다(`this@apply`).
- **엘비스 연산자(`?:`)** — 왼쪽이 null 이면 오른쪽을 내는 연산자.

## 더 들어가면

- **`takeIf`/`takeUnless`** 도 같은 파일에 산다((2)의 역어셈블에 보인다). 축이 하나 더 있다 —\
  **조건을 보고 수신자 아니면 `null` 을 낸다.** 그래서 `?.let` 과 짝이 잘 맞는다(`x.takeIf { … }?.let { … }`).\
  다만 다섯과 달리 **`@IgnorableReturnValue` 가 안 붙어 있다** — 반환값을 버리면 의미가 없기 때문이다.
- **수신자 없는 `run { }`** 은 「블록을 식으로」 쓰는 도구라 성격이 다르다. `val x = run { … }` 은\
  Java 의 즉시 실행 람다 자리에 온다.
- ★ **`@ExtensionFunctionType`** 이 (2)에서 말한 「디스크립터가 못 담는 구분」의 실체다.\
  `kotlin.Metadata` 의 문자열 배열에 `Lkotlin/ExtensionFunctionType;` 이 그대로 들어 있다.\
  **이 문서는 그 메타데이터 문자열을 찍어 보지는 않았다** — `javap -v` 의 상수 풀에서 본 것까지다.
- **코루틴의 `suspend` 람다**도 수신자 지정 람다와 조합된다(`suspend T.() -> R`). 정본은 목록의 **52번 주제**다.
