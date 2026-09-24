# python/syntax/28-context-managers-and-with — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> [1-question.md](1-question.md)의 번호와 **1:1**로 대응한다. 질문 12개 = 답 12개.
>
> 이 파일의 모든 출력은 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> 던지는 형태는 `python3 - <파일` 로 고정했다.
> ★ **이 파일에는 트레이스백이 한 줄도 없다** — `contextlib` 안에서 난 예외에는 **절대경로가 박혀**
> 다른 머신에서 재현이 안 되기 때문이다. 대신 **타입·메시지·`__context__` 사슬**을 찍었다.
> ★ 이 파일의 블록에는 **주소도 시간도 절대경로도 안 찍힌다** — 같은 판에서 다시 돌리면 **한 글자도 안 변한다.**
> 단 **내부 클래스 이름**과 **예외 문구**는 구현·판에 달린 것이다(12번 답).

## 정답

### 1. `as` 는 `'자원'` 을 받고, `__exit__` 는 `(None, None, None)` 또는 셋 다를 받는다

**출력**

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

**왜 그런가**

레퍼런스가 등가식을 단계로 적는다.

> 2. The context manager's `__enter__()` is loaded for later use.
> 3. The context manager's `__exit__()` is loaded for later use.
> 4. The context manager's `__enter__()` method is invoked. …
> 7. The context manager's `__exit__()` method is invoked.

- ★ **`as` 가 받은 것은 객체 자신이 아니라 `'자원'` 이라는 문자열**이다.
  **`__enter__` 가 돌려주는 것이면 무엇이든** 된다.
- ①의 `__exit__` 는 **`(None, None, None)`** 을 받았다 — 예외가 없었다는 뜻이다.
- ②는 **`('ValueError', "ValueError('몸통이 터졌다')", 'tb 있음')`** 세 값을 받았다.
- ②에서 **`__exit__` 가 `False` 를 돌려줬으므로** 예외가 밖으로 나갔고,
  **「with 문 다음 줄」에 해당하는 줄은 없다** — 대신 `except ValueError` 가 잡았다.

### 2. 삼켜지는 것은 **셋** — `True`·`1`·`'빈 문자열이 아닌 문자열'`

**출력**

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

**왜 그런가**

레퍼런스가 못 박는다.

> If the suite was exited due to an exception, and the return value from the `__exit__()` method was false,
> the exception is reraised. If the return value was true, the exception is suppressed.

| 돌려준 값 | 진릿값 | 예외가 |
|---|---|---|
| `True` | 참 | ★ **삼켜진다** |
| `False` | 거짓 | 나간다 |
| `None` | 거짓 | 나간다 |
| `1` | 참 | ★ **삼켜진다** |
| `0` | 거짓 | 나간다 |
| `'빈 문자열이 아닌 문자열'` | 참 | ★ **삼켜진다** |
| `''` | 거짓 | 나간다 |

- ★★ 기준은 「`True` 인가」가 아니라 「**참인가**」다.
  [05번](../05-truthiness-and-short-circuit/2-summary.md)의 진릿값 규칙이 **그대로** 쓰인다.
- ★ **`return` 을 아예 안 쓰면 `None` 이 돌아간다** — `None` 줄과 같아진다. **안 삼킨다.**
  기본값이 **안전한 쪽**이라는 뜻이고, 위험한 것은 반대다 —
  **`__exit__` 안에서 무심코 무언가를 `return` 하면** 예외가 조용히 사라진다.

```text
   __exit__ 가 돌려준 값
        |
   bool(값) 이 참인가?
      /            \
    예              아니오
     |                |
  예외를 삼킨다     예외를 다시 던진다
```

### 3. 한 글자도 같다 — 「몸통」은 ③에서 안 찍히고, 닫힘은 언제나 역순이다

**출력**

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

**왜 그런가**

- ★ **①과 ②의 출력이 한 글자도 같다.** 다중 `with` 는 **중첩 `with` 의 문법 설탕**이다.

```text
   with A, B, C:          ==      with A:
       몸통                            with B:
                                           with C:
                                               몸통
```

- ★ ③에서 **「몸통」이 안 찍혔다.** 예외가 그 앞에서 터졌기 때문이다.
  그래도 **닫힘: C → B → A** 로 **역순**이 지켜졌다.
- **괄호로 감싼 형태는 3.10+** 다. 그 전에는 역슬래시로 줄을 이어야 했다 — **옛 판은 안 돌려 봤다.**

### 4. `BadEnter.__exit__` 는 안 찍히고, `Good.__exit__` 는 찍힌다

**출력**

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

**왜 그런가**

등가식이 이유를 그대로 말한다 — **`try` 는 `__enter__()` 가 끝난 뒤에 시작한다.**

```text
   ② __exit__ 를 찾아 둔다
   ③ __enter__() 를 부른다     <- ★ 여기서 터지면 아직 try 밖이다
   ④ try:
   ⑤     몸통
   ⑥ finally:
   ⑦     __exit__(...)         <- 그래서 이 줄에 못 온다
```

- ★ ①에서 **`BadEnter.__exit__` 가 안 찍혔다.** **못 연 문은 안 닫는다.**
- ★ ②에서 **`Good.__exit__` 는 찍혔다.** 갈리는 이유는 하나다 —
  **`Good` 은 `__enter__` 가 이미 끝나 `try` 안에 들어갔고, `BadEnter` 는 아직 못 들어갔다.**
  다중 `with` 는 **이미 성공한 것만** 되감는다.
- 「몸통」 줄은 **한 번도 안 찍힌다.**
- ★ 그래서 **`__enter__` 안에서 자원을 여럿 잡으면 안 된다** — 두 번째에서 터지면 **첫 번째가 샌다.**
  그 자리에 쓰는 것이 `ExitStack` 이다(9번 답).

### 5. `as` 는 `'열린 자원'`, 예외는 제너레이터 **안**에서 잡히고, `managed` 는 함수다

**출력**

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

**왜 그런가**

- ①에서 **`as` 가 받은 것은 `yield` 한 값**(`'열린 자원'`)이다. `managed("자원")` 자체가 아니다.
- ★★ ②에서 **예외가 `yield` 자리로 던져졌다** — `except ValueError` 가 **제너레이터 안에서** 잡았고,
  그 뒤 `finally` 가 돌고, **다시 던졌으므로** 밖의 `except` 가 잡았다.
  순서가 「**yield 자리에서 잡았다 → finally → 바깥에서 잡힘**」이다.
  이것은 [17번](../17-generators-yield/2-summary.md)의 `throw()` 가 그대로 쓰인 것이다.

```text
   with watcher():                     제너레이터
       raise ValueError  ────throw───>  yield "값"   <- 여기로 예외가 들어온다
                                            |
                                        except ValueError -> 잡는다 -> raise
                                            |
                                        finally -> 돈다
                                            |
   except ValueError  <────────────────  다시 던져져 나온다
```

- ★ ③에서 **`managed` 자체는 `function`** 이고 **`__wrapped__` 가 있다** —
  [24번](../24-decorators/2-summary.md)의 데코레이터가 `functools.wraps` 를 썼다는 증거다.
  **`managed(...)` 를 불러야** `_GeneratorContextManager` 객체가 나온다.

### 6. 밖으로 나온 것은 넷 다 `A` — 그런데 `ExitStack` 한 줄만 사슬이 짧다

**출력**

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

**왜 그런가**

| | 밖으로 나온 것 | `__context__` 사슬 |
|---|---|---|
| 중첩 `with` — 몸통은 멀쩡 | `A` | `A` ← `B` |
| **`ExitStack` — 몸통은 멀쩡** | `A` | ★★ **`A` 하나뿐 — `B` 를 잃었다** |
| 중첩 `with` — 몸통도 터짐 | `A` | `A` ← `B` ← `ValueError` |
| `ExitStack` — 몸통도 터짐 | `A` | `A` ← `B` ← `ValueError` |

- **밖으로 나오는 것은 네 경우 다 `A`** 다 — **마지막으로 닫히는 것**이 이긴다(해제가 역순이므로 `B` 가 먼저 닫힌다).
- ★★ **둘째 줄만 사슬이 다르다.** `ExitStack` 은 **몸통이 멀쩡할 때** `B` 의 예외를 **사슬에서 잃는다.**
  중첩 `with` 는 안 잃는다 — **같은 일을 한다고 믿으면 여기서 틀린다.**
- ★ 이유는 `contextlib` 소스에 있다. `_fix_exception_context` 가
  **`new_exc.__context__` 가 `None` 이면 「이미 올바르다」로 보고 그냥 돌아간다**(주석에 `see issue 20317`).
  **몸통 예외가 없으면 그 자리가 정확히 `None`** 이라 연결이 안 붙는다.
  몸통이 터진 셋째·넷째 줄에서는 그 자리가 `None` 이 아니어서 **양쪽이 같아진다.**
- ★★ **넷 다 묶음이 아니다**(`묶음인가: False`).
  [27번](../27-exception-groups-and-except-star/2-summary.md)의 `ExceptionGroup` 은 **여기에 안 쓰인다.**
  자바 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **26번**이 쓰는
  suppressed exception 같은 장치도 **파이썬에는 없다.**

★ **그래서 정리 코드가 터질 수 있으면 그 안에서 직접 잡아 기록한다.** 안 그러면 정보를 잃는다.

### 7. 안 된다 — 특수 메서드는 타입에서 찾고, 문구도 갈린다

**출력**

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

**왜 그런가**

레퍼런스가 규칙을 적는다.

> For custom classes, implicit invocations of special methods are only guaranteed to work correctly
> if defined on an object's type, not in the object's instance dictionary.

- ★ 셋째 줄이 규칙의 증거다 — **인스턴스에는 둘 다 달려 있는데**(`True True`)
  **클래스에는 없어서**(`False False`) `TypeError` 가 난다.
- ★ **`hasattr(obj, "__enter__")` 는 `True` 를 답한다.** 그래서 **그것으로 판정하면 틀린다** —
  [26번](../26-eafp-vs-lbyl/2-summary.md)의 「검사가 실행과 같은 기준인가」가 여기서도 그대로다.
- ★★ **문구가 갈린다.** `__exit__` 만 없을 때만 **`(missed __exit__ method)`** 가 붙는다.
  **등가식에서 `__exit__` 를 먼저 찾아 두기 때문**이고, `__enter__` 가 없을 때는 그냥 프로토콜 미지원으로 끝난다.

### 8. 삼켜진다 — 또 `yield` 하면 `RuntimeError` 다

**출력**

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

**왜 그런가**

- ★ **잡고 다시 안 던지면 삼켜진다.** 제너레이터가 **정상 종료**하면
  `contextlib` 이 `__exit__` 에서 **참**을 돌려주기 때문이다(2번 답의 규칙 그대로다).
  **「with 다음 줄까지 왔다」가 그 증거**다.
- ★★ 예외가 온 뒤 또 `yield` 하면 **`RuntimeError: generator didn't stop after throw()`** 다.
  `with` 는 **한 번만 멈추는 제너레이터**를 요구한다.
- ★ `yield` 뒤의 정리 코드를 `try/finally` 로 **안 감싸면**,
  **몸통이 터졌을 때 그 줄에 안 온다** — 예외가 `yield` 자리에서 밖으로 나가 버리기 때문이다.
  **정상 경로에서는 멀쩡해 보여서** 더 나쁘다.

### 9. 각각 「삼키기」·「`close()` 씌우기」·「개수를 실행 중에 정하기」를 푼다

**출력**

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

**출력** — 개수가 실행 중에 정해질 때.

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

**왜 그런가**

- **`suppress`** — [26번](../26-eafp-vs-lbyl/2-summary.md)의 `try/except/pass` 를 한 줄로 접은 것이다.
  ★ **지정한 타입만** 삼킨다 — `PermissionError` 는 그대로 나갔다.
- **`closing`** — `__exit__` 가 **없는** 객체(`hasattr` 가 `False`)를 `with` 에 넣게 씌운다.
  ③이 대조군이다 — 그냥 넣으면 **`TypeError: 'Closeable' object does not support the context manager protocol`.**
- **`ExitStack`** — ①에서 컴프리헨션으로 셋을 쌓았고 **역순**으로 닫혔다.
  ②에서 **몸통이 터져도 역순**이다.
- ★ ③이 답이다 — **`callback` 은 컨텍스트와 같은 스택**에 쌓인다.
  `A` 열기 → 콜백 등록 → `B` 열기 순으로 쌓였고, **닫힘: B → 콜백 → 닫힘: A** 로 **등록 역순**으로 풀렸다.

### 10. 안 된다 — `AttributeError` 가 나고, 제너레이터가 이미 소진됐다

**출력**

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

**왜 그런가**

- ★ ①에서 **두 번째 `with` 가 `AttributeError`** 로 터진다 —
  `'_GeneratorContextManager' object has no attribute 'args'`.
  객체가 **제너레이터를 만들 재료(`args`)를 첫 `__enter__` 에서 지웠기 때문**이다.
- ②에서 **상태가 없는 클래스는 두 번 써도 된다** — 「열림/몸통/닫힘」이 두 벌 찍혔다.
- ★ **클래스 이름과 문구는 구현 세부**다. **성질**은 「일회용이다」이고, 그쪽이 안 흔들리는 칸이다.
- 고치는 법은 **매번 새로 부르는 것**이다 — `with managed():` 처럼 **`with` 줄에서 호출**한다.
  재사용이 필요하면 **클래스로** 쓴다.

### 11. 더 있는 것은 「삼킴 스위치」다 — 그리고 난이도가 정반대다

**왜 그런가**

```text
   try / finally  (25번)              with  (여기)

   try:                               with 객체 as x:
       몸통                               몸통
   finally:                           (나가는 길)
       정리                               __exit__(타입, 값, tb)
                                          -> 참을 돌려주면 삼킨다

   ★ finally 에는 예외를 "보는" 길이 없다
     __exit__ 는 예외를 인자로 받는다
```

- ★★ **더 있는 것 둘** — **`__exit__` 는 예외를 인자로 받고**, **참을 돌려주는 것만으로 삼킨다.**
  그리고 **그 한 벌이 객체에 들어가 이름이 붙어 재사용된다.**
- ★ **난이도가 정반대다.**
  - [25번](../25-exceptions-and-finally/2-summary.md)의 `finally` 로 예외를 삼키려면
    **`return`·`break`·`continue` 로 그 절을 빠져나가야** 한다 — **실수로 하기 쉽지만 눈에는 보인다.**
  - `__exit__` 는 **참을 돌려주기만 하면** 삼킨다 — **`return 로그찍기()` 한 줄로도 일어나고, 눈에 안 보인다.**
  - 그래서 **`with` 쪽이 더 조용히 사고가 난다.**
- ★ `@contextmanager` 는 둘을 이어 쓴다 —
  **[24번](../24-decorators/2-summary.md)의 데코레이터**가 함수를 **팩토리로 바꾸고**,
  **[17번](../17-generators-yield/2-summary.md)의 `throw()`** 가 몸통의 예외를 **`yield` 자리로 던져 넣는다.**

### 12. 세 층과 이웃 경계

**왜 그런가**

**언어 보장**(레퍼런스·PEP 가 정한 것)

- **등가식** — `__exit__` 를 먼저 찾아 두고 `__enter__` 를 부르며, `try` 는 그 **뒤에** 시작한다.
- **`as` 가 받는 것은 `__enter__` 의 반환값**이다.
- ★ **`__exit__` 가 참이면 삼키고 거짓이면 다시 던진다.** 예외가 없으면 `(None, None, None)`.
- **여러 개는 중첩과 같고 해제는 역순**이다.
- ★ **`__enter__` 가 터지면 그 객체의 `__exit__` 는 안 불린다.**
- **특수 메서드는 타입에서 찾는다**(3.3.1).
- `@contextmanager` 는 **한 번만 `yield`** 해야 한다 · `suppress` 는 **지정한 것만** 삼킨다 ·
  `ExitStack` 은 **등록 역순**으로 푼다.
- 괄호 다중 `with` 는 **3.10+**.

**CPython 구현 세부사항**

- ★ **`ExitStack` 의 `_fix_exception_context` 가 `__context__` 가 `None` 이면 그냥 돌아간다**
  (`/usr/lib/python3.12/contextlib.py` 의 `see issue 20317` 주석).
- 그래서 **몸통이 멀쩡할 때 먼저 난 정리 예외가 사슬에서 사라진다.**
- 내부 클래스 이름 `_GeneratorContextManager` 와 재사용 시 문구.
- `TypeError` 문구가 셋으로 갈리는 것(`(missed __exit__ method)` 가 붙는 자리).
- `RuntimeError: generator didn't stop after throw()`.

**이 판(3.12.3)의 관찰**

- 내부 클래스 이름과 예외 문구 전부.
- `ExitStack` 의 사슬이 한 칸인 것 — ★ **구현 쪽 문제로 보이므로 판이 오르면 다시 던져야 한다.**
- `contextlib.py` 의 **절대경로**가 트레이스백에 박히는 것 —
  **그래서 이 문서는 트레이스백을 한 줄도 안 실었다.**

★ **6번 문항에서 갈린 것은 CPython 구현 층**이다.
언어가 정한 것은 「`__exit__` 가 나가는 길에서 불린다」까지이고,
**여러 정리 예외를 어떻게 잇느냐는 `contextlib` 이 정한다.**

**이웃 경계 한 줄씩**

- **`async with` 와 `__aenter__`/`__aexit__` 는 `목록의 **51번 주제**`·`목록의 **52번 주제**`** 다.
  여기는 **동기 판**만 다룬다.
- **`with open(...)` 의 실무(모드·인코딩·`newline`)는 `목록의 **48번 주제**`** 다.
  여기는 **`with` 라는 문법**까지다.
- **`try/finally` 자체는 [25번](../25-exceptions-and-finally/2-summary.md)** 이고,
  **`contextlib.suppress` 를 고르는 판단은 [26번](../26-eafp-vs-lbyl/2-summary.md)**,
  **정리 예외를 묶음으로 만드는 이야기는 [27번](../27-exception-groups-and-except-star/2-summary.md)** 이다
  — 다만 **여기서는 묶음이 안 만들어진다**는 것이 6번 답의 결론이다.

## 실행 검증

| 무엇 | 어디서 | 몇 번 | 구현 의존인가 |
|---|---|---|---|
| `__enter__`/`__exit__` 계약과 세 인자 | `python3` 3.12.3 · Linux x86_64 | 캡처 + 제출 전 재실행 | **아니다** — 8.5 등가식 |
| `__exit__` 반환값 **일곱 가지** | 〃 | 〃 | **아니다** — 진릿값 규칙 |
| 해제 역순 · 다중 = 중첩 | 〃 | 〃 | **아니다** |
| `__enter__` 실패 시 `__exit__` 미호출 | 〃 | 〃 | **아니다** — 등가식 |
| 특수 메서드 타입 조회 · `TypeError` 문구 셋 | 〃 | 〃 | 규칙은 명세, **문구는 구현** |
| `@contextmanager` 의 `yield` 전후와 `throw` | 〃 | 〃 | **아니다** |
| 제너레이터 삼킴 · 두 번 `yield` | 〃 | 〃 | 동작은 명세, **문구는 구현** |
| `suppress`·`closing`·`ExitStack`·`callback` | 〃 | 〃 | **아니다** |
| 재사용 시 `AttributeError` | 〃 | 〃 | ★ **문구·클래스 이름은 구현** |
| ★ **`ExitStack` 의 `__context__` 유실** | 〃 + `contextlib.py` 소스를 읽음 | 〃 | ★★ **그렇다 — CPython 3.12.3** |
| **안 돌려 본 것** | 3.9 이하의 괄호 다중 `with` · `async with`·`AsyncExitStack` · `ContextDecorator` · 다른 판의 `ExitStack` 사슬 | — | — |

★ **판이 오르면 다시 돌릴 것** — **6번의 `ExitStack` 사슬**과 **10번의 클래스 이름·문구**다.
나머지는 등가식에 묶여 있다.
