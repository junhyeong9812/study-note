# java/syntax/35 — `String`: 불변성·상수 풀·자주 쓰는 메서드 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **Temurin JDK 21.0.5 에서 실제로 돌려 얻은 것**이다.\
> 바이트코드는 `javap -c` 출력을, JDK 소스는 `lib/src.zip` 의 실파일을, JLS는 원문을 그대로 옮겼다.\
> 실행 파일명은 전부 `Ex.java` 로 고정했다 — 예외 트레이스에 그 이름이 박힌다.\
> 17.0.13 · 25.0.1 에서도 같은 프로그램을 돌렸다. **갈린 곳은 10번 하나**다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 여섯 줄의 `==` 를 예측하라

**출력** (JDK 21.0.5 — 17·25 동일)

```text
1) 리터럴 둘        a == b : true
2) new String      a == c : false
   equals                 : true
   c.intern() == a        : true
3) 리터럴 + 리터럴  a == d : true
6) StringBuilder    a == g : false
```

**여섯 줄의 출력**

- `a == b` -> **true**
- `a == c` -> **false**
- `a == d` -> **true**
- `a == g` -> **false**
- `c.equals(a)` -> **true**
- `c.intern() == a` -> **true**

```text
  a --+                            c --> [복사본 : hello]   (new 가 만든 것)
      +--> [비치본 : hello]
  b --+                            g --> [복사본 : hello]   (StringBuilder 가 만든 것)
  d --+  ("hel"+"lo" 가 접혀서
          비치본을 그대로 가리킨다)
```

**`a == d` 가 `true` 인 이유 — 바이트코드 명령 하나**

```text
  static java.lang.String litPlusLit();
    Code:
       0: ldc           #7                  // String hello
       2: areturn
```

- **`ldc #7`** 하나다. `+` 가 아예 사라졌다.
- `"hel" + "lo"` 는 **상수 식**이라 컴파일 타임에 `"hello"` 로 접힌다.
- `#7` 은 상수 풀 항목 번호이고, `main` 안의 리터럴 `"hello"` 도 **같은 `#7`** 을 쓴다.\
  같은 항목이므로 실행 시 같은 객체다.

**`g` 만 `false` 가 되는 이유**

- `StringBuilder.toString()` 은 **새 `String` 객체를 만들어 돌려준다.**
- 상수 풀을 보지도 않고, 등록하지도 않는다.
- `c`(= `new String`)와 같은 부류다 — **런타임에 만들어진 것은 전부 복사본**이다.
- `g.intern() == a` 로 하면 `true` 가 된다(같은 원리를 `f` 로 확인했다 — 2번).

> **상수 식(constant expression)** — 컴파일 타임에 값이 확정되는 식(JLS §15.29).\
> 예: `"hel" + "lo"` 는 상수 식이고, `sb.toString()` 은 아니다.

### 2. `final` 한 글자가 결과를 뒤집는다

**출력**

```text
4) static final + 리터럴 a == e : true
5) 변수 + 리터럴    a == f : false
   f.equals(a)            : true
   f.intern() == a        : true
```

또 다른 프로그램에서 같은 것을 직접 찍은 결과:

```text
true
true
false
```

(위에서부터 `litPlusLit() == "hello"` · `finalPlusLit() == "hello"` · `varPlusLit() == "hello"`)

**두 줄의 출력**

- `e == "hello"` -> **true**
- `f == "hello"` -> **false**

**`final` 하나가 차이를 만드는 이유**

```text
static final String PREFIX = "hel";        static String DYNAMIC = "hel";

  PREFIX 는 상수 변수다                      DYNAMIC 은 그냥 필드다
  -> PREFIX + "lo" 가 상수 식이다             -> 값이 언제 바뀔지 컴파일러가 모른다
  -> 컴파일 타임에 "hello" 로 접힌다           -> 런타임에 이어 붙여야 한다
  -> 비치본을 가리킨다                        -> 새 복사본이 생긴다
```

- **상수 변수(constant variable)** 라는 개념 때문이다(JLS §4.12.4) — `final` + 컴파일 타임 상수 초기화.
- 상수 변수가 들어간 연결은 **상수 식**이 되고, 상수 식의 값은 JLS §3.10.5가 인터닝을 보장한다.
- `final` 을 떼는 순간 그 보장이 **통째로 사라진다.**

**`javap -c` 로 본 차이**

```text
  static java.lang.String finalPlusLit();       static java.lang.String varPlusLit();
    Code:                                         Code:
       0: ldc  #7   // String hello                  0: getstatic #11  // Field dynamic:...
       2: areturn                                    3: invokedynamic #15,  0
                                                        // makeConcatWithConstants
                                                     8: areturn
```

- 왼쪽은 **명령 두 개**로 끝난다 — 연결이 없다.
- 오른쪽은 필드를 읽고 **런타임 연결**을 한다.
- `+` 가 소스에는 양쪽 다 있는데 **클래스 파일에는 한쪽에만** 있다.

**`f` 를 `e` 와 같은 객체로 만들려면**

- **`f.intern()`** 을 부르고 그 반환값을 쓴다.
- 실행으로 확인: `f.intern() == a` 가 `true`.
- 단 `f` 자신은 그대로다 — `intern()` 은 **새 참조를 돌려줄 뿐** 원본을 바꾸지 않는다.

### 3. 이 세 줄 뒤 `u` 는 무엇인가

**출력**

```text
u.replace('l','L')  = heLLo   원본 u = hello
u.toUpperCase()     = HELLO   원본 u = hello
u.concat("!")       = hello!  원본 u = hello
바꿀 게 없는 replace 가 같은 객체? true
substring(0) 이 같은 객체?         true
u.toString() 이 같은 객체?         true
```

**세 줄의 출력**

- `System.out.println(u)` -> **hello** (하나도 안 바뀌었다)
- `u.replace('z','Z') == u` -> **true**
- `u.substring(0) == u` -> **true**

**왜 `u` 가 안 바뀌는가**

```text
u.toUpperCase();          반환값을 안 받았다

  u --> ["hello"]                      u --> ["hello"]     <- 그대로
                                             ["HELLO"]     <- 만들어졌다가 아무도 안 잡아서 버려짐
```

- `String` 에는 **내용을 바꾸는 메서드가 없다.** 전부 새 객체를 반환한다.
- `u.toUpperCase();` 한 줄은 **객체 하나를 만들었다 버리는 것** 이상도 이하도 아니다.
- 컴파일 경고도 안 난다 — 반환값을 무시하는 것은 자바에서 합법이다.\
  IDE의 "result of method is ignored" 검사가 잡아 주는 정도다.

**마지막 두 줄이 `true` 인 이유와 안전한 이유**

```java
// JDK 21.0.5  java.base/java/lang/String.java  2832~2841행 — 실제 소스 그대로
public String substring(int beginIndex, int endIndex) {
    int length = length();
    checkBoundsBeginEnd(beginIndex, endIndex, length);
    if (beginIndex == 0 && endIndex == length) {
        return this;
    }
    ...
}
```

- **바꿀 것이 없으면 자기 자신을 돌려준다.** 새 객체를 만들 이유가 없기 때문이다.
- `replace` 도 같은 최적화를 한다(찾는 문자가 없으면 `this`).
- **불변이라서 안전하다** — 받은 쪽이 고칠 수 없으니 공유해도 문제가 없다.\
  `StringBuilder` 가 이런 최적화를 못 하는 이유가 바로 이것이다(가변이라 공유하면 위험하다).
- 함의: **`==` 의 결과가 메서드의 내부 최적화에 달려 있다.** 이것만으로도 `==` 를 쓰면 안 되는 이유가 된다.

### 4. `trim` 과 `strip` 중 무엇이 지우는가

**출력** (JDK 21.0.5 — 17·25 동일)

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

**세 문자 각각**

| 문자 | `trim()` | `strip()` | 왜 |
|---|---|---|---|
| U+2003 (em space) | **못 지운다** | **지운다** | U+0020 보다 크지만 유니코드 공백이다 |
| U+0000 (NUL) | **지운다** | **못 지운다** | U+0020 이하지만 유니코드 공백이 아니다 |
| U+00A0 (NBSP) | 못 지운다 | 못 지운다 | 둘 다의 기준에서 벗어난다 |

```text
  trim 의 기준                          strip 의 기준
  +--------------------------+        +--------------------------+
  | 코드 포인트 <= U+0020     |        | Character.isWhitespace   |
  | (제어문자 포함)           |        | (전각 공백 등 포함)       |
  +--------------------------+        +--------------------------+
        U+0000 O · U+2003 X                U+0000 X · U+2003 O

              둘 다 U+00A0 는 X — 서로를 못 덮는다
```

**둘 다 못 지우는 문자**

- **U+00A0**(줄바꿈 없는 공백, non-breaking space).
- `Character.isWhitespace(' ')` 가 **`false`** 이기 때문이다(실행으로 확인).\
  "줄을 끊지 않는" 공백이라 유니코드가 공백류로 분류하지 않는다.
- 웹 페이지·워드 문서에서 복사해 붙여넣은 값에 자주 섞인다 —\
  **화면에는 공백으로 보이는데 `strip` 이 안 먹는다.** 검색·비교가 조용히 실패한다.
- 잡으려면 명시적으로: `s.replace(' ', ' ').strip()`. *(이 조합은 안 돌려 봤다.)*

**두 기준**

- `trim` — 코드 포인트가 **U+0020(공백) 이하**인 문자를 양끝에서 제거. Java 1.0부터의 옛 정의다.
- `strip` — **`Character.isWhitespace`** 가 참인 문자를 양끝에서 제거. Java 11부터.

**`isEmpty` 와 `isBlank`**

```text
"".isEmpty()   = true   "".isBlank()   = true
" ".isEmpty()  = false  " ".isBlank()  = true
"\t\n".isBlank() = true
```

- `" "` 에 대해 `isEmpty()` 는 **`false`**, `isBlank()` 는 **`true`**.
- 사용자 입력 검증에서 원하는 것은 거의 항상 **`isBlank()`** 다.\
  `isEmpty()` 로 검사하면 스페이스 하나짜리 이름이 통과한다.

### 5. `split` 결과의 길이

**출력**

```text
"a,b,,c,,".split(",")      = [a, b, , c]  len=4
"a,b,,c,,".split(",", -1)  = [a, b, , c, , ]  len=6
",,a".split(",")           = [, , a]  len=3
"".split(",")              = []  len=1
"a.b".split(".")           = []  len=0
"a.b".split("\\.")         = [a, b]
```

**네 결과**

| 식 | 원소 | 길이 |
|---|---|---|
| `"a,b,,c,,".split(",")` | `"a"`, `"b"`, `""`, `"c"` | **4** |
| `"a,b,,c,,".split(",", -1)` | `"a"`, `"b"`, `""`, `"c"`, `""`, `""` | **6** |
| `"".split(",")` | `""` (빈 문자열 하나) | **1** |
| `"a.b".split(".")` | 없음 | **0** |

**앞쪽과 뒤쪽 처리가 다른 이유**

```text
"a,b,,c,,"  를 쪼개면 논리적으로 6조각

  [a][b][ ][c][ ][ ]
                ^^^^^
                인자 없는 split 은 뒤쪽 빈 조각을 버린다 (limit = 0)

",,a"  를 쪼개면 3조각

  [ ][ ][a]
   ^^^^^^
   앞쪽 빈 조각은 안 버린다
```

- `split(regex)` 는 `split(regex, 0)` 이고, **limit 0은 "뒤쪽 빈 문자열을 제거"** 를 뜻한다.
- 앞쪽·중간 빈 조각은 제거 대상이 아니다 — 그래서 비대칭이다.
- 전부 살리려면 **`split(regex, -1)`**.

**`"".split(",")` 의 길이가 `0` 이 아닌 위험**

- 결과는 **빈 문자열 하나가 든 배열**이다(`Arrays.toString` 이 `[]` 로 찍히지만 `length` 는 1).
- 그래서 `if (parts.length == 0)` 로 "빈 입력"을 잡으려는 코드는 **절대 참이 안 된다.**
- 빈 줄 하나가 "필드 한 개짜리 레코드"로 파싱되어 아래로 흘러간다 — **조용한 실패**다.
- 잡으려면 `s.isBlank()` 를 먼저 검사한다.

**`split(".")` 이 빈 배열을 내는 이유**

- 인자가 **정규식**이고 정규식의 `.` 은 **아무 문자 하나**다.
- 그래서 `"a.b"` 의 모든 문자가 구분자가 되고, 조각은 전부 빈 문자열이 된다.
- 그 다음 limit 0 규칙이 **뒤쪽 빈 조각을 전부 제거**하므로 남는 게 없다 -> 길이 0.
- 문자 그대로 쓰려면 `split("\\.")` 또는 `split(Pattern.quote("."))`.

> **조용한 실패(silent failure)** — 에러 없이 정상처럼 끝나는데 결과만 틀린 것.\
> 예: CSV 마지막 열이 비어서 `split` 이 짧은 배열을 냈는데 길이 검사를 통과하는 것.

### 6. 이모지가 섞이면

**출력** (JDK 21.0.5 — 17·25 동일)

```text
s              = a😀b
s.length()     = 4
s.codePointCount= 3
"가나다".length() = 3
s.substring(0,2) = [a?]  length=2
  그 조각의 char = U+0061 U+D83D 
예외가 났나? 아니오 — 조용히 반쪽이 남는다
s.offsetByCodePoints(0, 2) = 3
s.substring(0, s.offsetByCodePoints(0, 2)) = [a😀]
```

**네 줄의 출력**

- `s.length()` -> **4**
- `s.codePointCount(0, s.length())` -> **3**
- `"가나다".length()` -> **3**
- `s.substring(0, 2)` -> **`a` + 반쪽 서로게이트** (콘솔에 `a?` 로 찍힌다)

```text
  index    0        1        2        3
         +------+--------+--------+------+
         | 'a'  | D83D   | DE00   | 'b'  |
         +------+--------+--------+------+
                 <--- 😀 하나 --->
  substring(0,2) 가 여기서 자른다 ---^
                                    반쪽만 떼어 간다
```

**`length()` 가 세는 단위**

- **UTF-16 코드 단위(code unit)** 다. `char` 한 칸이다.
- 유니코드 문자 하나(코드 포인트)가 항상 한 칸이 아니다 — U+FFFF 를 넘으면 두 칸이다.
- `length()` 가 O(1)인 이유도 여기 있다 — 배열 길이를 그대로 읽는다.\
  반면 `codePointCount` 는 전체를 훑어야 해서 O(n)이다.

**한글만으로 테스트하면 안 보이는 이유**

- 한글 음절은 U+AC00~U+D7A3 이라 **전부 코드 단위 하나**다.
- 그래서 `"가나다".length() == 3` 이고, 사람이 세는 수와 일치한다.
- 이모지·일부 한자 확장·고대 문자만 두 칸이 된다.
- 검증 코드의 테스트 데이터에 **이모지 한 글자**를 넣는 것만으로 이 문제가 드러난다.

**반으로 자르면 예외가 나는가**

- **안 난다.** 이것이 핵심이다.
- `substring(0, 2)` 는 인덱스가 유효하므로 정상 반환하고, **반쪽 서로게이트가 든 문자열**이 나온다.
- 그 문자열은 어떤 문자도 표현하지 않는다 — 콘솔에 `?`, DB에는 깨진 값으로 들어간다.
- 안전하게 자르려면 `s.substring(0, s.offsetByCodePoints(0, n))` (실행으로 확인).
- 다만 **코드 포인트 단위도 "사람이 보는 글자"는 아니다** — 국기·가족 이모지는 코드 포인트 여럿이 한 글자다.\
  거기까지 맞추려면 `java.text.BreakIterator` 가 필요하다. *(안 돌려 봤다.)*

### 7. `intern()` 이 보장하는 것

**자기 자신을 바꾸는가**

- **안 바꾼다.** `String` 은 불변이라 바꿀 방법이 없다.
- **새 참조를 돌려준다.** 반환값을 받지 않으면 아무 의미가 없다 — 3번의 `toUpperCase()` 와 같은 함정이다.
- 실행으로 확인: `f.intern() == a` 가 `true` 이지만 `f == a` 는 여전히 `false`.

**필요충분조건**

- **`s.equals(t)`** 다.
- JDK 21 `String.java` javadoc 원문:

> It follows that for any two strings `s` and `t`, `s.intern() == t.intern()` is `true`
> if and only if `s.equals(t)` is `true`.

- 즉 **양쪽 다 `intern()` 을 불렀을 때만** 성립한다.\
  한쪽만 부르면 아무 보장이 없다(다만 다른 쪽이 리터럴이면 이미 풀에 있으므로 사실상 성립한다).

**어디에 적혀 있는가**

- `String.intern()` 의 **javadoc**(API 계약)이다.
- 그 위층에 JLS §3.10.5가 있다 — "리터럴과 상수 식은 `String.intern` 을 실행한 것처럼 인터닝된다".
- **두 근거의 층이 다르다**: JLS는 *언어* 보장, javadoc은 *API* 보장이다.\
  01번 주제의 `Integer.valueOf` 와 똑같은 이중 구조다.

**실무에서 쓰는 이유와 쓰지 말아야 할 이유**

| 쓰는 이유 | 쓰지 말아야 할 이유 |
|---|---|
| 같은 값이 수백만 번 나오는 데이터(로그 태그·enum 이름)의 메모리 절감 | 풀 조회에 `equals` 비교가 들어가 **공짜가 아니다** |
| | 풀에 들어간 문자열의 수명을 내가 통제하지 못한다 |
| | `==` 를 쓰려고 `intern()` 을 부르는 것은 **문제를 더 어렵게 만든다** |

- 판단 규칙: **메모리 문제를 측정으로 확인했을 때만 쓴다.**\
  `==` 비교를 쓰려고 쓰는 것은 거의 항상 잘못된 이유다.
- 대안: GC가 배열만 공유해 주는 `-XX:+UseStringDeduplication`(기본 꺼짐 — 플래그 출력으로 확인).

### 8. 어디까지가 JLS 보장이고 어디부터가 구현인가

**명세가 "같은 인스턴스"를 보장하는 대상**

- **리터럴**과 **상수 식의 값**, 둘뿐이다.
- 런타임에 만들어진 문자열은 **아무 보장이 없다.**

**원문 인용** — JLS SE 21 §3.10.5.

> At run time, a string literal is a reference to an instance of class `String` (§4.3.3) that denotes
> the string represented by the string literal.
>
> Moreover, a string literal always refers to the *same* instance of class `String`. This is because
> string literals - or, more generally, strings that are the values of constant expressions (§15.29) -
> are "interned" so as to share unique instances, as if by execution of the method `String.intern` (§12.5).

- "or, more generally, strings that are the values of constant expressions" 가 **2번 질문의 근거**다.
- `final` 이 붙으면 상수 식이 되어 이 문장이 적용되고, 안 붙으면 적용되지 않는다.

**풀의 위치와 크기는 누가 정하는가**

- **구현(HotSpot)이 정한다.** 명세는 풀의 구조를 한 글자도 말하지 않는다.
- 이 머신의 JVM에게 직접 물어본 결과다(출력 그대로).

```text
$ java -XX:+PrintFlagsFinal -version | grep -Ei 'CompactStrings|StringTableSize|StringDedup'
     bool CompactStrings                           = true                                   {pd product} {default}
     uint StringDeduplicationAgeThreshold          = 3                                         {product} {default}
    uintx StringTableSize                          = 65536                                     {product} {default}
     bool UseStringDeduplication                   = false                                     {product} {default}
```

- **`StringTableSize = 65536`** — 풀이 해시 테이블이고 크기가 플래그다.
- `{pd product}` 의 `pd` 는 platform-dependent 라는 뜻이다 — **플랫폼마다 기본값이 다를 수 있다.**

**내부가 `byte[]` 라는 사실이 동작을 바꾸는가**

```java
// JDK 21.0.5  java.base/java/lang/String.java  158·171·174행 — 실제 소스 그대로
private final byte[] value;
private final byte coder;
private int hash; // Default to 0
```

- **안 바꾼다.** `length()`·`charAt`·`substring` 은 여전히 **UTF-16 코드 단위** 기준으로 동작한다.
- `coder` 가 LATIN1(1바이트)인지 UTF16(2바이트)인지에 따라 **메모리 사용량만** 달라진다.
- Java 9의 compact strings(JEP 254)로 들어온 구현이고, 9 이전에는 `char[]` 였다.\
  **소스 코드를 한 글자도 안 고치고 메모리를 줄인 변경**이라 관측 가능한 동작이 없다.
- `hash` 가 `final` 이 아닌 이유: 첫 `hashCode()` 호출 때 계산해 캐시한다. 불변이라 안전하다.

**`identityHashCode` 를 로그 대조에 쓸 수 있는가**

- **못 쓴다.** 실행마다 다르다. 같은 프로그램을 세 JDK에서 돌린 결과다.

```text
JDK 17: a=349885916 b=349885916 c=414493378 f=1984697014
JDK 21: a=692404036 b=692404036 c=1554874502 f=1846274136
JDK 25: a=2060468723 b=2060468723 c=622488023 f=1933863327
```

- 의미가 있는 것은 **`a` 와 `b` 가 매번 같다**는 관계뿐이고, 값 자체는 매번 달라진다.
- 같은 이유로 **예외 메시지 문구**도 대조에 쓰면 안 된다(10번).

### 9. `switch` 에 `null` 을 넣으면

**출력**

```text
null.equals("A")               -> Cannot invoke "String.equals(Object)" because "<local2>" is null
switch(null)                   -> Cannot invoke "String.hashCode()" because "<local1>" is null
```

**어떤 예외, 어떤 메서드**

- **`NullPointerException`**.
- 메시지에 등장하는 메서드는 **`String.hashCode()`** 다.

**소스에 없는데 왜 나오는가**

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
      42: ifeq          61
      45: iconst_0
      46: istore_2
      47: goto          61
      50: aload_1
      51: ldc           #19                 // String B
      53: invokevirtual #15                 // Method java/lang/String.equals:(Ljava/lang/Object;)Z
      56: ifeq          61
      59: iconst_1
      60: istore_2
      61: iload_2
      62: lookupswitch  { // 2
                     0: 88
                     1: 91
               default: 94
          }
```

- **컴파일러가 넣은 `hashCode()` 호출**이다. 소스에는 `hashCode` 라는 글자가 없다.
- `65`·`66` 은 `"A"`·`"B"` 의 해시값(= `'A'`·`'B'` 의 코드)이다.

**두 단계**

```text
1단계 — 해시로 후보 좁히기          2단계 — 좁혀진 후보로 분기
  hashCode()                        정수 인덱스(0·1·-1)로
  -> lookupswitch                   -> lookupswitch
  -> 같은 해시의 case 로 점프         -> 각 case 본문
  -> equals() 로 진짜 확인
```

- 해시가 충돌해도 안전한 이유는 **2단계에서 `equals` 로 확인**하기 때문이다.
- 그래서 `switch(String)` 은 `if-else` 사슬보다 빠르다 — 해시 한 번으로 후보를 O(1)에 좁힌다.
- 대신 `null` 은 1단계에서 죽는다.\
  (Java 21의 `switch` 패턴 매칭에서는 `case null` 을 쓸 수 있다 — [**23번 주제**](../23-switch-pattern-matching/). *안 돌려 봤다.*)

**`new String("A")` 를 넣으면**

```text
switch(new String("A"))         : 우수
```

- **매치된다.**
- 2단계가 `equals` 이기 때문이다 — `==` 였다면 복사본은 매치되지 않았을 것이다.
- 즉 `switch(String)` 은 **`==` 가 아니라 `equals` 의미론**을 쓴다.

### 10. `substring` 의 경계와 버전

**`"hello".substring(5)`**

```text
substring(5)   = []
```

- **예외가 아니라 빈 문자열**이다.
- `beginIndex == length` 는 유효한 경계다 — "끝에서부터 0글자"라는 뜻이다.
- 그래서 `substring(5)` 와 `substring(6)` 이 **하나 차이로 갈린다.**

**두 예외** — JDK 21.0.5 · 25.0.1:

```text
substring(2,1) -> java.lang.StringIndexOutOfBoundsException: Range [2, 1) out of bounds for length 5
substring(6)   -> java.lang.StringIndexOutOfBoundsException: Range [6, 5) out of bounds for length 5
```

- 클래스는 둘 다 **`StringIndexOutOfBoundsException`**.
- `substring(6)` 의 메시지가 `Range [6, 5)` 인 것이 재미있다 —\
  `substring(b)` 가 내부적으로 `substring(b, length())` 를 부르기 때문에 `end` 가 5로 찍힌다.
- 즉 **한 인자짜리 호출인데 메시지는 두 인자짜리로 나온다.** 소스를 찾을 때 헷갈리는 자리다.

**JDK 17과 같은가**

```text
JDK 17.0.13
substring(2,1) -> java.lang.StringIndexOutOfBoundsException: begin 2, end 1, length 5
substring(6)   -> java.lang.StringIndexOutOfBoundsException: begin 6, end 5, length 5
```

- **다르다.** 같은 코드·같은 예외 클래스인데 **메시지 문구가 바뀌었다.**
- 이 문서에서 세 JDK의 출력이 갈린 **유일한 자리**다.

**테스트 코드에 주는 함의**

- **예외 메시지를 문자열로 단언하면 JDK를 올릴 때 테스트가 깨진다.**\
  `assertThat(ex.getMessage()).isEqualTo("begin 2, end 1, length 5")` 는 17에서만 통과한다.
- 단언할 것은 **예외 클래스**와, 필요하면 **메시지에 포함된 값**(인덱스·길이) 정도다.
- 같은 이유로 **로그 파싱·알림 규칙을 예외 메시지 문구에 걸면 안 된다.**
- 반대로 **에러 코드나 커스텀 예외**를 두는 이유가 여기 있다 — 문구는 구현이고 타입은 계약이다.

### 11. 다른 주제와 잇기

**`"Aa".hashCode()` 와 `"BB".hashCode()`**

```text
"".hashCode()                  : 0
"Aa".hashCode()                : 2112
"BB".hashCode()                : 2112
"Aa".equals("BB")              : false
```

- **같다.** 둘 다 `2112` 다.
- `String.hashCode` 는 `31*h + c` 를 누적하는 식이라 `'A'*31 + 'a'` 와 `'B'*31 + 'B'` 가 같아진다.\
  손계산: `65*31 + 97 = 2112`, `66*31 + 66 = 2112`. 실행 결과와 일치한다.
- **정상이다.** 해시는 "같으면 같은 해시"만 보장하고, 다른 값이 같은 해시를 가져도 계약 위반이 아니다.
- 최종 판정은 `equals` 가 한다 — 계약 전체는 [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/).

**상수 풀 보장과 `Integer` 캐시 보장의 근거 차이**

| | `Integer` 캐시 | 문자열 상수 풀 |
|---|---|---|
| 근거 조항 | JLS **§5.1.7** (박싱 변환) | JLS **§3.10.5** (문자열 리터럴) |
| 보장 범위 | `-128`~`127` 의 **상수 식** | **모든** 리터럴·상수 식 (값 제한 없음) |
| 범위 밖 | "어떤 가정도 허용하지 않는다" | 런타임 생성 문자열은 보장 밖 |
| 옵션으로 바뀌나 | **바뀐다** (`-XX:AutoBoxCacheMax`) | 풀 크기는 바뀌지만 **보장 자체는 안 바뀐다** |

- 둘 다 "같은 값이면 같은 객체인가"를 묻지만 **`String` 쪽이 훨씬 강한 보장**이다.\
  값의 크기 제한이 없기 때문이다.
- 대신 `String` 쪽은 **"상수 식인가"라는 조건이 더 까다롭다** — `final` 하나로 뒤집힌다.
- 자세한 것은 [`../01-primitives-and-wrappers/`](../01-primitives-and-wrappers/).

**`"" + 'A' + 'B'` 가 `"AB"` 인 이유**

- **[`../02-numeric-operations/`](../02-numeric-operations/) 의 규칙**이다 — 이항 수치 승격과 `+` 의 의미 결정.
- `'A' + 'B'` 는 둘 다 `char` 라 이항 수치 승격이 걸려 `int` 덧셈 `131` 이 된다.
- `"" + 'A'` 는 한쪽이 `String` 이라 **문자열 연결**이 되고, 왼쪽부터 평가하므로 그 뒤도 전부 연결이다.
- 실행으로 확인: `'A' + 'B' = 131` / `"" + 'A' + 'B' = AB`.

**루프에서 이어 붙이면 왜 느린가**

- **`String` 이 불변이기 때문**이다.
- 한 번 이어 붙일 때마다 **기존 내용을 전부 복사한 새 객체**가 만들어진다.\
  n번 반복하면 복사 총량이 1+2+3+...+n = n(n+1)/2 로 **O(n²)** 이 된다(손계산).
- 즉 "느린 이유"는 컴파일 방식이 아니라 **이 주제의 불변성**에 있다.
- 실제로 얼마나 느린지, 그리고 컴파일러가 무엇으로 바꾸는지는
  [`../36-stringbuilder-and-concat/`](../36-stringbuilder-and-concat/) 에서 **측정과 바이트코드**로 확인한다.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Ex`(35-pool) | 리터럴·`new String`·상수 식·런타임 연결·`StringBuilder` 의 `==` 6종, `intern()`, `identityHashCode` | 17 · 21 · 25 (**identityHashCode 만 다름**) |
| `Ex`(35-javap) `javap -c` | 상수 접기(`ldc #7`) 대 런타임 연결(`invokedynamic`), `static` 초기화 블록 | 21 |
| `Ex`(35-methods) | `trim`/`strip`/`isBlank`/`substring`/`split`/불변성 반환값 | 17 · 21 · 25 (**`substring` 예외 메시지만 다름**) |
| `Ex`(35-strip) | `trim` 과 `strip` 의 두 방향 비대칭, `Character.isWhitespace` 3종 | 17 · 21 · 25 (동일) |
| `Ex`(35-utf16) | `length` 대 `codePointCount`, 서로게이트 쌍, `chars()`, `reverse()` | 17 · 21 · 25 (동일) |
| `Ex`(35-cut) | 이모지를 반으로 자르기, `offsetByCodePoints` 로 안전하게 자르기 | 17 · 21 · 25 (동일) |
| `Ex`(35-equals) `javap -c` | `==`/`equals`/`compareTo`/`contentEquals`, `switch(null)` NPE, `switch` 의 2단계 컴파일, `hashCode` 충돌 | 21 |
| `java -XX:+PrintFlagsFinal` | `CompactStrings`·`StringTableSize`·`UseStringDeduplication` 기본값 | 21 |
| `src.zip` 열람 | `String.substring` 구현, `value`/`coder`/`hash` 필드, `intern()` javadoc | 21 |
| JLS 원문 | §3.10.5 문자열 리터럴 인터닝 | — |

**구현에 의존하는 항목**

| 항목 | 무엇에 의존하나 |
|---|---|
| `identityHashCode` 값 | 실행마다 다르다 — 대조 불가 |
| `substring` 예외 **메시지** | JDK 버전 (17 ↔ 21에서 실제로 바뀜) |
| 풀 크기·위치 | `-XX:StringTableSize`, 플랫폼 기본값 |
| 내부가 `byte[]` 인 것 | `-XX:+CompactStrings` (기본 켜짐), Java 9+ |
| `replace`/`substring` 이 `this` 를 돌려주는 것 | JDK 구현 최적화 — **명세가 아니다** |

**버전이 오르면 다시 돌려야 할 것**

- `substring` 계열의 **예외 메시지**(이미 한 번 바뀌었다).
- `String` 에 새 메서드가 들어왔는지.
- `==` 결과는 명세가 보장하므로 바뀌면 그것이 버그다.

## 안 돌려 본 것

- `s.replace(' ', ' ').strip()` 조합 — U+00A0 를 명시적으로 지우는 법.
- `java.text.BreakIterator` 로 "사람이 보는 글자" 세기.
- `-XX:+UseStringDeduplication` 의 실제 동작 — 플래그 기본값만 확인했다.
- Java 21 `switch` 의 `case null` — [목록의 **23번 주제**](../23-switch-pattern-matching/)에서 다룬다.
- `substring` 이 Java 6까지 배열을 공유했다는 연혁 — 기준 소스로 확인하지 않았다(**확인 필요**).
- `String.format`·`join`·`repeat` — [`../36-stringbuilder-and-concat/`](../36-stringbuilder-and-concat/) 에서 돌렸다.
