# java/syntax/47 — `Collectors`: 기본 수집기와 `toMap` 의 함정 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **선행** — [`../46-terminal-operations/`](../46-terminal-operations/) 의 질문을 먼저 푼다. `collect` 가 최종 연산이라는 것이 전제다.
> 이 주제는 **계약형에 가깝다** — 「어기면 무엇이 출력되나」를 묻는 문항이 많다.
> 그룹핑·분할은 [`../48-collectors-grouping/`](../48-collectors-grouping/) 의 질문이다.

## 예시 데이터

세 문항 이상이 이 데이터를 쓴다.

```java
record P(String team, String name, int score) {}

List<P> SRC = List.of(
        new P("red",   "kim",  10),
        new P("blue",  "lee",  20),
        new P("red",   "park", 30),
        new P("green", "choi", 40),
        new P("blue",  "jung", 50));
```

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 세 가지 `toList` 의 차이 (예측)

```java
Stream.of("x", null).toList()
Stream.of("x", null).collect(Collectors.toList())
Stream.of("x", null).collect(Collectors.toUnmodifiableList())
```

- 세 줄은 각각 무엇을 출력하거나 무엇을 던지는가?
- 세 결과에 `add("b")` 를 하면 각각 어떻게 되는가?
- 세 구체 타입은 무엇이며, 그 타입은 보장된 것인가?
- "불변"이라는 한 단어로 셋을 묶으면 무엇을 놓치는가?
- 기본으로 무엇을 쓰고, 언제 다른 것으로 바꾸는가?

### 2. `toMap` 의 첫 함정 (예측)

```java
List<P> dup = List.of(new P("red","kim",10), new P("blue","lee",20), new P("red","kim",30));

Map<String,Integer> m = new HashMap<>();
for (P p : dup) m.put(p.name(), p.score());        // (A)

dup.stream().collect(Collectors.toMap(P::name, P::score));   // (B)
```

- (A)의 결과는 무엇인가?
- (B)는 무엇을 출력하거나 던지는가?
- 예외라면 **메시지 전문**은 무엇인가?
- 둘 중 어느 쪽이 더 안전한가, 그 이유는 무엇인가?
- 그 메시지를 만드는 JDK 소스는 어떻게 생겼는가?

### 3. `toMap` 의 둘째 함정 (예측)

```java
List<P2> src = List.of(new P2("kim", 10), new P2("lee", null));   // score 가 Integer

new HashMap<>() { { for (P2 p : src) put(p.name(), p.score()); } }   // (A)
src.stream().collect(Collectors.toMap(P2::name, P2::score))          // (B)
src.stream().collect(Collectors.toMap(P2::name, P2::score, (a,b)->b))// (C)
```

- (A)는 어떻게 되는가, `containsKey("lee")` 와 `get("lee")` 는 각각 무엇인가?
- (B)와 (C)는 각각 무엇을 던지는가?
- 두 예외는 **같은 자리에서** 나는가?
- 예외 메시지가 있는가?
- **키**가 `null` 이면 어떻게 되는가?

### 4. merge 함수가 `null` 을 돌려주면 (예측)

```java
List.of(new P("red","kim",10), new P("red","kim",30)).stream()
    .collect(Collectors.toMap(P::name, P::score, (a, b) -> null));
```

- 결과는 무엇인가?
- 예외가 나는가?
- 왜 그렇게 되는가 — 어느 메서드의 계약 때문인가?
- 이것이 왜 위험한 실패 모드인가?

### 5. 집계 수집기의 반환 타입 (예측)

```java
SRC.stream().collect(Collectors.counting())
SRC.stream().collect(Collectors.summingInt(P::score))
SRC.stream().collect(Collectors.averagingInt(P::score))
SRC.stream().collect(Collectors.maxBy(Comparator.comparingInt(P::score)))
```

- 네 줄의 값과 타입은 각각 무엇인가?
- `averagingInt` 가 `Integer` 가 아닌 이유는 무엇인가?
- 빈 스트림에서 네 줄은 각각 무엇을 돌려주는가?
- 그중 어느 것만 `Optional` 인가, 왜 그것만인가?

### 6. `joining` 의 앞뒤 문자열 (예측)

```java
Stream.of("kim","lee").collect(Collectors.joining(", ", "[", "]"))
Stream.<String>empty().collect(Collectors.joining(", ", "[", "]"))
```

- 두 줄은 각각 무엇인가?
- 빈 스트림에서도 앞뒤가 붙는가?
- 숫자 스트림에 `joining` 을 바로 걸 수 있는가?
- `joining` 은 내부에서 무엇을 쓰는가?

### 7. 합계가 조용히 틀리는 자리 (예측)

```java
Stream.of(Integer.MAX_VALUE, 1).collect(Collectors.summingInt(i -> i))
Stream.of(Integer.MAX_VALUE, 1).collect(Collectors.summingLong(i -> i))
```

- 두 줄의 결과는 각각 무엇인가?
- 첫 줄에서 예외나 경고가 나는가?
- 실무에서 무엇을 기본으로 쓰는가?

### 8. 빈 목록의 평균 (경계)

```java
orders.stream().collect(Collectors.averagingInt(Order::amount))   // orders 가 비었을 때
```

- 결과는 무엇인가?
- 이것이 왜 위험한가?
- "데이터 없음"과 "평균이 0"을 구별하려면 무엇을 쓰는가?

### 9. 이 코드는 왜 컴파일이 안 되는가 (경계)

```java
System.out.println(src.stream().collect(
        Collectors.toMap(P::name, P::score, (a,b)->b, TreeMap::new)));
```

- 어떤 에러가 나는가?
- 원인은 `toMap` 인가 `println` 인가?
- 어떻게 고치는가?

### 10. 반환 타입은 어디까지 믿어도 되나 (경계)

- `collect(Collectors.toList())` 가 `ArrayList` 라는 것을 코드에서 가정해도 되는가?
- `toMap` 이 `HashMap` 이라는 것은 어떤가?
- javadoc 의 어느 문장이 근거인가?
- 그러면 **무엇이** 계약인가?

### 11. 17·21·25 에서 무엇이 달랐나 (경계)

- 예외 **메시지**는 세 버전에서 같았는가?
- 스택트레이스는 어땠는가?
- 람다 이름(`lambda$...$1`)은 어땠는가?
- 그래서 이 주제의 동작을 테스트로 고정할 때 무엇을 쓰고 무엇을 쓰지 않는가?

### 12. 무엇을 고르는가 (연결)

- 리스트를 id 로 맵으로 바꾼다 — 어느 `toMap` 을 쓰는가?
- 키 순서가 입력 순서여야 한다 — 무엇을 더 주는가?
- 중복을 없애되 입력 순서는 지켜야 한다 — 무엇을 쓰는가?
- 개수만 센다 — `counting()` 인가 다른 것인가?
- `counting()`·`summingInt()` 의 진짜 자리는 어디인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
