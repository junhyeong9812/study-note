# kotlin/syntax/26 — `value class`(인라인 클래스) — 언제 박싱되나 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Inline value classes](https://kotlinlang.org/docs/inline-classes.html) · [Java 에서 Kotlin 호출하기 — Inline value classes](https://kotlinlang.org/docs/java-to-kotlin-interop.html#inline-value-classes) · [KEEP — Inline classes](https://github.com/Kotlin/KEEP/blob/master/proposals/inline-classes.md).
> **실행 검증** — 이 문서의 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javac`·`javap` 에서 실제로 얻었다.\
> `kotlinc` 8회(컴파일 실패 2벌) · `javac` 2회(1벌은 실패가 결과) · `java` 5회 · `javap` 7회.\
> ★★ 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적지 않았다. 소스 펜스의 첫 줄 배너도 캡처가 찍었다.
> ⚠️ **`-jvm-target` 을 밝히지 않은 바이트코드 주장은 반쪽이다.** 이 문서의 역어셈블은 전부 **기본값 1.8**(`major version: 52`)이다.
> **버전** — `value class` 는 **Stable 1.5** 다(그 전 판의 `inline class` 가 개명된 것 — 1.4 이하는 `inline class` 로 적고 실험이었다). 이 판에서 버전으로 갈리는 항목은 **`@JvmExposeBoxed`** 하나다 — **2.4.20 에서도 옵트인이 필요하다**((5)).
> **경계** — 「값을 값으로」라는 논지는 [`../../언어-특성/README.md`](../../언어-특성/README.md) §4 가 정본이고, 여기는 **박싱이 사라지는 조건과 다시 살아나는 조건**만 본다.\
> 생성되는 `equals`/`toString` 의 모양은 [22번 주제](../22-data-class-generated-members/)(`data class`)와 같은 집안이다 — 거기서 본 것은 결론만 쓴다.\
> 제네릭이 `Object` 로 지워지는 원리는 [12번 주제](../12-reified-type-parameters/)가 정본이다. 여기서는 **그 소거가 박싱을 부르는 자리**만 센다.\
> `@JvmName` 을 포함한 상호운용 애너테이션 전부는 목록의 **39번 주제**, `==`/`===` 규약은 [목록의 **32번 주제**](../32-equality-and-equals-contract/)다.\
> ★ **29번과 짝이다** — `value class` 는 **새 타입을 만들고** [29번 주제](../29-type-aliases-and-nested-type-aliases/)(`typealias`)는 **안 만든다.**
> **대비** — Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **26번**([`26-orphan-rule-and-newtype/`](../../../rust/syntax/26-orphan-rule-and-newtype/)) — Rust 의 newtype 은 **박싱이라는 개념 자체가 없다**(그쪽 (3)이 `size_of` 로 잰 결론).\
> C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **3번**([`03-boxing-and-unboxing/`](../../../csharp/syntax/03-boxing-and-unboxing/)) — C# `struct` 는 **제네릭에서는 박싱되지 않고** 인터페이스로 올릴 때 박싱된다(그쪽이 할당 바이트로 잰 결론).
> 이 본문은 Claude 작성이다(원고 없음).

★ **본체는 셋째 창이다** — 「`javap -c` 에서 **`box-impl` 호출이 나타나는가**를 자리마다 세는 창」.
언어는 「`value class` 는 값처럼 동작한다」까지만 약속한다. **어디서 상자에 담기는가는 JVM 백엔드가 정하고**, 그것은 바이트코드에만 적혀 있다.

## 이 주제가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **언어 보장** | 명세·공식 문서가 약속한 것 | 「프로퍼티 하나」「`===` 금지」「`init` 허용」 — 전부 **컴파일 에러로도** 확인된다 |
| **구현(JVM 백엔드)** | kotlinc 가 JVM 바이트코드로 내리는 방식 | ★★★ **이름 뭉개기(mangling)·`box-impl`·`constructor-impl`** — `javap` 로만 보인다 |
| **이 판의 관찰** | kotlinc 2.4.20 · JDK 21.0.5 에서 이번에 본 것 | 뭉개진 이름의 **해시 글자**(`-Bu7z9Ig`) · 진단 문구 |

★★★ **mangling 과 박싱 위치는 전부 가운데 층이다.** 「`Meters` 를 받는 함수가 `double` 을 받는다」는 **Kotlin 언어의 사실이 아니라 JVM 백엔드의 사실**이다 — JS·Native 백엔드는 다르게 내릴 수 있다. 이 문서는 JVM 만 잰다.

## 이 판

```text
===== kotlinc -version =====
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
(exit 0)
```

```text
===== javap -version =====
21.0.5
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | (이 주제에는 없다) | 기본 `toString`·해시코드를 **하나도 안 찍었다** — `hashCode()` 는 `Int` 값 그대로라 결정적이다((4)) |
| 안 흔들린다 | ★★★ `javap` 출력 **전체** — 뭉개진 이름의 해시 글자까지 | 같은 소스·같은 판이면 같다. ★ 다만 해시 글자는 **판이 바뀌면 달라질 수 있는** 칸이라 **모양**(`이름-해시`)만 근거로 쓴다 |
| 안 흔들린다 | ★★★ `box-impl`·`unbox-impl` **호출 개수** | 이 주제의 답 자체다 |
| 안 흔들린다 | 컴파일 에러·`javac` 에러의 **문구·`파일:줄:칸`** · 예외 트레이스(사용자 프레임뿐) | 결정적이다 |
| 해당 없음 | 시간·할당 바이트 | ★★★ **안 쟀다.** 「박싱이 없으니 빠르다」는 이 문서가 **주장하지 않는다**(부적용 창 참조) |

★ 근거 — 캡처 스크립트를 처음부터 두 번 돌려 **블록 전체를 바이트 단위로 대조**했다(수치는 3-answer 의 「실행 검증」).

## 한눈에 — 쉽게 말하면

**`value class` 는 「알맹이에 이름표 스티커만 붙이는 것」이다.** 상자를 따로 만들지 않는다.

`UserId` 라는 이름표를 `Long` 에 붙이면 **컴파일러는 이름표를 보고 검사**하지만, 실행할 때는 **`long` 하나만 굴러다닌다.**\
문제는 **규격 상자만 받는 창고**다. 제네릭 컬렉션·`Any`·인터페이스 자리는 **객체(참조)만** 받으므로, 그 문 앞에서는 **진짜 상자(`UserId` 객체)에 담는다** — 그것이 박싱이다.

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 알맹이에 붙인 이름표 스티커 | `@JvmInline value class UserId(val raw: Long)` | (1) |
| 이름표가 달린 물건만 받는 창구 | `fun lookup(id: UserId)` — **JVM 에서는 `long` 을 받는다** | (1) |
| 창구 이름을 살짝 바꿔 달기 | ★★ **이름 뭉개기** — `lookup-Bu7z9Ig(long)` | (1) |
| 규격 상자만 받는 창고 | 제네릭 `T` · `List<UserId>` · `Any` · 인터페이스 | (2) |
| 창고 앞에서 상자에 담기 | ★★★ **`box-impl`** 호출 | (2) |
| 창고에서 꺼내며 상자 벗기기 | **`unbox-impl`** 호출 | (2) |
| 「빈 자리」 표시가 필요한 선반 | `UserId?` — **알맹이가 원시 타입일 때만** 상자가 필요하다 | (2) |
| 이름표를 붙일 때 검사하는 사람 | `init { require(...) }` | (4) |

```text
   소스                                    JVM 에서 실제로 도는 것
   -------------------------------------   ------------------------------------------
   value class Meters(val v: Double)       double  (객체가 없다)
   fun plain(m: Meters)                    plain-ZF1rqJE(double)       <- 상자 없음
   fun nullable(m: Meters?)                nullable-zjV8Y1s(Meters)    <- 상자
   fun viaAny(a: Any)       에 Meters 를    Meters.box-impl(double) 를 부른 뒤 넘긴다
   listOf(Meters(1.0))      에 넣으면       Meters.box-impl(double)  → List 에는 객체
   list[0].v                로 꺼내면       Meters.unbox-impl()      → 다시 double
```

**「value class 는 박싱이 없다」는 반만 맞다.** 정확히는 「**박싱이 필요 없는 자리에서는 안 한다**」다 — 그 자리가 어디인지가 이 주제의 전부다.

## 이 주제가 답하려는 질문

1. `value class` 를 받는 함수는 JVM 에서 **무엇을 받는가** — 그리고 이름은 왜 뭉개지나.
2. 박싱은 **어느 자리에서** 다시 살아나는가 — `box-impl` 을 자리마다 세면 몇인가.
3. 새 타입을 만든 대가로 **무엇이 금지되고**(`===`·프로퍼티 둘·`var`), **Java 에서는 어떻게 보이나**.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| **실행 출력** | 값이 **맞게 흘렀는가** — 박싱 여부와 **무관하게 같다** | 이 갈래의 기본 창 |
| **컴파일 진단** | 금지 사례 다섯 가지((3)) · Java 쪽 `cannot find symbol`((5)) | 이 갈래의 기본 창 |
| ★★★ **`javap -c` 에서 `box-impl` 세기** | 자리마다 **상자에 담았나** — 스크립트가 센다((2)) | ★ **본체 창** |
| ★★ **`javap -s -p` 서명** | 함수가 JVM 에서 **무엇을 받나**(`(J)` · `(D)` · `(LMeters;)`)와 **뭉개진 이름**((1)) | [25번 주제](../25-object-declaration-companion-and-object-expression/)에서 쓰던 창을 서명까지 넓혔다 |
| ★ **Java 에서 던지기** | 뭉개진 이름이 **Java 에서 안 보이는** 것((5)) | [25번 주제](../25-object-declaration-companion-and-object-expression/) (3)에서 쓰던 창 |
| **부적용 — 시간·할당 바이트** | ★★★ **이 문서는 안 쟀다.** 「박싱이 없으니 빠르다」도 「박싱되니 느리다」도 **주장하지 않는다** | — |

★★ **제5의 상태 — 「같은 질문을 다른 창으로 물었다」.**
「여기서 객체가 생기나」는 원래 **할당 계수기**로 물을 질문이다. 이 문서는 그것을 **`box-impl` 호출이 바이트코드에 있나**로 바꿔 물었다.\
★ 바꾼 창의 한계 — **`box-impl` 호출이 있다는 것은 「컴파일러가 상자를 요청했다」까지**다. 실행 중에 JIT 가 그 호출을 어떻게 다루는지는 **이 창이 못 본다.**
그 층을 재려면 규칙 24 대로 **판 격자**(JIT 계층·최적화 수준)를 돌려야 하고, 이 문서는 그것을 **돌리지 않았다.**

### (1) ★★★ 받는 쪽은 **알맹이를 받는다** — 그리고 이름이 뭉개진다

**언제 쓰나** — `value class` 를 파라미터로 받는 함수가 **JVM 에서 무엇이 되나** 물을 때.

```kotlin
// vcsig.kt
@JvmInline
value class UserId(val raw: Long)

fun lookup(id: UserId): String = "user#${id.raw}"
fun lookup(raw: Long): String = "raw#$raw"
fun make(n: Long): UserId = UserId(n)

class Repo {
    fun find(id: UserId): String = "find#${id.raw}"
}

fun main() {
    val id = make(7)
    println("A ${lookup(id)}")
    println("B ${lookup(7L)}")
    println("C ${Repo().find(id)}")
    println("D ${id == UserId(7)} $id")
}
```

```text
===== kotlinc vcsig.kt -d o26s =====
(exit 0)
===== java -cp o26s:kotlin-stdlib.jar VcsigKt =====
A user#7
B raw#7
C find#7
D true UserId(raw=7)
(exit 0)
```

```text
===== javap -s -p o26s/VcsigKt.class o26s/Repo.class =====
Compiled from "vcsig.kt"
public final class VcsigKt {
  public static final java.lang.String lookup-Bu7z9Ig(long);
    descriptor: (J)Ljava/lang/String;

  public static final java.lang.String lookup(long);
    descriptor: (J)Ljava/lang/String;

  public static final long make(long);
    descriptor: (J)J

  public static final void main();
    descriptor: ()V

  public static void main(java.lang.String[]);
    descriptor: ([Ljava/lang/String;)V
}
Compiled from "vcsig.kt"
public final class Repo {
  public Repo();
    descriptor: ()V

  public final java.lang.String find-Bu7z9Ig(long);
    descriptor: (J)Ljava/lang/String;
}
(exit 0)
```

```text
   Kotlin 선언                        JVM 서명                                   descriptor
   --------------------------------   ----------------------------------------   ----------------------
   fun lookup(id: UserId)             lookup-Bu7z9Ig(long)                       (J)Ljava/lang/String;
   fun lookup(raw: Long)              lookup(long)                               (J)Ljava/lang/String;
                                      ^^^^^^^^^^^^^^ 이름만 다르다                ^^^^^^^^^^^^^^^^^^^^^ 똑같다
   fun make(n: Long): UserId          make(long) → long                          (J)J   <- 이름이 안 뭉개졌다
   Repo.find(id: UserId)              find-Bu7z9Ig(long)                         <- 같은 해시 글자
```

- ★★★ **`UserId` 를 받는 함수가 JVM 에서는 `long` 을 받는다**(descriptor `(J)`). 객체가 **아예 안 만들어진다.**
- ★★★ **이름이 뭉개진 이유가 이 블록에 있다** — `lookup(UserId)` 와 `lookup(Long)` 의 descriptor 가 **`(J)Ljava/lang/String;` 으로 똑같다.** 이름까지 같으면 JVM 에서 **같은 메서드 두 개**가 되므로, 컴파일러가 한쪽 이름에 **해시를 붙여 갈랐다.**
- ★★ 그래서 **Kotlin 에서는 두 오버로드가 공존한다**(`A user#7` · `B raw#7`). [29번 주제](../29-type-aliases-and-nested-type-aliases/)(`typealias`)에서는 **같은 모양이 「`conflicting overloads`」로 막힌다** — 새 타입을 만드느냐 안 만드느냐의 차이가 여기서 처음 드러난다.
- ★ **해시 글자는 이름이 아니라 파라미터 타입에서 온다** — `lookup` 과 `Repo.find` 가 **같은 `-Bu7z9Ig`** 를 달았다. 함수 이름이 다른데 꼬리가 같다.
- ★ **반환만 `UserId` 인 `make` 는 안 뭉개졌다**(`make(long)`, `(J)J`). 뭉개기는 **값 클래스가 파라미터에 있을 때** 걸린다 — **이 판·최상위 함수 기준의 관찰**이다. 왜 반환 쪽은 안 가르는지는 이 블록이 **말하지 않는다**(JVM descriptor 자체는 반환 타입까지 포함한다).

**`value class` 자신은 무엇으로 컴파일되나**

```text
===== javap -p o26s/UserId.class =====
Compiled from "vcsig.kt"
public final class UserId {
  private final long raw;
  public final long getRaw();
  public static java.lang.String toString-impl(long);
  public java.lang.String toString();
  public static int hashCode-impl(long);
  public int hashCode();
  public static boolean equals-impl(long, java.lang.Object);
  public boolean equals(java.lang.Object);
  private UserId(long);
  public static long constructor-impl(long);
  public static final UserId box-impl(long);
  public final long unbox-impl();
  public static final boolean equals-impl0(long, long);
}
(exit 0)
```

- ★★ **클래스는 있다** — 필드 `long raw` 하나짜리 `UserId`. 이것이 **상자**다. (2)의 `box-impl` 이 이 객체를 만든다.
- ★★ 멤버가 **두 벌씩** 있다 — `toString()`/`toString-impl(long)`, `hashCode()`/`hashCode-impl(long)`, `equals(Object)`/`equals-impl(long, Object)`.
  `-impl` 이 붙은 **정적** 쪽은 **상자 없이 알맹이로 부르는 길**이고, 인스턴스 쪽은 **상자에 담겼을 때** 부르는 길이다.
- ★ **생성자는 `private`** 이고 밖에서 쓰는 것은 **`constructor-impl(long)` → `long`** 이다 — 「만든다」가 **값을 검사해서 그대로 돌려준다**는 뜻이다((4)의 `init` 이 여기에 들어간다).
- ★ `equals-impl0(long, long)` — **상자 없는 두 값끼리 비교**하는 정적 메서드다. `==` 가 이것으로 내려간다.

### (2) ★★★ 박싱이 다시 살아나는 네 자리 — `box-impl` 을 세면

**언제 쓰나** — 「`value class` 로 바꿨으니 객체가 안 생기겠지」라고 믿을 때. **자리에 따라 다르다.**

자리를 하나씩 함수로 떼어(`site0` \~ `site6`) 바이트코드에서 **`box-impl` 이 몇 번 불리는지** 스크립트가 세게 했다.

```kotlin
// vcbox.kt
@JvmInline
value class Meters(val v: Double)

interface Measured { fun raw(): Double }

@JvmInline
value class Cm(val v: Double) : Measured {
    override fun raw() = v
}

@JvmInline
value class Name(val s: String)

fun plain(m: Meters): Double = m.v
fun nullable(m: Meters?): Double = m?.v ?: -1.0
fun nullableRef(n: Name?): Int = n?.s?.length ?: -1
fun viaInterface(x: Measured): Double = x.raw()
fun viaAny(a: Any): String = a.toString()
fun <T> viaGeneric(t: T): T = t

fun site0() = plain(Meters(1.0))
fun site1() = nullable(Meters(1.0))
fun site2() = nullableRef(Name("ab"))
fun site3() = viaInterface(Cm(1.0))
fun site4() = viaAny(Meters(1.0))
fun site5() = listOf(Meters(1.0))[0].v
fun site6() = viaGeneric(Meters(1.0)).v

fun main() {
    println("${site0()} ${site1()} ${site2()} ${site3()} ${site4()} ${site5()} ${site6()}")
}
```

```text
===== kotlinc vcbox.kt -d o26b =====
(exit 0)
===== java -cp o26b:kotlin-stdlib.jar VcboxKt =====
1.0 1.0 2 1.0 Meters(v=1.0) 1.0 1.0
(exit 0)
```

**받는 쪽 서명부터** — 무엇을 받느냐가 곧 「상자가 필요한가」다.

```text
===== javap -p o26b/VcboxKt.class | grep -v site =====
Compiled from "vcbox.kt"
public final class VcboxKt {
  public static final double plain-ZF1rqJE(double);
  public static final double nullable-zjV8Y1s(Meters);
  public static final int nullableRef-SnuFtEM(java.lang.String);
  public static final double viaInterface(Measured);
  public static final java.lang.String viaAny(java.lang.Object);
  public static final <T> T viaGeneric(T);
  public static final void main();
  public static void main(java.lang.String[]);
}
(exit 0)
```

**그리고 세기** — 사람이 안 센다. 스크립트가 각 `siteN` 본문에서 `box-impl`·`unbox-impl` 호출을 센다.

```text
===== javap -c -p o26b/VcboxKt.class | awk '/ site[0-9]\(\);$/{n=$NF; o[++k]=n; b[n]=0; u[n]=0} n!="" && /\."box-impl"/{b[n]++} n!="" && /"unbox-impl"/{u[n]++} /^$/{n=""} END{for(i=1;i<=k;i++) printf "%-9s box-impl %d  unbox-impl %d\n", o[i], b[o[i]], u[o[i]]}' =====
site0();  box-impl 0  unbox-impl 0
site1();  box-impl 1  unbox-impl 0
site2();  box-impl 0  unbox-impl 0
site3();  box-impl 1  unbox-impl 0
site4();  box-impl 1  unbox-impl 0
site5();  box-impl 1  unbox-impl 1
site6();  box-impl 1  unbox-impl 1
(exit 0)
```

```text
   자리                                  받는 쪽 서명               box-impl   왜
   -----------------------------------   ------------------------   --------   ---------------------------
   site0  plain(m: Meters)               plain-ZF1rqJE(double)          0      알맹이를 그대로 받는다
   site1  nullable(m: Meters?)           nullable-zjV8Y1s(Meters)       1      ★ double 에는 null 칸이 없다
   site2  nullableRef(n: Name?)          nullableRef-...(String)        0      ★★ String 은 원래 null 을 담는다
   site3  viaInterface(x: Measured)      viaInterface(Measured)         1      인터페이스는 객체만 받는다
   site4  viaAny(a: Any)                 viaAny(Object)                 1      Any 는 객체만 받는다
   site5  listOf(Meters(1.0))[0].v       listOf(Object)                 1+un   제네릭 = Object 로 지워진다
   site6  viaGeneric(Meters(1.0)).v      viaGeneric(Object)             1+un   〃
```

- ★★★ **네 자리 모두 `box-impl` 이 나타났다** — nullable(`site1`) · 인터페이스(`site3`) · `Any`(`site4`) · 제네릭(`site5`·`site6`).
- ★ 공식 문서의 문장은 「Inline classes are boxed whenever they are used as another type」이고, 예로 `asNullable(f) // boxed: used as Foo?` 를 든다 — **그 예의 알맹이는 `Int`** 다.
- ★★★ **그런데 nullable 은 조건부다** — **알맹이가 `String` 이면 `Name?` 도 `String` 을 받고 `box-impl` 이 0** 이다(`site2`).
  `double` 에는 「없음」을 담을 칸이 없으니 상자가 필요하지만, `String` 은 **원래 참조라 `null` 을 담을 수 있다** — **상자 없이 `null` 로 「없음」을 표현한다.**
  「nullable 이면 박싱된다」로 외우면 **절반이 틀린다.**
- ★★ **제네릭 두 자리는 `unbox-impl` 까지 나온다** — 넣을 때 담고, **꺼낼 때 `checkcast Meters` → `unbox-impl()`** 로 벗긴다. 왕복이다.
- ★ `site3` 은 **`Cm.box-impl`** 이다 — `value class` 가 인터페이스를 **구현할 수는 있지만**, 인터페이스 타입으로 받는 순간 상자에 담긴다.
- ★ **실행 출력 한 줄(`1.0 1.0 2 1.0 Meters(v=1.0) 1.0 1.0`)은 상자 유무를 전혀 드러내지 않는다** — 첫째 창으로는 이 질문에 답이 안 나오는 이유다.

**상자가 실제로 끼는 모습** — 세기만으로는 「어디에」가 안 보이므로 덤프를 같이 싣는다.

```text
===== javap -c -p o26b/VcboxKt.class | awk '/ site[0-9]\(\);$/,/^$/' =====
  public static final double site0();
    Code:
       0: dconst_1
       1: invokestatic  #64                 // Method Meters."constructor-impl":(D)D
       4: invokestatic  #66                 // Method "plain-ZF1rqJE":(D)D
       7: dreturn

  public static final double site1();
    Code:
       0: dconst_1
       1: invokestatic  #64                 // Method Meters."constructor-impl":(D)D
       4: invokestatic  #71                 // Method Meters."box-impl":(D)LMeters;
       7: invokestatic  #73                 // Method "nullable-zjV8Y1s":(LMeters;)D
      10: dreturn

  public static final int site2();
    Code:
       0: ldc           #76                 // String ab
       2: invokestatic  #81                 // Method Name."constructor-impl":(Ljava/lang/String;)Ljava/lang/String;
       5: invokestatic  #83                 // Method "nullableRef-SnuFtEM":(Ljava/lang/String;)I
       8: ireturn

  public static final double site3();
    Code:
       0: dconst_1
       1: invokestatic  #87                 // Method Cm."constructor-impl":(D)D
       4: invokestatic  #90                 // Method Cm."box-impl":(D)LCm;
       7: invokestatic  #92                 // Method viaInterface:(LMeasured;)D
      10: dreturn

  public static final java.lang.String site4();
    Code:
       0: dconst_1
       1: invokestatic  #64                 // Method Meters."constructor-impl":(D)D
       4: invokestatic  #71                 // Method Meters."box-impl":(D)LMeters;
       7: invokestatic  #95                 // Method viaAny:(Ljava/lang/Object;)Ljava/lang/String;
      10: areturn

  public static final double site5();
    Code:
       0: dconst_1
       1: invokestatic  #64                 // Method Meters."constructor-impl":(D)D
       4: invokestatic  #71                 // Method Meters."box-impl":(D)LMeters;
       7: invokestatic  #102                // Method kotlin/collections/CollectionsKt.listOf:(Ljava/lang/Object;)Ljava/util/List;
      10: iconst_0
      11: invokeinterface #108,  2          // InterfaceMethod java/util/List.get:(I)Ljava/lang/Object;
      16: checkcast     #13                 // class Meters
      19: invokevirtual #17                 // Method Meters."unbox-impl":()D
      22: dreturn

  public static final double site6();
    Code:
       0: dconst_1
       1: invokestatic  #64                 // Method Meters."constructor-impl":(D)D
       4: invokestatic  #71                 // Method Meters."box-impl":(D)LMeters;
       7: invokestatic  #111                // Method viaGeneric:(Ljava/lang/Object;)Ljava/lang/Object;
      10: checkcast     #13                 // class Meters
      13: invokevirtual #17                 // Method Meters."unbox-impl":()D
      16: dreturn
(exit 0)
```

- `site0` — `constructor-impl` → `plain-ZF1rqJE` 로 **`double` 이 바로 건너간다.** 사이에 아무것도 없다.
- `site1` — `constructor-impl` 과 `nullable-zjV8Y1s` **사이에 `Meters."box-impl":(D)LMeters;`** 가 끼었다. **이 한 줄이 박싱이다.**
- `site2` — `Name."constructor-impl":(Ljava/lang/String;)Ljava/lang/String;` → 곧장 `nullableRef-SnuFtEM`. **`String` 이 그대로 건너간다.**
- `site5` — `box-impl` → `listOf` → `List.get` → **`checkcast Meters` → `unbox-impl`**. 컬렉션에 들어간 동안은 **객체**다.

### (3) ★★ 새 타입을 만든 대가 — 금지 사례 전수

**언제 쓰나** — `data class` 처럼 쓰려다 막힐 때. **막히는 이유가 전부 「알맹이 하나로 내려야 한다」에서 나온다.**

```kotlin
// vcbad.kt
value class NoAnno(val v: Int)

@JvmInline
value class Two(val a: Int, val b: Int)

@JvmInline
value class VarProp(var v: Int)

@JvmInline
value class WithField(val v: Int) {
    val twice = v * 2
}

@JvmInline
value class Id(val v: Int)

fun main() {
    val a = Id(1)
    val b = Id(1)
    println(a === b)
}
```

```text
===== kotlinc vcbad.kt -d o26x =====
vcbad.kt:1:1: error: value classes without '@JvmInline' annotation are not yet supported.
value class NoAnno(val v: Int)
^^^^^
vcbad.kt:4:16: error: value class must have exactly one primary constructor parameter.
value class Two(val a: Int, val b: Int)
               ^^^^^^^^^^^^^^^^^^^^^^^^
vcbad.kt:7:21: error: value class primary constructor must only have final read-only ('val') property parameters.
value class VarProp(var v: Int)
                    ^^^^^^^^^^
vcbad.kt:11:5: error: value class cannot have properties with backing fields.
    val twice = v * 2
    ^^^^^^^^^
vcbad.kt:20:13: error: identity equality for arguments of types 'Id' and 'Id' is prohibited.
    println(a === b)
            ^^^^^^^
(exit 1)
```

| 쓴 꼴 | 진단 | 왜 막히나 |
|---|---|---|
| `@JvmInline` 없이 `value class` | 「`value classes without '@JvmInline' annotation are not yet supported.`」 | ★ JVM 에서 **인라인이 아닌 값 클래스는 아직 없다** — 문구가 「**not yet**」이다 |
| 프로퍼티 **둘** | 「`value class must have exactly one primary constructor parameter.`」 | 알맹이 **하나**로 내려야 파라미터를 `long` 하나로 바꿀 수 있다 |
| `var` 프로퍼티 | 「`value class primary constructor must only have final read-only ('val') property parameters.`」 | 값이 **복사되어 다니므로** 고치면 누구의 것을 고친 건지 정의가 안 된다 |
| 본문에 `val twice = v * 2` | 「`value class cannot have properties with backing fields.`」 | 필드를 하나 더 두면 **알맹이가 둘**이 된다 — 계산 프로퍼티(`get()`)만 된다 |
| `a === b` | 「`identity equality for arguments of types 'Id' and 'Id' is prohibited.`」 | ★★★ **정체성이 없다** — 상자는 자리마다 **새로 생겼다 사라지므로** 「같은 객체인가」라는 질문이 성립하지 않는다 |

- ★★★ **`===` 금지가 (2)와 이어진다.** 같은 값이 한 자리에서는 `double`, 다른 자리에서는 **그때 만든 상자**다. 참조 비교를 허용하면 **박싱 위치에 따라 답이 바뀌므로** 언어가 아예 막았다.
- ★ 공식 문서의 문장이 이 칸의 근거다 — 「inline classes may be represented both as the underlying value and as a wrapper, referential equality is pointless for them and is therefore prohibited」.
- ★ 「`not yet supported`」는 **판에 매인 문구**다 — 「아직」이라고 말하므로 **다음 판에서 다시 던질 자리**다.

### (4) ★ 검사는 `init` 에 넣는다 — `equals`·`hashCode` 는 알맹이의 것이다

**언제 쓰나** — `UserId`·`Percent` 처럼 **범위가 있는 값**을 타입으로 만들 때.

```kotlin
// vcinit.kt
@JvmInline
value class Percent(val v: Int) {
    init { require(v in 0..100) { "0..100 밖: $v" } }
    fun half() = Percent(v / 2)
}

fun main() {
    val a = Percent(40)
    val b = Percent(40)
    System.err.println("A ${a == b} ${a.hashCode() == b.hashCode()} ${a.hashCode()}")
    System.err.println("B $a ${a.half()}")
    System.err.println("C ${setOf(a, b).size}")
    System.err.println("D 직전")
    Percent(140)
    System.err.println("E 안 찍힌다")
}
```

```text
===== kotlinc vcinit.kt -d o26i =====
(exit 0)
===== java -cp o26i:kotlin-stdlib.jar VcinitKt =====
A true true 40
B Percent(v=40) Percent(v=20)
C 1
D 직전
Exception in thread "main" java.lang.IllegalArgumentException: 0..100 밖: 140
	at Percent.constructor-impl(vcinit.kt:3)
	at VcinitKt.main(vcinit.kt:14)
	at VcinitKt.main(vcinit.kt)
(exit 1)
```

- ★★ **`init` 이 허용된다** — 그래서 「**만들 수 있으면 유효하다**」를 타입으로 걸 수 있다. `Percent(140)` 이 `IllegalArgumentException` 으로 막혔다.
- ★★ 트레이스의 첫 프레임이 **`Percent.constructor-impl(vcinit.kt:3)`** 이다 — `init` 은 **(1)에서 본 정적 `constructor-impl` 안에** 들어가 있다. 상자를 만들지 않아도 **검사는 돈다.**
- `A true true 40` — `==` 는 **알맹이 비교**이고, `hashCode()` 는 **알맹이 `Int` 의 해시**(`40`)다. `data class` 처럼 **자동으로 생긴다**([22번 주제](../22-data-class-generated-members/)).
- `B Percent(v=40) Percent(v=20)` — `toString` 도 `data class` 모양이다.
- `C 1` — 같은 값 둘을 `Set` 에 넣으면 **하나**다(값 동등성).
- ★ 마커를 **`System.err.println`** 으로 찍었다. 예외 트레이스도 표준 오류라 **한 블록 안에서 순서가 고정**된다(규칙 18).
- ★ **`E 안 찍힌다`** 가 안 찍힌 것도 출력이다 — `Percent(140)` 에서 멈췄다.

### (5) ★★ Java 에서 부르면 — 뭉개진 이름은 **Java 에서 안 보인다**

**언제 쓰나** — `value class` 를 받는 Kotlin API 를 Java 에 낼 때.

```kotlin
// vcjava.kt
@JvmInline
value class UserId(val raw: Long) {
    init { require(raw > 0) { "양수만: $raw" } }
}

fun lookup(id: UserId): String = "user#${id.raw}"

@JvmName("lookupRaw")
fun lookupNamed(id: UserId): String = "named#${id.raw}"
```

```java
// CallIt.java
public class CallIt {
    public static void main(String[] args) {
        System.out.println(VcjavaKt.lookup(7L));
    }
}
```

```text
===== kotlinc vcjava.kt -d o26j =====
(exit 0)
===== javac -cp o26j:kotlin-stdlib.jar -d o26j CallIt.java =====
CallIt.java:3: error: cannot find symbol
        System.out.println(VcjavaKt.lookup(7L));
                                   ^
  symbol:   method lookup(long)
  location: class VcjavaKt
1 error
(exit 1)
```

- ★★★ **Java 는 `lookup(long)` 을 못 찾는다**(「`cannot find symbol`」). 실제 이름이 **`lookup-Bu7z9Ig`** 이고, **`-` 는 Java 식별자에 쓸 수 없는 글자**라 Java 소스로는 **적을 방법조차 없다.**
- ★ 공식 문서가 밝힌 mangling 의 이유는 **서명 충돌 방지**다(「unexpected platform signature clashes … functions using inline classes are mangled by adding some stable hashcode」). Java 에서 못 부르게 되는 것은 **그 결과**다 — 그리고 아래에서 보듯 **그 결과가 방어선 노릇도 한다.**

**`@JvmName` 으로 풀면**

```java
// CallOk.java
public class CallOk {
    public static void main(String[] args) {
        System.out.println(VcjavaKt.lookupRaw(7L));
        System.out.println(VcjavaKt.lookupRaw(-1L));
    }
}
```

```text
===== javap -p o26j/VcjavaKt.class =====
Compiled from "vcjava.kt"
public final class VcjavaKt {
  public static final java.lang.String lookup-Bu7z9Ig(long);
  public static final java.lang.String lookupRaw(long);
}
(exit 0)
===== javac -cp o26j:kotlin-stdlib.jar -d o26j CallOk.java =====
(exit 0)
===== java -cp o26j:kotlin-stdlib.jar CallOk =====
named#7
named#-1
(exit 0)
```

- ★★ **`@JvmName("lookupRaw")` 를 붙인 쪽은 이름이 안 뭉개졌다**(`lookupRaw(long)`). Java 에서 부를 수 있고 `named#7` 이 찍혔다.
- ★★★ **그리고 `named#-1` 도 찍혔다.** `UserId` 의 `init` 은 「양수만」을 요구하는데, **Java 는 `long` 을 직접 넘기므로 `constructor-impl` 을 거치지 않는다** — 검사가 **한 번도 안 돌았다.**
  Kotlin 에서 `UserId(-1)` 이라고 쓰면 (4)처럼 막혔을 값이다. **`@JvmName` 은 이름만 푸는 것이 아니라 타입의 방어선을 Java 쪽에서 통째로 연다.**

**상자째 받는 길 — `@JvmExposeBoxed`(이 판에서 옵트인이 필요하다)**

```kotlin
// vcexpose.kt
@JvmInline
value class UserId(val raw: Long)

@JvmExposeBoxed
fun find(id: UserId): String = "find#${id.raw}"
```

```text
===== kotlinc vcexpose.kt -d o26e =====
vcexpose.kt:4:2: error: this declaration needs opt-in. Its usage must be marked with '@kotlin.ExperimentalStdlibApi' or '@OptIn(kotlin.ExperimentalStdlibApi::class)'
@JvmExposeBoxed
 ^^^^^^^^^^^^^^
(exit 1)
```

```kotlin
// vcexpose2.kt
@JvmInline
value class UserId(val raw: Long)

@OptIn(ExperimentalStdlibApi::class)
@JvmExposeBoxed
fun find(id: UserId): String = "find#${id.raw}"
```

```text
===== kotlinc vcexpose2.kt -d o26e2 =====
(exit 0)
===== javap -p o26e2/Vcexpose2Kt.class =====
Compiled from "vcexpose2.kt"
public final class Vcexpose2Kt {
  public static final java.lang.String find-Bu7z9Ig(long);
  public static final java.lang.String find(UserId);
}
(exit 0)
```

- ★★ **2.4.20 에서도 `@JvmExposeBoxed` 는 실험 API 다** — 「`this declaration needs opt-in.`」. `@OptIn(ExperimentalStdlibApi::class)` 를 붙이자 통과했다.
- ★★ 붙이면 **메서드가 둘**이 된다 — 뭉개진 `find-Bu7z9Ig(long)` 과 **상자를 받는 `find(UserId)`**. Java 쪽 서명에 **`UserId` 라는 타입이 남는다** — `@JvmName` 이 `long` 으로 타입을 지운 것과 반대 방향이다.
  ★ 공식 문서는 이 애너테이션을 **값 클래스 선언에** 붙이면 **Java 에서 부를 수 있는 공개 생성자**가 생긴다고 적는다(「generates a public constructor that you can call from Java directly」). 이 문서는 **함수에만** 붙여 던졌다 — 위 블록은 함수 쪽 서명만 보였고, 생성자는 **안 던졌다.**
- ★ 이 애너테이션의 판 경계는 **다음 판에서 다시 던질 자리**다. 상호운용 애너테이션 전부는 목록의 **39번 주제**가 정본이다.

## 문법 — 형태와 규칙

**형태** — `init` 검사·계산 프로퍼티·값 동등성·컬렉션 안의 값이 한 프로그램에서 전부 도는 최소 예제다.

```kotlin
// form26.kt
@JvmInline
value class Email(val raw: String) {
    init { require('@' in raw) { "이메일 아님: $raw" } }
    val domain: String get() = raw.substringAfter('@')
}

fun send(to: Email): String = "send -> ${to.domain}"

fun main() {
    val e = Email("kim@example.com")
    println("Z ${send(e)}")
    println("Y ${e == Email("kim@example.com")} $e")
    println("X ${listOf(e, Email("lee@test.org")).map { it.domain }}")
}
```

```text
===== kotlinc form26.kt -d o26f =====
(exit 0)
===== java -cp o26f:kotlin-stdlib.jar Form26Kt =====
Z send -> example.com
Y true Email(raw=kim@example.com)
X [example.com, test.org]
(exit 0)
```

**규칙 불릿**

- 선언은 **`@JvmInline value class 이름(val 프로퍼티: 타입)`** — JVM 에서는 `@JvmInline` 이 **필수**다((3)).
- 주 생성자 프로퍼티는 **정확히 하나**, **`val`** 이어야 한다((3)).
- 본문에 **`init` 블록·함수·계산 프로퍼티**(`get()`)를 둘 수 있다. **backing field 가 있는 프로퍼티는 못 둔다**((3)).
- 인터페이스를 **구현할 수 있다** — 다만 그 인터페이스 타입으로 받는 순간 **박싱**된다((2)의 `site3`).
- `equals`·`hashCode`·`toString` 은 **알맹이 기준으로 자동**이다((4)). **`===` 는 금지**다((3)).
- 파라미터로 받으면 **JVM 서명에서 알맹이 타입**이 되고 **이름이 뭉개진다**((1)). **Java 에 낼 거면 `@JvmName`**((5)).
- 박싱 자리 — **nullable(알맹이가 원시일 때) · 인터페이스 · `Any` · 제네릭**((2)).

## 어디서 틀리나

1. ★★★ **「`value class` 는 박싱이 없다」고 믿는다.** **네 자리에서 `box-impl` 이 나온다**((2)) — `List<Meters>` 에 담는 순간 객체다.
2. ★★★ **「nullable 이면 무조건 박싱」이라고 외운다.** **알맹이가 참조 타입이면 안 박싱된다**((2)의 `site2`) — 틀린 방향이 반대일 뿐 같은 실수다.
3. ★★★ **박싱 여부를 실행 결과로 판단하려 한다.** 출력은 **같다**((2)). **`javap -c` 에서 `box-impl` 을 봐야** 보인다.
4. ★★ **`box-impl` 이 보이니 느리다, 안 보이니 빠르다고 결론낸다.** **이 문서는 시간을 안 쟀다**((0)). 호출이 있다는 것과 **그 호출이 실행 중에 무엇을 치르나**는 다른 질문이다.
5. ★★ **`value class` 로 `===` 를 쓰려 한다.** 「`identity equality ... is prohibited.`」((3)).
6. ★★ **Java 에서 `lookup(7L)` 을 부르려 한다.** 이름이 **`lookup-Bu7z9Ig`** 라 「`cannot find symbol`」((5)). `@JvmName` 으로 풀면 **`init` 검사까지 사라진다**(`named#-1`).
7. ★ **프로퍼티를 둘 두려 한다.** 「`exactly one primary constructor parameter`」 — 둘이면 `data class` 로 간다([22번 주제](../22-data-class-generated-members/)).
8. ★ **`@JvmInline` 을 빠뜨린다.** 「`not yet supported`」((3)).

## 구현 세부사항 대 언어 보장

| 항목 | 어느 쪽인가 | 근거 |
|---|---|---|
| 프로퍼티 **하나**·`val` 만 | **언어 보장** | (3) |
| **`===` 금지** | **언어 보장** | (3) |
| `init` 허용 · `equals`/`hashCode`/`toString` 자동 | **언어 보장** | (4) |
| `==` 가 **알맹이 비교** | **언어 보장** | (4) |
| JVM 에서 **`@JvmInline` 필수** | **JVM 백엔드의 제약**(문구가 「not yet」) | (3) |
| 파라미터가 **알맹이 타입으로 내려가는 것** | ★★★ **JVM 백엔드의 구현** | (1) |
| **이름 뭉개기** · 해시 글자 `-Bu7z9Ig` | **JVM 백엔드의 구현** · 해시 글자는 **이 판의 관찰** | (1) |
| **박싱이 일어나는 네 자리** | ★★★ **JVM 백엔드의 구현**(소거·원시 타입이라는 JVM 의 성질에서 온다) | (2) |
| 알맹이가 참조면 **nullable 이 안 박싱되는 것** | **JVM 백엔드의 구현** | (2)의 `site2` |
| `box-impl`·`unbox-impl`·`constructor-impl`·`equals-impl0` 이라는 **이름** | **JVM 백엔드의 구현** | (1) |
| `@JvmExposeBoxed` 가 **옵트인** | **이 판(2.4.20)의 상태** | (5) |
| 진단 **문구 그 자체** | **컴파일러 판의 산출물** | 전부 |

★★ **언어가 약속하는 것은 「값처럼 동작한다」까지**다. 「`double` 로 내려간다」「여기서 상자에 담긴다」는 **JVM 이라는 과녁이 원시 타입과 소거를 가졌기 때문에 생긴 구현**이다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| `Long`·`String` 을 **의미가 다른 여러 ID** 로 쓴다 | `value class` | 섞어 넣으면 **컴파일 에러**다([29번 주제](../29-type-aliases-and-nested-type-aliases/)와 대비) |
| 범위·형식 검사가 붙은 값(`Percent`·`Email`) | `value class` + `init` | 만들 수 있으면 유효하다((4)) |
| 필드가 **둘 이상** | `data class` | (3) — 값 클래스는 하나뿐이다 |
| 주로 **컬렉션·제네릭** 안에서 다닌다 | 둘 다 된다 — 다만 **거기서는 객체**다 | (2) — 「상자가 없다」는 이득을 기대하지 마라 |
| **Java 에서 많이 부를** API | 서명에 `value class` 를 **드러내지 않거나** `@JvmName` | (5) — 뭉개진 이름은 Java 에서 안 보인다 |
| 이름만 붙이고 **검사는 필요 없다** | `typealias` | [29번 주제](../29-type-aliases-and-nested-type-aliases/) — 새 타입이 **아니다** |

## 핵심 문장

1. `value class` 를 받는 함수는 JVM 에서 **알맹이를 받는다** — `UserId` 가 `long` 이 된다.
2. 그래서 **같은 descriptor 의 오버로드가 생기고**, 컴파일러가 **이름을 뭉개서**(`lookup-Bu7z9Ig`) 가른다.
3. 박싱은 **nullable(원시 알맹이) · 인터페이스 · `Any` · 제네릭** 네 자리에서 살아난다 — `box-impl` 호출로 센다.
4. **알맹이가 참조 타입이면 nullable 도 안 박싱된다** — 「nullable 이면 박싱」은 반만 맞다.
5. **정체성이 없으므로 `===` 가 금지**다. `==`·`hashCode` 는 **알맹이의 것**이다.
6. 뭉개진 이름은 **Java 에서 안 보인다** — `@JvmName` 으로 풀면 Java 는 `long` 을 넘기고 **`init` 검사가 한 번도 안 돈다.**

## 관련 자료

- [22번 주제](../22-data-class-generated-members/) — `data class`. **생성되는 `equals`/`toString` 의 모양**이 거기다. 필드가 둘 이상이면 그쪽이다.
- [12번 주제](../12-reified-type-parameters/) — 소거. **제네릭이 `Object` 로 지워지는 원리**가 거기이고, 여기는 **그 소거가 박싱을 부르는 자리**만 센다.
- [25번 주제](../25-object-declaration-companion-and-object-expression/) — Java 에서 Kotlin 을 부르는 창. `@JvmStatic` 이 거기다.
- [29번 주제](../29-type-aliases-and-nested-type-aliases/) — `typealias`. ★ **짝이다** — 이쪽은 새 타입을 만들어 **섞으면 막히고**, 그쪽은 **안 막힌다.**
- [목록의 **32번 주제**](../32-equality-and-equals-contract/) — `==`/`===` 규약. 여기는 **`===` 가 왜 금지인가**까지다.
- 목록의 **39번 주제** — `@JvmName`·`@JvmStatic` 등 상호운용 애너테이션 전부.
- [`../../언어-특성/README.md`](../../언어-특성/README.md) §4 — 「값을 값으로」라는 **설계 논지**와 실측. 여기는 **박싱이 살아나는 구체 조건**이다.
- [`../../../rust/syntax/26-orphan-rule-and-newtype/`](../../../rust/syntax/26-orphan-rule-and-newtype/) — Rust newtype. **박싱이 없는 언어**의 같은 관용구.
- [`../../../csharp/syntax/03-boxing-and-unboxing/`](../../../csharp/syntax/03-boxing-and-unboxing/) — C# 박싱. **제네릭이 박싱을 없애는 쪽**이라 Kotlin 과 정반대 자리다.
- [`../../../java/syntax/01-primitives-and-wrappers/`](../../../java/syntax/01-primitives-and-wrappers/) — Java 의 원시 타입과 래퍼. `box-impl` 이 하는 일이 `Integer.valueOf` 와 같은 모양이다.

## 용어 풀이

> **`value class`(값 클래스)** — 프로퍼티 **하나**를 감싸 **새 타입**을 만들되, 가능한 자리에서는 **감싸지 않은 알맹이로** 다니게 하는 클래스.\
> 예: `@JvmInline value class UserId(val raw: Long)`.

> **알맹이(underlying type)** — 값 클래스가 감싼 프로퍼티의 타입. JVM 에서 실제로 굴러다니는 것.\
> 예: `UserId` 의 알맹이는 `Long`(JVM 에서 `long`).

> **박싱(boxing)** — 알맹이를 **객체(상자)** 에 담는 것. 값 클래스에서는 **`box-impl`** 정적 메서드 호출로 보인다.\
> 예: `Meters."box-impl":(D)LMeters;`.

> **이름 뭉개기(mangling)** — 값 클래스를 받는 함수의 JVM 이름에 **해시를 붙이는 것**. 같은 descriptor 의 오버로드를 가르려고 한다.\
> 예: `lookup(id: UserId)` → `lookup-Bu7z9Ig(long)`.

> **descriptor** — JVM 이 메서드를 가르는 **파라미터·반환 타입의 표기**. `javap -s` 로 보인다.\
> 예: `(J)Ljava/lang/String;` — `long` 을 받아 `String` 을 돌려준다.

> **`@JvmInline`** — JVM 에서 값 클래스를 **인라인(알맹이로 내려 보내기)** 방식으로 컴파일하라는 표시. 이 판에서는 필수다.

> **`@JvmName`** — JVM 에 보일 **이름을 직접 정하는** 애너테이션. 뭉개진 이름을 Java 에서 부를 수 있게 한다.

> **정체성(identity)** — 「같은 객체인가」를 묻는 성질. `===` 가 묻는 것. 값 클래스에는 **없다.**

## 더 들어가면

- **왜 해시를 붙였나** — (1)의 descriptor 가 답이다. 알맹이로 내리는 순간 `f(UserId)` 와 `f(Long)` 이 **JVM 에서 구별이 안 된다.** 이름을 안 바꾸면 두 메서드가 한 클래스 파일에 공존할 수 없다. 부수 효과로 Java 에서 못 부르게 되는데, (5)의 `named#-1` 이 보여 주듯 **그 부수 효과가 `init` 을 건너뛴 값이 들어오는 길을 막고 있었다.**
- **C# `struct` 와 정반대 자리** — C# 는 제네릭이 **값 타입마다 코드를 따로 만들어** `List<int>` 에 박싱이 없다([C# 03번](../../../csharp/syntax/03-boxing-and-unboxing/)이 잰 결론). Kotlin(JVM)은 제네릭이 **`Object` 로 지워지므로** `List<Meters>` 가 **바로 박싱 자리**다((2)의 `site5`). **같은 「값 타입」이 제네릭에서 반대로 간다** — 차이는 언어가 아니라 **런타임의 제네릭 모델**에서 온다.
- **Rust newtype 은 이 질문 자체가 없다** — 제네릭이 **단형화**(타입마다 코드 생성)되므로 `Vec<Meters>` 도 `f64` 를 그대로 담는다([Rust 26번](../../../rust/syntax/26-orphan-rule-and-newtype/)이 `size_of` 로 같은 크기임을 쟀다). Kotlin 의 `value class` 는 **JVM 위에서 newtype 을 흉내 낸 것**이라 **흉내가 벗겨지는 자리**가 생긴다 — 그것이 (2)의 네 자리다.
