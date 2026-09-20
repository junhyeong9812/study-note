# java/syntax/39 — 컬렉션 프레임워크 지도: 인터페이스 계층과 구현체 선택 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **선행** — [`../17-generic-declarations/`](../17-generic-declarations/). 컬렉션은 전부 제네릭 타입이라 `List<String>` 의 `<String>` 이 무엇인지가 전제다.
> **기준 소스** — JDK 21.0.5 의 `lib/src.zip` 을 **직접 풀어 읽은** javadoc 과 구현이다.\
> `java.base/java/util/Collection.java` — 「Unmodifiable Collections」·「View Collections」·`optional-restrictions` 절.\
> `java.base/java/util/Map.java` — 클래스 javadoc(컬렉션 뷰 셋·가변 키 경고)·`get` 의 `null` 모호성 서술.\
> `java.base/java/util/SequencedCollection.java` — `@since 21` 과 encounter order 정의.\
> 인용은 **그 파일에서 복사한 것만** 옮겼다.
> **실행 검증** — 이 문서의 모든 출력·에러는 Temurin JDK 에서 **실제로 돌려** 얻은 것이다.\
> 도는 프로그램 4개 + 컴파일 에러용 1개. `SequencedCollection` 을 쓰는 하나만 **21.0.5 · 25.0.1** 에서,\
> 나머지 셋은 **17.0.13 · 21.0.5 · 25.0.1** 셋 다에서 돌렸다.\
> 세 버전의 출력 차이는 [`3-answer.md`](3-answer.md) 의 「실행 검증」 표에 적었다.
> **버전** — `Collection`·`Map`·`List`·`Set` 은 **Java 1.2**. `Deque` 는 **6**. `removeIf`·`stream()` 은 **8**.\
> `List.of`·`Set.of`·`Map.of` 는 **9**, `copyOf` 는 **10**, `SequencedCollection` 은 **21**(`@since` 를 `src.zip` 에서 직접 읽었다).
> **범위** — **자료구조의 원리는 여기가 아니다.**\
> 해시 테이블이 어떻게 동작하나, 적흑 트리가 어떻게 회전하나, 동적 배열의 상각 분석은
> [`../../../../../data-structure/`](../../../../../data-structure/) 35편이 정본이다.\
> 그쪽은 **자료구조가 어떻게 만들어져 있나**까지, 여기는 **자바가 그것을 어떤 인터페이스로 노출하고 어느 구현체를 왜 고르나**부터다.
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**컬렉션 프레임워크는 창고의 「보관 방식 카탈로그」다.**

물건을 맡기러 창고에 가면 직원이 이렇게 묻는다.

| 비유 | 실체 |
|---|---|
| "꺼낼 때 넣은 순서대로 필요하세요?" | **순서(encounter order)가 필요한가** — `List`·`LinkedHashSet` 대 `HashSet` |
| "같은 물건 두 개를 따로 세나요?" | **중복을 허용하는가** — `List` 대 `Set` |
| "가나다순으로 정리해 둘까요?" | **정렬이 필요한가** — `TreeSet`·`TreeMap` |
| "이름표 없는 물건도 받나요?" | **`null` 을 허용하는가** — `HashMap` 대 `TreeMap` |
| "여러 직원이 동시에 손댑니까?" | **동시성이 필요한가** — `ConcurrentHashMap` |
| **물건만 맡기는 창구** | **`Collection`** — 원소만 담는다 |
| **번호표를 붙여 맡기는 창구** | **`Map`** — 키와 값을 짝지어 담는다 |
| "이 창구에서는 반품이 안 됩니다" | **옵셔널 연산** — `UnsupportedOperationException` |

**똑같은 구조로** 자바가 동작한다: 카탈로그 = 인터페이스 계층, 창구 = `Collection`/`Map`,
"이 창구에서는 안 됩니다" = 선언 타입에는 있는데 런타임에 던지는 메서드.

핵심은 **창구가 둘이라는 것**이다.

```text
        Iterable            (for 문이 도는 것)
            |
            v
       Collection                           Map
            |                                |
   +--------+--------+            +----------+----------+
   |        |        |            |          |          |
  List     Set     Queue       HashMap  LinkedHashMap  TreeMap
                                   |
                            keySet()/values()/entrySet()
                                   |
                                   v
                              Collection 으로 돌아온다
```

- **`Map` 은 `Collection` 이 아니다.** 상속 관계가 아예 없다 — 형제도 아니다.
- `Map` 을 `for` 로 돌 수 없는 이유가 이것이다. `Iterable` 이 아니기 때문이다.
- 대신 `Map` 은 **자기 내용을 `Collection` 으로 보여 주는 뷰 셋**을 준다.

실무에서 이 지도가 필요해지는 자리는 **"여기에 뭘 써야 하지?"** 한 줄이다.\
`ArrayList` 를 기본으로 쓰다가 중복이 문제가 되고, `HashMap` 을 쓰다가 순서가 문제가 된다.

> **컬렉션 프레임워크(Collections Framework)** — `java.util` 이 제공하는 자료구조 인터페이스와 구현체 묶음.\
> 예: `List` 라는 인터페이스와 그것을 구현한 `ArrayList`·`LinkedList` 가 한 묶음이다.

> **인터페이스 대 구현체** — 인터페이스는 "무엇을 할 수 있나", 구현체는 "어떻게 하나".\
> 예: `List` 는 "순서대로 담고 인덱스로 꺼낸다"까지만 약속하고, `ArrayList` 가 "배열로 그렇게 한다"를 맡는다.

## 이 주제가 답하려는 질문

원고가 없는 API 주제라 「문제」 대신 이 세 질문을 둔다.

1. `Collection` 과 `Map` 은 **왜 형제가 아닌가** — 그 결과 코드에서 무엇이 달라지나.
2. 요구(순서·중복·정렬·`null`·동시성)를 받았을 때 **어느 구현체를 고르나** — 무엇을 보고 고르나.
3. 인터페이스 하나에 여러 구현체를 매달기 위해 자바가 치른 대가는 무엇인가 —
   **왜 컴파일되는 코드가 `UnsupportedOperationException` 으로 죽나.**

## 예시 데이터 — 이 묶음이 공유하는 것

39~43번은 같은 데이터를 쓴다. 주제를 건너다니며 읽을 때 비교가 공짜로 따라온다.

```text
과일 다섯 개 (중복 하나)

  "pear"  "apple"  "fig"  "apple"  "date"

  - 중복 확인용  : "apple" 이 두 번
  - 정렬 확인용  : 사전순은 apple date fig pear
  - 길이(값) 확인용 : pear=4 apple=5 fig=3 date=4
```

- 39번은 **어느 컨테이너에 담을지**를 고른다.
- 40번은 담은 뒤 **`List`·`Set` 의 API** 를 쓴다.
- 41번은 **키-값으로** 담는다.
- 42·43번은 담긴 것을 **순서대로 / 하나씩** 꺼낸다.

## 동작 방식

### (1) 계층의 첫 갈림 — `Collection` 과 `Map` 은 이어져 있지 않다

**언제 쓰나** — "이 메서드 파라미터를 `Collection` 으로 열어 둘까 `Map` 으로 둘까"를 정할 때.

**실행 결과** (`Ex.java` — 39-a, 21·25 동일)

```text
--- Collection 과 Map 은 형제인가
Collection.isAssignableFrom(Map)  : false
Map.isAssignableFrom(Collection)  : false
Collection 의 상위 인터페이스     : [interface java.lang.Iterable]
Map 의 상위 인터페이스            : []
```

```text
      전 상태 — 흔한 오해                 후 상태 — 실제

      "컬렉션"                            Iterable
          |                                  |
    +-----+-----+                       Collection            Map
    |           |                            |             (상위 없음)
Collection     Map                    List  Set  Queue
                                                          keySet()  -> Set
   (이어져 있다고 믿는다)                (이어져 있지 않다)  values()  -> Collection
                                                          entrySet()-> Set<Entry>
```

그림 해설 (한 단계씩):

- `Map` 의 **상위 인터페이스 목록이 비어 있다.** `Object` 외에 아무것도 확장하지 않는다.
- `Collection` 은 `Iterable` 하나만 확장한다. 그래서 향상된 `for` 가 `Collection` 에만 돈다.
- `Map` 은 대신 **세 개의 뷰**로 `Collection` 세계와 이어진다 — `keySet`·`values`·`entrySet`.
- javadoc 이 그 셋을 "collection views" 라고 이름 붙여 놓았다.

> The `Map` interface provides three *collection views*, which allow a map's contents to be viewed as a set of keys, collection of values, or set of key-value mappings.

- 그래서 `for (String k : map)` 은 **컴파일이 안 된다.**

```text
$ javac Ex.java
Ex.java:6: error: for-each not applicable to expression type
        for (String s : m) System.out.println(s);
                        ^
  required: array or java.lang.Iterable
  found:    Map<String,Integer>
```

비용 — `Map` 을 `Collection` 처럼 다루는 유틸리티를 쓸 수 없다.\
`Collections.unmodifiableCollection` 은 `Map` 에 못 쓰고, `Collections.unmodifiableMap` 이 따로 있다.\
대신 `Map` 은 **키의 유일성**이라는, `Collection` 이 약속할 수 없는 계약을 가질 수 있다.

### (2) 계층의 실제 모양 — 어느 인터페이스가 무엇을 확장하나

**언제 쓰나** — API 시그니처에 어느 타입을 쓸지 고를 때. 좁게 쓸수록 약속이 강해진다.

**실행 결과** (`Ex.java` — 39-a, 21·25 동일)

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

```text
Iterable
   |
Collection ──────────────────────────────┐
   |                                     |
SequencedCollection                     Set
   |          \                          |
 List        Deque              SequencedSet ── SortedSet ── NavigableSet
              |                                        (Sequenced 쪽에서도 옴)
            Queue

Map
 |
SequencedMap ── SortedMap ── NavigableMap
```

그림 해설 (한 단계씩):

- **`List` 는 `Collection` 을 직접 확장하지 않는다.** 21부터 `SequencedCollection` 을 거친다.
- `Deque` 도 마찬가지다 — `Queue` 와 `SequencedCollection` 둘을 확장한다.
- `SortedSet` 은 `Set` 과 `SequencedSet` **둘을** 확장한다. 다중 상속이 인터페이스에서는 된다([**11번 주제**](../11-interfaces-default-methods/)).
- 21에서 `SequencedCollection` 이 **기존 계층 중간에 끼워 넣어졌다.** 그 사정은 [`../42-sequenced-collections/`](../42-sequenced-collections/) 가 정본이다.

비용 — 계층이 깊어지면 "이 타입이 저 타입인가"를 머리로 못 센다.\
그래서 확인은 `instanceof` 로 **돌려서** 한다 — 아래가 그 결과다.

**실행 결과** (`Ex.java` — 39-a, 21·25 동일)

```text
--- instanceof 로 본 소속
ArrayList  : Collection=true List=true SequencedCollection=true Map=false
HashSet    : Collection=true Set=true SequencedCollection=false
ArrayDeque : Collection=true Queue=true Deque=true List=false
HashMap    : Collection=false Map=true SequencedMap=false
LinkedHashMap : SequencedMap=true
TreeMap       : SequencedMap=true
```

- **`ArrayDeque` 는 `List` 가 아니다.** 양끝만 열려 있고 인덱스 접근이 없다.
- **`HashSet` 은 `SequencedCollection` 이 아니다.** 순서 개념 자체가 없기 때문이다.

### (3) 구현체가 무엇을 구현하나 — 이름이 비슷해도 소속이 다르다

**언제 쓰나** — "이 구현체를 저 인터페이스 자리에 넣을 수 있나"를 판단할 때.

**실행 결과** (`Ex.java` — 39-a, 21·25 동일)

```text
--- 구현체가 직접 구현하는 것
ArrayList          -> [List, RandomAccess, Cloneable, Serializable]
LinkedList         -> [List, Deque, Cloneable, Serializable]
ArrayDeque         -> [Deque, Cloneable, Serializable]
PriorityQueue      -> [Serializable]
HashSet            -> [Set, Cloneable, Serializable]
LinkedHashSet      -> [SequencedSet, Cloneable, Serializable]
TreeSet            -> [NavigableSet, Cloneable, Serializable]
HashMap            -> [Map, Cloneable, Serializable]
LinkedHashMap      -> [SequencedMap]
TreeMap            -> [NavigableMap, Cloneable, Serializable]
EnumMap            -> [Serializable, Cloneable]
```

```text
 "직접 구현하는 것" 은 선언에 적힌 것만 보여 준다

  PriorityQueue -> [Serializable]      <- Queue 가 안 보인다
        |
        v
  extends AbstractQueue 가 Queue 를 들고 있다 (상속으로 들어온다)

  LinkedHashSet -> [SequencedSet]      <- Set 이 안 보인다
        |
        v
  extends HashSet 이 Set 을, SequencedSet 이 다시 Set 을 들고 있다
```

그림 해설 (한 단계씩):

- 이 목록은 **`getInterfaces()` 의 결과**라 상위 클래스가 들고 온 것은 안 보인다.
- `PriorityQueue` 는 `Queue` 를 **`AbstractQueue` 를 통해** 얻는다 — `instanceof Queue` 는 `true` 다.
- **`LinkedList` 는 `List` 이면서 `Deque` 다.** 그래서 스택·큐·리스트 셋 다로 쓸 수 있다.
- `RandomAccess` 는 메서드가 하나도 없는 **표식 인터페이스**다 — "인덱스 접근이 싸다"는 신호일 뿐이다.

> **표식 인터페이스(marker interface)** — 메서드가 없고 "이 성질을 가졌다"만 알리는 인터페이스.\
> 예: `ArrayList` 가 `RandomAccess` 를 달고 있어서 `Collections.binarySearch` 가 인덱스 접근 알고리즘을 고른다.

비용 — `ArrayList` 는 `RandomAccess` 이고 `LinkedList` 는 아니다.\
표식 하나로 `Collections` 의 알고리즘들이 다른 길을 고른다 — 그 내부는 자료구조의 영역이다
([`../../../../../data-structure/01-dynamic-array/`](../../../../../data-structure/01-dynamic-array/)·[`../../../../../data-structure/02-linked-list/`](../../../../../data-structure/02-linked-list/)).

### (4) 무엇을 보고 고르나 (1) — `null` 을 받나

**언제 쓰나** — DB 에서 온 nullable 컬럼을 컬렉션에 담을 때. 거의 언제나.

**실행 결과** (`Ex.java` — 39-b, 17·21·25 동일)

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

```text
   null 을 받는 쪽                        null 을 거부하는 쪽

  ArrayList / LinkedList                TreeSet / TreeMap(키)
  HashSet / LinkedHashSet                 -> 비교해야 하는데 null 은 비교가 안 된다
  HashMap / LinkedHashMap
  CopyOnWriteArrayList                  ArrayDeque / PriorityQueue
                                          -> null 을 "없음" 신호로 쓴다 (poll/peek)
        |
        v                               Hashtable / ConcurrentHashMap
  "값 없음"을 원소로 표현할 수 있다          -> 동시성에서 "없음"과 구분해야 한다

                                        List.of / Set.of / Map.of (9+)
                                          -> 계약으로 금지 (40번)
```

그림 해설 (한 단계씩):

- **거부하는 이유가 셋으로 갈린다.** 비교 불가 / `null` 을 신호로 씀 / 동시성.
- 정렬 컬렉션은 `compareTo` 를 불러야 하는데 `null.compareTo` 가 안 된다 — **에러 메시지가 그대로 말해 준다.**
- `Deque`·`Queue` 는 `poll()`·`peek()` 가 비었을 때 `null` 을 돌려주므로 **원소로도 `null` 이면 구분이 안 된다.**
- `Hashtable` 은 키에서는 `hashCode()` 를, 값에서는 명시적 검사를 한다 — **메시지가 다르다.**

비용 — `null` 을 받는 쪽이 편하지만, 그만큼 **"값이 없다"와 "`null` 이라는 값"이 섞인다.**\
`Map` 에서 그 문제가 가장 크게 터진다 — [`../41-map-api-merge-compute/`](../41-map-api-merge-compute/) 가 정본이다.

### (5) 무엇을 보고 고르나 (2) — 순서와 중복

**언제 쓰나** — 같은 데이터를 담았는데 꺼낼 때 순서가 다를 때. 즉 거의 언제나.

**실행 결과** (`Ex.java` — 39-b, 17·21·25 동일)

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
--- 맵의 키 순서
HashMap          : {date=4, apple=5, pear=4, fig=3}
LinkedHashMap    : {pear=4, apple=5, fig=3, date=4}
TreeMap          : {apple=5, date=4, fig=3, pear=4}
```

```text
입력  [pear] [apple] [fig] [apple] [date]

  중복을 남기나?
    남긴다 -> List 계열         [pear, apple, fig, apple, date]   5개
    지운다 -> Set 계열          apple 하나가 사라진다             4개

  순서는?
    넣은 순서   -> ArrayList / LinkedHashSet / LinkedHashMap
    정렬 순서   -> TreeSet / TreeMap
    말 안 함    -> HashSet / HashMap        <- 위 출력은 "이번에 그랬다"일 뿐
    꺼내는 순서만 정렬 -> PriorityQueue      <- toString 은 정렬돼 있지 않다
```

그림 해설 (한 단계씩):

- **`PriorityQueue` 의 `toString` 은 정렬돼 있지 않다.** 힙 배열을 그대로 찍기 때문이다.\
  `[apple, apple, fig, pear, date]` 에서 `date` 가 끝에 있다 — **정렬된 컬렉션이 아니다.**\
  정렬된 것은 **`poll()` 로 꺼내는 순서**뿐이다.
- `HashSet`·`HashMap` 의 출력 순서는 **관찰일 뿐 계약이 아니다.**\
  이 세 JDK 에서 같았지만 그것은 보장이 아니다 — 아래 「구현 세부사항 대 언어 보장」을 보라.
- `LinkedHashSet` 은 **중복은 지우되 순서는 남긴다** — 두 요구가 함께 올 때의 답이다.

비용 — 순서를 지키는 대가는 메모리다.\
`LinkedHashSet` 은 `HashSet` 에 양방향 링크를 얹은 것이고, `TreeSet` 은 비교 비용을 매 삽입마다 낸다.\
그 구조와 복잡도는 [`../../../../../data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/)·[`../../../../../data-structure/16-red-black-tree/`](../../../../../data-structure/16-red-black-tree/) 가 정본이다.

### (6) 무엇을 보고 고르나 (3) — 정렬 컬렉션은 계약을 요구한다

**언제 쓰나** — 내가 만든 타입을 `TreeSet`·`TreeMap` 에 넣을 때.

**실행 결과** (`Ex.java` — 39-b, 17·21·25 동일)

```text
--- 정렬 컬렉션은 Comparable 을 요구한다
TreeSet 에 P 넣기 : java.lang.ClassCastException: class Ex$1P cannot be cast to class java.lang.Comparable (Ex$1P is in unnamed module of loader 'app'; java.lang.Comparable is in module java.base of loader 'bootstrap')
TreeMap 에 P 키   : java.lang.ClassCastException: class Ex$1P cannot be cast to class java.lang.Comparable (Ex$1P is in unnamed module of loader 'app'; java.lang.Comparable is in module java.base of loader 'bootstrap')
TreeMap 에 P 키 1개 : java.lang.ClassCastException: class Ex$1P cannot be cast to class java.lang.Comparable (Ex$1P is in unnamed module of loader 'app'; java.lang.Comparable is in module java.base of loader 'bootstrap')
HashSet 에 P 넣기 : OK
```

```text
  record P(String n) {}      <- Comparable 을 구현하지 않았다

  HashSet 에 넣는다                    TreeSet 에 넣는다
        |                                    |
  hashCode()/equals() 만 부른다         compareTo() 를 불러야 한다
  Object 에 이미 있다                   P 에 없다 -> Comparable 로 캐스팅
        |                                    |
        v                                    v
  들어간다                             ClassCastException
                                       (원소가 하나여도 던진다)
```

그림 해설 (한 단계씩):

- **원소가 하나여도 던진다.** `TreeMap.put` 이 첫 키에서 `compare(key, key)` 로 타입을 검사하기 때문이다.
- 컴파일은 통과한다 — `TreeSet<Object>` 의 타입 파라미터에는 `Comparable` 바운드가 없다.\
  `new TreeSet<P>()` 로 써도 마찬가지다. **바운드는 생성자가 아니라 사용 시점 계약이다.**
- 해결은 둘 — `P` 가 `Comparable<P>` 를 구현하거나, **비교자를 생성자에 준다**(`new TreeSet<>(cmp)`).
- 계약의 자세한 내용과 위반의 증상은 [`../28-comparable-comparator/`](../28-comparable-comparator/) 가 정본이다.

비용 — 해시 기반은 `equals`/`hashCode` 를, 정렬 기반은 `compareTo`/`Comparator` 를 요구한다.\
**요구하는 계약이 다르다.** 해시 쪽 계약은 [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) 가 정본이다.

### (7) 잘못 고르면 결과가 조용히 달라진다 — 스택 세 가지

**언제 쓰나** — "스택이 필요하다"고 했을 때. 셋 중 아무거나 고르면 **순회 순서가 갈린다.**

**실행 결과** (`Ex.java` — 39-e, 17·21·25 동일)

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
```

```text
   push(pear) push(apple) push(fig) 한 뒤

   Stack (= Vector 의 하위 클래스)        ArrayDeque / LinkedList

   [pear][apple][fig]                     [fig][apple][pear]
     0     1      2   <- 배열 순서 그대로    ^ 앞쪽에 밀어 넣는다
        |                                       |
   순회 = pear apple fig                   순회 = fig apple pear
   pop  = fig apple pear                   pop  = fig apple pear
        |                                       |
   ★ 순회와 pop 이 반대다                   순회와 pop 이 같다
```

그림 해설 (한 단계씩):

- **`Stack` 만 순회 순서가 `pop` 순서와 반대다.** `Vector` 를 상속해 **배열을 앞에서부터** 찍기 때문이다.
- `pop` 결과는 셋 다 같다 — **`toString` 과 향상된 `for` 만 다르다.** 그래서 로그를 볼 때 헷갈린다.
- 그리고 `Stack` 은 **`List` 라서 가운데에 끼워 넣을 수 있다.**

```text
--- Stack 은 Vector 의 하위 클래스다
Stack 의 상위 클래스 : java.util.Vector
Stack 은 List 인가   : true
List 로서 가운데 삽입 : [z, a, b] / pop = b / 남은 것 [z, a]
```

- `st.add(0, "z")` 가 **컴파일되고 동작한다.** "끝에서만 넣고 뺀다"는 스택의 불변식이 **타입으로 안 지켜진다.**
- 그래서 새 코드에서는 **`ArrayDeque`** 를 쓴다. `Stack`·`Vector` 는 레거시다.

비용 — `ArrayDeque` 는 `null` 을 못 받는다(위 (4)). 그 하나만 주의하면 된다.

### (8) 인터페이스 설계의 대가 — 옵셔널 연산

**언제 쓰나** — `List` 를 파라미터로 받았는데 `add` 가 터질 때. 라이브러리 경계에서 자주 난다.

**실행 결과** (`Ex.java` — 39-c, 17·21·25 동일)

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

```text
        선언 타입이 같다                          실제 능력이 다르다

  List<String> l = ...                     ArrayList        add O  set O  remove O
        |                                  Arrays.asList    add X  set O  remove X
  컴파일러가 보는 것: List                    List.of          add X  set X  remove X
  add·set·remove 전부 있다                  unmodifiableList add X  set X  remove X
        |                                        |
        v                                        v
  컴파일 통과                               런타임 UnsupportedOperationException
```

그림 해설 (한 단계씩):

- 인터페이스 하나가 **능력이 다른 구현체 전부**를 덮으려면 "선택적으로 안 되는 메서드"를 허용해야 한다.\
  그것이 자바가 치른 대가다 — **컴파일러가 못 막는다.**
- `Arrays.asList` 는 **`set` 만 되고 `add`·`remove` 는 안 된다.** 길이가 고정된 배열 위의 뷰이기 때문이다.
- javadoc 이 이 설계를 명시한다.

> Certain methods of this interface are considered "destructive" and are called "mutator" methods in that they modify the group of objects contained within the collection on which they operate. They can be specified to throw `UnsupportedOperationException` if this collection implementation does not support the operation.

- **"효과가 없으면 던지지 않아도 된다"까지 허용한다** — 그래서 `addAll(빈 컬렉션)` 이 구현마다 갈린다.

> Such methods should (but are not required to) throw an `UnsupportedOperationException` if the invocation would have no effect on the collection. ... However, it is recommended that such cases throw an exception unconditionally, as throwing only in certain cases can lead to programming errors.

- **`List.of` 는 권고를 따라 무조건 던지고, `Arrays.asList` 는 안 던진다.** 위 출력이 그 차이다.
- 에러 메시지의 스택트레이스가 어느 구현인지까지 알려 준다.

```text
List.of("a").add("z")                        Arrays.asList("a").add("z")
java.lang.UnsupportedOperationException      java.lang.UnsupportedOperationException
  at ImmutableCollections.uoe(...)             at java.util.AbstractList.add(...)
  at ImmutableCollections$Abstract...add(..)   at java.util.AbstractList.add(...)
```

비용 — 방어는 하나뿐이다. **받은 컬렉션을 고칠 거면 내 것으로 복사한다.**\
`new ArrayList<>(받은것)` 한 줄이면 이 계열의 사고가 전부 사라진다.\
셋의 차이(널 허용·변경 가능성·원본 반영)는 [`../40-list-set-and-immutable-factories/`](../40-list-set-and-immutable-factories/) 가 정본이다.

## 문법 — 형태와 규칙

직접 쓴 최소 예제다. 출력은 전부 실행 결과다.

### 선택 표 — 무엇을 보고 고르나

이 표가 이 주제의 결론이다. **왼쪽 요구에서 오른쪽 구현체로 간다.**

| 요구 | 고르는 것 | 순서 | 중복 | `null` |
|---|---|---|---|---|
| 그냥 순서대로 담는다 | **`ArrayList`** — 기본 선택 | 넣은 순서 | 허용 | 허용 |
| 앞뒤로 자주 넣고 뺀다 | `ArrayDeque` | 넣은 순서 | 허용 | **금지** |
| 중간 삽입·삭제가 많고 인덱스 접근은 안 한다 | `LinkedList` | 넣은 순서 | 허용 | 허용 |
| 중복을 없앤다 | **`HashSet`** | **없음** | 제거 | 허용 |
| 중복을 없애되 넣은 순서는 지킨다 | **`LinkedHashSet`** | 넣은 순서 | 제거 | 허용 |
| 중복을 없애고 정렬한다 | `TreeSet` | 정렬 | 제거 | **금지** |
| 키로 찾는다 | **`HashMap`** | **없음** | 키 유일 | 키·값 허용 |
| 키로 찾고 넣은 순서를 지킨다 | **`LinkedHashMap`** | 넣은 순서 | 키 유일 | 키·값 허용 |
| 키로 찾고 정렬·범위 질의를 한다 | `TreeMap` | 정렬 | 키 유일 | 키 **금지** |
| 우선순위가 가장 높은 것부터 꺼낸다 | `PriorityQueue` | **꺼낼 때만** | 허용 | **금지** |
| 키가 `enum` 이다 | `EnumMap` / `EnumSet` | 상수 선언 순서 | 키 유일 | 키 **금지** |
| 여러 스레드가 동시에 쓴다 | `ConcurrentHashMap` | 없음 | 키 유일 | **둘 다 금지** |
| 읽기가 압도적으로 많고 쓰기가 드물다 | `CopyOnWriteArrayList` | 넣은 순서 | 허용 | 허용 |
| 바꾸지 않을 것을 넘긴다 | `List.of` / `Set.of` / `Map.of` (9+) | 리스트만 | 리스트만 허용 | **금지** |

- **모르면 `ArrayList` 와 `HashMap`.** 그 둘로 시작해서 요구가 생길 때 바꾼다.
- 표의 `null` 칸은 위 (4)의 **실행 결과**에서 옮긴 것이다.
- `EnumMap`·`EnumSet` 의 자세한 것은 [`../13-enum-classes/`](../13-enum-classes/) 가 정본이다.
- `ConcurrentHashMap` 의 동시성 계약은 [**55번 주제**](../55-atomics-and-concurrent-collections/)가 정본이다.

### 선언은 인터페이스로, 생성은 구현체로

```java
// 이렇게 쓴다
List<String> names = new ArrayList<>();
Map<String, Integer> counts = new HashMap<>();
Set<String> seen = new LinkedHashSet<>();

// 이렇게 쓰지 않는다 — 구현체를 바꿀 수 없게 된다
ArrayList<String> names2 = new ArrayList<>();
```

- 다만 **선언 타입이 약속을 줄인다.** `Map` 으로 선언하면 `firstEntry()` 를 못 쓴다.
- 순서가 계약의 일부면 **`LinkedHashMap` 으로 선언**하는 것이 맞다 — 42번이 그 이야기다.
- 반환 타입도 마찬가지다. `ArrayList` 를 반환한다고 적으면 호출자가 그것에 기댄다.

### `Map` 을 도는 네 가지 형태

```java
Map<String, Integer> m = new LinkedHashMap<>();

for (String k : m.keySet())                 { }        // 키만
for (int v : m.values())                    { }        // 값만
for (Map.Entry<String, Integer> e : m.entrySet()) { }  // 둘 다 — 기본 선택
m.forEach((k, v) -> { });                              // 8+
```

- **`keySet()` 을 돌며 `get(k)` 를 부르지 않는다.** 조회가 두 번이 된다.
- `entrySet()` 이 기본이다. 뷰라는 사실과 그 결과는 [`../41-map-api-merge-compute/`](../41-map-api-merge-compute/) 가 정본이다.

### `Collection` 으로 받으면 인덱스가 없다

```text
$ javac Ex.java
Ex.java:8: error: cannot find symbol
        System.out.println(c.get(0));
                            ^
  symbol:   method get(int)
  location: variable c of type Collection<String>
```

- `Collection` 에는 `get(int)` 가 없다. **인덱스는 `List` 의 개념**이다.
- 변수에 `ArrayList` 를 담아 놓아도 **선언 타입이 `Collection` 이면 컴파일이 안 된다.**

## 어디서 틀리나

### 1. `Map` 을 `Collection` 이라고 생각한다

```java
void process(Collection<?> c) { }
process(map);        // 컴파일 에러
for (var e : map) { } // 컴파일 에러
```

- **`Map` 은 `Iterable` 이 아니다.** 셋 중 하나를 골라 넘긴다 — `map.entrySet()`·`map.keySet()`·`map.values()`.
- `Map.Entry` 를 `Map` 이라고 부르지 않는다. `Entry` 는 **한 칸**이고 `Map` 은 **칸 전체**다.

### 2. `HashSet`·`HashMap` 의 출력 순서에 기댄다

```java
Set<String> s = new HashSet<>(List.of("pear", "apple", "fig"));
assertEquals("[date, apple, pear, fig]", s.toString());   // 언젠가 깨진다
```

- 위 (5)의 출력은 **이 세 JDK 에서 그랬다**는 관찰이다. javadoc 은 순서를 약속하지 않는다.
- 테스트에서 순서를 비교해야 하면 `LinkedHashSet`·`TreeSet` 을 쓰거나 **정렬해서 비교**한다.
- 순서가 도메인 요구라면 **자료형 선택으로 표현한다.** 주석으로 적지 않는다.

### 3. `PriorityQueue` 를 정렬된 컬렉션으로 읽는다

```java
PriorityQueue<String> pq = new PriorityQueue<>(List.of("pear","apple","fig","apple","date"));
System.out.println(pq);                       // [apple, apple, fig, pear, date]  <- 정렬 아님
for (String s : pq) { }                       // 순회 순서도 정렬이 아니다
```

- 정렬돼 있는 것은 **`poll()` 로 꺼내는 순서**뿐이다. `toString`·`iterator`·`stream` 은 힙 배열 순서다.
- 전부 정렬해서 보고 싶으면 `new TreeSet<>(pq)` 또는 `pq.stream().sorted().toList()`.
- 힙의 구조는 [`../../../../../data-structure/07-heap/`](../../../../../data-structure/07-heap/) 가 정본이다.

### 4. 받은 컬렉션을 그 자리에서 고친다

```java
void addDefault(List<String> l) { l.add("default"); }
addDefault(List.of("a", "b"));      // UnsupportedOperationException
```

- 호출자가 무엇을 넘길지 모른다. **파라미터로 받은 컬렉션은 읽기만 한다**가 기본이다.
- 고쳐야 하면 복사한다 — `new ArrayList<>(l)`.
- 반대로 **내 필드를 그대로 돌려주지 않는다.** 호출자가 고쳐 버린다([**59번 주제**](../59-immutable-objects/)).

### 5. `TreeMap`·`TreeSet` 에 `Comparable` 아닌 것을 넣는다

- 컴파일은 통과하고 **런타임에 `ClassCastException`** 이 난다.
- 원소가 **하나여도** 던진다. 테스트 데이터가 비어 있으면 통과하고 운영에서 터진다.
- 방어: 생성자에 비교자를 준다 — `new TreeMap<>(Comparator.comparing(P::n))`.

### 6. `null` 을 아무 컬렉션에나 넣는다

```java
Deque<String> d = new ArrayDeque<>();
d.add(maybeNull);       // NullPointerException — 메시지가 없다
```

- `ArrayDeque`·`PriorityQueue`·`TreeSet`·`ConcurrentHashMap` 은 거부한다.
- **`ArrayDeque` 의 NPE 에는 메시지가 없다.** 어느 줄인지 스택트레이스로 찾아야 한다.
- 애초에 `null` 을 안 담는 쪽이 낫다([`../60-null-handling/`](../60-null-handling/)).

### 7. `Vector`·`Hashtable` 을 쓴다

- 둘 다 1.0 시대의 클래스다. 모든 메서드가 `synchronized` 라 **혼자 쓸 때도 비용을 낸다.**
- 그리고 그 동기화는 **복합 연산을 보호하지 못한다** — `if (!v.contains(x)) v.add(x)` 는 여전히 경쟁한다.
- `Collections.synchronizedMap` 으로 감싸도 같다.

**실행 결과** (`Ex.java` — 39-e, 17·21·25 동일)

```text
--- Collections.synchronizedMap 의 복합 연산
타입                 : java.util.Collections$SynchronizedMap
put/get 은 락을 잡는다. 하지만 아래 두 줄 사이에는 락이 없다:
  if (!sm.containsKey(k)) sm.put(k, v);
한 호출로 하려면     : sm.putIfAbsent(k, v) -> 1 / {a=1}
```

- **메서드 하나하나는 락을 잡지만 두 호출 사이는 안 잡는다.** 그것이 동기화 래퍼의 한계다.
- 방어는 **복합 연산을 한 호출로 줄이는 것**이다(`putIfAbsent`·`merge` — [`../41-map-api-merge-compute/`](../41-map-api-merge-compute/)).
- 동시성이 필요하면 `ConcurrentHashMap`·`CopyOnWriteArrayList`([**55번 주제**](../55-atomics-and-concurrent-collections/)), 아니면 `ArrayList`·`HashMap`.
- **`Stack` 대신 `ArrayDeque`** 를 쓴다 — (7)에서 본 순회 순서와 타입 안전성 둘 다 그쪽이 낫다.

### 8. "컬렉션 하나 고르는 건 나중에 바꾸면 되지"

- **구현체는 바꾸기 쉽지만 그 컬렉션이 만든 순서 가정은 코드 전체에 퍼진다.**
- `HashMap` 으로 개발하다 출력 순서가 우연히 맞아서, 나중에 데이터가 늘자 순서가 바뀌는 사고가 전형적이다.
- 선택 표의 질문 다섯(순서·중복·정렬·`null`·동시성)에 **먼저 답하고 고른다.**

## 구현 세부사항 대 언어 보장

| 관측한 것 | 보장인가 | 근거 |
|---|---|---|
| `Map` 이 `Collection` 이 아님 | **보장** | `Map` 인터페이스 선언(`extends` 절이 없다) |
| `List` 가 `SequencedCollection` 을 확장 | **보장 (21+)** | `List` 선언. 17 에는 이 타입이 없다 |
| `TreeSet` 이 `null` 에 NPE | **사실상 보장** | `TreeSet` javadoc — 자연 순서일 때 `null` 은 `NullPointerException` |
| 그 NPE 메시지 `Cannot invoke "java.lang.Comparable.compareTo(Object)"` | **보장 아님** | JVM 의 helpful NullPointerException 이 만든 문구다 |
| `ArrayDeque` 가 `null` 에 NPE | **보장** | `ArrayDeque` javadoc — "Null elements are prohibited" |
| `HashSet` 의 순회 순서가 `[date, apple, pear, fig]` | **보장 아님** | `HashSet` javadoc — "makes no guarantees as to the iteration order" |
| `HashMap` 의 키 순서 | **보장 아님** | 같은 문장 |
| `LinkedHashSet` 이 넣은 순서 | **보장** | `LinkedHashSet` javadoc — 삽입 순서 |
| `TreeSet`·`TreeMap` 이 정렬 순서 | **보장** | `SortedSet`·`SortedMap` 계약 |
| `PriorityQueue.toString` 이 정렬돼 있지 않음 | **보장** | `PriorityQueue` javadoc — "not ordered ... iterator is not guaranteed to traverse in any particular order" |
| `List.of` 가 `add` 에 UOE | **보장** | `List` javadoc 「Unmodifiable Lists」 |
| `Arrays.asList` 의 `addAll(빈 컬렉션)` 이 통과 | **보장 아님** | `Collection` javadoc 이 양쪽을 다 허용한다 |
| `getInterfaces()` 가 보여 주는 목록 | **그 클래스 선언 그대로** | 상속으로 들어온 인터페이스는 안 나온다 |
| 구체 타입 `java.util.Arrays$ArrayList` 등 | **보장 아님** | 문서화되지 않은 내부 클래스다 |

**세 JDK 실측** — 프로그램 3개를 17.0.13 · 21.0.5 · 25.0.1 에서 돌려 `diff` 했다.

```text
39-b (null·순서·정렬 계약)   : 세 버전 출력이 한 글자도 같다
39-c (옵셔널 연산)           : 본문 출력은 같다. 스택트레이스 줄 번호만 다르다
   17: AbstractList.add(AbstractList.java:153) / 21: (:155)
   21: ImmutableCollections.uoe(ImmutableCollections.java:142) / 25: (:159)
39-a (계층)                  : 17 에서는 컴파일 자체가 안 된다 (SequencedCollection 이 없다)
```

- ★ **`HashSet` 의 순회 순서가 세 버전에서 똑같았다.** 그래서 **더 위험하다.**\
  똑같다는 관찰은 관찰일 뿐이고, javadoc 은 그것을 약속하지 않았다.
- 스택트레이스 줄 번호는 **매 릴리스 바뀐다.** 테스트에서 비교하지 않는다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 일 | 고를 것 |
|---|---|
| 뭘 쓸지 모르겠다 | **`ArrayList`** / **`HashMap`** |
| 중복을 지우고 싶다 | `HashSet`. 순서가 필요하면 **`LinkedHashSet`** |
| 정렬된 상태로 들고 있어야 한다 | `TreeSet`·`TreeMap`. **한 번만 정렬하면 되면 `List.sort`** 가 싸다 |
| 앞뒤로 넣고 빼는 큐·스택 | **`ArrayDeque`**. `Stack`·`Vector` 는 쓰지 않는다 |
| 우선순위 큐 | `PriorityQueue`. **꺼낼 때만 정렬**이라는 것을 기억한다 |
| 키가 `enum` | **`EnumMap`·`EnumSet`** — 배열이라 빠르고 순서가 보장된다 |
| 메서드 파라미터 타입 | 가장 **넓은** 것 — 읽기만 하면 `Collection<? extends T>`([`../18-wildcards-pecs/`](../18-wildcards-pecs/)) |
| 반환 타입 | 약속할 만큼만 — 순서가 계약이면 `List`, 아니면 `Collection` |
| 바꾸지 말라고 주고 싶다 | `List.copyOf(...)` ([`../40-list-set-and-immutable-factories/`](../40-list-set-and-immutable-factories/)) |
| 여러 스레드 | `ConcurrentHashMap`. `Collections.synchronizedMap` 은 복합 연산을 못 지킨다 |
| 자료구조 자체가 궁금하다 | **여기가 아니라** [`../../../../../data-structure/`](../../../../../data-structure/) |

판단 규칙 세 줄.

- **고르기 전에 다섯을 묻는다** — 순서? 중복? 정렬? `null`? 동시성?
- **선언은 인터페이스로, 생성은 구현체로.** 단 순서가 계약이면 그 사실이 타입에 드러나야 한다.
- **받은 컬렉션은 읽기만 한다.** 고칠 거면 복사한다.

## 핵심 문장

- **`Map` 은 `Collection` 이 아니다** — 상속 관계가 없다. 그래서 `for` 로 못 돌고, 대신 뷰 셋(`keySet`·`values`·`entrySet`)으로 이어진다.
- 구현체 선택은 **다섯 질문**으로 끝난다 — 순서·중복·정렬·`null`·동시성.
- **`HashSet`·`HashMap` 의 순회 순서는 계약이 아니다.** 여러 버전에서 같아도 보장이 아니다.
- **옵셔널 연산이 인터페이스 설계의 대가다** — 같은 `List` 타입인데 `add` 가 되는 것과 `UnsupportedOperationException` 을 던지는 것이 섞여 있고, 컴파일러가 막지 못한다.
- 정렬 컬렉션은 `Comparable`/`Comparator` 를, 해시 컬렉션은 `equals`/`hashCode` 를 요구한다. **요구하는 계약이 다르다.**

## 관련 자료

- [`../17-generic-declarations/`](../17-generic-declarations/) — **이 주제의 선행.** `List<String>` 의 타입 파라미터가 무엇인지
- [`../18-wildcards-pecs/`](../18-wildcards-pecs/) — 컬렉션을 파라미터로 받을 때 `? extends`/`? super` 중 무엇을 쓰나
- [`../40-list-set-and-immutable-factories/`](../40-list-set-and-immutable-factories/) — **옵셔널 연산의 정본.** 그쪽은 `List.of`·`Arrays.asList`·`unmodifiableList` **셋의 차이**부터, 여기는 **"인터페이스가 대가를 치렀다"까지**
- [`../41-map-api-merge-compute/`](../41-map-api-merge-compute/) — `Map` 의 메서드와 `null` 값의 의미. 여기는 **`Map` 이 어디 서 있나**까지, 그쪽은 **`Map` 으로 무엇을 하나**부터
- [`../42-sequenced-collections/`](../42-sequenced-collections/) — 21 에서 계층 중간에 끼워 넣어진 세 인터페이스. **그 사정은 그쪽이 정본**
- [`../43-iterator-and-fail-fast/`](../43-iterator-and-fail-fast/) — `Iterable` 이 주는 `Iterator` 의 계약과 순회 중 수정
- [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) — **해시 컬렉션이 요구하는 계약의 정본**
- [`../28-comparable-comparator/`](../28-comparable-comparator/) — **정렬 컬렉션이 요구하는 계약의 정본**. `TreeSet` 의 `ClassCastException` 의 뿌리
- [`../13-enum-classes/`](../13-enum-classes/) — `EnumMap`·`EnumSet` 이 왜 다른 카테고리인지
- [`../20-control-flow-statements/`](../20-control-flow-statements/) — 향상된 `for` 가 `Iterable` 에만 도는 이유
- [`../../../../../data-structure/`](../../../../../data-structure/) — **자료구조 원리의 정본 35편.**\
  그쪽은 **자료구조가 어떻게 만들어져 있나**(해시 충돌·트리 회전·상각 분석)까지,\
  여기는 **자바가 그것을 어떤 인터페이스로 노출하고 어느 구현체를 왜 고르나**부터
- [`../../../../../data-structure/01-dynamic-array/`](../../../../../data-structure/01-dynamic-array/) — `ArrayList` 의 내부가 왜 2배씩 늘어나나
- [`../../../../../data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/) — `HashMap`·`HashSet` 의 버킷과 충돌
- [`../../../../../data-structure/16-red-black-tree/`](../../../../../data-structure/16-red-black-tree/) — `TreeMap`·`TreeSet` 의 균형 트리
- [`../../../../../data-structure/07-heap/`](../../../../../data-structure/07-heap/) — `PriorityQueue` 의 힙
- [`../../../../../data-structure/04-queue-deque/`](../../../../../data-structure/04-queue-deque/) — `ArrayDeque` 의 원형 버퍼
- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 39번)
- [`../55-atomics-and-concurrent-collections/`](../55-atomics-and-concurrent-collections/)(원자 변수와 동시 컬렉션) — `ConcurrentHashMap` 의 계약
- [`../59-immutable-objects/`](../59-immutable-objects/)(불변 객체 만들기) — 컬렉션 필드를 방어적으로 복사하는 자리

## 용어 풀이

- **컬렉션 프레임워크** — `java.util` 의 자료구조 인터페이스와 구현체 묶음. Java 1.2 에서 들어왔다.
- **`Collection`** — 원소를 담는 인터페이스. `Iterable` 하나를 확장한다.
- **`Map`** — 키와 값을 짝지어 담는 인터페이스. **아무것도 확장하지 않는다.**
- **컬렉션 뷰(collection view)** — `Map` 이 자기 내용을 `Set`·`Collection` 으로 보여 주는 것. `keySet`·`values`·`entrySet` 셋.
- **뷰(view)** — 원소를 직접 저장하지 않고 뒤에 있는 컬렉션에 위임하는 컬렉션. 원본이 바뀌면 같이 바뀐다.
- **옵셔널 연산(optional operation)** — 구현체가 지원하지 않아도 되는 메서드. 안 되면 `UnsupportedOperationException` 을 던진다.
- **`UnsupportedOperationException`** — 그 구현체가 그 연산을 지원하지 않을 때의 런타임 예외.
- **encounter order(순회 순서)** — "첫 원소부터 끝 원소까지"가 정해져 있는 것. 21 의 `SequencedCollection` 이 이 말을 정의했다.
- **표식 인터페이스(marker interface)** — 메서드 없이 성질만 알리는 인터페이스. `RandomAccess`·`Cloneable`.
- **`RandomAccess`** — 인덱스 접근이 싸다는 표식. `ArrayList` 는 달고 `LinkedList` 는 안 단다.
- **`Map.Entry`** — 맵의 한 칸(키 하나 + 값 하나). 맵 자체가 아니다.
- **`ClassCastException`** — 캐스팅이 안 될 때의 예외. 정렬 컬렉션이 `Comparable` 을 요구할 때 여기서 난다.

## 더 들어가면

- **`LinkedList` 는 `List` 이면서 `Deque` 다.** 그래서 스택·큐로도 쓸 수 있지만,
  **양끝 작업만 한다면 `ArrayDeque` 가 낫다** — 노드마다 객체를 만들지 않기 때문이다.\
  왜 그런가는 [`../../../../../data-structure/02-linked-list/`](../../../../../data-structure/02-linked-list/) 와 [`../../../../../data-structure/04-queue-deque/`](../../../../../data-structure/04-queue-deque/) 가 정본이다.
- **`Collections` 는 클래스이고 `Collection` 은 인터페이스다.** 이름이 한 글자 차이다.\
  `Collections.unmodifiableList`·`Collections.sort`·`Collections.emptyList` 는 전부 정적 유틸리티다.
- **`Collections.synchronizedMap` 은 `ConcurrentHashMap` 의 대체가 아니다.**\
  메서드 하나하나는 락을 잡지만 `if (!m.containsKey(k)) m.put(k, v)` 같은 **복합 연산은 여전히 깨진다.**\
  그리고 순회는 호출자가 직접 `synchronized` 블록으로 감싸야 한다 — javadoc 이 그렇게 적어 놓았다.
- **`Hashtable` 의 `null` 거부 메시지가 키와 값에서 다르다.**\
  키는 `Cannot invoke "Object.hashCode()" because "key" is null`(JVM 이 만든 문구),
  값은 메시지 없는 NPE(코드가 명시적으로 던진다). **어느 쪽이 `null` 이었는지 메시지로 구분된다.**
- **`Map` 이 `Collection` 이 아닌 것은 설계 논쟁거리였다.**\
  `Map<K,V>` 가 `Collection<Map.Entry<K,V>>` 였다면 `add(Entry)` 가 키 중복에서 무엇을 해야 하는지 정할 수 없다.\
  자바는 이어 붙이지 않는 쪽을 골랐고, 그래서 뷰 셋이 생겼다.
- **`getInterfaces()` 는 선언에 적힌 것만 돌려준다.**\
  `PriorityQueue -> [Serializable]` 이 `Queue` 가 아니라는 뜻이 아니다 — `AbstractQueue` 가 들고 있다.\
  전부 보려면 상위 클래스를 타고 올라가야 한다. **`instanceof` 가 더 정직한 질문이다.**
