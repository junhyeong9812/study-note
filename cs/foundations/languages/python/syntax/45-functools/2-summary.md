# python/syntax/45-functools — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만(문서 원본 `.rst` 를 받아 문장을 찾았다).
> - [`functools`(3.12)](https://docs.python.org/3.12/library/functools.html) —
>   `lru_cache` 의 *"Since a dictionary is used to cache results, the positional and keyword arguments to the function must be hashable."* ·
>   *"The cache keeps references to the arguments and return values until they age out of the cache or until the cache is cleared."* ·
>   *"If a method is cached, the `self` instance argument is included in the cache."* ·
>   *"If typed is false, the implementation will usually regard them as equivalent calls and only cache a single result. (Some types such as str and int may be cached separately even when typed is false.)"* ·
>   *"`f(a=1, b=2)` and `f(b=2, a=1)` differ in their keyword argument order and may have two separate cache entries."*
> - 같은 문서 `cached_property` 절 — *"The cached_property decorator only runs on lookups and only when an attribute of the same name doesn't exist."* ·
>   *"The cached value can be cleared by deleting the attribute."* · *"versionchanged 3.12: Prior to Python 3.12, cached_property included an undocumented lock … In Python 3.12+ this locking is removed."*
> - 같은 문서 `singledispatch` 절 — *"the dispatch happens on the type of the first argument"* · *"its method resolution order is used to find a more generic implementation"* · *"versionchanged 3.11: The register() attribute now supports types.UnionType and typing.Union as type annotations."*
> - 같은 문서 `partial` 객체 절 — *"They have three read-only attributes"* · *"the `__name__` and `__doc__` attributes are not created automatically."*
> - 같은 문서 `reduce` 절 — *"If initializer is not given and iterable contains only one item, the first item is returned."*
> - [FAQ — How do I cache method calls?](https://docs.python.org/3.12/faq/programming.html#faq-cache-method-calls) —
>   *"The disadvantage is that instances are kept alive until they age out of the cache or until the cache is cleared."*
> - [What's New in 3.12](https://docs.python.org/3.12/whatsnew/3.12.html) — *"Exceptions raised in a class or type's `__set_name__` method are no longer wrapped by a RuntimeError. Context information is added to the exception as a PEP 678 note."*
>
> **실행 검증** — 이 문서에 실린 출력은 전부 이 머신에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.\
> 판은 `python3` **3.12.3** 이 본판이고, 판 경계를 위해 `python3.11` **3.11.15** 로 두 블록을 더 던졌다.\
> ★★★ **이 문서가 잰 것은 「몸통이 몇 번 돌았나」·`cache_info()` 의 적중·실패 수·「약한 참조가 아직 가리키나」(참/거짓)뿐이다** —
> **시간·메모리 바이트는 한 번도 재지 않았다.** 「`lru_cache` 가 빠르게 한다」는 이 문서가 주장하지 않는다 — 잰 것은 **몸통 실행 수 21891 대 21** 이다.\
> **버전**(문서의 `versionadded`·`versionchanged`) — `lru_cache` **3.2**(`typed` **3.3**) · `partial`·`reduce` 는 3.12 문서에 추가 판 표기가 없다 · `singledispatch` **3.4**(어노테이션 등록 **3.7**, 유니온 **3.11**) · `cached_property` **3.8**(잠금 제거 **3.12**) · `cache` **3.9**.\
> ★ **구현 대 언어 보장 한 줄** — 위 문서 문장들이 보장이고, **「`int`·`str` 인자 하나는 따로 칸을 잡는다」는 CPython 의 키 함수가 정한 것**이다(문서는 「그럴 수 있다」고만 적는다). 예외 **문구**도 CPython 의 것이다.\
> ★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다 | 안 흔들린다(근거로 써도 되는 칸) |
> |---|---|
> | 판이 오르면 예외 **문구**(3.11 과 3.12 가 `__set_name__` 에서 이미 갈렸다 — 동작 10) | ★★ **몸통 실행 수** · `CacheInfo(...)` 의 네 수 · **살아 있나 `True`/`False`** |
> | — (주소·시간·`set` 출력을 한 곳도 안 찍었다 · `registry` 는 이름순으로 정렬해 찍었다) | 격자 마지막 줄 **「… N / M」** · 불린 구현의 이름 |
>
> **선행** — [24-decorators](../24-decorators/2-summary.md)(★★★ **`@` 는 이름에 결과를 다시 묶는다 · `functools.wraps` 가 옮기는 칸** — 그쪽이 정본) ·
> [30-repr-eq-hash-contracts](../30-repr-eq-hash-contracts/2-summary.md)(★★ **`unhashable type`** — 캐시 키가 되려면 해시가 돼야 한다) ·
> [12-dict-and-key-requirements](../12-dict-and-key-requirements/2-summary.md)(★★ **`1`·`1.0`·`True` 가 한 칸** — 그런데 이 주제의 캐시는 그 규칙을 **그대로 따르지 않는다**) ·
> [33-property-descriptor-slots](../33-property-descriptor-slots/2-summary.md)(`cached_property` 가 **비데이터 디스크립터**) ·
> [40-type-hints-at-runtime](../40-type-hints-at-runtime/2-summary.md)(`singledispatch` 는 **힌트가 실행을 바꾸는 자리**).

## 한눈에 — 쉽게 말하면

**`functools` 는 「함수에 덧대는 부품 상자」다.** 함수 몸통은 안 건드리고 **바깥에 무언가를 덧댄다.**

* `lru_cache` — 함수 옆에 **메모장**을 붙인다. 같은 주문이 오면 몸통을 안 부르고 메모를 읽는다.
* `partial` — 주문서의 **몇 칸을 미리 채워 둔** 새 주문서.
* `reduce` — 줄 선 값들을 **왼쪽부터 하나로 접는** 사람.
* `cached_property` — 처음 한 번 계산해 **물건에 스티커로 붙여 두는** 속성.
* `singledispatch` — 첫 손님의 **옷(타입)을 보고 창구를 골라 주는** 안내 데스크.

★★★ 이 주제의 과녁은 **메모장이 무엇을 붙드나**다. 메모장은 **주문서(인자)와 답(반환값)을 통째로 들고 있다** — 그래서 주문서에 적힌 손님(`self`)도 **메모장이 버릴 때까지** 집에 못 간다.

```text
   @lru_cache(maxsize=2)                          메모장 (함수 옆에 붙은 dict)
   def rain(self, day): ...                     ┌──────────────────────────────┐
                                                │ 키 (self=s, day=1)  ->  10    │
   s = Station(); s.rain(1); del s     ───▶     │      ▲                        │
                                                └──────┼───────────────────────┘
                                                       │  ★ 키가 s 를 붙들고 있다
   gc 를 돌려도 s 는 안 사라진다                          s ── 살아 있다 (True)
   다른 호출 둘로 메모장이 밀려나면                           s ── 사라진다 (False)
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 메모장 | `lru_cache` 가 함수 옆에 두는 사전 | `cache_info()` 의 `currsize` |
| 메모장에 적힌 주문서 | 인자로 만든 **키** — 인자 객체를 붙든다 | 약한 참조가 `del` 뒤에도 `True` |
| 메모장의 쪽수 한도 | `maxsize` — 넘치면 **오래된 것부터** 버린다 | 다른 호출 뒤 `False` |
| 해시가 안 되는 주문서 | 리스트 인자 | `TypeError: unhashable type` |
| 미리 채운 주문서 | `partial` 객체 | `func`·`args`·`keywords` 세 칸 |
| 물건에 붙인 스티커 | `cached_property` 가 인스턴스 `__dict__` 에 넣은 값 | `vars(o)` 에 보인다 |
| 안내 데스크의 창구표 | `singledispatch` 의 `registry` | `dispatch(타입)` 이 고른 이름 |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.\
「**메서드에 `@lru_cache` 를 달았더니 요청마다 만든 객체가 안 사라진다**」와
「**캐시된 함수가 돌려준 리스트를 호출한 쪽이 고쳤더니 다음 호출이 이상한 값을 준다**」가 그것이다.\
앞엣것은 **메모장이 주문서째 붙든 것**이고, 뒤엣것은 **메모장의 답을 복사하지 않고 원본을 건넨 것**이다.

> **메모이제이션(memoization)** — 같은 인자로 다시 부르면 계산하지 않고 **적어 둔 답**을 돌려주는 것.\
> 예: `fib(20)` 을 캐시 없이 부르면 몸통이 21891 번 돌고, 캐시를 달면 21 번 돈다(동작 1).

> **LRU(least recently used)** — 칸이 모자랄 때 **가장 오래 안 쓴 것**부터 버리는 방식.\
> 예: `maxsize=2` 인 캐시에 셋째 키가 들어오면 가장 먼저 쓰고 안 쓴 키가 밀려난다.

### ★★ 이 주제가 쓰는 창 / 부적용인 창

**본체는 ③ 「약한 참조가 아직 가리키나」 창이다.** 「캐시가 메모리에 주는 영향」을 **바이트로 재지 않고**, `weakref.ref` 로 **객체가 회수됐나를 참/거짓으로** 묻는다 — **같은 질문을 다른 창으로 물은 것**(제5의 상태)이다.

| 창 | 무엇을 말해 주나 | 못 보는 것 |
|---|---|---|
| ① ★★ **`cache_info()`** | 적중·실패·칸 수 | 칸 안에 **무엇이** 있나 |
| ② ★★ **몸통 실행 계수기** | 몸통이 **실제로 몇 번** 돌았나 | 시간 |
| ③ ★★★ **약한 참조 `alive(r)`**(`gc.collect()` 뒤) | 캐시가 객체를 **붙들고 있나** | 몇 바이트인가 |
| ④ ★★ **`registry`·`dispatch(타입)`** | `singledispatch` 가 **어느 구현을 고르나** | — |
| ⑤ ★ **`vars(obj)`** | `cached_property` 가 값을 **어디에 두나** | — |
| ⑥ ★ **판 격자**(3.11 대 3.12) | `cached_property` 의 잠금 · `__set_name__` 예외 포장 | 3.13 이후 |
| ★ **부적용인 창** — 시간 · 메모리 바이트 | — | 「`lru_cache` 가 빠르다」·「N 바이트 샌다」를 **한 번도 재지 않았다** |

★★ **③이 이 주제의 네 번째 창이다.** ①만 보면 캐시는 **숫자 넷**(`hits`·`misses`·`maxsize`·`currsize`)이다. 그 숫자는 **칸이 몇 개인지만** 말하고 **그 칸이 무엇을 쥐고 있는지**는 말하지 않는다.\
③을 열어야 「**칸 하나가 인스턴스 하나를 살려 두고 있다**」가 보인다.

## 이 주제가 답하려는 질문

1. ★★★ **`lru_cache` 는 무엇을 붙드나** — 인자·`self`·반환값이 **언제까지** 살아 있나. 「영원히」가 맞는 말인가.
2. ★★ **무엇이 같은 칸이 되나** — `typed=False` 에서 `1`·`1.0`·`True` 는 한 칸인가. [12번](../12-dict-and-key-requirements/2-summary.md)의 사전 키 규칙과 같은가.
3. **나머지 부품은 무엇을 대가로 무엇을 주나** — `partial` 의 세 칸 · `reduce` 의 빈 입력 · `singledispatch` 가 보는 것 · `cached_property` 가 값을 두는 곳.

★ 첫째가 이 주제의 인출 목표다.
**「캐시의 키가 인자 객체를 붙든다 — 그래서 `maxsize` 가 곧 수명이다」라는 한 문장으로 메서드 누수와 `cache_clear` 를 함께 설명할 수 있는 것**이 아는 것과 들은 것의 경계다.

## 동작 방식

> 이 절이 본문이다. 그림이 먼저 오고 문장이 그 그림을 읽어 준다.

### 1. ★★ `lru_cache` 의 계수 — 몸통 실행 수와 `cache_info()`

**언제 쓰나** — 「캐시가 일을 하고 있나」를 확인할 때. **시간 대신 몸통 실행 수와 적중 수**로 본다.

```text
   fib(20) 호출 나무                     캐시를 달면
   fib(20)                              fib(20) ─ miss ─ fib(19) ─ miss ─ … ─ fib(1) miss, fib(0) miss
   ├─ fib(19)                                      └ fib(18) hit        ★ 둘째 가지는 대개 메모를 읽는다
   │  ├─ fib(18) …                       miss = 서로 다른 n 의 수 = 21  (0 ~ 20)
   │  └─ fib(17) …                       hit  = 둘째 가지에서 읽은 수
   └─ fib(18) … ★ 같은 n 이 수없이 반복
```

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

그림 해설.

* ★★ **`[1]`·`[2]` — 몸통 실행 수 `21891` 대 `21`.** 캐시를 달면 **서로 다른 `n` 마다 한 번씩만**(`0` 부터 `20` 까지 21개) 몸통이 돈다. `misses=21` 과 같은 수다.
  ★ **잰 것은 실행 수다 — 시간이 아니다.** 「몇 배 빨라졌다」는 이 블록이 말하지 않는다.
* ★★ **`[3]`** — 같은 `fib(20)` 을 다시 부르면 **`hits` 만 1 늘고** 몸통은 안 돈다.
* ★★ **`[4]` — `__wrapped__` 는 맨 위 한 번만 캐시를 건너뛴다.** 몸통 실행이 **1** 늘었고 `hits` 가 **2** 늘었다.
  `__wrapped__(20)` 안에서 부른 `fib(19)`·`fib(18)` 은 **전역 이름 `fib` — 캐시 쪽**을 부르기 때문이다. `__wrapped__` 는 [24번](../24-decorators/2-summary.md) 동작 6 의 그 칸이다 — `lru_cache` 로 감싼 것도 `__name__` 과 `__wrapped__` 를 갖는다(`fib` · `True`).
* ★ **`[6]`** — `pair(a=1, b=2)`·`pair(b=2, a=1)`·`pair(1, 2)` 가 **`misses=3`**, 칸 셋. 같은 뜻의 호출인데 **키가 셋**이다.
  ★ 문서가 먼저 적는다 — *"differ in their keyword argument order and may have two separate cache entries."* **위치로 준 것과 키워드로 준 것도** 다른 칸이다.

**비용** — 칸 하나마다 **키(인자)와 답을 붙든다.** 무엇을 붙드는지가 동작 2 다.

### 2. ★★★ 메모장이 붙드는 것 — 약한 참조로 본 수명 (본체)

**언제 쓰나** — 캐시 달린 함수에 **객체**를 넘길 때. 특히 **메서드**에 `@lru_cache` 를 달 때.

```text
   캐시 칸 하나                                    회수되려면
   ┌──────────────── 키 ────────────────┐         키에서 빠져야 한다
   │ (look, t)   또는 (rain, self=s, 1) │ ──▶ 답   ① cache_clear()
   └────────────────────────────────────┘         ② maxsize 가 차서 밀려남 (LRU)
        ★ t · s 에 대한 강한 참조                    ③ maxsize=None 이면 ②가 없다 -> ①뿐
```

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

그림 해설.

* ★★★ **`[1]` — 인자로 넘긴 객체는 `del` 뒤에도 `True`, `cache_clear()` 뒤에야 `False`.** 키가 그 객체를 붙들고 있다.
  문서 — *"The cache keeps references to the arguments and return values until they age out of the cache or until the cache is cleared."*
* ★★★ **`[2]` — 메서드도 같다. `self` 가 키에 들어간다.** `del s` 뒤에도 `True`.
  ★★ **그런데 「영원히」는 아니다** — `maxsize=2` 인 캐시에 **다른 인스턴스 둘**이 부르자 `s` 의 칸이 밀려나 **`False`** 가 됐다(`misses=3 · currsize=2`).
  **수명을 정하는 것은 `maxsize` 와 `cache_clear()` 다.** `maxsize=None`(`[1]` 처럼)이면 밀려나는 일이 없으니 **`cache_clear()` 까지 영원히**다.
  FAQ 가 이 둘을 그대로 적는다 — *"instances are kept alive until they age out of the cache or until the cache is cleared."*
* ★★ **`Station.rain.cache_info()` 는 클래스에 하나다** — 세 인스턴스의 호출이 **한 메모장**에 쌓였다. FAQ 의 말로는 `lru_cache` 가 *"at the class level"*, `cached_property` 가 *"at the instance level"* 이다.
* ★★ **`[3]` — `cached_property` 는 `self` 를 안 붙든다**(`False`). 값을 **인스턴스 자신의 `__dict__`** 에 두니 인스턴스와 함께 사라진다(동작 8).
* ★ **`[4]` — 반환값도 붙든다.** 받은 쪽이 `del` 해도 `True` 이고, 다시 부르면 **같은 객체**(`is` 가 `True`)를 준다 — 동작 4 의 「돌려준 리스트를 고치면」이 여기서 나온다.

**비용** — 메서드에 `@lru_cache` 를 달면 **캐시 칸 수만큼 인스턴스가 살아 있다.** `maxsize=None`(또는 `@cache`)이면 **프로세스가 끝날 때까지**다. 바이트 수는 **재지 않았다.**

### 3. ★★ 무엇이 같은 칸이 되나 — `typed` 격자

**언제 쓰나** — `1` 과 `1.0` 처럼 **`==` 인데 타입이 다른 인자**로 같은 함수를 부를 때.

```text
   12번의 사전 규칙                         이 캐시의 실제 (typed=False)
   d[1] · d[1.0] · d[True]  -> 한 칸         f(1) ; f(1.0)     -> 칸 2   ★ 규칙과 다르다
   hash 같고 == 참이면 같은 키               f(1.0) ; f(True)  -> 칸 1
                                           f(1, 0) ; f(1.0, 0) -> 칸 1
   ★ 차이는 "키를 무엇으로 만드나" — 인자 하나가 int·str 이면 그 값 자체가 키, 아니면 튜플 모양의 키
       키 1  대  키 [1.0]  : 한쪽은 int, 한쪽은 리스트 모양 -> == 가 거짓 -> 다른 칸
```

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

그림 해설.

* ★★★ **`typed=False` 에서 `f(1) ; f(1.0)` 이 칸 2 다.** 「`typed=False` 면 `1` 과 `1.0` 이 한 칸」은 **인자가 하나일 때 틀린다.**
  `f(1.0) ; f(True)` 는 칸 1, `f(1, 0) ; f(1.0, 0)` 도 칸 1 이다 — **`int` 인자 하나만** 따로 논다. `f(1) ; f(True)` 도 칸 2 다(`True` 는 `bool` 이지 `int` 그 자체가 아니다).
  ★ 문서가 이 여지를 남겨 두었다 — *"(Some types such as str and int may be cached separately even when typed is false.)"*
* ★★ **`[구현]` 줄이 이유를 보여 준다.** 순수 파이썬 판 키 함수 `_make_key` 는 **인자가 `int`·`str` 하나면 그 값을 그대로** 키로 쓰고(`1`·`'a'`), 나머지는 **`_HashedSeq`**(리스트 모양)로 싼다.
  `1 == [1.0]` 은 거짓이라 **다른 칸**이 된다. ★ 실제로 도는 것은 C 모듈 `_functools` 의 판이다(`True`) — 격자 표는 **그 C 판을 부른 결과**이고, `_make_key` 는 **같은 결과를 설명하는 순수 파이썬 판**이다.
* ★★ **`typed=True` 는 타입이 다르면 전부 나눈다** — 단 **튜플 속의 것은 안 본다**(마지막 행 칸 1). 문서 — *"type specificity applies only to the function's immediate arguments rather than their contents."*
* ★ 스크립트의 집계 — **`typed=False 6 / 8 · typed=True 2 / 8`**. `f('a') ; f('a')` 는 **대조 행**(늘 칸 1)이다.

**비용** — 캐시가 「같은 호출」을 **사전 규칙보다 좁게** 본다. 틀린 답은 안 나오고 **칸이 더 생길 뿐**이다. 그래서 **조용하다.**

### 4. ★★ 가변 인자 · 가변 반환 — 막히는 것과 조용한 것

**언제 쓰나** — 리스트를 인자로 넘기거나, 리스트·제너레이터를 돌려주는 함수에 캐시를 달 때.

```text
   인자가 리스트              -> 키를 못 만든다 -> TypeError (시끄럽다)       30번의 unhashable 과 같은 문구
   돌려준 리스트를 고친다       -> 메모장의 답 그 자체를 고쳤다 -> 다음 호출이 고친 것을 받는다 (조용하다)
   돌려준 것이 제너레이터       -> 메모장에 "한 번 쓰면 끝나는 것"이 적혔다 -> 둘째 호출은 빈 것 (조용하다)
```

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

그림 해설.

* ★★ **`[1]` — 리스트 인자는 `TypeError: unhashable type: 'list'`.** 튜플 **안에** 리스트가 있어도 같다. [30번](../30-repr-eq-hash-contracts/2-summary.md) 동작 2 의 그 문구다 — 캐시의 키가 사전 키이기 때문이다.
  ★ 실패한 두 호출은 **적중도 실패도 아니다** — `misses=2` 는 성공한 튜플·`frozenset` 호출 둘이다.
* ★★★ **`[2]` — 돌려준 리스트에 `append` 하자 두 번째 호출이 `['n0', 'n1', 'extra']` 를 받았다.** `a is b` 가 `True` — **메모장의 답 자체**를 건넸기 때문이다(동작 2 의 `[4]`).
  **에러가 없다.** 이 주제에서 가장 조용한 사고다.
* ★★ **`[3]` — 제너레이터를 돌려주는 함수에 캐시를 달면 둘째 호출이 `[]`.** 첫 호출이 소진한 **같은 제너레이터**를 다시 받았다(`hits=1`).
  [16번](../16-iterator-protocol/2-summary.md)의 「소진된 것과 빈 것은 구분되지 않는다」가 캐시를 만나 생긴 모양이다. 문서도 *"functions that need to create distinct mutable objects on each call (such as generators and async functions)"* 에 캐시가 맞지 않는다고 적는다.

**비용** — 캐시를 달 함수는 **해시되는 인자를 받고, 불변인 값을 돌려줘야** 안전하다. 가변을 돌려줘야 하면 **받는 쪽이 복사**한다.

### 5. ★ `partial` — 세 칸을 가진 호출 가능 객체

**언제 쓰나** — 인자 몇 개를 **미리 고정한 새 함수**가 필요할 때([19번](../19-function-argument-rules/2-summary.md)·[23번](../23-lambda-and-higher-order-functions/2-summary.md)이 넘긴 자리).

```text
   partial(price, 1000, fee=50)          부를 때 p(2, fee=0)
   ┌ func     = price                    price( *args , *(2,) , **{**keywords, **{fee: 0}} )
   ├ args     = (1000,)                         1000    2        fee=0  ★ 부를 때 준 키워드가 이긴다
   └ keywords = {'fee': 50}              p.keywords 는 그대로 {'fee': 50}
```

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

그림 해설.

* ★ **`[1]`** — 세 칸이 `price`·`(1000,)`·`{'fee': 50}`. 부를 때 준 `fee=0` 이 **이번 호출에서만** 이기고, `p.keywords` 는 그대로다. `inspect.signature(p)` 는 **남은 인자**만 보여 준다.
* ★ **`[2]` — `partial` 을 `partial` 로 다시 싸면 `q.func is price` 가 `True`** 다. 안쪽 `partial` 을 **펴서** 한 겹으로 만들었다 — ★ **CPython 의 동작**이고 문서의 보장 문장은 찾지 못했다.
* ★★ **`[3]`** — `partial` 은 **함수가 아니다**. `__name__` 이 없다(`False`). 문서 — *"the `__name__` and `__doc__` attributes are not created automatically."*
  그래서 `partial` 객체를 [24번](../24-decorators/2-summary.md)의 데코레이터로 감싸 `functools.wraps` 를 쓰면 **옮길 이름이 없다.**
* ★★ **`[4]` — `partial` 은 만들 때 값을 잡고, `lambda` 는 부를 때 이름을 찾는다.** `rate` 를 2 에서 3 으로 바꾸자 `partial` 은 `2000`, `lambda` 는 `3000`.
  [22번](../22-closures-and-late-binding/2-summary.md)의 늦은 바인딩을 `partial` 이 피하는 이유가 이것이다.

**비용** — 없다시피 하다. 다만 **이름표가 없어** 로그·예외 메시지에서 `functools.partial(...)` 로 보인다.

### 6. ★ `reduce` — 빈 입력과 한 원소

**언제 쓰나** — 두 인자 함수로 줄을 **하나로 접을** 때. 순서(왼쪽부터 `((1+2)+3)`)는 [23번](../23-lambda-and-higher-order-functions/2-summary.md) 동작 13 이 정본이다 — 여기는 **가장자리**만.

```text
   reduce(add, [1, 2, 3])        add(add(1, 2), 3)        호출 2
   reduce(add, [1, 2, 3], 100)   add(add(add(100, 1), 2), 3)   호출 3   ★ 초깃값이 맨 앞에 선다
   reduce(add, [7])              7                        호출 0   ★ 한 원소면 함수를 안 부른다
   reduce(add, [])               ???                      접을 것이 없다
```

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

그림 해설.

* ★★ **빈 입력에 초깃값이 없으면 `TypeError: reduce() of empty iterable with no initial value`.** 초깃값이 있으면 **그것을 그대로**(`100`) 돌려준다 — 함수는 **0 번**.
* ★ **한 원소면 함수를 안 부른다**(`[7]` → `7`, 호출 0). 문서 — *"If initializer is not given and iterable contains only one item, the first item is returned."*
* ★★ **`None` 도 초깃값이다** — `reduce(add, [], None)` 은 `None`, `reduce(add, [1, 2], None)` 은 `add(None, 1)` 을 불러 `TypeError`.
  ★ 문서의 「대략 같은 코드」는 `initializer=None` 을 **「안 줬다」의 표시**로 쓴다 — 그 코드대로면 `None` 을 안 준 것으로 본다. **실제 C 판은 「안 줬다」와 `None` 을 구분한다.** 문서의 대략 코드는 대략이다.
* ★ **`[2]` — `accumulate` 는 중간값을 전부 내고, 마지막 값이 `reduce` 와 같다**(`True`). `initial=` 을 주면 **초깃값부터** 낸다. [44번](../44-itertools/2-summary.md)이 재지 않고 넘긴 함수다.

**비용** — `sum`·`max`·`any` 로 되는 것에 `reduce` 를 쓰면 **읽는 사람이 접는 방향을 머리로 재구성**해야 한다([23번](../23-lambda-and-higher-order-functions/2-summary.md)).

### 7. ★★ `singledispatch` — 첫 인자의 타입으로 창구를 고른다

**언제 쓰나** — 타입마다 다른 처리를 `if isinstance …` 사슬 대신 **등록**으로 나눌 때.

```text
   show(Meters(3))        Meters 의 MRO:  Meters -> float -> object
                                             │        │
   registry 에서 차례로 찾는다               없음    ★ for_float_or_str
   show(True)             bool 의 MRO:    bool -> int -> object
                                                   ★ for_int
   show({1: 2})           dict -> object                    ★ show (object 에 등록된 원래 함수)
   show('s')              str 은 등록돼 있다 -> for_float_or_str   (Sequence 이기도 하지만 더 가까운 것이 이긴다)
```

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

그림 해설.

* ★★ **`[1]` — `registry` 는 `타입 -> 구현` 표**이고, `int | str` 로 등록한 함수는 **두 칸**(`float`·`str`)에 들어간다(3.11+ — 동작 10 의 판 격자에서 3.11 도 받았다). 원래 함수는 **`object` 칸**이다.
* ★★ **`[2]` — 등록 안 된 타입은 MRO 를 따라 올라간다.** `bool` → `int` 구현, `Meters`(float 하위 클래스) → `float` 구현, `dict`·`None` → `object` 칸의 원래 함수.
  `list`·`tuple` 은 **추상 기반 클래스 `Sequence`** 로 등록한 구현에 갔다 — 문서의 *"virtual subclasses of the base class will be dispatched to that implementation"*.
* ★ **`type(show.registry)` 는 `mappingproxy`** — 읽기 전용이다. 등록은 `register` 로만.
* ★★★ **`[3]` — 둘째 인자는 안 본다.** `pair(1, 2)` 는 둘째가 `int` 인데도 **`int 칸`** 으로 갔다 — 어노테이션 `b: str` 은 **무시**됐다. 문서 — *"the dispatch happens on the type of the first argument"*.
* ★★ **`[4]` — `list[int]` 는 등록이 안 된다** — `Invalid annotation for 'x'. list[int] is not a class.` 원소 타입으로는 못 가른다.
* ★ 등록은 **어노테이션을 실행 중에 읽는다** — 그래서 `from __future__ import annotations` 가 지역 클래스 등록을 `NameError` 로 깨뜨린다. 그 격자는 [40번](../40-type-hints-at-runtime/2-summary.md) 동작 3·4 가 정본이다. [41번](../41-typing-and-generic-syntax/2-summary.md)이 넘긴 「유니온 어노테이션으로 등록되나」의 답이 `[1]` 이다.

**비용** — 호출마다 **첫 인자의 타입으로 표를 찾는다.** 둘째 인자로 가르고 싶으면 이 도구가 아니다.

### 8. ★★ `cached_property` — 인스턴스 칸에 적어 두고 비켜선다

**언제 쓰나** — 인자 없는 비싼 계산을 **인스턴스마다 한 번만** 하고 싶을 때.

비데이터 디스크립터라는 것 · `vars(c)` 에 값이 들어가는 것 · `__slots__` 클래스에서 `TypeError`(*"No '__dict__' attribute … to cache"*) 는 [33번](../33-property-descriptor-slots/2-summary.md) 「더 들어가면」이 이미 쟀다 — **여기는 그 다음부터**다.

```text
   첫 읽기  o.total                     둘째 읽기 o.total
   인스턴스 __dict__ 에 'total' 없음       인스턴스 __dict__ 에 'total': 6   ★ 인스턴스 칸이 이긴다 (비데이터)
        -> 클래스의 cached_property 호출        -> cached_property 는 불리지도 않는다
        -> 결과를 o.__dict__['total'] 에 적는다
   del o.total  -> 적어 둔 것을 지운다 -> 다음 읽기에서 다시 계산
```

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

그림 해설.

* ★★ **`[1]`·`[2]`** — 두 번 읽어도 몸통 **1** 번. `items` 를 고쳐도 **옛 값 `6`** 이다 — **값이 바뀐 것을 모른다.** 스티커는 붙인 뒤로 다시 안 본다.
* ★★ **`[3]` — `del o.total` 이 캐시를 지운다**(다음 읽기에서 `10`, 몸통 **2**). 문서 — *"The cached value can be cleared by deleting the attribute."*
* ★ **`[4]`·`[5]`** — `cached_property` 는 **대입을 막지 않는다**(`0`). `setter` 없는 `property` 는 `AttributeError` 다. 문서 — *"A regular property blocks attribute writes unless a setter is defined. In contrast, a cached_property allows writes."*
* ★ **`[6]`** — 클래스에서 읽으면 **디스크립터 자신**(`cached_property`)이 나오고, 자기가 붙은 이름을 `attrname` 으로 안다(`__set_name__`).
* ★ 한 `cached_property` 객체를 **두 이름에** 붙이면 클래스를 만드는 순간 예외가 난다 — 그 예외의 **타입이 판마다 다르다**(동작 10).

**비용** — **인스턴스마다** 값을 들고 있다(동작 2 의 `[3]` — 대신 인스턴스와 함께 사라진다). 문서는 이것이 **PEP 412 키 공유 사전**을 방해해 사전이 커질 수 있다고 적는다 — 크기는 **재지 않았다.**

### 9. ★ `cmp_to_key` — 비교 함수를 키로 바꾼다

**언제 쓰나** — 옛 `cmp(a, b)` 꼴 비교 함수를 `sorted(key=)` 에 넣어야 할 때([10번](../10-list-methods-and-sort-key/2-summary.md)·[31번](../31-comparison-protocol-and-sortability/2-summary.md)이 「본거지」로 넘긴 자리).

```python
# e45_cmp.py
from functools import cmp_to_key


def by_len_then_desc(a, b):
    if len(a) != len(b):
        return len(a) - len(b)
    return (a < b) - (a > b)


words = ["kiwi", "fig", "apple", "pear", "date"]
key = cmp_to_key(by_len_then_desc)
print("[1] sorted(words, key=cmp_to_key(...)) :", sorted(words, key=key))
k1, k2 = key("fig"), key("pear")
print("[2] type(key('fig')).__name__          :", type(k1).__name__)
print("    key('fig') < key('pear')           :", k1 < k2)
print("    key('fig').obj                     :", k1.obj)
try:
    hash(k1)
except TypeError as ex:
    print("[3] hash(key('fig')) -> TypeError:", ex)
```

```text
===== python3 - <e45_cmp.py =====
[1] sorted(words, key=cmp_to_key(...)) : ['fig', 'pear', 'kiwi', 'date', 'apple']
[2] type(key('fig')).__name__          : KeyWrapper
    key('fig') < key('pear')           : True
    key('fig').obj                     : fig
[3] hash(key('fig')) -> TypeError: unhashable type: 'functools.KeyWrapper'
(exit 0)
```

* ★ **`[1]`** — 길이 오름차순, 같은 길이면 **글자 내림차순**. 비교 함수 하나가 두 기준을 다 표현했다.
* ★ **`[2]`** — 키 함수가 돌려주는 것은 **`KeyWrapper`** 라는 객체이고, `<` 를 그 비교 함수로 푼다. 원래 값은 `.obj` 에 있다.
* ★ **`[3]` — 그 객체는 해시가 안 된다**(`unhashable type: 'functools.KeyWrapper'`). 정렬 키로만 쓰라는 뜻이다 — 사전 키·`lru_cache` 인자로는 못 쓴다.

**비용** — 비교가 **파이썬 함수 호출**이 된다. 몇 번 불리는지는 정렬 알고리즘이 정하므로 **세지 않았다.**

### 10. ★ 판 격자 — 3.11 대 3.12

**언제 쓰나** — 같은 코드가 3.11 서버와 3.12 서버에서 다르게 도는지 볼 때.

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

(3.11 블록의 소스는 위와 **한 글자도 같다** — 파일 이름만 `e45_version_py311.py` 다.)

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

(`e45_setname_py311.py` 도 위 소스와 한 글자도 같다.)

* ★★ **`cached_property` 의 잠금** — 3.11 은 `lock` 속성이 **있고**(`True`) 3.12 는 **없다**(`False`). 문서 — *"In Python 3.12+ this locking is removed."*
  ★ **그래서 3.12 에서는 여러 스레드가 같은 인스턴스의 몸통을 두 번 돌릴 수 있다**(문서 — *"The getter function could run more than once on the same instance"*). **경쟁은 재지 않았다** — 속성의 있고 없음만 봤다.
* ★★ **`__set_name__` 의 예외** — 3.11 은 `RuntimeError: Error calling __set_name__ …`(원인 `TypeError` 가 `__cause__`), 3.12 는 **`TypeError` 그대로** + 같은 문장이 **`__notes__`** 로. What's New 3.12 의 그 문장이다.
* ★ **유니온 등록·`functools.cache`** — 두 판 다 된다(3.11·3.9 부터).

**비용** — `except RuntimeError` 로 `__set_name__` 실패를 잡던 코드는 **3.12 에서 못 잡는다.**

## 문법 — 형태와 규칙

**형태**

```text
from functools import lru_cache, cache, partial, reduce, cached_property, singledispatch, cmp_to_key

@lru_cache(maxsize=128, typed=False)   # 인자는 해시돼야 한다 · f.cache_info() · f.cache_clear() · f.__wrapped__
@cache                                 # = lru_cache(maxsize=None) — 3.9+
p = partial(f, 1, k=2)                 # p.func · p.args · p.keywords
reduce(f, xs[, 초깃값])                  # 빈 xs + 초깃값 없음 -> TypeError
@cached_property                       # 인자 없는 메서드 · 인스턴스 __dict__ 에 적는다 · del 로 지운다
@singledispatch / @f.register          # 첫 인자의 타입 · 어노테이션 또는 register(타입)
sorted(xs, key=cmp_to_key(cmp))
```

규칙 열.

1. ★★★ **캐시의 키는 인자 객체를 붙든다** — `self` 도 인자다. 수명은 **`maxsize` 와 `cache_clear()`** 가 정한다(동작 2).
2. ★★ **캐시의 「같은 호출」은 사전 규칙보다 좁다** — `int`·`str` 인자 하나는 따로, 키워드 순서·위치 대 키워드도 따로(동작 1·3).
3. ★★ **인자는 해시돼야 하고, 반환값은 공유된다** — 리스트 인자는 `TypeError`, 돌려준 리스트는 **메모장의 원본**(동작 4).
4. ★ **`partial` 은 만들 때 값을 잡는다** — 부를 때 준 키워드가 이번 호출에서만 이긴다(동작 5).
5. ★ **`reduce` 는 빈 입력 + 초깃값 없음이면 `TypeError`** — `None` 도 초깃값이다(동작 6).
6. ★★ **`singledispatch` 는 첫 인자의 타입만 본다** — 없으면 MRO 를 따라 `object` 까지(동작 7).
7. ★★ **`cached_property` 는 인스턴스 칸에 적고 비켜선다** — 값이 바뀌어도 모른다 · `del` 로 지운다 · `__slots__` 면 못 쓴다(동작 8).

## 어디서 틀리나

### (1) ★★★ 메서드에 `@lru_cache` 를 달고 인스턴스가 사라질 거라 믿는다

**`self` 가 키에 들어가 캐시 칸 수만큼 살아 있다**(동작 2 의 `[2]`). `maxsize=None` 이면 `cache_clear()` 까지다.

### (2) ★★★ 「`lru_cache` 는 영원히 붙든다」로 외운다

**`maxsize` 가 차면 밀려나 회수된다**(`False`). 「영원히」는 **`maxsize=None`·`@cache` 일 때**만 맞다.

### (3) ★★ 「`typed=False` 면 `1` 과 `1.0` 이 한 칸」으로 안다

**인자가 하나면 칸 2**(동작 3). 사전 규칙([12번](../12-dict-and-key-requirements/2-summary.md))과 다르다 — 캐시가 키를 만드는 방식이 다르기 때문이다.

### (4) ★★ 캐시된 함수가 돌려준 리스트를 고친다

**다음 호출이 고친 것을 받는다**(동작 4 의 `[2]`). 에러가 없다.

### (5) ★★ 제너레이터를 돌려주는 함수에 캐시를 단다

**둘째 호출이 빈 결과**(동작 4 의 `[3]`).

### (6) ★ 리스트를 받는 함수에 캐시를 단다

**`TypeError: unhashable type: 'list'`**. 튜플로 바꿔 넘긴다.

### (7) ★ `partial` 객체에 `__name__` 이 있을 거라 믿는다

**없다**(동작 5 의 `[3]`). 로그에 이름을 찍으려면 `p.func.__name__`.

### (8) ★ `reduce(f, xs)` 에 빈 `xs` 가 올 수 있다는 것을 잊는다

**`TypeError`**. 초깃값을 준다.

### (9) ★★ `singledispatch` 로 둘째 인자를 가르려 한다

**첫 인자만 본다**(동작 7 의 `[3]`). 둘째 인자의 어노테이션은 **조용히 무시된다.**

### (10) ★★ `cached_property` 의 값이 원본 변경을 따라갈 거라 믿는다

**안 따라간다**(동작 8 의 `[2]`). 원본을 고치면 `del o.total`.

### (11) ★ 3.12 에서 `cached_property` 가 스레드마다 한 번만 돈다고 믿는다

**잠금이 없어졌다**(동작 10). 필요하면 몸통 안에 직접 잠근다(문서).

## 구현 세부사항 대 언어 보장

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **라이브러리 보장** | `functools` 문서·FAQ·What's New 가 정한 것 | 문서 문장을 열어서 인용 |
| **CPython 구현** | 키를 만드는 방식 · `partial` 펴기 · 예외 문구 | 실행 · `functools._make_key` |
| **이 판(3.12.3 · 3.11.15)의 관찰** | 이 판에서 그랬을 뿐 | 출력 |
| ★ **부적용** | 시간·메모리 바이트 · 스레드 경쟁 | 재지 않았다 |

### 라이브러리 보장

| 사실 | 근거 |
|---|---|
| `lru_cache` 의 인자는 **해시돼야** 한다 | `lru_cache` 절 |
| 캐시는 **인자와 반환값을 참조**한다 — 밀려나거나 지워질 때까지 | `lru_cache` 절 · FAQ |
| 메서드면 **`self` 가 캐시에 들어간다** | `lru_cache` 절 |
| `typed=False` 여도 **`int`·`str` 은 따로 캐시될 수 있다** | `lru_cache` 절(괄호 안) |
| 키워드 순서가 다르면 **다른 칸일 수 있다** | `lru_cache` 절 |
| `cached_property` 는 **같은 이름의 속성이 없을 때만** 돈다 · `del` 로 지운다 · 3.12 에서 잠금 제거 | `cached_property` 절 |
| `singledispatch` 는 **첫 인자의 타입** · MRO · 유니온 등록 3.11 | `singledispatch` 절 |
| `partial` 은 **읽기 전용 세 속성** · `__name__` 없음 | `partial` 객체 절 |
| `reduce` 는 **한 원소면 그 원소** | `reduce` 절 |
| 3.12 는 `__set_name__` 예외를 **`RuntimeError` 로 안 싼다** | What's New 3.12 |

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| **`int`·`str` 인자 하나는 그 값 자체가 키**, 나머지는 `_HashedSeq` | `functools._make_key` 실행(동작 3) |
| 실제 캐시는 **C 모듈 `_functools`** 의 `_lru_cache_wrapper` | `is` 비교(동작 3) |
| `partial(partial(f, …), …)` 를 **한 겹으로 편다** | `q.func is price`(동작 5) |
| `reduce` 가 **초깃값 `None` 과 「안 줌」을 구분** | 실행(동작 6) |
| 예외 **문구** 전부 — `unhashable type: …` · `reduce() of empty iterable …` · `Invalid annotation for 'x'. …` · `Cannot assign the same cached_property …` | 실행 |

### 이 판(3.12.3)의 관찰

- **몸통 실행 수 `21891` 대 `21`** · `CacheInfo(hits=18, misses=21, …)` — 알고리즘이 정하는 수라 판을 안 탈 것으로 보이지만 **이 판에서 센 것**이다.
- **`typed` 격자 `6 / 8 · 2 / 8`** — 문서는 「그럴 수 있다」까지만 말한다. 판이 오르면 **다시 돌릴 격자**다.
- **약한 참조의 `True`/`False`** — `gc.collect()` 를 부른 뒤의 값이다. CPython 은 참조 계수로 대부분 즉시 회수하지만 **이 문서는 매번 `gc.collect()` 를 불러** 판정을 굳혔다.
- 3.11 의 `RuntimeError` · `lock` 속성 — **3.11.15 에서 본 것**이다.

### 그래서 이렇게 적으면 틀린다

* ✗ 「`lru_cache` 가 함수를 N 배 빠르게 한다(재 봤다)」\
  ○ **시간은 재지 않았다.** 잰 것은 **몸통 실행 수**(21891 대 21)다.
* ✗ 「메서드에 `@lru_cache` 를 달면 인스턴스가 **영원히** 새다」\
  ○ **`maxsize` 가 차면 밀려나 회수된다.** 영원히는 `maxsize=None` 일 때만이다.
* ✗ 「`typed=False` 면 `1`·`1.0`·`True` 가 사전처럼 한 칸」\
  ○ 인자 하나일 때 **`1` 은 따로 논다**(칸 2). `1.0`·`True` 끼리는 한 칸.
* ✗ 「`reduce` 에 초깃값 `None` 을 주면 안 준 것과 같다」\
  ○ **다르다.** `None` 부터 접는다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 해시되는 인자 · 불변 반환 · 부작용 없음 | `lru_cache`(`maxsize` 를 정해서) | 칸 수가 곧 수명이다 |
| 인자 없는 비싼 계산 · 인스턴스마다 | `cached_property` | 인스턴스와 함께 사라진다 |
| 인자 있는 메서드 캐시 | `lru_cache` + **`maxsize` 를 작게** — 또는 인스턴스에 사전을 둔다 | 기본은 `self` 를 붙든다 |
| `__slots__` 클래스 | `property` 위에 `lru_cache`(문서의 대안) | `cached_property` 는 넣을 칸이 없다 |
| 인자 일부 고정 | `partial` | 만들 때 값을 잡는다 |
| 합·최대·모두 | `sum`·`max`·`all` | `reduce` 는 읽기 어렵다 |
| 중간값도 필요 | `itertools.accumulate` | 마지막 값이 `reduce` 와 같다 |
| 첫 인자 타입으로 나누기 | `singledispatch` | 둘째 인자로는 못 나눈다 |

## 핵심 문장

1. **캐시의 키는 인자 객체를 붙든다** — 메서드면 `self` 도. `del` 뒤에도 `True`, 밀려나거나 `cache_clear()` 뒤에 `False`.
2. **「영원히」가 아니라 「`maxsize` 가 허락하는 동안」** 이다 — `maxsize=None` 이면 그게 영원히가 된다.
3. **캐시의 「같은 호출」은 사전 규칙보다 좁다** — `typed=False` 에서도 `f(1)`·`f(1.0)` 은 칸 2(**6 / 8 · 2 / 8**).
4. **돌려준 값은 메모장의 원본이다** — 고치면 다음 호출이 고친 것을 받는다.
5. **`singledispatch` 는 첫 인자만, `cached_property` 는 인스턴스 칸에** — 시간·메모리 바이트는 한 번도 재지 않았다.

## 관련 자료

* 선행: [24-decorators](../24-decorators/2-summary.md) — ★★★ **경계**: `@` 의 의미와 `functools.wraps` 가 **옮기는 칸·안 옮기는 칸**(일곱 칸 대조)은 그쪽이 정본. 여기는 **`lru_cache` 가 그 `wraps` 를 쓴 결과**(`__name__` · `__wrapped__`)만 인용했다.
* 선행: [30-repr-eq-hash-contracts](../30-repr-eq-hash-contracts/2-summary.md) — `unhashable type` 과 해시 계약. **경계**: 계약은 그쪽, 여기는 **그 계약이 캐시 키에서 드러나는 자리**.
* 선행: [12-dict-and-key-requirements](../12-dict-and-key-requirements/2-summary.md) — `1`·`1.0`·`True` 한 칸. ★ **이 주제의 캐시는 그 규칙보다 좁다**(동작 3).
* 선행: [33-property-descriptor-slots](../33-property-descriptor-slots/2-summary.md) — ★ **경계**: `cached_property` 가 비데이터라는 것·`vars` 에 들어가는 것·`__slots__` 의 `TypeError` 는 그쪽 「더 들어가면」이 쟀다. 여기는 **`del`·대입·원본 변경·두 이름·판**부터.
* 선행: [40-type-hints-at-runtime](../40-type-hints-at-runtime/2-summary.md) — `singledispatch` 가 어노테이션을 읽어 **`__future__` 에서 `NameError`**(지역 클래스) — 그 격자가 정본.
* 선행: [23-lambda-and-higher-order-functions](../23-lambda-and-higher-order-functions/2-summary.md) — `reduce` 의 **접는 순서**. 여기는 빈 입력·한 원소·`None` 초깃값.
* 이웃: [44-itertools](../44-itertools/2-summary.md) — `accumulate`(동작 6 의 `[2]`). [22-closures-and-late-binding](../22-closures-and-late-binding/2-summary.md) — `partial` 이 늦은 바인딩을 피하는 것(동작 5 의 `[4]`).
* 이웃: [10-list-methods-and-sort-key](../10-list-methods-and-sort-key/2-summary.md) · [31-comparison-protocol-and-sortability](../31-comparison-protocol-and-sortability/2-summary.md) — `cmp_to_key` 를 쓰는 자리.
* 공식 문서: [`functools`(3.12)](https://docs.python.org/3.12/library/functools.html) · [FAQ — How do I cache method calls?](https://docs.python.org/3.12/faq/programming.html#faq-cache-method-calls) · [What's New 3.12](https://docs.python.org/3.12/whatsnew/3.12.html)

## 용어 풀이

* **메모이제이션(memoization)**: 같은 인자의 답을 적어 두고 다시 계산하지 않는 것.\
  예: `fib(20)` 몸통 실행 21891 번이 21 번이 된다.
* **LRU**: 가장 오래 안 쓴 칸부터 버리는 방식.\
  예: `maxsize=2` 에 셋째 키가 오면 가장 오래 안 쓴 칸이 나간다.
* **`cache_info()`**: `hits`·`misses`·`maxsize`·`currsize` 넷을 담은 이름 있는 튜플.\
  예: 실패한 호출(`TypeError`)은 어느 쪽에도 안 센다.
* **캐시 키**: 인자로 만든 사전 키. **인자 객체를 붙든다.**\
  예: CPython 은 `int`·`str` 인자 하나면 그 값 자체를 키로 쓴다.
* **`typed`**: 참이면 인자의 **타입이 다를 때** 칸을 나눈다. 인자 **안쪽**은 안 본다.\
  예: `f(('k', D(42)))`·`f(('k', F(42)))` 는 `typed=True` 여도 한 칸.
* **약한 참조(weak reference)**: 객체를 **살려 두지 않고** 가리키는 참조. 객체가 사라지면 `None` 을 준다.\
  예: `weakref.ref(t)()` 가 `None` 이 아니면 누군가 `t` 를 붙들고 있다.
* **`partial` 객체**: `func`·`args`·`keywords` 세 칸을 가진 호출 가능 객체. 함수가 아니라 `__name__` 이 없다.\
  예: `partial(price, 1000)` 은 `price(1000, …)` 을 부르는 새 객체.
* **`reduce`**: 두 인자 함수로 줄을 왼쪽부터 접어 값 하나를 만든다.\
  예: 빈 줄 + 초깃값 없음은 `TypeError`.
* **`singledispatch`**: 첫 인자의 타입으로 구현을 고르는 제네릭 함수.\
  예: 등록 안 된 `bool` 은 MRO 를 따라 `int` 구현으로 간다.
* **`registry`**: `singledispatch` 의 `타입 -> 구현` 표. 읽기 전용 `mappingproxy`.
* **`cached_property`**: 처음 읽을 때 계산해 **인스턴스 `__dict__`** 에 적어 두는 비데이터 디스크립터.\
  예: `del o.total` 이면 다음 읽기에서 다시 계산한다.
* **`cmp_to_key`**: `cmp(a, b)` 꼴 함수를 정렬 키로 바꾼다. 돌려주는 `KeyWrapper` 는 해시가 안 된다.

## 더 들어가면

* ★ **`lru_cache` 의 스레드 안전** — 문서는 *"The cache is threadsafe"* 라 적되 *"It is possible for the wrapped function to be called more than once if another thread makes an additional call before the initial call has been completed and cached."* 라고 덧붙인다. **스레드 경쟁은 이 문서가 재지 않았다**(목록의 **53번 주제**).
* ★ **메서드 캐시를 인스턴스에 두는 법** — FAQ 는 `station_id` 가 바뀌는 경우 `__eq__`·`__hash__` 를 정의해 캐시가 변경을 알아채게 하는 예를 싣는다. 해시 계약은 [30번](../30-repr-eq-hash-contracts/2-summary.md)이 정본이다.
* ★ **`singledispatchmethod`**(3.8) — 메서드판. 첫 인자가 아니라 **`self`·`cls` 다음 인자**의 타입으로 고른다(문서). 이 문서는 재지 않았다.
* ★ **`total_ordering`** — 비교 메서드 하나로 나머지를 채운다. [31번](../31-comparison-protocol-and-sortability/2-summary.md)의 몫이다.
