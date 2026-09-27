# java/syntax/46 — 최종 연산과 지연 평가·단락 평가 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **Temurin JDK 21.0.5 에서 실제로 돌려 얻은 것**이다.\
> javadoc 인용은 `lib/src.zip` 의 `java.base/java/util/stream/Stream.java`·`package-info.java` 와 [패키지 문서](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/package-summary.html) 원문이다.\
> 17.0.13 · 25.0.1 에서도 같은 프로그램을 돌렸다 — **스택트레이스 줄 번호 말고는 출력이 전부 같았다**(11번).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 이 두 블록의 출력 줄 수를 예측하라

**출력**

```text
== (1) 최종 연산 없음 ==
(여기까지 filter 가 한 줄도 없어야 한다)
== (2) 최종 연산 있음 ==
  filter a
  filter b
  filter c
결과 [a, b, c]
```

**왜 그런가**

- (A) — **0줄.** `filter` 의 람다가 한 번도 불리지 않았다.
- (B) — **3줄.** `toList()` 라는 최종 연산이 붙어서야 원소가 흐른다.

```text
(A) 최종 연산 없음                        (B) 최종 연산 있음

  소스 [a][b][c]                          소스 [a][b][c]
        |                                       |
   filter 스테이지 생성                     filter 스테이지 생성
        |                                       |
   (끝. 순회가 시작되지 않는다)            toList() 가 순회를 시작한다
        |                                       |
   람다 0회 · 출력 0줄                      람다 3회 · 출력 3줄
```

**예외나 경고가 나는가**

- **아니다.** 컴파일 경고도, 런타임 예외도 없다.
- `filter` 가 돌려준 `Stream` 을 버리는 것은 문법적으로 완전히 정상이다.

**javadoc 근거**

> Intermediate operations return a new stream. They are always *lazy*; executing an intermediate operation such as `filter()` does not actually perform any filtering, but instead creates a new stream that, when traversed, contains the elements of the initial stream that match the given predicate. **Traversal of the pipeline source does not begin until the terminal operation of the pipeline is executed.**

**실무에서 드러나는 증상**

```java
users.stream().filter(User::isActive).map(this::save);   // 저장이 안 된다
```

- **데이터가 그냥 안 들어간다.** 로그도 에러도 없다.
- 이것이 이 주제에서 가장 비싼 함정이다 — 조용하고, 배포 뒤에 발견된다.
- 방어: 저장·로깅은 `forEach` 에서 한다. 중간 연산에 부작용을 넣지 않는다.

### 2. 네 가지 단락 연산의 호출 횟수

**출력** (`Ex.java` — 46-a)

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

**각각 몇 번인가**

| 연산 | `peek` 횟수 | 멈춘 이유 |
|---|---|---|
| `findFirst()` | **1** | 첫 원소가 곧 답이다 |
| `anyMatch(짝수)` | **2** | `2` 에서 `true` 가 나왔다 |
| `allMatch(3 미만)` | **3** | `3` 에서 `false` 가 나왔다 |
| `noneMatch(==2)` | **2** | `2` 에서 `true` 가 나왔다 |

```text
입력 [1, 2, 3, 4, 5]

  anyMatch(짝수)     1 아니다 -> 2 맞다!  -> true      3,4,5 안 봄
  allMatch(3 미만)   1 맞다 -> 2 맞다 -> 3 아니다 -> false   4,5 안 봄
  noneMatch(==2)     1 아니다 -> 2 맞다!  -> false     3 안 봄
```

**`allMatch` 가 멈추는 조건**

- **첫 `false`** 다. 하나라도 안 맞으면 나머지를 볼 필요가 없다.

**`noneMatch` 가 멈추는 조건**

- **첫 `true`** 다. 하나라도 맞으면 "하나도 안 맞는다"가 깨진다.

**단락 평가를 하는 최종 연산 전부**

- `findFirst` · `findAny` · `anyMatch` · `allMatch` · `noneMatch` — **다섯**이다.
- 나머지(`toList`·`count`·`forEach`·`reduce`·`collect`·`min`·`max`·`sum`)는 전부를 본다.

**최종 연산만의 성질인가**

- **아니다.** 중간 연산 `limit(n)` 과 `takeWhile(p)`(9+)도 단락 평가다.
- 그래서 `Stream.iterate(...).limit(4).toList()` 가 끝난다 — 최종 연산은 단락이 아닌데도.

### 3. 빈 스트림에서 무엇이 나오는가

**출력** (`Ex.java` — 46-b)

```text
== 빈 스트림에서의 세 술어 ==
anyMatch  : false
allMatch  : true
noneMatch : true
== reduce 세 형태 ==
빈 스트림 + 항등원   : 0
빈 스트림 항등원 없음 : Optional.empty
== Optional 을 돌려주는 최종 연산 ==
빈 min    : Optional.empty
빈 findFirst : Optional.empty
== 값을 그냥 돌려주는 최종 연산 ==
빈 count  : 0
빈 IntStream sum : 0
빈 IntStream max : OptionalInt.empty
```

**`anyMatch` / `allMatch`**

- `anyMatch` → **`false`** (맞는 게 하나도 없다)
- `allMatch` → **`true`** (반례가 하나도 없다)

**그 답을 뭐라고 부르는가**

> **공허한 참(vacuously true)** — 대상이 하나도 없을 때 "전부 ~하다"가 반례가 없어 참이 되는 것.\
> 예: 빈 바구니에 대고 "이 안의 사과는 전부 빨갛다"고 해도 틀렸다고 할 수가 없다.

- 실무 함정: **필터로 다 걸러진 빈 스트림에 `allMatch(유효성검사)` 를 걸면 검증이 통과해 버린다.**\
  "하나 이상 있고 전부 유효하다"를 원했다면 개수 검사를 따로 해야 한다.

**`reduce` 두 형태**

| 형태 | 반환 타입 | 빈 스트림에서 |
|---|---|---|
| `reduce(0, Integer::sum)` | `Integer` (값 그대로) | `0` — 항등원이 기본값 |
| `reduce(Integer::sum)` | `Optional<Integer>` | `Optional.empty` |

**`sum()` 과 `max()` 가 갈리는 이유**

```text
합                                        최댓값

  항등원이 있다 — 0                        항등원이 없다
  "아무것도 안 더한 합" = 0                 "아무것도 없을 때의 최댓값" = ???
        |                                        |
        v                                        v
  0 을 돌려주면 된다                        없음을 표현해야 한다 -> Optional
```

- `sum()` → `0`, `average()`·`max()`·`min()` → `Optional*`.
- 빈 스트림의 합이 `0` 인 것은 **규약이지 우연이 아니다** — 덧셈의 항등원이 0이기 때문이다.

### 4. 최종 연산이 있는데도 중간 연산이 안 돈다

**출력** (`Ex.java` — 46-a)

```text
== (7) 단락이 아닌 최종 연산 — count 는 전부 본다? ==
결과 3
  peek-filter-count a
  peek-filter-count b
  peek-filter-count c
결과 3
```

**(A)는 몇 번인가**

- **0번.** 첫 `결과 3` 위에 아무 줄도 없다.

**(B)는 몇 번인가**

- **3번.**

**둘 다 `count()` 인데 왜 다른가**

```text
(A) peek.count()                          (B) filter.peek.count()

  소스 Stream.of(3개) -> SIZED             filter 가 개수를 바꿀 수 있다
  peek 는 개수를 안 바꾼다                   몇 개가 통과할지 돌려 봐야 안다
        |                                        |
        v                                        v
  "3" 을 바로 돌려준다                      원소를 실제로 흘려보낸다
  peek 0회                                  peek 3회
```

- **소스가 크기를 알고(`SIZED`), 그 뒤 연산이 개수를 안 바꾸면** `count()` 는 순회를 건너뛴다.
- `filter` 는 개수를 바꿀 수 있으므로 그 최적화가 깨진다.
- 즉 **파이프라인 모양이 부작용의 실행 횟수를 바꾼다.**

**언어 보장인가 구현 세부인가**

- **구현 세부다.** javadoc 은 "부작용이 **항상 실행되지는 않을 수 있다**"고만 적는다.

> With the exception of terminal operations `forEach` and `forEachOrdered`, **side-effects of behavioral parameters may not always be executed when the stream implementation can optimize away the execution of behavioral parameters without affecting the result of the computation.**

- 뒤집어 읽으면 **`forEach`·`forEachOrdered` 만이 부작용을 넣어도 되는 자리**다.

**`peek` 디버깅에서 조심할 것**

- **안 찍혔다는 것이 "파이프라인이 안 돌았다"의 증거가 못 된다.**
- 디버깅할 때는 최종 연산을 `toList()` 로 바꿔 놓고 본다.
- `peek` 는 javadoc 이 "This method exists mainly to support debugging" 이라 적은 **디버깅 전용**이다. 운영 코드에 남기지 않는다.

### 5. 무한 스트림이 끝나는 조건

**출력** (`Ex.java` — 46-c)

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

**몇 줄이며 결과는**

- **세 줄** (`next from 1`·`2`·`4`), 결과는 `[1, 2, 4, 8]`.

**4가 아닌 이유**

```text
Stream.iterate(1, f).limit(4)

  원소 1: 씨앗 그대로      -> f 호출 0회
  원소 2: f(1) = 2        -> f 호출 1회  (next from 1)
  원소 3: f(2) = 4        -> f 호출 2회  (next from 2)
  원소 4: f(4) = 8        -> f 호출 3회  (next from 4)
  원소 5: 요청이 없다       -> f(8) 은 안 불린다
                             합 3회
```

- **첫 원소는 씨앗**이라 함수가 필요 없다. n 개를 만들려면 **n-1 번**.
- 다섯 번째를 위한 `f(8)` 은 **불리지 않았다** — `limit` 이 딱 필요한 만큼만 당긴다.

**밀어내는가 당겨 오는가**

- **최종 연산이 당겨 온다(pull).**
- 이것이 무한 스트림이 성립하는 이유 전부다.\
  소스가 밀어내는 구조였다면 `Stream.iterate` 는 만들 수 없다.

**`Stream.iterate(1, i -> i + 1).count()`**

- **끝나지 않는다.** `count()` 는 단락 평가가 아니라 전부를 봐야 한다.
- `toList()`·`sorted()`·`max()` 도 같다.\
  `sorted()` 는 44번 7번에서 실행으로 확인했듯 **`OutOfMemoryError`** 로 죽는다(버퍼를 쌓기 때문).
- 규칙: **무한 소스에는 단락 평가를 짝지어 둔다.**

**`limit` 는 최종 연산인가**

- **아니다. 중간 연산이다.** 단락 평가이면서 중간 연산이다.

**출력** (`Ex.java` — 46-c)

```text
== limit 가 최종 연산이 아니라는 증거 ==
limit 만 붙인 상태 — 위에 아무 줄도 없다
  안 나와야 한다 1
  안 나와야 한다 2
이제 소비 : [1, 2, 3]
```

- `limit(3)` 만 붙여 놓았을 때는 **한 줄도 안 나왔다.** 최종 연산이 붙어서야 돌았다.

### 6. 스트림을 두 번 건드리면

**출력** (`Ex.java` — 46-d)

```text
== (1) 최종 연산 두 번 ==
첫 소비 : 2
두 번째 : java.lang.IllegalStateException: stream has already been operated upon or closed
== (2) 중간 연산으로 가지를 친다 ==
둘째 가지 : java.lang.IllegalStateException: stream has already been operated upon or closed
== (3) 소비한 스트림에 중간 연산을 붙이면 ==
소비 뒤 filter : java.lang.IllegalStateException: stream has already been operated upon or closed
```

**어느 줄에서 무엇이 던져지는가**

- **셋째 줄** — `Stream<String> b = s.map(x -> x + "!");` 에서 `IllegalStateException`.
- 최종 연산을 부르기도 전에 **중간 연산을 붙이는 시점**에 던진다.

**같은 예외인가**

- **같다.** 타입도 메시지도 세 경우 모두 동일하다.
- 즉 스트림은 최종 연산이 일회용인 게 아니라 **연결 자체가 일회용**이다.

```text
되는 것                                   안 되는 것

  src.stream().map(f).toList();            Stream<T> s = src.stream();
  src.stream().map(g).toList();            s.map(f);
   (소스에서 두 번 만든다)                    s.map(g);   <- 던진다

                                           s.toList();
                                           s.count();  <- 던진다
```

**메시지**

```text
stream has already been operated upon or closed
```

**다시 보려면**

- **소스를 들고 있다가 `stream()` 을 새로 부른다.**
- 스트림 자체를 복제하는 방법은 없다.

**반환값으로 돌려줘야 한다면**

```java
// 위험 — 호출자가 둘이면 둘째가 터진다
Stream<User> all() { return this.cachedStream; }

// 안전 — 부를 때마다 새 스트림
Stream<User> all() { return users.stream(); }

// 안전 — 지연이 필요하면 Supplier
Supplier<Stream<User>> all() { return users::stream; }
```

- 실무 함정: **호출 순서에 따라 터진다.** 테스트 하나만 돌리면 통과한다.

**스택트레이스 원문** (`Ex.java` — 46-d, JDK 21.0.5)

```text
Exception in thread "main" java.lang.IllegalStateException: stream has already been operated upon or closed
	at java.base/java.util.stream.AbstractPipeline.evaluateToArrayNode(AbstractPipeline.java:246)
	at java.base/java.util.stream.ReferencePipeline.toArray(ReferencePipeline.java:616)
	at java.base/java.util.stream.ReferencePipeline.toArray(ReferencePipeline.java:622)
	at java.base/java.util.stream.ReferencePipeline.toList(ReferencePipeline.java:627)
	at Ex.main(Ex.java:36)
```

### 7. `forEach` 와 `forEachOrdered`

**출력** (`Ex.java` — 46-e, 입력 1~12)

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

**(A)와 (B)**

- **둘 다 `1 2 3 ... 12`.** 순차에서는 구별되지 않는다.

**(C)와 (D)**

- (C) `forEach` — **뒤섞인다.** 세 번 다 다른 순서였다.
- (D) `forEachOrdered` — **입력 순서 그대로.**

**실행마다 달라지는 것**

- **(C)뿐이다.**

```text
순차 스트림                               병렬 스트림

  forEach        1 2 3 ... 12              forEach        실행마다 다르다
  forEachOrdered 1 2 3 ... 12              forEachOrdered 1 2 3 ... 12
        |                                         |
   차이가 안 보인다                          여기서만 차이가 드러난다
   (그래서 무심코 forEach 를 쓴다)
```

**javadoc 이 특별 취급하는 이유**

- 4번에서 본 문장이 **이 둘만을 예외로 뺐다** — 부작용이 실행되는 것이 보장되는 유일한 두 연산이다.
- 그리고 둘의 계약이 정반대로 적혀 있다.

> (`forEach`) **The behavior of this operation is explicitly nondeterministic.** For parallel stream pipelines, this operation does *not* guarantee to respect the encounter order of the stream, as doing so would sacrifice the benefit of parallelism.

> (`forEachOrdered`) Performs an action for each element of this stream, **in the encounter order of the stream if the stream has a defined encounter order.**

**`forEachOrdered` 가 치르는 대가**

**실행 결과** (`Ex.java` — 49-h, 1000만 개 `int[]`, 마이크로초 중앙값)

```text
  병렬 forEach                                 8472
  병렬 forEachOrdered                        125047
  순차 forEach                               116889
```

- **15배**다. 그리고 `forEachOrdered` 는 **순차와 거의 같다** — 병렬의 이득을 사실상 전부 반납한다.
- 측정 방법과 한계는 [`../49-parallel-streams/`](../49-parallel-streams/) 가 정본이다.
- 그래서 순서가 필요하면 **`forEachOrdered` 보다 `collect` 로 모아서 나중에 순회**하는 쪽이 보통 낫다.

### 8. 최종 연산이 스트림을 닫는가

**출력** (`Ex.java` — 46-f)

```text
== onClose 는 최종 연산이 부르지 않는다 ==
toList : [a, b]
(위에 「닫혔다」가 없다)
== 직접 close() 하면 ==
toList : [a, b]
  닫혔다
== try-with-resources ==
toList : [a, b]
  닫혔다(twr)
```

**`닫혔다` 가 출력되는가**

- **아니다.** 최종 연산은 스트림을 **소비 완료** 상태로 만들 뿐 `close()` 를 부르지 않는다.

**언제 출력되는가**

- `close()` 를 직접 부르거나 `try`-with-resources 로 감쌌을 때.

**`Files.lines` 를 닫지 않으면**

**출력** (`Ex.java` — 46-f)

```text
== 닫지 않은 Files.lines (파일 핸들이 남는다) ==
첫 줄 : 1
(예외는 없다 — 조용히 샌다)
```

- **예외가 나지 않는다.** 결과도 정상으로 나온다.
- 파일 핸들이 남을 뿐이다 — 반복되면 `Too many open files` 로 **엉뚱한 자리에서** 터진다.
- 전형적인 무음 실패다.

**`try`-with-resources 가 필요한 스트림**

- **바깥 자원을 잡는 스트림만** — `Files.lines`·`Files.walk`·`Files.list`·`Files.find`·JDBC 결과 스트림 등.
- 컬렉션·배열·`Stream.of`·`IntStream.range` 는 잡는 자원이 없어 **닫지 않아도 된다.**
- 판단 기준: **만드는 메서드가 `IOException` 을 던지면 대개 닫아야 한다.**

### 9. `iterator()` 는 어느 쪽인가

**출력** (`Ex.java` — 46-b)

```text
== iterator 도 최종 연산이다 ==
iterator() 를 부른 직후 — 위에 peek 가 없어야 한다
  peek a
첫 next() : a
iterator 뒤 재사용 : java.lang.IllegalStateException: stream has already been operated upon or closed
```

**직후 `peek` 는 몇 번인가**

- **0번.** `iterator()` 를 부른 것만으로는 원소가 흐르지 않는다.
- `next()` 를 부른 순간 `peek a` 가 찍혔다.

**중간 연산인가 최종 연산인가**

- **최종 연산이다.** 스트림이 소비 완료로 표시된다.
- 다만 **원소를 당장 흘려보내지 않는 유일한 최종 연산**이다 — `next()` 마다 한 개씩 흐른다.

**그 뒤 `s.count()` 를 부르면**

- `IllegalStateException: stream has already been operated upon or closed`.

**javadoc 이 뭐라고 부르는가**

> Except for the **escape-hatch operations** `iterator()` and `spliterator()`, execution begins when the terminal operation is invoked, and ends when the terminal operation completes.

- **탈출구 연산(escape-hatch operation)** 이다.
- 이름대로 스트림 모델을 빠져나가는 통로다 — 원소를 직접 당겨 쓸 수 있게 해 준다.
- 실무에서는 거의 안 쓴다. 쓰게 됐다면 **애초에 `for` 가 맞는 자리**일 가능성이 높다.

### 10. 어느 최종 연산을 고르는가

**"하나라도 있나"**

- **`anyMatch(p)`**.
- `filter(p).findFirst().isPresent()` 도 같은 답을 내지만 의도가 덜 드러난다.
- `count() > 0` 은 **쓰지 않는다** — 전부를 보므로 단락 평가를 잃는다.

**결과를 수정해야 한다**

- `toList()`(16+)는 **수정 불가**다. `add` 하면 `UnsupportedOperationException`.
- 수정이 필요하면 `collect(Collectors.toList())` 또는 `collect(Collectors.toCollection(ArrayList::new))`.
- 자세한 대비는 [`../47-collectors-basics/`](../47-collectors-basics/) 1번이 정본이다.

**저장(DB write)**

- **`forEach`** 에 넣는다(순서가 중요하면 `forEachOrdered`).
- 이유: **부작용의 실행이 보장되는 자리가 그 둘뿐**이기 때문이다(4번의 javadoc).
- `map(this::save)` 는 최종 연산이 무엇이냐에 따라 **0회 실행될 수 있다.**

**1억 건에서 첫 건만**

```java
huge.stream().filter(조건).findFirst();
```

- `filter` 를 앞에, `findFirst` 를 끝에. **찾는 자리에서 멈춘다.**
- 하면 안 되는 것: `huge.stream().filter(조건).toList().get(0)` — 전부를 모은다.
- 그리고 `sorted()` 를 끼우면 단락 평가가 죽는다(45번 (6)).

**`map` 안에 로그가 있는데 개수를 센다**

- **로그가 안 찍힐 수 있다.** 4번의 (A)가 그 경우다.
- 더 나쁜 것은 **파이프라인을 조금 고치면 찍히기 시작한다**는 점이다 — 재현이 안 되는 버그가 된다.
- 방어: 로그를 `map` 에서 빼거나, 세는 것을 `Collectors.counting()` 다운스트림으로 옮긴다([`../48-collectors-grouping/`](../48-collectors-grouping/)).

### 11. 세 JDK 에서 무엇이 달랐나

**달라진 것**

- **스택트레이스의 줄 번호뿐**이다. 프로그램 6개(46-a·b·c·d·f)를 세 버전에서 돌려 `diff` 로 확인했다.

```text
JDK 21.0.5                                        JDK 25.0.1
  AbstractPipeline.evaluateToArrayNode(:246)        AbstractPipeline.evaluateToArrayNode(:277)
  ReferencePipeline.toArray(:616)                   ReferencePipeline.toArray(:652)
  ReferencePipeline.toArray(:622)                   ReferencePipeline.toArray(:658)
  ReferencePipeline.toList(:627)                    ReferencePipeline.toList(:663)

  메시지는 한 글자도 같다:  stream has already been operated upon or closed
```

- 17.0.13 은 46-a·b·c·d·f 전부 **21과 완전히 동일**했다(줄 번호 포함).

**예외 메시지는 계약인가**

- **아니다.** javadoc 은 메시지 문구를 규정하지 않는다.
- 여기서 세 버전이 같았던 것은 **운이지 계약이 아니다.** 47번에서는 실제로 버전 간에 갈리는 메시지가 나온다.

**예외 타입은 계약인가**

- **그렇다.** javadoc 이 `IllegalStateException` 을 명시한다.

**코드에서 무엇을 기준으로 삼나**

```java
// 안 된다 — 메시지 파싱
if (e.getMessage().contains("already been operated")) { ... }

// 된다 — 타입
catch (IllegalStateException e) { ... }
```

- 로그·알림에는 메시지를 남기되, **분기 조건에는 타입만** 쓴다.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Ex.java` (46-a) | 최종 연산 없음 = 0줄, 네 단락 연산의 호출 횟수, `count()` 의 `peek` 생략과 `filter` 를 끼웠을 때의 복원 | 17 · 21 · 25 (동일) |
| `Ex.java` (46-b) | 빈 스트림의 세 술어·`reduce`·`Optional`, 최종 연산의 반환 타입, `iterator()` 의 지연과 소비 표시 | 17 · 21 · 25 (동일) |
| `Ex.java` (46-c) | 무한 스트림 + `limit`/`findFirst`/`anyMatch`, `limit` 이 중간 연산임 | 17 · 21 · 25 (동일) |
| `Ex.java` (46-d) | 재사용 `IllegalStateException` 세 경로, 스택트레이스 원문 | 17 (21과 동일) · 21 · 25 (**줄 번호만 다름**) |
| `Ex.java` (46-e) | 순차/병렬 × `forEach`/`forEachOrdered` 의 순서, 관여 스레드 수 | 21 (병렬이라 출력이 매번 다름 — 5회 반복 확인) |
| `Ex.java` (46-f) | `onClose` 가 최종 연산에 안 불림, `Files.lines` 를 안 닫아도 예외 없음, 한 번의 순회 | 17 · 21 · 25 (동일) |
| `Ex.java` (49-h) | `forEach` 대 `forEachOrdered` 의 병렬 비용(49번과 공유) | 21 |
| `src.zip` 열람 | `Stream.forEach`/`forEachOrdered` javadoc, `package-info` 의 Side-effects·Non-interference 절 | 21 |

**구현 의존 항목** (버전이 오르면 다시 돌려야 하는 것)

- `count()` 가 `peek` 를 건너뛰는 것 — 최적화이지 계약이 아니다. **Java 8 에서는 달랐다고 알려져 있으나 이 머신에 8이 없어 안 돌려 봄.**
- 병렬 `forEach` 의 출력 순서와 관여 스레드 수 — 머신의 코어 수(이 머신은 24)에 따라 다르다.
- 스택트레이스의 줄 번호 — 버전마다 다르다.
- `forEachOrdered` 의 액션을 실행하는 스레드 — 실측에서 `main` 일 때도, 워커일 때도 있었다(5회 중 1~2개 스레드).
