# java/syntax/44 — `Stream` 생성: 소스별·기본형 스트림 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력과 원소 개수를 맞힐 수 있는지**를 묻는다.
> 순회·필터 **알고리즘**은 [`cs/algorithm`](../../../../../algorithm/) 의 질문이다. 여기서는 **API 표면과 평가 시점**만 묻는다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 이 세 줄의 `count()` 를 예측하라 (예측)

```java
int[]     ints  = {1, 2, 3};
Integer[] boxed = {1, 2, 3};

Stream.of(ints).count()
Stream.of(boxed).count()
Arrays.stream(ints).count()
```

- 세 줄의 답은 각각 무엇인가?
- 첫 줄의 스트림은 정확히 어떤 타입이고 원소는 무엇인가?
- 왜 `Stream.of(int[])` 만 다르게 동작하는가?
- 컴파일 경고가 나는가?

### 2. 이 코드는 무엇을 출력하는가 (예측)

```java
Stream.of("a", "b").peek(x -> System.out.println("peek " + x));
```

- 몇 줄이 출력되는가?
- 그 이유를 javadoc 의 어느 문장으로 설명할 수 있는가?
- 뒤에 `.toList()` 를 붙이면 몇 줄이 되는가?
- 뒤에 `.count()` 를 붙이면 몇 줄이 되는가?
- `.count()` 의 답이 `.toList()` 와 다르다면 그 근거는 무엇인가?

### 3. 스트림을 두 번 쓰면 (예측)

```java
Stream<String> once = Stream.of("a", "b");
System.out.println(once.count());
System.out.println(once.count());
```

- 첫 줄과 둘째 줄은 각각 무엇을 출력하거나 무엇을 던지는가?
- 예외라면 그 메시지는 무엇인가?
- 같은 원소를 다시 보려면 무엇을 해야 하는가?
- 스트림을 필드나 반환값으로 들고 다니면 왜 위험한가?

### 4. 만든 뒤 소스를 고치면 (예측)

```java
List<String> mut = new ArrayList<>(List.of("a", "b"));
Stream<String> st = mut.stream();
mut.add("c");
System.out.println(st.toList());
```

- 출력은 무엇인가?
- 스트림은 소스를 복사해 두는가?
- 소비가 **시작된 뒤에** 소스를 고치면 무슨 일이 생기며, 그 규칙은 어느 주제가 정본인가?

### 5. 기본형 스트림에만 있는 것 (경계)

```java
int[] nums = {3, 1, 4, 1, 5};
```

- `Arrays.stream(nums).sum()` 은 무엇인가?
- `Stream<Integer>` 에는 왜 `sum()` 이 없는가, 대신 무엇을 쓰는가?
- `IntStream.of().sum()` 과 `IntStream.of().max()` 는 각각 무엇을 돌려주는가?
- 두 답의 형태가 갈리는 이유는 무엇인가?
- `boxed()` 는 내부에서 무엇을 부르는가, 그것이 어느 주제와 이어지는가?

### 6. `"abc".chars()` (예측)

- `"abc".chars().boxed().toList()` 는 무엇을 출력하는가?
- 왜 그런 값이 나오는가?
- `[a, b, c]` 를 얻으려면 무엇을 붙이는가?

### 7. 무한 스트림 (경계)

- `Stream.iterate(1, i -> i * 2)` 의 원소 개수는 몇 개인가?
- `Stream.iterate(1, i -> i * 2).toList()` 를 실행하면 무슨 일이 생기는가?
- `Stream.iterate(1, i -> i < 20, i -> i * 2)` 는 무엇이 다르며 어느 버전부터인가?
- 무한 스트림을 끝낼 수 있는 연산의 종류를 뭐라고 부르는가?
- `sorted()` 를 무한 스트림에 걸면 왜 특히 위험한가?

### 8. 손에 든 것에서 소스를 고르기 (연결)

- `int[]` 를 받았다 — 무엇을 쓰는가?
- 인덱스가 필요한 반복이다 — 무엇을 쓰는가?
- `null` 일 수 있는 값 하나를 스트림으로 잇고 싶다 — 무엇을 쓰는가, 어느 버전부터인가?
- 도중에 검사 예외를 던져야 한다 — 스트림을 쓰는가?
- `Stream.toList()` 와 `collect(Collectors.toList())` 의 결과는 무엇이 다른가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
