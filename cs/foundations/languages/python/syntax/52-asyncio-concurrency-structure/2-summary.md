# python/syntax/52-asyncio-concurrency-structure — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만(문서 원본 `.rst` 를 받아 문장을 찾았다).
> - [`asyncio.gather`(3.12)](https://docs.python.org/3.12/library/asyncio-task.html#asyncio.gather) — *"If return_exceptions is `False` (default), the first raised exception is immediately propagated to the task that awaits on `gather()`. Other awaitables in the aws sequence **won't be cancelled** and will continue to run."* ·
>   *"If `gather()` is cancelled, all submitted awaitables (that have not completed yet) are also cancelled."* ·
>   *"If any Task or Future from the aws sequence is cancelled, it is treated as if it raised `CancelledError` -- the `gather()` call is **not** cancelled in this case."*
> - [Task Groups](https://docs.python.org/3.12/library/asyncio-task.html#task-groups)(3.11) — *"The first time any of the tasks belonging to the group fails with an exception other than `asyncio.CancelledError`, the remaining tasks in the group are cancelled."* ·
>   *"those exceptions are combined in an `ExceptionGroup` or `BaseExceptionGroup` (as appropriate; see their documentation) which is then raised."*
> - [Task Cancellation](https://docs.python.org/3.12/library/asyncio-task.html#task-cancellation) — *"The asyncio components that enable structured concurrency, like `asyncio.TaskGroup` and `asyncio.timeout`, are implemented using cancellation internally and might misbehave if a coroutine swallows `asyncio.CancelledError`."*
> - [`asyncio.timeout`](https://docs.python.org/3.12/library/asyncio-task.html#asyncio.timeout)(3.11) — *"the context manager will cancel the current task and handle the resulting `asyncio.CancelledError` internally, transforming it into a `TimeoutError` which can be caught and handled."* · *"the `TimeoutError` can only be caught *outside* of the context manager."*
> - [`asyncio.wait_for`](https://docs.python.org/3.12/library/asyncio-task.html#asyncio.wait_for) — *"If a timeout occurs, it cancels the task and raises `TimeoutError`."* · 3.11 판 변경 *"Raises `TimeoutError` instead of `asyncio.TimeoutError`."*
> - [`asyncio.TimeoutError`](https://docs.python.org/3.12/library/asyncio-exceptions.html#asyncio.TimeoutError) — *"A deprecated alias of `TimeoutError`"* · *"This class was made an alias of `TimeoutError`."*(3.11) · `CancelledError` — *"`CancelledError` is now a subclass of `BaseException` rather than `Exception`."*(3.8)
> - [`asyncio.wait`](https://docs.python.org/3.12/library/asyncio-task.html#asyncio.wait) — *"Note that this function does not raise `TimeoutError`."* · *"Unlike `wait_for()`, `wait()` does not cancel the futures when a timeout occurs."* · 3.11 *"Passing coroutine objects to `wait()` directly is forbidden."*
> - [`asyncio.create_task`](https://docs.python.org/3.12/library/asyncio-task.html#asyncio.create_task) 의 **Important** — *"Save a reference to the result of this function, to avoid a task disappearing mid-execution. The event loop only keeps weak references to tasks. A task that isn't referenced elsewhere may get garbage collected at any time, even before it's done."*
> - [`asyncio.to_thread`](https://docs.python.org/3.12/library/asyncio-task.html#asyncio.to_thread)(3.9) · [Developing with asyncio — Running Blocking Code](https://docs.python.org/3.12/library/asyncio-dev.html#running-blocking-code) — *"Blocking (CPU-bound) code should not be called directly."* ·
>   *"While a Task is running in the event loop, no other Tasks can run in the same thread."*
> - [What's New 3.11 — asyncio](https://docs.python.org/3.12/whatsnew/3.11.html#asyncio) — `TaskGroup` *"For new code this is recommended over using `create_task()` and `gather()` directly."* · `timeout` *"recommended over using `wait_for()` directly."*
>
> **실행 검증** — 이 문서에 실린 출력은 전부 이 머신(Linux)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.\
> 판은 `python3` **3.12.3** 이 본판이고, 판 경계를 위해 `python3.11` **3.11.15** 로 취소 전파 격자(동작 2 — **한 글자도 같았다**)와 「더 들어가면」의 블록 하나를 더 던졌다.\
> ★★★ **이 문서는 시간을 한 번도 출력하지 않는다.** `sleep` 의 길이는 소스에만 있고, 출력은 전부 **순서 · 참/거짓 · 「N / M 판」** 이다. 「몇 배 빠르다」는 한 줄도 없다.\
> ★★ **격자·태스크 순서 탐침은 시간을 아예 안 쓴다** — 한 걸음을 `await asyncio.sleep(0)`(루프에 한 차례 양보)로 셌다. 그래서 순서가 타이머에 안 흔들린다.\
> **버전** — `asyncio.to_thread` **3.9** · `TaskGroup`·`asyncio.timeout`·`ExceptionGroup`·`except*`·`Task.cancelling()` **3.11** · `asyncio.TimeoutError` 가 내장 `TimeoutError` 의 별칭 **3.11** · `wait()` 에 코루틴을 직접 주면 거절 **3.11** · `CancelledError` 가 `BaseException` 하위 **3.8**.\
> ★ **구현 대 언어 보장 한 줄** — `gather`·`TaskGroup`·`timeout`·`wait` 의 취소 규칙과 예외 모양은 **라이브러리 보장**이고, 한 걸음(`sleep(0)`)이 몇 번 돌았나 · `Task was destroyed but it is pending!` 문구 · 「혼자 기다리는 퓨처」 태스크가 수거되는 것은 **CPython 구현**이다.\
> ★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다 | 안 흔들린다(근거로 써도 되는 칸) |
> |---|---|
> | ★ 머신이 아주 바쁘면 **타이머를 쓰는 세 탐침**(동작 4·5·8)의 「끼어들었나」 칸이 움직일 수 있다 — 틈을 크게 벌려 두었고(소스의 `sleep` 길이) **세 번 캡처에서 한 번도 안 움직였다** | ★★★ 격자 마지막 줄 **「… 4 / 9」** · 칸마다 `finished`/`cancelled`/`raised` · 예외 **타입** |
> | 판이 오르면 예외 **문구**(`Passing coroutines is forbidden, use tasks explicitly.`) | `sleep(0)` 걸음으로 센 순서(동작 1·2·3) — 타이머가 없다 |
> | 걸음 수 칸(`A steps at that moment`)은 **구현이 콜백을 몇 차례에 나눠 돌리나**에 달렸다 — 3.11·3.12 는 같았다 | 「N / M 판」의 **N 과 M** · `(exit N)` |
> | — (주소·시간·`set` 순서를 한 곳도 안 찍었다 — `done`/`pending` 은 `sorted` 로 찍었다) | `is`·`issubclass` 의 참/거짓 |
>
> **선행** — [51-asyncio-coroutine-basics](../51-asyncio-coroutine-basics/2-summary.md)(★★★ **51 이 보인 것** — 코루틴 함수를 **부르기만 하면 한 줄도 안 돈다**(`coroutine … was never awaited`) · `asyncio.run` 이 루프를 **만들고 닫는다** · `await` 는 그 자리에서 **한 코루틴을 끝까지 기다린다**. 이 문서는 그 위에서 **「여럿을 동시에 걸어 두면 누가 누구를 취소하나」** 부터 시작한다) ·
> [17-generators-yield](../17-generators-yield/2-summary.md)(코루틴이 멈췄다 이어지는 자리 — `yield` 의 후손).

## 한눈에 — 쉽게 말하면

**이벤트 루프는 「요리사가 한 명뿐인 주방」이다.** 요리사는 한 번에 **한 냄비만** 젓는다.

* **태스크(Task)** — 주방 벽에 **걸어 둔 주문표**. 걸어 두기만 하면 요리사가 손이 빌 때 **알아서** 집어 든다(`await` 안 해도 돈다).
* **`await asyncio.sleep`** — 「타이머 맞춰 놓고 **다른 냄비로** 간다」. 이것이 **양보**다.
* **`time.sleep`** — 요리사가 **냄비 앞에 서서 존다.** 다른 주문표는 아무도 안 본다.
* **`asyncio.to_thread`** — **알바를 불러** 냄비 앞에 세워 두고 요리사는 다른 일을 한다.
* **`gather`** — 「이 주문표들 **다 되면** 알려 줘」. 하나가 망하면 **바로 알려 주지만 나머지 요리는 계속한다.**
* **`TaskGroup`** — **한 테이블의 코스 요리.** 한 접시가 망하면 **그 테이블 요리를 전부 멈추고** 망한 사연을 **한 봉투(`ExceptionGroup`)** 에 담아 올린다.
* **취소(cancel)** — 요리사에게 「그 주문 접어」 하고 **쪽지를 꽂는 것.** 쪽지는 요리사가 **다음에 손을 멈추는 자리(`await`)** 에서 읽힌다.

```text
   한 주방, 주문표 세 장(A · B · C) — B 가 망했을 때

   gather          A ───────────── finished     ← 계속 만든다
                   B ──✗ ValueError  ──────────► 기다리던 사람에게 즉시 ValueError
                   C ───────────── finished     ← 계속 만든다

   TaskGroup       A ───✂ cancelled
                   B ──✗ ValueError
                   C ───✂ cancelled
                   └─ 모두 멈춘 뒤에야 ──────────► ExceptionGroup[ValueError]
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 요리사 한 명 | 이벤트 루프(한 스레드) | 블로킹 탐침(동작 4) |
| 벽에 건 주문표 | `asyncio.create_task` 의 `Task` | `await` 없이도 돈다(동작 1) |
| 다른 냄비로 간다 | `await` — 루프에 양보 | 로그가 끼어든다(동작 4) |
| 냄비 앞에서 존다 | 블로킹 호출(`time.sleep`) | 끼어든 줄 `0 / 5` 판(동작 4) |
| 「다 되면 알려 줘」 | `gather` | 취소 전파 격자(동작 2) |
| 한 테이블의 코스 | `TaskGroup` | 취소 전파 격자(동작 2) · 봉투(동작 3) |
| 「그 주문 접어」 쪽지 | `Task.cancel()` → 다음 `await` 에서 `CancelledError` | 삼키면(동작 6) |
| 주문표를 아무도 안 들고 있다 | 태스크 참조를 안 쥔 `create_task` | GC 탐침(동작 7) |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.\
「**`gather` 로 요청 셋을 보냈는데 하나가 실패했다 — 에러는 받았는데 나머지 둘이 계속 돌아 DB 에 썼다**」·
「**비동기 서버에서 한 요청이 `requests.get` 을 부르자 다른 요청이 전부 멈췄다**」·
「**`timeout` 을 걸었는데 시간이 지나도 예외가 안 났다**」가 그것이다.\
첫째는 **`gather` 는 형제를 안 취소한다**는 것이고, 둘째는 **블로킹 호출이 요리사를 재운** 것이고, 셋째는 **어딘가에서 `CancelledError` 를 삼킨** 것이다(동작 6).

> **태스크(Task)** — 코루틴을 이벤트 루프에 **걸어 두어** 루프가 알아서 돌리게 만든 객체. `asyncio.create_task(coro)` 로 만든다.\
> 예: `t = asyncio.create_task(job())` 한 줄이면 `await t` 를 안 해도 `job` 은 돈다(동작 1).

> **구조적 동시성(structured concurrency)** — 동시에 도는 작업들을 **한 블록에 묶어**, 그 블록을 나갈 때 **전부 끝났거나 전부 취소됐음**을 보장하는 방식. `TaskGroup` 이 그것이다.\
> 예: `async with asyncio.TaskGroup() as tg:` 를 나오면 그 안에서 만든 태스크는 하나도 안 남는다.

### ★★ 이 주제가 쓰는 창 / 부적용인 창

**본체는 ① 취소 전파 격자다.** 세 구조(`gather` · `gather(return_exceptions=True)` · `TaskGroup`) × 세 사건(자식 하나가 예외 · 자식 하나가 취소됨 · 기다리는 쪽이 취소됨) 에서
**형제 A·C 의 운명**과 **기다리던 코드가 본 것**을 한 표로 찍고, **`gather` 와 `TaskGroup` 이 갈린 칸을 스크립트가 센다.**
그리고 ② **로그 끼어들기 창**이 블로킹을 **시간 없이** 보인다.

| 창 | 무엇을 말해 주나 | 못 보는 것 |
|---|---|---|
| ① ★★★ **취소 전파 격자**(`sleep(0)` 걸음) | 형제가 **취소됐나 · 끝까지 돌았나** · 기다리던 코드가 **무엇을 받았나** | 실제 I/O 가 도중에 끊기는 모양 |
| ② ★★★ **로그 끼어들기 창**(「A 시작과 A 끝 사이에 B 의 줄이 있나」 참/거짓 · 5판) | 루프가 **멈췄나** | 얼마나 멈췄나(★ 부적용 — 시간을 안 찍는다) |
| ③ ★★ **예외 모양 창**(타입 · `.exceptions` · `cancelling()`) | `ExceptionGroup` 인가 · **취소 요청을 받은 것인가, 결과로 `CancelledError` 를 받은 것인가** | — |
| ④ ★★ **약한 참조 창**(`weakref.ref(task)` + `gc.collect()` · 20판) | 참조 없는 태스크가 **정말 사라지나** | 「언제든」의 **자연 발생 시점**(강제로 `gc.collect()` 를 불렀다) |
| ⑤ ★ **판 격자**(3.11 대 3.12) | 취소 규칙이 판 사이에 **움직였나** | 3.10 이하(`TaskGroup` 자체가 없다) · 3.13 이후 |
| ⑥ ★ **교차 갈래 창**(인용만) | Go `context` 나무 · Go `select` · JS `Promise.all` 과 **같은 자리** | — |
| ★ **부적용인 창** — 경과 시간 | — | ★★★ 이 주제의 질문은 「**멈췄나 · 끼어들었나**」이지 「**얼마나**」가 아니다 — **잴 것이 없다**(재지 않은 것이 아니라 질문 밖이다) |
| ★ **제5의 상태** — 「태스크가 GC 될 수 있다」 | 문서가 「**언제든**」이라 한 것을 **「참조를 끊고 `gc.collect()` 를 부르면 사라지나」** 로 바꿔 물었다 | ★ 바꾼 창은 **「어떤 코드에서 저절로 일어나나」는 못 본다** — `asyncio.sleep` 을 기다리는 태스크는 **20판 모두 안 사라졌다**(동작 7) |
| ★ **못 잰 것** — 3.10 이하의 `gather` 대 `TaskGroup` | — | 이 머신에 3.10 이 없고, `TaskGroup` 은 3.11 부터다 |

★★ **②가 이 주제의 네 번째 창이다.** 블로킹을 **시간**으로 재면 「느렸다」까지만 말하고, 머신이 바쁘면 숫자가 흔들린다.
**「`slow start` 와 `slow end` 사이에 `tick` 줄이 하나라도 있나」** 로 물으면 답이 `0 / 5` 대 `5 / 5` 로 갈리고 **숫자가 안 흔들린다**(동작 4).

## 이 주제가 답하려는 질문

1. ★★★ **동시에 걸어 둔 태스크 중 하나가 실패하거나 취소되면 나머지는 어떻게 되나** — `gather` 와 `TaskGroup` 은 **어디서 갈리나**, 그리고 **기다리던 코드는 무엇을 받나**(`ValueError` 인가 `ExceptionGroup` 인가 `CancelledError` 인가).
2. ★★★ **왜 블로킹 호출 하나가 루프 전체를 멈추나** — `await` 없는 `time.sleep` · `await asyncio.sleep` · `await asyncio.to_thread` 에서 **다른 태스크가 끼어드나.**
3. ★★ **타임아웃과 취소는 어떻게 한 몸인가** — `asyncio.timeout` 과 `wait_for` 가 안쪽에 무엇을 던지고 바깥에 무엇을 내놓나, 그리고 **`CancelledError` 를 삼키면 무엇이 조용히 깨지나.**

★ 첫째가 이 주제의 인출 목표다.
**「`gather` 는 형제를 안 취소하고 첫 예외를 곧바로 넘긴다 · `TaskGroup` 은 형제를 취소하고 다 멈춘 뒤 봉투에 담아 올린다 · 기다리는 쪽이 취소되면 둘 다 형제를 취소한다」 세 문장으로 격자의 `4 / 9` 를 설명할 수 있는 것**이 아는 것과 들은 것의 경계다.

## 동작 방식

> 이 절이 본문이다. 그림이 먼저 오고 문장이 그 그림을 읽어 준다.

### 1. ★★ 태스크는 걸어 두는 순간 예약된다 — `await` 는 「결과를 받는 자리」다

**언제 쓰나** — 「두 일을 동시에 돌린다」를 쓸 때마다. `await` 를 두 번 쓰는 것과 태스크 둘을 거는 것이 **무엇이 다른가.**

```text
   한 걸음 = await asyncio.sleep(0)  (루프에 한 차례 양보 — 타이머 없음)

   sequential       await a  ──  a start · a end
                    await b  ──                    b start · b end        ← 하나 끝나고 하나

   two_tasks        create_task(a) · create_task(b)    ← 이 줄에서 이미 예약
                    main: both tasks created
                    await ta ──  a start · b start · a end · b end        ← 번갈아 걷는다

   task_never_awaited  create_task(a) 만 하고 await 는 한 번도 안 한다
                    ──  a start · a end  (main 이 양보하는 동안 저절로 끝까지)
```

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

그림 해설.

* ★★ **`sequential` — `await` 두 줄은 동시가 아니다.** `a end` 가 나온 뒤에야 `b start`. `await` 는 **그 자리에서 한 코루틴을 끝까지 기다린다**([51번](../51-asyncio-coroutine-basics/2-summary.md)이 정본).
* ★★★ **`two_tasks` — `main: both tasks created` 가 `a start` 보다 먼저다.** `create_task` 는 **돌리지 않고 예약만** 한다. `main` 이 `await ta` 로 양보하는 순간 **a 와 b 가 번갈아** 걷는다.
* ★★★ **`task_never_awaited` — `await` 를 한 번도 안 한 태스크도 끝까지 돌았다**(`a start | a end`).
  51번의 「부르기만 하면 한 줄도 안 돈다」는 **코루틴 객체**의 말이고, **태스크는 걸어 두기만 하면 돈다.** 이 차이가 동작 7 의 GC 경고로 이어진다 — 아무도 안 쥐고 있어도 도는 물건이라서.
* ★ **`gather_order` — 결과 리스트는 인자 순서**(`['slow', 'fast']`)이고, **끝난 순서**(`fast end | slow end`)가 아니다. 문서 — *"The order of result values corresponds to the order of awaitables in aws."*

**비용** — 태스크는 **예외도 혼자 들고 있다.** 아무도 `await` 하지 않은 태스크가 실패하면 그 예외는 **기다리는 사람 없이** 태스크 안에 남는다. 그래서 「걸어 두고 잊기」는 동작 7 의 참조 문제와 함께 **예외를 잃는** 자리이기도 하다 — 그 예외가 루프의 예외 처리기로만 가는 것은 「더 들어가면」의 블록이 보인다.

### 2. ★★★ 취소 전파 격자 — `gather` 대 `TaskGroup` × 세 사건

**언제 쓰나** — 여러 요청을 한꺼번에 보내고 기다릴 때마다. 특히 「**하나가 실패하면 나머지를 멈춰야 하나**」.

```text
   한 칸을 채우는 법 — 칸마다 새 태스크 A · B · C 를 만든다(칸끼리 안 샌다)

   A, C : 네 걸음 걷고 끝나는 일꾼 (한 걸음 = sleep(0))
   B    : 사건마다 다르다
          one raises           첫 걸음에서 ValueError('b')
          one child cancelled  B 에게 b.cancel()  (기다리는 쪽은 안 건드린다)
          outer cancelled      B 도 일꾼 · 두 걸음 뒤 「기다리는 쪽」 태스크에 .cancel()

   칸 : A · B · C 가 마지막에 어떻게 됐나 (finished · cancelled · raised)
        · 기다리던 코드가 본 것 · 그 순간 기다리던 태스크의 cancelling() · 그 순간 A 가 몇 걸음 걸었나
   ★ 구조가 끝난 뒤에도 열두 걸음을 더 기다린다 — 남은 태스크가 「끝까지 가나」를 보려고
```

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

그림 해설 — 격자를 사건별로 다시 그리면 이렇다.

```text
   사건            gather(기본)                    TaskGroup
   ─────────────  ──────────────────────────────  ──────────────────────────────
   one raises      A finished · C finished         A cancelled · C cancelled
                   ValueError 를 곧바로 (A 3걸음)    ExceptionGroup[ValueError] (A 2걸음에서 멈춤)
                                        ★ 갈림 3칸
   one child       A finished · C finished         A finished · C finished
   cancelled       CancelledError 를 받는다          블록이 정상으로 끝난다
                   (그런데 cancelling() 은 0)
                                        ★ 갈림 1칸
   outer           A · B · C 전부 cancelled         A · B · C 전부 cancelled
   cancelled       CancelledError                   CancelledError
                                        갈림 0칸
                                                       → 4 / 9
```

* ★★★ **마지막 줄 — `gather` 와 `TaskGroup` 이 갈린 칸 `4 / 9`.** 셋이 `one raises` 에 몰려 있고, 하나가 `one child cancelled` 에 있다. **`outer cancelled` 는 한 칸도 안 갈렸다.**
* ★★★ **`one raises` — `gather` 는 형제를 안 취소한다.** 기다리던 코드는 `ValueError('b')` 를 **A 가 3걸음일 때** 받았고(A 는 아직 안 끝났다), A·C 는 그 뒤에 **혼자 끝까지 갔다**(`finished`).
  문서 그대로다 — *"Other awaitables in the aws sequence **won't be cancelled** and will continue to run."*
  **`TaskGroup` 은 A·C 를 2걸음에서 멈추고**, 다 멈춘 **뒤에야** `ExceptionGroup[ValueError('b')]` 를 올렸다. 예외 **하나**여도 봉투에 담긴다.
* ★★★ **`outer cancelled` — 여기서는 `gather` 도 자식을 취소한다.** 「`gather` 는 나머지를 안 취소한다」는 **자식 하나가 예외일 때의 말**이다.
  기다리는 쪽이 취소되면 **A·B·C 가 전부 `cancelled`** — 문서 *"If `gather()` is cancelled, all submitted awaitables (that have not completed yet) are also cancelled."*
  이 사건만 보면 두 구조는 **구별이 안 된다**(`0` 칸).
* ★★ **`one child cancelled` — `gather` 는 기다리던 코드에게 `CancelledError` 를 던지는데, 그 태스크는 취소 요청을 받은 적이 없다**(`cancelling()` 이 `0`).
  문서 — *"it is treated as if it raised `CancelledError` -- the `gather()` call is **not** cancelled in this case."* 형제 A·C 는 **끝까지** 갔다.
  `TaskGroup` 은 **`CancelledError` 를 실패로 치지 않아**(*"fails with an exception other than `asyncio.CancelledError`"*) 블록이 **정상으로** 끝났다.
  ★ **이 칸이 함정이다** — `except CancelledError:` 에서 「내가 취소됐구나」 하고 정리하면 틀린다. 취소된 것은 **자식**이다. 가르는 법은 `asyncio.current_task().cancelling()` 이다(3.11).
* ★ **`return_exceptions=True` 는 형제 운명을 안 바꾼다** — A·C 는 `gather` 기본과 같이 `finished` 이고, 예외가 **결과 리스트의 한 칸**(`['A', 'ValueError', 'C']`)이 될 뿐이다. 기다리는 쪽이 취소되면 **여전히 `CancelledError`** 다.
* ★ **`TaskGroup` 의 `one raises` 칸에서 기다리던 태스크의 `cancelling()` 이 `1`** 이다 — 문서가 말한 *"the task directly containing the `async with` statement is also cancelled"* 의 흔적이다. 그 `CancelledError` 는 **블록 밖으로 안 나오고** `ExceptionGroup` 으로 바뀌어 나왔다.

★★ **3.11 판도 한 글자도 같았다** — 같은 소스를 `python3.11` 로 던졌다.

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

**비용** — `TaskGroup` 의 「다 멈춘 뒤에야 올린다」는 **첫 실패를 늦게 안다**는 뜻이기도 하다. A·C 가 `CancelledError` 를 받고 **정리(`finally`)에 오래 걸리면** 그만큼 기다린다. 그리고 예외가 **늘 봉투**라 `except ValueError:` 로는 못 잡는다(동작 3).

> **`ExceptionGroup`** — 여러 예외를 **한 예외로 묶어** 올리는 내장 예외(3.11+). `.exceptions` 에 안에 든 예외들이 있다.\
> 예: `TaskGroup` 안에서 둘이 실패하면 `ExceptionGroup(… [ValueError, KeyError])`.

> **`cancelling()`** — 그 태스크가 **취소 요청을 몇 번 받았나**를 세는 메서드(3.11+). 받은 `CancelledError` 가 **나에 대한 취소인가**를 가르는 데 쓴다.\
> 예: `gather` 의 자식이 취소돼 기다리던 쪽이 `CancelledError` 를 받았을 때 `0`.

### 3. ★★ `TaskGroup` 의 봉투 — `except*` 로 뜯는다

**언제 쓰나** — `TaskGroup` 을 쓰는 순간 예외 처리가 이 꼴이 된다.

```text
   async with TaskGroup():          나오는 것
     ├─ ValueError('v')    ─┐
     └─ KeyError('k')      ─┴──►  ExceptionGroup[ValueError, KeyError]
                                   except* ValueError  → 봉투에서 ValueError 만
                                   except* KeyError    → 봉투에서 KeyError 만   (둘 다 돈다)
                                   except ValueError   → ✗ 안 걸린다(봉투는 ValueError 가 아니다)
   몸통이 RuntimeError 를 던지면     → 자식은 cancelled · ExceptionGroup[RuntimeError]
```

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

* ★★ **`except*` 두 가지가 둘 다 돌았다** — 봉투를 **종류별로 쪼개** 각 가지에 준다. `except` 와 달리 **하나만 도는 것이 아니다.**
* ★★ **`except ValueError:` 는 못 잡았다** — `plain except ValueError caught it` 줄이 **없고**, 다음 가지 `except Exception` 이 `ExceptionGroup` 을 잡았다.
* ★ **몸통(`async with` 안쪽)이 던져도 자식이 취소되고 봉투에 담긴다** — `walker cancelled` · `ExceptionGroup ["RuntimeError('body')"]`. 문서 — *"this is treated the same as if one of the tasks failed"*.

### 4. ★★★ 블로킹 호출은 루프를 멈춘다 — 로그가 끼어들었나

**언제 쓰나** — `async def` 안에서 **`await` 가 안 붙는 느린 호출**(동기 HTTP 클라이언트 · `time.sleep` · 무거운 계산)을 부를 때마다.

```text
   slow 태스크와 tick 태스크(짧게 쉬며 한 줄씩 · 세 번)를 같이 건다 — 「slow start 와 slow end 사이에 tick 이 있나」

   time.sleep                  요리사 ███████████████ 존다 ███████████████│ tick tick tick
                               slow start ─────────────────────── slow end │
                               ★ 사이에 tick 0 줄                          ▲ 깨어난 뒤에야

   await asyncio.sleep         slow start ─ tick ─ tick ─ tick ────── slow end
                               ★ 사이에 tick 3 줄 — 양보했으니까

   await asyncio.to_thread     slow start ─ tick ─ tick ─ tick ────── slow end
      (time.sleep)             ★ 조는 것은 알바(다른 스레드) — 요리사는 계속 젓는다
```

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

* ★★★ **`time.sleep` — 끼어든 판 `0 / 5`.** 로그가 `slow start | slow end | tick 0 | …` — `tick 0` 조차 **slow 가 끝난 뒤**에 나왔다. `ticker` 는 이미 **걸어 둔 태스크**인데도 한 번도 못 돌았다.
  문서 — *"While a Task is running in the event loop, no other Tasks can run in the same thread. When a Task executes an `await` expression, the running Task gets suspended, and the event loop executes the next Task."* `time.sleep` 에는 **`await` 가 없다.**
* ★★★ **`await asyncio.sleep` · `await asyncio.to_thread(time.sleep)` — 끼어든 판 `5 / 5`.** 세 `tick` 이 전부 `slow start` 와 `slow end` **사이**에 있다.
  **`to_thread` 는 블로킹 호출을 그대로 두고 자리를 옮긴 것**이다 — 조는 것은 다른 스레드이고, 루프의 스레드는 `await` 에서 양보한다.
* ★★ **`distinct log orders over 5 runs: 1`** — 세 경우 모두 다섯 판이 **한 가지 순서**였다. 「끼어드나」는 판마다 흔들리는 성질이 아니었다.
* ★ **이 탐침은 「얼마나 늦었나」를 안 잰다** — 시간을 찍지 않았다. 말할 수 있는 것은 **「그동안 아무도 못 돌았다」** 뿐이고, 그것이 곧 서버에서 **다른 요청이 전부 멈춘** 모양이다.
* ★ **`to_thread` 가 CPU 계산에도 듣나**는 이 문서의 몫이 아니다 — 문서는 *"Due to the GIL, `asyncio.to_thread()` can typically only be used to make IO-bound functions non-blocking."* 이라 적고, 그 GIL 이 무엇을 막는지는 [53번](../53-gil-and-choosing-concurrency/2-summary.md)이 잰다.

**비용** — `to_thread` 는 **스레드 하나를 빌린다**(기본 실행기). 블로킹 호출이 **아주 많이** 동시에 걸리면 그 풀의 크기가 새 한계가 된다 — 그 한계는 이 문서의 창(끼어들었나) 밖이다. **처방의 순서는 「비동기 판 라이브러리를 쓴다 → 안 되면 `to_thread`」** 다.

> **블로킹 호출(blocking call)** — 끝날 때까지 **그 스레드를 붙잡고 안 놓는** 호출. `await` 가 없어 루프에 양보할 틈이 없다.\
> 예: `time.sleep(1)` · `requests.get(url)` · 큰 `for` 계산.

### 5. ★★ 타임아웃은 취소다 — 안에서는 `CancelledError`, 밖에서는 `TimeoutError`

**언제 쓰나** — 「이 일에 최대 N초」를 걸 때마다.

```text
   async with asyncio.timeout(마감):          await asyncio.wait_for(inner(), 마감)
       await inner()                               │
         │ 마감 → 현재 태스크에 cancel()             │ 마감 → inner 태스크에 cancel()
         ▼                                         ▼
   inner 안     : CancelledError  (finally 도 돈다)   inner 안   : CancelledError
   블록 안쪽    : CancelledError  ← 여기서는 아직 취소다
   블록 바깥    : TimeoutError    ← __aexit__ 가 바꿔 준다     wait_for 바깥 : TimeoutError
```

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

* ★★★ **안쪽 코루틴은 두 경우 모두 `CancelledError` 를 받았다** — `inner got CancelledError` · `inner finally`. 타임아웃은 **별도의 신호가 아니라 취소**다.
* ★★ **`asyncio.timeout` 블록 안쪽에서는 아직 `CancelledError`, 바깥에서야 `TimeoutError`** — 문서 *"the `TimeoutError` can only be caught *outside* of the context manager."* 블록 **안에** `except TimeoutError:` 를 두면 안 걸린다.
* ★★ **`asyncio.TimeoutError is TimeoutError` 가 `True`** — 3.11 부터 **같은 클래스**다(문서 *"A deprecated alias of `TimeoutError`"*). 옛 코드의 `except asyncio.TimeoutError:` 도 그대로 걸린다.
* ★ **`CancelledError` 는 `Exception` 의 하위가 아니다**(`False`) — 3.8 부터 `BaseException` 직속이다. 그래서 `except Exception:` 은 취소를 **안 삼킨다** — 그런데 `except BaseException:`·맨 `except:` 는 삼킨다(동작 6).
* ★ **두 방식이 이 탐침에서 낸 줄은 같다** — 차이는 **모양**이다. `timeout` 은 **여러 `await` 를 한 블록에** 묶고 마감을 `reschedule` 로 옮길 수 있고, `wait_for` 는 **awaitable 하나**를 받는다. 3.11 What's New 는 새 코드에 `timeout` 을 권한다.

### 6. ★★★ `CancelledError` 를 삼키면 — 타임아웃이 조용히 사라진다

**언제 쓰나** — `try: … except: …` · `except BaseException:` 으로 「다 잡아서 로그만 남긴다」를 쓰는 모든 자리.

```text
   task.cancel()  →  쪽지를 꽂는다  →  다음 await 에서 CancelledError
                                          │
                     ┌────────────────────┴───────────────────┐
                     다시 던진다(raise)                         삼킨다(pass)
                     await t → CancelledError                  await t → 그냥 값
                     t.cancelled() True                        t.cancelled() False
                                                                ★ cancelling() 은 1 로 남는다

   timeout 블록 안에서 삼키면 ─► 블록이 「정상 종료」 ─► TimeoutError 없음 · 마감이 지났는데 코드는 계속
   TaskGroup 의 형제가 삼키면  ─► 그 형제는 끝까지 간다   ─► 봉투는 그 뒤에야
```

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

* ★★ **삼키면 취소가 「없던 일」이 된다** — `await gave: value 'swallows returned'` · `cancelled(): False`. 그런데 **`cancelling()` 은 `1`** 로 남았다 — 취소 요청을 받은 기록은 지워지지 않는다.
  문서 — *"in cases when suppressing `asyncio.CancelledError` is truly desired, it is necessary to also call `uncancel()` to completely remove the cancellation state."*
* ★★★ **`timeout` 블록 안에서 삼키면 `TimeoutError` 가 안 난다** — `block body reached its end` · `after the block, no exception`. **마감이 지났는데도** 블록 뒤의 코드가 **정상 경로로** 돌았다. 에러도 경고도 없다.
  문서가 미리 적어 둔 자리다 — *"might misbehave if a coroutine swallows `asyncio.CancelledError`."* **「misbehave」의 실체가 이 침묵**이다.
* ★★ **`TaskGroup` 도 같은 집안이다** — 형제 취소를 `CancelledError` 로 하므로, 삼킨 형제는 **멈추지 않았다**(`sibling swallowed a cancel at step 1` · `sibling reached its end`). 봉투(`['ValueError']`)는 **그 형제가 제 발로 끝난 뒤에야** 올라왔다.

**비용** — 고치는 법은 한 줄이다: **`except asyncio.CancelledError:` 에서 정리하고 `raise`**, 또는 **`finally` 로 정리**. 문서 — *"It is recommended that coroutines use `try/finally` blocks to robustly perform clean-up logic."*

### 7. ★★ 참조 없는 태스크 — 문서의 경고를 약한 참조로 잰다

**언제 쓰나** — `asyncio.create_task(…)` 의 반환값을 **버리는**(「걸어 두고 잊기」) 모든 자리.

```text
   누가 태스크를 쥐고 있나

   이벤트 루프 ─ 약한 참조(all_tasks 는 WeakSet) ─ ─ ─►  Task
   await asyncio.sleep(10) ─► 루프의 타이머 핸들 ─ 강한 참조 ─►  (콜백 → Task)   ★ 살아 있다
   await 혼자만 아는 future ─► future ↔ Task 끼리만 서로 쥔다    ★ 바깥에서 닿는 길이 없다
                                                   gc.collect() ─► 사라진다
                                                   loop 예외 처리기: Task was destroyed but it is pending!
```

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

* ★★ **참조를 안 쥔 채 「혼자만 아는 퓨처」를 기다리던 태스크는 `20 / 20` 판 사라졌다** — `gc.collect()` 한 번에. 루프의 예외 처리기에 `Task was destroyed but it is pending!` 가 **20번** 왔다. 태스크는 **끝나지 못하고** 없어졌다.
  문서 — *"The event loop only keeps weak references to tasks. A task that isn't referenced elsewhere may get garbage collected at any time, even before it's done."*
* ★★ **참조를 쥐면(`held.append(task)`) `0 / 20`** — 문서의 처방(*"gather them in a collection"*)이 그대로 듣는다.
* ★★★ **그런데 `asyncio.sleep` 을 기다리는 태스크는 참조를 안 쥐어도 `0 / 20`** — 루프의 **타이머**가 그 태스크의 깨우기 콜백을 쥐고 있기 때문이다(★ 이것은 **구현의 사정**이다). 그래서 흔한 예제로는 **재현이 안 되고**, 「내 코드는 괜찮던데」가 된다.
  ★ **문서는 「언제든」이라 했다 — 이 탐침이 보인 것은 「이 두 경우에서 그랬다」 뿐이다.** 기다리는 대상이 무엇이냐에 따라 달라지므로 **규칙은 문서대로 「늘 쥔다」** 다.
* ★ 이 탐침은 **`gc.collect()` 를 손으로 불렀다** — 순환 수집기가 **저절로** 도는 시점은 재지 않았다(창 표의 제5의 상태).

### 8. ★ `asyncio.wait` — 「먼저 끝난 것」을 받고, 나머지는 네가 정한다

**언제 쓰나** — 「여럿 중 **먼저 끝난 것**만 쓰고 싶다」 · 「기다리되 **예외 없이** 마감만」.

```text
   wait({fast, slow}, FIRST_COMPLETED)          Go 의 select
   ───────────────────────────────────           ──────────────────────────────
   done={fast} · pending={slow}                  준비된 가지 하나를 고른다
   slow 는 여전히 돈다(cancelled False)             나머지 채널의 송신자는 여전히 돈다
   ★ 취소는 부르는 쪽이 직접                          ★ 멈추게 하려면 취소 신호(context)를 따로

   wait(…, timeout=…)  → 예외 없음 · 못 끝난 것은 pending 에      (wait_for 는 취소 + TimeoutError)
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

* ★★ **`FIRST_COMPLETED` 뒤에도 `slow` 는 안 끝났고 안 취소됐다**(`False False`) — 우리가 `cancel()` 한 **뒤에야** `cancelled(): True`.
* ★★ **`wait(timeout=…)` 는 아무것도 안 던지고 안 취소한다** — `done=0 pending=1 ; other.cancelled(): False`. 문서 — *"Unlike `wait_for()`, `wait()` does not cancel the futures when a timeout occurs."*
* ★ **3.11 부터 코루틴을 직접 주면 `TypeError`** — `Passing coroutines is forbidden, use tasks explicitly.` 태스크로 **감싸서** 줘야 한다.
* ★ **Go `select` 와 같은 자리** — [Go 30번](../../../go/syntax/30-select-default-and-timeouts/2-summary.md) 의 「타임아웃이 났으니 일도 멈췄다」가 틀린 이유(고루틴이 남는다)와 **같은 모양**이다. 먼저 끝난 것을 고른다고 나머지가 멈추지 않는다.

## 문법 — 형태와 규칙

```text
   t = asyncio.create_task(coro())               걸어 둔다 — 반환값을 쥔다(동작 7)
   r = await t                                   결과 · 예외 · CancelledError 를 받는다

   rs = await asyncio.gather(c1, c2, c3)         결과는 인자 순서 · 첫 예외를 곧바로 · 형제는 안 취소
   rs = await asyncio.gather(…, return_exceptions=True)   예외도 결과 칸으로

   async with asyncio.TaskGroup() as tg:         (3.11+)
       t1 = tg.create_task(c1())                 한 실패 → 나머지 취소 → ExceptionGroup
   except* ValueError as eg: …                   봉투를 종류별로

   async with asyncio.timeout(delay): …          (3.11+) 안: CancelledError · 밖: TimeoutError
   await asyncio.wait_for(aw, delay)             aw 를 취소하고 TimeoutError
   done, pending = await asyncio.wait(tasks, return_when=FIRST_COMPLETED)   아무것도 취소 안 함
   await asyncio.to_thread(blocking_fn, *args)   (3.9+) 블로킹 호출을 다른 스레드로
```

* `create_task` 는 **실행 중인 루프 안에서만** 부른다(`async def` 안).
* `gather` 는 코루틴을 **저절로 태스크로 감싼다** — `wait` 는 3.11 부터 **안 감싸고 거절한다.**
* `TaskGroup` 의 태스크는 **블록을 나갈 때 전부 끝나 있다** — 참조를 따로 안 쥐어도 블록이 쥔다.
* `CancelledError` 는 `BaseException` 직속이다 — `except Exception:` 에 안 걸린다.

## 어디서 틀리나

### (1) ★★★ 「`gather` 는 하나가 실패하면 나머지를 멈춘다」

* 격자의 `gather;one raises` 칸 — A·C 가 **`finished`**. 에러는 곧바로 받지만 **형제는 끝까지 간다.** 부작용(DB 쓰기·메일 발송)이 있으면 **실패 뒤에도 일어난다.**
* 멈추고 싶으면 **`TaskGroup`**(3.11+)이다. JS 도 같은 함정이다 — [JS 38번](../../../js/syntax/38-promise-combinators/2-summary.md) 의 「`Promise.all` 이 거부된 뒤에도 나머지는 끝까지 돈다」(`lines printed by the jobs after the combinator settled: 8`). **JS 에는 `TaskGroup` 같은 자동 취소가 없고**, 취소 신호를 따로 넘겨야 한다.

### (2) ★★★ 「`gather` 는 절대 자식을 취소하지 않는다」

* 반대쪽으로 외워도 틀린다 — **기다리는 쪽이 취소되면** `gather` 도 A·B·C 를 **전부 취소한다**(`outer cancelled` 행). 이 사건에서는 `TaskGroup` 과 **한 칸도 안 갈렸다.**

### (3) ★★★ 「`except CancelledError:` 에 왔으니 내가 취소된 것이다」

* `gather` 의 **자식 하나가 취소되면** 기다리는 코드도 `CancelledError` 를 받는다 — 그런데 `cancelling()` 은 **`0`** 이다(격자 `one child cancelled`). 정리하고 빠져나가면 **멀쩡한 태스크가 스스로 그만둔다.**

### (4) ★★★ `TaskGroup` 을 `except ValueError:` 로 받는다

* 예외가 **하나여도** `ExceptionGroup` 이다(격자 `ExceptionGroup[ValueError('b')]`). `except ValueError:` 는 **지나친다**(동작 3). `except*` 로 받는다.

### (5) ★★★ `async def` 안에서 동기 라이브러리를 부른다

* `time.sleep` 을 부른 판은 끼어든 줄이 **`0 / 5`** — 그동안 **다른 태스크가 하나도 못 돌았다**(동작 4). `requests`·동기 DB 드라이버·큰 계산이 전부 같은 자리다. **비동기 판 라이브러리**를 쓰거나 `to_thread` 로 옮긴다.

### (6) ★★★ `except BaseException:`·맨 `except:` 로 다 잡아 로그만 남긴다

* `CancelledError` 까지 삼켜 **취소가 없던 일이 되고**, `timeout` 블록 안이면 **`TimeoutError` 가 조용히 사라진다**(동작 6 — `after the block, no exception`). **잡았으면 다시 던진다.**

### (7) ★★ `timeout` 블록 **안에서** `except TimeoutError:` 를 쓴다

* 블록 안에서 보이는 것은 **`CancelledError`** 다(`inside the block: CancelledError`). `TimeoutError` 는 **블록 바깥**에서만 잡힌다.

### (8) ★★ `create_task` 의 반환값을 버린다 — 「내 코드는 잘 돌던데」

* `asyncio.sleep` 을 기다리는 태스크는 참조가 없어도 **안 사라졌다**(`0 / 20`) — 그래서 예제에서는 문제가 안 보인다. **혼자만 아는 퓨처를 기다리면 `20 / 20` 사라졌다.** 규칙은 **늘 쥔다**(집합에 넣고 `add_done_callback(set.discard)` — 문서의 예).

### (9) ★★ `wait(timeout=…)` 이 타임아웃에서 작업을 멈춰 줄 것이라 믿는다

* **아무것도 안 던지고 아무것도 안 취소한다**(`other.cancelled(): False`). `pending` 을 **직접** 취소해야 한다. 멈춰 주는 것은 `wait_for`·`timeout` 쪽이다.

### (10) ★ 3.11 코드와 3.10 코드를 섞는다

* `TaskGroup`·`asyncio.timeout`·`except*`·`cancelling()` 은 **3.11** 부터다. `wait()` 에 코루틴을 주던 3.10 코드는 **3.11 에서 `TypeError`** 다(동작 8).

## 구현 세부사항 대 언어 보장

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **라이브러리 보장** | `asyncio` 문서가 정한 취소 규칙·예외 모양 | 문서 문장을 열어서 인용 |
| **CPython 구현** | 한 걸음이 몇 번 돌았나 · 수거 경로 · 문구 | 실행 |
| **이 판(3.12.3 · 3.11.15)·이 머신의 관찰** | 이 판·이 부하에서 그랬을 뿐 | 출력 |
| ★ **못 잰 것** | 3.10 이하 · 순환 수집기가 저절로 도는 시점 | 판이 없다 · 손으로 `gc.collect()` 를 불렀다 |
| ★ **부적용** | 경과 시간 | 이 주제의 질문 밖이다 |

### 라이브러리 보장

| 사실 | 근거 |
|---|---|
| `gather` 는 첫 예외를 곧바로 넘기고 **형제를 안 취소한다** | `gather` — *"won't be cancelled and will continue to run"* |
| `gather` 가 **취소되면** 안 끝난 자식을 전부 취소한다 | `gather` — *"all submitted awaitables … are also cancelled"* |
| `gather` 의 자식이 취소되면 `CancelledError` 를 **낸 것처럼** 다루고 `gather` 는 안 취소된다 | `gather` 의 셋째 문단 |
| `TaskGroup` 은 첫 실패(취소 제외)에 나머지를 취소하고, 모은 예외를 `ExceptionGroup` 으로 올린다 · 몸통의 예외도 같다 | Task Groups 절 |
| `timeout` 은 현재 태스크를 취소하고 **블록 밖에서** `TimeoutError` 로 바꾼다 | `timeout` 과 그 note |
| `wait_for` 는 타임아웃에 취소하고 `TimeoutError` · `wait` 는 **안 던지고 안 취소한다** | `wait_for`·`wait` |
| `asyncio.TimeoutError` 는 `TimeoutError` 의 별칭(3.11) · `CancelledError` 는 `BaseException` 하위(3.8) | asyncio Exceptions |
| 루프는 태스크를 **약한 참조**로만 쥔다 — 참조가 없으면 언제든 수거될 수 있다 | `create_task` 의 Important |
| `CancelledError` 를 삼키면 `TaskGroup`·`timeout` 이 **오동작할 수 있다** · 억누를 거면 `uncancel()` 까지 | Task Cancellation |
| 태스크가 돌 때 같은 스레드의 다른 태스크는 못 돈다 · 블로킹 코드는 직접 부르지 마라 | Developing with asyncio |

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| 격자의 **걸음 수** 칸(`3`·`2`·`4`·`0`·`1`) — `gather`·`TaskGroup` 이 콜백을 **몇 차례에 나눠** 돌리나 | 실행 — ★ 문서는 순서를 말하지 않는다. **운명(`finished`/`cancelled`) 칸만 근거로** 썼다 |
| `sleep(0)` 이 **준비된 태스크들을 등록 순서로 한 바퀴** 돌리는 것 | 실행(동작 1 의 `a start \| b start \| a end \| b end`) |
| 참조 없는 태스크가 **무엇을 기다리느냐에 따라** 수거되거나 안 되는 것(타이머 핸들이 쥔다) | 실행(동작 7) — 문서는 「언제든」이라고만 한다 |
| 문구 — `Task was destroyed but it is pending!` · `Passing coroutines is forbidden, use tasks explicitly.` | 실행 |
| `TaskGroup` 의 `one raises` 칸에서 기다리던 태스크의 `cancelling()` 이 `1` 로 남은 것 | 실행 |

### 이 판(3.12.3)의 관찰

- **취소 전파 격자가 3.11.15 와 한 글자도 같았다** — 걸음 수 칸까지.
- **타이머를 쓴 탐침 셋이 세 번 캡처(재대조 포함)에서 한 번도 안 움직였다** — 블로킹 `0 / 5` · 양보 `5 / 5` · `wait` 의 `done`/`pending`.
- **두 태스크가 같은 걸음에서 동시에 실패하면 둘 다 봉투에 들어갔다**(동작 3 의 `['ValueError', 'KeyError']`) — 먼저 실패한 쪽이 다른 쪽을 취소하기 **전에** 둘 다 던졌다.

### 그래서 이렇게 적으면 틀린다

* ✗ 「`gather` 는 자식을 취소하지 않는다」\
  ○ **자식 하나가 예외일 때만** 그렇다. 기다리는 쪽이 취소되면 **전부 취소한다**(`outer cancelled` — `TaskGroup` 과 `0` 칸 차이).
* ✗ 「`TaskGroup` 은 첫 예외를 그대로 올린다」\
  ○ 하나여도 **`ExceptionGroup`** 이다.
* ✗ 「`CancelledError` 를 받았으면 내가 취소된 것이다」\
  ○ `gather` 의 자식이 취소된 경우 `cancelling()` 이 **`0`** 이다.
* ✗ 「`timeout` 을 걸면 마감에 반드시 `TimeoutError` 가 난다」\
  ○ 안에서 `CancelledError` 를 삼키면 **안 난다**(동작 6).
* ✗ 「참조 없는 태스크는 GC 된다 — 내가 해 봤는데 안 되던데?」 / 「안 되니 괜찮다」\
  ○ 둘 다 한 경우만 본 것이다. **`sleep` 은 `0 / 20`, 혼자만 아는 퓨처는 `20 / 20`** — 규칙은 문서대로 **늘 쥔다.**
* ✗ 「블로킹 호출은 루프를 느리게 한다」\
  ○ 이 문서가 잰 것은 「느리다」가 아니라 **「그동안 아무도 못 돈다」**(`0 / 5`)다. 시간은 재지 않았다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 여럿을 돌리고 **하나라도 실패하면 전부 멈춘다** | `TaskGroup`(3.11+) | 형제 취소 + 봉투 |
| 여럿을 돌리고 **실패해도 나머지 결과는 받는다** | `gather(return_exceptions=True)` | 형제 안 취소 · 예외가 결과 칸 |
| 3.10 이하에서 여럿을 돌린다 | `gather` + 실패 시 **직접** 취소 | `TaskGroup` 이 없다 |
| **먼저 끝난 것** 하나만 | `wait(…, FIRST_COMPLETED)` + `pending` 직접 취소 | `wait` 는 아무것도 안 취소한다 |
| 한 블록 전체에 마감 | `asyncio.timeout`(3.11+) | 여러 `await` 를 묶는다 · 밖에서 `TimeoutError` |
| awaitable 하나에 마감 | `wait_for` | 그 하나를 취소하고 `TimeoutError` |
| 동기 라이브러리를 꼭 불러야 한다 | `await asyncio.to_thread(fn, …)` | 루프 스레드가 양보한다 — ★ CPU 계산은 [53번](../53-gil-and-choosing-concurrency/2-summary.md) |
| 「걸어 두고 잊기」 | 집합에 넣고 `add_done_callback(set.discard)` | 루프는 약한 참조만 쥔다 |
| 취소를 받고 정리 | `try/finally`, 또는 `except CancelledError:` 뒤 `raise` | 삼키면 `timeout`·`TaskGroup` 이 깨진다 |

## 핵심 문장

1. **`gather` 는 형제를 안 취소하고, `TaskGroup` 은 취소한다 — 단 기다리는 쪽이 취소되면 둘 다 취소한다.** 격자에서 갈린 칸 **4 / 9**, 3.11 과 3.12 는 한 글자도 같았다.
2. **`TaskGroup` 의 예외는 하나여도 `ExceptionGroup`** — `except*` 로 받는다.
3. **`await` 가 없는 느린 호출은 루프 전체를 세운다** — `time.sleep` 은 끼어든 판 **0 / 5**, `asyncio.sleep`·`to_thread` 는 **5 / 5**.
4. **타임아웃은 취소다** — 안쪽은 `CancelledError`, 바깥은 `TimeoutError`. 안에서 삼키면 **`TimeoutError` 가 조용히 사라진다.**
5. **`create_task` 의 반환값은 쥔다** — 혼자만 아는 퓨처를 기다리던 태스크는 `gc.collect()` 에 **20 / 20** 사라졌다(`sleep` 은 0 / 20 — 그래서 예제로는 안 보인다).

## 관련 자료

* 목록: [python/syntax 주제 목록](../README.md) — 이 주제는 **52번**
* 선행: [51-asyncio-coroutine-basics](../51-asyncio-coroutine-basics/2-summary.md) — ★★★ **경계**: 코루틴 객체 · 이벤트 루프 · `asyncio.run` · `await` 없이 부르면 아무 일도 안 일어나는 것은 그쪽이 정본. 여기는 **태스크 여럿을 걸어 두면 누가 누구를 취소하나**부터.
* 다음: [53-gil-and-choosing-concurrency](../53-gil-and-choosing-concurrency/2-summary.md) — ★ **경계**: 스레드·프로세스·실행기 **선택**과 GIL 은 그쪽. 여기는 **`to_thread` 로 루프가 다시 끼어든다**까지(동작 4).
* 함께 보는 곳: [17-generators-yield](../17-generators-yield/2-summary.md) — 멈췄다 이어지는 자리. [27-exception-groups-and-except-star](../27-exception-groups-and-except-star/2-summary.md) — `ExceptionGroup`·`except*` 의 분배 규칙은 그쪽이 정본이다(동작 3 은 `TaskGroup` 이 봉투를 **만드는 자리**만).
* 다른 갈래: [Go 34 — `context`](../../../go/syntax/34-context-cancellation-deadlines-and-values/2-summary.md) — ★★ **취소 나무**: root 를 끊으면 `Done 을 받은 노드 7 / 7`, 자식 하나를 끊으면 **`2 / 7`**(부모·형제는 `Err=<nil>`) — **취소는 아래로만** 흐른다. `TaskGroup` 은 **형제 하나의 실패가 위로 올라가 형제 전부를 취소**한다(`one raises` 행) — Go 의 나무에는 **없는 방향**이다. 대신 Go 는 `cancel()` 이 `Done` 을 닫을 뿐이라 **안 보는 코드는 안 멈추고**, asyncio 는 **다음 `await` 에 예외를 꽂는다**(그래도 삼키면 안 멈춘다 — 동작 6).
  [Go 30 — `select`](../../../go/syntax/30-select-default-and-timeouts/2-summary.md) — `asyncio.wait(FIRST_COMPLETED)` 와 같은 자리(동작 8). [JS 38 — Promise 조합기](../../../js/syntax/38-promise-combinators/2-summary.md) — `Promise.all` 은 `gather` 기본과 같은 모양(나머지는 끝까지 돈다).
* 공식 문서: [Coroutines and Tasks](https://docs.python.org/3.12/library/asyncio-task.html) · [asyncio Exceptions](https://docs.python.org/3.12/library/asyncio-exceptions.html) · [Developing with asyncio](https://docs.python.org/3.12/library/asyncio-dev.html) · [What's New 3.11](https://docs.python.org/3.12/whatsnew/3.11.html#asyncio)

## 용어 풀이

* **태스크(Task)**: 코루틴을 루프에 걸어 두어 알아서 돌게 만든 객체. `create_task` 로 만든다.\
  예: 걸기만 하고 `await` 안 해도 끝까지 돈다(동작 1).
* **`gather`**: 여러 awaitable 을 동시에 돌리고 **결과를 인자 순서의 리스트**로 주는 함수.\
  예: 하나가 실패하면 그 예외를 곧바로 주고 형제는 계속 돈다.
* **`TaskGroup`**: `async with` 로 쓰는 태스크 묶음(3.11+). 한 실패에 나머지를 취소하고 `ExceptionGroup` 을 올린다.\
  예: 블록을 나가면 안의 태스크가 하나도 안 남는다.
* **취소(cancellation)**: `Task.cancel()` 로 태스크의 **다음 `await`** 에 `CancelledError` 를 꽂는 것.\
  예: 다시 던지면 `cancelled()` 가 `True`, 삼키면 `False`.
* **`CancelledError`**: 취소될 때 태스크 안에서 나는 예외. 3.8 부터 `BaseException` 직속.\
  예: `except Exception:` 에 안 걸린다.
* **`ExceptionGroup`**: 여러 예외를 묶은 예외(3.11+). `.exceptions` 로 꺼내고 `except*` 로 종류별로 받는다.\
  예: `ExceptionGroup[ValueError, KeyError]`.
* **`asyncio.timeout`**: 블록에 마감을 거는 비동기 컨텍스트 매니저(3.11+). 마감에 현재 태스크를 취소하고 밖에서 `TimeoutError` 로 바꾼다.\
  예: 블록 안에서는 `CancelledError` 가 보인다.
* **`wait_for`**: awaitable 하나에 마감을 거는 함수. 마감에 그것을 취소하고 `TimeoutError`.\
  예: 안쪽 코루틴의 `finally` 가 돈다.
* **`asyncio.wait`**: 태스크 집합을 기다려 `(done, pending)` 을 주는 함수. 아무것도 취소하지 않고 타임아웃에도 안 던진다.\
  예: `FIRST_COMPLETED` 뒤에도 느린 쪽은 돈다.
* **블로킹 호출(blocking call)**: `await` 없이 스레드를 붙잡는 호출. 그동안 같은 루프의 다른 태스크는 못 돈다.\
  예: `time.sleep`.
* **`asyncio.to_thread`**: 동기 함수를 다른 스레드에서 돌리고 그 결과를 `await` 로 받게 하는 함수(3.9+).\
  예: `await asyncio.to_thread(time.sleep, 1)` 동안 다른 태스크가 돈다.
* **약한 참조(weak reference)**: 객체를 **살려 두지 않는** 참조. 루프는 태스크를 이것으로만 쥔다.\
  예: `weakref.ref(task)()` 가 `None` 이면 이미 수거됐다.
* **`cancelling()`**: 태스크가 받은 취소 요청의 수(3.11+).\
  예: `gather` 의 자식이 취소돼 `CancelledError` 를 받은 쪽은 `0`.

## 더 들어가면

* ★ **`asyncio.shield`** — 문서의 말로 바깥의 취소로부터 awaitable 을 지키는 도구다(*"Protect an awaitable object from being cancelled."*). 격자의 `outer cancelled` 행에 넣으면 칸이 바뀔 자리지만 **이 격자에는 넣지 않았다** — 격자는 세 구조만 본다.

### 걸어 두고 잊은 태스크 둘 — 예외는 어디로 가나 · 3.12 의 `eager_task_factory`

```python
# e52_leftover.py
import asyncio
import gc


async def job(name, log):
    log.append(name + " start")
    await asyncio.sleep(0)
    log.append(name + " end")


async def fails():
    raise ValueError("v")


async def two_tasks(log):
    ta = asyncio.create_task(job("a", log))
    tb = asyncio.create_task(job("b", log))
    log.append("main: both tasks created")
    await ta
    await tb


async def main():
    loop = asyncio.get_running_loop()
    messages = []
    loop.set_exception_handler(lambda lp, ctx: messages.append(
        "%s ; %s" % (ctx["message"], type(ctx.get("exception")).__name__)))

    print("has eager_task_factory:", hasattr(asyncio, "eager_task_factory"))
    for factory in ("default", "eager"):
        if factory == "eager":
            if not hasattr(asyncio, "eager_task_factory"):
                continue
            loop.set_task_factory(asyncio.eager_task_factory)
        log = []
        await two_tasks(log)
        print("[%s] " % factory + " | ".join(log))
    loop.set_task_factory(None)

    asyncio.create_task(fails())      # created, never awaited, reference dropped
    for _ in range(3):
        await asyncio.sleep(0)
    gc.collect()
    print("loop exception handler got:", messages)


asyncio.run(main())
```

```text
===== python3 - <e52_leftover.py =====
has eager_task_factory: True
[default] main: both tasks created | a start | b start | a end | b end
[eager] a start | b start | main: both tasks created | a end | b end
loop exception handler got: ['Task exception was never retrieved ; ValueError']
(exit 0)
```

```text
===== python3.11 - <e52_leftover_py311.py =====
has eager_task_factory: False
[default] main: both tasks created | a start | b start | a end | b end
loop exception handler got: ['Task exception was never retrieved ; ValueError']
(exit 0)
```

* ★★ **아무도 `await` 안 한 태스크의 예외는 루프의 예외 처리기로 간다** — `Task exception was never retrieved ; ValueError`. **호출한 코드는 모른다**(두 판 같다). 동작 1 의 「비용」이 이것이다.
* ★ **3.12 의 `eager_task_factory` 를 켜면 `create_task` 가 그 자리에서 첫 `await` 까지 돈다** — `a start | b start | main: both tasks created`. 기본(`default`)과 **순서가 뒤집힌다.** 3.11 에는 그 이름이 없다(`has eager_task_factory: False`).
  ★ 이 칸은 **태스크 팩토리 설정**이 바꾼 것이다 — 동작 1 의 「걸어 두면 예약만 한다」는 **기본 팩토리**의 말이다.
