# java/syntax/50 — `Stream` Gatherers (24) — 커스텀 중간 연산 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **선행** — [`../46-terminal-operations/`](../46-terminal-operations/) 의 질문을 먼저 푼다. 지연 평가와 단락 평가를 모르면 5·6번이 안 풀린다.
> 이 주제의 코드는 **JDK 24 이상에서만** 컴파일된다. 1번이 그것을 묻는다.
> 예측형 문항의 출력은 전부 **Temurin JDK 25.0.1** 에서 실제로 돌린 것이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 이 코드를 JDK 21 에서 빌드하면 (예측)

```java
import java.util.stream.Gatherers;
import java.util.stream.Stream;

public class Ex {
    public static void main(String[] args) {
        System.out.println(Stream.of(1, 2, 3, 4, 5).gather(Gatherers.windowFixed(2)).toList());
    }
}
```

- 21 에서 무엇이 일어나는가 — 컴파일 에러인가, 런타임 예외인가?
- 에러 메시지는 무엇이고 **몇 개** 나오는가?
- `Gatherers` 가 `class` 가 아니라 `variable` 로 불리는 줄이 있다 — 왜 그런가?
- `Stream.gather` 메서드는 21 에 있는가?
- 25 에서 같은 코드의 출력은 무엇인가?

### 2. 이 기능은 몇 번부터 정식인가 (경계)

- `src.zip` 의 `@since` 는 무엇이라고 적혀 있는가?
- 그 앞의 두 판에서는 어떤 상태였는가?
- JDK 25 의 `javac` 에 `--release 23` 을 주면 어떤 에러가 나오는가?
- `--release 21` 을 주면 에러 문구가 어떻게 **달라지는가**, 그 차이가 뜻하는 것은 무엇인가?
- JDK 25 에서 `--release 23 --enable-preview` 로 그 시절을 재현할 수 있는가?

### 3. 내장 Gatherer 넷의 출력을 예측하라 (예측)

```java
Stream.of(1,2,3,4,5,6,7,8).gather(Gatherers.windowFixed(3)).toList();
Stream.of(1,2,3,4,5,6,7,8).gather(Gatherers.windowSliding(3)).toList();
Stream.of(1,2,3,4,5).gather(Gatherers.scan(() -> 0, Integer::sum)).toList();
Stream.of(1,2,3,4,5).gather(Gatherers.fold(() -> "", (s, i) -> s + i)).toList();
```

- 네 줄의 출력은 각각 무엇인가?
- `windowSliding(3)` 이 원소 8개에서 창을 **몇 개** 만드는가, 그 수식은 무엇인가?
- `fold` 의 결과가 `15` 가 아니라 리스트인 이유는 무엇인가?
- `scan` 과 `fold` 는 입력 5개에 대해 각각 몇 개를 내놓는가?
- `fold` 뒤에 `map`·`findFirst` 를 더 붙일 수 있는가?

### 4. 빈 스트림과 짧은 창 (경계)

```java
Stream.<Integer>of().gather(Gatherers.windowFixed(3)).toList();
Stream.<Integer>of().gather(Gatherers.scan(() -> 0, Integer::sum)).toList();
Stream.<Integer>of().gather(Gatherers.fold(() -> 0, Integer::sum)).toList();
Stream.of(1,2).gather(Gatherers.windowSliding(5)).toList();
```

- 네 줄의 출력은 각각 무엇인가?
- 셋 중 하나만 원소가 있다 — 어느 것이고 왜인가?
- 원소 7개를 `windowFixed(3)` 에 넣으면 마지막 창은 어떻게 되는가?
- 소비하는 쪽 코드가 여기서 어떻게 깨지는가?
- `Gatherers.windowFixed(0)` 은 **언제** 무엇을 던지는가?

### 5. 단락 평가가 정말 통과하는지 (예측)

```java
List<Integer> seen = new ArrayList<>();
Optional<List<Integer>> first = Stream.of(1,2,3,4,5,6,7,8)
        .peek(seen::add).gather(Gatherers.windowFixed(3)).findFirst();
```

- `first` 와 `seen` 은 각각 무엇인가?
- 같은 일을 `collect(Collectors.groupingBy(i -> (i-1)/3))` 로 하면 `seen` 은 무엇이 되는가?
- 두 결과가 갈리는 이유를 한 문장으로 말하면?
- `gather` 앞에 최종 연산이 하나도 없으면 `seen` 은 무엇인가?
- 무한 스트림에 `gather` 를 거는 것이 가능한 조건은 무엇인가?

### 6. `Collector` 와 `Gatherer` 는 무엇이 다른가 (왜)

- 둘 다 "여러 원소를 하나로 모은다"인데 왜 둘인가?
- `collect(...)` 뒤에 `map` 을 붙이려면 무엇을 해야 하는가?
- `gather(...)` 뒤에는 무엇을 붙일 수 있는가?
- 한 파이프라인에 `gather` 와 `collect` 를 같이 쓸 수 있는가?
- "뒤에 더 붙일 연산이 없다"면 둘 중 무엇을 고르는가?

### 7. 이 Gatherer 의 출력을 예측하라 (예측)

```java
static <T> Gatherer<T, ?, T> dedupeAdjacent() {
    return Gatherer.ofSequential(
            () -> new Object() { T prev = null; boolean started = false; },
            Gatherer.Integrator.ofGreedy((state, element, downstream) -> {
                if (!state.started || !Objects.equals(state.prev, element)) {
                    state.started = true;
                    state.prev = element;
                    return downstream.push(element);
                }
                return true;
            })
    );
}
// 입력 ["a","a","b","b","b","a","c","c"]
```

- `gather(dedupeAdjacent())` 의 결과는 무엇인가?
- 같은 입력에 `distinct()` 를 쓰면 무엇이 나오는가?
- 두 결과가 갈리는 이유는 무엇인가?
- `return true;` 를 `return downstream.push(element);` 로 바꾸면 무엇이 달라지는가?
- 이 변환을 `map` 이나 `filter` 로 쓸 수 없는 이유는 무엇인가?

### 8. `integrate` 의 반환값은 무슨 뜻인가 (왜)

```java
Gatherer.Integrator.of((state, element, downstream) -> {
    boolean more = downstream.push(element);
    return more && !stop.test(element);
});
```

- `integrate` 가 `false` 를 돌려주면 무슨 일이 생기는가?
- `downstream.push(...)` 가 돌려주는 `boolean` 은 무슨 뜻인가?
- `Integrator.of` 와 `Integrator.ofGreedy` 의 차이는 무엇인가?
- `ofGreedy` 로 선언해 놓고 `false` 를 돌려주면 어떻게 되는가?
- 이 Gatherer 와 `takeWhile` 의 결과는 무엇이 다른가?

### 9. Gatherer 의 네 함수 (연결)

- 네 함수의 이름과 각각의 역할은 무엇인가?
- 그중 **필수**인 것은 무엇인가?
- `combiner` 를 안 주면 무엇이 달라지는가?
- `ofSequential` 로 만든 Gatherer 를 `parallelStream()` 에 걸면 예외가 나는가?
- `finisher` 가 있는 Gatherer 의 출력 원소 수는 입력과 어떤 관계인가?

### 10. 창이 돌려준 리스트를 고치면 (예측)

```java
List<List<Integer>> ws = Stream.of(1,2,3,4).gather(Gatherers.windowFixed(2)).toList();
ws.get(0).add(99);
```

- 무엇이 던져지는가?
- 예외 **메시지**는 무엇인가?
- 그것이 왜 문제가 되는가?
- 이 동작은 언어 보장인가 구현 세부인가?
- 고쳐야 한다면 무엇을 하는가?

### 11. 24 이전에는 어떻게 했나 (연결)

```java
// 21 에서 3개씩 묶으려면
List<Integer> materialized = src.stream().toList();
List<List<Integer>> chunks = IntStream.range(0, (materialized.size() + 2) / 3)
        .mapToObj(i -> materialized.subList(i * 3, Math.min(materialized.size(), i * 3 + 3)))
        .toList();
```

- 이 우회가 Gatherer 와 비교해 잃는 것은 무엇인가?
- `Collectors.groupingBy(x -> idx[0]++ / 3)` 라는 우회는 무엇이 위험한가?
- `map` 안에 외부 배열로 누적을 넣는 우회를 **병렬**로 돌리면 어떻게 되는가?
- 세 우회가 **공통으로** 못 하는 것은 무엇인가?
- 그래서 Gatherer 가 메운 구멍을 한 문장으로 말하면?

### 12. 어느 것을 고르는가 (연결)

- 1,000건씩 묶어 외부 API 로 보내야 한다 — 무엇을 쓰는가?
- 직전 값과의 차이를 계산해야 한다 — 무엇을 쓰는가?
- 느린 HTTP 호출 6개를 동시에 하고 순서는 지켜야 한다 — 무엇을 쓰는가?
- 결과를 `Map` 으로 모으기만 하면 된다 — 무엇을 쓰는가?
- 타깃이 JDK 21 이다 — 위 답들은 어떻게 바뀌는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
