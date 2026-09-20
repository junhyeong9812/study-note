# java/syntax/18 — 와일드카드와 PECS: `? extends` / `? super` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [JLS SE 21 §4.5.1 Type Arguments of Parameterized Types](https://docs.oracle.com/javase/specs/jls/se21/html/jls-4.html) · [§5.1.10 Capture Conversion](https://docs.oracle.com/javase/specs/jls/se21/html/jls-5.html) · [§4.10.2 Subtyping among Class and Interface Types](https://docs.oracle.com/javase/specs/jls/se21/html/jls-4.html) · [§4.10.3 Subtyping among Array Types](https://docs.oracle.com/javase/specs/jls/se21/html/jls-4.html) · JDK 21.0.5 표준 라이브러리 소스 `java.base/java/util/*.java`(`lib/src.zip`).
> **실행 검증** — 이 문서의 모든 출력·에러는 Temurin **JDK 21.0.5** 에서 실제로 돌려 얻은 것이다.\
> `Ex.java (18-a)` `(18-b)` 는 **17.0.13 · 21.0.5 · 25.0.1** 에서 다 돌렸고 출력이 한 글자도 다르지 않았다.\
> 컴파일 에러 `(18-c)` `(18-d)` 도 17 과 25 에서 `diff` 로 대조해 **문자 단위로 같았다.**\
> **"세 곳에서 같았다"는 관찰이지 보장이 아니다** — 보장은 JLS·javadoc 인용으로만 적었다.
> **버전** — 와일드카드는 **Java 5**. 이후 문법 변화 없다.
> **범위** — 타입 파라미터를 **선언하는 것**은 [`../17-generic-declarations/`](../17-generic-declarations/) 가,\
> 타입 인자가 **런타임에 사라지는 것**은 [`../19-type-erasure/`](../19-type-erasure/) 가 정본이다.\
> 여기는 **`?` 가 읽기·쓰기를 어떻게 막는가**만 다룬다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 JLS 로, 출력은 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**`? extends` 는 "출구 전용 문", `? super` 는 "입구 전용 문"이다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 창고 | 컬렉션 객체 |
| 창고 문에 붙은 팻말 | 변수의 **선언 타입** (`List<? extends Number>`) |
| 창고 안에 실제로 든 물건의 종류 | 실제 타입 인자 (`List<Integer>`) |
| **출구 전용 문** — 꺼낼 수만 있다 | `? extends` |
| **입구 전용 문** — 넣을 수만 있다 | `? super` |
| 문지기 | 컴파일러 |
| "무엇이 들었는지는 모른다"는 팻말 | 무제한 와일드카드 `?` |

- **출구 전용 문**(`? extends Number`) — 안에 `Integer` 가 들었는지 `Double` 이 들었는지 **모른다.**\
  하지만 나오는 것은 전부 **`Number` 이상**이다. 그래서 **꺼내는 건 안전하고 넣는 건 위험하다.**
- **입구 전용 문**(`? super Integer`) — 안이 `Integer` 창고인지 `Number` 창고인지 `Object` 창고인지 **모른다.**\
  하지만 어느 쪽이든 **`Integer` 는 받아 준다.** 그래서 **넣는 건 안전하고 꺼내는 건 `Object` 로만 된다.**
- 배열에는 이 문이 **없다.** 배열은 "아무 문이나 통과시키고 넣을 때 경비원이 막는" 구조라 **런타임에 터진다.**

```text
PECS — 무엇을 하는 쪽이냐로 문을 고른다

   Producer(생산자: 꺼내 주는 쪽)          Consumer(소비자: 받아 주는 쪽)
   List<? extends Number> src            List<? super Integer> dst
   +---------------------------+         +---------------------------+
   |   [꺼내기] OK              |         |   [꺼내기] Object 로만     |
   |   Number n = src.get(0);  |         |   Object o = dst.get(0);  |
   |                           |         |                           |
   |   [넣기]  막힌다           |         |   [넣기]  OK              |
   |   src.add(1); // 에러     |         |   dst.add(1);             |
   +---------------------------+         +---------------------------+
           E = Extends                            S = Super
        "꺼내 오는 쪽은 extends"               "넣어 주는 쪽은 super"
```

**똑같은 구조로** Java 가 동작한다: 창고 = 컬렉션, 팻말 = 선언 타입, 문의 방향 = `extends`/`super`, 문지기 = 컴파일러.

실무에서 이게 물리는 자리는 **"복사" 유틸**이다.\
`copy(List<T> src, List<T> dst)` 로 쓰면 `List<Integer>` → `List<Number>` 복사가 **컴파일 에러**가 된다.\
`copy(List<? extends T> src, List<? super T> dst)` 로 바꿔야 비로소 통한다.

> **와일드카드(wildcard)** — 타입 인자 자리에 쓰는 `?`. "어떤 타입인지 모른다"를 타입으로 적은 것.\
> 예: `List<?>` 는 `List<String>` 일 수도 `List<Integer>` 일 수도 있는, 무엇인지 모르는 리스트다.

> **불공변(invariant)** — 타입 인자가 다르면 하위 타입 관계가 없는 것. 제네릭이 이쪽이다.\
> 예: `String` 이 `Object` 의 하위 타입이지만 `List<String>` 은 `List<Object>` 의 하위 타입이 **아니다.**

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 네 질문을 둔다.

1. **왜 `? extends` 에는 못 넣고 `? super` 에서는 못 꺼내는가.**
2. `List<Object>` 와 `List<?>` 는 무엇이 다른가 — 둘 다 "아무거나"처럼 보이는데.
3. 배열은 왜 같은 실수를 **런타임에** 터뜨리고 제네릭은 **컴파일에서** 막는가.
4. 와일드카드 둘을 쓴 리스트끼리 값을 옮기지 못하는 이유는 무엇인가.

## 동작 방식

### (1) 불공변 — 출발점

**언제 쓰나** — `List<String>` 을 `List<Object>` 파라미터에 넘기려다 막혔을 때.

**`javac` 출력 그대로** (`Ex.java (18-e)`, JDK 21.0.5)

```text
Ex.java:5: error: incompatible types: List<String> cannot be converted to List<Object>
        List<Object> objects = strings;      // (A) 제네릭은 공변인가
                               ^
```

(B) `List<?> unknown = strings;` 와 (C) `List<? extends Object> ext = strings;` 는 **통과했다.**

```text
같은 대입, 다른 결과

  List<String> strings = new ArrayList<>();

  List<Object>           objects = strings;   -> 컴파일 에러
  List<?>                unknown = strings;   -> OK
  List<? extends Object> ext     = strings;   -> OK
```

그림 해설 (한 단계씩):

- 제네릭은 **불공변**이다 — `String` 이 `Object` 의 하위 타입이어도 `List<String>` 은 `List<Object>` 의 하위 타입이 아니다.
- 그러면 `List<String>` 을 받아 주는 **상위 타입이 아예 없는가** — 있다. 그것이 **와일드카드**다.
- `List<?>` 와 `List<? extends Object>` 는 같은 뜻이고, **모든 `List<...>` 의 상위 타입**이다.
- 즉 와일드카드는 **불공변이 막아 버린 유연성을 되돌려 주되, 대신 읽기·쓰기를 제한**하는 장치다.

비용 — 없다. 컴파일 타임 규칙이다.

### (2) `? extends` 에 넣으면 왜 막히나 — 핵심 도식

**언제 쓰나** — "읽기만 하는 파라미터"를 선언할 때.

**`javac` 출력 그대로** (`Ex.java (18-c)`, JDK 21.0.5)

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
```

(D) `Number n = ext.get(0);` 은 **통과했다.**

```text
왜 못 넣나 — "무엇이 들었는지 모른다"를 끝까지 따라가면

  List<? extends Number> ext = ???;

  가능한 실체가 여럿이다
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

```text
반대편 — ? super 에서 왜 못 꺼내나

  List<? super Integer> sup = ???;

  가능한 실체가 여럿이다
  +--------------------+  +--------------------+  +--------------------+
  | List<Integer>      |  | List<Number>       |  | List<Object>       |
  +--------------------+  +--------------------+  +--------------------+

  sup.add(1) 은?
     어느 창고든 Integer 는 받아 준다 (Integer 는 셋 다의 하위)  -> 안전하다

  Integer i = sup.get(0) 을 허용하면?
     List<Object> 였다면 String 이 나올 수도 있다              -> 깨진다
     그래서 Object 로만 받게 한다
```

**`? super` 쪽 에러도 그대로 실었다** (`Ex.java (18-d)`, JDK 21.0.5)

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
```

(A) `sup.add(1);` 과 (D) `Object o = sup.get(0);` 은 **통과했다.**

그림 해설 (한 단계씩):

- 에러 메시지의 **`CAP#1`** 이 열쇠다. 컴파일러는 `?` 를 만나면 **이름 없는 임시 타입 변수**를 하나 만든다(캡처 변환).
- `? extends Number` → `CAP#1 extends Number` — **상한만 안다.** 그래서 **꺼낼 때는 `Number` 로 받을 수 있고**, 넣을 때는 `CAP#1` 이 정확히 무엇인지 몰라 아무것도 못 넣는다.
- `? super Integer` → `CAP#1 super Integer` — **하한만 안다.** 그래서 **넣을 때는 `Integer` 가 통하고**, 꺼낼 때는 상한이 `Object` 뿐이라 `Object` 로만 받는다.
- 향상된 `for` 도 막힌다 — `for (Integer x : sup)` 은 결국 `get` 이기 때문이다.

> **캡처 변환(capture conversion)** — 컴파일러가 와일드카드 `?` 를 그 자리에서만 유효한 임시 타입 변수로 바꾸는 것(JLS §5.1.10).\
> 예: `List<? extends Number>` 를 `List<CAP#1>`(단, `CAP#1 extends Number`)로 취급한다. 에러 메시지의 `CAP#1` 이 그것이다.

비용 — 없다. 전부 컴파일 타임이다.

### (3) PECS — 그래서 파라미터를 어떻게 선언하나

**언제 쓰나** — 컬렉션을 파라미터로 받는 메서드를 선언할 때. **매번** 이 판단을 한다.

**와일드카드 없이 쓰면 어떻게 되는지부터 던져 봤다** (`Ex.java (18-h)`, JDK 21.0.5)

```text
Ex.java:8: error: method copyStrict in class Ex cannot be applied to given types;
        copyStrict(src, dst);                      // (A) 같은 T 로 맞출 수 있나
        ^
  required: List<T>,List<T>
  found:    List<Integer>,List<Number>
  reason: inference variable T has incompatible equality constraints Number,Integer
  where T is a type-variable:
    T extends Object declared in method <T>copyStrict(List<T>,List<T>)
```

`List<Integer>` 를 `List<Number>` 에 복사하는 **가장 평범한 호출**이 막힌다.

와일드카드를 쓰면 통한다.

```java
static <T> void copy(List<? extends T> src, List<? super T> dst) {
    for (T t : src) dst.add(t);          // src 에서 꺼내고(생산), dst 에 넣는다(소비)
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

**같은 파라미터에 어떤 실인자가 들어갈 수 있나** (`Ex.java (18-a)`)

```text
--- ? extends 는 어떤 리스트를 받나
sum(List<Integer>) = 6.0
sum(List<Double>)  = 4.0
sum(List<Long>)    = 10.0
--- ? super 는 어떤 리스트를 받나
List<Integer> = [1, 2, null]
List<Number>  = [1, 2, null]
List<Object>  = [1, 2, null]
```

```text
  Collection<? extends Number> ns 가 받는 것         List<? super Integer> dst 가 받는 것

        Number                                              Object
       /  |  \                                                |
  Integer Double Long   <- 전부 받는다                       Number
                                                              |
                                                           Integer   <- 셋 다 받는다
      "Number 를 포함한 아래쪽"                          "Integer 를 포함한 위쪽"
```

그림 해설 (한 단계씩):

- **PECS** = **P**roducer **E**xtends, **C**onsumer **S**uper.\
  "이 파라미터가 나에게 값을 **주는가**(producer) **받는가**(consumer)"로 고른다.
- 둘 다 하는 파라미터(꺼내고 또 넣는)에는 **와일드카드를 쓰면 안 된다** — 그냥 `List<T>` 로 둔다.
- 반환 타입에도 와일드카드를 쓰지 않는다 — 호출자가 캡처를 떠안게 된다.

비용 — 없다. 선언이 길어지는 것이 대가다.

### (4) `List<Object>` 와 `List<?>` 는 다르다

**언제 쓰나** — "아무거나 받는 리스트"를 선언하려 할 때. 두 후보가 정반대 성질을 갖는다.

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

```text
정반대 성질이다

  List<Object>                          List<?>
  +-----------------------------+       +-----------------------------+
  | 받을 수 있는 것              |       | 받을 수 있는 것              |
  |   List<Object> 뿐           |       |   모든 List<...>            |
  |                             |       |                             |
  | 넣기                        |       | 넣기                        |
  |   아무거나 된다              |       |   null 만 된다              |
  |                             |       |                             |
  | 꺼내기                      |       | 꺼내기                      |
  |   Object 로                 |       |   Object 로                 |
  +-----------------------------+       +-----------------------------+
    "무엇이든 담는 창고"                   "무엇이 담겼는지 모르는 창고"
```

그림 해설 (한 단계씩):

- `List<Object>` 는 **"Object 를 원소로 하는 리스트"**다. `List<String>` 을 여기 대입할 수 없다(불공변).
- `List<?>` 는 **"원소 타입을 모르는 리스트"**다. 모든 `List<...>` 를 받는다.
- 대신 `List<?>` 에는 **아무것도 못 넣는다.** 단 하나 예외가 `null` 이다.
- 원소 타입을 쓰지 않는 연산(`size()`·`clear()`·`remove(int)`·`isEmpty()`)은 **전부 된다.**

**`null` 만 되는 이유**

```text
--- ? extends 에 넣을 수 있는 유일한 값
ext.add(null) 만 된다 -> [null]
```

- `null` 은 **모든 참조 타입의 값**이다. `CAP#1` 이 무엇이든 `null` 은 대입할 수 있다.
- 그래서 "읽기는 되고 쓰기는 `null` 만" 이라는 말이 나온다.
- 실용적 의미는 거의 없다 — **"못 넣는다"로 외우는 것이 맞고**, `null` 은 규칙의 귀결일 뿐이다.

비용 — 없다.

### (5) 배열 공변성과의 대비 — 이 주제의 값

**언제 쓰나** — "배열 대신 `List` 를 쓰라"는 조언의 근거를 판단할 때.

**같은 실수를 두 방식으로 써서 나란히 돌렸다.**

**배열 쪽** (`Ex.java (18-g)`, JDK 21.0.5 — `javac` 는 통과했다)

```text
Exception in thread "main" java.lang.ArrayStoreException: java.lang.Integer
	at Ex.main(Ex.java:7)
```

**제네릭 쪽** (`Ex.java (18-e)`, JDK 21.0.5)

```text
Ex.java:5: error: incompatible types: List<String> cannot be converted to List<Object>
        List<Object> objects = strings;      // (A) 제네릭은 공변인가
                               ^
```

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

그림 해설 (한 단계씩):

- **배열은 공변**이다 — `String[]` 은 `Object[]` 의 하위 타입이다(JLS §4.10.3). 그래서 대입이 통과한다.
- 대신 **저장할 때마다 런타임 타입 검사**를 한다. 그 검사 주체가 `aastore` 명령이고, 실패가 `ArrayStoreException` 이다.\
  그 정본은 [`../05-arrays/`](../05-arrays/) 다(거기서 `javap` 로 `aastore` 대 `iastore` 를 본다).
- **제네릭은 불공변**이다 — 대입 자체를 막는다. 런타임 검사가 **아예 필요 없다.**
- 제네릭이 런타임 검사를 못 하는 이유도 있다 — 타입 인자가 **런타임에 지워지기** 때문이다([`../19-type-erasure/`](../19-type-erasure/)).

```text
그래서 성질이 이렇게 갈린다

              배열                          제네릭
  공변성      공변 (S[] <: T[])             불공변 (List<S> !<: List<T>)
  검사 시점   런타임 (저장할 때마다)          컴파일 타임 (대입할 때 한 번)
  실패 형태   ArrayStoreException           컴파일 에러
  비용        저장마다 타입 검사 1회          없다
  유연성      기본으로 제공                  와일드카드로 필요할 때만
```

- **와일드카드는 배열 공변성을 "안전하게 다시 만든 것"**이다.\
  배열이 "전부 허용하고 사고 나면 터뜨린다"면, 와일드카드는 **"위험한 연산만 골라 막는다."**
- `List<? extends Object> l = stringList;` 는 `Object[] a = stringArray;` 와 **같은 유연성**을 준다.\
  차이는 그다음 줄이다 — `l.add(42)` 는 **컴파일 에러**이고 `a[0] = 42` 는 **런타임 예외**다.

비용 — 제네릭 쪽은 런타임 비용이 0이다. 배열은 참조 배열에 값을 넣을 때마다 검사 1회.

### (6) 캡처 — 같은 `?` 라도 서로 다른 것이다

**언제 쓰나** — `List<?>` 안에서 원소를 자리바꿈하려 할 때.

**`javac` 출력 그대로** (`Ex.java (18-f)`, JDK 21.0.5)

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
```

```text
같은 리스트인데 왜 못 넣나

  static void swapFirstTwo(List<?> list)

    list.get(1)   ->  컴파일러가 보기엔 CAP#1  (그런데 식의 정적 타입은 Object 로 올라간다)
    list.set(0, ?) ->  CAP#1 을 요구한다
                       Object 는 CAP#1 이 아니다 -> 막힌다

  두 파라미터면 더 분명하다

  static void mix(List<? extends Number> a, List<? extends Number> b)

    a 의 ?  ->  CAP#1        b 의 ?  ->  CAP#2
    둘 다 "Number 아래 어딘가"지만 같은 타입이라는 보장이 없다
    a 가 List<Integer>, b 가 List<Double> 일 수도 있다
```

**풀어 주는 관용구 — 캡처 헬퍼**

```java
static void swapOk(List<?> list) { swapHelper(list); }      // 여기서 캡처가 T 로 잡힌다
private static <T> void swapHelper(List<T> list) {
    T tmp = list.get(0);
    list.set(0, list.get(1));
    list.set(1, tmp);
}
```

그림 해설 (한 단계씩):

- `?` 는 **쓰일 때마다 새 임시 타입 변수**가 된다. 같은 변수의 두 번 사용도 **각각 캡처**된다.
- **타입 파라미터로 한 번 받으면** 그 이름(`T`)이 고정되어 자유롭게 읽고 쓸 수 있다.
- 이것이 `Collections.swap` 같은 표준 API 가 내부에 `private` 헬퍼를 두는 이유다.
- 판단 규칙: **공개 API 는 와일드카드로 유연하게, 내부 구현은 타입 파라미터로.**

비용 — 없다. 메서드 하나가 더 생기는 것이 대가다.

### (7) 표준 API 가 쓰는 PECS

**언제 쓰나** — "왜 `Collections.max` 의 시그니처가 저렇게 생겼나"를 읽을 때.

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
<R> Stream<R> flatMap(Function<? super T, ? extends Stream<? extends R>> mapper)
void forEach(Consumer<? super T> action)

// java/lang/Iterable.java
default void forEach(Consumer<? super T> action)
```

**출력** (`Ex.java (18-a)`, JDK 21.0.5)

```text
--- 표준 API 가 쓰는 PECS
List<Integer>.sort(Comparator<Number>) = [1, 2, 3]
Collections.copy(List<Object>, List<Integer>) = [1, 2, 3]
Collections.max(List<Integer>) = 3
```

```text
각각이 어느 쪽인가

  Collections.copy(dest, src)
      dest : ? super T    <- 받아 준다 (Consumer)
      src  : ? extends T  <- 꺼내 준다 (Producer)

  list.sort(Comparator<? super E>)
      Comparator 는 E 를 "받아서" 비교한다 -> Consumer -> super
      그래서 List<Integer> 를 Comparator<Number> 로 정렬할 수 있다

  stream.map(Function<? super T, ? extends R>)
      입력 T 는 함수가 받는다  -> Consumer -> super
      출력 R 은 함수가 만든다  -> Producer -> extends
      한 시그니처에 둘이 다 있다
```

그림 해설 (한 단계씩):

- **함수형 인터페이스의 방향**을 읽는 것이 요령이다 — `Consumer<? super T>` 는 T 를 **받으니** super, `Supplier<? extends T>` 는 T 를 **주니** extends.
- `Function<? super T, ? extends R>` 은 **한 타입에 둘이 다 있는** 교과서적 예다.\
  함수형 인터페이스 지도는 [`../31-functional-interfaces/`](../31-functional-interfaces/) 가 정본이다.
- `List<Integer>` 를 `Comparator<Number>` 로 정렬할 수 있는 것이 `? super` 의 실익이다.\
  `Comparator<E>` 였다면 `Comparator<Integer>` 만 받았을 것이다.

비용 — 없다.

### (8) 와일드카드를 쓸 수 없는 자리

**언제 쓰나** — `new ArrayList<?>()` 를 써 보고 막혔을 때.

**`javac` 출력 그대로** (`Ex.java (18-i)`, JDK 21.0.5)

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

선언에 쓰면 파서에서 막힌다.

```text
Ex.java:3: error: <identifier> expected
    static class Box<? extends Number> {}          // (A) 선언에 와일드카드
                     ^
1 error
```

```text
와일드카드가 되는 자리 / 안 되는 자리

  된다                                    안 된다
  +---------------------------------+     +---------------------------------+
  | 변수의 타입                      |     | 클래스·메서드 선언의 타입 파라미터 |
  |   List<?> l;                    |     |   class Box<? extends Number>   |
  | 파라미터의 타입                  |     | new 의 타입 인자                 |
  |   void f(List<? extends T> x)   |     |   new ArrayList<?>()            |
  | 필드의 타입                      |     | 상속 절                          |
  |   Map<String, ? extends Number> |     |   class A implements List<?>    |
  +---------------------------------+     +---------------------------------+
```

그림 해설 (한 단계씩):

- 와일드카드는 **"타입을 쓰는 자리"**에만 온다. **"타입을 선언하는 자리"**에는 못 온다.
- `new` 는 **실제 객체를 만드는 것**이라 원소 타입이 확정돼야 한다. "모르는 타입"으로 만들 수는 없다.
- 그래서 관용구는 `List<?> l = new ArrayList<String>();` 처럼 **만들 때는 확정하고 받을 때만 `?`** 로 둔다.
- `Map<String, ? extends Number> ok = new HashMap<String, Integer>();` 는 **통과한다** — 왼쪽은 타입 사용 자리다.

비용 — 없다.

## 문법 — 형태와 규칙

직접 쓴 최소 예제다. 묻는 것 하나만 남겼다.

### 세 가지 형태

```java
List<?>                 unknown;   // 무제한 — "무엇인지 모른다"
List<? extends Number>  producer;  // 상한 — "Number 이하 어딘가"
List<? super Integer>   consumer;  // 하한 — "Integer 이상 어딘가"
```

- `List<?>` 는 `List<? extends Object>` 의 줄임이다.
- 와일드카드에는 **다중 바운드가 없다.** `? extends A & B` 는 쓸 수 없다(타입 파라미터에서만 된다).
- `? super` 에는 **상한이 없다** — 항상 `Object` 가 상한이다.

### 할 수 있는 것과 없는 것

| | `List<T>` | `List<? extends T>` | `List<? super T>` | `List<?>` |
|---|---|---|---|---|
| `add(t)` | O | **X** | O | **X** |
| `add(null)` | O | O | O | O |
| `T x = get(0)` | O | O | **X** | **X** |
| `Object x = get(0)` | O | O | O | O |
| `size()`·`clear()`·`remove(int)` | O | O | O | O |
| 받을 수 있는 실인자 | `List<T>` 만 | `List<T>` 와 그 하위 | `List<T>` 와 그 상위 | 모든 `List<...>` |

이 표의 모든 칸을 실행·컴파일로 확인했다(`Ex.java (18-a)` `(18-b)` `(18-c)` `(18-d)` `(18-e)`).

### PECS 를 적용하는 절차

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

- **반환 타입에는 와일드카드를 쓰지 않는다.** 호출자가 캡처 문제를 떠안게 된다.
- `Collection<?>` 을 파라미터로 받으면 `contains`·`containsAll` 도 쓸 수 있다 — 그 시그니처가 `Object` 를 받기 때문이다.

## 어디서 틀리나

이 주제의 값어치는 전부 여기 있다.

### 1. 배열로 같은 일을 해서 운영에서 터진다

```text
Exception in thread "main" java.lang.ArrayStoreException: java.lang.Integer
	at Ex.main(Ex.java:7)
```

- `javac` 는 **경고 하나 없이** 통과시킨다.
- 터지는 곳이 유틸 안쪽이면 **스택트레이스가 호출자를 안 가리킨다.**
- 같은 코드를 `List` 로 쓰면 컴파일 에러라 **배포가 안 된다.**
- 정본은 [`../05-arrays/`](../05-arrays/) 다.

### 2. `List<Object>` 를 "아무거나 받는 파라미터"로 쓴다

```text
error: incompatible types: List<String> cannot be converted to List<Object>
```

- `List<Object>` 는 **`List<Object>` 만** 받는다. `List<String>` 도 `List<Integer>` 도 못 받는다.
- 원소 타입을 안 쓸 거면 `List<?>`, 읽을 거면 `List<? extends Object>` 를 쓴다.

### 3. `? extends` 파라미터에 값을 넣으려 한다

```text
error: incompatible types: Integer cannot be converted to CAP#1
  where CAP#1 is a fresh type-variable:
    CAP#1 extends Number from capture of ? extends Number
```

- `CAP#1` 이 나오면 **와일드카드 때문**이라고 읽으면 된다.
- 고치는 법은 둘 — 파라미터를 `? super` 로 바꾸거나, **타입 파라미터 `<T>` 로 받는다.**

### 4. 와일드카드 리스트 안에서 자리바꿈을 한다

```text
Ex.java:6: error: incompatible types: Object cannot be converted to CAP#1
        list.set(0, list.get(1));       // (A) 같은 리스트인데도?
```

- **같은 변수인데도 막힌다.** `?` 는 쓰일 때마다 새로 캡처되기 때문이다.
- `private static <T> void helper(List<T>)` 로 한 번 받아 넘기면 풀린다.

### 5. 반환 타입에 와일드카드를 쓴다

```java
static List<? extends Number> makeNumbers() { return List.of(1, 2); }   // 이렇게 쓰지 마라
```

**`javac` 출력 그대로** (`Ex.java (18-k)`, JDK 21.0.5)

```text
Ex2.java:6: error: incompatible types: int cannot be converted to CAP#1
        got.add(3);                     // 호출자가 받은 리스트에 넣으려 하면
                ^
  where CAP#1 is a fresh type-variable:
    CAP#1 extends Number from capture of ? extends Number
```

- 호출자가 받은 리스트에 **아무것도 못 넣는다.** 유연성을 주는 게 아니라 **호출자를 묶는다.**
- 읽기는 된다 — `Number n = got.get(0);` 은 통과한다(`Ex.java (18-j)` 의 마지막 줄).
- 반환은 `List<Number>` 처럼 **확정 타입**으로 한다.

### 6. `new` 에 와일드카드를 쓴다

```text
error: unexpected type
  required: class or interface without bounds
  found:    ?
```

- 객체는 **실제 원소 타입이 있어야** 만들 수 있다.
- `List<?> l = new ArrayList<String>();` 처럼 **만들 때는 확정, 받을 때만 `?`**.

## 구현 세부사항 대 언어 보장

이 절은 **"어디까지 믿어도 되나"**를 가른다.

| 항목 | 누가 보장하나 | 근거 |
|---|---|---|
| 제네릭이 불공변인 것 | **JLS (언어 보장)** | JLS §4.10.2 — 하위 타입 규칙에 타입 인자 공변이 없다 |
| 배열이 공변인 것 | **JLS (언어 보장)** | JLS §4.10.3 |
| 배열 저장 실패가 `ArrayStoreException` | **JLS (언어 보장)** | JLS §10.10 |
| `? extends` 에 `null` 만 넣을 수 있는 것 | **JLS (언어 보장)** | JLS §5.1.10 캡처 변환의 귀결 |
| `List<?>` 가 모든 `List<...>` 의 상위 타입인 것 | **JLS (언어 보장)** | JLS §4.5.1 포함(containment) 규칙 |
| `Collections.copy` 가 PECS 로 선언된 것 | **javadoc (API 계약)** | `Collections.java` 실파일 |
| `javac` 의 `CAP#1` 표기 | **구현 세부** | 관찰값(17·21·25 동일). 캡처라는 **개념**은 JLS 보장 |
| 에러 메시지 문구 | **구현 세부** | `Some messages have been simplified` 안내가 나오기도 한다 |

### 에러 메시지는 `-Xdiags` 에 따라 달라진다

같은 소스를 `-Xdiags:verbose` 로 다시 컴파일했다(`Ex.java (18-c)`).

```text
Ex.java:5: error: no suitable method found for add(int)
        ext.add(1);                    // (A) Integer 를 넣으면?
           ^
    method List.add(CAP#1) is not applicable
      (argument mismatch; int cannot be converted to CAP#1)
    method List.add(int,CAP#1) is not applicable
      (actual and formal argument lists differ in length)
  where CAP#1 is a fresh type-variable:
    CAP#1 extends Number from capture of ? extends Number
```

- 기본 출력은 **줄여서** 보여 준다(맨 아래 `Some messages have been simplified` 안내가 붙는다).
- 어느 쪽이든 **`CAP#1 ... from capture of ?`** 는 그대로 나온다 — 이것이 읽어야 할 부분이다.
- 외울 것은 문구가 아니라 **"캡처된 타입에는 아무것도 못 넣는다"**는 성질이다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 |
|---|---|
| 파라미터에서 값을 **꺼내기만** 한다 | `Collection<? extends T>` |
| 파라미터에 값을 **넣기만** 한다 | `Collection<? super T>` |
| 꺼내고 또 넣는다 | `Collection<T>` — **와일드카드를 쓰지 마라** |
| 원소 타입을 전혀 안 쓴다 (`size`·`clear`) | `Collection<?>` |
| 반환 타입 | **확정 타입** (`List<Number>`) — 와일드카드 금지 |
| 필드 타입 | 대개 확정 타입. `?` 를 두면 그 객체로 할 수 있는 일이 줄어든다 |
| 비교자·함수를 받는다 | `Comparator<? super E>` · `Function<? super T, ? extends R>` |

| 배열이냐 제네릭이냐 | 판단 |
|---|---|
| 타입 안전이 중요하다 | **제네릭** — 같은 실수를 컴파일에서 잡는다 |
| 기본형 대량 데이터 | 배열 — 박싱이 없다 |
| 공개 API 의 파라미터·반환 | **제네릭** — 배열은 호출자가 고칠 수 있다 |

판단 규칙 두 줄.

- **파라미터마다 "이건 주는 쪽인가 받는 쪽인가"만 물으면 PECS 는 저절로 나온다.**
- **와일드카드는 배열 공변성을 안전하게 다시 만든 것이다** — 유연성은 같고, 사고가 컴파일로 당겨진다.

## 핵심 문장

- 제네릭은 **불공변**이라 `List<String>` 을 `List<Object>` 에 못 넣는다. 그 유연성을 되돌려 주는 것이 **와일드카드**다.
- `? extends` 는 **꺼내기 전용**이다 — 실체가 `List<Integer>` 인지 `List<Double>` 인지 몰라서 **아무것도 못 넣는다**(`null` 만 예외).
- `? super` 는 **넣기 전용**이다 — 실체가 무엇이든 `T` 는 받아 주지만, 꺼낼 때 상한이 `Object` 뿐이라 **`Object` 로만 받는다.**
- **PECS** — 값을 **주는** 파라미터는 `extends`, **받는** 파라미터는 `super`. 둘 다 하면 와일드카드를 쓰지 않는다.
- `List<Object>` 는 **"Object 를 담는 리스트"**이고 `List<?>` 는 **"무엇을 담는지 모르는 리스트"**다 — 받을 수 있는 실인자가 정반대다.
- **배열은 공변이라 런타임에 `ArrayStoreException` 으로 터지고, 제네릭은 불공변이라 컴파일에서 막힌다.** 같은 실수의 검사 시점이 다르다.
- `?` 는 **쓰일 때마다 새로 캡처**된다. 같은 변수의 두 사용도 서로 다른 타입이라 자리바꿈이 막힌다 — `<T>` 헬퍼로 푼다.

## 관련 자료

- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 18번)
- [`../05-arrays/`](../05-arrays/) — **그쪽은 배열 공변성이 `aastore` 로 런타임에 검사되는 경로까지(`javap` 로 `aastore` 대 `iastore`), 여기는 제네릭이 같은 실수를 컴파일에서 막는 대비부터.**\
  `ArrayStoreException` 의 메시지와 발생 조건은 그쪽이 정본이고, **"그래서 `List` 를 쓰라"는 근거**가 여기다
- [`../17-generic-declarations/`](../17-generic-declarations/) — **그쪽은 `<T>` 를 선언하는 자리까지, 여기는 `?` 를 쓰는 자리부터.**\
  `Comparable<? super T>` 바운드가 왜 필요한지는 그쪽 9번, 그 `? super` 가 무엇을 막는지는 여기
- [`../19-type-erasure/`](../19-type-erasure/) — 제네릭이 **런타임 검사를 못 하는 이유**(타입 인자가 지워진다). 그래서 불공변으로 설계할 수밖에 없었다
- [`../31-functional-interfaces/`](../31-functional-interfaces/) — `Function<? super T, ? extends R>` 을 읽는 법. 함수형 인터페이스의 **방향**이 PECS 를 정한다
- [`../45-intermediate-operations/`](../45-intermediate-operations/) — `map`·`filter`·`flatMap` 의 시그니처가 전부 PECS 다. 실사용 예
- [`../46-terminal-operations/`](../46-terminal-operations/) — `forEach(Consumer<? super T>)`·`reduce` 의 와일드카드
- [`../47-collectors-basics/`](../47-collectors-basics/) — `Collector<? super T, A, R>` 의 형태
- [`../28-comparable-comparator/`](../28-comparable-comparator/) — `Comparator<? super E>` 로 정렬이 넓어지는 자리
- 목록의 **40번 주제**(`List.of`·`copyOf`) — `copyOf(Collection<? extends E>)` 가 PECS 를 쓰는 예
- [`../../../../../../history/java/java-5.md`](../../../../../../history/java/java-5.md) — 와일드카드가 **언제·왜 들어왔나**가 정본. 여기는 **어떻게 쓰고 무엇을 못 하나**

## 용어 풀이

- **와일드카드(wildcard)** — 타입 인자 자리의 `?`. "어떤 타입인지 모른다"를 타입으로 적은 것.
- **무제한 와일드카드(unbounded wildcard)** — `?` 만 쓴 것. `? extends Object` 와 같다.
- **상한 와일드카드(upper-bounded wildcard)** — `? extends T`. T 와 그 하위 타입 중 하나를 뜻한다.
- **하한 와일드카드(lower-bounded wildcard)** — `? super T`. T 와 그 상위 타입 중 하나를 뜻한다.
- **PECS** — Producer Extends, Consumer Super. 값을 주는 파라미터는 `extends`, 받는 파라미터는 `super`.
- **불공변(invariant)** — 타입 인자가 다르면 하위 타입 관계가 없는 것. 제네릭이 이쪽이다.
- **공변(covariant)** — 하위 타입 관계가 그대로 이어지는 것. 배열이 이쪽이다(`String[] <: Object[]`).
- **캡처 변환(capture conversion)** — 컴파일러가 `?` 를 그 자리에서만 유효한 임시 타입 변수(`CAP#1`)로 바꾸는 것(JLS §5.1.10).
- **캡처 헬퍼(capture helper)** — 와일드카드 타입을 타입 파라미터로 한 번 받아 넘기는 `private` 메서드. 캡처 제약을 푸는 관용구.
- **`ArrayStoreException`** — 배열의 런타임 원소 타입과 맞지 않는 값을 저장할 때 던져지는 unchecked 예외. 제네릭에는 대응물이 없다.
- **생산자(producer)** — 메서드에 값을 **주는** 쪽. 메서드가 그 컬렉션에서 꺼내 온다.
- **소비자(consumer)** — 메서드에서 값을 **받는** 쪽. 메서드가 그 컬렉션에 넣는다.

## 더 들어가면

- **`? super` 에서도 `Object` 로는 꺼낼 수 있다.** 출력의 `sup.get(0) 을 Object 로 = 1 (실제 클래스 Integer)` 가 그것이다.\
  상한이 항상 `Object` 이기 때문이다. 그래서 "`? super` 에서는 못 꺼낸다"는 말은 정확히는 **"`T` 로는 못 꺼낸다"**다.
- **와일드카드에는 다중 바운드가 없다.** `? extends Comparable & Serializable` 은 **파서에서** 막힌다(`Ex.java (18-k)`).

```text
Ex.java:4: error: > or ',' expected
    static void f(List<? extends Comparable & Serializable> l) { }   // (A) 와일드카드 다중 바운드
                                            ^
```

  필요하면 타입 파라미터로 옮긴다 — `<T extends Comparable<T> & Serializable> void g(List<T> l)` 는 **통과한다.**
- **`Collection<?>` 에도 `contains`·`remove(Object)` 는 쓸 수 있다.**\
  그 시그니처가 `E` 가 아니라 **`Object`** 를 받기 때문이다.

**출력** (`Ex.java (18-j)`, JDK 21.0.5)

```text
contains("a") = true
contains(42)  = false
remove("a")   = true -> [b]
```
 이것은 제네릭 이전과의 호환성 때문에 남은 설계이고,\
  그래서 `list.remove(1)` 과 `list.remove(Integer.valueOf(1))` 이 다르게 동작하는 유명한 함정이 생긴다\
  (그 정본은 목록의 **40번 주제**다).
- **배열과 제네릭을 섞으면 컴파일러가 아예 막는다.** `new List<String>[3]` 은 `generic array creation` 에러다.\
  공변성(배열)과 소거(제네릭)를 합치면 **검사가 아무것도 못 잡는 배열**이 생기기 때문이다.\
  정본은 [`../19-type-erasure/`](../19-type-erasure/) 다.
