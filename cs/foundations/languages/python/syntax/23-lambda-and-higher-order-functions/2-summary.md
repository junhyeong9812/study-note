# python/syntax/23-lambda-and-higher-order-functions — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만.
> - [6.14. Lambdas](https://docs.python.org/3.12/reference/expressions.html#lambda) — `lambda` 가 무엇을 만들고 **무엇을 담을 수 없는가**
> - [8.7. Function definitions](https://docs.python.org/3.12/reference/compound_stmts.html#function-definitions) — 파라미터 문법은 `def`와 공유한다
> - [`map`](https://docs.python.org/3.12/library/functions.html#map) · [`filter`](https://docs.python.org/3.12/library/functions.html#filter) · [`sorted`](https://docs.python.org/3.12/library/functions.html#sorted)
> - [`functools.partial`](https://docs.python.org/3.12/library/functools.html#functools.partial) · [`functools.cmp_to_key`](https://docs.python.org/3.12/library/functools.html#functools.cmp_to_key) · [`functools.reduce`](https://docs.python.org/3.12/library/functools.html#functools.reduce)
> - [`inspect.signature`](https://docs.python.org/3.12/library/inspect.html#inspect.signature)
> - [Sorting HOW TO](https://docs.python.org/3.12/howto/sorting.html) · [The standard type hierarchy](https://docs.python.org/3.12/reference/datamodel.html#the-standard-type-hierarchy) — 함수 객체의 `__name__`·`__qualname__`·`__closure__`
>
> **실행 검증** — 이 문서에 실린 출력은 전부 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.\
> ★ **던지는 형태를 하나로 고정했다** — `python3 - <파일` 로 던져 트레이스백이 `File "<stdin>", line N` 이 된다.\
> ★★ **이 주제의 `SyntaxError` 다섯 판은 전부 캐럿이 나온다** — 파서가 잡기 때문이다.
> [21번](../21-scope-legb-global-nonlocal/2-summary.md)의 `nonlocal` 오류들은 **캐럿도 소스 줄도 없다**(심볼 테이블 단계가 잡는다).
> 같은 `SyntaxError` 인데 **어느 단계가 잡았는지가 화면에 드러난다.**\
> **버전** — `lambda` 자체는 Python 3 전체 공통이다. 몸통에 쓰는 `:=` 는 **3.8+**(PEP 572),
> 파라미터의 위치 전용 `/` 는 **3.8+**(PEP 570). 이 노트 범위(3.10\~3.13)에서 `lambda` 문법은 안 바뀌었다.\
> **★ 구현 대 언어 보장 한 줄** — 「`lambda`가 만드는 것은 `def`로 만든 함수 객체처럼 동작한다」는 **문서가 말하는 것**이고,
> 「**바이트코드가 한 바이트도 같다**」는 **CPython 을 들여다본 관찰**이다. 둘을 같은 문장으로 적으면 틀린다.\
> **★ 흔들리는 칸 / 안 흔들리는 칸** — 재대조에서 「고칠 것」과 「설계상 안 맞는 것」을 기계적으로 가르려고 미리 선언한다.
>
> | 흔들린다 | 안 흔들린다(근거로 써도 되는 칸) |
> |---|---|
> | `<function … at 0x…>` 의 **주소**, `id()` 값 | 예외 **타입**, `File "<stdin>", line N`, `(exit N)` |
> | (판이 오르면) `SyntaxError` **문구**와 **캐럿 폭** | **캐럿이 나온다는 사실**(이 다섯은 파서가 잡는다) |
> | (판이 오르면) `dis` 의 **오프셋·명령 이름**, `co_flags` 값 | `co_code` 가 **같다**는 판정, `co_name` 이 **다르다**는 판정 |
> | (판이 오르면) `cmp_to_key` 가 만드는 **타입 이름** | `key` 호출 **8회**(원소당 한 번 — 문서가 정한다) |
> | (데이터가 바뀌면) `cmp` 호출 **16회** | `cmp` 쪽이 **원소 수보다 많이** 불린다는 사실 |
>
> ★ **이 주제의 실행 출력은 주소를 하나도 안 찍는다** — 같은 판에서 다시 돌리면 한 글자도 안 변한다.\
> **선행** — [19번](../19-function-argument-rules/2-summary.md)(인자 규칙) ·
> [21번](../21-scope-legb-global-nonlocal/2-summary.md)(이름 해소) · [22번](../22-closures-and-late-binding/2-summary.md)(클로저).\
> **정본 이웃** — [10번](../10-list-methods-and-sort-key/2-summary.md)이 **정렬 `key`의 정본**이고,
> [16번](../16-iterator-protocol/2-summary.md)이 **이터레이터 계약의 정본**이다. 여기서는 **`lambda`가 그 자리에 들어가는 것**만 다룬다.\
> **후행** — [24번](../24-decorators/2-summary.md)(데코레이터).

```python
# v_version.py
import sys

print("version_info =", sys.version_info)
print("implementation =", sys.implementation.name)
print("platform =", sys.platform)
```

```text
===== python3 - <v_version.py =====
version_info = sys.version_info(major=3, minor=12, micro=3, releaselevel='final', serial=0)
implementation = cpython
platform = linux
(exit 0)
```

## 한눈에 — 쉽게 말하면

**`lambda`의 제약은 「짧아야 한다」가 아니라 「식(expression)이어야 한다」다.**

서식의 빈칸을 생각하면 된다.\
빈칸에는 **값이 되는 말**만 적을 수 있다 — 「3 더하기 4」는 적히지만 「이것을 창고에 넣으시오」는 못 적는다.\
`lambda`의 콜론 뒤가 바로 그 빈칸이다.

```text
   def 로 만든 함수 몸통            lambda 의 콜론 뒤
   ┌──────────────────────┐        ┌──────────────────────┐
   │ 문장을 몇 줄이든      │        │ 식 하나              │
   │   x = x + 1          │        │   x + 1              │
   │   if ...: ...        │        │   (a if c else b)    │
   │   return x           │        │   [f(i) for i in xs] │
   │   raise ValueError   │        │   (y := n * n) + y   │  <- := 는 식이다
   └──────────────────────┘        └──────────────────────┘
        시키는 말도 된다                  값이 되는 말만
```

★ **그래서 짧음은 결과이지 규칙이 아니다.** 식 하나로는 길게 쓰기가 어려울 뿐이다.

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 서식의 빈칸 | `lambda`의 콜론 뒤 | 문장을 넣으면 `SyntaxError`(동작 1) |
| 「값이 되는 말」 | 식(expression) | `:=`는 되고 `=`는 안 된다(동작 2) |
| 빈칸을 채워 만든 **도구** | 함수 객체 | `type()`이 `def`로 만든 것과 같다(동작 3) |
| 도구에 이름표가 없다 | `__name__`이 `<lambda>` | 트레이스백에서 구분이 안 된다(동작 4) |
| 속은 같은 도구 | 코드 객체 | `co_code`가 같고 `co_name`만 다르다(동작 5) |
| 도구를 남에게 건네준다 | 고차 함수 | `map`·`filter`·`sorted(key=)`(동작 8) |
| 도구가 바깥 상자를 들고 다닌다 | 클로저 | `__closure__`에 셀이 잡힌다(동작 7) |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.\
「**정렬 기준 한 줄을 넘기려고 `lambda`를 쓰는 것**」과 「**`lambda`를 이름에 묶어 두고 트레이스백에서 못 찾는 것**」이 그것이다.
앞엣것이 `lambda`의 제자리이고, 뒤엣것은 `def`로 써야 할 자리다(동작 4).

> **식(expression)** — 계산하면 **값이 남는** 말.\
> 예: `x + 1`·`f(3)`·`[i for i in xs]`·`a if c else b`. `lambda` 자신도 식이다.

> **문장(statement)** — 무언가를 **시키는** 말. 값이 남지 않는다.\
> 예: `x = 1`·`return x`·`pass`·`raise ValueError("no")`·`x: int`(애너테이션).

> **고차 함수(higher-order function)** — 함수를 **인자로 받거나 함수를 돌려주는** 함수.\
> 예: `sorted(xs, key=len)`의 `sorted`, `map(f, xs)`의 `map`.

## 이 주제가 답하려는 질문

1. **무엇을 못 담나** — `lambda` 몸통에 넣을 수 없는 것이 무엇이고, 그 경계가 정확히 어디인가(`:=`는 되는데 `=`는 안 되는 이유).
2. **`def`와 무엇이 다른가** — 만들어지는 물건이 다른가, 이름만 다른가. 그 차이가 어디서 드러나는가.
3. **어디에 끼워 넣나** — `map`·`filter`·`sorted(key=)`·`reduce`의 자리에 `lambda`가 들어갈 때 무엇이 달라지는가.

## 동작 방식

> 이 절이 본문이다. 이 주제의 네 번째 창은 **코드 객체**다 —
> `__code__.co_code`·`co_name`·`__name__`·`__qualname__`·`__closure__`.
> **무엇이 안 되는지는 던져서**, **왜 같은지는 코드 객체로** 본다.

### 1. ★★ 다섯 판 — 문장을 넣으면 전부 `SyntaxError` 인데 문구가 갈린다

**언제 쓰나** — 「`lambda`는 왜 한 줄만 되나」를 물을 때. 답은 「한 줄」이 아니라 「**한 식**」이다.

공식 문서가 직접 말한다.

> *"Note that functions created with lambda expressions cannot contain statements or annotations."*

**statements or annotations** — 두 가지를 말한다. 다섯 판을 **따로따로** 던졌다.

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

★★ **다섯 전부 `SyntaxError` 인데 문구는 둘로 갈린다.**

```text
   lambda 몸통에 넣은 것        문구                            캐럿
   ────────────────────────    ────────────────────────────    ──────────────
   x = x + 1  (대입문)          cannot assign to lambda         lambda 식 전체
   return x                    invalid syntax                  return 낱말
   pass                        invalid syntax                  pass 낱말
   raise ValueError("no")      invalid syntax                  raise 낱말
   x: int  (애너테이션)         invalid syntax                  콜론 한 칸
```

그림 해설.

- ★ **대입문만 다른 문구가 나온다.** `f = lambda x: x = x + 1` 을 파서가 읽으면
  `f = (lambda x: x)` 까지가 한 식이고 그 뒤에 `= x + 1` 이 오므로 **왼쪽이 `lambda` 식인 대입으로** 읽힌다.
  그래서 「이 자리에 `lambda`를 못 넣는다」가 아니라 **`lambda`에 대입할 수 없다는 말**이 나온다.
  캐럿이 `lambda x: x` **전체**를 덮는 것이 그 증거다.
- **나머지 넷은 그냥 「말이 안 된다」다.** `return`·`pass`·`raise`는 **식이 시작될 수 없는 낱말**이라
  파서가 그 낱말 앞에서 멈춘다. 캐럿이 그 낱말에 정확히 붙는다.
- ★ **애너테이션 판의 캐럿은 한 칸짜리다.** `lambda x: int: x` 에서 앞쪽 콜론까지는 멀쩡한 `lambda`라
  **두 번째 콜론**에서 처음 어긋난다. 문서가 말한 **"or annotations"** 쪽의 실증이 이것이다.

★★ **다섯 전부 캐럿이 나온다 — 파서가 잡았다는 뜻이다.**
[21번](../21-scope-legb-global-nonlocal/2-summary.md)의 `no binding for nonlocal 'x' found` 는
**소스 줄도 캐럿도 없다** — 파싱을 끝낸 뒤 **심볼 테이블 단계**가 잡기 때문이다.
**같은 `SyntaxError` 인데 어느 단계가 잡았는지가 화면에 드러난다.**

**비용** — 다섯 전부 **프로그램이 시작조차 안 한다.** 런타임 비용은 0이고, 대신 **정적으로 100% 잡힌다.**

### 2. ★★ 경계는 여기다 — `:=` 는 되고 `=` 는 안 된다

**언제 쓰나** — 「문장 금지」가 정확히 무엇을 금지하는지 그어야 할 때.

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

★★ **같은 「값을 이름에 붙이는 일」인데 한쪽만 된다.**

```text
   x = x + 1        대입"문"      ->  문장이다        ->  lambda 몸통에 못 넣는다
   (x := x + 1)     대입"식"      ->  값이 남는다      ->  lambda 몸통에 들어간다
                    ^^^^^^^^^^        (x + 1 이 남는다)
```

- ★ **`:=` 는 값을 남긴다.** `(sq := n * n) + sq` 에서 `(sq := n * n)` 자체가 `n * n` 이라는 값이고,
  이름 `sq`에도 붙는다. **값이 남으므로 식**이고, 식이므로 `lambda` 안에 들어간다.
- **`=` 는 값을 안 남긴다.** `x = 1` 을 다른 식의 일부로 쓸 수 없는 이유가 그것이다.
- ★ 그래서 「`lambda`는 상태를 못 바꾼다」는 **틀린 요약**이다. `:=`로 바꿀 수 있고,
  `lst.append(x)` 같은 **부작용 있는 호출**은 언제나 식이었다.

**괄호 안이면 여러 줄도 된다** — 「한 줄」이 규칙이 아니라는 두 번째 증거다.

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

★ **줄바꿈이 세 번 있는데 멀쩡히 돈다.** 괄호 안에서는 줄바꿈이 **문장 끝**이 아니기 때문이다.
`lambda`가 요구하는 것은 **한 줄이 아니라 한 식**이다.

**비용** — 이 자유를 쓰면 읽기가 급격히 나빠진다.\
`(print(...), x * 2)[1]` 처럼 **튜플을 만들어 마지막 것만 꺼내는** 꼴은 `def` 두 줄로 쓰면 될 것을 비틀어 놓은 것이다.

### 3. `lambda` 가 만드는 것은 그냥 함수 객체다

**언제 쓰나** — 「`lambda`는 함수가 아니라 무언가 다른 것」이라는 오해를 떼어낼 때.

문서가 말하는 것은 이것이다.

> *"The unnamed object behaves like a function object defined with `def <lambda>(parameters): return expression`"*

★ **`def <lambda>(...)` — 문서가 직접 그 이름을 적어 놓았다.** 실제로 그렇게 나온다.

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

```text
   f = lambda n: n * n

   소스의 lambda 식
        │
        │  컴파일 — 코드 객체를 하나 만든다 (co_name = "<lambda>")
        ▼
   ┌──────────────────────────────┐
   │ 함수 객체                     │
   │  __name__      = "<lambda>"  │  <- 이름표가 비어 있다
   │  __qualname__  = "<lambda>"  │
   │  __doc__       = None        │  <- 독스트링을 담을 자리가 없다
   │  type          = function    │  <- def 로 만든 것과 같은 타입
   └──────────────────────────────┘
        │
        │  f = ...   (이건 lambda 의 일이 아니라 대입문의 일이다)
        ▼
   이름 f 가 그 객체를 가리킨다
```

그림 해설.

- **타입이 같다.** `type(square) is type(square_def)` 가 `True` 다 — **다른 종류의 물건이 아니다.**
- ★ **`__name__` 만 다르다.** `def`로 만들면 `__name__` 에 그 이름이 들어가는데,
  `lambda`는 이름 없이 만들어지므로 `<lambda>` 라는 **자리표시자**가 들어간다.
  `f = lambda ...` 로 이름에 묶어도 **`__name__` 은 안 바뀐다** — 대입은 함수 객체를 안 건드린다.
- ★ **`__doc__` 이 `None` 이다.** 몸통이 식 하나라 **독스트링을 둘 자리가 없다.**
- ★ **함수 안에서 만들면 `__qualname__` 에 자취가 남는다** — `make.<locals>.<lambda>`.
  **어느 함수 안에서 만들어졌는지**까지는 알 수 있고, **그 함수 안의 몇 번째인지는 모른다.**

**비용** — 이름표가 없어 **에러가 났을 때 찾는 비용**이 오른다. 다음 절이 그것이다.

### 4. ★ 그래서 트레이스백이 모호해진다 — 실측 근거

**언제 쓰나** — 「`lambda`를 이름에 묶지 마라」의 **이유**를 대야 할 때.

같은 줄에 `lambda`를 **둘** 놓고 **뒤엣것**만 터뜨렸다.

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

★★ **`in <lambda>` 라고만 나온다 — 둘 중 어느 것인지 알 수 없다.**

```text
   fns = [lambda: 1 / 0, lambda: 1 / 0]
          ^^^^^^^^^^^^^  ^^^^^^^^^^^^^
            첫째             둘째  <- 터진 것은 이쪽

   트레이스백이 말해 주는 것
   ┌────────────────────────────────────┐
   │ File "<stdin>", line 5, in <lambda> │   줄 번호는 5
   └────────────────────────────────────┘        둘 다 5 번 줄에 있다
                       │
                       └─> 이름도 <lambda>, 줄도 같다 -> 구분 불가

   def 로 썼다면
   ┌────────────────────────────────────┐
   │ File "<stdin>", line 5, in divide_b │  <- 이름이 답한다
   └────────────────────────────────────┘
```

- ★ **이것이 「이름에 묶을 거면 `def`를 써라」의 실측 근거다.** 「스타일이 나쁘다」가 아니라
  **디버깅할 때 정보가 실제로 없다**는 것이 근거다.
- ★★ **성능을 근거로 대지 마라 — 이 문서는 `timeit` 을 안 돌렸다.** 둘의 코드 객체가 같다는 것만 봤다(동작 5).
  「`lambda`가 느리다」도 「빠르다」도 이 노트의 근거로는 **못 쓴다.**
- 반대로 **한 번 쓰고 버리는 자리**(정렬 `key` 인자·`map`의 첫 인자)에서는 이 비용이 안 생긴다.
  거기서 터지면 **호출한 쪽 줄**이 트레이스백에 남기 때문이다.

**비용** — `lambda` 하나를 이름에 묶어 아끼는 것은 `def` 한 줄이고, 잃는 것은 **트레이스백의 이름 한 칸**이다.

### 5. ★★ `lambda` 와 `def` 는 바이트코드가 같다 — 줄 표만 다르다

**언제 쓰나** — 「둘이 정말 같은가」를 끝까지 확인할 때.

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

★★ **`co_code` 가 `True` 다 — 바이트열이 한 바이트도 같다.**

```text
   add_lambda = lambda a, b: a + b        def add_def(a, b):
                                              return a + b
   ┌─────────────────────────┐            ┌─────────────────────────┐
   │ co_code    : 같다        │  <──────>  │ co_code    : 같다        │
   │ co_consts  : (None,)    │            │ co_consts  : (None,)    │
   │ co_varnames: ('a','b')  │            │ co_varnames: ('a','b')  │
   │ co_flags   : 3          │            │ co_flags   : 3          │
   │ co_name    : <lambda>   │  <- 여기만 ->│ co_name    : add_def    │
   └─────────────────────────┘            └─────────────────────────┘
```

★ **그런데 `dis` 출력의 줄 표는 다르다.**

```text
   dis.dis(add_lambda)              dis.dis(add_def)
   ───────────────────────          ───────────────────────
     3   0 RESUME                     6   0 RESUME          <- 줄 6 (def 줄)
         2 LOAD_FAST  a                   (빈 줄)
         4 LOAD_FAST  b               7   2 LOAD_FAST  a    <- 줄 7 (return 줄)
         6 BINARY_OP  +                   4 LOAD_FAST  b
        10 RETURN_VALUE                   6 BINARY_OP  +
                                         10 RETURN_VALUE
   한 줄짜리라 안 갈린다              두 줄이라 갈린다
```

- ★ **명령·오프셋은 다섯 개 전부 같고, 왼쪽의 줄 번호 칸만 갈린다.** `def`는 헤더 줄과 `return` 줄이
  **소스에서 다른 줄**이라 `RESUME` 과 몸통이 갈리고, `lambda`는 **전부 한 줄**이라 안 갈린다.
- ★★ **이것은 CPython 구현이지 언어 보장이 아니다.** 언어 쪽 보장은 문서의
  「`def <lambda>(parameters): return expression` 로 정의한 함수 객체처럼 **동작한다**」이지
  「**같은 바이트코드를 낸다**」가 아니다. 다른 파이썬 구현은 바이트코드 자체가 없을 수도 있다.
- ★ **`co_flags` 가 `3` 인 것**(`CO_OPTIMIZED | CO_NEWLOCALS`)도 둘이 같다 — [19번](../19-function-argument-rules/2-summary.md)에서 본 그 플래그다.

**비용** — 없다. **고를 이유가 성능이 아니라 「이름이 필요한가」라는 뜻**이다.

### 6. `lambda` 를 쓸 수 있는 자리 — 여덟 군데

**언제 쓰나** — 「어디에 넣을 수 있나」를 지도로 잡을 때. **`lambda`는 식이므로 식이 들어가는 자리엔 전부 들어간다.**

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

| 자리 | 꼴 | 쓸모 |
|---|---|---|
| **dict 값** | `{"+": lambda a, b: a + b}` | ★ 분기표(dispatch table) — `if/elif` 사다리를 없앤다 |
| **다른 함수의 인자** | `apply(lambda a, b: a * b, 3, 4)` | ★ 가장 흔한 제자리. `map`·`filter`·`sorted(key=)`가 전부 이것이다 |
| **클래스 몸통** | `fmt = staticmethod(lambda n: ...)` | 작은 포맷터. [21번](../21-scope-legb-global-nonlocal/2-summary.md)의 클래스 스코프 규칙이 그대로 걸린다 |
| **기본값** | `def f(cb=lambda: ...)` | 「아무것도 안 하는 콜백」의 기본값 |
| **즉시 호출** | `(lambda n: n + 1)(41)` | 괄호로 싸서 그 자리에서 부른다 |
| **반환값** | `return lambda: ...` | ★ 여기서 **클로저**가 생긴다(동작 7) |
| **`partial` 과 함께** | `functools.partial(lambda a, b: a - b, 10)` | 인자를 미리 고정한 새 호출 가능 객체 |
| **데코레이터가 할 일** | `(lambda fn: lambda: fn() * 2)(...)` | ★ **[24번](../24-decorators/2-summary.md)의 골격을 손으로 편 것** |

- ★ **마지막 칸은 「`@` 뒤에 `lambda`를 쓴다」는 뜻이 아니다.** 데코레이터가 하는 일
  (**함수를 받아 함수를 돌려준다**)을 `lambda` 두 겹으로 편 것이고, `@` 문법에 직접 쓰는 것은 **이 문서에서 안 던져 봤다.**
- ★ **「반환값으로」 칸의 `(lambda: (lambda: "두 겹"))()()` 는 괄호가 둘인 것이 요점이다** —
  바깥을 부르면 **안쪽 `lambda`가 값으로 나오고**, 한 번 더 불러야 문자열이 나온다.

**비용** — 여덟 자리 전부 **식 자리**다. 문장 자리(`if`의 몸통·`for`의 몸통)에는 못 들어간다.

### 7. ★ `lambda` 는 [22번](../22-closures-and-late-binding/2-summary.md)의 클로저를 만드는 **가장 짧은 문법**이다

**언제 쓰나** — 루프 안에서 `lambda`를 만들었는데 전부 같은 값을 낼 때.

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

★★ **`lambda`라고 다르지 않다 — [22번](../22-closures-and-late-binding/2-summary.md)과 같은 결과다.**

```text
   bad = [lambda: i for i in range(3)]

   컴프리헨션의 i  ┌──── 셀(cell) 하나 ────┐
                  │        i = 2         │   <- 루프가 끝난 뒤의 값
                  └──────────┬───────────┘
                     ▲       ▲       ▲
                     │       │       │        셋 다 같은 셀을 본다
                  lambda  lambda  lambda      -> [2, 2, 2]

   good = [lambda i=i: i for i in range(3)]

                  ┌──────┐ ┌──────┐ ┌──────┐
                  │ i=0  │ │ i=1  │ │ i=2  │   <- 기본값은 만들 때 한 번 굳는다
                  └──────┘ └──────┘ └──────┘   -> [0, 1, 2]
                  __closure__ 가 None 이다      <- 자유 변수가 아예 없다
```

- ★ **대조할 것은 주소가 아니라 「셀이 하나」라는 것이다** — 실측에서
  `bad[0].__closure__[0] is bad[2].__closure__[0]` 가 `True` 였다.
- ★★ **고친 쪽은 `__closure__` 가 `None` 이다.** 클로저를 「고친」 것이 아니라 **클로저를 안 만든 것**이다.
  `i`가 파라미터가 되어 **자유 변수이기를 그만두었다**(`__defaults__` 에 `(0,)`·`(1,)`·`(2,)` 가 들어간다).
- **왜 정본이 22번인가** — 늦은 바인딩은 `def`로 만든 중첩 함수에서도 똑같이 난다.
  **`lambda`의 성질이 아니라 클로저의 성질**이다. 여기서 말할 것은 「`lambda`라고 예외가 아니다」 한 줄뿐이다.
- ★ **기본값이 정의 시점에 한 번 굳는 것**의 정본은 [20번](../20-mutable-default-args/2-summary.md)이다.

**비용** — 셀 하나를 공유하므로 메모리는 싸고, **의미가 틀리기 쉽다.**

### 8. `lambda` 도 [19번](../19-function-argument-rules/2-summary.md)의 인자 문법을 전부 쓴다

**언제 쓰나** — 「`lambda`는 간단한 인자만 받는다」는 오해를 뗄 때.

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

★ **기본값·`*args`·키워드 전용·위치 전용이 전부 된다.** `def`와 **같은 파라미터 문법**을 쓴다.

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

- **괄호가 없다는 것만 다르다.** `def f(a, b=1)` 의 소괄호가 `lambda a, b=1` 에는 없다.
- ★ **`__defaults__`·`__kwdefaults__` 도 `def`와 같은 모양으로 붙는다** — 실측에서 `(1,)`·`None` 이었다.
- ★ **`inspect.signature` 가 그대로 읽는다** — 시그니처 층에서 보면 **`def`인지 `lambda`인지 구분할 정보가 없다.**

**비용** — 문법은 되지만, **인자가 복잡해질수록 `lambda`로 쓸 이유가 사라진다.** 그 시점이 `def`로 옮길 때다.

### 9. 고차 함수 — `map`·`filter` 는 이터레이터다

**언제 쓰나** — `map`의 결과를 두 번 쓰려 할 때.

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

★★ **두 번째로 `list()` 를 걸면 빈 리스트가 나온다.**

```text
   nums = [1, 2, 3, 4, 5]
        │
        ├─ map(lambda n: n*n, nums) ──> ┌ map 객체 ┐
        │                               └────┬─────┘   아직 아무것도 계산 안 했다
        │                                    │
        │  list(m)  ─ 한 번 흘려보낸다 ──────> [1, 4, 9, 16, 25]
        │                                    │
        │                               ┌────┴─────┐
        │                               │ 다 비었다 │
        │                               └────┬─────┘
        │  list(m)  ─ 다시 부르면 ──────────> []
```

- ★ **`iter(m) is m` 이 `True` 다** — 이터레이터의 정의 그대로다. **정본은 [16번](../16-iterator-protocol/2-summary.md)이다.**
  **경계**: 「이터레이터가 한 번 쓰고 비는 것」은 16번, 여기서는 **`lambda`가 `map`의 첫 인자로 들어간다**는 것까지다.
- ★ **컴프리헨션으로 같은 결과가 나온다** — `[n * n for n in nums]` 와 `[n for n in nums if n % 2]`.
  **정본은 [14번](../14-comprehensions/2-summary.md)이고**, 실무 판단은 「언제 쓰고 언제 안 쓰나」 절에 적었다.
- **`filter` 의 판정은 참/거짓 판정**이다 — `n % 2` 가 `0`이면 버린다([05번](../05-truthiness-and-short-circuit/2-summary.md)).

**비용** — 지연되므로 **안 쓰면 계산도 안 한다.** 대신 **두 번 못 쓴다** — 두 번 쓸 것이면 `list()` 로 굳힌다.

### 10. 고차 함수 — 정렬 `key` 의 자리

**언제 쓰나** — 「무엇을 기준으로 정렬하나」를 넘길 때.

```python
# e23_sorted_key.py
people = [("김", 30, 170), ("이", 25, 180), ("박", 30, 165), ("최", 25, 175)]

print("원본        :", [p[0] for p in people])
print("나이만      :", [p[0] for p in sorted(people, key=lambda p: p[1])])
print("나이↑ 키↑   :", [p[0] for p in sorted(people, key=lambda p: (p[1], p[2]))])
print("나이↑ 키↓   :", [p[0] for p in sorted(people, key=lambda p: (p[1], -p[2]))])
print("reverse=True:", [p[0] for p in sorted(people, key=lambda p: p[1], reverse=True)])
print("이름 길이   :", sorted(["bb", "a", "ccc", "dd"], key=len))
```

```text
===== python3 - <e23_sorted_key.py =====
원본        : ['김', '이', '박', '최']
나이만      : ['이', '최', '김', '박']
나이↑ 키↑   : ['최', '이', '박', '김']
나이↑ 키↓   : ['이', '최', '김', '박']
reverse=True: ['김', '박', '이', '최']
이름 길이   : ['a', 'bb', 'dd', 'ccc']
(exit 0)
```

★ **정렬 규칙 자체의 정본은 [10번](../10-list-methods-and-sort-key/2-summary.md)이다.**
**경계**: 「`key`가 원소당 한 번 계산된다는 계약·안정 정렬·`reverse`의 의미」는 전부 그쪽이고,
여기서는 **그 `key` 자리에 `lambda`가 들어간다**는 것과 **그 `lambda`를 어떻게 짜느냐**만 본다.

```text
   people = [("김",30,170), ("이",25,180), ("박",30,165), ("최",25,175)]

   key=lambda p: p[1]            나이만        -> 이 최 김 박   (동점은 원본 순서 = 안정)
   key=lambda p: (p[1], p[2])    나이↑ 키↑     -> 최 이 박 김
   key=lambda p: (p[1], -p[2])   나이↑ 키↓     -> 이 최 김 박   <- 부호를 뒤집어 한 축만 역순
   key=lambda p: p[1], reverse=True            -> 김 박 이 최   <- 전체가 뒤집힌다
   key=len                        (lambda 가 필요 없는 자리)
```

- ★★ **`-p[2]` 와 `reverse=True` 는 다른 것이다.** 앞엣것은 **두 번째 축만** 뒤집고,
  뒤엣것은 **정렬 결과 전체**를 뒤집는다. 실측에서 두 줄의 결과가 달랐다.
- ★ **`key=len` 은 `lambda`를 쓸 자리가 아니다** — `lambda s: len(s)` 는 **`len` 을 한 겹 싸기만 한 것**이다.
  `str.lower`·`operator.itemgetter(1)` 도 같다.
- **부호 뒤집기는 숫자에서만 된다.** 문자열은 `-` 가 없어 튜플 키로 못 뒤집는다 — 그때가 `cmp_to_key` 자리다(동작 11).

**비용** — `key` 는 원소당 한 번이라 **비싼 계산일수록 유리하다**. 다음 절이 그 수치다.

### 11. ★ `key=` 와 `cmp_to_key` — 호출 횟수가 이렇게 나왔다

**언제 쓰나** — 두 원소를 **같이 봐야** 순서가 정해질 때.

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

★★ **원소 8개에 `key` 는 8번, `cmp` 는 16번 불렸다.**

```text
   data = [5, 3, 8, 1, 9, 2, 7, 4]   (원소 8개)

   key= 로 주면                          cmp_to_key(cmp) 로 주면
   ┌──────────────────────────┐          ┌──────────────────────────┐
   │ 5 -> key(5)              │          │ 정렬이 두 원소를 볼 때마다 │
   │ 3 -> key(3)              │          │   cmp(a, b) 를 부른다     │
   │ 8 -> key(8)              │          │                          │
   │ ... 원소당 한 번, 8번     │          │ 이 데이터에서 16번        │
   └──────────────────────────┘          └──────────────────────────┘
        문서가 정한 횟수                       데이터·구현에 달린 관찰
```

- ★★ **「더 빠르다」고 적지 마라 — 이 문서는 시간을 안 쟀다.** 적을 수 있는 것은
  「**호출 횟수가 8 대 16으로 나왔다**」와 「**`key` 는 원소당 한 번이라고 문서가 정한다**」 둘뿐이다.
- ★ **8은 보장이고 16은 관찰이다.** `key` 호출 횟수는 [Sorting HOW TO](https://docs.python.org/3.12/howto/sorting.html)와
  `list.sort` 문서가 정하고, `cmp` 호출 횟수는 **정렬 알고리즘과 데이터 배열**에 달렸다 — 다른 데이터면 다른 수가 나온다.
- **`key` 가 받은 순서는 원본 순서**였다(`[5, 3, 8, 1, 9, 2, 7, 4]`). ★ **그 순서는 문서가 약속하지 않는다** — [10번](../10-list-methods-and-sort-key/2-summary.md)의 실측과 같다.

**비용** — `key` 는 계산 결과 n 개를 **메모리에 들고** 있고, `cmp` 는 메모리를 덜 쓰는 대신 **비교마다 파이썬 함수를 부른다.**

### 12. `cmp_to_key` — 두 원소를 봐야 정해지는 순서

**언제 쓰나** — 「한 원소에서 뽑을 수 있는 이름표」로 표현이 안 되는 순서일 때.

```python
# e23_cmp_to_key.py
from functools import cmp_to_key

words = ["bb", "a", "ccc", "dd"]


def by_len_then_rev(x, y):
    if len(x) != len(y):
        return len(x) - len(y)
    if x < y:
        return 1
    if x > y:
        return -1
    return 0


k = cmp_to_key(by_len_then_rev)
print("cmp_to_key 가 만든 것:", type(k).__name__)
print("한 원소를 감싸면    :", type(k("a")).__name__)
print("정렬 결과           :", sorted(words, key=k))
print("같은 것을 key 로     :", sorted(words, key=lambda w: (len(w), [-ord(c) for c in w])))
```

```text
===== python3 - <e23_cmp_to_key.py =====
cmp_to_key 가 만든 것: KeyWrapper
한 원소를 감싸면    : KeyWrapper
정렬 결과           : ['a', 'dd', 'bb', 'ccc']
같은 것을 key 로     : ['a', 'dd', 'bb', 'ccc']
(exit 0)
```

```text
   cmp_to_key(by_len_then_rev)
        │
        ▼
   ┌──────────────────────────────────────────┐
   │ KeyWrapper 라는 타입                      │   <- CPython 구현의 이름이다
   │   원소 하나를 감싸면 KeyWrapper 가 되고    │
   │   그것끼리 < 를 하면 cmp(a, b) 가 불린다   │
   └──────────────────────────────────────────┘
        │
        ▼
   sorted 는 평소처럼 < 만 쓴다
```

- ★ **`KeyWrapper` 라는 이름은 CPython 구현 세부사항이다.** `functools` 는 순수 파이썬 대체 구현이 있고,
  그쪽에서는 **다른 이름**이 나온다. 이름에 기대어 테스트를 쓰면 안 된다.
- ★★ **같은 결과를 `key` 로도 낼 수 있었다** — `lambda w: (len(w), [-ord(c) for c in w])`.
  둘의 출력이 같았다(`['a', 'dd', 'bb', 'ccc']`).
  **즉 `cmp_to_key` 가 꼭 필요한 경우는 생각보다 드물다** — 대개 **키를 비트는 것**으로 풀린다.
- **`cmp` 의 계약** — 음수면 앞, 0이면 같음, 양수면 뒤. `(a > b) - (a < b)` 가 그 관용구다.

**비용** — 감싸는 객체를 원소마다 만들고 비교마다 파이썬 함수를 부른다.\
그럼에도 **두 원소를 같이 봐야만 정해지는 순서**에서는 이것이 유일한 길이다.

### 13. `reduce` — 누적이 어떤 순서로 도는가

**언제 쓰나** — 목록 하나를 값 하나로 접을 때.

```python
# e23_reduce.py
from functools import reduce

nums = [1, 2, 3, 4]
print("reduce 합       :", reduce(lambda a, b: a + b, nums))
print("초깃값을 주면   :", reduce(lambda a, b: a + b, nums, 100))
print("빈 것 + 초깃값  :", reduce(lambda a, b: a + b, [], 0))
print("sum 으로 같은 것:", sum(nums))

steps = []
reduce(lambda a, b: (steps.append((a, b)), a + b)[1], nums)
print("누적 순서:", steps)
```

```text
===== python3 - <e23_reduce.py =====
reduce 합       : 10
초깃값을 주면   : 110
빈 것 + 초깃값  : 0
sum 으로 같은 것: 10
누적 순서: [(1, 2), (3, 3), (6, 4)]
(exit 0)
```

```text
   reduce(lambda a, b: a + b, [1, 2, 3, 4])

   (1, 2) -> 3
      └──> (3, 3) -> 6
              └──> (6, 4) -> 10        <- 왼쪽부터 누적한다

   초깃값 100 을 주면   (100, 1) 부터 시작해 110
   빈 목록 + 초깃값 0   -> 0            (초깃값이 없고 빈 목록이면 TypeError 다 — 여긴 안 던졌다)
```

- ★ **실측한 누적 순서는 `[(1, 2), (3, 3), (6, 4)]` 였다** — **왼쪽부터 접는다**는 것이 그대로 보인다.
- ★ **합은 `sum` 이 답이다.** 실측에서 `reduce(lambda a, b: a + b, nums)` 와 `sum(nums)` 가 같은 `10` 을 냈다 —
  **`sum`·`max`·`min`·`any`·`all` 로 되는 것에 `reduce` 를 쓰지 않는다.**
- **`reduce` 의 정본은 [목록의 45번 주제](../45-functools/)**(`functools`)다. 여기서는 **`lambda`가 그 첫 인자로 들어간다**는 것까지다.

**비용** — 읽는 사람이 **누적 방향을 머리로 재구성**해야 한다. 그것이 `reduce` 를 아껴 쓰는 이유다.

## 문법 — 형태와 규칙

```python
lambda: 0                        # 인자 없음
lambda x: x * 2                  # 인자 하나
lambda a, b=1, *args, c, **kw: None   # def 와 같은 파라미터 문법
lambda a, /, b, *, c: None       # 위치 전용 / 도 된다 (3.8+)

f = lambda x: x + 1              # ★ 이름에 묶는 것은 lambda 의 일이 아니라 대입문의 일이다
(lambda n: n + 1)(41)            # 즉시 호출 — 괄호로 싸야 한다
sorted(xs, key=lambda p: p[1])   # ★ 제자리
map(lambda n: n * n, xs)         # 이터레이터가 나온다
lambda x: (y := x * 2) + y       # := 는 식이므로 된다
```

규칙 여섯.

1. **콜론 뒤는 식 하나다.** 문장도 애너테이션도 못 온다 — `SyntaxError`.
2. **파라미터 문법은 `def`와 같다** — 기본값·`*args`·키워드 전용·위치 전용 전부.
   다만 **괄호가 없다**(`lambda a, b:` 이지 `lambda(a, b):` 가 아니다).
3. **`lambda` 자신이 식이다** — 식이 들어가는 자리엔 어디든 들어간다(동작 6의 여덟 자리).
4. **반환은 암묵이다** — 식의 값이 곧 반환값이고, `return` 을 쓰면 `SyntaxError`.
5. **`:=` 는 되고 `=` 는 안 된다** — 앞엣것은 식, 뒤엣것은 문장이라서다.
6. **괄호 안이면 여러 줄로 써도 된다** — 「한 줄」은 규칙이 아니다.

**금지 사례 — 전부 `SyntaxError` 이고 프로그램이 시작조차 안 한다**

```python
lambda x: x = x + 1         # cannot assign to lambda      ★ 이것만 문구가 다르다
lambda x: return x          # invalid syntax
lambda: pass                # invalid syntax
lambda: raise ValueError()  # invalid syntax
lambda x: int: x            # invalid syntax               ★ 애너테이션 — 캐럿이 한 칸이다
```

★★ **다섯 전부 캐럿이 나온다 — 파서가 잡았다는 표시다.**
[21번](../21-scope-legb-global-nonlocal/2-summary.md)의 `nonlocal` 오류들은 **캐럿도 소스 줄도 없다.**

## 어디서 틀리나

### (1) 「`lambda` 는 한 줄이어야 한다」로 안다

★ **아니다 — 「한 식」이어야 한다.** 괄호 안이면 여러 줄로 써도 돌아간다(동작 2).
「한 줄」로 외우면 `:=`가 왜 되는지 설명하지 못한다.

### (2) 「`lambda` 안에서는 아무것도 못 바꾼다」로 안다

★ **`:=` 로 바꿀 수 있고**, `append` 같은 **부작용 있는 호출**은 언제나 식이었다.
금지된 것은 **문장**이지 **변경**이 아니다.

### (3) 다섯 `SyntaxError` 의 문구가 다 같을 것이라 믿는다

★ **대입만 `cannot assign to lambda` 이고 나머지 넷은 `invalid syntax` 다.**
대입 판은 파서가 **`lambda` 식 전체를 대입의 왼쪽으로 읽어서** 그렇다 — 캐럿이 `lambda x: x` 를 덮는다.

### (4) `f = lambda ...` 로 묶으면 `__name__` 이 `f` 가 될 것이라 믿는다

★ **`<lambda>` 그대로다.** 대입은 함수 객체를 **안 건드린다.**
`__qualname__` 도 같고, 함수 안이면 `make.<locals>.<lambda>` 까지만 나온다.

### (5) 트레이스백을 보면 어느 `lambda` 인지 알 것이라 믿는다

★★ **모른다.** 한 줄에 둘을 놓고 실측했더니 **`in <lambda>` 에 줄 번호까지 같아서** 구분이 안 됐다.
**이름에 묶을 거면 `def`를 써라**의 근거가 이것이다.

### (6) 「`lambda` 가 `def` 보다 가볍다·빠르다」고 적는다

★★ **이 문서의 근거로는 못 적는다 — 시간을 안 쟀다.**
잰 것은 **`co_code` 가 같다**는 것뿐이고, 그것은 오히려 **성능 차이를 기대할 근거가 없다**는 쪽이다.

### (7) 「바이트코드가 같으니 어느 파이썬에서나 같다」로 적는다

★ **CPython 구현 세부사항이다.** 언어가 보장하는 것은 「`def <lambda>(...)` 로 만든 함수 객체처럼 **동작한다**」까지다.

### (8) `map` 결과를 두 번 쓴다

★ **두 번째는 빈 리스트다.** 이터레이터라 한 번 흐르면 빈다([16번](../16-iterator-protocol/2-summary.md)).

### (9) `lambda s: len(s)` 처럼 한 겹 싸기만 한다

★ **`key=len` 으로 족하다.** `str.lower`·`operator.itemgetter(1)`·`operator.attrgetter("x")` 도 같다.
**싸기만 하는 `lambda`는 이름 한 칸을 잃고 얻는 것이 없다.**

### (10) `reverse=True` 로 한 축만 뒤집으려 한다

★ **`reverse` 는 결과 전체를 뒤집는다.** 한 축만 뒤집는 것은 **키의 부호**(`-p[2]`)이고,
실측에서 두 줄의 결과가 달랐다(동작 10).

### (11) `cmp_to_key` 가 `key` 보다 낫다고 믿는다

★ **호출 횟수가 8 대 16으로 나왔고**, 실측한 예제는 **키를 비트는 것만으로 같은 결과**가 나왔다.
`cmp_to_key` 는 **두 원소를 같이 봐야만 정해지는 순서**에서만 쓴다.

### (12) `KeyWrapper` 라는 이름에 기댄다

★ **CPython 구현의 이름이다.** 순수 파이썬 대체 구현이면 다른 이름이 나온다.

### (13) 루프 안의 `lambda` 가 각자 값을 들고 있을 것이라 믿는다

★★ **셋이 같은 셀을 본다** — `[2, 2, 2]`. **`lambda`라서가 아니라 클로저라서**다.
정본은 [22번](../22-closures-and-late-binding/2-summary.md)이고, 고침(`i=i`)의 부작용은 **`__closure__` 가 `None` 이 되는 것**이다.

### (14) `lambda` 에 독스트링을 단다

★ **달 자리가 없다.** `__doc__` 이 `None` 이다 — 설명이 필요한 순간이 **`def`로 옮길 때**다.

## 구현 세부사항 대 언어 보장

세 층으로 가른다. ★ **이 주제는 「언어 보장」이 얇고 「구현」이 두껍다** —
문서가 정하는 것은 **「식이어야 한다」와 「함수 객체처럼 동작한다」** 두 문장에 가깝고,
우리가 본 것의 대부분은 **그 함수 객체를 CPython 이 어떻게 만들어 놓았나**였다.

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **언어 보장** | 언어 레퍼런스·라이브러리 문서가 정한 것 | 공식 문서 문장을 열어서 인용 |
| **CPython 구현** | 이 구현이 그렇게 하는 것 | `co_code`·`co_name`·`dis`·`__closure__`·예외 문구 |
| **이 판(3.12.3)의 관찰** | 3.12.3 에서 그랬을 뿐 | 캐럿 폭 · `co_flags` 값 · `cmp` 호출 횟수 · `key` 가 받은 순서 |

### 언어 보장

| 사실 | 근거 |
|---|---|
| `lambda` 로 만든 함수는 **문장도 애너테이션도 담을 수 없다** | 6.14 Lambdas — *"cannot contain statements or annotations"* |
| 만들어지는 것은 **`def <lambda>(parameters): return expression` 로 정의한 함수 객체처럼 동작한다** | 6.14 Lambdas |
| **파라미터 목록의 문법이 함수 정의의 것과 같다** | 6.14 Lambdas · 8.7 Function definitions |
| `:=` 는 **식**이다(그래서 식만 오는 자리에 들어간다) | PEP 572 — Assignment **Expressions** |
| `map`·`filter` 는 **이터레이터를 돌려준다** | `map`·`filter` 문서 |
| `sorted` 의 `key` 는 **원소당 한 번** 계산된다 | Sorting HOW TO — 정본은 [10번](../10-list-methods-and-sort-key/2-summary.md) |
| `sorted` 는 **안정 정렬**이다 | `sorted` 문서 — 정본은 [10번](../10-list-methods-and-sort-key/2-summary.md) |
| `cmp_to_key` 는 **cmp 형 함수를 key 형으로 바꾼다** | `functools.cmp_to_key` 문서 |
| `reduce` 는 **왼쪽부터 누적한다** | `functools.reduce` 문서 |

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| **`co_code` 가 `def` 쪽과 한 바이트도 같다** · `co_name` 만 `<lambda>` | 실행 — 동작 5 |
| **`dis` 의 줄 표가 갈린다**(`def`는 `RESUME` 과 몸통이 다른 줄, `lambda`는 한 줄) | 실행 — 동작 5 |
| `__name__`·`__qualname__` 이 **`<lambda>`** · 함수 안이면 **`make.<locals>.<lambda>`** | 실행 — 동작 3 |
| **트레이스백에 `in <lambda>` 로 찍힌다** | 실행 — 동작 4 |
| `SyntaxError` **문구**가 둘로 갈린다(`cannot assign to lambda` 대 `invalid syntax`) | 실행 — 동작 1 |
| **이 다섯에는 캐럿이 있다**(파서가 잡는다) — 21번의 `nonlocal` 오류에는 **없다** | 실행 — 동작 1 |
| `cmp_to_key` 가 만드는 타입 이름이 **`KeyWrapper`** | 실행 — 동작 12 |
| `__closure__`·셀 객체의 **겉모습**, `i=i` 로 고치면 **`None`** | 실행 — 동작 7 |
| `map`·`filter` 객체의 **타입 이름**과 `iter(m) is m` | 실행 — 동작 9 |

### 이 판(3.12.3)의 관찰

| 관찰 | 어디가 흔들리나 |
|---|---|
| `SyntaxError` 문구와 **캐럿 폭** | 판마다 손본다. **캐럿이 나온다는 사실**만 근거로 쓴다 |
| `dis` 의 **오프셋·명령 이름**(`RESUME`·`BINARY_OP`) | 컴파일러가 정한다 |
| `co_flags` 가 **`3`** 인 것 | 다른 비트가 섞일 수 있다 |
| **`cmp` 호출 16회** | 데이터 배열과 정렬 구현에 달렸다. **`key` 8회만 보장이다** |
| **`key` 가 받은 순서가 원본 순서**인 것 | 문서는 **횟수만** 약속한다 |
| 함수 `repr` 의 **주소** | 실행마다 바뀐다 |

### 그래서 이렇게 적으면 틀린다

- ✗ 「`lambda`는 한 줄짜리 함수다」\
  ○ **한 식짜리 함수다.** 괄호 안이면 여러 줄이 된다.
- ✗ 「`lambda` 안에서는 변수를 못 바꾼다」\
  ○ **`:=` 로 바꿀 수 있다.** 금지된 것은 **문장**이다.
- ✗ 「`lambda`의 `SyntaxError` 는 다 `invalid syntax` 다」\
  ○ **대입만 다르다** — `cannot assign to lambda` 이고 나머지 넷은 `invalid syntax` 다.
- ✗ 「`lambda`는 `def`보다 가볍다」\
  ○ **안 쟀다.** 잰 것은 **`co_code` 가 같다**는 것뿐이다.
- ✗ 「바이트코드가 같은 것이 언어 보장이다」\
  ○ **CPython 관찰**이다. 문서는 「**동작한다**」까지만 말한다.
- ✗ 「`f = lambda ...` 로 묶으면 이름이 붙는다」\
  ○ **`__name__` 은 `<lambda>` 그대로다.**
- ✗ 「`cmp_to_key` 가 `key` 보다 효율적이다」\
  ○ **호출 횟수가 8 대 16으로 나왔다.** 시간은 안 쟀다.
- ✗ 「`KeyWrapper` 라는 타입이 언어에 있다」\
  ○ **CPython `functools` 의 구현 이름**이다.
- ✗ 「루프 안 `lambda`가 각자 값을 든다」\
  ○ **셀 하나를 공유한다** — [22번](../22-closures-and-late-binding/2-summary.md).

**판정 기준 한 줄**: **「이것을 괄호로 싸서 변수에 대입할 수 있나」를 물으면 식인지 문장인지가 갈리고,
「이 함수를 이름으로 다시 부를 일이 있나」를 물으면 `lambda`인지 `def`인지가 갈린다.**

## 언제 쓰고 언제 안 쓰나

| 상황 | 판정 |
|---|---|
| 정렬 기준 한 줄을 넘긴다 | ★ **`lambda`의 제자리** — `sorted(xs, key=lambda p: (p[1], -p[2]))` |
| 기준이 **속성·인덱스 하나**다 | ★ **`operator.itemgetter`·`attrgetter`** — 싸기만 하는 `lambda`를 쓰지 않는다 |
| 기준이 **내장 함수 하나**다 | ★ **`key=len`·`key=str.lower`** — `lambda s: len(s)` 는 군더더기다 |
| 분기표(dict)를 만든다 | ★ **`lambda`** — `if/elif` 사다리보다 낫다 |
| 콜백의 기본값이 「아무것도 안 함」이다 | **`lambda: None`** 이 읽힌다 |
| 함수를 **이름에 묶으려** 한다 | ★ **`def`를 쓴다** — `__name__`·트레이스백·독스트링이 전부 살아난다 |
| 몸통에 `if`·`try`·루프가 필요해진다 | ★ **`def`** — 식으로 비틀면 읽는 비용이 폭증한다 |
| `map(lambda n: n * n, xs)` 를 쓰려 한다 | ★ **컴프리헨션이 대개 읽힌다** — `[n * n for n in xs]`([14번](../14-comprehensions/2-summary.md)) |
| `map(str, xs)` 처럼 **함수가 이미 있다** | **`map` 이 낫다** — 컴프리헨션이 이름을 새로 만들 필요가 없다 |
| 결과를 **두 번 이상** 쓴다 | `list()` 로 굳힌다 — `map`·`filter` 는 한 번 흐르면 빈다 |
| 합·최대·전부·하나라도를 구한다 | ★ **`sum`·`max`·`any`·`all`** — `reduce` 를 쓰지 않는다 |
| 두 원소를 **같이 봐야** 순서가 정해진다 | **`cmp_to_key`** — 그 전에 **키를 비틀어** 풀리는지 먼저 본다 |
| 루프 안에서 `lambda`를 여러 개 만든다 | ★ **기본 인자로 굳힌다**(`lambda i=i: i`) — [22번](../22-closures-and-late-binding/2-summary.md)이 정본 |
| 인자 몇 개를 미리 고정한다 | **`functools.partial`**([목록의 **45번 주제**](../45-functools/)) |

## 핵심 문장

- ★★ **`lambda`의 제약은 「짧아야 한다」가 아니라 「식이어야 한다」다.**
  그래서 `pass`·`return`·`raise`·애너테이션·대입문이 전부 `SyntaxError` 이고,
  **괄호 안이면 여러 줄이 된다.**
- ★ **경계는 `:=` 에 있다** — 왈러스는 **식**이라 되고 `=` 는 **문장**이라 안 된다.
  「`lambda` 안에서는 아무것도 못 바꾼다」가 아니다.
- ★ **다섯 판의 문구가 둘로 갈린다** — 대입만 `cannot assign to lambda`, 나머지 넷은 `invalid syntax`.
  **다섯 전부 캐럿이 나온다**(파서가 잡는다) — [21번](../21-scope-legb-global-nonlocal/2-summary.md)의 `nonlocal` 오류는 **캐럿이 없다**.
- ★★ **`lambda`와 `def`는 같은 함수 객체를 만든다** — CPython 에서 **`co_code` 가 한 바이트도 같고 `co_name` 만 다르다.**
  다른 것은 **이름표**뿐이다. 다만 **이것은 구현 관찰이고**, 언어 보장은 「`def <lambda>(...)` 처럼 **동작한다**」까지다.
- ★ **`__name__` 이 `<lambda>` 라서 트레이스백이 모호해진다** — 한 줄에 둘을 놓으면 **어느 것이 터졌는지 알 수 없다.**
  이것이 「이름에 묶을 거면 `def`를 써라」의 **실측 근거**이고, 성능은 근거가 아니다(안 쟀다).
- ★ **`lambda`는 [22번](../22-closures-and-late-binding/2-summary.md)의 클로저를 만드는 가장 짧은 문법이다** —
  루프 안에서 만들면 **셋이 같은 셀을 본다**. `lambda`라고 예외가 아니다.
- **`lambda`도 [19번](../19-function-argument-rules/2-summary.md)의 인자 문법을 전부 쓴다** — 기본값·`*args`·키워드 전용·위치 전용.
  괄호가 없다는 것만 다르다.
- **`map`·`filter` 는 이터레이터라 한 번 흐르면 빈다**([16번](../16-iterator-protocol/2-summary.md)).
- ★ **`key` 는 원소당 한 번, `cmp` 는 비교마다** — 실측에서 원소 8개에 **8회 대 16회**였다.
  **8은 문서가 정한 것이고 16은 이 데이터의 관찰**이다.

## 관련 자료

- 목록: [python/syntax 주제 목록](../README.md) — 이 주제는 **23번**
- 정본 이웃: [10-list-methods-and-sort-key](../10-list-methods-and-sort-key/2-summary.md) — **정렬 `key`의 정본.**\
  **경계**: 「`key` 가 원소당 한 번이라는 계약·안정 정렬·`reverse`·비교 횟수」는 전부 그쪽이다.
  여기는 **그 자리에 `lambda`가 들어간다**는 것과 **그 `lambda`를 어떻게 짜나**까지.
- 정본 이웃: [16-iterator-protocol](../16-iterator-protocol/2-summary.md) — **이터레이터 계약의 정본.**\
  **경계**: 「한 번 흐르면 빈다」는 그쪽, 「`map`·`filter` 가 그 계약을 따른다」는 여기.
- 선행: [19-function-argument-rules](../19-function-argument-rules/2-summary.md) — 인자 문법.\
  **경계**: 「어떤 호출이 되나」는 그쪽, 「`lambda`도 그 문법을 전부 쓴다」는 여기.
- 선행: [21-scope-legb-global-nonlocal](../21-scope-legb-global-nonlocal/2-summary.md) — 이름 해소.\
  **경계**: 「캐럿 없는 `SyntaxError`」의 정본은 그쪽 — 여기는 **캐럿이 나오는 쪽**의 대조군이다.
- 선행: [22-closures-and-late-binding](../22-closures-and-late-binding/2-summary.md) — 클로저와 늦은 바인딩의 **정본.**\
  **경계**: 「왜 늦게 읽나·셀이 무엇인가」는 그쪽, 「`lambda`라고 다르지 않다」는 여기.
- 함께 보는 곳: [14-comprehensions](../14-comprehensions/2-summary.md) — `map`·`filter` 대신 쓰는 자리.
- 함께 보는 곳: [20-mutable-default-args](../20-mutable-default-args/2-summary.md) — `lambda i=i:` 고침이 기대는 **기본값 평가 시점**의 정본.
- 이어지는 곳: [24-decorators](../24-decorators/2-summary.md) — **함수를 받아 함수를 돌려주는** 고차 함수의 문법 설탕.
- 이어지는 곳: [목록의 **44번 주제**](../44-itertools/) 「`itertools`」 — 지연 이터레이터를 조합하는 쪽.
- 이어지는 곳: [목록의 **45번 주제**](../45-functools/) 「`functools`」 — `partial`·`reduce`·`lru_cache` 의 정본.
- 기존 노트: [`cs/foundations/python-basics/`](../../../../python-basics/) — 「이렇게 쓴다」까지가 그쪽이다.\
  **경계**: 여기는 「**무엇을 못 담고, 못 담으면 무슨 에러가 나며, 어디서 틀리나**」부터다.
- 공식 문서: [Lambdas](https://docs.python.org/3.12/reference/expressions.html#lambda) · [`map`](https://docs.python.org/3.12/library/functions.html#map) · [`filter`](https://docs.python.org/3.12/library/functions.html#filter) · [`sorted`](https://docs.python.org/3.12/library/functions.html#sorted) · [Sorting HOW TO](https://docs.python.org/3.12/howto/sorting.html) · [`functools`](https://docs.python.org/3.12/library/functools.html#functools.cmp_to_key)

## 용어 풀이

- **식(expression)**: 계산하면 **값이 남는** 말.\
  예: `x + 1`·`f(3)`·`a if c else b`. **`lambda` 자신도 식**이라 다른 식 안에 들어간다.
- **문장(statement)**: 무언가를 **시키는** 말. 값이 안 남는다.\
  예: `x = 1`·`return`·`pass`·`raise`. `lambda` 몸통에 못 들어간다.
- **`lambda` 식(lambda expression)**: 이름 없는 함수 객체를 만드는 식.\
  예: `lambda a, b: a + b`. 콜론 뒤의 식 값이 곧 반환값이다.
- **고차 함수(higher-order function)**: 함수를 **인자로 받거나 돌려주는** 함수.\
  예: `sorted(xs, key=len)`·`map(f, xs)`·데코레이터.
- **함수 객체(function object)**: `def`든 `lambda`든 만들어지는 물건.\
  예: 실측에서 `type(square) is type(square_def)` 가 `True` 였다 — **같은 타입**이다.
- **`__name__` / `__qualname__`**: 함수의 이름표와 **경로가 붙은** 이름표.\
  예: `lambda`는 `<lambda>` 이고, 함수 안에서 만들면 `make.<locals>.<lambda>` 가 된다.
- **코드 객체(`__code__`)**: 컴파일된 몸통. `co_code`(바이트열)·`co_name`(이름)·`co_varnames` 등을 담는다.\
  예: `lambda`와 `def`의 `co_code` 가 같고 `co_name` 만 달랐다.
- **왈러스 연산자(`:=`)**: 값을 이름에 붙이면서 **그 값을 남기는** 식. 3.8+(PEP 572).\
  예: `(sq := n * n) + sq` — `lambda` 안에서 되는 이유가 「식이라서」다.
- **셀(cell)·자유 변수(free variable)**: 클로저가 바깥 이름을 들고 있는 상자와 그 이름.\
  예: 루프 안 `lambda` 셋이 **같은 셀**을 봐서 `[2, 2, 2]` 가 나온다([22번](../22-closures-and-late-binding/2-summary.md)).
- **`key` 함수**: 원소에서 **비교용 이름표**를 뽑는 함수. 원소당 한 번 불린다.\
  예: `key=lambda p: (p[1], -p[2])` — 튜플로 다축 정렬, 부호로 한 축 역순.
- **`cmp` 함수**: 두 원소를 받아 음수·0·양수를 돌려주는 옛 방식.\
  예: `(a > b) - (a < b)`. `functools.cmp_to_key` 로 감싸야 `sorted` 에 넘길 수 있다.
- **`KeyWrapper`**: `cmp_to_key` 가 만드는 감싸개 타입의 **CPython 구현 이름**.\
  예: 다른 구현이면 이름이 다르다 — 이름에 기대어 테스트를 쓰면 안 된다.
- **지연 평가(lazy evaluation)**: 필요할 때까지 안 계산하는 것.\
  예: `map`·`filter` 가 그렇고, 그래서 **한 번 흐르면 빈다**([16번](../16-iterator-protocol/2-summary.md)).
- **즉시 호출**: 만들자마자 부르는 꼴 — `(lambda n: n + 1)(41)`.\
  예: 괄호로 싸지 않으면 `lambda`가 호출 자체를 삼켜 버린다.
- **`functools.partial`**: 인자 일부를 미리 고정한 **새 호출 가능 객체**.\
  예: `partial(lambda a, b: a - b, 10)(3)` 이 `7` 이다 — 고정은 **앞에서부터**다.
- **`functools.reduce`**: 왼쪽부터 접어 값 하나로 만드는 것.\
  예: 누적 순서가 `[(1, 2), (3, 3), (6, 4)]` 로 관찰됐다.

## 더 들어가면

- ★ **`lambda`가 「함수형 언어의 잔재」라는 말은 절반만 맞다.** 파이썬에서 `lambda`가 **꼭 필요한 자리**는
  「**식 자리에 함수가 필요한데 이름을 붙일 데가 없을 때**」뿐이다 —
  dict 리터럴 안, 인자 자리, 클래스 몸통의 한 줄. 그 밖에는 전부 `def`로 쓸 수 있다.
- ★ **`map`·`filter` 와 컴프리헨션의 갈림은 「함수가 이미 있나」다.**
  `map(str, xs)` 는 `[str(x) for x in xs]` 보다 짧고 이름을 새로 안 만든다.
  반대로 `map(lambda n: n * n, xs)` 는 **`lambda`를 만드느라** 컴프리헨션보다 길어진다.
- **`sorted` 에 `key` 가 없던 시절**에는 `cmp` 가 유일한 방법이었다. Python 3 에서 `sorted(cmp=...)` 가 사라지고
  `functools.cmp_to_key` 가 **이주 경로**로 남았다 — 그래서 이 함수는 「쓰라고 있는 것」이 아니라 「옮겨 오라고 있는 것」에 가깝다.
- ★ **`lambda` 의 기본값은 [20번](../20-mutable-default-args/2-summary.md)의 함정을 그대로 물려받는다** —
  `lambda xs=[]: xs.append(1)` 은 `def`로 쓴 것과 똑같이 새어 흐른다. **몸통이 식이라고 예외가 아니다.**
- ★ **`lambda` 는 디버거에서도 불편하다** — 한 줄에 여러 식이 겹쳐 있어 **중단점을 걸 단위가 없다.**
  트레이스백 모호성(동작 4)과 같은 뿌리다.
