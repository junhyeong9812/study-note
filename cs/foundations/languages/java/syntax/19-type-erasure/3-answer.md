# java/syntax/19 — 타입 소거: 런타임에 없는 것·제네릭 배열·브리지 메서드 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러·바이트코드는 **Temurin JDK 21.0.5 에서 실제로 돌려 얻은 것**이다.\
> 실행 프로그램(`19-b`·`19-d`·`19-e`·`19-f`)은 **17.0.13 · 25.0.1** 에서도 돌렸고 출력이 한 글자도 다르지 않았다.\
> 컴파일 에러(`19-c1`·`19-c3`)도 17 과 25 에서 `diff` 로 대조해 **문자 단위로 같았다.**\
> 바이트코드는 `javap -c -p` · `javap -v -p` 출력을 그대로 옮겼다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 이 코드의 바이트코드에는 무엇이 있는가

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

**왜 그런가**

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

- **`names` 필드의 타입** — `Ljava/util/List;` 다. `<String>` 이 없다.
- **`add` 와 `get`** — `add:(Ljava/lang/Object;)Z` 와 `get:(I)Ljava/lang/Object;` 다.\
  `List` 의 `E` 가 **`Object` 로 소거**됐다.
- **소스에 없던 명령** — **`checkcast class java/lang/String`** 이다.\
  `get` 직후, 결과를 지역 변수에 넣기(`astore_1`) 직전에 들어간다.
- 그래서 제네릭은 "**컴파일러가 캐스팅을 대신 써 주는 것**"이라고 요약된다.

**`<T extends Comparable<T>> T max(List<T>)` 의 반환**

```text
  static <T extends java.lang.Comparable<T>> T max(java.util.List<T>);
    Code:
       0: aload_0
       1: iconst_0
       2: invokeinterface #23,  2           // InterfaceMethod java/util/List.get:(I)Ljava/lang/Object;
       7: checkcast     #29                 // class java/lang/Comparable
      10: areturn
```

- **`Comparable` 로 소거**된다. 타입 변수는 **바운드로** 소거되기 때문이다(바운드가 없으면 `Object`).
- 다중 바운드라면 **맨 앞의 것**으로 소거된다.

### 2. 그럼 지워지기만 하는가

**`javap -v -p Ex.class` 출력 그대로** (`Ex.java (19-a)`, 관련 줄만)

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

**왜 그런가**

**나오는 두 줄은 `descriptor` 와 `Signature`** 다.

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

- **`names`** — descriptor 는 `Ljava/util/List;`, `Signature` 는 `Ljava/util/List<Ljava/lang/String;>;`.
- **`Box<T extends Number>` 의 `T value`** — descriptor 가 **`Ljava/lang/Number;`** 다.\
  바운드로 소거됐다. `Signature` 에는 `TT;`(= 타입 변수 T)가 남는다.
- 표기 읽는 법 — `TT;` 는 "타입 변수 T", `<T:Ljava/lang/Number;>` 는 "T 의 클래스 바운드가 Number",\
  `<T::Ljava/lang/Comparable<TT;>;>` 의 `::` 는 **클래스 바운드가 없고 인터페이스 바운드만 있다**는 뜻이다.

**`Signature` 를 JVM 이 실행에 쓰는가** — **안 쓴다.**

- JVM 은 메서드를 찾고 스택을 검증할 때 **descriptor** 만 본다.
- `Signature` 는 javac 가 **다른 클래스를 컴파일할 때**, IDE 가 자동완성할 때, 리플렉션의 `getGeneric*` 이 읽는다.
- 그래서 **"제네릭은 런타임에 완전히 사라진다"는 말은 정확하지 않다.** 사라지는 것은 **실행 경로**에서다.

### 3. 리플렉션의 비대칭

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

**왜 그런가**

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

| 물어본 것 | 답 |
|---|---|
| `getType()` | `interface java.util.List` (소거된 것) |
| `getGenericType()` | `java.util.List<java.lang.String>` (`Signature` 에서 읽은 것) |
| `count` 의 `getParameterTypes()` | `[interface java.util.List, interface java.util.Set]` |
| `count` 의 `getGenericParameterTypes()` | `[java.util.List<java.lang.String>, java.util.Set<? extends java.lang.Number>]` — **와일드카드까지** 남는다 |
| `strings.getClass() == ints.getClass()` | **`true`** |
| `getTypeParameters()` | `[E]` — **이름과 바운드뿐**. `String` 은 알 수 없다 |

- 그래서 **DI·ORM·JSON 라이브러리는 "필드를 보고" 동작한다.** 객체를 보고는 못 한다.
- `getTypeParameters()` 가 `[E]` 를 주는 것도 **`ArrayList` 의 선언에서 읽은 것**이다 — 인스턴스에서 읽은 게 아니다.

### 4. 소거된 리스트에 다른 타입을 넣으면

**출력** (`Ex.java (19-b)`, JDK 21.0.5)

```text
--- 그래서 소거된 리스트에 아무거나 넣을 수 있다
strings = [a, 42]
catch -> java.lang.ClassCastException: class java.lang.Integer cannot be cast to class java.lang.String (java.lang.Integer and java.lang.String are in module java.base of loader 'bootstrap')
```

컴파일 시 경고는 이렇게 난다.

```text
warning: [unchecked] unchecked call to add(E) as a member of the raw type List
        raw.add(42);
               ^
```

**왜 그런가**

- **`raw.add(42)` 는 안 터진다.** `ArrayList` 안에는 원소 타입 검사가 없다 — 있을 수가 없다(소거돼서 무엇인지 모른다).
- `println(strings)` 는 **`[a, 42]`** 를 찍는다. `List<String>` 이라고 선언된 변수에 `Integer` 가 들어 있다.
- 마지막 줄에서 `ClassCastException` 이 난다.

```text
왜 꺼내는 자리에서 터지나

  raw.add(42)                            String bad = strings.get(1)
  +-----------------------------+        +-----------------------------+
  | raw 는 로 타입 List         |        | strings 는 List<String>     |
  | add(Object) 로 컴파일된다   |        | get 의 결과를 String 으로    |
  |   -> checkcast 가 없다      |        |   받으므로 javac 가          |
  |   -> 통과                   |        |   checkcast String 을 넣었다 |
  +-----------------------------+        +-----------------------------+
      조용히 오염된다                        여기서 발각된다
```

- 검사는 **javac 가 캐스트를 끼워 넣은 자리에서만** 일어난다.
- 그래서 **오염은 조용히, 발각은 나중에**다. 8번의 힙 오염과 정확히 같은 구조다.

### 5. 런타임에 못 하는 것들

**출력** (`Ex.java (19-c1)` `javac`, JDK 21.0.5 — 17·25 에서도 동일)

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

**(F) `new List<?>[3]` 와 (G) `new List[3]` 은 에러가 없다.**

**왜 그런가**

```text
기준은 하나다 — 런타임에 그 타입을 확인할 수 있나

  못 한다                                 된다
  +-----------------------------------+   +-----------------------------------+
  | new T[n]     배열은 원소 타입을    |   | new List<?>[3]   ? 는 아무것도    |
  |              런타임에 들고 있어야  |   |                  주장하지 않는다   |
  |              한다                 |   | new List[3]      로 타입          |
  | new T()      어느 생성자를 부를지  |   |                                   |
  |              모른다               |   |                                   |
  | T.class      클래스 객체가 없다    |   |                                   |
  | catch (T e)  어느 예외인지 모른다  |   |                                   |
  | new List<String>[3]               |   |                                   |
  +-----------------------------------+   +-----------------------------------+
```

- JLS 는 이것을 **reifiable type**(구체화 가능 타입)이라는 개념으로 정리한다 — 배열 생성과 `instanceof` 는 구체화 가능 타입만 허용한다.
- `List<?>` 와 `List`(로 타입)는 **구체화 가능**하다. `List<String>` 은 아니다.

**우회 관용구**

| 하고 싶은 것 | 관용구 |
|---|---|
| `new T[n]` | `(T[]) new Object[n]` + `@SuppressWarnings` (**밖으로 내보내지 않는다** — 12번) |
| | 또는 `Array.newInstance(clazz, n)` + `Class<T>` 파라미터 |
| `new T()` | `Supplier<T>` 를 파라미터로 받는다 |
| `T.class` | `Class<T> clazz` 를 파라미터로 받는다 (**타입 토큰**) |
| `catch (T e)` | `Class<T>` 를 받아 `catch (Exception e)` 안에서 `isInstance` 로 분기 |
| `new List<String>[3]` | `List<List<String>>` 을 쓴다 |

### 6. `instanceof` 와 캐스팅

**출력** (`Ex.java (19-c2)` `javac`, JDK 21.0.5)

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

**왜 그런가**

| 자리 | 결과 |
|---|---|
| (A) `o instanceof List<String>` | **에러** — `Object cannot be safely cast to List<String>` |
| (B) `o instanceof List<?>` | **OK** |
| (C) `o instanceof List` | **OK** |
| (D) `(List<String>) o` | **컴파일된다** — `unchecked cast` 경고만 |

- (A)가 막히는 이유는 **런타임에 `String` 인지 확인할 방법이 없기** 때문이다.
- (B)(C)는 "`List` 인가"만 물으므로 확인할 수 있다.

**(D)가 "성공"했다는 것의 뜻**

```text
캐스팅은 막지 않는다 — 검사를 아예 안 한다

  (List<String>) o
        |
        +-- javac : "확인할 수 없다" -> unchecked 경고만 내고 통과
        |
        +-- 바이트코드 : checkcast java/util/List  (String 은 확인하지 않는다)
        |
        +-- 런타임 : o 가 List 이기만 하면 통과한다
                     안에 Integer 가 들어 있어도 모른다
```

- 문제는 **원소를 꺼낼 때** 드러난다 — 4번의 `ClassCastException` 이 정확히 그것이다.
- 그래서 `@SuppressWarnings("unchecked")` 가 위험하다. 경고는 **"아무도 검사하지 않는다"는 통보**다.

### 7. 소거 후 충돌

**출력** (`Ex.java (19-c3)` `javac`, JDK 21.0.5 — 17·25 에서도 동일)

```text
Ex.java:4: error: name clash: print(List<Integer>) and print(List<String>) have the same erasure
    void print(List<Integer> l) {}            // 오버로드인가?
         ^
1 error
```

**(B) 공변 반환은 같은 파일에서 통과했다.**

**(C)** (`Ex.java (19-c4)`)

```text
Ex.java:7: error: repeated interface
    static class Both implements Comparable<String>, Comparable<Integer> {
                                                               ^
Ex.java:7: error: Comparable cannot be inherited with different arguments: <java.lang.String> and <java.lang.Integer>
    static class Both implements Comparable<String>, Comparable<Integer> {
           ^
2 errors
```

**왜 그런가**

```text
소거하면 같아진다

  소스                                     소거 후
  +-----------------------------+          +-----------------------------+
  | void print(List<String>  l) |    ->    | void print(List l)          |
  | void print(List<Integer> l) |    ->    | void print(List l)          |
  +-----------------------------+          +-----------------------------+
                                             같은 시그니처 두 개 -> 불가능
```

- 오버로드는 **시그니처로 구별**되는데, 소거 후 같아지면 클래스 파일에 둘을 담을 수 없다.
- (C)도 같은 이유다 — 소거하면 `Comparable` 둘이라 **같은 인터페이스를 두 번 구현**하는 꼴이 된다.

**(B)가 되는 이유** — **공변 반환은 소거 후에도 충돌하지 않는다.**

- `A.get()` 은 `()Ljava/lang/Object;`, `B.get()` 은 `()Ljava/lang/String;` 이다.
- 시그니처가 다르지만, JVM 의 시그니처에는 **반환 타입이 포함**되므로 한 클래스에 둘 다 놓을 수 있다.
- 그래서 javac 가 **브리지 메서드**를 만들어 잇는다(10번).

**(A)를 피하는 법** — **이름을 다르게 짓는 것**뿐이다(`printStrings`·`printInts`).\
파라미터를 더해도 소거 후 여전히 같다면 소용없다.

### 8. 힙 오염은 어디서 터지는가

**출력** (`Ex.java (19-e)`, JDK 21.0.5 — 17·25 에서도 동일)

```text
--- 힙 오염: 메서드 안에서는 아무 일도 안 일어난다
  메서드 안: 예외 없이 통과했다. first = 42 (Integer)
--- 오염된 배열이 호출자에게 돌아가면
  저장 성공. arr[0] = [42]
  catch -> class java.lang.Integer cannot be cast to class java.lang.String (java.lang.Integer and java.lang.String are in module java.base of loader 'bootstrap')
```

**왜 그런가**

- **(A)는 예외를 던지지 않는다.** `메서드 안: 예외 없이 통과했다. first = 42 (Integer)` 가 찍힌다.\
  `T first = lists[0].get(0)` 에서 `T` 가 `Object` 로 소거돼 **`checkcast` 가 없기** 때문이다.

```text
왜 배열의 경비원이 못 막나

  List<String>[] 의 런타임 실체는 List[] 다
                                  ^^^^^^ 원소 타입은 "List" 일 뿐

  objects[0] = List.of(42);
     aastore 의 검사 : "넣는 값이 List 인가?"  -> List.of(42) 도 List 다 -> 통과
     확인하고 싶었던 것 : "List<String> 인가?" -> 그 정보가 없다

  배열의 런타임 검사(05번)와 제네릭의 소거(이 주제)가 만나 검사가 무력해진다
```

- **(B)의 마지막 줄**에서 `ClassCastException` 이 난다.\
  `String s = arr[0].get(0)` 에는 javac 가 `checkcast String` 을 넣었기 때문이다.

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

**경고가 나오는 자리** — **선언 쪽과 호출 쪽 양쪽**이다.

```text
Ex.java:6: warning: [unchecked] Possible heap pollution from parameterized vararg type List<T>
    static <T> void polluteQuietly(List<T>... lists) {
                                              ^
Ex.java:15: warning: [unchecked] Possible heap pollution from parameterized vararg type List<T>
    static <T> List<T>[] leak(List<T>... lists) { return lists; }
                                         ^
Ex.java:31: warning: [unchecked] unchecked generic array creation for varargs parameter of type List<String>[]
        polluteQuietly(List.of("a"), List.of("b"));
                      ^
Ex.java:34: warning: [unchecked] unchecked generic array creation for varargs parameter of type List<String>[]
        List<String>[] arr = leak(List.of("a"), List.of("b"));
                                 ^
```

- 선언 쪽은 `Possible heap pollution from parameterized vararg type`,\
  호출 쪽은 `unchecked generic array creation for varargs parameter` 다.
- `@SafeVarargs` 를 붙이면 **양쪽 경고가 다 사라진다.**

### 9. `@SafeVarargs`

**출력** (`Ex.java (19-g)` `javac`, JDK 21.0.5)

```text
Ex.java:4: error: Invalid SafeVarargs annotation. Instance method <T>instanceMethod(List<T>...) is neither final nor private.
    <T> List<T> instanceMethod(List<T>... l) { return l[0]; }        // (A) 그냥 인스턴스 메서드
                ^
  where T is a type-variable:
    T extends Object declared in method <T>instanceMethod(List<T>...)
Ex.java:10: error: Invalid SafeVarargs annotation. Method <T>notVarargs(List<T>) is not a varargs method.
    <T> List<T> notVarargs(List<T> l) { return l; }                  // (D) 가변 인자가 아님
                ^
  where T is a type-variable:
    T extends Object declared in method <T>notVarargs(List<T>)
2 errors
```

**(B) `final` 과 (C) `static` 은 통과했다.**

**왜 그런가**

- **(A) 에러** — 재정의될 수 있는 메서드에는 못 붙인다.\
  하위 클래스가 **안전하지 않게 재정의하면 선언이 거짓**이 되기 때문이다.
- **(D) 에러** — 가변 인자 메서드가 아니면 붙일 이유가 없다.
- 붙일 수 있는 자리는 **`static`·`final`·`private` 메서드와 생성자**다.

**`@SafeVarargs` 가 실제로 하는 일** — **경고를 끄는 것뿐**이다. 안전하게 만들어 주지 않는다.

```text
안전의 조건은 코드가 지켜야 한다

  안전하다                                위험하다
  +-----------------------------------+  +-----------------------------------+
  | static <T> List<T> safeConcat(    |  | static <T> List<T>[] leak(        |
  |         List<T>... lists) {       |  |         List<T>... lists) {       |
  |   for (List<T> l : lists)         |  |   return lists;                   |
  |     out.addAll(l);                |  |   ^^^^^^^^^^^^ 배열을 내보낸다     |
  |   return out;   <- 배열은 안 나간다|  | }                                 |
  | }                                 |  |                                   |
  +-----------------------------------+  +-----------------------------------+
     배열에서 읽기만 한다                    호출자가 오염시킬 수 있다
```

**출력** (`Ex.java (19-e)`)

```text
--- @SafeVarargs 를 붙인 쪽은 경고가 없다
  safeConcat = [a, b, c]
```

- 조건 두 줄 — **가변 인자 배열에 쓰지 않는다** · **그 배열을 밖으로 내보내지 않는다.**

### 10. 브리지 메서드

**출력** (`Ex.java (19-d)`, JDK 21.0.5 — 17·25 에서도 동일)

```text
--- StringNode 가 실제로 가진 메서드
get[] -> Object                          bridge=true  synthetic=true
get[] -> String                          bridge=false synthetic=false
set[class java.lang.String] -> void      bridge=false synthetic=false
set[class java.lang.Object] -> void      bridge=true  synthetic=true
```

**소스에 둘을 썼는데 넷이 나온다.**

**`javap -c -p Ex$StringNode` 출력 그대로**

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

**왜 그런가**

```text
소거 때문에 재정의 관계가 끊어진다

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

- **소스에 없는 메서드 둘** — `set(Object)` 와 `get()` 이 반환 `Object` 인 것.\
  각각 **`checkcast` 후 진짜 구현으로 넘기는** 일만 한다.
- 다형성이 실제로 도는 것을 확인했다.

```text
--- 다형성이 실제로 도는 경로
n.get() = HELLO
```

**반환 타입만 다른 메서드 둘이 한 클래스에 있을 수 있는가** — **자바 소스에서는 불가능하고, 클래스 파일에서는 가능하다.**

- JVM 의 메서드 시그니처에는 **반환 타입이 포함**되기 때문이다.
- `javap` 출력에 `java.lang.String get();` 과 `java.lang.Object get();` 이 나란히 있는 것이 그 증거다.

**브리지에 `Integer` 를 넘기면**

```text
--- 브리지 메서드를 직접 부르면 (소거된 시그니처)
찾았다: void Ex$StringNode.set(java.lang.Object) / isBridge=true
invoke -> java.lang.reflect.InvocationTargetException : java.lang.ClassCastException: class java.lang.Integer cannot be cast to class java.lang.String (java.lang.Integer and java.lang.String are in module java.base of loader 'bootstrap')
```

- 브리지 안의 `checkcast` 가 막아 줬다 — **이것이 브리지가 타입 안전을 지키는 방식**이다.

**프레임워크가 조심할 것** — **`isBridge()` 인 메서드를 걸러야 한다.**

- `getDeclaredMethods()` 가 같은 이름의 메서드를 둘 준다.
- 그리고 **애너테이션도 브리지에 그대로 붙어 나온다**(`Ex.java (19-h)`).

```text
set[class java.lang.String]    bridge=false 애너테이션=[@Ex.Mark()]
set[class java.lang.Object]    bridge=true  애너테이션=[@Ex.Mark()]
```

- 안 거르면 **같은 메서드를 두 번 처리**한다(핸들러 두 번 등록, 트랜잭션 두 번 감싸기 등).

### 11. `TypeToken` / super type token 은 왜 동작하는가

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

**왜 그런가**

- **`ref.type` 은 `java.util.Map<java.lang.String, java.util.List<java.lang.Integer>>`** 다.\
  중첩된 타입 인자까지 읽힌다 — 출력의 `둘째 인자 안으로 = class java.lang.Integer` 가 그 확인이다.

**그 정보가 어디에 있나 — `javap` 로 확인했다.**

```text
$ javap -v -p 'Ex$1'
class Ex$1 extends Ex$TypeRef<java.util.Map<java.lang.String, java.util.List<java.lang.Integer>>>
Signature: #12    // LEx$TypeRef<Ljava/util/Map<Ljava/lang/String;Ljava/util/List<Ljava/lang/Integer;>;>;>;

$ javap -v -p 'Ex$Raw'
class Ex$Raw extends Ex$TypeRef
   (Signature 속성이 없다)
```

```text
왜 되나 — "선언은 남는다"를 이용한 것이다

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

**`new Raw()` 는** — `IllegalStateException` 을 던진다.\
`Raw extends TypeRef`(타입 인자 없음)에는 **`Signature` 속성이 아예 없어서** `getGenericSuperclass()` 가 `ParameterizedType` 이 아닌 그냥 `Class` 를 준다.

**`{}` 를 빼면 안 되는 이유** — **익명 하위 클래스가 안 생기기** 때문이다.

- `{}` 가 없으면 `TypeRef` 는 `abstract` 라 인스턴스를 만들 수도 없고,\
  만들 수 있더라도 **타입 인자를 적을 클래스 선언이 없다.**
- 즉 이 관용구는 **"인스턴스에서는 못 읽는다"는 한계를 "클래스 선언에서는 읽힌다"로 우회**한 것이다.
- `new ArrayList<>() {}` 처럼 **표준 클래스에도 통한다** — 출력의 마지막 줄이 `java.util.ArrayList<java.lang.String>` 이다.

**실제 라이브러리** — Jackson 의 `TypeReference`, Guava 의 `TypeToken`, Spring 의 `ParameterizedTypeReference` 가 전부 이 구조다.\
`mapper.readValue(json, new TypeReference<List<User>>() {})` 라는 문법이 이상해 보이는 이유가 여기 있다.

### 12. 가변 인자 배열의 런타임 타입

**출력** (`Ex.java (19-e)`, JDK 21.0.5 — 17·25 에서도 동일)

```text
--- 가변 인자 배열의 런타임 타입
  whatIsIt("a","b"):  런타임 타입 = [Ljava.lang.Object;
  whatIsItGeneric("a","b"):  런타임 타입 = [Ljava.lang.String;
  whatIsItGeneric(1,2):  런타임 타입 = [Ljava.lang.Integer;
--- pickTwo: 컴파일은 되는데 대입에서 터진다
  catch -> class [Ljava.lang.Object; cannot be cast to class [Ljava.lang.String; ([Ljava.lang.Object; and [Ljava.lang.String; are in module java.base of loader 'bootstrap')
  Object[] 로 받으면 = [a, b] / 런타임 타입 = [Ljava.lang.Object;
```

**왜 그런가**

- `void whatIsIt(Object... xs)` — 파라미터가 `Object` 라 **`Object[]`** 가 만들어진다.
- `<T> void whatIsItGeneric(T... xs)` — **호출부에서 추론한 타입**으로 배열이 만들어진다.\
  `"a","b"` 면 `String[]`, `1,2` 면 `Integer[]` 다. **`Object[]` 가 아니다.**

```text
배열을 누가 만드느냐로 갈린다

  호출부가 만든다                          메서드 안에서 만든다
  +-----------------------------------+   +-----------------------------------+
  | whatIsItGeneric("a","b")          |   | (T[]) new Object[]{a, b}          |
  |   javac 가 String[] 를 만든다      |   |   Object[] 를 만든다               |
  |   런타임 타입 = [Ljava.lang.String;|   |   런타임 타입 = [Ljava.lang.Object;|
  +-----------------------------------+   +-----------------------------------+

  그 둘이 만나면
    String[] picked = pickTwo("a","b","c");
             ^^^^^^^^  javac 가 checkcast [Ljava/lang/String; 을 넣는다
                       그런데 실제로는 Object[] 다 -> ClassCastException
```

- **`String[] picked = ...` 는 터진다** — 메시지는 `class [Ljava.lang.Object; cannot be cast to class [Ljava.lang.String;` 이다.
- **`Object[] ok = ...` 는 된다** — 받는 타입이 `Object[]` 라 `checkcast` 가 `[Ljava/lang/Object;` 이고, 실제도 그렇기 때문이다.
- **받는 타입에 따라 갈린다.** 메서드 안에서는 절대 안 터진다(`T[]` 가 `Object[]` 로 소거돼 캐스트가 없다).
- `ArrayList.toArray()` 가 `Object[]` 를 돌려주는 이유가 이것이다 — 정본은 [`../05-arrays/`](../05-arrays/).

### 13. 지역 변수의 제네릭 타입은 어디에 있는가

**출력** (`Ex.java (19-h)`, JDK 21.0.5)

```text
$ javac -g
      LocalVariableTypeTable:
        Start  Length  Slot  Name   Signature
            8      10     1 local   Ljava/util/List<Ljava/lang/String;>;

$ javac (기본)
   LocalVariableTypeTable 이 0개
```

**왜 그런가**

- 지역 변수의 제네릭 타입은 **`Signature` 속성이 아니라 `LocalVariableTypeTable`** 에 들어간다.
- 그리고 **`javac -g`(또는 `-g:vars`)가 있어야** 생긴다. 기본 컴파일에는 없다.
- 이것을 읽는 **표준 리플렉션 API 는 없다** — `Method` 에 지역 변수를 주는 메서드가 없기 때문이다.

```text
"지역 변수만 빠진다"는 구조는 애너테이션과 같다

  19 타입 소거                            16 애너테이션
  +-----------------------------+        +-----------------------------+
  | 필드·메서드·클래스           |        | 필드·메서드·클래스·파라미터  |
  |   -> Signature 속성          |        |   -> Runtime*Annotations    |
  |   -> 리플렉션으로 읽힌다      |        |   -> 리플렉션으로 읽힌다     |
  |                             |        |                             |
  | 지역 변수                    |        | 지역 변수                    |
  |   -> LocalVariableTypeTable |        |   -> (아예 없다)             |
  |   -> 표준 API 로는 못 읽는다  |        |   -> 못 읽는다               |
  +-----------------------------+        +-----------------------------+
```

정본은 [`../16-annotations/`](../16-annotations/) 8번과 나란히 읽으면 된다.

### 14. 다른 주제와 잇기

**`new List<String>[3]` 금지와 배열의 성질**

```text
Ex.java:9: error: generic array creation
    static List<String>[] genericArray = new List<String>[3];     // (E)
                                         ^
```

```text
공변성 + 소거 = 아무도 못 잡는 사고

  만약 허용됐다면

    List<String>[] arr = new List<String>[3];
    Object[] objs = arr;                  // 배열은 공변이므로 통과
    objs[0] = new ArrayList<Integer>();   // aastore 의 검사는 "List 인가"뿐
                                          //   -> 소거 때문에 String/Integer 구분 못 한다
                                          //   -> 통과해 버린다
    String s = arr[0].get(0);             // 여기서 ClassCastException
```

- **배열의 공변성과 런타임 검사**(정본 [`../05-arrays/`](../05-arrays/))와 **제네릭의 소거**(이 주제)가 맞물려 검사가 무력해진다.
- 8번의 힙 오염이 정확히 이 경로를 **가변 인자로 뚫은 것**이다.

**제네릭이 불공변으로 설계된 이유**

- 배열처럼 공변으로 만들려면 **저장할 때 런타임 검사**가 있어야 한다.
- 그런데 소거 때문에 **검사할 정보가 없다.** `List<String>` 과 `List<Integer>` 가 같은 클래스다.
- 그래서 **대입 자체를 컴파일에서 막는** 쪽을 택했다. 정본은 [`../18-wildcards-pecs/`](../18-wildcards-pecs/) 다.

**구조가 같은 주제**

- [`../16-annotations/`](../16-annotations/) 다. 둘 다 "**javac 가 클래스 파일에 무엇을 적었나**"를 `javap -v` 로 확인한다.

```text
같은 질문, 다른 대상

  19 타입 소거                          16 애너테이션
  +------------------------------+     +------------------------------+
  | 소스에 List<String> 을 썼다   |     | 소스에 @Foo 를 썼다           |
  |   |                          |     |   |                          |
  |   v javac                    |     |   v javac                    |
  | descriptor 는 List (지워짐)   |     | @Retention 에 따라           |
  | Signature 에는 List<String>  |     |   없음 / Invisible / Visible |
  +------------------------------+     +------------------------------+
    항상 둘 다 (descriptor+Signature)     @Retention 이 갈림길
```

- 그리고 **둘 다 리플렉션에서 만난다** — [**58번 주제**](../58-reflection/)(리플렉션)가 합류 지점이다.

**소거를 택한 이유**

- **하위 호환**이었다. Java 5 가 제네릭을 넣을 때, 기존 `List` 를 쓰던 코드와 새 `List<String>` 코드가 **같은 JVM·같은 라이브러리에서 함께 돌아야** 했다.
- 타입 인자를 런타임에 남기는 방식(reification)이면 `java.util.List` 자체를 갈아엎어야 했고, 기존 클래스 파일이 못 돌게 된다.
- 그 선택의 연혁은 [`../../../../../../history/java/java-5.md`](../../../../../../history/java/java-5.md) 가 정본이다.\
  여기는 **그래서 오늘 무엇을 못 하나**까지다.

---

## 이 주제를 확인한 실행 목록

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Ex.java (19-a)` `javap -c -p` | 필드·`add`·`get` 이 소거되는 것, javac 가 끼워 넣은 `checkcast`, 바운드로 소거되는 `max` | 21 |
| `Ex.java (19-a)` `javap -v -p` | `descriptor` 대 `Signature` 를 필드·메서드·클래스에서 나란히 | 21 |
| `Ex.java (19-b)` | `getGenericType`/`getGenericParameterTypes` 가 읽는 것, 인스턴스에서는 못 읽는 것, 로 타입으로 오염시키고 꺼낼 때 터지는 것 | 17 · 21 · 25 (**출력 동일**) |
| `Ex.java (19-c1)` `javac` | `new T[]`·`new T()`·`T.class`·`catch (T)`·`new List<String>[3]` 금지 / `List<?>[]`·`List[]` 허용 | 17 · 21 · 25 (**동일**) |
| `Ex.java (19-c2)` `javac` | `instanceof List<String>` 에러, `List<?>`·`List` 허용, unchecked cast 경고 | 21 |
| `Ex.java (19-c3)` `javac` | 소거 후 충돌(`have the same erasure`), 공변 반환은 통과 | 17 · 21 · 25 (**동일**) |
| `Ex.java (19-c4)` `javac` | 같은 인터페이스를 다른 타입 인자로 두 번 구현 금지 | 21 |
| `Ex.java (19-d)` + `javap -c -p` | 브리지 메서드 둘의 바이트코드, `isBridge()`/`isSynthetic()`, 반환 타입만 다른 메서드 둘, 브리지 직접 호출 시 CCE | 17 · 21 · 25 (**출력 동일**) |
| `Ex.java (19-e)` | 힙 오염이 메서드 안에서는 조용한 것, 호출자에서 터지는 것, `@SafeVarargs`, 가변 인자 배열의 런타임 타입, `pickTwo` | 17 · 21 · 25 (**출력 동일**) |
| `Ex.java (19-e)` `javac -Xlint:all` | 경고 여섯 개가 선언 쪽·호출 쪽 양쪽에 나는 것 | 21 |
| `Ex.java (19-f)` + `javap -v -p` | super type token 이 읽어 내는 타입, `Ex$1` 에 `Signature` 가 있고 `Ex$Raw` 에는 없는 것 | 17 · 21 · 25 (**출력 동일**) |
| `Ex.java (19-g)` `javac` | `@SafeVarargs` 를 붙일 수 있는 자리(`static`·`final`), 못 붙이는 자리 | 21 |
| `Ex.java (19-h)` + `javap -v -p` | 브리지에 애너테이션이 그대로 붙는 것, `LocalVariableTypeTable` 이 `-g` 에서만 생기는 것 | 21 |

**구현 의존 항목** — `checkcast` 가 **어느 명령 자리에** 끼워지는지, `javap` 가 브리지를 출력하는 **순서**, `javac` 의 에러·경고 문구, `ClassCastException` 메시지의 `... are in module java.base of loader 'bootstrap'` 꼬리는 **전부 구현 세부**다.\
버전이 올랐을 때 다시 돌려 볼 것은 이 표의 **`(19-a)`·`(19-d)`** 둘이다 — 바이트코드 형태가 걸려 있다.\
반면 소거 규칙, `Signature` 속성의 존재, 브리지 메서드가 생기는 것, `new T[]`·`instanceof List<String>` 금지, 소거 후 충돌은 JLS·JVMS 가 보장한다.
