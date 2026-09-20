# java/syntax/40 — `List`·`Set` API 와 불변 팩토리: `List.of`·`copyOf`·`unmodifiable*` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **선행** — [`../39-collections-framework-map/`](../39-collections-framework-map/) 의 질문을 먼저 푼다. 옵셔널 연산이 전제다.
> 해시 집합의 **내부**(버킷·충돌)는 여기서 묻지 않는다 — [`../../../../../data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/) 의 질문이다.
> `equals`/`hashCode` **계약 자체**도 여기가 아니다 — [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) 의 질문이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 세 팩토리의 세 축 (예측)

```java
List<String> src = new ArrayList<>(List.of("a", "b", "c"));

List.of("a", null)
Arrays.asList("a", null)
Collections.unmodifiableList(src)
List.copyOf(src)
```

- 네 줄은 각각 무엇을 만들거나 무엇을 던지는가?
- 네 결과에 `add("z")` / `set(0,"z")` / `remove(0)` 을 하면 각각 어떻게 되는가?
- `src.add("d")` 를 한 뒤 셋째와 넷째를 출력하면 각각 무엇인가?
- 세 축의 이름을 각각 무엇이라 부르는가?
- "불변"과 "수정 불가 뷰"를 javadoc 은 어떻게 구별하는가?

### 2. `Arrays.asList` 는 어느 방향으로 비치나 (예측)

```java
String[] back = {"a", "b", "c"};
List<String> view = Arrays.asList(back);
view.set(1, "Z");
System.out.println(Arrays.toString(back));
back[2] = "Y";
System.out.println(view);
```

- 두 출력은 각각 무엇인가?
- `Arrays.asList` 는 배열을 복사하는가?
- `set` 은 되는데 `add` 가 안 되는 이유를 한 문장으로 말하면?
- `int[] arr` 를 `Arrays.asList(arr)` 에 넣으면 크기가 몇인 리스트가 되는가, 왜인가?

### 3. `subList` 는 어디까지 살아 있나 (예측)

```java
List<String> base = new ArrayList<>(List.of("a","b","c","d","e"));
List<String> sub = base.subList(1, 4);
sub.set(0, "B");        // (A) base 는?
sub.clear();            // (B) base 는?

List<String> b2 = new ArrayList<>(List.of("a","b","c","d","e"));
List<String> s2 = b2.subList(1, 4);
b2.add("f");
s2.size();              // (C) 무엇이 되는가?
b2.set(0, "A");         // (D) 그 다음 s2 를 읽으면?
```

- (A)~(D)는 각각 어떻게 되는가?
- (C)에서 나는 예외는 **보장인가**? javadoc 은 무엇이라 적는가?
- (D)가 (C)와 다른 이유는 무엇인가?
- `subList` 로 잘라낸 것을 캐시에 넣으면 무엇이 문제인가?

### 4. 같은 프로그램을 세 번 실행하면 (예측)

```java
System.out.println(Set.of("a","b","c","d","e"));
System.out.println(new HashSet<>(List.of("a","b","c","d","e")));
System.out.println(List.of("a","b","c","d","e"));
```

- 같은 JDK 에서 JVM 을 세 번 띄우면 세 줄은 각각 매번 같은가?
- 다르다면 **왜 그렇게 만들어 놓았는가**?
- 그 의도를 밝힌 JDK 소스의 필드 이름은 무엇인가?
- 이 사실은 "여러 버전에서 같았다"는 관찰과 어떻게 다른 종류의 근거인가?

### 5. 중복을 넣으면 (예측)

```java
Set.of("a", "a")
Map.of("a", 1, "a", 2)
List.of("a", "a")
new HashSet<>(List.of("a", "a"))
```

- 네 줄은 각각 무엇을 돌려주거나 무엇을 던지는가?
- 던진다면 예외 **클래스와 메시지 전문**은?
- `HashSet` 과 `Set.of` 중 어느 쪽이 더 안전한가, 왜인가?
- 런타임 데이터로 집합을 만들 때는 어느 쪽을 쓰는가?

### 6. `Set` 에 넣고 필드를 바꾸면 (예측)

```java
class Box { int v; /* equals·hashCode 를 v 로 재정의 */ }

Box box = new Box(1);
Set<Box> s = new HashSet<>();
s.add(box);
box.v = 99;
// contains(box) / remove(box) / size() / 순회
```

- 네 가지는 각각 무엇을 돌려주는가?
- 원소가 **사라진 것인가**, 못 찾는 것인가?
- `new Box(99)` 로 찾으면 되는가?
- javadoc 은 이 상황을 무엇이라 적는가?

### 7. `removeIf` 가 가끔만 터진다 (경계)

```java
Arrays.asList(1, 2).removeIf(n -> n % 2 == 0);
Arrays.asList(1, 3).removeIf(n -> n % 2 == 0);
List.of(1, 3).removeIf(n -> n % 2 == 0);
```

- 세 줄은 각각 어떻게 되는가?
- 둘째와 셋째가 갈리는 이유는 무엇인가?
- 예외 메시지에 `remove` 가 붙는 이유는 무엇인가?
- 이 갈림을 허용하는 javadoc 문장은 어느 것인가?

### 8. `remove` 의 오버로드 (경계)

```java
List<Integer> l = new ArrayList<>(List.of(10, 20, 30));
l.remove(1);
l.remove(Integer.valueOf(20));
l.remove(100);
```

- 세 줄은 각각 무엇을 하는가?
- 셋째 줄은 무엇을 던지는가 — 메시지 전문은?
- 이 함정이 `List<String>` 에서는 왜 안 생기는가?

### 9. `copyOf` 는 언제 복사하나 (경계)

- `List.copyOf(List.of("a","b"))` 는 새 객체를 만드는가?
- `List.copyOf(new ArrayList<>(...))` 는?
- `List.copyOf(Arrays.asList(...))` 는?
- `Collections.unmodifiableList(이미_unmodifiable)` 은?
- 이 최적화는 보장인가, 관측인가 — 근거 문장은?

### 10. getter 에 무엇을 쓰나 (연결)

```java
private final List<String> items = new ArrayList<>();
public List<String> getItems() { return ???; }
```

- 후보 넷(`items` 그대로 / `unmodifiableList` / `copyOf` / `new ArrayList<>`)은 각각 무엇을 막고 무엇을 못 막는가?
- "호출자가 순회 중인데 내가 `items.add` 를 한다" — 넷 중 어디서 문제가 나는가?
- 스냅샷이 필요하면 무엇을 쓰는가?
- 복사 비용이 아까울 때의 선택과 그때 문서에 적어야 할 것은 무엇인가?

### 11. 어느 것을 쓰는가 (연결)

- 상수 목록 선언 →
- `null` 이 섞일 수 있는 값들로 리스트를 만든다 →
- 받은 컬렉션을 필드에 보관한다 →
- 리스트의 앞 20개를 잘라 캐시에 넣는다 →
- 리스트의 구간을 통째로 지운다 →
- 조건에 맞는 원소를 지운다 →
- 배열을 잠깐 리스트처럼 읽는다 →

### 12. 무엇이 보장인가 (경계)

- `List.of(...)` 의 구체 타입이 `ImmutableCollections$List12` 라는 것은?
- `Set.of("a","a")` 의 메시지가 `duplicate element: a` 라는 것은?
- 원본을 고친 뒤 `subList` 를 읽으면 CME 가 난다는 것은?
- `Set.of` 의 순회 순서가 실행마다 바뀐다는 것은?
- 이 넷 중 테스트에 적어도 되는 것은 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
