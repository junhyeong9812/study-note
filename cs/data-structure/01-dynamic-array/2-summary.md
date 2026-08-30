# data-structure/01-dynamic-array — 정리

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.

## 전체 흐름

<!-- 동적 배열이 "늘어나는 것처럼" 보이는 원리를 자기 말로.
     고정 길이 배열 -> 내부 배열 + size/capacity 분리 -> 확장/축소 -> 연속 저장의 대가 순으로. -->

## 구현 — DynamicArray (`src/main/java/com/datastructure/dynamicarray/DynamicArray.java`)

<!-- 메서드마다 내 언어로. 복잡도는 "왜 그런지"까지. -->

### `필드`

- `private static final int DEFAULT_CAPACITY = 4` — 역할:
- `private Object[] elements` — 역할:
- `private int size` — 역할:
- size 와 capacity(`elements.length`)가 다른 이유:

### `DynamicArray()`, `DynamicArray(int initialCapacity)`

- 하는 일:
- 논리:
- 비용(왜):

### `size()`, `isEmpty()`, `capacity()`

- 하는 일:
- 논리:
- 비용(왜):

### `get(int index)`

- 하는 일:
- 논리:
- 비용(왜):

### `set(int index, E element)`

- 하는 일:
- 논리:
- 비용(왜):

### `add(E element)`

- 하는 일:
- 논리:
- 비용(왜):

### `add(int index, E element)`

- 하는 일:
- 논리:
- 비용(왜):

### `remove(int index)`

- 하는 일:
- 논리:
- 비용(왜):

### `remove(Object o)`

- 하는 일:
- 논리:
- 비용(왜):

### `indexOf(Object o)`, `contains(Object o)`

- 하는 일:
- 논리:
- 비용(왜):

### `clear()`

- 하는 일:
- 논리:
- 비용(왜):

### `toArray()`

- 하는 일:
- 논리:
- 비용(왜):

### `toString()`

- 하는 일:
- 논리:
- 비용(왜):

### `private void ensureCapacity(int minCapacity)` — 용량 확장

- 하는 일:
- 논리:
- 비용(왜):

### `private void maybeShrink()` — 용량 축소

- 하는 일:
- 논리:
- 비용(왜):

### `private void checkIndex(int)`, `private void checkPositionIndex(int)`

- 하는 일:
- 논리:
- 비용(왜):

## 문제 — ArrayProblems (`src/main/java/com/datastructure/dynamicarray/ArrayProblems.java`)

> 공통 계약: 정렬을 다루는 문제(1, 3, 5)의 입력에는 null 이 들어오지 않는다고 가정한다.
> DynamicArray 자체는 null 을 담을 수 있지만, "오름차순"이라는 조건이 null 의 순서를 정의하지 않는다.

### 문제 1. 정렬된 배열에서 중복 제거 (제자리)

> 문제 설명: 오름차순으로 정렬된 배열이 주어진다. 중복을 없애고 남은 개수를 반환한다.
> 새 배열을 만들지 말고 주어진 배열을 직접 줄여야 한다.
>
> `[1, 1, 2, 2, 2, 3]  ->  [1, 2, 3],  반환 3`
>
> 생각할 것
> - 정렬되어 있다는 조건을 어디에 쓸 수 있는가?
> - 한 번의 순회로 끝낼 수 있는가?

#### 접근 1: 뒤에서부터 remove

- 논리:
- 비용(왜):

#### 접근 2: 두 포인터(read/write)로 덮어쓰고 꼬리만 자르기

- 논리:
- 비용(왜):
- 두 접근의 차이:

### 문제 2. k 칸 오른쪽으로 회전

> 문제 설명: `[1, 2, 3, 4, 5], k=2  ->  [4, 5, 1, 2, 3]`
>
> 생각할 것
> - k 가 size 보다 클 수 있다. k 가 음수일 수도 있다.
> - 임시 배열을 하나 써서 옮겨도 되고, 세 번 뒤집는 방법도 있다.
>   (전체 뒤집기 -> 앞 k 개 뒤집기 -> 나머지 뒤집기)

- 내 접근:
- 논리:
- 비용(왜):

### 문제 3. 정렬을 유지하며 삽입

> 문제 설명: 오름차순 배열에 값을 넣되 정렬이 깨지지 않게 한다. 삽입된 위치를 반환한다.
> 같은 값이 이미 있으면 그 뒤에 넣는다.
>
> `[1, 3, 5], 4  ->  [1, 3, 4, 5],  반환 2`
>
> 생각할 것
> - 위치를 찾는 데 이진 탐색을 쓰면 O(log n) 이다.
>   그런데 삽입 자체가 O(n) 시프트다. 전체 복잡도는 결국 무엇인가?

- 내 접근:
- 논리:
- 비용(왜):

### 문제 4. 조건에 맞는 원소를 모두 제거 (이 문제집의 핵심)

> 문제 설명: predicate 가 true 인 원소를 전부 없애고, 제거한 개수를 반환한다.
>
> 함정
> - 가장 먼저 떠오르는 방법은 훑으면서 remove(i) 를 부르는 것이다. 정답은 나온다.
>   그런데 remove 한 번의 비용이 얼마인가? 그걸 n 번 부르면 총 비용은?
>   테스트에 100만 개짜리 케이스가 있고 시간 제한이 걸려 있다.
> - O(n) 이어야 한다.

- 내 접근:
- 논리:
- 비용(왜):

### 문제 5. 정렬된 두 배열 병합

> 문제 설명: 오름차순 배열 둘을 합쳐 오름차순 새 배열로 만든다. 원본은 건드리지 않는다.
>
> `[1, 3, 5] + [2, 3, 6]  ->  [1, 2, 3, 3, 5, 6]`
>
> 생각할 것
> - 합쳐서 정렬하면 O((n+m) log(n+m)) 이다. 이미 정렬되어 있다는 조건을 쓰면 O(n+m) 으로 된다.
> - 결과 배열의 최종 크기를 미리 알 수 있다. 그러면 확장이 몇 번 일어나는가?

- 내 접근:
- 논리:
- 비용(왜):

## 핵심 문장

<!-- 지도 수준의 문장들 — 세부가 아니라 "왜 이 구조인가"를 담은 문장 -->

-
-
-

## 관련 자료

<!-- 원본 문서·코드 경로. 기준 소스는 문서가 아니라 코드/원전이다. -->

- 챕터 안내: `/home/jun/project/myway/data-structure/01-dynamic-array/README.md`
- 내 구현: `/home/jun/project/myway/data-structure/01-dynamic-array/src/main/java/com/datastructure/dynamicarray/DynamicArray.java`
- 내 문제 풀이: `/home/jun/project/myway/data-structure/01-dynamic-array/src/main/java/com/datastructure/dynamicarray/ArrayProblems.java`
- 계약(테스트): `.../src/test/java/com/datastructure/dynamicarray/DynamicArrayTest.java`, `DynamicArrayRemovalTest.java`, `ArrayProblemsTest.java`, `TestSupport.java`
- 정답 기준 소스: `/home/jun/project/myway/data-structure/01-dynamic-array/impl/DynamicArray.java`, `impl/ArrayProblems.java`
- 다음 챕터로의 다리: `02-linked-list` (같은 인터페이스를 연속 저장이 아닌 방식으로)
