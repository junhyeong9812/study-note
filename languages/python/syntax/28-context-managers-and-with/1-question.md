# python/syntax/28-context-managers-and-with — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> ★★ 이 주제에서는 **「어떤 줄이 안 찍히나」가 답인 자리가 많다.**
> `__exit__` 가 **안 도는** 경우와 정리가 **안 되는** 경우를 짚어야 맞은 것이다.
> ★ 이 주제의 블록에는 **트레이스백이 한 줄도 없다** — `contextlib` 안에서 난 예외에는 **절대경로가 박혀**
> 다른 머신에서 재현이 안 되기 때문이다. 대신 **타입·메시지·`__context__` 사슬**을 찍었다.
>
> 실행 환경: `python3` **3.12.3** · Linux. 던지는 형태는 `python3 - <파일` 로 고정했다.
> ★ **이 주제는 [25번](../25-exceptions-and-finally/2-summary.md)·[17번](../17-generators-yield/2-summary.md)·[24번](../24-decorators/2-summary.md)·[05번](../05-truthiness-and-short-circuit/2-summary.md)을 전부 쓴다.**
> 막히면 그 넷 중 어느 것이 안 잡힌 것인지부터 짚어라.
> ★ **이 사슬은 [25](../25-exceptions-and-finally/1-question.md) → [26](../26-eafp-vs-lbyl/1-question.md) → [27](../27-exception-groups-and-except-star/1-question.md) → 28** 로 이어지고, **여기가 끝**이다.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. `as` 가 받는 것과 `__exit__` 가 받는 것 (예측)

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

- ①에서 **`as` 가 받은 것**은 무엇인가?
- ★ ①과 ②에서 `__exit__` 가 받은 **세 값**이 각각 무엇인가?
- ②에서 **「with 문 다음 줄」에 해당하는 줄이 찍히는가**?

### 2. 일곱 가지를 돌려주면 (예측)

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

- 일곱 묶음 중 **예외가 삼켜지는 것은 몇 개**이고 어느 값들인가?
- ★ 기준이 무엇인가 — 「`True` 인가」인가 다른 것인가?
- ★ `__exit__` 에서 **`return` 을 아예 안 쓰면** 어느 줄과 같아지는가?

### 3. 셋을 한 줄에 열면 (예측)

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

- ①과 ②의 출력이 **같은가 다른가**?
- ★ ③에서 **「몸통」이 찍히는가**? 닫히는 순서는?
- 괄호로 감싼 형태는 **몇 판부터**인가?

### 4. 여는 도중에 터지면 (예측)

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

- ①에서 **`BadEnter.__exit__` 가 찍히는가**?
- ★ ②에서 **`Good.__exit__` 는 찍히는가**? 둘의 답이 갈린다면 왜 갈리는가?
- 「몸통」 줄은 몇 번 찍히는가?

### 5. `yield` 앞뒤로 나뉜 것 (예측)

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

- ①에서 **`as` 가 받은 것**은 무엇인가?
- ★ ②에서 **몸통의 예외가 어디서 잡히는가** — 제너레이터 안인가 밖인가? 그리고 그 뒤 순서는?
- ★ ③에서 `managed` **자체**의 타입과 `managed(...)` 의 타입은 각각 무엇인가?

### 6. 닫다가 둘 다 터지면 (예측)

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

- 네 묶음에서 **밖으로 나온 예외**는 각각 무엇인가 — 같은가 다른가?
- ★★ **`__context__` 사슬이 네 묶음에서 전부 같은가**? 다르다면 **어느 묶음이 짧고 무엇을 잃었는가**?
- ★ 넷 중 **묶음(`ExceptionGroup`)이 된 것**이 있는가?

### 7. `__enter__` 를 인스턴스에 달아 두면 (경계)

- `obj.__enter__ = ...`·`obj.__exit__ = ...` 로 달아 두면 `with obj:` 가 되는가?
- ★ `hasattr(obj, "__enter__")` 는 무엇을 답하는가 — 그리고 그것으로 판정하면 왜 틀리는가?
- ★ `__exit__` **만** 없을 때와 `__enter__` **만** 없을 때 **에러 문구가 같은가**?

### 8. 제너레이터가 예외를 삼키려면 (경계)

- `@contextmanager` 안에서 예외를 **잡고 다시 안 던지면** 어떻게 되는가?
- ★ 예외가 온 뒤 **`yield` 를 또 하면** 무슨 예외가 나는가?
- `yield` 뒤의 정리 코드를 **`try/finally` 로 안 감싸면** 언제 문제가 되는가?

### 9. 표준이 주는 셋 (경계)

- `suppress`·`closing`·`ExitStack` 이 각각 **무엇을 풀어 주는가**?
- ★ `ExitStack` 의 `callback` 은 **컨텍스트와 같은 스택**에 쌓이는가 다른 스택인가?
- `close()` 만 있는 객체를 그냥 `with` 에 넣으면 무엇이 나는가?

### 10. 컨텍스트 매니저를 변수에 담아 두면 (경계)

- `@contextmanager` 로 만든 객체를 **두 번** `with` 에 넣으면 되는가?
- ★ 안 된다면 **무슨 예외**가 나고, **왜** 그런가?
- 재사용이 필요하면 무엇으로 쓰는가?

### 11. [25번](../25-exceptions-and-finally/2-summary.md)의 `try/finally` 와 무엇이 다른가 (연결)

- `with` 가 `try/finally` 로 **풀리는** 것이라면, **더 있는 것**은 무엇인가?
- ★ [25번](../25-exceptions-and-finally/2-summary.md)의 `finally` 는 어떻게 해야 예외를 삼키고,
  `__exit__` 는 어떻게 해야 삼키는가 — 둘의 **난이도**가 왜 다른가?
- ★ `@contextmanager` 가 [24번](../24-decorators/2-summary.md)·[17번](../17-generators-yield/2-summary.md)의 무엇을 각각 쓰는지 한 줄로 이을 수 있는가?

### 12. 세 층 가르기와 이웃 경계 (경계)

- 이 주제에서 **언어 보장** · **CPython 구현 세부사항** · **이 판(3.12.3)의 관찰**에 해당하는 것을 각각 둘 이상 댈 수 있는가?
- ★ 6번 문항에서 갈린 것은 **어느 층**인가?
- **`async with` 가 어디부터 다른 주제이고, `with open(...)` 의 실무가 어디부터인지** 한 줄로 그을 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
