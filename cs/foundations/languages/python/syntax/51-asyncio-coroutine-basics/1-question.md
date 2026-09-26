# python/syntax/51-asyncio-coroutine-basics — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> ★★★ 1·3번은 **표준 출력과 표준 오류를 따로** 적는다 — 한 파일을 두 번 던져 두 블록으로 받는다.
> ★★ 이 주제는 **시간을 묻지 않는다** — 한 번도 재지 않았다.
>
> 실행 환경: `python3` **3.12.3** · Linux(10번은 `python3.11` 3.11.15 도 함께, 3번은 `node` v18.19.1 도 함께). 던지는 형태는 `python3 - <파일` 이다.
> ★ 선행 — [17](../17-generators-yield/1-question.md)(제너레이터 · `send` · `StopIteration.value`).

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 코루틴 함수를 부르기만 하는 파일 — 표준 출력과 표준 오류 (예측)

```text
같은 파일을 네 번 던진다 — ① 2>/dev/null ② 2>&1 >/dev/null ③ -W error::RuntimeWarning 에 2>/dev/null ④ ③ 의 표준 오류에서 「Exception ignored in」 으로 시작하는 줄 수.
네 블록의 줄과 종료 코드를 적는다.
```

```python
# e51_call.py
# No asyncio import. Define a coroutine function and only call it.
async def f():
    print("in f")


print("before f()")
f()
print("after f()")
```

### 2. ★★★ 경고가 기록되는 자리 — 일곱 단계의 개수와 줄 번호 (예측)

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

### 3. ★★★ 몸통이 `await` 전에 던지는 함수 — 파이썬 두 블록, node 두 블록 (예측)

```text
파이썬은 ① 2>/dev/null ② 2>&1 >/dev/null, node 는 ③ hooks 인자 ④ 인자 없이 2>/dev/null. 네 블록의 줄과 종료 코드를 적는다.
```

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

### 4. ★★★ 루프 없이 `send` 로 한 걸음씩 (예측)

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

### 5. ★★ `asyncio.run` 을 두 번 · 루프 밖 · 예외 · 코루틴 아닌 것 (예측)

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

### 6. ★★ 두 가지 순서로 `await` 하기 (예측)

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

### 7. ★★★ 루프가 없으면 무엇이 안 되나 (왜)

* 루프 없이 `send(None)` 만으로 `asyncio.sleep(0)` 과 `asyncio.sleep(0.01)` 을 돌리면 각각 어디까지 가나 — 둘이 **왜** 갈리나?
* 그 차이로 「이벤트 루프가 하는 일」을 한 문장으로 말하면? 「루프가 코루틴을 멈춘다」는 왜 틀린 문장인가?

### 8. ★★ 코루틴은 제너레이터인가 (경계)

* `type` · `inspect.isgenerator` · `collections.abc.Iterator` · `next()` 로 물으면 코루틴은 각각 무엇이라 답하나 — 제너레이터와 **같은 것**과 **다른 것**을 하나씩?
* 「몸통이 아직 안 돌았다」를 **로그 없이** 확인하려면 어느 함수를 쓰나?

### 9. ★★ `await` 의 자리와 대상 (경계)

* `await 42` · `await f`(괄호 없음) · `def` 안의 `await` · 모듈 맨 위의 `await` 는 각각 어떤 예외 **타입**인가 — 실행 중인가, 컴파일 때인가?
* `async def` 안에 `yield` 를 쓰면 무엇이 되고, `yield from` 과 값 있는 `return` 은?

### 10. ★★ 도는 루프 안의 `asyncio.run` · 그리고 판 (경계)

* 루프 안에서 `asyncio.run(inner())` 를 부르면 무엇이 나오고, `inner` 의 몸통은 도나 — 경고는?
* 이 주제의 탐침 여덟 줄을 3.11 과 3.12 에 던지면 몇 칸이 갈리나 — 그 결과를 「보장」으로 적으면 왜 틀리나?

### 11. 층 가르기 (경계)

* 「부르면 코루틴 객체를 돌려준다」·「두 번 `await` 하면 `RuntimeError`」·「`asyncio.run` 은 끝에 루프를 닫는다」·「never awaited 경고가 난다」·「그 경고가 `del` 하는 줄에서 난다」 —
  각각 **언어 레퍼런스 · `asyncio` 문서 · CPython 구현** 중 어디인가?
* ★ `asyncio-dev` 문서는 경고를 누가 낸다고 적는데, 1번 파일로 보면 그 주어는 왜 넓은가?

### 12. 이웃 주제와의 경계 (연결)

* ★ [17번](../17-generators-yield/2-summary.md)의 「끝난 제너레이터에 `next`」와 이 주제의 「끝난 코루틴에 `send`」는 각각 무엇을 내나 — 첫 `send` 에 `None` 이 아닌 값을 주면 두 문구는 어디가 다른가?
* ★ [JS 39번 동작 (9)](../../../js/syntax/39-async-await/2-summary.md)의 「부른 순간」 결과와 3번을 이으면, JS 로 옮긴 코드의 `f()` 한 줄은 파이썬에서 무엇을 잃나? 겹쳐 돌리는 도구는 어느 주제로 넘어가나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|---|---|---|---|
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |
