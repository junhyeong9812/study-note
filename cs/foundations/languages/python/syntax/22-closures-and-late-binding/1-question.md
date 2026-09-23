# python/syntax/22-closures-and-late-binding — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> ★ 이 주제에서는 **「무슨 값이 나오나」보다 「상자가 몇 개인가」가 답인 자리가 많다.**
> 값만 맞히고 셀 개수를 못 대면 반만 맞은 것이다.
>
> 실행 환경: `python3` **3.12.3**(Linux). 던지는 형태는 `python3 - <파일` 로 고정했다 —
> 트레이스백이 `File "<stdin>", line N` 이 되고, **실행 중 예외에는 소스 줄도 캐럿도 안 나온다**.
> ★ 출력에 `0x…` 주소가 박히는 문항이 둘 있다(2번·11번). **그 숫자는 맞힐 필요가 없다** —
> 맞혀야 할 것은 **셀이 몇 개이고 안에 무엇이 들었나**다.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. 루프에서 함수를 셋 만들어 부르면 (예측)

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

- 세 줄의 출력은 각각 무엇인가?
- 마지막 줄이 앞줄의 결과를 어떻게 설명하는가?

### 2. 같은 루프를 함수 안에 넣고 속을 들여다보면 (예측)

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

- 네 줄의 출력은 각각 무엇인가?
- 이 출력에서 **다음에 돌려도 안 변하는 칸**은 어디인가?

### 3. 세 함수의 셀을 `is` 로 재면 (예측)

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

- 다섯 줄의 출력은 각각 무엇인가?
- 이 실험이 2번보다 **근거로 강한 이유**는 무엇인가?

### 4. 「나중에 읽어서 덮어써졌다」 (왜)

- 이 설명은 왜 **반쪽**인가?
- 이 설명을 믿으면 **왜 고침을 못 찾게 되나**?

### 5. 읽는 함수와 쓰는 함수 (예측)

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

- 여섯 줄의 출력은 각각 무엇인가?
- 클로저가 「사진」이 아니라 「창문」이라는 말이 이 출력의 어느 줄에 해당하는가?

### 6. 같은 바깥 이름을 한쪽은 기본값으로, 한쪽은 몸통에서 (예측)

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

- 다섯 줄의 출력은 각각 무엇인가?
- 마지막 줄이 왜 그 값인가?

### 7. 함수를 두 번 만들면 어느 쪽이 갈리나 (연결)

- [20번](../20-mutable-default-args/2-summary.md)의 **기본 인자**와 이 주제의 **클로저**를
  ①값이 정해지는 때 ②값이 사는 곳 ③바깥 이름을 다시 묶었을 때 ④함수를 두 번 만들었을 때
  **네 칸으로 갈라** 적을 수 있는가?
- 네 번째 칸에서 **기본값 쪽은 하나이고 클로저 쪽은 둘로 갈리는** 이유는 무엇인가?

### 8. 루프 변수를 기본 인자로 받으면 (예측)

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

- 다섯 줄의 출력은 각각 무엇인가?
- 20번에서 **함정**이던 성질이 여기서 **고침**이 되는 지점은 어디인가?

### 9. 고침 셋이 각각 옮기는 것 (연결)

- 기본 인자 트릭 · 팩토리 · `functools.partial` 은 **각각 무엇을 어디로 옮기는가**?
- 셋 중 **클로저를 없애지 않고 고치는 것**은 어느 것이며, 그것이 남기는 흔적은 무엇인가?
- 셋 중 **함수가 아닌 것**은 어느 것인가?

### 10. 카운터의 `tick` 과 `peek` (왜)

- `tick()` 을 세 번 부른 뒤 `peek()` 가 그 값을 보는 이유는 무엇인가?
- `make_counter(100)` 으로 **두 번째 카운터**를 만들면 첫 카운터는 어떻게 되며, 그 이유는 무엇인가?
- 이 구조가 **팩토리 고침**(`make(i)` 를 세 번 부르는 쪽)과 같은 그림인 이유는 무엇인가?

### 11. 이름이 준비 안 된 두 자리 (경계)

- `nonlocal` 없이 바깥 이름에 `n += 1` 을 하면 **무슨 예외**가 나는가?
- 바깥 함수가 그 지역 변수를 `del` 한 뒤 안쪽 함수를 부르면 **무슨 예외**가 나는가?
- 둘은 **왜 다른 예외**이고, 두 예외 클래스는 서로 어떤 관계인가?
- `del` 뒤에 `__closure__` 를 찍으면 **튜플이 비어 있는가, 셀이 남아 있는가**?

### 12. 무엇이 구현이고 무엇이 언어 보장인가 (경계)

- 「루프에서 만든 함수 셋이 같은 값을 낸다」는 **언어 보장**인가 **CPython 구현 세부사항**인가?
- `__closure__` · `cell_contents` · `<cell at 0x…: empty>` · 예외 **문구**는 각각 어느 층인가?
- 「이 주제의 판정 기준」을 **한 문장**으로 말할 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
