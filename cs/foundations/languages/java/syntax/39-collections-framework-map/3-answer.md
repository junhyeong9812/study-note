# java/syntax/39 — 컬렉션 프레임워크 지도: 인터페이스 계층과 구현체 선택 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러는 **Temurin JDK 에서 실제로 돌려 얻은 것**이다.\
> 소스·javadoc 인용은 JDK 21.0.5 의 `lib/src.zip` 을 풀어 읽은 원문이다.\
> 어느 프로그램을 어느 버전에서 돌렸는지는 맨 끝 「실행 검증」 표에 있다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `Map` 은 어디에 매달려 있나

**출력** (`Ex.java` — 39-a, 21·25 동일)

```text
--- Collection 과 Map 은 형제인가
Collection.isAssignableFrom(Map)  : false
Map.isAssignableFrom(Collection)  : false
Collection 의 상위 인터페이스     : [interface java.lang.Iterable]
Map 의 상위 인터페이스            : []
```

**`for` 문은 컴파일 에러다** (`Ex.java` — 39-d, JDK 21)

```text
$ javac Ex.java
Ex.java:6: error: for-each not applicable to expression type
        for (String s : m) System.out.println(s);
                        ^
  required: array or java.lang.Iterable
  found:    Map<String,Integer>
```

**왜 그런가**

```text
      Iterable                         Map
         |                        (상위 인터페이스 없음)
     Collection                          |
         |                     keySet()  values()  entrySet()
   List  Set  Queue                |        |         |
                                  Set  Collection  Set<Entry>
                                   |        |         |
                                   +--------+---------+
                                            |
                                     Collection 세계로 들어온다
```

- `Map.class.getInterfaces()` 가 **빈 배열**이다. `Object` 말고는 아무것도 확장하지 않는다.
- 향상된 `for` 는 **배열 또는 `Iterable`** 에만 돈다 — 에러 문구가 그대로 말한다.
- `Collection` 은 `Iterable` 하나만 확장한다. 그래서 `for` 가 돈다([`../20-control-flow-statements/`](../20-control-flow-statements/)).

**통로는 셋**

- `keySet()` → `Set<K>`, `values()` → `Collection<V>`, `entrySet()` → `Set<Map.Entry<K,V>>`.
- javadoc 이 이 셋에 이름을 붙여 놓았다.

> The `Map` interface provides three *collection views*, which allow a map's contents to be viewed as a set of keys, collection of values, or set of key-value mappings.

**`Map` 이 `Collection<Entry>` 였다면**

- **`add(Entry)` 가 정의 불가능해진다.** 이미 있는 키를 담은 `Entry` 를 `add` 하면 무엇을 해야 하나.
  - 덮어쓴다? 그러면 `Collection.add` 의 "원소가 하나 늘어난다"는 기대가 깨진다.
  - 거부한다? 그러면 `Set.add` 처럼 `false` 를 줘야 하는데, `Set` 의 기준은 `equals` 이지 **키만** 보는 것이 아니다.
- `addAll`·`contains`·`remove` 도 같은 문제를 겪는다. 자바는 **이어 붙이지 않는 쪽**을 골랐다.

### 2. 같은 데이터를 여섯 곳에 담으면

**출력** (`Ex.java` — 39-b, 17·21·25 동일)

```text
--- 같은 것을 넣었을 때의 순서
입력             : [pear, apple, fig, apple, date]
ArrayList        : [pear, apple, fig, apple, date]
HashSet          : [date, apple, pear, fig]
LinkedHashSet    : [pear, apple, fig, date]
TreeSet          : [apple, date, fig, pear]
ArrayDeque       : [pear, apple, fig, apple, date]
PriorityQueue(toString) : [apple, apple, fig, pear, date]
PriorityQueue(poll 순서) : [apple, apple, date, fig, pear]
```

**크기**

```text
  ArrayList        5     <- 중복을 남긴다
  ArrayDeque       5     <- 중복을 남긴다
  PriorityQueue    5     <- 중복을 남긴다
  HashSet          4     <- apple 하나가 사라진다
  LinkedHashSet    4
  TreeSet          4
```

**`toString` 과 `poll` 순서는 다르다**

- `toString` : `[apple, apple, fig, pear, date]` — **`date` 가 끝에 있다.** 정렬이 아니다.
- `poll` 순서 : `[apple, apple, date, fig, pear]` — 이것만 정렬이다.
- 이유는 `toString` 이 **힙 배열을 그대로** 찍기 때문이다. 힙은 부모 ≤ 자식만 지킨다.

**javadoc 이 순서를 약속하는 것**

| 컬렉션 | 순서 약속 | 근거 |
|---|---|---|
| `ArrayList` | **있다** — 넣은 순서 | `List` 계약(위치가 있는 컬렉션) |
| `LinkedHashSet` | **있다** — 넣은 순서 | `LinkedHashSet` javadoc |
| `TreeSet` | **있다** — 정렬 순서 | `SortedSet` 계약 |
| `ArrayDeque` | **있다** — 넣은 순서 | `Deque` 계약 |
| `HashSet` | **없다** | "makes no guarantees as to the iteration order of the set" |
| `PriorityQueue` | **없다**(순회는) | "the Iterator ... is not guaranteed to traverse the elements in any particular order" |

**세 JDK 에서 같았다면 테스트에 적어도 되나**

- **안 된다.** 그것은 관찰이고, 계약은 javadoc 이다.
- 여기서는 `HashSet` 의 `[date, apple, pear, fig]` 가 **17·21·25 에서 한 글자도 같았다.**\
  ★ **똑같아서 더 위험하다** — 우연히 통과하는 테스트는 "맞는 테스트"처럼 보인다.
- 순서를 비교해야 하면 `LinkedHashSet`·`TreeSet` 을 쓰거나, 비교 전에 정렬한다.

### 3. `null` 은 어디까지 들어가나

**출력** (`Ex.java` — 39-b, 17·21·25 동일)

```text
--- null 원소를 받나 (Collection)
ArrayList.add(null)      : OK
LinkedList.add(null)     : OK
HashSet.add(null)        : OK
LinkedHashSet.add(null)  : OK
TreeSet.add(null)        : java.lang.NullPointerException: Cannot invoke "java.lang.Comparable.compareTo(Object)" because "k1" is null
ArrayDeque.add(null)     : java.lang.NullPointerException
PriorityQueue.add(null)  : java.lang.NullPointerException
CopyOnWriteArrayList.add(null) : OK
List.of(null)            : java.lang.NullPointerException
--- null 키·값을 받나 (Map)
HashMap.put(null, 1)     : OK
HashMap.put("a", null)   : OK
LinkedHashMap.put(null,1): OK
TreeMap.put(null, 1)     : java.lang.NullPointerException: Cannot invoke "java.lang.Comparable.compareTo(Object)" because "k1" is null
TreeMap.put("a", null)   : OK
Hashtable.put(null, 1)   : java.lang.NullPointerException: Cannot invoke "Object.hashCode()" because "key" is null
Hashtable.put("a", null) : java.lang.NullPointerException
ConcurrentHashMap.put(null,1) : java.lang.NullPointerException
ConcurrentHashMap.put("a",null) : java.lang.NullPointerException
```

**던지는 것과 그 이유 — 세 갈래**

```text
(1) 비교해야 한다            (2) null 을 신호로 쓴다        (3) 동시성에서 구분이 안 된다

  TreeSet.add(null)            ArrayDeque.add(null)          ConcurrentHashMap (키·값 둘 다)
  TreeMap.put(null, 1)         PriorityQueue.add(null)       Hashtable (키·값 둘 다)
        |                            |                             |
  compareTo 를 불러야 하는데    poll()/peek() 가 비었을 때     get 이 null 을 주면
  null.compareTo 가 없다        null 을 돌려준다               "없음"인지 "null 값"인지
        |                            |                        확인할 방법이 원자적이지 않다
  메시지가 그대로 말한다         원소로도 null 이면 구분 불가
```

- `TreeMap.put("a", null)` 은 **통과한다.** 비교하는 것은 **키**뿐이다.
- `List.of(null)` 은 (1)~(3)과 다른 넷째 이유다 — **불변 컬렉션 계약이 `null` 을 금지**한다([`../40-list-set-and-immutable-factories/`](../40-list-set-and-immutable-factories/)).

**`ArrayDeque` 가 거부하는 이유**

- `poll()`·`peek()`·`pollFirst()` 가 **비었을 때 `null` 을 돌려준다.**
- 원소로 `null` 이 들어가면 `poll()` 의 `null` 이 "비었다"인지 "`null` 원소를 꺼냈다"인지 알 수 없다.
- 그래서 `ArrayDeque` javadoc 이 "Null elements are prohibited" 라고 못박는다.

**`Hashtable` 의 메시지가 다른 이유**

```text
키가 null                                        값이 null
Cannot invoke "Object.hashCode()"                (메시지 없음)
  because "key" is null                            |
        |                                    코드가 명시적으로
JVM 이 만든 helpful NullPointerException      throw new NullPointerException()
(key.hashCode() 를 부르다 터졌다)              을 던진다
```

- **키 쪽은 JVM 이 만든 문구**다(helpful NullPointerException, JDK 14+).
- **값 쪽은 코드가 직접 던진 것**이라 문구가 없다.
- 그래서 **어느 쪽이 `null` 이었는지 메시지로 구분된다.**

### 4. 같은 `List` 인데 능력이 다르다

**출력** (`Ex.java` — 39-c, 17·21·25 동일 — 스택트레이스 줄 번호만 다르다)

```text
--- 같은 List 인터페이스, 다른 능력
                               add          set(0,z)     remove(0)   
new ArrayList<>()              OK           OK           OK          
Arrays.asList(...)             UOE          OK           UOE         
List.of(...)                   UOE          UOE          UOE         
Collections.unmodifiableList   UOE          UOE          UOE         
Collections.emptyList()        UOE          UOE          UOE         
addAll(빈 컬렉션) 은?  List.of  : java.lang.UnsupportedOperationException
addAll(빈 컬렉션) 은?  asList   : OK
clear() 는?            asList   : java.lang.UnsupportedOperationException
```

**성공하는 칸**

- `ArrayList` 의 세 칸 전부.
- **`Arrays.asList` 의 `set` 한 칸.**

**`Arrays.asList` 만 특이한 칸**

```text
  Arrays.asList(배열)  =  배열 위에 씌운 List 뷰

  [a][b][c]   <- 길이가 고정된 배열
   ^
   |
  set(0, "z") 은 배열 칸을 덮어쓰면 된다 -> 된다
  add("z")   는 배열을 늘려야 한다      -> 못 한다 -> UOE
  remove(0)  은 배열을 줄여야 한다      -> 못 한다 -> UOE
```

- **길이를 바꾸지 않는 연산만 된다.** 그것이 배열 뷰의 정확한 능력이다.

**`addAll(빈 컬렉션)` 은 결과가 다르다**

- `List.of(...).addAll(List.of())` → **`UnsupportedOperationException`**.
- `Arrays.asList(...).addAll(List.of())` → **`OK`** (아무 일도 안 일어난다).
- `Arrays.asList` 는 `AbstractCollection.addAll` 을 그대로 쓰는데, 그 구현은 **원소를 돌며 `add` 를 부른다.**
  원소가 없으니 `add` 가 한 번도 안 불리고, 그래서 안 던진다.
- `List.of` 는 `addAll` 자체를 재정의해 **무조건 던진다.**

**그 차이를 허용하는 javadoc**

> Such methods should (but are not required to) throw an `UnsupportedOperationException` if the invocation would have no effect on the collection. For example, consider a collection that does not support the `add` operation. What will happen if the `addAll` method is invoked on this collection, with an empty collection as the argument? The addition of zero elements has no effect, so it is permissible for this collection simply to do nothing and not to throw an exception. However, it is recommended that such cases throw an exception unconditionally, as throwing only in certain cases can lead to programming errors.

- **`List.of` 가 권고를 따랐고 `Arrays.asList` 는 안 따랐다.** 위 출력이 그 차이 그대로다.

**이 설계의 이름과 대가**

- 이름은 **옵셔널 연산(optional operation)** 이다.
- **얻은 것** — 인터페이스 하나(`List`)로 가변 리스트·배열 뷰·불변 리스트·빈 리스트를 전부 덮는다.\
  호출하는 코드는 그 차이를 몰라도 된다.
- **잃은 것** — **컴파일러가 막지 못한다.** 선언 타입에 `add` 가 있으니 컴파일은 통과하고 런타임에 죽는다.
- 스택트레이스가 어느 구현인지 말해 준다.

```text
List.of("a").add("z")                          Arrays.asList("a").add("z")
java.lang.UnsupportedOperationException        java.lang.UnsupportedOperationException
  at java.util.ImmutableCollections.uoe          at java.util.AbstractList.add
  at ImmutableCollections$Abstract...add         at java.util.AbstractList.add
```

### 5. `TreeSet` 에 내 타입을 넣으면

**출력** (`Ex.java` — 39-b, 17·21·25 동일)

```text
--- 정렬 컬렉션은 Comparable 을 요구한다
TreeSet 에 P 넣기 : java.lang.ClassCastException: class Ex$1P cannot be cast to class java.lang.Comparable (Ex$1P is in unnamed module of loader 'app'; java.lang.Comparable is in module java.base of loader 'bootstrap')
TreeMap 에 P 키   : java.lang.ClassCastException: class Ex$1P cannot be cast to class java.lang.Comparable (Ex$1P is in unnamed module of loader 'app'; java.lang.Comparable is in module java.base of loader 'bootstrap')
TreeMap 에 P 키 1개 : java.lang.ClassCastException: class Ex$1P cannot be cast to class java.lang.Comparable (Ex$1P is in unnamed module of loader 'app'; java.lang.Comparable is in module java.base of loader 'bootstrap')
HashSet 에 P 넣기 : OK
```

**컴파일 에러가 아니라 런타임이다**

- `ClassCastException` — `java.lang.RuntimeException` 의 하위다.
- 컴파일은 통과한다. `TreeSet<E>` 의 타입 파라미터에 `E extends Comparable<E>` 바운드가 **없기 때문**이다.\
  바운드를 걸면 비교자를 주는 사용법(`new TreeSet<>(cmp)`)을 막게 된다.

**키가 하나뿐일 때도 던진다**

```java
Map<Object,Integer> m = new TreeMap<>();
m.put(new P("a"), 1);      // 이것만으로 ClassCastException
```

- `TreeMap.put` 이 트리가 비었을 때 `compare(key, key)` 를 한 번 부른다 — **타입 검사를 겸한 호출**이다.
- 그래서 "원소가 둘 이상일 때만 터진다"가 아니다. **첫 삽입에서 터진다.**
- ★ 이것이 위험한 이유: **빈 목록이면 안 터진다.** 테스트가 통과하고 운영에서 죽는다.

**두 컬렉션이 요구하는 계약이 다르다**

```text
   HashSet / HashMap                    TreeSet / TreeMap

  hashCode() 로 자리를 찾고             compareTo() 또는 Comparator 로
  equals() 로 같은지 본다                 순서를 정한다
        |                                     |
  Object 에 둘 다 이미 있다             P 에는 없다
  -> 아무 타입이나 들어간다              -> Comparable 을 구현하거나 비교자를 줘야 한다
        |                                     |
  다만 계약을 지켜야 제대로 동작한다      다만 전순서를 지켜야 제대로 동작한다
  (27번)                                (28번)
```

**고치는 방법 — 둘**

```java
// 1) 타입이 Comparable 을 구현한다
record P(String n) implements Comparable<P> {
    public int compareTo(P o) { return n.compareTo(o.n); }
}

// 2) 비교자를 생성자에 준다 — 타입을 못 고칠 때
new TreeSet<>(Comparator.comparing(P::n));
new TreeMap<>(Comparator.comparing(P::n));
```

- 계약의 조항과 위반 증상은 [`../28-comparable-comparator/`](../28-comparable-comparator/) 가 정본이다.

### 6. 계층에서 누가 누구를 확장하나

**출력** (`Ex.java` — 39-a, 21·25 동일)

```text
--- 인터페이스가 직접 확장하는 것
Collection         -> [Iterable]
List               -> [SequencedCollection]
Set                -> [Collection]
SortedSet          -> [Set, SequencedSet]
NavigableSet       -> [SortedSet]
Queue              -> [Collection]
Deque              -> [Queue, SequencedCollection]
Map                -> []
SortedMap          -> [SequencedMap]
NavigableMap       -> [SortedMap]
SequencedCollection -> [Collection]
SequencedSet       -> [SequencedCollection, Set]
SequencedMap       -> [Map]
```

**`List` 는 `Collection` 을 직접 확장하지 않는다**

- **21부터** `SequencedCollection` 을 거친다. 17 에서는 `List -> [Collection]` 이었다.
- `Collection` 의 하위인 것은 변함없다 — 한 칸이 중간에 끼워 넣어진 것이다.

**`SortedSet` 은 둘을 확장한다**

- `[Set, SequencedSet]`. 인터페이스는 다중 상속이 된다([`../11-interfaces-default-methods/`](../11-interfaces-default-methods/)).

**`ArrayDeque` 는 `List` 가 아니다**

```text
ArrayDeque : Collection=true Queue=true Deque=true List=false
```

- 양끝만 열려 있고 **인덱스 접근이 없다.** `get(int)` 가 없다.

**`LinkedList` 는 둘 다다**

```text
LinkedList -> [List, Deque, Cloneable, Serializable]
```

- 그래서 리스트로도 큐로도 스택으로도 쓸 수 있다.

**`PriorityQueue` 에 `Queue` 가 안 보이는 이유**

- `getInterfaces()` 는 **그 클래스 선언에 적힌 것만** 돌려준다.
- `PriorityQueue extends AbstractQueue<E>` 이고 `AbstractQueue implements Queue<E>` 다.
- **상속으로 들어온 인터페이스는 안 나온다.** `instanceof Queue` 로 물으면 `true` 다.

### 7. 다섯 질문으로 고른다

| 요구 | 고르는 것 | 결정적 질문 |
|---|---|---|
| 로그 줄을 읽은 순서대로 | **`ArrayList`** | 순서 O · 중복 O |
| 방문 URL 을 중복 없이 방문 순서대로 | **`LinkedHashSet`** | 중복 X · 순서 O |
| 사용자 ID 로 객체 찾기 | **`HashMap`** | 키-값 · 순서 불필요 |
| 마감이 임박한 것부터 | **`PriorityQueue`** | 꺼내는 순서만 정렬 |
| 요일(`enum`)별 설정값 | **`EnumMap`** | 키가 `enum` |
| 여러 스레드가 카운터를 올린다 | **`ConcurrentHashMap`** | 동시성 |
| 점수 범위 질의 | **`TreeMap`** | `subMap(80, 90)` 이 필요하다 |

- 마지막 것만 설명이 필요하다. **범위 질의는 `TreeMap`/`TreeSet` 만 할 수 있다.**\
  `subMap`·`headMap`·`tailMap`·`floorKey`·`ceilingKey` 는 `NavigableMap` 의 메서드다.
- `ConcurrentHashMap` 의 카운터는 `merge(k, 1, Integer::sum)` 또는 `LongAdder` 를 쓴다([**55번 주제**](../55-atomics-and-concurrent-collections/)).
- `EnumMap` 은 배열 인덱스로 동작해 해시를 쓰지 않는다 — [`../13-enum-classes/`](../13-enum-classes/) 가 정본이다.

### 8. 선언 타입을 무엇으로 두나

**기본은 `List<String> b = new ArrayList<>()`**

- 선언은 인터페이스로, 생성은 구현체로. 구현체를 바꿀 때 **선언 줄 하나만** 고친다.
- `ArrayList<String> a = ...` 로 적으면 `LinkedList` 로 못 바꾼다.

**`c.get(0)` 은 컴파일 안 된다** (`Ex.java` — 39-d, JDK 21)

```text
Ex.java:8: error: cannot find symbol
        System.out.println(c.get(0));
                            ^
  symbol:   method get(int)
  location: variable c of type Collection<String>
```

- 실제 객체가 `ArrayList` 여도 **선언 타입이 `Collection` 이면 없는 메서드**다.
- 인덱스는 `List` 의 개념이다.

**반환 타입을 `ArrayList` 로 적으면**

- 호출자가 `ArrayList` 의 능력(가변·`RandomAccess`)에 기대기 시작한다.
- 나중에 `List.of(...)` 나 불변 리스트로 바꾸면 **호출자 코드가 전부 깨진다.**
- 반환 타입은 **약속할 만큼만** 넓게 적는다.

**`LinkedHashMap` 으로 선언해야 하는 때**

- **순서가 계약의 일부일 때.** "응답 JSON 의 키 순서가 입력 순서와 같아야 한다" 같은 요구.
- `Map` 으로 선언하면 다음 사람이 `HashMap` 으로 바꿔도 컴파일이 되고, 순서 요구가 조용히 깨진다.
- 21부터는 `SequencedMap` 으로 선언하는 선택지가 생겼다([`../42-sequenced-collections/`](../42-sequenced-collections/)).

### 9. `Map` 을 도는 네 형태

**기본은 `entrySet()`**

- 키와 값을 **한 번에** 얻는다. 조회가 한 번이다.

**첫 줄이 낭비인 이유**

```text
for (String k : m.keySet()) { m.get(k); }

  keySet 순회      -> 노드를 하나씩 찾는다
  m.get(k)         -> 해시를 다시 계산하고 버킷을 다시 찾는다
        |
  같은 노드를 두 번 찾는다
```

- `entrySet()` 은 순회하면서 노드를 이미 들고 있으므로 다시 찾지 않는다.

**`Map.Entry` 와 `Map`**

- `Map.Entry` 는 **한 칸**(키 하나 + 값 하나), `Map` 은 **칸 전체**다.
- `Entry` 에는 `getKey()`·`getValue()`·`setValue()` 셋뿐이다.
- `entrySet()` 이 돌려주는 `Entry` 는 **뷰**라서 `setValue` 가 맵에 쓴다 — [`../41-map-api-merge-compute/`](../41-map-api-merge-compute/) 가 정본이다.

**`Map` 이 `Iterable` 이 아님을 가장 잘 드러내는 것**

- 앞의 셋 전부다. **`for (x : m)` 이 아니라 `for (x : m.무엇인가())` 라는 것** 자체가 그 증거다.
- `m.forEach((k,v) -> ...)` 는 `Map` 자신의 메서드라 뷰를 안 거친다 — 다만 이것도 `Iterable` 과는 무관하다.

### 10. 무엇이 보장이고 무엇이 구현 세부인가

| 관측 | 보장? | 근거 |
|---|---|---|
| `HashMap` 의 키 순서 | **아니다** | `HashMap` javadoc — "makes no guarantees as to the order of the map; in particular, it does not guarantee that the order will remain constant over time" |
| `LinkedHashSet` 의 순서 | **그렇다** | `LinkedHashSet` javadoc — 삽입 순서 |
| `TreeSet.add(null)` 의 NPE **메시지 문구** | **아니다** | JVM 의 helpful NullPointerException 이 만든 문장이다. NPE 가 난다는 것만 계약 |
| `List.of(...)` 의 구체 타입 | **아니다** | `ImmutableCollections$List12` 는 문서화되지 않은 내부 클래스다 |

**"17·21·25 에서 같았다"가 되는 근거 / 안 되는 근거**

```text
  근거가 된다                           근거가 안 된다

  "이 세 버전에서 재현했다"              "앞으로도 그럴 것이다"
  "버전 차이 때문은 아니다"              "이것이 계약이다"
        |                                     |
  실행 검증 표에 적는다                  테스트에 assert 로 적지 않는다
```

- ★ 실제로 `HashSet` 의 순서가 세 버전에서 **한 글자도 같았다.** 그래서 더 위험하다.
- 같다는 관찰은 **관찰로 적고**, 보장은 **javadoc 으로만** 적는다.

### 11. 스택이 필요하다

**출력** (`Ex.java` — 39-e, 17·21·25 동일)

```text
--- 스택을 세 가지로 만들면 순회 순서가 갈린다
넣은 순서            : [pear, apple, fig]
Stack  toString      : [pear, apple, fig]
ArrayDeque toString  : [fig, apple, pear]
LinkedList toString  : [fig, apple, pear]
Stack  순회          : pear apple fig 
ArrayDeque 순회      : fig apple pear 
LinkedList 순회      : fig apple pear 
Stack  pop 순서      : fig apple pear
ArrayDeque pop 순서  : fig apple pear
--- Stack 은 Vector 의 하위 클래스다
Stack 의 상위 클래스 : java.util.Vector
Stack 은 List 인가   : true
List 로서 가운데 삽입 : [z, a, b] / pop = b / 남은 것 [z, a]
```

**`toString`**

- `Stack` : **`[pear, apple, fig]`** — 넣은 순서 그대로.
- `ArrayDeque` : **`[fig, apple, pear]`** — 마지막에 넣은 것이 앞이다.

**향상된 `for`**

- `Stack` : `pear apple fig`
- `ArrayDeque` : `fig apple pear`

**`pop` 순서 — 둘이 같다**

- 둘 다 **`fig apple pear`** 다. **꺼내는 동작은 같다.**

**`Stack` 만 어긋나는 것**

```text
                 순회 순서        pop 순서

  Stack          pear apple fig   fig apple pear    <- 반대다
  ArrayDeque     fig apple pear   fig apple pear    <- 같다
```

- **`Stack` 의 순회 순서가 `pop` 순서와 반대**다.
- 이유는 `Stack` 이 **`Vector` 를 상속**해 배열을 인덱스 0부터 찍기 때문이다.
  `push` 는 배열 끝에 붙이므로, 마지막에 넣은 것이 **마지막에 순회**된다.
- 그래서 **로그로 찍은 순서와 실제 처리 순서가 다르다.** 디버깅에서 사람을 속인다.

**상위 클래스와 `add(0, "z")`**

- 상위 클래스는 **`java.util.Vector`** 이고 `Stack instanceof List` 가 **`true`** 다.
- 그래서 **`st.add(0, "z")` 가 컴파일되고 동작한다** — `[z, a, b]` 가 되고 `pop` 은 여전히 `b` 다.
- **"끝에서만 넣고 뺀다"는 스택의 불변식이 타입으로 지켜지지 않는다.**

**새 코드에서는**

- **`ArrayDeque`** 다. 순회 순서가 `pop` 순서와 같고, `List` 가 아니라 가운데 삽입이 애초에 컴파일 안 된다.
- 단 **`null` 을 못 넣는다**(3번). 그 하나만 주의한다.
- `Stack`·`Vector` 는 모든 메서드가 `synchronized` 라 혼자 쓸 때도 비용을 낸다.

### 12. 이 주제의 경계

| 질문 | 정본 |
|---|---|
| 해시 충돌이 나면 버킷에서 무슨 일이 나나 | [`../../../../../data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/) · [`../../../../../data-structure/29-open-addressing/`](../../../../../data-structure/29-open-addressing/) |
| `HashMap` 과 `TreeMap` 중 무엇을 고르나 | **여기(39번)** |
| `SequencedCollection` 이 왜 21에 들어왔나 | [`../../../../../../history/java/java-21.md`](../../../../../../history/java/java-21.md) (JEP 431 의 맥락) |
| `getFirst()` 를 어떻게 쓰나 | [`../42-sequenced-collections/`](../42-sequenced-collections/) |
| `equals` 를 깨면 `HashMap` 에서 무슨 일이 나나 | [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) |

- 한 줄로 갈라 보면 이렇다.\
  **자료구조가 어떻게 만들어져 있나 = `data-structure/`,
  언제·왜 들어왔나 = `history/`,
  어느 것을 왜 고르나 = 여기.**

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Ex.java` (39-a) | `Collection`/`Map` 의 무관계, 인터페이스가 확장하는 것, 구현체가 구현하는 것, `instanceof` 소속 | 21 · 25 (**출력 동일**) / **17 은 컴파일 불가**(`SequencedCollection` 없음) |
| `Ex.java` (39-b) | `null` 허용 9+9칸, 같은 입력의 순서 7종, `PriorityQueue` 의 `toString` 대 `poll`, `TreeSet`/`TreeMap` 의 `ClassCastException` | 17 · 21 · 25 (**출력 동일**) |
| `Ex.java` (39-c) | 옵셔널 연산 5×3 격자, `addAll(빈 컬렉션)` 의 갈림, UOE 스택트레이스, 구체 타입 | 17 · 21 · 25 (**본문 동일 · 스택트레이스 줄 번호만 다름**) |
| `Ex.java` (39-e) | `Stack`·`ArrayDeque`·`LinkedList` 의 `toString`/순회/`pop` 순서, `Stack` 의 상위 클래스와 `List` 성질, `Collections.synchronizedMap` 의 복합 연산 | 17 · 21 · 25 (**출력 동일**) |
| `Ex.java` (39-d) | `for (x : map)` 과 `Collection.get(int)` 의 컴파일 에러 | 21 (컴파일만) |
| `src.zip` 열람 | `Collection` 의 「Unmodifiable Collections」·「View Collections」·`optional-restrictions`, `Map` 클래스 javadoc, `SequencedCollection` 의 `@since 21` | 21 |

**javac 13회 · java 11회** (17 에서의 39-a 컴파일 실패 1회 포함).

**버전별로 갈린 것**

```text
39-a : 17 에서 컴파일이 안 된다
  Ex.java:... error: cannot find symbol  symbol: class SequencedCollection
  -> 이 프로그램은 21·25 에서만 돌렸다

39-c : 스택트레이스 줄 번호만 갈린다
  17: AbstractList.add(AbstractList.java:153)        21·25: (:155)
  21: ImmutableCollections.uoe(...:142)              25:    (:159)
  -> 본문 출력(UOE 격자)은 세 버전이 한 글자도 같다

39-b · 39-e : 세 버전 출력이 한 글자도 같다 — HashSet 의 순회 순서까지 같다
  -> 같다는 것이 보장의 근거가 아니다 (10번)
```

**구현 의존 항목** (버전이 오르면 다시 돌려야 하는 것)

- `HashSet`·`HashMap` 의 순회 순서 — javadoc 이 명시적으로 보장하지 않는다.
- `PriorityQueue.toString` 의 배열 순서 — 힙 배치에 달려 있다.
- 구체 타입 문자열(`java.util.Arrays$ArrayList`·`ImmutableCollections$List12` 등).
- NPE·UOE 의 **메시지 문구**와 스택트레이스 줄 번호.
- `getInterfaces()` 의 결과 — 계층이 또 바뀌면 달라진다(21 에서 실제로 바뀌었다).
- **Java 8 은 안 돌려 봄** — 이 머신에 8이 없다. `List.of`(9+)는 애초에 8에 없다.
