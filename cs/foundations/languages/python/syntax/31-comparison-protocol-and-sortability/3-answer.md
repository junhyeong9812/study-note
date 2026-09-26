# python/syntax/31-comparison-protocol-and-sortability — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> [1-question.md](1-question.md)의 번호와 **1:1**로 대응한다. 질문 12개 = 답 12개.
>
> 이 파일의 모든 출력은 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> 던지는 형태는 `python3 - <파일` 로 고정했다.
> ★ **이 파일에는 트레이스백이 한 줄도 없다** — 예외를 전부 `except` 로 받아 한 줄로 찍었기 때문이다.
> 그래서 블록에 주소도 시간도 절대경로도 안 들어간다. 같은 판에서 다시 돌리면 **한 글자도 안 변한다.**
> ★★ 단 **호출 횟수**는 TimSort 의 성질이고, **예외 문구**는 판에 달린 것이다(12번 답).
> ★ `DeprecationWarning` 은 `warnings.catch_warnings` 로 **잡아서 표준 출력에 찍었다** —
> 그냥 두면 표준 오류로 새서 파이프에서 맨 앞으로 몰린다.

## 정답

### 1. `sorted` 는 `__lt__` 만 묻고, `<=` 는 `TypeError`, `>` 는 반사 연산으로 돈다

**출력**

```python
# e31_lt_only.py
class V:
    def __init__(self, n):
        self.n = n

    def __repr__(self):
        return "V(%d)" % self.n

    def __lt__(self, other):
        print("      __lt__  %d < %d" % (self.n, other.n))
        return self.n < other.n


data = [V(3), V(1), V(2)]
print("① 정의된 비교 메서드 :", [m for m in ("__lt__", "__le__", "__gt__", "__ge__", "__eq__") if m in V.__dict__])
print("② sorted 를 부른다 — 아래가 호출 로그다")
out = sorted(data)
print("   결과 :", out)
print("③ 세 원소를 정렬하는 데 __lt__ 가 몇 번 불렸나 : 위 줄을 세어라")
print("④ 다른 비교는 어떻게 되나")
for expr, fn in (("V(1) <= V(2)", lambda: V(1) <= V(2)),
                 ("V(1) > V(2)", lambda: V(1) > V(2)),
                 ("V(1) == V(2)", lambda: V(1) == V(2))):
    try:
        print("   %-13s ->" % expr, fn())
    except TypeError as ex:
        print("   %-13s -> TypeError:" % expr, ex)
```

```text
===== python3 - <e31_lt_only.py =====
① 정의된 비교 메서드 : ['__lt__']
② sorted 를 부른다 — 아래가 호출 로그다
      __lt__  1 < 3
      __lt__  2 < 1
      __lt__  2 < 3
      __lt__  2 < 1
   결과 : [V(1), V(2), V(3)]
③ 세 원소를 정렬하는 데 __lt__ 가 몇 번 불렸나 : 위 줄을 세어라
④ 다른 비교는 어떻게 되나
   V(1) <= V(2)  -> TypeError: '<=' not supported between instances of 'V' and 'V'
      __lt__  2 < 1
   V(1) > V(2)   -> False
   V(1) == V(2)  -> False
(exit 0)
```

**왜 그런가**

- ① **정의된 것은 `__lt__` 하나뿐**이다. 나머지 넷은 클래스 칸에 없다.
- ② **로그에 `__lt__` 말고는 아무것도 없다.** Sorting HOWTO 가 적은 그대로다 —
  *"The sort routines use `<` when comparing two objects."*
- ③ 네 줄이 찍혔지만 **그 숫자는 답이 아니다.** TimSort 가 정하는 것이라 판이 오르면 달라진다.
  답은 「**`__lt__` 만 찍혔다**」이다.
- ★★ ④ 가 이 문항의 과녁이고 셋이 각각 다르게 끝난다.

| 식 | 결과 | 로그 | 왜 |
|---|---|---|---|
| `` V(1) <= V(2) `` | `TypeError` | 없음 | `__le__` 의 반사 짝은 `__ge__` 다. `__lt__` 로는 안 생긴다 |
| `` V(1) > V(2) `` | `False` | `` __lt__  2 < 1 `` | **반사 연산** — `` V(2).__lt__(V(1)) `` 이 불렸다 |
| `` V(1) == V(2) `` | `False` | 없음 | `__eq__` 를 안 썼으니 `object` 의 **정체 비교**다 |

- ★ **`>` 는 메서드가 생겨서 되는 것이 아니다.** 로그의 `2 < 1` 이 그 증거다 — **인자가 뒤집혀** 들어갔다(3번 답).
- ★ 예외 문구가 `'<=' not supported between instances of 'V' and 'V'` 로 **연산자와 두 타입 이름**을 다 적는다.

### 2. 정렬 루틴 셋은 `__lt__` 만, `max` 는 `__gt__` 를 쓴다

**출력**

```python
# e31_gt_ignored.py
class Both:
    def __init__(self, n):
        self.n = n

    def __repr__(self):
        return "Both(%d)" % self.n

    def __lt__(self, o):
        print("      __lt__  %d %d" % (self.n, o.n))
        return self.n < o.n

    def __gt__(self, o):
        print("      __gt__  %d %d" % (self.n, o.n))
        return self.n > o.n


def fresh():
    return [Both(3), Both(1), Both(2)]


print("① sorted")
print("   결과 :", sorted(fresh()))
print("② sorted(reverse=True) — 「큰 것부터」인데 무엇이 불리나")
print("   결과 :", sorted(fresh(), reverse=True))
print("③ list.sort 도 같나")
xs = fresh()
xs.sort()
print("   결과 :", xs)
print("④ max / min 은 다르다")
print("   max :", max(fresh()))
print("   min :", min(fresh()))
print("⑤ heapq 는?")
import heapq
h = fresh()
heapq.heapify(h)
print("   heappop :", heapq.heappop(h))
```

```text
===== python3 - <e31_gt_ignored.py =====
① sorted
      __lt__  1 3
      __lt__  2 1
      __lt__  2 3
      __lt__  2 1
   결과 : [Both(1), Both(2), Both(3)]
② sorted(reverse=True) — 「큰 것부터」인데 무엇이 불리나
      __lt__  1 2
      __lt__  3 1
      __lt__  3 2
   결과 : [Both(3), Both(2), Both(1)]
③ list.sort 도 같나
      __lt__  1 3
      __lt__  2 1
      __lt__  2 3
      __lt__  2 1
   결과 : [Both(1), Both(2), Both(3)]
④ max / min 은 다르다
      __gt__  1 3
      __gt__  2 3
   max : Both(3)
      __lt__  1 3
      __lt__  2 1
   min : Both(1)
⑤ heapq 는?
      __lt__  1 2
      __lt__  3 1
      __lt__  2 3
   heappop : Both(1)
(exit 0)
```

**왜 그런가**

- ① 과 ③ 의 로그는 **한 글자도 같다.** `sorted` 와 `list.sort` 는 같은 루틴이고 돌려주는 것만 다르다.
- ★★ ② **`reverse=True` 도 `__lt__` 만 쓴다.** 「큰 것부터」라고 `__gt__` 로 갈아타지 않는다.
  ★ 그런데 **로그가 ① 과 다르다.**

| | 찍힌 줄 | 무엇을 물었나 |
|---|---|---|
| ① `sorted` | `1 3` · `2 1` · `2 3` · `2 1` | 오름차순 기준의 비교 |
| ② `reverse=True` | `1 2` · `3 1` · `3 2` | **뒤집힌 기준의 비교** |

  **비교 자체가 다르다** — 그래서 `reverse=True` 는 「정렬한 뒤 뒤집기」가 **아니다**(7번 답).
- ★★ ④ **`max` 는 `__gt__` 를, `min` 은 `__lt__` 를 부른다.**
  「파이썬은 늘 `__lt__` 만 쓴다」는 **틀린 외움**이다. 맞는 문장은 「**정렬 루틴**이 `<` 를 쓴다」이다.
  ★ 문서는 `max` 가 어느 연산자를 쓰는지 **안 적는다** — 이 줄은 **CPython 구현**이다(12번 답).
- ⑤ **`heapq` 도 `__lt__` 만 쓴다.** 그래서 `__lt__` 하나짜리 객체가 힙에 그대로 들어간다.

### 3. 없으면 상대의 짝을 인자를 뒤집어 부르고, 하위 클래스가 먼저다

**출력**

```python
# e31_reflected.py
class NoLt:
    def __init__(self, n):
        self.n = n

    def __repr__(self):
        return "NoLt(%d)" % self.n

    def __gt__(self, o):
        print("      NoLt.__gt__ 가 불렸다 : self=%d other=%d" % (self.n, o.n))
        return self.n > o.n


class OnlyLt:
    def __init__(self, n):
        self.n = n

    def __repr__(self):
        return "OnlyLt(%d)" % self.n

    def __lt__(self, o):
        print("      OnlyLt.__lt__ 가 불렸다 : self=%d other=%d" % (self.n, o.n))
        return self.n < o.n


print("① NoLt(1) < NoLt(2) — 왼쪽에 __lt__ 가 없다")
print("   결과 :", NoLt(1) < NoLt(2))
print("② OnlyLt(1) > OnlyLt(2) — 왼쪽에 __gt__ 가 없다")
print("   결과 :", OnlyLt(1) > OnlyLt(2))
print("③ 둘 다 없으면")


class Bare:
    def __init__(self, n):
        self.n = n


try:
    Bare(1) < Bare(2)
except TypeError as ex:
    print("   TypeError:", ex)

print("④ 오른쪽이 왼쪽의 하위 클래스면 오른쪽이 먼저 불린다")


class P:
    def __lt__(self, o):
        print("      P.__lt__")
        return True


class Q(P):
    def __gt__(self, o):
        print("      Q.__gt__  (하위 클래스가 먼저다)")
        return True


print("   P() < Q() ->", P() < Q())
print("   P() < P() ->", P() < P())
print("⑤ 반사 짝은 정해져 있다 : < ↔ > · <= ↔ >= · == ↔ == · != ↔ !=")
print("   NoLt(1) <= NoLt(2) 는?")
try:
    print("   ->", NoLt(1) <= NoLt(2))
except TypeError as ex:
    print("   TypeError:", ex)
```

```text
===== python3 - <e31_reflected.py =====
① NoLt(1) < NoLt(2) — 왼쪽에 __lt__ 가 없다
      NoLt.__gt__ 가 불렸다 : self=2 other=1
   결과 : True
② OnlyLt(1) > OnlyLt(2) — 왼쪽에 __gt__ 가 없다
      OnlyLt.__lt__ 가 불렸다 : self=2 other=1
   결과 : False
③ 둘 다 없으면
   TypeError: '<' not supported between instances of 'Bare' and 'Bare'
④ 오른쪽이 왼쪽의 하위 클래스면 오른쪽이 먼저 불린다
      Q.__gt__  (하위 클래스가 먼저다)
   P() < Q() -> True
      P.__lt__
   P() < P() -> True
⑤ 반사 짝은 정해져 있다 : < ↔ > · <= ↔ >= · == ↔ == · != ↔ !=
   NoLt(1) <= NoLt(2) 는?
   TypeError: '<=' not supported between instances of 'NoLt' and 'NoLt'
(exit 0)
```

**왜 그런가**

- ★ ① **`NoLt` 에는 `__gt__` 밖에 없는데 `<` 가 된다.**
  로그가 `self=2 other=1` 이다 — `` NoLt(1) < NoLt(2) `` 가 `` NoLt(2).__gt__(NoLt(1)) `` 로 갔다.
  **「1이 2보다 작은가」를 「2가 1보다 큰가」로 바꿔 물은 것**이고 답은 같다.
- ② 거꾸로도 같다. `` OnlyLt(1) > OnlyLt(2) `` 가 `` OnlyLt(2).__lt__(OnlyLt(1)) `` 로 가서 `False` 다.
- ③ 둘 다 없으면 `TypeError` 다. `object` 는 **순서 메서드를 하나도 안 준다.**
- ★ ④ **하위 클래스가 먼저다.** 문서의 문장 그대로다 —
  *"If the operands are of different types, and right operand's type is a direct or indirect subclass of the left operand's type,
  the reflected method of the right operand has priority."*
  `` P() < Q() `` 는 `Q.__gt__` 가, `` P() < P() `` 는 `P.__lt__` 가 불렸다.
  **이 규칙이 있어야 하위 클래스가 상위의 비교를 덮을 수 있다.**
- ★★ ⑤ **반사 짝은 건너뛰지 않는다.** `<=` 의 짝은 `>=` 이지 `>` 가 아니다.
  그래서 `` NoLt(1) <= NoLt(2) `` 는 `__gt__` 가 있어도 **`TypeError`** 다. 1번 답의 `V` 와 **같은 이유**다.

### 4. 채우는 것은 순서 셋뿐이고 `__hash__` 는 `None` 인 채로 남는다

**출력**

```python
# e31_total_ordering.py
import functools


class Before:
    def __init__(self, n):
        self.n = n

    def __repr__(self):
        return "Before(%d)" % self.n

    def __eq__(self, o):
        return isinstance(o, Before) and self.n == o.n

    def __lt__(self, o):
        return self.n < o.n


@functools.total_ordering
class After:
    def __init__(self, n):
        self.n = n

    def __repr__(self):
        return "After(%d)" % self.n

    def __eq__(self, o):
        return isinstance(o, After) and self.n == o.n

    def __lt__(self, o):
        return self.n < o.n


names = ("__lt__", "__le__", "__gt__", "__ge__", "__eq__", "__ne__", "__hash__")
print("① 클래스 칸에 무엇이 들어 있나")
print("   %-10s | %-12s | %s" % ("이름", "데코레이터 전", "후"))
for nm in names:
    print("   %-10s | %-12s | %s" % (nm, nm in Before.__dict__, nm in After.__dict__))

print()
print("② 채워진 것들의 정체 — 어느 함수가 들어갔나")
print("   ", [(nm, After.__dict__[nm].__name__) for nm in ("__le__", "__gt__", "__ge__")])

print()
print("③ 못 채우는 것 — __hash__")
print("   Before.__hash__ :", Before.__hash__)
print("   After.__hash__  :", After.__hash__)
try:
    {After(1): 0}
except TypeError as ex:
    print("   {After(1): 0} -> TypeError:", ex)

print()
print("④ 채운 것은 실제로 도나")
print("   After(1) <= After(1) :", After(1) <= After(1))
print("   After(2) >= After(1) :", After(2) >= After(1))
print("   Before(1) <= Before(1) 는?")
try:
    print("   ->", Before(1) <= Before(1))
except TypeError as ex:
    print("   TypeError:", ex)

print()
print("⑤ 무엇도 안 주면 데코레이터가 거부한다")
try:
    @functools.total_ordering
    class Nothing:
        pass
except ValueError as ex:
    print("   ", type(ex).__name__, ":", ex)

print()
print("⑥ __eq__ 가 없으면? — object 의 것(정체 기준)으로 그냥 돈다")


@functools.total_ordering
class NoEq:
    def __init__(self, n):
        self.n = n

    def __lt__(self, o):
        return self.n < o.n


print("   NoEq.__eq__ is object.__eq__ :", NoEq.__eq__ is object.__eq__)
print("   NoEq(1) <= NoEq(1) :", NoEq(1) <= NoEq(1))
print("   NoEq(1) == NoEq(1) :", NoEq(1) == NoEq(1))
```

```text
===== python3 - <e31_total_ordering.py =====
① 클래스 칸에 무엇이 들어 있나
   이름         | 데코레이터 전      | 후
   __lt__     | True         | True
   __le__     | False        | True
   __gt__     | False        | True
   __ge__     | False        | True
   __eq__     | True         | True
   __ne__     | False        | False
   __hash__   | True         | True

② 채워진 것들의 정체 — 어느 함수가 들어갔나
    [('__le__', '__le__'), ('__gt__', '__gt__'), ('__ge__', '__ge__')]

③ 못 채우는 것 — __hash__
   Before.__hash__ : None
   After.__hash__  : None
   {After(1): 0} -> TypeError: unhashable type: 'After'

④ 채운 것은 실제로 도나
   After(1) <= After(1) : True
   After(2) >= After(1) : True
   Before(1) <= Before(1) 는?
   TypeError: '<=' not supported between instances of 'Before' and 'Before'

⑤ 무엇도 안 주면 데코레이터가 거부한다
    ValueError : must define at least one ordering operation: < > <= >=

⑥ __eq__ 가 없으면? — object 의 것(정체 기준)으로 그냥 돈다
   NoEq.__eq__ is object.__eq__ : True
   NoEq(1) <= NoEq(1) : False
   NoEq(1) == NoEq(1) : False
(exit 0)
```

**왜 그런가**

- ① **`False` 에서 `True` 로 바뀐 줄은 셋**이다 — `__le__`·`__gt__`·`__ge__`.

| 이름 | 전 | 후 | 누가 채웠나 |
|---|---|---|---|
| `__lt__` | 있음 | 있음 | 내가 썼다 |
| `__le__` · `__gt__` · `__ge__` | 없음 | **있음** | ★ 데코레이터 |
| `__eq__` | 있음 | 있음 | 내가 썼다 |
| `__ne__` | 없음 | **없음** | ★ `object` 가 `__eq__` 를 뒤집어 준다 |
| `__hash__` | 있음(**값은 `None`**) | 있음(**값은 `None`**) | ★ 아무도 안 채운다 |

- ★ **`__ne__` 를 왜 안 채우나** — 채울 필요가 없다. `object.__ne__` 가 `__eq__` 의 결과를 뒤집는다.
- ★ ② 채워진 셋의 함수 이름이 각각 `__le__`·`__gt__`·`__ge__` 다. 데코레이터가 그 이름을 붙여 넣었다.
- ★★★ ③ **`` {After(1): 0} `` 은 안 된다.** `TypeError: unhashable type: 'After'` 다.
  **`__eq__` 를 정의하면 `__hash__` 가 `None` 으로 꺼지고**([30번](../30-repr-eq-hash-contracts/2-summary.md)),
  `total_ordering` 은 **그 칸을 건드리지 않는다.**
  ★ 그래서 나오는 물건이 「**정렬은 되는데 `set`·`dict` 에는 못 넣는 객체**」다(11번 답).
- ④ 채운 것은 실제로 돈다. **안 붙인 `Before` 는 `<=` 에서 `TypeError`** 다.
- ⑤ 순서 연산을 하나도 안 주면 **클래스를 만드는 순간** `ValueError: must define at least one ordering operation: < > <= >=` 다.
  ★ 이 주제에서 **유일하게 일찍 잡히는 계약 위반**이다.
- ★★ ⑥ **`` NoEq(1) <= NoEq(1) `` 은 `False`** 다.
  문서의 낱말이 `must` 가 아니라 `should` 라 `__eq__` 없이도 통과하는데,
  그러면 `object.__eq__` 즉 **정체 비교**로 돈다.
  데코레이터가 만든 `__le__` 는 `a < b or a == b` 꼴이고, **두 `NoEq(1)` 은 딴 객체**라 둘 다 거짓이다.
  ★ **같은 객체 하나로 `x <= x` 를 물으면 참**이다 — 정체가 같으니 `==` 가 참이기 때문이다.
  결과는 **반사성이 깨진 순서**이고 아무도 안 알려 준다.

### 5. `NotImplemented` 는 반사 연산을 거쳐 `TypeError` 가 되고, 진릿값으로는 참이다

**출력**

```python
# e31_notimplemented.py
import warnings


class Strict:
    def __init__(self, n):
        self.n = n

    def __repr__(self):
        return "Strict(%d)" % self.n

    def __lt__(self, o):
        print("      Strict.__lt__ 가 불렸다. 상대의 타입 :", type(o).__name__)
        if not isinstance(o, Strict):
            return NotImplemented
        return self.n < o.n


print("① 같은 타입끼리")
print("   Strict(1) < Strict(2) ->", Strict(1) < Strict(2))
print("② 다른 타입과 — 돌려준 NotImplemented 가 무엇이 되나")
try:
    Strict(1) < 2
except TypeError as ex:
    print("   TypeError:", ex)
print("③ 메서드를 직접 부르면 그 값이 그대로 나온다")
r = Strict.__lt__(Strict(1), 2)
print("   돌려받은 것 :", r, "| 타입 :", type(r).__name__)
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    b = bool(r)
print("   bool(NotImplemented) ->", b)
print("   그때 난 경고 :", [(x.category.__name__, str(x.message)) for x in w])
print("④ 정렬 안에서 나면")
try:
    sorted([Strict(1), 2])
except TypeError as ex:
    print("   TypeError:", ex)
print("⑤ NotImplemented 를 「안 된다」는 뜻의 False 로 쓰면 조용히 틀린다")
with warnings.catch_warnings(record=True) as w2:
    warnings.simplefilter("always")
    verdict = "참" if Strict.__lt__(Strict(1), 2) else "거짓"
print("   if 로 쓰면 이렇게 읽힌다 :", verdict)
print("   그때 난 경고 :", [(x.category.__name__, str(x.message)) for x in w2])
```

```text
===== python3 - <e31_notimplemented.py =====
① 같은 타입끼리
      Strict.__lt__ 가 불렸다. 상대의 타입 : Strict
   Strict(1) < Strict(2) -> True
② 다른 타입과 — 돌려준 NotImplemented 가 무엇이 되나
      Strict.__lt__ 가 불렸다. 상대의 타입 : int
   TypeError: '<' not supported between instances of 'Strict' and 'int'
③ 메서드를 직접 부르면 그 값이 그대로 나온다
      Strict.__lt__ 가 불렸다. 상대의 타입 : int
   돌려받은 것 : NotImplemented | 타입 : NotImplementedType
   bool(NotImplemented) -> True
   그때 난 경고 : [('DeprecationWarning', 'NotImplemented should not be used in a boolean context')]
④ 정렬 안에서 나면
   TypeError: '<' not supported between instances of 'int' and 'Strict'
⑤ NotImplemented 를 「안 된다」는 뜻의 False 로 쓰면 조용히 틀린다
      Strict.__lt__ 가 불렸다. 상대의 타입 : int
   if 로 쓰면 이렇게 읽힌다 : 참
   그때 난 경고 : [('DeprecationWarning', 'NotImplemented should not be used in a boolean context')]
(exit 0)
```

**왜 그런가**

- ★★ ② **`__lt__` 는 불렸다.** 로그에 `상대의 타입 : int` 가 찍혀 있다.
  언어가 그 반환값을 보고 **`int` 에게 반사 연산을 시도했고**, `int` 도 `Strict` 를 모르니 **`TypeError` 로 바꿨다.**
  ★ 예외 문구는 내 메서드 이야기를 **한 마디도 안 한다** — `'<' not supported between instances of 'Strict' and 'int'` 뿐이다.
- ★ ③ 메서드를 직접 부르면 **`NotImplemented` 가 그대로** 나오고 타입 이름은 `NotImplementedType` 이다.
  그리고 **`` bool(NotImplemented) `` 은 `True`** 이며 `DeprecationWarning` 이 따라온다 —
  `NotImplemented should not be used in a boolean context`.
  문서가 *"It will raise a `TypeError` in a future version of Python"* 이라고 적었으니 **언젠가 예외가 된다.**
- ★ ④ **두 타입 이름이 뒤바뀌어** 나온다 — `'int' and 'Strict'`.
  `` sorted([Strict(1), 2]) `` 에서 TimSort 가 `` 2 < Strict(1) `` 쪽을 물었기 때문이다.
  **왼쪽이 누구인지는 정렬 루틴이 정한다.**
- ★★★ ⑤ 가 가장 나쁜 자리다. `NotImplemented` 를 **「안 된다」는 뜻의 거짓으로 읽으면 조용히 틀린다** —
  `if` 는 **참**으로 읽는다. 경고는 나지만 **기본 설정에서는 안 보인다.**
- ★ 그래서 `__lt__` 가 모르는 타입을 만나면 **`False` 가 아니라 `NotImplemented` 를 돌려줘야 한다.**
  `False` 를 돌려주면 반사 연산의 길이 막히고 `a < b` 와 `b > a` 가 **둘 다 거짓**이 되는 비대칭이 생긴다.

### 6. `key` 를 주면 원소의 `__lt__` 는 한 번도 안 불린다

**출력**

```python
# e31_key_vs_lt.py
class Loud:
    def __init__(self, n):
        self.n = n

    def __repr__(self):
        return "Loud(%d)" % self.n

    def __lt__(self, o):
        print("      Loud.__lt__ 가 불렸다")
        return self.n < o.n


def fresh():
    return [Loud(3), Loud(1), Loud(2)]


print("① key 없이")
print("   결과 :", sorted(fresh()))
print("② key= 로 정수를 뽑아 쓰면")
print("   결과 :", sorted(fresh(), key=lambda x: x.n))
print("③ key 가 돌려준 것의 __lt__ 가 쓰인다 — key 를 -n 으로")
print("   결과 :", sorted(fresh(), key=lambda x: -x.n))
print("④ key 는 원소마다 정확히 한 번 불린다")
calls = []


def k(x):
    calls.append(x.n)
    return x.n


sorted(fresh(), key=k)
print("   key 가 불린 횟수 :", len(calls), "| 불린 순서 :", calls)
print("⑤ key 를 쓰면 원소의 __lt__ 는 아예 안 쓰이므로, 비교 불가 타입도 정렬된다")


class NoCompare:
    def __init__(self, n):
        self.n = n

    def __repr__(self):
        return "NoCompare(%d)" % self.n


try:
    sorted([NoCompare(2), NoCompare(1)])
except TypeError as ex:
    print("   key 없이 -> TypeError:", ex)
print("   key 로   ->", sorted([NoCompare(2), NoCompare(1)], key=lambda x: x.n))
```

```text
===== python3 - <e31_key_vs_lt.py =====
① key 없이
      Loud.__lt__ 가 불렸다
      Loud.__lt__ 가 불렸다
      Loud.__lt__ 가 불렸다
      Loud.__lt__ 가 불렸다
   결과 : [Loud(1), Loud(2), Loud(3)]
② key= 로 정수를 뽑아 쓰면
   결과 : [Loud(1), Loud(2), Loud(3)]
③ key 가 돌려준 것의 __lt__ 가 쓰인다 — key 를 -n 으로
   결과 : [Loud(3), Loud(2), Loud(1)]
④ key 는 원소마다 정확히 한 번 불린다
   key 가 불린 횟수 : 3 | 불린 순서 : [3, 1, 2]
⑤ key 를 쓰면 원소의 __lt__ 는 아예 안 쓰이므로, 비교 불가 타입도 정렬된다
   key 없이 -> TypeError: '<' not supported between instances of 'NoCompare' and 'NoCompare'
   key 로   -> [NoCompare(1), NoCompare(2)]
(exit 0)
```

**왜 그런가**

- ① `key` 없이는 `Loud.__lt__` 가 네 줄 찍힌다.
- ★★ ② **`key` 를 주자 로그가 통째로 비었다.** 비교는 `key` 가 돌려준 `int` 끼리 한 것이다.
  **원소의 비교 메서드는 정렬에 아무 상관이 없어진다.**
- ③ 이름표를 `-n` 으로 만들면 내림차순이 된다. **비교되는 것은 어디까지나 이름표**이고 돌려주는 것은 원소다.
- ★ ④ **`key` 는 세 번, 원본 순서대로** 불렸다 — `[3, 1, 2]`.
  「원소당 정확히 한 번」은 **문서가 약속한 보장**이고 정본은 [10번](../10-list-methods-and-sort-key/2-summary.md)이다.
- ★★ ⑤ **비교 메서드가 아예 없는 타입도 `key` 로는 정렬된다.**
  `key` 없이는 `TypeError: '<' not supported between instances of 'NoCompare' and 'NoCompare'` 인데
  `key` 를 주면 그냥 선다.
  **「이 객체는 정렬 가능한가」라는 질문 자체가 `key` 앞에서는 의미가 없다.**

### 7. 둘은 다르다 — `reverse=True` 는 동점 무리를 안 뒤집는다

**출력**

```python
# e31_stable.py
rows = [("b", 1), ("a", 2), ("c", 1), ("a", 1), ("b", 2)]
print("원래 순서 :", rows)
by_num = sorted(rows, key=lambda r: r[1])
print("두 번째 칸으로만 정렬 :", by_num)

print()
print("① 같은 키끼리 원래 순서가 유지되나")
for k in (1, 2):
    print("   키 %d : 원래 %s -> 정렬 후 %s"
          % (k, [r[0] for r in rows if r[1] == k], [r[0] for r in by_num if r[1] == k]))

print()
print("② 안정성을 쓰면 다중 기준 정렬이 두 번의 정렬이 된다 (뒤 기준부터)")
tmp = sorted(rows, key=lambda r: r[0])
print("   ① 이름으로     :", tmp)
print("   ② 그 다음 수로 :", sorted(tmp, key=lambda r: r[1]))
print("   한 번에 튜플로  :", sorted(rows, key=lambda r: (r[1], r[0])))

print()
print("③ reverse=True 도 안정적이다 — 같은 키끼리 뒤집히지 않는다")
rev = sorted(rows, key=lambda r: r[1], reverse=True)
print("   결과 :", rev)
for k in (2, 1):
    print("   키 %d : 원래 %s -> 정렬 후 %s"
          % (k, [r[0] for r in rows if r[1] == k], [r[0] for r in rev if r[1] == k]))
print("   reversed(sorted(...)) 와 같은가 :", rev == list(reversed(by_num)))
```

```text
===== python3 - <e31_stable.py =====
원래 순서 : [('b', 1), ('a', 2), ('c', 1), ('a', 1), ('b', 2)]
두 번째 칸으로만 정렬 : [('b', 1), ('c', 1), ('a', 1), ('a', 2), ('b', 2)]

① 같은 키끼리 원래 순서가 유지되나
   키 1 : 원래 ['b', 'c', 'a'] -> 정렬 후 ['b', 'c', 'a']
   키 2 : 원래 ['a', 'b'] -> 정렬 후 ['a', 'b']

② 안정성을 쓰면 다중 기준 정렬이 두 번의 정렬이 된다 (뒤 기준부터)
   ① 이름으로     : [('a', 2), ('a', 1), ('b', 1), ('b', 2), ('c', 1)]
   ② 그 다음 수로 : [('a', 1), ('b', 1), ('c', 1), ('a', 2), ('b', 2)]
   한 번에 튜플로  : [('a', 1), ('b', 1), ('c', 1), ('a', 2), ('b', 2)]

③ reverse=True 도 안정적이다 — 같은 키끼리 뒤집히지 않는다
   결과 : [('a', 2), ('b', 2), ('b', 1), ('c', 1), ('a', 1)]
   키 2 : 원래 ['a', 'b'] -> 정렬 후 ['a', 'b']
   키 1 : 원래 ['b', 'c', 'a'] -> 정렬 후 ['b', 'c', 'a']
   reversed(sorted(...)) 와 같은가 : False
(exit 0)
```

**왜 그런가**

- ① **같은 키끼리 원래 순서가 그대로다.** 키 1 의 무리가 원래도 정렬 후에도 `['b', 'c', 'a']` 다.
  ★ 이것은 **문서가 약속한 보장**이지 TimSort 의 부수 효과가 아니다 —
  *"The `sort()` method is guaranteed to be stable."*
- ② 그 보장 덕에 **나눠 정렬**이 성립한다. 세부는 [10번](../10-list-methods-and-sort-key/2-summary.md)이 정본이다.
- ★★★ ③ 이 이 문항의 과녁이다. **`reverse=True` 도 안정적이다.**
  키 2 의 무리가 `['a', 'b']`, 키 1 이 `['b', 'c', 'a']` 로 **원래 순서 그대로**다.
- ★★ 그래서 마지막 줄이 **`False`** 다.

```text
   원본        b1   a2   c1   a1   b2

   sorted(key=수)          b1  c1  a1   a2  b2
   그것을 reversed()        b2  a2   a1  c1  b1      <- 동점 무리까지 뒤집힌다
   sorted(key=수, reverse)  a2  b2   b1  c1  a1      <- 동점 무리는 원래 순서

   ★ 동점이 없으면 둘이 같고, 동점이 있으면 갈린다.
```

- ★ 2번 답의 로그가 이것을 미리 설명해 두었다 — `reverse=True` 는 **비교 자체를 다르게 한다.**
  결과를 뒤집는 것이 아니므로 **동점 무리의 원래 순서가 살아남는다.**

### 8. 타입이 섞이면 `TypeError`, `nan` 이 섞이면 아무 일도 안 난다

**출력**

```python
# e31_uncomparable.py
print("① 정수와 문자열")
try:
    sorted([1, "a"])
except TypeError as ex:
    print("   TypeError:", ex)

print("② None 과 정수")
try:
    sorted([1, None])
except TypeError as ex:
    print("   TypeError:", ex)

print("③ == 는 되는데 < 는 안 된다")
print("   1 == 'a'        ->", 1 == "a")
print("   [1, 2] == (1, 2) ->", [1, 2] == (1, 2))
try:
    [1, 2] < (1, 2)
except TypeError as ex:
    print("   [1, 2] < (1, 2) -> TypeError:", ex)

print("④ bool 은 int 라 섞인다 :", sorted([True, 0, 2, False]))

print("⑤ nan 이 섞이면 — 예외 없이 틀린 답이 나온다")
nan = float("nan")
print("   nan < 1.0 :", nan < 1.0, "| nan > 1.0 :", nan > 1.0, "| nan == nan :", nan == nan)
print("   sorted([3.0, 1.0, nan, 2.0]) :", sorted([3.0, 1.0, nan, 2.0]))
print("   sorted([nan, 3.0, 1.0, 2.0]) :", sorted([nan, 3.0, 1.0, 2.0]))
print("   정렬됐는지 검사하면 :", all(a <= b for a, b in zip(sorted([3.0, 1.0, nan, 2.0]),
                                                        sorted([3.0, 1.0, nan, 2.0])[1:])))
print("   nan in [nan] :", nan in [nan], "  (정체 지름길)")
```

```text
===== python3 - <e31_uncomparable.py =====
① 정수와 문자열
   TypeError: '<' not supported between instances of 'str' and 'int'
② None 과 정수
   TypeError: '<' not supported between instances of 'NoneType' and 'int'
③ == 는 되는데 < 는 안 된다
   1 == 'a'        -> False
   [1, 2] == (1, 2) -> False
   [1, 2] < (1, 2) -> TypeError: '<' not supported between instances of 'list' and 'tuple'
④ bool 은 int 라 섞인다 : [0, False, True, 2]
⑤ nan 이 섞이면 — 예외 없이 틀린 답이 나온다
   nan < 1.0 : False | nan > 1.0 : False | nan == nan : False
   sorted([3.0, 1.0, nan, 2.0]) : [1.0, 2.0, 3.0, nan]
   sorted([nan, 3.0, 1.0, 2.0]) : [nan, 1.0, 2.0, 3.0]
   정렬됐는지 검사하면 : False
   nan in [nan] : True   (정체 지름길)
(exit 0)
```

**왜 그런가**

- ① ② **타입이 섞이면 예외**다. 문구가 **어느 두 타입인지** 적어 준다.
  ★ `` sorted([1, "a"]) `` 의 문구가 `'str' and 'int'` 로 **`str` 이 왼쪽**인 것에 주의하라 —
  TimSort 가 `` "a" < 1 `` 쪽을 물었기 때문이고 5번 답 ④ 와 같은 자리다.
- ★ ③ **`==` 는 되는데 `<` 는 안 된다.** `1 == 'a'` 도 `` [1, 2] == (1, 2) `` 도 조용히 `False` 다.
  같음은 「**모르면 거짓**」, 순서는 「**모르면 예외**」다. 이 비대칭이 이 주제에서 가장 자주 사람을 놓친다.
- ④ **`bool` 은 `int` 의 하위 타입**이라 섞인다. `[0, False, True, 2]` 에서 `0` 이 `False` 보다 앞인 것은
  둘이 동점이고 원본 순서가 그렇기 때문이다 — 7번 답의 안정성이다([02번](../02-is-vs-eq-interning/2-summary.md)).
- ★★★ ⑤ 가 이 주제의 네 번째 창이 잡아내는 자리다.
  `nan` 은 `<`·`>`·`==` **셋 다 거짓**이라 **전순서가 아니다.**
  그런데 `sorted` 는 **예외를 안 던진다** — 입력 순서만 바꿨는데 `nan` 이 다른 자리에 놓인다.
  그리고 `` all(a <= b …) `` 검사가 **`False`** 다. **스스로 정렬됐다고 주장하지도 못하는 결과**를 돌려준 것이다.

```text
   세 언어가 같은 결함을 어디서 잡나

   Rust    v.sort()  ->  컴파일 실패      the trait bound `f64: Ord` is not satisfied
   Java    List.sort ->  원소가 많으면 예외  IllegalArgumentException: ... violates its general contract!
   Python  sorted()  ->  아무 일도 안 난다   안 정렬된 리스트를 돌려준다

   ★ 계약을 어기면 컴파일러가 아니라 "자료구조가 조용히 틀린다" — 그것이 이 갈래의 얼굴이다.
```

- ★ 세부는 [Rust 28번](../../../rust/syntax/28-partialeq-eq-partialord-ord-and-hash-contracts/2-summary.md)과
  [Java 28번](../../../java/syntax/28-comparable-comparator/2-summary.md)이 정본이다.

**★★ 그러면 원소가 많아지면 파이썬도 던지나 — 같은 축으로 한 번 더 던졌다**

```python
# e31_no_check.py
import random


class Shaky:
    """비일관 비교 — 자기가 흔들린다. Java 갈래 28편이 같은 실험으로 예외를 받았다."""

    def __init__(self, n):
        self.n = n

    def __repr__(self):
        return "Shaky(%d)" % self.n

    def __lt__(self, other):
        return random.random() < 0.5          # ★ 물을 때마다 답이 달라진다


def sorted_properly(xs):
    return all(not (b < a) for a, b in zip(xs, xs[1:]))


for n in (10, 100, 2000, 10000, 100000):
    random.seed(0)                            # 같은 수열을 쓰도록 고정한다
    data = [Shaky(i) for i in range(n)]
    try:
        out = sorted(data)
        print("n=%-7d 예외 없음 | 길이 %-7d | 정말 정렬됐나 %s"
              % (n, len(out), sorted_properly(out)))
    except Exception as ex:
        print("n=%-7d %s: %s" % (n, type(ex).__name__, ex))

print()
print("비교가 아예 예외를 던지면? — 그때는 그 예외가 그대로 나간다")


class Boom:
    def __lt__(self, other):
        raise RuntimeError("비교 중에 터졌다")


try:
    sorted([Boom(), Boom()])
except Exception as ex:
    print("  ", type(ex).__name__, ":", ex)

print()
print("리스트는 어떤 상태로 남나 — 예외가 난 sort 뒤의 원본")
xs = [Boom(), Boom(), Boom()]
try:
    xs.sort()
except RuntimeError:
    pass
print("   길이 :", len(xs), "| 전부 Boom 인가 :", all(isinstance(v, Boom) for v in xs))
```

```text
===== python3 - <e31_no_check.py =====
n=10      예외 없음 | 길이 10      | 정말 정렬됐나 False
n=100     예외 없음 | 길이 100     | 정말 정렬됐나 False
n=2000    예외 없음 | 길이 2000    | 정말 정렬됐나 False
n=10000   예외 없음 | 길이 10000   | 정말 정렬됐나 False
n=100000  예외 없음 | 길이 100000  | 정말 정렬됐나 False

비교가 아예 예외를 던지면? — 그때는 그 예외가 그대로 나간다
   RuntimeError : 비교 중에 터졌다

리스트는 어떤 상태로 남나 — 예외가 난 sort 뒤의 원본
   길이 : 3 | 전부 Boom 인가 : True
(exit 0)
```

- ★★★ **10 · 100 · 2000 · 10000 · 100000 다섯 크기 전부 `예외 없음`** 이다.
  Java 는 **계약을 어긴 비교자**(추이성을 깬 것)에 **`n=2000` 부터**
  `IllegalArgumentException: Comparison method violates its general contract!` 를 던졌다
  ([Java 28번](../../../java/syntax/28-comparable-comparator/2-summary.md)).
  ★ **자의 모양이 서로 달라 「같은 입력에서 갈렸다」는 아니다** — 갈린 것은 「**검사하는 코드가 있느냐**」이고,
  파이썬은 Java 가 던지기 시작한 크기의 **50배까지 가도 조용하다.**
- ★★ **그런데 결과는 정말 안 정렬돼 있다** — `정말 정렬됐나 False` 가 다섯 줄 전부다.
  「예외가 없다」와 「답이 맞다」가 **같은 줄에서 갈린다.**
- ★ **길이는 보존된다**(`길이 100000`). 원소를 잃지도 만들지도 않으니 **개수 검사로는 절대 안 잡힌다.**
- ★★ **「검사를 안 한다」이지 「예외를 삼킨다」가 아니다** — `Boom` 의 `__lt__` 가 던진
  `RuntimeError: 비교 중에 터졌다` 가 **그대로 밖으로 나왔다.**
  정렬 루틴은 비교의 **결과를 안 볼 뿐** 예외는 안 건드린다.
- ★ 예외로 끝난 `sort` 뒤에도 **원본은 길이 3 · 전부 `Boom`** 으로 남는다. 잃는 원소는 없다(순서는 보장 안 된다).
- ★★★ **층을 조심해라** — 「검사하지 않는다」는 **언어 보장이 아니라 CPython 의 관찰**이다.
  문서는 검사 여부를 한 마디도 안 적는다. 「명세가 안 던진다고 보장한다」로 읽으면 틀린다.
- ★ 처방은 **자를 고치는 것**이다 — `` key=lambda x: (math.isnan(x), x) `` 처럼 `nan` 을 한쪽 끝으로 몬다.
  6번 답의 이름표가 그 자리다.
- ★ 마지막 줄의 `` nan in [nan] `` 이 `True` 인 것은 `==` 가 아니라 **정체를 먼저 보는 CPython 의 지름길** 때문이다.

### 9. 문서가 「정렬 루틴은 `<` 를 쓴다」고 적었기 때문이다

**왜 그런가**

- Sorting Techniques HOWTO 의 문장이 근거다 —
  *"The sort routines use `<` when comparing two objects.
  So, it is easy to add a standard sort order to a class by defining an `__lt__()` method."*
- ★ **줄을 세우는 데는 「둘 중 누가 앞이냐」 하나면 충분하다.**
  **전순서라면** `a <= b` 는 `` not (b < a) `` 로, `a > b` 는 `b < a` 로 전부 `<` 하나에서 유도된다
  (전순서가 아닌 `nan` 에서 그 유도가 깨지는 것이 8번 답이다).
  그래서 비교 기반 정렬은 **연산자 하나만 요구하는 것이 표준**이다.
- ★ 그런데 **언어가 그 유도를 자동으로 해 주지는 않는다.**
  `` V(1) <= V(2) `` 가 `TypeError` 인 것이 그 증거다(1번 답).
  **정렬 루틴이 `<` 만 쓰는 것**과 **`<=` 가 `<` 에서 만들어지는 것**은 다른 이야기다.
- ★★ 그리고 이 문장은 **정렬 루틴**에 대한 것이지 파이썬 전체에 대한 것이 아니다.
  `max` 는 `__gt__` 를 쓴다(2번 답).

### 10. 안 채우는 것은 `__eq__`·`__ne__`·`__hash__` 셋이고, 사고를 내는 것은 `__hash__` 다

**왜 그런가**

| 안 채우는 것 | 왜 | 결과 |
|---|---|---|
| `__eq__` | 내가 주기로 돼 있다(문서는 `should`) | 안 주면 **정체 비교**로 돌아 반사성이 깨진 순서가 된다(4번 답 ⑥) |
| `__ne__` | 채울 필요가 없다 | `object.__ne__` 가 `__eq__` 를 뒤집는다 — **문제 없음** |
| ★★ `__hash__` | **동등성 쪽 계약이라 순서 데코레이터의 몫이 아니다** | `__eq__` 를 쓴 순간 `None` 이라 **dict·set 에 못 들어간다** |

- ★★★ **버그로 이어지는 것은 `__hash__` 다.** 나머지 둘은 설계 의도이거나 무해하다.
- ★ 증상이 **엉뚱한 자리에서** 난다 — 정렬은 잘 되는데 **나중에 `set` 으로 중복을 없애려는 줄**에서 터진다.
  `TypeError: unhashable type: 'After'` 이고, 그 줄에는 `total_ordering` 이라는 낱말이 없다.
- ★ 고치는 길은 [30번](../30-repr-eq-hash-contracts/2-summary.md)이 정본이다 —
  `__hash__` 를 같이 정의하거나 `` __hash__ = object.__hash__ `` 로 되살린다.
  ★ **뒤엣것은 정체 기준이라 「값이 같으면 같은 키」가 되지 않는다.**

### 11. `__eq__` 와 순서를 쓰고 `__hash__` 를 안 쓴 클래스에서 나온다

**왜 그런가**

- 이런 코드가 그 얼굴이다 — `__eq__` 와 `__lt__` 를 쓰고 `@total_ordering` 을 붙인 클래스.
  **정렬·비교는 여섯 연산자가 다 돌고**, `` {obj: ...} `` 한 줄에서 `TypeError` 가 난다(4번 답 ③).
- ★ **원인은 30 과 31 이 다른 계약이기 때문**이다.

```text
   30 의 계약            31 의 계약
   "같음"                "순서"
   __eq__ / __hash__     __lt__ ... __ge__
      |                      |
      +--- __eq__ 가 겹친다 ---+
           여기서 __hash__ 가 꺼진다
           그런데 순서 쪽 도구는 그것을 안 되살린다
```

- ★★ **고치는 길 셋**
  1. `__hash__` 를 **값 기준으로** 직접 쓴다 — `` def __hash__(self): return hash(self.n) ``.
     ★ 그러면 **`__eq__` 가 보는 것과 `__hash__` 가 섞는 것을 같게** 맞춰야 한다([30번](../30-repr-eq-hash-contracts/2-summary.md)).
  2. `` __hash__ = object.__hash__ `` 로 되살린다 — **정체 기준**이라 값이 같아도 딴 키다. 뜻이 달라진다.
  3. `` @dataclass(frozen=True, order=True) `` 로 간다 — **순서 넷과 `__hash__` 를 함께** 만들어 준다.
     정본은 [목록의 **36번 주제**](../36-dataclasses/)다.
- ★ 거꾸로도 성립한다 — **`__hash__` 만 맞춰 놓고 순서를 안 쓰면** `set` 에는 들어가는데 `sorted` 에서 `TypeError` 다.
  **두 계약은 서로를 보장하지 않는다.**

### 12. 차례로 언어 보장 · CPython 구현 · 이 판의 관찰이다

**왜 그런가**

| 문장 | 층 | 근거 |
|---|---|---|
| 「`__lt__` 하나로 `sorted` 가 된다」 | **언어 보장** | Sorting HOWTO 가 *"The sort routines use `<`"* 라고 적는다 |
| 「`max` 가 `__gt__` 를 쓴다」 | **CPython 구현** | 문서에 없다. 호출 로그로만 본다(2번 답 ④) |
| 「세 원소에 `__lt__` 가 네 번 불린다」 | **이 판의 관찰** | TimSort 가 정하는 것이라 판이 오르면 달라진다 |
| ★ 「계약 위반을 검사하지 않는다」 | **CPython 구현 · 이 판의 관찰** | 문서가 검사 여부를 **한 마디도 안 적는다**(8번 답) |

★ 같은 층 나누기를 나머지에도 적용하면 이렇다.

- **언어 보장** — 반사 짝 · 하위 클래스 우선권 · `NotImplemented` 처리 · `object.__ne__` 가 `__eq__` 를 뒤집는 것 ·
  **안정 정렬** · **`key` 가 원소당 한 번** · `total_ordering` 의 요구 사항.
- **CPython 구현** — `max`·`min` 이 쓰는 연산자 · `heapq` 가 `__lt__` 만 쓰는 것 ·
  비교의 횟수와 순서 · `` nan in [nan] `` 이 참인 **정체 지름길** ·
  ★★ **비교 계약 위반을 검사하지 않는 것**(명세가 아무 말도 안 한 자리다).
- **이 판(3.12.3)의 관찰** — 예외 문구 전부 · `NotImplementedType` 이라는 타입 이름 ·
  경고 문구 · `` sorted([3.0, 1.0, nan, 2.0]) `` 이 `[1.0, 2.0, 3.0, nan]` 인 것(**입력 순서에 달린 한 판의 결과**).

★★ **가장 흔한 사고는 셋째를 첫째로 적는 것**이다.\
「세 원소면 네 번」을 성질로 적으면 판이 오를 때 통째로 틀리고, **호출 로그를 다시 찍기 전에는 아무도 모른다.**

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 판 확인 | `` python3 - <e31_version.py `` | 1 | 3.12.3 · cpython · linux |
| `__lt__` 하나로 정렬 · `<=`·`>`·`==` | `` python3 - <e31_lt_only.py `` | 2 | 두 판 한 글자도 같음 |
| `sorted`·`reverse`·`list.sort`·`max`·`min`·`heapq` | `` python3 - <e31_gt_ignored.py `` | 2 | 두 판 한 글자도 같음 |
| 반사 연산 · 하위 클래스 우선 | `` python3 - <e31_reflected.py `` | 2 | 두 판 한 글자도 같음 |
| `total_ordering` 의 `__dict__` 전후 | `` python3 - <e31_total_ordering.py `` | 2 | 두 판 한 글자도 같음 |
| `NotImplemented` 의 네 갈래 | `` python3 - <e31_notimplemented.py `` | 2 | 두 판 한 글자도 같음 |
| 안정성 · `reverse=True` 대 `[::-1]` | `` python3 - <e31_stable.py `` | 2 | 두 판 한 글자도 같음 |
| `key=` 와 `__lt__` | `` python3 - <e31_key_vs_lt.py `` | 2 | 두 판 한 글자도 같음 |
| 비교 불가 타입 · `nan` | `` python3 - <e31_uncomparable.py `` | 2 | 두 판 한 글자도 같음 |
| ★ 흔들리는 비교자를 10\~100000 개에 물리기 | `` python3 - <e31_no_check.py `` | 2 | 다섯 크기 전부 예외 없음 · `random.seed(0)` 으로 고정해 두 판 동일 |

**구현에 기댄 항목 — 판이 오르면 다시 돌릴 것**

| 항목 | 왜 다시 돌려야 하나 |
|---|---|
| `__lt__` 호출 **횟수** | TimSort 가 정한다. 같은 결과를 다른 비교로 낼 수 있다 |
| `max`·`min` 이 쓰는 연산자 | 문서에 없다. CPython 의 선택이다 |
| 예외·경고 **문구** 전부 | 판마다 다듬어진다 |
| `NotImplementedType` 이라는 타입 이름 | 내부 이름이다 |
| `` bool(NotImplemented) `` 이 참인 것 | ★ **문서가 미래에 `TypeError` 가 된다고 적었다.** 판이 오르면 여기가 먼저 바뀐다 |
| `` sorted `` 가 `nan` 을 놓는 자리 | 입력 순서에 달린 한 판의 결과다 |
| ★★ **계약 위반을 검사하지 않는 것** | 문서가 검사 여부를 안 적는다. **보장이 아니라 관찰**이라 판이 오르면 다시 봐야 한다 |
| 다섯 크기에서 예외가 없던 것 | **다섯 크기를 본 것**이지 모든 크기를 본 것이 아니다 |

**안 잰 것 — 이 배치의 경계**

| 항목 | 왜 안 쟀나 |
|---|---|
| `total_ordering` 과 손으로 쓴 여섯의 속도 차 | 문서가 주의를 적어 두었으나 **이 배치는 안 쟀다** |
| `key=` 와 `__lt__` 중 어느 쪽이 빠른가 | 안 쟀다 |
