# java/syntax/42 — `SequencedCollection` (21): 순서 있는 컬렉션의 공통 API — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러는 **Temurin JDK 에서 실제로 돌려 얻은 것**이다.\
> javadoc·소스 인용은 JDK 21.0.5 의 `lib/src.zip` 을 풀어 읽은 원문이다.\
> 도는 프로그램은 **21.0.5 · 25.0.1** 에서 돌렸다(출력 동일). **17 에서는 컴파일이 안 된다** — 그 에러도 실었다(9·10번).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 21 이전에는 어떻게 썼나

**출력** (`Ex.java` — 42-a, 21·25 동일)

```text
--- 1) 21 이전에는 첫 원소를 이렇게 꺼냈다
List           첫: list.get(0)                    끝: list.get(list.size()-1)
Deque          첫: deque.getFirst()               끝: deque.getLast()
LinkedHashSet  첫: lhs.iterator().next()          끝: 순회를 끝까지 돌아야 한다
SortedSet      첫: ts.first()                     끝: ts.last()
LinkedHashMap  첫: lhm.entrySet().iterator().next() 끝: 순회를 끝까지 돌아야 한다
SortedMap      첫: tm.firstKey()                  끝: tm.lastKey()
```

| 컬렉션 | 첫 | 끝 |
|---|---|---|
| `List` | `list.get(0)` | `list.get(list.size()-1)` |
| `Deque` | `getFirst()` | `getLast()` |
| `LinkedHashSet` | `iterator().next()` | **없다** |
| `SortedSet` | `first()` | `last()` |
| `LinkedHashMap` | `entrySet().iterator().next()` | **없다** |
| `SortedMap` | `firstKey()` | `lastKey()` |

**끝 원소를 O(1) 에 못 얻던 것**

- **`LinkedHashSet` 과 `LinkedHashMap`** 이다.
- ★ **내부적으로는 얻을 수 있었다.** 둘 다 **이중 연결 리스트**를 들고 있어 끝 노드를 알고 있다.
- **API 가 그것을 노출하지 않았을 뿐**이다. 그래서 순회를 끝까지 돌아야 했다(O(n)).
- 자료구조 자체는 [`../../../../../data-structure/02-linked-list/`](../../../../../data-structure/02-linked-list/) 가 정본이다.

### 2. 21 이 통일한 것

**`SequencedCollection` 의 메서드 — 일곱**

```text
  getFirst()   getLast()
  addFirst(e)  addLast(e)
  removeFirst() removeLast()
  reversed()
```

**`SequencedMap` 이 이름이 다른 이유**

- **`Map` 은 `Collection` 이 아니다**(39번). 원소가 아니라 **항목(`Map.Entry`)** 을 다룬다.
- 그리고 **기존 `SortedMap`·`NavigableMap` 의 이름 규칙에 맞췄다** — `firstKey`·`pollFirstEntry` 가 이미 있었다.

```text
  SequencedCollection        SequencedMap
    getFirst()        <->      firstEntry()
    getLast()         <->      lastEntry()
    addFirst(e)       <->      putFirst(k, v)
    addLast(e)        <->      putLast(k, v)
    removeFirst()     <->      pollFirstEntry()
    removeLast()      <->      pollLastEntry()
    reversed()        <->      reversed()
```

**`SequencedSet` 이 더하는 메서드 — 0개**

- 하나도 안 더한다. **`reversed()` 의 반환 타입만 `SequencedSet` 으로 좁힌다.**

> The only difference from the `SequencedCollection.reversed` method is that the return type of `SequencedSet.reversed` is `SequencedSet`.

**`SequencedMap` 에만 있는 뷰 셋**

- `sequencedKeySet()` · `sequencedValues()` · `sequencedEntrySet()`.
- 왜 따로 있는지는 8번이다.

### 3. 누가 하위 타입이 됐나

**출력** (`Ex.java` — 42-a, 21·25 동일)

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

**열한 줄**

| | 결과 |
|---|---|
| `ArrayList` | `true` |
| `ArrayDeque` | `true` |
| `HashSet` | **`false`** |
| `LinkedHashSet` (`SequencedSet`) | `true` |
| `TreeSet` (`SequencedSet`) | `true` |
| `PriorityQueue` | **`false`** |
| `List.of()` | `true` |
| `Set.of()` | **`false`** |
| `HashMap` (`SequencedMap`) | **`false`** |
| `LinkedHashMap` (`SequencedMap`) | `true` |
| `TreeMap` (`SequencedMap`) | `true` |

**`PriorityQueue` 가 빠진 이유**

- **순회 순서가 정렬 순서가 아니다.** 힙 배열을 그대로 돈다(39번 (5)).
- "꺼낼 때만 정렬"은 encounter order 가 **아니다.** `getFirst()` 가 무엇을 줘야 할지 정할 수 없다.

**`Set.of()` 가 빠진 이유**

- **순회 순서가 JVM 실행마다 다르다**([`../40-list-set-and-immutable-factories/`](../40-list-set-and-immutable-factories/) (6)).
- 순서가 "지정되지 않았다"고 javadoc 이 못박은 것에 `getFirst()` 를 줄 수는 없다.
- 반면 **`List.of()` 는 됐다** — 불변이어도 순서가 계약이기 때문이다.

**`ArrayDeque` 는 `List` 가 아니다**

- `List=false`. `SequencedCollection` 이지만 **인덱스 접근이 없다.**

### 4. ★ `reversed()` 는 복사인가 뷰인가

**출력** (`Ex.java` — 42-b, 21·25 동일)

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
--- 2) 인덱스도 뒤집힌다
l            : [a, b, c, d]  l.get(0)=a l.indexOf("c")=2
l.reversed() : [d, c, b, a]  get(0)=d indexOf("c")=1
l.reversed().subList(0,2) : [d, c]
```

**(A)~(D)**

- **(A)** `rev` 가 `[d, c, b, a]` — **따라 바뀐다.**
- **(B)** `src` 가 `[z, a, b, c, d]` — **`"z"` 가 앞에 들어갔다.**
- **(C)** `src` 가 `[z, a, b, c, Z]` — 뷰의 0번이 원본의 끝이다.
- **(D)** `true`. 두 번 뒤집으면 **원본 객체 그 자체**가 나온다.

**`"z"` 가 앞에 들어가는 이유**

```text
   rev 에서 add 는 "뷰의 끝에 붙인다"

   rev  [d][c][b][a]  + z  ->  [d][c][b][a][z]
                                            ^
   그 자리는 원본에서 어디인가?

   src  [a][b][c][d]  를 뒤집은 것이 rev 이므로
   rev 의 끝  =  src 의 앞
        |
   src  [z][a][b][c][d]
```

**`rev` 의 구체 타입**

- **`java.util.ReverseOrderListView$Rand`** — `RandomAccess` 원본용 래퍼다.
- `LinkedList` 를 뒤집으면 `LinkedList$ReverseOrderLinkedListView`,
  `ArrayDeque` 는 `ReverseOrderDequeView`, `LinkedHashSet` 은 `LinkedHashSet$1ReverseLinkedHashSetView` 다(42-f).

**인덱스도 뒤집힌다**

- `get(0)` 이 원본의 마지막이고, `indexOf("c")` 가 `2` 대신 `1` 이다.
- `subList` 도 역방향 기준으로 잘린다 — **뷰 위의 뷰**다.

**javadoc 이 뷰라고 적은 자리**

> Returns a reverse-ordered **view** of this collection. (`SequencedCollection.reversed`)

> Other examples of view collections include collections that provide a different representation of the same elements, for example, as provided by `List.subList`, `NavigableSet.subSet`, `Map.entrySet`, or **`SequencedCollection.reversed`**. (`Collection` 의 「View Collections」)

**원본의 변경이 뷰에 보이는 것은 보장인가**

- **아니다.** javadoc 이 두 방향을 다르게 적는다.

> If the collection implementation permits modifications to this view, the modifications **"write through"** to the underlying collection. Changes to the underlying collection **might or might not** be visible in this reversed view, depending upon the implementation.

- ★ **쓰기 방향만 보장이다.** `ArrayList` 에서는 읽기 방향도 보였지만((A)) 그것은 계약이 아니다.

### 5. `LinkedHashMap` 의 순서 조작

**출력** (`Ex.java` — 42-b · 42-h, 21·25 동일)

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
--- 삽입 순서 모드에서 put 은 순서를 안 바꾼다      (Ex.java — 42-h)
처음          : {a=1, b=2, c=3}
put("a",99)   : {a=99, b=2, c=3}
putLast("a")  : {b=2, c=3, a=100}
```

**(A)~(D)**

- **(A)** `putFirst("c", 30)` → `{c=30, a=1, b=2}` — 값도 바꾸고 **맨 앞으로 옮긴다.**
- **(B)** `putLast("a", 10)` → `{c=30, b=2, a=10}` — 맨 뒤로 옮긴다.
- **(C)** `pollFirstEntry()` → 반환 `c=30`, 맵은 `{b=2, a=10}` — **꺼내면서 지운다.**
- **(D)** `put("b", 99)` → **순서는 안 바뀐다.** 값만 바뀐다(42-h 의 `put("a",99)` 줄).

**javadoc 문장**

> Note that encounter order is not affected if a key is *re-inserted* into the map with the `put` method. (A key `k` is reinserted into a map `m` if `m.put(k, v)` is invoked when `m.containsKey(k)` would return `true` immediately prior to the invocation.) ... The encounter order of entries already in the map can be changed by using the `putFirst` and `putLast` methods.

**접근 순서 모드에서 `lastEntry()` 를 읽으면**

**출력** (`Ex.java` — 42-h, 21·25 동일)

```text
--- 접근 순서 모드에서 읽기가 순서를 바꾸나
처음          : {a=1, b=2, c=3}
get("a") 후    : {b=2, c=3, a=1}
lastEntry() 후 : {b=2, c=3, a=1}
firstEntry() 후: {b=2, c=3, a=1}
containsKey 후 : {b=2, c=3, a=1}
getOrDefault 후: {c=3, a=1, b=2}
```

- **`lastEntry()`·`firstEntry()` 는 순서를 안 바꾼다.**
- **`get` 과 `getOrDefault` 는 바꾼다.** `containsKey` 는 안 바꾼다.

**그 규칙을 적은 javadoc**

> Invoking the `put`, `putIfAbsent`, `get`, `getOrDefault`, `compute`, `computeIfAbsent`, `computeIfPresent`, or `merge` methods results in an access to the corresponding entry (assuming it exists after the invocation completes). ... *No other methods generate entry accesses.* ... Explicit-positioning methods such as `putFirst` or `lastEntry`, whether on the map or on its reverse-ordered view, perform the positioning operation and **do not generate entry accesses**.

- ★ 세는 목록을 **열거**해 놓았다. `containsKey` 가 거기 없어서 안 센다 — 실행 결과와 정확히 맞는다.

### 6. 안 되는 것

**출력** (`Ex.java` — 42-a · 42-e, 21·25 동일)

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
$ javac Ex.java                                    (Ex.java — 42-e, JDK 21)
Ex.java:6: error: cannot find symbol
        System.out.println(s.getFirst());
                            ^
  symbol:   method getFirst()
  location: variable s of type Set<String>
1 error
```

**여덟 줄**

| 호출 | 결과 |
|---|---|
| `HashSet.getFirst()` | **컴파일 에러** |
| `List.of("a").addFirst("z")` | `UnsupportedOperationException` |
| `TreeSet.addFirst("z")` | `UnsupportedOperationException` |
| `TreeSet.removeFirst()` | **`a`** (성공한다) |
| 빈 `ArrayList.getFirst()` | `NoSuchElementException` |
| 빈 `LinkedHashMap.firstEntry()` | **`null`** |
| 빈 `LinkedHashMap.pollFirstEntry()` | **`null`** |
| `TreeMap.putFirst("z", 9)` | `UnsupportedOperationException` |

**첫 줄만 성질이 다르다**

- **컴파일 에러**다. 나머지는 전부 런타임이다.
- `HashSet` 은 아예 그 타입이 아니므로 **컴파일러가 막아 준다.** 그것이 가장 좋은 실패다.

**`TreeSet` 이 `addFirst` 는 막고 `removeFirst` 는 허용하는 이유**

```text
   addFirst("z")                       removeFirst()

   "z 를 맨 앞에 두라"                  "맨 앞 것을 빼라"
        |                                    |
   순서는 비교자가 정한다                  빼는 것은 순서를 안 어긴다
   내가 위치를 정할 수 없다                남은 것들의 순서는 그대로다
        |                                    |
   UnsupportedOperationException          된다
```

- javadoc 이 이유까지 적어 놓았다.

> Throws `UnsupportedOperationException`. The encounter order induced by this set's comparison method determines the position of elements, so explicit positioning is not supported.

**빈 컬렉션과 빈 맵의 규약**

```text
   Collection 쪽                       Map 쪽

   getFirst()      -> NoSuchElement    firstEntry()     -> null
   getLast()       -> NoSuchElement    lastEntry()      -> null
   removeFirst()   -> NoSuchElement    pollFirstEntry() -> null
   removeLast()    -> NoSuchElement    pollLastEntry()  -> null
        |                                    |
   던진다                               null 을 준다
```

- ★ **정반대다.** `Map` 쪽은 전통적으로 "없으면 `null`" 이다(`get` 도 그렇다).
- 이름에 `peek`/`poll` 이 붙으면 `null`, `get`/`remove` 면 예외 — `Deque` 에서 온 관례다.

### 7. `TreeSet.reversed()` 와 `descendingSet()`

**출력** (`Ex.java` — 42-b, 21·25 동일)

```text
--- 3) 정렬 컬렉션의 reversed()
TreeSet             : [a, b, c]  타입 java.util.TreeSet
TreeSet.reversed()  : [c, b, a]
descendingSet() 과 같은가 : true
원본에 d 추가 후 뷰 : [d, c, b, a]
```

- **`equals` 로 같다.** 내용이 같은 역순 집합이다.
- **`TreeSet.reversed()` 의 구체 타입은 `java.util.TreeSet`** 이다 — `descendingSet()` 을 그대로 쓴다.
- **둘 다 뷰다.** 원본에 `d` 를 넣으면 둘 다 `[d, c, b, a]` 가 된다.

**새 코드에서는 `reversed()`**

- **이름 하나로 모든 `SequencedCollection` 에 통하기 때문**이다.
- `descendingSet()` 은 `NavigableSet` 에만 있다 — `ArrayList` 에는 없다.
- 기존 코드를 굳이 고칠 필요는 없다. `descendingSet`·`descendingMap`·`descendingIterator` 는 그대로 남아 있다.

### 8. `sequencedKeySet()` 이 왜 따로 있나

**출력** (`Ex.java` — 42-f, 21·25 동일)

```text
keySet 의 타입          : java.util.LinkedHashMap$LinkedKeySet
sequencedKeySet 의 타입 : java.util.LinkedHashMap$LinkedKeySet
두 객체가 같은가        : true
내용이 같은가           : true
keySet 은 SequencedSet 인가 : true
```

```text
$ javac Ex.java                                    (Ex.java — 42-g, JDK 21)
Ex.java:5: error: cannot find symbol
        System.out.println(m.keySet().reversed());
                                     ^
  symbol:   method reversed()
  location: interface Set<String>
1 error
```

**(A)~(C)**

- **(A)** `m.keySet() == m.sequencedKeySet()` → **`true`.** 같은 객체다.
- **(B)** `m.keySet() instanceof SequencedSet` → **`true`.** 런타임 타입은 이미 `SequencedSet` 이다.
- **(C)** `m.keySet().reversed()` → **컴파일 에러.**

**런타임 타입인가 선언 타입인가**

- ★ **선언 타입 때문이다.** `Map.keySet()` 의 반환 타입이 `Set<K>` 로 선언돼 있다.
- 객체는 이미 `SequencedSet` 인데 **컴파일러가 그것을 모른다.**

**새 이름이 필요했던 이유**

```text
   Map.keySet() 의 반환 타입을 SequencedSet 으로 바꾼다?

   -> Map 을 구현한 세상의 모든 클래스가 영향을 받는다
   -> 대부분의 Map 은 순서가 없어서 SequencedSet 을 돌려줄 수 없다
        |
   그래서 기존 메서드는 그대로 두고
   SequencedMap 에만 sequencedKeySet() 을 새로 팠다
```

- **기존 메서드의 반환 타입은 호환을 깨지 않고는 못 바꾼다.** 그 제약이 만든 이름이다.

### 9. 17 에서는

**JDK 17 의 `javac`** (`Ex.java` — 42-c)

```text
Ex.java:6: error: cannot find symbol
        System.out.println(list.getFirst());
                               ^
  symbol:   method getFirst()
  location: variable list of type List<String>
Ex.java:7: error: cannot find symbol
        System.out.println(list.reversed());
                               ^
  symbol:   method reversed()
  location: variable list of type List<String>
Ex.java:8: error: cannot find symbol
        SequencedCollection<String> sc = list;
        ^
  symbol:   class SequencedCollection
  location: class Ex
3 errors
```

**JDK 21 의 `javac --release 17`**

- **같은 에러 3개**다. 한 글자도 다르지 않다.
- 즉 **21 JDK 로 빌드해도 17 타깃이면 못 쓴다.** `--release` 가 API 까지 17 로 제한한다.

**21 에서 컴파일한 클래스를 17 로 실행하면**

```text
오류: 기본 클래스 Ex을(를) 로드하는 중 LinkageError가 발생했습니다.
	java.lang.UnsupportedClassVersionError: Ex has been compiled by a more recent version of the Java Runtime (class file version 65.0), this version of the Java Runtime only recognizes class file versions up to 61.0
```

- `getFirst()` 에 닿기도 전에 **클래스 파일 버전**에서 막힌다(65.0 = 21, 61.0 = 17).

### 10. 17 에서 되던 것이 21 에서 깨진다

**출력** (`Ex.java` — 42-d)

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

- **JDK 17 에서는 컴파일되고 실행된다** — `뒤집힌 문자열` 이 찍힌다.
- **JDK 21(·25)에서는 컴파일 에러**다. 반환 타입이 안 맞는다.

**충돌할 수 있는 이름 — 일곱**

```text
  reversed  getFirst  getLast  addFirst  addLast  removeFirst  removeLast
```

- `Map` 쪽까지 세면 `firstEntry`·`lastEntry`·`putFirst`·`putLast`·`pollFirstEntry`·`pollLastEntry`·
  `sequencedKeySet`·`sequencedValues`·`sequencedEntrySet` 이 더해진다.

**이 현상의 이름**

- **소스 비호환(source incompatibility)** 이다.
- 예전에 컴파일되던 **소스**가 새 버전에서 컴파일이 안 되는 것 — 바이너리 호환과 다르다.
- 기존 계층에 인터페이스를 끼워 넣으면 피할 수 없는 대가다. JEP 431 이 이름 충돌 위험을 감수하고 고른 길이다.

### 11. 어느 것을 쓰는가

| 상황 | 답 |
|---|---|
| 리스트를 역순으로 돈다 | **`for (x : list.reversed())`** |
| 역순 결과를 **보관**한다 | **`List.copyOf(list.reversed())`** — 뷰를 보관하지 않는다 |
| `LinkedHashSet` 의 마지막 원소 | **`set.getLast()`** — 21 이전에는 방법이 없었다 |
| LRU 에서 가장 오래된 항목을 꺼내 지운다 | **`map.pollFirstEntry()`** |
| "순서 있는 컬렉션만 받는다" | 파라미터를 **`SequencedCollection<E>`** 로 — `HashSet` 이 안 들어온다 |
| 17 타깃에서 첫 원소 | **`list.get(0)`** — `getFirst()` 는 `--release 17` 에서 컴파일 에러(9번) |

### 12. 무엇이 보장인가

| 관측 | 보장? | 근거 |
|---|---|---|
| `reversed()` 가 뷰 | **그렇다** | `SequencedCollection.reversed` javadoc — "reverse-ordered **view**" |
| 뷰에 쓴 것이 원본에 반영 | **그렇다** | "the modifications **write through** to the underlying collection" |
| 원본의 변경이 뷰에 보임 | **아니다** | "**might or might not** be visible in this reversed view, depending upon the implementation" |
| `rev.reversed() == src` | **아니다** | javadoc 에 없다. 구현의 최적화다 |
| `TreeSet.reversed()` 가 `descendingSet()` 과 같은 것 | **아니다** | 구현이 그렇게 돼 있을 뿐. `equals` 로 같다는 것만 관측이다 |

- ★ **뷰의 두 방향이 비대칭**이라는 것이 이 표의 핵심이다.\
  쓰기는 보장이고 읽기는 "might or might not" 이다.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Ex.java` (42-a) | 21 이전의 여섯 가지 관용구, 통일된 `getFirst`/`getLast`/`reversed` 7타입, `instanceof` 14줄, 안 되는 것 8줄 | 21 · 25 (**출력 동일**) |
| `Ex.java` (42-b) | `reversed()` 가 뷰인 것(양방향)·`rev.reversed()==src`·인덱스 반전·`subList`, `TreeSet.reversed` 와 `descendingSet`, `LinkedHashMap` 의 `putFirst`/`putLast`/`pollFirstEntry`/`sequenced*`, 접근 순서 모드, 불변 리스트의 `reversed`, 역순 `for`·스트림 | 21 · 25 (**출력 동일**) |
| `Ex.java` (42-c) | `getFirst`·`reversed`·`SequencedCollection` 이 **17 에서 컴파일 안 되는 것**, `--release 17` 도 같은 것, 21 클래스를 17 로 실행할 때의 `UnsupportedClassVersionError` | 17(컴파일 실패) · 21(`--release 17` 컴파일 실패) · 21(성공) · 17(실행 실패) |
| `Ex.java` (42-d) | `ArrayList` 를 확장하며 `String reversed()` 를 둔 클래스 — **17 에서 되고 21·25 에서 컴파일 에러** | 17(성공·실행) · 21(에러) · 25(에러) |
| `Ex.java` (42-e) | `Set` 선언 변수에 `getFirst()` 를 부른 컴파일 에러 | 21 · 25 (같은 에러) |
| `Ex.java` (42-f) | `keySet()` 과 `sequencedKeySet()` 이 **같은 객체**인 것, 구현체별 `reversed()` 구체 타입 4종 | 21 · 25 (**출력 동일**) |
| `Ex.java` (42-g) | `m.keySet().reversed()` 의 컴파일 에러(선언 타입이 `Set`) | 21 (컴파일만) |
| `Ex.java` (42-h) | 삽입 순서 모드에서 `put` 이 순서를 안 바꾸는 것, 접근 순서 모드에서 `get`·`getOrDefault` 는 세고 `containsKey`·`firstEntry`·`lastEntry` 는 안 세는 것 | 21 · 25 (**출력 동일**) |
| `src.zip` 열람 | `SequencedCollection` 의 `@since 21`·encounter order 정의·`getLast`/`removeFirst` 의 `@implSpec`, `SequencedSet`·`SequencedMap` 의 메서드, `SortedSet.addFirst` 의 "always throws", `LinkedHashMap` 의 접근 순서 규칙, `Collection` 의 「View Collections」 | 21 |

**javac 20회 · java 13회.**

**버전별로 갈린 것**

```text
21 vs 25 : 도는 프로그램 4개(42-a·42-b·42-f·42-h) 출력이 한 글자도 같다

17       : 이 주제의 API 가 아예 없다
  42-c  -> cannot find symbol: getFirst / reversed / class SequencedCollection
  42-d  -> 17 에서는 컴파일·실행 성공, 21·25 에서 컴파일 에러  (소급 적용의 대가)
  21 --release 17 -> 42-c 와 같은 에러 3개
```

- ★ **이 주제에서는 "세 버전에서 같았다"를 쓸 수 없다.** 17에 기능이 없기 때문이다.
- 대신 **17에서 나는 에러를 실어** 경계를 고정했다. 추측으로 "17에는 없다"고 적지 않았다.

**구현 의존 항목** (버전이 오르면 다시 돌려야 하는 것)

- `reversed()` 의 구체 타입 — `ReverseOrderListView$Rand` · `LinkedList$ReverseOrderLinkedListView` ·
  `ReverseOrderDequeView` · `LinkedHashSet$1ReverseLinkedHashSetView` · `LinkedHashMap$ReversedLinkedHashMapView`.
- **`rev.reversed() == src`** 가 `true` 인 것 — 최적화다.
- `TreeSet.reversed()` 가 `descendingSet()` 과 같은 것을 돌려주는 것.
- `keySet() == sequencedKeySet()` 인 것 — `LinkedHashMap` 의 구현이 그럴 뿐이다.
- **원본의 변경이 뷰에 보이는 것** — javadoc 이 "might or might not" 이라고 적었다.
- 컴파일 에러 문구 — `javac` 메시지는 릴리스마다 다듬어진다.
- **Java 22~24 는 안 돌려 봄** — 이 머신에 17·21·25 만 있다.
