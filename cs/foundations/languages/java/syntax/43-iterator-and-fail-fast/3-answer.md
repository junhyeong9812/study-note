# java/syntax/43 — `Iterator`·`ListIterator`·fail-fast 와 `ConcurrentModificationException` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러는 **Temurin JDK 에서 실제로 돌려 얻은 것**이다.\
> javadoc·소스 인용은 JDK 21.0.5 의 `lib/src.zip` 을 풀어 읽은 원문이다.\
> 43-a·43-b 는 **17.0.13 · 21.0.5 · 25.0.1** 셋 다에서 돌렸고 출력이 같았다(11번).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `Iterator` 의 세 메서드 계약

**출력** (`Ex.java` — 43-a, 17·21·25 동일)

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

**(A)~(E)**

| | 결과 |
|---|---|
| (A) 끝난 뒤 `next()` | **`NoSuchElementException`** |
| (B) `next()` 없이 `remove()` | **`IllegalStateException`** |
| (C) 연달아 `remove()` | **`IllegalStateException`** |
| (D) `List.of` 의 `remove()` | **`UnsupportedOperationException`** (메시지 없음) |
| (E) `Arrays.asList` 의 `remove()` | **`UnsupportedOperationException: remove`** |

**각 예외가 가리키는 실수**

```text
  NoSuchElementException          끝을 안 봤다        -> hasNext() 를 먼저 보라
  IllegalStateException           순서를 어겼다       -> next() 뒤에, 한 번만
  UnsupportedOperationException   그 컬렉션이 못 한다 -> 가변 컬렉션으로 복사하라
```

**(D)와 (E)의 메시지가 다른 이유**

```text
   List.of 의 이터레이터                  Arrays.asList 의 이터레이터

   ImmutableCollections 가                remove() 를 재정의하지 않는다
   remove() 를 재정의해 uoe() 를 던진다    -> Iterator 의 기본 구현이 돈다
        |                                         |
   메시지 없음                             throw new UnsupportedOperationException("remove")
```

```java
// JDK 21.0.5  java.base/java/util/Iterator.java  — 실제 소스 그대로
    default void remove() {
        throw new UnsupportedOperationException("remove");
    }
```

**`next()` 한 번당 `remove()` 는 한 번**

> Removes from the underlying collection the last element returned by this iterator (optional operation). **This method can be called only once per call to `next`.**

### 2. ★ 어느 원소를 지울 때 터지나

**출력** (`Ex.java` — 43-a, 17·21·25 동일)

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

**예외가 안 나는 `k`**

- **`k = 3`**, 즉 **끝에서 두 번째**다.
- 그때 루프 본문에 들어온 원소는 **네 개**(`[e0, e1, e2, e3]`)다. **`e4` 는 한 번도 안 들어왔다.**

**그 이유 — `hasNext()` 한 줄**

```java
// JDK 21.0.5  java.base/java/util/ArrayList.java  1043~1045행 — 실제 소스 그대로
        public boolean hasNext() {
            return cursor != size;
        }
```

```text
   e3 를 돌려준 직후                     e3 를 지운 뒤

   cursor = 4                           cursor = 4  (그대로)
   size   = 5                           size   = 4  (하나 줄었다)
        |                                    |
   hasNext() = (4 != 5) = true          hasNext() = (4 != 4) = false
                                             |
                                    루프가 그냥 끝난다
                                    checkForComodification() 이 안 불린다
```

- ★ **`hasNext()` 는 `modCount` 를 보지 않는다.** 그래서 대조 자체가 일어나지 않는다.
- `next()` 만 `checkForComodification()` 을 부르는데, `next()` 가 한 번도 더 안 불렸다.

**크기 2 리스트에서 첫 원소를 지우면**

- 같은 일이 벌어진다 — `cursor=1`, `size` 가 `2`→`1` 이 되어 `hasNext()` 가 `false`.
- **예외 없음, 결과 `[b]`, 그런데 `"b"` 는 루프에 안 들어왔다.**
- 크기 2 에서는 "끝에서 두 번째 = 첫 번째" 다.

**javadoc 의 표현**

> Note that fail-fast behavior **cannot be guaranteed** ... Fail-fast operations throw `ConcurrentModificationException` **on a best-effort basis**. Therefore, it would be wrong to write a program that depended on this exception for its correctness: *`ConcurrentModificationException` should be used only to detect bugs.*

> The behavior of an iterator is **unspecified** if the underlying collection is modified while the iteration is in progress in any way other than by calling this method. (`Iterator.remove` javadoc)

- 표현은 **`best-effort basis`** 와 **`unspecified`** 다.

### 3. 같은 일을 세 가지 형태로 쓰면

**출력** (`Ex.java` — 43-a, 17·21·25 동일)

```text
--- 7) forEach 와 스트림은 어떤가
forEach e3 제거 : java.util.ConcurrentModificationException
stream e3 제거  : java.lang.NullPointerException: Cannot invoke "String.equals(Object)" because "<parameter2>" is null
forEach e0 제거 : java.util.ConcurrentModificationException
```

**셋**

| | 결과 |
|---|---|
| (A) 향상된 `for` | **예외 없음**, `e4` 를 건너뛴다(2번) |
| (B) `list.forEach` | **`ConcurrentModificationException`** |
| (C) `stream().forEach` | **`NullPointerException`** |

**(C)의 메시지 전문**

```text
java.lang.NullPointerException: Cannot invoke "String.equals(Object)" because "<parameter2>" is null
```

- 람다가 **`null` 을 원소로 받았다.** 배열이 줄면서 뒤쪽 칸이 `null` 이 됐고 스플리터레이터가 그것을 꺼냈다.

**(B)가 (A)와 다른 이유**

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

```text
   향상된 for                         list.forEach

   hasNext() 가 cursor != size        루프 조건에 modCount 대조가 들어 있다
   -> modCount 를 안 본다              -> 매 원소마다 본다
        |                                   |
   줄어든 size 때문에 조용히 끝난다     조건이 깨져 루프를 나오고
                                      끝에서 한 번 더 보고 던진다
```

- **`size` 를 루프 전에 베껴 두고 `modCount` 를 루프 조건에 넣은 것**이 차이다.

**가장 나쁜 실패**

- ★ **(A)** 다. **예외가 없는데 결과가 틀리기** 때문이다.
- (C)의 `NullPointerException` 도 나쁘다 — 원인이 전혀 안 보인다. 하지만 **멈추기는 한다.**
- (B)가 가장 낫다. 시끄럽고 이름이 정확하다.

### 4. fail-fast 는 어떻게 구현돼 있나

**`modCount`**

- **`java.util.AbstractList` 의 `protected transient int modCount`** 다.
- `ArrayList`·`LinkedList`·`AbstractMap` 계열이 각자 들고 있다(`HashMap` 은 자기 필드로 따로 둔다).

**`expectedModCount`**

- **이터레이터의 필드**다. `ArrayList$Itr` 의 `int expectedModCount = modCount;`.
- 이터레이터를 **만드는 순간** 베껴 둔다.

**무엇을 셀 때만 오르나**

> The number of times this list has been *structurally modified*. Structural modifications are those that change the size of the list, or otherwise perturb it in such a fashion that iterations in progress may yield incorrect results.

- **크기를 바꾸는 변경**만 센다.
- **`set(i, x)` 는 안 오른다.** 순회 중 `set` 은 CME 를 안 낸다.
- 다만 `ArrayList.replaceAll` 은 **오른다**(소스에 `modCount++` 가 있고 그 옆에 `// TODO(8203662)` 주석이 달려 있다).

**`checkForComodification()` 을 부르는 메서드**

```text
   부른다                           안 부른다
   next()                           hasNext()          <- 여기가 구멍이다 (2번)
   remove()                         hasPrevious()
   previous()  (ListItr)
   set()       (ListItr)
   add()       (ListItr)
   forEachRemaining() (끝에서)
```

**`modCount` 는 의무인가**

> **Use of this field by subclasses is optional.** If a subclass wishes to provide fail-fast iterators (and list iterators), then it merely has to increment this field in its `add(int, E)` and `remove(int)` methods ... If an implementation does not wish to provide fail-fast iterators, this field may be ignored.

- ★ **선택이다.** 직접 만든 `List` 구현체는 fail-fast 가 아예 없을 수 있다.
- 그래서 "`ConcurrentModificationException` 이 나겠지"를 전제로 코드를 쓸 수 없다.

### 5. 안전하게 지우는 법 셋

**출력** (`Ex.java` — 43-b, 17·21·25 동일)

```text
--- 1) 안전하게 지우는 법 셋
(1) Iterator.remove : [e0, e2, e3, e4]
(2) removeIf        : [e0, e2, e3, e4]
(3) 복사본 순회      : [e0, e2, e3, e4]
--- 2) 전부 지울 때도 셋 다 된다
Iterator.remove 로 전부 : []
removeIf 로 전부        : []
--- 3) 셋의 차이
removeIf 가 본 원소 수 : 5 (크기 5)
```

- **셋의 결과가 같다.**

**(1)이 CME 를 안 내는 한 줄**

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

- **`expectedModCount = modCount;`** — 지운 뒤 다시 베낀다. 그래서 다음 `next()` 의 대조가 통과한다.

**`cursor = lastRet` 이 막는 것**

```text
   이 줄이 없다면

   [e0][e1][e2]   cursor=2 (e1 을 돌려줬다)
   e1 을 지운다 -> [e0][e2]   cursor=2
   next() -> 인덱스 2 -> 범위 밖 / 또는 e2 를 건너뛴다
        |
   cursor = lastRet (=1) 로 되돌리면
   next() -> 인덱스 1 -> e2   <- 건너뛰지 않는다
```

- **건너뛰기**를 막는다. 2번의 사고와 같은 종류를 이터레이터가 스스로 방지하는 것이다.

**(2)는 몇 번 훑나**

- **두 번**이다. 소스 주석이 이름까지 적어 놓았다.

```java
// JDK 21.0.5  java.base/java/util/ArrayList.java  1750~1776행 — 실제 소스 그대로(발췌)
        // Tolerate predicates that reentrantly access the collection for
        // read (but writers still get CME), so traverse once to find
        // elements to delete, a second pass to physically expunge.
        if (i < end) {
            final int beg = i;
            final long[] deathRow = nBits(end - beg);
```

- 표시용 비트 집합의 이름이 **`deathRow`** 다.
- 첫 패스에서 지울 자리를 비트로 표시하고, **둘째 패스에서 한 번에 밀어낸다.**
- 그래서 `modCount++` 가 **한 번**이다.

**(3)의 비용**

- **복사 O(n)** 이 추가로 든다. 그리고 `l.remove(s)` 가 매번 선형 탐색이라 지울 것이 많으면 O(n²)다.
- 대신 **원본이 어떤 구현인지 몰라도 된다** — 복사본은 내가 만든 `ArrayList` 다.

**기본은 (2) `removeIf`**

- 가장 짧고, 밀어내기가 한 번이고, 계약상 안전하다.

### 6. `removeIf` 안에서 컬렉션을 고치면

**출력** (`Ex.java` — 43-b, 17·21·25 동일)

```text
--- 4) removeIf 안에서 리스트를 고치면
removeIf 안에서 add : java.util.ConcurrentModificationException
```

**주석이 읽기와 쓰기를 구분한다**

> `// Tolerate predicates that reentrantly access the collection for read (but writers still get CME), so traverse once to find elements to delete, a second pass to physically expunge.`

- **읽기는 허용(tolerate)**, **쓰기는 CME.**
- 두 패스로 나눈 이유가 바로 그 "읽기 허용"이다 — 첫 패스 동안에는 리스트를 안 건드리기 때문이다.

**`modCount` 를 몇 번 올리나**

- **한 번**이다. 둘째 패스 직전의 `modCount++` 한 줄뿐이다.
- `Iterator.remove()` 를 N 번 부르면 N 번 오른다. 그래서 `removeIf` 가 더 싸다.

### 7. 맵에서 지우기

**출력** (`Ex.java` — 43-b, 17·21·25 동일)

```text
--- 5) HashMap 에서
맵 직접 remove : java.util.ConcurrentModificationException
entrySet Iterator.remove : {k0=0, k2=2, k3=3, k4=4}
entrySet().removeIf      : {k0=0, k2=2, k3=3, k4=4}
values().removeIf        : {k0=0, k2=2, k3=3, k4=4}
```

**다섯**

| | 결과 |
|---|---|
| (A) `keySet()` 순회 중 `m.remove(k)` | **`ConcurrentModificationException`** |
| (B) `keySet().removeIf` | 통과 |
| (C) `entrySet().removeIf` | 통과 |
| (D) `values().removeIf` | 통과 |
| (E) `entrySet()` 의 `Iterator.remove` | 통과 |

**(A)만 다른 이유**

```text
   (A) 맵을 직접 고친다                (B)~(E) 뷰/이터레이터로 고친다

   m.remove(k) -> modCount++           뷰의 이터레이터가 지우면서
   순회 중인 이터레이터는 모른다          expectedModCount 도 같이 갱신한다
        |                                    |
   다음 next() 에서 대조 실패            대조가 통과한다
```

- 뷰가 무엇인지는 [`../41-map-api-merge-compute/`](../41-map-api-merge-compute/) 가 정본이다.

**키·값을 다 보면서 지우려면**

- **`entrySet().removeIf(e -> ...)`** 다. `e.getKey()` 와 `e.getValue()` 를 다 볼 수 있다.

### 8. `ListIterator` 의 커서

**출력** (`Ex.java` — 43-c, 21·25 동일)

```text
--- 1) 커서는 원소가 아니라 원소 사이에 있다
동작                     nextIndex    previousIndex hasNext    hasPrevious
시작                     0            -1           true       false
next()=a               1            0            true       true
next()=b               2            1            true       true
previous()=b           1            0            true       true
```

**열여섯 칸**

| 시점 | `nextIndex()` | `previousIndex()` | `hasNext()` | `hasPrevious()` |
|---|---|---|---|---|
| 시작 | `0` | **`-1`** | `true` | `false` |
| `next()`=a 뒤 | `1` | `0` | `true` | `true` |
| `next()`=b 뒤 | `2` | `1` | `true` | `true` |
| `previous()`=b 뒤 | `1` | `0` | `true` | `true` |

**`next()` 로 `b` 를 받고 바로 `previous()`**

- **다시 `b`** 가 나온다.

```text
        [a]     [b]     [c]
       ^   ^   ^   ^   ^   ^
       0   |   1   |   2   3

   next() 로 b 를 받으면 커서가 1 -> 2 로 간다 (b 를 넘어갔다)
   previous() 를 부르면 커서가 2 -> 1 로 되돌아가며 넘어온 b 를 돌려준다
```

**시작 시점의 `previousIndex()`**

- **`-1`** 이다. 앞에 아무것도 없다는 표시다.

**커서는 어디를 가리키나**

- **원소 사이**를 가리킨다. 크기 `n` 리스트에서 커서 자리가 **`n+1` 개**다.
- 이것이 `set` 이 "마지막으로 돌려준 원소"를 대상으로 삼는 이유다 — 커서만으로는 대상이 안 정해진다.

### 9. `ListIterator` 의 `set` 과 `add`

**출력** (`Ex.java` — 43-c, 21·25 동일)

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

**(A)~(D)**

- **(A)** `[A, b, c]` — `next()` 가 돌려준 `a` 가 대상이다.
- **(B)** `[A, B, c]` — `next()` 로 `b` 를 받고 `previous()` 로 다시 `b` 를 받았으니 **`b` 가 대상**이다.
- **(C)** **예외 없음.** 결과는 `[a, b, b2, c]`.
- **(D)** **`IllegalStateException`**.

**(B)의 대상**

- **`previous()` 가 돌려준 원소**다. `set` 은 "마지막으로 돌려준 것"을 본다 — 방향과 무관하다.

**(C)가 CME 를 안 내는 이유**

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

- **`expectedModCount = modCount;`** — `Iterator.remove()` 와 같은 장치다.

**방금 넣은 것을 다시 만나나**

- **아니다.** 돈 원소가 `[a, b, c]` 세 개다. `"b2"` 는 안 들어왔다.
- `cursor = i + 1` 로 **커서를 새 원소 뒤**에 두기 때문이다. 이것이 없으면 무한 루프가 된다.

**(D)의 한 줄**

- **`lastRet = -1;`** 이다. "마지막으로 돌려준 원소"가 없어지므로 `set`·`remove` 가 `IllegalStateException` 을 던진다.

### 10. 안 던지는 컬렉션

**출력** (`Ex.java` — 43-b, 17·21·25 동일)

```text
--- 6) 동시 컬렉션은 안 터진다
CopyOnWriteArrayList : 예외 없음 / 결과 [e0, e2, e3, e4] / 돈 원소 [e0, e1, e2, e3, e4]
COW 의 Iterator.remove : java.lang.UnsupportedOperationException
ConcurrentHashMap    : 예외 없음 / 결과 {k0=0, k2=2, k3=3, k4=4} / 돈 키 5개
```

**(A)~(C)**

- **(A)** 예외 없음. 결과 `[e0, e2, e3, e4]`. **돈 원소는 다섯 개** — 지운 `e1` 까지 들어왔다.
- **(B)** **`UnsupportedOperationException`**.
- **(C)** 예외 없음. 결과 `{k0=0, k2=2, k3=3, k4=4}`. 돈 키도 다섯 개.

**(A)에서 다섯 개인 이유**

```text
   CopyOnWriteArrayList

   iterator() 를 만들 때 그 시점의 배열을 붙잡는다  (스냅샷)
        |
   cow.remove("e1") 은 새 배열을 만들어 필드를 갈아 끼운다
        |
   이터레이터는 옛 배열을 계속 본다 -> e1 도 돈다
        |
   예외가 날 이유가 없다 — 보고 있는 배열은 안 바뀌었다
```

**(B)의 이유**

- **스냅샷을 고쳐 봐야 원본에 반영되지 않는다.** 그래서 아예 막아 놓았다.
- `cow.removeIf(...)` 를 쓴다.

**안 던지는 것은 보장인가**

- **보장이다.** `CopyOnWriteArrayList` javadoc 이 스냅샷 이터레이터를 명시한다.
- `ConcurrentHashMap` 의 순회는 **약한 일관성(weakly consistent)** 으로 명세돼 있다 — 던지지 않는 것은 보장이고,
  **언제의 상태를 보는지는 약속이 약하다.**
- 계약의 자세한 내용은 [**55번 주제**](../55-atomics-and-concurrent-collections/)가 정본이다.

### 11. 무엇이 보장인가

| 관측 | 보장? | 근거 |
|---|---|---|
| 끝에서 `next()` → `NoSuchElementException` | **그렇다** | `Iterator.next` javadoc `@throws` |
| 순회 중 수정 → `ConcurrentModificationException` | **아니다** | CME javadoc — "cannot be guaranteed ... on a best-effort basis" |
| 끝에서 두 번째를 지우면 안 터짐 | **아니다** | `Iterator` javadoc — 그 동작은 "unspecified" |
| `removeIf` 가 `modCount` 를 한 번만 올림 | **아니다** | `ArrayList` 구현의 최적화다 |

**`catch` 해서 재시도하는 코드가 틀린 이유**

> Therefore, **it would be wrong to write a program that depended on this exception for its correctness**: *`ConcurrentModificationException` should be used only to detect bugs.*

- **예외가 안 나는 경우가 있기 때문**이다(2번). 재시도 로직이 있어도 **안 터진 경로는 못 잡는다.**
- 그리고 `modCount` 를 안 쓰는 구현에서는 **아예 안 난다**(4번의 javadoc).
- CME 는 **버그 탐지기**이지 안전장치가 아니다.

### 12. 이 주제의 경계

| 질문 | 정본 |
|---|---|
| 향상된 `for` 가 배열과 컬렉션에서 어떻게 다르게 컴파일되나 | [`../20-control-flow-statements/`](../20-control-flow-statements/) |
| `ArrayList` 에서 중간 삭제가 왜 O(n) 인가 | [`../../../../../data-structure/01-dynamic-array/`](../../../../../data-structure/01-dynamic-array/) |
| `reversed()` 로 역순 순회하기 | [`../42-sequenced-collections/`](../42-sequenced-collections/) |
| `compute*` 안에서 맵을 고치면 | [`../41-map-api-merge-compute/`](../41-map-api-merge-compute/) |
| `CopyOnWriteArrayList` 의 동시성 계약 | [`../55-atomics-and-concurrent-collections/`](../55-atomics-and-concurrent-collections/) |

- 20번과의 경계를 한 줄로 하면 이렇다.\
  **`for` 문이라는 문법 = 20번, `Iterator` 라는 API 의 계약과 그 구현의 한계 = 여기.**
- 41번과의 경계도 한 줄이다.\
  **`compute*` 가 best-effort 로 던진다는 사실 = 41번, best-effort 가 무슨 뜻이고 어디서 새는가 = 여기.**

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Ex.java` (43-a) | `Iterator` 계약 3예외, 불변 컬렉션의 두 UOE 메시지, **크기 5 리스트에서 지우는 위치별 CME 격자 5줄 + 돈 원소 목록**, 크기 2 리스트, 추가할 때의 5줄, `forEach`·`stream().forEach` | 17 · 21 · 25 (**출력 동일**) |
| `Ex.java` (43-b) | 안전한 삭제 셋, 전부 삭제, `removeIf` 가 본 원소 수, `removeIf` 안에서 add, `HashMap` 에서 5형태, `CopyOnWriteArrayList`·`ConcurrentHashMap`, `subList` 뷰 | 17 · 21 · 25 (**출력 동일**) |
| `Ex.java` (43-c) | `ListIterator` 의 커서 4시점 × 4값, `set` 의 대상, 순회 중 `add`, `add` 직후 `set`/`remove`, 역순 순회 두 형태, 불변 리스트의 `add`/`set`, `LinkedList` | 21 · 25 (**출력 동일**) — `List.reversed()` 를 써서 17 에서는 컴파일 불가 |
| `src.zip` 열람 | `Iterator` 의 세 메서드 javadoc 과 `remove()` 기본 구현, CME 클래스 javadoc, `AbstractList` 의 `modCount` javadoc, `ArrayList` 의 `Itr`·`ListItr`·`forEach`·`removeIf`·`replaceAll` 구현, `Enumeration.asIterator` 의 `@since 9` | 21 |

**javac 8회 · java 8회.**

**버전별로 갈린 것**

```text
43-a · 43-b : 세 버전 출력이 한 글자도 같다
43-c        : 21 · 25 동일 (42번의 reversed() 를 한 줄 썼기 때문에 17 에서는 컴파일이 안 된다)
```

- ★ **"e3 를 지우면 안 터진다"가 17·21·25 에서 똑같았다.**\
  그래도 **보장이 아니다.** javadoc 이 `unspecified` 라고 적었으므로 **터져도 맞고 안 터져도 맞다.**\
  세 버전이 같다는 것은 "지금 그렇다"이지 "앞으로도 그렇다"가 아니다.\
  이 주제에서 그 구별이 가장 중요하다 — **관측을 보장으로 읽으면 정확히 이 사고가 난다.**

**구현 의존 항목** (버전이 오르면 다시 돌려야 하는 것)

- **어느 위치를 지울 때 CME 가 나는지** — `hasNext()` 구현에 달려 있고 계약이 아니다.
- **`stream().forEach` 가 `NullPointerException` 을 내는 것** — 스플리터레이터 구현의 결과다.
- 예외 **메시지 문구** — `remove` · helpful NullPointerException 의 `<parameter2>` 같은 이름.
- `removeIf` 가 `modCount` 를 한 번만 올리는 것 · `deathRow` 라는 이름.
- `ArrayList.replaceAll` 이 `modCount` 를 올리는 것 — 소스에 `// TODO(8203662)` 가 달려 있어 **바뀔 수 있다고 예고된 자리**다.
- `ConcurrentHashMap` 순회가 보는 상태 — 약한 일관성이라 원래 약속이 약하다.
- **Java 8 은 안 돌려 봄** — 이 머신에 8이 없다. 다만 `Iterator`·`ListIterator` 는 1.2 부터라 계약 자체는 같다.
