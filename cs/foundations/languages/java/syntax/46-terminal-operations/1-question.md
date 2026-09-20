# java/syntax/46 — 최종 연산과 지연 평가·단락 평가 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **선행** — [`../45-intermediate-operations/`](../45-intermediate-operations/) 의 질문을 먼저 푼다. 원소 단위 통과를 모르면 여기가 안 풀린다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **몇 줄이 출력되고 무엇이 던져지는지**를 맞힐 수 있는지를 묻는다.
> 병렬에서만 달라지는 것은 [`../49-parallel-streams/`](../49-parallel-streams/) 의 질문이다. 여기는 **순차 기준**으로 답한다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 이 두 블록의 출력 줄 수를 예측하라 (예측)

```java
// (A)
Stream.of("a", "b", "c").filter(s -> { System.out.println("  filter " + s); return true; });

// (B)
Stream.of("a", "b", "c").filter(s -> { System.out.println("  filter " + s); return true; }).toList();
```

- (A)는 몇 줄을 출력하는가?
- (A)에서 예외나 경고가 나는가?
- (B)는 몇 줄인가?
- 이 차이를 설명하는 javadoc 문장은 무엇인가?
- 실무에서 이 함정이 드러나는 전형적인 증상은 무엇인가?

### 2. 네 가지 단락 연산의 호출 횟수 (예측)

```java
Stream.of(1, 2, 3, 4, 5).peek(print).anyMatch(i -> i % 2 == 0);
Stream.of(1, 2, 3, 4, 5).peek(print).allMatch(i -> i < 3);
Stream.of(1, 2, 3).peek(print).noneMatch(i -> i == 2);
Stream.of("a", "b", "c").peek(print).findFirst();
```

- 네 줄은 각각 `peek` 를 몇 번 실행하는가?
- `allMatch` 가 멈추는 조건은 무엇인가?
- `noneMatch` 가 멈추는 조건은 무엇인가?
- 단락 평가를 하는 최종 연산을 전부 나열하라.
- 단락 평가는 최종 연산만의 성질인가?

### 3. 빈 스트림에서 무엇이 나오는가 (경계)

- `Stream.empty().anyMatch(i -> true)` 는 무엇인가?
- `Stream.empty().allMatch(i -> false)` 는 무엇인가?
- 그 답을 뭐라고 부르는가?
- `Stream.empty().reduce(0, Integer::sum)` 과 `Stream.empty().reduce(Integer::sum)` 의 반환 타입과 값은 각각 무엇인가?
- `IntStream.empty()` 의 `sum()` 과 `max()` 가 갈리는 이유는 무엇인가?

### 4. 최종 연산이 있는데도 중간 연산이 안 돈다 (예측)

```java
// (A)
Stream.of("a", "b", "c").peek(print).count();

// (B)
Stream.of("a", "b", "c").filter(s -> true).peek(print).count();
```

- (A)는 `peek` 를 몇 번 실행하는가?
- (B)는 몇 번인가?
- 둘 다 `count()` 인데 왜 다른가?
- 이 동작은 언어 보장인가 구현 세부인가?
- 그래서 `peek` 로 디버깅할 때 무엇을 조심해야 하는가?

### 5. 무한 스트림이 끝나는 조건 (예측)

```java
Stream.iterate(1, i -> { System.out.println("  next from " + i); return i * 2; }).limit(4).toList();
```

- `next from` 은 몇 줄 출력되며 결과는 무엇인가?
- 그 횟수가 4가 아닌 이유는 무엇인가?
- 소스가 원소를 밀어내는가, 최종 연산이 당겨 오는가?
- `Stream.iterate(1, i -> i + 1).count()` 를 실행하면 무슨 일이 생기는가?
- `limit` 는 최종 연산인가?

### 6. 스트림을 두 번 건드리면 (예측)

```java
Stream<String> s = Stream.of("a", "b");
Stream<String> a = s.map(String::toUpperCase);
Stream<String> b = s.map(x -> x + "!");
```

- 어느 줄에서 무엇이 던져지는가?
- 최종 연산을 두 번 부르는 것과 같은 예외인가, 다른 예외인가?
- 예외 메시지는 무엇인가?
- 같은 원소를 다시 보려면 무엇을 해야 하는가?
- 스트림을 메서드 반환값으로 돌려줘야 한다면 대신 무엇을 돌려주는가?

### 7. `forEach` 와 `forEachOrdered` (예측)

```java
List<Integer> src = IntStream.rangeClosed(1, 12).boxed().toList();
src.stream().forEach(print);          // (A)
src.stream().forEachOrdered(print);   // (B)
src.parallelStream().forEach(print);          // (C)
src.parallelStream().forEachOrdered(print);   // (D)
```

- (A)와 (B)의 출력 순서는 각각 무엇인가?
- (C)와 (D)는 어떤가?
- 넷 중 **실행마다 달라지는 것**은 어느 것인가?
- 이 둘이 javadoc 에서 특별 취급되는 이유는 무엇인가?
- `forEachOrdered` 가 병렬에서 치르는 대가는 얼마인가?

### 8. 최종 연산이 스트림을 닫는가 (경계)

```java
Stream<String> s = Stream.of("a", "b").onClose(() -> System.out.println("닫혔다"));
s.toList();
```

- `닫혔다` 가 출력되는가?
- 그렇다면/아니라면 언제 출력되는가?
- `Files.lines(path)` 를 닫지 않으면 무슨 일이 생기며, 예외가 나는가?
- 스트림 중 `try`-with-resources 가 필요한 것은 어떤 것인가?

### 9. `iterator()` 는 어느 쪽인가 (경계)

```java
Stream<String> s = Stream.of("a", "b").peek(print);
Iterator<String> it = s.iterator();
```

- `iterator()` 를 부른 직후 `peek` 는 몇 번 실행되었는가?
- 그렇다면 `iterator()` 는 중간 연산인가 최종 연산인가?
- 그 뒤 `s.count()` 를 부르면 무슨 일이 생기는가?
- javadoc 은 이 메서드들을 뭐라고 부르는가?

### 10. 어느 최종 연산을 고르는가 (연결)

- "조건에 맞는 것이 하나라도 있나"를 묻고 싶다 — 무엇을 쓰는가?
- 결과를 나중에 수정해야 한다 — `toList()` 인가 다른 것인가?
- 저장(DB write)을 해야 한다 — 어느 연산에 넣는가, 그 이유는 무엇인가?
- 1억 건에서 조건에 맞는 첫 건만 필요하다 — 어떤 파이프라인을 쓰는가?
- 개수를 세려는데 `map` 안에 로그가 있다 — 무엇을 조심해야 하는가?

### 11. 세 JDK 에서 무엇이 달랐나 (경계)

- 같은 프로그램을 17·21·25 에서 돌렸을 때 달라진 것은 무엇인가?
- 예외 **메시지**는 계약인가?
- 예외 **타입**은 계약인가?
- 그래서 코드에서 예외를 식별할 때 무엇을 기준으로 삼아야 하는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
