# language/18-functional-concepts — 불변·순수 함수·고차 함수·지연 평가 — 정리 (힌트)

## 해결하는 문제

함수가 **바깥 상태를 몰래 읽고 쓰면**, 같은 호출이 언제 부르느냐에 따라 다른 결과를 낸다. 테스트·병렬화·캐싱이 모두 어려워진다.

```text
  순수하지 않은 함수                       순수 함수
  total += price  (바깥 변수 수정)         sum(prices) → 값 반환, 바깥은 그대로
  → 두 번 부르면 두 배, 병렬이면 경쟁       → 몇 번을 언제 불러도 같은 답
```

- *순수 함수(pure function)*: 결과가 인자에만 달려 있고, 바깥에 보이는 부수효과가 없는 함수.
- *부수효과(side effect)*: 반환값 말고 바깥에 남기는 변화. 변수·컬렉션 수정, I/O, 로그, 시간 읽기.
- *참조 투명성(referential transparency)*: 식을 그 값으로 바꿔 써도 프로그램 의미가 같은 성질. 순수 함수 호출이 이것을 갖는다.

쉬운 예: 계산기와 은행 창구다.
- 계산기 `3 + 4`는 언제 눌러도 7이다 → 순수.
- 창구의 "잔액 조회"는 앞에서 누가 입금했느냐에 따라 다르다 → 상태 의존.
- 수도꼭지는 틀 때만 물이 나온다. 물탱크는 미리 다 채워 둔다 → 지연 평가 vs 즉시 평가.

똑같은 구조다.\
함수형 개념은 "부수효과를 어디에 두나"와 "계산을 언제 하나"를 통제한다. 그 통제를 모르고 쓰면 **실행되지 않는 부수효과, 두 번 못 쓰는 스트림, 사라지는 원소**가 생긴다.

실무 예:
- 같은 `Stream`을 두 번 쓰다 `IllegalStateException: stream has already been operated upon or closed`.
- `map` 안에 넣은 감사 로그가 `count()`에서는 한 줄도 안 남는다.
- 병렬 스트림에서 공유 `ArrayList`에 `add`했더니 원소가 모자란다.
- Python 제너레이터를 두 번째 보고서에 다시 썼더니 **예외 없이 빈 결과**가 나온다.

부수효과를 바깥으로 미는 **설계**(Functional Core, Imperative Shell)는 [software-design/26](../../software-design/26-functional-core-imperative-shell/2-summary.md)에, 불변 객체 설계는 [software-design/19](../../software-design/19-immutability-and-value-objects/2-summary.md)에 있다. 이 노트는 **언어 개념과 런타임 동작**을 다룬다.

## 동작·원리

### 1. 불변과 구조 공유 — 고치지 않고 새로 만들되, 대부분을 공유한다

```text
  base = 1 → 2 → 3 → nil
  a = base.push(10)    10 ─┐
                           ├──> 1 → 2 → 3 → nil      ← 꼬리 공유(복사 없음)
  b = base.push(20)    20 ─┘
  base는 그대로 1,2,3
```

- *불변(immutable)*: 만든 뒤 바뀌지 않는 값.
- *영속 자료구조(persistent data structure)*: 갱신하면 새 판을 만들고 옛 판도 그대로 쓸 수 있는 자료구조. 바뀌지 않은 부분을 참조로 공유해 비용을 줄인다.
- 실험(`eclipse-temurin:21-jdk` 21.0.12, `scratchpad/lang/05/e18/Lazy.java`의 `Cons` record):

```text
a=10,1,2,3  b=20,1,2,3  base=1,2,3  꼬리 공유: true
```

- 공유해도 안전한 이유: 아무도 고치지 않기 때문이다. 같은 구조를 가변으로 공유하면 [06](../06-values-references-passing/2-summary.md)의 "얕은 복사 사고"가 난다.
- 리스트 앞에 붙이기는 O(1)이다. 중간 위치를 갱신하려면 그 앞쪽 노드들을 복사(경로 복사)해야 한다. n번째 원소 읽기는 복사가 필요 없지만 앞에서부터 따라가야 해 O(n)이다(SICP 2.2.1 `list-ref`). 트리 기반 영속 맵은 [data-structure/26-persistent](../../data-structure/26-persistent/2-summary.md).

### 2. 고차 함수 — 함수를 받고 함수를 돌려준다

```text
  map(f)    : [a, b, c] → [f(a), f(b), f(c)]
  filter(p) : [a, b, c] → p가 참인 것만
  reduce(⊕) : [a, b, c] → a ⊕ b ⊕ c        (⊕가 결합적이면 쪼개서 병렬로 가능)
```

- *고차 함수(higher-order function)*: 함수를 인자로 받거나 함수를 반환하는 함수. 함수를 값으로 넘기고 돌려줄 수 있는 1급 함수가 있으면 된다. 클로저([07](../07-scope-closures-first-class-functions/2-summary.md))는 필수가 아니지만(예: Java의 정적 메서드 참조 `Integer::parseInt`도 함수형 인터페이스 값으로 넘어간다, JLS 15.13) 바깥 값을 담아 함수를 만들어 돌려줄 때 필요하다.
- SICP 1.3 "Formulating Abstractions with Higher-Order Procedures"가 이 주제다(MIT Press 공개 HTML 목차로 확인).
- `map`·`filter`에 넘기는 함수가 **순수**하면, 라이브러리가 적용 순서를 바꾸거나 결과에 필요 없는 호출을 건너뛰거나 병렬로 나눠도 결과가 같다. 라이브러리는 그 전제와 무관하게 "결과에 영향이 없음을 증명하면" 연산을 생략할 수 있다(`java.util.stream` 패키지 문서) — 부수효과가 있으면 그 생략이 눈에 보일 뿐이다. 결과가 필요한 호출은 순수해도 생략되지 않고, 순서가 정의된 스트림은 결과 순서를 지킨다. 아래 실험들은 이 전제가 깨질 때다.

### 3. 지연 평가 — 최종 연산이 당길 때만 계산한다

```text
  Java Stream 파이프라인
  source ──> map ──> filter ──> findFirst(최종 연산)
             (중간 연산: 연결만 해 둠)    │
                                          └─ 당긴다: 원소 하나씩 세로로 내려보냄, 답이 나오면 멈춤

  원소 1: map 1 → filter 10 (탈락)
  원소 2: map 2 → filter 20 (통과) → findFirst = 20, 원소 3·4·5는 계산 안 함
```

- *지연 평가(lazy evaluation)*: 값이 필요해질 때까지 계산을 미루는 것.
- *중간 연산*: 새 스트림을 돌려주고 아무것도 계산하지 않는다(`map`, `filter`). *최종 연산*: 파이프라인을 실제로 돌린다(`forEach`, `count`, `collect`, `findFirst`).
- `java.util.stream` 패키지 문서 "Laziness-seeking": "find the first String with three consecutive vowels" need not examine all the input strings.
- SICP 3.5 "Streams"(3.5.1 "Streams Are Delayed Lists")가 같은 생각을 지연 리스트로 설명한다.

### 실험 A: 언제, 몇 번 계산되나

(실험, `eclipse-temurin:21-jdk` 21.0.12 / 호스트 CPython 3.12.3, `scratchpad/lang/05/e18/Lazy.java`·`once.py`, 2026-10-07)

```text
Java   파이프라인 만든 직후 (map 출력 없음)
         map 1
         filter 10
         map 2
         filter 20
       findFirst = 20                         ← 3·4·5는 map조차 안 함
Python generator 만든 직후 — 본문은 아직 실행 안 됨
         (본문 시작)
       next: 1
```

- 이 `map`·`filter` 파이프라인에서는 원소가 단계별로(가로로) 처리되지 않고 원소마다 끝까지(세로로) 내려갔다. 그래서 단락(short-circuit)이 가능하다. `sorted` 같은 상태 보유 중간 연산은 결과를 내기 전에 입력 전체를 처리할 수 있다(`java.util.stream` 패키지 문서 "Stateful operations may need to process the entire input").
- Python 제너레이터도 첫 `next()` 전에는 본문을 실행하지 않는다.

### 4. 한 번만 소비된다 — 그런데 언어마다 실패하는 모양이 다르다

```text
  Java Stream       : 두 번째 소비 → IllegalStateException (시끄럽게 실패 — JDK 21 구현에서 관찰, 명세는 "감지하면 던질 수 있다")
  Python 제너레이터 객체: 두 번째 소비 → 빈 결과 (조용히 실패)
  JS 제너레이터 객체    : 두 번째 소비 → 빈 결과 (조용히 실패)
  ※ 배열 같은 이터러블은 [Symbol.iterator]()가 순회마다 새 이터레이터를 주므로 다시 돌 수 있다(MDN "Iteration protocols")
```

### 실험 B: 두 번째 소비

(실험 A와 같은 환경 + `node:22-alpine` v22.23.2, `Lazy.java`·`once.py`·`once.js`)

```text
Java   두 번째 소비: java.lang.IllegalStateException: stream has already been operated upon or closed
Python first : [0, 10, 20]
       second: []   ← 예외 없이 빈 결과
JS     first : [1,2]
       second: []  ← 예외 없이 빈 결과
```

- `Stream` 문서: "A stream should be operated on (invoking an intermediate or terminal stream operation) only once. … A stream implementation may throw IllegalStateException if it detects that the stream is being reused."
- Python·JS는 같은 실수에 예외를 내지 않는다. 두 번째 집계가 0건으로 "성공"한다. 조용한 실패 쪽이 더 위험하다.

### 5. 부수효과가 지연·최적화·병렬과 만날 때

```text
  라이브러리가 할 수 있는 일            순수 함수일 때     부수효과가 있을 때
  단계 건너뛰기(count 최적화)          결과 같음          부수효과가 사라짐
  원소 일부만 처리(단락)               결과 같음          일부 원소에만 부수효과
  여러 스레드로 나눠 실행(parallel)    결과 같음          공유 상태 경쟁
```

### 실험 C: `map`의 부수효과가 건너뛰어지고, 병렬에서 사라진다

(실험 A와 같은 Java 환경, `Lazy.java`·`Closed.java`)

```text
count = 3, map 부수효과로 모은 것 = []                    ← map이 한 번도 안 불림
filter 뒤 count = 3, 모은 것 = [1, 2, 3]                  ← 크기를 모르면 map이 돈다
parallel add round 1: size = 59685 (기대 100000)
parallel add round 2: size = 68777 (기대 100000)
parallel add round 3: size = 71746 (기대 100000)
collect 사용: size = 100000
consume after close: java.lang.IllegalStateException: source already consumed or closed
eager inside try: [user_001, user_002]
```

- `count()`: 원본 크기를 알면 파이프라인을 돌리지 않을 수 있다. `Stream.count` API Note: "An implementation may choose to not execute the stream pipeline … if it is capable of computing the count directly from the stream source. In such cases no source elements will be traversed and no intermediate operations will be evaluated."
  - `map`은 원소 수를 바꾸지 않으니 건너뛰어도 개수는 같다. 중간에 `filter`가 있으면 크기를 몰라 실제로 돈다. **같은 `map`이 앞뒤 연산에 따라 실행되기도, 안 되기도 한다.**
- 병렬 `forEach(out::add)`: `ArrayList`는 스레드 안전하지 않다. 여러 스레드의 `add`가 겹쳐 원소가 사라졌다(3회 모두 10만 미만, 예외는 이번 3회에는 나지 않았다). 사실 점검 재실행(JVM 3회 × 3라운드)도 9라운드 모두 57,126 ~ 81,564로 10만 미만이었고 예외는 없었다. `collect`는 스레드별 부분 결과를 만들고 합쳐 10만 개가 정확했다.
  - 패키지 문서 "Side-effects": "Side-effects in behavioral parameters to stream operations are, in general, discouraged, as they can often lead to unwitting violations of the statelessness requirement, as well as other thread-safety hazards."
- `Files.lines`를 try-with-resources 안에서 **반환만** 하면, 지연 스트림이 파일이 닫힌 뒤에야 소비되어 `IllegalStateException: source already consumed or closed`. 자원 수명 안에서 최종 연산까지 끝내야 한다.

## 쓰이는 자료구조·알고리즘

- **지연 리스트(스트림)**: 머리 + "꼬리를 계산하는 함수(thunk)". 필요할 때 꼬리를 계산하고, 메모하면 한 번만 계산한다(SICP 3.5.1). Java `Stream`은 메모하지 않는 **한 번짜리 당김(pull) 파이프라인**이라 재사용이 금지된다.
- **영속 자료구조**: 구조 공유 연결 리스트(실험 §1), 경로 복사 트리([data-structure/26-persistent](../../data-structure/26-persistent/2-summary.md)).
- **반복자**: `next()`로 하나씩 당기는 인터페이스. 상태(현재 위치)를 가지므로 한 번 끝나면 다시 처음으로 가지 않는다([languages/python/syntax/16](../../../languages/python/syntax/16-iterator-protocol/2-summary.md)).
- **결합적 리덕션의 병렬 분할**: `reduce(⊕)`는 ⊕가 결합적이면 구간을 나눠 각자 접고 합칠 수 있다(분할 정복, [algorithm/24-divide-conquer](../../algorithm/24-divide-conquer/2-summary.md)). `collect`가 실험 C에서 정확했던 이유다.
- **메모이제이션**: 순수 함수만 결과를 캐시해도 의미가 같다([algorithm/21-dp-basics](../../algorithm/21-dp-basics/2-summary.md)).

## 적용 — 풀어나가는 법

1. **증상**: `IllegalStateException: stream has already been operated upon or closed`.
   - 원리: 스트림은 한 번만 소비된다.
   - 확인: 스트림을 필드·변수에 담아 두 번 쓰는 곳, 메서드가 같은 `Stream`을 두 소비자에게 돌려주는 곳을 찾는다.
   - 대처: 여러 번 쓸 거면 `toList()`로 모으거나 `Supplier<Stream<T>>`로 매번 새로 만든다.
2. **증상**: `map`·`peek` 안의 로그·카운터·DB 쓰기가 실행되지 않거나 횟수가 이상하다.
   - 원리: 지연 평가 + 최종 연산이 일부 단계를 건너뛸 수 있다(실험 C `count`), 단락으로 일부 원소만 처리(실험 A).
   - 대처: 부수효과는 최종 연산(`forEach`)이나 파이프라인 밖으로. 파이프라인 안 함수는 순수하게.
3. **증상**: 병렬 스트림 결과의 개수가 실행마다 다르다·가끔 `ArrayIndexOutOfBoundsException`.
   - 원리: 공유 가변 컬렉션에 부수효과로 쓴다.
   - 대처: `collect(Collectors.toList())`·`toList()`·`reduce`로 바꾼다.
4. **증상**: Python에서 두 번째 집계가 0건.
   - 확인: 그 값이 제너레이터·`map` 객체·파일 객체인지 `type(x)`로 본다.
   - 대처: 한 번 `list()`로 만들어 재사용하거나, 두 소비자가 동시에 필요하면 `itertools.tee`.

```java
// 나쁜 예: 파이프라인 안의 부수효과 + 지연 스트림 재사용
Stream<Order> paid = orders.stream().filter(Order::isPaid);
paid.map(o -> { audit.log(o); return o; }).count();   // 크기를 알 수 있으면 audit.log가 안 불릴 수 있다
paid.forEach(this::ship);                               // IllegalStateException

// 나은 예: 한 번 모으고, 부수효과는 최종 단계에서 명시적으로
List<Order> paidList = orders.stream().filter(Order::isPaid).toList();
paidList.forEach(audit::log);
paidList.forEach(this::ship);
long n = paidList.size();
```

## 장애 시나리오와 대처

### 1. 지연 스트림 두 번 소비 → `IllegalStateException` (⚠ 커리큘럼)

- 현상: 리포트 API가 특정 분기에서만 500을 낸다.
- 보이는 형태: `java.lang.IllegalStateException: stream has already been operated upon or closed`(실험 B).
- 원인: 한 `Stream`을 개수 계산과 목록 응답에 모두 썼다.
- 대처: `toList()`로 모은 뒤 두 번 쓴다. 메서드가 `Stream`을 반환하면 "한 번만 소비"라는 계약을 문서화하거나 `List`를 반환한다.

### 2. `map` 안 부수효과 → 실행이 건너뛰어진다 (⚠ 커리큘럼)

- 현상: 감사 로그가 일부 API에서만 비어 있다. 코드는 같은 `map(o -> { audit(o); return o; })`.
- 보이는 형태: 에러 없음, 로그 없음. 실험 C `count = 3, map 부수효과로 모은 것 = []`.
- 원인: `count()`가 원본 크기로 답을 내 파이프라인을 돌리지 않았다(`Stream.count` API Note). 앞에 `filter`가 있는 API에서는 돌았다.
- 대처: 부수효과를 파이프라인에서 빼 최종 단계·명시적 루프로 옮긴다. "중간 연산 함수는 순수하게"를 리뷰 규칙으로.

### 3. 병렬 스트림 + 공유 컬렉션 → 원소 유실

- 현상: 병렬로 바꾼 뒤 배치 처리 건수가 매번 다르고 실제보다 적다.
- 보이는 형태: 59,685 / 68,777 / 71,746(기대 100,000, 실험 C), 재실행 9라운드 57,126 ~ 81,564. 실행에 따라 `ArrayIndexOutOfBoundsException`이 날 수도 있다 [?].
- 원인: 스레드 안전하지 않은 `ArrayList`에 여러 스레드가 동시에 `add`.
- 대처: `collect`·`toList()`. 병렬 자체가 이득인지도 측정한다([languages/java/syntax/49](../../../languages/java/syntax/49-parallel-streams/2-summary.md)).

### 4. 제너레이터 재사용 → 조용히 0건

- 현상: 일일 정산 메일의 두 번째 표가 매일 비어 있다. 에러는 없다.
- 보이는 형태: `second: []`(실험 B).
- 원인: 첫 표를 만들 때 제너레이터를 다 소비했다. Python은 다시 돌려도 예외 없이 빈 반복을 한다.
- 대처: `rows = list(gen)`으로 한 번 실체화. 함수가 제너레이터를 반환하면 이름·타입 힌트(`Iterator[...]`)로 드러낸다([languages/python/syntax/17](../../../languages/python/syntax/17-generators-yield/2-summary.md)).

### 5. 지연 스트림이 자원보다 오래 산다

- 현상: 파일을 읽는 함수가 결과를 반환한 뒤, 호출자에서 `IllegalStateException: source already consumed or closed`.
- 원인: try-with-resources 안에서 `Files.lines(...)`의 **지연** 스트림만 반환했다. 소비는 파일이 닫힌 뒤 일어났다(실험 C).
- 대처: 자원 블록 안에서 최종 연산까지 끝내고 결과(`List`)를 반환한다. 스트림을 반환해야 하면 닫을 책임을 호출자에게 넘기고 문서화한다.

## 핵심 문장

- 순수 함수는 결과가 인자에만 달려 있어, 적용 순서를 바꾸거나 결과에 필요 없는 호출을 건너뛰거나 나눠도 결과가 같다.
- 불변 값은 공유해도 안전하므로, 영속 자료구조는 바뀌지 않은 부분을 공유해 복사 비용을 줄인다.
- Java 스트림의 중간 연산은 아무것도 계산하지 않고, 최종 연산이 원소를 당긴다(`map`·`filter` 같은 무상태 단계는 원소 하나씩 끝까지, `sorted` 같은 상태 보유 단계는 전체를 모은 뒤).
- 그래서 `map` 안의 부수효과는 단락·`count()` 최적화로 실행되지 않을 수 있다.
- 여기서 다룬 지연 시퀀스(Java `Stream`, Python·JS 제너레이터 객체)는 한 번만 소비된다. Java는 (JDK 21 구현에서) 예외로, Python·JS는 빈 결과로 그것을 드러낸다. 계산 결과를 메모하는 SICP 3.5.1의 스트림은 다시 순회할 수 있다.
- 병렬 파이프라인에서 공유 가변 컬렉션에 쓰면 원소가 사라진다. 리덕션(`collect`)으로 합친다.

## 관련 주제·근거

- 선행: [07-scope-closures-first-class-functions](../07-scope-closures-first-class-functions/2-summary.md)
- 후속: [16-concurrency-design-patterns](../16-concurrency-design-patterns/2-summary.md)(불변 스냅샷 + 원자 참조 교체)
- 다른 영역
  - [software-design/26-functional-core-imperative-shell](../../software-design/26-functional-core-imperative-shell/2-summary.md) · [software-design/19-immutability-and-value-objects](../../software-design/19-immutability-and-value-objects/2-summary.md)
  - [data-structure/26-persistent](../../data-structure/26-persistent/2-summary.md)
  - 언어별: [java/44 stream 생성](../../../languages/java/syntax/44-stream-creation/2-summary.md), [java/45 중간 연산](../../../languages/java/syntax/45-intermediate-operations/2-summary.md), [java/46 최종 연산](../../../languages/java/syntax/46-terminal-operations/2-summary.md), [java/49 parallel](../../../languages/java/syntax/49-parallel-streams/2-summary.md), [python/15 generator expressions](../../../languages/python/syntax/15-generator-expressions-lazy-eval/2-summary.md), [js/20 generators](../../../languages/js/syntax/20-generators/2-summary.md), [rust/36 iterator laziness](../../../languages/rust/syntax/36-iterator-adapters-laziness-and-collect/2-summary.md)
- 명세·문서
  - Java SE 21 API `java.util.stream.Stream`(재사용 금지, `count` API Note) — <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/Stream.html>
  - Java SE 21 API `java.util.stream` 패키지 요약(Laziness-seeking, Side-effects) — <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/package-summary.html>
  - Abelson·Sussman 『SICP』 1.3 Higher-Order Procedures · 3.1.3 The Costs of Introducing Assignment · 3.5 Streams — <https://mitp-content-server.mit.edu/books/content/sectbyfn/books_pres_0/6515/sicp.zip/full-text/book/book.html>
- 실험 목록(모두 `scratchpad/lang/05/e18/`, 2026-10-07, 컨테이너는 `--rm --network none --cpus=2`)
  - A `Lazy.java`·`once.py`: 지연·세로 처리·단락 — `eclipse-temurin:21-jdk` 21.0.12, 호스트 CPython 3.12.3
  - B `Lazy.java`·`once.py`·`once.js`: 두 번째 소비 — 위 + `node:22-alpine` v22.23.2
  - C `Lazy.java`·`Closed.java`: `count()` 건너뛰기, 병렬 공유 `ArrayList` 3회, `collect`, 닫힌 자원 — `eclipse-temurin:21-jdk`
  - §1 `Lazy.java`의 `Cons`: 영속 리스트 꼬리 공유
