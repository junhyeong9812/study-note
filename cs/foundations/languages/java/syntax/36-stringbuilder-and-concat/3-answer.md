# java/syntax/36 — `StringBuilder` 와 문자열 연결이 컴파일되는 방식 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **Temurin JDK 21.0.5 에서 실제로 돌려 얻은 것**이다.\
> 바이트코드는 `javap -c`·`javap -v` 출력을, JDK 소스는 `lib/src.zip` 의 실파일을, JLS는 원문을 그대로 옮겼다.\
> 실행 파일명은 전부 `Ex.java` 로 고정했다.\
> 바이트코드 형태는 17.0.13 · 25.0.1 에서도 같았고, 측정은 세 JDK 모두에서 따로 돌렸다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 세 메서드의 바이트코드를 예측하라

**출력** (`javap -c -p Ex.class`, JDK 21.0.5 — 출력 그대로)

```text
  static java.lang.String constFold();
    Code:
       0: ldc           #7                  // String hello
       2: areturn

  static java.lang.String twoVars(java.lang.String, java.lang.String);
    Code:
       0: aload_0
       1: aload_1
       2: invokedynamic #9,  0              // InvokeDynamic #0:makeConcatWithConstants:(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
       7: areturn

  static java.lang.String loopBuilder(java.lang.String[]);
    Code:
       0: new           #15                 // class java/lang/StringBuilder
       3: dup
       4: invokespecial #17                 // Method java/lang/StringBuilder."<init>":()V
       7: astore_1
       8: aload_0
       9: astore_2
      10: aload_2
      11: arraylength
      12: istore_3
      13: iconst_0
      14: istore        4
      16: iload         4
      18: iload_3
      19: if_icmpge     41
      22: aload_2
      23: iload         4
      25: aaload
      26: astore        5
      28: aload_1
      29: aload         5
      31: invokevirtual #18                 // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
      34: pop
      35: iinc          4, 1
      38: goto          16
      41: aload_1
      42: invokevirtual #22                 // Method java/lang/StringBuilder.toString:()Ljava/lang/String;
      45: areturn
```

**세 메서드의 명령**

| 메서드 | 핵심 명령 | 뜻 |
|---|---|---|
| `constFold` | `ldc #7` | 이미 합쳐진 상수를 꺼낸다 |
| `twoVars` | `invokedynamic makeConcatWithConstants` | 런타임에 정해지는 연결 호출 **한 번** |
| `loopBuilder` | `new StringBuilder` **1회**(루프 밖) + 루프 안 `append` | 내가 쓴 그대로다 |

**`constFold` 에 `+` 의 흔적이 남는가**

- **안 남는다.** 명령이 `ldc` 와 `areturn` 둘뿐이다.
- 상수 식이라 **컴파일 타임에 `"hello"` 로 접혔다.**
- 그래서 가독성을 위해 긴 상수 문자열을 `+` 로 여러 줄에 쪼개 써도 **런타임 비용이 0**이다.

**`twoVars` 에 `StringBuilder` 가 나오는가**

- **안 나온다.** 이것이 이 주제에서 가장 자주 틀리는 자리다.
- JDK 9(JEP 280)부터 `+` 는 `invokedynamic` 으로 컴파일된다.

**호출 대상과 확인 방법**

`javap -v` 의 `BootstrapMethods` 를 보면 된다(출력 그대로).

```text
BootstrapMethods:
  0: #73 REF_invokeStatic java/lang/invoke/StringConcatFactory.makeConcatWithConstants:(Ljava/lang/invoke/MethodHandles$Lookup;Ljava/lang/String;Ljava/lang/invoke/MethodType;Ljava/lang/String;[Ljava/lang/Object;)Ljava/lang/invoke/CallSite;
    Method arguments:
      #71 \u0001\u0001
```

- 대상은 **`java.lang.invoke.StringConcatFactory.makeConcatWithConstants`** 다.
- `javap -c` 는 `invokedynamic #9` 까지만 보여 주고, **무엇을 부르는지는 `-v` 로만 보인다.**
- `Method arguments` 의 `\u0001\u0001` 이 **연결 레시피**다 — `\u0001` 하나가 인자 하나의 자리다.\
  인자가 둘이니 자리표시자도 둘이다. 리터럴이 섞이면 그 글자가 레시피에 그대로 들어간다.

> **`invokedynamic`** — "무엇을 부를지 런타임에 정한다"고 클래스 파일에 적어 두는 JVM 명령.\
> 예: 첫 실행 때 부트스트랩 메서드가 불려 실제 호출 대상을 정하고, 이후에는 그것이 재사용된다.

### 2. ★ 루프 안 `+=` 는 무엇으로 컴파일되는가

**출력** (`javap -c -p Ex.class`, JDK 21.0.5 — 출력 그대로)

```text
  static java.lang.String loopConcat(java.lang.String[]);
    Code:
       0: ldc           #13                 // String
       2: astore_1
       3: aload_0
       4: astore_2
       5: aload_2
       6: arraylength
       7: istore_3
       8: iconst_0
       9: istore        4
      11: iload         4
      13: iload_3
      14: if_icmpge     38
      17: aload_2
      18: iload         4
      20: aaload
      21: astore        5
      23: aload_1
      24: aload         5
      26: invokedynamic #9,  0              // InvokeDynamic #0:makeConcatWithConstants:(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
      31: astore_1
      32: iinc          4, 1
      35: goto          11
      38: aload_1
      39: areturn
```

**루프 몸통 안에 `new StringBuilder` 가 몇 번 나오는가**

- **0번.** 클래스 파일 어디에도 `StringBuilder` 가 없다.
- 「반복마다 `StringBuilder` 를 새로 만든다」는 **JDK 9 이전의 설명**이고, 지금 컴파일러는 그렇게 하지 않는다.

**실제로 나오는 명령**

```text
루프 몸통 (오프셋 17~35)

  17: aload_2 / 18: iload 4 / 20: aaload / 21: astore 5     이번 원소 p 를 꺼낸다
  23: aload_1                                                지금까지의 s
  24: aload 5                                                이번 조각 p
  26: invokedynamic makeConcatWithConstants                  s + p  <- 여기서 새 String 이 생긴다
  31: astore_1                                               s 를 그 새 String 으로 교체
  32: iinc 4, 1 / 35: goto 11                                다음 반복
```

- **`invokedynamic` 하나**가 반복마다 실행된다.

**느린 진짜 이유**

- 도구가 `StringBuilder` 든 `invokedynamic` 이든 **결과 `String` 은 반복마다 새로 만들어진다.**
- `String` 이 불변이므로([35번](../35-string/)) 기존 내용을 **전부 복사**할 수밖에 없다.
- n번 반복하면 복사 총량이 1+2+...+n = n(n+1)/2 — **O(n²)** 이다(손계산).
- 즉 원인은 **컴파일 방식이 아니라 자료구조의 성질**이다. 그래서 JDK를 올려도 안 고쳐진다.

**Java 8 시절 바이트코드를 재현하는 방법**

`javac -XDstringConcat=inline` 으로 컴파일하면 옛 형태가 나온다(출력 그대로).

```text
      23: new           #9                  // class java/lang/StringBuilder
      26: dup
      27: invokespecial #11                 // Method java/lang/StringBuilder."<init>":()V
      30: aload_1
      31: invokevirtual #12                 // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
      34: aload         5
      36: invokevirtual #12                 // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
      39: invokevirtual #16                 // Method java/lang/StringBuilder.toString:()Ljava/lang/String;
      42: astore_1
      43: iinc          4, 1
      46: goto          11
```

```text
  JDK 9+ 기본                              -XDstringConcat=inline
  +-----------------------------+         +-----------------------------+
  | 루프 몸통:                  |         | 루프 몸통:                  |
  |   invokedynamic  x1         |         |   new StringBuilder         |
  |                             |         |   append x2                 |
  |                             |         |   toString                  |
  +-----------------------------+         +-----------------------------+
   명령 수가 적다                            옛 교과서의 그림 그대로

     두 형태 모두 "결과 String 을 반복마다 새로 만든다" -> 둘 다 O(n^2)
```

- `-XD...` 는 **문서화되지 않은 javac 내부 옵션**이다. 학습·확인용으로만 쓴다.
- 이 옵션으로 옛 설명이 **어디서 왔는지**까지 눈으로 볼 수 있다.

**17·21·25에서 같은가**

- **같다.** 세 JDK 모두 루프 안이 `invokedynamic #9 makeConcatWithConstants` 였다.
- 차이는 `javap` 출력의 들여쓰기뿐이다(25가 두 칸 더 들여쓴다).

### 3. n 을 2배로 늘리면 시간은 몇 배가 되는가

**출력** (JDK 21.0.5, 이 머신 — 측정 조건은 아래)

```text
       n |   s += (ms) |   builder (ms) |       배수 |     s+= 증가율
    1000 |       0.056 |          0.002 |       26 |           -
    2000 |       0.249 |          0.004 |       63 |       4.42배
    4000 |       0.954 |          0.006 |      147 |       3.84배
    8000 |       3.290 |          0.012 |      279 |       3.45배
   16000 |      13.382 |          0.028 |      484 |       4.07배
   32000 |      55.281 |          0.049 |     1118 |       4.13배
   64000 |     241.935 |          0.132 |     1836 |       4.38배
```

세 JDK의 「증가율」:

| n | 17.0.13 | 21.0.5 | 25.0.1 |
|---|---|---|---|
| 1000 → 2000 | 3.72배 | 4.42배 | 3.95배 |
| 2000 → 4000 | 4.07배 | 3.84배 | 4.79배 |
| 4000 → 8000 | 3.88배 | 3.45배 | 3.65배 |
| 8000 → 16000 | 3.84배 | 4.07배 | 4.06배 |
| 16000 → 32000 | 4.76배 | 4.13배 | 5.09배 |
| 32000 → 64000 | 4.79배 | 4.38배 | 4.01배 |

**`s += "x"` 의 배수**

- **약 4배.** 세 JDK·여섯 구간 모두 3.4~5.1배 사이였다.

**`StringBuilder` 의 배수**

- **약 2배.** 0.002 → 0.004 → 0.006 → 0.012 → 0.028 → 0.049 → 0.132 (JDK 21).
- 작은 n 에서는 측정 잡음이 크다(0.002ms 는 2마이크로초다) — 큰 n 쪽이 더 믿을 만하다.

**복잡도 기호**

- `s += x` -> **O(n²)**. 2배마다 4배 = 2² 배.
- `sb.append(x)` -> **O(n)** (상환). 2배마다 2배.

**"1836배 느리다"가 불완전한 이유**

```text
   n        배수
  1000        26
  4000       147
 16000       484
 64000      1836      <- 배수 자체가 n 에 비례해 커진다
```

- **배수는 상수가 아니다.** n 에 비례해 커지므로 "몇 배"라는 표현은 **그 n 에서만** 참이다.
- 남길 결론은 배수가 아니라 **"n² 로 늘어난다"** 여야 한다.
- 같은 이유로 **밀리초 절댓값도 이 기계에서만** 의미가 있다 — 다른 기계에서 재현되지 않는다.

**워밍업을 안 하면**

- JIT가 아직 인터프리터로 돌리는 구간이 측정에 섞여 **첫 n 이 과대평가**된다.
- 그러면 증가율이 4배보다 작게 나와 O(n²)가 흐려진다.
- 이 측정은 두 메서드를 각각 `n=2000` 으로 **200회** 먼저 돌렸다.

**측정 조건(그대로)**

| 항목 | 값 |
|---|---|
| 기계 | 13th Gen Intel Core i7-13700HX · 24 논리 코어 · Linux |
| JDK | Temurin 17.0.13 · 21.0.5 · 25.0.1 |
| 방법 | `System.nanoTime` 으로 감싸고 같은 n 을 5회 반복해 **최솟값** |
| 워밍업 | 두 메서드를 각각 n=2000 으로 200회 |
| 검증 | 결과 길이 != n 이면 `AssertionError` — 연산이 최적화로 사라지지 않았음을 보장 |
| 한계 | **JMH가 아니다.** GC·배치 효과를 통제하지 않았고 단일 실행이다 |

> **JMH** — OpenJDK의 마이크로벤치마크 도구. 워밍업·포크·데드코드 제거 방지를 자동으로 해 준다.\
> 예: 이 문서의 측정은 JMH를 쓰지 않았으므로 **기울기는 믿고 절댓값은 참고만** 한다.

### 4. `StringBuilder` 의 용량

**출력** (JDK 21.0.5 — 17·25 동일)

```text
new StringBuilder()          capacity = 16, length = 0
length 17 에서 capacity 16 -> 34
length 35 에서 capacity 34 -> 70
length 71 에서 capacity 70 -> 142
length 143 에서 capacity 142 -> 286
length 287 에서 capacity 286 -> 574

new StringBuilder("abc")     capacity = 19
new StringBuilder(100)       capacity = 100

빈 것 capacity         = 16
한글 한 자 넣은 뒤     = 16 (length 1)
한글 20자 넣은 뒤      = 34 (length 20)
ASCII 20자 넣은 뒤     = 34 (length 20)
```

**기본 용량**

- **16.**

**증가 규칙**

- **`새 용량 = 기존 × 2 + 2`.**
- 16 → 34 → 70 → 142 → 286 → 574 가 전부 이 식과 맞는다(손계산으로 대조).
- JDK 21 소스가 `+2` 의 출처다.

```java
// JDK 21.0.5  java.base/java/lang/AbstractStringBuilder.java  259~268행 — 실제 소스 그대로
private int newCapacity(int minCapacity) {
    int oldLength = value.length;
    int newLength = minCapacity << coder;
    int growth = newLength - oldLength;
    int length = ArraysSupport.newLength(oldLength, growth, oldLength + (2 << coder));
    if (length == Integer.MAX_VALUE) {
        throw new OutOfMemoryError("Required length exceeds implementation limit");
    }
    return length >> coder;
}
```

- 세 번째 인자 `oldLength + (2 << coder)` 가 **선호 증가량**이다 — LATIN1(`coder=0`)이면 `oldLength + 2`.\
  기존에 그만큼을 더하니 결과가 `2배 + 2` 가 된다.

**`new StringBuilder("abc")` 의 용량이 3이 아닌 이유**

- **`문자열 길이 + 16`** 으로 잡기 때문이다. `3 + 16 = 19`.
- 초기 문자열 뒤에 **더 붙일 것을 예상한** 설계다.
- `new StringBuilder(100)` 은 정확히 100이다 — 숫자를 주면 그것이 용량이다.\
  **같은 생성자 이름인데 `"3"` 과 `3` 의 의미가 완전히 다르다.** `new StringBuilder('a')` 같은 실수가 여기서 나온다.

**`capacity()` 의 단위**

- **글자 수**다. 바이트 수가 아니다.
- 확인: ASCII 20자와 **한글 20자의 `capacity` 가 둘 다 34**로 같았다.\
  한글은 내부적으로 글자당 2바이트(UTF16)로 저장되므로 배열 크기는 68바이트인데, `capacity()` 는 34를 돌려준다.
- 소스가 그 변환을 한다: `public int capacity() { return value.length >> coder; }`\
  `coder` 가 1(UTF16)이면 바이트 수를 2로 나눈다.

### 5. `null` 이 섞이면

**출력**

```text
String.valueOf((Object) null) = null
String.valueOf((char[]) null) -> NPE
"x" + null 참조               = xnull
sb.append((String) null)      = [null] length=4
join 에 null 원소가 섞이면      = a,null
```

**다섯 줄**

| 식 | 결과 |
|---|---|
| `"x" + s` (`s` 가 `null`) | **`"xnull"`** |
| `sb.append((String) null)` 뒤 `sb.length()` | **4** |
| `String.join(",", ["a", null])` | **`"a,null"`** |
| `String.valueOf((Object) null)` | **`"null"`** |
| `String.valueOf((char[]) null)` | **`NullPointerException`** |

**왜 마지막 줄만 다른가**

```text
String.valueOf(Object obj)              String.valueOf(char[] data)
  -> obj == null ? "null" : ...           -> new String(data)  (data 를 읽는다)
     null 을 검사한다                        null 검사가 없다 -> NPE
```

- **오버로드가 다르게 뽑힌 것**이다. `(char[]) null` 캐스트가 `char[]` 오버로드를 고른다.
- `Object` 판은 `null` 을 문자열 `"null"` 로 바꾸도록 정의돼 있고, `char[]` 판은 배열 내용을 읽어야 해서 NPE가 난다.
- 캐스트 하나로 **같은 이름의 메서드가 다른 계약**을 갖게 되는 자리다.

**조용한 실패인 이유**

```text
  사용자 이름이 null 인 행 하나                그대로 조립해 저장하면

  name = null                                  CSV:  1,null,2026-09-21
  csv = id + "," + name + "," + date           DB :  name 컬럼에 'null' 네 글자
                                               로그:  user=null
```

- **예외도 경고도 없다.** `"null"` 이라는 **글자 네 개**가 데이터에 들어간다.
- 나중에 진짜 `NULL` 인 행과 `'null'` 문자열인 행이 섞여 **구분이 불가능**해진다.
- 되돌리려면 어느 행이 언제 들어갔는지를 알아야 하는데 그 정보가 없다.
- 방어는 조립 시점이 아니라 **값이 들어오는 경계**에서 한다([**60번 주제**](../60-null-handling/)).\
  조립 시점에 막으려면 `Objects.toString(x, "")` 또는 `Objects.requireNonNull`.

### 6. 반복과 서식의 경계

**출력**

```text
"ab".repeat(3)   = ababab
"ab".repeat(0)   = []
"ab".repeat(0) == "" ? true
"ab".repeat(-1)  -> java.lang.IllegalArgumentException: count is negative: -1

String.format("%05.2f", 3.14159)      = 03.14
String.format("%,d", 1234567)         = 1,234,567
"%s".formatted("x")                   = x!
String.format("%d", "문자열") -> java.util.IllegalFormatConversionException: d != java.lang.String
```

**다섯 식**

| 식 | 결과 |
|---|---|
| `"ab".repeat(0)` | **빈 문자열** |
| `"ab".repeat(0) == ""` | **true** |
| `"ab".repeat(-1)` | `IllegalArgumentException: count is negative: -1` |
| `String.format("%d", "문자열")` | `IllegalFormatConversionException: d != java.lang.String` |
| `String.format("%,d", 1234567)` | **`"1,234,567"`** |

**`repeat(0) == ""` 를 의존해도 되는가**

- **안 된다.**
- 이것은 구현이 빈 결과에 상수 풀의 `""` 를 그대로 돌려주는 **최적화**다.
- 명세가 보장하는 것은 **내용**이지 **동일성**이 아니다.\
  [35번](../35-string/)의 `substring(0) == this` 와 같은 부류의 함정이다.
- 판단 규칙은 하나다 — **`String` 에 `==` 를 쓰지 않는다.**

**`String.format` 의 타입 오류가 컴파일 타임에 잡히는가**

- **안 잡힌다.** 인자가 `Object...` 라 컴파일러가 서식 문자열을 해석하지 않는다.
- 런타임에 `IllegalFormatConversionException` 이 난다 — **`RuntimeException` 이라 안 잡아도 컴파일된다.**
- 메시지 `d != java.lang.String` 은 "`%d` 자리에 `String` 이 왔다"는 뜻이다.\
  왼쪽이 **서식 문자**, 오른쪽이 **실제로 온 타입**이다.
- 그래서 서식 문자열은 **테스트로만 검증된다.** 정적 분석 도구(`-Xlint` 는 못 잡는다)나 IDE 검사에 기댄다.

### 7. 잇는 세 가지 방법

**출력**

```text
String.join(", ", "a","b","c")      = a, b, c
String.join("-", List.of("a","b"))   = a-b
String.join(",", List.of())          = []
join 에 null 원소가 섞이면            = a,null
Collectors.joining                   = [a, b, c]
```

**언제 쓰는가**

| 방법 | 언제 | 특징 |
|---|---|---|
| `String.join(sep, ...)` | 이미 컬렉션·배열이 있을 때 | 가장 짧다. 접두·접미는 못 붙인다 |
| `Collectors.joining(sep, pre, suf)` | 스트림 파이프라인의 끝 | 접두·접미까지 한 번에 |
| `StringBuilder` | **조건 분기가 섞인 조립** | 구분자를 직접 관리해야 한다 |

- 구분자만 필요하면 앞의 둘을 쓴다 — **마지막 구분자를 지우는 코드가 필요 없다.**
- "값이 있을 때만 붙인다" 같은 분기가 있으면 `StringBuilder` 나 `StringJoiner` 를 직접 쓴다.

**`String.join(",", List.of())`**

- **빈 문자열**이다. 예외가 아니다(실행으로 확인).
- `join` 에 `null` **원소**가 있으면 `"null"` 글자가 된다.\
  단 구분자나 컬렉션 자체가 `null` 이면 NPE다. *(그 경우는 안 돌려 봤다.)*

**`Collectors.joining` 의 내부**

```java
// JDK 21.0.5  java.base/java/util/stream/Collectors.java  370~377행 — 실제 소스 그대로
public static Collector<CharSequence, ?, String> joining(CharSequence delimiter,
                                                         CharSequence prefix,
                                                         CharSequence suffix) {
    return new CollectorImpl<>(
            () -> new StringJoiner(delimiter, prefix, suffix),
            StringJoiner::add, StringJoiner::merge,
            StringJoiner::toString, CH_NOID);
}
```

- **`StringJoiner`** 다. `StringBuilder` 가 아니다.

**`StringBuilder` 와 어떻게 다른가**

```java
// JDK 21.0.5  java.base/java/util/StringJoiner.java  76·79·82행 — 실제 소스 그대로
private String[] elts;
/** The number of string components added so far. */
private int size;
/** Total length in chars so far, excluding prefix and suffix. */
private int len;
```

- `StringJoiner` 는 조각을 **`String[]` 에 모아 두고 길이만 누적**하다가 마지막에 한 번에 합친다.
- `StringBuilder` 는 **글자를 바로 배열에 쓴다.**
- 공통점은 **"매번 전체를 복사하지 않는다"** 는 것이고, 그래서 둘 다 O(n)이다.
- `merge` 가 있는 것은 **병렬 스트림에서 부분 결과를 합치기 위해서**다 —\
  `StringBuilder` 로는 그 계약을 만들기 어렵다([**49번 주제**](../49-parallel-streams/)).

### 8. 명세는 무엇을 보장하는가

**JLS가 `StringBuilder` 로 컴파일된다고 말하는가**

- **말하지 않는다.** 명세는 **결과**만 정하고 **방법**은 열어 둔다.

**원문 인용** — JLS SE 21 §15.18.1.

> The `String` object is newly created (§12.5) unless the expression is a constant expression (§15.29).
>
> An implementation **may** choose to perform conversion and concatenation in one step to avoid creating
> and then discarding an intermediate `String` object. To increase the performance of repeated string
> concatenation, a Java compiler **may** use the `StringBuffer` class or a similar technique to reduce
> the number of intermediate `String` objects that are created by evaluation of an expression.

- **"may"** 가 두 번 나온다 — 해도 되고 안 해도 된다.
- 명세가 적은 클래스 이름은 `StringBuffer` 다. `StringBuilder` 는 Java 5에 들어왔는데 이 문장은 안 바뀌었다.\
  명세가 구현을 **예시로만** 들었기 때문에 바꿀 필요가 없었던 것이다.

**그래서 "`+` 는 `StringBuilder` 가 된다"는 무엇이었나**

```text
  명세가 정한 것                        javac 가 고른 것
  +---------------------------+        +---------------------------+
  | 결과 String 의 내용        |        | Java 8까지: StringBuilder |
  | 상수 식이면 새로 안 만듦   |        | JDK 9부터: invokedynamic  |
  | 왼쪽부터 결합              |        |                           |
  +---------------------------+        +---------------------------+
   버전이 올라도 안 바뀐다               버전이 올라 실제로 바뀌었다
```

- **그 시절 javac의 구현 선택**이었다. 명세가 아니었다.
- JDK 9가 다른 선택을 했고 **명세는 한 글자도 안 바꿔도 됐다.**
- 교훈: "컴파일러가 X로 바꾼다"는 설명을 들으면 **`javap` 를 떠서 지금도 그런지 확인**한다.

**재현되는 수치와 안 되는 수치**

| 재현된다 | 재현 안 된다 |
|---|---|
| 증가율 ≈ 4배 (O(n²)) — 세 JDK 모두 | 밀리초 절댓값 |
| `StringBuilder` 가 O(n) | "1836배" 같은 배수 (n 의존) |
| 용량 16 → 34 → 70 (같은 JDK 계열) | 다른 JVM 구현의 용량 정책 |
| 바이트코드 형태 (JDK 9+) | Java 8 이하의 바이트코드 |

### 9. 어디를 고치고 어디를 두나

**셋 중 고쳐야 할 것**

| 코드 | 판정 | 왜 |
|---|---|---|
| 루프 안 `s += p` | **고친다** | O(n²) — 데이터가 커지면 반드시 문제가 된다 |
| 한 줄 `a + b + c` | **둔다** | 이미 `invokedynamic` 한 번이다 |
| 한 줄 `new StringBuilder().append().append().toString()` | **`+` 로 되돌린다** | 객체가 오히려 하나 더 생기고 읽기 나쁘다 |

**한 줄 연결을 `StringBuilder` 로 바꾸면 나빠지는 것**

- **객체가 하나 늘어난다** — `StringBuilder` 인스턴스 + 결과 `String`.\
  `+` 는 연결 호출 한 번으로 결과 `String` 만 만든다.
- **읽기가 나빠진다.** `"user=" + id + " ok"` 가 `append` 세 번보다 명백히 낫다.
- **JIT가 도울 여지도 줄어든다** — `invokedynamic` 쪽은 런타임이 최종 길이를 먼저 계산해
  배열을 한 번만 잡는 전략을 고를 수 있다. *(그 전략이 실제로 선택되는지는 안 확인했다.)*

**용량 최적화의 순서**

- **나중이다.**
- `+=` 의 O(n²) 앞에서 용량 재할당 십여 번은 **사소하다.**\
  측정 표를 보면 `StringBuilder` 쪽은 n=64000 에서도 0.132ms 인데, 그 안에 재할당이 이미 다 포함돼 있다.
- 순서: ① 루프 안 `+=` 를 `StringBuilder` 로 바꾼다 → ② 그래도 느리면 **측정한다** → ③ 그때 용량을 논한다.
- 이 순서를 뒤집으면 **효과 없는 최적화에 시간을 쓰고 진짜 문제를 못 본다.**

### 10. 다른 주제와 잇기

**O(n²)의 근본 원인은 어느 주제인가**

- **[35번](../35-string/)의 성질**이다 — `String` 이 **불변**이라 매번 새 객체에 전체를 복사한다.
- 36번(이 주제)은 **"그래서 컴파일러가 무엇을 하는가"** 와 **"얼마나 느린가"** 를 다룬다.
- 그래서 이 주제의 결론은 "컴파일이 바뀌어도 복잡도는 안 바뀐다"이고,\
  그 근거가 17·21·25에서 모두 4배 증가율이 나온 측정이다.

**"2배 + 2" 와 동적 배열의 증폭**

- 같은 **상환 분석**의 사례다.
- 한 칸씩 늘리면 복사 총량이 O(n²)이고, **배수로 늘리면 총 복사량이 O(n)** 이 된다.\
  원리는 [`../../../../../data-structure/01-dynamic-array/`](../../../../../data-structure/01-dynamic-array/) 가 정본이다.
- `StringBuilder` 는 **`2배 + 2`** 를 골랐다(실행으로 확인한 16→34→70→142→286→574).\
  `+2` 는 용량 0에서 시작해도 늘어나게 만드는 장치다 — `0 × 2 = 0` 이면 영원히 안 늘어난다.
- 재미있는 대비: **`+=` 루프는 "한 칸씩 늘리기"와 같은 O(n²)** 이고, `StringBuilder` 는 "배수로 늘리기"다.\
  같은 주제가 문자열에서 되풀이된다.

**`1 + 2 + "x"` 가 `"3x"` 인 것**

- **[`../02-numeric-operations/`](../02-numeric-operations/) 의 규칙**이다(이항 수치 승격 + `+` 의 왼쪽 결합).
- `1 + 2` 는 양쪽이 `int` 라 **산술 덧셈** `3` 이 되고, 그 다음 `3 + "x"` 에서 문자열 연결이 된다.
- JLS §15.18.1이 이 예제를 직접 싣고 있다 — `1 + 2 + " fiddlers"` 는 `"3 fiddlers"`, `"fiddlers " + 1 + 2` 는 `"fiddlers 12"`.
- 실행으로 확인: `1 + 2 + "x" = 3x`, `"x" + 1 + 2 = x12`.

**`StringBuffer` 와 `StringBuilder` 의 유일한 차이**

```java
// JDK 21.0.5 — 실제 소스 그대로
public final class StringBuffer      extends AbstractStringBuilder ...   // StringBuffer.java  112~113행
public final class StringBuilder     extends AbstractStringBuilder ...   // StringBuilder.java  91~92행

public synchronized StringBuffer append(String str) {                    // StringBuffer.java  311행
```

- **동기화**다. 둘 다 `AbstractStringBuilder` 를 상속하고 실제 로직은 거기 있다.
- `StringBuffer`(1.0)는 메서드에 `synchronized` 가 붙어 있고, `StringBuilder`(5)는 안 붙어 있다.
- 단일 스레드면 `StringBuilder` 를 쓴다 — 락 획득 비용이 없다.
- 그리고 **여러 스레드가 하나의 버퍼를 공유하는 설계 자체가 드물다.** `StringBuffer` 가 필요한 경우는 거의 없다.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Ex`(36-javap) `javap -c -p` | 상수 접기 · `twoVars` 의 `invokedynamic` · **루프 `+=` 가 `invokedynamic`** · `loopBuilder` | 17 · 21 · 25 (**형태 동일**) |
| `Ex`(36-javap) `javap -v` | `BootstrapMethods` — `StringConcatFactory.makeConcatWithConstants` 와 레시피 | 21 |
| `Ex`(36-javap) `javac -XDstringConcat=inline` + `javap -c` | Java 8 방식 재현 — 루프 안 `new StringBuilder` | 21 |
| `Ex`(36-bench) | `+=` 대 `StringBuilder` 시간, n 2배당 증가율 | 17 · 21 · 25 (**셋 다 ≈4배**) |
| `Ex`(36-capacity) | 기본 16, `2배+2` 증가, `"abc"` -> 19, 한글/ASCII 용량 단위 | 17 · 21 · 25 (동일) |
| `Ex`(36-utils) | `String.join`·`Collectors.joining`·`repeat`·`format`·`null` 조립 | 17 · 21 · 25 (동일) |
| `src.zip` 열람 | `AbstractStringBuilder.newCapacity`·`capacity`, `Collectors.joining`, `StringJoiner` 필드, `StringBuffer`/`StringBuilder` 선언부 | 21 |
| JLS 원문 | §15.18.1 문자열 연결 — "may use the `StringBuffer` class or a similar technique" | — |

**구현에 의존하는 항목**

| 항목 | 무엇에 의존하나 |
|---|---|
| `invokedynamic` 으로 컴파일되는 것 | **javac 구현**(JDK 9+). `-XDstringConcat=inline` 로 뒤집힌다 |
| 기본 용량 16, 증가 `2배+2` | `AbstractStringBuilder` 구현 |
| `"abc"` 로 만든 용량이 19 | 〃 (`길이 + 16`) |
| `repeat(0) == ""` | 구현 최적화 — 명세가 아니다 |
| 측정 밀리초 | 이 기계·이 JDK·이 측정 방법 |
| `javap` 출력 들여쓰기 | JDK 버전(25가 두 칸 더 들여쓴다) |

**버전이 오르면 다시 돌려야 할 것**

- `javap -c` 로 **연결 전략이 여전히 `invokedynamic` 인지**. 이것이 이 주제의 본문이다.
- `BootstrapMethods` 의 부트스트랩 메서드 이름·시그니처.
- 용량 정책(16 · `2배+2`).
- 측정은 **기울기만** 다시 확인하면 된다 — 절댓값은 애초에 이식되지 않는다.

## 안 돌려 본 것

- JMH로 같은 것을 재기 — 이 문서의 측정은 손으로 만든 하네스다.
- `invokedynamic` 의 **첫 호출(부트스트랩) 비용** — 기동 시간 영향은 안 쟀다.
- `StringConcatFactory` 가 런타임에 **실제로 어떤 전략을 고르는지**(`-Djava.lang.invoke.stringConcat=...`).
- `String.join` 의 구분자·컬렉션 자체가 `null` 일 때 — 원소가 `null` 인 경우만 돌렸다.
- 로깅 API(`log.debug("..." + x)`)의 실제 동작 — 「어디서 틀리나 3」에 적었지만 돌려 보지 않았다.
- `StringBuffer` 의 실제 동기화 비용.
