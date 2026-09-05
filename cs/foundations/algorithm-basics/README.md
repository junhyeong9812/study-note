# 알고리즘 기초 (컴퓨터사이언스 부트캠프 with 파이썬 ch.14)

> 원고: computer_science repo의 따라 친 노트를 구조만 잡아 이관(2026-09-05). 내용 보강 없음 — 원문 유지, 오탈자만 교정.
> 심화판: [data-structure/](../../data-structure/) · [algorithm/](../../algorithm/) — 이 문서는 책 원고 이관본

## 목차 (파일→절 매핑)

| 원본 파일 | 절 |
|---|---|
| `chapter14/chapter14-2.py` | 1. 빅오(Big-O) · 2. 분할 상환 분석 |
| `chapter14/chapter14.py` | 3. 선형 탐색 |
| `chapter14/chapter14-1.py` | 4. 이진 탐색 |
| `chapter14/chapter14-2.py` | 5. 거품 정렬과 퀵 정렬 |

---

## 1. 빅오 (Big-O)

출처: `computer_science/chapter/chapter14/chapter14-2.py`

빅오란?
일반적으로 알고리즘 성능 분석의 기준은 실행되는 데 걸리는 초나 분 같은 절대적인 시간이 아니라
데이터 크기가 커지면 분기를 몇 번 더 실행하는지, 상대적인 연산 횟수이다.
빅오란 데이터가 증가하면 연산 횟수가 어떻게 변화하는지 이 경향을 나타내는 지표 개념이다.

- `O(1)`: 1은 상수를 의미하며 데이터가 증가해도 연산 횟수는 항상 같다. (배열 — 인덱싱을 통한 데이터 접근) → map
- `O(n)`: 증가 형태가 선형입니다. 데이터 개수가 늘면 개수에 비례하여 연산 횟수가 증가한다. (연결 리스트)
- `O(log n)`: 증가 형태가 로그 함수의 그래프를 그린다. 데이터가 증가해도 연산 횟수의 증가가 매우 낮다. (이진 탐색 트리)
- `O(n log n)`: 증가 형태가 선형·로그형의 곱으로 나타나며 선형 빅오보다는 성능이 떨어지지만 제곱 형태의 함수와 비교하면 성능이 월등하다. (퀵 정렬)
- `O(n^2)`: 증가 형태가 제곱이며 데이터 개수가 적으면 괜찮지만 데이터 개수가 많아지면 연산 횟수가 너무 늘어나서 부담스럽다. (거품 정렬)

## 2. 분할 상환 분석

출처: `computer_science/chapter/chapter14/chapter14-2.py`

알고리즘 성능이 나와 있는 자료를 보면 분할 상환 분석(amortized analysis)을 적용하여
'이 알고리즘의 복잡도는 분할 상환 상수(amortized constant time)를 가진다'
같은 표현을 볼 수 있다.

분할 상환 분석이란?
특정 상황에서 좋지 않은 성능을 내지만 나머지 상황에서는 좋은 성능을 낼 때, 모든 연산을 고려해 성능을 분석하는 것을 말한다.
특정 상황에서의 고비용을 일정 기간으로 분산시켜 성능을 평가하는 것이다.

분할 상환 상수 시간이란?
동적 배열에서 데이터를 넣는 건 O(1)이지만 배열이 다 차면 복사를 위해 O(n)이 된다. 하지만 요소를 추가할 때는 비용이 거의 안 들기 때문에 분산시키면
성능은 상수 시간과 비슷해지는데 이걸 의미한다.

## 3. 선형 탐색

출처: `computer_science/chapter/chapter14/chapter14.py`

탐색 알고리즘에는 두 가지 종류가 존재한다.

1. 선형 탐색: 대상 데이터와 저장되어 있는 데이터를 순서대로 하나씩 비교하는 방식
2. 이진 탐색: 대상 데이터와 가운데 위치한 데이터를 비교해 대상 데이터가 작으면 비교 데이터의 이전 데이터를,
   크면 비교 데이터의 이후 데이터를 같은 방식으로 반복해 비교하는 방식.

선형 탐색 알고리즘에서 다룰 데이터를 List라고 정의하자.
선형 탐색은 리스트의 처음부터 끝까지 순회하며 대상을 찾는다.

```python
def linear_search(data, target):
    for idx in range(len(data)):
        if data[idx] == target:
            return idx

    return None
```

선형 탐색 알고리즘의 성능은 if문 실행 횟수, 즉 비교 연산 횟수를 성능의 기준으로 삼는다.

- 첫 번째 요소를 찾는 경우: 최선의 경우(Best Case)
- 마지막 요소를 찾는 경우: 최악의 경우(Worst Case)

즉 데이터가 뒤에 있을수록 성능이 떨어지게 된다.
즉 기울기가 1이다.

## 4. 이진 탐색

출처: `computer_science/chapter/chapter14/chapter14-1.py`

이진 탐색 알고리즘을 요약해보면

- 리스트의 모든 데이터는 정렬된 상태여야 한다.
- 첫 번째 인덱스를 start로 설정하고 마지막 인덱스를 end로 설정한다.
- 가운데 인덱스를 mid로 설정하고 mid 데이터와 target 데이터를 비교한다.
- target 데이터와 mid 데이터가 같다면 mid를 반환한다.
- target 데이터가 작으면 end를 mid - 1로 한다.
- target 데이터가 크면 start를 mid + 1로 한다.
- 데이터를 찾거나 start와 end가 교차하기 전까지 계속 진행한다.
- 데이터를 찾지 못했다면 None을 반환한다.

이진 탐색 알고리즘을 적용하려면 반드시 데이터가 정렬된 상태여야 한다.

```python
def binary_search(data, target):
    # 리스트를 정렬 상태로 만든다.
    data.sort()
    # start는 시작 인덱스, end는 마지막 인덱스
    start = 0
    end = len(data) - 1

    # start와 end가 교차하기 전까지 반복
    while start <= end:
        # mid는 start와 end 가운데 인덱스
        mid = (start + end) // 2

        # target 데이터가 mid의 데이터와 같다면 mid를 반환
        if data[mid] == target:
            return mid
        # target 데이터가 작다면 end를 mid - 1로 지정
        elif data[mid] > target:
            end = mid - 1
        # target 데이터가 크다면 start를 mid + 1로 지정
        else:
            start = mid + 1
    # start와 end가 교차했을 때까지
    # target을 찾지 못했다면
    # target이 리스트에 존재하지 않는다.
    return None
```

### 이진 탐색 알고리즘의 성능

최선의 경우는 한 번에 찾는 것이고,
대상 데이터가 1이면 비교 횟수는 늘어 10까지의 데이터라면 3번 비교하게 된다.
이때 보면 mid 데이터와 target 데이터를 한 번 비교할 때마다 데이터의 개수는 절반으로 줄어든다.
이때 연산을 계속하다 보면 비교할 데이터가 1개이며, 마지막으로 한 번 더 비교하면 최악의 경우 비교 횟수를 구할 수 있다.
공식으로 보면 n(1/2)^k = 1 (n은 데이터 개수, 비교 횟수를 k)
이때 우리가 구하고자 하는 k는 지수이므로 로그를 적용하면 k = log2(n)이다.
이진 탐색: 매번 반으로 줄이므로

```
1) K번 반복 후 남은 크기
   n * (1/2)^K = 1

2) 정리
   n * (1/2)^K = 1
   n * 2^(-K)  = 1
   2^(-K)      = n^(-1)      ← 양변을 n으로 나눔
   2^(-K)      = 1/n

3) 양변에 log2 취하기
   log2(2^(-K)) = log2(n^(-1))
   -K           = -log2(n)    ← log2(2^x) = x 이므로

4) 양변에 -1 곱하기
   K = log2(n)

∴ 이진탐색의 시간복잡도 = O(log2(n)) = O(log n)
```

```
^
 |                                                    *  n²
 |                                                 *
 |                                              *
 |                                           *
 |                                        *
 |                                     *
 |                                  *
 |                               *
 |                            *
 |                         *
 |                      *
 |                   *              * n log n
 |                *              *
 |             *              *
 |          *              *
 |        *             *
 |      *            *          * n
 |    *           *          *
 |   *         *          *
 |  *        *         *
 | *       *        *
 | *     *       *
 |*    *      *
 |*  *     *
 |* *   *          * log n
 |**  *      ·  ·  ·  ·  ·  ·  ·  ·  ·
 |* *  · ·
 |**·
 |*
 └──────────────────────────────────────────────→ n

 정리:
 ─────────────────────────
  log n     거의 평평
  n         직선
  n log n   직선보다 살짝 휘어짐
  n²        급격히 치솟음
 ─────────────────────────
```

## 5. 거품 정렬과 퀵 정렬

출처: `computer_science/chapter/chapter14/chapter14-2.py`

그럼 거품 정렬 알고리즘을 보자.

```python
def bubble_sort(data):
    data_len = len(data)

    for i in range(data_len-1):
        for j in range(data_len-1 - i):
            if data[j] > data[j+1]:
                data[j], data[j+1] = data[j+1], data[j]
```

퀵 정렬:

```python
def quick_sort(data, start, end):
    # 탈출 조건
    if start >= end:
        return

    left = start
    right = end
    pivot = data[ (start + end) // 2 ]

    # left와 right가 교차할 때까지 반복
    while left <= right:
        # left 데이터가 pivot보다 크거나 같으면 멈춘다.
        while data[left] < pivot:
            left += 1
        # right 데이터가 pivot보다 작거나 같으면 멈춘다.
        while data[right] > pivot:
            right -= 1

        # left와 right가 교차하지 않았으면 교환
        if left <= right:
            data[left], data[right] = data[right], data[left]
            left += 1
            right -= 1

    quick_sort(data, start, right)
    quick_sort(data, left, end)
```
