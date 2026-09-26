# python/syntax/16-iterator-protocol — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만.
> - [Iterator Types](https://docs.python.org/3.12/library/stdtypes.html#iterator-types) — **두 메서드 계약**과 `__iter__` 가 자기를 돌려줘야 한다는 요구
> - [`iter()`](https://docs.python.org/3.12/library/functions.html#iter) — 한 인자 꼴 · **두 인자 꼴** · `__getitem__` 대체 경로
> - [`next()`](https://docs.python.org/3.12/library/functions.html#next) · [`StopIteration`](https://docs.python.org/3.12/library/exceptions.html#StopIteration)
> - [PEP 479 — Change StopIteration handling inside generators](https://peps.python.org/pep-0479/)
> - [`operator.length_hint`](https://docs.python.org/3.12/library/operator.html#operator.length_hint) · [glossary — iterable / iterator](https://docs.python.org/3.12/glossary.html#term-iterable)
>
> **실행 검증** — 이 문서에 실린 출력은 전부 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.\
> ★ **던지는 형태를 하나로 고정했다** — `python3 - <파일` 로 던져 트레이스백이 `File "<stdin>", line N` 이 된다.
> 그래서 **실행 중 예외에는 소스 줄과 캐럿이 안 나온다.**\
> **버전** — 이터레이터 프로토콜 자체는 **2.2+**(PEP 234)이고 이 노트 범위(3.10\~3.13)에서 안 바뀌었다.
> 갈리는 것은 하나다 — **`StopIteration` 이 제너레이터 밖으로 새면 `RuntimeError` 가 되는 것이 3.7 부터**다(PEP 479).
> 3.5\~3.6 에서는 `from __future__ import generator_stop` 로 켜는 선택이었다.
> `gi_suspended` 속성은 3.11.15 에도 있었다(대조 확인).\
> **★ 흔들리는 칸 / 안 흔들리는 칸** — 재대조에서 「고칠 것」과 「설계상 안 맞는 것」을 기계적으로 가르려고 미리 선언한다.
>
> | 흔들린다 | 안 흔들린다(근거로 써도 되는 칸) |
> |---|---|
> | (판이 오르면) **타입 이름** `list_iterator`·`callable_iterator`·`iterator` | `iter(x) is x` 의 참·거짓 · `__next__` 유무 |
> | (판이 오르면) **예외 문구** 전부 | 예외 **종류**(`StopIteration`·`RuntimeError`·`TypeError`) |
> | (판이 오르면) `gi_*` 속성의 있고 없음 | **소진 여부**와 「소진과 공집합이 구분 안 된다」는 사실 |
> | — | `File "<stdin>", line N` · `__getitem__` 이 **몇 번** 불렸나 |
>
> ★ **이 주제의 실행 출력은 전부 결정적이다** — 같은 판에서 다시 돌리면 한 글자도 안 변한다(수치·주소를 안 찍는다).\
> ★ **단 한 블록만 stdout 과 stderr 가 섞인다**(PEP 479 — `[1, 2]` 다음에 트레이스백).
> 파이프로 받아 **세 판을 md5 로 대조해 순서가 같음을 확인**했다 — CPython 이 트레이스백을 찍기 전에 stdout 을 flush 하기 때문이다.
>
> **선행** — [15-generator-expressions-lazy-eval](../15-generator-expressions-lazy-eval/2-summary.md)(지연의 값어치) ·
> [09-sequence-ops-and-slicing](../09-sequence-ops-and-slicing/2-summary.md)(시퀀스가 무엇인가).\
> **정본 이웃** — [17-generators-yield](../17-generators-yield/2-summary.md)가 **제너레이터의 정본**이다.
> `yield`·프레임·`send`·`close`·`yield from` 은 전부 그쪽이고, 여기는 **「제너레이터가 아닌 것까지 포함한 계약」** 만 다룬다.

## 한눈에 — 쉽게 말하면

**이터러블은 「번호표 뽑는 기계」이고, 이터레이터는 「뽑아 든 번호표」다.**

- 기계(`list`·`range`·`str`)에 가면 **새 번호표**가 나온다. 몇 번이고 다시 뽑을 수 있다.
- 번호표(`list_iterator`·제너레이터)는 **한 장뿐**이다. 다 쓰면 끝이고, 다시 가서 뽑아야 한다.
- ★ **번호표에게 「번호표 주세요」 하면 자기 자신을 준다.** 그래야 `for` 가 둘을 구분 안 하고 쓸 수 있다.

```text
   이터러블(기계)                       이터레이터(번호표)
   ┌─────────────┐                      ┌──────────────┐
   │ [1, 2, 3]   │ ── iter() ──>        │ 커서: 0번 앞  │
   │ 값을 들고 있다│ ── iter() ──>        │ 커서: 0번 앞  │  <- 또 부르면 새것
   └─────────────┘                      └──────────────┘
         iter(x) is x  ->  False              iter(x) is x  ->  True
         __next__ 없음                        __next__ 있음
```

★ **`iter(x) is x` 한 줄이 둘을 가른다.** 이 문서에서 가장 많이 쓰는 검사다.

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 번호표 기계 | 이터러블 | `iter(x) is x` 가 `False` |
| 뽑아 든 번호표 | 이터레이터 | `iter(x) is x` 가 `True` |
| 번호표에 「번호표 주세요」 | `__iter__` 가 `self` 반환 | 계약이다. 안 지키면 객체가 거짓말을 한다 |
| 다음 번호 | `__next__` | `getattr(o, '__next__', None)` |
| 「더 없습니다」 | `StopIteration` | `for` 가 잡아 조용히 빠져나간다 |
| ★ **다 쓴 표와 빈 표가 똑같이 생겼다** | 소진 대 공집합 | **바깥에서는 구분이 안 된다** |
| 옛날 기계 — 1번부터 불러 보기 | `__getitem__` 대체 경로 | `__iter__` 가 없어도 `for` 가 돈다 |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.\
「**함수에 넘긴 이터러블이 두 번째 루프에서 비어 있었다**」가 그것이다.
호출한 쪽은 리스트를 준 줄 알았고 실제로는 `map` 이나 제너레이터를 줬다. **에러가 안 난다.**

> **이터러블(iterable)** — `iter()` 를 걸 수 있는 것. 리스트·문자열·dict·파일 전부.\
> 예: `for` 가 받아 주는 것은 전부 이터러블이다.

> **이터레이터(iterator)** — `__next__()` 로 다음 값을 하나씩 꺼낼 수 있고, `__iter__()` 가 **자기 자신**을 돌려주는 것.\
> 예: `iter([1,2])` 의 결과. 한 방향으로만 가고 되감기가 없다.

## 이 주제가 답하려는 질문

1. **`for` 는 안에서 무엇을 하나** — `iter`·`next`·`StopIteration` 세 조각으로 손으로 재현할 수 있나.
2. **계약이 정확히 무엇인가** — `__iter__` 만 있으면 되나, `__next__` 만 있으면 되나, **둘 다 없어도 되나.**
3. **소진된 것과 원래 빈 것을 어떻게 구분하나** — ★ 결론부터 말하면 **바깥에서는 구분이 안 된다.** 그것이 이 주제의 조용한 실패다.

## 동작 방식

> 이 절이 본문이다. 이 주제의 네 번째 창은 **객체 상태**다 —
> `iter(x) is x` · `getattr(o, '__next__', None)` · `gi_frame`·`gi_running`·`gi_suspended`.
> 값만 보면 **소진된 것과 빈 것이 같아 보인다.**

### 1. ★ `for` 를 손으로 뜯어 보면 세 조각이다

**언제 쓰나** — `for` 가 왜 `StopIteration` 을 안 보여 주는지 궁금할 때.

```text
   for item in xs:              와 같다        it = iter(xs)        <- ①
       본문                                    while True:
                                                   try:
                                                       item = next(it)   <- ②
                                                   except StopIteration: <- ③
                                                       break
                                                   본문
```

```text
===== 소스: ex.py =====
xs = ["a", "b"]
it = iter(xs)
print("iter(xs)        ->", type(it).__name__)
print("next            ->", next(it))
print("next            ->", next(it))
try:
    next(it)
except StopIteration as e:
    print("next            -> StopIteration", repr(e.value), "| args =", e.args)
print("next(it, '기본') ->", next(it, "기본"))
print("두 번째 list(it) ->", list(it), " <- 예외가 아니다")
```

```text
iter(xs)        -> list_iterator
next            -> a
next            -> b
next            -> StopIteration None | args = ()
next(it, '기본') -> 기본
두 번째 list(it) -> []  <- 예외가 아니다
```

그림 해설.

- ① **`iter(xs)` 가 `list` 가 아니라 `list_iterator` 를 낸다.** 리스트 자신은 커서를 안 들고 있다.
- ② `next` 두 번에 값이 다 나오고,
- ③ 세 번째가 **`StopIteration`**. `for` 는 이것을 잡아 **조용히 빠져나간다** — 그래서 사용자는 볼 일이 없다.
- ★ **`next(it, 기본값)`** 을 주면 예외 대신 그 값이 나온다. **예외를 안 보고 끝을 감지하는 유일한 내장 수단**이다.
- ★ **소진 뒤 `list(it)` 가 `[]`** 다. 문서가 계약으로 못 박는다 —
  *"Once an iterator's `__next__()` method raises `StopIteration`, it must **continue to do so on subsequent calls**."*\
  즉 **「빈 것이 나오는 것」은 구현 편의가 아니라 명세**다.

★ `for` 가 제너레이터를 어떻게 소비하는지는 [17번](../17-generators-yield/2-summary.md)이 같은 그림을 제너레이터 쪽에서 그린다.
여기서는 **제너레이터가 아닌 것**(리스트·파일·`map`)에도 같은 세 조각이 쓰인다는 것이 요점이다.

**비용** — `for` 한 줄이 세 조각을 감춘다. 덕분에 리스트든 파일이든 무한 수열이든 문법이 하나다.\
대신 **`StopIteration` 이 눈에 안 보이므로** 그것이 엉뚱한 데서 새면 원인을 못 찾는다(동작 5).

### 2. ★ 둘을 가르는 한 줄 — `iter(x) is x`

**언제 쓰나** — 「이걸 두 번 돌려도 되나」를 판단할 때. 함수가 받은 인자를 신뢰해도 되나 판단할 때.

```text
===== 소스: ex.py =====
import sys
print("python", ".".join(map(str, sys.version_info[:3])))

def gen():
    yield 1

objs = [
    ("[1, 2]", [1, 2]),
    ("iter([1, 2])", iter([1, 2])),
    ("(1, 2)", (1, 2)),
    ("'ab'", "ab"),
    ("range(3)", range(3)),
    ("iter(range(3))", iter(range(3))),
    ("gen()", gen()),
    ("enumerate('ab')", enumerate("ab")),
    ("zip('ab', 'cd')", zip("ab", "cd")),
    ("map(str, [1])", map(str, [1])),
    ("reversed([1, 2])", reversed([1, 2])),
]
print(f"{'object':<16}{'__iter__':>9}{'__next__':>10}{'iter(x) is x':>14}")
for name, o in objs:
    print(f"{name:<16}{str(hasattr(o, '__iter__')):>9}"
          f"{str(getattr(o, '__next__', None) is not None):>10}{str(iter(o) is o):>14}")
```

```text
python 3.12.3
object           __iter__  __next__  iter(x) is x
[1, 2]               True     False         False
iter([1, 2])         True      True          True
(1, 2)               True     False         False
'ab'                 True     False         False
range(3)             True     False         False
iter(range(3))       True      True          True
gen()                True      True          True
enumerate('ab')      True      True          True
zip('ab', 'cd')      True      True          True
map(str, [1])        True      True          True
reversed([1, 2])     True      True          True
```

그림 해설 — 표의 세 열이 각각 무엇을 말한다.

- **`__iter__` 열은 아무것도 못 가른다** — 전부 `True` 다. **이터러블이냐 아니냐만** 말한다.
- ★ **`__next__` 열과 `iter(x) is x` 열이 정확히 같다.** 이것이 계약이다 —
  문서 — *"iterators are required to have an `__iter__()` method that **returns the iterator object itself**."*
- ★★ **`enumerate`·`zip`·`map`·`reversed` 가 전부 이터레이터 쪽이다.**
  「리스트를 줬겠지」 하고 받은 인자가 이쪽이면 **두 번째 루프가 조용히 빈 것이 된다.**
- ★ **`range` 는 이터레이터가 아니다.** `iter(r) is r` 이 `False` 라 **몇 번이든 다시 돈다** — 이 성질은 [18번](../18-loop-control-and-else/2-summary.md)이 정본이다.

**비용** — 이 구분 덕에 `for` 가 둘 다 받는다.\
대신 **타입 이름만 봐서는 안 보인다.** `map` 객체와 리스트는 `print` 로도 잘 구분이 안 간다.

### 3. ★ 계약을 직접 써 보면 — 기계와 번호표를 분리한다

**언제 쓰나** — 내 클래스를 `for` 에 넣고 싶을 때. 「왜 두 번째 루프가 비나」를 고칠 때.

```text
   Countdown (기계)                  CountdownIter (번호표)
   __iter__ -> 새 CountdownIter      __iter__ -> self
                                     __next__ -> 값 또는 StopIteration

   for x in c:  -> 매번 새 번호표      for x in it: -> 그 번호표 하나
   두 번 돌면 둘 다 나온다              두 번 돌면 두 번째가 빈다
```

```text
===== 소스: ex.py =====
class Countdown:              # 이터러블 — 돌 때마다 새 이터레이터를 준다
    def __init__(self, n): self.n = n
    def __iter__(self): return CountdownIter(self.n)

class CountdownIter:          # 이터레이터 — 자기 자신을 돌려준다
    def __init__(self, n): self.k = n
    def __iter__(self): return self
    def __next__(self):
        if self.k <= 0:
            raise StopIteration
        self.k -= 1
        return self.k + 1

c = Countdown(3)
print("두 번 돌린다 :", list(c), list(c))
it = iter(c)
print("이터레이터를 직접 두 번 :", list(it), list(it))
print("iter(c) is c :", iter(c) is c, "| iter(it) is it :", iter(it) is it)

class Broken:                 # __iter__ 가 자기를 안 돌려주는 이터레이터
    def __iter__(self): return CountdownIter(2)
    def __next__(self): raise StopIteration

b = Broken()
print("__next__ 는 있는데 __iter__ 가 남을 주면 :", list(b))
print("  next(b) 는 :", end=" ")
try:
    next(b)
except StopIteration:
    print("StopIteration")

class NoNext:
    def __iter__(self): return self
n = NoNext()
try:
    for _ in n: pass
except TypeError as e:
    print("__next__ 없이 __iter__ 만 :", type(e).__name__ + ":", e)
```

```text
두 번 돌린다 : [3, 2, 1] [3, 2, 1]
이터레이터를 직접 두 번 : [3, 2, 1] []
iter(c) is c : False | iter(it) is it : True
__next__ 는 있는데 __iter__ 가 남을 주면 : [2, 1]
  next(b) 는 : StopIteration
__next__ 없이 __iter__ 만 : TypeError: iter() returned non-iterator of type 'NoNext'
```

그림 해설.

- **기계를 두 번 돌리면 둘 다 나오고, 번호표를 두 번 돌리면 두 번째가 빈다.** 같은 데이터인데 결과가 다르다.
- ★★ **`Broken` 이 이 절의 핵심이다.** `__iter__` 가 자기가 아닌 남을 돌려주자
  **`list(b)` 는 `[2, 1]` 인데 `next(b)` 는 즉시 `StopIteration`** 이다. **같은 객체가 두 얼굴을 갖는다.**\
  ★ **예외도 경고도 없다.** 계약 위반을 언어가 잡아 주지 않는다 — 그래서 「`__iter__` 는 `self` 를 돌려준다」가 **외워야 하는 규칙**이다.
- **`NoNext` 는 잡힌다** — `__iter__` 가 `__next__` 없는 것을 돌려주면 `TypeError: iter() returned non-iterator` 다.
  ★ **한쪽(`__next__` 없음)은 잡히고 한쪽(`__iter__` 가 남을 줌)은 안 잡힌다.**

**비용** — 기계와 번호표를 나누면 **몇 번이든 도는 객체**가 된다.\
대신 클래스가 둘이 된다. 그래서 실무에서는 `__iter__` 를 **제너레이터 함수로** 쓰는 쪽이 더 흔하다([17번](../17-generators-yield/2-summary.md)).

### 4. ★ `__iter__` 가 없어도 `for` 가 돈다 — 낡은 프로토콜

**언제 쓰나** — 남의 클래스가 왜 `for` 에 들어가는지 설명이 안 될 때.

문서가 그 대체 경로를 적는다 — *"If the object is a sequence, ... the iteration protocol via the special method
`__getitem__()` with integer arguments starting at 0 ... **falls back**"*(즉 `__iter__` 가 없으면 `__getitem__` 을 0부터 부른다).

```text
   for v in o:   -- __iter__ 가 없다 --> o[0], o[1], o[2], ...
                                         IndexError 가 나면 끝
```

```text
===== 소스: ex.py =====
class Old:
    def __init__(self, data): self.data = data
    def __getitem__(self, i):
        print("   __getitem__", i)
        return self.data[i]

o = Old(["x", "y"])
print("__iter__ 가 있나 :", hasattr(o, "__iter__"))
print("__next__ 가 있나 :", getattr(o, "__next__", None) is not None)
print("for 가 도나 :")
for v in o:
    print("  받음:", v)
print("iter(o) ->", type(iter(o)).__name__)
print("list(o) ->", list(o))
print("'x' in o ->", "x" in o)
print("reversed 는?")
try:
    print(list(reversed(o)))
except TypeError as e:
    print("   TypeError:", e)
```

```text
__iter__ 가 있나 : False
__next__ 가 있나 : False
for 가 도나 :
   __getitem__ 0
  받음: x
   __getitem__ 1
  받음: y
   __getitem__ 2
iter(o) -> iterator
   __getitem__ 0
   __getitem__ 1
   __getitem__ 2
list(o) -> ['x', 'y']
   __getitem__ 0
'x' in o -> True
reversed 는?
   TypeError: object of type 'Old' has no len()
```

그림 해설 — 찍힌 인덱스를 세어 보면 규칙이 보인다.

- ★ **두 값을 얻는 데 `__getitem__` 이 세 번 불렸다**(0·1·2). **끝은 `IndexError` 로 알려진다.**
  그 `IndexError` 는 `StopIteration` 으로 **번역돼** 바깥에 안 나온다.
- ★ **`__iter__` 도 `__next__` 도 없는데 `for` 가 돈다.** `hasattr(o, '__iter__')` 로 「이터러블인가」를 검사하면 **틀린 답**을 얻는다.
- `iter(o)` 는 **`iterator`** 라는 이름의 대체 이터레이터를 만들어 준다. 즉 **언어가 번호표를 대신 만들어 준다.**
- `in` 도 같은 경로를 탄다 — `'x'` 를 0번에서 찾고 멈췄다.
- ★ **`reversed` 는 안 된다** — `__len__` 이 있어야 하기 때문이다. **대체 경로가 모든 것을 대체하지는 않는다.**

★ 「이터러블인가」를 제대로 검사하려면 `hasattr` 이 아니라 **`iter(x)` 를 걸어 보고 `TypeError` 를 잡는 것**이다.

**비용** — 옛 코드가 그대로 돈다(PEP 234 이전 호환).\
대신 **검사로는 안 보이고**, `IndexError` 를 내야 끝나므로 **엉뚱한 `IndexError` 가 나면 루프가 조용히 일찍 끝난다.**

### 5. ★ `StopIteration` 이 제너레이터 안에서 새면 `RuntimeError` 다 (PEP 479)

**언제 쓰나** — 제너레이터 안에서 `next(다른것)` 을 부를 때. 곧 **파이프라인을 짤 때 전부**다.

```text
   제너레이터 안에서 StopIteration 이 새면

   3.6 이전 :  바깥의 for 가 그것을 "끝났다" 로 읽는다  -> 조용히 잘린다
   3.7 이후 :  RuntimeError 로 바뀐다                 -> 터진다
```

```text
===== 소스: ex.py =====
def take_two(it):
    yield next(it)
    yield next(it)

print(list(take_two(iter([1, 2]))))
print(list(take_two(iter([1]))))
```

```text
[1, 2]
Traceback (most recent call last):
  File "<stdin>", line 3, in take_two
StopIteration

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "<stdin>", line 6, in <module>
RuntimeError: generator raised StopIteration
```

그림 해설 — 트레이스백 두 덩어리가 각각 무엇인지.

- 첫 덩어리가 **원인**이다 — `take_two` 3번 줄의 `next(it)` 가 `StopIteration` 을 냈다.
- `The above exception was the **direct cause** of` — `__cause__` 로 이어 붙였다는 뜻이다. **원인이 안 지워진다.**
- 둘째 덩어리가 **바깥으로 나온 것** — `RuntimeError: generator raised StopIteration`.
- ★★ **3.6 이전에는 이것이 예외가 아니었다.** `list(...)` 가 `[1]` 을 조용히 돌려줬다 —
  **두 개를 달라고 했는데 하나만 오고 아무도 안 알려 주는** 상태였다. PEP 479 가 그 무음 실패를 **시끄러운 실패로 바꾼 것**이다.
- 고치는 법은 **끝을 명시적으로 다루는 것**이다 — `next(it, None)` 로 기본값을 주거나 `try/except StopIteration: return`.

★ 이 판(3.12.3)에는 끄는 스위치가 없다. **3.5\~3.6 에서만** `from __future__ import generator_stop` 로 미리 켜 볼 수 있었고,
**3.7 부터 무조건**이다(PEP 479). 이 머신에 3.6 이하가 없어 **옛 동작은 직접 못 돌려 봤다** — PEP 문서 근거다.

**비용** — 조용히 잘리던 버그가 터져서 보인다.\
대신 **제너레이터 안에서 `next()` 를 맨손으로 쓰는 관용구가 위험해졌다** — 기본값을 주거나 잡아야 한다.

### 6. ★★ 소진된 것과 빈 것은 구분되지 않는다 — 이 주제의 조용한 실패

**언제 쓰나** — 「왜 결과가 비어 있지」를 조사할 때. 이 주제의 값이 여기 몰린다.

```text
===== 소스: ex.py =====
def src():
    yield 1
    yield 2

full  = src()
spent = src(); list(spent)
empty = iter([])
worn  = iter([1]); next(worn)

print("--- 바깥에서 보이는 것만으로 넷을 가를 수 있나 ---")
rows = [("아직 안 돈 제너레이터", full), ("소진된 제너레이터", spent),
        ("처음부터 빈 이터레이터", empty), ("소진된 리스트 이터레이터", worn)]
for name, o in rows:
    print("  bool={0!s:<5} iter(x) is x={1!s:<5} next(x,'없음')={2!r:<8} <- {3}".format(
        bool(o), iter(o) is o, next(o, "없음"), name))

print()
print("--- 제너레이터만은 안이 보인다 (CPython 내성) ---")
a = src()
def snap(tag, g):
    print("  {0:<10} gi_frame={1!s:<6} gi_running={2!s:<6} gi_suspended={3!s:<6}".format(
        tag, g.gi_frame is not None, g.gi_running, g.gi_suspended))
snap("만든 직후", a); next(a); snap("next 1회", a); list(a); snap("소진 후", a)

print()
print("--- 남은 개수 힌트도 둘을 못 가른다 ---")
b = iter([1, 2])
print("  소진 전 iter([1,2]).__length_hint__() =", b.__length_hint__())
list(b)
print("  소진 후                               =", b.__length_hint__())
print("  iter([]).__length_hint__()            =", iter([]).__length_hint__())
```

```text
--- 바깥에서 보이는 것만으로 넷을 가를 수 있나 ---
  bool=True  iter(x) is x=True  next(x,'없음')=1        <- 아직 안 돈 제너레이터
  bool=True  iter(x) is x=True  next(x,'없음')='없음'     <- 소진된 제너레이터
  bool=True  iter(x) is x=True  next(x,'없음')='없음'     <- 처음부터 빈 이터레이터
  bool=True  iter(x) is x=True  next(x,'없음')='없음'     <- 소진된 리스트 이터레이터

--- 제너레이터만은 안이 보인다 (CPython 내성) ---
  만든 직후      gi_frame=True   gi_running=False  gi_suspended=False 
  next 1회    gi_frame=True   gi_running=False  gi_suspended=True  
  소진 후       gi_frame=False  gi_running=False  gi_suspended=False 

--- 남은 개수 힌트도 둘을 못 가른다 ---
  소진 전 iter([1,2]).__length_hint__() = 2
  소진 후                               = 0
  iter([]).__length_hint__()            = 0
```

그림 해설 — 네 줄을 세로로 읽는다.

- ★★ **`bool` 이 넷 다 `True` 다.** 빈 이터레이터도 **참**이다 — 리스트와 정반대다(`bool([])` 은 `False`).
  **`if it:` 로 「값이 있나」를 검사하면 언제나 참이다.**
- ★★ **아래 세 줄이 한 글자도 다르지 않다.** 소진된 제너레이터 · 처음부터 빈 것 · 소진된 리스트 이터레이터 —
  **어떤 검사로도 안 갈린다.**
- ★ **그리고 검사하는 행위 자체가 값을 먹는다.** 첫 줄의 `next(x,'없음')` 이 `1` 을 반환하며 **그 값을 꺼내 버렸다.**
  「남았나」를 물어보면 **남은 것이 줄어든다.**
- **`__length_hint__` 도 못 가른다** — 소진된 것과 빈 것이 둘 다 `0` 이다. 그리고 문서상 **힌트일 뿐** 보장이 아니다.

**★ 제너레이터만은 반쯤 보인다 — 그러나 그것은 CPython 내성이다**

```text
   만든 직후 : gi_frame 있음  gi_suspended False   <- 아직 시작 전
   next 1회 : gi_frame 있음  gi_suspended True    <- yield 에서 멈춤
   소진 후   : gi_frame None  gi_suspended False   <- 프레임을 놓았다
```

- ★ **`gi_frame` 이 `None` 이면 「끝났다」는 것을 알 수 있다.** 하지만 **`close()` 로 닫힌 것과 구분은 안 된다.**
- ★ **리스트 이터레이터·`map`·`zip` 에는 이런 창이 아예 없다.** 제너레이터만 있는 특권이고, **CPython 의 내성 기능**이다.
- 상태의 이름과 전이(`GEN_CREATED`\~`GEN_CLOSED`)는 [17번](../17-generators-yield/2-summary.md)이 정본이다.

★★ **결론 — 구분하려면 객체를 안 믿고 「흐름을 바꾸는」 수밖에 없다.**

| 하고 싶은 것 | 안 되는 법 | 되는 법 |
|---|---|---|
| 「값이 있나」 검사 | `if it:` (**언제나 참**) | `first = next(it, 센티널)` 로 하나 꺼내 보고 되돌릴 수 없음을 받아들인다 |
| 두 번 돌기 | 같은 이터레이터를 두 번 | `xs = list(it)` 로 **한 번만** 물질화 |
| 함수가 받은 것을 믿기 | 타입 이름 보기 | `if iter(x) is x: x = list(x)` 로 **방어적 물질화** |
| 「몇 개냐」 | `len(it)` (`TypeError`) | `sum(1 for _ in it)` — **그 순간 소진된다** |

**비용** — 구분이 안 되는 대신 **`for` 가 모든 것을 똑같이 받는다.**\
대가는 **디버깅이 안 되는 무음 실패**다. 「결과가 비었다」의 원인이 코드가 아니라 **이미 지나간 소비**에 있다.

## 문법 — 형태와 규칙

```python
it = iter(x)                 # 이터러블 -> 이터레이터
it = iter(callable, sentinel)  # ★ 두 인자 꼴 — callable() 이 sentinel 과 같아질 때까지
next(it)                     # 다음 값, 없으면 StopIteration
next(it, 기본값)              # 없으면 기본값 (예외 없음)

class C:
    def __iter__(self): return self      # 이터레이터의 계약
    def __next__(self):
        if 끝: raise StopIteration
        return 값

class D:
    def __iter__(self): return iter(...)  # 이터러블 — 매번 새 이터레이터
```

규칙 여섯.

1. **이터러블은 `__iter__` 만**, **이터레이터는 `__iter__` + `__next__`** 를 갖는다.
2. **이터레이터의 `__iter__` 는 반드시 `self`** 를 돌려준다. **안 지켜도 언어가 안 잡아 준다.**
3. **`StopIteration` 은 한 번 내면 계속 내야** 한다(명세). 그래서 두 번째가 빈 결과다.
4. **`__iter__` 가 없어도 `__getitem__`(0부터)만 있으면 `for` 가 돈다.** 끝은 `IndexError` 로 알린다.
5. **제너레이터 안에서 새어 나온 `StopIteration` 은 `RuntimeError`** 가 된다(3.7+, PEP 479).
6. **이터레이터는 언제나 참이다.** `if it:` 로 빈 것을 검사할 수 없다.

**★ 두 인자 꼴 — 「센티널이 나올 때까지 계속 부르기」**

```text
===== 소스: ex.py =====
import io
buf = io.StringIO("ab\ncd\nef\n")
print("--- iter(callable, sentinel) ---")
it = iter(lambda: buf.readline(), "")
print("타입      :", type(it).__name__)
print("iter(it) is it :", iter(it) is it)
for line in it:
    print("  받음:", repr(line))

steps = iter([3, 1, 0, 9].pop, 0)
print("--- pop 이 0 을 낼 때까지 ---")
print(list(steps))

print("--- 한 인자 iter 와 두 인자 iter 는 다른 타입이다 ---")
print("iter([1])            ->", type(iter([1])).__name__)
print("iter(lambda: 1, 0)   ->", type(iter(lambda: 1, 0)).__name__)
```

```text
--- iter(callable, sentinel) ---
타입      : callable_iterator
iter(it) is it : True
  받음: 'ab\n'
  받음: 'cd\n'
  받음: 'ef\n'
--- pop 이 0 을 낼 때까지 ---
[9]
--- 한 인자 iter 와 두 인자 iter 는 다른 타입이다 ---
iter([1])            -> list_iterator
iter(lambda: 1, 0)   -> callable_iterator
```

★ **두 인자 꼴은 「인자 없는 함수를 반복해서 부르는 `while` 문」을 이터레이터로 바꿔 준다.**
`readline()` 이 `""` 를 낼 때까지, 큐가 비어 센티널을 낼 때까지 — **`while True: v = f(); if v == s: break` 를 한 줄로** 줄인다.\
★ **`[3,1,0,9].pop` 이 `[9]` 만 낸 것**은 `pop()` 이 **뒤에서** 빼기 때문이다 — `9` 를 내고 그다음 `0` 이 센티널과 같아 멈췄다.
**센티널은 결과에 안 들어간다.**

**금지 사례 — 에러가 나는 자리**

```python
next([1, 2])             # TypeError — 리스트는 이터레이터가 아니다
len(iter([1, 2]))        # TypeError — 개수를 모른다
iter([1,2])[0]           # TypeError — 첨자가 없다
class C: __iter__ = lambda self: self      # for 에 넣으면 TypeError (__next__ 없음)
```

```text
===== 소스: ex.py =====
try:
    next([1, 2])
except TypeError as e:
    print("next([1,2])      ->", type(e).__name__ + ":", e)
try:
    len(iter([1, 2]))
except TypeError as e:
    print("len(iter([1,2])) ->", type(e).__name__ + ":", e)
try:
    iter([1, 2])[0]
except TypeError as e:
    print("iter([1,2])[0]   ->", type(e).__name__ + ":", e)
```

```text
next([1,2])      -> TypeError: 'list' object is not an iterator
len(iter([1,2])) -> TypeError: object of type 'list_iterator' has no len()
iter([1,2])[0]   -> TypeError: 'list_iterator' object is not subscriptable
```

★ **첫 문구가 정확히 이 주제의 이름을 부른다** — *"`'list'` object is **not an iterator**"*.
리스트는 이터**러블**이지 이터**레이터**가 아니라는 것을 언어가 직접 말해 준다.

## 어디서 틀리나

### (1) 이터러블과 이터레이터를 같은 것으로 안다

`iter(x) is x` 로 갈린다. **`map`·`zip`·`enumerate`·`filter`·`reversed`·제너레이터**가 전부 이터레이터 쪽이다.

### (2) 함수가 받은 것을 두 번 돈다

호출한 쪽이 리스트를 줄지 `map` 을 줄지 모른다.\
고치는 법: `if iter(x) is x: x = list(x)` 로 **방어적으로 물질화**한다.

### (3) `if it:` 로 빈 것을 검사한다

**이터레이터는 언제나 참**이다. 빈 것도 참이다. `next(it, 센티널)` 을 써야 하고, **그러면 하나가 사라진다.**

### (4) 소진된 것과 빈 것을 구분하려 한다

★ **바깥에서는 구분이 안 된다.** `bool`·`iter(x) is x`·`next(x, 기본)`·`__length_hint__` 가 전부 같다.

### (5) 검사하는 행위가 값을 먹는 것을 잊는다

`next(it, None)` 도, `3 in it` 도, `any(it)` 도 **꺼내 버린다.** 되돌릴 수 없다.

### (6) `hasattr(x, '__iter__')` 로 「이터러블인가」를 검사한다

★ **`__getitem__` 만 있는 것을 놓친다.** `iter(x)` 를 걸어 보고 `TypeError` 를 잡는 것이 바른 검사다.

### (7) 이터레이터의 `__iter__` 가 `self` 를 안 돌려준다

★ **예외가 안 난다.** `for` 와 `next()` 가 **다른 답**을 내는 객체가 된다.

### (8) 제너레이터 안에서 `next()` 를 맨손으로 쓴다

안쪽이 끝나면 `RuntimeError: generator raised StopIteration` 이다(3.7+).\
`next(it, None)` 로 기본값을 주거나 잡아서 `return` 해야 한다.

### (9) `__getitem__` 안에서 `IndexError` 를 내는 코드를 쓴다

낡은 프로토콜로 도는 객체라면 **루프가 조용히 일찍 끝난다.** 예외가 끝 신호로 번역되기 때문이다.

### (10) `list(it)` 를 두 번 쓴다

두 번째가 `[]` 다. **명세가 그렇게 정했다** — 버그가 아니다.

## 구현 세부사항 대 언어 보장

세 층으로 가른다. ★ **이 주제는 「언어 보장」이 두껍고 「관찰」이 얇다** —
프로토콜 자체가 명세이기 때문이다. 구현 쪽에 남는 것은 **들여다보는 창과 타입 이름**이다.

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **언어 보장** | 라이브러리·언어 레퍼런스가 정한 것 | 공식 문서 문장을 열어서 인용 |
| **CPython 구현** | 이 구현이 그렇게 하는 것 | 실행 + `gi_*` 내성 + 타입 이름 |
| **이 판의 관찰** | 3.12.3 에서 그랬을 뿐 | 「관찰」로 명기 |

### 언어 보장

| 사실 | 근거 |
|---|---|
| 이터레이터는 **`__iter__` 가 자기 자신**을 돌려줘야 한다 | Iterator Types — *"required to have an `__iter__()` method that returns the iterator object itself"* |
| `__next__` 는 다음 값을, 없으면 **`StopIteration`** 을 낸다 | 〃 |
| **한 번 `StopIteration` 을 내면 계속 내야** 한다 | 〃 — *"must continue to do so on subsequent calls"* |
| `__iter__` 가 없고 **`__getitem__`(0부터)만 있으면** 대체 경로로 순회된다 | `iter()` — 시퀀스 프로토콜 대체 |
| `iter(callable, sentinel)` 두 인자 꼴 — 센티널이 나오면 멈춘다(**센티널은 안 낸다**) | `iter()` |
| `next(it, default)` 는 예외 대신 기본값을 낸다 | `next()` |
| 제너레이터 안에서 새어 나온 `StopIteration` 은 **`RuntimeError`** 가 된다 | **PEP 479** — 3.7 부터 무조건 |
| `__length_hint__` 는 **힌트일 뿐** 정확할 의무가 없다 | `operator.length_hint` |

★ **「소진되면 빈 결과」가 언어 보장이다.** 「구현이 편해서」가 아니라 **계약 문장에서 따라 나온다.**

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| 타입 이름 `list_iterator`·`range_iterator`·`callable_iterator`·`iterator`(대체 경로) | 실행 — **이름은 구현의 것**이다 |
| `gi_frame`·`gi_running`·`gi_suspended` 로 제너레이터 안을 본다 | 실행 — **제너레이터에만** 있다. 3.11.15 에도 있었다 |
| 소진된 제너레이터의 `gi_frame` 이 `None` 이 된다 | 실행 |
| `list_iterator.__length_hint__()` 가 소진 후 `0` | 실행 — **힌트**라 보장이 아니다 |
| 리스트 이터레이터가 **정수 커서**로 구현된 것 | 실행([18번](../18-loop-control-and-else/2-summary.md)의 순회 중 변경이 그 증거다) |
| `iter()` 가 대체 경로용 이터레이터를 **대신 만들어 주는 것** | 실행 — `type(iter(o)).__name__` 이 `iterator` |
| 예외 **문구** 전부 | 실행 |

### 이 판(3.12.3)의 관찰

| 관찰 | 어디가 흔들리나 |
|---|---|
| `TypeError: 'list' object is not an iterator` 등 문구 | 예외 **종류**는 명세지만 문구는 아니다 |
| `RuntimeError: generator raised StopIteration` 문구 | 위와 같다 |
| 트레이스백이 **두 덩어리**로 나오는 것(`direct cause`) | 예외 체이닝의 표시 방식 |
| `gi_suspended` 가 있는 것 | 3.11.15 에도 있었다 — **그래도 명세가 아니다** |
| `iter([3,1,0,9].pop, 0)` 이 `[9]` 인 것 | `list.pop()` 이 뒤에서 뺀다는 **문서화된 동작**의 결과 |
| `__getitem__` 이 **3번** 불린 것(값 2개에) | 대체 경로가 `IndexError` 로 끝을 안다는 결과 |

### 그래서 이렇게 적으면 틀린다

- ✗ 「이터러블과 이터레이터는 같은 말이다」\
  ○ `iter(x) is x` 로 갈린다. **`map`·`zip`·`enumerate` 는 이터레이터 쪽**이다.
- ✗ 「`for` 에 들어가면 `__iter__` 가 있는 것이다」\
  ○ **`__getitem__` 만 있어도 돈다.** `hasattr` 검사는 그것을 놓친다.
- ✗ 「소진된 이터레이터는 `False` 다」\
  ○ **언제나 참**이다. `bool` 로는 아무것도 못 안다.
- ✗ 「소진된 것과 빈 것은 구분할 수 있다」\
  ○ **바깥에서는 못 한다.** 네 가지 검사가 전부 같은 답을 준다.
- ✗ 「`__iter__` 에 `self` 말고 다른 걸 돌려줘도 잘 돌던데」\
  ○ **`for` 와 `next()` 가 다른 답을 내는** 객체가 된다. 예외가 안 나서 더 나쁘다.
- ✗ 「제너레이터 안에서 `next()` 를 그냥 쓰면 된다」\
  ○ 안쪽이 끝나면 **`RuntimeError`** 다(3.7+). 기본값을 주거나 잡아야 한다.
- ✗ 「`gi_frame` 으로 상태를 볼 수 있으니 이터레이터 상태는 알 수 있다」\
  ○ **제너레이터에만 있고 CPython 의 내성 기능**이다. `map`·`zip` 에는 그런 창이 없다.
- ✗ 「`__length_hint__` 로 남은 개수를 알 수 있다」\
  ○ **힌트**다. 정확할 의무가 없고, 소진과 공집합을 못 가른다.

**판정 기준 한 줄**: **「두 번 돌아도 되나」를 물으면 `iter(x) is x` 를 보고, 「왜 비었나」를 물으면 객체가 아니라 「누가 먼저 소비했나」를 보라.**

## 언제 쓰고 언제 안 쓰나

| 상황 | 판정 |
|---|---|
| 내 객체를 `for` 에 넣고 싶다 | **`__iter__` 를 제너레이터 함수로** 쓴다 — 가장 짧고 계약 위반이 안 난다 |
| 여러 번 돌 수 있어야 한다 | **이터러블 클래스**(`__iter__` 가 매번 새것을 준다) |
| 한 번만 돌고 상태를 들고 있다 | **이터레이터 클래스**(`__iter__` 는 `self`) |
| 「센티널이 나올 때까지 반복 호출」 | **`iter(callable, sentinel)`** — `while` 문보다 짧고 `for` 에 바로 들어간다 |
| 끝을 예외 없이 감지하고 싶다 | **`next(it, 센티널)`** |
| 함수가 받은 것을 두 번 돌아야 한다 | **`list()` 로 물질화** — `iter(x) is x` 로 판정한 뒤 |
| 남은 개수를 알고 싶다 | **방법이 없다** — 세면 소진된다. 개수가 필요하면 애초에 시퀀스를 쓴다 |
| 낡은 `__getitem__` 프로토콜을 새로 쓴다 | **쓰지 않는다** — 읽는 사람이 못 알아본다. `__iter__` 를 쓴다 |

## 핵심 문장

- **이터러블은 기계, 이터레이터는 번호표**다. `iter(x) is x` 한 줄이 둘을 가른다.
- **이터레이터의 `__iter__` 는 자기 자신을 돌려주는 것이 계약**이다 — 어기면 `for` 와 `next()` 가 다른 답을 내는데 **예외가 안 난다.**
- **`for` 는 `iter` + 반복 `next` + `StopIteration` 잡기** 세 조각이다. 그래서 두 번째 순회가 **에러가 아니라 빈 결과**다 — 그것이 **명세**다.
- **`__iter__` 가 없어도 `__getitem__`(0부터)만 있으면 `for` 가 돈다.** 끝은 `IndexError` 로 알린다 — `hasattr` 검사가 놓치는 자리다.
- **`iter(callable, sentinel)`** 두 인자 꼴은 `while` 루프를 이터레이터로 바꿔 준다. 센티널은 결과에 안 들어간다.
- **제너레이터 안에서 새어 나온 `StopIteration` 은 `RuntimeError`** 다(3.7+, PEP 479). 조용히 잘리던 것을 시끄럽게 만든 변화다.
- ★★ **소진된 것과 원래 빈 것은 바깥에서 구분되지 않는다** — `bool` 도 `next(x, 기본)` 도 `__length_hint__` 도 같은 답을 준다. **이터레이터는 언제나 참이다.**
- **검사하는 행위가 값을 먹는다.** 「남았나」를 물으면 남은 것이 줄어든다.

## 관련 자료

- 목록: [python/syntax 주제 목록](../README.md) — 이 주제는 **16번**
- 선행: [15-generator-expressions-lazy-eval](../15-generator-expressions-lazy-eval/2-summary.md) — 지연이 왜 값어치가 있나.\
  **경계**: 그쪽은 **메모리와 평가 시점**까지, 여기는 「**그 객체가 지켜야 하는 계약**」부터다.
- 선행: [09-sequence-ops-and-slicing](../09-sequence-ops-and-slicing/2-summary.md) — 시퀀스가 무엇인가. `__getitem__` 대체 경로가 왜 「시퀀스 프로토콜」인지.
- 정본 이웃: [17-generators-yield](../17-generators-yield/2-summary.md) — **제너레이터의 정본.**\
  **경계**: `yield`·프레임·상태 이름·`send`·`close`·`yield from` 은 전부 그쪽이다.
  여기는 **제너레이터가 아닌 것**(리스트·`map`·`__getitem__` 객체)까지 덮는 계약만 다룬다.
- 함께 보는 곳: [18-loop-control-and-else](../18-loop-control-and-else/2-summary.md) — `range` 가 이터레이터가 **아닌** 것, 순회 중 변경이 커서를 어긋내는 것.
- 함께 보는 곳: [14-comprehensions](../14-comprehensions/2-summary.md) — 컴프리헨션이 이 프로토콜 위에 얹혀 있다.
- 함께 보는 곳: [19-function-argument-rules](../19-function-argument-rules/2-summary.md) — `f(*it)` 로 풀 때 이터레이터가 소진되는 것.
- 이어지는 곳: [목록의 **32번 주제**](../32-container-protocol/) 「컨테이너 프로토콜」 — `__len__`·`__contains__` 까지 묶은 정본.
- 이어지는 곳: 목록의 **44번 주제** 「`itertools`」 — 이 프로토콜 위에 지어진 도구 모음.
- 이어지는 곳: 목록의 **51번 주제** 「`asyncio` 코루틴 기초」 — `__aiter__`/`__anext__` 의 비동기 판.
- 기존 노트: [`cs/foundations/python-basics/`](../../../../python-basics/) — `for` 로 순회하는 법까지가 그쪽이다.\
  **경계**: 여기는 **그 `for` 가 안쪽에서 무엇을 부르고 있었나**부터다.
- 공식 문서: [Iterator Types](https://docs.python.org/3.12/library/stdtypes.html#iterator-types) · [`iter()`](https://docs.python.org/3.12/library/functions.html#iter) · [PEP 479](https://peps.python.org/pep-0479/)

## 용어 풀이

- **이터러블(iterable)**: `iter()` 를 걸 수 있는 것. `__iter__` 가 있거나 **`__getitem__`(0부터)** 이 있으면 된다.
- **이터레이터(iterator)**: `__next__` 가 있고 `__iter__` 가 **자기 자신**을 돌려주는 것. 한 방향, 되감기 없음.
- **이터레이터 프로토콜(iterator protocol)**: 위 두 메서드로 된 계약. `for`·컴프리헨션·언패킹이 전부 이것 위에 있다.
- **`StopIteration`**: 「더 없다」는 신호 예외. `for` 가 잡아 조용히 빠져나간다.\
  ★ **한 번 내면 계속 내야 한다**는 것이 계약이다.
- **소진(exhaustion)**: 끝까지 꺼내 더 낼 것이 없어진 상태. **처음부터 빈 것과 구분되지 않는다.**
- **센티널(sentinel)**: 「여기가 끝」을 뜻하는 특별한 값. `iter(f, s)` 의 `s`, `next(it, s)` 의 `s`.\
  예: 결과에는 안 들어간다.
- **시퀀스 프로토콜 대체 경로(`__getitem__` fallback)**: `__iter__` 가 없을 때 0부터 `__getitem__` 을 부르는 옛 방식.\
  예: `IndexError` 가 나면 끝난 것으로 본다.
- **`__length_hint__`**: 남은 개수의 **추정치**. `operator.length_hint()` 로 부른다. **보장이 아니다.**
- **PEP 479**: 제너레이터 안에서 새어 나온 `StopIteration` 을 `RuntimeError` 로 바꾼 변경. **3.7 부터 무조건.**
- **`gi_frame`·`gi_running`·`gi_suspended`**: 제너레이터 안을 들여다보는 CPython 속성.\
  예: 소진되면 `gi_frame` 이 `None` 이 된다. **다른 이터레이터에는 이런 창이 없다.**
- **방어적 물질화(defensive materialization)**: 받은 것이 이터레이터면 `list()` 로 바꿔 두는 것.\
  예: `if iter(x) is x: x = list(x)`.

## 더 들어가면

- **`itertools.tee`** 는 「한 이터레이터를 둘로 나눠 두 번 돌기」처럼 보이지만 **내부 버퍼에 쌓는다** —
  한쪽이 멀리 앞서면 리스트를 만드는 것과 비용이 같아진다(목록의 **44번 주제**).
- **`collections.abc.Iterable`·`Iterator`** 로 `isinstance` 검사를 할 수 있지만,
  ★ **`Iterable` 검사는 `__getitem__` 만 있는 것을 놓친다**(`__iter__` 만 본다). 문서가 그 한계를 직접 적는다. [목록의 **35번 주제**](../35-abc-and-protocol/).
- **파일 객체가 자기 자신의 이터레이터다** — `iter(f) is f` 가 참이다. 그래서 파일을 두 번 `for` 로 돌면 두 번째가 빈다.
  `f.seek(0)` 이 되감기다(목록의 **48번 주제**).
- **언패킹도 이 프로토콜을 쓴다** — `a, b = it` 이 `next` 를 두 번 부르고 세 번째로 끝을 확인한다([11번](../11-tuple-and-unpacking/2-summary.md)).
- **비동기 판**은 `__aiter__`/`__anext__` 와 `StopAsyncIteration` 이다(PEP 492). 구조가 그대로 대응된다(목록의 **51번 주제**).
