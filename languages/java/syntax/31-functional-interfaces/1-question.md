# java/syntax/31 — 함수형 인터페이스: `java.util.function` 지도·`@FunctionalInterface` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **선행** — [`../29-lambda-expressions/`](../29-lambda-expressions/) 의 질문을 먼저 푼다.
> 이 주제는 **지도·선택형**이라 예측형 비율이 낮은 것이 정상이다(작성 규칙 §2-1 규칙 6).
> 대신 **「이름을 조립하라」**(1·2번)와 **「어기면 무엇이 출력되나」**(6~9번)로 인출한다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 이름을 조립하라 (연결)

아래 시그니처에 맞는 **표준 인터페이스 이름**을 대라. 없으면 "없다"라고 답하라.

- `String` 을 받아 `int` 를 준다?
- 아무것도 안 받고 `String` 을 준다?
- `int` 를 받아 합격·불합격을 준다?
- `String` 둘을 받아 `String` 을 준다?
- `String` 둘을 받아 `int` 를 준다?
- `String` 과 `int` 를 받아 아무것도 안 돌려준다?
- `int` 를 받아 `String` 을 준다?
- `int` 를 받아 `long` 을 준다?
- 인자 셋을 받아 하나를 준다?

### 2. 이름 규칙의 축은 무엇인가 (왜)

- `Function` 이 아니라 `Predicate` 가 되는 조건은 무엇인가?
- `Function` 이 아니라 `Operator` 가 되는 조건은 무엇인가?
- `Bi` 접두어는 무엇을 뜻하는가?
- `ToInt...` 와 `IntTo...` 와 `Int...` 는 각각 어디가 기본형인가?
- `ObjIntConsumer` 는 무엇을 받는가?
- `java.util.function` 에 인터페이스가 모두 몇 개인가?

### 3. 메서드 이름 (경계)

- `Function` · `Predicate` · `Supplier` · `Consumer` 의 SAM 이름은 각각 무엇인가?
- `IntUnaryOperator` 의 SAM 이름은 `apply` 인가?
- `IntSupplier` 의 SAM 이름은 무엇인가?
- 기본형을 **내놓는** 인터페이스의 메서드 이름 규칙 한 줄은 무엇인가?

### 4. `andThen` 과 `compose` (예측)

```java
Function<Integer, Integer> plus1  = n -> n + 1;
Function<Integer, Integer> times2 = n -> n * 2;
System.out.println(plus1.andThen(times2).apply(5));
System.out.println(plus1.compose(times2).apply(5));
```

- 두 줄의 출력은 각각 무엇인가?
- 둘 중 읽는 순서와 실행 순서가 같은 것은 무엇인가?
- `Predicate` 의 `and`/`or` 는 단락 평가하는가?
- `Consumer.andThen` 은 단락 평가하는가? 그 이유는?
- `Predicate.not(...)` 은 어느 버전부터인가?

### 5. 있는 조합 메서드와 없는 것 (경계)

- `BiFunction` 에 `compose` 가 있는가? 없다면 그 이유는 무엇인가?
- `Supplier` 에 조합 메서드가 몇 개 있는가?
- `Function` 의 static 메서드는 무엇인가?
- `Predicate` 의 static 메서드 둘은 무엇인가?
- `Function.identity()` 를 두 번 부르면 `==` 가 참인가? 그것은 보장인가?

### 6. ★ 박싱이 바이트코드에 어떻게 보이나 (예측)

```java
Predicate<Integer> boxed = n -> n > 0;
IntPredicate       prim  = n -> n > 0;
Function<Integer, Integer> fBoxed = n -> n + 1;
IntUnaryOperator           fPrim  = n -> n + 1;
```

- `javap -c -p Ex.class` 에서 네 합성 메서드의 시그니처는 각각 무엇인가?
- 래퍼판에만 보이는 호출 두 개는 무엇인가?
- `IntUnaryOperator` 쪽 합성 메서드의 명령은 몇 개인가?
- 이 차이가 기본형 특화가 존재하는 이유와 어떻게 이어지는가?
- 이 관찰로 **성능이 얼마나 차이 나는지** 말할 수 있는가?

### 7. `@FunctionalInterface` 가 세는 것 (경계)

```java
@FunctionalInterface
interface Mixed {
    String run(String s);
    boolean equals(Object o);
    String toString();
    default String twice(String s) { return run(run(s)); }
    static Mixed id() { return s -> s; }
}
```

- 이것은 컴파일되는가?
- 다섯 멤버 중 추상 메서드 수로 세는 것은 몇 개인가?
- `equals`·`toString` 이 안 세는 근거 문장은 무엇인가?
- 추상 메서드를 둘로 늘리면 에러 메시지는 무엇이며 **어느 줄**을 가리키는가?
- 추상 메서드를 0개로 만들면 메시지는 무엇인가?

### 8. 애너테이션을 안 붙이면 (왜)

- `@FunctionalInterface` 없이 추상 메서드가 하나인 인터페이스에 람다를 넣을 수 있는가?
- 추상 메서드가 둘인 인터페이스에 람다를 넣으면 어떤 에러가 나는가?
- 애너테이션이 있을 때와 없을 때 **에러가 나는 시점**이 어떻게 다른가?
- 그래서 언제 붙여야 하는가?

### 9. ★ 검사 예외를 던지는 람다 (예측)

```java
Function<String, String> read = p -> Files.readString(Path.of(p));   // IOException
Supplier<String>         s    = () -> Files.readString(p);
Callable<String>         c    = () -> Files.readString(p);
```

- 세 줄 중 컴파일되는 것은 무엇인가?
- 안 되는 것들의 에러 메시지는 무엇인가?
- 그 근본 이유는 무엇인가 — `java.util.function` 의 43개에 공통으로 없는 것은?
- 통상적 우회 두 단계는 무엇인가?
- 그 우회의 대가는 무엇인가?

### 10. 오버로드와 void 호환 (경계)

```java
static void run(Consumer<String> c) { ... }
static void run(Predicate<String> p) { ... }
run(list::add);
```

- 컴파일되는가? 안 된다면 에러 메시지는 무엇인가?
- `list::add` 가 `Consumer` 도 되는 이유는 무엇인가?
- `Consumer<String> c = s -> { return list.add(s); };` 는 컴파일되는가?
- 식 본문과 블록 본문에서 void 호환 규칙이 어떻게 갈리는가?
- 이 사고를 막는 설계 규칙 한 줄은 무엇인가?

### 11. `UnaryOperator` 와 `Function` (경계)

- `UnaryOperator<String>` 을 `Function<String,String>` 변수에 넣을 수 있는가?
- 반대는 되는가? 에러 메시지는 무엇인가?
- 같은 람다(`s -> s.toUpperCase()`)를 둘 중 어느 타입으로 선언해도 컴파일되는가?
- API 파라미터로는 어느 쪽이 넓게 받는가?

### 12. 버전과 이 패키지의 변화 (연결)

- `java.util.function` 의 인터페이스들은 어느 버전부터인가 — 근거는 어디서 읽었나?
- 8 이후에 이 패키지에 추가된 것은 무엇인가?
- 세 JDK(17·21·25)에서 확인했을 때 파일 수는 각각 몇 개였는가?
- 세 JDK 에서 **달랐던** 것은 무엇인가?
- `Runnable`·`Callable`·`Comparator` 는 이 패키지에 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
