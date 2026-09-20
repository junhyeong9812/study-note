# java/syntax/30 — 메서드 참조 네 형태 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **선행** — [`../29-lambda-expressions/`](../29-lambda-expressions/). 람다가 무엇으로 컴파일되는지 먼저 본다.
> **기준 소스** — 이 머신의 `21.0.5-tem/lib/src.zip` 과 `javac`·`javap` 가 실제로 낸 출력.\
> [JLS SE 21 §15.13](https://docs.oracle.com/javase/specs/jls/se21/html/jls-15.html#jls-15.13) 은 이 작업에서 **본문을 열지 못했다** — 그래서 본문의 판정은 **컴파일러 에러와 역어셈블**만 근거로 삼았다.
> **실행 검증** — 이 문서의 모든 출력·에러·역어셈블은 Temurin **JDK 21.0.5** 에서 실제로 돌려 얻은 것이다.\
> 프로그램 17개를 **17.0.13 · 21.0.5 · 25.0.1** 세 JDK 에서 각각 돌렸고, `Ex.` 로 시작하는 출력은 전부 같았다.\
> (JDK 내부 프레임의 줄 번호만 달랐다. 「구현 세부사항 대 언어 보장」 참조.)
> **버전** — 메서드 참조는 **Java 8**. 이 주제에 21·25 에서 새로 생긴 문법은 없다.
> **범위** — 람다가 **무엇으로 컴파일되나**는 [`../29-lambda-expressions/`](../29-lambda-expressions/) 가 정본이다.\
> 여기는 **네 형태를 어떻게 읽고, 언제 람다보다 나쁜가**만 다룬다.
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**메서드 참조는 "그 일은 이미 있는 저 메서드가 한다"고 손가락으로 가리키는 것이다.**

네 형태는 **무엇을 가리키느냐**로 갈린다.

| 비유 | 실체 | 문법 |
|---|---|---|
| 부서 이름을 가리킨다 — 담당자가 따로 없다 | static 메서드 | `Type::staticM` |
| **이 사람**을 가리킨다 — 지금 이 사람으로 못 박는다 | 특정 객체의 인스턴스 메서드 | `obj::instanceM` |
| **직책**을 가리킨다 — 맡을 사람은 나중에 온다 | 수신 객체가 첫 인자로 오는 인스턴스 메서드 | `Type::instanceM` |
| 새로 뽑아서 시킨다 | 생성자 | `Type::new` |
| 상자를 새로 짠다 | 배열 생성자 | `int[]::new` |

```text
       obj::instanceM                          Type::instanceM

  "김씨가 길이를 잰다"                      "맡은 사람이 길이를 잰다"
        |                                          |
  김씨는 지금 정해진다                       맡을 사람은 부를 때 정해진다
        |                                          |
  Supplier<Integer>                          Function<String, Integer>
  s.get()          인자 0개                  f.apply("abcde")   인자 1개
        |                                          |
  받는 인자에 수신 객체가 없다                받는 첫 인자가 수신 객체다
```

**똑같은 구조로** Java 가 이렇게 동작한다 — `"고정"::length` 는 인자가 없고, `String::length` 는 인자가 하나다.\
같은 `length` 를 가리키는데 **함수 모양이 다르다.**

실무에서 이게 값을 내는 자리는 **스트림의 `map`·`comparing`** 이다.\
`map(String::toUpperCase)` 가 `map(s -> s.toUpperCase())` 보다 짧고, **스택트레이스에 진짜 이름이 뜬다**([`../29-lambda-expressions/`](../29-lambda-expressions/) 「어디서 틀리나」 5번).

> **메서드 참조(method reference)** — 람다 대신 이미 있는 메서드를 그대로 가리키는 식. `수신자::메서드이름` 꼴이다.\
> 예: `s -> s.length()` 를 `String::length` 로 줄여 쓴다.

> **수신 객체(receiver)** — 인스턴스 메서드를 부를 때 점 앞에 오는 객체.\
> 예: `"abc".length()` 에서 `"abc"` 가 수신 객체다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. 같은 메서드를 가리키는 두 형태(`obj::m` 과 `Type::m`)가 **왜 다른 함수 타입**이 되나.
2. 어떤 람다가 메서드 참조로 **안 바뀌나** — 그리고 **바뀌면 안 되나.**
3. 컴파일러는 메서드 참조를 **무엇으로 바꾸나** — 람다와 같은가.

## 동작 방식

### (1) 네 형태를 한 프로그램에서

**언제 쓰나** — 코드에서 `::` 를 만났을 때 어느 형태인지 판별할 때.

**입력 코드** (`Ex.java (30-a)`)

```java
static int twice(int n) { return n * 2; }           // static 메서드
String greet(String who) { return "안녕 " + who; }  // 인스턴스 메서드

Ex me = new Ex();

IntUnaryOperator f1 = Ex::twice;                    // 형태 1
Function<String, String> f2 = me::greet;            // 형태 2
Function<String, Integer> f3 = String::length;      // 형태 3
BiFunction<Ex, String, String> f3b = Ex::greet;     // 형태 3 (내 클래스로)
Supplier<ArrayList<String>> f4 = ArrayList::new;    // 형태 4
Function<String, StringBuilder> f4b = StringBuilder::new;
```

**실행 결과** (17 · 21 · 25 동일)

```text
1) Ex::twice          42
2) me::greet          안녕 자바
3) String::length     5
3) Ex::greet          안녕 파이썬
4) ArrayList::new     []
4) StringBuilder::new 씨앗
+) this::toString     [내가 재정의한 toString]
+) super::toString    [Ex@...]
```

```text
형태 1  Ex::twice          (int) -> int            수신 객체 없음
형태 2  me::greet          (String) -> String      수신 객체 = me (고정)
형태 3  String::length     (String) -> Integer     수신 객체 = 첫 인자
형태 3  Ex::greet          (Ex, String) -> String  수신 객체 = 첫 인자
형태 4  ArrayList::new     () -> ArrayList         새 객체를 만든다
```

그림 해설 (한 단계씩):

- 형태 1은 가장 단순하다 — **메서드 시그니처가 그대로 함수 모양**이 된다.
- 형태 2도 그렇다 — `greet(String)` 이 `(String) -> String` 이다. **`me` 는 이미 정해져 있다.**
- 형태 3에서 **인자가 하나 늘어난다.** `greet(String)` 이 `(Ex, String) -> String` 이 됐다.
- 형태 4는 인자가 생성자 인자 그대로이고, **반환 타입이 그 클래스**다.
- `this::m`·`super::m` 도 형태 2다. `super::toString` 이 재정의를 건너뛴 것에 주의한다(「더 들어가면」).

비용 — 형태 자체에는 비용 차이가 없다. 형태 2만 **수신 객체를 붙잡는다**((3) 참조).

### (2) ★ 셋째 형태 — 수신 객체가 첫 인자로 들어간다

**언제 쓰나** — `String::length` 가 왜 `Function<String,Integer>` 인지 설명해야 할 때. 인자 개수가 안 맞을 때.

**실행 결과** (`Ex.java (30-b)`)

```text
묶인  fixed::length    -> 9
안묶인 String::length  -> 5
  같은 람다로 쓰면     -> 5
안묶인 String::startsWith("ab","a") -> true
안묶인 String::equalsIgnoreCase -> true
String::compareTo 정렬  -> [가, 나, 다]
naturalOrder 정렬       -> [가, 나, 다]
Integer::compare  (3,1) -> 1
Integer::compareTo(3,1) -> 1
```

```text
메서드 선언          String.length()              String.startsWith(String)
                     인자 0개                      인자 1개
                          |                              |
  obj::m  (묶인다)   Supplier<Integer>            Predicate<String>
                     인자 0개                      인자 1개
                     수신 객체는 이미 있다          수신 객체는 이미 있다
                          |                              |
  Type::m (안 묶인다) Function<String,Integer>     BiFunction<String,String,Boolean>
                     인자 1개  <- 하나 늘었다       인자 2개  <- 하나 늘었다
                     첫 인자가 수신 객체            첫 인자가 수신 객체
```

그림 해설 (한 단계씩):

- **같은 메서드인데 두 형태가 함수 모양을 다르게 만든다.**
- 형태 3은 **인자가 항상 하나 더 많다.** 그 첫 인자가 수신 객체다.
- `fixed::length` 는 9(`"고정된 수신 객체"` 의 길이), `String::length` 에 `"abcde"` 를 넣으면 5다.\
  **같은 `length` 인데 무엇을 재는지가 다르다.**
- 읽는 요령: **`Type::m` 을 보면 `(그 Type 하나, 그리고 m 의 인자들)` 로 읽는다.**
- `Integer::compare` 와 `Integer::compareTo` 가 **같은 `Comparator<Integer>` 가 되는 것**이 이 규칙의 결정적 예다.\
  앞은 static `compare(int,int)` — 인자 2개 그대로.\
  뒤는 인스턴스 `compareTo(Integer)` — 인자 1개인데 수신 객체가 붙어 2개.
- 그래서 **형태 1과 형태 3은 겉모양이 같다.** `Type::m` 하나로는 어느 쪽인지 알 수 없고, 컴파일러가 메서드를 찾아 정한다.\
  둘 다 맞으면 컴파일 에러다(「어디서 틀리나」 2번).

비용 — 없다. 다만 **읽는 사람이 인자 개수를 세어야 한다** — 형태 3이 헷갈리는 이유가 이것이다.

### (3) ★ `obj::m` 은 그 순간의 `obj` 를 평가한다

**언제 쓰나** — 메서드 참조가 `null` 로 터질 때. 나중에 바뀐 값이 안 보일 때.

**실행 결과** (`Ex.java (30-c)` · `Ex.` 프레임은 17 · 21 · 25 동일)

```text
== 1. 람다는 부를 때 평가한다 ==
  람다를 만들었다 — 아직 아무 일도 없다
  이제 부른다 -> 5

== 2. obj::m 은 만들 때 obj 를 평가한다 ==
  target 은 지금 "훨씬 더 긴 나중 값" (11자)
  그런데 ref.get() -> 4  <- 붙잡은 것은 "처음 값"

== 3. obj 가 null 이면 그 자리에서 터진다 ==
  java.lang.NullPointerException
  메시지: null
  at java.base/java.util.Objects.requireNonNull(Objects.java:233)
  at Ex.main(Ex.java:25)

== 4. 같은 일을 람다로 쓰면 ==
  만드는 것은 성공한다 (target 이 null 이어도)
  터지는 것은 get() 을 부를 때: at Ex.lambda$main$1(Ex.java:35)
```

```text
  Supplier<Integer> ref = target::length;      Supplier<Integer> lazy = () -> target.length();

  이 줄에서 target 을 읽는다                    이 줄에서는 아무것도 안 읽는다
        |                                             |
  null 이면 여기서 NPE                          null 이어도 여기는 통과
  값이면 그 값을 붙잡는다                        나중에 target 을 바꾸면 바뀐 값을 본다
        |                                             |
  at Ex.main(Ex.java:25)                        at Ex.lambda$main$1(Ex.java:35)
  참조를 만든 줄                                 람다를 부른 줄
```

그림 해설 (한 단계씩):

- 2번에서 `target` 을 더 긴 값으로 바꿨는데 `ref.get()` 은 **여전히 4** 다.\
  참조를 만들 때의 `"처음 값"`(4자)을 붙잡았기 때문이다.
- 3번에서 **`boom` 을 한 번도 안 불렀는데** NPE 가 났다. 스택트레이스가 `Ex.main(Ex.java:25)` — **참조를 만든 줄**이다.
- 4번의 람다는 정반대다 — 만들 때는 통과하고 **`get()` 을 부를 때** 터진다.
- 근거는 바이트코드에 그대로 있다.

**역어셈블** (`javap -c -p Ex.class` · `target::length` 자리)

```text
      66: getstatic     #29                 // Field target:Ljava/lang/String;
      69: dup
      70: invokestatic  #56                 // Method java/util/Objects.requireNonNull:(Ljava/lang/Object;)Ljava/lang/Object;
      73: pop
      74: invokedynamic #62,  0             // InvokeDynamic #2:get:(Ljava/lang/String;)Ljava/util/function/Supplier;
```

- 컴파일러가 **`Objects.requireNonNull` 을 직접 끼워 넣었다.**
- 그 다음 `invokedynamic ... (Ljava/lang/String;)` 으로 그 값을 **캡처**한다.
- 즉 `obj::m` 은 「`obj` 를 읽고 → `null` 검사하고 → 캡처」다. 그 셋이 **참조를 만드는 줄에서** 일어난다.

**같은 자리에 둘을 나란히 두면** (`Ex.java (30-h)` · 17 · 21 · 25 동일)

```text
메서드 참조 ref.get() = 4
람다      lam.get() = 11
```

- `target` 을 `"처음 값"`(4자)으로 둔 채 둘을 만들고, `"훨씬 더 긴 나중 값"`(11자)으로 바꾼 뒤 불렀다.
- **같은 프로그램의 같은 시점**인데 답이 다르다. 차이는 오직 **평가 시점**이다.

비용 — 참조를 만드는 순간의 비용이다. `obj` 가 비싼 식이면 **그 자리에서 한 번** 평가된다.\
반대로 매번 다시 평가하고 싶으면 **람다를 써야 한다.** 이것이 메서드 참조가 람다보다 나쁜 대표적 자리다.

> **캡처(capture)** — 함수 객체를 만들 때 바깥 값을 안으로 가져오는 것.\
> 예: `obj::m` 은 `obj` 를 캡처한다. 그래서 `obj` 를 읽는 시점이 참조를 만드는 시점이 된다.

### (4) 배열 생성자 참조 — 길이를 받아 배열을 만든다

**언제 쓰나** — `toArray(String[]::new)` 를 만났을 때. 제네릭 코드에서 배열이 필요할 때.

**실행 결과** (`Ex.java (30-d)` · 17 · 21 · 25 동일)

```text
int[]::new    apply(3) -> [0, 0, 0]
String[]::new apply(2) -> [null, null]
int[][]::new  apply(2) -> [null, null]
toArray(String[]::new) -> [가, 나, 다] / 타입 String[]
toArray()              -> 타입 Object[]
n -> new String[n]     -> [null, null]
ArrayList::new 0인자 -> []
ArrayList::new 1인자(int) -> []
ArrayList::new 1인자(Collection) -> [가]
```

```text
  int[]::new            n -> new int[n]           IntFunction<int[]>
  String[]::new         n -> new String[n]        IntFunction<String[]>
  int[][]::new          n -> new int[n][]         IntFunction<int[][]>
                                                   바깥 차원만 만든다
```

그림 해설 (한 단계씩):

- 배열 생성자 참조는 **언제나 `int` 하나를 받는다.** 그 값이 길이다.
- 원소는 **기본값**으로 채워진다 — `int` 는 0, 참조는 `null`.
- 2차원은 **바깥 차원만** 만든다. `[null, null]` 이 그 증거다.
- `toArray()` 는 `Object[]` 를, `toArray(String[]::new)` 는 `String[]` 를 준다.\
  **`String[]` 로 받아야 할 때 이 형태가 필요하다.** 캐스트로는 안 된다 — 던져 봤다.

**실행 결과** (`Ex.java (30-l)` · 17 · 21 · 25 동일)

```text
toArray() 의 런타임 타입 = [Ljava.lang.Object;
ClassCastException: class [Ljava.lang.Object; cannot be cast to class [Ljava.lang.String; ([Ljava.lang.Object; and [Ljava.lang.String; are in module java.base of loader 'bootstrap')
toArray(String[]::new) = [가, 나] / [Ljava.lang.String;
```

- `(String[]) stream.toArray()` 는 **컴파일은 되고 런타임에 `ClassCastException`** 이다.
- 배열은 원소가 아니라 **배열 자체의 타입**이 `Object[]` 라 캐스트가 실패한다.
- 생성자 참조는 **인자 개수와 타입으로 오버로드가 갈린다.**\
  `ArrayList::new` 하나가 `Supplier`·`IntFunction`·`Function<Collection,...>` 셋 다 된다.\
  마지막 것만 `[가]` 가 나온 것이 그 증거다 — `IntFunction` 쪽은 용량 10을 준 빈 리스트다.

비용 — `toArray(String[]::new)` 는 원소 수만큼의 배열을 한 번 만든다.\
`toArray()` 뒤에 캐스트하는 것보다 안전하다(런타임 `ArrayStoreException` 을 피한다).

### (5) 컴파일러는 메서드 참조를 람다와 다르게 바꾼다

**언제 쓰나** — 「메서드 참조는 람다의 짧은 문법」이라고 알고 있을 때.

**입력 코드** (`Ex.java (30-f)`)

```java
Function<String, Integer> byRef    = String::length;     // 메서드 참조
Function<String, Integer> byLambda = s -> s.length();    // 같은 일을 하는 람다
IntFunction<String[]> arrRef       = String[]::new;      // 배열 생성자 참조
Supplier<StringBuilder> ctorRef    = StringBuilder::new; // 생성자 참조
```

**역어셈블** (`javap -p Ex.class` — 합성 메서드만)

```text
public class Ex {
  public Ex();
  public static void main(java.lang.String[]);
  private static java.lang.String[] lambda$main$1(int);
  private static java.lang.Integer lambda$main$0(java.lang.String);
}
```

```text
함수 객체 4개를 만들었는데 합성 메서드는 2개다.

  String::length      -> 합성 메서드 없음
  s -> s.length()     -> lambda$main$0  있음
  String[]::new       -> lambda$main$1  있음
  StringBuilder::new  -> 합성 메서드 없음
```

**역어셈블** (`javap -v -p Ex.class` 의 `BootstrapMethods` — 각 항의 두 번째 인자만)

```text
  0:  #86 REF_invokeVirtual java/lang/String.length:()I
  1:  #88 REF_invokeStatic Ex.lambda$main$0:(Ljava/lang/String;)Ljava/lang/Integer;
  2:  #92 REF_invokeStatic Ex.lambda$main$1:(I)[Ljava/lang/String;
  3:  #97 REF_newInvokeSpecial java/lang/StringBuilder."<init>":()V
```

그림 해설 (한 단계씩):

- **메서드 참조는 진짜 메서드를 바로 가리킨다** — `REF_invokeVirtual java/lang/String.length`.
- 같은 일을 하는 **람다는 합성 메서드를 하나 만든다** — `REF_invokeStatic Ex.lambda$main$0`.
- 생성자 참조도 바로 가리킨다 — `REF_newInvokeSpecial ... "<init>"`.
- **배열 생성자 참조만 합성 메서드를 만든다.** `new String[n]` 에 대응하는 진짜 메서드가 없기 때문이다.
- 이것이 [`../29-lambda-expressions/`](../29-lambda-expressions/) 7번의 스택트레이스 차이를 만든다 —\
  메서드 참조는 `Ex.boom` 이 뜨고 람다는 `Ex.lambda$main$0` 이 뜬다.

비용 — 메서드 참조는 합성 메서드가 하나 덜 생긴다. 실행 성능 차이를 이 문서는 **측정하지 않았다.**\
값은 성능이 아니라 **스택트레이스와 읽기 쉬움**에 있다.

### (6) 묶인 참조와 안 묶인 참조는 같은 메서드 핸들을 쓴다

**언제 쓰나** — (2)와 (3)이 같은 이야기인지 다른 이야기인지 정리할 때.

**역어셈블** (`Ex.java (30-g)` · `javap -v -p Ex.class`)

```text
  0: ... LambdaMetafactory.metafactory ...
    Method arguments:
      #65 ()Ljava/lang/Object;
      #66 REF_invokeVirtual java/lang/String.length:()I
      #71 ()Ljava/lang/Integer;
  1: ... LambdaMetafactory.metafactory ...
    Method arguments:
      #73 (Ljava/lang/Object;)Ljava/lang/Object;
      #66 REF_invokeVirtual java/lang/String.length:()I
      #74 (Ljava/lang/String;)Ljava/lang/Integer;
```

```text
  fixed::length  (묶인다)                    String::length  (안 묶인다)

  같은 메서드 핸들 #66 을 쓴다                같은 메서드 핸들 #66 을 쓴다
        |                                          |
  호출 자리: get:(Ljava/lang/String;)        호출 자리: apply:()
  수신 객체를 캡처해 넘긴다                    캡처하는 것이 없다
        |                                          |
  함수 모양: () -> Integer                    함수 모양: (String) -> Integer
        |                                          |
  앞에 requireNonNull 이 있다                 없다
```

그림 해설 (한 단계씩):

- 두 항의 **두 번째 인자가 같다** — `#66 REF_invokeVirtual java/lang/String.length:()I`.\
  같은 메서드를 가리키고 있다.
- 다른 것은 **첫째·셋째 인자(함수 모양)와 호출 자리의 서술자**다.
- 묶인 쪽만 호출 자리에 `(Ljava/lang/String;)` 이 있다 — **수신 객체를 캡처해 넘긴다.**
- 안 묶인 쪽은 캡처가 없고, 대신 **부를 때 인자로 받은 것을 수신 객체로 쓴다.**
- 그래서 (2)의 「인자가 하나 늘어난다」와 (3)의 「그 순간의 `obj` 를 평가한다」는 **같은 사실의 두 면**이다.

비용 — 묶인 참조는 캡처가 있으므로 **객체가 하나 후보로 생긴다.**\
안 묶인 참조는 캡처가 없어 재사용될 수 있다([`../29-lambda-expressions/`](../29-lambda-expressions/) (6)).

## 문법 — 형태와 규칙

직접 쓴 최소 예제다. 출력은 전부 실행 결과다.

### 네 형태 한 표

| 형태 | 문법 | 대응 람다 | 함수의 인자 |
|---|---|---|---|
| 1. static | `Type::staticM` | `(a, b) -> Type.staticM(a, b)` | 메서드 인자 그대로 |
| 2. 묶인 인스턴스 | `obj::instanceM` | `(a) -> obj.instanceM(a)` | 메서드 인자 그대로 |
| 3. 안 묶인 인스턴스 | `Type::instanceM` | `(recv, a) -> recv.instanceM(a)` | **수신 객체 + 메서드 인자** |
| 4. 생성자 | `Type::new` | `(a) -> new Type(a)` | 생성자 인자 그대로 |
| 4'. 배열 생성자 | `Type[]::new` | `n -> new Type[n]` | **`int` 하나(길이)** |

- 형태 2의 변형으로 **`this::m`** 과 **`super::m`** 이 있다.
- 형태 1과 형태 3은 **겉모양이 같다**(`Type::m`). 컴파일러가 메서드를 찾아 정한다.

### 어떤 람다가 메서드 참조가 되나

```java
s -> s.length()              // String::length          된다
s -> s.trim().length()       //                          안 된다 (두 단계)
(a, b) -> a + b              //                          안 된다 (연산자는 메서드가 아니다)
x -> Math.abs(x)             // Math::abs               된다
x -> foo(x, 1)               //                          안 된다 (고정 인자가 있다)
() -> new ArrayList<>()      // ArrayList::new          된다
n -> new String[n]           // String[]::new           된다
x -> x                       // Function.identity()     메서드 참조는 아니지만 표준 것이 있다
```

- 규칙 한 줄: **람다 본문이 「메서드 하나를 그 인자들로 그대로 부르는 것」이면 된다.**
- 인자 순서를 바꾸거나, 인자를 더하거나, 결과에 뭘 하면 안 된다.

**억지로 써 보면 무엇이 나오나** — 세 경우를 던져 봤다(17 · 21 · 25 동일).

**두 단계를 이어 쓰려는 시도** (`Ex.java (30-i)`)

```text
Ex.java:4: error: method reference not expected here
        Function<String,Integer> a = String::trim::length;   // 두 단계를 이어 쓰려는 시도
                                     ^
1 error
```

**인자 하나를 고정하려는 시도** (`Ex.java (30-j)`)

```text
Ex.java:5: error: incompatible types: invalid method reference
        IntUnaryOperator b = Ex::foo;     // 인자 하나를 고정하려는 시도
                             ^
    method foo in class Ex cannot be applied to given types
      required: int,int
      found:    int
      reason: actual and formal argument lists differ in length
1 error
```

**연산자를 가리키려는 시도** (`Ex.java (30-k)`)

```text
Ex.java:4: error: <identifier> expected
        IntBinaryOperator c = Integer::+;     // 연산자를 가리키려는 시도
                                       ^
Ex.java:4: error: illegal start of expression
        IntBinaryOperator c = Integer::+;     // 연산자를 가리키려는 시도
                                        ^
2 errors
```

- 셋의 메시지가 각각 다르다 — **`::` 는 두 번 못 쓰고, 인자 개수가 맞아야 하고, 뒤에는 이름만 온다.**
- 둘째 메시지가 특히 읽기 좋다. 「`required: int,int` / `found: int`」가 **인자 개수 문제**임을 바로 말해 준다.

### 형태 2와 형태 3을 구분해 읽는 법

```java
String fixed = "고정된 수신 객체";

Supplier<Integer>         bound   = fixed::length;    // 인자 0개
Function<String, Integer> unbound = String::length;   // 인자 1개
```

- 왼쪽이 **변수**면 형태 2(묶인다), **타입 이름**이면 형태 1 아니면 형태 3.
- 형태 3이면 **인자를 하나 더 세라.**
- 「`Type::m` 의 함수 모양 = `(Type, m 의 인자들) -> m 의 반환형`」 — 이 한 줄을 외운다.

## 어디서 틀리나

### 1. `Integer::toString` 을 쓴다

**컴파일 에러** (`Ex.java (30-e1)`)

```text
Ex.java:5: error: incompatible types: invalid method reference
        Function<Integer, String> f = Integer::toString;
                                      ^
    reference to toString is ambiguous
      both method toString(int) in Integer and method toString() in Integer match
1 error
```

- `Integer` 에는 **static `toString(int)`** 와 **인스턴스 `toString()`** 이 둘 다 있다.
- 형태 1로 읽으면 `(int) -> String`, 형태 3으로 읽어도 `(Integer) -> String` — **둘 다 맞는다.**
- 컴파일러는 고르지 않고 **거부한다.**
- 해결: `String::valueOf` 를 쓰거나 람다로 `i -> i.toString()` 을 쓴다.

### 2. static 과 인스턴스에 같은 이름이 있다

**컴파일되는 경우** (`Ex.java (30-e2)`)

```java
static String pick(String s) { return "static " + s; }
String pick() { return "instance"; }
interface F { String apply(Ex e); }

F f = Ex::pick;      // 출력: instance
```

**컴파일 에러가 나는 경우** (`Ex.java (30-e6)`)

```java
static String pick(Ex e) { return "static 쪽"; }    // static, 인자 Ex
String pick() { return "인스턴스 쪽"; }              // 인스턴스, 인자 없음
```

```text
Ex.java:8: error: incompatible types: invalid method reference
        F f = Ex::pick;      // 둘 다 (Ex) -> String 모양이 된다
              ^
    reference to pick is ambiguous
      both method pick(Ex) in Ex and method pick() in Ex match
1 error
```

```text
  둘 다 있어도 모양이 다르면                 둘 다 (Ex) -> String 이 되면

  static  pick(String)  ->  (String)->String    static  pick(Ex)  ->  (Ex)->String
  인스턴스 pick()       ->  (Ex)->String        인스턴스 pick()   ->  (Ex)->String
                |                                          |
  F 의 모양 (Ex)->String 과                     둘 다 맞는다
  맞는 것이 하나뿐 -> 뽑힌다                     -> 컴파일 에러
```

- 같은 이름의 static·인스턴스 메서드가 있는 것 자체는 문제가 아니다.
- **타깃 타입에 맞는 후보가 둘이 되는 순간** 에러다.
- 이것이 형태 1과 형태 3이 겉모양을 공유하는 대가다.

### 3. 타깃 타입이 없는 자리에 쓴다

**컴파일 에러** (`Ex.java (30-e3)`)

```text
Ex.java:3: error: incompatible types: Object is not a functional interface
        Object o = String::length;
                   ^
1 error
```

- 메서드 참조는 **혼자서는 타입이 없다.** 어떤 함수형 인터페이스가 될지 주변이 정한다.
- `var` 에도 못 쓴다 — 같은 이유다.
- 람다도 마찬가지다. 「타깃 타입이 필요하다」는 둘의 공통 성질이다.

### 4. 인터페이스나 추상 클래스로 `Type::new` 를 쓴다

**컴파일 에러** (`Ex.java (30-e4)`)

```text
Ex.java:6: error: List is abstract; cannot be instantiated
        Supplier<List<String>> s = List::new;
                                   ^
1 error
```

- 생성자 참조는 **진짜 생성자를 가리킨다.** 인터페이스에는 없다.
- `ArrayList::new` 처럼 구현체를 쓴다.
- 에러 메시지가 `new List<>()` 를 쓴 것과 같다 — 컴파일러가 그렇게 취급한다.

### 5. 제네릭 배열을 만들려 한다

**컴파일 에러** (`Ex.java (30-e5)`)

```text
Ex.java:5: error: generic array creation
        return T[]::new;              // 제네릭 배열 생성
                ^
1 error
```

- `T[]::new` 는 **안 된다.** 타입 소거 때문에 런타임에 `T` 를 모른다.
- 그래서 라이브러리가 `toArray(IntFunction<T[]>)` 처럼 **배열 생성자 참조를 받아** 우회한다.\
  호출하는 쪽에서 `String[]::new` 라고 구체 타입을 적어 주는 것이다.
- 이 제약의 정본은 목록의 **19번 주제**(타입 소거)다.

### 6. ★ `obj::m` 으로 써서 `null` 로 터진다

- (3)절에서 본 것 — **참조를 만드는 줄에서 NPE 가 난다.** 부르지도 않았는데 터진다.
- 실제 스택트레이스는 `Objects.requireNonNull` 과 **참조를 만든 줄**을 가리킨다.
- 흔한 형태: `Optional.map(cachedService::lookup)` 에서 `cachedService` 가 아직 `null` 인 경우.
- 해결: **람다로 바꾼다.** `x -> cachedService.lookup(x)` 는 부를 때 평가한다.
- 판단 규칙: **수신 객체가 나중에 바뀌거나 늦게 채워지면 람다다.**

### 7. 메서드 참조가 오버로드를 모호하게 만든다

**컴파일 에러** (`Ex.java (31-i)`)

```java
static void run(Consumer<String> c) { ... }
static void run(Predicate<String> p) { ... }

run(list::add);          // add 는 boolean 을 돌려준다 — 둘 다 맞는다
```

```text
Ex.java:10: error: reference to run is ambiguous
        run(list::add);          // add 는 boolean 을 돌려준다 — 둘 다 맞는다
        ^
  both method run(Consumer<String>) in Ex and method run(Predicate<String>) in Ex match
1 error
```

- `List.add` 는 `boolean` 을 돌려주므로 `Predicate` 가 되고, **반환값을 버리면** `Consumer` 도 된다.
- 오버로드가 둘 다 함수형 인터페이스를 받으면 **어느 쪽인지 정할 수 없다.**
- 해결: 캐스트로 못 박거나(`run((Consumer<String>) list::add)`), 오버로드 이름을 나눈다.
- 이 규칙의 정본은 [`../31-functional-interfaces/`](../31-functional-interfaces/) 「어디서 틀리나」다.

## 구현 세부사항 대 언어 보장

| 관찰한 것 | 보장인가 | 근거 |
|---|---|---|
| `obj::m` 이 `obj` 를 그 자리에서 평가한다 | **언어 규칙** | 실행 결과(값이 안 바뀐다 · 그 줄에서 NPE)로 관측된다. 세 JDK 동일 |
| 모호하면 컴파일 에러 | **언어 규칙** | `javac` 가 거부한다. 세 JDK 에서 같은 메시지 |
| 제네릭 배열 생성자 참조 금지 | **언어 규칙** | `javac` 가 거부한다 |
| `null` 검사가 `Objects.requireNonNull` 이다 | 구현 세부 | javac 가 고른 방식. 「그 자리에서 터진다」만 성질이다 |
| 메서드 참조가 합성 메서드를 안 만든다 | 구현 세부 | 배열 생성자 참조는 만든다 — 같은 컴파일러 안에서도 갈린다 |
| `REF_invokeVirtual`·`REF_newInvokeSpecial` 같은 핸들 종류 | 구현 세부 | 대상 메서드의 종류에 따라 정해진다 |

**실측 — 세 JDK 에서 달랐던 것**

| 무엇 | 17.0.13 | 21.0.5 | 25.0.1 |
|---|---|---|---|
| `Objects.requireNonNull` 프레임의 줄 번호 | `Objects.java:209` | `Objects.java:233` | `Objects.java:220` |
| `Ex.main(Ex.java:25)` 프레임 | 같다 | 같다 | 같다 |
| 나머지 출력 전부 | 같다 | 같다 | 같다 |

- **JDK 내부 파일의 줄 번호는 버전마다 바뀐다.** 스택트레이스를 문자열로 비교하는 테스트는 그래서 깨진다.
- **내 코드의 프레임(`Ex.main(Ex.java:25)`)은 셋 다 같았다.** 그 프레임이 이 절의 근거다.
- `javac --release 8` 로 다시 찍어도 (5)·(6)의 메서드 핸들 종류는 같았다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓰는 것 |
|---|---|
| 있는 메서드를 그대로 넘긴다 | **메서드 참조** — 스택트레이스에 진짜 이름이 뜬다 |
| 인자를 가공하거나 순서를 바꾼다 | **람다** (메서드 참조가 안 된다) |
| 수신 객체가 아직 `null` 이거나 나중에 바뀐다 | **람다** — `obj::m` 은 그 자리에서 평가한다 |
| 수신 객체를 지금 못 박고 싶다 | **`obj::m`** — 그 자리 평가가 오히려 장점이다 |
| 스트림 원소를 배열로 받는다 | **`Type[]::new`** — `toArray()` + 캐스트보다 안전하다 |
| 팩토리를 넘긴다 | **`Type::new`** |
| 오버로드가 여럿인 메서드를 가리킨다 | 모호하면 **람다** 또는 캐스트 |
| 본문이 서너 줄이다 | 메서드로 뽑고 **메서드 참조** |

판단 규칙 세 줄.

- **`Type::m` 을 만나면 인자를 하나 더 세라.** 그것이 셋째 형태다.
- **`obj::m` 은 그 줄에서 `obj` 를 읽는다.** 늦게 채워지는 것에 쓰지 않는다.
- **메서드 참조가 안 되면 억지로 만들지 않는다.** 람다가 읽기 쉬우면 람다다.

## 핵심 문장

- 네 형태는 `Type::staticM` · `obj::instanceM` · `Type::instanceM` · `Type::new` 이고, 배열 생성자 `Type[]::new` 가 따로 있다.
- **셋째 형태는 인자가 하나 더 많다** — 수신 객체가 첫 인자로 들어간다. `String::length` 가 `Function<String,Integer>` 인 이유다.
- 형태 1과 형태 3은 **겉모양이 같아서**(`Type::m`) 후보가 둘 되면 컴파일 에러다 — `Integer::toString` 이 그 예다.
- **`obj::m` 은 참조를 만드는 줄에서 `obj` 를 평가한다.** 바이트코드에 `Objects.requireNonNull` 이 끼어 있다 — `null` 이면 부르기도 전에 터진다.
- 메서드 참조는 **진짜 메서드를 바로 가리킨다**(합성 메서드 없음). 람다는 합성 메서드를 만든다. **배열 생성자 참조만 예외**다.
- 그래서 **스택트레이스에 진짜 이름이 뜬다** — 메서드 참조가 람다보다 나은 가장 실질적인 이유다.

## 관련 자료

- [`../29-lambda-expressions/`](../29-lambda-expressions/) — **이 주제의 선행.** 합성 메서드·캡처·스택트레이스의 정본
- [`../31-functional-interfaces/`](../31-functional-interfaces/) — 메서드 참조가 들어갈 **타입**을 고르는 지도. 오버로드 모호성의 정본
- [`../45-intermediate-operations/`](../45-intermediate-operations/) — `map(String::toUpperCase)` 처럼 실제로 쓰이는 자리
- [`../44-stream-creation/`](../44-stream-creation/) — `Stream.generate(Supplier)`·`toArray(IntFunction)` 가 이 형태를 받는다
- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 30번)
- [`../../../../../../history/java/java-8.md`](../../../../../../history/java/java-8.md) — 메서드 참조가 **왜 그때 들어왔나**. 설계 맥락은 **거기까지**, 여기는 **네 형태를 읽는 법부터**
- [`../../언어-특성/README.md`](../../언어-특성/README.md) — JIT·메서드 핸들 실행의 **JVM 내부는 거기**. 여기는 `javap` 로 보이는 **바이트코드 표면까지**
- [**08번 주제**](../08-method-declaration-overloading/)(메서드 선언 — 오버로딩 해소) — 「어디서 틀리나」 1·2·7번이 기대는 해소 규칙의 정본
- [**09번 주제**](../09-inheritance-overriding/)(상속과 오버라이딩) — `super::m` 이 디스패치를 건너뛰는 것의 배경
- 목록의 **19번 주제**(타입 소거) — 제네릭 배열 생성자 참조가 막히는 이유의 정본
- 목록의 **28번 주제**(`Comparator`) — `Integer::compare` 와 `Integer::compareTo` 가 둘 다 비교자가 되는 자리

## 용어 풀이

- **메서드 참조(method reference)** — 이미 있는 메서드를 그대로 가리키는 식. `수신자::메서드이름`.
- **수신 객체(receiver)** — 인스턴스 메서드를 부를 때 점 앞에 오는 객체.
- **묶인 참조(bound reference)** — `obj::m` — 수신 객체가 이미 정해진 참조.
- **안 묶인 참조(unbound reference)** — `Type::m` — 수신 객체를 첫 인자로 받는 참조.
- **타깃 타입(target type)** — 그 식이 무슨 타입이 되어야 하는지 정하는 주변 문맥.
- **생성자 참조(constructor reference)** — `Type::new` — 생성자를 가리키는 참조.
- **배열 생성자 참조** — `Type[]::new` — `int` 길이를 받아 배열을 만드는 참조.
- **메서드 핸들(method handle)** — 메서드를 가리키는 런타임 객체. `BootstrapMethods` 의 `REF_...` 항이 그것이다.
- **합성 메서드(synthetic method)** — 컴파일러가 만든 메서드. 람다 본문이 여기로 간다.
- **모호(ambiguous)** — 후보가 둘 이상이라 컴파일러가 하나를 고를 수 없는 상태. 에러다.

## 더 들어가면

- **`super::m` 은 디스패치를 건너뛴다.** `Ex.java (30-a)` 에서 같은 객체인데 결과가 갈렸다.

  ```text
  +) this::toString     [내가 재정의한 toString]
  +) super::toString    [Ex@...]
  ```

  `super.m()` 과 같은 규칙이다 — 재정의를 무시하고 부모 것을 부른다.\
  이 비대칭의 정본은 [**09번 주제**](../09-inheritance-overriding/)다.
- **`Comparator` 가 두 길로 만들어진다.** `String::compareTo`(형태 3, 인자 1→2)와 `Integer::compare`(형태 1, 인자 2)가\
  같은 `Comparator` 모양을 낸다. 정렬 결과도 같았다(`[가, 나, 다]`).\
  형태를 구분하지 못하면 **왜 둘 다 되는지** 설명할 수 없다.
- **생성자 참조는 오버로드를 타깃 타입으로 고른다.** `ArrayList::new` 하나가\
  `Supplier`(0인자)·`IntFunction`(용량)·`Function<Collection,...>`(복사) 셋으로 다 쓰였다.\
  실행 결과에서 마지막 것만 `[가]` 가 나온 것이 그 증거다.
- **메서드 참조는 `Optional`·`Stream` 에서 특히 잘 맞는다.**\
  `map(Type::method)`·`filter(Type::isX)`·`toArray(Type[]::new)`·`collect(..., ArrayList::new, ...)` 가 전부 이 네 형태다.\
  그 연산들의 계약은 [`../45-intermediate-operations/`](../45-intermediate-operations/) 이 정본이다.
