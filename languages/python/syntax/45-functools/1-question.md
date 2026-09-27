# python/syntax/45-functools — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> ★★★ 2번은 **줄마다 `True`/`False`** 와 `cache_info()` 의 네 수까지 적어야 맞은 것이다.
> ★★ 이 주제는 **속도·메모리 바이트를 묻지 않는다** — 한 번도 재지 않았다. 묻는 것은 **몸통 실행 수·적중 수·회수 여부**다.
>
> 실행 환경: `python3` **3.12.3** · Linux(9번은 `python3.11` 3.11.15 도 함께). 던지는 형태는 `python3 - <파일` 로 고정했다.
> ★ 선행 — [24](../24-decorators/1-question.md)(데코레이터·`wraps`) · [30](../30-repr-eq-hash-contracts/1-question.md)(해시 계약) · [12](../12-dict-and-key-requirements/1-question.md)(사전 키) · [33](../33-property-descriptor-slots/1-question.md)(디스크립터).

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ 캐시 없이 · 캐시로 · 우회해서 · 키워드 순서를 바꿔서 (예측)

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

### 2. ★★★ 캐시에 넘긴 객체를 지운 뒤 (예측)

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

### 3. ★★ 두 호출이 몇 칸이 되나 — `typed` 두 판 (예측)

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

### 4. ★★ 리스트 인자 · 돌려준 리스트 · 돌려준 제너레이터 (예측)

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

### 5. ★ 미리 채운 주문서 (예측)

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

### 6. ★★ 창구를 고르는 안내 데스크 (예측)

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

### 7. ★★ `cached_property` 는 두 번째 읽기부터 몸통을 안 부른다 (왜)

* 그 이유를 **비데이터 디스크립터**와 **인스턴스 `__dict__`** 두 낱말로 설명하라.
* 원본(`self.items`)을 고친 뒤 다시 읽으면 무엇이 나오나 — 그리고 캐시를 지우는 한 줄은?
* 같은 이유로 **`__slots__` 클래스**에서는 무엇이 일어나나?

### 8. ★ `reduce` 의 가장자리 (경계)

* `reduce(add, [])` · `reduce(add, [], 100)` · `reduce(add, [7])` 는 각각 무엇을 내고 `add` 를 몇 번 부르나?
* 초깃값으로 `None` 을 주는 것은 「안 준 것」과 같은가?

### 9. ★ 3.11 과 3.12 사이 (경계)

* `cached_property` 가 3.12 에서 잃은 것은 무엇이고, 그 결과 멀티스레드에서 무엇이 가능해졌나?
* 한 `cached_property` 객체를 두 이름에 붙이면 두 판이 **어떤 예외 타입**으로 알리나 — `except RuntimeError` 로 잡던 코드는 3.12 에서 어떻게 되나?

### 10. 층 가르기 (경계)

* 「캐시는 인자와 반환값을 참조한다」·「`int` 인자 하나는 그 값 자체가 키」·「`partial` 을 겹치면 한 겹으로 편다」·「`partial` 에는 `__name__` 이 없다」 —
  각각 **라이브러리 보장 · CPython 구현** 중 어디인가?
* ★ 이 문서가 「캐시가 메모리에 주는 영향」을 **무엇으로** 보였나 — 무엇은 재지 않았나?

### 11. 이웃 주제와의 경계 (연결)

* ★ [12번](../12-dict-and-key-requirements/2-summary.md)의 「`1`·`1.0`·`True` 는 한 칸」과 3번의 결과는 **어디서 갈리나** — 둘 다 사전을 쓰는데 왜 다른가?
* ★ [24번](../24-decorators/2-summary.md)의 `__wrapped__` 는 1번 `[4]` 에서 **몸통을 몇 번** 돌렸나 — 캐시를 완전히 건너뛰었다고 말할 수 있나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|---|---|---|---|
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |
