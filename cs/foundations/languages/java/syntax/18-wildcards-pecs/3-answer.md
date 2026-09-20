# java/syntax/18 — 와일드카드와 PECS: `? extends` / `? super` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러는 **Temurin JDK 21.0.5 에서 실제로 돌려 얻은 것**이다.\
> 실행 프로그램(`18-a`·`18-b`)은 **17.0.13 · 25.0.1** 에서도 돌렸고 출력이 한 글자도 다르지 않았다.\
> 컴파일 에러(`18-c`·`18-d`)도 17 과 25 에서 `diff` 로 대조해 **문자 단위로 같았다.**\
> 표준 라이브러리 시그니처는 `lib/src.zip` 의 실파일을 그대로 옮겼다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 이 대입들 중 어디가 막히는가

**출력** (`Ex.java (18-e)` `javac`, JDK 21.0.5)

```text
Ex.java:5: error: incompatible types: List<String> cannot be converted to List<Object>
        List<Object> objects = strings;      // (A) 제네릭은 공변인가
                               ^
```

**왜 그런가**

- **(A)만 에러**다. (B)와 (C)는 통과했다.

```text
같은 대입, 다른 결과

  List<String> strings = new ArrayList<>();

  List<Object>           objects = strings;   -> 컴파일 에러  (불공변)
  List<?>                unknown = strings;   -> OK
  List<? extends Object> ext     = strings;   -> OK
```

- 제네릭은 **불공변**이다(JLS §4.10.2). `String <: Object` 라고 `List<String> <: List<Object>` 가 되지 않는다.

**`List<String>` 을 받아 주는 상위 타입이 없는가** — 있다. **와일드카드**가 그것이다.

- `List<?>` 는 **모든 `List<...>` 의 상위 타입**이다.
- 즉 와일드카드는 **불공변이 막아 버린 유연성을 되돌려 주되, 대신 읽기·쓰기를 제한**하는 장치다.

**(B)와 (C)의 차이** — **없다.** `List<?>` 는 `List<? extends Object>` 의 줄임이다.\
둘 다 "원소 타입을 모르는 리스트"이고, 할 수 있는 일도 같다(6번 표 참조).

### 2. `? extends` 에 넣으면

**출력** (`Ex.java (18-c)` `javac`, JDK 21.0.5)

```text
Ex.java:5: error: incompatible types: int cannot be converted to CAP#1
        ext.add(1);                    // (A) Integer 를 넣으면?
                ^
  where CAP#1 is a fresh type-variable:
    CAP#1 extends Number from capture of ? extends Number
Ex.java:6: error: incompatible types: Integer cannot be converted to CAP#1
        ext.add(Integer.valueOf(1));   // (B)
                               ^
  where CAP#1 is a fresh type-variable:
    CAP#1 extends Number from capture of ? extends Number
Ex.java:7: error: incompatible types: Object cannot be converted to CAP#1
        ext.add(new Object());         // (C)
                ^
  where CAP#1 is a fresh type-variable:
    CAP#1 extends Number from capture of ? extends Number
Note: Some messages have been simplified; recompile with -Xdiags:verbose to get full output
3 errors
```

(D)와 (E)는 통과했다 — (E)의 실행 결과는 이렇다(`Ex.java (18-b)`).

```text
ext.add(null) 통과, ext = [null]
```

**왜 그런가**

| 자리 | 결과 |
|---|---|
| (A) `add(1)` | 에러 |
| (B) `add(Integer.valueOf(1))` | 에러 |
| (C) `add(new Object())` | 에러 |
| (D) `Number n = ext.get(0)` | **OK** |
| (E) `add(null)` | **OK** |

**`CAP#1` 은 무엇인가** — 컴파일러가 `?` 를 만나 만든 **이름 없는 임시 타입 변수**다(캡처 변환, JLS §5.1.10).

```text
List<? extends Number> ext  ->  컴파일러는 List<CAP#1> 로 본다
                                 단, CAP#1 extends Number

  꺼낼 때  get() : CAP#1 -> 상한이 Number 이므로 Number 로 받을 수 있다   OK
  넣을 때  add(x) : x 가 CAP#1 이어야 한다
                    CAP#1 이 Integer 인지 Double 인지 모른다 -> 아무것도 못 넣는다
```

**(E)만 되는 이유** — `null` 은 **모든 참조 타입의 값**이다.\
`CAP#1` 이 무엇이든 `null` 은 대입할 수 있으므로 유일하게 통과한다.\
실용적 의미는 거의 없다. **"못 넣는다"로 외우는 것이 맞고**, `null` 은 규칙의 귀결일 뿐이다.

### 3. `? super` 에서 꺼내면

**출력** (`Ex.java (18-d)` `javac`, JDK 21.0.5)

```text
Ex.java:6: error: incompatible types: CAP#1 cannot be converted to Integer
        Integer i = sup.get(0);        // (B) Integer 로 꺼내면?
                           ^
  where CAP#1 is a fresh type-variable:
    CAP#1 extends Object super: Integer from capture of ? super Integer
Ex.java:7: error: incompatible types: CAP#1 cannot be converted to Number
        Number  m = sup.get(0);        // (C) Number 로는?
                           ^
  where CAP#1 is a fresh type-variable:
    CAP#1 extends Object super: Integer from capture of ? super Integer
Ex.java:9: error: incompatible types: CAP#1 cannot be converted to Integer
        for (Integer x : sup) { }      // (E) 향상된 for 는?
                         ^
  where CAP#1 is a fresh type-variable:
    CAP#1 extends Object super: Integer from capture of ? super Integer
3 errors
```

(A)와 (D)는 통과했다. 실행 결과는 이렇다(`Ex.java (18-a)`).

```text
--- ? super 는 어떤 리스트를 받나
List<Integer> = [1, 2, null]
List<Number>  = [1, 2, null]
List<Object>  = [1, 2, null]
--- ? super 에서 꺼내면 무슨 타입인가
sup.get(0) 을 Object 로 = 1 (실제 클래스 Integer)
```

**왜 그런가**

| 자리 | 결과 |
|---|---|
| (A) `sup.add(1)` | **OK** |
| (B) `Integer i = sup.get(0)` | 에러 |
| (C) `Number m = sup.get(0)` | 에러 |
| (D) `Object o = sup.get(0)` | **OK** |
| (E) `for (Integer x : sup)` | 에러 |

```text
List<? super Integer> sup  ->  컴파일러는 List<CAP#1> 로 본다
                                단, CAP#1 super Integer, CAP#1 extends Object

  넣을 때  add(1) : Integer 가 CAP#1 의 하위임이 보장된다              OK
  꺼낼 때  get() : CAP#1 의 상한이 Object 뿐이다 -> Object 로만 받는다
```

**(C)가 안 되는 이유** — 변수가 `List<Number>` 를 가리킨다는 것은 **그 자리의 코드가 모르는 사실**이다.

```text
List<? super Integer> sup 가 가리킬 수 있는 실체

  +--------------------+  +--------------------+  +--------------------+
  | List<Integer>      |  | List<Number>       |  | List<Object>       |
  +--------------------+  +--------------------+  +--------------------+

  Number m = sup.get(0) 을 허용하면?
     List<Object> 였다면 String 이 나올 수도 있다 -> 깨진다
     그래서 상한인 Object 로만 받게 한다
```

출력의 `sup.get(0) 을 Object 로 = 1 (실제 클래스 Integer)` 가 보여 주는 것이 정확히 이것이다 —\
**실제로 든 것은 `Integer` 인데 정적 타입은 `Object`** 다.

**(E)가 (B)와 같은 에러인 이유** — 향상된 `for` 는 결국 `get`(정확히는 `Iterator.next()`)이기 때문이다.\
`for (Object x : sup)` 로 쓰면 통과한다.

### 4. 왜 그렇게 되는가 — 규칙의 이유

**`? extends Number` 에 못 넣는 이유**

```text
List<? extends Number> ext 가 가리킬 수 있는 실체를 나열한다

  +--------------------+  +--------------------+  +--------------------+
  | List<Integer>      |  | List<Double>       |  | List<Number>       |
  +--------------------+  +--------------------+  +--------------------+

  ext.add(1) 을 허용하면?
     List<Double> 이었다면 Double 창고에 Integer 가 들어간다  -> 깨진다
     List<Number> 이었다면 문제없다
     어느 쪽인지 컴파일러가 모른다 -> 전부 막는다

  ext.get(0) 은?
     Integer 든 Double 든 Number 든 -> 전부 Number 이상이다   -> 안전하다
```

**`? super Integer` 에서 `Integer` 로 못 꺼내는 이유**

```text
List<? super Integer> sup 가 가리킬 수 있는 실체를 나열한다

  +--------------------+  +--------------------+  +--------------------+
  | List<Integer>      |  | List<Number>       |  | List<Object>       |
  +--------------------+  +--------------------+  +--------------------+

  sup.add(1) 은?
     어느 창고든 Integer 는 받아 준다 (Integer 는 셋 다의 하위)  -> 안전하다

  Integer i = sup.get(0) 을 허용하면?
     List<Object> 였다면 String 이 나올 수도 있다              -> 깨진다
     그래서 Object 로만 받게 한다
```

**두 설명이 대칭인가** — **대칭이다.** 같은 문장을 방향만 뒤집어 읽으면 된다.

```text
                   ? extends T                    ? super T
  아는 것          상한만 안다 (T 이하)            하한만 안다 (T 이상)
  꺼내기           T 로 받을 수 있다   OK          Object 로만 받는다
  넣기             아무것도 못 넣는다              T 와 그 하위를 넣을 수 있다  OK
  역할             Producer                       Consumer
```

다만 **완전한 대칭은 아니다** — `? super T` 에서 `Object` 로는 꺼낼 수 있다.\
모든 타입의 상한이 `Object` 이기 때문이다. 그래서 "`? super` 에서는 못 꺼낸다"는 정확히는 **"`T` 로는 못 꺼낸다"**다.

### 5. 와일드카드 없이 copy 를 쓰면

**출력** (`Ex.java (18-h)` `javac`, JDK 21.0.5)

```text
Ex.java:8: error: method copyStrict in class Ex cannot be applied to given types;
        copyStrict(src, dst);                      // (A) 같은 T 로 맞출 수 있나
        ^
  required: List<T>,List<T>
  found:    List<Integer>,List<Number>
  reason: inference variable T has incompatible equality constraints Number,Integer
  where T is a type-variable:
    T extends Object declared in method <T>copyStrict(List<T>,List<T>)
Ex.java:10: error: method copyStrict in class Ex cannot be applied to given types;
        copyStrict(src, dst2);                     // (B)
        ^
  required: List<T>,List<T>
  found:    List<Integer>,List<Object>
  reason: inference variable T has incompatible equality constraints Object,Integer
2 errors
```

**왜 그런가**

- **컴파일되지 않는다.** `T` 를 `Integer` 와 `Number` 양쪽에 맞출 수 없다(`incompatible equality constraints`).
- 가장 평범한 복사(`List<Integer>` → `List<Number>`)가 막힌다는 것이 요점이다.

**PECS 를 적용한 시그니처**

```java
static <T> void copy(List<? extends T> src, List<? super T> dst) {
    for (T t : src) dst.add(t);
}
```

**출력** (`Ex.java (18-a)`, JDK 21.0.5 — 17·25 에서도 동일)

```text
--- PECS copy
List<Integer> -> List<Number> = [1, 2, 3]
List<Integer> -> List<Object> = [1, 2, 3]
```

```text
한 메서드 안에서 양쪽 문이 다 필요하다

  copy(src, dst)

   src : List<? extends T>              dst : List<? super T>
   +---------------------------+        +---------------------------+
   |  T 를 만들어 주는 쪽        |        |  T 를 받아 주는 쪽         |
   |  (Producer)               |  --->  |  (Consumer)               |
   |  꺼내기만 한다             |   T    |  넣기만 한다               |
   +---------------------------+        +---------------------------+
          Producer Extends                    Consumer Super
```

- **`src` 가 `? extends T`** — 메서드에 값을 **주는** 쪽이라 Producer 다.
- **`dst` 가 `? super T`** — 메서드에서 값을 **받는** 쪽이라 Consumer 다.
- 표준 라이브러리도 같은 형태다(9번 참조). `Collections.copy` 는 인자 순서만 반대다.

### 6. `List<Object>` 와 `List<?>` 의 차이

**출력** (`Ex.java (18-a)` `(18-b)`, JDK 21.0.5)

```text
--- List<Object> 는 List<?> 와 다르다
List<Object>.add(42)  = [a, 42]
List<?> 에는 add(42) 가 컴파일 에러
List<?> 에 List<String> 대입 = OK / List<Object> 에는 컴파일 에러
```

```text
size·clear·remove(int) 처럼 원소 타입을 안 쓰는 연산은 된다
  size = 2
  remove(0) 후 = [b]
  clear 후 = []
```

**`List<?>` 에 넣으려 하면** (`Ex.java (18-e)`)

```text
Ex.java:10: error: incompatible types: String cannot be converted to CAP#1
        u.add("x");                           // (D) 무제한에 문자열을 넣으면?
              ^
  where CAP#1 is a fresh type-variable:
    CAP#1 extends Object from capture of ?
Ex.java:11: error: incompatible types: Object cannot be converted to CAP#1
        u.add(new Object());                  // (E)
              ^
```

**왜 그런가**

```text
정반대 성질이다

  List<Object>                          List<?>
  +-----------------------------+       +-----------------------------+
  | 받을 수 있는 것              |       | 받을 수 있는 것              |
  |   List<Object> 뿐           |       |   모든 List<...>            |
  | 넣기                        |       | 넣기                        |
  |   아무거나 된다              |       |   null 만 된다              |
  | 꺼내기                      |       | 꺼내기                      |
  |   Object 로                 |       |   Object 로                 |
  +-----------------------------+       +-----------------------------+
    "무엇이든 담는 창고"                   "무엇이 담겼는지 모르는 창고"
```

**`size()`·`clear()`·`remove(0)` 가 되는 이유** — **원소 타입(`E`)을 시그니처에 쓰지 않기** 때문이다.

- `size()` 는 `int` 를 돌려주고, `clear()` 는 인자가 없고, `remove(int)` 는 인덱스를 받는다.
- 반면 `add(E)`·`set(int, E)` 는 `E`(= `CAP#1`)를 요구해서 막힌다.
- `contains(Object)`·`remove(Object)` 도 **`Object` 를 받으므로 된다**(`Ex.java (18-j)`).

```text
contains("a") = true
contains(42)  = false
remove("a")   = true -> [b]
```

**"아무거나 받는 파라미터"에는** — **`List<?>`** 를 쓴다.\
`List<Object>` 는 `List<Object>` 만 받으므로 그 목적을 전혀 달성하지 못한다.\
단, 읽어서 쓸 거면 `List<? extends 쓸타입>` 이 더 낫다.

### 7. 배열과 제네릭의 대비

**배열 쪽** — `javac` 는 **통과**하고 실행에서 터진다(`Ex.java (18-g)`, JDK 21.0.5).

```text
Exception in thread "main" java.lang.ArrayStoreException: java.lang.Integer
	at Ex.main(Ex.java:7)
```

**제네릭 쪽** — `javac` 에서 막힌다(`Ex.java (18-e)`).

```text
Ex.java:5: error: incompatible types: List<String> cannot be converted to List<Object>
        List<Object> objects = strings;      // (A) 제네릭은 공변인가
                               ^
```

**왜 그런가**

```text
배열 (공변) — 런타임에 터진다               제네릭 (불공변) — 컴파일에서 막힌다
+-----------------------------------+      +-----------------------------------+
| String[] strings = new String[3]; |      | List<String> strings = ...;       |
| Object[] objects = strings;  // OK|      | List<Object> objects = strings;   |
| objects[0] = Integer.valueOf(42); |      |                       ^ 여기서 에러 |
|                                   |      |                                   |
| javac : 통과 (경고도 없다)         |      | javac : error: incompatible types |
| java  : ArrayStoreException       |      | java  : 실행되지 않는다            |
+-----------------------------------+      +-----------------------------------+
  테스트에서 안 걸리면 운영에서 터진다         컴파일이 안 되므로 배포가 안 된다
```

```text
검사를 언제 하나 — 같은 실수의 두 타임라인

  배열
    컴파일 [대입 통과] --------> 실행 [저장 시 aastore 가 타입 검사] -> ArrayStoreException
                                       ^ 여기서 처음 안다

  제네릭
    컴파일 [대입 거부] -X
              ^ 여기서 끝난다
```

**시점이 다른 이유**

- **배열은 자기 원소 타입을 런타임에 들고 있다.** 그래서 저장할 때 비교할 수 있고, 공변을 허용해도 사고를 잡아낸다.\
  그 검사 주체가 `aastore` 명령이다 — 정본은 [`../05-arrays/`](../05-arrays/).
- **제네릭은 타입 인자를 런타임에 잃는다.** `List<String>` 과 `List<Integer>` 가 같은 클래스다.\
  그래서 **런타임 검사가 불가능**하고, 공변을 허용하면 아무도 못 잡는 사고가 된다 → **불공변으로 설계**했다.\
  정본은 [`../19-type-erasure/`](../19-type-erasure/).
- 배열이 공변인 것은 **제네릭이 없던 Java 1.0 에서 `Arrays.sort(Object[])` 같은 범용 메서드를 쓰기 위한** 선택이었다.

**이 대비에서 와일드카드의 자리**

```text
  배열의 공변성이 준 것            와일드카드가 주는 것
  +---------------------------+   +---------------------------+
  | Object[] a = stringArray; |   | List<?> l = stringList;   |
  |   -> 유연성 있음           |   |   -> 유연성 있음           |
  |                           |   |                           |
  | a[0] = 42;                |   | l.add(42);                |
  |   -> 런타임 예외           |   |   -> 컴파일 에러           |
  +---------------------------+   +---------------------------+
      전부 허용하고 사고 나면 터뜨린다      위험한 연산만 골라 막는다
```

**와일드카드는 배열 공변성을 안전하게 다시 만든 것**이다. 유연성은 같고, 사고가 컴파일로 당겨진다.

### 8. 캡처 — 같은 리스트인데 왜 못 옮기나

**출력** (`Ex.java (18-f)` `javac`, JDK 21.0.5)

```text
Ex.java:6: error: incompatible types: Object cannot be converted to CAP#1
        list.set(0, list.get(1));       // (A) 같은 리스트인데도?
                            ^
  where CAP#1 is a fresh type-variable:
    CAP#1 extends Object from capture of ?
Ex.java:7: error: incompatible types: Object cannot be converted to CAP#1
        list.set(1, tmp);
                    ^
  where CAP#1 is a fresh type-variable:
    CAP#1 extends Object from capture of ?
Ex.java:17: error: incompatible types: Number cannot be converted to CAP#1
        a.set(0, b.get(0));             // (B) 둘 다 ? extends Number 인데?
                      ^
  where CAP#1 is a fresh type-variable:
    CAP#1 extends Number from capture of ? extends Number
3 errors
```

**왜 그런가** — (A)(B)(C) 셋 다 에러다.

```text
? 는 쓰일 때마다 새로 캡처된다

  static void swapFirstTwo(List<?> list)

    list.get(1)    ->  결과의 정적 타입은 Object 로 올라간다
    list.set(0, ?) ->  CAP#1 을 요구한다
                       Object 는 CAP#1 이 아니다 -> 막힌다

  두 파라미터면 더 분명하다

  static void mix(List<? extends Number> a, List<? extends Number> b)

    a 의 ?  ->  CAP#1          b 의 ?  ->  CAP#2
    둘 다 "Number 아래 어딘가"지만 같은 타입이라는 보장이 없다
    a 가 List<Integer>, b 가 List<Double> 일 수도 있다
```

- 같은 변수의 `get` 과 `set` 인데도 막히는 이유는, 와일드카드가 **"이 리스트의 원소 타입"이라는 이름을 갖지 못하기** 때문이다.\
  꺼낸 값의 타입과 넣어야 할 타입이 **같다고 적을 방법이 없다.**

**푸는 관용구 — 캡처 헬퍼**

```java
static void swapOk(List<?> list) { swapHelper(list); }      // 여기서 캡처가 T 로 잡힌다
private static <T> void swapHelper(List<T> list) {
    T tmp = list.get(0);
    list.set(0, list.get(1));
    list.set(1, tmp);
}
```

- **타입 파라미터로 한 번 받으면** 그 이름(`T`)이 고정되어 자유롭게 읽고 쓸 수 있다.
- `Collections.swap` 같은 표준 API 가 내부에 `private` 헬퍼를 두는 이유가 이것이다.
- 판단 규칙: **공개 API 는 와일드카드로 유연하게, 내부 구현은 타입 파라미터로.**

### 9. 표준 API 의 시그니처를 읽기

`src.zip` 의 실파일에서 읽은 시그니처다.

```java
// java/util/Collections.java
public static <T> void copy(List<? super T> dest, List<? extends T> src)
public static <T> void fill(List<? super T> list, T obj)
public static <T extends Object & Comparable<? super T>> T max(Collection<? extends T> coll)
public static <T> boolean addAll(Collection<? super T> c, T... elements)

// java/util/List.java
default void sort(Comparator<? super E> c)

// java/util/Collection.java
boolean addAll(Collection<? extends E> c)

// java/util/stream/Stream.java
Stream<T> filter(Predicate<? super T> predicate)
<R> Stream<R> map(Function<? super T, ? extends R> mapper)
void forEach(Consumer<? super T> action)
```

**출력** (`Ex.java (18-a)`, JDK 21.0.5)

```text
--- 표준 API 가 쓰는 PECS
List<Integer>.sort(Comparator<Number>) = [1, 2, 3]
Collections.copy(List<Object>, List<Integer>) = [1, 2, 3]
Collections.max(List<Integer>) = 3
```

**왜 그런가**

| 와일드카드 | 역할 | 이유 |
|---|---|---|
| `copy` 의 `dest: ? super T` | Consumer | 메서드가 거기에 **넣는다** |
| `copy` 의 `src: ? extends T` | Producer | 메서드가 거기서 **꺼낸다** |
| `max` 의 `coll: ? extends T` | Producer | 꺼내서 비교한다 |
| `max` 의 `Comparable<? super T>` | Consumer | `compareTo` 가 T 를 **받는다** |
| `sort` 의 `Comparator<? super E>` | Consumer | 비교자가 E 를 **받는다** |
| `filter` 의 `Predicate<? super T>` | Consumer | 술어가 T 를 **받는다** |
| `addAll(Collection<? extends E>)` | Producer | 인자에서 **꺼내** 자기에게 넣는다 |

**`map` 에 둘이 다 나오는 이유**

```text
  <R> Stream<R> map(Function<? super T, ? extends R> mapper)
                             \_________/  \________/
                             함수가 받는다  함수가 만든다
                             Consumer      Producer
                             -> super      -> extends
```

- 함수형 인터페이스 하나에 **입력과 출력이 다 있기** 때문이다.
- 그래서 `Stream<Integer>` 에 `Function<Number, Object>` 를 넘길 수 있다 — 받는 쪽은 넓게, 주는 쪽은 좁게.
- 함수형 인터페이스 지도는 [`../31-functional-interfaces/`](../31-functional-interfaces/) 가 정본이다.

**`List<Integer>` 를 `Comparator<Number>` 로 정렬할 수 있는가** — 있다. 위 출력의 첫 줄이 그 확인이다.

- 근거는 `sort` 의 시그니처가 `Comparator<? super E>` 라는 것이다.
- `E = Integer` 이고 `Number` 는 `Integer` 의 상위이므로 `Comparator<Number>` 가 `Comparator<? super Integer>` 를 만족한다.
- `Comparator<E>` 였다면 `Comparator<Integer>` 만 받았을 것이다.

### 10. 와일드카드를 쓸 수 없는 자리

**(A) 선언에 쓰면** (`Ex.java (18-i)` `javac` — 이 줄은 파서에서 끊겨 나머지와 따로 컴파일했다)

```text
Ex.java:3: error: <identifier> expected
    static class Box<? extends Number> {}          // (A) 선언에 와일드카드
                     ^
1 error
```

**(B)(C) `new` 에 쓰면** (`Ex.java (18-i)`)

```text
Ex.java:4: error: unexpected type
        List<?> a = new ArrayList<?>();            // (B) new 에 와일드카드
                                 ^
  required: class or interface without bounds
  found:    ?
Ex.java:5: error: unexpected type
        List<? extends Number> b = new ArrayList<? extends Number>();  // (C)
                                                ^
  required: class or interface without bounds
  found:    ? extends Number
2 errors
```

**(D)는 통과**했다 — `Map<String, ? extends Number> ok = new HashMap<String, Integer>();`

**(E) 다중 바운드** (`Ex.java (18-k)`)

```text
Ex.java:4: error: > or ',' expected
    static void f(List<? extends Comparable & Serializable> l) { }   // (A) 와일드카드 다중 바운드
                                            ^
1 error
```

**왜 그런가**

```text
와일드카드가 되는 자리 / 안 되는 자리

  된다                                    안 된다
  +---------------------------------+     +---------------------------------+
  | 변수의 타입                      |     | 클래스·메서드 선언의 타입 파라미터 |
  |   List<?> l;                    |     |   class Box<? extends Number>   |
  | 파라미터의 타입                  |     | new 의 타입 인자                 |
  |   void f(List<? extends T> x)   |     |   new ArrayList<?>()            |
  | 필드의 타입                      |     | 다중 바운드                      |
  |   Map<String, ? extends Number> |     |   ? extends A & B               |
  +---------------------------------+     +---------------------------------+
```

- 와일드카드는 **"타입을 쓰는 자리"**에만 온다. **"타입을 선언하는 자리"**에는 못 온다.

**`new` 에 못 쓰는 이유** — `new` 는 **실제 객체를 만드는 것**이라 원소 타입이 확정돼야 한다.\
"모르는 타입의 리스트"라는 객체는 만들 수 없다.\
관용구는 `List<?> l = new ArrayList<String>();` — **만들 때는 확정하고 받을 때만 `?`** 로 둔다.

**(E)가 필요하면** — **타입 파라미터로 옮긴다.** 그쪽은 다중 바운드가 된다(`Ex.java (18-k)` 에서 통과 확인).

```java
static <T extends Comparable<T> & Serializable> void g(List<T> l) { }
```

### 11. 반환 타입에 와일드카드를 쓰면

**출력** (`Ex.java (18-j)` 실행 + `(18-k)` `javac`, JDK 21.0.5)

```text
반환된 와일드카드에서 읽기 = 1
```

```text
Ex2.java:6: error: incompatible types: int cannot be converted to CAP#1
        got.add(3);                     // 호출자가 받은 리스트에 넣으려 하면
                ^
  where CAP#1 is a fresh type-variable:
    CAP#1 extends Number from capture of ? extends Number
```

**왜 그런가**

- **(A) 읽기는 된다** — `Number n = got.get(0);` 이 통과한다.
- **(B) 넣기는 막힌다** — 2번과 같은 `CAP#1` 에러다.

```text
파라미터의 와일드카드 vs 반환의 와일드카드

  파라미터                               반환
  +-----------------------------+       +-----------------------------+
  | void f(List<? extends T> s) |       | List<? extends T> g()       |
  | 호출자가 넓게 넘길 수 있다   |       | 호출자가 받은 것으로         |
  |   -> 유연성을 준다           |       |   할 수 있는 일이 줄어든다   |
  +-----------------------------+       +-----------------------------+
```

**반환 타입에는 확정 타입**을 쓴다 — `List<Number>` 처럼.\
와일드카드는 **호출자에게 유연성을 주는 장치이지, 구현자가 애매하게 남기는 장치가 아니다.**

### 12. 어느 것을 고를 것인가

```text
파라미터 하나를 보고 이렇게 묻는다

  이 메서드가 그 컬렉션에서 값을 꺼내는가?
        |
        +-- 꺼내기만 한다        -> List<? extends T>   (Producer Extends)
        |
        +-- 넣기만 한다          -> List<? super T>     (Consumer Super)
        |
        +-- 둘 다 한다           -> List<T>             (와일드카드를 쓰지 마라)
        |
        +-- 원소 타입을 안 쓴다   -> List<?>
```

**필드 타입에 와일드카드를 두면**

- 그 필드로 할 수 있는 일이 **영구히** 줄어든다. 메서드 파라미터는 호출 하나로 끝나지만 필드는 객체 수명 내내 간다.
- `List<? extends Number> items;` 를 필드로 두면 **그 객체는 `items` 에 아무것도 못 넣는다.**
- 그래서 필드는 대개 확정 타입으로 두고, **받을 때만** 와일드카드로 넓힌다.

**`Comparator` 파라미터가 항상 `? super` 인 이유**

- 비교자는 원소를 **받아서** 비교한다 — **Consumer** 다.
- `Comparator<Number>` 는 `Integer` 도 비교할 수 있다. 그것을 받아 주려면 `? super E` 여야 한다.
- 9번의 출력 `List<Integer>.sort(Comparator<Number>) = [1, 2, 3]` 이 그 실익이다.

### 13. 다른 주제와 잇기

**제네릭이 런타임 검사를 못 하는 이유**

- **타입 소거** 때문이다. `List<String>` 과 `List<Integer>` 가 런타임에 같은 클래스다.
- 배열처럼 "저장할 때 비교"를 하려 해도 **비교할 정보가 없다.**
- 정본은 [`../19-type-erasure/`](../19-type-erasure/) 다.

**`ArrayStoreException` 의 발생 조건과 메시지**

- 정본은 [`../05-arrays/`](../05-arrays/) 다. 거기서 `javap` 로 `aastore` 대 `iastore` 를 보고, 메시지가 **타입 이름 하나뿐**이라는 것까지 확인한다.
- 여기서는 **"제네릭에는 이 예외에 해당하는 것이 없다"**는 대비까지가 범위다.

**`new List<String>[3]` 이 왜 금지인가**

```text
Ex.java:9: error: generic array creation
    static List<String>[] genericArray = new List<String>[3];     // (E)
                                         ^
```

```text
공변성 + 소거 = 아무도 못 잡는 사고

  만약 new List<String>[3] 이 허용됐다면

    List<String>[] arr = new List<String>[3];
    Object[] objs = arr;                  // 배열은 공변이므로 통과
    objs[0] = new ArrayList<Integer>();   // aastore 가 검사하는 것은 "List 인가"뿐
                                          //   -> 소거 때문에 String/Integer 구분 못 한다
                                          //   -> 통과해 버린다
    String s = arr[0].get(0);             // 여기서 ClassCastException
```

- **배열의 런타임 검사**(공변성의 안전장치)와 **제네릭의 소거**가 맞물려 **검사가 무력해진다.**
- 그래서 언어가 아예 생성을 막았다. 정본은 [`../19-type-erasure/`](../19-type-erasure/) 다.
- 이 사고 경로가 **이 주제와 05번·19번을 하나로 묶는 자리**다.

**`Comparable<? super T>` 바운드**

- [`../17-generic-declarations/`](../17-generic-declarations/) 9번이 그 실험을 갖고 있다.\
  `Animal implements Comparable<Animal>`, `Dog extends Animal` 일 때 `Comparable<T>` 바운드는 `List<Dog>` 을 거부한다.
- 왜 `? super` 가 그것을 푸는지는 여기 4번의 대칭표가 답이다.
- `Comparable` 계약 자체는 [`../28-comparable-comparator/`](../28-comparable-comparator/) 가 정본이다.

---

## 이 주제를 확인한 실행 목록

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Ex.java (18-a)` | PECS `copy`, `? extends` 가 받는 세 리스트, `? super` 가 받는 세 리스트, `? super` 에서 `Object` 로 읽기, `add(null)`, `List<Object>` 대비, 표준 API 세 개 | 17 · 21 · 25 (**출력 동일**) |
| `Ex.java (18-b)` | `? extends`·`?` 에 `null` 만 들어가는 것, 원소 타입을 안 쓰는 연산(`size`·`remove(int)`·`clear`) | 17 · 21 · 25 (**출력 동일**) |
| `Ex.java (18-c)` `javac` | `? extends` 에 `int`·`Integer`·`Object` 를 넣는 세 에러와 `CAP#1` | 17 · 21 · 25 (**동일**) |
| `Ex.java (18-c)` `javac -Xdiags:verbose` | 같은 에러의 전체 형태(`no suitable method found for add(int)`) | 21 |
| `Ex.java (18-d)` `javac` | `? super` 에서 `Integer`·`Number` 로 꺼내기, 향상된 `for` 의 세 에러 | 17 · 21 · 25 (**동일**) |
| `Ex.java (18-e)` `javac` | `List<String>` → `List<Object>` 불공변 에러, `List<?>` 에 넣기 두 에러 | 21 |
| `Ex.java (18-f)` `javac` | 캡처 — 같은 리스트 자리바꿈, 두 와일드카드 파라미터 간 이동 | 21 |
| `Ex.java (18-g)` `javac` + 실행 | 배열 공변성이 **컴파일을 통과**하고 `ArrayStoreException` 으로 터지는 것 | 21 |
| `Ex.java (18-h)` `javac` | 와일드카드 없는 `copyStrict` 가 `List<Integer>`→`List<Number>` 를 거부하는 것 | 21 |
| `Ex.java (18-i)` `javac` | 선언·`new` 에 와일드카드를 쓸 수 없는 것 | 21 |
| `Ex.java (18-j)` | `Collection<?>` 의 `contains`/`remove(Object)`, 반환된 와일드카드에서 읽기 | 21 |
| `Ex.java (18-k)` `javac` | 와일드카드 다중 바운드 금지(타입 파라미터는 허용), 반환된 와일드카드에 넣기 실패 | 21 |
| `src.zip` 열람 | `Collections.copy`/`fill`/`max`/`addAll`, `List.sort`, `Collection.addAll`, `Stream.filter`/`map`/`flatMap`/`forEach`, `Iterable.forEach` 의 시그니처 | 21 |

**구현 의존 항목** — `javac` 의 `CAP#1`·`INT#1` 표기와 에러 문구, `-Xdiags` 에 따라 메시지가 줄어드는 것은 **구현 세부**다.\
버전이 올랐을 때 다시 돌려 볼 것은 없다 — 이 주제의 근거는 전부 JLS 규칙(불공변·캡처 변환·배열 공변)이고,\
문구가 바뀌어도 **에러가 나는 자리 자체는 바뀌지 않는다.**\
다만 **`ArrayStoreException` 의 메시지 형식**은 구현 세부이므로 [`../05-arrays/`](../05-arrays/) 쪽 표를 따른다.
