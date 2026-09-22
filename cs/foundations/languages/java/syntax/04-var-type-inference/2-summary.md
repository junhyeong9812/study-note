# java/syntax/04 — `var` 지역 변수 타입 추론 (10+) — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [JLS SE 21 §14.4 Local Variable Declarations](https://docs.oracle.com/javase/specs/jls/se21/html/jls-14.html#jls-14.4) · [§4.10.4 Least Upper Bound](https://docs.oracle.com/javase/specs/jls/se21/html/jls-4.html#jls-4.10.4) · [§6.1 Declarations](https://docs.oracle.com/javase/specs/jls/se21/html/jls-6.html#jls-6.1) · [JEP 286 Local-Variable Type Inference](https://openjdk.org/jeps/286) · [JEP 323 Local-Variable Syntax for Lambda Parameters](https://openjdk.org/jeps/323).
> **실행 검증** — 이 문서의 모든 출력·컴파일 에러·바이트코드는 Temurin **JDK 21.0.5** 에서 실제로 돌려 얻은 것이다.\
> 실행 프로그램 `Ex.java (04-a)` 는 **17.0.13 · 21.0.5 · 25.0.1** 세 곳에서 돌려 **출력이 한 글자도 다르지 않았다**.\
> 컴파일 에러 14종(`04-c1`·`04-c2`·`04-e1`~`04-e5`·`04-f1`·`04-f2`·`04-f4`·`04-h`·`04-i`·`04-j`·`04-k`)도 세 JDK 에서 **바이트 단위로 같았다**.\
> 다만 **"세 곳에서 같았다"는 관찰이지 보장이 아니다** — 보장은 JLS·JEP 인용으로만 적었다.
> **버전** — `var` 지역 변수는 **Java 10**(JEP 286). 람다 파라미터의 `var` 는 **Java 11**(JEP 323).\
> 17·21·25 에서 규칙이 같았고, `--release 10` 으로 내리면 람다 파라미터 쪽만 거부됐다(실측, 「구현 세부사항 대 언어 보장」).
> **범위** — 도입 맥락과 설계 논쟁은 [`../../../../../../history/java/java-10.md`](../../../../../../history/java/java-10.md) 가 정본이다.\
> 여기는 「**그래서 어디에 쓰고 어디서 컴파일이 막히나**」만 다룬다.
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**`var` 는 "이름표를 컴파일러에게 대신 쓰게 하는 것"이다. 이름표 자체를 떼는 게 아니다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 상자에 붙이는 이름표 | 변수의 **정적 타입**(컴파일러가 아는 타입) |
| 이름표를 **내가** 손으로 쓴다 | `String s = "hi";` |
| 이름표를 **컴파일러가** 대신 쓴다 | `var s = "hi";` |
| 이름표를 쓰려면 봐야 하는 것 | **초기화식**(`=` 오른쪽) |
| 이름표를 못 쓰는 상황 | 오른쪽을 봐도 타입이 안 정해지는 경우(`null`·람다·`{1,2}`) |
| 창고에 실제로 붙어 나가는 이름표 | 클래스 파일의 `LocalVariableTable` 항목 |

- `var` 를 써도 **이름표는 반드시 붙는다.** 누가 쓰느냐만 달라진다.
- 컴파일러는 이름표를 쓰려고 **오른쪽만 본다.** 왼쪽에는 아무 정보가 없기 때문이다.
- 그래서 오른쪽이 `null` 이면 못 쓴다 — `null` 은 모든 타입이 될 수 있어서 하나로 못 정한다.
- 이름표가 정해지고 나면 **그다음은 완전히 평범한 변수**다.\
  다른 타입을 대입하면 그대로 컴파일 에러다. 동적 타입이 아니다.

```text
   var i = 1;                          int i = 1;
        |                                   |
   컴파일러가 오른쪽을 본다              내가 왼쪽에 적는다
        |                                   |
        v                                   v
   이름표: int                          이름표: int
        |                                   |
        +-----------------+-----------------+
                          |
                          v
        클래스 파일에는 둘이 완전히 같은 것으로 들어간다
        LocalVariableTable:  Slot 0  Name i  Signature I
```

**똑같은 구조로** 자바가 동작한다: 이름표 = 정적 타입, 오른쪽을 본다 = 초기화식에서 추론, 클래스 파일 = `javap` 로 눈으로 확인 가능.

실무에서 이게 헷갈리는 자리는 **"`var` 를 쓰면 타입이 사라진다"고 믿는 코드**다.\
`var list = new ArrayList<>();` 가 `ArrayList<Object>` 가 되어 아무거나 들어가는 것이 그 대표다 —
타입이 사라진 게 아니라 **컴파일러가 `Object` 라고 써 버린 것**이다.

> **타입 추론(type inference)** — 프로그래머가 안 적은 타입을 컴파일러가 문맥에서 계산해 채워 넣는 것.\
> 예: `var s = "hi";` 에서 컴파일러가 `"hi"` 를 보고 `String` 이라고 결정하는 것.

> **정적 타입(static type)** — 컴파일러가 그 식·변수에 대해 아는 타입. 실행 중에 바뀌지 않는다.\
> 예: `Object o = "hi";` 에서 `o` 의 정적 타입은 `Object` 이고, 실제 객체의 클래스(`String`)는 런타임 타입이다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. `var` 를 쓸 수 있는 자리와 **못 쓰는 자리**는 정확히 어디까지인가 — 그리고 각각 어떤 에러가 나는가.
2. **추론된 타입이 무엇인지** 내 머리가 아니라 도구로 확인하려면 어떻게 하나.
3. `var` 가 **런타임에 무엇을 바꾸는가** — 아무것도 안 바꾼다면 그것을 어떻게 증명하나.

## 동작 방식

### (1) 컴파일러는 오른쪽만 본다

**언제 쓰나** — `var` 를 쓴 모든 줄. 이 그림 하나가 나머지 규칙 전부를 낳는다.

```text
  var  x  =  <초기화식> ;
   |   |        |
   |   |        +---- 컴파일러가 보는 유일한 정보
   |   +------------- 이름. 타입 정보가 없다
   +----------------- "네가 채워라" 라는 표시

     초기화식의 타입을 계산한다
             |
             v
     +-------+--------+
     |                |
   하나로 정해진다   안 정해진다
     |                |
     v                v
   그 타입으로      error: cannot infer type
   선언이 완성된다   for local variable x
                    (괄호 안에 이유가 한 줄 더 나온다)
```

그림 해설 (한 단계씩):

- `var` 는 **왼쪽에 아무 정보가 없다**는 선언이다. 그래서 오른쪽이 없으면 시작 자체가 안 된다.
- 초기화식 하나가 **한 타입으로 확정**되면 그 타입이 그대로 선언 타입이 된다.
- 확정이 안 되는 경우는 셋이다 — 값이 `null` 이라 후보가 무한, **대상 타입이 있어야 결정되는 식**(람다·메서드 참조·배열 초기화 축약), 자기 자신을 참조.
- ★ **확정된 뒤에는 그냥 그 타입이다.** 나중에 다른 타입을 대입할 수 없다.

비용 — 컴파일 타임에만 든다. 런타임 비용은 **0**이다((6) 에서 바이트코드로 확인한다).

### (2) 무엇으로 추론되는지 — 눈으로 확인하는 세 가지 방법

**언제 쓰나** — `var` 를 쓴 줄이 뭘로 추론됐는지 확신이 안 설 때. **추측하지 말고 확인한다.**

★ 방법 1 — **일부러 `Void` 에 대입해 컴파일 에러를 뽑는다.** 가장 빠르다.

```java
var x     = 1;
var y     = 1L;
var s     = "hi";
Void v1 = x;   Void v2 = y;   Void v3 = s;   // 일부러 틀린 대입
```

**컴파일 에러** (`Ex.java (04-c1)`, JDK 21.0.5 — 17·25 에서도 문구 동일)

```text
Ex.java:6: error: incompatible types: int cannot be converted to Void
        Void v1 = x;
                  ^
Ex.java:7: error: incompatible types: long cannot be converted to Void
        Void v2 = y;
                  ^
Ex.java:8: error: incompatible types: String cannot be converted to Void
        Void v3 = s;
                  ^
3 errors
```

- 에러 문구의 **`int` / `long` / `String` 이 곧 추론된 타입**이다. 컴파일러가 직접 말해 준다.
- `Void` 를 쓰는 이유는 **어떤 타입도 `Void` 로 변환되지 않기 때문**이다. 반드시 에러가 나고, 그 에러가 타입을 실어 준다.

같은 방법으로 까다로운 경우를 뽑아 보면 이렇게 나온다(`Ex.java (04-c2)`·`(04-h)`).

```text
Ex.java:9: error: incompatible types: ArrayList<Object> cannot be converted to Void
        Void v1 = raw;                      // var raw = new ArrayList<>();
Ex.java:10: error: incompatible types: ArrayList<String> cannot be converted to Void
        Void v2 = typed;                    // var typed = new ArrayList<String>();
Ex.java:11: error: incompatible types: <anonymous Object> cannot be converted to Void
        Void v3 = anon;                     // var anon = new Object() { int count = 1; };
Ex.java:12: error: incompatible types: long cannot be converted to Void
        Void v4 = cond;                     // var cond = args.length == 0 ? 1 : 2L;
Ex.java:13: error: incompatible types: int[] cannot be converted to Void
        Void v5 = arr;                      // var arr = new int[]{1, 2, 3};
```

- ★ **`new ArrayList<>()` 는 `ArrayList<Object>` 다.** 이것이 `var` 의 대표 함정이다.
- ★ **익명 클래스는 `<anonymous Object>`** — **이름이 없는 타입**이라 손으로는 적을 수가 없다.
- 삼항 연산자는 **두 갈래를 합친 타입**이 된다. `1 : 2L` 은 수치 승격으로 `long` 이다.

```text
Ex.java:10: error: incompatible types: INT#1 cannot be converted to Void
        Void v2 = mixed;                    // var mixed = a.length == 0 ? "a" : 1;
              ^
  where INT#1,INT#2 are intersection types:
    INT#1 extends Object,Serializable,Comparable<? extends INT#2>,Constable,ConstantDesc
    INT#2 extends Object,Serializable,Comparable<?>,Constable,ConstantDesc
```

- `String` 과 `Integer` 를 합치면 **교집합 타입(intersection type)** 이 나온다. 이것도 손으로 못 적는다.

★ 방법 2 — **`javac -g` + `javap -v` 로 클래스 파일에 박힌 이름표를 읽는다.** (6)에서 이어 본다.

★ 방법 3 — **IDE 의 인레이 힌트.** 눈으로 보는 용도로는 편하지만 **근거로 쓰기엔 약하다**(설정에 따라 꺼져 있다).\
확인이 필요하면 방법 1·2로 간다.

비용 — 방법 1은 컴파일 한 번. 방법 2는 `javac -g` 한 번 + `javap` 한 번.

> **교집합 타입(intersection type)** — 여러 타입을 동시에 만족하는 이름 없는 타입.\
> 예: `String` 과 `Integer` 의 공통 상위는 `Object & Serializable & Comparable<...>` 인데, 이 조합에는 이름이 없다.

### (3) 쓸 수 있는 자리 — 여섯 곳뿐이다

**언제 쓰나** — "여기 `var` 써도 되나?"를 판단할 때.

```text
  지역 변수 선언       var s = "hi";                            O
  기본 for 의 인덱스   for (var i = 0; i < 2; i++)              O
  향상된 for 의 변수   for (var e : list)                        O
  try-with-resources   try (var sc = new Scanner("토큰"))        O
  람다 파라미터 (11+)  (var a, var b) -> a + b                   O
  final 과 함께        final var fn = 10;                        O
  -------------------------------------------------------------
  필드                 var field = 1;                            X
  파라미터             void m(var p)                             X
  반환 타입            var r() { ... }                           X
  catch 파라미터       catch (var e)                             X
  제네릭 인자          new ArrayList<var>()                      X
  타입 선언 이름       class var { }                             X
```

**출력** (`Ex.java (04-a)`, JDK 21.0.5 — 17·25 에서도 동일)

```text
--- 5. 쓸 수 있는 자리 ---
  기본 for      : k=0
  기본 for      : k=1
  향상된 for    : e=a
  향상된 for    : e=b
  try-with-res  : 토큰
  람다 파라미터 : 7
```

그림 해설 (한 단계씩):

- 허용되는 자리의 공통점은 **"초기화식이 바로 옆에 있는 지역 변수"** 다.
- 필드·파라미터·반환 타입은 **클래스 파일의 공개 표면(시그니처)** 이다.\
  여기에 추론을 허용하면 **호출하는 쪽의 컴파일이 내 구현 세부에 매이게 된다.** 그래서 막혔다.
- `catch` 파라미터는 초기화식이 없다 — 던져지는 예외가 무엇인지 선언으로 밝혀야 한다.

비용 — 없다. 판단 규칙이다.

### (4) 못 쓰는 자리 — 에러 메시지가 이유까지 말해 준다

**언제 쓰나** — `cannot infer type` 이 떴을 때. **괄호 안 한 줄이 원인이다.**

다섯 가지를 각각 따로 컴파일해 얻은 것이다(`Ex.java (04-e1)`~`(04-e5)`, 17·21·25 문구 동일).

```text
(04-e1)  var x = null;
Ex.java:1: error: cannot infer type for local variable x
  (variable initializer is 'null')

(04-e2)  var x; x = 1;
Ex.java:1: error: cannot infer type for local variable x
  (cannot use 'var' on variable without initializer)

(04-e3)  var x = {1, 2, 3};
Ex.java:1: error: cannot infer type for local variable x
  (array initializer needs an explicit target-type)

(04-e4)  var x = () -> {};
Ex.java:1: error: cannot infer type for local variable x
  (lambda expression needs an explicit target-type)

(04-e5)  var x = Ex::hello;
Ex.java:2: error: cannot infer type for local variable x
  (method reference needs an explicit target-type)

(04-f4)  var x = x + 1;
Ex.java:1: error: cannot infer type for local variable x
  (cannot use 'var' on self-referencing variable)
```

선언 자리가 아예 아닌 경우는 다른 문구가 나온다(`Ex.java (04-c3)`·`(04-e6)`·`(04-e7)`).

```text
Ex.java:2: error: 'var' is not allowed here
    var field = 1;                       // (1) 필드
    ^
Ex.java:3: error: 'var' is not allowed here
    static var sfield = 1;               // (2) static 필드
           ^
Ex.java:4: error: 'var' is not allowed here
    void m(var p) { }                    // (3) 파라미터
           ^
Ex.java:5: error: 'var' is not allowed here
    var r() { return 1; }                // (4) 반환 타입
    ^
4 errors
```

```text
Ex.java:3: error: 'var' is not allowed here
    try { throw new RuntimeException("x"); } catch (var e) { }
                                                    ^
1 error
```

```text
Ex.java:2: error: 'var' is not allowed here
public class Ex { public static void main(String[] a) { var x = new ArrayList<var>(); } }
                                                                              ^
1 error
```

그림 해설 (한 단계씩):

- **두 갈래로 갈린다.** `cannot infer type` 은 "자리는 되는데 오른쪽으로 못 정하겠다",
  `'var' is not allowed here` 는 "그 자리 자체가 안 된다".
- 앞의 것은 **초기화식을 고치면** 풀리고, 뒤의 것은 **타입을 손으로 적어야** 풀린다.
- 셋(`{1,2,3}`·람다·메서드 참조)의 이유가 같다 — **대상 타입(target type)이 있어야 의미가 정해지는 식**이라,
  왼쪽이 비면 결정할 근거가 없다.

비용 — 없다. 컴파일 타임 에러다.

> **대상 타입(target type)** — 식의 의미가 "어디에 대입되느냐"로 정해질 때, 그 대입되는 쪽의 타입.\
> 예: `Runnable r = () -> {};` 에서 람다의 대상 타입은 `Runnable` 이다. `var r = () -> {};` 에는 그것이 없다.

### (5) 람다 파라미터의 `var` — 섞어 쓰면 막힌다 (11+)

**언제 쓰나** — 람다 파라미터에 애너테이션(`@NonNull` 등)이나 `final` 을 붙이고 싶을 때. 그것이 이 문법의 용도다.

```java
BiFunction<Integer, Integer, Integer> add = (var a, var b) -> a + b;   // OK (11+)
```

**출력** (`Ex.java (04-a)`)

```text
  람다 파라미터 : 7
```

혼용은 컴파일 에러다. **두 가지 혼용이 각각 다른 문구**로 나온다.

```text
(04-f1)  (var x, y) -> x + y
Ex.java:4: error: invalid lambda parameter declaration
    BiFunction<Integer,Integer,Integer> f = (var x, y) -> x + y;
                                            ^
  (cannot mix 'var' and implicitly-typed parameters)
1 error

(04-f2)  (var x, Integer y) -> x + y
Ex.java:4: error: invalid lambda parameter declaration
    BiFunction<Integer,Integer,Integer> f = (var x, Integer y) -> x + y;
                                            ^
  (cannot mix 'var' and explicitly-typed parameters)
1 error
```

괄호도 생략할 수 없다.

```text
(04-f3)  Function<Integer,Integer> f = var x -> x + 1;
Ex.java:4: error: ';' expected
Ex.java:4: error: not a statement
2 errors
```

```text
  전부 var        (var a, var b) -> ...       O
  전부 생략       (a, b)         -> ...       O
  전부 명시       (Integer a, Integer b) -> O
  섞음            (var a, b)     -> ...       X   implicitly-typed 와 혼용 불가
  섞음            (var a, Integer b) -> ...   X   explicitly-typed 와 혼용 불가
  괄호 생략       var x -> ...                X   문법 자체가 안 된다
```

그림 해설 (한 단계씩):

- **세 방식 중 하나로 통일**해야 한다. 파라미터 목록 안에서 섞는 것만 막힌다.
- `var` 를 쓰는 유일한 실익은 **애너테이션·`final` 을 붙일 자리가 생긴다**는 것이다
  (`(@NonNull var a, var b) -> ...`). 그게 필요 없으면 `(a, b)` 가 짧다.

비용 — 없다. 람다 파라미터의 `var` 는 바이트코드를 바꾸지 않는다.

### (6) ★ `var` 는 런타임에 아무것도 아니다 — `javap` 가 증언한다

**언제 쓰나** — "`var` 를 쓰면 느려지나?"·"동적 타입인가?"를 판단할 때. **도구로 끝낸다.**

같은 내용을 두 번 쓴 프로그램이다(`Ex.java (04-b)`).

```java
static void withVar() {
    var i = 1;
    var s = "hi";
    var list = new ArrayList<String>();
    var raw  = new ArrayList<>();
    list.add(s);
    raw.add(s);
}
static void withTypes() {
    int i = 1;
    String s = "hi";
    ArrayList<String> list = new ArrayList<String>();
    ArrayList<Object> raw  = new ArrayList<Object>();
    list.add(s);
    raw.add(s);
}
```

**`javac -g Ex.java && javap -c -p -l Ex.class` 출력 그대로** (JDK 21.0.5)

```text
  static void withVar();
    Code:
       0: iconst_1
       1: istore_0
       2: ldc           #7                  // String hi
       4: astore_1
       5: new           #9                  // class java/util/ArrayList
       8: dup
       9: invokespecial #11                 // Method java/util/ArrayList."<init>":()V
      12: astore_2
      13: new           #9                  // class java/util/ArrayList
      16: dup
      17: invokespecial #11                 // Method java/util/ArrayList."<init>":()V
      20: astore_3
      21: aload_2
      22: aload_1
      23: invokevirtual #12                 // Method java/util/ArrayList.add:(Ljava/lang/Object;)Z
      26: pop
      27: aload_3
      28: aload_1
      29: invokevirtual #12                 // Method java/util/ArrayList.add:(Ljava/lang/Object;)Z
      32: pop
      33: return
    LocalVariableTable:
      Start  Length  Slot  Name   Signature
          2      32     0     i   I
          5      29     1     s   Ljava/lang/String;
         13      21     2  list   Ljava/util/ArrayList;
         21      13     3   raw   Ljava/util/ArrayList;

  static void withTypes();
    Code:
       0: iconst_1
       1: istore_0
       2: ldc           #7                  // String hi
       4: astore_1
       5: new           #9                  // class java/util/ArrayList
       8: dup
       9: invokespecial #11                 // Method java/util/ArrayList."<init>":()V
      12: astore_2
      13: new           #9                  // class java/util/ArrayList
      16: dup
      17: invokespecial #11                 // Method java/util/ArrayList."<init>":()V
      20: astore_3
      21: aload_2
      22: aload_1
      23: invokevirtual #12                 // Method java/util/ArrayList.add:(Ljava/lang/Object;)Z
      26: pop
      27: aload_3
      28: aload_1
      29: invokevirtual #12                 // Method java/util/ArrayList.add:(Ljava/lang/Object;)Z
      32: pop
      33: return
    LocalVariableTable:
      Start  Length  Slot  Name   Signature
          2      32     0     i   I
          5      29     1     s   Ljava/lang/String;
         13      21     2  list   Ljava/util/ArrayList;
         21      13     3   raw   Ljava/util/ArrayList;
```

제네릭 인자까지 보려면 `javap -v` 의 `LocalVariableTypeTable` 을 본다.

```text
  static void withVar();
      LocalVariableTypeTable:
        Start  Length  Slot  Name   Signature
           13      21     2  list   Ljava/util/ArrayList<Ljava/lang/String;>;
           21      13     3   raw   Ljava/util/ArrayList<Ljava/lang/Object;>;

  static void withTypes();
      LocalVariableTypeTable:
        Start  Length  Slot  Name   Signature
           13      21     2  list   Ljava/util/ArrayList<Ljava/lang/String;>;
           21      13     3   raw   Ljava/util/ArrayList<Ljava/lang/Object;>;
```

그림 해설 (한 단계씩):

- ★ **두 메서드의 명령열이 한 바이트도 다르지 않다.** `var` 는 실행되는 코드를 바꾸지 않는다.
- ★ **`LocalVariableTable` 에 추론된 타입이 그대로 박힌다** — `I`(int), `Ljava/lang/String;`.\
  `var` 라는 흔적은 클래스 파일 어디에도 없다.
- ★ **`var raw = new ArrayList<>()` 의 시그니처가 `ArrayList<Ljava/lang/Object;>`** 다.\
  손으로 `ArrayList<Object>` 라고 쓴 쪽과 **글자 단위로 같다.** 추론 결과가 무엇인지 여기서 확정된다.
- 이 표들은 `javac -g`(또는 `-g:vars`)로 컴파일해야 생긴다. 없으면 `javap` 에도 안 나온다.

비용 — **런타임 비용 0.** `var` 는 컴파일 타임 문법이다.

> **`LocalVariableTable`** — 클래스 파일의 선택적 속성. 지역 변수의 이름과 **소거 후 타입 서술자**를 담는다. `javac -g` 로만 생성된다.\
> 예: `int i` 는 `Signature I`, `String s` 는 `Ljava/lang/String;`.

> **`LocalVariableTypeTable`** — 같은 성격의 속성이지만 **제네릭 인자까지 살아 있는 시그니처**를 담는다.\
> 예: `ArrayList<String> list` 는 `Ljava/util/ArrayList<Ljava/lang/String;>;`.

### (7) `var` 는 `final` 이 아니다

**언제 쓰나** — `var` 를 쓰면 불변이 된다고 오해할 때. **아니다.**

```java
var n = 1;
n = 2;
n++;
final var fn = 10;   // final 을 붙이고 싶으면 직접 붙인다
```

**출력** (`Ex.java (04-a)`)

```text
--- 4. var 는 final 이 아니다 ---
var n = 1; n = 2; n++ -> 3
final var fn     : 10
```

그림 해설 (한 단계씩):

- `var` 는 **타입만 생략**한다. 재대입 가능 여부와는 무관하다.
- `final var` 는 허용되고, 이 조합은 **"타입은 컴파일러가, 불변성은 내가"** 를 뜻한다.
- 람다 캡처 조건인 **effectively final** 도 그대로 적용된다 — `var` 로 선언해도 재대입하면 캡처가 막힌다.\
  캡처 규칙의 정본은 [`../03-variables-and-assignment/`](../03-variables-and-assignment/)·[`../29-lambda-expressions/`](../29-lambda-expressions/).

비용 — 없다.

### (8) 익명 클래스와 쓰면 — 이름 없는 타입을 붙잡을 수 있다

**언제 쓰나** — 그 자리에서만 쓰고 버릴 작은 묶음을 만들 때. `var` 가 **새로 열어 준 유일한 능력**이다.

```java
var anon = new Object() {
    int count = 0;
    int bump() { return ++count; }
};
anon.bump(); anon.bump();
```

**출력** (`Ex.java (04-a)`)

```text
--- 3. 익명 클래스 ---
anon.count       : 2
anon.getClass()  : Ex$1
```

```text
  Object anon = new Object() { int count; ... };        var anon = new Object() { int count; ... };
  +----------------------------------------+            +----------------------------------------+
  | 정적 타입: Object                       |            | 정적 타입: <anonymous Object>           |
  | anon.count  -> 컴파일 에러              |            | anon.count  -> 2                        |
  | anon.bump() -> 컴파일 에러              |            | anon.bump() -> 된다                     |
  +----------------------------------------+            +----------------------------------------+
    손으로 적을 수 있는 이름은 Object 뿐이라               컴파일러가 이름 없는 타입 그대로 기억한다
    새 멤버가 전부 가려진다
```

그림 해설 (한 단계씩):

- 익명 클래스의 타입은 **이름이 없다.** 손으로 적을 수 있는 가장 가까운 이름은 상위 타입뿐이다.
- `var` 는 그 이름 없는 타입을 **그대로 붙잡는다.** 그래서 새로 선언한 멤버에 접근할 수 있다.
- 런타임 클래스 이름은 `Ex$1` — 이것은 **javac 의 명명 규칙**이지 언어 보장이 아니다.
- 다만 **이 타입은 메서드 밖으로 못 나간다.** 반환 타입에는 `var` 를 못 쓰기 때문이다((3)).

비용 — 익명 클래스 하나당 클래스 파일 하나(`Ex$1.class`).

## 문법 — 형태와 규칙

직접 쓴 최소 예제다. 묻는 것 하나만 남겼다.

### `var` 는 키워드가 아니다 — "예약된 타입 이름"이다

```java
int var = 3;              // 변수 이름으로는 쓸 수 있다
var x = var + 1;          // 그 옆에서 var 를 타입 자리로도 쓸 수 있다
```

**출력** (`Ex.java (04-g1)`)

```text
int var = 3; var x = var + 1; -> 4
```

**타입 선언의 이름으로만 막힌다.**

```text
(04-g2)
Ex.java:1: error: 'var' not allowed here
class var { }
      ^
  as of release 10, 'var' is a restricted type name and cannot be used for type declarations
1 error
```

- 그래서 **Java 10 이전에 `var` 라는 변수·메서드·패키지 이름을 쓰던 코드는 그대로 컴파일된다.**
- 막힌 것은 `class var`·`interface var`·`enum var`·`record var` 같은 **타입 선언 이름**뿐이다.

### 추론 결과가 직관과 갈리는 것들

```java
var bytes = (byte) 1;      // byte  — 캐스트 타입이 그대로 온다
var ch    = 'a' + 1;       // int   ★ char 가 아니다 (이항 승격)
var div   = 1 / 2;         // int   — 값은 0
var empty = Collections.emptyList();   // List<Object>  ★ 대상 타입이 없어 Object 로 간다
var arr   = new int[]{1, 2, 3};        // int[]
```

이 다섯은 전부 **방법 1(`Void` 대입)로 확인한 것**이다(`Ex.java (04-h)`).

```text
Ex.java:9: error: incompatible types: List<Object> cannot be converted to Void
Ex.java:11: error: incompatible types: byte cannot be converted to Void
Ex.java:12: error: incompatible types: int cannot be converted to Void
Ex.java:13: error: incompatible types: int cannot be converted to Void
```

- ★ `var empty = Collections.emptyList();` 가 `List<Object>` 인 것이 `new ArrayList<>()` 와 같은 함정이다.\
  **제네릭 메서드의 타입 인자도 대상 타입에서 나오기 때문**이다. `var` 는 그 대상 타입을 없앤다.
- 이럴 때는 타입을 손으로 적거나(`List<String> empty = ...`) 인자를 명시한다(`Collections.<String>emptyList()`).

### 언제 `var` 를 쓰면 읽히나 — 「타입이 오른쪽에 보이면 쓴다」

```java
var users = new ArrayList<User>();               // 오른쪽에 ArrayList<User> 가 보인다  -> 쓴다
var line  = reader.readLine();                   // readLine 이 String 임을 안다        -> 쓴다
var entry = (Map.Entry<String, Integer>) obj;    // 캐스트에 타입이 있다                -> 쓴다
var conn  = DriverManager.getConnection(url);    // 이름으로 짐작된다                   -> 대개 쓴다

var r = compute();                               // compute 가 뭘 주는지 여기선 모른다  -> 쓰지 않는다
var x = list.get(0);                             // list 의 원소 타입을 거슬러 봐야 안다 -> 상황에 따라
var v = service.process(a, b, c);                // 모른다                              -> 쓰지 않는다
```

판단 한 줄: **읽는 사람이 그 줄만 보고 타입을 말할 수 있으면 `var`, 아니면 타입을 적는다.**

## 어디서 틀리나

이 주제의 값어치는 전부 여기 있다.

### 1. `var` 를 "동적 타입"으로 오해한다

```java
var x = 1;
x = "hi";     // 컴파일 에러
```

- `var` 는 **타입이 없어지는 것이 아니라 컴파일러가 정하는 것**이다. 정해지면 끝이다.
- (6)의 `javap` 출력이 증거다 — 클래스 파일에는 `I`·`Ljava/lang/String;` 가 그대로 박힌다.
- 파이썬·자바스크립트의 변수와 **완전히 다른 물건**이다.

### 2. ★ 다이아몬드와 함께 써서 `Object` 컬렉션을 만든다

```java
var raw = new ArrayList<>();
raw.add("문자열");
raw.add(42);
raw.add(null);
```

**출력** (`Ex.java (04-a)`)

```text
--- 2. var + 다이아몬드 ---
new ArrayList<>() 에 넣은 것 : [문자열, 42, null]
new ArrayList<String>()      : [문자열]
```

```text
  var raw = new ArrayList<>();                 var typed = new ArrayList<String>();
  +-----------------------------------+        +-----------------------------------+
  | 추론: ArrayList<Object>           |        | 추론: ArrayList<String>           |
  | raw.add(42)    -> 그냥 된다        |        | typed.add(42)  -> 컴파일 에러      |
  | 꺼내면 Object  -> 캐스트 필요      |        | 꺼내면 String                     |
  +-----------------------------------+        +-----------------------------------+
    타입 안전이 조용히 사라진다                  컴파일러가 막아 준다
```

- **에러가 안 난다.** 다이아몬드는 대상 타입에서 인자를 받는데, `var` 가 그 대상 타입을 없앴다.
  남은 후보가 `Object` 뿐이라 그대로 확정된다.
- 진단: (2)의 방법 1로 찍어 보면 `ArrayList<Object>` 가 나온다.
- 방어: **`var` 와 `<>` 를 한 줄에 같이 쓰지 않는다.** `var list = new ArrayList<String>();` 처럼 한쪽은 적는다.

### 3. `var` 로 선언하면 불변이라고 믿는다

- (7) 에서 보았듯 `var n = 1; n = 2;` 는 그냥 된다.
- 코틀린의 `val`/`var` 대응을 자바에 옮기면 틀린다 — 자바에는 **`final var` 를 직접 써야** `val` 이 된다.
- 람다 캡처가 막히는 이유도 `var` 와 무관하다. 재대입했는지만 본다([`../29-lambda-expressions/`](../29-lambda-expressions/)).

### 4. `null` 로 초기화해 놓고 나중에 값을 채우려 한다

```java
var conn = null;             // cannot infer type — (variable initializer is 'null')
if (...) conn = openA(); else conn = openB();
```

- 흔한 옛날 패턴이지만 `var` 와는 안 맞는다.
- 고치는 방향은 둘 중 하나다.
  - 타입을 적는다 — `Connection conn = null;`
  - ★ **삼항이나 메서드 추출로 초기화를 한 식으로 만든다** — `var conn = cond ? openA() : openB();`\
    이쪽이 대개 더 나은 코드가 된다(`final` 로도 만들 수 있다).

### 5. 람다·메서드 참조를 `var` 에 담으려 한다

```java
var f = () -> System.out.println("hi");   // cannot infer type — lambda expression needs an explicit target-type
var g = String::length;                   // cannot infer type — method reference needs an explicit target-type
```

- 람다는 **대상 타입이 있어야 무엇의 구현인지 정해진다.** `() -> {}` 하나가 `Runnable` 일 수도 `Action` 일 수도 있다.
- 고치려면 함수형 인터페이스를 적는다 — `Runnable f = () -> ...;`\
  또는 대상 타입이 있는 자리로 옮긴다(메서드 인자로 바로 넘기기).
- 함수형 인터페이스 고르기는 [`../31-functional-interfaces/`](../31-functional-interfaces/) 가 정본이다.

### 6. 필드에 쓰려다 막히고 이유를 모른다

```text
Ex.java:2: error: 'var' is not allowed here
    var field = 1;
    ^
```

- 필드·파라미터·반환 타입은 **다른 클래스가 컴파일할 때 읽는 표면**이다.
- 여기에 추론을 허용하면 내 초기화식을 고치는 순간 **쓰는 쪽의 컴파일이 깨진다.**\
  JEP 286 이 범위를 "지역 변수"로 좁힌 이유가 이것이다.
- 고치는 법은 하나다 — **타입을 적는다.**

## 구현 세부사항 대 언어 보장

이 절은 "**어디까지 믿어도 되나**"를 가른다.

| 항목 | 누가 보장하나 | 근거 |
|---|---|---|
| `var` 는 지역 변수에만 쓸 수 있다 | **JLS (언어 보장)** | JLS §14.4.1 — `var` 는 지역 변수 선언의 타입 자리에만 허용 |
| `null` 초기화로는 추론할 수 없다 | **JLS (언어 보장)** | JLS §14.4.1 — 초기화식의 타입이 `null` 타입이면 컴파일 에러 |
| 람다·메서드 참조·배열 초기화 축약은 못 쓴다 | **JLS (언어 보장)** | 대상 타입이 필요한 식(poly expression)이다 |
| `var` 는 `final` 을 의미하지 않는다 | **JLS (언어 보장)** | 제어자와 타입은 별개다. `final var` 를 명시해야 한다 |
| `var` 가 런타임 동작을 바꾸지 않는다 | **JLS + 구현** | 타입이 확정되면 평범한 선언이다. **명령열이 같다는 것은 관찰**이다(아래) |
| `withVar` 와 `withTypes` 의 바이트코드가 동일 | **구현 세부(관찰)** | `javap -c -p -l`, JDK 21.0.5 |
| `LocalVariableTable` 에 타입이 남는 것 | **구현 세부 + 컴파일 옵션** | `javac -g` 없이는 표 자체가 안 생긴다 |
| 익명 클래스 이름이 `Ex$1` | **구현 세부** | javac 의 명명 규칙 |
| 에러 문구(`cannot infer type for local variable x`) | **구현 세부** | javac 의 메시지. 17·21·25 에서 같았다 — **관찰이다** |

### 버전에 갈리는 것은 람다 파라미터뿐이다

같은 소스를 `--release` 만 바꿔 컴파일했다(`Ex.java (04-g3)`, JDK 21.0.5 의 javac).

```text
$ javac --release 10 Ex.java
Ex.java:4: error: var syntax in implicit lambdas are not supported in -source 10
    BiFunction<Integer,Integer,Integer> f = (var x, var y) -> x + y;
                                                 ^
  (use -source 11 or higher to enable var syntax in implicit lambdas)
1 error

$ javac --release 11 Ex.java
(성공)
```

- **지역 변수의 `var` 는 10**(JEP 286), **람다 파라미터의 `var` 는 11**(JEP 323)이다.
- 17·21·25 에서 이 문서의 **모든 출력과 에러 문구가 같았다.** 관찰이고, 보장은 JEP·JLS 쪽이다.

**경계 한 줄** — `javap` 로 본 것(`I`·`Ljava/util/ArrayList<Ljava/lang/Object;>;`·`Ex$1`)은 **관찰**이고,
"지역 변수에만 쓸 수 있다"·"`null` 로는 추론 불가"는 **명세**다.\
외울 것은 명령 이름이 아니라 **"`var` 는 컴파일러가 이름표를 대신 써 주는 것"** 이라는 성질이다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 판단 |
|---|---|
| `var x = new Foo();` — 오른쪽에 타입이 그대로 보인다 | **쓴다.** 같은 단어를 두 번 안 적는다 |
| `var e : list` — 향상된 for 의 원소 | **쓴다.** 원소 타입이 컬렉션 선언에 이미 있다 |
| `var entry : map.entrySet()` — 긴 제네릭 타입 | **쓴다.** `Map.Entry<String, List<Order>>` 를 안 적어도 된다 |
| `var r = compute();` — 메서드 이름만으로 타입을 모른다 | **안 쓴다.** 읽는 사람이 정의로 뛰어야 한다 |
| `var x = 0;` — 나중에 `long` 이 필요해질 수 있는 수치 | **주의.** `int` 로 굳는다. `var x = 0L;` 로 의도를 적는다 |
| `var list = new ArrayList<>();` | **쓰지 않는다.** `ArrayList<Object>` 가 된다 |
| 익명 클래스에 새 멤버를 달아 그 자리에서 쓴다 | **쓴다.** `var` 가 아니면 접근이 안 된다 |
| 람다 파라미터에 애너테이션을 달아야 한다 | **쓴다.** `(@NonNull var a, var b) -> ...` |
| 필드·파라미터·반환 타입 | **못 쓴다.** 컴파일 에러 |
| 공개 API 의 경계 | 타입을 적는다. 읽는 사람이 다르다 |

판단 규칙 두 줄.

- **「타입이 오른쪽에 보이면 쓴다」** — 그 줄만 읽고 타입을 말할 수 있는가로 정한다.
- **`var` 와 `<>` 를 한 줄에 같이 쓰지 않는다** — 둘 다 추론이라 서로 기댈 곳이 없어진다.

## 핵심 문장

- `var` 는 **지역 변수의 타입을 컴파일러가 초기화식에서 계산해 채워 주는 것**이다. 타입이 없어지는 것이 아니다.
- 쓸 수 있는 자리는 **지역 변수·두 종류 for·try-with-resources·람다 파라미터(11+)** 뿐이고,
  필드·파라미터·반환 타입·`catch` 는 `'var' is not allowed here` 로 막힌다.
- 못 쓰는 경우의 이유는 **에러 괄호 안 한 줄**에 그대로 나온다 — `'null'`·`without initializer`·`needs an explicit target-type`·`self-referencing`.
- ★ **추론 결과는 추측하지 말고 확인한다** — `Void` 에 일부러 대입해 에러를 뽑거나, `javac -g` + `javap -v` 의 `LocalVariableTable`/`LocalVariableTypeTable` 을 읽는다.
- ★ **`var` 는 런타임에 아무것도 아니다.** 같은 코드를 `var` 로 쓴 것과 타입을 적은 것의 바이트코드가 한 바이트도 다르지 않았다(JDK 21.0.5 관찰).
- `var` 는 **`final` 이 아니다.** 불변이 필요하면 `final var` 를 직접 쓴다.
- `var list = new ArrayList<>();` 는 `ArrayList<Object>` 다 — **이 문서에서 실측으로 확인한 대표 함정**이다.

## 관련 자료

- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 04번)
- [`../../../../../../history/java/java-10.md`](../../../../../../history/java/java-10.md) — **그쪽은 `var` 가 왜·언제 들어왔나(JEP 286, 도입 논쟁)까지, 여기는 그래서 코드에서 어디에 쓰고 어디서 컴파일이 막히나부터.**\
  설계 배경은 그쪽이 정본이고, 이 문서는 배경을 다시 쓰지 않는다
- [`../03-variables-and-assignment/`](../03-variables-and-assignment/) — **변수·대입·`final`·effectively final 의 정본.**\
  `final var` 가 무엇을 막는지, 캡처가 왜 값 복사인지는 거기서 본다. 여기는 **타입을 누가 적느냐**만 다룬다
- [`../29-lambda-expressions/`](../29-lambda-expressions/) — 람다의 문법과 캡처가 정본. `(var a, var b)` 의 나머지 규칙은 거기
- [`../31-functional-interfaces/`](../31-functional-interfaces/) — `var f = () -> ...` 가 막힐 때 어떤 인터페이스를 적어야 하는지
- [`../12-nested-classes/`](../12-nested-classes/) — 익명 클래스의 정본. (8)의 `var anon` 은 그 타입을 붙잡는 방법일 뿐이다
- [`../14-records/`](../14-records/) — 이름 있는 작은 묶음이 필요하면 익명 클래스보다 `record` 가 낫다
- [`../36-stringbuilder-and-concat/`](../36-stringbuilder-and-concat/) — 같은 `javap -c` 로 "컴파일러가 한 일"을 보는 다른 사례
- [**17번 주제**](../17-generic-declarations/)(제네릭 선언) — 「어디서 틀리나」 2번의 `ArrayList<Object>` 가 왜 타입 안전을 잃는지
- [**19번 주제**](../19-type-erasure/)(타입 소거) — `LocalVariableTable` 과 `LocalVariableTypeTable` 이 왜 둘로 갈리는지

## 용어 풀이

- **`var`** — 지역 변수 선언에서 타입 자리에 쓰는 예약된 타입 이름. 컴파일러가 초기화식에서 타입을 계산한다(Java 10+).
- **타입 추론(type inference)** — 적지 않은 타입을 컴파일러가 문맥에서 계산해 채우는 것.
- **정적 타입(static type)** — 컴파일러가 그 변수·식에 대해 아는 타입. 실행 중에 바뀌지 않는다.
- **초기화식(initializer)** — 선언의 `=` 오른쪽 식. `var` 가 보는 유일한 정보다.
- **대상 타입(target type)** — 식의 의미가 대입되는 쪽 타입으로 정해질 때 그 타입. 람다·메서드 참조·`<>`·배열 초기화 축약이 요구한다.
- **다이아몬드(`<>`)** — 제네릭 타입 인자를 대상 타입에서 받아 오는 축약 표기. `var` 와 같이 쓰면 받을 곳이 없어진다.
- **교집합 타입(intersection type)** — 여러 타입을 동시에 만족하는 이름 없는 타입. 삼항 연산자의 두 갈래를 합칠 때 나온다.
- **예약된 타입 이름(restricted type name)** — 키워드는 아니지만 타입 선언의 이름으로는 못 쓰는 식별자. `var` 가 그렇다.
- **`LocalVariableTable`** — 클래스 파일의 선택 속성. 지역 변수 이름과 소거 후 타입을 담는다. `javac -g` 로만 생긴다.
- **`LocalVariableTypeTable`** — 같은 성격이되 제네릭 인자가 살아 있는 시그니처를 담는 속성.
- **effectively final** — `final` 을 안 붙였지만 재대입이 없어 붙여도 되는 변수. 람다 캡처의 조건이며 `var` 와 무관하다.
- **인레이 힌트(inlay hint)** — IDE 가 소스에 없는 정보(추론된 타입 등)를 화면에만 겹쳐 보여 주는 기능.

## 더 들어가면

- **`var` 는 지역 변수 선언의 "타입 자리"에만 쓰는 이름이라, 하위 호환이 깨지지 않았다.**\
  Java 10 이전에 `var` 라는 이름의 변수·메서드·패키지를 쓰던 코드는 그대로 컴파일된다.\
  막힌 것은 `class var` 같은 타입 선언 이름뿐이고, 그것도 실측으로 확인된다(`04-g2`).
- **`var` 가 붙잡을 수 있는 "손으로 못 적는 타입"이 둘 더 있다.**\
  익명 클래스 타입(`<anonymous Object>`)과 교집합 타입(`INT#1`)이다.\
  둘 다 반환 타입에는 못 쓰므로 **그 메서드 안에서만 살 수 있는 타입**이 된다.
- **`var` 는 제네릭 메서드의 타입 인자 추론도 끊는다.**\
  `var empty = Collections.emptyList();` 가 `List<Object>` 가 되는 것이 그 예다.\
  대상 타입이 있어야 `<String>` 이 결정되는데 `var` 가 그것을 없애기 때문이다.
- **`var` 를 쓰면 좁은 타입이 보존된다.**\
  `var b = (byte) 1;` 은 `byte` 이고, `int b = (byte) 1;` 로 적으면 `int` 로 넓어진다.\
  수치 타입을 다룰 때는 이 차이가 이후 연산의 승격 규칙에 영향을 준다([`../02-numeric-operations/`](../02-numeric-operations/)).
