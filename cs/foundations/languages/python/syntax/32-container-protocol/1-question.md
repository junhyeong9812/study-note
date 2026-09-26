# python/syntax/32-container-protocol — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> ★★ 이 주제에서는 **「어느 메서드가 대신 불렸나」가 답인 자리가 대부분이다.**
> 결과값만 맞히고 **호출 로그를 못 맞히면 틀린 것**으로 친다.
> ★ 그리고 **「안 불린 줄」을 짚어야 맞은 것**인 문항이 둘 있다(1번의 슬라이스, 3번의 `__bool__`).
>
> 실행 환경: `python3` **3.12.3** · Linux. 던지는 형태는 `python3 - <파일` 로 고정했다.
> ★ **이 주제는 [16번](../16-iterator-protocol/1-question.md)을 전부 쓴다** — `__getitem__` 낡은 프로토콜이 거기 정본이다.
> 막히면 그것이 안 잡힌 것인지부터 짚어라.
> ★ **이 사슬은 [29](../29-classes-and-attribute-lookup/1-question.md) → [30](../30-repr-eq-hash-contracts/1-question.md) → [31](../31-comparison-protocol-and-sortability/1-question.md) → 32** 로 이어지고, **여기가 끝**이다.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. 네 메서드를 다 열어 두고 여덟 문법을 던지면 (예측)

```python
# e32_four.py
class Full:
    def __init__(self, data):
        self.data = list(data)

    def __len__(self):
        print("      __len__")
        return len(self.data)

    def __getitem__(self, i):
        print("      __getitem__", i)
        return self.data[i]

    def __contains__(self, v):
        print("      __contains__", v)
        return v in self.data

    def __iter__(self):
        print("      __iter__")
        return iter(self.data)


f = Full("ab")
print("① len(f)")
print("   ->", len(f))
print("② f[0]")
print("   ->", f[0])
print("③ 'a' in f")
print("   ->", "a" in f)
print("④ for v in f")
for v in f:
    print("   받음:", v)
print("⑤ list(f)")
print("   ->", list(f))
print("⑥ bool(f)")
print("   ->", bool(f))
print("⑦ reversed(f)")
print("   ->", list(reversed(f)))
print("⑧ f[0:2] — 슬라이스는 __getitem__ 한 번이다")
print("   ->", f[0:2])
```

- ⑤의 `list(f)` 에서 로그가 **몇 줄** 찍히는가?
- ⑦의 `reversed(f)` 는 `__getitem__` 을 **어느 순서로** 부르는가?
- ★ ⑧의 `f[0:2]` 에서 `__getitem__` 은 **몇 번** 불리고, 인자로 **무엇**을 받는가?

### 2. 여덟 조합에 `in` 과 `for` 를 던지면 (예측)

```python
# e32_fallback.py
import itertools

LOG = []


def build(has_iter, has_getitem, has_contains):
    ns = {"__init__": lambda self, data: setattr(self, "data", list(data))}

    def _iter(self):
        LOG.append("__iter__")
        return iter(self.data)

    def _getitem(self, i):
        LOG.append("__getitem__(%r)" % (i,))
        return self.data[i]

    def _contains(self, v):
        LOG.append("__contains__")
        return v in self.data

    if has_iter:
        ns["__iter__"] = _iter
    if has_getitem:
        ns["__getitem__"] = _getitem
    if has_contains:
        ns["__contains__"] = _contains
    return type("C", (), ns)


def probe(obj, what):
    LOG.clear()
    try:
        if what == "in":
            r = repr("b" in obj)
        else:
            r = repr([v for v in obj])
    except TypeError as ex:
        return "TypeError: " + str(ex)
    trail = " ".join(LOG) if LOG else "(아무것도 안 불림)"
    return trail + " => " + r


print("가진 것 = (__iter__, __getitem__, __contains__) 의 8가지 조합. __len__ 은 전부 없다.")
print("데이터는 전부 ['a', 'b'] 이고 찾는 값은 'b' 다.")
print()
head = "%-24s | %s" % ("가진 것", "'b' in o — 무엇이 불렸나")
print(head)
print("-" * 78)
for it, gi, co in itertools.product([1, 0], repeat=3):
    have = "+".join(n for n, b in (("iter", it), ("getitem", gi), ("contains", co)) if b) or "(없음)"
    print("%-24s | %s" % (have, probe(build(it, gi, co)("ab"), "in")))

print()
head2 = "%-24s | %s" % ("가진 것", "for v in o — 무엇이 불렸나")
print(head2)
print("-" * 78)
for it, gi, co in itertools.product([1, 0], repeat=3):
    have = "+".join(n for n, b in (("iter", it), ("getitem", gi), ("contains", co)) if b) or "(없음)"
    print("%-24s | %s" % (have, probe(build(it, gi, co)("ab"), "for")))
```

- `iter+getitem` 인 줄에서 `'b' in o` 는 **무엇을 부르는가**?
- ★ `contains` 만 가진 줄에서 `'b' in o` 와 `for v in o` 의 결과가 **어떻게 갈리는가**?
- ★ `getitem` 만 가진 줄에서 `in` 과 `for` 의 `__getitem__` 호출 **횟수가 같은가**?
- 아무것도 없는 줄에서 나는 두 `TypeError` 의 **문구가 같은가**?

### 3. `__len__` 만 있는 객체를 `if` 에 넣으면 (예측)

```python
# e32_len_bool.py
class OnlyLen:
    def __init__(self, n):
        self.n = n

    def __len__(self):
        print("      __len__ ->", self.n)
        return self.n


class LenAndBool:
    def __len__(self):
        print("      __len__")
        return 0

    def __bool__(self):
        print("      __bool__")
        return True


class Nothing:
    pass


print("① __len__ 만 있을 때 — 0 이면 거짓, 아니면 참")
print("   bool(OnlyLen(0)) ->", bool(OnlyLen(0)))
print("   bool(OnlyLen(3)) ->", bool(OnlyLen(3)))
print("   if 문에서도 같다 ->", "참" if OnlyLen(0) else "거짓")
print("② 둘 다 있으면 __bool__ 이 이긴다 — __len__ 은 아예 안 불린다")
print("   bool(LenAndBool()) ->", bool(LenAndBool()))
print("③ 아무것도 없으면 늘 참이다")
print("   bool(Nothing()) ->", bool(Nothing()))
print("④ not 도 같은 길을 탄다")
print("   not OnlyLen(0) ->", not OnlyLen(0))
print("⑤ len 이 몇이든 bool 은 「0 인가 아닌가」만 본다")
print("   bool(OnlyLen(1)) ->", bool(OnlyLen(1)))
```

- ①에서 `bool(OnlyLen(0))` 과 `bool(OnlyLen(3))` 은 각각 무엇인가?
- ★ ②에서 **로그에 몇 줄이 찍히는가**?
- ③의 `Nothing()` 은 참인가 거짓인가?

### 4. 다섯 가지 길이를 돌려주면 (예측)

```python
# e32_len_bad.py
class Neg:
    def __len__(self):
        return -1


class Big:
    def __len__(self):
        return 2 ** 63


class NotInt:
    def __len__(self):
        return 1.5


class Boolish:
    def __len__(self):
        return True


class Indexy:
    def __len__(self):
        class I:
            def __index__(self):
                return 2
        return I()


for cls in (Neg, Big, NotInt, Boolish, Indexy):
    try:
        print("%-8s len ->" % cls.__name__, len(cls()))
    except Exception as ex:
        print("%-8s ->" % cls.__name__, type(ex).__name__ + ":", ex)

print()
print("bool 로 물어도 같은 자리에서 막히나")
try:
    print("bool(Neg()) ->", bool(Neg()))
except Exception as ex:
    print("bool(Neg()) ->", type(ex).__name__ + ":", ex)
```

- 다섯 클래스 중 **`len()` 이 통과하는 것은 몇 개**인가?
- 막히는 것들은 각각 **어떤 예외**인가?
- ★ 마지막 줄에서 `bool(Neg())` 은 어떻게 되는가?

### 5. 대괄호 안에 아홉 가지를 넣으면 (예측)

```python
# e32_slice.py
class Peek:
    def __getitem__(self, key):
        print("   받은 것 : %-22r | 타입 : %s" % (key, type(key).__name__))
        return key


p = Peek()
for expr in ("p[3]", "p[1:5]", "p[1:5:2]", "p[::-1]", "p[:]", "p[1, 2]", "p['a']", "p[...]", "p[1:5, ::2]"):
    print(expr)
    eval(expr)

print()
s = slice(1, 9, 3)
print("slice(1, 9, 3) 의 칸  :", s.start, s.stop, s.step)
print("길이 5 에 맞추면      :", s.indices(5))
print("그것을 range 로 풀면  :", list(range(*s.indices(5))))
print("p[::-1] 이 준 것      :", slice(None, None, -1).indices(5))
print()
print("음수 인덱스는 언어가 안 고쳐 준다 — 그대로 온다")
p[-1]
print("리스트는 스스로 고친다 :", ["a", "b", "c"][-1])
```

- `p[:]` 가 받는 것은 무엇인가?
- `p[1, 2]` 와 `p[1:5, ::2]` 가 받는 것의 **타입**은 각각 무엇인가?
- ★ 마지막의 `p[-1]` 이 받는 것은 무엇인가?

### 6. 둘만 쓰고 `Sequence` 를 물려받으면 (예측)

```python
# e32_abc.py
from collections.abc import Sequence, Iterable, Container, Sized, MutableSequence


class MySeq(Sequence):
    def __init__(self, data):
        self.data = list(data)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, i):
        return self.data[i]


s = MySeq("abc")
mine = [n for n in ("__len__", "__getitem__", "__contains__", "__iter__", "__reversed__", "index", "count")
        if n in MySeq.__dict__]
free = [n for n in ("__contains__", "__iter__", "__reversed__", "index", "count")
        if n not in MySeq.__dict__]
print("① 내가 쓴 것       :", mine)
print("② 안 썼는데 되는 것 :", free)
print("   s[1]              ->", s[1])
print("   'b' in s          ->", "b" in s)
print("   list(s)           ->", list(s))
print("   list(reversed(s)) ->", list(reversed(s)))
print("   s.index('c')      ->", s.index("c"))
print("   s.count('a')      ->", s.count("a"))

print()
print("③ 추상 메서드를 안 채우면 만들 수조차 없다")


class Broken(Sequence):
    pass


try:
    Broken()
except TypeError as ex:
    print("   TypeError:", ex)

print()
print("④ 상속하지 않아도 isinstance 가 참인 것들 — __subclasshook__ 을 가진 ABC")


class Duck:
    def __iter__(self):
        return iter(())


for abc in (Iterable, Container, Sized, Sequence):
    print("   isinstance(Duck(), %-9s) : %s" % (abc.__name__, isinstance(Duck(), abc)))
print("   isinstance([], Sequence)           :", isinstance([], Sequence))
print("   isinstance('x', Sequence)          :", isinstance("x", Sequence))
print("   isinstance((1,), MutableSequence)  :", isinstance((1,), MutableSequence))

print()
print("⑤ Sequence 를 물려받아도 옛 프로토콜이 살아 있다 — 0 부터 IndexError 까지")


class Old:
    def __getitem__(self, i):
        return ["a", "b"][i]


print("   isinstance(Old(), Iterable) :", isinstance(Old(), Iterable))
print("   그런데 for 는 돈다          :", [v for v in Old()])
```

- ②에 **몇 개**가 나오고 그 이름들은 무엇인가?
- ③에서 `Broken()` 은 어떻게 되는가?
- ★ ④에서 `Duck()` 은 네 ABC 중 **몇 개**에 참인가?
- ★★ ⑤의 두 줄이 **서로 어긋나는가**?

### 7. 넣고 지우고 더하면 무엇이 불리나 (경계)

- `r["b"] += 10` 한 줄이 부르는 특수 메서드는 **몇 개**이고 무엇인가?
- `r[1:3] = ["x", "y"]` 는 `__setitem__` 에 **무엇을** 넘기는가?
- `__setitem__` 을 안 만든 객체에 대입하면 어느 예외가 나는가?

### 8. 음수 길이의 트레이스백 (경계)

- `__len__` 이 `-1` 을 돌려줬을 때 트레이스백의 프레임은 **몇 개**인가?
- ★ 그 예외를 낸 것은 **내 `__len__` 인가 `len()` 인가**?

### 9. `__getitem__` 하나로 `for` 가 도는 이유 (연결)

- 그 대체 경로의 정본은 [16번](../16-iterator-protocol/2-summary.md)의 어느 절인가?
- 그 경로는 **끝을 무엇으로** 아는가?
- ★ `in` 도 같은 경로를 타는데 **우선순위에서 무엇이 앞서는가**?

### 10. 대체 경로가 대체하지 못하는 것 (경계)

- `__contains__` 만 있는 객체가 **못 하는 것**은 무엇인가?
- 대체가 **한 방향으로만 흐르는** 이유를 정보량으로 설명하면?
- ★ `collections.abc` 가 주는 것과 대체 경로가 주는 것의 **차이**는 무엇인가?

### 11. 세 층 가르기 (경계)

- `in` 의 세 단계 대체 순서는 **언어 보장인가 CPython 구현인가**?
- `list(x)` 가 `__len__` 을 한 번 더 묻는 것은 어느 층인가?
- ★ `2 ** 63` 이 `OverflowError` 가 되는 것은 어느 층인가?

### 12. 이웃 주제와의 경계 (연결)

- [16번](../16-iterator-protocol/2-summary.md)이 정본인 것과 이 주제가 정본인 것을 한 줄씩으로 가르면?
- ★ 「`for` 가 돈다」와 「`isinstance(o, Iterable)` 이 참이다」가 갈리는 객체는 어떤 것인가?
- [30번](../30-repr-eq-hash-contracts/2-summary.md)의 `__eq__` 가 틀리면 이 주제의 무엇이 같이 틀리는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|---|---|---|---|
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |
