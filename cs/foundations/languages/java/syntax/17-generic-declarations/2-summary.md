# java/syntax/17 — 제네릭 선언: 타입 파라미터·바운드·제네릭 메서드 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [JLS SE 21 §4.4 Type Variables](https://docs.oracle.com/javase/specs/jls/se21/html/jls-4.html) · [§8.1.2 Generic Classes and Type Parameters](https://docs.oracle.com/javase/specs/jls/se21/html/jls-8.html) · [§8.4.4 Generic Methods](https://docs.oracle.com/javase/specs/jls/se21/html/jls-8.html) · [§18 Type Inference](https://docs.oracle.com/javase/specs/jls/se21/html/jls-18.html) · JDK 21.0.5 표준 라이브러리 소스 `java.base/java/util/*.java`(`lib/src.zip`).
> **실행 검증** — 이 문서의 모든 출력·에러·바이트코드는 Temurin **JDK 21.0.5** 에서 실제로 돌려 얻은 것이다.\
> `Ex.java (17-a)` `(17-h)` 는 **17.0.13 · 21.0.5 · 25.0.1** 에서 다 돌렸고 출력이 한 글자도 다르지 않았다.\
> 컴파일 에러 다섯 종류도 17 과 25 에서 **문자 단위로 같았다**(`diff` 로 확인).\
> **"세 곳에서 같았다"는 관찰이지 보장이 아니다** — 보장은 JLS·javadoc 인용으로만 적었다.
> **버전** — 제네릭은 **Java 5**. 다이아몬드 `<>` 는 **7**, 익명 클래스의 다이아몬드는 **9**,
> `var` 와의 조합은 **10** 부터다.
> **범위** — 타입 인자가 **런타임에 사라지는 것**은 [`../19-type-erasure/`](../19-type-erasure/) 가, `? extends`/`? super` 는 [`../18-wildcards-pecs/`](../18-wildcards-pecs/) 가 정본이다.\
> 여기는 **타입 파라미터를 어디에 어떻게 선언하고 무엇으로 묶는가**까지다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 JLS 로, 출력은 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**타입 파라미터는 "나중에 채울 빈칸"이고, 바운드는 "그 빈칸에 들어올 수 있는 것의 조건"이다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 서식(양식) 한 장 | 제네릭 클래스·메서드 선언 |
| 서식의 빈칸 `[ ]` | 타입 파라미터 `<T>` |
| 빈칸 옆의 "숫자만 기입" 단서 | 바운드 `<T extends Number>` |
| 빈칸을 채워 낸 서류 한 장 | 파라미터화 타입 `Box<String>` |
| 채운 서류를 창구가 검사하는 시점 | **컴파일 타임** |
| 서식 한 장으로 여러 서류를 찍어낸다 | 같은 클래스 파일 하나가 모든 타입 인자를 처리한다 |

- 빈칸은 **서식 전체에 걸칠 수도**(클래스 타입 파라미터) **한 항목에만 걸칠 수도**(메서드 타입 파라미터) 있다.
- 서식에 "숫자만"이라고 적어 두면 **창구가 글자를 받지 않는다** — 이것이 바운드다.
- 그리고 빈칸에 적은 것은 **접수가 끝나면 지워진다.** 창구(컴파일러)만 보고, 뒤쪽 사무실(JVM)은 못 본다.

```text
타입 파라미터의 범위 두 가지

  class Box<T> {              <- T 의 범위는 클래스 전체
      T value;                   인스턴스마다 하나로 고정된다
      T get() { ... }
      <U> Box<U> map(...)     <- U 의 범위는 이 메서드 안쪽뿐
  }                              호출할 때마다 새로 정해진다

  static <T> List<T> listOfTwo(T a, T b)   <- T 의 범위는 이 메서드 안쪽뿐
```

**똑같은 구조로** Java 가 동작한다: 서식 = 제네릭 선언, 빈칸 = 타입 파라미터, 단서 = 바운드, 창구 = 컴파일러.

실무에서 이게 물리는 자리는 **`static` 메서드에서 클래스 타입 파라미터를 쓰려 할 때**다.\
서식 전체에 걸친 빈칸은 "서류 한 장"에 속한 것인데, `static` 은 **서류가 아니라 서식에 속하므로** 채울 값이 없다.

> **타입 파라미터(type parameter)** — 선언에서 `<T>` 처럼 쓰는, 나중에 실제 타입으로 채워질 이름.\
> 예: `class Box<T>` 의 `T`. `new Box<String>()` 을 하면 그 인스턴스에서 `T` 는 `String` 이다.

> **타입 인자(type argument)** — 타입 파라미터 자리에 실제로 넣은 타입.\
> 예: `Box<String>` 의 `String`. 빈칸에 써 넣은 값에 해당한다.

> **바운드(bound)** — 타입 인자가 만족해야 하는 상한. `<T extends Number>` 처럼 `extends` 로 적는다.\
> 예: `NumberBox<Integer>` 는 되고 `NumberBox<String>` 은 컴파일 에러다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 네 질문을 둔다.

1. 타입 파라미터를 **클래스에 둘지 메서드에 둘지**는 무엇으로 갈리는가.
2. `static` 메서드가 클래스 타입 파라미터를 **못 쓰는 이유**는 무엇인가.
3. 바운드를 **왜 붙이고**, 다중 바운드에는 어떤 순서 규칙이 있는가.
4. `<T extends Comparable<T>>` 라는 **자기 자신을 참조하는 바운드**는 무엇을 위한 것인가.

## 동작 방식

### (1) 타입 파라미터의 범위 — 클래스냐 메서드냐

**언제 쓰나** — 제네릭을 선언할 때 맨 처음 정하는 것.

**출력** (`Ex.java (17-a)`, JDK 21.0.5)

```text
--- 클래스 타입 파라미터
bs           = Box[hello]
bs.get()     = hello (캐스팅 없이 String)
map 후       = Box[5]  타입은 Box<Integer>
```

```java
static class Box<T> {                        // T 의 범위: 클래스 전체
    private T value;
    T get() { return value; }
    void set(T v) { this.value = v; }
    <U> Box<U> map(Function<? super T, ? extends U> f) {   // U 의 범위: 이 메서드만
        return new Box<>(f.apply(value));
    }
}
```

```text
한 인스턴스 안에서 T 는 하나로 고정된다

  Box<String> bs                     bs.map(String::length)
  +-------------------------+        +-------------------------+
  | T = String              |        | T = String (그대로)      |
  | value : String          |  ->    | U = Integer (이번 호출만) |
  | get() : String          |        | 결과 : Box<Integer>      |
  +-------------------------+        +-------------------------+
     인스턴스를 만들 때 정해진다         호출할 때마다 새로 정해진다
```

그림 해설 (한 단계씩):

- **클래스 타입 파라미터**는 인스턴스를 만들 때 정해지고 **그 인스턴스가 사는 동안 고정**이다.
- **메서드 타입 파라미터**는 **호출할 때마다** 인자에서 추론된다. 같은 객체에 다른 `U` 로 여러 번 부를 수 있다.
- 판단 규칙: **여러 멤버가 같은 타입을 공유해야 하면 클래스에, 한 호출 안에서만 관계가 성립하면 메서드에** 둔다.
- 메서드 타입 파라미터는 **반환 타입 앞**에 온다 — `static <T> List<T> listOfTwo(...)`.

비용 — 없다. 컴파일 타임 개념이고, 바이트코드에는 소거된 형태만 남는다([`../19-type-erasure/`](../19-type-erasure/)).

### (2) `static` 은 클래스 타입 파라미터를 못 쓴다

**언제 쓰나** — 제네릭 클래스에 정적 팩토리나 상수를 넣으려 할 때.

**`javac` 출력 그대로** (`Ex.java (17-b)`, JDK 21.0.5)

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

(D) 인스턴스 메서드와 (E) 자기 타입 파라미터를 새로 선언한 `static <T> T ownParam(T t)` 는 **통과했다.**

**왜 그런가** — 실행으로 이유를 보였다.

**출력** (`Ex.java (17-h)`, JDK 21.0.5)

```text
--- static 멤버는 타입 인자와 무관하게 하나뿐이다
Counter.created = 3  (세 타입이 같은 카운터를 썼다)
Counter<String>.class 와 Counter<Integer>.class 는 같은 객체인가 = true
그 클래스 = Ex$Counter
```

```text
Counter<String> · Counter<Integer> · Counter<List<Double>> 을 만들었는데

  힙의 인스턴스                        static 영역
  +-------------------+
  | Counter (T=String)|  \
  +-------------------+   \
  +-------------------+    ->   +---------------------+
  | Counter (T=Integer)|   /    | Ex$Counter.created  |   <- 딱 하나뿐이다
  +-------------------+   /     |        = 3         |
  +-------------------+  /      +---------------------+
  | Counter (T=List)  | /
  +-------------------+
        세 인스턴스                  셋이 같은 저장소를 쓴다
```

그림 해설 (한 단계씩):

- 클래스 타입 파라미터는 **인스턴스에 딸린 것**이다. `T` 의 값은 인스턴스마다 다르다.
- `static` 멤버는 **인스턴스와 무관하게 하나**다 — 그래서 `T` 가 무엇인지 물을 대상이 없다.
- 실제로 `Counter<String>.class == Counter<Integer>.class` 가 **`true`** 다. 클래스가 하나뿐이니 static 저장소도 하나다.
- 우회는 하나뿐이다 — **`static` 메서드가 자기 타입 파라미터를 새로 선언**한다.

```java
static <U> Counter<U> of(U u) { return new Counter<>(u); }   // 이것은 된다
```

- 표준 라이브러리의 `List.of`·`Collections.emptyList` 가 전부 이 형태다.
- 타입 인자와 **무관한** `static` 필드(`static int created`)는 아무 문제 없다.

비용 — 없다. 설계 제약이다.

### (3) 바운드 — 타입 파라미터로 무엇을 할 수 있는지 정한다

**언제 쓰나** — 타입 파라미터 위에서 메서드를 부르고 싶을 때.

**출력** (`Ex.java (17-a)`, JDK 21.0.5)

```text
--- 바운드
NumberBox<Integer>.doubled() = 42.0
NumberBox<Double>.doubled()  = 3.0
```

```java
static class NumberBox<T extends Number> {
    private final T v;
    double doubled() { return v.doubleValue() * 2; }   // 바운드 덕에 Number 의 메서드를 쓸 수 있다
}
```

```text
바운드가 있을 때와 없을 때 무엇이 달라지나

  <T>                                  <T extends Number>
  +-----------------------------+      +-----------------------------+
  | T 에서 부를 수 있는 것       |      | T 에서 부를 수 있는 것       |
  |   = Object 의 메서드뿐      |      |   = Number 의 메서드까지     |
  |   equals/hashCode/toString  |      |   doubleValue/intValue ...  |
  +-----------------------------+      +-----------------------------+
    무엇이든 받지만 아무것도 못 한다       Number 만 받고 그만큼 할 수 있다
```

**바운드가 없으면** 어떻게 되는지 던져 봤다(`Ex.java (17-d)`).

```text
Ex.java:11: error: cannot find symbol
        for (T t : list) if (t.compareTo(best) > 0) best = t;   // (A) 바운드가 없으면?
                              ^
  symbol:   method compareTo(T)
  location: variable t of type T
  where T is a type-variable:
    T extends Object declared in method <T>maxNoBound(List<T>)
```

그림 해설 (한 단계씩):

- 바운드가 없는 `<T>` 는 **`<T extends Object>` 와 같다.** 에러 메시지의 `T extends Object` 가 그것이다.
- 그래서 `Object` 의 메서드밖에 못 부른다. `compareTo` 를 부르려면 바운드가 필요하다.
- 바운드는 **받을 수 있는 타입을 좁히는 대가로 할 수 있는 일을 넓힌다.**

**바운드를 어기면** (`Ex.java (17-c)`)

```text
Ex.java:7: error: type argument String is not within bounds of type-variable T
        NumberBox<String> a = new NumberBox<>("x");        // (A) 바운드 위반
                  ^
  where T is a type-variable:
    T extends Number declared in class NumberBox
```

비용 — 없다. 컴파일 타임 검사다.

### (4) 다중 바운드 — 클래스는 하나, 그것도 맨 앞

**언제 쓰나** — "Comparable 이면서 Serializable 인 것"처럼 조건이 여럿일 때.

```java
static <T extends Resource & Closeable2> String describe(T t) {
    return t + " / " + t.tag() + " / compareTo(self)=" + t.compareTo(t);
}
```

**출력** (`Ex.java (17-a)`, JDK 21.0.5)

```text
--- 다중 바운드
R7 / closeable / compareTo(self)=0
```

**규칙을 어기면** (`Ex.java (17-e)`)

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

그림 해설 (한 단계씩):

- **`&` 로 잇는다.** `extends` 를 여러 번 쓰는 게 아니다(인터페이스여도 `extends` 다).
- **클래스는 최대 하나**이고 **맨 앞**이어야 한다. 자바가 단일 상속이기 때문이다.
- 두 번째 자리부터는 인터페이스로 해석하므로 클래스를 쓰면 `interface expected here` 가 나온다.
- `final` 클래스를 바운드로 쓰는 것(`<T extends String>`)은 **컴파일된다** — 의미는 없지만(`T` 가 `String` 하나뿐) 에러는 아니다.

비용 — 다중 바운드의 **첫 번째** 타입이 소거 시 남는 타입이 된다 — 그 결과는 [`../19-type-erasure/`](../19-type-erasure/) 에서 본다.

### (5) 제네릭 메서드의 타입 추론 — 어디까지 알아서 해 주나

**언제 쓰나** — 제네릭 메서드를 부를 때(거의 항상 명시하지 않는다).

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

`listOfTwo(1, "a")` 가 **컴파일된다는 것**이 놀라운 자리다. `T` 가 무엇으로 추론됐는지 에러로 끌어냈다.

**`javac` 출력 그대로** (`Ex.java (17-g)`, JDK 21.0.5 — 17·25 에서도 같았다)

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
        = 교차 타입(intersection type). 이름 없는 타입이다
```

그림 해설 (한 단계씩):

- 컴파일러는 인자 둘의 **공통 상위 타입**을 만들어 `T` 로 삼는다. 그것이 **교차 타입**이다.
- 그래서 에러가 안 난다 — **"타입이 안 맞아서 못 부른다"가 아니라 "이상한 타입으로 불린다"**가 된다.
- 반환값을 `List<String>` 에 넣으려 하면 그때서야 터진다(`Ex.java (17-f)`).

```text
Ex.java:5: error: incompatible types: inference variable T has incompatible bounds
        List<String> bad = listOfTwo(1, "a");
                                    ^
    equality constraints: String
    lower bounds: String,Integer
```

- 추론이 마음에 안 들면 **명시적 타입 인자**를 쓴다 — `Ex.<Object>listOfTwo(1, "a")`.\
  메서드 이름 앞, 수신자 뒤에 쓴다는 것이 형태의 함정이다(`Ex.` 를 생략할 수 없다).

> **교차 타입(intersection type)** — 여러 타입을 동시에 만족하는, 이름이 없는 타입.\
> 예: `Integer` 와 `String` 의 공통 상위는 `Object & Serializable & Comparable<...>` 이고, 소스에 그 이름을 쓸 수는 없다.

비용 — 없다. 다만 **의도치 않은 추론이 컴파일을 통과한다**는 것이 비용이다.

### (6) 재귀 바운드 — `<T extends Comparable<T>>`

**언제 쓰나** — "자기들끼리 비교할 수 있는 타입"만 받고 싶을 때. 정렬·최댓값이 전부 이 형태다.

**출력** (`Ex.java (17-a)`, JDK 21.0.5)

```text
--- 재귀 바운드
maxOf(List.of(3,9,4))               = 9
maxOf(List.of("pear","fig","apple")) = pear
maxOf(List.of(R3,R1,R9))            = R9
```

```java
static <T extends Comparable<T>> T maxOf(List<T> list) {
    T best = list.get(0);
    for (T t : list) if (t.compareTo(best) > 0) best = t;
    return best;
}
```

```text
왜 Comparable 만으로는 모자란가

  <T extends Comparable>            <T extends Comparable<T>>
  +-----------------------------+   +-----------------------------+
  | t.compareTo(best) 에서       |   | compareTo 가 T 를 받는다고   |
  |   compareTo(Object) 를 부른다|   |   컴파일러가 안다            |
  | 로 타입 경고가 뜬다           |   | 경고 없음                   |
  | Object 도 통과할 뻔한다       |   | 비교 불가능한 타입은 막힌다   |
  +-----------------------------+   +-----------------------------+
```

**로 타입 바운드로 써 보면** (`Ex.java (17-d)`)

```text
Ex.java:4: warning: [rawtypes] found raw type: Comparable
    static <T extends Comparable> T maxRaw(List<T> list) {   // 로 타입 바운드
                      ^
Ex.java:6: warning: [unchecked] unchecked call to compareTo(T) as a member of the raw type Comparable
        for (T t : list) if (t.compareTo(best) > 0) best = t;
                                        ^
```

**비교 불가능한 타입을 넘기면** (`Ex.java (17-c)`)

```text
Ex.java:10: error: method maxOf in class Ex cannot be applied to given types;
        maxOf(List.of(new Object(), new Object()));         // (D) Comparable 이 아닌 타입
        ^
  required: List<T>
  found:    List<Object>
  reason: inference variable E has incompatible bounds
    upper bounds: Comparable<T>,Object
    lower bounds: Object
```

그림 해설 (한 단계씩):

- 재귀 바운드는 **"T 는 T 와 비교할 수 있어야 한다"**를 타입으로 적은 것이다.
- 이것이 없으면 `compareTo` 의 인자가 `Object` 라서 **아무 타입이나 넘길 수 있게 된다.**
- 그래서 정렬·최댓값 API 는 전부 이 형태를 쓴다. `Comparable` 계약 자체는 [`../28-comparable-comparator/`](../28-comparable-comparator/) 가 정본이다.

**그런데 표준 라이브러리는 한 발 더 간다.** `Collections.max` 의 실제 시그니처를 `src.zip` 에서 읽었다.

```java
public static <T extends Object & Comparable<? super T>> T max(Collection<? extends T> coll) {
```

`Comparable<T>` 가 아니라 **`Comparable<? super T>`** 다. 왜 그런지 실행으로 확인했다.

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

```text
Animal 이 Comparable<Animal> 을 구현하고, Dog extends Animal 일 때

  Dog 는 Comparable<Dog> 인가?          Dog 는 Comparable<? super Dog> 인가?
  +-----------------------------+      +-----------------------------+
  | Dog 가 구현한 것은           |      | Comparable<Animal> 이고     |
  |   Comparable<Animal>        |      | Animal 은 Dog 의 상위다      |
  |   != Comparable<Dog>        |      |   -> 만족한다               |
  | -> 아니다                   |      |                             |
  +-----------------------------+      +-----------------------------+
      maxStrict(List<Dog>) 컴파일 에러     maxSuper(List<Dog>) 통과
```

- **상속 계층에서 `Comparable` 을 상위가 구현하면** `Comparable<T>` 바운드는 하위 타입을 거부한다.
- 그래서 실무 API 는 `Comparable<? super T>` 를 쓴다 — 왜 `? super` 인지는 [`../18-wildcards-pecs/`](../18-wildcards-pecs/) 가 정본이다.

비용 — 없다. 선언이 길어지는 것이 대가다.

### (7) 타입 파라미터 가리기와 inner 클래스

**언제 쓰나** — 제네릭 클래스 안에 제네릭 메서드나 inner 클래스를 둘 때.

**출력** (`Ex.java (17-h)`, JDK 21.0.5)

```text
--- 타입 파라미터 가리기
  메서드 안의 T 는 바깥 T 와 다른 타입 파라미터다: 42
  inner.fromOuter = 안쪽이 바깥 T 를 쓴다
```

```java
static class Outer<T> {
    T outerValue;
    <T> void shadow(T t) { ... }     // 같은 이름의 새 T — 바깥 T 를 가린다
    class Inner { T fromOuter; }     // inner 클래스는 바깥 T 를 쓸 수 있다
}
```

```text
이름이 같아도 다른 빈칸이다

  Outer<String>                          o.<Integer>shadow(42)
  +-------------------------+            +-------------------------+
  | 바깥 T = String         |            | 메서드 T = Integer       |
  |   outerValue : String   |            |   t : Integer           |
  |   Inner.fromOuter : String|          | 바깥 T 는 가려져서 못 쓴다|
  +-------------------------+            +-------------------------+
```

그림 해설 (한 단계씩):

- 메서드가 같은 이름의 타입 파라미터를 선언하면 **바깥 것을 가린다**(shadowing). 컴파일은 되지만 읽기가 나쁘다.
- **inner 클래스**(non-static 중첩 클래스)는 바깥 인스턴스에 딸려 있으므로 **바깥 `T` 를 쓸 수 있다.**
- **`static` 중첩 클래스**는 못 쓴다 — (2)의 `static` 규칙과 같은 이유다.
- `Outer<String>.Inner in = o.new Inner();` 라는 선언 형태가 이 관계를 그대로 보여 준다.

비용 — 없다. 가려진 이름을 사람이 헷갈리는 것이 비용이다.

### (8) 다이아몬드와 `var` — 어디까지 생략되나

**언제 쓰나** — 제네릭 객체를 만들 때.

**출력** (`Ex.java (17-a)`, JDK 21.0.5)

```text
--- 다이아몬드 추론
m = {k=[1]}
var + 다이아몬드 = Box[var 로 받으면] / get().length() = 9
```

```java
Map<String, List<Integer>> m = new HashMap<>();       // <> 가 좌변에서 추론된다
m.computeIfAbsent("k", k -> new ArrayList<>()).add(1); // <> 가 파라미터 타입에서 추론된다
var inferred = new Box<>("var 로 받으면");             // <> 가 인자에서 추론된다
```

```text
무엇에서 추론하나

  Map<String,List<Integer>> m = new HashMap<>();
                                            ^^ 좌변의 선언 타입에서

  m.computeIfAbsent("k", k -> new ArrayList<>())
                                            ^^ 파라미터의 기대 타입에서

  var inferred = new Box<>("문자열");
      ^^^                    ^^      인자에서 T=String, 다시 var 가 Box<String>
```

그림 해설 (한 단계씩):

- 다이아몬드 `<>`(Java 7)는 **기대 타입이 있는 자리**에서만 생략을 해 준다.
- `var`(Java 10)와 함께 쓰면 **인자 → 타입 파라미터 → 변수 타입** 순으로 흘러간다.\
  출력의 `get().length()` 가 `9` 를 낸 것이 `Box<String>` 으로 제대로 추론됐다는 증거다.
- `var x = new ArrayList<>();` 처럼 **양쪽 다 정보가 없으면** `ArrayList<Object>` 가 된다. 이것이 `var` 의 함정이다.

비용 — 없다. 읽는 사람이 타입을 못 읽게 되는 것이 대가다.

## 문법 — 형태와 규칙

직접 쓴 최소 예제다. 묻는 것 하나만 남겼다.

### 선언의 형태

```java
class Box<T> { }                                   // 클래스 타입 파라미터
class Pair<K, V> { }                               // 여러 개
class NumberBox<T extends Number> { }              // 바운드
class Multi<T extends Comparable<T> & Serializable> { }  // 다중 바운드 (& 로 잇는다)
class Node<T extends Node<T>> { }                  // 재귀 바운드
interface Repo<T, ID> { }                          // 인터페이스도 같다

static <T> List<T> listOfTwo(T a, T b) { }         // 제네릭 메서드 — 반환 타입 앞
static <T, U extends T> void copyInto(List<T> d, List<U> s) { }   // 파라미터끼리 바운드
<T> Box<T> instanceGeneric(T t) { return null; }   // 인스턴스 메서드도 가능
<T> Box(T seed) { }                                // 제네릭 생성자도 가능
```

### 호출의 형태

```java
Box<String> b = new Box<>("x");          // 다이아몬드 (7+)
var c = new Box<>("x");                  // var + 다이아몬드 (10+)
List<String> l = listOfTwo("a", "b");    // 추론
List<Object> o = Ex.<Object>listOfTwo(1, "a");   // 명시적 타입 인자 — 이름 앞, 수신자 뒤
this.<String>instanceGeneric("x");       // 인스턴스 메서드는 this. 를 붙인다
```

### 이름 관례

| 이름 | 관례상 쓰는 곳 |
|---|---|
| `T` | Type — 일반 |
| `E` | Element — 컬렉션의 원소 |
| `K`, `V` | Key, Value — 맵 |
| `R` | Result — 반환 타입 |
| `N` | Number |
| `U`, `S` | 두 번째·세 번째 타입 |

`java.util` 의 실제 선언에서 확인할 수 있다 — `List<E>`·`Map<K,V>`·`Function<T,R>`.

### 안 되는 것 한눈에

| 쓰려 한 것 | 결과 | 메시지 |
|---|---|---|
| `static` 필드·메서드에서 클래스 `T` | 에러 | `non-static type variable T cannot be referenced from a static context` |
| `List<int>` · `Box<int>` | 에러 | `unexpected type / required: reference / found: int` |
| 바운드 위반 `NumberBox<String>` | 에러 | `type argument String is not within bounds of type-variable T` |
| `<T extends Runnable & Object>` | 에러 | `interface expected here` |
| `<T extends Number & String>` | 에러 | `interface expected here` |
| `<T extends T>` | 에러 | `cyclic inheritance involving T` |
| 제네릭 애너테이션 `@interface A<T>` | 에러 | `annotation interface A cannot be generic` |

마지막 줄의 정본은 [`../16-annotations/`](../16-annotations/) 다.

## 어디서 틀리나

이 주제의 값어치는 전부 여기 있다.

### 1. `static` 팩토리를 만들다 막힌다

```text
error: non-static type variable T cannot be referenced from a static context
```

- 제네릭 클래스에 `static Box<T> empty()` 를 쓰려다 만난다.
- **고치는 법은 하나** — `static <U> Box<U> empty()` 로 **자기 타입 파라미터를 새로 선언**한다.
- 이 규칙을 "제네릭 클래스에는 static 을 못 쓴다"로 외우면 틀린다. 쓸 수 있고, **클래스의 `T` 만 못 쓴다.**

### 2. 기본형을 타입 인자로 쓴다

```text
Ex.java:8: error: unexpected type
        NumberBox<int> b = null;                            // (B) 기본형을 타입 인자로
                  ^
  required: reference
  found:    int
```

- `List<int>` 는 안 된다. **래퍼**(`Integer`)를 써야 한다.
- 이 규칙의 뿌리와 박싱 비용은 [`../01-primitives-and-wrappers/`](../01-primitives-and-wrappers/) 가 정본이다.
- 그래서 `IntStream`·`int[]` 같은 **기본형 전용 API** 가 따로 있다.

### 3. 추론이 조용히 이상한 타입을 만든다

```text
listOfTwo(1, "a")          = [1, a]  <- 컴파일된다
```

- **에러가 안 난다.** `T` 가 교차 타입으로 추론돼 통과한다.
- 문제는 **호출한 자리가 아니라 반환값을 쓰는 자리**에서 터진다.
- 그래서 제네릭 메서드는 **인자의 타입이 정말 같아야 하는지** 설계에서 정해야 한다.\
  다르게 받아야 하면 파라미터를 `<T, U>` 로 나누거나 와일드카드를 쓴다([`../18-wildcards-pecs/`](../18-wildcards-pecs/)).

### 4. 바운드를 로 타입으로 쓴다

```text
warning: [rawtypes] found raw type: Comparable
warning: [unchecked] unchecked call to compareTo(T) as a member of the raw type Comparable
```

- `<T extends Comparable>` 는 **컴파일된다.** 경고만 나온다.
- 그 결과 `compareTo(Object)` 를 부르게 되고, **타입 안전이 그 지점에서 끊긴다.**
- `-Xlint:all` 을 켜지 않으면 경고도 안 보인다.

### 5. `Comparable<T>` 로 바운드를 좁게 잡는다

```text
error: method maxStrict in class Ex cannot be applied to given types;
  reason: inference variable T has incompatible equality constraints Animal,Dog
```

- `Animal implements Comparable<Animal>` 이고 `Dog extends Animal` 이면 **`List<Dog>` 을 못 받는다.**
- `Dog` 가 구현한 것은 `Comparable<Animal>` 이지 `Comparable<Dog>` 가 아니기 때문이다.
- 표준 라이브러리가 `Comparable<? super T>` 를 쓰는 이유가 이것이다.

### 6. `var` 와 다이아몬드를 같이 쓴다

**출력** (`Ex.java (17-j)`, JDK 21.0.5)

```text
--- var + 빈 다이아몬드
  list = [문자열, 42] / get(0) 의 정적 타입은 Object
  typed.get(0).length() = 3
```

```text
$ javac  ... var list = new ArrayList<>(); list.add("x"); String s = list.get(0);
error: incompatible types: Object cannot be converted to String
```

- 양쪽 다 정보가 없으면 **`ArrayList<Object>`** 가 된다. **에러도 경고도 없다** — `String` 과 `int` 를 한 리스트에 넣어도 통과한다.
- 꺼낼 때서야 터진다. 위 에러가 그 자리다.
- `var` 를 쓸 거면 **생성 쪽에 타입 인자를 적는다** — `var typed = new ArrayList<String>();` (출력의 마지막 줄)

## 구현 세부사항 대 언어 보장

이 절은 **"어디까지 믿어도 되나"**를 가른다.

| 항목 | 누가 보장하나 | 근거 |
|---|---|---|
| `static` 문맥에서 클래스 타입 변수 금지 | **JLS (언어 보장)** | JLS §8.1.2 |
| 다중 바운드에서 클래스는 최대 하나·맨 앞 | **JLS (언어 보장)** | JLS §4.4 |
| 기본형이 타입 인자가 못 되는 것 | **JLS (언어 보장)** | JLS §4.5 |
| 바운드 없는 `<T>` = `<T extends Object>` | **JLS (언어 보장)** | JLS §4.4 |
| 타입 추론이 교차 타입을 만드는 것 | **JLS (언어 보장)** | JLS §18 |
| `Collections.max` 가 `Comparable<? super T>` 를 쓰는 것 | **javadoc (API 계약)** | `Collections.java` 실파일 |
| 교차 타입에 `Constable`·`ConstantDesc` 가 들어간 것 | **구현 세부** | `Integer`·`String` 이 구현한 인터페이스 목록에 달렸다(12 에서 추가) |
| `javac` 에러 문구 (`INT#1`·`CAP#1` 표기) | **구현 세부** | 관찰값(17·21·25 동일) |
| `Counter<String>.class == Counter<Integer>.class` | **JLS + JVMS** | 소거의 결과 — [`../19-type-erasure/`](../19-type-erasure/) |

### 교차 타입의 구성원은 라이브러리에 달려 있다

```text
INT#1 extends Object,Serializable,Comparable<? extends INT#2>,Constable,ConstantDesc
```

- `Constable`·`ConstantDesc` 는 **Java 12 에서 `Integer`·`String` 에 붙은 인터페이스**다.
- 즉 이 목록은 **JDK 버전에 따라 달라질 수 있다.** 17·21·25 에서는 같았다(`diff` 로 확인).
- 외울 것은 목록이 아니라 **"공통 상위 타입을 만들어 통과시킨다"**는 성질이다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 타입 파라미터를 어디에 | 이유 |
|---|---|---|
| 필드가 그 타입을 들고 있어야 한다 | **클래스** | 인스턴스 수명 동안 같아야 한다 |
| 여러 메서드가 같은 타입을 주고받는다 | **클래스** | 관계를 타입으로 고정한다 |
| 한 호출 안에서만 관계가 성립한다 | **메서드** | 호출마다 다른 타입이어도 된다 |
| `static` 유틸이다 | **메서드** | 클래스 타입 파라미터를 못 쓴다 |
| 인자와 반환 타입이 이어져 있다 | **메서드** | `<T> T first(List<T>)` |

| 바운드를 붙일까 | 판단 |
|---|---|
| `T` 위에서 메서드를 부른다 | 붙인다 — 안 붙이면 `Object` 의 것만 쓸 수 있다 |
| 담기만 한다 | 안 붙인다 — 받을 수 있는 타입을 좁힐 이유가 없다 |
| 비교·정렬이 필요하다 | `<T extends Comparable<? super T>>` — `<T>` 만으로는 `compareTo` 를 못 부른다 |
| 여러 조건이 필요하다 | `&` 로 잇되 **클래스는 맨 앞 하나**만 |

판단 규칙 두 줄.

- **`T` 로 무엇을 할 건지 먼저 적어 보고, 그것이 `Object` 에 없으면 바운드를 붙인다.**
- **클래스에 둘지 메서드에 둘지는 "이 타입이 인스턴스의 상태인가"로 가른다.**

## 핵심 문장

- 타입 파라미터의 범위는 **클래스 전체**이거나 **메서드 하나**다. 전자는 인스턴스마다 고정되고 후자는 호출마다 추론된다.
- `static` 멤버는 인스턴스와 무관하게 **하나뿐**이라 클래스 타입 파라미터를 쓸 수 없다 — 쓰려면 **자기 타입 파라미터를 새로 선언**한다.
- 바운드 없는 `<T>` 는 **`<T extends Object>`** 다. `T` 위에서 부를 수 있는 것은 `Object` 의 메서드뿐이다.
- 다중 바운드는 **`&`** 로 잇고 **클래스는 최대 하나·맨 앞**이다. 어기면 `interface expected here` 다.
- 추론은 인자들의 **공통 상위 타입(교차 타입)**을 만들어서라도 통과시킨다 — **에러가 안 나는 것이 위험한 자리**다.
- 재귀 바운드 `<T extends Comparable<T>>` 는 **"T 는 T 와 비교할 수 있다"**를 타입으로 적은 것이고, 상속 계층까지 받으려면 **`Comparable<? super T>`** 여야 한다.

## 관련 자료

- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 17번)
- [`../18-wildcards-pecs/`](../18-wildcards-pecs/) — **그쪽은 `? extends`/`? super` 가 읽기·쓰기를 어떻게 막는가부터, 여기는 타입 파라미터를 선언하는 자리까지.**\
  "`T` 를 어디에 쓰나"는 여기, "`?` 를 언제 쓰나"는 그쪽이다
- [`../19-type-erasure/`](../19-type-erasure/) — **그쪽은 선언한 `T` 가 런타임에 무엇으로 남는가가 정본.**\
  `Counter<String>.class == Counter<Integer>.class` 가 왜 참인지의 이유가 그쪽에 있다
- [`../09-inheritance-overriding/`](../09-inheritance-overriding/) — 바운드가 **상속 계층**을 전제로 동작한다. `<T extends Resource>` 가 받는 것이 무엇인지의 규칙
- [`../05-arrays/`](../05-arrays/) — 배열은 **공변**이고 제네릭은 **불공변**이다. 그 대비는 [`../18-wildcards-pecs/`](../18-wildcards-pecs/) 가 정본
- [`../01-primitives-and-wrappers/`](../01-primitives-and-wrappers/) — `List<int>` 가 안 되는 이유. 래퍼와 박싱 비용
- [`../08-method-declaration-overloading/`](../08-method-declaration-overloading/) — 제네릭 메서드의 타입 추론이 **오버로딩 해소**와 어떻게 맞물리는가
- [`../31-functional-interfaces/`](../31-functional-interfaces/) — `Function<T,R>`·`Predicate<T>` 가 전부 제네릭 인터페이스다. 실사용 예
- [`../16-annotations/`](../16-annotations/) — 애너테이션이 **제네릭이 될 수 없다**는 제약
- [`../28-comparable-comparator/`](../28-comparable-comparator/) — **재귀 바운드가 필요한 이유의 반대편.** 여기는 바운드를 **어떻게 적나**까지, 그쪽은 **전순서 계약과 위반의 결과**
- [**39번 주제**](../39-collections-framework-map/)(컬렉션 지도) — `List<E>`·`Map<K,V>` 의 타입 파라미터가 무엇을 뜻하는지
- [`../../../../../../history/java/java-5.md`](../../../../../../history/java/java-5.md) — 제네릭이 **언제·왜 들어왔나**가 정본. 여기는 **어떻게 쓰고 무엇을 못 하나**

## 용어 풀이

- **제네릭(generics)** — 타입을 파라미터로 받아 여러 타입에 같은 코드를 쓰게 하는 기능(Java 5).
- **타입 파라미터(type parameter)** — 선언에 쓰는 `<T>` 같은 이름. 나중에 실제 타입으로 채워진다.
- **타입 인자(type argument)** — 타입 파라미터 자리에 실제로 넣은 타입. `Box<String>` 의 `String`.
- **파라미터화 타입(parameterized type)** — 타입 인자를 채운 타입. `List<String>` 이 그것이다.
- **바운드(bound)** — 타입 인자가 만족해야 하는 상한. `<T extends Number>`.
- **다중 바운드(multiple bounds)** — `&` 로 여러 조건을 잇는 것. 클래스는 최대 하나이고 맨 앞이어야 한다.
- **재귀 바운드(recursive bound)** — 바운드에 자기 자신이 나오는 것. `<T extends Comparable<T>>`.
- **제네릭 메서드(generic method)** — 자기 타입 파라미터를 선언한 메서드. 반환 타입 앞에 `<T>` 를 쓴다.
- **타입 추론(type inference)** — 타입 인자를 적지 않아도 컴파일러가 정해 주는 것(JLS §18).
- **교차 타입(intersection type)** — 여러 타입을 동시에 만족하는, 소스에 이름을 쓸 수 없는 타입. 추론 결과로 나온다.
- **다이아몬드(`<>`)** — `new HashMap<>()` 처럼 생성 쪽 타입 인자를 생략하는 문법(Java 7, 익명 클래스는 9).
- **로 타입(raw type)** — 타입 인자를 아예 안 쓴 제네릭 타입. `List` 처럼. 호환성을 위해 남아 있고 경고가 난다.
- **가리기(shadowing)** — 안쪽 선언이 같은 이름의 바깥 선언을 가리는 것. 메서드 타입 파라미터가 클래스 것을 가릴 수 있다.

## 더 들어가면

- **제네릭 생성자도 있다.** 클래스가 제네릭이 아니어도 생성자만 제네릭일 수 있다.

```java
class Holder { <T> Holder(T seed) { } }
new <String>Holder("x");        // 명시적 타입 인자를 주는 형태 (거의 안 쓴다)
```

**출력** (`Ex.java (17-j)`, JDK 21.0.5)

```text
--- 제네릭 생성자
  생성자 T 로 받은 것 = 추론
  생성자 T 로 받은 것 = 명시
```

- **`final` 클래스를 바운드로 쓰면 컴파일된다.** `<T extends String>` 은 에러가 아니다(`Ex.java (17-e)` 에서 확인).\
  `T` 가 될 수 있는 것이 `String` 하나뿐이라 의미가 없을 뿐이다.
- **타입 파라미터끼리 바운드로 쓸 수 있다.** `<T, U extends T>` 가 그 형태다.

```text
copyInto(List<Number>, List<Integer>) = [1.0, 1, 2, 3]
```

  다만 이 형태보다 와일드카드(`List<? extends T>`)가 읽기 쉽다 — [`../18-wildcards-pecs/`](../18-wildcards-pecs/).
- **타입 파라미터 이름은 클래스 파일에 남는다.** 값은 안 남지만 이름과 바운드는 `Signature` 속성에 남는다.

```text
Counter 의 타입 파라미터 = [T]
  바운드 = [class java.lang.Object]
```

  이 비대칭(**이름은 남고 인자는 사라진다**)이 [`../19-type-erasure/`](../19-type-erasure/) 의 본문이다.
