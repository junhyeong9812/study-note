# kotlin/syntax/01 — `val`/`var` 와 기본 타입: 암묵 수치 변환이 없다 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Basic types](https://kotlinlang.org/docs/basic-types.html) · [Numbers](https://kotlinlang.org/docs/numbers.html) · [Properties](https://kotlinlang.org/docs/properties.html) · [Unsigned integer types](https://kotlinlang.org/docs/unsigned-integer-types.html).
> **실행 검증** — 이 문서의 모든 출력·에러·경고·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 에서 실제로 돌려 얻었다.\
> 바이트코드는 Temurin **JDK 21.0.5** 의 `javap` 출력이다. 버전 확인 명령은 「실행 검증」 절에 있다.
> **버전** — `val`/`var` 와 여덟 기본 타입은 1.0 부터. **`UInt` 등 부호 없는 정수는 1.5 Stable.**\
> 컴파일러는 **K2**(2.0 이후 기본)다 — 이 문서의 에러 문구는 K2 프런트엔드가 낸 것이다.
> **경계** — [`../../언어-특성/README.md`](../../언어-특성/README.md) §5 는 **「왜 가변성을 이름에 적는 언어를 고르나」** 를 답한다(읽기 전용 컬렉션 실측표가 거기 정본).\
> 여기는 **「이 문법이 JVM 위에서 무엇으로 내려앉나」** 만 다룬다 — `val` 이 만드는 필드, `Int` 와 `Int?` 의 디스크립터.\
> **박싱 캐시(`-128\~127`)의 정본은 [`../../../java/syntax/01-primitives-and-wrappers/`](../../../java/syntax/01-primitives-and-wrappers/)** 다. 여기서는 **결론만 받아 쓰고 재서술하지 않는다.**
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**`val` 은 「이 이름표를 다른 상자에 다시 못 붙인다」는 뜻이지 「상자 안이 안 바뀐다」는 뜻이 아니다.**\
**그리고 Kotlin 의 수 타입은 「서로 다른 규격의 상자」라 내용물을 말없이 옮겨 담아 주지 않는다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 이름표 | 변수 이름 |
| 이름표를 다른 상자에 다시 붙이기 | 재대입 (`x = ...`) |
| 상자 안의 물건을 바꾸기 | 객체 내부 변경 (`list.add(3)`) |
| 이름표에 박힌 대못 | `val` |
| 규격이 다른 상자들 | `Byte`·`Short`·`Int`·`Long`·`Float`·`Double` |
| 작은 상자 내용물을 큰 상자에 옮기려면 사람이 직접 | `i.toLong()` |
| 물류센터가 알아서 옮겨 주는 나라 | Java 의 확대 변환 |
| 주문서에 규격이 적혀 있으면 그 규격으로 포장해 준다 | 리터럴은 기대 타입을 따라간다 |

```text
  val list = mutableListOf(1, 2)          var list = mutableListOf(1, 2)

   list ──대못──> [ 1, 2 ]                 list ─────> [ 1, 2 ]
        list.add(3)  OK                         list = mutableListOf(9)  OK
   list ──대못──> [ 1, 2, 3 ]              list ─────> [ 9 ]
        list = ...   컴파일 에러
```

**똑같은 구조로** Kotlin 이 동작한다: 대못 = `val`, 이름표 = 변수, 상자 = 힙의 객체.

실무에서 이게 터지는 자리는 **"`val` 로 선언했으니 불변이다"** 라고 믿고\
`val` 컬렉션을 그대로 밖에 내주는 코드다. 밖에서 `add` 가 통한다.

> **재대입(reassignment)** — 이미 있는 변수 이름에 다른 값을 다시 넣는 것.\
> 예: `x = 2` 는 재대입이고, `list.add(3)` 은 재대입이 아니라 객체 내부 변경이다.

> **확대 변환(widening conversion)** — 작은 수 타입을 큰 수 타입에 정보 손실 없이 자동으로 옮겨 담는 것.\
> 예: Java 는 `long l = anInt;` 가 통한다. **Kotlin 은 이것을 거부한다.**

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. `val` 은 **정확히 무엇을 막고 무엇을 못 막는가** — 그리고 바이트코드에 무엇을 남기는가.
2. Kotlin 은 **왜 `Int` 를 `Long` 에 그냥 못 넣게 하는가** — 그런데 왜 `val l: Long = 1` 은 되는가.
3. `Int` 와 `Int?` 는 **같은 타입의 두 표기인가, 다른 타입인가** — 무엇으로 확인하는가.

## 동작 방식

### (1) `val` 이 고정하는 것 — 이름표지 내용물이 아니다

**언제 쓰나** — "`val` 을 썼는데 왜 값이 바뀌었나" 를 겪을 때.

```kotlin
val list = mutableListOf(1, 2)
list.add(3)
```

**출력** (`ex.kt`, kotlinc 2.4.20)

```text
--- 1. val 은 재대입만 막는다 ---
val list 에 add -> [1, 2, 3]
```

그리고 재대입만 골라서 막는다.

```text
bad2.kt:3:5: error: 'val' cannot be reassigned.
    x = 2
    ^
```

그림 해설 (한 단계씩):

- `val` 은 **참조를 고정**한다. 참조가 가리키는 객체 안은 그 객체의 규칙이 정한다.
- 그래서 `val` + 가변 컬렉션 = **아무것도 안 잠긴 상태**다. 잠그려면 타입 쪽에서 `List` 를 쓴다.
- **읽기 전용 타입조차 「뷰」라서 완전한 잠금이 아니다** — 그 실측표는 [`../../언어-특성/README.md`](../../언어-특성/README.md) §5 가 정본이다.

비용 — 없다. 컴파일러 검사일 뿐이다((2)).

### (2) ★ `val` 이 바이트코드에 남기는 것 — 프로퍼티는 남고 지역 변수는 안 남는다

**언제 쓰나** — "`val` 이 런타임 보장인가 컴파일 검사인가" 를 가를 때.

```kotlin
class P(val a: Int, var b: Int) {
    val c: String = "고정"
    var d: String = "가변"
}
```

**출력** (`javap -p -s outvv/P.class`)

```text
public final class P {
  private final int a;
  private int b;
  private final java.lang.String c;
  private java.lang.String d;
  public P(int, int);
  public final int getA();
  public final int getB();
  public final void setB(int);
  public final java.lang.String getC();
  public final java.lang.String getD();
  public final void setD(java.lang.String);
}
```

- **`val` 프로퍼티 → `private final` 필드 + 게터만.** 세터가 아예 안 생긴다.
- **`var` 프로퍼티 → `private` 필드 + 게터 + 세터.** `final` 이 빠진다.
- 즉 프로퍼티의 `val` 은 **JVM 의 `final` 로 실제로 내려간다** — Java 쪽에서도 못 고친다.

지역 변수는 다르다.

```kotlin
fun withVal(): Int { val x = 1; return x + 1 }
fun withVar(): Int { var x = 1; x = 2; return x + 1 }
```

**출력** (`javap -c -p outloc/LocKt.class`)

```text
  public static final int withVal();
       0: iconst_1
       1: istore_0
       2: iload_0
       3: iconst_1
       4: iadd
       5: ireturn

  public static final int withVar();
       0: iconst_1
       1: istore_0
       2: iconst_2
       3: istore_0
       4: iload_0
       5: iconst_1
       6: iadd
       7: ireturn
```

- 둘 다 `istore_0` 이다. **지역 `val` 은 바이트코드에 흔적이 없다** — 순수한 프런트엔드 검사다.
- 그래서 **지역 `val` 의 보장은 「이 함수 소스 안에서」** 끝난다. 프로퍼티의 `val` 과 세기가 다르다.

비용 — 0. 지역 `val` 은 코드 크기도 실행 시간도 안 바꾼다.

### (3) ★★ 암묵 수치 변환이 없다 — 던져서 받은 에러

**언제 쓰나** — Java 에서 넘어와 `long l = anInt;` 를 그대로 썼을 때.

```kotlin
val i: Int = 1
val l: Long = i
val d: Double = i
val b: Byte = 1
val i2: Int = b
val c: Char = 'a'
val n: Int = c
```

**출력** (`kotlinc bad.kt`)

```text
bad.kt:3:17: error: initializer type mismatch: expected 'Long', actual 'Int'.
    val l: Long = i
                ^
bad.kt:4:19: error: initializer type mismatch: expected 'Double', actual 'Int'.
    val d: Double = i
                  ^
bad.kt:6:17: error: initializer type mismatch: expected 'Int', actual 'Byte'.
    val i2: Int = b
                ^
bad.kt:8:16: error: initializer type mismatch: expected 'Int', actual 'Char'.
    val n: Int = c
               ^
```

그림 해설:

```text
  Java                                    Kotlin
  +--------------------------+            +--------------------------+
  | int i = 1;               |            | val i: Int = 1           |
  | long l = i;   OK (자동)   |            | val l: Long = i   ERROR  |
  | double d = i; OK (자동)   |            | val d: Double = i ERROR  |
  | int n = 'a'; OK (97)      |            | val n: Int = 'a'  ERROR  |
  +--------------------------+            +--------------------------+
        확대는 말없이 통과                       전부 명시 변환을 요구
```

- 넓히는 방향(`Int` → `Long`)조차 거부한다. **손실이 없어도 거부한다**는 점이 요점이다.
- 이유는 손실이 아니라 **타입 추론과의 충돌**이다 — 암묵 확대가 있으면 `val x = 1` 의 타입을 컴파일러가 혼자 못 정한다.
- 대신 **명시 변환 함수**가 전부 있다: `toByte()`·`toShort()`·`toInt()`·`toLong()`·`toFloat()`·`toDouble()`·`toChar()`.

**출력** (`ex.kt`)

```text
--- 3. 명시 변환 ---
i.toLong() = 1  i.toDouble() = 1.0  i.toByte() = 1
300.toByte() = 44
1.9.toInt() = 1   (-1.9).toInt() = -1
```

- `300.toByte()` 가 `44` 다 — **좁히는 변환은 조용히 자른다.** 거부하는 것은 대입뿐이고 변환 함수는 안 막아 준다.
- `toInt()` 는 **0 쪽으로 버린다**(`-1.9` → `-1`). 반올림이 아니다.

비용 — 없다. `toLong()` 은 `i2l` 한 명령으로 내려간다.

### (4) ★ 그런데 리터럴은 예외다 — 비대칭이 있다

**언제 쓰나** — "(3)이 맞다면 `val l: Long = 1` 도 에러여야 하지 않나" 라고 물을 때.

```kotlin
val b: Byte = 1      // 통과
val big: Byte = 200  // 에러
val l2: Long = 1     // 통과
val f: Float = 1.0   // 에러
val d2: Double = 1f  // 에러
```

**출력** (`kotlinc bad2.kt`)

```text
bad2.kt:4:19: error: initializer type mismatch: expected 'Byte', actual 'Int'.
    val big: Byte = 200
                  ^
bad2.kt:7:18: error: initializer type mismatch: expected 'Float', actual 'Double'.
    val f: Float = 1.0
                 ^
bad2.kt:9:20: error: initializer type mismatch: expected 'Double', actual 'Float'.
    val d2: Double = 1f
                   ^
```

★ **여기서 셋이 갈린다.**

```text
  정수 리터럴                         실수 리터럴
  +--------------------------+       +--------------------------+
  | val b: Byte   = 1   OK   |       | val f: Float  = 1.0  ERR |
  | val l: Long   = 1   OK   |       | val d: Double = 1f   ERR |
  | val big: Byte = 200 ERR  |       +--------------------------+
  +--------------------------+         실수는 어느 방향도 안 된다
    기대 타입에 맞춰 준다
    단 그 타입의 범위 안일 때만
```

- **정수 리터럴은 기대 타입을 따라간다** — 범위에 들어가면 `Byte`·`Short`·`Long` 어디로든 간다.
- 범위를 벗어나면(`200` 은 `Byte` 에 안 들어간다) 리터럴이 `Int` 로 굳고 그때 타입 불일치가 난다 — **에러 메시지의 `actual 'Int'` 가 그 증거다.**
- **실수 리터럴은 따라가지 않는다.** `1.0` 은 `Double` 로 굳고 `Float` 자리를 거부한다. `1f` 도 `Double` 자리를 거부한다.
- 그래서 "Kotlin 에는 암묵 변환이 없다" 는 **값에는 맞고 리터럴에는 절반만 맞다.**

**타입 추론 결과** (`ex.kt`)

```text
--- 2. 리터럴 타입 추론 ---
1   -> Int / java.lang.Integer
1L  -> Long
1.0 -> Double
1f  -> Float
1u  -> UInt
1_000_000 = 1000000, 0xFF = 255, 0b1010 = 10
```

- 기대 타입이 없으면 `1` 은 `Int`, `1.0` 은 `Double` 이다.
- 밑줄 `_` 은 자릿수 구분자이고 값에 영향이 없다. 16진 `0x`, 2진 `0b` 는 있고 **8진 리터럴은 없다.**

비용 — 전부 컴파일 타임. 런타임에 남는 것이 없다.

### (5) ★ `Char` 는 수가 아니다 — 그런데 `+ 1` 은 된다

**언제 쓰나** — Java 의 `char c = 'a'; int n = c + 1;` 을 옮길 때.

**출력** (`ex.kt`)

```text
--- 4. Char ---
'a' + 1 = b  (타입 Char)
'a'.code = 97   'b' - 'a' = 1  (타입 Int)
'a'.toString() = a   65.toChar() = A
```

```text
  Java                              Kotlin
  'a' + 1  ──> int 98               'a' + 1  ──> Char 'b'      ★ 타입이 다르다
  'b' - 'a' ─> int 1                'b' - 'a' ─> Int 1
  int n = 'a'  OK                   val n: Int = 'a'  ERROR
                                    'a'.code ──> Int 97        ★ 이것이 정식 통로
```

- `Char + Int` 는 **`Char` 를 낸다**(연산자 오버로드). Java 처럼 `int` 로 승격되지 않는다.
- `Char - Char` 는 `Int` 다. 거리는 수이므로 말이 된다.
- **코드포인트를 얻는 정식 통로는 `.code`** 다. `Char.toInt()` 는 **아직 있지만 경고가 붙는다.**

```text
ch.kt:3:17: warning: 'fun toInt(): Int' is deprecated. Conversion of Char to Number is deprecated. Use Char.code property instead.
    println('a'.toInt())
                ^^^^^
```

비용 — 없다. 바이트코드에서는 그냥 `int` 연산이다.

### (6) ★★ `Int` 와 `Int?` 는 바이트코드에서 다른 타입이다 — 이 주제의 급소

**언제 쓰나** — "`?` 하나 붙였을 뿐인데 뭐가 달라지나" 를 물을 때.

```kotlin
fun plain(a: Int, b: Int): Int = a + b
fun nullable(a: Int?, b: Int?): Int? = if (a == null || b == null) null else a + b
```

**출력** (`javap -s -p outbox/BoxKt.class`)

```text
  public static final int plain(int, int);
    descriptor: (II)I

  public static final java.lang.Integer nullable(java.lang.Integer, java.lang.Integer);
    descriptor: (Ljava/lang/Integer;Ljava/lang/Integer;)Ljava/lang/Integer;
```

★ **`?` 하나가 `I` 를 `Ljava/lang/Integer;` 로 바꾼다.** 소스의 한 글자가 JVM 타입을 갈아 끼운 것이다.

그 전환이 어디서 일어나는지도 보인다.

```kotlin
fun boxIt(n: Int): Int? = n
```

```text
public final class TwoKt {
  public static final java.lang.Integer boxIt(int);
    Code:
       0: iload_0
       1: invokestatic  #12                 // Method java/lang/Integer.valueOf:(I)Ljava/lang/Integer;
       4: areturn
}
```

- 소스에는 `return n` 한 줄뿐인데 **`Integer.valueOf` 호출이 들어 있다.** 컴파일러가 끼워 넣은 것이다.
- `Int` 는 **JVM 기본형**이라 `null` 을 담을 자리가 없다. `Int?` 를 쓰는 순간 객체가 필요해진다.
- 그래서 **`Int?` 는 「`Int` 에 null 을 추가한 것」이 아니라 「다른 런타임 표현」이다.**

비용 — 박싱 한 번마다 `valueOf` 호출 1회. 캐시 밖이면 힙에 객체 하나.

### (7) `===` 가 `Int?` 에서 갈리는 것 — 원인은 Java 쪽 캐시다

**언제 쓰나** — `Int?` 두 개를 `===` 로 비교하고 싶어질 때. (결론: **하지 마라.**)

**출력** (`box.kt`)

```text
Int  127 === 127 : true
Int? 127 === 127 : true
Int? 128 === 128 : false
Int? 127 ==  127 : true
Int? 128 ==  128 : true
```

★ **`===` 만 128 에서 뒤집히고 `==` 는 안 뒤집힌다.** 원인은 (6)의 `Integer.valueOf` 안에 있는 캐시다.

- **캐시의 정본은 [`../../../java/syntax/01-primitives-and-wrappers/`](../../../java/syntax/01-primitives-and-wrappers/)** 다 — 범위가 왜 `-128\~127` 인지, JLS 가 무엇을 보장하는지, JVM 옵션으로 어떻게 뒤집히는지가 전부 거기 있다. **여기서 다시 설명하지 않는다.**
- 여기서 받아 쓸 결론은 하나다 — **Kotlin 의 `===` 는 Java 의 `==`(참조 비교)이고, `Int?` 는 `Integer` 이므로 같은 함정에 그대로 빠진다.**

그런데 컴파일러가 먼저 말린다.

**경고** (`kotlinc box.kt`)

```text
box.kt:11:35: warning: identity equality for arguments of types 'Int' and 'Int' is deprecated.
box.kt:12:35: warning: identity equality for arguments of types 'Int?' and 'Int?' is prohibited.
box.kt:13:35: warning: identity equality for arguments of types 'Int?' and 'Int?' is prohibited.
```

- ★ **두 문구가 다르다** — `Int` 끼리는 `deprecated`, `Int?` 끼리는 **`prohibited`**.
- 그런데 **`prohibited` 인데도 컴파일은 통과했다**(경고일 뿐 에러가 아니다). 앞으로 에러가 될 것이라는 예고로 읽는다.
- 수 타입에는 `==` 만 쓴다. `===` 는 **참조 동일성을 정말 묻고 싶을 때**만 쓴다.

비용 — `==` 는 `Integer.equals` 또는 기본형 비교. 캐시에 의존하지 않는다.

## 문법 — 형태와 규칙

```kotlin
// 선언
val a = 1                 // 재대입 불가. 타입 추론
var b = 1                 // 재대입 가능
val c: Long = 1L          // 타입 명시
val d: Int                // 나중에 한 번만 대입 가능 (선언과 대입 분리)
d = 2

// 여덟 기본 타입
val byte: Byte = 1        // 8bit
val short: Short = 1      // 16bit
val int: Int = 1          // 32bit
val long: Long = 1L       // 64bit
val float: Float = 1f     // 32bit
val double: Double = 1.0  // 64bit
val bool: Boolean = true
val char: Char = 'a'      // 16bit

// 리터럴
val hex = 0xFF            // 255
val bin = 0b1010          // 10
val sep = 1_000_000
val u: UInt = 1u          // 부호 없음 (1.5 Stable)

// 변환은 전부 명시
val l = int.toLong()
val code = char.code      // Char -> Int 는 .code
```

**출력** (`types.kt`)

```text
Byte    8bit  -128 ~ 127
Short   16bit -32768 ~ 32767
Int     32bit -2147483648 ~ 2147483647
Long    64bit -9223372036854775808 ~ 9223372036854775807
Float   32bit
Double  64bit
Char    16bit 0 ~ 65535
Boolean (SIZE_BITS 없음)
```

규칙 불릿.

- `val` 은 **한 번만 대입**이지 **선언 자리에서 대입**이 아니다. 위 `d` 처럼 나눠 쓸 수 있다.
- `Boolean` 에는 `SIZE_BITS` 가 없다 — **크기가 명세되지 않았다**(JVM 구현에 달렸다).
- 산술 연산자는 **혼합 타입을 받는다**. 대입만 막는 것이지 연산까지 막는 게 아니다.

**출력** (`ex.kt`)

```text
--- 5. 혼합 산술은 되나 ---
1 + 2L = 3  (타입 Long)
1 + 2.0 = 3.0  (타입 Double)
```

- `Int + Long` 은 `Long`, `Int + Double` 은 `Double` 이다. **`Int.plus(Long)` 같은 오버로드가 stdlib 에 전부 선언돼 있어서**지 자동 승격이 아니다.
- 오버플로는 **조용히 감긴다** — `Int.MAX_VALUE + 1 = -2147483648`(위 `ex.kt` 출력). 예외가 아니다.

## 어디서 틀리나

| 틀리는 형태 | 무슨 일이 일어나나 | 고치는 법 |
|---|---|---|
| `val` 컬렉션을 밖에 내주고 "불변" 이라 믿기 | 밖에서 `add` 가 통한다 | 타입을 `List` 로 내리고, 그래도 뷰일 뿐임을 안다 |
| `val l: Long = someInt` | `initializer type mismatch` | `someInt.toLong()` |
| `val f: Float = 1.0` | `expected 'Float', actual 'Double'` | `1.0f` 또는 `1f` |
| `val b: Byte = 200` | `expected 'Byte', actual 'Int'` | 범위 밖이다 — `Short` 를 쓰거나 값을 고친다 |
| `'a' + 1` 이 `Int` 일 거라 예상 | `Char` 다 | 수가 필요하면 `'a'.code + 1` |
| `Int?` 를 `===` 로 비교 | 128부터 `false` | `==` 를 쓴다. 경고가 이미 말해 준다 |
| `300.toByte()` 로 좁히기 | `44` 가 조용히 나온다 | 범위를 먼저 검사한다 — 변환 함수는 안 막아 준다 |
| 지역 `val` 을 런타임 보장으로 믿기 | 바이트코드에 흔적이 없다 | 프로퍼티 `val` 만 `final` 로 내려간다 |

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 | 근거 |
|---|---|---|
| `val` 재대입이 컴파일 에러다 | **언어** | 명세·에러 메시지 |
| **`val` 프로퍼티가 JVM `final` 필드가 된다** | **구현** (Kotlin/JVM) | `javap` — 다른 타깃에는 `final` 개념이 없을 수 있다 |
| **지역 `val` 이 바이트코드에 안 남는다** | **구현** | `javap` — 두 함수가 같은 `istore_0` |
| `Int` → `Long` 대입이 에러다 | **언어** | `initializer type mismatch` |
| 정수 리터럴이 기대 타입을 따라간다 | **언어** | 명세 (Integer literals) |
| **`Int?` 가 `java.lang.Integer` 로 내려간다** | **구현** (Kotlin/JVM) | `javap -s` — 디스크립터 |
| **`-128\~127` 의 `===` 가 `true` 인 것** | **Java 구현** | [`java/syntax/01`](../../../java/syntax/01-primitives-and-wrappers/) 이 정본 — JVM 옵션으로 뒤집힌다 |
| `Int?` 끼리의 `===` 가 `prohibited` 경고다 | **언어**(예고) | kotlinc 경고 — 지금은 통과하지만 앞으로 막힌다 |
| `Int` 오버플로가 감긴다 | **언어** | 2의 보수 — 표현 자체는 [`cs/foundations/data-representation/`](../../../../data-representation/) 가 정본 |
| `Boolean` 의 크기 | **미명세** | `Boolean.SIZE_BITS` 가 없다 |

★ **"`Int` 는 기본형이고 `Int?` 는 객체다" 는 JVM 타깃의 구현 사실**이다. Kotlin 언어가 보장하는 것은 "`Int?` 는 `null` 을 담을 수 있고 `Int` 는 못 담는다" 까지다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 기본 선언 | **`val`** | 재대입을 막으면 읽는 사람이 추적할 상태가 줄어든다 |
| 루프 누적·상태 기계 | `var` | 억지로 `val` 로 바꾸면 더 어려워진다 |
| "없을 수도 있음" 을 표현 | `Int?` | 단 박싱이 붙는다((6)) |
| 대량 수치 루프 | `Int` (non-null) | `Int?` 로 두면 원소마다 박싱 |
| 컬렉션을 필드로 들고 외부에 노출 | `val` + 읽기 전용 타입 | `val` 만으로는 아무것도 안 잠긴다 |
| Java 의 `long`/`double` 과 섞이는 계산 | 경계에서 한 번에 `toLong()` | 식마다 변환을 흩뿌리지 않는다 |
| 부호 없는 값(바이트 프로토콜) | `UByte`/`UInt` | 1.5 Stable. 다만 Java 쪽에서는 안 보인다 |

판단 규칙 두 줄.

- **`var` 를 쓸 때마다 "이 값이 언제 바뀌나" 를 한 문장으로 말할 수 있어야 한다.** 못 하면 `val` 로 되돌린다.
- **`?` 는 "없음" 이라는 뜻일 때만 붙인다.** 귀찮음을 피하려고 붙이면 런타임 표현까지 같이 바뀐다.

## 핵심 문장

- `val` 은 **이름표를 못 바꾼다**는 뜻이지 **내용물이 안 바뀐다**는 뜻이 아니다.
- `val` 프로퍼티는 JVM `final` 로 내려가지만 **지역 `val` 은 바이트코드에 흔적이 없다** — 보장의 세기가 다르다.
- Kotlin 은 **손실이 없는 확대 변환조차 거부한다.** 이유는 손실이 아니라 타입 추론과의 충돌이다.
- 그런데 **정수 리터럴은 기대 타입을 따라가고 실수 리터럴은 따라가지 않는다** — 비대칭을 외운다.
- `Int` 는 `I`, `Int?` 는 `Ljava/lang/Integer;` 다. **`?` 한 글자가 JVM 타입을 바꾼다.**
- `Char + Int` 는 `Char` 다. 수가 필요하면 **`.code`** 를 쓴다.

## 관련 자료

- [`../README.md`](../README.md) — Kotlin 문법·API 주제 목록(이 주제는 01번)
- [`../../언어-특성/README.md`](../../언어-특성/README.md) §5 — **「왜 가변성을 이름에 적나」라는 설계 논증과 읽기 전용 컬렉션 런타임 클래스 실측표가 거기 정본**이다. 여기는 그 문법이 바이트코드로 무엇이 되는지까지만
- [`../../../java/syntax/01-primitives-and-wrappers/`](../../../java/syntax/01-primitives-and-wrappers/) — **박싱 캐시(`-128\~127`)·오토박싱·`==` 의 정본.** 이 문서의 (7)은 거기 결론을 받아 쓴 것이다
- [`../../../java/syntax/02-numeric-operations/`](../../../java/syntax/02-numeric-operations/) — Java 의 이항 수치 승격. **Kotlin 이 거부하는 그것**이 거기서 정본으로 다뤄진다
- [`../../../../data-representation/`](../../../../data-representation/) — 2의 보수·IEEE 754. 비트 표현 자체는 거기가 정본
- [02번 주제](../02-string-templates-and-raw-strings/) — 이 타입들이 문자열에 끼워지는 방법
- [03번 주제](../03-null-safe-types/) — `Int` 와 `Int?` 의 갈림이 **타입 시스템 쪽에서** 무엇을 뜻하는지
- [목록의 **32번 주제**](../32-equality-and-equals-contract/)(동등성 — `==`/`===`) — `===` 의 의미 전체는 거기가 정본이 된다
- 목록의 **40번 주제**(읽기 전용 컬렉션) — `val` + 가변 컬렉션 문제의 반대쪽 절반

## 용어 풀이

- **`val` / `var`** — 재대입 불가 / 가능. Java 의 `final` 유무에 해당하지만 **프로퍼티일 때만 `final` 로 내려간다.**
- **재대입** — 이미 있는 변수에 다른 값을 다시 넣는 것. 객체 내부 변경과 다르다.
- **확대 변환** — 작은 수 타입을 큰 수 타입에 자동으로 옮기는 것. **Kotlin 에는 없다.**
- **좁히는 변환(narrowing)** — 큰 타입을 작은 타입으로. `toByte()` 처럼 명시 호출로만 가능하고 **값을 자른다.**
- **타입 추론** — 초기값에서 변수 타입을 컴파일러가 정하는 것. 암묵 변환이 없는 진짜 이유.
- **박싱(boxing)** — 기본형을 객체로 감싸는 것. `Int?` 는 항상 박싱된 표현이다.
- **디스크립터(descriptor)** — JVM 이 타입을 적는 문자열. `I` 는 `int`, `Ljava/lang/Integer;` 는 `Integer`.
- **`===` / `==`** — 참조 동일성 / 구조적 동등성. Kotlin 의 `==` 는 `equals` 호출로 내려간다.
- **프로퍼티(property)** — 필드 + 게터(+세터) 한 묶음. Kotlin 에는 "필드만" 이라는 선언이 없다.
- **`code`** — `Char` 의 코드포인트를 `Int` 로 주는 프로퍼티. `Char.toInt()` 를 대체했다.
- **부호 없는 타입** — `UByte`/`UShort`/`UInt`/`ULong`. 1.5 Stable. 내부는 부호 있는 타입 위의 `value class` 다.

---

## 더 들어가면

- `UInt` 는 **`value class`** 로 만들어졌다 — JVM 에 부호 없는 정수가 없으므로 `Int` 위에 얹은 것이다.\
  그래서 Java 쪽에서 보면 그냥 `int` 로 보이고 부호가 안 지켜진다. [목록의 **26번 주제**](../26-value-class-and-boxing/)(`value class`)가 그 기법의 정본이 된다.
- `Int.MAX_VALUE + 1` 이 감기는 것은 **Java 와 같다.** 감김을 막고 싶으면 `Math.addExact` 를 직접 부른다 — stdlib 에 대응 함수가 없다.
- `val` 프로퍼티는 `final` 필드가 되지만 **`open val` 은 게터가 오버라이드 가능**해져서 성질이 완전히 달라진다.\
  그 차이가 [04번 주제](../04-smart-casts/)(스마트 캐스트)에서 그대로 실패 모드가 된다 — 「커스텀 getter」 항목이다.
- `0x`·`0b` 는 있는데 **8진 리터럴은 없다.** Java 의 `010 == 8` 같은 함정을 통째로 없앤 것이다.
