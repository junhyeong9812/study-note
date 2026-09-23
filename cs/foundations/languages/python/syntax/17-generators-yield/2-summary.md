# python/syntax/17-generators-yield — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만.
> - [6.2.9. Yield expressions](https://docs.python.org/3.12/reference/expressions.html#yield-expressions) — 중단·재개, `send`·`close`·`yield from`
> - [`inspect.getgeneratorstate()`](https://docs.python.org/3.12/library/inspect.html#inspect.getgeneratorstate) — 제너레이터의 네 상태
> - [`StopIteration`](https://docs.python.org/3.12/library/exceptions.html#StopIteration) — `value` 속성
>
> **실행 검증** — 이 문서에 실린 출력은 전부 `python3` **3.12.3**(Linux)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> **버전** — `yield` 는 Python 2.2+, `send`/`close` 는 2.5+, **`yield from` 은 3.3+**, `StopIteration.value` 는 3.3+.\
>   3.7 부터 제너레이터 안에서 새어 나온 `StopIteration` 은 `RuntimeError` 로 바뀐다(PEP 479).
> **구현 대 명세** — 중단·재개·상태 전이는 **언어 보장**이다. `gi_frame`·`f_lineno` 같은 내부 들여다보기는 CPython 의 내성(introspection) 기능이다.

## 한눈에 — 쉽게 말하면

**읽다 만 책에 끼워 둔 책갈피.**

- 보통 함수는 **한 번 부르면 끝까지 읽고 책을 덮는다.** 다음에 부르면 1쪽부터 다시 읽는다.
- 제너레이터 함수는 `yield` 를 만나면 **그 쪽에 책갈피를 끼우고 책을 펼친 채 덮어 둔다.**
- 다음에 `next()` 로 부르면 **1쪽이 아니라 책갈피 자리에서 이어 읽는다.**
- 그동안 **밑줄 쳐 둔 것(지역 변수)이 그대로 남아 있다.** 그래서 이어 읽는 것이 가능하다.

```text
보통 함수                            제너레이터 함수
  call ──> [ 처음부터 끝까지 ] ──> return   call ──> 아무것도 안 함, 책만 건넨다
  다음 call 은 처음부터 다시                next ──> [ 1줄 ~ yield ] ──> 값, 책갈피
                                          next ──> [ 책갈피 ~ 다음 yield ] ──> 값
                                          next ──> [ 책갈피 ~ 끝 ] ──> StopIteration
```

이 책갈피가 **똑같은 구조로** 파이썬의 **프레임(frame)** 이다.\
실무에서 이것이 값을 내는 자리는 하나다 — **다 만들기 전에 하나씩 내보내야 할 때.**\
10GB 로그 파일을 한 줄씩, 페이지네이션 API 를 한 쪽씩, 무한 수열을 필요한 만큼만.

> **프레임(frame)** — 함수 하나가 돌아가는 데 필요한 작업 공간. 지역 변수와 "지금 몇 번째 줄인지"가 들어 있다.\
> 예: 보통 함수는 `return` 하면 이 작업 공간을 버리지만, 제너레이터는 **버리지 않고 들고 있는다.**

> **지연 평가(lazy evaluation)** — 값을 미리 다 만들어 두지 않고 요청받을 때 하나씩 만드는 방식.\
> 예: 1억 줄짜리 파일을 리스트로 읽으면 메모리가 터지지만, 제너레이터로 읽으면 한 줄씩만 메모리에 올라온다.

## 이 주제가 답하려는 질문

1. **부르면 무엇이 도나** — 제너레이터 함수를 **호출하는 것**과 **실행하는 것**은 왜 다른 일인가.
2. **「멈춘다」가 정확히 무슨 뜻인가** — 무엇이 남아 있길래 다음 `next()` 가 이어 갈 수 있나.
3. **멈춘 자리에 무엇을 할 수 있나** — `send`·`close`·`yield from` 이 각각 그 자리에 무엇을 하나.

## 동작 방식

> 이 절이 본문이다. **멈추고 재개하는 것은 눈에 안 보인다.** 그래서 그림이 본문이고 글은 그림을 읽는다.

### 1. 호출해도 몸통이 안 돈다

**언제 쓰나** — `def` 안에 `yield` 가 하나라도 있으면 그 함수는 제너레이터 함수다. 부르는 순간부터 보통 함수와 다르게 움직인다.

```text
def steps():                        g = steps()  를 실행하면
    print("A: 시작")                   1. 함수 몸통은 한 줄도 안 돈다
    yield 1                           2. 제너레이터 객체를 만들어 돌려준다
    print("B: 1 과 2 사이")            3. 그 안에 프레임이 "시작 전" 상태로 들어 있다
    yield 2
    print("C: 끝내는 중")              -> print("A: 시작") 은 아직 안 찍혔다
```

```python
def steps():
    print("   A: 시작")
    yield 1
    print("   B: 1 과 2 사이")
    yield 2
    print("   C: 끝내는 중")

print("호출 직전")
g = steps()
print("호출 직후 ->", g)
print("next 1 ->", next(g))
print("next 2 ->", next(g))
try:
    next(g)
except StopIteration as e:
    print("StopIteration, value =", e.value)
```

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

그림 해설 — 출력 순서를 한 줄씩 읽는다.

- `호출 직후` 가 `A: 시작` **보다 먼저** 찍혔다. → 호출은 몸통을 돌리지 않는다.
- 첫 `next` 가 `A: 시작` 을 찍고 `yield 1` 에서 멈춰 1을 돌려줬다.
- 둘째 `next` 는 **`A: 시작` 을 다시 찍지 않았다.** → 처음부터가 아니라 **멈춘 자리에서** 이어 갔다.
- 셋째 `next` 는 `C: 끝내는 중` 을 찍고 함수 끝에 닿아 `StopIteration` 을 던졌다.
- `return` 이 없으면 `StopIteration.value` 는 `None` 이다.

문서 표현으로 "제너레이터 함수를 호출하면 **제너레이터라는 이터레이터를 돌려준다**. 실행은 제너레이터의 메서드가 불릴 때 시작된다".

**비용** — 값을 미리 만들지 않으므로 메모리가 거의 안 든다.\
대신 **몸통이 언제 도는지가 코드 순서와 어긋난다** — 부작용(로그·파일 열기)이 예상 밖의 시점에 일어난다.

### 2. ★ 어디서 멈추고 무엇이 살아 있나

**언제 쓰나** — 이 주제의 핵심. "멈춘다"가 정확히 무슨 뜻인지 확인할 때.

문서가 규정한다 — "중단됐다는 것은 **모든 지역 상태가 유지된다**는 뜻이다. 지역 변수의 현재 바인딩, **명령 포인터**, 내부 평가 스택, 예외 처리 상태까지 포함해서."

그걸 눈으로 보기 위해 줄 번호를 매긴 파일 하나를 그대로 돌렸다.

```python
 1  import inspect
 2
 3  def counter():
 4      total = 0
 5      for i in (10, 20, 30):
 6          total += i
 7          yield total
 8
 9  g = counter()
10  print(inspect.getgeneratorstate(g))
11  for _ in range(3):
12      v = next(g)
13      print(v, inspect.getgeneratorstate(g), g.gi_frame.f_lineno, g.gi_frame.f_locals)
14  try:
15      next(g)
16  except StopIteration:
17      print(inspect.getgeneratorstate(g), g.gi_frame)
```

```text
GEN_CREATED
10 GEN_SUSPENDED 7 {'total': 10, 'i': 10}
30 GEN_SUSPENDED 7 {'total': 30, 'i': 20}
60 GEN_SUSPENDED 7 {'total': 60, 'i': 30}
GEN_CLOSED None
```

이 출력을 그림으로 펴면 이렇다.

```text
호출자 쪽                         제너레이터가 들고 있는 프레임
------------------------          --------------------------------
g = counter()                     +------------------------------+
   몸통 안 돎                      | total = ?    i = ?           |
   GEN_CREATED                    | 커서: 3번 줄 앞 (시작 전)      |
                                  +------------------------------+
        |
   next(g)  -- 제어권 넘김 -->      4  total = 0
                                  5  for i in (10,20,30):
                                  6      total += i        -> 10
                                  7      yield total   ← 여기서 멈춘다
   v = 10   <-- 값 + 제어권 --      +------------------------------+
   GEN_SUSPENDED                   | total = 10   i = 10          |
                                   | 커서: 7번 줄                  |
                                   +------------------------------+
        |
   next(g)  -- 제어권 넘김 -->      7 의 다음부터 재개
                                  5      for 의 다음 i 를 꺼낸다 -> 20
                                  6      total += i        -> 30
                                  7      yield total   ← 또 멈춘다
   v = 30   <--                    +------------------------------+
                                   | total = 30   i = 20          |
                                   | 커서: 7번 줄                  |
                                   +------------------------------+
```

그림 해설 — 출력의 어느 글자가 그림의 어디인지.

- `GEN_CREATED` — 아직 한 줄도 안 돌았다. `total` 도 `i` 도 없다.
- `f_lineno` 가 **세 번 다 `7`** 이다. 7번 줄은 `yield total` — **언제나 `yield` 자리에서 멈춘다.**
- `f_locals` 가 `{'total': 10, 'i': 10}` → `{'total': 30, 'i': 20}` → `{'total': 60, 'i': 30}` 로 **이어진다.**\
  매번 처음부터 돌았다면 `total` 이 늘 10 이어야 한다. 늘어난다는 것이 **프레임이 살아 있다는 증거**다.
- `for` 문이 어디까지 진행됐는지도 프레임 안에 남아 있다. 그래서 `i` 가 10 → 20 → 30 으로 넘어간다.
- 마지막 `GEN_CLOSED` 에서 **`gi_frame` 이 `None`** 이 됐다 → 끝난 제너레이터는 프레임을 놓아 준다. 메모리가 회수되는 자리다.

> **`gi_frame`** — 제너레이터가 들고 있는 프레임 객체. 끝나면 `None` 이 된다.\
> 예: `g.gi_frame.f_lineno` 로 지금 몇 번 줄에 멈춰 있는지, `f_locals` 로 어떤 지역 변수가 살아 있는지 볼 수 있다.

**비용** — 프레임을 들고 있으므로 **끝내지 않은 제너레이터는 메모리를 잡고 있다.**\
그 안에 열린 파일이 있으면 파일도 안 닫힌 채 남는다(5번 절).

### 3. 상태는 넷뿐이다

**언제 쓰나** — "이 제너레이터를 또 돌려도 되나"를 판단할 때.

```text
   GEN_CREATED ──(첫 next/send)──> GEN_RUNNING ──(yield)──> GEN_SUSPENDED
        │                              ^                          │
        │                              └────(next/send)───────────┘
        │                                                         │
        └──────(close)──────> GEN_CLOSED <──(끝까지 감 / 예외 / close)┘
```

```python
import inspect
def introspect():
    yield inspect.getgeneratorstate(g)
g = introspect()
print("안에서 본 상태:", next(g))
```

```text
안에서 본 상태: GEN_RUNNING
```

그림 해설.

- `GEN_RUNNING` 은 **바깥에서는 절대 볼 수 없다.** 돌고 있는 동안 호출자는 멈춰 있기 때문이다.\
  위 코드는 제너레이터가 **자기 자신을 들여다본** 것이라 볼 수 있었다.
- 돌고 있는 제너레이터를 또 `next` 하면 막힌다.

```python
def reenter():
    yield next(h)
h = reenter()
next(h)
```

```text
ValueError: generator already executing
```

- `GEN_CLOSED` 는 **되돌아갈 수 없는 상태**다. 재시작 버튼이 없다.

**비용** — 상태가 단순해서 추론이 쉽다.\
대신 **한 번 소진하면 끝**이라 "다시 돌려야 하면 다시 만들어야 한다"는 제약이 생긴다(4번 절).

### 4. `for` 가 실제로 하는 일

**언제 쓰나** — `for` 가 왜 `StopIteration` 을 안 보여주는지 궁금할 때.

```text
for item in src():          와 같다      it = iter(src())
    print(item)                          while True:
                                             try:
                                                 item = next(it)
                                             except StopIteration:
                                                 break
                                             print(item)
```

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

소진되면 다시 안 돈다.

```python
g = src()
print(list(g))
print(list(g))
```

```text
['a', 'b']
[]
```

그림 해설.

- `for` 는 `iter()` 로 이터레이터를 얻고, `next()` 를 반복하고, `StopIteration` 을 잡아 **조용히 빠져나간다.**
- 그래서 사용자는 `StopIteration` 을 볼 일이 없다.
- 두 번째 `list(g)` 가 `[]` 인 것은 **에러가 아니다.** 이미 `GEN_CLOSED` 라서 처음부터 끝난 상태로 취급된다.\
  이것이 제너레이터에서 가장 조용히 틀리는 자리다 — **빈 결과가 나오고 아무도 안 알려 준다.**
- 여러 번 돌려야 하면 제너레이터가 아니라 **`__iter__` 를 가진 클래스**를 만든다. 돌 때마다 새 제너레이터가 생긴다.

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

**비용** — 이터러블 클래스는 여러 번 돌 수 있다.\
대신 클래스 하나를 더 쓰고, 매번 처음부터 다시 계산한다.

### 5. `close()` — 멈춘 자리에서 예외가 터진다

**언제 쓰나** — 제너레이터 안에서 파일·커넥션을 열었을 때. 정리가 언제 도는지가 문제가 된다.

```text
  guarded() 가 yield 1 에서 멈춰 있다
        +----------------------------+
        | 커서: yield 1              |
        | try 블록 안에 있다          |
        +----------------------------+
              |
        c.close() 호출
              |
              v
   멈춘 그 자리에 GeneratorExit 를 던진다
        try:
            yield 1      <- 여기서 예외 발생
            yield 2      <- 영영 안 돈다
        finally:
            print("정리했다")   <- 이건 돈다
```

```python
def guarded():
    try:
        yield 1
        yield 2
    finally:
        print("   finally: 정리했다")

c = guarded()
print(next(c))
c.close()
try:
    next(c)
except StopIteration:
    print("   StopIteration — 더 없음")
```

```text
1
   finally: 정리했다
   StopIteration — 더 없음
```

그림 해설.

- `close()` 는 **멈춰 있던 `yield` 자리에 `GeneratorExit` 를 던진다.** 문서 표현 그대로다.
- `finally` 는 돈다. 그래서 파일 닫기·락 해제를 `finally` 에 두면 안전하다.
- `yield 2` 는 영영 실행되지 않는다.
- 닫힌 뒤 `next` 하면 곧바로 `StopIteration` 이다.

> **`GeneratorExit`** — 제너레이터를 닫을 때 그 멈춘 자리에 던져지는 전용 예외.\
> 예: `except Exception:` 으로는 안 잡힌다(`BaseException` 계열이다). 잡아서 삼키면 안 되고, 정리만 하고 빠져나가야 한다.

**비용** — `finally` 덕에 정리를 보장할 수 있다.\
대신 **`close()` 를 아무도 안 부르면** 그 정리는 제너레이터가 회수될 때까지 미뤄진다. 그래서 `with` 안에서 쓰거나 다 소비하는 편이 낫다.

### 6. `send()` — 값이 `yield` 자리로 들어온다

**언제 쓰나** — 제너레이터를 "값을 내는 것"이 아니라 "값을 받는 것"으로 쓸 때.

```text
   x = yield total
       ^^^^^^^^^^^  yield 는 식(expression)이다. 값을 돌려준다.

   바깥에서 a.send(10) 을 하면
        +--------------------------------------------+
        | 그 값 10 이 "yield total" 식의 값이 된다    |
        | 즉 x 에 10 이 들어간다                     |
        | 그리고 거기서부터 재개해서 다음 yield 까지   |
        +--------------------------------------------+
```

```python
def adder():
    total = 0
    while True:
        x = yield total
        if x is None:
            x = 0
        total += x

a = adder()
print(next(a))
print(a.send(10))
print(a.send(5))
```

```text
0
10
15
```

그림 해설.

- 첫 `next(a)` 가 **프라이밍**이다. 첫 `yield total` 까지 몰고 가서 `0` 을 받아 온다.
- `a.send(10)` 은 두 가지를 동시에 한다 — **`x` 에 10을 넣고**, 다음 `yield` 까지 재개시킨다. 그 결과 `10` 이 나온다.
- `a.send(5)` 로 `15`.
- 프라이밍을 빼먹으면 막힌다.

```python
b = adder()
b.send(10)
```

```text
TypeError: can't send non-None value to a just-started generator
```

문서가 규정한다 — "제너레이터를 **시작**시키려고 `send()` 를 부를 때는 `None` 을 인자로 줘야 한다. 그 값을 받을 `yield` 식이 아직 없기 때문이다."

**비용** — 양방향 통신이 된다(코루틴의 뿌리).\
대신 **프라이밍이라는 암묵 규약**이 생기고, 읽는 사람이 흐름을 따라가기 어려워진다. 요즘은 이 용도를 `async`/`await`(목록의 51번 주제)가 가져갔다.

### 7. `yield from` — 하위 제너레이터에 그대로 이어 붙인다

**언제 쓰나** — 제너레이터가 다른 제너레이터의 값을 그대로 흘려보낼 때.

```text
   바깥                outer()                inner()
   list(outer())  <--  yield from inner() <-- yield "i1"
                                          <-- yield "i2"
                         got = ...        <-- return "inner 의 return"
                       yield "o1"
                            ^
             하위가 끝나면서 낸 StopIteration.value 가
             yield from 식의 값(got)이 된다 — 바깥으로는 안 나간다
```

```python
def inner():
    yield "i1"
    yield "i2"
    return "inner 의 return"

def outer():
    got = yield from inner()
    print("   outer 가 받은 return 값:", repr(got))
    yield "o1"

print(list(outer()))
```

```text
   outer 가 받은 return 값: 'inner 의 return'
['i1', 'i2', 'o1']
```

그림 해설.

- `yield from` 은 하위 제너레이터의 값을 **바깥 호출자에게 직접 건넨다.** `outer` 가 중간에서 받아 다시 `yield` 하는 게 아니다.
- 하위가 `return` 한 값은 **결과 목록에 안 들어간다.** `yield from` 식의 값이 될 뿐이다.\
  그래서 `['i1', 'i2', 'o1']` 에 `'inner 의 return'` 이 없다.
- `send`·`throw`·`close` 도 하위로 그대로 전달된다. 그것이 `for x in inner(): yield x` 로 쓰는 것과 다른 점이다.

**비용** — 위임이 한 줄로 끝나고 양방향 통신이 보존된다.\
대신 **어느 층에서 값이 나왔는지 추적이 어려워진다.**

## 문법 — 형태와 규칙

```python
def gen():
    yield 1              # 값을 내고 멈춘다
    x = yield            # 값을 내지 않고(= None) 멈췄다가, 보내온 값을 x 로 받는다
    y = yield 2          # 둘 다 한다
    yield from other()   # 다른 이터러블/제너레이터에 위임
    return "끝"          # StopIteration.value 가 된다

g = gen()
next(g)          # = g.send(None)
g.send(v)        # 재개하면서 yield 식의 값으로 v 를 넣는다
g.throw(Err)     # 멈춘 자리에서 예외를 던진다
g.close()        # 멈춘 자리에 GeneratorExit 를 던진다
g.gi_frame       # 살아 있는 프레임 (끝나면 None)
```

규칙 다섯.

1. **`def` 몸통에 `yield` 가 하나라도 있으면** 그 함수는 제너레이터 함수다. 도달 못 하는 자리에 있어도 그렇다 — `def f(): return 1; yield` 를 부르면 `<class 'generator'>` 가 나오고 `list(f())` 는 `[]` 다(실행 확인).
2. **호출은 몸통을 돌리지 않는다.** 제너레이터 객체만 만들어 돌려준다.
3. **`yield` 는 문이 아니라 식이다.** 값을 돌려받을 수 있다(`x = yield`).
4. **`return` 은 값을 내보내지 않는다.** `StopIteration.value` 에 실릴 뿐이다.
5. **한 번 소진하면 끝이다.** 되감기가 없다.

> **이터레이터(iterator)** — `__next__()` 를 가지고 있어서 `next()` 로 다음 값을 꺼낼 수 있는 객체.\
> 예: 제너레이터는 이터레이터다. 그래서 `for` 에 바로 넣을 수 있다.

> **프라이밍(priming)** — `send()` 로 값을 넣기 전에 첫 `next()` 로 첫 `yield` 까지 몰고 가는 것.\
> 예: 값을 받을 `yield` 식이 아직 없는 상태에 값을 보내면 `TypeError` 가 난다.

## 어디서 틀리나

### (1) 소진된 것을 두 번 쓰는데 에러가 안 난다

```python
g = (n for n in range(3))
print(sum(g))
print(sum(g))
```

```text
3
0
```

한 번 쓴 제너레이터를 함수에 또 넘기면 **`0`·`[]`·`None` 이 조용히 나온다.**\
집계 결과가 0으로 나오는 버그의 단골 원인이다. 에러가 안 나므로 로그에도 안 남는다.

### (2) `len()` 이 안 된다

```python
def src():
    yield 1
    yield 2
len(src())
```

```text
TypeError: object of type 'generator' has no len()
```

**아직 몇 개인지 모르기 때문이다.** 개수를 알려면 다 꺼내 봐야 하고, 꺼내면 소진된다.\
개수가 필요하면 `list()` 로 물질화하거나 `sum(1 for _ in it)` 로 세되, **그 순간 지연의 이점이 사라진다.**

### (3) 예외가 "만들 때"가 아니라 "꺼낼 때" 터진다

```python
def boom():
    yield 1
    raise ValueError("여기서 터진다")

g = boom()
print("제너레이터는 만들어졌다:", g)
print("첫 값:", next(g))
next(g)
```

```text
제너레이터는 만들어졌다: <generator object boom at 0x77d836934b80>
첫 값: 1
ValueError: 여기서 터진다
```

`try`/`except` 를 **만드는 자리**에 두면 아무것도 못 잡는다. **소비하는 자리**에 둬야 한다.\
그래서 `with open(...) as f: return (line for line in f)` 는 위험하다 — 소비할 때쯤 파일이 이미 닫혀 있다.

### (4) 만들어만 놓으면 아무 일도 안 일어난다

```python
def effect(n):
    print("   effect 실행:", n)
    return n * 2

gen = (effect(n) for n in [1, 2, 3])
print("제너레이터 표현식을 만들었다 — 위에 아무 줄도 안 찍혔다")
print("합:", sum(gen))
```

```text
제너레이터 표현식을 만들었다 — 위에 아무 줄도 안 찍혔다
   effect 실행: 1
   effect 실행: 2
   effect 실행: 3
합: 12
```

부작용이 목적인 코드를 제너레이터로 짜면 **아무도 소비하지 않아 영영 안 돈다.**\
"DB 에 다 넣었는데 아무 행도 안 들어갔다"가 이 모양이다.

### (5) 소비 시점의 원본을 읽는다

```python
nums = [1, 2, 3]
lazy = (n * 10 for n in nums)
nums.append(4)
print(list(lazy))
```

```text
[10, 20, 30, 40]
```

만들 때가 아니라 **꺼낼 때** 원본을 훑기 때문이다.\
반대로 **가장 바깥 `for` 의 iterable 만은 만들 때 평가된다** — 이름을 새 객체로 갈아 끼우면 안 따라간다.

```python
src_list = [1, 2, 3]
lazy2 = (n for n in src_list)
src_list = [9, 9, 9]
print(list(lazy2))
```

```text
[1, 2, 3]
```

문서가 규정한다 — "**가장 왼쪽 `for` 절의 iterable 식은 즉시 평가된다.**" 자세한 것은 [14번 주제](../14-comprehensions/2-summary.md)에 있다.

### (6) 돌고 있는 제너레이터를 또 `next` 한다

```text
ValueError: generator already executing
```

재귀적으로 자기를 소비하는 구조를 짜면 난다. 제너레이터는 **동시에 한 곳에서만** 돈다.

## 구현 세부사항 대 언어 보장

세 층으로 가른다. ★ **이 주제는 「언어 보장」이 두꺼운 편이다** — 중단·재개·상태 전이가 전부 명세에 있다.\
구현 쪽에 남는 것은 **들여다보는 도구**다.

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **언어 보장** | 언어·라이브러리 레퍼런스가 정한 것 | 공식 문서 문장을 열어서 인용 |
| **CPython 구현** | 이 구현이 그렇게 하는 것 | 실행 + `gi_frame` 으로 확인 |
| **이 판의 관찰** | 3.12.3 에서 그랬을 뿐 | 「관찰」로 명기 |

### 언어 보장

| 사실 | 근거 |
|---|---|
| 제너레이터 함수를 호출하면 **이터레이터를 돌려주고**, 실행은 **그 메서드가 불릴 때** 시작된다 | 6.2.9 — *"When a generator function is called, it returns an iterator known as a generator... The execution starts when one of the generator's methods is called."* |
| 「중단됐다」는 **모든 지역 상태가 유지된다**는 뜻이다 — 지역 변수 바인딩·명령 포인터·내부 평가 스택·예외 처리 상태 | 6.2.9 — *"all local state is retained, including the current bindings of local variables, the instruction pointer, the internal evaluation stack, and the state of any exception handling"* |
| `close()` 는 **제너레이터가 멈춰 있던 그 자리에** `GeneratorExit` 를 던진다 | 6.2.9 — *"Raises a GeneratorExit at the point where the generator function was paused."* |
| `send()` 로 **시작**시킬 때는 `None` 을 줘야 한다 — 값을 받을 `yield` 식이 아직 없기 때문이다 | 6.2.9 — *"it must be called with None as the argument, because there is no yield expression that could receive the value"* |
| 하위 이터레이터가 끝나면 그 `StopIteration` 의 `value` 가 **`yield from` 식의 값**이 된다 | 6.2.9 — *"the value attribute of the raised StopIteration instance becomes the value of the yield expression"* |
| 제너레이터의 네 상태 — `GEN_CREATED`·`GEN_RUNNING`·`GEN_SUSPENDED`·`GEN_CLOSED` | `inspect.getgeneratorstate()` |
| 3.7 부터 제너레이터 안에서 새어 나온 `StopIteration` 은 `RuntimeError` 로 바뀐다 | PEP 479 — 실행에서 `RuntimeError: generator raised StopIteration` 확인 |

★ **`for` 가 `iter` + 반복 `next` + `StopIteration` 잡기라는 것도 언어 보장이다.** 「소진된 제너레이터가 에러가 아니라 빈 결과를 낸다」는 그 정의에서 따라 나오는 것이지 구현 편의가 아니다.

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| `gi_frame`·`gi_running`·`gi_code`·`gi_yieldfrom` 으로 **안을 들여다볼 수 있다** | `inspect` 문서의 "Types and members" 표에 실려 있다. **다른 구현에 프레임 객체가 이 모양으로 있으리라는 보장은 없다** |
| `f_lineno` 가 **멈춘 소스 줄 번호**를 준다 | 실행 — 세 번 다 `7`(`yield total` 줄) |
| `f_locals` 가 **살아 있는 지역 변수**를 dict 로 준다 | 실행 — `{'total': 10, 'i': 10}` → `{'total': 30, 'i': 20}` → `{'total': 60, 'i': 30}` |
| 끝난 제너레이터의 `gi_frame` 이 `None` 이 된다 | 실행 — `GEN_CLOSED None` |
| `GeneratorExit` 를 잡고 또 `yield` 하면 `RuntimeError: generator ignored GeneratorExit` | 실행 확인 |
| `close()` 를 아무도 안 부르면 `finally` 가 **회수 시점까지** 미뤄진다 | 회수 시점은 참조 카운팅의 결과다. **명세가 정한 시점이 아니다** |

★ **`f_lineno` 로 「언제나 `yield` 자리에서 멈춘다」를 눈으로 본 것은 구현 도구로 명세를 확인한 것**이다. 멈추는 자리가 `yield` 인 것은 명세, 그것을 `7` 이라는 숫자로 보여 준 것은 이 구현이다.

### 이 판(3.12.3)의 관찰

| 관찰 | 어디가 흔들리나 |
|---|---|
| `<generator object steps at 0x7c6faebd0b80>` 의 주소 숫자 | **실행할 때마다 다르다.** 값 자체는 아무 의미가 없다 |
| `TypeError: can't send non-None value to a just-started generator` 문구 | 예외 **종류**는 명세지만 **문구**는 아니다 |
| `ValueError: generator already executing` 문구 | 위와 같다 |
| `f_locals` 가 `{'total': ..., 'i': ...}` 로 **두 칸만** 보였다 | 컴파일러가 무엇을 지역으로 잡았느냐에 달렸다 |
| `list(g)` 를 두 번 불러 `[]` 가 나오기까지 **아무 경고도 없었다** | 경고가 없는 것은 설계지만, 「어떤 진단도 안 나온다」는 이 판의 확인일 뿐이다 |

### 그래서 이렇게 적으면 틀린다

- ✗ 「제너레이터를 만들면 첫 값이 미리 계산된다」\
  → **한 줄도 안 돈다.** 문서가 *"The execution starts when one of the generator's methods is called."* 라고 적는다.
- ✗ 「소진된 제너레이터를 다시 쓰면 에러가 난다」\
  → **빈 결과가 나온다.** 이것이 이 주제에서 가장 조용히 틀리는 자리다.
- ✗ 「`close()` 하면 그냥 버려진다」\
  → **멈춘 자리에 예외를 던진다.** 그래서 `finally` 가 돈다.
- ✗ 「`yield from` 은 `for x in inner(): yield x` 의 짧은 표기다」\
  → `return` 값 회수·`send`·`throw`·`close` 전달이 다르다. **값 전달만 같다.**
- ✗ 「`gi_frame.f_lineno` 로 확인했으니 어느 파이썬에서나 그렇다」\
  → **확인 도구가 CPython 것이다.** 확인된 사실(멈추는 자리가 `yield` 다)은 명세지만, 그 도구는 아니다.
- ✗ 「`finally` 는 제너레이터를 안 닫아도 언젠가 돈다」\
  → **회수 시점이 명세에 없다.** 닫거나 다 소비하는 쪽이 유일하게 보장된 길이다.

**판정 기준 한 줄**: **「무엇이 일어나나」는 명세에 있고, 「그것을 어떻게 들여다보나」는 이 구현에 있다.** `gi_*` 로 확인한 것은 확인이지 보장이 아니다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 판정 |
|---|---|
| 원소가 아주 많거나 무한하다 | **제너레이터** — 메모리가 개수와 무관해진다 |
| 앞쪽 몇 개만 필요할 수 있다 | **제너레이터** — 뒤는 계산조차 안 한다 |
| 파이프라인으로 단계를 잇는다 | **제너레이터** — 각 단계가 한 줄씩 흘려보낸다 |
| 여러 번 순회해야 한다 | **리스트**, 또는 `__iter__` 를 가진 클래스 |
| `len()`·인덱싱·슬라이싱이 필요하다 | **리스트** |
| 원소가 적고 코드를 단순하게 두고 싶다 | **리스트** — 지연은 공짜가 아니다 |
| 부작용(쓰기·전송)이 목적이다 | **제너레이터로 쓰지 않는다** — 소비를 잊으면 안 돈다 |

## 핵심 문장

- 제너레이터 함수를 **호출하는 것**과 **실행하는 것**은 다른 일이다. 호출은 객체만 만들고, 실행은 `next()` 가 시작한다.
- `yield` 에서 멈춘다는 것은 **프레임을 버리지 않는다**는 뜻이다 — 지역 변수·루프 진행 상태·명령 포인터가 통째로 남는다. `f_lineno` 와 `f_locals` 로 눈으로 확인된다.
- `for` 는 `iter` + 반복 `next` + `StopIteration` 잡기다. 그래서 소진된 제너레이터를 다시 돌려도 **에러가 아니라 빈 결과**가 나온다.
- `send`/`close`/`yield from` 은 전부 "멈춘 그 자리"에 대고 하는 조작이다 — 값을 넣거나, 예외를 던지거나, 위임한다.
- 지연의 대가는 **부작용의 시점이 코드 순서와 어긋나는 것**이다. 예외도, 파일 접근도, DB 쓰기도 소비하는 자리에서 일어난다.

## 관련 자료

- 목록: [python/syntax 주제 목록](../README.md) — 이 주제는 **17번**
- 선행: [목록의 **16번**](../16-iterator-protocol/) 「이터레이터 프로토콜」, **15번** 「제너레이터 표현식과 지연 평가」(폴더 아직 없음)
- 함께 보는 곳: [14-comprehensions](../14-comprehensions/2-summary.md) — 리스트 컴프리헨션과 제너레이터 표현식의 평가 시점 차이
- 이어지는 곳: 목록의 **44번** 「`itertools`」, **51번** 「`asyncio` 코루틴 기초」(폴더 아직 없음)
- 기존 노트: [`cs/foundations/python-basics/`](../../../../python-basics/README.md) — `for`/`while` 로 순회하는 법까지가 그쪽이다.\
  이 주제는 그 위에서 「**그 `for` 가 안쪽에서 무엇을 하고 있었나**」만 다룬다.
- 연혁은 여기가 아니다: [`history/python/06-핵심-개념-진화.md`](../../../../../../history/python/06-핵심-개념-진화.md)
- 공식 문서: [6.2.9. Yield expressions](https://docs.python.org/3.12/reference/expressions.html#yield-expressions)

## 용어 풀이

- **제너레이터 함수(generator function)**: 몸통에 `yield` 가 있는 함수.\
  호출하면 몸통이 도는 게 아니라 제너레이터 객체가 나온다.
- **제너레이터(generator)**: 그 호출이 돌려주는 객체. 이터레이터의 한 종류다.
- **이터레이터(iterator)**: `next()` 로 다음 값을 하나씩 꺼낼 수 있는 객체.\
  더 없으면 `StopIteration` 을 던진다.
- **이터러블(iterable)**: `iter()` 를 걸 수 있는 것.\
  리스트는 이터러블이고, `iter(리스트)` 의 결과가 이터레이터다.
- **프레임(frame)**: 함수 하나가 도는 데 필요한 작업 공간 — 지역 변수와 지금 몇 번째 줄인지.\
  제너레이터는 멈출 때 이것을 버리지 않는다.
- **`gi_frame`**: 제너레이터가 들고 있는 프레임 객체. 끝나면 `None`.\
  `f_lineno`(멈춘 줄)와 `f_locals`(살아 있는 지역 변수)를 볼 수 있다.
- **`StopIteration`**: 더 낼 값이 없다는 신호 예외.\
  `return` 한 값은 이 예외의 `value` 속성에 실린다.
- **`GeneratorExit`**: `close()` 가 멈춘 자리에 던지는 전용 예외.\
  `BaseException` 계열이라 `except Exception:` 으로는 안 잡힌다.
- **프라이밍(priming)**: `send()` 를 쓰기 전에 첫 `next()` 로 첫 `yield` 까지 몰고 가는 것.
- **`yield from`**: 다른 이터러블에 위임하는 문법(3.3+).\
  값뿐 아니라 `send`·`throw`·`close` 까지 그대로 전달한다.
- **지연 평가(lazy evaluation)**: 미리 다 만들지 않고 요청받을 때 하나씩 만드는 방식.
- **물질화(materialize)**: 지연된 것을 `list()`·`tuple()` 로 전부 꺼내 실제 자료구조로 만드는 것.\
  개수를 세거나 여러 번 순회하려면 필요하고, 그 순간 메모리 이점이 사라진다.
- **소진(exhaustion)**: 제너레이터의 값을 끝까지 꺼내 더 낼 것이 없어진 상태.\
  다시 쓰면 에러가 아니라 **빈 결과**가 나온다.
