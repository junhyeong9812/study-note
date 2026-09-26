# python/syntax/52-asyncio-concurrency-structure — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> ★★★ 1번은 **아홉 행을 전부** 적고, 마지막 줄의 수까지 세어야 맞은 것이다.
> ★★ 이 주제는 **시간을 묻지 않는다** — 출력은 전부 순서 · 참/거짓 · 「N / M 판」이다.
>
> 실행 환경: `python3` **3.12.3** · Linux(1번은 `python3.11` 3.11.15 로도 던졌다). 던지는 형태는 `python3 - <파일` 이다.
> ★ 선행 — [51](../51-asyncio-coroutine-basics/1-question.md)(코루틴 · `asyncio.run` · `await`) · [27](../27-exception-groups-and-except-star/1-question.md)(`ExceptionGroup`·`except*`).

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 세 구조 × 세 사건 — 형제 태스크의 운명 (예측)

`A`·`B`·`C` 열의 마지막 상태, 기다리던 코드가 본 것, 그 순간의 `cancelling()` 을 행마다 적고 **마지막 줄의 수**를 센다(걸음 수 열은 틀려도 된다).

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

### 2. ★★ `await` 두 줄 · 태스크 둘 · 기다리지 않은 태스크 · `gather` 의 결과 (예측)

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

### 3. ★★★ 느린 일 하나와 짧은 줄 셋 — 세 가지 기다리는 법 (예측)

세 경우마다 `first run:` 줄과 마지막 줄의 수를 적는다.

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

### 4. ★★ 마감이 온 뒤 — 안쪽 · 블록 안 · 블록 밖에서 보이는 것 (예측)

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

### 5. ★★★ 취소를 삼키는 코드 셋 (예측)

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

### 6. ★★ 태스크 그룹에서 둘이 실패하고, 몸통이 던지면 (예측)

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

### 7. ★★ 참조를 안 쥔 태스크 (왜)

* 문서는 「루프는 태스크를 약한 참조로만 쥔다 — 참조가 없으면 언제든 수거될 수 있다」고 적는다. 그런데 `asyncio.create_task(asyncio.sleep(10))` 의 반환값을 버리고 `gc.collect()` 를 불러도 **태스크가 살아 있는** 까닭은 무엇인가?
* 반대로 **사라지는** 태스크는 무엇을 기다리고 있어야 하나 — 그리고 「내가 해 봤는데 안 사라지더라」가 규칙의 근거가 못 되는 이유는?

### 8. ★★ `CancelledError` 를 받았는데 취소된 것은 내가 아니다 (경계)

* `gather` 로 기다리던 코드가 `CancelledError` 를 받았다. **그 태스크 자신이 취소 요청을 받은 것인지** 어떻게 가르나 — 1번 격자의 어느 열이 그 답인가?
* 가르지 않고 `except CancelledError:` 에서 정리하고 빠져나가면 무엇이 잘못되나?

### 9. ★★ 블로킹 호출을 다른 스레드로 옮기면 (왜)

* 3번에서 `to_thread` 가 줄을 끼어들게 한 까닭은 무엇인가 — 조는 것은 **누구**인가?
* 같은 처방이 **순수 파이썬 계산**에도 듣는가 — 문서는 무엇이라 적고, 그것을 재는 것은 어느 편인가?

### 10. ★ 3.11 이 들여온 것 (경계)

* `TaskGroup` · `asyncio.timeout` · `cancelling()` · `asyncio.TimeoutError` 의 별칭 · `wait()` 에 코루틴을 직접 주기 — 각각 3.11 에서 **무엇이 생겼거나 바뀌었나?**
* 1번 격자를 3.11 로 던지면 3.12 와 무엇이 달라질 것이라 보나 — 실제로는?

### 11. 층 가르기 (경계)

* 「`gather` 는 자식 하나의 예외에 형제를 안 취소한다」·「격자의 걸음 수 칸」·「`asyncio.sleep` 을 기다리는 참조 없는 태스크는 `gc.collect()` 에 안 사라진다」·「`Task was destroyed but it is pending!` 문구」 —
  각각 **라이브러리 보장 · CPython 구현 · 이 판의 관찰** 중 어디인가?

### 12. 다른 갈래의 취소 (연결)

* ★★ [Go 34번](../../../go/syntax/34-context-cancellation-deadlines-and-values/2-summary.md)의 취소 나무에서 **자식 하나를 끊으면 몇 노드가 받나** — `TaskGroup` 에서 자식 하나가 **실패**하면 취소는 어느 방향으로 번지나? 두 방향이 왜 다른가?
* ★ `asyncio.wait(FIRST_COMPLETED)` 뒤의 느린 태스크는 [Go 30번](../../../go/syntax/30-select-default-and-timeouts/2-summary.md)의 어느 함정과 같은 모양인가 · [JS 38번](../../../js/syntax/38-promise-combinators/2-summary.md)의 `Promise.all` 은 1번 격자의 어느 행과 같은가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|---|---|---|---|
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |
