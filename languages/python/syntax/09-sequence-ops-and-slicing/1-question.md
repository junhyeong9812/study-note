# python/syntax/09-sequence-ops-and-slicing — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> ★ 이 주제에서는 **「에러가 안 난다」가 답인 자리가 많다.** 빈 것이 나오는지 예외가 나는지까지 적는다.
> 실행 환경: `python3` 3.12.3.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. 범위를 넘으면 (예측)

```python
s = [10, 20, 30, 40, 50]
for expr in ("s[4]", "s[5]", "s[-6]"):
    try:
        print(expr, "=", eval(expr))
    except IndexError as e:
        print(expr, "->", type(e).__name__)
print(s[5:], s[5:99], s[99:], s[-99:], s[3:1])
print(repr("abc"[9:]), (1, 2)[9:], range(3)[9:])
```

### 2. 역순으로 자르면 (예측)

```python
s = [10, 20, 30, 40, 50]
print(s[::-1])
print(s[-1:0:-1])
print(s[-1::-1])
print(s[-1:-1:-1])
print(s[3:0:-1], s[3::-1])
print(s[-1:-3], s[-3:-1])
```

- 여섯 줄의 출력은 각각 무엇이고, 둘째 줄에서 **무엇이 빠지며 왜** 빠지는가?

### 3. 대괄호 안에 무엇이 들어가나 (예측)

```python
class Show:
    def __getitem__(self, k):
        print(f"{k!r}  ({type(k).__name__})")

x = Show()
x[1]; x[1:4]; x[::-1]; x[1, 2]; x[1:2, 3]; x[...]
print(slice(1, 99, 2).indices(5))
print(slice(None, None, -1).indices(5))
print(list(range(*slice(None, None, -1).indices(5))))
```

### 4. 슬라이스에 대입하면 (예측)

```python
a = [1, 2, 3, 4, 5]
a[1:3] = ["X"]
print(a, len(a))
a[0:0] = ["앞"]
print(a)
b = [1, 2, 3]; c = b
b[:] = [9, 9, 9, 9]
print(b, c, b is c)
d = [1, 2, 3, 4, 5, 6]
try:
    d[::2] = ["a", "b"]
except ValueError as e:
    print(type(e).__name__, e)
e = [1, 2, 3]
e[0:1] = "XY"
print(e)
```

### 5. 세 칸이 같은 것을 가리키면 (예측)

```python
grid = [[]] * 3
grid[0].append("X")
print(grid, grid[0] is grid[1])

nums = [0] * 3
nums[0] = 9
print(nums)

a = [1, 2]; a2 = a
a += [3]
print(a2, a2 is a)

t1 = (1, 2); t2 = t1
t1 += (3,)
print(t2, t1 is t2)

print(repr([1, 2] * -1), repr("abc" * 0))
```

- 다섯 덩어리의 출력은 각각 무엇이고, 첫 덩어리는 걸리는데 **둘째는 안 걸리는 이유**는 무엇인가?

### 6. `in` 이 묻는 것 (예측)

```python
print("bc" in "abcd", "" in "abcd")
print([2, 3] in [1, 2, 3, 4], [2, 3] in [[2, 3], 1])
print((2, 3) in (1, 2, 3))
print(b"bc" in b"abcd", 98 in b"abcd")
try:
    "a" in b"abcd"
except TypeError as e:
    print(type(e).__name__)
```

### 7. `s[:]` 가 무엇을 새로 만드나 (경계)

- `list`·`tuple`·`str`·`bytes`·`bytearray`·`range` 각각에 대해 `o[:] is o` 가 무엇인지 말하고, 그중 **언어 보장이 아닌 것**을 가려낼 수 있는가?

### 8. 순회하면서 지우면 (왜)

- 리스트를 `for` 로 돌면서 `remove` 를 부르면 왜 예외가 안 나고 원소가 남는지 **인덱스의 움직임**으로 설명할 수 있는가?

### 9. `range` 의 `in` (경계)

- `x in range(n)` 의 비용이 `x` 의 **무엇에** 달려 있는지 말하고, 그 사실이 언어 보장인지 구현 관찰인지 판정할 수 있는가?

### 10. 세 층 가르기 (경계)

- 이 주제에서 **언어 보장** · **CPython 구현 세부사항** · **이 판(3.12.3)·이 머신의 관찰**에 각각 해당하는 것을 나열할 수 있는가?

### 11. 조용한 실패를 막는 자리 (연결)

- 이 주제에서 **에러 없이 틀린 결과가 나오는 세 자리**를 대고, 각각을 무엇으로 막을지 판정할 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
