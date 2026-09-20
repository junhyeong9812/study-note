# java/syntax/44 — `Stream` 생성: 소스별·기본형 스트림 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **Temurin JDK 21.0.5 에서 실제로 돌려 얻은 것**이다.\
> javadoc 인용은 [Java SE 21 `java.util.stream` 패키지 문서](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/package-summary.html) 원문이다.\
> 17.0.13 · 25.0.1 에서도 같은 프로그램을 돌려 출력이 동일함을 확인했다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 이 세 줄의 `count()` 를 예측하라

**실행 결과** (`Traps.java`)

```text
Stream.of(int[])      count = 1
Stream.of(Integer[])  count = 3
Arrays.stream(int[])  count = 3
```

**세 줄의 답**

- `Stream.of(ints).count()` -> **1**
- `Stream.of(boxed).count()` -> **3**
- `Arrays.stream(ints).count()` -> **3**

**첫 줄의 타입과 원소**

- 타입은 **`Stream<int[]>`**.
- 원소는 **배열 객체 그 자체 하나**다. `1`·`2`·`3` 이 아니다.

**왜 `Stream.of(int[])` 만 다른가**

```text
Stream.of 의 시그니처:  static <T> Stream<T> of(T... values)

  Integer[] 를 넘기면                     int[] 를 넘기면
    T = Integer 로 맞는다                   T 가 int 일 수 없다
    values = 그 배열 자체                    (제네릭 타입 인자는 참조 타입만)
    -> 원소 3개                                  |
                                                 v
                                            T = int[] 로 추론
                                            values = new int[][]{ ints }
                                            -> 원소 1개 (배열 하나)
```

- 가변 인자는 "배열을 그대로 쓸지, 한 원소로 감쌀지"를 **타입으로 결정**한다.
- `T` 는 참조 타입만 될 수 있어서([**19번 주제**](../19-type-erasure/) — 타입 소거) `int` 를 받을 수 없다.
- 그래서 컴파일러가 **`int[]` 하나를 원소로 감싸는 쪽**을 고른다.
- `Arrays.stream` 은 `int[]`·`long[]`·`double[]` 전용 오버로드를 따로 갖고 있어 이 문제가 없다.

**컴파일 경고가 나는가**

- **안 난다.** `Stream<int[]>` 는 완벽히 정상인 타입이다.
- 그래서 **컴파일·실행 모두 성공하고 결과만 틀린다** — 조용한 실패다.
- 뒤에 `.mapToInt(...)` 를 붙이면 컴파일 에러로 드러나기도 하지만, `.forEach(System.out::println)` 이면 배열의 `toString`(`[I@1b6d3586` 같은 것)이 조용히 찍힌다.

> **가변 인자(varargs)** — `T...` 형태의 매개변수. 인자 여러 개를 배열로 모아 받는다.\
> 예: `Stream.of("a","b")` 는 `new String[]{"a","b"}` 로 바뀌어 전달된다.

### 2. 이 코드는 무엇을 출력하는가

**실행 결과** (`Traps.java`)

```text
-- 최종 연산 없음 --
-- 최종 연산 있음 --
-- count() 는 peek 를 건너뛸 수 있다 (위 출력 확인) --
-- toList() 로 --
  peek a
  peek b
```

**몇 줄이 출력되는가**

- **0 줄.** 아무것도 출력되지 않는다.

**javadoc 의 근거 문장**

> Intermediate operations return a new stream. They are always *lazy*; executing an intermediate operation such as `filter()` does not actually perform any filtering, but instead creates a new stream that, when traversed, contains the elements of the initial stream that match the given predicate. **Traversal of the pipeline source does not begin until the terminal operation of the pipeline is executed.**

- 마지막 문장이 근거다 — **최종 연산이 실행될 때까지 소스 순회가 시작되지 않는다.**

**`.toList()` 를 붙이면**

- **2 줄** (`peek a`, `peek b`).
- 리스트를 만들려면 원소가 실제로 필요하다.

**`.count()` 를 붙이면**

- **0 줄.** 최종 연산이 있는데도 안 찍힌다.

**`.count()` 의 근거**

> The eliding of side-effects may also be surprising. With the exception of terminal operations `forEach` and `forEachOrdered`, **side-effects of behavioral parameters may not always be executed when the stream implementation can optimize away the execution of behavioral parameters without affecting the result of the computation.**

```text
toList()                                 count()
  개수만으로는 답을 못 낸다                 소스가 크기를 안다 (Stream.of 는 SIZED)
  원소를 하나씩 흘려보내야 한다              peek 를 통과시켜도 답이 안 바뀐다
        |                                        |
  peek 2회                                 peek 0회 — 통째로 생략
```

- **중간 연산의 부작용은 실행이 보장되지 않는다.**
- 함의 둘.
  1. `peek` 로 디버깅할 때 **안 찍히는 것이 "파이프라인이 안 돌았다"의 증거가 못 된다.**
  2. **중간 연산에 로깅·카운팅·저장을 넣으면 안 된다.** 최종 연산이 무엇이냐에 따라 횟수가 달라진다.

### 3. 스트림을 두 번 쓰면

**실행 결과** (`Traps.java`)

```text
첫 소비 : 2
두 번째 : IllegalStateException - stream has already been operated upon or closed
```

**두 줄**

- 첫 줄 -> **`2`**
- 둘째 줄 -> **`IllegalStateException`**

**예외 메시지**

- `stream has already been operated upon or closed`

**같은 원소를 다시 보려면**

- **소스를 들고 있다가 `stream()` 을 다시 부른다.**

```java
List<String> src = List.of("a", "b");
src.stream().count();     // 2
src.stream().count();     // 2  — 새 스트림
```

- javadoc: "The elements of a stream are only visited once during the life of a stream. **Like an `Iterator`, a new stream must be generated to revisit the same elements of the source.**"
- 값을 두 번 써야 하면 **한 번 수집해서 리스트로** 만든 뒤 그 리스트를 쓴다.

**필드·반환값으로 들고 다니면 왜 위험한가**

```text
List 를 돌려주는 메서드                      Stream 을 돌려주는 메서드
+-----------------------------+            +-----------------------------+
| 호출자가 몇 번이든 순회 가능   |            | 호출자가 한 번만 쓸 수 있다    |
| 호출자가 size() 를 물어봄      |            | 두 번째 호출자가 터진다        |
| 계약이 명확하다               |            | "이미 썼는지" 가 숨은 상태다    |
+-----------------------------+            +-----------------------------+
```

- 스트림에는 **"이미 소비됨"이라는 숨은 상태**가 있다.
- 그 상태가 타입에 안 드러나므로, 두 곳에서 같은 스트림을 받으면 **뒤에 받은 쪽이 런타임에 터진다.**
- API 경계에서는 `Stream` 보다 `List`·`Collection` 을 돌려주는 편이 안전하다.\
  단 결과가 아주 크거나 무한할 수 있으면 `Stream` 을 돌려주고 **"한 번만 쓸 수 있다"를 문서에 적는다.**

### 4. 만든 뒤 소스를 고치면

**실행 결과** (`Traps.java`)

```text
스트림 만든 뒤 add 하고 소비 : [a, b, c]
```

**출력**

- **`[a, b, c]`** — `"c"` 가 들어 있다.

**스트림은 소스를 복사해 두는가**

- **아니다.** 소스를 가리킬 뿐이다.

```text
  t1  mut.stream()      스트림이 mut 를 가리킨다. 원소는 하나도 안 읽었다
  t2  mut.add("c")      리스트가 [a, b, c] 가 된다
  t3  st.toList()       ★ 여기서 비로소 읽기 시작 -> [a, b, c]
```

- 지연 평가의 직접적 귀결이다 — **읽는 시점이 `t3` 이므로 `t3` 의 내용을 본다.**
- javadoc 은 이 성질을 대부분의 소스에 대해 "late-binding" 이라 부른다.

**소비가 시작된 뒤에 고치면**

- **`ConcurrentModificationException`** 이 날 수 있다.
- "날 수 있다"이지 "난다"가 아니다 — fail-fast 는 최선 노력 보장이다.
- 그 규칙은 [**43번 주제**](../43-iterator-and-fail-fast/)(`Iterator`·fail-fast)가 정본이다.
- 방어: **스트림을 변수에 담지 않고 만든 자리에서 바로 소비한다.**\
  `mut.stream().filter(...).toList()` 처럼 한 문장이면 사이에 끼어들 자리가 없다.

### 5. 기본형 스트림에만 있는 것

**실행 결과** (`Prim.java`)

```text
IntStream.sum()       : 14
IntStream.average()   : 2.8
IntStream.max()       : 5
summaryStatistics     : IntSummaryStatistics{count=5, sum=14, min=1, average=2.800000, max=5}
Stream<Integer> 합계   : 14
reduce 로 합계        : 14
boxed()               : [3, 1, 4, 1, 5]
mapToObj              : [#3, #1, #4, #1, #5]
asLongStream          : 14
asDoubleStream avg    : 2.8
mapToInt from String  : 6
빈 IntStream.sum()    : 0
빈 IntStream.max()    : OptionalInt.empty
빈 IntStream.average(): OptionalDouble.empty
```

**`Arrays.stream(nums).sum()`**

- **14** (`3+1+4+1+5`).

**`Stream<Integer>` 에 `sum()` 이 없는 이유**

- `Stream<T>` 는 **`T` 가 무엇인지 모른다.** `T` 가 `String` 일 수도 있다.
- "더한다"는 연산은 숫자에만 의미가 있으므로 **숫자 전용 타입에만** 둘 수 있다.
- 대신 쓰는 것 둘.

```java
boxed.stream().mapToInt(Integer::intValue).sum();   // 기본형 스트림으로 내려가서
boxed.stream().reduce(0, Integer::sum);             // 또는 reduce 로 직접
```

- `mapToInt` 쪽이 낫다 — 그 뒤로 `average()`·`summaryStatistics()` 까지 쓸 수 있고 박싱도 사라진다.

**빈 스트림의 `sum()` 과 `max()`**

- `IntStream.of().sum()` -> **`0`**
- `IntStream.of().max()` -> **`OptionalInt.empty`**
- `IntStream.of().average()` -> **`OptionalDouble.empty`**

**두 형태가 갈리는 이유**

```text
합                                        최댓값
+-------------------------------+        +-------------------------------+
| 빈 것의 합 = 0                 |        | 빈 것의 최댓값 = ???            |
| 0 은 덧셈의 항등원이다          |        | 항등원이 없다                   |
| "아무것도 안 더했다" = 0        |        | Integer.MIN_VALUE 를 주면       |
|                               |        | 진짜 그 값과 구분이 안 된다      |
| -> int 를 그대로 준다          |        | -> Optional 로 "없음"을 표현     |
+-------------------------------+        +-------------------------------+
```

- **항등원이 있으면 그 값을, 없으면 `Optional`.**\
  `count()` 가 `0` 을 주는 것도 같은 이유다.
- 그래서 `max().getAsInt()` 를 바로 부르면 빈 입력에서 `NoSuchElementException` 이 난다.\
  `orElse(...)` 나 `ifPresent(...)` 를 거친다([**38번 주제**](../38-optional/) `Optional`).

**`boxed()` 는 무엇을 부르는가**

```java
// JDK 21.0.5  java.base/java/util/stream/IntPipeline.java  232~234행 — 실제 소스 그대로
public final Stream<Integer> boxed() {
    return mapToObj(Integer::valueOf, 0);
}
```

- **`Integer::valueOf`** 를 부른다.
- 이것이 [`../01-primitives-and-wrappers/`](../01-primitives-and-wrappers/) 의 그 `valueOf` 다.\
  `-128`~`127` 구간은 캐시에서 나오고 그 위는 객체가 새로 생긴다.
- 함의: `IntStream` 으로 있는 동안은 **객체가 0개**, `boxed()` 를 부르는 순간 원소 수만큼 박싱이 일어난다.\
  그래서 `boxed()` 는 **꼭 필요한 자리에서 가장 늦게** 부른다.

### 6. `"abc".chars()`

**실행 결과** (`Sources.java`)

```text
14 String.chars       : [97, 98, 99]
15 String.chars->char : [a, b, c]
```

**`"abc".chars().boxed().toList()`**

- **`[97, 98, 99]`**

**왜 그런 값이 나오는가**

```text
"abc".chars() 의 반환 타입은 IntStream 이다 (Stream<Character> 가 아니다)

  'a'  'b'  'c'          문자
   |    |    |           char -> int 로 확장 (암묵적)
   v    v    v
  97   98   99           IntStream 의 원소

  boxed() -> Stream<Integer> -> toList() -> [97, 98, 99]
```

- `chars()` 가 `IntStream` 인 이유는 **`Stream<Character>` 였다면 문자마다 `Character` 객체가 생기기 때문**이다.\
  기본형 스트림을 둔 목적 그대로다.
- `boxed()` 는 `IntStream` 의 메서드라 `Integer` 로 감싼다. `Character` 로 바뀌지 않는다.

**`[a, b, c]` 를 얻으려면**

```java
"abc".chars().mapToObj(c -> (char) c).toList();
```

- **`mapToObj` 에서 `(char)` 캐스팅**을 해야 한다.
- `boxed()` 로는 안 된다 — `boxed()` 는 `Integer` 로만 간다.
- 문자열을 문자 단위로 다룰 일이 많으면 `split("")` 으로 `Stream<String>` 을 만드는 쪽이 읽기 쉽다.

### 7. 무한 스트림

**원소 개수**

- **무한**이다. 끝이 없다.

**`.toList()` 를 실행하면**

**실행 결과** (`Infinite.java`, `-Xmx64m` 으로 30초 제한을 걸고 실행)

```text
시작
Exception in thread "main" java.lang.OutOfMemoryError: Java heap space
	at java.base/java.lang.Integer.valueOf(Integer.java:1073)
	at Infinite.lambda$main$0(Infinite.java:5)
```

- 힙이 찰 때까지 돌다가 **`OutOfMemoryError`** 로 죽는다.
- 힙이 크면 죽는 데 더 오래 걸릴 뿐 결과는 같다 — **멈추지 않는다.**
- 스택트레이스에 `Integer.valueOf` 가 보인다 — 박싱이 힙을 채운 것이다(01번 주제).

**3인자 `Stream.iterate`**

```java
Stream.iterate(1, i -> i < 20, i -> i * 2)     // [1, 2, 4, 8, 16]
```

- **가운데 인자가 종료 조건**(`hasNext`)이다. `for(int i=1; i<20; i*=2)` 와 같은 모양이다.
- **Java 9** 부터.
- 이점: `limit` 를 잊을 수 없다. 조건이 **소스 안에** 있다.
- 2인자 형태 + `limit(5)` 와 결과가 같았다(`Sources.java` 8번과 9번 줄이 둘 다 `[1, 2, 4, 8, 16]`).\
  다른 점은 **끝을 개수로 정하느냐 조건으로 정하느냐**다.

**무한 스트림을 끝내는 연산의 종류**

- **단락 평가(short-circuiting) 연산**이다.

javadoc 원문:

> An intermediate operation is short-circuiting if, when presented with infinite input, it may produce a finite stream as a result. A terminal operation is short-circuiting if, when presented with infinite input, it may terminate in finite time.

| 중간 | `limit` · `takeWhile`(9+) |
|---|---|
| 최종 | `findFirst` · `findAny` · `anyMatch` · `allMatch` · `noneMatch` |

**`sorted()` 가 무한 스트림에 특히 위험한 이유**

```text
filter — 원소 하나씩 판정                   sorted — 전부 모아야 한다
  [1] -> 통과/버림 -> 다음                    [1][2][4]... 을 전부 버퍼에 쌓고
  메모리가 안 쌓인다                           다 쌓인 뒤에야 정렬해서 내보낸다
  무한이어도 앞쪽은 흘러간다                    무한이면 영원히 안 끝난다
```

- `sorted()`·`distinct()` 는 **상태 있는 중간 연산**이다.\
  `sorted()` 는 전부를 봐야 첫 원소를 낼 수 있다.
- 그래서 `Stream.iterate(...).sorted().limit(5)` 는 **`limit` 이 있어도 안 끝난다.**\
  실행 결과 (`SortedInf.java`, `-Xmx64m`):

  ```text
  limit 를 sorted 앞에: [1, 2, 3, 4, 5]
  이제 sorted 를 앞에 둔다
  Exception in thread "main" java.lang.OutOfMemoryError: Java heap space
  	at java.base/java.util.Arrays.copyOf(Arrays.java:3513)
  	at java.base/java.util.ArrayList.grow(ArrayList.java:237)
  ```

  스택트레이스가 `ArrayList.grow` 를 가리킨다 — **`sorted` 가 원소를 버퍼에 쌓다가 죽은 것**이다.
- 순서가 중요하다 — `limit` 를 **`sorted` 앞에** 둬야 한다.
- `distinct()` 는 조금 다르다: 무한이어도 새 값이 계속 나오면 하나씩 흘려보낼 수 있지만, **본 값을 전부 기억**하므로 메모리가 무한히 는다.

### 8. 손에 든 것에서 소스를 고르기

**`int[]` 를 받았다**

- **`Arrays.stream(ints)`.**
- `IntStream` 이 나와 `sum()`·`average()` 를 바로 쓸 수 있고 박싱이 없다.
- `Stream.of(ints)` 는 1번의 함정이다.

**인덱스가 필요한 반복**

- **`IntStream.range(0, n)`.**

```java
IntStream.range(0, list.size())
         .mapToObj(i -> i + ": " + list.get(i))
         .forEach(System.out::println);
```

- 끝을 포함해야 하면 `rangeClosed`.
- 다만 인덱스가 정말 필요한 게 아니면 **그냥 `for` 를 쓰는 편**이 읽기 쉽다.

**`null` 일 수 있는 값 하나**

- **`Stream.ofNullable(x)`** — **Java 9** 부터.

```text
Stream.ofNullable(null)  ->  []
Stream.ofNullable("x")   ->  [x]
```

- `if (x != null)` 분기 없이 `flatMap(Stream::ofNullable)` 로 `null` 을 걸러 낼 수 있다(45번 주제).
- Java 8 이라면 `Optional.ofNullable(x).stream()` 도 9부터라, `x == null ? Stream.empty() : Stream.of(x)` 를 써야 한다.

**도중에 검사 예외를 던져야 한다**

- **스트림을 쓰지 않는다.**
- 람다가 구현하는 함수형 인터페이스(`Function`·`Predicate`)의 시그니처에 `throws` 가 없어서, **검사 예외를 그 안에서 던질 수 없다.**
- 억지로 쓰면 `try`-`catch` 로 감싸 `RuntimeException` 으로 포장하게 되는데, 그러면 **어느 원소에서 터졌는지**가 흐려지고 스택트레이스도 길어진다.
- 그런 코드는 `for` 가 낫다. `break`·`continue` 도 쓸 수 있다.

**`Stream.toList()` 와 `collect(Collectors.toList())`**

**실행 결과** (`Extra.java`)

```text
toList() 에 null : [x, null]
toList() 수정: UnsupportedOperationException
collect(toList()) 수정: 가능
collect(toList()) 타입 : java.util.ArrayList
toUnmodifiableList + null : NPE
```

| | `Stream.toList()` (16+) | `collect(Collectors.toList())` |
|---|---|---|
| 수정 | **불가** (`UnsupportedOperationException`) | 가능 |
| 구체 타입 | 구현 세부 (보장 없음) | 실측 `java.util.ArrayList` (보장은 아님) |
| `null` 원소 | **허용** | 허용 |

- 셋째 줄이 중요하다 — **`Collectors.toUnmodifiableList()` 는 `null` 에서 NPE 를 던진다.**\
  `Stream.toList()` 와 "불변"의 뜻이 다르다.
- 기본은 **`toList()`**. 반환 후 수정이 필요하면 `collect(Collectors.toCollection(ArrayList::new))`.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Sources` | 18가지 소스 팩토리의 실제 출력 | 21 |
| `Traps` | `Stream.of(int[])`, 재사용 예외, 지연 평가, `count()` 의 `peek` 생략, late-binding | 21 |
| `Prim` | 기본형 스트림 전용 연산, 빈 스트림의 `sum`/`max`/`average` | 21 |
| `Extra` | `toList()` vs `collect(toList())`, `toUnmodifiableList` 의 NPE, `Random.ints` | 21 |
| `Infinite` | 무한 스트림 + `toList()` -> `OutOfMemoryError` (`-Xmx64m`) | 21 |
| `SortedInf` | `limit` 를 `sorted` 뒤에 두면 OOM, 앞에 두면 정상 | 21 |
| `src.zip` 열람 | `IntPipeline.boxed`, `Collection.stream` 의 기본 구현 | 21 |
