# java/syntax/44 — `Stream` 생성: 소스별·기본형 스트림 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [`java.util.stream` 패키지 javadoc (Java SE 21)](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/package-summary.html) · JDK 21.0.5 표준 라이브러리 소스 `java.base/java/util/stream/IntPipeline.java`(`lib/src.zip`)
> **실행 검증** — 이 문서의 모든 출력은 Temurin **JDK 21.0.5** 에서 실제로 돌려 얻은 것이다.\
> 같은 프로그램을 **17.0.13 · 25.0.1** 에서도 돌려 확인했다.
> **버전** — `Stream` 은 **Java 8**. `Stream.ofNullable` 과 3인자 `Stream.iterate` 는 **Java 9**.\
> `toList()`(중간 리스트 없이 바로 불변 리스트)는 **Java 16**. 17·21·25 동작 동일.
> **범위** — "무엇을 순회하고 무엇을 거르는가"라는 **알고리즘**은 [`../../../../../algorithm/`](../../../../../algorithm/) 이 정본이다.\
> 여기는 **API 표면과 평가 시점**만 다룬다.
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**스트림은 컨베이어 벨트이고, 소스는 그 벨트에 물건을 올려 주는 장치다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 벨트에 물건을 올려 주는 장치 | 소스 — `Collection.stream()`·`Arrays.stream`·`Stream.of`·`Stream.iterate` … |
| 벨트 위의 작업대 | 중간 연산 — `map`·`filter` … (45번 주제) |
| 벨트 끝의 시동 스위치 | 최종 연산 — `toList`·`sum`·`forEach` … (46번 주제) |
| 물건을 상자에 담아 올리기 | 박싱 — `Stream<Integer>` |
| 맨 물건 그대로 올리기 | 기본형 스트림 — `IntStream`·`LongStream`·`DoubleStream` |

- 장치를 벨트에 연결하고 작업대를 늘어놓아도 **벨트는 안 돈다.**\
  끝의 스위치를 눌러야 그제서야 물건이 하나씩 올라온다.
- 그래서 `stream().filter(...)` 만 써 놓으면 **아무 일도 안 일어난다.**\
  에러도 없다. 조용히 아무것도 안 한다.
- 벨트는 **한 번 돌면 끝**이다. 되감기가 없다.
- 그리고 물건을 상자에 담아 올릴지 맨 것으로 올릴지를 **장치가 정한다.**\
  `Arrays.stream(int[])` 은 맨 `int` 를, `Stream.of(Integer[])` 은 상자에 담긴 `Integer` 를 올린다.

```text
소스를 고르는 순간 정해지는 것

  int[] nums = {3, 1, 4};

  Arrays.stream(nums)              Stream.of(nums)
       |                                |
       v                                v
  +----------------+              +------------------+
  |   IntStream    |              | Stream<int[]>    |
  | 원소: 3, 1, 4  |              | 원소: 배열 그 자체 |
  | 개수: 3        |              | 개수: 1           |
  | .sum() 가능    |              | .sum() 없음       |
  +----------------+              +------------------+
```

**똑같은 구조로** Java 가 이렇게 동작한다: 장치 = 소스 팩토리, 스위치 = 최종 연산, 상자 = 래퍼 객체.

실무에서 이게 터지는 자리는 **`Stream.of(배열)` 을 쓰고 원소가 하나뿐인 스트림을 받는 것**, 그리고 **최종 연산을 안 붙여 놓고 "왜 로그가 안 찍히지" 하는 것**이다.

> **스트림(stream)** — 원소의 **연속**을 한 번 흘려보내며 처리하는 파이프라인. 컬렉션과 달리 **값을 저장하지 않는다.**\
> 예: `list.stream()` 은 리스트를 복사하지 않는다. 리스트를 읽어 갈 통로를 만들 뿐이다.

> **지연 평가(lazy evaluation)** — 결과가 실제로 필요해질 때까지 계산을 미루는 것.\
> 예: `filter` 를 걸어 둬도 최종 연산을 부르기 전에는 조건 검사가 한 번도 실행되지 않는다.

> **최종 연산(terminal operation)** — 파이프라인을 실제로 돌리고 스트림을 끝내는 연산.\
> 예: `toList()`·`count()`·`forEach()`·`sum()`. 이걸 부른 뒤에는 그 스트림을 다시 못 쓴다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. 손에 든 것(컬렉션·배열·문자열·무한 규칙)에서 **어떤 팩토리로 스트림을 만드나.**
2. 그 선택이 **원소 타입과 쓸 수 있는 연산**을 어떻게 정하나.
3. 스트림은 **언제 실제로 도는가** — 만든 순간인가, 최종 연산 때인가.

## 동작 방식

### (1) 만들기만 해서는 아무 일도 안 일어난다

**언제 쓰나** — "로그를 넣었는데 안 찍힌다"를 만났을 때.

javadoc 원문이다.

> Intermediate operations return a new stream. They are always *lazy*; executing an intermediate operation such as `filter()` does not actually perform any filtering, but instead creates a new stream that, when traversed, contains the elements of the initial stream that match the given predicate. **Traversal of the pipeline source does not begin until the terminal operation of the pipeline is executed.**

**실행 결과** (`Traps.java`)

```text
-- 최종 연산 없음 --
-- 최종 연산 있음 --
-- count() 는 peek 를 건너뛸 수 있다 (위 출력 확인) --
-- toList() 로 --
  peek a
  peek b
```

```text
Stream.of("a","b").peek(print)                    ... .peek(print).toList()

  [a][b] --> (peek) --> ???                        [a][b] --> (peek) --> [수집]
                          |                                      |
                     스위치가 없다                            스위치가 있다
                          |                                      |
                   벨트가 안 돈다                            a, b 가 흘러간다
                   출력 0줄                                  출력 2줄
```

그림 해설 (한 단계씩):

- 첫 블록은 **한 줄도 출력되지 않았다.** `peek` 의 람다가 한 번도 안 불린 것이다.
- 세 번째 블록(`toList()`)에서야 `peek a`·`peek b` 가 나온다.
- 두 번째 블록(`count()`)도 **한 줄도 안 나왔다** — 최종 연산이 있는데도.\
  이유는 (4)에서 다룬다.

비용 — 최종 연산이 없으면 비용이 **0**이다. 대신 아무 일도 안 한다.

### (2) 소스가 원소 타입을 정한다

**언제 쓰나** — 컴파일은 되는데 원소 개수가 이상할 때.

**실행 결과** (`Traps.java`)

```text
Stream.of(int[])      count = 1
Stream.of(Integer[])  count = 3
Arrays.stream(int[])  count = 3
  합계 (IntStream)    = 6
```

```text
Stream.of 의 시그니처는  <T> Stream<T> of(T... values)

  int[] 를 넘기면                        Integer[] 를 넘기면
    T 가 int 일 수 없다                    T = Integer 로 맞는다
    (제네릭 타입 인자는 참조 타입만)          가변 인자가 배열을 펼친다
        |                                      |
        v                                      v
    T = int[] 로 추론된다                   원소 3개짜리 Stream<Integer>
    가변 인자 하나짜리로 본다
        |
        v
    원소 1개짜리 Stream<int[]>
```

그림 해설 (한 단계씩):

- `Stream.of` 는 **가변 인자**다. 배열을 넘기면 보통 "펼쳐서" 받는다.
- 그런데 `int[]` 는 **`T` 가 될 수 없다** — 제네릭 타입 인자는 참조 타입만 가능하기 때문이다([**19번 주제**](../19-type-erasure/)).
- 그래서 컴파일러는 "배열 하나를 원소로 받았다"로 해석한다.\
  **경고도 에러도 없다.** `count()` 가 `1` 이 되어서야 드러난다.
- `Arrays.stream(int[])` 은 **`IntStream` 전용 오버로드**가 있어 원소 3개가 제대로 나온다.

비용 — 틀린 쪽을 고르면 이후 모든 연산이 배열 한 개에 대해 돈다.\
`.map(x -> x * 2)` 가 컴파일 에러로 드러나기도 하지만, `.forEach(System.out::println)` 처럼 `Object` 를 받는 자리면 **조용히 배열 주소가 찍힌다.**

### (3) 기본형 스트림 — 상자에 담지 않는 벨트

**언제 쓰나** — 숫자를 다룰 때. `sum()`·`average()` 가 필요할 때.

```text
Stream<Integer>                          IntStream
+--------------------------------+       +--------------------------------+
| 원소 = Integer 객체             |       | 원소 = int 값                   |
| [상자3][상자1][상자4]            |       |  3      1      4               |
|                                |       |                                |
| sum() 없음                     |       | sum() average() max() 있음     |
| reduce(0, Integer::sum) 로     |       | summaryStatistics() 있음        |
| mapToInt(...).sum() 로          |       |                                |
|                                |       | boxed() 로 넘어갈 수 있다        |
+--------------------------------+       +--------------------------------+
        ^                                          |
        +------------------ boxed() ---------------+
        +--------------- mapToInt(...) ------------>
```

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

그림 해설 (한 단계씩):

- `sum()`·`average()`·`max()`·`summaryStatistics()` 는 **기본형 스트림에만** 있다.
- `Stream<Integer>` 로 합계를 내려면 `mapToInt(...).sum()` 이나 `reduce(0, Integer::sum)` 을 거쳐야 한다.
- 빈 스트림에서 `sum()` 은 **`0`** 을 주지만 `max()`·`average()` 는 **`Optional*.empty`** 를 준다.\
  합의 항등원은 0이지만 최댓값의 항등원은 없기 때문이다.
- `boxed()` 의 구현은 이렇다 — 여기서 **01번 주제의 `Integer` 캐시로 이어진다.**

```java
// JDK 21.0.5  java.base/java/util/stream/IntPipeline.java  232~234행 — 실제 소스 그대로
public final Stream<Integer> boxed() {
    return mapToObj(Integer::valueOf, 0);
}
```

비용 — `IntStream` 으로 있는 동안은 **래퍼 객체가 하나도 안 생긴다.**\
`boxed()` 를 부르는 순간 원소 수만큼 `Integer.valueOf` 가 불린다(`-128`~`127` 은 캐시).

### (4) 최종 연산이 중간 연산을 건너뛸 수 있다

**언제 쓰나** — `peek` 로 디버깅할 때, 그리고 중간 연산에 부작용을 넣었을 때.

**실행 결과** (`Traps.java` — 두 번째 블록)

```text
-- 최종 연산 있음 --
(아무것도 출력되지 않음)
```

- `Stream.of("a","b").peek(print).count()` 인데 **`peek` 가 한 번도 안 불렸다.**
- `count()` 는 "개수만" 필요하고, 소스가 크기를 알고 있으면 **원소를 흘려보낼 필요가 없다.**

javadoc 이 이 동작을 명시한다.

> The eliding of side-effects may also be surprising. With the exception of terminal operations `forEach` and `forEachOrdered`, **side-effects of behavioral parameters may not always be executed when the stream implementation can optimize away the execution of behavioral parameters without affecting the result of the computation.**

```text
toList()  — 원소가 실제로 필요하다          count() — 개수만 필요하다
  [a] -> peek -> 수집                        소스가 SIZED 라면
  [b] -> peek -> 수집                        "2" 를 바로 돌려준다
  peek 2회 실행                              peek 0회 실행
```

그림 해설 (한 단계씩):

- **중간 연산의 부작용은 실행이 보장되지 않는다.**
- 그래서 `peek` 로 "여기까지 왔나"를 확인할 때, **안 찍히는 것이 파이프라인이 안 돌았다는 증거가 못 된다.**
- 더 중요한 함의: **중간 연산에 로깅·카운팅·DB 쓰기를 넣으면 안 된다.**\
  최종 연산이 무엇이냐에 따라 실행 횟수가 달라진다.

비용 — 이득 쪽이다(불필요한 순회를 건너뛴다).\
대가는 **부작용의 실행 횟수가 계약이 아니라는 것**이다.

## 문법 — 형태와 규칙

직접 쓴 최소 예제다. 아래 출력은 전부 `Sources.java` 의 실행 결과다.

### 소스별 팩토리 지도

| 손에 든 것 | 쓰는 것 | 실행 결과 |
|---|---|---|
| 컬렉션 | `list.stream()` | `[a, b, c]` |
| 참조 배열 전체 | `Arrays.stream(arr)` | `[a, b, c]` |
| 참조 배열 일부 | `Arrays.stream(arr, 1, 3)` | `[b, c]` |
| 값 몇 개 | `Stream.of("a", "b")` | `[a, b]` |
| 없음 | `Stream.empty()` | `[]` |
| `null` 일 수 있는 값 하나 (9+) | `Stream.ofNullable(x)` | `null` -> `[]` / `"x"` -> `[x]` |
| 규칙으로 무한 생성 | `Stream.iterate(1, i -> i*2).limit(5)` | `[1, 2, 4, 8, 16]` |
| 규칙 + 종료 조건 (9+) | `Stream.iterate(1, i -> i<20, i -> i*2)` | `[1, 2, 4, 8, 16]` |
| 같은 값·난수 무한 | `Stream.generate(() -> "x").limit(3)` | `[x, x, x]` |
| 정수 범위 (끝 제외) | `IntStream.range(0, 5)` | `[0, 1, 2, 3, 4]` |
| 정수 범위 (끝 포함) | `IntStream.rangeClosed(0, 5)` | `[0, 1, 2, 3, 4, 5]` |
| `int` 값 몇 개 | `IntStream.of(3, 1, 2)` | `[3, 1, 2]` |
| `int[]` | `Arrays.stream(ints)` | `IntStream` |
| 문자열의 문자들 | `"abc".chars()` | `[97, 98, 99]` (`IntStream`!) |
| 문자열의 문자들 (char 로) | `"abc".chars().mapToObj(c -> (char) c)` | `[a, b, c]` |
| 구분자로 자른 문자열 | `Pattern.compile(",").splitAsStream("a,b,c")` | `[a, b, c]` |
| 맵 | `map.entrySet().stream()` | `[k=1]` |
| 스트림 둘 잇기 | `Stream.concat(s1, s2)` | `[a, b]` |

주의할 것 둘.

- **`"abc".chars()` 는 `IntStream`** 이다. 그대로 출력하면 `[97, 98, 99]` 가 나온다.
- **`Stream.iterate` 와 `generate` 는 무한**이다. `limit` 를 안 걸면 끝나지 않는다.\
  단 3인자 `iterate`(9+)는 종료 조건을 안에 갖는다.

### `Stream.of` vs `Arrays.stream`

```java
int[]     ints  = {1, 2, 3};
Integer[] boxed = {1, 2, 3};

Stream.of(ints)         // Stream<int[]>    원소 1개   <- 거의 항상 실수
Stream.of(boxed)        // Stream<Integer>  원소 3개
Arrays.stream(ints)     // IntStream        원소 3개   <- int[] 에는 이쪽
Arrays.stream(boxed)    // Stream<Integer>  원소 3개
```

규칙 한 줄: **기본형 배열이면 `Arrays.stream`, 그 밖에는 아무거나.**

### 스트림은 한 번만 쓴다

```text
Stream<String> once = Stream.of("a", "b");
once.count();     // 2
once.count();     // IllegalStateException
```

**실행 결과** (`Traps.java`)

```text
첫 소비 : 2
두 번째 : IllegalStateException - stream has already been operated upon or closed
```

- javadoc 이 이렇게 쓴다 — "The elements of a stream are only visited once during the life of a stream. Like an `Iterator`, a new stream must be generated to revisit the same elements of the source."
- 재사용이 필요하면 **소스를 들고 있다가 다시 `stream()`** 을 부른다.
- 스트림을 필드나 메서드 반환값으로 들고 다니면 이 함정을 만나기 쉽다.

## 어디서 틀리나

### 1. `Stream.of(기본형 배열)`

- 위 (2)에서 본 것이다. 원소가 **하나**가 된다.
- 컴파일 경고가 **없다.** `Stream<int[]>` 는 완벽히 정상인 타입이기 때문이다.
- 드러나는 지점이 늦다 — `count()` 나 최종 출력에서야 보인다.
- 방어: **기본형 배열에는 언제나 `Arrays.stream`.**

### 2. 최종 연산을 안 붙인다

```java
list.stream().filter(x -> x.isActive()).map(this::save);   // 아무 일도 안 일어난다
```

- 에러도 경고도 없다. **조용히 아무것도 안 한다.**
- `map` 안에서 저장을 하려던 의도라면 데이터가 그냥 안 들어간다.
- 정적 분석 도구(SpotBugs·IDE 인스펙션)가 "스트림 결과를 버렸다"로 잡아 주기도 하지만 언어가 막지는 않는다.
- 방어: **중간 연산에 부작용을 넣지 않는다.** 저장은 `forEach` 로 한다.

### 3. `peek` 가 안 찍힌다고 파이프라인이 안 돈 것은 아니다

- 위 (4)에서 본 것이다. `count()` 가 `peek` 를 통째로 건너뛰었다.
- 디버깅할 때 **최종 연산을 `toList()` 로 바꿔 놓고** 확인한다.
- 그리고 `peek` 를 운영 코드에 남기지 않는다 — 실행 횟수가 계약이 아니다.

### 4. 무한 스트림에 `limit` 를 안 건다

```java
Stream.iterate(1, i -> i * 2).toList();     // 끝나지 않는다
```

- `Stream.iterate` 2인자 형태와 `Stream.generate` 는 **무한**이다.
- 단락 평가(`findFirst`·`anyMatch`·`limit`)가 없으면 프로그램이 멈추지 않는다.
- `sorted()`·`count()` 처럼 **전부를 봐야 하는 연산**을 무한 스트림에 걸면 특히 위험하다.
- 방어: 무한 소스를 쓰면 **같은 문장 안에서 `limit` 나 3인자 `iterate`** 로 끝을 준다.

### 5. 소스를 소비 전에 고치면

**실행 결과** (`Traps.java`)

```text
스트림 만든 뒤 add 하고 소비 : [a, b, c]
```

```text
List<String> mut = new ArrayList<>(List.of("a", "b"));
Stream<String> st = mut.stream();      // (1) 스트림을 만든다
mut.add("c");                          // (2) 리스트에 추가
st.toList();                           // (3) 소비 -> [a, b, c]
```

- **스트림을 만든 시점이 아니라 소비 시점의 내용**이 흘러간다.
- 스트림은 원소를 **복사해 두지 않는다.** 소스를 가리킬 뿐이다.
- 반대로 **소비가 시작된 뒤에** 소스를 고치면 `ConcurrentModificationException` 이 날 수 있다.\
  그 규칙(fail-fast)은 [**43번 주제**](../43-iterator-and-fail-fast/)가 정본이다.
- 방어: 스트림을 변수에 담아 들고 다니지 않는다. **만든 자리에서 바로 소비**한다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 |
|---|---|
| `int[]`·`long[]`·`double[]` | `Arrays.stream(arr)` — 기본형 스트림이 나온다 |
| 인덱스가 필요한 반복 | `IntStream.range(0, n)` — 그 뒤 `mapToObj` |
| 숫자 집계(합·평균·최대) | 기본형 스트림. `Stream<Integer>` 면 `mapToInt` 부터 |
| `null` 일 수 있는 단일 값 | `Stream.ofNullable(x)` (9+) — `if` 없이 이어진다 |
| 규칙으로 만드는 유한 수열 | 3인자 `Stream.iterate`(9+) — `limit` 를 잊을 일이 없다 |
| 난수·상수 무한 | `Stream.generate` + 반드시 `limit` |
| 단순 반복 한 번 | **스트림을 안 쓴다.** `for` 가 더 읽기 쉽고 디버깅도 쉽다 |
| 도중에 `break`·`continue`·예외가 필요 | **스트림을 안 쓴다.** 검사 예외를 람다에서 던질 수 없다 |

판단 규칙 두 줄.

- **소스를 고를 때 원소 타입이 정해진다.** 숫자면 기본형 스트림에서 출발한다.
- **최종 연산까지 한 문장 안에서 끝낸다.** 스트림을 변수에 담으면 재사용·수정 함정을 둘 다 만난다.

## 핵심 문장

- 소스를 고르는 순간 **원소 타입과 쓸 수 있는 연산이 정해진다** — `Arrays.stream(int[])` 은 `IntStream`, `Stream.of(int[])` 은 원소 하나짜리 `Stream<int[]>`.
- **최종 연산이 없으면 소스 순회가 시작되지 않는다**(javadoc 명시). 중간 연산만 써 놓으면 조용히 아무 일도 안 일어난다.
- **중간 연산의 부작용은 실행이 보장되지 않는다** — `count()` 는 `peek` 를 통째로 건너뛴다.
- 스트림은 **한 번만 소비**된다. 두 번째 최종 연산은 `IllegalStateException`.
- 스트림은 원소를 **복사하지 않는다.** 소비 시점의 소스 내용이 흘러간다.

## 관련 자료

- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 44번)
- [`../45-intermediate-operations/`](../45-intermediate-operations/) — 이 스트림 위에 무엇을 얹는가. **이 주제가 45번의 선행**이다
- [`../01-primitives-and-wrappers/`](../01-primitives-and-wrappers/) — `boxed()` 가 부르는 `Integer.valueOf` 와 캐시
- [`../../../../../algorithm/`](../../../../../algorithm/) — 순회·필터 **알고리즘은 거기**가 정본. 여기는 API 표면만
- [`../../../../../../history/java/java-8.md`](../../../../../../history/java/java-8.md) — 스트림이 **왜 Java 8 에 들어왔나**. 도입 맥락은 거기
- [`../../언어-특성/README.md`](../../언어-특성/README.md) — JIT·GC. 박싱 비용이 실제로 얼마인가는 거기
- [**31번 주제**](../31-functional-interfaces/)(함수형 인터페이스) — `Stream.generate(Supplier)` 의 그 `Supplier`
- [**39번 주제**](../39-collections-framework-map/)(컬렉션 프레임워크 지도) — `Collection.stream()` 이 어디에 붙어 있나
- [**43번 주제**](../43-iterator-and-fail-fast/)(fail-fast) — 소비 중 소스를 고쳤을 때
- [**46번 주제**](../46-terminal-operations/)(최종 연산과 지연 평가) — 이 문서의 「스위치」가 정본으로 다뤄지는 곳
- [**49번 주제**](../49-parallel-streams/)(병렬 스트림) — `parallelStream()` 이 값을 내는 조건

## 용어 풀이

- **스트림(stream)** — 원소의 연속을 한 번 흘려보내며 처리하는 파이프라인. 값을 저장하지 않는다.
- **소스(source)** — 스트림에 원소를 공급하는 것. 컬렉션·배열·생성 함수.
- **중간 연산(intermediate operation)** — 스트림을 받아 스트림을 돌려주는 연산. 언제나 지연된다.
- **최종 연산(terminal operation)** — 파이프라인을 실제로 돌리고 스트림을 닫는 연산.
- **지연 평가** — 결과가 필요해질 때까지 계산을 미루는 것.
- **단락 평가(short-circuiting)** — 전부를 보지 않고 답이 정해지면 멈추는 것. 무한 스트림을 끝낼 수 있는 유일한 수단.
- **기본형 스트림(primitive stream)** — `IntStream`·`LongStream`·`DoubleStream`. 원소가 래퍼 객체가 아니라 값이다.
- **박싱(boxing)** — 기본형을 래퍼 객체로 감싸는 것. `boxed()` 가 하는 일.
- **가변 인자(varargs)** — `T...` 형태의 매개변수. 배열을 넘기면 펼쳐지지만 기본형 배열은 펼쳐지지 않는다.
- **`IllegalStateException`** — 객체가 그 호출을 받을 수 있는 상태가 아닐 때의 예외. 이미 소비한 스트림을 다시 쓰면 난다.

---

## 더 들어가면

- **`IntStream.range(0, n)` 은 `SIZED` 특성을 갖는다.**\
  그래서 `toArray()` 같은 최종 연산이 배열 크기를 미리 잡을 수 있고, `count()` 는 순회 없이 끝난다.\
  반대로 `Stream.iterate` 2인자 형태는 크기를 모르므로 그런 최적화가 안 걸린다.
- **`Files.lines(path)` 는 닫아야 한다.**\
  스트림 중 파일·소켓을 붙잡는 것은 `AutoCloseable` 이라 `try`-with-resources 가 필요하다.\
  대부분의 스트림은 닫지 않아도 된다 — 컬렉션·배열 소스는 붙잡는 자원이 없다.
- **`Collection.stream()` 의 기본 구현**은 `StreamSupport.stream(spliterator(), false)` 다.\
  `Spliterator` 가 "어떻게 쪼갤 수 있나"를 알려 주고, 그 정보로 병렬 성능이 갈린다(목록의 49번 주제).
- **`Random.ints()`·`Random.doubles()`** 도 스트림 소스다. 난수 n 개가 필요하면 `new Random().ints(n, 0, 100)`.
- **`Stream.toList()`(16+)와 `collect(Collectors.toList())` 는 다르다.** 실제로 돌려 확인했다(`Extra.java`).

  ```text
  toList() 에 null : [x, null]
  toList() 수정: UnsupportedOperationException
  collect(toList()) 수정: 가능
  collect(toList()) 타입 : java.util.ArrayList
  toUnmodifiableList + null : NPE
  ```

  `toList()` 는 **수정 불가능하지만 `null` 원소는 받는다.**\
  `Collectors.toUnmodifiableList()` 는 `null` 에서 NPE 를 던진다 — 같은 "불변"이 아니다.
