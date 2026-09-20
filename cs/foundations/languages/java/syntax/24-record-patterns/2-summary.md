# java/syntax/24 — `record` 패턴 (21): 중첩 해체 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — JDK 21.0.5 의 `lib/src.zip` 을 **직접 풀어 읽은** javadoc 하나다.\
> `java.base/java/lang/MatchException.java` — `@since 21`.\
> 그 javadoc 이 나열한 **네 가지 사례** 중 이 주제에 해당하는 **셋**(중첩 `sealed`·중첩 `record`·접근자 예외)을\
> 본문에서 인용하고 **전부 실행으로 재현**했다. JLS 본문은 열지 않았다.
> **실행 검증** — 이 문서의 모든 출력·에러 메시지는 Temurin JDK 에서 실제로 돌려 얻은 것이다.\
> 프로그램 6개 + 컴파일 에러용 7개. `javac` 30회 · `java` 14회 · `javap` 2회.\
> 도는 프로그램은 **21.0.5 · 25.0.1** 에서 돌렸다.\
> ★ **17.0.13 에서는 문법 자체가 파싱되지 않는다** — 그 에러도 실어 두었다.\
> 버전 갈림(`--release 20` / `21`, 25 의 `--enable-preview`)도 실제로 찍었다.\
> 역어셈블은 `javap -c -p` 출력을 **그대로** 옮겼다.
> **버전** — `record` 패턴은 **Java 21** 정식(19·20 프리뷰).\
> ★ 컴포넌트에 **원시 타입 확대**(`int` 컴포넌트를 `long` 패턴으로)는 **25 에서도 아직 프리뷰**다 — 돌려 확인했다.
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**`record` 패턴은 「상자를 열면서 안의 물건을 꺼내 이름표를 붙이는 것」이다.**

타입 패턴([**22번 주제**](../22-instanceof-type-patterns/))은 **상자 자체에** 이름표를 붙인다 — `Line l`.\
`record` 패턴은 **상자를 열고 안의 칸마다** 이름표를 붙인다 — `Line(Point a, Point b)`.\
그리고 안의 칸이 또 상자면 **한 번 더 열 수 있다** — `Line(Point(int ax, int ay), Point(int bx, int by))`.

여기서 이 주제의 모든 함정이 나온다. **상자를 열려면 상자가 있어야 한다.**\
칸이 비어 있으면(=`null`) **열 수 없으므로 매칭이 실패**하고, 칸에 이름표만 붙이는 것은 **비어 있어도 된다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 상자 | `record` 인스턴스 |
| 상자의 칸 | `record` 컴포넌트 |
| 상자에 이름표만 붙임 | 타입 패턴 `Line l` |
| **상자를 열고 칸마다 이름표** | **`record` 패턴 `Line(Point a, Point b)`** |
| 칸을 여는 손 | 컴포넌트 접근자 호출 (`l.from()`) |
| 칸이 비어 있음 | 컴포넌트가 `null` |
| 빈 칸에 이름표만 붙이기 | 무조건 타입 패턴 — **된다** |
| 빈 칸을 열려고 함 | 중첩 `record` 패턴 — **안 된다(매칭 실패)** |
| 칸을 여는 손이 다침 | 접근자가 예외를 던짐 -> `MatchException` |

```text
타입 패턴                                record 패턴
+-------------------------------+       +-------------------------------+
| if (o instanceof Line l) {    |       | if (o instanceof Line(        |
|     Point a = l.from();       |       |         Point(int ax,int ay), |
|     Point b = l.to();         |       |         Point(int bx,int by)))|
|     ... a.x() ... b.y() ...   |       |     ... ax ... by ...         |
| }                             |       |                               |
+-------------------------------+       +-------------------------------+
  접근자를 손으로 부른다                   컴파일러가 대신 부른다
  중간 변수 a·b 가 남는다                  필요한 값만 이름이 생긴다
```

**똑같은 구조로** Java 가 이렇게 동작한다: 상자를 여는 손 = `invokevirtual Line.from()`,\
칸을 여는 데 실패 = `instanceof` 가 거짓, 손이 다침 = 예외 테이블이 `MatchException` 으로 감싼다.\
셋 다 `javap -c -p` 에 그대로 보인다.

실무에서 이게 값을 내는 자리는 **중첩된 불변 데이터**다 — JSON 트리, 수식 트리, 이벤트 페이로드.\
`sealed` + `record` 로 모양을 닫아 두면, `switch` 한 덩어리가 **구조 검사와 값 꺼내기를 한 번에** 한다.

> **해체 패턴(deconstruction pattern)** — `record` 의 컴포넌트를 꺼내면서 매칭하는 패턴.\
> 예: `Point(int x, int y)` 는 "`Point` 이면 `x()`·`y()` 를 꺼내 `x`·`y` 로 부른다"는 뜻이다.\
> javac 의 에러 메시지가 이 이름을 쓴다 — `deconstruction patterns can only be applied to records`.

> **무조건 패턴(unconditional pattern)** — 그 자리의 **선언된 타입 전부**에 맞는 패턴.\
> 예: 컴포넌트 타입이 `Point` 일 때 `Point p` 는 무조건 패턴이고, `String s` 는 아니다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 셋을 과녁으로 둔다.

1. `record` 패턴 한 줄이 **무엇으로 펼쳐지는가** — 접근자는 누가 부르는가.
2. ★ **왜 `null` 컴포넌트는 매칭되는데 중첩 `record` 의 `null` 은 안 되는가.**
3. 완결하다고 판정된 중첩 패턴이 런타임에 안 맞는 경우가 있는가 — 있다면 언제인가.

## 동작 방식

### (1) 한 줄이 무엇으로 펼쳐지나 — 접근자 호출 + `instanceof`

**언제 쓰나** — "`record` 패턴이 마법인가"를 따질 때. 그리고 (2)의 `null` 규칙을 이해하기 전에.

`Ex.java (24-a)`

```java
record Point(int x, int y) { }
record Line(Point from, Point to) { }

// 타입 패턴만 쓰면 접근자를 손으로 부른다
static String withoutRecordPattern(Object o) {
    if (o instanceof Line l) {
        Point a = l.from(), b = l.to();
        return "(" + a.x() + "," + a.y() + ")-(" + b.x() + "," + b.y() + ")";
    }
    return "그 밖";
}

// record 패턴 — 한 줄로 해체한다
static String withRecordPattern(Object o) {
    if (o instanceof Line(Point(int ax, int ay), Point(int bx, int by)))
        return "(" + ax + "," + ay + ")-(" + bx + "," + by + ")";
    return "그 밖";
}
```

**실행 결과** (JDK 21.0.5 — 25.0.1 에서도 같았다)

```text
withoutRecordPattern = (1,2)-(3,4)
withRecordPattern    = (1,2)-(3,4)
```

`javap -c -p Ex.class` 로 `withRecordPattern` 을 연다(JDK 21.0.5). **핵심만 추린 것이 아니라 전부다.**

```text
  static java.lang.String withRecordPattern(java.lang.Object);
    Code:
       0: aload_0
       1: instanceof    #7                  // class Ex$Line
       4: ifeq          132
       7: aload_0
       8: checkcast     #7                  // class Ex$Line
      11: astore_1
      12: aload_1
      13: invokevirtual #9                  // Method Ex$Line.from:()LEx$Point;
      16: astore        8
      18: aload         8
      20: instanceof    #17                 // class Ex$Point          <- 여기가 핵심이다
      23: ifeq          132
      26: aload         8
      28: astore_2
      29: aload_1
      30: invokevirtual #13                 // Method Ex$Line.to:()LEx$Point;
      33: astore        8
      35: aload         8
      37: instanceof    #17                 // class Ex$Point
      40: ifeq          132
      43: aload         8
      45: astore_3
      46: aload_2
      47: invokevirtual #16                 // Method Ex$Point.x:()I
      50: istore        8
      ...
     114: iload         8
     116: istore        7
     118: iload         4
     120: iload         5
     122: iload         6
     124: iload         7
     126: invokedynamic #25,  0             // InvokeDynamic #0:makeConcatWithConstants:(IIII)Ljava/lang/String;
     131: areturn
     132: ldc           #29                 // String 그 밖
     134: areturn
     135: astore_1
     136: new           #33                 // class java/lang/MatchException
     139: dup
     140: aload_1
     141: invokevirtual #35                 // Method java/lang/Throwable.toString:()Ljava/lang/String;
     144: aload_1
     145: invokespecial #39                 // Method java/lang/MatchException."<init>":(Ljava/lang/String;Ljava/lang/Throwable;)V
     148: athrow
    Exception table:
       from    to  target type
          13    16   135   Class java/lang/Throwable
          30    33   135   Class java/lang/Throwable
          47    50   135   Class java/lang/Throwable
          65    68   135   Class java/lang/Throwable
         101   104   135   Class java/lang/Throwable
```

그림 해설 (한 단계씩):

- **컴파일러가 접근자를 대신 부른다** — `Line.from()`(13) · `Line.to()`(30) · `Point.x()`(47) · `Point.y()` …
- ★ **접근자 결과마다 `instanceof` 가 따라붙는다**(20·37). 이것이 (2)의 `null` 규칙 전부다.
- **예외 테이블**을 보라 — **접근자 호출 구간마다** `Throwable` 을 잡아 `MatchException` 으로 다시 던진다.\
  `from ~ to` 가 `13~16`·`30~33`·`47~50`·… 로, 전부 `invokevirtual` 한 줄씩이다.
- 즉 `record` 패턴은 **"접근자를 부르고, 결과를 검사하고, 다음 칸으로"** 를 반복하는 평범한 코드다.\
  마법이 없다 — 대신 **접근자가 진짜로 불린다**는 점을 기억해야 한다(부수효과·비용).

**비용** — 컴포넌트 하나당 **접근자 호출 한 번**. 손으로 쓴 코드와 같다.\
다만 `record` 의 접근자를 **오버라이드했다면** 그것이 불린다 — (4)에서 본다.

### (2) ★ `null` — 왜 하나는 되고 하나는 안 되나

**언제 쓰나** — 이 주제에서 가장 많이 틀리는 자리. `record` 컴포넌트에 `null` 이 들어갈 수 있을 때마다.

`Ex.java (24-c)` — 무조건 패턴과 해체 패턴을 나란히 던져 본다.

```java
record Point(int x, int y) { }
record Holder(Object o) { }      // 컴포넌트 타입이 Object
record Typed(Point p) { }        // 컴포넌트 타입이 Point

// Holder 의 컴포넌트를 Object 로 받는 것과 String 으로 받는 것
h instanceof Holder(Object o)          // 무조건 (컴포넌트 타입 = 패턴 타입)
h instanceof Holder(String s)          // 조건부 (좁히는 패턴)

// Typed 의 컴포넌트를 Point 로 받는 것과 해체하는 것
t instanceof Typed(Point p)            // 무조건 타입 패턴
t instanceof Typed(Point(var x, var y))// 해체 패턴
```

**실행 결과** (JDK 21.0.5 — 25.0.1 에서도 같았다)

```text
--- Holder
Holder("s")  Holder(Object o)  = 맞음 o=s | Holder(String s) = 맞음 s=s
Holder(null) Holder(Object o)  = 맞음 o=null | Holder(String s) = 안 맞음
Holder(42)   Holder(Object o)  = 맞음 o=42 | Holder(String s) = 안 맞음
--- Typed
Typed(Point(1,2)) Typed(Point p)         = 맞음 p=Point[x=1, y=2] | Typed(Point(var x, var y)) = 맞음 1,2
Typed(null)       Typed(Point p)         = 맞음 p=null | Typed(Point(var x, var y)) = 안 맞음
```

★ **둘째 줄과 마지막 줄이 이 주제의 핵심이다.**

```text
  컴포넌트 값이 null 일 때

  Holder(Object o)          Holder(String s)        Typed(Point p)        Typed(Point(var x, var y))
  +-------------------+     +-------------------+   +-------------------+ +-------------------------+
  | 컴포넌트 타입 Object|     | 컴포넌트 타입 Object|   | 컴포넌트 타입 Point| | 컴포넌트 타입 Point      |
  | 패턴 타입   Object |     | 패턴 타입   String |   | 패턴 타입   Point | | 패턴은 "열어라"         |
  | -> 같다 = 무조건   |     | -> 좁힌다 = 조건부 |   | -> 같다 = 무조건  | | -> 열려면 상자가 있어야 |
  +-------------------+     +-------------------+   +-------------------+ +-------------------------+
       맞는다                    안 맞는다              맞는다                안 맞는다
```

**왜 그런지가 (1)의 바이트코드에 있다.** `Ex.java (24-d)` 로 두 형태만 따로 찍었다.

```text
  static boolean unconditional(Ex$Typed);          <- t instanceof Typed(Point p)
    Code:
       0: aload_0
       1: instanceof    #7                  // class Ex$Typed
       4: ifeq          20
       7: aload_0
       8: astore_2
       9: aload_2
      10: invokevirtual #9                  // Method Ex$Typed.p:()LEx$Point;
      13: astore_3
      14: aload_3
      15: astore_1                          <- 바로 저장한다. instanceof 가 없다
      16: iconst_1
      17: goto          21
      20: iconst_0
      21: ireturn
```

```text
  static boolean deconstruct(Ex$Typed);            <- t instanceof Typed(Point(var x, var y))
    Code:
       0: aload_0
       1: instanceof    #7                  // class Ex$Typed
       4: ifeq          50
       7: aload_0
       8: astore        4
      10: aload         4
      12: invokevirtual #9                  // Method Ex$Typed.p:()LEx$Point;
      15: astore        5
      17: aload         5
      19: instanceof    #24                 // class Ex$Point          <- 검사가 있다
      22: ifeq          50
      25: aload         5
      27: astore_3
      28: aload_3
      29: invokevirtual #26                 // Method Ex$Point.x:()I
      ...
```

- ★ **무조건 패턴에는 `instanceof` 가 없다.** 접근자 결과를 **바로 저장**한다 — 그래서 `null` 도 통과한다.
- ★ **해체 패턴에는 `instanceof Ex$Point` 가 있다.** `null instanceof Point` 는 `false` 이므로 **매칭이 깨진다.**
- `Holder(String s)` 도 좁히는 패턴이라 `instanceof String` 이 들어가고, `null` 에서 실패한다.

**규칙을 한 문장으로.**

> **컴포넌트 자리의 패턴이 「그 컴포넌트 타입에 대한 무조건 타입 패턴」이면 `null` 도 맞고,\
> 그 밖(좁히는 타입 패턴 · 해체 패턴)이면 `null` 은 안 맞는다.**

**실행 결과** (`Ex.java (24-d)`, JDK 21.0.5 — 25.0.1 에서도 같았다)

```text
unconditional(Typed(null)) = true
deconstruct(Typed(null))   = false
```

- ★ **중첩을 한 겹 덜 하면 `null` 이 통과한다.** 이것이 (3)의 `MatchException` 으로 이어진다.
- 실무 대응: **`record` 컴포넌트에 `null` 을 허용하지 않는 것**이 가장 간단하다.\
  컴팩트 생성자에서 `Objects.requireNonNull` 로 막는다 — 그 문법은 [`../14-records/`](../14-records/)가 정본이다.

**비용** — 없다. 규칙을 모르면 **매칭이 조용히 실패**하는 것이 비용이다.

### (3) ★ 완결한데 안 맞는다 — `MatchException` 의 두 번째 사례

**언제 쓰나** — 중첩 패턴으로 `sealed` 계층을 완결시킬 때.

`MatchException` 의 javadoc 이 이 상황을 **직접 예고**한다 (JDK 21.0.5 `src.zip`).

```text
 *     <li>{@code null} values and nested patterns involving sealed classes. If,
 *         for example, an interface {@code I} is {@code sealed} with two permitted
 *         subclasses {@code A} and {@code B}, and a record class {@code R} has a
 *         single component of type {@code I}, then the two record patterns {@code
 *         R(A a)} and {@code R(B b)} together are considered to be exhaustive for
 *         the type {@code R}, but neither of these patterns will match against the
 *         result of {@code new R(null)}.</li>
```

javadoc 이 적은 그대로 만들어 돌렸다 — `Ex.java (24-e)`.

```java
sealed interface I permits A, B { }
record A(int n) implements I { }
record B(String s) implements I { }
record R(I i) { }

// R(A a) 와 R(B b) 둘이 R 에 대해 완결하다고 판정된다 — default 가 없다
static String f(R r) {
    return switch (r) {
        case R(A a) -> "A " + a.n();
        case R(B b) -> "B " + b.s();
    };
}

// 한 겹 위로 올리면 null 도 덮인다
static String g(R r) {
    return switch (r) {
        case R(I i) -> "I " + i;
    };
}
```

**실행 결과** (JDK 21.0.5 — 25.0.1 에서도 같았다)

```text
f(R(A(1)))   = A 1
f(R(B("x"))) = B x
g(R(null))   = I null
Exception in thread "main" java.lang.MatchException
	at Ex.f(Ex.java:9)
	at Ex.main(Ex.java:26)
```

```text
  case R(A a) / case R(B b)              case R(I i)
  +-----------------------------+        +-----------------------------+
  | I 는 sealed -> A 아니면 B    |        | 컴포넌트 타입 I 를 그대로 받음|
  | 둘을 덮었으니 완결하다고 판정 |        | -> 무조건 패턴 -> null 도 맞음|
  | 그러나 null 은 A 도 B 도 아님 |        |                             |
  +-----------------------------+        +-----------------------------+
    new R(null) -> MatchException          new R(null) -> "I null"
```

- ★ **컴파일은 통과한다.** `default` 가 없는데도 완결 판정을 받는다.
- 그런데 `new R(null)` 은 **어느 가지에도 안 맞는다.** 그래서 런타임에 `MatchException` 이다.
- 한 겹 위(`case R(I i)`)로 올리면 무조건 패턴이 되어 `null` 도 받는다 — (2)의 규칙 그대로다.
- **javadoc 이 세 번째 사례로 적은 것**도 같은 모양이다 — 중첩 `record` 에서 `R(S(var s))` 가 `new R(null)` 에 안 맞는 것.\
  `Ex.java (24-d)` 의 `deconstruct(Typed(null)) = false` 가 그 형태다.

[**23번 주제**](../23-switch-pattern-matching/)에서 본 `MatchException` 은 **분리 컴파일** 사례였다.\
이 주제의 것은 **분리 컴파일이 아니다** — 한 번에 컴파일하고 한 번에 실행해도 난다.

```text
  23번의 MatchException                   24번의 MatchException
  +-----------------------------+        +-----------------------------+
  | 원인: 컴파일 뒤 계층이 바뀜   |        | 원인: null 컴포넌트          |
  | 재현: 2단계 컴파일이 필요     |        | 재현: 한 번에 컴파일해도 난다 |
  | 방어: 같이 빌드·배포          |        | 방어: 컴포넌트에 null 금지    |
  |                             |        |      또는 한 겹 위로 받기     |
  +-----------------------------+        +-----------------------------+
```

**비용** — 없다. 대신 **이 함정을 모르면 완결성을 믿고 `default` 를 뺐다가 운영에서 터진다.**

### (4) 접근자가 던지면 — `MatchException` 의 네 번째 사례

**언제 쓰나** — `record` 의 접근자를 오버라이드했거나, 컴포넌트 계산이 실패할 수 있을 때.

javadoc 이 이것도 적어 뒀다 (JDK 21.0.5 `src.zip`).

```text
 * <p>{@code MatchException} may also be thrown by the process of pattern matching
 * a value against a pattern. For example, pattern matching involving a record
 * pattern may require accessor methods to be implicitly invoked in order to
 * extract the component values. If any of these accessor methods throws an
 * exception, pattern matching completes abruptly and throws {@code
 * MatchException}. The original exception will be set as a {@link
 * Throwable#getCause() cause} of the {@code MatchException}. No {@link
 * Throwable#addSuppressed(java.lang.Throwable) suppressed} exceptions will be
 * recorded.
```

`Ex.java (24-d)` 의 뒷부분으로 재현했다.

```java
record Bad(int v) {
    @Override public int v() { throw new IllegalStateException("접근자가 터졌다"); }
}
record Wrap(Bad b) { }
...
Object o = new Wrap(new Bad(1));
if (o instanceof Wrap(Bad(int v))) System.out.println("v=" + v);
```

**실행 결과** (JDK 21.0.5 — 25.0.1 에서도 같았다)

```text
Exception in thread "main" java.lang.MatchException: java.lang.IllegalStateException: 접근자가 터졌다
	at Ex.main(Ex.java:21)
Caused by: java.lang.IllegalStateException: 접근자가 터졌다
	at Ex$Bad.v(Ex.java:13)
	... 1 more
```

- ★ **원래 예외가 그대로 올라오지 않는다.** `MatchException` 으로 **감싸져서** 온다.
- javadoc 이 적은 대로 원래 예외는 **`cause`** 에 들어간다 — 스택의 `Caused by:` 가 그것이다.
- 이것이 (1)의 **예외 테이블**이 하는 일이다. 접근자 호출 구간마다 `Throwable` 을 잡아 다시 던진다.
- 실무 함의: **`record` 접근자를 오버라이드해 일을 시키지 마라.**\
  `record` 컴포넌트는 "그냥 값"이어야 한다. 그 설계 원칙은 [`../14-records/`](../14-records/)가 정본이다.

**비용** — 예외 테이블 항목이 컴포넌트 수만큼 늘어난다. 실행 비용은 예외가 안 날 때 0이다.

### (5) `var` 와 제네릭 — 타입 추론이 들어오는 자리

**언제 쓰나** — 중첩이 깊어져 타입을 다 적기가 번거로울 때.

`Ex.java (24-b)`

```java
record Point(int x, int y) { }
record Box<T>(T value) { }
record Pair<A, B>(A first, B second) { }

// var 를 컴포넌트에 쓴다 — 타입은 컴포넌트 선언에서 추론된다
static String withVar(Object o) {
    if (o instanceof Point(var x, var y)) return "x=" + x + " y=" + y + " (x+y=" + (x + y) + ")";
    return "그 밖";
}

// 제네릭 record 패턴 — 타입 인자를 적는다
static String generic(Object o) {
    return switch (o) {
        case Box<?>(String s)  -> "문자열 상자 " + s.toUpperCase();
        case Box<?>(Integer i) -> "정수 상자 " + (i + 1);
        case Box<?>(var v)     -> "그 밖 상자 " + v;
        default                -> "상자가 아니다";
    };
}

// 제네릭 — 타입 인자를 추론시킨다
static String inferred(Box<String> b) {
    if (b instanceof Box(String s)) return "추론된 String " + s;
    return "?";
}

static String pair(Pair<?, ?> p) {
    return switch (p) {
        case Pair(Integer a, Integer b) -> "정수 쌍 합=" + (a + b);
        case Pair(String a, var b)      -> "문자열 " + a + " + " + b;
        case Pair(var a, var b)         -> "그 밖 " + a + "/" + b;
    };
}
```

**실행 결과** (JDK 21.0.5 — 25.0.1 에서도 같았다)

```text
withVar(Point)          = x=3 y=4 (x+y=7)
generic(Box<String>)    = 문자열 상자 ABC
generic(Box<Integer>)   = 정수 상자 42
generic(Box<Double>)    = 그 밖 상자 1.5
inferred(Box<String>)   = 추론된 String zz
pair(1,2)               = 정수 쌍 합=3
pair("a",2)             = 문자열 a + 2
pair(1.5,2)             = 그 밖 1.5/2
```

- **`var x` 의 타입은 `int` 다** — `withVar` 의 `(x + y)` 가 `7` 로 나왔다(문자열 연결이 아니라 덧셈).\
  타입을 **컴포넌트 선언**에서 가져오기 때문이다. [**22번 주제**](../22-instanceof-type-patterns/)에서 `instanceof var v` 가 막힌 것과 대비된다.
- **`Box<?>(String s)` 처럼 타입 인자를 적을 수 있다.** 와일드카드는 런타임에 검사할 것이 없다.
- **`Box(String s)` 처럼 생략하면 추론된다** — `inferred` 가 그 형태다(`Box<String>` 파라미터에서 추론).
- **`case Pair(var a, var b)` 는 무조건 패턴이라 `default` 없이 완결**이다 — `pair` 에 `default` 가 없다.

```text
  var 가 쓰일 수 있는 자리

  instanceof var v                  X   무엇을 검사할지가 없다 (22번 주제)
  Point(var x, var y)               O   컴포넌트 선언이 타입을 준다
  case Box<?>(var v)                O   같은 이유
```

**비용** — 없다. 다만 `var` 를 쓰면 **읽는 사람이 `record` 선언을 찾아가야** 한다.\
컴포넌트 타입이 자명하지 않으면 적어 주는 편이 낫다.

### (6) 중첩은 몇 겹이든 된다 — 그리고 중간에 이름을 붙이려면

**언제 쓰나** — 트리 모양 데이터를 다룰 때.

`Ex.java (24-a)`

```java
record Point(int x, int y) { }
record Line(Point from, Point to) { }
record Colored(Line line, String color) { }

static String deep(Object o) {
    return switch (o) {
        case Colored(Line(Point(var ax, var ay), Point(var bx, var by)), String color)
            -> color + " 선 (" + ax + "," + ay + ")-(" + bx + "," + by + ")";
        case Line(Point p, Point q) -> "선 " + p + "-" + q;
        case Point(int x, int y)    -> "점 " + x + "," + y;
        default                     -> "그 밖";
    };
}

// 한쪽은 통째로 받고 한쪽은 해체한다
static String halfway(Object o) {
    return switch (o) {
        case Line(Point from, Point(int bx, int by)) -> "from=" + from + " to=(" + bx + "," + by + ")";
        default -> "그 밖";
    };
}
```

**실행 결과** (JDK 21.0.5 — 25.0.1 에서도 같았다)

```text
deep(Colored)        = 빨강 선 (1,2)-(3,4)
deep(Line)           = 선 Point[x=1, y=2]-Point[x=3, y=4]
deep(Point)          = 점 9,9
deep("x")            = 그 밖
halfway(Line)        = from=Point[x=1, y=2] to=(3,4)
```

```text
  Colored( Line( Point(var ax, var ay), Point(var bx, var by) ), String color )
     |       |      |                     |                       |
     |       |      +-- 3겹              +-- 3겹                 +-- 1겹
     |       +-- 2겹
     +-- 1겹 (selector 자리)
```

- **깊이 제한이 없다.** 위는 3겹이다.
- ★ **한 패턴에 이름과 해체를 동시에 붙일 수 없다** — `Point(int x, int y) p` 는 문법 에러다(「어디서 틀리나」 4번).\
  둘 다 필요하면 **칸마다 골라서** 쓴다 — `halfway` 처럼 한쪽은 `Point from`, 한쪽은 해체.
- 중첩이 깊어지면 **`switch` 가 트리 모양을 그대로 그린 것처럼** 읽힌다. 그것이 이 문법의 목적이다.

**비용** — 접근자 호출이 컴포넌트 수만큼 늘어난다. 그리고 **읽기 어려워지는 지점**이 있다 —\
3겹을 넘으면 중간 타입으로 한 번 받아 메서드를 나누는 편이 대개 낫다.

## 문법 — 형태와 규칙

### 선언 형태

```java
// instanceof 에서
if (o instanceof Point(int x, int y)) { ... }

// switch 에서
switch (o) {
    case Point(int x, int y) -> ...;
    case Line(Point a, Point b) -> ...;
}

// 중첩
case Line(Point(var ax, var ay), Point(var bx, var by)) -> ...;

// 섞기 — 한쪽은 통째로, 한쪽은 해체
case Line(Point from, Point(int bx, int by)) -> ...;

// 제네릭 — 명시
case Box<?>(String s) -> ...;

// 제네릭 — 추론
if (b instanceof Box(String s)) { ... }

// 가드와 함께
case Point(int x, int y) when x == y -> ...;
```

### 규칙 불릿

- 대상은 **`record` 뿐**이다. 일반 클래스에는 못 쓴다.
- **컴포넌트 개수가 정확히 맞아야** 한다. 하나라도 모자라거나 남으면 에러다.
- 컴포넌트 자리에는 **타입 패턴**(`int x`·`Point p`·`var v`) 또는 **또 다른 `record` 패턴**이 온다.
- **`var` 를 컴포넌트에 쓸 수 있다.** 타입은 컴포넌트 선언에서 온다.
- **원시 타입 컴포넌트는 정확히 그 타입**으로만 받는다. `int` 컴포넌트를 `long` 으로 받는 것은\
  ★ **25 에서도 프리뷰**다(JEP 507 원시 타입 패턴).
- **패턴 전체에 이름을 붙일 수 없다** — `Point(int x, int y) p` 는 문법 에러다.
- ★ **컴포넌트가 `null` 이면**, 그 자리의 패턴이 **무조건 타입 패턴일 때만** 맞는다.
- 제네릭 `record` 는 **`Box<?>(...)`** 로 명시하거나, selector 타입에서 **추론**시킬 수 있다.
- `when` 가드는 `record` 패턴에도 그대로 붙는다.

### `null` 판정표 — 이 표가 이 주제의 값이다

컴포넌트 선언 타입이 `C`, 그 자리에 쓴 패턴이 `P` 일 때.

| `P` 의 모양 | 컴포넌트가 `null` 이면 | 예 (`C` = `Point`) |
|---|---|---|
| `C x` (무조건 타입 패턴) | **맞는다** (`x` 는 `null`) | `Typed(Point p)` |
| `C` 의 상위 타입 `S x` | **맞는다** | `Holder(Object o)` |
| `C` 의 하위 타입 `D x` (좁힘) | 안 맞는다 | `Holder(String s)` |
| `C(...)` (해체 패턴) | **안 맞는다** | `Typed(Point(var x, var y))` |
| `var x` | **맞는다** (무조건이므로) | `Typed(var p)` |

- 기억법: **"이름표만 붙이면 빈 칸도 된다. 열려고 하면 안 된다."**

## 어디서 틀리나

★ 이 주제의 값은 대부분 여기 있다. **아래 에러 메시지는 전부 JDK 21.0.5 의 javac 실출력이다.**

### 1. ★ `null` 컴포넌트에서 매칭이 조용히 실패한다

```text
Typed(null)       Typed(Point p)         = 맞음 p=null | Typed(Point(var x, var y)) = 안 맞음
```

- **예외도 경고도 없다.** `if` 면 그냥 `else` 로 가고, `switch` 면 다음 `case` 로 간다.
- 무조건 타입 패턴이면 맞고(그리고 **`p` 가 `null` 이다** — 그 다음 줄에서 NPE 가 날 수 있다),\
  해체 패턴이면 안 맞는다.
- 대응 둘: **컴포넌트에 `null` 을 허용하지 않거나**(컴팩트 생성자에서 막는다),\
  **한 겹 위로 받고 안에서 검사**한다.

### 2. ★ 완결한데 `MatchException` 이 난다

```text
f(R(A(1)))   = A 1
f(R(B("x"))) = B x
g(R(null))   = I null
Exception in thread "main" java.lang.MatchException
	at Ex.f(Ex.java:9)
	at Ex.main(Ex.java:26)
```

- `case R(A a)` + `case R(B b)` 가 **완결 판정을 받는데** `new R(null)` 에 안 맞는다.
- `MatchException` javadoc 이 **두 번째 사례**로 명시한 상황이다(「동작 방식」 (3)에 인용).
- 대응: `case R(I i)` 처럼 **한 겹 위로** 받거나, `default`/`case null` 을 둔다.
- ★ [**23번 주제**](../23-switch-pattern-matching/)의 `MatchException`(분리 컴파일)과 **원인이 다르다.**\
  이쪽은 **한 번에 컴파일하고 한 번에 실행해도** 난다.

### 3. 컴포넌트 개수가 안 맞는다

`Ex.java (24-e1)` · `Ex.java (24-e6)`

```text
Ex.java:5: error: incorrect number of nested patterns
        if (o instanceof Point(int x)) System.out.println(x);      // 컴포넌트가 둘인데 하나만
                         ^
  required: int,int
  found: int
1 error
```

```text
Ex.java:5: error: incorrect number of nested patterns
        if (o instanceof Point(var x, var y, var z)) System.out.println(x);   // 개수가 많다
                         ^
  required: int,int
  found: int,int,<none>
1 error
```

- 메시지가 **`required:` 와 `found:` 로 무엇이 어긋났는지** 그대로 말해 준다.
- 많을 때의 `found: int,int,<none>` 이 재미있다 — 셋째 자리에 대응할 컴포넌트가 **없다**는 표시다.
- ★ `record` 에 컴포넌트를 추가하면 **모든 `record` 패턴이 깨진다.** 이것은 **좋은 에러**다 —\
  생성자 호출과 달리 패턴은 위치로 매칭하므로, 빠뜨린 자리를 컴파일러가 전부 찾아 준다.

### 4. 패턴 전체에 이름을 붙이려 했다

`Ex.java (24-e4)`

```java
if (o instanceof Point(int x, int y) p) System.out.println(p);
```

```text
Ex.java:5: error: ')' expected
        if (o instanceof Point(int x, int y) p) System.out.println(p);       // 전체에 이름을 붙인다
                                            ^
Ex.java:5: error: not a statement
        if (o instanceof Point(int x, int y) p) System.out.println(p);       // 전체에 이름을 붙인다
                                             ^
Ex.java:5: error: ';' expected
        if (o instanceof Point(int x, int y) p) System.out.println(p);       // 전체에 이름을 붙인다
                                              ^
3 errors
```

- **파싱 에러 셋**이 쏟아진다. 문법 자체에 그 형태가 없다는 뜻이다.
- 다른 언어(스칼라의 `p @ Point(x, y)` 등)에 있는 기능이라 습관적으로 쓰기 쉽다.
- 대응: **둘 다 필요하면 칸마다 고른다.** `Line(Point from, Point(int bx, int by))` 처럼.\
  통째와 해체가 **같은 자리**에 동시에 필요하면 해체를 포기하고 접근자를 부른다.

### 5. `record` 가 아닌 것을 해체하려 했다

`Ex.java (24-e3)`

```java
static class Point { int x, y; }
if (o instanceof Point(int x, int y)) ...
```

```text
Ex.java:5: error: deconstruction patterns can only be applied to records, Point is not a record
        if (o instanceof Point(int x, int y)) System.out.println(x + y);     // record 가 아니다
                         ^
1 error
```

- 메시지가 이 문법의 **정식 이름**을 알려 준다 — **해체 패턴(deconstruction pattern)**.
- 일반 클래스에는 "컴포넌트가 무엇인가"라는 정보가 없다. `record` 만 그 목록을 갖는다.
- 사용자 정의 해체는 Java 21·25 기준으로 **없다.**

### 6. 컴포넌트 타입을 넓혀 받으려 했다 — ★ 25 에서도 프리뷰다

`Ex.java (24-e2)`

**JDK 21.0.5**

```text
Ex.java:5: error: incompatible types: pattern of type long is not applicable at int
        if (o instanceof Point(long x, long y)) System.out.println(x + y);   // int -> long
                               ^
Ex.java:5: error: incompatible types: pattern of type long is not applicable at int
        if (o instanceof Point(long x, long y)) System.out.println(x + y);   // int -> long
                                       ^
2 errors
```

**JDK 25.0.1 (기본)**

```text
Ex.java:5: error: primitive patterns are a preview feature and are disabled by default.
        if (o instanceof Point(long x, long y)) System.out.println(x + y);   // int -> long
                               ^
  (use --enable-preview to enable primitive patterns)
1 error
```

**JDK 25.0.1 + `--enable-preview`**

```text
Note: Ex.java uses preview features of Java SE 25.
Note: Recompile with -Xlint:preview for details.
3
```

- ★ **메시지가 판에 따라 다르다.** 21 은 "안 맞는다", 25 는 **"프리뷰라 꺼져 있다"**.\
  즉 **25 에는 기능이 들어와 있지만 아직 정식이 아니다**(JEP 507 원시 타입 패턴).
- `--enable-preview` 를 붙이면 컴파일되고 `3`(= 1 + 2)이 나온다.
- 실무에서는 **원시 타입 컴포넌트를 정확히 그 타입으로 받는다.** 넓히고 싶으면 꺼낸 뒤에 한다.

### 7. 컴포넌트 타입이 아예 안 맞는다

`Ex.java (24-e5)`

```java
if (o instanceof Point(String x, int y)) ...    // x 는 int 컴포넌트
```

```text
Ex.java:5: error: incompatible types: int cannot be converted to String
        if (o instanceof Point(String x, int y)) System.out.println(x + y);  // 컴포넌트 타입이 다르다
                               ^
1 error
```

- 6번과 메시지가 다르다 — 이쪽은 **아예 변환 불가**라서 평범한 타입 에러다.
- 참조 타입 컴포넌트는 **좁히는 것**이 허용된다(`Object` 컴포넌트를 `String` 으로).\
  원시 타입만 정확히 맞아야 한다.

### 8. ★ 17 에서 컴파일했다 — 파서가 문법을 모른다

**JDK 17.0.13** (`Ex.java (24-e0)` — `record` 패턴 한 줄짜리)

```text
Ex.java:5: error: ')' expected
        if (o instanceof Point(int x, int y)) System.out.println(x + y);
                              ^
Ex.java:5: error: -> expected
        if (o instanceof Point(int x, int y)) System.out.println(x + y);
                                            ^
2 errors
```

**JDK 21 의 `javac --release 20`** (같은 소스)

```text
Ex.java:5: error: deconstruction patterns are not supported in -source 20
        if (o instanceof Point(int x, int y)) System.out.println(x + y);
                              ^
  (use -source 21 or higher to enable deconstruction patterns)
1 error
```

- ★ **차이가 크다.** 17 의 javac 는 **문법을 아예 모른다** — `')' expected` 는 괄호를 닫으라는 소리다.\
  21 의 javac 는 문법을 알기 때문에 **정확한 안내**(`use -source 21 or higher`)를 준다.
- [**23번 주제**](../23-switch-pattern-matching/)의 패턴 `switch` 는 17 에서 **프리뷰로라도 있었다.**\
  `record` 패턴은 19 프리뷰라서 **17 에는 없다** — 그래서 파싱조차 안 된다.
- 큰 파일에서는 이 차이가 더 두드러진다 — `Ex.java (24-a)` 를 17 로 컴파일하면 **에러가 33개** 쏟아진다.\
  하나가 어긋나 그 뒤 전부가 깨진 것이지, 문제가 33곳인 것이 아니다.

## 구현 세부사항 대 언어 보장

| 무엇 | 어디에 속하나 | 근거 |
|---|---|---|
| `record` 패턴이 Java 21 부터 | **언어 보장** | `--release 20` 에러 `(use -source 21 or higher)` |
| `record` 에만 쓸 수 있다 | **언어 보장** | `deconstruction patterns can only be applied to records` |
| 컴포넌트 개수가 맞아야 한다 | **언어 보장** | `incorrect number of nested patterns` |
| 패턴 전체에 이름을 못 붙인다 | **언어 보장** | 파싱 에러 |
| ★ `null` 컴포넌트가 무조건 패턴에만 맞는다 | **언어 보장** | `MatchException` javadoc 이 사례로 명시 + 실행 |
| 완결한 중첩 패턴이 `null` 에 `MatchException` | **언어 보장** | javadoc 두 번째·세 번째 사례 |
| 접근자 예외가 `MatchException` 으로 감싸진다 | **API 보장** | javadoc 이 `cause` 까지 명시 |
| ★ 원시 타입 확대가 25 에서도 프리뷰 | **관찰(그 판에서)** | 25 의 `primitive patterns are a preview feature` |
| `var` 를 컴포넌트에 쓸 수 있다 | **언어 보장** | 컴파일되고 `int` 로 추론됐다 |
| 접근자 호출 순서(왼쪽 -> 오른쪽) | **구현 세부** | `javap` 로 관찰 |
| 무조건 패턴에 `instanceof` 가 없는 것 | **구현 세부** | javac 21 의 코드 생성. **결과(`null` 이 맞는다)는 보장** |
| 예외 테이블로 `MatchException` 을 만드는 방식 | **구현 세부** | 같은 이유 |
| 에러 메시지의 **문구 자체** | **구현 세부** | javac 의 것이다. **판마다 다르다**(6·8번이 실례) |

### 보장과 구현을 가르는 예 — 6번과 8번

```text
  같은 소스, 다른 판, 다른 메시지
  +--------------------------------------------------------------+
  | 24-e2 (int 컴포넌트를 long 패턴으로)                          |
  |   21: incompatible types: pattern of type long ...            |
  |   25: primitive patterns are a preview feature ...            |
  +--------------------------------------------------------------+
  | 24-e0 (record 패턴 한 줄)                                     |
  |   17: ')' expected  (파서가 모른다)                            |
  |   21 --release 20: deconstruction patterns are not supported  |
  +--------------------------------------------------------------+
    -> "이 에러가 난다" 를 버전 없이 적으면 반쪽이다
```

- ★ **에러 메시지를 근거로 쓸 때는 반드시 판을 적는다.** 이 주제가 그 필요성의 실례 둘을 갖고 있다.

## 언제 쓰고 언제 안 쓰나

**쓴다**

- **중첩 불변 데이터를 다룰 때** — JSON 트리, 수식 트리, 이벤트 페이로드.\
  `sealed` + `record` + `switch` 셋이 한 덩어리로 움직인다.
- **꺼낸 값을 바로 쓸 때** — 중간 변수 없이 이름이 생긴다.
- **구조와 값을 동시에 검사할 때** — 돌려 확인했다(`Ex.java (24-f)`, 21 · 25 동일).

```java
return switch (o) {
    case Point(int x, int y) when x == y                   -> "대각선 위의 점 " + x;
    case Point(int x, int y)                               -> "점 " + x + "," + y;
    case Line(Point(var ax, var ay), Point p) when ax == 0 -> "y축에서 시작하는 선, to=" + p;
    case Line(Point a, Point b)                            -> "선 " + a + "-" + b;
    default                                                -> "그 밖";
};
```

```text
대각선 위의 점 3
점 1,2
y축에서 시작하는 선, to=Point[x=2, y=2]
선 Point[x=1, y=5]-Point[x=2, y=2]
그 밖
```

  가드 안에서 **해체로 꺼낸 이름(`ax`)을 그대로 쓸 수 있다.** 같은 가지에서 통째(`Point p`)와 해체를 섞는 것도 된다.

**안 쓴다**

- **컴포넌트가 하나뿐이고 그대로 쓸 때** — `case Box(var v)` 보다 `case Box b` + `b.value()` 가 읽기 나을 수 있다.
- **3겹을 넘을 때** — 중간 타입으로 받아 메서드를 나눈다. 한 줄이 화면을 넘으면 이득이 사라진다.
- **컴포넌트에 `null` 이 들어올 수 있을 때** — 해체가 조용히 실패한다.\
  먼저 `record` 쪽에서 `null` 을 막는 것이 순서다.
- **`record` 가 아닐 때** — 방법이 없다. `record` 로 바꿀 수 없으면 접근자를 손으로 부른다.

**중간 지대**

- `var` 를 쓸지 타입을 적을지는 **컴포넌트 타입이 자명한가**로 판단한다.\
  `Point(var x, var y)` 는 자명하지만, 도메인 타입이 섞이면 적어 주는 편이 낫다.

## 핵심 문장

1. `record` 패턴은 **컴파일러가 접근자를 대신 불러 주는 것**이다. 마법이 없다 — `javap` 에 그대로 보인다.
2. 접근자 결과마다 **`instanceof` 가 따라붙느냐 아니냐**가 이 주제의 모든 `null` 규칙을 만든다.
3. ★ **컴포넌트 자리의 패턴이 그 컴포넌트 타입의 무조건 타입 패턴이면 `null` 도 맞는다.**\
   좁히는 타입 패턴이나 해체 패턴이면 **안 맞는다.**
4. 기억법: **"이름표만 붙이면 빈 칸도 된다. 열려고 하면 안 된다."**
5. ★ `case R(A a)` + `case R(B b)` 는 **완결 판정을 받는데 `new R(null)` 에 안 맞는다** — `MatchException`.
6. 그 `MatchException` 은 [**23번 주제**](../23-switch-pattern-matching/)의 것과 **원인이 다르다** — 분리 컴파일이 필요 없다.
7. **접근자가 던지면 `MatchException` 으로 감싸진다.** 원래 예외는 `cause` 에 들어간다.
8. `var` 는 **컴포넌트 자리에서는 쓸 수 있다** — `instanceof var v` 가 막히는 것과 대비된다.
9. **패턴 전체에 이름을 붙일 수 없다.** 통째와 해체가 동시에 필요하면 칸마다 고른다.
10. ★ 원시 타입 컴포넌트를 넓혀 받는 것은 **25 에서도 프리뷰**다.
11. 17 에서는 **파서가 문법을 모른다** — 에러가 `')' expected` 로 나온다.

## 관련 자료

- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 24번)
- [`../../../../../../history/java/java-21.md`](../../../../../../history/java/java-21.md) — **언제·왜 들어왔나**(JEP 440 확정, 두 번의 프리뷰).\
  여기는 **어떻게 쓰고 무엇을 못 하나**만 다룬다
- [`../14-records/`](../14-records/) — **`record` 자체가 정본이다.**\
  컴팩트 생성자, 얕은 불변, `equals`/`hashCode` 가 `invokedynamic` 으로 만들어지는 것,\
  접근자를 오버라이드할 때의 주의가 전부 거기 있다.\
  여기는 **그 `record` 를 패턴으로 해체할 때의 규칙**만 — 특히 **`null` 컴포넌트**
- [**23번 주제**](../23-switch-pattern-matching/)(`switch` 패턴 매칭) — **패턴 `switch` 의 뼈대가 정본.**\
  완결성·지배·`case null`·`when` 가드·`invokedynamic typeSwitch` 가 거기다.\
  여기는 **`case` 안에 해체가 들어왔을 때**만. `MatchException` 은 **양쪽에 다른 사례로** 나온다
- [**22번 주제**](../22-instanceof-type-patterns/)(`instanceof` 타입 패턴) — **타입 패턴과 흐름 스코프가 정본.**\
  `Point p` 가 어떤 물건인지는 거기가 답한다. 여기는 **그것이 컴포넌트 자리에 들어갔을 때**\
  (그리고 **`var` 가 거기서는 되는 것**)
- [`../15-sealed-classes/`](../15-sealed-classes/) — `sealed` + `record` 가 합타입이 되는 것.\
  **허용 목록 규칙은 거기**, 여기는 **그 합타입을 중첩으로 해체할 때 생기는 `null` 틈**만
- [**21번 주제**](../21-switch-statement-and-expression/)(`switch` 문과 식) — 화살표·`yield`·완결성의 기본. **문법 뼈대는 거기**
- [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) — `record` 의 `equals` 계약. **계약은 거기**
- [**19번 주제**](../19-type-erasure/)(타입 소거) — `Box<?>(String s)` 가 되고 `List<String>` 이 안 되는 이유. **소거 규칙은 거기**
- [**04번 주제**](../04-var-type-inference/)(`var`) — `var` 의 일반 규칙. **여기는 "컴포넌트 자리에서는 된다"까지**
- [**60번 주제**](../60-null-handling/)(`null` 다루기) — `Objects.requireNonNull` 로 막는 자리.\
  **`null` 정책의 정본은 거기**, 여기는 **막지 않았을 때 패턴에서 무슨 일이 나는가**만
- [`../../언어-특성/README.md`](../../언어-특성/README.md) — JIT·GC·메모리 모델. **이 주제와 겹치지 않는다**

## 용어 풀이

- **`record` 패턴 / 해체 패턴(deconstruction pattern)** — 컴포넌트를 꺼내면서 매칭하는 패턴. Java 21.
- **컴포넌트(component)** — `record` 선언 괄호 안의 각 칸. 접근자 메서드가 자동으로 생긴다.
- **중첩 패턴(nested pattern)** — 컴포넌트 자리에 또 패턴이 오는 것. 깊이 제한이 없다.
- **무조건 패턴(unconditional pattern)** — 그 자리의 **선언된 타입 전부**에 맞는 패턴.\
  ★ 컴포넌트 자리에서는 이것만 `null` 을 받는다.
- **`var` (패턴에서)** — 컴포넌트 선언에서 타입을 가져온다. `instanceof var v` 와 달리 **허용된다.**
- **`MatchException`** — 완결 판정된 매칭이 안 맞거나 **접근자가 던졌을 때** 나는 예외. Java 21.\
  접근자 예외는 `cause` 에 들어간다.
- **원시 타입 패턴(primitive pattern)** — `int` 컴포넌트를 `long` 으로 받는 것 등.\
  ★ **25 에서도 프리뷰**(JEP 507).
- **프리뷰 기능(preview feature)** — `--enable-preview` 로만 쓰는 기능. 정본 설명은 [**23번 주제**](../23-switch-pattern-matching/).

## 더 들어가면

- **`record` 패턴은 생성자의 거울이다.**\
  `new Point(1, 2)` 가 값 둘을 넣어 상자를 만들고, `case Point(int x, int y)` 가 그 상자를 열어 값 둘을 꺼낸다.\
  **같은 순서, 같은 개수**여서 눈으로 대응이 된다. 컴포넌트를 추가하면 양쪽이 같이 깨지는 것도 그래서다.
- **이 문법이 `record` 에만 되는 이유**는 `record` 만 **컴포넌트 목록을 클래스 파일에 갖기 때문**이다.\
  일반 클래스는 "무엇이 상태인가"를 언어가 모른다. 그 목록의 정본은 [`../14-records/`](../14-records/)다.
- **접근자가 진짜로 불린다는 사실**은 성능보다 **의미** 쪽에서 중요하다.\
  `record` 접근자에 방어 복사를 넣어 뒀다면 **패턴 매칭할 때마다 복사가 일어난다.**\
  그리고 던지면 `MatchException` 이 된다 — 「동작 방식」 (4).
- **완결성과 `null` 의 틈은 설계상 의도된 것**이다.\
  javadoc 이 사례로 적어 둘 만큼 알려진 구멍이고, 언어가 그것을 **`MatchException` 으로 드러내기로** 한 것이다.\
  조용히 `default` 로 보내지 않는다는 점에서 **무음 실패보다 낫다** — 다만 **테스트에 `null` 케이스가 있어야** 발견된다.
- **`record` 패턴이 못 하는 것 하나** — 같은 값을 두 이름으로 받을 수 없다.\
  `Point(int x, int y) p` 가 막히는 것이 그 표현이다(「어디서 틀리나」 4번).\
  통째가 필요하면 그 자리를 타입 패턴으로 받고, 컴포넌트는 안에서 접근자로 꺼낸다.
- **사용자 정의 해체(deconstructor)는 21·25 기준으로 없다.**\
  그래서 "패턴으로 열리게 하려면 `record` 로 만들어야 한다"가 설계 압력이 된다.\
  불변 데이터 홀더를 `record` 로 쓰는 이유가 하나 더 생긴 셈이다.
