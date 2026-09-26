# kotlin/syntax/22 — `data class`: 무엇이 생성되고 무엇이 안 되나 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Data classes](https://kotlinlang.org/docs/data-classes.html) · [Destructuring declarations](https://kotlinlang.org/docs/destructuring-declarations.html) · [Object declarations](https://kotlinlang.org/docs/object-declarations.html)(`data object`).
> **실행 검증** — 이 문서의 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 에서 실제로 얻었다.\
> `kotlinc` 7회(컴파일 실패 1벌) · `java` 6회 · `javap` 2회.\
> ★★ 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적지 않았다.
> ⚠️ **`-jvm-target` 을 밝히지 않은 바이트코드 주장은 반쪽이다.** 이 문서의 역어셈블은 전부 **기본값 1.8**(`major version: 52`)이다.
> **버전** — `data class` 는 **1.0**, `data object` 는 **1.9** 다. 뒤의 것은 이 판에서 직접 던져 확인했다((5)).
> **경계** — 프로퍼티의 backing field·`const` 는 [16번 주제](../16-properties-backing-field-lateinit-const/)가 정본이고, 상속 기본값은 [19번 주제](../19-inheritance-open-final-override/)가 정본이다.\
> `componentN` 규약 자체를 파고드는 것은 [목록의 **30번 주제**](../30-destructuring-declarations-and-componentn/), `==`/`===` 와 `equals` 규약은 [목록의 **32번 주제**](../32-equality-and-equals-contract/), 박싱이 사라지는 `value class` 는 [목록의 **26번 주제**](../26-value-class-and-boxing/)다.\
> Java 쪽 짝은 [`../../../java/syntax/14-records/`](../../../java/syntax/14-records/) — **같은 목적에 방어선을 다른 곳에 둔 것**이 이 주제의 대비 축이다.
> 이 본문은 Claude 작성이다(원고 없음).

★ **흔들리는 칸 / 안 흔들리는 칸** — 제출 전 재대조에서 「고칠 것」과 「설계상 다른 것」을 가르는 선언이다.

| 흔들린다 | 안 흔들린다 |
|---|---|
| 기본 `toString()` 의 `Plain@1b6d3586` 꼴 **해시코드 숫자** | 컴파일 에러의 **문구·`파일:줄:칸`·캐럿 줄** |
| `hashCode()` 의 **값 자체**(컴포넌트가 `Any.hashCode` 로 떨어질 때) | `javap` 출력 **전체**(필드 목록·메서드 목록·시그니처) |
| | `hashCode()` 가 **같나 다르나** — 이 문서의 근거는 전부 이 쪽이다 |
| | 모든 **종료 코드** · `println` 출력 |

> ★★ **이 주제에서 `hashCode` 가 정확히 그 자리다.** `Wrap(Plain(1))` 두 개의 해시코드는 **실행마다 바뀌므로 값을 실을 수 없다.**\
> 그래서 이 문서는 `hashCode()` 를 **찍지 않고** `h1 == h2` 라는 **불리언**만 찍는다 — 값이 아니라 「같나 다르나」가 근거다((7)).\
> 같은 이유로 `object Plain` 의 기본 `toString()` 은 `@` 앞만 잘라 찍었다((5)).
>
> 근거 — 캡처 스크립트를 두 번 돌려 블록 전체를 바이트 단위로 대조했다(수치는 3-answer 의 「실행 검증」).

## 한눈에 — 쉽게 말하면

**`data` 한 낱말이 컴파일러에게 「이 클래스는 값이다」라고 말한다.** 그러면 값에 필요한 멤버 다섯 벌이 딸려 온다.

문제는 **재료를 어디서 읽느냐**다. 컴파일러는 **주 생성자 괄호 안에 적힌 프로퍼티만** 읽는다. 본문(`{ }`)에 적은 것은 **필드로는 만들어지지만 아무도 안 본다**.

비유는 문서 끝까지 이것 하나로 고정한다 — **부품 명세서가 붙은 조립 키트**다.

| 비유 | 실체 |
|---|---|
| 조립 키트 | `data class` 선언 |
| 상자 겉면의 **부품 명세서** | 주 생성자 괄호 안의 `val`/`var` |
| 명세서에 안 올리고 상자에만 넣은 부품 | 클래스 **본문**에 선언한 프로퍼티 |
| 「이 키트와 저 키트가 같은가」 판정 | `equals` — **명세서만 대조한다** |
| 키트 번호표 | `hashCode` — 역시 명세서만 |
| 상자에 인쇄된 내용물 목록 | `toString` — 역시 명세서만 |
| 「같은 명세로 하나 더 주세요」 | `copy` — **명세서 항목만 받아 새로 만든다** |
| 부품을 **번호로** 꺼내기 | `component1()`·`component2()` — 순서가 곧 번호다 |

```text
   data class User(val id: Int, val name: String) {   <- 괄호 안 = 부품 명세서
       var note: String = ""                          <- 본문 = 명세서 밖
       val upper: String get() = name.uppercase()     <- 서랍도 없다(계산값)
   }
          |
          v  컴파일러가 찍어 주는 것 — 전부 명세서만 읽는다
   +-----------------------------------------------------+
   |  equals / hashCode / toString                       |  id, name 만 본다
   |  component1() / component2()                        |  둘뿐이다
   |  copy(id, name)                                     |  파라미터가 둘뿐이다
   +-----------------------------------------------------+
          |
          v  그런데 필드는 셋이다
   private final int id;   private final String name;   private String note;
                                                        ^^^^^^^^^^^^^^^^^^^^
                                                        만들어지지만 아무도 안 본다
```

**「생성되는 것」과 「그것이 읽는 것」은 다른 질문이다.** 이 주제의 값은 뒤엣것에 있다.

## 이 주제가 답하려는 질문

1. **무엇이 생성되고 무엇이 안 생기나** — 목록을 `javap` 로 셀 수 있나.
2. 생성된 멤버는 **무엇을 재료로 읽나** — 필드 전부인가, 명세서뿐인가.
3. `data class` 가 **못 하는 것**은 무엇인가 — 어디서 컴파일이 깨지나.

## 동작 방식

### (1) ★★★ 생성되는 멤버 전수 — `javap -p` 가 답한다

**언제 쓰나** — 「`data` 를 붙이면 뭐가 생기지?」를 외우지 말고 세어 볼 때.

```kotlin
// dcgen.kt
data class User(val id: Int, val name: String) {
    var note: String = ""
    val upper: String get() = name.uppercase()
}

fun main() {
    val a = User(1, "kim")
    val b = User(1, "kim")
    a.note = "A 쪽 메모"
    b.note = "B 쪽 메모"
    println("A ${a == b}")
    println("B ${a.hashCode() == b.hashCode()}")
    println("C $a")
    println("D ${a.note} / ${b.note}")
    println("E ${a.component1()} ${a.component2()}")
    println("F ${a.copy().note == ""}")
}
```

```text
===== javap -p o22gen/User.class =====
Compiled from "dcgen.kt"
public final class User {
  private final int id;
  private final java.lang.String name;
  private java.lang.String note;
  public User(int, java.lang.String);
  public final int getId();
  public final java.lang.String getName();
  public final java.lang.String getNote();
  public final void setNote(java.lang.String);
  public final java.lang.String getUpper();
  public final int component1();
  public final java.lang.String component2();
  public final User copy(int, java.lang.String);
  public static User copy$default(User, int, java.lang.String, int, java.lang.Object);
  public java.lang.String toString();
  public int hashCode();
  public boolean equals(java.lang.Object);
}
(exit 0)
```

```text
   선언한 것                          javap 가 보여 주는 것
   --------------------------------   ------------------------------------------
   val id, val name (괄호 안)      ->  private final int id;
                                       private final java.lang.String name;
                                       getId() / getName()
   var note (본문)                 ->  private java.lang.String note;
                                       getNote() / setNote()
   val upper (본문·계산값)         ->  getUpper()  ← 필드 없음(서랍이 없다)

   data 가 더해 준 것              ->  component1() / component2()
                                       copy(int, String)
                                       copy$default(...)          ← 기본 인자용 다리
                                       toString() / hashCode() / equals(Object)
```

- **생성되는 것은 여섯 종**이다 — `componentN` · `copy` · `toString` · `hashCode` · `equals`, 그리고 기본 인자를 받기 위한 **`copy$default`**.
- ★★★ **`copy` 의 시그니처를 보라 — `copy(int, java.lang.String)` 이다.** 파라미터가 **둘뿐**이고 `note` 는 **없다.** 명세서에 없으니 받을 방법이 없다.
- ★ **`note` 필드는 만들어진다.** 「생성 안 됨」이 아니라 「**생성되지만 어느 생성 멤버도 안 읽는다**」가 정확한 표현이다. 이 구분이 (2)의 사고를 만든다.
- **안 생기는 것**도 세어 두라 — `Object` 의 `clone`·직렬화 훅·`compareTo`·빌더·검증 로직은 **아무것도 안 생긴다.** `data` 는 `Comparable` 을 구현해 주지 않는다.

> **주 생성자(primary constructor)** — 클래스 이름 바로 뒤 괄호에 적는 생성자.\
> 예: `data class User(val id: Int, val name: String)` 에서 `(val id: Int, val name: String)` 이 그것이다. [15번 주제](../15-class-declaration-constructors-and-init/)가 정본이다.

### (2) ★★★ 본문에 선언한 `var` 는 `equals` 에서 빠진다 — 출력과 필드 목록 둘로 확인한다

**언제 쓰나** — 캐시·플래그·타임스탬프처럼 「부수적인 상태」를 `data class` 본문에 얹었을 때.

```text
===== 소스: dcgen.kt =====
data class User(val id: Int, val name: String) {
    var note: String = ""
    val upper: String get() = name.uppercase()
}

fun main() {
    val a = User(1, "kim")
    val b = User(1, "kim")
    a.note = "A 쪽 메모"
    b.note = "B 쪽 메모"
    println("A ${a == b}")
    println("B ${a.hashCode() == b.hashCode()}")
    println("C $a")
    println("D ${a.note} / ${b.note}")
    println("E ${a.component1()} ${a.component2()}")
    println("F ${a.copy().note == ""}")
}
===== kotlinc dcgen.kt -d o22gen =====
(exit 0)
===== java -cp o22gen:kotlin-stdlib.jar DcgenKt =====
A true
B true
C User(id=1, name=kim)
D A 쪽 메모 / B 쪽 메모
E 1 kim
F true
(exit 0)
```

- `A true` — **`note` 가 다른데 `==` 가 참**이다. `equals` 가 `id`·`name` 만 대조하기 때문이다.
- `B true` — 해시코드도 같다. 값을 안 찍고 「같나」만 찍은 이유는 머리말의 표를 보라.
- `C User(id=1, name=kim)` — `toString` 에도 **`note` 가 없다.**
- `D A 쪽 메모 / B 쪽 메모` — 그런데 **`note` 자체는 멀쩡히 살아 있다.** 「사라진 것」이 아니라 「**안 보이는 것**」이다.
- `E 1 kim` — `componentN` 은 둘뿐이고 순서대로다.
- `F true` — **`copy()` 가 돌려준 객체의 `note` 는 빈 문자열**이다. `a.note` 를 안 물려받고 **선언한 초기값으로 다시 시작**한다((3)).

```text
   a = User(1,"kim"), a.note="A 쪽 메모"      b = User(1,"kim"), b.note="B 쪽 메모"
        id=1  name="kim"  note="A 쪽 메모"         id=1  name="kim"  note="B 쪽 메모"
             \                     /
              +--- equals 가 보는 것 ---+
              |  id  ==  id            |    -> true
              |  name == name          |    -> true
              +------------------------+
                 note 는 비교 대상이 아니다   -> a == b  이다
```

- ★★★ 이것이 **`HashSet`·`Map` 키에서 사고가 되는 자리**다. `note` 만 다른 두 객체가 **같은 키로 취급**되어 하나가 덮인다. 해시 자료구조 쪽 정본은 [`../../../../../data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/)이다.
- ★ 반대로 **일부러 그렇게 쓰는** 경우도 있다 — 「신원은 `id`·`name` 이고 나머지는 부수 상태」라는 설계를 문법으로 표현한 것이다. 문제는 **의도인지 사고인지가 코드에 안 적힌다**는 점이다.

### (3) ★★ `copy` 는 얕고, 본문 프로퍼티를 되살리지 않는다

**언제 쓰나** — 「불변 객체니까 `copy` 하면 안전하겠지」라고 믿을 때.

```text
===== 소스: dccopy.kt =====
data class Cart(val owner: String, val items: MutableList<String>) {
    var coupon: String? = "WELCOME"
}

fun main() {
    val a = Cart("kim", mutableListOf("사과"))
    val b = a.copy()
    b.items.add("배")
    println("A ${a.items}")
    println("B ${b.items}")
    println("C ${a.items === b.items}")
    println("D ${a == b}")
    a.coupon = null
    val c = a.copy(owner = "lee")
    println("E ${c.owner} ${c.coupon}")
    println("F ${a.coupon}")
}
===== kotlinc dccopy.kt -d o22copy =====
(exit 0)
===== java -cp o22copy:kotlin-stdlib.jar DccopyKt =====
A [사과, 배]
B [사과, 배]
C true
D true
E lee WELCOME
F null
(exit 0)
```

```text
   a = Cart("kim", [사과])            b = a.copy()
        owner --> "kim"                    owner --> "kim"
        items --> [사과] <----------------- items  (같은 리스트를 가리킨다)
        coupon--> "WELCOME"                coupon--> "WELCOME"  (본문 초기값으로 새로 시작)

   b.items.add("배")  ->  a.items 도 [사과, 배] 가 된다
```

- `A`·`B`·`C` — `b.items.add("배")` 한 번에 **`a.items` 도 같이 바뀌었고** `a.items === b.items` 가 **`true`** 다. **`copy` 는 참조만 베낀다**(얕은 복사).
- `D true` — 그래서 둘은 여전히 `==` 다. 같은 리스트를 보고 있으니 당연하다.
- ★★ `E lee WELCOME` / `F null` — `a.coupon` 을 `null` 로 바꾼 뒤 `copy` 했는데 **사본의 `coupon` 은 `WELCOME`** 이다. `copy` 는 `coupon` 을 **읽지 않고**, 새 객체를 만들면서 **본문의 초기화식을 다시 실행**한다.
- ★★★ 그래서 `copy` 의 정확한 뜻은 「이 객체의 복사본」이 아니라 「**명세서 값만 물려받아 새로 만든 객체**」다. 본문 상태는 **조용히 초기화된다** — 에러도 경고도 없다.

> **얕은 복사(shallow copy)** — 필드에 든 **참조 값**만 베끼고, 그 참조가 가리키는 객체는 안 베끼는 것.\
> 예: `copy()` 한 두 `Cart` 가 **같은 리스트 한 개**를 공유한다.

- ★ 막는 법은 `data class` 밖에 있다 — 생성자에서 **방어 복사**를 하거나(`init { }` 에서 `toList()`), 애초에 **읽기 전용 타입**(`List`)으로 받는 것이다. 목록의 **40번 주제**가 「읽기 전용은 불변이 아니다」를 다룬다 — 방어선은 거기서 다시 한 겹 새는 것까지 봐야 한다.
- ★ Java `record` 도 **똑같이 얕다**([`../../../java/syntax/14-records/`](../../../java/syntax/14-records/)). 다른 것은 record 쪽에 **컴팩트 생성자**라는 검증 자리가 문법으로 있다는 점이다.

### (4) ★★ 구조 분해는 **이름이 아니라 위치**다 — 순서를 바꾸면 조용히 깨진다

**언제 쓰나** — `val (a, b) = obj` 를 쓸 때, 그리고 남의 `data class` 필드 순서를 바꿀 때.

```text
===== 소스: dcorder.kt =====
data class Point(val x: Int, val y: Int)

fun main() {
    val p = Point(x = 10, y = 20)
    val (x, y) = p
    println("A x=$x y=$y")
    val (y2, x2) = p
    println("B x=$x2 y=$y2")
    println("C ${p.component1()} ${p.component2()}")
}
===== kotlinc dcorder.kt -d o22ord =====
(exit 0)
===== java -cp o22ord:kotlin-stdlib.jar DcorderKt =====
A x=10 y=20
B x=20 y=10
C 10 20
(exit 0)
```

- `A x=10 y=20` — 이름을 맞춰 받으면 맞는다.
- ★★ `B x=20 y=10` — **이름만 바꿔 받았더니 값이 뒤집혔다.** 컴파일러는 `component1()`·`component2()` 를 **순서대로** 꽂을 뿐, 내가 붙인 이름을 **전혀 안 본다.**
- `C 10 20` — `componentN` 자체는 선언 순서 그대로다.

**더 나쁜 쪽은 반대 방향이다** — 읽는 코드를 안 고쳤는데 **선언 쪽 순서가 바뀌는** 것이다.

```text
===== 소스: dcorder2.kt =====
data class Coord(val y: Int, val x: Int)

fun readIt(c: Coord) {
    val (x, y) = c
    println("A x=$x y=$y")
}

fun main() {
    readIt(Coord(y = 20, x = 10))
    println("B ${Coord(20, 10)}")
}
===== kotlinc dcorder2.kt -d o22ord2 =====
(exit 0)
===== java -cp o22ord2:kotlin-stdlib.jar Dcorder2Kt =====
A x=20 y=10
B Coord(y=20, x=10)
(exit 0)
```

- `readIt` 안의 `val (x, y) = c` 는 **한 글자도 안 고쳤다.** 그런데 `Coord` 가 `(y, x)` 순으로 선언되어 있으니 `x` 에 `20` 이, `y` 에 `10` 이 들어간다.
- ★★★ **컴파일 에러도 경고도 없다.** 타입이 둘 다 `Int` 라 타입 검사가 아무것도 못 잡는다. 두 필드의 타입이 같은 순간 **이 사고는 전부 조용해진다.**
- ★ 막는 법 — 구조 분해 대신 **이름으로 읽는다**(`c.x`·`c.y`). 셋 이상이면 거의 항상 이쪽이 맞다.
- ★ Kotlin 2.3.20 에 **이름 기반 구조 분해**가 실험 기능으로 들어와 있지만 아직 Experimental 이라 이 목록에서 뺐다(Kotlin README 의 「뺀 것」 표).

### (5) ★ `data object` — 1.9 에서 들어온 것을 이 판에서 직접 확인했다

**언제 쓰나** — `sealed` 계층에 「데이터 없는 변형」을 넣을 때([23번 주제](../23-sealed-classes-and-when-exhaustiveness/)).

```text
===== 소스: dcobject.kt =====
object Plain
data object Marked

fun main() {
    println("A ${Plain.toString().substringBefore('@')} / @ 붙음=${'@' in Plain.toString()}")
    println("B $Marked / @ 붙음=${'@' in Marked.toString()}")
    println("C ${Plain == Plain} ${Marked == Marked}")
    println("D ${Marked.hashCode() == Marked.hashCode()}")
    println("E ${Plain === Plain} ${Marked === Marked}")
}
===== kotlinc dcobject.kt -d o22obj =====
(exit 0)
===== java -cp o22obj:kotlin-stdlib.jar DcobjectKt =====
A Plain / @ 붙음=true
B Marked / @ 붙음=false
C true true
D true
E true true
(exit 0)
```

```text
===== javap -p o22obj/Plain.class o22obj/Marked.class =====
Compiled from "dcobject.kt"
public final class Plain {
  public static final Plain INSTANCE;
  private Plain();
  static {};
}
Compiled from "dcobject.kt"
public final class Marked {
  public static final Marked INSTANCE;
  private Marked();
  public java.lang.String toString();
  public int hashCode();
  public boolean equals(java.lang.Object);
  static {};
}
(exit 0)
```

```text
   object Plain                       data object Marked
   -------------------------------    ------------------------------------------
   public static final Plain INSTANCE public static final Marked INSTANCE
   private Plain();                   private Marked();
   static {};                         toString() / hashCode() / equals(Object)
                                      static {};
   toString() 은 Any 것 그대로         toString() 이 "Marked" 를 돌려준다
   -> "Plain@15db9742"                -> "Marked"
```

- `A` 줄이 `@ 붙음=true` 다 — 그냥 `object` 는 **`Any.toString()` 이 그대로 떨어져** 클래스 이름 뒤에 해시코드가 붙는다. **그 숫자는 실행마다 바뀌므로 이 문서는 `@` 앞만 잘라 찍었다.**
- `B Marked / @ 붙음=false` — `data object` 는 **`toString()` 을 만들어 줘서** 이름만 나온다. 로그·`toString` 기반 표시에서 이것 하나가 값어치다.
- `C`·`E` — 둘 다 싱글턴이므로 `==` 도 `===` 도 참이다. **`data` 를 붙였다고 인스턴스가 늘지 않는다.**
- ★ `javap` 로 보면 차이가 정확히 **세 메서드**다 — `data object` 에만 `toString`/`hashCode`/`equals` 가 있다. `componentN`·`copy` 는 **둘 다 없다**(명세서가 비어 있으니 만들 것이 없다).
- ★★ 판 확인 — **2.4.20 에서 `data object` 는 경고 없이 컴파일된다.** Kotlin README 의 판 이력표가 적어 둔 「data object = 1.9」와 어긋나지 않는다. 다만 **이 실행은 「1.9 부터다」를 증명하지 않는다** — 증명한 것은 「**2.4.20 에서는 된다**」뿐이다.

### (6) ★★ `data class` 가 못 하는 것 — 금지 사례 전수

**언제 쓰나** — `data class` 를 계층의 뿌리로 쓰려다 막힐 때.

```text
===== 소스: dcforbid.kt =====
open class Base(val tag: String)

open data class Bad1(val x: Int)

data class Ok1(val x: Int) : Base("b")

class Sub : Ok1(1)

data class Bad3()

data class Bad4(x: Int)

data class Bad5(val x: Int) {
    fun component1() = 99
}
===== kotlinc dcforbid.kt -d o22bad =====
dcforbid.kt:3:1: error: modifier 'open' is incompatible with 'data'.
open data class Bad1(val x: Int)
^^^^
dcforbid.kt:3:6: error: modifier 'data' is incompatible with 'open'.
open data class Bad1(val x: Int)
     ^^^^
dcforbid.kt:7:13: error: this type is final, so it cannot be extended.
class Sub : Ok1(1)
            ^^^
dcforbid.kt:9:16: error: data class must have at least one primary constructor parameter.
data class Bad3()
               ^^
dcforbid.kt:11:17: error: primary constructor of data class must only have property ('val' / 'var') parameters.
data class Bad4(x: Int)
                ^^^^^^
dcforbid.kt:13:12: error: conflicting overloads:
fun component1(): Int
data class Bad5(val x: Int) {
           ^^^^^^^^^^^^^^^^
dcforbid.kt:14:5: error: conflicting overloads:
fun component1(): Int
    fun component1() = 99
    ^^^^^^^^^^^^^^^^
(exit 1)
```

```text
   data class ... : Base()      <- 된다.    남을 상속하는 것은 막지 않는다
   open data class ...          <- 안 된다. open 과 data 가 양립 불가
   class Sub : Ok1(1)           <- 안 된다. data class 는 final 이다
   data class Bad3()            <- 안 된다. 명세서가 비면 안 된다
   data class Bad4(x: Int)      <- 안 된다. val/var 없는 파라미터는 프로퍼티가 아니다
   fun component1() = 99        <- 안 된다. 컴파일러 것과 충돌한다
```

- ★★★ **전제가 뒤집힌 자리다.** 「`data class` 는 상속을 못 한다」로 외우면 **절반이 틀린다** — `data class Ok1(val x: Int) : Base("b")` 는 **그냥 컴파일된다.** 막히는 것은 **상속당하는 쪽**이다(`class Sub : Ok1(1)` → 「`this type is final, so it cannot be extended.`」).
- `open` 과 `data` 는 **양립 불가**라 컴파일러가 **양방향으로 한 번씩** 말한다(에러 두 줄). [19번 주제](../19-inheritance-open-final-override/)의 `private override` 에서도 같은 모양이 나왔다.
- 「`data class must have at least one primary constructor parameter.`」 — **명세서가 비면 만들 것이 없다.** 그래서 `data object` 가 따로 있는 것이다((5)).
- 「`primary constructor of data class must only have property ('val' / 'var') parameters.`」 — 괄호에 적혀도 **`val`/`var` 가 없으면 프로퍼티가 아니라 생성자 인자**일 뿐이라 명세서에 못 오른다.
- `componentN` 을 손으로 쓰면 「`conflicting overloads:`」가 **선언 자리와 함수 자리 두 곳에** 뜬다.

### (7) ★ `equals`/`hashCode` 는 컴포넌트에 **위임**한다 — 그래서 컴포넌트가 흔들리면 같이 흔들린다

**언제 쓰나** — `data class` 안에 평범한 클래스를 넣었을 때.

```text
===== 소스: dchash.kt =====
class Plain(val v: Int)

data class Wrap(val p: Plain)
data class Flat(val v: Int)

fun main() {
    val w1 = Wrap(Plain(1))
    val w2 = Wrap(Plain(1))
    println("A ${w1 == w2}")
    println("B ${w1.hashCode() == w2.hashCode()}")
    val f1 = Flat(1)
    val f2 = Flat(1)
    println("C ${f1 == f2}")
    println("D ${f1.hashCode() == f2.hashCode()}")
    println("E ${w1.toString().substringBefore('@')}")
}
===== kotlinc dchash.kt -d o22hash =====
(exit 0)
===== java -cp o22hash:kotlin-stdlib.jar DchashKt =====
A false
B false
C true
D true
E Wrap(p=Plain
(exit 0)
```

```text
   data class Wrap(val p: Plain)          data class Flat(val v: Int)
        Wrap.equals -> p.equals                Flat.equals -> v == v
                        |                                       |
                        v                                       v
            Plain 은 equals 를 안 고쳤다              Int 는 값 비교다
            -> Any.equals = 참조 비교                 -> 같다
            -> Wrap(Plain(1)) != Wrap(Plain(1))       -> Flat(1) == Flat(1)
```

- `A false` / `B false` — `Wrap` 둘은 **다르다.** `data` 가 붙었는데도 그렇다.
- `C true` / `D true` — `Flat` 둘은 같다.
- ★★ **`data` 는 「깊은 비교」를 약속하지 않는다.** 약속은 「**컴포넌트마다 그 컴포넌트의 `equals` 를 부른다**」뿐이고, 컴포넌트가 참조 비교면 결과도 참조 비교다.
- ★ 그래서 `Wrap` 의 해시코드는 **실행마다 바뀐다.** 값이 아니라 「같나 다르나」만 근거로 쓴 이유가 여기 있다(머리말 표).
- ★ 배열 컴포넌트는 특히 위험하다 — `Array` 의 `equals` 는 **참조 비교**라 내용이 같아도 다르다. Java `record` 도 **완전히 같은 함정**이다([`../../../java/syntax/14-records/`](../../../java/syntax/14-records/)).

## 문법 — 형태와 규칙

**형태** — `data class` 하나에 명세서·본문·`copy`·구조 분해·`data object` 가 전부 도는 최소 예제다.

```text
===== 소스: form22.kt =====
data class Book(val isbn: String, var stock: Int) {
    var lastTouched: Int = 0
}

data object OutOfPrint

fun main() {
    val b = Book("978-1", 3)
    b.lastTouched = 99
    val c = b.copy(stock = 0)
    val (isbn, stock) = b
    println("Z ${b == Book("978-1", 3)} $c ${c.lastTouched} $isbn $stock $OutOfPrint")
}
===== kotlinc form22.kt -d o22form =====
(exit 0)
===== java -cp o22form:kotlin-stdlib.jar Form22Kt =====
Z true Book(isbn=978-1, stock=0) 0 978-1 3 OutOfPrint
(exit 0)
```

**규칙 불릿**

- `data` 는 **주 생성자에 `val`/`var` 파라미터가 하나 이상** 있어야 붙는다.
- 생성되는 멤버는 **`componentN`·`copy`·`toString`·`hashCode`·`equals`** 다(+ 기본 인자용 `copy$default`).
- **다섯 멤버 전부 주 생성자 프로퍼티만** 읽는다. 본문 프로퍼티는 **필드로는 생기고 아무도 안 읽는다**((1)·(2)).
- 내가 직접 `equals`/`hashCode`/`toString` 을 쓰면 **컴파일러가 그것을 존중해 안 만든다.** `componentN`·`copy` 는 **충돌 에러**다((6)).
- `data class` 는 **항상 `final`** 이다. `open`·`abstract`·`sealed`·`inner` 를 붙일 수 없다.
- **남을 상속하는 것은 된다** — 막히는 것은 상속당하는 쪽뿐이다((6)).
- `data object` 는 **1.9** 부터다. `toString`/`hashCode`/`equals` 만 만들어 주고 `copy`·`componentN` 은 **안 만든다**((5)).
- `copy` 는 **얕은 복사**이고 본문 프로퍼티를 **초기값으로 되돌린다**((3)).

## 어디서 틀리나

1. ★★★ **본문에 상태를 얹고 `equals` 가 그것을 볼 거라 믿는다.** 안 본다((2)). `Set`·`Map` 키로 쓰는 순간 사고가 된다.
2. ★★★ **`copy()` 를 「이 객체의 복사본」으로 읽는다.** 본문 프로퍼티는 **초기값으로 새로 시작**한다((3)) — 조용하다.
3. ★★ **`copy` 가 깊은 복사인 줄 안다.** 컬렉션·배열 컴포넌트는 **그대로 공유된다**((3)).
4. ★★ **구조 분해에서 이름이 맞춰 줄 거라 믿는다.** 위치뿐이다((4)). **타입이 같으면 컴파일러가 아무것도 못 잡는다.**
5. ★★ **`data class` 필드 순서를 바꾼다.** 기존 구조 분해가 **에러 없이 뒤집힌다**((4)).
6. ★ **「`data class` 는 상속을 못 한다」로 외운다.** 남을 상속하는 것은 된다((6)) — 막히는 방향을 정확히 기억해야 한다.
7. ★ **컴포넌트에 평범한 클래스를 넣고 깊은 비교를 기대한다**((7)). 컴포넌트 쪽 `equals` 가 없으면 참조 비교로 떨어진다.
8. ★ **`data class` 가 검증도 해 줄 거라 믿는다.** 아무것도 안 해 준다 — 검증은 `init { }` 에 직접 쓴다([15번 주제](../15-class-declaration-constructors-and-init/)).
9. ★ **`data` 를 붙이면 불변이 된다고 믿는다.** `var` 파라미터도 허용되므로 **가변 `data class` 가 정상 문법**이다. Java `record` 와 갈리는 지점이다.

## 구현 세부사항 대 언어 보장

| 항목 | 어느 쪽인가 | 근거 |
|---|---|---|
| `componentN`·`copy`·`toString`·`hashCode`·`equals` 가 생성되는 것 | **언어 보장** | (1) |
| 그 다섯이 **주 생성자 프로퍼티만** 읽는 것 | **언어 보장** | (1)·(2) |
| `copy` 가 **얕은 복사**인 것 | **언어 보장** | (3) |
| 구조 분해가 **위치 기반**인 것 | **언어 보장** | (4) |
| `data class` 가 `final` 인 것 · 상속당할 수 없는 것 | **언어 보장** | (6) |
| `data object` 가 세 메서드만 만드는 것 | **언어 보장**(1.9+) | (5) |
| `copy$default` 라는 **이름의 다리 메서드**가 생기는 것 | **JVM 백엔드의 구현** | (1)의 `javap` |
| `note` 가 `private java.lang.String note;` 로 나가는 것 · 멤버 나열 **순서** | **JVM 백엔드의 구현** | (1)의 `javap` |
| `toString` 의 **출력 형식**(`User(id=1, name=kim)`) | **문서화된 형식이되 판의 산출물로 읽는 편이 안전하다** | (2) |
| `hashCode()` 의 **값** | **컴포넌트에 달렸다 — 보장 아님** | (7) |
| 에러 메시지의 **문구 그 자체** | **컴파일러 판의 산출물** | (6) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 값 몇 개를 묶어 나르고 비교·출력이 필요하다 | `data class` | 다섯 멤버가 공짜다 |
| 필드가 하나뿐이고 래핑 비용이 아깝다 | `value class` | [목록의 **26번 주제**](../26-value-class-and-boxing/) — 박싱이 사라진다 |
| 데이터 없는 변형(싱글턴)이 필요하다 | `data object` | (5) — `toString` 이 이름으로 나온다 |
| 계층을 열어야 한다(하위 타입이 필요하다) | `sealed` + 그 아래 `data class` | [23번 주제](../23-sealed-classes-and-when-exhaustiveness/) — `data class` 자신은 못 연다 |
| 신원(identity)이 값이 아니라 **객체 자체**다 | **일반 `class`** | 엔티티에 `data` 를 붙이면 `equals` 의 뜻이 바뀐다 |
| 불변을 **강제**하고 싶다 | Java 라면 `record` | [`../../../java/syntax/14-records/`](../../../java/syntax/14-records/) — Kotlin `data class` 는 `var` 를 허용한다 |
| 부수 상태를 같이 들고 다녀야 한다 | **`data class` 밖으로 뺀다** | 본문에 얹으면 (2)·(3)의 사고가 난다 |

## 핵심 문장

1. `data` 가 만드는 것은 **여섯**이고(`componentN`·`copy`·`toString`·`hashCode`·`equals` + `copy$default`), 그 전부가 **주 생성자 프로퍼티만** 읽는다.
2. 본문 프로퍼티는 「**안 생기는 것**」이 아니라 「**생기지만 아무도 안 읽는 것**」이다 — `javap` 의 필드 목록이 그것을 보여 준다.
3. `copy` 는 **얕고**, 본문 프로퍼티를 **초기값으로 되돌린다.** 둘 다 조용하다.
4. 구조 분해는 **위치**다. 타입이 같으면 순서가 뒤집혀도 **컴파일러가 못 잡는다.**
5. `data class` 는 **상속당할 수 없을 뿐** 상속하는 것은 된다.
6. `equals` 는 **컴포넌트에 위임**할 뿐이다 — 깊은 비교를 약속하지 않는다.

## 관련 자료

- [15번 주제](../15-class-declaration-constructors-and-init/) — 주 생성자·`init`. **무엇이 「주 생성자 프로퍼티」인가**의 정본이 거기다.
- [16번 주제](../16-properties-backing-field-lateinit-const/) — backing field. **`upper` 에 서랍이 없는 이유**가 거기다.
- [19번 주제](../19-inheritance-open-final-override/) — `final` 기본값. **`data class` 가 `open` 이 안 되는 것**이 그 규칙 위에 선다.
- [23번 주제](../23-sealed-classes-and-when-exhaustiveness/) — `sealed`. **`data class` 를 변형으로 쓰는 자리**가 거기다.
- [24번 주제](../24-enum-class-vs-sealed/) — `enum` 과 `sealed` 의 선택. **인스턴스를 여럿 만들 수 있나**가 갈림길이다.
- [목록의 **26번 주제**](../26-value-class-and-boxing/) — `value class`. 필드 하나짜리 값은 그쪽이다.
- [목록의 **30번 주제**](../30-destructuring-declarations-and-componentn/) — 구조 분해 선언. (4)에서 결론만 썼고 **`componentN` 규약 자체는 거기**가 정본이다.
- [목록의 **32번 주제**](../32-equality-and-equals-contract/) — `==`/`===` 와 `equals` 규약. (7)의 위임 규칙을 **규약 쪽에서** 다시 본다.
- [`../../../java/syntax/14-records/`](../../../java/syntax/14-records/) — Java `record`. **불변을 강제하는 쪽**과의 정면 대비.
- [`../../../../../data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/) — 해시 자료구조. (2)의 사고가 **왜 데이터 손실이 되는지**는 거기가 정본이다.
- [`../../언어-특성/README.md`](../../언어-특성/README.md) §4 — 「값을 값으로」라는 **설계 논지**. 여기는 **생성되는 멤버 목록**까지다.

## 용어 풀이

> **`data class`** — 값처럼 쓸 클래스에 붙이는 수식어. 다섯 멤버를 컴파일러가 만들어 준다.\
> 예: `data class User(val id: Int, val name: String)`.

> **주 생성자 프로퍼티** — 클래스 이름 뒤 괄호에 `val`/`var` 로 적은 것.\
> 예: `data class User(val id: Int)` 의 `id`. `data class User(id: Int)` 의 `id` 는 **프로퍼티가 아니다**.

> **`componentN`** — 구조 분해가 부르는 함수. `component1()`·`component2()` 처럼 **번호가 곧 위치**다.\
> 예: `val (a, b) = p` 는 `p.component1()`·`p.component2()` 로 풀린다.

> **`copy`** — 명세서 값만 물려받아 새 객체를 만드는 함수. 바꿀 것만 이름 붙인 인자로 준다.\
> 예: `a.copy(owner = "lee")`.

> **`copy$default`** — 기본 인자를 처리하려고 컴파일러가 더 만드는 정적 다리 메서드.\
> 예: `javap` 에 `public static User copy$default(User, int, String, int, Object);` 로 보인다.

> **얕은 복사(shallow copy)** — 참조 값만 베끼는 복사. 가리키는 객체는 공유된다.\
> 예: `copy()` 한 두 `Cart` 가 같은 `MutableList` 하나를 본다.

> **`data object`** — 데이터 없는 싱글턴에 `toString`/`hashCode`/`equals` 를 붙여 주는 선언(1.9+).\
> 예: `data object Pending` 의 `toString()` 은 `"Pending"` 이다.

## 더 들어가면

- **왜 본문 프로퍼티를 안 읽게 설계했나** — 읽으면 `copy` 의 시그니처가 정해지지 않는다. 계산 프로퍼티(`upper`)·`lateinit`·위임 프로퍼티까지 들어오면 「무엇을 인자로 받을 것인가」의 답이 없다. **주 생성자 괄호를 명세서로 고정한 것**이 그 문제를 한 줄로 끊은 것이다.
- **Java `record` 와의 방어선 위치** — record 는 **컴포넌트가 곧 불변 필드**이고 본문에 인스턴스 필드를 **아예 못 둔다.** 그래서 (2)의 사고가 **문법 단계에서 불가능**하다. Kotlin 은 본문을 허용하는 대신 「생성 멤버는 명세서만 본다」는 규칙 하나로 처리했다 — **자유도를 주고 사고 가능성을 남긴 쪽**이다.
- **`hashCode` 값을 저장소에 내보내지 마라** — (7)에서 봤듯 컴포넌트 하나가 `Any.hashCode` 로 떨어지면 **실행마다 바뀐다.** 같은 함정의 `enum` 판이 `ordinal` 이고, 그쪽은 [24번 주제](../24-enum-class-vs-sealed/)에서 실측으로 깨뜨린다.
