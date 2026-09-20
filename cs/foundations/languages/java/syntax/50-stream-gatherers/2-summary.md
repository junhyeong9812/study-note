# java/syntax/50 — `Stream` Gatherers (24) — 커스텀 중간 연산 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **선행** — [`../46-terminal-operations/`](../46-terminal-operations/). 「최종 연산이 당겨 온다」를 모르면 Gatherer 의 단락 평가가 안 읽힌다.\
> 그 앞에 [`../45-intermediate-operations/`](../45-intermediate-operations/)(중간 연산이 무엇을 못 하나)·[`../44-stream-creation/`](../44-stream-creation/)(소스)이 있다.
> **기준 소스** — Temurin **JDK 25.0.1** 표준 라이브러리 소스 `java.base/java/util/stream/Gatherer.java`·`Gatherers.java`·`Stream.java`(`lib/src.zip`) · [`Gatherer` javadoc (Java SE 24)](https://docs.oracle.com/en/java/javase/24/docs/api/java.base/java/util/stream/Gatherer.html) · [`Gatherers` javadoc (Java SE 24)](https://docs.oracle.com/en/java/javase/24/docs/api/java.base/java/util/stream/Gatherers.html)
> **실행 검증** — 이 문서의 모든 출력은 실제로 돌려 얻은 것이다.\
> Gatherers 를 쓰는 프로그램 셋(50-a·50-b·50-c)은 **25.0.1 에서만** 돌아간다 — 17·21 에서는 **컴파일이 안 된다**(아래 「구현 세부사항 대 언어 보장」에 두 판의 출력을 다 실었다).\
> Gatherers 를 안 쓰는 프로그램 하나(50-d)는 17.0.13 · 21.0.5 · 25.0.1 **셋 다** 돌렸다.\
> 최소 예제 둘(50-a-min·50-a-min2)은 **세 판에서 컴파일만** 했고, `--release 21/22/23/24` 도 25 의 `javac` 으로 걸어 봤다.
> **버전** — `Gatherer`·`Gatherers`·`Stream.gather` 전부 `src.zip` 의 **`@since 24`**. 22·23 에서는 **프리뷰**였다(아래에서 `--release` 로 실증).\
> **범위** — 스트림 파이프라인의 평가 시점·단락 평가는 [`../46-terminal-operations/`](../46-terminal-operations/) 가 정본이다.\
> 그쪽은 **기존 연산이 언제 도느냐**까지, 여기는 **그 연산 목록에 내가 하나를 더 끼워 넣는 방법**부터다.\
> Gatherers 가 **언제·왜 들어왔나**(JEP 번호·프리뷰 두 번)는 [`../../../../../../history/java/java-24.md`](../../../../../../history/java/java-24.md) 가 정본이다 — 여기는 **어떻게 쓰고 무엇을 못 하나**만 쓴다.
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**Gatherer 는 내가 직접 만들어 벨트에 끼우는 작업대다.**

44·45·46 번의 컨베이어 벨트 비유를 그대로 잇는다.

| 비유 | 실체 |
|---|---|
| 물건을 올려 주는 장치 | 소스 — 44번 |
| 벨트 위의 **정해진** 작업대 | `map`·`filter`·`sorted` — 45번 |
| 벨트 끝의 시동 스위치 | 최종 연산 — 46번 |
| **내가 만들어 끼우는 작업대** | **`gather(...)` — 이 주제** |
| 작업대 옆의 **메모지** | Gatherer 의 상태(initializer) |
| 물건을 받아 처리하는 손 | integrator |
| **"이제 그만 보내세요"** 라고 말하는 것 | `integrate` 가 `false` 를 돌려주는 것 = 단락 평가 |
| 벨트가 다 끝난 뒤 **마지막 한 개를 더 올리는 것** | finisher |
| 벨트 **끝에서** 상자에 담는 사람 | `Collector` — 47·48번 |

- 기존 작업대는 **물건 하나만 보고 하나를 내보낸다.**\
  `map` 은 하나 받아 하나, `filter` 는 하나 받아 0 또는 1개.
- 그래서 **"직전에 뭐가 지나갔더라"** 가 필요한 일은 기존 작업대로 못 한다.\
  3개씩 묶기·누적 합·연속 중복 제거가 전부 그런 일이다.
- `Gatherer` 는 작업대 옆에 **메모지 한 장**을 놓아 준다.\
  받은 물건을 메모지에 적어 두고, **0개든 1개든 여러 개든** 마음대로 내보낼 수 있다.
- `Collector` 와의 자리가 다르다. Collector 는 **벨트 끝**이라 그 뒤에 작업대를 더 놓을 수 없다.\
  Gatherer 는 **벨트 중간**이라 뒤에 무엇이든 더 붙는다.

```text
                기존 중간 연산                        Gatherer

  [1][2][3][4]                            [1][2][3][4]
       |                                       |
   +---------+  하나 보고 하나            +----------------+  메모지를 보며
   | map     |  (앞뒤를 모른다)           | gather(window) |  여러 개를 모아
   +---------+                            +----------------+  한 개를 내보낸다
       |                                       |
  [a][b][c][d]                            [[1,2]][[3,4]]
```

- 왼쪽은 원소 수가 그대로다(`filter` 면 줄기만 한다).
- 오른쪽은 **원소 수도, 타입도, 묶는 단위도** 바뀐다. 그러면서 **여전히 중간 연산**이다.

> **중간 연산(intermediate operation)** — 스트림을 받아 스트림을 돌려주는 연산. 최종 연산이 붙기 전에는 아무것도 실행하지 않는다.\
> 예: `map`·`filter`·`gather`. `toList()` 는 최종 연산이라 여기 안 들어간다.

> **상태 있는 변환(stateful transformation)** — 지금 원소 하나만으로는 답이 안 나오고, 앞서 지나간 것을 기억해야 하는 변환.\
> 예: "직전 값과 같으면 버린다"는 직전 값을 어딘가 적어 둬야 한다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. `map`·`filter`·`flatMap` 으로 **못 하던 것**은 무엇이고, Gatherer 는 그것을 어떻게 하나.
2. `Collector` 와 `Gatherer` 는 **어디가 다른가** — 둘 다 "여러 원소를 모은다"인데 왜 둘인가.
3. 21 에서 이 코드를 돌리면 **정확히 무슨 일이 생기나.**

## 동작 방식

### (1) 21 에서 무슨 일이 생기나 — 먼저 이것부터

**언제 쓰나** — 25 기준 예제를 21 LTS 프로젝트에 붙여 넣기 전에.

최소 예제 하나(`Ex.java` — 50-a-min)를 세 판에서 컴파일했다.

```java
import java.util.List;
import java.util.stream.Gatherers;
import java.util.stream.Stream;

public class Ex {
    public static void main(String[] args) {
        List<List<Integer>> w = Stream.of(1, 2, 3, 4, 5)
                .gather(Gatherers.windowFixed(2))
                .toList();
        System.out.println(w);
    }
}
```

**실행 결과** (세 판 전부 실제로 돌린 것)

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

```text
JDK 17 / 21                              JDK 25

  java.util.stream 패키지                 java.util.stream 패키지
  +---------------------+                +---------------------+
  | Stream              |                | Stream              |
  | Collectors          |                | Collectors          |
  | (Gatherer 없음)     |                | Gatherer            |
  | (Gatherers 없음)    |                | Gatherers           |
  +---------------------+                +---------------------+
         |                                       |
  import 줄에서 이미 실패                  컴파일·실행 모두 성공
  = 런타임 에러가 아니라 컴파일 에러
```

그림 해설 (한 단계씩):

- **클래스 자체가 없다.** import 줄에서 `cannot find symbol: class Gatherers` 로 끝난다.
- 그 아래 `Gatherers.windowFixed(2)` 는 컴파일러가 **`Gatherers` 를 변수로** 읽어 `variable Gatherers` 라고 적는다 — 타입을 못 찾았으니 식별자로 본 것이다.
- **런타임에 `NoSuchMethodError` 가 나는 게 아니다.** 21 에서는 빌드 자체가 안 된다.

`Stream.gather` 메서드도 21 에 없다는 것을 따로 확인했다(`Ex.java` — 50-a-min2).

```text
===== javac 21 =====
Ex.java:5: error: cannot find symbol
        System.out.println(Stream.of(1, 2).gather(null).toList());
                                          ^
  symbol:   method gather(<null>)
  location: interface Stream<Integer>
1 error
```

비용 — 21 LTS 를 쓰는 프로젝트에서는 **선택지가 아니다.** 45·46 의 우회로 돌아가야 한다((6)).

### (2) 22·23 에서는 프리뷰였다 — `--release` 로 실증

**언제 쓰나** — "24 부터"라는 말의 앞쪽이 궁금할 때. 사내 JDK 가 22·23 일 때.

`src.zip` 의 `@since` 는 24 다.

```text
$ grep '@since' java.base/java/util/stream/Gatherer.java
197: * @since 24              <- 인터페이스 Gatherer
482:     * @since 24
524:     * @since 24
583:         * @since 24
$ grep '@since' java.base/java/util/stream/Gatherers.java
51: * @since 24               <- 클래스 Gatherers
$ grep -A3 '@since 24' java.base/java/util/stream/Stream.java | grep 'default <R>'
    default <R> Stream<R> gather(Gatherer<? super T, ?, R> gatherer) {
```

`@PreviewFeature` 애너테이션은 25 의 소스에 **없다.** 24 에서 정식이라는 뜻이다.

프리뷰였던 시절은 JDK 25 의 `javac` 에 `--release` 를 주면 그대로 재현된다.

**실행 결과** (`Ex.java` — 50-a-min, JDK 25.0.1 의 javac)

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
(23 과 같은 메시지 3줄)
===== javac 25 --release 21 =====
Ex.java:5: error: cannot find symbol
        System.out.println(Stream.of(1, 2).gather(null).toList());
                                          ^
  symbol:   method gather(<null>)
  location: interface Stream<Integer>
1 error
```

```text
  release 21        release 22 · 23          release 24 · 25
      |                   |                        |
  API 가 없다        API 는 있는데            그냥 된다
  cannot find        preview API and
  symbol             is disabled by default
```

그림 해설 (한 단계씩):

- **22·23 에서는 API 가 존재는 한다.** 그래서 에러 문구가 `cannot find symbol` 이 아니라 `preview API` 다.
- `--release 21` 로 내려가면 그제서야 `cannot find symbol` 로 바뀐다 — **존재하지 않는 구간**이다.
- 세 문장은 `Gatherers` 클래스·그 정적 메서드·`Stream.gather` 를 **따로따로** 걸고 넘어진다.

프리뷰를 켜 보려 했더니 이런 메시지가 나왔다.

```text
$ javac --release 23 --enable-preview Ex.java
error: invalid source release 23 with --enable-preview
  (preview language features are only supported for release 25)
```

- **JDK 25 에서는 23 의 프리뷰를 되살릴 수 없다.** `--enable-preview` 는 그 JDK 자신의 릴리스에만 붙는다.
- 그래서 이 문서는 "22·23 에서 프리뷰였다"를 **거부 메시지로만** 실증했고, 프리뷰로 컴파일해 돌린 결과는 **안 돌려 봄**이다(이 머신에 22·23 JDK 가 없다).

비용 — 프리뷰 API 로 빌드한 클래스 파일은 그 마이너 버전에 묶인다. 정식이 된 24 부터는 그 제약이 없다.

### (3) 내장 Gatherer 넷 — 무엇을 돌려주나

**언제 쓰나** — 배치 처리·이동 평균·누적 합·순서 의존 접기.

**실행 결과** (`Ex.java` — 50-a, JDK 25.0.1)

```text
--- (1) windowFixed(3) — 8개를 3씩
[[1, 2, 3], [4, 5, 6], [7, 8]]
--- (2) windowSliding(3) — 겹치는 창
[[1, 2, 3], [2, 3, 4], [3, 4, 5], [4, 5, 6], [5, 6, 7], [6, 7, 8]]
--- (3) windowSliding(2) — 이웃 쌍
[[10, 13], [13, 9], [9, 20]]
--- (4) scan — 누적 중간값이 전부 나온다
[1, 3, 6, 10, 15]
--- (5) fold — 최종값 하나만 남는다(스트림 크기 1)
[12345]
--- (6) fold 뒤에도 중간 연산을 더 붙일 수 있다
Optional[합=15]
```

```text
입력 [1][2][3][4][5][6][7][8]

 windowFixed(3)    [1 2 3]        [4 5 6]        [7 8]
                   +-----+        +-----+        +---+
                   겹치지 않는다 · 마지막이 짧을 수 있다 · 원소 3개 나온다

 windowSliding(3)  [1 2 3]
                     [2 3 4]
                       [3 4 5]
                         [4 5 6]
                           [5 6 7]
                             [6 7 8]
                   한 칸씩 민다 · 원소 6개 나온다 (8 - 3 + 1)
```

그림 해설 (한 단계씩):

- `windowFixed(3)` 은 **8 ÷ 3 = 2 묶음 + 나머지 2개**라 마지막 창이 `[7, 8]` 로 짧다.
- `windowSliding(3)` 은 **원소 수 − 창 크기 + 1 = 6개**를 낸다. 겹치는 부분이 그대로 반복된다.
- `windowSliding(2)` 는 **이웃 쌍**이 되어 "직전 값과의 차이" 같은 계산의 재료가 된다.

```text
 scan(0, +)        [1] -> 1
                   [2] -> 1+2 = 3
                   [3] -> 3+3 = 6      중간값을 매번 내보낸다 -> 5개
                   [4] -> 6+4 = 10
                   [5] -> 10+5 = 15

 fold("", concat)  [1][2][3][4][5] 를 전부 먹고
                                     끝에서 "12345" 하나만 내보낸다 -> 1개
```

그림 해설 (한 단계씩):

- `scan` 은 **누적 중간값을 전부** 내보낸다 — 입력 5개, 출력 5개.
- `fold` 는 **끝에서 한 개**만 내보낸다 — 입력 5개, 출력 1개. 그래도 **스트림**이라 뒤에 `map`·`findFirst` 가 붙는다((6)의 `Optional[합=15]`).
- `fold` 의 javadoc 이 못박는다.

  > @implSpec If no exceptions are thrown during processing, then this operation only ever produces a single element.

비용 — `windowFixed` 는 창 하나 분량만 들고 있으면 되지만, javadoc 이 이렇게 경고한다.

> @apiNote For efficiency reasons, windows may be allocated contiguously and eagerly. This means that choosing large window sizes for small streams may use excessive memory for the duration of evaluation of this operation.

### (4) 경계 — 빈 스트림과 안 나눠떨어지는 창

**언제 쓰나** — 창 단위 배치에서 마지막 묶음 처리를 정할 때.

**실행 결과** (`Ex.java` — 50-a)

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

```text
  빈 스트림에서

   windowFixed  ->  []        창을 하나도 안 만든다
   scan         ->  []        누적할 것이 없다
   fold         ->  [0]       <- 초깃값이 그대로 한 개 나온다
                              (fold 만 원소가 있다 — reduce(identity, ...) 와 같은 성격)
```

그림 해설 (한 단계씩):

- 셋 중 **`fold` 만 빈 스트림에서 원소를 낸다.** 초깃값 공급자(`() -> 0`)가 곧 답이다.
- `windowFixed` 의 javadoc 이 "If the stream is empty then no window will be produced" 라고 못박는다.
- 원소 수가 창 크기보다 **작으면** 둘 다 **짧은 창 하나**를 낸다 — `windowSliding(5)` 에 2개를 넣어도 `[[1, 2]]` 다.

비용 — 마지막 창이 짧을 수 있다는 것을 **소비하는 쪽이 알아야 한다.** "항상 N개"를 가정한 코드가 여기서 깨진다.

### (5) 직접 만들기 — 상태와 단락 평가

**언제 쓰나** — 내장 넷으로 안 되는 상태 있는 변환이 필요할 때.

직접 쓴 최소 예제 셋이다(`Ex.java` — 50-b).

```java
// (a) 연달아 같은 값이면 뒤엣것을 버린다 — 직전 값 하나를 기억해야 한다
static <T> Gatherer<T, ?, T> dedupeAdjacent() {
    return Gatherer.ofSequential(
            () -> new Object() { T prev = null; boolean started = false; },   // initializer
            Gatherer.Integrator.ofGreedy((state, element, downstream) -> {    // integrator
                if (!state.started || !Objects.equals(state.prev, element)) {
                    state.started = true;
                    state.prev = element;
                    return downstream.push(element);
                }
                return true;            // 버리고 계속
            })
    );
}

// (b) 조건을 만족한 원소까지 내보내고 거기서 끝낸다 — 단락 평가
static <T> Gatherer<T, ?, T> takeUntilInclusive(Predicate<? super T> stop) {
    return Gatherer.ofSequential(
            Gatherer.Integrator.of((state, element, downstream) -> {
                boolean more = downstream.push(element);
                return more && !stop.test(element);   // false 를 돌려주면 소스가 멈춘다
            })
    );
}

// (c) 다 흐른 뒤에 한 번 더 밀어 넣는다 — finisher
static Gatherer<Integer, ?, String> sumWithTrailer() {
    return Gatherer.ofSequential(
            () -> new int[1],
            Gatherer.Integrator.<int[], Integer, String>ofGreedy((state, element, downstream) -> {
                state[0] += element;
                return downstream.push("원소 " + element);
            }),
            (state, downstream) -> downstream.push("합계 " + state[0])        // finisher
    );
}
```

**실행 결과** (`Ex.java` — 50-b, JDK 25.0.1)

```text
--- (1) dedupeAdjacent — 연속 중복만 제거(distinct 와 다르다)
입력           : [a, a, b, b, b, a, c, c]
dedupeAdjacent : [a, b, a, c]
distinct       : [a, b, c]
--- (2) takeUntilInclusive — takeWhile 과의 차이
입력                    : [1, 3, 5, 8, 9, 11]
takeWhile(홀수)         : [1, 3, 5]
takeUntilInclusive(짝수): [1, 3, 5, 8]
--- (3) 정말로 단락되나 — peek 로 센다
결과  : [1, 3, 5, 8]
소스가 흘려보낸 원소 : [1, 3, 5, 8]
--- (4) 무한 스트림에도 붙는다
[1, 2, 3, 4]
--- (5) finisher — 스트림이 끝난 뒤 한 개 더
[원소 1, 원소 2, 원소 3, 합계 6]
--- (6) andThen — Gatherer 를 이어 붙인다
[[1, 2], [3, 4]]
--- (7) gather 는 중간 연산이다 — 뒤에 아무거나 붙는다
[7, 11]
```

```text
  dedupeAdjacent 의 메모지 한 장

  입력  a    a    b    b    b    a    c    c
  메모  -    a    a    b    b    b    a    c    <- 직전 값
  판정  새   같   새   같   같   새   새   같
  출력  a         b              a    c
                                      = [a, b, a, c]

  distinct 는 지나간 값을 전부 기억한다 -> [a, b, c]
  Gatherer 는 한 개만 기억한다          -> [a, b, a, c]
```

그림 해설 (한 단계씩):

- `distinct()` 는 **본 적 있는 값 전부**를 기억해 두 번째 `a` 를 지운다.
- `dedupeAdjacent` 는 **직전 하나**만 기억하므로 `b` 뒤의 `a` 가 살아남는다.
- 기억하는 양이 다르면 **답이 다르다.** 상태의 크기가 곧 의미다.

```text
  단락 평가 — integrate 가 false 를 돌려주면

  소스  [1] -> push(1) -> true  && 1은 짝수 아님 -> true   계속
        [3] -> push(3) -> true  && 3은 짝수 아님 -> true   계속
        [5] -> push(5) -> true  && 5는 짝수 아님 -> true   계속
        [8] -> push(8) -> true  && 8은 짝수      -> false  <- 여기서 끝
        [9]     요청이 오지 않는다
       [11]     요청이 오지 않는다

  peek 가 [1, 3, 5, 8] 네 개만 찍힌 것이 그 증거다.
```

그림 해설 (한 단계씩):

- `takeWhile` 은 **조건이 깨진 원소를 버린다** — `[1, 3, 5]`.
- `takeUntilInclusive` 는 **깨뜨린 그 원소까지 내보내고** 끝낸다 — `[1, 3, 5, 8]`. 기존 연산으로는 이 형태가 없다.
- 단락이 진짜인지는 `peek` 로 센다. 소스가 흘려보낸 원소도 **넷뿐**이었다.
- 그래서 `Stream.iterate(1, i -> i + 1)` 같은 **무한 스트림에도 붙는다**((4)의 `[1, 2, 3, 4]`).
- `Integrator.of` 와 `Integrator.ofGreedy` 의 차이가 여기 있다. javadoc 이 못박는다.

  > Gatherers whose integrator is an instance of `Integrator.Greedy` can be assumed not to short-circuit, and the return value of invoking `Integrator.integrate` does not need to be inspected.

비용 — 상태 객체 하나와 람다 호출 한 번이 원소마다 든다. 대신 **중간 리스트를 만들지 않는다**((6)의 우회와 비교).

### (6) 24 이전에는 어떻게 했나 — 그리고 무엇이 안 됐나

**언제 쓰나** — 21 LTS 에서 같은 일을 해야 할 때.

**실행 결과** (`Ex.java` — 50-d, 17·21·25 에서 모두 돌림 — 아래는 21.0.5)

```text
--- (1) 24 이전의 우회 1 — 리스트로 먼저 받고 인덱스로 자른다
[[1, 2, 3], [4, 5, 6], [7, 8]]
--- (2) 24 이전의 우회 2 — Collectors 로 그룹핑(인덱스가 필요하다)
{0=[1, 2, 3], 1=[4, 5, 6], 2=[7, 8]}
(부작용이 있는 분류 함수 — 병렬이면 깨진다)
--- (3) 24 이전의 우회 3 — 누적(scan) 을 map + 외부 상태로
[1, 3, 6, 10, 15, 21, 28, 36]
(map 의 람다가 상태를 들고 있다 — javadoc 이 금지하는 형태)
--- (4) 셋 다 공통으로 못 하는 것 — 무한 스트림
Stream.iterate(1, i -> i+1) 에 (1)을 적용하려면 toList() 가 먼저 와야 하고,
toList() 는 무한 스트림에서 끝나지 않는다. (2)(3)도 마찬가지로 최종 연산이 먼저다.
--- (5) 상태 있는 변환을 map/filter 로 쓰면 무엇이 깨지나 — 병렬
병렬 map + 외부 상태 : [27, 32, 30, 36, 26, 21, 15, 8]
(순차의 [1, 3, 6, 10, 15, 21, 28, 36] 과 비교하라 — 실행마다 달라진다)
```

```text
  24 이전 (21)                              24 이후 (25)

  src.stream().toList()                     src.stream()
     |  <- 여기서 전부 메모리에                   .gather(windowFixed(3))
     v     무한 스트림이면 끝나지 않는다            |  <- 지연된 채로 흐른다
  IntStream.range(...)                         v     무한 스트림도 된다
     .mapToObj(i -> sub(i))                  .findFirst()
     .toList()
```

그림 해설 (한 단계씩):

- 우회 (1)은 **`toList()` 가 먼저 와야 한다.** 그 순간 지연 평가가 끝나고 전부 메모리에 올라간다.
- 우회 (2)는 분류 함수 안에 **카운터를 숨긴다.** 순차에서는 맞지만 병렬에서 무너진다.
- 우회 (3)의 병렬 결과가 그 증거다 — 같은 코드가 17·21·25 에서 **셋 다 다른 순열**을 냈다.
- Gatherer 는 **지연된 채로** 같은 일을 한다. (2)에서 `findFirst()` 가 원소 세 개만 당겨 온 것이 증거다.

비용 — 우회는 **메모리(1) 또는 정확성(2·3)** 중 하나를 내준다. Gatherer 는 둘 다 안 내준다.

### (7) `gather` 는 진짜 중간 연산이다 — 지연·단락이 통과한다

**언제 쓰나** — 큰 입력에 창 연산을 걸 때. Collector 와 어느 쪽을 쓸지 고를 때.

**실행 결과** (`Ex.java` — 50-c, JDK 25.0.1)

```text
--- (1) gather 는 지연된다 — 최종 연산 없이는 한 원소도 안 흐른다
최종 연산 없음 — 흘러간 원소 : []
--- (2) 단락 평가가 gather 를 통과한다 — findFirst 는 3개만 당긴다
결과 : Optional[[1, 2, 3]]
흘러간 원소 : [1, 2, 3]
--- (3) 같은 일을 Collector 로 하면 전부 흘러간다
결과 : {0=[1, 2, 3], 1=[4, 5, 6], 2=[7, 8]}
흘러간 원소 : [1, 2, 3, 4, 5, 6, 7, 8]
--- (4) Collector 는 최종 연산이라 뒤에 중간 연산을 못 붙인다
gather  뒤 : [2, 2]
collect 뒤 : [10, 20, 30, 40]  (스트림을 새로 만들어야 한다)
--- (5) gather 와 collect 를 한 파이프라인에 같이 쓴다
{1=2, 3=4, 5=6}
```

```text
  gather + findFirst                       collect(groupingBy)

  [1][2][3] 만 소스에서 나온다               [1]...[8] 전부 소스에서 나온다
      |                                         |
  windowFixed 가 창 하나를 채우자마자        그룹핑은 마지막 원소까지 봐야
  findFirst 가 "그만" 이라고 한다            어느 키에 들어갈지 끝난다
      |                                         |
  peek 3회                                   peek 8회
```

그림 해설 (한 단계씩):

- `gather(...).findFirst()` 는 **원소 셋만** 당겼다. 창 하나가 채워지자 파이프라인이 끝났다.
- 같은 묶음을 `Collectors.groupingBy` 로 만들면 **여덟 개 전부** 흘러간다 — 최종 연산이라 단락이 없다.
- 그래서 **큰 입력에서 앞쪽 일부만 필요하면 Gatherer 가 싸다.**
- 그리고 `gather` 뒤에는 `map`·`filter` 가 그대로 붙지만, `collect` 뒤에는 **`stream()` 을 새로 만들어야** 한다.

비용 — Gatherer 는 지연을 지키는 대신 **한 원소씩 흐른다.** 전체를 어차피 다 볼 거라면 Collector 와 비용이 비슷하다.

## 문법 — 형태와 규칙

### 네 함수로 된 인터페이스

javadoc 이 Gatherer 를 이렇게 정의한다.

> A `Gatherer` is specified by four functions that work together to process input elements, optionally using intermediate state, and optionally perform a final action at the end of input. They are:
> - creating a new, potentially mutable, state (`initializer()`)
> - integrating a new input element (`integrator()`)
> - combining two states into one (`combiner()`)
> - performing an optional final action at the end of input (`finisher()`)

| 함수 | 시그니처 | 없으면 |
|---|---|---|
| `initializer` | `Supplier<A>` | 기본값 = 상태 없음(stateless 로 취급) |
| `integrator` | `Integrator<A, T, R>` — `boolean integrate(A, T, Downstream<R>)` | **필수** |
| `combiner` | `BinaryOperator<A>` | 기본값 = **순차 전용**이 된다 |
| `finisher` | `BiConsumer<A, Downstream<R>>` | 기본값 = 끝에서 아무것도 안 한다 |

javadoc 이 동작을 이 의사코드로 못박는다.

> ```java
> Gatherer.Downstream<? super R> downstream = ...;
> A state = gatherer.initializer().get();
> for (T t : data) {
>     gatherer.integrator().integrate(state, t, downstream);
> }
> gatherer.finisher().accept(state, downstream);
> ```

### 만드는 팩토리

```java
Gatherer.of(integrator)                                   // 상태 없음 · 병렬 가능
Gatherer.of(integrator, finisher)
Gatherer.of(initializer, integrator, combiner, finisher)  // 전부 지정
Gatherer.ofSequential(integrator)                         // 순차 전용
Gatherer.ofSequential(initializer, integrator)
Gatherer.ofSequential(initializer, integrator, finisher)
```

- `ofSequential` 은 **combiner 를 기본값으로 둔다** = 순차 실행만 한다는 선언이다.
- javadoc: "Gatherers whose combiner is `defaultCombiner()` **may only be evaluated sequentially.**"

### `Downstream.push` 의 반환값이 계약이다

```java
boolean push(R element);       // false = 아래쪽이 더는 안 받겠다
default boolean isRejecting()  // 기본 false
```

- `integrate` 가 **`false` 를 돌려주면 소스가 멈춘다.** javadoc: "When the integrator function returns `false`, it shall be interpreted just as if there were no more elements to pass it."
- 그래서 `push` 결과를 **그대로 돌려주는 것**이 보통의 올바른 형태다.
- 단락을 안 할 거면 `Integrator.ofGreedy` 로 감싸 **"나는 멈추지 않는다"고 선언**한다. 그러면 구현이 반환값 검사를 건너뛴다.

### 내장 다섯 (`Gatherers`)

| 하고 싶은 일 | 팩토리 | 입력 N개 → 출력 |
|---|---|---|
| 겹치지 않는 묶음 | `windowFixed(int)` | `ceil(N/size)` 개 (마지막이 짧을 수 있다) |
| 한 칸씩 미는 묶음 | `windowSliding(int)` | `N - size + 1` 개 (N < size 면 1개) |
| 순서 의존 접기 | `fold(Supplier, BiFunction)` | **1개** |
| 누적 중간값 | `scan(Supplier, BiFunction)` | N개 |
| 동시 매핑 | `mapConcurrent(int, Function)` | N개 (순서 유지) |

`mapConcurrent` 의 javadoc.

> An operation which executes a function concurrently with a configured level of max concurrency, using **virtual threads**. This operation preserves the ordering of the stream.

**실행 결과** (`Ex.java` — 50-c)

```text
--- (10) mapConcurrent — 가상 스레드로 동시에 매핑
결과 : [v1, v2, v3, v4, v5, v6]
6개 × 200ms 를 동시성 6으로 : 700ms 미만 (실측 212ms)
```

- 각 매퍼가 200ms 를 자는데 **여섯 개가 212ms 만에** 끝났다. 순차라면 1,200ms 다.
- 이 수치는 **이 머신 1회 측정**이다(JMH 아님). 재현되는 것은 절댓값이 아니라 **"순차의 1/6 자릿수"** 쪽이다.

### `andThen` 으로 이어 붙인다

```java
Stream.of(1, 1, 2, 2, 3, 3, 4)
      .gather(Ex.<Integer>dedupeAdjacent().andThen(Gatherers.windowFixed(2)))
      .toList();
// [[1, 2], [3, 4]]
```

- `andThen` 은 **Gatherer 둘을 하나로** 만든다. `gather(a).gather(b)` 와 결과가 같다.
- `Stream.gather` 의 javadoc: "Implementations are allowed, but not required, to detect consecutive invocations and compose them into a single, fused, operation."

## 어디서 틀리나

### 1. 21 LTS 에 25 예제를 붙여 넣는다

- 런타임 에러가 아니라 **컴파일 에러**다((1)). 빌드가 안 되므로 배포 전에 드러난다 — 이것만은 다행이다.
- 반대로 **IDE 가 25 를 가리키는데 빌드는 21** 인 구성에서는 IDE 에서만 초록색이다가 CI 에서 깨진다.
- 방어: `--release` 를 프로젝트의 실제 타깃으로 고정한다. (2)에서 본 것처럼 `--release 21` 은 정확히 21 의 API 만 보여 준다.

### 2. `fold` 를 `reduce` 대신이라고 생각한다

```java
Stream.of(1,2,3,4,5).gather(Gatherers.fold(() -> 0, Integer::sum)).toList();  // [15] — 리스트다
Stream.of(1,2,3,4,5).reduce(0, Integer::sum);                                  // 15  — 값이다
```

- `fold` 는 **스트림을 돌려준다.** 최종 연산이 아니다. 값을 꺼내려면 `findFirst()` 를 더 붙인다.
- 빈 스트림에서 `fold` 는 `[0]`, `scan` 은 `[]` 다((4)) — 여기서 갈린다.
- `fold` 의 javadoc 이 존재 이유를 적는다: "for scenarios where **no combiner-function can be implemented**, or for reductions which are **intrinsically order-dependent**."

### 3. 창이 돌려준 `List` 를 고친다

**실행 결과** (`Ex.java` — 50-c)

```text
--- (6) windowFixed 가 돌려주는 List 는 수정 불가
window.add : java.lang.UnsupportedOperationException: null
```

- javadoc 이 못박는다: "@implSpec Each window produced is an **unmodifiable List**; calls to any mutator method will always cause `UnsupportedOperationException` to be thrown."
- **메시지가 `null`** 이라는 점에 주의 — `getMessage()` 로 원인을 알 수 없다. 타입으로 잡아야 한다.
- 방어: 고쳐야 하면 `new ArrayList<>(window)` 로 복사한다.

### 4. 창 크기 인자를 검증하지 않는다

**실행 결과** (`Ex.java` — 50-c)

```text
--- (7) 인자 검증 — 창 크기 0
windowFixed(0)   : java.lang.IllegalArgumentException: 'windowSize' must be greater than zero
windowSliding(0) : java.lang.IllegalArgumentException: 'windowSize' must be greater than zero
windowFixed(-1)  : java.lang.IllegalArgumentException: 'windowSize' must be greater than zero
--- (8) 예외는 언제 던져지나 — 팩토리에서인가 실행에서인가
팩토리 호출만 : java.lang.IllegalArgumentException: 'windowSize' must be greater than zero
```

- **팩토리 호출 시점에 바로 던진다.** 스트림을 돌리기 전이다.
- 그래서 설정값에서 창 크기를 읽어 오는 코드는 **스트림과 무관한 자리에서** 터진다.

### 5. `Integrator.of` 와 `ofGreedy` 를 아무거나 쓴다

- `ofGreedy` 로 선언해 놓고 `false` 를 돌려주면 **구현이 그 값을 안 볼 수 있다**(javadoc 의 implSpec).
- 반대로 단락을 안 하는데 `of` 를 쓰면 구현이 매번 반환값을 검사한다 — 손해는 작지만 **의도가 안 드러난다.**
- 방어: **멈출 수 있으면 `of`, 절대 안 멈추면 `ofGreedy`.**

### 6. 상태 객체를 밖으로 내보낸다

javadoc 이 금지한다.

> Implementations of Gatherer **must not capture, retain, or expose to other threads**, the references to the state instance, or the downstream `Downstream`, for longer than the invocation duration of the method which they are passed to.

- 상태를 필드에 저장하거나 다른 스레드에 넘기면 **병렬에서 조용히 깨진다.**
- 같은 이유로 `Gatherer` 인스턴스를 **한 번 만들어 필드에 두고 여러 스트림에 재사용**하는 것은 괜찮다 — 상태는 `initializer` 가 매번 새로 만든다.

### 7. 순차 전용 Gatherer 를 병렬 스트림에 걸고 병렬을 기대한다

**실행 결과** (`Ex.java` — 50-c)

```text
--- (9) 순차 전용 Gatherer 를 병렬 스트림에 걸면
parallel + windowFixed(5) : [[1, 2, 3, 4, 5], [6, 7, 8, 9, 10], [11, 12]]
parallel + fold           : [78]
parallel + scan (앞 4개)   : [1, 3, 6, 10]
```

- **예외는 나지 않는다.** 결과도 순차와 같다.
- 하지만 `ofSequential` 로 만든 단계는 **병렬로 나뉘지 않는다.** 병렬로 얻을 것이 없는 채로 병렬 오버헤드만 낸다.
- 방어: 병렬이 목적이면 **combiner 를 주는 `Gatherer.of(4-인자)`** 로 만든다. 못 주겠으면 그 파이프라인은 순차로 둔다.

## 구현 세부사항 대 언어 보장

| 관측한 것 | 보장인가 | 근거 |
|---|---|---|
| `Gatherer`·`Gatherers`·`Stream.gather` 는 24부터 | **보장** | `src.zip` 의 `@since 24` |
| 22·23 에서는 프리뷰 | **보장** | `--release 22/23` 이 `preview API and is disabled by default` 로 거부 |
| 17·21 에는 없다 | **보장** | `--release 21` 이 `cannot find symbol` |
| `integrate` 가 `false` 면 소스가 멈춘다 | **보장** | javadoc implSpec — "shall be interpreted just as if there were no more elements" |
| `fold` 는 원소를 하나만 낸다 | **보장** | javadoc implSpec |
| 창의 `List` 가 수정 불가 | **보장** | javadoc implSpec |
| `ofSequential` 이 순차로만 돈다 | **보장** | javadoc implSpec — "may only be evaluated sequentially" |
| `gather(a).gather(b)` 가 합쳐지는지 | **보장 아님** | javadoc — "allowed, but **not required**, to detect consecutive invocations" |
| 창이 통째로 미리 할당되는지 | **보장 아님** | javadoc apiNote — "may be allocated contiguously and eagerly" |
| `UnsupportedOperationException` 의 **메시지가 `null`** | **보장 아님** | 실측 결과일 뿐 |
| `mapConcurrent` 의 212ms | **보장 아님** | 이 머신 1회 측정 |

**세 JDK 실측 요약**

```text
프로그램            17.0.13          21.0.5           25.0.1
50-a  (Gatherers)   컴파일 실패      컴파일 실패      정상
50-b  (커스텀)      컴파일 실패      컴파일 실패      정상
50-c  (대 Collector) 컴파일 실패      컴파일 실패      정상
50-d  (24 이전 우회) 정상            정상             정상
                                  <- (5)의 병렬 결과만 실행마다 다르다
```

- 50-d 의 (5) 병렬 결과는 **세 판에서 전부 달랐고, 같은 판에서도 매번 다르다.** 순서가 보장되지 않는 코드라 정상이다.
- 나머지 네 절은 **결정적**이다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 일 | 고를 것 |
|---|---|
| N개씩 묶어 배치 전송 | `gather(Gatherers.windowFixed(N))` |
| 이동 평균·이웃 차이 | `gather(Gatherers.windowSliding(N))` |
| 누적 합·누적 최대 | `gather(Gatherers.scan(...))` |
| 순서에 의존하는 접기 | `gather(Gatherers.fold(...))` — `reduce` 로 안 되는 경우 |
| 연속 중복 제거·상태 있는 필터 | **직접 만든다**((5)) |
| I/O 여러 개를 동시에 | `gather(Gatherers.mapConcurrent(n, f))` |
| 결과를 **그냥 모으기만** | `collect(Collector)` — 47·48번. Gatherer 가 아니다 |
| 뒤에 더 붙일 연산이 **없다** | `collect` 로 충분하다 |
| **21 LTS 프로젝트** | 쓸 수 없다 — (6)의 우회 또는 직접 루프 |
| 병렬 이득이 목적 | combiner 를 줄 수 있을 때만. 못 주면 순차로 둔다 |

판단 규칙 세 줄.

- **"앞에 뭐가 지나갔는지 알아야 하나"** — 그렇다면 Gatherer 후보다. 아니면 `map`·`filter` 로 끝난다.
- **"이 뒤에 연산을 더 붙일 건가"** — 붙인다면 Gatherer, 여기서 끝이면 Collector.
- **"타깃이 24 이상인가"** — 아니면 나머지 답은 의미가 없다.

## 핵심 문장

- Gatherer 는 **상태를 들고 0~N 개를 내보내는 중간 연산**이다 — `map`(1→1)·`filter`(1→0|1)이 못 하던 자리를 메운다.
- `Collector` 와의 차이는 능력이 아니라 **자리**다. Collector 는 벨트 끝이라 뒤가 없고, Gatherer 는 중간이라 뒤가 있다.
- `integrate` 가 `false` 를 돌려주는 것이 **단락 평가**다 — 그래서 `gather` 를 무한 스트림에 걸 수 있다.
- **17·21 에서는 컴파일이 안 된다.** `@since 24` 이고, 22·23 에서는 프리뷰였다(`--release` 로 실증).
- 내장 다섯 중 `fold` 만 **빈 스트림에서 원소를 낸다**(초깃값). `windowFixed`·`scan` 은 빈 스트림을 낸다.

## 관련 자료

- [`../46-terminal-operations/`](../46-terminal-operations/) — **이 주제의 선행.** 그쪽은 **최종 연산이 언제 파이프라인을 돌리나**까지, 여기는 **그 파이프라인에 내가 단계를 하나 더 넣는 법**부터
- [`../45-intermediate-operations/`](../45-intermediate-operations/) — `map`·`filter`·`flatMap`·`mapMulti`. 그쪽은 **정해진 중간 연산의 계약**까지, 여기는 **그 목록에 없는 변환**부터
- [`../44-stream-creation/`](../44-stream-creation/) — 소스. `Stream.iterate` 로 만든 무한 스트림을 (5)에서 그대로 쓴다
- [`../47-collectors-basics/`](../47-collectors-basics/) · [`../48-collectors-grouping/`](../48-collectors-grouping/) — `Collector`. 그쪽은 **모으는 방법**까지, 여기는 **모으기 전에 흐름을 바꾸는 것**까지
- [`../49-parallel-streams/`](../49-parallel-streams/) — 병렬의 조건. Gatherer 의 combiner 유무가 그쪽 규칙에 그대로 걸린다
- [`../../../../../../history/java/java-24.md`](../../../../../../history/java/java-24.md) — **왜·언제 들어왔나**가 정본(JEP 461 프리뷰 → 473 2차 → 485 정식). 여기는 **어떻게 쓰나**만
- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 50번)
- [**56번 주제**](../56-virtual-threads/)(가상 스레드) — `mapConcurrent` 가 쓰는 그 스레드
- [**31번 주제**](../31-functional-interfaces/)(함수형 인터페이스) — `Supplier`·`BiConsumer`·`BinaryOperator` 가 Gatherer 의 네 함수다

## 용어 풀이

- **Gatherer** — 상태를 가질 수 있는 사용자 정의 **중간** 연산. `Stream.gather(...)` 로 끼운다. Java 24부터.
- **`Gatherers`** — 내장 Gatherer 다섯을 만드는 팩토리 클래스(`windowFixed`·`windowSliding`·`fold`·`scan`·`mapConcurrent`).
- **initializer** — 원소를 받기 전에 상태 객체를 하나 만드는 함수. 예: `() -> new int[1]` 로 누적용 칸 하나를 만든다.
- **integrator** — 원소 하나를 받아 처리하고 `boolean` 을 돌려주는 함수. `false` 면 "더 안 받는다"는 뜻이다.
- **combiner** — 병렬로 나뉘어 생긴 두 상태를 하나로 합치는 함수. 안 주면 그 Gatherer 는 순차로만 돈다.
- **finisher** — 입력이 다 끝난 뒤 한 번 불리는 함수. 남은 것을 마저 내보낼 자리다. 예: `fold` 가 최종값을 여기서 밀어 넣는다.
- **`Downstream`** — 다음 단계로 원소를 밀어 넣는 통로. `push(x)` 가 `false` 를 돌려주면 아래가 더는 안 받는다는 뜻이다.
- **greedy integrator** — 절대 단락하지 않겠다고 선언한 integrator(`Integrator.ofGreedy`). 구현이 반환값 검사를 건너뛸 수 있다.
- **단락 평가(short-circuiting)** — 답이 정해지면 나머지를 안 보고 멈추는 것. Gatherer 에서는 `integrate` 가 `false` 를 돌려주는 것이다.
- **프리뷰 API(preview API)** — 정식이 되기 전 시험 기간의 API. `--enable-preview` 없이는 컴파일이 거부된다. Gatherers 는 22·23 이 그랬다.
- **윈도(window)** — 연속한 원소 N개를 하나로 묶은 것. 겹치지 않으면 fixed, 한 칸씩 밀면 sliding.
- **prefix scan** — 누적 중간값을 전부 내놓는 연산. `[1,2,3]` → `[1,3,6]`. `reduce` 가 최종값 하나만 내놓는 것과 대비된다.

## 더 들어가면

- **`Gatherer.of` 의 4인자 판이 병렬의 문이다.**\
  combiner 를 주면 구현이 입력을 나눠 부분마다 상태를 만들고 마지막에 합친다.\
  javadoc 이 그 규칙을 못박는다 — "Outputs and state later in the input sequence will be **discarded** if processing an earlier partition short-circuits."\
  즉 병렬 + 단락은 **앞쪽 조각이 이기는** 구조다.
- **javadoc 이 `map` 을 Gatherer 로 다시 쓴 예제를 싣는다.**

  > ```java
  > public static <T, R> Gatherer<T, ?, R> map(Function<? super T, ? extends R> mapper) {
  >     return Gatherer.of(
  >         (unused, element, downstream) -> downstream.push(mapper.apply(element))
  >     );
  > }
  > ```

  **기존 중간 연산이 전부 Gatherer 로 표현된다**는 뜻이다. `gather` 를 javadoc 이 "extension point" 라 부르는 이유다.
- **`Stream.gather` 의 기본 구현은 spliterator 를 감싼다.**

  > @implSpec The default implementation obtains the spliterator of this stream, wraps that spliterator so as to support the semantics of this operation on traversal, and returns a new stream associated with the wrapped spliterator. ... but **the wrapped spliterator may choose to not support splitting.**

  기본형 스트림(`IntStream` 등)에는 `gather` 가 **없다** — 박싱해서 `Stream` 으로 넘어와야 한다.
- **`mapConcurrent` 의 예외 처리가 특이하다.**

  > @implSpec If a result of the function is to be pushed downstream but instead the function completed exceptionally then the corresponding exception will instead be **rethrown by this method as an instance of `RuntimeException`**, after which any remaining tasks are canceled.

  검사 예외를 던지는 매퍼는 `RuntimeException` 으로 감싸여 나온다. 이 문서의 (10) 예제도 `Thread.sleep` 의 `InterruptedException` 을 직접 감싸야 컴파일됐다.
