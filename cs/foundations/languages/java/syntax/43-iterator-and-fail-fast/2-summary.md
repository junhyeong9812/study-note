# java/syntax/43 — `Iterator`·`ListIterator`·fail-fast 와 `ConcurrentModificationException` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **선행** — [`../39-collections-framework-map/`](../39-collections-framework-map/). `Collection` 이 `Iterable` 이라는 것이 전제다.
> **기준 소스** — JDK 21.0.5 의 `lib/src.zip` 을 **직접 풀어 읽은** javadoc 과 구현이다.\
> `java.base/java/util/Iterator.java` — 세 메서드의 계약과 `remove()` 의 기본 구현.\
> `java.base/java/util/ConcurrentModificationException.java` — 클래스 javadoc(`best-effort basis` 문단).\
> `java.base/java/util/AbstractList.java` — `protected transient int modCount` 의 javadoc.\
> `java.base/java/util/ArrayList.java` — `Itr`·`ListItr` 의 `hasNext`/`next`/`remove`/`add`, `forEach`, `removeIf` 구현.\
> 인용은 **그 파일에서 복사한 것만** 옮겼다.
> **실행 검증** — 이 문서의 모든 출력·에러는 Temurin JDK 에서 **실제로 돌려** 얻은 것이다.\
> 프로그램 3개. 둘은 **17.0.13 · 21.0.5 · 25.0.1** 셋 다에서 돌려 `diff` 했고(출력 동일),
> `ListIterator` 쪽은 21·25 에서 돌렸다.
> **버전** — `Iterator`·`ListIterator` 는 **Java 1.2**. `Iterator.remove()` 의 `default` 구현은 **Java 8**.\
> `Collection.removeIf` 는 **Java 8**. `@since` 는 `src.zip` 에서 직접 읽었다. 21·25 에 새로 생긴 것은 없다.
> **범위** — **향상된 `for` 라는 문법**(무엇 위에서 도나·배열과의 차이·레이블 `break`)은
> [`../20-control-flow-statements/`](../20-control-flow-statements/) 가 정본이다.\
> 그쪽은 **향상된 `for` 를 설명하는 데 필요한 만큼**(`hasNext`/`next`/`remove` 셋)까지,\
> 여기는 **`Iterator` 인터페이스 자체의 계약·`ListIterator`·안전한 삭제 셋·fail-fast 의 구현과 그 한계**부터다.\
> 자료구조의 순회 비용(연결 리스트 대 배열)은 [`../../../../../data-structure/`](../../../../../data-structure/) 가 정본이다.
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**이터레이터는 책에 끼운 책갈피다.**

| 비유 | 실체 |
|---|---|
| 책갈피를 끼운다 | `Iterator it = c.iterator()` |
| 다음 장이 있나 본다 | `it.hasNext()` |
| 한 장 넘긴다 | `it.next()` |
| **방금 읽은 장을 찢는다** | `it.remove()` |
| 뒤로도 넘길 수 있는 책갈피 | `ListIterator` — `previous()`·`set()`·`add()` |
| **책갈피가 기억해 둔 "이 책의 쪽수"** | `expectedModCount` |
| 책 자체의 쪽수 | `modCount` |
| 둘이 다르면 "누가 책을 고쳤다" | `ConcurrentModificationException` |

**똑같은 구조로** 자바가 동작한다: 책갈피 = 이터레이터, 쪽수 대조 = `modCount` 검사.

```text
     list [e0][e1][e2][e3][e4]        modCount = 5
                ^
             cursor = 1               expectedModCount = 5   <- 책갈피가 적어 둔 값

     list.remove("e1")  ->  modCount = 6

     it.next()  ->  5 != 6  ->  ConcurrentModificationException
```

핵심은 **이 대조가 완벽하지 않다**는 것이다.

```text
   크기 5 리스트를 향상된 for 로 돌면서 하나를 지우면

     e0 지움 -> ConcurrentModificationException
     e1 지움 -> ConcurrentModificationException
     e2 지움 -> ConcurrentModificationException
     e3 지움 -> 예외 없음. 그리고 e4 는 루프에 들어오지도 않는다   <- 여기
     e4 지움 -> ConcurrentModificationException
```

- **끝에서 두 번째를 지우면 안 터진다.** 그리고 **마지막 원소를 조용히 건너뛴다.**
- javadoc 이 그것을 미리 인정해 놓았다 — **"on a best-effort basis"**.

> **fail-fast** — 잘못된 상태를 발견 즉시 예외로 멈추는 설계.\
> 예: 순회 중에 리스트가 바뀐 것을 `next()` 에서 발견하고 바로 던지는 것.

> **best-effort** — "되는 만큼만 해 본다". 감지하면 던지지만 못 할 수도 있다는 뜻.\
> 예: 위에서 `e3` 를 지운 경우는 감지되지 않는다.

실무에서 이게 터지는 자리는 **"목록을 돌면서 조건에 맞는 걸 지우자"** 한 줄이다.\
운이 나쁘면 예외가 나고, **운이 더 나쁘면 예외 없이 원소 하나가 처리에서 빠진다.**

## 이 주제가 답하려는 질문

원고가 없는 API 주제라 「문제」 대신 이 세 질문을 둔다.

1. `Iterator` 의 세 메서드는 **무엇을 약속하고 무엇을 어기면 무엇이 나오나** —
   그리고 `ListIterator` 는 무엇을 더 주나.
2. fail-fast 는 **어떻게 구현돼 있나**(`modCount`) — 그리고 **왜 보장이 아닌가.**
3. 순회 중에 안전하게 지우는 법 **셋**은 무엇이고 각각 언제 쓰나.

## 예시 데이터 — 이 묶음이 공유하는 것

39~43번은 같은 데이터를 쓴다. 다만 이 주제는 **위치가 중요**해서 위치가 이름에 드러나는 것을 쓴다.

```text
크기 5, 인덱스가 이름에 박힌 리스트
  ["e0", "e1", "e2", "e3", "e4"]

  - e3 = 끝에서 두 번째   <- fail-fast 의 구멍이 드러나는 자리
  - e4 = 마지막
```

## 동작 방식

### (1) `Iterator` 의 계약 — 세 메서드와 세 예외

**언제 쓰나** — `for` 문 없이 직접 순회할 때. 순회하며 지울 때.

**실행 결과** (`Ex.java` — 43-a, 17·21·25 동일)

```text
--- 1) Iterator 계약 — next 전에 hasNext
hasNext : true / next : a / hasNext : false
끝난 뒤 next() : java.util.NoSuchElementException
--- 2) remove 는 next 뒤에 한 번만
next 전에 remove() : java.lang.IllegalStateException
next 뒤 remove()   : OK
연달아 remove()    : java.lang.IllegalStateException
--- 3) 불변 컬렉션의 Iterator
List.of 의 remove() : java.lang.UnsupportedOperationException
asList 의 remove()  : java.lang.UnsupportedOperationException: remove
```

```text
   Iterator 의 상태 기계

        [시작]
           |
      hasNext() = true
           |
        next()  --------> [next 직후]  ---- remove() ----> [remove 직후]
           ^                   |                                |
           |                   +-- remove() 한 번만 허용         |
           +-------------------+--------------------------------+
                               |
   hasNext() = false 인데 next() -> NoSuchElementException
   [시작] 또는 [remove 직후] 에서 remove() -> IllegalStateException
```

그림 해설 (한 단계씩):

- **`next()` 전에 `hasNext()` 를 봐야 한다.** 안 보고 부르면 `NoSuchElementException` 이다.
- **`remove()` 는 `next()` 한 번당 한 번**이다. 그것을 어기면 `IllegalStateException`.
- javadoc 이 그대로 적는다.

> Removes from the underlying collection the last element returned by this iterator (optional operation). **This method can be called only once per call to `next`.**

- **불변 컬렉션에서는 `UnsupportedOperationException`** 이다 — 옵셔널 연산이다(39번 (8)).
- `Arrays.asList` 쪽 메시지에 `remove` 가 붙는 이유는 **기본 구현이 던지기** 때문이다.

```java
// JDK 21.0.5  java.base/java/util/Iterator.java  — 실제 소스 그대로
    default void remove() {
        throw new UnsupportedOperationException("remove");
    }
```

비용 — 세 예외가 **서로 다른 실수**를 가리킨다.\
`NoSuchElementException` = 끝을 안 봤다 · `IllegalStateException` = 순서를 어겼다 ·
`UnsupportedOperationException` = 그 컬렉션이 못 한다.

### (2) fail-fast 의 구현 — `modCount` 두 개

**언제 쓰나** — `ConcurrentModificationException` 이 났을 때 "왜"를 설명해야 할 때.

**소스** (JDK 21.0.5 — 실제 파일에서 복사)

```java
// java.base/java/util/ArrayList.java  1035~1058행
    private class Itr implements Iterator<E> {
        int cursor;       // index of next element to return
        int lastRet = -1; // index of last element returned; -1 if no such
        int expectedModCount = modCount;

        public boolean hasNext() {
            return cursor != size;
        }

        public E next() {
            checkForComodification();
            int i = cursor;
            if (i >= size)
                throw new NoSuchElementException();
            Object[] elementData = ArrayList.this.elementData;
            if (i >= elementData.length)
                throw new ConcurrentModificationException();
            cursor = i + 1;
            return (E) elementData[lastRet = i];
        }
```

```java
// java.base/java/util/ArrayList.java  1093~1095행
        final void checkForComodification() {
            if (modCount != expectedModCount)
                throw new ConcurrentModificationException();
```

```text
     컬렉션                        이터레이터

     modCount = 5      <----->     expectedModCount = 5
        ^                                 ^
   add/remove 마다 +1            만들 때 한 번 베껴 둔다

     next() 가 부르는 checkForComodification() 이
     둘을 비교해서 다르면 던진다
```

그림 해설 (한 단계씩):

- **`modCount` 는 컬렉션의 필드**이고 **`expectedModCount` 는 이터레이터의 필드**다.
- 이터레이터를 만들 때 값을 **베껴 두고**, `next()` 마다 대조한다.
- `modCount` 의 javadoc 이 그 규칙을 정의한다.

> The number of times this list has been *structurally modified*. Structural modifications are those that change the size of the list, or otherwise perturb it in such a fashion that iterations in progress may yield incorrect results.

- ★ **"크기를 바꾸는" 것만 센다.** `set(i, x)` 는 구조적 수정이 아니라 `modCount` 가 안 오른다.
- 그리고 javadoc 이 **이 필드를 쓰는 것 자체가 선택**이라고 적는다.

> **Use of this field by subclasses is optional.** If a subclass wishes to provide fail-fast iterators (and list iterators), then it merely has to increment this field ... If an implementation does not wish to provide fail-fast iterators, this field may be ignored.

비용 — `int` 필드 하나와 비교 한 번. 거의 공짜다.\
대신 **정확하지 않다** — 다음 절이 그 이야기다.

### (3) ★ 안 터지는 경우 — fail-fast 는 보장이 아니다

**언제 쓰나** — "예외가 안 났으니 괜찮다"고 읽으려 할 때.

**실행 결과** (`Ex.java` — 43-a, 17·21·25 동일)

```text
--- 4) 어느 원소를 지울 때 터지나 (크기 5 리스트, 향상된 for)
지우는 원소       인덱스        결과                       돈 원소
e0           0          ConcurrentModificationException [e0]
e1           1          ConcurrentModificationException [e0, e1]
e2           2          ConcurrentModificationException [e0, e1, e2]
e3           3          예외 없음 -> [e0, e1, e2, e4] [e0, e1, e2, e3]
e4           4          ConcurrentModificationException [e0, e1, e2, e3, e4]
--- 5) 크기 2 리스트에서 첫 원소를 지우면
예외 없음 -> [b] / 돈 원소 [a]
```

```text
   e3 (끝에서 두 번째) 를 지운 순간

     전:  [e0][e1][e2][e3][e4]   size=5   cursor=4   (e3 를 방금 돌려줬다)
     후:  [e0][e1][e2][e4]       size=4   cursor=4

     hasNext() 는 무엇을 보나?   ->  cursor != size   ->  4 != 4  ->  false
                                          ^
                          modCount 를 안 본다! 그래서 검사 자체가 안 일어난다
     루프가 그냥 끝난다.
     e4 는 한 번도 본문에 들어오지 않았다.
```

그림 해설 (한 단계씩):

- **`hasNext()` 는 `checkForComodification()` 을 부르지 않는다.** `cursor != size` 한 줄뿐이다((2)의 소스).
- 원소가 하나 줄면서 `cursor` 와 `size` 가 **우연히 같아지는** 자리가 끝에서 두 번째다.
- 그래서 **예외도 없고 마지막 원소도 처리 안 된다.** 결과만 조용히 틀린다.
- 크기 2 리스트에서 첫 원소를 지워도 같다 — `"b"` 가 루프에 안 들어왔다.
- javadoc 이 이 성질을 미리 인정해 놓았다.

> Note that fail-fast behavior **cannot be guaranteed** as it is, generally speaking, impossible to make any hard guarantees in the presence of unsynchronized concurrent modification. Fail-fast operations throw `ConcurrentModificationException` **on a best-effort basis**. Therefore, it would be wrong to write a program that depended on this exception for its correctness: *`ConcurrentModificationException` should be used only to detect bugs.*

- **"only to detect bugs"** — 제어 흐름으로 쓰지 말라는 뜻이다.
- `Iterator` 쪽 javadoc 도 같은 말을 다르게 적는다.

> The behavior of an iterator is **unspecified** if the underlying collection is modified while the iteration is in progress in any way other than by calling this method, unless an overriding class has specified a concurrent modification policy.

비용 — **"예외가 안 났다"가 "맞게 돌았다"가 아니다.**\
이것이 이 주제 전체의 결론이다. 순회 중 수정은 **예외가 나면 운이 좋은 것**이다.

### (4) 같은 자리에서 `stream().forEach` 는 전혀 다른 것을 던진다

**언제 쓰나** — `for` 를 스트림으로 바꿨을 때.

**실행 결과** (`Ex.java` — 43-a, 17·21·25 동일)

```text
--- 7) forEach 와 스트림은 어떤가
forEach e3 제거 : java.util.ConcurrentModificationException
stream e3 제거  : java.lang.NullPointerException: Cannot invoke "String.equals(Object)" because "<parameter2>" is null
forEach e0 제거 : java.util.ConcurrentModificationException
```

```text
   같은 일 — e3 를 지운다

   향상된 for      -> 예외 없음, e4 건너뜀        (3)
   list.forEach    -> ConcurrentModificationException
   stream().forEach-> NullPointerException        <- 전혀 다른 예외
                            ^
              스플리터레이터가 줄어든 배열의 빈 칸을 읽어 null 을 꺼냈다
```

그림 해설 (한 단계씩):

- **같은 코드 세 형태가 세 가지 다른 결과를 낸다.** 예외가 나기도, 안 나기도, 엉뚱한 예외가 나기도 한다.
- `list.forEach` 는 **끝에서 한 번 대조**한다.

```java
// JDK 21.0.5  java.base/java/util/ArrayList.java  1590~1599행 — 실제 소스 그대로
    public void forEach(Consumer<? super E> action) {
        Objects.requireNonNull(action);
        final int expectedModCount = modCount;
        final Object[] es = elementData;
        final int size = this.size;
        for (int i = 0; modCount == expectedModCount && i < size; i++)
            action.accept(elementAt(es, i));
        if (modCount != expectedModCount)
            throw new ConcurrentModificationException();
    }
```

- **`size` 를 루프 시작 전에 베껴 둔다.** 그래서 줄어든 뒤에도 원래 크기만큼 돌려다가 끝에서 던진다.
- `stream().forEach` 는 스플리터레이터를 쓰는데, **배열이 줄면서 뒤쪽이 `null`** 이 돼 그 `null` 을 람다가 받았다.
- ★ **`NullPointerException` 이 `ConcurrentModificationException` 보다 훨씬 나쁘다.** 원인이 전혀 안 보인다.

비용 — 없다. **순회 중에 컬렉션을 고치지 않는 것**이 유일한 답이다.

### (5) 안전하게 지우는 법 — 셋

**언제 쓰나** — 조건에 맞는 원소를 지울 때. 즉 자주.

**실행 결과** (`Ex.java` — 43-b, 17·21·25 동일)

```text
--- 1) 안전하게 지우는 법 셋
(1) Iterator.remove : [e0, e2, e3, e4]
(2) removeIf        : [e0, e2, e3, e4]
(3) 복사본 순회      : [e0, e2, e3, e4]
--- 2) 전부 지울 때도 셋 다 된다
Iterator.remove 로 전부 : []
removeIf 로 전부        : []
```

```java
// (1) Iterator.remove — 1.2
for (Iterator<String> it = l.iterator(); it.hasNext(); )
    if (it.next().endsWith("1")) it.remove();

// (2) removeIf — 8+   가장 짧다
l.removeIf(s -> s.endsWith("1"));

// (3) 복사본 순회 — 원본을 직접 고친다
for (String s : new ArrayList<>(l))
    if (s.endsWith("1")) l.remove(s);
```

```text
   (1) Iterator.remove            (2) removeIf              (3) 복사본 순회

   이터레이터가 지우면서          두 번 훑는다               복사본을 돌고
   expectedModCount 도            1) 지울 것 표시            원본을 고친다
   같이 갱신한다                  2) 한 번에 밀어낸다             |
        |                              |                    복사 비용 O(n)
   원소마다 뒤를 당긴다           밀기가 한 번뿐               원본이 뭔지 안 가린다
```

그림 해설 (한 단계씩):

- **(1)이 안전한 이유는 한 줄이다** — 지운 뒤 `expectedModCount = modCount` 를 다시 베낀다.

```java
// JDK 21.0.5  java.base/java/util/ArrayList.java  1060~1073행 — 실제 소스 그대로
        public void remove() {
            if (lastRet < 0)
                throw new IllegalStateException();
            checkForComodification();

            try {
                ArrayList.this.remove(lastRet);
                cursor = lastRet;
                lastRet = -1;
                expectedModCount = modCount;
            } catch (IndexOutOfBoundsException ex) {
                throw new ConcurrentModificationException();
            }
        }
```

- `cursor = lastRet` 도 중요하다 — **커서를 한 칸 되돌려** 건너뛰기를 막는다.
- **(2) `removeIf` 는 두 번 훑는다.** 소스 주석이 그렇게 적혀 있다.

```java
// JDK 21.0.5  java.base/java/util/ArrayList.java  1750~1776행 — 실제 소스 그대로(발췌)
    boolean removeIf(Predicate<? super E> filter, int i, final int end) {
        Objects.requireNonNull(filter);
        int expectedModCount = modCount;
        final Object[] es = elementData;
        // Optimize for initial run of survivors
        for (; i < end && !filter.test(elementAt(es, i)); i++)
            ;
        // Tolerate predicates that reentrantly access the collection for
        // read (but writers still get CME), so traverse once to find
        // elements to delete, a second pass to physically expunge.
        if (i < end) {
            final int beg = i;
            final long[] deathRow = nBits(end - beg);
            deathRow[0] = 1L;   // set bit 0
            for (i = beg + 1; i < end; i++)
                if (filter.test(elementAt(es, i)))
                    setBit(deathRow, i - beg);
            if (modCount != expectedModCount)
                throw new ConcurrentModificationException();
            modCount++;
```

- **`deathRow` 라는 비트 집합**에 지울 자리를 표시하고, 두 번째 패스에서 한 번에 밀어낸다.
- 그래서 **`modCount` 가 한 번만 오른다.** `Iterator.remove` 를 N 번 하는 것보다 싸다.
- 그리고 이 코드도 **람다 안에서 쓰기를 하면 CME 를 던진다.**

```text
--- 4) removeIf 안에서 리스트를 고치면
removeIf 안에서 add : java.util.ConcurrentModificationException
```

비용 —

| 방법 | 밀어내기 | 복사 | 언제 |
|---|---|---|---|
| `Iterator.remove` | 지울 때마다 | 없음 | 지우면서 다른 일도 할 때 |
| **`removeIf`** | **한 번** | 없음 | **조건만으로 지울 때 — 기본 선택** |
| 복사본 순회 | 지울 때마다 | O(n) | 원본이 어떤 타입인지 모를 때 |

### (6) 맵에서 지우기 — 뷰를 쓴다

**언제 쓰나** — `Map` 에서 조건에 맞는 항목을 지울 때.

**실행 결과** (`Ex.java` — 43-b, 17·21·25 동일)

```text
--- 5) HashMap 에서
맵 직접 remove : java.util.ConcurrentModificationException
entrySet Iterator.remove : {k0=0, k2=2, k3=3, k4=4}
entrySet().removeIf      : {k0=0, k2=2, k3=3, k4=4}
values().removeIf        : {k0=0, k2=2, k3=3, k4=4}
```

```java
m.entrySet().removeIf(e -> e.getValue() == 1);   // 키·값 둘 다 볼 수 있다
m.values().removeIf(v -> v == 1);                // 값만 보면 될 때
m.keySet().removeIf(k -> k.startsWith("tmp"));   // 키만 보면 될 때
```

- **뷰에서 지우면 맵이 바뀌고 CME 가 안 난다.** 뷰의 이터레이터가 `modCount` 를 같이 관리한다.
- 뷰가 무엇인지는 [`../41-map-api-merge-compute/`](../41-map-api-merge-compute/) 가 정본이다.

비용 — `entrySet()` 이 가장 넓다. 키와 값을 다 볼 수 있다.

### (7) `ListIterator` — 양방향 · `set` · `add`

**언제 쓰나** — 순회하며 **바꾸거나 끼워 넣어야** 할 때. 뒤에서부터 돌 때.

**실행 결과** (`Ex.java` — 43-c, 21·25 동일)

```text
--- 1) 커서는 원소가 아니라 원소 사이에 있다
동작                     nextIndex    previousIndex hasNext    hasPrevious
시작                     0            -1           true       false
next()=a               1            0            true       true
next()=b               2            1            true       true
previous()=b           1            0            true       true
```

```text
   커서는 칸이 아니라 "칸 사이" 에 있다

        [a]     [b]     [c]
       ^   ^   ^   ^   ^   ^
       0   |   1   |   2   3      <- 커서가 있을 수 있는 자리는 size+1 개

   커서가 1 일 때
     nextIndex() = 1      next()     -> b
     previousIndex() = 0  previous() -> a
```

그림 해설 (한 단계씩):

- **`next()` 와 `previous()` 는 같은 원소를 돌려줄 수 있다.** 커서가 그 사이에 있기 때문이다.
- `next()` 로 `b` 를 받고 바로 `previous()` 를 부르면 **다시 `b`** 다. 위 출력이 그것이다.
- `previousIndex()` 는 시작 시점에 **`-1`** 이다.

**실행 결과** (`Ex.java` — 43-c, 21·25 동일)

```text
--- 2) set 은 마지막으로 돌려준 원소를 바꾼다
next 뒤 set("A")        : [A, b, c]
next·previous 뒤 set("B") : [A, B, c]   <- previous 가 돌려준 원소가 대상이다
next 전에 set()          : java.lang.IllegalStateException
--- 3) add 는 커서 앞에 끼워 넣는다 — 그리고 안 터진다
순회하며 add : [a, b, b2, c]   <- ConcurrentModificationException 이 안 난다
같은 일을 리스트에 직접 : java.util.ConcurrentModificationException
--- 4) add 뒤에 방금 넣은 것을 다시 만나나
돈 원소 : [a, b, c] / 결과 : [a, b, b2, c]
--- 5) add 직후 set·remove 는?
add 직후 set()    : java.lang.IllegalStateException
add 직후 remove() : java.lang.IllegalStateException
```

```text
   ListIterator.add 는 안전하다

        [a][b][c]   cursor=2 (b 를 방금 돌려줬다)
              ^
         add("b2")
              |
        [a][b][b2][c]   cursor=3
                  ^
   커서가 새 원소 뒤로 간다 -> 방금 넣은 것을 다시 만나지 않는다
   그리고 expectedModCount 를 다시 베껴서 CME 를 피한다
```

그림 해설 (한 단계씩):

- **`set` 의 대상은 "마지막으로 돌려준 원소"** 다. `previous()` 뒤면 그것이 대상이다.
- **`add` 는 순회 중에 안전하다.** 같은 일을 리스트에 직접 하면 CME 다.
- 이유는 `Iterator.remove` 와 같다 — 내부에서 `expectedModCount` 를 다시 베낀다.

```java
// JDK 21.0.5  java.base/java/util/ArrayList.java  1145~1157행 — 실제 소스 그대로
        public void add(E e) {
            checkForComodification();

            try {
                int i = cursor;
                ArrayList.this.add(i, e);
                cursor = i + 1;
                lastRet = -1;
                expectedModCount = modCount;
            } catch (IndexOutOfBoundsException ex) {
                throw new ConcurrentModificationException();
            }
        }
```

- **`lastRet = -1`** 로 되돌리므로 `add` 직후의 `set`·`remove` 는 `IllegalStateException` 이다.
- 그리고 **방금 넣은 것을 다시 만나지 않는다** — 돈 원소가 `[a, b, c]` 로 세 개뿐이다.

비용 — `ArrayList` 의 중간 `add` 는 뒤를 전부 민다(O(n)).\
`LinkedList` 는 그 자리가 O(1)이다 — 그 차이는 [`../../../../../data-structure/02-linked-list/`](../../../../../data-structure/02-linked-list/) 가 정본이다.

### (8) 안 던지는 컬렉션도 있다

**언제 쓰나** — 여러 스레드가 같은 컬렉션을 볼 때.

**실행 결과** (`Ex.java` — 43-b, 17·21·25 동일)

```text
--- 6) 동시 컬렉션은 안 터진다
CopyOnWriteArrayList : 예외 없음 / 결과 [e0, e2, e3, e4] / 돈 원소 [e0, e1, e2, e3, e4]
COW 의 Iterator.remove : java.lang.UnsupportedOperationException
ConcurrentHashMap    : 예외 없음 / 결과 {k0=0, k2=2, k3=3, k4=4} / 돈 키 5개
```

```text
   ArrayList                          CopyOnWriteArrayList

   순회 중 수정 -> CME (대개)          순회 중 수정 -> 예외 없음
        |                                    |
   같은 배열을 본다                     이터레이터는 만들 때의 스냅샷을 본다
                                       -> 지운 e1 도 루프에 들어온다 (5개 다 돌았다)
                                       -> 대신 Iterator.remove 가 UOE
```

그림 해설 (한 단계씩):

- **`CopyOnWriteArrayList` 는 스냅샷을 돈다.** 지운 `e1` 도 본문에 들어왔다 — **돈 원소가 5개**다.
- 대신 **`Iterator.remove` 를 지원하지 않는다.** 스냅샷을 고쳐 봐야 소용없기 때문이다.
- `ConcurrentHashMap` 은 **약한 일관성(weakly consistent)** 이다 — 안 던지되 언제의 상태를 보는지는 약속이 약하다.
- 이 컬렉션들의 계약은 [**55번 주제**](../55-atomics-and-concurrent-collections/)가 정본이다.

비용 — `CopyOnWriteArrayList` 는 **쓸 때마다 배열 전체를 복사**한다. 읽기가 압도적으로 많을 때만 쓴다.

## 문법 — 형태와 규칙

직접 쓴 최소 예제다. 출력은 전부 실행 결과다.

### 세 인터페이스

| | `Iterator<E>` | `ListIterator<E>` |
|---|---|---|
| 어디에 | 모든 `Collection` | **`List` 에만** |
| 앞으로 | `hasNext()` · `next()` | 같다 |
| 뒤로 | — | **`hasPrevious()` · `previous()`** |
| 위치 | — | **`nextIndex()` · `previousIndex()`** |
| 지우기 | `remove()` (선택) | 같다 |
| 바꾸기 | — | **`set(e)`** (선택) |
| 끼워 넣기 | — | **`add(e)`** (선택) |
| 만드는 법 | `c.iterator()` | `list.listIterator()` · `list.listIterator(i)` |

- `ListIterator` 는 **`List` 에만** 있다. `Set` 에는 `listIterator()` 가 없다.
- 얻는 법이 셋이다 — `iterator()`·`listIterator()`·`listIterator(시작위치)`.

### 예외 세 가지의 뜻

| 예외 | 언제 | 뜻 |
|---|---|---|
| `NoSuchElementException` | `hasNext()` 가 `false` 인데 `next()` | 끝을 안 봤다 |
| `IllegalStateException` | `next()` 없이 `remove()`/`set()`, 또는 두 번 `remove()` | 호출 순서를 어겼다 |
| `UnsupportedOperationException` | 불변 컬렉션의 `remove()`/`set()`/`add()` | 그 컬렉션이 못 한다 |
| `ConcurrentModificationException` | 순회 중 컬렉션이 구조적으로 바뀜 | **버그를 알려 주는 신호**(보장 아님) |

### 역순 순회 — 세 가지

```java
// 1) 21+ — 가장 짧다 (42번)
for (String s : list.reversed()) { }

// 2) ListIterator — 1.2 부터 어디서나
for (var it = list.listIterator(list.size()); it.hasPrevious(); ) { it.previous(); }

// 3) Deque 전용 — 6+
for (var it = deque.descendingIterator(); it.hasNext(); ) { it.next(); }
```

**실행 결과** (`Ex.java` — 43-c, 21·25 동일)

```text
--- 6) 뒤에서부터 순회
listIterator(size()) 로 역순 : cba
21 부터는 이렇게도 된다       : [c, b, a]
```

- **`listIterator(list.size())` 로 시작**하는 것이 핵심이다. `listIterator()` 는 앞에서 시작한다.

### 불변 컬렉션의 `ListIterator`

**실행 결과** (`Ex.java` — 43-c, 21·25 동일)

```text
--- 7) ListIterator 는 List 에만 있다
Set 에는 listIterator 가 없다 — Set<String>.listIterator() 는 컴파일이 안 된다
List.of(..).listIterator().add : 
  java.lang.UnsupportedOperationException
  set : java.lang.UnsupportedOperationException
```

- `add`·`set` 둘 다 막힌다. **옵셔널 연산**이다.

## 어디서 틀리나

### 1. ★ "예외가 안 났으니 맞게 돌았다"

```java
for (String s : list) if (cond(s)) list.remove(s);
```

- **끝에서 두 번째를 지우면 예외가 안 난다.** 대신 **마지막 원소가 처리에서 빠진다**((3)).
- 테스트 데이터에서 우연히 안 터지면 **버그가 그대로 배포된다.**
- 방어: 순회 중 원본을 고치지 않는다. `removeIf` 를 쓴다.

### 2. `for` 를 `stream().forEach` 로 바꾼다

```java
list.stream().forEach(s -> { if (cond(s)) list.remove(s); });
```

- **`NullPointerException`** 이 난다((4)). `ConcurrentModificationException` 이 아니다.
- 메시지가 `because "<parameter2>" is null` 이라 원인이 전혀 안 보인다.
- 방어: 같다. 순회 중에 고치지 않는다.

### 3. `Iterator.remove()` 를 `next()` 없이 부른다

```java
Iterator<String> it = l.iterator();
it.remove();                 // IllegalStateException
```

- 그리고 **연달아 두 번**도 안 된다. "`next()` 한 번당 `remove()` 한 번" 이다.

### 4. `hasNext()` 없이 `next()` 를 부른다

```java
String first = c.iterator().next();      // 비었으면 NoSuchElementException
```

- 21부터는 `c.getFirst()` 가 같은 예외를 던진다([`../42-sequenced-collections/`](../42-sequenced-collections/)).
- 빈 컬렉션이 가능하면 `isEmpty()` 를 먼저 본다.

### 5. `remove(Object)` 로 지우면서 "이 원소만" 지워질 거라고 믿는다

```java
for (String s : new ArrayList<>(l)) if (cond(s)) l.remove(s);
```

- `List.remove(Object)` 는 **첫 번째로 일치하는 것**을 지운다. 중복이 있으면 의도와 다를 수 있다.
- 그리고 매번 선형 탐색이라 O(n²)이다.
- 방어: `removeIf` 가 짧고 빠르고 정확하다.

### 6. `removeIf` 의 람다 안에서 컬렉션을 고친다

```java
l.removeIf(s -> { if (s.equals("e2")) l.add("x"); return false; });   // CME
```

- **읽기는 허용하지만 쓰기는 CME** 다. 소스 주석이 그렇게 적혀 있다((5)).

### 7. `ListIterator.add` 뒤에 `set` 을 부른다

```java
it.add("x");
it.set("y");                 // IllegalStateException
```

- `add` 가 `lastRet = -1` 로 되돌리기 때문이다((7)의 소스).
- 방금 넣은 것을 바꾸려면 **넣을 값을 먼저 정한다.**

### 8. `CopyOnWriteArrayList` 에서 `Iterator.remove` 를 쓴다

```java
for (var it = cow.iterator(); it.hasNext(); ) { it.next(); it.remove(); }   // UOE
```

- **스냅샷 이터레이터라 지울 대상이 없다.** `cow.removeIf(...)` 를 쓴다.

### 9. `ConcurrentModificationException` 을 `catch` 해서 다시 돈다

```java
try { for (...) { ... } } catch (ConcurrentModificationException e) { retry(); }
```

- javadoc 이 명시적으로 금지한다 — *"it would be wrong to write a program that depended on this exception for its correctness"*.
- **안 날 수도 있기 때문**이다((3)). 재시도 로직이 있어도 안 터진 경우는 못 잡는다.

### 10. `set(i, x)` 이 순회를 깬다고 생각한다

```java
for (String s : l) { }              // 이 안에서 l.set(0, "z") 는 CME 가 아니다
```

- **`set` 은 구조적 수정이 아니다.** `modCount` 가 안 오른다((2)의 javadoc).
- 다만 `ArrayList.replaceAll` 은 **`modCount` 를 올린다**(소스에 `modCount++` 가 있다) — 이름만 비슷하고 다르다.

## 구현 세부사항 대 언어 보장

| 관측한 것 | 보장인가 | 근거 |
|---|---|---|
| `hasNext()=false` 인데 `next()` → `NoSuchElementException` | **보장** | `Iterator.next` javadoc `@throws` |
| `next()` 없이 `remove()` → `IllegalStateException` | **보장** | `Iterator.remove` javadoc `@throws` |
| 불변 컬렉션의 `remove()` → `UnsupportedOperationException` | **보장** | 옵셔널 연산 |
| 그 메시지가 `remove` | **보장 아님** | `Iterator.remove` 기본 구현의 문자열이다 |
| 순회 중 수정 → `ConcurrentModificationException` | **보장 아님 — best-effort** | CME javadoc — "cannot be guaranteed ... on a best-effort basis" |
| **끝에서 두 번째를 지우면 안 터지는 것** | **보장 아님** | `Iterator` javadoc — 그 동작은 "unspecified" |
| 그때 마지막 원소를 건너뛰는 것 | **보장 아님** | 같은 문장. `hasNext()` 구현에 달려 있다 |
| `stream().forEach` 에서 NPE | **보장 아님** | 스플리터레이터 구현이 만든 결과다 |
| `Iterator.remove()` 가 CME 를 안 냄 | **보장** | javadoc — "with well-defined semantics" |
| `removeIf` 가 CME 를 안 냄 | **보장** | `Collection.removeIf` 가 이터레이터로 지우도록 명세됨 |
| `removeIf` 가 `modCount` 를 **한 번만** 올림 | **보장 아님** | `ArrayList` 구현의 최적화다 |
| `ListIterator.add` 가 CME 를 안 냄 | **보장** | `ListIterator.add` javadoc |
| `CopyOnWriteArrayList` 가 안 던짐 | **보장** | 그 클래스 javadoc — 스냅샷 이터레이터 |
| `modCount` 필드의 존재 | **보장 아님** | `AbstractList` javadoc — "Use of this field by subclasses is **optional**" |

**세 JDK 실측** — 프로그램 2개를 17.0.13 · 21.0.5 · 25.0.1 에서 돌려 `diff` 했다.

```text
43-a (계약·CME 위치 격자·forEach·stream) : 세 버전 출력이 한 글자도 같다
43-b (안전한 삭제 셋·맵·동시 컬렉션)      : 세 버전 출력이 한 글자도 같다
43-c (ListIterator)                       : 21 · 25 동일 (List.reversed() 를 써서 17 에서는 컴파일 불가)
```

- ★ **"e3 를 지우면 안 터진다"가 세 버전에서 똑같았다.** 그래도 **보장이 아니다.**\
  javadoc 이 "unspecified" 라고 적었으므로 **터져도 맞고 안 터져도 맞다.**\
  세 버전이 같다는 것은 "지금 그렇다"이지 "앞으로도 그렇다"가 아니다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 일 | 고를 것 |
|---|---|
| 그냥 순회 | **향상된 `for`** ([`../20-control-flow-statements/`](../20-control-flow-statements/)) |
| 조건으로 지우기 | **`removeIf`** — 기본 선택 |
| 지우면서 다른 일도 | `Iterator.remove()` |
| 맵에서 지우기 | **`entrySet().removeIf`** / `values().removeIf` / `keySet().removeIf` |
| 순회하며 값 바꾸기 (리스트) | **`replaceAll`** 또는 `ListIterator.set` |
| 순회하며 값 바꾸기 (맵) | `replaceAll` 또는 `Entry.setValue`([`../41-map-api-merge-compute/`](../41-map-api-merge-compute/)) |
| 순회하며 끼워 넣기 | **`ListIterator.add`** |
| 역순 순회 | 21+ 는 `reversed()`, 그 전은 `listIterator(size())` |
| 원본을 못 고칠 때 | 복사본 순회 — `new ArrayList<>(l)` |
| 여러 스레드가 본다 | `CopyOnWriteArrayList`·`ConcurrentHashMap`([**55번 주제**](../55-atomics-and-concurrent-collections/)) |
| 스트림으로 걸러 새 리스트 | `l.stream().filter(...).toList()`([`../46-terminal-operations/`](../46-terminal-operations/)) |
| `ConcurrentModificationException` 을 제어 흐름으로 | **하지 않는다** — javadoc 이 금지한다 |

판단 규칙 세 줄.

- **순회 중에 컬렉션을 고치지 않는다.** 고쳐야 하면 이터레이터를 통해서만.
- **`removeIf` 를 기본으로.** 짧고, 한 번에 밀어내고, 안전하다.
- **예외가 안 났다고 맞게 돈 것이 아니다.** `ConcurrentModificationException` 은 버그 탐지기이지 안전장치가 아니다.

## 핵심 문장

- `Iterator` 의 계약은 **`next()` 전에 `hasNext()`**, **`remove()` 는 `next()` 한 번당 한 번**이다. 어기면 각각 `NoSuchElementException` 과 `IllegalStateException` 이다.
- fail-fast 는 **컬렉션의 `modCount` 와 이터레이터의 `expectedModCount` 를 `next()` 마다 대조**하는 것이다. `modCount` 는 **크기를 바꾸는 수정만** 센다.
- ★ **그 대조는 `hasNext()` 에서는 일어나지 않는다.** 그래서 **끝에서 두 번째를 지우면 예외 없이 마지막 원소를 건너뛴다** — javadoc 이 `best-effort` 라고 미리 인정해 놓았다.
- 같은 코드를 `list.forEach` 로 쓰면 `ConcurrentModificationException`, `stream().forEach` 로 쓰면 **메시지가 다른 `NullPointerException`** 이 난다. 셋이 전부 다르다.
- 안전하게 지우는 법은 셋이다 — **`Iterator.remove()`**(내부에서 `expectedModCount` 를 다시 베낀다) · **`removeIf`**(두 번 훑고 한 번에 밀어낸다) · **복사본 순회**.

## 관련 자료

- [`../20-control-flow-statements/`](../20-control-flow-statements/) — **향상된 `for` 라는 문법의 정본.**\
  그쪽은 **`for` 가 무엇 위에서 돌고 배열과 어떻게 다른가**까지(설명에 필요한 만큼 `hasNext`/`next`/`remove` 셋을 다룬다),\
  여기는 **`Iterator` 인터페이스 자체의 계약·`ListIterator`·삭제 셋·fail-fast 의 구현과 한계**부터
- [`../39-collections-framework-map/`](../39-collections-framework-map/) — **이 주제의 선행.** `Collection` 이 `Iterable` 이고 `Map` 은 아니라는 것
- [`../40-list-set-and-immutable-factories/`](../40-list-set-and-immutable-factories/) — `removeIf` 가 불변 컬렉션에서 갈리는 것. `subList` 뷰가 죽는 것도 같은 `modCount` 다
- [`../41-map-api-merge-compute/`](../41-map-api-merge-compute/) — 맵의 뷰에서 지우기, `compute*` 안에서 맵을 고쳤을 때의 CME. **그쪽도 같은 best-effort 다**
- [`../42-sequenced-collections/`](../42-sequenced-collections/) — `reversed()` 로 역순 순회하기. `removeFirst()` 의 기본 구현이 `Iterator.remove()` 를 쓴다
- [`../46-terminal-operations/`](../46-terminal-operations/) — 스트림이 순회를 대신하는 길. **고치지 말고 새로 만드는** 접근
- [`../26-try-with-resources/`](../26-try-with-resources/) — 이터레이터는 `AutoCloseable` 이 아니다. 닫을 것이 없다
- [`../../../../../data-structure/01-dynamic-array/`](../../../../../data-structure/01-dynamic-array/) — `ArrayList` 에서 중간 삭제가 뒤를 미는 이유. **비용의 정본은 그쪽**
- [`../../../../../data-structure/02-linked-list/`](../../../../../data-structure/02-linked-list/) — `LinkedList` 에서 `ListIterator.remove` 가 싼 이유
- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 43번)
- [`../55-atomics-and-concurrent-collections/`](../55-atomics-and-concurrent-collections/)(원자 변수와 동시 컬렉션) — CME 를 안 던지는 컬렉션들의 계약. **여기는 "안 던지는 구현이 있다"까지**

## 용어 풀이

- **`Iterator`** — `hasNext()`·`next()`·(선택) `remove()` 로 순회를 진행시키는 객체. Java 1.2.
- **`ListIterator`** — `List` 전용 양방향 이터레이터. `previous`·`set`·`add`·`nextIndex` 를 더 가진다.
- **`Iterable`** — `iterator()` 하나를 요구하는 인터페이스. 향상된 `for` 의 대상.
- **커서(cursor)** — 이터레이터가 가리키는 자리. 원소가 아니라 **원소 사이**에 있다.
- **`modCount`** — 컬렉션이 **구조적으로** 몇 번 바뀌었나를 세는 필드. `AbstractList` 에 `protected` 로 있다.
- **`expectedModCount`** — 이터레이터가 만들 때 베껴 둔 `modCount`. 둘이 다르면 던진다.
- **구조적 수정(structural modification)** — 크기를 바꾸는 변경. `set` 은 해당 없음, `add`·`remove` 는 해당.
- **fail-fast** — 잘못된 상태를 발견 즉시 멈추는 설계. **보장이 아니라 best-effort 다.**
- **best-effort** — 되는 만큼만 해 본다. 감지 못 하는 경우가 있다는 뜻.
- **`ConcurrentModificationException`** — `modCount` 불일치를 감지했을 때의 예외. Java 1.2.
- **`NoSuchElementException`** — 더 꺼낼 것이 없는데 꺼내려 할 때.
- **`IllegalStateException`** — 그 호출을 받을 상태가 아닐 때. `remove()` 순서 위반이 이것이다.
- **스냅샷 이터레이터(snapshot iterator)** — 만들 때의 배열을 들고 도는 이터레이터. `CopyOnWriteArrayList` 가 그렇다.
- **약한 일관성(weakly consistent)** — 던지지는 않지만 언제의 상태를 보는지 약속이 약한 것. `ConcurrentHashMap` 의 순회.
- **`deathRow`** — `ArrayList.removeIf` 가 지울 자리를 표시하는 비트 집합. 구현의 이름이다.

## 더 들어가면

- **`hasNext()` 가 `checkForComodification()` 을 안 부르는 것은 성능 때문만은 아니다.**\
  `hasNext()` 는 `boolean` 을 돌려주는 질의라 **예외를 던지는 것이 어울리지 않는다.**\
  그 설계 선택이 (3)의 구멍을 만들었다. **계약과 구현이 맞물린 자리**다.
- **`Itr.next()` 에는 CME 를 던지는 자리가 둘이다.**

  ```java
  // JDK 21.0.5  java.base/java/util/ArrayList.java  1048~1057행 — 실제 소스 그대로
          public E next() {
              checkForComodification();
              int i = cursor;
              if (i >= size)
                  throw new NoSuchElementException();
              Object[] elementData = ArrayList.this.elementData;
              if (i >= elementData.length)
                  throw new ConcurrentModificationException();
  ```

  둘째(`i >= elementData.length`)는 **다른 스레드가 배열을 줄였을 때**를 위한 방어다.\
  한 스레드만 도는 코드에서는 첫째만 발동한다.
- **`ArrayList.forEach` 와 `Itr.forEachRemaining` 은 둘 다 루프 조건에 `modCount` 를 넣는다.**\
  `for (; i < size && modCount == expectedModCount; i++)` — **매 원소마다 대조**하고 끝에서 한 번 더 본다.\
  향상된 `for` 는 `hasNext()` 가 대조를 안 하는 반면((3)), 이쪽은 **루프 조건 자체가 대조**라
  (4)에서 `e3` 제거가 `list.forEach` 에서는 잡혔다.
- **`ArrayList.replaceAll` 은 `modCount` 를 올린다.**\
  값만 바꾸는데도 올린다. 소스에 `// TODO(8203662): remove increment of modCount from ...` 라는 주석이 달려 있다 —
  **JDK 개발자 자신도 이것을 이상하게 여긴다**는 표시다.
- **`Iterator.forEachRemaining` 뒤의 `remove()` 는 정의되지 않는다.**\
  javadoc — "The behavior of an iterator is unspecified if this method is called after a call to the `forEachRemaining` method."
- **`Enumeration` 은 `Iterator` 의 전신이다.**\
  `Vector`·`Hashtable` 시절의 인터페이스로, `remove` 가 없고 이름이 길다(`hasMoreElements`·`nextElement`).\
  `Enumeration.asIterator()`(9+)로 변환할 수 있다. 새 코드에서는 쓰지 않는다.
- **`Spliterator`(8+)는 이터레이터의 병렬 버전이다.**\
  `trySplit()` 으로 반씩 쪼개며, `IMMUTABLE`·`CONCURRENT` 같은 특성 비트로 **fail-fast 여부를 선언**한다.\
  스트림이 이것 위에서 돈다 — [`../49-parallel-streams/`](../49-parallel-streams/)가 그 이야기다.
