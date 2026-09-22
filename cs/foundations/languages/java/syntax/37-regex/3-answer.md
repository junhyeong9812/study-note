# java/syntax/37 — 정규식: `Pattern`/`Matcher`·`String` 의 정규식 메서드 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·예외는 **Temurin JDK 21.0.5 에서 실제로 돌려 얻은 것**이다.\
> JDK 소스 인용은 `lib/src.zip` 의 `java.base/java/util/regex/Pattern.java` 실파일에서 그대로 옮겼다.\
> 실행 파일명은 전부 `Ex.java` 로 고정했고, 프로그램이 여럿이라 `Ex.java (37-a)` 처럼 라벨로 구분한다.\
> 17.0.13 · 25.0.1 에서도 같은 프로그램을 돌렸다. **갈린 곳은 2번 하나**다.
> **★ 측정 조건**(9·10번) — **JMH 가 아니다.** `System.nanoTime()` 반복 측정이고,
> 머신은 13th Gen Intel Core i7-13700HX · 24 스레드 · Linux 7.0.0-31-generic 이다.\
> **재현되는 것은 절댓값이 아니라 기울기(+2 글자마다 약 4배)와 자릿수(3\~4배)다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 세 메서드의 아홉 줄

**출력** (`Ex.java (37-a)`, JDK 21.0.5 — 17 · 25 동일)

```text
--- matches / find / lookingAt  (패턴 \d+, 입력 "abc123def456")
  matcher.matches()   = false
  matcher.lookingAt() = false
  matcher.find()      = true
--- 같은 패턴, 입력 "123"
  matches()   = true
  lookingAt() = true
  find()      = true
--- 같은 패턴, 입력 "123abc"
  matches()   = false
  lookingAt() = true
  find()      = true
```

**셋의 차이 — 한 마디씩**

| | 묻는 것 |
|---|---|
| `matches()` | **입력 전체**가 패턴과 맞나 |
| `lookingAt()` | **맨 앞부터** 맞나 (뒤에 뭐가 남아도 된다) |
| `find()` | **아무 데나** 맞는 데가 있나 |

**검증에 `find()` 를 쓰면**

- **"숫자가 하나라도 있으면" 통과**한다. `"12; DROP TABLE users"` 도 `[0-9]+` 의 `find()` 를 통과한다.
- 검증은 `matches()`(또는 `\A...\z` 앵커)여야 한다.

### 2. `Matcher` 를 잘못 쓰면 무엇이 나오나

**출력** (`Ex.java (37-d)`, JDK 21.0.5)

```text
--- find() 없이 group()
  java.lang.IllegalStateException
  메시지:
    No match found
--- 매치 실패 뒤 group()
  find() = false
  java.lang.IllegalStateException
  메시지:
    No match found
--- find() 없이 start()
  java.lang.IllegalStateException
  메시지:
    No match found
```

- (가)·(나)·(다) 전부 **`IllegalStateException`** 이다.
- 메시지는 JDK 21 에서 전부 `No match found`.

**★ 17 과 21 에서 다른 것 — (다) `start()`**

```text
JDK 17.0.13 : No match available
JDK 21.0.5  : No match found
JDK 25.0.1  : No match found
```

- 같은 프로그램에서 `group()` 쪽(가·나)은 **세 버전 다 `No match found`** 였고, `start()` 만 17 에서 달랐다.
- 함의: **예외 메시지를 문자열로 단언하는 테스트는 JDK 를 올리면 깨진다.** 타입으로 단언하라.

**`group(5)` 와 `group("없는이름")`**

```text
--- 없는 그룹 이름 "(?<a>x)" 에 group("b")
  java.lang.IllegalArgumentException
  메시지:
    No group with name <b>
--- 없는 그룹 번호 group(5)
  java.lang.IndexOutOfBoundsException
  메시지:
    No group 5
```

- 셋이 **다른 타입**이다 — 상태(`IllegalStateException`) / 이름(`IllegalArgumentException`) / 번호(`IndexOutOfBoundsException`).

### 3. 탐욕·게으름·소유

**출력** (`Ex.java (37-b)`, JDK 21.0.5)

```text
--- 탐욕 / 게으름 / 소유  (입력 "<a><b></b></a>")
  탐욕   <.+>           -> "<a><b></b></a>"  (end=14)
  게으름 <.+?>          -> "<a>"  (end=3)
  소유   <.++>          -> 매치 없음
--- 같은 세 수량자, 입력 "aaa", 패턴 a*a
  탐욕   a*a            -> "aaa"  (end=3)
  게으름 a*?a           -> "a"  (end=1)
  소유   a*+a           -> 매치 없음
```

**소유가 실패하는 이유 — 한 문장**

- **`.++` 가 입력 끝까지 먹고 한 글자도 되돌려주지 않아, 뒤의 `>` 가 볼 글자가 남지 않기 때문이다.**

**"되돌려준다"로 정리하면**

```text
탐욕   : 최대한 먹는다 -> 뒤가 안 맞으면 한 글자씩 되돌려준다
게으름 : 최소로 먹는다 -> 뒤가 안 맞으면 한 글자씩 더 먹는다
소유   : 최대한 먹는다 -> 되돌려주지 않는다 (그래서 실패도 빠르다)
```

- 소유 수량자의 값어치는 **속도**다 — 백트래킹을 원천 차단한다(9번).

### 4. `split` 결과의 길이 일곱 줄

**출력** (`Ex.java (37-c)`, JDK 21.0.5 — 17 · 25 동일)

```text
--- split 의 빈 조각
  "a,b,,c,,".split(",")        길이=4  [a, b, , c]
  "a,b,,c,,".split(",", -1)    길이=6  [a, b, , c, , ]
  "a,b,,c,,".split(",", 2)     길이=2  [a, b,,c,,]
  ",,a".split(",")             길이=3  [, , a]
  "".split(",")                길이=1  []
  ",".split(",")               길이=0  []
  ",".split(",", -1)           길이=2  [, ]
```

**앞과 뒤가 다른 이유 — 근거 문장**

`Pattern.split` 의 javadoc(JDK 21.0.5 `src.zip` 원문).

```text
If the limit is zero then the pattern will be applied as
many times as possible, the array can have any length, and trailing
empty strings will be discarded.

If the limit is negative then the pattern will be applied
as many times as possible and the array can have any length.
```

- **버려지는 것은 `trailing`(뒤쪽) 빈 조각뿐**이다. 앞쪽은 손대지 않는다.
- `limit > 0` 이면 패턴을 최대 `limit - 1` 번만 적용한다 → `split(",", 2)` 가 `[a, "b,,c,,"]`.

**`""` 와 `","` 가 갈리는 이유**

- `"".split(",")` — 패턴이 **한 번도 안 맞았다.** javadoc: *"If this pattern does not match any subsequence of the input then the resulting array has just one element, namely the input sequence in string form."*\
  그래서 `[""]`, 길이 1 이다.
- `",".split(",")` — 패턴이 맞아 조각 둘(`""`, `""`)이 생겼고, **둘 다 뒤쪽 빈 조각**이라 전부 버려져 길이 0 이다.

**CSV 의 기본형**

- **`split(",", -1)`** 이다. 그러지 않으면 **마지막 빈 열들이 사라져** 열 수가 줄어든다.\
  (진짜 CSV 는 따옴표 안의 쉼표 때문에 `split` 으로 풀면 안 된다 — 파서를 쓴다.)

### 5. 인자가 정규식인 줄 모르면

**출력** (`Ex.java (37-a)` · `(37-c)`, JDK 21.0.5)

```text
  "a.b.c".split(".")           길이=0  []
  "a.b.c".split("\\.")         길이=3  [a, b, c]
  "a|b".split("|")             길이=3  [a, |, b]
  "a.b".replace(".","#")     = a#b   (정규식 아님)
  "a.b".replaceAll(".","#")  = ###   (정규식이다)
--- 치환문에서 $ 를 그대로 쓰려 하면
  java.lang.IndexOutOfBoundsException: No group 9
```

- `split(".")` — `.` 이 **아무 글자**라 전부 구분자가 되고 조각이 전부 빈 문자열 → 뒤에서부터 다 버려져 **길이 0**.
- `split("|")` — `|` 는 **빈 대안**이라 글자 사이마다 잘린다. `[a, |, b]`.
- `replaceAll("price", "$9")` — `$9` 를 **9번 그룹 참조**로 읽어 `IndexOutOfBoundsException: No group 9`.

**`replace` 대 `replaceAll` — 한 줄**

- **`replace` 는 글자 그대로, `replaceAll` 은 정규식.** 이름만으로는 반대로 읽히니 외워야 한다.\
  (`replace` 는 "모든 것을 바꾼다"는 점에서도 `replaceAll` 과 같다 — 다른 것은 **정규식이냐**뿐이다.)

**`quote` 둘이 막는 것**

| | 막는 자리 | 결과 |
|---|---|---|
| `Pattern.quote(s)` | **패턴** 쪽의 메타문자 | `\Q` ... `\E` 로 감싼다 |
| `Matcher.quoteReplacement(s)` | **치환문** 쪽의 `$` 와 `\` | 각각 앞에 `\` 를 붙인다 |

```text
  Pattern.quote("a.b|c") = \Qa.b|c\E
  Matcher.quoteReplacement("$1\\") = \$1\\
  quoteReplacement 쓰면 : $9
```

- `Pattern.quote("a.b|c")` 의 결과 문자열은 **`\Qa.b|c\E`** 다.

### 6. 문법이 틀린 정규식

**출력** (`Ex.java (37-d)` · `(37-g)`, JDK 21.0.5)

```text
--- 괄호를 안 닫음  "(\\d+"
  java.util.regex.PatternSyntaxException
  메시지:
    Unclosed group near index 4
    (\d+
--- 수량자만 있음  "*abc"
  java.util.regex.PatternSyntaxException
  메시지:
    Dangling meta character '*' near index 0
    *abc
    ^
--- 문자 클래스 안 닫음 "[a-z"
  java.util.regex.PatternSyntaxException
  메시지:
    Unclosed character class near index 3
    [a-z
       ^
--- 알 수 없는 이스케이프 "\\p{Nope}"
  java.util.regex.PatternSyntaxException
  메시지:
    Unknown character property name {Nope} near index 7
    \p{Nope}
           ^
--- 역참조가 가리킬 그룹이 없음 "\\1abc"
  예외 없음
```

**예외가 나는 것은 네 개**다. `\1abc` 만 예외가 안 난다.

- 타입은 넷 다 **`PatternSyntaxException`**.
- 메시지 첫 줄은 각각 `Unclosed group` · `Dangling meta character '*'` · `Unclosed character class` · `Unknown character property name {Nope}` 에 `near index N` 이 붙는다.

**검사 예외인가**

- **아니다.** `PatternSyntaxException` 은 `IllegalArgumentException` 의 하위라 **비검사 예외**다.
- 함의: **컴파일러가 잡아 주지 않는다.** 그래서 패턴 오타는 **그 코드가 실제로 실행될 때** 터진다.\
  방어: `static final Pattern` 으로 두면 **클래스 로딩 때** 터져 기동 단계에서 잡힌다(12번).

**`\1abc` 는 무엇을 매치하나**

```text
  "abc" 에 find() = false
  "" 에 find()    = false
```

- **아무것도 매치하지 않는다.** 가리킬 그룹이 없는 역참조는 실패한다.
- **그런데 이 "아무것도 아닌" 것이 엔진의 백트래킹 방어를 끈다** — 9번이 그 이야기다.

### 7. 그룹

**출력** (`Ex.java (37-b)`, JDK 21.0.5)

```text
--- 그룹
  group(0) = jun@example.com
  group(1) = jun
  group(2) = example
  group(3) = com
  groupCount() = 3
--- 이름 있는 그룹
  user = jun
  host = example.com
--- 비캡처 그룹 (?: )
  groupCount() = 1 / group(1) = example
```

- `groupCount()` 는 **3** 이다. `group(0)`(매치 전체)은 세지 않는다.
- **`(?:...)` 는 번호를 차지하지 않는다** — 그래서 `(?:\w+)@(\w+)` 의 `groupCount()` 가 1 이고 `group(1)` 이 `example` 이다.

**패턴 안 대 치환문 — 표기가 다르다**

```text
--- 역참조 \1 — 같은 낱말이 두 번 나오는 곳
  중복: "the the"  (반복된 낱말=the)
  중복: "brown brown"  (반복된 낱말=brown)
--- 치환에서 그룹 참조 $1
  21/09/2026
  이름 참조 ${y} : 21.09.2026
```

| 자리 | 번호로 | 이름으로 |
|---|---|---|
| **패턴 안**(역참조) | `\1` | `\k<name>` |
| **치환문 안** | `$1` | `${name}` |

**이름 있는 그룹은 7 부터**다(`Matcher.group(String)` 의 `@since 1.7` — `src.zip` 직접 확인).

### 8. `Pattern` 과 `Matcher` 중 무엇을 공유해도 되나

**javadoc 원문** (JDK 21.0.5 `Pattern.java` 클래스 javadoc)

```text
Instances of this class are immutable and are safe for use by multiple
concurrent threads.  Instances of the Matcher class are not safe for
such use.
```

- **`Pattern` 은 공유해도 되고 `Matcher` 는 안 된다.** 계약 문장이 딱 한 문단이다.

**`Matcher` 를 다른 입력에 다시 쓰는 법** — `reset(CharSequence)`.

```text
--- Matcher 는 재사용 가능하지만 스레드 안전이 아니다
  첫 매치 1 / 둘째 22
  reset(다른 입력) 후 9
```

- `reset()` 은 커서만 되돌리고, `reset(새 입력)` 은 입력까지 바꾼다.

**여러 스레드가 쓸 때의 권장 형태**

```java
private static final Pattern P = Pattern.compile("\\d+");   // 공유
...
Matcher m = P.matcher(input);                               // 호출마다 새로
```

- `matcher()` 호출은 `compile()` 보다 훨씬 싸다 — 10번의 측정이 그것을 보여 준다.
- 정말 뜨거운 코드라면 `ThreadLocal<Matcher>` 도 방법이지만, **먼저 `compile` 을 밖으로 빼는 것**이 효과가 크다.

### 9. ★ 파국적 백트래킹 — 터뜨릴 수 있는가

**출력** (`Ex.java (37-e)` · `(37-e6)`, JDK 21.0.5)

```text
--- (x+x+)+y            입력 "xxx...x" (y 가 없어 반드시 실패한다)
  x 20 개         1 ms
  x 24 개         0 ms
  x 28 개         0 ms
  x 32 개         0 ms
  x 36 개         0 ms
  x 40 개         0 ms
--- (a)\1?(x+x+)+y      입력 "a"+"xxx...x" — 역참조 \1 이 하나 끼어 있다
  x 16 개         2 ms
  x 18 개         7 ms
  x 20 개        21 ms
  x 22 개        64 ms
  x 24 개       232 ms
  x 26 개       818 ms
  x 28 개      2912 ms
  x 30 개     11815 ms
```

**(가) `(x+x+)+y` 에 40 글자 → 0 ms.** 교과서가 "지수"라고 말하는 패턴인데 평평하다.

**(나) `\1?(x+x+)+y` 에 26 글자 → 753 ms**(같은 조건의 별도 실행). 입력이 **14 글자나 짧은데** 그렇다.

```text
--- (x+x+)+y                 <- 역참조 없음
  x 26 개         0 ms
--- \1?(x+x+)+y              <- 존재하지도 않는 그룹을 가리키는 \1 하나
  x 26 개       753 ms
```

**`\1?` 는 매치 결과에 영향을 주는가 — 주지 않는다.**

- 가리킬 그룹이 없어 항상 실패하고, `?` 라서 없어도 된다. **의미상 아무것도 아니다.**
- 그런데 이것 하나로 0 ms 가 753 ms 가 됐다.

**JDK 내부 장치의 이름과 꺼지는 조건**

`java.base/java/util/regex/Pattern.java` 의 `Loop.match`(JDK 21.0.5 원문).

```java
// This block is for after we have the minimum
// iterations required for the loop to match
if (count < cmax) {
    // Let's check if we have already tried and failed
    // at this starting position "i" in the past.
    // If yes, then just return false without trying
    // again, to stop the exponential backtracking.
    if (posIndex != -1 &&
        matcher.localsPos[posIndex].contains(i)) {
        return next.match(matcher, i, seq);
    }
```

꺼지는 조건도 같은 파일에 적혀 있다.

```java
/*
 * Turn off the stop-exponential-backtracking optimization if there
 * is a group ref in the pattern.
 */
transient boolean hasGroupRef;
```

```java
// Optimize the greedy Loop to prevent exponential backtracking, IF there
// is no group ref in this pattern. ...
if (!hasGroupRef) {
    for (Node node : topClosureNodes) {
        if (node instanceof Loop) {
            ((Loop)node).posIndex = localTCNCount++;
        }
    }
}
```

- 장치: **그리디 `Loop` 의 "실패한 시작 위치" 메모이제이션**.
- 꺼지는 조건: **패턴에 역참조(`\N`·`\k<name>`)가 하나라도 있을 때.**

**두 글자 늘 때 몇 배인가**

```text
  16 ->  2 ms
  18 ->  7 ms      (3.5배)
  20 -> 21 ms      (3.0배)
  22 -> 64 ms      (3.0배)
  24 -> 232 ms     (3.6배)
  26 -> 818 ms     (3.5배)
  28 -> 2912 ms    (3.6배)
  30 -> 11815 ms   (4.1배)
```

- **약 3\~4배**다. 지수(2^n)의 모양이고, 32 글자를 실제로 돌린 별도 실행에서 **42,847 ms** 가 나왔다.
- 17 · 21 · 25 에서 30 글자가 각각 **11,734 / 11,815 / 11,696 ms** — 세 버전이 같은 곡선이다.

**막는 법 세 가지** (실측 — `Ex.java (37-e)`)

```text
--- 같은 입력, 소유 수량자 (a++)+b
  n=26      결과=false       0 ms
  n=1000    결과=false       0 ms
  n=100000  결과=false       5 ms
--- 같은 입력, 중첩을 없앤 a+b
  n=100000  결과=false       0 ms
```

1. **소유 수량자**(`++`)로 백트래킹을 차단한다.
2. **중첩 수량자를 없앤다**(`(a+)+` → `a+`). 의미가 같은 경우가 많다.
3. **입력 길이 상한**을 정규식 앞에 둔다. 지수라 길이 상한이 곧 시간 상한이다.

### 10. `Pattern` 컴파일 비용

**출력** (`Ex.java (37-f)`, JDK 21.0.5 — 20만 건 × 6 회, JMH 아님)

```text
  1회차  매번 compile= 227 ms   미리 compile=  44 ms   String.matches= 187 ms
  2회차  매번 compile= 227 ms   미리 compile=  38 ms   String.matches= 152 ms
  3회차  매번 compile=  82 ms   미리 compile=  23 ms   String.matches=  79 ms
  4회차  매번 compile=  81 ms   미리 compile=  26 ms   String.matches=  84 ms
  5회차  매번 compile=  79 ms   미리 compile=  24 ms   String.matches=  84 ms
  6회차  매번 compile=  88 ms   미리 compile=  23 ms   String.matches=  78 ms
```

**몇 배인가** — 안정 구간(3 회차 이후)에서 **약 3\~4배**다(79\~88 ms 대 23\~26 ms).

**`String.matches` 는 "매번 compile" 쪽**이다.

- 78\~84 ms 로 "매번 compile"(79\~88 ms)과 같은 자릿수다.
- 이유: `String.matches(regex)` 는 `Pattern.matches(regex, this)` 를 부르고, 그것이 **매번 `Pattern.compile`** 을 한다.

**1\~2 회차가 느린 이유** — **JIT 웜업**이다. 인터프리터로 돌다가 핫스팟이 네이티브로 컴파일되기 전이다.\
(JIT 자체는 [`../../언어-특성/README.md`](../../언어-특성/README.md) 가 정본이다.)

**재현되는 것 / 안 되는 것**

| 재현된다 | 재현 안 된다 |
|---|---|
| **3\~4배**라는 자릿수 | 79 ms · 23 ms 같은 절댓값 |
| 세 방식의 **순서**(미리 < 매번 ≈ String.matches) | 회차별 정확한 ms |
| 1\~2 회차가 느리다는 **모양** | 웜업이 끝나는 정확한 회차 |

- 두 번째 실행에서도 68\~72 / 18\~21 / 67\~80 ms 로 **같은 자릿수**였다.

### 11. 무엇이 계약이고 무엇이 구현인가

| 항목 | 계약 / 구현 | 근거 |
|---|---|---|
| `split` 의 limit 규칙 | **계약** | `Pattern.split` javadoc |
| 예외 **타입** | **계약** | 각 메서드의 `@throws` |
| 예외 **메시지** | **구현** | 17 ↔ 21 에서 `start()` 메시지가 바뀌었다(2번) |
| `Pattern` 불변·스레드 안전 | **계약** | 클래스 javadoc |
| **그리디 루프 메모이제이션** | **구현** | `Pattern.java` 의 **주석** — javadoc 이 아니다 |
| `(x+x+)+y` 가 빠른 것 | **구현** | 위 최적화의 결과 |

**코드 리뷰에서 뜻하는 바**

- **"Java 니까 ReDoS 는 괜찮다"로 넘길 수 없다.**\
  그 방어는 javadoc 에 없는 구현 최적화이고, **역참조 한 글자로 꺼진다.**
- 사용자 입력에 정규식을 돌리는 코드는 여전히 **길이 상한**과 **패턴 모양 검토**가 필요하다.

**고쳐 쓴 문장**

> "Java 정규식 엔진에는 그리디 루프의 실패 위치를 기억해 지수 백트래킹을 막는 **구현 최적화**가 있다.\
> 다만 패턴에 역참조가 있으면 그 최적화가 꺼지고, 그때는 다른 백트래킹 엔진과 똑같이 폭발한다."

### 12. 다른 주제와 잇기

**텍스트 블록에 정규식을 적으면**

- **역슬래시가 줄지 않는다.** 텍스트 블록은 **raw 문자열이 아니라** 이스케이프를 해석하는 리터럴이다.
- `\d` 를 쓰려면 텍스트 블록에서도 `\\d` 다. 정본은 [32 텍스트 블록](../32-text-blocks/).

**정규식으로 하면 안 되는 일 셋**

1. **중첩 구조 파싱** — HTML·XML·JSON·괄호 짝. 정규식의 표현력 밖이다.
2. **단순 포함·접두사 검사** — `contains`·`startsWith` 가 더 빠르고 안전하다.
3. **고정 문자열 치환** — `replace` 를 쓴다(5번).

**`asPredicate` 대 `asMatchPredicate`**

```text
--- asPredicate(find 기준) 대 asMatchPredicate(matches 기준)
  asPredicate("ab1")      = true
  asMatchPredicate("ab1") = false
```

- `asPredicate` = **`find` 기준**, `asMatchPredicate` = **`matches` 기준**.
- 이름만으로는 안 갈리니 "**Match 가 붙은 쪽이 `matches`**"로 외운다.

**`PatternSyntaxException` 을 기동 시점에 터뜨리려면**

```java
private static final Pattern P = Pattern.compile("...");   // 클래스 로딩 때 컴파일된다
```

- 필드가 `static` 이라 **클래스 초기화 때** `compile` 이 돌고, 오타면 거기서 터진다.
- 메서드 안에서 `Pattern.compile` 을 부르면 **그 메서드가 처음 실행될 때** 터진다 — 운영에서 새벽에 만난다.
- 클래스 초기화 순서는 [06 초기화 순서](../06-initialization-order/) 가 정본이다.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Ex`(37-a) | `matches`/`lookingAt`/`find` 9 종, `find` 반복·`reset`, `String` 의 정규식 메서드 5 종 | 17 · 21 · 25 (**동일**) |
| `Ex`(37-b) | 탐욕/게으름/소유 6 종, 그룹·이름 그룹·비캡처·역참조·치환 참조 | 17 · 21 · 25 (**동일**) |
| `Ex`(37-c) | `split` 7 종, 정규식 인자 4 종, `quote` 둘, `splitAsStream` | 17 · 21 · 25 (**동일**) |
| `Ex`(37-d) | 예외 10 종(`PatternSyntaxException`·`IllegalStateException`·`IllegalArgumentException`·`IndexOutOfBoundsException`) | 17 · 21 · 25 (**`start()` 메시지만 17 에서 다름**) |
| `Ex`(37-e) | 파국적 백트래킹 — `(x+x+)+y` 대 `(a)\1?(x+x+)+y`, 소유 수량자·중첩 제거 대안 | 17 · 21 · 25 (**같은 곡선**) |
| `Ex`(37-e6) | 존재하지 않는 그룹을 가리키는 `\1?` 하나만으로 방어가 꺼지는 것 | 21 |
| `Ex`(37-f) | `Pattern` 재사용 대 매번 컴파일 대 `String.matches` (20만 건 × 6 회, 2 회 실행) | 21 |
| `Ex`(37-g) | `results()`·`replaceAll(Function)`·`appendReplacement`·플래그 6 종·`asPredicate`·`\1abc`·`Matcher` 재사용 | 17 · 21 · 25 (**동일**) |
| `src.zip` 열람 | `Pattern` 클래스 javadoc, `split` javadoc, `Loop.match` 구현 주석, `hasGroupRef` 주석, 각 `@since` | 17 · 21 · 25 |

- 프로그램 **8개**, 실행 왕복 **26회**(5개 × 3 JDK + 측정 프로그램 반복), `javap` 는 쓰지 않았다(이 주제는 바이트코드가 근거가 아니다).

**구현에 의존하는 항목**

| 항목 | 무엇에 의존하나 |
|---|---|
| 예외 **메시지** | JDK 버전 (17 ↔ 21 에서 실제로 바뀜) |
| `(x+x+)+y` 가 빠른 것 | JDK 의 그리디 루프 메모이제이션 — **javadoc 계약이 아니다** |
| 모든 ms 값 | 머신·JIT·부하 — 재현되는 것은 기울기와 자릿수 |
| `ImmutableCollections` 같은 내부 클래스 이름 | 이 주제에서는 쓰지 않았다 |

**버전이 오르면 다시 돌려야 할 것**

- **예외 메시지 문자열**(이미 한 번 바뀌었다).
- **백트래킹 방어의 조건** — `hasGroupRef` 라는 스위치 자체가 바뀔 수 있다.\
  버전을 올리면 `Ex`(37-e) 를 다시 돌려 곡선이 그대로인지 본다.
- `Pattern`·`Matcher` 에 새 메서드가 들어왔는지.

## 안 돌려 본 것

- **다른 정규식 엔진**(RE2J·`java.util.regex` 외부 라이브러리)과의 비교 — 이 배치의 범위 밖이다.
- **스레드 여럿이 같은 `Matcher` 를 쓰는** 실제 경쟁 — javadoc 계약으로만 적었다(데이터 경쟁은 재현이 보장되지 않아 관찰로 쓰면 오히려 위험하다).
- `Pattern.CANON_EQ`·`UNICODE_CHARACTER_CLASS` 등 나머지 플래그.
- `MatchResult` 인터페이스의 9 이후 확장 메서드들.
- 정규식 **컴파일 시간** 자체의 분해(파싱 대 노드 조립) — 총량만 쟀다.
