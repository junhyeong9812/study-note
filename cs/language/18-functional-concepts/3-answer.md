# language/18-functional-concepts — 정답

## 정답

### 1. 순수 함수와 참조 투명성

- 순수 함수: 결과가 인자에만 달려 있고, 바깥에 보이는 부수효과가 없다.
- 참조 투명성: 식을 그 값으로 바꿔 써도 의미가 같다.
- 순수할 때 라이브러리가 할 수 있는 일
  1. 단계 건너뛰기(`count()`가 원본 크기로 답하기)
  2. 일부 원소만 처리(단락 — `findFirst`)
  3. 여러 스레드로 나눠 실행하고 합치기(`parallel`, `collect`)

### 2. 영속 리스트의 구조 공유

```text
  a: 10 ─┐
         ├──> 1 → 2 → 3 → nil
  b: 20 ─┘
  base ────^ (1부터)
```

- `a.tail() == b.tail()` → `true`(실험 §1 `꼬리 공유: true`). 출력: `a=10,1,2,3 b=20,1,2,3 base=1,2,3`.
- 안전 조건: 공유되는 노드를 아무도 고치지 않는다(불변). 가변이면 한 판의 수정이 다른 판에 샌다.

### 3. 세로 처리

- 출력(실험 A): `map 1` → `filter 10` → `map 2` → `filter 20` → `findFirst = 20`. 3·4·5는 `map`조차 실행되지 않았다.
- 최종 연산 `findFirst`가 원소를 하나씩 당겨 파이프라인 끝까지 보낸다(이 무상태 `map`·`filter` 파이프라인의 경우 — `sorted` 같은 상태 보유 단계가 끼면 전체 입력을 먼저 처리할 수 있다). 답이 나오면 더 당기지 않는다. 단계별로 전체를 처리(가로)하면 단락할 수 없다.

### 4. 두 번째 소비

- Java: `IllegalStateException: stream has already been operated upon or closed`(JDK 21 구현에서 관찰 — `Stream` 문서는 재사용을 금지하고 "감지하면 던질 수 있다"고만 한다).
- Python: `first : [0, 10, 20]`, `second: []`. JS: `first : [1,2]`, `second: []`. 둘 다 예외가 없다(실험 B — 둘 다 제너레이터 객체를 다시 돈 경우다. 배열 같은 이터러블은 순회마다 새 이터레이터를 받아 다시 돌 수 있다).
- 운영에서 더 위험한 쪽: Python·JS. 두 번째 집계가 0건으로 "성공"해 조용한 실패가 된다. Java는 시끄럽게 실패해 바로 드러난다.

### 5. `count()`와 `map`의 부수효과

- `filter` 없음: `count = 3, map 부수효과로 모은 것 = []` — `map`이 한 번도 실행되지 않았다.
- `filter(x -> true)` 있음: `filter 뒤 count = 3, 모은 것 = [1, 2, 3]` — 크기를 미리 몰라 파이프라인이 돌았다.
- `Stream.count` API Note: "An implementation may choose to not execute the stream pipeline … if it is capable of computing the count directly from the stream source. In such cases no source elements will be traversed and no intermediate operations will be evaluated."

### 6. 병렬 + 공유 `ArrayList`

- 원인: `ArrayList`는 스레드 안전하지 않다. 여러 스레드의 `add`가 겹쳐 원소가 사라졌다(실험 C: 59,685 / 68,777 / 71,746, 사실 점검 재실행 9라운드 57,126 ~ 81,564, 기대 100,000).
- 고침: 부수효과 대신 리덕션으로 모은다.

```java
List<Integer> safe = IntStream.range(0, 100_000).parallel().boxed().collect(Collectors.toList());   // size = 100000
```

### 7. 닫힌 자원 위의 지연 스트림

- `IllegalStateException: source already consumed or closed`(실험 C).
- `filter`는 중간 연산이라 반환 시점에 파일을 한 줄도 읽지 않았다. try-with-resources가 블록을 나가며 스트림(파일)을 닫았다. 실제 읽기는 호출자의 최종 연산 때 일어나는데, 그때는 이미 닫혀 있다.
- 블록 안에서 `toList()`까지 끝내면 정상(`eager inside try: [user_001, user_002]`).

### 8. 지연 리스트 vs Java Stream

- 같은 점: 필요할 때까지 계산을 미루고, 소비자가 당길 때 원소를 만든다.
- 다른 점: SICP의 지연 리스트는 꼬리 계산을 메모하는 **값**이라 여러 번 순회해도 된다(3.5.1). Java `Stream`은 원본에서 원소를 한 번 흘려보내는 **일회용 파이프라인**이라 계산 결과를 보관하지 않는다.
- 그래서 재사용하면 이미 소비된 원본을 다시 읽어야 하는데, 그것을 보장할 수 없다. `Stream` 문서는 "should be operated on … only once"라 하고, 감지하면 `IllegalStateException`을 던질 수 있다고 한다.
