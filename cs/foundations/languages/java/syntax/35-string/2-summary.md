# java/syntax/35 — `String`: 불변성·상수 풀·자주 쓰는 메서드 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [JLS SE 21 §3.10.5 String Literals](https://docs.oracle.com/javase/specs/jls/se21/html/jls-3.html) · [§15.29 Constant Expressions](https://docs.oracle.com/javase/specs/jls/se21/html/jls-15.html) · [Java SE 21 `String` API 문서](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/String.html) · JDK 21.0.5 표준 라이브러리 소스 `java.base/java/lang/String.java`(`lib/src.zip`).
> **실행 검증** — 이 문서의 모든 출력은 Temurin **JDK 21.0.5** 에서 실제로 돌려 얻은 것이다.\
> 프로그램 5개를 **17.0.13 · 21.0.5 · 25.0.1** 에서 모두 돌렸다.\
> **한 군데가 갈렸다** — `substring` 의 예외 메시지가 17과 21에서 다르다(「어디서 틀리나」 3번).
> **버전** — `String` 자체는 Java 1.0. 아래 `@since` 는 JDK 21 `src.zip` 에서 직접 읽은 것이다.\
> `isBlank`·`strip`·`repeat`·`lines` = **11** · `formatted`·`stripIndent` = **15** ·
> `chars`·`codePoints` = **`CharSequence` 의 default 로 1.8**(`String` 의 전용 재정의는 **9**) ·
> `join` = **1.8**. 내부 표현(compact strings)은 **9**부터.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.
> 선행: [01 기본형과 래퍼](../01-primitives-and-wrappers/).

## 한눈에 — 쉽게 말하면

**리터럴로 쓴 문자열은 도서관의 비치본이고, `new String` 은 내가 따로 찍은 복사본이다.**\
그리고 **어느 쪽이든 책에 낙서할 수 없다** — 고치려면 새 책을 찍는 수밖에 없다.

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 도서관 | 문자열 상수 풀(string pool) — JVM이 하나만 관리하는 공유 저장소 |
| 비치본 | 리터럴·상수 식으로 만들어진 `String` 객체 — 같은 내용이면 **딱 하나** |
| 내가 따로 찍은 복사본 | `new String(...)`·`StringBuilder.toString()`·런타임 연결로 만든 객체 |
| "같은 내용 비치본 주세요" 하고 바꿔 받는 것 | `intern()` |
| 책에 낙서 금지 | 불변성(immutability) — 내용을 바꾸는 메서드가 아예 없다 |
| 고친 판을 새로 찍는 것 | `replace`·`toUpperCase` 등이 **새 객체를 반환**하는 것 |
| 책장에 꽂힌 번호표 | 참조(reference) — 변수가 실제로 들고 있는 것 |

- 소스에 `"hello"` 라고 두 번 쓰면 **객체는 하나**다.\
  컴파일러가 두 곳에서 **같은 비치본의 번호표**를 건넨다.
- `new String("hello")` 는 **같은 내용의 복사본을 하나 더 찍는 것**이다.\
  내용은 같지만 **다른 책**이라 `==` 가 거짓이다.
- 런타임에 이어 붙인 문자열도 **복사본**이다 — 도서관에 자동으로 들어가지 않는다.\
  `intern()` 을 부르면 그때 비치본으로 바꿔 받는다.

```text
String a = "hello";                  String c = new String("hello");
String b = "hello";                  String f = var + "lo";   (var = "hel")

  a --번호표--+                        c --번호표--> [복사본 #1 : hello]
              +--> [비치본 : hello]
  b --번호표--+                        f --번호표--> [복사본 #2 : hello]

  a == b  -> true                      a == c -> false
                                       a == f -> false
                                       f.intern() == a -> true   (실행으로 확인)
```

`==` 는 **"같은 책인가"**를 묻고, `.equals` 는 **"내용이 같은가"**를 묻는다.

실무에서 이게 터지는 자리는 **HTTP 요청 파라미터·DB 컬럼 값을 `==` 로 비교하는 코드**다.\
테스트에서는 리터럴을 넣으니 비치본끼리 비교되어 통과하고,\
운영에서는 네트워크에서 만들어진 복사본이라 **조용히 `false`** 가 된다.

> **문자열 상수 풀(string pool)** — 같은 내용의 `String` 을 하나만 두고 공유하는 JVM 내부 저장소.\
> 예: `"hello"` 라는 리터럴이 소스 100군데에 있어도 실행 중 객체는 하나다.

> **불변(immutable)** — 만들어진 뒤 내부 상태가 절대 바뀌지 않는 것.\
> 예: `s.toUpperCase()` 는 `s` 를 바꾸지 않고 **대문자로 된 새 문자열을 돌려준다.**

> **인터닝(interning)** — 같은 내용의 객체를 하나로 모아 공유시키는 것.\
> 예: `f.intern()` 은 풀에 같은 내용이 있으면 **그 객체**를, 없으면 자기 자신을 넣고 돌려준다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. 같은 글자를 담은 두 `String` 이 **언제 같은 객체이고 언제 아닌가** — 그 경계는 누가 정하는가.
2. "불변"이 **무엇을 보장하고 무엇을 보장하지 않는가.**
3. `length()` 가 세는 것은 **무엇인가** — 사람이 세는 글자 수와 언제 갈리는가.

## 동작 방식

### (1) 불변성 — 바꾸는 메서드가 아예 없다

**언제 쓰나** — 문자열을 "고쳤다"고 생각하는 모든 자리.

```text
String u = "hello";
u.toUpperCase();          <- 반환값을 안 받으면 아무 일도 안 일어난다

  전                                  후
  u --> ["hello"]                     u --> ["hello"]      <- 그대로
                                            ["HELLO"]      <- 새로 만들어졌다가 버려짐
```

실행 결과 (JDK 21.0.5):

```text
u.replace('l','L')  = heLLo   원본 u = hello
u.toUpperCase()     = HELLO   원본 u = hello
u.concat("!")       = hello!  원본 u = hello
바꿀 게 없는 replace 가 같은 객체? true
substring(0) 이 같은 객체?         true
u.toString() 이 같은 객체?         true
```

그림 해설 (한 단계씩):

- `replace`·`toUpperCase`·`concat` 은 전부 **새 객체를 반환**하고 원본은 그대로다.
- 그래서 **반환값을 받지 않으면 아무 일도 안 일어난다** — 이것이 가장 흔한 초보 실수다.
- 마지막 세 줄이 흥미롭다: **바꿀 것이 없으면 자기 자신을 돌려준다.**\
  불변이라 그래도 안전하다 — 공유해도 누가 고칠 수 없기 때문이다.

JDK 21 소스가 그 최적화를 보여 준다.

```java
// JDK 21.0.5  java.base/java/lang/String.java  2832~2841행 — 실제 소스 그대로
public String substring(int beginIndex, int endIndex) {
    int length = length();
    checkBoundsBeginEnd(beginIndex, endIndex, length);
    if (beginIndex == 0 && endIndex == length) {
        return this;
    }
    int subLen = endIndex - beginIndex;
    return isLatin1() ? StringLatin1.newString(value, beginIndex, subLen)
                      : StringUTF16.newString(value, beginIndex, subLen);
}
```

- 전 구간이면 `return this` — **복사 안 한다.**
- 아니면 `newString` 으로 **바이트 배열을 새로 복사한다.**\
  (Java 6까지는 원본 배열을 공유했다. 짧은 조각이 큰 원본을 붙잡아 누수가 나서 7에서 복사로 바뀌었다.\
  *이 연혁은 이 문서의 기준 소스로 확인하지 않았다 — 확인 필요.*)

비용 — `substring(i, j)` 는 **O(j-i) 복사**다. 루프에서 부분 문자열을 떼면 그만큼 복사가 쌓인다.

**불변이 주는 것 넷.**

| 얻는 것 | 왜 |
|---|---|
| 공유해도 안전 | 아무도 못 고치니 상수 풀이 성립한다 |
| 스레드 안전 | 동기화 없이 여러 스레드가 읽어도 된다 |
| 해시 캐시 | `hashCode` 를 한 번 계산해 필드에 저장해 둘 수 있다 (`private int hash`) |
| `Map` 키로 안전 | 키를 넣은 뒤 내용이 바뀌어 못 찾는 일이 없다 |

### (2) 상수 풀 — 컴파일러가 접을 수 있으면 접는다

**언제 쓰나** — `==` 로 문자열을 비교하는 코드를 볼 때마다.

```text
소스                          컴파일러가 하는 일              실행 시 결과

"hel" + "lo"          --->    상수 식 -> "hello" 로 접음      비치본을 그대로
PREFIX + "lo"         --->    PREFIX 가 static final 상수     비치본을 그대로
 (static final)                -> 역시 접음
dynamic + "lo"        --->    접을 수 없음 -> 런타임 연결      새 복사본
 (그냥 static 필드)
```

`javap -c` 가 그 접기를 보여 준다(JDK 21.0.5, 출력 그대로).

```text
  static java.lang.String litPlusLit();
    Code:
       0: ldc           #7                  // String hello
       2: areturn

  static java.lang.String finalPlusLit();
    Code:
       0: ldc           #7                  // String hello
       2: areturn

  static java.lang.String varPlusLit();
    Code:
       0: getstatic     #11                 // Field dynamic:Ljava/lang/String;
       3: invokedynamic #15,  0             // InvokeDynamic #0:makeConcatWithConstants:(Ljava/lang/String;)Ljava/lang/String;
       8: areturn
```

그림 해설 (한 단계씩):

- 앞의 두 메서드는 `+` 가 **사라지고** `ldc #7` 하나만 남았다 — 연결이 컴파일 타임에 끝났다.
- `#7` 은 **상수 풀 항목 번호**다. `main` 안의 리터럴 `"hello"` 도 같은 `#7` 을 쓴다.\
  그래서 `litPlusLit() == "hello"` 가 `true` 다.
- 세 번째만 런타임 연결이 남았다(`invokedynamic` — 자세한 것은 [`../36-stringbuilder-and-concat/`](../36-stringbuilder-and-concat/)).

실행 결과:

```text
1) 리터럴 둘        a == b : true
2) new String      a == c : false
   equals                 : true
   c.intern() == a        : true
3) 리터럴 + 리터럴  a == d : true
4) static final + 리터럴 a == e : true
5) 변수 + 리터럴    a == f : false
   f.equals(a)            : true
   f.intern() == a        : true
6) StringBuilder    a == g : false
```

비용 — 접히는 연결은 **런타임 비용 0**이다. 접히지 않는 연결은 객체 하나.

### (3) `intern()` — 복사본을 들고 가서 비치본으로 바꿔 받기

**언제 쓰나** — 같은 내용의 문자열이 대량으로 만들어져 메모리를 먹을 때. 그 외에는 거의 안 쓴다.

```text
  f = "hel" + dynamic   (복사본 #2)

   f.intern() 호출
        |
        v
  풀에 "hello" 가 있나?  --- 있다 ---> 비치본의 번호표를 돌려준다
        |                             (f 자신은 그대로 남아 있다)
       없다
        |
        v
  f 를 풀에 넣고 f 를 돌려준다
```

JDK 21 소스의 javadoc이 그대로 말한다(원문 인용).

> When the intern method is invoked, if the pool already contains a string equal to this `String`
> object as determined by the `equals(Object)` method, then the string from the pool is returned.
> Otherwise, this `String` object is added to the pool and a reference to this `String` object is returned.
>
> It follows that for any two strings `s` and `t`, `s.intern() == t.intern()` is `true`
> if and only if `s.equals(t)` is `true`.

- **`intern()` 은 원본을 바꾸지 않는다.** 반환값을 받아야 의미가 있다.
- 마지막 문장이 `intern()` 의 계약 전부다 — 내용이 같으면 `intern()` 결과의 `==` 가 참이다.

비용 — 네이티브 호출 + 풀 조회. `equals` 비교가 들어가므로 **공짜가 아니다.**\
대량 데이터에서 메모리를 아끼려고 쓰는 것이고, `==` 를 쓰려고 쓰는 것이 아니다.

### (4) `length()` 는 **UTF-16 코드 단위**를 센다

**언제 쓰나** — 글자 수를 세거나, 자르거나, 뒤집을 때. 이모지가 들어오면 전부 깨진다.

```text
"a😀b" 를 자바가 담는 방식

  index    0        1        2        3
         +------+--------+--------+------+
         | 'a'  | D83D   | DE00   | 'b'  |
         +------+--------+--------+------+
           1칸    <--- 이모지 하나 --->  1칸
                  (서로게이트 쌍 2칸)

  length()       = 4    <- 사람이 세면 3
  codePointCount = 3
```

실행 결과 (JDK 21.0.5 — 17·25 동일):

```text
섞음   = "a😀b"
  length()          = 4
  codePointCount    = 3
  char 단위          = U+0061 U+D83D U+DE00 U+0062 
  코드포인트 단위     = U+0061 U+1F600 U+0062 
```

그림 해설 (한 단계씩):

- `char` 는 **16비트**라 U+FFFF 를 넘는 문자를 담지 못한다.
- 그래서 이모지 하나가 **서로게이트 쌍**이라 불리는 `char` 두 개로 쪼개져 들어간다.
- `length()` 는 그 `char` 칸 수를 센다 — 사람이 세는 글자 수가 아니다.
- 한글은 U+AC00~U+D7A3 이라 **한 칸**이다 — `"가나다".length()` 는 `3` 이다(실행으로 확인).\
  그래서 한글만 테스트하면 이 문제가 안 보인다.

`substring` 으로 반쪽만 떼면 이렇게 된다(실행 출력 그대로).

```text
emoji.charAt(0) 단독 출력 = [?]
emoji.substring(0,1)      = [?]  length=1
emoji.substring(0,1).equals(emoji) = false
Character.isHighSurrogate(emoji.charAt(0)) = true
Character.isLowSurrogate(emoji.charAt(1))  = true
```

- 반쪽 서로게이트는 **어떤 문자도 아니다** — 콘솔에 `?` 로 찍힌다.
- 예외도 경고도 없다. **깨진 문자열이 그대로 DB에 들어간다.**

비용 — `codePointCount` 는 전체를 훑으므로 O(n)이다. `length()` 는 O(1)이다.\
그래서 "정확한 글자 수"는 공짜가 아니다.

> **코드 단위(code unit)** — 문자 인코딩이 다루는 고정 크기 조각. 자바 `char` = UTF-16 코드 단위 1개.\
> 예: 이모지 하나는 코드 단위 2개다.

> **코드 포인트(code point)** — 유니코드가 문자 하나에 붙인 번호.\
> 예: 😀 의 코드 포인트는 U+1F600 하나이고, 그것이 코드 단위 둘(U+D83D U+DE00)로 저장된다.

> **서로게이트 쌍(surrogate pair)** — U+FFFF 를 넘는 코드 포인트를 UTF-16으로 담기 위한 두 칸짜리 표현.\
> 예: 앞칸(high) U+D800~U+DBFF, 뒤칸(low) U+DC00~U+DFFF. 둘이 붙어야만 의미가 있다.

## 문법 — 형태와 규칙

직접 쓴 최소 예제다. 묻는 것 하나만 남겼다.

### 만드는 네 가지 방법

```java
String a = "hello";                                  // 리터럴 — 비치본
String c = new String("hello");                      // 복사본 (쓰지 말 것)
String f = var + "lo";                               // 런타임 연결 — 복사본
String g = new StringBuilder("hel").append("lo").toString();  // 복사본
```

- **`new String(...)` 은 쓸 이유가 없다.** 객체 하나를 더 만들 뿐이다.
- 예외적으로 쓰는 자리: `new String(byte[], Charset)` 처럼 **다른 표현에서 변환**할 때.

### 자르고 다듬는 메서드

| 메서드 | 하는 일 | 함정 |
|---|---|---|
| `substring(b)` / `substring(b, e)` | 조각을 **복사해** 돌려준다 | `b > e` 면 예외. 전 구간이면 `this` |
| `trim()` | 양끝에서 **U+0020 이하** 문자를 제거 | 유니코드 공백(전각 공백)을 못 지운다 |
| `strip()` | 양끝에서 **유니코드 공백**을 제거 (11+) | 제어문자 U+0000 은 못 지운다 |
| `isEmpty()` | 길이가 0인가 | 공백만 있는 문자열은 `false` |
| `isBlank()` | 비었거나 **공백뿐인가** (11+) | 〃 판정이 `strip` 기준이다 |
| `split(regex)` | **정규식**으로 쪼갠다 | 인자가 정규식이다. 뒤쪽 빈 조각을 버린다 |
| `chars()` | `IntStream` 을 돌려준다 (8+) | `char` 스트림이 아니라 **`int`** 스트림 |
| `repeat(n)` | n번 이어 붙인다 (11+) | `n < 0` 이면 예외 |

`trim` 과 `strip` 이 **서로를 못 덮는다** — 세 코드 포인트로 확인한 실행 결과다.

```text
원본   U+2003 U+0068 U+0069 U+2003
  trim()  -> U+2003 U+0068 U+0069 U+2003   (len 4)
  strip() -> U+0068 U+0069   (len 2)
  isWhitespace(U+2003) = true
원본   U+0000 U+0068 U+0069 U+0000
  trim()  -> U+0068 U+0069   (len 2)
  strip() -> U+0000 U+0068 U+0069 U+0000   (len 4)
  isWhitespace(U+0000) = false
원본   U+00A0 U+0068 U+0069 U+00A0
  trim()  -> U+00A0 U+0068 U+0069 U+00A0   (len 4)
  strip() -> U+00A0 U+0068 U+0069 U+00A0   (len 4)
  isWhitespace(U+00A0) = false
```

- `U+2003`(em space)은 **`strip` 만** 지운다 — `trim` 의 기준(U+0020 이하)보다 크다.
- `U+0000`(NUL)은 **`trim` 만** 지운다 — 유니코드 공백이 아니다.
- `U+00A0`(줄바꿈 없는 공백)은 **둘 다 못 지운다** — `Character.isWhitespace` 가 `false` 다.\
  사용자가 붙여넣기로 흘려보내는 대표적인 문자다. 이것만 따로 지우려면 명시적으로 `replace` 해야 한다.

`split` 의 세 가지 함정 (실행 출력 그대로):

```text
"a,b,,c,,".split(",")      = [a, b, , c]  len=4
"a,b,,c,,".split(",", -1)  = [a, b, , c, , ]  len=6
",,a".split(",")           = [, , a]  len=3
"".split(",")              = []  len=1
"a.b".split(".")           = []  len=0
"a.b".split("\\.")         = [a, b]
```

- **뒤쪽 빈 조각은 버려진다** — 앞쪽은 안 버린다. 비대칭이다.\
  전부 살리려면 `split(regex, -1)`.
- `"".split(",")` 의 길이가 **0이 아니라 1**이다. 빈 문자열 하나가 든 배열이 나온다.
- `split(".")` 은 **정규식의 `.`**(아무 문자)라 전부 쪼개지고 결과가 빈 배열이다.\
  문자 그대로 쓰려면 `split("\\.")`.\
  정규식 자체는 [**37번 주제**](../37-regex/)가 정본이다.

### 비교하는 메서드

```text
new String("A") == "A"          : false
new String("A").equals("A")     : true
switch(new String("A"))         : 우수
"a".equalsIgnoreCase("A")       : true
"a".compareTo("A")              : 32
"apple".compareTo("banana")     : -1
"a".contentEquals(new StringBuilder("a")) : true
"a".equals(new StringBuilder("a"))        : false
"A".equals(null)               : false
```

- `switch` 는 **`equals` 로 비교**한다 — `==` 가 아니다. 그래서 복사본도 잘 매치된다.
- `compareTo` 는 **차이값**을 돌려준다. `"a" - "A" = 32`. 0인지만 보고 쓴다.
- `equals` 는 타입까지 보므로 `StringBuilder` 와는 **항상 `false`** 다. `contentEquals` 를 쓴다.
- `"A".equals(null)` 은 `false` 다 — **리터럴을 왼쪽에 두면 NPE가 안 난다.**

## 어디서 틀리나

이 주제의 값어치는 전부 여기 있다. 다섯 다 **에러 없이, 또는 엉뚱한 줄에서 터진다.**

### 1. `==` 로 문자열을 비교한다

```text
왼쪽 — 테스트: 리터럴끼리                  오른쪽 — 운영: 입력에서 온 값
+---------------------------------+      +---------------------------------+
| String role = "ADMIN";          |      | String role = req.get("role");  |
| if (role == "ADMIN") { ... }    |      | if (role == "ADMIN") { ... }    |
|                                 |      |                                 |
| 둘 다 비치본 -> true            |      | 복사본 vs 비치본 -> false       |
| 테스트 초록                      |      | 권한 분기를 안 탄다              |
+---------------------------------+      +---------------------------------+
```

- 왼쪽이 통과하는 것은 **컴파일러가 접어 준 덕**이지 코드가 맞아서가 아니다.
- 오른쪽은 **에러도 로그도 없다** — 조건이 그냥 거짓이 된다.
- 보안 분기에서 이 실수가 나면 **권한을 못 받는 쪽**으로 틀리는 게 그나마 다행이고,
  `!=` 를 썼다면 **반대로 열린다.**

### 2. `equals` 의 왼쪽에 `null` 이 올 수 있는 값을 둔다

```text
null.equals("A")               -> Cannot invoke "String.equals(Object)" because "<local2>" is null
switch(null)                   -> Cannot invoke "String.hashCode()" because "<local1>" is null
```

- 두 번째가 재미있다 — `switch` 에 `null` 을 넣으면 **`hashCode()` 에서** NPE가 난다.
- 소스에는 `hashCode` 라는 글자가 없다. `javap -c` 가 왜 그런지 보여 준다(출력 그대로).

```text
  static java.lang.String grade(java.lang.String);
    Code:
       0: aload_0
       1: astore_1
       2: iconst_m1
       3: istore_2
       4: aload_1
       5: invokevirtual #7                  // Method java/lang/String.hashCode:()I
       8: lookupswitch  { // 2
                    65: 36
                    66: 50
               default: 61
          }
      36: aload_1
      37: ldc           #13                 // String A
      39: invokevirtual #15                 // Method java/lang/String.equals:(Ljava/lang/Object;)Z
```

- `switch(String)` 은 **`hashCode` 로 후보를 좁히고 `equals` 로 확인**하는 두 단계로 컴파일된다.
- 그래서 `null` 은 첫 단계에서 터진다.\
  (Java 21의 `switch` 패턴 매칭에서는 `case null` 을 쓸 수 있다 — [**23번 주제**](../23-switch-pattern-matching/).)
- 습관: **리터럴을 왼쪽에** 두거나 `Objects.equals(a, b)` 를 쓴다.

### 3. `substring` 의 인덱스를 뒤집는다 — **예외 메시지가 버전마다 다르다**

```text
JDK 21.0.5 · 25.0.1
substring(2,1) -> java.lang.StringIndexOutOfBoundsException: Range [2, 1) out of bounds for length 5
substring(6)   -> java.lang.StringIndexOutOfBoundsException: Range [6, 5) out of bounds for length 5

JDK 17.0.13
substring(2,1) -> java.lang.StringIndexOutOfBoundsException: begin 2, end 1, length 5
substring(6)   -> java.lang.StringIndexOutOfBoundsException: begin 6, end 5, length 5
```

- **같은 코드, 같은 예외 클래스, 다른 메시지.** 이 문서에서 버전이 갈린 유일한 자리다.
- 함의: **예외 메시지를 파싱하거나 테스트에서 문자열로 단언하면 JDK를 올릴 때 깨진다.**
- `substring(5)`(길이와 같은 인덱스)는 **예외가 아니라 빈 문자열**이다 — 경계가 하나 차이다.

### 4. `length()` 로 글자 수를 센다

```text
왼쪽 — 한글·영문만                        오른쪽 — 이모지가 들어옴
+---------------------------------+      +---------------------------------+
| "가나다".length() = 3           |      | "a😀b".length() = 4             |
| 닉네임 최대 3자 검사 통과        |      | 사람이 세면 3자인데 4로 센다     |
|                                 |      | substring(0,3) 으로 자르면       |
| 테스트 초록                      |      | 이모지가 반쪽만 남는다           |
+---------------------------------+      +---------------------------------+
```

- **한글만 테스트하면 절대 안 보인다.** 한글은 코드 단위 하나다.
- 글자 수를 세려면 `s.codePointCount(0, s.length())`.
- 안전하게 자르려면 `s.substring(0, s.offsetByCodePoints(0, n))` — 실행으로 확인한 결과다.

```text
s.substring(0,2) = [a?]  length=2
  그 조각의 char = U+0061 U+D83D 
예외가 났나? 아니오 — 조용히 반쪽이 남는다
s.offsetByCodePoints(0, 2) = 3
s.substring(0, s.offsetByCodePoints(0, 2)) = [a😀]
```

  **예외가 안 난다**는 것이 이 절의 핵심이다 — 반쪽 서로게이트가 그대로 흘러간다.
- 다만 **코드 포인트도 "사람이 보는 글자"가 아니다.** 국기·가족 이모지는 코드 포인트 여러 개가 한 글자로 보인다.\
  거기까지 맞추려면 `java.text.BreakIterator` 가 필요하다. *(안 돌려 봤다.)*
- 참고로 `StringBuilder.reverse()` 는 **서로게이트 쌍을 보존한다** — 실행하면 `a😀b` 가 `b😀a` 가 된다.\
  직접 `char` 배열을 뒤집는 코드는 그러지 못한다.

### 5. `split` 결과의 길이를 믿는다

```text
"a,b,,c,,".split(",")      = [a, b, , c]  len=4      <- 뒤쪽 빈 칸 둘이 사라졌다
"a,b,,c,,".split(",", -1)  = [a, b, , c, , ]  len=6
"".split(",")              = []  len=1               <- 0이 아니다
```

- CSV 한 줄을 `split(",")` 으로 쪼개고 **열 개수로 검증**하면, 마지막 열들이 비었을 때 통과해 버린다.
- 그리고 부족한 열을 배열 인덱스로 읽는 순간 `ArrayIndexOutOfBoundsException` 이
  **파싱한 줄이 아니라 사용하는 줄**에서 난다.
- 고치는 법: **항상 `split(regex, -1)`** 로 쪼개고 길이를 검사한다.

## 구현 세부사항 대 언어 보장

이 주제에서 가장 헷갈리는 경계다. "리터럴은 풀에 들어간다"까지는 명세이고, 그 아래는 전부 구현이다.

```text
     언어(JLS)가 보장하는 것                    구현(HotSpot)이 정하는 것
  +--------------------------------+        +--------------------------------+
  | 리터럴은 같은 인스턴스다        |        | 풀이 어디에 있나 (힙/메타스페이스)|
  | 상수 식의 값도 인터닝된다       |        | 풀 해시 테이블 크기             |
  |                                |        |  (-XX:StringTableSize)         |
  | intern() 의 계약:              |        | 내부 저장이 byte[] 인지 char[] |
  |  s.intern()==t.intern()        |        |  (-XX:+CompactStrings)         |
  |  iff s.equals(t)               |        | 풀 항목이 GC 되는 시점          |
  +--------------------------------+        +--------------------------------+
   소스만 보고 판정할 수 있다                  JVM 옵션·버전으로 바뀐다
```

**언어 보장** — JLS SE 21 §3.10.5 원문.

> At run time, a string literal is a reference to an instance of class `String` (§4.3.3) that denotes
> the string represented by the string literal.
>
> Moreover, a string literal always refers to the *same* instance of class `String`. This is because
> string literals - or, more generally, strings that are the values of constant expressions (§15.29) -
> are "interned" so as to share unique instances, as if by execution of the method `String.intern` (§12.5).

- 보장되는 것은 **리터럴과 상수 식**뿐이다.
- `"hel" + "lo"` 는 상수 식이라 보장 대상이고, `dynamic + "lo"` 는 **아니다.**
- `static final String PREFIX = "hel";` 로 만든 `PREFIX + "lo"` 는 **보장 대상이다** —\
  `PREFIX` 가 상수 변수라 그 연결이 상수 식이 되기 때문이다(실행으로 확인: `a == e` 가 `true`).
- 반대로 `static String dynamic = "hel";`(`final` 없음)은 상수 변수가 아니라 **보장이 사라진다**(`a == f` 가 `false`).\
  **`final` 한 글자가 `==` 의 결과를 뒤집는다.**

`intern()` 의 계약도 javadoc이 명시한다 — "`s.intern() == t.intern()` is `true` if and only if `s.equals(t)` is `true`".\
즉 **내가 직접 `intern()` 을 부른 것들끼리는** `==` 가 성립한다. 부르지 않은 것과는 아무 보장이 없다.

**구현 세부** — 이 머신의 JVM에게 직접 물어본 것이다.

```text
$ java -XX:+PrintFlagsFinal -version | grep -Ei 'CompactStrings|StringTableSize|StringDedup'
     bool CompactStrings                           = true                                   {pd product} {default}
     uint StringDeduplicationAgeThreshold          = 3                                         {product} {default}
    uintx StringTableSize                          = 65536                                     {product} {default}
     bool UseStringDeduplication                   = false                                     {product} {default}
```

- **풀의 크기가 플래그다.** 명세는 풀의 구현을 정하지 않는다.
- `CompactStrings` 가 켜져 있으면 `String` 이 내부적으로 **`byte[]` 에 LATIN-1 또는 UTF-16** 으로 저장된다.\
  JDK 21 소스가 그 필드를 그대로 보여 준다.

```java
// JDK 21.0.5  java.base/java/lang/String.java  158·171·174행 — 실제 소스 그대로
private final byte[] value;
private final byte coder;
private int hash; // Default to 0
```

- `char[]` 가 아니라 **`byte[]` 다.** Java 9의 compact strings(JEP 254)로 바뀌었다.\
  ASCII만 든 문자열은 글자당 1바이트, 아니면 2바이트다.
- **하지만 이것은 관측 가능한 동작을 바꾸지 않는다** — `length()`·`charAt` 은 여전히 UTF-16 코드 단위 기준이다.\
  달라지는 것은 메모리 사용량뿐이다.
- `hash` 필드가 `final` 이 아닌 이유는 **처음 `hashCode()` 를 부를 때 계산해 캐시**하기 때문이다.\
  불변이라 이 지연 계산이 안전하다.

**그래서 무엇을 코드가 의존해도 되나.**

| 의존해도 되는 것 | 의존하면 안 되는 것 |
|---|---|
| 리터럴끼리의 `==` (그래도 쓰지 말 것) | 런타임에 만든 문자열끼리의 `==` |
| `equals`·`compareTo`·`hashCode` 의 값 | `identityHashCode` — **실행마다 다르다**(확인함) |
| `length()` 가 코드 단위를 센다 | 내부가 `char[]` 라는 가정 |
| `intern()` 의 계약 | `intern()` 의 성능·풀 크기 |
| 예외 클래스 | **예외 메시지 문구**(17↔21에서 실제로 바뀌었다) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓰는 것 | 왜 |
|---|---|---|
| 내용 비교 | `equals` / `equalsIgnoreCase` | `==` 는 같은 객체인지를 묻는다 |
| `null` 일 수 있는 값 비교 | `Objects.equals(a, b)` | 양쪽 `null` 안전 |
| 빈 값 검사 | `isBlank()` (11+) | 공백만 있는 입력을 잡는다 |
| 사용자 입력 다듬기 | `strip()` | `trim` 은 유니코드 공백을 못 지운다 |
| 구분자로 쪼개기 | `split(regex, -1)` | 뒤쪽 빈 조각을 살린다 |
| 반복 연결 | `StringBuilder` | [`../36-stringbuilder-and-concat/`](../36-stringbuilder-and-concat/) |
| 글자 수 세기 | `codePointCount` | `length()` 는 코드 단위다 |
| 같은 문자열 대량 중복 | `intern()` 또는 `-XX:+UseStringDeduplication` | 메모리 목적일 때만 |
| 객체 만들기 | 리터럴 | `new String` 은 쓸 이유가 없다 |

판단 규칙 세 줄.

- **`String` 에 `==` 를 쓰는 코드는 전부 버그 후보다.** 예외는 `intern()` 을 명시적으로 부른 경우뿐이다.
- **"고쳤다"고 생각한 자리는 전부 반환값을 받았는지 본다.**
- **`length()` 를 글자 수로 쓰는 자리는 이모지 테스트 하나를 추가한다.**

## 핵심 문장

- 리터럴과 **상수 식**의 결과만 상수 풀에 들어간다 — 그 둘만 `==` 가 명세로 보장된다.
- `static final` 한 글자가 연결을 상수 식으로 만들어 `==` 의 결과를 **뒤집는다.**
- `String` 의 모든 "변경" 메서드는 **새 객체를 반환**하고, 바꿀 게 없으면 **자기 자신**을 돌려준다.
- `length()` 는 UTF-16 **코드 단위**를 센다 — 이모지 하나가 2로 세어지고, 한글만 테스트하면 안 보인다.
- `switch(String)` 은 `hashCode` + `equals` 로 컴파일되므로 `null` 을 넣으면 **`hashCode()` 에서** 터진다.

## 관련 자료

- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 35번)
- [`../36-stringbuilder-and-concat/`](../36-stringbuilder-and-concat/) — **경계: 여기는 「`String` 객체 하나가 무엇인가」까지,
  그쪽은 「여러 조각을 이어 붙일 때 컴파일러가 무엇을 하나」부터다.**\
  `+` 가 `invokedynamic` 이 되는 이야기는 전부 36번이다.
- [`../01-primitives-and-wrappers/`](../01-primitives-and-wrappers/) — **경계: `Integer` 캐시는 거기, 문자열 상수 풀은 여기.**\
  둘 다 "같은 값이면 같은 객체인가"를 묻지만 보장의 근거 조항이 다르다(§5.1.7 대 §3.10.5).
- [`../../../../data-representation/`](../../../../data-representation/) — ASCII·유니코드·문자 인코딩.\
  **경계: 그쪽은 「문자가 숫자로 어떻게 표현되나」까지, 여기는 「자바 `String` 이 그 표현 위에서 무엇을 세나」부터다.**
- [`../02-numeric-operations/`](../02-numeric-operations/) — `'A' + 'B'` 가 `131` 인 이유(이항 수치 승격)
- [**37번 주제**](../37-regex/)(정규식) — `split`·`replaceAll` 의 정규식 자체가 다뤄지는 곳
- [**27번 주제**](../27-equals-hashcode-contract/)([`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/)) — `equals`/`hashCode` 계약 일반
- [`../../언어-특성/README.md`](../../언어-특성/README.md) — GC·메모리. **문자열이 힙을 얼마나 먹는지는 거기**

## 용어 풀이

- **문자열 상수 풀** — 같은 내용의 `String` 을 하나만 두고 공유하는 JVM 저장소.
- **인터닝** — 같은 내용의 객체를 풀의 하나로 모으는 것. `intern()` 이 그 동작이다.
- **리터럴(string literal)** — 소스에 따옴표로 쓴 문자열. JLS가 인터닝을 보장하는 대상.
- **상수 식** — 컴파일 타임에 값이 확정되는 식. 리터럴 연결·상수 변수 연결이 여기 든다.
- **상수 변수(constant variable)** — `final` 이면서 컴파일 타임 상수로 초기화된 변수. `final` 이 없으면 아니다.
- **불변 객체** — 만들어진 뒤 내부 상태가 바뀌지 않는 객체. `String` 이 그렇다.
- **코드 단위 / 코드 포인트** — 인코딩의 고정 크기 조각 / 유니코드가 문자에 붙인 번호.
- **서로게이트 쌍** — U+FFFF 초과 문자를 UTF-16 두 칸으로 담는 방식. 반쪽만 있으면 깨진 문자다.
- **compact strings** — Java 9부터 `String` 내부를 `byte[]` + `coder` 로 저장하는 구현. 동작은 안 바뀌고 메모리만 준다.
- **`ldc`** — JVM 바이트코드 명령. 상수 풀 항목을 스택에 올린다. 같은 번호면 같은 객체다.
- **`lookupswitch`** — 흩어진 정숫값으로 분기하는 JVM 명령. `switch(String)` 의 해시 단계가 이것으로 컴파일된다.

## 더 들어가면

- **`identityHashCode` 는 실행마다 달라진다.** 같은 프로그램을 세 JDK에서 돌린 결과다.

```text
JDK 17: a=349885916 b=349885916 c=414493378 f=1984697014
JDK 21: a=692404036 b=692404036 c=1554874502 f=1846274136
JDK 25: a=2060468723 b=2060468723 c=622488023 f=1933863327
```

  `a` 와 `b` 가 매번 같은 것만 의미가 있다 — **값 자체는 로그에 남겨도 대조에 못 쓴다.**

- **`-XX:+UseStringDeduplication`** 은 GC가 같은 내용의 `char`/`byte` 배열을 **뒤늦게** 합쳐 주는 기능이다.\
  `intern()` 과 달리 `==` 는 여전히 거짓이다 — **배열만 공유하고 객체는 따로 남는다.**\
  기본값은 꺼짐(위 플래그 출력 확인). *(실제 동작은 안 돌려 봤다.)*
- **`String` 의 `hashCode` 는 `31 * h + c` 누적**이고 오버플로가 **의도된 동작**이다.\
  그래서 `"Aa"` 와 `"BB"` 의 해시가 둘 다 `2112` 로 같다(실행으로 확인) — 충돌은 정상이고, `equals` 가 최종 판정을 한다.
- **`String` 은 `final` 클래스**다. 상속해서 `equals` 를 깨뜨릴 수 없게 막은 것이고,\
  그 덕에 상수 풀·해시 캐시 같은 최적화가 성립한다.
