# python/syntax/28-context-managers-and-with — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만.
> - [8.5. The `with` statement](https://docs.python.org/3.12/reference/compound_stmts.html#the-with-statement) — **등가식**과 `__exit__` 반환값의 계약
> - [3.3.9. With Statement Context Managers](https://docs.python.org/3.12/reference/datamodel.html#with-statement-context-managers) — `__enter__`·`__exit__` 의 계약
> - [3.3.1. Special method lookup](https://docs.python.org/3.12/reference/datamodel.html#special-method-lookup) — **특수 메서드는 타입에서 찾는다**
> - [`contextlib`](https://docs.python.org/3.12/library/contextlib.html) — `contextmanager`·`suppress`·`closing`·`ExitStack`
> - [PEP 343 — The "with" Statement](https://peps.python.org/pep-0343/) · [PEP 617 로 들어온 괄호 다중 `with`(3.10)](https://docs.python.org/3.12/whatsnew/3.10.html#parenthesized-context-managers)
>
> **실행 검증** — 이 문서에 실린 출력은 전부 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.\
> ★ **던지는 형태를 하나로 고정했다** — `python3 - <파일` 로 던져 트레이스백이 `File "<stdin>", line N` 이 된다.
> ★★ **이 주제는 트레이스백을 한 블록도 싣지 않았다** — `contextlib` 안에서 난 예외의 트레이스백에는
> **`/usr/lib/python3.12/contextlib.py` 라는 절대경로가 박혀** 다른 머신에서 재현이 안 되기 때문이다.
> 대신 **예외의 타입·메시지·`__context__` 사슬을 찍어** 같은 사실을 결정적으로 보였다.\
> **버전** — `with` 는 **2.5+**(PEP 343), `contextlib.ExitStack` 은 **3.3+**, `suppress` 는 **3.4+**.
> 갈리는 것 하나 — **괄호로 감싼 다중 `with` 가 3.10 부터**다(그 전에는 역슬래시가 필요했다).
> 3.9 이하는 이 머신에 없어 **옛 판의 `SyntaxError` 는 직접 못 돌려 봤다** — 문서 근거다.\
> **구현 대 언어 보장 한 줄** — **등가식·`__exit__` 반환값의 계약·해제 역순·`__enter__` 실패 시 `__exit__` 미호출까지가 언어 보장**이고,
> **`ExitStack` 이 정리 중 예외를 어떻게 잇는지는 CPython `contextlib` 의 구현**이다.\
> **★ 흔들리는 칸 / 안 흔들리는 칸** — 재대조에서 「고칠 것」과 「설계상 안 맞는 것」을 기계적으로 가르려고 미리 선언한다.
>
> | 흔들린다 | 안 흔들린다(근거로 써도 되는 칸) |
> |---|---|
> | (판이 오르면) `_GeneratorContextManager` 같은 **내부 클래스 이름** | `__enter__`·`__exit__` 가 **불렸나 안 불렸나** |
> | (판이 오르면) 예외 **문구** 전부 | 예외 **종류** · **열림/닫힘 마커의 순서** · 종료 코드 |
> | (판이 오르면) `ExitStack` 의 **`__context__` 사슬 길이** | `__exit__` 반환값의 **참·거짓에 따른 삼킴 여부** |
> | — | **해제가 역순이라는 것** · `__enter__` 실패 시 그 객체의 `__exit__` 가 **안 도는 것** |
>
> ★ **이 주제의 블록에는 주소도 시간도 절대경로도 한 곳도 안 찍힌다.** 같은 판에서 다시 돌리면 **한 글자도 안 변한다.**\
> **선행** — [25-exceptions-and-finally](../25-exceptions-and-finally/2-summary.md)(**`try/finally` 의 정본**) ·
> [17-generators-yield](../17-generators-yield/2-summary.md)(`yield` 자리로 예외를 던지는 것) ·
> [24-decorators](../24-decorators/2-summary.md)(**`@contextmanager` 가 데코레이터다**) ·
> [05-truthiness-and-short-circuit](../05-truthiness-and-short-circuit/2-summary.md)(**`__exit__` 반환값은 「참」이지 「`True`」가 아니다**).\
> **이 사슬** — [25](../25-exceptions-and-finally/2-summary.md) → [26](../26-eafp-vs-lbyl/2-summary.md) → [27](../27-exception-groups-and-except-star/2-summary.md) → 28.
> **여기가 사슬의 끝이다** — 25 의 `try/finally` 를 **객체로 굳혀** 재사용 가능하게 만든 것이 `with` 다.

## 한눈에 — 쉽게 말하면

**`with` 는 「`try/finally` 를 객체에 넣어 이름 붙인 것」이다.**

- `__enter__` — 열고, **`as` 에 줄 값을 돌려준다**(자기 자신이 아니어도 된다).
- `__exit__` — 닫는다. **나가는 모든 길에서** 불린다 — 25번의 `finally` 자리다.
- ★★ 다른 점 하나 — **`__exit__` 는 예외를 볼 수 있고, 참을 돌려주면 삼킨다.**
  `finally` 에는 그런 스위치가 없다.

```text
   try / finally                      with

   try:                               with 객체 as x:      <- __enter__() 가 x 를 준다
       몸통                               몸통
   finally:                           (나가는 길)          <- __exit__(타입, 값, tb)
       정리                                                   참을 돌려주면 예외를 삼킨다

   ★ finally 는 예외를 못 삼킨다(나가야 삼켜진다 — 25번)
     __exit__ 는 "참을 돌려주는 것" 만으로 삼킨다
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 문을 연다 | `__enter__` | 마커 「열림」이 찍힌다 |
| 손에 쥐여 주는 것 | `__enter__` 의 **반환값** | `as` 가 받는 것 — **객체 자신이 아니어도 된다** |
| 나가면서 문을 닫는다 | `__exit__` | 마커 「닫힘」이 찍힌다 |
| ★ **닫으면서 「없던 일로」라고 말한다** | `__exit__` 가 **참**을 돌려준다 | `with` 다음 줄까지 간다 |
| 여러 문을 지나왔다 | 다중 `with` | **닫히는 순서가 역순**이다 |
| ★ **못 연 문은 닫지 않는다** | `__enter__` 가 터지면 | 그 객체의 `__exit__` 가 **안 돈다** |
| 문이 몇 개일지 실행 중에 안다 | `ExitStack` | `enter_context` 로 쌓는다 |
| 문지기를 제너레이터로 쓴다 | `@contextmanager` | `yield` 앞이 열기, 뒤가 닫기 |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.\
「**`__exit__` 에서 실수로 참을 돌려줬더니 예외가 전부 사라졌다**」와
「**`@contextmanager` 에서 `try/finally` 를 빼먹어 몸통이 터지면 정리가 안 됐다**」가 그것이다.\
둘 다 **정상 경로에서는 멀쩡해 보인다** — 예외가 날 때만 드러난다.

> **컨텍스트 매니저(context manager)** — `__enter__` 와 `__exit__` 를 **타입에** 가진 객체.\
> 예: 파일 객체, `threading.Lock`, `contextlib.suppress(...)`.

> **등가식(desugaring)** — 문법 설탕을 원래 형태로 풀어 쓴 것.\
> 예: `with A() as x:` 는 `__enter__`/`__exit__` 를 부르는 `try/finally` 로 풀린다.

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

1. **`__enter__`·`__exit__` 의 계약이 정확히 무엇인가** — `as` 가 받는 것은 무엇이고, `__exit__` 는 무엇을 받나.
2. **예외는 언제 삼켜지는가** — `True` 를 돌려줘야만 삼켜지나.
3. **여러 개를 열었는데 중간에 실패하면** — 무엇이 닫히고 무엇이 안 닫히나.

★ 둘째·셋째 질문이 이 주제의 인출 목표다. **「`__exit__` 가 참을 돌려주면 삼킨다」와 「못 연 것은 안 닫는다」를 대는 것**이 아는 것과 들은 것의 경계다.

## 동작 방식

> 이 절이 본문이다. 이 주제의 네 번째 창은 **「불렸나 안 불렸나」 마커**다 —
> `with` 는 **정상 경로에서는 어느 구현이나 똑같아 보인다.**
> 갈리는 것은 **예외가 났을 때**와 **여는 도중 실패했을 때**이고,
> 그것은 **`__enter__`·`__exit__` 안에 마커를 박아야만** 보인다.

### 1. ★ 계약 — `as` 가 받는 것과 `__exit__` 가 받는 것

**언제 쓰나** — 컨텍스트 매니저를 직접 쓸 때. 그리고 「`as f` 의 `f` 가 뭐지」가 막힐 때.

레퍼런스가 등가식을 준다.

> The execution of the `with` statement … proceeds as follows.
> 1. The context expression … is evaluated to obtain a context manager.
> 2. The context manager's `__enter__()` is loaded for later use.
> 3. The context manager's `__exit__()` is loaded for later use.
> 4. The context manager's `__enter__()` method is invoked. …
> 6. The suite is executed. …
> 7. The context manager's `__exit__()` method is invoked.

```text
   with 객체 as x:
       몸통

   ① 객체를 만든다
   ② type(객체).__enter__ 를 찾는다      <- ★ 인스턴스가 아니라 타입에서
   ③ type(객체).__exit__ 를 찾는다       <- ★ 여기서 없으면 몸통을 돌기 전에 터진다
   ④ __enter__() 를 부른다 -> 그 반환값이 x
   ⑤ 몸통
   ⑥ __exit__(타입, 값, 트레이스백) 을 부른다
        예외가 없었으면 (None, None, None)
```

```python
# e28_contract.py
class Trace:
    def __init__(self, name):
        self.name = name

    def __enter__(self):
        print("  __enter__", self.name, "— 돌려주는 것: 문자열 '자원'")
        return "자원"

    def __exit__(self, exc_type, exc_value, tb):
        print("  __exit__ ", self.name,
              "— 받은 것:", (exc_type.__name__ if exc_type else None,
                           repr(exc_value) if exc_value else None,
                           "tb 있음" if tb else None))
        return False


print("① 예외 없이 지나갈 때")
with Trace("A") as got:
    print("  몸통 — as 가 받은 것:", repr(got))
print("  with 문 다음 줄")

print("② 몸통에서 예외가 날 때")
try:
    with Trace("B") as got:
        raise ValueError("몸통이 터졌다")
except ValueError as e:
    print("  바깥에서 잡힘:", e)
```

```text
===== python3 - <e28_contract.py =====
① 예외 없이 지나갈 때
  __enter__ A — 돌려주는 것: 문자열 '자원'
  몸통 — as 가 받은 것: '자원'
  __exit__  A — 받은 것: (None, None, None)
  with 문 다음 줄
② 몸통에서 예외가 날 때
  __enter__ B — 돌려주는 것: 문자열 '자원'
  __exit__  B — 받은 것: ('ValueError', "ValueError('몸통이 터졌다')", 'tb 있음')
  바깥에서 잡힘: 몸통이 터졌다
(exit 0)
```

- ★ **`as` 가 받은 것은 객체 자신이 아니라 `'자원'` 이라는 문자열**이다.
  **`__enter__` 가 돌려주는 것이면 무엇이든** 된다.
- 예외가 없으면 `__exit__` 가 **`(None, None, None)`** 을 받는다.
- 예외가 나면 **타입·값·트레이스백 셋**을 받는다. 그리고 `False` 를 돌려줬으므로 **밖으로 나갔다.**

**비용** — 메서드 둘을 써야 한다. 그 값으로 **정리를 잊을 수 없게** 만든다.

### 2. ★★ `__exit__` 의 반환값 — 「`True`」가 아니라 「**참**」이다

**언제 쓰나** — `__exit__` 를 쓸 때마다. 이 주제에서 가장 비싼 실수가 여기 있다.

레퍼런스가 못 박는다.

> If the suite was exited due to an exception, and the return value from the `__exit__()` method was false,
> the exception is reraised. If the return value was true, the exception is suppressed,
> and execution continues with the statement following the `with` statement.

**「참(true)」이지 「`True`」가 아니다.** 일곱 가지를 던져 확인했다.

```python
# e28_exit_return.py
class Ret:
    def __init__(self, value):
        self.value = value

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        print("    __exit__ 가 받은 예외:", exc_type.__name__ if exc_type else None,
              "· 돌려주는 것:", repr(self.value))
        return self.value


for value in (True, False, None, 1, 0, "빈 문자열이 아닌 문자열", ""):
    print("[ __exit__ 가", repr(value), "를 돌려줄 때 ]")
    try:
        with Ret(value):
            raise ValueError("몸통이 터졌다")
        print("    with 다음 줄까지 왔다 — 예외가 삼켜졌다")
    except ValueError:
        print("    바깥까지 나왔다 — 안 삼켜졌다")
```

```text
===== python3 - <e28_exit_return.py =====
[ __exit__ 가 True 를 돌려줄 때 ]
    __exit__ 가 받은 예외: ValueError · 돌려주는 것: True
    with 다음 줄까지 왔다 — 예외가 삼켜졌다
[ __exit__ 가 False 를 돌려줄 때 ]
    __exit__ 가 받은 예외: ValueError · 돌려주는 것: False
    바깥까지 나왔다 — 안 삼켜졌다
[ __exit__ 가 None 를 돌려줄 때 ]
    __exit__ 가 받은 예외: ValueError · 돌려주는 것: None
    바깥까지 나왔다 — 안 삼켜졌다
[ __exit__ 가 1 를 돌려줄 때 ]
    __exit__ 가 받은 예외: ValueError · 돌려주는 것: 1
    with 다음 줄까지 왔다 — 예외가 삼켜졌다
[ __exit__ 가 0 를 돌려줄 때 ]
    __exit__ 가 받은 예외: ValueError · 돌려주는 것: 0
    바깥까지 나왔다 — 안 삼켜졌다
[ __exit__ 가 '빈 문자열이 아닌 문자열' 를 돌려줄 때 ]
    __exit__ 가 받은 예외: ValueError · 돌려주는 것: '빈 문자열이 아닌 문자열'
    with 다음 줄까지 왔다 — 예외가 삼켜졌다
[ __exit__ 가 '' 를 돌려줄 때 ]
    __exit__ 가 받은 예외: ValueError · 돌려주는 것: ''
    바깥까지 나왔다 — 안 삼켜졌다
(exit 0)
```

★★ **표로 굳히면 이렇다.**

| 돌려준 값 | 진릿값 | 예외가 | 왜 |
|---|---|---|---|
| `True` | 참 | ★ **삼켜진다** | — |
| `False` | 거짓 | 나간다 | — |
| `None` | 거짓 | 나간다 | ★ **`return` 을 빼먹으면 이것**이다 |
| `1` | 참 | ★ **삼켜진다** | 진릿값 판정이다 |
| `0` | 거짓 | 나간다 | 〃 |
| `'빈 문자열이 아닌 문자열'` | 참 | ★ **삼켜진다** | 〃 |
| `''` | 거짓 | 나간다 | 〃 |

- ★★ **`if` 에 넣었을 때 참인 것은 전부 삼킨다.**
  [05번](../05-truthiness-and-short-circuit/2-summary.md)의 진릿값 규칙이 **그대로** 쓰인다.
- ★ **`return` 을 빼먹으면 `None` 이라 안 삼킨다** — 다행히 **기본값이 안전한 쪽**이다.
- ★ 위험한 것은 반대다 — **`__exit__` 안에서 무심코 무언가를 `return` 하면** 예외가 사라진다.
  로그 함수의 반환값을 그대로 돌려주는 실수가 그 모양이다.

```text
   __exit__ 가 돌려준 값
        |
   bool(값) 이 참인가?
      /            \
    예              아니오
     |                |
  예외를 삼킨다     예외를 다시 던진다
  with 다음 줄로     밖으로 나간다

   ★ "True 인가" 가 아니라 "참인가" 다
```

**비용** — 없다. **`return False` 를 명시**하거나 **아무것도 안 돌려주면** 된다.

### 3. ★ 해제는 **역순** — 다중 `with` 와 중첩 `with` 가 같다

**언제 쓰나** — 파일과 락을 함께 잡을 때. 순서가 의심될 때.

```text
   with A, B, C:          열림: A -> B -> C
       몸통                닫힘: C -> B -> A        ★ 역순

   등가:
   with A:
       with B:
           with C:
               몸통
```

```python
# e28_nested_order.py
class M:
    def __init__(self, name):
        self.name = name

    def __enter__(self):
        print("  열림:", self.name)
        return self

    def __exit__(self, *exc):
        print("  닫힘:", self.name)
        return False


print("① 한 with 에 셋 — 괄호 문법은 3.10+")
with (M("A"), M("B"), M("C")):
    print("  몸통")

print("② 중첩해서 쓴 것 — 같은 순서인가")
with M("A"):
    with M("B"):
        with M("C"):
            print("  몸통")

print("③ 몸통이 터져도 역순으로 닫힌다")
try:
    with M("A"), M("B"), M("C"):
        raise ValueError("몸통이 터졌다")
except ValueError as e:
    print("  바깥에서 잡힘:", e)
```

```text
===== python3 - <e28_nested_order.py =====
① 한 with 에 셋 — 괄호 문법은 3.10+
  열림: A
  열림: B
  열림: C
  몸통
  닫힘: C
  닫힘: B
  닫힘: A
② 중첩해서 쓴 것 — 같은 순서인가
  열림: A
  열림: B
  열림: C
  몸통
  닫힘: C
  닫힘: B
  닫힘: A
③ 몸통이 터져도 역순으로 닫힌다
  열림: A
  열림: B
  열림: C
  닫힘: C
  닫힘: B
  닫힘: A
  바깥에서 잡힘: 몸통이 터졌다
(exit 0)
```

- ★ **①과 ②의 출력이 한 글자도 같다.** 다중 `with` 는 **중첩 `with` 의 문법 설탕**이다.
- ★ ③에서 **몸통이 터져도 역순**으로 닫혔다. 그리고 「몸통」이 안 찍혔다 — 터졌으니 당연하다.
- ★ **괄호로 감싼 형태는 3.10+** 다(`with (A(), B(), C()):`). 그 전에는 역슬래시가 필요했다 —
  **옛 판은 안 돌려 봤다.**

**비용** — 없다. 다만 **순서가 계약이다** — 락을 먼저 잡고 파일을 열었으면 **파일이 먼저 닫힌다.**

### 4. ★★ `__enter__` 가 터지면 그 객체의 `__exit__` 는 **안 돈다**

**언제 쓰나** — 여는 것 자체가 실패할 수 있을 때(연결·락 획득). 자원 누수의 고전적 자리다.

등가식이 이유를 그대로 말한다 — **`try` 는 `__enter__()` 가 끝난 뒤에 시작한다.**

```text
   ② __exit__ 를 찾아 둔다
   ③ __enter__() 를 부른다     <- ★ 여기서 터지면 아직 try 밖이다
   ④ try:
   ⑤     몸통
   ⑥ finally:
   ⑦     __exit__(...)         <- 그래서 이 줄에 못 온다
```

```python
# e28_enter_fails.py
class Good:
    def __enter__(self):
        print("  Good.__enter__")
        return self

    def __exit__(self, *exc):
        print("  Good.__exit__  <- 이건 돈다")
        return False


class BadEnter:
    def __enter__(self):
        print("  BadEnter.__enter__ — 여기서 터진다")
        raise RuntimeError("자원을 못 열었다")

    def __exit__(self, *exc):
        print("  BadEnter.__exit__  <- 이 줄이 찍히면 안 된다")
        return False


print("① __enter__ 가 터지면 그 객체의 __exit__ 는 안 돈다")
try:
    with BadEnter():
        print("  몸통 — 안 돈다")
except RuntimeError as e:
    print("  바깥에서 잡힘:", e)

print("② 앞에서 이미 연 것은 닫힌다")
try:
    with Good(), BadEnter():
        print("  몸통 — 안 돈다")
except RuntimeError as e:
    print("  바깥에서 잡힘:", e)
```

```text
===== python3 - <e28_enter_fails.py =====
① __enter__ 가 터지면 그 객체의 __exit__ 는 안 돈다
  BadEnter.__enter__ — 여기서 터진다
  바깥에서 잡힘: 자원을 못 열었다
② 앞에서 이미 연 것은 닫힌다
  Good.__enter__
  BadEnter.__enter__ — 여기서 터진다
  Good.__exit__  <- 이건 돈다
  바깥에서 잡힘: 자원을 못 열었다
(exit 0)
```

- ★★ ①에서 **`BadEnter.__exit__` 가 안 찍혔다.** 못 연 문은 안 닫는다.
- ★ ②에서 **앞에서 이미 연 `Good` 은 닫혔다.** 다중 `with` 는 **이미 성공한 것만** 되감는다.
- 그래서 **`__enter__` 안에서 자원을 여럿 잡으면 안 된다** — 두 번째에서 터지면 **첫 번째가 새어 나간다.**
  그 자리에 쓰는 것이 `ExitStack` 이다(동작 8).

**비용** — 없다. **계약을 알고 쓰면 된다.**

### 5. ★ 특수 메서드는 **타입에서** 찾는다

**언제 쓰나** — 인스턴스에 `__enter__` 를 달아 두고 안 된다고 할 때. 그리고 **에러 문구가 셋으로 갈리는 것**을 볼 때.

레퍼런스가 규칙을 적는다.

> For custom classes, implicit invocations of special methods are only guaranteed to work correctly
> if defined on an object's type, not in the object's instance dictionary.

```python
# e28_protocol_lookup.py
class OnlyEnter:
    def __enter__(self):
        return self


class OnlyExit:
    def __exit__(self, *exc):
        return False


class OnInstance:
    pass


obj = OnInstance()
obj.__enter__ = lambda: obj
obj.__exit__ = lambda *exc: False


def try_with(label, thing):
    print("[", label, "]")
    try:
        with thing:
            print("    몸통이 돌았다")
    except TypeError as e:
        print("    TypeError:", e)


try_with("__exit__ 만 없다", OnlyEnter())
try_with("__enter__ 만 없다", OnlyExit())
try_with("인스턴스에만 달아 둔 것", obj)
print("인스턴스에 실제로 달려 있나:", hasattr(obj, "__enter__"), hasattr(obj, "__exit__"))
print("클래스에 달려 있나        :", hasattr(type(obj), "__enter__"), hasattr(type(obj), "__exit__"))
```

```text
===== python3 - <e28_protocol_lookup.py =====
[ __exit__ 만 없다 ]
    TypeError: 'OnlyEnter' object does not support the context manager protocol (missed __exit__ method)
[ __enter__ 만 없다 ]
    TypeError: 'OnlyExit' object does not support the context manager protocol
[ 인스턴스에만 달아 둔 것 ]
    TypeError: 'OnInstance' object does not support the context manager protocol
인스턴스에 실제로 달려 있나: True True
클래스에 달려 있나        : False False
(exit 0)
```

- ★★ **셋이 다른 문구를 낸다.** 특히 첫 줄이 **`(missed __exit__ method)`** 까지 말해 준다 —
  **`__exit__` 가 먼저 준비되기 때문**이다(등가식 ③).
- ★ 셋째 줄이 규칙의 증거다 — **인스턴스에는 둘 다 달려 있는데**(`True True`)
  **클래스에는 없어서**(`False False`) 안 된다.
- ★ 그래서 **`hasattr(obj, "__enter__")` 로 「컨텍스트 매니저인가」를 판정하면 틀린다.**

**비용** — 없다. **클래스에 정의하면 된다.**

### 6. ★ `@contextlib.contextmanager` — `yield` 앞이 열기, 뒤가 닫기

**언제 쓰나** — 클래스를 만들기 귀찮을 때. 실무에서 대부분 이쪽이다.

★ **이것은 [24번](../24-decorators/2-summary.md)의 데코레이터다** — 함수를 받아 **다른 것을 돌려준다.**
돌려주는 것은 「제너레이터 함수」가 아니라 「**부르면 컨텍스트 매니저를 만드는 함수**」다.

```text
   @contextlib.contextmanager
   def managed(name):
       준비                     <- __enter__ 에 해당
       try:
           yield 값             <- 이 값이 as 로 간다. 여기서 몸통이 돈다
       finally:
           정리                 <- __exit__ 에 해당

   ★ 몸통에서 난 예외는 "yield 자리로 던져진다" (17번의 throw)
```

```python
# e28_contextmanager.py
import contextlib


@contextlib.contextmanager
def managed(name):
    print("  yield 앞 — __enter__ 에 해당:", name)
    try:
        yield "열린 " + name
    finally:
        print("  yield 뒤 — __exit__ 에 해당:", name)


print("① 정상 경로")
with managed("자원") as got:
    print("  몸통 — as 가 받은 것:", repr(got))

print("② 몸통이 터질 때 — 예외가 yield 자리로 던져진다")


@contextlib.contextmanager
def watcher():
    try:
        yield "값"
    except ValueError as e:
        print("  yield 자리에서 잡았다:", type(e).__name__, "-", e)
        raise
    finally:
        print("  finally 는 언제나 돈다")


try:
    with watcher():
        raise ValueError("몸통이 터졌다")
except ValueError as e:
    print("  바깥에서 잡힘:", e)

print("③ 데코레이터가 만든 것의 정체")
cm = managed("정체")
print("  managed(...) 가 돌려준 것의 타입:", type(cm).__name__)
print("  __enter__ 가 있나:", hasattr(cm, "__enter__"),
      "· __exit__ 가 있나:", hasattr(cm, "__exit__"))
print("  managed 자체는:", type(managed).__name__,
      "· __wrapped__ 가 있나:", hasattr(managed, "__wrapped__"))
```

```text
===== python3 - <e28_contextmanager.py =====
① 정상 경로
  yield 앞 — __enter__ 에 해당: 자원
  몸통 — as 가 받은 것: '열린 자원'
  yield 뒤 — __exit__ 에 해당: 자원
② 몸통이 터질 때 — 예외가 yield 자리로 던져진다
  yield 자리에서 잡았다: ValueError - 몸통이 터졌다
  finally 는 언제나 돈다
  바깥에서 잡힘: 몸통이 터졌다
③ 데코레이터가 만든 것의 정체
  managed(...) 가 돌려준 것의 타입: _GeneratorContextManager
  __enter__ 가 있나: True · __exit__ 가 있나: True
  managed 자체는: function · __wrapped__ 가 있나: True
(exit 0)
```

- ①에서 **`as` 가 받은 것이 `yield` 한 값**(`'열린 자원'`)이다.
- ★★ ②에서 **예외가 `yield` 자리로 던져졌다** — `except ValueError` 가 **제너레이터 안에서** 잡았다.
  [17번](../17-generators-yield/2-summary.md)의 `throw()` 가 그대로 쓰인 것이다.
- ★ ③에서 정체를 찍었다 — **`managed` 자체는 함수**이고(데코레이터가 `functools.wraps` 를 쓴 덕에 `__wrapped__` 가 있다),
  **`managed(...)` 를 불러야** 컨텍스트 매니저 객체가 나온다.

★★ **그래서 `try/finally` 로 감싸는 것이 의무다.** `yield` 뒤에 그냥 정리 코드를 적으면
**몸통이 터졌을 때 그 줄에 안 온다.**

**비용** — 객체가 **일회용**이다(동작 9).

### 7. ★ 제너레이터가 예외를 삼키려면 — 그리고 `yield` 를 또 하면

**언제 쓰나** — `@contextmanager` 로 예외를 처리할 때.

```python
# e28_gen_swallow.py
import contextlib


@contextlib.contextmanager
def swallow():
    try:
        yield
    except ValueError as e:
        print("  잡고 다시 안 던진다:", e)


@contextlib.contextmanager
def twice():
    try:
        yield "첫째"
    except ValueError:
        yield "둘째"


print("① 잡고 다시 안 던지면 — 삼켜진다")
with swallow():
    raise ValueError("몸통이 터졌다")
print("  with 다음 줄까지 왔다")

print("② 예외가 온 뒤 또 yield 하면")
try:
    with twice():
        raise ValueError("몸통이 터졌다")
except RuntimeError as e:
    print("  RuntimeError:", e)
```

```text
===== python3 - <e28_gen_swallow.py =====
① 잡고 다시 안 던지면 — 삼켜진다
  잡고 다시 안 던진다: 몸통이 터졌다
  with 다음 줄까지 왔다
② 예외가 온 뒤 또 yield 하면
  RuntimeError: generator didn't stop after throw()
(exit 0)
```

- ★ **잡고 다시 안 던지면 삼켜진다.** 제너레이터가 **정상 종료**하면 `contextlib` 이 `__exit__` 에서 **참**을 돌려준다.
- ★★ **예외가 온 뒤 또 `yield` 하면 `RuntimeError: generator didn't stop after throw()`** 다.
  `with` 는 **한 번만 멈출 수 있는 제너레이터**를 요구한다.

**비용** — 삼키는 것이 **너무 쉽다.** `except` 를 쓰면 **다시 던질지**를 반드시 결정해야 한다.

### 8. `suppress`·`closing`·`ExitStack` — 표준이 주는 셋

**언제 쓰나** — 직접 클래스를 쓰기 전에. 대개 이 셋으로 끝난다.

```python
# e28_helpers.py
import contextlib


class Closeable:
    def __init__(self, name):
        self.name = name

    def close(self):
        print("    close():", self.name)


print("① suppress — 지정한 예외만 조용히 삼킨다")
with contextlib.suppress(FileNotFoundError):
    open("/없는/경로/에/없는/파일", encoding="utf-8")
print("  지나왔다")

try:
    with contextlib.suppress(FileNotFoundError):
        raise PermissionError("다른 종류")
except PermissionError as e:
    print("  다른 종류는 안 삼킨다:", type(e).__name__)

print("② closing — __exit__ 가 없고 close() 만 있는 것에 씌운다")
c = Closeable("연결")
print("  __exit__ 가 있나:", hasattr(c, "__exit__"))
with contextlib.closing(c) as got:
    print("    몸통 — as 가 받은 것:", got.name)

print("③ __exit__ 가 없는 것을 그냥 with 에 넣으면")
try:
    with Closeable("연결"):
        pass
except TypeError as e:
    print("  TypeError:", e)
```

```text
===== python3 - <e28_helpers.py =====
① suppress — 지정한 예외만 조용히 삼킨다
  지나왔다
  다른 종류는 안 삼킨다: PermissionError
② closing — __exit__ 가 없고 close() 만 있는 것에 씌운다
  __exit__ 가 있나: False
    몸통 — as 가 받은 것: 연결
    close(): 연결
③ __exit__ 가 없는 것을 그냥 with 에 넣으면
  TypeError: 'Closeable' object does not support the context manager protocol
(exit 0)
```

- **`suppress` 는 지정한 예외만** 삼킨다. 다른 종류는 그대로 나간다.
  [26번](../26-eafp-vs-lbyl/2-summary.md)의 `try/except/pass` 를 한 줄로 접은 것이다.
- **`closing` 은 `close()` 만 있는 것에 씌운다** — `__exit__` 가 없는 객체도 `with` 에 넣을 수 있다.
- ③이 대조군이다 — 그냥 넣으면 **`TypeError: 'Closeable' object does not support the context manager protocol`.**

개수가 실행 중에 정해지면 `ExitStack` 이다.

```python
# e28_exitstack.py
import contextlib


class M:
    def __init__(self, name):
        self.name = name

    def __enter__(self):
        print("  열림:", self.name)
        return self

    def __exit__(self, *exc):
        print("  닫힘:", self.name)
        return False


print("① 개수가 실행 중에 정해질 때 — ExitStack")
names = ["A", "B", "C"]
with contextlib.ExitStack() as stack:
    opened = [stack.enter_context(M(n)) for n in names]
    print("  몸통 — 연 것:", [m.name for m in opened])

print("② 몸통이 터져도 역순으로 닫힌다")
try:
    with contextlib.ExitStack() as stack:
        for n in names:
            stack.enter_context(M(n))
        raise ValueError("몸통이 터졌다")
except ValueError as e:
    print("  바깥에서 잡힘:", e)

print("③ callback 도 같은 스택에 쌓인다")
with contextlib.ExitStack() as stack:
    stack.enter_context(M("A"))
    stack.callback(print, "  콜백이 돈다")
    stack.enter_context(M("B"))
    print("  몸통")
```

```text
===== python3 - <e28_exitstack.py =====
① 개수가 실행 중에 정해질 때 — ExitStack
  열림: A
  열림: B
  열림: C
  몸통 — 연 것: ['A', 'B', 'C']
  닫힘: C
  닫힘: B
  닫힘: A
② 몸통이 터져도 역순으로 닫힌다
  열림: A
  열림: B
  열림: C
  닫힘: C
  닫힘: B
  닫힘: A
  바깥에서 잡힘: 몸통이 터졌다
③ callback 도 같은 스택에 쌓인다
  열림: A
  열림: B
  몸통
  닫힘: B
  콜백이 돈다
  닫힘: A
(exit 0)
```

- ①에서 **리스트 컴프리헨션으로 셋을 쌓았고**, 닫히는 것은 **역순**이다.
- ②에서 **몸통이 터져도 역순**으로 닫혔다.
- ★ ③에서 **`callback` 도 같은 스택에 쌓인다** — `A` 열기 → `콜백` 등록 → `B` 열기 순으로 쌓였고,
  **닫힘: B → 콜백 → 닫힘: A** 로 **등록 역순**으로 풀렸다.

**비용** — `ExitStack` 은 **정리 중 난 예외를 다루는 방식이 중첩 `with` 와 다르다**(동작 10).

### 9. `@contextmanager` 가 만든 객체는 **일회용**이다

**언제 쓰나** — 컨텍스트 매니저를 변수에 담아 두고 여러 번 쓸 때.

```python
# e28_reuse.py
import contextlib


@contextlib.contextmanager
def once():
    print("    열림")
    yield "자원"
    print("    닫힘")


class Reusable:
    def __enter__(self):
        print("    열림")
        return "자원"

    def __exit__(self, *exc):
        print("    닫힘")
        return False


def twice(cm):
    for n in ("첫 번째", "두 번째"):
        print("  ", n, "with")
        try:
            with cm as got:
                print("    몸통:", got)
        except Exception as e:
            print("    터짐:", type(e).__name__, "-", e)


print("① @contextmanager 가 만든 객체를 두 번 쓰면")
twice(once())
print("② 직접 쓴 클래스는 상태가 없으면 두 번 써도 된다")
twice(Reusable())
```

```text
===== python3 - <e28_reuse.py =====
① @contextmanager 가 만든 객체를 두 번 쓰면
   첫 번째 with
    열림
    몸통: 자원
    닫힘
   두 번째 with
    터짐: AttributeError - '_GeneratorContextManager' object has no attribute 'args'
② 직접 쓴 클래스는 상태가 없으면 두 번 써도 된다
   첫 번째 with
    열림
    몸통: 자원
    닫힘
   두 번째 with
    열림
    몸통: 자원
    닫힘
(exit 0)
```

- ★ ①에서 **두 번째 `with` 가 `AttributeError`** 로 터진다.
  객체가 **제너레이터 하나를 품고 있고**, 첫 번째에서 이미 소진했기 때문이다.
- ②에서 **상태가 없는 클래스는 두 번 써도 된다** — 「열림/몸통/닫힘」이 두 벌 찍혔다.
- ★ **클래스 이름(`_GeneratorContextManager`)과 문구는 구현 세부**다.
  **성질**은 「일회용이다」이고, 그것이 안 흔들리는 칸이다.

★ 고치는 법은 **매번 새로 부르는 것**이다 — `with managed():` 처럼 **`with` 줄에서 호출**한다.

**비용** — 재사용이 필요하면 **클래스로 쓴다.** `contextlib` 문서도 그렇게 권한다.

### 10. ★★ 정리 중에 예외가 나면 — 중첩 `with` 와 `ExitStack` 이 **갈린다**

**언제 쓰나** — `close()` 가 실패할 수 있을 때. 로그에서 원인이 사라지는 자리다.

두 개의 `__exit__` 가 **둘 다** 터지게 해 놓고, **몸통이 멀쩡할 때와 터질 때**를 각각 던졌다.

```python
# e28_exit_raises.py
import contextlib


class BadExit:
    def __init__(self, name):
        self.name = name

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        raise RuntimeError("닫다가 터졌다: " + self.name)


def chain(e):
    out = []
    while e is not None:
        out.append(type(e).__name__ + "(" + str(e) + ")")
        e = e.__context__
    return " <- __context__ - ".join(out)


def run(label, body):
    print("[", label, "]")
    try:
        body()
    except BaseException as e:
        print("    밖으로 나온 것:", type(e).__name__, "-", e)
        print("    묶음인가      :", isinstance(e, BaseExceptionGroup))
        print("    연쇄          :", chain(e))


def nested():
    with BadExit("A"), BadExit("B"):
        pass


def stacked():
    with contextlib.ExitStack() as stack:
        stack.enter_context(BadExit("A"))
        stack.enter_context(BadExit("B"))


def nested_with_body():
    with BadExit("A"), BadExit("B"):
        raise ValueError("몸통도 터졌다")


def stacked_with_body():
    with contextlib.ExitStack() as stack:
        stack.enter_context(BadExit("A"))
        stack.enter_context(BadExit("B"))
        raise ValueError("몸통도 터졌다")


run("중첩 with — 몸통은 멀쩡", nested)
run("ExitStack — 몸통은 멀쩡", stacked)
run("중첩 with — 몸통도 터짐", nested_with_body)
run("ExitStack — 몸통도 터짐", stacked_with_body)
```

```text
===== python3 - <e28_exit_raises.py =====
[ 중첩 with — 몸통은 멀쩡 ]
    밖으로 나온 것: RuntimeError - 닫다가 터졌다: A
    묶음인가      : False
    연쇄          : RuntimeError(닫다가 터졌다: A) <- __context__ - RuntimeError(닫다가 터졌다: B)
[ ExitStack — 몸통은 멀쩡 ]
    밖으로 나온 것: RuntimeError - 닫다가 터졌다: A
    묶음인가      : False
    연쇄          : RuntimeError(닫다가 터졌다: A)
[ 중첩 with — 몸통도 터짐 ]
    밖으로 나온 것: RuntimeError - 닫다가 터졌다: A
    묶음인가      : False
    연쇄          : RuntimeError(닫다가 터졌다: A) <- __context__ - RuntimeError(닫다가 터졌다: B) <- __context__ - ValueError(몸통도 터졌다)
[ ExitStack — 몸통도 터짐 ]
    밖으로 나온 것: RuntimeError - 닫다가 터졌다: A
    묶음인가      : False
    연쇄          : RuntimeError(닫다가 터졌다: A) <- __context__ - RuntimeError(닫다가 터졌다: B) <- __context__ - ValueError(몸통도 터졌다)
(exit 0)
```

★★ **표로 굳히면 이렇다.**

| | 밖으로 나온 것 | `__context__` 사슬 |
|---|---|---|
| 중첩 `with` — 몸통은 멀쩡 | `A` | ★ `A` ← `B` |
| **`ExitStack` — 몸통은 멀쩡** | `A` | ★★ **`A` 하나뿐 — `B` 가 사라졌다** |
| 중첩 `with` — 몸통도 터짐 | `A` | `A` ← `B` ← `ValueError` |
| `ExitStack` — 몸통도 터짐 | `A` | `A` ← `B` ← `ValueError` |

- **밖으로 나오는 것은 네 경우 다 `A`** 다 — **마지막으로 닫히는 것**이 이긴다.
- ★★ **둘째 줄이 이 절의 발견이다.** `ExitStack` 은 **몸통이 멀쩡할 때** `B` 의 예외를 **사슬에서 잃는다.**
  중첩 `with` 는 안 잃는다. **같은 일을 한다고 믿으면 여기서 틀린다.**
- ★ 이유는 `contextlib` 소스에 있다 — `_fix_exception_context` 가
  **`new_exc.__context__` 가 `None` 이면 「이미 올바르다」로 보고 그냥 돌아간다**(주석에 `see issue 20317`).
  몸통 예외가 없으면 그 자리가 정확히 `None` 이다.
- ★★ **어느 쪽도 [27번](../27-exception-groups-and-except-star/2-summary.md)의 `ExceptionGroup` 을 만들지 않는다**(`묶음인가: False`).
  자바 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **26번**이 쓰는
  suppressed exception 같은 장치도 **여기엔 없다.**

**비용** — **정리 코드가 터지면 정보를 잃는다.** 정리에서 예외가 날 수 있으면 **그 안에서 직접 잡아 기록**한다.

## 문법 — 형태와 규칙

**형태 — 다섯 가지뿐이다**

```python
# e28_forms.py
import contextlib


# ① 클래스로 — 메서드 둘이 계약의 전부다
class Managed:
    def __enter__(self):
        return "as 가 받는 것"          # 객체 자신이 아니어도 된다

    def __exit__(self, exc_type, exc_value, tb):
        return False                    # 참이면 예외를 삼킨다


# ② 제너레이터로 — yield 앞이 __enter__, 뒤가 __exit__
@contextlib.contextmanager
def managed():
    준비 = "자원"
    try:
        yield 준비                      # 이 값이 as 로 간다
    finally:
        pass                            # 정리. 예외가 나도 돈다


# ③ 여러 개를 한 줄에 — 괄호로 감싸는 형태는 3.10+
def many():
    with Managed() as a, Managed() as b:        # 해제는 역순
        pass
    with (Managed() as a, Managed() as b):      # 3.10+
        pass


# ④ 개수가 실행 중에 정해지면 ExitStack
def dynamic(names):
    with contextlib.ExitStack() as stack:
        opened = [stack.enter_context(Managed()) for _ in names]
        stack.callback(print, "콜백도 같은 스택에 쌓인다")
        return len(opened)


# ⑤ 표준이 주는 것 둘
def helpers(d, key, conn):
    with contextlib.suppress(KeyError):   # try/except/pass 한 줄
        d[key]
    with contextlib.closing(conn):        # close() 만 있는 것에 씌운다
        pass
```

규칙 열.

1. **`with` 는 `type(객체)` 에서 `__enter__`·`__exit__` 를 찾는다.** 인스턴스에 달아 두면 **안 본다.**
2. **`as` 가 받는 것은 `__enter__` 의 반환값**이다 — 객체 자신이 아니어도 된다.
3. **`__exit__(타입, 값, 트레이스백)`** 을 받는다. 예외가 없으면 **`(None, None, None)`**.
4. ★ **`__exit__` 가 「참」을 돌려주면 예외를 삼킨다.** `True` 만이 아니라 **진릿값이 참인 모든 것**이다.
5. **`return` 을 빼먹으면 `None`** 이라 안 삼킨다 — 기본값이 안전한 쪽이다.
6. **여러 개를 쓰면 해제는 역순.** 다중 `with` 는 **중첩 `with` 의 설탕**이고, **괄호 형태는 3.10+**.
7. ★ **`__enter__` 가 터지면 그 객체의 `__exit__` 는 안 돈다.** 앞에서 연 것은 닫힌다.
8. **`@contextmanager` 는 `yield` 로 한 번만 멈춰야** 한다. 두 번 멈추면 `RuntimeError`.
9. ★ **`@contextmanager` 안에서는 `try/finally` 가 의무**다. 안 감싸면 몸통이 터졌을 때 정리가 안 된다.
10. ★ **`@contextmanager` 가 만든 객체는 일회용**이다. 재사용하려면 **클래스로** 쓴다.

**금지 사례 — 문법은 맞는데 조용히 어긋나는 것들**

```python
# e28_pitfalls.py
import contextlib


class M:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


# ① __exit__ 가 참을 돌려준다 — 예외가 조용히 사라진다
class Swallow:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return True            # ★ 몸통의 예외가 전부 삼켜진다


# ② 제너레이터에서 정리를 try/finally 로 안 감싼다
@contextlib.contextmanager
def leaky():
    자원 = object()
    yield 자원
    print("정리")              # ★ 몸통이 터지면 이 줄이 안 돈다


# ③ __exit__ 가 없는 것을 with 에 넣는다
class OnlyClose:
    def close(self):
        pass


def wrong(conn):
    with OnlyClose():          # ★ TypeError — closing() 으로 씌워야 한다
        pass


# ④ 인스턴스에 __enter__/__exit__ 를 달아 둔다
def on_instance():
    obj = M()
    obj.__enter__ = lambda: obj      # ★ 특수 메서드는 타입에서 찾는다
    obj.__exit__ = lambda *e: False  #   인스턴스에 달아도 안 본다
    return obj


# ⑤ @contextmanager 가 만든 객체를 두 번 쓴다
def reuse():
    cm = managed()             # ★ 제너레이터 하나를 품은 일회용 객체다
    with cm:
        pass
    with cm:                   # ★ AttributeError — 이미 소진됐다
        pass


@contextlib.contextmanager
def managed():
    yield
```

## 어디서 틀리나

### (1) ★★ `__exit__` 에서 무심코 무언가를 `return` 한다

**진릿값이 참이면 예외가 사라진다.** `1`·`'문자열'` 전부 삼킨다.
로그 함수의 반환값을 그대로 돌려주는 실수가 이 모양이다.

### (2) ★ 「`True` 를 돌려줘야 삼킨다」로 안다

★ **「참」이면 삼킨다.** [05번](../05-truthiness-and-short-circuit/2-summary.md)의 진릿값 규칙 그대로다.

### (3) ★ `__enter__` 안에서 자원을 여럿 잡는다

**두 번째에서 터지면 첫 번째가 샌다** — 그 객체의 `__exit__` 는 **안 돌기 때문**이다.
`ExitStack` 을 쓴다.

### (4) ★ `@contextmanager` 에서 `try/finally` 를 뺀다

**정상 경로에서는 멀쩡해 보인다.** 몸통이 터질 때만 정리가 안 된다.

### (5) `@contextmanager` 객체를 재사용한다

**`AttributeError`** 가 난다. 제너레이터가 이미 소진됐다. **`with` 줄에서 호출**한다.

### (6) 인스턴스에 `__enter__`/`__exit__` 를 달아 둔다

★ **특수 메서드는 타입에서 찾는다.** `hasattr` 가 `True` 를 답해도 안 된다.

### (7) `close()` 만 있는 것을 그냥 `with` 에 넣는다

**`TypeError: ... does not support the context manager protocol`.**
`contextlib.closing` 으로 씌운다.

### (8) ★ 해제 순서를 정의 순서로 안다

**역순이다.** 「나중에 연 것이 먼저 닫힌다」.

### (9) ★ `ExitStack` 이 중첩 `with` 와 같다고 믿는다

★★ **정리 중 예외가 나면 갈린다.** 몸통이 멀쩡할 때 `ExitStack` 은 **먼저 난 정리 예외를 사슬에서 잃는다.**

### (10) 정리에서 난 예외가 묶음이 될 것이라 믿는다

★ **안 된다.** 실측에서 `isinstance(e, BaseExceptionGroup)` 이 **네 경우 다 `False`** 였다.
[27번](../27-exception-groups-and-except-star/2-summary.md)의 장치는 여기에 안 쓰인다.

### (11) `suppress` 로 넓게 삼킨다

**지정한 타입만** 삼키는 것이 장점이다. `Exception` 을 주면 [26번](../26-eafp-vs-lbyl/2-summary.md)의 「삼키기」가 된다.

### (12) 괄호 다중 `with` 를 3.9 에서 쓴다

**3.10+ 다.** 그 전에는 역슬래시가 필요했다 — **옛 판은 안 돌려 봤다.**

## 구현 세부사항 대 언어 보장

세 층으로 가른다. ★ **이 주제는 「언어 보장」이 두껍다** — 등가식이 레퍼런스에 단계별로 적혀 있어서
`__exit__` 의 반환값도, 해제 역순도, `__enter__` 실패 시 미호출도 **전부 글로 확인된다.**\
구현 쪽에 남는 것은 **`contextlib` 이 예외를 잇는 방식**과 **예외 문구**다.

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **언어 보장** | 레퍼런스·PEP 가 정한 것 | 공식 문서 문장을 열어서 인용 |
| **CPython 구현** | 이 구현이 그렇게 하는 것 | `contextlib` 소스 · 예외 문구 |
| **이 판(3.12.3)의 관찰** | 이 판에서 그랬을 뿐 | 내부 클래스 이름 · `__context__` 사슬 길이 |

### 언어 보장

| 사실 | 근거 |
|---|---|
| `with` 의 **등가식** — `__exit__` 를 먼저 찾아 두고 `__enter__` 를 부른다 | 8.5 The `with` statement |
| **`as` 가 받는 것은 `__enter__` 의 반환값** | 8.5 |
| **`__exit__` 가 참을 돌려주면 예외를 삼키고, 거짓이면 다시 던진다** | 8.5 — *"If the return value was true, the exception is suppressed"* |
| 예외가 없으면 `__exit__` 가 **`(None, None, None)`** 을 받는다 | 3.3.9 |
| **여러 개는 중첩과 같고, 해제는 역순** | 8.5 |
| ★ **`__enter__` 가 터지면 그 객체의 `__exit__` 는 안 불린다**(아직 `try` 밖이다) | 8.5 등가식 |
| **특수 메서드는 타입에서 찾는다** | 3.3.1 Special method lookup |
| `@contextmanager` 는 **한 번만 `yield`** 해야 한다 | `contextlib` |
| `suppress` 는 **지정한 예외만** 삼킨다 · `closing` 은 `close()` 를 부른다 | `contextlib` |
| `ExitStack` 은 **등록 역순**으로 풀고 `callback` 도 같은 스택에 쌓는다 | `contextlib` |
| 괄호 다중 `with` 는 **3.10+** | What's New In Python 3.10 |

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| ★ `ExitStack` 의 **`_fix_exception_context` 가 `__context__` 가 `None` 이면 그냥 돌아간다** | `/usr/lib/python3.12/contextlib.py` 를 읽음 (`see issue 20317` 주석) |
| ★ 그래서 **몸통이 멀쩡할 때 먼저 난 정리 예외가 사슬에서 사라진다** | 실행 — 동작 10 |
| `@contextmanager` 가 만드는 객체의 클래스가 `_GeneratorContextManager` | 실행 |
| 재사용 시 문구 — `'_GeneratorContextManager' object has no attribute 'args'` | 실행 |
| `TypeError` 문구 셋이 갈리는 것 — `(missed __exit__ method)` 가 붙는 자리 | 실행 |
| `RuntimeError: generator didn't stop after throw()` | 실행 |

### 이 판(3.12.3)의 관찰

| 관찰 | 어디가 흔들리나 |
|---|---|
| 내부 클래스 이름 `_GeneratorContextManager` | 이름은 사적(private)이다. **성질**은 「일회용」이고 그쪽이 안 흔들린다 |
| 예외 **문구** 전부 | 종류는 명세, 문구는 아니다 |
| `ExitStack` 의 `__context__` 사슬이 한 칸인 것 | ★ **구현 버그로 고쳐질 수 있다.** 다른 판은 안 돌려 봤다 |
| `contextlib.py` 의 **절대경로**가 트레이스백에 박히는 것 | 머신마다 다르다 — **그래서 이 문서는 그 트레이스백을 안 실었다** |

### 그래서 이렇게 적으면 틀린다

- ✗ 「`__exit__` 가 `True` 를 돌려줘야 삼킨다」\
  ○ **참이면 삼킨다.** `1`·`'문자열'` 전부 삼킨다.
- ✗ 「`with` 는 `try/finally` 와 완전히 같다」\
  ○ **`__exit__` 는 예외를 삼킬 수 있다.** `finally` 에는 그 스위치가 없다.
- ✗ 「`as` 가 받는 것은 `with` 에 쓴 객체다」\
  ○ **`__enter__` 의 반환값**이다. 다른 것이어도 된다.
- ✗ 「`__enter__` 가 터져도 `__exit__` 가 정리해 준다」\
  ○ **안 돈다.** 아직 `try` 밖이다.
- ✗ 「`hasattr(obj, '__enter__')` 면 `with` 에 넣을 수 있다」\
  ○ **타입에 있어야** 한다.
- ✗ 「`@contextmanager` 함수는 제너레이터다」\
  ○ **함수**다. 부르면 **컨텍스트 매니저 객체**가 나온다.
- ✗ 「`@contextmanager` 객체는 여러 번 쓸 수 있다」\
  ○ **일회용**이다.
- ✗ 「`ExitStack` 은 중첩 `with` 와 같다」\
  ○ **정리 중 예외의 사슬이 다르다**(실측).
- ✗ 「정리에서 난 예외들은 `ExceptionGroup` 이 된다」\
  ○ **안 된다.** 네 경우 다 `False` 였다.

**판정 기준 한 줄**: **「이 값이 참인가」를 물으면 삼킴이 갈리고,
「이 객체의 `__enter__` 가 끝났나」를 물으면 `__exit__` 가 도는지가 갈린다.**

## 언제 쓰고 언제 안 쓰나

| 상황 | 판정 |
|---|---|
| 자원을 열고 반드시 닫는다 | ★ **`with`** — 25번의 `try/finally` 를 굳힌 것이다 |
| 컨텍스트 매니저를 **한 군데**서만 쓴다 | **`@contextmanager`** — 클래스보다 짧다 |
| **재사용**해야 한다 | ★ **클래스로** — `@contextmanager` 객체는 일회용 |
| 개수가 **실행 중에** 정해진다 | **`ExitStack`** |
| `__enter__` 에서 **자원을 여럿** 잡아야 한다 | ★ **`ExitStack` 을 안에서 쓴다** — 아니면 샌다 |
| `close()` 만 있는 객체다 | **`contextlib.closing`** |
| 특정 예외를 조용히 넘긴다 | **`contextlib.suppress(구체타입)`** — `Exception` 은 주지 마라 |
| 예외를 **삼켜야** 한다 | `__exit__` 에서 **참**을 돌려준다. **의도를 주석으로 남긴다** |
| 정리 코드가 **실패할 수 있다** | ★ **그 안에서 직접 잡아 기록**한다 — 안 그러면 정보를 잃는다 |
| `async with` 가 필요하다 | `[목록의 **51번 주제**](../51-asyncio-coroutine-basics/)`·`[목록의 **52번 주제**](../52-asyncio-concurrency-structure/)` — **이 주제 밖이다** |

## 핵심 문장

- ★★ **`__exit__` 가 「참」을 돌려주면 예외를 삼킨다** — `True` 만이 아니다.
  실측에서 `1`·`'빈 문자열이 아닌 문자열'` 도 삼켰고 `0`·`''`·`None` 은 안 삼켰다.
  [05번](../05-truthiness-and-short-circuit/2-summary.md)의 진릿값 규칙 그대로다.
- ★★ **`__enter__` 가 터지면 그 객체의 `__exit__` 는 안 돈다.** 등가식에서 `try` 가
  **`__enter__()` 가 끝난 뒤에 시작**하기 때문이고, **앞에서 이미 연 것은 닫힌다.**
- ★★ **해제는 역순이다.** 다중 `with` 는 중첩 `with` 의 설탕이라 **출력이 한 글자도 같고**,
  `ExitStack` 도 **등록 역순**(콜백 포함)으로 푼다.
- ★★ **`ExitStack` 은 중첩 `with` 와 정리 중 예외 처리가 다르다.**
  몸통이 멀쩡할 때 **먼저 난 정리 예외를 `__context__` 사슬에서 잃는다** —
  `contextlib` 의 `_fix_exception_context` 가 `None` 을 「이미 올바르다」로 보기 때문이다.
- ★ **`as` 가 받는 것은 `__enter__` 의 반환값**이다. 객체 자신이 아니어도 된다.
- ★ **특수 메서드는 타입에서 찾는다.** 인스턴스에 달아 두면 `hasattr` 가 참을 답해도 `with` 가 거부한다.
  에러 문구가 셋으로 갈리고, **`__exit__` 가 없을 때만 `(missed __exit__ method)`** 가 붙는다.
- ★ **`@contextmanager` 는 [24번](../24-decorators/2-summary.md)의 데코레이터**다. `yield` 앞이 열기, 뒤가 닫기이고,
  **몸통의 예외는 `yield` 자리로 던져진다**([17번](../17-generators-yield/2-summary.md)의 `throw`).
  **`try/finally` 로 감싸는 것이 의무**이고, **만든 객체는 일회용**이다.
- ★ **정리에서 난 예외들은 [27번](../27-exception-groups-and-except-star/2-summary.md)의 묶음이 되지 않는다** —
  실측에서 네 경우 다 `False` 였다. **마지막에 닫히는 것의 예외가 이긴다.**

## 관련 자료

- 목록: [python/syntax 주제 목록](../README.md) — 이 주제는 **28번**
- 선행: [25-exceptions-and-finally](../25-exceptions-and-finally/2-summary.md) — **`try/finally` 의 정본.**\
  **경계**: 절의 실행 순서·`finally` 의 `return`·연쇄는 전부 그쪽.
  여기는 **그것을 객체로 굳혔을 때 무엇이 더 생기나**(삼킴 스위치)만 다룬다.
- 선행: [17-generators-yield](../17-generators-yield/2-summary.md) — **`throw()` 의 정본.**\
  **경계**: 제너레이터에 예외를 던져 넣는 것 자체는 그쪽, **`with` 가 그것을 쓰는 것**만 여기다.
- 선행: [24-decorators](../24-decorators/2-summary.md) — **`@contextmanager` 가 데코레이터인 것.**\
  **경계**: 데코레이터 문법과 `functools.wraps` 는 그쪽.
- 선행: [05-truthiness-and-short-circuit](../05-truthiness-and-short-circuit/2-summary.md) — **진릿값.**\
  **경계**: 「참」의 정의는 그쪽, **`__exit__` 가 그 규칙을 쓰는 것**만 여기다.
- 함께 보는 곳: [26-eafp-vs-lbyl](../26-eafp-vs-lbyl/2-summary.md) — `contextlib.suppress` 가
  거기서 「접어 둔 API」로 나온다. **정본은 여기**다.
- 함께 보는 곳: [27-exception-groups-and-except-star](../27-exception-groups-and-except-star/2-summary.md) —
  **정리 중 예외 여럿**을 묶음으로 만들지 **않는다**는 확인이 동작 10에 있다.
- 이어지는 곳: `[목록의 **48번 주제**](../48-pathlib-and-file-io/)` — `pathlib` 와 파일 I/O. **`with open(...)` 의 실무 자리**다.
- 이어지는 곳: `[목록의 **51번 주제**](../51-asyncio-coroutine-basics/)`·`[목록의 **52번 주제**](../52-asyncio-concurrency-structure/)` — `async with` 와 `__aenter__`/`__aexit__`.
- 다른 갈래: 자바 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **26번** — try-with-resources.
  `AutoCloseable` 이 `__exit__` 자리이고, **정리 중 예외를 주 예외에 붙인다**(suppressed) —
  파이썬은 **그 장치가 없다**(동작 10).
- 다른 갈래: Go 갈래 목록([`go/syntax/README.md`](../../../go/syntax/README.md))의 **26번** — `defer`.
  **LIFO 로 푸는 것**이 같고, **예외를 삼키는 스위치가 없다**는 것이 다르다.
- 다른 갈래: Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **09번** — `Drop`.
  **스코프를 벗어날 때 자동**이라 `with` 라는 문법 자체가 필요 없다.
- 공식 문서: [The `with` statement](https://docs.python.org/3.12/reference/compound_stmts.html#the-with-statement) ·
  [With Statement Context Managers](https://docs.python.org/3.12/reference/datamodel.html#with-statement-context-managers) ·
  [`contextlib`](https://docs.python.org/3.12/library/contextlib.html) ·
  [PEP 343](https://peps.python.org/pep-0343/)

## 용어 풀이

- **컨텍스트 매니저(context manager)**: `__enter__`·`__exit__` 를 **타입에** 가진 객체.\
  예: 파일 객체, `threading.Lock`.
- **`__enter__`**: 여는 메서드. **돌려준 값이 `as` 로 간다.**\
  예: 객체 자신이 아니어도 된다.
- **`__exit__(타입, 값, tb)`**: 닫는 메서드. **참을 돌려주면 예외를 삼킨다.**\
  예: 예외가 없으면 셋 다 `None` 이다.
- **삼킴(suppression)**: 예외를 다시 던지지 않고 `with` 다음 줄로 가는 것.\
  예: `contextlib.suppress` 가 이것을 한 줄로 만든 것이다.
- **등가식(desugaring)**: 문법 설탕을 원래 형태로 풀어 쓴 것.\
  예: `try` 가 `__enter__()` **뒤에** 시작한다는 사실이 거기서 나온다.
- **해제 역순(LIFO unwinding)**: 나중에 연 것이 먼저 닫히는 것.\
  예: `with A, B, C:` 는 `C → B → A` 로 닫힌다.
- **`@contextlib.contextmanager`**: 제너레이터 함수를 컨텍스트 매니저 팩토리로 바꾸는 데코레이터.\
  예: `yield` 앞이 열기, 뒤가 닫기.
- **`contextlib.suppress(타입들)`**: 지정한 예외만 삼키는 컨텍스트 매니저(3.4+).\
  예: 다른 종류는 그대로 나간다.
- **`contextlib.closing(객체)`**: `close()` 만 있는 객체를 `with` 에 넣게 씌우는 것.\
  예: `__exit__` 가 없는 객체도 쓸 수 있다.
- **`contextlib.ExitStack`**: 개수를 실행 중에 정하는 스택(3.3+). **등록 역순**으로 푼다.\
  예: `callback` 도 같은 스택에 쌓인다.
- **특수 메서드 조회(special method lookup)**: `__enter__` 같은 이름을 **타입에서만** 찾는 규칙.\
  예: 인스턴스에 달아 두면 안 본다.
- **일회용(one-shot)**: 한 번 쓰면 다시 못 쓰는 것.\
  예: `@contextmanager` 가 만든 객체가 그렇다.

## 더 들어가면

- **`async with` 와 `__aenter__`/`__aexit__`** — 같은 계약의 비동기 판.
  `contextlib.AsyncExitStack` 도 있다. **이 주제에서는 안 돌려 봤다** — 정본은 `[목록의 **51번 주제**](../51-asyncio-coroutine-basics/)`·`[목록의 **52번 주제**](../52-asyncio-concurrency-structure/)` 다.
- **`contextlib.ContextDecorator`** — 컨텍스트 매니저를 **데코레이터로도** 쓰게 하는 믹스인.
  `@contextmanager` 가 만든 객체는 이미 이것을 상속한다. **안 돌려 봤다.**
- ★ **`__exit__` 안에서 새 예외를 던지면** 원래 예외가 `__context__` 가 된다 —
  [25번](../25-exceptions-and-finally/2-summary.md)의 `finally` 와 같은 모양이다. 동작 10이 그 실측이다.
- ★ **`ExitStack` 의 `__context__` 유실은 구현 쪽 문제로 보인다** — `contextlib` 소스의
  `see issue 20317` 주석이 그 자리를 가리킨다. **판이 오르면 고쳐질 수 있으므로 다시 던져 봐야 한다.**
- ★ **`with` 가 등가식대로 `__exit__` 를 먼저 찾아 두는 것**은 실무에서 한 줄로 드러난다 —
  `__exit__` 만 없을 때 에러 문구에 **`(missed __exit__ method)`** 가 붙는 것이 그 증거다.
