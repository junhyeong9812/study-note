# java/syntax/40 — `List`·`Set` API 와 불변 팩토리: `List.of`·`copyOf`·`unmodifiable*` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러는 **Temurin JDK 에서 실제로 돌려 얻은 것**이다.\
> javadoc·소스 인용은 JDK 21.0.5 의 `lib/src.zip` 을 풀어 읽은 원문이다.\
> 어느 프로그램을 어느 버전에서 돌렸는지는 맨 끝 「실행 검증」 표에 있다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 세 팩토리의 세 축

**출력** (`Ex.java` — 40-a, 17·21·25 동일)

```text
--- 1) null 원소를 받나
List.of("a", null)                  : NullPointerException
Arrays.asList("a", null)             : [a, null]
Collections.unmodifiableList(널 포함) : [a, null]
List.copyOf(널 포함)                  : NullPointerException
Set.of("a", null)                    : NullPointerException
new ArrayList<>(널 포함)              : [a, null]
--- 2) 고칠 수 있나
List.of.set(0,"z")                   : UnsupportedOperationException
Arrays.asList.set(0,"z")             : OK  -> [z, b, c]
Arrays.asList.add("z")               : UnsupportedOperationException
unmodifiableList.set(0,"z")          : UnsupportedOperationException
List.copyOf.set(0,"z")               : UnsupportedOperationException
--- 3) 원본을 고치면 따라 바뀌나
원본 src                 : [a, b, c]
unmodifiableList(src)    : [a, b, c]
List.copyOf(src)         : [a, b, c]
src.add("d") 후 ...
원본 src                 : [a, b, c, d]
unmodifiableList(src)    : [a, b, c, d]   <- 따라 바뀌었다 (뷰)
List.copyOf(src)         : [a, b, c]      <- 그대로다 (복사본)
```

**세 축으로 정리하면**

```text
                        null 원소   add/remove   set(i,x)   원본이 비치나
  new ArrayList<>(c)       O           O            O            X
  Arrays.asList(...)       O           X            O            O   <- 배열이 원본
  Collections
    .unmodifiableList(l)   O           X            X            O   <- l 이 원본
  List.of(...)             X           X            X            —   <- 원본이 없다
  List.copyOf(c)           X           X            X            X
```

**세 축의 이름**

1. **`null` 허용** — 9 이후 팩토리(`of`·`copyOf`)만 금지한다.
2. **변경 가능성** — `Arrays.asList` 만 반쪽(길이 고정, `set` 만 가능).
3. **원본 반영** — 뷰인가 아닌가. `unmodifiableList`·`Arrays.asList` 가 뷰다.

**javadoc 이 구별하는 말**

> An *unmodifiable collection* is a collection, all of whose mutator methods (as defined above) are specified to throw `UnsupportedOperationException`. Such a collection thus cannot be modified by calling any methods on it.

> An *unmodifiable view collection* is a collection that is unmodifiable and that is also a view onto a backing collection. Its mutator methods throw `UnsupportedOperationException`, as described above, while reading and querying methods are delegated to the backing collection.

- 그리고 셋째 문장이 쐐기를 박는다.

> An unmodifiable collection is not necessarily immutable.

- **`Collections.unmodifiableList` 는 둘째 것**이다. 이름에 "view" 가 없어서 놓치기 쉽다.

### 2. `Arrays.asList` 는 어느 방향으로 비치나

**출력** (`Ex.java` — 40-a, 17·21·25 동일)

```text
--- 4) Arrays.asList 는 배열의 뷰다
리스트를 고치면 배열도    : [a, Z, c]
배열을 고치면 리스트도    : [a, Z, Y]
```

**복사하지 않는다**

- javadoc 이 그렇게 적는다 — "Returns a fixed-size list **backed by** the specified array."
- 실측 타입은 `java.util.Arrays$ArrayList` 다. `java.util.ArrayList` **가 아니다.**

**`set` 은 되고 `add` 가 안 되는 이유 — 한 문장**

- **배열은 칸을 덮어쓸 수는 있어도 칸 수를 바꿀 수 없다.**

**기본형 배열을 넘기면**

**출력** (`Ex.java` — 40-d, 17·21·25 동일)

```text
--- 1) 기본형 배열을 Arrays.asList 에 넣으면
Arrays.asList(int[]) 크기 : 1 / 원소 0 의 타입 int[]
Arrays.asList(String[]) 크기 : 3
올바른 길 : [1, 2, 3]
```

```text
  Arrays.asList(T... a)   <- 가변 인자다

  String[] {"a","b","c"}   -> T = String  -> 배열이 펼쳐진다 -> 크기 3
  int[]    {1,2,3}         -> T = int[]   -> 펼쳐지지 않는다 -> 크기 1
                              (int 는 T 가 될 수 없다)
```

- 방어: `Arrays.stream(arr).boxed().toList()`.

### 3. `subList` 는 어디까지 살아 있나

**출력** (`Ex.java` — 40-b, 17·21·25 동일)

```text
--- 1) subList 는 뷰다
base            : [a, b, c, d, e]
base.subList(1,4): [b, c, d]
sub.set(0,"B") 후 base : [a, B, c, d, e]
base.set(2,"C") 후 sub : [B, C, d]
sub.clear() 후 base    : [a, e]   <- 구간이 통째로 지워졌다
--- 2) 원본을 구조적으로 고치면 뷰가 죽는다
base.add 후 sub.size() : ConcurrentModificationException
base.add 후 sub.get(0) : ConcurrentModificationException
base.set 후 sub        : OK [b, c, d]
```

**(A)~(D)**

- **(A)** `sub.set(0,"B")` → `base` 가 `[a, B, c, d, e]`. 뷰에 쓰면 원본에 간다.
- **(B)** `sub.clear()` → `base` 가 `[a, e]`. **구간이 통째로 빠진다.**
- **(C)** `s2.size()` → **`ConcurrentModificationException`.** 크기를 읽기만 해도 던진다.
- **(D)** `b2.set(0,"A")` 뒤 `s2` 는 **멀쩡하다** — `[b, c, d]`.

**(C)의 예외는 보장이 아니다**

> The semantics of the list returned by this method become undefined if the backing list (i.e., this list) is *structurally modified* in any way other than via the returned list. (Structural modifications are those that change the size of this list, or otherwise perturb it in such a fashion that iterations in progress may yield incorrect results.)

- javadoc 이 약속하는 것은 **"의미가 정의되지 않는다"** 까지다.
- `ConcurrentModificationException` 은 `ArrayList$SubList` 가 `modCount` 를 대조해 **친절하게 알려 준 것**이다.
- 다른 `List` 구현이라면 조용히 틀린 답을 줄 수도 있다. 이 점이 [`../43-iterator-and-fail-fast/`](../43-iterator-and-fail-fast/) 와 같은 성질이다.

**(D)가 다른 이유**

- **`set` 은 구조적 수정이 아니다.** 크기가 안 바뀌므로 `modCount` 가 안 오른다.
- 그래서 뷰가 살아 있고, 바뀐 값이 그대로 비친다.

**캐시에 넣으면**

```text
--- 3) subList 로 잘라낸 것을 오래 들고 있으면
keep 의 구체 타입 : java.util.ArrayList$SubList
끊으려면          : [a, b] / [a, b]
List.copyOf(keep) 의 타입 : java.util.ImmutableCollections$List12
```

- **원본 전체가 메모리에 붙잡힌다.** 20개를 위해 백만 개가 살아 있는다.
- 원본이 구조적으로 바뀌는 순간 **읽기만 해도 죽는다.**
- 방어: `List.copyOf(all.subList(0, 20))` 또는 `new ArrayList<>(...)`.

### 4. 같은 프로그램을 세 번 실행하면

**출력** (`Ex.java` — 40-c, JDK 21.0.5 — **같은 JVM 을 세 번 띄웠다**)

```text
--- 실행 1
Set.of  : [a, b, c, d, e]
Map.of  : {a=1, b=2, c=3, d=4, e=5}
HashSet : [a, b, c, d, e]
HashMap : {a=1, b=2, c=3, d=4, e=5}
List.of : [a, b, c, d, e]
--- 실행 2
Set.of  : [c, d, e, a, b]
Map.of  : {c=3, d=4, e=5, a=1, b=2}
HashSet : [a, b, c, d, e]
HashMap : {a=1, b=2, c=3, d=4, e=5}
List.of : [a, b, c, d, e]
--- 실행 3
Set.of  : [e, d, c, b, a]
Map.of  : {e=5, d=4, c=3, b=2, a=1}
HashSet : [a, b, c, d, e]
HashMap : {a=1, b=2, c=3, d=4, e=5}
List.of : [a, b, c, d, e]
```

- **`Set.of`·`Map.of` 만 매번 다르다.** `HashSet`·`HashMap`·`List.of` 는 매번 같았다.
- `List.of` 는 당연하다 — 리스트는 **순서가 계약**이다.

**왜 그렇게 만들었나**

- **순서에 기대는 코드를 빨리 깨뜨리려고**다. 조용히 통과하다 나중에 터지는 것보다 낫다.

**의도를 밝힌 소스**

```java
// JDK 21.0.5  java.base/java/util/ImmutableCollections.java  53~66행 — 실제 소스 그대로
    /**
     * A "salt" value used for randomizing iteration order. This is initialized once
     * and stays constant for the lifetime of the JVM. It need not be truly random, but
     * it needs to vary sufficiently from one run to the next so that iteration order
     * will vary between JVM runs.
     */
    private static final long SALT32L;

    /**
     * For set and map iteration, we will iterate in "reverse" stochastically,
     * decided at bootstrap time.
     */
    private static final boolean REVERSE;
```

- 필드 이름은 **`SALT32L`** 과 **`REVERSE`** 다. `System.nanoTime()` 으로 만든다.

**"여러 버전에서 같았다"와 어떻게 다른가**

```text
  버전을 바꿔 가며 세 번 돌린다          같은 버전에서 세 번 돌린다

  17 · 21 · 25 에서 같았다               실행 1 · 2 · 3 이 달랐다
        |                                      |
  "버전 때문은 아니다" 까지만 말한다        "이것은 계약이 아니다" 를 증명한다
  (같아도 보장이 아니다)                   (반례가 하나 나오면 끝이다)
```

- ★ **반증이 확증보다 강하다.** 여러 버전에서 같았다는 것은 아무것도 증명하지 못하지만,
  한 버전에서 한 번이라도 다르면 **순서에 기대면 안 된다**가 증명된다.

### 5. 중복을 넣으면

**출력** (`Ex.java` — 40-a, 17·21·25 동일)

```text
--- 7) 중복을 넣으면
Set.of("a","a")   : IllegalArgumentException: duplicate element: a
Map.of("a",1,"a",2) : IllegalArgumentException: duplicate key: a
List.of("a","a")  : [a, a]
new HashSet<>(중복 포함) : [a]
```

**메시지 전문**

```text
duplicate element: a
duplicate key: a
```

- 어느 원소·어느 키가 겹쳤는지 들어 있다.

**어느 쪽이 안전한가**

```text
  new HashSet<>(List.of("a","a"))        Set.of("a","a")

  add 가 false 를 돌려준다                 IllegalArgumentException
  아무도 그 false 를 안 본다                       |
        |                                          v
        v                                    멈춘다 — 어느 원소인지까지 알려 준다
  [a] — 하나가 조용히 사라졌다              = 시끄러운 실패
  = 무음 실패
```

- **`Set.of` 가 안전하다.** 상수 선언의 실수를 **클래스 로딩 시점에** 잡는다.

**런타임 데이터로 만들 때**

- **`new HashSet<>(...)` 또는 `Set.copyOf(...)`.**
- **`Set.copyOf` 는 중복을 던지지 않고 흡수한다.**

  **출력** (`Ex.java` — 40-e)

  ```text
  Set.copyOf(중복 있는 List) : [a, b]        <- 17 에서는 [b, a] 였다 (SALT — 4번)
  Set.copyOf(널 있는 List)   : NullPointerException: Cannot invoke "Object.equals(Object)" because "e0" is null
  ```

  중복은 받아 주지만 **`null` 은 여전히 거부한다.** 두 계약이 따로 논다.
- `Set.of(a, b)` 에 런타임 값을 넣으면 **데이터에 중복이 들어오는 날 터진다.**

**판정 기준은 `equals` 다**

**출력** (`Ex.java` — 40-d, 17·21·25 동일)

```text
--- 3) Set.of 의 중복 판정 기준
equals 재정의한 Box 둘 : IllegalArgumentException: duplicate element: Box(1)
재정의 안 한 Plain 둘  : 2
```

- 같은 값이어도 `equals` 를 재정의하지 않았으면 **둘 다 들어간다.**
  [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) 의 계약이 여기서도 판정 기준이다.

### 6. `Set` 에 넣고 필드를 바꾸면

**출력** (`Ex.java` — 40-b, 17·21·25 동일)

```text
--- 6) Set 에 넣고 키를 바꾸면
넣은 직후 contains  : true / 내용 [Box(1)]
필드를 바꾼 뒤 contains : false / 내용 [Box(99)]
같은 값으로 새 객체     : false
remove 도 안 된다       : false / 크기 1
순회로는 보인다         : Box(99)
```

**네 가지의 답**

| 호출 | 결과 |
|---|---|
| `contains(box)` | **`false`** |
| `remove(box)` | **`false`** (안 지워진다) |
| `size()` | **`1`** |
| 순회 | **`Box(99)`** 가 나온다 |

**사라진 것이 아니라 못 찾는 것이다**

```text
   전 상태                            후 상태 (box.v = 99)

   버킷 1  -> [Box(1)]                버킷 1  -> [Box(99)]     <- 객체는 여기 그대로
   버킷 99 -> 비었다                   버킷 99 -> 비었다
       ^                                  ^
  contains 는 hashCode()=1 로            contains 는 hashCode()=99 로
  버킷 1 을 본다 -> 찾는다                버킷 99 를 본다 -> 없다
```

- **자리(버킷)는 넣을 때 정해지고, 찾을 때 다시 계산한다.** 그 둘이 어긋난 것이다.
- 버킷이 무엇인지는 [`../../../../../data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/) 가 정본이다.

**`new Box(99)` 로도 못 찾는다**

- `false` 다. 객체가 **버킷 1** 에 들어 있으므로 버킷 99 를 아무리 뒤져도 없다.

**javadoc**

> Note: great care must be exercised if mutable objects are used as map keys. The behavior of a map is not specified if the value of an object is changed in a manner that affects `equals` comparisons while the object is a key in the map.

- **"동작이 명세되지 않는다"** — 즉 위에서 본 것도 "이렇게 되기로 되어 있는" 것이 아니다.

### 7. `removeIf` 가 가끔만 터진다

**출력** (`Ex.java` — 40-b, 17·21·25 동일)

```text
--- 4) removeIf
removeIf(짝수)          : [1, 3, 5]
List.of 에 removeIf      : UnsupportedOperationException
List.of 에 removeIf(아무것도 안 걸림) : UnsupportedOperationException
Arrays.asList 에 removeIf : UnsupportedOperationException: remove
Arrays.asList 에 removeIf(아무것도 안 걸림) : OK
```

**세 줄의 답**

- `Arrays.asList(1, 2).removeIf(짝수)` → **`UnsupportedOperationException: remove`**
- `Arrays.asList(1, 3).removeIf(짝수)` → **`OK`** (지울 것이 없다)
- `List.of(1, 3).removeIf(짝수)` → **`UnsupportedOperationException`** (지울 것이 없어도)

**둘째와 셋째가 갈리는 이유**

```text
  Arrays.asList                          List.of

  removeIf 를 재정의하지 않는다            removeIf 를 재정의해서
  -> Collection 의 기본 구현을 쓴다          무조건 uoe() 를 던진다
     = 이터레이터를 돌며 조건에 맞으면
       it.remove() 를 부른다
        |
  조건에 맞는 원소가 없으면
  it.remove() 가 한 번도 안 불린다 -> 안 던진다
```

**메시지에 `remove` 가 붙는 이유**

- `Iterator.remove()` 의 **기본 구현**이 던지는 것이라 메시지가 `"remove"` 다.

```java
// JDK 21.0.5  java.base/java/util/Iterator.java  — 실제 소스 그대로
    default void remove() {
        throw new UnsupportedOperationException("remove");
    }
```

- `List.of` 쪽은 `ImmutableCollections.uoe()` 가 **메시지 없이** 던진다. 그래서 문구가 다르다.

**갈림을 허용하는 javadoc**

> Such methods should (but are not required to) throw an `UnsupportedOperationException` if the invocation would have no effect on the collection.

- 39번 (8)에서 본 그 문장이다. **`addAll(빈 컬렉션)` 과 같은 성질의 갈림**이다.

### 8. `remove` 의 오버로드

**출력** (`Ex.java` — 40-b, 17·21·25 동일)

```text
--- 5) remove(int) 와 remove(Object)
remove(1) 후         : [10, 30]   <- 인덱스 1 이 지워졌다
remove(Integer(20)) 후 : [10, 30]
remove(100) 은?      : IndexOutOfBoundsException: Index 100 out of bounds for length 3
```

**세 줄**

- `l.remove(1)` → **인덱스 1** 을 지운다. 결과 `[10, 30]`.
- `l.remove(Integer.valueOf(20))` → **값 20** 을 지운다. 결과 `[10, 30]`.
- `l.remove(100)` → **인덱스 100** 을 지우려다 죽는다.

**메시지 전문**

```text
Index 100 out of bounds for length 3
```

**`List<String>` 에서는 왜 안 생기나**

```text
  List<Integer>                          List<String>

  remove(int)      <- int 인자          remove(int)      <- int 인자
  remove(Object)   <- Integer 도 여기   remove(Object)   <- String 은 여기밖에 없다
        |                                      |
  l.remove(1) 은 두 후보가 다 맞는다       l.remove("a") 는 후보가 하나뿐
  -> 박싱 없는 remove(int) 가 이긴다
```

- 오버로딩 해소는 **박싱이 필요 없는 후보를 먼저** 고른다([`../08-method-declaration-overloading/`](../08-method-declaration-overloading/)).
- `List<String>` 에는 `remove(int)` 와 맞는 호출이 애초에 안 생긴다.

### 9. `copyOf` 는 언제 복사하나

**출력** (`Ex.java` — 40-a, 17·21·25 동일)

```text
--- 5) copyOf 는 이미 불변이면 복사하지 않는다
List.copyOf(List.of(..)) == 원본 : true
List.copyOf(ArrayList) == 원본   : false
Set.copyOf(Set.of(..)) == 원본   : true
Map.copyOf(Map.of(..)) == 원본   : true
List.copyOf(Arrays.asList) == 원본 : false
unmodifiableList(unmodifiableList) == 원본 : true
```

| 호출 | 새 객체를 만드나 |
|---|---|
| `List.copyOf(List.of("a","b"))` | **아니다** — 자기 자신을 돌려준다 |
| `List.copyOf(new ArrayList<>(...))` | **그렇다** |
| `List.copyOf(Arrays.asList(...))` | **그렇다** — 불변이 아니다(`set` 이 된다) |
| `Collections.unmodifiableList(이미_unmodifiable)` | **아니다** — 두 번 감싸지 않는다 |

**보장인가**

- **관측이다.** javadoc 은 성능 최적화를 약속하지 않고, 오히려 인스턴스 동일성에 기대지 말라고 적는다.

> Callers should make no assumptions about the identity of the returned instances. Factories are free to create new instances or reuse existing ones.

- 그러니 **`copyOf` 를 값싸다고 믿는 것은 되지만, `==` 로 같은지 검사하면 안 된다.**

### 10. getter 에 무엇을 쓰나

| 후보 | 호출자가 고칠 수 있나 | 내 변경이 새나 | 호출자 순회 중 내가 `add` 하면 |
|---|---|---|---|
| `return items;` | **O** — 막는 것이 없다 | O | `ConcurrentModificationException` |
| `unmodifiableList(items)` | X | **O — 샌다** | **`ConcurrentModificationException`** |
| `List.copyOf(items)` | X | X | 아무 일 없음 |
| `new ArrayList<>(items)` | O(자기 복사본을) | X | 아무 일 없음 |

**"호출자가 순회 중인데 내가 `items.add` 를 한다"**

- **`unmodifiableList` 와 `items` 그대로** 에서 터진다. 둘 다 **같은 리스트를 보고 있기** 때문이다.
- 호출자는 아무 잘못도 안 했는데 자기 `for` 문에서 예외를 받는다. 원인이 안 보인다.

**스냅샷이 필요하면**

- **`List.copyOf(items)`**. 그 순간의 내용이 굳고, `null` 이 없다면 비용도 한 번뿐이다.

**복사 비용이 아까울 때**

- `Collections.unmodifiableList(items)` 를 쓰되 **"이것은 살아 있는 뷰다"를 javadoc 에 적는다.**
- 호출자가 오래 들고 있으면 안 된다는 것, 순회 중 변경이 보일 수 있다는 것까지 적는다.
- 적지 않으면 호출자는 **사진이라고 믿는다.** 그것이 이 주제의 대표 사고다.

### 11. 어느 것을 쓰는가

| 상황 | 답 | 이유 |
|---|---|---|
| 상수 목록 선언 | **`List.of(...)`** | 짧고, `null` 을 막고, 진짜 불변 |
| `null` 이 섞일 수 있다 | `Arrays.asList(...)` 를 감싼 `new ArrayList<>(...)` | `of` 계열은 NPE |
| 받은 컬렉션을 필드에 보관 | **`List.copyOf(받은것)`** | 호출자가 나중에 고쳐도 안 바뀐다 |
| 앞 20개를 잘라 캐시에 | **`List.copyOf(all.subList(0,20))`** | 뷰를 캐시에 넣으면 원본을 붙잡고 죽는다 |
| 구간을 통째로 지운다 | **`l.subList(a,b).clear()`** | 이때는 뷰가 이득이다 |
| 조건에 맞는 원소를 지운다 | **`removeIf`** | 순회하며 지우면 CME(43번) |
| 배열을 잠깐 리스트처럼 읽는다 | `Arrays.asList(arr)` | 복사가 없다. **읽기만** |

### 12. 무엇이 보장인가

| 관측 | 보장? | 근거 |
|---|---|---|
| `List.of` 의 구체 타입이 `ImmutableCollections$List12` | **아니다** | 문서화되지 않은 내부 클래스 |
| `Set.of("a","a")` 메시지가 `duplicate element: a` | **아니다** | 예외 **클래스**(`IllegalArgumentException`)만 계약이다 |
| 원본을 고친 뒤 `subList` 에서 CME | **아니다** | javadoc 은 "semantics become undefined" 까지만 |
| `Set.of` 의 순회 순서가 실행마다 바뀜 | **사실상 보장** | `Set.of` javadoc — "iteration order ... is unspecified and is subject to change" |

**테스트에 적어도 되는 것**

- **넷 다 적으면 안 된다.**
- 넷째는 "바뀐다"는 성질이 보장이지 **어떤 순서인지**가 보장이 아니다.
  그러니 `assertEquals("[a, b, c]", set.toString())` 은 여전히 틀린 테스트다.
- 적어도 되는 것은 **예외 클래스**(`UnsupportedOperationException`·`IllegalArgumentException`·`NullPointerException`)와
  **컬렉션 내용의 동등성**(`assertEquals(Set.of("a","b"), result)` — `Set.equals` 는 순서와 무관하다)뿐이다.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Ex.java` (40-a) | 세 팩토리의 세 축(널·변경·원본 반영), `Arrays.asList` 의 양방향 뷰, `copyOf` 의 동일 인스턴스 최적화, 구체 타입 8종, 중복 원소·중복 키 | 17 · 21 · 25 (**출력 동일**) |
| `Ex.java` (40-b) | `subList` 의 쓰기 전파·`clear`·구조적 수정 뒤 CME, `removeIf` 의 데이터 의존 갈림, `remove(int)`/`remove(Object)`, 가변 키를 넣고 바꾼 뒤의 `contains`/`remove`/순회, 집합 연산 셋 | 17 · 21 · 25 (**출력 동일**) |
| `Ex.java` (40-c) | `Set.of`·`Map.of` 의 순회 순서가 **JVM 실행마다 달라지는 것** — 같은 JDK 21.0.5 로 **3회 실행** | 21 (**3회 실행 · 3회 다름**) |
| `Ex.java` (40-d) | 기본형 배열의 `Arrays.asList`, `unmodifiableList` 의 두 구체 타입, `Set.of` 의 중복 판정 기준(`equals`), `List.of()` 의 동일 인스턴스, `Map.ofEntries` 11쌍, `Collections.sort(Arrays.asList)` 가 되는 것 | 17 · 21 · 25 (**출력 동일**) |
| `Ex.java` (40-e) | `Set.copyOf` 가 중복은 흡수하고 `null` 은 거부하는 것 | 17 · 21 · 25 (**널 거부 동일 · 순서만 실행마다 다름**) |
| `src.zip` 열람 | `List` 의 「Unmodifiable Lists」·`subList` javadoc, `Collection` 의 「Unmodifiable (View) Collections」, `ImmutableCollections` 의 `SALT32L`/`REVERSE`, `Iterator.remove` 기본 구현, `@since` 확인(`of`=9 · `copyOf`=10 · `removeIf`=1.8) | 21 |

**javac 13회 · java 15회**(40-c 의 3회 실행 포함).

**버전별로 갈린 것**

```text
40-a · 40-b · 40-d : 세 버전 출력이 한 글자도 같다
                     (스택트레이스를 찍지 않는 프로그램이라 줄 번호 차이조차 없다)

40-c               : 버전이 아니라 "실행" 이 축이다
                     같은 21.0.5 에서 세 번 띄웠더니 Set.of 순서가 세 번 다 달랐다
```

- ★ **이 주제에서는 「세 버전 비교」가 답을 못 주는 축이 있다.**\
  `Set.of` 의 순서는 **버전이 아니라 JVM 실행마다** 흔들린다.\
  버전만 바꿔 가며 돌렸다면 "세 번 다 같았다"는 **잘못된 안심**을 얻었을 수도 있었다.

**구현 의존 항목** (버전이 오르면 다시 돌려야 하는 것)

- 구체 타입 문자열 — `ImmutableCollections$List12`/`$ListN`/`$Set12`/`$Map1`, `Arrays$ArrayList`,
  `Collections$UnmodifiableRandomAccessList`/`$UnmodifiableList`/`$EmptyList`, `ArrayList$SubList`.
- `List.copyOf` 의 **동일 인스턴스 반환** — 최적화이지 계약이 아니다.
- 예외 **메시지 문구** — `duplicate element: a` · `duplicate key: a` · `Index 100 out of bounds for length 3` · `remove`.
- 구조적 수정 뒤 `subList` 에서 **CME 가 난다는 것 자체** — javadoc 은 "undefined" 까지만 약속한다.
- `Set.of`·`Map.of` 의 **구체적인 순서** — 매 실행 다르다. 다시 돌릴 때마다 값이 바뀐다.
- **Java 8·9 는 안 돌려 봄** — 이 머신에 없다. `List.of`(9)·`copyOf`(10)는 8에 애초에 없다.
