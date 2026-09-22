# java/syntax/21 — `switch` 문과 `switch` 식 (14+): 화살표 · `yield` · 폴스루 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — JDK 21.0.5 의 `lib/src.zip` 을 **직접 풀어 읽은** javadoc 하나다.\
> `java.base/java/lang/MatchException.java` — `@since 21`, `@jls 14.11.3` `@jls 14.30.2` `@jls 15.28.2`.\
> JLS 절 번호는 **그 javadoc 의 `@jls` 태그에 적힌 것만** 옮겼다. JLS 본문은 열지 않았다.
> **실행 검증** — 이 문서의 모든 출력·에러 메시지는 Temurin JDK 에서 실제로 돌려 얻은 것이다.\
> 프로그램 5개 + 컴파일 에러용 9개 + 분리 컴파일 시나리오 3벌(17·21·25).\
> `javac` 41회 · `java` 21회 · `javap` 6회 · `-Xlint:fallthrough` 1회. 도는 프로그램은 **17.0.13 · 21.0.5 · 25.0.1 셋 다**에서 돌렸다.\
> ★ 이 주제는 **세 판에서 바이트코드가 갈렸다** — 그 자리를 따로 표시했다.\
> 역어셈블은 `javap -c -p` 출력을 **그대로** 옮겼다.
> **버전** — 화살표 `->` · `switch` **식** · `yield` 는 **Java 14** 정식(12·13 프리뷰).\
> `case null` 과 타입 패턴은 **21** 이다 — 이 주제가 아니라 [**23번 주제**](../23-switch-pattern-matching/)다.\
> `MatchException` 은 **21**. 그 전에는 같은 자리에 `IncompatibleClassChangeError` 가 들어갔다 — **돌려 확인했다.**
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 javac 의 실제 에러 메시지와 `javap` 출력으로 접지했다.

## 한눈에 — 쉽게 말하면

**옛 `switch` 는 「문이 없는 칸막이 방들」이다. 화살표 `switch` 는 「문이 달린 방들」이다.**

옛 `switch` 에서 `case` 는 **들어가는 자리를 정할 뿐**이고, 나가는 것은 `break` 를 적어야 한다.\
안 적으면 옆방으로 계속 걸어간다. 이것이 폴스루(fall-through)다.\
화살표는 **방마다 문을 달았다** — 한 칸을 실행하면 끝이다.

그리고 한 걸음이 더 있다. **`switch` 가 값을 돌려주는 식(expression)이 되면서 완결성이 요구된다.**\
값을 돌려줘야 하니 **"어떤 입력에도 돌려줄 값이 있어야"** 하기 때문이다.

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 칸막이 방 | `case 1:` — 레이블(들어가는 자리) |
| 문이 없어 옆방으로 걸어감 | 폴스루 — `break` 를 안 적었을 때 |
| 문을 달았다 | `case 1 ->` — 화살표 규칙 |
| 방에서 물건을 들고 나옴 | `switch` **식**이 값을 돌려주는 것 |
| 방이 넓어 물건을 고르는 작업이 필요 | 블록 가지 `-> { ... yield v; }` |
| **"어느 방에 들어가도 물건이 있어야 한다"** | **완결성(exhaustiveness)** |
| 방 번호표를 늘어놓은 게시판 | `tableswitch` — 값이 촘촘할 때 |
| 방 번호를 찾아보는 색인 | `lookupswitch` — 값이 흩어졌을 때 |
| 번호표를 인쇄한 뒤 방이 늘었다 | 분리 컴파일 -> `MatchException` |

```text
콜론 switch (break 없음)                 화살표 switch
+-----------------------------+         +-----------------------------+
| case 1: s = "월";           |         | case 1 -> s = "월";         |
|         (문이 없다)          |         |          (여기서 끝)        |
| case 2: s = "화";           |         | case 2 -> s = "화";         |
|         (문이 없다)          |         |          (여기서 끝)        |
| case 3: s = "수"; break;    |         | case 3 -> s = "수";         |
+-----------------------------+         +-----------------------------+
  day=1 을 넣으면 "수" 가 나온다           day=1 을 넣으면 "월" 이 나온다
```

**똑같은 구조로** Java 가 이렇게 동작한다: 문이 없는 것 = `goto` 가 없는 바이트코드,\
문을 단 것 = 가지마다 붙는 `goto`, 물건 = 스택에 남는 값, 게시판/색인 = `tableswitch`/`lookupswitch`.

실무에서 이게 값을 내는 자리는 "**상태에 따라 값을 하나 고르는 코드**"다.\
`if-else` 사슬이나 `Map` 조회로 쓰던 자리가 `switch` 식 하나로 줄고, **빠뜨리면 컴파일이 멈춘다.**

> **폴스루(fall-through)** — `case` 본문이 끝나도 멈추지 않고 **다음 `case` 본문으로 이어서 실행**되는 것.\
> 예: `case 1: s = "월";` 다음에 `break` 가 없으면 `case 2:` 의 `s = "화";` 도 실행된다.

> **식(expression)과 문(statement)** — 식은 **값이 되는 것**, 문은 **일을 하는 것**.\
> 예: `switch (d) { ... }` 를 `String s = switch (d) { ... };` 처럼 대입 오른쪽에 쓰면 식이다.

> **완결성(exhaustiveness)** — `case` 들이 입력의 **모든 경우를 덮는다**는 컴파일러의 판정.\
> 예: `enum` 상수 넷을 전부 적으면 `default` 없이도 `switch` 식이 컴파일된다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 셋을 과녁으로 둔다.

1. 화살표가 **폴스루를 없앴다**는 말은 컴파일된 코드에서 **무엇이 달라진 것**인가.
2. `switch` 가 **식**이 되면서 무엇이 새로 요구되는가 — 문(statement)에는 왜 그 요구가 없는가.
3. 완결하다고 판정된 `switch` 식이 **런타임에 아무 가지에도 안 걸리면** 무슨 일이 일어나는가.

## 동작 방식

### (1) 폴스루는 바이트코드에서 **`goto` 가 없는 것**이다

**언제 쓰나** — "화살표가 폴스루를 없앴다"가 정확히 무엇을 뜻하는지 따질 때.

`Ex.java (21-a)` — 같은 분기를 콜론(break 누락)과 화살표로 각각 쓴다.

```java
// 콜론 switch — break 를 빠뜨렸다
static String colonBuggy(int day) {
    String s = "?";
    switch (day) {
        case 1: s = "월";
        case 2: s = "화";
        case 3: s = "수"; break;
        default: s = "그 밖";
    }
    return s;
}

// 화살표 switch 식 — 값을 돌려준다
static String arrowExpr(int day) {
    return switch (day) {
        case 1 -> "월";
        case 2 -> "화";
        case 3 -> "수";
        default -> "그 밖";
    };
}
```

**실행 결과** (JDK 21.0.5 — 17.0.13 · 25.0.1 에서도 같았다)

```text
day=1  colonBuggy=수    colonFixed=월    arrow=월    arrowExpr=월    grouped=평일   scored=10
day=2  colonBuggy=수    colonFixed=화    arrow=화    arrowExpr=화    grouped=평일   scored=20
day=3  colonBuggy=수    colonFixed=수    arrow=수    arrowExpr=수    grouped=평일   scored=30
day=4  colonBuggy=그 밖  colonFixed=그 밖  arrow=그 밖  arrowExpr=그 밖  grouped=평일   scored=40
```

- `colonBuggy(1)` 이 **`"수"`** 다. 1 로 들어가서 2·3 을 지나오며 `s` 가 세 번 덮였다.

이제 `javap -c -p Ex.class` 로 두 메서드를 나란히 본다. **차이가 한 가지뿐**이다.

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
      35: ldc           #11                 // String 화        <- 32 에서 그대로 흘러 들어온다
      37: astore_1
      38: ldc           #13                 // String 수        <- 35 에서 그대로 흘러 들어온다
      40: astore_1
      41: goto          47                  <- break 를 적은 가지에만 goto 가 있다
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
      30: goto          45                  <- 가지마다 goto 가 붙는다
      33: ldc           #11                 // String 화
      35: goto          45
      38: ldc           #13                 // String 수
      40: goto          45
      43: ldc           #15                 // String 그 밖
      45: areturn
```

그림 해설 (한 단계씩):

- ★ **차이는 `goto` 의 개수뿐이다.** 콜론 쪽은 `break` 를 적은 가지(오프셋 41)에만 `goto` 가 있다.
- 화살표 쪽은 **가지마다** `goto 45` 가 붙는다. 그래서 다음 가지로 흘러갈 길이 없다.
- 즉 **"화살표가 폴스루를 없앴다" = "컴파일러가 `break` 를 대신 넣어 준다"** 가 아니라,\
  **"가지의 끝이 문법적으로 정해져 있어서 넘어갈 자리가 없다"** 는 뜻이다.
- 분기 선택 명령(`tableswitch`)은 **양쪽이 똑같다.** 화살표는 분기 방식을 바꾸지 않는다.

**비용** — 없다. 가지마다 `goto` 3바이트가 늘 뿐이고, 그마저 마지막 가지에는 필요 없다.\
읽는 쪽 비용은 크게 준다 — **`break` 를 눈으로 세지 않아도 된다.**

### (2) 분기 선택은 값의 **촘촘함**으로 갈린다 — `tableswitch` 대 `lookupswitch`

**언제 쓰나** — "`switch` 가 `if-else` 사슬보다 빠른가"를 따질 때.

`Ex.java (21-b)` — 같은 모양인데 `case` 값만 다르다.

```java
static String dense(int code) {          // 1, 2, 3
    return switch (code) {
        case 1 -> "하나";
        case 2 -> "둘";
        case 3 -> "셋";
        default -> "?";
    };
}

static String sparse(int code) {         // 1, 500, 9999
    return switch (code) {
        case 1    -> "하나";
        case 500  -> "오백";
        case 9999 -> "구천구백구십구";
        default   -> "?";
    };
}
```

```text
  dense — 값이 촘촘하다                    sparse — 값이 흩어졌다
  +-----------------------------+         +-----------------------------+
  | tableswitch { // 1 to 3     |         | lookupswitch { // 3         |
  |          1: 28              |         |            1: 36            |
  |          2: 33              |         |          500: 41            |
  |          3: 38              |         |         9999: 46            |
  |    default: 43              |         |      default: 51            |
  | }                           |         | }                           |
  +-----------------------------+         +-----------------------------+
    값 - 1 을 배열 인덱스로 쓴다             키 목록을 이진 탐색한다
    O(1)                                   O(log n)
```

**실행 결과** (JDK 21.0.5 — 17 · 25 에서도 같았다)

```text
둘 / 오백 / ?
```

- `tableswitch` 는 **점프 테이블**이다. `1 to 3` 이라는 범위를 적어 두고 그 안의 오프셋을 배열로 갖는다.
- `lookupswitch` 는 **키-오프셋 쌍의 정렬 목록**이다. 값이 흩어져 있으면 테이블을 만들 수 없다.
- 둘 다 **가지 수와 무관하게(또는 로그로) 한 번에 간다** — `if-else` 사슬의 선형 비교와 다른 점이다.
- ★ 어느 쪽을 쓸지는 **javac 가 정한다.** 소스에 표시할 방법이 없다.
- `switch (String)` 은 또 다르다 — `hashCode()` 로 후보를 좁히고 `equals` 로 확인하는 **2단계**다.\
  그쪽은 [**35번 주제**](../35-string/)가 정본이다.

**비용** — `tableswitch` 는 범위만큼 테이블을 만든다. `case 1` 과 `case 1000` 둘만 있으면\
테이블이 1000칸이 되므로 javac 가 `lookupswitch` 를 고른다. **판단은 컴파일러의 몫**이다.

### (3) 식이 되면서 생긴 **완결성 요구** — 문에는 없다

**언제 쓰나** — "`switch` 에 `default` 를 꼭 써야 하나"를 판단할 때.

`Ex.java (21-c)` — `enum` 하나를 식과 문으로 각각 `switch` 한다.

```java
enum Day { MON, TUE, SAT, SUN }

// 식(expression) — default 가 없는데 통과한다. 상수 넷을 전부 덮었기 때문이다
static String kindExpr(Day d) {
    return switch (d) {
        case MON, TUE -> "평일";
        case SAT, SUN -> "주말";
    };
}

// 문(statement) — 상수를 둘만 적었는데도 통과한다. 안 걸리면 아무 일도 안 일어난다
static String kindStmt(Day d) {
    String s = "안 걸림";
    switch (d) {
        case MON -> s = "월";
        case TUE -> s = "화";
    }
    return s;
}
```

**실행 결과** (JDK 21.0.5 — 17 · 25 에서도 같았다)

```text
MON  expr=평일    stmt=월
TUE  expr=평일    stmt=화
SAT  expr=주말    stmt=안 걸림
SUN  expr=주말    stmt=안 걸림
```

```text
  switch 식                                switch 문 (옛 selector 타입)
  +-----------------------------+          +-----------------------------+
  | 값을 돌려줘야 한다            |          | 값을 안 돌려준다             |
  |   -> 모든 입력에 값이 있어야  |          |   -> 안 걸리면 그냥 지나간다  |
  |   -> 완결성 검사가 돈다       |          |   -> 완결성 검사가 없다       |
  +-----------------------------+          +-----------------------------+
    빠뜨리면 컴파일 에러                      빠뜨리면 조용히 아무 일도 안 함
```

- **식은 값이 되어야 한다.** `SAT` 를 넣었는데 돌려줄 값이 없으면 프로그램이 성립하지 않는다.\
  그래서 컴파일러가 **모든 경우를 덮었는지** 검사한다.
- **문은 값을 안 돌려준다.** 안 걸리면 그냥 `switch` 를 빠져나간다 — 검사할 이유가 없다.
- ★ 위 `kindStmt` 는 **`SAT`·`SUN` 에서 아무 일도 안 한다.** 컴파일러가 아무 말도 안 해 준다.\
  이것이 `switch` **문**을 쓸 때의 가장 흔한 무음 실패다.
- ★ 단, **패턴을 쓰는 `switch` 문은 완결성을 요구한다.** 그쪽은 [**23번 주제**](../23-switch-pattern-matching/)다.\
  경계가 「문이냐 식이냐」가 아니라 「**옛 selector 냐 패턴이냐**」에도 걸려 있다.

**비용** — 식 쪽은 **하위 상수가 늘 때마다 모든 `switch` 를 고쳐야 한다.**\
그 비용을 치르는 대신 빠뜨림이 불가능해진다. 문 쪽은 그 반대의 거래다.

### (4) `enum` 의 특별 대우 — 그리고 `MatchException` 이 **이미 여기 있다**

**언제 쓰나** — "`case MON:` 처럼 한정 없이 쓸 수 있는 이유"와 "그 코드가 무엇으로 컴파일되나"를 볼 때.

`enum` 은 `case` 에 **상수 이름을 그대로** 쓸 수 있는 특별한 타입이다(`Day.MON` 이 아니라 `MON`).\
그 규칙과 `case Day.MON` 이 버전에 따라 갈리는 이야기는 [`../13-enum-classes/`](../13-enum-classes/)가 정본이다.

여기서 볼 것은 **`kindExpr` 이 무엇으로 컴파일되는가**다. `javap -c -p Ex.class` (JDK 21.0.5).

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

- ★ **소스에 `default` 가 없는데 바이트코드에는 `default:` 가 있다.** 하는 일은 `MatchException` 을 던지는 것뿐이다.
- 패턴이 하나도 없는 **평범한 `enum` `switch` 식**인데 `MatchException` 이 나온다.\
  `MatchException` 을 "패턴 매칭 전용"으로 외우면 틀린다.
- 타입 판별은 `ordinal()` + `tableswitch` 다. `invokedynamic` 이 아니다 — [**23번 주제**](../23-switch-pattern-matching/)와 갈리는 지점이다.

★ **그런데 이 자리가 JDK 판에 따라 달랐다.** 같은 소스를 각 판의 `javac` 로 컴파일해 비교했다.

```text
  JDK 17.0.13 의 javac                          JDK 21.0.5 · 25.0.1 의 javac
  +----------------------------------+          +----------------------------------+
  | getstatic Ex$1.$SwitchMap$Ex$Day |          | invokevirtual Ex$Day.ordinal()   |
  | invokevirtual Ex$Day.ordinal()   |          | tableswitch { // 0 to 3          |
  | iaload                           |          |   ...                            |
  | tableswitch { // 1 to 4          |          |   default: 36                    |
  |   ...                            |          | }                                |
  |   default: 40                    |          | new java/lang/MatchException     |
  | }                                |          | invokespecial <init>(String,     |
  | new java/lang/                   |          |                      Throwable)  |
  |     IncompatibleClassChangeError |          | athrow                           |
  | invokespecial <init>()           |          |                                  |
  | athrow                           |          |                                  |
  +----------------------------------+          +----------------------------------+
    합성 $SwitchMap 클래스를 거친다               ordinal() 을 바로 쓴다
    IncompatibleClassChangeError                  MatchException (21+)
```

- 17 은 **합성 클래스 `Ex$1` 의 `$SwitchMap`** 을 거친다. 같은 파일 안의 `enum` 인데도 그렇다.\
  (`$SwitchMap` 이 무엇을 위한 장치인지는 [`../13-enum-classes/`](../13-enum-classes/)가 정본이다.)
- 21·25 는 **`ordinal()` 을 바로** 쓴다. 같은 소스인데 **컴파일 전략이 바뀌었다.**
- 그리고 예외 종류가 다르다 — **17 은 `IncompatibleClassChangeError`, 21·25 는 `MatchException`.**
- ★ **"세 판에서 같았다"를 여기에 쓸 수 없다.** 실행 출력은 같았지만 컴파일 결과가 달랐다.

**비용** — `$SwitchMap` 쪽은 합성 클래스 하나와 `int[]` 하나가 더 생긴다.\
어느 쪽이든 **소스에서 고를 수 없다.** 외울 것은 명령 이름이 아니라 **"완결성은 컴파일 시점의 판정"** 이라는 성질이다.

### (5) `yield` — 블록 가지에서 값을 내는 유일한 방법

**언제 쓰나** — 가지 하나가 한 줄로 안 끝날 때.

`Ex.java (21-a)` 의 `scored`.

```java
static int scored(int day) {
    return switch (day) {
        case 1, 2, 3, 4, 5 -> {
            int base = 10;
            yield base * day;      // 블록 가지는 yield 로 값을 낸다
        }
        case 6, 7 -> 0;
        default   -> -1;
    };
}
```

**실행 결과** (JDK 21.0.5 — 17 · 25 에서도 같았다)

```text
day=1 ... scored=10
day=2 ... scored=20
day=3 ... scored=30
day=4 ... scored=40
```

`Ex.java (21-d)` — **콜론 문법으로도 `switch` 식**을 쓸 수 있다.

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

**실행 결과** (JDK 21.0.5 — 17 · 25 에서도 같았다)

```text
1:작다 2:작다 3:보통 4:크다 
```

```text
  가지의 형태 세 가지
  +-------------------------------------------------------------+
  | case 1 -> "월";                식 하나. 그것이 값이다        |
  | case 1 -> { ... yield v; }     블록. yield 로 값을 낸다      |
  | case 1 -> throw new X();       던진다. 값을 안 내도 된다      |
  +-------------------------------------------------------------+
  콜론 문법에서는 -> 자리가 : 이고 값은 항상 yield 로 낸다
```

- **`yield` 는 `switch` 식 전용**이다. 밖에서 쓰면 `yield outside of switch expression` 이다.
- **`return` 은 `switch` 식 안에서 쓸 수 없다.** `switch` 는 값을 내는 자리이지 메서드를 끝내는 자리가 아니다.
- 가지는 **값을 내거나 던지거나** 둘 중 하나여야 한다. 그냥 끝나면 컴파일 에러다(「어디서 틀리나」 4번).
- ★ **`yield` 는 예약어가 아니라 제한 식별자(restricted identifier)다.** 변수 이름으로는 여전히 쓸 수 있다.\
  다만 **메서드 호출은 한정해야** 한다 — `yield(3)` 은 막히고 `Ex.yield(3)` 은 된다(「어디서 틀리나」 8번).

**비용** — 블록 가지는 지역 변수가 그 블록 안에만 산다. 가지가 길어지면 **메서드로 빼는 편**이 낫다.

### (6) 분리 컴파일 — 완결성 판정이 낡으면

**언제 쓰나** — `default` 없는 `switch` 식을 라이브러리 경계에 둘지 판단할 때.

`Ex.java (21-rt)` — `enum` 과 `switch` 를 **다른 파일**에 둔다.

```text
21rt/
  Day.java   public enum Day { MON, TUE, SAT, SUN }
  Ex.java    switch (d) { case MON, TUE -> "평일"; case SAT, SUN -> "주말"; }   // default 없음
```

1차 컴파일은 통과한다. 이때 `javap -c -p` 로 `kind` 를 보면 **다른 파일이라 `$SwitchMap` 을 거친다**\
(같은 파일이던 (4) 와 다르다 — 이 갈림은 [`../13-enum-classes/`](../13-enum-classes/)의 관찰이 `switch` 식에도 그대로 적용된 것이다).

```text
  static java.lang.String kind(Day);
    Code:
       0: getstatic     #7                  // Field Ex$1.$SwitchMap$Day:[I
       3: aload_0
       4: invokevirtual #13                 // Method Day.ordinal:()I
       7: iaload
       8: tableswitch   { // 1 to 4
                     1: 50
                     2: 50
                     3: 55
                     4: 55
               default: 40
          }
      40: new           #19                 // class java/lang/MatchException
      ...
      49: athrow
```

그 뒤 `Day` 에 상수 `HOLIDAY` 를 넣고 **`Day` 만** 다시 컴파일한다.

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

**같은 시나리오를 JDK 17 에서 돌리면 예외가 다르다.**

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

```text
  컴파일 시점                              실행 시점
  +-----------------------------+         +-----------------------------+
  | Day = {MON,TUE,SAT,SUN}     |         | Day = {MON,TUE,SAT,SUN,     |
  | 네 상수를 전부 덮었다        |  ---->  |        HOLIDAY}             |
  | -> 완결하다고 판정           |         | HOLIDAY 는 어느 가지도 아님  |
  +-----------------------------+         +-----------------------------+
                                            JDK 21+ : MatchException
                                            JDK 17  : IncompatibleClassChangeError
```

- **기존 상수는 그대로 돈다.** 깨지는 것은 새로 생긴 상수뿐이다.
- javac 는 이것을 **막아 주지 못한다.** 완결성 검사는 `Ex.java` 를 컴파일할 때만 돈다.
- ★ 실무 함의: **`enum` 에 상수를 추가하는 것은 바이너리 호환이 깨지는 변경**이다.\
  그 `enum` 을 `default` 없이 `switch` 하는 코드가 어딘가에 있다면 재컴파일이 필요하다.
- `sealed` 계층에서 같은 일이 일어나는 쪽은 [`../15-sealed-classes/`](../15-sealed-classes/)가 정본이다.

**비용** — `default` 를 넣으면 이 예외가 사라진다. 대신 **새 상수가 조용히 `default` 로 샌다.**\
어느 쪽이 나은지는 "새 상수가 늘어날 것인가"로 갈린다.

## 문법 — 형태와 규칙

### 형태 넷

```java
// 1. 콜론 문 — 폴스루가 있다
switch (n) {
    case 1: doA(); break;
    case 2: doB(); break;
    default: doC();
}

// 2. 화살표 문 — 폴스루가 없다
switch (n) {
    case 1 -> doA();
    case 2 -> doB();
    default -> doC();
}

// 3. 화살표 식 — 값이 된다
String s = switch (n) {
    case 1 -> "하나";
    case 2, 3 -> "둘셋";          // 쉼표로 묶는다
    default -> { yield "그 밖"; }  // 블록이면 yield
};

// 4. 콜론 식 — 값은 yield 로만
String t = switch (n) {
    case 1: yield "하나";
    default: yield "그 밖";
};
```

### 규칙 불릿

- **화살표와 콜론을 한 `switch` 안에서 섞을 수 없다.** 섞으면 `different case kinds used in the switch`.
- `switch` **식**의 가지는 **값을 내거나 던져야** 한다. 그냥 끝나면 컴파일 에러다.
- `switch` 식 안에서 **`return` 을 쓸 수 없다.** 값은 `yield`(또는 화살표 뒤 식 하나)로 낸다.
- `yield` 는 **`switch` 식 안에서만** 쓸 수 있다.
- `case` 레이블은 **상수 식**이어야 한다. 지역 변수는 `final` 이어도 상수 식이 아닌 한 못 쓴다.
- `case` 값과 `default` 는 **중복될 수 없다.**
- 하나의 가지에 여러 레이블을 쉼표로 묶을 수 있다 — `case 1, 2, 3 ->`.
- 옛 selector 타입(`byte`·`short`·`char`·`int`·그 래퍼·`String`·`enum`)의 **문**은 완결성을 요구하지 않는다.
- 같은 타입의 **식**은 완결성을 요구한다. `enum` 이면 상수 전부, 그 밖이면 `default` 가 필요하다.

### 선택 가이드

| 상황 | 쓸 것 |
|---|---|
| 값을 하나 고른다 | **화살표 식** |
| 가지마다 일을 시킨다(반환값 없음) | **화살표 문** |
| 의도적으로 여러 레이블을 묶는다 | `case 1, 2, 3 ->` (폴스루 말고 **쉼표**) |
| 옛 코드를 읽는다 | 콜론 — `break` 가 있는지 **눈으로 센다** |
| 새 코드에 콜론을 쓴다 | **거의 없다.** 화살표가 짧고 안전하다 |

## 어디서 틀리나

★ 이 주제의 값은 대부분 여기 있다. **아래 에러 메시지는 전부 JDK 21.0.5 의 javac 실출력이다.**

### 1. `break` 를 빠뜨렸다 — 옛 `switch` 최대의 함정

```text
day=1  colonBuggy=수
```

- `case 1:` 로 들어가 `case 2:`·`case 3:` 본문까지 실행됐다. **예외도 경고도 없다.**
- javac 는 이것을 **기본으로는 경고하지 않는다.** `-Xlint:fallthrough` 를 켜야 한다 — 돌려 확인했다.

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

- 경고가 **둘**이다. `case 1` 에서 `case 2` 로, `case 2` 에서 `case 3` 으로 새는 두 자리를 각각 짚는다.
- 고치는 법은 `break` 를 넣는 것이 아니라 **화살표로 바꾸는 것**이다 — 실수할 자리가 사라진다.

### 2. `switch` 식이 모든 경우를 안 덮었다

`Ex.java (21-e1)`

```java
static String f(int n) {
    return switch (n) {
        case 1 -> "하나";
        case 2 -> "둘";
    };
}
```

```text
Ex.java:3: error: the switch expression does not cover all possible input values
        return switch (n) {
               ^
1 error
```

- `int` 는 상수가 40억 개가 넘는다. **`default` 없이 덮을 방법이 없다.**
- 같은 코드를 `switch` **문**으로 쓰면 통과한다 — 「동작 방식」 (3).
- 이 에러는 **좋은 에러**다. `enum`·`sealed` 를 `switch` 할 때 이 에러를 받기 위해 `default` 를 안 쓴다.

### 3. 화살표와 콜론을 섞었다

`Ex.java (21-e2)`

```java
return switch (n) {
    case 1 -> "하나";
    case 2: yield "둘";
    default -> "?";
};
```

```text
Ex.java:5: error: different case kinds used in the switch
            case 2: yield "둘";
            ^
1 error
```

- **한 `switch` 안에서는 한 문법만** 쓸 수 있다.
- 옛 코드를 화살표로 옮길 때 가지를 하나씩 바꾸다 보면 이 에러를 만난다. **한꺼번에 바꿔야 한다.**

### 4. `switch` 식 안에서 `return` 했다

`Ex.java (21-e3)`

```java
return switch (n) {
    case 1 -> { return "하나"; }
    default -> "?";
};
```

```text
Ex.java:4: error: attempt to return out of a switch expression
            case 1 -> { return "하나"; }
                        ^
1 error
```

- `switch` **식**은 값이 되는 자리다. 거기서 메서드를 끝내면 "식의 값"이 정의되지 않는다.
- `yield "하나";` 로 고친다. 메서드를 끝내고 싶으면 `switch` 를 **문**으로 쓴다.

### 5. 블록 가지가 값을 안 내고 끝났다

`Ex.java (21-e4)`

```java
return switch (n) {
    case 1 -> { String s = "하나"; }
    default -> "?";
};
```

```text
Ex.java:4: error: switch rule completes without providing a value
            case 1 -> { String s = "하나"; }
                                         ^
  (switch rules in switch expressions must either provide a value or throw)
1 error
```

- ★ 괄호 안 설명이 규칙 전부다 — **값을 내거나 던지거나.**
- `throw new IllegalStateException()` 으로 끝내는 가지는 **정상**이다. 값을 안 내도 된다.

### 6. `case` 에 변수를 썼다

`Ex.java (21-e5)`

```java
int limit = 3;
switch (n) {
    case limit -> System.out.println("상수가 아니다");
    default -> System.out.println("?");
}
```

```text
Ex.java:6: error: constant expression required
            case limit -> System.out.println("상수가 아니다");
                 ^
1 error
```

- `case` 레이블은 **컴파일 시점에 값이 정해져야** 한다. `tableswitch`/`lookupswitch` 에 숫자를 박아야 하기 때문이다.
- `static final int LIMIT = 3;` 처럼 **컴파일 상수**로 만들면 통과한다 — 돌려 확인했다(`Ex.java (21-f)`).

```text
constCase(3) = 상수 식은 된다
```

- `enum` 상수는 예외적으로 허용된다 — 그것이 「특별 대우」의 한 조각이다.

### 7. 레이블이 겹쳤다

`Ex.java (21-e6)` · `Ex.java (21-e8)`

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

- 값이든 `default` 든 **두 번 나올 수 없다.** 분기표에 같은 키가 둘일 수 없기 때문이다.
- 긴 `switch` 에서 복사·붙여넣기로 만들어지는 흔한 실수다. **컴파일러가 잡아 준다** — 좋은 에러다.

### 8. `yield` 를 밖에서 쓰거나, 이름으로 쓰려 했다

`Ex.java (21-e7)`

```java
static int f(int n) {
    if (n > 0) yield n;
    return 0;
}
```

```text
Ex.java:3: error: yield outside of switch expression
        if (n > 0) yield n;
                   ^
1 error
```

`Ex.java (21-e9)` — 메서드 이름으로 `yield` 를 만들고 **한정 없이** 불렀다.

```java
static int yield(int x) { return x * 2; }
...
System.out.println("... 메서드 yield(3) = " + yield(3));
```

```text
Ex.java:24: error: invalid use of a restricted identifier 'yield'
        System.out.println("변수 yield = " + yield + " / 메서드 yield(3) = " + yield(3));
                                                                          ^
  (to invoke a method called yield, qualify the yield with a receiver or type name)
1 error
```

- ★ **17 · 21 · 25 에서 한 글자도 같은 에러**가 나왔다 — 세 판에서 돌려 확인했다.
- 괄호 안 설명이 고치는 법이다 — **`Ex.yield(3)` 처럼 한정**한다. 실제로 그렇게 고치니 통과했다.

```text
1:작다 2:작다 3:보통 4:크다 
변수 yield = 5 / 메서드 yield(3) = 6
```

- **변수 이름 `yield` 는 그대로 통과한다.** `yield` 는 예약어가 아니라 **제한 식별자**다.
- `goto` 처럼 아예 못 쓰는 예약어와 다르다([**20번 주제**](../20-control-flow-statements/) 참고).

### 9. `switch` **문**에서 가지를 빠뜨렸다 — 아무 말도 안 해 준다

```java
String s = "안 걸림";
switch (d) {
    case MON -> s = "월";
    case TUE -> s = "화";
}
```

```text
SAT  expr=주말    stmt=안 걸림
SUN  expr=주말    stmt=안 걸림
```

- ★ **컴파일 에러도 경고도 없다.** `SAT`·`SUN` 에서 아무 일도 안 일어난다.
- 이것이 2번의 반대편이다 — 값을 돌려주지 않는 자리에서는 컴파일러가 세어 주지 않는다.
- 대응: **분기해서 값을 고르는 코드는 문이 아니라 식으로 쓴다.** 그러면 이 실수가 컴파일 에러가 된다.

### 10. `enum` 에 상수를 추가하고 `switch` 를 다시 안 컴파일했다

```text
--- 새 상수 (JDK 21)
Exception in thread "main" java.lang.MatchException
	at Ex.kind(Ex.java:3)
```

```text
--- 새 상수 (JDK 17)
Exception in thread "main" java.lang.IncompatibleClassChangeError
	at Ex.kind(Ex.java:3)
```

- 같은 소스·같은 시나리오인데 **예외 클래스가 다르다.** 21 에서 `MatchException` 으로 통일된 것이다.
- 로그에서 `IncompatibleClassChangeError` 를 보면 "낡은 클래스를 섞었다"까지는 같은 뜻이다.
- 대응: **`enum` 과 그것을 `switch` 하는 코드는 같이 빌드·배포한다.**

### 11. `case null` 을 옛 `switch` 에 쓰려 했다

옛 `switch` 에 `null` 을 넣으면 **NPE** 다. `case null` 은 **21 의 패턴 `switch`** 부터다.

```text
oldEnumSwitch(null)   -> 던짐: java.lang.NullPointerException: Cannot invoke "Ex$Day.ordinal()" because "<parameter1>" is null
```

- 메시지가 **`ordinal()`** 을 가리킨다 — (4) 의 바이트코드 첫 줄이 그것이다.
- `switch (String)` 이면 대신 `hashCode()` 에서 터진다. 그쪽은 [**35번 주제**](../35-string/)가 정본이다.
- `case null` 을 쓰는 법은 [**23번 주제**](../23-switch-pattern-matching/)가 정본이다. **여기서는 "옛 `switch` 에서는 NPE"까지만.**

## 구현 세부사항 대 언어 보장

이 주제는 **같은 소스가 JDK 판에 따라 다른 바이트코드**가 되므로 경계가 특히 중요하다.

| 무엇 | 어디에 속하나 | 근거 |
|---|---|---|
| 화살표 가지에 폴스루가 없다는 것 | **언어 보장** | 문법 규칙. 섞으면 `different case kinds` |
| `switch` 식의 완결성 요구 | **언어 보장** | javac 에러 `does not cover all possible input values` |
| 옛 selector 의 `switch` **문**은 완결성을 요구하지 않는다 | **언어 보장** | 21-c 가 컴파일되고 조용히 지나간다 |
| `yield` 가 `switch` 식 전용 | **언어 보장** | javac 에러 `yield outside of switch expression` |
| `yield` 가 **제한 식별자**(변수명 가능) | **언어 보장** | 변수 `yield` 는 통과, 무한정 호출만 막힘 |
| `case` 레이블이 상수 식이어야 한다 | **언어 보장** | javac 에러 `constant expression required` |
| `MatchException` 이 **21 부터** | **API 보장** | `MatchException` javadoc `@since 21` |
| 완결 `switch` 식이 안 맞으면 **무언가 던진다** | **언어 보장** | 21 이전엔 `IncompatibleClassChangeError`, 21+ 는 `MatchException` |
| **어느 예외를 던지는지** | **버전 의존** | 17 과 21 에서 달랐다(실측) |
| `tableswitch` 냐 `lookupswitch` 냐 | **구현 세부** | javac 가 값의 촘촘함으로 고른다 |
| 같은 파일 `enum` 이 `ordinal()` 직접이냐 `$SwitchMap` 이냐 | **구현 세부** | 17 은 `$SwitchMap`, 21·25 는 `ordinal()` 직접 |
| 가지마다 붙는 `goto` 의 개수·오프셋 | **구현 세부** | javac 의 코드 생성 방식 |
| 에러 메시지의 **문구 자체** | **구현 세부** | javac 의 것이다 |

### 판이 바뀌면 무엇을 다시 봐야 하나

```text
  버전이 올라도 안 변한 것                  버전이 오르며 변한 것
  +-----------------------------+          +-----------------------------+
  | 완결성을 요구한다는 규칙      |          | 안 맞을 때 던지는 예외 클래스 |
  | yield 의 문법과 에러 메시지   |          | enum switch 의 컴파일 전략    |
  | 폴스루의 유무                |          |   ($SwitchMap 경유 여부)     |
  | 실행 결과(출력)              |          |                             |
  +-----------------------------+          +-----------------------------+
    -> 문서에 "보장" 으로 적어도 된다          -> "이 판에서 그랬다" 로만 적는다
```

- 출력이 세 판에서 같았다고 **바이트코드가 같은 것은 아니다.** 이 주제가 그 반례다.
- 그래서 `javap` 를 근거로 쓸 때는 **어느 판의 javac 인지를 반드시 적는다.**

## 언제 쓰고 언제 안 쓰나

**화살표 `switch` 식을 쓴다**

- **값을 하나 고를 때** — `if-else` 사슬보다 짧고, 빠뜨리면 컴파일이 멈춘다.
- **`enum` 을 분기할 때** — `default` 를 안 쓰면 상수가 늘 때 빌드가 멈춰 준다.
- **`sealed` 계층을 분기할 때** — 같은 이유. 그쪽은 [**23번 주제**](../23-switch-pattern-matching/)의 영역이다.

**화살표 `switch` 문을 쓴다**

- 가지마다 **일을 시키고 값을 안 돌려줄 때.** 단 "값을 고르는" 코드를 문으로 쓰지 않는다(「어디서 틀리나」 9번).

**콜론 `switch` 를 안 쓴다**

- 새 코드에는 거의 이유가 없다. **폴스루가 필요한 경우는 쉼표(`case 1, 2, 3 ->`)로 표현된다.**
- 옛 코드를 옮길 때는 **가지를 하나씩 바꾸지 말고 한꺼번에** 바꾼다(섞으면 에러다).

**`switch` 자체를 안 쓴다**

- **가지마다 로직이 길 때** — `enum` 의 상수별 본문이나 다형성이 낫다([`../13-enum-classes/`](../13-enum-classes/)).
- **가지가 데이터일 때** — `Map<K, V>` 조회가 맞다. `switch` 는 코드에 박히는 분기다.
- **조건이 값이 아니라 범위일 때** — `if-else` 가 맞다. `case` 는 상수 하나씩만 받는다.

**중간 지대**

- `default` 를 넣을지 말지는 **"선택지가 늘어날 것인가"** 로 판단한다.\
  늘어날 것이면 `default` 로 방어하고, 늘어나면 안 되는 것이면 `default` 를 빼서 **빌드가 멈추게** 한다.

## 핵심 문장

1. 화살표가 폴스루를 없앤 것은 **가지마다 `goto` 가 붙기 때문**이다 — 콜론 쪽은 `break` 를 적은 가지에만 있다.
2. 화살표는 **분기 방식을 바꾸지 않는다.** `tableswitch`/`lookupswitch` 는 양쪽이 같다.
3. `tableswitch` 와 `lookupswitch` 는 **값이 촘촘한가 흩어졌는가**로 javac 가 고른다. 소스에서 못 정한다.
4. **완결성은 식(expression)의 요구**다 — 값을 돌려줘야 하니 모든 입력에 값이 있어야 한다.
5. ★ 옛 selector 의 `switch` **문**은 완결성을 요구하지 않는다 — **빠뜨려도 아무 말을 안 해 준다.**
6. `yield` 는 `switch` 식 전용이고, `return` 은 `switch` 식 안에서 못 쓴다. 가지는 **값을 내거나 던진다.**
7. `yield` 는 예약어가 아니라 **제한 식별자**다 — 변수명은 되고, 무한정 메서드 호출만 막힌다.
8. ★ 완결한 `enum` `switch` 식은 **패턴이 없어도** `MatchException` 을 던지는 `default:` 를 갖는다(21+).
9. 그 예외는 **17 에서는 `IncompatibleClassChangeError`** 였다 — 같은 소스, 다른 판, 다른 바이트코드.
10. 완결성은 **`switch` 를 컴파일한 시점의 판정**이다. `enum` 에 상수가 늘면 런타임에 깨진다.

## 관련 자료

- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 21번)
- [`../../../../../../history/java/java-14.md`](../../../../../../history/java/java-14.md) — **언제·왜 들어왔나**(JEP 361 확정, 두 번의 프리뷰).\
  여기는 **어떻게 쓰고 무엇을 못 하나**만 다룬다
- [`../../../../../../history/java/java-21.md`](../../../../../../history/java/java-21.md) — `MatchException` 과 패턴 `switch` 가 정식이 된 판. **연혁은 거기**
- [**20번 주제**](../20-control-flow-statements/)(제어문) — **이 주제의 앞 칸.**\
  `break` 가 루프에서 무엇을 하는지는 거기가 정본, **`switch` 안에서 무엇을 하는지는 여기**
- [**22번 주제**](../22-instanceof-type-patterns/)(`instanceof` 타입 패턴) — 조건이 타입 검사가 되는 것.\
  **여기는 값으로 분기하는 것까지**, 거기는 **타입으로 분기하며 변수를 꺼내는 것**부터
- [**23번 주제**](../23-switch-pattern-matching/)(`switch` 패턴 매칭, 21) — **`case null`·`when` 가드·패턴 `case` 의 정본.**\
  여기는 **패턴이 하나도 없는 `switch`** 만 다룬다. 완결성의 개념은 여기, **패턴에서의 완결성 규칙은 거기**
- [**24번 주제**](../24-record-patterns/)(`record` 패턴, 21) — 가지 안에서 값을 해체하는 것. **여기는 그 앞 단계까지**
- [`../13-enum-classes/`](../13-enum-classes/) — **`enum` 의 `switch` 특별 대우가 정본이다.**\
  `case MON` 을 한정 없이 쓸 수 있는 근거, `case Day.MON` 의 버전 갈림, `$SwitchMap` 합성 클래스의 존재 이유가 전부 거기 있다.\
  여기서는 **그것이 `switch` 식에서도 그대로라는 것**과 **17/21 의 전략 차이**만 덧붙였다
- [`../15-sealed-classes/`](../15-sealed-classes/) — `sealed` 계층의 완결성과 `MatchException`.\
  **`sealed` 쪽 규칙은 거기**, 여기는 **`enum` 쪽 같은 현상**만
- [`../35-string/`](../35-string/) — **`switch (String)` 이 `hashCode` + `lookupswitch` 2단계로 컴파일되는 것이 정본.**\
  `null` 을 넣으면 `hashCode()` 에서 NPE 가 나는 것도 거기다. 여기서는 **링크만** 한다
- [`../25-exceptions/`](../25-exceptions/) — 가지에서 `throw` 로 끝내는 형태. **예외 규칙은 거기**
- [`../../../../../engineering/design-patterns-gof/`](../../../../../engineering/design-patterns-gof/) — 전략·상태 패턴.\
  **`switch` 를 다형성으로 바꾸는 판단**은 거기, 여기는 `switch` 자체의 문법만
- [`../../언어-특성/README.md`](../../언어-특성/README.md) — JIT·GC·메모리 모델. **이 주제와 겹치지 않는다**

## 용어 풀이

- **`switch` 문(statement)** — 값을 돌려주지 않고 가지마다 일을 시키는 형태. Java 1.0.
- **`switch` 식(expression)** — 값이 되는 `switch`. 대입·`return`·인자 자리에 쓸 수 있다. **Java 14.**
- **화살표 규칙(arrow rule)** — `case L -> ...` 형태. 폴스루가 없다. Java 14.
- **콜론 규칙(colon rule)** — `case L: ...` 형태. 폴스루가 있다. Java 1.0.
- **폴스루(fall-through)** — `break` 가 없어 다음 `case` 본문까지 이어서 실행되는 것.
- **`yield`** — `switch` 식의 블록 가지에서 값을 내는 문. **제한 식별자**이지 예약어가 아니다.
- **제한 식별자(restricted identifier)** — 특정 문맥에서만 키워드처럼 쓰이는 이름. `yield`·`var`·`record`·`sealed` 가 그렇다.
- **완결성(exhaustiveness)** — `case` 들이 입력의 모든 경우를 덮는다는 컴파일러의 판정.
- **selector** — `switch (x)` 의 `x`. 그 타입이 규칙을 상당 부분 결정한다.
- **`tableswitch`** — 값의 범위를 점프 테이블로 만드는 JVM 명령. 값이 촘촘할 때 javac 가 고른다.
- **`lookupswitch`** — 키-오프셋 쌍을 정렬 목록으로 두는 JVM 명령. 값이 흩어졌을 때.
- **`$SwitchMap`** — `enum` `switch` 를 위해 javac 가 만드는 합성 배열. 정본은 [`../13-enum-classes/`](../13-enum-classes/).
- **`MatchException`** — 완결하다고 판정된 매칭이 런타임에 안 맞을 때 던지는 예외. **Java 21.**
- **`IncompatibleClassChangeError`** — 컴파일 때와 실행 때 클래스가 어긋났을 때의 에러. 21 이전 `enum` `switch` 식이 이것을 썼다.
- **분리 컴파일(separate compilation)** — 프로그램의 일부만 따로 컴파일해 합치는 것. 완결성 판정이 낡는 원인.

## 더 들어가면

- **`-Xlint:fallthrough` 로 폴스루를 경고로 받을 수 있다.**\
  옛 코드베이스를 화살표로 옮기기 전에 켜 두면 어디가 의도된 폴스루이고 어디가 실수인지 목록이 나온다.\
  다만 **기본은 꺼져 있다** — 그래서 「어디서 틀리나」 1번이 조용히 지나간다.
- **`switch` 식은 `if-else` 보다 "표"에 가깝다.**\
  가지가 전부 한 줄이면 읽는 눈이 왼쪽 레이블만 훑으면 된다.\
  가지에 블록이 셋 이상 생기면 그 신호는 **"`switch` 가 아니라 다형성일 때"** 다 —\
  `enum` 상수별 본문([`../13-enum-classes/`](../13-enum-classes/))이나 `sealed` + 타입별 메서드로 옮긴다.
- **`case 1, 2, 3 ->` 는 폴스루가 아니다.**\
  옛 코드의 `case 1: case 2: case 3: doX(); break;` 를 옮길 때 이 형태가 정답이다.\
  겉보기가 비슷해서 "폴스루를 남겨 둔 것"으로 읽히지만, **실행 경로가 하나**라는 점이 다르다.
- **`switch` 식이 값을 돌려준다는 것은 `null` 도 돌려줄 수 있다는 뜻이다** — 돌려 확인했다(`Ex.java (21-f)`).

  ```java
  static String nullable(int n) {
      return switch (n) {
          case 1  -> null;
          default -> "그 밖";
      };
  }
  ```

  ```text
  nullable(1)  = null
  nullable(2)  = 그 밖
  ```

  완결성은 "값이 있느냐"만 묻지 **"그 값이 쓸모 있느냐"를 묻지 않는다.** 17 · 21 · 25 에서 같았다.
- **17 과 21 의 컴파일 전략 차이는 `enum` 상수 개수와 무관했다.**\
  네 상수짜리 같은 소스를 두 판의 javac 로 찍어 비교한 결과다 — 21 쪽이 `$SwitchMap` 을 **안 만든다.**\
  합성 클래스 하나가 줄어든 셈이지만, **그것을 근거로 성능을 말하지는 않는다**(측정하지 않았다).
