# java/syntax/24 — `record` 패턴 (21): 중첩 해체 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러 메시지는 Temurin JDK 에서 **실제로 돌려 얻은 것**이다.\
> 기본은 **21.0.5**이고, 도는 프로그램은 **25.0.1** 에서도 돌렸다.\
> ★ **17.0.13 에서는 파싱조차 안 된다** — 그 에러는 9번에 실었다.\
> ★ **8번과 9번은 판마다 메시지가 달랐다.** 그 자리는 판을 명시했다.\
> 두 판에서 같았던 것은 "같았다"라고 **관찰로** 적었다 — 보장이 아니다.\
> 역어셈블은 `javap -c -p` 출력을 그대로 옮겼다.\
> javadoc 인용은 JDK 21.0.5 의 `lib/src.zip` 에서 복사한 것이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 한 줄이 무엇으로 펼쳐지나

**출력** (JDK 21.0.5 — 25.0.1 에서도 같았다)

```text
withoutRecordPattern = (1,2)-(3,4)
withRecordPattern    = (1,2)-(3,4)
```

**바이트코드** — `javap -c -p Ex.class`

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
      20: instanceof    #17                 // class Ex$Point
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
      ...
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

**왜 그런가**

- **컴파일러가 접근자를 대신 부른다.** 명령은 **`invokevirtual`** 이다 —\
  `Line.from()`(13) · `Line.to()`(30) · `Point.x()`(47) · `Point.y()` …
- ★ **접근자 결과마다 `instanceof` 가 따라붙는다**(20·37). 이것이 2번의 `null` 규칙 전부다.
- **예외 테이블**의 `from~to` 구간은 **접근자 호출 한 줄씩**이다(`13~16`·`30~33`·`47~50`·…).\
  그 구간에서 `Throwable` 이 나오면 `135` 로 가서 **`MatchException` 으로 감싸 다시 던진다.**
- **실무 주의**: **접근자가 진짜로 불린다.**\
  `record` 접근자에 방어 복사를 넣어 뒀다면 **패턴 매칭할 때마다 복사가 일어나고**,\
  접근자가 던지면 `MatchException` 이 된다(4번). 정본은 [`../14-records/`](../14-records/).

### 2. ★ `null` 컴포넌트 — 네 가지

**출력** (`Ex.java (24-c)`, JDK 21.0.5 — 25.0.1 에서도 같았다)

```text
--- Holder
Holder("s")  Holder(Object o)  = 맞음 o=s | Holder(String s) = 맞음 s=s
Holder(null) Holder(Object o)  = 맞음 o=null | Holder(String s) = 안 맞음
Holder(42)   Holder(Object o)  = 맞음 o=42 | Holder(String s) = 안 맞음
--- Typed
Typed(Point(1,2)) Typed(Point p)         = 맞음 p=Point[x=1, y=2] | Typed(Point(var x, var y)) = 맞음 1,2
Typed(null)       Typed(Point p)         = 맞음 p=null | Typed(Point(var x, var y)) = 안 맞음
```

| | 결과 |
|---|---|
| (a) `Holder(null) instanceof Holder(Object o)` | **`true`** — `o` 는 **`null`** |
| (b) `Holder(null) instanceof Holder(String s)` | `false` |
| (c) `Typed(null) instanceof Typed(Point p)` | **`true`** — `p` 는 **`null`** |
| (d) `Typed(null) instanceof Typed(Point(var x, var y))` | `false` |

**왜 그런가**

- ★ 한 문장: **"컴포넌트 자리의 패턴이 그 컴포넌트 타입에 대한 무조건 타입 패턴이면 `null` 도 맞고,\
  좁히는 타입 패턴이나 해체 패턴이면 안 맞는다."**
- (a) 컴포넌트 타입 `Object` = 패턴 타입 `Object` → 무조건 → 맞는다.
- (b) 컴포넌트 타입 `Object` 를 `String` 으로 **좁힌다** → 조건부 → `null` 은 안 맞는다.
- (c) 컴포넌트 타입 `Point` = 패턴 타입 `Point` → 무조건 → 맞는다.
- (d) **해체 패턴**이므로 상자를 열어야 한다 → `null` 은 못 연다 → 안 맞는다.

**바이트코드의 차이** (`Ex.java (24-d)`)

```text
  static boolean unconditional(Ex$Typed);          <- Typed(Point p)
       ...
      10: invokevirtual #9                  // Method Ex$Typed.p:()LEx$Point;
      13: astore_3
      14: aload_3
      15: astore_1                          <- 바로 저장. instanceof 가 없다
      16: iconst_1
```

```text
  static boolean deconstruct(Ex$Typed);            <- Typed(Point(var x, var y))
       ...
      12: invokevirtual #9                  // Method Ex$Typed.p:()LEx$Point;
      15: astore        5
      17: aload         5
      19: instanceof    #24                 // class Ex$Point          <- 검사가 있다
      22: ifeq          50
```

```text
unconditional(Typed(null)) = true
deconstruct(Typed(null))   = false
```

- ★ **차이는 `instanceof` 한 줄**이다. 무조건 패턴에는 없고 해체 패턴에는 있다.
- `null instanceof Point` 가 `false` 이므로 해체 쪽에서 매칭이 깨진다.
- 기억법: **"이름표만 붙이면 빈 칸도 된다. 열려고 하면 안 된다."**

### 3. ★ 완결한데 안 맞는다

**출력** (`Ex.java (24-e)`, JDK 21.0.5 — 25.0.1 에서도 같았다)

```text
f(R(A(1)))   = A 1
f(R(B("x"))) = B x
g(R(null))   = I null
Exception in thread "main" java.lang.MatchException
	at Ex.f(Ex.java:9)
	at Ex.main(Ex.java:26)
```

**왜 그런가**

- `f` 는 `default` 가 없는데 **컴파일된다.** `I` 가 `sealed` 이고 `A`·`B` 를 다 덮었기 때문이다.
- `f(new R(new A(1)))` = `"A 1"`, `g(new R(null))` = `"I null"`, `f(new R(null))` = **`java.lang.MatchException`**.
- `g` 가 되는 이유는 2번 그대로다 — `case R(I i)` 의 `I i` 는 컴포넌트 타입 `I` 에 대한 **무조건 패턴**이다.
- `MatchException` javadoc 이 이것을 **두 번째 사례**로 예고한다 (JDK 21.0.5 `src.zip`).

```text
 *     <li>{@code null} values and nested patterns involving sealed classes. If,
 *         for example, an interface {@code I} is {@code sealed} with two permitted
 *         subclasses {@code A} and {@code B}, and a record class {@code R} has a
 *         single component of type {@code I}, then the two record patterns {@code
 *         R(A a)} and {@code R(B b)} together are considered to be exhaustive for
 *         the type {@code R}, but neither of these patterns will match against the
 *         result of {@code new R(null)}.</li>
```

- javadoc 이 쓴 이름(`I`·`A`·`B`·`R`)을 그대로 써서 만든 프로그램이다.
- ★ **[23번 주제](../23-switch-pattern-matching/)의 `MatchException` 과 원인이 다르다.**

```text
  23번의 MatchException                   24번의 MatchException
  +-----------------------------+        +-----------------------------+
  | 원인: 컴파일 뒤 계층이 바뀜   |        | 원인: null 컴포넌트          |
  | 재현: 2단계 컴파일이 필요     |        | 재현: 한 번에 컴파일해도 난다 |
  | 방어: 같이 빌드·배포          |        | 방어: 컴포넌트에 null 금지    |
  |                             |        |      또는 한 겹 위로 받기     |
  +-----------------------------+        +-----------------------------+
```

### 4. 접근자가 던지면

**출력** (`Ex.java (24-d)`, JDK 21.0.5 — 25.0.1 에서도 같았다)

```text
Exception in thread "main" java.lang.MatchException: java.lang.IllegalStateException: 접근자가 터졌다
	at Ex.main(Ex.java:21)
Caused by: java.lang.IllegalStateException: 접근자가 터졌다
	at Ex$Bad.v(Ex.java:13)
	... 1 more
```

**왜 그런가**

- 던져지는 것은 **`MatchException`** 이다. `IllegalStateException` 이 아니다.
- 원래 예외는 **`cause`** 로 들어간다 — 스택의 `Caused by:` 가 그것이다.
- javadoc 이 그렇게 명시했다 (JDK 21.0.5 `src.zip`).

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

- 이것을 만드는 장치는 1번의 **예외 테이블**이다. 접근자 호출 구간마다 `Throwable` 을 잡아 다시 던진다.
- **실무 규칙**: **`record` 접근자를 오버라이드해 일을 시키지 마라.**\
  `record` 컴포넌트는 "그냥 값"이어야 한다. 예외를 던지면 호출부에서 **원인이 한 겹 가려진다.**\
  `record` 의 설계 원칙은 [`../14-records/`](../14-records/)가 정본이다.

### 5. `var` 와 제네릭

**출력** (`Ex.java (24-b)`, JDK 21.0.5 — 25.0.1 에서도 같았다)

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

**왜 그런가**

- (a) `(x + y)` 가 **`7`** 이다 — 문자열 연결(`"34"`)이 아니라 **덧셈**이다.\
  즉 `var x` 가 **`int`** 로 추론됐다. 타입을 **컴포넌트 선언**에서 가져오기 때문이다.
- (b) **`Box<?>(String s)` 는 된다.** 와일드카드는 런타임에 검사할 것이 없다.\
  ★ **`Box<String>(String s)` 는 안 된다** — 돌려 확인했다(`Ex.java (24-g)`, 21 · 25 동일).

```text
Ex.java:5: error: Object cannot be safely cast to Box<String>
            case Box<String>(String s) -> "문자열 상자 " + s;
                 ^
1 error
```

- [**22번 주제**](../22-instanceof-type-patterns/)의 `o instanceof List<String> l` 과 **같은 에러**다.\
  selector 가 `Object` 라 `Box<String>` 인지 런타임에 확인할 방법이 없다. 소거 때문이다.
- (c) **생략하면 추론된다.** `inferred(Box<String> b)` 에서 `b instanceof Box(String s)` 가 통과했다.\
  selector 타입이 `Box<String>` 이라 타입 인자가 이미 알려져 있다.
- **`instanceof var v` 가 막히는 이유**: 그 자리에는 **검사할 타입이 필요한데** `var` 는 타입을 안 준다.\
  **`Point(var x, var y)` 가 되는 이유**: 컴포넌트 **선언**이 타입을 알려 준다. 검사할 것이 이미 정해져 있다.

```text
  var 가 쓰일 수 있는 자리
  +--------------------------------------------------------------+
  | instanceof var v          X   무엇을 검사할지가 없다 (22번)    |
  | Point(var x, var y)       O   컴포넌트 선언이 타입을 준다      |
  | case Box<?>(var v)        O   같은 이유                       |
  +--------------------------------------------------------------+
```

### 6. 중첩과 이름

**출력** — (a)(b) (`Ex.java (24-a)`, JDK 21.0.5 — 25.0.1 에서도 같았다)

```text
deep(Colored)        = 빨강 선 (1,2)-(3,4)
deep(Line)           = 선 Point[x=1, y=2]-Point[x=3, y=4]
deep(Point)          = 점 9,9
deep("x")            = 그 밖
halfway(Line)        = from=Point[x=1, y=2] to=(3,4)
```

**출력** — (c) (`Ex.java (24-e4)`)

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

**왜 그런가**

- (a)는 **3겹**이다. `Colored( Line( Point(...) , Point(...) ), String color )`.\
  **깊이 제한은 없다.**

```text
  Colored( Line( Point(var ax, var ay), Point(var bx, var by) ), String color )
     |       |      |                     |                       |
     |       |      +-- 3겹              +-- 3겹                 +-- 1겹
     |       +-- 2겹
     +-- 1겹 (selector 자리)
```

- (b) **된다.** `Line(Point from, Point(int bx, int by))` 처럼 **칸마다 다르게** 쓸 수 있다.
- (c)는 **파싱 에러 셋**이다. 문법에 그 형태가 아예 없다.\
  다른 언어(스칼라의 `p @ Point(x, y)` 등)에 있어서 습관적으로 쓰기 쉽다.
- **같은 자리에 통째와 해체가 동시에 필요하면**: 해체를 포기하고 **타입 패턴으로 받은 뒤 접근자를 부른다.**\
  `case Line(Point from, Point to) -> ... from.x() ...` 처럼.

### 7. 개수와 타입이 안 맞으면

**출력** — (a) 모자람

```text
Ex.java:5: error: incorrect number of nested patterns
        if (o instanceof Point(int x)) System.out.println(x);      // 컴포넌트가 둘인데 하나만
                         ^
  required: int,int
  found: int
1 error
```

**출력** — (b) 남음

```text
Ex.java:5: error: incorrect number of nested patterns
        if (o instanceof Point(var x, var y, var z)) System.out.println(x);   // 개수가 많다
                         ^
  required: int,int
  found: int,int,<none>
1 error
```

**출력** — (c) 타입 불일치

```text
Ex.java:5: error: incompatible types: int cannot be converted to String
        if (o instanceof Point(String x, int y)) System.out.println(x + y);  // 컴포넌트 타입이 다르다
                               ^
1 error
```

**출력** — (d) `record` 가 아님

```text
Ex.java:5: error: deconstruction patterns can only be applied to records, Point is not a record
        if (o instanceof Point(int x, int y)) System.out.println(x + y);     // record 가 아니다
                         ^
1 error
```

**왜 그런가**

- (a) `required: int,int` / `found: int` — 컴포넌트 선언과 패턴을 **나란히 찍어 준다.**
- (b) `found: int,int,<none>` — 셋째 자리에 **대응할 컴포넌트가 없다**는 표시가 `<none>` 이다.
- (d) 메시지가 이 문법의 **정식 이름**을 알려 준다 — **해체 패턴(deconstruction pattern)**.\
  일반 클래스에는 "무엇이 컴포넌트인가"라는 목록이 없다. `record` 만 그것을 갖는다.
- ★ **`record` 에 컴포넌트를 추가하면 기존 `record` 패턴이 전부 깨진다.** 그리고 **그것이 좋은 일이다.**\
  패턴은 **위치로** 매칭하므로, 새 컴포넌트를 어디서 처리할지 컴파일러가 **모든 자리를 찾아 준다.**\
  생성자 호출도 같이 깨지므로, 변경의 파급이 전부 컴파일 에러로 드러난다.

### 8. ★ 원시 타입을 넓혀 받으려 하면

**출력** — JDK 21.0.5

```text
Ex.java:5: error: incompatible types: pattern of type long is not applicable at int
        if (o instanceof Point(long x, long y)) System.out.println(x + y);   // int -> long
                               ^
Ex.java:5: error: incompatible types: pattern of type long is not applicable at int
        if (o instanceof Point(long x, long y)) System.out.println(x + y);   // int -> long
                                       ^
2 errors
```

**출력** — JDK 25.0.1 (기본)

```text
Ex.java:5: error: primitive patterns are a preview feature and are disabled by default.
        if (o instanceof Point(long x, long y)) System.out.println(x + y);   // int -> long
                               ^
  (use --enable-preview to enable primitive patterns)
1 error
```

**출력** — JDK 25.0.1 + `--enable-preview`

```text
Note: Ex.java uses preview features of Java SE 25.
Note: Recompile with -Xlint:preview for details.
3
```

**왜 그런가**

- JDK 21 은 에러가 **2개**다 — `x` 와 `y` 각각. "그런 패턴은 안 맞는다"는 평범한 타입 에러다.
- JDK 25 는 에러가 **1개**이고 문구가 전혀 다르다 — **"프리뷰 기능인데 꺼져 있다".**\
  즉 **25 에는 기능이 들어와 있지만 아직 정식이 아니다**(원시 타입 패턴).
- `--enable-preview` 를 붙이면 컴파일되고 **`3`**(= 1 + 2)이 나온다. 확대가 실제로 동작한다.
- ★ **문서 작성 규칙**: **에러 메시지를 근거로 쓸 때는 반드시 판을 적는다.**\
  "이 코드는 이 에러가 난다"를 버전 없이 적으면, 판이 바뀌는 순간 **문서가 거짓이 된다.**\
  이 주제는 그 실례를 둘 갖고 있다 — 이 문항과 9번.

### 9. ★ 17 에서 컴파일하면

**출력** — JDK 17.0.13 의 javac (`Ex.java (24-e0)`)

```text
Ex.java:5: error: ')' expected
        if (o instanceof Point(int x, int y)) System.out.println(x + y);
                              ^
Ex.java:5: error: -> expected
        if (o instanceof Point(int x, int y)) System.out.println(x + y);
                                            ^
2 errors
```

**출력** — JDK 21 의 `javac --release 20`

```text
Ex.java:5: error: deconstruction patterns are not supported in -source 20
        if (o instanceof Point(int x, int y)) System.out.println(x + y);
                              ^
  (use -source 21 or higher to enable deconstruction patterns)
1 error
```

**왜 그런가**

- ★ **17 의 javac 는 문법을 아예 모른다.** `')' expected` 는 "괄호를 닫으라"는 일반 파싱 에러다.\
  `instanceof Point` 까지 읽고 그 뒤의 `(` 를 이해하지 못한 것이다.
- **21 의 javac 는 문법을 안다.** 그래서 파싱은 되고 **버전 안내**를 준다.
- 이유: `record` 패턴은 **19 프리뷰**로 들어왔다. **17 에는 아예 없다.**\
  반면 [**23번 주제**](../23-switch-pattern-matching/)의 패턴 `switch` 는 **17 프리뷰**로 있었다 —\
  그래서 17 에서도 `patterns in switch statements are a preview feature and are disabled by default.` 라는\
  **기능을 아는 메시지**가 나왔다.

```text
  17 에서 컴파일했을 때
  +--------------------------------------------------------------+
  | 패턴 switch (17 프리뷰)  -> "preview feature, disabled"       |
  |                            (--enable-preview 로 쓸 수 있다)   |
  | record 패턴 (19 프리뷰)  -> "')' expected"                    |
  |                            (파서가 모른다. 방법이 없다)        |
  +--------------------------------------------------------------+
```

- 큰 파일에서는 이 차이가 더 크다 — `Ex.java (24-a)` 를 17 로 컴파일하면 **에러가 33개** 쏟아진다.\
  하나가 어긋나 그 뒤 전부가 깨진 것이지, 문제가 33곳인 것이 아니다.

### 10. 가드와 함께

**출력** (`Ex.java (24-f)`, JDK 21.0.5 — 25.0.1 에서도 같았다)

```text
대각선 위의 점 3
점 1,2
y축에서 시작하는 선, to=Point[x=2, y=2]
선 Point[x=1, y=5]-Point[x=2, y=2]
그 밖
```

**왜 그런가**

- `f(new Point(3, 3))` = `"대각선 위의 점 3"`, `f(new Point(1, 2))` = `"점 1,2"`.
- ★ **가드 안에서 해체로 꺼낸 이름을 쓸 수 있다.** `when x == y` 의 `x`·`y` 가 그 예이고,\
  `Line(Point(var ax, var ay), Point p) when ax == 0` 의 `ax` 도 그렇다.
- **한 가지 안에서 통째와 해체를 섞을 수 있다** — 위 세 번째 `case` 가 `Point p`(통째)와 해체를 같이 쓴다.
- **가드 붙은 가지를 뒤로 옮기면 지배 에러**다 — 돌려 확인했다(`Ex.java (24-e7)`).

```text
Ex.java:6: error: this case label is dominated by a preceding case label
            case Point(int x, int y) when x == y -> "대각선 위의 점 " + x;
                 ^
1 error
```

- 앞의 무가드 `case Point(int x, int y)` 가 모든 `Point` 를 먼저 가져가기 때문이다.\
  지배 규칙의 정본은 [**23번 주제**](../23-switch-pattern-matching/)다 — **`record` 패턴에도 그대로 적용된다.**
- 순서 규칙: **가드 붙은 것을 먼저, 무가드를 뒤에.**

### 11. 언제 쓰고 언제 안 쓰나

**왜 그런가**

- **안 쓰는 편이 나은 경우 넷.**

| 경우 | 대신 |
|---|---|
| 컴포넌트가 하나뿐이고 그대로 쓸 때 | `case Box b` + `b.value()` 가 읽기 나을 수 있다 |
| 3겹을 넘을 때 | 중간 타입으로 받아 메서드를 나눈다 |
| 컴포넌트에 `null` 이 들어올 수 있을 때 | 먼저 `record` 쪽에서 막는다 |
| `record` 가 아닐 때 | 방법이 없다 — 접근자를 손으로 부른다 |

- **컴포넌트에 `null` 이 들어올 수 있으면 먼저 `record` 쪽에서 막는다.**\
  컴팩트 생성자에서 `Objects.requireNonNull(x)` 를 부르는 형태이고,\
  그 문법은 [`../14-records/`](../14-records/)가, `null` 정책 전반은 [**60번 주제**](../60-null-handling/)가 정본이다.
- **사용자 정의 해체(deconstructor)는 21·25 에 없다.**\
  `record` 만 컴포넌트 목록을 갖기 때문에 그것만 열린다.
- ★ 그 사실이 주는 **설계 압력**: **"패턴으로 열리게 하려면 `record` 로 만들어야 한다."**\
  불변 데이터 홀더를 `record` 로 쓸 이유가 하나 더 생긴 셈이다.\
  반대로 가변 상태나 상속이 필요하면 `record` 가 아니고, 그러면 이 문법을 못 쓴다.

### 12. 정본 경계

**왜 그런가**

| 주제 | 그쪽이 다루는 것 | 여기가 다루는 것 |
|---|---|---|
| [**14번**](../14-records/) `record` | 컴팩트 생성자 · 얕은 불변 · `equals` 가 `invokedynamic` 으로 만들어지는 것 · 접근자 오버라이드 주의 | **그 `record` 를 해체할 때의 규칙** — 특히 `null` 컴포넌트 |
| [**22번**](../22-instanceof-type-patterns/) 타입 패턴 | `Point p` 라는 패턴 자체 · 흐름 스코프 · `var` 금지 | 그것이 **컴포넌트 자리**에 들어갔을 때 (그리고 거기서는 `var` 가 되는 것) |
| [**23번**](../23-switch-pattern-matching/) 패턴 `switch` | 완결성 · 지배 · `case null` · `when` · `typeSwitch` | **`case` 안에 해체가 들어왔을 때**만 |
| [**15번**](../15-sealed-classes/) `sealed` | 허용 목록 규칙 · `PermittedSubclasses` · `non-sealed` | **그 합타입을 중첩으로 해체할 때 생기는 `null` 틈** |

- **`MatchException` 이 두 주제에 다른 사례로 나온다.**

| | 23번 | 24번 |
|---|---|---|
| javadoc 사례 | 첫째 — 분리 컴파일 | 둘째·셋째 — `null` 과 중첩 패턴 / 넷째 — 접근자 예외 |
| 재현 방법 | 2단계 컴파일 | 한 번에 컴파일·실행 |
| 방어 | 같이 빌드·배포 | 컴포넌트 `null` 금지, 한 겹 위로 받기 |

- **무조건 패턴에 `instanceof` 가 없다는 것은 구현 세부**다 — javac 21 이 그렇게 만들 뿐이다.\
  ★ 그러나 **그 결과(`null` 컴포넌트가 무조건 패턴에 맞는다)는 언어 보장**이다.\
  `MatchException` javadoc 이 그 동작을 사례로 적어 두었기 때문이다.
- ★ **판마다 메시지가 달랐던 자리 둘**.

```text
  +--------------------------------------------------------------+
  | 24-e2 (int 컴포넌트를 long 패턴으로)                          |
  |   21: incompatible types: pattern of type long ...            |
  |   25: primitive patterns are a preview feature ...            |
  +--------------------------------------------------------------+
  | 24-e0 (record 패턴 한 줄)                                     |
  |   17: ')' expected  (파서가 모른다)                            |
  |   21 --release 20: deconstruction patterns are not supported  |
  +--------------------------------------------------------------+
```

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Ex (24-a)` | 타입 패턴 대 `record` 패턴 · 3겹 중첩 · 한쪽만 해체 | 21 · 25 (출력 동일) |
| `Ex (24-a)` + `javap -c -p` | 접근자 `invokevirtual` · 결과마다 `instanceof` · **접근자 구간마다 예외 테이블** | 21 |
| `Ex (24-a)` JDK 17 javac | 파싱 에러 **33개** | 17 |
| `Ex (24-b)` | `var` 컴포넌트가 `int` 로 추론(`x+y=7`) · `Box<?>(...)` · 타입 인자 추론 · `Pair(var,var)` 로 완결 | 21 · 25 (출력 동일) |
| `Ex (24-c)` | ★ `null` 컴포넌트 네 조합 — 무조건은 맞고 좁힘·해체는 안 맞는다 | 21 · 25 (출력 동일) |
| `Ex (24-d)` | ★ 무조건에는 `instanceof` 없음 / 해체에는 있음 (`javap`) · 접근자 예외 -> `MatchException` + `cause` | 21 · 25 (출력 동일) |
| `Ex (24-e)` | ★ `case R(A a)`+`case R(B b)` 가 완결인데 `new R(null)` 에 **`MatchException`** · `case R(I i)` 는 통과 | 21 · 25 (출력 동일) |
| `Ex (24-f)` | `when` 가드 + `record` 패턴 · 가드에서 해체 이름 사용 · 통째와 해체 섞기 | 21 · 25 (출력 동일) |
| `Ex (24-e0)` | ★ **17 은 `')' expected`**, 21 `--release 20` 은 `deconstruction patterns are not supported` | 17 · 21 (**메시지 다름**) |
| `Ex (24-e1)` | 컴포넌트 모자람 -> `incorrect number of nested patterns` (`required: int,int` / `found: int`) | 21 |
| `Ex (24-e2)` | ★ 원시 확대 — **21 은 타입 에러 2개, 25 는 프리뷰 안내 1개**, 25 `--enable-preview` 는 통과(`3`) | 21 · 25 (**메시지 다름**) |
| `Ex (24-e3)` | `record` 아님 -> `deconstruction patterns can only be applied to records` | 21 |
| `Ex (24-e4)` | 패턴 전체에 이름 -> 파싱 에러 3개 | 21 |
| `Ex (24-e5)` | 컴포넌트 타입 불일치 -> `int cannot be converted to String` | 21 |
| `Ex (24-e6)` | 컴포넌트 남음 -> `found: int,int,<none>` | 21 |
| `Ex (24-e7)` | 무가드 뒤의 가드 -> `dominated by a preceding case label` | 21 |
| `Ex (24-g)` | `Box<String>(String s)` -> `Object cannot be safely cast to Box<String>` | 21 · 25 (동일) |
| `src.zip` (`MatchException.java`) | `@since 21` · 네 사례 중 **둘째·셋째·넷째** 인용 | 21.0.5 |

**합계** — 프로그램 17개 · `javac` 30회 · `java` 14회 · `javap` 2회(메서드 3개 덤프).

**구현 의존 항목** — 버전이 오르면 다시 돌려야 하는 것

- ★ **원시 타입 확대**는 25 에서 **프리뷰**였다. 다음 LTS 에서 정식이 되면 8번의 답이 바뀐다.
- ★ **에러 메시지가 판마다 달랐다** — 8번(21 대 25)과 9번(17 대 21)이 실례다.\
  이 주제의 에러를 인용할 때는 **판을 반드시 적는다.**
- **무조건 패턴에 `instanceof` 가 없는 것 · 접근자 호출 순서 · 예외 테이블 구간**은\
  javac 21 의 코드 생성 방식이다. **결과(`null` 규칙·`MatchException` 감싸기)는 javadoc 이 보장한다.**
- **`javap` 의 오프셋 숫자와 상수 풀 번호**는 컴파일할 때마다 달라질 수 있다.
- 두 판(21·25)에서 출력이 같았던 것은 **관찰**이다.\
  [**21번 주제**](../21-switch-statement-and-expression/)에서 **출력이 같은데 바이트코드가 달랐던 실례**를 봤으므로,\
  이 주제에서도 "같았다"를 보장으로 읽지 않는다.
