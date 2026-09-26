# python/syntax/24-decorators — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만.
> - [8.7. Function definitions](https://docs.python.org/3.12/reference/compound_stmts.html#function-definitions) — 데코레이터 문법과 **평가 시점**, 등가식
> - [8.8. Class definitions](https://docs.python.org/3.12/reference/compound_stmts.html#class-definitions) — 클래스에도 같은 문법이 붙는다
> - [`functools.wraps`](https://docs.python.org/3.12/library/functools.html#functools.wraps) · [`functools.update_wrapper`](https://docs.python.org/3.12/library/functools.html#functools.update_wrapper) — `WRAPPER_ASSIGNMENTS`·`WRAPPER_UPDATES`·`__wrapped__`
> - [`inspect.signature`](https://docs.python.org/3.12/library/inspect.html#inspect.signature) · [`inspect.unwrap`](https://docs.python.org/3.12/library/inspect.html#inspect.unwrap)
> - [3.2. The standard type hierarchy](https://docs.python.org/3.12/reference/datamodel.html#the-standard-type-hierarchy) — 함수 객체의 `__closure__`·`__dict__`
> - [PEP 318 — Decorators for Functions and Methods](https://peps.python.org/pep-0318/)
>
> **실행 검증** — 이 문서에 실린 출력은 전부 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.\
> ★ **던지는 형태를 하나로 고정했다** — `python3 - <파일` 로 던져 트레이스백이 `File "<stdin>", line N` 이 된다.
> 이 주제의 예외는 전부 **실행 중 예외**라 소스 줄도 캐럿도 안 나온다.\
> **버전** — 함수 데코레이터는 **2.4+**(PEP 318), 클래스 데코레이터는 **2.6+**(PEP 3129).
> `functools.wraps` 가 `__wrapped__` 를 붙이는 것은 **3.2+**.
> ★ `WRAPPER_ASSIGNMENTS` 안의 `__type_params__` 는 **3.12 의 타입 파라미터 문법(PEP 695)이 붙인 이름**이다 —
> **다른 판의 목록이 어떤지는 여기서 안 돌려 봤다.**\
> **구현 대 언어 보장 한 줄** — **「`@deco` 가 `f = deco(f)` 이고 그것이 정의 시점에 돈다」까지가 언어 보장**이고,
> `__closure__`·셀·`co_freevars` 로 그 속을 들여다본 것은 **CPython 구현**이다.\
> **★ 흔들리는 칸 / 안 흔들리는 칸** — 재대조에서 「고칠 것」과 「설계상 안 맞는 것」을 기계적으로 가르려고 미리 선언한다.
>
> | | 무엇 |
> |---|---|
> | **흔들린다** | `<cell at 0x…>`·`<function … at 0x…>` 의 **주소**, `id()` 값 |
> | **안 흔들린다** | 예외 **타입**과 **메시지 본문**, `File "<stdin>", line N`, **셀 개수**, `is` 판정, `co_freevars`·`co_varnames`, `__defaults__` 값, `(exit N)` |
>
> ★ **이 주제의 블록에는 주소가 한 곳도 안 찍힌다** — `is` 판정(`True`·`False`)과 이름·개수만 찍게 짰다.
> 그래서 같은 판에서 다시 돌리면 **한 글자도 안 변한다.**\
> **선행** — [19번](../19-function-argument-rules/2-summary.md)(`*args`·`**kwargs` 로 받는 법) ·
> [21번](../21-scope-legb-global-nonlocal/2-summary.md)(이름이 어디서 풀리나) ·
> [22번](../22-closures-and-late-binding/2-summary.md)(셀과 자유 변수) ·
> [23번](../23-lambda-and-higher-order-functions/2-summary.md)(함수를 값으로 다루는 것).\
> ★★ **이 넷이 전부 여기서 쓰인다.** 데코레이터는 **새 문법이 아니라 앞 넷의 합**이다.

## 한눈에 — 쉽게 말하면

**데코레이터는 「선물을 한 겹 더 포장하고, 이름표는 그대로 옮겨 붙이는 일」이다.**

- 포장하는 시점은 **부칠 때가 아니라 만들 때**다 — `def` 문을 지나는 그 순간 한 번.
- 포장지(래퍼)는 **아무 선물이나 받을 수 있어야** 하므로 `*args`·`**kwargs` 로 받는다([19번](../19-function-argument-rules/2-summary.md)).
- 포장하면 **겉에 붙은 이름표가 포장지 것으로 바뀐다** — `functools.wraps` 가 그 이름표를 원래 것으로 **옮겨 붙인다.**

```text
   @deco                    deco 가 한 번 돌아 새 함수를 만든다
   def f(...):     ------>  이름 f 는 이제 그 새 함수(wrapper)를 가리킨다
       ...

        f ----> wrapper ----(__wrapped__)----> 원래 함수
        ^                                      ^
        이름이 가리키는 것                       포장 안에 든 것
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 선물 | 원래 함수 | `__wrapped__` 로 꺼낸다 |
| 포장지 | 래퍼 함수 | `__qualname__` 이 `deco.<locals>.wrapper` |
| 포장은 **만들 때 한 번** | **정의 시점 평가** | `deco` 안의 `print` 가 **한 번만** 찍힌다 |
| 부칠 때마다 하는 일 | 래퍼 호출 | 호출 수만큼 `wrapper` 가 찍힌다 |
| 이름표를 옮겨 붙인다 | `functools.wraps` | `__name__`·`__qualname__`·`__doc__` |
| 겹겹이 포장 | 데코레이터 스택 | 여섯 줄이 **대칭**으로 찍힌다 |
| 포장 기계를 **먼저 고른다** | 인자 있는 데코레이터 | 층이 **셋**이 된다 |
| 포장지를 벗긴다 | `inspect.unwrap` | 체인을 끝까지 따라간다 |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.\
「**로그·재시도·캐시를 붙였더니 `help()` 가 쓸모없어졌다**」와
「**`@retry` 를 괄호 없이 붙였더니 엉뚱한 줄에서 터졌다**」가 그것이다.
앞엣것은 `functools.wraps` 한 줄로 막고, 뒤엣것은 **층이 몇 개인지**를 세면 안 걸린다.

> **데코레이터(decorator)** — `def` 문 위에 `@` 로 붙이는 **호출 가능한 것**. 함수 객체를 받아 **무엇이든** 돌려준다.\
> 예: `@deco` 를 `def f` 위에 쓰면 이름 `f` 는 `deco(f)` 가 돌려준 것에 묶인다.

> **래퍼(wrapper)** — 원래 함수를 품고 **대신 불리는** 함수. 앞뒤로 할 일을 하고 가운데서 원본을 부른다.\
> 예: `wrapper(*a, **k)` 안에서 `fn(*a, **k)` 를 부르는 그 함수.

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

## 이 주제가 답하려는 질문

1. **`@deco` 는 무슨 문법인가** — 새로운 것인가, 아니면 `f = deco(f)` 를 짧게 쓴 것인가.
2. **언제 도는가** — 데코레이터는 정의할 때 도는가 부를 때 도는가. 겹치면 어느 쪽부터 도는가.
3. **`functools.wraps` 를 빼면 정확히 무엇이 깨지는가** — 「전부 깨진다」가 맞는 말인가, 항목마다 다른가.

★ 셋째 질문이 이 주제의 인출 목표다. **「무엇을 잃는지 항목으로 댈 수 있느냐」가 아는 것과 들은 것의 경계**다.

## 동작 방식

> 이 절이 본문이다. 이 주제의 네 번째 창은 **함수 객체의 속성**이다 —
> `__name__`·`__qualname__`·`__doc__`·`__annotations__`·`__dict__`·`__wrapped__`·`__closure__`.
> **무엇이 일어나는지는 `print` 로**, **무엇이 남았는지는 그 속성으로** 본다.

### 1. ★ `@deco` 는 `f = deco(f)` 다 — 새 문법이 아니다

**언제 쓰나** — 데코레이터를 처음 볼 때. 그리고 「이게 도대체 무슨 마법인가」가 막힐 때마다.

레퍼런스가 등가식을 **그대로** 준다.

> `@f1(arg)` `@f2` `def func(): pass` is roughly equivalent to
> `def func(): pass` / `func = f1(arg)(f2(func))`
> except that the original function is not temporarily bound to the name func.

우리말로 — **`@` 줄은 「함수를 만들고, 그것을 데코레이터에 넣고, 돌려받은 것을 그 이름에 묶어라」의 줄임**이다.
다른 점은 **단 하나**, 원래 함수가 **이름에 잠시라도 묶이지 않는다**는 것뿐이다.

```text
   쓴 것                       파이썬이 하는 일
   ----------------------      ------------------------------------
   @deco                       ① def 문으로 함수 객체를 만든다
   def f(a):           ==>     ② deco(그 함수 객체) 를 부른다
       return a                ③ 돌려받은 것을 이름 f 에 묶는다

   손으로 푼 것                 ★ 다른 점은 하나뿐이다
   def f(a):                      손으로 푼 쪽은 ②의 앞에서
       return a                   원래 함수가 이름 f 에 "잠시" 묶인다
   f = deco(f)                    @ 쪽은 그 한순간이 없다
```

두 형태를 한 파일에서 나란히 돌렸다.

```python
# e24_desugar.py
def deco(fn):
    print("  deco 가 돈다:", fn.__name__)
    return fn


print("① @ 문법")


@deco
def a():
    pass


print("② 손으로 푼 것")


def b():
    pass


b = deco(b)
print("③ 둘이 같은 일인가:", a is not None and b is not None)
```

```text
===== python3 - <e24_desugar.py =====
① @ 문법
  deco 가 돈다: a
② 손으로 푼 것
  deco 가 돈다: b
③ 둘이 같은 일인가: True
(exit 0)
```

- **`@deco` 를 붙인 쪽과 `b = deco(b)` 라고 쓴 쪽이 똑같이 `deco 가 돈다` 를 찍는다.** 같은 일이다.
- ★ **「잠시 묶이지 않는다」는 것도 언어 보장이다**(위 인용의 `except that …`).
  눈에 띄는 자리는 드물지만, **데코레이터가 예외를 던지면** 갈린다 —
  손으로 푼 쪽은 이름 `b` 가 **원래 함수를 가리킨 채** 남고, `@` 쪽은 **이름이 아예 안 생긴다.**
- ★ **돌려주는 것이 함수일 필요는 없다.** 레퍼런스는 **호출 가능한 것**(callable)을 넣으라고만 한다 —
  받는 쪽 제약이지 돌려주는 쪽 제약이 아니다(동작 9).

**비용** — `@` 는 **읽는 순서를 뒤집는다.** `f = deco(f)` 는 한 줄에 다 보이지만
`@deco` 는 **아래의 `def` 를 먼저 읽고 위로 올라와야** 뜻이 완성된다.

### 2. ★★ 정의 시점에 한 번 돈다 — 호출은 몇 번이든 래퍼만

**언제 쓰나** — 「데코레이터 안에 무거운 준비 코드를 둬도 되나」를 물을 때. 그리고 임포트가 느려졌을 때.

레퍼런스 한 문장이 그대로 답이다.

> A function definition may be wrapped by one or more decorator expressions. Decorator expressions
> are evaluated when the function is defined, in the scope that contains the function definition.
> The result must be a callable, which is invoked with the function object as the only argument.

**「함수가 정의될 때 평가된다」 — 언어 보장이다.**

```text
   시간 ---------------------------------------------------->

   def 문을 지난다       f()          f()          f()
        |                 |            |            |
        v                 v            v            v
     deco 가 1회        wrapper      wrapper      wrapper
     (여기서 끝)         1회           1회           1회

   ★ deco 는 몇 번을 부르든 다시 안 돈다
```

```python
# e24_define_time.py
def deco(fn):
    print("  [정의 시점] deco 실행 — 받은 것:", fn.__name__)

    def wrapper(*a, **k):
        print("  [호출 시점] wrapper 실행")
        return fn(*a, **k)

    return wrapper


print("① def 문을 만나기 전")


@deco
def work():
    return "결과"


print("② def 문을 지난 뒤 — 아직 한 번도 안 불렀다")
print("③ 첫 호출:", work())
print("④ 둘째 호출:", work())
```

```text
===== python3 - <e24_define_time.py =====
① def 문을 만나기 전
  [정의 시점] deco 실행 — 받은 것: work
② def 문을 지난 뒤 — 아직 한 번도 안 불렀다
  [호출 시점] wrapper 실행
③ 첫 호출: 결과
  [호출 시점] wrapper 실행
④ 둘째 호출: 결과
(exit 0)
```

- `[정의 시점]` 줄이 **①과 ② 사이에 한 번**만 찍혔다. 그때 **함수 몸통은 아직 한 줄도 안 돌았다.**
- `[호출 시점]` 줄은 **부를 때마다** 찍혔다.
- ★★ **[20번](../20-mutable-default-args/2-summary.md)의 기본값도 정확히 같은 시점이다** —
  `def` 문을 **실행할 때** 한 번. **그쪽이 그 성질의 정본**이므로 여기서 다시 설명하지 않는다.
  외울 것은 하나다 — **`def` 문은 「정의를 적어 두는 것」이 아니라 「실행되는 문장」이다.**

**비용** — 데코레이터 안의 준비 코드는 **임포트 시간에 전부 치른다.**
모듈을 불러오기만 해도 돌므로, 무거운 것(연결·파일 읽기)을 여기 두면 임포트가 느려진다.

### 3. 기본 데코레이터 — 무엇이든 받아 그대로 넘긴다

**언제 쓰나** — 데코레이터를 직접 쓸 때. 형태는 늘 이 하나다.

래퍼는 **원본이 어떤 시그니처든 받아 넘겨야** 하므로 `*args`·`**kwargs` 로 받는다
— [19번](../19-function-argument-rules/2-summary.md)의 「남는 것을 담는 통」이 여기 쓰인다.

```python
# e24_basic.py
import functools


def trace(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        print("  들어간다:", fn.__name__, args, kwargs)
        result = fn(*args, **kwargs)
        print("  나온다  :", result)
        return result

    return wrapper


@trace
def add(a, b=0):
    return a + b


print("add(1, 2)")
add(1, 2)
print("add(1, b=9)")
add(1, b=9)
print("add 는 무엇인가:", add.__name__, "· 실제 함수는", add.__wrapped__.__name__)
```

```text
===== python3 - <e24_basic.py =====
add(1, 2)
  들어간다: add (1, 2) {}
  나온다  : 3
add(1, b=9)
  들어간다: add (1,) {'b': 9}
  나온다  : 10
add 는 무엇인가: add · 실제 함수는 add
(exit 0)
```

- `add(1, 2)` 는 `args=(1, 2)`·`kwargs={}` 로, `add(1, b=9)` 는 `args=(1,)`·`kwargs={'b': 9}` 로 들어왔다.
  **호출부가 위치로 줬는지 이름으로 줬는지가 래퍼에 그대로 보인다.**
- `functools.wraps` 덕에 `add.__name__` 이 `'add'` 로 남았고, `add.__wrapped__` 로 **원본도 꺼낼 수 있다.**
- ★ **래퍼는 `return` 을 반드시 해야 한다.** 안 하면 모든 호출이 `None` 을 돌려주는 조용한 버그가 된다
  — 이 블록의 `result` 를 그대로 돌려주는 줄이 그 자리다.

**비용** — `(*args, **kwargs)` 는 **시그니처를 지운다.** 그것을 되살리는 것이 `wraps` 이고, 그 이야기가 동작 6\~8이다.

### 4. ★★ 겹쳐 쌓으면 — 적용은 아래에서 위로, 호출은 위에서 아래로

**언제 쓰나** — `@app.route` 와 `@login_required` 처럼 둘 이상을 쌓았는데 순서가 의심될 때.

레퍼런스는 한마디로 적는다 — *"Multiple decorators are applied in nested fashion."*
**중첩**이라는 말이 두 방향을 한꺼번에 설명한다.

```text
   적용 (def 문을 지날 때)              호출 (f() 를 부를 때)
   아래에서 위로                        위에서 아래로, 그리고 되돌아온다

      @바깥      <- 3번째                 들어감: 바깥      1
      @가운데    <- 2번째                   들어감: 가운데   2
      @안쪽      <- 1번째                     들어감: 안쪽   3
      def f                                      몸통       4
                                              나옴: 안쪽    5
                                            나옴: 가운데    6
                                          나옴: 바깥        7

   결국 이 모양이다:  바깥( 가운데( 안쪽( 몸통 ) ) )
```

```python
# e24_stack_order.py
def make(tag):
    def deco(fn):
        print("  적용:", tag)

        def wrapper(*a, **k):
            print("  들어감:", tag)
            r = fn(*a, **k)
            print("  나옴  :", tag)
            return r

        return wrapper

    return deco


print("① 적용 순서 (def 문을 지날 때)")


@make("바깥")
@make("가운데")
@make("안쪽")
def f():
    print("  몸통")
    return 1


print("② 호출 순서")
f()
```

```text
===== python3 - <e24_stack_order.py =====
① 적용 순서 (def 문을 지날 때)
  적용: 안쪽
  적용: 가운데
  적용: 바깥
② 호출 순서
  들어감: 바깥
  들어감: 가운데
  들어감: 안쪽
  몸통
  나옴  : 안쪽
  나옴  : 가운데
  나옴  : 바깥
(exit 0)
```

- ★ **`적용:` 세 줄이 안쪽 → 가운데 → 바깥**이다. `def` 에 **가장 가까운 것이 먼저** 원본을 받는다.
- ★★ **`들어감`·`나옴` 여섯 줄이 대칭**이다 — 바깥·가운데·안쪽으로 들어가 몸통을 찍고 **역순으로** 나온다.
  **이 대칭이 「중첩」의 근거다.** 순서를 외우지 말고 **괄호를 그려라** — `바깥(가운데(안쪽(f)))`.
- ★ 그래서 **캐시는 바깥, 로그는 안쪽** 같은 판단이 생긴다. 바깥에 둔 것이 **먼저 보고 나중에 놓는다.**

**비용** — 순서가 바뀌면 **동작이 바뀐다.** 인증을 캐시 바깥에 둘 것이냐 안쪽에 둘 것이냐가
「캐시된 응답도 인증을 거치나」를 통째로 가른다. **쌓는 순서는 주석이 아니라 계약이다.**

### 5. ★ 인자 있는 데코레이터 — 층이 셋이 된다

**언제 쓰나** — `@repeat(3)`·`@retry(times=5)` 처럼 **데코레이터 자체에 설정을 주고 싶을 때.**

`@` 뒤에는 **식**이 올 수 있다. `@repeat(3)` 은 **먼저 `repeat(3)` 을 계산해** 그 결과를 데코레이터로 쓴다는 뜻이다.
그래서 함수가 하나 더 필요하다 — **「데코레이터를 만들어 주는 함수」**.

```text
   @repeat(3)
   def hello(name): ...

   ① repeat(3)          -> deco 를 돌려준다      def 문을 지날 때, 즉시
   ② deco(hello)        -> wrapper 를 돌려준다   그 직후, 즉시
   ③ wrapper("파이썬")   -> 결과                 부를 때만

   ①②는 정의 시점에 붙어서 일어나고, ③만 호출 시점이다.
   인자 없는 데코레이터는 이 가운데 ①이 없는 것뿐이다.
```

```python
# e24_args_deco.py
import functools


def repeat(times):
    print("  [1층] repeat 가 돈다 — times =", times)

    def deco(fn):
        print("  [2층] deco 가 돈다 — fn =", fn.__name__)

        @functools.wraps(fn)
        def wrapper(*a, **k):
            print("  [3층] wrapper 가 돈다")
            out = [fn(*a, **k) for _ in range(times)]
            return out

        return wrapper

    return deco


print("① def 문을 지난다")


@repeat(3)
def hello(name):
    return "안녕 " + name


print("② 호출한다")
print("결과:", hello("파이썬"))
```

```text
===== python3 - <e24_args_deco.py =====
① def 문을 지난다
  [1층] repeat 가 돈다 — times = 3
  [2층] deco 가 돈다 — fn = hello
② 호출한다
  [3층] wrapper 가 돈다
결과: ['안녕 파이썬', '안녕 파이썬', '안녕 파이썬']
(exit 0)
```

- `[1층]`·`[2층]` 이 **①과 ② 사이에 나란히** 찍혔다 — **둘 다 정의 시점**이다.
- `[3층]` 만 **부를 때** 찍혔다.
- ★ **`times` 는 1층의 지역 이름인데 3층에서 읽힌다** — 이것이 [22번](../22-closures-and-late-binding/2-summary.md)의 클로저다.
  데코레이터 인자를 담아 두는 통이 **셀**이라는 뜻이고, 동작 10에서 그 셀을 직접 꺼내 본다.

**비용** — 층이 하나 늘면 **읽는 사람이 세어야 할 것도 하나 는다.**
그리고 **괄호를 빠뜨리면 조용히 어긋난다**(「어디서 틀리나」 (1)).

### 6. ★★ `functools.wraps` 없이 잃는 것 — 항목마다 다르다

**언제 쓰나** — 데코레이터를 쓸 때마다. 그리고 「`wraps` 는 관례라던데 왜 필요한가」를 물을 때.

`wraps` 없이 감싼 함수와 원본을 **일곱 칸 전부** 찍어 대조했다.

```python
# e24_wraps_missing.py
def deco(fn):
    def wrapper(*a, **k):
        return fn(*a, **k)

    return wrapper


def target(a, b: int = 1) -> int:
    """이 함수가 하는 일."""
    return a + b


target.retries = 3

wrapped = deco(target)

for attr in ("__name__", "__qualname__", "__doc__", "__module__",
             "__annotations__", "__dict__"):
    print("%-15s 원본: %-34r 감싼 뒤: %r"
          % (attr, getattr(target, attr), getattr(wrapped, attr)))
print("%-15s 원본: %-34r 감싼 뒤: %r"
      % ("__wrapped__", getattr(target, "__wrapped__", "(없음)"),
         getattr(wrapped, "__wrapped__", "(없음)")))
```

```text
===== python3 - <e24_wraps_missing.py =====
__name__        원본: 'target'                           감싼 뒤: 'wrapper'
__qualname__    원본: 'target'                           감싼 뒤: 'deco.<locals>.wrapper'
__doc__         원본: '이 함수가 하는 일.'                      감싼 뒤: None
__module__      원본: '__main__'                         감싼 뒤: '__main__'
__annotations__ 원본: {'b': <class 'int'>, 'return': <class 'int'>} 감싼 뒤: {}
__dict__        원본: {'retries': 3}                     감싼 뒤: {}
__wrapped__     원본: '(없음)'                             감싼 뒤: '(없음)'
(exit 0)
```

같은 일곱 칸을 `wraps` 를 붙여 다시 찍었다.

```python
# e24_wraps_present.py
import functools


def deco(fn):
    @functools.wraps(fn)
    def wrapper(*a, **k):
        return fn(*a, **k)

    return wrapper


def target(a, b: int = 1) -> int:
    """이 함수가 하는 일."""
    return a + b


target.retries = 3

wrapped = deco(target)

for attr in ("__name__", "__qualname__", "__doc__", "__module__",
             "__annotations__"):
    print("%-15s 원본: %-34r 감싼 뒤: %r"
          % (attr, getattr(target, attr), getattr(wrapped, attr)))
print("%-15s 원본: %-34s 감싼 뒤: %s"
      % ("__dict__ 키", sorted(target.__dict__), sorted(wrapped.__dict__)))
print("%-15s 감싼 뒤가 원본을 가리키나: %s"
      % ("__wrapped__", wrapped.__wrapped__ is target))
print("옮기는 목록 WRAPPER_ASSIGNMENTS:", functools.WRAPPER_ASSIGNMENTS)
print("합치는 목록 WRAPPER_UPDATES    :", functools.WRAPPER_UPDATES)
```

```text
===== python3 - <e24_wraps_present.py =====
__name__        원본: 'target'                           감싼 뒤: 'target'
__qualname__    원본: 'target'                           감싼 뒤: 'target'
__doc__         원본: '이 함수가 하는 일.'                      감싼 뒤: '이 함수가 하는 일.'
__module__      원본: '__main__'                         감싼 뒤: '__main__'
__annotations__ 원본: {'b': <class 'int'>, 'return': <class 'int'>} 감싼 뒤: {'b': <class 'int'>, 'return': <class 'int'>}
__dict__ 키      원본: ['retries']                        감싼 뒤: ['__wrapped__', 'retries']
__wrapped__     감싼 뒤가 원본을 가리키나: True
옮기는 목록 WRAPPER_ASSIGNMENTS: ('__module__', '__name__', '__qualname__', '__doc__', '__annotations__', '__type_params__')
합치는 목록 WRAPPER_UPDATES    : ('__dict__',)
(exit 0)
```

★★ **항목별 대조표** — 이 표가 이 주제의 인출 목표다.

| 칸 | 원본 | `wraps` 없이 | `wraps` 있이 | 무슨 일인가 |
|---|---|---|---|---|
| `__name__` | `'target'` | `'wrapper'` | `'target'` | **잃는다** → 옮겨진다 |
| `__qualname__` | `'target'` | `'deco.<locals>.wrapper'` | `'target'` | **잃는다** → 옮겨진다 |
| `__doc__` | 독스트링 | `None` | 독스트링 | **잃는다** → 옮겨진다 |
| `__module__` | `'__main__'` | `'__main__'` | `'__main__'` | ★ **안 잃는다** |
| `__annotations__` | `{'b': int, 'return': int}` | `{}` | 원본과 같다 | **잃는다** → 옮겨진다 |
| `__dict__` | `{'retries': 3}` | `{}` | `retries` 가 있다 | **잃는다** → ★ **합쳐진다**(옮김이 아니다) |
| `__wrapped__` | 없다 | 없다 | **원본을 가리킨다** | ★ **잃는 게 아니라 새로 붙는다** |

★ **「전부 잃는다」는 틀린 요약이다.** 표에서 **`__module__` 한 칸만 색이 다르다.**
`wraps` 없이도 둘 다 `'__main__'` 인데, 이유는 간단하다 — **래퍼도 원본과 같은 모듈에서 정의됐기 때문**이다.
같은 파일에서 만든 함수라 처음부터 같은 값을 갖고 있었을 뿐, **`wraps` 가 지켜 준 것이 아니다.**
(★ **다른 모듈에서 정의된 데코레이터였으면 어땠는지는 여기서 안 돌려 봤다** — 그러니 적지 않는다.
다만 `__module__` 이 `WRAPPER_ASSIGNMENTS` **목록의 맨 앞에 있다**는 것은 아래 출력에 찍혀 있다.)

★ **`__wrapped__` 는 잃는 칸이 아니다.** 원본에도 없고 `wraps` 없이 감싼 쪽에도 없다 —
`wraps` 가 **새로 만들어 붙인다.** 문서가 그렇게 적는다.

> The default values for these arguments are the module level constants WRAPPER_ASSIGNMENTS
> (which assigns to the wrapper function's `__module__`, `__name__`, `__qualname__`,
> `__annotations__`, `__type_params__`, and `__doc__`) and WRAPPER_UPDATES (which updates the
> wrapper function's `__dict__`). … this function automatically adds a `__wrapped__` attribute
> to the wrapper that refers to the function being wrapped.

```text
   원본 target                          래퍼 wrapper

   __module__        '__main__'  ==대입==>  '__main__'   (원래 같았다)
   __name__          'target'    ==대입==>  'target'
   __qualname__      'target'    ==대입==>  'target'
   __doc__           '...'       ==대입==>  '...'
   __annotations__   {...}       ==대입==>  {...}
   __type_params__   ()          ==대입==>  ()
   __dict__          {retries}   ==update=> {retries, ...}   ★ 대입이 아니다

                                 ==신규==>  __wrapped__ = target
```

- **여섯 칸은 `WRAPPER_ASSIGNMENTS` 로 대입**되고, **`__dict__` 한 칸만 `WRAPPER_UPDATES` 로 합쳐진다.**
  출력에 그 두 튜플이 그대로 찍혀 있다 — 대입 목록 여섯 개, 합침 목록은 `('__dict__',)` 하나뿐이다.
- ★ **`__type_params__` 가 목록에 들어 있다** — 3.12 의 타입 파라미터 문법(PEP 695)이 붙인 속성이다.
  **이 판의 관찰**이고, 다른 판의 목록은 안 돌려 봤다.
- ★ **`wraps` 있이 감싼 래퍼의 `__dict__` 키에 `__wrapped__` 가 들어 있다** —
  `__wrapped__` 는 특별한 슬롯이 아니라 **그냥 속성 하나**라는 뜻이다.

**비용** — 없다시피 하다. **한 줄(`@functools.wraps(fn)`)이고 정의 시점에 한 번 돈다.**
안 붙일 이유가 사실상 없다.

### 7. ★ `__dict__` 는 「옮기기」가 아니라 「합치기」다

**언제 쓰나** — 원본 함수에 표시(`fn.is_task = True` 류)를 붙여 쓰는 코드에서. 프레임워크가 흔히 그렇다.

`WRAPPER_UPDATES` 가 `('__dict__',)` 라는 말은 **`wrapper.__dict__.update(원본.__dict__)`** 를 한다는 뜻이다.
**대입이 아니므로** 세 가지가 따라온다.

```python
# e24_wraps_dict.py
import functools


def deco(fn):
    @functools.wraps(fn)
    def wrapper(*a, **k):
        return fn(*a, **k)

    wrapper.added_by_wrapper = "래퍼가 나중에 붙인 것"
    return wrapper


def target(a):
    return a


target.retries = 3
target.owner = "billing"

wrapped = deco(target)
print("원본 __dict__ 키 :", sorted(target.__dict__))
print("래퍼 __dict__ 키 :", sorted(wrapped.__dict__))
print("같은 dict 객체인가:", wrapped.__dict__ is target.__dict__)
print("원본에도 번졌나  :", "added_by_wrapper" in target.__dict__)
print("원본 retries 값  :", target.retries, "· 래퍼 retries 값:", wrapped.retries)
wrapped.retries = 99
print("래퍼 쪽만 바꾸면 — 원본:", target.retries, "· 래퍼:", wrapped.retries)
```

```text
===== python3 - <e24_wraps_dict.py =====
원본 __dict__ 키 : ['owner', 'retries']
래퍼 __dict__ 키 : ['__wrapped__', 'added_by_wrapper', 'owner', 'retries']
같은 dict 객체인가: False
원본에도 번졌나  : False
원본 retries 값  : 3 · 래퍼 retries 값: 3
래퍼 쪽만 바꾸면 — 원본: 3 · 래퍼: 99
(exit 0)
```

- **같은 dict 객체가 아니다**(`False`) — 내용만 복사됐다.
- **래퍼가 나중에 붙인 것은 원본에 안 번진다**(`added_by_wrapper` 가 원본에 없다).
- **래퍼 쪽 값을 바꿔도 원본은 그대로다**(`99` 대 `3`).

```text
   target.__dict__                 wrapper.__dict__
   +-------------------+           +-----------------------+
   | retries: 3        | --복사--> | retries: 3            |
   | owner : 'billing' | --복사--> | owner  : 'billing'    |
   +-------------------+           | added_by_wrapper: ... |  <- 래퍼만 갖는다
                                   | __wrapped__: target   |  <- wraps 가 붙였다
                                   +-----------------------+

   ★ 화살표는 한 방향이고, 한 번뿐이다(감쌀 때 딱 한 번).
     그 뒤로 둘은 남남이다.
```

★★ **그래서 「감싼 뒤에 원본에 붙인 표시」는 래퍼에 안 보인다.** 순서가 중요하다 —
`wraps` 는 **감싸는 그 순간의 `__dict__` 를 복사**할 뿐, 계속 동기화하지 않는다.

**비용** — 얕은 복사다. **값이 가변 객체면 둘이 같은 객체를 가리킨다**
([03번](../03-mutability-and-copying/2-summary.md)의 얕은 복사와 같은 이야기다).

### 8. ★ `inspect.signature` 는 시그니처를 복사한 게 아니라 `__wrapped__` 를 따라간다

**언제 쓰나** — `help()`·IDE·타입 체커·문서 생성기가 이상한 시그니처를 보여 줄 때.

```python
# e24_signature.py
import functools
import inspect


def plain_deco(fn):
    def wrapper(*a, **k):
        return fn(*a, **k)

    return wrapper


def wraps_deco(fn):
    @functools.wraps(fn)
    def wrapper(*a, **k):
        return fn(*a, **k)

    return wrapper


def target(a, b=1, *, c):
    return a + b


print("원본                :", inspect.signature(target))
print("wraps 없이 감싼 것    :", inspect.signature(plain_deco(target)))
print("wraps 로 감싼 것      :", inspect.signature(wraps_deco(target)))
print("follow_wrapped=False :", inspect.signature(wraps_deco(target), follow_wrapped=False))
print("unwrap 으로 벗기면    :", inspect.unwrap(wraps_deco(target)) is target)
print("도움말이 보는 이름    :", wraps_deco(target).__name__, "대", plain_deco(target).__name__)
```

```text
===== python3 - <e24_signature.py =====
원본                : (a, b=1, *, c)
wraps 없이 감싼 것    : (*a, **k)
wraps 로 감싼 것      : (a, b=1, *, c)
follow_wrapped=False : (*a, **k)
unwrap 으로 벗기면    : True
도움말이 보는 이름    : target 대 wrapper
(exit 0)
```

- **`wraps` 없이 감싼 것은 `(*a, **k)`** — 래퍼가 실제로 그렇게 생겼으니 정직한 답이다.
- **`wraps` 로 감싼 것은 `(a, b=1, *, c)`** — 원본 그대로다.
- ★★ **`follow_wrapped=False` 를 주면 `wraps` 가 있어도 다시 `(*a, **k)`** 가 된다.
  **이것이 결정적 증거다** — `wraps` 는 **시그니처를 복사하지 않았다.**
  `signature` 가 **`__wrapped__` 를 따라가서** 원본의 시그니처를 읽어 온 것이다.
- `inspect.unwrap` 으로 벗기면 **원본 객체 자체**가 나온다(`True`).

```text
   inspect.signature(wrapper)

     wrapper 에 __wrapped__ 가 있나?
        |                    |
        아니오                 예  (기본값 follow_wrapped=True)
        |                    |
        v                    v
     래퍼의 시그니처        __wrapped__ 를 따라가 원본을 읽는다
     (*a, **k)            (a, b=1, *, c)

   follow_wrapped=False 는 이 화살표를 끊는다 -> 다시 (*a, **k)
```

★ [19번](../19-function-argument-rules/2-summary.md)이 「어떤 호출이 되나」의 정본이고,
여기는 **「감싼 뒤에도 그 시그니처가 보이나」만** 다룬다.
★★ 다만 **보이는 것과 실제로 되는 것은 다르다** — `signature` 가 `(a, b=1, *, c)` 라고 답해도
래퍼는 여전히 `(*a, **k)` 라 **무엇이든 받아서** 원본에 넘긴다. 실제 검사는 **원본이 불릴 때** 난다.

**비용** — `signature` 의 답을 **런타임 검증의 근거로 쓰면 안 된다.** 그것은 **문서용 답**이다.

### 9. `__wrapped__` 체인 — 두 겹이면 두 겹이 남는다

**언제 쓰나** — 데코레이터를 여럿 쌓은 함수에서 **원본**을 꺼내야 할 때.

```python
# e24_unwrap_chain.py
import functools
import inspect


def tag(label):
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*a, **k):
            return label + ":" + fn(*a, **k)

        return wrapper

    return deco


@tag("바깥")
@tag("안쪽")
def base():
    return "몸통"


print("결과            :", base())
print("__name__        :", base.__name__)
print("한 겹 벗기면     :", base.__wrapped__.__name__, base.__wrapped__())
print("두 겹 벗기면     :", base.__wrapped__.__wrapped__())
print("inspect.unwrap  :", inspect.unwrap(base)())
depth = 0
f = base
while hasattr(f, "__wrapped__"):
    f = f.__wrapped__
    depth += 1
print("체인 길이        :", depth, "· 맨 밑:", f.__qualname__)
```

```text
===== python3 - <e24_unwrap_chain.py =====
결과            : 바깥:안쪽:몸통
__name__        : base
한 겹 벗기면     : base 안쪽:몸통
두 겹 벗기면     : 몸통
inspect.unwrap  : 몸통
체인 길이        : 2 · 맨 밑: base
(exit 0)
```

```text
   base ----__wrapped__----> (안쪽 wrapper) ----__wrapped__----> 원래 base
     ^                            ^                                 ^
     바깥 wrapper                 한 겹 벗긴 것                      맨 밑

   inspect.unwrap(base) 는 이 화살표를 끝까지 따라간다  -> 체인 길이 2
```

- `base()` 가 `바깥:안쪽:몸통` 을 냈다 — **바깥이 먼저 손대고 안쪽이 나중**(동작 4의 순서 그대로).
- **`__wrapped__.__wrapped__`** 로 두 겹을 벗기면 `몸통` 만 남는다.
- `inspect.unwrap` 은 **같은 일을 한 번에** 한다.
- ★ **체인 길이가 2** 이고 맨 밑의 `__qualname__` 이 `base` 다 — **`wraps` 가 겹마다 하나씩 남긴 덕**이다.
  `wraps` 를 안 붙인 겹이 하나라도 있으면 **거기서 체인이 끊긴다.**

**비용** — `unwrap` 은 **래퍼가 하던 일을 건너뛴다.** 원본을 직접 부르면 로그도 캐시도 인증도 안 걸린다.
**들여다보는 용도**이지 **부르는 용도**가 아니다.

### 10. ★ 실체는 22번의 셀이다 — 데코레이터에 새로운 저장소는 없다

**언제 쓰나** — 「`times` 나 `fn` 은 도대체 어디에 저장되나」가 궁금할 때.

```python
# e24_closure_view.py
import functools


def limit(n):
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*a, **k):
            return fn(*a, **k)[:n]

        return wrapper

    return deco


@limit(2)
def letters():
    return ["a", "b", "c", "d"]


print("결과:", letters())
print("co_freevars      :", letters.__code__.co_freevars)
print("셀 개수          :", len(letters.__closure__))
cells = dict(zip(letters.__code__.co_freevars, letters.__closure__))
print("fn 셀이 가리키는 것:", cells["fn"].cell_contents.__name__)
print("n 셀이 가리키는 것 :", cells["n"].cell_contents)
print("__wrapped__ 와 같나:", cells["fn"].cell_contents is letters.__wrapped__)
```

```text
===== python3 - <e24_closure_view.py =====
결과: ['a', 'b']
co_freevars      : ('fn', 'n')
셀 개수          : 2
fn 셀이 가리키는 것: letters
n 셀이 가리키는 것 : 2
__wrapped__ 와 같나: True
(exit 0)
```

- `co_freevars` 가 `('fn', 'n')` — **래퍼가 바깥에서 빌려 쓰는 이름이 정확히 둘**이다.
- **셀이 2개**이고, `fn` 셀에는 원본 함수가, `n` 셀에는 `2` 가 들어 있다.
- ★★ **`fn` 셀의 내용이 `__wrapped__` 와 같은 객체다**(`True`).
  **`__wrapped__` 는 그 셀을 밖에서 읽을 수 있게 붙여 준 손잡이**인 셈이다.

```text
   @limit(2) 를 지난 뒤

     letters (이름)
        |
        v
     wrapper 함수 객체
        __code__.co_freevars = ('fn', 'n')
        __closure__ = ( 셀A , 셀B )
                        |      |
                        v      v
                   원래 letters  2
                        ^
                        __wrapped__ 도 여기를 가리킨다  (같은 객체)
```

★ **`__closure__`·`co_freevars` 는 CPython 구현이다** — 언어 보장이 아니다.
클로저가 있다는 것은 [21번](../21-scope-legb-global-nonlocal/2-summary.md)·[22번](../22-closures-and-late-binding/2-summary.md)의 이름 해소 규칙이 보장하지만,
**그것이 「셀」이라는 객체로 보인다는 것은 이 구현의 사정**이다.
★ **셀의 정본은 [22번](../22-closures-and-late-binding/2-summary.md)이다.** 여기서는 **「그것이 여기서 이렇게 쓰인다」만** 본다.

**비용** — 셀이 원본 함수를 붙들고 있으므로 **원본은 회수되지 않는다.** 감싼 함수를 들고 있는 한 원본도 살아 있다.

### 11. 클래스 데코레이터 — 같은 문법이 클래스에도 붙는다

**언제 쓰나** — `@dataclass` 류를 볼 때. **이름만 알면 된다.**

```python
# e24_class_deco.py
def tag(cls):
    cls.tagged = True
    return cls


@tag
class C:
    pass


print("클래스도 같은 문법으로 감싼다:", C.tagged, "· 타입:", type(C).__name__)
```

```text
===== python3 - <e24_class_deco.py =====
클래스도 같은 문법으로 감싼다: True · 타입: type
(exit 0)
```

클래스 데코레이터도 **똑같이** 「정의된 것을 받아 무엇이든 돌려주는」 함수다.
받는 것이 함수 객체 대신 **클래스 객체**일 뿐이다.

★ **여기서는 이름만 세운다.** 클래스 쪽의 정본은 `[목록의 **29번 주제**](../29-classes-and-attribute-lookup/)`(클래스 기초)와
`[목록의 **33번 주제**](../33-property-descriptor-slots/)`(디스크립터·속성)다.
★ `functools.lru_cache`·`cached_property` 처럼 **표준 라이브러리가 주는 데코레이터**는
`목록의 **45번 주제**` 가 정본이다.

## 문법 — 형태와 규칙

**형태 — 세 가지뿐이다**

```python
# ① 인자 없는 데코레이터 — 두 층
def deco(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)
    return wrapper

@deco
def f(): ...

# ② 인자 있는 데코레이터 — 세 층
def repeat(times):
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            return [fn(*args, **kwargs) for _ in range(times)]
        return wrapper
    return deco

@repeat(3)
def g(): ...

# ③ 클래스에 붙이기 — 받는 것이 클래스일 뿐 같은 문법
def tag(cls):
    cls.tagged = True
    return cls

@tag
class C: ...
```

규칙 여덟.

1. **`@식` 의 `식` 은 정의 시점에 평가**되고, 그 결과가 **함수 객체 하나를 인자로** 불린다.
2. **돌려받은 것이 그 이름에 묶인다.** 원래 함수는 **이름에 잠시도 안 묶인다.**
3. **돌려주는 것은 호출 가능해야** 쓸모가 있다 — 아니어도 정의는 통과하고, **부를 때** 터진다.
4. **여럿 쌓으면 적용은 아래에서 위로**, **호출은 위에서 아래로.** 결국 `바깥(가운데(안쪽(f)))`.
5. **래퍼는 `*args`·`**kwargs` 로 받고 `return` 을 잊지 않는다.**
6. **`@functools.wraps(fn)` 을 래퍼 위에 붙인다.** 여섯 칸을 대입하고 `__dict__` 를 합치고 `__wrapped__` 를 붙인다.
7. **인자 있는 데코레이터는 괄호가 필수다.** `@repeat` 과 `@repeat(3)` 은 전혀 다른 일을 한다.
8. **클래스에도 같은 문법이 붙는다**(2.6+).

**금지 사례 — 정의 때 조용히 지나가고 나중에 터지는 것들**

```python
# ① 인자 있는 데코레이터에서 괄호를 빠뜨린다
@repeat                 # repeat(hello) 가 불린다 -> times 자리에 함수가 들어앉는다
def hello(name): ...    # 정의 때 안 터진다. 부르고 또 불러야 TypeError

# ② 호출 가능하지 않은 것을 돌려준다
def to_string(fn):
    return "문자열"      # 정의 때 안 터진다
@to_string
def f(): ...            # f() 할 때 TypeError: 'str' object is not callable

# ③ 래퍼가 return 을 빼먹는다
def deco(fn):
    def wrapper(*a, **k):
        fn(*a, **k)     # 결과를 버린다 -> 모든 호출이 None
    return wrapper

# ④ wraps 를 안 붙인다
def deco(fn):
    def wrapper(*a, **k):   # __name__ 이 'wrapper' 가 되고 독스트링·주석·__dict__ 가 사라진다
        return fn(*a, **k)
    return wrapper
```

## 어디서 틀리나

### (1) ★ 인자 있는 데코레이터에 괄호를 빠뜨린다

**정의 때 아무 일도 안 난다.** 그게 이 실수의 고약한 점이다.

```python
# e24_missing_call.py
import functools


def repeat(times):
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*a, **k):
            return [fn(*a, **k) for _ in range(times)]

        return wrapper

    return deco


@repeat
def hello(name):
    return "안녕 " + name


print("hello 의 정체 :", hello.__name__, "·", type(hello).__name__)
print("한 번 부르면  :", hello("파이썬").__qualname__)
print("그것을 또 부르면 —")
hello("파이썬")()
```

```text
===== python3 - <e24_missing_call.py =====
hello 의 정체 : deco · function
한 번 부르면  : repeat.<locals>.deco.<locals>.wrapper
그것을 또 부르면 —
Traceback (most recent call last):
  File "<stdin>", line 23, in <module>
  File "<stdin>", line 8, in wrapper
TypeError: 'function' object cannot be interpreted as an integer
(exit 1)
```

```text
   @repeat            -> repeat(hello) 가 불린다
   def hello(...)        times 자리에 hello 함수가 들어앉는다
                         돌려받은 것은 deco 다 -> 이름 hello 가 deco 를 가리킨다

   hello("파이썬")     -> deco(fn="파이썬") 이 불린다 -> wrapper 를 돌려준다
                         ★ 여기서도 안 터진다

   그것을 또 부르면     -> range(times) 에서 times 가 함수다
                      -> TypeError: 'function' object cannot be interpreted as an integer
```

- `hello.__name__` 이 **`deco`** 다 — 이름만 찍어 봐도 어긋난 것이 보인다.
- **한 번 불렀더니 함수가 나왔다**(`repeat.<locals>.deco.<locals>.wrapper`). 에러가 아니라 **함수**다.
- **두 번째 호출에서야** `TypeError` 가 나고, 그 자리는 **`range(times)` 를 쓰는 줄**이다 —
  **틀린 곳과 터지는 곳이 다르다.**
- ★ **진단법 하나** — 데코레이터를 붙인 뒤 `f.__name__` 을 찍어 봐라.
  `wraps` 를 제대로 쓴 데코레이터라면 **원래 이름**이 나와야 한다.

### (2) ★ 호출 가능하지 않은 것을 돌려준다

```python
# e24_returns_nonfunction.py
def to_string(fn):
    return "함수가 아니라 문자열을 돌려줬다"


@to_string
def f():
    return 1


print("f 는 무엇인가:", repr(f), "· 타입:", type(f).__name__)
f()
```

```text
===== python3 - <e24_returns_nonfunction.py =====
f 는 무엇인가: '함수가 아니라 문자열을 돌려줬다' · 타입: str
Traceback (most recent call last):
  File "<stdin>", line 11, in <module>
TypeError: 'str' object is not callable
(exit 1)
```

- **정의는 통과한다.** `f` 가 그냥 **문자열**이 됐다(`type` 이 `str`).
- `f()` 하는 순간 `TypeError: 'str' object is not callable`.
- ★ 이것도 **틀린 곳과 터지는 곳이 다르다.** 레퍼런스가 "The result must be a callable" 이라고 적은 것은
  **데코레이터에 넣는 것**에 대한 말이고, **돌려주는 것은 검사되지 않는다.**
- ★ **가장 흔한 형태는 `return` 을 빼먹는 것**이다 — 그러면 `None` 이 돌아가
  `'NoneType' object is not callable` 이 난다. 같은 사고의 다른 얼굴이다.

### (3) 「`wraps` 를 빼면 전부 잃는다」로 안다

★ **`__module__` 은 안 잃는다** — 래퍼도 **같은 모듈에서 정의됐기 때문**이다.
「전부」가 아니라 **항목마다 다르다**는 것이 요점이고, 그 목록을 댈 수 있느냐가 이 주제의 과녁이다.

### (4) 「`wraps` 가 시그니처를 복사한다」로 안다

★ **복사하지 않는다.** `signature` 가 **`__wrapped__` 를 따라갔을 뿐**이고,
`follow_wrapped=False` 를 주면 **`(*a, **k)` 로 돌아간다.**
그래서 `wraps` 를 붙여도 **런타임 인자 검사는 여전히 원본이 불릴 때** 일어난다.

### (5) 「`__dict__` 가 옮겨진다」로 안다

★ **`update` 다.** 같은 dict 객체가 아니고, **래퍼가 나중에 붙인 것은 원본에 안 번진다.**
그리고 **감싼 뒤에 원본에 붙인 것은 래퍼에 안 보인다** — 복사는 **감쌀 때 한 번뿐**이다.

### (6) 스택 순서를 뒤집어 안다

★ **적용은 아래에서 위**, **호출은 위에서 아래**다.
외우지 말고 **괄호로 풀어 써라** — `@A @B def f` 는 `A(B(f))` 다.

### (7) 데코레이터 안에 무거운 준비 코드를 둔다

**임포트 시간에 전부 돈다.** 정의 시점이기 때문이다.
무거운 것은 **래퍼 안으로**(호출 시점) 옮기거나 지연 초기화로 미룬다.

### (8) 래퍼에서 `return` 을 빼먹는다

**모든 호출이 `None` 을 돌려준다.** 예외도 안 나서 **가장 오래 안 걸리는 버그**다.

### (9) 감싼 함수를 `unwrap` 해서 부른다

**래퍼가 하던 일이 전부 건너뛰어진다.** `unwrap` 은 **들여다보는 도구**다.

### (10) 데코레이터가 원본을 가두는 것을 잊는다

★ 셀이 원본을 붙들고 있다 — **감싼 쪽이 살아 있는 한 원본도 산다.**
`__wrapped__` 로도 그 참조가 하나 더 생긴다.

### (11) 「데코레이터는 함수를 고친다」로 안다

★ **원본은 한 글자도 안 바뀐다.** **이름이 다른 것을 가리키게 될 뿐**이다.
원본을 계속 쓰는 다른 이름이 있으면 그쪽은 **감싸이지 않은 채** 남는다.

### (12) 클래스 데코레이터를 다른 문법으로 안다

**같은 문법이다.** 받는 것이 클래스일 뿐이다.

## 구현 세부사항 대 언어 보장

세 층으로 가른다. ★ **이 주제는 「언어 보장」이 두껍다** — 등가식과 평가 시점이 레퍼런스에 그대로 있고,
`wraps` 가 무엇을 옮기는지는 `functools` 문서가 **목록으로** 준다.\
구현 쪽에 남는 것은 **셀의 겉모습**과 **예외 문구**다.

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **언어 보장** | 레퍼런스·PEP·라이브러리 문서가 정한 것 | 공식 문서 문장을 열어서 인용 |
| **CPython 구현** | 이 구현이 그렇게 하는 것 | `__closure__`·`co_freevars`·예외 문구 |
| **이 판의 관찰** | 3.12.3 에서 그랬을 뿐 | `WRAPPER_ASSIGNMENTS` 의 내용 · `__qualname__` 표기 |

### 언어 보장

| 사실 | 근거 |
|---|---|
| **`@deco` 는 `func = deco(func)` 와 같다** — 원래 함수가 **이름에 잠시도 안 묶이는 것**만 다르다 | 8.7 Function definitions |
| **데코레이터 식은 함수가 정의될 때 평가**되고, **정의를 감싸는 스코프**에서 평가된다 | 8.7 |
| 데코레이터에 넣는 것은 **호출 가능해야** 하고, **함수 객체 하나만** 인자로 받는다 | 8.7 |
| 돌려받은 값이 **함수 이름에 묶인다** | 8.7 |
| **여럿이면 중첩으로 적용된다**(`A(B(f))`) | 8.7 — *"applied in nested fashion"* |
| **클래스에도 같은 문법이 붙는다**(2.6+) | 8.8 Class definitions |
| `wraps` 가 옮기는 목록 = `WRAPPER_ASSIGNMENTS`, 합치는 목록 = `WRAPPER_UPDATES` | `functools` 문서 |
| `wraps` 가 **`__wrapped__` 를 자동으로 붙인다**(3.2+) | `functools` 문서 |
| `inspect.signature` 가 **`__wrapped__` 를 따라간다** — `follow_wrapped=False` 로 끌 수 있다 | `inspect` 문서 |

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| 래퍼의 `__closure__` 가 **셀 객체의 튜플**이고 `co_freevars` 에 이름이 있다 | 실행 — `('fn', 'n')` · 셀 2개 |
| `fn` 셀의 내용이 **`__wrapped__` 와 같은 객체**다 | 실행 — `is` 판정 `True` |
| `__qualname__` 이 `deco.<locals>.wrapper` 꼴로 **중첩 경로**를 적는다 | 실행 |
| `TypeError` 문구 — `'function' object cannot be interpreted as an integer` · `'str' object is not callable` | 실행 |
| `wraps` 가 붙인 `__wrapped__` 가 래퍼의 **`__dict__` 키로** 보인다 | 실행 |

### 이 판(3.12.3)의 관찰

| 관찰 | 어디가 흔들리나 |
|---|---|
| `WRAPPER_ASSIGNMENTS` 가 **여섯 개**이고 `__type_params__` 를 포함한다 | 판마다 늘 수 있다. **다른 판은 안 돌려 봤다** |
| `WRAPPER_UPDATES` 가 `('__dict__',)` 하나뿐이다 | 위와 같다 |
| 예외 **문구** 전부 | 종류는 명세, 문구는 아니다 |
| `__module__` 이 양쪽 다 `'__main__'` 인 것 | **같은 파일에서 정의했기 때문**이다. 다른 모듈 사례는 안 돌려 봤다 |

### 그래서 이렇게 적으면 틀린다

- ✗ 「데코레이터는 함수를 고친다」\
  ○ **원본은 안 바뀐다.** **이름이 다른 것을 가리키게** 될 뿐이다.
- ✗ 「데코레이터는 부를 때마다 돈다」\
  ○ **정의 시점에 한 번**이다. 부를 때 도는 것은 **래퍼**다.
- ✗ 「`wraps` 를 빼면 전부 잃는다」\
  ○ **`__module__` 은 안 잃는다.** 항목마다 다르다.
- ✗ 「`wraps` 가 `__wrapped__` 도 되살린다」\
  ○ **원본에 없던 것을 새로 붙이는** 것이다.
- ✗ 「`wraps` 가 시그니처를 복사한다」\
  ○ **`signature` 가 `__wrapped__` 를 따라갈 뿐**이다. `follow_wrapped=False` 면 `(*a, **k)`.
- ✗ 「`wraps` 가 `__dict__` 를 옮긴다」\
  ○ **`update` 로 합친다.** 같은 객체가 아니고 이후 변경은 서로 안 번진다.
- ✗ 「쌓은 순서대로 적용된다」\
  ○ **적용은 아래에서 위**, **호출은 위에서 아래**다.
- ✗ 「`@repeat` 과 `@repeat(3)` 은 비슷한 것」\
  ○ **전혀 다르다.** 괄호를 빼면 **함수가 `times` 자리에 앉고**, 엉뚱한 곳에서 `TypeError` 가 난다.
- ✗ 「데코레이터가 함수가 아닌 것을 돌려주면 정의에서 막힌다」\
  ○ **안 막힌다.** **부를 때** `not callable` 이 난다.
- ✗ 「`__closure__` 로 봤으니 어느 파이썬에서나 그렇다」\
  ○ **CPython 의 내성 인터페이스**다. 클로저는 명세, 셀의 모양은 아니다.

**판정 기준 한 줄**: **「지금 도는 것이 데코레이터인가 래퍼인가」를 물으면 시점이 갈리고,
「이 칸이 원본에도 있었나」를 물으면 `wraps` 가 옮긴 것과 새로 붙인 것이 갈린다.**

## 언제 쓰고 언제 안 쓰나

| 상황 | 판정 |
|---|---|
| 여러 함수에 **같은 앞뒤 처리**(로그·시간 측정·인증)를 붙인다 | ★ **데코레이터가 제자리다** |
| 붙일 곳이 **한 군데뿐**이다 | **그냥 그 함수 안에 쓴다** — 층을 늘릴 이유가 없다 |
| 감싸면서 **설정값**을 주고 싶다 | **인자 있는 데코레이터**(세 층). 괄호를 잊지 마라 |
| **원본 시그니처가 문서·IDE 에 보여야** 한다 | ★ **`functools.wraps` 필수** |
| 감싼 뒤 **원본을 꺼내야** 한다 | `__wrapped__` · `inspect.unwrap` — **들여다보기 전용** |
| **캐시**를 붙이고 싶다 | 직접 만들지 말고 `functools.lru_cache`(`목록의 **45번 주제**`) |
| **클래스 전체**에 붙이고 싶다 | 클래스 데코레이터 — 정본은 `[목록의 **29번 주제**](../29-classes-and-attribute-lookup/)`·`[목록의 **33번 주제**](../33-property-descriptor-slots/)` |
| 데코레이터 안에서 **무거운 준비**를 한다 | ★ **래퍼 안으로 옮긴다** — 정의 시점은 임포트 시간이다 |
| **부분 적용**이 필요할 뿐이다 | `functools.partial`(`목록의 **45번 주제**`) — 감싸는 것이 아니다 |
| 감싼 함수를 **동등성·`is` 로 비교**하는 코드가 있다 | ★ **안 된다** — 이름이 가리키는 객체가 **다른 객체**다 |

## 핵심 문장

- ★★ **`@deco` 는 `f = deco(f)` 다.** 새 문법이 아니라 **줄임**이고, 다른 점은
  **원래 함수가 이름에 잠시도 안 묶인다**는 것 하나뿐이다(레퍼런스가 그렇게 적는다).
- ★★ **데코레이터는 정의 시점에 한 번 돈다.** 부를 때 도는 것은 래퍼다.
  [20번](../20-mutable-default-args/2-summary.md)의 기본값과 **같은 시점**이다 — `def` 문은 실행되는 문장이다.
- ★★ **적용은 아래에서 위, 호출은 위에서 아래.** 괄호로 풀면 `바깥(가운데(안쪽(f)))` 이고,
  출력에 **여섯 줄이 대칭**으로 찍히는 것이 그 근거다.
- ★★ **`functools.wraps` 없이 잃는 것** — `__name__`·`__qualname__`·`__doc__`·`__annotations__`·`__dict__`.
  ★ **`__module__` 은 안 잃는다**(래퍼도 같은 모듈이라서). ★ **`__wrapped__` 는 잃는 게 아니라 새로 붙는 것**이다.
- ★ **`__dict__` 만 성격이 다르다** — **대입이 아니라 `update`** 다. `WRAPPER_UPDATES` 가 `('__dict__',)` 인 이유고,
  같은 dict 객체가 아니며 **이후 변경은 서로 안 번진다.**
- ★ **`wraps` 는 시그니처를 복사하지 않는다.** `inspect.signature` 가 **`__wrapped__` 를 따라간** 것이고,
  `follow_wrapped=False` 를 주면 **`(*a, **k)` 로 돌아간다.**
- ★ **인자 있는 데코레이터는 층이 셋**이다 — `repeat(3)` 이 돌고, `deco` 가 돌고, `wrapper` 는 부를 때만.
  앞의 둘은 **정의 시점에 붙어서** 일어난다.
- ★ **괄호를 빠뜨리면 정의 때 조용히 지나간다.** 함수가 `times` 자리에 앉고,
  **엉뚱한 줄에서** `'function' object cannot be interpreted as an integer` 가 난다.
- ★ **데코레이터는 호출 가능하지 않은 것도 돌려줄 수 있다** — 정의는 통과하고 **부를 때** `not callable` 이 난다.
- ★ **실체는 [22번](../22-closures-and-late-binding/2-summary.md)의 셀이다** — `co_freevars` 가 `('fn', 'n')`,
  셀이 둘, `fn` 셀의 내용이 **`__wrapped__` 와 같은 객체**다. 단 **셀은 CPython 구현**이다.

## 관련 자료

- 목록: [python/syntax 주제 목록](../README.md) — 이 주제는 **24번**
- 선행: [19-function-argument-rules](../19-function-argument-rules/2-summary.md) — `*args`·`**kwargs`·`inspect.signature`.\
  **경계**: 「어떤 호출이 되고 안 되나」는 그쪽, 「감싼 뒤에도 그 시그니처가 보이나」는 여기다.
- 선행: [20-mutable-default-args](../20-mutable-default-args/2-summary.md) — **「`def` 문이 돌 때 한 번」의 정본.**\
  **경계**: 그 성질 자체와 가변 기본값 함정은 전부 그쪽이다. 여기는 **데코레이터도 같은 시점에 돈다**는 한 줄만.
- 선행: [21-scope-legb-global-nonlocal](../21-scope-legb-global-nonlocal/2-summary.md) — 이름이 어디서 풀리나.\
  **경계**: 데코레이터 식이 **정의를 감싸는 스코프**에서 평가된다는 것이 그 규칙의 적용이다.
- 선행: [22-closures-and-late-binding](../22-closures-and-late-binding/2-summary.md) — **셀의 정본.**\
  **경계**: 셀·자유 변수·늦은 바인딩은 전부 그쪽. 여기는 **래퍼의 셀 둘을 꺼내 보는 것**까지다.
- 선행: [23-lambda-and-higher-order-functions](../23-lambda-and-higher-order-functions/2-summary.md) — 함수를 값으로 넘기고 돌려받는 것.\
  **경계**: 데코레이터는 **고차 함수의 특수한 경우**에 문법 설탕이 붙은 것이다.
- 함께 보는 곳: [03-mutability-and-copying](../03-mutability-and-copying/2-summary.md) — `__dict__` 를 `update` 하는 것이 **얕은 복사**다.
- 이어지는 곳: `[목록의 **29번 주제**](../29-classes-and-attribute-lookup/)` · `[목록의 **33번 주제**](../33-property-descriptor-slots/)` — **클래스 데코레이터의 정본.**
- 이어지는 곳: `목록의 **45번 주제**` — `functools.lru_cache`·`cached_property`·`partial`.
- 이어지는 곳: `목록의 **40번 주제**` — 타입 힌트. `wraps` 가 `__annotations__` 를 옮기는 이유가 거기 있다.
- 공식 문서: [Function definitions](https://docs.python.org/3.12/reference/compound_stmts.html#function-definitions) ·
  [`functools.wraps`](https://docs.python.org/3.12/library/functools.html#functools.wraps) ·
  [`inspect.signature`](https://docs.python.org/3.12/library/inspect.html#inspect.signature) ·
  [PEP 318](https://peps.python.org/pep-0318/)

## 용어 풀이

- **데코레이터(decorator)**: `def`·`class` 위에 `@` 로 붙이는 **호출 가능한 것**. 정의된 객체를 받아 무엇이든 돌려준다.\
  예: `@deco` 는 `f = deco(f)` 와 같다.
- **문법 설탕(syntactic sugar)**: 없어도 되는데 읽기 좋으라고 있는 문법.\
  예: `@deco` 가 그것이다 — 손으로 풀어 쓸 수 있다.
- **래퍼(wrapper)**: 원본을 품고 대신 불리는 함수. 보통 `*args`·`**kwargs` 로 받는다.\
  예: `__qualname__` 이 `deco.<locals>.wrapper` 로 찍힌다.
- **정의 시점(definition time)**: `def` 문이 **실행되는** 순간. 데코레이터와 기본값이 여기서 돈다.\
  예: 임포트만 해도 데코레이터가 돈다.
- **데코레이터 팩토리(인자 있는 데코레이터)**: 데코레이터를 **만들어 돌려주는** 함수. 층이 셋이 된다.\
  예: `repeat(3)` 이 `deco` 를 돌려주고, `deco(fn)` 이 `wrapper` 를 돌려준다.
- **`functools.wraps(fn)`**: 래퍼 위에 붙이는 데코레이터. 원본의 표식을 래퍼로 옮긴다.\
  예: `@functools.wraps(fn)` 한 줄이면 `help()` 가 되살아난다.
- **`functools.update_wrapper`**: `wraps` 가 실제로 하는 일. `wraps` 는 그것의 데코레이터 판이다.
- **`WRAPPER_ASSIGNMENTS`**: **대입**되는 속성 목록. 이 판에서 여섯 개다.
- **`WRAPPER_UPDATES`**: **합쳐지는**(`update`) 속성 목록. `('__dict__',)` 하나뿐이다.
- **`__wrapped__`**: `wraps` 가 래퍼에 새로 붙이는 속성. **원본을 가리킨다.**\
  예: 겹겹이 쌓으면 **체인**이 된다.
- **`inspect.unwrap(f)`**: `__wrapped__` 체인을 **끝까지** 따라가 맨 밑을 꺼낸다.
- **`follow_wrapped`**: `inspect.signature` 의 인자. `False` 면 `__wrapped__` 를 **안 따라간다.**\
  예: `wraps` 를 붙여도 `(*a, **k)` 가 나온다.
- **셀(cell)**: 바깥 함수의 지역 이름을 **안쪽 함수와 나눠 갖는 상자**. CPython 구현.\
  예: 래퍼의 `__closure__` 에 `fn`·`n` 두 셀이 있다.
- **호출 가능(callable)**: `()` 를 붙여 부를 수 있는 것. 함수·클래스·`__call__` 이 있는 객체.\
  예: 데코레이터가 문자열을 돌려주면 **부를 때** `not callable` 이 난다.
- **클래스 데코레이터**: 클래스 정의 위에 붙는 같은 문법(2.6+). 받는 것이 클래스 객체다.

## 더 들어가면

- **클래스로 만드는 데코레이터** — `__call__` 이 있는 객체도 호출 가능하므로 데코레이터가 될 수 있다.
  이 주제에서는 **안 돌려 봤다.** 정본은 `[목록의 **33번 주제**](../33-property-descriptor-slots/)` 다.
- **메서드에 붙일 때가 까다롭다** — `@staticmethod`·`@classmethod`·`@property` 는
  **디스크립터**를 돌려주는 특수한 데코레이터라 **순서가 걸린다.** 여기서는 안 다뤘다(`[목록의 **33번 주제**](../33-property-descriptor-slots/)`).
- ★ **`wraps` 가 있어도 래퍼는 여전히 `(*a, **k)` 를 받는다** — 보이는 시그니처와 실제 받는 것이 다르다.
  **엄격히 맞추려면** 래퍼 자체를 원본과 같은 시그니처로 쓰거나, `inspect.Signature.bind` 로 **직접 검사**해야 한다.
- ★ **데코레이터를 껐다 켤 수 있게 만드는 흔한 방법**은 래퍼 안에서 플래그를 보는 것이다.
  **데코레이터 바깥에서 분기하면 정의 시점에 굳어** 나중에 못 바꾼다 — 정의 시점과 호출 시점의 차이가 그대로 설계가 된다.
- **`__wrapped__` 를 손으로 붙여도 된다** — `signature` 는 그것만 보고 따라간다.
  `wraps` 를 안 쓰는 래퍼에도 이 한 줄을 붙이면 문서 도구가 원본을 찾는다. **이 주제에서 그렇게는 안 돌려 봤다.**
