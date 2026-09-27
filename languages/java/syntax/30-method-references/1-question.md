# java/syntax/30 — 메서드 참조 네 형태 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **선행** — [`../29-lambda-expressions/`](../29-lambda-expressions/) 의 질문을 먼저 푼다. 합성 메서드와 캡처를 모르면 5·9번이 안 풀린다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **함수 타입과 컴파일 여부**를 맞힐 수 있는지를 묻는다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 네 형태를 구분하라 (예측)

```java
static int twice(int n) { return n * 2; }
String greet(String who) { return "안녕 " + who; }
Ex me = new Ex();

// (a) Ex::twice   (b) me::greet   (c) String::length   (d) Ex::greet   (e) ArrayList::new
```

- (a)~(e)는 각각 네 형태 중 무엇인가?
- 각각 어떤 함수형 인터페이스에 들어가는가 — 인자 개수와 타입은?
- (b)와 (d)는 같은 `greet` 을 가리키는데 왜 함수 모양이 다른가?
- `this::m` 과 `super::m` 은 어느 형태인가?

### 2. 같은 `length` 인데 왜 다른가 (예측)

```java
String fixed = "고정된 수신 객체";       // 9자
Supplier<Integer>         bound   = fixed::length;
Function<String, Integer> unbound = String::length;
System.out.println(bound.get() + " / " + unbound.apply("abcde"));
```

- 출력은 무엇인가?
- 두 참조가 받는 인자 개수는 각각 몇 개인가?
- `String::startsWith` 는 어떤 함수형 인터페이스가 되는가?
- `Type::instanceM` 의 함수 모양을 한 줄 규칙으로 말하면?

### 3. `Integer::compare` 와 `Integer::compareTo` (연결)

- 둘 다 `Comparator<Integer>` 에 들어가는가?
- 각각 어느 형태인가?
- `compare` 는 인자가 몇 개이고 `compareTo` 는 몇 개인가 — 그런데 왜 둘 다 비교자가 되는가?
- `String::compareTo` 와 `Comparator.naturalOrder()` 의 정렬 결과는 같은가?

### 4. 배열 생성자 참조 (예측)

```java
IntFunction<int[]>    a = int[]::new;
IntFunction<String[]> b = String[]::new;
IntFunction<int[][]>  c = int[][]::new;
String[] arr = Stream.of("가","나","다").toArray(String[]::new);
Object[] objs = Stream.of("가","나").toArray();
```

- `a.apply(3)`·`b.apply(2)`·`c.apply(2)` 의 출력은 각각 무엇인가?
- 배열 생성자 참조가 받는 인자는 무엇인가?
- `arr` 와 `objs` 의 런타임 타입은 각각 무엇인가?
- `toArray(String[]::new)` 를 쓰는 이유는 무엇인가?

### 5. 컴파일러는 메서드 참조를 무엇으로 바꾸나 (예측)

```java
Function<String, Integer> byRef    = String::length;
Function<String, Integer> byLambda = s -> s.length();
IntFunction<String[]> arrRef       = String[]::new;
Supplier<StringBuilder> ctorRef    = StringBuilder::new;
```

- `javap -p Ex.class` 에 합성 메서드가 몇 개 보이는가?
- 넷 중 어떤 것이 합성 메서드를 만들고 어떤 것이 안 만드는가?
- `BootstrapMethods` 에서 `String::length` 가 가리키는 것은 무엇인가?
- 배열 생성자 참조만 합성 메서드가 생기는 이유는 무엇인가?
- 이 차이가 스택트레이스에 어떻게 나타나는가?

### 6. 어느 것이 컴파일 에러인가 (경계)

```java
// (A) Function<Integer, String> f = Integer::toString;
// (B) Object o = String::length;
// (C) Supplier<List<String>> s = List::new;
// (D) static <T> IntFunction<T[]> maker() { return T[]::new; }
// (E) static String pick(Ex e){...}  String pick(){...}  →  F f = Ex::pick;
```

- 다섯 중 컴파일되는 것이 있는가?
- (A)의 에러 메시지 두 줄은 무엇인가?
- (B)는 왜 에러인가 — 메서드 참조에 없는 것이 무엇인가?
- (C)의 에러 메시지는 무엇을 말하는가?
- (D)가 막히는 이유는 어느 언어 기능 때문인가?
- (E)와 달리 컴파일되는 경우는 어떤 때인가?

### 7. ★ 이 코드는 무엇을 출력하나 (예측)

```java
static String target = null;

target = "처음 값";                                  // 4자
Supplier<Integer> ref = target::length;
target = "훨씬 더 긴 나중 값";                        // 11자
System.out.println(ref.get());
```

- 출력은 무엇인가?
- 그 이유는 무엇인가 — `obj::m` 이 `obj` 를 언제 읽는가?
- 같은 코드를 `() -> target.length()` 로 바꾸면 출력은 무엇인가?
- `target` 이 `null` 인 상태에서 `target::length` 를 쓰면 언제 터지는가?
- 그때 스택트레이스의 맨 위 두 줄은 무엇인가?

### 8. 메서드 참조가 오버로드를 모호하게 만든다 (경계)

```java
static void run(Consumer<String> c) { ... }
static void run(Predicate<String> p) { ... }
run(list::add);
```

- 컴파일되는가?
- 안 된다면 그 이유는 무엇인가 — `List.add` 의 무엇 때문인가?
- 에러 메시지는 무엇인가?
- 고치는 방법 두 가지를 대라.

### 9. 람다로 써야 하는 자리 (연결)

- `s -> s.trim().length()` 를 메서드 참조로 쓸 수 있는가? 왜인가?
- `x -> foo(x, 1)` 은 어떤가?
- `(a, b) -> a + b` 는 어떤가?
- 메서드 참조로 쓸 수 있는 람다의 조건을 한 줄로 말하면?
- 메서드 참조가 **가능한데도** 람다를 써야 하는 자리는 어디인가?

### 10. 세 JDK 에서 무엇이 달랐나 (경계)

- 7번의 실행에서 17·21·25 가 달랐던 줄은 무엇인가?
- 같았던 줄은 무엇인가?
- 그래서 스택트레이스를 어떻게 비교해야 하는가?
- `Objects.requireNonNull` 이 끼어 있는 것은 보장인가 구현 세부인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
