# python/python-data-structures/07 — bisect (이진 탐색 모듈) — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 중복 값이 있는 리스트에서 두 경계 함수 (예측)

```python
# 질문용 발췌
import bisect
sorted_list = [1, 3, 3, 3, 5, 7, 9]
print(f"bisect_left(3):  {bisect.bisect_left(sorted_list, 3)}")
print(f"bisect_right(3): {bisect.bisect_right(sorted_list, 3)}")
print(f"bisect_left(4):  {bisect.bisect_left(sorted_list, 4)}")
print(f"bisect_right(4): {bisect.bisect_right(sorted_list, 4)}")
```

- 네 줄에 각각 어떤 수가 찍히나?
- 4 에 대해서는 두 함수의 결과를 견주면 어떤 관계인가?

### 2. `insort` 뒤에 `insort_left` (예측)

```python
# 질문용 발췌
import bisect
data = [1, 3, 5, 7, 9]
print("삽입 전:", data)
bisect.insort(data, 4)
print("insort(4):", data)
bisect.insort_left(data, 4)
print("insort_left(4):", data)
```

- 세 줄에 찍히는 리스트는 각각 무엇인가?
- 마지막 리스트만 보고 두 4 가운데 어느 쪽이 나중에 들어간 것인지 가릴 수 있나?

### 3. 분기점과 같은 점수의 등급 (예측)

```python
# 질문용 발췌
import bisect
def grade(score, breakpoints=None, grades=None):
    if breakpoints is None:
        breakpoints = [60, 70, 80, 90]
    if grades is None:
        grades = 'FDCBA'
    i = bisect.bisect(breakpoints, score)
    return grades[i]

scores = [33, 99, 77, 70, 89, 90, 100]
for score in scores:
    print(f"  {score}점 -> {grade(score)}")
```

- 70점 · 89점 · 90점 줄에는 각각 어떤 등급이 찍히나?

### 4. 리스트에 없는 값의 개수를 세면 (예측)

- `[1, 2, 2, 2, 3, 4, 4, 5]` 에서 `count_value(data, 6)` 은 두 경계를 각각 얼마로 잡고 무엇을 돌려주나?

### 5. 검색 함수가 위치를 찾은 뒤에도 두 조건을 확인하는 까닭 (왜)

- `binary_search` 는 `bisect_left` 의 결과를 왜 그대로 돌려주지 않고 `i < len(...)` 과 `sorted_list[i] == target` 을 확인하나?

### 6. 등급 함수가 `bisect_right` 쪽을 쓰는 까닭 (왜)

- `grade` 에서 `bisect` 대신 `bisect_left` 를 쓰면 어떤 점수들의 등급이 달라지고, 왜 원래 쪽이 맞나?

### 7. `insort` 를 아주 자주 부를 때 (경계)

- 탐색이 O(log n) 인데도 `insort` 를 많이 부르면 왜 느려지고, 원본 팁은 이때 무엇을 권하나?

### 8. 정렬되지 않은 리스트에 `bisect_left` 를 부르면 (경계)

- 이때 오류가 나나, 아니면 무엇이 문제인가?

### 9. C++ 의 두 함수와의 대응 (연결)

- C++ 의 `lower_bound` 와 `upper_bound` 는 `bisect` 모듈의 어느 함수에 각각 해당하나?

### 10. `SortedList` 의 `in` 과 보통 리스트의 `in` (연결)

- `5 in sl` 이 이진 탐색으로 답하게 되는 고리는 무엇이고, 보통 리스트의 `in` 과 무엇이 다른가?

## 실습

### 실습 1. `bisect` 로 검색 · 개수 · 등급 · 정렬 컨테이너 만들기

**만들 것** — `bisect` 모듈의 경계 함수와 `insort` 를 써 보고, 그것을 바탕으로 검색 함수 · 개수 함수 · 등급 함수 · 정렬을 유지하는 클래스를 만든다.

**요구 조건**

1단계 — 경계 함수
1. `[1, 3, 3, 3, 5, 7, 9]` 에서 3 과 4 에 대한 `bisect_left` · `bisect_right` 결과, 그리고 3 에 대한 `bisect` 결과를 출력한다.

2단계 — 정렬 삽입
2. `[1, 3, 5, 7, 9]` 에 `insort` 로 4 를 넣고 리스트를 출력한다.
3. 이어서 `insort_left` 로 4 를 한 번 더 넣고 리스트를 출력한다.

3단계 — 값 검색
4. `binary_search(sorted_list, target)` 은 `bisect_left` 로 자리를 찾는다.
5. 그 자리가 리스트 길이보다 작고 그 자리의 값이 `target` 과 같으면 인덱스를, 아니면 `-1` 을 돌려준다.
6. `[2, 5, 8, 12, 16, 23, 38, 56, 72, 91]` 에서 23 과 25 를 찾아 출력한다.

4단계 — 개수 세기
7. `count_value(sorted_list, target)` 은 `bisect_right` 결과에서 `bisect_left` 결과를 뺀 값을 돌려준다.
8. `[1, 2, 2, 2, 3, 4, 4, 5]` 에서 2 · 4 · 6 의 개수를 출력한다.

5단계 — 성적 등급
9. `grade(score, breakpoints=None, grades=None)` 은 인자가 없으면 분기점 `[60, 70, 80, 90]` 과 등급 `'FDCBA'` 를 쓴다.
10. `bisect` 로 분기점에서의 자리를 찾고 그 자리의 등급 문자를 돌려준다.
11. `[33, 99, 77, 70, 89, 90, 100]` 의 각 점수를 `  {점수}점 -> {등급}` 꼴로 출력한다.

6단계 — 정렬을 유지하는 클래스
12. `SortedList` 는 빈 리스트 `data` 로 시작한다.
13. `add` 는 `insort` 로 값을 넣는다.
14. `remove` 는 `bisect_left` 로 자리를 찾고, 그 자리에 값이 실제로 있을 때만 `pop` 으로 뺀다.
15. `__contains__` 는 `bisect_left` 와 값 확인으로 `in` 연산자에 답한다.
16. `__repr__` 은 `SortedList([...])` 꼴의 글자를 돌려준다.
17. `[5, 2, 8, 1, 9, 3]` 을 차례로 `add` 하며 매번 객체를 출력하고, `5 in sl` · `6 in sl` 결과와 `remove(5)` 뒤의 객체를 출력한다.

**시작 코드**

```python
import bisect

# === 1단계: bisect_left / bisect_right ===
print("=== bisect_left / bisect_right ===")
sorted_list = [1, 3, 3, 3, 5, 7, 9]
print("리스트:", sorted_list)
# TODO: 3 · 4 에 대한 bisect_left / bisect_right 결과를 출력한다
# TODO: 3 에 대한 bisect 결과를 출력한다

# === 2단계: insort ===
print("\n=== insort ===")
data = [1, 3, 5, 7, 9]
print("삽입 전:", data)
# TODO: insort 로 4 를 넣고 data 를 출력한다
# TODO: insort_left 로 4 를 한 번 더 넣고 data 를 출력한다

# === 3단계: 값 검색 ===
print("\n=== 이진 탐색으로 값 검색 ===")
def binary_search(sorted_list, target):
    """정렬된 리스트에서 target의 인덱스 반환 (없으면 -1)"""
    # TODO: bisect_left 로 자리를 찾는다
    # TODO: 자리가 범위 안이고 값이 같으면 인덱스, 아니면 -1
    pass

nums = [2, 5, 8, 12, 16, 23, 38, 56, 72, 91]
print("리스트:", nums)
print("23 검색:", binary_search(nums, 23))
print("25 검색:", binary_search(nums, 25))

# === 4단계: 개수 세기 ===
print("\n=== 특정 값의 개수 ===")
def count_value(sorted_list, target):
    # TODO: 두 경계의 차를 돌려준다
    pass

data = [1, 2, 2, 2, 3, 4, 4, 5]
print("리스트:", data)
print("2의 개수:", count_value(data, 2))
print("4의 개수:", count_value(data, 4))
print("6의 개수:", count_value(data, 6))

# === 5단계: 성적 등급 ===
print("\n=== 성적 등급 ===")
def grade(score, breakpoints=None, grades=None):
    if breakpoints is None:
        breakpoints = [60, 70, 80, 90]
    if grades is None:
        grades = 'FDCBA'
    # TODO: 분기점에서 score 의 자리를 찾아 그 자리의 등급을 돌려준다
    pass

scores = [33, 99, 77, 70, 89, 90, 100]
for score in scores:
    print(f"  {score}점 -> {grade(score)}")

# === 6단계: 동적 정렬 리스트 ===
print("\n=== 동적 정렬 리스트 ===")
class SortedList:
    def __init__(self):
        self.data = []

    def add(self, value):
        # TODO: 정렬을 지키며 넣는다
        pass

    def remove(self, value):
        # TODO: 자리를 찾고, 값이 실제로 있을 때만 뺀다
        pass

    def __contains__(self, value):
        # TODO: 이진 탐색으로 있는지 답한다
        pass

    def __repr__(self):
        return f"SortedList({self.data})"

sl = SortedList()
for v in [5, 2, 8, 1, 9, 3]:
    sl.add(v)
    print(f"  add({v}): {sl}")
print(f"  5 in sl: {5 in sl}")
print(f"  6 in sl: {6 in sl}")
sl.remove(5)
print(f"  remove(5): {sl}")
```

**확인 방법** — 파일을 `bisect_practice.py` 처럼 `bisect.py` 가 아닌 이름으로 저장하고 `python bisect_practice.py` 로 돌린다. 1단계에서 3 의 두 경계가 서로 다르고 4 의 두 경계가 같은지, 등급에서 70점과 90점이 어느 등급으로 가는지, `SortedList` 가 매번 정렬된 채로 찍히는지를 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
