# python/syntax/23-lambda-and-higher-order-functions — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> ★ 이 주제에서는 **「무슨 예외인가」보다 「문구가 왜 갈리는가」가 답인 자리가 있다.**
> 예외 이름만 맞히고 문구의 갈림을 못 대면 반만 맞은 것이다.
>
> 실행 환경: `python3` **3.12.3**(Linux, x86_64). 던지는 형태는 `python3 - <파일` 로 고정했다 —
> 그래서 트레이스백이 `File "<stdin>", line N` 이 된다.\
> ★ **캐럿 규칙** — `SyntaxError` 에는 소스 줄과 캐럿(`^`)이 나오고 **실행 중 예외에는 안 나온다.**
> 단 `SyntaxError` 안에서도 **파서가 잡은 것만** 캐럿이 있다(심볼 테이블 단계가 잡은 것은 없다).
> 이 주제의 다섯 판이 어느 쪽인지도 문항에 들어 있다.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. 몸통에 이 다섯을 넣으면 (예측)

다섯을 **따로따로** 던졌다.

```python
# e23_stmt_assign.py
f = lambda x: x = x + 1
```

```python
# e23_stmt_return.py
f = lambda x: return x
```

```python
# e23_stmt_pass.py
handlers = [lambda: pass]
```

```python
# e23_stmt_raise.py
f = lambda: raise ValueError("no")
```

```python
# e23_stmt_annotation.py
f = lambda x: int: x
```

- 다섯이 각각 **무엇을 내는지** 예외 종류와 문구까지 적을 수 있는가?
- 다섯 중 **하나만 문구가 다르다** — 어느 것이고, 왜 그렇게 읽히는가?
- 다섯에 **캐럿이 나오는가**? 나온다면/안 나온다면 그것이 무엇을 말해 주는가?

### 2. 콜론 뒤에서 `:=` 를 쓰면 (예측)

```python
# e23_walrus.py
f = lambda n: (sq := n * n) + sq
print("lambda 안 := :", f(3))

vals = [1, 2, 3]
g = lambda xs: [(y := x * 2) for x in xs] + [y]
print("컴프리헨션 안 := :", g(vals))
```

- 두 줄이 각각 무엇을 찍는가?
- 1번의 대입문은 안 되는데 이것은 되는/안 되는 **기준이 무엇인가**?

### 3. 괄호를 열고 줄을 바꾸면 (예측)

```python
# e23_stmt_multiline.py
f = lambda x: (
    print("여러 줄은 된다 — 괄호 안이면 한 식이다"),
    x * 2,
)[1]
print(f(21))
```

- 무엇이 몇 줄 찍히는가?
- 이 결과가 「`lambda`는 한 줄짜리다」라는 요약에 **무엇을 하는가**?

### 4. 이름에 묶어 놓고 이름표를 물어보면 (예측)

```python
# e23_name.py
square = lambda n: n * n


def square_def(n):
    return n * n


print("__name__      :", square.__name__, "|", square_def.__name__)
print("__qualname__  :", square.__qualname__, "|", square_def.__qualname__)
print("__module__    :", square.__module__, "|", square_def.__module__)
print("__doc__       :", square.__doc__, "|", square_def.__doc__)
print("타입          :", type(square) is type(square_def))
print("repr 첫 낱말  :", repr(square).split()[0], repr(square).split()[1])


def make():
    return lambda: 0


print("함수 안 lambda 의 __qualname__:", make().__qualname__)
```

- 일곱 줄이 각각 무엇을 찍는가?
- 마지막 줄(`make()` 안에서 만든 것)은 **앞의 것들과 어디가 다른가**?

### 5. 한 줄에 둘을 놓고 뒤엣것을 터뜨리면 (예측)

```python
# e23_name_stack.py
import traceback


def boom():
    fns = [lambda: 1 / 0, lambda: 1 / 0]
    fns[1]()


try:
    boom()
except ZeroDivisionError:
    traceback.print_exc()
```

- 트레이스백이 **몇 줄**이고 마지막 프레임에 **무슨 이름**이 찍히는가?
- 그 출력만 보고 **둘 중 어느 것이 터졌는지 알 수 있는가**?

### 6. 같은 식을 `def` 와 `lambda` 로 써서 코드 객체를 맞대면 (예측)

```python
# e23_dis_same.py
import dis

add_lambda = lambda a, b: a + b


def add_def(a, b):
    return a + b


print("co_code 가 같은가 :", add_lambda.__code__.co_code == add_def.__code__.co_code)
print("co_consts         :", add_lambda.__code__.co_consts, "|", add_def.__code__.co_consts)
print("co_varnames       :", add_lambda.__code__.co_varnames, "|", add_def.__code__.co_varnames)
print("co_name           :", add_lambda.__code__.co_name, "|", add_def.__code__.co_name)
print("co_flags          :", add_lambda.__code__.co_flags, "|", add_def.__code__.co_flags)
print("--- dis.dis(add_lambda) ---")
dis.dis(add_lambda)
print("--- dis.dis(add_def) ---")
dis.dis(add_def)
```

- 다섯 개의 `co_*` 가 각각 **같은지 다른지** 적을 수 있는가?
- `dis` 출력 두 벌에서 **명령이 아니라 무엇이 갈리는가**?
- 이 결과를 「**언어 보장**」으로 적으면 왜 틀리는가?

### 7. `key=` 와 `cmp_to_key` 의 호출 횟수 (경계)

원소 8개짜리 리스트를 `sorted(data, key=k)` 로 한 번, `sorted(data, key=cmp_to_key(cmp))` 로 한 번 정렬하면서
`k`·`cmp` 가 불린 횟수를 셌다.

- 두 수가 각각 **몇 회**로 나왔고, 그중 **어느 쪽이 문서가 정한 수이고 어느 쪽이 관찰인가**?
- 이 실측으로 「`key` 쪽이 **더 빠르다**」고 적으면 왜 안 되는가?
- 정렬 규칙 자체의 정본은 [10번](../10-list-methods-and-sort-key/2-summary.md)인데, **여기서 말할 몫은 어디까지인가**?

### 8. `map` 객체를 두 번 쓰면 (경계)

`m = map(lambda n: n * n, [1, 2, 3, 4, 5])` 를 만들어 `list(m)` 을 **두 번** 불렀다.

- 두 번째가 무엇을 돌려주고, 그 근거가 **어느 주제의 계약**인가?
- `iter(m) is m` 이 무엇이며 그것이 왜 답의 근거가 되는가?

### 9. 루프 안에서 `lambda` 를 세 개 만들면 (연결)

`bad = [lambda: i for i in range(3)]` 를 만들어 셋을 전부 불렀다.

- 무엇이 나오고, 그 이유의 **정본이 어느 주제**인가?
- `lambda i=i: i` 로 고치면 `__closure__` 가 어떻게 되며, 그것이 **무엇을 뜻하는가**?

### 10. `lambda` 를 놓을 수 있는 자리 (경계)

- `lambda`가 들어갈 수 있는 자리를 **여덟 군데** 댈 수 있는가?
- 그중 **못 들어가는 자리**는 어디이고 그 기준은 무엇인가?

### 11. 인자 문법은 어디까지 되나 (연결)

- `lambda`에 **기본값·`*args`·키워드 전용·위치 전용**을 전부 쓸 수 있는가? 쓸 수 있다면 `def`와 **무엇만 다른가**?
- `inspect.signature` 로 봤을 때 `def`로 만든 것과 **구분할 수 있는 정보가 있는가**?

### 12. 세 층 가르기와 이웃 경계 (경계)

- 이 주제에서 **언어 보장** · **CPython 구현 세부사항** · **이 판(3.12.3)의 관찰**에 해당하는 것을 각각 셋 이상 나열할 수 있는가?
- 정렬은 [10번](../10-list-methods-and-sort-key/2-summary.md), 이터레이터는 [16번](../16-iterator-protocol/2-summary.md),
  클로저는 [22번](../22-closures-and-late-binding/2-summary.md)이 정본이다 — **여기서 다루는 몫을 한 줄씩** 그을 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
