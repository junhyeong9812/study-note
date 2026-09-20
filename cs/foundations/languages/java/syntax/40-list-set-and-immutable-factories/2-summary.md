# java/syntax/40 — `List`·`Set` API 와 불변 팩토리: `List.of`·`copyOf`·`unmodifiable*` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **선행** — [`../39-collections-framework-map/`](../39-collections-framework-map/). 옵셔널 연산이 왜 존재하는지가 전제다.
> **기준 소스** — JDK 21.0.5 의 `lib/src.zip` 을 **직접 풀어 읽은** javadoc 과 구현이다.\
> `java.base/java/util/List.java` — 「Unmodifiable Lists」 절 · `subList` javadoc · `of`/`copyOf` 의 `@since`.\
> `java.base/java/util/Collection.java` — 「Unmodifiable Collections」·「Unmodifiable View Collections」·「View Collections」 절.\
> `java.base/java/util/ImmutableCollections.java` — `SALT32L`·`REVERSE` 필드와 그 주석.\
> 인용은 **그 파일에서 복사한 것만** 옮겼다.
> **실행 검증** — 이 문서의 모든 출력·에러는 Temurin JDK 에서 **실제로 돌려** 얻은 것이다.\
> 프로그램 5개. 넷(40-a·40-b·40-d·40-e)은 **17.0.13 · 21.0.5 · 25.0.1** 에서 돌렸고,
> 나머지 하나(40-c)는 **같은 JVM 을 세 번 띄워** 실행마다 결과가 달라지는 것을 보였다.
> **버전** — `Arrays.asList` 는 **Java 1.2**, `Collections.unmodifiableList` 도 **1.2**.\
> `List.of`·`Set.of`·`Map.of` 는 **Java 9**, `List.copyOf`·`Set.copyOf`·`Map.copyOf` 는 **Java 10**.\
> `removeIf` 는 **Java 8**. `@since` 는 전부 `src.zip` 에서 직접 읽었다.
> **범위** — 동적 배열이라는 **자료구조**(2배 증폭·상각 분석)와 해시 집합의 내부는
> [`../../../../../data-structure/01-dynamic-array/`](../../../../../data-structure/01-dynamic-array/)·[`../../../../../data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/) 가 정본이다.\
> 그쪽은 **`ArrayList` 가 왜 2배씩 늘어나나**까지, 여기는 **그것을 어느 팩토리로 만들고 무엇이 막히나**부터다.\
> `Set` 이 원소에 요구하는 계약은 [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) 가 정본이다.
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**리스트를 만드는 세 가지는 「사진」·「창문」·「복사본」이다.**

| 비유 | 실체 | 고칠 수 있나 | `null` 을 받나 | 원본이 비치나 |
|---|---|---|---|---|
| **사진** — 찍은 순간 그대로 굳는다 | **`List.of(...)`** (9+) | X | **X** | 원본이 없다 |
| **창문** — 밖이 바뀌면 그대로 보인다 | **`Collections.unmodifiableList(l)`** | X | O | **O** |
| **배열에 낸 창문** — 칸 수는 못 바꾼다 | **`Arrays.asList(...)`** | **set 만 O** | O | **O**(배열이 원본) |
| 사진을 새로 찍는다 | **`List.copyOf(l)`** (10+) | X | **X** | X |
| 진짜 리스트 | `new ArrayList<>(l)` | O | O | X |

- **"불변"이라는 한 단어로 셋을 묶으면 틀린다.**\
  세 축이 따로 논다 — **고칠 수 있나 · `null` 을 받나 · 원본이 비치나.**
- 셋 다 `add` 는 `UnsupportedOperationException` 이다. **거기까지만 같다.**

```text
        List.of("a","b")              Collections.unmodifiableList(src)

  [a][b]  <- 자기 배열을 들고 있다      +-----------+
   ^                                   | 읽기만 전달 |  --->  src [a][b][c]
   |                                   +-----------+         ^
  src 를 나중에 고쳐도                        |                |
  아무 일도 안 일어난다                  src 를 고치면 창문에 비친다
```

**똑같은 구조로** 자바가 동작한다: 사진 = 불변 컬렉션, 창문 = 수정 불가 **뷰**.

실무에서 이게 터지는 자리는 **"방어적 복사를 했다"고 믿는 한 줄**이다.

```java
private final List<String> items;
public List<String> getItems() { return Collections.unmodifiableList(items); }   // 창문이다
```

호출자는 못 고치지만, **내가 `items` 를 고치면 호출자가 들고 있던 것도 바뀐다.**

> **불변(immutable)** — 만들어진 뒤 내용이 절대 안 바뀌는 것.\
> 예: `List.of("a","b")` 는 어디서 무엇을 해도 `[a, b]` 다.

> **수정 불가(unmodifiable)** — 고치는 메서드가 `UnsupportedOperationException` 을 던지는 것.\
> 예: `Collections.unmodifiableList(src)` 는 내가 못 고칠 뿐, `src` 가 바뀌면 내용이 바뀐다.

> **뷰(view)** — 원소를 직접 저장하지 않고 뒤에 있는 것(리스트·배열)에 위임하는 컬렉션.\
> 예: `Arrays.asList(arr)` 는 `arr` 의 칸을 그대로 읽고 쓴다.

## 이 주제가 답하려는 질문

원고가 없는 API 주제라 「문제」 대신 이 세 질문을 둔다.

1. `List.of` · `Arrays.asList` · `Collections.unmodifiableList` 는 **무엇이 다른가** —
   세 축(널 허용·변경 가능성·원본 반영)으로 갈라서.
2. **뷰인 것과 아닌 것**을 어떻게 구별하나 — `subList`·`Arrays.asList`·`unmodifiableList` 가 왜 위험한가.
3. `Set` 이 원소에 요구하는 것을 어기면 **무엇이 관측되나** — 그리고 `Set.of` 가 왜 중복에 던지나.

## 예시 데이터 — 이 묶음이 공유하는 것

39~43번은 같은 데이터를 쓴다.

```text
과일 다섯 개 (중복 하나)
  "pear"  "apple"  "fig"  "apple"  "date"

팩토리 비교용 축소판
  ["a", "b", "c"]  — 짧아야 뷰의 전·후를 한 줄에 나란히 놓을 수 있다
```

- 39번이 **어디에 담을지**를 골랐다면, 40번은 **어떻게 만들지**를 고른다.

## 동작 방식

### (1) 세 팩토리의 첫째 축 — `null` 을 받나

**언제 쓰나** — DB·JSON 에서 온 값으로 리스트를 만들 때. `null` 이 한 칸만 섞여도 갈린다.

**실행 결과** (`Ex.java` — 40-a, 17·21·25 동일)

```text
--- 1) null 원소를 받나
List.of("a", null)                  : NullPointerException
Arrays.asList("a", null)             : [a, null]
Collections.unmodifiableList(널 포함) : [a, null]
List.copyOf(널 포함)                  : NullPointerException
Set.of("a", null)                    : NullPointerException
new ArrayList<>(널 포함)              : [a, null]
```

```text
        null 을 거부하는 쪽                      null 을 통과시키는 쪽

  List.of / Set.of / Map.of  (9+)         Arrays.asList          (1.2)
  List.copyOf / Set.copyOf   (10+)        Collections.unmodifiableList
        |                                  new ArrayList<>(...)
  계약 자체가 금지한다                            |
  "They disallow null elements"          옛 API 라 null 을 막지 않는다
        |                                        |
  NPE 가 생성 시점에 난다                   나중에 NPE 가 난다 (정렬·스트림에서)
```

그림 해설 (한 단계씩):

- **9 이후에 들어온 팩토리는 전부 `null` 을 거부한다.** 계약에 적혀 있다.

> They disallow `null` elements. Attempts to create them with `null` elements result in `NullPointerException`.

- **`copyOf` 도 거부한다.** 원본에 `null` 이 하나라도 있으면 복사 자체가 안 된다.
- 옛 API(`Arrays.asList`·`unmodifiableList`)는 통과시킨다 — 1.2 시절 설계다.

비용 — 거부하는 쪽이 **더 일찍 터진다.**\
통과시키면 리스트를 만드는 자리는 조용하고, 나중에 `sorted()`·`joining()` 에서 터진다.
그때는 **어디서 들어온 `null` 인지 모른다.**

### (2) 세 팩토리의 둘째 축 — 고칠 수 있나

**언제 쓰나** — 받은 리스트를 정렬하거나 원소를 더할 때.

**실행 결과** (`Ex.java` — 40-a, 17·21·25 동일)

```text
--- 2) 고칠 수 있나
List.of.set(0,"z")                   : UnsupportedOperationException
Arrays.asList.set(0,"z")             : OK  -> [z, b, c]
Arrays.asList.add("z")               : UnsupportedOperationException
unmodifiableList.set(0,"z")          : UnsupportedOperationException
List.copyOf.set(0,"z")               : UnsupportedOperationException
```

```text
        add / remove          set(i, x)
  ArrayList          O              O        진짜 리스트
  Arrays.asList      X              O        <- 배열 뷰: 길이만 고정
  List.of            X              X        불변
  List.copyOf        X              X        불변
  unmodifiableList   X              X        수정 불가 뷰
```

그림 해설 (한 단계씩):

- **`Arrays.asList` 만 한 칸이 다르다.** `set` 은 되고 `add`/`remove` 는 안 된다.
- 이유는 배열 위의 뷰이기 때문이다 — **칸을 덮어쓰는 건 되고 칸 수를 바꾸는 건 안 된다.**
- 나머지 셋은 세 칸 전부 `UnsupportedOperationException` 이다.

비용 — `Arrays.asList` 의 이 반쪽 능력이 가장 헷갈린다.\
`Collections.sort(Arrays.asList(arr))` 는 **동작한다**(정렬은 `set` 만 쓴다).
그런데 `Arrays.asList(arr).removeIf(...)` 는 조건에 걸리는 원소가 있을 때만 터진다.

### (3) 세 팩토리의 셋째 축 — 원본이 비치나

**언제 쓰나** — getter 로 내부 컬렉션을 내보낼 때. 이 축을 놓치면 **방어가 안 된 채로 방어했다고 믿는다.**

**실행 결과** (`Ex.java` — 40-a, 17·21·25 동일)

```text
--- 3) 원본을 고치면 따라 바뀌나
원본 src                 : [a, b, c]
unmodifiableList(src)    : [a, b, c]
List.copyOf(src)         : [a, b, c]
src.add("d") 후 ...
원본 src                 : [a, b, c, d]
unmodifiableList(src)    : [a, b, c, d]   <- 따라 바뀌었다 (뷰)
List.copyOf(src)         : [a, b, c]      <- 그대로다 (복사본)
```

```text
    전 상태                          조작                     후 상태

  src        [a][b][c]          src.add("d")          src        [a][b][c][d]
  unmod  ->  src 를 가리킴                             unmod  ->  [a,b,c,d]   바뀐다
  copyOf     [a][b][c] (자기 것)                       copyOf     [a,b,c]     그대로
```

그림 해설 (한 단계씩):

- `Collections.unmodifiableList` 는 **읽기를 원본에 위임**한다. 그것이 뷰의 정의다.
- javadoc 이 둘을 다른 이름으로 구별해 놓았다.

> An *unmodifiable collection* is a collection, all of whose mutator methods ... are specified to throw `UnsupportedOperationException`.

> An *unmodifiable view collection* is a collection that is unmodifiable and that is also a view onto a backing collection. Its mutator methods throw `UnsupportedOperationException`, ... while reading and querying methods are delegated to the backing collection.

- **`unmodifiableList` 는 둘째 것**이다. 이름에 "view" 가 안 붙어 있어서 잘 놓친다.
- javadoc 은 "unmodifiable 이 immutable 은 아니다"까지 명시한다.

> An unmodifiable collection is not necessarily immutable. If the contained elements are mutable, the entire collection is clearly mutable, even though it might be unmodifiable.

비용 — getter 에서 무엇을 쓸지가 이 축으로 갈린다.

```java
// 창문 — 내가 items 를 고치면 호출자가 들고 있던 것도 바뀐다
return Collections.unmodifiableList(items);
// 사진 — 그 순간의 내용이 굳는다. 대신 복사 비용이 든다
return List.copyOf(items);
```

### (4) `Arrays.asList` 는 배열의 뷰다 — 양방향으로

**언제 쓰나** — 배열을 리스트로 바꿔 쓸 때. `String[] args` 를 다룰 때 자주 나온다.

**실행 결과** (`Ex.java` — 40-a, 17·21·25 동일)

```text
--- 4) Arrays.asList 는 배열의 뷰다
리스트를 고치면 배열도    : [a, Z, c]
배열을 고치면 리스트도    : [a, Z, Y]
```

```text
     String[] back = {"a","b","c"}
              |
     Arrays.asList(back)  <- 배열을 복사하지 않는다. 그대로 감싼다
              |
   view.set(1,"Z")  ---> back 이 [a, Z, c] 가 된다
   back[2] = "Y"    ---> view 가 [a, Z, Y] 가 된다
```

그림 해설 (한 단계씩):

- **복사가 아니다.** `Arrays$ArrayList` 가 배열 참조를 그대로 들고 있다.
- **양방향으로 비친다.** 리스트를 고쳐도 배열이 바뀌고, 배열을 고쳐도 리스트가 바뀐다.
- 끊으려면 복사한다 — `new ArrayList<>(Arrays.asList(back))` 또는 `List.of(back)`(널 없을 때).

비용 — 복사를 안 하니 싸다. 대신 **원본 배열의 수명에 묶인다.**\
배열을 잠깐 리스트처럼 읽을 때만 쓰고, 오래 들고 있지 않는다.

### (5) `subList` 도 뷰다 — 그리고 원본을 고치면 죽는다

**언제 쓰나** — 리스트의 일부만 넘길 때. 페이지네이션 코드에서 자주 나온다.

**실행 결과** (`Ex.java` — 40-b, 17·21·25 동일)

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

```text
     base  [a][b][c][d][e]
               ^-----^
               subList(1,4)  <- 원본의 1~3 칸을 가리킨다

   sub.set(0,"B")   -> base 의 1번 칸이 바뀐다
   sub.clear()      -> base 에서 1~3 칸이 통째로 빠진다 -> [a, e]
   base.add("f")    -> 뷰가 무효가 된다 -> 읽기만 해도 CME
   base.set(0,"A")  -> 크기가 안 바뀌었으므로 뷰는 살아 있다
```

그림 해설 (한 단계씩):

- `subList` 는 **구간을 가리키는 창문**이다. javadoc 이 그 용법까지 적어 놓았다.

> This method eliminates the need for explicit range operations ... For example, the following idiom removes a range of elements from a list:
> `list.subList(from, to).clear();`

- **원본을 구조적으로 고치면 뷰의 의미가 정의되지 않는다.**

> The semantics of the list returned by this method become undefined if the backing list (i.e., this list) is *structurally modified* in any way other than via the returned list.

- ★ `ConcurrentModificationException` 은 **그 "정의되지 않음"을 `ArrayList` 가 친절하게 알려 준 것**이지 계약이 아니다.
- **`set` 은 구조적 수정이 아니다.** 크기가 안 바뀌므로 뷰가 살아 있다.

비용 — `subList` 로 잘라 낸 것을 **오래 들고 있으면 안 된다.**\
원본 리스트 전체가 메모리에 붙잡혀 있고, 원본이 바뀌는 순간 죽는다.\
끊으려면 복사한다 — 실측 타입이 그 차이를 보여 준다.

```text
--- 3) subList 로 잘라낸 것을 오래 들고 있으면
keep 의 구체 타입 : java.util.ArrayList$SubList
끊으려면          : [a, b] / [a, b]
List.copyOf(keep) 의 타입 : java.util.ImmutableCollections$List12
```

### (6) `Set.of` 의 순회 순서는 **실행할 때마다 다르다**

**언제 쓰나** — `Set.of(...)` 의 출력을 로그·테스트에서 볼 때.

**실행 결과** (`Ex.java` — 40-c, JDK 21.0.5 — **같은 프로그램을 세 번 실행**)

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

```text
     같은 JDK · 같은 프로그램 · 세 번 실행

  Set.of   [a,b,c,d,e]  ->  [c,d,e,a,b]  ->  [e,d,c,b,a]   매번 다르다
  HashSet  [a,b,c,d,e]  ->  [a,b,c,d,e]  ->  [a,b,c,d,e]   매번 같다
  List.of  [a,b,c,d,e]  ->  [a,b,c,d,e]  ->  [a,b,c,d,e]   리스트는 순서가 계약
```

그림 해설 (한 단계씩):

- ★ **`Set.of`·`Map.of` 는 JVM 을 다시 띄울 때마다 순회 순서가 바뀐다.** 일부러 그렇게 만들었다.
- JDK 소스가 그 의도를 그대로 적어 놓았다.

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

- **`HashSet` 은 안 바뀐다.** 그래서 `HashSet` 의 순서에는 실수로 기대게 되고, `Set.of` 는 못 기댄다.
- 이것이 **의도된 설계**다 — 순서에 기대는 코드를 **빨리 깨뜨려서** 알려 주려는 것이다.

비용 — 없다(그것이 이득이다).\
`Set.of` 의 출력을 로그로 비교하거나 테스트에 적으면 **CI 에서 무작위로 실패**한다.\
순서가 필요하면 `List.of` 나 `LinkedHashSet` 을 쓴다.

### (7) `Set.of`·`Map.of` 는 중복에 **던진다**

**언제 쓰나** — 상수 집합을 선언할 때. 상수가 늘면서 실수로 겹칠 때.

**실행 결과** (`Ex.java` — 40-a, 17·21·25 동일)

```text
--- 7) 중복을 넣으면
Set.of("a","a")   : IllegalArgumentException: duplicate element: a
Map.of("a",1,"a",2) : IllegalArgumentException: duplicate key: a
List.of("a","a")  : [a, a]
new HashSet<>(중복 포함) : [a]
```

```text
  new HashSet<>(List.of("a","a"))          Set.of("a","a")

  둘째 add 가 false 를 돌려준다              IllegalArgumentException:
  조용히 하나가 사라진다                       duplicate element: a
        |                                            |
        v                                            v
  [a]  — 결과는 나오는데 내가 의도한 건가?      멈춘다 — 그래서 알게 된다
```

그림 해설 (한 단계씩):

- **`Set.of` 가 더 엄격하다.** `HashSet` 의 조용한 흡수를 예외로 승격시킨다.
- 메시지에 **어느 원소가 겹쳤는지**가 들어 있다.
- `List.of` 는 중복을 그대로 둔다 — 리스트는 원래 중복을 허용한다.
- 같은 설계를 `Collectors.toMap` 에서도 본다([`../47-collectors-basics/`](../47-collectors-basics/)).

비용 — 상수 선언에서 실수를 **클래스 로딩 시점에** 잡아 준다.\
대신 런타임 데이터로 `Set.of(a, b)` 를 만들면 **중복이 들어오는 순간 터진다** — 그때는 `new HashSet<>(...)` 가 맞다.

### (8) `Set` 에 넣고 키를 바꾸면 원소가 사라진다

**언제 쓰나** — 가변 객체를 `Set`·`Map` 키로 쓸 때.

**실행 결과** (`Ex.java` — 40-b, 17·21·25 동일)

```text
--- 6) Set 에 넣고 키를 바꾸면
넣은 직후 contains  : true / 내용 [Box(1)]
필드를 바꾼 뒤 contains : false / 내용 [Box(99)]
같은 값으로 새 객체     : false
remove 도 안 된다       : false / 크기 1
순회로는 보인다         : Box(99)
```

```text
   전 상태                       조작                    후 상태

  hashCode()=1 인 칸            box.v = 99          hashCode()=1 인 칸
     [Box(1)]                                          [Box(99)]
        ^                                                 ^
   contains(box) -> 1번 칸을 본다                  contains(box) -> 99번 칸을 본다
   있다 -> true                                    비어 있다 -> false
                                                   remove 도 같은 이유로 실패
                                                   순회는 칸을 안 쓰므로 보인다
```

그림 해설 (한 단계씩):

- **원소는 그대로 있다.** `size()` 가 1 이고 순회하면 나온다.
- 못 찾는 것뿐이다 — `contains`·`remove` 가 **해시 값으로 칸을 먼저 찾기** 때문이다.
- javadoc 이 `Map` 쪽에서 이 상황을 못박아 놓았다(`Set` 도 같은 이유다).

> Note: great care must be exercised if mutable objects are used as map keys. The behavior of a map is not specified if the value of an object is changed in a manner that affects `equals` comparisons while the object is a key in the map.

- 계약의 다섯 조항과 위반 증상은 [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) 가 정본이다.

비용 — 방어는 하나다. **`Set`·`Map` 키에는 불변 객체만 쓴다.**\
`record`([`../14-records/`](../14-records/))·`String`·래퍼 타입이 그래서 키로 좋다.

## 문법 — 형태와 규칙

직접 쓴 최소 예제다. 출력은 전부 실행 결과다.

### 팩토리 지도

| 하고 싶은 일 | 쓰는 것 | 버전 | `null` | 고칠 수 있나 | 원본이 비치나 |
|---|---|---|---|---|---|
| 상수 리스트 선언 | **`List.of(...)`** | 9 | X | X | — |
| 상수 집합 선언 | **`Set.of(...)`** | 9 | X | X | — |
| 상수 맵 선언 | **`Map.of(k,v,...)`** | 9 | X | X | — |
| 키·값 쌍이 10쌍 넘는 맵 | `Map.ofEntries(Map.entry(k,v), ...)` | 9 | X | X | — |
| 받은 것을 얼려서 보관 | **`List.copyOf(c)`** | 10 | X | X | **X** |
| 내부 컬렉션을 읽기 전용으로 노출 | `Collections.unmodifiableList(l)` | 1.2 | O | X | **O** |
| 배열을 잠깐 리스트처럼 | `Arrays.asList(arr)` | 1.2 | O | **set 만** | **O** |
| 고칠 리스트 | `new ArrayList<>(c)` | 1.2 | O | O | X |
| 고칠 집합 (순서 유지) | `new LinkedHashSet<>(c)` | 1.4 | O | O | X |
| 빈 것 | `List.of()` / `Collections.emptyList()` | 9 / 1.5 | — | X | — |

- **`Map.of` 는 10쌍까지**다(오버로드가 10개). 그 이상은 `Map.ofEntries`.
- `Map.entry(k, v)` 는 **Java 9**다. 반환 타입은 `Map.Entry` 지만 `setValue` 가 막혀 있다(41번).

### `copyOf` 는 이미 불변이면 복사하지 않는다

**실행 결과** (`Ex.java` — 40-a, 17·21·25 동일)

```text
--- 5) copyOf 는 이미 불변이면 복사하지 않는다
List.copyOf(List.of(..)) == 원본 : true
List.copyOf(ArrayList) == 원본   : false
Set.copyOf(Set.of(..)) == 원본   : true
Map.copyOf(Map.of(..)) == 원본   : true
List.copyOf(Arrays.asList) == 원본 : false
unmodifiableList(unmodifiableList) == 원본 : true
```

- **이미 `List.of` 계열이면 자기 자신을 돌려준다.** 복사 비용이 0 이다.
- `Arrays.asList` 는 불변이 아니므로 복사한다(`set` 이 되기 때문이다).
- `Collections.unmodifiableList` 도 **두 번 감싸지 않는다.**
- 이 최적화는 **관측**이다. javadoc 이 "같은 인스턴스를 돌려줄 수 있다"까지만 열어 둔다.

### 구체 타입 — 기대지 말 것

**실행 결과** (`Ex.java` — 40-a, 17·21·25 동일)

```text
--- 6) 구체 타입
List.of("a")                       java.util.ImmutableCollections$List12
List.of("a","b")                   java.util.ImmutableCollections$List12
List.of(1..3)                      java.util.ImmutableCollections$ListN
List.of()                          java.util.ImmutableCollections$ListN
Arrays.asList(..)                  java.util.Arrays$ArrayList
Collections.unmodifiableList       java.util.Collections$UnmodifiableRandomAccessList
Set.of("a","b")                    java.util.ImmutableCollections$Set12
Map.of("a",1)                      java.util.ImmutableCollections$Map1
```

- **원소가 1~2개면 `List12`, 3개 이상이면 `ListN`** 이다. 작은 리스트를 위한 전용 클래스가 있다.
- `Arrays$ArrayList` 는 `java.util.ArrayList` **가 아니다.** 이름만 같은 중첩 클래스다.
- 전부 **문서화되지 않은 내부 타입**이다. 캐스팅하지 않는다.

### `removeIf` — 그리고 옵셔널 연산의 마지막 함정

**실행 결과** (`Ex.java` — 40-b, 17·21·25 동일)

```text
--- 4) removeIf
removeIf(짝수)          : [1, 3, 5]
List.of 에 removeIf      : UnsupportedOperationException
List.of 에 removeIf(아무것도 안 걸림) : UnsupportedOperationException
Arrays.asList 에 removeIf : UnsupportedOperationException: remove
Arrays.asList 에 removeIf(아무것도 안 걸림) : OK
```

```text
   조건에 걸리는 원소가 있나?

   List.of         있다 -> UOE        없다 -> UOE      <- 항상 던진다
   Arrays.asList   있다 -> UOE        없다 -> OK       <- 데이터에 따라 갈린다
```

- ★ **`Arrays.asList.removeIf` 는 데이터에 따라 터진다.**\
  조건에 걸리는 원소가 없으면 조용히 통과하고, 하나라도 걸리면 `UnsupportedOperationException: remove` 다.
- 테스트 데이터로는 안 터지고 운영에서 터지는 전형적인 모양이다.
- 메시지 `remove` 는 `Iterator.remove()` 의 기본 구현이 던지는 것이다 —
  `Collection.removeIf` 기본 구현이 이터레이터를 쓰기 때문이다([`../43-iterator-and-fail-fast/`](../43-iterator-and-fail-fast/)).

### `remove(int)` 와 `remove(Object)`

**실행 결과** (`Ex.java` — 40-b, 17·21·25 동일)

```text
--- 5) remove(int) 와 remove(Object)
remove(1) 후         : [10, 30]   <- 인덱스 1 이 지워졌다
remove(Integer(20)) 후 : [10, 30]
remove(100) 은?      : IndexOutOfBoundsException: Index 100 out of bounds for length 3
```

```java
List<Integer> l = new ArrayList<>(List.of(10, 20, 30));
l.remove(1);                     // 인덱스 1 -> [10, 30]
l.remove(Integer.valueOf(20));   // 값 20   -> [10, 30]
l.remove(100);                   // IndexOutOfBoundsException — 값 100 을 찾는 게 아니다
```

- **`List<Integer>` 에서만 생기는 함정**이다. `remove(int)` 오버로드가 이긴다.
- 오버로딩 해소가 왜 그렇게 되는지는 [`../08-method-declaration-overloading/`](../08-method-declaration-overloading/) 가 정본이다.

### `Set` 의 집합 연산

**실행 결과** (`Ex.java` — 40-b, 17·21·25 동일)

```text
--- 7) Set 의 집합 연산
합집합 addAll    : [a, b, c, d]
교집합 retainAll : [b, c]
차집합 removeAll : [a]
```

```java
Set<String> u = new LinkedHashSet<>(s); u.addAll(other);     // 합집합
Set<String> i = new LinkedHashSet<>(s); i.retainAll(other);  // 교집합
Set<String> d = new LinkedHashSet<>(s); d.removeAll(other);  // 차집합
```

- 셋 다 **원본을 고친다.** 그래서 복사부터 하는 것이 관용구다.
- `LinkedHashSet` 을 쓰면 결과의 순서가 재현된다.

## 어디서 틀리나

### 1. "불변으로 돌려줬다"고 믿는 getter

```java
private final List<String> items = new ArrayList<>();
public List<String> getItems() { return Collections.unmodifiableList(items); }
```

- 호출자는 못 고친다. **하지만 내가 `items.add(...)` 하면 호출자가 들고 있던 것도 바뀐다.**
- 호출자가 그 리스트를 스냅샷으로 믿고 순회하면 `ConcurrentModificationException` 까지 날 수 있다.
- 방어: 스냅샷이 필요하면 **`List.copyOf(items)`**. 뷰가 의도라면 그렇다고 문서에 적는다.

### 2. `List.of` 에 `null` 이 섞일 수 있는 값을 넣는다

```java
List<String> l = List.of(dto.getName(), dto.getEmail());   // 하나라도 null 이면 NPE
```

- **생성 시점에** `NullPointerException` 이 난다. 메시지가 없다.
- 방어: `Arrays.asList` 를 쓰거나, `Stream.of(...).filter(Objects::nonNull).toList()`.
- 애초에 `null` 을 안 만드는 쪽이 낫다([`../60-null-handling/`](../60-null-handling/)).

### 3. `Arrays.asList` 로 만든 것에 `add` 한다

```java
List<String> l = Arrays.asList("a", "b");
l.add("c");        // UnsupportedOperationException
```

- **가장 오래된 함정**이다. "리스트를 만들었다"고 읽히는데 배열 뷰다.
- `set` 은 되니까 더 헷갈린다.
- 방어: 고칠 거면 `new ArrayList<>(Arrays.asList(...))`, 아니면 `List.of(...)`.

### 4. `Arrays.asList` 에 기본형 배열을 넘긴다

```java
int[] arr = {1, 2, 3};
List<int[]> l = Arrays.asList(arr);     // 크기 1 짜리 리스트가 된다
```

**실행 결과** (`Ex.java` — 40-d, 17·21·25 동일)

```text
--- 1) 기본형 배열을 Arrays.asList 에 넣으면
Arrays.asList(int[]) 크기 : 1 / 원소 0 의 타입 int[]
Arrays.asList(String[]) 크기 : 3
올바른 길 : [1, 2, 3]
```

- `int[]` 는 `Object` 하나로 취급되므로 **원소가 하나인 리스트**가 나온다.
- 방어: `Arrays.stream(arr).boxed().toList()`([`../44-stream-creation/`](../44-stream-creation/)).

### 5. `subList` 결과를 오래 들고 있는다

```java
List<Row> page = all.subList(0, 20);
cache.put(key, page);        // all 전체가 메모리에 붙잡힌다
all.add(newRow);             // 이후 page 를 읽으면 ConcurrentModificationException
```

- 뷰는 **원본 전체를 붙잡는다.** 20개를 위해 백만 개가 살아 있는다.
- 원본이 구조적으로 바뀌면 **읽기만 해도 죽는다.**
- 방어: 경계를 넘길 때 복사한다 — `List.copyOf(all.subList(0, 20))`.

### 6. `Set.of` 의 순회 순서를 로그·테스트에 적는다

```java
assertEquals("[a, b, c, d, e]", Set.of("a","b","c","d","e").toString());   // 실행마다 다르다
```

- ★ **같은 JVM·같은 코드인데 실행할 때마다 다르다.** (6)의 세 번 실행 결과가 그것이다.
- 방어: 순서가 필요하면 `List.of`. 비교가 필요하면 `Set` 끼리 `equals` 로 비교한다(순서 무관).

### 7. 가변 객체를 `Set`·`Map` 키로 쓴다

- 넣고 나서 필드를 바꾸면 **`contains` 도 `remove` 도 실패**한다. 원소는 남아 있다.
- 방어: 키는 불변으로. `record` 로 만들되 **안에 가변 필드(배열·리스트)를 두지 않는다**([**59번 주제**](../59-immutable-objects/)).

### 8. `Arrays.asList(...).removeIf(...)` 가 가끔만 터진다

- (문법 절에서 본 것) **조건에 걸리는 원소가 하나라도 있을 때만** 던진다.
- 테스트에서 통과하고 운영에서 터지는 모양이다.
- 방어: `Arrays.asList` 결과에는 **읽기만** 한다.

## 구현 세부사항 대 언어 보장

| 관측한 것 | 보장인가 | 근거 |
|---|---|---|
| `List.of(null)` 이 NPE | **보장** | `List` javadoc 「Unmodifiable Lists」 — "They disallow `null` elements" |
| `List.of` 가 `add` 에 UOE | **보장** | 같은 절 — "Calling any mutator method on the List will always cause `UnsupportedOperationException`" |
| `Set.of("a","a")` 가 `IllegalArgumentException` | **보장** | `Set.of` javadoc — 중복 원소는 `IllegalArgumentException` |
| 그 메시지가 `duplicate element: a` | **보장 아님** | 구현의 문자열이다 |
| `Arrays.asList` 가 배열의 뷰 | **보장** | `Arrays.asList` javadoc — "Returns a fixed-size list backed by the specified array" |
| `Collections.unmodifiableList` 가 뷰 | **보장** | `Collection` javadoc 「Unmodifiable View Collections」 |
| `subList` 가 뷰 | **보장** | `List.subList` javadoc — "backed by this list" |
| 원본을 구조적으로 고친 뒤 `subList` 가 **CME** | **보장 아님** | javadoc 은 "semantics ... become undefined" 까지만. CME 는 `ArrayList` 의 호의다 |
| `Set.of` 의 순회 순서가 **실행마다 다름** | **사실상 보장** | `Set.of` javadoc — "iteration order ... is unspecified and is subject to change". 소스의 `SALT32L` 주석이 의도를 밝힌다 |
| `HashSet` 의 순회 순서가 실행마다 같음 | **보장 아님** | `HashSet` javadoc 이 순서를 약속하지 않는다 |
| `List.copyOf(List.of(..))` 가 같은 인스턴스 | **보장 아님** | 최적화다. javadoc 은 "Factories are free to create new instances or reuse existing ones" |
| 구체 타입 `ImmutableCollections$List12` 등 | **보장 아님** | 문서화되지 않은 내부 클래스 |
| `Arrays.asList(...).removeIf` 가 조건에 따라 갈림 | **보장 아님** | `Collection` javadoc 이 양쪽을 다 허용한다(39번 (8)) |

**세 JDK 실측** — 프로그램 2개를 17.0.13 · 21.0.5 · 25.0.1 에서 돌려 `diff` 했다.

```text
40-a · 40-b : 세 버전 출력이 한 글자도 같다 (스택트레이스를 찍지 않는 프로그램이라 줄 번호 차이도 없다)

40-c        : 같은 JVM(21.0.5) 을 세 번 띄웠더니 Set.of 의 순서가 세 번 다 달랐다
              -> "여러 버전에서 같았다"보다 "한 버전에서도 다르다"가 더 강한 근거다
```

- ★ **세 버전 비교가 답을 못 주는 축이 있다.** `Set.of` 의 순서는 **버전이 아니라 실행마다** 다르다.\
  버전만 바꿔 가며 돌렸다면 "세 번 다 같았다"는 잘못된 안심을 얻었을 수도 있다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 일 | 고를 것 |
|---|---|
| 상수 목록·집합·맵 선언 | **`List.of` / `Set.of` / `Map.of`** — 기본 선택 |
| 받은 컬렉션을 필드에 보관 | **`List.copyOf(받은것)`** — 그 순간에 얼린다 |
| 필드를 getter 로 노출 | **`List.copyOf(items)`**. 뷰가 의도면 `unmodifiableList` + 문서 |
| 고칠 리스트가 필요하다 | `new ArrayList<>(...)` |
| `null` 이 섞일 수 있다 | `Arrays.asList` 또는 `new ArrayList<>(Arrays.asList(...))`. **`of` 계열은 못 쓴다** |
| 배열을 잠깐 리스트로 읽는다 | `Arrays.asList(arr)` — **읽기만** |
| 배열을 리스트로 바꿔 고친다 | `new ArrayList<>(Arrays.asList(arr))` |
| 리스트의 일부를 넘긴다 | **`List.copyOf(l.subList(a, b))`** — 뷰를 넘기지 않는다 |
| 구간을 지운다 | `l.subList(a, b).clear()` — 이때는 뷰가 이득이다 |
| 조건으로 지운다 | **`removeIf`** — 순회하며 지우지 않는다(43번) |
| 중복 제거 + 순서 유지 | `new LinkedHashSet<>(c)` |
| 집합 연산 | 복사한 뒤 `addAll`/`retainAll`/`removeAll` |
| 스트림에서 불변 리스트로 | `stream.toList()`(16+) 또는 `collect(toUnmodifiableList())`([`../47-collectors-basics/`](../47-collectors-basics/)) |

판단 규칙 세 줄.

- **세 축을 따로 묻는다** — 고칠 수 있나 · `null` 을 받나 · **원본이 비치나**.
- **경계를 넘길 때는 복사한다.** `copyOf` 는 이미 불변이면 공짜다.
- **`Arrays.asList` 는 읽기 전용으로만.** `set` 이 된다는 사실이 함정이다.

## 핵심 문장

- **"불변"과 "수정 불가 뷰"는 다른 것이다.** `List.of` 는 사진이고 `Collections.unmodifiableList` 는 창문이다 — 창문은 원본이 바뀌면 같이 바뀐다.
- 세 팩토리는 **세 축**으로 갈린다 — `null` 허용(`of` 계열만 금지)·변경 가능성(`Arrays.asList` 는 `set` 만 허용)·원본 반영(`unmodifiableList`·`Arrays.asList`·`subList` 만 비친다).
- **`subList` 는 뷰다.** 원본을 구조적으로 고치면 그 뷰의 의미가 **정의되지 않는다** — `ConcurrentModificationException` 은 계약이 아니라 호의다.
- ★ **`Set.of`·`Map.of` 의 순회 순서는 JVM 을 다시 띄울 때마다 바뀐다.** 순서에 기대는 코드를 일찍 깨뜨리려고 일부러 그렇게 만들었다.
- `Set`·`Map` 의 키를 넣은 뒤에 고치면 **원소는 남는데 못 찾게 된다** — `contains` 도 `remove` 도 실패하고 순회에만 보인다.

## 관련 자료

- [`../39-collections-framework-map/`](../39-collections-framework-map/) — **이 주제의 선행.** 그쪽은 **옵셔널 연산이 왜 존재하나**까지, 여기는 **그래서 어느 팩토리를 고르나**부터
- [`../41-map-api-merge-compute/`](../41-map-api-merge-compute/) — `Map` 쪽 팩토리와 뷰. **`Map.of`·`entrySet` 은 그쪽이 정본**
- [`../42-sequenced-collections/`](../42-sequenced-collections/) — `reversed()` 도 뷰다. **뷰 목록의 21년 추가분은 그쪽**
- [`../43-iterator-and-fail-fast/`](../43-iterator-and-fail-fast/) — `removeIf` 가 내부에서 무엇을 쓰나, 순회 중 삭제. **`ConcurrentModificationException` 의 정본**
- [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) — **`Set` 이 원소에 요구하는 계약의 정본.**\
  그쪽은 **다섯 조항과 위반 증상**까지, 여기는 **가변 키를 넣으면 관측되는 것**만
- [`../28-comparable-comparator/`](../28-comparable-comparator/) — `TreeSet` 이 요구하는 다른 계약
- [`../14-records/`](../14-records/) — `Set`·`Map` 키로 쓰기 좋은 타입을 만드는 법
- [`../08-method-declaration-overloading/`](../08-method-declaration-overloading/) — `remove(int)` 와 `remove(Object)` 의 해소가 왜 그렇게 되나
- [`../44-stream-creation/`](../44-stream-creation/) — 기본형 배열을 리스트로 바꾸는 올바른 길
- [`../47-collectors-basics/`](../47-collectors-basics/) — `toList`·`toUnmodifiableList` 의 같은 세 축. **스트림 쪽은 그쪽이 정본**
- [`../60-null-handling/`](../60-null-handling/) — `of` 계열이 `null` 을 거부하는 것을 방어로 쓰는 법
- [`../../../../../data-structure/01-dynamic-array/`](../../../../../data-structure/01-dynamic-array/) — **동적 배열 자료구조의 정본.**\
  그쪽은 **왜 2배씩 늘리나·상각 분석**까지, 여기는 **`ArrayList` 를 어느 팩토리로 만드나**부터
- [`../../../../../data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/) — `HashSet` 이 원소를 어느 칸에 두나. **해시 원리는 그쪽**
- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 40번)
- [`../59-immutable-objects/`](../59-immutable-objects/)(불변 객체 만들기) — 컬렉션 필드를 가진 클래스를 정말 불변으로 만드는 법
- [`../05-arrays/`](../05-arrays/)(배열) — `Arrays.asList` 가 감싸는 그 배열의 언어 규칙

## 용어 풀이

- **불변(immutable)** — 만들어진 뒤 내용이 절대 안 바뀌는 것. `List.of` 가 그렇다.
- **수정 불가(unmodifiable)** — 고치는 메서드가 `UnsupportedOperationException` 을 던지는 것. 불변보다 약한 말이다.
- **수정 불가 뷰(unmodifiable view)** — 수정 불가이면서 뒤에 원본이 있는 것. `Collections.unmodifiableList` 가 그렇다.
- **뷰(view)** — 원소를 직접 저장하지 않고 뒤에 있는 것에 위임하는 컬렉션. `subList`·`Arrays.asList`·`entrySet`·`reversed`.
- **구조적 수정(structural modification)** — 크기를 바꾸는 변경. `set` 은 해당 없음, `add`·`remove`·`clear` 는 해당.
- **팩토리 메서드(static factory)** — 생성자 대신 객체를 만들어 돌려주는 정적 메서드. `List.of`·`List.copyOf`.
- **`UnsupportedOperationException`** — 그 구현체가 그 연산을 지원하지 않을 때의 런타임 예외.
- **`IllegalArgumentException`** — 인자가 잘못됐을 때의 예외. `Set.of` 의 중복 원소가 이것이다.
- **SALT** — `ImmutableCollections` 가 JVM 시작 시 한 번 정하는 값. `Set.of`·`Map.of` 의 순회 순서를 실행마다 흔든다.
- **방어적 복사(defensive copy)** — 경계를 넘을 때 컬렉션을 복사해 내부 상태가 새지 않게 하는 것.

## 더 들어가면

- **`List.of` 의 구체 타입이 원소 수로 갈린다.**\
  1~2개면 `List12`(필드 두 개), 3개 이상이면 `ListN`(배열). 작은 리스트가 흔해서 전용 클래스를 둔 것이다.\
  `List.of()` 는 `ListN` 인데 **빈 배열을 공유**한다.
- **`SALT32L` 은 `System.nanoTime()` 으로 만든다.**\
  다만 `-Xshare:dump`(CDS 아카이브 생성) 중에는 JVM 빌드에서 유도한 고정 시드를 쓴다 —
  같은 JDK 빌드로 같은 아카이브가 나오게 하기 위해서다. 소스 주석에 그렇게 적혀 있다.
- **`Collections.unmodifiableList` 는 `RandomAccess` 여부로 두 클래스를 고른다.**

  ```text
  --- 2) unmodifiableList 의 타입은 RandomAccess 여부로 갈린다   (Ex.java — 40-d)
  ArrayList 를 감싸면  : java.util.Collections$UnmodifiableRandomAccessList
  LinkedList 를 감싸면 : java.util.Collections$UnmodifiableList
  ```
- **`Arrays.asList` 는 가변 인자다.** `Arrays.asList(arr)` 에서 `arr` 이 `String[]` 이면 원소 3개짜리,
  `int[]` 이면 원소 1개짜리가 나온다. **가변 인자 해소가 참조형 배열에만 펼쳐지기 때문**이다.
- **`Set.of` 가 던지는 중복 검사는 `equals` 기준이다.**

  ```text
  --- 3) Set.of 의 중복 판정 기준   (Ex.java — 40-d)
  equals 재정의한 Box 둘 : IllegalArgumentException: duplicate element: Box(1)
  재정의 안 한 Plain 둘  : 2
  ```

  같은 값인데 `equals` 를 재정의하지 않으면 **둘 다 들어간다.**\
  즉 [**27번 주제**](../27-equals-hashcode-contract/)의 계약이 여기서도 판정 기준이다.
- **불변 컬렉션은 value-based 다.**\
  javadoc 이 "Programmers should treat instances that are equal as interchangeable and should not use them for synchronization" 라고 적는다.\
  `synchronized (List.of("a"))` 는 쓰지 않는다 — 나중 릴리스에서 인스턴스가 공유될 수 있다.
