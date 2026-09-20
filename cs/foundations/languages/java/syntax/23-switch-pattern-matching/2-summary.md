# java/syntax/23 — `switch` 패턴 매칭 (21): 완결성 · `null` · `when` 가드 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — JDK 21.0.5 의 `lib/src.zip` 을 **직접 풀어 읽은** javadoc 하나다.\
> `java.base/java/lang/MatchException.java` — `@since 21`, `@jls 14.11.3` `@jls 14.30.2` `@jls 15.28.2`.\
> 그 javadoc 이 나열한 **세 가지 사례**를 본문에서 인용하고 그중 둘을 실행으로 재현했다.\
> JLS 절 번호는 **그 javadoc 의 `@jls` 태그에 적힌 것만** 옮겼다. JLS 본문은 열지 않았다.
> **실행 검증** — 이 문서의 모든 출력·에러 메시지는 Temurin JDK 에서 실제로 돌려 얻은 것이다.\
> 프로그램 7개 + 컴파일 에러용 12개 + 분리 컴파일 시나리오 1벌.\
> `javac` 41회 · `java` 16회 · `javap` 5회. 도는 프로그램은 **21.0.5 · 25.0.1** 에서 돌렸다.\
> ★ **17.0.13 에서는 아예 컴파일되지 않는다** — 그 에러도 실어 두었다.\
> 버전 갈림(`--release 17` / `20` / `21`)은 JDK 21 의 `javac --release` 로 찍었다.\
> 역어셈블은 `javap -c -p` · `javap -v -p` 출력을 **그대로** 옮겼다.
> **버전** — `switch` 패턴 매칭은 **Java 21** 정식(17~20 프리뷰).\
> 선행인 `sealed` 는 **17**, `instanceof` 타입 패턴은 **16**, `switch` 식은 **14** 다 — **넷이 다 다른 버전이다.**
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 javac 의 실제 에러 메시지와 바이트코드로 접지했다.

## 한눈에 — 쉽게 말하면

**옛 `switch` 는 「번호표 뽑기」이고, 패턴 `switch` 는 「검문소」다.**

옛 `switch` 는 값에서 **번호를 뽑아** 그 번호의 칸으로 점프한다 — `enum` 이면 `ordinal()`, `String` 이면 `hashCode()`.\
번호를 뽑으려면 값이 있어야 하므로 **`null` 이 오면 뽑기 전에 터진다.**

패턴 `switch` 는 값을 **검문소에 세워 놓고 "몇 번 조건에 맞나"를 물어본다.**\
그 물음이 `invokedynamic typeSwitch` 다. 검문소는 `null` 도 받아 줄 수 있다 — **`-1` 번**이라고 답한다.

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 번호표 뽑는 기계 | `ordinal()` · `hashCode()` |
| 번호표대로 칸으로 점프 | `tableswitch` · `lookupswitch` |
| **검문소에 세워 놓고 묻는다** | **`invokedynamic typeSwitch`** |
| 검문소가 돌려주는 줄 번호 | 몇 번째 `case` 에 맞나 (0부터) |
| 검문소가 `null` 에 주는 번호 | **`-1`** (`case null` 이 있을 때) |
| `case null` 이 없으면 입구에서 돌려보냄 | `Objects.requireNonNull` -> NPE |
| 명단이 확정돼 전원 점호가 된다 | `sealed` + 완결성 -> `default` 불필요 |
| 넓은 조건이 앞에 서서 뒤를 다 막음 | **지배(dominance)** -> 컴파일 에러 |
| 조건을 하나 더 붙인 검문 | `when` 가드 |
| 점호표를 인쇄한 뒤 명단이 늘었다 | 분리 컴파일 -> `MatchException` |

```text
옛 switch (enum)                         패턴 switch
+-------------------------------+       +-------------------------------+
| ordinal()      <- 번호를 뽑는다 |       | invokedynamic typeSwitch      |
| tableswitch    <- 번호로 점프   |       |   <- "몇 번 case 인가" 를 묻는다|
|                               |       | tableswitch   <- 답으로 점프   |
| null 이면 ordinal() 에서 NPE   |       | null 이면 -1 (case null 있을 때)|
+-------------------------------+       +-------------------------------+
  값에서 번호를 계산한다                    타입을 런타임에 물어본다
```

**똑같은 구조로** Java 가 이렇게 동작한다: 검문소 = `java.lang.runtime.SwitchBootstraps.typeSwitch`,\
검문 항목 목록 = 그 부트스트랩의 `Method arguments`, 전원 점호 = 완결성 검사,\
인쇄된 점호표 = 이미 컴파일된 `Ex.class` 의 부트스트랩 인자.

실무에서 이게 값을 내는 자리는 **`sealed` 계층 분기**다.\
`if (x instanceof A a) ... else if (x instanceof B b) ...` 사슬은 **빠뜨려도 조용하고**,\
같은 분기를 `sealed` + 패턴 `switch` 로 쓰면 **빠뜨리면 빌드가 멈춘다.**

> **타입 패턴(type pattern)** — `String s` 처럼 타입과 이름으로 된 패턴. 정본은 [**22번 주제**](../22-instanceof-type-patterns/).

> **완결성(exhaustiveness)** — `case` 들이 selector 타입의 **모든 값을 덮는다**는 컴파일러의 판정.\
> 예: `sealed interface Shape permits Circle, Square` 면 그 둘을 적는 것으로 완결이다.

> **지배(dominance)** — 앞의 `case` 가 뒤의 `case` 가 맞을 수 있는 값을 **전부 먼저 가져가는** 관계.\
> 예: `case Object o` 를 먼저 쓰면 그 뒤의 어떤 `case` 도 도달할 수 없다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 넷을 과녁으로 둔다.

1. 패턴 `switch` 는 **무엇으로 컴파일되는가** — 옛 `switch` 와 어디서 갈라지는가.
2. **`null` 의 취급이 왜 바뀌었는가** — `default` 는 `null` 을 받는가.
3. `case` 의 **순서**가 왜 컴파일 에러를 만드는가(지배) — 가드가 있으면 어떻게 달라지는가.
4. 완결하다고 판정된 `switch` 가 런타임에 안 맞으면 무슨 일이 일어나는가.

## 동작 방식

### (1) ★ 옛 `switch` 와 패턴 `switch` 의 바이트코드 — 이 주제의 뼈대

**언제 쓰나** — "패턴 `switch` 가 `if` 사슬로 펼쳐지는 건가"를 따질 때.

`Ex.java (23-a)` — `sealed` 계층을 `default` 없이 `switch` 한다.

```java
sealed interface Shape permits Circle, Square, Rect { }
record Circle(double r)           implements Shape { }
record Square(double side)        implements Shape { }
record Rect  (double w, double h) implements Shape { }

static String name(Shape s) {
    return switch (s) {
        case Circle c -> "원";
        case Square q -> "정사각형";
        case Rect   r -> "직사각형";
    };
}
```

`javap -c -p Ex.class` (JDK 21.0.5)

```text
  static java.lang.String name(Ex$Shape);
    Code:
       0: aload_0
       1: dup
       2: invokestatic  #7                  // Method java/util/Objects.requireNonNull:(Ljava/lang/Object;)Ljava/lang/Object;
       5: pop
       6: astore_1
       7: iconst_0
       8: istore_2
       9: aload_1
      10: iload_2
      11: invokedynamic #13,  0             // InvokeDynamic #0:typeSwitch:(Ljava/lang/Object;I)I
      16: tableswitch   { // 0 to 2
                     0: 54
                     1: 64
                     2: 75
               default: 44
          }
      44: new           #17                 // class java/lang/MatchException
      47: dup
      48: aconst_null
      49: aconst_null
      50: invokespecial #19                 // Method java/lang/MatchException."<init>":(Ljava/lang/String;Ljava/lang/Throwable;)V
      53: athrow
      54: aload_1
      55: checkcast     #22                 // class Ex$Circle
      58: astore_3
      59: ldc           #24                 // String 원
      61: goto          83
      64: aload_1
      65: checkcast     #26                 // class Ex$Square
      68: astore        4
      70: ldc           #28                 // String 정사각형
      72: goto          83
      75: aload_1
      76: checkcast     #30                 // class Ex$Rect
      79: astore        5
      81: ldc           #32                 // String 직사각형
      83: areturn
```

**대비할 것은 [**21번 주제**](../21-switch-statement-and-expression/)의 `enum` `switch` 식이다.** 같은 판(21.0.5)의 javac 로 찍은 것이다.

```text
  static java.lang.String kindExpr(Ex$Day);
    Code:
       0: aload_0
       1: invokevirtual #7                  // Method Ex$Day.ordinal:()I     <- 값에서 번호를 뽑는다
       4: tableswitch   { // 0 to 3
                     0: 46
                     1: 46
                     2: 51
                     3: 51
               default: 36
          }
      36: new           #13                 // class java/lang/MatchException
      ...
```

```text
  옛 switch (enum · String · int)          패턴 switch
  +-------------------------------+       +-------------------------------+
  | ordinal() / hashCode() / 그냥  |       | Objects.requireNonNull  <- null|
  |   값 자체                      |       |   을 먼저 막는다               |
  | tableswitch / lookupswitch     |       | invokedynamic typeSwitch       |
  |                               |       |   -> 몇 번 case 인가 (int)     |
  |                               |       | tableswitch / lookupswitch     |
  |                               |       | 가지마다 checkcast             |
  +-------------------------------+       +-------------------------------+
    번호 계산이 컴파일 시점에 정해진다        번호 계산이 런타임 호출이다
```

그림 해설 (한 단계씩):

- ★ **`if` 사슬이 아니다.** 타입 판별이 `invokedynamic typeSwitch` **한 번**으로 끝나고,\
  그것이 돌려준 `int` 로 평범한 `tableswitch` 를 탄다.
- 오프셋 2 의 **`Objects.requireNonNull`** 이 `null` 처리의 자리다 — (3)에서 다시 본다.
- 오프셋 44 의 **`MatchException`** 이 완결성의 뒷문이다 — (6)에서 다시 본다.
- 가지마다 **`checkcast`** 가 하나씩 붙는다(54·65·76). 패턴 변수를 만드는 자리다.

**검문 항목 목록은 클래스 파일에 박힌다.** `javap -v -p` 의 `BootstrapMethods` 에서 보인다.

```text
BootstrapMethods:
  0: #154 REF_invokeStatic java/lang/runtime/SwitchBootstraps.typeSwitch:(Ljava/lang/invoke/MethodHandles$Lookup;Ljava/lang/String;Ljava/lang/invoke/MethodType;[Ljava/lang/Object;)Ljava/lang/invoke/CallSite;
    Method arguments:
      #22 Ex$Circle
      #26 Ex$Square
      #30 Ex$Rect
  1: #154 REF_invokeStatic java/lang/runtime/SwitchBootstraps.typeSwitch:(Ljava/lang/invoke/MethodHandles$Lookup;Ljava/lang/String;Ljava/lang/invoke/MethodType;[Ljava/lang/Object;)Ljava/lang/invoke/CallSite;
    Method arguments:
      #37 java/lang/Integer
      #43 java/lang/String
      #52 "[I"
      #55 Ex$Shape
```

- 부트스트랩 **0번**이 `name()` 의 것이다 — `case` 에 적은 타입 셋이 **그 순서 그대로** 들어 있다.
- 부트스트랩 **1번**은 같은 파일의 `describe(Object)` 것이다 — `Integer`·`String`·`int[]`·`Shape`.\
  **배열 타입(`"[I"`)도 패턴으로 쓸 수 있다**는 것이 여기 드러난다.
- ★ **이 목록이 컴파일 시점에 박힌다**는 사실이 (6) 의 `MatchException` 으로 이어진다.

**실행 결과** (`Ex.java (23-a)`, JDK 21.0.5 — 25.0.1 에서도 같았다)

```text
Circle[r=1.0]        name=원      ifElse=원
Square[side=2.0]     name=정사각형   ifElse=정사각형
Rect[w=2.0, h=3.0]   name=직사각형   ifElse=빠뜨린 것이 여기로 온다
describe -> 정수 42
describe -> 문자열 길이 4
describe -> int 배열 길이 3
describe -> 도형 원
describe -> 그 밖 Double
```

- 셋째 줄이 이 주제의 존재 이유다 — 같은 분기를 `if` 사슬로 쓰면 **빠뜨려도 조용하다.**

**비용** — 첫 호출에서 부트스트랩이 한 번 돌아 호출 지점을 만든다. 그 뒤로는 고정된다.\
`if` 사슬 대비 이득은 **가지 수가 늘어도 판별이 한 번**이라는 것이고, 값은 대부분 **컴파일 검사** 쪽에 있다.

### (2) 완결성 — `sealed` 와 만나면 `default` 가 필요 없다

**언제 쓰나** — `default` 를 쓸지 말지 판단할 때.

(1) 의 `name()` 에는 `default` 가 없다. **`Shape` 가 `sealed` 이고 셋을 전부 적었기 때문**이다.\
`sealed` 쪽 규칙(허용 목록·`non-sealed` 에서 완결성이 끊기는 것)은 [`../15-sealed-classes/`](../15-sealed-classes/)가 정본이다.

selector 타입별로 이렇게 갈린다.

| selector | `default` 없이 완결할 수 있나 | 방법 |
|---|---|---|
| `sealed` 인터페이스/클래스 | **된다** | 허용 하위 타입을 전부 `case` 로 |
| `enum` | **된다** | 상수를 전부 `case` 로 (패턴 없이도) |
| `Object` · 그 밖의 열린 타입 | 안 된다 | `default` 또는 **무조건 패턴** 하나 |
| `record` 하나 | **된다** | 그 타입의 무조건 패턴 하나 |

`Ex.java (23-a)` 의 `describe(Object)` 가 `default` 를 쓴 경우다.

```java
static String describe(Object o) {
    return switch (o) {
        case Integer i -> "정수 " + i;
        case String  s -> "문자열 길이 " + s.length();
        case int[]   a -> "int 배열 길이 " + a.length;
        case Shape   s -> "도형 " + name(s);
        default        -> "그 밖 " + o.getClass().getSimpleName();
    };
}
```

```text
  default 를 쓴 코드                       완결성에 기댄 코드
  +---------------------------+           +---------------------------+
  | case Circle -> ...        |           | case Circle -> ...        |
  | case Square -> ...        |           | case Square -> ...        |
  | default     -> "?"        |           | case Rect   -> ...        |
  +---------------------------+           +---------------------------+
    Rect 가 추가되면                         Rect 가 추가되면
      -> 조용히 "?" 가 나온다                  -> 컴파일 에러로 멈춘다
```

- ★ **`default` 와 무조건 패턴(`case Object o`)은 같이 쓸 수 없다.** 둘 다 "나머지 전부"이기 때문이다.
- ★ **패턴 `switch` 는 문(statement)에도 완결성을 요구한다.** 옛 selector 의 `switch` 문과 다른 점이다\
  ([**21번 주제**](../21-switch-statement-and-expression/)와 갈리는 지점 — 「어디서 틀리나」 2번).

**비용** — `default` 를 안 쓰면 **하위 타입이 늘 때마다 모든 `switch` 를 고쳐야 한다.**\
그 대신 빠뜨림이 불가능해진다. 하위 타입이 자주 느는 설계면 이 거래가 손해다.

### (3) ★ `null` — 취급이 바뀐 자리

**언제 쓰나** — `null` 이 들어올 수 있는 값을 `switch` 할 때. 여기서 가장 많이 틀린다.

`Ex.java (23-b)` — 네 가지를 한 번에 돌렸다.

```java
// 옛 switch — null 을 넣으면 NPE
static String oldEnumSwitch(Day d) {
    switch (d) { case MON: return "월"; case SAT: return "토"; default: return "?"; }
}

// 패턴 switch — case null 을 쓸 수 있다
static String withCaseNull(Object o) {
    return switch (o) {
        case null      -> "널이다";
        case String s  -> "문자열 " + s;
        case Integer i -> "정수 " + i;
        default        -> "그 밖";
    };
}

// case null, default 로 묶을 수 있다
static String nullWithDefault(Object o) {
    return switch (o) {
        case String s       -> "문자열 " + s;
        case null, default  -> "널이거나 그 밖";
    };
}

// case null 이 없는 패턴 switch 에 null 을 넣으면
static String noCaseNull(Object o) {
    return switch (o) {
        case String s  -> "문자열 " + s;
        case Integer i -> "정수 " + i;
        default        -> "그 밖";
    };
}
```

**실행 결과** (JDK 21.0.5 — 25.0.1 에서도 같았다)

```text
oldEnumSwitch(null)   -> 던짐: java.lang.NullPointerException: Cannot invoke "Ex$Day.ordinal()" because "<parameter1>" is null
withCaseNull(null)    -> 널이다
withCaseNull("a")     -> 문자열 a
nullWithDefault(null) -> 널이거나 그 밖
noCaseNull(null)      -> 던짐: java.lang.NullPointerException
sealedNoNull(null)    -> 던짐: java.lang.NullPointerException
sealedNoNull(Circle)  -> 원
```

★ **다섯째 줄을 두 번 읽는다.** `noCaseNull` 에는 **`default` 가 있는데도 NPE** 다.

```text
  옛 switch                                패턴 switch
  +-----------------------------+          +-----------------------------+
  | null -> ordinal()/hashCode()|          | case null 이 있나?          |
  |         에서 NPE             |          |   있다 -> 그 가지로 간다     |
  | default 로 안 간다           |          |   없다 -> requireNonNull    |
  |                             |          |           에서 NPE          |
  +-----------------------------+          +-----------------------------+
    null 을 다루려면 switch 밖에서           default 는 null 을 받지 않는다
    미리 검사해야 한다                        case null 을 명시해야 받는다
```

**왜 그런지가 바이트코드에 그대로 있다.** `case null` 이 **없을 때**(`Ex.java (23-b2)`):

```text
  static java.lang.String noCaseNull(java.lang.Object);
    Code:
       0: aload_0
       1: dup
       2: invokestatic  #7                  // Method java/util/Objects.requireNonNull:(Ljava/lang/Object;)Ljava/lang/Object;
       5: pop
       6: astore_1
       7: iconst_0
       8: istore_2
       9: aload_1
      10: iload_2
      11: invokedynamic #13,  0             // InvokeDynamic #0:typeSwitch:(Ljava/lang/Object;I)I
      16: lookupswitch  { // 2
                     0: 44
                     1: 58
               default: 74
          }
```

`case null` 이 **있을 때**(`Ex.java (23-b)` 의 `withCaseNull`):

```text
  static java.lang.String withCaseNull(java.lang.Object);
    Code:
       0: aload_0
       1: astore_1                          <- requireNonNull 이 없다
       2: iconst_0
       3: istore_2
       4: aload_1
       5: iload_2
       6: invokedynamic #19,  0             // InvokeDynamic #0:typeSwitch:(Ljava/lang/Object;I)I
      11: tableswitch   { // -1 to 1        <- 범위가 -1 부터 시작한다
                    -1: 36
                     0: 41
                     1: 55
               default: 71
          }
      36: ldc           #23                 // String 널이다
      38: goto          73
```

- ★ **`case null` 을 쓰면 `requireNonNull` 이 사라지고 `tableswitch` 의 범위가 `-1` 부터 시작한다.**\
  `typeSwitch` 는 **`null` 에 `-1` 을 돌려준다.** 그 `-1` 이 `case null` 가지로 간다.
- `case null` 이 없으면 애초에 **검문소에 보내지도 않는다** — 입구의 `requireNonNull` 에서 튕긴다.
- 그래서 NPE **메시지가 비어 있다.** 스택 트레이스가 그것을 보여 준다.

```text
문자열 a
Exception in thread "main" java.lang.NullPointerException
	at java.base/java.util.Objects.requireNonNull(Objects.java:233)
	at Ex.noCaseNull(Ex.java:3)
	at Ex.main(Ex.java:11)
```

- 스택 맨 위가 **`Objects.requireNonNull`** 이다 — 위 바이트코드의 오프셋 2 와 정확히 같은 자리다.
- 옛 `switch` 의 NPE 는 메시지가 있었다(`Cannot invoke "Ex$Day.ordinal()" ...`). **여기는 없다.**\
  로그만 보고 원인을 찾기 더 어렵다는 뜻이다.

**규칙 정리**

| 쓴 것 | `null` 이 들어오면 |
|---|---|
| 옛 `switch`(`enum`·`String`·`int` 등) | **NPE** (번호를 뽑는 메서드에서) |
| 패턴 `switch` + `case null` | 그 가지로 간다 |
| 패턴 `switch` + `case null, default` | 그 가지로 간다 |
| 패턴 `switch` + `default` 만 | **NPE** (`requireNonNull` 에서) |
| 패턴 `switch` + 완결(`sealed`) · `case null` 없음 | **NPE** |

**비용** — `case null` 을 쓰면 `requireNonNull` 호출 하나가 빠지고 가지가 하나 는다. 실무에서 셀 크기가 아니다.\
진짜 비용은 **"`default` 가 `null` 을 받는다"는 오해**다. 그 오해가 운영에서 NPE 로 돌아온다.

### (4) ★ 지배(dominance) — `case` 의 순서가 컴파일 에러를 만든다

**언제 쓰나** — `case` 를 넓은 것부터 쓸지 좁은 것부터 쓸지 정할 때.

**규칙: 넓은 패턴이 좁은 패턴보다 앞에 오면 컴파일 에러다.**

```text
  잘못된 순서                              올바른 순서
  +-----------------------------+         +-----------------------------+
  | case Object x -> ...        |         | case String s -> ...        |
  | case String s -> ...  X     |         | case Object x -> ...        |
  +-----------------------------+         +-----------------------------+
    String 은 도달할 수 없다                좁은 것부터 넓은 것으로
    -> dominated by a preceding case label
```

`Ex.java (23-e1)`

```java
return switch (o) {
    case Object x  -> "아무거나";
    case String s  -> "문자열";      // 앞의 Object 가 이미 다 먹었다
    default        -> "그 밖";
};
```

```text
Ex.java:6: error: switch has both an unconditional pattern and a default label
            default        -> "그 밖";
            ^
Ex.java:5: error: this case label is dominated by a preceding case label
            case String s  -> "문자열";      // 앞의 Object 가 이미 다 먹었다
                 ^
2 errors
```

- 에러가 **둘**이다. 하나는 지배, 하나는 **"무조건 패턴과 `default` 를 같이 썼다"**.
- `Object x` 가 `Object` selector 에 대해 **무조건 패턴**이라서 `default` 와 역할이 겹친다.

`Ex.java (23-e8)` — `sealed` 계층에서도 같다.

```java
return switch (sh) {
    case Shape  x -> "도형";
    case Circle c -> "원";
};
```

```text
Ex.java:8: error: this case label is dominated by a preceding case label
            case Circle c -> "원";
                 ^
1 error
```

**`default` 뒤에 `case` 를 두어도 지배다** (`Ex.java (23-e3)`).

```text
Ex.java:6: error: this case label is dominated by a preceding case label
            case Integer i -> "정수";        // default 뒤에 case 를 두면?
                 ^
1 error
```

- ★ **`default` 는 위치와 무관하게 "나머지 전부"가 아니다** — **적은 자리에서** 나머지를 가져간다.\
  그래서 뒤에 오는 `case` 는 도달할 수 없다.
- 옛 `switch` 에서는 `default` 를 가운데 두어도 됐다(폴스루로 흘러 들어갈 수 있으므로).\
  패턴 `switch` 는 폴스루가 없으므로 이 자유가 사라졌다.

**★ 가드가 붙으면 지배가 성립하지 않는다.** `Ex.java (23-e4)`

```java
return switch (o) {
    case String s when s.length() > 3 -> "긴 문자열";
    case String s when s.length() > 3 -> "또 긴 문자열";   // 똑같은 가드
    case String s -> "짧은 문자열";
    default -> "그 밖";
};
```

```text
(컴파일 성공)
짧은 문자열
```

- ★ **완전히 같은 가드를 두 번 써도 컴파일된다.** javac 는 **가드의 내용을 보지 않는다.**
- 둘째 가지는 **영원히 도달할 수 없는데** 경고도 없다. 지배 검사는 **가드가 없을 때만** 돈다.
- 반대로 **무가드가 먼저 오면 가드 붙은 것도 지배된다** (`Ex.java (23-e7)`).

```text
Ex.java:5: error: this case label is dominated by a preceding case label
            case String s when s.length() > 3 -> "긴 문자열";   // 가드가 있어도 앞이 먹었다
                 ^
1 error
```

**비용** — 없다. 이 규칙은 **도달 불가능한 코드를 컴파일 시점에 없애 준다.**\
다만 가드가 낀 경우는 컴파일러가 봐 주지 않으니 **순서를 직접 따져야 한다.**

### (5) `when` 가드 — 타입을 조건으로 더 쪼갠다

**언제 쓰나** — 같은 타입인데 값에 따라 다르게 처리할 때.

`Ex.java (23-d)`

```java
static String size(Shape s) {
    return switch (s) {
        case Circle c when c.r() > 10     -> "큰 원";
        case Circle c                     -> "작은 원";
        case Square q when q.side() > 10  -> "큰 정사각형";
        case Square q                     -> "작은 정사각형";
        case Rect r when r.w() == r.h()   -> "정사각형인 직사각형";
        case Rect r                       -> "직사각형";
    };
}
```

**실행 결과** (JDK 21.0.5 — 25.0.1 에서도 같았다)

```text
Circle[r=20.0]         -> 큰 원
Circle[r=1.0]          -> 작은 원
Square[side=20.0]      -> 큰 정사각형
Square[side=1.0]       -> 작은 정사각형
Rect[w=3.0, h=3.0]     -> 정사각형인 직사각형
Rect[w=2.0, h=3.0]     -> 직사각형
```

- ★ **`default` 가 없는데 컴파일된다.** 가드 붙은 가지 뒤에 **무가드 가지**가 있어서 완결하다.
- 가드만 있는 `case` 는 **완결성에 안 쳐 준다** — 「어디서 틀리나」 6번.

**가드는 `case` 순서대로 평가된다.** 부수효과로 확인했다.

```java
static String order(Object o) {
    return switch (o) {
        case String s when check("A", s.length() > 100) -> "A";
        case String s when check("B", s.length() > 10)  -> "B";
        case String s when check("C", s.length() > 1)   -> "C";
        case String s                                   -> "D";
        default                                         -> "그 밖";
    };
}
```

```text
order("abc") = C  평가된 가드 = ABC
order("a")   = D  평가된 가드 = ABC
```

- `"abc"`(길이 3)는 A·B 를 지나 C 에서 걸렸다. `"a"` 는 셋 다 지나 무가드 가지로 갔다.
- ★ **세 가드가 모두 평가된다.** 가드에 **비싼 연산이나 부수효과**를 넣으면 안 되는 이유다.

```text
  case A when 조건1   -> 조건1 평가
       |  거짓
       v
  case B when 조건2   -> 조건2 평가
       |  거짓
       v
  case C when 조건3   -> 조건3 평가
       |  거짓
       v
  case D (무가드)     -> 여기로
```

- `when` 은 **제한 식별자가 아니다** — 변수·메서드 이름으로 아무 제약 없이 쓸 수 있다.\
  `yield` 와 다른 점이다([**21번 주제**](../21-switch-statement-and-expression/)).

**비용** — 가드는 **순서대로 전부 평가될 수 있다.** 비싼 조건은 앞으로 빼거나 `switch` 밖에서 계산한다.

### (6) `MatchException` — 점호표를 인쇄한 뒤 명단이 늘었을 때

**언제 쓰나** — `sealed` 계층을 라이브러리 경계에 둘지 판단할 때.

`Ex.java (23-rt)` — `sealed` 계층과 `switch` 를 **다른 파일**에 둔다.

```text
23rt/
  Shape.java     public sealed interface Shape permits Circle, Square { }
  Circle.java    public record Circle(double r) implements Shape { }
  Square.java    public record Square(double s) implements Shape { }
  Ex.java        switch (sh) { case Circle c -> "원"; case Square q -> "정사각형"; }   // default 없음
```

1차 컴파일 직후의 부트스트랩 인자를 찍어 둔다.

```text
BootstrapMethods:
  0: #98 REF_invokeStatic java/lang/runtime/SwitchBootstraps.typeSwitch:(Ljava/lang/invoke/MethodHandles$Lookup;Ljava/lang/String;Ljava/lang/invoke/MethodType;[Ljava/lang/Object;)Ljava/lang/invoke/CallSite;
    Method arguments:
      #22 Circle
      #26 Square
```

그 뒤 `Shape` 의 허용 목록에 `Triangle` 을 넣고 **`Shape` 와 `Triangle` 만** 다시 컴파일한다.

```text
--- 1차 컴파일
(성공)
Circle[r=1.0] -> 원
--- 2차 컴파일: Shape 와 Triangle 만 (Ex 는 그대로)
(성공)
--- 기존 타입
Circle[r=1.0] -> 원
--- 새 타입
Exception in thread "main" java.lang.MatchException
	at Ex.name(Ex.java:3)
	at Ex.main(Ex.java:10)
```

```text
  컴파일 시점                              실행 시점
  +-----------------------------+         +-----------------------------+
  | Shape permits Circle, Square|         | Shape permits Circle,       |
  | 부트스트랩 인자 = {Circle,   |  ---->  |        Square, Triangle     |
  |                   Square}   |         | 부트스트랩 인자는 그대로      |
  | -> 완결하다고 판정           |         | Triangle -> 어느 번호도 아님  |
  +-----------------------------+         +-----------------------------+
                                            -> default: 44 -> MatchException
```

- ★ **부트스트랩 인자가 낡은 것**이 이 현상의 정확한 모양이다. 목록이 클래스 파일에 박혀 있다(1).
- **기존 타입은 그대로 돈다.** 깨지는 것은 새로 생긴 타입뿐이다.
- javac 는 **막아 주지 못한다** — 완결성 검사는 `Ex.java` 를 컴파일할 때만 돈다.

`MatchException` 의 javadoc 이 이 상황을 **첫 번째 사례**로 적었다 (JDK 21.0.5 `src.zip`).

```text
 * <ul>
 *     <li>Separate compilation anomalies, where parts of the type hierarchy that
 *         the patterns reference have been changed, but the pattern matching
 *         construct has not been recompiled. For example, if a sealed interface
 *         has a different set of permitted subtypes at run time than it had at
 *         compile time, or if an enum class has a different set of enum constants
 *         at runtime than it had at compile time, or if the type hierarchy has
 *         been changed in some incompatible way between compile time and run time.</li>
```

- 같은 javadoc 이 **`null` 과 중첩 패턴** 사례도 둘 더 적었다 — 그쪽은 [**24번 주제**](../24-record-patterns/)가 정본이다.
- `sealed` 쪽 관점(허용 목록이 `PermittedSubclasses` 속성으로 남는 것)은 [`../15-sealed-classes/`](../15-sealed-classes/)가 정본이다.

**비용** — `default` 를 넣으면 이 예외가 사라진다. 대신 **새 타입이 조용히 `default` 로 샌다.**\
실무 함의: **`sealed` 계층과 그것을 `switch` 하는 코드는 같이 빌드·배포한다.**

## 문법 — 형태와 규칙

### 형태

```java
// 타입 패턴
switch (o) {
    case String s  -> ...;
    case Integer i -> ...;
    default        -> ...;
}

// null 을 받는다
case null -> ...;
case null, default -> ...;

// 가드
case String s when s.length() > 3 -> ...;

// 여러 레이블을 묶는다 — 패턴에는 못 묶는다 (아래 규칙 참고)
case 1, 2, 3 -> ...;           // 상수는 된다

// 배열 타입도 패턴이 된다
case int[] a -> ...;

// sealed 라서 default 가 없다
switch (shape) {
    case Circle c -> ...;
    case Square q -> ...;
    case Rect   r -> ...;
}
```

### 규칙 불릿

- **패턴 `switch` 는 문에도 식에도 완결성을 요구한다.** 옛 selector 의 `switch` 문과 다르다.
- `default` 와 **무조건 패턴**(`case Object o`)은 **같이 쓸 수 없다.**
- **넓은 패턴이 앞에 오면 지배 에러**다. 좁은 것부터 넓은 것으로 적는다.
- **`default` 뒤의 `case` 도 지배 에러**다. `default` 는 마지막에 둔다.
- **가드가 붙은 `case` 끼리는 지배 검사를 하지 않는다.** 순서는 직접 따져야 한다.
- **가드만 있는 `case` 는 완결성에 안 쳐 준다.** 무가드 가지가 따로 있어야 한다.
- **`case null` 이 없으면 `null` 은 NPE** 다. `default` 가 있어도 그렇다.
- `case null` 은 **다른 패턴과 묶을 수 없고**, `default` 와만 묶인다(`case null, default`).
- **상수 `case` 와 패턴 `case` 를 한 `switch` 에 섞을 때는 selector 타입이 맞아야 한다.**\
  selector 가 `Object` 면 `case "hello"` 는 에러다.
- `when` 은 **제한 식별자가 아니다.** 변수·메서드 이름으로 그대로 쓸 수 있다.

### 완결성을 만드는 것 — 네 가지

| 방법 | 예 | 새 타입이 생기면 |
|---|---|---|
| `default` | `default -> ...` | 조용히 흡수한다 |
| 무조건 패턴 | `case Object o -> ...` | 조용히 흡수한다 |
| `sealed` 전부 나열 | `case Circle`·`case Square`·`case Rect` | **컴파일 에러** |
| `enum` 상수 전부 나열 | `case MON`·`case TUE`·... | **컴파일 에러** |

- 아래 둘이 이 주제를 쓰는 이유다. 위 둘은 **옛 `switch` 와 같은 안전성**이다.

## 어디서 틀리나

★ 이 주제의 값은 대부분 여기 있다. **아래 에러 메시지는 전부 JDK 21.0.5 의 javac 실출력이다.**

### 1. ★ `default` 가 `null` 을 받을 줄 알았다

```text
noCaseNull(null)      -> 던짐: java.lang.NullPointerException
```

```text
Exception in thread "main" java.lang.NullPointerException
	at java.base/java.util.Objects.requireNonNull(Objects.java:233)
	at Ex.noCaseNull(Ex.java:3)
	at Ex.main(Ex.java:11)
```

- **`default` 가 있는데도 NPE** 다. 이 주제 최대의 함정이다.
- `case null` 이 없으면 `switch` **입구의 `requireNonNull`** 에서 튕긴다. 검문소까지 가지도 않는다.
- **NPE 메시지가 비어 있다** — 옛 `switch` 의 NPE 와 달리 어느 메서드에서 났는지 문구가 없다.
- 고치는 법 둘: `case null -> ...` 를 추가하거나 `case null, default -> ...` 로 묶는다.

### 2. 패턴 `switch` **문**도 완결해야 한다

`Ex.java (23-e10)`

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

- 메시지가 **`the switch statement`** 라고 말한다 — 식이 아니라 문이다.
- [**21번 주제**](../21-switch-statement-and-expression/)에서 `enum` `switch` **문**은 상수를 빠뜨려도 통과했다.\
  ★ 경계는 「문이냐 식이냐」만이 아니라 **「옛 selector 냐 패턴이냐」**에도 걸려 있다.

### 3. `sealed` 인데 가지를 빠뜨렸다 — 이건 **좋은** 에러다

`Ex.java (23-e2)`

```text
Ex.java:6: error: the switch expression does not cover all possible input values
        return switch (sh) {
               ^
1 error
```

- 이 에러를 받으려고 `sealed` + 패턴 `switch` 를 쓴다. **원하던 동작**이다.
- `default` 를 넣으면 이 에러가 사라지고 **`sealed` 의 값어치도 대부분 사라진다.**

### 4. 넓은 패턴을 먼저 썼다

`Ex.java (23-e1)` · `Ex.java (23-e8)` · `Ex.java (23-e3)`

```text
Ex.java:6: error: switch has both an unconditional pattern and a default label
            default        -> "그 밖";
            ^
Ex.java:5: error: this case label is dominated by a preceding case label
            case String s  -> "문자열";      // 앞의 Object 가 이미 다 먹었다
                 ^
2 errors
```

```text
Ex.java:8: error: this case label is dominated by a preceding case label
            case Circle c -> "원";
                 ^
1 error
```

```text
Ex.java:6: error: this case label is dominated by a preceding case label
            case Integer i -> "정수";        // default 뒤에 case 를 두면?
                 ^
1 error
```

- 셋 다 같은 규칙이다 — **앞이 뒤를 다 먹으면 뒤는 도달 불가**.
- 첫 번째만 에러가 둘이다. `case Object o` 가 무조건 패턴이라 `default` 와 겹친 것이다.
- 기억법: **좁은 것 -> 넓은 것 -> `default`.** 예외 없다.

### 5. ★ 같은 가드를 두 번 썼는데 **컴파일된다**

`Ex.java (23-e4)`

```java
case String s when s.length() > 3 -> "긴 문자열";
case String s when s.length() > 3 -> "또 긴 문자열";   // 똑같은 가드
case String s -> "짧은 문자열";
default -> "그 밖";
```

```text
(컴파일 성공)
짧은 문자열
```

- ★ **경고도 에러도 없다.** javac 는 **가드의 내용을 보지 않는다.**
- 둘째 가지는 **영원히 도달할 수 없는 죽은 코드**다. 컴파일러가 봐 주는 것은 여기까지다.
- 반대로 **무가드가 먼저 오면** 가드 붙은 것도 막힌다(`Ex.java (23-e7)`).

```text
Ex.java:5: error: this case label is dominated by a preceding case label
            case String s when s.length() > 3 -> "긴 문자열";   // 가드가 있어도 앞이 먹었다
                 ^
1 error
```

- 정리: **무가드 -> 가드는 에러, 가드 -> 가드는 통과.** 후자는 사람이 순서를 책임진다.

### 6. 가드만으로 완결하려 했다

`Ex.java (23-e9)`

```java
return switch (o) {
    case String s when s.length() > 3 -> "긴 문자열";
};
```

```text
Ex.java:3: error: the switch expression does not cover all possible input values
        return switch (o) {
               ^
1 error
```

- 타입이 전부를 덮어도 **가드가 붙으면 완결에 안 쳐 준다.** 가드가 거짓일 수 있기 때문이다.
- 무가드 가지(`case String s ->`)나 `default` 가 따로 있어야 한다.

### 7. `case null` 을 두 번 썼다

`Ex.java (23-e6)`

```text
Ex.java:6: error: duplicate case label
            case null      -> "또 널";
                 ^
1 error
```

- `null` 도 하나의 레이블이다. 중복은 상수와 같은 규칙으로 막힌다.

### 8. selector 타입과 안 맞는 상수를 썼다

`Ex.java (23-e5)`

```java
return switch (o) {          // o 는 Object
    case String s -> "문자열";
    case "hello"  -> "인사";          // 타입 패턴 뒤의 상수
    default       -> "그 밖";
};
```

```text
Ex.java:5: error: constant label of type String is not compatible with switch selector type Object
            case "hello"  -> "인사";          // 타입 패턴 뒤의 상수
                 ^
1 error
```

- 메시지가 정확하다 — **상수 레이블의 타입이 selector 타입과 맞아야** 한다.
- `switch (s)` 에서 `s` 가 `String` 이면 `case "hello"` 는 된다. selector 가 `Object` 라서 막힌 것이다.

### 9. ★ 17 에서 컴파일했다

**JDK 17.0.13 의 javac** (`Ex.java (23-a)` 그대로)

```text
Ex.java:10: error: patterns in switch statements are a preview feature and are disabled by default.
            case Circle c -> "원";
                 ^
  (use --enable-preview to enable patterns in switch statements)
1 error
```

**JDK 21 의 `javac --release 17`** (같은 소스)

```text
Ex.java:10: error: patterns in switch statements are not supported in -source 17
            case Circle c -> "원";
                 ^
  (use -source 21 or higher to enable patterns in switch statements)
1 error
```

`--release 20` 도 같은 모양이다(숫자만 `20`).

- ★ **두 메시지가 다르다.** 17 의 javac 는 "프리뷰라 꺼져 있다", 21 의 javac 는 "17에서는 지원 안 된다".
- **17 에서 `--enable-preview` 를 붙이면 컴파일된다** — 다만 대가가 크다.

```text
--- 17 + --enable-preview 로 컴파일
Note: Ex.java uses preview features of Java SE 17.
Note: Recompile with -Xlint:preview for details.
--- 그 클래스를 --enable-preview 없이 실행
java.lang.UnsupportedClassVersionError: Preview features are not enabled for Ex (class file version 61.65535). Try running with '--enable-preview'
--- 그 클래스를 JDK 21 로 실행
java.lang.UnsupportedClassVersionError: Ex (class file version 61.65535) was compiled with preview features that are unsupported. This version of the Java Runtime only recognizes preview features for class file version 65.65535
```

- ★ **클래스 파일 버전이 `61.65535`** 다. 마이너 버전 `65535` 가 "프리뷰"를 뜻한다.
- 그래서 **그 클래스 파일은 딱 그 JDK 에서만 돈다.** 21 로 가져가면 실행조차 안 된다.
- 프리뷰로 컴파일한 산출물은 **배포할 수 없다**는 뜻이다. 21 로 올리는 것 말고 답이 없다.
- (위 실행 오류 줄의 한국어 머리말 `오류: 기본 클래스 ...` 는 **한국어 로캘의 런처 메시지**라 생략했다.)

### 10. `if` 사슬로 쓰고 빠뜨렸다

```text
Rect[w=2.0, h=3.0]   name=직사각형   ifElse=빠뜨린 것이 여기로 온다
```

- 같은 분기를 `if (x instanceof A a) ... else if ...` 로 쓰면 **빠뜨려도 조용하다.**
- 경고도 에러도 없다. 이것이 **`switch` 로 옮기는 이유 전부**다.
- `if` 사슬 자체의 규칙(스코프 등)은 [**22번 주제**](../22-instanceof-type-patterns/)가 정본이다.

## 구현 세부사항 대 언어 보장

| 무엇 | 어디에 속하나 | 근거 |
|---|---|---|
| 패턴 `switch` 가 Java 21 부터 | **언어 보장** | `--release 20` 에러 `(use -source 21 or higher)` |
| 문·식 **둘 다** 완결성을 요구 | **언어 보장** | `the switch statement does not cover ...` |
| `default` 와 무조건 패턴 공존 금지 | **언어 보장** | `switch has both an unconditional pattern and a default label` |
| 지배 관계 | **언어 보장** | `this case label is dominated by a preceding case label` |
| 가드끼리는 지배 검사를 안 한다 | **언어 보장** | 같은 가드 둘이 컴파일된다(23-e4) |
| 가드만으로는 완결이 안 된다 | **언어 보장** | `does not cover all possible input values` |
| ★ `case null` 없으면 `null` 이 NPE | **언어 보장** | 실행으로 확인 · `default` 가 있어도 그렇다 |
| `MatchException` 이 21 부터 | **API 보장** | javadoc `@since 21` |
| 분리 컴파일에서 `MatchException` 이 난다 | **언어 보장** | javadoc 이 첫 사례로 명시 |
| `invokedynamic typeSwitch` 로 컴파일되는 것 | **구현 세부** | javac 21 의 코드 생성 방식 |
| `SwitchBootstraps.typeSwitch` 라는 이름 | **구현 세부** | `java.lang.runtime` 의 내부 API |
| `typeSwitch` 가 `null` 에 `-1` 을 준다 | **구현 세부** | 바이트코드의 `tableswitch { // -1 to 1 }` 로 관찰 |
| `Objects.requireNonNull` 로 `null` 을 막는 것 | **구현 세부** | 어떤 방법으로 NPE 를 내느냐는 컴파일러 자유 |
| 부트스트랩 `Method arguments` 의 타입 목록 | **구현 세부** | 같은 이유. **낡는다는 사실**은 보장이다 |
| 에러 메시지의 **문구 자체** | **구현 세부** | javac 의 것이다 |

### 두 `switch` 가 갈리는 자리를 한 그림으로

```text
  옛 switch                                 패턴 switch
  +----------------------------------+      +----------------------------------+
  | 값 -> 번호 (ordinal/hashCode/값)  |      | null 검사 (requireNonNull)       |
  |   null 이면 여기서 NPE            |      |   case null 이 있으면 생략        |
  | tableswitch / lookupswitch        |      | invokedynamic typeSwitch -> int  |
  | 가지 본문                         |      | tableswitch / lookupswitch       |
  |                                  |      | 가지마다 checkcast + 본문         |
  +----------------------------------+      +----------------------------------+
    완결성: 식만 요구                          완결성: 문·식 둘 다 요구
    default 가 null 을 못 받는다               default 가 null 을 못 받는다 (같다)
    지배 개념 없음 (상수는 중복만 금지)          지배 검사가 있다
```

- ★ **바뀐 것은 "무엇으로 분기하나"이고, 바뀌지 않은 것은 "`default` 가 `null` 을 안 받는다"** 이다.\
  후자를 "옛 `switch` 에서 그랬으니 패턴에서도 그렇다"로 외우면 정확하다.

## 언제 쓰고 언제 안 쓰나

**쓴다**

- **`sealed` 계층 분기** — 이 주제의 존재 이유다. `default` 없이 쓰면 새 타입이 빌드를 멈춘다.
- **`instanceof` 사슬이 셋을 넘을 때** — 같은 코드를 완결성 검사가 붙은 형태로 바꾼다.
- **`Object` 를 받아 여러 타입으로 갈라야 할 때**(직렬화·프로토콜 디코딩·프레임워크 경계).
- **같은 타입 안에서 값으로 더 쪼갤 때** — `when` 가드.

**안 쓴다**

- **타입이 하나뿐일 때** — `if (o instanceof X x)` 로 충분하다([**22번 주제**](../22-instanceof-type-patterns/)).
- **내가 설계한 열린 계층일 때** — 다형성(메서드 재정의)이 맞다.\
  하위 타입이 자주 느는 곳에 완결 `switch` 를 두면 고칠 곳이 계속 늘어난다.
- **가지 본문이 길어질 때** — `switch` 는 지도여야 한다. 본문은 메서드로 뺀다.
- **가드에 비싼 연산이 들어갈 때** — 가드는 순서대로 전부 평가될 수 있다.

**중간 지대**

- `default` 를 넣을지는 **"선택지가 늘어날 것인가"** 로 판단한다.\
  라이브러리의 공개 `sealed` 타입이라면 **명단을 늘리지 않겠다는 약속**까지 같이 하는 셈이다.
- `case null` 을 항상 쓸지는 **"`null` 이 정말 올 수 있나"** 로 판단한다.\
  올 수 없으면 NPE 가 나는 쪽이 낫다 — 버그를 감추지 않는다.

## 핵심 문장

1. 옛 `switch` 는 **값에서 번호를 뽑고**, 패턴 `switch` 는 **`invokedynamic typeSwitch` 로 번호를 물어본다.**
2. ★ 패턴 `switch` 는 **`if` 사슬이 아니다.** 판별이 한 번이고, 그 뒤는 평범한 `tableswitch` 다.
3. `case` 에 적은 타입 목록은 **부트스트랩 인자로 클래스 파일에 박힌다** — 그래서 낡을 수 있다.
4. 완결성은 **`sealed` 전부 나열** 또는 **`enum` 상수 전부 나열**로 만들 때만 값이 있다.\
   `default` 와 무조건 패턴은 옛 `switch` 와 같은 안전성이다.
5. ★ 패턴 `switch` 는 **문에도 완결성을 요구한다.** 옛 selector 의 `switch` 문과 다르다.
6. ★ **`default` 는 `null` 을 받지 않는다.** `case null` 이 없으면 입구의 `requireNonNull` 에서 NPE 다.
7. `case null` 을 쓰면 `requireNonNull` 이 사라지고 `typeSwitch` 가 **`-1`** 을 돌려준다.
8. **넓은 패턴이 앞에 오면 지배 에러**다. `default` 뒤의 `case` 도 마찬가지다.
9. ★ **가드끼리는 지배 검사를 하지 않는다.** 같은 가드를 두 번 써도 컴파일된다 — 순서는 사람 책임이다.
10. 가드만 있는 `case` 는 **완결에 안 쳐 준다.**
11. 완결성은 **컴파일 시점의 판정**이다 — `sealed` 명단이 뒤에 늘면 런타임에 `MatchException` 이다.
12. 17 에서는 **프리뷰**다. `--enable-preview` 로 컴파일한 클래스 파일은 **그 JDK 에서만 돈다**(`61.65535`).

## 관련 자료

- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 23번)
- [`../../../../../../history/java/java-21.md`](../../../../../../history/java/java-21.md) — **언제·왜 들어왔나**(JEP 441 확정, 네 번의 프리뷰).\
  여기는 **어떻게 쓰고 무엇을 못 하나**만 다룬다
- [`../15-sealed-classes/`](../15-sealed-classes/) — **`sealed` 자체가 정본이다.**\
  허용 목록의 조건, `PermittedSubclasses` 속성, `non-sealed` 에서 완결성이 끊기는 것이 거기 있다.\
  여기는 **`switch` 쪽에서 본 완결성**과 **`typeSwitch` 부트스트랩**만
- [**21번 주제**](../21-switch-statement-and-expression/)(`switch` 문과 식) — **`switch` 문법의 뼈대가 정본.**\
  화살표·`yield`·폴스루·`tableswitch`/`lookupswitch`·식의 완결성이 거기다.\
  여기는 **`case` 에 패턴이 들어오면서 달라지는 것**만 — `null`·지배·가드·문의 완결성
- [**22번 주제**](../22-instanceof-type-patterns/)(`instanceof` 타입 패턴) — **타입 패턴과 흐름 스코프가 정본.**\
  `case String s` 의 `s` 가 어떤 물건인지는 거기가 답한다. 여기는 **그것이 `case` 에 들어갔을 때**만
- [**24번 주제**](../24-record-patterns/)(`record` 패턴, 21) — `case Circle(double r)` 형태의 해체가 정본.\
  `MatchException` javadoc 의 **나머지 두 사례**(`null` 과 중첩 패턴)도 거기서 재현한다
- [`../13-enum-classes/`](../13-enum-classes/) — `enum` 의 `switch` 특별 대우. **`case MON` 의 규칙은 거기**
- [`../14-records/`](../14-records/) — `record` 가 `sealed` 와 묶여 합타입이 되는 것. **`record` 문법은 거기**
- [`../09-inheritance-overriding/`](../09-inheritance-overriding/) — 다형성으로 분기하는 반대편 해법.\
  **디스패치 규칙은 거기**, 여기는 **타입을 직접 물어보는 쪽**
- [`../35-string/`](../35-string/) — `switch (String)` 의 `hashCode` + `lookupswitch`. **옛 `switch` 쪽 정본**
- [`../25-exceptions/`](../25-exceptions/) — `MatchException` 도 `RuntimeException` 이다. **예외 규칙은 거기**
- [`../../../../../engineering/design-patterns-gof/`](../../../../../engineering/design-patterns-gof/) — Visitor 패턴.\
  **`sealed` + `switch` 가 Visitor 를 대체하는 거래**는 [`../15-sealed-classes/`](../15-sealed-classes/)에 있다
- [`../../언어-특성/README.md`](../../언어-특성/README.md) — JIT·GC·`invokedynamic` 의 런타임 내부.\
  **여기서는 `invokedynamic` 을 "런타임에 한 번 정해지는 호출"까지만** 쓴다

## 용어 풀이

- **패턴 `switch`** — `case` 에 상수 대신 패턴을 쓰는 `switch`. Java 21 정식(17~20 프리뷰).
- **타입 패턴(type pattern)** — `String s` 형태. 정본은 [**22번 주제**](../22-instanceof-type-patterns/).
- **완결성(exhaustiveness)** — `case` 들이 selector 타입의 모든 값을 덮는다는 판정.
- **무조건 패턴(unconditional pattern)** — selector 타입의 모든 값에 맞는 패턴. `default` 와 같이 못 쓴다.
- **지배(dominance)** — 앞 `case` 가 뒤 `case` 의 값을 전부 먼저 가져가는 관계. 컴파일 에러다.
- **가드(`when`)** — `case` 에 붙는 추가 조건. `when` 은 제한 식별자가 **아니다.**
- **`case null`** — `null` 을 받는 레이블. **Java 21.** 없으면 `null` 은 NPE 다.
- **`invokedynamic`** — 호출 대상을 런타임에 한 번 정하고 그 뒤 고정하는 JVM 명령.
- **`typeSwitch`** — `java.lang.runtime.SwitchBootstraps` 의 부트스트랩. "몇 번째 `case` 인가"를 돌려준다.
- **부트스트랩 인자(`Method arguments`)** — `invokedynamic` 호출 지점에 박히는 상수들.\
  패턴 `switch` 에서는 **`case` 에 적은 타입 목록**이 여기 들어간다.
- **`Objects.requireNonNull`** — `null` 이면 NPE 를 던지는 표준 메서드. `case null` 이 없을 때 앞에 붙는다.
- **`MatchException`** — 완결 판정된 매칭이 런타임에 안 맞을 때 던지는 예외. **Java 21.**
- **프리뷰 기능(preview feature)** — 정식이 되기 전 `--enable-preview` 로만 쓰는 기능.\
  그 클래스 파일은 마이너 버전이 `65535` 라 **그 JDK 에서만** 돈다.

## 더 들어가면

- **`typeSwitch` 가 `null` 에 `-1` 을 주는 설계**가 `case null` 문법을 가능하게 한 것이다.\
  검문소가 "번호 없음"을 표현할 수 있으니, 그 번호에 가지를 붙이면 된다.\
  옛 `switch` 는 번호를 **값에서 계산**했기 때문에 `null` 에 줄 번호가 애초에 없었다.
- **`case null` 이 다른 패턴과 못 묶이는 이유**도 같은 데서 온다 — 돌려 확인했다(`Ex.java (23-e11)`).

  ```text
  Ex.java:4: error: invalid case label combination
              case null, String s -> "널이거나 문자열";
                         ^
  1 error
  ```

  `case null, String s ->` 는 "`-1` 번이거나 `0` 번"이 되는데, 그러면 `s` 가 `null` 일 수도 있게 된다.\
  패턴 변수가 항상 그 타입임을 보장할 수 없으므로 막는다. `default` 는 변수를 안 만들어서 묶을 수 있다.
- **지배 검사가 가드를 안 보는 이유**는 **정지 문제**에 가깝다.\
  `when` 안에는 아무 식이나 올 수 있고, 두 조건이 겹치는지 판정하는 일반 알고리즘이 없다.\
  그래서 javac 는 **타입만 보고** 판정하고, 가드가 있으면 손을 뗀다.
- **`switch` 문에도 완결성을 요구하게 만든 것**은 설계 선택이다.\
  옛 `switch` 문은 "안 걸리면 아무 일도 안 함"이 자연스러웠지만,\
  패턴 `switch` 는 **패턴 변수를 만드는 구문**이라 "아무 일도 안 함"이 버그일 확률이 훨씬 높다.
- **`enum` 을 패턴 `switch` 로 쓸 수도 있다** — 돌려 확인했다(`Ex.java (23-f2)`, 21 · 25 동일).

  ```java
  sealed interface Cmd permits Basic, Custom { }
  enum Basic implements Cmd { UP, DOWN }
  record Custom(String s) implements Cmd { }

  static String f(Cmd c) {
      return switch (c) {
          case Basic b          -> "기본 " + b;
          case Custom(String s) -> "사용자 " + s;
      };
  }
  ```

  ```text
  기본 UP / 기본 DOWN / 사용자 q
  ```

  `case Basic b ->` 처럼 **타입으로** 받으면 상수 하나하나를 안 적어도 되고, `default` 없이 완결이다.\
  `enum` 이 `sealed` 인터페이스를 구현할 수 있다는 것은 [`../15-sealed-classes/`](../15-sealed-classes/)의 「더 들어가면」이 정본이다.
- **이 주제의 선행 넷이 전부 다른 버전**이라는 점은 외울 값어치가 있다.

  ```text
  14  switch 식 · 화살표 · yield        (21번 주제)
  16  instanceof 타입 패턴              (22번 주제)
  17  sealed / permits                 (15번 주제)
  21  switch 패턴 매칭 · case null      (이 주제)
  21  record 패턴                       (24번 주제)
  ```

  "패턴 매칭은 21부터"라고 뭉뚱그리면 **16·17 짜리 코드까지 21 이라고 잘못 외운다.**
