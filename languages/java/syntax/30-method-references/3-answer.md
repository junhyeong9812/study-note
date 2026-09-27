# java/syntax/30 — 메서드 참조 네 형태 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러·역어셈블은 **Temurin JDK 21.0.5 에서 실제로 돌려 얻은 것**이다.\
> 프로그램 17개를 17.0.13 · 21.0.5 · 25.0.1 에서 각각 돌렸다. **달랐던 것은 10번 답에 모아 두었다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 네 형태를 구분하라

**출력** (`Ex.java (30-a)` · 17 · 21 · 25 동일)

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

**각각 어느 형태인가**

| | 참조 | 형태 | 들어가는 타입 |
|---|---|---|---|
| (a) | `Ex::twice` | 1. static | `IntUnaryOperator` — `(int) -> int` |
| (b) | `me::greet` | 2. 묶인 인스턴스 | `Function<String,String>` — `(String) -> String` |
| (c) | `String::length` | 3. 안 묶인 인스턴스 | `Function<String,Integer>` — `(String) -> Integer` |
| (d) | `Ex::greet` | 3. 안 묶인 인스턴스 | `BiFunction<Ex,String,String>` — `(Ex, String) -> String` |
| (e) | `ArrayList::new` | 4. 생성자 | `Supplier<ArrayList<String>>` — `() -> ArrayList` |

**(b)와 (d)가 갈리는 이유**

- `greet` 의 선언은 `String greet(String who)` — **인자 하나**다.
- (b)는 **`me` 라는 수신 객체가 이미 정해져 있다.** 그래서 인자가 선언 그대로 하나다.
- (d)는 수신 객체가 **아직 없다.** 부를 때 인자로 받아야 한다 — 그래서 **인자가 둘**이 된다.

```text
  me::greet                                  Ex::greet

  수신 객체 = me (고정)                       수신 객체 = 첫 인자
  (String who) -> String                     (Ex recv, String who) -> String
  f2.apply("자바")                            f3b.apply(me, "파이썬")
```

**`this::m` 과 `super::m`**

- 둘 다 **형태 2**(묶인 인스턴스)다. 수신 객체가 각각 `this` 와 `super` 로 고정된다.
- `super::m` 은 **재정의를 건너뛴다** — 출력에서 `super::toString` 만 `Ex@...` 가 나왔다.\
  `super.m()` 과 같은 규칙이다([**09번 주제**](../09-inheritance-overriding/)).

### 2. 같은 `length` 인데 왜 다른가

**출력** (`Ex.java (30-b)`)

```text
묶인  fixed::length    -> 9
안묶인 String::length  -> 5
  같은 람다로 쓰면     -> 5
안묶인 String::startsWith("ab","a") -> true
안묶인 String::equalsIgnoreCase -> true
```

**왜 그런가**

- `9` 는 `"고정된 수신 객체"` 의 길이다 — **참조가 그 문자열을 붙잡고 있다.**
- `5` 는 `"abcde"` 의 길이다 — **부를 때 넘긴 것이 수신 객체가 됐다.**

**인자 개수**

- `fixed::length` — **0개.** `Supplier<Integer>` 다.
- `String::length` — **1개.** `Function<String,Integer>` 다.

**`String::startsWith`**

- 선언은 `boolean startsWith(String prefix)` — 인자 1개.
- 안 묶인 참조라 **인자가 둘**이 된다 — `BiFunction<String,String,Boolean>` 또는 `BiPredicate<String,String>`.
- 실행 결과에서 `apply("ab", "a")` 가 `true` 였다 — `"ab".startsWith("a")` 와 같다.

**한 줄 규칙**

> **`Type::m` 의 함수 모양 = `(Type, m 의 인자들) -> m 의 반환형`**

- 수신 객체가 **맨 앞에** 끼어든다.
- 이 한 줄이 셋째 형태를 읽는 전부다.

### 3. `Integer::compare` 와 `Integer::compareTo`

**출력** (`Ex.java (30-b)`)

```text
String::compareTo 정렬  -> [가, 나, 다]
naturalOrder 정렬       -> [가, 나, 다]
Integer::compare  (3,1) -> 1
Integer::compareTo(3,1) -> 1
```

**둘 다 `Comparator<Integer>` 가 되는가**

- **된다.** 그리고 `compare(3, 1)` 의 결과도 둘 다 `1` 로 같았다.

**각각 어느 형태인가**

- `Integer::compare` — **형태 1(static)**. 선언이 `static int compare(int x, int y)` 다.
- `Integer::compareTo` — **형태 3(안 묶인 인스턴스)**. 선언이 `int compareTo(Integer other)` 다.

**왜 둘 다 비교자가 되는가**

```text
  Comparator<Integer> 가 요구하는 모양:  (Integer, Integer) -> int

  Integer::compare     static compare(int, int)
                       인자 2개 그대로                    -> (Integer, Integer) -> int  ✔

  Integer::compareTo   인스턴스 compareTo(Integer)
                       인자 1개 + 수신 객체 1개           -> (Integer, Integer) -> int  ✔
```

- **도착 모양이 같다.** 가는 길이 다를 뿐이다.
- 이것이 「셋째 형태는 인자가 하나 더 많다」의 가장 좋은 연습 문제다.
- **겉모양(`Integer::이름`)만으로는 구분할 수 없다** — 메서드 선언을 봐야 한다.

**`String::compareTo` 와 `naturalOrder()`**

- **같았다.** 둘 다 `[가, 나, 다]` 였다.
- `Comparator.naturalOrder()` 는 내부적으로 `Comparable.compareTo` 를 쓰므로 같은 순서가 나온다.
- 비교자의 계약 자체는 [**28번 주제**](../28-comparable-comparator/)가 정본이다.

### 4. 배열 생성자 참조

**출력** (`Ex.java (30-d)` · 17 · 21 · 25 동일)

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

**세 출력**

- `[0, 0, 0]` — `int` 배열은 **0으로** 채워진다.
- `[null, null]` — 참조 배열은 **`null` 로** 채워진다.
- `[null, null]` — 2차원은 **바깥 차원만** 만든다. 안쪽 배열은 아직 없다.

**받는 인자**

- **`int` 하나.** 그것이 길이다.
- 그래서 타입이 언제나 `IntFunction<T[]>` 다. 대응 람다는 `n -> new T[n]`.

**런타임 타입**

- `arr` 는 **`String[]`**, `objs` 는 **`Object[]`**.
- `toArray()` 는 원소 타입을 모르므로 `Object[]` 를 줄 수밖에 없다.

**`toArray(String[]::new)` 를 쓰는 이유**

- **`String[]` 로 바로 받기 위해서**다. 캐스트로는 안 된다 — 던져 봤다.

**실행 결과** (`Ex.java (30-l)` · 17 · 21 · 25 동일)

```text
toArray() 의 런타임 타입 = [Ljava.lang.Object;
ClassCastException: class [Ljava.lang.Object; cannot be cast to class [Ljava.lang.String; ([Ljava.lang.Object; and [Ljava.lang.String; are in module java.base of loader 'bootstrap')
toArray(String[]::new) = [가, 나] / [Ljava.lang.String;
```

- `(String[]) stream.toArray()` 는 **컴파일은 되고 런타임에 터진다.** 원소가 전부 `String` 이어도 그렇다 —\
  실패하는 것은 원소가 아니라 **배열 자체의 타입**이다.
- 라이브러리가 배열을 만들 수 없어서(제네릭 배열 금지, 6번 (D)) **호출자에게 만드는 법을 받아 오는** 형태다.

### 5. 컴파일러는 메서드 참조를 무엇으로 바꾸나

**출력** (`Ex.java (30-f)` · `javap -p Ex.class`)

```text
public class Ex {
  public Ex();
  public static void main(java.lang.String[]);
  private static java.lang.String[] lambda$main$1(int);
  private static java.lang.Integer lambda$main$0(java.lang.String);
}
```

**합성 메서드는 몇 개인가**

- **두 개.** 함수 객체는 넷을 만들었는데 합성 메서드는 둘뿐이다.

**어떤 것이 만들고 어떤 것이 안 만드나**

```text
  String::length      ->  합성 메서드 없음
  s -> s.length()     ->  lambda$main$0(java.lang.String)   있음
  String[]::new       ->  lambda$main$1(int)                있음
  StringBuilder::new  ->  합성 메서드 없음
```

**`BootstrapMethods` 에서 `String::length` 가 가리키는 것**

```text
  0:  #86 REF_invokeVirtual java/lang/String.length:()I
  1:  #88 REF_invokeStatic Ex.lambda$main$0:(Ljava/lang/String;)Ljava/lang/Integer;
  2:  #92 REF_invokeStatic Ex.lambda$main$1:(I)[Ljava/lang/String;
  3:  #97 REF_newInvokeSpecial java/lang/StringBuilder."<init>":()V
```

- **`java.lang.String.length` 그 자체**다. 중간에 아무것도 없다.
- 람다는 `Ex.lambda$main$0` 이라는 **컴파일러가 만든 메서드**를 가리킨다.
- 생성자 참조는 `REF_newInvokeSpecial ... "<init>"` — 생성자를 바로 가리킨다.

**배열 생성자 참조만 합성 메서드가 생기는 이유**

- **`new String[n]` 에 대응하는 진짜 메서드가 없기 때문**이다.
- 배열 생성은 바이트코드 명령(`anewarray`)이지 메서드 호출이 아니다.
- 그래서 컴파일러가 그 명령을 감싼 메서드를 하나 만들어 가리킨다.

**스택트레이스에 어떻게 나타나나**

- [`../29-lambda-expressions/`](../29-lambda-expressions/) 7번의 실행 결과가 그대로 이 차이다.

```text
람다        ->  at Ex.lambda$main$0(Ex.java:9)
메서드 참조  ->  at Ex.boom(Ex.java:4)
```

- 메서드 참조 쪽은 **진짜 메서드 이름**이 뜬다. 로그에서 검색되고 리팩토링해도 따라간다.
- 이것이 메서드 참조를 고르는 가장 실질적인 이유다.

### 6. 어느 것이 컴파일 에러인가

**어느 것이 컴파일되나** (다섯 조각을 각각 따로 `javac` 에 넣어 본 결과다)

| | 결과 |
|---|---|
| (A) `Integer::toString` | 컴파일 에러 — 모호 |
| (B) `Object o = String::length` | 컴파일 에러 — 타깃 타입 아님 |
| (C) `List::new` | 컴파일 에러 — 추상 타입 |
| (D) `T[]::new` | 컴파일 에러 — 제네릭 배열 |
| (E) 후보가 둘인 `Ex::pick` | 컴파일 에러 — 모호 |

**컴파일되는 것**

- **없다.** 다섯 다 에러다.

**(A)의 에러 메시지** (`Ex.java (30-e1)`)

```text
Ex.java:5: error: incompatible types: invalid method reference
        Function<Integer, String> f = Integer::toString;
                                      ^
    reference to toString is ambiguous
      both method toString(int) in Integer and method toString() in Integer match
1 error
```

- `Integer` 에 **static `toString(int)`** 와 **인스턴스 `toString()`** 이 둘 다 있다.
- 형태 1로 읽어도 `(int) -> String`, 형태 3으로 읽어도 `(Integer) -> String` — **둘 다 맞는다.**
- 해결: `String::valueOf` 를 쓰거나 람다 `i -> i.toString()` 을 쓴다.

**(B)** (`Ex.java (30-e3)`)

```text
Ex.java:3: error: incompatible types: Object is not a functional interface
        Object o = String::length;
                   ^
1 error
```

- 메서드 참조에 없는 것은 **자기 타입**이다.
- 어떤 함수형 인터페이스가 될지는 **주변이 정한다**(타깃 타입). `Object` 는 함수형 인터페이스가 아니다.
- 그래서 `var` 에도 못 쓴다. 람다도 같다.

**(C)** (`Ex.java (30-e4)`)

```text
Ex.java:6: error: List is abstract; cannot be instantiated
        Supplier<List<String>> s = List::new;
                                   ^
1 error
```

- 「`List` 는 추상이라 인스턴스를 만들 수 없다」 — `new List<>()` 를 쓴 것과 같은 에러다.
- **생성자 참조는 진짜 생성자를 가리킨다.** 인터페이스에는 생성자가 없다.
- 해결: `ArrayList::new` 같은 구현체.

**(D)** (`Ex.java (30-e5)`)

```text
Ex.java:5: error: generic array creation
        return T[]::new;              // 제네릭 배열 생성
                ^
1 error
```

- **타입 소거** 때문이다. 런타임에 `T` 가 무엇인지 모르므로 그 배열을 만들 수 없다.
- 그래서 라이브러리가 `toArray(IntFunction<T[]>)` 처럼 **밖에서 받아 오는** 형태를 쓴다.
- 정본은 [**19번 주제**](../19-type-erasure/)다.

**(E)와 달리 컴파일되는 경우** (`Ex.java (30-e2)` 대 `(30-e6)`)

```text
(30-e6) static pick(Ex) + 인스턴스 pick()   ->  둘 다 (Ex)->String  ->  에러
Ex.java:8: error: incompatible types: invalid method reference
        F f = Ex::pick;
              ^
    reference to pick is ambiguous
      both method pick(Ex) in Ex and method pick() in Ex match

(30-e2) static pick(String) + 인스턴스 pick()  ->  모양이 다르다  ->  컴파일됨, 출력 "instance"
```

- 같은 이름의 static·인스턴스 메서드가 **있는 것 자체는 문제가 아니다.**
- **타깃 타입에 맞는 후보가 둘이 되는 순간** 에러다.
- (30-e2)에서는 `F.apply(Ex)` 에 맞는 것이 인스턴스 `pick()` 하나뿐이라 뽑혔다.

### 7. 이 코드는 무엇을 출력하나

**출력** (`Ex.java (30-c)` · `Ex.` 프레임은 17 · 21 · 25 동일)

```text
== 2. obj::m 은 만들 때 obj 를 평가한다 ==
  target 은 지금 "훨씬 더 긴 나중 값" (11자)
  그런데 ref.get() -> 4  <- 붙잡은 것은 "처음 값"
```

- **`4`** 다. 11이 아니다.

**왜 그런가**

- `obj::m` 은 **참조를 만드는 줄에서 `obj` 를 읽는다.**
- 그 시점의 `target` 은 `"처음 값"`(4자)이었다. 그 **값**을 캡처했다.
- 그 뒤에 `target` 을 바꿔도 이미 캡처된 것은 안 바뀐다.

**역어셈블** (`javap -c -p Ex.class` · `target::length` 자리)

```text
      66: getstatic     #29                 // Field target:Ljava/lang/String;
      69: dup
      70: invokestatic  #56                 // Method java/util/Objects.requireNonNull:(Ljava/lang/Object;)Ljava/lang/Object;
      73: pop
      74: invokedynamic #62,  0             // InvokeDynamic #2:get:(Ljava/lang/String;)Ljava/util/function/Supplier;
```

- `getstatic` 으로 **읽고**, `requireNonNull` 로 **검사하고**, `invokedynamic ... (Ljava/lang/String;)` 으로 **캡처한다.**
- 셋 다 참조를 만드는 줄에서 일어난다.

**람다로 바꾸면**

같은 자리에 둘을 나란히 두고 돌렸다 (`Ex.java (30-h)` · 17 · 21 · 25 동일).

```text
메서드 참조 ref.get() = 4
람다      lam.get() = 11
```

- **`11`** 이 나온다. 람다는 `get()` 을 부를 때 `target` 을 읽기 때문이다.
- 두 줄이 **같은 프로그램의 같은 시점**에서 나왔다 — 차이는 오직 평가 시점이다.

**`null` 이면 언제 터지나**

```text
== 3. obj 가 null 이면 그 자리에서 터진다 ==
  java.lang.NullPointerException
  메시지: null
  at java.base/java.util.Objects.requireNonNull(Objects.java:233)
  at Ex.main(Ex.java:25)

== 4. 같은 일을 람다로 쓰면 ==
  만드는 것은 성공한다 (target 이 null 이어도)
  터지는 것은 get() 을 부를 때: at Ex.lambda$main$1(Ex.java:35)
```

- **참조를 만드는 줄에서** 터진다. `get()` 을 한 번도 안 불렀는데 NPE 가 났다.
- 스택트레이스 맨 위 두 줄은 **`java.util.Objects.requireNonNull`** 과 **`Ex.main(Ex.java:25)`** 다.\
  25번 줄이 `Supplier<Integer> boom = target::length;` 다.
- 람다는 `Ex.lambda$main$1(Ex.java:35)` — **람다를 부른 줄**에서 터진다.
- 실무에서 흔한 형태: `Optional.map(service::lookup)` 에서 `service` 가 아직 주입되지 않은 경우.

### 8. 메서드 참조가 오버로드를 모호하게 만든다

**출력** (`Ex.java (31-i)`)

```text
Ex.java:10: error: reference to run is ambiguous
        run(list::add);          // add 는 boolean 을 돌려준다 — 둘 다 맞는다
        ^
  both method run(Consumer<String>) in Ex and method run(Predicate<String>) in Ex match
1 error
```

**컴파일되는가**

- **안 된다.**

**그 이유 — `List.add` 의 무엇 때문인가**

- `List.add(E)` 가 **`boolean` 을 돌려주기 때문**이다.
- 값을 돌려주므로 `Predicate<String>` 이 된다.
- 반환값을 **버리면** `Consumer<String>` 도 된다(void 호환).
- 그래서 오버로드 둘이 다 맞아 버린다.

```text
  list::add  ->  boolean add(String)

  Predicate<String>  (String) -> boolean      ✔ 그대로 맞는다
  Consumer<String>   (String) -> void         ✔ 반환값을 버리면 맞는다
        |
  둘 다 맞는다 -> 컴파일러가 고르지 않는다
```

**고치는 두 방법**

1. **캐스트로 못 박는다** — `run((Consumer<String>) list::add)`.
2. **오버로드 이름을 나눈다** — `runConsumer` / `runPredicate`.

덧붙여, 람다로 써도 같은 문제가 난다. 원인은 메서드 참조가 아니라 **오버로드 설계**다.\
해소 규칙 자체는 [**08번 주제**](../08-method-declaration-overloading/), 함수형 인터페이스 쪽 사정은 [`../31-functional-interfaces/`](../31-functional-interfaces/) 가 정본이다.

### 9. 람다로 써야 하는 자리

세 경우 다 **실제로 던져 본** 에러다(17 · 21 · 25 동일).

**`s -> s.trim().length()`** — `String::trim::length` 로 써 보면 (`Ex.java (30-i)`)

```text
Ex.java:4: error: method reference not expected here
        Function<String,Integer> a = String::trim::length;   // 두 단계를 이어 쓰려는 시도
                                     ^
1 error
```

- **안 된다.** 메서드를 **두 번** 부르기 때문이다. `::` 는 이어 쓸 수 없다.

**`x -> foo(x, 1)`** — `Ex::foo` 를 `IntUnaryOperator` 에 넣어 보면 (`Ex.java (30-j)`)

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

- **안 된다.** 메시지가 「`required: int,int` / `found: int`」로 **인자 개수**를 짚는다.
- 메서드 참조는 받은 인자를 그대로 넘기기만 한다. 고정값을 끼워 넣을 자리가 없다.

**`(a, b) -> a + b`** — `Integer::+` 로 써 보면 (`Ex.java (30-k)`)

```text
Ex.java:4: error: <identifier> expected
        IntBinaryOperator c = Integer::+;     // 연산자를 가리키려는 시도
                                       ^
Ex.java:4: error: illegal start of expression
        IntBinaryOperator c = Integer::+;     // 연산자를 가리키려는 시도
                                        ^
2 errors
```

- **안 된다.** `::` 뒤에는 **이름**만 온다 — 파서 단계에서 걸린다.
- 다만 `Integer::sum`·`Double::sum`·`String::concat` 처럼 **같은 일을 하는 메서드가 있으면** 그것을 쓴다.

**조건 한 줄**

> **람다 본문이 「메서드 하나를 그 인자들로, 순서 그대로, 가공 없이 부르는 것」이면 메서드 참조가 된다.**

**가능한데도 람다를 써야 하는 자리**

- **수신 객체가 아직 `null` 이거나 나중에 바뀔 때** — 7번이 그 경우다.\
  `obj::m` 은 그 줄에서 평가하므로 늦게 채워지는 필드에 쓰면 NPE 가 난다.
- **오버로드가 모호해질 때** — 8번.
- **읽는 사람이 인자를 세어야 할 때** — 형태 3이 여러 겹 쌓이면 람다가 낫다.

### 10. 세 JDK 에서 무엇이 달랐나

**달랐던 줄**

| | 17.0.13 | 21.0.5 | 25.0.1 |
|---|---|---|---|
| `requireNonNull` 프레임 | `Objects.java:209` | `Objects.java:233` | `Objects.java:220` |

**같았던 줄**

- **나머지 전부.** 특히 `at Ex.main(Ex.java:25)` 와 `at Ex.lambda$main$1(Ex.java:35)` 가 셋 다 같았다.
- `ref.get() -> 4` 도, 배열 생성자 참조의 출력도, 다섯 컴파일 에러 메시지도 전부 같았다.

**그래서 어떻게 비교해야 하나**

- **JDK 내부 프레임의 줄 번호를 비교하지 않는다.** 버전마다 바뀐다.
- 비교할 것은 **내 코드의 클래스·메서드·줄 번호**와 **예외 타입**이다.
- 스택트레이스를 문자열 통째로 단언하는 테스트는 JDK 를 올리면 깨진다.

**`requireNonNull` 은 보장인가**

- **구현 세부다.** javac 가 고른 방식이다.
- **성질**은 보장된다 — 「`obj::m` 은 그 자리에서 `obj` 를 평가하고, `null` 이면 그때 터진다」.
- 외울 것은 명령이나 메서드 이름이 아니라 **평가 시점**이다.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Ex.java (30-a)` | 네 형태 + `this::m`·`super::m` 의 실제 동작 | 17 · 21 · 25 (동일) |
| `Ex.java (30-b)` | 묶인/안 묶인 참조의 인자 개수, `startsWith`·`equalsIgnoreCase`, `compare` 대 `compareTo` | 17 · 21 · 25 (동일) |
| `Ex.java (30-c)` | `obj::m` 의 평가 시점, `null` NPE 위치, 람다와의 대비, `requireNonNull` 바이트코드 | 17 · 21 · 25 (**JDK 내부 줄 번호만 다름**) |
| `Ex.java (30-d)` | 배열 생성자 참조 3종, `toArray` 두 형태의 런타임 타입, `ArrayList::new` 오버로드 3종 | 17 · 21 · 25 (동일) |
| `Ex.java (30-e1)`~`(30-e6)` | `Integer::toString` 모호 · 타깃 타입 없음 · `List::new` · `T[]::new` · static/인스턴스 모호와 비모호 | 17 · 21 · 25 (동일) |
| `Ex.java (30-f)` | 메서드 참조 대 람다의 합성 메서드 유무, `BootstrapMethods` 의 핸들 종류 4종 | 17 · 21 · 25 (동일) |
| `Ex.java (30-g)` | 묶인/안 묶인 참조가 **같은 메서드 핸들**을 쓰고 호출 자리 서술자만 다름 | 21 |
| `Ex.java (30-h)` | 같은 자리의 메서드 참조(4)와 람다(11)를 나란히 — 평가 시점만 다름 | 17 · 21 · 25 (동일) |
| `Ex.java (30-i)` · `(30-j)` · `(30-k)` | 메서드 참조로 **못 쓰는** 세 경우의 실제 에러(두 단계 · 인자 고정 · 연산자) | 17 · 21 · 25 (동일) |
| `Ex.java (30-l)` | `(String[]) toArray()` 의 `ClassCastException`, `toArray(String[]::new)` 의 정상 타입 | 17 · 21 · 25 (동일) |
| `Ex.java (31-i)` | 메서드 참조가 `Consumer`/`Predicate` 오버로드를 모호하게 만듦 | 17 · 21 · 25 (동일) |
| `Ex.java (29-d)` | 람다·익명 클래스·메서드 참조의 스택트레이스 이름 대비 (29번과 공유) | 17 · 21 · 25 (`Ex.` 프레임 동일) |

**구현 의존 항목** — 버전이 오르면 다시 돌려야 하는 것

- 스택트레이스의 JDK 내부 줄 번호 — 세 버전에서 전부 달랐다.
- `Objects.requireNonNull` 삽입 — javac 가 고른 방식이다.
- 합성 메서드 이름(`lambda$main$0`) — 컴파일러가 정하는 구현 세부다.
- 메서드 핸들 종류(`REF_invokeVirtual` 등) — `javac --release 8` 에서도 같았지만 보장은 아니다.
