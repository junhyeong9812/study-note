# java/syntax/17 — 제네릭 선언: 타입 파라미터·바운드·제네릭 메서드 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러·바이트코드는 **Temurin JDK 21.0.5 에서 실제로 돌려 얻은 것**이다.\
> 실행 프로그램(`17-a`·`17-h`)은 **17.0.13 · 25.0.1** 에서도 돌렸고 출력이 한 글자도 다르지 않았다.\
> 컴파일 에러도 17 과 25 에서 `diff` 로 대조해 **문자 단위로 같았다.**\
> 바이트코드는 `javap -v -p` 출력을, 표준 라이브러리 시그니처는 `lib/src.zip` 의 실파일을 그대로 옮겼다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 타입 파라미터의 범위는 어디까지인가

**출력** (`Ex.java (17-a)`, JDK 21.0.5)

```text
--- 클래스 타입 파라미터
bs           = Box[hello]
bs.get()     = hello (캐스팅 없이 String)
map 후       = Box[5]  타입은 Box<Integer>
```

**왜 그런가**

```text
  class Box<T> {              <- T 의 범위는 클래스 전체
      T value;                   인스턴스를 만들 때 정해지고 그대로 간다
      T get() { ... }
      <U> Box<U> map(...)     <- U 의 범위는 이 메서드 안쪽뿐
  }                              호출할 때마다 새로 정해진다
```

- **`T`** 는 `new Box<String>("hello")` 하는 순간 `String` 으로 정해지고, 그 인스턴스가 사는 동안 고정이다.
- **`U`** 는 `map` 을 부를 때마다 **인자(`Function`)의 반환 타입에서 추론**된다.

**`bs.map(String::length)` 의 결과 타입** — `Box<Integer>` 다.\
`String::length` 가 `Function<String, Integer>` 이므로 `U = Integer` 가 된다. 출력의 `Box[5]` 가 그 확인이다.

**같은 객체에 `map` 을 두 번 다른 `U` 로 부를 수 있는가** — 있다.\
`U` 는 인스턴스 상태가 아니라 **호출 하나의 지역 개념**이기 때문이다.

**클래스에 둘지 메서드에 둘지의 기준**

| 조건 | 어디에 |
|---|---|
| 필드가 그 타입을 들고 있어야 한다 | 클래스 |
| 여러 메서드가 같은 타입을 주고받아야 한다 | 클래스 |
| 한 호출 안에서만 인자·반환의 관계가 성립한다 | 메서드 |
| `static` 이다 | 메서드 (2번 참조) |

한 문장으로 — "**이 타입이 인스턴스의 상태인가**"로 가른다.

### 2. `static` 이 클래스 타입 파라미터를 쓰면

**출력** (`Ex.java (17-b)` `javac`, JDK 21.0.5)

```text
Ex.java:6: error: non-static type variable T cannot be referenced from a static context
        static T shared;                       // (A) static 필드가 T 를 쓸 수 있나
               ^
Ex.java:7: error: non-static type variable T cannot be referenced from a static context
        static void putStatic(T t) { }         // (B) static 메서드가 T 를 쓸 수 있나
                              ^
Ex.java:8: error: non-static type variable T cannot be referenced from a static context
        static T getStatic() { return null; }  // (C) 반환 타입은?
               ^
3 errors
```

**왜 그런가**

- **(A)(B)(C) 세 자리가 에러**다. 필드든 파라미터든 반환 타입이든 상관없다.
- **(D) 인스턴스 메서드**는 통과한다 — 인스턴스가 있으니 `T` 의 값이 있다.
- **(E) `static <T> T ownParam(T t)`** 도 통과한다.

```text
왜 (E)만 되나

  static void putStatic(T t)        static <T> T ownParam(T t)
  +---------------------------+     +---------------------------+
  | T 는 클래스의 빈칸         |     | T 는 이 메서드가 새로 선언한 |
  |   -> 인스턴스가 있어야 채움 |     |   빈칸 (이름만 같다)        |
  | static 은 인스턴스가 없다   |     |   -> 호출 인자에서 채운다    |
  | -> 채울 수 없다            |     | -> 문제없다                |
  +---------------------------+     +---------------------------+
```

**규칙의 이유를 실증하는 프로그램** — `static` 필드 하나를 두고 타입 인자만 바꿔 인스턴스를 만든다(3번의 답이 그것이다).\
클래스 타입 파라미터가 `static` 에 통했다면, 타입 인자마다 `static` 저장소가 따로 있어야 한다.\
그런데 **클래스는 하나뿐**이므로 그럴 수 없다.

표준 라이브러리의 정적 팩토리가 전부 (E) 형태다 — `static <E> List<E> of(...)`, `static <T> List<T> emptyList()`.

### 3. 제네릭 클래스의 `static` 필드는 타입 인자마다 따로인가

**출력** (`Ex.java (17-h)`, JDK 21.0.5 — 17·25 에서도 동일)

```text
--- static 멤버는 타입 인자와 무관하게 하나뿐이다
Counter.created = 3  (세 타입이 같은 카운터를 썼다)
Counter<String>.class 와 Counter<Integer>.class 는 같은 객체인가 = true
그 클래스 = Ex$Counter
```

**왜 그런가**

```text
세 타입으로 만들었는데 저장소는 하나다

  힙의 인스턴스                        static 영역
  +--------------------+
  | Counter (T=String) |  \
  +--------------------+   \
  +--------------------+    ->   +---------------------+
  | Counter (T=Integer)|   /     | Ex$Counter.created  |   <- 딱 하나
  +--------------------+  /      |        = 3         |
  +--------------------+ /       +---------------------+
  | Counter (T=List)   |/
  +--------------------+
```

- `Counter.created` 는 **3** 이다. 세 인스턴스가 **같은 저장소**를 늘렸다.
- `getClass()` 비교는 **`true`** 다 — 타입 인자가 달라도 **클래스는 하나**다.
- 그 클래스 이름은 **`Ex$Counter`** 다. 타입 인자는 이름에 안 들어간다.

이것이 2번의 `static` 금지 규칙의 근거이고, 동시에 [`../19-type-erasure/`](../19-type-erasure/) 의 출발점이다.

### 4. 바운드가 없으면 무엇을 못 하나

**출력** (`Ex.java (17-d)` `javac`, JDK 21.0.5)

```text
Ex.java:11: error: cannot find symbol
        for (T t : list) if (t.compareTo(best) > 0) best = t;   // (A) 바운드가 없으면?
                              ^
  symbol:   method compareTo(T)
  location: variable t of type T
  where T is a type-variable:
    T extends Object declared in method <T>maxNoBound(List<T>)
```

**왜 그런가**

- **컴파일되지 않는다.** `T` 위에서 `compareTo` 를 못 찾는다.
- 에러 메시지가 이유를 그대로 적어 준다 — **`T extends Object`**.

```text
바운드 없는 <T> 는 <T extends Object> 다

  <T>                                  <T extends Number>
  +-----------------------------+      +-----------------------------+
  | T 에서 부를 수 있는 것       |      | T 에서 부를 수 있는 것       |
  |   = Object 의 메서드뿐      |      |   = Number 의 메서드까지     |
  |   equals/hashCode/toString  |      |   doubleValue/intValue ...  |
  |   getClass/wait/notify      |      |                             |
  +-----------------------------+      +-----------------------------+
    무엇이든 받지만 아무것도 못 한다       Number 만 받고 그만큼 할 수 있다
```

**로 타입으로 바운드를 주면** — 컴파일은 되고 **경고 둘**이 난다.

```text
Ex.java:4: warning: [rawtypes] found raw type: Comparable
    static <T extends Comparable> T maxRaw(List<T> list) {   // 로 타입 바운드
                      ^
  missing type arguments for generic class Comparable<T>
Ex.java:6: warning: [unchecked] unchecked call to compareTo(T) as a member of the raw type Comparable
        for (T t : list) if (t.compareTo(best) > 0) best = t;
                                        ^
```

- `compareTo(Object)` 를 부르는 셈이 되어 **타입 안전이 그 지점에서 끊긴다.**
- `-Xlint:all` 을 안 켜면 경고도 안 보인다.

### 5. 바운드를 어기면

**출력** (`Ex.java (17-c)` `javac`, JDK 21.0.5)

```text
Ex.java:7: error: type argument String is not within bounds of type-variable T
        NumberBox<String> a = new NumberBox<>("x");        // (A) 바운드 위반
                  ^
  where T is a type-variable:
    T extends Number declared in class NumberBox
Ex.java:7: error: cannot infer type arguments for NumberBox<>
        NumberBox<String> a = new NumberBox<>("x");        // (A) 바운드 위반
                              ^
  reason: inference variable T has incompatible bounds
    upper bounds: Number
    lower bounds: String
  where T is a type-variable:
    T extends Number declared in class NumberBox
Ex.java:8: error: unexpected type
        NumberBox<int> b = null;                            // (B) 기본형을 타입 인자로
                  ^
  required: reference
  found:    int
Ex.java:9: error: unexpected type
        List<int> c = null;                                 // (C)
             ^
  required: reference
  found:    int
Ex.java:10: error: method maxOf in class Ex cannot be applied to given types;
        maxOf(List.of(new Object(), new Object()));         // (D) Comparable 이 아닌 타입
        ^
  required: List<T>
  found:    List<Object>
  reason: inference variable E has incompatible bounds
    upper bounds: Comparable<T>,Object
    lower bounds: Object
  where T,E are type-variables:
    T extends Comparable<T> declared in method <T>maxOf(List<T>)
    E extends Object declared in method <E>of(E,E)
5 errors
```

**왜 그런가**

| 자리 | 에러 | 핵심 |
|---|---|---|
| (A) | `type argument String is not within bounds` + `cannot infer type arguments` | **에러 둘** |
| (B)(C) | `unexpected type / required: reference / found: int` | 타입 인자는 **참조 타입만** |
| (D) | `inference variable E has incompatible bounds` | 재귀 바운드를 못 만족 |

**(A)에서 에러가 둘인 이유** — 같은 줄에 **검사가 두 번** 일어난다.

```text
NumberBox<String> a = new NumberBox<>("x");
          ^^^^^^                ^^
          (1) 선언 타입의 타입 인자가 바운드를 만족하나  -> String 은 Number 가 아니다
                                (2) 다이아몬드의 T 를 추론할 수 있나 -> 상한 Number, 하한 String -> 불가
```

**(B)(C) 의 메시지가 `required: reference` 인 이유**

- 타입 인자는 **참조 타입만** 될 수 있다(JLS §4.5). `int` 는 참조 타입이 아니다.
- 그래서 `List<Integer>` 처럼 **래퍼**를 써야 한다. 뿌리는 [`../01-primitives-and-wrappers/`](../01-primitives-and-wrappers/) 가 정본이다.
- 같은 이유로 기본형 전용 API(`IntStream`·`int[]`)가 따로 존재한다.

### 6. 다중 바운드의 규칙

**출력** (`Ex.java (17-e)` `javac`, JDK 21.0.5)

```text
Ex.java:5: error: cyclic inheritance involving T
    static class SelfExtends<T extends T> {}                       // (C) 자기 자신
                             ^
  where T is a type-variable:
    T extends T declared in class SelfExtends
Ex.java:3: error: interface expected here
    static class BadOrder<T extends Runnable & Object> {}          // (A) 클래스가 뒤에
                                               ^
Ex.java:4: error: interface expected here
    static class TwoClasses<T extends Number & String> {}          // (B) 클래스 둘
                                               ^
3 errors
```

**왜 그런가**

- **(B)(C)(D) 세 자리가 에러**다. **(A) `Multi` 와 (E) `FinalBound` 는 통과**했다.

```text
다중 바운드의 형태

  <T extends Resource & Closeable2 & Serializable>
             \______/   \_________________________/
             클래스 0~1개        인터페이스 여러 개
             반드시 맨 앞          순서 자유

  안 되는 것
    <T extends Runnable & Object>   -> 클래스가 뒤 : interface expected here
    <T extends Number & String>     -> 클래스 둘   : interface expected here
    <T extends T>                   -> 자기 자신   : cyclic inheritance involving T
```

**순서 규칙** — **클래스는 최대 하나이고 맨 앞**이다.

- 자바가 **단일 상속**이라 클래스 바운드는 하나뿐이다.
- 두 번째 자리부터 컴파일러는 **인터페이스로 해석**한다 — 그래서 클래스를 쓰면 `interface expected here` 다.
- 인터페이스에도 `extends` 를 쓴다(`implements` 가 아니다). `&` 로 잇는다.

**(E) `<T extends String>` 이 에러가 아닌 이유**

- `String` 은 `final` 이라 `T` 가 될 수 있는 타입이 **`String` 하나뿐**이다.
- 그래도 **문법적으로 위반이 아니다.** 컴파일러는 "쓸모"를 판정하지 않는다.
- 쓸모는 사실상 없다 — 그냥 `String` 을 쓰면 된다.

**다중 바운드가 실제로 동작하는 것** (`Ex.java (17-a)`)

```text
--- 다중 바운드
R7 / closeable / compareTo(self)=0
```

`<T extends Resource & Closeable2>` 에서 `Resource` 의 `toString`·`compareTo` 와 `Closeable2` 의 `tag()` 를 **둘 다** 불렀다.

### 7. 이 호출이 컴파일되는가

**출력** (`Ex.java (17-a)`, JDK 21.0.5)

```text
--- 제네릭 메서드의 타입 추론
listOfTwo(1, 2)            = [1, 2]
listOfTwo("a", "b")        = [a, b]
listOfTwo(1, "a")          = [1, a]  <- 컴파일된다. T 는 무엇이 됐나?
  원소 0 의 클래스 = Integer
  원소 1 의 클래스 = String
명시적 타입 인자 Ex.<Object>listOfTwo(1,"a") = [1, a]
```

**왜 그런가**

**(A) 는 컴파일된다.** 컴파일러가 `Integer` 와 `String` 의 **공통 상위 타입**을 만들어 `T` 로 삼는다.

**추론된 타입을 끌어내는 법** — 결과를 **그 타입이 아닌 변수에 대입**해 에러를 유도한다.

**출력** (`Ex.java (17-g)` `javac`, JDK 21.0.5 — 17·25 에서도 같았다)

```text
Ex.java:6: error: incompatible types: INT#1 cannot be converted to String
        String s = x.get(0);          // 추론된 T 의 정체가 여기서 드러난다
                        ^
  where INT#1,INT#2 are intersection types:
    INT#1 extends Object,Serializable,Comparable<? extends INT#2>,Constable,ConstantDesc
    INT#2 extends Object,Serializable,Comparable<?>,Constable,ConstantDesc
```

```text
T 를 어떻게 정했나

  listOfTwo(1, "a")
       |      |
   Integer  String
       \      /
        \    /  둘 다를 만족하는 가장 좁은 타입을 만든다
         \  /
          v
   Object & Serializable & Comparable<...> & Constable & ConstantDesc
        = 교차 타입(intersection type). 소스에 이름을 쓸 수 없다
```

**(B) 의 에러** (`Ex.java (17-f)`)

```text
Ex.java:5: error: incompatible types: inference variable T has incompatible bounds
        List<String> bad = listOfTwo(1, "a");
                                    ^
    equality constraints: String
    lower bounds: String,Integer
  where T is a type-variable:
    T extends Object declared in method <T>listOfTwo(T,T)
```

- 좌변이 `T = String` 을 요구하는데(`equality constraints: String`) 인자가 `String`·`Integer` 를 아래에서 밀어 올린다(`lower bounds`).
- 둘이 충돌해서 터진다. **호출한 자리가 아니라 받는 자리**에서 터진다는 것이 요점이다.

**추론을 강제로 바꾸는 문법** — **명시적 타입 인자**다.

```java
Ex.<Object>listOfTwo(1, "a")      // 메서드 이름 앞, 수신자(Ex.) 뒤
this.<String>instanceGeneric("x") // 인스턴스 메서드는 this. 가 필요하다
```

수신자를 생략할 수 없다는 것이 형태의 함정이다 — `<Object>listOfTwo(...)` 는 파싱되지 않는다.

### 8. 재귀 바운드는 무엇을 위한 것인가

**출력** (`Ex.java (17-a)`, JDK 21.0.5)

```text
--- 재귀 바운드
maxOf(List.of(3,9,4))               = 9
maxOf(List.of("pear","fig","apple")) = pear
maxOf(List.of(R3,R1,R9))            = R9
```

**왜 그런가**

```text
<T extends Comparable>            <T extends Comparable<T>>
+-----------------------------+   +-----------------------------+
| compareTo(Object) 를 부른다   |   | compareTo 가 T 를 받는다고   |
| 로 타입 경고 둘               |   |   컴파일러가 안다            |
| 아무 타입이나 인자로 넘어간다  |   | 경고 없음                   |
+-----------------------------+   +-----------------------------+
```

- `<T extends Comparable<T>>` 는 "**T 는 T 와 비교할 수 있어야 한다**"를 타입으로 적은 것이다.
- 재귀라고 부르는 이유는 **바운드 안에 자기 자신(`T`)이 나오기** 때문이다.

**이 선언이 막아 주는 호출** (`Ex.java (17-c)` (D))

```text
Ex.java:10: error: method maxOf in class Ex cannot be applied to given types;
        maxOf(List.of(new Object(), new Object()));
        ^
  reason: inference variable E has incompatible bounds
    upper bounds: Comparable<T>,Object
    lower bounds: Object
```

- `Object` 는 `Comparable` 이 아니므로 **호출 자체가 막힌다.**
- 로 타입 바운드였다면 컴파일이 통과하고 **런타임에 `ClassCastException`** 이 됐을 것이다.

**`Comparable` 계약 자체의 정본** — [`../28-comparable-comparator/`](../28-comparable-comparator/) 다.\
"전순서 계약을 어기면 `TimSort` 가 무엇을 던지나"는 그쪽이고, **바운드를 어떻게 적나**가 여기다.

### 9. `Comparable<T>` 와 `Comparable<? super T>` 는 무엇이 다른가

**출력** (`Ex.java (17-i)`, JDK 21.0.5)

```text
maxSuper(dogs)  = Dog
maxStrict(List<Animal>) = Animal
```

`maxStrict(dogs)` 는 컴파일 에러다.

```text
Ex.java:14: error: method maxStrict in class Ex cannot be applied to given types;
        System.out.println("maxStrict(dogs) = " + maxStrict(dogs));   // 되나?
                                                  ^
  required: List<T>
  found:    List<Dog>
  reason: inference variable T has incompatible equality constraints Animal,Dog
  where T is a type-variable:
    T extends Comparable<T> declared in method <T>maxStrict(List<T>)
```

**왜 그런가**

```text
Animal implements Comparable<Animal> 이고 Dog extends Animal 일 때

  Dog 는 Comparable<Dog> 인가?          Dog 는 Comparable<? super Dog> 인가?
  +-----------------------------+      +-----------------------------+
  | Dog 가 구현한 것은           |      | Dog 가 구현한 것은           |
  |   Comparable<Animal>        |      |   Comparable<Animal>        |
  | Comparable<Dog> 와 다르다    |      | Animal 은 Dog 의 상위다      |
  |   (제네릭은 불공변)          |      |   -> ? super Dog 를 만족     |
  | -> 아니다                   |      | -> 그렇다                   |
  +-----------------------------+      +-----------------------------+
      maxStrict(List<Dog>) 컴파일 에러     maxSuper(List<Dog>) 통과
```

- 제네릭이 **불공변**이라 `Comparable<Animal>` 은 `Comparable<Dog>` 가 아니다.
- 상속 계층에서 **상위가 `Comparable` 을 구현하면** `Comparable<T>` 바운드는 하위 타입을 거부한다.
- `maxStrict` 는 `List<Animal>` 은 받는다(출력의 둘째 줄) — **하위 타입만 못 받는다.**

**`Collections.max` 의 실제 시그니처** — `src.zip` 의 `java/util/Collections.java` 에서 읽었다.

```java
public static <T extends Object & Comparable<? super T>> T max(Collection<? extends T> coll) {
```

- **`Comparable<? super T>`** 쪽이다. 같은 파일의 `min` 도 같다.
- 왜 `? super` 가 그런 일을 하는지는 [`../18-wildcards-pecs/`](../18-wildcards-pecs/) 가 정본이다.

### 10. 타입 파라미터 가리기와 inner 클래스

**출력** (`Ex.java (17-h)`, JDK 21.0.5)

```text
--- 타입 파라미터 가리기
  메서드 안의 T 는 바깥 T 와 다른 타입 파라미터다: 42
  inner.fromOuter = 안쪽이 바깥 T 를 쓴다
```

**왜 그런가**

```text
이름이 같아도 다른 빈칸이다

  Outer<String>                          o.<Integer>shadow(42)
  +-------------------------+            +-------------------------+
  | 바깥 T = String         |            | 메서드 T = Integer       |
  |   outerValue : String   |            |   t : Integer           |
  |   Inner.fromOuter : String|          | 바깥 T 는 가려져서 못 쓴다|
  +-------------------------+            +-------------------------+
```

- **`shadow` 의 `T` 는 다른 것**이다. 메서드가 같은 이름의 타입 파라미터를 새로 선언해 **바깥 것을 가린다**(shadowing).
- 컴파일은 되지만 읽기가 나쁘다 — 이름을 `U` 로 바꾸는 것이 맞다.

**`Inner` 가 바깥 `T` 를 쓸 수 있는 이유**

- `Inner` 는 **non-static 중첩 클래스(inner class)** 라 **바깥 인스턴스에 딸려 있다.**
- 바깥 인스턴스가 있으면 그 인스턴스의 `T` 가 정해져 있으므로 쓸 수 있다.
- 중첩 클래스의 종류별 차이는 [`../12-nested-classes/`](../12-nested-classes/) 가 정본이다.

**`static` 으로 바꾸면** (`Ex.java (17-k)`)

```text
Ex.java:5: error: non-static type variable T cannot be referenced from a static context
        static class StaticNested { T fromOuter; }   // (B) static nested — 되나?
                                    ^
1 error
```

2번과 **정확히 같은 에러**다. `static` 은 인스턴스가 없으니 `T` 를 채울 수 없다.

**인스턴스를 만드는 형태**

```java
Outer<String> o = new Outer<>();
Outer<String>.Inner in = o.new Inner();     // 타입 이름과 new 의 형태를 보라
```

선언 타입이 `Outer<String>.Inner` 라는 것이 "바깥의 `T` 에 딸려 있다"는 관계를 그대로 드러낸다.

### 11. 다이아몬드와 `var` 가 추론하는 것

**출력** (`Ex.java (17-a)` `(17-j)`, JDK 21.0.5)

```text
--- 다이아몬드 추론
m = {k=[1]}
var + 다이아몬드 = Box[var 로 받으면] / get().length() = 9
```

```text
--- var + 빈 다이아몬드
  list = [문자열, 42] / get(0) 의 정적 타입은 Object
  typed.get(0).length() = 3
```

**왜 그런가**

```text
무엇에서 추론하나

  Map<String,List<Integer>> m = new HashMap<>();
                                            ^^ 좌변의 선언 타입에서

  m.computeIfAbsent("k", k -> new ArrayList<>())
                                            ^^ 파라미터의 기대 타입에서

  var inferred = new Box<>("var 로 받으면");
      ^^^                    ^^      인자에서 T=String, 다시 var 가 Box<String>

  var list = new ArrayList<>();
      ^^^                   ^^      양쪽 다 정보가 없다 -> ArrayList<Object>
```

**`inferred.get().length()` 는 컴파일되는가** — 된다. 출력의 `9` 가 그 확인이다(`"var 로 받으면"` 의 길이).

**마지막 줄은 컴파일되는가** — 안 된다.

```text
error: incompatible types: Object cannot be converted to String
... var list = new ArrayList<>(); list.add("x"); String s = list.get(0); ...
                                                                     ^
```

- `var list = new ArrayList<>()` 는 **`ArrayList<Object>`** 가 된다. **에러도 경고도 없다.**
- `String` 과 `int` 를 한 리스트에 넣는 것도 통과한다(출력의 `[문자열, 42]`).
- **꺼내는 자리에서야** 터진다.
- `var` 를 쓸 거면 **생성 쪽에 타입 인자를 적는다** — `var typed = new ArrayList<String>();`

### 12. 무엇을 어디에 둘 것인가

| 상황 | 타입 파라미터를 어디에 | 이유 |
|---|---|---|
| 필드가 그 타입을 들고 있어야 한다 | **클래스** | 인스턴스 수명 동안 같아야 한다 |
| 여러 메서드가 같은 타입을 주고받는다 | **클래스** | 관계를 타입으로 고정한다 |
| 한 호출 안에서만 관계가 성립한다 | **메서드** | 호출마다 달라도 된다 |
| `static` 유틸이다 | **메서드** | 클래스 타입 파라미터를 못 쓴다(2번) |

**`static` 유틸 메서드** — 반드시 **자기 타입 파라미터**를 선언한다.

```java
static <T> List<T> listOfTwo(T a, T b) { ... }
static <T, U extends T> void copyInto(List<T> dst, List<U> src) { ... }
```

**바운드를 붙일지의 판단**

| 조건 | 판단 |
|---|---|
| `T` 위에서 메서드를 부른다 | 붙인다 — 안 붙이면 `Object` 의 것만 쓸 수 있다(4번) |
| 담기만 한다 | 안 붙인다 — 받을 타입을 좁힐 이유가 없다 |
| 비교·정렬이 필요하다 | `<T extends Comparable<? super T>>` (9번) |
| 조건이 여럿이다 | `&` 로 잇되 **클래스는 맨 앞 하나**(6번) |

한 문장으로 — **`T` 로 무엇을 할 건지 먼저 적어 보고, 그것이 `Object` 에 없으면 바운드를 붙인다.**

### 13. 다른 주제와 잇기

**`Counter<String>.class == Counter<Integer>.class` 가 참인 이유**

```text
Counter<String>.class 와 Counter<Integer>.class 는 같은 객체인가 = true
그 클래스 = Ex$Counter
```

- **타입 소거** 때문이다. 타입 인자는 컴파일 후 사라지고 클래스는 하나만 만들어진다.
- 정본은 [`../19-type-erasure/`](../19-type-erasure/) 다. 거기서는 `javap` 로 **무엇이 지워지고 무엇이 `Signature` 에 남는지**까지 본다.

**`List<int>` 가 안 되는 이유**

```text
error: unexpected type
  required: reference
  found:    int
```

- 타입 인자는 **참조 타입만** 될 수 있다(JLS §4.5).
- 뿌리는 [`../01-primitives-and-wrappers/`](../01-primitives-and-wrappers/) — 기본형과 래퍼의 구분이 정본이다.
- 그래서 `Arrays.asList(int[])` 가 원소 하나짜리 리스트가 되는 함정도 같은 뿌리다([`../05-arrays/`](../05-arrays/)).

**`List<String>`/`List<Integer>` 로 오버로드할 수 있는가** — 없다.

```text
error: name clash: print(List<Integer>) and print(List<String>) have the same erasure
```

- 소거 후 둘 다 `print(List)` 가 되어 **같은 시그니처**가 된다.
- 정본은 [`../19-type-erasure/`](../19-type-erasure/) 이고, 오버로딩 해소 규칙 자체는 [`../08-method-declaration-overloading/`](../08-method-declaration-overloading/) 다.

**애너테이션이 제네릭이 될 수 없는 이유**

```text
error: annotation interface Generic cannot be generic
```

- 애너테이션 값은 **클래스 파일에 상수로 박히는 것**이고, 타입 인자는 **클래스 파일에서 지워지는 것**이다.
- 정본은 [`../16-annotations/`](../16-annotations/) 다.

---

## 이 주제를 확인한 실행 목록

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Ex.java (17-a)` | 클래스·메서드 타입 파라미터의 범위, 바운드·다중 바운드, 추론, 재귀 바운드, 타입 파라미터끼리 바운드, 다이아몬드·`var` | 17 · 21 · 25 (**출력 동일**) |
| `Ex.java (17-b)` `javac` | `static` 필드·메서드·반환 타입에서 클래스 `T` 금지, 자기 타입 파라미터는 허용 | 17 · 21 · 25 (**동일**) |
| `Ex.java (17-c)` `javac` | 바운드 위반(에러 둘), 기본형 타입 인자, `Comparable` 아닌 타입에 재귀 바운드 | 17 · 21 · 25 (**동일**) |
| `Ex.java (17-d)` `javac` | 바운드 없는 `T` 에서 `compareTo` 불가, 로 타입 바운드의 경고 둘 | 21 |
| `Ex.java (17-e)` `javac` | 다중 바운드 순서 규칙, `<T extends T>` 순환, `<T extends String>` 은 통과 | 17 · 21 · 25 (**동일**) |
| `Ex.java (17-f)` `javac` | `List<String> = listOfTwo(1,"a")` 의 추론 충돌 메시지 | 21 |
| `Ex.java (17-g)` `javac` | 추론된 `T` 가 교차 타입(`INT#1`)이라는 것 | 17 · 21 · 25 (**동일**) |
| `Ex.java (17-h)` | `static` 필드가 타입 인자와 무관하게 하나, `getClass()` 동일, 타입 파라미터 가리기, inner 클래스 | 17 · 21 · 25 (**출력 동일**) |
| `Ex.java (17-i)` `javac` + 실행 | `Comparable<T>` 가 하위 타입을 거부하고 `Comparable<? super T>` 는 받는 것 | 21 |
| `Ex.java (17-j)` | 제네릭 생성자, `var` + 빈 다이아몬드가 `ArrayList<Object>` 가 되는 것 | 21 |
| `Ex.java (17-k)` `javac` | `static` 중첩 클래스가 바깥 `T` 를 못 쓰는 것 | 21 |
| `javap -v -p` (19-a 의 클래스) | 제네릭 클래스·메서드의 `Signature` 속성에 타입 파라미터 이름과 바운드가 남는 것 | 21 |
| `src.zip` 열람 | `Collections.max`/`min`/`copy`/`fill` 의 시그니처, `List.sort`, `Comparator.comparing` | 21 |

**구현 의존 항목** — 교차 타입에 `Constable`·`ConstantDesc` 가 들어간 것(`Integer`·`String` 이 Java 12 에서 구현한 인터페이스), `javac` 의 `INT#1`·`CAP#1` 표기 방식은 **구현 세부**다.\
버전이 올랐을 때 다시 돌려 볼 것은 이 표의 **`(17-g)`** 다 — 교차 타입의 구성원이 라이브러리에 달려 있다.\
반면 `static` 문맥 금지, 다중 바운드 순서, 기본형 금지, 바운드 없는 `<T>` = `<T extends Object>` 는 JLS 가 보장한다.
