# python/syntax/22-closures-and-late-binding — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만.
> - [4.2.1. Binding of names](https://docs.python.org/3.12/reference/executionmodel.html#naming-and-binding) — 자유 변수의 정의
> - [4.2.2. Resolution of names](https://docs.python.org/3.12/reference/executionmodel.html#resolution-of-names) — 이름이 **쓰일 때** 풀린다 · `NameError` 와 `UnboundLocalError`
> - [7.13. The `nonlocal` statement](https://docs.python.org/3.12/reference/simple_stmts.html#the-nonlocal-statement) — 바깥 함수 스코프의 이름에 다시 묶기
> - [3.2. The standard type hierarchy](https://docs.python.org/3.12/reference/datamodel.html#the-standard-type-hierarchy) — 함수 객체의 `__closure__`·`__defaults__`
> - [`functools.partial`](https://docs.python.org/3.12/library/functools.html#functools.partial) — 인자를 미리 붙여 둔 객체
> - [PEP 227 — Statically Nested Scopes](https://peps.python.org/pep-0227/) — 중첩 스코프가 들어온 경위
>
> **실행 검증** — 이 문서에 실린 출력은 전부 `python3` **3.12.3**(Linux)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.\
> 던지는 형태는 `python3 - <파일` 로 고정했다 — 트레이스백이 `File "<stdin>", line N` 이 된다.\
> **버전** — 중첩 스코프(클로저)는 **2.2+**(PEP 227), `nonlocal` 은 **3.0+**(PEP 3104).
> 이 노트 범위(3.10\~3.13)에서 규칙은 안 바뀌었다. 다만 **예외 문구는 명세가 아니다** — 이 노트는 **3.12.3 한 판만** 돌렸다.\
> **구현 대 언어 보장 한 줄** — 「클로저가 바깥 이름을 **부를 때** 본다」는 언어 보장이고,
> 「그 이름이 `cell` 객체 하나로 실체화돼 `__closure__` 에 담긴다」는 **CPython 구현**이다.
>
> **★ 흔들리는 칸 / 안 흔들리는 칸** — 제출 전 재대조에서 「고칠 것」과 「설계상 불일치」를 기계로 가르려고 미리 선언한다.
>
> | 흔들린다 | 안 흔들린다(근거로 써도 되는 칸) |
> |---|---|
> | `<cell at 0x…>`·`<function … at 0x…>` 의 **주소** | 예외 **타입**과 **메시지 본문** |
> | `id()` 가 내놓는 **숫자** | `File "<stdin>", line N` · `(exit N)` |
> | | **셀 개수** · `is` 판정 |
> | | `co_freevars`·`co_varnames` · `__defaults__` 값 |
>
> ★ 이 주제에서 **주소가 박히는 블록은 `e22_loop_fn` 과 `e22_del_cell` 둘뿐이다.**
> 그 두 자리에서 **대조할 것은 주소가 아니라 「셀이 하나라는 것」과 「셀이 비었다는 것」이다.**
> 셀이 하나임을 주소로 말하지 않고 `is` 로 말하는 블록을 따로 두었다(동작 3).
>
> **선행** — [21-scope-legb-global-nonlocal](../21-scope-legb-global-nonlocal/2-summary.md)(이름이 어느 스코프에서 풀리나).\
> **정본 이웃** — [20-mutable-default-args](../20-mutable-default-args/2-summary.md)가 **기본값 쪽의 정본**이다.
> 「기본값이 `def` 실행 때 한 번 만들어진다」와 그 함정·고침은 전부 그쪽이고,
> 여기서는 그것과 **정확히 반대인 쪽**(부를 때마다 읽는다)만 세우고 **대비**한다.

## 한눈에 — 쉽게 말하면

**함수가 들고 나오는 것은 값이 아니라 사물함 열쇠다.**

- 바깥 함수가 이름 하나를 두면, 안쪽 함수는 그 값을 **복사해 가지지 않는다.**
- 대신 그 이름이 들어 있는 **사물함(셀) 하나를 가리키는 열쇠**를 들고 나온다.
- 그래서 안쪽 함수를 **부를 때** 비로소 사물함을 열어 본다 — 그 사이에 누가 안을 바꿔 놓았으면 바뀐 것이 나온다.
- 루프가 함수를 세 개 만들면 **열쇠 세 개가 같은 사물함 하나를 연다.** 그래서 셋이 같은 값을 낸다.

```text
   바깥 함수가 연 사물함        [ i ]
                                  ^
                f0  ──┐           │
                f1  ──┼───────────┘   열쇠 셋이 같은 구멍을 본다
                f2  ──┘

   f0() f1() f2()  ->  "지금 사물함에 뭐가 들었나?" 를 그때 묻는다
   루프가 이미 끝났으므로  ->  마지막에 넣어 둔 것 하나가 셋 다에게 나온다
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 사물함 | 셀(`cell` 객체) | `함수.__closure__[0]` |
| 열쇠 | 자유 변수 이름 하나 | `함수.__code__.co_freevars` |
| 사물함을 연다 | 함수를 **호출**해 그 이름을 읽는다 | 호출 시점에 값이 정해진다 |
| 열쇠 셋이 한 구멍 | 셀 공유 | `셀0 is 셀1` 이 `True` |
| 사물함을 새로 빌린다 | 바깥 함수를 **다시 호출**한다 | 새 셀 — `is` 가 `False` |
| 값을 복사해 왔다 | 기본 인자(20번) | `__defaults__` 에 박힌다 |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.\
「**버튼 열 개에 콜백을 달았더니 전부 마지막 것만 동작한다**」와
「**루프에서 `lambda` 로 태스크를 만들어 스레드풀에 넣었더니 전부 같은 인덱스를 처리한다**」가 그것이다.\
둘 다 원인이 하나다 — **루프가 이름을 새로 만들어 주지 않는다.**

> **자유 변수(free variable)** — 어떤 코드 블록에서 **쓰이는데 그 블록에서 정의되지는 않은** 이름.\
> 예: 바깥 함수의 `i` 를 안쪽 `def f(): return i` 가 읽으면 `i` 는 `f` 의 자유 변수다.
> 언어 레퍼런스가 그대로 적는다 — *"If a variable is used in a code block but not defined there, it is a free variable."*

> **클로저(closure)** — 자유 변수를 가진 안쪽 함수 + 그 이름이 사는 바깥 스코프를 **함께 묶은 것**.\
> 예: `make_counter()` 가 돌려준 `tick` 은 자기 코드와 바깥의 `n` 을 함께 들고 다닌다.

> **늦은 바인딩(late binding)** — 이름이 **정의할 때가 아니라 쓸 때** 값으로 풀리는 것.\
> 예: 루프에서 만든 함수 셋을 루프가 끝난 뒤에 부르면 셋 다 마지막 값을 본다.

## 이 주제가 답하려는 질문

1. **루프에서 만든 함수 셋은 왜 같은 값을 내나** — 「나중에 읽어서」인가, 「애초에 상자가 하나여서」인가.
2. **그 상자가 하나라는 것을 무엇으로 증명하나** — 주소를 눈으로 비교하는 것 말고 판정할 방법이 있나.
3. **고치는 세 가지는 각각 무엇을 옮기는 것인가** — 기본 인자·팩토리·`partial` 이 서로 어떻게 다른가.

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 문장으로 읽는다.\
> 이 주제의 네 번째 창은 **함수 객체의 속 보기**다 — `__closure__` · `cell_contents` · `co_freevars` · `__defaults__`.\
> **무엇이 나오는지는 던져서**, **왜 그런지는 이 네 속성으로** 본다.

돌린 판은 이것이다.

```python
# v_version.py
import sys

print("version_info =", sys.version_info)
print("implementation =", sys.implementation.name)
print("platform =", sys.platform)
```

```text
===== python3 - <v_version.py =====
version_info = sys.version_info(major=3, minor=12, micro=3, releaselevel='final', serial=0)
implementation = cpython
platform = linux
(exit 0)
```

### 1. ★ 루프는 상자를 안 만든다

**언제 쓰나** — 「루프 변수를 캡처했는데 왜 마지막 값만 나오나」를 물을 때. 시작은 늘 여기다.

```text
   for i in range(3):        이름 쪽에서 무슨 일이 나나
   ------------------        ------------------------------
     회차 0                    i 라는 이름에 0 을 묶는다
     회차 1                    같은 이름에 1 을 다시 묶는다
     회차 2                    같은 이름에 2 를 다시 묶는다
   루프 끝                     i 는 지워지지 않는다 (= 2)

   ★ 회차마다 새 이름이 생기지 않는다 -> 담을 상자도 하나뿐이다
```

```python
# e22_loop.py
makers = []
for i in range(3):
    def maker():
        return i
    makers.append(maker)

print("만든 함수 개수:", len(makers))
print("부른 결과     :", [m() for m in makers])
print("루프가 끝난 뒤 i =", i)
```

```text
===== python3 - <e22_loop.py =====
만든 함수 개수: 3
부른 결과     : [2, 2, 2]
루프가 끝난 뒤 i = 2
(exit 0)
```

그림 해설.

- 함수는 **세 개가 맞다.** `len(makers)` 가 `3` 이다 — 만들어지기는 회차마다 새로 만들어진다.
- 그런데 부른 결과가 `[2, 2, 2]` 다. **함수는 셋인데 보는 이름은 하나**다.
- 마지막 줄이 그 증거다 — **루프가 끝난 뒤에도 `i` 가 살아 있고 값이 `2`** 다.\
  파이썬에서 **`for` 는 스코프를 만들지 않는다.** 이름 하나를 세 번 다시 묶었을 뿐이다.
- ★ 이 판은 **모듈 수준**이라 `i` 는 전역 이름이다. 자유 변수의 정의(위 용어 블록)상 **아직 클로저가 아니다.**\
  셀 이야기는 **함수 안으로 들어가야** 시작된다 — 그것이 다음 절이다.

**비용** — 없다. 이것은 최적화가 아니라 **이름 바인딩 규칙의 필연적 결과**다.\
회차마다 새 이름을 만드는 언어(자바스크립트의 `let`)와 갈리는 지점이 정확히 여기다.

### 2. ★ 셀 — 함수 안에서는 상자가 눈에 보인다

**언제 쓰나** — 「같은 값이 나온다」를 말로 하지 말고 **보여 줘야** 할 때.

같은 루프를 함수 안에 넣으면, 이번에는 `i` 가 **바깥 함수의 지역 이름**이라 안쪽 함수의 자유 변수가 된다.

```python
# e22_loop_fn.py
def build():
    fns = []
    for i in range(3):
        def f():
            return i
        fns.append(f)
    return fns


fns = build()
print("부른 결과:", [f() for f in fns])
print("f.__closure__       :", fns[0].__closure__)
print("셀 안의 값          :", fns[0].__closure__[0].cell_contents)
print("자유 변수 이름      :", fns[0].__code__.co_freevars)
```

```text
===== python3 - <e22_loop_fn.py =====
부른 결과: [2, 2, 2]
f.__closure__       : (<cell at 0x7a60305d4220: int object at 0xb370c8>,)
셀 안의 값          : 2
자유 변수 이름      : ('i',)
(exit 0)
```

★ **대조할 것은 주소가 아니라 「셀이 하나」라는 것이다.** 위 출력의 `0x7a60305d4220` 과 `0xb370c8` 은
**돌릴 때마다 달라진다.** 근거로 쓸 칸은 그 옆의 세 가지다.

| 봐야 할 칸 | 값 | 무엇을 말하나 |
|---|---|---|
| `co_freevars` | `('i',)` | 이 함수는 `i` 를 **자기 것으로 안 가지고 빌려 쓴다** |
| `__closure__` 의 길이 | 1 | 빌려 쓰는 이름이 하나 → 셀도 하나 |
| `cell_contents` | `2` | 그 셀 안에 지금 들어 있는 값 |

```text
   build() 를 부르면

   build 프레임
   +-----------------------+
   |    i  ->  [ 셀 : 2 ]  |
   +-----------------------+
         ^       ^       ^
         |       |       |
        f0      f1      f2      셋 다 __closure__[0] 가 이 셀
```

그림 해설.

- `__closure__` 는 **셀들의 튜플**이다. 자유 변수 하나당 셀 하나가 들어간다.
- `cell_contents` 는 그 셀이 **지금** 들고 있는 값이다. 함수가 값을 복사해 간 것이 아니라 **셀을 가리키고 있다.**
- 그래서 `f()` 를 부르면 파이썬이 그때 셀을 열어 본다 — **「늦은 바인딩」의 실체가 이것**이다.
- ★ `__closure__`·`cell_contents` 는 **CPython 구현**이다(아래 「구현 세부사항 대 언어 보장」). 언어가 보장하는 것은 「바깥 이름을 본다」까지다.

**비용** — 자유 변수를 읽는 일이 지역 변수 읽기보다 한 단계 더 든다(셀을 거친다).\
다만 **재지 않았으므로 「느리다」고 적지 않는다** — 이 노트는 `timeit` 을 돌리지 않았다.

### 3. ★★ 셀이 하나라는 것을 `is` 로 증명한다

**언제 쓰나** — 이 주제의 핵심. 「같은 값이 나온다」에서 「**같은 상자를 본다**」로 넘어갈 때.

앞 절의 주소는 흔들린다. 그래서 **주소를 비교하지 않고 판정**한다.

```python
# e22_cell_shared.py
def build():
    fns = []
    for i in range(3):
        def f():
            return i
        fns.append(f)
    return fns


fns = build()
cells = [f.__closure__[0] for f in fns]
print("셀 개수:", len(cells))
print("셀 0 is 셀 1:", cells[0] is cells[1])
print("셀 1 is 셀 2:", cells[1] is cells[2])
print("서로 다른 셀이 몇 개인가:", len({id(c) for c in cells}))
print("셀 안 값 세 개:", [c.cell_contents for c in cells])
```

```text
===== python3 - <e22_cell_shared.py =====
셀 개수: 3
셀 0 is 셀 1: True
셀 1 is 셀 2: True
서로 다른 셀이 몇 개인가: 1
셀 안 값 세 개: [2, 2, 2]
(exit 0)
```

그림 해설.

- 셀 객체를 세 개 꺼냈는데 `셀0 is 셀1` 과 `셀1 is 셀2` 가 **둘 다 `True`** 다.
- 「서로 다른 셀이 몇 개인가」가 **`1`** 이다. 함수는 셋인데 **셀은 하나**다.
- `is` 는 **정체 판정**이라 주소를 눈으로 대조할 필요가 없다. 재대조에서도 한 글자도 안 흔들린다.

★★ **그래서 답은 「나중에 읽어서」가 아니라 「애초에 상자가 하나여서」다.**\
「나중에 읽는다」는 **증상의 절반**만 설명한다 — 상자가 셋이었다면 나중에 읽어도 `[0, 1, 2]` 가 나왔을 것이다.\
실제로 **상자를 셋으로 가르면 그렇게 된다**(동작 6의 팩토리).

```text
   틀린 그림 (이렇게 생각하기 쉽다)        맞는 그림
   f0 -> [0]   f1 -> [1]   f2 -> [2]       f0 ─┐
   "나중에 읽어서 덮어써졌다"                f1 ─┼──> [ 2 ]   셀 하나
                                            f2 ─┘
   -> 상자가 셋이면 값도 셋이었을 것이다     -> 값이 하나인 이유는 상자가 하나이기 때문
```

**비용** — 없음. 이 성질이 곧 다음 절의 **쓸모**가 된다(카운터).

### 4. ★ 셀은 살아 있다 — 읽는 쪽과 쓰는 쪽이 같은 상자를 본다

**언제 쓰나** — 클로저가 「사진」이 아니라 「창문」임을 확인할 때.

```python
# e22_cell_live.py
def build():
    box = "처음"

    def read():
        return box

    def write(v):
        nonlocal box
        box = v

    return read, write


read, write = build()
cell = read.__closure__[0]
print("① read()          :", read())
print("① cell_contents   :", cell.cell_contents)
write("나중")
print("② read()          :", read())
print("② cell_contents   :", cell.cell_contents)
print("셀 객체는 그대로인가:", cell is read.__closure__[0])
print("read 와 write 가 같은 셀을 보나:", read.__closure__[0] is write.__closure__[0])
```

```text
===== python3 - <e22_cell_live.py =====
① read()          : 처음
① cell_contents   : 처음
② read()          : 나중
② cell_contents   : 나중
셀 객체는 그대로인가: True
read 와 write 가 같은 셀을 보나: True
(exit 0)
```

그림 해설.

- `write("나중")` 뒤에 `read()` 도 `cell_contents` 도 **함께** 바뀌었다. 둘이 같은 것을 보고 있다는 뜻이다.
- **셀 객체 자체는 그대로다** — `cell is read.__closure__[0]` 이 `True`. 갈아 끼운 것이 아니라 **안을 고친 것**이다.
- `read` 와 `write` 는 서로 다른 함수인데 `__closure__[0]` 이 **같은 셀**이다.\
  → 클로저는 함수 하나에 딸린 것이 아니라 **스코프에 딸린 것**이고, 그 스코프를 공유하는 함수들이 같은 셀을 나눠 쓴다.
- 바깥 이름에 **다시 묶는** 일은 `nonlocal` 이 있어야 한다. 그 규칙의 정본은 [21번](../21-scope-legb-global-nonlocal/2-summary.md)이다.

**비용** — 상태가 **함수 바깥에서 안 보이는 자리**에 산다.\
캡슐화로는 값이고, 디버깅으로는 대가다 — `print` 로 들여다볼 이름이 없어서 `__closure__` 를 열어야 한다.

### 5. ★★ 20번과 정확히 반대다

**언제 쓰나** — 두 주제를 함께 복습할 때. **이 문서의 축이 여기다.**

★ **기본값 쪽의 정본은 [20번](../20-mutable-default-args/2-summary.md)이다.** 여기서는 **대비만** 세운다.

```text
   기본 인자 (20번이 정본)                 클로저 (여기)
   -----------------------                 --------------------------
   def 문이 돌 때 한 번 계산               부를 때마다 셀을 읽는다
   +---------------------+                 +----------------------+
   | 함수 by_default     |                 | 함수 by_closure      |
   | __defaults__ -> (10,)|                | __closure__ -> [셀]  |
   | __closure__  -> None |                +----------------------+
   +---------------------+                            |
             |                                        |
        값이 박혔다                               이름이 이어졌다
   바깥 limit 을 99 로 다시 묶으면           바깥 limit 을 99 로 다시 묶으면
        ->  10 그대로                             ->  99 가 나온다
```

```python
# e22_vs_20.py
def build(limit):
    def by_default(v=limit):
        return v

    def by_closure():
        return limit

    def rebind(new):
        nonlocal limit
        limit = new

    return by_default, by_closure, rebind


by_default, by_closure, rebind = build(10)

print("바꾸기 전 — 기본값:", by_default(), "· 클로저:", by_closure())
rebind(99)
print("바꾼 뒤   — 기본값:", by_default(), "· 클로저:", by_closure())
print("by_default.__defaults__          :", by_default.__defaults__)
print("by_closure 셀 내용               :", by_closure.__closure__[0].cell_contents)
print("by_default 에 __closure__ 가 있나:", by_default.__closure__)
```

```text
===== python3 - <e22_vs_20.py =====
바꾸기 전 — 기본값: 10 · 클로저: 10
바꾼 뒤   — 기본값: 10 · 클로저: 99
by_default.__defaults__          : (10,)
by_closure 셀 내용               : 99
by_default 에 __closure__ 가 있나: None
(exit 0)
```

**표의 네 칸과 그것을 실증한 블록**

| | 기본 인자(20번) | 클로저(22번) | 어느 블록이 실증하나 |
|---|---|---|---|
| 값이 정해지는 때 | `def` 문이 돌 때 **한 번** | 함수를 **부를 때마다** | `e22_vs_20` — `rebind(99)` 뒤 기본값은 `10`, 클로저는 `99` |
| 어디에 사는가 | `__defaults__` 튜플 | `__closure__` 의 셀 | `e22_vs_20` — `(10,)` 대 셀 내용 `99` |
| 바깥 이름을 다시 묶으면 | 안 따라간다 | 따라간다 | `e22_vs_20` — 위 두 줄이 같은 실행이다 |
| 함수를 두 번 만들면 | 기본값 객체는 **하나** | 셀이 **둘로 갈린다** | `e22_vs_20_mutable` — `is` 가 `True` 대 `False` |

그림 해설.

- `by_default(v=limit)` 는 **`def` 가 도는 순간** `limit` 을 읽어 `v` 의 기본값으로 박았다. 그래서 `(10,)` 이다.
- `by_closure()` 는 `limit` 을 몸통에서 읽는다. 그래서 자유 변수이고, `rebind(99)` 가 셀을 고치자 **따라 바뀐다.**
- ★ **`by_default` 의 `__closure__` 가 `None`** 이다 — 기본값으로 받은 쪽은 **자유 변수를 아예 안 가진다.**\
  같은 바깥 이름을 참조했는데 **한쪽은 셀이 없고 한쪽은 셀이 있다.** 「어디에 사는가」 칸이 이 한 줄로 실증된다.

네 번째 칸은 따로 돌렸다 — **가변 객체**로 보면 더 선명하다.

```python
# e22_vs_20_mutable.py
def by_default(bag=[]):
    bag.append("x")
    return bag


def make_by_closure():
    bag = []

    def add():
        bag.append("x")
        return bag

    return add


add1 = make_by_closure()
add2 = make_by_closure()

print("기본값 — 두 호출이 받는 리스트")
print("  1회:", by_default(), "· 2회:", by_default())
print("  두 호출이 같은 객체인가:", by_default() is by_default())
print("클로저 — 두 번 만든 함수의 리스트")
print("  add1:", add1(), "· add2:", add2())
print("  둘이 같은 셀인가:", add1.__closure__[0] is add2.__closure__[0])
```

```text
===== python3 - <e22_vs_20_mutable.py =====
기본값 — 두 호출이 받는 리스트
  1회: ['x', 'x'] · 2회: ['x', 'x']
  두 호출이 같은 객체인가: True
클로저 — 두 번 만든 함수의 리스트
  add1: ['x'] · add2: ['x']
  둘이 같은 셀인가: False
(exit 0)
```

그림 해설.

- 기본값 쪽 첫 줄이 `['x', 'x']` **두 번**이다. `print` 의 인자 둘이 왼쪽부터 평가되면서 **같은 리스트에 두 번 붙었고**,
  찍을 때는 둘 다 **그 같은 리스트**를 보기 때문이다. 이것 자체가 「같은 객체」의 증거다.
- 다음 줄의 `is` 판정이 그것을 못 박는다 — **`True`**.
- 클로저 쪽은 `make_by_closure()` 를 **두 번 불렀다.** 호출마다 새 프레임·새 `bag`·새 셀이라 `is` 가 **`False`** 이고,
  둘 다 `['x']` 로 서로를 오염시키지 않는다.

★ **한 문장으로** — 기본값은 **함수당 하나**이고, 셀은 **바깥 함수의 호출당 하나**다.

**비용** — 두 기계가 각각 맞는 자리가 다르다.\
「고정해 두고 싶다」면 기본값, 「따라 움직이게 하고 싶다」면 클로저다. **어느 쪽도 항상 옳지 않다.**

### 6. ★ 고침 셋 — 각각 무엇을 옮기는가

**언제 쓰나** — 루프 클로저를 실제로 고칠 때. 셋 다 동작하고, **옮기는 자리가 다르다.**

```text
   고장난 것                고침 ①              고침 ②             고침 ③
   셀 하나를 공유           셀을 없앤다          셀을 가른다         함수 밖으로 뺀다
   f0 ─┐                    f0 [기본값 0]        f0 -> [0]          partial(f, 0)
   f1 ─┼─> [ 2 ]            f1 [기본값 1]        f1 -> [1]          partial(f, 1)
   f2 ─┘                    f2 [기본값 2]        f2 -> [2]          partial(f, 2)
   __closure__ 길이 1       __closure__ None     서로 다른 셀 3      __closure__ 없음
```

#### 고침 ① 기본 인자 트릭 — 셀을 없애고 `__defaults__` 로 옮긴다

```python
# e22_fix_default.py
def build_default():
    fns = []
    for i in range(3):
        def f(i=i):
            return i
        fns.append(f)
    return fns


fns = build_default()
print("부른 결과      :", [f() for f in fns])
print("__closure__    :", fns[0].__closure__)
print("__defaults__   :", [f.__defaults__ for f in fns])
print("co_freevars    :", fns[0].__code__.co_freevars)
print("co_varnames    :", fns[0].__code__.co_varnames)
```

```text
===== python3 - <e22_fix_default.py =====
부른 결과      : [0, 1, 2]
__closure__    : None
__defaults__   : [(0,), (1,), (2,)]
co_freevars    : ()
co_varnames    : ('i',)
(exit 0)
```

그림 해설.

- 결과가 `[0, 1, 2]` 다. 회차마다 **그때의 `i` 값이 `def` 실행 중에 평가돼 박혔다.**
- `__closure__` 가 **`None`** 이 됐다. `co_freevars` 도 **비었다** — `i` 가 더는 자유 변수가 아니다.
- 대신 `co_varnames` 에 `i` 가 있고 `__defaults__` 가 `(0,)`·`(1,)`·`(2,)` 로 **셋이 다르다.**\
  **이름이 자유 변수에서 파라미터로 이사했다.** 그것이 이 고침의 전부다.
- ★★ **20번에서 함정이던 성질이 여기서는 고침이 된다** — 「기본값은 `def` 때 한 번 평가된다」.\
  같은 기계를 **가변 객체에 쓰면 함정**이고 **루프 변수에 쓰면 해법**이다. 두 주제를 나란히 두는 이유가 이것이다.
- 대가 — **시그니처가 더러워진다.** `f(i=i)` 는 호출자가 `f(5)` 로 덮어쓸 수 있다. 공개 API 에는 권하지 않는다.

#### 고침 ② 팩토리 — 셀을 셋으로 가른다

```python
# e22_fix_factory.py
def make(i):
    def f():
        return i
    return f


fns = [make(i) for i in range(3)]
print("부른 결과:", [f() for f in fns])
cells = [f.__closure__[0] for f in fns]
print("서로 다른 셀 개수:", len({id(c) for c in cells}))
print("셀 0 is 셀 1:", cells[0] is cells[1])
print("셀 안 값     :", [c.cell_contents for c in cells])
```

```text
===== python3 - <e22_fix_factory.py =====
부른 결과: [0, 1, 2]
서로 다른 셀 개수: 3
셀 0 is 셀 1: False
셀 안 값     : [0, 1, 2]
(exit 0)
```

그림 해설.

- **서로 다른 셀 개수가 `3`** 이다. 동작 3에서 `1` 이던 그 칸이다 — **같은 칸을 같은 방법으로 쟀다.**
- `셀0 is 셀1` 이 **`False`**. 주소를 안 보고 판정한 것도 그대로다.
- `make(i)` 를 세 번 불렀으므로 **프레임이 세 개** 생겼고, 프레임마다 자기 `i` 와 자기 셀을 가진다.
- ★ 클로저를 **없애지 않고** 고친 유일한 방법이다. `__closure__` 는 그대로 있고 **개수만 갈렸다.**\
  그래서 「클로저는 위험하다」가 아니라 「**셀의 개수를 내가 정한다**」가 맞는 교훈이다.

#### 고침 ③ `functools.partial` — 함수 밖 객체로 옮긴다

```python
# e22_fix_partial.py
from functools import partial


def identity(i):
    return i


fns = [partial(identity, i) for i in range(3)]
print("부른 결과:", [f() for f in fns])
print("partial 은 함수인가:", callable(fns[0]), "· 타입:", type(fns[0]).__name__)
print("고정된 인자:", [f.args for f in fns])
print("__closure__ 가 있나:", hasattr(fns[0], "__closure__"))
print("감싼 대상  :", fns[0].func is identity)
```

```text
===== python3 - <e22_fix_partial.py =====
부른 결과: [0, 1, 2]
partial 은 함수인가: True · 타입: partial
고정된 인자: [(0,), (1,), (2,)]
__closure__ 가 있나: False
감싼 대상  : True
(exit 0)
```

```text
   클로저                                  partial
   함수 ─┬─> __closure__ ─> 셀             partial 객체 ─┬─> func -> identity
         └─> 코드                                         └─> args -> (0,)
   값이 함수 「안쪽」에 붙는다               값이 함수 「바깥」 객체에 붙는다
```

그림 해설.

- 결과는 `[0, 1, 2]` 로 같은데 **물건이 다르다** — 타입이 `partial` 이다. **함수가 아니다.**
- `callable()` 은 `True` 라 부르는 데는 지장이 없다. 그러나 `hasattr(fns[0], "__closure__")` 가 **`False`** 다 —
  **클로저가 아니라 속성조차 없다.**
- 고정한 값은 `args` 에 **튜플로 보인다**(`(0,)`·`(1,)`·`(2,)`). 감싼 대상은 `func` 로 꺼낼 수 있다.
- ★ 셋 중 **유일하게 밖에서 들여다보기 쉬운** 형태다. 디버깅과 로깅에서 값을 친다.
- 대가 — 함수가 아니므로 **함수인 것을 전제한 코드와 어긋난다.** 데코레이터·`functools.wraps` 와 섞을 때 걸린다([24번](../24-decorators/2-summary.md)).

**셋의 판정표**

| 고침 | 무엇을 옮기나 | 남는 흔적 | 언제 고르나 |
|---|---|---|---|
| 기본 인자 `f(i=i)` | 셀을 **없애고** `__defaults__` 로 | `__closure__` 가 `None` | 한 줄로 급히 고칠 때 · 내부 함수 |
| 팩토리 `make(i)` | 셀을 **가른다** | 서로 다른 셀 N개 | **기본값**이 읽는 사람에게 설명되는 표준 해법 |
| `partial(f, i)` | **함수 밖 객체**에 담는다 | `args` 에 보인다 | 값을 밖에서 봐야 할 때 · 이미 있는 함수를 재활용할 때 |

**비용** — 셋 다 「호출 시점의 값 하나를 미리 고정한다」는 같은 일을 한다.\
고르는 기준은 성능이 아니라 **누가 그 값을 볼 수 있어야 하나**다.

### 7. ★ 쓸모 쪽 — `nonlocal` 카운터

**언제 쓰나** — 클로저가 버그가 아니라 **도구**인 자리. 셀 공유가 그대로 값이 된다.

```text
   make_counter() 프레임
   +------------------+
   |   n  ->  [ 3 ]   |
   +------------------+
        ^          ^
        |          |
      tick       peek       같은 셀 — is 가 True
     (쓴다)      (읽는다)

   make_counter(100) 을 또 부르면 -> 새 프레임 · 새 셀 — is 가 False
```

```python
# e22_counter.py
def make_counter(start=0):
    n = start

    def tick():
        nonlocal n
        n += 1
        return n

    def peek():
        return n

    return tick, peek


tick, peek = make_counter()
print("세 번 부른다:", [tick(), tick(), tick()])
print("peek()      :", peek())
print("tick 과 peek 가 같은 셀:", tick.__closure__[0] is peek.__closure__[0])

tick2, peek2 = make_counter(100)
print("새로 만든 것:", [tick2(), tick2()])
print("먼저 것은 그대로:", peek())
print("두 카운터가 같은 셀인가:", tick.__closure__[0] is tick2.__closure__[0])
```

```text
===== python3 - <e22_counter.py =====
세 번 부른다: [1, 2, 3]
peek()      : 3
tick 과 peek 가 같은 셀: True
새로 만든 것: [101, 102]
먼저 것은 그대로: 3
두 카운터가 같은 셀인가: False
(exit 0)
```

그림 해설.

- `tick` 을 세 번 불러 `[1, 2, 3]`, 그다음 `peek()` 가 **`3`** 이다. 둘이 같은 상태를 본다.
- `tick.__closure__[0] is peek.__closure__[0]` 이 **`True`** — 동작 4의 `read`/`write` 와 같은 구조다.
- `make_counter(100)` 으로 만든 두 번째 카운터는 **`101`·`102`** 로 자기 길을 가고,
  첫 카운터의 `peek()` 는 **`3`** 그대로다. 셀이 갈렸기 때문이다(`is` 가 `False`).
- ★ **동작 6의 팩토리와 똑같은 그림이다.** 「바깥 함수를 다시 부르면 셀이 갈린다」 하나로 둘이 설명된다.

**비용** — 클래스보다 가볍고, 상태가 **완전히 숨는다.**\
대신 상태를 꺼내 볼 공식 통로가 없다 — 그래서 `peek` 같은 읽기 함수를 같이 돌려주는 형태가 관용구가 된다.

### 8. ★ 비어 있는 자리 — 두 예외가 다르다

**언제 쓰나** — 「이름이 준비 안 됐다」가 두 가지라는 것을 가를 때.

#### `nonlocal` 없이 바깥 이름에 더하기

```python
# e22_counter_broken.py
def make_counter():
    n = 0

    def tick():
        n += 1
        return n

    return tick


tick = make_counter()
tick()
```

```text
===== python3 - <e22_counter_broken.py =====
Traceback (most recent call last):
  File "<stdin>", line 12, in <module>
  File "<stdin>", line 5, in tick
UnboundLocalError: cannot access local variable 'n' where it is not associated with a value
(exit 1)
```

- `n += 1` 은 **대입**이다. 대입이 있으면 그 블록에서 `n` 은 **지역 이름**이 되고, 읽을 값이 아직 없어 터진다.
- 예외는 **`UnboundLocalError`**, 문구는 *"cannot access local variable"* 이다.
- ★ **이 규칙의 정본은 [21번](../21-scope-legb-global-nonlocal/2-summary.md)이다.** 여기서는 **다음 것과 가르기 위해서만** 싣는다.

#### 셀은 있는데 비었다

```python
# e22_del_cell.py
def outer():
    v = "있었다"

    def read():
        return v

    del v
    return read


read = outer()
print("셀은 있나:", read.__closure__)
read()
```

```text
===== python3 - <e22_del_cell.py =====
셀은 있나: (<cell at 0x78297df3feb0: empty>,)
Traceback (most recent call last):
  File "<stdin>", line 13, in <module>
  File "<stdin>", line 5, in read
NameError: cannot access free variable 'v' where it is not associated with a value in enclosing scope
(exit 1)
```

★ **대조할 것은 주소가 아니라 「셀이 비었다」는 것이다** — `0x78297df3feb0` 은 돌릴 때마다 달라진다.\
봐야 할 칸은 `<cell at …: empty>` 의 **`empty`** 와 예외 타입·문구다.

```text
   del v 직후

   read.__closure__  ->  ( <cell : empty> )
                            ^^^^^^^^^^^
                         셀은 있는데 안이 비었다

   read() 호출  ->  NameError: cannot access free variable 'v' ...
                    (UnboundLocalError 가 아니다)
```

**두 예외를 가르는 그림**

```text
   "이름이 준비 안 됐다" 는 두 자리에서 난다

   ① 지역인데 아직 안 묶였다        ->  UnboundLocalError
      (nonlocal 없이 n += 1)            "cannot access local variable 'n' ..."

   ② 자유 변수인데 셀이 비었다      ->  NameError
      (바깥에서 del v)                  "cannot access free variable 'v' ...
                                         in enclosing scope"

   UnboundLocalError 는 NameError 의 하위 클래스다 — 계층의 정본은 21번
```

그림 해설.

- 두 트레이스백 모두 **`File "<stdin>", line N` 이 두 줄**이다(부른 자리 + 터진 자리). 이 칸은 안 흔들린다.
- ★ **`del v` 가 셀을 없애지 않는다.** 셀은 남고 **안만 빈다** — 그래서 `__closure__` 를 찍으면 튜플이 나온다.
- 문구에 **`in enclosing scope`** 가 붙는 것이 ①과 갈리는 자리다. 「지역」이 아니라 「바깥 스코프의 자유 변수」라는 말이다.
- 언어 레퍼런스가 두 경우를 나눠 적는다 — *"When a name is not found at all, a NameError exception is raised.
  If the current scope is a function scope, and the name refers to a local variable that has not yet been bound to a value
  at the point where the name is used, an UnboundLocalError exception is raised. UnboundLocalError is a subclass of NameError."*

**비용** — 실무에서 ②를 만날 일은 드물다(바깥 지역 변수를 일부러 `del` 해야 한다).\
값은 **경계를 아는 것**이다 — `except UnboundLocalError:` 로 ②를 못 잡고, `except NameError:` 로는 둘 다 잡힌다.

## 문법 — 형태와 규칙

```python
def outer():
    x = 1

    def inner():        # x 를 읽기만 하면 -> 자유 변수, 셀이 생긴다
        return x

    def setter(v):
        nonlocal x      # 바깥 x 에 다시 묶으려면 이 선언이 필요하다
        x = v

    return inner, setter


inner, setter = outer()
inner.__closure__          # 셀들의 튜플, 없으면 None
inner.__closure__[0].cell_contents   # 그 셀이 지금 들고 있는 값
inner.__code__.co_freevars           # 자유 변수 이름들의 튜플
```

규칙 여섯.

1. **자유 변수는 「쓰였는데 여기서 정의되지 않은 이름」이다.** 읽기만 하면 선언이 필요 없다.
2. **자유 변수는 함수를 부를 때 풀린다.** 정의할 때가 아니다 — 그래서 늦은 바인딩이다.
3. **`for`·`if`·`while` 은 스코프를 만들지 않는다.** 새 이름이 생기지 않으니 새 셀도 없다.
4. **바깥 이름에 다시 묶으려면 `nonlocal`이 필요하다.** 없이 대입하면 그 이름은 지역이 된다(정본 [21번](../21-scope-legb-global-nonlocal/2-summary.md)).
5. **셀은 스코프당 하나다.** 그 스코프를 공유하는 함수들이 같은 셀을 나눠 쓴다.
6. **바깥 함수를 다시 부르면 새 프레임·새 셀이다.** 셀을 가르는 유일한 방법이 이것이다(팩토리).

> **셀(cell)** — 자유 변수 하나를 담는 CPython 내부 객체.\
> 예: `f.__closure__[0]` 이 셀이고, `.cell_contents` 로 안을 본다.

> **`nonlocal`** — 가장 가까운 바깥 **함수** 스코프의 이름에 다시 묶겠다는 선언.\
> 예: `nonlocal n` 없이 `n += 1` 을 쓰면 `n` 이 지역이 돼 `UnboundLocalError` 가 난다.

## 어디서 틀리나

> ★ 이 절의 (2)\~(4)에 실은 코드는 **출력을 싣지 않았다.** 위 규칙에서 따라 나오는 것을 적었을 뿐이고,
> **돌려 본 블록은 「동작 방식」에 실린 것이 전부**다. 각각의 정본 주제를 옆에 적어 둔다.

### (1) 「나중에 읽어서 덮어써졌다」는 반쪽 설명이다

가장 흔한 오해다. **고침을 못 찾게 만든다는 점**에서 실질적인 해다.

- 「나중에 읽는다」가 맞다면, 고치는 법은 「**더 일찍 읽게 하는 것**」이 된다 — 그런 수단은 없다.
- 맞는 진단은 「**상자가 하나다**」이고, 그래서 고침이 「**상자를 없애거나 가르는 것**」이 된다.
- 동작 3의 `서로 다른 셀이 몇 개인가` 가 `1` 이고 동작 6의 팩토리에서 `3` 인 것이 이 진단의 근거다.

### (2) `lambda` 로 바꾸면 달라진다고 생각한다

```python
fns = [lambda: i for i in range(3)]
```

`lambda` 는 **함수를 만드는 식일 뿐** 바인딩 규칙을 바꾸지 않는다. `def` 와 같은 일이 난다.\
★ `lambda` 쪽의 정본은 [23번](../23-lambda-and-higher-order-functions/2-summary.md)이다 — **그 편의 늦은 바인딩 예제도 결국 이 문서의 규칙**이다.

### (3) 컴프리헨션 안이라 안전하다고 생각한다

`[lambda: i for i in range(3)]` 은 컴프리헨션이 자기 스코프를 가지므로 「바깥 `i` 를 안 건드린다」까지는 맞다.\
그러나 **그 안에서도 `i` 는 이름 하나**다. 만들어진 `lambda` 셋은 여전히 같은 상자를 본다.\
★ 컴프리헨션 스코프의 정본은 [21번](../21-scope-legb-global-nonlocal/2-summary.md)이다.

### (4) 스레드·콜백에 넘길 때 값이 「그때」 고정된다고 생각한다

```python
for i in range(3):
    pool.submit(lambda: work(i))
```

`submit` 에 넘어가는 것은 **함수 객체**이고, 그것이 실제로 돌 때 `i` 를 읽는다.\
루프가 먼저 끝나면 **셋 다 마지막 값**으로 일한다. 고침은 동작 6의 셋 중 하나다 — 이 자리에서는 `partial` 이 읽기 좋다.

### (5) `__closure__` 가 없다고 클로저가 아니라고 단정한다

기본 인자 트릭(동작 6 ①)으로 고친 함수는 `__closure__` 가 `None` 이다. 그것이 **맞다** — 자유 변수가 없으니 클로저가 아니다.\
자유 변수가 아예 없는 함수도 그렇다.

```python
# e22_no_closure.py
def plain(x):
    return x + 1


def outer():
    y = 1

    def uses_free():
        return y

    def no_free():
        return 1

    return uses_free, no_free


uses_free, no_free = outer()
print("plain.__closure__     :", plain.__closure__)
print("no_free.__closure__   :", no_free.__closure__)
print("uses_free.__closure__ 길이:", len(uses_free.__closure__))
print("co_freevars — plain    :", plain.__code__.co_freevars)
print("co_freevars — uses_free:", uses_free.__code__.co_freevars)
```

```text
===== python3 - <e22_no_closure.py =====
plain.__closure__     : None
no_free.__closure__   : None
uses_free.__closure__ 길이: 1
co_freevars — plain    : ()
co_freevars — uses_free: ('y',)
(exit 0)
```

- 모듈 수준의 `plain` 도, 바깥 함수 안에 있지만 자유 변수를 안 쓰는 `no_free` 도 **`__closure__` 가 `None`** 이다.
- **「함수 안에 있다」가 아니라 「바깥 이름을 쓴다」가 클로저의 조건**이다. `co_freevars` 가 그 판정을 그대로 보여 준다.

### (6) 셀에 담긴 것이 「값의 복사본」이라고 생각한다

동작 4에서 본 대로다 — `write` 가 고친 것을 `read` 가 **본다.**\
클로저는 **사진이 아니라 창문**이다. 값을 얼려 두고 싶으면 동작 6의 셋 중 하나로 **일부러 옮겨야** 한다.

### (7) `del` 로 난 예외를 `UnboundLocalError` 로 외운다

동작 8이 그 자리다. **`NameError` 다.**\
`UnboundLocalError` 가 `NameError` 의 하위 클래스라 `except NameError:` 로는 둘 다 잡히지만, 반대로는 안 잡힌다.

## 구현 세부사항 대 언어 보장

세 층으로 가른다.

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **언어 보장** | 레퍼런스가 정한 것 | 공식 문서 문장을 열어서 인용 |
| **CPython 구현** | 이 구현이 그렇게 하는 것 | 실행으로 확인 |
| **이 판(3.12.3)의 관찰** | 위 둘이 아닌 전부 | 「관찰」로 명기 |

### 언어 보장

| 사실 | 근거 |
|---|---|
| **쓰였는데 여기서 정의되지 않은 이름은 자유 변수다** | 실행 모델 4.2.1 — *"If a variable is used in a code block but not defined there, it is a free variable."* |
| **이름은 쓰일 때 가장 가까운 바깥 스코프에서 풀린다** | 4.2.2 — *"When a name is used in a code block, it is resolved using the nearest enclosing scope."* ← **늦은 바인딩의 근거가 이 한 줄이다** |
| 블록 안 어디서든 그 이름에 바인딩이 일어나면 **그 블록의 이름으로 취급된다** | 4.2.1 — *"If a name binding operation occurs anywhere within a code block, all uses of the name within the block are treated as references to the current block."* ← `nonlocal` 없는 `n += 1` 이 지역이 되는 이유 |
| 아예 못 찾으면 `NameError`, **지역인데 아직 안 묶였으면** `UnboundLocalError` 이고 후자는 전자의 **하위 클래스**다 | 4.2.2 — *"…an UnboundLocalError exception is raised. UnboundLocalError is a subclass of NameError."* |
| `nonlocal` 은 **가장 가까운 바깥 함수 스코프**의 이름을 가리키게 한다 | 7.13 — *"The nonlocal statement causes corresponding names to refer to previously bound variables in the nearest enclosing function scope."* |
| 함수 객체에 `__closure__`·`__defaults__` 속성이 있다 | 데이터 모델 3.2 — callable types |

★ **「루프에서 만든 함수 셋이 같은 값을 낸다」는 언어 보장이다.** 구현 세부가 아니다 —
`for` 가 새 이름을 안 만들고, 이름이 쓰일 때 풀리므로 **어떤 파이썬 구현에서도 그래야 한다.**

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| 자유 변수가 `cell` **객체**로 실체화된다 | 실행 — `<cell at 0x…: int object at 0x…>` 라는 **repr 자체가 이 구현의 것**이다 |
| `__closure__` 가 **셀들의 튜플**이고 `.cell_contents` 로 안을 읽는다 | 실행 — 데이터 모델은 속성의 존재를 적지만 **셀의 겉모습과 repr 은 구현이다** |
| 빈 셀의 표시가 `<cell at 0x…: empty>` 다 | 실행(`e22_del_cell`) — **「비었다」는 상태는 언어 쪽 사실이고, `empty` 라는 글자는 이 구현의 표시**다 |
| 예외 **문구** — *"cannot access local variable … where it is not associated with a value"* · *"cannot access free variable … in enclosing scope"* | 실행 — **예외 타입은 명세, 문구는 구현**이다. **다른 판과 대조하지 않았다** — 판이 오르면 다시 돌릴 칸이다 |
| `co_freevars`·`co_varnames` 라는 속성 이름과 그 배치 | 실행 — 코드 객체의 표면은 컴파일러가 정한다 |
| `dis` 의 명령 이름(`LOAD_DEREF`·`MAKE_CELL` 류) | **이 문서는 `dis` 를 싣지 않았다.** 싣는다면 전부 이 층이다 — 정본은 [21번](../21-scope-legb-global-nonlocal/2-summary.md) |
| `functools.partial` 객체에 `__closure__` 속성이 **아예 없다**는 것 | 실행(`e22_fix_partial`) — 문서는 「함수가 아닌 호출 가능 객체」라고만 하고 **속성 목록을 보장하지 않는다** |

★ **판정 기준 한 줄** — **「무엇이 보이나」는 언어 보장이고, 「어떤 객체로 그것을 보여 주나」는 이 구현이다.**

### 이 판(3.12.3)의 관찰

| 관찰 | 어디가 흔들리나 |
|---|---|
| `<cell at 0x7a60305d4220: int object at 0xb370c8>` | **주소 두 개가 실행마다 다르다.** 볼 것은 **셀이 하나**라는 것뿐 |
| `<cell at 0x78297df3feb0: empty>` | 같다. 볼 것은 **`empty`** 뿐 |
| `id()` 로 센 「서로 다른 셀 개수」 | **개수는 안 흔들린다.** 개수를 내려고 `id` 를 쓴 것이고 **숫자는 안 찍었다** |
| 트레이스백의 `line 12`·`line 13` | 소스가 그대로면 안 흔들린다. **소스를 손대면 바뀐다** |
| `partial` 의 타입 이름이 `partial` | 표준 라이브러리 구현이다 |

### 그래서 이렇게 적으면 틀린다

- ✗ 「루프 클로저 함정은 CPython 구현 세부사항이다」\
  → **아니다.** `for` 가 스코프를 안 만드는 것과 이름이 쓸 때 풀리는 것 **둘 다 명세**다.
- ✗ 「클로저는 바깥 값을 복사해 간다」\
  → **가리킨다.** 복사였다면 동작 4에서 `write` 뒤 `read()` 가 안 바뀌었을 것이다.
- ✗ 「세 함수의 셀 주소가 같으니 같은 셀이다」\
  → 결론은 맞지만 **근거가 흔들리는 칸**이다. `is` 로 말해라 — 그래서 `e22_cell_shared` 를 따로 돌렸다.
- ✗ 「`del` 뒤 호출하면 `UnboundLocalError` 다」\
  → **`NameError` 다.** 지역이 아니라 자유 변수이기 때문이다.
- ✗ 「`partial` 은 클로저를 만든다」\
  → **속성조차 없다.** 값은 `args` 에 있고, 물건 자체가 함수가 아니다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 판정 |
|---|---|
| 루프에서 함수·콜백·태스크를 만든다 | **값을 고정해라** — 팩토리(기본) · `partial`(밖에서 봐야 할 때) · 기본 인자(급할 때) |
| 바깥 상태를 **따라 움직이게** 하고 싶다 | 클로저 그대로가 맞다. 이것이 버그가 아니라 기능인 자리다 |
| 상태 하나 + 동작 두어 개 | 클로저(`tick`/`peek`)가 클래스보다 가볍다 |
| 상태가 셋 이상이거나 밖에서 들여다봐야 한다 | **클래스로 간다.** 클로저는 상태를 숨기는 것이 장점이자 한계다 |
| 값을 **로그에 찍어야** 한다 | `partial` — `args` 로 보인다 |
| 공개 API 의 시그니처 | 기본 인자 트릭은 **쓰지 않는다** — 호출자가 덮어쓸 수 있는 파라미터가 하나 는다 |
| 바깥 이름에 다시 묶어야 한다 | `nonlocal`. 안 쓰면 지역이 돼 `UnboundLocalError` 다 |

한 줄 규칙: **「부를 때 읽는다」가 곤란하면 값을 옮겨라 — 셀을 없애든, 가르든, 밖으로 내든.**

## 핵심 문장

- 클로저가 들고 다니는 것은 **값이 아니라 이름**이다. 값은 **부를 때** 읽는다.
- 루프에서 만든 함수들이 같은 값을 내는 이유는 「나중에 읽어서」가 아니라 「**상자가 하나여서**」다.\
  `for` 가 스코프를 만들지 않으므로 이름이 하나이고, 셀도 하나다.
- 그 증명은 주소가 아니라 **`is` 판정과 「서로 다른 셀 개수」** 로 한다 — 주소는 흔들리고 이 둘은 안 흔들린다.
- [20번](../20-mutable-default-args/2-summary.md)과 정확히 반대다 — 기본값은 **`def` 때 한 번 박히고**, 클로저는 **부를 때마다 읽는다.**\
  20번에서 함정이던 「한 번만 평가된다」가 여기서는 **고침**으로 쓰인다.
- 고침 셋은 옮기는 자리가 다르다 — 기본 인자는 셀을 **없애고**, 팩토리는 **가르고**, `partial` 은 **함수 밖으로** 낸다.
- 셀은 스코프당 하나다. 그래서 `tick`/`peek` 가 같은 상태를 보고, 바깥 함수를 다시 부르면 갈린다.
- 이름이 준비 안 된 자리는 둘이다 — 지역이면 `UnboundLocalError`, 자유 변수면 `NameError`.

## 관련 자료

- 목록: [python/syntax 주제 목록](../README.md) — 이 주제는 **22번**
- 선행: [21-scope-legb-global-nonlocal](../21-scope-legb-global-nonlocal/2-summary.md) — **이름이 어디서 풀리나가 그쪽**, 「그래서 루프 클로저가 같은 값」이 여기다.\
  `UnboundLocalError`·예외 계층·`nonlocal` 문법·컴프리헨션 스코프의 **정본은 전부 21번**이고, 여기서는 **가르기 위해서만** 인용한다.
- 정본 이웃: [20-mutable-default-args](../20-mutable-default-args/2-summary.md) — **기본값 쪽 전부가 그쪽**이다.\
  여기는 「그것과 반대다」만 세운다 — 네 칸 대비표가 이 문서의 몫이다.
- 이어지는 곳: [23-lambda-and-higher-order-functions](../23-lambda-and-higher-order-functions/2-summary.md) — **`lambda` 가 이 클로저를 만든다.**\
  [24-decorators](../24-decorators/2-summary.md) — **데코레이터는 이 클로저를 전부 쓴다**(감싼 함수를 셀에 담는다).
- 함께 보는 곳: [01-object-and-name-binding](../01-object-and-name-binding/2-summary.md) — 「이름은 객체에 붙는 꼬리표」가 이 문서의 바닥이다.\
  [19-function-argument-rules](../19-function-argument-rules/2-summary.md) — `__defaults__` 가 **어떻게 생겼나**는 그쪽, **그것이 셀과 어떻게 다른가**가 여기다.
- 공식 문서: [Resolution of names](https://docs.python.org/3.12/reference/executionmodel.html#resolution-of-names) · [`nonlocal`](https://docs.python.org/3.12/reference/simple_stmts.html#the-nonlocal-statement) · [`functools.partial`](https://docs.python.org/3.12/library/functools.html#functools.partial) · [PEP 227](https://peps.python.org/pep-0227/)

## 용어 풀이

- **클로저(closure)**: 자유 변수를 가진 함수와 그 이름이 사는 바깥 스코프를 함께 묶은 것.\
  예: `make_counter()` 가 돌려준 `tick` 은 바깥의 `n` 을 계속 본다.
- **자유 변수(free variable)**: 그 블록에서 쓰이는데 그 블록에서 정의되지는 않은 이름.\
  예: `co_freevars` 가 `('i',)` 면 `i` 를 바깥에서 빌려 쓰고 있다는 뜻이다.
- **늦은 바인딩(late binding)**: 이름이 정의 시점이 아니라 **사용 시점**에 값으로 풀리는 것.\
  예: 루프가 끝난 뒤 부르면 마지막 값이 나온다.
- **셀(cell)**: 자유 변수 하나를 담는 CPython 내부 객체.\
  예: `f.__closure__[0]` 이 셀이고 `.cell_contents` 로 안을 본다.
- **`__closure__`**: 함수 객체에 달린 셀들의 튜플. 자유 변수가 없으면 `None`.\
  예: 기본 인자 트릭으로 고친 함수는 이것이 `None` 이 된다.
- **`cell_contents`**: 셀이 **지금** 들고 있는 값.\
  예: `nonlocal` 로 바깥 이름을 바꾸면 이 값도 함께 바뀐다.
- **`co_freevars`**: 코드 객체가 들고 있는 자유 변수 이름들의 튜플.\
  예: 클로저인지 아닌지를 **이름 단위로** 판정하는 칸이다.
- **`__defaults__`**: 위치 인자 기본값들의 튜플. 20번의 정본 창이다.\
  예: `f(i=i)` 로 고치면 값이 셀에서 이쪽으로 이사한다.
- **`nonlocal`**: 가장 가까운 바깥 **함수** 스코프의 이름에 다시 묶겠다는 선언.\
  예: 없이 `n += 1` 을 쓰면 `n` 이 지역이 돼 `UnboundLocalError` 가 난다.
- **팩토리(factory)**: 값을 받아 **함수를 만들어 돌려주는 함수**.\
  예: `make(i)` 를 세 번 부르면 셀이 셋으로 갈린다.
- **`functools.partial`**: 함수에 인자 일부를 미리 붙여 둔 **호출 가능 객체**. 함수는 아니다.\
  예: `partial(identity, 0)` 의 `args` 가 `(0,)` 로 보인다.
- **정체 판정(`is`)**: 두 이름이 **같은 객체**를 가리키는지 묻는 것. 값 비교가 아니다.\
  예: 셀이 하나임을 주소 없이 증명하는 데 쓴다.

## 더 들어가면

- **셀을 가르는 방법은 사실 하나다** — **바깥 함수를 다시 부르는 것.**\
  팩토리가 그것이고, 카운터를 두 개 만드는 것도 그것이다. 기본 인자와 `partial` 은 **셀을 가르는 대신 셀을 안 쓰는** 쪽이다.
- **왜 파이썬은 회차마다 새 이름을 안 만드나** — `for` 의 대상이 **스코프가 아니라 문**이기 때문이다.\
  자바스크립트가 `let` 에서 반대를 고른 것과 대비된다. 어느 쪽도 버그가 아니라 **선택**이고, 대비를 알면 두 언어를 오갈 때 안 물린다.
- **PEP 227 이 들어오기 전**(2.1 이전)에는 중첩 함수가 바깥 지역 이름을 아예 못 봤다.\
  그 시절의 관용구가 바로 **기본 인자 트릭**이다 — 지금은 고침으로 쓰지만 원래는 **유일한 통로**였다.
- **데코레이터는 이 문서의 전부를 쓴다** — 감싼 원본 함수가 래퍼의 셀에 들어 있다.\
  [24번](../24-decorators/2-summary.md)에서 `__closure__` 를 열어 원본을 꺼내 보는 대목이 정확히 동작 2의 창이다.
