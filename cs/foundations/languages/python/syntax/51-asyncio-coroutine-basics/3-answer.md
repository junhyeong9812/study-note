# python/syntax/51-asyncio-coroutine-basics — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> [1-question.md](1-question.md)의 번호와 **1:1**로 대응한다. 질문 12개 = 답 12개.
>
> 이 파일의 모든 출력은 `python3` **3.12.3** 과 `python3.11` **3.11.15**(Linux, x86_64), 그리고 `node` **v18.19.1** 에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> 던지는 형태는 `python3 - <파일` 로 고정했고, **표준 출력과 표준 오류는 따로 던져 따로 실었다.** ★ **시간은 한 번도 재지 않았다.**

## 정답

### 1. 표준 출력은 `before f()`·`after f()` 두 줄(`in f` 없음) · 표준 오류는 `<stdin>:7: RuntimeWarning: coroutine 'f' was never awaited` 와 안내 한 줄 · `-W error` 여도 `after f()` 가 찍히고 `exit 0`, `Exception ignored in` 한 덩어리

**출력**

```python
# e51_call.py
# No asyncio import. Define a coroutine function and only call it.
async def f():
    print("in f")


print("before f()")
f()
print("after f()")
```

```text
===== cd e51_call && python3 - <e51_call.py 2>/dev/null =====
before f()
after f()
(exit 0)
```

```text
===== cd e51_call && python3 - <e51_call.py 2>&1 >/dev/null =====
<stdin>:7: RuntimeWarning: coroutine 'f' was never awaited
RuntimeWarning: Enable tracemalloc to get the object allocation traceback
(exit 0)
```

```text
===== cd e51_call && python3 -W error::RuntimeWarning - <e51_call.py 2>/dev/null =====
before f()
after f()
(exit 0)
```

```text
===== cd e51_call && echo "stderr lines that start with 'Exception ignored in': $(python3 -W error::RuntimeWarning - <e51_call.py 2>&1 >/dev/null | grep -c '^Exception ignored in')" =====
stderr lines that start with 'Exception ignored in': 1
(exit 0)
```

**왜 그런가**

* ★★★ **코루틴 함수를 부르면 코루틴 객체만 나오고 몸통은 안 돈다** — 문서 *"Note that simply calling a coroutine will not schedule it to be executed"*. 받은 이름이 없으니 문장 끝에서 사라지고, 그때 **CPython 이** 경고한다(이 파일은 `asyncio` 를 가져오지도 않았다).
* ★★★ **경고는 실패가 아니다** — `exit 0`. `-W error` 로 예외로 바꿔도 **소멸 과정 안**에서 난 예외라 호출자에게 못 가고 `Exception ignored in` 으로 버려진다 — 여전히 `exit 0` 이고 `after f()` 가 찍힌다.

### 2. `0`·`0`·`1`(`del x` 18행)·`2`(`f()` 21행)·`2`(순환이라 안 사라짐)·`3`(`gc.collect()` 28행)·`3`(`close()` 뒤는 경고 없음)

**출력**

```python
# e51_when.py
# When does the "never awaited" warning fire? Warnings are recorded and printed to stdout.
import gc
import warnings


async def f():
    print("in f")


with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")

    c = f()
    print("[1] c = f()                     ; recorded:", len(w))
    x = c
    del c
    print("[2] del c (x still refers)      ; recorded:", len(w))
    del x
    print("[3] del x                       ; recorded:", len(w))

    f()
    print("[4] bare f() statement          ; recorded:", len(w))

    box = [f()]
    box.append(box)
    del box
    print("[5] del of a self-referencing list ; recorded:", len(w))
    gc.collect()
    print("[6] gc.collect()                ; recorded:", len(w))

    c = f()
    c.close()
    del c
    print("[7] c.close() then del c        ; recorded:", len(w))

for i, m in enumerate(w, 1):
    print("  #%d %s ; %s ; line %d" % (i, m.category.__name__, m.message, m.lineno))
```

```text
===== python3 - <e51_when.py =====
[1] c = f()                     ; recorded: 0
[2] del c (x still refers)      ; recorded: 0
[3] del x                       ; recorded: 1
[4] bare f() statement          ; recorded: 2
[5] del of a self-referencing list ; recorded: 2
[6] gc.collect()                ; recorded: 3
[7] c.close() then del c        ; recorded: 3
  #1 RuntimeWarning ; coroutine 'f' was never awaited ; line 18
  #2 RuntimeWarning ; coroutine 'f' was never awaited ; line 21
  #3 RuntimeWarning ; coroutine 'f' was never awaited ; line 28
(exit 0)
```

**왜 그런가**

* ★★★ **경고는 코루틴이 사라지는 순간에 난다** — 이름이 둘이면 `del` 하나로는 안 사라지고(`[2]`), 마지막 이름이 사라질 때(`[3]`, `line 18`). **만든 줄(13)이 아니다.**
* ★★ **자기 자신을 품은 리스트**는 참조 계수가 0 이 안 되어 `del` 로 안 사라진다 — **순환 수집이 돈 28행**이 경고의 줄이 된다.
* ★ **`close()` 로 닫으면** 「끝난 것」으로 표시되어 경고 대상이 아니다(문서 — *"marked as having finished executing, even if it was never started"*).

### 3. 파이썬은 `f: line 1` 없이 `caller:` 세 줄 + 표준 오류에 never awaited(10행) · `exit 0` / node 는 `f: line 1` 이 `caller: after` 앞 · 훅이 있으면 `unhandledRejection(boom)` 에 `exit 0`, 없으면 `exit 1`

**출력**

```python
# e51_pair.py
# Python: the body raises before any await. The caller only calls it.
async def f():
    print("f: line 1")
    raise ValueError("boom")


print("caller: before f()")
c = f()
print("caller: after f() -- got", type(c).__name__)
del c
print("caller: end")
```

```text
===== cd e51_pair && python3 - <e51_pair.py 2>/dev/null =====
caller: before f()
caller: after f() -- got coroutine
caller: end
(exit 0)
```

```text
===== cd e51_pair && python3 - <e51_pair.py 2>&1 >/dev/null =====
<stdin>:10: RuntimeWarning: coroutine 'f' was never awaited
RuntimeWarning: Enable tracemalloc to get the object allocation traceback
(exit 0)
```

```javascript
// e51_pair.js
// JS: the same shape. argv[2] === "hooks" installs node's rejection hook (printed to stdout).
if (process.argv[2] === "hooks") {
  process.on("unhandledRejection", (r) => console.log("unhandledRejection(" + r.message + ")"));
}
async function f() {
  console.log("f: line 1");
  throw new Error("boom");
}
console.log("caller: before f()");
const p = f();
console.log("caller: after f() -- got " + p.constructor.name);
console.log("caller: end");
```

```text
===== cd e51_pair && node e51_pair.js hooks =====
caller: before f()
f: line 1
caller: after f() -- got Promise
caller: end
unhandledRejection(boom)
(exit 0)
```

```text
===== cd e51_pair && node e51_pair.js 2>/dev/null =====
caller: before f()
f: line 1
caller: after f() -- got Promise
caller: end
(exit 1)
```

**왜 그런가**

* ★★★ **파이썬은 몸통이 안 돌았으니 `ValueError` 가 만들어지지도 않았다** — 남은 것은 `del c`(10행)에서 난 경고뿐이다.
* ★★★ **JS 의 `async` 함수는 부르는 순간 첫 `await` 까지 돈다** — 이 함수는 `await` 가 없어 끝까지 돌고 던진다. 던진 것은 **거부된 `Promise`** 가 되고 아무도 안 받았으니 미처리 거부 — node 18 은 기본으로 `exit 1`([JS 37번](../../../js/syntax/37-promise-state-model/2-summary.md)이 정본).
* ★★ 두 「보고」는 뜻이 다르다 — JS 는 **돌았는데 실패를 아무도 안 받았다**, 파이썬은 **돌지도 않았다.**

### 4. `'p1'` → `'p2'` → `StopIteration` 의 `value = (10, 20)` · 끝난 뒤 `send` 는 `RuntimeError` · 첫 `send(1)` 은 `TypeError` · `outer.send(None)` 이 `'from-inner'`, `send(5)` 가 `12` · 손 드라이버는 `((None, None), 2)`

**출력**

```python
# e51_manual.py
# Drive coroutines by hand with send(), with no event loop at all.
import inspect


class Pause:
    """An awaitable whose __await__ yields once, then returns what it was sent."""

    def __init__(self, tag):
        self.tag = tag

    def __await__(self):
        got = yield self.tag
        return got


async def g():
    print("   g: start")
    a = await Pause("p1")
    print("   g: resumed with", a)
    b = await Pause("p2")
    print("   g: resumed with", b)
    return (a, b)


print("[1] one coroutine, three send() calls")
c = g()
print("state:", inspect.getcoroutinestate(c))
print("send(None) ->", repr(c.send(None)), "; state:", inspect.getcoroutinestate(c))
print("send(10)   ->", repr(c.send(10)), "; state:", inspect.getcoroutinestate(c))
try:
    c.send(20)
except StopIteration as e:
    print("send(20)   -> StopIteration, value =", e.value)
print("state:", inspect.getcoroutinestate(c))

print("[2] send() after it finished")
try:
    c.send(None)
except Exception as e:
    print(type(e).__name__, "|", e)

print("[3] send(1) as the first call")
c2 = g()
try:
    c2.send(1)
except Exception as e:
    print(type(e).__name__, "|", e)
c2.close()


async def outer():
    print("   outer: before await inner()")
    v = await inner()
    print("   outer: inner returned", v)
    return v * 2


async def inner():
    print("   inner: before await Pause")
    v = await Pause("from-inner")
    return v + 1


print("[4] await of a coroutine: who does outer.send() reach?")
o = outer()
print("outer.send(None) ->", repr(o.send(None)))
try:
    o.send(5)
except StopIteration as e:
    print("outer.send(5)    -> StopIteration, value =", e.value)


def run_by_hand(coro):
    """The smallest driver: keep calling send(None) until StopIteration."""
    n = 0
    while True:
        try:
            coro.send(None)
            n += 1
        except StopIteration as e:
            return e.value, n


print("[5] a hand-written driver")
print("run_by_hand(g()) ->", run_by_hand(g()))
```

```text
===== python3 - <e51_manual.py =====
[1] one coroutine, three send() calls
state: CORO_CREATED
   g: start
send(None) -> 'p1' ; state: CORO_SUSPENDED
   g: resumed with 10
send(10)   -> 'p2' ; state: CORO_SUSPENDED
   g: resumed with 20
send(20)   -> StopIteration, value = (10, 20)
state: CORO_CLOSED
[2] send() after it finished
RuntimeError | cannot reuse already awaited coroutine
[3] send(1) as the first call
TypeError | can't send non-None value to a just-started coroutine
[4] await of a coroutine: who does outer.send() reach?
   outer: before await inner()
   inner: before await Pause
outer.send(None) -> 'from-inner'
   outer: inner returned 6
outer.send(5)    -> StopIteration, value = 12
[5] a hand-written driver
   g: start
   g: resumed with None
   g: resumed with None
run_by_hand(g()) -> ((None, None), 2)
(exit 0)
```

**왜 그런가**

* ★★★ **`await` 는 `__await__` 의 `yield` 를 통과해 바깥까지 값을 내민다** — `send(None)` 이 첫 `await` 까지 돌고 `'p1'` 을 받아 온다. 다음 `send(10)` 의 `10` 이 `await` 식의 값이다.
* ★★★ **끝나면 `StopIteration.value` 가 반환값** — [17번](../17-generators-yield/2-summary.md)의 제너레이터와 같은 기계. 문서 — *"the exception's `value` attribute holds the return value."*
* ★★ **`await inner()` 는 통로다** — `outer` 에 보낸 것이 `inner` 의 `Pause` 까지 내려가고, 그 팻말이 `outer` 바깥까지 올라온다(17번의 `yield from` 과 같은 모양).
* ★ **끝난 코루틴은 `RuntimeError`**(제너레이터는 조용히 `StopIteration` — 17번) · 첫 호출에 값은 `TypeError`.

### 5. 결과 `A`·`B` · 두 루프는 다른 객체(`False`) · 둘 다 닫힘 · 루프 밖 `get_running_loop()` 는 `RuntimeError` · 예외는 그대로 · `run(42)` 는 `ValueError`

**출력**

```python
# e51_run.py
# asyncio.run: what loop does it use, and what is left afterwards?
import asyncio

loops = []


async def main(tag):
    loop = asyncio.get_running_loop()
    loops.append(loop)
    print("  %s: running=%s closed=%s" % (tag, loop.is_running(), loop.is_closed()))
    await asyncio.sleep(0)
    return tag.upper()


async def raises():
    await asyncio.sleep(0)
    raise ValueError("from main")


print("[1] result:", asyncio.run(main("a")))
print("[2] result:", asyncio.run(main("b")))
print("[3] the two loops are the same object:", loops[0] is loops[1])
print("[4] closed afterwards:", [lp.is_closed() for lp in loops])

print("[5] get_running_loop() outside any loop")
try:
    asyncio.get_running_loop()
except Exception as e:
    print("   ", type(e).__name__, "|", e)

print("[6] the exception raised by main")
try:
    asyncio.run(raises())
except Exception as e:
    print("   ", type(e).__name__, "|", e)

print("[7] asyncio.run(42)")
try:
    asyncio.run(42)
except Exception as e:
    print("   ", type(e).__name__, "|", e)
```

```text
===== python3 - <e51_run.py =====
  a: running=True closed=False
[1] result: A
  b: running=True closed=False
[2] result: B
[3] the two loops are the same object: False
[4] closed afterwards: [True, True]
[5] get_running_loop() outside any loop
    RuntimeError | no running event loop
[6] the exception raised by main
    ValueError | from main
[7] asyncio.run(42)
    ValueError | a coroutine was expected, got 42
(exit 0)
```

**왜 그런가**

* ★★★ **`asyncio.run` 은 부를 때마다 새 루프를 만들고 끝에 닫는다** — 문서 *"otherwise `asyncio.new_event_loop()` is used. The loop is closed at the end."* 그래서 `is` 가 `False`, `is_closed()` 가 둘 다 `True`.
* ★★ `main` 의 반환값과 예외가 **그대로** 호출자에게 온다. 루프 밖에는 **도는 루프가 없다**(`[5]`).

### 6. `A start > A end > B start > B end` / `both created > B start > B end > A start > A end`

**출력**

```python
# e51_sequence.py
# Two awaits in a row, and two coroutines created before either is awaited.
import asyncio

log = []


async def job(name):
    log.append(name + " start")
    await asyncio.sleep(0)
    log.append(name + " end")


async def one_after_another():
    await job("A")
    await job("B")


async def create_then_await():
    a = job("A")
    b = job("B")
    log.append("both created")
    await b
    await a


for main in (one_after_another, create_then_await):
    log.clear()
    asyncio.run(main())
    print("%-18s: %s" % (main.__name__, " > ".join(log)))
```

```text
===== python3 - <e51_sequence.py =====
one_after_another : A start > A end > B start > B end
create_then_await : both created > B start > B end > A start > A end
(exit 0)
```

**왜 그런가**

* ★★★ **`await` 두 줄은 차례로 돈다** — 첫 `await` 가 끝나야 둘째 줄로 간다. `sleep(0)` 으로 양보해도 **루프에 올라간 다른 일이 없다.**
* ★★★ **만든 순서가 아니라 `await` 한 순서** — 만들 때는 몸통이 안 돈다(1번). 겹쳐 돌리려면 [52번](../52-asyncio-concurrency-structure/2-summary.md)의 태스크가 필요하다.

### 7. `sleep(0)` 은 `None` 을 한 번 내밀고 끝 · `sleep(0.01)` 은 첫 `send` 에서 `RuntimeError | no running event loop` — 루프는 「팻말을 받아 두었다가 때가 되면 `send` 를 불러 주는 쪽」

**출력**

```python
# e51_noloop.py
# Hand-drive asyncio.sleep(0) and asyncio.sleep(0.01) with send(None) -- no loop is running.
import asyncio

for label, make in [("sleep(0)", lambda: asyncio.sleep(0)),
                    ("sleep(0.01)", lambda: asyncio.sleep(0.01))]:
    c = make()
    steps = []
    try:
        while True:
            steps.append(repr(c.send(None)))
    except StopIteration as e:
        print("%-11s: yielded %s ; StopIteration value=%r" % (label, steps, e.value))
    except RuntimeError as e:
        print("%-11s: yielded %s ; RuntimeError | %s" % (label, steps, e))
```

```text
===== python3 - <e51_noloop.py =====
sleep(0)   : yielded ['None'] ; StopIteration value=None
sleep(0.01): yielded [] ; RuntimeError | no running event loop
(exit 0)
```

**왜 그런가**

* ★★ **`sleep(0)` 은 「한 번 양보」라는 팻말 하나**(이 판 소스로는 `@types.coroutine` 이 붙은 맨 `yield`) — 누가 받든 끝까지 간다.
* ★★★ **`sleep(0.01)` 은 「0.01 뒤에 다시 불러 줄 쪽」이 필요해 도는 루프를 찾는다** — 없으니 `RuntimeError`. 그 「다시 불러 주는 쪽」이 루프다.
* ★ 「루프가 코루틴을 멈춘다」가 틀린 까닭 — **코루틴이 스스로** `await` 에서 멈춘다. 4번의 손 드라이버는 루프 없이 멈추고 이었다.

### 8. 타입은 `coroutine`(`GeneratorType` 과 별개) · `isgenerator` `False` · `Iterator` 아님 · `next()` 는 `TypeError` / 같은 것은 `send`·`throw`·`close` · 로그 없이는 `inspect.getcoroutinestate` 가 `CORO_CREATED`

**출력**

```python
# e51_identity.py
# What is the object that calling a coroutine function returns?
import collections.abc as abc
import inspect
import types


async def f():
    return 42


def g():
    yield 1


c = f()
print("type(c).__name__               :", type(c).__name__)
print("type(c) is types.CoroutineType  :", type(c) is types.CoroutineType)
print("CoroutineType is GeneratorType  :", types.CoroutineType is types.GeneratorType)
print("inspect.iscoroutinefunction(f)  :", inspect.iscoroutinefunction(f))
print("inspect.iscoroutine(c)          :", inspect.iscoroutine(c))
print("inspect.isgenerator(c)          :", inspect.isgenerator(c))
print("isinstance(c, abc.Coroutine)    :", isinstance(c, abc.Coroutine))
print("isinstance(c, abc.Awaitable)    :", isinstance(c, abc.Awaitable))
print("isinstance(c, abc.Generator)    :", isinstance(c, abc.Generator))
print("isinstance(c, abc.Iterator)     :", isinstance(c, abc.Iterator))
print("hasattr send / throw / close    :", [hasattr(c, n) for n in ("send", "throw", "close")])
print("hasattr __next__ / __await__    :", [hasattr(c, n) for n in ("__next__", "__await__")])
print("getcoroutinestate(c)            :", inspect.getcoroutinestate(c))
print("type(c.__await__()).__name__    :", type(c.__await__()).__name__)

for label, op in [("next(c)", lambda: next(c)), ("iter(c)", lambda: iter(c)),
                  ("list(c)", lambda: list(c))]:
    try:
        op()
        print(label, ": no exception")
    except Exception as e:
        print(label, ":", type(e).__name__, "|", e)

print("inspect.iscoroutine(g())        :", inspect.iscoroutine(g()))
c.close()
print("after close, state              :", inspect.getcoroutinestate(c))
```

```text
===== python3 - <e51_identity.py =====
type(c).__name__               : coroutine
type(c) is types.CoroutineType  : True
CoroutineType is GeneratorType  : False
inspect.iscoroutinefunction(f)  : True
inspect.iscoroutine(c)          : True
inspect.isgenerator(c)          : False
isinstance(c, abc.Coroutine)    : True
isinstance(c, abc.Awaitable)    : True
isinstance(c, abc.Generator)    : False
isinstance(c, abc.Iterator)     : False
hasattr send / throw / close    : [True, True, True]
hasattr __next__ / __await__    : [False, True]
getcoroutinestate(c)            : CORO_CREATED
type(c.__await__()).__name__    : coroutine_wrapper
next(c) : TypeError | 'coroutine' object is not an iterator
iter(c) : TypeError | 'coroutine' object is not iterable
list(c) : TypeError | 'coroutine' object is not iterable
inspect.iscoroutine(g())        : False
after close, state              : CORO_CLOSED
(exit 0)
```

**왜 그런가**

* ★★ 문서 — *"Coroutines also have the methods listed below, which are analogous to those of generators … However, unlike generators, coroutines do not directly support iteration."* 손잡이는 같고 **이터레이터가 아니다.**
* ★ 「특수한 제너레이터」는 **구현의 계보**로 읽는다 — 이 판의 타입은 별개다.

### 9. `await 42`·`await f` 는 실행 중 `TypeError` · `def` 안·모듈 맨 위의 `await` 는 컴파일 때 `SyntaxError` · `async def` + `yield` 는 비동기 제너레이터, `yield from`·값 있는 `return` 은 `SyntaxError`

**출력**

```python
# e51_await_errors.py
# What can follow await, and where can await / yield appear?
import asyncio
import inspect


async def f():
    return 1


def plain():
    return 1


async def probe():
    for label, make in [("await 42", lambda: 42),
                        ("await f    (no call)", lambda: f),
                        ("await plain()", plain),
                        ("await f()", f)]:
        try:
            v = await make()
            print(label, "->", v)
        except TypeError as e:
            print(label, "-> TypeError |", e)

asyncio.run(probe())

print("[compile] snippets:")
snippets = [
    "def h():\n    await f()\n",
    "await f()\n",
    "async def h():\n    yield 1\n",
    "async def h():\n    yield from [1]\n",
    "async def h():\n    yield 1\n    return 2\n",
]
for s in snippets:
    head = s.replace("\n", " / ").strip(" /")
    try:
        compile(s, "<snippet>", "exec")
        print("  ok          :", head)
    except SyntaxError as e:
        print("  SyntaxError :", head, "|", e.msg)


async def agen():
    yield 1

a = agen()
print("type(agen()).__name__:", type(a).__name__)
print("inspect.isasyncgen   :", inspect.isasyncgen(a))
print("inspect.iscoroutine  :", inspect.iscoroutine(a))
```

```text
===== python3 - <e51_await_errors.py =====
await 42 -> TypeError | object int can't be used in 'await' expression
await f    (no call) -> TypeError | object function can't be used in 'await' expression
await plain() -> TypeError | object int can't be used in 'await' expression
await f() -> 1
[compile] snippets:
  SyntaxError : def h(): /     await f() | 'await' outside async function
  SyntaxError : await f() | 'await' outside function
  ok          : async def h(): /     yield 1
  SyntaxError : async def h(): /     yield from [1] | 'yield from' inside async function
  SyntaxError : async def h(): /     yield 1 /     return 2 | 'return' with value in async generator
type(agen()).__name__: async_generator
inspect.isasyncgen   : True
inspect.iscoroutine  : False
(exit 0)
```

**왜 그런가**

* ★★ **`await` 뒤에는 awaitable**(`__await__` 가 있는 것)만 — 함수 **객체**와 `int` 는 아니다. `await f` 는 괄호를 빠뜨린 오타다.
* ★★ 문서 — *"Can only be used inside a coroutine function."* 그래서 `def` 안은 `'await' outside async function`.
* ★ `yield` 하나로 **코루틴이 아니라 `async_generator`** 가 된다 — `inspect.iscoroutine` 이 `False`.

### 10. `RuntimeError | asyncio.run() cannot be called from a running event loop` · `inner body` 없음 · never awaited 한 번 / 판 격자 `0 / 8` — 관찰이지 보장이 아니다

**출력**

```python
# e51_nested.py
# Call asyncio.run from inside a running loop. What is raised, and what happens to the coroutine passed in?
import asyncio
import warnings


async def inner():
    print("inner body")
    return 1


async def main():
    try:
        asyncio.run(inner())
    except Exception as e:
        print("[1]", type(e).__name__, "|", e)


with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    asyncio.run(main())
    print("[2] recorded:", len(w))
    for m in w:
        print("   ", m.category.__name__, ";", m.message)
```

```text
===== python3 - <e51_nested.py =====
[1] RuntimeError | asyncio.run() cannot be called from a running event loop
[2] recorded: 1
    RuntimeWarning ; coroutine 'inner' was never awaited
(exit 0)
```

```python
# e51_ver_probe.py
# One line per probe: "<probe>;<what came out>". Run by e51_ver.sh under two interpreters.
import asyncio
import gc
import inspect
import warnings


async def f():
    return 1


def show(name, fn):
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        try:
            out = repr(fn())
        except BaseException as e:
            out = "%s | %s" % (type(e).__name__, e)
        gc.collect()
        out += " ; warnings=" + ",".join(str(m.message) for m in w)
    print("%s;%s" % (name, out))


def call_only():
    f()


def send_first_value():
    c = f()
    try:
        c.send(1)
    finally:
        c.close()


def reuse():
    c = f()
    try:
        c.send(None)
    except StopIteration:
        pass
    c.send(None)


async def nested_main():
    asyncio.run(f())


show("call_only", call_only)
show("type_name", lambda: type(f()).__name__)
show("state_created", lambda: inspect.getcoroutinestate(f()))
show("send_first_value", send_first_value)
show("reuse", reuse)
show("next_on_coro", lambda: next(f()))
show("nested_run", lambda: asyncio.run(nested_main()))
show("run_42", lambda: asyncio.run(42))
```

```sh
# e51_ver.sh
#!/usr/bin/env bash
# Run the probe under python3.11 and python3; print both answers per probe and count the rows that differ.
set -u -o pipefail
a=$(python3.11 - <e51_ver_probe.py) || exit 1
b=$(python3 - <e51_ver_probe.py) || exit 1
echo "python3.11 = $(python3.11 -c 'import platform; print(platform.python_version())') ; python3 = $(python3 -c 'import platform; print(platform.python_version())')"
diffs=0 rows=0
while IFS=';' read -r name rest; do
  other=$(printf '%s\n' "$b" | grep "^$name;" | cut -d';' -f2-)
  rows=$((rows + 1))
  if [ "$rest" = "$other" ]; then mark=same; else mark=DIFFERENT; diffs=$((diffs + 1)); fi
  printf '%s\t%s\n  3.11: %s\n  3.12: %s\n' "$name" "$mark" "$rest" "$other"
done <<< "$a"
echo "rows that differ between the two versions: $diffs / $rows"
```

```text
===== cd e51_ver && bash e51_ver.sh =====
python3.11 = 3.11.15 ; python3 = 3.12.3
call_only	same
  3.11: None ; warnings=coroutine 'f' was never awaited
  3.12: None ; warnings=coroutine 'f' was never awaited
type_name	same
  3.11: 'coroutine' ; warnings=coroutine 'f' was never awaited
  3.12: 'coroutine' ; warnings=coroutine 'f' was never awaited
state_created	same
  3.11: 'CORO_CREATED' ; warnings=coroutine 'f' was never awaited
  3.12: 'CORO_CREATED' ; warnings=coroutine 'f' was never awaited
send_first_value	same
  3.11: TypeError | can't send non-None value to a just-started coroutine ; warnings=
  3.12: TypeError | can't send non-None value to a just-started coroutine ; warnings=
reuse	same
  3.11: RuntimeError | cannot reuse already awaited coroutine ; warnings=
  3.12: RuntimeError | cannot reuse already awaited coroutine ; warnings=
next_on_coro	same
  3.11: TypeError | 'coroutine' object is not an iterator ; warnings=coroutine 'f' was never awaited
  3.12: TypeError | 'coroutine' object is not an iterator ; warnings=coroutine 'f' was never awaited
nested_run	same
  3.11: RuntimeError | asyncio.run() cannot be called from a running event loop ; warnings=coroutine 'f' was never awaited
  3.12: RuntimeError | asyncio.run() cannot be called from a running event loop ; warnings=coroutine 'f' was never awaited
run_42	same
  3.11: ValueError | a coroutine was expected, got 42 ; warnings=
  3.12: ValueError | a coroutine was expected, got 42 ; warnings=
rows that differ between the two versions: 0 / 8
(exit 0)
```

**왜 그런가**

* ★★★ 문서 — *"This function cannot be called when another asyncio event loop is running in the same thread."* **`inner()` 는 인자라서 먼저 만들어졌고** 거절당해 안 돈 채 버려졌다 — 1번과 같은 경고.
* ★★ **`0 / 8` 은 두 판의 관찰**이다 — 예외 **문구**와 경고 **문구**는 CPython 의 것이라 판이 오르면 바뀔 수 있다. 근거로 쓸 것은 **타입**과 「몸통이 돌았나」다.
* ★ `nested_run` 행은 `gc.collect()` 를 넣어야 경고가 그 행 안에 잡혔다 — 트레이스백이 프레임을 붙들어 코루틴이 늦게 사라진다(2번의 순환과 같은 꼴).

### 11. 언어 레퍼런스 · 언어 레퍼런스 · `asyncio` 문서 · CPython 구현 · CPython 구현(참조 계수) — `asyncio-dev` 는 `asyncio` 가 낸다고 적지만 경고는 인터프리터가 낸다

* ★★ **「부르면 코루틴 객체」**(용어집) · **「두 번 `await` 하면 `RuntimeError`」**(데이터 모델, 3.5.2) — 언어 레퍼런스.
* ★★ **「`asyncio.run` 은 끝에 루프를 닫는다」** — `asyncio` 문서.
* ★★★ **「never awaited 경고」와 「그 시점」** — CPython. 언어는 *"automatically closed … when they are about to be destroyed"* 까지만 말하고, **언제 사라지나**(참조 계수 · 순환 수집)는 구현이다.
* ★★ `asyncio-dev` 의 *"asyncio will emit a `RuntimeWarning`"* 은 `asyncio` 를 쓰는 사람에게 한 말이다 — 1번 파일은 **`asyncio` 를 안 가져왔는데** 경고가 났다. 이 판에서 그 경고는 `warnings` 모듈의 `_warn_unawaited_coroutine` 을 거쳐 나온다(`-W error` 판의 버려진 덩어리에 그 이름이 찍혔다 — 경로가 박혀 싣지 않았다).

### 12. 제너레이터는 조용히 `StopIteration` · 코루틴은 `RuntimeError` · 첫 `send` 문구는 `generator`/`coroutine` 한 낱말만 다르다 / JS 의 `f()` 는 이미 일을 한다 — 파이썬으로 옮기면 그 일이 통째로 사라진다, 겹치기는 52번

* ★★ [17번](../17-generators-yield/2-summary.md) — `can't send non-None value to a just-started generator` 대 이 주제 4번의 `… just-started coroutine`. 끝난 뒤: 제너레이터는 `StopIteration`, 코루틴은 `cannot reuse already awaited coroutine`.
* ★★★ [JS 39번 동작 (9)](../../../js/syntax/39-async-await/2-summary.md) — JS 는 부른 순간 `f: line 1` 이 찍힌다. 그 `f()` 한 줄을 파이썬에 그대로 옮기면 **몸통·부작용·실패가 전부 사라지고** 경고 한 줄만 남는다(3번).
* ★★ **코루틴을 겹쳐 돌리는 도구**(`create_task`·`gather`·`TaskGroup`)와 취소·타임아웃은 [52번](../52-asyncio-concurrency-structure/2-summary.md), 스레드·프로세스와의 선택은 [53번](../53-gil-and-choosing-concurrency/2-summary.md).

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 부르기만 하기 | `cd e51_call && python3 - <e51_call.py` 를 네 가지로(출력만 · 오류만 · `-W error` 출력 · `-W error` 오류 줄 수) | 3(캡처 + 재대조 + `PYTHONHASHSEED` 바꾼 재캡처) | `in f` 없음 · 경고 7행 · `-W error` 도 `exit 0` |
| 경고 시점 | `python3 - <e51_when.py` | 3 | `0 0 1 2 2 3 3` · 18·21·28행 |
| JS 한 쌍 | `cd e51_pair && python3 …`(두 가지) · `node e51_pair.js`(두 가지) | 3 | 파이썬 `exit 0` · node 훅 `exit 0` / 기본 `exit 1` |
| 정체 | `python3 - <e51_identity.py` | 3 | `coroutine` · `CORO_CREATED` |
| 손으로 돌리기 | `python3 - <e51_manual.py` | 3 | `(10, 20)` · `12` · `((None, None), 2)` |
| 루프 없는 `sleep` | `python3 - <e51_noloop.py` | 3 | `['None']` / `no running event loop` |
| `asyncio.run` | `python3 - <e51_run.py` | 3 | `False` · `[True, True]` |
| 중첩 `run` | `python3 - <e51_nested.py` | 3 | `RuntimeError` · 경고 1 |
| `await` 자리 | `python3 - <e51_await_errors.py` | 3 | `TypeError` 셋 · `SyntaxError` 넷 |
| 차례 | `python3 - <e51_sequence.py` | 3 | 두 줄 |
| 판 격자 | `cd e51_ver && bash e51_ver.sh`(`python3.11` · `python3`) | 3 | **0 / 8** |

**구현 의존 항목** — 판이 오르면 다시 돌려야 하는 것.

| 항목 | 왜 |
|---|---|
| ★★ 경고의 **시점**과 줄 번호(2번) | 참조 계수·순환 수집은 CPython 의 것 — 다른 구현(PyPy 등)은 다를 수 있다 |
| 예외·경고 **문구** 전부 | 구현이다 |
| `sleep(0)` 이 내미는 팻말 | `asyncio` 의 내부(`__sleep0`) |
| node 의 `exit 1` | node 의 기본값(`--unhandled-rejections`) |

★ **안 흔들리는 칸** — 로그 줄의 **순서와 개수** · 예외 **타입** · 상태 이름 · 경고가 기록된 **줄 번호** · 판 격자 **「0 / 8」** · `(exit N)`.
★★ **이 주제가 한 번도 안 잰 것** — **시간**(부적용) · **3.13·3.14**(판 없음 — 못 잰 것) · 디버그 모드와 `tracemalloc` 트레이스백(절대 경로 — 안 실음).
