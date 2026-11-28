# python/python-data-structures/17 — 재귀 (Recursion) — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. `factorial_trace(4)` 가 찍는 줄들 (예측)

```python
# 질문용 발췌
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
```

- 찍히는 줄을 차례대로, 들여쓰기까지 적으면 어떻게 되는가?
- `-> 1` 줄은 어느 줄과 같은 들여쓰기를 쓰는가?

### 2. `hanoi(3, 'A', 'C', 'B')` 의 이동 기록 (예측)

```python
# 질문용 발췌
def hanoi(n, source, target, auxiliary):
    if n == 1:
        print(f"  원판 {n}: {source} -> {target}")
        return
    hanoi(n - 1, source, auxiliary, target)
    print(f"  원판 {n}: {source} -> {target}")
    hanoi(n - 1, auxiliary, target, source)

hanoi(3, 'A', 'C', 'B')
```

- 모두 몇 줄이 찍히는가?
- 찍히는 줄을 차례대로 적으면 어떻게 되는가?

### 3. `power(2, 10)` 이 `power` 를 부르는 횟수 (예측)

- 맨 처음 호출을 포함해 `power` 는 모두 몇 번 불리고, 각 호출의 `exp` 는 차례로 무엇인가?

### 4. 마지막 동작이 재귀 호출인 `factorial_tail` 도 깊은 `n` 에서 한도에 걸리는 까닭 (왜)

- 꼬리 재귀 꼴인데도 `factorial_tail(100000)` 이 기본 한도에서 실패하는 까닭은 무엇인가?

### 5. `flatten_iterative` 가 원소를 `reversed` 로 넣는 까닭 (왜)

- `reversed` 없이 `stack = list(nested)` 와 `stack.extend(item)` 으로 넣으면 결과의 차례는 어떻게 달라지고, 그 까닭은 무엇인가?

### 6. base case 를 `n == 1` 로 바꾼 `factorial` 에 0 을 넣으면 (경계)

- `if n == 1: return 1` 로 바꾼 `factorial(0)` 은 어떻게 끝나는가?

### 7. `sys.setrecursionlimit` 로 한도를 올리는 것의 한계 (경계)

- 한도를 `10**6` 으로 올리면 깊이 `10**6` 의 재귀가 안전해지는가?

### 8. 호출 스택과 명시적 스택 (연결)

- `flatten` 을 `flatten_iterative` 로 바꿀 때, 호출 스택이 하던 일을 무엇이 맡는가?
- 꼬리 재귀를 `while` 로 바꾸는 변환과 비교하면, 이 변환에는 왜 리스트가 따로 필요한가?

### 9. 같은 값이 섞인 두 리스트의 병합 (예측)

```python
# 질문용 발췌
left = [2, 5]          # 이 5 를 「왼쪽 5」라 부른다
right = [1, 5, 9]      # 이 5 를 「오른쪽 5」라 부른다
print(merge(left, right))
```

- 결과 리스트는 무엇이고, 두 5 중 어느 것이 먼저 들어가는가?

## 실습

### 실습 1. 재귀 기법 모음 — 기본 재귀부터 명시적 스택까지

**만들 것** — 계승 · 호출 추적 · 꼬리 재귀와 반복문 · 재귀 한도 · 머지 소트 · 빠른 거듭제곱 · 하노이 탑 · 중첩 리스트 평탄화를 한 파일에 구현하고, 각 절의 결과를 찍는다.

**요구 조건**

1. 1단계 — `factorial(n)` 은 `n <= 1` 이면 `1` 을, 아니면 `n * factorial(n - 1)` 을 돌려준다. `5!` 과 `10!` 을 찍는다.
2. 2단계 — `factorial_trace(n, depth=0)` 은 `"  " * depth` 만큼 들여 `factorial(n)` 을 찍고, base case 에서는 같은 들여쓰기로 `-> 1` 을, 아니면 `depth + 1` 로 재귀한 뒤 `-> 결과` 를 찍고 결과를 돌려준다. `factorial_trace(4)` 를 부른다.
3. 3단계 — `factorial_tail(n, acc=1)` 은 `n <= 1` 이면 `acc` 를, 아니면 `factorial_tail(n - 1, n * acc)` 를 돌려준다(꼬리 재귀).
4. 3단계 — `factorial_iterative(n)` 은 `acc = 1` 에서 시작해 `while n > 1` 동안 `acc *= n`, `n -= 1` 을 하고 `acc` 를 돌려준다. 두 함수로 `5!` 을 찍는다.
5. 4단계 — `sys.getrecursionlimit()` 로 기본 한도를 찍고, `sys.setrecursionlimit(10000)` 으로 바꾼 뒤 다시 찍는다.
6. 5단계 — `merge_sort(arr)` 는 길이 1 이하면 그대로 돌려주고, 아니면 `mid = len(arr) // 2` 로 나눠 양쪽을 재귀 정렬한 뒤 `merge` 로 합친다.
7. 5단계 — `merge(left, right)` 는 두 인덱스로 앞에서부터 비교해 `left[i] <= right[j]` 이면 왼쪽을, 아니면 오른쪽을 넣고, 끝나면 남은 원소를 이어 붙인다. 정렬 전 · 후 리스트를 찍는다.
8. 6단계 — `power(base, exp)` 는 `exp == 0` 이면 `1`, 짝수면 `power(base, exp // 2)` 를 한 번 구해 제곱, 홀수면 `base * power(base, exp - 1)` 을 돌려준다. `2^10` · `3^5` 를 찍는다.
9. 7단계 — `hanoi(n, source, target, auxiliary)` 는 `n == 1` 이면 `  원판 1: source -> target` 을 찍고 끝내고, 아니면 n-1 장을 보조로 → 원판 n 이동을 찍기 → n-1 장을 목표로 옮긴다. `hanoi(3, 'A', 'C', 'B')` 를 부른다.
10. 8단계 — `flatten(nested)` 는 원소가 리스트면 `flatten(item)` 결과를 `extend`, 아니면 `append` 해 평탄한 리스트를 돌려준다.
11. 8단계 — `flatten_iterative(nested)` 는 재귀 없이 `reversed` 로 채운 스택에서 `pop` 하며, 리스트를 만나면 그 원소를 `reversed` 로 다시 넣는다. 두 함수의 결과를 찍는다.

**시작 코드**

```python
import sys

# === 기본 재귀 ===
print("=== 기본 재귀 ===")
def factorial(n):
    """n! 계산 (재귀)"""
    pass  # TODO: base case 와 recursive case

print(f"5! = {factorial(5)}")
print(f"10! = {factorial(10)}")

# === 재귀 호출 추적 ===
print("\n=== 재귀 호출 추적 ===")
def factorial_trace(n, depth=0):
    indent = "  " * depth
    pass  # TODO: 들어갈 때 f"{indent}factorial({n})", 나올 때 f"{indent}-> {값}" 을 찍는다

factorial_trace(4)

# === 꼬리 재귀 패턴 ===
print("\n=== 꼬리 재귀 패턴 ===")
def factorial_tail(n, acc=1):
    """꼬리 재귀 형태"""
    pass  # TODO: 곱셈을 acc 에 미리 누적해 넘긴다

def factorial_iterative(n):
    """꼬리 재귀를 반복문으로"""
    pass  # TODO: while 로 바꾼다

print(f"꼬리 재귀: 5! = {factorial_tail(5)}")
print(f"반복문: 5! = {factorial_iterative(5)}")

# === 재귀 한도 ===
print("\n=== 재귀 한도 ===")
# TODO: 기본 한도를 f"기본 재귀 한도: {...}" 로 찍는다
# TODO: 한도를 10000 으로 바꾸고 f"변경 후 한도: {...}" 로 찍는다

# === 분할 정복: 머지 소트 ===
print("\n=== 분할 정복: 머지 소트 ===")
def merge_sort(arr):
    pass  # TODO: base case → 분할 → 결합

def merge(left, right):
    result = []
    i = j = 0
    # TODO: 양쪽을 비교하며 작은 것부터 넣고, 남은 원소를 이어 붙인다
    return result

arr = [38, 27, 43, 3, 9, 82, 10]
print(f"정렬 전: {arr}")
print(f"정렬 후: {merge_sort(arr)}")

# === 빠른 거듭제곱 ===
print("\n=== 빠른 거듭제곱 ===")
def power(base, exp):
    """O(log n) 거듭제곱"""
    pass  # TODO: exp == 0 / 짝수 / 홀수

print(f"2^10 = {power(2, 10)}")
print(f"3^5 = {power(3, 5)}")

# === 하노이 탑 ===
print("\n=== 하노이 탑 ===")
def hanoi(n, source, target, auxiliary):
    pass  # TODO: 이동은 f"  원판 {n}: {source} -> {target}" 꼴로 찍는다

hanoi(3, 'A', 'C', 'B')

# === 재귀 -> 반복 (스택) ===
print("\n=== 재귀 -> 반복 (스택) ===")
def flatten(nested):
    """중첩 리스트를 재귀로 평탄화"""
    result = []
    # TODO: 리스트면 재귀, 아니면 그대로 넣는다
    return result

def flatten_iterative(nested):
    """스택으로 평탄화 (재귀 없이)"""
    stack = []   # TODO: 처리 차례를 지키도록 채운다
    result = []
    # TODO: 스택이 빌 때까지 pop 하며 처리한다
    return result

nested = [1, [2, [3, 4]], [5, 6], [[7], 8]]
print(f"재귀: {flatten(nested)}")
print(f"반복: {flatten_iterative(nested)}")
```

**확인 방법** — `python recursion.py` 로 실행해, 계승 `120` · `3628800`, 추적 출력이 오른쪽으로 파고들었다가 돌아오는 꼴, 정렬 결과 `[3, 9, 10, 27, 38, 43, 82]`, `1024` · `243`, 하노이 이동 7줄, 평탄화 두 결과가 `[1, 2, 3, 4, 5, 6, 7, 8]` 로 같은지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
