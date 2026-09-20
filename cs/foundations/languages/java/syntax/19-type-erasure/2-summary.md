# java/syntax/19 — 타입 소거: 런타임에 없는 것·제네릭 배열·브리지 메서드 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [JLS SE 21 §4.6 Type Erasure](https://docs.oracle.com/javase/specs/jls/se21/html/jls-4.html) · [§4.8 Raw Types](https://docs.oracle.com/javase/specs/jls/se21/html/jls-4.html) · [§8.4.8.3 Requirements in Overriding and Hiding](https://docs.oracle.com/javase/specs/jls/se21/html/jls-8.html) · [JVMS SE 21 §4.7.9 The Signature Attribute](https://docs.oracle.com/javase/specs/jvms/se21/html/jvms-4.html) · [JVMS §4.3 Descriptors](https://docs.oracle.com/javase/specs/jvms/se21/html/jvms-4.html) · JDK 21.0.5 표준 라이브러리 소스(`lib/src.zip`).
> **실행 검증** — 이 문서의 모든 출력·에러·바이트코드는 Temurin **JDK 21.0.5** 에서 실제로 돌려 얻은 것이다.\
> `Ex.java (19-b)` `(19-d)` `(19-e)` `(19-f)` 는 **17.0.13 · 21.0.5 · 25.0.1** 에서 다 돌렸고 출력이 한 글자도 다르지 않았다.\
> 컴파일 에러 `(19-c1)` `(19-c3)` 도 17 과 25 에서 `diff` 로 대조해 **문자 단위로 같았다.**\
> **"세 곳에서 같았다"는 관찰이지 보장이 아니다** — 보장은 JLS·JVMS 인용으로만 적었다.
> **버전** — 제네릭과 소거는 **Java 5**. `@SafeVarargs` 는 **7**(`src.zip` 의 `@since 1.7` 확인).
> **범위** — 타입 파라미터를 **선언하는 것**은 [`../17-generic-declarations/`](../17-generic-declarations/) 가,\
> `? extends`/`? super` 는 [`../18-wildcards-pecs/`](../18-wildcards-pecs/) 가 정본이다.\
> 여기는 **컴파일 후에 무엇이 남고 무엇이 사라지나**만 다룬다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 JLS·JVMS 로, 출력은 실행과 `javap` 로 접지했다.

## 한눈에 — 쉽게 말하면

**소거는 "실행에 쓰는 표에서는 타입 인자를 지우고, 설명서에는 남겨 두는 것"이다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 공장의 **작업 지시서** | 클래스 파일의 **descriptor** — JVM 이 실제로 쓰는 타입 |
| 옆에 붙은 **설명 주석** | 클래스 파일의 **`Signature` 속성** — 컴파일러·리플렉션이 읽는 제네릭 정보 |
| 지시서에서 지워진 "빨간색" | 타입 인자 `<String>` |
| 지시서를 보고 일하는 작업자 | JVM (실행) |
| 설명 주석까지 읽는 검수자 | javac · 리플렉션의 `getGeneric*` |
| 자재 받을 때 한 번 하는 색 검사 | 컴파일러가 끼워 넣은 `checkcast` |

- 지시서에는 **"리스트를 가져온다"**만 적혀 있고 "문자열 리스트"라는 말은 없다.\
  그래서 JVM 은 `List<String>` 과 `List<Integer>` 를 **구별하지 못한다.**
- 그런데 **설명 주석에는 남아 있다.** `javap -v` 로 `Signature: Ljava/util/List<Ljava/lang/String;>;` 를 볼 수 있다.
- 이 비대칭 때문에 리플렉션에서 이상한 일이 생긴다 —\
  **필드·메서드의 시그니처는 읽히는데, 손에 든 객체의 타입 인자는 못 읽는다.**

```text
javac 가 한 일 — 같은 한 줄에서 갈린다

  소스           List<String> names;
                        |
                        +--------------------------+
                        |                          |
                  descriptor                  Signature 속성
                  Ljava/util/List;            Ljava/util/List<Ljava/lang/String;>;
                        |                          |
                  JVM 이 쓴다                 javac·리플렉션이 읽는다
                  (String 정보 없음)           (String 정보 있음)
```

**똑같은 구조로** Java 가 동작한다: 지시서 = descriptor, 설명 주석 = `Signature`, 자재 검사 = `checkcast`.

실무에서 이게 물리는 자리는 **JSON 역직렬화**다.\
`mapper.readValue(json, List.class)` 로는 원소 타입을 줄 방법이 없어서, 라이브러리들이 **`TypeReference<List<User>>() {}`** 라는 이상한 문법을 요구한다.\
그 문법이 동작하는 이유가 바로 **`Signature` 속성은 지워지지 않는다**는 것이다.

> **타입 소거(type erasure)** — 컴파일 후 타입 인자를 지우고, 타입 변수는 그 바운드(없으면 `Object`)로 바꾸는 것(JLS §4.6).\
> 예: `List<String>` 은 `List` 가 되고, `<T extends Number> T get()` 의 반환 타입은 `Number` 가 된다.

> **descriptor** — JVM 이 필드·메서드의 타입을 적는 형식. 제네릭이 없다(JVMS §4.3).\
> 예: `List<String> names` 의 descriptor 는 `Ljava/util/List;` 다.

> **`Signature` 속성** — 제네릭 정보를 따로 적어 두는 클래스 파일 속성(JVMS §4.7.9).\
> 예: 같은 필드의 `Signature` 는 `Ljava/util/List<Ljava/lang/String;>;` 다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 네 질문을 둔다.

1. 소거는 **정확히 무엇을 지우고 무엇을 남기는가** — `javap` 로 어떻게 확인하는가.
2. 그래서 런타임에 **못 하는 것들**(`new T[]`·`instanceof List<String>`·오버로드)은 각각 어떤 에러가 나는가.
3. **힙 오염**은 어떤 경로로 생기고 왜 조용한가.
4. **`TypeToken`/super type token** 은 왜 동작하는가 — 소거된다면서.

## 동작 방식

### (1) 무엇이 지워지나 — `javap -c` 로 본다

**언제 쓰나** — "제네릭이 런타임에 사라진다"는 말을 확인할 때.

```java
List<String> names = new ArrayList<>();
Map<String, List<Integer>> index = new HashMap<>();

int firstLength() {
    names.add("hello");
    String s = names.get(0);     // 캐스팅을 안 썼는데 바이트코드에는?
    return s.length();
}
```

**`javap -c -p Ex.class` 출력 그대로** (`Ex.java (19-a)`, JDK 21.0.5)

```text
  int firstLength();
    Code:
       0: aload_0
       1: getfield      #10                 // Field names:Ljava/util/List;
       4: ldc           #31                 // String hello
       6: invokeinterface #33,  2           // InterfaceMethod java/util/List.add:(Ljava/lang/Object;)Z
      11: pop
      12: aload_0
      13: getfield      #10                 // Field names:Ljava/util/List;
      16: iconst_0
      17: invokeinterface #23,  2           // InterfaceMethod java/util/List.get:(I)Ljava/lang/Object;
      22: checkcast     #37                 // class java/lang/String
      25: astore_1
      26: aload_1
      27: invokevirtual #39                 // Method java/lang/String.length:()I
      30: ireturn
```

```text
소스에 없던 것이 하나 생기고, 있던 것이 하나 사라졌다

  소스                                    바이트코드
  +---------------------------------+    +---------------------------------+
  | List<String> names;             |    | Field names:Ljava/util/List;    |
  |          ^^^^^^^^ 있다          |    |                  <String> 없다  |
  |                                 |    |                                 |
  | names.add("hello");             |    | List.add:(Ljava/lang/Object;)Z  |
  |                                 |    |           파라미터가 Object     |
  |                                 |    |                                 |
  | String s = names.get(0);        |    | List.get:(I)Ljava/lang/Object;  |
  |   캐스팅을 안 썼다               |    | checkcast class java/lang/String|
  |                                 |    |   <- javac 가 끼워 넣었다        |
  +---------------------------------+    +---------------------------------+
```

그림 해설 (한 단계씩):

- 필드의 타입이 **`Ljava/util/List;`** 다 — `<String>` 이 없다.
- `add` 의 파라미터가 **`Ljava/lang/Object;`** 다 — `List` 의 `E` 가 `Object` 로 소거됐다.
- `get` 의 반환도 `Object` 인데, 바로 뒤에 **`checkcast class java/lang/String`** 이 붙는다.\
  **캐스팅을 소스에 안 썼는데 바이트코드에는 있다** — javac 가 끼워 넣은 것이다.
- 그래서 제네릭은 **"컴파일러가 캐스팅을 대신 써 주는 것"**이라고 요약된다.

바운드가 있으면 `Object` 가 아니라 **바운드로** 소거된다.

```text
  static <T extends java.lang.Comparable<T>> T max(java.util.List<T>);
    Code:
       0: aload_0
       1: iconst_0
       2: invokeinterface #23,  2           // InterfaceMethod java/util/List.get:(I)Ljava/lang/Object;
       7: checkcast     #29                 // class java/lang/Comparable
      10: areturn
```

- `T extends Comparable<T>` 라서 `checkcast` 대상이 **`Comparable`** 이다.
- 다중 바운드라면 **맨 앞의 것**으로 소거된다.

비용 — `checkcast` 명령 하나. 제네릭을 쓰든 직접 캐스팅하든 **바이트코드는 같다.**

### (2) 무엇이 남나 — `Signature` 속성

**언제 쓰나** — "그럼 IDE 는 어떻게 타입을 아나"를 물을 때.

**`javap -v -p Ex.class` 출력 그대로** (`Ex.java (19-a)`, JDK 21.0.5 — 관련 줄만 뽑았다)

```text
  java.util.List<java.lang.String> names;
    descriptor: Ljava/util/List;
    flags: (0x0000)
    Signature: #64                          // Ljava/util/List<Ljava/lang/String;>;

  java.util.Map<java.lang.String, java.util.List<java.lang.Integer>> index;
    descriptor: Ljava/util/Map;
    flags: (0x0000)
    Signature: #65                          // Ljava/util/Map<Ljava/lang/String;Ljava/util/List<Ljava/lang/Integer;>;>;

  static <T extends java.lang.Comparable<T>> T max(java.util.List<T>);
    descriptor: (Ljava/util/List;)Ljava/lang/Comparable;
    flags: (0x0008) ACC_STATIC
    Signature: #70                          // <T::Ljava/lang/Comparable<TT;>;>(Ljava/util/List<TT;>;)TT;
```

제네릭 클래스도 마찬가지다.

```text
class Ex$Box<T extends java.lang.Number> extends java.lang.Object
  T value;
    descriptor: Ljava/lang/Number;
    Signature: #14                          // TT;
  T get();
    descriptor: ()Ljava/lang/Number;
    Signature: #19                          // ()TT;
  void set(T);
    descriptor: (Ljava/lang/Number;)V
    Signature: #22                          // (TT;)V
Signature: #23                              // <T:Ljava/lang/Number;>Ljava/lang/Object;
```

```text
지워진 것과 남은 것을 나란히

  지워진 쪽 (descriptor — JVM 이 쓴다)      남은 쪽 (Signature — 도구가 읽는다)
  +-----------------------------------+    +-------------------------------------------+
  | Ljava/util/List;                  |    | Ljava/util/List<Ljava/lang/String;>;      |
  | Ljava/util/Map;                   |    | Ljava/util/Map<Ljava/lang/String;         |
  |                                   |    |   Ljava/util/List<Ljava/lang/Integer;>;>; |
  | (Ljava/util/List;)Ljava/lang/     |    | <T::Ljava/lang/Comparable<TT;>;>          |
  |   Comparable;                     |    |   (Ljava/util/List<TT;>;)TT;              |
  | Ljava/lang/Number;   (T value)    |    | TT;                                       |
  +-----------------------------------+    +-------------------------------------------+
     실행에 쓰인다                              실행에는 안 쓰인다
```

그림 해설 (한 단계씩):

- **둘 다 클래스 파일 안에 있다.** 하나가 다른 것을 대체한 것이 아니다.
- **`descriptor`** 는 JVM 이 메서드를 찾고 스택을 검증하는 데 쓴다. 제네릭이 없다.
- **`Signature`** 는 JVM 이 실행에 쓰지 않는다. javac 가 다른 클래스를 컴파일할 때, IDE 가 자동완성할 때, 리플렉션의 `getGeneric*` 이 읽는다.
- 표기 읽는 법 — `TT;` 는 "타입 변수 T", `<T::Ljava/lang/Comparable<TT;>;>` 는 "T 의 바운드가 `Comparable<T>` 인 인터페이스 바운드"다(`::` 는 클래스 바운드가 없다는 뜻).
- 그래서 **"제네릭은 런타임에 완전히 사라진다"는 말은 정확하지 않다.** 사라지는 것은 **실행 경로**에서다.

비용 — 클래스 파일이 조금 커진다. 실행 성능에는 영향이 없다.

### (3) 그래서 생기는 비대칭 — 선언은 읽히고 인스턴스는 안 읽힌다

**언제 쓰나** — 프레임워크가 "이 필드는 `List<User>` 구나"를 어떻게 아는지 궁금할 때.

**출력** (`Ex.java (19-b)`, JDK 21.0.5 — 17·25 에서도 동일)

```text
--- 선언은 읽힌다 (Signature 속성)
getType()        = interface java.util.List
getGenericType() = java.util.List<java.lang.String>
  rawType        = interface java.util.List
  actualTypeArgs = [class java.lang.String]
index generic    = java.util.Map<java.lang.String, java.util.List<java.lang.Integer>>
count 파라미터(소거) = [interface java.util.List, interface java.util.Set]
count 파라미터(제네릭)= [java.util.List<java.lang.String>, java.util.Set<? extends java.lang.Number>]
count 반환(소거)     = interface java.util.Map
count 반환(제네릭)   = java.util.Map<java.lang.String, java.lang.Integer>
max 반환(소거)       = interface java.lang.Comparable
max 반환(제네릭)     = T
  타입 파라미터 T 의 바운드 = [java.lang.Comparable<T>]
--- 인스턴스는 안 읽힌다
strings.getClass() = class java.util.ArrayList
ints.getClass()    = class java.util.ArrayList
같은 클래스인가     = true
getClass().getTypeParameters() = [E]
  -> 이름(E)만 남았고, String 인지 Integer 인지는 어디에도 없다
getGenericSuperclass() = java.util.AbstractList<E>
```

```text
같은 리플렉션 API 안에서 갈린다

  선언에서 읽을 때                          인스턴스에서 읽을 때
  +-----------------------------------+    +-----------------------------------+
  | Field.getGenericType()            |    | obj.getClass()                    |
  |   -> List<String>                 |    |   -> class java.util.ArrayList    |
  | Method.getGenericParameterTypes() |    | getClass().getTypeParameters()    |
  |   -> Set<? extends Number> 까지    |    |   -> [E]  (이름만)                |
  |                                   |    |                                   |
  | 근거: Signature 속성이 남아 있다   |    | 근거: 객체에는 아무 표시도 없다     |
  +-----------------------------------+    +-----------------------------------+
```

그림 해설 (한 단계씩):

- **선언**(필드·메서드·클래스)의 제네릭 정보는 **`Signature` 속성에 있으니 읽힌다.**\
  `getGenericType()`·`getGenericParameterTypes()`·`getGenericReturnType()` 이 그것이다.
- **인스턴스**에는 **아무 표시도 없다.** `new ArrayList<String>()` 과 `new ArrayList<Integer>()` 가 **같은 클래스**다.
- `getTypeParameters()` 가 `[E]` 를 주는 것도 **선언에서 읽은 것**이다 — 이름과 바운드일 뿐 인자가 아니다.
- 그래서 **DI·ORM·JSON 라이브러리는 "필드를 보고" 동작한다.** 객체를 보고는 못 한다.

**소거된 리스트에 아무거나 넣어 보면**

```text
--- 그래서 소거된 리스트에 아무거나 넣을 수 있다
strings = [a, 42]
catch -> java.lang.ClassCastException: class java.lang.Integer cannot be cast to class java.lang.String (java.lang.Integer and java.lang.String are in module java.base of loader 'bootstrap')
```

- `List raw = strings; raw.add(42);` 가 **런타임에 통과한다.** `ArrayList` 안에는 검사가 없다.
- 터지는 곳은 **꺼내는 자리**다 — javac 가 끼워 넣은 `checkcast` 가 거기 있기 때문이다.
- 즉 **오염은 조용히 되고 발각은 나중에** 된다. 이것이 (6)의 힙 오염과 같은 구조다.

비용 — 없다. 리플렉션 조회 비용뿐이다.

### (4) 런타임에 못 하는 것들 — 전부 던져 봤다

**언제 쓰나** — `new T[n]` 을 쓰려다 막혔을 때.

**`javac` 출력 그대로** (`Ex.java (19-c1)`, JDK 21.0.5 — 17·25 에서도 동일)

```text
Ex.java:3: error: generic array creation
    static <T> T[] makeArray(int n) { return new T[n]; }          // (A)
                                             ^
Ex.java:4: error: unexpected type
    static <T> T makeOne() { return new T(); }                    // (B)
                                        ^
  required: class
  found:    type parameter T
  where T is a type-variable:
    T extends Object declared in method <T>makeOne()
Ex.java:5: error: cannot select from a type variable
    static <T> Class<T> clazz() { return T.class; }               // (C)
                                          ^
Ex.java:7: error: unexpected type
        try { r.run(); } catch (T e) { }                          // (D)
                                ^
  required: class
  found:    type parameter T
  where T is a type-variable:
    T extends Exception declared in method <T>c(Runnable)
Ex.java:9: error: generic array creation
    static List<String>[] genericArray = new List<String>[3];     // (E)
                                         ^
5 errors
```

**(F) `new List<?>[3]` 와 (G) `new List[3]` 은 통과했다.**

**`instanceof` 와 캐스팅** (`Ex.java (19-c2)`)

```text
Ex.java:5: error: Object cannot be safely cast to List<String>
        System.out.println(o instanceof List<String>);      // (A)
                           ^
Ex.java:8: warning: [unchecked] unchecked cast
        List<String> l = (List<String>) o;                  // (D) 캐스팅은?
                                        ^
  required: List<String>
  found:    Object
1 error
1 warning
```

(B) `o instanceof List<?>` 와 (C) `o instanceof List` 는 **통과했다.**

```text
왜 그렇게 갈리나 — "런타임에 확인할 수 있나"가 기준이다

  못 한다 (런타임에 T 가 없다)              된다
  +-----------------------------------+   +-----------------------------------+
  | new T[n]     배열은 원소 타입을    |   | new List<?>[3]   원소 타입을      |
  |              런타임에 들고 있어야  |   | new List[3]      확인할 것이 없다  |
  |              한다                 |   |                                   |
  | new T()      어느 생성자를 부를지  |   | o instanceof List                 |
  |              모른다               |   | o instanceof List<?>              |
  | T.class      클래스 객체가 없다    |   |   -> "List 인가"만 물으면 된다     |
  | catch (T e)  어느 예외인지 모른다  |   |                                   |
  | instanceof List<String>           |   | (List<String>) o                  |
  |   -> String 인지 확인 불가         |   |   -> 경고만. 검사를 안 한다        |
  +-----------------------------------+   +-----------------------------------+
```

그림 해설 (한 단계씩):

- 기준은 하나다 — **런타임에 그 타입을 확인할 수 있나.**
- `new List<?>[3]` 이 되는 이유는 `?` 가 **어차피 아무것도 주장하지 않기** 때문이다(확인할 것이 없다).
- **캐스팅은 막지 않는다.** `(List<String>) o` 는 경고만 나고 통과한다 — 검사가 **아예 일어나지 않는다.**\
  그래서 캐스팅이 "성공"해도 나중에 꺼낼 때 터진다((3)의 출력이 그것이다).
- 이것이 `@SuppressWarnings("unchecked")` 가 위험한 이유다 — **경고를 끄면 아무도 검사하지 않는다.**

비용 — 없다. 전부 컴파일 타임이다.

### (5) 소거 후 충돌 — 오버로드가 안 된다

**언제 쓰나** — `List<String>` 과 `List<Integer>` 로 오버로드하려 할 때.

**`javac` 출력 그대로** (`Ex.java (19-c3)`, JDK 21.0.5 — 17·25 에서도 동일)

```text
Ex.java:4: error: name clash: print(List<Integer>) and print(List<String>) have the same erasure
    void print(List<Integer> l) {}            // 오버로드인가?
         ^
1 error
```

같은 파일의 **공변 반환**(`A.get(): Object` → `B.get(): String`)은 **통과했다.**

```text
소거하면 같아진다

  소스                                     소거 후
  +-----------------------------+          +-----------------------------+
  | void print(List<String>  l) |    ->    | void print(List l)          |
  | void print(List<Integer> l) |    ->    | void print(List l)          |
  +-----------------------------+          +-----------------------------+
                                             같은 시그니처 두 개 -> 불가능
```

**같은 인터페이스를 다른 타입 인자로 두 번 구현하면** (`Ex.java (19-c4)`)

```text
Ex.java:7: error: repeated interface
    static class Both implements Comparable<String>, Comparable<Integer> {
                                                               ^
Ex.java:7: error: Comparable cannot be inherited with different arguments: <java.lang.String> and <java.lang.Integer>
    static class Both implements Comparable<String>, Comparable<Integer> {
           ^
2 errors
```

그림 해설 (한 단계씩):

- 오버로드는 **시그니처로 구별**되는데, 소거 후 시그니처가 같아지면 **클래스 파일에 둘을 담을 수 없다.**
- 같은 이유로 `Comparable<String>` 과 `Comparable<Integer>` 를 **함께 구현할 수 없다** — 소거하면 둘 다 `Comparable` 이다.
- 피하는 법은 **이름을 다르게** 짓는 것뿐이다(`printStrings`·`printInts`).
- 오버로딩 해소 규칙 자체는 [`../08-method-declaration-overloading/`](../08-method-declaration-overloading/) 가 정본이다.

비용 — 없다. 설계를 바꿔야 하는 것이 대가다.

### (6) 힙 오염 — 조용히 오염되고 나중에 터진다

**언제 쓰나** — `Possible heap pollution` 경고를 봤을 때.

**출력** (`Ex.java (19-e)`, JDK 21.0.5 — 17·25 에서도 동일)

```text
--- 힙 오염: 메서드 안에서는 아무 일도 안 일어난다
  메서드 안: 예외 없이 통과했다. first = 42 (Integer)
--- 오염된 배열이 호출자에게 돌아가면
  저장 성공. arr[0] = [42]
  catch -> class java.lang.Integer cannot be cast to class java.lang.String (java.lang.Integer and java.lang.String are in module java.base of loader 'bootstrap')
```

```java
static <T> void polluteQuietly(List<T>... lists) {
    Object[] objects = lists;              // List<T>[] 를 Object[] 로 본다
    objects[0] = List.of(42);              // aastore 가 막지 못한다 (원소 타입이 List 라서)
    T first = lists[0].get(0);             // T 는 Object 로 소거 -> 캐스트가 없다
    System.out.println(...);               // 예외 없이 통과
}
```

```text
왜 배열의 경비원이 못 막나

  List<String>[] arr 의 런타임 실체는 List[] 다
                                      ^^^^^^ 원소 타입은 "List" 일 뿐

  objects[0] = List.of(42);
     aastore 의 검사 : "넣는 값이 List 인가?"  -> List.of(42) 도 List 다 -> 통과
     확인하고 싶었던 것 : "List<String> 인가?" -> 그 정보가 없다

  배열의 런타임 검사(05번)와 제네릭의 소거(이 주제)가 만나 검사가 무력해진다
```

```text
어디서 터지나 — 캐스트가 있는 곳에서만

  메서드 안                                 호출자 쪽
  +-----------------------------------+    +-----------------------------------+
  | T first = lists[0].get(0);        |    | String s = arr[0].get(0);         |
  | T 는 Object 로 소거됐다            |    | String 으로 받으니                 |
  |   -> checkcast 가 없다             |    |   -> checkcast String 이 있다     |
  |   -> 통과 (first = 42)            |    |   -> ClassCastException           |
  +-----------------------------------+    +-----------------------------------+
     오염된 줄 모른다                          한참 뒤에 발각된다
```

**경고는 어디에 나오나**

```text
Ex.java:6: warning: [unchecked] Possible heap pollution from parameterized vararg type List<T>
    static <T> void polluteQuietly(List<T>... lists) {
                                              ^
Ex.java:31: warning: [unchecked] unchecked generic array creation for varargs parameter of type List<String>[]
        polluteQuietly(List.of("a"), List.of("b"));
                      ^
```

그림 해설 (한 단계씩):

- 경고가 **선언 쪽과 호출 쪽 양쪽**에 난다. 메서드를 만든 사람과 쓰는 사람이 각각 본다.
- `@SafeVarargs` 를 붙이면 **양쪽 경고가 다 사라진다** — 그래서 **"안전하다"고 선언하는 것**이지 안전해지는 게 아니다.
- 안전의 조건은 하나다 — **가변 인자 배열에서 읽기만 하고, 그 배열을 밖으로 내보내지 않는다.**\
  위 코드의 `leak` 은 내보냈기 때문에 사고가 났고, `safeConcat` 은 읽기만 해서 안전하다.

**`@SafeVarargs` 를 아무 데나 붙일 수는 없다** (`Ex.java (19-g)`)

```text
Ex.java:4: error: Invalid SafeVarargs annotation. Instance method <T>instanceMethod(List<T>...) is neither final nor private.
    <T> List<T> instanceMethod(List<T>... l) { return l[0]; }        // (A) 그냥 인스턴스 메서드
                ^
Ex.java:10: error: Invalid SafeVarargs annotation. Method <T>notVarargs(List<T>) is not a varargs method.
    <T> List<T> notVarargs(List<T> l) { return l; }                  // (D) 가변 인자가 아님
                ^
2 errors
```

- **재정의될 수 있는 메서드에는 못 붙인다.** 하위 클래스가 안전하지 않게 재정의하면 선언이 거짓이 되기 때문이다.
- `static`·`final`·`private` 메서드와 생성자에만 붙는다.

> **힙 오염(heap pollution)** — 어떤 타입의 변수가 실제로는 그 타입이 아닌 객체를 가리키게 된 상태(JLS §4.12.2).\
> 예: `List<String>[]` 의 한 칸에 `List<Integer>` 가 들어가 있는 것. 그 자리에서는 예외가 안 나고 나중에 터진다.

비용 — 없다. 조용한 오염이 나중에 비용으로 돌아온다.

### (7) 브리지 메서드 — javac 가 몰래 만드는 메서드

**언제 쓰나** — 제네릭 상위 타입을 구체 타입으로 구현했을 때(사실상 매번).

```java
static class Node<T> { T value; void set(T v) { this.value = v; } T get() { return value; } }
static class StringNode extends Node<String> {
    @Override void set(String v) { this.value = v.toUpperCase(); }
    @Override String get() { return value; }
}
```

**`javap -c -p Ex$StringNode` 출력 그대로** (`Ex.java (19-d)`, JDK 21.0.5)

```text
class Ex$StringNode extends Ex$Node<java.lang.String> {
  void set(java.lang.String);
    Code:
       0: aload_0
       1: aload_1
       2: invokevirtual #7                  // Method java/lang/String.toUpperCase:()Ljava/lang/String;
       5: putfield      #13                 // Field value:Ljava/lang/Object;
       8: return

  java.lang.String get();
    Code:
       0: aload_0
       1: getfield      #13                 // Field value:Ljava/lang/Object;
       4: checkcast     #8                  // class java/lang/String
       7: areturn

  java.lang.Object get();
    Code:
       0: aload_0
       1: invokevirtual #19                 // Method get:()Ljava/lang/String;
       4: areturn

  void set(java.lang.Object);
    Code:
       0: aload_0
       1: aload_1
       2: checkcast     #8                  // class java/lang/String
       5: invokevirtual #22                 // Method set:(Ljava/lang/String;)V
       8: return
}
```

**소스에 둘을 썼는데 넷이 나왔다.** 리플렉션으로도 확인된다.

```text
--- StringNode 가 실제로 가진 메서드
get[] -> Object                          bridge=true  synthetic=true
get[] -> String                          bridge=false synthetic=false
set[class java.lang.String] -> void      bridge=false synthetic=false
set[class java.lang.Object] -> void      bridge=true  synthetic=true
```

```text
왜 필요한가

  Node<T> 의 소거된 시그니처              StringNode 가 쓴 시그니처
  +-----------------------------+        +-----------------------------+
  | void set(Object)            |        | void set(String)            |
  | Object get()                |        | String get()                |
  +-----------------------------+        +-----------------------------+
        JVM 이 보기에 둘은 다른 메서드다 -> 재정의가 아니다!

  그래서 javac 가 다리를 놓는다

  Node<String> n = new StringNode();
  n.set("hello");
       |
       v  invokevirtual Node.set:(Ljava/lang/Object;)V     <- 소거된 시그니처로 호출
       |
       +--> StringNode.set(Object)   [브리지]
              checkcast String
              invokevirtual set(String)                    <- 진짜 구현으로 넘긴다
```

```text
--- 다형성이 실제로 도는 경로
n.get() = HELLO
```

그림 해설 (한 단계씩):

- 소거 때문에 **재정의 관계가 끊어진다** — `set(String)` 은 `set(Object)` 를 재정의한 것이 아니다.
- javac 가 **`set(Object)` 를 자동 생성**해서 `checkcast` 후 진짜 구현으로 넘긴다. 이것이 브리지 메서드다.
- `get()` 은 더 놀랍다 — **반환 타입만 다른 메서드 둘**이 한 클래스에 있다.\
  자바 소스에서는 불가능하지만 **클래스 파일에서는 가능**하다(JVM 의 시그니처에 반환 타입이 포함된다).
- 브리지 메서드는 `ACC_BRIDGE`·`ACC_SYNTHETIC` 플래그가 붙어 있어 `Method.isBridge()` 로 구별된다.

**브리지 메서드를 직접 부르면** 타입 안전이 뚫린다.

```text
--- 브리지 메서드를 직접 부르면 (소거된 시그니처)
찾았다: void Ex$StringNode.set(java.lang.Object) / isBridge=true
invoke -> java.lang.reflect.InvocationTargetException : java.lang.ClassCastException: class java.lang.Integer cannot be cast to class java.lang.String (java.lang.Integer and java.lang.String are in module java.base of loader 'bootstrap')
```

- 브리지 안의 `checkcast` 가 막아 줬다 — **이것이 브리지가 타입 안전을 지키는 방식**이다.
- 그래서 리플렉션으로 메서드를 훑는 프레임워크는 **`isBridge()` 인 것을 걸러야 한다.** 안 그러면 같은 메서드를 두 번 처리한다.\
  **애너테이션도 브리지에 그대로 붙어 나온다** — 걸러야 할 이유가 하나 더 있다.

**출력** (`Ex.java (19-h)`, JDK 21.0.5 — `@Mark` 를 `set(String)` 에만 붙였다)

```text
set[class java.lang.String]    bridge=false 애너테이션=[@Ex.Mark()]
set[class java.lang.Object]    bridge=true  애너테이션=[@Ex.Mark()]
```

비용 — 클래스 파일에 메서드가 늘어난다. 호출은 한 단계 더 거치지만 JIT 가 인라인한다.\
*(그 속도 영향은 이 문서에서 측정하지 않았다.)*

### (8) super type token — 왜 동작하나

**언제 쓰나** — `new TypeReference<List<User>>() {}` 같은 문법을 볼 때.

```java
static abstract class TypeRef<T> {
    final Type type;
    protected TypeRef() {
        Type sup = getClass().getGenericSuperclass();
        if (!(sup instanceof ParameterizedType pt))
            throw new IllegalStateException("타입 인자 없이 만들었다: " + sup);
        this.type = pt.getActualTypeArguments()[0];
    }
}
```

**출력** (`Ex.java (19-f)`, JDK 21.0.5 — 17·25 에서도 동일)

```text
--- super type token 이 읽어 낸 타입
type            = java.util.Map<java.lang.String, java.util.List<java.lang.Integer>>
type.getClass() = ParameterizedType
rawType         = interface java.util.Map
인자들          = [class java.lang.String, java.util.List<java.lang.Integer>]
둘째 인자 안으로 = class java.lang.Integer
--- 이 정보가 어디에 있나
익명 클래스 이름       = Ex$1
getGenericSuperclass() = Ex$TypeRef<java.util.Map<java.lang.String, java.util.List<java.lang.Integer>>>
getSuperclass()        = class Ex$TypeRef
--- 타입 인자를 안 주면
  -> java.lang.IllegalStateException: 타입 인자 없이 만들었다: class Ex$TypeRef
--- 그래도 인스턴스에서는 못 읽는다
plain.getClass().getGenericSuperclass() = java.util.AbstractList<E>
익명으로 만들면                         = java.util.ArrayList<java.lang.String>
```

**그 정보가 정말 클래스 파일에 있나 — `javap` 로 확인했다.**

```text
$ javap -v -p 'Ex$1'
class Ex$1 extends Ex$TypeRef<java.util.Map<java.lang.String, java.util.List<java.lang.Integer>>>
Signature: #12    // LEx$TypeRef<Ljava/util/Map<Ljava/lang/String;Ljava/util/List<Ljava/lang/Integer;>;>;>;

$ javap -v -p 'Ex$Raw'
class Ex$Raw extends Ex$TypeRef
   (Signature 속성이 없다)
```

```text
왜 되나 — 선언은 남는다는 것을 이용한 것이다

  new TypeRef<Map<String,List<Integer>>>() {}
      \_______________________________/  \/
              타입 인자                 익명 하위 클래스를 만든다
                    |
                    v
  javac 가 클래스 Ex$1 을 만들고, 그 "상위 클래스"를 Signature 에 적는다
       Signature: LEx$TypeRef<Ljava/util/Map<...>;>;
                              ^^^^^^^^^^^^^^^^ 여기 남는다
                    |
                    v
  런타임에 getClass().getGenericSuperclass() 로 읽는다
```

그림 해설 (한 단계씩):

- **`{}` 가 핵심이다.** 그것이 없으면 익명 클래스가 안 생기고, 적을 자리도 없다.
- `Raw extends TypeRef`(타입 인자 없음)에는 **`Signature` 속성이 아예 없다.** 그래서 예외를 던진다.
- 즉 super type token 은 **"인스턴스에서는 못 읽는다"는 한계를 "클래스 선언에서는 읽힌다"로 우회**한 것이다.
- `new ArrayList<>() {}` 처럼 **표준 클래스에도 통한다** — 출력의 마지막 줄이 그것이다.\
  익명 하위 클래스를 만들면 `ArrayList<java.lang.String>` 이 `Signature` 에 남는다.
- Jackson 의 `TypeReference`, Guava 의 `TypeToken`, Spring 의 `ParameterizedTypeReference` 가 전부 이 구조다.

비용 — 타입 토큰 하나마다 **클래스가 하나 더 생긴다.** 로딩 비용과 메타스페이스를 쓴다.

## 문법 — 형태와 규칙

직접 쓴 최소 예제다. 묻는 것 하나만 남겼다.

### 소거 규칙 (JLS §4.6)

| 소스 | 소거 후 |
|---|---|
| `List<String>` | `List` |
| `Map<K, V>` | `Map` |
| `T` (바운드 없음) | `Object` |
| `T extends Number` | `Number` |
| `T extends Comparable<T>` | `Comparable` |
| `T extends Resource & Closeable2` | `Resource` (맨 앞) |
| `List<? extends Number>` | `List` |
| `T[]` | `Object[]` |

전부 `javap` 로 확인했다((1)(2)의 출력).

### 런타임에 못 하는 것

```java
new T[n]                      // error: generic array creation
new List<String>[3]           // error: generic array creation
new T()                       // error: unexpected type / required: class
T.class                       // error: cannot select from a type variable
catch (T e)                   // error: unexpected type / required: class
o instanceof List<String>     // error: Object cannot be safely cast to List<String>
void f(List<String>) + void f(List<Integer>)   // error: ... have the same erasure
class A implements Comparable<String>, Comparable<Integer>  // error: repeated interface
```

### 되는 것

```java
new List<?>[3]                // OK — ? 는 확인할 것이 없다
new List[3]                   // OK — 로 타입
o instanceof List             // OK
o instanceof List<?>          // OK
(List<String>) o              // OK (unchecked 경고만 — 검사를 안 한다)
class B extends A { String get(); }   // OK — 공변 반환. 브리지 메서드가 생긴다
```

### 우회 관용구

| 하고 싶은 것 | 관용구 |
|---|---|
| `new T[n]` | `(T[]) new Object[n]` + `@SuppressWarnings` (또는 `Array.newInstance(clazz, n)`) |
| `new T()` | `Supplier<T>` 를 파라미터로 받는다 |
| `T.class` | `Class<T> clazz` 를 파라미터로 받는다 (**타입 토큰**) |
| 타입 인자를 런타임에 알고 싶다 | **super type token** — `new TypeRef<List<User>>() {}` |
| 같은 소거를 갖는 오버로드 | 이름을 다르게 짓는다 |

## 어디서 틀리나

이 주제의 값어치는 전부 여기 있다.

### 1. `(T[]) new Object[n]` 을 밖으로 내보낸다

**출력** (`Ex.java (19-e)`, JDK 21.0.5)

```text
--- pickTwo: 컴파일은 되는데 대입에서 터진다
  catch -> class [Ljava.lang.Object; cannot be cast to class [Ljava.lang.String; ([Ljava.lang.Object; and [Ljava.lang.String; are in module java.base of loader 'bootstrap')
  Object[] 로 받으면 = [a, b] / 런타임 타입 = [Ljava.lang.Object;
```

```java
static <T> T[] pickTwo(T a, T b, T c) { return (T[]) new Object[]{a, b}; }
String[] picked = pickTwo("a", "b", "c");     // 여기서 터진다
```

- **메서드 안에서는 안 터진다.** `T[]` 가 `Object[]` 로 소거돼 캐스트가 없기 때문이다.
- **호출자가 `String[]` 으로 받는 순간** `checkcast [Ljava/lang/String;` 이 돌고 터진다.
- `Object[]` 로 받으면 통과한다 — **받는 타입에 따라 갈린다**는 것이 함정이다.
- `ArrayList.toArray()` 가 `Object[]` 를 돌려주는 이유가 이것이다([`../05-arrays/`](../05-arrays/)).

### 2. 가변 인자 배열을 밖으로 내보낸다

```text
  저장 성공. arr[0] = [42]
  catch -> class java.lang.Integer cannot be cast to class java.lang.String ...
```

- `static <T> List<T>[] leak(List<T>... lists) { return lists; }` 가 그 형태다.
- 경고는 나오지만 **컴파일은 된다.** 사고는 호출자 쪽에서, 한참 뒤에 난다.
- `@SafeVarargs` 는 **경고만 끈다.** 내보내는 코드에 붙이면 거짓 선언이 된다.

### 3. `@SuppressWarnings("unchecked")` 로 캐스팅 경고를 끈다

```text
warning: [unchecked] unchecked cast
  required: List<String>
  found:    Object
```

- 이 경고는 **"런타임 검사가 일어나지 않는다"**는 통보다. 끄면 **아무도 검사하지 않는다.**
- 캐스팅 자체는 성공하고, **나중에 원소를 꺼낼 때** `ClassCastException` 이 난다.
- 범위를 최소로 좁혀 붙이고, **왜 안전한지 주석으로 남긴다.**

### 4. 리플렉션으로 메서드를 훑을 때 브리지를 안 거른다

```text
get[] -> Object                          bridge=true  synthetic=true
get[] -> String                          bridge=false synthetic=false
```

- `getDeclaredMethods()` 가 **같은 이름의 메서드를 둘** 준다.
- 애너테이션을 훑는 프레임워크가 이것을 못 거르면 **같은 메서드를 두 번 처리**한다.
- 브리지에는 애너테이션이 복사되지 않는 경우가 있어, **`isBridge()` 인 것을 건너뛰는 것**이 관용구다.

### 5. 인스턴스에서 타입 인자를 읽으려 한다

```text
strings.getClass() = class java.util.ArrayList
ints.getClass()    = class java.util.ArrayList
같은 클래스인가     = true
```

- `list.getClass()` 로는 **절대** 원소 타입을 못 안다.
- 알고 싶으면 **선언**(필드·메서드 파라미터)에서 읽거나 **super type token** 을 써야 한다.
- "리스트가 비어 있지 않으면 첫 원소의 클래스를 본다"는 우회는 **빈 리스트에서 무너진다.**

### 6. 소거가 같은 메서드를 오버로드하려 한다

```text
error: name clash: print(List<Integer>) and print(List<String>) have the same erasure
```

- 컴파일 에러라 **금방 발견된다** — 그나마 나은 경우다.
- 고칠 방법은 **이름을 바꾸는 것**뿐이다. 파라미터를 추가해도 소용없다(소거 후 여전히 같다면).

## 구현 세부사항 대 언어 보장

이 절은 **"어디까지 믿어도 되나"**를 가른다.

| 항목 | 누가 보장하나 | 근거 |
|---|---|---|
| 소거 규칙(타입 인자 제거, 타입 변수 → 바운드) | **JLS (언어 보장)** | JLS §4.6 |
| `Signature` 속성이 제네릭 정보를 담는 것 | **JVMS (플랫폼 보장)** | JVMS §4.7.9 |
| descriptor 에 제네릭이 없는 것 | **JVMS (플랫폼 보장)** | JVMS §4.3 |
| 브리지 메서드가 생기는 것 | **JLS (언어 보장)** | JLS §8.4.8.3 |
| `new T[]`·`instanceof List<String>` 금지 | **JLS (언어 보장)** | JLS §15.10.1, §15.20.2 |
| 소거 후 충돌이 컴파일 에러인 것 | **JLS (언어 보장)** | JLS §8.4.8.3 |
| `getGenericType()` 이 선언의 타입 인자를 주는 것 | **javadoc (API 계약)** | `java.lang.reflect` javadoc |
| `Method.isBridge()` 로 브리지를 구별하는 것 | **javadoc (API 계약)** | `Method.isBridge` javadoc |
| `checkcast` 가 **어느 명령 자리에** 끼워지는지 | **구현 세부** | javac 가 고른 위치. "캐스트가 들어간다"는 성질이 JLS 보장 |
| 브리지 메서드가 `javap` 출력에 나오는 **순서** | **구현 세부** | 관찰값(21.0.5) |
| `javac` 에러·경고 문구 | **구현 세부** | 관찰값(17·21·25 동일) |
| `ClassCastException` 메시지의 `... are in module java.base of loader 'bootstrap'` 꼬리 | **구현 세부** | 관찰값(17·21·25 동일) |

### 소거는 "런타임에 아무 정보도 없다"가 아니다

이 주제에서 가장 자주 틀리는 문장이다.

```text
  틀린 요약                              실제
  +-----------------------------+       +-----------------------------------+
  | 제네릭은 런타임에            |       | 실행 경로(descriptor)에서만 사라진다|
  |   완전히 사라진다            |       | Signature 속성에는 남아 있고       |
  |                             |       | 리플렉션으로 읽을 수 있다          |
  +-----------------------------+       +-----------------------------------+
```

- 사라지는 것은 **인스턴스의 타입 인자**다. **선언의 타입 인자**는 남는다.
- 이 구분이 없으면 "그럼 Jackson 은 어떻게 `List<User>` 를 아나"에 답할 수 없다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 대응 |
|---|---|
| `T` 의 인스턴스나 배열이 필요하다 | `Class<T>` 나 `Supplier<T>` 를 **파라미터로 받는다** |
| 런타임에 타입 인자를 알아야 한다 | **super type token** (`new TypeRef<...>() {}`) |
| 제네릭 배열이 필요하다 | `List<T>` 를 쓴다. 꼭 배열이면 `(T[]) new Object[n]` 을 **내부에만** 둔다 |
| 가변 인자 제네릭을 만든다 | 배열에서 **읽기만** 하고 `@SafeVarargs` 를 붙인다. **내보내지 않는다** |
| 소거가 같은 오버로드가 필요하다 | 이름을 다르게 짓는다 |
| 리플렉션으로 메서드를 훑는다 | `isBridge()`·`isSynthetic()` 을 거른다 |

판단 규칙 두 줄.

- **런타임에 타입이 필요하면 타입을 값으로 넘겨라** — `Class<T>`·`TypeRef<T>`·`Supplier<T>`.
- **제네릭과 배열을 섞지 마라.** 배열의 런타임 검사와 제네릭의 소거는 서로를 무력화한다.

## 핵심 문장

- 소거는 **타입 인자를 지우고 타입 변수를 바운드(없으면 `Object`)로 바꾼다.** `javap -c` 의 `Ljava/util/List;` 와 `add:(Ljava/lang/Object;)Z` 가 그 증거다.
- **javac 가 `checkcast` 를 끼워 넣는다.** 소스에 없는 캐스트가 바이트코드에 있고, 사고는 항상 그 자리에서 터진다.
- **지운 것을 `Signature` 속성에 따로 적어 둔다.** descriptor 는 `Ljava/util/List;` 인데 `Signature` 는 `Ljava/util/List<Ljava/lang/String;>;` 다.
- 그래서 리플렉션이 비대칭이다 — **선언의 제네릭은 읽히고, 인스턴스의 타입 인자는 못 읽는다.**
- **런타임에 확인할 수 없는 것이 전부 금지**다 — `new T[]`·`new T()`·`T.class`·`catch (T)`·`instanceof List<String>`·소거가 같은 오버로드.
- **힙 오염은 조용하다.** 오염되는 자리에는 캐스트가 없고, 터지는 자리는 한참 뒤의 호출자다.
- **브리지 메서드**는 소거로 끊긴 재정의 관계를 잇는 javac 생성 메서드다. `javap` 로 보면 반환 타입만 다른 메서드 둘이 나온다.
- **super type token 이 동작하는 이유는 `Signature` 가 남기 때문**이다. `{}` 로 익명 하위 클래스를 만들어 선언 자리에 타입 인자를 박아 넣는다.

## 관련 자료

- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 19번)
- [`../17-generic-declarations/`](../17-generic-declarations/) — **그쪽은 `<T>` 를 선언하고 바운드를 거는 자리까지, 여기는 그것이 컴파일 후 무엇으로 남는가부터.**\
  `Counter<String>.class == Counter<Integer>.class` 의 관찰은 그쪽에, 그 이유는 여기에 있다
- [`../18-wildcards-pecs/`](../18-wildcards-pecs/) — **그쪽은 `?` 가 읽기·쓰기를 막는 규칙까지, 여기는 제네릭이 왜 런타임 검사를 못 하는가부터.**\
  제네릭이 불공변으로 설계된 이유가 여기 있다
- [`../05-arrays/`](../05-arrays/) — **그쪽은 배열이 런타임 원소 타입을 들고 `aastore` 로 검사하는 것까지, 여기는 그 검사가 제네릭 앞에서 무력해지는 자리부터.**\
  `new List<String>[3]` 금지가 두 주제가 만나는 지점이다
- [`../16-annotations/`](../16-annotations/) — **구조가 같다** — "클래스 파일에 무엇이 남나"를 `javap -v` 로 확인하는 주제. 그쪽은 `Runtime*Annotations` 속성, 여기는 `Signature` 속성
- [`../09-inheritance-overriding/`](../09-inheritance-overriding/) — 브리지 메서드가 **재정의 관계를 잇기 위해** 생긴다. 동적 디스패치의 규칙은 그쪽이 정본
- [`../08-method-declaration-overloading/`](../08-method-declaration-overloading/) — 소거 후 충돌이 왜 오버로드로 성립하지 않는가. 오버로딩 해소 규칙은 그쪽
- [**58번 주제**](../58-reflection/)(리플렉션) — **`getGenericType()` 으로 읽은 다음 무엇을 하나가 그쪽이다.** 여기는 **읽히느냐 마느냐**까지
- [`../../../../../../history/java/java-5.md`](../../../../../../history/java/java-5.md) — 제네릭과 소거가 **언제·왜 이 방식으로 들어왔나**가 정본(하위 호환을 위한 선택). 여기는 **그래서 무엇을 못 하나**

## 용어 풀이

- **타입 소거(type erasure)** — 컴파일 후 타입 인자를 지우고 타입 변수를 바운드로 바꾸는 것(JLS §4.6).
- **descriptor** — JVM 이 필드·메서드의 타입을 적는 형식. 제네릭이 없다. `Ljava/util/List;` 처럼 쓴다.
- **`Signature` 속성** — 제네릭 정보를 따로 담는 클래스 파일 속성(JVMS §4.7.9). 실행에는 쓰이지 않는다.
- **`checkcast`** — 참조가 특정 타입인지 검사하고 아니면 `ClassCastException` 을 던지는 JVM 명령. javac 가 제네릭 자리에 끼워 넣는다.
- **로 타입(raw type)** — 타입 인자를 아예 안 쓴 제네릭 타입(`List`). 호환성을 위해 남아 있고 경고가 난다.
- **힙 오염(heap pollution)** — 어떤 타입의 변수가 실제로는 그 타입이 아닌 객체를 가리키게 된 상태(JLS §4.12.2).
- **`@SafeVarargs`** — 제네릭 가변 인자의 힙 오염 경고를 끄는 애너테이션(Java 7). `static`·`final`·`private` 메서드와 생성자에만 붙는다.
- **브리지 메서드(bridge method)** — 소거로 끊어진 재정의 관계를 잇기 위해 javac 가 만드는 메서드. `ACC_BRIDGE` 플래그가 붙는다.
- **합성 멤버(synthetic member)** — 소스에 없는데 컴파일러가 만든 멤버. `ACC_SYNTHETIC` 플래그가 붙는다.
- **타입 토큰(type token)** — 타입 정보를 값으로 넘기기 위한 `Class<T>` 파라미터. `T.class` 를 못 쓰는 것의 우회다.
- **super type token** — 익명 하위 클래스의 `Signature` 에 타입 인자를 박아 넣어 런타임에 읽어 내는 관용구. `new TypeRef<List<User>>() {}`.
- **`ParameterizedType`** — `List<String>` 처럼 타입 인자가 붙은 타입을 나타내는 리플렉션 인터페이스. `getActualTypeArguments()` 로 인자를 꺼낸다.

## 더 들어가면

- **`T[]` 의 소거는 `Object[]` 다.** 그런데 가변 인자 배열의 **런타임 타입은 호출부에서 정해진다.**

```text
  whatIsIt("a","b"):  런타임 타입 = [Ljava.lang.Object;      // void f(Object... xs)
  whatIsItGeneric("a","b"):  런타임 타입 = [Ljava.lang.String;  // <T> void f(T... xs)
  whatIsItGeneric(1,2):  런타임 타입 = [Ljava.lang.Integer;
```

  `<T> void f(T... xs)` 에서 `xs.getClass()` 가 `Object[]` 가 **아니다.** javac 가 호출부에서 추론한 타입으로 배열을 만든다.\
  그래서 `pickTwo` 처럼 **메서드 안에서 만든 `Object[]`** 와 **호출부가 만든 `String[]`** 이 섞이면 사고가 난다.

- **`instanceof List<?>` 는 되는데 `instanceof List<String>` 은 안 되는 이유**가 정확히 "확인 가능한가"다.\
  `?` 는 아무것도 주장하지 않으므로 `List` 인지만 보면 되고, `<String>` 은 확인할 정보가 없다.\
  JLS 는 이것을 **reifiable type**(구체화 가능 타입)이라는 개념으로 정의한다 — `instanceof` 와 배열 생성은 구체화 가능 타입만 허용한다.

- **지역 변수의 제네릭 타입은 `Signature` 가 아니라 `LocalVariableTypeTable` 에 들어간다.** 그것도 `javac -g` 가 있어야 생긴다(`Ex.java (19-h)`).

```text
$ javac -g   ->
      LocalVariableTypeTable:
        Start  Length  Slot  Name   Signature
            8      10     1 local   Ljava/util/List<Ljava/lang/String;>;

$ javac (기본)  ->  LocalVariableTypeTable 이 0개
```

  그리고 이것을 읽는 **표준 리플렉션 API 는 없다.**\
  "지역 변수만 리플렉션에서 빠진다"는 구조는 [`../16-annotations/`](../16-annotations/) 에서 본 것과 같다 — 거기서도 지역 변수 선언 애너테이션만 저장 자리가 없었다.

- **소거를 택한 이유는 하위 호환이었다.** Java 5 가 제네릭을 넣을 때, 기존 `List` 를 쓰던 코드와 새 `List<String>` 코드가 **같은 JVM·같은 라이브러리에서 함께 돌아야** 했다.\
  타입 인자를 런타임에 남기는 방식(reification)이면 `java.util.List` 를 갈아엎어야 했다.\
  그 선택의 연혁은 [`../../../../../../history/java/java-5.md`](../../../../../../history/java/java-5.md) 가 정본이다.
