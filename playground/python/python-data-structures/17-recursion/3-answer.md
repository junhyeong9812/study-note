# python/python-data-structures/17 — 재귀 (Recursion) — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 펼치며 깊어졌다가 감기며 돌아오는 여덟 줄

**출력**

```text
factorial(4)
  factorial(3)
    factorial(2)
      factorial(1)
      -> 1
    -> 2
  -> 6
-> 24
```

**왜 그런가**

- 호출마다 `depth` 가 1 늘어 들여쓰기가 두 칸씩 깊어지므로 「factorial(n)」 줄이 오른쪽으로 파고든다.
- `factorial(1)` 은 base case 라 같은 들여쓰기(`depth = 3`)로 `-> 1` 을 찍는다 — 바로 위 `factorial(1)` 줄과 들여쓰기가 같다.
- 그 뒤 안쪽 호출부터 차례로 돌아오며 각자 자기 들여쓰기로 `-> 2` · `-> 6` · `-> 24` 를 찍는다.
- 근거: 2-summary 「동작 방식 (2)」.

### 2. 7줄 — 가장 큰 원판의 이동이 가운데에 온다

**출력**

```text
  원판 1: A -> C
  원판 2: A -> B
  원판 1: C -> B
  원판 3: A -> C
  원판 1: B -> A
  원판 2: B -> C
  원판 1: A -> C
```

**왜 그런가**

- 이동 횟수는 `2^n - 1` 이므로 n=3 에서 7줄이다.
- 1단계 `hanoi(2, A, B, C)` 가 위 두 장을 B 로 옮긴다 — 처음 세 줄이다.
- 2단계에서 원판 3 을 A 에서 C 로 옮긴다 — 가운데 네 번째 줄이다.
- 3단계 `hanoi(2, B, C, A)` 가 B 의 두 장을 C 로 옮긴다 — 마지막 세 줄이다.
- 근거: 2-summary 「동작 방식 (7)」.

### 3. 6번 — `exp` 가 10 → 5 → 4 → 2 → 1 → 0

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

`power(2, 10)` → `power(2, 5)` → `power(2, 4)` → `power(2, 2)` → `power(2, 1)` → `power(2, 0)` 으로 모두 6번 불린다.
돌아오며 `1 → 2 → 4 → 16 → 32 → 1024` 가 된다.

**왜 그런가**

- 10 은 짝수라 `exp // 2 = 5` 로 한 번만 부른다.
- 5 는 홀수라 `exp - 1 = 4` 로 부른다.
- 4 → 2 는 짝수 단계, 2 → 1 도 짝수 단계, 1 → 0 은 홀수 단계다.
- 0 에서 base case 로 `1` 을 돌려주고, 짝수 단계는 제곱, 홀수 단계는 `2` 를 곱한다.
- 근거: 2-summary 「동작 방식 (6)」.

### 4. Python 은 꼬리 호출을 최적화하지 않아 프레임이 그대로 쌓인다

Python(CPython)은 TCO 를 하지 않는다.
그래서 `factorial_tail` 도 호출마다 프레임을 하나씩 쌓고, 깊이 100000 은 기본 한도(1000)를 넘어 `RecursionError` 가 난다.
꼬리 재귀는 Python 에서 「`while` 로 기계적으로 옮기기 쉬운 모양」일 뿐이고, 깊은 계산은 `factorial_iterative` 처럼 반복문으로 바꿔야 한다.
근거: 2-summary 「동작 방식 (3)」 · 「동작 방식 (4)」 · 「어디서 틀리나 2」.

### 5. `pop()` 이 맨 끝을 꺼내므로, 거꾸로 넣어야 원래 차례로 나온다

`reversed` 없이 넣으면 마지막 원소가 먼저 꺼내져 각 단계의 차례가 뒤집힌다.
`[1, [2, [3, 4]], [5, 6], [[7], 8]]` 라면 원소가 뒤에서부터 처리돼 `[8, 7, 6, 5, 4, 3, 2, 1]` 처럼 거꾸로 된 결과가 나온다(원본에 근거 없음 — 추론).
`stack.pop()` 은 마지막에 넣은 것을 먼저 꺼내는 스택이므로, 앞의 원소를 먼저 처리하려면 앞의 원소가 맨 끝에 오도록 거꾸로 넣어야 한다.
안쪽 리스트를 펼칠 때도 같은 까닭으로 `reversed(item)` 을 쓴다.
근거: 2-summary 「동작 방식 (8)」.

### 6. 1 에 닿지 못하고 내려가다 `RecursionError` 로 멈춘다

`factorial(0)` 은 `n == 1` 이 아니므로 `0 * factorial(-1)` 을 부르고, 인자는 `-1, -2, -3 …` 으로 1 에서 멀어지기만 한다.
base case 에 영영 닿지 못하므로 깊이가 재귀 한도를 넘는 순간 `RecursionError` 가 난다.
원본의 `n <= 1` 은 0 과 음수도 base case 로 받아 이 문제가 없다.
근거: 2-summary 「어디서 틀리나 1」 · 「동작 방식 (4)」.

### 7. 안전해지지 않는다 — 한도는 숫자일 뿐 실제 스택은 늘지 않는다

`sys.setrecursionlimit` 는 허용 깊이라는 숫자만 바꾸고, 실제 스택 크기는 운영체제가 정한다.
깊이 `10**6` 이면 실제 스택이 먼저 바닥나 `RecursionError` 대신 스택 오버플로로 프로세스가 죽을 수 있다.
원본은 깊이가 10^5 이상이면 한도를 올리지 말고 반복문을 쓰라고 권한다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 3」.

### 8. 명시적 스택(리스트)이 「나중에 처리할 일」을 기억한다

- 재귀판 `flatten` 은 안쪽 리스트를 만나면 지금 반복을 멈추고 깊이 들어가며, 남은 원소는 호출 스택의 프레임이 기억한다.
- 반복판은 그 「남은 원소」를 리스트 `stack` 에 직접 넣어 두고 `pop()` 으로 하나씩 꺼낸다.
- 꼬리 재귀는 돌아온 뒤 할 일이 없어서 상태가 인자 `(n, acc)` 하나로 충분하므로 변수 몇 개로 `while` 이 된다.
- `flatten` 은 안쪽을 처리한 뒤에도 바깥 리스트의 남은 원소를 처리해야 하므로, 기억할 일이 여러 개 쌓인다 — 그래서 리스트로 된 스택이 필요하다.
- 근거: 2-summary 「동작 방식 (3)」 · 「동작 방식 (8)」 · 「핵심 문장 5」.

### 9. `[1, 2, 5, 5, 9]` — 왼쪽 5 가 먼저 들어간다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

결과는 `[1, 2, 5, 5, 9]` 이고, 앞의 5 가 왼쪽 5 다.

**왜 그런가**

- `2 <= 1` 이 거짓이라 오른쪽 `1` 이 먼저 들어간다.
- `2 <= 5` 가 참이라 왼쪽 `2` 가 들어간다.
- `5 <= 5` 가 참이라 **왼쪽 5** 가 들어가고, 왼쪽이 끝나 `while` 이 멈춘다.
- 남은 `right[1:]` 인 `[5, 9]` 가 이어 붙어, 오른쪽 5 는 그 뒤에 온다.
- 비교가 `<=` 라서 같은 값이면 왼쪽 것이 먼저 나온다.
- 근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 6」.

## 실습 정답

### 실습 1. 재귀 기법 모음 — 기본 재귀부터 명시적 스택까지

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 계승 재귀 · `5!` · `10!` 출력 | `factorial` 의 `if n <= 1: return 1` / `return n * factorial(n - 1)` |
| 2. 호출 추적 | `factorial_trace` 의 `indent = "  " * depth`, `factorial_trace(n - 1, depth + 1)` |
| 3. 꼬리 재귀 | `factorial_tail` 의 `return factorial_tail(n - 1, n * acc)` |
| 4. 반복문 변환 | `factorial_iterative` 의 `while n > 1: acc *= n; n -= 1` |
| 5. 재귀 한도 읽기 · 바꾸기 | `sys.getrecursionlimit()` · `sys.setrecursionlimit(10000)` |
| 6. 머지 소트 분할 · 결합 | `merge_sort` 의 `mid = len(arr) // 2`, `merge(left, right)` |
| 7. 병합 | `merge` 의 `while i < len(left) and j < len(right)`, `left[i] <= right[j]`, `result.extend(left[i:])` |
| 8. 빠른 거듭제곱 | `power` 의 `half = power(base, exp // 2)` / `base * power(base, exp - 1)` |
| 9. 하노이 탑 | `hanoi` 의 세 단계 — `hanoi(n - 1, source, auxiliary, target)`, `print(...)`, `hanoi(n - 1, auxiliary, target, source)` |
| 10. 재귀 평탄화 | `flatten` 의 `isinstance(item, list)` → `result.extend(flatten(item))` |
| 11. 스택 평탄화 | `flatten_iterative` 의 `stack = list(reversed(nested))`, `stack.pop()`, `stack.extend(reversed(item))` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-data-structures/reference/recursion.py`

```python
# [자료구조 & 알고리즘] 재귀 (Recursion)
# 설명: 재귀 함수, 꼬리 재귀, 분할 정복, sys.setrecursionlimit 활용
# 팁: 모든 재귀에는 base case가 반드시 필요하다. Python은 꼬리 재귀 최적화(TCO)를 지원하지 않으므로, 깊은 재귀는 반복문이나 스택으로 변환해야 한다. sys.setrecursionlimit으로 한도를 올릴 수 있지만, 스택 오버플로 위험이 있어 10^5 이상이면 반복문을 사용한다.

# sys: 재귀 한도 조회/변경
import sys

# === 기본 재귀 ===
# factorial: n! = n * (n-1)!. 시간/공간 모두 O(n) (호출 스택 때문).
print("=== 기본 재귀 ===")
def factorial(n):
    """n! 계산 (재귀)"""
    # base case: 더 이상 재귀하지 않는 종료 조건
    if n <= 1:        # base case
        return 1
    # recursive case: 자기 자신을 더 작은 인자로 호출
    return n * factorial(n - 1)  # recursive case

print(f"5! = {factorial(5)}")    # 120
print(f"10! = {factorial(10)}")  # 3628800

# === 재귀 호출 추적 ===
# 들여쓰기로 호출 깊이를 시각화. 재귀의 펼침-감김 흐름을 이해하는 데 유용.
print("\n=== 재귀 호출 추적 ===")
def factorial_trace(n, depth=0):
    indent = "  " * depth
    print(f"{indent}factorial({n})")
    if n <= 1:
        print(f"{indent}-> 1")
        return 1
    result = n * factorial_trace(n - 1, depth + 1)
    print(f"{indent}-> {result}")
    return result

factorial_trace(4)

# === 꼬리 재귀 (Python은 최적화하지 않지만 패턴 이해용) ===
# 꼬리 재귀: 마지막 동작이 재귀 호출인 형태. 누적값(acc)을 인자로 전달.
print("\n=== 꼬리 재귀 패턴 ===")
def factorial_tail(n, acc=1):
    """꼬리 재귀 형태 (Python은 TCO 미지원)"""
    if n <= 1:
        return acc
    # 곱셈을 미리 누적해 acc로 전달 -> 호출 후 추가 연산 없음
    return factorial_tail(n - 1, n * acc)

# 꼬리 재귀는 항상 반복문으로 기계적 변환 가능
def factorial_iterative(n):
    """꼬리 재귀는 반복문으로 변환 가능"""
    acc = 1
    while n > 1:
        acc *= n
        n -= 1
    return acc

print(f"꼬리 재귀: 5! = {factorial_tail(5)}")
print(f"반복문: 5! = {factorial_iterative(5)}")

# === sys.setrecursionlimit ===
# Python 기본 재귀 한도는 약 1000. 깊은 재귀가 필요하면 늘릴 수 있지만 실제 스택 크기 제약은 OS에 의존.
print("\n=== 재귀 한도 ===")
print(f"기본 재귀 한도: {sys.getrecursionlimit()}")  # 보통 1000

# 깊은 재귀가 필요할 때
sys.setrecursionlimit(10000)
print(f"변경 후 한도: {sys.getrecursionlimit()}")

# === 분할 정복: 머지 소트 ===
# 분할 정복: 분할(divide) -> 정복(conquer) -> 결합(combine). 머지 소트는 O(n log n).
print("\n=== 분할 정복: 머지 소트 ===")
def merge_sort(arr):
    # base case: 길이 1 이하면 이미 정렬됨
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    # 좌/우 절반을 각각 재귀 정렬 (분할)
    left = merge_sort(arr[:mid])    # 분할
    right = merge_sort(arr[mid:])   # 분할
    # 두 정렬된 절반을 병합 (결합)
    return merge(left, right)        # 정복 (병합)

# 정렬된 두 리스트를 하나의 정렬된 리스트로 병합. O(n).
def merge(left, right):
    result = []
    i = j = 0
    # 양쪽을 동시에 비교하며 작은 것부터 결과에 추가
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    # 남은 원소 이어붙이기
    result.extend(left[i:])
    result.extend(right[j:])
    return result

arr = [38, 27, 43, 3, 9, 82, 10]
print(f"정렬 전: {arr}")
print(f"정렬 후: {merge_sort(arr)}")

# === 분할 정복: 거듭제곱 ===
# 빠른 거듭제곱: O(log n). 지수의 절반씩 줄여가며 곱셈.
print("\n=== 빠른 거듭제곱 ===")
def power(base, exp):
    """O(log n) 거듭제곱"""
    if exp == 0:
        return 1
    # 짝수 지수: half * half
    if exp % 2 == 0:
        half = power(base, exp // 2)
        return half * half
    # 홀수 지수: base를 한 번 빼서 짝수 케이스로 환원
    else:
        return base * power(base, exp - 1)

print(f"2^10 = {power(2, 10)}")   # 1024
print(f"3^5 = {power(3, 5)}")     # 243

# === 하노이 탑 ===
# 고전 재귀 문제. n=k에서 k+1로 일반화. 이동 횟수 2^n - 1.
print("\n=== 하노이 탑 ===")
def hanoi(n, source, target, auxiliary):
    # base case: 한 장이면 바로 이동
    if n == 1:
        print(f"  원판 {n}: {source} -> {target}")
        return
    # 1) 위 n-1개를 보조 막대로 옮기고
    hanoi(n - 1, source, auxiliary, target)
    # 2) 가장 큰 원판을 목표 막대로 옮긴 뒤
    print(f"  원판 {n}: {source} -> {target}")
    # 3) 보조 막대의 n-1개를 목표 막대로 옮긴다
    hanoi(n - 1, auxiliary, target, source)

hanoi(3, 'A', 'C', 'B')

# === 재귀 -> 반복 변환 (스택 사용) ===
# 깊이 큰 데이터에서 재귀는 스택 오버플로 위험 -> 명시적 스택으로 같은 로직 구현.
print("\n=== 재귀 -> 반복 (스택) ===")
def flatten(nested):
    """중첩 리스트를 재귀로 평탄화"""
    result = []
    for item in nested:
        if isinstance(item, list):
            # 리스트면 재귀적으로 평탄화 후 합침
            result.extend(flatten(item))
        else:
            result.append(item)
    return result

def flatten_iterative(nested):
    """스택으로 평탄화 (재귀 없이)"""
    # 처리 순서를 유지하기 위해 reversed로 push
    stack = list(reversed(nested))
    result = []
    while stack:
        item = stack.pop()
        if isinstance(item, list):
            # 내부 리스트의 원소를 다시 스택에 reversed로 push
            stack.extend(reversed(item))
        else:
            result.append(item)
    return result

nested = [1, [2, [3, 4]], [5, 6], [[7], 8]]
print(f"재귀: {flatten(nested)}")
print(f"반복: {flatten_iterative(nested)}")

# 출력:
# === 기본 재귀 ===
# 5! = 120
# === 재귀 호출 추적 ===
# factorial(4)
#   factorial(3)
#     factorial(2)
#       factorial(1)
#       -> 1
#     -> 2
#   -> 6
# -> 24
# === 분할 정복: 머지 소트 ===
# 정렬 후: [3, 9, 10, 27, 38, 43, 82]
# === 하노이 탑 ===
# 원판 1: A -> C ... (7 moves)
```

**실행 결과** — 원본 예제(`component`)를 실제로 돌린 출력이다. 환경 `Python 3.12.3` · 2026-11-28 · exit 0 · 두 번 돌려 출력이 같았다.

````text
$ python3 -I example.py
=== 기본 재귀 ===
5! = 120
10! = 3628800

=== 재귀 호출 추적 ===
factorial(4)
  factorial(3)
    factorial(2)
      factorial(1)
      -> 1
    -> 2
  -> 6
-> 24

=== 꼬리 재귀 패턴 ===
꼬리 재귀: 5! = 120
반복문: 5! = 120

=== 재귀 한도 ===
기본 재귀 한도: 1000
변경 후 한도: 10000

=== 분할 정복: 머지 소트 ===
정렬 전: [38, 27, 43, 3, 9, 82, 10]
정렬 후: [3, 9, 10, 27, 38, 43, 82]

=== 빠른 거듭제곱 ===
2^10 = 1024
3^5 = 243

=== 하노이 탑 ===
  원판 1: A -> C
  원판 2: A -> B
  원판 1: C -> B
  원판 3: A -> C
  원판 1: B -> A
  원판 2: B -> C
  원판 1: A -> C

=== 재귀 -> 반복 (스택) ===
재귀: [1, 2, 3, 4, 5, 6, 7, 8]
반복: [1, 2, 3, 4, 5, 6, 7, 8]
````

**풀이 요점**

- 모든 함수가 맨 위에 base case 를 두고, 인자가 base case 쪽으로 줄어든다(`n - 1` · `exp // 2` · `arr[:mid]` · 안쪽 리스트).
- `factorial_tail` 과 `factorial_iterative` 는 같은 `(n, acc)` 상태를 쓰므로 한 줄씩 대응한다.
- `power` 는 짝수 단계에서 절반을 **한 번만** 불러 `half * half` 로 재사용해야 O(log n) 이 된다.
- `hanoi` 는 1단계와 3단계에서 목표 · 보조 막대의 자리를 바꿔 넘기는 것이 핵심이다.
- `flatten_iterative` 는 `pop()` 이 맨 끝을 꺼내므로 `reversed` 로 넣어야 재귀판과 같은 차례가 나온다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 원본 예제를 `Python 3.12.3` 에서 2회 돌렸다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
