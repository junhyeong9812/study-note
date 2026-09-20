# java/syntax/18 — 와일드카드와 PECS: `? extends` / `? super` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력·에러를 맞힐 수 있는지**를 묻는다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 이 대입들 중 어디가 막히는가 (예측)

```java
List<String> strings = new ArrayList<>();
List<Object>           objects = strings;      // (A)
List<?>                unknown = strings;      // (B)
List<? extends Object> ext     = strings;      // (C)
```

- 셋 중 어디가 컴파일 에러인가, **메시지 전문**은 무엇인가?
- 제네릭이 불공변이라면 `List<String>` 을 받아 주는 상위 타입은 아예 없는가?
- (B)와 (C)는 무엇이 다른가?

### 2. `? extends` 에 넣으면 (예측)

```java
List<? extends Number> ext = new ArrayList<Integer>();
ext.add(1);                    // (A)
ext.add(Integer.valueOf(1));   // (B)
ext.add(new Object());         // (C)
Number n = ext.get(0);         // (D)
ext.add(null);                 // (E)
```

- 다섯 자리에서 각각 어떻게 되는가?
- 에러 메시지에 나오는 **`CAP#1`** 은 무엇인가?
- (E)만 되는 이유는 무엇인가?

### 3. `? super` 에서 꺼내면 (예측)

```java
List<? super Integer> sup = new ArrayList<Number>();
sup.add(1);                    // (A)
Integer i = sup.get(0);        // (B)
Number  m = sup.get(0);        // (C)
Object  o = sup.get(0);        // (D)
for (Integer x : sup) { }      // (E)
```

- 다섯 자리에서 각각 어떻게 되는가?
- (C)가 안 되는 이유는 무엇인가 — `Number` 창고인데?
- (E)는 왜 (B)와 같은 에러가 나는가?

### 4. 왜 그렇게 되는가 — 규칙의 이유 (왜)

- `? extends Number` 에 아무것도 못 넣는 이유를 **가능한 실체를 나열해서** 설명할 수 있는가?
- `? super Integer` 에서 `Integer` 로 못 꺼내는 이유를 같은 방식으로 설명할 수 있는가?
- 그 두 설명이 **정확히 대칭**인가?

### 5. 와일드카드 없이 copy 를 쓰면 (예측)

```java
static <T> void copyStrict(List<T> src, List<T> dst) { for (T t : src) dst.add(t); }

List<Integer> src = new ArrayList<>(List.of(1, 2));
List<Number>  dst = new ArrayList<>();
copyStrict(src, dst);          // (A)
```

- (A)는 컴파일되는가? 안 된다면 메시지는 무엇인가?
- PECS 를 적용하면 시그니처가 어떻게 되는가?
- 그 시그니처에서 `? extends T` 와 `? super T` 는 각각 어느 파라미터인가?

### 6. `List<Object>` 와 `List<?>` 의 차이 (경계)

- 각각에 `add(42)` 를 하면 어떻게 되는가?
- 각각에 `List<String>` 을 대입할 수 있는가?
- `List<?>` 에서 `size()`·`clear()`·`remove(0)` 는 되는가? 왜인가?
- "아무거나 받는 파라미터"가 필요하면 어느 쪽을 쓰는가?

### 7. 배열과 제네릭의 대비 (예측)

```java
// 배열
String[] strings = new String[3];
Object[] objects = strings;
objects[0] = Integer.valueOf(42);

// 제네릭
List<String> stringList = new ArrayList<>();
List<Object> objectList = stringList;
```

- 배열 쪽은 컴파일되는가? 실행하면 무엇이 나오는가 — **메시지 전문**은?
- 제네릭 쪽은 어디서 막히는가?
- 두 검사의 **시점**이 다른 이유는 무엇인가?
- 와일드카드는 이 대비에서 어느 자리에 있는가?

### 8. 캡처 — 같은 리스트인데 왜 못 옮기나 (예측)

```java
static void swapFirstTwo(List<?> list) {
    Object tmp = list.get(0);
    list.set(0, list.get(1));       // (A)
    list.set(1, tmp);               // (B)
}
static void mix(List<? extends Number> a, List<? extends Number> b) {
    a.set(0, b.get(0));             // (C)
}
```

- (A)(B)(C)는 컴파일되는가? 메시지는 무엇인가?
- 같은 변수의 `get` 과 `set` 인데도 막히는 이유는 무엇인가?
- 이것을 푸는 관용구는 무엇인가?

### 9. 표준 API 의 시그니처를 읽기 (연결)

```java
public static <T> void copy(List<? super T> dest, List<? extends T> src)
default void sort(Comparator<? super E> c)
<R> Stream<R> map(Function<? super T, ? extends R> mapper)
public static <T extends Object & Comparable<? super T>> T max(Collection<? extends T> coll)
```

- 각 와일드카드가 producer 인지 consumer 인지 말할 수 있는가?
- `map` 의 시그니처에 둘이 다 나오는 이유는 무엇인가?
- `List<Integer>` 를 `Comparator<Number>` 로 정렬할 수 있는가? 그 근거는?

### 10. 와일드카드를 쓸 수 없는 자리 (경계)

```java
static class Box<? extends Number> {}                              // (A)
List<?> a = new ArrayList<?>();                                    // (B)
List<? extends Number> b = new ArrayList<? extends Number>();      // (C)
Map<String, ? extends Number> ok = new HashMap<String, Integer>(); // (D)
static void f(List<? extends Comparable & Serializable> l) {}      // (E)
```

- 다섯 중 어디가 컴파일 에러이고 메시지는 무엇인가?
- `new` 에 와일드카드를 못 쓰는 이유는 무엇인가?
- (E)가 필요하면 어떻게 쓰는가?

### 11. 반환 타입에 와일드카드를 쓰면 (예측)

```java
static List<? extends Number> makeNumbers() { return List.of(1, 2); }
List<? extends Number> got = makeNumbers();
Number n = got.get(0);    // (A)
got.add(3);               // (B)
```

- (A)(B)는 각각 어떻게 되는가?
- 그래서 반환 타입에는 무엇을 쓰는 것이 맞는가?

### 12. 어느 것을 고를 것인가 (연결)

- 파라미터가 producer / consumer / 둘 다 / 원소 타입 미사용일 때 각각 무엇을 쓰는가?
- 필드 타입에 와일드카드를 두면 무엇이 불편해지는가?
- `Comparator` 를 받는 파라미터는 왜 항상 `? super` 인가?

### 13. 다른 주제와 잇기 (연결)

- 제네릭이 **런타임 검사를 못 하는** 이유는 어느 주제가 정본인가?
- `ArrayStoreException` 의 발생 조건과 메시지는 어느 주제가 정본인가?
- `new List<String>[3]` 이 왜 금지인가? 공변성과 어떻게 얽히는가?
- `Comparable<? super T>` 바운드가 왜 필요한지는 어느 주제와 이어지는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
