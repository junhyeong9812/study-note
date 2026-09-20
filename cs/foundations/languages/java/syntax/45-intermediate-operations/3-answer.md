# java/syntax/45 — 중간 연산: `map`/`filter`/`flatMap`/`mapMulti` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **Temurin JDK 21.0.5 에서 실제로 돌려 얻은 것**이다.\
> javadoc 인용은 `lib/src.zip` 의 `java.base/java/util/stream/Stream.java` 와 [패키지 문서](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/package-summary.html) 원문이다.\
> 17.0.13 · 25.0.1 에서도 같은 프로그램을 돌려 **출력이 한 글자도 다르지 않음**을 확인했다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 출력 순서를 한 줄씩 예측하라

**실행 결과** (`Order.java`, 17·21·25 동일)

```text
  filter apple
    map apple
  filter fig
  filter banana
    map banana
결과 [APPLE, BANANA]
```

**몇 줄이며 순서는**

- **다섯 줄.** `filter` 세 번, `map` 두 번이 **번갈아** 나온다.

**`filter` 세 줄이 먼저 나오는가**

- **아니다.** `filter apple` 다음 줄이 바로 `map apple` 이다.

```text
잘못된 기대 — 작업대별                      실제 — 원소별

  filter apple   \                          filter apple   \  apple 이
  filter fig      | filter 를 다 하고        map apple      /  끝까지 간다
  filter banana  /                          filter fig        <- 탈락
    map apple    \  그 다음 map             filter banana  \  banana 가
    map banana   /                            map banana   /  끝까지 간다
```

**`fig` 에 대해 `map` 이 안 나오는 이유**

- `filter` 에서 **탈락했기 때문**이다.
- 탈락한 원소는 뒤쪽 연산으로 **넘어가지 않는다** — 비용이 0이다.
- 이것이 「연산 순서가 곧 비용」의 근거다(8번).

**이 실행 방식의 이름과 메모리 함의**

- **원소 단위 통과(element-at-a-time)**, 또는 스트림 융합(fusion).
- 메모리 함의: **중간 결과 컬렉션이 안 생긴다.**\
  `filter` 결과를 리스트에 담고 그걸 `map` 하는 게 아니다.
- 그래서 원소가 천만 개여도 메모리에 있는 것은 **한 번에 원소 하나**다.\
  `sorted`·`distinct` 같은 상태 있는 연산이 끼기 전까지는(7번).

> **원소 단위 통과(element-at-a-time)** — 원소 하나가 파이프라인 끝까지 간 뒤 다음 원소가 시작되는 실행 방식.\
> 예: 컨베이어 벨트에서 물건 하나가 작업대를 전부 지나간 뒤 다음 물건이 올라오는 것.

### 2. 최종 연산을 `findFirst` 로 바꾸면

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

**몇 줄이며 무엇인가**

- **두 줄.** `filter apple` 과 `map apple`.

**`banana` 는 처리되는가**

- **아니다.** `fig` 도 마찬가지다.
- 소스에서 **꺼내지지도 않았다** — `filter` 가 안 불렸다는 것이 그 증거다.

```text
toList()                                  findFirst()

  apple  -> filter -> map -> 수집           apple -> filter -> map -> 답
  fig    -> filter -> 탈락                            |
  banana -> filter -> map -> 수집                     v
                                            fig, banana 는 소스에서 안 읽는다
  filter 3회 / map 2회                      filter 1회 / map 1회
```

**`Stream.iterate` 의 람다는 몇 번 불리는가**

- **세 번**이다. 출력이 `next from 1`·`next from 2`·`next from 4` 로 세 줄.

**4가 아닌 이유**

```text
Stream.iterate(1, f).limit(4)

  원소 1: 씨앗(seed) 그대로       -> f 호출 0회
  원소 2: f(1) = 2               -> f 호출 1회  (next from 1)
  원소 3: f(2) = 4               -> f 호출 2회  (next from 2)
  원소 4: f(4) = 8               -> f 호출 3회  (next from 4)
                                    합 3회
```

- **첫 원소는 씨앗**이므로 함수가 필요 없다.
- n 개를 만들려면 함수가 **n-1 번** 불린다.
- 그리고 다섯 번째 원소를 위한 `f(8)` 은 **불리지 않았다** — `limit` 가 정확히 필요한 만큼만 당겨 온다.

### 3. `map` 과 `flatMap`

**실행 결과** (`Flat.java`)

```text
map     : 3 개 (원소가 Stream 객체다)
map 타입: Stream<Stream<Integer>>
flatMap : [1, 2, 3]
map     : 2 개 (원소가 String[] 이다)
flatMap : [a, b, c, d]
```

**`map(List::stream)` 의 타입과 개수**

- 타입: **`Stream<Stream<Integer>>`**
- 원소 개수: **3개** — 전부 `Stream` 객체다. 안에 든 숫자가 아니다.

**`flatMap(List::stream).toList()`**

- **`[1, 2, 3]`**

```text
nested = [[1,2], [3], []]

  map(List::stream)                        flatMap(List::stream)

  [1,2] -> Stream@a   \                     [1,2] -> 열어서 1, 2 를 쏟는다
  [3]   -> Stream@b    | 3개 그대로          [3]   -> 열어서 3 을 쏟는다
  []    -> Stream@c   /                     []    -> 쏟을 게 없다
         |                                         |
         v                                         v
  Stream<Stream<Integer>> (3개)             Stream<Integer> (3개: 1,2,3)
```

- **`map` 은 개수를 바꾸지 않는다** — 3개가 들어가면 3개가 나온다.
- **`flatMap` 은 한 겹을 벗긴다** — 개수가 바뀐다.

**빈 리스트는 어떻게 나타나는가**

- **사라진다.** `[]` 에서 쏟아질 원소가 없다.
- `map` 쪽에서는 **빈 `Stream` 객체 하나**로 남아 개수에 포함된다(3개 중 하나).
- 이 성질 덕에 `flatMap` 으로 **거르기**가 가능하다(4번).

**판단 기준 한 줄**

> **람다가 `Stream`(또는 컬렉션·배열)을 돌려주면 `flatMap`, 값 하나를 돌려주면 `map`.**

**`map` 을 잘못 써도 컴파일되는 경우**

- **뒤 연산이 `Object` 를 받을 때**다.

```java
nested.stream().map(List::stream).forEach(System.out::println);
// java.util.stream.ReferencePipeline$Head@... 가 찍힌다
```

- `String.valueOf`·`println`·`Objects.toString` 처럼 `Object` 를 받는 자리는 **무엇이든 받는다.**
- `String[]` 을 원소로 남긴 경우도 같다 — 실행 결과의 `map : 2 개 (원소가 String[] 이다)` 가 그것이다.\
  `println` 에 넘기면 `[Ljava.lang.String;@...` 가 찍힌다.
- 즉 **컴파일러가 안 잡아 주는 경로가 있다.** 결과 타입을 눈으로 확인한다.

### 4. `flatMap` 으로 할 수 있는 세 가지

**실행 결과** (`Flat.java`)

```text
flatMap 으로 거르기 : [2, 4]
flatMap 으로 불리기 : [1, 10, 2, 20]
map 은 null 통과   : [a, null, c]
flatMap 으로 제거  : [a, c]
```

**`flatMap(i -> i%2==0 ? Stream.of(i) : Stream.empty())`**

- **`[2, 4]`**

**어느 연산과 같은 일인가**

- **`filter(i -> i % 2 == 0)`** 과 같다.

```text
flatMap 으로 거르기                         filter

  1 -> Stream.empty()  -> 사라짐             1 -> false -> 사라짐
  2 -> Stream.of(2)    -> 2                  2 -> true  -> 2
  3 -> Stream.empty()  -> 사라짐             3 -> false -> 사라짐
  4 -> Stream.of(4)    -> 4                  4 -> true  -> 4
```

- 결과는 같지만 **`filter` 를 쓴다.** 의도가 드러나고 스트림 객체도 안 만든다.
- `flatMap` 으로 거르는 게 의미 있는 경우는 **거르기와 변환을 한 번에** 할 때다.\
  예: 파싱에 성공한 것만 변환된 값으로 내보내기.

**`null` 이 섞였을 때**

- `map(s -> s)` -> **`[a, null, c]`** — `null` 이 그대로 통과한다.
- `flatMap(Stream::ofNullable)` -> **`[a, c]`** — `null` 이 빈 스트림이 되어 사라진다.
- `Stream.ofNullable` 은 **Java 9** 부터다.

**람다가 `null` 을 돌려주면**

**실행 결과** (`Edge.java`)

```text
flatMap 이 null 을 돌려주면 : [2]
```

- **NPE 가 아니라 빈 스트림으로 처리**된다.
- javadoc 원문이 그렇게 적고 있다.

> Each mapped stream is closed after its contents have been placed into this stream. **(If a mapped stream is `null` an empty stream is used, instead.)**

- 관대해 보이지만 **버그를 숨긴다** — 매퍼가 실수로 `null` 을 돌려줘도 조용히 원소가 사라진다.
- 의도적으로 "없음"을 표현하려면 `Stream.empty()` 를 명시한다.

### 5. `flatMap` 과 단락 평가

**실행 결과** (`FlatLazy.java`, **17 · 21 · 25 동일**)

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

**`안쪽` 은 몇 줄인가**

- **한 줄.** `안쪽 1` 만.

**바깥 스트림은 몇 원소를 읽는가**

- **하나.** `바깥 [1, 2, 3]` 한 줄만 나왔다. `[4, 5]` 는 안 열었다.

```text
nested = [[1,2,3],[4,5]] 에 findFirst

  바깥 [1,2,3]  -> 안쪽 스트림을 연다
                    안쪽 1 -> 찾았다 -> 전체 멈춤
  안쪽 2, 3     -> 읽지 않는다
  바깥 [4,5]    -> 열지도 않는다
```

**`.limit(2)` 로 바꾸면**

- **두 줄** (`안쪽 1`, `안쪽 2`).
- 필요한 만큼만 더 읽었다. 여전히 바깥은 하나만 열었다.

**17·21·25 에서 같은가**

- **같다.** 세 JDK 에서 출력이 동일했다.
- 이 단락 평가가 처음부터 있었던 것은 아니라고 알려져 있지만, **이 머신의 세 JDK 로는 다른 동작을 재현할 수 없다.**\
  그러므로 "Java 8 초기에는 달랐다"는 이 문서에서 **확인하지 못한 주장**으로 둔다.
- 실무 함의: 21 이상을 쓴다면 중첩 구조에서도 `findFirst`·`limit` 를 믿고 쓸 수 있다.

### 6. `mapMulti`

**버전**

- **Java 16** 부터.

**`flatMap` 과 내부에서 무엇이 다른가**

```text
flatMap                                   mapMulti
  i -> Stream.of(i, i*10)                 (i, sink) -> { sink.accept(i);
                                                         sink.accept(i*10); }

  원소마다 Stream 객체 1개 생성             Stream 객체 0개
  그 스트림을 다시 소비                     sink 에 바로 밀어 넣는다
```

**실행 결과** (`Flat.java`)

```text
flatMap 으로 불리기 : [1, 10, 2, 20]
mapMulti 같은 일   : [1, 10, 2, 20]
flatMap 으로 거르기 : [2, 4]
mapMulti 로 거르기 : [2, 4]
mapMultiToInt      : 6
```

- 결과는 완전히 같다. **다른 것은 중간에 만들어지는 객체 수**뿐이다.
- `mapMultiToInt` 는 `Stream<String>` 에서 바로 `IntStream` 으로 건너간다 — `"1,2"`·`"3"` 을 쪼개 합이 `6`.

**`sink.accept` 를 안 부르면**

- 그 원소는 **사라진다.** `filter` 를 겸하는 셈이다.
- `mapMulti 로 거르기 : [2, 4]` 가 그 결과다 — 홀수에서는 `accept` 를 안 불렀다.

**`mapToInt(x -> x)` 를 붙이면 컴파일되는가**

- **안 된다.**

```text
$ javac MM3.java
MM3.java:5: error: incompatible types: bad return type in lambda expression
                        .mapToInt(x -> x)
                                       ^
    Object cannot be converted to int
```

**에러가 어느 줄에서 나며 어떻게 고치는가**

- **`mapMulti` 줄이 아니라 그 다음 줄**에서 난다.
- `mapMulti` 자체는 통과한다 — 결과 타입 `R` 이 **`Object` 로 추론**될 뿐이다.
- 그래서 메시지가 원인을 안 가리킨다.\
  "`Object cannot be converted to int`" 만 보고 `mapMulti` 를 의심하기 어렵다.
- 고치는 법: **타입 인자를 명시**한다.

```java
Stream.of(1, 2).<Integer>mapMulti((i, sink) -> { sink.accept(i * 10); })
               .mapToInt(x -> x)
               .sum();                       // 실행 결과: sum = 30
```

- **입력 타입은 제대로 추론된다** — `Stream.of("1,2","3").mapMulti((s, sink) -> s.split(","))` 에서 `s` 는 `String` 으로 추론되어 캐스팅이 필요 없다(`MM4.java` 로 확인).
- 문제는 **출력 쪽**뿐이다. 근거가 람다 본문밖에 없기 때문이다.

### 7. `sorted` 를 끼우면

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

**(A)와 (B)의 순서**

- (A) — `map`/`forEach` 가 **번갈아** 나온다.
- (B) — `map` 세 줄이 **먼저 다 나오고** 그 뒤에 `forEach` 세 줄이 **정렬된 순서로** 나온다.

**`sorted` 가 그렇게 만드는 이유**

```text
상태 없는 연산                             상태 있는 연산 (sorted)

  [3] -> map -> forEach                    [3] -> map -> 버퍼
  [1] -> map -> forEach                    [1] -> map -> 버퍼
  [2] -> map -> forEach                    [2] -> map -> 버퍼
                                                          | 입력이 끝나야
  원소 하나만 보면 결과를 낼 수 있다                          v 첫 결과가 나온다
                                                     정렬 -> forEach 1,2,3
```

- **첫 결과를 내려면 마지막 입력까지 봐야 한다.**\
  아직 안 본 원소가 최솟값일 수 있기 때문이다.
- 그래서 `sorted` 는 **파이프라인의 장벽(barrier)** 이 된다.

**무한 스트림에 쓸 수 없는 이유**

- 입력이 안 끝나므로 **버퍼가 영원히 안 찬다.**
- 그리고 그 버퍼가 힙을 채운다.

**`Stream.iterate(...).sorted().limit(5)`**

**실행 결과** (`SortedInf.java`, `-Xmx64m`)

```text
limit 를 sorted 앞에: [1, 2, 3, 4, 5]
이제 sorted 를 앞에 둔다
Exception in thread "main" java.lang.OutOfMemoryError: Java heap space
	at java.base/java.util.Arrays.copyOf(Arrays.java:3513)
	at java.base/java.util.ArrayList.grow(ArrayList.java:237)
```

- **`OutOfMemoryError`** 로 죽는다. `limit` 가 뒤에 있어도 소용없다.
- 스택트레이스가 `ArrayList.grow` 를 가리킨다 — `sorted` 가 쌓던 버퍼다.
- `limit` 를 `sorted` **앞**에 두면 정상으로 끝난다.

**네 연산은 어느 쪽인가**

- `map`·`filter`·`flatMap`·`mapMulti` 는 **전부 상태 없는 연산**이다.
- 그래서 이 넷만으로 이루어진 파이프라인은 **무한 스트림에서도 안전**하다.
- 상태 있는 중간 연산: `sorted`·`distinct`·`limit`·`skip`.\
  단 `limit` 는 상태가 있지만 **단락 평가**라 무한 스트림을 끝낼 수 있다.

### 8. 연산의 위치가 비용을 바꾼다

**실행 결과** (`Placement.java`)

```text
map -> filter : 결과 [APPLE, BANANA] / map 호출 4회
filter -> map : 결과 [APPLE, BANANA] / map 호출 2회
```

**결과는 같은가**

- **같다.** 둘 다 `[APPLE, BANANA]`.

**`map` 람다는 몇 번 불리는가**

- (A) `map -> filter` — **4회**
- (B) `filter -> map` — **2회**

```text
(A) map 먼저                              (B) filter 먼저

  apple  -> MAP -> 길이 5 -> 통과           apple  -> 길이 5 -> MAP
  fig    -> MAP -> 길이 3 -> 버림  <- 낭비   fig    -> 길이 3 -> 버림 (MAP 안 함)
  banana -> MAP -> 길이 6 -> 통과           banana -> 길이 6 -> MAP
  kiwi   -> MAP -> 길이 4 -> 버림  <- 낭비   kiwi   -> 길이 4 -> 버림 (MAP 안 함)

  map 4회 (그중 2회는 순수 낭비)             map 2회
```

**테스트에서 안 드러나는 이유**

- **결과가 같기 때문**이다. 출력을 검사하는 테스트는 둘 다 통과한다.
- 드러나는 것은 **`map` 안이 비싼 일일 때**뿐이다 — DB 조회, HTTP 호출, 암복호화, 대용량 변환.
- 그리고 그때는 보통 **운영에서** 드러난다. 테스트 데이터는 작기 때문이다.
- 이것도 **조용한 낭비**다 — 답은 맞고 비용만 두 배다.

**순서를 못 바꾸는 경우와 대처**

- `filter` 의 조건이 **변환 결과**에 걸려 있을 때다.

```java
// 조건이 parse 결과에 걸려 있다 — filter 를 앞에 둘 수 없다
src.stream().map(this::parse).filter(r -> r.isValid()).toList();
```

- 이때 `map` 을 앞으로 뺄 수 없으므로 **두 번 변환하지 않게** 묶는다.

```java
// mapMulti 로 한 번에 — 유효한 것만 내보낸다
src.stream().<Result>mapMulti((s, sink) -> {
    Result r = parse(s);
    if (r.isValid()) sink.accept(r);
}).toList();
```

- `flatMap` 으로도 같은 일을 할 수 있다(4번).\
  차이는 내부 스트림 객체뿐이다.

### 9. 중간 연산에 무엇을 넣지 말아야 하나

**`map` 안에서 로그·저장을 하면 보장되지 않는 것**

- **실행 여부**와 **실행 순서** 둘 다 보장되지 않는다.
- 44번에서 실행으로 확인했다 — `Stream.of("a","b").peek(print).count()` 는 **`peek` 를 0회 실행**했다.
- 병렬 스트림이면 순서도 잃는다(목록의 **49번 주제**).

**javadoc 근거**

> The eliding of side-effects may also be surprising. With the exception of terminal operations `forEach` and `forEachOrdered`, **side-effects of behavioral parameters may not always be executed when the stream implementation can optimize away the execution of behavioral parameters without affecting the result of the computation.**

- **`forEach` 와 `forEachOrdered` 만 예외**라고 못박았다.
- 뒤집어 말하면 **그 둘만이 부작용을 넣어도 되는 자리**다.

**`peek` 는 무엇을 위한 메서드인가**

JDK 21.0.5 `Stream.java` 의 `@apiNote` 원문이다.

> This method exists mainly to support debugging, where you want to see the elements as they flow past a certain point in a pipeline

- **디버깅용**이라고 명시돼 있다.
- 실행이 보장되지 않으므로 운영 코드에 남기지 않는다.

**원소 개수를 세려면**

- **`count()`** 최종 연산, 또는 `Collectors.counting()` 다운스트림(목록의 **48번 주제**).
- `map` 안에서 `AtomicInteger` 를 올리는 방식은 쓰지 않는다.\
  실행 횟수가 보장되지 않으니 **세는 값 자체가 틀릴 수 있다.**

**`distinct()` 는 무엇에 기대는가**

**실행 결과** (`Edge.java`)

```text
distinct, hashCode 없음 : [N1, N1]
distinct, hashCode 있음 : [W1]
```

- **`equals` 와 `hashCode`** 에 기댄다.
- 계약이 깨진 객체면 **중복이 안 걸러진다** — 위 첫 줄이 그 증거다.\
  `equals` 로는 같은 두 객체가 둘 다 남았다.
- 예외도 경고도 없다. **조용히 중복이 통과한다.**
- 그 계약은 [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) 이 정본이다.

---

## 이 주제를 확인한 실행 목록

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Order` | 원소 단위 통과, `findFirst` 의 단락 평가, `iterate` 람다 호출 횟수 | 17 · 21 (동일) |
| `Flat` | `map` vs `flatMap` 의 개수·타입, `flatMap` 의 세 쓰임, `mapMulti` | 17 · 21 (동일) |
| `FlatLazy` | `flatMap` 이 안쪽·바깥 스트림을 필요한 만큼만 읽음 | 17 · 21 · 25 (동일) |
| `Stateful` | `sorted` 가 장벽이 됨, `takeWhile`/`dropWhile`/`filter` 의 차이 | 21 |
| `Placement` | 연산 순서가 `map` 호출 횟수를 두 배로 바꿈 | 21 |
| `Edge` | `flatMap` 이 `null` 을 빈 스트림으로, `distinct` 가 `hashCode` 에 기댐 | 21 |
| `MM3` / `MM4` / `MM5` `javac` | `mapMulti` 의 출력 타입이 `Object` 로 추론됨, 입력은 정상 추론 | 21 |
| `SortedInf` | `sorted` 뒤의 `limit` 는 OOM, 앞이면 정상 (44번과 공유) | 21 |
| `src.zip` 열람 | `peek` 의 `@apiNote`, `flatMap` 계열의 "closed / null -> empty" | 21 |
