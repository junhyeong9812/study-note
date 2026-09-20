# java/syntax/17 — 제네릭 선언: 타입 파라미터·바운드·제네릭 메서드 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력·에러를 맞힐 수 있는지**를 묻는다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 타입 파라미터의 범위는 어디까지인가 (경계)

```java
static class Box<T> {
    private T value;
    T get() { return value; }
    <U> Box<U> map(Function<? super T, ? extends U> f) { return new Box<>(f.apply(value)); }
}
```

- `T` 와 `U` 는 각각 언제 정해지는가?
- `Box<String> bs` 에 `bs.map(String::length)` 를 하면 결과의 타입은 무엇인가?
- 같은 객체에 `map` 을 두 번 다른 `U` 로 부를 수 있는가?
- 타입 파라미터를 클래스에 둘지 메서드에 둘지는 무엇으로 가르는가?

### 2. `static` 이 클래스 타입 파라미터를 쓰면 (예측)

```java
static class Box<T> {
    private T value;
    static T shared;                       // (A)
    static void putStatic(T t) { }         // (B)
    static T getStatic() { return null; }  // (C)
    T get() { return value; }              // (D)
    static <T> T ownParam(T t) { return t; }   // (E)
}
```

- (A)~(E) 중 어디가 컴파일 에러인가, **메시지 전문**은 무엇인가?
- (E)는 왜 되는가?
- 그 규칙의 이유를 `static` 필드 하나로 실증하려면 어떤 프로그램을 짜겠는가?

### 3. 제네릭 클래스의 `static` 필드는 타입 인자마다 따로인가 (예측)

```java
static class Counter<T> {
    static int created = 0;
    Counter(T value) { created++; }
}
new Counter<String>("a");
new Counter<Integer>(1);
new Counter<List<Double>>(List.of(1.0));
```

- `Counter.created` 는 무엇인가?
- `new Counter<String>("x").getClass() == new Counter<Integer>(1).getClass()` 는 무엇인가?
- 그 클래스의 이름은 무엇인가?

### 4. 바운드가 없으면 무엇을 못 하나 (예측)

```java
static <T> T maxNoBound(List<T> list) {
    T best = list.get(0);
    for (T t : list) if (t.compareTo(best) > 0) best = t;
    return best;
}
```

- 이 코드는 컴파일되는가? 안 된다면 메시지는 무엇인가?
- 바운드 없는 `<T>` 는 무엇과 같은가?
- `<T extends Comparable>` 처럼 로 타입으로 바운드를 주면 어떻게 되는가?

### 5. 바운드를 어기면 (예측)

```java
static class NumberBox<T extends Number> { NumberBox(T v) {} }
NumberBox<String> a = new NumberBox<>("x");   // (A)
NumberBox<int> b = null;                       // (B)
List<int> c = null;                            // (C)
maxOf(List.of(new Object(), new Object()));    // (D) <T extends Comparable<T>> T maxOf(List<T>)
```

- 네 자리에서 각각 어떤 에러가 나는가?
- (A)에서는 **에러가 몇 개** 나는가? 왜인가?
- (B)(C)의 메시지는 왜 `required: reference` 인가?

### 6. 다중 바운드의 규칙 (예측)

```java
static class Multi<T extends Comparable<T> & java.io.Serializable> {}   // (A)
static class BadOrder<T extends Runnable & Object> {}                   // (B)
static class TwoClasses<T extends Number & String> {}                   // (C)
static class SelfExtends<T extends T> {}                                // (D)
static class FinalBound<T extends String> {}                            // (E)
```

- 다섯 중 어디가 컴파일 에러이고 각각 메시지는 무엇인가?
- 클래스와 인터페이스를 섞을 때의 순서 규칙은 무엇인가?
- (E)는 왜 에러가 아닌가? 쓸모가 있는가?

### 7. 이 호출이 컴파일되는가 (예측)

```java
static <T> List<T> listOfTwo(T a, T b) { return new ArrayList<>(List.of(a, b)); }

listOfTwo(1, 2);
listOfTwo("a", "b");
listOfTwo(1, "a");          // (A)
List<String> bad = listOfTwo(1, "a");   // (B)
```

- (A)는 컴파일되는가? `T` 는 무엇으로 추론되는가?
- 그 추론된 타입을 **에러 메시지로 끌어내려면** 어떻게 하는가?
- (B)의 에러 메시지는 무엇인가?
- 추론을 강제로 바꾸려면 어떤 문법을 쓰는가?

### 8. 재귀 바운드는 무엇을 위한 것인가 (왜)

```java
static <T extends Comparable<T>> T maxOf(List<T> list) { ... }
```

- `<T extends Comparable>` 대신 `<T extends Comparable<T>>` 를 쓰는 이유는 무엇인가?
- 이 선언이 어떤 호출을 막아 주는가?
- `Comparable` 계약 자체는 어느 주제가 정본인가?

### 9. `Comparable<T>` 와 `Comparable<? super T>` 는 무엇이 다른가 (경계)

```java
static <T extends Comparable<T>>         T maxStrict(List<T> l) { ... }
static <T extends Comparable<? super T>> T maxSuper(List<T> l)  { ... }

static class Animal implements Comparable<Animal> { public int compareTo(Animal o) { return 0; } }
static class Dog extends Animal {}
```

- `maxStrict(List<Dog>)` 와 `maxSuper(List<Dog>)` 중 어느 쪽이 컴파일되는가?
- 안 되는 쪽의 에러 메시지는 무엇인가?
- `Collections.max` 의 실제 시그니처는 어느 쪽인가?

### 10. 타입 파라미터 가리기와 inner 클래스 (경계)

```java
static class Outer<T> {
    T outerValue;
    <T> void shadow(T t) { }
    class Inner { T fromOuter; }
}
```

- `shadow` 의 `T` 는 바깥 `T` 와 같은 것인가?
- `Inner` 가 바깥 `T` 를 쓸 수 있는 이유는 무엇인가?
- `Inner` 를 `static` 으로 바꾸면 어떻게 되는가?
- `Outer<String>.Inner` 인스턴스는 어떻게 만드는가?

### 11. 다이아몬드와 `var` 가 추론하는 것 (예측)

```java
Map<String, List<Integer>> m = new HashMap<>();
var inferred = new Box<>("var 로 받으면");
var list = new ArrayList<>();
list.add("x");
String s = list.get(0);
```

- 세 줄의 `<>` 는 각각 무엇에서 추론되는가?
- `inferred.get().length()` 는 컴파일되는가?
- 마지막 줄은 컴파일되는가? 안 된다면 메시지는 무엇인가?

### 12. 무엇을 어디에 둘 것인가 (연결)

- 필드가 그 타입을 들고 있어야 한다면 타입 파라미터를 어디에 두는가?
- `static` 유틸 메서드는 어떤가?
- 바운드를 붙일지 말지는 무엇으로 판단하는가?

### 13. 다른 주제와 잇기 (연결)

- `Counter<String>.class == Counter<Integer>.class` 가 참인 이유의 정본은 어느 주제인가?
- `List<int>` 가 안 되는 이유는 어느 주제와 이어지는가?
- 제네릭 메서드 둘을 `List<String>`/`List<Integer>` 로 오버로드할 수 있는가? 그 정본은 어디인가?
- 애너테이션이 제네릭이 될 수 없는 이유는 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
