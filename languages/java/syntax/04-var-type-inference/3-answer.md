# java/syntax/04 — `var` 지역 변수 타입 추론 (10+) — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·컴파일 에러·바이트코드는 **Temurin JDK 21.0.5 에서 실제로 돌려 얻은 것**이다.\
> 실행 프로그램은 **17.0.13 · 25.0.1** 에서도 출력이 같았고, 컴파일 에러 문구 14종도 세 JDK 에서 바이트 단위로 같았다\
> (관찰이다 — 보장은 JLS·JEP 인용으로만 적었다).\
> 바이트코드는 `javac -g` 로 컴파일한 뒤 `javap -c -p -l` / `javap -v -p` 출력을 그대로 옮겼다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 이 다섯 줄은 각각 무슨 타입으로 추론되는가

**출력** — 확인은 실행이 아니라 **일부러 낸 컴파일 에러**로 했다(`Ex.java (04-h)`, JDK 21.0.5 — 17·25 동일)

```text
Ex.java:9: error: incompatible types: List<Object> cannot be converted to Void
    Void v1 = empty;
              ^
Ex.java:10: error: incompatible types: INT#1 cannot be converted to Void
    Void v2 = mixed;
              ^
  where INT#1,INT#2 are intersection types:
    INT#1 extends Object,Serializable,Comparable<? extends INT#2>,Constable,ConstantDesc
    INT#2 extends Object,Serializable,Comparable<?>,Constable,ConstantDesc
Ex.java:11: error: incompatible types: byte cannot be converted to Void
    Void v3 = bytes;
              ^
Ex.java:12: error: incompatible types: int cannot be converted to Void
    Void v4 = ch;
              ^
Ex.java:13: error: incompatible types: int cannot be converted to Void
    Void v5 = div;
              ^
5 errors
```

삼항 `1 : 2L` 은 따로 찍었다(`Ex.java (04-c2)`).

```text
Ex.java:12: error: incompatible types: long cannot be converted to Void
        Void v4 = cond;
                  ^
```

**다섯 변수의 타입**

| 선언 | 추론된 타입 | 왜 |
|---|---|---|
| `var bytes = (byte) 1;` | `byte` | 캐스트식의 타입이 그대로 온다 |
| `var ch = 'a' + 1;` | **`int`** | `char + int` 는 이항 수치 승격으로 `int` 가 된다 |
| `var div = 1 / 2;` | `int` | 정수 나눗셈. 값은 `0` |
| `var cond = args.length == 0 ? 1 : 2L;` | **`long`** | 두 갈래를 합친 타입. `int` 와 `long` 은 `long` 으로 승격된다 |
| `var empty = Collections.emptyList();` | **`List<Object>`** | 제네릭 메서드의 타입 인자도 대상 타입에서 나온다 |

**`ch` 가 `char` 가 아닌 이유**

- `'a' + 1` 은 **식의 타입이 이미 `int`** 다. `var` 가 그 식의 타입을 그대로 받았을 뿐이다.
- ★ **타입을 손으로 적으면 결과가 달라진다** — 실행으로 확인했다(`Ex.java (04-m)`).

```text
char c = 'a' + 1  -> b
var  v = 'a' + 1  -> 98
```

- `char c = 'a' + 1;` 은 **상수식의 좁히기 변환**이 허용돼 `char` 로 들어가 `b` 가 찍힌다.
- `var v = 'a' + 1;` 에는 좁힐 대상 타입이 없다. 식의 타입 `int` 가 그대로 확정돼 `98` 이 찍힌다.
- **`var` 는 왼쪽이 만들어 주던 변환을 없앤다** — 이것이 「오른쪽만 본다」의 실제 결과다.\
  이항 수치 승격과 좁히기의 정본은 [`../02-numeric-operations/`](../02-numeric-operations/).

**`empty` 가 `List<String>` 이 될 수 없는 이유**

- `Collections.<T>emptyList()` 의 `T` 는 **대입되는 쪽(대상 타입)에서 결정**된다.
- `var` 는 왼쪽에 아무 정보도 두지 않으므로 결정할 근거가 사라지고, 경계인 `Object` 로 떨어진다.
- 고치려면 둘 중 하나다 — `List<String> empty = Collections.emptyList();` 또는 `var empty = Collections.<String>emptyList();`

> **이항 수치 승격(binary numeric promotion)** — 산술 연산의 두 피연산자를 공통의 더 넓은 수치 타입으로 맞추는 규칙.\
> 예: `char + int` 는 양쪽을 `int` 로 맞춘 뒤 더한다.

### 2. 추론된 타입을 도구로 확인하는 방법은 무엇인가

**가장 짧은 방법 — `Void` 에 일부러 대입한다**

```java
var x = 1;
Void v = x;      // 반드시 에러가 나고, 에러가 타입을 실어 준다
```

```text
Ex.java:6: error: incompatible types: int cannot be converted to Void
        Void v1 = x;
                  ^
```

**그 방법이 반드시 답을 주는 이유**

- `java.lang.Void` 는 **인스턴스를 만들 수 없는 자리 표시용 클래스**이고, 어떤 타입도 `Void` 로 변환되지 않는다.
- 그래서 대입이 **무조건 실패**하고, javac 의 `incompatible types: <왼쪽> cannot be converted to Void` 메시지가
  **추론 결과를 그대로 출력**한다.
- 교집합 타입(`INT#1`)이나 익명 클래스 타입(`<anonymous Object>`)처럼 **손으로 못 적는 타입도 이름을 보여 준다.**

**클래스 파일에서 읽는 방법**

```text
javac -g Ex.java          <- -g 없이는 표 자체가 안 생긴다
javap -c -p -l Ex.class   <- LocalVariableTable (소거 후 타입)
javap -v -p Ex.class      <- LocalVariableTypeTable (제네릭 인자까지)
```

- **소거 후 타입**은 `LocalVariableTable` 의 `Signature` 칸 — `I`, `Ljava/lang/String;`, `Ljava/util/ArrayList;`.
- **제네릭 인자까지** 보려면 `LocalVariableTypeTable` — `Ljava/util/ArrayList<Ljava/lang/Object;>;`.
- 두 표가 갈리는 이유는 타입 소거다([**19번 주제**](../19-type-erasure/)).

**IDE 인레이 힌트**는 눈으로 보기엔 편하지만 **설정에 따라 꺼져 있다.** 근거가 필요하면 위 둘로 간다.

### 3. 이 두 줄의 차이가 만드는 것

**출력** (`Ex.java (04-a)`, JDK 21.0.5 — 17·25 동일)

```text
--- 2. var + 다이아몬드 ---
new ArrayList<>() 에 넣은 것 : [문자열, 42, null]
new ArrayList<String>()      : [문자열]
```

**추론된 타입** (`Ex.java (04-c2)`)

```text
Ex.java:9: error: incompatible types: ArrayList<Object> cannot be converted to Void
        Void v1 = raw;
                  ^
Ex.java:10: error: incompatible types: ArrayList<String> cannot be converted to Void
        Void v2 = typed;
                  ^
```

- `raw` -> **`ArrayList<Object>`**
- `typed` -> **`ArrayList<String>`**

**세 `add` 중 무엇이 컴파일되나**

| 호출 | 결과 |
|---|---|
| `raw.add("문자열")` | **컴파일된다** (`Object` 자리에 `String`) |
| `raw.add(42)` | **컴파일된다** ★ 타입 안전이 사라졌다 |
| `typed.add(42)` | **컴파일 에러** |

```text
Ex.java:5: error: incompatible types: int cannot be converted to String
        typed.add(42);
                  ^
Note: Some messages have been simplified; recompile with -Xdiags:verbose to get full output
1 error
```

```text
  var raw = new ArrayList<>();                 var typed = new ArrayList<String>();
  +-----------------------------------+        +-----------------------------------+
  | 다이아몬드가 인자를 받을 곳        |        | 인자가 오른쪽에 적혀 있다          |
  |   = 대상 타입                      |        |                                   |
  | 그런데 왼쪽이 var 라 비어 있다     |        | var 가 그것을 그대로 받는다        |
  |   -> Object 로 떨어진다            |        |   -> ArrayList<String>            |
  +-----------------------------------+        +-----------------------------------+
    raw.add(42) 가 조용히 통과한다               typed.add(42) 는 컴파일에서 막힌다
```

**규칙 한 줄**

> **`var` 와 `<>` 를 한 줄에 같이 쓰지 않는다.** 둘 다 추론이라 서로 기댈 곳이 없어진다.

한쪽은 반드시 적는다 — `var list = new ArrayList<String>();` 또는 `List<String> list = new ArrayList<>();`

### 4. 이 여섯 줄은 왜 컴파일되지 않고, 에러 문구는 각각 어떻게 다른가

**출력** — 여섯을 각각 따로 컴파일했다(`Ex.java (04-e1)`~`(04-e5)`·`(04-f4)`, 17·21·25 문구 동일)

```text
(04-e1)  var a = null;
Ex.java:1: error: cannot infer type for local variable x
public class Ex { public static void main(String[] a) { var x = null; } }
                                                            ^
  (variable initializer is 'null')
1 error

(04-e2)  var b;
Ex.java:1: error: cannot infer type for local variable x
  (cannot use 'var' on variable without initializer)

(04-e3)  var c = {1, 2, 3};
Ex.java:1: error: cannot infer type for local variable x
  (array initializer needs an explicit target-type)

(04-e4)  var d = () -> {};
Ex.java:1: error: cannot infer type for local variable x
  (lambda expression needs an explicit target-type)

(04-e5)  var e = String::length;   (실측은 Ex::hello 로 확인)
Ex.java:2: error: cannot infer type for local variable x
  (method reference needs an explicit target-type)

(04-f4)  var f = f + 1;   (실측은 var x = x + 1 로 확인)
Ex.java:1: error: cannot infer type for local variable x
  (cannot use 'var' on self-referencing variable)
```

**첫 줄은 같은가**

- **여섯 다 첫 줄이 같다** — `error: cannot infer type for local variable <이름>`.
- 갈리는 것은 **괄호 안 한 줄**이다. 그 줄이 진짜 원인을 말한다.

**이유 한 줄 정리**

| 줄 | 괄호 안 이유 | 고치는 방향 |
|---|---|---|
| `var a = null;` | `variable initializer is 'null'` | 타입을 적거나, 초기화식을 한 식으로 만든다 |
| `var b;` | `cannot use 'var' on variable without initializer` | 선언과 초기화를 붙인다 |
| `var c = {1, 2, 3};` | `array initializer needs an explicit target-type` | `new int[]{1, 2, 3}` 으로 적는다 |
| `var d = () -> {};` | `lambda expression needs an explicit target-type` | `Runnable d = () -> {};` |
| `var e = String::length;` | `method reference needs an explicit target-type` | `Function<String,Integer> e = String::length;` |
| `var f = f + 1;` | `cannot use 'var' on self-referencing variable` | 타입을 적거나 다른 변수를 쓴다 |

**`c`·`d`·`e` 의 이유가 같은 까닭**

- 셋 다 **그 자체로는 타입이 정해지지 않는 식**이다. 대입되는 쪽(대상 타입)을 봐야 의미가 정해진다.
  - `{1, 2, 3}` — `int[]` 인지 `long[]` 인지 `Integer[]` 인지 왼쪽이 정한다.
  - `() -> {}` — `Runnable` 인지 다른 함수형 인터페이스인지 왼쪽이 정한다.
  - `String::length` — 어떤 시그니처에 맞추는지 왼쪽이 정한다.
- `var` 는 그 왼쪽을 비우는 문법이다. **비운 자리에서 정보를 달라는 것**이라 원리적으로 불가능하다.

> **대상 타입(target type)** — 식의 의미가 대입되는 쪽 타입으로 정해질 때 그 타입.\
> 예: `Runnable r = () -> {};` 에서 람다의 대상 타입은 `Runnable` 이다.

### 5. `var` 를 쓸 수 없는 자리는 어디까지인가

**출력** (`Ex.java (04-c3)`·`(04-e6)`·`(04-e7)`, 17·21·25 문구 동일)

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

**4번의 에러와 무엇이 다른가**

```text
  cannot infer type for local variable x        'var' is not allowed here
  +---------------------------------+           +---------------------------------+
  | 자리는 된다                     |           | 자리 자체가 안 된다              |
  | 오른쪽으로 타입을 못 정한다      |           | 오른쪽과 무관하다                |
  | -> 초기화식을 고치면 풀린다      |           | -> 타입을 적어야만 풀린다        |
  +---------------------------------+           +---------------------------------+
```

**필드·파라미터·반환 타입이 막힌 이유**

- 셋 다 **클래스 파일의 공개 표면(시그니처)** 이다. 다른 클래스가 컴파일할 때 이 표면을 읽는다.
- 여기에 추론을 허용하면 **내가 초기화식만 고쳐도 쓰는 쪽의 컴파일이 깨진다.**\
  예: `var x = 1;` 을 `var x = 1L;` 로 바꾸는 순간 필드 타입이 바뀌어 버린다.
- JEP 286 이 범위를 "지역 변수"로 좁힌 근거가 이것이다 — **한 메서드 안에서만 영향이 끝나는 자리**로 한정했다.

**허용된 자리 여섯 곳**

| 자리 | 예 |
|---|---|
| 지역 변수 선언 | `var s = "hi";` |
| 기본 `for` 의 인덱스 | `for (var i = 0; i < 2; i++)` |
| 향상된 `for` 의 변수 | `for (var e : list)` |
| try-with-resources 의 자원 | `try (var sc = new Scanner("토큰"))` |
| 람다 파라미터 (11+) | `(var a, var b) -> a + b` |
| `final` 과 조합 | `final var fn = 10;` |

### 6. 이 두 메서드의 바이트코드는 같은가 다른가

**출력** — `javac -g Ex.java && javap -c -p -l Ex.class` 그대로 (`Ex.java (04-b)`, JDK 21.0.5)

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

`javap -v -p` 의 제네릭 시그니처까지 보면 이렇다.

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

**명령열은 같은가**

- **같다. 한 바이트도 다르지 않다.** 오프셋·명령·상수 풀 인덱스가 전부 일치한다.

**`var` 라는 흔적이 남는가**

- **없다.** `LocalVariableTable` 에는 **추론된 타입이 그대로 박힌다** — `I`, `Ljava/lang/String;`.
- 제네릭까지 보면 `var raw = new ArrayList<>()` 의 시그니처가 `Ljava/util/ArrayList<Ljava/lang/Object;>;` 로,
  손으로 `ArrayList<Object>` 를 적은 쪽과 **글자 단위로 같다.**
- `-g` 없이 컴파일하면 이 표들이 아예 안 생긴다. 표의 존재 여부는 **컴파일 옵션**에 달렸다.

**`var` 의 런타임 비용**

- **0이다.** `var` 는 컴파일 타임 문법이고, 실행되는 코드에 아무 영향이 없다.
- 그래서 "`var` 가 느리다"·"`var` 는 동적 타입이다"는 이 출력 하나로 반증된다.
- 다른 타입을 대입하면 그냥 막힌다(`Ex.java (04-k)`).

```text
Ex.java:4: error: incompatible types: String cannot be converted to int
        x = "hi";
            ^
1 error
```

### 7. 람다 파라미터의 `var` 는 어디까지 허용되는가

**출력** (`Ex.java (04-a)`)

```text
  람다 파라미터 : 7
```

**몇 버전부터인가**

- **Java 11**(JEP 323). 지역 변수의 `var`(Java 10, JEP 286)보다 한 버전 늦다.
- `--release` 를 내려 확인했다(`Ex.java (04-g3)`, JDK 21.0.5 의 javac).

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

**혼용 에러 두 가지** (`Ex.java (04-f1)`·`(04-f2)`)

```text
Ex.java:4: error: invalid lambda parameter declaration
    BiFunction<Integer,Integer,Integer> f = (var x, y) -> x + y;
                                            ^
  (cannot mix 'var' and implicitly-typed parameters)
1 error
```

```text
Ex.java:4: error: invalid lambda parameter declaration
    BiFunction<Integer,Integer,Integer> f = (var x, Integer y) -> x + y;
                                            ^
  (cannot mix 'var' and explicitly-typed parameters)
1 error
```

- **생략형과 섞어도 막히고, 명시형과 섞어도 막힌다.** 문구가 각각 다르다.
- 파라미터 목록 안에서 **셋 중 하나로 통일**해야 한다.

**괄호를 빼면** (`Ex.java (04-f3)`)

```text
Ex.java:4: error: ';' expected
    Function<Integer,Integer> f = var x -> x + 1;
                                     ^
Ex.java:4: error: not a statement
    Function<Integer,Integer> f = var x -> x + 1;
                                      ^
2 errors
```

- 파서 단계에서 깨진다. `x -> x + 1` 은 괄호 생략이 되지만 **`var x -> ...` 는 문법 자체가 없다.**

**실익**

- **애너테이션과 `final` 을 붙일 자리가 생긴다** — `(@NonNull var a, var b) -> ...`.
- 그것이 필요 없으면 `(a, b)` 가 더 짧고, JEP 323 도 그 경우를 권하지 않는다.

### 8. `var` 는 `final` 인가

**출력** (`Ex.java (04-a)`)

```text
--- 4. var 는 final 이 아니다 ---
var n = 1; n = 2; n++ -> 3
final var fn     : 10
```

**`var n = 1; n = 2;` 는 컴파일되나**

- **된다.** `var` 는 타입만 생략하는 문법이고, 재대입 가능 여부와는 아무 관계가 없다.

**코틀린의 `val` 에 해당하는 것**

- `final var x = ...;` 라고 **직접 적어야** 한다.
- 코틀린은 `val`/`var` 두 키워드로 가르지만, 자바는 **타입 추론(`var`)과 불변(`final`)이 서로 다른 축**이다.

```text
              타입을 내가 적는다        타입을 컴파일러가 적는다
  재대입 가능      int x = 1;                var x = 1;
  재대입 금지      final int x = 1;          final var x = 1;
```

**람다 캡처와의 관계**

- **관계없다.** 캡처 조건은 `final` 또는 **effectively final**(선언 후 재대입 없음)이고, `var` 로 선언했는지는 보지 않는다.
- `var n = 1;` 뒤에 `n = 2;` 가 있으면 캡처가 막히고, 없으면 `var` 여도 캡처된다.
- 캡처의 정본은 [`../03-variables-and-assignment/`](../03-variables-and-assignment/)·[`../29-lambda-expressions/`](../29-lambda-expressions/).

### 9. 익명 클래스와 함께 쓰면 무엇이 달라지는가

**출력** (`Ex.java (04-j)`, JDK 21.0.5 — 17·25 동일)

```text
Ex.java:6: error: cannot find symbol
        System.out.println(anon2.count);
                                ^
  symbol:   variable count
  location: variable anon2 of type Object
1 error
```

- **`anon1` 쪽만 컴파일된다.** `anon2.count` 는 `Object` 에 `count` 가 없어서 막힌다.

실제 동작은 이렇다(`Ex.java (04-a)`).

```text
--- 3. 익명 클래스 ---
anon.count       : 2
anon.getClass()  : Ex$1
```

**컴파일러는 그 타입을 뭐라고 부르나**

```text
Ex.java:11: error: incompatible types: <anonymous Object> cannot be converted to Void
        Void v3 = anon;
                  ^
```

- **`<anonymous Object>`** — 꺾쇠까지 포함해 그대로 출력된다. **손으로 적을 수 있는 이름이 없다.**

```text
  Object anon2 = new Object() { int count; };     var anon1 = new Object() { int count; };
  +----------------------------------+            +----------------------------------+
  | 정적 타입: Object                |            | 정적 타입: <anonymous Object>    |
  | count 가 보이지 않는다           |            | count 가 보인다                  |
  | cannot find symbol               |            | 그냥 읽고 쓴다                   |
  +----------------------------------+            +----------------------------------+
    적을 수 있는 이름이 Object 뿐이라              이름 없는 타입을 그대로 붙잡았다
    새 멤버가 전부 가려진다
```

**메서드 밖으로 내보낼 수 있나**

- **못 한다.** 반환 타입에는 `var` 를 못 쓰기 때문이다(5번).
- 그래서 이 타입은 **선언한 메서드 안에서만 사는 타입**이 된다.
- 밖으로 내보내야 하면 `record` 나 이름 있는 클래스로 바꾼다([`../14-records/`](../14-records/)).

### 10. `var` 는 키워드인가

**출력** (`Ex.java (04-g1)`)

```text
int var = 3; var x = var + 1; -> 4
```

**`int var = 3;` 은 컴파일되나**

- **된다.** 같은 줄 옆에서 `var` 를 타입 자리로 쓰는 것까지 함께 된다.

**`class var { }` 는** (`Ex.java (04-g2)`)

```text
Ex.java:1: error: 'var' not allowed here
class var { }
      ^
  as of release 10, 'var' is a restricted type name and cannot be used for type declarations
1 error
```

- **안 된다.** 에러가 이유를 직접 말한다 — `restricted type name`.

**두 답이 갈리는 이유 한 문장**

> `var` 는 **키워드가 아니라 "예약된 타입 이름(restricted type name)"** 이라, 변수·메서드 이름으로는 쓸 수 있고 **타입 선언의 이름으로만** 막힌다.

- 그래서 Java 10 이전 코드에 `var` 라는 변수·메서드·패키지가 있어도 **그대로 컴파일된다.**
- 막힌 것은 `class var`·`interface var`·`enum var`·`record var` 뿐이다.

### 11. 어디에 쓰고 어디에 안 쓰나

**「타입이 오른쪽에 보이면 쓴다」의 실제 기준**

> **읽는 사람이 그 한 줄만 보고 타입을 말할 수 있는가.**

| 줄 | 판단 | 왜 |
|---|---|---|
| `var users = new ArrayList<User>();` | 쓴다 | 오른쪽에 타입이 그대로 있다. 같은 단어를 두 번 안 적는다 |
| `var line = reader.readLine();` | 쓴다 | 표준 API 라 `String` 임이 알려져 있다 |
| `var entry = (Map.Entry<String, List<Order>>) o;` | 쓴다 | 캐스트에 타입이 있다. 왼쪽에 또 적으면 두 줄이 된다 |
| `for (var e : orders)` | 쓴다 | 원소 타입이 컬렉션 선언에 이미 있다 |
| `var r = compute();` | 안 쓴다 | 메서드 정의로 뛰어야 타입을 안다 |
| `var v = service.process(a, b, c);` | 안 쓴다 | 같은 이유 |
| `var list = new ArrayList<>();` | **쓰지 않는다** | `ArrayList<Object>` 가 된다(3번) |

**`var r = compute();` 를 안 쓰는 이유**

- 읽는 사람이 **그 줄에서 멈춰 다른 파일로 이동**해야 한다. 인지 비용이 줄 수 하나만큼 줄고 탐색 비용이 늘어난다.
- `var` 가 줄이려는 것은 **중복**(`ArrayList<User> users = new ArrayList<User>()`)이지 정보가 아니다.

**`var x = 0;` 이 문제가 되는 상황**

- `int` 로 굳는다. 나중에 큰 값을 담게 되면 **조용히 오버플로**한다.
- 의도가 `long` 이면 `var x = 0L;` 로 리터럴에 적는다 — `var` 는 오른쪽만 보기 때문에 **오른쪽에 의도를 적어야** 한다.
- 오버플로의 정본은 [`../02-numeric-operations/`](../02-numeric-operations/).

### 12. 다른 주제와 잇기

**`final var` 와 effectively final**

- **서로 다른 축이다.** `var` 는 "타입을 누가 적나", `final` 은 "재대입이 되나".
- `final var x = 1;` 은 둘을 동시에 쓰는 것이고, 이때 `x` 는 당연히 effectively final 이기도 하다.
- `var x = 1;` 만 쓰고 재대입을 안 하면 **`final` 을 안 붙여도 effectively final** 이라 람다에 캡처된다.
- 정본은 [`../03-variables-and-assignment/`](../03-variables-and-assignment/).

**`var f = () -> ...` 가 막힐 때 적어야 하는 것**

- **함수형 인터페이스 이름**이다 — `Runnable`, `Supplier<String>`, `Function<String,Integer>` 등.
- 시그니처에 맞는 표준 인터페이스를 고르는 법은 [`../31-functional-interfaces/`](../31-functional-interfaces/) 가 정본이다.
- 대안으로 **대상 타입이 있는 자리로 옮기는 것**도 된다 — 변수에 담지 말고 메서드 인자로 바로 넘긴다.

**`var` 가 붙잡을 수 있는 "손으로 못 적는 타입" 둘**

| 타입 | 언제 나오나 | 컴파일러가 부르는 이름 |
|---|---|---|
| 익명 클래스 타입 | `new Object() { ... }` | `<anonymous Object>` |
| 교집합 타입 | 삼항 연산자의 두 갈래를 합칠 때 | `INT#1 extends Object,Serializable,Comparable<...>` |

- 둘 다 **반환 타입·필드에는 못 쓰므로 그 메서드 안에서만 산다.**
- 익명 클래스 자체의 정본은 [`../12-nested-classes/`](../12-nested-classes/).

---

## 이 주제를 확인한 실행 목록

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Ex.java (04-a)` | 기본 추론·다이아몬드·익명 클래스·`final` 아님·허용 자리 여섯·삼항 | 17 · 21 · 25 (출력 동일) |
| `Ex.java (04-b)` `javap -c -p -l` · `javap -v -p` | `var` 와 명시 타입의 바이트코드 동일, `LocalVariableTable`/`LocalVariableTypeTable` 에 박힌 추론 결과 | 21 |
| `Ex.java (04-c1)` `javac` | `Void` 대입으로 `int`·`long`·`String` 확인 | 17 · 21 · 25 (문구 동일) |
| `Ex.java (04-c2)` `javac` | `ArrayList<Object>`·`ArrayList<String>`·`<anonymous Object>`·`long`·`int[]` 확인 | 17 · 21 · 25 (문구 동일) |
| `Ex.java (04-c3)` `javac` | 필드·`static` 필드·파라미터·반환 타입 -> `'var' is not allowed here` | 21 |
| `Ex.java (04-e1)` `javac` | `var x = null` -> `(variable initializer is 'null')` | 17 · 21 · 25 (문구 동일) |
| `Ex.java (04-e2)` `javac` | 초기화 없음 -> `(cannot use 'var' on variable without initializer)` | 17 · 21 · 25 (문구 동일) |
| `Ex.java (04-e3)` `javac` | 배열 초기화 축약 -> `(array initializer needs an explicit target-type)` | 17 · 21 · 25 (문구 동일) |
| `Ex.java (04-e4)` `javac` | 람다 -> `(lambda expression needs an explicit target-type)` | 17 · 21 · 25 (문구 동일) |
| `Ex.java (04-e5)` `javac` | 메서드 참조 -> `(method reference needs an explicit target-type)` | 17 · 21 · 25 (문구 동일) |
| `Ex.java (04-e6)` `javac` | `catch (var e)` -> `'var' is not allowed here` | 21 |
| `Ex.java (04-e7)` `javac` | `new ArrayList<var>()` -> `'var' is not allowed here` | 21 |
| `Ex.java (04-f1)` `javac` | `(var x, y)` -> `(cannot mix 'var' and implicitly-typed parameters)` | 17 · 21 · 25 (문구 동일) |
| `Ex.java (04-f2)` `javac` | `(var x, Integer y)` -> `(cannot mix 'var' and explicitly-typed parameters)` | 17 · 21 · 25 (문구 동일) |
| `Ex.java (04-f3)` `javac` | `var x -> ...` -> 파서 에러 2건 | 21 |
| `Ex.java (04-f4)` `javac` | 자기 참조 -> `(cannot use 'var' on self-referencing variable)` | 17 · 21 · 25 (문구 동일) |
| `Ex.java (04-g1)` | `int var = 3; var x = var + 1;` 이 컴파일·실행됨 | 21 |
| `Ex.java (04-g2)` `javac` | `class var { }` -> `restricted type name` | 21 |
| `Ex.java (04-g3)` `javac --release 10/11` | 람다 파라미터 `var` 는 11부터 | 21 의 javac |
| `Ex.java (04-h)` `javac` | `List<Object>`·`INT#1`(교집합)·`byte`·`int`·`int` 확인 | 17 · 21 · 25 (문구 동일) |
| `Ex.java (04-i)` `javac` | `typed.add(42)` -> `int cannot be converted to String` | 17 · 21 · 25 (문구 동일) |
| `Ex.java (04-j)` `javac` | `Object anon2` 에서 `anon2.count` -> `cannot find symbol` | 17 · 21 · 25 (문구 동일) |
| `Ex.java (04-k)` `javac` | `var x = 1; x = "hi";` -> `String cannot be converted to int` | 17 · 21 · 25 (문구 동일) |
| `Ex.java (04-m)` | `char c = 'a' + 1` 은 `b`, `var v = 'a' + 1` 은 `98` | 21 |

**구현 의존 항목** — javac 의 에러 문구(`cannot infer type for local variable`·괄호 안 이유·`<anonymous Object>`·`INT#1`),
`LocalVariableTable` 의 존재 여부(`-g` 옵션), 익명 클래스 이름 `Ex$1`, 두 메서드의 바이트코드가 동일하다는 것 —
전부 **javac 의 구현 세부**다. 버전이 올라 달라질 수 있으므로 그때 다시 찍는다.\
반면 "지역 변수에만 쓸 수 있다"·"`null` 로는 추론할 수 없다"·"대상 타입이 필요한 식은 못 쓴다"는 **JLS §14.4.1 이 보장**한다.
