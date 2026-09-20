# java/syntax/45 — 중간 연산: `map`/`filter`/`flatMap`/`mapMulti` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **선행** — [`../44-stream-creation/`](../44-stream-creation/). 스트림을 어떻게 만드는지와 **지연 평가**를 먼저 본다.
> **기준 소스** — [`java.util.stream` 패키지 javadoc (Java SE 21)](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/package-summary.html) · [`Stream` javadoc (Java SE 21)](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/Stream.html)
> **실행 검증** — 이 문서의 모든 출력은 Temurin **JDK 21.0.5** 에서 실제로 돌려 얻은 것이다.\
> 같은 프로그램을 **17.0.13 · 25.0.1** 에서도 돌려 **출력이 한 글자도 다르지 않음**을 확인했다.
> **버전** — `map`·`filter`·`flatMap` 은 **Java 8**. `takeWhile`/`dropWhile` 은 **Java 9**. `mapMulti` 는 **Java 16**.\
> 17·21·25 동작 동일.
> **범위** — "무엇을 걸러 무엇을 만드는가"라는 **알고리즘**은 [`../../../../../algorithm/`](../../../../../algorithm/) 이 정본이다.\
> 여기는 **연산의 타입 계약과 평가 시점**만 다룬다.
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**중간 연산은 벨트 위에 늘어놓은 작업대다.**

44번의 비유를 그대로 잇는다.

| 비유 | 실체 |
|---|---|
| 벨트 위의 작업대 | 중간 연산 |
| 물건 하나를 다른 물건 하나로 바꾸는 작업대 | `map` — 1:1 |
| 통과·탈락을 정하는 검사대 | `filter` — 1:0 또는 1:1 |
| 상자를 열어 안의 물건들을 벨트에 쏟는 작업대 | `flatMap` — 1:N |
| 작업자가 손으로 필요한 만큼 올리는 작업대 | `mapMulti` — 1:N (16+) |
| 물건을 전부 모았다가 한꺼번에 내보내는 작업대 | 상태 있는 연산 — `sorted`·`distinct` |

- 중요한 것은 **벨트가 도는 방식**이다.\
  작업대별로 전부 처리하고 다음 작업대로 넘기는 게 **아니다.**
- **물건 하나가 작업대 전부를 통과한 뒤에야 다음 물건이 올라온다.**\
  그래서 앞쪽 검사대에서 탈락한 물건은 뒤쪽 작업대에 **아예 가지 않는다.**
- 그 덕에 **끝에서 "하나만 주세요"라고 하면 물건 하나만 처리하고 벨트가 선다.**

```text
Stream.of("apple", "fig", "banana").filter(길이>3).map(대문자).toList()

  apple  -> filter 통과 -> map -> APPLE     <- apple 이 끝까지 간 뒤
  fig    -> filter 탈락                      <- fig 는 map 을 아예 안 거친다
  banana -> filter 통과 -> map -> BANANA

  실제 출력:
    filter apple
      map apple
    filter fig            <- map 이 안 나온다
    filter banana
      map banana
```

**똑같은 구조로** Java 가 이렇게 동작한다: 작업대 = 중간 연산, 물건 하나가 끝까지 = 원소 단위 파이프라인 통과.

실무에서 이게 값을 내는 자리는 **비싼 연산(DB 조회·변환)을 `filter` 뒤에 두는 것**이다.\
`map` 을 먼저 하면 버릴 원소까지 변환한다 — 같은 결과, 두 배의 일.

> **중간 연산(intermediate operation)** — 스트림을 받아 스트림을 돌려주는 연산. **언제나 지연**된다.\
> 예: `filter` 를 부른 시점에는 조건 검사가 한 번도 실행되지 않는다. 최종 연산이 와야 돈다.

> **원소 단위 통과(element-at-a-time)** — 원소 하나가 파이프라인 끝까지 간 뒤 다음 원소가 시작되는 것.\
> 예: `filter` 를 3번 실행하고 나서 `map` 을 2번 실행하는 게 아니라, 둘이 번갈아 실행된다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. `map` 과 `flatMap` 이 갈리는 자리를 **타입으로** 어떻게 판단하나.
2. 연산들은 **어떤 순서로** 실행되나 — 작업대별인가 원소별인가.
3. 연산을 **어디에 두느냐**가 무엇을 바꾸나.

## 동작 방식

### (1) 원소 하나가 파이프라인 끝까지 간다

**언제 쓰나** — 실행 횟수·순서를 따질 때. 비싼 연산의 위치를 정할 때.

**실행 결과** (`Order.java`)

```text
== filter -> map, 원소 하나씩 끝까지 간다 ==
  filter apple
    map apple
  filter fig
  filter banana
    map banana
결과 [APPLE, BANANA]
```

```text
잘못된 기대 — 작업대별로 처리             실제 — 원소별로 처리

  filter apple                            filter apple
  filter fig                                map apple
  filter banana                           filter fig          <- 탈락, map 안 감
    map apple                             filter banana
    map banana                              map banana
```

그림 해설 (한 단계씩):

- 왼쪽처럼 돈다면 `filter` 세 줄이 먼저 다 나오고 `map` 이 나와야 한다.
- 실제 출력은 오른쪽이다 — **`filter apple` 바로 다음이 `map apple`** 이다.
- `fig` 는 `filter` 에서 탈락했으므로 `map` 에 **아예 도달하지 않았다.**
- 그래서 중간 버퍼가 필요 없다 — 원소 하나만 메모리에 있으면 된다.

비용 — 메모리는 파이프라인 깊이에 비례할 뿐 원소 수와 무관하다.\
`filter` 가 걸러 낸 원소는 뒤쪽 연산의 비용을 **전혀** 발생시키지 않는다.

### (2) 최종 연산이 멈추면 벨트도 멈춘다

**언제 쓰나** — 무한 스트림을 쓸 때. 큰 입력에서 앞부분만 필요할 때.

**실행 결과** (`Order.java`)

```text
== findFirst 는 첫 통과에서 멈춘다 ==
  filter apple
    map apple
결과 APPLE
== 무한 스트림 + limit ==
  next from 1
  next from 2
  next from 4
결과 [1, 2, 4, 8]
```

```text
toList() — 전부 필요                    findFirst() — 하나면 된다

  apple  -> filter -> map -> 수집         apple -> filter -> map -> 찾았다
  fig    -> filter -> (탈락)                          |
  banana -> filter -> map -> 수집                     v
                                          fig, banana 는 소스에서 꺼내지도 않는다
  filter 3회 / map 2회                    filter 1회 / map 1회
```

그림 해설 (한 단계씩):

- `findFirst` 는 `apple` 하나만 처리하고 끝났다.\
  `fig`·`banana` 는 **소스에서 읽히지도 않았다.**
- 무한 스트림 예에서 `next from` 이 **세 번**만 나왔다.\
  `limit(4)` 니까 원소가 넷 필요한데, 첫 원소는 씨앗(`1`)이라 함수는 세 번만 불리면 된다.
- 이것이 **무한 스트림이 실용적인 이유**다 — 필요한 만큼만 만들어진다.

비용 — 단락 평가가 있으면 **필요한 원소 수 × 파이프라인 깊이**만큼만 일한다.

> **단락 평가(short-circuiting)** — 전부를 보지 않고 답이 정해지면 멈추는 것.\
> 예: `findFirst`·`anyMatch`·`limit`. 무한 스트림을 끝낼 수 있는 유일한 수단이다.

### (3) `map` 과 `flatMap` — 타입으로 갈린다

**언제 쓰나** — 결과가 `Stream<Stream<...>>` 이나 `Stream<List<...>>` 이 됐을 때.

```text
List<List<Integer>> nested = [[1, 2], [3], []]

map(List::stream)                          flatMap(List::stream)

  [1,2] -> Stream 객체                       [1,2] -> 열어서 1, 2 를 쏟는다
  [3]   -> Stream 객체                       [3]   -> 열어서 3 을 쏟는다
  []    -> Stream 객체                       []    -> 쏟을 게 없다
     |                                          |
     v                                          v
  Stream<Stream<Integer>>                    Stream<Integer>
  원소 3개 (전부 Stream 객체)                 원소 3개 (1, 2, 3)
```

**실행 결과** (`Flat.java`)

```text
map     : 3 개 (원소가 Stream 객체다)
map 타입: Stream<Stream<Integer>>
flatMap : [1, 2, 3]
map     : 2 개 (원소가 String[] 이다)
flatMap : [a, b, c, d]
```

그림 해설 (한 단계씩):

- **`map` 은 개수를 바꾸지 않는다.** 원소 3개가 들어가면 3개가 나온다.\
  안이 무엇이든 껍데기 개수는 그대로다.
- **`flatMap` 은 한 겹을 벗긴다.** 개수가 바뀐다.
- 판단 기준 한 줄: **람다가 `Stream`(또는 컬렉션)을 돌려주면 `flatMap`, 값 하나를 돌려주면 `map`.**
- 빈 것(`[]`)은 **사라진다** — 그래서 `flatMap` 으로 걸러 낼 수도 있다.

비용 — `flatMap` 은 원소마다 내부 스트림을 하나씩 만든다.\
그 객체 생성이 부담이면 `mapMulti` 를 쓴다((5)).

### (4) `flatMap` 도 단락 평가를 존중한다

**언제 쓰나** — 중첩 구조에서 앞부분만 필요할 때.

**실행 결과** (`FlatLazy.java`, 17·21·25 동일)

```text
== flatMap + findFirst ==
  안쪽 1
결과 1
== flatMap + limit(2) ==
  안쪽 1
  안쪽 2
결과 [1, 2]
== 바깥 스트림은 몇 번 돌았나 ==
  바깥 [1, 2, 3]
```

```text
nested = [[1,2,3],[4,5]] 에서 findFirst

  바깥 [1,2,3] -> 안쪽 스트림을 연다
                   안쪽 1 -> 찾았다 -> 멈춤
  바깥 [4,5]   -> 열지도 않는다
  안쪽 2, 3    -> 읽지도 않는다
```

그림 해설 (한 단계씩):

- **안쪽 스트림도 필요한 만큼만** 소비된다. `안쪽 1` 하나만 찍혔다.
- 바깥 스트림도 첫 원소만 열었다 — `바깥 [4,5]` 가 안 나왔다.
- 세 JDK 에서 모두 같았다.\
  (초기 Java 8 구현에서는 안쪽 스트림을 끝까지 소비했다는 것이 알려진 사실이지만, **이 머신의 세 JDK 로는 확인할 수 없다** — 17·21·25 모두 단락 평가한다.)

비용 — 단락 평가가 중첩 구조에서도 유지되므로 큰 데이터에서도 안전하다.

### (5) `mapMulti` — 스트림을 안 만들고 직접 내보낸다 (16+)

**언제 쓰나** — `flatMap` 으로 하면 내부 스트림 객체가 아까울 때. 내보낼 개수가 0이나 1인 경우가 대부분일 때.

```text
flatMap                                    mapMulti
  람다가 Stream 을 만들어 돌려준다             람다가 sink 에 직접 밀어 넣는다
  원소마다 Stream 객체 1개                    Stream 객체 0개

  i -> Stream.of(i, i * 10)                 (i, sink) -> { sink.accept(i);
                                                          sink.accept(i * 10); }
```

**실행 결과** (`Flat.java`)

```text
flatMap 으로 불리기 : [1, 10, 2, 20]
mapMulti 같은 일   : [1, 10, 2, 20]
flatMap 으로 거르기 : [2, 4]
mapMulti 로 거르기 : [2, 4]
mapMultiToInt      : 6
```

그림 해설 (한 단계씩):

- 결과는 같다. **다른 것은 내부 객체 생성**뿐이다.
- `sink.accept(...)` 를 **부르지 않으면 그 원소는 사라진다** — `filter` 를 겸한다.
- `mapMultiToInt`·`mapMultiToLong`·`mapMultiToDouble` 로 **기본형 스트림으로 건너갈 수 있다.**\
  `Stream.of("1,2", "3")` 을 쪼개 `IntStream` 으로 받아 `sum()` 이 `6` 이 나왔다.
- 타입 추론이 약해 **`.<Integer>mapMulti(...)` 처럼 타입 인자를 명시**해야 하는 경우가 흔하다.

비용 — 원소당 내부 스트림 객체가 사라진다.\
대가는 가독성 — `flatMap` 쪽이 읽기 쉽다. **성능이 문제가 되는 것을 확인한 뒤에만** 바꾼다.

> **sink** — `mapMulti` 의 람다가 받는 소비자(`Consumer`). 여기에 넣은 것이 아래 연산으로 흘러간다.\
> 예: `sink.accept(x)` 를 두 번 부르면 원소 하나에서 둘이 나온다.

### (6) 상태 있는 중간 연산은 벨트를 멈춘다

**언제 쓰나** — `sorted`·`distinct` 를 섞었을 때. 출력 순서가 이상할 때.

**실행 결과** (`Stateful.java`)

```text
== map 은 원소마다 바로 흘려보낸다 ==
  map 3
    forEach 3
  map 1
    forEach 1
  map 2
    forEach 2
== sorted 는 다 모은 뒤에 흘려보낸다 ==
  map 3
  map 1
  map 2
    forEach 1
    forEach 2
    forEach 3
```

```text
상태 없는 연산 (map·filter·flatMap)        상태 있는 연산 (sorted·distinct)

  [3] -> map -> forEach                     [3] -> map -> 버퍼
  [1] -> map -> forEach                     [1] -> map -> 버퍼
  [2] -> map -> forEach                     [2] -> map -> 버퍼
                                                           |
  버퍼 없음. 무한 스트림 가능                                v  다 모인 뒤
                                                     정렬 -> forEach 1,2,3
                                            버퍼 필요. 무한 스트림 불가
```

그림 해설 (한 단계씩):

- `sorted` 앞까지는 **원소별로** 흐르다가, `sorted` 에서 **전부 모일 때까지 막힌다.**
- 첫 결과가 나오려면 **마지막 입력까지 봐야** 하기 때문이다.
- 그래서 `sorted`·`distinct` 는 **무한 스트림에서 쓸 수 없다**(44번 7번 참조 — 실제로 OOM 이 났다).
- `map`·`filter`·`flatMap`·`mapMulti` 는 **상태가 없다**. 이 넷이 이 주제의 대상이다.

비용 — `sorted` 는 원소 전부를 버퍼에 담는다. 메모리 O(n).\
`distinct` 도 본 값을 전부 기억한다.

## 문법 — 형태와 규칙

직접 쓴 최소 예제다. 출력은 전부 실행 결과다.

### 네 연산의 시그니처와 개수 변화

| 연산 | 람다의 타입 | 원소 개수 | 버전 |
|---|---|---|---|
| `map(Function<T,R>)` | `T -> R` | **그대로** | 8 |
| `filter(Predicate<T>)` | `T -> boolean` | **줄거나 그대로** | 8 |
| `flatMap(Function<T, Stream<R>>)` | `T -> Stream<R>` | **늘거나 줄거나** | 8 |
| `mapMulti(BiConsumer<T, Consumer<R>>)` | `(T, sink) -> void` | **늘거나 줄거나** | 16 |

### `flatMap` 의 세 가지 쓰임

```java
// 1:N — 펼치기
Stream.of(1, 2).flatMap(i -> Stream.of(i, i * 10))            // [1, 10, 2, 20]

// 1:0 — 거르기 (filter 를 겸한다)
Stream.of(1, 2, 3, 4).flatMap(i -> i % 2 == 0 ? Stream.of(i) : Stream.empty())   // [2, 4]

// null 제거 (9+)
Arrays.asList("a", null, "c").stream().flatMap(Stream::ofNullable)   // [a, c]
```

- 마지막 형태가 특히 쓸모 있다.\
  `map` 은 `null` 을 그대로 통과시킨다 — 실행 결과: `map 은 null 통과 : [a, null, c]`.

### 기본형 스트림을 건너다니기

| 가는 방향 | 쓰는 것 |
|---|---|
| `Stream<T>` -> `IntStream` | `mapToInt(ToIntFunction)` |
| `IntStream` -> `Stream<Integer>` | `boxed()` |
| `IntStream` -> `Stream<R>` | `mapToObj(IntFunction)` |
| `IntStream` -> `LongStream` | `asLongStream()` |
| `Stream<T>` -> `IntStream` (1:N) | `mapMultiToInt` (16+) |

- `IntStream` 에는 `map(IntUnaryOperator)` 가 있지만 **`int` 를 `int` 로만** 바꾼다.\
  다른 타입으로 가려면 `mapToObj`.

### `takeWhile` / `dropWhile` 와 `filter` 의 차이 (9+)

**실행 결과** (`Stateful.java`)

```text
  [1, 2]              takeWhile(i -> i < 3)
  dropWhile [5, 1]    dropWhile(i -> i < 3)
  filter    [1, 2, 1] filter(i -> i < 3)
```

```text
입력 [1, 2, 5, 1]

  filter     : 전부 검사해서 조건에 맞는 것을 모은다   -> [1, 2, 1]
  takeWhile  : 처음 어긋나는 순간 멈춘다              -> [1, 2]
  dropWhile  : 처음 어긋나는 순간부터 전부 통과        -> [5, 1]
```

- `takeWhile` 은 **단락 평가**다 — 무한 스트림을 끝낼 수 있다.
- 셋 다 같은 술어인데 결과가 다르다. **정렬된 입력**에서 의미가 갈린다.

## 어디서 틀리나

### 1. `map` 을 써야 할 자리에 `flatMap`, 또는 그 반대

- 증상: 결과 타입이 `Stream<Stream<X>>`·`Stream<List<X>>` 가 되거나, `toList()` 결과의 원소가 이상한 객체다.
- 컴파일 에러가 나면 다행이다 — `forEach(System.out::println)` 처럼 `Object` 를 받는 자리면 **조용히 `java.util.stream.ReferencePipeline$Head@...` 같은 게 찍힌다.**
- 판단: **람다의 반환 타입을 본다.** `Stream`·`List` 면 `flatMap`.

### 2. `map` 을 `filter` 앞에 둔다

**실행 결과** (`Placement.java`)

```text
map -> filter : 결과 [APPLE, BANANA] / map 호출 4회
filter -> map : 결과 [APPLE, BANANA] / map 호출 2회
```

```text
map -> filter                              filter -> map
  4개 전부 변환                              2개만 변환
  그중 2개를 버린다                          버릴 것은 변환하지 않는다
  +----------------------------+           +----------------------------+
  | map 4회                    |           | map 2회                    |
  | 버린 2회는 순수 낭비        |           |                            |
  +----------------------------+           +----------------------------+
   결과는 같다. 비용만 두 배                  같은 결과, 절반의 일
```

- **결과가 같아서 안 드러난다.** 테스트도 통과한다.
- `map` 안이 DB 조회·HTTP 호출·무거운 변환이면 이 차이가 곧바로 응답 시간이 된다.
- 규칙: **거르기를 먼저, 바꾸기를 나중에.**
- 예외: `filter` 의 조건이 변환 결과에 걸려 있으면 순서를 못 바꾼다.\
  그때는 `map` 을 한 번만 하도록 `flatMap` 이나 `mapMulti` 로 묶는다.

### 3. 중간 연산에 부작용을 넣는다

```java
list.stream().map(x -> { log.info("처리 {}", x); return convert(x); }).toList();
```

- 44번 (4)에서 본 것 — **중간 연산의 부작용은 실행이 보장되지 않는다.**\
  최종 연산이 `count()` 면 `map` 이 통째로 생략될 수 있다.
- 병렬 스트림이면 실행 **순서**도 보장되지 않는다(목록의 **49번 주제**).
- 그리고 외부 변수에 쓰려면 `final` 제약 때문에 배열·`AtomicInteger` 같은 우회를 쓰게 되는데, 그 자체가 **스트림을 잘못 쓰고 있다는 신호**다.
- 규칙: **부작용은 `forEach` 에서.** 세기는 `count()`·`Collectors.counting()` 으로.

### 4. `mapMulti` 의 출력 타입이 조용히 `Object` 가 된다

```java
Stream.of(1, 2).mapMulti((i, sink) -> { sink.accept(i * 10); })
               .mapToInt(x -> x)            // 여기서 컴파일 에러
```

```text
$ javac MM3.java
MM3.java:5: error: incompatible types: bad return type in lambda expression
                        .mapToInt(x -> x)
                                       ^
    Object cannot be converted to int
```

- `mapMulti` 자체는 **컴파일된다.** `sink.accept(i * 10)` 도 통과한다.\
  결과 타입 `R` 이 **`Object` 로 추론**될 뿐이다.
- 에러는 **한참 뒤 연산**에서 난다 — 메시지가 `mapMulti` 를 가리키지 않아 원인을 찾기 어렵다.
- 입력 타입은 제대로 추론된다 — `Stream.of("1,2","3").mapMulti((s, sink) -> s.split(","))` 에서 `s` 는 `String` 이다.\
  **출력 쪽만** 근거가 람다 본문밖에 없어서 못 정한다.
- 해결: **`.<Integer>mapMulti(...)` 로 타입 인자를 명시**한다. 그러면 `sum = 30` 이 정상으로 나온다.
- 이 불편함이 `mapMulti` 를 기본 선택으로 두지 않는 이유 중 하나다.

### 5. `sorted` 뒤에 `limit` 를 둔다

- 44번 7번에서 실행으로 확인한 것 — `Stream.iterate(...).sorted().limit(5)` 는 **OOM** 으로 죽는다.
- `sorted` 는 상태 있는 연산이라 **전부 모아야** 첫 원소를 낸다.
- 유한 스트림에서도 손해다 — n 개를 전부 정렬한 뒤 5개만 쓴다.
- 규칙: **`limit` 를 가능한 한 앞으로.** 상위 k 개가 필요하면 `sorted().limit(k)` 대신 정렬 없는 방법(우선순위 큐)을 고려한다.\
  그 알고리즘은 [`../../../../../algorithm/`](../../../../../algorithm/) 과 [`../../../../../data-structure/07-heap/`](../../../../../data-structure/07-heap/) 이 정본이다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 일 | 쓰는 것 |
|---|---|
| 값 하나를 값 하나로 | `map` |
| 조건으로 거르기 | `filter` |
| 중첩 구조 펼치기 | `flatMap` |
| `null` 빼기 | `flatMap(Stream::ofNullable)` (9+) |
| 하나에서 0~N 개, 그런데 대부분 0이나 1 | `mapMulti` (16+) — 스트림 객체를 안 만든다 |
| 정렬된 입력에서 앞부분만 | `takeWhile` (9+) — 전부 검사하지 않는다 |
| 숫자로 내려가기 | `mapToInt`·`mapToLong`·`mapToDouble` |
| 로깅·저장 | **중간 연산이 아니라 `forEach`** |
| 인덱스가 필요한 변환 | 스트림이 아니라 `for`, 또는 `IntStream.range` 로 시작 |

판단 규칙 세 줄.

- **람다의 반환 타입이 `map`/`flatMap` 을 결정한다.** 개수를 바꾸면 `flatMap`.
- **거르기를 먼저, 바꾸기를 나중에.** 같은 결과에 비용이 절반이 된다.
- **중간 연산은 순수하게.** 부작용은 실행 횟수도 순서도 보장되지 않는다.

## 핵심 문장

- 중간 연산은 **작업대별이 아니라 원소별**로 실행된다 — 원소 하나가 끝까지 간 뒤 다음 원소가 올라온다.
- 그래서 `filter` 에서 탈락한 원소는 뒤쪽 연산의 비용을 **전혀 발생시키지 않는다.** 연산 순서가 곧 비용이다.
- **`map` 은 개수를 안 바꾸고 `flatMap` 은 한 겹을 벗긴다.** 판단은 람다의 반환 타입으로 한다.
- `flatMap` 도 **단락 평가를 존중한다** — 17·21·25 에서 `findFirst` 가 안쪽 원소 하나만 읽었다.
- `sorted`·`distinct` 는 **상태 있는 연산**이라 전부 모일 때까지 막힌다. 무한 스트림에 쓸 수 없다.

## 관련 자료

- [`../44-stream-creation/`](../44-stream-creation/) — **이 주제의 선행.** 소스 팩토리와 지연 평가의 정본
- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 45번)
- [`../../../../../algorithm/`](../../../../../algorithm/) — 순회·필터·상위 k 개 **알고리즘은 거기**가 정본. 여기는 API 표면만
- [`../../../../../data-structure/07-heap/`](../../../../../data-structure/07-heap/) — 「어디서 틀리나」 5번의 대안(우선순위 큐)
- [`../01-primitives-and-wrappers/`](../01-primitives-and-wrappers/) — `mapToInt`/`boxed` 를 건널 때의 박싱
- [`../../../../../../history/java/java-8.md`](../../../../../../history/java/java-8.md) — 스트림·람다가 **왜 들어왔나**
- 목록의 **46번 주제**(최종 연산과 지연 평가) — 이 문서의 「멈춤」이 정본으로 다뤄지는 곳
- 목록의 **49번 주제**(병렬 스트림) — 부작용이 순서까지 잃는 곳
- 목록의 **50번 주제**(Gatherers, 24+) — 윈도·스캔처럼 기존 중간 연산으로 안 되는 것

## 용어 풀이

- **중간 연산(intermediate operation)** — 스트림을 받아 스트림을 돌려주는 연산. 언제나 지연된다.
- **상태 없는 연산(stateless)** — 원소 하나를 보고 결과를 낼 수 있는 연산. `map`·`filter`·`flatMap`·`mapMulti`.
- **상태 있는 연산(stateful)** — 결과를 내려면 다른 원소들도 봐야 하는 연산. `sorted`·`distinct`·`limit`·`skip`.
- **원소 단위 통과** — 원소 하나가 파이프라인 끝까지 간 뒤 다음 원소가 시작되는 실행 방식.
- **단락 평가(short-circuiting)** — 답이 정해지면 나머지를 안 보고 멈추는 것.
- **sink** — `mapMulti` 의 람다가 받는 `Consumer`. 여기에 넣은 값이 아래로 흘러간다.
- **부작용(side effect)** — 값을 돌려주는 것 말고 바깥 상태를 바꾸는 일(로깅·저장·카운터 증가).
- **`Function` / `Predicate` / `BiConsumer`** — `map`·`filter`·`mapMulti` 가 각각 받는 함수형 인터페이스. 목록의 31번 주제.

---

## [Claude 추가] 더 알면 좋은 것

- **`flatMap` 은 내부 스트림을 닫아 준다.** javadoc 원문(`Stream.java`, `flatMapToInt` 등)이 이렇게 쓴다.

  > Each mapped stream is closed after its contents have been placed into this stream. (If a mapped stream is `null` an empty stream is used, instead.)

  `Files.lines(path)` 처럼 자원을 붙잡는 스트림을 `flatMap` 안에서 만들면 다 쓴 뒤 닫힌다.\
  `map` 으로 만들어 쌓아 두면 아무도 안 닫는다.\
  덤으로 — 람다가 **`null` 을 돌려줘도 NPE 가 아니라 빈 스트림**으로 처리된다.
- **`peek` 는 디버깅용이고 그 외의 용도가 없다.**\
  javadoc 도 "This method exists mainly to support debugging" 이라고 쓴다.\
  44번에서 본 대로 실행이 보장되지 않으므로 운영 코드에 남기지 않는다.
- **`distinct()` 는 `equals`/`hashCode` 에 기댄다.**\
  계약이 깨진 객체면 중복이 안 걸러진다 — [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/).
- **`mapMulti` 가 JDK 에 들어온 동기**는 "1:0 또는 1:1 이 대부분인데 `flatMap` 은 매번 스트림을 만든다"였다.\
  그래서 개수가 대체로 0이나 1이면 `mapMulti`, 진짜로 여러 개로 펼칠 일이 많으면 `flatMap` 이 자연스럽다.
- **Gatherers(24+)** 가 들어오면서 "중간 연산을 직접 만드는" 길이 열렸다.\
  슬라이딩 윈도·누적 스캔처럼 기존 넷으로 표현할 수 없던 것이 대상이다 — 목록의 50번 주제.
