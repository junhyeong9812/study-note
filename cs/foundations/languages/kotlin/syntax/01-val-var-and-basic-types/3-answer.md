# kotlin/syntax/01 — `val`/`var` 와 기본 타입: 암묵 수치 변환이 없다 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러·경고·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과
> Temurin **JDK 21.0.5** 의 `javap` 에서 실제로 얻은 것이다.\
> 박싱 캐시 관련 결론은 [`../../../java/syntax/01-primitives-and-wrappers/`](../../../java/syntax/01-primitives-and-wrappers/) 에서 **받아 쓴 것**이고 여기서 재측정하지 않았다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★ `val` 은 무엇을 막고 무엇을 못 막는가

**출력** (`ex.kt` · `kotlinc bad2.kt`)

```text
--- 1. val 은 재대입만 막는다 ---
val list 에 add -> [1, 2, 3]
```

```text
bad2.kt:3:5: error: 'val' cannot be reassigned.
    x = 2
    ^
```

**왜 그런가**

- `[A]` `list.add(3)` — **통과.** 결과는 `[1, 2, 3]`.
- `[B]` `list = mutableListOf(9)` — 에러 (`'val' cannot be reassigned.`).
- `[C]` `x = 2` — 에러 (같은 메시지).

```text
   list ──대못──> [ 1, 2 ]
        list.add(3)      ← 대못과 무관. 상자 안의 일이다
   list ──대못──> [ 1, 2, 3 ]
        list = ...       ← 대못이 막는다
```

- `val` 이 고정하는 것은 **참조**다. 참조가 가리키는 객체 내부는 그 객체 타입이 정한다.
- 그래서 **"`val` 이니까 불변"은 `val` + 가변 타입 조합에서 바로 깨진다.**
- 타입을 `List` 로 낮추면 `add` 가 컴파일 에러가 되지만, 그것도 **뷰일 뿐 진짜 불변이 아니다** —\
  런타임 클래스 실측표는 [`../../언어-특성/README.md`](../../언어-특성/README.md) §5 가 정본이다.

### 2. ★★ 이 네 줄 중 어느 것이 에러이고 메시지는 무엇인가

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

**왜 그런가**

| | 구문 | 결과 |
|---|---|---|
| `[A]` | `val l: Long = i` | **에러** — 넓히는 방향인데도 |
| `[B]` | `val d: Double = i` | **에러** |
| `[C]` | `val b: Byte = 1` | **통과** — 리터럴이라서 (3번) |
| `[D]` | `val i2: Int = b` | **에러** |
| `[E]` | `val n: Int = c` | **에러** — `Char` 는 수가 아니다 |

- 메시지 형태는 고정이다 — **`expected '<적은 타입>', actual '<실제 타입>'`**. 이 두 낱말만 읽으면 된다.
- Java 였다면 `[A]`·`[B]`·`[D]`·`[E]` 가 **전부 통과**한다(확대 변환·`char` → `int`). 즉 **다섯 중 넷이 뒤집혔다.**
- **정보 손실이 없는 `[A]` 까지 막는 이유는 손실이 아니라 타입 추론과의 충돌이다.**\
  암묵 확대가 허용되면 `val x = 1` 을 볼 때 컴파일러가 `Byte`·`Short`·`Int`·`Long` 중 무엇으로 정할지 근거가 없어진다.\
  Kotlin 은 **모든 값이 하나의 정해진 타입을 갖는다**를 지키는 대신 대입에서의 편의를 버렸다.
- 고치는 법은 전부 명시 변환이다 — `i.toLong()`·`i.toDouble()`·`b.toInt()`·`c.code`.

### 3. ★★ 리터럴은 왜 예외처럼 보이는가 — 넷의 결과를 예측하라

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

**왜 그런가**

| | 구문 | 결과 |
|---|---|---|
| `[A]` | `val b: Byte = 1` | **통과** |
| `[B]` | `val big: Byte = 200` | 에러 — `actual 'Int'` |
| `[C]` | `val l: Long = 1` | **통과** |
| `[D]` | `val f: Float = 1.0` | 에러 — `actual 'Double'` |
| `[E]` | `val d: Double = 1f` | 에러 — `actual 'Float'` |

```text
  정수 리터럴                         실수 리터럴
  +--------------------------+       +--------------------------+
  | Byte  = 1    OK          |       | Float  = 1.0   ERROR     |
  | Long  = 1    OK          |       | Double = 1f    ERROR     |
  | Byte  = 200  ERROR       |       +--------------------------+
  +--------------------------+         어느 방향도 안 된다
    기대 타입을 따라간다
    단 범위 안일 때만
```

- `[B]` 의 `actual 'Int'` 가 결정적이다 — **`200` 이 `Byte` 범위를 벗어나자 리터럴이 `Int` 로 굳었고**,\
  그 다음에 비로소 "`Int` 를 `Byte` 에 못 넣는다"는 2번의 규칙이 걸린다.\
  즉 **에러가 난 이유가 두 단계**다. 메시지 한 줄에 그 두 단계가 다 적혀 있다.
- **정수 리터럴은 타입이 미정인 채로 기대 타입에 맞춰지고, 실수 리터럴은 `1.0` 이 `Double`·`1f` 가 `Float` 로 즉시 굳는다.**
- 그래서 2번의 결론은 이렇게 고쳐야 한다 — **"값에는 암묵 변환이 없다. 리터럴은 정수 쪽만 기대 타입을 따라간다."**

### 4. ★ `Char` 는 수인가 — 이 넷의 값과 타입은 무엇인가

**출력** (`ex.kt`)

```text
--- 4. Char ---
'a' + 1 = b  (타입 Char)
'a'.code = 97   'b' - 'a' = 1  (타입 Int)
'a'.toString() = a   65.toChar() = A
```

```text
bad.kt:8:16: error: initializer type mismatch: expected 'Int', actual 'Char'.
    val n: Int = c
               ^
```

**왜 그런가**

| | 식 | 값 | 타입 |
|---|---|---|---|
| `[A]` | `'a' + 1` | `b` | **`Char`** |
| `[B]` | `'b' - 'a'` | `1` | `Int` |
| `[C]` | `'a'.code` | `97` | `Int` |
| `[D]` | `val n: Int = 'a'` | — | **컴파일 에러** |

```text
  Java                              Kotlin
  'a' + 1   ──> int 98              'a' + 1   ──> Char 'b'     ★ 여기가 갈린다
  'b' - 'a' ──> int 1               'b' - 'a' ──> Int 1
  int n = 'a'   OK (97)             val n: Int = 'a'  ERROR
                                    'a'.code  ──> Int 97       ★ 정식 통로
```

- `[A]` 가 Java 와 다르다. **`Char.plus(Int): Char` 라는 연산자가 선언돼 있어서** 결과가 다시 `Char` 다.\
  "다음 글자" 를 얻는 연산으로 설계된 것이고, `char` 를 `int` 로 승격시키는 Java 와 의도가 다르다.
- `[B]` 는 `Char.minus(Char): Int` — **거리**이므로 수가 나온다.
- `Char.toInt()` 는 **제거된 게 아니라 아직 있고 경고만 붙는다** — 던져 보면 컴파일이 통과한다.

```text
ch.kt:3:17: warning: 'fun toInt(): Int' is deprecated. Conversion of Char to Number is deprecated. Use Char.code property instead.
    println('a'.toInt())
                ^^^^^
```

  경고 문구가 이유를 말한다 — **`Char` 를 `Number` 로 바꾸는 것 자체를 폐기**한 것이다.\
  `'a' + 1` 이 `Char` 인 것과 `'a'.toInt()` 가 `Int` 인 것이 섞여 "`Char` 가 수인가" 가 모호해졌기 때문이고,\
  `.code`(코드포인트)와 `.digitToInt()`(문자 `'7'` → 수 `7`)로 **의도를 이름에 적게** 갈랐다.

### 5. ★★ `Int` 와 `Int?` 는 바이트코드에서 같은 타입인가

**출력** (`javap -s -p outbox/BoxKt.class`)

```text
  public static final int plain(int, int);
    descriptor: (II)I

  public static final java.lang.Integer nullable(java.lang.Integer, java.lang.Integer);
    descriptor: (Ljava/lang/Integer;Ljava/lang/Integer;)Ljava/lang/Integer;
```

**출력** (`javap -c -p outtwo/TwoKt.class`)

```text
public final class TwoKt {
  public static final java.lang.Integer boxIt(int);
    Code:
       0: iload_0
       1: invokestatic  #12                 // Method java/lang/Integer.valueOf:(I)Ljava/lang/Integer;
       4: areturn
}
```

**왜 그런가**

- **디스크립터가 통째로 다르다** — `(II)I` 대 `(Ljava/lang/Integer;Ljava/lang/Integer;)Ljava/lang/Integer;`.\
  `?` 한 글자가 JVM 기본형을 객체 참조로 바꾼다.
- `boxIt` 의 본문은 `return n` 뿐인데 바이트코드에는 **`Integer.valueOf` 호출**이 있다. **컴파일러가 끼워 넣은 것**이고,\
  이 호출 안에서 박싱 캐시가 끼어든다(6번).
- 그래서 `Int?` 는 **「`Int` 에 null 을 더한 것」이 아니라 다른 런타임 표현**이다.\
  `Int` 는 `null` 을 담을 **자리가 없다** — 값 32비트가 전부이고 "없음" 을 표시할 비트가 없다.
- 실무적 결론 — **대량 수치 루프에서 `Int?` 를 쓰면 원소마다 객체가 생긴다.** 타입 하나 바꿨을 뿐인데 할당이 생긴다.

### 6. ★ 이 다섯 줄의 출력과 컴파일러 경고는 무엇인가

**출력** (`box.kt`)

```text
Int  127 === 127 : true
Int? 127 === 127 : true
Int? 128 === 128 : false
Int? 127 ==  127 : true
Int? 128 ==  128 : true
```

**경고** (`kotlinc box.kt` — 컴파일은 성공했다)

```text
box.kt:11:35: warning: identity equality for arguments of types 'Int' and 'Int' is deprecated.
    println("Int  127 === 127 : ${a === b}")
                                  ^^^^^^^
box.kt:12:35: warning: identity equality for arguments of types 'Int?' and 'Int?' is prohibited.
    println("Int? 127 === 127 : ${c === d}")
                                  ^^^^^^^
box.kt:13:35: warning: identity equality for arguments of types 'Int?' and 'Int?' is prohibited.
```

**왜 그런가**

| | 식 | 출력 |
|---|---|---|
| `[A]` | `a === b` (`Int`, 127) | `true` |
| `[B]` | `c === d` (`Int?`, 127) | `true` |
| `[C]` | `e === f` (`Int?`, 128) | **`false`** |
| `[D]` | `c == d` | `true` |
| `[E]` | `e == f` | `true` |

- ★ **경고 문구가 두 가지다** — `Int` 끼리는 **`deprecated`**, `Int?` 끼리는 **`prohibited`**.\
  `Int` 끼리의 `===` 는 애초에 기본형 비교라 의미가 없고, `Int?` 끼리는 **의미가 있는데 그 의미가 함정**이라 더 세게 말린다.
- ★ **`prohibited` 인데도 컴파일은 통과했다**(경고일 뿐 에러가 아니다). 낱말만 보고 "막혔다" 고 읽으면 틀린다 —\
  **앞으로 에러가 된다는 예고**로 읽는다.
- 원인은 **Kotlin 이 아니라 Java 쪽**에 있다. `Int?` 는 5번에서 본 대로 `java.lang.Integer` 이고,\
  `Integer.valueOf` 안의 캐시가 `-128\~127` 에서만 같은 객체를 돌려준다.
- **정본은 [`../../../java/syntax/01-primitives-and-wrappers/`](../../../java/syntax/01-primitives-and-wrappers/)** 다 —\
  범위가 왜 그 값인지, JLS 가 무엇을 보장하는지, `-Djava.lang.Integer.IntegerCache.high` 로 어떻게 뒤집히는지가 전부 거기 있다.
- 받아 쓸 결론 한 줄 — **Kotlin `===` 는 Java `==`(참조 비교)이고, 수 타입에는 `==` 만 쓴다.**

### 7. `val` 은 런타임 보장인가 컴파일 검사인가

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

**왜 그런가**

| | JVM 에 남는 것 | 보장 범위 |
|---|---|---|
| `val` 프로퍼티 | `private final` 필드 + 게터 **(세터 없음)** | **런타임까지** — Java 쪽에서도 못 고친다 |
| `var` 프로퍼티 | `private` 필드 + 게터 + 세터 | — |
| 지역 `val` | **아무것도 없다** (`istore_0`) | **이 함수 소스 안에서만** |
| 지역 `var` | 같은 `istore_0` | — |

- 두 함수의 `istore_0` 이 같다 — **지역 `val` 과 `var` 는 바이트코드에서 구별되지 않는다.**
- 그래서 **"`val` 이다" 라는 문장의 세기가 두 가지**다. 프로퍼티는 JVM `final` 이고, 지역 변수는 프런트엔드 검사뿐이다.
- Java 에서 Kotlin 의 `val` 프로퍼티는 **못 고친다** — `private final` 이고 세터도 없다.\
  다만 리플렉션은 별개이고, `@JvmField` 를 붙이면 `public final` 필드로 노출되어 **읽기는 직접** 가능해진다.

### 8. 대입은 막는데 산술은 왜 되는가

**출력** (`ex.kt`)

```text
--- 5. 혼합 산술은 되나 ---
1 + 2L = 3  (타입 Long)
1 + 2.0 = 3.0  (타입 Double)
--- 6. UInt ---
UInt.MAX_VALUE = 4294967295  u = 4294967295
Int.MAX_VALUE + 1 = -2147483648
```

**왜 그런가**

- `1 + 2L` 은 `Long`, `1 + 2.0` 은 `Double` 이다.
- **이것을 "자동 승격" 이라고 부르면 틀린다.** Java 의 이항 수치 승격은 **언어 규칙**이지만,\
  Kotlin 에는 그런 규칙이 없고 **`Int` 에 `plus(Long): Long`·`plus(Double): Double` 같은 오버로드가 stdlib 에 전부 선언돼 있을 뿐**이다.\
  즉 **함수 오버로드 해소**가 답을 내는 것이지 타입이 변환된 게 아니다.
- 그래서 대입은 막히고 산술은 통한다 — **대입에는 오버로드할 함수가 없다.**
- `Int.MAX_VALUE + 1` 은 **예외가 아니라 감김**이다(`-2147483648`). Java 와 같다.\
  막고 싶으면 `Math.addExact` 를 직접 부른다 — stdlib 에 대응 함수가 없다.
- Java 의 이항 승격 정본은 [`../../../java/syntax/02-numeric-operations/`](../../../java/syntax/02-numeric-operations/).

### 9. 명시 변환 함수는 무엇을 안 막아 주는가

**출력** (`ex.kt`)

```text
--- 3. 명시 변환 ---
i.toLong() = 1  i.toDouble() = 1.0  i.toByte() = 1
300.toByte() = 44
1.9.toInt() = 1   (-1.9).toInt() = -1
```

**왜 그런가**

- `300.toByte()` 는 **`44`** 다. `300` 의 하위 8비트(`0b00101100` = 44)만 남는다 — **조용히 자른다.**
- `1.9.toInt()` = `1`, `(-1.9).toInt()` = `-1`. **반올림이 아니라 0 쪽으로 버린다**(truncation).\
  반올림이 필요하면 `Math.round` 또는 `roundToInt()` 를 쓴다.
- 경계는 이렇다.

```text
  컴파일러가 막는 것                 변환 함수가 통과시키는 것
  +-------------------------+       +-------------------------+
  | val b: Byte = anInt     |       | anInt.toByte()          |
  |   -> 타입 불일치 에러    |  ★    |   -> 잘려도 통과        |
  +-------------------------+       +-------------------------+
      "말없이 하지 마라"                "네가 적었으니 네 책임"
```

- **Kotlin 이 막는 것은 「말없이 일어나는 것」이지 「손실 자체」가 아니다.**\
  그래서 `toByte()`·`toInt()` 앞에서는 **범위 검사를 직접** 해야 한다 — 컴파일러가 도와줄 일이 없다.

### 10. 어느 것이 언어 보장이고 어느 것이 JVM 구현인가

| 사실 | 어느 쪽 | 근거 |
|---|---|---|
| `val` 재대입이 컴파일 에러다 | **언어** | `'val' cannot be reassigned.` |
| `Int` → `Long` 대입이 에러다 | **언어** | `initializer type mismatch` |
| 정수 리터럴이 기대 타입을 따라간다 | **언어** | 명세 |
| **`val` 프로퍼티가 `final` 필드가 된다** | **구현**(Kotlin/JVM) | `javap` |
| **지역 `val` 이 바이트코드에 안 남는다** | **구현** | `javap` — 두 함수가 같다 |
| **`Int?` 가 `java.lang.Integer` 다** | **구현**(Kotlin/JVM) | `javap -s` 디스크립터 |
| **`-128\~127` 의 `===` 가 `true`** | **Java 구현** | [`java/syntax/01`](../../../java/syntax/01-primitives-and-wrappers/) — `IntegerCache.high` 옵션으로 뒤집힌다 |
| `Int?` 끼리 `===` 가 `prohibited` 경고 | **언어**(예고) | kotlinc 경고 |
| `Boolean` 의 비트 크기 | **미명세** | `Boolean.SIZE_BITS` 가 없다 |

- 경계를 한 문장으로 — **"`Int?` 는 null 을 담을 수 있다" 는 언어, "그 표현이 `Integer` 다" 는 구현.**
- 그래서 Kotlin/Native·Kotlin/JS 에서는 **뒤쪽 절반이 성립하지 않는다.** 앞쪽 절반만 옮겨 간다.

### 11. 다른 주제와 잇기

- **`Int` 와 `Int?` 의 갈림 → [03번](../03-null-safe-types/)** — 거기서는 같은 갈림이 **타입 시스템 쪽**에서 다뤄진다.\
  `String` 과 `String?` 도 **다른 타입**이고, `?.`·`?:`·`!!` 는 그 두 타입 사이를 건너는 세 가지 다리다.
- **`val` + 커스텀 getter → [04번](../04-smart-casts/)** — `val` 프로퍼티라도 **게터가 있으면 스마트 캐스트가 거부된다**.\
  에러 메시지는 `smart cast to 'String' is impossible, because 's' is a property that has an open or custom getter.` 이다.\
  "`val` 이면 안 바뀐다" 가 컴파일러 기준으로도 틀린 자리다.
- **Java 의 이항 수치 승격 → [`../../../java/syntax/02-numeric-operations/`](../../../java/syntax/02-numeric-operations/)** 가 정본.\
  Kotlin 이 거부한 바로 그것이다.
- **박싱 캐시 → [`../../../java/syntax/01-primitives-and-wrappers/`](../../../java/syntax/01-primitives-and-wrappers/)** 가 정본.\
  이 문서가 받아 쓴 것은 **결론 한 줄**뿐이다 — "`-128\~127` 은 같은 객체이고 그 밖은 아니며, 그것은 JVM 옵션으로 뒤집힌다."

---

## 실행 검증

**환경** (`kotlinc -version` · `java -version`)

```text
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
openjdk version "21.0.5" 2024-10-15 LTS
OpenJDK Runtime Environment Temurin-21.0.5+11 (build 21.0.5+11-LTS)
```

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `ex.kt` | `val` + `add`, 리터럴 추론, 명시 변환, `Char` 산술, 혼합 산술, `UInt`, 오버플로 | `kotlinc ex.kt -d out/` → `java -cp "out:kotlin-stdlib.jar" ExKt` |
| `bad.kt` | 암묵 수치 변환 거부 4건 | `kotlinc bad.kt` (컴파일 실패가 결과) |
| `bad2.kt` | `val` 재대입 거부, 리터럴 범위·실수 리터럴 비대칭 3건 | `kotlinc bad2.kt` |
| `types.kt` | 여덟 기본 타입의 비트 폭·범위 | `kotlinc` → `java` |
| `box.kt` | `Int`/`Int?` 의 `===`·`==`, **경고 두 종류** | `kotlinc box.kt` → `java` |
| `two.kt` | `Int` → `Int?` 에 `Integer.valueOf` 가 끼워지는 것 | `javap -c -p outtwo/TwoKt.class` |
| `vv.kt` | `val`/`var` 프로퍼티의 필드 수식어와 접근자 | `javap -p -s outvv/P.class` |
| `loc.kt` | 지역 `val`/`var` 가 바이트코드에서 같은 것 | `javap -c -p outloc/LocKt.class` |
| `ch.kt` | `Char.toInt()` 가 **제거가 아니라 경고**인 것, `digitToInt()` 존재 | `kotlinc ch.kt` (경고가 결과) |
| `jf.kt` | `@JvmField` 가 `public final` 필드를 만드는 것 | `javap -p outjf/Q.class` |

**구현 의존 항목** — `javap` 디스크립터(`I` / `Ljava/lang/Integer;`), `Integer.valueOf` 호출이 끼워지는 것,
`private final` 필드, 지역 변수 슬롯 번호, `-128\~127` 의 `===` 결과, 경고 문구(`deprecated`/`prohibited`) —
전부 **이 컴파일러 버전·이 JVM 타깃의 산출물**이다. 버전이 오르면 다시 찍는다.\
반면 "`val` 은 재대입 불가"·"값에는 암묵 수치 변환이 없다"·"정수 리터럴은 기대 타입을 따른다"·
"`Char + Int` 는 `Char`" 는 **언어 규칙**이라 타깃과 무관하다.

**못 잰 것** — `-128\~127` 캐시 범위를 **Kotlin 쪽에서 다시 재지 않았다.**
[`java/syntax/01`](../../../java/syntax/01-primitives-and-wrappers/) 이 정본이고 재측정은 그 문서의 규칙(중복 금지)에 어긋나므로,
여기서는 `Int?` 에서 같은 경계가 관찰된다는 사실(`127` → `true`, `128` → `false`)만 확인했다.
