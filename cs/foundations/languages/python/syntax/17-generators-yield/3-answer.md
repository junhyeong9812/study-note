# python/syntax/17-generators-yield — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> [1-question.md](1-question.md)의 번호와 **1:1**로 대응한다. 질문 8개 = 답 8개.
>
> 이 파일의 모든 출력은 `python3` **3.12.3** 에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> `<generator object ... at 0x...>` 의 **주소 숫자**만 실행할 때마다 달라진다.

## 정답

### 1. 출력 순서가 답이다 (예측)

**출력**

```text
호출 직전
호출 직후 -> <generator object steps at 0x7c6faebd0b80>
   A: 시작
next 1 -> 1
   B: 1 과 2 사이
next 2 -> 2
   C: 끝내는 중
StopIteration, value = None
```

**한 줄씩 왜**

- `호출 직후` 가 **`A: 시작` 보다 먼저** 찍혔다.\
  → `steps()` 호출은 몸통을 한 줄도 돌리지 않았다. 제너레이터 객체만 만들었다.\
  문서 표현 — "제너레이터 함수를 호출하면 제너레이터라는 이터레이터를 돌려준다. **실행은 제너레이터의 메서드가 불릴 때 시작된다.**"
- 첫 `next(g)` 가 `A: 시작` 을 찍고 **`yield 1` 에서 멈춰** 1을 돌려줬다.\
  그래서 `A: 시작` 이 `next 1 -> 1` **보다 먼저**다 — 값이 나오기 전에 그 앞의 코드가 돈 것이다.
- 둘째 `next(g)` 는 `A: 시작` 을 **다시 안 찍었다.**\
  → 처음부터가 아니라 **멈춘 자리에서** 이어 갔다는 증거.
- 셋째 `next(g)` 는 `C: 끝내는 중` 을 찍고 함수 끝에 닿아 `StopIteration` 을 던졌다.
- `return` 문이 없으므로 `StopIteration.value` 는 `None`.

```text
 print("호출 직전")            호출 직전
 g = steps()                  (몸통 안 돎)
 print("호출 직후", g)         호출 직후 -> <generator ...>
 next(g) ─┬─ A: 시작 찍음
          └─ yield 1 에서 멈춤 -> 1        next 1 -> 1
 next(g) ─┬─ 멈춘 자리에서 재개, B 찍음
          └─ yield 2 에서 멈춤 -> 2        next 2 -> 2
 next(g) ─┬─ 재개, C 찍음
          └─ 함수 끝 -> StopIteration      StopIteration, value = None
```

**여기서 틀리는 자리**

"함수를 불렀으니 안이 돌았겠지"가 틀린다.\
제너레이터 함수 안에 로그·검증·파일 열기를 넣어 두면, **아무도 소비하지 않는 한 영영 안 돈다.**

### 2. 프레임이 살아 있다는 증거 (예측)

**출력**

```text
GEN_CREATED
10 GEN_SUSPENDED 7 {'total': 10, 'i': 10}
30 GEN_SUSPENDED 7 {'total': 30, 'i': 20}
60 GEN_SUSPENDED 7 {'total': 60, 'i': 30}
GEN_CLOSED None
```

**무엇이 무엇을 증명하나**

| 관찰 | 증명하는 것 |
|---|---|
| 첫 줄이 `GEN_CREATED` | 만들기만 하면 아직 아무것도 안 돈 상태다 |
| `f_lineno` 가 **세 번 다 `7`** | 7번 줄은 `yield total`. **멈추는 자리는 언제나 `yield`** 다 |
| `f_locals` 의 `total` 이 10 → 30 → 60 | 매번 처음부터 돌았다면 늘 10 이어야 한다. **이어졌다** |
| `f_locals` 의 `i` 가 10 → 20 → 30 | `for` 루프가 **어디까지 진행됐는지**도 프레임에 남아 있다 |
| 마지막 `gi_frame` 이 `None` | 끝난 제너레이터는 프레임을 **놓아 준다** |

문서가 "중단"의 뜻을 그대로 규정한다 — "**모든 지역 상태가 유지된다**는 뜻이다. 지역 변수의 현재 바인딩, 명령 포인터, 내부 평가 스택, 예외 처리 상태까지."

**그림으로**

```text
호출자 쪽                       제너레이터가 들고 있는 프레임
-----------------------         --------------------------------
g = counter()                   +------------------------------+
  GEN_CREATED                   | total = ?   i = ?            |
                                | 커서: 시작 전                 |
                                +------------------------------+
   next(g) ── 제어권 ──>         4  total = 0
                                5  for i in (10,20,30):
                                6      total += i     -> 10
                                7      yield total  ← 멈춤
   v = 10  <── 값 + 제어권 ──    +------------------------------+
  GEN_SUSPENDED                 | total = 10  i = 10           |
                                | 커서: 7번 줄                  |
                                +------------------------------+
   next(g) ── 제어권 ──>         7 다음부터 재개
                                5      다음 i 를 꺼낸다 -> 20
                                6      total += i     -> 30
                                7      yield total  ← 또 멈춤
   v = 30  <──                  | total = 30  i = 20           |
```

**한 문장**

**"멈춘다"는 "버리지 않는다"는 뜻이다.**\
보통 함수는 `return` 할 때 작업 공간을 버리지만, 제너레이터는 그것을 들고 다음 `next()` 를 기다린다.

**그 대가**

끝내지 않은 제너레이터는 프레임을 **계속 잡고 있다.**\
그 안에서 파일을 열었으면 파일도 안 닫힌 채 남는다.

### 3. 소진 — 에러가 아니라 빈 결과 (예측)

**출력**

```text
['a', 'b']
[]
```

**왜 예외가 아닌가**

- `list(g)` 는 `g` 가 `StopIteration` 을 낼 때까지 `next` 를 반복한다.
- 첫 `list(g)` 가 끝나면 `g` 는 **`GEN_CLOSED`** 다. 프레임은 이미 버려졌다.
- 둘째 `list(g)` 는 `next` 를 한 번 부르고 **곧바로 `StopIteration`** 을 받는다.\
  `list` 입장에서는 "처음부터 낼 것이 없는 이터레이터"와 **구별되지 않는다.** 그래서 `[]` 다.
- 되감기(rewind)가 없다. 상태도가 한 방향이다.

```text
   GEN_CREATED ──> GEN_RUNNING ──> GEN_SUSPENDED ──> GEN_CLOSED
                                        ^    |            │
                                        └────┘         돌아가는 길 없음
```

**이것이 왜 위험한가 — 조용한 실패**

```python
g = (n for n in range(3))
print(sum(g))      # 3
print(sum(g))      # 0
```

두 번째 합계가 **`0`** 이다. 예외도 경고도 없다.\
집계를 두 번 하는 코드, 제너레이터를 두 함수에 넘기는 코드에서 **결과만 조용히 틀린다.**

> **조용한 실패(silent failure)** — 에러 없이 정상처럼 끝나는데 결과만 틀린 것.\
> 예: 로그 파이프라인에서 "총 건수"와 "오류 건수"를 같은 제너레이터로 세면 뒤엣것이 0이 된다.

**고치는 법 — 두 갈래**

1. **여러 번 돌 일이 있으면 물질화한다** — `items = list(gen)` 한 번 하고 그 리스트를 쓴다.
2. **매번 새로 만들 수 있게 한다** — `__iter__` 를 가진 클래스를 쓴다. 돌 때마다 새 제너레이터가 생긴다.

```python
class Countdown:
    def __init__(self, n): self.n = n
    def __iter__(self):
        k = self.n
        while k > 0:
            yield k
            k -= 1

c = Countdown(3)
print(list(c))
print(list(c))
```

```text
[3, 2, 1]
[3, 2, 1]
```

### 4. `send` 와 프라이밍 (예측)

**출력**

```text
0
10
15
```

그리고 마지막 줄에서

```text
TypeError: can't send non-None value to a just-started generator
```

**왜 그런가**

`yield` 는 **문이 아니라 식**이다. 값을 돌려받는다.

```text
   x = yield total
       ^^^^^^^^^^^  이 식의 값이 곧 send 로 보낸 값이다

   next(a)     = send(None)  -> x 에 None 이 들어간다 (그래서 0 으로 보정)
   a.send(10)  -> x 에 10    -> total = 0 + 10 = 10, 다음 yield 에서 10 을 낸다
   a.send(5)   -> x 에 5     -> total = 10 + 5 = 15
```

- `print(next(a))` → `0`.\
  첫 `yield total` 까지 몰고 갔고 그때 `total` 은 0이다. 이것이 **프라이밍**이다.
- `a.send(10)` 은 두 일을 한꺼번에 한다 — **값을 `x` 에 넣고**, 다음 `yield` 까지 재개시킨다. 그 결과가 `10`.
- `a.send(5)` 로 `15`.

**마지막 줄이 막히는 이유**

`b` 는 `GEN_CREATED` 다. **값을 받을 `yield` 식이 아직 없다.**\
문서가 규정한다 — "`send()` 를 불러 제너레이터를 **시작**시킬 때는 `None` 을 인자로 줘야 한다. 그 값을 받을 yield 식이 없기 때문이다."

```text
GEN_CREATED 인 제너레이터              GEN_SUSPENDED 인 제너레이터
  아직 멈춘 자리가 없다                  yield 식 자리에 멈춰 있다
  -> send(값) 은 TypeError              -> send(값) 이 그 자리에 값을 놓는다
  -> send(None) / next() 만 가능
```

**여기서 배울 것**

`send` 를 쓰는 제너레이터는 **"먼저 `next` 한 번"이라는 암묵 규약**을 갖게 된다.\
그 규약이 코드 어디에도 안 적혀 있는 것이 이 API 의 약점이고, 요즘 이 용도를 `async`/`await`(목록의 51번 주제)가 가져간 이유다.

### 5. `close()` 는 멈춘 자리에 예외를 던진다 (왜)

**출력**

```text
1
   finally: 정리했다
```

**정확히 무엇을 하나**

`close()` 는 **제너레이터가 멈춰 있던 바로 그 `yield` 자리에 `GeneratorExit` 예외를 던진다.**\
문서 표현 그대로다 — "Raises a `GeneratorExit` **at the point where the generator function was paused**."

```text
  close() 호출 전                      close() 호출
  +--------------------------+         멈춘 자리에 GeneratorExit 를 던진다
  | 커서: yield 1            |                 |
  | try 블록 안에 있다        |                 v
  +--------------------------+         try:
                                           yield 1     <- 여기서 예외 발생
                                           yield 2     <- 영영 안 돈다
                                       finally:
                                           print(...)  <- 이건 돈다
```

- **`yield 2` 는 돌지 않는다.** 예외가 그 앞에서 났기 때문이다.
- **`finally` 는 돈다.** 예외가 빠져나가는 길에 반드시 지나기 때문이다.
- 그래서 파일 닫기·락 해제·커넥션 반납은 `finally` 에 둔다.
- 닫힌 뒤 `next(c)` 하면 곧바로 `StopIteration` 이다 — 이미 `GEN_CLOSED` 다.

> **`GeneratorExit`** — 제너레이터를 닫을 때 멈춘 자리에 던져지는 전용 예외.\
> 예: `BaseException` 계열이라 `except Exception:` 에 안 잡힌다. 그 덕에 넓은 `except` 로 실수로 삼켜지지 않는다.

**주의 두 가지**

1. `GeneratorExit` 를 잡아서 **또 `yield` 하면** `RuntimeError: generator ignored GeneratorExit` 가 난다(실행 확인).\
   잡았으면 정리만 하고 빠져나가야 한다.
2. **아무도 `close()` 를 안 부르면** `finally` 는 제너레이터가 회수될 때까지 미뤄진다.\
   그래서 자원을 여는 제너레이터는 `with` 안에서 쓰거나 끝까지 소비하는 편이 안전하다.

### 6. `yield from` 과 `return` 값 (예측)

**출력**

```text
   outer 가 받은 return 값: 'inner 의 return'
['i1', 'i2', 'o1']
```

(`print` 가 `list(...)` 를 계산하는 도중에 돌기 때문에 **위에** 찍힌다.)

**왜 `"inner 의 return"` 이 리스트에 없나**

`yield` 와 `return` 은 서로 다른 통로다.

```text
   바깥              outer()                   inner()
   list(outer()) <-- yield from inner()  <---- yield "i1"    ┐ 값 통로
                                         <---- yield "i2"    ┘ (바깥까지 간다)
                       got = ─────────── <---- return "inner 의 return"
                             ^                                 ┐ 반환 통로
                    StopIteration.value 가 이 식의 값이 된다     ┘ (여기서 멈춘다)
                     yield "o1"  ───────────────────> 바깥
```

- `yield` 한 값은 **바깥 호출자까지 그대로** 간다. `outer` 가 중간에서 받아 다시 내보내는 게 아니다.
- `return` 한 값은 `StopIteration` 에 실려 **`yield from` 식의 값**이 된다. 거기서 멈춘다.
- 문서 표현 — "하위 이터레이터가 끝나면 그때 발생한 `StopIteration` 의 `value` 속성이 **yield 식의 값이 된다**."
- 그래서 결과는 `['i1', 'i2', 'o1']` 이고 `'inner 의 return'` 은 `got` 에만 들어간다.

**`for x in inner(): yield x` 와 무엇이 다른가**

| | `for x in inner(): yield x` | `yield from inner()` |
|---|---|---|
| 값 전달 | 된다 | 된다 |
| `return` 값 회수 | **안 된다** | `yield from` 식의 값으로 받는다 |
| `send()` 전달 | **안 된다**(바깥 층이 삼킨다) | 하위까지 전달된다 |
| `throw()`·`close()` 전달 | **안 된다** | 하위까지 전달된다 |

**비용** — 위임이 한 줄이 되고 양방향 통신이 보존된다.\
대신 값이 **어느 층에서 나왔는지** 추적하기 어려워진다.

### 7. 셋이 공통으로 말하는 것 (경계)

**(a) 예외는 만들 때가 아니라 꺼낼 때 난다**

```python
g = boom()
print("(a) 제너레이터 생성:", g)
```

```text
(a) 제너레이터 생성: <generator object boom at 0x77e65b9d07c0>
```

예외가 안 났다. `raise` 줄은 두 번째 `next` 에서야 돈다.

**(b) `len()` 이 안 된다**

```text
(b) TypeError: object of type 'generator' has no len()
```

**아직 몇 개인지 모르기 때문이다.** 알려면 다 꺼내 봐야 하고, 꺼내면 소진된다.

**(c) 만들기만 하면 아무것도 안 찍힌다**

```python
gen = (print(n) for n in [1, 2, 3])
print("(c) 만들기만 했다:", gen)
```

```text
(c) 만들기만 했다: <generator object <genexpr> at 0x77e65b9af9f0>
```

`1`·`2`·`3` 이 안 찍혔다.

**공통으로 말하는 성질 — 한 문장**

> **제너레이터는 "값의 묶음"이 아니라 "값을 만드는 절차"다. 그 절차는 소비할 때만 돈다.**

그래서 셋이 전부 여기서 나온다.

```text
       만드는 시점                        소비하는 시점
   ┌──────────────────────┐        ┌──────────────────────────────┐
   │ 객체 하나가 생긴다      │  ───>  │ 몸통이 돈다                   │
   │ 몸통은 안 돈다         │        │ 부작용이 일어난다              │
   │ 개수를 모른다          │        │ 예외가 터진다                  │
   │ 예외가 안 난다         │        │ 그때서야 개수를 알 수 있다      │
   └──────────────────────┘        └──────────────────────────────┘
```

**실무에서 이것이 물리는 세 자리**

1. `try`/`except` 를 **만드는 자리**에 둬서 아무것도 못 잡는다.
2. `with open(...) as f: return (line for line in f)` — 소비할 때쯤 파일이 **이미 닫혀 있다.**
3. 부작용(DB 쓰기·전송)이 목적인데 제너레이터로 짜서, 아무도 소비하지 않아 **아무 일도 안 일어난다.**

### 8. `for` 를 풀어 쓰면 (연결)

```python
it = iter(gen)
while True:
    try:
        item = next(it)
    except StopIteration:
        break
    # 여기가 for 몸통
    print(item)
```

**실행 확인**

```python
def src():
    yield "a"
    yield "b"

it = iter(src())
while True:
    try:
        item = next(it)
    except StopIteration:
        break
    print("  받음:", item)
```

```text
  받음: a
  받음: b
```

**이 풀이가 설명해 주는 것 세 가지**

1. **왜 `StopIteration` 을 볼 일이 없나** — `for` 가 잡아서 `break` 로 바꿔 준다. 사용자 눈에는 "루프가 끝났다"로만 보인다.
2. **왜 소진된 제너레이터가 빈 결과를 내나**(3번 답) — 첫 `next` 부터 `StopIteration` 이 오면 몸통이 0회 돈다. 그것은 "원소가 0개인 이터러블"과 **구별되지 않는다.**
3. **왜 `else` 절이 있나** — `for ... else` 의 `else` 는 `break` 없이 정상 종료(= `StopIteration`)했을 때만 돈다. 위 풀이의 `break` 자리를 보면 그 의미가 그대로 보인다(목록의 18번 주제).

**`iter()` 가 하는 일**

- 리스트·문자열 같은 **이터러블**에는 `iter()` 가 새 이터레이터를 만들어 준다. 그래서 `for` 를 두 번 돌 수 있다.
- **제너레이터**는 이미 이터레이터다. `iter(g) is g` 가 참이라 **새것을 안 만들어 준다.**\
  그것이 `for` 를 두 번 돌면 두 번째가 비는 이유다.

```python
def g():
    yield 1
gg = g()
print("iter(gg) is gg ->", iter(gg) is gg)
print("iter([1,2]) is [1,2] ->", iter([1, 2]) is [1, 2])
```

```text
iter(gg) is gg -> True
iter([1,2]) is [1,2] -> False
```

---

## 실행 검증

이 파일에 실린 출력은 전부 아래 환경에서 직접 돌려 얻었다.

```text
$ python3 --version
Python 3.12.3
```

- 1번 — `steps()` 의 출력 일곱 줄
- 2번 — 줄 번호를 매긴 파일로 `gi_frame.f_lineno` / `f_locals` 세 번
- 3번 — `list(g)` 두 번, `sum(g)` 두 번, `Countdown` 두 번
- 4번 — `adder` 의 `next`/`send` 세 줄과 프라이밍 생략 시 `TypeError`
- 5번 — `guarded()` 의 `close()` 와 `finally`
- 6번 — `yield from` 의 출력 순서와 `got`
- 7번 — `boom()` 생성, `len()` 의 `TypeError`, `(print(n) for n in ...)` 무실행
- 8번 — `iter`/`next`/`StopIteration` 풀어쓰기
- 부록 — `GEN_RUNNING`(제너레이터가 자기를 들여다봄), `generator already executing`, 도달 못 하는 `yield`, PEP 479(`RuntimeError: generator raised StopIteration`)

중단·재개·상태 전이는 **언어 보장**이다. `gi_frame`·`f_lineno` 같은 내부 들여다보기는 CPython 의 내성 기능이므로 다른 구현에서는 안 보일 수 있다.
