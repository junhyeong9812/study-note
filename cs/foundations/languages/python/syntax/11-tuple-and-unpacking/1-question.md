# python/syntax/11-tuple-and-unpacking — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> ★ 이 주제에서는 **예외의 「종류와 문구」가 답인 자리가 많다.** 무엇이 나오는지까지 적는다.
> 실행 환경: `python3` 3.12.3.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. 괄호와 쉼표 (예측)

```python
for src in ("(1)", "(1,)", "1,", "1, 2", "()"):
    v = eval(src)
    print(f"{src:8} -> {v!r:10} {type(v).__name__}")
try:
    len((1))
except TypeError as e:
    print("len((1)) ->", type(e).__name__, e)
print(repr(((1))), repr(((1,))))

def g(*a): return a
print(g(1), g(1,), g((1,)), g(1, 2))
```

- 마지막 줄에서 `g(1)` 과 `g(1,)` 의 결과가 **같은 이유**는 무엇인가?

### 2. 여섯 가지 대입이 각각 어떻게 끝나나 (예측)

```python
for src in ("a, b = (1, 2, 3)", "a, b, c = (1, 2)", "a, b, *r = (1,)",
            "a, b = 5", "a, b = 'xyz'", "a, b = None"):
    try:
        exec(src)
        print(f"{src:20} -> OK")
    except (ValueError, TypeError) as e:
        print(f"{src:20} -> {type(e).__name__}: {e}")
```

- 예외가 **두 종류**로 갈리는 기준은 무엇인가?

### 3. 별표가 받는 것 (예측)

```python
a, *rest = [1, 2, 3, 4]
print(a, rest, type(rest).__name__)
*init, last = [1, 2, 3, 4]
print(init, last)
a, *r = [1]
print(a, r)
a, *r = (1, 2, 3)
print(a, r, type(r).__name__)
a, *r = {"k": 1, "j": 2}
print(a, r)

for src in ("a, *b, *c = [1,2,3]", "*a, *b = [1,2]"):
    try:
        exec(src)
        print(f"{src:20} -> OK")
    except SyntaxError as e:
        print(f"{src:20} -> SyntaxError: {e.msg}")
```

### 4. 세 자리의 별표 (예측)

```python
def show(a, b, c=0, **kw):
    return f"a={a} b={b} c={c} kw={kw}"
def gather(*a, **kw):
    return a, kw

print(show(*(1, 2), 3))
print(show(*"xy"))
print(gather(1, 2, k=3))
print(gather(*[1], *[2], *[3]))
try:
    show(**{1: 2})
except TypeError as e:
    print(type(e).__name__, e)
t = (1, 2)
print([*t, 3], (*t, 3), {**{"a": 1}, "b": 2})
```

- `gather` 가 받은 두 덩어리의 **타입**은 각각 무엇이고, 3번 문항의 `rest` 와 무엇이 다른가?

### 5. 컴파일러가 스왑에 무엇을 쓰나 (예측)

```python
import dis
dis.dis(compile("a, b = b, a", "<2>", "exec"))
print("-----")
dis.dis(compile("a, b, c, d = d, c, b, a", "<4>", "exec"))
print("-----")
dis.dis(compile("x = (1, 2, 3)", "<const>", "exec"))
```

- 두 스왑이 **다른 명령**을 쓰는가, 그렇다면 어디서 갈리는가?

### 6. 같은 상수 튜플의 정체 (예측)

```python
def f():
    a = (1, 2, 3)
    b = (1, 2, 3)
    return a is b
print(f(), f.__code__.co_consts)

t0 = (1, 2)
print(tuple(t0) is t0, t0[:] is t0, list(t0) is t0)
```

- 위 세 `is` 중 **문서가 약속한 것**은 어느 것인가?

### 7. 튜플이 불변인데 안이 바뀌는 것 (왜)

- `t = (1, [2, 3])` 에서 `t[1].append(4)` 가 되는데 `t[0] = 9` 는 안 되는 이유를, 「튜플이 무엇을 지키나」로 설명할 수 있는가?

### 8. `namedtuple` 과 `NamedTuple` 은 튜플인가 (경계)

- 두 가지로 만든 `(1, 2)` 와 평범한 `(1, 2)` 를 **한 집합에 넣으면 몇 개가 남는지** 말하고, 그 이유를 댈 수 있는가?

### 9. 봉지의 타입이 문제가 되는 자리 (경계)

- `a, *rest = t` 의 `rest` 를 딕셔너리 키로 쓰면 무엇이 나는지 말하고, 고치는 법을 댈 수 있는가?

### 10. 세 층 가르기 (경계)

- 이 주제에서 **언어 보장** · **CPython 구현 세부사항** · **이 판(3.12.3)·이 머신의 관찰**에 각각 해당하는 것을 나열할 수 있는가?

### 11. 조용한 실패를 막는 자리 (연결)

- 이 주제에서 **에러 없이 틀린 결과가 나오는 두 자리**를 대고, 각각을 무엇으로 막을지 판정할 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
