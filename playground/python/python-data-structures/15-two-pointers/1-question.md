# python/python-data-structures/15 — 투 포인터 & 슬라이딩 윈도우 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 합이 12인 쌍을 양끝에서 찾으면 (예측)

```python
# 질문용 발췌
arr = [1, 3, 5, 7, 9, 11]
result = two_sum_sorted(arr, 12)
print(f"결과: 인덱스 {result} -> {arr[result[0]]} + {arr[result[1]]} = 12")
```

- 합이 12 인 쌍은 여럿인데, 이 함수는 어느 인덱스 쌍을 돌려주는가?

### 2. "pwwkew" 의 중복 없는 최장 부분 문자열 (예측)

```python
# 질문용 발췌
substr, length = longest_unique_substring("pwwkew")
print(f"  '{'pwwkew'}' -> '{substr}' (길이: {length})")
```

- 출력되는 부분 문자열과 길이는 무엇인가?

### 3. 합이 3인 연속 부분 배열의 수 (예측)

```python
# 질문용 발췌
print(f"합이 3인 부분 배열 수: {subarray_sum_count([1, 1, 1, 2, 3], 3)}")
```

- 출력되는 개수는 얼마인가?

### 4. 양끝 투 포인터가 정렬을 요구하는 까닭 (왜)
- 합이 작을 때 `left` 를 옮겨 `arr[left]` 를 후보에서 버려도 되는 근거는 무엇인가?

### 5. 안쪽 `while` 이 있는데도 가변 윈도우가 O(n)인 까닭 (왜)
- `for` 안에 `while` 이 들어 있는데 왜 전체가 O(n²) 가 아닌가?

### 6. 음수가 섞인 배열과 가변 윈도우 (경계)
- `min_subarray_len` 은 왜 음수가 섞인 배열에서 틀린 답을 낼 수 있는가?

### 7. 떨어져 있는 중복과 `remove_duplicates` (경계)
- `[1, 2, 1]` 처럼 같은 값이 떨어져 있으면 중복 제거가 어디서 실패하는가?

### 8. `prefix_count` 를 `{}` 로 시작하면 (경계)
- 빈 dict 로 시작하면 어떤 구간들을 세지 못하는가?

### 9. 3Sum 과 앞의 기법들 (연결)
- 3Sum 은 이 문서의 어느 기법을 어떻게 재사용하며, 시간 복잡도는 왜 O(n²) 인가?

## 실습

### 실습 1. 투 포인터 · 슬라이딩 윈도우 · 부분합 함수 일곱 개 만들기

**만들 것** — 투 포인터 · 슬라이딩 윈도우 · 부분합 기법으로 일곱 문제를 푸는 함수를 만들고, 정해진 입력으로 결과를 출력하는 스크립트를 완성한다.

**요구 조건**

1. 1단계 — `two_sum_sorted(arr, target)`: 양끝에서 출발해 `left < right` 인 동안 두 원소의 합을 비교한다. 같으면 `(left, right)` 튜플을 돌려주고, 작으면 `left` 를, 크면 `right` 를 한 칸 옮긴다. 못 찾으면 `None` 을 돌려준다.
2. 2단계 — `remove_duplicates(arr)`: 빈 리스트면 0 을 돌려준다. `slow` 는 결과 위치, `fast` 는 1부터 끝까지 읽는 위치이고, 새 값을 만나면 `slow` 를 한 칸 옮겨 그 자리에 쓴다. 유효 길이 `slow + 1` 을 돌려준다(리스트는 제자리에서 바뀐다).
3. 3단계 — `max_sum_subarray(arr, k)`: 첫 k 개의 합으로 시작해, 한 칸 밀 때마다 들어온 원소를 더하고 나간 원소를 빼며 최대 합을 돌려준다.
4. 4단계 — `min_subarray_len(target, arr)`: `right` 로 윈도우를 넓히고, 합이 `target` 이상인 동안 길이를 기록하며 `left` 로 줄인다. 조건을 만족하는 구간이 없으면 0 을 돌려준다.
5. 5단계 — `longest_unique_substring(s)`: 문자마다 마지막 위치를 dict 에 담고, 윈도우 안에서 중복이 나오면 `left` 를 그 다음으로 점프한다. `(부분 문자열, 길이)` 튜플을 돌려주고, 세 문자열 `"abcabcbb"` · `"bbbbb"` · `"pwwkew"` 에 대해 출력한다.
6. 6단계 — `subarray_sum_count(arr, target)`: 누적합 빈도 dict 를 `{0: 1}` 로 시작해, 누적합 − target 이 몇 번 나왔는지를 더해 합이 `target` 인 연속 부분 배열의 수를 돌려준다.
7. 7단계 — `three_sum(nums)`: 정렬한 뒤 `i` 를 고정하고 나머지에서 양끝 투 포인터로 합 0 을 찾는다. `i` 와 `left`/`right` 의 중복을 건너뛰어 서로 다른 세 수 조합의 리스트를 돌려준다.
8. 각 단계는 `=== … ===` 제목 줄과 입력 · 결과 줄을 출력한다(시작 코드에 이미 있다).

**시작 코드**

```python
# 투 포인터 & 슬라이딩 윈도우 연습

print("=== 양끝 투 포인터 ===")
def two_sum_sorted(arr, target):
    # TODO: 양끝에서 시작해 합을 비교하며 좁힌다
    return None

arr = [1, 3, 5, 7, 9, 11]
target = 12
result = two_sum_sorted(arr, target)
print(f"배열: {arr}, target={target}")
print(f"결과: 인덱스 {result} -> {arr[result[0]]} + {arr[result[1]]} = {target}")

print("\n=== 같은 방향 투 포인터 ===")
def remove_duplicates(arr):
    # TODO: 빈 리스트 처리, slow/fast 로 제자리 중복 제거, 유효 길이 반환
    pass

data = [1, 1, 2, 2, 3, 4, 4, 5]
print(f"원본: {data}")
new_len = remove_duplicates(data)
print(f"중복 제거: {data[:new_len]}")

print("\n=== 슬라이딩 윈도우 (고정 크기) ===")
def max_sum_subarray(arr, k):
    """크기 k인 연속 부분 배열의 최대 합"""
    # TODO: 첫 윈도우 합 → 한 칸씩 밀며 더하고 빼기
    pass

arr = [2, 1, 5, 1, 3, 2]
k = 3
print(f"배열: {arr}, k={k}")
print(f"최대 합: {max_sum_subarray(arr, k)}")

print("\n=== 슬라이딩 윈도우 (가변 크기) ===")
def min_subarray_len(target, arr):
    """합이 target 이상인 최소 길이 부분 배열"""
    # TODO: right 로 확장, 조건 만족 동안 left 로 축소, 없으면 0
    pass

arr = [2, 3, 1, 2, 4, 3]
target = 7
print(f"배열: {arr}, target={target}")
print(f"최소 길이: {min_subarray_len(target, arr)}")

print("\n=== 중복 없는 최장 부분 문자열 ===")
def longest_unique_substring(s):
    # TODO: 마지막 위치 dict, 윈도우 안 중복이면 left 점프, (문자열, 길이) 반환
    pass

for s in ["abcabcbb", "bbbbb", "pwwkew"]:
    substr, length = longest_unique_substring(s)
    print(f"  '{s}' -> '{substr}' (길이: {length})")

print("\n=== 부분합 ===")
def subarray_sum_count(arr, target):
    """합이 target인 연속 부분 배열 개수"""
    # TODO: 누적합 빈도 dict 로 개수 세기
    pass

arr = [1, 1, 1, 2, 3]
target = 3
print(f"배열: {arr}, target={target}")
print(f"합이 {target}인 부분 배열 수: {subarray_sum_count(arr, target)}")

print("\n=== 3Sum ===")
def three_sum(nums):
    # TODO: 정렬 → i 고정 → 양끝 투 포인터 → 중복 건너뛰기
    pass

nums = [-1, 0, 1, 2, -1, -4]
print(f"nums: {nums}")
print(f"3Sum: {three_sum(nums)}")
```

**확인 방법** — `python two-pointers.py` 로 돌려 일곱 단계의 결과 줄(쌍의 인덱스, 중복 제거된 리스트, 최대 합, 최소 길이, 세 문자열의 최장 부분 문자열, 부분 배열 수, 3Sum 조합)이 손으로 계산한 값과 맞는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
