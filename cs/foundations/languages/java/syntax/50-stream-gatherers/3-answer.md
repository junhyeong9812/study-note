# java/syntax/50 — `Stream` Gatherers (24) — 커스텀 중간 연산 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 출력은 전부 실제로 돌려 얻은 것이다.\
> Gatherers 를 쓰는 프로그램은 **Temurin JDK 25.0.1** 에서만 돌아간다 — 17.0.13 · 21.0.5 에서는 **컴파일 에러**이고, 그 에러도 그대로 실었다.\
> javadoc 인용은 JDK 25.0.1 의 `lib/src.zip` — `java.base/java/util/stream/Gatherer.java`·`Gatherers.java`·`Stream.java` 원문이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 이 코드를 JDK 21 에서 빌드하면

**출력** (`Ex.java` — 50-a-min)

```text
===== javac 17.0.13 =====
Ex.java:2: error: cannot find symbol
import java.util.stream.Gatherers;
                       ^
  symbol:   class Gatherers
  location: package java.util.stream
Ex.java:8: error: cannot find symbol
                .gather(Gatherers.windowFixed(2))
                        ^
  symbol:   variable Gatherers
  location: class Ex
2 errors
(exit=1)
===== javac 21.0.5 =====
Ex.java:2: error: cannot find symbol
import java.util.stream.Gatherers;
                       ^
  symbol:   class Gatherers
  location: package java.util.stream
Ex.java:8: error: cannot find symbol
                .gather(Gatherers.windowFixed(2))
                        ^
  symbol:   variable Gatherers
  location: class Ex
2 errors
(exit=1)
===== javac 25.0.1 =====
(exit=0)
[[1, 2], [3, 4], [5]]
```

**컴파일 에러인가 런타임 예외인가**

- **컴파일 에러**다. 빌드 자체가 안 된다.
- 런타임 `NoSuchMethodError` 가 아니라는 점이 중요하다 — **배포 전에 드러난다.**
- 17 과 21 의 출력이 **한 글자도 같았다.** 둘 다 API 가 없다.

**메시지와 개수**

- `cannot find symbol` 두 개. `2 errors` 로 끝난다.
- 첫 번째는 **import 줄**(`symbol: class Gatherers`), 두 번째는 **사용 줄**(`symbol: variable Gatherers`).

**왜 `variable` 인가**

```text
  javac 가 Gatherers.windowFixed(2) 를 보는 순서

  1. Gatherers 라는 타입이 있나?  -> 없다(import 가 이미 실패했다)
  2. 그럼 Gatherers 라는 변수인가? -> 그것도 없다
  3. 마지막으로 본 후보 이름으로 보고한다 -> "variable Gatherers"
```

- `X.y()` 라는 식에서 `X` 는 **타입일 수도 변수일 수도** 있다.
- 타입 후보가 먼저 탈락했으므로 컴파일러는 **변수로 해석하려다 실패**하고 그 이름으로 보고한다.
- 그래서 같은 클래스 이름이 한 줄에서는 `class`, 다른 줄에서는 `variable` 로 나온다.

**`Stream.gather` 는 21 에 있는가**

- **없다.** 따로 확인했다(`Ex.java` — 50-a-min2).

```text
===== javac 21 =====
Ex.java:5: error: cannot find symbol
        System.out.println(Stream.of(1, 2).gather(null).toList());
                                          ^
  symbol:   method gather(<null>)
  location: interface Stream<Integer>
1 error
```

**25 에서의 출력**

```text
[[1, 2], [3, 4], [5]]
```

- 원소 5개를 2씩 나누면 `[1,2]`·`[3,4]` 와 **마지막 짧은 창 `[5]`** 가 남는다.

### 2. 이 기능은 몇 번부터 정식인가

**`src.zip` 의 `@since`**

```text
$ grep '@since' java.base/java/util/stream/Gatherer.java
197: * @since 24              <- public interface Gatherer<T, A, R>
$ grep '@since' java.base/java/util/stream/Gatherers.java
51: * @since 24               <- public final class Gatherers
$ (Stream.java 의 default <R> Stream<R> gather(...) 위)
1097:     * @since 24
```

- 셋 다 **24**다. `@PreviewFeature` 애너테이션은 25 의 소스에 없다.

**앞의 두 판**

- **22·23 에서는 프리뷰였다.** 이것을 기억이 아니라 **컴파일러로** 확인했다(아래).

**출력** (`Ex.java` — 50-a-min 을 JDK 25.0.1 의 javac 으로)

```text
===== javac 25 --release 24 =====
(exit=0)
===== javac 25 --release 23 =====
Ex.java:2: error: Gatherers is a preview API and is disabled by default.
import java.util.stream.Gatherers;
                       ^
  (use --enable-preview to enable preview APIs)
Ex.java:8: error: Gatherers is a preview API and is disabled by default.
                .gather(Gatherers.windowFixed(2))
                        ^
  (use --enable-preview to enable preview APIs)
Ex.java:8: error: <R>gather(Gatherer<? super T,?,R>) is a preview API and is disabled by default.
                .gather(Gatherers.windowFixed(2))
                ^
  (use --enable-preview to enable preview APIs)
  where R,T are type-variables:
    R extends Object declared in method <R>gather(Gatherer<? super T,?,R>)
    T extends Object declared in interface Stream
3 errors
(exit=1)
===== javac 25 --release 22 =====
(23 과 같은 3 errors)
```

**`--release 21` 과의 차이**

```text
  release 22·23                          release 21

  "preview API and is disabled"          "cannot find symbol"
          |                                      |
  API 는 존재한다 — 잠겨 있을 뿐            API 자체가 없다
```

- **문구가 다른 것이 그대로 증거다.** 22·23 에는 클래스가 있고, 21 에는 없다.
- 이것이 `@since 24` 라는 한 줄보다 강한 근거다 — 기억이 아니라 **컴파일러가 판별한 것**이다.

**`--enable-preview` 로 재현되는가**

```text
$ javac --release 23 --enable-preview Ex.java
error: invalid source release 23 with --enable-preview
  (preview language features are only supported for release 25)
```

- **안 된다.** `--enable-preview` 는 그 JDK 자신의 릴리스에만 붙는다.
- 그래서 "22·23 에서 프리뷰로 컴파일해 돌린 결과"는 **안 돌려 봄**이다 — 이 머신에 22·23 JDK 가 없다.

### 3. 내장 Gatherer 넷의 출력을 예측하라

**출력** (`Ex.java` — 50-a, JDK 25.0.1)

```text
--- (1) windowFixed(3) — 8개를 3씩
[[1, 2, 3], [4, 5, 6], [7, 8]]
--- (2) windowSliding(3) — 겹치는 창
[[1, 2, 3], [2, 3, 4], [3, 4, 5], [4, 5, 6], [5, 6, 7], [6, 7, 8]]
--- (4) scan — 누적 중간값이 전부 나온다
[1, 3, 6, 10, 15]
--- (5) fold — 최종값 하나만 남는다(스트림 크기 1)
[12345]
--- (6) fold 뒤에도 중간 연산을 더 붙일 수 있다
Optional[합=15]
```

**`windowSliding(3)` 의 개수**

```text
  원소 8개, 창 3칸

  시작 위치 : 1 2 3 4 5 6      <- 여섯 자리
              |         |
              첫 창      마지막 창(6,7,8)

  개수 = N - size + 1 = 8 - 3 + 1 = 6
```

- N < size 면 이 식이 음수가 되지만, 그때는 **짧은 창 하나**가 나온다(4번).

**`fold` 가 리스트인 이유**

- `gather(...)` 는 **중간 연산**이다. 스트림을 돌려준다.
- `fold` 는 그 스트림에 원소를 **하나만** 넣을 뿐, 스트림이라는 사실은 그대로다.
- javadoc 의 implSpec: "If no exceptions are thrown during processing, then this operation **only ever produces a single element**."

**`scan` 대 `fold` 의 출력 개수**

| | 입력 | 출력 | 언제 내보내나 |
|---|---|---|---|
| `scan` | 5개 | **5개** | 원소마다(integrator 에서) |
| `fold` | 5개 | **1개** | 입력이 끝난 뒤(finisher 에서) |

**뒤에 더 붙일 수 있는가**

```java
Stream.of(1,2,3,4,5)
      .gather(Gatherers.fold(() -> 0, Integer::sum))
      .map(n -> "합=" + n)
      .findFirst();          // Optional[합=15]
```

- **붙는다.** 이것이 `reduce` 와의 결정적 차이다.

### 4. 빈 스트림과 짧은 창

**출력** (`Ex.java` — 50-a)

```text
--- (7) 빈 스트림
windowFixed : []
scan        : []
fold        : [0]
--- (8) 창이 나눠떨어지지 않을 때 — 마지막 창이 짧다
[[1, 2, 3], [4, 5, 6], [7]]
--- (9) windowSliding 은 원소 수 < 창 크기면 창 하나
[[1, 2]]
--- (10) windowFixed 도 마찬가지
[[1, 2]]
```

**하나만 원소가 있다**

- **`fold` 다.** 결과는 `[0]`.
- integrator 는 한 번도 안 불렸지만 **finisher 는 불린다.** 그 finisher 가 초깃값 `0` 을 밀어 넣는다.
- `reduce(identity, op)` 가 빈 스트림에서 `identity` 를 돌려주는 것과 같은 성격이다(46번 3번).
- `windowFixed` 의 javadoc 이 반대쪽을 못박는다: "If the stream is empty then **no window will be produced**."

**7개를 `windowFixed(3)` 에 넣으면**

- `[[1, 2, 3], [4, 5, 6], [7]]` — 마지막 창이 **1개짜리**다.
- javadoc: "The last window may contain **fewer elements** than the supplied window size."

**소비 쪽이 어떻게 깨지나**

```java
// 위험 — 창이 항상 3개라고 가정한다
stream.gather(Gatherers.windowFixed(3))
      .map(w -> w.get(0) + w.get(1) + w.get(2))   // 마지막 창에서 IndexOutOfBoundsException
      .toList();
```

- 방어: `w.stream().mapToInt(...).sum()` 처럼 **크기에 의존하지 않는 형태**로 쓰거나, `filter(w -> w.size() == 3)` 으로 자른다.

**`windowFixed(0)` 은 언제 무엇을 던지나**

```text
--- (7) 인자 검증 — 창 크기 0
windowFixed(0)   : java.lang.IllegalArgumentException: 'windowSize' must be greater than zero
windowSliding(0) : java.lang.IllegalArgumentException: 'windowSize' must be greater than zero
windowFixed(-1)  : java.lang.IllegalArgumentException: 'windowSize' must be greater than zero
--- (8) 예외는 언제 던져지나 — 팩토리에서인가 실행에서인가
팩토리 호출만 : java.lang.IllegalArgumentException: 'windowSize' must be greater than zero
```

- **팩토리를 부르는 순간**이다. 스트림을 돌리기 전이고, 최종 연산도 필요 없다.

### 5. 단락 평가가 정말 통과하는지

**출력** (`Ex.java` — 50-c, JDK 25.0.1)

```text
--- (1) gather 는 지연된다 — 최종 연산 없이는 한 원소도 안 흐른다
최종 연산 없음 — 흘러간 원소 : []
--- (2) 단락 평가가 gather 를 통과한다 — findFirst 는 3개만 당긴다
결과 : Optional[[1, 2, 3]]
흘러간 원소 : [1, 2, 3]
--- (3) 같은 일을 Collector 로 하면 전부 흘러간다
결과 : {0=[1, 2, 3], 1=[4, 5, 6], 2=[7, 8]}
흘러간 원소 : [1, 2, 3, 4, 5, 6, 7, 8]
```

**`first` 와 `seen`**

- `first` = `Optional[[1, 2, 3]]`, `seen` = `[1, 2, 3]`.
- 창 하나가 채워지자마자 `findFirst` 가 답을 얻고 파이프라인을 끝냈다.

**Collector 로 하면**

- `seen` 은 `[1, 2, 3, 4, 5, 6, 7, 8]` — **여덟 개 전부**다.

**갈리는 이유 한 문장**

- `gather` 는 중간 연산이라 **단락이 위로 전파되고**, `collect` 는 최종 연산이라 **전부를 봐야 끝난다.**

**최종 연산이 없으면**

- `seen` 은 `[]` 다. `gather` 도 다른 중간 연산과 똑같이 **지연된다**(46번 1번과 같은 규칙).

**무한 스트림에 걸 수 있는 조건**

```text
--- (4) 무한 스트림에도 붙는다
[1, 2, 3, 4]
```

- 위는 `Stream.iterate(1, i -> i + 1).gather(takeUntilInclusive(i -> i >= 4)).toList()` 의 결과다.
- 조건은 **파이프라인 어딘가에 단락이 있어야** 한다는 것이다. 둘 중 하나면 된다.
  - Gatherer 자신이 `integrate` 에서 `false` 를 돌려준다(위 예).
  - 뒤에 `limit`·`findFirst`·`anyMatch` 같은 단락이 붙는다.
- 둘 다 없이 `gather(windowFixed(3)).toList()` 를 무한 스트림에 걸면 **끝나지 않는다**(46번 4번과 같다 — 안 돌려 봄. 끝나지 않는 프로그램이라 타임아웃 없이 확인할 수 없다).

### 6. `Collector` 와 `Gatherer` 는 무엇이 다른가

**왜 둘인가**

```text
  파이프라인에서의 자리

  소스 -> 중간 -> 중간 -> [gather] -> 중간 -> [최종]
                             ^                   ^
                          Gatherer            Collector
                       (뒤가 있다)           (여기서 끝난다)
```

- 능력이 겹치는 부분이 있지만 **자리가 다르다.**
- Collector 는 `collect(...)` 라는 **최종 연산의 인자**다. 그 호출이 끝나면 스트림도 끝난다.
- Gatherer 는 `gather(...)` 라는 **중간 연산의 인자**다. 스트림이 계속 살아 있다.

**`collect` 뒤에 `map` 을 붙이려면**

```text
--- (4) Collector 는 최종 연산이라 뒤에 중간 연산을 못 붙인다
gather  뒤 : [2, 2]
collect 뒤 : [10, 20, 30, 40]  (스트림을 새로 만들어야 한다)
```

```java
// gather — 그대로 이어진다
Stream.of(1,2,3,4).gather(Gatherers.windowFixed(2)).map(List::size).toList();

// collect — .stream() 을 새로 불러야 한다
Stream.of(1,2,3,4).collect(Collectors.toList()).stream().map(i -> i * 10).toList();
```

- 중간에 `List` 가 하나 생긴다. **전부 메모리에 올라간 뒤** 다시 흐른다.

**`gather` 뒤에 붙일 수 있는 것**

- **아무 중간 연산이나.** `map`·`filter`·`sorted`·`limit`·또 다른 `gather`.

**한 파이프라인에 같이**

```text
--- (5) gather 와 collect 를 한 파이프라인에 같이 쓴다
{1=2, 3=4, 5=6}
```

```java
Stream.of(1,2,3,4,5,6)
      .gather(Gatherers.windowFixed(2))
      .collect(Collectors.toMap(w -> w.get(0), w -> w.get(1)));
```

- **자연스러운 조합**이다. 흐름을 바꾸는 것은 Gatherer, 마지막에 모으는 것은 Collector.

**뒤에 붙일 연산이 없다면**

- **Collector 를 고른다.** 굳이 중간 연산을 쓸 이유가 없고, 익숙한 API 가 낫다.

### 7. 이 Gatherer 의 출력을 예측하라

**출력** (`Ex.java` — 50-b, JDK 25.0.1)

```text
--- (1) dedupeAdjacent — 연속 중복만 제거(distinct 와 다르다)
입력           : [a, a, b, b, b, a, c, c]
dedupeAdjacent : [a, b, a, c]
distinct       : [a, b, c]
```

**왜 갈리나**

```text
  입력  a    a    b    b    b    a    c    c

  dedupeAdjacent 의 메모지 (한 칸)
  메모  -    a    a    b    b    b    a    c
  판정  새   같   새   같   같   새   새   같
  출력  a         b              a    c      -> [a, b, a, c]

  distinct 의 메모지 (본 것 전부)
  메모  {}   {a}  {a}  {a,b} ...  {a,b}  {a,b} {a,b,c}
  판정  새   같   새   같   같   같!  새   같
  출력  a         b                   c      -> [a, b, c]
                                 ^
                     여기서 갈린다 — distinct 는 앞의 a 를 기억한다
```

- **기억하는 양이 다르면 답이 다르다.** 한 칸이냐, 본 것 전부냐.
- 메모리도 다르다 — `dedupeAdjacent` 는 O(1), `distinct` 는 서로 다른 값의 수만큼.

**`return true;` 를 `return downstream.push(element);` 로 바꾸면**

- **버려야 할 원소를 내보내게 된다.** 결과가 입력 그대로가 된다.
- `return true` 는 "이 원소는 안 내보내지만 **계속 받겠다**"는 뜻이다. 반환값은 **내보냈는지가 아니라 계속할지**를 말한다.

**`map`·`filter` 로 안 되는 이유**

- `filter` 의 술어는 **원소 하나만** 받는다. 직전 값을 볼 자리가 없다.
- 외부 변수를 캡처해 흉내 낼 수는 있지만, javadoc 의 non-interference·stateless 계약을 어긴다 — 11번에서 그 결과를 본다.

### 8. `integrate` 의 반환값은 무슨 뜻인가

**`false` 를 돌려주면**

- **소스가 멈춘다.** javadoc 의 implSpec 이 못박는다.

  > When the integrator function returns `false`, it shall be interpreted just as if there were no more elements to pass it.

**출력** (`Ex.java` — 50-b)

```text
--- (2) takeUntilInclusive — takeWhile 과의 차이
입력                    : [1, 3, 5, 8, 9, 11]
takeWhile(홀수)         : [1, 3, 5]
takeUntilInclusive(짝수): [1, 3, 5, 8]
--- (3) 정말로 단락되나 — peek 로 센다
결과  : [1, 3, 5, 8]
소스가 흘려보낸 원소 : [1, 3, 5, 8]
```

**`push` 의 반환값**

- **아래쪽이 더 받을 생각이 있는지**를 말한다. `false` 면 아래가 이미 닫혔다는 뜻이다.
- 그래서 보통은 `push` 결과를 **그대로(또는 자기 조건과 `&&` 해서) 돌려준다.**

**`of` 와 `ofGreedy`**

| | 뜻 | 구현이 하는 일 |
|---|---|---|
| `Integrator.of` | 멈출 수 **있다** | 반환값을 매번 검사한다 |
| `Integrator.ofGreedy` | 절대 안 멈춘다 | 반환값 검사를 **건너뛸 수 있다** |

  > Gatherers whose integrator is an instance of `Integrator.Greedy` **can be assumed not to short-circuit**, and the return value of invoking `Integrator.integrate` **does not need to be inspected**.

**`ofGreedy` 로 선언해 놓고 `false` 를 돌려주면**

- **무시될 수 있다.** 구현이 반환값을 안 볼 권리를 갖기 때문이다.
- 이것은 예외가 아니라 **무음 오작동**이다. 계약을 어긴 쪽이 잘못이다.

**`takeWhile` 과의 차이**

```text
  입력 [1, 3, 5, 8, 9, 11] · 조건 "짝수를 만나면 그만"

  takeWhile(홀수)          1 3 5 | 8 은 조건에 안 맞아 버린다     -> [1, 3, 5]
  takeUntilInclusive(짝수) 1 3 5   8 까지 내보내고 거기서 끝     -> [1, 3, 5, 8]
                                   ^
                          "경계가 된 원소를 포함하느냐"가 전부다
```

- 로그의 "에러가 난 줄까지 포함해서 보여 달라" 같은 요구가 정확히 이 형태다.

### 9. Gatherer 의 네 함수

**이름과 역할**

| 함수 | 타입 | 역할 |
|---|---|---|
| `initializer()` | `Supplier<A>` | 상태 객체를 하나 만든다 |
| `integrator()` | `Integrator<A, T, R>` | 원소 하나를 받아 처리하고 계속할지 돌려준다 |
| `combiner()` | `BinaryOperator<A>` | 병렬로 나뉜 두 상태를 합친다 |
| `finisher()` | `BiConsumer<A, Downstream<R>>` | 입력이 끝난 뒤 한 번 불린다 |

javadoc 의 의사코드가 이 순서를 그대로 보여 준다.

> ```java
> A state = gatherer.initializer().get();
> for (T t : data) {
>     gatherer.integrator().integrate(state, t, downstream);
> }
> gatherer.finisher().accept(state, downstream);
> ```

**필수인 것**

- **`integrator` 하나**다. 나머지 셋은 기본값이 있다(`defaultInitializer`·`defaultCombiner`·`defaultFinisher`).

**`combiner` 를 안 주면**

  > Gatherers whose combiner is `defaultCombiner()` **may only be evaluated sequentially.**

- 그 Gatherer 가 든 파이프라인의 그 단계는 **병렬로 나뉘지 않는다.**

**`parallelStream()` 에 걸면**

**출력** (`Ex.java` — 50-c)

```text
--- (9) 순차 전용 Gatherer 를 병렬 스트림에 걸면
parallel + windowFixed(5) : [[1, 2, 3, 4, 5], [6, 7, 8, 9, 10], [11, 12]]
parallel + fold           : [78]
parallel + scan (앞 4개)   : [1, 3, 6, 10]
```

- **예외는 안 난다.** 결과도 순차와 같다.
- 잃는 것은 정확성이 아니라 **병렬의 이득**이다. 오버헤드만 내고 그 단계는 한 스레드로 돈다.

**`finisher` 가 있으면 출력 개수는**

- **입력 개수와 무관하다.** `fold` 가 그 극단이다 — 입력 N개, 출력 1개.
- 반대로 finisher 가 여러 개를 밀어 넣을 수도 있다.

```text
--- (5) finisher — 스트림이 끝난 뒤 한 개 더
[원소 1, 원소 2, 원소 3, 합계 6]
```

- 입력 3개인데 출력은 4개다. integrator 가 3개, finisher 가 1개를 냈다.

### 10. 창이 돌려준 리스트를 고치면

**출력** (`Ex.java` — 50-c)

```text
--- (6) windowFixed 가 돌려주는 List 는 수정 불가
window.add : java.lang.UnsupportedOperationException: null
```

**무엇이 던져지나 · 메시지**

- `java.lang.UnsupportedOperationException`.
- **메시지가 `null`** 이다. `getMessage()` 가 `null` 을 돌려준다는 뜻이다.

**왜 문제가 되나**

```java
catch (UnsupportedOperationException e) {
    log.error("실패: " + e.getMessage());   // "실패: null" 만 남는다
}
```

- 로그에 **원인이 안 남는다.** 어느 리스트였는지, 어떤 연산이었는지가 전부 사라진다.
- 스택트레이스를 통째로 남기지 않으면 추적이 안 된다.

**보장인가 구현 세부인가**

| | 판정 | 근거 |
|---|---|---|
| `UnsupportedOperationException` 이 던져지는 것 | **보장** | javadoc implSpec — "calls to any mutator method will **always** cause `UnsupportedOperationException`" |
| 메시지가 `null` 인 것 | **보장 아님** | 실측 결과일 뿐. javadoc 은 메시지를 규정하지 않는다 |
| 리스트의 **구현 타입** | **보장 아님** | javadoc — "There are **no guarantees** on the implementation type or serializability of the produced Lists" |

**고쳐야 한다면**

```java
.gather(Gatherers.windowFixed(3))
.map(ArrayList::new)      // 여기서 복사한다
```

### 11. 24 이전에는 어떻게 했나

**출력** (`Ex.java` — 50-d, 17.0.13 · 21.0.5 · 25.0.1 에서 모두 돌림 — 아래는 21.0.5)

```text
--- (1) 24 이전의 우회 1 — 리스트로 먼저 받고 인덱스로 자른다
[[1, 2, 3], [4, 5, 6], [7, 8]]
--- (2) 24 이전의 우회 2 — Collectors 로 그룹핑(인덱스가 필요하다)
{0=[1, 2, 3], 1=[4, 5, 6], 2=[7, 8]}
(부작용이 있는 분류 함수 — 병렬이면 깨진다)
--- (3) 24 이전의 우회 3 — 누적(scan) 을 map + 외부 상태로
[1, 3, 6, 10, 15, 21, 28, 36]
(map 의 람다가 상태를 들고 있다 — javadoc 이 금지하는 형태)
--- (5) 상태 있는 변환을 map/filter 로 쓰면 무엇이 깨지나 — 병렬
병렬 map + 외부 상태 : [27, 32, 30, 36, 26, 21, 15, 8]
(순차의 [1, 3, 6, 10, 15, 21, 28, 36] 과 비교하라 — 실행마다 달라진다)
```

**우회 1이 잃는 것**

- **지연 평가**다. `toList()` 가 먼저 와야 하므로 그 순간 전부 메모리에 올라간다.
- 100만 건이면 100만 건이 다 올라간다. Gatherer 는 창 하나 분량만 든다.

**우회 2의 위험**

```java
int[] idx = {0};
src.stream().collect(Collectors.groupingBy(x -> idx[0]++ / 3));
```

- 분류 함수가 **부작용을 갖는다.** javadoc 이 "stateless" 를 요구하는 자리다.
- 순차에서는 맞는 답이 나오므로 **테스트가 통과한다.** 병렬로 바꾸는 순간 깨진다.
- 게다가 `Map` 이라 **키 순서가 보장되지 않는다**(여기서는 `HashMap` 이고 작은 정수 키라 우연히 정렬돼 보인다).

**병렬로 돌리면**

```text
  같은 코드, 같은 입력 [1..8]

  순차      [1, 3, 6, 10, 15, 21, 28, 36]
  병렬 17   [36, 35, 33, 30, 26, 21, 15, 8]
  병렬 21   [27, 32, 30, 36, 26, 21, 15, 8]
  병렬 25   [34, 36, 33, 30, 26, 21, 15, 8]
           ^^^ 세 판이 다 다르고, 같은 판에서도 실행마다 다르다
```

- **예외가 아니라 틀린 답**이 나온다. 이것이 가장 비싼 실패 모드다.
- `acc[0] += x` 가 스레드마다 끼어들어 각 원소가 "그 시점의 합"을 받는다 — 순서도 값도 무너진다.

**셋이 공통으로 못 하는 것**

- **무한 스트림**이다. 셋 다 최종 연산(`toList`·`collect`)이 먼저 와야 하고, 최종 연산은 무한 스트림에서 끝나지 않는다.

**Gatherer 가 메운 구멍 한 문장**

- **상태 있는 변환을, 지연을 깨지 않고, 부작용 없이, 중간 연산 자리에서 할 수 있게 했다.**

### 12. 어느 것을 고르는가

| 요구 | 고를 것 | 이유 |
|---|---|---|
| 1,000건씩 묶어 외부 API 로 | `gather(Gatherers.windowFixed(1000))` | 전부 메모리에 올리지 않고 묶인다 |
| 직전 값과의 차이 | `gather(Gatherers.windowSliding(2))` | 이웃 쌍이 바로 나온다 |
| 느린 호출 6개 동시 + 순서 유지 | `gather(Gatherers.mapConcurrent(6, f))` | javadoc 이 "preserves the ordering" 을 명시 |
| `Map` 으로 모으기만 | `collect(Collectors.toMap(...))` | 뒤에 붙일 것이 없다 — Gatherer 를 쓸 이유가 없다 |

**타깃이 21 이면**

- **위 세 답이 전부 무효다.** 컴파일이 안 된다(1번).
- 배치 묶기는 **리스트로 받아 `subList`**(11번 우회 1) 또는 **그냥 `for` 루프**로 한다.
- 이웃 차이는 `IntStream.range(1, n).mapToObj(i -> list.get(i) - list.get(i-1))`.
- 동시 호출은 `ExecutorService` 에 `invokeAll` — [**54번 주제**](../54-executorservice-and-future/)(`java.util.concurrent`)의 영역이다.
- 누적은 **스트림을 쓰지 않는다.** 외부 상태를 캡처한 `map` 은 11번에서 본 대로 깨진다.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Ex.java` (50-a-min) | `Gatherers` 가 17·21 에 없다 · 25 에서의 출력 · `--release 21/22/23/24` 의 에러 문구 차이 | 17 · 21 · 25 (**17·21 은 컴파일 실패**) |
| `Ex.java` (50-a-min2) | `Stream.gather` 메서드가 21 에 없다 · `--release 21` 도 같다 | 21 · 25 |
| `Ex.java` (50-a) | 내장 넷의 출력, 빈 스트림 셋, 안 나눠떨어지는 창, 원소 수 < 창 크기 | **25 만** (17·21 컴파일 실패) |
| `Ex.java` (50-b) | 커스텀 Gatherer 셋(dedupe·takeUntilInclusive·finisher), 단락 실증, 무한 스트림, `andThen` | **25 만** |
| `Ex.java` (50-c) | 지연·단락 대 Collector, 수정 불가 리스트, 인자 검증, 병렬 + 순차 전용, `mapConcurrent` | **25 만** |
| `Ex.java` (50-d) | 24 이전의 우회 셋과 그 한계, 병렬에서 외부 상태가 깨지는 것 | 17 · 21 · 25 (**(5)만 매번 다름**) |
| `src.zip` 열람 | `Gatherer`·`Gatherers`·`Stream.gather` 의 `@since 24` · `Gatherer` 클래스 javadoc(네 함수·implSpec) · `windowFixed`/`fold`/`mapConcurrent` javadoc | 25 |
| `javac --release` | 22·23 에서 프리뷰였다는 것 · 21 에는 아예 없다는 것 | 25 의 javac |

**구현 의존 항목** (버전이 오르면 다시 돌려야 하는 것)

- `mapConcurrent` 의 **212ms** — 이 머신(코어 24) 1회 측정이다. JMH 가 아니고 반복도 1회다. 재현되는 것은 절댓값이 아니라 **"순차의 1/6 자릿수"** 다.
- `UnsupportedOperationException` 의 **메시지가 `null`** — javadoc 이 규정하지 않는다.
- 창이 돌려주는 `List` 의 **구현 타입** — javadoc 이 "no guarantees" 라고 적는다.
- `gather(a).gather(b)` 가 하나로 합쳐지는지 — javadoc 이 "not required" 라고 적는다. **합쳐지는지 안 합쳐지는지는 안 돌려 봄**(관측할 수 있는 출력 차이가 없다).
- 50-d (5) 의 병렬 출력 — 실행마다 다르다. 세 판의 값을 각각 실었지만 **재현되지 않는 것이 정상**이다.
- 22·23 에서 `--enable-preview` 로 실제 실행한 결과 — **안 돌려 봄.** 이 머신에 22·23 JDK 가 없고, JDK 25 는 `--release 23 --enable-preview` 를 거부한다(2번의 에러 메시지).
- 무한 스트림 + 단락 없는 `gather` — **안 돌려 봄.** 끝나지 않는 프로그램이다.
