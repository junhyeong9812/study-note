# java/syntax/59 — 불변 객체 만들기: 방어적 복사·`record` 와의 조합 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력을 맞힐 수 있는지**를 묻는다.
> 선행: [14 `record`](../14-records/) · [40 `List`·`Set` API 와 불변 팩토리](../40-list-set-and-immutable-factories/).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 불변의 조건 (경계)

- "불변으로 만들었다"고 말하려면 갖춰야 할 조건 **넷**을 댈 수 있는가?
- 그중 `record` 가 **공짜로 주는 것**은 어느 둘인가?
- 방어 복사는 **몇 군데**에 넣어야 하는가?
- 조건 하나를 빼먹었을 때 각각 어떤 증상이 나오는가?

### 2. 세 단계 클래스의 출력 (예측)

```java
final class Leaky {          // 생성자도 getter 도 그대로
    private final int[] scores; private final List<String> tags;
    Leaky(int[] s, List<String> t) { this.scores = s; this.tags = t; }
    int[] scores() { return scores; }  List<String> tags() { return tags; }
}
final class HalfSafe {       // 생성자에서만 복사
    HalfSafe(int[] s, List<String> t) { this.scores = s.clone(); this.tags = new ArrayList<>(t); }
    int[] scores() { return scores; }  List<String> tags() { return tags; }
}
final class Safe {           // 양쪽 다
    Safe(int[] s, List<String> t) { this.scores = s.clone(); this.tags = List.copyOf(t); }
    int[] scores() { return scores.clone(); }  List<String> tags() { return tags; }
}
// 셋 다 {90,80} 과 ["vip"] 로 만든 뒤
//   (ㄱ) 생성자에 넘긴 원본을 고치고
//   (ㄴ) getter 로 꺼낸 것을 고친다
```

- 세 클래스의 (ㄱ)·(ㄴ) 뒤 상태는 각각 무엇인가?
- `Safe.tags()` 로 꺼낸 리스트에 `add` 하면 무엇이 나오는가, 메시지는?
- `Safe` 는 왜 `tags()` 에서 복사를 안 해도 되는가?

### 3. ★ `List.copyOf` 대 `Collections.unmodifiableList` (예측)

```java
List<String> origin = new ArrayList<>(List.of("a", "b"));
List<String> view = Collections.unmodifiableList(origin);
List<String> copy = List.copyOf(origin);

view.add("x");      // (가)
copy.add("x");      // (나)
origin.add("c");
System.out.println(view);   // (다)
System.out.println(copy);   // (라)
origin.clear();
System.out.println(view.size() + " " + copy.size());   // (마)
```

- (가)~(마) 의 결과는 각각 무엇인가?
- 두 javadoc 이 이 차이를 어떤 낱말로 적었는가 — 인용할 수 있는가?
- 불변 클래스의 **필드**에 담을 때는 어느 것을 골라야 하는가?
- `unmodifiableList` 가 맞는 자리는 어디인가?

### 4. `copyOf` 의 성질 (예측)

```java
List.copyOf(List.of("a","b")) == List.of("a","b")        // 같은 인스턴스를 넘겼을 때
List.copyOf(Collections.unmodifiableList(mutable))       // 뷰를 넘겼을 때 — 복사하는가?
List.copyOf(listContainingNull)
```

- 첫 줄에서 `copyOf` 가 **복사를 하는가**?
- 뷰를 넘기면 복사하는가, 왜 그렇게 갈리는가?
- `null` 이 들어 있으면 무엇이 나오는가?
- `unmodifiableList` 는 `null` 을 어떻게 처리하는가?

### 5. `Arrays.asList` 와 얕은 복사 (예측)

```java
String[] arr = {"a", "b"};
List<String> asList = Arrays.asList(arr);
arr[0] = "Z";           System.out.println(asList);   // (가)
asList.set(1, "Y");     System.out.println(arr[1]);   // (나)
asList.add("c");                                      // (다)

List<int[]> rows = new ArrayList<>(); rows.add(new int[]{1,2});
List<int[]> frozen = List.copyOf(rows);
rows.get(0)[0] = 999;   System.out.println(frozen.get(0)[0]);  // (라)
```

- (가)~(라) 의 결과는 각각 무엇인가?
- `Arrays.asList` 를 방어적 복사로 쓰면 왜 안 되는가?
- (라) 가 보여 주는 한계를 뭐라고 부르는가?

### 6. `record` 는 어디까지 해 주나 (예측)

```java
record Order(String id, List<String> items, int[] counts) { }

List<String> items = new ArrayList<>(List.of("책"));
int[] counts = {1};
Order o = new Order("A1", items, counts);
items.add("펜"); counts[0] = 99;
System.out.println(o.items() + " " + Arrays.toString(o.counts()));   // (가)
o.items().add("또"); o.counts()[0] = -1;
System.out.println(o.items() + " " + Arrays.toString(o.counts()));   // (나)

Order o1 = new Order("A1", List.of("책"), new int[]{1});
Order o2 = new Order("A1", List.of("책"), new int[]{1});
System.out.println(o1.equals(o2));                                   // (다)
```

- (가)·(나)·(다) 의 출력은 각각 무엇인가?
- (다) 가 그렇게 나오는 이유는 무엇인가?
- 막으려면 컴팩트 생성자와 접근자에 각각 무엇을 넣는가?
- 접근자만 복사하면 `record` 의 어떤 불변식이 깨지는가?

### 7. `final` 클래스가 아니면 (예측)

```java
class Money { private final long amount;
    Money(long a) { this.amount = a; } long amount() { return amount; } }
class FakeMoney extends Money { private long real;
    FakeMoney(long a) { super(a); this.real = a; }
    @Override long amount() { return real++; } }

Money m = new FakeMoney(100);
System.out.println(m.amount() + " " + m.amount() + " " + m.amount());
```

- 출력은 무엇인가?
- `Money` 자신은 흠이 없는데 왜 문제가 되는가?
- 이 객체를 `Map` 키로 쓰면 무슨 일이 생기는가?
- 막는 방법 두 가지는 무엇인가?

### 8. ★ 생성자가 재정의 가능한 메서드를 부르면 (예측)

```java
class Base {
    private final int size;
    Base(int size) { this.size = size; describe(); }
    void describe() { System.out.println("Base.describe size=" + size); }
}
class Child extends Base {
    private final String label = "완성된 라벨";
    private final List<String> data = new ArrayList<>(List.of("x"));
    Child() { super(3); }
    @Override void describe() { System.out.println("Child.describe label=" + label + " data=" + data); }
}
new Child();
```

- 출력은 무엇인가?
- `label` 과 `data` 중 하나만 `null` 이다 — 어느 쪽이고 **왜 다른가**?
- 그 이유를 `javap -c` 로 어떻게 확인하는가?
- 이 증상이 특히 헷갈리는 이유는 무엇인가?

### 9. `this` 유출의 다른 경로 (왜)

```java
class Escaper {
    private final int value;
    Escaper(int value) { Registry.ALL.add(this); this.value = value; }
}
```

- 이 생성자가 끝난 뒤 `Registry.ALL.get(0)` 은 그 객체와 같은 객체인가?
- 무엇이 위험한가 — 단일 스레드에서도 문제가 되는가?
- `final` 필드가 주는 보장은 무엇이고, 이 코드가 그 보장을 어떻게 깨는가?
- 그 보장은 어느 문서 어느 절에 있는가?

### 10. 필드 타입별 방어법 (경계)

- `String`·`LocalDate`·`BigDecimal` 필드에는 방어 복사가 필요한가?
- `List` 필드와 배열 필드는 복사를 **각각 몇 군데**에 넣는가, 왜 다른가?
- 다차원 배열에 `clone()` 을 쓰면 무엇이 부족한가?
- `Date` 필드는 어떻게 다루는가 — 복사가 최선인가?

### 11. 무엇이 계약이고 무엇이 구현인가 (경계)

- `unmodifiableList` 가 뷰라는 것은 계약인가 구현인가?
- `copyOf` 가 이미 불변이면 복사를 안 하는 것은 어느 쪽인가 — javadoc 의 어떤 태그인가?
- `view.getClass()` 가 돌려준 클래스 이름에 기대도 되는가?
- `UnsupportedOperationException` 의 메시지에 기대도 되는가?

### 12. 다른 주제와 잇기 (연결)

- 불변이 아니면 `equals`/`hashCode` 계약에서 무엇이 깨지는가?
- `String` 이 불변이라 얻는 것 넷은 무엇인가?
- 불변 객체에 "바꾼 사본"을 주는 메서드의 예를 표준 라이브러리에서 둘 댈 수 있는가?
- 불변으로 만들면 안 되는(또는 어려운) 자리는 어디인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
