# python/syntax/14-comprehensions — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 「컴프리헨션을 쓸 줄 아는가」는 묻지 않는다([`python-basics`](../../../../python-basics/README.md) 에 있다).
> 여기서 묻는 것은 **언제 계산되고, 이름이 어디까지 보이고, 예외가 어느 줄에서 나는가**다.
> 실행 환경: `python3` 3.12.3.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. 계산이 일어나는 줄 (예측)

```python
def mark(n):
    print("   계산:", n)
    return n * n

print("리스트 만들기 시작")
squares = [mark(n) for n in (1, 2, 3)]
print("리스트 완성:", squares)

print("제너레이터 만들기 시작")
lazy = (mark(n) for n in (1, 2, 3))
print("제너레이터 완성:", lazy)
print("첫 개 꺼냄:", next(lazy))
print("나머지:", list(lazy))
```

- `계산:` 줄들이 **어느 출력 줄들 사이에** 찍히는가?

### 2. 크기 (예측)

```python
import sys
print(sys.getsizeof([n for n in range(100000)]))
print(sys.getsizeof((n for n in range(100000))))
```

- 두 값의 자릿수가 어떻게 다르고, 원소를 1000만 개로 늘리면 각각 어떻게 변하는가?

### 3. 이름이 새는 곳과 안 새는 곳 (예측)

```python
for i in range(3):
    pass
print("A:", i)

sq = [j for j in range(3)]
print("B:", j)

i = "원래 값"
_ = [i for i in range(3)]
print("C:", repr(i))
```

- A·B·C 세 줄에서 각각 무슨 일이 일어나는가?

### 4. 왈러스 연산자가 만든 이름은 어디에 (예측)

```python
total = [(y := n * 2) for n in range(3)]
print(total, "| y =", y)
```

- `y` 는 살아남는가, 살아남는다면 값은 무엇이고 3번 답과 왜 달라지는가?

### 5. 클래스 몸통 안에서 (예측)

```python
class Table:
    factor = 10
    rows = [1, 2, 3]
    scaled = [r * factor for r in rows]
```

- 이 코드는 어떻게 되고, `rows` 는 보이는데 `factor` 는 안 보이는(혹은 보이는) 이유는 무엇인가?

### 6. 중첩 순서와 중복 (예측)

```python
print([(a, b) for a in "xy" for b in (1, 2)])
pairs = [("a", 1), ("b", 2), ("a", 3)]
print({k: v for k, v in pairs})
print({n % 3 for n in range(5)})
```

- 세 줄의 출력은 각각 무엇인가?

### 7. 예외가 나는 줄 (예측)

```python
data = [1, 0, 2]
bad = [10 // n for n in data]          # (a)
lazy = (10 // n for n in data)         # (b)
first = next(lazy)                     # (c)
second = next(lazy)                    # (d)
```

- (a)~(d) 중 **어느 줄에서** `ZeroDivisionError` 가 나는가?

### 8. 소진 — `in` 도 먹어 치운다 (경계)

```python
g = (n for n in range(5))
print(3 in g)
print(3 in g)
print(list(g))
```

- 세 줄의 출력은 무엇이고, 이것을 리스트 컴프리헨션으로 바꾸면 무엇이 달라지는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
