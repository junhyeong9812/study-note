# java/syntax/39 — 컬렉션 프레임워크 지도: 인터페이스 계층과 구현체 선택 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **선행** — [`../17-generic-declarations/`](../17-generic-declarations/) 의 질문을 먼저 푼다.
> 이 주제는 **지도·선택형**이다 — 예측형보다 「무엇을 보고 고르나」를 묻는 문항이 많다(정상이다).
> **자료구조의 내부**(해시 충돌·트리 회전·상각 분석)는 여기서 묻지 않는다.
> 그것은 [`../../../../../data-structure/`](../../../../../data-structure/) 의 질문이다.

## 예시 데이터

여러 문항이 이 데이터를 쓴다.

```java
List<String> IN = List.of("pear", "apple", "fig", "apple", "date");
```

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `Map` 은 어디에 매달려 있나 (예측)

```java
System.out.println(Collection.class.isAssignableFrom(Map.class));
System.out.println(Arrays.toString(Map.class.getInterfaces()));

Map<String,Integer> m = new HashMap<>();
for (String s : m) System.out.println(s);
```

- 앞 두 줄은 각각 무엇을 출력하는가?
- 마지막 `for` 문은 무엇이 되는가 — 실행되는가, 컴파일 에러인가?
- 에러라면 **에러 문구 전문**은 무엇인가?
- `Map` 이 `Collection` 세계와 이어지는 통로는 무엇이며 몇 개인가?
- 만약 `Map<K,V>` 가 `Collection<Map.Entry<K,V>>` 였다면 어느 메서드가 정의 불가능해지는가?

### 2. 같은 데이터를 여섯 곳에 담으면 (예측)

```java
List<String> IN = List.of("pear", "apple", "fig", "apple", "date");

new ArrayList<>(IN)
new HashSet<>(IN)
new LinkedHashSet<>(IN)
new TreeSet<>(IN)
new PriorityQueue<>(IN)      // toString 과 poll 순서를 나눠서
```

- 다섯의 `toString` 은 각각 무엇인가 — **크기**는 각각 몇인가?
- `PriorityQueue` 의 `toString` 과 `poll` 순서는 같은가?
- 다섯 중 **javadoc 이 순서를 약속하는 것**은 무엇인가?
- 약속하지 않는 것의 출력이 세 JDK 에서 똑같았다면, 그것을 테스트에 적어도 되는가?

### 3. `null` 은 어디까지 들어가나 (예측)

```java
new ArrayList<String>().add(null)
new HashSet<String>().add(null)
new TreeSet<String>().add(null)
new ArrayDeque<String>().add(null)
new HashMap<String,Integer>().put(null, 1)
new TreeMap<String,Integer>().put("a", null)
new ConcurrentHashMap<String,Integer>().put("a", null)
```

- 일곱 줄 중 **던지는 것**은 어느 것인가?
- 던지는 것들의 예외 **클래스와 메시지**는 각각 무엇인가?
- 거부하는 이유가 **세 갈래**로 나뉜다 — 무엇과 무엇과 무엇인가?
- `ArrayDeque` 가 `null` 을 거부하는 이유를 그 클래스의 다른 메서드로 설명하면?
- `Hashtable` 은 키와 값에서 **왜 다른 메시지**가 나오는가?

### 4. 같은 `List` 인데 능력이 다르다 (예측)

```java
List<String> a = new ArrayList<>(List.of("a","b"));
List<String> b = Arrays.asList("a","b");
List<String> c = List.of("a","b");
List<String> d = Collections.unmodifiableList(a);
// 각각에 add("z") / set(0,"z") / remove(0)
```

- 넷 × 셋 = 열두 칸 중 **성공하는 칸**은 어디인가?
- `Arrays.asList` 만 특이한 칸이 있다 — 어느 칸이고 왜인가?
- `c.addAll(List.of())` 와 `b.addAll(List.of())` 는 같은 결과인가?
- 그 차이를 허용하는 javadoc 문장은 무엇인가?
- 이 설계에 이름이 있다 — 무엇이라 부르며, 무엇을 얻고 무엇을 잃었는가?

### 5. `TreeSet` 에 내 타입을 넣으면 (예측)

```java
record P(String n) {}
new TreeSet<>(List.of(new P("a"), new P("b")));
new TreeMap<Object,Integer>().put(new P("a"), 1);   // 키가 하나뿐일 때
new HashSet<>(List.of(new P("a"), new P("b")));
```

- 세 줄은 각각 무엇을 던지거나 무엇을 돌려주는가?
- 던진다면 예외 **클래스 이름**은 무엇인가 — 컴파일 에러인가 런타임인가?
- **키가 하나뿐일 때도** 던지는가? 왜 그런가?
- `HashSet` 은 왜 통과하는가 — 두 컬렉션이 요구하는 계약이 어떻게 다른가?
- 고치는 방법은 몇 가지이며 각각 무엇인가?

### 6. 계층에서 누가 누구를 확장하나 (경계)

- `List` 는 `Collection` 을 **직접** 확장하는가?
- `SortedSet` 이 확장하는 인터페이스는 몇 개이며 무엇인가?
- `ArrayDeque` 는 `List` 인가?
- `LinkedList` 는 `List` 인가 `Deque` 인가?
- `PriorityQueue.class.getInterfaces()` 에 `Queue` 가 없는데도 `instanceof Queue` 가 `true` 인 이유는 무엇인가?

### 7. 다섯 질문으로 고른다 (연결)

다음 요구에 각각 무엇을 고르는가.

- 로그 줄을 읽은 순서대로 담는다 →
- 방문한 URL 을 중복 없이, 방문 순서대로 →
- 사용자 ID 로 사용자 객체를 찾는다 →
- 마감이 가장 임박한 작업부터 꺼낸다 →
- 요일(`enum`)별 설정값 →
- 여러 스레드가 동시에 카운터를 올린다 →
- 점수 구간으로 범위 질의(80점 이상 90점 미만)를 한다 →

### 8. 선언 타입을 무엇으로 두나 (왜)

```java
ArrayList<String> a = new ArrayList<>();
List<String> b = new ArrayList<>();
Collection<String> c = new ArrayList<>();
```

- 셋 중 무엇을 기본으로 쓰는가, 그 이유는?
- `c.get(0)` 은 컴파일되는가?
- 반환 타입을 `ArrayList` 로 적으면 나중에 무엇이 곤란해지는가?
- 반대로 **`LinkedHashMap` 으로 선언해야 하는** 상황은 언제인가?

### 9. `Map` 을 도는 네 형태 (경계)

```java
for (String k : m.keySet())                       { m.get(k); }
for (int v : m.values())                          { }
for (Map.Entry<String,Integer> e : m.entrySet())  { }
m.forEach((k, v) -> { });
```

- 넷 중 기본으로 쓰는 것은 무엇이며 왜인가?
- 첫 줄의 형태가 낭비인 이유는 무엇인가?
- `Map.Entry` 와 `Map` 은 무엇이 다른가?
- 넷 중 `Map` 이 `Iterable` 이 아니라는 사실을 가장 잘 드러내는 것은 무엇인가?

### 10. 무엇이 보장이고 무엇이 구현 세부인가 (경계)

- `HashMap` 의 키 순서는 보장인가? 근거 문장은 무엇인가?
- `LinkedHashSet` 의 순서는 보장인가?
- `TreeSet.add(null)` 의 NPE **메시지 문구**는 보장인가?
- `List.of(...)` 의 구체 타입이 `ImmutableCollections$List12` 라는 것은 보장인가?
- "17·21·25 에서 같았다"는 것은 무엇의 근거가 되고 무엇의 근거가 안 되는가?

### 11. 스택이 필요하다 (예측)

```java
List<String> in = List.of("pear", "apple", "fig");
Stack<String> st = new Stack<>();
Deque<String> dq = new ArrayDeque<>();
for (String s : in) { st.push(s); dq.push(s); }
// toString / 향상된 for 순회 / pop 순서
```

- `st` 와 `dq` 의 `toString` 은 각각 무엇인가?
- 향상된 `for` 로 돌면 각각 무엇이 나오는가?
- `pop` 순서는 각각 무엇인가 — 둘이 같은가?
- 셋(`toString`·순회·`pop`) 중 **`Stack` 만 어긋나는 것**은 무엇이며 왜인가?
- `Stack` 의 상위 클래스는 무엇이고, 그래서 `st.add(0, "z")` 가 되는가?
- 새 코드에서 스택이 필요하면 무엇을 쓰는가?

### 12. 이 주제의 경계 (연결)

- 「해시 충돌이 나면 버킷에서 무슨 일이 일어나나」는 어느 문서의 질문인가?
- 「`HashMap` 과 `TreeMap` 중 무엇을 고르나」는 어느 문서의 질문인가?
- 「`SequencedCollection` 이 왜 21에 들어왔나」는 어디인가?
- 「`getFirst()` 를 어떻게 쓰나」는 어디인가?
- 「`equals` 를 깨면 `HashMap` 에서 무슨 일이 나나」는 어디인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
