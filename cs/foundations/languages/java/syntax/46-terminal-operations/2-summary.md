# java/syntax/46 — 최종 연산과 지연 평가·단락 평가 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **선행** — [`../45-intermediate-operations/`](../45-intermediate-operations/). 중간 연산이 원소별로 흐른다는 것을 먼저 본다.
> **기준 소스** — [`java.util.stream` 패키지 javadoc (Java SE 21)](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/package-summary.html) · [`Stream` javadoc (Java SE 21)](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/Stream.html) · JDK 21.0.5 표준 라이브러리 소스 `java.base/java/util/stream/Stream.java`·`package-info.java`(`lib/src.zip`)
> **실행 검증** — 이 문서의 모든 출력은 Temurin **JDK 21.0.5** 에서 실제로 돌려 얻은 것이다.\
> 같은 프로그램 6개를 **17.0.13 · 25.0.1** 에서도 돌렸다. **스택트레이스의 줄 번호 말고는 출력이 전부 같았다**(아래 「구현 세부사항 대 언어 보장」).
> **버전** — 최종 연산은 전부 **Java 8**. `Stream.toList()` 만 **Java 16**. 17·21·25 동작 동일.
> **범위** — "무엇을 세고 무엇을 찾는가"라는 **알고리즘**은 [`../../../../../algorithm/`](../../../../../algorithm/) 이 정본이다.\
> 그쪽은 **탐색·집계를 어떤 절차로 하느냐**까지, 여기는 **그 절차를 스트림이 언제 실제로 돌리느냐**부터다.
> 병렬에서 달라지는 것은 [`../49-parallel-streams/`](../49-parallel-streams/) 가 정본이다 — 여기는 **순차 기준**으로 읽는다.
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**최종 연산은 벨트 끝의 시동 스위치다.**

44·45번의 비유를 그대로 잇는다.

| 비유 | 실체 |
|---|---|
| 물건을 올려 주는 장치 | 소스 — 44번 |
| 벨트 위의 작업대 | 중간 연산 — 45번 |
| **벨트 끝의 시동 스위치** | **최종 연산 — 이 주제** |
| 스위치를 누르지 않은 상태 | 지연 평가 — 아무 일도 안 난다 |
| "하나만 나오면 바로 끄세요" | 단락 평가 — `findFirst`·`anyMatch`·`limit` |
| 벨트를 한 번 돌리면 장치를 뗀다 | 스트림은 한 번만 소비된다 |
| 물건을 상자에 **순서대로** 담아 달라 | `forEachOrdered` |
| 물건을 **닥치는 대로** 담아 달라 | `forEach` |

- 장치를 연결하고 작업대를 늘어놓아도 **벨트는 안 돈다.**\
  스위치를 눌러야 그제서야 물건이 하나씩 올라온다.
- 스위치에는 **"다 돌려 주세요"** 와 **"하나만 나오면 바로 끄세요"** 두 종류가 있다.\
  뒤쪽이 단락 평가다. 무한히 물건을 만드는 장치를 붙여도 **끝난다.**
- 스위치는 **한 번만** 누를 수 있다. 두 번째로 누르면 벨트가 예외를 던진다.

```text
                   중간 연산만 있을 때            최종 연산이 붙었을 때

  소스 [a][b][c]   +--------------+              +--------------+
        |          | filter       |              | filter       |
        v          | map          |              | map          |
                   +--------------+              +--------------+
                          |                             |
                    (스위치 없음)                   toList()  <- 스위치
                          |                             |
                          v                             v
                   아무 일도 안 난다                  a, b, c 가 흐른다
                   출력 0줄 · 비용 0                 출력 3줄 · 결과 [A, B, C]
```

**똑같은 구조로** Java 가 이렇게 동작한다: 스위치 = 최종 연산, "하나만 나오면 끄세요" = 단락 평가.

실무에서 이게 터지는 자리는 **`stream().map(this::save)` 라고 써 놓고 데이터가 안 들어가는 것**,\
그리고 **스트림을 필드에 담아 두었다가 두 번째 호출에서 `IllegalStateException` 을 맞는 것**이다.

> **최종 연산(terminal operation)** — 파이프라인을 실제로 돌리고 스트림을 끝내는 연산.\
> 예: `toList()`·`count()`·`forEach()`·`sum()`. 이걸 부른 뒤에는 그 스트림을 다시 못 쓴다.

> **지연 평가(lazy evaluation)** — 결과가 실제로 필요해질 때까지 계산을 미루는 것.\
> 예: `filter` 를 걸어 둬도 최종 연산 전에는 조건 검사가 **한 번도** 실행되지 않는다.

> **단락 평가(short-circuiting)** — 답이 정해지면 나머지를 안 보고 멈추는 것.\
> 예: `anyMatch(i -> i % 2 == 0)` 은 짝수를 처음 만난 자리에서 끝난다. 뒤쪽 원소는 읽지도 않는다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. 최종 연산이 **없으면** 무슨 일이 일어나나 — 에러인가, 아무 일도 안 일어나나.
2. 최종 연산이 **있는데도** 중간 연산이 안 도는 경우가 있나. 있다면 무엇이 그것을 정하나.
3. 무한 스트림이 **끝나는 조건**은 무엇이고, 끝나지 않는 조건은 무엇인가.

## 동작 방식

### (1) 최종 연산이 없으면 아무 일도 안 난다

**언제 쓰나** — "저장 코드를 넣었는데 DB 에 안 들어간다"를 만났을 때.

javadoc 원문이다.

> Intermediate operations return a new stream. They are always *lazy*; ...
> **Traversal of the pipeline source does not begin until the terminal operation of the pipeline is executed.**

**실행 결과** (`Ex.java` — 46-a, 17·21·25 동일)

```text
== (1) 최종 연산 없음 ==
(여기까지 filter 가 한 줄도 없어야 한다)
== (2) 최종 연산 있음 ==
  filter a
  filter b
  filter c
결과 [a, b, c]
```

```text
Stream.of("a","b","c").filter(print)          ... .filter(print).toList()

  [a][b][c] --> (filter) --> ???               [a][b][c] --> (filter) --> [수집]
                    |                                           |
              스위치가 없다                                 스위치가 있다
                    |                                           |
           filter 람다 0회 호출                          filter 람다 3회 호출
           출력 0줄 · 에러도 0                             출력 3줄
```

그림 해설 (한 단계씩):

- 왼쪽은 **한 줄도 출력되지 않았다.** `filter` 의 람다가 한 번도 안 불린 것이다.
- 예외도 경고도 없다. **조용히 아무것도 안 한다** — 이것이 이 주제에서 가장 비싼 함정이다.
- 오른쪽은 `toList()` 라는 스위치가 붙어서야 세 줄이 나왔다.

비용 — 최종 연산이 없으면 비용이 **0**이다. 대신 하려던 일도 0이다.

### (2) 단락 평가 — 답이 정해지면 멈춘다

**언제 쓰나** — 큰 입력에서 조건에 맞는 첫 원소만 필요할 때. 무한 스트림을 쓸 때.

**실행 결과** (`Ex.java` — 46-a)

```text
== (3) findFirst ==
  peek a
결과 Optional[a]
== (4) anyMatch ==
  peek 1
  peek 2
결과 true
== (5) allMatch — 첫 false 에서 멈춘다 ==
  peek 1
  peek 2
  peek 3
결과 false
== (6) noneMatch ==
  peek 1
  peek 2
결과 false
```

```text
입력 [1, 2, 3, 4, 5]

  anyMatch(짝수)      1 검사 -> 아니다
                      2 검사 -> 맞다!  -> true      3,4,5 는 안 본다
  allMatch(3 미만)    1 검사 -> 맞다
                      2 검사 -> 맞다
                      3 검사 -> 아니다 -> false     4,5 는 안 본다
  noneMatch(==2)      1 검사 -> 아니다
                      2 검사 -> 맞다!  -> false     3,4,5 는 안 본다
```

그림 해설 (한 단계씩):

- 셋 다 **판정이 뒤집히는 순간** 멈춘다.\
  `anyMatch` 는 첫 `true`, `allMatch` 는 첫 `false`, `noneMatch` 는 첫 `true` 에서.
- `findFirst` 는 **첫 원소 하나**만 흘려보내고 끝났다 — `peek a` 한 줄뿐이다.
- 뒤쪽 원소는 **소스에서 꺼내지지도 않는다.** 람다가 안 불렸다는 것이 그 증거다.

비용 — 최악에는 전부 보지만, 평균적으로 **찾는 자리까지**만 일한다.\
무한 스트림에서는 이것이 「끝나느냐 안 끝나느냐」를 가른다.

### (3) 무한 스트림 + `limit` 이 끝나는 이유

**언제 쓰나** — `Stream.iterate`·`Stream.generate` 를 쓸 때.

**실행 결과** (`Ex.java` — 46-c)

```text
== 무한 스트림 + limit(4) ==
  next from 1
  next from 2
  next from 4
결과 [1, 2, 4, 8]
== 무한 스트림 + findFirst ==
  next from 1
  next from 2
  next from 4
  next from 8
결과 Optional[16]
== 무한 스트림 + anyMatch ==
  generate 1
  generate 2
  generate 3
결과 true
```

```text
Stream.iterate(1, i -> i*2).limit(4).toList()

  toList 가 "다음 원소 주세요" 라고 4번 요청한다
      |
      v
  limit 이 센다: 1번째 -> 씨앗 1 그대로        (함수 호출 0회)
                 2번째 -> f(1)=2              (next from 1)
                 3번째 -> f(2)=4              (next from 2)
                 4번째 -> f(4)=8              (next from 4)
                 5번째 -> 요청이 오지 않는다     <- 여기서 소스가 멈춘다
```

그림 해설 (한 단계씩):

- **소스가 원소를 밀어내는 게 아니라 최종 연산이 당겨 온다.**\
  그래서 "무한히 만드는 장치"를 붙여도 당기지 않으면 만들지 않는다.
- `limit(4)` 는 네 개를 받은 뒤 **더 달라고 하지 않는다.** 그 순간 파이프라인이 끝난다.
- `next from` 이 **세 번**만 나왔다 — 첫 원소는 씨앗이라 함수가 필요 없다.
- `findFirst` 도 같은 원리로 끝난다. `anyMatch` 도 마찬가지다.
- 거꾸로 **단락 평가가 하나도 없으면 끝나지 않는다** — `toList()`·`count()`·`sorted()` 를 무한 스트림에 걸면 프로그램이 멈추지 않거나 `OutOfMemoryError` 로 죽는다(44번 7번에서 실행으로 확인).

비용 — **필요한 원소 수 × 파이프라인 깊이**만큼만 일한다. 무한 소스의 나머지는 존재하지 않는 것과 같다.

### (4) 최종 연산이 중간 연산을 통째로 건너뛸 수 있다

**언제 쓰나** — `peek` 로 디버깅할 때. 중간 연산에 부작용을 넣었을 때.

**실행 결과** (`Ex.java` — 46-a)

```text
== (7) 단락이 아닌 최종 연산 — count 는 전부 본다? ==
결과 3
  peek-filter-count a
  peek-filter-count b
  peek-filter-count c
결과 3
```

```text
Stream.of("a","b","c").peek(print).count()     ... .filter(s->true).peek(print).count()

  소스가 크기를 안다 (SIZED)                    filter 가 끼면 크기를 모른다
  "3" 을 바로 돌려주면 된다                      몇 개가 통과할지는 돌려 봐야 안다
        |                                             |
        v                                             v
  peek 0회 호출 — 출력 0줄                       peek 3회 호출 — 출력 3줄
```

그림 해설 (한 단계씩):

- 첫 줄 `결과 3` **위에 `peek-count` 가 한 줄도 없다.** `count()` 가 파이프라인을 통째로 건너뛰었다.
- 그런데 `filter` 를 하나 끼우자 `peek` 가 세 번 불렸다.\
  **`filter` 가 개수를 바꿀 수 있어서** 더 이상 크기를 미리 알 수 없기 때문이다.
- 즉 **같은 `count()` 인데 파이프라인 모양에 따라 부작용 실행 횟수가 달라진다.**

javadoc 이 이 동작을 못박는다.

> The eliding of side-effects may also be surprising. With the exception of terminal operations `forEach` and `forEachOrdered`, **side-effects of behavioral parameters may not always be executed when the stream implementation can optimize away the execution of behavioral parameters without affecting the result of the computation.**

비용 — 이득 쪽이다(불필요한 순회를 건너뛴다).\
대가는 **부작용의 실행 횟수가 계약이 아니라는 것**이다.

### (5) 스트림은 한 번만 쓴다

**언제 쓰나** — 스트림을 변수·필드·반환값으로 들고 다닐 때.

**실행 결과** (`Ex.java` — 46-d)

```text
== (1) 최종 연산 두 번 ==
첫 소비 : 2
두 번째 : java.lang.IllegalStateException: stream has already been operated upon or closed
== (2) 중간 연산으로 가지를 친다 ==
둘째 가지 : java.lang.IllegalStateException: stream has already been operated upon or closed
== (3) 소비한 스트림에 중간 연산을 붙이면 ==
소비 뒤 filter : java.lang.IllegalStateException: stream has already been operated upon or closed
```

```text
되는 것                                   안 되는 것

  Stream<String> s = src.stream();         Stream<String> s = src.stream();
  s.map(f).toList();                       Stream<String> a = s.map(f);
                                           Stream<String> b = s.map(g);  <- 여기서 던진다
  src.stream().map(f).toList();
  src.stream().map(g).toList();            s.toList();
   (소스에서 새 스트림을 두 번 만든다)        s.count();                    <- 여기서 던진다
```

그림 해설 (한 단계씩):

- 세 경우 **전부 같은 메시지**다 — `stream has already been operated upon or closed`.
- 중요한 것은 **중간 연산을 두 번 붙이는 것도 막힌다**는 점이다.\
  최종 연산을 두 번 부르는 것만 금지가 아니다. 스트림은 **연결 자체가 일회용**이다.
- 다시 보려면 **소스를 들고 있다가 `stream()` 을 새로 부른다.**

비용 — 재사용은 불가. 대신 파이프라인이 중간 버퍼를 안 만든다(45번 (1)).

### (6) `forEach` 와 `forEachOrdered`

**언제 쓰나** — 부작용(로깅·저장·출력)을 넣어야 할 때. 특히 병렬에서.

**실행 결과** (`Ex.java` — 46-e, 입력은 1~12)

```text
== 순차 forEach ==
1 2 3 4 5 6 7 8 9 10 11 12
== 순차 forEachOrdered ==
1 2 3 4 5 6 7 8 9 10 11 12
== 병렬 forEach (3회) ==
  8 9 7 11 12 10 1 4 5 2 3 6
  8 9 7 11 12 10 2 3 1 5 4 6
  8 9 7 11 12 10 4 6 5 2 3 1
== 병렬 forEachOrdered (3회) ==
  1 2 3 4 5 6 7 8 9 10 11 12
  1 2 3 4 5 6 7 8 9 10 11 12
  1 2 3 4 5 6 7 8 9 10 11 12
```

```text
순차 스트림                                병렬 스트림

  forEach        1 2 3 ... 12               forEach        실행마다 다르다
  forEachOrdered 1 2 3 ... 12               forEachOrdered 1 2 3 ... 12
        |                                          |
   둘이 똑같다 — 차이가 안 보인다            여기서만 차이가 드러난다
```

그림 해설 (한 단계씩):

- **순차에서는 두 메서드가 구별되지 않는다.** 그래서 차이를 모른 채 `forEach` 를 쓰게 된다.
- 병렬로 바꾸는 순간 `forEach` 의 출력 순서가 무너진다. **실행마다 다르다.**
- `forEachOrdered` 는 병렬에서도 입력 순서(encounter order)를 지킨다.

javadoc 이 두 메서드를 이렇게 갈라 놓는다.

> (`forEach`) **The behavior of this operation is explicitly nondeterministic.** For parallel stream pipelines, this operation does *not* guarantee to respect the encounter order of the stream, as doing so would sacrifice the benefit of parallelism.

> (`forEachOrdered`) Performs an action for each element of this stream, **in the encounter order of the stream if the stream has a defined encounter order.**

비용 — `forEachOrdered` 는 병렬의 이득을 대부분 반납한다.\
1000만 개 `int[]` 실측에서 **병렬 `forEach` 8,472us 대 병렬 `forEachOrdered` 125,047us**(15배)였다.\
같은 측정에서 순차 `forEach` 는 116,889us — **`forEachOrdered` 는 순차와 거의 같다**([`../49-parallel-streams/`](../49-parallel-streams/) 가 정본).

## 문법 — 형태와 규칙

직접 쓴 최소 예제다. 출력은 전부 실행 결과다.

### 최종 연산 지도 — 무엇을 돌려주나

| 하고 싶은 일 | 최종 연산 | 돌려주는 것 | 단락? |
|---|---|---|---|
| 리스트로 받기 | `toList()` (16+) | 수정 불가 `List` | 아니다 |
| 리스트로 받기(수정 가능) | `collect(Collectors.toList())` | `ArrayList` (실측) | 아니다 |
| 배열로 받기 | `toArray()` / `toArray(T[]::new)` | `Object[]` / `T[]` | 아니다 |
| 개수 | `count()` | `long` | 아니다 |
| 하나씩 처리 | `forEach` / `forEachOrdered` | `void` | 아니다 |
| 최소·최대 | `min(cmp)` / `max(cmp)` | `Optional<T>` | 아니다 |
| 접기 | `reduce(...)` | `Optional<T>` 또는 `T` | 아니다 |
| 모으기 | `collect(Collector)` | 수집기 나름 (47·48번) | 아니다 |
| 첫 원소 | `findFirst()` | `Optional<T>` | **그렇다** |
| 아무 원소 | `findAny()` | `Optional<T>` | **그렇다** |
| 하나라도 맞나 | `anyMatch(p)` | `boolean` | **그렇다** |
| 전부 맞나 | `allMatch(p)` | `boolean` | **그렇다** |
| 하나도 안 맞나 | `noneMatch(p)` | `boolean` | **그렇다** |
| 직접 순회 | `iterator()` / `spliterator()` | `Iterator` / `Spliterator` | — (탈출구) |
| 합·평균 (기본형만) | `sum()` / `average()` | `int`·`long`·`double` / `Optional*` | 아니다 |

- `limit` 도 단락 평가지만 **최종 연산이 아니라 중간 연산**이다.\
  단락 평가는 최종 연산만의 성질이 아니다 — `limit`·`takeWhile` 도 그렇다.

### 빈 스트림에서 무엇이 나오나

**실행 결과** (`Ex.java` — 46-b)

```text
anyMatch  : false
allMatch  : true
noneMatch : true
빈 스트림 + 항등원   : 0
빈 스트림 항등원 없음 : Optional.empty
빈 min    : Optional.empty
빈 findFirst : Optional.empty
빈 count  : 0
빈 IntStream sum : 0
빈 IntStream max : OptionalInt.empty
```

- **`allMatch` 와 `noneMatch` 는 빈 스트림에서 `true`** 다. 이것을 공허한 참이라 부른다.
- 합에는 항등원 `0` 이 있어서 값을 돌려주지만, 최댓값에는 항등원이 없어서 `Optional` 이 나온다.

> **공허한 참(vacuously true)** — 대상이 하나도 없을 때 "전부 ~하다"가 참이 되는 것.\
> 예: 빈 바구니에 대고 "이 안의 사과는 전부 빨갛다"는 반례가 없어 참이다.

### `reduce` 세 형태

```java
Stream.of(1,2,3,4).reduce(Integer::sum)        // Optional[10]  — 항등원 없음
Stream.of(1,2,3,4).reduce(0, Integer::sum)     // 10            — 항등원 있음
Stream.<Integer>empty().reduce(0, Integer::sum)// 0             — 항등원이 기본값
```

- 항등원을 주면 **`Optional` 이 아니라 값**이 나온다. 빈 스트림이면 항등원 자체가 답이다.
- 항등원은 **아무 값이나 되는 게 아니다.** javadoc 은 `combiner.apply(identity, u)` 가 `u` 와 같아야 한다고 요구한다.\
  이 요구를 어기면 순차에서는 티가 안 나고 **병렬에서만 틀린 답이 나온다**([`../49-parallel-streams/`](../49-parallel-streams/)).

### `iterator()` 는 최종 연산인데 지연된다

**실행 결과** (`Ex.java` — 46-b)

```text
iterator() 를 부른 직후 — 위에 peek 가 없어야 한다
  peek a
첫 next() : a
iterator 뒤 재사용 : java.lang.IllegalStateException: stream has already been operated upon or closed
```

- `iterator()`·`spliterator()` 는 **최종 연산이면서도 원소를 당장 흘려보내지 않는다.**\
  `next()` 를 부를 때 한 개씩 흐른다.
- 그래도 스트림은 **소비된 것으로 표시**된다. 그 뒤 재사용은 예외다.
- javadoc 은 이 둘을 「탈출구(escape-hatch) 연산」이라 부른다.

## 어디서 틀리나

### 1. 최종 연산을 안 붙인다

```java
users.stream().filter(User::isActive).map(this::save);   // 아무 일도 안 일어난다
```

- 에러도 경고도 없다. **데이터가 그냥 안 들어간다.**
- 배포하고 며칠 뒤 "왜 저장이 안 되지"로 발견되는 유형이다.
- IDE 인스펙션·SpotBugs 가 "스트림 결과를 버렸다"로 잡아 주기도 하지만 **언어가 막지 않는다.**
- 방어: **저장·로깅은 `forEach` 에서.** 중간 연산에 부작용을 넣지 않는다.

### 2. `peek` 가 안 찍힌다고 파이프라인이 안 돈 것은 아니다

- (4)에서 본 것이다. `count()` 는 `peek` 를 **0회** 실행했다.
- 그런데 `filter` 를 끼우자 3회 실행됐다 — **같은 `count()` 인데** 그렇다.
- 디버깅할 때는 **최종 연산을 `toList()` 로 바꿔 놓고** 확인한다.
- `peek` 는 javadoc 이 "This method exists mainly to support debugging" 이라 적은 디버깅 전용 메서드다. 운영 코드에 남기지 않는다.

### 3. 스트림을 필드·반환값으로 들고 다닌다

```java
class Repo {
    private final Stream<User> users;          // 위험하다
    Stream<User> all() { return users; }       // 두 번째 호출자가 터진다
}
```

- 호출자가 둘이면 **둘째가 `IllegalStateException`** 을 맞는다.
- 더 나쁜 것은 **호출 순서에 따라 터진다**는 점이다 — 테스트 하나만 돌리면 통과한다.
- 방어: **컬렉션을 들고 있다가 그때그때 `stream()` 을 만든다.**\
  꼭 스트림을 돌려줘야 하면 `Supplier<Stream<T>>` 를 돌려준다.

### 4. 무한 스트림에 단락 평가가 아닌 최종 연산을 건다

```java
Stream.iterate(1, i -> i + 1).count();      // 끝나지 않는다
Stream.iterate(1, i -> i + 1).sorted();     // OutOfMemoryError (44번에서 확인)
```

- `count()`·`toList()`·`sorted()`·`max()` 는 **전부를 봐야** 답이 나온다.
- 단락 평가 목록을 외워 두는 게 방어다 — `findFirst`·`findAny`·`anyMatch`·`allMatch`·`noneMatch` (+ 중간 연산 `limit`·`takeWhile`).
- 방어: 무한 소스를 쓰면 **같은 문장 안에서** `limit` 또는 3인자 `iterate`(9+)로 끝을 준다.

### 5. `forEach` 로 병렬 순서를 기대한다

```java
list.parallelStream().forEach(out::println);   // 순서가 실행마다 다르다
```

- (6)에서 실행으로 확인했다. 같은 코드가 세 번 다 다른 순서를 냈다.
- 순차로 개발·테스트하면 **차이가 안 보인다.** 병렬로 바꾼 뒤에야 드러난다.
- 방어: 순서가 필요하면 `forEachOrdered`, 아니면 **애초에 `collect` 로 모아서** 나중에 순회한다.\
  `forEachOrdered` 는 병렬 이득을 거의 다 반납한다는 것도 같이 안다((6)의 비용).

### 6. `forEach` 안에서 공유 컬렉션을 고친다

```java
List<String> out = new ArrayList<>();
list.parallelStream().forEach(out::add);       // 조용히 원소가 사라진다
```

- 이것은 **예외가 아니라 무음 실패**로 끝나는 경우가 많다 — 자세한 실측은 [`../49-parallel-streams/`](../49-parallel-streams/) 가 정본이다.
- 방어: **`collect` 로 받는다.** `forEach` 안에서 바깥 컬렉션을 고치지 않는다.

### 7. 최종 연산이 스트림을 **닫지는** 않는다

**실행 결과** (`Ex.java` — 46-f)

```text
== onClose 는 최종 연산이 부르지 않는다 ==
toList : [a, b]
(위에 「닫혔다」가 없다)
== 직접 close() 하면 ==
toList : [a, b]
  닫혔다
```

- 최종 연산은 스트림을 **소비 완료 상태로 만들지만 `close()` 를 부르지는 않는다.**
- 대부분의 스트림은 닫을 자원이 없어서 문제가 안 된다.
- **`Files.lines`·`Files.walk` 처럼 파일 핸들을 잡는 스트림만** `try`-with-resources 가 필요하다.\
  안 닫아도 **예외가 없다** — 조용히 샌다.

## 구현 세부사항 대 언어 보장

이 주제는 **"보장"과 "지금 그렇게 동작함"이 가장 크게 갈리는** 자리다.

| 관측한 것 | 보장인가 | 근거 |
|---|---|---|
| 최종 연산 전에는 소스 순회가 시작되지 않는다 | **보장** | 패키지 javadoc 명시 |
| 스트림 재사용은 `IllegalStateException` | **보장** | `BaseStream` javadoc — "must be generated to revisit" |
| `count()` 가 `peek` 를 건너뛴다 | **보장 아님** — 최적화가 가능할 때의 동작 | javadoc 은 "may not always be executed" 라고만 적는다 |
| `filter` 를 끼우면 `peek` 가 실행된다 | **보장 아님** | 위와 같다. 구현이 크기를 모를 뿐이다 |
| `forEach`·`forEachOrdered` 의 부작용은 실행된다 | **보장** | 위 인용의 "With the exception of ..." |
| 병렬 `forEach` 의 순서 | **보장 없음(명시적 비결정)** | javadoc "explicitly nondeterministic" |
| `IllegalStateException` 의 **메시지 문구** | **보장 아님** | 아래 실측 |
| 스택트레이스의 **줄 번호** | **보장 아님** | 아래 실측 |

**세 JDK 실측** — 같은 프로그램 6개를 17.0.13 · 21.0.5 · 25.0.1 에서 돌렸다.\
출력이 달라진 곳은 **스택트레이스의 줄 번호뿐**이었다.

```text
JDK 21.0.5                                          JDK 25.0.1
  AbstractPipeline.evaluateToArrayNode(:246)          AbstractPipeline.evaluateToArrayNode(:277)
  ReferencePipeline.toArray(:616)                     ReferencePipeline.toArray(:652)
  ReferencePipeline.toList(:627)                      ReferencePipeline.toList(:663)
   예외 메시지는 한 글자도 같다                          예외 메시지는 한 글자도 같다
```

- **메시지를 코드에서 파싱하지 마라.** 버전 간에 같았던 것은 운이지 계약이 아니다.
- 반대로 **`IllegalStateException` 이라는 타입은 계약**이다. 잡으려면 타입으로 잡는다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 일 | 고를 것 |
|---|---|
| 결과를 리스트로 | `toList()` (16+). 수정이 필요하면 `collect(Collectors.toList())` |
| 조건에 맞는 첫 원소 | `findFirst()` — 단락 평가라 큰 입력에서 싸다 |
| 있는지만 알면 됨 | `anyMatch(p)` — `filter(p).findFirst().isPresent()` 보다 의도가 드러난다 |
| 개수만 | `count()` — 단 부작용이 걸려 있으면 건너뛸 수 있다 |
| 저장·로깅·출력 | `forEach` — **부작용이 보장되는 유일한 자리**(와 `forEachOrdered`) |
| 순서가 중요한 부작용 | `forEachOrdered`. 단 병렬 이득을 거의 잃는다 |
| 집계·그룹핑 | `collect(Collector)` — [`../47-collectors-basics/`](../47-collectors-basics/)·[`../48-collectors-grouping/`](../48-collectors-grouping/) |
| 무한 스트림 | 단락 평가를 **반드시** 하나 넣는다 |
| 도중에 `break`·검사 예외 | **스트림을 안 쓴다.** `for` 가 낫다 |

판단 규칙 세 줄.

- **최종 연산까지 한 문장 안에서 끝낸다.** 스트림을 변수에 담으면 재사용 함정을 만난다.
- **부작용은 `forEach`(와 `forEachOrdered`)에만.** 나머지 자리에서는 실행 횟수가 계약이 아니다.
- **무한 소스에는 단락 평가를 짝지어 둔다.** 짝이 없으면 안 끝나거나 OOM 이다.

## 핵심 문장

- **최종 연산이 없으면 소스 순회가 시작되지 않는다** — 에러가 아니라 무음이다. 이것이 이 주제의 첫 번째 함정이다.
- 단락 평가(`findFirst`·`findAny`·`anyMatch`·`allMatch`·`noneMatch`)는 **판정이 뒤집히는 순간 멈춘다.** 그 덕에 무한 스트림이 끝난다.
- **최종 연산이 있어도 중간 연산이 안 돌 수 있다** — `count()` 는 `peek` 를 0회 실행했고, `filter` 를 끼우자 3회 실행했다.
- 스트림은 **연결 자체가 일회용**이다 — 최종 연산 두 번도, 중간 연산으로 가지를 치는 것도 같은 `IllegalStateException`.
- `forEach` 와 `forEachOrdered` 의 차이는 **병렬에서만 드러난다.** 순차에서 둘은 구별되지 않는다.

## 관련 자료

- [`../44-stream-creation/`](../44-stream-creation/) — 소스 팩토리. **이 문서의 「스위치」를 처음 언급한 곳**
- [`../45-intermediate-operations/`](../45-intermediate-operations/) — **이 주제의 선행.** 원소 단위 통과와 상태 있는 연산
- [`../47-collectors-basics/`](../47-collectors-basics/) — `collect` 라는 최종 연산의 인자. 그쪽은 **무엇을 어떻게 모으나**까지, 여기는 **언제 모으기가 시작되나**부터
- [`../49-parallel-streams/`](../49-parallel-streams/) — 병렬에서 이 문서의 규칙이 어디까지 유지되나. 그쪽은 **분할·스레드·측정**까지, 여기는 **순차 기준의 평가 시점**까지
- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 46번)
- [`../../../../../algorithm/`](../../../../../algorithm/) — 탐색·집계 **알고리즘은 거기**가 정본. 그쪽은 **어떤 절차로 찾나**까지, 여기는 **그 절차가 언제 도나**부터
- [**38번 주제**](../38-optional/)(`Optional`) — `findFirst`·`min`·`max` 가 돌려주는 그 타입의 정본
- [`../../../../../../history/java/java-8.md`](../../../../../../history/java/java-8.md) — 스트림이 **왜 Java 8 에 들어왔나**. 도입 맥락은 거기
- [**26번 주제**](../26-try-with-resources/)(`try`-with-resources) — 「어디서 틀리나」 7번의 `Files.lines`
- [**43번 주제**](../43-iterator-and-fail-fast/)(fail-fast) — 소비 중 소스를 고쳤을 때

## 용어 풀이

- **최종 연산(terminal operation)** — 파이프라인을 실제로 돌리고 스트림을 끝내는 연산. `toList`·`count`·`forEach`·`collect` 등.
- **지연 평가(lazy evaluation)** — 결과가 필요해질 때까지 계산을 미루는 것. 중간 연산은 언제나 지연된다.
- **단락 평가(short-circuiting)** — 답이 정해지면 나머지를 안 보고 멈추는 것. 무한 스트림을 끝낼 수 있는 수단.
- **공허한 참(vacuously true)** — 대상이 하나도 없어서 "전부 ~하다"가 반례 없이 참이 되는 것. 빈 스트림의 `allMatch`.
- **항등원(identity)** — 어떤 값과 결합해도 그 값을 그대로 돌려주는 값. 덧셈의 `0`, 곱셈의 `1`. `reduce` 의 첫 인자가 이것이어야 한다.
- **입력 순서(encounter order)** — 소스가 원소를 내놓는 순서. `List`·배열에는 있고 `HashSet` 에는 없다.
- **탈출구 연산(escape-hatch operation)** — `iterator()`·`spliterator()`. 최종 연산이면서 원소를 당장 흘려보내지 않는다.
- **부작용(side effect)** — 값을 돌려주는 것 말고 바깥 상태를 바꾸는 일(로깅·저장·카운터 증가).
- **`IllegalStateException`** — 객체가 그 호출을 받을 수 있는 상태가 아닐 때의 예외. 소비한 스트림을 다시 쓰면 난다.
- **`Optional`** — 값이 있을 수도 없을 수도 있음을 타입으로 표현한 것. `findFirst`·`min`·`max`·인자 없는 `reduce` 의 반환형.

## 더 들어가면

- **`count()` 의 최적화는 Java 9 에서 들어왔다.**\
  Java 8 에서는 `count()` 도 원소를 전부 흘려보냈다. 9부터 소스가 `SIZED` 이고 개수를 바꾸는 연산이 없으면 순회를 건너뛴다.\
  이 머신에는 8이 없어 **8의 동작은 안 돌려 봄**이다. 17·21·25 는 셋 다 건너뛴다.
- **단락 평가는 "멈춘다"이지 "즉시 멈춘다"가 아니다.**\
  병렬에서는 이미 시작된 다른 조각의 작업이 조금 더 진행될 수 있다. `findAny` 가 `findFirst` 와 다른 답을 내는 이유도 여기에 있다(49번).
- **`forEachOrdered` 의 happens-before 보장**을 javadoc 이 명시한다.

  > Performing the action for one element *happens-before* performing the action for subsequent elements, but for any given element, the action may be performed in whatever thread the library chooses.

  **순서는 보장하지만 스레드는 보장하지 않는다.** 실측에서도 `forEachOrdered` 의 액션이 워커 스레드에서 돌았고, 실행마다 1~2개 스레드가 관여했다(`main` 이 될 때도 있었다).
- **`collect` 는 최종 연산 하나일 뿐이다.** 그 안에서 무엇을 어떻게 모으는지는 `Collector` 가 정한다 — 47·48번이 그 이야기다.
