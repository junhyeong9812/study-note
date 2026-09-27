# python/syntax/53-gil-and-choosing-concurrency — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> [1-question.md](1-question.md)의 번호와 **1:1**로 대응한다. 질문 11개 = 답 11개.
>
> 이 파일의 모든 출력은 `python3` **3.12.3** 과 `python3.11` **3.11.15**(Linux, x86_64, 24 논리 코어)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> 던지는 형태는 `python3 - <파일` 로 고정했고, `multiprocessing` 을 쓰는 탐침만 **파일로**(`python3 e53_x.py`) 던졌다. ★★★ **경과 시간은 한 번도 싣지 않았다** — 판정(참/거짓)에만 썼다.

## 정답

### 1. `cpu` 행 — 스레드 `True;False` · 프로세스 `True;True` · `asyncio` `False;False` / `hash` 행 — 스레드도 `True;True` / `io` 행 — 다섯 칸 다 겹친다 · `13 / 15` · `6 / 10`

**출력**

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

```text
===== cd e53_grid && python3 e53_grid.py =====
version (3, 12) start method: fork
switch interval: 0.005
work;means;intervals overlap (5 trials);cpu time sum > 1.5 x wall (5 trials)
cpu;threading;True;False
cpu;ThreadPoolExecutor;True;False
cpu;multiprocessing;True;True
cpu;ProcessPoolExecutor;True;True
cpu;asyncio;False;False
hash;threading;True;True
hash;ThreadPoolExecutor;True;True
hash;multiprocessing;True;True
hash;ProcessPoolExecutor;True;True
hash;asyncio;False;False
io;threading;True;-
io;ThreadPoolExecutor;True;-
io;multiprocessing;True;-
io;ProcessPoolExecutor;True;-
io;asyncio;True;-
cells where the two intervals overlapped in every trial: 13 / 15
cells where cpu time sum exceeded 1.5 x wall in every trial: 6 / 10
(exit 0)
```

**왜 그런가**

* ★★★ **순수 파이썬 루프(`cpu`)는 스레드 둘이 칼을 번갈아 쥔다** — 둘 다 「진행 중」이라 구간은 겹치지만 **CPU 시간 합이 벽시계를 못 넘는다.** 프로세스는 GIL 이 프로세스마다 있어 **정말 동시에** 계산한다.
* ★★★ **`hashlib.sha256` 은 2047 바이트를 넘는 입력을 해시하는 동안 GIL 을 놓는다**(`hashlib` 문서) — 그래서 스레드인데 둘째 값이 `True`.
* ★★ **`time.sleep` 은 GIL 을 놓고 기다린다**(용어집 — *"the GIL is always released when doing I/O"*) — 다섯 수단이 다 겹친다.
* ★★ **`asyncio` 는 `await` 에서만 양보한다** — `cpu`·`hash` 코루틴 안에는 `await` 가 없으니 하나가 끝나야 다음이 시작한다. 구간조차 안 겹친다.
* ★ 두 풀은 바로 아래 수단과 칸이 **같다** — 풀은 인터페이스다(6번).

### 2. 기본 `0.005` 에서는 덩어리가 2 개를 넘고 `ABAB` · 구간 겹침 `True` / `10.0` 에서는 정확히 `AB` · 구간 겹침 `False`

**출력**

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

```text
===== python3 - <e53_switch.py =====
default switch interval: 0.005
ticks logged per thread: 300
interval;runs == 2;runs > 2;first runs;intervals overlap
0.005;False;True;ABAB;True
10.0;True;False;AB;False
(exit 0)
```

**왜 그런가**

* ★★★ **기본 간격마다 「넘겨라」 요청이 가서 두 스레드가 교대한다** — 로그에 두 이름이 **번갈아 덩어리로** 나온다. 한 덩어리 안에 두 이름이 섞이지 않는다 — **칼을 쥔 쪽만 적을 수 있다.**
* ★★★ **간격을 `10.0` 으로 올리면 A 가 일을 다 끝낼 때까지 아무도 못 빼앗는다** — 메인 스레드가 B 를 `start()` 하는 것조차 A 가 끝난 뒤라 **구간이 안 겹친다.** 교대를 만드는 것이 이 간격이다.
* ★ 누가 다음에 쥐는지는 **OS 가 정한다**(문서 — *"The interpreter doesn't have its own scheduler."*). `ABAB` 는 스레드 둘일 때 5판 같았던 **관찰**이다.

### 3. `call_between` 만 잃었다(두 간격 다 — 10판 중 한 판 이상) · `plain`·`split`·락을 쓴 본문은 안 잃었다 · `2 / 8` · 판 차이 `0 / 8`

**출력**

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

```text
===== cd e53_race && bash e53_race_grid.sh =====
body;interval;3.11 any lost;3.12 any lost
plain;0.005;False;False
split;0.005;False;False
call_between;0.005;True;True
call_between_locked;0.005;False;False
plain;1e-06;False;False
split;1e-06;False;False
call_between;1e-06;True;True
call_between_locked;1e-06;False;False
3.12 cells where some trial lost updates: 2 / 8
cells that differ between 3.11 and 3.12: 0 / 8
(exit 0)
```

두 판의 바이트코드 — `+=` 가 명령 몇 개인가.

```python
# e53_dis.py
import dis

n = 0


def plain():
    global n
    for _ in range(3):
        n += 1


def call_between():
    global n
    for _ in range(3):
        t = n
        nop()
        n = t + 1


def nop():
    pass


for f in (plain, call_between):
    print("--", f.__name__)
    for ins in dis.get_instructions(f):
        if ins.opname in ("CACHE", "RESUME", "NOP"):
            continue
        print(f"  {ins.opname:<16} {ins.argrepr}".rstrip())
```

```text
===== python3 - <e53_dis.py =====
-- plain
  LOAD_GLOBAL      NULL + range
  LOAD_CONST       3
  CALL
  GET_ITER
  FOR_ITER         to 50
  STORE_FAST       _
  LOAD_GLOBAL      n
  LOAD_CONST       1
  BINARY_OP        +=
  STORE_GLOBAL     n
  JUMP_BACKWARD    to 24
  END_FOR
  RETURN_CONST     None
-- call_between
  LOAD_GLOBAL      NULL + range
  LOAD_CONST       3
  CALL
  GET_ITER
  FOR_ITER         to 74
  STORE_FAST       _
  LOAD_GLOBAL      n
  STORE_FAST       t
  LOAD_GLOBAL      NULL + nop
  CALL
  POP_TOP
  LOAD_FAST        t
  LOAD_CONST       1
  BINARY_OP        +
  STORE_GLOBAL     n
  JUMP_BACKWARD    to 24
  END_FOR
  RETURN_CONST     None
(exit 0)
```

```text
===== python3.11 - <e53_dis_py311.py =====
-- plain
  LOAD_GLOBAL      NULL + range
  LOAD_CONST       3
  PRECALL
  CALL
  GET_ITER
  FOR_ITER         to 58
  STORE_FAST       _
  LOAD_GLOBAL      n
  LOAD_CONST       1
  BINARY_OP        +=
  STORE_GLOBAL     n
  JUMP_BACKWARD    to 32
  LOAD_CONST       None
  RETURN_VALUE
-- call_between
  LOAD_GLOBAL      NULL + range
  LOAD_CONST       3
  PRECALL
  CALL
  GET_ITER
  FOR_ITER         to 90
  STORE_FAST       _
  LOAD_GLOBAL      n
  STORE_FAST       t
  LOAD_GLOBAL      NULL + nop
  PRECALL
  CALL
  POP_TOP
  LOAD_FAST        t
  LOAD_CONST       1
  BINARY_OP        +
  STORE_GLOBAL     n
  JUMP_BACKWARD    to 32
  LOAD_CONST       None
  RETURN_VALUE
(exit 0)
```

**왜 그런가**

* ★★★ **`n += 1` 은 명령 넷**(`LOAD_GLOBAL` · `LOAD_CONST` · `BINARY_OP +=` · `STORE_GLOBAL`)이다 — 두 판 다. **GIL 은 명령 하나만 지킨다.** 읽기와 쓰기 사이에서 칼이 넘어가면 잃는다.
* ★★★ **이 두 판에서 `plain`·`split` 은 안 잃었다** — 간격을 `1e-06` 으로 줄여도. **「안 잃었다」는 보장이 아니다**(문서에 `+=` 의 원자성 문장이 없다). 읽기·쓰기 사이에 **파이썬 함수 호출(`CALL`) 하나**를 끼우니 잃었다.
  왜 그 자리에서만 전환이 일어났는지는 **인터프리터 소스의 영역**이다 — 읽지 않았다.
* ★★ **락으로 묶은 `call_between_locked` 는 안 잃었다** — 이쪽이 보장이다(`Lock` 은 한 번에 한 스레드만 쥔다).
* ★ **3.11 은 `CALL` 앞에 `PRECALL` 이 있다** — 바이트코드는 다른데 격자는 **`0 / 8`**, 한 칸도 안 갈렸다.

### 4. 두 판 다 기본 `fork` · `fork` 자식은 `'value set in main block'`(`__main__`) · `spawn` 자식은 `'value at import'`(`__mp_main__`) · 스레드가 도는 중의 `fork` — 3.12 는 `DeprecationWarning` 한 건, 3.11 은 0 건

**출력**

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

```text
===== cd e53_start && python3 e53_start.py =====
version (3, 12) default start method: fork
fork;__main__;'value set in main block'
spawn;__mp_main__;'value at import'
fork while another thread runs -> warnings caught: 1
  DeprecationWarning This process (pid=<pid>) is multi-threaded, use of fork() may lead to deadlocks in the child.
(exit 0)
```

```text
===== cd e53_start && python3.11 e53_start.py =====
version (3, 11) default start method: fork
fork;__main__;'value set in main block'
spawn;__mp_main__;'value at import'
fork while another thread runs -> warnings caught: 0
(exit 0)
```

**왜 그런가**

* ★★★ **`fork` 는 부모를 통째로 복제한다** — 자식은 main 블록에서 바꾼 값까지 본다. **`spawn` 은 새 인터프리터가 주 모듈을 `__mp_main__` 으로 다시 import** 한다 — 가드 안쪽이 안 돌아 import 직후 값을 본다.
* ★★ **3.12 부터 여러 스레드인 프로세스의 `fork` 가 `DeprecationWarning`** 이다(문서 `versionchanged:: 3.12`). 경고 문구의 PID 는 스크립트가 `pid=<pid>` 로 바꿔 찍었다.
* ★ 3.14 에서 POSIX 기본은 **`forkserver`** 가 된다(문서 — 이 머신에 3.14 가 없다). 그 판에서는 아무 문맥도 안 준 자식이 `spawn` 과 같은 쪽 값을 볼 것이라는 게 **문서에서 온 예측**이다.

### 5. 파일로는 두 방식 다 `exitcode 0`·`9` / 표준 입력으로는 `spawn` 만 `exitcode 1`·`BrokenProcessPool` — 자식은 `'<stdin>'` 을 파일로 찾다가 `FileNotFoundError`

**출력**

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

```text
===== cd e53_stdin && python3 e53_stdin.py =====
fork Process exitcode: 0
fork pool result: 9
spawn Process exitcode: 0
spawn pool result: 9
(exit 0)
```

```text
===== cd e53_stdin && python3 - <e53_stdin.py 2>/dev/null =====
fork Process exitcode: 0
fork pool result: 9
spawn Process exitcode: 1
spawn pool raised: BrokenProcessPool | A process in the process pool was terminated abruptly while the future was running or pending.
(exit 0)
```

```sh
# e53_stdin_err.sh
# 표준 출력은 버리고 표준 오류에서 예외 줄만 센다(트레이스백 본문은 표준 라이브러리 경로가 박혀 싣지 않는다)
err=$(python3 - <e53_stdin.py 2>&1 >/dev/null)
printf '%s\n' "$err" | grep -E '^[A-Za-z.]+(Error|Exception|Warning)' | sort | uniq -c
```

```text
===== cd e53_stdin && bash e53_stdin_err.sh 2>&1 | sed "s#$PWD#.#g" =====
      2 FileNotFoundError: [Errno 2] No such file or directory: './<stdin>'
(exit 0)
```

**왜 그런가**

* ★★★ **`spawn` 자식은 주 모듈을 다시 읽어야 한다** — 표준 입력이면 다시 읽을 파일이 없다. 자식은 `'<stdin>'` 이라는 이름을 **현재 디렉토리의 파일**로 찾다가 죽었다(두 번 — `Process` 하나, 풀 일꾼 하나).
  문서 — *"Functionality within this package requires that the `__main__` module be importable by the children."*
* ★★ **부모는 원인을 모른다** — `Process` 는 `exitcode 1`, 풀은 `BrokenProcessPool`(*"terminated abruptly"*)뿐이다. 원인은 **자식의 표준 오류**에만 있다.
* ★ `fork` 는 복제라 다시 읽을 것이 없어 표준 입력에서도 된다 — **3.14 에서 기본이 `forkserver` 가 되면** 이 차이가 기본값에서 드러날 수 있다(예측).

### 6. 스레드 풀은 둘 다 `9` · 프로세스 풀은 람다에서 `PicklingError` — *"attribute lookup <lambda> on `__main__` failed"* · 3.11 도 같다

**출력**

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

```text
===== cd e53_pickle && python3 e53_pickle.py =====
ThreadPoolExecutor;def square;->;9
ThreadPoolExecutor;lambda;->;9
ProcessPoolExecutor;def square;->;9
ProcessPoolExecutor;lambda;->;PicklingError;Can't pickle <function <lambda>>: attribute lookup <lambda> on __main__ failed
(exit 0)
```

```text
===== cd e53_pickle && python3.11 e53_pickle.py =====
ThreadPoolExecutor;def square;->;9
ThreadPoolExecutor;lambda;->;9
ProcessPoolExecutor;def square;->;9
ProcessPoolExecutor;lambda;->;PicklingError;Can't pickle <function <lambda>>: attribute lookup <lambda> on __main__ failed
(exit 0)
```

**왜 그런가**

* ★★ **프로세스 풀은 함수와 인자를 pickle 해서 보낸다** — 함수는 **`모듈.이름`** 으로 pickle 되고 받는 쪽이 그 이름으로 찾는다. `<lambda>` 는 모듈에 그 이름이 없다.
* ★ **스레드 풀은 같은 프로세스라 객체를 그대로 건넨다** — 그래서 람다도 된다. 풀을 바꾸면 **GIL 에 관한 것은 안 바뀌고(1번) 넘길 수 있는 것만 바뀐다.**
* ★ 주소(`at 0x…`)는 스크립트가 지웠다 — 흔들리는 칸이다.

### 7. 첫 값(구간 겹침)은 교대로도 참이 된다 — 둘째 값(CPU 시간 합 > 1.5 × 벽시계)과 교대 로그(`ABAB`)가 「번갈아」를 보인다 · 그 창은 코어 수를 못 본다

* ★★★ **구간이 겹친다는 것은 「둘 다 시작했고 아직 안 끝났다」까지다.** 5ms 마다 번갈아 돌아도 겹친다. 1번의 `cpu;threading` 이 `True;False` 인 까닭이다.
* ★★ **둘째 값** — 두 작업이 스스로 잰 CPU 시간의 합이 벽시계 구간보다 **크면** 두 CPU 가 동시에 일했다는 뜻이다. 한 번에 하나씩이면 합이 벽시계를 못 넘는다. **교대 로그**는 그 「하나씩」의 **순서**(`ABAB`)를 보이고, 간격을 `10.0` 으로 올리면 `AB` 가 되어 교대의 원인을 가리킨다.
* ★ **제5의 상태** — 코어 사용률 도구 대신 **CPU 시간 합**으로 물었다. 그 창은 **문턱 1.5 를 넘었나** 하나만 답한다 — 코어가 몇 개 쓰였는지, 어느 코어였는지는 못 본다. 기계가 몹시 바쁘면 프로세스 칸이 뒤집힐 수 있다(흔들리는 칸).

### 8. GIL 이 막는 것은 「파이썬 바이트코드」다 — `hashlib` 은 GIL 을 놓고 C 로 계산한다 · 이벤트 루프는 그 호출이 끝나야 돌아온다

* ★★★ 용어집 — *"only one thread executes Python bytecode at a time"* · *"some extension modules … release the GIL when doing computationally intensive tasks such as compression or hashing."* `cpu` 는 바이트코드를 계속 돌리고 `hash` 는 C 코드가 돈다.
* ★★ **`hash;asyncio` 가 `False`** 인 것은 GIL 과 무관하다 — `asyncio` 는 **스레드가 하나**이고, 그 스레드가 `sha256(...)` 호출 안에 있는 동안 루프가 다른 코루틴으로 **갈 수 없다.** GIL 을 놓아도 **놓은 GIL 을 받을 다른 스레드가 없다.**
* ★ 64MB 한 번만 쟀다 — 2047 바이트 이하 칸은 재지 않았다(문서대로면 놓지 않는다).

### 9. 이 머신의 두 판은 free-threaded 빌드가 아니다(`Py_GIL_DISABLED` `None` · `sys._is_gil_enabled` 없음 · `python3.13t` 없음) — 3.13 은 실험, 3.14 는 지원되지만 선택 · 빌드 지원과 실행 중 상태는 따로다

**출력**

```python
# e53_ft.py
import shutil
import sys
import sysconfig

print("version:", sys.version.split()[0])
print("'free-threading' in sys.version:", "free-threading" in sys.version)
print("Py_GIL_DISABLED:", sysconfig.get_config_var("Py_GIL_DISABLED"))
print("hasattr(sys, '_is_gil_enabled'):", hasattr(sys, "_is_gil_enabled"))
if hasattr(sys, "_is_gil_enabled"):
    print("sys._is_gil_enabled():", sys._is_gil_enabled())
for exe in ("python3.13t", "python3.14t", "python3.13", "python3.14"):
    print(f"which {exe}:", shutil.which(exe) is not None)
```

```text
===== python3 - <e53_ft.py =====
version: 3.12.3
'free-threading' in sys.version: False
Py_GIL_DISABLED: None
hasattr(sys, '_is_gil_enabled'): False
which python3.13t: False
which python3.14t: False
which python3.13: False
which python3.14: False
(exit 0)
```

```text
===== python3.11 - <e53_ft_py311.py =====
version: 3.11.15
'free-threading' in sys.version: False
Py_GIL_DISABLED: None
hasattr(sys, '_is_gil_enabled'): False
which python3.13t: False
which python3.14t: False
which python3.13: False
which python3.14: False
(exit 0)
```

* ★★★ **알 수 있는 것** — 이 인터프리터가 **GIL 이 있는 빌드**라는 것. **알 수 없는 것** — free-threaded 빌드에서 1번·3번 격자가 어떻게 되나(**못 잰 것**).
  `sys._is_gil_enabled` 가 **없다**는 것은 「GIL 이 꺼졌다」도 「켜졌다」도 아니라 **그 함수가 들어온 3.13 보다 옛 판**이라는 뜻이다(`versionadded:: 3.13` · *"It is not guaranteed to exist in all implementations of Python."*).
* ★★ **3.13** — *"This is an experimental feature and therefore is not enabled by default. The free-threaded mode requires a different executable, usually called `python3.13t`"* · **3.14** — *"The free-threaded build of Python is now supported and no longer experimental."* · *"officially supported but still optional."*
* ★ **따로 묻는 까닭** — 빌드가 지원해도 실행 중에 GIL 이 다시 켜질 수 있다(`PYTHON_GIL`·`-X gil=1` · 준비 안 된 C 확장). 빌드는 `sysconfig.get_config_var("Py_GIL_DISABLED")`(HOWTO 의 *"recommended mechanism"*), 지금 상태는 `sys._is_gil_enabled()`.

### 10. CPython 구현 · 라이브러리 보장 · CPython 구현 · 이 판의 관찰 · 못 잰 것 — 원자성은 **어느 쪽도 문서에 없다** → 락

* 「한 번에 한 스레드만 바이트코드를 실행」 — **CPython 구현**(용어집의 주어가 *"the CPython interpreter"* · `threading` 의 문장은 impl-detail 상자). ★★★ 언어 보장으로 적으면 틀린다.
* 「`spawn` 자식은 새 인터프리터」 — **라이브러리 보장**(`multiprocessing` 의 start methods 절).
* 「전환 간격 기본값 `0.005`」 — **CPython 구현**(문서는 뜻만 적고, 값은 실행으로 봤다).
* 「3번의 `plain` 행에서 본 것」(한 번도 안 잃었다) — **이 판의 관찰.**
* 「3.14 의 POSIX 기본 `forkserver`」 — 문서가 말하는 **보장**이지만 이 머신에서는 **못 잰 것.**
* ★★ **이번에 연 문서(용어집·`threading`·`sys`)에는 `+=` 의 원자성 문장이 어느 쪽으로도 없다** — `threading` 에서 *"atomically"* 는 락·조건 변수 **메서드**에만 쓰였다. 보장이 없으니 **`threading.Lock`**.

### 11. 두 판 여섯 번 다 `5,000,000` — 그래도 락이 필요하다(호출이 끼면 잃었다) · Go 는 `-race` 검출기, 파이썬은 틀린 값으로만 · 52 의 블로킹 호출과 같은 모양 — 스레드·프로세스 풀로 넘긴다

```python
# e53_doc_case.py
import threading

g_count = 0


def thread_main():
    global g_count
    for i in range(100000):
        g_count += 1


def trial():
    global g_count
    g_count = 0
    threads = [threading.Thread(target=thread_main) for _ in range(50)]
    for th in threads:
        th.start()
    for th in threads:
        th.join()
    return g_count


print("expected 5,000,000 ; got:", [f"{trial():,}" for _ in range(3)])
```

```text
===== python3 - <e53_doc_case.py =====
expected 5,000,000 ; got: ['5,000,000', '5,000,000', '5,000,000']
(exit 0)
```

```text
===== python3.11 - <e53_doc_case_py311.py =====
expected 5,000,000 ; got: ['5,000,000', '5,000,000', '5,000,000']
(exit 0)
```

* ★★ 원리 쪽 문서는 이 코드가 「**매번 다른 값**」을 낸다고 적는데, 이 머신 3.11·3.12 에서는 **세 번씩 다 정확했다.** 그 문서에 **어느 판에서 쟀는지가 없다.**
  ★★★ 「그러니 락이 필요 없다」는 틀린다 — 같은 GIL 아래에서 **읽기·쓰기 사이에 호출 하나가 끼면 잃었다**(3번). 안 잃은 것은 **이 본문·이 판**의 관찰이다.
* ★ **Go** 는 레이스를 **실행해서 `-race` 검출기로** 찾는다([Go 35](../../../go/syntax/35-data-races-and-the-race-detector/2-summary.md) — 「데이터 레이스는 『순서 없이』다, 『동시에』가 아니다」). 파이썬 표준에는 그런 검출기가 없고, 잃은 갱신은 **값이 틀려서야** 보인다 — 그래서 **틀린 값이 안 나온 판이 가장 위험한 근거**다.
* ★ `cpu;asyncio` 가 `False;False` 인 것은 [52번](../52-asyncio-concurrency-structure/2-summary.md)이 보인 **「코루틴 안의 블로킹 호출이 다른 태스크를 못 끼어들게 한다」** 와 같은 모양이다. 넘기는 법(`to_thread`·실행기)은 52번이 정본이고, **CPU 작업이면 스레드가 아니라 프로세스 풀**이다(1번의 `cpu` 행).

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 겹침 격자 | `cd e53_grid && python3 e53_grid.py`(칸마다 5판) | 3(캡처 + 재대조 + `PYTHONHASHSEED` 바꾼 재캡처) | **13 / 15** · **6 / 10** |
| 교대 로그 | `python3 - <e53_switch.py`(간격마다 5판) · 시험 중 3.11 로도 한 번 | 3 | `ABAB` · `AB` |
| 잃은 갱신 격자 | `cd e53_race && bash e53_race_grid.sh`(`python3.11`·`python3`, 칸마다 10판) | 3 | **2 / 8** · 판 차이 **0 / 8** |
| `dis` | `python3 - <e53_dis.py` · `python3.11 - <e53_dis_py311.py` | 3씩 | 명령 넷 · 3.11 의 `PRECALL` |
| 원리 문서의 실험 | `python3 - <e53_doc_case.py` · `python3.11 - <e53_doc_case_py311.py` | 3씩(한 번에 3회) | 전부 `5,000,000` |
| 시작 방식 | `cd e53_start && python3 e53_start.py` · `python3.11 e53_start.py` | 3씩 | `fork` / `spawn` 전역 · 경고 1 대 0 |
| 표준 입력 | `cd e53_stdin && …`(세 명령) | 3 | `spawn` 만 `exitcode 1` · `FileNotFoundError` 2 |
| pickle | `cd e53_pickle && python3 e53_pickle.py` · `python3.11 …` | 3씩 | 람다만 `PicklingError` |
| free-threaded 판별 | `python3 - <e53_ft.py` · `python3.11 - <e53_ft_py311.py` | 3씩 | 두 판 다 GIL 빌드 |

**구현 의존 항목** — 판이 오르면 다시 돌려야 하는 것.

| 항목 | 왜 |
|---|---|
| ★★★ 겹침 격자 · 잃은 갱신 격자 | **free-threaded 빌드**에서 뜻이 바뀐다 — 이 머신에 없다(못 잰 것) |
| ★★ 시작 방식 · 표준 입력 | **3.14** 의 POSIX 기본이 `forkserver`(문서) |
| ★ `dis` | 바이트코드는 판마다 바뀐다(이미 3.11 과 3.12 가 다르다) |
| ★ `plain` 이 안 잃은 것 | 전환이 일어나는 자리는 인터프리터 구현이다 |

★ **못 잰 것 하나 더 — `forkserver`.** 시험 판에서 `forkserver` 칸을 넣었더니 두 판 다 **`OSError: AF_UNIX path too long`** 으로 죽었다 — 캡처가 임시 디렉토리를 깊은 스크래치패드 경로로 돌려서 **유닉스 소켓 경로 길이 한도**를 넘은 것이다. 그래서 그 칸을 뺐다. 짧은 임시 경로에서는 다를 것이다(재지 않았다).
★ **안 흔들리는 칸** — 격자의 **「13 / 15」·「6 / 10」·「2 / 8」·「0 / 8」** · 칸마다의 참/거짓 · `dis` 명령 · 시작 방식별 값 · 예외 타입 · `(exit N)`.
★★ **이 주제가 한 번도 안 실은 것** — **경과 시간·배수**(판정에만 썼다) · **free-threaded·3.14**(판 없음 — 못 잰 것).
