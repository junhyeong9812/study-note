# java/syntax/21 — `switch` 문과 `switch` 식 (14+): 화살표 · `yield` · 폴스루 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러 메시지는 Temurin JDK 에서 **실제로 돌려 얻은 것**이다.\
> 기본은 **21.0.5**이고, 도는 프로그램은 **17.0.13 · 25.0.1** 에서도 돌렸다.\
> ★ **이 주제는 세 판에서 바이트코드가 갈렸다.** 그 자리는 판을 명시했다.\
> 세 판에서 같았던 것은 "같았다"라고 **관찰로** 적었다 — 보장이 아니다.\
> 역어셈블은 `javap -c -p` 출력을 그대로 옮겼다. `javap` 는 **각 판의 javac 로 컴파일한 결과**를 찍은 것이다.\
> javadoc 인용은 JDK 21.0.5 의 `lib/src.zip` 에서 복사한 것이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `break` 를 빠뜨리면

**출력** (JDK 21.0.5 — 17 · 25 에서도 같았다)

```text
day=1  colonBuggy=수    colonFixed=월    arrow=월    arrowExpr=월    grouped=평일   scored=10
day=2  colonBuggy=수    colonFixed=화    arrow=화    arrowExpr=화    grouped=평일   scored=20
day=3  colonBuggy=수    colonFixed=수    arrow=수    arrowExpr=수    grouped=평일   scored=30
day=4  colonBuggy=그 밖  colonFixed=그 밖  arrow=그 밖  arrowExpr=그 밖  grouped=평일   scored=40
```

- `colonBuggy(1)` = **`"수"`**, `colonBuggy(2)` = **`"수"`**, `colonBuggy(4)` = `"그 밖"`.
- 1 로 들어가면 `case 2`·`case 3` 본문까지 실행되며 `s` 가 세 번 덮인다. `case 3` 의 `break` 에서 멈춘다.
- `default` 가 마지막에 있어도 **`case 3` 의 `break` 때문에 거기까지는 안 간다.**

**경고는 기본으로 안 나온다.** `-Xlint:fallthrough` 를 켜야 한다 — 돌려 확인했다.

```text
--- 기본
(아무 출력 없음)
--- -Xlint:fallthrough
Ex.java:7: warning: [fallthrough] possible fall-through into case
            case 2: s = "화";
            ^
Ex.java:8: warning: [fallthrough] possible fall-through into case
            case 3: s = "수"; break;
            ^
2 warnings
```

- 경고는 **2개**다. `case 1 -> case 2` 로 새는 자리와 `case 2 -> case 3` 으로 새는 자리를 각각 짚는다.
- 화살표로 바꾸면 **실수할 자리가 사라진다.** `break` 를 적을 필요도 없고 빠뜨릴 수도 없다.

### 2. 폴스루는 바이트코드에서 무엇인가

**출력** — `javap -c -p Ex.class` (JDK 21.0.5 의 javac)

```text
  static java.lang.String colonBuggy(int);
    Code:
       0: ldc           #7                  // String ?
       2: astore_1
       3: iload_0
       4: tableswitch   { // 1 to 3
                     1: 32
                     2: 35
                     3: 38
               default: 44
          }
      32: ldc           #9                  // String 월
      34: astore_1
      35: ldc           #11                 // String 화
      37: astore_1
      38: ldc           #13                 // String 수
      40: astore_1
      41: goto          47
      44: ldc           #15                 // String 그 밖
      46: astore_1
      47: aload_1
      48: areturn
```

```text
  static java.lang.String arrowExpr(int);
    Code:
       0: iload_0
       1: tableswitch   { // 1 to 3
                     1: 28
                     2: 33
                     3: 38
               default: 43
          }
      28: ldc           #9                  // String 월
      30: goto          45
      33: ldc           #11                 // String 화
      35: goto          45
      38: ldc           #13                 // String 수
      40: goto          45
      43: ldc           #15                 // String 그 밖
      45: areturn
```

**왜 그런가**

- **분기 선택 명령은 같다** — 둘 다 `tableswitch { // 1 to 3 }` 이다.
- **`goto` 의 개수가 다르다.** 콜론 쪽은 **1개**(오프셋 41, `break` 를 적은 가지), 화살표 쪽은 **3개**다.
- ★ 한 문장으로: **"화살표는 가지마다 `goto` 를 붙여 다음 가지로 흘러갈 길을 없앤다."**\
  컴파일러가 `break` 를 "대신 넣어 주는" 것이 아니라, **가지의 끝이 문법으로 정해져 있는 것**이다.
- **더 빨라지지 않는다.** 분기 방식이 같고, 늘어난 것은 `goto` 3바이트씩이다.\
  화살표의 이득은 **정확성과 가독성**이지 속도가 아니다.

```text
  콜론 (break 누락)                        화살표
  case 1 ----+                            case 1 --> goto 끝
             |  흘러 들어감
  case 2 ----+                            case 2 --> goto 끝
             |
  case 3 --> goto 끝                       case 3 --> goto 끝
```

### 3. `tableswitch` 와 `lookupswitch`

**출력** — `javap -c -p Ex.class` (JDK 21.0.5)

```text
  static java.lang.String dense(int);
    Code:
       0: iload_0
       1: tableswitch   { // 1 to 3
                     1: 28
                     2: 33
                     3: 38
               default: 43
          }
```

```text
  static java.lang.String sparse(int);
    Code:
       0: iload_0
       1: lookupswitch  { // 3
                     1: 36
                   500: 41
                  9999: 46
               default: 51
          }
```

**왜 그런가**

- `dense` 는 **`tableswitch`**, `sparse` 는 **`lookupswitch`** 다.
- 가르는 것은 **`case` 값이 얼마나 촘촘한가**다. 소스에서는 고를 수 없다 — **javac 가 정한다.**
- `{ // 1 to 3 }` 은 **범위**다. 점프 테이블이 1·2·3 세 칸이고, 값에서 1 을 빼 인덱스로 쓴다.
- `{ // 3 }` 은 **개수**다. 키-오프셋 쌍 셋을 정렬해 두고 찾아본다.

| | `tableswitch` | `lookupswitch` |
|---|---|---|
| 구조 | 범위 점프 테이블 | 정렬된 키-오프셋 목록 |
| 찾는 비용 | 상수 시간 | 로그 시간 |
| 공간 | 범위 크기만큼 | 키 개수만큼 |
| 언제 골라지나 | 값이 촘촘할 때 | 값이 흩어졌을 때 |

- `case 1` 과 `case 1000` 둘만 있으면 테이블이 1000칸이 되므로 javac 가 `lookupswitch` 를 고른다.
- ★ **`switch (String)` 은 또 다르다.** `hashCode()` 로 후보를 좁히고 `equals` 로 확인하는 **2단계**다.\
  정본은 [**35번 주제**](../35-string/)다 — 거기서 `hashCode` + `lookupswitch` 형태를 바이트코드로 다뤘다.

### 4. ★ 완결한 `enum` `switch` 식의 바이트코드

**출력** — JDK 21.0.5 의 javac

```text
  static java.lang.String kindExpr(Ex$Day);
    Code:
       0: aload_0
       1: invokevirtual #7                  // Method Ex$Day.ordinal:()I
       4: tableswitch   { // 0 to 3
                     0: 46
                     1: 46
                     2: 51
                     3: 51
               default: 36
          }
      36: new           #13                 // class java/lang/MatchException
      39: dup
      40: aconst_null
      41: aconst_null
      42: invokespecial #15                 // Method java/lang/MatchException."<init>":(Ljava/lang/String;Ljava/lang/Throwable;)V
      45: athrow
      46: ldc           #18                 // String 평일
      48: goto          53
      51: ldc           #20                 // String 주말
      53: areturn
```

**출력** — JDK 17.0.13 의 javac (같은 소스)

```text
  static java.lang.String kindExpr(Ex$Day);
    Code:
       0: getstatic     #7                  // Field Ex$1.$SwitchMap$Ex$Day:[I
       3: aload_0
       4: invokevirtual #13                 // Method Ex$Day.ordinal:()I
       7: iaload
       8: tableswitch   { // 1 to 4
                     1: 48
                     2: 48
                     3: 53
                     4: 53
               default: 40
          }
      40: new           #19                 // class java/lang/IncompatibleClassChangeError
      43: dup
      44: invokespecial #21                 // Method java/lang/IncompatibleClassChangeError."<init>":()V
      47: athrow
      48: ldc           #22                 // String 평일
      50: goto          55
      53: ldc           #24                 // String 주말
      55: areturn
```

**왜 그런가**

- 소스에 `default` 가 없어도 **바이트코드에는 `default:` 가 있다.** 하는 일은 **예외를 던지는 것뿐**이다.
- 이 `switch` 에는 패턴이 하나도 없다. **그런데도 21 에서는 `MatchException` 이다.**\
  ★ 그러니 `MatchException` 을 "패턴 매칭 전용"으로 외우면 틀린다 —\
  **"완결하다고 판정했는데 런타임에 안 맞았다"** 가 이 예외의 조건이고, `enum` 상수도 그 대상이다.
- **17 과 21 은 두 군데가 다르다.**

| | JDK 17.0.13 의 javac | JDK 21.0.5 · 25.0.1 의 javac |
|---|---|---|
| 분기 인덱스 | `Ex$1.$SwitchMap$Ex$Day` 배열을 거친다 | `ordinal()` 을 **바로** 쓴다 |
| 범위 | `// 1 to 4` (맵이 1부터 매긴다) | `// 0 to 3` (ordinal 그대로) |
| `default:` 가 던지는 것 | `IncompatibleClassChangeError` | `MatchException` |
| 합성 클래스 | `Ex$1` 이 생긴다 | 안 생긴다 |

- **실행 출력은 세 판에서 같았다.** 그러나 바이트코드는 달랐다 — 이것이 "출력이 같으면 같다"를 반박하는 실례다.
- `$SwitchMap` 이 왜 존재하는지(상수 순서가 바뀌어도 옳게 돌기 위한 장치)는 [`../13-enum-classes/`](../13-enum-classes/)가 정본이다.
- `MatchException` 이 21 부터인 근거는 javadoc 이다 (JDK 21.0.5 `src.zip`).

```text
 * @jls 14.11.3 Execution of a {@code switch} Statement
 * @jls 14.30.2 Pattern Matching
 * @jls 15.28.2 Run-Time Evaluation of {@code switch} Expressions
 *
 * @since 21
```

### 5. 식이냐 문이냐로 갈리는 것

**출력** (JDK 21.0.5 — 17 · 25 에서도 같았다)

```text
MON  expr=평일    stmt=월
TUE  expr=평일    stmt=화
SAT  expr=주말    stmt=안 걸림
SUN  expr=주말    stmt=안 걸림
```

**왜 그런가**

- (a) 식은 **`default` 없이 컴파일된다.** `enum` 상수 넷을 전부 덮었기 때문이다.
- (b) 문은 **상수를 둘만 적어도 컴파일된다.** 완결성 검사가 아예 돌지 않는다.
- `kindStmt(Day.SAT)` 는 `"안 걸림"` 이다 — `switch` 에 들어갔다가 **아무것도 안 하고 나온다.**
- ★ 한 문장으로: **"식은 값이 되어야 하므로 모든 입력에 값이 있어야 하고, 문은 값이 안 되므로 그럴 필요가 없다."**

```text
  switch 식                                switch 문 (옛 selector)
  +-----------------------------+          +-----------------------------+
  | String s = switch (d) {...} |          | switch (d) { ... }          |
  | 이 자리에 값이 와야 한다      |          | 값이 오는 자리가 아니다       |
  | -> 안 덮이면 값이 없다       |          | -> 안 덮이면 그냥 나간다      |
  | -> 컴파일 에러               |          | -> 아무 말도 안 해 준다       |
  +-----------------------------+          +-----------------------------+
```

- ★ **패턴을 쓰는 `switch` 문에는 그대로가 아니다.** 패턴 `switch` 는 **문에도 완결성을 요구한다** — 돌려 확인했다.

```java
Object o = "a";
switch (o) {                       // 문(statement) 인데 패턴을 쓴다
    case String s -> System.out.println("문자열");
    case Integer i -> System.out.println("정수");
}
```

```text
Ex.java:4: error: the switch statement does not cover all possible input values
        switch (o) {                       // 문(statement) 인데 패턴을 쓴다
        ^
1 error
```

- 메시지가 `the switch **statement**` 라고 말한다. 경계는 「문이냐 식이냐」만이 아니라\
  **「옛 selector 냐 패턴이냐」**에도 걸려 있다. 그쪽 규칙은 [**23번 주제**](../23-switch-pattern-matching/)가 정본이다.

### 6. `yield` 와 블록 가지

**출력** (JDK 21.0.5 — 17 · 25 에서도 같았다)

```text
day=3  ... scored=30
```

- `scored(3)` = **30**(`base * day` = 10 × 3), `scored(6)` = **0**.

**`return` 을 쓰면**

```text
Ex.java:4: error: attempt to return out of a switch expression
            case 1 -> { return "하나"; }
                        ^
1 error
```

**값도 안 내고 `throw` 도 안 하면**

```text
Ex.java:4: error: switch rule completes without providing a value
            case 1 -> { String s = "하나"; }
                                         ^
  (switch rules in switch expressions must either provide a value or throw)
1 error
```

**왜 그런가**

- 괄호 설명이 규칙 전부다 — **`switch` 식의 가지는 값을 내거나 던져야 한다.**
- `return` 은 메서드를 끝내는 문이다. `switch` **식**은 값이 되는 자리이므로 거기서 메서드를 끝낼 수 없다.
- **콜론 문법으로도 `switch` 식을 쓸 수 있다** — 돌려 확인했다(`Ex.java (21-d)`).

```java
static String colonExpr(int n) {
    return switch (n) {
        case 1:
        case 2:
            yield "작다";
        case 3: {
            String s = "보통";
            yield s;
        }
        default:
            yield "크다";
    };
}
```

```text
1:작다 2:작다 3:보통 4:크다 
```

- 콜론 식에서는 **화살표 자리가 콜론일 뿐** 값은 항상 `yield` 로 낸다.
- `case 1:` 과 `case 2:` 를 연달아 적어 **의도된 폴스루**로 묶는 것도 된다. 다만 화살표의 쉼표가 더 명확하다.

### 7. `switch` 식이 안 덮었을 때

**출력**

```text
Ex.java:3: error: the switch expression does not cover all possible input values
        return switch (n) {
               ^
1 error
```

**왜 그런가**

- `default -> "?"` 를 넣으면 통과한다. `default` 가 "나머지 전부"를 덮기 때문이다.
- **`int` 를 `default` 없이 완결할 방법은 사실상 없다.** `int` 의 값은 40억 개가 넘고,\
  `case` 는 상수 하나씩만 받는다. `enum`·`sealed` 처럼 **선택지가 닫힌 타입**에서만 `default` 를 뺄 수 있다.
- 같은 본문을 `switch` **문**으로 바꾸면 컴파일된다 — 5번의 (b) 가 그 형태다.
- 이 에러는 **받으려고 만든 에러**다. `enum`·`sealed` 에 선택지가 늘 때 빌드를 멈추게 하는 장치가 이것이다.\
  `sealed` 쪽 정본은 [`../15-sealed-classes/`](../15-sealed-classes/)다.

### 8. 섞으면 안 되는 것 셋

**출력** — (a) 화살표와 콜론을 섞음

```text
Ex.java:5: error: different case kinds used in the switch
            case 2: yield "둘";
            ^
1 error
```

**출력** — (b) `switch` 식 안에서 `return`

```text
Ex.java:4: error: attempt to return out of a switch expression
            case 1 -> { return "하나"; }
                        ^
1 error
```

**출력** — (c) `case` 에 변수

```text
Ex.java:6: error: constant expression required
            case limit -> System.out.println("상수가 아니다");
                 ^
1 error
```

**왜 그런가**

- (a) **한 `switch` 안에서는 한 문법만.** 옛 코드를 옮길 때 가지를 하나씩 바꾸면 이 에러를 만난다.
- (c) `static final int LIMIT = 3;` 으로 바꾸면 **통과한다** — 돌려 확인했다(`Ex.java (21-f)`).

```text
constCase(3) = 상수 식은 된다
```

- ★ **3번과 이어진다** — `tableswitch`/`lookupswitch` 에는 **숫자가 박혀야** 한다.\
  런타임에 정해지는 값은 그 테이블에 넣을 수 없다. 그래서 `case` 는 컴파일 상수만 받는다.
- `enum` 상수가 예외적으로 허용되는 것은 javac 가 `ordinal()` 로 숫자를 만들어 주기 때문이다(4번).

**중복 레이블 둘**

```text
Ex.java:6: error: duplicate case label
            case 1 -> System.out.println("또 하나");
            ^
1 error
```

```text
Ex.java:6: error: duplicate default label
            default -> "??";
            ^
1 error
```

- 분기표에 같은 키가 둘일 수 없다. 복사·붙여넣기로 만든 긴 `switch` 에서 흔하다 — **좋은 에러**다.

### 9. `yield` 는 예약어인가

**출력** — (a) `switch` 식 밖에서 `yield`

```text
Ex.java:3: error: yield outside of switch expression
        if (n > 0) yield n;
                   ^
1 error
```

**출력** — (b) 메서드 `yield` 를 한정 없이 호출

```text
Ex.java:24: error: invalid use of a restricted identifier 'yield'
        System.out.println("변수 yield = " + yield + " / 메서드 yield(3) = " + yield(3));
                                                                          ^
  (to invoke a method called yield, qualify the yield with a receiver or type name)
1 error
```

- ★ **이 에러는 17 · 21 · 25 에서 한 글자도 같았다.** 세 판에서 돌려 확인했다.

**왜 그런가**

- **변수 `yield` 는 선언할 수 있다.** 메시지도 변수 쪽이 아니라 **호출 쪽**(`yield(3)`)을 가리킨다.
- 괄호 설명이 고치는 법이다 — **한정하면 된다.** `Ex.yield(3)` 으로 고치니 통과했다.

```text
1:작다 2:작다 3:보통 4:크다 
변수 yield = 5 / 메서드 yield(3) = 6
```

- `yield` 는 **제한 식별자(restricted identifier)** 다. 특정 문맥에서만 키워드처럼 읽힌다.
- **`goto` 와 다르다.** `goto` 는 진짜 예약어라 변수 이름으로도 못 쓴다 —\
  [**20번 주제**](../20-control-flow-statements/)에서 `int goto = 2;` 가 파싱 에러로 막히는 것을 확인했다.

| | `yield` | `goto` |
|---|---|---|
| 분류 | 제한 식별자 | 예약어 |
| 변수 이름으로 | 된다 | 안 된다 |
| 메서드 이름으로 | 된다 (호출은 한정 필요) | 안 된다 |
| 기능이 있나 | 있다 (`switch` 식) | 없다 (자리만 예약) |

### 10. ★ `enum` 에 상수를 추가하고 `switch` 를 안 고쳤다

**출력** — JDK 21.0.5

```text
--- 1차 컴파일 (21)
(성공)
--- 실행
SAT -> 주말
--- 2차 컴파일: Day 만 다시 (Ex 는 그대로)
(성공)
--- 기존 상수
SAT -> 주말
--- 새 상수
Exception in thread "main" java.lang.MatchException
	at Ex.kind(Ex.java:3)
	at Ex.main(Ex.java:10)
```

**출력** — JDK 17.0.13 (같은 소스·같은 시나리오)

```text
--- 1차 컴파일 (17)
(성공)
--- 2차 컴파일: Day 만
(성공)
--- 기존 상수
SAT -> 주말
--- 새 상수
Exception in thread "main" java.lang.IncompatibleClassChangeError
	at Ex.kind(Ex.java:3)
	at Ex.main(Ex.java:10)
```

**왜 그런가**

- 2차 컴파일은 **성공한다.** `Day` 만 보면 아무 문제가 없다.
- `java Ex SAT` 는 `SAT -> 주말` 이다 — **기존 경로는 그대로 돈다.**
- `java Ex HOLIDAY` 는 **`java.lang.MatchException`**(21·25) / **`java.lang.IncompatibleClassChangeError`**(17).
- ★ 같은 시나리오인데 **예외 이름이 다르다.** 21 에서 `MatchException` 으로 통일된 것이다.
- javac 가 못 막는 이유: **완결성 검사는 `Ex.java` 를 컴파일하는 시점에만 돈다.**\
  그 뒤에 `Day` 가 바뀌어도 이미 찍힌 `Ex.class` 는 옛 판정을 들고 있다.

```text
  Ex.java 를 컴파일할 때                   Day.java 만 다시 컴파일한 뒤
  +-----------------------------+         +-----------------------------+
  | Day 의 상수 = 4개            |         | Day 의 상수 = 5개            |
  | 네 가지를 전부 덮었다         |         | Ex.class 는 그대로 (4개 기준) |
  | -> 완결. default: 는          |         | -> HOLIDAY 가 default: 로 간다|
  |    예외를 던지는 가지로만     |         | -> 예외                      |
  +-----------------------------+         +-----------------------------+
```

- 실무 함의: **`enum` 에 상수를 추가하는 것은 바이너리 호환이 깨지는 변경**이다.\
  그 `enum` 을 `default` 없이 `switch` 하는 코드가 있다면 **같이 재컴파일**해야 한다.
- `sealed` 계층에서 같은 일이 벌어지는 쪽은 [`../15-sealed-classes/`](../15-sealed-classes/)가 정본이다.

### 11. 옛 `switch` 에 `null` 을 넣으면

**출력** (JDK 21.0.5 — 17 · 25 에서도 같았다)

```text
enum   -> Cannot invoke "Ex$Day.ordinal()" because "<parameter1>" is null
String -> Cannot invoke "String.hashCode()" because "<local1>" is null
```

**왜 그런가**

- `enum` 쪽은 **`ordinal()`** 이 메시지에 박힌다 — 4번의 바이트코드 첫 줄이 그것이다.
- `default` 가 있는데도 `default` 로 안 가는 이유: **`default` 에 도달하기 전에 터진다.**\
  분기 인덱스를 구하려면 `ordinal()` 을 불러야 하는데, 그 호출 자체가 NPE 다.
- `String` 쪽은 **`hashCode()`** 다. `switch (String)` 이 해시로 후보를 좁히기 때문이다.\
  그 2단계 컴파일은 [**35번 주제**](../35-string/)가 정본이다.

```text
  switch (enum)                            switch (String)
  +-----------------------------+          +-----------------------------+
  | ordinal() 호출               |          | hashCode() 호출              |
  |   -> null 이면 여기서 NPE    |          |   -> null 이면 여기서 NPE    |
  | tableswitch                  |          | lookupswitch (해시)          |
  |                              |          | equals 로 확인               |
  +-----------------------------+          +-----------------------------+
    default 에 도달하지 못한다               default 에 도달하지 못한다
```

- **`case null` 은 Java 21 의 패턴 `switch`** 부터다. 정본은 [**23번 주제**](../23-switch-pattern-matching/)다.\
  여기서는 **"옛 `switch` 에서는 무조건 NPE"** 까지만 외운다.

### 12. 무엇이 보장이고 무엇이 판마다 다른가

**왜 그런가**

- **17 · 21 · 25 사이에 달랐던 것 둘**.
  1. **완결 `enum` `switch` 식의 `default:` 가 던지는 예외** — 17 은 `IncompatibleClassChangeError`, 21·25 는 `MatchException`.
  2. **같은 파일 `enum` `switch` 의 분기 인덱스 방식** — 17 은 `$SwitchMap` 경유, 21·25 는 `ordinal()` 직접.
- **실행 출력이 같았다는 것으로 주장할 수 있는 것**: "내가 돌린 이 세 판에서 이 프로그램의 출력이 같았다."
- **주장할 수 없는 것**: "이 동작은 보장된다" · "바이트코드가 같다" · "다른 판에서도 같을 것이다."\
  ★ 이 주제가 그 반례다 — **출력이 같은데 바이트코드가 달랐다.**
- `MatchException` 은 **Java 21** 부터다. 근거는 `MatchException.java` 의 `@since 21` 태그다(4번에 인용).
- `tableswitch`/`lookupswitch` 선택은 **구현 세부**다. javac 가 값의 촘촘함으로 고르고, 소스에서 지정할 방법이 없다.

| 보장으로 적어도 되는 것 | 이 판에서 그랬다고만 적어야 하는 것 |
|---|---|
| 식은 완결해야 한다 | `default:` 가 던지는 예외 클래스 |
| 문(옛 selector)은 완결 안 해도 된다 | `$SwitchMap` 경유 여부 |
| 화살표에 폴스루가 없다 | `tableswitch` 냐 `lookupswitch` 냐 |
| `yield` 는 `switch` 식 전용 | `goto` 개수·오프셋 숫자 |
| `case` 는 상수 식만 | 에러 메시지의 문구 |

### 13. 정본 경계와 선택

**왜 그런가**

| 주제 | 그쪽이 다루는 것 | 여기가 다루는 것 |
|---|---|---|
| [**13번**](../13-enum-classes/) `enum` | `case MON` 을 한정 없이 쓰는 근거 · `case Day.MON` 의 버전 갈림 · `$SwitchMap` 의 존재 이유 | 그 규칙이 **`switch` 식에서도 같다**는 것 · 17/21 전략 차이 |
| [**23번**](../23-switch-pattern-matching/) 패턴 `switch` | `case null` · `when` 가드 · 패턴 `case` · 지배 관계 | **패턴이 하나도 없는 `switch`** 만 |
| [**35번**](../35-string/) `String` | `switch (String)` 의 `hashCode` + `lookupswitch` 2단계 | 링크만 한다 |
| [**15번**](../15-sealed-classes/) `sealed` | `sealed` 계층의 완결성과 `MatchException` | `enum` 쪽의 같은 현상만 |
| [**20번**](../20-control-flow-statements/) 제어문 | `break` 가 **루프**에서 하는 일 | `break` 가 **`switch`** 에서 하는 일 |

- **`default` 를 넣을지 말지**: **"선택지가 앞으로 늘어날 것인가"** 로 판단한다.\
  늘어날 것이면 `default` 로 방어하고, 늘어나면 안 되는 것이면 `default` 를 빼서 **빌드가 멈추게** 한다.
- **가지에 블록이 셋 이상 생기면** 그것은 **`switch` 가 아니라 다형성일 때**라는 신호다.\
  `enum` 상수별 본문([`../13-enum-classes/`](../13-enum-classes/))이나 `sealed` + 타입별 메서드로 옮긴다.
- **`case 1, 2, 3 ->` 와 옛 `case 1: case 2: case 3:` 는 같지 않다.**

```text
  case 1: case 2: case 3: doX(); break;    case 1, 2, 3 -> doX();
  +-----------------------------+          +-----------------------------+
  | 레이블 셋이 한 본문을 공유    |          | 레이블 셋이 한 가지를 가리킴  |
  | break 를 빼면 아래로 샌다     |          | 샐 자리가 없다               |
  | -Xlint 가 폴스루로 볼 수 있다 |          | 폴스루라는 개념이 없다        |
  +-----------------------------+          +-----------------------------+
    결과는 같지만 실수의 여지가 다르다
```

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Ex (21-a)` | 폴스루 실측(`colonBuggy(1)="수"`) · 화살표 문/식 · 쉼표 레이블 · 블록 가지 `yield` | 17 · 21 · 25 (출력 동일) |
| `Ex (21-a)` + `javap -c -p` | 콜론은 `goto` 1개, 화살표는 3개 · `tableswitch` 는 양쪽 동일 | 21 |
| `Ex (21-a)` + `-Xlint:fallthrough` | 기본은 무경고, 켜면 경고 2개 | 21 |
| `Ex (21-b)` + `javap -c -p` | 촘촘 -> `tableswitch { // 1 to 3 }` · 흩어짐 -> `lookupswitch { // 3 }` | 21 |
| `Ex (21-c)` | `enum` 식은 `default` 없이 통과 · 문은 상수를 빠뜨려도 통과하고 **조용히 지나간다** | 17 · 21 · 25 (출력 동일) |
| `Ex (21-c)` + `javap -c -p` | ★ **17 은 `$SwitchMap` + `IncompatibleClassChangeError`, 21·25 는 `ordinal()` + `MatchException`** | 17 · 21 · 25 (**바이트코드 다름**) |
| `Ex (21-d)` | 콜론 문법의 `switch` 식 · `yield` 변수/메서드(한정 호출) | 17 · 21 · 25 (출력 동일) |
| `Ex (21-e9)` | `yield(3)` 무한정 호출 -> `invalid use of a restricted identifier 'yield'` | 17 · 21 · 25 (**메시지 동일**) |
| `Ex (21-f)` | `case LIMIT`(컴파일 상수) 통과 · `case 1 -> null` 통과 | 17 · 21 · 25 (출력 동일) |
| `Ex (21-g)` | 옛 `switch` 에 `null` — `enum` 은 `ordinal()`, `String` 은 `hashCode()` 에서 NPE | 17 · 21 · 25 (출력 동일) |
| `21-rt` (2파일, 2단계 컴파일) | `enum` 상수 추가 후 미재컴파일 -> **`MatchException`** | 21 |
| `21-rt` (같은 시나리오) | 같은 소스인데 -> **`IncompatibleClassChangeError`** | 17 |
| `21-rt` (같은 시나리오) | 21 과 같은 `MatchException` | 25 |
| `Ex (21-e1)` | 식이 안 덮음 -> `does not cover all possible input values` | 21 |
| `Ex (21-e2)` | 화살표/콜론 혼용 -> `different case kinds used in the switch` | 21 |
| `Ex (21-e3)` | 식 안 `return` -> `attempt to return out of a switch expression` | 21 |
| `Ex (21-e4)` | 값 없는 블록 가지 -> `switch rule completes without providing a value` | 21 |
| `Ex (21-e5)` | `case` 에 변수 -> `constant expression required` | 21 |
| `Ex (21-e6)` / `(21-e8)` | `duplicate case label` / `duplicate default label` | 21 |
| `Ex (21-e7)` | `switch` 밖 `yield` -> `yield outside of switch expression` | 21 |
| `Ex (23-e10)` | 패턴 `switch` **문**은 완결성을 요구한다 -> `the switch statement does not cover ...` | 21 |
| `src.zip` (`MatchException.java`) | `@since 21` · `@jls` 셋 | 21.0.5 |

**합계** — 프로그램 15개 + 분리 컴파일 3벌 · `javac` 41회 · `java` 21회 · `javap` 6회 · `-Xlint` 1회.

**구현 의존 항목** — 버전이 오르면 다시 돌려야 하는 것

- ★ **`default:` 가 던지는 예외 클래스**. 17 과 21 에서 달랐다. 다음 판에서 또 바뀔 수 있다.
- ★ **`enum` `switch` 의 분기 인덱스 전략**(`$SwitchMap` 경유 여부). 17 과 21 에서 달랐다.
- **`tableswitch` 냐 `lookupswitch` 냐** 는 javac 가 값의 촘촘함으로 고른다. 경계값은 명세가 아니다.
- **`goto` 의 개수·오프셋 숫자**는 코드 생성 방식이다.\
  외울 것은 명령 이름이 아니라 **"화살표 가지는 흘러갈 길이 없다"** 는 성질이다.
- **에러 메시지의 문구 자체**는 javac 의 것이다. 다만 9번의 `yield` 메시지는 세 판에서 같았다 — **관찰**이다.
- 세 판에서 출력이 같았던 것은 **관찰**이다. 이 주제에서는 그 관찰이 **바이트코드 동일성을 뜻하지 않았다.**
