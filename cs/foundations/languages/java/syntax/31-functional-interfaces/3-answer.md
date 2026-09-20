# java/syntax/31 — 함수형 인터페이스: `java.util.function` 지도·`@FunctionalInterface` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러·역어셈블은 **Temurin JDK 21.0.5 에서 실제로 돌려 얻은 것**이다.\
> 프로그램 19개를 17.0.13 · 21.0.5 · 25.0.1 에서 각각 돌렸다. **달랐던 것은 12번 답에 모아 두었다.**\
> javadoc 인용과 `@since` 는 각 JDK 의 `lib/src.zip` 원문이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 이름을 조립하라

**답** — 근거는 `Ex.java (31-m)` 이 리플렉션으로 뽑은 43개 목록이다(2번). 아래 SAM 칸은 그 출력에서 그대로 옮겼다.

| 시그니처 | 이름 | SAM |
|---|---|---|
| `String` → `int` | **`ToIntFunction<String>`** | `applyAsInt(Object) -> int` |
| `()` → `String` | **`Supplier<String>`** | `get() -> Object` |
| `int` → `boolean` | **`IntPredicate`** | `test(int) -> boolean` |
| `(String, String)` → `String` | **`BinaryOperator<String>`** | `apply(Object, Object) -> Object` |
| `(String, String)` → `int` | **`ToIntBiFunction<String,String>`** | `applyAsInt(Object, Object) -> int` |
| `(String, int)` → `void` | **`ObjIntConsumer<String>`** | `accept(Object, int) -> void` |
| `int` → `String` | **`IntFunction<String>`** | `apply(int) -> Object` |
| `int` → `long` | **`IntToLongFunction`** | `applyAsLong(int) -> long` |
| 인자 셋 → 하나 | **없다** | — |

**전부 돌려 봤다** (`Ex.java (31-o)` · 17 · 21 · 25 동일)

```text
5 값 true 가나 0 n=3 42
  ObjIntConsumer 7
```

- 여덟 이름에 각각 람다·메서드 참조를 넣어 **전부 컴파일·실행됐다.**
- `5` = `ToIntFunction<String>` + `String::length`, `가나` = `BinaryOperator<String>` + `String::concat`,\
  `0` = `ToIntBiFunction<String,String>` + `String::compareTo`("a" 대 "a"), `42` = `IntToLongFunction`.

**왜 그런가**

- 넷째를 `BiFunction<String,String,String>` 이라 해도 **틀리지 않는다.**\
  다만 셋 다 같은 타입이면 `BinaryOperator` 가 **의도를 더 드러낸다.**
- 다섯째는 반환이 `int` 이므로 `Operator` 가 아니다 — `ToInt...` 가 붙는다.
- 마지막 — **`Bi` 까지만 있다.** 인자 셋은 `record` 로 묶거나 직접 만든다(2-summary 「어디서 틀리나」 6번).

### 2. 이름 규칙의 축은 무엇인가

**`Predicate` 가 되는 조건**

- **내놓는 것이 `boolean`** 일 때. `Function<T,Boolean>` 이 아니라 `Predicate<T>` 를 쓴다.
- 차이는 박싱이다 — `Predicate.test` 는 `boolean` 을 그대로 돌려준다.

**`Operator` 가 되는 조건**

- **받는 것과 내놓는 것의 타입이 같을** 때.
- 인자 1개면 `UnaryOperator<T>`, 2개면 `BinaryOperator<T>`.

**`Bi` 접두어**

- **인자가 2개**라는 뜻이다. `BiFunction`·`BiPredicate`·`BiConsumer`.
- 인자 3개짜리(`Tri`)는 없다.

**`ToInt...` / `IntTo...` / `Int...`**

```text
  Int...        받는 쪽이 기본형      IntPredicate      (int) -> boolean
  ToInt...      내놓는 쪽이 기본형    ToIntFunction     (Object) -> int
  IntTo...      양쪽 다 기본형        IntToLongFunction (int) -> long
```

**`ObjIntConsumer`**

- **객체 하나와 `int` 하나**를 받고 아무것도 안 돌려준다 — `accept(Object, int) -> void`.
- `Obj`+기본형 조합은 `Consumer` 계열에만 있다(`ObjIntConsumer`·`ObjLongConsumer`·`ObjDoubleConsumer`).

**모두 몇 개인가**

- **43개.** 리플렉션 출력의 마지막 줄이 `합계 43 개` 였다.
- `src.zip` 의 파일 수는 44개다 — 43개 + `package-info.java`.
- 17 · 21 · 25 세 JDK 에서 **전부 44개**였다.

### 3. 메서드 이름

**네 기본형의 SAM**

| 인터페이스 | SAM |
|---|---|
| `Function` | `apply` |
| `Predicate` | `test` |
| `Supplier` | `get` |
| `Consumer` | `accept` |

**`IntUnaryOperator` 의 SAM 이 `apply` 인가**

- **아니다.** `applyAsInt` 다. 리플렉션 출력이 그렇게 찍혔다.

```text
IntUnaryOperator       applyAsInt   (int) -> int
DoubleUnaryOperator    applyAsDouble (double) -> double
```

**`IntSupplier` 의 SAM**

- **`getAsInt`** 다. `get` 이 아니다.

```text
BooleanSupplier        getAsBoolean () -> boolean
IntSupplier            getAsInt     () -> int
LongSupplier           getAsLong    () -> long
DoubleSupplier         getAsDouble  () -> double
```

**규칙 한 줄**

> **기본형을 내놓으면 메서드 이름 뒤에 `As<타입>` 이 붙는다.**

- `apply` → `applyAsInt`, `get` → `getAsInt`.
- **받기만 하는 쪽은 안 붙는다** — `IntConsumer.accept`·`IntPredicate.test` 는 그대로다.\
  돌려주는 것이 `void`·`boolean` 이라 구분할 필요가 없기 때문이다.

### 4. `andThen` 과 `compose`

**출력** (`Ex.java (31-b)` · 17 · 21 · 25 동일)

```text
== Function 의 andThen 과 compose — 순서가 뒤집힌다 ==
  plus1.andThen(times2).apply(5) = 12   (먼저 +1, 그 다음 *2)
  plus1.compose(times2).apply(5) = 11   (먼저 *2, 그 다음 +1)

== 단락 평가되나 ==
  false and ...:
    왼쪽 평가됨
  false or  ...:
    왼쪽 평가됨
    오른쪽 평가됨

== Consumer 의 andThen — 둘 다 실행된다 ==
    첫째 값
    둘째 값
```

**왜 그런가**

```text
  plus1.andThen(times2)                      plus1.compose(times2)

  5 ──plus1──> 6 ──times2──> 12              5 ──times2──> 10 ──plus1──> 11
```

**읽는 순서와 실행 순서가 같은 것**

- **`andThen`.** 왼쪽에 쓴 것이 먼저 실행된다.
- `compose` 는 수학의 합성(f∘g) 순서다 — 오른쪽이 먼저.
- **헷갈리면 `andThen` 만 쓴다.**

**`Predicate` 의 `and`/`or`**

- **단락 평가한다.** 출력에서 `false and ...` 일 때 `오른쪽 평가됨` 이 안 나왔다.
- `&&`·`||` 와 같다.

**`Consumer.andThen`**

- **안 한다.** 둘 다 실행됐다.
- 이유: **돌려줄 값이 없어서 멈출 근거가 없다.** `Consumer` 는 부작용을 일으키는 것이 목적이다.

**`Predicate.not(...)`**

- **Java 11** 부터다. `src.zip` 의 `Predicate.java:133` 에 `@since 11` 이 있다.
- 17 · 21 · 25 세 `src.zip` 에서 이것이 **이 패키지의 유일한 `1.8` 아닌 `@since`** 였다.
- 쓸모: `Predicate.not(String::isBlank)` 처럼 **메서드 참조에 바로 씌울 수 있다.**\
  `negate()` 는 `Predicate` 변수가 이미 있어야 한다.
- 실제로 돌려 봤다 (`Ex.java (31-o)`) — `["가", "  ", "나"]` 에 `removeIf(Predicate.not(String::isBlank))` 를 걸어\
  **공백이 아닌 것만 지워지고** `[  ]` 가 남았다.

### 5. 있는 조합 메서드와 없는 것

**출력** (`Ex.java (31-b)` · 리플렉션 · **JDK 21.0.5 기준**)

```text
  BiFunction.andThen 있나 ? 합=3
  Supplier 에는 조합 메서드가 하나도 없다: [public abstract java.lang.Object java.util.function.Supplier.get()]
  Consumer 의 선언 메서드: [accept, andThen, lambda$andThen$0]
  Predicate 의 선언 메서드: [and, isEqual, lambda$and$0, lambda$isEqual$3, lambda$negate$1, lambda$or$2, negate, not, or, test]
  Function 의 선언 메서드: [andThen, apply, compose, identity, lambda$andThen$1, lambda$compose$0, lambda$identity$2]
```

**`BiFunction.compose`**

```text
Ex.java:6: error: cannot find symbol
        System.out.println(bf.compose(n -> n).apply(1, 2));
                             ^
  symbol:   method compose((n)->n)
  location: variable bf of type BiFunction<Integer,Integer,Integer>
1 error
```

- **없다.** `andThen` 만 있다.
- 이유: `compose` 는 **앞에 붙일 함수**를 받는데, `BiFunction` 앞에 붙으려면 **값 둘을 내놓아야** 한다.\
  자바의 함수는 값을 하나만 돌려준다 — 그래서 성립하지 않는다.

**`Supplier` 의 조합 메서드**

- **0개.** 선언 메서드가 `get()` 하나뿐이다.
- 이유: 받는 것이 없어 **앞에 붙일 자리가 없다.**
- 뒤에 붙이고 싶으면 `Function` 으로 감싸거나 `() -> f.apply(s.get())` 을 직접 쓴다.

**`Function` 의 static 메서드**

- **`identity()`** 하나. `t -> t` 를 돌려준다.

**`Predicate` 의 static 메서드 둘**

- **`not(Predicate)`**(11+)와 **`isEqual(Object)`**.
- `isEqual("가").test("가")` 가 `true` 였다 — `Objects.equals` 로 비교하는 술어를 만든다.

**`Function.identity()` 두 번이 `==` 인가**

```text
  Function.identity() 두 번이 같은 객체인가 ? true
```

- 이 실행에서는 **참**이었다. 캡처 없는 람다라 재사용됐다.
- **보장이 아니다.** `LambdaMetafactory` javadoc 이 identity 를 명시적으로 부정한다\
  ([`../29-lambda-expressions/`](../29-lambda-expressions/) 8번에 원문이 있다).
- 그러므로 `f == Function.identity()` 같은 검사로 최적화를 분기하면 안 된다.

**덤** — 위 목록에 `lambda$andThen$0`·`lambda$compose$0` 이 섞여 있다.\
**JDK 자신의 `default` 메서드도 람다로 쓰여 있다**는 증거다([`../29-lambda-expressions/`](../29-lambda-expressions/) 「더 들어가면」).

### 6. 박싱이 바이트코드에 어떻게 보이나

**출력** (`Ex.java (31-c)` · `javap -c -p Ex.class` · 17 · 21 · 25 에서 명령 동일)

```text
  private static int lambda$main$3(int);            <- IntUnaryOperator
    Code:
       0: iload_0
       1: iconst_1
       2: iadd
       3: ireturn

  private static java.lang.Integer lambda$main$2(java.lang.Integer);   <- Function<Integer,Integer>
    Code:
       0: aload_0
       1: invokevirtual #69                 // Method java/lang/Integer.intValue:()I
       4: iconst_1
       5: iadd
       6: invokestatic  #28                 // Method java/lang/Integer.valueOf:(I)Ljava/lang/Integer;
       9: areturn

  private static boolean lambda$main$1(int);        <- IntPredicate
    Code:
       0: iload_0
       1: ifle          8
       4: iconst_1
       5: goto          9
       8: iconst_0
       9: ireturn

  private static boolean lambda$main$0(java.lang.Integer);             <- Predicate<Integer>
    Code:
       0: aload_0
       1: invokevirtual #69                 // Method java/lang/Integer.intValue:()I
       4: ifle          11
       7: iconst_1
       8: goto          12
      11: iconst_0
      12: ireturn
```

**네 시그니처**

| 선언한 타입 | 합성 메서드 시그니처 |
|---|---|
| `Predicate<Integer>` | `boolean lambda$main$0(java.lang.Integer)` |
| `IntPredicate` | `boolean lambda$main$1(int)` |
| `Function<Integer,Integer>` | `java.lang.Integer lambda$main$2(java.lang.Integer)` |
| `IntUnaryOperator` | `int lambda$main$3(int)` |

**래퍼판에만 보이는 호출 둘**

- **`Integer.intValue()`** — 언박싱. 상자를 연다.
- **`Integer.valueOf(int)`** — 박싱. 상자에 담는다.
- `Predicate<Integer>` 쪽은 `intValue()` 만 있다(결과가 `boolean` 이라 담을 일이 없다).
- `Function<Integer,Integer>` 쪽은 **둘 다** 있다 — 열고 다시 담는다.

**`IntUnaryOperator` 쪽 명령 수**

- **네 개.** `iload_0` · `iconst_1` · `iadd` · `ireturn`. **호출이 하나도 없다.**

**기본형 특화가 존재하는 이유와의 연결**

- 그 열고 담기가 **원소마다** 반복된다. 백만 개면 백만 번이다.
- 그래서 `java.util.function` 43개 중 **34개가 기본형 특화**이고, 스트림도 `IntStream`·`mapToInt`·`boxed()` 를 갖는다.
- 같은 이야기가 [`../44-stream-creation/`](../44-stream-creation/) 과 [`../45-intermediate-operations/`](../45-intermediate-operations/) 에 있다.

**성능이 얼마나 차이 나는지 말할 수 있는가**

- **말할 수 없다.** 이 문서는 **측정하지 않았다.**
- 보인 것은 「명령이 더 있고 호출이 둘 더 있다」까지다.
- 실제 비용은 JIT·탈출 분석·`Integer` 캐시에 따라 달라진다.\
  그 영역은 [`../../언어-특성/README.md`](../../언어-특성/README.md) 와 [`../01-primitives-and-wrappers/`](../01-primitives-and-wrappers/) 가 정본이다.

### 7. `@FunctionalInterface` 가 세는 것

**출력** (`Ex.java (31-d4)`)

```text
값! / 값!! / 정체
```

**컴파일되는가**

- **된다.** 그리고 실행도 정상이다.

**세는 것은 몇 개인가**

- **1개** — `String run(String s)` 뿐이다.

```text
  세는 것                                    안 세는 것

  String run(String s)                       default String twice(...)   본문이 있다
                                             static Mixed id()           구현체가 아니다
                                             boolean equals(Object)      Object 것이다
                                             String toString()           Object 것이다
```

**`equals`·`toString` 이 안 세는 근거**

`FunctionalInterface` javadoc 원문(`src.zip`)이다.

> If an interface declares an abstract method overriding one of the
> public methods of `java.lang.Object`, that also does *not* count toward
> the interface's abstract method count since any implementation of the
> interface will have an implementation from `java.lang.Object` or elsewhere.

- 어떤 구현체든 `Object` 에서 그 구현을 물려받기 때문이다.
- 그래서 `Comparator` 가 `equals(Object)` 를 선언하고도 함수형 인터페이스다.

**추상 메서드가 둘이면** (`Ex.java (31-d1)`)

```text
Ex.java:1: error: Unexpected @FunctionalInterface annotation
@FunctionalInterface
^
  TwoAbstract is not a functional interface
    multiple non-overriding abstract methods found in interface TwoAbstract
1 error
```

- **1번째 줄** — 애너테이션 줄을 가리킨다. 문제의 메서드가 아니다.
- 「`multiple non-overriding abstract methods`」 — `non-overriding` 이 중요하다.\
  `Object` 의 것을 재선언한 것은 `overriding` 이라 이 셈에서 빠진다.

**추상 메서드가 0개면** (`Ex.java (31-d2)`·`(31-d3)`)

```text
  NoAbstract is not a functional interface
    no abstract method found in interface NoAbstract
```

```text
  OnlyObjectMethods is not a functional interface
    no abstract method found in interface OnlyObjectMethods
```

- 둘 다 「`no abstract method found`」다.
- 둘째가 특히 좋은 증거다 — `equals`·`toString`·`hashCode` 를 **셋이나 선언했는데** 「못 찾았다」고 한다.

### 8. 애너테이션을 안 붙이면

**넣을 수 있는가**

- **있다.** 애너테이션은 검사 장치일 뿐이다. 근거는 같은 javadoc 원문이다.

  > However, the compiler will treat any interface meeting the definition of
  > a functional interface as a functional interface regardless of whether or
  > not a `FunctionalInterface` annotation is present on the interface declaration.

**추상 메서드가 둘이면** (`Ex.java (31-d5)`)

```text
Ex.java:8: error: incompatible types: TwoAbstract is not a functional interface
        TwoAbstract t = s -> s;   // 그래도 람다는 못 넣는다
                        ^
    multiple non-overriding abstract methods found in interface TwoAbstract
1 error
```

- 인터페이스 선언은 **통과하고**, 람다를 넣는 **8번째 줄**에서 터진다.

**에러 시점의 차이**

```text
  @FunctionalInterface 있음                  없음

  1번째 줄 (인터페이스 선언)                   8번째 줄 (쓰는 자리)
  "이 인터페이스가 잘못됐다"                  "이 타입에는 람다를 못 넣는다"
       |                                          |
  만든 사람이 즉시 안다                        쓰던 사람이 나중에 안다
  고칠 사람이 그 자리에 있다                    고칠 권한이 없을 수도 있다
```

**언제 붙이나**

- **람다로 쓰라고 만든 인터페이스에는 반드시 붙인다.**
- 나중에 누군가 메서드를 하나 더 추가하면 **그 순간 컴파일이 깨져** 막아 준다.
- 안 붙이면 그 추가가 통과하고, **이미 그 타입을 쓰던 모든 호출자 코드**가 깨진다.

### 9. 검사 예외를 던지는 람다

**어느 것이 컴파일되나** (세 줄을 각각 따로 `javac` 에 넣어 본 결과다)

| 타입 | 결과 |
|---|---|
| `Function<String,String>` | 컴파일 에러 |
| `Supplier<String>` | 컴파일 에러 |
| `Callable<String>` | **컴파일된다** — 실행 결과 `Callable.call() = 파일 내용` |

**에러 메시지** (`Ex.java (31-e1)` · `(31-e3)`)

```text
Ex.java:8: error: unreported exception IOException; must be caught or declared to be thrown
        Function<String, String> read = p -> Files.readString(Path.of(p));   // IOException
                                                             ^
1 error
```

```text
Ex.java:7: error: unreported exception IOException; must be caught or declared to be thrown
        Supplier<String> s = () -> Files.readString(p);   // 같은 람다인데 Supplier 에는 못 들어간다
                                                   ^
1 error
```

**근본 이유**

- **`java.util.function` 의 43개 어디에도 `throws` 가 없다.**
- 람다 본문은 SAM 의 `throws` 목록을 넘어서는 검사 예외를 던질 수 없다.
- `Callable.call()` 은 `throws Exception` 이라서 **같은 람다가 들어간다.**\
  실행 결과: `Callable.call() = 파일 내용`.
- 즉 **모양이 같아도 `throws` 하나로 갈린다.**

**통상적 우회 두 단계** (`Ex.java (31-e2)`)

```java
// 1. throws 를 선언한 나만의 함수형 인터페이스
@FunctionalInterface
interface ThrowingFunction<T, R> { R apply(T t) throws Exception; }

// 2. 그것을 표준 Function 으로 감싸는 어댑터
static <T, R> Function<T, R> unchecked(ThrowingFunction<T, R> f) {
    return t -> {
        try { return f.apply(t); }
        catch (RuntimeException e) { throw e; }
        catch (Exception e) { throw new 비검사예외(e); }
    };
}
```

```text
== 우회 1 — 직접 만든 인터페이스 ==
  파일 내용
== 우회 2 — 어댑터로 표준 Function 에 끼우기 ==
  [파일 내용]
== 실패하면 비검사 예외로 바뀌어 나온다 ==
  UncheckedIOException_ <- java.nio.file.NoSuchFileException
```

- **1단계만으로는 부족하다.** 직접 만든 타입은 `stream().map(...)` 에 못 들어간다.
- 2단계를 거친 것이 실제로 `stream().map(f)` 에 들어갔다 — `[파일 내용]` 이 그 증거다.
- `RuntimeException` 을 먼저 잡아 다시 던지는 것은 **이미 비검사인 것을 두 번 감싸지 않기 위해서**다.

**대가**

- **컴파일러의 강제가 사라진다.** 호출자가 안 잡아도 컴파일된다.
- 예외 타입이 바뀌므로 `catch (IOException e)` 가 더 이상 안 잡는다. 원인은 `getCause()` 에만 남는다.
- `IOException` 전용이면 표준 `UncheckedIOException` 을 쓴다 — 적어도 이름이 알려져 있다.
- 검사/비검사의 판단 자체는 [`../25-exceptions/`](../25-exceptions/) 가 정본이다.

### 10. 오버로드와 void 호환

**출력** (`Ex.java (31-i)`)

```text
Ex.java:10: error: reference to run is ambiguous
        run(list::add);          // add 는 boolean 을 돌려준다 — 둘 다 맞는다
        ^
  both method run(Consumer<String>) in Ex and method run(Predicate<String>) in Ex match
1 error
```

**컴파일되는가**

- **안 된다.** 「reference to run is ambiguous」다.

**`Consumer` 도 되는 이유**

- **void 호환** 때문이다. 식 본문의 값은 **버려도 된다.**
- `List.add(E)` 가 `boolean` 을 돌려주므로 `Predicate` 가 되고, 그 값을 버리면 `Consumer` 도 된다.

**블록 본문에서 `return 값;`** (`Ex.java (31-k)`)

```text
Ex.java:7: error: incompatible types: bad return type in lambda expression
        Consumer<String> bad = s -> { return list.add(s); };
                                                     ^
    unexpected return value
1 error
```

- **컴파일 에러다.** 「`unexpected return value`」.

**식 본문과 블록 본문의 차이**

```text
  식 본문                                    블록 본문

  s -> list.add(s)                           s -> { return list.add(s); }
  값이 버려진다 -> Consumer 가 된다            return 에 값이 있다 -> 에러
  s -> list.add(s)                           s -> { list.add(s); }
  (Predicate 도 된다)                         (Consumer 만 된다)
```

- 실행 결과가 둘 다 정상으로 나왔다 — `Consumer 로 쓴 list.add -> [가, 나]`, `Predicate 로 쓴 list.add -> true`.
- 블록 본문에서 `Consumer` 로 쓰려면 `return;` 만 쓰거나 `return` 을 생략한다.

**설계 규칙 한 줄**

> **함수형 인터페이스를 받는 메서드를 오버로드하지 않는다.**

- 고쳐야 한다면 캐스트로 못 박거나(`run((Consumer<String>) list::add)`) 이름을 나눈다.
- 같은 사고가 메서드 참조 쪽에서도 난다 — [`../30-method-references/`](../30-method-references/) 「어디서 틀리나」 7번.

### 11. `UnaryOperator` 와 `Function`

**출력** (`Ex.java (31-a)` · `(31-n)` · 17 · 21 · 25 동일)

```text
Function 으로 선언      : 가능
UnaryOperator 로 선언   : 가능
UnaryOperator -> Function : 된다
```

**`UnaryOperator<String>` 를 `Function<String,String>` 에**

- **넣을 수 있다.** `interface UnaryOperator<T> extends Function<T,T>` 이기 때문이다.

**반대는** (`Ex.java (31-g)`)

```text
Ex.java:6: error: incompatible types: Function<String,String> cannot be converted to UnaryOperator<String>
        UnaryOperator<String> u = f;          // 반대 방향은 안 된다
                                  ^
1 error
```

- **안 된다.** 상위 타입을 하위 타입 변수에 넣는 것이라 거부된다.

**같은 람다는 어느 쪽으로 선언해도 되는가**

- **된다.** `s -> s.toUpperCase()` 를 두 타입으로 각각 선언해 둘 다 `가능` 이 출력됐다.
- 람다는 **타깃 타입에 맞춰 만들어지는 것**이라 그렇다.\
  안 되는 것은 **이미 `Function` 타입이 된 변수**를 옮겨 담는 것이다.

**API 파라미터로 넓게 받는 쪽**

- **`Function<T,T>`.** `UnaryOperator` 도 받을 수 있다.
- 반환 타입으로는 `UnaryOperator` 가 낫다 — 호출자가 더 구체적인 타입을 얻는다.
- 「받는 것은 넓게, 주는 것은 좁게」의 한 사례다.

### 12. 버전과 이 패키지의 변화

**어느 버전부터인가 — 근거**

- **전부 Java 8**이다. `@since 1.8`.
- 근거는 각 JDK 의 **`lib/src.zip` 을 풀어 `java.base/java/util/function/*.java` 의 `@since` 를 직접 읽은 것**이다.\
  기억이 아니라 파일에서 세었다.

**8 이후에 추가된 것**

- **메서드 하나** — `Predicate.not(Predicate)` 가 `Predicate.java:133` 에 `@since 11` 로 있다.
- 인터페이스는 하나도 추가되지 않았다.

**세 JDK 의 파일 수**

| | 17.0.13 | 21.0.5 | 25.0.1 |
|---|---|---|---|
| `java.util.function` 파일 수 | **44** | **44** | **44** |
| 그중 인터페이스 | 43 | 43 | 43 |
| 파일 머리의 `@since` | 전부 `1.8` | 전부 `1.8` | 전부 `1.8` |
| `1.8` 이 아닌 `@since` | `Predicate.java:133` 의 `11` 하나 | 같음 | 같음 |

**세 JDK 에서 달랐던 것**

| 무엇 | 17.0.13 | 21.0.5 | 25.0.1 |
|---|---|---|---|
| 43개 목록·SAM 시그니처 | 같다 | 같다 | 같다 |
| 조합 메서드 동작·출력 | 같다 | 같다 | 같다 |
| 박싱 바이트코드 명령 | 같다 | 같다 | 같다 (상수 풀 번호만 다름) |
| **JDK 내부 `Predicate` 의 합성 메서드 번호** | `and$0`·`negate$1`·`or$2`·`isEqual$3` | 같음 | **전부 `$0`** |
| **JDK 내부 `Function` 의 합성 메서드 번호** | `compose$0`·`andThen$1`·`identity$2` | 같음 | **`compose$0`·`andThen$0`·`identity$0`** |

- 25 에서 **합성 메서드 번호 매김 규칙이 달라졌다** — 클래스 단위가 아니라 메서드 단위로 센다.
- 그 이름은 **구현 세부**다. 기대면 안 된다([`../29-lambda-expressions/`](../29-lambda-expressions/) 11번).

**`Runnable`·`Callable`·`Comparator` 는 이 패키지에 있는가**

- **셋 다 없다.**

| 타입 | 어디에 있나 | SAM |
|---|---|---|
| `Runnable` | `java.lang` | `void run()` |
| `Callable<V>` | `java.util.concurrent` | `V call() throws Exception` |
| `Comparator<T>` | `java.util` | `int compare(T, T)` |

- 셋 다 **8 이전부터 있던 타입**이라 `java.util.function` 에 들어가지 않았다.
- `Runnable` 은 「받는 것도 내놓는 것도 없음」 자리를 메운다.
- `Callable` 은 `Supplier` 와 모양이 같은데 **`throws` 가 있다**(9번).
- `Comparator` 는 `equals(Object)` 를 선언하고도 함수형 인터페이스인 표준 예다(7번). 정본은 [**28번 주제**](../28-comparable-comparator/).

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Ex.java (31-a)` | 아홉 기본 인터페이스의 SAM 호출, `UnaryOperator` → `Function` 대입, `identity()` 의 `==` | 17 · 21 · 25 (동일) |
| `Ex.java (31-b)` | `andThen`/`compose` 순서, `and`/`or` 단락 평가, `Consumer.andThen`, 각 인터페이스의 선언 메서드 목록 | 17 · 21 · 25 (**25 에서 JDK 내부 합성 메서드 번호가 다름**) |
| `Ex.java (31-c)` | 기본형 특화와 래퍼판의 합성 메서드 바이트코드 비교(`intValue`·`valueOf`) | 17 · 21 · 25 (명령 동일, 상수 풀 번호만 다름) |
| `Ex.java (31-d1)`~`(31-d5)` | `@FunctionalInterface` 위반 3종 · 유효한 혼합 선언 · 애너테이션 없는 경우의 에러 시점 | 17 · 21 · 25 (동일) |
| `Ex.java (31-e1)`~`(31-e3)` | 검사 예외 컴파일 에러 2종, 우회 2단계 실제 동작, `Callable` 대비 | 17 · 21 · 25 (동일) |
| `Ex.java (31-g)` | `Function` → `UnaryOperator` 대입 컴파일 에러 | 17 · 21 · 25 (동일) |
| `Ex.java (31-h)` | `BiFunction.compose` 부재 컴파일 에러 | 17 · 21 · 25 (동일) |
| `Ex.java (31-i)` | `Consumer`/`Predicate` 오버로드 모호성 | 17 · 21 · 25 (동일) |
| `Ex.java (31-j)` · `(31-k)` | void 호환(식 본문은 되고 블록 본문의 `return 값` 은 에러) | 17 · 21 · 25 (동일) |
| `Ex.java (31-m)` | 43개 인터페이스의 이름·SAM 이름·시그니처를 리플렉션으로 전수 출력 | 17 · 21 · 25 (**출력이 한 글자도 같음**) |
| `Ex.java (31-n)` | 같은 람다를 `Function`·`UnaryOperator` 양쪽으로 선언해 둘 다 동작 | 17 · 21 · 25 (동일) |
| `Ex.java (31-o)` | 1번 답의 여덟 이름이 실제로 컴파일·실행됨, `Predicate.not(String::isBlank)`, `Comparator` 에 람다 | 17 · 21 · 25 (동일) |
| `src.zip` 열람 (17 · 21 · 25) | `java.util.function` 파일 수 44, 전부 `@since 1.8`, `Predicate.not` 만 `@since 11`, `FunctionalInterface` javadoc | 17 · 21 · 25 |

**구현 의존 항목** — 버전이 오르면 다시 돌려야 하는 것

- JDK 내부 `default` 메서드의 합성 메서드 이름·번호 — 21에서 25로 가며 바뀌었다.
- `Function.identity()` 의 `==` 결과 — javadoc 이 보장을 부정한다.
- 박싱 바이트코드의 상수 풀 번호 — 17과 21에서 달랐다(명령은 같다).
- 기본형 특화의 **성능 이득** — 이 문서는 **측정하지 않았다.** 수치가 필요하면 별도 측정이 필요하다.
- `java.util.function` 의 인터페이스 수 — 새 버전에서 추가될 수 있으므로 `src.zip` 으로 다시 센다.
