# kotlin/syntax/24 — `enum class` 와 `sealed` 선택 기준 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 에서 실제로 얻었다.\
> 역어셈블은 **기본 `-jvm-target`(1.8 · `major version: 52`)** 이 정본이다. 리플렉션 실험에는 `kotlin-reflect.jar` 를 썼다.
> ★★ 아래 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적은 자리가 없다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★ `values()` 는 **매번 다른 배열**, `entries` 는 **늘 같은 객체**

**출력**

```text
===== 소스: enumdata.kt =====
enum class Color(val hex: String) {
    RED("#f00"), GREEN("#0f0"), BLUE("#00f");

    fun bright() = "$name($hex)"
}

fun main() {
    println("A ${Color.entries}")
    println("B ${Color.entries.size} ${Color.values().size}")
    println("C ${Color.values() === Color.values()}")
    println("D ${Color.entries === Color.entries}")
    println("E ${Color.RED === Color.valueOf("RED")}")
    println("F ${Color.BLUE.ordinal} ${Color.BLUE.name} ${Color.BLUE.bright()}")
    println("G ${Color.entries.javaClass.name}")
    println("H ${Color.values().javaClass.name}")
    val arr = Color.values()
    arr[0] = Color.BLUE
    println("I ${Color.values()[0]} ${arr[0]}")
}
===== kotlinc enumdata.kt -d o24e =====
(exit 0)
===== java -cp o24e:kotlin-stdlib.jar EnumdataKt =====
A [RED, GREEN, BLUE]
B 3 3
C false
D true
E true
F 2 BLUE BLUE(#00f)
G kotlin.enums.EnumEntriesList
H [LColor;
I RED BLUE
(exit 0)
```

**왜 그런가**

| 줄 | 값 | 뜻 |
|---|---|---|
| `A` | `[RED, GREEN, BLUE]` | `entries` 는 **선언 순서**다 |
| `B` | `3 3` | 개수는 같다 |
| `C` | `false` | ★ `values()` 는 **부를 때마다 새 배열** |
| `D` | `true` | ★ `entries` 는 **늘 같은 객체** |
| `E` | `true` | `valueOf` 는 **같은 인스턴스**를 돌려준다 |
| `F` | `2 BLUE BLUE(#00f)` | `ordinal`·`name`·상수별 데이터 |
| `G` | `kotlin.enums.EnumEntriesList` | `entries` 의 런타임 타입 — `List` 다 |
| `H` | `[LColor;` | `values()` 는 **배열**이라 `List` API 가 없다 |
| `I` | `RED BLUE` | ★ **방어 복사** — 내 배열만 바뀌었다 |

- ★★ `C`/`D` 가 갈리는 이유 — `values()` 는 **`$VALUES.clone()`** 을 돌려주고, `entries` 는 `$ENTRIES` 를 **그대로** 돌려준다(2번의 `javap`).
- `I` 줄이 그 결과다 — 내가 받은 배열의 0번을 `BLUE` 로 덮어도 **다음 `values()` 는 원본을 다시 복사**하므로 `RED` 가 나온다. **원본을 못 건드리게 하려고 매번 복사하는 것**이다.
- ★ 그래서 반복에는 `entries` 가 낫다 — 할당이 없고 `List` 연산이 붙는다. ★ **다만 이 문서는 시간을 재지 않았다.** 근거는 「`clone()` 호출이 있고 없고」이지 속도 측정이 아니다.
- ★ `entries` 는 **1.9** 부터다. 그 이전 코드는 `values()` 를 쓴다.

### 2. ★ `java.lang.Enum<Color>` 를 상속한 **진짜 클래스**다

**출력**

```text
===== javap -p o24e/Color.class =====
Compiled from "enumdata.kt"
public final class Color extends java.lang.Enum<Color> {
  private final java.lang.String hex;
  public static final Color RED;
  public static final Color GREEN;
  public static final Color BLUE;
  private static final Color[] $VALUES;
  private static final kotlin.enums.EnumEntries $ENTRIES;
  private Color(java.lang.String);
  public final java.lang.String getHex();
  public final java.lang.String bright();
  public static Color[] values();
  public static Color valueOf(java.lang.String);
  public static kotlin.enums.EnumEntries<Color> getEntries();
  private static final Color[] $values();
  static {};
}
(exit 0)
```

**왜 그런가**

```text
   public final class Color extends java.lang.Enum<Color>
     private final String hex;                      <- 생성자 인자가 인스턴스 필드
     public static final Color RED, GREEN, BLUE;    <- 상수 = static final 필드
     private static final Color[] $VALUES;          <- 원본 배열(숨어 있다)
     private static final EnumEntries $ENTRIES;     <- entries 용
     private Color(String);                         <- ★ 생성자가 private
     public static Color[] values();                <- $VALUES.clone()
     public static EnumEntries<Color> getEntries();  <- $ENTRIES 그대로
     static {};                                     <- 여기서 셋을 만든다
```

- 상수는 **`<clinit>`(`static {}`)이 딱 한 번 만드는 `public static final` 필드**다. 그래서 **싱글턴이 공짜**이고 `===` 로 비교해도 된다(6번의 `G`).
- ★ 생성자가 **`private`** 이라 밖에서 인스턴스를 못 만든다. **`sealed` 와 명단을 닫는 방식이 다르다** — `sealed` 는 **하위 타입**을 막고, `enum` 은 **인스턴스 생성**을 막는다.
- `hex` 가 인스턴스 필드인 것을 보라 — **`enum` 도 데이터를 든다.** 다만 상수당 **한 벌 고정**이다(10번).
- ★ `$VALUES` 와 `$ENTRIES` 가 **둘 다** 있는 이유 — `values()` 는 매번 복사본을 만들어야 하므로 **원본 배열**(`$VALUES`)이 필요하고, `entries` 는 복사 없이 돌려줄 **읽기 전용 뷰**(`$ENTRIES`)가 따로 필요하다. **이름과 존재는 JVM 백엔드의 구현**이다.

### 3. ★★★ `B` 에 **말이 안 되는 객체**가 경고 없이 만들어진다

**출력**

```text
===== 소스: modelenum.kt =====
enum class PayState { SUCCESS, FAILURE, PENDING }

data class PayResult(
    val state: PayState,
    val amount: Int? = null,
    val reason: String? = null,
)

fun describe(r: PayResult): String = when (r.state) {
    PayState.SUCCESS -> "${r.amount!!}원 결제"
    PayState.FAILURE -> "실패: ${r.reason!!}"
    PayState.PENDING -> "대기"
}

fun main() {
    println("A ${describe(PayResult(PayState.SUCCESS, amount = 1000))}")
    val impossible = PayResult(PayState.SUCCESS, reason = "카드 거절")
    println("B $impossible")
    println("C ${PayState.SUCCESS === PayState.SUCCESS}")
    println("D ${PayState.entries.size}")
    println("E ${runCatching { describe(impossible) }.exceptionOrNull()?.javaClass?.name}")
}
===== kotlinc modelenum.kt -d o24me =====
(exit 0)
===== java -cp o24me:kotlin-stdlib.jar ModelenumKt =====
A 1000원 결제
B PayResult(state=SUCCESS, amount=null, reason=카드 거절)
C true
D 3
E java.lang.NullPointerException
(exit 0)
```

**왜 그런가**

```text
   PayResult(state: PayState, amount: Int?, reason: String?)
                               ^^^^^^^^^^   ^^^^^^^^^^^^^^^
                               상태마다 다른 데이터를 한 클래스에 욱여넣으려니
                               전부 nullable 이 됐다

   PayResult(SUCCESS, amount = null, reason = "카드 거절")
             ^^^^^^^  ^^^^^^^^^^^^^  말이 안 되는 조합인데 컴파일된다 (B)
                |
                v
   describe -> "${r.amount!!}원"  ->  NullPointerException  (E)
```

- `A 1000원 결제` — 정상 경로는 잘 돈다.
- ★★★ `B PayResult(state=SUCCESS, amount=null, reason=카드 거절)` — **성공인데 금액이 없고 실패 사유가 있는 객체**다. **경고 한 줄 없이** 만들어진다.
- `C true` — `enum` 상수는 싱글턴이다.
- `D 3` — 인스턴스가 정확히 셋이다(4번).
- `E java.lang.NullPointerException` — `describe(impossible)` 이 `r.amount!!` 에서 터진다.
- ★★ **근본 원인은 `describe` 가 아니라 `PayResult`** 다. `!!` 는 **설계가 이미 허용해 버린 구멍을 런타임으로 미뤄 둔 표시**일 뿐이다. `describe` 를 아무리 고쳐도 `B` 같은 객체는 계속 만들어진다.

### 4. ★★ `!!` 가 **한 개도 없다** — 그리고 `D` 와 `E` 가 갈린다

**출력**

```text
===== 소스: modelsealed.kt =====
sealed interface Pay
data class Success(val amount: Int) : Pay
data class Failure(val reason: String) : Pay
data object Pending : Pay

fun describe(p: Pay): String = when (p) {
    is Success -> "${p.amount}원 결제"
    is Failure -> "실패: ${p.reason}"
    Pending -> "대기"
}

fun main() {
    println("A ${describe(Success(1000))}")
    println("B ${describe(Failure("카드 거절"))}")
    println("C ${describe(Pending)}")
    println("D ${Success(1000) === Success(1000)} ${Success(1000) == Success(1000)}")
    println("E ${Pending === Pending}")
    val many = listOf(Success(1000), Success(2000), Success(3000))
    println("F ${many.size} ${many.distinct().size}")
}
===== kotlinc modelsealed.kt -d o24ms =====
(exit 0)
===== java -cp o24ms:kotlin-stdlib.jar ModelsealedKt =====
A 1000원 결제
B 실패: 카드 거절
C 대기
D false true
E true
F 3 3
(exit 0)
```

**왜 그런가**

| 줄 | 값 | 뜻 |
|---|---|---|
| `A`·`B`·`C` | `1000원 결제` · `실패: 카드 거절` · `대기` | 세 변형이 각자 자기 데이터를 갖는다 |
| `D` | `false true` | ★ `Success(1000)` 둘은 **다른 객체**이고 `==` 만 참이다 |
| `E` | `true` | ★ `data object Pending` 은 **싱글턴**이다 |
| `F` | `3 3` | `Success` 인스턴스 셋이 `distinct()` 후에도 셋 |

- `describe` 에 **`!!` 가 0개**다. `Success` 안에서 `amount` 는 **`Int`**(널 불가), `Failure` 안에서 `reason` 은 **`String`** 이다. 3번은 두 개였다.
- ★★ `D`/`E` 가 갈리는 이유 — `Success` 는 **`data class`** 라 호출할 때마다 새 객체를 만들고, `Pending` 은 **`data object`** 라 객체가 하나다([22번 주제](../22-data-class-generated-members/)).
- ★ `F` 가 「같은 변형의 인스턴스를 여럿」의 증거다. `enum` 으로는 **`SUCCESS` 를 금액별로 여러 개 만들 수 없다.**

### 5. ★★ 에러 **세 줄** — 없는 파라미터, 빠진 파라미터, 없는 프로퍼티

**출력**

```text
===== 소스: modelbad.kt =====
sealed interface Pay
data class Success(val amount: Int) : Pay
data class Failure(val reason: String) : Pay
data object Pending : Pay

fun main() {
    val impossible = Success(reason = "카드 거절")
    println(impossible)
    val p: Pay = Pending
    println(p.amount)
}
===== kotlinc modelbad.kt -d o24mb =====
modelbad.kt:7:22: error: no value passed for parameter 'amount'.
    val impossible = Success(reason = "카드 거절")
                     ^^^^^^^
modelbad.kt:7:30: error: no parameter with name 'reason' found.
    val impossible = Success(reason = "카드 거절")
                             ^^^^^^
modelbad.kt:10:15: error: unresolved reference 'amount' on receiver of type 'Pay'.
    println(p.amount)
              ^^^^^^
(exit 1)
```

**왜 그런가**

| 시도 | 에러 |
|---|---|
| `Success(reason = "카드 거절")` | `no value passed for parameter 'amount'.` — **있어야 할 것이 없다** |
| 〃 | `no parameter with name 'reason' found.` — **없어야 할 것을 줬다** |
| `p.amount`(`p: Pay`) | `unresolved reference 'amount' on receiver of type 'Pay'.` — **변형을 좁히기 전에는 못 읽는다** |

- ★★★ 3번의 `PayResult(SUCCESS, reason = "카드 거절")` 은 **컴파일되고**, 여기 `Success(reason = ...)` 는 **컴파일이 안 된다.** 같은 값을 만들려는 같은 시도인데 결과가 정반대다.
- 그것이 「**불가능한 상태를 표현할 수 없게 만든다**」의 실체다 — 말이 안 되는 조합이 **타입에 존재하지 않으므로** 문법 단계에서 막힌다.
- ★ 세 번째 에러도 같은 집안이다 — `Pay` 로만 들고 있으면 `amount` 를 못 읽는다. **`when` 으로 좁혀야 읽을 수 있고**, 그 `when` 은 완결성을 요구한다([23번 주제](../23-sealed-classes-and-when-exhaustiveness/)). **설계가 사용법을 강제하는 사슬**이 여기서 닫힌다.

### 6. ★ `entries` 는 **값 목록**, `sealedSubclasses` 는 **클래스 목록**

**출력**

```text
===== 소스: enumref.kt =====
import kotlin.reflect.KClass

enum class Color { RED, GREEN, BLUE }

sealed interface Shape
data class Circle(val r: Double) : Shape
data class Rect(val w: Double, val h: Double) : Shape
data object Empty : Shape

fun main() {
    println("A ${Color.entries.map { it.name }}")
    val subs: List<KClass<out Shape>> = Shape::class.sealedSubclasses
    println("B ${subs.mapNotNull { it.simpleName }.sorted()}")
    println("C ${subs.size}")
    println("D ${Color::class.java.isEnum} ${Shape::class.java.isEnum}")
    println("E ${Circle(1.0) === Circle(1.0)} ${Circle(1.0) == Circle(1.0)}")
    println("F ${Empty === Empty}")
    println("G ${Color.entries.map { it === Color.valueOf(it.name) }}")
}
===== kotlinc -cp kotlin-reflect.jar enumref.kt -d o24r =====
(exit 0)
===== java -cp o24r:kotlin-stdlib.jar:kotlin-reflect.jar EnumrefKt =====
A [RED, GREEN, BLUE]
B [Circle, Empty, Rect]
C 3
D true false
E false true
F true
G [true, true, true]
(exit 0)
```

**왜 그런가**

| 줄 | 값 | 뜻 |
|---|---|---|
| `A` | `[RED, GREEN, BLUE]` | `entries` 는 **값**이다 — 바로 순회한다 |
| `B` | `[Circle, Empty, Rect]` | `sealedSubclasses` 는 **클래스**다 — 인스턴스는 내가 만든다 |
| `C` | `3` | 개수 |
| `D` | `true false` | `Color` 는 JVM enum, **`Shape` 는 아니다** |
| `E` | `false true` | `Circle(1.0)` 둘은 다른 객체, 값만 같다 |
| `F` | `true` | `data object Empty` 는 싱글턴 |
| `G` | `[true, true, true]` | `valueOf` 가 **같은 객체**를 돌려준다 |

- ★★ **`B` 를 정렬해서 찍은 이유** — `sealedSubclasses` 의 **순서는 보장되지 않는다.** 5판을 돌려 모두 같았지만 그것은 **관찰이지 계약이 아니다.** 근거로 쓸 칸은 **집합과 개수**이므로 정렬해서 결정적으로 만들었다.\
  ★ 반대로 `A` 는 정렬하지 않았다 — **`entries` 의 선언 순서는 계약**이다.
- ★ 테스트에서 모든 변형을 돌리기에는 **`enum` 이 훨씬 싸다.** `entries` 를 그냥 `forEach` 하면 되는데, `sealedSubclasses` 는 **클래스만 주므로 생성자 인자를 내가 정해야** 한다. 게다가 **`kotlin-reflect` 의존이 붙는다.**
- ★ `D` 줄이 갈라 주는 것 — `sealed` 는 **JVM 층의 enum 이 아니다.** `EnumSet`·`EnumMap` 같은 `enum` 전용 자료구조를 못 쓴다(11번).

### 7. ★ **같은 문구로 깨진다** — 그래서 완결성은 기준이 아니다

**출력**

```text
===== 소스: enumwhen.kt =====
enum class Status { NEW, PENDING, DONE }

fun label(s: Status): String = when (s) {
    Status.NEW -> "새로 만듦"
    Status.DONE -> "끝남"
}
===== kotlinc enumwhen.kt -d o24w =====
enumwhen.kt:3:32: error: 'when' expression must be exhaustive. Add the 'PENDING' branch or an 'else' branch.
fun label(s: Status): String = when (s) {
                               ^^^^
(exit 1)
```

**왜 그런가**

- 「`'when' expression must be exhaustive. Add the 'PENDING' branch or an 'else' branch.`」 — [23번 주제](../23-sealed-classes-and-when-exhaustiveness/)에서 `sealed` 로 본 것과 **한 글자 차이**(빠진 이름)뿐이다.
- ★★ 그러므로 **「완결성 때문에 `sealed` 를 쓴다」는 말은 틀렸다.** `enum` 도 똑같이 된다. 완결성은 **둘의 공통점**이지 갈림길이 아니다.
- 갈림길은 **① 변형마다 다른 데이터**(3번·4번) · **② 같은 변형의 인스턴스가 여럿**(4번) 둘이다.
- ★ `enum` 쪽이 하나 더 갖는 안전망이 있다 — **상수별 추상 메서드**다. `abstract fun` 을 두면 상수를 늘렸을 때 **`when` 이 없어도** 컴파일이 깨진다([`../../../java/syntax/13-enum-classes/`](../../../java/syntax/13-enum-classes/)가 정본이다).

**출력** — `enum` 이 추가로 막는 것들

```text
===== 소스: enumforbid.kt =====
data enum class Bad1 { A, B }

enum class Bad2 { A }
class SubEnum : Bad2()

sealed enum class Bad3 { A }

enum class Bad4 {
    A;
    override fun equals(other: Any?) = true
}
===== kotlinc enumforbid.kt -d o24fb =====
enumforbid.kt:1:1: error: modifier 'data' is not applicable to 'enum class'.
data enum class Bad1 { A, B }
^^^^
enumforbid.kt:4:17: error: this type is final, so it cannot be extended.
class SubEnum : Bad2()
                ^^^^
enumforbid.kt:4:17: error: cannot access 'constructor(): Bad2': it is private in 'Bad2'.
class SubEnum : Bad2()
                ^^^^
enumforbid.kt:6:1: error: modifier 'sealed' is not applicable to 'enum class'.
sealed enum class Bad3 { A }
^^^^^^
enumforbid.kt:10:5: error: 'equals' in 'Bad4' is final and cannot be overridden.
    override fun equals(other: Any?) = true
    ^^^^^^^^
(exit 1)
```

| 시도 | 문구 |
|---|---|
| `data enum class` | `modifier 'data' is not applicable to 'enum class'.` |
| `class SubEnum : Bad2()` | `this type is final, so it cannot be extended.` + `cannot access 'constructor(): Bad2': it is private` |
| `sealed enum class` | `modifier 'sealed' is not applicable to 'enum class'.` |
| `override fun equals(...)` | `'equals' in 'Bad4' is final and cannot be overridden.` |

- ★★ **`data` 가 안 붙는 이유가 마지막 줄에 있다** — `enum` 의 `equals` 는 **이미 `final`** 이라 `data` 가 만들 자리가 없다. `hashCode` 도 마찬가지다.
- ★ `enum` 을 상속하려 하면 에러가 **두 줄**이다 — **`final` 이라서** 하나, **생성자가 `private` 이라서** 하나. 2번의 `javap` 가 그 둘을 다 보여 준다.
- ★ `sealed` 도 안 붙는다 — `enum` 은 **이미 닫힌 명단**이라 겹치는 선언이다.

### 8. ★★ `IllegalArgumentException: No enum constant Status.PENDING`

**출력**

```text
===== 소스: enumfail.kt =====
enum class Status { NEW, DONE }

fun main() {
    System.err.println("--- Status.valueOf(\"PENDING\") 을 부른다 ---")
    Status.valueOf("PENDING")
}
===== kotlinc enumfail.kt -d o24f =====
(exit 0)
===== java -cp o24f:kotlin-stdlib.jar EnumfailKt =====
--- Status.valueOf("PENDING") 을 부른다 ---
Exception in thread "main" java.lang.IllegalArgumentException: No enum constant Status.PENDING
	at java.base/java.lang.Enum.valueOf(Enum.java:293)
	at Status.valueOf(enumfail.kt)
	at EnumfailKt.main(enumfail.kt:5)
	at EnumfailKt.main(enumfail.kt)
(exit 1)
```

**왜 그런가**

- 예외 타입과 메시지가 그대로 답이다 — `java.lang.IllegalArgumentException: No enum constant Status.PENDING`.
- ★★★ **마커를 `System.err.println` 으로 찍은 이유** — 스택트레이스는 **표준 오류**로 나간다. 마커를 `println`(표준 출력)으로 찍으면 터미널에서는 섞여 보이는데 **파이프로 받으면 순서가 달라진다.** 둘을 같은 스트림으로 몰아야 **한 블록에 담은 순서가 재현된다.**
- ★ 스택트레이스에서 **근거로 써도 되는 줄과 안 되는 줄**:

| 줄 | 근거로 | 왜 |
|---|---|---|
| `Exception in thread "main" java.lang.IllegalArgumentException: No enum constant Status.PENDING` | ★ **써도 된다** | 타입·메시지는 계약에 가깝다 |
| `at java.base/java.lang.Enum.valueOf(Enum.java:293)` | **쓰면 안 된다** | **JDK 판마다 줄 번호가 바뀐다** |
| `at Status.valueOf(enumfail.kt)` · `at EnumfailKt.main(enumfail.kt:5)` | 써도 된다 | 내 소스의 위치다 |

**안 터뜨리는 길**

```text
===== 소스: enumsafe.kt =====
enum class Status { NEW, DONE }

fun main() {
    println("A ${Status.entries.find { it.name == "PENDING" }}")
    println("B ${runCatching { Status.valueOf("PENDING") }.exceptionOrNull()?.javaClass?.name}")
    println("C ${runCatching { Status.valueOf("PENDING") }.exceptionOrNull()?.message}")
    println("D ${Status.valueOf("DONE")}")
}
===== kotlinc enumsafe.kt -d o24sf =====
(exit 0)
===== java -cp o24sf:kotlin-stdlib.jar EnumsafeKt =====
A null
B java.lang.IllegalArgumentException
C No enum constant Status.PENDING
D DONE
(exit 0)
```

- `A null` — `entries.find { }` 는 **없으면 `null`** 이다.
- `B`·`C` — `runCatching` 으로 예외를 **값으로** 받는다(목록의 **49번 주제**).
- ★ stdlib 에 **`valueOf` 의 널 안전판이 없다.** 그래서 이 두 관용구가 쓰인다.
- ★★ **`sealed` 에는 이 문제가 아예 없다** — 문자열에서 타입을 만들어 주는 기본 장치가 없으니 처음부터 내가 매핑을 쓴다. **공짜로 주는 것이 없어서 함정도 없다.**

### 9. ★★★ 이름으로 저장한 것은 **버티고**, `ordinal` 로 저장한 것은 **조용히 다른 값**이 된다

**출력** — 상수가 둘인 판에서 저장

```text
===== 소스: ordv1.kt =====
import java.io.*

enum class Status { NEW, DONE }

fun main() {
    println("A ${Status.entries.map { "${it.ordinal}:${it.name}" }}")
    val bos = ByteArrayOutputStream()
    ObjectOutputStream(bos).use { it.writeObject(Status.DONE) }
    File("status.bin").writeBytes(bos.toByteArray())
    File("status.ordinal").writeText(Status.DONE.ordinal.toString())
    val printable = String(bos.toByteArray(), Charsets.ISO_8859_1)
        .map { if (it.code in 32..126) it else '.' }.joinToString("")
    println("B $printable")
    println("C 저장한 ordinal = ${Status.DONE.ordinal}")
}
===== kotlinc ordv1.kt -d o24o1 =====
(exit 0)
===== java -cp o24o1:kotlin-stdlib.jar Ordv1Kt =====
A [0:NEW, 1:DONE]
B ....~r..Status...........xr..java.lang.Enum...........xpt..DONE
C 저장한 ordinal = 1
(exit 0)
```

**출력** — 가운데에 상수 하나를 끼우고 읽기

```text
===== 소스: ordv2.kt =====
import java.io.*

enum class Status { NEW, PENDING, DONE }

fun main() {
    println("A ${Status.entries.map { "${it.ordinal}:${it.name}" }}")
    val back = ObjectInputStream(ByteArrayInputStream(File("status.bin").readBytes())).readObject() as Status
    println("B $back ${back.ordinal} ${back === Status.DONE}")
    val savedOrdinal = File("status.ordinal").readText().toInt()
    println("C 저장했던 ordinal $savedOrdinal 로 읽으면 = ${Status.entries[savedOrdinal]}")
}
===== kotlinc ordv2.kt -d o24o2 =====
(exit 0)
===== java -cp o24o2:kotlin-stdlib.jar Ordv2Kt =====
A [0:NEW, 1:PENDING, 2:DONE]
B DONE 2 true
C 저장했던 ordinal 1 로 읽으면 = PENDING
(exit 0)
```

**왜 그런가**

```text
   v1  enum class Status { NEW, DONE }            0:NEW  1:DONE
   v2  enum class Status { NEW, PENDING, DONE }   0:NEW  1:PENDING  2:DONE

   ① 직렬화 바이트   "....~r..Status...........xr..java.lang.Enum...........xpt..DONE"
                                                                              ^^^^
                                                            이름이 박혀 있다
      -> v2 에서 읽으면  DONE 2 true       <- 같은 상수를 찾았고 === 도 참이다

   ② ordinal 숫자    1
      -> v2 에서 읽으면  entries[1] = PENDING   <- ★ 조용히 다른 값
```

- ★★★ `ordv2` 의 `C 저장했던 ordinal 1 로 읽으면 = PENDING` 이 이 절의 전부다. **예외도 경고도 없이** 값이 바뀐다.
- `ordv2` 의 `B DONE 2 true` — 역직렬화한 것이 `Status.DONE` 과 **`===` 로 같다.** 역직렬화도 새 객체를 만들지 않는다 — 2번의 싱글턴이 여기까지 온다.
- 버티는 이유는 `ordv1` 의 `B` 에 보인다 — **직렬화 바이트 안에 `DONE` 이라는 이름이 들어 있다.** Java 직렬화는 `enum` 을 **이름으로** 쓰고 읽는다.
- ★★ 규칙 한 줄 — 「**저장·전송에는 `name`, 메모리 안에서만 `ordinal`**」. `ordinal` 은 **선언 순서의 부산물**이지 값이 아니다.
- ★ Java 쪽에서도 같은 결론이 나왔다([`../../../java/syntax/13-enum-classes/`](../../../java/syntax/13-enum-classes/)). **언어가 달라도 같은 함정**이다.
- ★ [22번 주제](../22-data-class-generated-members/)의 `hashCode` 와 **같은 집안**이다 — 둘 다 「프로그램 안에서만 뜻이 있는 숫자」를 경계 밖으로 내보내서 나는 사고다.

### 10. 들 수 있는 데이터가 **상수당 한 벌로 고정**되기 때문이다

**왜 그런가**

```text
   enum class Level(val threshold: Int) { LOW(1), MID(5), HIGH(9) }
                         ^^^^^^^^^^^^^^        ^      ^      ^
                         상수마다 하나씩, 선언할 때 정해지고 안 바뀐다

   Success(1000)  Success(2000)  Success(3000)
           ^^^^           ^^^^           ^^^^
           호출할 때마다 다른 값 — enum 으로는 못 한다
```

- `enum` 도 데이터를 든다(2번의 `hex`, 형태 예제의 `threshold`). 못 하는 것은 「**호출마다 다른 값**」이다.
- 그래서 결제 금액·실패 사유처럼 **실행 중에 정해지는 값**을 붙이려면 `enum` 밖에 별도 클래스를 둬야 하고, 그 클래스는 **모든 상태의 필드를 다 가져야** 하므로 **전부 nullable** 이 된다(3번).
- ★★ **부족함이 드러나는 지표는 `null` 과 `!!` 의 개수**다. 3번의 `describe` 에는 `!!` 가 둘, 4번에는 **0개**다.
- ★ 거꾸로 읽으면 선택 규칙이 나온다 — **「이 타입의 값을 실행 중에 새로 만들어야 하나」**. 그렇다면 `sealed`, 아니면 `enum`.

### 11. 잠금 **넷**, `EnumSet`/`EnumMap` 상실, 명단은 **둘 다 클래스 파일에**(단 조건부)

**왜 그런가**

- [`../../../java/syntax/13-enum-classes/`](../../../java/syntax/13-enum-classes/)가 센 **싱글턴 잠금 넷** — ① `new` 금지와 `private` 생성자(컴파일 에러) ② 리플렉션 차단 ③ `final clone` ④ 역직렬화 차단. 9번의 `B DONE 2 true` 가 ④의 결과다.
- ★★ **`EnumSet`·`EnumMap` 은 `sealed` 로 못 옮긴다.** 둘 다 `ordinal` 을 **비트 위치·배열 인덱스**로 쓰는 자료구조라 `enum` 에만 존재한다. `sealed` 로 옮기면 `Set<Shape>` 이 **해시 기반**으로 떨어지고, 순회 순서 보장도 사라진다.
- **명단을 어디에 적는가** — Java `sealed` 는 **`PermittedSubclasses` 속성**에 적는다([`../../../java/syntax/15-sealed-classes/`](../../../java/syntax/15-sealed-classes/)). Kotlin 도 **같은 속성**을 쓰는데, **`-jvm-target 17` 이상일 때만** 내보낸다([23번 주제](../23-sealed-classes-and-when-exhaustiveness/)에서 실측했다). 기본값(1.8)에서는 **클래스 파일에 명단이 없고** Kotlin 컴파일러만 안다.
- ★ `enum` 쪽은 그런 조건이 없다 — **명단이 곧 `static final` 필드 목록**이라 어느 타깃에서도 클래스 파일에 그대로 있다(2번).

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
| 스택트레이스의 **JDK 내부 프레임 줄 번호**(`Enum.java:293`) — 이 JDK 판의 것 | 예외 **타입·메시지**(`No enum constant Status.PENDING`) |
| `sealedSubclasses` 의 **원소 순서** — **정렬해서 찍어 피했다**(6번) | `Color.entries` 의 **선언 순서** — 계약이다 |
| | `javap` 출력 **전체** · 직렬화 바이트의 **printable 표현** |
| | 컴파일 에러의 **문구·`파일:줄:칸`** · 모든 **종료 코드** |

> ★ `sealedSubclasses` 는 5판을 돌려 원소 순서가 모두 같았다. **그래서 더 위험하다** — 세 판만 보고 「보장된다」로 읽기 쉽다. 근거로 쓴 것은 **집합과 개수**이고 출력은 정렬해 두었다.
>
> 근거 — 캡처 스크립트를 처음부터 다시 돌려 **블록 전체를 바이트 단위로 대조**했고, 이 주제에서 **달라진 파일은 0개**였다.

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `enumdata.kt` | ★★ `values()` 의 **방어 복사** · `entries` 가 **같은 객체**인 것 | `kotlinc` → `java` → `javap -p` |
| `modelenum.kt` | ★★★ **불가능한 상태가 경고 없이 만들어지는 것** · `!!` 가 런타임에 터지는 것 | `kotlinc` → `java` |
| `modelsealed.kt` | ★★ `!!` 가 **0개**인 것 · 같은 변형의 **인스턴스가 여럿**인 것 | `kotlinc` → `java` |
| `modelbad.kt` | ★★ 같은 값을 **sealed 로는 못 만드는 것**(에러 3줄) | `kotlinc` (컴파일 실패가 결과) |
| `enumref.kt` | `entries` 대 `sealedSubclasses` · `isEnum` 이 갈리는 것 | `kotlinc` → `java` (`kotlin-reflect`) |
| `enumwhen.kt` | **`enum` 도 완결성이 요구되는 것** — `sealed` 와 같은 문구 | `kotlinc` (컴파일 실패가 결과) |
| `enumforbid.kt` | `data`·`sealed` 수식어 금지 · 상속 금지 · `equals` 가 `final` 인 것 | `kotlinc` (컴파일 실패가 결과) |
| `enumfail.kt` | ★ `valueOf` 실패 **예외 전문**(마커를 표준 오류로) | `kotlinc` → `java` (**예외로 죽는 것이 결과**) |
| `enumsafe.kt` | 예외를 안 터뜨리는 두 관용구 | `kotlinc` → `java` |
| `ordv1.kt` → `ordv2.kt` | ★★★ **`ordinal` 은 깨지고 `name` 은 버티는 것** · 역직렬화도 싱글턴인 것 | `kotlinc` ×2 → `java` ×2(파일로 주고받음) |
| `form24.kt` | `enum` 의 상수별 데이터와 `sealed` 의 변형별 데이터가 **나란히 도는 것**(`Z`·`Y`) | `kotlinc` → `java` |

**구현 의존 항목** — `$VALUES`·`$ENTRIES` 라는 **필드 이름**, `entries` 의 런타임 타입(`EnumEntriesList`), 직렬화 바이트의 **형식**, `sealedSubclasses` 의 **순서**, 스택트레이스의 **JDK 내부 줄 번호**, 에러·예외 메시지의 **문구** — 전부 이 컴파일러·JDK 판의 산출물이다.\
반면 **「상수가 싱글턴이다」·「`entries` 는 선언 순서다」·「`values()` 는 매번 새 배열이다」·「`valueOf` 실패는 `IllegalArgumentException` 이다」·「둘 다 완결성이 된다」** 는 **언어·javadoc 의 계약**이다.

**★ 못 잰 것** — 「`entries` 는 1.9 부터」는 **이 환경에서 잴 수 없다.** 2.4.20 이 옛 `-language-version` 을 거부하므로 **1.8 판에서 `entries` 가 없다는 것을 직접 못 보인다.**
확인한 것은 「**2.4.20 에서 `entries` 와 `values()` 가 어떻게 다른가**」이고, 「언제부터인가」는 Kotlin 목록([`../README.md`](../README.md))의 판 이력을 인용한 것이다.

**★ 던져 봤더니 예상과 달랐던 것 — 두 건**

1. ★★ **`Color.entries === Color.entries` 가 참이었다.** 「`entries` 도 뷰 객체를 매번 새로 감싸겠지」라고 예상했는데 **`$ENTRIES` 라는 정적 필드를 그대로 돌려준다**(1번·2번). `values()` 와 갈리는 지점이 「복사냐 뷰냐」가 아니라 「**매번 새로 만드느냐 아니냐**」였다.
2. ★★ **`data class Ok1 : Base()` 는 되는데 `data enum class` 는 안 된다.** [22번 주제](../22-data-class-generated-members/)에서 `data class` 가 남을 상속하는 것은 통과했기에 `enum` 에도 `data` 를 얹을 수 있을 줄 알았는데 「`modifier 'data' is not applicable to 'enum class'.`」였다(`enumforbid.kt`). 이유는 같은 파일의 다른 에러가 말해 준다 — **`equals` 가 이미 `final`** 이라 `data` 가 만들 자리가 없다.

**안 터진 것도 출력이다** — 3번의 `PayResult(SUCCESS, reason = "카드 거절")` 은 **경고 한 줄 없이** 컴파일되고 `toString` 까지 멀쩡히 찍힌다.
9번의 `entries[1]` 도 **예외 없이 다른 값**을 돌려준다. 이 주제의 두 핵심 사고가 **둘 다 조용하다**는 것이 결론이고, 그래서 근거를 **컴파일 에러가 아니라 실행 출력**에서 찾아야 했다.
