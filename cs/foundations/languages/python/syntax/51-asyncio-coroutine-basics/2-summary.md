# python/syntax/51-asyncio-coroutine-basics — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만(문서 원본 `.rst` 를 받아 문장을 찾았다).
> - [데이터 모델 — Coroutines](https://docs.python.org/3.12/reference/datamodel.html#coroutines) — *"A coroutine's execution can be controlled by calling `__await__()` and iterating over the result. When the coroutine has finished executing and returns, the iterator raises `StopIteration`, and the exception's `value` attribute holds the return value."* ·
>   *"However, unlike generators, coroutines do not directly support iteration."* · *"It is a `RuntimeError` to await on a coroutine more than once."*(3.5.2) ·
>   `coroutine.send` — *"Starts or resumes execution of the coroutine. If value is `None`, this is equivalent to advancing the iterator returned by `__await__()`."* ·
>   `coroutine.close` — *"Coroutine objects are automatically closed using the above process when they are about to be destroyed."* ·
>   `__await__` 의 note — *"The language doesn't place any restriction on the type or value of the objects yielded by the iterator returned by `__await__`, as this is specific to the implementation of the asynchronous execution framework (e.g. `asyncio`)"*
> - [식 — Await expression](https://docs.python.org/3.12/reference/expressions.html#await) — *"Suspend the execution of coroutine on an awaitable object. Can only be used inside a coroutine function."*
> - [Coroutines and Tasks](https://docs.python.org/3.12/library/asyncio-task.html#coroutines) — *"Note that simply calling a coroutine will not schedule it to be executed"*
> - [`asyncio.run`](https://docs.python.org/3.12/library/asyncio-runner.html#asyncio.run) — *"This function cannot be called when another asyncio event loop is running in the same thread."* · *"otherwise `asyncio.new_event_loop()` is used. The loop is closed at the end."* · *"should ideally only be called once"*
> - [Developing with asyncio — Detect never-awaited coroutines](https://docs.python.org/3.12/library/asyncio-dev.html#detect-never-awaited-coroutines) — *"When a coroutine function is called, but not awaited … asyncio will emit a `RuntimeWarning`"* ★ **이 문장의 주어는 실행과 어긋난다** — 동작 1 은 `asyncio` 를 **가져오지도 않았는데** 경고가 났다(「구현 세부사항 대 언어 보장」).
> - [용어집 — coroutine function](https://docs.python.org/3.12/glossary.html#term-coroutine-function) — *"A function which returns a coroutine object."*
>
> **실행 검증** — 이 문서에 실린 출력은 전부 이 머신(Linux)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.\
> 판은 `python3` **3.12.3** 이 본판이고, 판 격자 한 블록(동작 11)에서 `python3.11` **3.11.15** 를 함께 던졌다. 교차 갈래 대비로 `node` **v18.19.1** 두 블록.\
> ★★ **표준 출력과 표준 오류를 한 블록에 섞지 않았다** — 「never awaited」 경고는 **표준 오류**라, 같은 파일을 `2>/dev/null`(출력만)과 `2>&1 >/dev/null`(오류만) **두 번 던져 두 블록**으로 실었다. 나머지는 `warnings.catch_warnings(record=True)` 로 받아 **표준 출력**에 찍었다.\
> ★ **스택이 `asyncio` 를 지나는 예외는 트레이스백을 싣지 않았다**(절대 경로가 박힌다) — **예외 타입 + 메시지**만 찍었다.\
> ★★★ **이 문서는 시간을 한 번도 재지 않았다** — `asyncio.sleep(0)` 은 「한 번 양보」로만 썼다.\
> **버전** — `async def`/`await` **3.5**(PEP 492) · 비동기 제너레이터 **3.6**(PEP 525) · `asyncio.run` **3.7** · 「두 번 `await` 하면 `RuntimeError`」 **3.5.2**. 이 문서의 탐침 여덟 줄은 3.11 과 3.12 에서 **한 칸도 안 갈렸다**(`0 / 8`).\
> ★ **구현 대 언어 보장 한 줄** — 「부르면 코루틴 객체만 돌려준다 · `send` 가 돌린다 · 끝나면 `StopIteration.value`」는 **언어 레퍼런스**, 「`asyncio.run` 은 새 루프를 만들고 닫는다 · 도는 루프 안에서는 못 부른다」는 **`asyncio` 문서**, 「never awaited 경고 · 그 경고가 **나오는 시점** · 예외 문구」는 **CPython** 이다.\
> ★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다 | 안 흔들린다(근거로 써도 되는 칸) |
> |---|---|
> | 판이 오르면 예외 **문구**와 경고 **문구**(CPython 의 것) | 예외 **타입** · `(exit N)` · 로그 줄의 **순서와 개수** · `inspect.getcoroutinestate` 의 상태 이름 |
> | — (주소·시간을 한 곳도 안 찍었다 — `repr(코루틴)` 에는 주소가 들어가서 `type(c).__name__` 으로 찍었다) | ★★ 경고가 **몇 번째 줄에서** 기록됐나(`line 18` 등 — 소스 줄 번호) · 판 격자 마지막 줄 **「0 / 8」** |
>
> **선행** — [17-generators-yield](../17-generators-yield/2-summary.md)(★★★ **「호출해도 몸통이 안 돈다」·`send`·`StopIteration.value` 는 그쪽이 정본** — 코루틴은 그 기계를 물려받았다) ·
> [16-iterator-protocol](../16-iterator-protocol/2-summary.md)(`next`·`StopIteration` — 코루틴은 **이터레이터가 아니다**, 동작 4).

## 한눈에 — 쉽게 말하면

**코루틴 함수를 부르는 것은 「주문서를 쓰는 것」이다.** 주문서를 써도 **부엌에서는 아무 일도 안 일어난다.**

* `async def f` — **메뉴판의 요리 이름.** 부르면(`f()`) 요리가 아니라 **주문서 한 장**(코루틴 객체)이 나온다.
* ★★★ **주문서는 쓰기만 하면 불이 안 켜진다** — 몸통의 첫 줄도 안 돈다. 주문서를 **주방에 넣어야**(`await` · `asyncio.run`) 요리가 시작된다.
* ★★ **안 넣은 주문서를 버리면 지배인이 한마디 한다** — `RuntimeWarning: coroutine 'f' was never awaited`. 버리는 **그 순간**에 말한다(쓴 순간이 아니다).
* `await` — **「오븐 기다려요」 팻말.** 요리사가 그 자리에서 손을 멈추고 **주방장에게 돌아간다.** 오븐이 끝나면 **멈춘 그 줄부터** 잇는다.
* 이벤트 루프 — **주방장.** 팻말을 받아 두었다가 「다시 해」(`send`)를 불러 준다. `asyncio.run` 은 **주방을 새로 열고, 요리 하나를 끝까지 시키고, 문을 닫는다.**
* ★ **JS 의 `async` 함수는 다르다** — 주문서를 쓰는 **손님이 첫 팻말까지는 직접 요리해 버린다.**

```text
   f() 를 부른 순간 — 두 언어

   Python    f()  ──▶  주문서(coroutine) 한 장        본문 0 줄 · 넣지 않고 버리면 경고(표준 오류)
   JS        f()  ──▶  첫 await 까지 지금 요리 ──▶ 번호표(Promise)   본문이 이미 돌았다 · 던지면 미처리 거부
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 메뉴판의 요리 이름 | **코루틴 함수**(`async def`) | `inspect.iscoroutinefunction(f)`(동작 4) |
| 주문서 한 장 | **코루틴 객체** | `type(f()).__name__` 은 `coroutine`(동작 4) |
| 쓰기만 하면 불이 안 켜진다 | 호출은 **본문을 안 돌린다** | 표준 출력 0 줄(동작 1) |
| 버린 주문서에 지배인이 한마디 | **never awaited** `RuntimeWarning` | 표준 오류 · 기록된 줄 번호(동작 1·2) |
| 「오븐 기다려요」 팻말 | `await` 가 **바깥으로 내보내는 값**(`yield`) | 손으로 `send` 하면 팻말이 돌아온다(동작 5) |
| 「다시 해」 | `coroutine.send(값)` | 멈춘 줄부터 잇는다(동작 5) |
| 주방장 | **이벤트 루프** | 루프 없이 `sleep(0.01)` 은 `RuntimeError`(동작 6) |
| 주방을 열고 닫기 | `asyncio.run` | 두 번 부르면 **다른 루프**, 끝나면 닫힘(동작 7) |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.\
「**`send_email(user)` 을 불렀는데 메일이 안 갔다 · 에러도 없다**」(앞에 `await` 가 빠졌다)·
「**Jupyter·웹 프레임워크 핸들러 안에서 `asyncio.run` 을 불렀더니 `RuntimeError`**」(이미 루프가 돌고 있다)·
「**JS 에서 옮겨 온 코드가 `f()` 만 부르고 `await` 를 안 했는데 파이썬에서는 아무 일도 안 일어난다**」가 그것이다.\
첫째와 셋째는 **호출이 본문을 안 돌린다**는 것이고, 둘째는 `asyncio.run` 이 「**주방을 새로 연다**」는 것이다.

> **코루틴 함수(coroutine function)** — `async def` 로 정의한 함수. 부르면 **코루틴 객체**를 돌려준다(용어집 — *"A function which returns a coroutine object."*).\
> 예: `async def f(): ...` 의 `f`.

> **코루틴(coroutine)** — 코루틴 함수를 불러 얻은 객체. **`send` 로 한 걸음씩 돌릴 수 있고**, `await` 자리에서 멈췄다가 이어 간다.\
> 예: `c = f()` 의 `c` — 이 시점에 `f` 의 몸통은 한 줄도 안 돌았다.

### ★★ 이 주제가 쓰는 창 / 부적용인 창

**본체는 ① 로그 창(「몸통이 돌았나」를 표준 출력 줄로)과 ② 경고 창(never awaited — 표준 오류 · `catch_warnings`) 두 짝이다.**
★★★ **네 번째 창은 ④ `send` 창이다** — 루프 없이 **손으로 한 걸음씩** 돌려, `await` 가 **무엇을 바깥으로 내보내는지**를 본다. 로그 창만으로는 「멈췄다」와 「안 돌았다」가 같은 모양(줄 없음)이다.

| 창 | 무엇을 말해 주나 | 못 보는 것 |
|---|---|---|
| ① ★★★ **로그 창**(표준 출력 줄) | 몸통이 **돌았나 · 어느 순서로** | 멈췄나 / 시작도 안 했나(둘 다 줄이 없다) |
| ② ★★★ **경고 창**(표준 오류 블록 · `catch_warnings(record=True)`) | 돌지 않은 코루틴이 **버려졌나 · 어느 줄에서** | 버려지지 않고 **살아 있는** 안 돈 코루틴 |
| ③ ★★ **상태 창**(`inspect.getcoroutinestate`) | `CORO_CREATED`·`SUSPENDED`·`CLOSED` | — |
| ④ ★★★ **`send` 창**(루프 없이 손으로) | `await` 가 **바깥으로 낸 값** · `StopIteration.value` | 실제 루프가 그 값을 **어떻게 쓰나**(그건 `asyncio` 의 구현) |
| ⑤ ★ **판 격자**(3.11 대 3.12) | 여덟 탐침이 판에 따라 **갈리나** | 3.13 이후 |
| ⑥ ★★ **교차 갈래 창**(node 두 블록) | 같은 모양의 **JS** 는 부른 순간 무엇을 하나 | — |
| ★ **제5의 상태** — 「몸통이 안 돌았다」 | 같은 질문을 로그 대신 **상태 창**으로 물었다 — `getcoroutinestate(c)` 가 `CORO_CREATED`(동작 4) | 상태 창은 **왜** 안 돌았는지(버려질 운명인지)를 못 본다 — 그건 ② 가 본다 |
| ★ **부적용** — 시간 · 스레드 | — | 한 번도 재지 않았다 · 이 주제는 **스레드 하나**다(동시성 구조는 [52번](../52-asyncio-concurrency-structure/2-summary.md), 스레드는 [53번](../53-gil-and-choosing-concurrency/2-summary.md)) |
| ★ **못 잰 것** — 3.13·3.14 의 같은 탐침 | — | 이 머신에 없다 |
| ★ **안 실은 것** — 디버그 모드의 「Coroutine created at」 트레이스백 · `tracemalloc` 의 할당 위치 | — | 둘 다 **절대 경로가 박힌다** — 문서가 적은 모양(`asyncio-dev`)만 인용 |

## 이 주제가 답하려는 질문

1. ★★★ **코루틴 함수를 부르면 무엇이 일어나나** — 몸통은 도나, 무엇을 돌려받나, 그것을 **안 기다리고 버리면** 무엇이 어디로(표준 출력 / 오류) 언제 나오나. 같은 모양의 JS 는?
2. ★★★ **코루틴은 무엇으로 돌아가나** — `send(None)` 한 번이 무엇을 하고, `await` 는 **무엇을 바깥으로 내보내며**, 끝나면 반환값이 어디에 실리나. 이벤트 루프가 하는 일은 그중 어디인가.
3. ★★ **`asyncio.run` 은 루프를 어떻게 다루나** — 두 번 부르면 · 도는 루프 안에서 부르면 · 넘긴 코루틴은 어떻게 되나. `await` 는 어디에, 무엇 앞에 쓸 수 있나.

★ 첫째가 이 주제의 인출 목표다.
**「호출은 주문서만 쓴다 · `send` 가 돌린다 · `await` 는 바깥으로 팻말을 내민다 · 루프는 `send` 를 불러 주는 쪽이다」 네 문장으로 동작 1·5·6 의 출력을 설명할 수 있는 것**이 아는 것과 들은 것의 경계다.

## 동작 방식

> 이 절이 본문이다. 그림이 먼저 오고 문장이 그 그림을 읽어 준다.

### 1. ★★★ 부르기만 하면 — 몸통이 찍는 줄 0, 표준 오류 두 줄

**언제 쓰나** — `await` 를 빠뜨린 줄을 찾을 때마다. 「에러는 없는데 일이 안 됐다」의 첫 용의자다.

```text
   같은 파일을 두 번 던진다 — 한 번은 표준 출력만, 한 번은 표준 오류만

   python3 - <e51_call.py 2>/dev/null        ← 표준 출력 : "in f" 가 찍혔나?
   python3 - <e51_call.py 2>&1 >/dev/null    ← 표준 오류 : 무엇이 나왔나?

   ★ 한 블록에 섞으면 받는 방식(터미널 / 파이프)에 따라 순서가 뒤집힌다 — 그래서 가른다
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

그림 해설.

* ★★★ **표준 출력에 `in f` 가 없다** — `before f()`·`after f()` 두 줄뿐이다. **몸통은 한 줄도 안 돌았다.** 문서 — *"Note that simply calling a coroutine will not schedule it to be executed"*.
* ★★★ **표준 오류에 `RuntimeWarning: coroutine 'f' was never awaited`** — 줄 번호 `<stdin>:7` 은 `f()` 를 부른 줄이다. 둘째 줄 `Enable tracemalloc …` 은 「어디서 만들었는지 알고 싶으면 `tracemalloc` 을 켜라」는 안내다.
* ★★ **종료 코드는 `0`** — 경고는 **실패가 아니다.** CI 가 종료 코드만 보면 이 줄은 **아무도 안 읽는다.**
* ★★ **이 파일은 `asyncio` 를 가져오지 않았다** — 그런데도 경고가 났다. 경고를 내는 것은 `asyncio` 가 아니라 **인터프리터**다(「구현 세부사항 대 언어 보장」).

★★★ **경고를 에러로 바꿔도 멈추지 않는다** — `-W error::RuntimeWarning` 을 주고 같은 파일을 던졌다.

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

* ★★★ **`after f()` 가 여전히 찍히고 `exit 0`** — 경고는 **예외로 바뀌긴 했지만** 코루틴이 **사라지는 자리**(소멸 과정)에서 났으므로 호출자에게 던져지지 못하고 **`Exception ignored in` 한 덩어리**로 표준 오류에 버려졌다(그 덩어리는 주소·설치 경로가 박혀 줄 수만 셌다).
  ★ 그래서 `-W error` 는 이 실수를 **실패로 만들어 주지 않는다** — 표준 오류를 읽는 쪽이 있어야 한다.

**비용** — 경고는 **표준 오류에 한 번** 나고 끝이다. 로그를 표준 출력만 모으는 배포 환경에서는 **흔적이 전혀 없다.**

> **never awaited 경고** — 한 번도 시작되지 않은 코루틴이 **사라질 때** CPython 이 내는 `RuntimeWarning`.\
> 예: `f()` 만 쓰고 결과를 버리면 `coroutine 'f' was never awaited`.

### 2. ★★★ 경고는 언제 나오나 — 만들 때가 아니라 사라질 때

**언제 쓰나** — 경고의 줄 번호를 보고 **어디를 고칠지** 정할 때. 그 줄이 「부른 줄」이 아닐 수 있다.

```text
   코루틴 하나가 사라지는 길 셋

   c = f(); del c ...        마지막 이름이 사라지는 순간     ← 참조 계수가 0
   f()                       문장이 끝나는 순간(아무도 안 받았다)
   [f()] 가 자기 자신을 품음   del 로는 안 사라진다 → gc.collect() 가 치울 때

   ★ 경고의 줄 번호 = 사라진 자리의 줄
```

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

그림 해설.

* ★★★ **`c = f()`(13행) 뒤에는 `0`, `del c` 뒤에도 `0`** — `x` 가 아직 같은 객체를 붙들고 있다. **`del x`(18행)에서 `1`** — 마지막 이름이 사라진 순간이다. 경고의 `line 18` 은 **만든 줄(13)이 아니라 사라진 줄**이다.
* ★★ **`f()` 문장(21행)은 그 자리에서 `2`** — 받은 이름이 없으니 문장이 끝나며 바로 사라진다.
* ★★★ **자기 자신을 품은 리스트는 `del box` 로 안 사라진다**(`[5]` 가 여전히 `2`) — **`gc.collect()`(28행)에서야 `3`.** 경고가 **엉뚱한 줄**(순환 수집이 돈 자리)에서 나오는 경우다.
* ★★ **`c.close()` 로 닫은 뒤 버리면 경고가 없다**(`[7]` 이 `3` 그대로) — 문서 `close` — *"the coroutine is marked as having finished executing, even if it was never started."* 경고는 「시작도 안 하고 끝나지도 않은」 코루틴만 대상이다.

**비용** — 코루틴을 **리스트·딕셔너리·객체 속성에 담아 두면** 경고는 그 컨테이너가 사라질 때까지 **미뤄진다.** 순환에 걸리면 **순환 수집이 도는 시점**까지 — 그 줄 번호는 원인과 무관하다.

> **참조 계수(reference count)** — 한 객체를 가리키는 이름·칸의 수. CPython 은 이것이 0 이 되는 **순간** 객체를 치운다.\
> 예: `x = c; del c` 는 계수를 2 → 1 로, `del x` 가 1 → 0 으로 만든다.

### 3. ★★★ JS 와 한 쌍 — 몸통이 `await` 전에 던지면

**언제 쓰나** — JS 에서 온 사람이 「부르고 안 기다린 함수는 **돌기는 돈다**」를 파이썬에 기대할 때 · 반대 방향.
★ 「부른 순간 몸통이 도나」 자체는 **[JS 39번 동작 (9)](../../../js/syntax/39-async-await/2-summary.md)가 이미 쟀다**(파이썬 `caller: before f() > caller: after f() -- got coroutine` 대 JS `caller: before f() > f: line 1 > caller: after f() -- got Promise`). 여기서는 한 걸음 더 — **몸통이 `await` 전에 던지면 누가 무엇을 보고하나.**

```text
   같은 모양 — 몸통 첫 줄이 찍고, 둘째 줄이 던진다(await 없음). 호출자는 부르기만 한다

   Python    f() ──▶ 주문서       몸통 0 줄 → 던질 일도 없다 → 버리는 순간 never awaited(표준 오류)
   JS        f() ──▶ 몸통이 돈다 ──▶ throw ──▶ 거부된 Promise ──▶ 아무도 안 받았다 → 미처리 거부
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

그림 해설.

* ★★★ **파이썬은 `f: line 1` 이 없다** — 몸통이 안 돌았으니 `ValueError("boom")` 은 **만들어지지도 않았다.** 남는 것은 `del c`(10행)에서 난 **never awaited 경고 한 줄**(표준 오류)과 `exit 0`.
* ★★★ **JS 는 `f: line 1` 이 `caller: after f()` 앞에 찍힌다** — 첫 `await` 까지(이 함수는 `await` 가 없으니 끝까지) **지금** 돈다. 던진 것은 **거부된 `Promise`** 가 되고, 아무도 안 받았으니 **미처리 거부**다.
* ★★ **node 는 기본으로 그 거부에 죽는다** — 훅이 없으면 **`exit 1`**(표준 오류의 스택은 경로가 박혀 `2>/dev/null` 로 버렸다). 훅이 있으면 `unhandledRejection(boom)` 이 표준 출력에 찍히고 `exit 0`. 미처리 거부가 **언제** 보고되는지는 [JS 37번 동작 (5)](../../../js/syntax/37-promise-state-model/2-summary.md)가 정본이다.
* ★★ **두 언어의 「보고」는 뜻이 다르다** — JS 는 「**돌았는데** 실패를 아무도 안 받았다」, 파이썬은 「**돌지도 않았다**」. 파이썬 쪽에는 **실패가 아예 없다.**

**비용** — 파이썬에서 `await` 를 빠뜨린 코드는 **예외 경로까지 통째로 안 돈다** — `try/except` 로 감싸 둔 로깅도 안 찍힌다. JS 에서는 반대로 **이미 일을 했고**(부작용이 났고) 실패만 떠돈다.

> **미처리 거부(unhandled rejection)** — JS 에서 거부된 `Promise` 에 아무도 처리기를 달지 않은 것. node 는 v15 부터 기본으로 프로세스를 끝낸다([JS 37번](../../../js/syntax/37-promise-state-model/2-summary.md)).\
> 예: 위 `node e51_pair.js` 가 `exit 1`.

### 4. ★★ 코루틴 객체의 정체 — 제너레이터의 친척, 그러나 이터레이터는 아니다

**언제 쓰나** — 「코루틴은 제너레이터다」라는 말을 들었을 때 · 라이브러리가 **코루틴인지 검사**할 때.

```text
   제너레이터(17번)                           코루틴
   ─────────────────                        ─────────────────
   def g(): yield 1                          async def f(): return 42
   g()  → generator                          f()  → coroutine            ← 둘 다 「부르면 몸통 0 줄」
   send · throw · close  있음                  send · throw · close  있음   ← 같은 조종 손잡이
   __next__ 있음 · for 로 돈다                 __next__ 없음 · for 로 못 돈다  ← ★ 여기서 갈린다
                                             __await__ 있음 → await 뒤에 올 수 있다
```

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

그림 해설.

* ★★ **`type(c).__name__` 은 `coroutine`**, `types.CoroutineType` 이고 **`GeneratorType` 과 다른 타입**이다. `inspect.isgenerator(c)` 도 `False`.
* ★★ **`send`·`throw`·`close` 는 있다** — 문서 — *"Coroutines also have the methods listed below, which are analogous to those of generators"*. [17번](../17-generators-yield/2-summary.md)의 조종 손잡이를 그대로 물려받았다.
* ★★★ **`__next__` 가 없다** — `next(c)` 는 `'coroutine' object is not an iterator`, `iter(c)`·`list(c)` 는 `'coroutine' object is not iterable`. 문서 — *"unlike generators, coroutines do not directly support iteration."*
* ★ **`getcoroutinestate(c)` 가 `CORO_CREATED`** — 동작 1 의 「몸통이 안 돌았다」를 **로그 없이** 물은 창이다(제5의 상태). `close()` 뒤에는 `CORO_CLOSED`.
* ★ **`c.__await__()` 는 `coroutine_wrapper`** — `await` 가 실제로 붙잡는 이터레이터다. 그 이름은 CPython 의 것이다.

★ [history 06번 §5.5](../../../../../../history/python/06-핵심-개념-진화.md)는 *「내부적으로 코루틴은 여전히 특수한 제너레이터이며」* 라고 적는다 — **이 판의 타입으로는 별개**(`CoroutineType is GeneratorType` 이 `False`)이고, 닮은 것은 **조종 손잡이와 멈춤·재개 기계**다. 그 문장은 **구현의 계보**로 읽어라.

### 5. ★★★ `send(None)` 으로 손으로 돌리기 — 루프 없이

**언제 쓰나** — 「`await` 는 무엇을 하나」를 루프라는 상자 없이 볼 때. 이 주제의 **네 번째 창**이다.

```text
   Pause("p1") 의 __await__ 는 yield 를 한 번 한다 — 그 값이 바깥으로 나간다

   바깥(나)                       코루틴 g
   ─────────                     ──────────────────────────────
   c.send(None)   ──────▶        g: start
                                 a = await Pause("p1")  ─ yield "p1" ─▶ 여기서 멈춤
                  ◀── "p1" ────
   c.send(10)     ──────▶        a = 10 (보낸 값이 await 의 값) · g: resumed with 10
                                 b = await Pause("p2")  ─ yield "p2" ─▶ 멈춤
                  ◀── "p2" ────
   c.send(20)     ──────▶        b = 20 · return (a, b)
                  ◀── StopIteration(value=(10, 20))
```

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

그림 해설.

* ★★★ **`send(None)` 한 번이 `g: start` 를 찍고 `'p1'` 을 돌려받는다** — `await` 는 `Pause.__await__` 의 **`yield` 를 통과해 바깥까지** 팻말을 내민다. 상태는 `CORO_SUSPENDED`.
* ★★★ **`send(10)` 의 `10` 이 `await` 식의 값이 된다**(`g: resumed with 10`). 끝나면 **`StopIteration` 의 `value` 에 반환값 `(10, 20)`** — [17번](../17-generators-yield/2-summary.md)의 「`return` 은 값을 내보내지 않는다, `StopIteration.value` 에 실릴 뿐」과 **같은 기계**다.
* ★★ **끝난 코루틴을 또 `send` 하면 `RuntimeError | cannot reuse already awaited coroutine`**(`[2]`) — 제너레이터는 조용히 `StopIteration` 인데(17번), 코루틴은 **예외**다. 문서 — *"It is a `RuntimeError` to await on a coroutine more than once."*
* ★ **첫 호출에 `None` 아닌 값은 `TypeError | can't send non-None value to a just-started coroutine`**(`[3]`) — 17번의 제너레이터 문구에서 **낱말 하나**(`generator` → `coroutine`)만 다르다.
* ★★★ **`[4]` — `outer` 에 `send` 하면 팻말은 맨 안쪽 `inner` 의 `Pause` 에서 온다**(`'from-inner'`). `await inner()` 는 **[17번의 `yield from`](../17-generators-yield/2-summary.md) 처럼 통로**가 된다 — 보낸 `5` 가 `inner` 까지 내려가 `6` 이 되고, `outer` 가 `12` 를 돌려준다.
* ★★ **`[5]` 의 `run_by_hand` 가 가장 작은 「루프」다** — `StopIteration` 이 날 때까지 `send(None)` 을 부른다. 팻말 **두 번**을 받고 끝났다.

**비용** — 이 손 드라이버는 팻말을 **무시**한다(`None` 만 되돌려 보낸다). 진짜 루프는 팻말(대개 `Future`)을 보고 **「언제 다시 부를지」** 를 정한다 — 그게 동작 6 이다.

> **`send(value)`** — 멈춘 코루틴을 이어 돌리며 `value` 를 **`await` 식의 값**으로 넣는 메서드. 처음에는 `None` 만 된다.\
> 예: `c.send(None)` 이 첫 `await` 까지 돌리고, 거기서 내민 값을 돌려준다.

### 6. ★★ 루프 없이 `asyncio.sleep` 을 돌리면 — 루프가 하는 일

**언제 쓰나** — 「이벤트 루프는 무엇을 하나」를 한 줄로 말해야 할 때.

```text
   sleep(0)      ─ send(None) ─▶  None 을 한 번 내민다(「한 번 양보」) ─ send ─▶ StopIteration
   sleep(0.01)   ─ send(None) ─▶  get_running_loop() ── 도는 루프가 없다 ──▶ RuntimeError
                                  ★ 「0.01 뒤에 깨워 줄 쪽」이 필요하다 = 루프
```

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

그림 해설.

* ★★ **`sleep(0)` 은 루프 없이도 끝까지 돈다** — 팻말 `None` 을 **한 번** 내밀고 끝(`yielded ['None']`). 「한 번 양보」는 **팻말 하나**일 뿐, 누가 받든 상관없다. ★ 이 판의 소스로는 **맨 `yield` 하나**다(「더 들어가면」).
* ★★★ **`sleep(0.01)` 은 첫 `send` 에서 `RuntimeError | no running event loop`** — 「0.01 뒤에 다시 불러 줄 쪽」을 찾다가 없다. **루프가 하는 일은 팻말을 받아 두었다가 알맞은 때에 `send` 를 불러 주는 것**이다.
* ★ 문서의 note 가 그 경계를 적는다 — *"The language doesn't place any restriction on the type or value of the objects yielded by the iterator returned by `__await__`, as this is specific to the implementation of the asynchronous execution framework (e.g. `asyncio`)"*. **팻말의 모양은 언어가 아니라 `asyncio` 의 약속**이다.

> **이벤트 루프(event loop)** — 멈춘 코루틴들이 내민 팻말을 받아 두었다가, 기다리던 일이 끝나면 그 코루틴을 이어 돌려 주는 반복.\
> 예: `asyncio.run` 이 하나를 만들어 쓰고 닫는다(동작 7).

### 7. ★★★ `asyncio.run` — 주방을 열고, 하나를 끝까지 시키고, 닫는다

**언제 쓰나** — 프로그램의 **입구**에서. 문서 — *"should ideally only be called once"*.

```text
   asyncio.run(main("a"))                         asyncio.run(main("b"))
   ─────────────────────────                     ─────────────────────────
   새 루프 L1 을 만든다                              새 루프 L2 를 만든다       ← L1 is L2 → False
   main 을 끝까지 돌린다 (running=True)              main 을 끝까지 돌린다
   반환값 "A" 를 돌려준다 · 예외면 그대로 던진다        "B"
   L1 을 닫는다 (closed=True)                       L2 를 닫는다
```

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

그림 해설.

* ★★★ **두 번 부르면 루프가 다른 객체다**(`[3]` `False`) · **끝나면 둘 다 닫혔다**(`[4]` `[True, True]`). 문서 — *"otherwise `asyncio.new_event_loop()` is used. The loop is closed at the end."* 루프는 **`asyncio.run` 한 번의 수명**이다.
* ★★ **반환값이 그대로 나온다**(`[1] result: A`) · **예외도 그대로 나온다**(`[6] ValueError | from main`).
* ★★ **루프 밖에서 `get_running_loop()` 는 `RuntimeError | no running event loop`**(`[5]`) — 동작 6 의 `sleep(0.01)` 이 부딪힌 그 벽이다.
* ★ **코루틴이 아닌 것을 주면 `ValueError | a coroutine was expected, got 42`**(`[7]`).

**비용** — 루프가 매번 새로 생기므로, **루프에 묶인 객체**(루프 안에서 만든 `Future`·연결 풀 등)를 `asyncio.run` 두 번에 걸쳐 쓰면 **다른 루프의 것**이 된다 — 이 문서는 그 실패를 재지 않았다.

### 8. ★★ 도는 루프 안에서 `asyncio.run` — `RuntimeError`, 넘긴 코루틴은 never awaited

**언제 쓰나** — 이미 루프가 도는 곳(Jupyter 셀·비동기 웹 핸들러) 안에서 「동기 함수처럼」 코루틴을 돌리고 싶을 때.

```text
   asyncio.run(main())                   ← 루프 L1 이 돈다
     └ main 안에서 asyncio.run(inner())   ← inner() 는 이미 만들어졌다(인자로 넘기려고)
         └ 「이 스레드에 도는 루프가 있다」 → RuntimeError
         └ inner 는 한 줄도 안 돌고 버려진다 → never awaited
```

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

그림 해설.

* ★★★ **`RuntimeError | asyncio.run() cannot be called from a running event loop`** — 문서 — *"This function cannot be called when another asyncio event loop is running in the same thread."*
* ★★ **`inner body` 가 없고 경고가 하나**(`coroutine 'inner' was never awaited`) — `asyncio.run(inner())` 의 **`inner()` 는 인자라서 먼저 만들어졌고**, `asyncio.run` 은 그것을 **돌리지 못하고 거절**했다. 동작 1 과 **같은 경고**다.
* ★ 루프 안에서는 **`await inner()`** 가 답이다 — 「동기처럼 돌리는」 길은 없다(그 대안들은 [52번](../52-asyncio-concurrency-structure/2-summary.md)의 `create_task` 쪽).

### 9. ★★ `await` 는 무엇 앞에, 어디에 — `TypeError` 와 `SyntaxError`

**언제 쓰나** — `await` 를 붙였는데도 에러가 날 때 · `async def` 안에 `yield` 를 쓰고 싶을 때.

```text
   await 뒤          awaitable 인가?        결과
   42                 아니다                 TypeError  「object int can't be used in 'await' expression」
   f   (괄호 없음)     함수 객체 — 아니다      TypeError  「object function …」
   plain()            int — 아니다           TypeError
   f()                코루틴 — 맞다           1

   await 가 있는 자리   def 안 → SyntaxError   · 모듈 맨 위 → SyntaxError(스크립트에서)
   async def 안의 yield → 코루틴이 아니라 비동기 제너레이터
```

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

그림 해설.

* ★★ **`await` 뒤에는 `__await__` 가 있는 것만** — `42`·함수 객체·`int` 를 돌려준 보통 함수 전부 `TypeError`. ★ **`await f`(괄호 빠짐)** 가 실무의 흔한 오타다.
* ★★ **`def` 안의 `await` 는 `'await' outside async function`**, 모듈 맨 위는 **`'await' outside function`** — 문서 — *"Can only be used inside a coroutine function."*
* ★ **`async def` 안에 `yield` 를 쓰면 코루틴이 아니라 비동기 제너레이터**(`async_generator`, `inspect.iscoroutine` 은 `False`) — `yield from` 은 `SyntaxError`, 값 있는 `return` 도 `SyntaxError`. **비동기 제너레이터·`async for` 는 이 주제 밖**이다(「더 들어가면」).

### 10. ★★ 두 `await` 를 이어 쓰면 — 차례로 돈다(52번으로 가는 다리)

**언제 쓰나** — 「`async` 로 썼으니 동시에 돌겠지」를 확인할 때.

```text
   await job("A"); await job("B")         A start > A end > B start > B end     ← 차례로
   a = job("A"); b = job("B")             both created > B start > …           ← 만든 순서는 상관없다
   await b; await a                                                            ← await 한 순서다
```

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

그림 해설.

* ★★★ **`await` 두 줄은 차례로 돈다** — `A` 가 **끝난 뒤** `B` 가 시작한다. `A` 안의 `await asyncio.sleep(0)` 이 양보해도, **루프에 올라가 있는 다른 일이 없으니** 받을 쪽이 없다.
* ★★★ **만들어 둔 순서는 상관없다** — `a`·`b` 를 먼저 만들고 `await b` 부터 하면 **`B` 가 먼저** 돈다. 동작 1 의 「부르면 주문서만」이 여기서 **순서**로 드러난다.
* ★ **둘을 겹쳐 돌리려면 코루틴을 루프에 따로 올려야 한다**(`asyncio.create_task` · `gather` · `TaskGroup`) — 그 구조와 취소 전파는 [52번](../52-asyncio-concurrency-structure/2-summary.md)이 정본이다.

### 11. ★ 판 격자 — 3.11 대 3.12, 여덟 탐침

**언제 쓰나** — 이 문서의 결론이 판을 타는지 확인할 때.

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

그림 해설.

* ★ **마지막 줄 `0 / 8`** — 호출만 하기 · 타입 이름 · 상태 · 첫 `send` 값 · 재사용 · `next` · 중첩 `run` · `run(42)` 의 **예외 타입·문구·경고**가 두 판에서 한 글자도 같았다. 이 주제의 핵심은 **3.5\~3.7 에 굳은 것**이다.
* ★ `nested_run` 행은 `gc.collect()` 를 해야 경고가 **그 행 안에서** 잡혔다 — 예외의 트레이스백이 프레임을 붙들어 코루틴이 **늦게** 사라진다(동작 2 의 「순환」과 같은 꼴). 처음 판(수집 없음)은 경고가 **프로그램 끝에** `sys:1:` 로 표준 오류에 나왔다.

## 문법 — 형태와 규칙

| 형태 | 무엇이 되나 | 판 | 어디서 봤나 |
|---|---|---|---|
| `async def f(): ...` | **코루틴 함수** — 부르면 코루틴 객체 | 3.5 | 동작 1·4 |
| `await x` | `x.__await__()` 의 이터레이터를 끝까지 통과 — 그 사이 내민 값은 **바깥으로** | 3.5 | 동작 5 |
| `c.send(v)` · `c.throw(e)` · `c.close()` | 코루틴을 한 걸음 · 예외 주입 · 닫기 | 3.5 | 동작 2·5 |
| `asyncio.run(coro)` | **새 루프**로 끝까지 돌리고 닫는다 | 3.7 | 동작 7·8 |
| `async def` 안의 `yield` | 비동기 제너레이터 | 3.6 | 동작 9 |

* 코루틴 함수를 **부르는 것**과 **돌리는 것**은 다른 일이다 — 돌리는 길은 `await`·`asyncio.run`·(52번의) 태스크뿐이다.
* `await` 는 **`async def` 안에서만** — `def` 안·모듈 맨 위는 `SyntaxError`.
* 코루틴은 **한 번만** 돌릴 수 있다 — 끝난 것을 다시 `await`·`send` 하면 `RuntimeError`.
* 코루틴은 **이터레이터가 아니다** — `for`·`next`·`list` 는 `TypeError`.

## 어디서 틀리나

### (1) ★★★ `await` 를 빠뜨리고 「에러가 없으니 됐다」

몸통이 **한 줄도 안 돈다**(동작 1). 남는 것은 **표준 오류의 경고 한 줄**과 `exit 0` 뿐이다. 로그를 표준 출력만 모으면 **흔적이 없다.**

### (2) ★★★ 경고의 줄 번호를 「부른 줄」로 읽는다

경고는 **코루틴이 사라진 줄**에서 난다(동작 2 — 만든 13행이 아니라 `del x` 18행 · 순환이면 `gc.collect()` 28행). 코루틴을 어딘가에 담아 두면 **엉뚱한 줄**을 가리킨다.

### (3) ★★★ JS 처럼 「부르면 첫 `await` 까지는 돈다」고 믿는다

파이썬은 **0 줄**이다(동작 3). 그래서 `await` 전에 있는 **검증·로그·예외**도 전부 안 돈다 — `ValueError` 가 **만들어지지도 않았다.**

### (4) ★★ 「코루틴은 제너레이터다」로 외워 `for`·`next` 를 쓴다

손잡이(`send`·`throw`·`close`)는 같지만 **이터레이터가 아니다**(동작 4). 타입도 별개다.

### (5) ★★ 끝난 코루틴을 다시 `await` 한다

제너레이터처럼 조용히 끝나지 않고 **`RuntimeError`**(「cannot reuse already awaited coroutine」)다(동작 5 `[2]`). 「결과를 캐시해 두고 두 번 기다리기」는 코루틴이 아니라 **태스크·퓨처**로 해야 한다(52번).

### (6) ★★★ 도는 루프 안에서 `asyncio.run` 을 부른다

`RuntimeError` 이고, **넘긴 코루틴은 안 돌고 never awaited**(동작 8). 루프 안에서는 `await` 한다.

### (7) ★★ `asyncio.run` 을 여러 번 부르며 같은 루프라고 믿는다

**매번 새 루프**이고 끝나면 **닫힌다**(동작 7 — `False` · `[True, True]`).

### (8) ★★ `await f`(괄호 없음)

`TypeError`(「object function can't be used in 'await' expression」)다(동작 9). **함수 객체는 awaitable 이 아니다.**

### (9) ★★ `async` 로 썼으니 두 `await` 가 동시에 돈다고 믿는다

**차례로** 돈다(동작 10). 겹치려면 루프에 따로 올려야 한다 — [52번](../52-asyncio-concurrency-structure/2-summary.md).

## 구현 세부사항 대 언어 보장

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **언어 레퍼런스** | 코루틴 객체 · `send`/`throw`/`close` · `StopIteration.value` · `await` 의 자리 | 데이터 모델·식 문서 인용 |
| **라이브러리 보장**(`asyncio` 문서) | `asyncio.run` 의 루프 수명 · 중첩 금지 · 「부르기만 하면 안 돈다」 | 문서 문장을 열어서 인용 |
| **CPython 구현** | never awaited 경고 · 그 **시점**(참조 계수) · 예외·경고 **문구** · `coroutine_wrapper` | 실행 |
| **이 판(3.12.3 · 3.11.15)의 관찰** | 여덟 탐침 판 차이 `0 / 8` | 출력 |
| ★ **못 잰 것** | 3.13·3.14 | 판이 없다 |
| ★ **부적용** | 시간 · 스레드 | 재지 않았다 · 스레드 하나 |

### 라이브러리 보장 — 언어 레퍼런스와 `asyncio` 문서

| 사실 | 근거 |
|---|---|
| 코루틴 함수를 부르면 **코루틴 객체**를 돌려준다 | 용어집 *coroutine function* |
| `send(None)` 이 시작·재개 · 끝나면 `StopIteration` 의 `value` 가 반환값 | 데이터 모델 *Coroutine Objects* |
| 코루틴은 **이터레이션을 직접 지원하지 않는다** | 같은 절 |
| 두 번 `await` 하면 `RuntimeError`(3.5.2) | 같은 절 |
| 사라질 때 `close()` 과정으로 **자동으로 닫힌다** | `coroutine.close` |
| `await` 는 **코루틴 함수 안에서만** | 식 — *Await expression* |
| `__await__` 가 내민 값의 모양은 **언어가 제약하지 않는다**(프레임워크의 것) | `__await__` 의 note |
| 부르기만 하면 **스케줄되지 않는다** | *Coroutines and Tasks* |
| `asyncio.run` 은 새 루프를 쓰고 끝에 닫는다 · 같은 스레드에 도는 루프가 있으면 못 부른다 | `asyncio.run` |

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| ★★★ **never awaited 경고를 내는 것은 인터프리터다** — `asyncio` 를 안 가져와도 난다(동작 1). `asyncio-dev` 의 *"asyncio will emit a `RuntimeWarning`"* 은 **주어가 넓다** | 실행 |
| ★★ 경고가 **사라지는 순간** 나는 것 — 참조 계수가 0 이 되는 자리 · 순환이면 `gc.collect()` 자리 | 실행(동작 2). 언어는 「사라질 때 닫힌다」까지만 말한다 — **「언제 사라지나」는 구현** |
| 경고 문구 `coroutine 'f' was never awaited` · `Enable tracemalloc …` 안내 줄 · ★ `-W error` 로 바꾸면 `Exception ignored in` 으로 **버려지고 `exit 0`** | 실행(동작 1) |
| 예외 문구 — `cannot reuse already awaited coroutine` · `can't send non-None value to a just-started coroutine` · `object int can't be used in 'await' expression` · `'coroutine' object is not an iterator` | 실행 |
| `c.__await__()` 의 타입 이름 `coroutine_wrapper` | 실행 |

### 이 판(3.12.3)의 관찰

- **여덟 탐침이 3.11.15 와 한 칸도 안 갈린 것**(`0 / 8`).
- **`sleep(0)` 이 팻말 `None` 을 한 번 내민 것**(동작 6) — `asyncio` 의 구현이 그렇다. 문서는 「한 번 양보한다」까지만.
- **node v18.19.1 이 미처리 거부에 `exit 1` 로 끝난 것** — node 의 기본값(JS 37번이 node 18·20 두 판에서 쟀다).

### 그래서 이렇게 적으면 틀린다

* ✗ 「`await` 를 빠뜨리면 `asyncio` 가 경고한다」\
  ○ **인터프리터**가 경고한다 — `asyncio` 를 안 가져온 파일에서도 났다.
* ✗ 「never awaited 경고는 코루틴을 만든 줄을 가리킨다」\
  ○ **사라진 줄**을 가리킨다(18행 · 28행). 만든 자리를 보려면 `tracemalloc`(안내 줄이 말하는 것).
* ✗ 「코루틴은 부르면 첫 `await` 까지 돈다」\
  ○ 그건 **JS** 다. 파이썬은 **0 줄**.
* ✗ 「코루틴은 제너레이터다」\
  ○ **이 판에서 타입이 다르고 이터레이터가 아니다.** 같은 것은 손잡이와 멈춤·재개 기계다.
* ✗ 「이벤트 루프가 코루틴을 멈춘다」\
  ○ 코루틴은 **스스로** `await` 에서 멈춘다(팻말을 내민다). 루프는 **다시 불러 주는 쪽**이다 — 루프 없이 손으로도 돌았다(동작 5).

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 프로그램 입구 | `asyncio.run(main())` **한 번** | 루프를 만들고 닫아 준다 |
| 코루틴 안에서 다른 코루틴의 결과 | `await other()` | 차례로 돈다 — 결과가 필요한 순서 그대로 |
| 이미 루프가 도는 곳 | `await` (절대 `asyncio.run` 아님) | 중첩은 `RuntimeError` |
| 여러 코루틴을 **겹쳐** 돌리기 | `create_task`·`gather`·`TaskGroup` | [52번](../52-asyncio-concurrency-structure/2-summary.md) |
| CPU 를 오래 쓰는 일 | 코루틴이 아니다 | 스레드 하나라 겹칠 곳이 없다 — [53번](../53-gil-and-choosing-concurrency/2-summary.md) |
| 코루틴인지 검사 | `inspect.iscoroutine(x)` / 함수는 `inspect.iscoroutinefunction(f)` | 제너레이터와 갈린다(동작 4) |
| `await` 누락을 잡기 | 표준 오류를 모은다 · 테스트는 `catch_warnings(record=True)` 로 개수를 단언 · 디버그 모드 | 경고는 `exit 0` 이고 `-W error` 로도 `exit 0` 이었다(동작 1) |

## 핵심 문장

1. **코루틴 함수를 부르면 주문서(코루틴 객체)만 나온다** — 몸통은 0 줄, 버리면 표준 오류에 `coroutine 'f' was never awaited`, 종료 코드는 `0`.
2. **그 경고는 코루틴이 사라지는 순간** 난다 — 줄 번호는 만든 줄이 아니라 사라진 줄(`del x` 18행 · 순환이면 `gc.collect()` 28행).
3. **JS 는 반대다** — 부르면 첫 `await` 까지 지금 돌고, 던지면 미처리 거부(node 18 `exit 1`). 파이썬은 던질 일조차 없다.
4. **`send` 가 코루틴을 돌리고, `await` 는 팻말을 바깥으로 내민다** — 끝나면 `StopIteration.value` 가 반환값. 루프는 **`send` 를 알맞은 때 불러 주는 쪽**이다(루프 없이 `sleep(0.01)` 은 `RuntimeError`).
5. **`asyncio.run` 은 새 루프를 열고 닫는다** — 두 번이면 다른 루프, 도는 루프 안에서는 `RuntimeError` 에 넘긴 코루틴은 never awaited.

## 관련 자료

* 목록: [python/syntax 주제 목록](../README.md) — 이 주제는 **51번**
* 선행: [17-generators-yield](../17-generators-yield/2-summary.md) — ★★★ **경계**: 「호출해도 몸통이 안 돈다」·`send`·`close`·`yield from`·`StopIteration.value` 의 기계는 그쪽이 정본. 여기는 **그 기계가 `async def`/`await` 로 무엇이 되었나**부터(동작 4·5).
* 다음: [52-asyncio-concurrency-structure](../52-asyncio-concurrency-structure/2-summary.md) — ★★ **경계**: `Task`·`create_task`·`gather`·`TaskGroup`·타임아웃·취소·블로킹 호출은 그쪽. 여기는 **코루틴 하나와 루프 하나**까지(동작 10 이 다리).
* 그 다음: [53-gil-and-choosing-concurrency](../53-gil-and-choosing-concurrency/2-summary.md) — 스레드·프로세스와 `asyncio` 중 무엇을 고르나.
* 도입 역사: [history/python 06번 §5 async 모델](../../../../../../history/python/06-핵심-개념-진화.md) — ★ **경계**: 제너레이터(PEP 255) → `send`(PEP 342) → `yield from`(PEP 380) → `asyncio`(PEP 3156) → `async`/`await`(PEP 492) 의 **도입 역사는 그쪽**, 여기는 **3.12 에서 지금 어떻게 도나**다. ★ 그쪽 §5.5 의 「특수한 제너레이터」는 계보로 읽는다(동작 4).
* 다른 갈래: [JS 39 — `async`/`await`](../../../js/syntax/39-async-await/2-summary.md) — 동작 (9)가 「부른 순간 몸통이 도나」를 파이썬과 나란히 이미 쟀다(여기 동작 3 은 그 다음 걸음). [JS 37 — 프라미스 상태 모델](../../../js/syntax/37-promise-state-model/2-summary.md) — 미처리 거부가 **언제** 보고되나. [JS 36 — 이벤트 루프와 마이크로태스크](../../../js/syntax/36-event-loop-and-microtasks/2-summary.md) — 동작 (6)이 `asyncio` 의 ready 큐가 **한 줄**임을 쟀다.
* 공식 문서: [Coroutines(데이터 모델)](https://docs.python.org/3.12/reference/datamodel.html#coroutines) · [Await expression](https://docs.python.org/3.12/reference/expressions.html#await) · [Coroutines and Tasks](https://docs.python.org/3.12/library/asyncio-task.html) · [Runners](https://docs.python.org/3.12/library/asyncio-runner.html) · [Developing with asyncio](https://docs.python.org/3.12/library/asyncio-dev.html) · [PEP 492](https://peps.python.org/pep-0492/)

## 용어 풀이

* **코루틴 함수(coroutine function)**: `async def` 로 정의한 함수. 부르면 코루틴 객체를 돌려준다.\
  예: `async def f(): ...` 의 `f`.
* **코루틴(coroutine)**: 코루틴 함수가 돌려준 객체. `send` 로 돌리고 `await` 에서 멈춘다.\
  예: `c = f()` — 아직 `CORO_CREATED`.
* **awaitable**: `await` 뒤에 올 수 있는 것. `__await__` 가 이터레이터를 돌려준다.\
  예: 코루틴 · `asyncio.Future` · 동작 5 의 `Pause`.
* **`await`**: awaitable 의 `__await__` 이터레이터를 끝까지 통과시키는 식. 그 사이 내민 값은 바깥으로 나간다.\
  예: `a = await Pause("p1")` 이 `'p1'` 을 내밀고, `send(10)` 에서 `a = 10`.
* **never awaited 경고**: 시작도 안 한 코루틴이 사라질 때 CPython 이 내는 `RuntimeWarning`.\
  예: `coroutine 'f' was never awaited`.
* **이벤트 루프(event loop)**: 코루틴이 내민 팻말을 받아 두었다가 때가 되면 `send` 로 이어 돌리는 반복.\
  예: `asyncio.run` 이 하나 만들어 쓰고 닫는다.
* **`asyncio.run`**: 새 루프로 코루틴 하나를 끝까지 돌리고 루프를 닫는 입구 함수(3.7+).\
  예: `asyncio.run(main())`.
* **`StopIteration.value`**: 코루틴(제너레이터)이 `return` 한 값이 실리는 자리.\
  예: `send(20)` 이 `StopIteration` 을 내며 `value = (10, 20)`.
* **참조 계수(reference count)**: 한 객체를 가리키는 칸의 수. CPython 은 0 이 되는 순간 치운다.\
  예: 동작 2 의 `del x`.
* **순환 수집(cyclic GC)**: 서로를 가리켜 계수가 0 이 안 되는 객체 무리를 치우는 CPython 의 수집기.\
  예: 자기를 품은 리스트는 `gc.collect()` 에서야 사라진다.
* **비동기 제너레이터(asynchronous generator)**: `async def` 안에 `yield` 가 있는 함수가 돌려주는 것(3.6+). `async for` 로 돈다.\
  예: `type(agen()).__name__` 은 `async_generator`.
* **미처리 거부(unhandled rejection)**: JS 에서 거부된 `Promise` 를 아무도 안 받은 것.\
  예: node 18 이 `exit 1`.

## 더 들어가면

* ★ **경고를 실패로 만들고 싶으면** — 동작 1 의 `-W error` 는 `Exception ignored in` 으로 버려졌다. 테스트에서는 `warnings.catch_warnings(record=True)` 로 받아 **개수를 단언**하는 쪽이 이 문서의 창(동작 2)과 같은 모양이다.
* ★ **디버그 모드**(`asyncio.run(main(), debug=True)` · `PYTHONASYNCIODEBUG=1`) — 문서(`asyncio-dev`)는 경고에 **「Coroutine created at」** 트레이스백이 붙는다고 적는다. 절대 경로가 박혀 이 문서는 싣지 않았다.
* ★ **`types.coroutine`** — 제너레이터 함수에 붙여 **`await` 할 수 있게** 만드는 데코레이터. 데이터 모델 note — *"The generator iterator objects returned from generators decorated with `types.coroutine` are also awaitable, but they do not implement `__await__()`."* ★ 이 판 `asyncio/tasks.py` 의 `sleep(0)` 이 그 길이다 — `@types.coroutine` 을 붙인 `__sleep0` 이 **맨 `yield` 하나**를 하고, 그 docstring 이 *"It uses a bare 'yield' expression (which Task.__step knows how to handle) instead of creating a Future object."* 라고 적는다(동작 6 의 `yielded ['None']`).
* ★ **비동기 제너레이터·`async for`·`async with`** — PEP 525·492. 이 주제는 **`async def` 가 코루틴이 되는 경우**까지다.
