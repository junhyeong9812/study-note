# java/syntax/37 — 정규식: `Pattern`/`Matcher`·`String` 의 정규식 메서드 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Java SE 21 `Pattern` API 문서](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/regex/Pattern.html) · [`Matcher`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/regex/Matcher.html) · JDK 17.0.13 / 21.0.5 / 25.0.1 표준 라이브러리 소스 `java.base/java/util/regex/Pattern.java` 의 **javadoc 과 구현 주석 원문**(`lib/src.zip` 에서 직접 읽음).
> **실행 검증** — 이 문서의 모든 출력·에러는 Temurin **JDK 21.0.5** 에서 실제로 돌려 얻은 것이다.\
> 프로그램 7개를 **17.0.13 · 21.0.5 · 25.0.1** 에서 전부 돌렸다.\
> **한 군데가 갈렸다** — `Matcher.start()` 를 매치 없이 부를 때의 예외 **메시지**가 17 과 21 에서 다르다(「어디서 틀리나」 4번).
> **★ 측정 조건**(수치를 싣는 절 — 「동작 방식 (5)」·「(6)」) — **JMH 가 아니다.** 단순 `System.nanoTime()` 반복 측정이다.\
> 머신: 13th Gen Intel Core i7-13700HX · 24 스레드 · Linux 7.0.0-31-generic. 각 측정은 한 JVM 안에서 3~6 회 반복했다.\
> **재현되는 것은 절댓값이 아니라 기울기와 자릿수다** — 파국적 백트래킹은 입력 +2 글자마다 시간이 약 4배가 되는 **모양**이,\
> `Pattern` 재사용은 **3~4배**라는 자릿수가 재현된다. 웜업 전 1~2 회차는 JIT 때문에 느리므로 표에 함께 싣는다.
> **버전** — `Pattern`/`Matcher` 는 **1.4**. `Pattern.quote`·`Matcher.quoteReplacement`·`usePattern` = **5** ·
> 이름 있는 그룹 `(?<name>...)`·`group(String)` = **7** · `splitAsStream` = **8** ·
> `Matcher.results()`·`replaceAll(Function)`·`appendReplacement(StringBuilder,...)` = **9** (전부 `src.zip` 의 `@since` 직접 확인).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.
> 선행: [35 `String`](../35-string/).

## 한눈에 — 쉽게 말하면

**정규식은 "찾기 규칙을 미리 컴파일해 둔 기계(`Pattern`)"와 "그 기계를 입력 하나에 물려 돌리는 손잡이(`Matcher`)"다.**\
기계는 여러 번 써도 되고 스레드끼리 공유해도 되지만, **손잡이는 한 사람이 한 입력에만** 쓴다.

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 찾기 규칙을 적은 설계도 | 정규식 문자열 (`"\\d+"`) |
| 설계도로 만든 기계 | `Pattern` — **불변·스레드 안전**, 만드는 데 비용이 든다 |
| 기계에 입력을 물린 손잡이 | `Matcher` — **가변**, 어디까지 봤는지(커서)를 기억한다 |
| 손잡이를 한 칸 당기는 것 | `find()` — 다음 매치로 커서를 옮긴다 |
| 당긴 뒤 꺼내 보는 결과 | `group()`·`start()`·`end()` — **당기지 않고 꺼내면 예외** |
| 손잡이를 처음으로 되돌리기 | `reset()` |
| 규칙을 끝까지 다 맞춰야 한다는 조건 | `matches()` — **입력 전체**가 맞아야 참 |
| 앞부분만 맞으면 된다는 조건 | `lookingAt()` |
| 아무 데나 한 군데만 맞으면 된다는 조건 | `find()` |

- `Pattern.compile` 은 **설계도를 기계로 만드는 일**이라 공짜가 아니다.\
  루프 안에서 매번 컴파일하면 **같은 기계를 매번 다시 만드는** 셈이다((6) 에서 측정).
- `Matcher` 는 **상태를 가진다.** `find()` 를 부르기 전의 `group()` 은 예외다.
- **`matches` / `lookingAt` / `find` 는 셋 다 다른 질문**이다. 이것을 섞는 것이 가장 흔한 버그다.

```text
패턴 \d+  ·  입력 "abc123def456"

  a b c 1 2 3 d e f 4 5 6
  ^---------------------^   matches()   : 전체가 \d+ 인가?     -> false
  ^                         lookingAt() : 맨 앞부터 맞나?      -> false
        ^-----^             find()      : 아무 데나 있나?      -> true  ("123")
                    ^-----^ find() 또    : 그다음은?           -> true  ("456")
                            find() 또    :                     -> false (끝)
```

실무에서 이게 터지는 자리는 **입력 검증에 `find()` 를 쓰는 코드**다.\
`Pattern.compile("[0-9]+").matcher(input).find()` 는 "숫자가 **하나라도 있으면**" 참이라,\
`"12; DROP TABLE"` 도 통과한다. 검증은 `matches()` 여야 한다.

> **`Pattern`** — 컴파일된 정규식. javadoc 원문: *"Instances of this class are immutable and are safe for use by multiple concurrent threads. Instances of the `Matcher` class are not safe for such use."*\
> 예: `static final Pattern P = Pattern.compile("\\d+");` 처럼 필드에 두고 공유하는 것이 정석이다.

> **`Matcher`** — `Pattern` 에 입력 하나를 물린 실행 상태. 커서와 마지막 매치 결과를 들고 있다.\
> 예: `find()` 를 세 번 부르면 매치 세 개를 차례로 준다.

> **백트래킹(backtracking)** — 매치가 실패했을 때 앞으로 되돌아가 다른 가능성을 다시 시도하는 것.\
> 예: `a*a` 가 `"aaa"` 를 볼 때 `a*` 에 셋을 다 주면 뒤의 `a` 가 못 먹으니, 하나 돌려주고 다시 해 본다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. `matches` / `find` / `lookingAt` / `split` 은 **각각 무엇을 요구하는가** — 잘못 고르면 무엇이 통과하는가.
2. 정규식이 **언제 느려지는가** — "짧은 입력인데 멈춘 것 같다"의 원인은 무엇인가.
3. `Pattern` 과 `Matcher` 중 **무엇을 재사용해도 되는가.**

## 동작 방식

### (1) 세 가지 질문 — `matches` · `lookingAt` · `find`

**언제 쓰나** — 정규식을 쓰는 모든 자리. 고르는 순간이 곧 요구사항 선언이다.

```text
입력 "123abc" · 패턴 \d+

  matches()                lookingAt()              find()
  +-------------------+    +-------------------+    +-------------------+
  | 1 2 3 a b c       |    | 1 2 3 a b c       |    | 1 2 3 a b c       |
  | ^^^^^^^^^^^       |    | ^^^^^             |    |   ^^^^^           |
  | 전부 맞아야 한다   |    | 앞부터 맞으면 된다 |    | 아무 데나 있으면   |
  +-------------------+    +-------------------+    +-------------------+
        false                    true                     true
```

실행 결과 (`Ex.java (37-a)`, JDK 21.0.5):

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

그림 해설 (한 단계씩):

- `"123"` 은 셋 다 참이다 — **셋의 차이는 "전체냐 앞이냐 아무 데나냐"**뿐이다.
- `"123abc"` 에서 `matches` 만 거짓이 된다. **검증 코드가 `find` 를 쓰면 이 입력이 통과한다.**
- `String.matches(regex)` 는 이름 그대로 **`matches` 쪽**이다 — `"abc123".matches("\\d+")` 는 `false`.

```text
--- String 의 정규식 메서드는 어느 쪽인가
  "abc123".matches("\\d+")  = false
  "abc123".replaceAll("\\d+","#") = abc#
  "abc123".replaceFirst("\\d","#") = abc#23
  "a.b".replace(".","#")     = a#b   (정규식 아님)
  "a.b".replaceAll(".","#")  = ###   (정규식이다)
```

- **`replace` 는 정규식이 아니고 `replaceAll` 은 정규식이다.** 이름이 비슷해 가장 자주 헷갈린다.
- `replaceAll("." , "#")` 이 `###` 인 것이 그 증거다 — `.` 이 "아무 글자"로 읽혔다.

비용 — `matches`·`lookingAt` 은 앵커가 있는 셈이라 대개 빠르고, `find` 는 **시작 위치를 옮겨 가며** 시도한다.

### (2) `Matcher` 는 상태를 가진다

**언제 쓰나** — `IllegalStateException: No match found` 를 만났을 때.

```text
Matcher m = p.matcher("abc123def456");

  상태: 커서=0, 마지막 매치=없음
        ↓ find()
  상태: 커서=6, 마지막 매치="123" (start=3, end=6)     -> group() 가능
        ↓ find()
  상태: 커서=12, 마지막 매치="456" (start=9, end=12)   -> group() 가능
        ↓ find()
  상태: 커서=끝, find() 가 false                        -> group() 는 예외
        ↓ reset()
  상태: 커서=0, 마지막 매치=없음                         -> group() 는 예외
```

실행 결과 (`Ex.java (37-a)`, JDK 21.0.5):

```text
--- find() 를 반복하면 어디까지 가나
  찾음: "123"  start=3 end=6
  찾음: "456"  start=9 end=12
  다시 find() = false  (끝까지 갔다)
  reset() 후 find() = true -> "123"
```

그림 해설 (한 단계씩):

- `find()` 가 **true 를 돌려준 뒤에만** `group()`·`start()`·`end()` 가 유효하다.
- `find()` 가 false 를 준 뒤에 `group()` 을 부르면 예외다 — 「어디서 틀리나」 4번.
- `reset()` 은 커서만 되돌린다. `reset(새 입력)` 으로 **같은 `Matcher` 에 다른 입력**을 물릴 수도 있다.

```text
--- Matcher 는 재사용 가능하지만 스레드 안전이 아니다
  첫 매치 1 / 둘째 22
  reset(다른 입력) 후 9
```

비용 — `Matcher` 를 새로 만드는 것은 싸다. **공유하지 말고 그때그때 만들라**는 것이 javadoc 의 결론이다.

### (3) 탐욕 · 게으름 · 소유 — 셋은 "되돌려주느냐"로 갈린다

**언제 쓰나** — `<.+>` 가 태그 하나가 아니라 줄 전체를 먹었을 때.

```text
입력 "<a><b></b></a>"

탐욕  <.+>    : .+ 가 끝까지 먹고, 뒤의 > 를 위해 하나씩 돌려준다
                +--------------------------------+
                | <a><b></b></a>                 |  -> "<a><b></b></a>"
                +--------------------------------+

게으름 <.+?>  : .+? 가 최소로 먹고, 안 되면 하나씩 더 먹는다
                +-----+
                | <a> |                            -> "<a>"
                +-----+

소유  <.++>   : .++ 가 끝까지 먹고 **절대 안 돌려준다**
                뒤의 > 가 먹을 글자가 없다          -> 매치 없음
```

실행 결과 (`Ex.java (37-b)`, JDK 21.0.5):

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

그림 해설 (한 단계씩):

- **탐욕(greedy, `*` `+` `?`)** — 먼저 최대한 먹고, 뒤가 안 맞으면 **되돌려준다**. 기본값이다.
- **게으름(reluctant, `*?` `+?` `??`)** — 먼저 최소로 먹고, 뒤가 안 맞으면 **더 먹는다**.
- **소유(possessive, `*+` `++` `?+`)** — 최대한 먹고 **되돌려주지 않는다.**\
  그래서 `a*+a` 는 절대 매치되지 않는다 — `a*+` 가 전부 삼켜 뒤의 `a` 가 굶는다.
- 소유 수량자의 값어치는 **백트래킹을 원천 차단**하는 것이다((5) 참고).

비용 — 되돌려주는 횟수가 곧 비용이다. **소유 > 게으름·탐욕**(빠른 쪽이 왼쪽) — 단 의미가 달라진다.

### (4) 그룹 — 번호·이름·역참조

**언제 쓰나** — 매치한 것 중 **일부만** 꺼내고 싶을 때.

```text
정규식  (\w+)@(\w+)\.(com|net)
        \___/  \___/  \______/
          1      2       3          <- 여는 괄호 순서로 번호가 붙는다

group(0) = 매치 전체
```

실행 결과 (`Ex.java (37-b)`, JDK 21.0.5):

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
--- 역참조 \1 — 같은 낱말이 두 번 나오는 곳
  중복: "the the"  (반복된 낱말=the)
  중복: "brown brown"  (반복된 낱말=brown)
--- 치환에서 그룹 참조 $1
  21/09/2026
  이름 참조 ${y} : 21.09.2026
```

그림 해설 (한 단계씩):

- **`groupCount()` 는 `group(0)` 을 세지 않는다.** 괄호 수와 같다.
- **`(?:...)` 는 그룹 번호를 차지하지 않는다** — 묶기만 하고 캡처는 안 한다. 번호가 밀리는 사고를 막는다.
- **이름 있는 그룹 `(?<user>...)`** 은 Java **7** 부터다. 번호를 세지 않아도 돼 유지보수가 낫다.
- **역참조 `\1`** 은 "앞에서 캡처한 것과 **같은 글자**"를 뜻한다 — 중복 낱말 찾기가 대표 용례다.
- 치환문에서는 `$1`(번호)·`${name}`(이름)이다. **`\1` 이 아니다** — 패턴 쪽과 표기가 다르다.

비용 — 캡처 그룹은 시작·끝 위치를 저장하므로 공짜가 아니다. **안 쓸 그룹은 `(?:...)` 로** 두는 것이 정석이고,\
`\1` 을 쓰면 **엔진의 백트래킹 최적화가 꺼진다**((5) 에서 이것이 결정적이다).

### (5) ★ 파국적 백트래킹 — 그리고 Java 가 실제로 하는 일

**언제 쓰나** — 정규식 하나가 CPU 를 100% 물고 안 끝날 때(ReDoS).

교과서적인 예는 **중첩 수량자**다.

```text
패턴 (x+x+)+y  ·  입력 "xxxxxxxxxxxxxxxxxxxx" (y 가 없어 반드시 실패한다)

  x 를 "몇 개씩 몇 덩어리로" 나눌지가 지수적으로 많다
      (1+1+1+...) (2+1+1+...) (1+2+1+...) ...
  전부 시도하고 전부 실패해야 "매치 없음"이 나온다
```

**그런데 JDK 17·21·25 에서 이 패턴은 터지지 않았다.**

```text
--- (x+x+)+y            입력 "xxx...x" (y 가 없어 반드시 실패한다)
  x 20 개         1 ms
  x 24 개         0 ms
  x 28 개         0 ms
  x 32 개         0 ms
  x 36 개         0 ms
  x 40 개         0 ms
```

이유는 JDK 소스에 **주석으로 적혀 있다** — `java.base/java/util/regex/Pattern.java` 의 `Loop.match`(JDK 21.0.5 원문).

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

**실패한 시작 위치를 기억해 두는 메모이제이션**이다. 그런데 켜지는 조건이 있다.

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

**즉 패턴에 역참조(`\1`)가 하나라도 있으면 이 방어가 통째로 꺼진다.**\
그래서 같은 패턴에 **의미 없는 역참조 하나**를 끼워 넣고 다시 돌렸다.

```text
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

```text
방어가 켜진 패턴  (x+x+)+y            방어가 꺼진 패턴  (a)\1?(x+x+)+y
+------------------------------+     +------------------------------+
| x 40 개 ->   0 ms            |     | x 30 개 -> 11,815 ms         |
| 입력이 길어도 평평하다        |     | x 가 2 개 늘 때마다 약 4배    |
+------------------------------+     +------------------------------+
  -> 실패한 위치를 기억한다            -> 매번 처음부터 다 해 본다
```

그림 해설 (한 단계씩):

- **입력 30 글자에 11.8 초**다. 요청 하나가 스레드를 12 초 붙잡으면 서비스가 멈춘다.
- **+2 글자마다 약 4배**(2^2)다 — 32 글자면 약 47 초, 34 글자면 약 3 분이다.\
  (이 외삽은 계산이 아니라 **측정된 기울기의 성질**이다. 실제 32 글자는 별도 실행에서 **42,847 ms** 였다.)
- **세 JDK(17·21·25)에서 거의 같은 곡선**이 나왔다 — 11,734 / 11,815 / 11,696 ms.

**그래서 무엇을 외우나**

- "Java 는 ReDoS 에 안전하다"도, "Java 도 위험하다"도 아니다.\
  **"그리디 루프 메모이제이션이 있고, 역참조가 있으면 꺼진다"**가 근거 있는 문장이다.
- 방어는 셋이다.

| 방어 | 어떻게 | 근거 |
|---|---|---|
| **소유 수량자** | `(a++)+b` 로 바꾼다 | (3) — 되돌려주지 않으니 폭발이 없다 |
| **중첩 제거** | `(a+)+` → `a+` 로 평평하게 | 의미가 같은 경우가 많다 |
| **입력 길이 제한** | 정규식 앞에서 `length()` 검사 | 지수라 길이 상한이 곧 시간 상한이다 |

실측으로 확인한 대안 (`Ex.java (37-e)`, JDK 21.0.5):

```text
--- 같은 입력, 소유 수량자 (a++)+b
  n=26      결과=false       0 ms
  n=1000    결과=false       0 ms
  n=100000  결과=false       5 ms
--- 같은 입력, 중첩을 없앤 a+b
  n=100000  결과=false       0 ms
```

비용 — 지수다. **입력 길이를 두 배로 늘리는 것이 아니라 두 글자 더하는 것**이 위험하다.

### (6) `Pattern` 컴파일 비용 — 재사용하면 3~4배

**언제 쓰나** — 루프·요청마다 `Pattern.compile` 또는 `String.matches` 를 부르는 코드를 볼 때.

같은 패턴(`^(\d{4})-(\d{2})-(\d{2})$`)으로 20만 건을 세 방식으로 검사했다 (`Ex.java (37-f)`).

```text
--- Pattern 재사용 대 매번 컴파일 (200,000건 x 6회, JDK 21.0.5, JMH 아님)
  1회차  매번 compile= 227 ms   미리 compile=  44 ms   String.matches= 187 ms
  2회차  매번 compile= 227 ms   미리 compile=  38 ms   String.matches= 152 ms
  3회차  매번 compile=  82 ms   미리 compile=  23 ms   String.matches=  79 ms
  4회차  매번 compile=  81 ms   미리 compile=  26 ms   String.matches=  84 ms
  5회차  매번 compile=  79 ms   미리 compile=  24 ms   String.matches=  84 ms
  6회차  매번 compile=  88 ms   미리 compile=  23 ms   String.matches=  78 ms
```

그림 해설 (한 단계씩):

- **1~2 회차는 웜업**이다(JIT 컴파일 전). 3 회차부터가 안정 구간이다.
- 안정 구간에서 **매번 compile ≈ 79~88 ms, 미리 compile ≈ 23~26 ms** — **약 3~4배**다.
- **`String.matches` 는 "매번 compile" 쪽**이다(78~84 ms). 내부에서 `Pattern.matches(regex, this)` 를 부르고,\
  그것이 매번 `Pattern.compile` 을 한다.
- 두 번째 실행에서도 같은 자릿수였다(68~72 / 18~21 / 67~80 ms). **재현되는 것은 3~4배라는 자릿수**다.

비용 — 정리하면 이렇다.

| 코드 | 언제 컴파일하나 | 쓸 자리 |
|---|---|---|
| `static final Pattern P = Pattern.compile(...)` | **클래스 로딩 때 한 번** | 기본값 |
| `Pattern.compile(...)` 를 루프 안에서 | 반복마다 | 패턴이 런타임에 정해질 때만 |
| `s.matches(regex)` | **호출마다** | 한두 번 쓰는 스크립트성 코드 |

## 문법 — 형태와 규칙

### 쓰는 순서

```java
Pattern p = Pattern.compile("(\\w+)@(\\w+)");   // 1) 컴파일 (필드에 두고 재사용)
Matcher m = p.matcher(input);                   // 2) 입력을 물린다
while (m.find()) {                              // 3) 당긴다
    String all  = m.group();                    // 4) 꺼낸다
    String user = m.group(1);
}
```

### 자주 쓰는 표기

| 표기 | 뜻 | 자바 문자열로 쓸 때 |
|---|---|---|
| `\d` `\w` `\s` | 숫자 / 낱말 글자 / 공백 | `"\\d"` — **역슬래시를 두 번** |
| `.` | 줄바꿈 뺀 아무 글자 (`DOTALL` 이면 줄바꿈도) | |
| `[abc]` `[^abc]` `[a-z]` | 문자 클래스 / 부정 / 범위 | |
| `*` `+` `?` `{n,m}` | 탐욕 수량자 | |
| `*?` `+?` `{n,m}?` | 게으름 | |
| `*+` `++` `{n,m}+` | **소유** | |
| `(...)` `(?:...)` `(?<n>...)` | 캡처 / 비캡처 / 이름 있는 그룹 | 이름 있는 그룹은 **7+** |
| `\1` `\k<n>` | 역참조 (패턴 안) | **메모이제이션을 끈다** — (5) |
| `$1` `${n}` | 치환문의 그룹 참조 | |
| `^` `$` `\b` | 줄 처음 / 줄 끝 / 낱말 경계 | `MULTILINE` 이면 줄마다 |

### 플래그

```text
--- 플래그
  대소문자 무시      : true
  인라인 (?i)        : true
  MULTILINE 없이 ^   : false
  MULTILINE 있고 ^   : true
  DOTALL 없이 .      : false
  DOTALL 있고 .      : true
```

- `Pattern.compile(regex, Pattern.CASE_INSENSITIVE)` 와 `"(?i)regex"` 는 같은 일을 한다.
- `MULTILINE` 은 `^`/`$` 를 **줄마다** 적용하게 한다. `DOTALL` 은 `.` 이 줄바꿈도 먹게 한다.

### `Matcher` 에서 꺼내는 법 (9+)

```text
--- Matcher.results() (9+) 로 전부 뽑기
  [12, 34]
--- replaceAll(Function) (9+)
  id=[24] name=jun id=[68] name=lee
--- appendReplacement / appendTail
  1:a 2:b
--- asPredicate(find 기준) 대 asMatchPredicate(matches 기준)
  asPredicate("ab1")      = true
  asMatchPredicate("ab1") = false
```

- `results()` 는 매치들을 **스트림**으로 준다 — `while (m.find())` 를 대체한다.
- `replaceAll(Function)` 은 **매치마다 계산해서** 치환한다(고정 문자열이 아닐 때).
- `asPredicate` 는 **`find` 기준**, `asMatchPredicate` 는 **`matches` 기준**이다 — 이름이 헷갈리니 표로 기억한다.

## 어디서 틀리나

### 1. ★ `split` 결과의 길이를 믿는다

**뒤쪽 빈 조각은 버려지고 앞쪽 빈 조각은 남는다.** 그리고 **빈 입력만 특별하다.**

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

```text
"a,b,,c,,".split(",")                  "a,b,,c,,".split(",", -1)
+--------------------------------+     +--------------------------------+
| a | b |  | c |                 |     | a | b |  | c |  |  |           |
| 길이 4 — 뒤 빈 조각 둘을 버림   |     | 길이 6 — 전부 남김              |
+--------------------------------+     +--------------------------------+
```

규칙은 `Pattern.split` 의 javadoc 이 적어 놓았다(JDK 21.0.5 `src.zip` 원문).

```text
If the limit is zero then the pattern will be applied as
many times as possible, the array can have any length, and trailing
empty strings will be discarded.

If the limit is negative then the pattern will be applied
as many times as possible and the array can have any length.
```

- **`"".split(",")` 은 길이 1** 이고 원소가 빈 문자열이다 — "패턴이 한 번도 안 맞으면 입력 전체를 담은 배열 하나"라는 규칙 때문이다.
- **`",".split(",")` 은 길이 0** 이다 — 조각 둘이 다 빈 문자열이라 뒤에서부터 전부 버려졌다.
- **CSV 를 `split(",")` 으로 읽으면 마지막 빈 칸들이 사라진다.** 열 수가 줄어드는 조용한 버그다.\
  방어: **`split(",", -1)`** 을 기본으로 쓴다.

### 2. `split`·`replaceAll` 의 인자가 정규식인 줄 모른다

```text
--- split 의 인자는 정규식이다
  "a.b.c".split(".")           길이=0  []
  "a.b.c".split("\\.")         길이=3  [a, b, c]
  "a|b".split("|")             길이=3  [a, |, b]
  "a|b".split(Pattern.quote("|")) 길이=2  [a, b]
```

- `split(".")` 은 **모든 글자가 구분자**가 되어 조각이 전부 빈 문자열 → 전부 버려져 길이 0.
- `split("|")` 은 `|` 가 **빈 대안(alternation)** 이라 글자 사이마다 잘린다.
- 방어: **`Pattern.quote`** 로 감싼다.

```text
--- Pattern.quote 가 만드는 것
  Pattern.quote("a.b|c") = \Qa.b|c\E
  Matcher.quoteReplacement("$1\\") = \$1\\
```

- `\Q ... \E` 는 "이 사이는 전부 글자 그대로"라는 표기다.
- **치환문 쪽은 `Matcher.quoteReplacement`** 로 따로 막아야 한다 — 패턴과 치환문은 이스케이프 규칙이 다르다.

```text
--- 치환문에서 $ 를 그대로 쓰려 하면
  java.lang.IndexOutOfBoundsException: No group 9
  quoteReplacement 쓰면 : $9
```

- `replaceAll("price", "$9")` 는 `$9` 를 **9번 그룹 참조**로 읽어 예외를 던진다.

### 3. 정규식 문법이 틀리면 — `PatternSyntaxException`

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
```

- **`PatternSyntaxException` 은 `RuntimeException`** 이다 — 컴파일러가 잡아 주지 않는다.
- 메시지가 **인덱스와 캐럿까지** 준다. 로그에 `getMessage()` 를 통째로 남기면 바로 고칠 수 있다.
- **`Pattern.compile` 은 클래스 로딩 때 부르는 편이 낫다** — 패턴 오타가 요청 처리 중이 아니라 기동 때 터진다.

### 4. `find()` 없이 `group()` — `IllegalStateException`

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
    No match found          <- JDK 21 · 25
```

**★ 여기가 버전이 갈린 유일한 자리다.**

```text
JDK 17.0.13 : No match available
JDK 21.0.5  : No match found
JDK 25.0.1  : No match found
```

- 같은 프로그램에서 `group()` 쪽은 **세 버전 모두 `No match found`** 였고, `start()` 쪽만 17 에서 달랐다.
- **예외 메시지를 문자열로 비교하는 테스트는 이런 자리에서 깨진다.** 타입으로 비교하라.

그 밖의 예외들.

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

- **셋이 서로 다른 예외 타입**이다 — 상태 문제는 `IllegalStateException`, 이름은 `IllegalArgumentException`, 번호는 `IndexOutOfBoundsException`.

### 5. 입력 검증에 `find()` 를 쓴다

```java
// 틀린 것
if (Pattern.compile("[0-9]+").matcher(input).find()) { ... }   // "12; DROP" 통과
// 맞는 것
if (Pattern.compile("[0-9]+").matcher(input).matches()) { ... }
```

- 또는 패턴에 `^...$` 앵커를 붙인다. 단 `MULTILINE` 이 켜지면 `$` 가 **줄 끝**이 되므로\
  `\A ... \z` 가 더 안전하다.

### 6. 정규식으로 할 일이 아닌 것을 정규식으로 한다

- **HTML·XML 파싱** — 중첩 구조는 정규식의 범위 밖이다. 파서를 쓴다.
- **JSON 파싱** — 같은 이유.
- **단순 포함 검사** — `contains`·`startsWith` 가 빠르고 안전하다.
- **고정 문자열 치환** — `replace` 가 정규식을 쓰지 않는다((1) 참고).

## 구현 세부사항 대 언어 보장

| 항목 | 누가 보장하나 | 근거 |
|---|---|---|
| `Pattern` 이 불변·스레드 안전, `Matcher` 는 아님 | **javadoc 계약** | `Pattern.java` 클래스 javadoc 원문 |
| `split` 의 limit 규칙(0=뒤 빈 조각 버림, 음수=전부) | **javadoc 계약** | (어디서 틀리나 1번의 인용) |
| `find`/`matches`/`lookingAt` 의 의미 | **javadoc 계약** | |
| 예외 **타입**(`IllegalStateException` 등) | **javadoc 계약** | |
| 예외 **메시지 문자열** | **구현** | 17 ↔ 21 에서 실제로 바뀌었다 |
| **그리디 루프 메모이제이션**(지수 백트래킹 차단) | **구현** | `Pattern.java` 의 주석 — javadoc 계약이 아니다 |
| 역참조가 있으면 그 최적화가 꺼지는 것 | **구현** | `hasGroupRef` 주석 |
| `(x+x+)+y` 가 빠른 것 | **구현** | 위 최적화의 결과 — 다른 JVM·다른 언어에서는 터진다 |
| 측정된 ms 값 | **머신·JIT** | 재현되는 것은 기울기와 자릿수 |

- ★ **여기가 이 주제에서 가장 중요한 경계다.** "Java 정규식은 ReDoS 에 안전하다"는 **명세가 아니라 구현**이고,\
  역참조 한 글자로 꺼진다. 코드 리뷰에서 "Java 니까 괜찮다"로 넘기면 안 되는 이유다.

## 언제 쓰고 언제 안 쓰나

| 쓴다 | 안 쓴다 |
|---|---|
| 형식 검증(날짜·전화·ID) — `matches` 로 | 중첩 구조(HTML·JSON·괄호 짝) |
| 로그·텍스트에서 필드 뽑기 — 이름 있는 그룹으로 | 단순 포함·접두사 — `contains`·`startsWith` |
| 규칙이 **설정으로 바뀌는** 치환 | 고정 문자열 치환 — `replace` |
| 토큰 나누기 — `split(regex, -1)` 로 | 성능이 극단적으로 중요한 핫패스(수동 파싱이 빠를 때) |
| 사용자 입력에 **길이 제한을 건 뒤** | 사용자가 **정규식 자체를 넣는** 기능(ReDoS 를 선물하는 것) |

## 핵심 문장

- **`matches`(전체) · `lookingAt`(앞) · `find`(아무 데나)는 서로 다른 질문**이다. 검증에는 `matches` 를 쓴다.
- **`Pattern` 은 재사용하고 `Matcher` 는 재사용하지 않는다** — javadoc 이 명시한 계약이다. 재사용하면 3~4배 빨랐다.
- **`split` 은 뒤쪽 빈 조각을 버린다.** 기본값은 `split(regex, -1)` 로 두는 것이 안전하다.
- **파국적 백트래킹은 Java 에도 있다.** 엔진의 메모이제이션이 막아 주지만 **역참조가 있으면 꺼진다** — 30글자에 11.8초를 봤다.
- **`replace` 는 정규식이 아니고 `replaceAll` 은 정규식이다.** 헷갈리면 `Pattern.quote` 로 막는다.

## 관련 자료

- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 37번)
- [`../35-string/`](../35-string/) — **경계: 그쪽은 「`String` 객체 하나가 무엇인가」와 `split` 의 *결과 배열*까지,
  여기는 「그 인자가 정규식으로 어떻게 해석되나」부터다.**\
  35번의 「어디서 틀리나」 5번(`split` 길이)과 이 문서 1번은 **같은 실행을 서로 다른 각도로** 본 것이다.
- [`../../../../../algorithm/25-string-matching/`](../../../../../algorithm/25-string-matching/) — **경계: 그쪽은 KMP·보이어-무어 같은
  문자열 매칭 *알고리즘*이 정본, 여기는 「`java.util.regex` API 를 어떻게 부르나」만.**\
  백트래킹 엔진이 왜 지수가 되는지의 이론은 그쪽이고, 여기는 **JDK 구현이 실제로 무엇을 하는지**다.
- [`../32-text-blocks/`](../32-text-blocks/) — **경계: 텍스트 블록은 raw 문자열이 아니다.**\
  정규식을 텍스트 블록에 적어도 `\\d` 는 그대로 `\\d` 다.
- [`../36-stringbuilder-and-concat/`](../36-stringbuilder-and-concat/) — `appendReplacement` 가 `StringBuilder` 를 받는 이유
- [`../25-exceptions/`](../25-exceptions/) — `PatternSyntaxException` 이 **검사 예외가 아닌** 이유
- [`../44-stream-creation/`](../44-stream-creation/) · [`../46-terminal-operations/`](../46-terminal-operations/) — `splitAsStream`·`results()` 가 만드는 스트림
- [`../../언어-특성/README.md`](../../언어-특성/README.md) — **경계: JIT 웜업이 왜 1~2 회차를 느리게 만드는지는 거기.**

## 용어 풀이

- **`Pattern`** — 컴파일된 정규식. 불변이고 스레드 안전이다(javadoc 계약). 만드는 데 비용이 든다.
- **`Matcher`** — `Pattern` 에 입력 하나를 물린 실행 상태. 가변이고 스레드 안전이 아니다.
- **`matches` / `lookingAt` / `find`** — 전체 일치 / 앞부분 일치 / 아무 데나 일치.
- **탐욕(greedy)** — 최대한 먹고 필요하면 되돌려주는 수량자. 기본값.
- **게으름(reluctant)** — 최소로 먹고 필요하면 더 먹는 수량자(`*?`).
- **소유(possessive)** — 최대한 먹고 **되돌려주지 않는** 수량자(`*+`). 백트래킹을 차단한다.
- **백트래킹** — 실패 시 되돌아가 다른 가능성을 시도하는 것.
- **파국적 백트래킹(catastrophic backtracking) / ReDoS** — 시도 가짓수가 지수로 늘어 짧은 입력에도 시간이 폭증하는 현상.
- **메모이제이션(memoization)** — 이미 실패한 상태를 기억해 다시 시도하지 않는 것. JDK 의 `Loop` 가 하는 일.
- **캡처 그룹 / 비캡처 그룹** — `(...)` 는 결과를 저장하고 `(?:...)` 는 묶기만 한다.
- **역참조(backreference)** — `\1` — 앞에서 캡처한 것과 **같은 글자**를 요구한다. 메모이제이션을 끈다.
- **`\Q...\E`** — 사이를 글자 그대로 읽으라는 표기. `Pattern.quote` 가 만든다.
- **앵커(anchor)** — `^`·`$`·`\A`·`\z`·`\b` 처럼 위치를 뜻하는 표기(글자를 먹지 않는다).

## 더 들어가면

- **`\1` 이 가리킬 그룹이 없어도 컴파일은 된다.**

```text
--- 가리킬 그룹이 없는 역참조 \1 은 컴파일은 되고 매치는?
  "abc" 에 find() = false
  "" 에 find()    = false
```

  `Pattern.compile("\\1abc")` 가 예외를 안 던지고, 매치만 실패한다.\
  **그리고 이 "아무것도 아닌" 역참조 하나가 백트래킹 방어를 끈다** — 실측으로 확인했다(`Ex.java (37-e6)`, JDK 21.0.5).

```text
--- (x+x+)+y                 <- 역참조 없음
  x 20 개         5 ms
  x 22 개         0 ms
  x 24 개         0 ms
  x 26 개         0 ms
--- \1?(x+x+)+y              <- 존재하지 않는 그룹을 가리키는 \1 하나를 앞에 붙였을 뿐
  x 20 개        19 ms
  x 22 개        44 ms
  x 24 개       178 ms
  x 26 개       753 ms
```

  `\1?` 는 **매치에 아무 영향도 주지 않는다**(가리킬 그룹이 없고 `?` 라서 없어도 된다).\
  그런데 그것만으로 0 ms 가 753 ms 가 됐다 — `hasGroupRef` 스위치가 켜졌기 때문이다.\
  (5) 의 실험이 이 성질을 이용한 것이다.

- **`Pattern.splitAsStream` 은 `split` 과 결과가 다를 수 있다.**

```text
  Pattern.compile(",").split("a,,")   길이=1  [a]
  Pattern.splitAsStream 개수 = 4       ("a,b,,c,," 에 대해)
```

  `split` 은 배열을 만들며 뒤쪽 빈 조각을 버리고, `splitAsStream` 은 **limit 0 규칙을 따르되 스트림**으로 준다.\
  두 입력이 다르므로 위 두 줄을 직접 비교하지 말고, **각각의 규칙을 따로** 기억한다.

- **`Arrays.asList` 처럼 `split` 도 "빈 것"의 처리가 특별하다.**\
  `"".split(",")` 이 길이 1 인 것은 javadoc 의 *"If this pattern does not match any subsequence of the input then the resulting array has just one element"* 에서 나온다.

- **한 `Matcher` 로 여러 입력을 처리할 수 있다** — `reset(CharSequence)`.\
  그래도 **스레드 간 공유는 안 된다.** 성능이 정말 문제면 `ThreadLocal<Matcher>` 를 쓰거나 그냥 매번 만든다\
  (`matcher()` 호출 자체는 `compile` 보다 훨씬 싸다).

- **`usePattern(Pattern)`**(5+)으로 입력은 그대로 두고 패턴만 바꿀 수도 있다.\
  토크나이저를 손으로 짤 때 쓰는 기법이다 — 커서를 유지한 채 다음에 기대하는 패턴으로 갈아 끼운다.

- **JDK 소스를 읽는 것이 가장 빠른 답이 되는 주제다.**\
  이 문서의 (5) 는 실행만으로는 **"왜 안 터지지?"에서 막혔다.**\
  `src.zip` 의 `Pattern.java` 주석 한 문단을 읽고 나서야 역참조라는 스위치를 찾았다.
