# kotlin/syntax/08 — 함수 선언: 기본 인자·이름 붙인 인자·단일 표현식 함수 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Functions](https://kotlinlang.org/docs/functions.html) · [Calling Kotlin from Java](https://kotlinlang.org/docs/java-to-kotlin-interop.html) · [Returns and jumps](https://kotlinlang.org/docs/returns.html).
> **실행 검증** — 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javap` 에서 실제로 얻었다.\
> **Java 쪽 호출은 같은 JDK 의 `javac` 로 컴파일해 실제로 섞어 돌렸다.**\
> `kotlinc` 7회 · `javac` 2회 · `java` 2회 · `javap` 6회. 컴파일 실패 시나리오 3벌.
> ⚠️ **`-jvm-target` 을 밝히지 않은 바이트코드 주장은 반쪽이다.** 이 문서의 역어셈블은 **기본값 1.8**(`major version: 52`)이다 —\
> 그래서 문자열 보간이 `StringBuilder` 로 보인다([02번 주제](../02-string-templates-and-raw-strings/)).
> **버전** — 기본 인자·이름 붙인 인자·단일 표현식 함수는 1.0. `@JvmOverloads` 도 1.0.
> **경계** — `vararg`·`spread`·로컬 함수·`infix` 는 [09번 주제](../09-varargs-spread-local-and-infix-functions/)가 정본이다.\
> 람다와 고차 함수는 [목록의 **10번 주제**](../10-lambdas-and-higher-order-functions/), `@JvmStatic`/`@JvmName` 등 상호운용 애너테이션 **전체**는 목록의 **39번 주제**가 정본이다 —\
> 여기서는 `@JvmOverloads` **하나만** 기본 인자의 짝으로 다룬다.\
> **Java 쪽 정본은 [`../../../java/syntax/08-method-declaration-overloading/`](../../../java/syntax/08-method-declaration-overloading/)** 다.
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**Java 는 "인자를 덜 받는 버전" 을 만들려고 메서드를 여러 개 적는다. Kotlin 은 한 개만 적고 기본값을 붙인다.**

그런데 JVM 에는 "기본 인자" 라는 개념이 없다.\
그래서 컴파일러가 **몰래 메서드를 하나 더 만든다** — `이름$default` 라는 숨은 메서드와,\
**"몇 번째 인자가 생략됐나" 를 비트로 적은 정수 한 칸**이다.

> **비트마스크(bitmask)** — 여러 개의 참/거짓을 정수 하나의 비트에 나눠 담은 것.\
> 예: `6` 은 이진수로 `110` 이라 "1번·2번 인자가 생략됐다" 는 뜻이 된다.

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 같은 요리를 크기별로 메뉴에 따로 적기 | Java 의 오버로드 사슬 |
| 요리 하나에 "빼는 재료는 말씀하세요" | Kotlin 의 기본 인자 |
| 주방에 붙은 주문표 | `$default` 합성 메서드 |
| 주문표의 "뺀 재료 체크칸" | 비트마스크 `int` |
| 체크칸이 모자라면 종이를 한 장 더 | 파라미터 33개부터 마스크가 2개 |
| 재료를 **주문할 때마다** 새로 꺼낸다 | 기본값은 **호출 시점**에 평가된다 |
| 밖에서 온 손님에게는 메뉴를 다시 써 준다 | `@JvmOverloads` — Java 용 오버로드 생성 |

```text
   Java                              Kotlin
   +---------------------------+     +----------------------------------+
   | greet(n)                  |     | greet(n, g = "안녕", p = "!")    |
   |   -> greet(n, "안녕")     |     |                                  |
   | greet(n, g)               |     | 소스는 한 개                     |
   |   -> greet(n, g, "!")     |     | 바이트코드는 두 개               |
   | greet(n, g, p)  ← 진짜    |     |   greet(...)      ← 진짜         |
   +---------------------------+     |   greet$default(..., mask, null) |
     소스가 세 개                     +----------------------------------+
```

**똑같은 구조인데 손으로 쓰던 사슬을 컴파일러가 대신 쓴다** — 그리고 그 사슬이 **메서드 하나**로 접힌다.

## 이 주제가 답하려는 질문

1. 기본 인자가 **무엇으로 컴파일되는가** — 오버로드 사슬인가, 다른 무엇인가.
2. 기본값은 **언제 평가되는가** — 선언 시점인가 호출 시점인가.
3. 이름 붙인 인자로 **순서를 어디까지 바꿀 수 있는가**, 그리고 Java 에서 보면 **무엇이 사라지는가**.

## 동작 방식

### (1) ★★ 기본 인자는 `$default` 합성 메서드 + **비트마스크**다

**언제 쓰나** — "기본 인자는 오버로드를 만들어 주는 문법" 이라고 믿을 때.

```kotlin
fun greet(name: String, greeting: String = "안녕", punct: String = "!"): String =
    "$greeting, $name$punct"

fun callIt(): String = greet("준")
fun callAll(): String = greet("준", "야", "?")
fun callMiddle(): String = greet("준", punct = "?")
```

**출력** (`javap -c -p out/IcodeKt.class`)

```text
  public static final java.lang.String greet(java.lang.String, java.lang.String, java.lang.String);
    Code:
       0: aload_0
       1: ldc           #9                  // String name
       3: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_1
       7: ldc           #17                 // String greeting
       9: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
      12: aload_2
      13: ldc           #19                 // String punct
      15: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
      18: new           #21                 // class java/lang/StringBuilder
      21: dup
      22: invokespecial #25                 // Method java/lang/StringBuilder."<init>":()V
      25: aload_1
      26: invokevirtual #29                 // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
      29: ldc           #31                 // String ,
      31: invokevirtual #29                 // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
      34: aload_0
      35: invokevirtual #29                 // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
      38: aload_2
      39: invokevirtual #29                 // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
      42: invokevirtual #35                 // Method java/lang/StringBuilder.toString:()Ljava/lang/String;
      45: areturn

  public static java.lang.String greet$default(java.lang.String, java.lang.String, java.lang.String, int, java.lang.Object);
    Code:
       0: iload_3
       1: iconst_2
       2: iand
       3: ifeq          9
       6: ldc           #40                 // String 안녕
       8: astore_1
       9: iload_3
      10: iconst_4
      11: iand
      12: ifeq          18
      15: ldc           #42                 // String !
      17: astore_2
      18: aload_0
      19: aload_1
      20: aload_2
      21: invokestatic  #44                 // Method greet:(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
      24: areturn

  public static final java.lang.String callIt();
    Code:
       0: ldc           #47                 // String 준
       2: aconst_null
       3: aconst_null
       4: bipush        6
       6: aconst_null
       7: invokestatic  #49                 // Method greet$default:(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;ILjava/lang/Object;)Ljava/lang/String;
      10: areturn

  public static final java.lang.String callAll();
    Code:
       0: ldc           #47                 // String 준
       2: ldc           #52                 // String 야
       4: ldc           #54                 // String ?
       6: invokestatic  #44                 // Method greet:(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
       9: areturn

  public static final java.lang.String callMiddle();
    Code:
       0: ldc           #47                 // String 준
       2: aconst_null
       3: ldc           #54                 // String ?
       5: iconst_2
       6: aconst_null
       7: invokestatic  #49                 // Method greet$default:(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;ILjava/lang/Object;)Ljava/lang/String;
      10: areturn
```

```text
   greet("준")                       mask = 6 = 0b110
                                              │││
                                              ││└─ 0번(name)   : 넘겼다
                                              │└── 1번(greeting): 생략 ★
                                              └─── 2번(punct)  : 생략 ★

   greet("준", punct = "?")          mask = 2 = 0b010
                                              │││
                                              ││└─ name    : 넘겼다
                                              │└── greeting: 생략 ★
                                              └─── punct   : 넘겼다
```

그림 해설:

- ★ **메서드는 딱 둘이다.** 진짜 `greet(String,String,String)` 와 합성 `greet$default(…, int, Object)`.\
  **생략 가능한 조합마다 오버로드를 만들지 않는다** — 그게 Java 의 방식이고 Kotlin 의 방식이 아니다.
- `$default` 안은 **`iand` 로 비트를 검사해 생략된 자리에만 기본값을 넣는 코드**다.\
  `iconst_2`(= 비트 1), `iconst_4`(= 비트 2)가 각각 `greeting`·`punct` 에 대응한다.
- 생략된 자리에는 호출부가 **`aconst_null`** 을 밀어 넣는다 — 값은 `$default` 가 채운다.
- ★ **인자를 다 넘기면(`callAll`) `$default` 를 아예 안 거친다.** 진짜 메서드를 직접 부른다.\
  **기본 인자를 선언해도 완전 호출에는 비용이 0** 이라는 뜻이다.
- 맨 끝의 `Object` 인자는 **마커**다. 여기서는 항상 `aconst_null` 이다.

비용 — 생략이 있을 때만 `$default` 한 겹(비교 몇 번). 완전 호출은 0.

### (2) ★ 파라미터가 33개가 되면 마스크가 **하나 더** 생긴다

**언제 쓰나** — "비트마스크가 `int` 하나면 32개까지 아닌가" 라고 물을 때.

파라미터가 32·33·65개인 함수를 만들어 전부 기본값을 주고 인자 없이 불렀다.

**출력** (`javap -s -p outbig/BigKt.class` — 디스크립터만 발췌)

```text
  public static int f32$default(int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, java.lang.Object);
    descriptor: (IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIILjava/lang/Object;)I

  public static int f33$default(int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, java.lang.Object);
    descriptor: (IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIILjava/lang/Object;)I

  public static int f65$default(int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, java.lang.Object);
    descriptor: (IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIILjava/lang/Object;)I
```

**출력** (`javap -c -p outbig/BigKt.class` — 호출부의 마스크만 발췌)

```text
      31: iconst_0
      32: iconst_m1
      33: aconst_null
      34: invokestatic  #109                // Method f32$default:(IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIILjava/lang/Object;)I
```

```text
      69: iconst_0
      70: iconst_m1
      71: iconst_1
      72: aconst_null
      73: invokestatic  #111                // Method f33$default:(IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIILjava/lang/Object;)I
```

```text
     141: iconst_0
     142: iconst_m1
     143: iconst_m1
     144: iconst_1
     145: aconst_null
     146: invokestatic  #113                // Method f65$default:(IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIILjava/lang/Object;)I
```

```text
   파라미터 32개 ──> I 가 33개  = 32 + 마스크 1개   마스크 = [-1]
   파라미터 33개 ──> I 가 35개  = 33 + 마스크 2개   마스크 = [-1, 1]
   파라미터 65개 ──> I 가 68개  = 65 + 마스크 3개   마스크 = [-1, -1, 1]

   -1 = 0b111…1 (32비트 전부 생략)
    1 = 0b000…1 (33번째 한 칸만 생략)
```

- ★ **마스크는 파라미터 32개마다 `int` 한 칸씩 붙는다.** 33개면 두 칸, 65개면 세 칸이다.
- `iconst_m1`(= -1)은 **그 32칸이 전부 생략됐다**는 뜻이고, 마지막 `iconst_1` 은 **남은 한 칸**이다.
- 그래서 `$default` 의 인자 수는 **파라미터 수 + `ceil(n/32)` + 1(마커)** 이다.

비용 — 마스크 `int` 하나가 늘 때마다 `iand` 검사 덩어리가 하나 는다. **파라미터가 33개인 함수를 쓰지 말라는 신호**로 읽으면 된다.

### (3) ★★ 기본값은 **호출할 때마다** 평가된다 — Python 과 반대다

**언제 쓰나** — 기본값에 `mutableListOf()` 나 `LocalDate.now()` 를 쓰려 할 때.

```kotlin
var counter = 0
fun nextId(): Int { counter++; return counter }
fun useDefault(id: Int = nextId()): Int = id

fun collect(x: Int, bag: MutableList<Int> = mutableListOf()): MutableList<Int> {
    bag.add(x)
    return bag
}
```

**출력** (`ex.kt`)

```text
=== 1. 기본 인자 평가 시점 ===
useDefault() = 1   counter=1
useDefault() = 2   counter=2
useDefault() = 3   counter=3
useDefault(99) = 99  counter=3   <- 넘기면 평가 자체를 안 한다
=== 2. 가변 기본값은 공유되나 ===
collect(1) = [1]
collect(2) = [2]
같은 리스트인가? false
```

```text
   Python (20번 주제)                 Kotlin
   +---------------------------+      +---------------------------+
   | def f(bag=[]):            |      | fun f(bag = mutableListOf())|
   | 기본값은 def 를 읽을 때    |      | 기본값은 $default 안의 코드 |
   | 한 번 만들어져 함수에 붙음 |      | -> 부를 때마다 새로 만든다  |
   +---------------------------+      +---------------------------+
      f(); f() 가 같은 리스트           f(); f() 가 다른 리스트 ★
```

- ★ **`useDefault()` 를 세 번 부르면 `1`·`2`·`3` 이다.** 기본값 식이 **매 호출마다** 실행된다.\
  (1)의 `$default` 바이트코드에서 기본값이 **메서드 본문 안**에 있던 것이 그 근거다.
- ★ **인자를 넘기면 기본값 식은 아예 안 돈다.** `useDefault(99)` 뒤에도 `counter` 가 3 그대로다.\
  `iand` 검사가 실패하면 `ldc`/호출을 건너뛴다.
- ★ **가변 기본값이 공유되지 않는다.** `collect(1)` 과 `collect(2)` 가 **다른 리스트**를 받았다 —\
  Python 의 대표적 함정이 **이 언어에는 없다.** 정본 대비는 [`../../../python/syntax/20-mutable-default-args/`](../../../python/syntax/20-mutable-default-args/).

**기본값은 왼쪽 파라미터를 볼 수 있다.**

```kotlin
fun rect(w: Int, h: Int = w, label: String = "${w}x$h"): String = label
```

**출력** (`ex.kt`)

```text
=== 3. 기본값이 왼쪽 파라미터를 본다 ===
rect(3)        = 3x3
rect(3, 4)     = 3x4
rect(3, label="L") = L
```

- **왼쪽에서 오른쪽으로** 채워지므로 `h` 의 기본값이 `w` 를, `label` 의 기본값이 `w`·`h` 를 볼 수 있다.
- 반대 방향은 안 된다 — 아직 채워지지 않은 칸이기 때문이다.

비용 — 기본값 식 그 자체. 넘기면 0.

### (4) 이름 붙인 인자 — 이름끼리는 순서를 바꿔도 되고, **되돌아가는 것만** 막힌다

**언제 쓰나** — `f(true, false, true)` 같은 호출을 읽을 수 있게 고칠 때.

```kotlin
fun f(a: Int, b: Int, c: Int): Int = a * 100 + b * 10 + c

fun ok1() = f(1, b = 2, c = 3)        // 위치 뒤에 이름
fun ok2() = f(a = 1, b = 2, c = 3)    // 전부 이름
fun ok3() = f(1, c = 3, b = 2)        // 이름끼리 순서 바꾸기
fun ok4() = f(b = 2, 1, c = 3)        // 이름 뒤에 위치 인자
fun bad1() = f(c = 3, 1, 2)
```

**출력** (`kotlinc bad1.kt`)

```text
bad1.kt:6:13: error: no value passed for parameter 'a'.
fun ok4() = f(b = 2, 1, c = 3)        // 이름 뒤에 위치 인자 — ?
            ^
bad1.kt:6:22: error: mixing named and positional arguments is not allowed unless the order of the arguments matches the order of the parameters.
fun ok4() = f(b = 2, 1, c = 3)        // 이름 뒤에 위치 인자 — ?
                     ^
bad1.kt:7:14: error: no value passed for parameter 'a'.
fun bad1() = f(c = 3, 1, 2)           // 이름 뒤에 위치 인자 둘 — ?
             ^
bad1.kt:7:14: error: no value passed for parameter 'b'.
fun bad1() = f(c = 3, 1, 2)           // 이름 뒤에 위치 인자 둘 — ?
             ^
bad1.kt:7:23: error: mixing named and positional arguments is not allowed unless the order of the arguments matches the order of the parameters.
fun bad1() = f(c = 3, 1, 2)           // 이름 뒤에 위치 인자 둘 — ?
                      ^
bad1.kt:7:26: error: mixing named and positional arguments is not allowed unless the order of the arguments matches the order of the parameters.
fun bad1() = f(c = 3, 1, 2)           // 이름 뒤에 위치 인자 둘 — ?
                         ^
```

```text
   f(1, b = 2, c = 3)   O   위치 → 이름 순
   f(a = 1, b = 2, c = 3)   O   전부 이름
   f(1, c = 3, b = 2)   O   ★ 이름끼리는 순서를 바꿔도 된다
   f(b = 2, 1, c = 3)   X   위치 인자가 「뒤로 돌아간다」
   f(c = 3, 1, 2)       X   같은 이유

   규칙: 위치 인자는 자기 자리에 있어야 한다. 이름은 자유다.
```

- ★ **`f(1, c = 3, b = 2)` 는 통과한다.** 이름이 붙은 것끼리는 **순서가 의미를 갖지 않는다.**
- 막히는 것은 **위치 인자가 자기 자리를 벗어날 때**다.\
  메시지가 그 조건을 그대로 말한다 — `unless the order of the arguments matches the order of the parameters`.
- 에러가 **두 겹으로** 나오는 것도 읽을 거리다 — `no value passed for parameter 'a'` 는\
  컴파일러가 **위치 인자를 어디에도 못 꽂아서** 나온 부수 효과다.

**출력** (`ex.kt`)

```text
=== 4. 이름 붙인 인자 — 순서를 바꾼다 ===
rect(h = 9, w = 2) = 2x9
```

비용 — 0. 이름은 바이트코드에 안 남는다(호출 순서로 다 풀린다).

### (5) 단일 표현식 함수 — 반환 타입이 **추론되는 자리와 안 되는 자리**

**언제 쓰나** — `= expr` 형태를 어디까지 쓸 수 있는지 정할 때.

```kotlin
fun sq(x: Int) = x * x          // 추론 O
fun name() = "준"                // 추론 O
fun fact(n: Int) = if (n <= 1) 1 else n * fact(n - 1)   // 재귀
fun blockNoType(x: Int) { return x }                     // 블록 몸통
```

**출력** (`kotlinc bad2.kt`)

```text
bad2.kt:1:43: error: type checking has run into a recursive problem. Easiest workaround: specify the types of your declarations explicitly.
fun fact(n: Int) = if (n <= 1) 1 else n * fact(n - 1)   // 재귀 + 타입 추론
                                          ^^^^^^^^^^^
bad2.kt:3:34: error: return type mismatch: expected 'Unit', actual 'Int'.
fun blockNoType(x: Int) { return x }                     // 블록 몸통에서 값 반환
                                 ^
```

```text
   fun sq(x: Int) = x * x            타입을 안 적으면 식에서 추론한다
   fun fact(n: Int) = … fact(…)      ★ 자기를 부르면 추론이 순환한다 -> 에러
   fun fact(n: Int): Int = …         타입을 적으면 풀린다

   fun f(x: Int) { return x }        ★ 블록 몸통은 타입을 안 적으면 Unit 이다
   fun f(x: Int): Int { return x }   적어야 값을 반환할 수 있다
```

- ★ **재귀 함수는 단일 표현식이어도 반환 타입을 적어야 한다.** 추론이 자기를 물어 순환한다.\
  메시지가 고치는 법까지 담고 있다(`specify the types of your declarations explicitly`).
- ★ **블록 몸통(`{ }`)은 타입을 안 적으면 `Unit` 이다.** `= expr` 형태만 추론된다.\
  이 둘을 헷갈리면 `return type mismatch: expected 'Unit'` 을 보게 된다.
- **공개 API 에는 타입을 적는 것이 관용**이다 — 구현을 고쳤을 때 **반환 타입이 조용히 바뀌는 것**을 막는다.

비용 — 0. 형태의 문제다.

### (6) `Unit` 은 **타입**이고 **싱글턴 객체**다

**언제 쓰나** — Java 의 `void` 와 같은 것인지 물을 때.

**출력** (`ex.kt`)

```text
=== 6. Unit ===
nothingBack() 의 값 = kotlin.Unit
u = kotlin.Unit,  u::class = kotlin.Unit
Unit === Unit 인가(싱글턴)? true
```

- **`Unit` 은 값이 하나뿐인 타입**이고 그 값의 이름도 `Unit` 이다.\
  `println(nothingBack())` 이 **`kotlin.Unit` 을 찍는다** — Java 의 `void` 는 찍을 값이 없다.
- `val u: Unit = Unit` 처럼 **변수에 담을 수 있다.** 제네릭 자리에도 들어간다(`(Int) -> Unit`).
- 바이트코드에서는 **반환 타입이 `void` 로 내려가는 경우가 많다** — 하지만 그건 구현이고,\
  **타입 시스템 안에서 `Unit` 은 다른 타입들과 똑같은 타입**이다.
- 값이 아예 없는 타입은 `Nothing` 이다 — 정본은 목록의 **34번 주제**.

비용 — 0(대개 `void` 로 접힌다).

### (7) ★★ Java 에서 보면 기본 인자가 **사라진다** — `@JvmOverloads` 가 그것을 되살린다

**언제 쓰나** — Kotlin 라이브러리를 Java 에서 쓰게 할 때.

```kotlin
fun greet(name: String, greeting: String = "안녕", punct: String = "!"): String =
    "$greeting, $name$punct"

@JvmOverloads
fun hello(name: String, greeting: String = "안녕", punct: String = "!"): String =
    "$greeting, $name$punct"
```

**출력** (`javap -s -p outk/KKt.class`)

```text
Compiled from "K.kt"
public final class KKt {
  public static final java.lang.String greet(java.lang.String, java.lang.String, java.lang.String);
    descriptor: (Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

  public static java.lang.String greet$default(java.lang.String, java.lang.String, java.lang.String, int, java.lang.Object);
    descriptor: (Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;ILjava/lang/Object;)Ljava/lang/String;

  public static final java.lang.String hello(java.lang.String, java.lang.String, java.lang.String);
    descriptor: (Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

  public static java.lang.String hello$default(java.lang.String, java.lang.String, java.lang.String, int, java.lang.Object);
    descriptor: (Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;ILjava/lang/Object;)Ljava/lang/String;

  public static final java.lang.String hello(java.lang.String, java.lang.String);
    descriptor: (Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

  public static final java.lang.String hello(java.lang.String);
    descriptor: (Ljava/lang/String;)Ljava/lang/String;
}
```

**출력** (`javac -cp outk J.java` → `java -cp "outk:kotlin-stdlib.jar" J`)

```text
안녕, 준!
야, 준!
야, 준?
야, 준?
```

**출력** (`javac -cp outk J2.java` — `@JvmOverloads` 없는 `greet` 를 한 인자로 부른 것)

```text
J2.java:3: error: method greet in class KKt cannot be applied to given types;
        System.out.println(KKt.greet("준"));
                              ^
  required: String,String,String
  found:    String
  reason: actual and formal argument lists differ in length
1 error
```

```text
   Java 에서 보이는 표면

   greet 쪽                        hello 쪽 (@JvmOverloads)
   +-------------------------+     +---------------------------+
   | greet(String,String,String) |  | hello(String,String,String)|
   | greet$default(...)  ← 숨김 ★|  | hello$default(...)  ← 숨김 |
   +-------------------------+     | hello(String,String)   ← + |
     인자 셋을 다 넘겨야 한다        | hello(String)          ← + |
                                   +---------------------------+
```

- ★ **`$default` 는 `ACC_SYNTHETIC` 이라 Java 에서 안 보인다.**

```text
  public static java.lang.String greet$default(java.lang.String, java.lang.String, java.lang.String, int, java.lang.Object);
    flags: (0x1009) ACC_PUBLIC, ACC_STATIC, ACC_SYNTHETIC
```

- 그래서 Java 는 **인자 세 개짜리 하나만** 볼 수 있고, 덜 넘기면 `cannot be applied to given types` 다.
- `@JvmOverloads` 를 붙이면 **오른쪽부터 하나씩 떼어 낸 오버로드**가 생긴다 — `hello(String,String)`·`hello(String)`.\
  **왼쪽부터가 아니라 오른쪽부터**다. `hello(String, String)` 은 `name`·`greeting` 을 받는다.
- 그 오버로드들의 본문은 **다시 `$default` 를 부른다.**

```text
  public static final java.lang.String hello(java.lang.String);
    Code:
       0: aload_0
       1: ldc           #9                  // String name
       3: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_0
       7: aconst_null
       8: aconst_null
       9: bipush        6
      11: aconst_null
      12: invokestatic  #52                 // Method hello$default:(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;ILjava/lang/Object;)Ljava/lang/String;
      15: areturn
```

- **마스크가 `bipush 6` 으로 (1)의 `callIt` 과 똑같다.** `@JvmOverloads` 는 **Java 용 얇은 껍데기**를 더한 것이다.
- ★ **이름 붙인 인자는 Java 에 아예 없다.** `@JvmOverloads` 로도 못 살린다 —\
  Java 쪽은 **오른쪽에서부터 연속으로 생략**하는 것만 된다. `punct` 만 넘기는 호출은 Java 에서 불가능하다.
- 상호운용 애너테이션 **전체**의 정본은 목록의 **39번 주제**다.

비용 — 오버로드 수만큼 메서드가 는다(`n` 개 기본값이면 `n` 개).

### (8) 기본 인자가 **오버로딩을 대신한다** — Java 사슬과 나란히

**언제 쓰나** — Java 코드를 Kotlin 으로 옮길 때 가장 먼저 접히는 자리.

```text
   Java (손으로 쓰는 사슬)                    Kotlin
   +-------------------------------------+   +------------------------------------+
   | String greet(String n) {            |   | fun greet(                         |
   |   return greet(n, "안녕");          |   |     name: String,                  |
   | }                                   |   |     greeting: String = "안녕",     |
   | String greet(String n, String g) {  |   |     punct: String = "!"            |
   |   return greet(n, g, "!");          |   | ): String = "$greeting, $name$punct"|
   | }                                   |   +------------------------------------+
   | String greet(String n, String g,    |     소스 1개 · 바이트코드 2개
   |              String p) { … }        |
   +-------------------------------------+
     소스 3개 · 바이트코드 3개
```

- Java 쪽에서 이 사슬이 **왜 위험한지**(오버로드 해소 규칙·`null` 인자의 모호성·`vararg` 와의 충돌)는\
  [`../../../java/syntax/08-method-declaration-overloading/`](../../../java/syntax/08-method-declaration-overloading/)가 정본이다.
- Kotlin 쪽에서 사라지는 것 —\
  ① **오버로드 해소 규칙 자체가 안 걸린다**(메서드가 하나다).\
  ② **중간 인자만 바꿔 부를 수 있다**(`greet("준", punct = "?")` — Java 사슬로는 불가능하다).\
  ③ **기본값이 한 곳에만 적힌다**(사슬에서는 중간 메서드마다 흩어진다).
- 대신 생기는 것 —\
  ① **Java 에서 볼 때 표면이 좁아진다**((7)).\
  ② **파라미터 순서가 API 계약이 된다** — 이름 붙인 인자를 쓰는 호출자는 **이름 변경에도 깨진다.**

비용 — (1)의 `$default` 한 겹.

## 문법 — 형태와 규칙

```kotlin
// 1) 기본 인자
fun greet(name: String, greeting: String = "안녕", punct: String = "!") = "$greeting, $name$punct"
fun rect(w: Int, h: Int = w)                 // 왼쪽 파라미터를 볼 수 있다
fun now(t: Long = System.currentTimeMillis()) // 호출할 때마다 평가된다

// 2) 이름 붙인 인자
greet("준", punct = "?")       // 중간만 바꾸기
greet(punct = "?", name = "준", greeting = "야")   // 전부 이름이면 순서 자유
greet("준", c = 3, b = 2)      // 이름끼리는 순서 자유
// greet(greeting = "야", "준") // X — 위치 인자가 자기 자리를 벗어난다

// 3) 단일 표현식 함수
fun sq(x: Int) = x * x
fun fact(n: Int): Int = if (n <= 1) 1 else n * fact(n - 1)   // 재귀는 타입 명시
fun log(m: String) { println(m) }                            // 블록 몸통 = Unit

// 4) Unit
fun f(): Unit { }
fun g(): Unit = println("x")
val u: Unit = Unit

// 5) Java 에게 보여 주기
@JvmOverloads
fun hello(name: String, greeting: String = "안녕") = "$greeting, $name"
```

규칙 불릿.

- **기본값은 호출 시점에 평가된다.** 인자를 넘기면 **평가 자체를 안 한다.**
- **기본값은 왼쪽 파라미터를 볼 수 있다.** 오른쪽은 못 본다.
- **위치 인자는 자기 자리에 있어야 한다.** 이름 붙인 것끼리는 순서가 자유다.
- **`= expr` 는 반환 타입이 추론되고, `{ }` 는 안 적으면 `Unit` 이다.**
- **재귀 함수는 반환 타입을 적어야 한다.**
- **Java 는 기본 인자를 못 본다.** `@JvmOverloads` 가 오른쪽부터 떼어 낸 오버로드를 만들어 준다.

## 어디서 틀리나

| 틀리는 형태 | 무슨 일이 일어나나 | 고치는 법 |
|---|---|---|
| 기본값을 "한 번만 평가" 라고 믿음 | **매 호출마다 평가된다.** `nextId()` 가 계속 증가한다 | 의도한 것인지 확인. 고정값이면 `val` 상수로 |
| Python 처럼 가변 기본값을 피함 | Kotlin 에서는 **공유되지 않는다** — 피할 이유가 없다 | [`../../../python/syntax/20-mutable-default-args/`](../../../python/syntax/20-mutable-default-args/)와 대비해 기억한다 |
| `f(b = 2, 1)` | `mixing named and positional arguments is not allowed…` | 위치 인자를 앞으로 옮긴다 |
| 재귀 함수를 `= expr` 로만 적음 | `type checking has run into a recursive problem.` | 반환 타입을 적는다 |
| `fun f(x: Int) { return x }` | `return type mismatch: expected 'Unit'` | `: Int` 를 적거나 `= x` 로 바꾼다 |
| 공개 API 를 `= expr` 로만 적음 | 구현을 고치면 **반환 타입이 조용히 바뀐다** | 공개 표면에는 타입을 명시한다 |
| Java 에서 기본 인자를 생략 | `cannot be applied to given types` | `@JvmOverloads` 를 붙인다 |
| `@JvmOverloads` 면 중간 인자도 될 줄 앎 | **오른쪽부터 연속 생략만** 된다 | Java 쪽은 전부 넘기거나 래퍼를 만든다 |
| 파라미터 이름을 리팩터링 | 이름 붙인 인자로 부르던 **호출자가 깨진다** | 공개 API 의 파라미터 이름도 계약이다 |
| 파라미터가 33개 넘음 | `$default` 의 마스크가 하나 더 붙는다 | 그 전에 데이터 클래스로 묶는다 |
| `Unit` 을 `void` 로 생각 | `Unit` 은 **값이 있는 타입**이다. 제네릭에 들어간다 | `Nothing` 과 구분한다(목록의 34번 주제) |

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 | 근거 |
|---|---|---|
| 기본값이 **호출 시점**에 평가된다 | **언어** | 명세 + 실행(`1`·`2`·`3`) |
| 인자를 넘기면 기본값 식이 안 돈다 | **언어** | 명세 + 실행(`counter` 가 안 늘었다) |
| 기본값이 왼쪽 파라미터를 본다 | **언어** | 명세 + 실행 |
| 위치 인자가 자기 자리에 있어야 한다 | **언어** | 컴파일 에러 |
| 이름끼리 순서 자유 | **언어** | 컴파일 통과 |
| `= expr` 의 반환 타입 추론 | **언어** | 컴파일 통과·에러 |
| 재귀 함수에 타입이 필요한 것 | **언어** | 컴파일 에러 |
| 블록 몸통의 기본 반환 타입이 `Unit` | **언어** | 컴파일 에러 |
| `Unit` 이 값 하나짜리 타입인 것 | **언어** | 실행(`kotlin.Unit`) |
| **`이름$default` 라는 메서드 이름** | **구현** | `javap` |
| **비트마스크 `int` 와 그 비트 배치** | **구현** | `javap`(`bipush 6` = 0b110) |
| **파라미터 32개마다 마스크 1개** | **구현** | `javap` 디스크립터 세기 |
| **끝의 `Object` 마커 인자** | **구현** | `javap` |
| **완전 호출이 `$default` 를 안 거치는 것** | **구현(최적화)** | `javap` |
| **`$default` 가 `ACC_SYNTHETIC` 인 것** | **구현** | `javap -v` |
| **`@JvmOverloads` 가 오른쪽부터 떼는 것** | **언어(애너테이션 계약)** | `javap -s` + Java 컴파일 통과 |
| **그 오버로드가 다시 `$default` 를 부르는 것** | **구현** | `javap -c` |

★ **가장 중요한 구분 한 줄** — **"기본 인자는 오버로드를 만들어 준다" 는 틀렸다.**\
만들어지는 것은 **오버로드가 아니라 `$default` 한 개**이고, **진짜 오버로드는 `@JvmOverloads` 를 붙여야만** 생긴다.\
그래서 **Kotlin 안에서는 표면이 하나, Java 에서는 표면이 하나 또는 n+1개**가 된다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 인자 대부분이 흔한 값일 때 | 기본 인자 | 사슬이 안 생긴다 |
| `Boolean` 인자가 둘 이상일 때 | 이름 붙인 인자 강제 | 호출부가 읽힌다 |
| 중간 인자만 바꿔야 할 때 | 이름 붙인 인자 | Java 사슬로는 불가능한 일이다 |
| 한 줄로 끝나는 함수 | `= expr` | `return` 과 중괄호가 사라진다 |
| 공개 API | `= expr` + **반환 타입 명시** | 타입이 조용히 바뀌는 것을 막는다 |
| 재귀 함수 | 반환 타입 명시 | 추론이 순환한다 |
| Java 에서도 쓸 라이브러리 | `@JvmOverloads` | 안 붙이면 전부 넘겨야 한다 |
| 파라미터가 5개를 넘어갈 때 | 데이터 클래스로 묶기 | 기본값으로 버티면 33개까지 간다 |
| 오버로드로 **타입이 다른** 입력을 받을 때 | 진짜 오버로드 | 기본 인자는 **개수**만 줄인다 |

판단 규칙 두 줄.

- **기본 인자가 줄이는 것은 「인자 개수」이지 「타입 종류」가 아니다.** 타입이 다르면 여전히 오버로드다.
- **Java 에서 부를 API 라면 `@JvmOverloads` 를 붙일지 선언 시점에 정한다.** 나중에 붙이면 표면이 늘어난다.

## 핵심 문장

- 기본 인자는 오버로드가 아니라 **`이름$default` 합성 메서드 하나 + 비트마스크 `int`** 로 컴파일된다.
- **`bipush 6` = `0b110`** 은 "1번·2번 인자가 생략됐다" 는 뜻이다. 생략된 자리에는 `aconst_null` 이 들어간다.
- ★ **인자를 다 넘기면 `$default` 를 안 거친다** — 진짜 메서드를 직접 부른다.
- ★ **파라미터 32개마다 마스크 `int` 가 한 칸씩 붙는다.** 33개면 둘, 65개면 셋이다.
- ★ **기본값은 호출할 때마다 평가된다.** Python 의 "선언 시점 한 번" 과 **반대**이고, 가변 기본값이 **공유되지 않는다.**
- **인자를 넘기면 기본값 식은 아예 안 돈다.**
- 기본값은 **왼쪽 파라미터를 볼 수 있다**(`h: Int = w`).
- 이름 붙인 인자끼리는 순서가 자유이고, **위치 인자가 자기 자리를 벗어날 때만** 막힌다.
- `= expr` 는 타입이 추론되지만 **재귀 함수는 명시해야** 하고, **블록 몸통은 안 적으면 `Unit`** 이다.
- ★ **Java 에서는 기본 인자가 안 보인다** — `$default` 가 `ACC_SYNTHETIC` 이기 때문이다.\
  `@JvmOverloads` 가 **오른쪽부터** 떼어 낸 오버로드를 만들어 주지만 **이름 붙인 인자는 못 살린다.**

## 관련 자료

- [`../README.md`](../README.md) — Kotlin 문법·API 주제 목록(이 주제는 08번)
- [`../../../java/syntax/08-method-declaration-overloading/`](../../../java/syntax/08-method-declaration-overloading/) — **Java 쪽 정본.**\
  거기는 **오버로드 해소 규칙과 가변 인자**가 정본이고, 여기는 **그 사슬을 없앤 문법과 그 바이트코드**다
- [`../../../python/syntax/20-mutable-default-args/`](../../../python/syntax/20-mutable-default-args/) — **기본값 평가 시점이 반대인 언어.**\
  Python 은 선언 시점에 한 번, Kotlin 은 호출마다 — 이 대비가 (3)의 값어치다
- [09번 주제](../09-varargs-spread-local-and-infix-functions/) — **`vararg`·spread·로컬 함수·`infix` 의 정본.** 이 문서의 직접 후속이다
- [02번 주제](../02-string-templates-and-raw-strings/) — 바이트코드에 보이는 `StringBuilder` 가 왜 거기 있는지의 정본
- [03번 주제](../03-null-safe-types/) — `checkNotNullParameter` 의 정본
- [목록의 **10번 주제**](../10-lambdas-and-higher-order-functions/)(람다와 고차 함수) — 함수 타입 파라미터·마지막 인자 람다의 정본
- [목록의 **11번 주제**](../11-inline-functions/)(인라인 함수) — 인라인이 기본 인자와 만나는 자리
- [목록의 **13번 주제**](../13-extension-functions-and-properties/)(확장 함수) — 수신자가 앞에 붙는 또 다른 선언 형태
- 목록의 **15번 주제**(클래스 선언 — 주 생성자) — **생성자에도 같은 `$default` 가 만들어진다**
- 목록의 **22번 주제**(`data class`) — `copy()` 가 기본 인자로 만들어지는 대표 사례
- 목록의 **34번 주제**(예외·`Nothing` 타입) — `Unit` 과 `Nothing` 의 구분
- 목록의 **39번 주제**(Java 상호운용 애너테이션) — `@JvmOverloads` **전체**의 정본. 여기는 기본 인자의 짝으로만 다뤘다

## 용어 풀이

- **기본 인자(default argument)** — 파라미터에 적어 두는 기본값. 호출자가 안 넘기면 그 값이 쓰인다.
- **이름 붙인 인자(named argument)** — 호출부에서 `이름 = 값` 으로 넘기는 것. 순서에 안 매인다.
- **단일 표현식 함수** — 몸통이 `= 식` 한 줄인 함수. 반환 타입이 추론된다.
- **`$default` 메서드** — 컴파일러가 만드는 합성 메서드. 원래 파라미터 + 비트마스크 + 마커를 받는다.
- **비트마스크(bitmask)** — 생략 여부를 비트로 담은 정수. `1 shl i` 가 켜져 있으면 i번 파라미터가 생략된 것이다.
- **`ACC_SYNTHETIC`** — "컴파일러가 만든 것이라 소스에 대응이 없다" 는 클래스 파일 플래그. Java 컴파일러가 무시한다.
- **마커 인자** — `$default` 의 마지막 `Object` 파라미터. 보통 `null` 이다.
- **`@JvmOverloads`** — Java 를 위해 **오른쪽부터 인자를 뗀 오버로드**를 만들어 달라는 애너테이션.
- **`Unit`** — 값이 하나뿐인 타입. Java 의 `void` 와 달리 **값이 있고 타입 자리에 들어간다.**
- **`Nothing`** — 값이 하나도 없는 타입. `throw`·`return` 의 타입이다.
- **오버로드 해소(overload resolution)** — 같은 이름의 메서드 여럿 중 어느 것을 부를지 정하는 규칙. Kotlin 의 기본 인자는 이 규칙을 **안 거친다.**

---

## 더 들어가면

- **생성자에도 같은 것이 생긴다.** `class C(val a: Int, val b: Int = 0)` 을 찍어 봤다.

```text
Compiled from "ctor.kt"
public final class C {
  private final int a;
    descriptor: I
  private final int b;
    descriptor: I
  public C(int, int);
    descriptor: (II)V

  public C(int, int, int, kotlin.jvm.internal.DefaultConstructorMarker);
    descriptor: (IIILkotlin/jvm/internal/DefaultConstructorMarker;)V

  public final int getA();
    descriptor: ()I

  public final int getB();
    descriptor: ()I
}
```

  ★ **`$default` 대신 「마스크가 붙은 생성자 오버로드」가 생긴다** — 이름을 못 바꾸니 시그니처로 가른 것이다.\
  마커 타입도 `Object` 가 아니라 **`DefaultConstructorMarker`** 다. 클래스 선언의 정본은 목록의 **15번 주제**.
- `@JvmOverloads` 가 **오른쪽부터** 떼는 이유는 Java 가 **연속 접미사 생략**만 표현할 수 있기 때문이다.\
  `greet(name, punct)` 같은 건너뛴 조합은 **시그니처가 `(String, String)` 으로 겹쳐** 만들 수가 없다.
- 마스크가 **`-1`** 로 보이는 것(2번)은 32비트가 전부 1이라서다. `javap` 는 `iconst_m1` 로 표시한다.
- 기본값이 **다른 파라미터를 참조**할 때, `$default` 안에서의 채우는 순서가 그대로 왼→오른쪽이다.\
  그래서 오른쪽을 참조하면 거부된다 — 던져서 확인했다.

```text
fwd.kt:1:16: error: parameter 'b' is uninitialized here.
fun f(a: Int = b, b: Int = 1): Int = a + b
               ^
```

  메시지가 **`uninitialized`** 다 — "그런 이름이 없다" 가 아니라 **"아직 안 채워졌다"** 라고 말한다.
- 이 문서에서 **성능은 재지 않았다.** "완전 호출은 `$default` 를 안 거친다" 는 **`javap` 로 본 호출 대상**이지 시간이 아니다.
