# python/syntax/31-comparison-protocol-and-sortability — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> 실행 환경: `python3` **3.12.3** · Linux. 던지는 형태는 `python3 - <파일` 로 고정했다.
>
> ★★ 이 주제에서는 **「어느 메서드가 불렸나」가 답인 자리가 대부분이다.**
> 결과값만 맞히고 **호출 로그를 못 맞혔으면 틀린 것**으로 센다.
> ★ **호출 「횟수」는 채점 대상이 아니다** — TimSort 의 성질이라 판이 오르면 달라진다.
> 채점하는 것은 **무엇이 불렸나**와 **순서**다.
> ★ 이 주제는 [10번](../10-list-methods-and-sort-key/1-question.md)과 [30번](../30-repr-eq-hash-contracts/1-question.md)을 쓴다.
> 막히면 그 둘 중 어느 것이 안 잡힌 것인지부터 짚어라.
> ★ **이 사슬은 [29](../29-classes-and-attribute-lookup/1-question.md) → [30](../30-repr-eq-hash-contracts/1-question.md) → 31 → [32](../32-container-protocol/1-question.md)** 로 이어진다.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. 메서드 하나만 써 놓고 셋을 물으면 (예측)

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

- ② 의 호출 로그에 **어느 메서드 이름**이 찍히는가?
- ★ ④ 의 세 줄은 각각 어떻게 끝나는가 — 값인가 `TypeError` 인가?
- ★★ ④ 의 세 줄 중 **호출 로그가 한 줄 끼어드는 것**은 어느 것이고, 왜 그런가?

### 2. 둘 다 써 두고 다섯 군데에 넣으면 (예측)

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

- ① 과 ③ 의 로그는 서로 같은가 다른가?
- ★ ② 의 로그에는 어느 메서드가 찍히는가 — 그리고 그 줄들이 ① 과 같은가?
- ★★ ④ 의 `max` 와 `min` 은 각각 어느 메서드를 부르는가?
- ⑤ 의 `heapq` 는 어느 쪽인가?

### 3. 왼쪽에 없으면 (예측)

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

- ① 에서 **어느 클래스의 어느 메서드**가 불리고, 로그의 `self` 와 `other` 는 각각 무엇인가?
- ★ ④ 에서 `` P() < Q() `` 와 `` P() < P() `` 는 **다른 메서드**를 부르는가?
- ★★ ⑤ 의 `` NoLt(1) <= NoLt(2) `` 는 되는가, 안 되는가?

### 4. 데코레이터를 붙이기 전과 후의 클래스 칸 (예측)

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

- ① 의 표에서 **`False` 가 `True` 로 바뀌는 줄**은 몇 개이고 어느 것들인가?
- ★ `__ne__` 와 `__hash__` 줄은 어떻게 되는가?
- ★★ ③ 에서 `` {After(1): 0} `` 은 되는가?
- ★ ⑥ 의 `` NoEq(1) <= NoEq(1) `` 은 무엇을 돌려주는가?

### 5. 「나는 못 재겠다」를 돌려주면 (예측)

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

- ② 에서 `__lt__` 는 **불리는가 안 불리는가**, 그리고 마지막에 무엇이 나오는가?
- ★ ③ 에서 `` bool(NotImplemented) `` 은 무엇이고 무엇이 따라 나오는가?
- ★ ④ 의 예외 문구에서 **두 타입 이름의 순서**는 어떻게 되는가?
- ★★ ⑤ 에서 `if` 는 어느 쪽으로 읽는가?

### 6. 이름표를 붙여 세우면 (예측)

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

- ② 와 ③ 의 호출 로그에는 무엇이 찍히는가?
- ★ ④ 에서 `key` 는 몇 번, **어떤 순서로** 불리는가?
- ★★ ⑤ 에서 `key` 없이 한 줄과 `key` 로 한 줄은 각각 어떻게 끝나는가?

### 7. 같은 키가 셋일 때의 순서 (경계)

`` sorted(rows, key=lambda r: r[1], reverse=True) `` 와 `` list(reversed(sorted(rows, key=lambda r: r[1]))) `` 는 같은 결과인가?

### 8. 섞으면 예외가 나는 자리와 안 나는 자리 (경계)

`` sorted([1, "a"]) `` 와 `` sorted([3.0, 1.0, float("nan"), 2.0]) `` 는 각각 어떻게 끝나는가?\
★★ 그리고 `__lt__` 가 **물을 때마다 다른 답**을 주는 객체를 **10만 개** 정렬하면 무엇이 나오는가 — 예외인가, 리스트인가?\
★ 비교가 **예외를 던지면** 그 예외는 어떻게 되는가?

### 9. 왜 `sorted` 는 `<` 하나로 충분한가 (왜)

`__le__`·`__gt__`·`__ge__` 가 하나도 없어도 정렬이 되는 이유를 문서의 문장으로 댈 수 있는가?

### 10. `total_ordering` 이 못 채우는 것 (경계)

이 데코레이터가 **안 채우는 것 셋**을 대고, 그중 무엇이 **버그로 이어지는지** 말할 수 있는가?

### 11. 30번의 계약과 31번의 계약이 어긋나면 (연결)

「정렬은 되는데 `set` 에 못 넣는 객체」는 어떤 코드에서 나오고, 그것을 고치는 길은 무엇인가?

### 12. 세 층 가르기 (경계)

「`__lt__` 하나로 `sorted` 가 된다」·「`max` 가 `__gt__` 를 쓴다」·「세 원소에 `__lt__` 가 네 번 불린다」는 각각 **언어 보장**·**CPython 구현**·**이 판의 관찰** 중 어디인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|---|---|---|---|
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |
