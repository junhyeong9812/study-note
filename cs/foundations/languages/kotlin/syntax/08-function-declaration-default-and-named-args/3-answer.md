# kotlin/syntax/08 — 함수 선언: 기본 인자·이름 붙인 인자·단일 표현식 함수 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javap` 에서 실제로 얻었다.\
> 8번의 Java 호출은 `javac -cp outk` 로 컴파일해 **같은 클래스패스에서 실제로 섞어 돌린 것**이다.\
> 역어셈블은 **기본 `-jvm-target`(1.8 · `major version: 52`)** 이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★ **둘**이다 — 진짜 `greet` 하나와 합성 `greet$default` 하나

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
```

**왜 그런가**

- ★ **오버로드가 셋 생기지 않는다.** 기본값이 둘이어도 메서드는 **둘**이다.
- 합성 메서드의 추가 파라미터 둘 —\
  **`int` 는 비트마스크**(어느 자리가 생략됐나), **`Object` 는 마커**(이 호출에서는 항상 `null`).
- 기본값 문자열 `"안녕"`·`"!"` 는 **`$default` 안**에 있다. 진짜 `greet` 는 기본값을 모른다.\
  그래서 기본값을 고치면 **`$default` 만 바뀐다.**
- `iand` 로 비트를 검사해 **생략된 자리에만** 값을 채운다 — `iconst_2`(비트 1)·`iconst_4`(비트 2).
- 맨 앞의 `checkNotNullParameter` 는 기본 인자와 무관하다([03번](../03-null-safe-types/)).\
  본문의 `StringBuilder` 는 **기본 타깃 1.8** 때문이다([02번](../02-string-templates-and-raw-strings/)).

### 2. ★★ `callAll` 만 직접 부른다 · 마스크는 `6` 과 `2`

**출력** (`javap -c -p out/IcodeKt.class`)

```text
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

**왜 그런가**

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

- ★ **`callAll` 은 `$default` 를 안 거친다** — `invokestatic greet:(…)` 로 **진짜 메서드를 직접** 부른다.
- `callIt` 은 `bipush 6`(= `0b110`), `callMiddle` 은 `iconst_2`(= `0b010`).\
  **비트 i 가 켜져 있으면 i번 파라미터가 생략됐다**는 뜻이다.
- 생략된 자리에는 **`aconst_null`** 이 밀려 들어간다 — 그 값은 어차피 `$default` 가 덮어쓴다.
- ★ 비용에 대해 말해 주는 것 — **기본 인자를 선언해도 완전 호출에는 비용이 0** 이다.\
  생략한 호출만 `$default` 한 겹(비트 검사 몇 번)을 더 지난다.

### 3. ★ 33 · 35 · 68 — 마스크는 **32개마다 한 칸**

**출력** (`javap -s -p outbig/BigKt.class`)

```text
  public static int f32$default(int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, java.lang.Object);
    descriptor: (IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIILjava/lang/Object;)I

  public static int f33$default(int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, java.lang.Object);
    descriptor: (IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIILjava/lang/Object;)I

  public static int f65$default(int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, java.lang.Object);
    descriptor: (IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIILjava/lang/Object;)I
```

**출력** (`javap -c -p outbig/BigKt.class` — `callBig` 의 마스크 부분만)

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

**왜 그런가**

```text
   파라미터 32개 ──> I 가 33개  = 32 + 마스크 1개   마스크 = [-1]
   파라미터 33개 ──> I 가 35개  = 33 + 마스크 2개   마스크 = [-1, 1]
   파라미터 65개 ──> I 가 68개  = 65 + 마스크 3개   마스크 = [-1, -1, 1]

   -1 = 0b111…1 (그 32칸이 전부 생략됐다)
    1 = 0b000…1 (남은 한 칸만 생략됐다)
```

- **마스크 `int` 가 파라미터 32개마다 한 칸씩** 붙는다.
- `iconst_m1`(= `-1`)은 **32비트가 전부 1** 이라 "이 묶음 32개가 전부 생략됐다" 는 뜻이다.
- `$default` 의 전체 인자 수 = **파라미터 수 + `ceil(n / 32)` + 1(마커)**.\
  32 → 32+1+1 = 34개(`I` 33 + `Object` 1) · 33 → 33+2+1 = 36개 · 65 → 65+3+1 = 69개.
- 실무 읽기 — **파라미터가 33개를 넘어가면 바이트코드가 한 겹 더 두꺼워진다.** 그 전에 타입으로 묶으라는 신호다.

### 4. ★★ `1` `2` `3` `99` / `counter=3` / **다른 리스트**

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

**왜 그런가**

```text
   Python (20번 주제)                 Kotlin
   +---------------------------+      +-----------------------------+
   | def f(bag=[]):            |      | fun f(bag = mutableListOf())|
   | 기본값은 def 를 읽을 때    |      | 기본값은 $default 안의 코드 |
   | 한 번 만들어져 함수에 붙음 |      | -> 부를 때마다 새로 만든다  |
   +---------------------------+      +-----------------------------+
      f(); f() 가 같은 리스트            f(); f() 가 다른 리스트 ★
```

- ★ **기본값 식은 호출마다 실행된다** — `1`·`2`·`3`.\
  근거는 1번의 바이트코드다. 기본값이 **`$default` 의 본문 안**에 있으니 부를 때마다 그 코드가 돈다.
- ★ **`useDefault(99)` 는 `counter` 를 안 늘렸다.** `iand` 검사가 실패하면 기본값 코드를 **건너뛴다.**\
  "안 넘기면 쓰는 값" 이 아니라 **"안 넘길 때만 만드는 값"** 이다.
- ★ **`a === b` 가 `false` 다.** 가변 기본값이 공유되지 않는다 —\
  Python 의 대표적 함정이 **이 언어에는 없다.** 정본 대비는 [`../../../python/syntax/20-mutable-default-args/`](../../../python/syntax/20-mutable-default-args/).
- 같은 코드를 Python 으로 옮기면 `f(); f()` 가 **같은 리스트를 계속 키운다.** 거기가 갈리는 유일한 자리다.

곁들여 — **기본값은 왼쪽 파라미터를 볼 수 있다.**

```text
=== 3. 기본값이 왼쪽 파라미터를 본다 ===
rect(3)        = 3x3
rect(3, 4)     = 3x4
rect(3, label="L") = L
```

오른쪽을 보면 거부된다.

```text
fwd.kt:1:16: error: parameter 'b' is uninitialized here.
fun f(a: Int = b, b: Int = 1): Int = a + b
               ^
```

### 5. ★ `[A]`·`[B]`·`[C]` 는 통과, `[D]`·`[E]` 는 에러

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

**왜 그런가**

```text
   f(1, b = 2, c = 3)   O   위치 → 이름 순
   f(a = 1, b = 2, c = 3)   O   전부 이름
   f(1, c = 3, b = 2)   O   ★ 이름끼리는 순서를 바꿔도 된다
   f(b = 2, 1, c = 3)   X   위치 인자가 「뒤로 돌아간다」
   f(c = 3, 1, 2)       X   같은 이유
```

- ★ **`[C]` 가 통과한다.** 이름이 붙은 것끼리는 **순서가 의미를 갖지 않는다.**
- 규칙 한 문장 — **위치 인자는 자기 자리를 지켜야 하고, 이름 붙인 인자는 자유다.**\
  에러 메시지가 그 조건을 그대로 말한다(`unless the order of the arguments matches the order of the parameters`).
- 에러가 **두 종류**로 나오는 이유 — `mixing named and positional…` 이 본질이고,\
  `no value passed for parameter 'a'` 는 **위치 인자를 어디에도 못 꽂아서 생긴 부수 효과**다.\
  `[E]` 는 못 꽂은 인자가 둘이라 그 줄이 **둘** 나왔다.
- 전부 이름이면 순서가 자유다 — 실행으로도 확인된다.

```text
=== 4. 이름 붙인 인자 — 순서를 바꾼다 ===
rect(h = 9, w = 2) = 2x9
```

### 6. ★ **둘 다 안 된다** — 이유가 서로 다르다

**출력** (`kotlinc bad2.kt`)

```text
bad2.kt:1:43: error: type checking has run into a recursive problem. Easiest workaround: specify the types of your declarations explicitly.
fun fact(n: Int) = if (n <= 1) 1 else n * fact(n - 1)   // 재귀 + 타입 추론
                                          ^^^^^^^^^^^
bad2.kt:3:34: error: return type mismatch: expected 'Unit', actual 'Int'.
fun blockNoType(x: Int) { return x }                     // 블록 몸통에서 값 반환
                                 ^
```

**왜 그런가**

```text
   fun sq(x: Int) = x * x            타입을 안 적으면 식에서 추론한다
   fun fact(n: Int) = … fact(…)      ★ 자기를 부르면 추론이 순환한다 -> 에러
   fun fact(n: Int): Int = …         타입을 적으면 풀린다

   fun f(x: Int) { return x }        ★ 블록 몸통은 타입을 안 적으면 Unit 이다
   fun f(x: Int): Int { return x }   적어야 값을 반환할 수 있다
```

- `[A]` — 반환 타입을 알려면 본문을 봐야 하는데 본문이 **자기 자신을 부른다.** 추론이 순환한다.\
  ★ **메시지에 고치는 법이 들어 있다** — `Easiest workaround: specify the types of your declarations explicitly.`
- `[B]` — **블록 몸통은 타입을 안 적으면 `Unit` 이다.** `= expr` 형태에서만 추론이 일어난다.\
  그래서 `expected 'Unit', actual 'Int'` 가 나온다.
- 둘이 다른 점 — **`= expr` 는 "이 식의 타입이 반환 타입" 이고, `{ }` 는 "명시 안 하면 `Unit`"** 이다.\
  형태가 타입 규칙을 바꾼다.
- 그래서 **공개 API 에는 반환 타입을 적는 것이 관용**이다. 구현을 고쳤을 때 타입이 조용히 바뀌는 것을 막는다.

### 7. 다르다 — `Unit` 은 **값이 있는 타입**이다

**출력** (`ex.kt`)

```text
=== 6. Unit ===
nothingBack() 의 값 = kotlin.Unit
u = kotlin.Unit,  u::class = kotlin.Unit
Unit === Unit 인가(싱글턴)? true
```

**왜 그런가**

| | `Unit` | `Nothing` | Java `void` |
|---|---|---|---|
| 값의 개수 | **1개**(그 값의 이름도 `Unit`) | **0개** | 값이라는 개념이 없다 |
| 변수에 담기 | `val u: Unit = Unit` — 된다 | 담을 값이 없다 | 불가 |
| 함수가 정상 반환 | 한다 | **절대 안 한다**(`throw`·무한 루프) | 한다 |
| 제네릭 인자 | `(Int) -> Unit` — 된다 | `List<Nothing>` — 된다 | 불가(`Void` 로 우회) |

- `println(f())` 가 **`kotlin.Unit` 을 찍는다.** Java 의 `void` 는 찍을 값이 없어 컴파일부터 안 된다.
- `Unit === Unit` 이 `true` 다 — **싱글턴 `object`** 이기 때문이다.
- 함수 타입 `(Int) -> Unit` 이 성립하는 이유가 여기 있다 —\
  함수 타입은 **반환 타입 자리에 타입을 요구**하는데 `void` 는 타입이 아니고 `Unit` 은 타입이다.\
  **"모든 함수가 값을 반환한다" 를 유지하려고 만든 타입**이다.
- `Nothing` 의 정본은 목록의 **34번 주제**다.

### 8. ★★ Java 는 `greet` 를 **세 인자로만** 부를 수 있다

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

**출력** (`javac -cp outk J2.java`)

```text
J2.java:3: error: method greet in class KKt cannot be applied to given types;
        System.out.println(KKt.greet("준"));
                              ^
  required: String,String,String
  found:    String
  reason: actual and formal argument lists differ in length
1 error
```

**출력** (`javap -v -p outk/KKt.class` — 플래그)

```text
  public static final java.lang.String greet(java.lang.String, java.lang.String, java.lang.String);
    flags: (0x0019) ACC_PUBLIC, ACC_STATIC, ACC_FINAL
  public static java.lang.String greet$default(java.lang.String, java.lang.String, java.lang.String, int, java.lang.Object);
    flags: (0x1009) ACC_PUBLIC, ACC_STATIC, ACC_SYNTHETIC
  public static final java.lang.String hello(java.lang.String, java.lang.String, java.lang.String);
    flags: (0x0019) ACC_PUBLIC, ACC_STATIC, ACC_FINAL
  public static java.lang.String hello$default(java.lang.String, java.lang.String, java.lang.String, int, java.lang.Object);
    flags: (0x1009) ACC_PUBLIC, ACC_STATIC, ACC_SYNTHETIC
  public static final java.lang.String hello(java.lang.String, java.lang.String);
    flags: (0x0019) ACC_PUBLIC, ACC_STATIC, ACC_FINAL
  public static final java.lang.String hello(java.lang.String);
    flags: (0x0019) ACC_PUBLIC, ACC_STATIC, ACC_FINAL
```

**왜 그런가**

```text
   Java 에서 보이는 표면

   greet 쪽                          hello 쪽 (@JvmOverloads)
   +----------------------------+    +----------------------------+
   | greet(String,String,String)|    | hello(String,String,String)|
   | greet$default(...) ← 숨김 ★|    | hello$default(...) ← 숨김  |
   +----------------------------+    | hello(String,String)   ← + |
     인자 셋을 다 넘겨야 한다         | hello(String)          ← + |
                                     +----------------------------+
```

- `KKt.greet("준")` 은 **안 된다** — `cannot be applied to given types` / `argument lists differ in length`.
- ★ **`$default` 가 안 보이는 이유는 `ACC_SYNTHETIC` 플래그**다. `javac` 는 이 플래그가 붙은 멤버를 후보에서 뺀다.\
  `javap -p` 에는 보이지만 Java 소스에서는 못 부른다.
- ★ **`@JvmOverloads` 는 오른쪽부터 뗀다.** `hello(String,String)` 은 `name`·`greeting` 을 받는다 —\
  **`name`·`punct` 조합은 안 만들어진다.**
- 그 오버로드의 본문은 **다시 `$default` 를 부른다.**

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

- 마스크가 **`bipush 6`** 으로 2번의 `callIt` 과 똑같다. `@JvmOverloads` 는 **Java 용 얇은 껍데기**다.

### 9. `punct` 만 바꿔 부를 수 없다 — **이름 붙인 인자는 Java 에 없다**

**왜 그런가**

```text
   Kotlin        greet("준", punct = "?")        O
   Java          KKt.greet("준", ?, "?")         X  — 중간을 비울 문법이 없다
                 KKt.greet("준", "안녕", "?")    O  — 기본값을 손으로 베껴 적어야 한다

   @JvmOverloads 가 만들 수 있는 조합
     hello(name, greeting, punct)
     hello(name, greeting)         ← 오른쪽 하나 뗌
     hello(name)                   ← 오른쪽 둘 뗌
   만들 수 없는 조합
     hello(name, punct)            ★ 시그니처가 (String,String) 으로 겹친다
```

- Java 에는 **이름 붙인 인자라는 문법이 없다.** 호출은 **위치로만** 맺어진다.
- `@JvmOverloads` 로도 못 만드는 이유는 **시그니처 충돌**이다 —\
  `hello(name, greeting)` 과 `hello(name, punct)` 는 둘 다 `(String, String)` 이라 **같은 메서드**가 된다.\
  그래서 **연속 접미사 생략만** 표현할 수 있다.
- Kotlin 쪽에서는 `greet("준", punct = "?")` 한 줄이다(2번의 `callMiddle`).
- ★ **Java 에 내놓을 때 잃는 것** — **"중간 인자만 바꾸는 호출"** 이다.\
  Java 호출자는 기본값을 **손으로 베껴 적어야** 하고, 그 값이 나중에 바뀌면 **조용히 어긋난다.**

### 10. 사라지는 것 셋 · 새로 계약이 되는 것 둘

**왜 그런가**

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

**사라지는 것 셋**

1. **오버로드 해소 규칙 자체가 안 걸린다** — 후보가 하나뿐이다.\
   Java 에서 `null` 인자가 어느 오버로드로 갈지 모호해지는 문제가 통째로 없다\
   (그 규칙의 정본은 [`../../../java/syntax/08-method-declaration-overloading/`](../../../java/syntax/08-method-declaration-overloading/)).
2. **중간 인자만 바꾸는 호출이 가능해진다** — 사슬로는 만들 수 없는 조합이다(9번).
3. **기본값이 한 곳에만 적힌다** — 사슬에서는 중간 메서드마다 흩어져 **서로 어긋날 수 있다.**

**새로 계약이 되는 것 둘**

1. **파라미터 이름**이 공개 계약이 된다 — 이름 붙인 인자로 부르던 호출자는 **이름만 바꿔도 깨진다.**\
   Java 사슬에서는 이름이 계약이 아니었다(위치만 계약이다).
2. **파라미터 순서**가 더 굳어진다 — 순서를 바꾸면 **위치로 부르던 호출자와 기본값 참조**가 동시에 깨진다.

**줄이지 못하는 오버로드** — **타입이 다른 입력을 받는 오버로드**다.\
기본 인자는 **개수**만 줄인다. `f(Int)` 와 `f(String)` 은 여전히 오버로드 둘이어야 한다.

### 11. 다른 주제와 잇기

- **`vararg`·spread·로컬 함수·`infix` → [09번 주제](../09-varargs-spread-local-and-infix-functions/)** 가 정본이다.\
  특히 `vararg` 와 기본 인자가 **한 선언에 같이 오는 경우**의 규칙이 거기 있다.
- **생성자의 기본 인자 → 마커 타입이 `Object` 가 아니라 `kotlin.jvm.internal.DefaultConstructorMarker`** 다.

```text
  public C(int, int);
    descriptor: (II)V

  public C(int, int, int, kotlin.jvm.internal.DefaultConstructorMarker);
    descriptor: (IIILkotlin/jvm/internal/DefaultConstructorMarker;)V
```

  생성자는 이름을 못 바꾸니 `$default` 대신 **시그니처로 가른** 것이다.\
  클래스 선언의 정본은 [목록의 **15번 주제**](../15-class-declaration-constructors-and-init/).
- **상호운용 애너테이션 전체 → 목록의 39번 주제**(`@JvmStatic`/`@JvmOverloads`/`@JvmName`/`@JvmField`/`@Throws`)가 정본이다.\
  여기서는 `@JvmOverloads` 만 기본 인자의 짝으로 다뤘다.
- **`data class` 의 `copy()`** 가 기본 인자의 대표 사례다 — 모든 파라미터에 **현재 값이 기본값**으로 들어간다.\
  그래서 `copy(name = "새 이름")` 한 줄이 된다. 정본은 [목록의 **22번 주제**](../22-data-class-generated-members/).

---

## 실행 검증

**환경**

```text
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
openjdk version "21.0.5" 2024-10-15 LTS
OpenJDK Runtime Environment Temurin-21.0.5+11 (build 21.0.5+11-LTS)
OpenJDK 64-Bit Server VM Temurin-21.0.5+11 (build 21.0.5+11-LTS, mixed mode, sharing)
```

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `icode.kt` | `$default` 의 존재·비트마스크·완전 호출이 직접 부르는 것 | `kotlinc` → `javap -c -p out/IcodeKt.class` |
| `big.kt` | 파라미터 32·33·65개에서 마스크가 1·2·3개인 것 | 생성 스크립트 → `kotlinc` → `javap -s -p`·`javap -c -p` |
| `ex.kt` | 기본값 평가 시점 4회·가변 기본값 비공유·왼쪽 참조·이름 순서 바꾸기·`Unit` | `kotlinc` → `java` |
| `bad1.kt` | 이름/위치 섞기 규칙 (통과 3 · 에러 2) | `kotlinc` (에러 6줄) |
| `bad2.kt` | 재귀 추론 순환 · 블록 몸통의 기본 반환 타입 | `kotlinc` (에러 2건) |
| `fwd.kt` | 기본값이 **오른쪽** 파라미터를 보면 거부되는 것 | `kotlinc` (에러 1건) |
| `ctor.kt` | 생성자의 `DefaultConstructorMarker` | `kotlinc` → `javap -s -p outc/C.class` |
| `K.kt` + `J.java` | `@JvmOverloads` 유무의 Java 표면 · 실제 호출 4건 | `kotlinc` → `javac -cp outk` → `java` |
| `K.kt` + `J2.java` | `@JvmOverloads` 없는 함수를 Java 에서 덜 부르면 나는 에러 | `javac -cp outk` (컴파일 실패가 결과) |
| `K.kt` (플래그) | `$default` 가 `ACC_SYNTHETIC` 인 것 | `javap -v -p outk/KKt.class` |

**구현 의존 항목** — `이름$default` 라는 메서드 이름, 비트마스크의 비트 배치와 `-1` 표현,
32개마다 마스크가 느는 것, 끝의 `Object`/`DefaultConstructorMarker` 마커,
완전 호출이 `$default` 를 건너뛰는 것, `ACC_SYNTHETIC` 플래그,
`@JvmOverloads` 오버로드가 다시 `$default` 를 부르는 것 — 전부 **이 컴파일러 버전의 산출물**이다.\
반면 "기본값은 호출 시점 평가" · "인자를 넘기면 평가 안 함" · "왼쪽 파라미터만 참조" ·
"위치 인자는 자기 자리" · "`= expr` 추론 / `{ }` 는 `Unit`" · "`Unit` 은 값이 하나인 타입" 은
**언어 규칙**이라 타깃·버전과 무관하다.

**양쪽을 다 돌린 것** — 8번은 **Kotlin 이 만든 클래스를 Java 소스에서 실제로 컴파일하고 실행했다.**
Kotlin 안에서만 보면 `greet` 와 `hello` 는 **똑같이 생겼다** — 차이는 Java 쪽에서만 드러난다.

**★ 던져 봤더니 예상과 달랐던 것 — 세 건**

1. **완전 호출이 `$default` 를 안 거친다.** "모든 호출이 `$default` 를 지난다" 고 예상했는데\
   `callAll` 은 진짜 메서드를 **직접** 불렀다. 기본 인자 선언의 비용이 호출 형태에 따라 갈린다.
2. **파라미터 33개에서 마스크가 정말 하나 더 늘었다** — 그리고 **65개에서 셋**이 됐다.\
   경계가 32/64 라는 것을 디스크립터의 `I` 개수를 세어 확인했다.
3. **가변 기본값이 공유되지 않는다.** Python 의 함정을 기대하고 던졌는데 `a === b` 가 `false` 였다 —\
   **기본값이 `$default` 본문 안의 코드라서** 호출마다 새로 만들어진다.

**안 잰 것** — **성능은 한 번도 측정하지 않았다.**
"완전 호출은 `$default` 를 안 거친다" 는 `javap` 로 본 **호출 대상**이지 시간이 아니고,
"마스크가 늘면 검사가 는다" 도 **명령의 개수**까지다.
