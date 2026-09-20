# java/syntax/31 — 함수형 인터페이스: `java.util.function` 지도·`@FunctionalInterface` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **선행** — [`../29-lambda-expressions/`](../29-lambda-expressions/). 람다가 무엇인지 먼저 본다.
> **기준 소스** — 이 머신의 `21.0.5-tem/lib/src.zip` · `25.0.1-tem/lib/src.zip` 에서 **직접 읽은**\
> `java.base/java/util/function/*.java` 43개와 `java/lang/FunctionalInterface.java`, 그리고 `javac` 가 실제로 낸 에러 메시지.
> **실행 검증** — 이 문서의 모든 출력·에러·역어셈블은 Temurin **JDK 21.0.5** 에서 실제로 돌려 얻은 것이다.\
> 프로그램 19개를 **17.0.13 · 21.0.5 · 25.0.1** 세 JDK 에서 각각 돌렸다.\
> 43개 인터페이스 목록은 **리플렉션으로 뽑은 것**이며 세 버전에서 한 글자도 다르지 않았다.
> **버전** — `java.util.function` 의 인터페이스 **43개 전부 `@since 1.8`** 이다(`src.zip` 의 `@since` 를 직접 읽었다).\
> 이 패키지에서 8 이후에 추가된 것은 **메서드 하나뿐** — `Predicate.not` 이 `@since 11` 이다.\
> **17 · 21 · 25 세 `src.zip` 모두** 파일 수가 44개(인터페이스 43 + `package-info`), `@since` 가 전부 `1.8`,
> 그리고 `1.8` 이 아닌 `@since` 는 `Predicate.java:133` 의 `@since 11` 하나뿐이었다.
> **범위** — 이 인터페이스들이 스트림에서 **어떻게 쓰이나**는 [`../44-stream-creation/`](../44-stream-creation/)\
> 과 [`../45-intermediate-operations/`](../45-intermediate-operations/) 가 정본이다.\
> 박싱 **비용이 실제로 얼마인가**는 [`../../언어-특성/README.md`](../../언어-특성/README.md) 의 영역이다(이 문서는 **측정하지 않았다**).\
> 여기는 **이름 규칙으로 골라 쓰는 법과 못 하는 것**이다.
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**`java.util.function` 은 연장통이 아니라 규격 이름표다.**

이름을 읽을 줄 알면 43개를 외울 필요가 없다 — **이름이 곧 시그니처**다.

| 비유 | 실체 |
|---|---|
| 만들어 내기만 하는 기계 — 넣는 구멍이 없다 | `Supplier` — `() -> T` |
| 삼키기만 하는 기계 — 나오는 구멍이 없다 | `Consumer` — `(T) -> void` |
| 넣으면 다른 것이 나오는 기계 | `Function` — `(T) -> R` |
| 넣으면 **같은 종류**가 나오는 기계 | `Operator` — `(T) -> T` |
| 넣으면 합격·불합격만 나오는 검사기 | `Predicate` — `(T) -> boolean` |
| 구멍이 두 개인 기계 | `Bi*` — 인자 2개 |
| 상자에 안 담고 맨것을 다루는 기계 | `Int*`·`Long*`·`Double*` — 기본형 특화 |

```text
                받는 것이 없다        받는 것이 있다
              +-------------------+---------------------------+
  내놓는 것    |   Supplier        |   Function / Operator     |
  이 있다      |   () -> T         |   (T) -> R  /  (T) -> T   |
              +-------------------+---------------------------+
  내놓는 것    |   (Runnable)      |   Consumer                |
  이 없다      |   () -> void      |   (T) -> void             |
              +-------------------+---------------------------+

  내놓는 것이 boolean 이면 Function 이 아니라 Predicate 다.
```

**똑같은 구조로** 이름이 붙어 있다 — `ToIntFunction` 은 「받아서 `int` 를 내놓는 함수」,\
`IntToDoubleFunction` 은 「`int` 를 받아 `double` 을 내놓는 함수」다.

실무에서 이게 값을 내는 자리는 **필요한 시그니처를 말로 옮기는 순간**이다.\
「문자열을 받아 길이를 준다」 → 받는 것 1, 내놓는 것이 `int` → **`ToIntFunction<String>`**.\
직접 인터페이스를 만들기 전에 **이름을 먼저 조립**해 보면 대개 이미 있다.

> **함수형 인터페이스(functional interface)** — 추상 메서드가 **정확히 하나**인 인터페이스. 람다가 들어갈 수 있는 타입.\
> 예: `Supplier<T>` 의 추상 메서드는 `T get()` 하나뿐이다.

> **SAM(single abstract method)** — 그 하나뿐인 추상 메서드. 람다의 본문이 이것의 구현이 된다.\
> 예: `Predicate` 의 SAM 은 `boolean test(T t)` 다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. 필요한 시그니처에서 **표준 인터페이스 이름을 역으로 조립**할 수 있나.
2. 언제 **직접 만들어야** 하나 — 그리고 `@FunctionalInterface` 는 무엇을 검사하나.
3. 표준 인터페이스가 **못 하는 것**은 무엇인가 — 검사 예외·기본형·조합.

## 동작 방식

### (1) 이름 규칙 — 43개는 다섯 축의 조합이다

**언제 쓰나** — 필요한 시그니처는 아는데 타입 이름이 생각나지 않을 때.

**실행 결과** (`Ex.java (31-m)` · 리플렉션으로 뽑은 전체 목록 · 17 · 21 · 25 동일)

```text
Function               apply        (Object) -> Object
BiFunction             apply        (Object, Object) -> Object
Predicate              test         (Object) -> boolean
BiPredicate            test         (Object, Object) -> boolean
Supplier               get          () -> Object
Consumer               accept       (Object) -> void
BiConsumer             accept       (Object, Object) -> void
UnaryOperator          apply        (Object) -> Object
BinaryOperator         apply        (Object, Object) -> Object
BooleanSupplier        getAsBoolean () -> boolean
IntSupplier            getAsInt     () -> int
LongSupplier           getAsLong    () -> long
DoubleSupplier         getAsDouble  () -> double
IntConsumer            accept       (int) -> void
LongConsumer           accept       (long) -> void
DoubleConsumer         accept       (double) -> void
ObjIntConsumer         accept       (Object, int) -> void
ObjLongConsumer        accept       (Object, long) -> void
ObjDoubleConsumer      accept       (Object, double) -> void
IntFunction            apply        (int) -> Object
LongFunction           apply        (long) -> Object
DoubleFunction         apply        (double) -> Object
IntPredicate           test         (int) -> boolean
LongPredicate          test         (long) -> boolean
DoublePredicate        test         (double) -> boolean
IntUnaryOperator       applyAsInt   (int) -> int
LongUnaryOperator      applyAsLong  (long) -> long
DoubleUnaryOperator    applyAsDouble (double) -> double
IntBinaryOperator      applyAsInt   (int, int) -> int
LongBinaryOperator     applyAsLong  (long, long) -> long
DoubleBinaryOperator   applyAsDouble (double, double) -> double
ToIntFunction          applyAsInt   (Object) -> int
ToLongFunction         applyAsLong  (Object) -> long
ToDoubleFunction       applyAsDouble (Object) -> double
ToIntBiFunction        applyAsInt   (Object, Object) -> int
ToLongBiFunction       applyAsLong  (Object, Object) -> long
ToDoubleBiFunction     applyAsDouble (Object, Object) -> double
IntToLongFunction      applyAsLong  (int) -> long
IntToDoubleFunction    applyAsDouble (int) -> double
LongToIntFunction      applyAsInt   (long) -> int
LongToDoubleFunction   applyAsDouble (long) -> double
DoubleToIntFunction    applyAsInt   (double) -> int
DoubleToLongFunction   applyAsLong  (double) -> long
합계 43 개
```

```text
  다섯 축

  1. 무엇을 내놓나   내놓는 것 없음 -> Consumer
                     boolean       -> Predicate
                     그 외          -> Function / Supplier
  2. 몇 개 받나      0개 -> Supplier
                     1개 -> (접두어 없음)
                     2개 -> Bi*
  3. 타입이 같나      받는 것과 내놓는 것이 같은 타입 -> Operator
  4. 기본형인가      받는 쪽이 기본형 -> Int*/Long*/Double*
                     내놓는 쪽이 기본형 -> To<기본형>*
                     양쪽 다 기본형    -> <기본형>To<기본형>*
  5. 섞였나          객체 하나 + 기본형 하나를 삼킨다 -> ObjIntConsumer 류
```

그림 해설 (한 단계씩):

- **메서드 이름도 규칙적이다** — `Function` 은 `apply`, `Predicate` 는 `test`, `Supplier` 는 `get`, `Consumer` 는 `accept`.
- 기본형을 내놓으면 이름이 `applyAs<타입>`·`getAs<타입>` 이 된다.\
  `IntUnaryOperator.applyAsInt` 지 `apply` 가 아니다 — **이름을 잘못 부르는 실수가 여기서 난다.**
- `Runnable` 만 이 패키지 밖에 있다(`java.lang`). 「받는 것도 내놓는 것도 없음」 자리다.
- 축을 알면 **없는 이름도 알아본다** — `ToIntConsumer` 는 없다(`Consumer` 는 내놓지 않으므로 `To` 가 성립하지 않는다).

비용 — 없다. 외울 것은 43개가 아니라 다섯 축이다.

### (2) 이름을 역으로 조립하기

**언제 쓰나** — 인터페이스를 직접 만들려는 순간. 직접 만들기 전에 이것을 먼저 한다.

```text
필요한 시그니처                        조립                                   이름

"String 을 받아 int 를 준다"           받는 것 1 · 내놓는 것 int              ToIntFunction<String>
"아무것도 안 받고 String 을 준다"       받는 것 0 · 내놓는 것 객체              Supplier<String>
"int 를 받아 검사한다"                 받는 것 int · 내놓는 것 boolean         IntPredicate
"String 둘을 받아 String 을 준다"      받는 것 2 · 전부 같은 타입              BinaryOperator<String>
"String 둘을 받아 int 를 준다"         받는 것 2 · 내놓는 것 int              ToIntBiFunction<String,String>
"String 과 int 를 받아 저장한다"        받는 것 2(섞임) · 내놓는 것 없음        ObjIntConsumer<String>
"int 를 받아 String 을 준다"           받는 것 int · 내놓는 것 객체            IntFunction<String>
"int 를 받아 long 을 준다"             받는 것 int · 내놓는 것 long           IntToLongFunction
```

- **말로 옮기고 → 축을 채우고 → 이름을 만든다.** 그 이름이 대개 실제로 있다.
- 없는 자리가 몇 군데 있다 — 예를 들어 **인자 3개짜리는 하나도 없다.**
- `Bi` 까지만 있고 `Tri` 는 없다. 인자가 셋이면 직접 만들거나 인자를 묶는다.

**조립한 이름이 진짜 맞는지 돌려 봤다** (`Ex.java (31-o)` · 17 · 21 · 25 동일)

```text
5 값 true 가나 0 n=3 42
  ObjIntConsumer 7
not(String::isBlank) 로 지우고 남은 것 = [  ]
Comparator 에 람다가 들어가나 = -1
```

- 위 여덟 이름에 각각 람다·메서드 참조를 넣어 전부 컴파일·실행됐다.
- `5` 는 `ToIntFunction<String>` 에 `String::length`, `가나` 는 `BinaryOperator<String>` 에 `String::concat`,\
  `0` 은 `ToIntBiFunction<String,String>` 에 `String::compareTo`("a" 대 "a"), `42` 는 `IntToLongFunction` 이다.
- `Predicate.not(String::isBlank)` 를 `removeIf` 에 넣어 **공백이 아닌 것만 지워졌다** — 남은 것이 `[  ]` 다.
- `Comparator` 에도 람다가 들어갔다(`-1`). **이 패키지 밖에도 함수형 인터페이스가 있다**(「더 들어가면」).

비용 — 직접 만든 인터페이스는 **표준 API 와 안 맞는다.** 스트림·`Optional` 에 못 넣는다.\
그래서 조립을 먼저 해 본다.

### (3) 조합 — `andThen`·`compose`·`negate`·`and`/`or`

**언제 쓰나** — 작은 함수를 이어 붙일 때. 순서가 헷갈릴 때.

**실행 결과** (`Ex.java (31-b)`)

```text
== Function 의 andThen 과 compose — 순서가 뒤집힌다 ==
  plus1.andThen(times2).apply(5) = 12   (먼저 +1, 그 다음 *2)
  plus1.compose(times2).apply(5) = 11   (먼저 *2, 그 다음 +1)

== Predicate 의 and / or / negate ==
  and     ("abcd") = false
  or      ("abcd") = true
  negate  ("abcd") = false
  Predicate.not(...) (11+) = false
  Predicate.isEqual("가") = true

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

```text
  plus1.andThen(times2)                      plus1.compose(times2)

  5 ──plus1──> 6 ──times2──> 12              5 ──times2──> 10 ──plus1──> 11
    앞의 것이 먼저                              뒤의 것이 먼저
    읽는 순서대로                               수학의 합성 순서 (f∘g)
```

그림 해설 (한 단계씩):

- **`andThen` 은 왼쪽부터**, **`compose` 는 오른쪽부터**다. 5로 넣으면 12와 11로 갈린다.
- 헷갈리면 **`andThen` 만 쓴다.** 읽는 순서와 실행 순서가 같다.
- `Predicate` 의 `and`·`or` 는 **단락 평가된다** — `false and ...` 에서 오른쪽이 안 찍혔다.\
  `&&`·`||` 와 같은 동작이다.
- `Consumer.andThen` 은 **둘 다 실행한다.** 단락 평가가 없다 — 돌려줄 값이 없으니 멈출 이유가 없다.
- `Predicate.not(p)` 는 `p.negate()` 와 같은 일을 한다. **`@since 11`** 이며, 메서드 참조에 바로 씌울 수 있어 유용하다\
  (`Predicate.not(String::isBlank)`).

비용 — 조합은 람다 객체를 하나 더 만든다. 파이프라인이 깊어지면 호출이 그만큼 겹친다.

### (4) 있는 조합 메서드와 없는 조합 메서드

**언제 쓰나** — `BiFunction.compose` 를 찾다가 없을 때.

**실행 결과** (`Ex.java (31-b)` · 리플렉션으로 선언 메서드를 찍은 것 · **JDK 21.0.5 기준**)

```text
  BiFunction.andThen 있나 ? 합=3
  Supplier 에는 조합 메서드가 하나도 없다: [public abstract java.lang.Object java.util.function.Supplier.get()]
  Consumer 의 선언 메서드: [accept, andThen, lambda$andThen$0]
  Predicate 의 선언 메서드: [and, isEqual, lambda$and$0, lambda$isEqual$3, lambda$negate$1, lambda$or$2, negate, not, or, test]
  Function 의 선언 메서드: [andThen, apply, compose, identity, lambda$andThen$1, lambda$compose$0, lambda$identity$2]
```

| 인터페이스 | 있는 것 | 없는 것 |
|---|---|---|
| `Function` | `andThen` · `compose` · `identity`(static) | — |
| `UnaryOperator` | `identity`(static) | `compose` 는 `Function` 것을 쓴다 |
| `BiFunction` | `andThen` | **`compose` 가 없다** |
| `Predicate` | `and` · `or` · `negate` · `not`(static, 11+) · `isEqual`(static) | — |
| `Consumer` | `andThen` | — |
| `BiConsumer` | `andThen` | — |
| `Supplier` | **없다** | 조합 메서드가 하나도 없다 |
| 기본형 특화 대부분 | 각자 조금씩 | 객체판보다 적다 |

**컴파일 에러** (`Ex.java (31-h)`)

```text
Ex.java:6: error: cannot find symbol
        System.out.println(bf.compose(n -> n).apply(1, 2));
                             ^
  symbol:   method compose((n)->n)
  location: variable bf of type BiFunction<Integer,Integer,Integer>
1 error
```

- **`BiFunction` 에 `compose` 가 없는 이유**: 앞에 붙일 함수가 인자 **둘**을 내놓아야 하는데, 함수는 값을 하나만 돌려준다.
- `Supplier` 에 조합이 없는 이유: 앞에 붙일 것이 없다(받는 것이 없으므로).\
  뒤에 붙이고 싶으면 `Function` 으로 감싼다.
- **`lambda$andThen$0` 같은 것이 목록에 섞여 있다** — JDK 자신의 `default` 메서드도 람다로 쓰여 있다는 증거다\
  ([`../29-lambda-expressions/`](../29-lambda-expressions/) 「더 들어가면」).

비용 — 없는 조합을 찾느라 시간을 쓴다. **표를 외우지 말고 IDE 자동완성을 믿는다.**

### (5) ★ 기본형 특화 — 박싱이 바이트코드에 보인다

**언제 쓰나** — `Predicate<Integer>` 와 `IntPredicate` 중 무엇을 쓸지 정할 때.

**입력 코드** (`Ex.java (31-c)`)

```java
Predicate<Integer> boxed = n -> n > 0;      // 래퍼를 쓰는 쪽
IntPredicate       prim  = n -> n > 0;      // 기본형 특화

Function<Integer, Integer> fBoxed = n -> n + 1;
IntUnaryOperator           fPrim  = n -> n + 1;
```

**역어셈블** (`javap -c -p Ex.class` · 17 · 21 · 25 에서 명령이 동일)

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

```text
  IntUnaryOperator                           Function<Integer,Integer>

  iload_0                                    aload_0
  iconst_1                                   invokevirtual Integer.intValue   <- 상자를 연다
  iadd                                       iconst_1
  ireturn                                    iadd
                                             invokestatic Integer.valueOf     <- 상자에 담는다
                                             areturn
       |                                          |
  명령 4개                                    명령 6개 + 호출 2번
  상자가 없다                                 원소마다 열고 담는다
```

그림 해설 (한 단계씩):

- 래퍼 쪽에만 **`Integer.intValue()`(언박싱)** 와 **`Integer.valueOf(...)`(박싱)** 가 있다.
- 기본형 쪽은 `iload_0; iconst_1; iadd; ireturn` — **호출이 하나도 없다.**
- `Predicate` 쪽도 마찬가지다. 래퍼판만 `intValue()` 를 한 번 더 부른다.
- 이것이 **왜 기본형 특화가 43개나 되는지**의 답이다 — 원소마다 이 일이 반복되기 때문이다.
- 그래서 스트림도 `IntStream`·`mapToInt`·`boxed()` 를 갖는다.\
  같은 이야기가 [`../44-stream-creation/`](../44-stream-creation/) 과 [`../45-intermediate-operations/`](../45-intermediate-operations/) 에 있다.
- ⚠️ **이 문서는 그 비용이 얼마인지 측정하지 않았다.** 보인 것은 「명령이 더 있다」까지다.\
  실제 비용은 JIT·탈출 분석에 따라 달라진다 — [`../../언어-특성/README.md`](../../언어-특성/README.md) 의 영역이다.

비용 — 기본형 특화는 **박싱을 없앤다.** 대신 타입이 늘어 이름이 복잡해지고, 제네릭이 아니라 조합이 덜 유연하다.

> **박싱(boxing)** — 기본형을 래퍼 객체로 감싸는 것. `Integer.valueOf(1)`.\
> 예: `Function<Integer,Integer>` 에 `int` 를 넣으면 들어갈 때 담기고 나올 때도 담긴다.

> **언박싱(unboxing)** — 래퍼 객체에서 기본형 값을 꺼내는 것. `Integer.intValue()`.\
> 예: 위 바이트코드의 `invokevirtual Integer.intValue` 가 그것이다.

### (6) `@FunctionalInterface` 가 검사하는 것

**언제 쓰나** — 직접 함수형 인터페이스를 만들 때.

**컴파일되는 예** (`Ex.java (31-d4)`)

```java
@FunctionalInterface
interface Mixed {
    String run(String s);                                    // 추상 1개 — 이것이 SAM
    boolean equals(Object o);                                // 안 센다
    String toString();                                       // 안 센다
    default String twice(String s) { return run(run(s)); }   // 안 센다
    static Mixed id() { return s -> s; }                     // 안 센다
}
```

```text
값! / 값!! / 정체
```

```text
  세는 것                                    안 세는 것

  추상 메서드 1개                             default 메서드 (본문이 있다)
       |                                     static 메서드 (구현체가 아니다)
       v                                     private 메서드 (9+)
  이것이 SAM 이다                             Object 의 public 메서드를
                                             재선언한 것
```

그림 해설 (한 단계씩):

- **추상 메서드만 센다.** `default`·`static`·`private` 는 본문이 있으므로 세지 않는다.
- **`Object` 의 public 메서드를 재선언한 것도 안 센다.** 어떤 구현체든 `Object` 에서 물려받기 때문이다.
- 근거는 `FunctionalInterface` javadoc 원문이다(`src.zip`).

  > If an interface declares an abstract method overriding one of the
  > public methods of `java.lang.Object`, that also does *not* count toward
  > the interface's abstract method count since any implementation of the
  > interface will have an implementation from `java.lang.Object` or elsewhere.

- 그래서 `Comparator` 가 `equals(Object)` 를 선언하고도 함수형 인터페이스다.

비용 — 애너테이션 자체는 런타임에 아무 일도 안 한다. **컴파일 시점 검사**일 뿐이다.

## 문법 — 형태와 규칙

직접 쓴 최소 예제다. 출력은 전부 실행 결과다.

### 아홉 개만 먼저 외운다

| 이름 | SAM | 모양 | 무엇을 하나 |
|---|---|---|---|
| `Supplier<T>` | `get()` | `() -> T` | 만들어 낸다 |
| `Consumer<T>` | `accept(T)` | `(T) -> void` | 삼킨다 |
| `Function<T,R>` | `apply(T)` | `(T) -> R` | 바꾼다 |
| `UnaryOperator<T>` | `apply(T)` | `(T) -> T` | 같은 타입으로 바꾼다 |
| `Predicate<T>` | `test(T)` | `(T) -> boolean` | 검사한다 |
| `BiFunction<T,U,R>` | `apply(T,U)` | `(T,U) -> R` | 둘을 받아 바꾼다 |
| `BinaryOperator<T>` | `apply(T,T)` | `(T,T) -> T` | 둘을 합친다 |
| `BiPredicate<T,U>` | `test(T,U)` | `(T,U) -> boolean` | 둘을 보고 검사한다 |
| `BiConsumer<T,U>` | `accept(T,U)` | `(T,U) -> void` | 둘을 삼킨다 |

**실행 결과** (`Ex.java (31-a)`)

```text
Supplier.get()        만들어 낸다
Consumer.accept()     삼킨다: 값
Function.apply()      5
UnaryOperator.apply() ABC
Predicate.test()      true
BiFunction.apply()    1+2
BinaryOperator.apply()3
BiPredicate.test()    true
BiConsumer.accept()   나이=7
```

### `UnaryOperator` 는 `Function` 의 하위 타입이다 — 한 방향으로만

**실행 결과** (`Ex.java (31-a)`)

```text
== UnaryOperator 는 Function 의 하위 타입이다 ==
  UnaryOperator<String> 를 Function<String,String> 자리에 넣을 수 있나 ?
  된다
```

**컴파일 에러** (`Ex.java (31-g)`)

```text
Ex.java:6: error: incompatible types: Function<String,String> cannot be converted to UnaryOperator<String>
        UnaryOperator<String> u = f;          // 반대 방향은 안 된다
                                  ^
1 error
```

```text
  UnaryOperator<String>  ──넣을 수 있다──>  Function<String,String>
  UnaryOperator<String>  <──못 넣는다────   Function<String,String>
```

- `interface UnaryOperator<T> extends Function<T,T>` 이므로 한 방향만 된다.
- **같은 람다는 양쪽 다 된다** — `s -> s.toUpperCase()` 는 어느 타입으로 선언하든 컴파일된다.\
  안 되는 것은 **이미 `Function` 타입인 변수**를 `UnaryOperator` 에 대입하는 것이다.
- 그래서 API 를 만들 때 **받는 쪽을 `Function` 으로 두면 더 넓게 받는다.**

### 정체 함수

**실행 결과** (`Ex.java (31-a)`)

```text
  Function.identity()      그대로
  UnaryOperator.identity() 그대로
  Function.identity() 두 번이 같은 객체인가 ? true
```

- `Function.identity()` 는 `t -> t` 를 돌려준다.
- 두 번 부른 결과가 `==` 로 같았다 — 캡처가 없는 람다이기 때문이다.\
  단 **그 동일성은 보장이 아니다**([`../29-lambda-expressions/`](../29-lambda-expressions/) 8번의 javadoc 인용).
- `Collectors.toMap(Function.identity(), ...)` 처럼 「키는 원소 그대로」를 쓸 때 나온다.

### void 호환 — 값을 돌려주는 식도 `Consumer` 에 들어간다

**실행 결과** (`Ex.java (31-j)`)

```text
  Consumer 로 쓴 list.add -> [가, 나]
  Predicate 로 쓴 list.add -> true / [가, 나, 다]
```

```java
Consumer<String>  c  = s -> list.add(s);   // add 의 boolean 반환값은 버려진다
Consumer<String>  c2 = list::add;          // 메서드 참조도 같다
Predicate<String> p  = list::add;          // 같은 것이 Predicate 도 된다
```

**컴파일 에러** (`Ex.java (31-k)`)

```text
Ex.java:7: error: incompatible types: bad return type in lambda expression
        Consumer<String> bad = s -> { return list.add(s); };
                                                     ^
    unexpected return value
1 error
```

- **식 본문**이면 값을 돌려줘도 된다 — 버려진다.
- **블록 본문**에서 `return 값;` 을 쓰면 에러다. `return;` 은 된다.
- 이 규칙이 「어디서 틀리나」 4번의 오버로드 모호성을 만든다.

## 어디서 틀리나

### 1. `@FunctionalInterface` 를 붙였는데 조건을 어긴다

**추상 메서드 둘** (`Ex.java (31-d1)`)

```text
Ex.java:1: error: Unexpected @FunctionalInterface annotation
@FunctionalInterface
^
  TwoAbstract is not a functional interface
    multiple non-overriding abstract methods found in interface TwoAbstract
1 error
```

**추상 메서드 0개** (`Ex.java (31-d2)`)

```text
Ex.java:1: error: Unexpected @FunctionalInterface annotation
@FunctionalInterface
^
  NoAbstract is not a functional interface
    no abstract method found in interface NoAbstract
1 error
```

**`Object` 의 메서드만 선언** (`Ex.java (31-d3)`)

```text
Ex.java:1: error: Unexpected @FunctionalInterface annotation
@FunctionalInterface
^
  OnlyObjectMethods is not a functional interface
    no abstract method found in interface OnlyObjectMethods
1 error
```

- 세 에러 다 **애너테이션 줄**을 가리킨다. 문제의 메서드가 아니다.
- 셋째가 중요하다 — `equals`·`toString`·`hashCode` 를 셋이나 선언했는데 **「추상 메서드를 못 찾았다」**고 한다.
- 즉 `Object` 의 public 메서드는 **세는 대상이 아니다**((6)의 javadoc 인용).

### 2. `@FunctionalInterface` 를 안 붙이면 괜찮다고 생각한다

**컴파일 에러** (`Ex.java (31-d5)`)

```java
interface TwoAbstract {          // @FunctionalInterface 를 안 붙였다
    String first(String s);
    String second(String s);
}
TwoAbstract t = s -> s;          // 그래도 람다는 못 넣는다
```

```text
Ex.java:8: error: incompatible types: TwoAbstract is not a functional interface
        TwoAbstract t = s -> s;   // 그래도 람다는 못 넣는다
                        ^
    multiple non-overriding abstract methods found in interface TwoAbstract
1 error
```

```text
  @FunctionalInterface 있음                  없음

  선언한 자리에서 에러                        쓰는 자리에서 에러
  "이 인터페이스가 잘못됐다"                  "이 타입에는 람다를 못 넣는다"
       |                                          |
  인터페이스를 고치면 된다                     인터페이스를 바꿔도 되는지
                                             호출자가 알 수 없다
```

- 애너테이션은 **의도를 못 박는 장치**다. 없어도 조건을 만족하면 함수형 인터페이스다.
- 근거는 javadoc 원문이다.

  > However, the compiler will treat any interface meeting the definition of
  > a functional interface as a functional interface regardless of whether or
  > not a `FunctionalInterface` annotation is present on the interface declaration.

- 값은 **에러 나는 시점**에 있다. 붙이면 인터페이스를 고치는 순간 걸리고, 안 붙이면 **쓰던 사람이 나중에** 걸린다.
- 규칙: 람다로 쓰라고 만든 인터페이스에는 **반드시 붙인다.**

### 3. ★ 검사 예외를 던지는 람다를 넣으려 한다

**컴파일 에러** (`Ex.java (31-e1)`)

```text
Ex.java:8: error: unreported exception IOException; must be caught or declared to be thrown
        Function<String, String> read = p -> Files.readString(Path.of(p));   // IOException
                                                             ^
1 error
```

**같은 람다인데 `Supplier` 도 안 된다** (`Ex.java (31-e3)`)

```text
Ex.java:7: error: unreported exception IOException; must be caught or declared to be thrown
        Supplier<String> s = () -> Files.readString(p);   // 같은 람다인데 Supplier 에는 못 들어간다
                                                   ^
1 error
```

- 이유는 단순하다 — **`Function.apply` 도 `Supplier.get` 도 `throws` 를 선언하지 않았다.**
- 람다 본문은 SAM 의 `throws` 목록을 넘어서는 검사 예외를 던질 수 없다.
- **`java.util.function` 의 43개 전부 `throws` 가 없다.** 그래서 이 패키지 전체가 같은 제약을 갖는다.

**통상적 우회 둘** (`Ex.java (31-e2)`)

```java
// 우회 1 — throws 를 선언한 나만의 함수형 인터페이스
@FunctionalInterface
interface ThrowingFunction<T, R> { R apply(T t) throws Exception; }

// 우회 2 — 그것을 표준 Function 으로 감싸는 어댑터
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
== 표준에도 throws 를 선언한 것이 있다 — Callable ==
  Callable.call() = 파일 내용
```

```text
  우회 1만 쓰면                              우회 1 + 우회 2

  내 인터페이스로만 쓸 수 있다                표준 Function 이 되어
  스트림·Optional 에 못 넣는다               stream().map(f) 에 들어간다
       |                                          |
  타입이 격리된다                             검사 예외가 비검사로 바뀐다
                                             (호출자가 안 잡아도 컴파일된다)
```

- **우회 1만으로는 부족하다.** 표준 API 에 못 들어가기 때문이다.
- 우회 2가 실제로 `stream().map(...)` 에 들어갔다 — 출력의 `[파일 내용]` 이 그 증거다.
- **대가**: 검사 예외가 비검사가 되어 **컴파일러의 강제가 사라진다.** 원인은 `getCause()` 로 남는다.
- 표준에도 `throws` 를 선언한 함수형 인터페이스가 있다 — **`java.util.concurrent.Callable`** 이다.\
  `Supplier` 와 모양이 같은데 `call() throws Exception` 이라 같은 람다가 들어간다.\
  다만 `Callable` 은 `java.util.function` 밖에 있고 `ExecutorService` 가 받는 타입이다(목록의 **54번 주제**).
- `IOException` 전용이면 `UncheckedIOException` 이 표준으로 있다.

### 4. 오버로드가 둘 다 함수형 인터페이스를 받는다

**컴파일 에러** (`Ex.java (31-i)`)

```java
static void run(Consumer<String> c) { ... }
static void run(Predicate<String> p) { ... }
run(list::add);
```

```text
Ex.java:10: error: reference to run is ambiguous
        run(list::add);          // add 는 boolean 을 돌려준다 — 둘 다 맞는다
        ^
  both method run(Consumer<String>) in Ex and method run(Predicate<String>) in Ex match
1 error
```

- `List.add` 는 `boolean` 을 돌려주므로 `Predicate` 가 되고, **반환값을 버리면** `Consumer` 도 된다(void 호환).
- 오버로드 둘이 다 맞으면 컴파일러가 고르지 않는다.
- 해결: 캐스트로 못 박거나(`run((Consumer<String>) list::add)`) 이름을 나눈다.
- 규칙: **함수형 인터페이스를 받는 메서드를 오버로드하지 않는다.**
- 같은 사고가 메서드 참조 쪽에서도 난다 — [`../30-method-references/`](../30-method-references/) 「어디서 틀리나」 7번.

### 5. 메서드 이름을 `apply` 로 부른다

- 기본형 특화는 **`applyAsInt`·`applyAsLong`·`applyAsDouble`·`getAsInt`** 같은 이름을 쓴다.
- `IntUnaryOperator` 에 `apply` 는 없다. (1)의 목록이 그 근거다.
- 이유: 소거 때문에 `apply(int)` 와 `apply(Object)` 가 한 타입에 공존하기 어렵고,\
  반환 타입만 다른 오버로드는 애초에 안 되기 때문이다.
- 찾는 요령: **내놓는 것이 기본형이면 `...As<타입>`** 이다.

### 6. 인자 3개짜리를 찾는다

- **없다.** `Bi` 까지만 있다.
- 방법 셋:
  1. 인자를 **`record` 로 묶는다** — 이름이 붙어 오히려 읽기 좋아진다([`../14-records/`](../14-records/)).
  2. **커링** — `Function<A, Function<B, Function<C, R>>>`. 읽기 나쁘다.
  3. 직접 만든다 — `@FunctionalInterface interface TriFunction<A,B,C,R> { R apply(A a, B b, C c); }`.
- 표준 API 에 넣을 일이 없으면 3번이 가장 단순하다.

## 구현 세부사항 대 언어 보장

| 관찰한 것 | 보장인가 | 근거 |
|---|---|---|
| 추상 메서드가 정확히 하나여야 한다 | **보장** | `FunctionalInterface` javadoc — "compilers are required to generate an error message unless ..." |
| `Object` 의 public 메서드는 안 센다 | **보장** | 같은 javadoc 원문 |
| 애너테이션이 없어도 함수형 인터페이스다 | **보장** | 같은 javadoc 원문 |
| 검사 예외를 못 던진다 | **언어 규칙** | 43개 인터페이스 어디에도 `throws` 가 없다(`src.zip` 확인) + 컴파일 에러 |
| 43개 전부 `@since 1.8` | **문서 사실** | 21·25 `src.zip` 의 `@since` 를 직접 읽었다 |
| `Predicate.not` 이 11+ | **문서 사실** | `Predicate.java:133` 의 `@since 11` |
| `Function.identity()` 두 번이 `==` 로 같다 | **보장 아님** | `LambdaMetafactory` javadoc 이 identity 를 부정한다 |
| 래퍼판 람다에 `intValue`/`valueOf` 가 들어간다 | 구현 세부 | javac 가 만든 합성 메서드의 모습이다 |
| JDK 내부 `default` 메서드의 합성 메서드 번호 | 구현 세부 | 아래 실측 참조 |

**실측 — 세 JDK 에서 달랐던 것**

| 무엇 | 17.0.13 | 21.0.5 | 25.0.1 |
|---|---|---|---|
| 43개 인터페이스와 SAM 시그니처 | 같다 | 같다 | 같다 |
| `java.util.function` 파일 수 | 44 (43 + `package-info`) | 44 | 44 |
| 파일 머리의 `@since` | 전부 `1.8` | 전부 `1.8` | 전부 `1.8` |
| `1.8` 이 아닌 `@since` | `Predicate.java:133` 의 `11` 하나 | 같음 | 같음 |
| 조합 메서드 동작·출력 | 같다 | 같다 | 같다 |
| 박싱 바이트코드 명령 | 같다 | 같다 | 같다 (상수 풀 번호만 다름) |
| **JDK 내부 `Predicate` 의 합성 메서드 번호** | `and$0`·`negate$1`·`or$2`·`isEqual$3` | 같음 | **전부 `$0`** |
| **JDK 내부 `Function` 의 합성 메서드 번호** | `compose$0`·`andThen$1`·`identity$2` | 같음 | **`compose$0`·`andThen$0`·`identity$0`** |

- 25 에서 **합성 메서드 번호 매김 규칙이 달라졌다** — 클래스 단위가 아니라 메서드 단위로 센다.
- **이 패키지 자체는 Java 8 이후 사실상 얼어 있다.** 메서드 하나(`Predicate.not`)만 추가됐다.
- ⚠️ 기본형 특화의 **성능 이득은 이 문서가 측정하지 않았다.** 보인 것은 바이트코드 명령 차이뿐이다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 일 | 쓰는 것 |
|---|---|
| 값을 만들어 낸다 (지연 생성·기본값) | `Supplier<T>` |
| 받아서 저장·로깅한다 | `Consumer<T>` |
| 타입을 바꾼다 | `Function<T,R>` |
| 같은 타입으로 바꾼다 | `UnaryOperator<T>` — 의도가 드러난다 |
| 거른다 | `Predicate<T>` |
| 둘을 합친다 (합계·최댓값) | `BinaryOperator<T>` |
| 원소가 많고 숫자다 | **기본형 특화** — `IntPredicate`·`ToIntFunction` 등 |
| 검사 예외를 던져야 한다 | 직접 만든 `Throwing*` + 어댑터, 또는 `Callable` |
| 인자가 셋 이상이다 | `record` 로 묶는다. 안 되면 직접 만든다 |
| 넓게 받는 API 를 만든다 | 파라미터는 `Function`, 반환은 `UnaryOperator` 쪽이 구체적 |
| 함수형 인터페이스를 받는 메서드를 오버로드한다 | **하지 않는다** |

판단 규칙 세 줄.

- **이름을 먼저 조립해 본다.** 「받는 것 N · 내놓는 것 X」를 축에 넣으면 대개 이미 있다.
- **직접 만들기 전에 `@FunctionalInterface` 를 붙인다.** 안 붙이면 에러가 호출자에게 미뤄진다.
- **검사 예외는 경계에서 처리한다.** 람다 안으로 끌고 들어가면 우회 코드가 붙는다.

## 핵심 문장

- 43개는 **다섯 축의 조합**이다 — 내놓는 것 · 받는 개수 · 타입이 같은가 · 기본형인가 · 섞였는가.
- 이름이 곧 시그니처다. **`ToIntFunction` 은 「받아서 `int` 를 내놓는다」**, `IntToLongFunction` 은 「`int` 를 받아 `long` 을 내놓는다」.
- `andThen` 은 **왼쪽부터**, `compose` 는 **오른쪽부터**. `Predicate.and`/`or` 는 단락 평가하고 `Consumer.andThen` 은 안 한다.
- **기본형 특화가 있는 이유는 박싱**이다 — 래퍼판 람다의 바이트코드에만 `Integer.intValue`·`Integer.valueOf` 가 들어 있다.
- `@FunctionalInterface` 는 **추상 메서드만** 센다. `default`·`static`·`private`·`Object` 의 public 메서드는 안 센다.
- **43개 어디에도 `throws` 가 없다.** 검사 예외를 던지는 람다는 못 들어가고, 직접 만든 인터페이스 + 어댑터로 우회한다.

## 관련 자료

- [`../29-lambda-expressions/`](../29-lambda-expressions/) — **이 주제의 선행.** 람다가 무엇으로 컴파일되나, 합성 메서드·캡처의 정본
- [`../30-method-references/`](../30-method-references/) — 이 인터페이스들에 **무엇을 넣나**. 오버로드 모호성이 같이 다뤄지는 곳
- [`../44-stream-creation/`](../44-stream-creation/) — `Stream.generate(Supplier)`·`IntStream` 등 이 타입들이 실제로 쓰이는 자리. **기본형 스트림의 정본**
- [`../45-intermediate-operations/`](../45-intermediate-operations/) — `map(Function)`·`filter(Predicate)`·`mapMulti(BiConsumer)` 의 **연산 계약이 정본**
- [`../01-primitives-and-wrappers/`](../01-primitives-and-wrappers/) — 박싱·`Integer` 캐시의 **값 의미론이 정본**. 여기는 「그래서 어느 인터페이스를 고르나」만
- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 31번)
- [`../../../../../../history/java/java-8.md`](../../../../../../history/java/java-8.md) — 이 패키지가 **왜 그때 들어왔나**. 설계 맥락은 **거기까지**, 여기는 **고르는 법부터**
- [`../../언어-특성/README.md`](../../언어-특성/README.md) — **박싱 비용이 실제로 얼마인가는 거기.** 이 문서는 바이트코드 명령 차이까지만 보였고 **측정하지 않았다**
- [`../14-records/`](../14-records/) — `record`. 인자 3개를 묶는 방법
- [`../25-exceptions/`](../25-exceptions/) — 예외(checked/unchecked). 「어디서 틀리나」 3번의 상위 개념
- [**46번 주제**](../46-terminal-operations/)(최종 연산)·**47·48번 주제**(`Collectors`) — `Supplier`·`BiConsumer`·`BinaryOperator` 가 한꺼번에 나오는 자리
- [**49번 주제**](../49-parallel-streams/)(병렬 스트림) — 기본형 특화와 박싱이 비용으로 드러나는 자리
- 목록의 **54번 주제**(`java.util.concurrent`) — `Callable` 이 받는 쪽의 정본

## 용어 풀이

- **함수형 인터페이스(functional interface)** — 추상 메서드가 정확히 하나인 인터페이스. 람다가 들어갈 수 있는 타입.
- **SAM(single abstract method)** — 그 하나뿐인 추상 메서드. 람다 본문이 이것의 구현이 된다.
- **타깃 타입(target type)** — 람다·메서드 참조가 무슨 타입이 될지 정하는 주변 문맥.
- **박싱(boxing)** — 기본형을 래퍼 객체로 감싸는 것. `Integer.valueOf(1)`.
- **언박싱(unboxing)** — 래퍼에서 기본형 값을 꺼내는 것. `Integer.intValue()`.
- **기본형 특화(primitive specialization)** — 박싱을 피하려고 기본형 전용으로 만든 인터페이스. `IntPredicate` 등.
- **void 호환(void-compatible)** — 값을 돌려주는 식도 반환형이 `void` 인 SAM 에 들어갈 수 있는 것. 값은 버려진다.
- **검사 예외(checked exception)** — 잡거나 `throws` 로 선언해야 컴파일되는 예외. `IOException` 등.
- **단락 평가(short-circuiting)** — 답이 정해지면 나머지를 안 보는 것. `Predicate.and`/`or` 가 그렇다.
- **커링(currying)** — 인자 여럿을 인자 하나짜리 함수의 연쇄로 바꾸는 것. `Function<A, Function<B, R>>`.

## 더 들어가면

- **`Runnable` 은 이 패키지에 없다.** `java.lang` 에 있고 `() -> void` 자리를 맡는다.\
  「받는 것도 내놓는 것도 없음」이라 이름 규칙의 빈칸을 메운다.
- **`Callable` 도 이 패키지 밖이다.** `java.util.concurrent` 에 있고 `V call() throws Exception` 이다.\
  실행 결과에서 `Files::readString` 람다가 `Supplier` 에는 못 들어가고 `Callable` 에는 들어갔다.\
  **모양이 같아도 `throws` 하나로 갈린다.**
- **`Comparator` 도 함수형 인터페이스다.** `java.util` 에 있고 SAM 은 `compare(T,T)` 다.\
  `equals(Object)` 를 선언하고도 함수형인 것이 (6)의 규칙을 보여 주는 표준 예다 — 정본은 [**28번 주제**](../28-comparable-comparator/).
- **`java.util.function` 은 Java 8 이후 거의 안 바뀌었다.** 17 · 21 · 25 세 `src.zip` 에서 파일 수가 전부 44개였고,\
  모든 `@since` 가 `1.8` 이었다. 메서드 단위로 추가된 것은 `Predicate.not`(11) 하나다.
- **JDK 자신의 `default` 메서드도 람다로 쓰여 있다.** 리플렉션 출력에 `lambda$andThen$0` 같은 것이 섞여 나온다.\
  그 이름 붙이기 규칙이 25 에서 달라졌다 — 「구현 세부사항 대 언어 보장」 표 참조.
- **`mapMulti` 가 `BiConsumer<T, Consumer<R>>` 를 받는 이유**도 이 지도로 읽힌다 —\
  「원소 하나와 `sink` 하나를 삼키고 아무것도 안 내놓는다」. 정본은 [`../45-intermediate-operations/`](../45-intermediate-operations/) 다.
