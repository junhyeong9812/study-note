# python/syntax/19-function-argument-rules — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> ★ 이 주제에서는 **「무슨 예외인가」보다 「언제 나는가」가 답인 자리가 많다.**
> 예외 이름만 맞히고 층을 못 대면 반만 맞은 것이다.
> 실행 환경: `python3` 3.12.3. 던지는 형태는 `python3 - <파일` 로 고정했다 —
> **실행 중 예외에는 캐럿이 없고 `SyntaxError` 에는 있다**(단 전부는 아니다).

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. 절대 안 도는 가지에 넣어 보면 (예측)

```text
===== 소스: ex.py =====
def f(*a, **k): pass
print("여기까지는 찍힐까?")
if False:
    f(a=1, 2)
```

그리고 따로 던진 이쪽.

```text
===== 소스: ex.py =====
def f(a, b): pass
print("여기는 찍힌다")
if False:
    f(1, 2, 3, 4, 5)
print("끝까지 왔다")
```

- 두 판이 갈리는 **기준을 한 문장**으로 말할 수 있는가?
- 「정의는 `SyntaxError`, 호출은 `TypeError`」라는 요약이 **왜 틀린 요약인가**?

### 2. 여덟 줄이 각각 무엇을 내나 (예측)

여덟 개를 **따로따로** 던졌다.

```text
===== 소스: ex.py =====
def f(a=1, b): pass
```

```text
===== 소스: ex.py =====
def f(**kw, a): pass
```

```text
===== 소스: ex.py =====
def f(*a, *b): pass
```

```text
===== 소스: ex.py =====
def f(*): pass
```

```text
===== 소스: ex.py =====
def f(a, /, b, /): pass
```

```text
===== 소스: ex.py =====
def f(/, a): pass
```

```text
===== 소스: ex.py =====
def f(a, a): pass
```

```text
===== 소스: ex.py =====
def f(*a, **k): pass
kw = {}; args = ()
f(x=1, x=2)
```

- 여덟 중 **여섯은 나오고 둘은 안 나오는 것**이 있다 — 무엇이고 왜 그런가?
- `def f(*): pass` 의 문구가 **무엇을 하라고 알려 주는가**?

### 3. 다섯 칸짜리 좌석표에 열두 번 (예측)

```text
===== 소스: ex.py =====
def f(pos, /, both, *, kw):
    return pos, both, kw

def show(label, thunk):
    try:
        print(f"  {label:<34} -> {thunk()}")
    except TypeError as e:
        print(f"  {label:<34} -> TypeError: {e}")

print("def f(pos, /, both, *, kw)")
show("f(1, 2, kw=3)",        lambda: f(1, 2, kw=3))
show("f(1, both=2, kw=3)",   lambda: f(1, both=2, kw=3))
show("f(1, 2, 3)",           lambda: f(1, 2, 3))
show("f(pos=1, both=2, kw=3)", lambda: f(pos=1, both=2, kw=3))
show("f(1, 2)",              lambda: f(1, 2))
show("f(1, 2, kw=3, extra=4)", lambda: f(1, 2, kw=3, extra=4))

print()
def g(a, b=2, *args, **kwargs):
    return a, b, args, kwargs
print("def g(a, b=2, *args, **kwargs)")
show("g(1)",                 lambda: g(1))
show("g(1, 2, 3, x=9)",      lambda: g(1, 2, 3, x=9))
show("g(1, 1, b=2)",         lambda: g(1, 1, b=2))
show("g(b=2)",               lambda: g(b=2))
show("g(1, pos=0)",          lambda: g(1, pos=0))

print()
print("--- 같은 인자를 위치와 키워드로 동시에 ---")
def h(x): return x
show("h(1, x=2)",            lambda: h(1, x=2))
def hp(x, /, **kw): return x, kw
show("hp(1, x=2)  (x 가 위치 전용)", lambda: hp(1, x=2))
```

- 마지막 두 줄이 **왜 갈리는지**, 그리고 그것이 `/` 의 **존재 이유와 어떻게 이어지는지** 말할 수 있는가?
- `g(1, pos=0)` 이 통과한 이유는?

### 4. 빈 것을 풀면 (예측)

```text
===== 소스: ex.py =====
def f(a, b=2, *args, kw="K", **kwargs):
    return a, b, args, kw, kwargs

def show(label, thunk):
    try:
        print(f"  {label:<38} -> {thunk()}")
    except TypeError as e:
        print(f"  {label:<38} -> TypeError: {e}")

print("def f(a, b=2, *args, kw='K', **kwargs)")
show("f(*[], **{})",              lambda: f(*[], **{}))
show("f(1, *[], **{})",           lambda: f(1, *[], **{}))
show("f(*[1, 2, 3], **{'kw': 'X'})", lambda: f(*[1, 2, 3], **{"kw": "X"}))
show("f(*'ab')",                  lambda: f(*"ab"))
show("f(*range(2), *range(2))",   lambda: f(*range(2), *range(2)))
show("f(1, **{'b': 9}, **{'z': 0})", lambda: f(1, **{"b": 9}, **{"z": 0}))
show("f(1, **{'b': 9}, **{'b': 8})", lambda: f(1, **{"b": 9}, **{"b": 8}))
show("f(*1)",                     lambda: f(*1))
show("f(1, **[('b', 2)])",        lambda: f(1, **[("b", 2)]))
show("f(1, **{1: 2})",            lambda: f(1, **{1: 2}))
show("f(1, **{'a': 9})",          lambda: f(1, **{"a": 9}))
```

- 키가 겹친 두 `**` 의 결과가 [12번](../12-dict-and-key-requirements/2-summary.md)의 `{**a, **b}` 와 **어떻게 다른가**?
- 출력 열한 줄 중 **함수 이름 앞에 `__main__.` 이 붙는 줄**은 어느 것이고, 그 차이가 무엇을 뜻하는가?

### 5. 네 창이 같은 시그니처를 어떻게 말하나 (예측)

```text
===== 소스: ex.py =====
import inspect

def f(pos, /, both=1, *args, kw, kw2="K", **kwargs):
    pass

print("signature      :", inspect.signature(f))
print()
print(f"{'이름':<8} {'종류':<22} {'기본값'}")
for name, p in inspect.signature(f).parameters.items():
    d = "없음" if p.default is inspect.Parameter.empty else repr(p.default)
    print(f"{name:<8} {p.kind.name:<22} {d}")

print()
c = f.__code__
print("__defaults__   :", f.__defaults__,   " <- 위치 인자의 기본값만, 뒤에서부터")
print("__kwdefaults__ :", f.__kwdefaults__, " <- 키워드 전용의 기본값")
print("co_argcount            :", c.co_argcount)
print("co_posonlyargcount     :", c.co_posonlyargcount)
print("co_kwonlyargcount      :", c.co_kwonlyargcount)
print("co_varnames[:co_argcount+co_kwonlyargcount+2] :", c.co_varnames[:c.co_argcount + c.co_kwonlyargcount + 2])
print("co_flags               :", c.co_flags, "=", bin(c.co_flags))
print("  CO_VARARGS  (0x04) 켜졌나 :", bool(c.co_flags & inspect.CO_VARARGS))
print("  CO_VARKEYWORDS (0x08)     :", bool(c.co_flags & inspect.CO_VARKEYWORDS))

def g(a, b):
    pass
print()
print("def g(a, b) 는")
print("  __defaults__   :", g.__defaults__)
print("  __kwdefaults__ :", g.__kwdefaults__)
print("  co_flags       :", g.__code__.co_flags, "| CO_VARARGS :", bool(g.__code__.co_flags & inspect.CO_VARARGS))
```

- `co_argcount` 가 세는 것과 **안 세는 것**은 각각 무엇인가?
- `co_varnames` 의 순서가 **소스 순서와 다른 자리**는 어디인가?
- `__defaults__` 가 **뒤에서부터** 대응한다는 사실이 **어떤 문법 규칙을 낳는가**?

### 6. 부르지 않고 알아본 것과 실제로 부른 것 (예측)

```text
===== 소스: ex.py =====
import inspect

def f(pos, /, both=1, *args, kw, kw2="K", **kwargs):
    return "돌았다"

sig = inspect.signature(f)
calls = [
    ((1,), {"kw": 2}),
    ((1, 2, 3), {"kw": 4, "z": 5}),
    ((1, 2), {}),
    ((), {"pos": 1, "kw": 2}),
]
for args, kwargs in calls:
    label = f"f(*{args}, **{kwargs})"
    try:
        b = sig.bind(*args, **kwargs)
        b.apply_defaults()
        print(f"  {label:<38} OK  {dict(b.arguments)}")
    except TypeError as e:
        print(f"  {label:<38} TypeError: {e}")

print()
print("--- 부르지 않고 미리 알아본 것과 실제로 부른 것이 같나 ---")
for args, kwargs in calls:
    label = f"f(*{args}, **{kwargs})"
    try:
        sig.bind(*args, **kwargs); pred = "OK"
    except TypeError:
        pred = "TypeError"
    try:
        f(*args, **kwargs); real = "OK"
    except TypeError:
        real = "TypeError"
    print(f"  {label:<38} 예측 {pred:<10} 실제 {real:<10} 같나 {pred == real}")
```

- **판정이 같은데 무엇이 다른가**, 그리고 그 차이가 **무엇을 하지 말라는 뜻인가**?

### 7. 키워드 전용에 기본값이 없으면 (경계)

- `def f(a, *, b)` 에서 `b` 를 안 주면 무엇이 나는지 말하고, 그것이 **`*args` 와 무엇이 다른지** 댈 수 있는가?

### 8. `/` 가 왜 있나 (왜)

- 위치 전용이 **「이름을 감추려고」가 아니라면** 무엇을 위한 것인지, 표준 라이브러리의 예를 들어 말할 수 있는가?

### 9. 두 층을 가르는 목록 (경계)

- 인자 관련 오류 열 가지를 **정의 시점(`SyntaxError`)과 호출 시점(`TypeError`)으로 갈라** 적을 수 있는가?
- 그중 **호출 자리에 쓰였는데 `SyntaxError` 인 것** 셋은 무엇인가?

### 10. 시그니처를 나중에 고칠 때 (연결)

- 이미 쓰이고 있는 함수에 인자를 하나 더 넣어야 한다 — **깨지지 않게** 하려면 어디에 무엇을 넣어야 하는가?

### 11. 세 층 가르기 (경계)

- 이 주제에서 **언어 보장** · **CPython 구현 세부사항** · **이 판(3.12.3)의 관찰**에 해당하는 것을 각각 나열할 수 있는가?

### 12. 이웃 주제와의 경계 (연결)

- 기본값 이야기가 **어디까지가 이 주제이고 어디부터가 [20번](../20-mutable-default-args/2-summary.md)인지** 한 줄로 그을 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
