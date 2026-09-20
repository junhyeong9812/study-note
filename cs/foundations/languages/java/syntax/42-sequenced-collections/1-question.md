# java/syntax/42 — `SequencedCollection` (21): 순서 있는 컬렉션의 공통 API — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **선행** — [`../39-collections-framework-map/`](../39-collections-framework-map/) 의 질문을 먼저 푼다.
> **이 주제는 Java 21 부터다.** 17 에서는 전부 컴파일 에러가 난다 — 그것도 문항이다(9번).
> **왜 21에 들어왔나**는 여기서 묻지 않는다 — [`../../../../../../history/java/java-21.md`](../../../../../../history/java/java-21.md) 의 영역이다.

## 예시 데이터

여러 문항이 이 데이터를 쓴다.

```java
List<String> list = new ArrayList<>(List.of("a", "b", "c"));
LinkedHashMap<String,Integer> lhm = new LinkedHashMap<>();  // {a=1, b=2, c=3}
```

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 21 이전에는 어떻게 썼나 (왜)

여섯 컬렉션에서 **첫 원소**와 **끝 원소**를 꺼내는 21 이전 코드는 각각 무엇인가.

- `List` →
- `Deque` →
- `LinkedHashSet` →
- `SortedSet` →
- `LinkedHashMap` →
- `SortedMap` →
- 여섯 중 **끝 원소를 O(1) 에 못 얻던 것**은 무엇이며, 내부적으로도 못 얻는 것인가?

### 2. 21 이 통일한 것 (경계)

- `SequencedCollection` 의 메서드는 몇 개이며 무엇인가?
- `SequencedMap` 은 왜 이름이 `getFirst` 가 아니라 `firstEntry` 인가?
- `SequencedSet` 이 새로 더하는 메서드는 몇 개인가?
- `SequencedMap` 에만 있는 뷰 메서드 셋은 무엇인가?

### 3. 누가 하위 타입이 됐나 (예측)

```java
new ArrayList<>()      instanceof SequencedCollection
new ArrayDeque<>()     instanceof SequencedCollection
new HashSet<>()        instanceof SequencedCollection
new LinkedHashSet<>()  instanceof SequencedSet
new TreeSet<>()        instanceof SequencedSet
new PriorityQueue<>()  instanceof SequencedCollection
List.of()              instanceof SequencedCollection
Set.of()               instanceof SequencedCollection
new HashMap<>()        instanceof SequencedMap
new LinkedHashMap<>()  instanceof SequencedMap
new TreeMap<>()        instanceof SequencedMap
```

- 열한 줄의 결과는 각각 무엇인가?
- `PriorityQueue` 가 빠진 이유는 무엇인가?
- `Set.of()` 가 빠진 이유는 무엇인가 — 40번과 이어서 말하면?
- `ArrayDeque` 는 `List` 인가?

### 4. ★ `reversed()` 는 복사인가 뷰인가 (예측)

```java
List<String> src = new ArrayList<>(List.of("a", "b", "c"));
List<String> rev = src.reversed();

src.add("d");            // (A) rev 는?
rev.add("z");            // (B) src 는?
rev.set(0, "Z");         // (C) src 는?
rev.reversed() == src;   // (D) ?
```

- (A)~(D)는 각각 무엇이 되는가?
- (B)에서 `"z"` 는 `src` 의 **어느 쪽 끝**에 들어가는가, 왜인가?
- `rev` 의 구체 타입은 무엇인가?
- `rev.get(0)` 과 `rev.indexOf("c")` 는 원본과 어떻게 다른가?
- javadoc 이 `reversed()` 를 뷰라고 적은 자리는 어디인가?
- 「원본의 변경이 뷰에 보이는 것」은 보장인가?

### 5. `LinkedHashMap` 의 순서 조작 (예측)

```java
LinkedHashMap<String,Integer> m = new LinkedHashMap<>();   // {a=1, b=2, c=3}
m.putFirst("c", 30);      // (A) ?
m.putLast("a", 10);       // (B) ?
m.pollFirstEntry();       // (C) 반환값과 맵은?
m.put("b", 99);           // (D) 순서가 바뀌는가?
```

- (A)~(D)는 각각 어떻게 되는가?
- `put` 과 `putFirst` 의 차이를 javadoc 문장으로 말하면?
- 접근 순서 모드(`new LinkedHashMap<>(16, 0.75f, true)`)에서 `lastEntry()` 를 읽으면 순서가 바뀌는가?
- 그 규칙을 적은 javadoc 문장은 무엇인가?

### 6. 안 되는 것 (예측)

```java
new HashSet<>(List.of("a")).getFirst()
List.of("a").addFirst("z")
new TreeSet<>(List.of("a")).addFirst("z")
new TreeSet<>(List.of("a","b")).removeFirst()
new ArrayList<>().getFirst()
new LinkedHashMap<>().firstEntry()
new LinkedHashMap<>().pollFirstEntry()
new TreeMap<>().putFirst("z", 9)
```

- 여덟 줄은 각각 무엇을 던지거나 무엇을 돌려주는가?
- 첫 줄만 성질이 다르다 — 무엇이 다른가?
- `TreeSet` 이 `addFirst` 는 막고 `removeFirst` 는 허용하는 이유는 무엇인가?
- **빈 컬렉션**과 **빈 맵**의 규약이 갈린다 — 어떻게 갈리는가?

### 7. `TreeSet.reversed()` 와 `descendingSet()` (경계)

- 둘은 같은 것인가? `equals` 로 비교하면?
- `TreeSet.reversed()` 의 **구체 타입**은 무엇인가?
- 둘 다 뷰인가?
- 새 코드에서는 무엇을 쓰는가, 왜인가?

### 8. `sequencedKeySet()` 이 왜 따로 있나 (왜)

```java
LinkedHashMap<String,Integer> m = new LinkedHashMap<>();
m.keySet() == m.sequencedKeySet();     // (A) ?
m.keySet() instanceof SequencedSet;    // (B) ?
m.keySet().reversed();                 // (C) ?
```

- (A)~(C)는 각각 무엇인가?
- (C)가 그렇게 되는 이유는 **런타임 타입** 때문인가 **선언 타입** 때문인가?
- 그래서 `sequencedKeySet()` 이라는 새 이름이 필요했던 이유는 무엇인가?

### 9. 17 에서는 (예측)

```java
List<String> list = new ArrayList<>(List.of("a","b","c"));
System.out.println(list.getFirst());
SequencedCollection<String> sc = list;
```

- JDK 17 의 `javac` 로 컴파일하면 무엇이 나오는가 — **에러 문구 전문**은?
- JDK 21 의 `javac --release 17` 은 어떤가?
- 21 에서 컴파일한 클래스 파일을 17 로 실행하면 무엇이 나오는가?

### 10. 17 에서 되던 것이 21 에서 깨진다 (예측)

```java
static class MyList extends ArrayList<String> {
    public String reversed() { return "뒤집힌 문자열"; }
}
```

- JDK 17 에서 컴파일되는가? 실행 결과는?
- JDK 21 에서는 어떤가 — **에러 문구 전문**은?
- 이런 충돌이 날 수 있는 메서드 이름은 몇 개이며 무엇인가?
- 이 현상을 무엇이라 부르는가?

### 11. 어느 것을 쓰는가 (연결)

- 리스트를 역순으로 돈다 →
- 역순 결과를 **보관**한다 →
- `LinkedHashSet` 의 마지막 원소를 얻는다 →
- LRU 캐시에서 가장 오래된 항목을 꺼내 지운다 →
- "순서가 있는 컬렉션만 받는다"를 타입으로 표현한다 →
- 17 타깃 라이브러리에서 첫 원소를 얻는다 →

### 12. 무엇이 보장인가 (경계)

- `reversed()` 가 뷰라는 것은?
- 뷰에 쓴 것이 원본에 반영된다는 것은?
- 원본의 변경이 뷰에 보인다는 것은?
- `rev.reversed() == src` 는?
- `TreeSet.reversed()` 가 `descendingSet()` 과 같은 것을 돌려준다는 것은?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
