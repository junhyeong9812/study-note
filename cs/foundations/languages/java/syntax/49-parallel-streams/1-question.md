# java/syntax/49 — 병렬 스트림: 값이 나오는 조건 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **선행** — [`../46-terminal-operations/`](../46-terminal-operations/) 의 질문을 먼저 푼다. `forEach`/`forEachOrdered` 와 `reduce` 의 항등원이 전제다.
> 이 주제는 **판단형**이다 — "병렬이 빠른가"가 아니라 **"어떤 조건에서 값이 나오는가"**를 묻는다.
> ⚠️ 수치를 묻는 문항은 **자릿수**만 맞히면 된다. 이 문서의 측정값도 이 머신(24코어)·이 방법의 것이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 어떤 소스가 잘 갈리는가 (예측)

```java
new ArrayList<>(...).spliterator()        // 원소 1024개
new LinkedList<>(...).spliterator()
new HashSet<>(...).spliterator()
Arrays.stream(new int[1024]).spliterator()
Stream.iterate(1, i -> i + 1).spliterator()
```

- 다섯 줄의 `estimateSize()` 는 각각 무엇인가?
- `trySplit()` 후 잘라 낸 쪽의 크기는 각각 무엇인가?
- 어떤 특성 플래그가 있어야 "잘 갈린다"고 말할 수 있는가?
- `LinkedList` 는 `SIZED` 가 붙어 있는데도 왜 잘 안 갈리는가?
- 무한 스트림의 `estimateSize()` 는 무엇인가?

### 2. 병렬이 이득인 경우와 손해인 경우 (예측)

다음 여섯 가지에서 **병렬 / 순차** 배수의 부호(1보다 큰가 작은가)를 예측하라.

```text
(A) int[] 1000만 개 합계
(B) List<Integer> 1000만 개 합계 (박싱)
(C) LinkedList 100만 개 합계
(D) int[] 100개 합계
(E) 2000개인데 원소당 계산이 무거움
(F) Stream.iterate 로 만든 100만 개
```

- 여섯 중 병렬이 이득인 것은 어느 것인가?
- (D)의 배수는 대략 얼마인가?
- (E)가 이득인데 (D)는 손해인 이유를 한 줄로 설명하라.
- 판단 기준이 "원소 수"가 아니라면 무엇인가?
- 이 수치들을 다른 머신에서 그대로 믿어도 되는가?

### 3. 누가 실행하는가 (예측)

```java
IntStream.range(0, 1000).forEach(i -> 스레드이름기록());            // (A)
IntStream.range(0, 1000).parallel().forEach(i -> 스레드이름기록());  // (B)
```

- (A)와 (B)에서 기록되는 스레드 이름은 각각 무엇인가?
- (B)의 스레드 개수는 몇인가?
- `ForkJoinPool.getCommonPoolParallelism()` 은 코어 수와 같은가?
- 호출한 스레드(`main`)도 일을 하는가?

### 4. 공용 풀을 공유한다는 것 (예측)

- 병렬 스트림 둘이 동시에 돌면 무슨 일이 생기는가?
- 다른 스레드가 공용 풀을 쓰는 중일 때 내 작업 시간은 얼마나 달라지는가?
- 이것이 웹 서버에서 왜 특히 위험한가?
- 병렬 스트림 안에서 블로킹 I/O 를 하면 무엇이 막히는가?
- 전용 풀을 쓰려면 어떻게 하며, 그 동작은 계약인가?

### 5. `ArrayList` 에 `forEach` 로 `add` 하면 (예측)

```java
List<Integer> out = new ArrayList<>();
IntStream.range(0, 100_000).parallel().boxed().forEach(out::add);
System.out.println(out.size());
```

- `out.size()` 는 무엇인가?
- 매번 같은 값이 나오는가?
- 예외가 나는가?
- `out` 에 `null` 이 들어갈 수 있는가, 왜인가?
- 순차로 바꾸면 어떻게 되는가?

### 6. 그 사고를 고치는 방법 (연결)

- `collect(toList())` 로 바꾸면 결과가 맞는가?
- `Collections.synchronizedList` 로 감싸면 무엇이 해결되고 무엇이 안 되는가?
- `CopyOnWriteArrayList` 는 왜 이 자리에 부적절한가?
- javadoc 의 어느 문장이 "바깥 상태를 고치지 마라"의 근거인가?

### 7. `reduce` 가 병렬에서 다른 답을 내는 두 경우 (예측)

```java
List<Integer> n = IntStream.rangeClosed(1, 10).boxed().toList();

n.stream().reduce(0, (a, b) -> a - b);           // (A) 순차
n.parallelStream().reduce(0, (a, b) -> a - b);   // (B) 병렬
n.stream().reduce(100, Integer::sum);            // (C) 순차
n.parallelStream().reduce(100, Integer::sum);    // (D) 병렬
```

- 네 줄의 결과는 각각 무엇인가?
- (B)가 (A)와 다른 이유를 한 문장으로 설명하라.
- (D)가 (C)와 다른 이유는 무엇인가?
- 예외나 경고가 나는가?
- (B)를 여러 번 돌리면 같은 값이 나오는가, 그것이 왜 함정인가?

### 8. 순서를 지키는 연산의 값 (예측)

1000만 개 `int[]` 병렬 파이프라인이다.

```text
(A) filter.count
(B) filter.limit(1000).sum
(C) unordered.filter.limit(1000).sum
(D) 순차 distinct.count  vs  병렬 distinct.count
(E) 병렬 forEach  vs  병렬 forEachOrdered  vs  순차 forEach
```

- (B)와 (C)의 차이는 대략 몇 배인가?
- (D)에서 병렬이 순차보다 빠른가?
- (E)의 셋을 빠른 순서로 나열하라.
- 병렬에서 **이득인** 순서 의존 연산도 있는가?

### 9. `findFirst` 와 `findAny` (예측)

```java
IntStream.range(0, 1000).boxed().toList()
         .parallelStream().filter(i -> i % 7 == 3).findFirst();   // (A)
// 같은 파이프라인의 findAny()                                      // (B)
```

- (A)와 (B)의 결과는 각각 무엇인가?
- 순차로 바꾸면 (B)는 무엇인가?
- 어느 쪽이 더 싼가, 왜인가?
- 이 차이가 순차 개발에서 안 드러나는 이유는 무엇인가?

### 10. 병렬에서의 `Collectors` (예측)

```java
Collectors.toList().characteristics()
Collectors.toSet().characteristics()
Collectors.toMap(...).characteristics()
Collectors.groupingBy(...).characteristics()
Collectors.groupingByConcurrent(...).characteristics()
```

- 다섯 줄의 특성 집합은 각각 무엇인가?
- `toMap` 이 `CONCURRENT` 가 아니면 병렬에서 어떻게 도는가?
- 그래서 병렬 `toMap` 의 결과는 순차와 같은가?
- `groupingByConcurrent` 는 무엇을 얻고 무엇을 잃는가?
- javadoc 은 `toMap` 의 병렬 비용을 뭐라고 적고 있는가?

### 11. 병렬에서 중복 키가 나면 (예측)

```java
IntStream.range(0, 200_000).boxed().toList()
         .parallelStream().collect(Collectors.toMap(i -> i % 10, i -> i));
```

- 무엇이 던져지는가?
- 메시지에 나오는 키와 값은 실행마다 같은가?
- 예외가 한 번 더 감싸지는 경우가 있는가?
- 그래서 병렬에서 난 예외를 어떻게 진단해야 하는가?

### 12. `.parallel()` 을 어디에 붙이는가 (경계)

```java
IntStream.range(0, 2000)
         .map(i -> { 스레드이름기록(); return i; })
         .parallel()
         .sum();
```

- `map` 은 몇 개의 스레드에서 도는가?
- `.parallel()` 을 뒤에 붙였는데 왜 그런가?
- `parallel()` 뒤에 `sequential()` 을 부르면 어떻게 되는가?
- 이것이 왜 위험한가?

### 13. 17·21·25 에서 무엇이 갈렸나 (경계)

- 소스별 분할 특성 중 버전에 따라 달라진 것이 있는가?
- 어느 소스에서 무엇이 달랐는가?
- 수집기 특성은 어땠는가?
- 그래서 `estimateSize()` 를 코드에서 써도 되는가?

### 14. 이 코드에 `.parallel()` 을 붙일 것인가 (연결)

각각 판단하고 이유를 한 줄로 적어라.

```text
(A) 웹 요청 핸들러에서 List<Order> 500건을 검증한다
(B) 배치로 CSV 1000만 행을 파싱해 합계를 낸다 (BufferedReader.lines)
(C) 배치로 int[] 1000만 개의 평균을 낸다
(D) 이미지 2000장을 리사이즈한다
(E) List<Long> 100만 개를 DB 에서 조회해 각각 HTTP 호출을 한다
```

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
