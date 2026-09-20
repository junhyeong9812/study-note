# java/syntax/36 — `StringBuilder` 와 문자열 연결이 컴파일되는 방식 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [JLS SE 21 §15.18.1 String Concatenation Operator +](https://docs.oracle.com/javase/specs/jls/se21/html/jls-15.html) · [Java SE 21 `StringBuilder` API 문서](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/StringBuilder.html) · JDK 21.0.5 표준 라이브러리 소스 `java.base/java/lang/AbstractStringBuilder.java`(`lib/src.zip`).
> **실행 검증** — 이 문서의 모든 출력은 Temurin **JDK 21.0.5** 에서 실제로 돌려 얻은 것이다.\
> `javap -c` · `javap -v` 로 **컴파일된 결과 자체**를 떴고, 성능은 **직접 재서** 표로 실었다.\
> 바이트코드 형태는 **17.0.13 · 21.0.5 · 25.0.1 에서 모두 같았다**(셋 다 `invokedynamic`).
> **버전** — ★ **JDK 9부터 `+` 는 `StringBuilder` 가 아니라 `invokedynamic` 으로 컴파일된다**(JEP 280).\
> "루프 안 `+=` 는 반복마다 `StringBuilder` 를 새로 만든다"는 **Java 8까지의 설명**이다. 이 문서는 그것을 바이트코드로 반증한다.\
> `String.join` 은 **8**, `String.repeat`·`lines` 는 **11**, `formatted` 는 **15**.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.
> 선행: [35 `String`](../35-string/).

## 한눈에 — 쉽게 말하면

**문자열을 `+` 로 이어 붙이는 것은 새 종이에 처음부터 다시 옮겨 적는 것이고,\
`StringBuilder` 는 한 장에 이어 쓰는 것이다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 종이 한 장 | `String` 객체 하나 — 다 쓰고 나면 못 고친다 |
| 새 종이에 처음부터 옮겨 적기 | `s = s + x` — 매번 새 `String` 을 만들고 전체를 복사한다 |
| 여백을 넉넉히 둔 공책 | `StringBuilder` 의 내부 배열(capacity) |
| 공책에 이어 쓰기 | `sb.append(x)` — 복사 없이 뒤에 쓴다 |
| 공책이 꽉 차서 더 큰 공책에 한 번 옮기기 | 용량 증가(배열 재할당) — 가끔만 일어난다 |
| 대필자가 문장 전체를 먼저 듣고 한 번에 적는 것 | 컴파일러가 `a + b + c` 를 **한 번의 호출**로 합치는 것 |

- 한 줄짜리 `a + b + c` 는 **대필자가 한 번에 적는다** — 중간 종이가 안 생긴다.
- 루프 안의 `s += x` 는 **대필자가 매 반복마다 새로 불려 온다.**\
  대필자는 그 반복 한 번만 알기 때문에, **그때까지 쓴 것을 전부 다시 옮겨 적는다.**
- `StringBuilder` 는 공책이라 **옮겨 적는 일 자체가 없다.**

```text
루프에서 100글자를 만들 때 복사되는 글자 수

  s += "x"  (String)                      sb.append("x")  (StringBuilder)
  1 + 2 + 3 + ... + 100 = 5,050자          100자 (여백에 그냥 쓴다)
                                           + 용량 증가 때 몇 번 통째 복사
  +------------------------------+        +------------------------------+
  | 반복마다 전체를 복사한다       |        | 반복마다 한 글자만 쓴다       |
  | O(n^2)                       |        | O(n) (상환)                  |
  +------------------------------+        +------------------------------+
```

실제로 재 보면 이렇게 나온다(JDK 21.0.5, 이 머신에서 측정 — 조건은 「동작 방식 (4)」).

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

- 오른쪽 열이 핵심이다 — **n 을 2배로 늘릴 때마다 시간이 약 4배**가 된다. 전형적인 O(n²)다.
- `StringBuilder` 쪽은 같은 구간에서 **약 2배씩** 늘어난다(0.002 → 0.132).

실무에서 이게 터지는 자리는 **로그 조립·CSV 생성·SQL 조립 루프**다.\
개발 데이터 100건에서는 0.1밀리초라 안 보이고, 운영에서 5만 건이 되는 순간 **한 요청이 수백 밀리초**가 된다.

> **상환(amortized) O(n)** — 가끔 드는 큰 비용을 평소의 싼 연산에 나눠 평균 낸 것.\
> 예: `append` 는 보통 한 글자만 쓰지만 가끔 배열을 통째로 복사한다. 그 비용을 나누면 한 번에 상수 시간이다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. 소스의 `+` 는 **클래스 파일에서 무엇이 되는가** — 그리고 그것이 버전마다 같은가.
2. 루프 안의 `+=` 가 느린 **진짜 이유**는 무엇인가 — 컴파일 방식인가, 다른 것인가.
3. **얼마나** 느린가 — 그리고 그것을 어떻게 재는가.

## 동작 방식

### (1) 상수 식 연결 — 컴파일 타임에 사라진다

**언제 쓰나** — 리터럴이나 `static final` 상수만으로 이뤄진 연결.

```text
소스                        클래스 파일

"he" + "l" + "lo"   --->    ldc #7   // String hello
                            areturn
```

`javap -c` 출력 그대로 (JDK 21.0.5):

```text
  static java.lang.String constFold();
    Code:
       0: ldc           #7                  // String hello
       2: areturn
```

그림 해설 (한 단계씩):

- **`+` 가 명령 하나도 남기지 않았다.** 연결이 컴파일 타임에 끝났다.
- 남은 것은 `ldc`(상수 풀 항목 적재) 하나다 — 이미 합쳐진 `"hello"` 를 그대로 꺼낸다.
- 그래서 상수 식 연결은 **런타임 비용이 0**이다. 가독성을 위해 여러 줄로 쪼개도 손해가 없다.

비용 — 0. 상수 풀에 합쳐진 문자열 하나가 더 들어갈 뿐이다.

### (2) 변수가 섞인 연결 — `invokedynamic` 한 번

**언제 쓰나** — 한 줄 안에서 변수를 이어 붙이는 모든 자리. 로그 메시지·예외 메시지.

```text
소스                        클래스 파일 (JDK 9+)

a + b               --->    aload_0
                            aload_1
                            invokedynamic makeConcatWithConstants
                            areturn
```

`javap -c` 출력 그대로 (JDK 21.0.5):

```text
  static java.lang.String twoVars(java.lang.String, java.lang.String);
    Code:
       0: aload_0
       1: aload_1
       2: invokedynamic #9,  0              // InvokeDynamic #0:makeConcatWithConstants:(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;
       7: areturn
```

`javap -v` 로 그 `invokedynamic` 이 무엇을 부르는지까지 본 것이다(출력 그대로):

```text
BootstrapMethods:
  0: #73 REF_invokeStatic java/lang/invoke/StringConcatFactory.makeConcatWithConstants:(Ljava/lang/invoke/MethodHandles$Lookup;Ljava/lang/String;Ljava/lang/invoke/MethodType;Ljava/lang/String;[Ljava/lang/Object;)Ljava/lang/invoke/CallSite;
    Method arguments:
      #71 \u0001\u0001
```

그림 해설 (한 단계씩):

- **`StringBuilder` 가 없다.** `new StringBuilder` 도 `append` 도 `toString` 도 안 나온다.
- 대신 `java.lang.invoke.StringConcatFactory.makeConcatWithConstants` 를 **부트스트랩 메서드**로 쓴다.
- `Method arguments` 의 `\u0001\u0001` 은 **연결 레시피**다 — `\u0001` 이 "여기에 인자 하나를 넣어라"는 자리표시자다.\
  인자가 둘이니 자리표시자도 둘이다.
- 실제로 무엇을 만들지는 **런타임에 처음 이 줄을 지날 때** 결정되고, 그 뒤로는 그 결과가 재사용된다.

비용 — 첫 호출에서 메서드 핸들을 조립하는 비용(한 번), 그 뒤로는 호출 한 번.\
중간 `String` 이 안 생기고 **최종 길이를 먼저 계산해 배열을 한 번만 잡는** 전략도 가능해진다.

> **`invokedynamic`** — "무엇을 부를지 런타임에 정한다"고 클래스 파일에 적어 두는 JVM 명령.\
> 예: 첫 실행 때 부트스트랩 메서드가 불려 실제 호출 대상을 정하고, 이후에는 그것이 그대로 쓰인다.

> **부트스트랩 메서드(bootstrap method)** — `invokedynamic` 이 처음 실행될 때 "무엇을 부를지"를 결정해 주는 메서드.\
> 예: 문자열 연결에서는 `StringConcatFactory.makeConcatWithConstants` 가 그 역할이다.

**★ 옛 설명은 이제 틀렸다 — 그러나 직접 확인할 수 있다.**

`javac` 의 내부 옵션 `-XDstringConcat=inline` 으로 **Java 8 방식**을 강제해 보면 이렇게 나온다(출력 그대로).

```text
  static java.lang.String twoVars(java.lang.String, java.lang.String);
    Code:
       0: new           #9                  // class java/lang/StringBuilder
       3: dup
       4: invokespecial #11                 // Method java/lang/StringBuilder."<init>":()V
       7: aload_0
       8: invokevirtual #12                 // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
      11: aload_1
      12: invokevirtual #12                 // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
      15: invokevirtual #16                 // Method java/lang/StringBuilder.toString:()Ljava/lang/String;
      18: areturn
```

- 이것이 **"`+` 는 `StringBuilder` 로 바뀐다"는 설명의 출처**다. 지금도 옵션으로 되살릴 수 있다.
- `-XD...` 는 **문서화되지 않은 javac 내부 옵션**이다. 학습용으로만 쓴다.

### (3) 루프 안의 `+=` — 반복마다 `invokedynamic` 한 번

**언제 쓰나** — 반복문에서 문자열을 누적하는 모든 코드.

```text
for (String p : parts) {
    s += p;
}
```

`javap -c` 출력 그대로 (JDK 21.0.5 — 17·25 동일):

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

그림 해설 (한 단계씩):

- 루프 몸통(오프셋 17~35)에 **`invokedynamic` 이 하나** 있다. `new StringBuilder` 는 **없다.**
- `aload_1`(지금까지의 `s`) + `aload 5`(이번 조각) -> 연결 -> `astore_1`(새 `s` 로 교체).
- 즉 **반복마다 새 `String` 이 하나씩 만들어지고, 그때마다 지금까지의 내용이 전부 복사된다.**
- 느린 이유는 `StringBuilder` 를 새로 만들어서가 아니라 **결과 `String` 을 매번 새로 만들어서**다.\
  그 뿌리는 [`../35-string/`](../35-string/) 의 **불변성**이다.

같은 소스를 `-XDstringConcat=inline` 으로 컴파일하면 **옛 형태**가 나온다(출력 그대로).

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
  JDK 9+ 기본 (indy)                       -XDstringConcat=inline (Java 8 방식)
  +-----------------------------+         +-----------------------------+
  | 루프 몸통 안:               |         | 루프 몸통 안:               |
  |   invokedynamic  x1         |         |   new StringBuilder         |
  |                             |         |   append x2                 |
  |                             |         |   toString                  |
  +-----------------------------+         +-----------------------------+
   StringBuilder 는 안 보인다               반복마다 StringBuilder 를 새로 만든다

        어느 쪽이든 결과 String 은 반복마다 새로 만들어진다 -> O(n^2)
```

- **두 형태 모두 O(n²)다.** 바뀐 것은 중간 도구이지 복잡도가 아니다.
- 실측에서도 17(indy)과 25(indy)의 곡선이 같은 모양이었다 — 「(4)」의 표.

비용 — 반복마다 연결 1회 + 전체 복사. 총 복사량 n(n+1)/2 = **O(n²)**(손계산).

### (4) `StringBuilder` — 공책에 이어 쓰고, 가끔 더 큰 공책으로 옮긴다

**언제 쓰나** — 반복·조건 분기로 문자열을 조립할 때.

```text
  capacity 16 짜리 공책                append 로 17번째 글자를 쓰려는 순간

  +--------------------------+        +----------------------------------------+
  | xxxxxxxxxxxxxxxx         |  --->  | 새 배열(34칸)을 만들고 16칸을 통째 복사 |
  | (16칸 다 씀)             |        | 그 뒤에 17번째 글자를 쓴다              |
  +--------------------------+        +----------------------------------------+
        복사 없음                            이때만 복사가 일어난다
```

실행 결과 (JDK 21.0.5 — 17·25 동일):

```text
new StringBuilder()          capacity = 16, length = 0
length 17 에서 capacity 16 -> 34
length 35 에서 capacity 34 -> 70
length 71 에서 capacity 70 -> 142
length 143 에서 capacity 142 -> 286
length 287 에서 capacity 286 -> 574

new StringBuilder("abc")     capacity = 19
new StringBuilder(100)       capacity = 100
```

그림 해설 (한 단계씩):

- 기본 용량은 **16**이다. 문자열로 초기화하면 **그 길이 + 16**(`"abc"` -> 19).
- 늘어나는 규칙은 **`새 용량 = 기존 × 2 + 2`** 다: 16 → 34 → 70 → 142 → 286 → 574.
- JDK 21 소스가 그 `+2` 의 출처를 보여 준다.

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

- 세 번째 인자 `oldLength + (2 << coder)` 가 **"기존 + 2배"** 를 만드는 선호 증가량이다.
- `coder` 는 0(LATIN1) 또는 1(UTF16)이다 — `<< coder` 와 `>> coder` 로 **바이트 수와 글자 수를 오간다.**\
  그래서 `capacity()` 는 바이트가 아니라 **글자 수**를 돌려준다(실행으로 확인: 한글 20자여도 34).

비용 — `append` 는 상환 O(1). 최종 길이를 알면 `new StringBuilder(n)` 으로 **재할당을 0번**으로 만들 수 있다.

> **용량(capacity)과 길이(length)** — 공책의 칸 수와 실제로 쓴 글자 수.\
> 예: `capacity 34, length 20` 이면 14칸이 비어 있어 14글자는 복사 없이 더 쓸 수 있다.

### (5) 측정 — "느리다"를 수치로

**언제 쓰나** — 성능 주장을 문서에 쓰기 전에.

측정 조건(그대로 적는다):

| 항목 | 값 |
|---|---|
| 기계 | 13th Gen Intel Core i7-13700HX · 24 논리 코어 · Linux |
| JDK | Temurin 17.0.13 · 21.0.5 · 25.0.1 |
| 방법 | `System.nanoTime` 으로 감싸고, 같은 n 을 **5회 반복해 최솟값** |
| 워밍업 | 두 메서드를 각각 `n=2000` 으로 **200회** 먼저 돌려 JIT 컴파일 유도 |
| 검증 | 결과 문자열 길이가 n 과 다르면 `AssertionError` (연산이 지워지지 않았음을 보장) |
| 한계 | **JMH가 아니다.** 단일 프로세스·단일 스레드, 배치 효과와 GC를 통제하지 않았다 |

JDK 21.0.5 결과:

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

세 JDK의 「증가율」만 나란히 놓으면 이렇다.

| n | 17.0.13 | 21.0.5 | 25.0.1 |
|---|---|---|---|
| 1000 → 2000 | 3.72배 | 4.42배 | 3.95배 |
| 2000 → 4000 | 4.07배 | 3.84배 | 4.79배 |
| 4000 → 8000 | 3.88배 | 3.45배 | 3.65배 |
| 8000 → 16000 | 3.84배 | 4.07배 | 4.06배 |
| 16000 → 32000 | 4.76배 | 4.13배 | 5.09배 |
| 32000 → 64000 | 4.79배 | 4.38배 | 4.01배 |

그림 해설 (한 단계씩):

- 세 버전 모두 **n 이 2배일 때 시간이 약 4배** — O(n²)의 지문이다.
- **JDK 버전이 이 복잡도를 바꾸지 못한다.** `invokedynamic` 은 상수 배수를 줄일 뿐이다.
- 배수(오른쪽에서 두 번째 열)는 **n 이 커질수록 커진다** — "몇 배 느리다"는 표현 자체가 n에 의존한다.\
  그래서 "`+=` 는 `StringBuilder` 보다 1800배 느리다"는 말은 **n=64000 에서만** 맞다.

비용 — 이 측정 자체가 약 2초쯤 걸린다. 그 정도면 문서에 수치를 적을 자격을 얻는다.

## 문법 — 형태와 규칙

직접 쓴 최소 예제다. 묻는 것 하나만 남겼다.

### 조립하는 네 가지 형태

```java
String a = x + ", " + y;                                   // 한 줄이면 이게 제일 낫다
StringBuilder sb = new StringBuilder();                    // 반복·분기 조립
for (String p : parts) sb.append(p);
String b = String.join(", ", parts);                       // 구분자로 잇기 (8+)
String c = parts.stream().collect(Collectors.joining(", ", "[", "]"));  // 접두·접미까지
```

실행 결과:

```text
String.join(", ", "a","b","c")      = a, b, c
String.join("-", List.of("a","b"))   = a-b
String.join(",", List.of())          = []
join 에 null 원소가 섞이면            = a,null
Collectors.joining                   = [a, b, c]
```

- `String.join` 은 **가변 인자와 `Iterable` 둘 다** 받는다.
- 빈 컬렉션이면 **빈 문자열**이다(예외가 아니다).
- **`null` 원소는 `"null"` 이라는 글자가 된다** — 조용히 데이터에 섞인다. 이 문서에서 가장 조용한 함정이다.

### `null` 이 섞이면 어디서나 `"null"` 이 된다

```text
String.valueOf((Object) null) = null
String.valueOf((char[]) null) -> NPE
"x" + null 참조               = xnull
sb.append((String) null)      = [null] length=4
```

- `+` 도 `append` 도 `join` 도 **`null` 을 `"null"` 네 글자로 바꾼다.**
- 예외가 안 나므로 로그·CSV·SQL에 `null` 이라는 **문자열**이 들어간다.
- 유일한 예외가 `String.valueOf((char[]) null)` 이다 — 이건 NPE를 던진다.\
  오버로드가 `char[]` 로 뽑혀 배열 내용을 읽으려 하기 때문이다.
- 방어: `Objects.toString(x, "")` 또는 조립 전에 `null` 을 막는다([**60번 주제**](../60-null-handling/)).

### 반복과 서식

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

- `repeat(0)` 이 **상수 풀의 `""` 를 그대로 돌려준다**(`== ""` 가 `true`).
- `repeat(-1)` 은 `IllegalArgumentException` 이고 메시지에 값이 찍힌다.
- `String.format` 의 타입 불일치는 **컴파일 타임에 안 잡힌다** — 런타임 `IllegalFormatConversionException` 이다.\
  메시지 `d != java.lang.String` 은 "`%d` 자리에 `String` 이 왔다"는 뜻이다.
- `formatted` 는 `String.format(this, args)` 와 같다(15+) — 읽는 순서가 자연스러워진다.

### 무엇을 언제 쓰나

| 형태 | 언제 | 왜 |
|---|---|---|
| `a + b + c` (한 줄) | 거의 항상 | `invokedynamic` 한 번. 가장 읽기 좋다 |
| `StringBuilder` | **루프·조건 분기** 조립 | `+=` 의 O(n²)를 피한다 |
| `String.join` | 구분자로 잇기 | 마지막 구분자 처리를 안 해도 된다 |
| `Collectors.joining` | 스트림에서 잇기 | 접두·접미까지 한 번에 |
| `String.format` | 서식이 필요할 때 | 자릿수·천 단위 구분 |
| `"x".repeat(n)` | 같은 조각 반복 | 루프보다 빠르고 짧다 |

## 어디서 틀리나

이 주제의 값어치는 전부 여기 있다.

### 1. "`+` 는 `StringBuilder` 로 바뀐다"고 외운다

```text
Java 8 까지 (그리고 -XDstringConcat=inline)   JDK 9+ 기본
+---------------------------------+          +---------------------------------+
| new StringBuilder               |          | invokedynamic                   |
| append x2                       |          |   makeConcatWithConstants       |
| toString                        |          |                                 |
+---------------------------------+          +---------------------------------+
  바이트코드에 StringBuilder 가 있다            바이트코드에 StringBuilder 가 없다
```

- 면접·블로그에서 가장 흔히 도는 낡은 설명이다.
- **틀린 것은 메커니즘이고, 결론(루프 안 `+=` 를 쓰지 마라)은 여전히 맞다.**\
  그래서 결론만 외운 사람은 틀린 근거를 들고 맞는 답을 한다.
- 확인하는 법은 하나다 — **자기 코드를 `javap -c` 로 떠 보는 것.**

### 2. 한 줄짜리 연결을 `StringBuilder` 로 "최적화"한다

```java
// 이렇게 쓸 이유가 없다
String msg = new StringBuilder().append("user=").append(id).append(" ok").toString();
// 이게 낫다 — invokedynamic 한 번으로 끝난다
String msg = "user=" + id + " ok";
```

- 한 줄 연결은 **이미 한 번의 호출**이다. `StringBuilder` 로 바꾸면 객체 하나가 오히려 늘어난다.
- 읽기도 나빠진다.
- 판단 규칙: **루프나 분기가 없으면 `+` 를 쓴다.**

### 3. 로그 문자열을 조건 없이 조립한다

```java
log.debug("state=" + heavyToString());   // debug 가 꺼져 있어도 조립은 일어난다
log.debug("state={}", heavyToString());  // 여전히 heavyToString() 은 호출된다
log.debug("state={}", lazySupplier);     // 이렇게 해야 안 불린다
```

- `+` 는 **인자를 만들 때 평가**되므로 로그 레벨과 무관하게 조립된다.
- 자리표시자(`{}`)를 써도 **인자 자체의 평가는 막지 못한다.**
- 이 주제의 범위를 넘는 이야기이므로 여기까지만 적는다. *(로깅 API 동작은 안 돌려 봤다.)*

### 4. `null` 이 `"null"` 로 조용히 들어간다

```text
"x" + null 참조               = xnull
sb.append((String) null)      = [null] length=4
join 에 null 원소가 섞이면      = a,null
```

- **예외가 안 난다.** CSV의 한 칸이 `null` 이라는 네 글자가 되고, 그대로 DB에 적재된다.
- 나중에 `"null"` 을 문자열로 저장한 행과 진짜 `NULL` 행이 섞여 **복구가 어려워진다.**
- 방어는 조립 시점이 아니라 **값이 들어오는 경계**에서 한다.

### 5. 용량을 미리 안 잡는다

```text
length 17 에서 capacity 16 -> 34
length 35 에서 capacity 34 -> 70
length 71 에서 capacity 70 -> 142
length 143 에서 capacity 142 -> 286
length 287 에서 capacity 286 -> 574
```

- 10만 글자를 만들면 재할당이 **십여 번** 일어나고 그때마다 전체 복사가 붙는다.
- 최종 길이를 대략 알면 `new StringBuilder(100_000)` 으로 **재할당 0번**이 된다.
- 다만 **`+=` 의 O(n²) 앞에서는 이 최적화가 사소하다.** 순서를 지킨다 —\
  먼저 `StringBuilder` 로 바꾸고, 그 다음에야 용량을 논한다.

## 구현 세부사항 대 언어 보장

이 주제는 **언어가 결과만 정하고 방법은 안 정한 대표 사례**다.

```text
     언어(JLS §15.18.1)가 보장하는 것            구현(javac·JVM)이 정하는 것
  +----------------------------------+      +----------------------------------+
  | 결과는 두 피연산자를 이어 붙인    |      | StringBuilder 를 쓸지            |
  | 새 String 이다                   |      | invokedynamic 을 쓸지            |
  | 상수 식이면 새로 만들지 않는다    |      | 중간 String 을 만들지 말지        |
  | 왼쪽부터 결합한다                 |      | 기본형을 직접 변환할지            |
  +----------------------------------+      +----------------------------------+
   소스만 보고 결과를 말할 수 있다             javap 를 떠 봐야 알 수 있다
```

**언어 보장** — JLS SE 21 §15.18.1 원문.

> The `String` object is newly created (§12.5) unless the expression is a constant expression (§15.29).
>
> An implementation **may** choose to perform conversion and concatenation in one step to avoid creating
> and then discarding an intermediate `String` object. To increase the performance of repeated string
> concatenation, a Java compiler **may** use the `StringBuffer` class or a similar technique to reduce
> the number of intermediate `String` objects that are created by evaluation of an expression.

- 명세가 **"may"** 라고 두 번 쓴다 — `StringBuffer` 를 쓰는 것도, 안 쓰는 것도 합법이다.\
  (명세는 `StringBuffer` 라고 적혀 있다. `StringBuilder` 는 Java 5에 들어왔는데 문장은 그대로 남아 있다.)
- 그래서 **"`+` 는 `StringBuilder` 가 된다"는 명세가 아니라 그 시절 javac의 선택**이었다.\
  JDK 9가 다른 선택을 했고, 명세는 한 글자도 안 바꿔도 됐다.
- 반대로 **결과와 결합 방향은 보장된다** — `1 + 2 + " fiddlers"` 가 `"3 fiddlers"` 인 것은 명세가 예제로 못박았다.\
  실행으로 확인: `1 + 2 + "x" = 3x`, `"x" + 1 + 2 = x12`.

**구현 세부** — 직접 확인한 것들.

| 확인한 것 | 값 | 무엇에 의존하나 |
|---|---|---|
| 연결 전략 | `invokedynamic` + `StringConcatFactory` | JDK 9+ 기본. `-XDstringConcat=inline` 로 뒤집힌다 |
| 기본 용량 | 16 | `StringBuilder` 구현 |
| 증가 규칙 | `기존 × 2 + 2` | `AbstractStringBuilder.newCapacity` 구현 |
| `capacity()` 단위 | 글자 수 (바이트 아님) | compact strings 구현(`>> coder`) |
| 절대 시간 | 표의 밀리초 값 | 이 기계·이 JDK·이 측정 방법 |

- **표의 밀리초는 다른 기계에서 재현되지 않는다.** 재현되는 것은 **증가율 ≈ 4배**뿐이다.
- 그래서 문서에 남길 결론은 "1836배 느리다"가 아니라 **"n² 로 늘어난다"** 여야 한다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓰는 것 | 왜 |
|---|---|---|
| 한 줄 연결 | `+` | `invokedynamic` 한 번. 제일 읽기 좋다 |
| 루프 누적 | `StringBuilder` | `+=` 는 O(n²) |
| 구분자로 잇기 | `String.join` / `Collectors.joining` | 마지막 구분자 예외 처리가 없다 |
| 최종 길이를 아는 대량 조립 | `new StringBuilder(n)` | 재할당 0번 |
| 여러 스레드가 같은 버퍼에 | `StringBuffer` | `StringBuilder` 는 동기화가 없다 |
| 같은 조각 반복 | `"x".repeat(n)` | 루프가 필요 없다 |
| 서식·자릿수 | `String.format` / `formatted` | 수동 패딩보다 안전하다 |

판단 규칙 세 줄.

- **루프 안에 `+=` 가 보이면 그 자리는 고친다.** 근거는 측정이고, 복잡도는 버전이 바꿔 주지 않는다.
- **루프 밖의 `+` 는 그대로 둔다.** 바꾸면 느려지고 읽기 나빠진다.
- **성능을 말하기 전에 `javap -c` 를 뜨고 시간을 잰다.** 이 주제의 절반은 그 습관이다.

## 핵심 문장

- JDK 9부터 `+` 는 **`invokedynamic` + `StringConcatFactory`** 로 컴파일된다 — 바이트코드에 `StringBuilder` 가 없다.
- 그래도 루프 안 `+=` 는 여전히 느리다. 이유는 컴파일 방식이 아니라 **`String` 이 불변**이라 매번 전체를 복사하기 때문이다.
- 상수 식 연결은 **`ldc` 하나**로 접혀 런타임 비용이 0이다.
- `StringBuilder` 의 용량은 **16에서 시작해 `기존 × 2 + 2`** 로 늘고, `capacity()` 는 글자 수를 돌려준다.
- 측정하면 n 이 2배일 때 `+=` 시간이 **약 4배** — 세 JDK 모두 같았다. 재현되는 것은 배수가 아니라 이 기울기다.

## 관련 자료

- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 36번)
- [`../35-string/`](../35-string/) — **경계: 그쪽은 「`String` 객체 하나가 무엇인가」(불변성·상수 풀·메서드)까지,
  여기는 「여러 조각을 이어 붙일 때 컴파일러가 무엇을 하나」부터다.**\
  상수 풀과 `intern()` 은 전부 35번이고, `ldc` 가 왜 같은 객체를 주는지도 거기다.
- [`../02-numeric-operations/`](../02-numeric-operations/) — **경계: `1 + 2 + "x"` 에서 `1 + 2` 가 `3` 이 되는 규칙(이항 수치 승격)은 거기,
  `+` 가 문자열 연결로 갈리는 자리부터가 여기다.**
- [`../../../../../data-structure/01-dynamic-array/`](../../../../../data-structure/01-dynamic-array/) — **경계: "왜 2배씩 늘리나"라는 상환 분석 원리는 거기,
  "`StringBuilder` 가 실제로 몇 배로 늘리나"는 여기.**
- [**37번 주제**](../37-regex/)(정규식) — `String.format` 이 아니라 `replaceAll` 쪽 조립
- [**60번 주제**](../60-null-handling/)(`null` 다루기) — `"null"` 이 섞이기 전에 막는 자리
- [`../../언어-특성/README.md`](../../언어-특성/README.md) — JIT·escape analysis. **왜 워밍업이 필요한지는 거기**

## 용어 풀이

- **`invokedynamic`** — 무엇을 부를지 런타임에 정하는 JVM 명령. 람다와 문자열 연결이 이것을 쓴다.
- **부트스트랩 메서드** — `invokedynamic` 이 처음 실행될 때 호출 대상을 정해 주는 메서드.
- **`StringConcatFactory`** — 문자열 연결의 부트스트랩을 담당하는 표준 라이브러리 클래스(`java.lang.invoke`).
- **연결 레시피(recipe)** — 부트스트랩에 넘기는 `\u0001` 자리표시자 문자열. 인자를 어디에 끼울지 적어 둔 것.
- **상수 접기(constant folding)** — 컴파일 타임에 값이 정해지는 식을 미리 계산해 두는 것. `"he"+"llo"` 가 `ldc` 하나가 된다.
- **용량(capacity)** — `StringBuilder` 내부 배열이 담을 수 있는 글자 수. 길이(length)와 다르다.
- **상환 분석(amortized analysis)** — 가끔 드는 큰 비용을 평소의 싼 연산에 나눠 평균 낸 것.
- **워밍업(warm-up)** — 측정 전에 같은 코드를 여러 번 돌려 JIT가 기계어로 컴파일하게 하는 것.
- **JMH** — 자바 마이크로벤치마크 도구. 이 문서의 측정은 JMH가 **아니다**.
- **`ldc`·`aload`·`astore`·`iinc`** — 상수 적재 · 참조 적재 · 참조 저장 · 정수 증가. 루프 바이트코드를 읽는 데 필요한 최소 명령들.

## 더 들어가면

- **`StringBuffer` 와 `StringBuilder` 의 차이는 동기화뿐**이다.\
  `StringBuffer`(1.0)가 메서드에 `synchronized` 를 걸고, `StringBuilder`(5)가 그것을 뺀 판이다.\
  둘 다 `AbstractStringBuilder` 를 상속한다 — `src.zip` 에서 선언부를 직접 확인했다.

```java
// JDK 21.0.5 — 실제 소스 그대로
public final class StringBuffer      extends AbstractStringBuilder ...   // StringBuffer.java  112~113행
public final class StringBuilder     extends AbstractStringBuilder ...   // StringBuilder.java  91~92행

public synchronized StringBuffer append(String str) {                    // StringBuffer.java  311행
```

  단일 스레드면 `StringBuilder` 를 쓴다.
- **`invokedynamic` 은 첫 호출이 느리다.** 부트스트랩이 메서드 핸들을 조립하기 때문이다.\
  그래서 기동 시간이 중요한 환경(서버리스)에서는 이것이 논점이 된다.\
  *(기동 비용은 이 문서에서 안 재 봤다.)*
- **`Collectors.joining` 의 내부는 `StringJoiner`** 다 — 소스를 열어 확인했다.

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

  그리고 `StringJoiner` 는 `StringBuilder` 가 아니라 **`String[]` 에 조각을 모아 두었다가 마지막에 한 번에 합친다**
  (`private String[] elts;` · `private int len;` — 소스 76·82행).\
  즉 이어 붙이는 방식이 셋(`+`·`StringBuilder`·`StringJoiner`)이고, **셋 다 "매번 전체 복사"를 피한다**는 점만 같다.
- **`String.repeat(0)` 이 `""` 와 `==` 인 것**은 구현 최적화다(실행으로 확인).\
  명세가 보장하는 것이 아니므로 코드가 의존하면 안 된다 — [`../35-string/`](../35-string/) 의 같은 교훈이다.
