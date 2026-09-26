# python/syntax/23-lambda-and-higher-order-functions — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> [1-question.md](1-question.md)의 번호와 **1:1**로 대응한다. 질문 12개 = 답 12개.
>
> 이 파일의 모든 출력은 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> 던지는 형태는 `python3 - <파일` 로 고정했다 — 그래서 `File "<stdin>", line N` 이 된다.\
> ★ **캐럿 규칙** — 이 주제의 `SyntaxError` 다섯 판은 **전부 캐럿이 나온다**(파서가 잡는다).
> [21번](../21-scope-legb-global-nonlocal/2-summary.md)의 `nonlocal` 오류들은 **소스 줄도 캐럿도 없다**(심볼 테이블 단계).\
> 단 **예외 문구·캐럿 폭·`dis` 출력·`co_flags` 값·`KeyWrapper` 라는 이름**은 구현에 달린 것이라 다른 판에서는 달라진다(12번 답).\
> ★ **이 문서는 시간을 안 쟀다** — 「`lambda`가 빠르다/느리다」는 여기 근거로 못 쓴다(6번 답).

## 정답

### 1. 다섯 전부 `SyntaxError` — 그런데 대입만 문구가 다르다

**출력** — 다섯을 따로 던진 결과다.

```python
# e23_stmt_assign.py
f = lambda x: x = x + 1
```

```text
===== python3 - <e23_stmt_assign.py =====
  File "<stdin>", line 1
    f = lambda x: x = x + 1
        ^^^^^^^^^^^
SyntaxError: cannot assign to lambda
(exit 1)
```

```python
# e23_stmt_return.py
f = lambda x: return x
```

```text
===== python3 - <e23_stmt_return.py =====
  File "<stdin>", line 1
    f = lambda x: return x
                  ^^^^^^
SyntaxError: invalid syntax
(exit 1)
```

```python
# e23_stmt_pass.py
handlers = [lambda: pass]
```

```text
===== python3 - <e23_stmt_pass.py =====
  File "<stdin>", line 1
    handlers = [lambda: pass]
                        ^^^^
SyntaxError: invalid syntax
(exit 1)
```

```python
# e23_stmt_raise.py
f = lambda: raise ValueError("no")
```

```text
===== python3 - <e23_stmt_raise.py =====
  File "<stdin>", line 1
    f = lambda: raise ValueError("no")
                ^^^^^
SyntaxError: invalid syntax
(exit 1)
```

```python
# e23_stmt_annotation.py
f = lambda x: int: x
```

```text
===== python3 - <e23_stmt_annotation.py =====
  File "<stdin>", line 1
    f = lambda x: int: x
                     ^
SyntaxError: invalid syntax
(exit 1)
```

**왜 그런가**

★★ **다섯 전부 `SyntaxError` 이고 프로그램이 시작조차 안 한다**(`(exit 1)`).
근거는 공식 문서 한 문장이다.

> *"Note that functions created with lambda expressions cannot contain statements or annotations."*

**statements or annotations** — 앞의 넷이 statements 이고, 다섯째가 annotations 다.

```text
   문구가 둘로 갈린다

   x = x + 1              cannot assign to lambda     <- 하나
   return / pass / raise  invalid syntax              <- 셋
   x: int                 invalid syntax              <- 애너테이션
```

★ **대입만 다른 이유** — `f = lambda x: x = x + 1` 을 파서가 왼쪽부터 읽으면
`f = (lambda x: x)` 까지가 **멀쩡한 한 식**이고, 그 뒤에 `= x + 1` 이 붙는다.
그러면 **`lambda` 식에 대입하려는 문장으로** 읽혀서
「이 자리에 문장을 못 쓴다」가 아니라 **`lambda`에 대입할 수 없다는 말**이 나온다.\
**캐럿이 `lambda x: x` 전체를 덮는 것**이 그 증거다 — 파서가 그 범위를 **대입의 왼쪽**으로 보고 있다.

- **나머지 셋은 그냥 「식이 시작될 수 없다」다.** `return`·`pass`·`raise` 는 **문장을 여는 낱말**이라
  파서가 그 낱말 앞에서 멈춘다. 캐럿이 그 낱말에 정확히 붙는다.
- ★ **애너테이션 판의 캐럿은 한 칸짜리다.** `lambda x: int: x` 에서 **첫 콜론까지는 멀쩡한 `lambda` 라서**
  **두 번째 콜론**에서 처음 어긋나기 때문이다. 문서가 말한 **"or annotations"** 쪽의 실증이 이것이다.

★★ **캐럿이 나온다는 것 자체가 정보다 — 「파서가 잡았다」는 표시다.**

```text
   파서가 잡는다                  심볼 테이블 단계가 잡는다
   ─────────────────────────     ─────────────────────────────
   File "<stdin>", line 1        File "<stdin>", line 3
     f = lambda x: return x      SyntaxError: no binding for nonlocal 'x' found
                   ^^^^^^
   SyntaxError: invalid syntax   <- 소스 줄도 캐럿도 없다 (21번)
```

★ **둘 다 `SyntaxError` 인데 화면이 다르다.** 어느 단계가 잡았는지가 **출력에 그대로 드러난다** —
정본은 [21번](../21-scope-legb-global-nonlocal/2-summary.md)이고, 여기는 **캐럿이 나오는 쪽의 대조군**이다.

### 2. `:=` 는 된다 — 경계는 「짧음」이 아니라 「식이냐」다

**출력**

```python
# e23_walrus.py
f = lambda n: (sq := n * n) + sq
print("lambda 안 := :", f(3))

vals = [1, 2, 3]
g = lambda xs: [(y := x * 2) for x in xs] + [y]
print("컴프리헨션 안 := :", g(vals))
```

```text
===== python3 - <e23_walrus.py =====
lambda 안 := : 18
컴프리헨션 안 := : [2, 4, 6, 6]
(exit 0)
```

**왜 그런가**

```text
   x = x + 1        대입"문"(statement)    값이 안 남는다  ->  lambda 몸통에 못 넣는다
   (x := x + 1)     대입"식"(expression)   값이 남는다     ->  들어간다
```

- `f = lambda n: (sq := n * n) + sq` 에서 `(sq := n * n)` 은 **`n * n` 이라는 값**이면서
  그 값을 이름 `sq`에도 붙인다. **값이 남으므로 식**이고, 식이므로 `lambda` 안에 들어간다.
  `f(3)` 은 `9 + 9` 라서 `18` 이다.
- 둘째 줄은 **컴프리헨션 안의 `:=` 를 쓴 것이다.** 컴프리헨션이 끝난 뒤에도 `y` 가 **마지막 값(`6`)으로 남아** 있어
  `[2, 4, 6] + [6]` 이 된다. ★ 컴프리헨션의 스코프 규칙은 [21번](../21-scope-legb-global-nonlocal/2-summary.md)이 정본이다.

★★ **그래서 「`lambda` 안에서는 아무것도 못 바꾼다」는 틀린 요약이다.**
금지된 것은 **문장**이지 **변경**이 아니다 — `lst.append(x)` 같은 **부작용 있는 호출**도 언제나 식이었다.

★ **1번과 나란히 놓으면 선이 정확히 보인다** — `=` 는 문장이라 `SyntaxError`, `:=` 는 식이라 통과.
**이것이 「문장 금지」의 정확한 경계다.**

### 3. 여러 줄이 된다 — 「한 줄」은 규칙이 아니었다

**출력**

```python
# e23_stmt_multiline.py
f = lambda x: (
    print("여러 줄은 된다 — 괄호 안이면 한 식이다"),
    x * 2,
)[1]
print(f(21))
```

```text
===== python3 - <e23_stmt_multiline.py =====
여러 줄은 된다 — 괄호 안이면 한 식이다
42
(exit 0)
```

**왜 그런가**

★ **소스에 줄바꿈이 세 번 있는데 멀쩡히 돈다.**
괄호(`(`·`[`·`{`) 안에서는 **줄바꿈이 문장의 끝이 아니기** 때문이다 — 괄호가 닫힐 때까지가 **한 식**이다.

```text
   f = lambda x: (          ┐
       print(...),          │  괄호가 안 닫혔으므로
       x * 2,               │  줄바꿈이 문장을 안 끝낸다
   )[1]                     ┘  -> 전부 한 식

   튜플 (None, 42) 를 만들고 [1] 로 42 만 꺼낸다
   print 는 만들면서 이미 찍혔다 -> 출력이 두 줄
```

- **`print(...)` 가 먼저 찍히고** 그 다음에 `42` 가 찍힌 것은, 튜플을 만들 때 원소를 **왼쪽부터 평가**하기 때문이다.
- ★ 그래서 정확한 요약은 **`lambda`는 한 식이라는 것**이고, **「한 줄」은 그 결과일 뿐**이다.
- ★★ **되는 것과 쓸 것은 다르다.** `(부작용, 값)[1]` 꼴은 `def` 두 줄로 쓸 것을 비틀어 놓은 것이라
  읽는 비용이 훨씬 크다. 이 블록은 **문법의 경계를 보이려고 던진 것**이지 본보기가 아니다.

### 4. 이름표는 `<lambda>` — 대입은 함수 객체를 안 건드린다

**출력**

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

```text
===== python3 - <e23_name.py =====
__name__      : <lambda> | square_def
__qualname__  : <lambda> | square_def
__module__    : __main__ | __main__
__doc__       : None | None
타입          : True
repr 첫 낱말  : <function <lambda>
함수 안 lambda 의 __qualname__: make.<locals>.<lambda>
(exit 0)
```

**왜 그런가**

문서가 직접 그 이름을 적어 놓았다.

> *"The unnamed object behaves like a function object defined with `def <lambda>(parameters): return expression`"*

```text
   square = lambda n: n * n

   ┌──────────────────────────────┐
   │ 함수 객체                     │
   │  __name__     = "<lambda>"   │  <- 대입해도 안 바뀐다
   │  __qualname__ = "<lambda>"   │
   │  __doc__      = None         │  <- 독스트링을 둘 자리가 없다
   │  type         = function     │  <- def 로 만든 것과 같은 타입
   └──────────────────────────────┘
        ▲
        │  square = ...  <- 이건 대입문의 일이지 lambda 의 일이 아니다
```

- **타입이 같다** — `type(square) is type(square_def)` 가 `True` 다. **다른 종류의 물건이 아니다.**
- ★ **`__name__` 만 다르다.** `lambda`는 이름 없이 만들어지므로 **`<lambda>` 라는 자리표시자**가 들어가고,
  `square = ...` 로 묶어도 **안 바뀐다.**
- ★ **`__doc__` 이 `None` 이다** — 몸통이 식 하나라 독스트링을 담을 자리가 없다.
  **설명이 필요해지는 순간이 `def`로 옮길 때**다.
- ★★ **마지막 줄이 앞의 것들과 다른 점** — `make()` 안에서 만든 `lambda`의 `__qualname__` 은
  `make.<locals>.<lambda>` 다. **어느 함수 안에서 태어났는지**는 남지만
  **그 함수 안의 몇 번째인지는 여전히 모른다.** 그 한계가 5번 답에서 그대로 문제가 된다.

### 5. 트레이스백이 `in <lambda>` 라고만 말한다 — 구분 불가

**출력**

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

```text
===== python3 - <e23_name_stack.py =====
Traceback (most recent call last):
  File "<stdin>", line 10, in <module>
  File "<stdin>", line 6, in boom
  File "<stdin>", line 5, in <lambda>
ZeroDivisionError: division by zero
(exit 0)
```

**왜 그런가**

★★ **`fns[1]()` 을 불렀는데 트레이스백은 `in <lambda>` 라고만 한다.**
둘이 **같은 줄**(5번 줄)에 있으니 **줄 번호로도 못 가른다.**

```text
   fns = [lambda: 1 / 0, lambda: 1 / 0]      <- 둘 다 5 번 줄
          ^^^^^^^^^^^^^  ^^^^^^^^^^^^^
            첫째             둘째 (터진 것)

   File "<stdin>", line 5, in <lambda>
                              ^^^^^^^^  이름표가 없으니 이것으로는 못 가른다

   def 로 썼다면
   File "<stdin>", line 5, in divide_b      <- 이름이 답한다
```

- 프레임은 셋이다 — `<module>`(부른 자리) → `boom` → `<lambda>`. **`boom` 까지는 이름으로 따라갈 수 있고**
  마지막 한 칸에서 정보가 끊긴다.
- ★★ **이것이 「이름에 묶을 거면 `def`를 써라」의 실측 근거다.**
  「스타일이 나쁘다」가 아니라 **디버깅할 때 정보가 실제로 없다**는 것이 근거다.
- ★★ **성능을 근거로 대면 안 된다 — 이 문서는 `timeit` 을 안 돌렸다.** 6번 답이 보여 주듯
  **코드 객체가 같아서** 성능 차이를 기대할 근거도 없다.
- ★ 반대로 **한 번 쓰고 버리는 자리**(`key=`·`map`의 첫 인자)에서는 이 비용이 안 생긴다 —
  거기서 터지면 **호출한 쪽 줄**이 트레이스백에 남기 때문이다.

### 6. `co_code` 가 같다 — `co_name` 만 다르고, `dis` 는 줄 표가 갈린다

**출력**

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

```text
===== python3 - <e23_dis_same.py =====
co_code 가 같은가 : True
co_consts         : (None,) | (None,)
co_varnames       : ('a', 'b') | ('a', 'b')
co_name           : <lambda> | add_def
co_flags          : 3 | 3
--- dis.dis(add_lambda) ---
  3           0 RESUME                   0
              2 LOAD_FAST                0 (a)
              4 LOAD_FAST                1 (b)
              6 BINARY_OP                0 (+)
             10 RETURN_VALUE
--- dis.dis(add_def) ---
  6           0 RESUME                   0

  7           2 LOAD_FAST                0 (a)
              4 LOAD_FAST                1 (b)
              6 BINARY_OP                0 (+)
             10 RETURN_VALUE
(exit 0)
```

**왜 그런가**

★★ **`co_code` 가 `True` — 바이트열이 한 바이트도 같다.**

```text
   add_lambda = lambda a, b: a + b       def add_def(a, b):
                                             return a + b
   ┌─────────────────────────┐           ┌─────────────────────────┐
   │ co_code     같다         │ <──────>  │ co_code     같다         │
   │ co_consts   (None,)     │           │ co_consts   (None,)     │
   │ co_varnames ('a','b')   │           │ co_varnames ('a','b')   │
   │ co_flags    3           │           │ co_flags    3           │
   │ co_name     <lambda>    │ <- 여기만 ->│ co_name     add_def     │
   └─────────────────────────┘           └─────────────────────────┘
```

★ **`dis` 에서 갈리는 것은 명령이 아니라 왼쪽의 줄 번호 칸이다.**

```text
   dis.dis(add_lambda)            dis.dis(add_def)
   ─────────────────────          ─────────────────────
     3   0 RESUME                   6   0 RESUME        <- def 줄
         2 LOAD_FAST  a                 (빈 줄로 끊긴다)
         4 LOAD_FAST  b             7   2 LOAD_FAST  a  <- return 줄
         6 BINARY_OP  +                 4 LOAD_FAST  b
        10 RETURN_VALUE                 6 BINARY_OP  +
                                       10 RETURN_VALUE
   소스가 한 줄이라 안 갈린다      소스가 두 줄이라 갈린다
```

- **명령 다섯 개와 오프셋(0·2·4·6·10)이 양쪽 다 같다.** 갈린 것은 **소스 줄 번호를 표시하는 칸**뿐이고,
  그것은 `co_code` 가 아니라 **줄 번호 표**에서 온다.
- ★ **`co_flags` 가 `3`** 인 것도 둘이 같다 — `CO_OPTIMIZED | CO_NEWLOCALS`([19번](../19-function-argument-rules/2-summary.md)에서 본 그 플래그다).

★★ **이것을 「언어 보장」으로 적으면 틀리는 이유** — 문서가 보장하는 것은
「`def <lambda>(parameters): return expression` 로 정의한 함수 객체처럼 **동작한다**」까지다.
**「같은 바이트코드를 낸다」는 약속이 아니다** — 애초에 **바이트코드가 없는 파이썬 구현**도 있을 수 있다.
`co_code`·`dis`·`co_flags` 는 전부 **CPython 의 내성 인터페이스**다.

★ 그래서 이 실측에서 **가져갈 결론은 하나**다 — **`lambda`와 `def`를 고를 이유는 성능이 아니라 「이름이 필요한가」다.**

### 7. 8회 대 16회 — 하나는 보장이고 하나는 관찰이다

**출력**

```python
# e23_key_call_count.py
from functools import cmp_to_key

data = [5, 3, 8, 1, 9, 2, 7, 4]

key_calls = []
cmp_calls = []


def key(x):
    key_calls.append(x)
    return x


def cmp(a, b):
    cmp_calls.append((a, b))
    return (a > b) - (a < b)


print("key 로 정렬:", sorted(data, key=key))
print("cmp 로 정렬:", sorted(data, key=cmp_to_key(cmp)))
print("원소 수      :", len(data))
print("key 호출 횟수:", len(key_calls), "— 원소당 한 번")
print("cmp 호출 횟수:", len(cmp_calls), "— 비교할 때마다")
print("key 가 받은 순서:", key_calls)
```

```text
===== python3 - <e23_key_call_count.py =====
key 로 정렬: [1, 2, 3, 4, 5, 7, 8, 9]
cmp 로 정렬: [1, 2, 3, 4, 5, 7, 8, 9]
원소 수      : 8
key 호출 횟수: 8 — 원소당 한 번
cmp 호출 횟수: 16 — 비교할 때마다
key 가 받은 순서: [5, 3, 8, 1, 9, 2, 7, 4]
(exit 0)
```

**왜 그런가**

```text
   data = [5, 3, 8, 1, 9, 2, 7, 4]   (원소 8개)

   key=k                              key=cmp_to_key(cmp)
   ┌────────────────────────┐         ┌────────────────────────┐
   │ 원소마다 한 번씩 k(x)   │         │ 두 원소를 볼 때마다      │
   │ 8 회                   │         │   cmp(a, b)            │
   │ 받은 순서 = 원본 순서   │         │ 이 데이터에서 16 회      │
   └────────────────────────┘         └────────────────────────┘
      문서가 정한 횟수                    데이터·구현에 달린 관찰
```

- ★★ **8은 보장, 16은 관찰이다.** `key` 가 **원소당 한 번** 계산된다는 것은
  [Sorting HOW TO](https://docs.python.org/3.12/howto/sorting.html)와 `list.sort` 문서가 정한다.
  `cmp` 호출 횟수는 **정렬 알고리즘과 데이터 배열**에 달렸다 — **다른 데이터면 다른 수가 나온다.**
- ★★ **「`key` 쪽이 더 빠르다」고 적으면 안 되는 이유** — **시간을 안 쟀다.**
  적을 수 있는 것은 「**호출 횟수가 8 대 16으로 나왔다**」와 「**`key` 는 원소당 한 번이라고 문서가 정한다**」뿐이다.
  호출 횟수와 시간은 다른 것이고, 이 노트에는 `timeit` 결과가 없다.
- **`key` 가 받은 순서는 원본 순서**(`[5, 3, 8, 1, 9, 2, 7, 4]`)였다.
  ★ **그 순서는 문서가 약속하지 않는다** — 횟수만 약속한다.

★ **여기서 말할 몫의 경계** — 정렬 규칙(안정성·`key` 계약·비교 횟수)의 정본은
[10번](../10-list-methods-and-sort-key/2-summary.md)이다.
**이 주제의 몫은 「그 `key` 자리에 `lambda`가 들어간다」와 「`lambda`를 어떻게 짜느냐가 호출 횟수를 바꾼다」까지다.**

### 8. 두 번째는 빈 리스트다 — 이터레이터라서

**출력**

```python
# e23_map_filter.py
nums = [1, 2, 3, 4, 5]

m = map(lambda n: n * n, nums)
f = filter(lambda n: n % 2, nums)
print("map 객체   :", type(m).__name__, "· 이터레이터인가:", iter(m) is m)
print("filter 객체:", type(f).__name__, "· 이터레이터인가:", iter(f) is f)
print("map 결과   :", list(m))
print("filter 결과:", list(f))
print("두 번째로 비우면:", list(m), list(f))

print("컴프리헨션으로 같은 것:", [n * n for n in nums], [n for n in nums if n % 2])
```

```text
===== python3 - <e23_map_filter.py =====
map 객체   : map · 이터레이터인가: True
filter 객체: filter · 이터레이터인가: True
map 결과   : [1, 4, 9, 16, 25]
filter 결과: [1, 3, 5]
두 번째로 비우면: [] []
컴프리헨션으로 같은 것: [1, 4, 9, 16, 25] [1, 3, 5]
(exit 0)
```

**왜 그런가**

```text
   nums ─> map 객체 ─ list(m) 한 번 ─> [1, 4, 9, 16, 25]
                          │
                          └─ 다 흘려보냈다 ─ list(m) 또 ─> []
```

- ★ **`iter(m) is m` 이 `True` 다.** **자기 자신을 돌려주는 것**이 이터레이터의 정의이고,
  그래서 **되감을 자리가 없다.** 한 번 흐르면 빈다.
  **정본은 [16번](../16-iterator-protocol/2-summary.md)이다** — 「왜 한 번만 흐르나」는 그쪽,
  「`map`·`filter` 가 그 계약을 따른다」는 여기.
- **`filter` 의 판정은 참/거짓 판정**이다 — `n % 2` 가 `0`이면 버린다([05번](../05-truthiness-and-short-circuit/2-summary.md)).
- ★ **컴프리헨션으로 같은 결과가 나온다** — `[n * n for n in nums]`·`[n for n in nums if n % 2]`.
  차이는 **리스트는 남고 `map` 객체는 빈다**는 것이다.
- **두 번 쓸 것이면 `list()` 로 굳힌다.** 그것이 유일한 처방이다.

### 9. `[2, 2, 2]` — `lambda` 라고 다르지 않다

**출력**

```python
# e23_late_binding.py
bad = [lambda: i for i in range(3)]
good = [lambda i=i: i for i in range(3)]
print("lambda 도 똑같이 늦게 읽는다:", [f() for f in bad])
print("기본 인자로 고치면        :", [f() for f in good])
print("bad 의 자유 변수            :", bad[0].__code__.co_freevars)
print("세 lambda 가 같은 셀인가    :", bad[0].__closure__[0] is bad[2].__closure__[0])
print("good[0].__closure__       :", good[0].__closure__)
print("good 의 __defaults__      :", [f.__defaults__ for f in good])
```

```text
===== python3 - <e23_late_binding.py =====
lambda 도 똑같이 늦게 읽는다: [2, 2, 2]
기본 인자로 고치면        : [0, 1, 2]
bad 의 자유 변수            : ('i',)
세 lambda 가 같은 셀인가    : True
good[0].__closure__       : None
good 의 __defaults__      : [(0,), (1,), (2,)]
(exit 0)
```

**왜 그런가**

```text
   bad = [lambda: i for i in range(3)]

        ┌──── 셀(cell) 하나 ────┐
        │        i = 2         │   <- 루프가 끝난 뒤의 값
        └──────────┬───────────┘
           ▲       ▲       ▲
        lambda  lambda  lambda   -> [2, 2, 2]

   good = [lambda i=i: i for i in range(3)]

        ┌──────┐ ┌──────┐ ┌──────┐
        │ i=0  │ │ i=1  │ │ i=2  │   __defaults__ 에 굳는다
        └──────┘ └──────┘ └──────┘   -> [0, 1, 2]
```

- ★ **대조할 것은 주소가 아니라 「셀이 하나」라는 것이다** —
  `bad[0].__closure__[0] is bad[2].__closure__[0]` 가 `True` 였다.
  `co_freevars` 가 `('i',)` 인 것이 **자유 변수를 잡았다**는 증거다.
- ★★ **고친 쪽은 `__closure__` 가 `None` 이다.** 클로저를 「고친」 것이 아니라 **아예 안 만든 것**이다 —
  `i`가 **파라미터**가 되어 자유 변수이기를 그만두었고, 값은 `__defaults__` 에 `(0,)`·`(1,)`·`(2,)` 로 굳었다.
  그 「기본값이 정의 시점에 한 번 굳는다」의 정본은 [20번](../20-mutable-default-args/2-summary.md)이다.
- ★ **정본은 [22번](../22-closures-and-late-binding/2-summary.md)이다.** 늦은 바인딩은 `def`로 만든 중첩 함수에서도
  똑같이 난다 — **`lambda`의 성질이 아니라 클로저의 성질**이다.
  여기서 말할 것은 **「`lambda`라고 예외가 아니다」** 한 줄과,
  **「`lambda`가 그 클로저를 만드는 가장 짧은 문법이다」** 한 줄뿐이다.

### 10. 여덟 자리 — 기준은 「식이 들어가는 자리인가」다

**출력**

```python
# e23_where_allowed.py
import functools

ops = {"+": lambda a, b: a + b, "-": lambda a, b: a - b}


def apply(fn, a, b):
    return fn(a, b)


class Row:
    fmt = staticmethod(lambda n: "[%03d]" % n)


def defaulted(f=lambda: "기본으로 넣은 lambda"):
    return f()


print("dict 값으로      :", ops["+"](3, 4), ops["-"](3, 4))
print("인자로           :", apply(lambda a, b: a * b, 3, 4))
print("클래스 몸통에서   :", Row.fmt(7))
print("기본값으로       :", defaulted())
print("즉시 부르기      :", (lambda n: n + 1)(41))
print("반환값으로       :", (lambda: (lambda: "두 겹"))()())
print("partial 과 함께  :", functools.partial(lambda a, b: a - b, 10)(3))
print("데코레이터 자리에 :", (lambda fn: lambda: fn() * 2)(lambda: 21)())
```

```text
===== python3 - <e23_where_allowed.py =====
dict 값으로      : 7 -1
인자로           : 12
클래스 몸통에서   : [007]
기본값으로       : 기본으로 넣은 lambda
즉시 부르기      : 42
반환값으로       : 두 겹
partial 과 함께  : 7
데코레이터 자리에 : 42
(exit 0)
```

**왜 그런가**

| 자리 | 꼴 | 쓸모 |
|---|---|---|
| **dict 값** | `{"+": lambda a, b: a + b}` | ★ 분기표 — `if/elif` 사다리를 없앤다 |
| **다른 함수의 인자** | `apply(lambda a, b: a * b, 3, 4)` | ★ 가장 흔한 제자리 |
| **클래스 몸통** | `fmt = staticmethod(lambda n: ...)` | 작은 포맷터 |
| **기본값** | `def f(cb=lambda: ...)` | 「아무것도 안 하는 콜백」 |
| **즉시 호출** | `(lambda n: n + 1)(41)` | 괄호로 싸서 그 자리에서 부른다 |
| **반환값** | `return lambda: ...` | ★ 여기서 클로저가 생긴다(9번 답) |
| **`partial` 과 함께** | `partial(lambda a, b: a - b, 10)(3)` | 인자를 앞에서부터 고정한다 |
| **데코레이터가 할 일** | `(lambda fn: lambda: fn() * 2)(...)` | ★ [24번](../24-decorators/2-summary.md)의 골격을 손으로 편 것 |

★ **기준 한 줄** — **`lambda`는 식이므로, 식이 들어가는 자리에는 전부 들어간다.**

```text
   들어간다 (식 자리)                    못 들어간다 (문장 자리)
   ─────────────────────────────        ─────────────────────────────
   인자 · dict 값 · 기본값               if 의 몸통 · for 의 몸통
   반환값 · 괄호 안 · 대입의 오른쪽       try/except 의 몸통
                                        (그 자리엔 문장이 와야 한다)
```

- ★ **마지막 칸은 「`@` 뒤에 `lambda`를 쓴다」는 뜻이 아니다.** 데코레이터가 하는 일
  (**함수를 받아 함수를 돌려준다**)을 `lambda` 두 겹으로 편 것이고,
  **`@` 문법에 직접 쓰는 것은 이 문서에서 안 던져 봤다.**
- ★ **「반환값으로」 칸에 괄호가 두 번 붙는 것**(`(lambda: (lambda: "두 겹"))()()`)이 요점이다 —
  바깥을 부르면 **안쪽 `lambda`가 값으로 나오고**, 한 번 더 불러야 문자열이 나온다.
- **클래스 몸통에 넣을 때는 [21번](../21-scope-legb-global-nonlocal/2-summary.md)의 클래스 스코프 규칙이 그대로 걸린다** —
  클래스 몸통의 이름은 메서드·`lambda` 안에서 안 보인다.

### 11. 인자 문법은 전부 된다 — 괄호만 없다

**출력**

```python
# e23_signature.py
import inspect

f = lambda a, b=1, *args, c, **kw: None
print("시그니처:", inspect.signature(f))
print("__defaults__ :", f.__defaults__)
print("__kwdefaults__:", f.__kwdefaults__)

g = lambda a, /, b, *, c: None
print("위치 전용까지:", inspect.signature(g))
```

```text
===== python3 - <e23_signature.py =====
시그니처: (a, b=1, *args, c, **kw)
__defaults__ : (1,)
__kwdefaults__: None
위치 전용까지: (a, /, b, *, c)
(exit 0)
```

**왜 그런가**

```text
   lambda a, b=1, *args, c, **kw: None
          │  ───  ─────  │  ────
          │   │     │    │    └ 나머지 키워드
          │   │     │    └───── 키워드 전용 (기본값이 없으니 필수)
          │   │     └────────── 나머지 위치
          │   └──────────────── 기본값
          └──────────────────── 위치

   lambda a, /, b, *, c: None      <- / 도 * 도 된다 (3.8+)
```

- **문서가 그렇게 정한다** — `lambda` 의 **파라미터 목록 문법이 함수 정의의 것과 같다.**
  그래서 [19번](../19-function-argument-rules/2-summary.md)에서 배운 다섯 칸이 **그대로 다 쓰인다.**
- ★ **`def`와 다른 것은 괄호 하나뿐이다** — `def f(a, b=1)` 의 소괄호가 `lambda a, b=1` 에는 없다.
  (그리고 몸통이 식 하나라는 것 — 그게 1번 답의 내용이다.)
- **`__defaults__` 가 `(1,)`, `__kwdefaults__` 가 `None`** 으로 나왔다 — `def`와 **같은 모양**이다.
- ★★ **`inspect.signature` 로 보면 구분할 정보가 없다** — `(a, b=1, *args, c, **kw)` 라고만 나온다.
  **시그니처 층에서는 `def`인지 `lambda`인지 알 수 없고**, 구분이 나타나는 곳은 **`__name__`·`__qualname__`** 뿐이다(4번 답).

★ 실무적 결론 — **문법은 되지만 인자가 복잡해질수록 `lambda`로 쓸 이유가 사라진다.**
키워드 전용까지 쓰는 함수라면 **이름과 독스트링이 필요한 함수**일 가능성이 높다.

### 12. 세 층과 이웃 경계

**세 층 가르기**

| 층 | 이 주제에서 |
|---|---|
| **언어 보장** | ① `lambda` 는 **문장도 애너테이션도 담을 수 없다**(6.14) ② 만들어지는 것은 **`def <lambda>(...)` 로 정의한 함수 객체처럼 동작한다** ③ **파라미터 목록 문법이 함수 정의와 같다** ④ `map`·`filter` 는 **이터레이터**를 돌려준다 ⑤ `sorted` 의 `key` 는 **원소당 한 번** ⑥ `reduce` 는 **왼쪽부터** 접는다 |
| **CPython 구현** | ① **`co_code` 가 `def` 쪽과 같고 `co_name` 만 다르다** ② `dis` 의 **줄 표가 갈린다** ③ 예외 **문구**가 `cannot assign to lambda` 와 `invalid syntax` 로 갈린다 ④ **이 다섯에 캐럿이 있다**(21번의 `nonlocal` 오류에는 없다) ⑤ `cmp_to_key` 가 만드는 타입 이름이 **`KeyWrapper`** ⑥ `__closure__`·셀 객체의 겉모습 |
| **이 판(3.12.3)의 관찰** | ① **캐럿 폭**(대입 판은 11칸, 애너테이션 판은 1칸) ② `dis` 의 **오프셋·명령 이름** ③ `co_flags` 가 **`3`** ④ **`cmp` 호출 16회** ⑤ `key` 가 받은 순서가 **원본 순서**인 것 ⑥ 함수 `repr` 의 **주소** |

★ **가장 자주 틀리는 자리** — **`co_code` 가 같다**는 것을 언어 보장으로 옮겨 적는 것이다.
문서는 「**동작한다**」까지만 말한다.

**이웃 경계 — 한 줄씩**

| 주제 | 경계 |
|---|---|
| [10번](../10-list-methods-and-sort-key/2-summary.md) | **정렬 규칙의 정본.** `key` 계약·안정성·`reverse`·비교 횟수는 그쪽, **그 자리에 `lambda`가 들어가는 것**은 여기 |
| [16번](../16-iterator-protocol/2-summary.md) | **이터레이터 계약의 정본.** 「한 번 흐르면 빈다」는 그쪽, 「`map`·`filter` 가 그 계약을 따른다」는 여기 |
| [22번](../22-closures-and-late-binding/2-summary.md) | **클로저의 정본.** 셀·늦은 바인딩의 이유는 그쪽, 「**`lambda`가 그 클로저를 만드는 가장 짧은 문법**」은 여기 |
| [19번](../19-function-argument-rules/2-summary.md) | 인자 규칙의 정본. 「`lambda`도 그 문법을 전부 쓴다」만 여기 |
| [21번](../21-scope-legb-global-nonlocal/2-summary.md) | **캐럿 없는 `SyntaxError` 의 정본.** 여기는 **캐럿이 나오는 쪽**의 대조군 |
| [20번](../20-mutable-default-args/2-summary.md) | `lambda i=i:` 고침이 기대는 **기본값 평가 시점**의 정본 |
| [14번](../14-comprehensions/2-summary.md) | `map`·`filter` 대신 쓰는 자리의 정본 |
| [24번](../24-decorators/2-summary.md) | **함수를 받아 함수를 돌려주는** 것의 문법 설탕은 그쪽 |
| [목록의 **45번 주제**](../45-functools/) | `partial`·`reduce`·`lru_cache` 의 정본 |

## 실행 검증

이 문서와 [2-summary.md](2-summary.md)에 실린 출력은 전부 아래처럼 돌려서 얻었다.

| 무엇을 | 어떻게 | 몇 번 | 어디에 |
|---|---|---|---|
| 버전·구현·플랫폼 확인 | `python3 - <v_version.py` · 3.12.3 | 1회 | 2-summary 머리말 |
| 몸통에 문장·애너테이션 5종 | `python3 - <ex.py` — **각각 따로** | 5회 | 1번 답 |
| `lambda` 안의 `:=` 2종 | 〃 | 1회(한 파일) | 2번 답 |
| 괄호 안 여러 줄 | 〃 | 1회 | 3번 답 |
| `__name__`·`__qualname__`·타입 | 〃 | 1회 | 4번 답 |
| 두 `lambda` 의 트레이스백 | 〃 | 1회 | 5번 답 |
| `co_code` 대조 + `dis` 두 벌 | 〃 | 1회 | 6번 답 |
| `key` 대 `cmp_to_key` 호출 횟수 | 〃 | 1회 | 7번 답 |
| `map`·`filter` 를 두 번 비우기 | 〃 | 1회 | 8번 답 |
| 루프 클로저 + `i=i` 고침 | 〃 | 1회 | 9번 답 |
| `lambda` 를 놓을 자리 8종 | 〃 | 1회(한 파일) | 10번 답 |
| `signature`·`__defaults__` | 〃 | 1회 | 11번 답 |
| `cmp_to_key` 의 타입 이름·같은 결과 | 〃 | 1회 | 2-summary 동작 12 |
| `sorted(key=)` 6종 | 〃 | 1회 | 2-summary 동작 10 |
| `reduce` 와 누적 순서 | 〃 | 1회 | 2-summary 동작 13 |

**구현 의존 항목 — 버전이 오르면 다시 돌려야 할 것**

- **`SyntaxError` 문구와 캐럿 폭**(1번 답) — 종류는 명세, 문구·폭은 아니다.
  **캐럿이 나온다는 사실**만 근거로 쓴다.
- **`dis` 출력 전부**(6번 답) — 명령 이름·오프셋은 컴파일러가 정한다. `RESUME`·`BINARY_OP` 는 3.11+ 의 이름이다.
- **`co_flags` = `3`**(6번 답) — 다른 비트가 섞일 수 있다.
- **`cmp` 호출 16회**(7번 답) — **데이터와 정렬 구현에 달렸다.** `key` 8회만 문서가 정한다.
- **`key` 가 받은 순서**(7번 답) — 문서는 **횟수만** 약속한다.
- **`KeyWrapper` 라는 타입 이름**(2-summary 동작 12) — CPython `functools` 의 구현 이름이다.
- **`__closure__`·셀 객체의 겉모습**(9번 답) — CPython 의 내성 인터페이스다.
- **함수 `repr` 의 주소**(4번 답) — 실행마다 바뀐다. 대조할 것은 **`<function <lambda>` 라는 앞머리**다.

★ **이 문서에 없는 것 — 시간 측정.** `timeit` 을 한 번도 안 돌렸으므로
**`lambda`와 `def`의 속도 비교는 이 노트의 근거로 쓸 수 없다.**
