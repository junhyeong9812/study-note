# python/syntax/22-closures-and-late-binding — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> [1-question.md](1-question.md)의 번호와 **1:1**로 대응한다. 질문 12개 = 답 12개.
>
> 이 파일의 모든 출력은 `python3` **3.12.3**(Linux)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> 던지는 형태는 `python3 - <파일` 로 고정했다 — 트레이스백이 `File "<stdin>", line N` 이 되고,
> **실행 중 예외에는 소스 줄도 캐럿도 안 나온다**(11번 답의 두 블록이 그렇다).
>
> ★ **흔들리는 칸** — `<cell at 0x…>` 의 주소와 `id()` 숫자는 **돌릴 때마다 달라진다.**
> 이 파일에서 주소가 박히는 블록은 **2번 답과 11번 답 둘뿐**이고,
> 그 자리에서 **대조할 것은 주소가 아니라 「셀이 하나라는 것」과 「셀이 비었다는 것」이다.**
> ★ **안 흔들리는 칸** — 예외 **타입**과 **메시지 본문**, `File "<stdin>", line N`, **셀 개수**,
> `is` 판정, `co_freevars`·`co_varnames`, `__defaults__` 값, `(exit N)`.

## 정답

### 1. 셋 다 `2` 를 낸다 — 루프가 이름을 새로 안 만들기 때문이다 (예측)

**출력**

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

**왜 그런가**

- 함수는 **정말 세 개** 만들어졌다(`len(makers)` 가 `3`). 회차마다 새 함수 객체가 생긴 것은 맞다.
- 그런데 셋이 보는 이름은 **`i` 하나**다. `for` 는 **스코프를 만들지 않는다** — 같은 이름에 0·1·2 를 차례로 다시 묶었을 뿐이다.
- 마지막 줄이 그 증거다. **루프가 끝난 뒤에도 `i` 가 살아 있고 값이 `2`** 다.\
  회차마다 새 이름이 생겼다면 루프 밖에서 `i` 를 못 읽었을 것이다.
- 리스트 컴프리헨션 `[m() for m in makers]` 는 **루프가 다 끝난 뒤에** 돌았다. 그때 셋 다 「지금 `i` 가 뭐냐」를 묻는다 → `2`.

```text
   for i in range(3):        이름 쪽에서 나는 일
   ------------------        ---------------------------
     회차 0                    i 에 0 을 묶는다
     회차 1                    같은 i 에 1 을 다시 묶는다
     회차 2                    같은 i 에 2 를 다시 묶는다
   루프 끝                     i 는 지워지지 않는다 (= 2)
```

**기대와 어긋나는 지점**

읽는 사람은 `def maker()` 를 「그 회차의 `i` 를 **찍어 둔** 함수」로 읽는다.\
실제 뜻은 「`i` 라는 **이름을 읽는** 함수」다. 찍어 두는 일은 아무도 안 했다.

★ 이 판은 **모듈 수준**이라 `i` 는 전역 이름이다. 자유 변수가 아니므로 **아직 클로저가 아니다** —
셀 이야기는 2번부터다. 결과가 같은 이유는 **양쪽 다 이름이 하나뿐이기 때문**이다.

### 2. 셀이 하나이고 그 안에 `2` 가 들어 있다 (예측)

**출력**

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

**왜 그런가**

★ **대조할 것은 주소가 아니라 「셀이 하나」라는 것이다.**
`0x7a60305d4220` 과 `0xb370c8` 은 **돌릴 때마다 달라진다.** 근거로 쓸 칸은 나머지 셋이다.

| 안 흔들리는 칸 | 값 | 무엇을 말하나 |
|---|---|---|
| `co_freevars` | `('i',)` | 이 함수는 `i` 를 **자기 것으로 안 가지고 빌려 쓴다** |
| `__closure__` 의 길이 | 1 | 빌려 쓰는 이름이 하나 → 셀도 하나 |
| `cell_contents` | `2` | 그 셀이 **지금** 들고 있는 값 |

- 이번에는 `i` 가 `build` 의 **지역 이름**이라 안쪽 `f` 의 **자유 변수**가 됐다. 1번과 갈리는 자리가 여기다.
- `__closure__` 는 **셀들의 튜플**이다. 자유 변수 하나당 셀 하나가 들어간다.
- `cell_contents` 가 `2` 인 것이 결과가 `[2, 2, 2]` 인 이유 그 자체다 — **함수가 값을 가진 게 아니라 셀을 가리킨다.**

```text
   build() 프레임
   +-----------------------+
   |    i  ->  [ 셀 : 2 ]  |
   +-----------------------+
         ^       ^       ^
        f0      f1      f2     셋 다 __closure__[0] 가 이 셀
```

★ `__closure__`·`cell_contents` 는 **CPython 구현**이다(12번 답). 언어가 보장하는 것은 「바깥 이름을 본다」까지다.

### 3. `is` 가 전부 `True` 이고 서로 다른 셀은 `1` 개다 (예측)

**출력**

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

**왜 2번보다 근거로 강한가**

- 2번은 **주소를 찍는다.** 주소는 실행마다 바뀌므로 「두 주소가 같다」를 문서에 근거로 실을 수 없다.
- 3번은 **`is` 로 판정**하고 **개수만 센다.** 둘 다 실행마다 안 변한다 — 그대로 근거가 된다.
- `셀 개수: 3` 과 `서로 다른 셀이 몇 개인가: 1` 이 나란히 있는 것이 핵심이다.\
  **셀 객체를 세 번 꺼냈는데 서로 다른 것은 하나**다.

```text
   틀린 그림 (이렇게 생각하기 쉽다)        맞는 그림
   f0 -> [0]  f1 -> [1]  f2 -> [2]        f0 ─┐
   "나중에 읽어서 덮어써졌다"               f1 ─┼──> [ 2 ]    셀 하나
                                           f2 ─┘
   -> 상자가 셋이면 값도 셋이었을 것이다    -> 값이 하나인 것은 상자가 하나이기 때문
```

★ `id()` 를 쓰긴 했지만 **숫자를 안 찍고 개수만 냈다.** 흔들리는 칸을 근거로 쓰지 않으려는 설계다.

### 4. 반쪽인 이유 — 상자가 셋이었다면 나중에 읽어도 값은 셋이다 (왜)

**답**

- 「나중에 읽는다」는 **맞는 관찰이지만 원인이 아니다.** 원인은 「**읽을 상자가 하나뿐**」인 것이다.
- 반증이 3번 답에 있다 — **상자를 셋으로 가르면**(팩토리) 나중에 읽어도 `[0, 1, 2]` 가 나온다.\
  「나중에 읽는다」는 그대로인데 결과가 달라지므로, 그것만으로는 설명이 안 된다.

**왜 고침을 못 찾게 되나**

| 진단 | 거기서 나오는 처방 | 실제로 되나 |
|---|---|---|
| 「나중에 읽어서 덮어써졌다」 | **더 일찍 읽게 하자** | 그런 수단이 **없다** — 함수 몸통은 부를 때만 돈다 |
| 「상자가 하나다」 | 상자를 **없애거나 가르자** | 된다 — 기본 인자·팩토리·`partial` 셋이 전부 그것이다 |

★ **진단이 틀리면 처방 목록이 통째로 안 보인다.** 이 주제에서 오해가 비싼 이유가 여기다.

★ 「늦은 바인딩」이라는 이름 자체가 오해를 돕는다. 정확히는 **「늦게 읽는다 + 읽을 곳이 하나다」** 두 가지가 겹친 것이고,
**고칠 수 있는 쪽은 뒤엣것**이다.

### 5. `write` 뒤에 `read()` 와 `cell_contents` 가 함께 바뀐다 (예측)

**출력**

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

**왜 그런가**

- ① 시점에는 둘 다 `처음`, ② 시점에는 둘 다 `나중`이다. **같은 것을 두 창으로 본 것**이다.
- `cell is read.__closure__[0]` 이 **`True`** — 셀을 **갈아 끼운 게 아니라 안을 고쳤다.**
- `read.__closure__[0] is write.__closure__[0]` 이 **`True`** — 서로 다른 함수인데 **같은 셀**이다.\
  → 클로저는 함수에 딸린 것이 아니라 **스코프에 딸린 것**이고, 그 스코프를 공유하는 함수들이 셀을 나눠 쓴다.

**「사진이 아니라 창문」은 어느 줄인가**

- `② read() : 나중` 이 그 줄이다.\
  `read` 는 `build` 가 끝난 뒤에 만들어진 게 아니다. **`build` 가 끝난 지 한참 뒤에 바뀐 값을 본다.**
- 사진이었다면 `read()` 는 끝까지 `처음`이었을 것이다.

★ 바깥 이름에 **다시 묶는** 일은 `nonlocal` 이 있어야 한다.
그 규칙의 정본은 [21번](../21-scope-legb-global-nonlocal/2-summary.md)이고, 여기서는 **셀이 공유된다는 결과**만 본다.

### 6. 기본값은 `10` 그대로, 클로저는 `99` 로 따라간다 (예측)

**출력**

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

**왜 그런가**

- `by_default(v=limit)` 는 **`def` 문이 도는 순간** `limit` 을 읽어 기본값으로 박았다. 그래서 `__defaults__` 가 `(10,)` 이다.
- `by_closure()` 는 `limit` 을 **몸통에서** 읽는다. 자유 변수이므로 셀을 가리키고, `rebind(99)` 가 그 셀을 고치자 **따라 바뀐다.**
- `rebind` 는 `nonlocal limit` 으로 **같은 셀**에 다시 묶었다. `by_closure` 와 `rebind` 가 한 셀을 공유한다(5번 답과 같은 구조).

**마지막 줄이 왜 `None` 인가**

- `by_default` 는 `limit` 을 **기본값 식에서만** 썼다. 그 식은 `build` 의 코드이지 `by_default` 의 몸통이 아니다.
- 그래서 `by_default` 의 몸통에는 자유 변수가 **없다** → 셀이 없고 `__closure__` 가 `None` 이다.
- ★ **같은 바깥 이름을 참조했는데 한쪽은 셀이 없고 한쪽은 셀이 있다.** 「값이 어디에 사는가」가 이 한 줄로 갈린다.

```text
   기본 인자 (20번이 정본)                클로저 (여기)
   def 문이 돌 때 한 번 계산              부를 때마다 셀을 읽는다
   +----------------------+               +---------------------+
   | by_default           |               | by_closure          |
   | __defaults__ -> (10,)|               | __closure__ -> [셀] |
   | __closure__  -> None |               +---------------------+
   +----------------------+                          |
             |                                       |
        값이 박혔다                              이름이 이어졌다
   rebind(99) 뒤에도 10                      rebind(99) 뒤에는 99
```

★ **기본값 쪽의 정본은 [20번](../20-mutable-default-args/2-summary.md)이다.** 여기서 본 것은 **대비**뿐이다.

### 7. 네 칸 대비 — 마지막 칸에서 갈린다 (연결)

**답 — 네 칸**

| | 기본 인자([20번](../20-mutable-default-args/2-summary.md)) | 클로저(22번) | 어느 실험이 실증하나 |
|---|---|---|---|
| 값이 정해지는 때 | `def` 문이 돌 때 **한 번** | 함수를 **부를 때마다** | 6번 답 — `rebind(99)` 뒤 `10` 대 `99` |
| 어디에 사는가 | `__defaults__` 튜플 | `__closure__` 의 셀 | 6번 답 — `(10,)` 대 셀 내용 `99`, 그리고 `__closure__` 가 `None` |
| 바깥 이름을 다시 묶으면 | 안 따라간다 | 따라간다 | 6번 답 — 위 두 줄이 **한 실행**이다 |
| 함수를 두 번 만들면 | 기본값 객체는 **하나** | 셀이 **둘로 갈린다** | 아래 출력 — `is` 가 `True` 대 `False` |

**네 번째 칸의 출력**

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

**왜 한쪽은 하나이고 한쪽은 둘인가**

- 기본값은 **함수 객체에 달린다.** 함수는 하나이므로 기본값도 하나다 — 몇 번을 불러도 그 리스트다.
  - 첫 줄이 `['x', 'x']` **두 번**인 것이 그 증거다. `print` 의 인자 둘이 왼쪽부터 평가되며 **같은 리스트에 두 번 붙었고**,
    찍을 때는 둘 다 **그 같은 리스트**를 본다.
  - 다음 줄의 `is` 판정이 못 박는다 — **`True`**.
- 셀은 **바깥 함수의 호출에 달린다.** `make_by_closure()` 를 두 번 불렀으니 **프레임이 둘, `bag` 이 둘, 셀이 둘**이다.
  - `add1.__closure__[0] is add2.__closure__[0]` 이 **`False`** 이고, 둘 다 `['x']` 로 서로를 오염시키지 않는다.

★ **한 문장으로** — 기본값은 **함수당 하나**, 셀은 **바깥 함수의 호출당 하나**다.\
그래서 셀을 가르는 유일한 방법이 「바깥 함수를 다시 부르는 것」이 된다(9번·10번 답).

### 8. `[0, 1, 2]` 가 나오고 `__closure__` 가 `None` 이 된다 (예측)

**출력**

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

**왜 그런가**

- `def f(i=i)` 의 기본값 식 `i` 는 **`def` 문이 실행되는 그 회차에** 평가된다. 회차마다 그때의 값이 박힌다 → `(0,)`·`(1,)`·`(2,)`.
- 그래서 `f` 의 몸통이 읽는 `i` 는 **자기 파라미터**다. 바깥 `i` 가 아니다.
- `co_freevars` 가 **비었고** `co_varnames` 에 `i` 가 있다. **이름이 자유 변수에서 파라미터로 이사했다.**
- 그 결과 `__closure__` 가 **`None`** 이다 — **셀이 아예 없어졌다.**

```text
   고치기 전                        고친 뒤
   co_freevars  ('i',)              co_freevars  ()
   co_varnames  ()                  co_varnames  ('i',)
   __closure__  (셀 1개,)           __closure__  None
   __defaults__ None                __defaults__ (0,) (1,) (2,)
   -> 셀 하나를 셋이 공유            -> 셀이 없고 값이 함수마다 박혔다
```

**20번에서 함정이던 성질이 여기서 고침이 되는 지점**

- 그 성질은 하나다 — **「기본값은 `def` 문을 실행할 때 한 번 평가된다」.**
- [20번](../20-mutable-default-args/2-summary.md)에서는 그것이 **가변 객체**에 걸려 「호출 사이에 상태가 샌다」가 됐다.
- 여기서는 그것이 **루프 변수**에 걸려 「회차마다 값이 고정된다」가 된다. **같은 기계, 반대 효과**다.
- ★ 그래서 두 주제를 나란히 둔다. **「한 번만 평가된다」가 함정인지 고침인지는 그 자리가 정한다.**

**대가**

`f(i=i)` 는 시그니처에 파라미터를 하나 노출한다 — 호출자가 `f(5)` 로 **덮어쓸 수 있다.**\
내부 함수에는 괜찮고, 공개 API 에는 권하지 않는다.

### 9. 없애기 · 가르기 · 밖으로 내기 (연결)

**답 — 셋이 옮기는 자리**

| 고침 | 무엇을 어디로 옮기나 | 남는 흔적 |
|---|---|---|
| 기본 인자 `f(i=i)` | 셀을 **없애고** 값을 `__defaults__` 로 | `__closure__` 가 `None` · `co_freevars` 가 빔 |
| 팩토리 `make(i)` | 셀을 **가른다**(없애지 않는다) | `__closure__` 가 살아 있고 **서로 다른 셀 N개** |
| `partial(f, i)` | 값을 **함수 밖 객체**에 담는다 | 함수가 아님 · `args` 에 보임 · `__closure__` **속성 자체가 없음** |

**클로저를 없애지 않고 고치는 것 — 팩토리**

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

- **서로 다른 셀 개수가 `3`** 이다. 3번 답에서 `1` 이던 그 칸이다 — **같은 칸을 같은 방법으로 쟀다.**
- `셀 0 is 셀 1` 이 **`False`**. 주소를 안 보고 판정한 것도 그대로다.
- `make(i)` 를 세 번 불렀으므로 **프레임이 셋**이고, 프레임마다 자기 `i` 와 자기 셀을 가진다.

```text
   루프 안 def                      make(i) 를 세 번 호출
   build 프레임 1개                 make 프레임 3개
      i -> [ 2 ]                      i -> [0]   i -> [1]   i -> [2]
      ^   ^   ^                       ^          ^          ^
     f0  f1  f2                       f0         f1         f2
   서로 다른 셀 1개                  서로 다른 셀 3개
```

★ 그래서 교훈은 「클로저는 위험하다」가 아니라 「**셀의 개수를 내가 정한다**」다.

**함수가 아닌 것 — `partial`**

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

- 타입이 `partial` 이다. `callable()` 은 `True` 라 부르는 데 지장이 없지만 **함수 객체가 아니다.**
- `hasattr(fns[0], "__closure__")` 가 **`False`** — 클로저가 아닌 정도가 아니라 **속성 자체가 없다.**
- 고정한 값은 `args` 에 **튜플로 보인다**(`(0,)`·`(1,)`·`(2,)`). 감싼 대상은 `func` 로 꺼낸다.

```text
   클로저                                partial
   함수 ─┬─> __closure__ ─> 셀           partial 객체 ─┬─> func -> identity
         └─> 코드                                       └─> args -> (0,)
   값이 함수 「안쪽」에 붙는다             값이 함수 「바깥」 객체에 붙는다
```

★ 셋 중 **유일하게 밖에서 값을 보기 쉬운** 형태다 — 로그·디버깅에서 이긴다.\
대신 **함수임을 전제한 코드와 어긋난다**([24번](../24-decorators/2-summary.md)에서 걸린다).

### 10. 둘이 같은 셀을 보기 때문이다 (왜)

**출력**

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

**왜 `peek()` 가 `tick` 의 결과를 보나**

- `tick` 과 `peek` 는 **같은 `make_counter()` 호출**에서 만들어졌다. 둘의 자유 변수 `n` 은 **그 프레임의 이름 하나**다.
- 그래서 `tick.__closure__[0] is peek.__closure__[0]` 이 **`True`** 다. 5번 답의 `read`/`write` 와 **같은 구조**다.
- `tick` 은 `nonlocal n` 으로 그 셀을 **고치고**, `peek` 는 같은 셀을 **읽는다.** 세 번 올린 `3` 이 그대로 보인다.

**두 번째 카운터를 만들면**

- `make_counter(100)` 은 **새 호출**이라 **새 프레임·새 `n`·새 셀**이다. 그래서 `101`·`102` 로 자기 길을 간다.
- 첫 카운터의 `peek()` 는 **`3`** 그대로다. `tick.__closure__[0] is tick2.__closure__[0]` 이 **`False`** 인 것이 그 이유다.

```text
   make_counter() 프레임                make_counter(100) 프레임
   +------------------+                 +--------------------+
   |   n  ->  [ 3 ]   |                 |   n  ->  [ 102 ]   |
   +------------------+                 +--------------------+
        ^         ^                            ^         ^
      tick      peek                        tick2     peek2
     (쓴다)     (읽는다)                    is 가 False — 남남이다
```

**팩토리와 같은 그림인 이유**

- 둘 다 **「바깥 함수를 다시 부르면 셀이 갈린다」** 하나로 설명된다.
- 9번 답의 `make(i)` 를 세 번 부른 것과, 여기서 `make_counter` 를 두 번 부른 것은 **같은 일**이다.
- ★ 그래서 **버그를 고치는 수단과 상태를 만드는 수단이 같은 기계**다. 클로저를 「피할 것」으로 외우면 이 쓸모가 안 보인다.

### 11. 하나는 `UnboundLocalError`, 다른 하나는 `NameError` 다 (경계)

**출력 — `nonlocal` 없이 `n += 1`**

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

**출력 — 바깥에서 `del v` 한 뒤 호출**

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

**왜 다른 예외인가**

```text
   "이름이 준비 안 됐다" 는 두 자리에서 난다

   ① 지역인데 아직 안 묶였다       ->  UnboundLocalError
      (nonlocal 없이 n += 1)           "cannot access local variable 'n'
                                        where it is not associated with a value"

   ② 자유 변수인데 셀이 비었다     ->  NameError
      (바깥에서 del v)                 "cannot access free variable 'v'
                                        ... in enclosing scope"
```

- ①은 **대입이 있어서** `n` 이 그 블록의 **지역 이름**이 된 경우다.\
  레퍼런스가 그대로 적는다 — *"If a name binding operation occurs anywhere within a code block,
  all uses of the name within the block are treated as references to the current block."*
- ②는 `v` 가 **지역이 아니라 자유 변수**인 경우다. 그래서 「local」이 아니라 「free variable … in enclosing scope」라고 말한다.
- 레퍼런스가 두 경우를 나눠 규정한다 — *"When a name is not found at all, a NameError exception is raised.
  If the current scope is a function scope, and the name refers to a local variable that has not yet been bound to a value
  at the point where the name is used, an UnboundLocalError exception is raised."*

**두 클래스의 관계**

- *"UnboundLocalError is a subclass of NameError."* — **`UnboundLocalError` 가 `NameError` 의 하위 클래스**다.
- 그래서 `except NameError:` 는 **둘 다** 잡고, `except UnboundLocalError:` 는 **②를 못 잡는다.**
- ★ 예외 **계층의 정본은 [21번](../21-scope-legb-global-nonlocal/2-summary.md)이다.** 여기서는 **②와 가르기 위해서만** 인용했다.

**`del` 뒤 `__closure__` 는 — 셀이 남아 있다**

- 출력이 `(<cell at 0x…: empty>,)` 다. **튜플이 빈 것이 아니라 셀이 남고 안만 비었다.**
- 셀은 **컴파일 시점에 정해진 구조**다. `del` 은 그 안의 값을 지울 뿐 구조를 바꾸지 않는다.
- 두 트레이스백 모두 `File "<stdin>", line N` 이 **두 줄**이다(부른 자리 + 터진 자리). 이 칸은 안 흔들린다.

### 12. 동작은 언어 보장, 보여 주는 물건은 CPython 구현 (경계)

**답 — 「루프 클로저가 같은 값을 낸다」는 언어 보장이다**

근거가 둘 다 레퍼런스에 있다.

| 사실 | 근거 |
|---|---|
| `for` 가 새 이름을 만들지 않는다(= 한 블록 안의 바인딩은 그 블록의 이름 하나) | 실행 모델 4.2.1 — *"If a name binding operation occurs anywhere within a code block, all uses of the name within the block are treated as references to the current block."* |
| 이름은 **쓰일 때** 가장 가까운 바깥 스코프에서 풀린다 | 4.2.2 — *"When a name is used in a code block, it is resolved using the nearest enclosing scope."* |
| 쓰였는데 여기서 정의 안 된 이름 = 자유 변수 | 4.2.1 — *"If a variable is used in a code block but not defined there, it is a free variable."* |
| 아예 못 찾으면 `NameError`, 지역인데 안 묶였으면 `UnboundLocalError`(후자는 전자의 하위 클래스) | 4.2.2 |
| `nonlocal` 이 가장 가까운 바깥 **함수** 스코프의 이름을 가리키게 한다 | 7.13 |
| 함수 객체에 `__closure__`·`__defaults__` 속성이 있다 | 데이터 모델 3.2 |

**각각 어느 층인가**

| 것 | 층 | 왜 |
|---|---|---|
| 「세 함수가 같은 값을 낸다」 | **언어 보장** | 위 두 줄에서 따라 나온다. 어떤 구현에서도 그래야 한다 |
| `__closure__` 라는 속성이 **있다** | **언어 보장** | 데이터 모델이 callable types 에 싣는다 |
| 그 안이 `cell` **객체**이고 `.cell_contents` 로 읽는다 | **CPython 구현** | 셀의 **겉모습과 repr 은 이 구현의 것**이다 |
| `<cell at 0x…: empty>` 라는 표시 | **CPython 구현** | 「비었다」는 상태는 언어 쪽 사실이고, **`empty` 라는 글자**는 표시 방식이다 |
| 예외 **타입**(`NameError`·`UnboundLocalError`) | **언어 보장** | 4.2.2 가 종류를 규정한다 |
| 예외 **문구** | **CPython 구현** | 규정된 적이 없다 — **판이 오르면 다시 돌려야 할 칸**이다(이 노트는 3.12.3 하나만 돌렸다) |
| `co_freevars`·`co_varnames` 의 이름과 배치 | **CPython 구현** | 코드 객체의 표면은 컴파일러가 정한다 |
| `partial` 에 `__closure__` 속성이 **없다** | **CPython 구현** | 문서는 「호출 가능 객체」라고만 하고 속성 목록을 보장하지 않는다 |
| `<cell at 0x…>` 의 주소 · `id()` 숫자 | **이 판의 관찰** | 같은 판에서도 **실행마다 바뀐다** |

**자유 변수가 없으면 클로저도 없다 — 판정의 바닥**

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

- 모듈 수준의 `plain` 도, 바깥 함수 **안에** 있지만 바깥 이름을 안 쓰는 `no_free` 도 `__closure__` 가 **`None`** 이다.
- **「함수 안에 있다」가 아니라 「바깥 이름을 쓴다」가 클로저의 조건**이다. `co_freevars` 가 그 판정을 이름 단위로 보여 준다.
- 8번 답에서 기본 인자 트릭으로 고친 함수가 `None` 이던 것도 같은 이유다 — **고친 결과 클로저가 아니게 된 것**이다.

**판정 기준 한 문장**

★ **「무엇이 보이나」는 언어 보장이고, 「어떤 객체로 그것을 보여 주나」는 이 구현이다.**

---

## 실행 검증

이 문서와 [2-summary.md](2-summary.md)에 실린 출력은 전부 아래처럼 돌려서 얻었다.\
블록은 손으로 옮겨 적지 않고 **캡처 파일을 그대로 끼워 넣었다.**

| 무엇을 | 어떻게 | 몇 번 | 어디에 |
|---|---|---|---|
| 판 확인(`sys.version_info`·구현·플랫폼) | `python3 - <파일` · 3.12.3 | 1회 | 2-summary 동작 방식 머리 |
| 모듈 수준 루프 클로저 | 〃 | 1회 | 1번 답 |
| 함수 안 루프 + `__closure__`·`cell_contents`·`co_freevars` | 〃 | 1회 | 2번 답 |
| 셀 공유 `is` 판정 3쌍 + 서로 다른 셀 개수 | 〃 | 1회 | 3번 답 |
| 셀의 생존 — `read`/`write` 가 같은 셀 | 〃 | 1회 | 5번 답 |
| 기본값 대 클로저 — `rebind` 전후 | 〃 | 1회 | 6번 답 |
| 기본값 대 클로저 — 가변 객체·두 번 만들기 | 〃 | 1회 | 7번 답 |
| 고침 ① 기본 인자 트릭 | 〃 | 1회 | 8번 답 |
| 고침 ② 팩토리 — 셀 3개 | 〃 | 1회 | 9번 답 |
| 고침 ③ `functools.partial` | 〃 | 1회 | 9번 답 |
| `nonlocal` 카운터 2대 | 〃 | 1회 | 10번 답 |
| `nonlocal` 없는 `n += 1`(`UnboundLocalError`) | 〃 | 1회 | 11번 답 |
| `del` 뒤 빈 셀(`NameError`) | 〃 | 1회 | 11번 답 |
| 자유 변수 없는 함수 2종 | 〃 | 1회 | 12번 답 |

**구현 의존 항목 — 버전이 오르면 다시 돌려야 할 것**

- **예외 문구 둘**(11번 답) — *"cannot access local variable …"* · *"cannot access free variable … in enclosing scope"*.\
  **타입은 명세, 문구는 구현**이다. 다른 판과 대조하지 않았으므로 **이 판의 문장으로만** 읽는다.
- **셀의 repr**(2번·11번 답) — `<cell at 0x…: int object at 0x…>` · `<cell at 0x…: empty>`.\
  주소는 **실행마다** 바뀌고, 형식 자체도 구현이 정한다.
- **`co_freevars`·`co_varnames` 의 배치**(2번·8번 답) — 컴파일러가 정한다.
- **`partial` 의 타입 이름과 속성 목록**(9번 답) — 표준 라이브러리 구현이다.
- **트레이스백의 `line N`**(11번 답) — 소스를 손대면 바뀐다. 소스가 그대로면 안 흔들린다.

**안 흔들리는 칸 — 재대조에서 한 글자도 달라지면 「고칠 것」이다**

`is` 판정 전부 · 서로 다른 셀 **개수** · `co_freevars` 값 · `__defaults__` 값 ·
예외 **타입**과 **메시지 본문** · `File "<stdin>", line N` · `(exit N)`.
