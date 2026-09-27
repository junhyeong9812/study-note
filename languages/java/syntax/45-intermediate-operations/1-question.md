# java/syntax/45 — 중간 연산: `map`/`filter`/`flatMap`/`mapMulti` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **선행** — [`../44-stream-creation/`](../44-stream-creation/) 의 질문을 먼저 푼다. 지연 평가를 모르면 여기가 안 풀린다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력의 순서와 횟수를 맞힐 수 있는지**를 묻는다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 출력 순서를 한 줄씩 예측하라 (예측)

```java
Stream.of("apple", "fig", "banana")
      .filter(s -> { System.out.println("  filter " + s); return s.length() > 3; })
      .map(s -> { System.out.println("    map " + s); return s.toUpperCase(); })
      .toList();
```

- 출력은 몇 줄이며 순서는 무엇인가?
- `filter` 세 줄이 먼저 나오고 그 뒤에 `map` 두 줄이 나오는가?
- `fig` 에 대해 `map` 이 출력되지 않는 이유는 무엇인가?
- 이 실행 방식을 뭐라고 부르며, 메모리 측면에서 무엇을 뜻하는가?

### 2. 최종 연산을 `findFirst` 로 바꾸면 (예측)

```java
// 위와 같은 파이프라인, 마지막만 .findFirst()
```

- 출력은 몇 줄이며 무엇인가?
- `banana` 는 처리되는가?
- `Stream.iterate(1, i -> { print(i); return i * 2; }).limit(4).toList()` 에서 람다는 몇 번 불리는가?
- 그 횟수가 4가 아닌 이유는 무엇인가?

### 3. `map` 과 `flatMap` (예측)

```java
List<List<Integer>> nested = List.of(List.of(1, 2), List.of(3), List.of());
```

- `nested.stream().map(List::stream)` 의 타입과 원소 개수는 무엇인가?
- `nested.stream().flatMap(List::stream).toList()` 는 무엇인가?
- 빈 리스트 `List.of()` 는 결과에 어떻게 나타나는가?
- 둘 중 무엇을 쓸지 판단하는 기준 한 줄은 무엇인가?
- `map` 을 잘못 써도 컴파일이 되는 경우는 어떤 때인가?

### 4. `flatMap` 으로 할 수 있는 세 가지 (연결)

- `Stream.of(1,2,3,4).flatMap(i -> i % 2 == 0 ? Stream.of(i) : Stream.empty())` 는 무엇인가?
- 그 코드는 어느 연산과 같은 일을 하는가?
- `List` 에 `null` 원소가 섞여 있을 때 `map(s -> s)` 와 `flatMap(Stream::ofNullable)` 의 결과는 각각 무엇인가?
- 람다가 `null` 을 돌려주면 `flatMap` 은 어떻게 되는가?

### 5. `flatMap` 과 단락 평가 (예측)

```java
List<List<Integer>> nested = List.of(List.of(1, 2, 3), List.of(4, 5));
nested.stream()
      .flatMap(inner -> inner.stream().peek(x -> System.out.println("  안쪽 " + x)))
      .findFirst();
```

- `안쪽` 은 몇 줄 출력되는가?
- 바깥 스트림은 몇 원소를 읽는가?
- `.limit(2)` 로 바꾸면 몇 줄이 되는가?
- 이 동작은 17·21·25 에서 같은가?

### 6. `mapMulti` (경계)

- `mapMulti` 는 어느 버전부터인가?
- `flatMap` 과 결과가 같은데 내부에서 무엇이 다른가?
- `sink.accept(...)` 를 한 번도 안 부르면 그 원소는 어떻게 되는가?
- `Stream.of(1,2).mapMulti((i, sink) -> sink.accept(i*10)).mapToInt(x -> x)` 는 컴파일되는가?
- 안 된다면 에러가 어느 줄에서 나며, 어떻게 고치는가?

### 7. `sorted` 를 끼우면 (예측)

```java
Stream.of(3, 1, 2).map(print).forEach(print);          // (A)
Stream.of(3, 1, 2).map(print).sorted().forEach(print); // (B)
```

- (A)와 (B)의 출력 순서는 각각 무엇인가?
- `sorted` 가 그렇게 만드는 이유는 무엇인가?
- `sorted`·`distinct` 를 무한 스트림에 쓸 수 없는 이유는 무엇인가?
- `Stream.iterate(...).sorted().limit(5)` 를 실행하면 무슨 일이 생기는가?
- `map`·`filter`·`flatMap`·`mapMulti` 는 그 분류에서 어느 쪽인가?

### 8. 연산의 위치가 비용을 바꾼다 (예측)

```java
List<String> src = List.of("apple", "fig", "banana", "kiwi");
// (A) .map(대문자).filter(길이>4)
// (B) .filter(길이>4).map(대문자)
```

- (A)와 (B)의 결과는 같은가?
- `map` 람다는 각각 몇 번 불리는가?
- 이 차이가 테스트에서 안 드러나는 이유는 무엇인가?
- 순서를 못 바꾸는 경우는 어떤 때이며, 그때는 무엇을 하는가?

### 9. 중간 연산에 무엇을 넣지 말아야 하나 (경계)

- `map` 안에서 로그를 찍거나 DB 에 저장하면 무엇이 보장되지 않는가?
- 그 근거가 되는 javadoc 문장은 무엇인가?
- `peek` 는 무엇을 위한 메서드라고 javadoc 이 적고 있는가?
- 원소 개수를 세야 한다면 무엇을 쓰는가?
- `distinct()` 는 무엇에 기대며, 그것이 깨지면 어떻게 되는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
