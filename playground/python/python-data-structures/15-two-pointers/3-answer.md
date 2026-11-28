# python/python-data-structures/15 — 투 포인터 & 슬라이딩 윈도우 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. (0, 5) — 가장 바깥쪽 쌍을 먼저 만난다

**출력**

```text
결과: 인덱스 (0, 5) -> 1 + 11 = 12
```

**왜 그런가**
`left=0`, `right=5` 에서 시작하고 첫 비교 `1 + 11` 이 이미 12 라 바로 돌려준다.
`(1, 4)`(3 + 9) 와 `(2, 3)`(5 + 7) 도 답이지만 포인터가 거기까지 가지 않는다.
원본의 출력 주석은 `(1, 4)` 라고 적었는데 실제 출력과 다르다.
근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 2」.

### 2. 'wke', 길이 3

**출력**

```text
  'pwwkew' -> 'wke' (길이: 3)
```

**왜 그런가**
`p`, `w` 로 "pw"(길이 2)가 되고, 두 번째 `w` 에서 `seen[w]=1 ≥ left` 라 `left` 가 2 로 점프한다.
그 뒤 `k`, `e` 가 붙어 "wke"(길이 3)가 최대가 된다.
마지막 `w` 에서 `left` 가 3 으로 점프해 "kew" 도 길이 3 이지만 `>` 로만 갱신하므로 먼저 나온 "wke" 가 남는다.
근거: 2-summary 「동작 방식 (5)」.

### 3. 3개 — [1,1,1] · [1,2] · [3]

**출력**

```text
합이 3인 부분 배열 수: 3
```

**왜 그런가**
누적합은 1, 2, 3, 5, 8 이다.
누적 3 에서 3−3=0 이 있어(`{0:1}`) [1,1,1] 이 세어진다.
누적 5 에서 5−3=2 가 있어 [1,2] 가, 누적 8 에서 8−3=5 가 있어 [3] 이 세어진다.
근거: 2-summary 「동작 방식 (6)」.

### 4. 정렬돼 있어야 버린 원소가 어떤 짝과도 답이 안 된다는 것이 보장된다

합이 모자랄 때 `arr[left]` 는 남은 원소 중 가장 큰 `arr[right]` 와 짝지어도 모자란다.
정렬돼 있으면 다른 어떤 짝과도 모자라므로 후보에서 버려도 답을 잃지 않는다.
정렬이 없으면 「가장 큰 짝」이라는 전제가 깨져 답을 지나칠 수 있다.
근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 1」.

### 5. `left` 가 전체 실행 동안 배열 길이만큼만 움직이기 때문이다

`while` 이 돌 때마다 `left` 가 한 칸 오른쪽으로 가고, `left` 는 뒤로 가지 않는다.
그래서 `while` 의 반복 횟수는 `for` 한 번마다가 아니라 전체 합계로 n 을 넘지 못한다.
각 인덱스는 들어올 때와 나갈 때 최대 두 번 방문된다.
근거: 2-summary 「동작 방식 (4)」.

### 6. 「빼면 합이 줄고 더하면 는다」는 전제가 깨지기 때문이다

가변 윈도우는 합이 `target` 이상일 때만 줄이고, 그렇지 않으면 계속 넓힌다.
음수가 있으면 앞쪽 원소를 빼야 합이 커지는 경우가 있는데 그 판단을 하지 않는다.
`[2, -5, 4]`, `target=4` 에서 누적 합이 한 번도 4 이상이 되지 않아 0 을 돌려주지만 `[4]` 가 답이다(손으로 따라간 것 — 실행 아님).
음수가 섞이면 부분합 + 해시맵을 쓴다.
근거: 2-summary 「어디서 틀리나 3」.

### 7. 직전에 남긴 값과만 비교해서 떨어진 중복을 못 본다

`fast=1` 의 2 는 `arr[slow]=1` 과 달라 남고, `fast=2` 의 1 은 `arr[slow]=2` 와 달라 또 남는다.
결과는 길이 3, `[1, 2, 1]` 그대로다(손으로 따라간 것 — 실행 아님).
같은 값이 붙어 있는(정렬된) 배열이어야 한다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 4」.

### 8. 인덱스 0 부터 시작하는 구간을 세지 못한다

그런 구간의 합은 누적합 그 자체라, 찾아야 할 「앞쪽 누적합」이 빈 앞부분의 0 이다.
`{0: 1}` 이 없으면 0 이 dict 에 없어서 놓친다.
`[1, 1, 1, 2, 3]`, `target=3` 에서는 `[1, 1, 1]` 이 빠져 3 이 아니라 2 가 된다.
근거: 2-summary 「동작 방식 (6)」 · 「어디서 틀리나 5」.

### 9. 정렬 후 하나를 고정하고 양끝 투 포인터를 재사용한다

`nums.sort()` 로 양끝 투 포인터의 전제(정렬)를 만든다.
`i` 를 고정하면 남은 문제는 「`[i+1..끝]` 에서 두 수의 합 맞추기」가 되어 (1)의 기법을 그대로 쓴다.
바깥 `i` 가 n 번, 안쪽 양끝 투 포인터가 O(n) 이라 곱해서 O(n²) 이다.
중복 건너뛰기를 더해 같은 조합이 두 번 나오지 않게 한다.
근거: 2-summary 「동작 방식 (7)」 · 「동작 방식 (1)」.

## 실습 정답

### 실습 1. 투 포인터 · 슬라이딩 윈도우 · 부분합 함수 일곱 개 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1단계 양끝 비교 · 이동 · `None` | `two_sum_sorted` — `left, right = 0, len(arr) - 1`, `while left < right`, `return None` |
| 2단계 slow/fast 제자리 중복 제거 | `remove_duplicates` — `if not arr: return 0`, `for fast in range(1, len(arr))`, `return slow + 1` |
| 3단계 고정 윈도우 최대 합 | `max_sum_subarray` — `sum(arr[:k])`, `window_sum += arr[i] - arr[i - k]` |
| 4단계 가변 윈도우 최소 길이 · 없으면 0 | `min_subarray_len` — `current_sum += arr[right]`, `while current_sum >= target`, `float('inf')` 검사 |
| 5단계 마지막 위치 dict · 점프 · 튜플 | `longest_unique_substring` — `seen`, `if char in seen and seen[char] >= left`, `return result, max_len` |
| 6단계 누적합 빈도 `{0: 1}` | `subarray_sum_count` — `prefix_count = {0: 1}`, `prefix_count.get(current_sum, 0) + 1` |
| 7단계 정렬 · i 고정 · 중복 건너뛰기 | `three_sum` — `nums.sort()`, `if i > 0 and nums[i] == nums[i - 1]: continue`, 안쪽 두 `while` |
| 단계별 제목 · 결과 출력 | 각 절의 `print("=== … ===")` 와 결과 `print` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-data-structures/reference/two-pointers.py`

```python
# [자료구조 & 알고리즘] 투 포인터 & 슬라이딩 윈도우
# 설명: 투 포인터, 슬라이딩 윈도우, 부분합 기법으로 O(n) 문제 해결
# 팁: 투 포인터는 (1) 양끝에서 좁혀오는 타입(정렬 필수), (2) 같은 방향 slow/fast 타입이 있다. 슬라이딩 윈도우는 연속 부분 배열/문자열 문제의 핵심이며, 고정/가변 크기로 나뉜다. 부분합(prefix sum)과 해시맵을 결합하면 합이 k인 부분 배열 문제를 O(n)에 풀 수 있다.

# === 양끝 투 포인터: 정렬 배열에서 두 수의 합 ===
# 정렬 배열에서 합이 target이 되는 쌍 찾기. 합이 작으면 left++, 크면 right--. 시간 O(n).
print("=== 양끝 투 포인터 ===")
def two_sum_sorted(arr, target):
    # 양끝에서 시작
    left, right = 0, len(arr) - 1
    while left < right:
        s = arr[left] + arr[right]
        # 정확히 일치 -> 정답
        if s == target:
            return (left, right)
        # 합이 모자라면 왼쪽 포인터를 키워 합을 늘림
        elif s < target:
            left += 1
        # 합이 크면 오른쪽 포인터를 줄여 합을 줄임
        else:
            right -= 1
    return None

arr = [1, 3, 5, 7, 9, 11]
target = 12
result = two_sum_sorted(arr, target)
print(f"배열: {arr}, target={target}")
print(f"결과: 인덱스 {result} -> {arr[result[0]]} + {arr[result[1]]} = {target}")

# === 같은 방향 투 포인터: 중복 제거 ===
# slow는 결과 위치, fast는 탐색 위치. 다른 값을 발견할 때만 slow 진행. 시간 O(n), 공간 O(1).
print("\n=== 같은 방향 투 포인터 ===")
def remove_duplicates(arr):
    if not arr:
        return 0
    slow = 0
    # fast는 1부터 끝까지 모든 원소 검사
    for fast in range(1, len(arr)):
        # 새로운 값 만나면 slow 다음 위치에 기록
        if arr[fast] != arr[slow]:
            slow += 1
            arr[slow] = arr[fast]
    # 유효한 길이 = slow + 1
    return slow + 1

data = [1, 1, 2, 2, 3, 4, 4, 5]
print(f"원본: {data}")
new_len = remove_duplicates(data)
print(f"중복 제거: {data[:new_len]}")

# === 슬라이딩 윈도우: 고정 크기 ===
# 윈도우를 한 칸 밀 때 들어오는 원소 추가, 나가는 원소 제거. 시간 O(n).
print("\n=== 슬라이딩 윈도우 (고정 크기) ===")
def max_sum_subarray(arr, k):
    """크기 k인 연속 부분 배열의 최대 합"""
    # 초기 윈도우 합
    window_sum = sum(arr[:k])
    max_sum = window_sum
    # 한 칸씩 이동: 새 원소 추가, 떠나는 원소 빼기
    for i in range(k, len(arr)):
        window_sum += arr[i] - arr[i - k]
        max_sum = max(max_sum, window_sum)
    return max_sum

arr = [2, 1, 5, 1, 3, 2]
k = 3
print(f"배열: {arr}, k={k}")
print(f"최대 합: {max_sum_subarray(arr, k)}")  # 9 (5+1+3)

# === 슬라이딩 윈도우: 가변 크기 ===
# right로 확장하다 조건 만족 시 left로 축소. 각 인덱스 최대 2번 방문 -> O(n).
print("\n=== 슬라이딩 윈도우 (가변 크기) ===")
def min_subarray_len(target, arr):
    """합이 target 이상인 최소 길이 부분 배열"""
    left = 0
    current_sum = 0
    min_len = float('inf')
    for right in range(len(arr)):
        # 오른쪽으로 윈도우 확장
        current_sum += arr[right]
        # 조건 만족 시 왼쪽을 줄이며 최솟값 갱신
        while current_sum >= target:
            min_len = min(min_len, right - left + 1)
            current_sum -= arr[left]
            left += 1
    return min_len if min_len != float('inf') else 0

arr = [2, 3, 1, 2, 4, 3]
target = 7
print(f"배열: {arr}, target={target}")
print(f"최소 길이: {min_subarray_len(target, arr)}")  # 2 ([4, 3])

# === 중복 없는 최장 부분 문자열 ===
# 마지막 등장 인덱스를 dict에 저장. 중복 발견 시 left를 jump. 시간 O(n).
print("\n=== 중복 없는 최장 부분 문자열 ===")
def longest_unique_substring(s):
    seen = {}
    left = 0
    max_len = 0
    result = ""
    for right, char in enumerate(s):
        # 윈도우 안에 같은 문자가 있으면 left를 그 다음으로 점프
        if char in seen and seen[char] >= left:
            left = seen[char] + 1
        # 마지막 위치 갱신
        seen[char] = right
        # 최장 길이 갱신
        if right - left + 1 > max_len:
            max_len = right - left + 1
            result = s[left:right + 1]
    return result, max_len

for s in ["abcabcbb", "bbbbb", "pwwkew"]:
    substr, length = longest_unique_substring(s)
    print(f"  '{s}' -> '{substr}' (길이: {length})")

# === 부분합 (Prefix Sum) ===
# 누적합 차이로 구간합 계산. 해시맵에 누적합 빈도를 저장하면 합이 target인 부분 배열 수를 O(n)에 카운트.
print("\n=== 부분합 ===")
def subarray_sum_count(arr, target):
    """합이 target인 연속 부분 배열 개수"""
    # prefix_count[s] = 지금까지 누적합이 s였던 횟수. 0은 빈 배열을 위해 1로 초기화.
    prefix_count = {0: 1}  # 빈 배열의 합 = 0
    current_sum = 0
    count = 0
    for num in arr:
        current_sum += num
        # current_sum - target이 이전에 존재하면
        # 그 지점부터 현재까지 합이 target
        if current_sum - target in prefix_count:
            count += prefix_count[current_sum - target]
        # 현재 누적합 빈도 갱신
        prefix_count[current_sum] = prefix_count.get(current_sum, 0) + 1
    return count

arr = [1, 1, 1, 2, 3]
target = 3
print(f"배열: {arr}, target={target}")
print(f"합이 {target}인 부분 배열 수: {subarray_sum_count(arr, target)}")  # 3

# === 3Sum ===
# 정렬 후 i를 고정, 나머지는 양끝 투 포인터. 중복 스킵 처리 핵심. 시간 O(n^2).
print("\n=== 3Sum ===")
def three_sum(nums):
    nums.sort()
    result = []
    for i in range(len(nums) - 2):
        # i 중복 스킵
        if i > 0 and nums[i] == nums[i - 1]:
            continue
        left, right = i + 1, len(nums) - 1
        while left < right:
            s = nums[i] + nums[left] + nums[right]
            if s == 0:
                result.append([nums[i], nums[left], nums[right]])
                # left/right 중복 스킵
                while left < right and nums[left] == nums[left + 1]:
                    left += 1
                while left < right and nums[right] == nums[right - 1]:
                    right -= 1
                # 두 포인터를 모두 한 칸 이동
                left += 1
                right -= 1
            # 합이 작으면 left를 키움
            elif s < 0:
                left += 1
            # 합이 크면 right를 줄임
            else:
                right -= 1
    return result

nums = [-1, 0, 1, 2, -1, -4]
print(f"nums: {nums}")
print(f"3Sum: {three_sum(nums)}")  # [[-1, -1, 2], [-1, 0, 1]]

# 출력:
# === 양끝 투 포인터 ===
# 결과: 인덱스 (1, 4) -> 3 + 9 = 12
# === 슬라이딩 윈도우 (고정 크기) ===
# 최대 합: 9
# === 슬라이딩 윈도우 (가변 크기) ===
# 최소 길이: 2
# === 중복 없는 최장 부분 문자열 ===
# 'abcabcbb' -> 'abc' (길이: 3)
# === 부분합 ===
# 합이 3인 부분 배열 수: 3
# === 3Sum ===
# 3Sum: [[-1, -1, 2], [-1, 0, 1]]
```

**실행 결과** — 원본 예제(`component`)를 실제로 돌린 출력이다. 환경 `Python 3.12.3` · 2026-11-28 · exit 0 · 두 번 돌려 출력이 같았다.

````text
$ python3 -I example.py
=== 양끝 투 포인터 ===
배열: [1, 3, 5, 7, 9, 11], target=12
결과: 인덱스 (0, 5) -> 1 + 11 = 12

=== 같은 방향 투 포인터 ===
원본: [1, 1, 2, 2, 3, 4, 4, 5]
중복 제거: [1, 2, 3, 4, 5]

=== 슬라이딩 윈도우 (고정 크기) ===
배열: [2, 1, 5, 1, 3, 2], k=3
최대 합: 9

=== 슬라이딩 윈도우 (가변 크기) ===
배열: [2, 3, 1, 2, 4, 3], target=7
최소 길이: 2

=== 중복 없는 최장 부분 문자열 ===
  'abcabcbb' -> 'abc' (길이: 3)
  'bbbbb' -> 'b' (길이: 1)
  'pwwkew' -> 'wke' (길이: 3)

=== 부분합 ===
배열: [1, 1, 1, 2, 3], target=3
합이 3인 부분 배열 수: 3

=== 3Sum ===
nums: [-1, 0, 1, 2, -1, -4]
3Sum: [[-1, -1, 2], [-1, 0, 1]]
````

**풀이 요점**
- 양끝 투 포인터는 정렬이 있어야 원소를 버릴 수 있고, 답이 여럿이면 가장 바깥쪽 쌍 `(0, 5)` 를 먼저 만난다.
- slow/fast 는 `fast` 가 읽고 `slow` 가 쓰며, 결과는 `arr[:slow + 1]` 이다.
- 고정 윈도우는 첫 합만 직접 구하고 그다음은 더하고 빼서 O(n)이다.
- 가변 윈도우의 안쪽 `while` 은 `left` 가 뒤로 가지 않아 전체 O(n)이고, 양수 배열을 전제로 한다.
- 최장 부분 문자열의 `seen[char] >= left` 는 윈도우 밖의 옛 기록을 무시하게 한다.
- 부분합 개수 세기는 `{0: 1}` 로 시작하고, 3Sum 은 정렬 + i 고정 + 양끝 투 포인터 + 중복 건너뛰기다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 원본 예제를 `Python 3.12.3` 에서 2회 돌렸다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
