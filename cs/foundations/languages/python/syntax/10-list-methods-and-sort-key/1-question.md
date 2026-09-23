# python/syntax/10-list-methods-and-sort-key — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> ★ 이 주제에서는 **「무엇을 돌려주나」가 답인 자리가 많다.** 값인지 `None` 인지까지 적는다.
> 실행 환경: `python3` 3.12.3.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. 각 호출이 무엇을 돌려주나 (예측)

```python
x = [3, 1, 2]
for call in ("x.sort()", "x.append(9)", "x.extend([8])", "x.insert(0, 7)",
             "x.remove(7)", "x.reverse()", "x.clear()"):
    print(f"{call:15} ->", repr(eval(call)))
y = [3, 1, 2]
print(f"{'y.pop()':15} ->", repr(y.pop()), "| y =", y)
print(f"{'sorted(y)':15} ->", repr(sorted(y)), "| y =", y)

words = ["pear", "fig", "apple"]
res = words.sort()
print("res =", repr(res), "| words =", words)
try:
    res[0]
except TypeError as e:
    print("res[0] ->", type(e).__name__, e)
```

- 마지막 세 줄에서 **에러가 나는 줄은 어디이고**, 그보다 앞줄에서는 왜 안 나는가?

### 2. 함수가 몇 번 불리나 (예측)

```python
def count_key(data, label):
    calls = []
    def k(x):
        calls.append(x)
        return x
    sorted(data, key=k)
    print(f"{label:16} n={len(data):3}  호출 {len(calls):3}회")

count_key([3, 1, 2], "무작위 3개")
count_key(list(range(10)), "정렬된 10개")
count_key(list(range(10))[::-1], "역순 10개")
count_key([1] * 50, "같은 값 50개")
```

- 네 줄의 호출 횟수는 각각 몇이고, 그 수가 **언어 보장인가 구현 관찰인가**?

### 3. 동점끼리의 순서 (예측)

```python
rows = [("a", 2), ("b", 1), ("c", 2), ("d", 1), ("e", 2)]
print(sorted(rows, key=lambda r: r[1]))
print(sorted(rows, key=lambda r: r[1], reverse=True))
print(sorted(rows, key=lambda r: -r[1]))
print(sorted(rows, key=lambda r: r[1])[::-1])
```

- 뒤 세 줄 중 **혼자 다른 것은 어느 줄**이고, 무엇이 달라지는가?

### 4. `key` 안에서 그 리스트를 보면 (예측)

```python
data = [3, 1, 2]
seen = []
def peek(x):
    seen.append(list(data))
    return x
data.sort(key=peek)
print("정렬 중에 본 data :", seen)
print("정렬 뒤 data      :", data)

d2 = [3, 1, 2]
def mutate(x):
    d2.append(99)
    return x
try:
    d2.sort(key=mutate)
except ValueError as e:
    print(type(e).__name__, e)
```

### 5. 무엇이 지워지나 (예측)

```python
a = [0, 1, 2, True, 1.0]
a.remove(True)
print(a)
print([0, 1, 2].index(True), [0, 1, 1.0, True].count(1))

d = [10, 20, 30, 40]
del d[1]
print(d)
e = [10, 20, 30, 40]
print(e.pop(1), e)
try:
    [1, 2].remove(9)
except ValueError as ex:
    print(type(ex).__name__, ex)
try:
    [1, 2].pop(9)
except IndexError as ex:
    print(type(ex).__name__, ex)
```

- 두 예외의 **종류가 다른 이유**를 한 문장으로 말할 수 있는가?

### 6. 두 가지 이어 붙이기 (예측)

```python
a = [1, 2]; keep = a
a += "xy"
print(a, a is keep)
try:
    c = [1, 2]; c = c + "xy"
except TypeError as e:
    print(type(e).__name__, e)
f = [1, 2]; f += range(3)
print(f)
shared = [1]; alias = shared
shared += [2]
print(alias, alias is shared)
shared2 = [1]; alias2 = shared2
shared2 = shared2 + [2]
print(alias2, alias2 is shared2)
```

### 7. 안정 정렬은 누가 약속하나 (왜)

- 「파이썬의 정렬은 안정적이다」가 **언어 보장인지 CPython 구현 세부사항인지** 말하고, 그 근거가 어느 문서의 어느 문장인지 댈 수 있는가?

### 8. 다중 기준에서 방향이 섞이면 (경계)

- 「부서는 오름차순, 등급은 내림차순」을 `reverse=True` 로 **못 하는 이유**를 말하고, 쓸 수 있는 방법 두 가지를 댈 수 있는가?

### 9. 비교할 수 없는 것이 섞이면 (경계)

- `[3, 1, 2, "a"].sort()` 가 실패한 뒤 **원본이 어떤 상태로 남는지** 말하고, 그것이 보장인지 관찰인지 판정할 수 있는가?

### 10. 세 층 가르기 (경계)

- 이 주제에서 **언어 보장** · **CPython 구현 세부사항** · **이 판(3.12.3)·이 머신의 관찰**에 각각 해당하는 것을 나열할 수 있는가?

### 11. 조용한 실패를 막는 자리 (연결)

- 이 주제에서 **에러 없이 틀린 결과가 나오는 세 자리**를 대고, 각각을 무엇으로 막을지 판정할 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
