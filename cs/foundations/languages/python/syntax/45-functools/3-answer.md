# python/syntax/45-functools — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> [1-question.md](1-question.md)의 번호와 **1:1**로 대응한다. 질문 11개 = 답 11개.
>
> 이 파일의 모든 출력은 `python3` **3.12.3** 과 `python3.11` **3.11.15**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> 던지는 형태는 `python3 - <파일` 로 고정했다. ★ **시간·메모리 바이트는 한 번도 재지 않았다.**

## 정답

### 1. 몸통 `21891` 대 `21` · 다시 부르면 `hits` 만 · `__wrapped__` 는 맨 위 한 번만 우회 · 키워드 순서·위치 대 키워드가 전부 다른 칸

**출력**

```python
# e45_lru_info.py
from functools import lru_cache

body = 0


def fib_plain(n):
    global body
    body += 1
    return n if n < 2 else fib_plain(n - 1) + fib_plain(n - 2)


fib_plain(20)
print("[1] 캐시 없이 fib(20) — 몸통 실행 수 :", body)

body = 0


@lru_cache(maxsize=None)
def fib(n):
    global body
    body += 1
    return n if n < 2 else fib(n - 1) + fib(n - 2)


fib(20)
print("[2] lru_cache 로 fib(20) — 몸통 실행 수 :", body)
print("    cache_info()                        :", fib.cache_info())
fib(20)
print("[3] 한 번 더 fib(20)                     :", fib.cache_info())

before = body
fib.__wrapped__(20)
print("[4] fib.__wrapped__(20) 뒤 몸통 실행 수 증가 :", body - before)
print("    cache_info()                        :", fib.cache_info())
print("    __name__ · __wrapped__ 가 있나        :", fib.__name__, hasattr(fib, "__wrapped__"))

fib.cache_clear()
print("[5] cache_clear() 뒤                    :", fib.cache_info())


@lru_cache
def pair(a, b):
    return a - b


pair(a=1, b=2)
pair(b=2, a=1)
pair(1, 2)
print("[6] pair(a=1, b=2) · pair(b=2, a=1) · pair(1, 2) :", pair.cache_info())
print("    cache_parameters()                  :", pair.cache_parameters())
```

```text
===== python3 - <e45_lru_info.py =====
[1] 캐시 없이 fib(20) — 몸통 실행 수 : 21891
[2] lru_cache 로 fib(20) — 몸통 실행 수 : 21
    cache_info()                        : CacheInfo(hits=18, misses=21, maxsize=None, currsize=21)
[3] 한 번 더 fib(20)                     : CacheInfo(hits=19, misses=21, maxsize=None, currsize=21)
[4] fib.__wrapped__(20) 뒤 몸통 실행 수 증가 : 1
    cache_info()                        : CacheInfo(hits=21, misses=21, maxsize=None, currsize=21)
    __name__ · __wrapped__ 가 있나        : fib True
[5] cache_clear() 뒤                    : CacheInfo(hits=0, misses=0, maxsize=None, currsize=0)
[6] pair(a=1, b=2) · pair(b=2, a=1) · pair(1, 2) : CacheInfo(hits=0, misses=3, maxsize=128, currsize=3)
    cache_parameters()                  : {'maxsize': 128, 'typed': False}
(exit 0)
```

**왜 그런가**

* ★★ 캐시를 달면 **서로 다른 `n` 마다 한 번**(0 부터 20 까지 21개)만 몸통이 돈다 — `misses=21` 과 같다. 둘째 가지(`fib(n - 2)`)는 이미 적힌 것을 읽는다(`hits=18`).
* ★★ `fib.__wrapped__(20)` 은 **맨 위 호출만** 원본이다 — 그 안에서 부른 `fib(19)`·`fib(18)` 은 전역 이름 `fib`, 즉 **캐시 쪽**으로 가서 `hits` 가 2 늘었다. 몸통 실행은 **1**.
* ★ `pair(a=1, b=2)`·`pair(b=2, a=1)`·`pair(1, 2)` 가 **칸 셋**(`misses=3`). 문서가 키워드 순서를 적어 두었고, 위치 대 키워드도 **다른 키**가 된다.

### 2. `True` → `cache_clear()` 뒤 `False` · 메서드도 `True` → 다른 인스턴스 둘이 밀어내면 `False` · `cached_property` 는 `False` · 반환값도 `True`

**출력**

```python
# e45_hold.py
import gc
import weakref
from functools import cached_property, lru_cache


class Thing:
    pass


def alive(ref):
    gc.collect()
    return ref() is not None


print("[1] 인자로 넘긴 객체")


@lru_cache(maxsize=None)
def look(obj):
    return 1


t = Thing()
r = weakref.ref(t)
look(t)
del t
print("    del 뒤 살아 있나            :", alive(r))
look.cache_clear()
print("    cache_clear() 뒤 살아 있나  :", alive(r))

print("[2] 메서드에 @lru_cache — self")


class Station:
    @lru_cache(maxsize=2)
    def rain(self, day):
        return day * 10


s = Station()
r = weakref.ref(s)
s.rain(1)
del s
print("    del 뒤 살아 있나            :", alive(r))
print("    Station.rain.cache_info()   :", Station.rain.cache_info())
others = [Station() for _ in range(2)]
for o in others:
    o.rain(1)
print("    다른 인스턴스 둘이 부른 뒤  :", alive(r))
print("    Station.rain.cache_info()   :", Station.rain.cache_info())

print("[3] cached_property — self")


class Report:
    @cached_property
    def total(self):
        return 99


p = Report()
r = weakref.ref(p)
p.total
del p
print("    del 뒤 살아 있나            :", alive(r))

print("[4] 돌려준 값")


@lru_cache(maxsize=None)
def make(n):
    return Thing()


v = make(1)
r = weakref.ref(v)
del v
print("    del 뒤 살아 있나            :", alive(r))
print("    make(1) is r()              :", make(1) is r())
```

```text
===== python3 - <e45_hold.py =====
[1] 인자로 넘긴 객체
    del 뒤 살아 있나            : True
    cache_clear() 뒤 살아 있나  : False
[2] 메서드에 @lru_cache — self
    del 뒤 살아 있나            : True
    Station.rain.cache_info()   : CacheInfo(hits=0, misses=1, maxsize=2, currsize=1)
    다른 인스턴스 둘이 부른 뒤  : False
    Station.rain.cache_info()   : CacheInfo(hits=0, misses=3, maxsize=2, currsize=2)
[3] cached_property — self
    del 뒤 살아 있나            : False
[4] 돌려준 값
    del 뒤 살아 있나            : True
    make(1) is r()              : True
(exit 0)
```

**왜 그런가**

* ★★★ 캐시 칸의 **키가 인자 객체를 붙든다.** 메서드면 **`self` 도 인자**라 키에 들어간다 — `del s` 뒤에도 살아 있다.
* ★★★ **수명은 `maxsize` 가 정한다.** `maxsize=2` 에 다른 인스턴스 둘이 부르자 `s` 의 칸이 **LRU 로 밀려나** `False`. `maxsize=None` 이면 밀려남이 없어 **`cache_clear()` 까지**다(`[1]`).
* ★★ `Station.rain.cache_info()` 가 **세 인스턴스의 호출을 한 곳에** 센다(`misses=3`) — 캐시는 **클래스에 하나**다.
* ★★ `cached_property` 는 값을 **인스턴스 자신의 `__dict__`** 에 두니 인스턴스를 안 붙든다 — FAQ 의 *"It does not create a reference to the instance."*
* ★ 반환값도 붙든다 — 다시 부르면 **같은 객체**다(`is` `True`).

### 3. `typed=False` — `f(1) ; f(1.0)` 칸 2 · `f(1.0) ; f(True)` 칸 1 · 둘 이상·키워드는 칸 1 — `6 / 8` / `typed=True` 는 안쪽만 칸 1 — `2 / 8`

**출력**

```python
# e45_lru_keys.py
from decimal import Decimal
from fractions import Fraction
from functools import lru_cache

# 한 행 = 두 호출. 두 호출이 같은 == 인 인자를 받는다.
ROWS = [
    ("f(1) ; f(1.0)", ((1,), {}), ((1.0,), {})),
    ("f(1) ; f(True)", ((1,), {}), ((True,), {})),
    ("f(1.0) ; f(True)", ((1.0,), {}), ((True,), {})),
    ("f('a') ; f('a')", (("a",), {}), (("a",), {})),
    ("f(1, 0) ; f(1.0, 0)", ((1, 0), {}), ((1.0, 0), {})),
    ("f(x=1) ; f(x=1.0)", ((), {"x": 1}), ((), {"x": 1.0})),
    ("f(D(42)) ; f(F(42))", ((Decimal(42),), {}), ((Fraction(42),), {})),
    ("f(('k', D(42))) ; f(('k', F(42)))", ((("k", Decimal(42)),), {}), ((("k", Fraction(42)),), {})),
]


def entries(typed, first, second):
    @lru_cache(typed=typed)
    def f(*args, **kwargs):
        return None

    f(*first[0], **first[1])
    f(*second[0], **second[1])
    return f.cache_info().currsize


print("%-34s\t%s\t%s" % ("두 호출", "typed=False", "typed=True"))
one = {False: 0, True: 0}
for label, first, second in ROWS:
    cells = []
    for typed in (False, True):
        n = entries(typed, first, second)
        one[typed] += n == 1
        cells.append("칸 %d" % n)
    print("%-34s\t%s\t%s" % (label, cells[0], cells[1]))
print("한 칸이 된 행 : typed=False %d / %d · typed=True %d / %d"
      % (one[False], len(ROWS), one[True], len(ROWS)))

print()
print("[구현] 순수 파이썬 판 functools._make_key 가 만드는 키")
import functools
for args in ((1,), (1.0,), (True,), ("a",), (1, 0)):
    key = functools._make_key(args, {}, False)
    print("   %-10r -> %-12r %s" % (args, key, type(key).__name__))
print("   lru_cache 가 돌려준 객체의 타입 :", type(lru_cache(lambda: 0)).__qualname__)
import _functools
print("   그 타입이 C 모듈 _functools 의 것인가 :", functools._lru_cache_wrapper is _functools._lru_cache_wrapper)
```

```text
===== python3 - <e45_lru_keys.py =====
두 호출                              	typed=False	typed=True
f(1) ; f(1.0)                     	칸 2	칸 2
f(1) ; f(True)                    	칸 2	칸 2
f(1.0) ; f(True)                  	칸 1	칸 2
f('a') ; f('a')                   	칸 1	칸 1
f(1, 0) ; f(1.0, 0)               	칸 1	칸 2
f(x=1) ; f(x=1.0)                 	칸 1	칸 2
f(D(42)) ; f(F(42))               	칸 1	칸 2
f(('k', D(42))) ; f(('k', F(42))) 	칸 1	칸 1
한 칸이 된 행 : typed=False 6 / 8 · typed=True 2 / 8

[구현] 순수 파이썬 판 functools._make_key 가 만드는 키
   (1,)       -> 1            int
   (1.0,)     -> [1.0]        _HashedSeq
   (True,)    -> [True]       _HashedSeq
   ('a',)     -> 'a'          str
   (1, 0)     -> [1, 0]       _HashedSeq
   lru_cache 가 돌려준 객체의 타입 : _lru_cache_wrapper
   그 타입이 C 모듈 _functools 의 것인가 : True
(exit 0)
```

**왜 그런가**

* ★★★ CPython 의 키 함수는 **인자가 `int`·`str` 하나(키워드 없음)면 그 값 자체**를 키로 쓴다(`1` · `'a'`). 그 밖은 **`_HashedSeq`**(인자를 담은 리스트 모양)로 싼다.
  **`1` 과 `[1.0]` 은 `==` 가 거짓** — 그래서 `f(1)`·`f(1.0)` 이 칸 2 다. `f(1)`·`f(True)` 도 같은 이유로 칸 2(`True` 의 타입은 `bool` 이지 `int` 그 자체가 아니라 지름길을 안 탄다).
* ★★ `f(1.0) ; f(True)` 는 둘 다 `_HashedSeq` — `[1.0] == [True]` 이고 해시도 같으니 **칸 1**. 둘 이상의 인자·키워드 인자도 전부 싸이니 **사전 규칙대로** 합쳐진다.
* ★★ `typed=True` 는 **바로 받은 인자**의 타입만 본다 — 튜플 **안쪽**의 `Decimal`/`Fraction` 은 안 본다(칸 1). 문서의 *"immediate arguments rather than their contents"*.
* ★ 문서는 이것을 **보장하지 않고 허용만** 한다 — *"(Some types such as str and int may be cached separately even when typed is false.)"*

### 4. 리스트는 `TypeError: unhashable type: 'list'`(튜플 안에 있어도) · 고친 리스트가 다음 호출로 · 제너레이터 둘째는 `[]`

**출력**

```python
# e45_mutable.py
from functools import lru_cache


@lru_cache
def total(xs):
    return sum(xs)


def attempt(label, fn):
    try:
        print("   %-32s -> %r" % (label, fn()))
    except TypeError as ex:
        print("   %-32s -> %s: %s" % (label, type(ex).__name__, ex))


print("[1] 인자")
attempt("total((1, 2, 3))", lambda: total((1, 2, 3)))
attempt("total([1, 2, 3])", lambda: total([1, 2, 3]))
attempt("total(((1, 2), [3]))", lambda: total(((1, 2), [3])))
attempt("total(frozenset({1, 2}))", lambda: total(frozenset({1, 2})))
print("   cache_info() :", total.cache_info())

print("[2] 돌려준 리스트를 고치면")


@lru_cache
def names(n):
    return ["n%d" % i for i in range(n)]


a = names(2)
a.append("extra")
b = names(2)
print("   첫 호출이 받은 것에 append 한 뒤 두 번째 호출 :", b)
print("   a is b :", a is b)

print("[3] 제너레이터를 돌려주는 함수")


@lru_cache
def evens(n):
    return (i for i in range(0, n, 2))


print("   list(evens(7)) 첫째 :", list(evens(7)))
print("   list(evens(7)) 둘째 :", list(evens(7)))
print("   cache_info()        :", evens.cache_info())
```

```text
===== python3 - <e45_mutable.py =====
[1] 인자
   total((1, 2, 3))                 -> 6
   total([1, 2, 3])                 -> TypeError: unhashable type: 'list'
   total(((1, 2), [3]))             -> TypeError: unhashable type: 'list'
   total(frozenset({1, 2}))         -> 3
   cache_info() : CacheInfo(hits=0, misses=2, maxsize=128, currsize=2)
[2] 돌려준 리스트를 고치면
   첫 호출이 받은 것에 append 한 뒤 두 번째 호출 : ['n0', 'n1', 'extra']
   a is b : True
[3] 제너레이터를 돌려주는 함수
   list(evens(7)) 첫째 : [0, 2, 4, 6]
   list(evens(7)) 둘째 : []
   cache_info()        : CacheInfo(hits=1, misses=1, maxsize=128, currsize=1)
(exit 0)
```

**왜 그런가**

* ★★ 캐시 키는 사전 키다 — **해시가 안 되면 키를 못 만든다.** 튜플은 해시될 때 **원소를 해시**하므로 안에 리스트가 있으면 같은 `TypeError` 다([30번](../30-repr-eq-hash-contracts/2-summary.md)). 실패한 호출은 `hits`·`misses` 어디에도 안 들어간다.
* ★★★ 캐시는 **답을 복사하지 않는다** — `a is b` 가 `True`. 받은 쪽의 `append` 가 **메모장의 답**을 고쳤다.
* ★★ 제너레이터도 **같은 객체**를 다시 준다 — 첫 `list` 가 소진했으니 둘째는 `[]`(`hits=1`).

### 5. `KRW 2050` · `KRW 2000`(이번만) · 겹치면 한 겹으로 · `__name__` 없음 · `partial` 은 `2000`, `lambda` 는 `3000`

**출력**

```python
# e45_partial.py
import inspect
from functools import partial


def price(base, rate, *, fee=0, currency="KRW"):
    return "%s %d" % (currency, base * rate + fee)


p = partial(price, 1000, fee=50)
print("[1] p.func · p.args · p.keywords :", p.func.__name__, p.args, p.keywords)
print("    p(2)                         :", p(2))
print("    p(2, fee=0)                  :", p(2, fee=0))
print("    p.keywords 는 그대로인가       :", p.keywords)
print("    inspect.signature(p)         :", inspect.signature(p))

q = partial(p, currency="USD")
print("[2] partial(p, currency='USD')")
print("    q.func is price              :", q.func is price)
print("    q.args · q.keywords          :", q.args, q.keywords)
print("    q(3)                         :", q(3))

print("[3] partial 객체의 정체")
print("    hasattr(p, '__name__')       :", hasattr(p, "__name__"))
print("    type(p).__name__             :", type(p).__name__)
try:
    p()
except TypeError as ex:
    print("    p() -> TypeError:", ex)

print("[4] 만들 때 값을 잡나, 부를 때 찾나")
rate = 2
by_partial = partial(price, 1000, rate)
by_lambda = lambda: price(1000, rate)
rate = 3
print("    partial :", by_partial())
print("    lambda  :", by_lambda())
```

```text
===== python3 - <e45_partial.py =====
[1] p.func · p.args · p.keywords : price (1000,) {'fee': 50}
    p(2)                         : KRW 2050
    p(2, fee=0)                  : KRW 2000
    p.keywords 는 그대로인가       : {'fee': 50}
    inspect.signature(p)         : (rate, *, fee=50, currency='KRW')
[2] partial(p, currency='USD')
    q.func is price              : True
    q.args · q.keywords          : (1000,) {'fee': 50, 'currency': 'USD'}
    q(3)                         : USD 3050
[3] partial 객체의 정체
    hasattr(p, '__name__')       : False
    type(p).__name__             : partial
    p() -> TypeError: price() missing 1 required positional argument: 'rate'
[4] 만들 때 값을 잡나, 부를 때 찾나
    partial : KRW 2000
    lambda  : KRW 3000
(exit 0)
```

**왜 그런가**

* ★ 부를 때 준 키워드는 `{**keywords, **새 키워드}` 로 **이번 호출에서만** 이긴다 — `p.keywords` 는 읽기 전용이고 그대로다.
* ★ `partial(p, …)` 의 `func` 가 `price` — CPython 이 안쪽 `partial` 을 **펴서** 한 겹으로 만든다(구현).
* ★★ `partial` 은 **함수가 아니라 `partial` 타입의 객체**다. 문서 — *"the `__name__` and `__doc__` attributes are not created automatically."* 모자란 인자는 **원래 함수의 메시지**(`price() missing …`)로 나온다.
* ★★ `partial(price, 1000, rate)` 는 **그 순간의 `rate` 값(2)** 을 `args` 에 넣었다. `lambda` 는 부를 때 이름 `rate` 를 찾아 **3** 을 본다 — [22번](../22-closures-and-late-binding/2-summary.md)의 늦은 바인딩.

### 6. `True` 는 `for_int` · `Meters` 는 `for_float_or_str` · `list`·`tuple` 은 `for_sequence` · `dict`·`None` 은 `show` · `pair(1, 2)` 는 `int 칸` · `list[int]` 는 `TypeError`

**출력**

```python
# e45_dispatch.py
from collections.abc import Sequence
from functools import singledispatch


@singledispatch
def show(x):
    return "object"


@show.register
def for_int(x: int):
    return "int"


@show.register
def for_float_or_str(x: float | str):
    return "float|str"


@show.register(Sequence)
def for_sequence(x):
    return "Sequence"


class Meters(float):
    pass


print("[1] registry 의 키 (이름순)")
for cls in sorted(show.registry, key=lambda c: c.__name__):
    print("   ", cls.__name__, "->", show.registry[cls].__name__)

print("[2] 무엇이 불리나")
for arg in (7, True, 2.5, Meters(3), "s", [1], (1,), {1: 2}, None):
    print("    show(%-9r) -> %-9s  dispatch(%s) -> %s"
          % (arg, show(arg), type(arg).__name__, show.dispatch(type(arg)).__name__))
print("    type(show.registry).__name__ :", type(show.registry).__name__)

print("[3] 인자 둘 — 무엇으로 고르나")


@singledispatch
def pair(a, b):
    return "기본"


@pair.register
def _(a: int, b: str):
    return "int 칸"


print("    pair(1, 2)       ->", pair(1, 2))
print("    pair('x', 'y')   ->", pair("x", "y"))

print("[4] 등록할 수 없는 어노테이션")
try:
    @show.register
    def _(x: list[int]):
        return "list[int]"
except TypeError as ex:
    print("    TypeError:", ex)
```

```text
===== python3 - <e45_dispatch.py =====
[1] registry 의 키 (이름순)
    Sequence -> for_sequence
    float -> for_float_or_str
    int -> for_int
    object -> show
    str -> for_float_or_str
[2] 무엇이 불리나
    show(7        ) -> int        dispatch(int) -> for_int
    show(True     ) -> int        dispatch(bool) -> for_int
    show(2.5      ) -> float|str  dispatch(float) -> for_float_or_str
    show(3.0      ) -> float|str  dispatch(Meters) -> for_float_or_str
    show('s'      ) -> float|str  dispatch(str) -> for_float_or_str
    show([1]      ) -> Sequence   dispatch(list) -> for_sequence
    show((1,)     ) -> Sequence   dispatch(tuple) -> for_sequence
    show({1: 2}   ) -> object     dispatch(dict) -> show
    show(None     ) -> object     dispatch(NoneType) -> show
    type(show.registry).__name__ : mappingproxy
[3] 인자 둘 — 무엇으로 고르나
    pair(1, 2)       -> int 칸
    pair('x', 'y')   -> 기본
[4] 등록할 수 없는 어노테이션
    TypeError: Invalid annotation for 'x'. list[int] is not a class.
(exit 0)
```

**왜 그런가**

* ★★ 등록 안 된 타입은 **MRO 를 따라** 가장 가까운 등록 타입으로 간다 — `bool → int`, `Meters → float`, `dict → object`.
* ★★ `str` 은 `Sequence` 이기도 하지만 **`str` 자체가 등록돼 있어** 그쪽이 이긴다. `int | str` 이 아니라 `float | str` 로 등록했으니 `registry` 에 `float`·`str` **두 칸**이 생겼다.
* ★★★ **첫 인자만 본다** — `pair(1, 2)` 의 둘째 `2` 는 `str` 이 아닌데도 `int 칸`. 둘째 인자의 어노테이션은 **조용히 무시**된다.
* ★ `list[int]` 는 클래스가 아니라 **제네릭 별칭**이라 `registry` 의 키가 될 수 없다.

### 7. 인스턴스 `__dict__` 에 같은 이름의 값이 생겨 비데이터 디스크립터를 이긴다 · 원본을 고쳐도 옛 값 · `del o.total` · `__slots__` 면 적을 칸이 없어 `TypeError`

**출력**

```python
# e45_cached.py
from functools import cached_property

runs = []


class Order:
    def __init__(self, items):
        self.items = items

    @cached_property
    def total(self):
        runs.append("total")
        return sum(self.items)

    @property
    def count(self):
        return len(self.items)


o = Order([1, 2, 3])
print("[1] 두 번 읽기           :", o.total, o.total, "· 몸통 실행", len(runs))
print("    vars(o)              :", vars(o))
o.items.append(4)
print("[2] items 를 고친 뒤     :", o.total, "· 몸통 실행", len(runs))
del o.total
print("[3] del o.total 뒤       :", o.total, "· 몸통 실행", len(runs))
o.total = 0
print("[4] o.total = 0 뒤       :", o.total, "· 몸통 실행", len(runs))
try:
    o.count = 0
except AttributeError as ex:
    print("[5] o.count = 0 (property) -> AttributeError:", ex)
print("[6] Order.total 의 타입  :", type(Order.total).__name__, "· attrname:", Order.total.attrname)
```

```text
===== python3 - <e45_cached.py =====
[1] 두 번 읽기           : 6 6 · 몸통 실행 1
    vars(o)              : {'items': [1, 2, 3], 'total': 6}
[2] items 를 고친 뒤     : 6 · 몸통 실행 1
[3] del o.total 뒤       : 10 · 몸통 실행 2
[4] o.total = 0 뒤       : 0 · 몸통 실행 2
[5] o.count = 0 (property) -> AttributeError: property 'count' of 'Order' object has no setter
[6] Order.total 의 타입  : cached_property · attrname: total
(exit 0)
```

**왜 그런가**

* ★★★ `cached_property` 는 `__get__` 만 가진 **비데이터 디스크립터**다([33번](../33-property-descriptor-slots/2-summary.md)). 첫 읽기에서 몸통을 돌려 **`o.__dict__['total']`** 에 적는다.
  둘째 읽기부터는 **인스턴스 칸이 비데이터 디스크립터를 이기므로**([29번](../29-classes-and-attribute-lookup/2-summary.md)의 네 층) 디스크립터가 **불리지도 않는다** — 몸통 실행 1.
* ★★ 그래서 `items` 를 고쳐도 **옛 값 `6`** — 다시 볼 기회가 없다. **`del o.total`** 로 칸을 지우면 다음 읽기에서 다시 돈다(`10`).
* ★ **`__slots__` 클래스**에는 적을 `__dict__` 가 없어 `TypeError: No '__dict__' attribute on 'Slotted' instance to cache 'value' property.`([33번](../33-property-descriptor-slots/2-summary.md) 「더 들어가면」 ②).

### 8. `TypeError`(0번) · `100`(0번) · `7`(0번) — `None` 은 「안 준 것」이 아니다

**출력**

```python
# e45_reduce.py
from functools import reduce
from itertools import accumulate

calls = []


def add(acc, x):
    calls.append((acc, x))
    return acc + x


def run(label, *args):
    calls.clear()
    try:
        out = repr(reduce(add, *args))
    except TypeError as ex:
        out = "TypeError: %s" % ex
    print("   %-28s -> %-28s 호출 %d" % (label, out, len(calls)))


print("[1] 원소 개수와 초깃값")
run("reduce(add, [1, 2, 3])", [1, 2, 3])
run("reduce(add, [1, 2, 3], 100)", [1, 2, 3], 100)
run("reduce(add, [7])", [7])
run("reduce(add, [7], 100)", [7], 100)
run("reduce(add, [])", [])
run("reduce(add, [], 100)", [], 100)
run("reduce(add, [], None)", [], None)
run("reduce(add, [1, 2], None)", [1, 2], None)

print("[2] accumulate 와 나란히")
print("   list(accumulate([1, 2, 3], add)) :", list(accumulate([1, 2, 3], add)))
print("   list(accumulate([1, 2, 3], add, initial=100)) :",
      list(accumulate([1, 2, 3], add, initial=100)))
print("   마지막 값이 reduce 와 같은가 :",
      list(accumulate([1, 2, 3], add))[-1] == reduce(add, [1, 2, 3]))
```

```text
===== python3 - <e45_reduce.py =====
[1] 원소 개수와 초깃값
   reduce(add, [1, 2, 3])       -> 6                            호출 2
   reduce(add, [1, 2, 3], 100)  -> 106                          호출 3
   reduce(add, [7])             -> 7                            호출 0
   reduce(add, [7], 100)        -> 107                          호출 1
   reduce(add, [])              -> TypeError: reduce() of empty iterable with no initial value 호출 0
   reduce(add, [], 100)         -> 100                          호출 0
   reduce(add, [], None)        -> None                         호출 0
   reduce(add, [1, 2], None)    -> TypeError: unsupported operand type(s) for +: 'NoneType' and 'int' 호출 1
[2] accumulate 와 나란히
   list(accumulate([1, 2, 3], add)) : [1, 3, 6]
   list(accumulate([1, 2, 3], add, initial=100)) : [100, 101, 103, 106]
   마지막 값이 reduce 와 같은가 : True
(exit 0)
```

**왜 그런가**

* ★★ 빈 입력 + 초깃값 없음은 **접을 첫 값이 없어** `TypeError: reduce() of empty iterable with no initial value`. 초깃값이 있으면 그것을 그대로 돌려주고 함수는 **0 번**.
* ★ 한 원소면 **그 원소**(함수 0 번) — 문서의 *"the first item is returned"*.
* ★★ **`None` 도 초깃값이다** — `reduce(add, [1, 2], None)` 은 `add(None, 1)` 을 불러 `TypeError`(호출 1). 문서의 「대략 같은 코드」는 `initializer=None` 을 표시로 써서 **이 둘을 못 가르지만**, 실제 판은 가른다.

### 9. 잠금(`lock`)을 잃었다 — 같은 인스턴스에서 몸통이 여러 번 돌 수 있다 · 3.11 `RuntimeError`(원인 `TypeError`) / 3.12 `TypeError` + `__notes__` — `except RuntimeError` 는 못 잡는다

**출력**

```python
# e45_version.py
import functools
import sys

print("판                                   :", "%d.%d" % sys.version_info[:2])
cp = functools.cached_property(lambda self: 1)
print("cached_property 객체에 lock 속성이 있나 :", hasattr(cp, "lock"))
print("functools.cache 가 있나              :", hasattr(functools, "cache"))


@functools.singledispatch
def f(x):
    return "object"


try:
    @f.register
    def for_union(x: int | str):
        return "int|str"
    print("register 가 int | str 을 받나        :", f(1), f("a"))
except TypeError as ex:
    print("register 가 int | str 을 받나        : TypeError:", ex)
```

```text
===== python3 - <e45_version.py =====
판                                   : 3.12
cached_property 객체에 lock 속성이 있나 : False
functools.cache 가 있나              : True
register 가 int | str 을 받나        : int|str int|str
(exit 0)
```

```text
===== python3.11 - <e45_version_py311.py =====
판                                   : 3.11
cached_property 객체에 lock 속성이 있나 : True
functools.cache 가 있나              : True
register 가 int | str 을 받나        : int|str int|str
(exit 0)
```

```python
# e45_setname.py
from functools import cached_property

print("한 cached_property 객체를 두 이름에")
shared = cached_property(lambda self: 1)
try:
    class Twice:
        a = shared
        b = shared
except (TypeError, RuntimeError) as ex:
    print("    %s: %s" % (type(ex).__name__, ex))
    print("    __cause__ :", type(ex.__cause__).__name__ if ex.__cause__ else None)
    print("    __notes__ :", getattr(ex, "__notes__", None))
```

```text
===== python3 - <e45_setname.py =====
한 cached_property 객체를 두 이름에
    TypeError: Cannot assign the same cached_property to two different names ('a' and 'b').
    __cause__ : None
    __notes__ : ["Error calling __set_name__ on 'cached_property' instance 'b' in 'Twice'"]
(exit 0)
```

```text
===== python3.11 - <e45_setname_py311.py =====
한 cached_property 객체를 두 이름에
    RuntimeError: Error calling __set_name__ on 'cached_property' instance 'b' in 'Twice'
    __cause__ : TypeError
    __notes__ : None
(exit 0)
```

(`e45_version_py311.py`·`e45_setname_py311.py` 는 각각 `e45_version.py`·`e45_setname.py` 와 **한 글자도 같다.**)

**왜 그런가**

* ★★ 3.12 가 **문서화되지 않았던 잠금**을 뺐다 — 문서: 잠금이 *"per-property, not per-instance"* 라 경합이 컸다. 그 결과 *"The getter function could run more than once on the same instance, with the latest run setting the cached value."* ★ **경쟁은 재지 않았다** — 속성의 있고 없음(`True`/`False`)만 봤다.
* ★★ `__set_name__` 이 던진 예외를 3.11 은 **`RuntimeError` 로 쌌고**(`__cause__` 가 `TypeError`), 3.12 는 **안 싸고** 같은 문장을 **노트**로 붙인다(What's New 3.12). 그래서 **`except RuntimeError` 는 3.12 에서 그 예외를 놓친다.**
* ★ 유니온 등록과 `functools.cache` 는 **두 판 다** 된다.

### 10. 보장 · 구현 · 구현 · 보장 — 「약한 참조가 아직 가리키나」(참/거짓)로 보였다 · 바이트는 안 쟀다

**왜 그런가**

| 사실 | 층 | 근거 |
|---|---|---|
| 캐시는 **인자와 반환값을 참조**한다 | **라이브러리 보장** | `lru_cache` 절 · FAQ |
| `int` 인자 하나는 **그 값 자체가 키** | **CPython 구현** | `functools._make_key` 실행 — 문서는 「따로 캐시될 수 있다」까지만 |
| 겹친 `partial` 을 **한 겹으로 편다** | **CPython 구현** | `q.func is price` — 보장 문장을 못 찾았다 |
| `partial` 에는 **`__name__` 이 없다** | **라이브러리 보장** | `partial` 객체 절 |

* ★★★ 「캐시가 메모리를 쓴다」를 **바이트가 아니라 회수 여부**로 보였다 — `weakref.ref` + `gc.collect()` 뒤 **`True`(살아 있다)/`False`(회수됐다)**.
  **몇 바이트인지·얼마나 빨라지는지는 재지 않았다.** 이 문서가 말하는 것은 「**붙들고 있다 / 놓았다**」 둘뿐이다.

### 11. 12번은 `hash` 와 `==` 로 칸을 가르고, 캐시는 **키를 먼저 만든다** — `1` 과 `[1.0]` 은 다른 키 / 몸통 **1 번** — 안쪽 호출은 캐시로 갔으니 완전한 우회가 아니다

**왜 그런가**

* ★★★ [12번](../12-dict-and-key-requirements/2-summary.md)의 사전은 **넣은 값 그대로**를 키로 쓴다 — `1`·`1.0`·`True` 는 해시가 같고 `==` 라 한 칸.
  캐시는 **인자를 키로 바꾸는 단계가 하나 더** 있다. `int` 하나면 `1`, `float` 하나면 `[1.0]`(`_HashedSeq`) — **모양이 다른 두 키**라 `==` 가 거짓이고 칸 2 다.
  **사전 규칙은 그대로 지켜졌다** — 다른 것은 **키로 무엇을 넣었나**다.
* ★★ [24번](../24-decorators/2-summary.md)의 `__wrapped__` 는 **원본 함수**를 준다. 1번 `[4]` 에서 몸통은 **1 번** 돌았지만, 그 몸통이 부른 `fib(n - 1)`·`fib(n - 2)` 는 **캐시된 전역 `fib`** 였다(`hits` +2).
  재귀 함수에서 `__wrapped__` 는 **맨 위 한 번만** 우회한다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 계수 | `python3 - <e45_lru_info.py` | 3(캡처 + 재대조 + `PYTHONHASHSEED` 바꾼 재캡처) | **21891 대 21** · `misses=3` |
| 붙드는 것 | `python3 - <e45_hold.py` | 3 | `True` → `False` 네 줄 |
| `typed` 격자 | `python3 - <e45_lru_keys.py` | 3 | **6 / 8 · 2 / 8** |
| 가변 | `python3 - <e45_mutable.py` | 3 | `TypeError` · `extra` · `[]` |
| `partial` | `python3 - <e45_partial.py` | 3 | `2000` 대 `3000` |
| `reduce` | `python3 - <e45_reduce.py` | 3 | `TypeError` · `None` |
| `singledispatch` | `python3 - <e45_dispatch.py` | 3 | `int 칸` |
| `cached_property` | `python3 - <e45_cached.py` | 3 | 몸통 1 → `del` 뒤 2 |
| `__set_name__` | `python3 - <e45_setname.py` · `python3.11 - <e45_setname_py311.py` | 3씩 | 3.12 `TypeError` · 3.11 `RuntimeError` |
| `cmp_to_key` | `python3 - <e45_cmp.py` | 3 | `KeyWrapper` 해시 불가 |
| 판 격자 | `python3 - <e45_version.py` · `python3.11 - <e45_version_py311.py` | 3씩 | `lock` `False` / `True` |

**구현 의존 항목** — 판이 오르면 다시 돌려야 하는 것.

| 항목 | 왜 |
|---|---|
| ★★ `typed` 격자 | 키를 만드는 방식은 CPython 의 것이다 — 문서는 허용만 한다 |
| ★ 판 격자 | `cached_property`·`__set_name__` 이 3.12 에서 바뀌었다 |
| 예외 **문구** | 구현이다 |

★ **안 흔들리는 칸** — 몸통 실행 수 · `CacheInfo(...)` · `True`/`False` · **「6 / 8」·「2 / 8」** · 불린 구현 이름 · `(exit N)`.
★★ **이 주제가 한 번도 안 잰 것** — **시간·메모리 바이트·스레드 경쟁**(부적용).
