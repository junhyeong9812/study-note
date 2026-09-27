# kotlin/syntax/22 — `data class`: 무엇이 생성되고 무엇이 안 되나 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javap` 에서 실제로 얻었다.\
> 역어셈블은 **기본 `-jvm-target`(1.8 · `major version: 52`)** 이 정본이다.
> ★★ 아래 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적은 자리가 없다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★ `==` 가 **참**이다 — `note` 는 비교에 안 들어간다

**출력**

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

**왜 그런가**

- `A true` — `note` 가 서로 다른데도 `==` 가 참이다. 생성된 `equals` 는 **주 생성자 프로퍼티(`id`·`name`)만** 대조한다.
- `B true` — `hashCode` 도 같은 재료를 쓴다. ★ **값을 안 찍고 「같나」만 찍은 이유**는 이 문서의 근거를 흔들리지 않는 칸에 두기 위해서다. 컴포넌트가 `Int`·`String` 이면 값도 결정적이지만, 8번처럼 컴포넌트 하나만 바뀌어도 **실행마다 달라진다.** 「같나 다르나」는 그때도 유지된다.
- `C User(id=1, name=kim)` — `toString` 에도 `note` 가 없다.
- `D A 쪽 메모 / B 쪽 메모` — ★ **`note` 자체는 살아 있다.** 이 줄이 없으면 「본문 프로퍼티는 안 만들어진다」로 오해한다. 만들어지고, 읽히고, 쓰인다 — **생성된 다섯 멤버만 그것을 안 볼 뿐이다.**
- `E 1 kim` — `componentN` 은 둘뿐이다.
- `F true` — `copy()` 가 돌려준 객체의 `note` 는 **빈 문자열**이다. `copy` 의 시그니처(`copy(int, String)`)에 `note` 자리가 **없으므로** 물려줄 방법이 없고, 새 객체의 본문이 `""` 로 다시 초기화된다(3번).

### 2. ★★ 필드는 **셋**, `copy` 파라미터는 **둘**

**출력**

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

**왜 그런가**

| `javap` 가 보여 주는 것 | 무엇을 뜻하나 |
|---|---|
| `private final int id;` · `private final java.lang.String name;` | 주 생성자 프로퍼티 — **명세서** |
| `private java.lang.String note;` | 본문 프로퍼티 — **필드는 있다** |
| `getUpper()` 만 있고 필드 없음 | 계산 프로퍼티라 **서랍이 없다**([16번 주제](../16-properties-backing-field-lateinit-const/)) |
| `component1()` · `component2()` | **둘뿐** — 명세서가 둘이라서 |
| `copy(int, java.lang.String)` | **파라미터 둘** — `note` 를 받을 자리가 없다 |
| `copy$default(User, int, String, int, Object)` | 기본 인자(`copy(owner = ...)`)를 처리하는 **정적 다리** |
| `toString()` · `hashCode()` · `equals(Object)` | 나머지 셋 |

- ★★★ **필드는 셋인데 `copy` 는 둘을 받는다** — 이 수치 하나가 이 주제의 전부다.
- `copy$default` 의 네 번째 `int` 는 **어느 인자가 생략됐는지 표시하는 비트마스크**이고 다섯 번째 `Object` 는 자리 채우개다. 이름과 모양은 **JVM 백엔드의 구현**이지 언어 보장이 아니다.
- **안 만들어 주는 것** — `compareTo`(`Comparable` 구현 없음) · 방어 복사 · 검증 · 빌더 · 직렬화 훅. `data` 는 **다섯 멤버 이상을 약속하지 않는다.**

### 3. ★★ 리스트는 **공유되고**, `coupon` 은 **초기값으로 되돌아간다**

**출력**

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

**왜 그런가**

```text
   a = Cart("kim", [사과])               b = a.copy()
        owner --> "kim"                       owner --> "kim"
        items --> [사과] <------------------- items   (같은 리스트 한 개)
        coupon--> "WELCOME"                   coupon--> "WELCOME"

   b.items.add("배")   ->  a.items 도 [사과, 배]      (A·B·C)
   a.coupon = null     ->  c = a.copy(owner="lee")
                           c.coupon 은 "WELCOME"      (E)  <- 읽지 않고 다시 초기화
                           a.coupon 은 null           (F)
```

- `A [사과, 배]` · `B [사과, 배]` · `C true` — **얕은 복사**다. `copy` 는 필드에 든 **참조 값**만 베낀다.
- `D true` — 같은 리스트를 보고 있으니 `equals` 도 참이다.
- ★★★ `E lee WELCOME` — **가장 놀라운 줄**이다. `a.coupon` 은 이미 `null` 인데 사본은 `WELCOME` 이다.\
  `copy` 는 「a 의 상태를 베끼는 함수」가 아니라 「**명세서 값을 인자로 받아 생성자를 다시 부르는 함수**」이기 때문이다. 생성자가 돌면 본문의 `= "WELCOME"` 초기화식이 **다시 실행된다.**
- `F null` — 원본은 그대로 `null` 이다. **두 객체의 본문 상태가 조용히 어긋났다.**
- ★ 막는 법은 `data class` 밖에 있다 — 본문에 상태를 두지 않거나, 생성자에서 **방어 복사**를 하거나, 애초에 읽기 전용 타입으로 받는 것이다.

### 4. ★★ `B` 에서 값이 **뒤집힌다** — 컴파일러는 이름을 안 본다

**출력**

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

**왜 그런가**

```text
   val (x, y)  = p      ->   x = p.component1()   y = p.component2()
   val (y2, x2) = p     ->   y2 = p.component1()  x2 = p.component2()
                                  ^^^^^^^^^^^^^        ^^^^^^^^^^^^^
                              내가 붙인 이름과 무관하게 순서대로 꽂힌다
```

- `A x=10 y=20` · `B x=20 y=10` · `C 10 20`.
- ★★ **경고가 한 줄도 없다.** 구조 분해는 `componentN` 을 **번호 순서대로** 호출하는 문법 설탕일 뿐이고, 왼쪽 괄호의 이름은 **그냥 새 변수 이름**이다.
- ★ 이름을 맞춰 주는 문법이 아니라는 것을 한 문장으로 — 「**`val (a, b) = p` 는 `val a = p.component1(); val b = p.component2()` 와 같다**」.
- ★ Kotlin 2.3.20 에 이름 기반 구조 분해가 **실험 기능**으로 들어와 있지만 아직 Experimental 이다(Kotlin 목록의 「뺀 것」 표).

### 5. ★★ 읽는 코드는 한 글자도 안 고쳤는데 **값이 뒤집힌다**

**출력**

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

**왜 그런가**

- `A x=20 y=10` — `readIt` 안의 `val (x, y) = c` 는 그대로인데 `Coord` 가 `(y, x)` 순이라 **`component1()` 이 `y` 를 돌려준다.**
- `B Coord(y=20, x=10)` — `toString` 은 선언 순서를 정직하게 보여 준다. **선언을 읽으면 알 수 있지만 호출부만 보면 모른다.**
- ★★★ **두 필드의 타입이 `Int` 로 같다는 것이 결정적**이다. 타입이 달랐다면 컴파일 에러가 났을 것이다. 타입이 같은 순간 **타입 시스템이 이 사고에서 완전히 손을 뗀다.**
- ★ 고치는 법 — 구조 분해를 버리고 **이름으로 읽는다**(`c.x`·`c.y`). 필드가 셋 이상이면 거의 항상 이쪽이 맞다.
- ★ 이것은 Java `record` 의 **레코드 패턴**에서도 같다 — 위치 기반 분해는 언어를 가리지 않고 같은 위험을 갖는다([`../../../java/syntax/24-record-patterns/`](../../../java/syntax/24-record-patterns/)).

### 6. ★ `data object` 는 **`toString` 이 이름으로 나온다** — 그것이 차이의 전부다

**출력**

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

**출력** — 멤버 목록으로 본 것

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

**왜 그런가**

| | `object Plain` | `data object Marked` |
|---|---|---|
| `INSTANCE` 정적 필드 | 있다 | 있다 |
| `toString()` | **없다**(`Any` 것이 떨어진다) | **있다** — `"Marked"` |
| `hashCode()` · `equals()` | 없다 | **있다** |
| `copy` · `componentN` | 없다 | **없다** |

- `A Plain / @ 붙음=true` — `Any.toString()` 이 `클래스이름@해시코드` 를 낸다. ★ **그 숫자는 실행마다 바뀌므로** 이 문서는 `@` 앞만 잘라 찍었다.
- `B Marked / @ 붙음=false` — `data object` 가 만들어 준 `toString()` 이 이름만 낸다.
- `C true true` · `E true true` — **둘 다 싱글턴**이다. `data` 를 붙여도 인스턴스가 늘지 않는다. `equals` 가 생기든 말든 **참조가 하나뿐이라 결과가 같다.**
- ★ `copy`·`componentN` 이 **둘 다 없는** 이유 — 명세서(주 생성자 괄호)가 **비어 있기** 때문이다. 만들 재료가 없다.
- ★★ **판 확인** — `data object` 는 **1.9** 에 들어왔고 **2.4.20 에서 경고 없이 컴파일된다.** 다만 이 실행이 증명한 것은 「2.4.20 에서 된다」뿐이고 「1.9 부터다」는 [Kotlin 목록](../README.md)의 판 이력표에 적힌 것을 인용한 것이다.

### 7. ★★ 에러 **여섯 줄**, 그리고 **에러가 안 나는 선언이 하나** 있다

**출력**

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

**왜 그런가**

| 선언 | 결과 | 문구 |
|---|---|---|
| `data class Ok1(val x: Int) : Base("b")` | ★ **통과한다** | — |
| `open data class Bad1` | 에러 **2줄** | `modifier 'open' is incompatible with 'data'.` + 반대 방향 |
| `class Sub : Ok1(1)` | 에러 | `this type is final, so it cannot be extended.` |
| `data class Bad3()` | 에러 | `data class must have at least one primary constructor parameter.` |
| `data class Bad4(x: Int)` | 에러 | `primary constructor of data class must only have property ('val' / 'var') parameters.` |
| `fun component1() = 99` | 에러 **2줄** | `conflicting overloads:` (선언 자리 + 함수 자리) |

- ★★★ **`data class Ok1(...) : Base("b")` 는 통과한다.** 「`data class` 는 상속을 못 한다」로 외우면 **절반이 틀린다** — 막히는 것은 **상속당하는 방향**뿐이다(10번).
- `open` 과 `data` 는 서로 양립 불가라 컴파일러가 **양방향으로 한 번씩** 말한다. [19번 주제](../19-inheritance-open-final-override/)의 `private override` 에서도 똑같은 모양이 나왔다 — **「양립 불가」 에러는 2줄이 기본형이라고 생각해 두는 편이 안전하다.**
- `Bad3()` 이 막히는 것과 **`data object` 가 따로 있는 것**은 같은 사실의 앞뒷면이다 — 명세서가 비면 `copy`·`componentN` 을 만들 수 없으므로, 데이터 없는 값에는 **다른 문법**(`data object`)을 줬다(6번).
- `Bad4(x: Int)` — 괄호에 적혀 있어도 `val`/`var` 가 없으면 **생성자 인자일 뿐 프로퍼티가 아니다.** 명세서에 못 오른다([15번 주제](../15-class-declaration-constructors-and-init/)).

### 8. ★ `Wrap` 둘은 **다르다** — `data` 는 깊은 비교를 약속하지 않는다

**출력**

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

**왜 그런가**

```text
   data class Wrap(val p: Plain)              data class Flat(val v: Int)
       Wrap.equals  ->  p.equals(other.p)         Flat.equals -> v == other.v
                             |                                      |
                             v                                      v
                 Plain 은 equals 를 안 고쳤다                 Int 는 값 비교
                 -> Any.equals = 참조 비교                    -> 같다
                 -> A false · B false                         -> C true · D true
```

- `A false` · `B false` — **`data` 를 붙였는데도 다르다.** 컴포넌트 `Plain` 이 `equals` 를 오버라이드하지 않아 **참조 비교**로 떨어지기 때문이다.
- `C true` · `D true` — `Int` 컴포넌트는 값 비교다.
- ★★ 생성된 `equals` 의 계약은 「깊게 비교한다」가 아니라 「**컴포넌트마다 그 컴포넌트의 `equals` 를 부른다**」다. 컴포넌트가 얕으면 결과도 얕다.
- `E Wrap(p=Plain` — `toString` 안에 **`Plain@해시코드` 가 박혀 나오므로** 그 앞에서 잘랐다. 자르지 않으면 이 블록은 **실행마다 달라져 재대조가 불가능**해진다.
- ★ **배열 컴포넌트가 같은 함정**이다 — `Array` 의 `equals` 는 참조 비교라 내용이 같아도 다르다. Java `record` 도 완전히 같다([`../../../java/syntax/14-records/`](../../../java/syntax/14-records/)).

### 9. 본문까지 읽으면 **`copy` 의 시그니처가 정해지지 않는다**

**왜 그런가**

```text
   만약 본문 프로퍼티까지 읽는다면 ...

   data class User(val id: Int) {
       var note: String = ""              -> copy(id, note) ?
       val upper: String get() = ...      -> copy(id, upper) ?   계산값인데 어떻게 받나
       lateinit var conn: Conn            -> copy(id, conn) ?    아직 없을 수도 있는데
       val cache by lazy { heavy() }      -> copy(id, cache) ?   평가를 강제하게 된다
   }
```

- **계산 프로퍼티에는 쓸 자리가 없다.** `val upper get() = name.uppercase()` 는 서랍이 없어서([16번 주제](../16-properties-backing-field-lateinit-const/)) 값을 받아 넣을 곳이 없다.
- `lateinit`·위임 프로퍼티까지 들어오면 「무엇을 인자로 받고 무엇을 뺄 것인가」에 **일관된 답이 없다.**
- ★ 그래서 **주 생성자 괄호를 명세서로 고정**했다. 규칙이 한 줄이고, `javap` 로 셀 수 있고, `copy` 시그니처가 선언만 보면 결정된다.
- ★ **대가는 (2)·(3)의 침묵**이다 — 본문에 상태를 얹는 것을 문법이 **막지 않으면서** 생성 멤버는 그것을 **안 본다.** 「자유를 주고 사고 가능성을 남긴 쪽」이고, Java `record` 는 반대로 골랐다(11번).

### 10. **상속하는 것은 되고, 상속당하는 것은 안 된다**

**왜 그런가**

```text
   Base (open class)
     ^
     |  된다  ->  data class Ok1(val x: Int) : Base("b")
   Ok1 (data class)
     ^
     |  안 된다 -> class Sub : Ok1(1)
   Sub                 error: this type is final, so it cannot be extended.
```

- **위쪽은 열려 있다** — `data class` 가 다른 클래스·인터페이스를 상속하는 것은 아무 제약이 없다(7번의 `Ok1`).
- **아래쪽은 닫혀 있다** — `data class` 는 **언제나 `final`** 이고 `open` 을 붙일 수 없다.
- ★ 이 `final` 은 [19번 주제](../19-inheritance-open-final-override/)의 기본값 규칙과 **다른 층**이다. 거기서는 `open` 을 적으면 열렸지만, `data class` 는 **`open` 을 적는 것 자체가 금지**다.
- ★ 왜 막았나 — 하위 클래스가 필드를 더하면 `equals` 가 **대칭성**을 잃는다(`a.equals(b)` 와 `b.equals(a)` 가 갈린다). 그 고전적인 문제를 **상속을 막는 것으로** 끊었다. Java `record` 도 같은 이유로 `final` 이다.
- ★ 계층이 필요하면 `data class` 를 **변형으로 쓰고 뿌리는 `sealed`** 로 둔다([23번 주제](../23-sealed-classes-and-when-exhaustiveness/)).

### 11. `record` 는 **본문에 인스턴스 필드를 못 둔다** — 그래서 1번의 사고가 불가능하다

**왜 그런가**

```text
   Kotlin data class                    Java record
   -----------------------------------  -----------------------------------
   본문에 var 를 둘 수 있다             본문에 인스턴스 필드를 둘 수 없다
     -> 생성 멤버가 그것을 안 본다          -> 안 볼 것이 애초에 없다
   var 파라미터가 허용된다               컴포넌트가 전부 final 이다
     -> 가변 data class 가 정상 문법        -> 불변이 강제된다
   검증 자리는 init { } (관용)           컴팩트 생성자가 문법으로 있다
   copy 가 생긴다                        copy 가 없다(직접 쓴다)
```

- Java `record` 는 **본문에 인스턴스 필드를 선언할 수 없다**(정적 필드는 가능). 그래서 「필드는 셋인데 `equals` 는 둘만 본다」는 상황이 **문법 단계에서 성립하지 않는다.**
- ★★ 「**방어선의 위치가 다르다**」 — record 는 **문법으로 막고**, `data class` 는 **규칙으로 정리한다.** 전자는 사고가 불가능하고 후자는 사고가 조용하다.
- ★ 대신 Kotlin 쪽이 얻은 것도 있다 — `copy` 가 공짜이고(record 에는 없다), 본문에 계산 프로퍼티·부수 상태를 둘 자유가 있고, `var` 가 필요하면 쓸 수 있다.
- ★ **얕은 복사는 둘 다 같다.** record 의 컴포넌트가 컬렉션이면 그쪽도 공유된다 — 이 함정은 방어선 위치와 무관하다.

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

★ **흔들리는 칸과 안 흔들리는 칸**(제출 전 재대조에서 「고칠 것」과 「설계상 다른 것」을 가르는 선언이다)

| 흔들린다 | 안 흔들린다 |
|---|---|
| 기본 `toString()` 의 `@` **뒤 해시코드 숫자** — **그래서 싣지 않았다**(6번·8번에서 잘랐다) | 컴파일 에러의 **문구·`파일:줄:칸`·캐럿 줄** |
| `Wrap` 류의 `hashCode()` **값** — **그래서 불리언만 실었다**(1번·8번) | `javap` 출력 **전체**(필드 목록·메서드 시그니처·나열 순서) |
| | `hashCode()` 가 **같나 다르나** |
| | 모든 **종료 코드** · `println` 출력 |

> 근거 — 캡처 스크립트를 처음부터 다시 돌려 **블록 전체를 바이트 단위로 대조**했고, 이 주제에서 **달라진 파일은 0개**였다.

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `dcgen.kt` | ★★★ **본문 `var` 가 `equals`/`toString`/`copy` 에서 빠지는 것** | `kotlinc` → `java` → `javap -p` |
| `dccopy.kt` | ★★ `copy` 가 **얕은 것** · 본문 프로퍼티가 **초기값으로 되돌아가는 것** | `kotlinc` → `java` |
| `dcorder.kt` | 구조 분해가 **위치 기반**이라 이름을 바꾸면 뒤집히는 것 | `kotlinc` → `java` |
| `dcorder2.kt` | ★★ **선언 순서가 바뀌면 읽는 쪽이 조용히 깨지는 것** | `kotlinc` → `java` |
| `dcobject.kt` | `data object` 가 만드는 **세 메서드** · 싱글턴인 것 | `kotlinc` → `java` → `javap -p` |
| `dcforbid.kt` | 금지 사례 전수 · ★ **상속하는 쪽은 통과하는 것** | `kotlinc` (컴파일 실패가 결과) |
| `dchash.kt` | ★ `equals` 가 **컴포넌트에 위임**할 뿐인 것 | `kotlinc` → `java` |
| `form22.kt` | 명세서·본문·`copy`·구조 분해·`data object` 가 **한 프로그램에서 도는 것**(`Z`) | `kotlinc` → `java` |

**구현 의존 항목** — `copy$default` 의 **이름과 시그니처**, `javap` 가 멤버를 나열하는 **순서**, 에러 메시지의 **문구 그 자체**, `toString` 의 **출력 형식** — 전부 이 컴파일러·JDK 판의 산출물이다.\
반면 **「다섯 멤버가 생성된다」·「그 전부가 주 생성자 프로퍼티만 읽는다」·「`copy` 는 얕다」·「구조 분해는 위치 기반이다」·「`data class` 는 `final` 이다」** 는 **언어의 계약**이다.

**★ 던져 봤더니 예상과 달랐던 것 — 두 건**

1. ★★★ **`data class` 가 다른 클래스를 상속하는 것은 된다.** 「`data class` 는 상속과 무관하다」고 알고 던졌는데 `data class Ok1(val x: Int) : Base("b")` 가 **에러 없이 컴파일됐다**(7번). 막히는 것은 **상속당하는 방향**뿐이다 — **「못 한다」를 방향 없이 외우면 절반이 틀린다.**
2. ★★ **`copy` 가 본문 프로퍼티를 「안 베끼는」 것이 아니라 「초기값으로 되돌리는」 것이었다.** `a.coupon = null` 로 바꾼 뒤 복사했는데 사본이 `null` 이 아니라 `"WELCOME"` 이었다(3번). 「안 베낀다」로만 알고 있으면 **사본이 `null` 일 것**이라고 예측하게 된다 — 실제로는 **생성자가 다시 돌아 초기화식이 재실행**된다.

**안 터진 것도 출력이다** — 4번·5번의 구조 분해 사고는 **경고 한 줄 없이** 컴파일되고 돈다. 「`data class` 필드 순서를 바꾸는 것」은 `javap` 로도 안 잡히고(시그니처가 `component1()`·`component2()` 로 같다) **테스트가 없으면 배포까지 간다.** 컴파일러의 침묵이 이 주제에서 가장 위험한 출력이다.
