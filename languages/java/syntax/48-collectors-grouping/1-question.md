# java/syntax/48 — `Collectors` 그룹핑·분할·다운스트림 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **선행** — [`../47-collectors-basics/`](../47-collectors-basics/) 의 질문을 먼저 푼다. 다운스트림 자리에 들어가는 것이 전부 거기 있다.
> 이 주제는 **조합형**이다 — "무엇이 나오는가"와 함께 "**어떻게 조립하는가**"를 묻는다.
> 병렬에서 달라지는 것은 [`../49-parallel-streams/`](../49-parallel-streams/) 의 질문이다.

## 예시 데이터

47번과 같은 데이터다. 거의 모든 문항이 이것을 쓴다.

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

### 1. `groupingBy` 의 기본값 (예측)

```java
Map<String, List<P>> g = SRC.stream().collect(Collectors.groupingBy(P::team));
```

- `g` 의 구체 타입과 값의 구체 타입은 각각 무엇인가?
- 그 타입들은 보장된 것인가, 어느 javadoc 문장이 근거인가?
- `g.get("red")` 의 원소 순서는 무엇인가?
- 1인자 `groupingBy` 는 무엇과 같은가?

### 2. 키 순서를 예측하라 (예측)

```java
List<String> keys = List.of("apple","banana","cherry","date","elderberry","fig","grape","honeydew");
keys.stream().collect(Collectors.groupingBy(s -> s)).keySet();
```

- 결과 키 순서는 입력 순서인가, 정렬 순서인가, 그 외인가?
- 같은 프로그램을 다시 돌리면 순서가 바뀌는가?
- 17·21·25 에서 순서가 달랐는가?
- 그 "안정성"이 왜 오히려 위험한가?
- 순서가 필요하면 무엇을 쓰는가?

### 3. `partitioningBy` 가 `groupingBy` 와 다른 점 (예측)

```java
SRC.stream().collect(Collectors.partitioningBy(p -> p.score() > 1000))   // (A)
SRC.stream().collect(Collectors.groupingBy(p -> p.score() > 1000))       // (B)
```

- (A)와 (B)의 크기는 각각 몇인가?
- (A)와 (B)에 `.get(true)` 를 하면 각각 무엇이 나오는가?
- 빈 스트림에 (A)를 걸면 무엇이 나오는가?
- 이 차이를 보장하는 javadoc 문장은 무엇인가?
- (A)의 결과 맵에 `put` 을 하면 어떻게 되는가?

### 4. 다운스트림으로 무엇이 나오는가 (예측)

```java
groupingBy(P::team, TreeMap::new, Collectors.counting())
groupingBy(P::team, TreeMap::new, Collectors.summingInt(P::score))
groupingBy(P::team, TreeMap::new, Collectors.averagingInt(P::score))
groupingBy(P::team, TreeMap::new, Collectors.mapping(P::name, Collectors.joining("+")))
```

- 네 줄의 결과를 각각 적어라.
- `counting()` 의 값 타입은 무엇인가?
- 왜 `TreeMap::new` 를 넣었는가?
- 다운스트림이 늘면 소스를 몇 번 읽는가?

### 5. `maxBy` 를 다운스트림으로 (예측)

```java
groupingBy(P::team, TreeMap::new, Collectors.maxBy(Comparator.comparingInt(P::score)))
```

- 결과의 값 타입은 무엇인가?
- 그 값이 비어 있을 수 있는가, 왜 그런가?
- 팀별 최고 득점자의 **이름만** 얻으려면 어떻게 고치는가?

### 6. `filtering` 과 `filter` (예측)

```java
// (A)
groupingBy(P::team, TreeMap::new, Collectors.filtering(p -> p.score() >= 40,
        Collectors.mapping(P::name, Collectors.toList())))
// (B)
SRC.stream().filter(p -> p.score() >= 40)
   .collect(groupingBy(P::team, TreeMap::new, Collectors.mapping(P::name, Collectors.toList())))
```

- (A)와 (B)의 결과는 각각 무엇인가?
- 어느 키가 한쪽에만 있는가?
- 어느 쪽을 언제 쓰는가?
- `filtering` 은 어느 버전부터인가?

### 7. 2단 그룹핑 (예측)

```java
groupingBy(P::team, TreeMap::new,
        groupingBy(p -> p.score() >= 30, TreeMap::new, mapping(P::name, toList())))
```

- 결과를 적어라.
- `green` 의 값에 칸이 몇 개인가?
- 안쪽을 `partitioningBy` 로 바꾸면 무엇이 달라지는가?
- 깊이 제한이 있는가?

### 8. `teeing` (연결)

```java
SRC.stream().collect(Collectors.teeing(
        Collectors.counting(), Collectors.summingInt(P::score), (c, s) -> c + "명 합계 " + s));
```

- 결과는 무엇인가?
- `teeing` 은 어느 버전부터인가?
- 그 전에는 같은 일을 어떻게 했는가?
- 왜 스트림을 두 번 쓸 수 없는가?

### 9. 분류 함수가 `null` 을 돌려주면 (예측)

```java
SRC.stream().collect(Collectors.groupingBy(p -> p.score() > 25 ? p.team() : null));
```

- 무엇이 던져지는가?
- 메시지가 있는가?
- 47번의 `toMap` `null` 값 예외와 비교하면 무엇이 다른가?
- 방어는 무엇인가?

### 10. `partitioningBy` 에 `null` 원소가 들어오면 (경계)

```java
List<String> withNull = new ArrayList<>(List.of("a","bb")); withNull.add(null);
withNull.stream().collect(Collectors.partitioningBy(s -> s.length() > 1));
```

- 무엇이 던져지는가?
- 던지는 것은 `partitioningBy` 인가 술어인가?
- 술어를 `s != null && s.length() > 1` 로 바꾸면 결과는 무엇인가?
- `groupingBy` 와 계약이 어떻게 다른가?

### 11. 이 두 줄은 왜 컴파일이 안 되는가 (경계)

```java
// (A)
Map<String, List<P>> m = SRC.stream().collect(Collectors.groupingBy(P::team, TreeMap::new));
// (B)
System.out.println(SRC.stream().collect(
        Collectors.groupingBy(P::team, TreeMap::new, Collectors.counting())));
```

- (A)의 에러는 무엇이며 원인은 무엇인가?
- (B)의 에러는 무엇이며 원인은 무엇인가?
- 둘은 같은 원인인가?
- 각각 어떻게 고치는가?

### 12. 이 코드의 버그를 찾아라 (연결)

```java
Map<String, List<P>> byTeam = SRC.stream().collect(Collectors.groupingBy(P::team));
for (String team : List.of("red", "blue", "green", "yellow")) {
    System.out.println(team + " : " + byTeam.get(team).size());
}
```

- 무엇이 터지는가?
- 왜 터지는가?
- 고치는 방법을 세 가지 적어라.
- 조건이 둘로 갈리는 경우였다면 애초에 무엇을 썼어야 하는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
