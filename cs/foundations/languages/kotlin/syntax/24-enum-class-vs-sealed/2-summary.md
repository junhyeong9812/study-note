# kotlin/syntax/24 — `enum class` 와 `sealed` 선택 기준 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Enum classes](https://kotlinlang.org/docs/enum-classes.html) · [Sealed classes and interfaces](https://kotlinlang.org/docs/sealed-classes.html) · [`kotlin.enums.EnumEntries`](https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.enums/-enum-entries/).
> **실행 검증** — 이 문서의 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 에서 실제로 얻었다.\
> `kotlinc` 10회(컴파일 실패 2벌) · `java` 8회(그중 1회는 **예외로 죽는 것이 결과**) · `javap` 1회. 리플렉션 실험에는 `kotlin-reflect.jar` 를 썼다.\
> ★★ 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적지 않았다.
> ⚠️ **`-jvm-target` 을 밝히지 않은 바이트코드 주장은 반쪽이다.** 이 문서의 역어셈블은 **기본값 1.8**(`major version: 52`)이다.
> **버전** — `enum class` 는 **1.0**, **`entries` 는 1.9**, `sealed interface` 는 **1.5** 다.
> **경계** — `sealed` 와 `when` 완결성은 [23번 주제](../23-sealed-classes-and-when-exhaustiveness/)가 정본이고, `when` 의 `enum` 주체가 어떤 바이트코드가 되는지는 [6번 주제](../06-when-expression/)가 정본이다(`$EnumSwitchMapping`).\
> `data class`·`data object` 는 [22번 주제](../22-data-class-generated-members/), `object` 가 싱글턴이 되는 원리는 [25번 주제](../25-object-declaration-companion-and-object-expression/)다.\
> Java 쪽 짝은 [`../../../java/syntax/13-enum-classes/`](../../../java/syntax/13-enum-classes/) — **`values()` 의 방어 복사·`ordinal` 의 위험은 거기가 정본**이고, 여기는 **`sealed` 와 견주어 무엇을 고르나**다.
> 이 본문은 Claude 작성이다(원고 없음).

★ **흔들리는 칸 / 안 흔들리는 칸** — 제출 전 재대조에서 「고칠 것」과 「설계상 다른 것」을 가르는 선언이다.

| 흔들린다 | 안 흔들린다 |
|---|---|
| 스택트레이스의 **JDK 내부 프레임 줄 번호**(`Enum.java:293`) — 이 JDK 판의 것이다 | 예외 **타입과 메시지**(`No enum constant Status.PENDING`) |
| `sealedSubclasses` 의 **원소 순서** — 5판 모두 같았지만 **관찰이지 보장이 아니다** | 첫 프레임 · `javap` 출력 **전체** · 종료 코드 |
| | `Color.entries` 의 순서 — **선언 순서로 보장된다** |
| | 직렬화 바이트에 **`DONE` 이라는 이름이 박히는 것** |

> ★ 그래서 이 문서는 `sealedSubclasses` 를 **정렬해서** 찍는다(`.sorted()`). **근거는 집합이지 순서가 아니다.**\
> 반대로 `entries` 는 정렬하지 않는다 — **선언 순서가 계약**이기 때문이다.
>
> 근거 — 캡처 스크립트를 두 번 돌려 블록 전체를 바이트 단위로 대조했다(수치는 3-answer 의 「실행 검증」).

## 한눈에 — 쉽게 말하면

**둘 다 「명단이 닫힌 타입」이다.** `when` 완결성도 둘 다 된다. 그래서 고르는 기준이 완결성이 **아니다.**

갈림길은 딱 두 개다 — **① 변형마다 다른 데이터를 들고 다니나** · **② 같은 변형의 인스턴스가 여럿 필요한가.** 둘 중 하나라도 「그렇다」면 `enum` 은 답이 아니다.

비유는 문서 끝까지 이것 하나로 고정한다 — **회원증**이다.

| 비유 | 실체 |
|---|---|
| **번호가 찍힌 회원증 세 장**이 벽에 걸려 있다 | `enum` — 상수가 **컴파일 시점에 만들어져 고정**된다 |
| 회원증마다 인쇄된 **고정 문구** | `enum` 생성자 인자 — 상수당 **하나뿐**이고 안 바뀐다 |
| 「3번 회원증 주세요」 | `Color.entries[2]` · `valueOf("BLUE")` — 늘 **같은 장**이 나온다 |
| **빈 양식 세 종류**가 서랍에 있다 | `sealed` — 변형은 **틀**이고 인스턴스는 그때그때 만든다 |
| 양식마다 **다른 칸**이 있다 | 변형마다 다른 프로퍼티 |
| 같은 양식을 **여러 장** 쓴다 | `Success(1000)`·`Success(2000)` — 서로 다른 객체 |
| 두 경우 모두 **접수처가 명단을 점호**한다 | `when` 완결성 — 둘 다 된다 |

```text
   enum class PayState { SUCCESS, FAILURE, PENDING }
      SUCCESS  FAILURE  PENDING        <- 객체가 셋. 영원히 셋이다
         ^        ^        ^
         |        |        |           데이터를 붙이려면?
      data class PayResult(state, amount: Int?, reason: String?)
                                       <- 전부 nullable 이 된다
                                       <- SUCCESS 인데 amount=null 이 컴파일된다

   sealed interface Pay
      +-- Success(amount: Int)         <- 성공에만 금액이 있다
      +-- Failure(reason: String)      <- 실패에만 사유가 있다
      +-- Pending                      <- 데이터 없음(data object)
                                       <- 불가능한 조합이 타입에서 사라진다
```

「**상태에 데이터가 붙는 순간 `enum` 이 부족해진다**」가 이 주제의 한 문장이고, 그 부족함은 **`null` 의 개수**로 드러난다.

## 이 주제가 답하려는 질문

1. `enum` 에 **데이터가 붙는 순간** 정확히 무엇이 부족해지나 — 같은 문제를 둘로 모델링해 보면.
2. **인스턴스**는 각각 몇 개까지 만들 수 있나 — 그것이 왜 갈림길인가.
3. `ordinal`·`name`·`valueOf` 에 기대면 **어디서 깨지나** — 직렬화까지 따라가면.

## 동작 방식

### (1) `enum` 은 상수 집합이 아니라 **진짜 클래스**다 — `javap` 가 답한다

**언제 쓰나** — 「`enum` 은 그냥 상수 묶음」이라고 알고 있을 때.

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

```text
   public final class Color extends java.lang.Enum<Color>   <- 진짜 클래스다
     private final String hex;                              <- 생성자 인자가 필드가 된다
     public static final Color RED;  GREEN;  BLUE;          <- 상수 = static final 필드
     private static final Color[] $VALUES;                  <- 원본 배열(숨어 있다)
     private static final EnumEntries $ENTRIES;             <- entries 용(1.9+)
     private Color(String);                                 <- 생성자가 private
     public static Color[] values();                        <- 부를 때마다 복사본
     public static EnumEntries<Color> getEntries();          <- 늘 같은 객체
     static {};                                             <- 여기서 셋을 만든다
```

- ★★ 상수는 **`<clinit>` 이 딱 한 번 만드는 `public static final` 필드**다. 그래서 **싱글턴이 공짜**다((4)).
- 생성자가 **`private`** 이라 밖에서 `Color("#fff")` 를 만들 수 없다. **명단이 닫히는 방식이 `sealed` 와 다르다** — `sealed` 는 하위 타입을 막고, `enum` 은 **인스턴스 생성 자체를 막는다.**
- `hex` 가 **인스턴스 필드**라는 점을 보라 — `enum` 도 데이터를 들 수 있다. **다만 상수당 하나씩 고정**이다((3)).
- ★ `$VALUES` 와 `$ENTRIES` 가 **따로 있다.** 이 둘의 차이가 (2)다.
- ★ Java 쪽 정본이 [`../../../java/syntax/13-enum-classes/`](../../../java/syntax/13-enum-classes/)다 — **싱글턴을 지키는 잠금 넷**(컴파일 에러·리플렉션 차단·`final clone`·역직렬화 차단)은 거기서 이미 셌다.

### (2) ★★ `values()` 는 **부를 때마다 복사본**, `entries` 는 **늘 같은 객체**(1.9+)

**언제 쓰나** — 반복문에서 `values()` 를 돌릴 때.

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

```text
   Color.values()                      Color.entries        (1.9+)
   -----------------------------       ------------------------------------
   Color[]  (배열)                      EnumEntries<Color>  (List 이다)
   부를 때마다 $VALUES.clone()          $ENTRIES 를 그대로
   -> C: values() === values() = false  -> D: entries === entries = true
   -> 내가 고쳐도 원본은 멀쩡           -> 읽기 전용이라 고칠 수 없다
   -> 호출마다 배열 하나를 할당          -> 할당 없음
```

- `C false` / `D true` — **`values()` 는 매번 다른 배열**이고 `entries` 는 **같은 객체**다.
- `I RED BLUE` — 내가 받은 배열의 0번을 `BLUE` 로 덮었는데 **다음 `values()[0]` 은 그대로 `RED`** 다. **방어 복사**가 그것을 지켰다.
- `G kotlin.enums.EnumEntriesList` — `entries` 의 런타임 타입이다. `List<Color>` 로 쓸 수 있다.
- `H [LColor;` — `values()` 는 **배열**이라 `List` API 가 안 붙는다.
- ★ 그래서 **반복에는 `entries` 가 낫다** — 할당이 없고 `List` 연산이 그대로 붙는다. 다만 **재지 않은 성능 주장은 하지 않는다**(이 문서는 시간을 안 쟀다). 근거는 **`javap` 에 보이는 `clone()` 호출 유무**뿐이다.
- ★ `F 2 BLUE BLUE(#00f)` — `ordinal`·`name` 과 상수별 데이터가 한 줄에 다 보인다. `ordinal` 은 (6)에서 깨뜨린다.

### (3) ★★★ 같은 문제를 둘로 모델링하면 — 부족함이 **`null` 의 개수**로 드러난다

**언제 쓰나** — 「상태 + 그 상태에만 있는 데이터」를 설계할 때. **이 주제의 본체다.**

**① `enum` 으로 모델링한 쪽**

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

**② `sealed` 로 모델링한 쪽**

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

```text
   enum 판                                     sealed 판
   ---------------------------------------     ---------------------------------------
   PayResult(state, amount: Int?,              Success(amount: Int)
                    reason: String?)           Failure(reason: String)
                                               Pending
   상태 3개 × 필드 2개 = 조합 여러 개            변형 3개, 각자 자기 칸만 갖는다
   그중 말이 되는 것은 3개                       말이 안 되는 조합은 타입에 없다

   B PayResult(state=SUCCESS, amount=null,     val impossible = Success(reason = "...")
                reason=카드 거절)                  -> 컴파일 에러 (5번 문항)
     ^^^^^ 컴파일된다. 경고도 없다
   E java.lang.NullPointerException            런타임에 터질 것이 없다
     ^^^^^ !! 가 런타임으로 미뤄 둔 값
```

- ★★★ `enum` 판의 `B` 줄이 전부다 — **`SUCCESS` 인데 `amount` 가 `null` 이고 `reason` 이 차 있는 객체**가 **경고 한 줄 없이 만들어진다.**
- `E java.lang.NullPointerException` — 그 객체를 `describe` 에 넣으면 `!!` 에서 터진다. **설계의 구멍이 런타임 예외로 옮겨져 있었을 뿐**이다.
- `sealed` 판에는 `!!` 가 **한 번도 안 나온다.** `Success` 안에서 `amount` 는 **`Int`**(널 불가)이고, `Failure` 안에서 `reason` 은 **`String`** 이다.
- ★★ **부족해지는 지점을 정확히 말하면** — 「상태마다 **다른 모양의 데이터**가 필요해지는 순간」이다. `enum` 은 상수마다 **같은 필드 집합**만 가질 수 있어서, 차이를 표현하려면 **전부 nullable 로 넓히는 수밖에** 없다.
- ★ **`enum` 도 데이터를 들 수 있다**는 것을 헷갈리지 마라((1)의 `hex`). 들 수 있는 것은 **상수당 고정된 한 벌**이고, **호출마다 달라지는 값**은 못 든다((4)).

### (4) ★★ 인스턴스 수가 갈림길이다 — `enum` 은 **영원히 셋**, `sealed` 는 **몇이든**

**언제 쓰나** — 「값이 세 종류」와 「값이 세 종류의 **모양**」을 구별할 때.

- (3)의 `enum` 판 `C true` — `PayState.SUCCESS === PayState.SUCCESS` 다. **같은 객체 하나**다.
- (3)의 `enum` 판 `D 3` — 인스턴스가 **정확히 3개**이고 프로그램이 도는 내내 그렇다.
- (3)의 `sealed` 판 `D false true` — **`Success(1000) === Success(1000)` 은 거짓**이고 `==` 만 참이다(서로 다른 객체이고 `data class` 라 값이 같다).
- (3)의 `sealed` 판 `E true` — 단 `data object Pending` 은 **싱글턴**이다. **`sealed` 계층 안에서도 데이터 없는 변형은 객체 하나로 둘 수 있다**([22번 주제](../22-data-class-generated-members/)).
- (3)의 `sealed` 판 `F 3 3` — `Success(1000)`·`Success(2000)`·`Success(3000)` 세 개가 `distinct()` 후에도 **셋**이다. **같은 변형의 인스턴스가 여럿**이다.

```text
   enum PayState                        sealed Pay
   --------------------------------     --------------------------------
   SUCCESS  FAILURE  PENDING            Success(1000)  Success(2000)  Success(3000)
   객체 3개, 끝                          Failure("a")  Failure("b")  ...
   === 로 비교해도 된다                  Pending        <- 이것만 객체 하나
                                        객체 수에 제한이 없다
                                        === 로 비교하면 거의 항상 false
```

- ★★★ **갈림길 한 문장** — 「같은 변형을 **서로 다른 값으로 여러 개** 만들어야 하는가」. 그렇다면 `enum` 은 시작부터 답이 아니다.
- ★ 반대로 「값이 딱 정해진 몇 개이고 그게 전부」라면 `enum` 이 낫다 — `valueOf`·`entries`·`EnumSet`·`EnumMap` 이 공짜로 따라온다.

### (5) ★ `when` 완결성은 **둘 다** 된다 — 그래서 고르는 기준이 아니다

**언제 쓰나** — 「완결성 때문에 `sealed` 를 쓴다」고 말하려 할 때.

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

- `enum` 도 가지를 빼면 **똑같이 깨진다** — 「`Add the 'PENDING' branch or an 'else' branch.`」.
- ★ 문구가 [23번 주제](../23-sealed-classes-and-when-exhaustiveness/)의 `sealed` 에서 본 것과 **같은 모양**이다. 완결성 검사는 **주체가 셀 수 있는 타입이면** 동작한다((2) 항목이 아니라 23번 (2)).
- ★★ 그러므로 **「완결성」은 둘을 가르는 기준이 될 수 없다.** 가르는 것은 (3)의 데이터와 (4)의 인스턴스 수다.
- ★ `enum` 쪽이 하나 더 갖는 것 — **상수별 추상 메서드**다. `enum class X { A { override fun f() = ... }, B { ... }; abstract fun f() }` 로 적으면 상수를 늘렸을 때 **`when` 없이도** 컴파일이 깨진다. Java 쪽 정본이 [`../../../java/syntax/13-enum-classes/`](../../../java/syntax/13-enum-classes/)다.

**`enum` 이 추가로 막는 것들**

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

- ★★ **`data enum class` 가 안 되는 이유가 마지막 에러에 있다** — `enum` 의 `equals` 는 **이미 `final`** 이라 `data` 가 만들 자리가 없다.
- `enum` 을 상속하려 하면 에러가 **두 줄**이다 — **`final` 이라서** 하나, **생성자가 `private` 이라서** 하나. (1)의 `javap` 가 그 둘을 다 보여 준다.
- `sealed enum class` 도 막힌다 — `enum` 은 **이미 닫힌 명단**이라 겹치는 선언이다.

### (6) ★★★ `ordinal` 에 기대면 깨지고, `name` 은 버틴다 — 직렬화까지 따라가면 보인다

**언제 쓰나** — `enum` 을 DB 컬럼·프로토콜·파일에 내보낼 때.

**① 상수가 둘인 판에서 저장한다.**

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

**② 가운데에 상수 하나를 끼우고 같은 데이터를 읽는다.**

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

```text
   v1: enum class Status { NEW, DONE }          v2: enum class Status { NEW, PENDING, DONE }
        0:NEW   1:DONE                               0:NEW   1:PENDING   2:DONE

   저장한 것 ①  직렬화 바이트  -> ".....xpt..DONE"   <- 이름이 박힌다
   저장한 것 ②  ordinal 숫자   -> 1

   다시 읽으면 ①  DONE 2 true   <- 같은 상수를 찾아냈고 === 도 참이다
              ②  entries[1] = PENDING  <- ★ 조용히 다른 값이 됐다
```

- ★★★ `②` 가 이 절의 전부다 — **저장할 때 `DONE` 이던 `1` 이 읽을 때 `PENDING`** 이다. **예외도 경고도 없다.** 값이 조용히 바뀐다.
- `①` 의 `B` 줄을 보면 Java 직렬화 바이트 안에 **`DONE` 이라는 이름이 그대로** 들어 있다. 그래서 상수를 끼워도 **이름으로 다시 찾는다.**
- `②` 의 `B DONE 2 true` — 역직렬화한 것이 `Status.DONE` 과 **`===` 로 같다.** 역직렬화도 **새 객체를 만들지 않는다**((4)의 싱글턴이 여기까지 간다).
- ★★ 그래서 규칙 한 줄 — 「**저장·전송에는 `name`, 메모리 안에서만 `ordinal`**」. `ordinal` 은 **선언 순서의 부산물**이지 값이 아니다.
- ★ Java 쪽 정본이 [`../../../java/syntax/13-enum-classes/`](../../../java/syntax/13-enum-classes/)다 — 거기서도 같은 결론이 나왔다(「`ordinal()` 을 저장소·프로토콜에 내보내면 상수 하나가 가운데 끼는 순간 에러 없이 다른 값으로 읽힌다」).
- ★ **`sealed` 에는 `ordinal` 이 아예 없다.** 이 함정 자체가 없는 대신, 직렬화를 쓰려면 **내가 직접** 형식을 정해야 한다.

### (7) ★★ `valueOf` 실패 — 예외 전문과, 그것을 안 쓰는 길

**언제 쓰나** — 바깥에서 들어온 문자열을 `enum` 으로 바꿀 때.

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

- 예외 타입과 메시지가 정확하다 — 「`java.lang.IllegalArgumentException: No enum constant Status.PENDING`」.
- ★ **마커를 `System.err.println` 으로 찍었다.** 스택트레이스도 표준 오류라 **한 블록 안에서 순서가 고정**된다. `println` 으로 찍었다면 파이프로 받을 때 순서가 뒤집혔을 것이다.
- ★ `at java.base/java.lang.Enum.valueOf(Enum.java:293)` 의 **줄 번호는 이 JDK 판의 것**이다(머리말의 흔들리는 칸). **첫 프레임과 메시지가 근거**다.

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

- `A null` — `entries.find { }` 는 **없으면 `null`** 이다. 예외를 안 쓴다.
- `B`·`C` — `runCatching` 으로 감싸면 예외를 **값으로** 받는다(목록의 **49번 주제**).
- ★ stdlib 에는 `enumValueOf<T>()` 의 널 안전판이 **없다.** 그래서 `entries.find` 나 직접 만든 `Map` 이 관용구다.
- ★★ **`sealed` 쪽에는 이 문제 자체가 없다** — 문자열에서 타입을 만들어 주는 기본 장치가 없으므로, 처음부터 **내가 매핑을 쓴다.** 「공짜로 주는 것이 없어서 함정도 없다」는 자리다.

### (8) ★ 명단을 프로그램에서 세기 — `entries` 와 `sealedSubclasses`

**언제 쓰나** — 테스트에서 「모든 변형을 한 번씩 돌린다」를 쓸 때.

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

```text
   Color.entries                     Shape::class.sealedSubclasses
   ------------------------------    -------------------------------------
   kotlin-stdlib 만으로 된다          kotlin-reflect.jar 가 필요하다
   List<Color> — 값이 나온다          List<KClass<out Shape>> — 클래스가 나온다
   선언 순서 보장                     ★ 순서는 보장 없음(5판 같았지만 관찰이다)
   -> 바로 순회해 쓸 수 있다          -> 인스턴스는 내가 만들어야 한다
```

- `A [RED, GREEN, BLUE]` — `entries` 는 **값 목록**이라 그대로 돌릴 수 있다.
- `B [Circle, Empty, Rect]` · `C 3` — `sealedSubclasses` 는 **클래스 목록**이다. `Circle` 을 실제로 만들려면 **생성자 인자를 내가 정해야** 한다.
- `D true false` — `Color::class.java.isEnum` 은 참, `Shape` 는 거짓. **`sealed` 는 JVM 의 enum 이 아니다.**
- `E false true` — `Circle(1.0)` 둘은 **다른 객체**이고 `==` 만 참이다((4)).
- `F true` · `G [true, true, true]` — `data object` 도 `enum` 상수도 **싱글턴**이고, `valueOf` 는 **같은 객체**를 돌려준다.
- ★★ **이 문서는 `B` 를 정렬해서 찍는다.** 5판 모두 순서가 같았지만 그것은 **관찰이지 보장이 아니다** — 근거로 쓸 칸은 **집합과 개수**다(머리말 표).
- ★ 「모든 변형 테스트」가 **`enum` 쪽은 공짜, `sealed` 쪽은 손이 간다** — 이것도 선택 기준의 한 칸이다.

## 문법 — 형태와 규칙

**형태** — `enum` 의 상수별 데이터와 `sealed` 의 변형별 데이터가 나란히 도는 최소 예제다.

```text
===== 소스: form24.kt =====
enum class Level(val threshold: Int) {
    LOW(1), MID(5), HIGH(9);

    fun over(n: Int) = n >= threshold
}

sealed interface Alarm
data class Fire(val floor: Int) : Alarm
data class Flood(val cm: Int) : Alarm
data object Drill : Alarm

fun levelOf(l: Level): String = when (l) {
    Level.LOW -> "낮음"
    Level.MID -> "중간"
    Level.HIGH -> "높음"
}

fun alarmOf(a: Alarm): String = when (a) {
    is Fire -> "${a.floor}층 화재"
    is Flood -> "${a.cm}cm 침수"
    Drill -> "훈련"
}

fun main() {
    println("Z ${Level.entries.map { levelOf(it) }} ${Level.MID.over(7)}")
    println("Y ${listOf(Fire(3), Flood(20), Drill).map { alarmOf(it) }}")
}
===== kotlinc form24.kt -d o24form =====
(exit 0)
===== java -cp o24form:kotlin-stdlib.jar Form24Kt =====
Z [낮음, 중간, 높음] true
Y [3층 화재, 20cm 침수, 훈련]
(exit 0)
```

**규칙 불릿**

- `enum` 상수는 **`<clinit>` 이 한 번 만드는 `static final` 필드**다. 생성자는 **`private`** 이라 밖에서 못 만든다((1)).
- `enum` 도 **생성자 인자로 데이터를 들 수 있다.** 단 **상수당 한 벌 고정**이다((1)·(3)).
- `entries`(**1.9**)는 **같은 객체**를 돌려주고 `values()` 는 **부를 때마다 복사본**이다((2)).
- `enum` 과 `sealed` 는 **완결성이 둘 다 된다**((5)). 고르는 기준이 아니다.
- `enum` 은 인스턴스가 **선언 개수로 고정**, `sealed` 는 **제한이 없다**((4)).
- **`ordinal` 은 선언 순서의 부산물**이다 — 저장·전송에는 `name` 을 쓴다((6)).
- Java 직렬화는 `enum` 을 **이름으로** 쓰고 읽으며, 역직렬화해도 **같은 객체**다((6)).
- `valueOf` 는 실패하면 **`IllegalArgumentException`** 이다. 널 안전판이 stdlib 에 없다((7)).
- `sealedSubclasses` 는 **`kotlin-reflect`** 가 필요하고 **순서 보장이 없다**((8)).

## 어디서 틀리나

1. ★★★ **상태에 데이터가 붙는데 `enum` 을 유지한다.** 필드가 전부 nullable 이 되고 `!!` 가 늘어난다((3)) — **`null` 의 개수가 설계가 틀렸다는 신호**다.
2. ★★★ **`ordinal` 을 DB 컬럼·프로토콜에 내보낸다.** 상수 하나가 가운데 끼면 **조용히 다른 값**이 된다((6)).
3. ★★ **「완결성 때문에 `sealed`」라고 말한다.** `enum` 도 된다((5)).
4. ★★ **`values()` 를 반복문 조건에서 부른다.** 부를 때마다 배열을 하나씩 만든다((2)) — `entries` 를 쓴다.
5. ★★ **`valueOf` 를 바깥 입력에 그대로 쓴다.** `IllegalArgumentException` 이 난다((7)) — `entries.find` 나 `runCatching`.
6. ★ **`sealedSubclasses` 의 순서에 기댄다.** 보장이 없다((8)).
7. ★ **`enum` 상수를 `===` 대신 `equals` 로 비교하려고 애쓴다.** 싱글턴이라 **`==` 로 충분**하고 `when` 에서는 그냥 값을 적으면 된다.
8. ★ **`sealed` 를 골라 놓고 변형마다 데이터가 없다.** 그러면 `enum` 이 더 낫다 — `valueOf`·`entries`·`EnumSet`·`EnumMap` 을 포기한 셈이다.
9. ★ **`enum` 에 `data` 를 붙이려 한다.** `enum` 에는 `data` 수식어를 붙일 수 없다 — `equals`/`hashCode` 가 **이미 `final` 로 정해져** 있기 때문이다([`../../../java/syntax/13-enum-classes/`](../../../java/syntax/13-enum-classes/)).

## 구현 세부사항 대 언어 보장

| 항목 | 어느 쪽인가 | 근거 |
|---|---|---|
| `enum` 상수가 **싱글턴**인 것 | **언어 보장** | (4)·(8) |
| `entries` 가 **선언 순서**인 것 | **언어 보장** | (2) |
| `values()` 가 **매번 새 배열**인 것 | **언어 보장**(javadoc 의 계약) | (2) |
| `valueOf` 실패가 **`IllegalArgumentException`** 인 것 | **언어 보장** | (7) |
| `enum`·`sealed` **둘 다 완결성이 되는 것** | **언어 보장** | (5) |
| `sealed` 변형의 인스턴스 수에 제한이 없는 것 | **언어 보장** | (4) |
| `$VALUES`·`$ENTRIES` 라는 **필드 이름** | **JVM 백엔드의 구현** | (1)의 `javap` |
| `entries` 의 런타임 타입이 `EnumEntriesList` 인 것 | **구현** | (2)의 `G` |
| 직렬화 바이트의 **형식** | **Java 직렬화 프로토콜의 산출물** | (6) |
| `sealedSubclasses` 의 **순서** | **관찰**(5판 동일) — **보장 아님** | (8) |
| 스택트레이스의 **JDK 내부 줄 번호** | **이 JDK 판의 산출물** | (7) |
| 에러·예외 메시지의 **문구 그 자체** | **컴파일러·런타임 판의 산출물** | 전부 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 값이 **정해진 몇 개**이고 데이터가 없거나 상수당 고정이다 | `enum` | `entries`·`valueOf`·`EnumSet`·`EnumMap` 이 공짜 |
| 변형마다 **다른 모양의 데이터** | `sealed` | (3) — `enum` 은 전부 nullable 이 된다 |
| 같은 변형을 **값이 다른 여러 개** 만든다 | `sealed` | (4) |
| 문자열·숫자로 **오가야 한다**(DB·API) | `enum` + **`name`** | (6) — `ordinal` 은 쓰지 마라 |
| **비트 집합·맵 키**로 쓴다 | `enum` | `EnumSet`·`EnumMap` — [`../../../java/syntax/13-enum-classes/`](../../../java/syntax/13-enum-classes/) |
| 데이터 없는 변형 하나가 `sealed` 안에 필요하다 | `data object` | [22번 주제](../22-data-class-generated-members/) |
| **테스트에서 모든 변형을 순회**해야 한다 | `enum` 이 훨씬 싸다 | (8) — `sealed` 는 인스턴스를 내가 만든다 |
| 변형이 **늘어날 예정**이고 각자 데이터가 다르다 | `sealed` | [23번 주제](../23-sealed-classes-and-when-exhaustiveness/) — 늘 때 깨지는 것이 목적이다 |

## 핵심 문장

1. **완결성은 둘 다 된다** — 그래서 고르는 기준이 아니다.
2. 갈림길은 **① 변형마다 다른 데이터** · **② 같은 변형의 인스턴스가 여럿** 둘이다.
3. `enum` 으로 데이터를 표현하면 **필드가 전부 nullable 이 되고 `!!` 가 늘어난다** — 그 개수가 설계의 신호다.
4. `enum` 상수는 **싱글턴**이고 역직렬화해도 같은 객체다. `sealed` 변형은 **인스턴스가 여럿**이다.
5. **`ordinal` 은 순서의 부산물**이다 — 저장·전송에는 `name` 을 쓴다. 직렬화 바이트에 이름이 박혀 있다.
6. `values()` 는 **매번 복사본**, `entries` 는 **같은 객체**다(1.9+).

## 관련 자료

- [6번 주제](../06-when-expression/) — `when` 의 `enum` 주체가 **`$EnumSwitchMapping` 으로 컴파일되는 것**이 거기가 정본이다.
- [22번 주제](../22-data-class-generated-members/) — `data class`·`data object`. **변형을 무엇으로 만드나**가 거기다.
- [23번 주제](../23-sealed-classes-and-when-exhaustiveness/) — `sealed` 와 완결성. **변형을 늘렸을 때 깨지는 자리**가 거기다.
- [25번 주제](../25-object-declaration-companion-and-object-expression/) — `object` 가 **`INSTANCE` 정적 필드**가 되는 원리. `enum` 상수와 같은 집안이다.
- 목록의 **32번 주제** — `==`/`===`. (4)의 `===` 비교가 왜 `enum` 에서만 안전한지는 거기가 정본이다.
- 목록의 **49번 주제** — `Result`·`runCatching`. (7)에서 쓴 것이 거기다.
- [`../../../java/syntax/13-enum-classes/`](../../../java/syntax/13-enum-classes/) — Java `enum`. **싱글턴 잠금 넷·`values()` 복사·`EnumSet`/`EnumMap`·`ordinal` 위험**이 전부 거기가 정본이다.
- [`../../../java/syntax/15-sealed-classes/`](../../../java/syntax/15-sealed-classes/) — Java `sealed`. **명단을 클래스 파일에 남기는 방식**이 거기다.

## 용어 풀이

> **`enum class`** — 상수 집합을 타입으로 만드는 선언. 상수는 컴파일 시점에 정해진 개수의 **싱글턴 객체**다.\
> 예: `enum class Color(val hex: String) { RED("#f00"), ... }`.

> **`entries`** — `enum` 의 모든 상수를 담은 **읽기 전용 `List`**(1.9+). 부를 때마다 **같은 객체**다.\
> 예: `Color.entries.map { it.name }`.

> **`values()`** — 같은 목록을 **배열**로 주는 옛 API. **부를 때마다 복사본**을 만든다.\
> 예: `Color.values()[0] = Color.BLUE` 로 고쳐도 원본은 안 바뀐다.

> **`ordinal`** — 상수의 **선언 순서 번호**(0부터). 선언을 고치면 **값이 바뀐다**.\
> 예: 가운데에 상수를 끼우면 그 뒤가 전부 밀린다.

> **`sealedSubclasses`** — `sealed` 타입의 직접 하위 타입 **클래스 목록**. `kotlin-reflect` 가 필요하다.\
> 예: `Shape::class.sealedSubclasses` — 순서는 보장되지 않는다.

> **불가능한 상태(impossible state)** — 타입은 허용하는데 의미상 말이 안 되는 값의 조합.\
> 예: `PayResult(SUCCESS, amount = null, reason = "카드 거절")`.

## 더 들어가면

- **「상태 기계」를 어느 쪽으로 쓸 것인가**가 이 선택의 실제 얼굴이다. 전이(transition)에 **페이로드가 붙으면** `sealed`, **상태 이름만 오가면** `enum` 이다. 둘을 섞는 관용구도 있다 — `enum` 으로 **상태 이름**을 두고 `sealed` 로 **이벤트**를 두는 식이다.
- **`enum` 이 `sealed` 로 못 하는 것** — `EnumSet`·`EnumMap` 이 대표다. 둘 다 `ordinal` 을 인덱스로 쓰는 자료구조라 **`enum` 에만 존재**한다([`../../../java/syntax/13-enum-classes/`](../../../java/syntax/13-enum-classes/)). 「플래그 여러 개를 켜고 끈다」면 `sealed` 로 옮기는 순간 `Set<Shape>` 이 해시로 떨어진다.
- **`ordinal` 함정의 집안 사람**이 [22번 주제](../22-data-class-generated-members/)의 `hashCode` 다 — 둘 다 **「프로그램 안에서만 뜻이 있는 숫자」를 밖으로 내보내서** 나는 사고다. 경계를 넘는 값은 **이름이나 명시적 코드**로 적는다.
