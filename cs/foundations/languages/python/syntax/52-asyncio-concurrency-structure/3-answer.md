# python/syntax/52-asyncio-concurrency-structure — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> [1-question.md](1-question.md)의 번호와 **1:1**로 대응한다. 질문 12개 = 답 12개.
>
> 이 파일의 모든 출력은 `python3` **3.12.3** 과 `python3.11` **3.11.15**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> 던지는 형태는 `python3 - <파일` 로 고정했다. ★ **시간은 한 번도 찍지 않았다** — `sleep` 의 길이는 소스에만 있다.

## 정답

### 1. 갈린 칸 `4 / 9` — 예외 하나에 `gather` 는 형제 `finished`, `TaskGroup` 은 `cancelled` + `ExceptionGroup` · 자식 취소에 `gather` 는 `CancelledError`(`cancelling()` `0`) · 바깥 취소에는 둘 다 전부 `cancelled`

**출력**

```python
# e52_grid.py
import asyncio

STEPS = 4


async def walker(name, log, steps):
    # takes STEPS single steps (sleep(0) = give the loop one turn), then ends
    steps[name] = 0
    try:
        for _ in range(STEPS):
            await asyncio.sleep(0)
            steps[name] += 1
        log[name] = "finished"
        return name
    except asyncio.CancelledError:
        log[name] = "cancelled"
        raise


async def raiser(log, steps):
    steps["B"] = 0
    await asyncio.sleep(0)
    log["B"] = "raised"
    raise ValueError("b")


def describe(exc):
    if isinstance(exc, BaseExceptionGroup):
        inner = ", ".join("%s(%r)" % (type(e).__name__, str(e)) for e in exc.exceptions)
        return "%s[%s]" % (type(exc).__name__, inner)
    return "%s(%r)" % (type(exc).__name__, str(exc))


async def run_cell(structure, scenario):
    log = {"A": "-", "B": "-", "C": "-"}
    steps = {}
    seen = {}

    def record(what):
        seen["outer"] = what
        seen["cancelling"] = asyncio.current_task().cancelling()
        seen["A steps"] = steps.get("A")

    def make_b(spawn):
        if scenario == "one raises":
            return spawn(raiser(log, steps))
        b = spawn(walker("B", log, steps))
        if scenario == "one child cancelled":
            asyncio.get_running_loop().call_soon(b.cancel)
        return b

    async def body_gather(flag):
        a = asyncio.create_task(walker("A", log, steps))
        c = asyncio.create_task(walker("C", log, steps))
        b = make_b(asyncio.create_task)
        try:
            r = await asyncio.gather(a, b, c, return_exceptions=flag)
        except BaseException as e:
            record(describe(e))
            raise
        record("result " + repr([x if isinstance(x, str) else type(x).__name__ for x in r]))

    async def body_tg():
        try:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(walker("A", log, steps))
                tg.create_task(walker("C", log, steps))
                make_b(tg.create_task)
        except BaseException as e:
            record(describe(e))
            raise
        record("block exited normally")

    if structure == "TaskGroup":
        outer = asyncio.create_task(body_tg())
    else:
        outer = asyncio.create_task(body_gather(structure != "gather"))
    if scenario == "outer cancelled":
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        outer.cancel()
    try:
        await outer
    except BaseException:
        pass
    # give every leftover task time to reach its own end
    for _ in range(STEPS * 3):
        await asyncio.sleep(0)
    return [log["A"], log["B"], log["C"], seen["outer"], str(seen["cancelling"]), str(seen["A steps"])]


async def main():
    structures = ["gather", "gather(return_exceptions=True)", "TaskGroup"]
    scenarios = ["one raises", "one child cancelled", "outer cancelled"]
    table = {}
    print("structure;scenario;A;B;C;what the awaiting code saw;its cancelling();A steps at that moment")
    for sc in scenarios:
        for st in structures:
            row = await run_cell(st, sc)
            table[st, sc] = row
            print(";".join([st, sc] + row))
    # compare gather (default) with TaskGroup on A, C and what the awaiting code saw
    cells = 0
    differ = 0
    for sc in scenarios:
        g = table["gather", sc]
        t = table["TaskGroup", sc]
        for i in (0, 2, 3):
            cells += 1
            if g[i] != t[i]:
                differ += 1
    print("gather vs TaskGroup, cells that differ (A, C, seen x 3 scenarios): %d / %d" % (differ, cells))


asyncio.run(main())
```

```text
===== python3 - <e52_grid.py =====
structure;scenario;A;B;C;what the awaiting code saw;its cancelling();A steps at that moment
gather;one raises;finished;raised;finished;ValueError('b');0;3
gather(return_exceptions=True);one raises;finished;raised;finished;result ['A', 'ValueError', 'C'];0;4
TaskGroup;one raises;cancelled;raised;cancelled;ExceptionGroup[ValueError('b')];1;2
gather;one child cancelled;finished;cancelled;finished;CancelledError('');0;3
gather(return_exceptions=True);one child cancelled;finished;cancelled;finished;result ['A', 'CancelledError', 'C'];0;4
TaskGroup;one child cancelled;finished;cancelled;finished;block exited normally;0;4
gather;outer cancelled;cancelled;cancelled;cancelled;CancelledError('');1;0
gather(return_exceptions=True);outer cancelled;cancelled;cancelled;cancelled;CancelledError('');1;0
TaskGroup;outer cancelled;cancelled;cancelled;cancelled;CancelledError('');1;1
gather vs TaskGroup, cells that differ (A, C, seen x 3 scenarios): 4 / 9
(exit 0)
```

**왜 그런가**

* ★★★ **`one raises`** — `gather` 는 첫 예외를 **곧바로**(A 가 아직 3걸음일 때) 넘기고 형제는 **안 취소한다** — A·C 가 뒤에 혼자 `finished`. 문서 *"Other awaitables in the aws sequence **won't be cancelled** and will continue to run."*
  `TaskGroup` 은 형제를 **취소하고**(`cancelled`) 다 멈춘 뒤 **하나여도** `ExceptionGroup[ValueError('b')]` 로 올린다. → 이 사건에서 **3칸** 갈림.
* ★★ **`one child cancelled`** — `gather` 는 자식의 취소를 **예외처럼** 넘겨 기다리던 코드가 `CancelledError` 를 받는다. 그런데 **그 태스크는 취소 요청을 안 받았다**(`cancelling()` `0`). 형제는 `finished`.
  `TaskGroup` 은 `CancelledError` 를 실패로 안 쳐 **블록이 정상으로** 끝난다. → **1칸**.
* ★★★ **`outer cancelled`** — **`gather` 도 자식을 전부 취소한다**(*"If `gather()` is cancelled, all submitted awaitables … are also cancelled."*). 두 구조가 **한 칸도 안 갈린다.** → **0칸**. 합해서 **4 / 9**.
* ★ `return_exceptions=True` 는 형제 운명을 안 바꾸고 예외를 **결과 칸**으로 만들 뿐이다 — 바깥이 취소되면 여전히 `CancelledError`.

### 2. `await` 두 줄은 하나 끝나고 하나 · 태스크 둘은 `main: both tasks created` 가 먼저, 그 뒤 번갈아 · 기다리지 않은 태스크도 끝까지 돈다 · 결과는 인자 순서 `['slow', 'fast']`

**출력**

```python
# e52_task.py
import asyncio


async def job(name, log, steps=2):
    log.append(name + " start")
    for _ in range(steps):
        await asyncio.sleep(0)
    log.append(name + " end")
    return name


async def sequential():
    log = []
    await job("a", log)
    await job("b", log)
    return log


async def two_tasks():
    log = []
    ta = asyncio.create_task(job("a", log))
    tb = asyncio.create_task(job("b", log))
    log.append("main: both tasks created")
    await ta
    await tb
    return log


async def task_never_awaited():
    log = []
    asyncio.create_task(job("a", log))   # no await on it anywhere below
    log.append("main: task created")
    for _ in range(5):
        await asyncio.sleep(0)
    log.append("main: after five turns")
    return log


async def gather_order():
    log = []
    r = await asyncio.gather(job("slow", log, steps=4), job("fast", log, steps=1))
    return log + ["gather result: %r" % r]


async def main():
    for fn in (sequential, two_tasks, task_never_awaited, gather_order):
        print("[%s] " % fn.__name__ + " | ".join(await fn()))


asyncio.run(main())
```

```text
===== python3 - <e52_task.py =====
[sequential] a start | a end | b start | b end
[two_tasks] main: both tasks created | a start | b start | a end | b end
[task_never_awaited] main: task created | a start | a end | main: after five turns
[gather_order] slow start | fast start | fast end | slow end | gather result: ['slow', 'fast']
(exit 0)
```

**왜 그런가**

* ★★ **`await` 는 그 자리에서 한 코루틴을 끝까지 기다린다** — 두 줄이면 차례차례다([51번](../51-asyncio-coroutine-basics/2-summary.md)).
* ★★★ **`create_task` 는 예약만 한다** — 그래서 `main: both tasks created` 가 먼저이고, `main` 이 양보하는 순간 a·b 가 **한 걸음씩 번갈아** 걷는다.
* ★★★ **태스크는 `await` 가 없어도 돈다** — `task_never_awaited` 의 `a start | a end`. 코루틴 객체(부르기만 하면 안 돈다)와 **다른 점**이 이것이다.
* ★ `gather` 의 결과는 **인자 순서** — `fast` 가 먼저 끝나도 `['slow', 'fast']`.

### 3. `time.sleep` 은 `slow start | slow end | tick 0 | …` 로 끼어든 판 `0 / 5` · `asyncio.sleep`·`to_thread` 는 `slow start | tick 0 | tick 1 | tick 2 | slow end` 로 `5 / 5`

**출력**

```python
# e52_block.py
import asyncio
import time

RUNS = 5


async def slow(kind, log):
    log.append("slow start")
    if kind == "time.sleep":
        time.sleep(0.3)
    elif kind == "await asyncio.sleep":
        await asyncio.sleep(0.3)
    elif kind == "await asyncio.to_thread(time.sleep)":
        await asyncio.to_thread(time.sleep, 0.3)
    log.append("slow end")


async def ticker(log):
    for i in range(3):
        log.append("tick %d" % i)
        await asyncio.sleep(0.01)


async def one_run(kind):
    log = []
    s = asyncio.create_task(slow(kind, log))
    t = asyncio.create_task(ticker(log))
    await asyncio.gather(s, t)
    return log


def interleaved(log):
    # did any tick line land between "slow start" and "slow end"?
    a = log.index("slow start")
    b = log.index("slow end")
    return any(x.startswith("tick") for x in log[a + 1:b])


async def main():
    kinds = ["time.sleep", "await asyncio.sleep", "await asyncio.to_thread(time.sleep)"]
    for kind in kinds:
        logs = [await one_run(kind) for _ in range(RUNS)]
        print("[%s]" % kind)
        print("  distinct log orders over %d runs: %d" % (RUNS, len({tuple(x) for x in logs})))
        print("  first run: " + " | ".join(logs[0]))
        print("  ticks between slow start and slow end: %d / %d runs" % (sum(interleaved(x) for x in logs), RUNS))


asyncio.run(main())
```

```text
===== python3 - <e52_block.py =====
[time.sleep]
  distinct log orders over 5 runs: 1
  first run: slow start | slow end | tick 0 | tick 1 | tick 2
  ticks between slow start and slow end: 0 / 5 runs
[await asyncio.sleep]
  distinct log orders over 5 runs: 1
  first run: slow start | tick 0 | tick 1 | tick 2 | slow end
  ticks between slow start and slow end: 5 / 5 runs
[await asyncio.to_thread(time.sleep)]
  distinct log orders over 5 runs: 1
  first run: slow start | tick 0 | tick 1 | tick 2 | slow end
  ticks between slow start and slow end: 5 / 5 runs
(exit 0)
```

**왜 그런가**

* ★★★ **`time.sleep` 에는 `await` 가 없다** — 루프의 스레드가 그 자리에 **붙잡혀** 걸어 둔 `ticker` 조차 한 번도 못 돈다. `tick 0` 이 `slow end` **뒤**다.
  문서 — *"While a Task is running in the event loop, no other Tasks can run in the same thread."*
* ★★ **`await asyncio.sleep` 은 양보다** — 그동안 `tick` 셋이 전부 들어온다.
* ★★ **`to_thread` 는 조는 일을 다른 스레드로 옮긴다** — 루프 스레드는 `await` 에서 양보하므로 `asyncio.sleep` 과 **같은 로그**가 나온다.
* ★ 세 경우 모두 다섯 판이 **한 가지 순서**(`distinct log orders over 5 runs: 1`)였다.

### 4. 안쪽은 두 방식 모두 `CancelledError` + `finally` · `timeout` 블록 안에서도 `CancelledError`, 밖에서야 `TimeoutError` · `wait_for` 바깥은 `TimeoutError` · `asyncio.TimeoutError is TimeoutError` `True` · `CancelledError` 는 `Exception` 이 아니다

**출력**

```python
# e52_timeout.py
import asyncio


async def inner(log):
    log.append("inner start")
    try:
        await asyncio.sleep(10)
        log.append("inner end")
    except asyncio.CancelledError:
        log.append("inner got CancelledError")
        raise
    finally:
        log.append("inner finally")


async def with_timeout_cm():
    log = []
    try:
        async with asyncio.timeout(0.05):
            try:
                await inner(log)
            except BaseException as e:
                log.append("inside the block: " + type(e).__name__)
                raise
    except BaseException as e:
        log.append("outside the block: " + type(e).__name__)
    return log


async def with_wait_for():
    log = []
    try:
        await asyncio.wait_for(inner(log), 0.05)
    except BaseException as e:
        log.append("around wait_for: " + type(e).__name__)
    return log


async def main():
    print("[asyncio.timeout]")
    for line in await with_timeout_cm():
        print("  " + line)
    print("[asyncio.wait_for]")
    for line in await with_wait_for():
        print("  " + line)
    print("asyncio.TimeoutError is TimeoutError:", asyncio.TimeoutError is TimeoutError)
    print("TimeoutError is subclass of Exception:", issubclass(TimeoutError, Exception))
    print("CancelledError is subclass of Exception:", issubclass(asyncio.CancelledError, Exception))


asyncio.run(main())
```

```text
===== python3 - <e52_timeout.py =====
[asyncio.timeout]
  inner start
  inner got CancelledError
  inner finally
  inside the block: CancelledError
  outside the block: TimeoutError
[asyncio.wait_for]
  inner start
  inner got CancelledError
  inner finally
  around wait_for: TimeoutError
asyncio.TimeoutError is TimeoutError: True
TimeoutError is subclass of Exception: True
CancelledError is subclass of Exception: False
(exit 0)
```

**왜 그런가**

* ★★★ **타임아웃은 취소다** — 마감이 오면 `timeout` 은 **현재 태스크**를, `wait_for` 는 **안쪽 태스크**를 취소한다. 안쪽 코루틴이 보는 것은 **`CancelledError`** 다.
* ★★ **`TimeoutError` 로 바꾸는 것은 `timeout` 의 `__aexit__`** — 그래서 블록 **안**에서는 아직 `CancelledError`. 문서 *"the `TimeoutError` can only be caught *outside* of the context manager."*
* ★ 3.11 부터 `asyncio.TimeoutError` 는 **내장 `TimeoutError` 그 자체**(`is` 가 `True`). `CancelledError` 는 3.8 부터 `BaseException` 직속이라 `except Exception:` 에 안 걸린다.

### 5. 삼키면 `await` 가 값을 주고 `cancelled()` `False`(그러나 `cancelling()` `1`) · `timeout` 안에서 삼키면 `TimeoutError` 없이 블록 뒤로 · `TaskGroup` 의 형제가 삼키면 끝까지 가고 봉투는 그 뒤

**출력**

```python
# e52_swallow.py
import asyncio


async def plain():
    await asyncio.sleep(10)
    return "plain returned"


async def swallows():
    try:
        await asyncio.sleep(10)
    except asyncio.CancelledError:
        pass
    return "swallows returned"


async def report(label, coro_fn):
    t = asyncio.create_task(coro_fn())
    await asyncio.sleep(0)
    t.cancel()
    try:
        r = await t
        seen = "value %r" % r
    except asyncio.CancelledError:
        seen = "CancelledError"
    print("[%s] await gave: %s ; cancelled(): %s ; cancelling(): %d" % (label, seen, t.cancelled(), t.cancelling()))


async def timeout_over_swallower():
    log = []
    try:
        async with asyncio.timeout(0.05):
            try:
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                log.append("swallowed inside the block")
            log.append("block body reached its end")
        log.append("after the block, no exception")
    except TimeoutError:
        log.append("TimeoutError outside the block")
    log.append("cancelling() of this task: %d" % asyncio.current_task().cancelling())
    return log


async def group_with_swallower():
    log = []

    async def fail():
        await asyncio.sleep(0)
        raise ValueError("v")

    async def sibling():
        for i in range(3):
            try:
                await asyncio.sleep(0)
            except asyncio.CancelledError:
                log.append("sibling swallowed a cancel at step %d" % i)
        log.append("sibling reached its end")

    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(fail())
            tg.create_task(sibling())
    except* ValueError as eg:
        log.append("group raised " + repr([type(e).__name__ for e in eg.exceptions]))
    return log


async def main():
    await report("plain", plain)
    await report("swallows", swallows)
    t = asyncio.create_task(timeout_over_swallower())
    print("[timeout over a swallower]")
    for line in await t:
        print("  " + line)
    print("[TaskGroup with a swallowing sibling]")
    for line in await group_with_swallower():
        print("  " + line)


asyncio.run(main())
```

```text
===== python3 - <e52_swallow.py =====
[plain] await gave: CancelledError ; cancelled(): True ; cancelling(): 1
[swallows] await gave: value 'swallows returned' ; cancelled(): False ; cancelling(): 1
[timeout over a swallower]
  swallowed inside the block
  block body reached its end
  after the block, no exception
  cancelling() of this task: 0
[TaskGroup with a swallowing sibling]
  sibling swallowed a cancel at step 1
  sibling reached its end
  group raised ['ValueError']
(exit 0)
```

**왜 그런가**

* ★★ **취소는 「다음 `await` 에 꽂히는 예외」일 뿐이다** — 잡아서 안 던지면 태스크는 **정상 종료**한다. 요청을 받은 기록(`cancelling()`)만 남는다. 지우려면 `uncancel()` 이다(문서).
* ★★★ **`timeout` 은 「내가 건 취소가 `CancelledError` 로 돌아왔나」를 보고 `TimeoutError` 로 바꾼다** — 삼키면 돌아올 것이 없어 **블록이 정상으로 끝나고 마감은 조용히 사라진다.** 에러도 경고도 없다.
  문서 — *"might misbehave if a coroutine swallows `asyncio.CancelledError`."*
* ★★ **`TaskGroup` 도 형제 취소를 `CancelledError` 로 하므로** 삼킨 형제는 **멈추지 않고 끝까지** 간다 — 블록은 그 형제가 끝나길 기다린 뒤에야 봉투를 올린다.

### 6. `except*` 두 가지가 **둘 다** 돈다 · 맨 `except ValueError` 는 못 잡고 `except Exception` 이 `ExceptionGroup ['ValueError', 'KeyError']` 를 잡는다 · 몸통이 던지면 자식 `cancelled` + `ExceptionGroup [RuntimeError]`

**출력**

```python
# e52_eg.py
import asyncio


async def fail(exc):
    await asyncio.sleep(0)
    raise exc


async def walker(log):
    try:
        for _ in range(5):
            await asyncio.sleep(0)
        log.append("walker finished")
    except asyncio.CancelledError:
        log.append("walker cancelled")
        raise


async def two_fail():
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(fail(ValueError("v")))
            tg.create_task(fail(KeyError("k")))
    except* ValueError as eg:
        print("except* ValueError got:", [repr(e) for e in eg.exceptions])
    except* KeyError as eg:
        print("except* KeyError got:", [repr(e) for e in eg.exceptions])


async def two_fail_plain_except():
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(fail(ValueError("v")))
            tg.create_task(fail(KeyError("k")))
    except ValueError:
        print("plain except ValueError caught it")
    except Exception as e:
        print("plain except Exception caught:", type(e).__name__, [type(x).__name__ for x in e.exceptions])


async def body_raises():
    log = []
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(walker(log))
            await asyncio.sleep(0)
            raise RuntimeError("body")
    except BaseException as e:
        print("body raised ->", type(e).__name__, [repr(x) for x in e.exceptions], "|", log)


async def main():
    await two_fail()
    await two_fail_plain_except()
    await body_raises()


asyncio.run(main())
```

```text
===== python3 - <e52_eg.py =====
except* ValueError got: ["ValueError('v')"]
except* KeyError got: ["KeyError('k')"]
plain except Exception caught: ExceptionGroup ['ValueError', 'KeyError']
body raised -> ExceptionGroup ["RuntimeError('body')"] | ['walker cancelled']
(exit 0)
```

**왜 그런가**

* ★★ **`TaskGroup` 은 늘 봉투(`ExceptionGroup`)를 올린다** — `except ValueError` 는 봉투가 `ValueError` 가 아니라서 지나친다. `except*` 는 봉투를 **종류별로 쪼개** 각 가지에 준다([27번](../27-exception-groups-and-except-star/2-summary.md)이 정본).
* ★ 둘이 **같은 걸음에서** 실패해 **둘 다** 봉투에 들어갔다.
* ★ **몸통의 예외도 한 자식의 실패와 같게** 다룬다 — 자식을 취소하고 몸통의 예외를 봉투에 담는다.

### 7. 루프의 **타이머**가 `sleep` 중인 태스크를 쥐고 있어서다 — **혼자만 아는 퓨처**를 기다리면 `20 / 20` 사라진다 · 한 경우의 관찰은 문서의 「언제든」을 못 이긴다

```python
# e52_gc.py
import asyncio
import gc
import weakref

RUNS = 20


async def waits_on_future():
    fut = asyncio.get_running_loop().create_future()   # nobody else holds this future
    await fut


async def waits_on_sleep():
    await asyncio.sleep(10)                             # the loop's timer holds this one


async def one(coro_fn, keep):
    held = []
    task = asyncio.create_task(coro_fn())
    ref = weakref.ref(task)
    if keep:
        held.append(task)
    del task
    await asyncio.sleep(0)          # let the task start and suspend
    gc.collect()
    gone = ref() is None
    for t in held:
        t.cancel()
    return gone


async def main():
    reports = []
    asyncio.get_running_loop().set_exception_handler(lambda loop, ctx: reports.append(ctx["message"]))
    for name, fn in [("await on a lone future", waits_on_future), ("await asyncio.sleep", waits_on_sleep)]:
        for keep in (False, True):
            gone = sum([await one(fn, keep) for _ in range(RUNS)])
            print("%s ; reference kept: %s ; task object gone after gc.collect(): %d / %d runs" % (name, keep, gone, RUNS))
    print("loop exception handler messages (distinct):", sorted(set(reports)))
    print("count:", len(reports))
    # clean up the sleeping orphans before the loop closes
    for t in asyncio.all_tasks():
        if t is not asyncio.current_task():
            t.cancel()


asyncio.run(main())
```

```text
===== python3 - <e52_gc.py =====
await on a lone future ; reference kept: False ; task object gone after gc.collect(): 20 / 20 runs
await on a lone future ; reference kept: True ; task object gone after gc.collect(): 0 / 20 runs
await asyncio.sleep ; reference kept: False ; task object gone after gc.collect(): 0 / 20 runs
await asyncio.sleep ; reference kept: True ; task object gone after gc.collect(): 0 / 20 runs
loop exception handler messages (distinct): ['Task was destroyed but it is pending!']
count: 20
(exit 0)
```

* ★★ **`asyncio.sleep` 은 루프에 타이머를 건다** — 그 타이머 핸들이 태스크를 깨울 콜백을 쥐므로 **루프에서 닿는 길**이 있다. 참조를 버려도 `0 / 20`.
* ★★ **혼자만 아는 퓨처**를 기다리면 퓨처와 태스크가 **서로만** 쥔다 — 루프는 약한 참조뿐이라 `gc.collect()` 한 번에 `20 / 20` 사라지고 `Task was destroyed but it is pending!` 가 20번 온다.
* ★★★ **「해 봤는데 안 사라지더라」는 기다리는 대상이 무엇이었느냐에 달린 관찰**이다. 이것은 구현의 사정이고, 문서는 *"may get garbage collected at any time"* 이라 적었다 — 규칙은 **늘 쥔다**(쥐면 두 경우 모두 `0 / 20`).

### 8. `asyncio.current_task().cancelling()` 이 `0` 이면 나에 대한 취소가 아니다 — 1번의 `its cancelling()` 열

* ★★ `gather;one child cancelled` 행 — 기다리던 코드가 `CancelledError('')` 를 받았는데 `cancelling()` 은 **`0`**. `outer cancelled` 행은 **`1`** 이다. 이 열 하나가 둘을 가른다(3.11+).
* ★★ 가르지 않고 정리·종료하면 **아무도 취소하지 않은 태스크가 스스로 그만둔다** — 게다가 `CancelledError` 를 다시 던지면 **그 태스크가 `cancelled` 로 끝나** 위쪽도 「취소됐다」로 읽는다.

### 9. 조는 것은 **다른 스레드**이고 루프 스레드는 `await` 에서 양보한다 · CPU 계산에는 문서가 「GIL 때문에 대개 I/O 에만」이라 적는다 — 재는 것은 53번

* ★★ `to_thread(time.sleep, …)` 는 **블로킹 호출을 없앤 것이 아니라 자리를 옮긴 것**이다. 루프 스레드가 붙잡히지 않으니 `tick` 이 끼어든다(3번 `5 / 5`).
* ★ 문서 — *"Due to the GIL, `asyncio.to_thread()` can typically only be used to make IO-bound functions non-blocking."* 순수 파이썬 계산을 스레드로 옮기면 무엇이 겹치고 무엇이 안 겹치나는 [53번](../53-gil-and-choosing-concurrency/2-summary.md)이 **겹침 로그**로 잰다.

### 10. 3.11 — `TaskGroup`·`timeout`·`cancelling()` 이 생겼고 `asyncio.TimeoutError` 가 별칭이 됐고 `wait()` 가 코루틴을 거절한다 · 격자는 3.11 과 **한 글자도 같았다**

```text
===== python3.11 - <e52_grid_py311.py =====
structure;scenario;A;B;C;what the awaiting code saw;its cancelling();A steps at that moment
gather;one raises;finished;raised;finished;ValueError('b');0;3
gather(return_exceptions=True);one raises;finished;raised;finished;result ['A', 'ValueError', 'C'];0;4
TaskGroup;one raises;cancelled;raised;cancelled;ExceptionGroup[ValueError('b')];1;2
gather;one child cancelled;finished;cancelled;finished;CancelledError('');0;3
gather(return_exceptions=True);one child cancelled;finished;cancelled;finished;result ['A', 'CancelledError', 'C'];0;4
TaskGroup;one child cancelled;finished;cancelled;finished;block exited normally;0;4
gather;outer cancelled;cancelled;cancelled;cancelled;CancelledError('');1;0
gather(return_exceptions=True);outer cancelled;cancelled;cancelled;cancelled;CancelledError('');1;0
TaskGroup;outer cancelled;cancelled;cancelled;cancelled;CancelledError('');1;1
gather vs TaskGroup, cells that differ (A, C, seen x 3 scenarios): 4 / 9
(exit 0)
```

```python
# e52_wait.py
import asyncio


async def job(name, delay):
    await asyncio.sleep(delay)
    return name


async def main():
    fast = asyncio.create_task(job("fast", 0.01), name="fast")
    slow = asyncio.create_task(job("slow", 0.5), name="slow")
    done, pending = await asyncio.wait({fast, slow}, return_when=asyncio.FIRST_COMPLETED)
    print("done   :", sorted(t.get_name() for t in done))
    print("pending:", sorted(t.get_name() for t in pending))
    print("slow.done() / slow.cancelled() right after wait:", slow.done(), slow.cancelled())
    for t in pending:
        t.cancel()
    await asyncio.gather(*pending, return_exceptions=True)
    print("after cancelling pending ourselves -> slow.cancelled():", slow.cancelled())

    # a timeout on wait() itself
    other = asyncio.create_task(job("other", 0.5), name="other")
    done, pending = await asyncio.wait({other}, timeout=0.01)
    print("wait(timeout=...) raised nothing; done=%d pending=%d ; other.cancelled(): %s"
          % (len(done), len(pending), other.cancelled()))
    other.cancel()
    coro = job("x", 0)
    try:
        await asyncio.wait([coro])
    except TypeError as e:
        print("coroutine passed to wait():", type(e).__name__, e)
    coro.close()   # it never ran; close it so no warning is left behind


asyncio.run(main())
```

```text
===== python3 - <e52_wait.py =====
done   : ['fast']
pending: ['slow']
slow.done() / slow.cancelled() right after wait: False False
after cancelling pending ourselves -> slow.cancelled(): True
wait(timeout=...) raised nothing; done=0 pending=1 ; other.cancelled(): False
coroutine passed to wait(): TypeError Passing coroutines is forbidden, use tasks explicitly.
(exit 0)
```

* ★★ **1번 격자를 3.11.15 로 던진 결과는 3.12.3 과 한 글자도 같았다** — 걸음 수 칸까지. 취소 규칙은 두 판 사이에 **안 움직였다.**
* ★ `wait()` 에 코루틴을 직접 주면 `TypeError` — `Passing coroutines is forbidden, use tasks explicitly.`(3.11 판도 같은 문구). 3.10 이하는 **이 머신에 없어** 그 판의 동작은 못 잰 것이다.
* ★ 3.12 가 더한 것 하나 — `eager_task_factory`(2번의 순서를 뒤집는다 — 2-summary 「더 들어가면」).

### 11. 보장 · CPython 구현 · 이 판의 관찰(구현의 사정) · CPython 구현

* 「`gather` 는 자식 하나의 예외에 형제를 안 취소한다」 — **라이브러리 보장**(`gather` 문서의 굵은 *won't be cancelled*).
* 「격자의 걸음 수 칸」 — **CPython 구현.** 문서는 콜백이 몇 차례에 도는지 말하지 않는다. 그래서 격자는 **운명 칸만** 셌다.
* 「`sleep` 을 기다리는 참조 없는 태스크가 안 사라진다」 — **이 판의 관찰**이고 그 까닭(타이머 핸들)은 **구현**이다. 보장은 반대쪽 — 「언제든 수거될 수 **있다**」.
* 「`Task was destroyed but it is pending!`」 — **CPython 구현**의 문구.

### 12. Go 는 자식을 끊으면 `2 / 7`(아래로만) · `TaskGroup` 은 자식의 **실패가 위로 올라가 형제 전부**를 취소한다 · `wait` 는 Go 30번의 「타임아웃이 났으니 일도 멈췄다」와 같은 함정 · `Promise.all` 은 `gather;one raises` 행

* ★★ [Go 34번](../../../go/syntax/34-context-cancellation-deadlines-and-values/2-summary.md) — root 를 끊으면 `7 / 7`, 자식 `a` 를 끊으면 `a`·`a1` 만 받아 **`2 / 7`**, 부모·형제는 `Err=<nil>`. **취소는 아래로만** 흐른다.
  `TaskGroup` 은 **취소가 아니라 실패**가 나면 그것을 **그룹(위)으로 올려 형제 전부**를 취소한다 — Go 의 `context` 나무에는 그 방향이 없다(그 일은 부모의 `cancel` 을 **직접** 불러야 한다). 반면 **자식이 취소되기만** 하면 `TaskGroup` 도 형제를 안 건드린다(1번 `one child cancelled` 행) — 이 칸은 Go 의 `2 / 7` 과 같은 모양이다.
* ★ `wait(FIRST_COMPLETED)` 뒤에도 느린 쪽은 **돈다**(`slow.cancelled()` `False`) — [Go 30번](../../../go/syntax/30-select-default-and-timeouts/2-summary.md) 의 「`select` 에서 타임아웃 가지가 뽑혀도 고루틴은 남는다」와 같다.
  [JS 38번](../../../js/syntax/38-promise-combinators/2-summary.md) 의 `Promise.all` 은 거부된 뒤에도 나머지가 끝까지 돌았다(`… after the combinator settled: 8`) — **`gather;one raises` 행**과 같은 모양이고, JS 에는 `TaskGroup` 칸에 해당하는 자동 취소가 없다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 취소 전파 격자 | `python3 - <e52_grid.py` · `python3.11 - <e52_grid_py311.py` | 3씩(캡처 + 재대조 + `PYTHONHASHSEED` 바꾼 재캡처) | **4 / 9** · 두 판 한 글자도 같다 |
| 태스크 예약 | `python3 - <e52_task.py` | 3 | `main: both tasks created` 가 먼저 · 결과는 인자 순서 |
| 블로킹 | `python3 - <e52_block.py` | 3(판마다 5회) | `0 / 5` · `5 / 5` · `5 / 5` |
| 타임아웃 | `python3 - <e52_timeout.py` | 3 | 안 `CancelledError` · 밖 `TimeoutError` |
| 삼키기 | `python3 - <e52_swallow.py` | 3 | `after the block, no exception` |
| 봉투 | `python3 - <e52_eg.py` | 3 | `except*` 둘 다 · 맨 `except` 못 잡음 |
| 참조 없는 태스크 | `python3 - <e52_gc.py` | 3(판마다 20회) | 퓨처 `20 / 20` · `sleep` `0 / 20` |
| `wait` | `python3 - <e52_wait.py` | 3 | `pending` 이 돈다 · `TypeError` |
| 잊은 태스크의 예외 · eager | `python3 - <e52_leftover.py` · `python3.11 - <e52_leftover_py311.py` | 3씩 | `Task exception was never retrieved` · 3.11 은 eager 없음 |

**구현 의존 항목** — 판이 오르면 다시 돌려야 하는 것.

| 항목 | 왜 |
|---|---|
| ★★ 격자의 **걸음 수** 칸 | 콜백을 몇 차례에 나눠 돌리나는 구현이다 — 운명 칸(`4 / 9`)은 문서가 정한다 |
| ★ 참조 없는 태스크의 수거 | 무엇이 태스크를 쥐나는 구현이다 |
| 예외 **문구** · 루프 예외 처리기의 메시지 | 구현이다 |
| ★ 타이머를 쓴 세 탐침 | 머신이 아주 바쁘면 「끼어들었나」 칸이 움직일 수 있다(세 번 다 안 움직였다) |

★ **안 흔들리는 칸** — 격자의 **「4 / 9」** · `finished`/`cancelled`/`raised` · 예외 타입 · `cancelling()` 값 · 「N / M 판」 · `(exit N)`.
★★ **이 주제가 한 번도 안 찍은 것** — **경과 시간**(질문 밖 — 부적용) · **3.10 이하**(판 없음 — 못 잰 것).
