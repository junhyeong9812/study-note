# python/syntax/53-gil-and-choosing-concurrency — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> ★★★ 1번은 **열다섯 행의 두 열을 전부** 적고, 마지막 두 줄의 수까지 세어야 맞은 것이다.
> ★★★ 이 주제는 **속도·경과 시간을 묻지 않는다** — 시간은 판정에만 썼고 한 번도 싣지 않았다. 묻는 것은 **「겹쳤나」「넘었나」「잃었나」** 같은 참/거짓이다.
>
> 실행 환경: `python3` **3.12.3** · Linux(24 논리 코어) · 3번·4번은 `python3.11` 3.11.15 도 함께. 던지는 형태는 `python3 - <파일` 이고, **`multiprocessing` 을 쓰는 문항(1·4·5·6)은 파일로** 던졌다(`python3 e53_x.py`).
> ★ 선행 — [52](../52-asyncio-concurrency-structure/1-question.md)(블로킹 호출과 루프) · [51](../51-asyncio-coroutine-basics/1-question.md)(코루틴).

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 작업 셋 × 수단 다섯 — 두 작업의 구간과 CPU 시간 (예측)

```text
칸마다 두 값을 적는다 — 두 작업의 구간이 겹쳤나 · 두 작업의 CPU 시간 합이 벽시계 구간의 1.5 배를 넘었나.
(io 행의 둘째 값은 스크립트가 - 로 찍는다.) 기본 시작 방식과 전환 간격 두 줄, 마지막 두 줄의 수도 적는다.
```

```python
# e53_grid.py
import asyncio
import hashlib
import multiprocessing as mp
import sys
import threading
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

LOOPS = 3_000_000
BLOB = b"x" * 64_000_000
SLEEP = 0.2
TRIALS = 5


def cpu_time():
    # 스레드 안에서는 그 스레드의 CPU 시간, 프로세스 안에서는 그 프로세스의 CPU 시간
    if threading.current_thread() is threading.main_thread():
        return time.process_time()
    return time.thread_time()


def cpu():
    t0, c0 = time.time(), cpu_time()
    x = 0
    for i in range(LOOPS):
        x += i
    return t0, time.time(), cpu_time() - c0


def hash_():
    t0, c0 = time.time(), cpu_time()
    hashlib.sha256(BLOB).digest()
    return t0, time.time(), cpu_time() - c0


def io():
    t0, c0 = time.time(), cpu_time()
    time.sleep(SLEEP)
    return t0, time.time(), cpu_time() - c0


def by_threading(fn):
    out = [None, None]

    def body(k):
        out[k] = fn()

    ts = [threading.Thread(target=body, args=(k,)) for k in range(2)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    return out


def by_thread_pool(fn):
    with ThreadPoolExecutor(max_workers=2) as ex:
        futs = [ex.submit(fn) for _ in range(2)]
        return [f.result() for f in futs]


def mp_body(fn, q):
    q.put(fn())


def by_multiprocessing(fn):
    q = mp.Queue()
    ps = [mp.Process(target=mp_body, args=(fn, q)) for _ in range(2)]
    for p in ps:
        p.start()
    res = [q.get() for _ in ps]
    for p in ps:
        p.join()
    return res


def by_process_pool(fn):
    with ProcessPoolExecutor(max_workers=2) as ex:
        futs = [ex.submit(fn) for _ in range(2)]
        return [f.result() for f in futs]


def by_asyncio(fn):
    async def one():
        if fn is io:
            t0, c0 = time.time(), cpu_time()
            await asyncio.sleep(SLEEP)
            return t0, time.time(), cpu_time() - c0
        return fn()

    async def main():
        return await asyncio.gather(one(), one())

    return asyncio.run(main())


def judge(res):
    (s1, e1, c1), (s2, e2, c2) = res
    overlap = max(s1, s2) < min(e1, e2)
    wall = max(e1, e2) - min(s1, s2)
    return overlap, (c1 + c2) > 1.5 * wall


def show(values):
    return "/".join(sorted({str(v) for v in values}))


MEANS = [
    ("threading", by_threading),
    ("ThreadPoolExecutor", by_thread_pool),
    ("multiprocessing", by_multiprocessing),
    ("ProcessPoolExecutor", by_process_pool),
    ("asyncio", by_asyncio),
]

if __name__ == "__main__":
    print("version", sys.version_info[:2], "start method:", mp.get_start_method())
    print("switch interval:", sys.getswitchinterval())
    print(f"work;means;intervals overlap ({TRIALS} trials);cpu time sum > 1.5 x wall ({TRIALS} trials)")
    overlap_cells = parallel_cells = total = 0
    for work, fn in (("cpu", cpu), ("hash", hash_), ("io", io)):
        for name, run in MEANS:
            got = [judge(run(fn)) for _ in range(TRIALS)]
            ov = show(g[0] for g in got)
            pa = show(g[1] for g in got) if work != "io" else "-"
            print(work, name, ov, pa, sep=";")
            total += 1
            overlap_cells += ov == "True"
            parallel_cells += pa == "True"
    print(f"cells where the two intervals overlapped in every trial: {overlap_cells} / {total}")
    print(f"cells where cpu time sum exceeded 1.5 x wall in every trial: {parallel_cells} / {total - 5}")
```

### 2. ★★★ CPU 스레드 둘 — 전환 간격 두 가지 (예측)

```python
# e53_switch.py
import sys
import threading
import time

LOOPS = 3_000_000
TICK = 10_000
TRIALS = 5


def work(name, log, span):
    span[name] = [time.time()]
    x = 0
    for i in range(LOOPS):
        x += i
        if i % TICK == 0:
            log.append(name)
    span[name].append(time.time())


def trial(interval):
    sys.setswitchinterval(interval)
    log, span = [], {}
    ts = [threading.Thread(target=work, args=(k, log, span)) for k in "AB"]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    runs = [log[0]] + [b for a, b in zip(log, log[1:]) if a != b]
    (s1, e1), (s2, e2) = span["A"], span["B"]
    return len(runs) == 2, len(runs) > 2, "".join(runs[:4]), max(s1, s2) < min(e1, e2)


default = sys.getswitchinterval()
print("default switch interval:", default)
print("ticks logged per thread:", LOOPS // TICK)
print("interval;runs == 2;runs > 2;first runs;intervals overlap")
for interval in (default, 10.0):
    seen = {trial(interval) for _ in range(TRIALS)}
    for row in sorted(seen):
        print(interval, *row, sep=";")
```

### 3. ★★★ 본문 넷 × 간격 둘 × 판 둘 — 갱신을 잃었나 (예측)

```text
e53_race.py 를 아래 셸 스크립트가 python3.11 과 python3 로 던진다. 여덟 행의 두 값(3.11 · 3.12)과 마지막 두 줄의 수를 적는다.
```

```python
# e53_race.py
import sys
import threading

N_THREADS = 4
N_LOOPS = 100_000
TRIALS = 10

n = 0


def nop():
    pass


def plain():
    global n
    for _ in range(N_LOOPS):
        n += 1


def split():
    global n
    for _ in range(N_LOOPS):
        t = n
        t += 1
        n = t


def call_between():
    global n
    for _ in range(N_LOOPS):
        t = n
        nop()
        n = t + 1


LOCK = threading.Lock()


def call_between_locked():
    global n
    for _ in range(N_LOOPS):
        with LOCK:
            t = n
            nop()
            n = t + 1


def trial(body):
    global n
    n = 0
    ts = [threading.Thread(target=body) for _ in range(N_THREADS)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    return n != N_THREADS * N_LOOPS


for interval in (0.005, 1e-6):
    sys.setswitchinterval(interval)
    for body in (plain, split, call_between, call_between_locked):
        lost = [trial(body) for _ in range(TRIALS)]
        print(body.__name__, interval, any(lost), sep=";")
```

```sh
# e53_race_grid.sh
# 같은 탐침을 두 판으로 던지고 칸마다 견준다. 칸 = (본문, 전환 간격) · 값 = 판 10 번 중 한 판이라도 잃었나
set -o pipefail
a=$(python3.11 e53_race.py) || exit 1
b=$(python3 e53_race.py) || exit 1
echo "body;interval;3.11 any lost;3.12 any lost"
paste -d';' <(printf '%s\n' "$a") <(printf '%s\n' "$b" | cut -d';' -f3)
total=$(printf '%s\n' "$a" | wc -l)
diff_cells=$(paste -d'\t' <(printf '%s\n' "$a") <(printf '%s\n' "$b") | awk -F'\t' '$1 != $2' | wc -l)
lost_any_312=$(printf '%s\n' "$b" | awk -F';' '$3 == "True"' | wc -l)
echo "3.12 cells where some trial lost updates: $lost_any_312 / $total"
echo "cells that differ between 3.11 and 3.12: $diff_cells / $total"
```

### 4. ★★ 시작 방식 둘 — 자식이 보는 전역, 그리고 스레드가 도는 중의 `fork` (예측)

```text
python3 e53_start.py 와 python3.11 e53_start.py 두 번. 판마다 다섯 줄 안팎이다.
```

```python
# e53_start.py
import multiprocessing as mp
import re
import sys
import threading
import time
import warnings

STATE = "value at import"


def child(q):
    q.put((__name__, STATE))


def ask(method):
    ctx = mp.get_context(method)
    q = ctx.Queue()
    p = ctx.Process(target=child, args=(q,))
    p.start()
    got = q.get()
    p.join()
    return got


if __name__ == "__main__":
    print("version", sys.version_info[:2], "default start method:", mp.get_start_method())
    STATE = "value set in main block"
    for method in ("fork", "spawn"):
        name, state = ask(method)
        print(method, name, repr(state), sep=";")

    stop = threading.Event()
    t = threading.Thread(target=stop.wait)
    t.start()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        ask("fork")
    stop.set()
    t.join()
    print("fork while another thread runs -> warnings caught:", len(caught))
    for w in caught:
        print(" ", w.category.__name__, re.sub(r"pid=\d+", "pid=<pid>", str(w.message)))
```

### 5. ★★ 같은 스크립트를 파일로, 그리고 표준 입력으로 (예측)

```text
python3 e53_stdin.py 와 python3 - <e53_stdin.py 2>/dev/null 두 번의 표준 출력을 적는다.
```

```python
# e53_stdin.py
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor


def square(x):
    return x * x


if __name__ == "__main__":
    for method in ("fork", "spawn"):
        ctx = mp.get_context(method)
        p = ctx.Process(target=square, args=(3,))
        p.start()
        p.join()
        print(method, "Process exitcode:", p.exitcode)
        try:
            with ProcessPoolExecutor(max_workers=1, mp_context=ctx) as ex:
                print(method, "pool result:", ex.submit(square, 3).result())
        except Exception as e:
            print(method, "pool raised:", type(e).__name__, "|", e)
```

### 6. ★ 두 풀에 모듈 함수와 람다 (예측)

```python
# e53_pickle.py
import re
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor


def square(x):
    return x * x


def clean(e):
    return re.sub(r" at 0x[0-9a-f]+", "", str(e))


if __name__ == "__main__":
    for Pool in (ThreadPoolExecutor, ProcessPoolExecutor):
        for label, fn in (("def square", square), ("lambda", lambda x: x * x)):
            try:
                with Pool(max_workers=1) as ex:
                    print(Pool.__name__, label, "->", ex.submit(fn, 3).result(), sep=";")
            except Exception as e:
                print(Pool.__name__, label, "->", type(e).__name__, clean(e), sep=";")
```

### 7. ★★★ 「동시에 돌았다」는 로그를 읽는 법 (왜)

* 1번의 `cpu;threading` 칸에서 **첫 값만 보고** 「두 스레드가 동시에 돌았다」고 적으면 왜 틀리나 — 둘째 값과 2번의 교대 로그가 각각 무엇을 보태나?
* 「동시에 계산했나」를 경과 시간을 싣지 않고 묻기 위해 이 편이 쓴 창은 무엇이고, **그 창이 못 보는 것**은 무엇인가?

### 8. ★★★ 같은 스레드 칸, 다른 작업 (왜)

* 1번에서 **같은 `threading` 칸**인데 `cpu` 행과 `hash` 행의 둘째 값이 갈린다면, GIL 이 막는 것은 정확히 **무엇**인가 — 「스레드」인가 「바이트코드」인가?
* 그 행의 `asyncio` 칸은 왜 `hash` 라도 안 겹치나 — C 코드가 GIL 을 놓는 것과 이벤트 루프가 돌아오는 것은 무엇이 다른가?

### 9. ★★ free-threaded 빌드와 이 머신 (경계)

* 이 머신의 3.11·3.12 에서 「GIL 이 켜져 있나」를 물으면 무엇을 알 수 있고 무엇을 알 수 없나 — `sys._is_gil_enabled` 가 **없다**는 대답은 무슨 뜻인가?
* 「3.13 부터 GIL 이 없다」는 말을 3.13 과 3.14 문서의 문장으로 고쳐 적으면? 빌드가 free-threading 을 지원한다는 것과 **지금 GIL 이 꺼져 있다**는 것은 왜 따로 묻나?

### 10. 층 가르기 (경계)

* 「한 번에 한 스레드만 바이트코드를 실행한다」·「`spawn` 자식은 새 인터프리터다」·「전환 간격 기본값이 `0.005` 다」·「3번 격자의 `plain` 행에서 본 것」·「3.14 의 POSIX 기본 시작 방식은 `forkserver` 다」 —
  각각 **라이브러리 보장 · CPython 구현 · 이 판의 관찰 · 못 잰 것** 중 어디인가?
* ★ 「`+=` 는 원자적이다」와 「`+=` 는 원자적이지 않다」 — 이번에 연 문서는 어느 쪽을 말하나? 그러면 공유 카운터에는 무엇을 쓰나?

### 11. 이웃 주제·다른 갈래와의 경계 (연결)

* ★ 원리 쪽 문서([프로세스와 스레드 §10](../../../../process-thread/README.md))의 50 스레드 × 10만 회 `g_count += 1` 은 이 머신의 두 판에서 무엇을 냈나 — 그 결과로 「이제 락이 필요 없다」고 적으면 왜 틀리나?
* ★ Go 는 같은 잃은 갱신을 무엇으로 찾나([Go 35](../../../go/syntax/35-data-races-and-the-race-detector/2-summary.md)) — 파이썬에서는 그것이 무엇으로 드러나나?
* ★ 1번의 `cpu;asyncio` 칸은 [52번](../52-asyncio-concurrency-structure/2-summary.md)의 어느 동작과 같은 모양인가 — `asyncio` 안에서 CPU 작업을 해야 하면 어디로 넘기나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|---|---|---|---|
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |
