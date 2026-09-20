# java/syntax/42 — `SequencedCollection` (21): 순서 있는 컬렉션의 공통 API — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **선행** — [`../39-collections-framework-map/`](../39-collections-framework-map/). 인터페이스 계층이 어떻게 생겼는지가 전제다.
> **기준 소스** — JDK 21.0.5 의 `lib/src.zip` 을 **직접 풀어 읽은** javadoc 과 구현이다.\
> `java.base/java/util/SequencedCollection.java` — `@since 21` · encounter order 정의 · 여섯 메서드의 `@implSpec`.\
> `java.base/java/util/SequencedMap.java` · `SequencedSet.java` — 각각의 메서드 목록과 반환 타입.\
> `java.base/java/util/LinkedHashMap.java` — 접근 순서 모드에서 `putFirst`·`lastEntry` 가 접근으로 안 세는 규칙.\
> `java.base/java/util/Collection.java` — 「View Collections」 절(`reversed` 가 뷰 목록에 있다).\
> 인용은 **그 파일에서 복사한 것만** 옮겼다.
> **실행 검증** — 이 문서의 모든 출력·에러는 Temurin JDK 에서 **실제로 돌려** 얻은 것이다.\
> 도는 프로그램 4개를 **21.0.5 · 25.0.1** 에서 돌려 `diff` 했다(출력 동일).\
> **17.0.13 에서는 컴파일 자체가 안 된다** — 그 에러도 본문에 실었다(컴파일 에러용 프로그램 4개).
> **버전** — `SequencedCollection`·`SequencedSet`·`SequencedMap` 은 **Java 21**(JEP 431).\
> `@since 21` 을 `src.zip` 에서 직접 읽었다. `List`·`Deque`·`SortedSet`·`SortedMap` 에 붙은 새 메서드들도 전부 `@since 21` 이다.
> **범위** — **왜 21에 들어왔나·어떤 논쟁이 있었나**는 [`../../../../../../history/java/java-21.md`](../../../../../../history/java/java-21.md) 가 정본이다.\
> 그쪽은 **언제·왜**까지, 여기는 **그래서 코드에서 어떻게 쓰고 무엇이 막히나**부터다.\
> 이중 연결 리스트·균형 트리 같은 **자료구조 자체**는 [`../../../../../data-structure/`](../../../../../data-structure/) 가 정본이다.
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**21 이전에는 「첫 번째를 꺼내라」를 컬렉션마다 다른 말로 해야 했다.**

같은 뜻인데 이름이 여섯 가지였다.

| 컬렉션 | 21 이전, 첫 원소 | 21 이전, 끝 원소 |
|---|---|---|
| `List` | `list.get(0)` | `list.get(list.size() - 1)` |
| `Deque` | `deque.getFirst()` | `deque.getLast()` |
| `LinkedHashSet` | `set.iterator().next()` | **방법이 없다** — 끝까지 돌아야 한다 |
| `SortedSet` | `set.first()` | `set.last()` |
| `LinkedHashMap` | `map.entrySet().iterator().next()` | **방법이 없다** |
| `SortedMap` | `map.firstKey()` | `map.lastKey()` |

**21부터는 전부 `getFirst()` · `getLast()` 다.**

> **encounter order(순회 순서)** — "첫 원소부터 끝 원소까지"가 정해져 있는 것.\
> 예: `ArrayList` 는 넣은 순서, `TreeSet` 은 정렬 순서가 encounter order 다. `HashSet` 에는 없다.

```text
   21 이전                                 21 이후

  List      get(0)        get(size()-1)    List
  Deque     getFirst()    getLast()        Deque          getFirst()
  LinkedHS  iterator()... (없음)           LinkedHashSet  getLast()
  SortedSet first()       last()           SortedSet      reversed()
                |                                |
         이름이 제각각이고                 SequencedCollection 하나에
         LinkedHashSet 은 아예 없었다        여섯 메서드로 모았다
```

**똑같은 구조로** 자바가 동작한다: 「끝을 다루는 말」을 인터페이스 하나로 통일한 것이다.

그리고 **`reversed()` 가 딸려 왔다.** 역순 순회가 한 줄이 된다.

```java
for (String s : list.reversed()) { }        // 21+
```

- 단 **`reversed()` 는 복사가 아니라 뷰**다. 원본을 고치면 따라 바뀌고, 뷰에 쓰면 원본에 간다.
- 그리고 이 셋은 **기존 타입에 소급 적용**됐다 — `List`·`Deque`·`LinkedHashSet`·`SortedSet`·`LinkedHashMap`·`SortedMap` 이 전부 하위 타입이 됐다.

실무에서 이것이 필요해지는 자리는 **"LRU 캐시에서 가장 오래된 항목을 꺼내자"** 같은 한 줄이다.\
21 이전에는 `map.entrySet().iterator().next()` 였고, 이제는 `map.firstEntry()` 다.

## 이 주제가 답하려는 질문

원고가 없는 API 주제라 「문제」 대신 이 세 질문을 둔다.

1. `SequencedCollection`·`SequencedSet`·`SequencedMap` 이 **무엇을 통일했나** —
   그리고 **어느 타입이 하위 타입이 되고 어느 타입이 안 됐나.**
2. `reversed()` 는 **복사인가 뷰인가** — 그 결과 무엇을 조심해야 하나.
3. 기존 계층 중간에 인터페이스를 끼워 넣은 **대가**는 무엇인가 — 17에서 되던 코드가 21에서 깨지는 자리가 있나.

## 예시 데이터 — 이 묶음이 공유하는 것

39~43번은 같은 데이터를 쓴다.

```text
과일 다섯 개 (중복 하나)
  "pear"  "apple"  "fig"  "apple"  "date"

끝 다루기 확인용 축소판
  ["a", "b", "c"]  — 첫·끝·역순을 한 줄에 놓을 수 있는 최소 크기
```

## 동작 방식

### (1) 21 이전에는 이름이 여섯 가지였다

**언제 쓰나** — 컬렉션 종류가 바뀔 때마다 "첫 원소 꺼내는 법"을 다시 찾을 때.

**실행 결과** (`Ex.java` — 42-a, 21·25 동일)

```text
--- 1) 21 이전에는 첫 원소를 이렇게 꺼냈다
List           첫: list.get(0)                    끝: list.get(list.size()-1)
Deque          첫: deque.getFirst()               끝: deque.getLast()
LinkedHashSet  첫: lhs.iterator().next()          끝: 순회를 끝까지 돌아야 한다
SortedSet      첫: ts.first()                     끝: ts.last()
LinkedHashMap  첫: lhm.entrySet().iterator().next() 끝: 순회를 끝까지 돌아야 한다
SortedMap      첫: tm.firstKey()                  끝: tm.lastKey()
```

```text
   같은 요구 — "첫 원소를 달라"

   List           get(0)
   Deque          getFirst()            <- 이름이 다르다
   SortedSet      first()               <- 또 다르다
   LinkedHashSet  iterator().next()     <- 메서드가 아예 없다
   LinkedHashMap  entrySet().iterator().next()
        |
   외워야 할 것이 여섯 개이고,
   그중 둘은 "끝 원소" 를 O(n) 순회 없이는 못 얻는다
```

그림 해설 (한 단계씩):

- **`LinkedHashSet` 과 `LinkedHashMap` 이 가장 나빴다.** 끝 원소를 얻으려면 전부 돌아야 했다.
- 내부는 **이중 연결 리스트**라 끝을 O(1)에 알고 있는데, **API 가 그것을 노출하지 않았다.**
- `Deque` 는 `getFirst`/`getLast` 가 있었지만 **인덱스 접근이 없어** `List` 자리에 못 썼다.

비용 — 제네릭 코드를 못 쓴다.\
"어떤 순서 있는 컬렉션이든 첫 원소를 로깅한다" 같은 유틸리티를 **타입마다 오버로드**해야 했다.

### (2) 21부터 — 여섯 메서드로 통일됐다

**언제 쓰나** — 컬렉션의 양끝을 다룰 때. 역순으로 돌 때.

**실행 결과** (`Ex.java` — 42-a, 21·25 동일)

```text
--- 2) 21 이후 — 같은 이름으로 통일됐다
타입               getFirst()     getLast()      reversed()              
ArrayList        a              c              [c, b, a]               
ArrayDeque       a              c              [c, b, a]               
LinkedHashSet    a              c              [c, b, a]               
TreeSet          a              c              [c, b, a]               
LinkedHashMap    a=1            c=3            {c=3, b=2, a=1}         
TreeMap          a=1            c=3            {c=3, b=2, a=1}         
List.of          a              b              [b, a]                  
```

```text
   SequencedCollection<E>          SequencedMap<K,V>

     getFirst()                      firstEntry()
     getLast()                       lastEntry()
     addFirst(e)                     putFirst(k, v)
     addLast(e)                      putLast(k, v)
     removeFirst()                   pollFirstEntry()
     removeLast()                    pollLastEntry()
     reversed()                      reversed()
                                     sequencedKeySet()
                                     sequencedValues()
                                     sequencedEntrySet()
```

그림 해설 (한 단계씩):

- **`SequencedCollection` 은 일곱 개**(여섯 + `reversed`), **`SequencedMap` 은 열 개**다.
- 이름이 다른 이유는 `Map` 이 `Collection` 이 아니기 때문이다 — 원소가 아니라 **항목**을 다룬다(39번).
- `SequencedSet` 은 메서드를 **하나도 더하지 않는다.** `reversed()` 의 **반환 타입만 좁힌다**(`SequencedSet`).
- javadoc 이 그 사정을 적어 놓았다.

> The only difference from the `SequencedCollection.reversed` method is that the return type of `SequencedSet.reversed` is `SequencedSet`.

비용 — 인터페이스에 메서드를 더하는 것은 **기존 구현체를 깨는 일**이다.\
자바는 `default` 메서드로 그것을 피했다([`../11-interfaces-default-methods/`](../11-interfaces-default-methods/)).

```java
// JDK 21.0.5  java.base/java/util/SequencedCollection.java  — 실제 소스 그대로
    default E getFirst() {
        return this.iterator().next();
    }

    default E getLast() {
        return this.reversed().iterator().next();
    }
```

- **`getLast()` 의 기본 구현은 `reversed()` 를 거친다.** 구현체가 재정의하면 O(1)이 된다.

### (3) 누가 하위 타입이 되고 누가 안 됐나

**언제 쓰나** — 파라미터 타입을 `SequencedCollection` 으로 열어 둘지 정할 때.

**실행 결과** (`Ex.java` — 42-a, 21·25 동일)

```text
--- 3) 어느 타입이 SequencedCollection 인가
ArrayList        SequencedCollection=true   SequencedSet=false  List=true
LinkedList       SequencedCollection=true   SequencedSet=false  List=true
ArrayDeque       SequencedCollection=true   SequencedSet=false  List=false
HashSet          SequencedCollection=false  SequencedSet=false  List=false
LinkedHashSet    SequencedCollection=true   SequencedSet=true   List=false
TreeSet          SequencedCollection=true   SequencedSet=true   List=false
PriorityQueue    SequencedCollection=false  SequencedSet=false  List=false
List.of()        SequencedCollection=true   SequencedSet=false  List=true
Arrays.asList()  SequencedCollection=true   SequencedSet=false  List=true
Set.of()         SequencedCollection=false  SequencedSet=false  List=false
HashMap          SequencedMap=false
LinkedHashMap    SequencedMap=true
TreeMap          SequencedMap=true
Map.of()         SequencedMap=false
```

```text
   된 것 (encounter order 가 있다)        안 된 것 (없다)

   List 전부 — ArrayList·LinkedList       HashSet
   Deque 전부 — ArrayDeque·LinkedList     Set.of  (순회 순서가 실행마다 다르다 — 40번)
   LinkedHashSet                          HashMap
   SortedSet — TreeSet                    Map.of
   LinkedHashMap                          PriorityQueue   <- 여기가 뜻밖이다
   SortedMap — TreeMap
   List.of · Arrays.asList
```

그림 해설 (한 단계씩):

- **`PriorityQueue` 가 안 됐다.** 힙이라 순회 순서가 정렬 순서가 아니기 때문이다(39번 (5)).\
  "꺼낼 때만 정렬"이라는 성질은 encounter order 가 **아니다.**
- `Set.of`·`Map.of` 도 안 됐다 — 순회 순서가 **JVM 실행마다 다르다**([`../40-list-set-and-immutable-factories/`](../40-list-set-and-immutable-factories/)).
- **`List.of` 는 됐다.** 불변이지만 순서가 계약이기 때문이다.
- `ArrayDeque` 는 `SequencedCollection` 이면서 **`List` 가 아니다** — 인덱스 접근이 없다.

비용 — 파라미터를 `SequencedCollection` 으로 열면 `List`·`Deque`·`LinkedHashSet`·`TreeSet` 을 다 받는다.\
대신 **`HashSet` 은 못 받는다** — 그것이 이 타입이 하는 약속이다.

### (4) ★ `reversed()` 는 복사가 아니라 뷰다

**언제 쓰나** — 역순으로 돌 때. 역순 결과를 보관할 때.

**실행 결과** (`Ex.java` — 42-b, 21·25 동일)

```text
--- 1) reversed() 는 복사가 아니라 뷰다
src          : [a, b, c]
rev          : [c, b, a]
rev 의 타입  : java.util.ReverseOrderListView$Rand
src.add("d") 후 rev : [d, c, b, a]   <- 따라 바뀌었다
rev.add("z") 후 src : [z, a, b, c, d]   <- 뷰에 쓰면 원본에 간다
rev.set(0,"Z") 후 src : [z, a, b, c, Z]
rev == src ?        : false
rev.reversed() == src ? : true
rev.reversed()      : [z, a, b, c, Z]
```

```text
     전 상태                    조작                     후 상태

  src  [a][b][c]           src.add("d")          src  [a][b][c][d]
  rev  -> src 를 역방향으로 본다                  rev  [d][c][b][a]    따라 바뀐다

  rev  [d][c][b][a]        rev.add("z")          src  [z][a][b][c][d]
                           (뷰의 "끝에" 붙인다)    rev  [d][c][b][a][z]
                                                       ^
                                        뷰의 끝 = 원본의 앞이다
```

그림 해설 (한 단계씩):

- **`reversed()` 는 새 리스트를 만들지 않는다.** `ReverseOrderListView$Rand` 라는 래퍼다.
- javadoc 이 `Collection` 의 「View Collections」 목록에 **`SequencedCollection.reversed` 를 명시**해 놓았다.

> Other examples of view collections include collections that provide a different representation of the same elements, for example, as provided by `List.subList`, `NavigableSet.subSet`, `Map.entrySet`, or **`SequencedCollection.reversed`**.

- **`rev.reversed() == src` 가 `true`** 다. 두 번 뒤집으면 원본 객체 그대로를 돌려준다.
- **뷰에 쓰면 원본에 간다.** `rev.add("z")` 가 원본의 **맨 앞**에 넣었다.

```text
--- 2) 인덱스도 뒤집힌다
l            : [a, b, c, d]  l.get(0)=a l.indexOf("c")=2
l.reversed() : [d, c, b, a]  get(0)=d indexOf("c")=1
l.reversed().subList(0,2) : [d, c]
```

- **인덱스도 뒤집힌다.** `get(0)` 이 원본의 마지막이고, `indexOf` 도 역방향 기준이다.
- `subList` 도 역방향 기준으로 잘린다 — **뷰 위의 뷰**다.

비용 — 복사가 없어서 싸다. 대신 **보관하면 원본에 묶인다.**\
스냅샷이 필요하면 복사한다 — `List.copyOf(l.reversed())`.

### (5) 정렬 컬렉션의 `reversed()` — 이미 있던 것과 같은가

**언제 쓰나** — `TreeSet`·`TreeMap` 을 역순으로 볼 때. 기존 `descendingSet()` 과 고를 때.

**실행 결과** (`Ex.java` — 42-b, 21·25 동일)

```text
--- 3) 정렬 컬렉션의 reversed()
TreeSet             : [a, b, c]  타입 java.util.TreeSet
TreeSet.reversed()  : [c, b, a]
descendingSet() 과 같은가 : true
원본에 d 추가 후 뷰 : [d, c, b, a]
```

```text
   TreeSet 의 역순 보기 — 두 이름, 같은 것

     ts.descendingSet()     (1.6 부터 — NavigableSet)
     ts.reversed()          (21 부터 — SequencedCollection)
            |
     equals 로 같고, 둘 다 뷰다
     reversed() 쪽이 모든 SequencedCollection 에서 쓸 수 있다
```

그림 해설 (한 단계씩):

- **`TreeSet.reversed()` 의 구체 타입이 `java.util.TreeSet`** 이다. `descendingSet()` 을 그대로 쓴다.
- 둘 다 뷰다 — 원본에 `d` 를 넣으면 뷰에 나타난다.
- **새 코드는 `reversed()` 를 쓴다.** 정렬 컬렉션이 아닌 것에도 같은 이름이 통하기 때문이다.

비용 — `descendingSet`·`descendingMap`·`descendingIterator` 는 그대로 남아 있다.\
21 이후에도 안 지워졌다 — **이름이 둘이 된 것이 통일의 대가**다.

### (6) `LinkedHashMap` 의 순서 조작 — `putFirst`·`pollFirstEntry`

**언제 쓰나** — LRU 캐시를 만들 때. 삽입 순서를 직접 옮길 때.

**실행 결과** (`Ex.java` — 42-b, 21·25 동일)

```text
--- 4) LinkedHashMap 의 순서 조작
맵                 : {a=1, b=2, c=3}
putFirst("c",30)   : {c=30, a=1, b=2}   <- 이미 있던 키가 맨 앞으로 옮겨졌다
putLast("a",10)    : {c=30, b=2, a=10}
pollFirstEntry()   : c=30 -> {b=2, a=10}
sequencedKeySet()  : [b, a] / reversed : [a, b]
sequencedValues()  : [2, 10]
reversed() 의 타입  : java.util.LinkedHashMap$ReversedLinkedHashMapView
```

```text
     {a=1, b=2, c=3}

     putFirst("c", 30)
        |
     c 는 이미 있다 -> 값을 30 으로 바꾸고 맨 앞으로 옮긴다
        |
        v
     {c=30, a=1, b=2}      <- put 과 다르다. put 은 순서를 안 바꾼다
```

그림 해설 (한 단계씩):

- **`put` 은 이미 있는 키의 순서를 안 바꾼다.** `putFirst`/`putLast` 는 바꾼다.
- javadoc 이 그 차이를 명시한다.

> Note that encounter order is not affected if a key is *re-inserted* into the map with the `put` method. ... The encounter order of entries already in the map can be changed by using the `putFirst` and `putLast` methods.

- `pollFirstEntry()` 는 **꺼내면서 지운다.** 빈 맵에서는 `null` 을 돌려준다(예외가 아니다).
- `sequencedKeySet()`·`sequencedValues()`·`sequencedEntrySet()` 은 **`reversed()` 가 붙은 뷰**다.\
  기존 `keySet()` 은 `Set` 이라 `reversed()` 가 없다.

비용 — 접근 순서 모드(`new LinkedHashMap<>(16, 0.75f, true)`)와 섞이면 헷갈린다.

```text
--- 5) 접근 순서 LinkedHashMap 에서 putFirst 는?
접근 순서 맵       : {a=1, b=2, c=3}
get("a") 후        : {b=2, c=3, a=1}
putFirst 는?       : {c=3, b=2, a=1}
```

- **`get` 이 순서를 바꾼다**(접근 순서 모드). 그런데 **`putFirst` 는 그 위에서도 그냥 앞으로 옮긴다.**
- javadoc 이 그 규칙을 따로 적었다.

> Explicit-positioning methods such as `putFirst` or `lastEntry`, whether on the map or on its reverse-ordered view, perform the positioning operation and **do not generate entry accesses**.

- 즉 **`lastEntry()` 를 읽어도 접근 순서가 안 바뀐다.** 읽기가 순서를 바꾸는 사고를 막아 준다.

**실행 결과** (`Ex.java` — 42-h, 21·25 동일)

```text
--- 삽입 순서 모드에서 put 은 순서를 안 바꾼다
처음          : {a=1, b=2, c=3}
put("a",99)   : {a=99, b=2, c=3}
putLast("a")  : {b=2, c=3, a=100}
--- 접근 순서 모드에서 읽기가 순서를 바꾸나
처음          : {a=1, b=2, c=3}
get("a") 후    : {b=2, c=3, a=1}
lastEntry() 후 : {b=2, c=3, a=1}
firstEntry() 후: {b=2, c=3, a=1}
containsKey 후 : {b=2, c=3, a=1}
getOrDefault 후: {c=3, a=1, b=2}
```

```text
   접근 순서 모드에서 "접근" 으로 세는 것과 안 세는 것

   세는 것    put · putIfAbsent · get · getOrDefault · compute* · merge
   안 세는 것 containsKey · firstEntry · lastEntry · putFirst · putLast
                   ^                         ^
         읽기인데 안 센다            위치 지정 메서드는 위치만 바꾼다
```

- ★ **`get` 은 순서를 바꾸고 `containsKey` 는 안 바꾼다.** javadoc 이 세는 목록을 열거해 놓았다.
- `getOrDefault` 도 센다 — 위 출력에서 `b` 가 맨 뒤로 갔다.
- LRU 캐시라는 **자료구조 자체**는 [`../../../../../data-structure/10-lru-cache/`](../../../../../data-structure/10-lru-cache/) 가 정본이다.

### (7) 안 되는 것 — 옵셔널 연산은 그대로 살아 있다

**언제 쓰나** — `SequencedCollection` 으로 받은 것에 `addFirst` 를 부를 때.

**실행 결과** (`Ex.java` — 42-a, 21·25 동일)

```text
--- 4) 안 되는 것
HashSet.getFirst 는 컴파일이 안 된다 (SequencedCollection 이 아니다)
List.of(..).addFirst("z") : UnsupportedOperationException
TreeSet.addFirst("z")     : UnsupportedOperationException
TreeSet.removeFirst()     : a
빈 ArrayList.getFirst()   : NoSuchElementException
빈 LinkedHashMap.firstEntry() : null
빈 LinkedHashMap.pollFirstEntry() : null
TreeMap.putFirst("z",9)   : UnsupportedOperationException
```

```text
   읽기는 다 되는데 "위치를 정해서 넣기" 가 갈린다

   ArrayList.addFirst("z")     -> 된다
   ArrayDeque.addFirst("z")    -> 된다
   LinkedHashSet.addFirst("z") -> 된다
   TreeSet.addFirst("z")       -> UnsupportedOperationException   위치를 내가 못 정한다
   TreeMap.putFirst("z", 9)    -> UnsupportedOperationException   순서는 비교자가 정한다
   List.of(..).addFirst("z")   -> UnsupportedOperationException   불변이다
```

그림 해설 (한 단계씩):

- **정렬 컬렉션은 위치를 정해서 넣을 수 없다.** 순서를 비교자가 정하기 때문이다.
- 그런데 **`removeFirst()` 는 된다** — 지우는 것은 순서를 어기지 않는다.
- **빈 컬렉션의 `getFirst()` 는 `NoSuchElementException`**, 빈 맵의 `firstEntry()` 는 **`null`** 이다.\
  ★ 둘의 규약이 다르다 — `Map` 쪽은 전통적으로 "없으면 `null`" 이다.
- `HashSet.getFirst()` 는 **컴파일 에러**다. 런타임 예외가 아니다.

```text
$ javac Ex.java
Ex.java:6: error: cannot find symbol
        System.out.println(s.getFirst());
                            ^
  symbol:   method getFirst()
  location: variable s of type Set<String>
1 error
```

비용 — 옵셔널 연산의 대가가 여기에도 그대로 있다(39번 (8)).\
`SequencedCollection` 으로 받았다고 `addFirst` 가 된다는 뜻은 아니다.

### (8) 기존 코드가 깨지는 자리 — 소급 적용의 대가

**언제 쓰나** — 17에서 21로 올릴 때. `List` 를 직접 구현한 클래스가 있을 때.

**실행 결과** (`Ex.java` — 42-d)

```java
static class MyList extends ArrayList<String> {
    public String reversed() { return "뒤집힌 문자열"; }
}
```

```text
===== JDK 17
뒤집힌 문자열
===== JDK 21
Ex.java:5: error: reversed() in MyList cannot implement reversed() in List
        public String reversed() { return "뒤집힌 문자열"; }
                      ^
  return type String is not compatible with List<String>
  where E is a type-variable:
    E extends Object declared in interface List
1 error
```

```text
        JDK 17                            JDK 21

  List 에 reversed() 가 없다          List 이 SequencedCollection 을 확장한다
  MyList.reversed() 는 그냥 내 메서드   -> reversed() 가 List 에 생겼다
        |                                    |
  컴파일된다 · 실행된다                 반환 타입이 안 맞아 컴파일 에러
```

그림 해설 (한 단계씩):

- ★ **17에서 컴파일되던 코드가 21에서 안 된다.** 소스 비호환이다.
- 대상은 **`List`·`Deque` 등을 구현하면서 같은 이름의 메서드를 가진 클래스**다.\
  `reversed`·`getFirst`·`getLast`·`addFirst`·`addLast`·`removeFirst`·`removeLast` 일곱 이름.
- 반대 방향(21에서 컴파일한 것을 17에서 실행)은 아예 안 돈다 — **클래스 파일 버전**에서 막힌다.

```text
오류: 기본 클래스 Ex을(를) 로드하는 중 LinkageError가 발생했습니다.
	java.lang.UnsupportedClassVersionError: Ex has been compiled by a more recent version of the Java Runtime (class file version 65.0), this version of the Java Runtime only recognizes class file versions up to 61.0
```

비용 — 이것이 **기존 계층에 인터페이스를 끼워 넣은 값**이다.\
이름이 겹칠 확률이 낮은 쪽을 골랐지만 0은 아니었다.

## 문법 — 형태와 규칙

직접 쓴 최소 예제다. 출력은 전부 실행 결과다.

### 세 인터페이스의 메서드 지도

| | `SequencedCollection<E>` | `SequencedSet<E>` | `SequencedMap<K,V>` |
|---|---|---|---|
| 첫 | `getFirst()` | 상속 | `firstEntry()` |
| 끝 | `getLast()` | 상속 | `lastEntry()` |
| 앞에 넣기 | `addFirst(e)` | 상속 | `putFirst(k, v)` |
| 뒤에 넣기 | `addLast(e)` | 상속 | `putLast(k, v)` |
| 앞에서 빼기 | `removeFirst()` | 상속 | `pollFirstEntry()` |
| 뒤에서 빼기 | `removeLast()` | 상속 | `pollLastEntry()` |
| 역순 뷰 | `reversed()` | `reversed()` — 반환 타입만 좁힘 | `reversed()` |
| 뷰 | — | — | `sequencedKeySet()` · `sequencedValues()` · `sequencedEntrySet()` |

- **`SequencedSet` 은 새 메서드를 하나도 안 더한다.** 반환 타입만 좁힌다.
- `Map` 쪽 이름이 `get*` 이 아니라 `first*`/`poll*` 인 것은 **기존 `SortedMap`·`NavigableMap` 의 이름과 맞춘** 것이다.

### 빈 컬렉션에서의 규약이 갈린다

| 호출 | 비었을 때 |
|---|---|
| `getFirst()` / `getLast()` | **`NoSuchElementException`** |
| `removeFirst()` / `removeLast()` | **`NoSuchElementException`** |
| `firstEntry()` / `lastEntry()` | **`null`** |
| `pollFirstEntry()` / `pollLastEntry()` | **`null`** |

- **`Collection` 쪽은 던지고 `Map` 쪽은 `null`** 이다. 실행 결과가 그렇다((7)).
- `Deque` 의 기존 `peekFirst()`·`pollFirst()` 도 `null` 을 준다 — 이름에 `peek`/`poll` 이 붙으면 `null` 이다.

### 역순 순회 — 세 가지 길

```java
// 1) 21+ — 가장 짧다
for (String s : list.reversed()) { }

// 2) ListIterator — 21 이전 (43번)
for (var it = list.listIterator(list.size()); it.hasPrevious(); ) { it.previous(); }

// 3) Deque 전용 — 6+
for (var it = deque.descendingIterator(); it.hasNext(); ) { it.next(); }
```

**실행 결과** (`Ex.java` — 42-b, 21·25 동일)

```text
--- 7) 역순 순회를 그냥 for 로
for (s : big.reversed()) : cba
스트림도 뒤집힌다        : [c, b, a]
```

- `reversed().stream()` 도 역순이다 — encounter order 가 뒤집혔기 때문이다.
- javadoc 이 `stream`·`spliterator`·`toArray`·`forEach` 까지 encounter order 를 따른다고 명시한다.

### 불변 컬렉션도 `reversed()` 는 된다

**실행 결과** (`Ex.java` — 42-b, 21·25 동일)

```text
--- 6) 불변 리스트의 reversed()
List.of.reversed()        : [c, b, a]  타입 java.util.ReverseOrderListView$Rand
List.of.reversed().add    : UnsupportedOperationException
```

- 읽기 전용 뷰이므로 문제가 없다. **쓰기만 막힌다.**

## 어디서 틀리나

### 1. `reversed()` 를 복사본으로 믿는다

```java
List<String> snapshot = list.reversed();
list.add("new");                 // snapshot 도 바뀐다
```

- **뷰다.** 원본이 바뀌면 따라 바뀐다.
- 방어: `List.copyOf(list.reversed())` 또는 `new ArrayList<>(list.reversed())`.

### 2. `reversed()` 에 쓰면 원본이 안 바뀐다고 믿는다

```java
list.reversed().add("z");        // 원본의 "맨 앞" 에 들어간다
```

- 뷰의 **끝**에 붙이는 것이 원본의 **앞**이다. 실행 결과가 그것이다((4)).
- 헷갈리면 `addFirst`/`addLast` 를 원본에 직접 부른다.

### 3. `HashSet` 에 `getFirst()` 를 부른다

- **컴파일 에러**다. `HashSet` 은 `SequencedCollection` 이 아니다.
- 순서가 필요하면 **자료형을 `LinkedHashSet` 으로 바꾼다.** 그것이 의도를 타입에 적는 길이다.

### 4. `TreeSet.addFirst` 를 부른다

- **`UnsupportedOperationException`** 이다. 정렬 컬렉션은 위치를 지정할 수 없다.
- 컴파일은 통과한다 — 옵셔널 연산의 대가다(39번 (8)).
- `SequencedCollection` 을 파라미터로 받는 메서드에서 `addFirst` 를 부르면 **호출자가 무엇을 넘겼는지에 따라 터진다.**

### 5. 빈 컬렉션의 `getFirst()` 를 `null` 검사로 막으려 한다

```java
String s = list.getFirst();
if (s == null) { }               // 여기 오기 전에 NoSuchElementException
```

- **`Collection` 쪽은 던진다.** `isEmpty()` 를 먼저 보거나, `Map` 쪽의 `firstEntry()` 처럼 `null` 을 주는 것과 헷갈리지 않는다.

### 6. `put` 이 `LinkedHashMap` 의 순서를 바꿀 거라고 믿는다

```java
lhm.put("a", 99);                // 순서는 그대로다 — 값만 바뀐다
lhm.putLast("a", 99);            // 이것이 맨 뒤로 옮긴다
```

- 삽입 순서 모드에서 **재삽입은 순서를 안 바꾼다.** javadoc 명시이고 실행 결과도 그렇다((6)).
- 반대로 **접근 순서 모드에서는 `get` 이 순서를 바꾼다.** 같은 코드가 생성자 인자 하나로 갈린다.

### 7. 17 타깃 빌드에서 `getFirst()` 를 쓴다

```text
Ex.java:6: error: cannot find symbol
        System.out.println(list.getFirst());
                               ^
  symbol:   method getFirst()
  location: variable list of type List<String>
```

- `--release 17` 로 컴파일하면 **21에서 컴파일해도 같은 에러**가 난다((8)의 실행 결과).
- 라이브러리를 17 타깃으로 배포한다면 `get(0)` 을 계속 써야 한다.

### 8. `List` 를 구현한 내 클래스에 `reversed()` 같은 이름을 쓴다

- 21로 올리는 순간 **컴파일이 깨진다**((8)).
- 일곱 이름(`reversed`·`getFirst`·`getLast`·`addFirst`·`addLast`·`removeFirst`·`removeLast`)을 피한다.

## 구현 세부사항 대 언어 보장

| 관측한 것 | 보장인가 | 근거 |
|---|---|---|
| `SequencedCollection` 이 Java 21 | **보장** | `src.zip` 의 `@since 21` |
| `List`·`Deque`·`SortedSet` 이 하위 타입 | **보장 (21+)** | 각 인터페이스의 `extends` 절 |
| `HashSet`·`PriorityQueue` 가 **아님** | **보장** | 그 타입들에 `extends` 가 없다 |
| `reversed()` 가 **뷰** | **보장** | `SequencedCollection.reversed` javadoc — "reverse-ordered **view**" · `Collection` 의 「View Collections」 목록 |
| 뷰에 쓰면 원본에 반영 | **보장** | "If the collection implementation permits modifications to this view, the modifications **write through** to the underlying collection" |
| 원본의 변경이 뷰에 보이는 것 | **보장 아님** | "Changes to the underlying collection **might or might not** be visible in this reversed view, depending upon the implementation" |
| `rev.reversed() == src` | **보장 아님** | 최적화다. javadoc 에 없다 |
| 구체 타입 `ReverseOrderListView$Rand` 등 | **보장 아님** | 내부 클래스 |
| 빈 컬렉션의 `getFirst()` 가 NSEE | **보장** | `@throws NoSuchElementException if this collection is empty` |
| 빈 맵의 `firstEntry()` 가 `null` | **보장** | `@return the first key-value mapping, or `null` if the map is empty` |
| `TreeSet.addFirst` 가 UOE | **보장** | `SortedSet.addFirst` javadoc — "always throws `UnsupportedOperationException`" |
| `TreeSet.reversed()` 가 `descendingSet()` 과 같음 | **보장 아님** | 구현이 그렇게 돼 있을 뿐 |
| `putFirst`·`lastEntry` 가 접근 순서를 안 바꿈 | **보장** | `LinkedHashMap` javadoc — "do not generate entry accesses" |
| 17에서 컴파일되던 `reversed()` 재정의가 21에서 깨짐 | **보장** | 인터페이스 메서드 추가의 필연적 결과다 |

**두 JDK 실측** — 도는 프로그램 2개를 21.0.5 · 25.0.1 에서 돌려 `diff` 했다.

```text
42-a · 42-b : 두 버전 출력이 한 글자도 같다

17 에서는 컴파일 자체가 안 된다
  Ex.java:6: error: cannot find symbol  symbol: method getFirst()
  Ex.java:8: error: cannot find symbol  symbol: class SequencedCollection
  -> "17 에서 안 된다" 를 컴파일 에러로 확인했다. 추측이 아니다

21 javac --release 17 도 같은 에러다
  -> 17 타깃 빌드에서는 21 JDK 로 컴파일해도 못 쓴다
```

- ★ **이 주제는 "세 버전에서 같았다"를 쓸 수 없다.** 애초에 17에 없는 기능이다.
- 대신 **17에서 나는 에러를 실어** 경계를 고정했다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 일 | 고를 것 |
|---|---|
| 리스트의 첫·끝 원소 | **`getFirst()` / `getLast()`** (21+). 17 타깃이면 `get(0)` / `get(size()-1)` |
| `LinkedHashSet` 의 끝 원소 | **`getLast()`** — 21 이전에는 방법이 없었다 |
| `LinkedHashMap` 의 가장 오래된 항목 | **`firstEntry()`** / 꺼내며 지우려면 `pollFirstEntry()` |
| 역순 순회 | **`for (x : c.reversed())`** |
| 역순 **복사본** | `List.copyOf(c.reversed())` — 뷰를 보관하지 않는다 |
| 순서 있는 컬렉션을 받는 파라미터 | `SequencedCollection<E>` — `HashSet` 을 거르는 효과가 있다 |
| 순서가 있는 `Set` 파라미터 | `SequencedSet<E>` |
| 순서가 있는 `Map` 파라미터 | `SequencedMap<K,V>` — `HashMap` 을 거른다 |
| `TreeSet` 역순 | `reversed()`. 기존 코드는 `descendingSet()` 그대로 두어도 된다 |
| LRU 캐시 | 접근 순서 `LinkedHashMap` + `removeEldestEntry` 또는 `pollFirstEntry()` |
| 17 타깃 라이브러리 | **쓸 수 없다** — `--release 17` 에서 컴파일 에러 |
| `HashSet`·`HashMap` 에서 첫 원소 | **없다.** 자료형을 바꾼다 |

판단 규칙 세 줄.

- **순서가 계약이면 타입에 적는다** — `SequencedCollection`·`SequencedMap` 으로 받으면 `HashSet`·`HashMap` 이 안 들어온다.
- **`reversed()` 는 뷰다.** 보관하려면 복사한다.
- **`addFirst` 류는 옵셔널 연산이다.** 받은 컬렉션에 부르지 않는다.

## 핵심 문장

- `SequencedCollection`(21)은 **"첫·끝을 다루는 말"을 통일했다** — `get(0)`·`getFirst()`·`first()`·`iterator().next()` 넷이 `getFirst()` 하나가 됐다.
- **`LinkedHashSet`·`LinkedHashMap` 은 21 이전에 끝 원소를 얻을 방법이 아예 없었다.** 내부는 알고 있었는데 API 가 없었다.
- **`reversed()` 는 복사가 아니라 뷰다** — 원본이 바뀌면 따라 바뀌고, 뷰에 쓰면 원본에 간다. 뷰의 끝이 원본의 앞이다.
- 세 인터페이스는 **기존 타입에 소급 적용**됐다 — `List`·`Deque`·`LinkedHashSet`·`SortedSet`·`LinkedHashMap`·`SortedMap`. **`HashSet`·`HashMap`·`PriorityQueue`·`Set.of` 는 빠졌다**(encounter order 가 없다).
- 그 대가로 **17에서 컴파일되던 코드가 21에서 깨질 수 있다** — `List` 를 구현하면서 `reversed()` 같은 이름을 쓴 클래스가 그렇다.

## 관련 자료

- [`../39-collections-framework-map/`](../39-collections-framework-map/) — **이 주제의 선행.** 그쪽은 **계층이 어떻게 생겼나**까지, 여기는 **21에서 그 계층 중간에 무엇이 끼워 넣어졌나**부터
- [`../40-list-set-and-immutable-factories/`](../40-list-set-and-immutable-factories/) — **뷰 대 복사본의 정본.** `subList`·`unmodifiableList` 와 같은 성질이 `reversed()` 에도 있다
- [`../41-map-api-merge-compute/`](../41-map-api-merge-compute/) — `Map` 의 나머지 메서드와 뷰 셋. **`entrySet`·`merge` 는 그쪽이 정본**
- [`../43-iterator-and-fail-fast/`](../43-iterator-and-fail-fast/) — `reversed()` 이전에 역순 순회를 하던 `ListIterator`. **순회 API 는 그쪽이 정본**
- [`../11-interfaces-default-methods/`](../11-interfaces-default-methods/) — 기존 인터페이스에 메서드를 더하고도 구현체를 안 깨는 장치. **`getFirst` 가 `default` 인 이유**
- [`../28-comparable-comparator/`](../28-comparable-comparator/) — `SortedSet`·`SortedMap` 의 순서를 정하는 것
- [`../../../../../../history/java/java-21.md`](../../../../../../history/java/java-21.md) — **언제·왜 들어왔나(JEP 431)의 정본.**\
  그쪽은 **21이 무엇을 바꿨나**까지, 여기는 **그래서 어떻게 쓰고 무엇이 막히나**부터
- [`../../../../../data-structure/10-lru-cache/`](../../../../../data-structure/10-lru-cache/) — 접근 순서 `LinkedHashMap` 이 흉내 내는 그 자료구조. **알고리즘은 그쪽**
- [`../../../../../data-structure/02-linked-list/`](../../../../../data-structure/02-linked-list/) — `LinkedHashSet`·`LinkedHashMap` 안의 이중 연결 리스트. **구조는 그쪽**
- [`../../../../../data-structure/04-queue-deque/`](../../../../../data-structure/04-queue-deque/) — `Deque` 가 원래 무엇을 하는 물건인가
- [`../../../../../data-structure/16-red-black-tree/`](../../../../../data-structure/16-red-black-tree/) — `TreeSet`·`TreeMap` 의 내부
- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 42번)
- [`../05-arrays/`](../05-arrays/)(배열) — 배열에는 `reversed()` 가 없다. `Arrays.asList(arr).reversed()` 로 우회한다

## 용어 풀이

- **`SequencedCollection`** — 첫·끝이 정해져 있고 뒤집을 수 있는 컬렉션 인터페이스. Java 21.
- **`SequencedSet`** — `SequencedCollection` 이면서 `Set`. 메서드를 더하지 않고 `reversed()` 반환 타입만 좁힌다.
- **`SequencedMap`** — 첫·끝이 정해져 있는 `Map`. `firstEntry`·`putFirst`·`pollFirstEntry` 등.
- **encounter order(순회 순서)** — "첫 원소부터 끝 원소까지"가 정해져 있는 것. `HashSet` 에는 없다.
- **뷰(view)** — 원소를 저장하지 않고 원본에 위임하는 컬렉션. `reversed()` 가 돌려주는 것.
- **write through** — 뷰에 한 변경이 원본에 반영되는 것.
- **소급 적용(retrofit)** — 이미 있는 타입을 새 인터페이스의 하위 타입으로 만드는 것. 21이 `List`·`Deque` 등에 한 일.
- **소스 비호환(source incompatibility)** — 예전에 컴파일되던 소스가 새 버전에서 컴파일이 안 되는 것.
- **`default` 메서드** — 인터페이스가 본문까지 가진 메서드. 기존 구현체를 안 깨고 메서드를 더하는 장치(Java 8).
- **옵셔널 연산(optional operation)** — 구현체가 지원 안 해도 되는 메서드. `addFirst` 도 그중 하나다.
- **접근 순서(access-order)** — `LinkedHashMap` 의 셋째 생성자 인자. `true` 면 읽을 때마다 뒤로 옮긴다.

## 더 들어가면

- **`getLast()` 의 기본 구현은 `reversed()` 를 거친다.**

  ```java
  // JDK 21.0.5  java.base/java/util/SequencedCollection.java  — 실제 소스 그대로
      default E getLast() {
          return this.reversed().iterator().next();
      }
  ```

  구현체가 재정의하지 않으면 **역순 뷰를 만들고 그 첫 원소를 꺼낸다.**\
  `ArrayList` 같은 주요 구현은 재정의해서 O(1)이다. **직접 만든 `List` 구현체라면 이 기본 구현이 돈다.**
- **`removeFirst()` 의 기본 구현은 `Iterator.remove()` 를 쓴다.**

  ```java
  // JDK 21.0.5  java.base/java/util/SequencedCollection.java  — 실제 소스 그대로
      default E removeFirst() {
          var it = this.iterator();
          E e = it.next();
          it.remove();
          return e;
      }
  ```

  그래서 `Iterator.remove()` 를 지원 안 하는 컬렉션이면 여기서 UOE 가 전파된다([`../43-iterator-and-fail-fast/`](../43-iterator-and-fail-fast/)).
- **`SequencedCollection` 은 `equals`/`hashCode` 를 요구하지 않는다.**\
  javadoc 이 이유를 적어 놓았다 — `List` 와 `SequencedSet`(`Set` 에서 상속)의 요구가 **서로 충돌**하기 때문이다.\
  `List.equals` 는 순서를 보고 `Set.equals` 는 안 본다. 상위 인터페이스가 어느 한쪽을 못 고른다.
- **`sequencedKeySet()` 이 따로 있는 이유는 객체가 달라서가 아니라 `keySet()` 의 *선언 타입*이 `Set` 이기 때문이다.**

  ```text
  --- (Ex.java — 42-f, 21·25 동일)
  keySet 의 타입          : java.util.LinkedHashMap$LinkedKeySet
  sequencedKeySet 의 타입 : java.util.LinkedHashMap$LinkedKeySet
  두 객체가 같은가        : true
  keySet 은 SequencedSet 인가 : true
  ```

  ★ **`LinkedHashMap` 에서는 같은 객체가 나온다.** 런타임 타입도 `SequencedSet` 이다.\
  그런데 `Map.keySet()` 의 **선언 반환 타입이 `Set<K>`** 라 컴파일이 안 된다.

  ```text
  $ javac Ex.java                                        (Ex.java — 42-g, JDK 21)
  Ex.java:5: error: cannot find symbol
          System.out.println(m.keySet().reversed());
                                       ^
    symbol:   method reversed()
    location: interface Set<String>
  1 error
  ```

  기존 메서드의 반환 타입을 바꿀 수 없어 **이름이 다른 메서드를 새로 판 것**이다.
- **`reversed()` 가 뷰라는 것에는 비대칭이 있다.**\
  javadoc 은 "뷰에 쓰면 원본에 write through 된다"는 **보장**이고,
  "원본의 변경이 뷰에 보이는 것"은 **"might or might not"** 이다.\
  `ArrayList` 에서는 보였지만((4)) 그것이 계약은 아니다.
- **17 타깃과 21 타깃을 같은 소스로 유지하려면** `getFirst()` 를 못 쓴다.\
  멀티릴리스 JAR 로 갈라 놓을 수는 있으나, 대개는 **`get(0)` 을 계속 쓰는 쪽**이 싸다.
