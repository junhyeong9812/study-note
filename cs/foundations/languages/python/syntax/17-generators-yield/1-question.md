# python/syntax/17-generators-yield — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 **「이 코드의 출력을 예측할 수 있는가」**를 묻는다.
> 이 주제는 특히 **출력의 순서**가 답이다. 값만 맞히고 순서를 틀리면 틀린 것이다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> 실행 환경: `python3` 3.12.3.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. (예측)

```python
def steps():
    print("   A: 시작")
    yield 1
    print("   B: 1 과 2 사이")
    yield 2
    print("   C: 끝내는 중")

print("호출 직전")
g = steps()
print("호출 직후 ->", g)
print("next 1 ->", next(g))
print("next 2 ->", next(g))
try:
    next(g)
except StopIteration as e:
    print("StopIteration, value =", e.value)
```

- 출력 일곱 줄이 **어떤 순서로** 찍히는가?

### 2. (예측)

```python
 1  import inspect
 2
 3  def counter():
 4      total = 0
 5      for i in (10, 20, 30):
 6          total += i
 7          yield total
 8
 9  g = counter()
10  print(inspect.getgeneratorstate(g))
11  for _ in range(3):
12      v = next(g)
13      print(v, inspect.getgeneratorstate(g), g.gi_frame.f_lineno, g.gi_frame.f_locals)
14  try:
15      next(g)
16  except StopIteration:
17      print(inspect.getgeneratorstate(g), g.gi_frame)
```

- `f_lineno` 와 `f_locals` 가 세 번 각각 무엇으로 찍히고, 그것이 "멈춘다"의 뜻을 어떻게 증명하는가?

### 3. (예측)

```python
def src():
    yield "a"
    yield "b"

g = src()
print(list(g))
print(list(g))
```

- 두 줄의 출력은 각각 무엇이고, 둘째 줄이 **예외가 아닌** 이유는 무엇인가?

### 4. (예측)

```python
def adder():
    total = 0
    while True:
        x = yield total
        if x is None:
            x = 0
        total += x

a = adder()
print(next(a))
print(a.send(10))
print(a.send(5))

b = adder()
b.send(10)
```

- 앞의 세 줄은 무엇이 찍히고, 마지막 줄에서는 무슨 일이 일어나는가?

### 5. (왜)

```python
def guarded():
    try:
        yield 1
        yield 2
    finally:
        print("   finally: 정리했다")

c = guarded()
print(next(c))
c.close()
```

- `close()` 는 정확히 **어디에 무엇을** 하는 것이고, `yield 2` 와 `finally` 는 각각 도는가?

### 6. (예측)

```python
def inner():
    yield "i1"
    yield "i2"
    return "inner 의 return"

def outer():
    got = yield from inner()
    print("   outer 가 받은 return 값:", repr(got))
    yield "o1"

print(list(outer()))
```

- 출력은 무엇이고, `"inner 의 return"` 이 결과 리스트에 **없는** 이유는 무엇인가?

### 7. (경계)

```python
def boom():
    yield 1
    raise ValueError("여기서 터진다")

g = boom()               # (a) 여기서 예외가 나는가?
len(g)                   # (b) 이건 되는가?
gen = (print(n) for n in [1, 2, 3])   # (c) 여기서 1,2,3 이 찍히는가?
```

- (a)(b)(c) 세 줄이 **공통으로** 말하고 있는 성질 하나는 무엇인가?

### 8. (연결)

- `for item in gen:` 을 `iter`·`next`·`StopIteration` 만으로 풀어 쓰면 어떤 코드가 되는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
