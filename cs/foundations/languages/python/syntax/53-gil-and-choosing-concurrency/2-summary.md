# python/syntax/53-gil-and-choosing-concurrency — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만(문서 원본 `.rst` 를 받아 문장을 찾았다).
> - [용어집 — global interpreter lock(3.12)](https://docs.python.org/3.12/glossary.html#term-global-interpreter-lock) — *"The mechanism used by the CPython interpreter to assure that only one thread executes Python bytecode at a time."* ·
>   *"some extension modules, either standard or third-party, are designed so as to release the GIL when doing computationally intensive tasks such as compression or hashing. Also, the GIL is always released when doing I/O."*
> - [`threading`(3.12)](https://docs.python.org/3.12/library/threading.html) 의 CPython 구현 세부 상자 — *"In CPython, due to the Global Interpreter Lock, only one thread can execute Python code at once"* · *"you are advised to use multiprocessing or concurrent.futures.ProcessPoolExecutor."*
> - [`hashlib`(3.12)](https://docs.python.org/3.12/library/hashlib.html) — *"the Python GIL is released while computing a hash supplied more than 2047 bytes of data at once"*
> - [`sys.setswitchinterval`(3.12)](https://docs.python.org/3.12/library/sys.html#sys.setswitchinterval) — *"This floating-point value determines the ideal duration of the "timeslices" allocated to concurrently running Python threads."* · *"which thread becomes scheduled at the end of the interval is the operating system's decision. The interpreter doesn't have its own scheduler."*
> - [`multiprocessing` — Contexts and start methods(3.12)](https://docs.python.org/3.12/library/multiprocessing.html#contexts-and-start-methods) — *spawn* 은 *"The parent process starts a fresh Python interpreter process."* · *fork* 는 *"The child process, when it begins, is effectively identical to the parent process."* · 3.12 의 *"will raise a DeprecationWarning"* ·
>   *"Functionality within this package requires that the `__main__` module be importable by the children."*
> - [`multiprocessing`(3.14)](https://docs.python.org/3.14/library/multiprocessing.html#contexts-and-start-methods) · [What's New 3.14](https://docs.python.org/3.14/whatsnew/3.14.html) — *"On POSIX platforms the default start method was changed from fork to forkserver"* · *"The free-threaded build of Python is now supported and no longer experimental."* ★ **3.14 는 이 머신에 없다 — 문서 인용만.**
> - [What's New 3.13 — Free-threaded CPython](https://docs.python.org/3.13/whatsnew/3.13.html#free-threaded-cpython) — *"This is an experimental feature and therefore is not enabled by default."* · [free threading HOWTO(3.14)](https://docs.python.org/3.14/howto/free-threading-python.html) — *"The `sysconfig.get_config_var("Py_GIL_DISABLED")` configuration variable can be used to determine whether the build supports free threading."*
> - [`sys._is_gil_enabled`(3.14 문서)](https://docs.python.org/3.14/library/sys.html#sys._is_gil_enabled) — *"versionadded:: 3.13"* · *"It is not guaranteed to exist in all implementations of Python."*
>
> **실행 검증** — 이 문서에 실린 출력은 전부 이 머신(Linux, 24 논리 코어)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.\
> 판은 `python3` **3.12.3** 이 본판이고, 판 경계를 위해 `python3.11` **3.11.15** 로 같은 탐침을 다시 던졌다(잃은 갱신 격자 · `dis` · 시작 방식 · 판별 블록).\
> ★★★ **이 문서는 경과 시간을 한 줄도 싣지 않는다.** 시간은 **판정에만** 쓰고(두 구간이 겹쳤나 · CPU 시간 합이 벽시계 구간보다 컸나) 출력은 **참/거짓**으로만 냈다. 「몇 배 빠르다」는 없다.\
> ★★ `multiprocessing` 탐침은 **파일로 던졌다**(`python3 e53_x.py` — 트리 실험). 표준 입력으로 던지면 `spawn` 이 안 되는 것은 동작 5 가 따로 보인다.\
> **버전** — `concurrent.futures`·`sys.setswitchinterval` **3.2** · `fork` + 여러 스레드 `DeprecationWarning` **3.12** · free-threaded 빌드(실험)·`sys._is_gil_enabled` **3.13** · free-threaded 공식 지원(PEP 779)·POSIX 기본 시작 방식 `forkserver` **3.14**(문서만).\
> ★ **구현 대 언어 보장 한 줄** — ★★★ **GIL 은 언어 보장이 아니라 CPython 구현이다**(용어집 문장이 주어를 *"the CPython interpreter"* 로 둔다 · `threading` 의 문장은 **impl-detail 상자** 안에 있다). `+=` 가 원자가 아니라는 것도, 원자처럼 보이는 것도 **보장이 아니다.** 겹침 격자의 참/거짓은 **이 판·이 머신의 관찰**이다.\
> ★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다 | 안 흔들린다(근거로 써도 되는 칸) |
> |---|---|
> | 경과 시간 · 각 판에서 잃은 갱신의 **개수**(그래서 한 번도 안 찍었다) | ★★ 격자 마지막 줄 **「… N / M」** · 칸마다의 참/거짓(판 N 번을 모아 한 값으로 낸 것) |
> | ★ 잃는 본문에서 **몇 판이 잃었나** — ★ 처음엔 「모든 판에서 잃었나」 칸도 냈는데 `PYTHONHASHSEED` 재캡처에서 기본 간격 칸이 `False` → `True` 로 뒤집혀(판 차이가 `0 / 8` → `1 / 8`) **그 칸을 뺐다.** 남긴 것은 「10판 중 한 판이라도 잃었나」뿐이다 | `dis` 의 명령 이름과 순서 · 시작 방식별 자식의 `__name__`·전역 값 · 예외 **타입** |
> | 기계의 부하(다른 작업이 코어를 다 쓰면 「CPU 시간 합 > 1.5 × 벽시계」 칸이 뒤집힐 수 있다 — 판정 문턱을 1.5 로 둔 까닭) | `sys.getswitchinterval()` 의 값 `0.005`(CPython 기본값 — 판마다 같았다) |
> | 경고 문구의 PID(스크립트가 `pid=<pid>` 로 바꿔 찍었다 — 소스에 보인다) · 주소(`at 0x…` 를 스크립트가 지웠다) | `(exit N)` · 자식의 표준 오류에서 센 예외 줄 수 |
>
> **선행** — [52-asyncio-concurrency-structure](../52-asyncio-concurrency-structure/2-summary.md)(★★★ **블로킹 호출이 루프를 멈추는 것은 그쪽이 정본** — 여기는 「그럼 무엇을 고르나」) ·
> [51-asyncio-coroutine-basics](../51-asyncio-coroutine-basics/2-summary.md)(코루틴은 `await` 에서 멈췄다가 이어진다 — 그쪽 동작 5 가 `send` 로 손으로 돌려 보였다).
> 원리 쪽 정본 — [프로세스와 스레드](../../../../process-thread/README.md)(§8 멀티 프로세스 대 멀티 스레드 · §10 경쟁 조건 · §12 GIL) · [history/python — 핵심 개념의 진화](../../../../../../history/python/06-핵심-개념-진화.md)(§1 GIL 의 연혁 · PEP 703).

## 한눈에 — 쉽게 말하면

**CPython 은 칼이 하나뿐인 부엌이다.** 요리사(스레드)를 여럿 불러도 **칼질(파이썬 바이트코드)은 한 번에 한 명만** 한다.

* 요리사끼리 칼을 **정해진 간격(5ms)마다** 넘겨받는다 — 그래서 **둘 다 「요리 중」** 으로 보인다. 그러나 **칼이 동시에 두 번 움직인 적은 없다.**
* **오븐을 기다리는 동안(I/O)은 칼을 내려놓는다** — 여럿이 동시에 기다릴 수 있다.
* **식기세척기(해시·압축 같은 C 확장)는 칼 없이 돈다** — 칼을 내려놓고 기계를 돌리면 두 대가 동시에 돈다.
* **부엌을 하나 더 빌리면(프로세스)** 부엌마다 칼이 있다 — 대신 재료를 **포장해서(pickle)** 건네야 한다.
* `asyncio` 는 **요리사 한 명이 냄비 여럿을 돌려 가며** 보는 것이다 — 냄비가 **스스로 뜸 들이는 동안**(`await`)에만 다른 냄비로 간다. **계속 저어야 하는 냄비(CPU 작업)** 앞에서는 다른 냄비로 못 간다.

```text
   같은 일 두 개를 수단 넷으로 — 누가 언제 칼을 쥐었나 (시간 →)

   CPU 작업 · 스레드 둘      A ▇▇  ▇▇  ▇▇  ▇▇          둘 다 「진행 중」이다
                            B   ▇▇  ▇▇  ▇▇  ▇▇        그러나 한 칸에 한 명
   CPU 작업 · 프로세스 둘    A ▇▇▇▇▇▇▇▇                 부엌이 둘 — 정말 동시에
                            B ▇▇▇▇▇▇▇▇
   CPU 작업 · asyncio        A ▇▇▇▇▇▇▇▇                  await 가 없으니 A 가 끝나야 B
                            B         ▇▇▇▇▇▇▇▇
   I/O 작업 · 무엇으로든     A ░░░░░░░░                 기다리는 동안 칼을 내려놓는다
                            B ░░░░░░░░
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 칼 하나 | **GIL**(CPython 의 전역 인터프리터 락) | 교대 로그(동작 2) |
| 칼을 넘기는 간격 | `sys.getswitchinterval()` — 이 판 `0.005` | 간격을 `10.0` 으로 올리면 교대가 사라진다(동작 2) |
| 둘 다 「요리 중」 | 두 스레드의 **시작\~끝 구간이 겹친다** | 겹침 격자의 첫 칸(동작 1) |
| 칼이 동시에 두 번 움직였나 | **CPU 시간 합이 벽시계 구간보다 큰가** | 겹침 격자의 둘째 칸(동작 1) |
| 오븐 기다리기 | `time.sleep`·소켓·파일 I/O — **GIL 을 놓는다** | `io` 행(동작 1) |
| 식기세척기 | `hashlib` 같은 C 확장이 **GIL 을 놓고 계산** | `hash` 행(동작 3) |
| 부엌을 더 빌린다 | `multiprocessing`·`ProcessPoolExecutor` | `cpu` 행의 프로세스 칸(동작 1) |
| 재료 포장 | 프로세스로 넘기는 함수·인자의 **pickle** | 람다가 안 넘어간다(동작 6) |
| 냄비 돌려 보기 | `asyncio` — `await` 에서만 양보 | `cpu`·`hash` 행의 `asyncio` 칸이 `False`(동작 1) |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.\
「**CPU 작업을 스레드 풀로 돌렸는데 코어 하나만 바쁘다**」·
「**`hashlib`·`zlib` 은 스레드로 돌려도 코어가 여럿 바빠진다**」·
「**`ProcessPoolExecutor` 에 람다를 넘겼더니 `PicklingError`**」·
「**GIL 이 있으니 `counter += 1` 은 락이 필요 없다고 믿었다**」가 그것이다.

> **GIL(global interpreter lock, 전역 인터프리터 락)** — CPython 이 **한 번에 한 스레드만 파이썬 바이트코드를 실행**하게 하는 장치. 언어 명세가 아니라 **CPython 구현**이다.\
> 예: 스레드 둘이 순수 파이썬 루프를 돌면 구간은 겹치지만 CPU 시간 합은 벽시계를 못 넘는다(동작 1).

> **바이트코드(bytecode)** — CPython 이 소스를 컴파일해 만든 **명령 목록.** `dis` 모듈로 본다.\
> 예: `n += 1` 은 `LOAD_GLOBAL` · `LOAD_CONST` · `BINARY_OP +=` · `STORE_GLOBAL` 네 개다(동작 4).

### ★★ 이 주제가 쓰는 창 / 부적용인 창

**본체는 ① 겹침 격자다.** 작업 셋(`cpu`·`hash`·`io`) × 수단 다섯(`threading`·`ThreadPoolExecutor`·`multiprocessing`·`ProcessPoolExecutor`·`asyncio`)을 한 표로 찍고, 칸마다 **두 가지를 참/거짓으로** 묻는다 —
**두 작업의 시작\~끝 구간이 겹쳤나** · **두 작업의 CPU 시간 합이 둘을 합친 벽시계 구간의 1.5 배를 넘었나.**
★★★ **둘을 가르는 것이 이 주제의 네 번째 창이다.** 앞의 것만 보면 스레드도 「동시에 돌았다」로 읽힌다.

| 창 | 무엇을 말해 주나 | 못 보는 것 |
|---|---|---|
| ① ★★★ **겹침 격자**(구간 겹침 · CPU 시간 합 대 벽시계) | 수단마다 **진행이 겹쳤나 · 계산이 정말 동시였나** | 어느 코어에서 돌았나 |
| ② ★★★ **교대 로그**(진행 틱을 공유 리스트에 기록) | 스레드가 **어떤 순서로 번갈아** 칼을 쥐었나 · 간격을 바꾸면 무엇이 바뀌나 | 프로세스 사이(리스트를 공유하지 않는다) |
| ③ ★★★ **잃은 갱신 격자**(본문 넷 × 간격 둘 × 판 둘) | `n += 1` 이 GIL 아래에서 **잃었나** | 잃은 **개수**(흔들린다 — 안 찍었다) |
| ④ ★★ **`dis` 창** | `+=` 가 **명령 몇 개**인가 · 읽기와 쓰기 사이에 무엇이 끼나 | 전환이 **어느 명령에서** 일어나나(그건 인터프리터 소스의 영역 — 안 읽었다) |
| ⑤ ★★ **시작 방식 창**(`fork` 대 `spawn`) | 자식이 부모의 **전역 상태를 보나** · 경고 | — |
| ⑥ ★ **pickle 창** | 두 풀이 **같은 인터페이스인데 무엇이 갈리나** | — |
| ★ **제5의 상태** — 「동시에 계산했나」 | ★★ **시간 대신 CPU 시간 합으로 물었다** — 코어 사용률을 재는 도구(`top` 류)를 캡처에 넣으면 다시 던질 수 없어서, **프로세스·스레드가 스스로 잰 CPU 시간**을 벽시계 구간과 견줬다 | ★ 그 창은 **코어 몇 개가 쓰였나**는 못 본다 — 「1.5 배를 넘었나」 한 문턱뿐이다 |
| ★ **못 잰 것** — free-threaded 빌드 | 판별 블록만 실었다(동작 7) | ★★★ 이 머신에 `python3.13t`·`python3.14t` 가 **없다** — 문서 인용만 |
| ★ **못 잰 것** — `forkserver` · 3.14 의 기본값 | — | 이 캡처 환경에서 `forkserver` 는 `OSError: AF_UNIX path too long` 으로 못 떴다(임시 디렉토리 경로가 길다 — 실행 검증 참고) · 3.14 는 판이 없다 |
| ★ **부적용** — 경과 시간·배수 | — | 시간은 판정에만 썼다 — **싣지 않았다** |

## 이 주제가 답하려는 질문

1. ★★★ **GIL 은 무엇을 막고 무엇을 안 막나** — 스레드 둘이 순수 파이썬 루프를 돌면 「동시에 돈다」는 말은 어디까지 참인가. `sleep`·`hashlib` 은 왜 다른가.
2. ★★★ **GIL 이 있으면 `n += 1` 은 안전한가** — 잃나 · 안 잃는다면 그건 보장인가 · 무엇을 끼우면 잃나.
3. ★★ **작업 성격에 맞는 수단은 무엇인가** — `threading`·`multiprocessing`·`concurrent.futures`·`asyncio` 를 고르는 기준, 그리고 프로세스로 가면 치르는 것(`fork`/`spawn` · pickle · `__main__` 가드).

★ 첫째가 이 주제의 인출 목표다.
**「구간이 겹친다 ≠ 계산이 동시다 — 스레드는 앞의 것만, 프로세스와 GIL 을 놓는 C 코드는 둘 다」 한 문장으로 겹침 격자의 두 열을 설명할 수 있는 것**이 아는 것과 들은 것의 경계다.

## 동작 방식

> 이 절이 본문이다. 그림이 먼저 오고 문장이 그 그림을 읽어 준다.

### 1. ★★★ 겹침 격자 — 작업 셋 × 수단 다섯 (본체)

**언제 쓰나** — 병행 수단을 고를 때마다. 특히 「스레드 풀로 바꿨는데 왜 그대로지?」.

```text
   한 칸을 채우는 법 — 같은 작업 둘을 그 수단으로 돌리고, 각 작업이 스스로 잰다

   작업 하나가 돌려주는 것 = (시작 벽시계, 끝 벽시계, 그 작업이 쓴 CPU 시간)
                              time.time()               스레드면 thread_time()
                                                        프로세스면 process_time()

   A  |<--------------->|                 구간 겹침   = 늦게 시작한 쪽 < 먼저 끝난 쪽
   B        |<--------------->|           CPU 시간 합 > 1.5 × (첫 시작 ~ 마지막 끝)  ?
      ^ 첫 시작                 ^ 마지막 끝

   ★ 두 작업이 정말 동시에 계산하면 CPU 시간 합이 벽시계의 거의 2 배가 된다
     한 번에 하나씩이면 합이 벽시계를 못 넘는다 — 문턱 1.5 는 그 사이
   ★ 칸마다 5 판을 돌려 값이 모두 같으면 그 값, 갈리면 True/False 로 찍는다
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

그림 해설.

* ★★★ **`cpu` 행 — 스레드 두 칸은 `True;False`.** 구간은 **겹쳤다**(둘 다 「진행 중」) — 그런데 **CPU 시간 합이 벽시계의 1.5 배를 못 넘었다.** 두 스레드가 칼을 **번갈아** 쥔 것이다.
  **프로세스 두 칸은 `True;True`** — 부엌이 둘이라 **정말 동시에** 계산했다.
* ★★★ **`hash` 행 — 스레드인데 `True;True`.** 같은 스레드인데 `cpu` 행과 갈린다. `hashlib.sha256` 은 **큰 데이터를 해시하는 동안 GIL 을 놓는다**(동작 3).
  ★ **GIL 이 막는 것은 「스레드」가 아니라 「파이썬 바이트코드」다.**
* ★★ **`io` 행 — 다섯 칸 전부 겹쳤다.** `time.sleep` 은 GIL 을 놓고 기다린다. `asyncio` 도 `await asyncio.sleep` 에서 양보해 겹친다. CPU 시간 칸은 **`-`** — 잠자는 동안 CPU 를 안 쓰니 물을 것이 없다(부적용).
* ★★ **`asyncio` 는 `cpu`·`hash` 행에서 `False;False`** — 코루틴 안에 `await` 가 없으면 **하나가 끝나야 다음이 시작**한다. 구간조차 안 겹친다.
  ★ 이것이 [52번](../52-asyncio-concurrency-structure/2-summary.md)의 「블로킹 호출이 루프를 멈춘다」와 **같은 모양**이다 — 그쪽이 정본.
* ★ **마지막 두 줄** — 구간이 **모든 판에서** 겹친 칸 `13 / 15` · CPU 시간 합이 **모든 판에서** 1.5 배를 넘은 칸 `6 / 10`(`io` 다섯 칸은 부적용이라 뺐다).
  ★★ **스레드가 `cpu` 행에서 `True` 를 받은 첫 열이 함정이다** — 그 열만 보면 「스레드도 동시에 돈다」가 된다.
* ★ `ThreadPoolExecutor` 는 `threading` 과, `ProcessPoolExecutor` 는 `multiprocessing` 과 **여섯 칸 다 같다** — 풀은 **수단을 바꾸지 않고 인터페이스만** 바꾼다(동작 6).

**비용** — 이 격자는 **「이득이 있나」를 참/거짓으로만** 말한다. 프로세스를 띄우고 인자를 pickle 하는 값이 얼마인지는 **재지 않았다.** 일이 작으면 그 값이 계산보다 클 수 있다는 것은 **문서의 말도 이 문서의 측정도 아니다** — 판단은 자기 작업으로 다시 재서 하라.

> **CPU 시간(CPU time)** — 벽시계가 아니라 **그 스레드·프로세스가 실제로 CPU 를 쓴 시간.** `time.thread_time()`(그 스레드) · `time.process_time()`(그 프로세스의 모든 스레드).\
> 예: `time.sleep(0.2)` 는 벽시계로 0.2초가 가도 CPU 시간은 거의 늘지 않는다.

### 2. ★★★ 교대 로그 — 구간은 겹쳐도 칼은 한 번에 하나

**언제 쓰나** — 「스레드 둘이 겹쳤다」는 로그를 보고 「병렬로 돌았다」고 읽기 전에.

```text
   두 스레드가 1만 회마다 자기 이름을 공유 리스트에 적는다 (스레드당 300 틱)

   리스트:  A A A … A B B B … B A A … A B …      같은 글자가 이어진 덩어리 = 한 번 칼을 쥔 구간
            └─ 덩어리 1 ─┘└─ 덩어리 2 ─┘└ 3 ┘

   덩어리가 2 개뿐   -> A 가 다 끝나고 B 가 돌았다 (교대 없음)
   덩어리가 2 개 넘음 -> 번갈아 돌았다
   ★ 덩어리 안에 두 글자가 섞일 수는 없다 — 한 스레드가 칼을 쥔 동안 다른 스레드는 적지 못한다
```

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

그림 해설.

* ★★★ **기본 간격 `0.005` — 덩어리가 2 개를 넘고(`runs > 2` `True`), 첫 네 덩어리가 `ABAB`, 구간이 겹친다.** 5판 모두 같았다.
  구간이 겹친 것은 **번갈아 돌았기 때문**이지 동시에 돌았기 때문이 아니다 — 동작 1 의 `cpu;threading;True;False` 가 이 그림이다.
* ★★★ **간격을 `10.0` 으로 올리면 덩어리가 정확히 2 개(`AB`), 구간이 안 겹친다.** A 가 칼을 쥔 채 일을 다 끝낼 때까지 아무도 못 빼앗았다 — **메인 스레드가 B 를 `start()` 하는 것조차** 그 뒤였다.
  ★ 교대를 만드는 것이 **이 간격**임이 격자 한 칸으로 보인다.
* ★ 문서의 말 — *"which thread becomes scheduled at the end of the interval is the operating system's decision. The interpreter doesn't have its own scheduler."* 간격은 **「넘겨 달라고 요청하는 때」** 를 정할 뿐, 누가 받을지는 OS 다.
  ★ 이 판에서는 첫 네 덩어리가 5판 모두 `ABAB` 였다 — **관찰이다.** 스레드가 셋 이상이면 순서가 갈릴 수 있다(재지 않았다).
* ★ `0.005` 는 **CPython 의 기본값**이다 — 문서는 값의 뜻(*"ideal duration of the "timeslices""*)을 적고, 이 판의 값은 출력으로 확인했다(3.11 도 같았다).

```text
   CPU 스레드 둘 — 간격이 정하는 두 모양 (시간 →)

   간격 0.005     A ▇▇▇·····▇▇▇·····▇▇▇·····▇▇▇           구간 A: |-------------------------|
                  B ·····▇▇▇·····▇▇▇·····▇▇▇·····▇▇▇      구간 B:    |-------------------------|
                                                             ★ 겹친다 — 그러나 ▇ 는 한 줄에만

   간격 10.0      A ▇▇▇▇▇▇▇▇▇▇▇▇                          구간 A: |-----------|
                  B             ▇▇▇▇▇▇▇▇▇▇▇▇              구간 B:             |-----------|
                                                             ★ 안 겹친다 — 덩어리 2 개
```

> **전환 간격(switch interval)** — 칼을 쥔 스레드에게 **「이제 넘겨라」를 요청하는 주기.** `sys.setswitchinterval(초)` 로 바꾼다(3.2+).\
> 예: 이 판의 기본값 `0.005`. `10.0` 으로 올리면 CPU 스레드 둘이 교대 없이 차례로 돌았다.

### 3. ★★ 무엇이 GIL 을 놓나 — I/O 와 C 확장

**언제 쓰나** — 「스레드는 CPU 작업에 소용없다」를 **외우기 전에.** 그 문장은 **순수 파이썬 루프**에만 맞다.

```text
   스레드 안에서 도는 코드의 세 부류 — 동작 1 격자의 스레드 칸

   순수 파이썬 루프  x += i  ……      바이트코드를 계속 실행      GIL 을 쥔 채      cpu  ; True ; False
   hashlib.sha256(64MB)              C 코드가 바이트를 계산      GIL 을 놓고       hash ; True ; True
   time.sleep(0.2)                   OS 에게 기다리게 한다       GIL 을 놓고       io   ; True ; -

   ★ 「스레드냐 프로세스냐」가 아니라 「그 시간 동안 누가 도나」가 칸을 가른다
```

* ★★★ **문서의 말** — *"some extension modules, either standard or third-party, are designed so as to release the GIL when doing computationally intensive tasks such as compression or hashing. Also, the GIL is always released when doing I/O."*
  **`hash` 행이 그 첫 문장의 관찰이고, `io` 행이 둘째 문장의 관찰이다.**
* ★★ **「어느 C 함수가 GIL 을 놓나」는 함수마다 다르다** — 용어집은 *"designed so as to"* 라고만 적고, 조건은 그 모듈 문서에 있다.
  `hashlib` 문서 — *"To allow multithreading, the Python GIL is released while computing a hash supplied more than 2047 bytes of data at once in its constructor or update method."*
  이 문서는 64MB 를 한 번에 준 경우만 쟀다 — **2047 바이트 이하 칸은 재지 않았다**(문서대로면 놓지 않는다).
* ★ `hash` 행의 `asyncio` 칸이 `False;False` 인 것 — C 코드가 GIL 을 놓아도 **이벤트 루프는 그 호출이 끝나야 돌아온다.** 루프는 스레드가 하나다.

### 4. ★★★ GIL 이 있으면 `n += 1` 은 안전한가

**언제 쓰나** — 「GIL 이 있으니 공유 카운터에 락이 필요 없다」는 말을 들었을 때.

먼저 `+=` 가 **명령 몇 개인지** 본다.

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

* ★★★ **`n += 1` 은 명령 네 개다** — `LOAD_GLOBAL n` → `LOAD_CONST 1` → `BINARY_OP +=` → `STORE_GLOBAL n`. **읽기와 쓰기가 따로다.** GIL 은 **명령 하나**를 다른 스레드와 겹치지 않게 할 뿐, **네 개를 한 덩어리로 묶지 않는다.**
* ★ `call_between` 은 읽기(`LOAD_GLOBAL n` → `STORE_FAST t`)와 쓰기(`STORE_GLOBAL n`) 사이에 **`CALL`**(파이썬 함수 `nop` 호출)이 끼어 있다. 아래 격자에서 이것만 잃는다.

```text
   잃은 갱신 — 읽기와 쓰기 사이에서 칼이 넘어가면 (n 은 처음 5)

   스레드 A                        스레드 B
   t = n          (t = 5)
   ─── 칼이 B 에게 ───────────────
                                   t = n        (t = 5)
                                   n = t + 1    (n = 6)
   ─── 칼이 A 에게 ───────────────
   n = t + 1      (n = 6)          ★ 두 번 더했는데 6 — B 의 갱신을 A 가 덮었다

   ★ 칼이 넘어가는 자리가 읽기와 쓰기 사이에 올 수 있느냐가 전부다
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

그림 해설.

* ★★★ **`plain`(`n += 1`)과 `split`(`t = n; t += 1; n = t`)은 두 간격 × 두 판 × 10판에서 한 번도 안 잃었다.** 간격을 `1e-06` 으로 줄여도 그랬다.
  ★★★ **그런데 이건 「원자적이다」가 아니다** — **안 터진 판은 안전의 근거가 아니다.** 문서 어디에도 `+=` 가 원자라는 문장은 없다(이번에 연 용어집·`threading`·`sys` 절에서 찾지 못했다).
* ★★★ **`call_between` 은 잃었다** — 두 간격 다, 10판 중 **한 판 이상**. 읽기와 쓰기 사이에 **파이썬 함수 호출 하나**를 끼운 것뿐이다.
  ★ 몇 판이 잃었는지는 흔들린다 — 「모든 판에서 잃었나」 칸은 재캡처에서 뒤집혀 뺐다(머리말의 흔들리는 칸).
  ★ 명령 **개수**(`split` 도 읽기·쓰기가 떨어져 있다)가 아니라 **그 사이에 무엇이 끼느냐**가 갈랐다. 왜 `CALL` 에서는 전환이 일어나고 `STORE_FAST` 사이에서는 안 일어났는지는 **인터프리터 소스의 영역**이다 — 이 문서는 읽지 않았다.
* ★★ **`call_between_locked`(`with LOCK:`)는 여덟 칸 다 안 잃었다** — 읽기\~쓰기를 락이 한 덩어리로 묶었다. **이것이 보장이다**(`threading.Lock` 의 뜻).
* ★ **마지막 두 줄** — 3.12 에서 잃은 칸 **`2 / 8`** · 3.11 과 3.12 가 갈린 칸 **`0 / 8`**. 두 판의 **바이트코드는 다르다**(3.11 은 `CALL` 앞에 `PRECALL` 이 있다 — 정답 3번) — 그런데 격자는 한 칸도 안 갈렸다.
* ★★ **「실무 코드에는 `nop()` 이 없다」로 안심하지 마라** — `n` 이 **`__add__`·`__iadd__` 를 파이썬으로 정의한 객체**면 `BINARY_OP` 가 그 메서드를 부르니 읽기와 쓰기 사이에 파이썬 호출이 낀다. 그 경우는 **재지 않았다** — 「끼면 잃는다」는 `nop` 한 번으로 본 것이다.

```text
   원리 쪽 문서의 실험(§10 — 50 스레드 × 10만 회 `g_count += 1`)을 그대로 두 판에서 세 번씩

   문서의 말      「500만이 나와야 하는데 매번 다른 값이 나오는 이유는 … 컨텍스트 스위칭」
   이 머신 3.12   5,000,000 · 5,000,000 · 5,000,000
   이 머신 3.11   5,000,000 · 5,000,000 · 5,000,000

   ★ 두 판 여섯 번 다 정확했다 — 그러나 위 격자의 call_between 이 같은 GIL 아래에서 잃는다
     「안 잃었다」는 이 판·이 본문의 관찰이고, 「잃을 수 있다」는 명령이 여럿이라는 사실에서 온다
```

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

* ★★ **원리 쪽 문서([프로세스와 스레드 §10](../../../../process-thread/README.md))는 이 코드가 「매번 다른 값」을 낸다고 적는다** — 이 머신의 3.12·3.11 에서는 **세 번 다 `5,000,000`** 이었다(3.11 은 정답 3번).
  ★ 그 문서가 틀렸다는 뜻이 아니다 — **어느 판에서 잰 것인지가 문서에 없다.** 이 문서가 말할 수 있는 것은 **「이 두 판에서는 이 본문이 안 잃었다 · 같은 GIL 아래에서 읽기와 쓰기 사이에 호출이 끼면 잃었다」** 까지다.

> **잃은 갱신(lost update)** — 두 실행 흐름이 같은 값을 읽고 각자 고쳐 쓴 탓에 **한쪽의 쓰기가 덮여 사라지는 것.**\
> 예: 위 그림 — 두 번 더했는데 `6`.

> **원자적(atomic)** — 중간에 다른 흐름이 끼어들 수 없이 **한 덩어리로 끝나는** 것.\
> 예: `with LOCK:` 안의 읽기\~쓰기는 다른 스레드가 같은 락을 쥔 채 끼어들 수 없다.

### 5. ★★ 프로세스를 띄우는 두 방식 — `fork` 대 `spawn`

**언제 쓰나** — `multiprocessing`·`ProcessPoolExecutor` 를 처음 쓸 때. 특히 「내 전역 변수가 자식에서 왜 옛 값이지?」.

```text
   부모가 import 뒤에 전역을 바꾸고 자식을 띄운다

   부모   import 시  STATE = "value at import"
          main 블록  STATE = "value set in main block"    <- 여기서 자식을 띄운다

   fork   부모 프로세스를 통째로 복제    자식은 "지금의 부모"를 본다      __name__ == "__main__"
   spawn  새 인터프리터를 띄우고          자식은 "import 한 직후"를 본다   __name__ == "__mp_main__"
          부모의 주 모듈을 다시 import   (main 블록은 가드에 막혀 안 돈다)
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

그림 해설.

* ★★★ **`fork` 자식은 `'value set in main block'`, `spawn` 자식은 `'value at import'`** — `spawn` 은 주 모듈을 **`__mp_main__` 이라는 이름으로 다시 import** 한다. 그래서 `if __name__ == "__main__":` 가드 안쪽은 자식에서 **안 돈다** — 가드가 없으면 자식이 또 자식을 띄우려 한다.
  ★ 문서 — *spawn* 은 *"The parent process starts a fresh Python interpreter process"*, *fork* 는 *"The child process, when it begins, is effectively identical to the parent process."*
* ★★★ **3.12 는 다른 스레드가 도는 중에 `fork` 하면 `DeprecationWarning` 한 건, 3.11 은 0 건.** 문서 — *"If Python is able to detect that your process has multiple threads, the os.fork function that this start method calls internally will raise a DeprecationWarning."*(3.12)
* ★★ **두 판 모두 기본 시작 방식은 `fork`**(Linux). 문서(3.12) — *"The default start method will change away from fork in Python 3.14."*
  ★★★ **3.14 에서 POSIX 기본은 `spawn` 이 아니라 `forkserver`** 다 — *"On POSIX platforms the default start method was changed from fork to forkserver"*(3.14 문서). macOS·윈도는 계속 `spawn`. ★ **이 머신에 3.14 가 없다 — 문서 인용만.**
  ★ 그래서 **「리눅스에서 잘 되던 코드」가 3.14 에서 `spawn` 과 같은 모양으로 갈릴 수 있다** — `forkserver` 도 자식이 부모의 **지금 상태를 복제하지 않는다**(문서 — *"No unnecessary resources are inherited."*). `forkserver` 자체는 이 캡처 환경에서 못 띄웠다(못 잰 것).

```text
   같은 파일을 두 형태로 던진다 — 자식이 주 모듈을 다시 읽을 수 있나

   python3 e53_stdin.py        주 모듈 = 디스크의 파일     spawn 자식이 다시 import  -> 된다
   python3 - <e53_stdin.py     주 모듈 = 표준 입력         spawn 자식이 '<stdin>' 을 파일로 찾는다 -> 없다
                               fork 자식은 복제라 다시 읽을 것이 없다                             -> 된다
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

* ★★★ **표준 입력으로 던지면 `spawn` 만 죽는다** — `Process` 는 `exitcode 1`, 풀은 **`BrokenProcessPool`**(부모가 받은 예외 — 자식이 무엇 때문에 죽었는지는 안 알려 준다).
  자식의 표준 오류에는 **`'<stdin>'` 이라는 이름의 파일을 찾는 `FileNotFoundError`** 가 두 번(`Process` 하나 · 풀 일꾼 하나) 있었다. 파일로 던진 판(정답 5번)은 두 방식 다 `9` 다.
  ★ 문서 — *"Functionality within this package requires that the `__main__` module be importable by the children."*
* ★ **이 갈래가 쓰는 던지는 형태(`python3 - <<'PY'`)는 `multiprocessing` 과 맞지 않는다** — 그래서 이 편의 프로세스 탐침은 전부 트리 실험(파일)으로 던졌다.

> **시작 방식(start method)** — `multiprocessing` 이 자식 프로세스를 만드는 법. `fork`(복제) · `spawn`(새 인터프리터) · `forkserver`(미리 띄운 서버가 복제).\
> 예: `mp.get_context("spawn").Process(...)`.

### 6. ★ `concurrent.futures` — 인터페이스는 하나, 경계는 둘

**언제 쓰나** — 스레드와 프로세스를 **코드 한 줄로 갈아 끼우고** 싶을 때.

```text
   ex.submit(fn, 3).result()                        같은 두 줄

   ThreadPoolExecutor    fn 을 같은 프로세스의 다른 스레드에 넘긴다     객체를 그대로 건넨다
   ProcessPoolExecutor   fn 과 인자를 pickle 해 다른 프로세스로 보낸다   pickle 못 하면 못 건넨다
                         함수는 "모듈의 이름"으로 pickle 된다 — 람다는 이름이 <lambda>
```

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

* ★★ **스레드 풀은 람다도 `9`, 프로세스 풀은 람다에서 `PicklingError`** — *"attribute lookup <lambda> on `__main__` failed"*. 함수는 **`모듈.이름`** 으로 pickle 되고, 받는 쪽이 그 이름으로 다시 찾는다. `<lambda>` 는 찾을 이름이 없다. 3.11 도 한 글자 같았다(정답 6번).
* ★ **동작 1 의 풀 두 칸이 바로 아래 줄(`threading`·`multiprocessing`)과 여섯 칸 다 같았던 것** — 풀은 GIL 에 관해 **아무것도 바꾸지 않는다.** 바꾸는 것은 **「넘길 수 있는 것」** 이다.

### 7. ★ free-threaded 빌드 — 판별 블록 (못 잰 것)

**언제 쓰나** — 「3.13 부터 GIL 이 없어졌다」는 말을 들었을 때 — 내 인터프리터가 그 빌드인지 먼저 묻는다.

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

* ★★★ **이 머신의 두 판은 free-threaded 빌드가 아니다** — `sys.version` 에 `free-threading` 없음 · `Py_GIL_DISABLED` 는 `None` · `sys._is_gil_enabled` 는 **속성째 없다**(3.13 에 들어온 함수다) · `python3.13t`·`python3.14t` 가 PATH 에 없다. 3.11 도 같았다(정답 9번).
  ★★ **그래서 이 문서의 모든 격자는 「GIL 이 있는 빌드」의 것이다** — free-threaded 에서 동작 1 의 `cpu;threading` 칸이 어떻게 되는지는 **못 잰 것**이다.
* ★★ **문서의 말(판마다 다르다)** —
  3.13: *"This is an experimental feature and therefore is not enabled by default. The free-threaded mode requires a different executable, usually called `python3.13t`"* ·
  3.14: *"The free-threaded build of Python is now supported and no longer experimental."* · *"free-threaded Python is officially supported but still optional."*
  ★ **「실험적」은 3.13 까지의 말이다** — 3.14 는 「지원되지만 선택」이다. 둘 다 **기본 빌드는 여전히 GIL 이 있다.**
* ★ 판별의 정본 — HOWTO(3.14) — *"If the variable is set to `1`, then the build supports free threading. This is the recommended mechanism for decisions related to the build configuration."* 빌드가 지원해도 **실행 중에 GIL 이 다시 켜질 수 있어서**(`PYTHON_GIL`·`-X gil=1` · GIL 을 지원한다고 표시하지 않은 C 확장 import) **「지금 꺼져 있나」는 `sys._is_gil_enabled()`** 로 따로 묻는다.

**판 경계 — 이 주제에서 판이 바꾼 것**

| 판 | 바뀐 것 | 이 문서에서 |
|---|---|---|
| 3.2 | `concurrent.futures` · `sys.setswitchinterval` | 이 머신 3.11 · 3.12 로 확인 |
| 3.12 | `fork` + 여러 스레드 → `DeprecationWarning` | 동작 5 — 3.11 은 0 건 |
| 3.13 | free-threaded 빌드(실험) · `sys._is_gil_enabled` | ★ 못 잰 것 — 판 없음 |
| 3.14 | free-threaded 공식 지원(PEP 779) · POSIX 기본 시작 방식 `forkserver` | ★ 못 잰 것 — 문서만 |

## 문법 — 형태와 규칙

```text
   수단            부르는 모양                                             넘기는 것 / 받는 것
   threading       t = threading.Thread(target=f, args=(x,)); t.start(); t.join()       객체 그대로 · 반환값 없음
   multiprocessing p = mp.Process(target=f, args=(x,)); p.start(); p.join()            pickle · exitcode
                   ctx = mp.get_context("spawn")  — 시작 방식은 문맥으로 고른다
   futures         with ThreadPoolExecutor(n) as ex: ex.submit(f, x).result()          Future — 예외도 result() 에서
                   with ProcessPoolExecutor(n, mp_context=ctx) as ex: …                 f·x 가 pickle 돼야 한다
   asyncio         asyncio.run(main()) · await asyncio.gather(a(), b())                 52번이 정본
   락              with LOCK: …      (LOCK = threading.Lock())                           읽기~쓰기를 한 덩어리로
```

* **`multiprocessing` 을 쓰는 스크립트는 `if __name__ == "__main__":` 가드 안에서 자식을 띄운다** — `spawn`·`forkserver` 자식이 주 모듈을 다시 import 한다(동작 5).
* **프로세스로 넘기는 함수는 모듈 최상위의 `def`** — 람다·중첩 함수는 pickle 되지 않는다(동작 6).
* **시작 방식을 코드가 가정하면 문맥으로 못 박는다** — 문서(3.12) *"Code that requires fork should explicitly specify that via get_context or set_start_method."*
* **공유 카운터는 락으로** — GIL 이 있어도 읽기와 쓰기 사이는 비어 있다(동작 4).

## 어디서 틀리나

### (1) ★★★ 「스레드 둘의 구간이 겹쳤으니 병렬로 돌았다」
**구간 겹침은 교대로도 생긴다.** 동작 1 의 `cpu;threading` 은 `True;False` — 겹쳤지만 CPU 시간 합이 벽시계를 못 넘었다. 동작 2 가 그 교대(`ABAB`)를 보인다.

### (2) ★★★ 「스레드는 CPU 작업에 소용없다」를 모든 CPU 작업에
**GIL 을 놓는 C 코드는 스레드로도 동시에 돈다** — `hash;threading` 이 `True;True`. 그 문장은 **순수 파이썬 루프**에 맞는 말이다.

### (3) ★★★ 「GIL 이 있으니 `n += 1` 은 안전하다」
`+=` 는 명령 넷이고 GIL 은 **명령 하나**만 지킨다. 이 판에서 `plain` 이 안 잃은 것은 **관찰**이고, 읽기·쓰기 사이에 호출 하나가 끼면 **잃었다**(`2 / 8`). 공유 상태는 **락으로** 묶는다.

### (4) ★★ 「GIL 이 있으면 파이썬은 경쟁 조건이 없다」
**GIL 은 CPython 을 보호하지 네 코드의 불변식을 보호하지 않는다.** 용어집 — GIL 은 *"making the object model (including critical built-in types such as dict) implicitly safe against concurrent access"* — **객체 모델**이 안 깨진다는 것이지 「읽고 고쳐 쓰기」가 한 덩어리라는 뜻이 아니다.

### (5) ★★ 원리 문서의 「매번 다른 값」을 이 판에서 재현하려 한다
50 스레드 × 10만 회 `g_count += 1` 은 이 머신 3.11·3.12 에서 **여섯 번 다 정확했다.** 재현이 안 된다고 「이제 안전하다」로 뒤집지도 마라 — **판과 본문에 달린 관찰**이다.

### (6) ★★ `asyncio` 로 CPU 작업을 「동시에」 돌린다
`await` 가 없는 코루틴은 **하나가 끝나야 다음**이다 — `cpu;asyncio` 는 구간조차 `False`. 루프 안의 CPU 작업은 [52번](../52-asyncio-concurrency-structure/2-summary.md)의 블로킹 호출과 같은 모양이다.

### (7) ★★ 전역 변수를 main 블록에서 바꾸고 자식이 볼 거라 믿는다
**`fork` 만 본다.** `spawn`(그리고 3.14 기본인 `forkserver`)은 주 모듈을 다시 import 해서 **import 직후의 값**을 본다(동작 5). 넘길 값은 **인자로** 넘긴다.

### (8) ★★ 「리눅스는 `fork` 가 기본」을 영원한 사실로
3.14 에서 POSIX 기본이 **`forkserver`** 로 바뀐다(문서). ★ 「`spawn` 으로 바뀐다」도 틀린 말이다 — `spawn` 은 macOS·윈도의 기본이다.

### (9) ★ 다른 스레드가 도는 프로세스에서 `fork`
3.12 가 `DeprecationWarning` 을 낸다(동작 5). 문서 — *"Note that safely forking a multithreaded process is problematic."*

### (10) ★ `ProcessPoolExecutor` 에 람다·중첩 함수
`PicklingError`. 스레드 풀에서 되던 코드가 풀만 바꾸면 깨진다(동작 6).

### (11) ★ `python3 - <script` 로 `multiprocessing` 을 시험한다
`spawn` 자식이 `'<stdin>'` 을 파일로 찾다 죽는다 — 부모는 `exitcode 1`·`BrokenProcessPool` 만 본다(동작 5).

### (12) ★ 「3.13 부터 GIL 이 없다」
**별도 빌드**(`python3.13t`)에서 **실험적으로**, 3.14 에서는 **지원되지만 선택**이다. 기본 빌드는 GIL 이 있다 — 이 머신의 두 판도 그랬다(동작 7).

## 구현 세부사항 대 언어 보장

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **라이브러리 보장** | `threading`·`multiprocessing`·`concurrent.futures`·`sys` 문서가 정한 것 | 문서 문장을 열어서 인용 |
| **CPython 구현** | ★★★ **GIL 그 자체** · 전환 간격 기본값 · 바이트코드 · 어느 C 함수가 GIL 을 놓나 | 문서가 CPython 을 주어로 둔 문장 · 실행 |
| **이 판(3.12.3 · 3.11.15)·이 머신의 관찰** | 겹침 격자의 참/거짓 · `plain` 이 안 잃은 것 · 교대 순서 `ABAB` | 출력 |
| ★ **못 잰 것** | free-threaded 빌드 · 3.14 의 `forkserver` 기본 · 이 캡처 환경의 `forkserver` | 판이 없다 · 소켓 경로가 길다 |
| ★ **부적용** | 경과 시간·배수 | 판정에만 썼고 싣지 않았다 |

### 라이브러리 보장

| 사실 | 근거 |
|---|---|
| `spawn` 은 새 인터프리터 · `fork` 는 부모와 사실상 같은 자식 | `multiprocessing` — Contexts and start methods |
| 자식이 주 모듈을 import 할 수 있어야 한다 | 같은 문서의 note |
| 3.12 — 여러 스레드인 프로세스에서 `fork` 하면 `DeprecationWarning` | 같은 절의 `versionchanged:: 3.12` |
| 3.14 — POSIX 기본 시작 방식이 `forkserver` | 3.14 `multiprocessing` · What's New 3.14 — ★ 못 잰 것 |
| 전환 간격은 **이상적인** 시간 조각의 길이 · 누가 다음에 도는지는 OS | `sys.setswitchinterval` |
| `threading.Lock` 은 한 번에 한 스레드만 쥔다 | `threading` — Lock Objects |
| `sys._is_gil_enabled` 는 모든 파이썬 구현에 있다고 보장되지 않는다 | 3.14 `sys` — impl-detail |

★ **「`+=` 는 원자적이다」 · 「`+=` 는 원자적이지 않다」 어느 쪽도 이번에 연 문서에 없다.** 보장이 없으므로 **락이 답**이다.

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| ★★★ **GIL** — *"The mechanism used by the CPython interpreter to assure that only one thread executes Python bytecode at a time."* | 용어집 — 주어가 CPython · `threading` 의 문장은 impl-detail 상자 |
| I/O 중에는 GIL 을 놓는다 · 일부 확장(압축·해시)은 계산 중 놓는다 | 용어집 · `io`·`hash` 행(동작 1) |
| 전환 간격 기본값 `0.005` | 실행(두 판) |
| 바이트코드 — `n += 1` 이 명령 넷 · 3.11 의 `PRECALL` | `dis`(동작 4 · 정답 3번) |
| 읽기·쓰기 사이에 `CALL` 이 끼면 잃고, 안 끼면 이 판에서 안 잃었다 — **왜 그 자리인지** | ★ 실행으로 본 것까지만 — 인터프리터 소스는 읽지 않았다 |
| `spawn` 자식의 주 모듈 이름 `__mp_main__` · 표준 입력일 때 `'<stdin>'` 을 파일로 찾는 것 | 실행(동작 5) |

### 이 판(3.12.3)의 관찰

- **겹침 격자 — 구간 겹침 `13 / 15` · CPU 시간 합 문턱 `6 / 10`**(칸마다 5판이 한 값). 부하가 심한 기계에서는 프로세스 칸의 둘째 열이 뒤집힐 수 있다 — 문턱을 1.5 로 둔 까닭이다.
- **교대 로그 — 첫 네 덩어리 `ABAB`**(5판 같음). 스레드 둘일 때의 관찰이다.
- **`plain`·`split` 이 두 간격 × 두 판 × 10판에서 한 번도 안 잃은 것** · 원리 문서의 50 스레드 실험이 여섯 번 다 정확했던 것.
- **3.11 과 3.12 가 잃은 갱신 격자에서 `0 / 8`** — 바이트코드가 다른데도 그랬다.

### 그래서 이렇게 적으면 틀린다

* ✗ 「파이썬 언어는 GIL 때문에 스레드가 병렬로 못 돈다」\
  ○ **CPython 구현**이 그렇다 — 그리고 CPython 에서도 **GIL 을 놓는 C 코드**와 **I/O** 는 겹친다. free-threaded 빌드는 GIL 이 없다(문서).
* ✗ 「GIL 덕분에 `+=` 는 원자적이다」\
  ○ 명령 넷이다. 이 판에서 안 잃었을 뿐, **호출이 끼면 잃었다.**
* ✗ 「`n += 1` 을 스레드 여럿이 돌리면 매번 값이 틀린다」\
  ○ 이 머신의 3.11·3.12 에서는 **틀리지 않았다**(여섯 번 · 격자 40판). **그래도 락이 필요하다** — 두 말은 모순이 아니다.
* ✗ 「3.14 에서 리눅스 기본이 `spawn` 이 된다」\
  ○ **`forkserver`** 다(문서).
* ✗ 「프로세스 풀이 스레드 풀보다 몇 배 빠르다」\
  ○ **시간은 싣지 않았다.** 잰 것은 **CPU 시간 합이 벽시계의 1.5 배를 넘었나**다.

## 언제 쓰고 언제 안 쓰나

| 작업 성격 | 고를 것 | 근거(이 문서의 칸) |
|---|---|---|
| 순수 파이썬 계산(루프·파싱) | `ProcessPoolExecutor`(또는 `multiprocessing`) | `cpu` 행 — 프로세스만 둘째 열 `True` |
| GIL 을 놓는 C 코드(해시·압축 등 — **그 함수 문서를 확인**) | 스레드로 충분할 수 있다 | `hash;threading;True;True` — 64MB `sha256` 한 경우만 쟀다 |
| 기다림이 대부분(네트워크·파일·`sleep`) | 스레드 풀 · 또는 `asyncio` | `io` 행 — 다섯 칸 다 겹쳤다 |
| 기다림이 수천 개 · 이미 `async` 라이브러리 | `asyncio` | 동시성 구조는 [52번](../52-asyncio-concurrency-structure/2-summary.md) |
| `asyncio` 안에서 CPU·블로킹 호출을 해야 한다 | 스레드·프로세스 풀로 넘긴다 | `cpu;asyncio;False` — 넘기는 법은 52번 |
| 스레드끼리 공유 카운터·딕셔너리 갱신 | `threading.Lock` | 잃은 갱신 격자의 `call_between_locked` |
| 자식에 넘길 설정값 | **인자로** 넘긴다(전역에 기대지 않는다) | 시작 방식 창 — `spawn` 은 import 직후 값 |

## 핵심 문장

1. **구간이 겹친다 ≠ 계산이 동시다** — `cpu` 행의 스레드는 `True;False`, 프로세스는 `True;True`. 모든 판에서 겹친 칸 **13 / 15**, CPU 시간 합 문턱을 넘은 칸 **6 / 10**.
2. **GIL 은 파이썬 바이트코드를 막는다, 스레드를 막지 않는다** — `sleep` 과 `hashlib`(64MB)은 스레드로도 겹쳤다.
3. **`n += 1` 은 명령 넷이고 GIL 은 명령 하나를 지킨다** — 이 두 판에서 `plain` 은 안 잃었지만 읽기·쓰기 사이에 호출이 끼면 잃었다(**2 / 8**, 판 차이 **0 / 8**). 공유 상태는 락으로.
4. **`spawn` 자식은 주 모듈을 다시 import 한다** — main 블록에서 바꾼 전역을 못 보고, 표준 입력 스크립트에서는 아예 못 뜬다. 3.14 의 POSIX 기본은 `forkserver`(문서).
5. **GIL 은 CPython 구현이다** — free-threaded 빌드는 3.13 에서 실험, 3.14 에서 지원되지만 선택. 이 머신에는 없다(못 잰 것).

## 관련 자료

* 목록: [python/syntax 주제 목록](../README.md) — 이 주제는 **53번**
* 선행: [52-asyncio-concurrency-structure](../52-asyncio-concurrency-structure/2-summary.md) — ★★★ **경계**: `Task`·`gather`·`TaskGroup`·블로킹 호출이 루프를 멈추는 것·`to_thread` 는 그쪽이 정본. 여기는 **스레드·프로세스·`asyncio` 중 무엇을 고르나**와 **GIL 이 무엇을 막나**다.
* 선행: [51-asyncio-coroutine-basics](../51-asyncio-coroutine-basics/2-summary.md) — 코루틴·이벤트 루프 자체는 그쪽.
* 원리: [프로세스와 스레드](../../../../process-thread/README.md) — ★★ **경계**: 프로세스·스레드·컨텍스트 스위칭·경쟁 조건·상호 배제의 **원리**는 그쪽(§1\~§12). 여기는 **파이썬에서 어떤 수단을 고르나**부터. ★ 그쪽 §10 의 「매번 다른 값」은 이 머신 3.11·3.12 에서 재현되지 않았다(동작 4) · §9 의 시간 수치는 이 문서가 다시 재지 않았다.
* 연혁: [history/python — 핵심 개념의 진화](../../../../../../history/python/06-핵심-개념-진화.md) — GIL 이 왜 생겼나 · PEP 684·703 의 흐름은 그쪽(§1). 여기는 **지금 이 판에서 무엇이 보이나**. 그쪽의 성능 수치(free-threaded 의 단일 스레드 비용 등)는 이 문서가 재지 않았다.
* 다른 갈래: [Go 35 — 데이터 레이스와 `-race`](../../../go/syntax/35-data-races-and-the-race-detector/2-summary.md) — ★ 대비: Go 는 레이스를 **실행해서 검출기로** 찾는다(그쪽 핵심 문장 — 「데이터 레이스는 『순서 없이』다, 『동시에』가 아니다」). 파이썬 표준에는 그런 검출기가 없고, GIL 은 **명령 하나**를 원자로 만들 뿐이라 잃은 갱신은 **값이 틀려서야** 보인다.
* 다른 갈래: [Go 28 — 고루틴](../../../go/syntax/28-goroutines-go-statement-cost-and-termination/2-summary.md) — 고루틴의 비용과 종료는 그쪽.
* 공식 문서: [용어집 — GIL](https://docs.python.org/3.12/glossary.html#term-global-interpreter-lock) · [`threading`](https://docs.python.org/3.12/library/threading.html) · [`multiprocessing`](https://docs.python.org/3.12/library/multiprocessing.html) · [`concurrent.futures`](https://docs.python.org/3.12/library/concurrent.futures.html) · [`sys.setswitchinterval`](https://docs.python.org/3.12/library/sys.html#sys.setswitchinterval) · [free threading HOWTO](https://docs.python.org/3.14/howto/free-threading-python.html) · [PEP 703](https://peps.python.org/pep-0703/) · [PEP 779](https://peps.python.org/pep-0779/)

## 용어 풀이

* **GIL(전역 인터프리터 락)**: CPython 이 한 번에 한 스레드만 바이트코드를 실행하게 하는 장치. CPython 구현이다.\
  예: CPU 스레드 둘의 CPU 시간 합이 벽시계를 못 넘는다.
* **바이트코드**: CPython 이 실행하는 명령 목록. `dis` 로 본다.\
  예: `n += 1` 은 네 명령.
* **전환 간격(switch interval)**: 칼을 쥔 스레드에게 넘기라고 요청하는 주기(3.2+).\
  예: 기본 `0.005`, `sys.setswitchinterval(10.0)` 이면 교대가 사라졌다.
* **CPU 시간**: 스레드·프로세스가 실제로 CPU 를 쓴 시간. `time.thread_time` · `time.process_time`.\
  예: `sleep` 중에는 거의 안 는다.
* **구간 겹침**: 두 작업의 시작\~끝 벽시계 구간이 겹치는 것. **교대로도 생긴다.**\
  예: `cpu;threading` 의 첫 열 `True`.
* **잃은 갱신(lost update)**: 같은 값을 읽고 각자 고쳐 써서 한쪽 쓰기가 덮이는 것.\
  예: 두 번 더했는데 한 번만 늘었다.
* **원자적(atomic)**: 다른 흐름이 끼어들 수 없이 한 덩어리로 끝나는 것.\
  예: `with LOCK:` 안의 읽기\~쓰기.
* **시작 방식(start method)**: 자식 프로세스를 만드는 법 — `fork` · `spawn` · `forkserver`.\
  예: `mp.get_context("spawn")`.
* **`__mp_main__`**: `spawn` 자식이 부모의 주 모듈을 다시 import 할 때 붙는 이름.\
  예: 그래서 `if __name__ == "__main__":` 안쪽은 자식에서 안 돈다.
* **pickle**: 파이썬 객체를 바이트로 바꾸는 표준 직렬화. 프로세스로 넘기는 함수·인자가 거친다.\
  예: 람다는 `PicklingError`.
* **free-threaded 빌드**: GIL 을 끈 CPython 빌드(`--disable-gil` · 보통 `python3.13t`). 3.13 실험, 3.14 지원되지만 선택.\
  예: `sysconfig.get_config_var("Py_GIL_DISABLED")` 가 `1`.
* **`BrokenProcessPool`**: 풀의 일꾼 프로세스가 갑자기 죽었을 때 부모가 받는 예외.\
  예: 표준 입력 스크립트에서 `spawn` 풀.

## 더 들어가면

* ★ **free-threaded 빌드를 설치하게 되면 다시 돌릴 것** — 동작 1 의 겹침 격자와 동작 4 의 잃은 갱신 격자. 문서대로면 `cpu;threading` 의 둘째 열이 `True` 가 될 것이고, `plain` 이 잃기 시작할 **수도** 있다 — ★ **예측이지 측정이 아니다.**
* ★ **3.14 를 설치하게 되면 다시 돌릴 것** — 동작 5 의 시작 방식 창. 기본이 `forkserver` 가 되면 **아무 문맥도 안 준** `Process` 가 `spawn` 칸과 같은 값(`'value at import'`)을 낼 것이다 — 문서의 *"No unnecessary resources are inherited"* 에서 온 예측이다.
* ★ **왜 `CALL` 에서는 잃고 `STORE_FAST` 사이에서는 안 잃나** — CPython 인터프리터가 **전환 요청을 확인하는 자리**의 문제다. 이 문서는 소스를 읽지 않았다 — 판이 바뀌면 그 자리도 바뀔 수 있으므로 **이 관찰 위에 설계를 세우지 마라.**
* ★ **서브인터프리터(PEP 684 · 3.14 의 `concurrent.interpreters`)** — 인터프리터마다 GIL 을 두는 길이다. 이 머신에 3.14 가 없어 재지 않았다. 연혁은 [history/python §1.4](../../../../../../history/python/06-핵심-개념-진화.md).
