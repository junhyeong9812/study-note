# kotlin/syntax/26 — `value class`(인라인 클래스) — 언제 박싱되나 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javap`·`javac` 에서 실제로 얻었다.\
> 역어셈블은 **기본 `-jvm-target`(1.8 · `major version: 52`)** 이 정본이다.
> ★★ 아래 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적은 자리가 없다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 둘 다 `long` 을 받고 descriptor 가 같다 — 그래서 한쪽 이름이 `lookup-Bu7z9Ig` 로 뭉개진다

**출력**

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

**왜 그런가**

- ★★★ `lookup(id: UserId)` 는 **`lookup-Bu7z9Ig(long)`**, `lookup(raw: Long)` 은 **`lookup(long)`** 이다. **descriptor 는 둘 다 `(J)Ljava/lang/String;`** 이다.
- 알맹이로 내리면 두 함수가 JVM 에서 **구별이 안 되므로** 컴파일러가 값 클래스를 받는 쪽 이름에 해시를 붙였다. 그래서 Kotlin 에서는 **오버로드 둘이 공존**한다(`A`·`B`).
- ★ `make(n: Long): UserId` 는 **`make(long)`, `(J)J`** — **안 뭉개졌다.** 뭉개기는 값 클래스가 **파라미터에 있을 때** 걸린다(이 판·최상위 함수 기준의 관찰 — 이유는 이 블록이 말하지 않는다).
- `D true UserId(raw=7)` — `==` 는 알맹이 비교, `toString` 은 `data class` 모양이다.

### 2. ★★★ `site0`·`site2` 는 0, 나머지 다섯 자리는 1 — 제네릭 두 자리는 `unbox-impl` 까지

**출력**

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

**왜 그런가**

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

- ★★★ **받는 쪽 서명이 답을 정한다.** `plain-ZF1rqJE(double)` 은 알맹이를 받으니 상자가 필요 없고, `nullable-zjV8Y1s(Meters)`·`viaInterface(Measured)`·`viaAny(Object)`·`viaGeneric(Object)`·`listOf(Object)` 는 **객체**를 받으니 넘기기 직전에 `box-impl` 을 부른다.
- ★★★ **`site1` 과 `site2` 는 다르다.** `Meters?`(알맹이 `Double`)는 **`Meters` 상자**를 받지만, `Name?`(알맹이 `String`)은 **`String` 그대로**(`nullableRef-SnuFtEM(java.lang.String)`)다. `String` 은 원래 `null` 을 담을 수 있기 때문이다.
- ★★ `unbox-impl` 은 **`site5`·`site6`** — 제네릭에서 꺼낼 때 `checkcast Meters` 뒤에 벗긴다.
- ★ 실행 출력 한 줄은 **이 질문에 아무 답도 안 준다** — 값은 상자 유무와 무관하게 같다.

### 3. ★★ 에러 다섯 줄 — `@JvmInline` 없음 · 프로퍼티 둘 · `var` · backing field · `===`

**출력**

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

**왜 그런가**

- 다섯이 전부 **「알맹이 하나로 내린다」** 에서 나온다 — 알맹이가 둘이면(프로퍼티 둘·backing field) 내릴 수 없고, 고칠 수 있으면(`var`) 복사된 값 중 어느 것을 고쳤는지 정의가 안 되고, 정체성이 없으면(`===`) 참조 비교가 뜻이 없다.
- ★ 판에 매인 낱말은 **「`not yet`」** — 「`value classes without '@JvmInline' annotation are not yet supported.`」. **다음 판에서 다시 던질 자리**라는 뜻이다.

### 4. ★ `A`\~`D` 가 찍히고 `Percent(140)` 에서 `IllegalArgumentException` — 첫 프레임은 `Percent.constructor-impl`

**출력**

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

**왜 그런가**

- `A true true 40` — `==` 와 `hashCode` 는 **알맹이 `Int`** 의 것이다(해시 `40`).
- ★★ **`init` 은 정적 `constructor-impl` 안에 들어간다**(트레이스 첫 프레임). 상자를 만들지 않아도 **Kotlin 에서 값을 만들면 검사가 돈다.**
- `E 안 찍힌다` 가 없는 것도 출력이다. 종료 코드는 **1**.

### 5. ★★ `CallIt` 은 「`cannot find symbol`」 — `CallOk` 는 `named#7` 과 **`named#-1`**, `require` 는 **안 돈다**

**출력**

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

**왜 그런가**

- ★★★ `lookup` 의 실제 이름은 **`lookup-Bu7z9Ig`** 라 Java 에서 `lookup(long)` 은 **없다.** `-` 는 Java 식별자에 못 쓰므로 **적을 방법도 없다.**
- ★★★ `@JvmName("lookupRaw")` 는 이름을 풀어 주지만 **Java 는 `long` 을 직접 넘긴다** — `constructor-impl` 을 안 거치므로 **`init` 의 `require(raw > 0)` 가 한 번도 안 돈다.** 그래서 `named#-1` 이 조용히 찍혔다.
- ★ 한 문장으로 — 「**뭉개진 이름은 불편함이 아니라 방어선이었다.** `@JvmName` 은 그 방어선을 Java 쪽에서 연다.」

### 6. 같은 이름·같은 descriptor 의 메서드가 둘이 되어 공존할 수 없다 — 해시는 **파라미터 타입**에서 온다

- 두 `lookup` 이 이름까지 같았다면 **`lookup(J)Ljava/lang/String;` 이 둘** — 한 클래스 파일에 둘 수 없다. 공식 문서도 mangling 의 이유를 「unexpected platform signature clashes」로 든다.
- ★ `Repo.find(id: UserId)` 도 **`find-Bu7z9Ig`** 다(1번 블록) — `lookup` 과 **이름이 다른데 꼬리가 같다.** 해시는 **값 클래스가 들어간 파라미터 목록**에서 온다.

### 7. **알맹이가 원시 타입일 때만** 박싱된다 — `Meters?` 는 `Meters`, `Name?` 은 `String`

- `double` 에는 「없음」을 담을 칸이 없어 **상자(`Meters`)가 `null` 을 대신 담는다.** `String` 은 원래 참조라 **`null` 로 「없음」을 표현**할 수 있다 — 상자가 필요 없다(2번 `site1` 대 `site2`).
- ★ 공식 문서의 예(`asNullable(f) // boxed`)는 **알맹이가 `Int`** 인 경우다. 그 문장을 알맹이 타입과 떼어 외우면 틀린다.

### 8. **박싱 위치**에 — 그래서 언어가 질문 자체를 막았다

- 같은 값이 `site0` 에서는 `double`, `site4` 에서는 **그때 만든 상자**다. 참조 비교를 허용하면 **컴파일러가 어디서 박싱했느냐**에 따라 `true`/`false` 가 갈린다.
- 공식 문서 — 「referential equality is pointless for them and is therefore prohibited」. 3번의 「`identity equality ... is prohibited.`」가 그 결과다.

### 9. **시간과 할당을 안 쟀다** — 유무는 말할 수 있고 비용은 못 말한다

- `box-impl` 호출의 유무로 답하는 것 — 「**컴파일러가 이 자리에서 상자를 요청했는가**」.
- 답하지 못하는 것 — 「실행 중에 **실제로 힙 할당이 일어나는가**」「**얼마나 느린가**」. 그 사이에 JIT 가 있다.
- 재려면 할당 계수·시간을 **판 격자**(JIT 계층·최적화 수준을 바꿔 가며)로 재야 한다(가이드 규칙 24). 한 판의 숫자로 성질을 말하지 않는다.

### 10. `equals`/`hashCode`/`toString` 이 자동인 것은 같다 — `value class` 는 프로퍼티 **하나**·`val` 만·`===` 금지

- `toString` 모양(`Percent(v=40)`)과 값 동등성은 [22번 주제](../22-data-class-generated-members/)의 `data class` 와 같다. `copy`·`componentN` 은 이 문서에서 **안 던졌다.**
- 필드가 **둘**이면 3번의 「`exactly one primary constructor parameter`」 — **`data class`** 로 간다.

### 11. C# 는 제네릭에서 **안** 박싱되고 Rust 는 **개념이 없다** — `typealias` 였다면 두 `lookup` 이 **충돌한다**

- C# 는 제네릭이 값 타입마다 코드를 만들어 `List<int>` 에 박싱이 없다([C# 03번](../../../csharp/syntax/03-boxing-and-unboxing/)이 할당 바이트로 잰 결론). JVM 제네릭은 **`Object` 로 지워지므로** `List<Meters>` 가 박싱 자리다 — **런타임의 제네릭 모델**이 가른다.
- Rust 는 제네릭이 단형화되어 newtype 이 **알맹이와 같은 크기**로 어디든 다닌다([Rust 26번](../../../rust/syntax/26-orphan-rule-and-newtype/)).
- ★★ `typealias UserId = Long` 은 **새 타입이 아니므로** `lookup(UserId)` 와 `lookup(Long)` 은 **같은 함수의 두 선언** — 「`conflicting overloads`」로 막힌다. 그 실측은 [29번 주제](../29-type-aliases-and-nested-type-aliases/)가 싣는다.

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

★ **흔들리는 칸과 안 흔들리는 칸**

| 흔들린다 | 안 흔들린다 |
|---|---|
| **없다** — 기본 `toString`·해시코드를 찍지 않았다 | `javap` 출력 **전체**(뭉개진 이름의 해시 글자까지) · `box-impl` **개수** |
| | 컴파일 에러·`javac` 에러의 **문구와 `파일:줄:칸`** · 예외 트레이스(사용자 프레임뿐) |
| | 모든 **종료 코드** · 출력 |

> 근거 — 캡처 스크립트를 처음부터 다시 돌려 **블록 전체를 바이트 단위로 대조**했다. 결과는 배치 전체 수치로 아래에 적는다.
>
> 실측 — `capture.sh blocks` 와 `capture.sh blocks-recheck` 를 처음부터 따로 돌려 `normalize-shaky.py` 로 대조했다 —\
> **블록 101개 · 동일 101 · 흔들린 칸 0 · ★고칠 것 0**(26\~29 네 주제를 한 캡처로 받았다). `diff -rq` 도 차이 0 이다.\
> ★ **정규화 규칙은 하나도 안 썼다** — 기본 넷(주소·PID·스레드 id·시간)에 걸리는 칸이 애초에 없었다.

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `vcsig.kt` | ★★★ **알맹이를 받는 서명**과 **이름 뭉개기** · 오버로드 공존 | `kotlinc` → `java` → `javap -s -p` · `javap -p` |
| `vcbox.kt` | ★★★ **`box-impl` 이 나타나는 자리**(스크립트가 셈) · nullable 의 조건부 박싱 | `kotlinc` → `java` → `javap -p` · `javap -c -p`(두 필터) |
| `vcbad.kt` | 금지 다섯 가지 | `kotlinc`(컴파일 실패가 결과) |
| `vcinit.kt` | `init` 검사 · 값 동등성 · `constructor-impl` 안의 `init` | `kotlinc` → `java` |
| `vcjava.kt` + `CallIt.java` + `CallOk.java` | ★★★ **Java 에서 안 보이는 이름** · **`@JvmName` 이 `init` 을 건너뛰는 것** | `kotlinc` → `javac`(실패 1벌) → `javap` → `java` |
| `vcexpose.kt` · `vcexpose2.kt` | `@JvmExposeBoxed` 의 **옵트인** · 상자 받는 오버로드 | `kotlinc`(실패 1벌) · `kotlinc` → `javap` |
| `form26.kt` | 형태 한 벌(`Z`·`Y`·`X`) | `kotlinc` → `java` |

**구현 의존 항목** — 파라미터가 **알맹이 타입으로 내려가는 것**, **이름 뭉개기와 해시 글자**, **박싱 네 자리와 nullable 의 조건**, `box-impl`·`unbox-impl`·`constructor-impl`·`equals-impl0` 이라는 이름, `@JvmExposeBoxed` 의 옵트인 상태 — 전부 **JVM 백엔드와 이 판**의 산출물이다.\
반면 **「프로퍼티 하나·`val` 만」「backing field 금지」「`===` 금지」「`init` 허용」「`==` 는 알맹이 비교」** 는 **언어의 계약**이다.

**★ 던져 봤더니 예상과 달랐던 것 — 세 건**

1. ★★★ **nullable 이 늘 박싱되지는 않았다.** 공식 문서의 예(`Foo?` 는 boxed)를 그대로 믿으면 `Name?` 도 상자일 텐데, **알맹이가 `String` 이면 `box-impl` 이 0** 이었다(2번).
2. ★★★ **`@JvmName` 으로 연 길로 들어온 값은 `init` 을 안 거쳤다.** 「이름만 바꾸는 애너테이션」으로 알았는데 **`named#-1`** 이 예외 없이 찍혔다(5번).
3. ★ **반환 타입만 값 클래스인 함수는 이름이 안 뭉개졌다**(`make(long)`). 「값 클래스가 서명에 있으면 뭉개진다」로 외우면 틀린다 — **파라미터에 있을 때**다(1번).
