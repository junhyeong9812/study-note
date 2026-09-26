# python/syntax/32-container-protocol — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> [1-question.md](1-question.md)의 번호와 **1:1**로 대응한다. 질문 12개 = 답 12개.
>
> 이 파일의 모든 출력은 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> 던지는 형태는 `python3 - <파일` 로 고정했다.
> ★ 이 파일의 블록에는 **주소도 시간도 절대경로도 안 찍힌다** — 같은 판에서 다시 돌리면 **한 글자도 안 변한다.**
> 단 **예외 문구**와 `list()` 가 길이를 미리 묻는지 여부는 구현·판에 달린 것이다(11번 답).

## 정답

### 1. `list` 는 둘, `reversed` 는 거꾸로 넷, 슬라이스는 딱 한 번

**출력**

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
```text
===== python3 - <e32_four.py =====
① len(f)
      __len__
   -> 2
② f[0]
      __getitem__ 0
   -> a
③ 'a' in f
      __contains__ a
   -> True
④ for v in f
      __iter__
   받음: a
   받음: b
⑤ list(f)
      __iter__
      __len__
   -> ['a', 'b']
⑥ bool(f)
      __len__
   -> True
⑦ reversed(f)
      __len__
      __len__
      __getitem__ 1
      __getitem__ 0
   -> ['b', 'a']
⑧ f[0:2] — 슬라이스는 __getitem__ 한 번이다
      __getitem__ slice(0, 2, None)
   -> ['a', 'b']
(exit 0)
```

**왜 그런가**

- **여덟 문법이 각자 정해진 창구로 간다.** `len`→`__len__`, `f[0]`→`__getitem__`, `in`→`__contains__`, `for`→`__iter__` 다.
  네 메서드가 다 있으므로 **대체가 한 번도 안 일어났다.**
- ★ **⑤ `list(f)` 는 두 줄이다** — `__iter__` 다음에 `__len__` 이 한 번 더 찍혔다.
  값을 얻는 데 필요해서가 아니라 **결과 리스트를 몇 칸으로 잡을지 미리 알아보는 것**이다.
  ★★ 이것은 **CPython 의 길이 힌트**이지 언어 보장이 아니다. 그래서 `__len__` 안에 부작용을 넣으면
  `list()` 만 했는데 그 부작용이 도는 일이 생긴다.
- ★ **⑦ `reversed(f)` 는 `__len__` 두 번 + `__getitem__ 1` + `__getitem__ 0`** 이다.
  `__reversed__` 가 없으므로 「길이를 알아내 뒤에서부터 인덱싱」 경로로 떨어졌고, 그 경로가 길이를 두 번 확인한다.
  인덱스가 `1` 다음 `0` 으로 **거꾸로** 불린 것이 역순의 증거다.
- ★ **⑧ `f[0:2]` 는 `__getitem__` 이 한 번**이고 인자는 `slice(0, 2, None)` 이다.
  「0번 달라, 1번 달라」로 쪼개지지 않는다 — **대괄호 안은 언제나 한 인자로 뭉친다**(5번 답).
- ⑥ `bool(f)` 가 `__len__` 을 부른 것은 `__bool__` 이 없어서다(3번 답).

### 2. `in` 은 셋으로 떨어지고 `for` 는 둘로만 떨어진다

**출력**

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
```text
===== python3 - <e32_fallback.py =====
가진 것 = (__iter__, __getitem__, __contains__) 의 8가지 조합. __len__ 은 전부 없다.
데이터는 전부 ['a', 'b'] 이고 찾는 값은 'b' 다.

가진 것                     | 'b' in o — 무엇이 불렸나
------------------------------------------------------------------------------
iter+getitem+contains    | __contains__ => True
iter+getitem             | __iter__ => True
iter+contains            | __contains__ => True
iter                     | __iter__ => True
getitem+contains         | __contains__ => True
getitem                  | __getitem__(0) __getitem__(1) => True
contains                 | __contains__ => True
(없음)                     | TypeError: argument of type 'C' is not iterable

가진 것                     | for v in o — 무엇이 불렸나
------------------------------------------------------------------------------
iter+getitem+contains    | __iter__ => ['a', 'b']
iter+getitem             | __iter__ => ['a', 'b']
iter+contains            | __iter__ => ['a', 'b']
iter                     | __iter__ => ['a', 'b']
getitem+contains         | __getitem__(0) __getitem__(1) __getitem__(2) => ['a', 'b']
getitem                  | __getitem__(0) __getitem__(1) __getitem__(2) => ['a', 'b']
contains                 | TypeError: 'C' object is not iterable
(없음)                     | TypeError: 'C' object is not iterable
(exit 0)
```

**왜 그런가**

문서가 `in` 의 순서를 글자로 적는다 —
*"For user-defined classes which define the `__contains__()` method, `x in y` returns True if `y.__contains__(x)` returns a true value ...
which do not define `__contains__()` but do define `__iter__()` ... is True if some value z ... is produced while iterating over y ...
which define `__getitem__()` ... if and only if there is a non-negative integer index i such that `x is y[i] or x == y[i]`, and no lower integer index raises the `IndexError` exception."*

- ★ **`in` 의 우선순위는 `__contains__` → `__iter__` → `__getitem__`** 이다.
  `iter+getitem` 인 줄에서 `__iter__` 가 불렸고 `__getitem__` 은 **한 번도 안 불렸다.**
  둘 다 있으면 **순회 쪽이 이긴다.**
- ★ **`for` 의 우선순위는 `__iter__` → `__getitem__` 둘뿐**이다. `__contains__` 는 그 사슬에 **안 들어온다.**
  그래서 `contains` 만 가진 줄이 갈린다 — `in` 은 `__contains__ => True` 인데
  `for` 는 `TypeError: 'C' object is not iterable` 이다.
- ★★ **대체는 한 방향으로만 흐른다.** 「있느냐」를 아는 능력으로 「전부 내놓기」를 할 수 없기 때문이다.
  **정보량이 많은 쪽으로만 떨어진다.**
- ★ **같은 `__getitem__` 인데 호출 횟수가 다르다.**
  `in` 은 `__getitem__(0) __getitem__(1)` 에서 **찾자마자 멈추고**,
  `for` 는 `__getitem__(2)` 까지 가서 **`IndexError` 로 끝을 안다.**
  그 `IndexError` 가 `StopIteration` 으로 번역되는 것은 [16번](../16-iterator-protocol/2-summary.md) §4 가 정본이다.
- ★ **막힐 때의 문구도 다르다** — `in` 은 `argument of type 'C' is not iterable`,
  `for` 는 `'C' object is not iterable` 이다. **어느 문법에서 막혔는지가 문구로 갈린다.**
- 그래서 판정 한 줄 — **`in` 이 된다고 이터러블인 것이 아니고, 이터러블이면 `in` 은 반드시 된다.**

### 3. `__bool__` 이 이기면 `__len__` 은 로그에 한 줄도 안 찍힌다

**출력**

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
```text
===== python3 - <e32_len_bool.py =====
① __len__ 만 있을 때 — 0 이면 거짓, 아니면 참
      __len__ -> 0
   bool(OnlyLen(0)) -> False
      __len__ -> 3
   bool(OnlyLen(3)) -> True
      __len__ -> 0
   if 문에서도 같다 -> 거짓
② 둘 다 있으면 __bool__ 이 이긴다 — __len__ 은 아예 안 불린다
      __bool__
   bool(LenAndBool()) -> True
③ 아무것도 없으면 늘 참이다
   bool(Nothing()) -> True
④ not 도 같은 길을 탄다
      __len__ -> 0
   not OnlyLen(0) -> True
⑤ len 이 몇이든 bool 은 「0 인가 아닌가」만 본다
      __len__ -> 1
   bool(OnlyLen(1)) -> True
(exit 0)
```

**왜 그런가**

문서가 규칙을 적는다 — *"an object that doesn't define a `__bool__()` method and whose `__len__()` method returns zero is considered to be false in a Boolean context."*

- ★ **묻는 순서는 `__bool__` → `__len__` → 무조건 참**이다.
- **①** `bool(OnlyLen(0))` 은 `False`, `bool(OnlyLen(3))` 은 `True` 다. `__len__` 이 실제로 불린 것이 로그에 있다.
- ★ **②가 이 문항의 과녁이다** — 로그가 `__bool__` **한 줄뿐**이다.
  「둘 다 정의했으니 둘 다 불리겠지」가 아니라 **하나만 불린다.** 안 찍힌 줄을 짚어야 맞은 것이다.
- **③** `Nothing()` 은 **참**이다. 아무것도 없으면 무조건 참이라서, 「빈 컨테이너인데 `if` 가 참이었다」는
  대개 `__len__` 을 안 만든 것이다.
- **④** `not` 도 같은 길을 탄다 — `if`·`while`·`not`·`and`/`or` 가 전부 한 길이다([05번](../05-truthiness-and-short-circuit/2-summary.md)).
- **⑤** 길이가 `1` 이어도 참이다. `bool` 은 **「0 인가 아닌가」만 본다.**

### 4. 다섯 중 둘만 통과한다 — 그리고 `bool()` 도 같은 자리에서 막힌다

**출력**

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
```text
===== python3 - <e32_len_bad.py =====
Neg      -> ValueError: __len__() should return >= 0
Big      -> OverflowError: cannot fit 'int' into an index-sized integer
NotInt   -> TypeError: 'float' object cannot be interpreted as an integer
Boolish  len -> 1
Indexy   len -> 2

bool 로 물어도 같은 자리에서 막히나
bool(Neg()) -> ValueError: __len__() should return >= 0
(exit 0)
```

**왜 그런가**

문서의 요구는 *"Should return the length of the object, an integer >= 0"* 이고, **그 요구를 `len()` 이 강제한다.**

- **통과하는 것은 둘**이다 — `Boolish`(길이 `1`)와 `Indexy`(길이 `2`).
- **`Neg` 는 `ValueError: __len__() should return >= 0`** 이다. 「0 이상」이 실제로 막힌다.
- **`Big` 은 `OverflowError: cannot fit 'int' into an index-sized integer`** 다.
  ★★ 문서가 이것을 **CPython 구현 세부사항으로 명시**한다 — 길이의 상한이 `sys.maxsize` 라는 것.
  **다른 구현에서 같은 예외를 기대하면 안 된다.**
- **`NotInt` 는 `TypeError: 'float' object cannot be interpreted as an integer`** 다.
- ★ **`Boolish` 가 통과하는 것이 함정이다** — `bool` 이 `int` 의 하위 타입이라 `True` 가 길이 `1` 이 된다.
  `__len__` 에 `return bool(...)` 을 쓰면 **길이가 언제나 0 아니면 1** 이 되는데 **예외가 안 난다.**
- ★ **`Indexy` 도 통과한다** — 정수 자체가 아니어도 `__index__` 가 있으면 받아 준다(CPython 이 `PyNumber_Index` 를 건다).
- ★★ **마지막 줄이 이 문항의 값이다** — `bool(Neg())` 도 **같은 `ValueError`** 다.
  3번의 대체 경로가 **검증까지 물려받는다.** 「`len` 은 안 쓰고 `if` 만 쓰니까 괜찮겠지」가 안 통한다.

### 5. 콜론은 `slice`, 쉼표는 `tuple`, 그리고 `-1` 은 `-1` 그대로다

**출력**

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
```text
===== python3 - <e32_slice.py =====
p[3]
   받은 것 : 3                      | 타입 : int
p[1:5]
   받은 것 : slice(1, 5, None)      | 타입 : slice
p[1:5:2]
   받은 것 : slice(1, 5, 2)         | 타입 : slice
p[::-1]
   받은 것 : slice(None, None, -1)  | 타입 : slice
p[:]
   받은 것 : slice(None, None, None) | 타입 : slice
p[1, 2]
   받은 것 : (1, 2)                 | 타입 : tuple
p['a']
   받은 것 : 'a'                    | 타입 : str
p[...]
   받은 것 : Ellipsis               | 타입 : ellipsis
p[1:5, ::2]
   받은 것 : (slice(1, 5, None), slice(None, None, 2)) | 타입 : tuple

slice(1, 9, 3) 의 칸  : 1 9 3
길이 5 에 맞추면      : (1, 5, 3)
그것을 range 로 풀면  : [1, 4]
p[::-1] 이 준 것      : (4, -1, -1)

음수 인덱스는 언어가 안 고쳐 준다 — 그대로 온다
   받은 것 : -1                     | 타입 : int
리스트는 스스로 고친다 : c
(exit 0)
```

**왜 그런가**

- ★ **대괄호 안은 통째로 한 인자다.** 파이썬이 먼저 객체 하나를 만들고 그것을 `__getitem__` 에 넘긴다.
- **`p[:]` 는 `slice(None, None, None)`** 이다. 「비었다」가 아니라 **셋 다 `None` 인 슬라이스**다.
- **`p[1, 2]` 는 튜플 `(1, 2)`** 다. 인자 둘이 아니다. `numpy` 의 `a[i, j]` 가 이 규칙 위에 서 있다.
- **`p[1:5, ::2]` 는 슬라이스 둘이 든 튜플**이다. 콜론과 쉼표가 섞이면 이렇게 온다.
- **`p[...]` 는 `Ellipsis`** 이고 타입 이름이 `ellipsis` 로 **소문자**다.
- **`slice.indices(길이)` 가 경계를 계산해 준다** — `slice(1, 9, 3).indices(5)` 가 `(1, 5, 3)` 이고
  `range` 에 풀면 `[1, 4]` 다. `p[::-1]` 이 준 슬라이스는 길이 5 에서 `(4, -1, -1)` 이 된다.
  **경계를 손으로 자르지 않아도 된다.**
- ★★ **마지막이 가장 중요하다** — `p[-1]` 이 받는 것은 **`-1` 그대로**다.
  「뒤에서 첫 번째」로 바꿔 주는 것은 **리스트가 스스로 하는 일**이지 문법의 일이 아니다
  (바로 아래 줄의 `["a", "b", "c"][-1]` 이 `c` 인 것이 그 증거다).
  ★ 내부에 리스트를 두고 그냥 넘기면 우연히 맞고, **인덱스로 계산을 시작하는 순간 음수가 그대로 새어 들어간다.**
- 그래서 직접 쓰는 `__getitem__` 은 세 갈래를 명시적으로 갈라야 한다 —
  `isinstance(key, slice)` 이면 `indices()` 로, 정수면 음수 보정 후 범위 검사, 그 밖이면 `TypeError`.

### 6. 둘을 주면 다섯이 따라오고, `Duck` 은 넷 중 하나만 참이다

**출력**

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
```text
===== python3 - <e32_abc.py =====
① 내가 쓴 것       : ['__len__', '__getitem__']
② 안 썼는데 되는 것 : ['__contains__', '__iter__', '__reversed__', 'index', 'count']
   s[1]              -> b
   'b' in s          -> True
   list(s)           -> ['a', 'b', 'c']
   list(reversed(s)) -> ['c', 'b', 'a']
   s.index('c')      -> 2
   s.count('a')      -> 1

③ 추상 메서드를 안 채우면 만들 수조차 없다
   TypeError: Can't instantiate abstract class Broken without an implementation for abstract methods '__getitem__', '__len__'

④ 상속하지 않아도 isinstance 가 참인 것들 — __subclasshook__ 을 가진 ABC
   isinstance(Duck(), Iterable ) : True
   isinstance(Duck(), Container) : False
   isinstance(Duck(), Sized    ) : False
   isinstance(Duck(), Sequence ) : False
   isinstance([], Sequence)           : True
   isinstance('x', Sequence)          : True
   isinstance((1,), MutableSequence)  : False

⑤ Sequence 를 물려받아도 옛 프로토콜이 살아 있다 — 0 부터 IndexError 까지
   isinstance(Old(), Iterable) : False
   그런데 for 는 돈다          : ['a', 'b']
(exit 0)
```

**왜 그런가**

- ★ **②에 다섯이 나온다** — `__contains__`·`__iter__`·`__reversed__`·`index`·`count`.
  `__len__` 과 `__getitem__` 둘만 썼는데 나머지가 **진짜 메서드로 붙는다.**
  ★★ 2번의 대체 경로가 「언어가 대신해 주는 것」이라면 이쪽은 「**메서드를 만들어 붙여 주는 것**」이다.
  대체 경로는 `index`·`count` 를 안 준다 — **그 차이가 ABC 를 쓰는 이유**다.
- ★ **③ `Broken()` 은 인스턴스화 자체가 막힌다** —
  `TypeError: Can't instantiate abstract class Broken without an implementation for abstract methods '__getitem__', '__len__'`.
  ★★ 30·31 이 「어겨도 아무 말 없이 자료구조가 틀린다」였던 것과 **정반대**다.
  ABC 는 이 사슬에서 **유일하게 앞당겨 터지는 장치**다.
- ★ **④ `Duck()` 은 넷 중 하나만 참이다** — `Iterable` 만 `True` 이고 `Container`·`Sized`·`Sequence` 는 `False` 다.
  **한 메서드짜리 ABC 만 오리 판정을 한다.** `Sequence` 처럼 여러 개가 필요한 ABC 는 **상속하거나 등록해야** 참이 된다.
  `isinstance((1,), MutableSequence)` 가 거짓인 것도 같은 이치이고, 튜플은 쓰기를 지원하지 않으니 **맞는 답**이다.
- ★★★ **⑤의 두 줄은 서로 어긋난다** — `isinstance(Old(), Iterable)` 이 `False` 인데 **`for` 는 돈다.**
  `Iterable` 이 보는 것은 `__iter__` 하나뿐이라 **대체 경로가 그 창에 안 비친다.**
  [16번](../16-iterator-protocol/2-summary.md)이 「`hasattr(x, '__iter__')` 로 검사하면 틀린 답을 얻는다」고 한 자리의 **ABC 판**이다.
- 그래서 판정 한 줄 — **「이터러블인가」는 `isinstance` 도 `hasattr` 도 아니라 `iter(x)` 를 걸어 보고 `TypeError` 를 잡아 묻는다.**

### 7. `+=` 는 둘을 부르고, 슬라이스 대입도 같은 자리로 온다

**출력**

```python
# e32_setitem.py
class Rec:
    def __init__(self):
        self.store = {}

    def __getitem__(self, k):
        print("      __getitem__", repr(k))
        return self.store[k]

    def __setitem__(self, k, v):
        print("      __setitem__", repr(k), "=", repr(v))
        self.store[k] = v

    def __delitem__(self, k):
        print("      __delitem__", repr(k))
        del self.store[k]

    def __len__(self):
        return len(self.store)


r = Rec()
print("① 넣기")
r["a"] = 1
r["b"] = 2
print("② 꺼내기")
print("   ->", r["a"])
print("③ 지우기")
del r["a"]
print("   남은 것 :", r.store, "| len :", len(r))
print("④ 슬라이스 대입도 같은 자리로 온다")
r[1:3] = ["x", "y"]
print("   store :", r.store)
print("⑤ += 는 __getitem__ 과 __setitem__ 을 둘 다 부른다")
r["b"] += 10
print("   store :", r.store)
print("⑥ 없는 키를 지우면 내가 낸 예외가 그대로 나간다")
try:
    del r["zz"]
except KeyError as ex:
    print("   KeyError:", ex)
print("⑦ __setitem__ 이 없으면")


class ReadOnly:
    def __getitem__(self, k):
        return k


try:
    ReadOnly()["a"] = 1
except TypeError as ex:
    print("   TypeError:", ex)
```
```text
===== python3 - <e32_setitem.py =====
① 넣기
      __setitem__ 'a' = 1
      __setitem__ 'b' = 2
② 꺼내기
      __getitem__ 'a'
   -> 1
③ 지우기
      __delitem__ 'a'
   남은 것 : {'b': 2} | len : 1
④ 슬라이스 대입도 같은 자리로 온다
      __setitem__ slice(1, 3, None) = ['x', 'y']
   store : {'b': 2, slice(1, 3, None): ['x', 'y']}
⑤ += 는 __getitem__ 과 __setitem__ 을 둘 다 부른다
      __getitem__ 'b'
      __setitem__ 'b' = 12
   store : {'b': 12, slice(1, 3, None): ['x', 'y']}
⑥ 없는 키를 지우면 내가 낸 예외가 그대로 나간다
      __delitem__ 'zz'
   KeyError: 'zz'
⑦ __setitem__ 이 없으면
   TypeError: 'ReadOnly' object does not support item assignment
(exit 0)
```

**왜 그런가**

- **`x[k] = v` 는 `__setitem__`, `del x[k]` 는 `__delitem__`** 으로 곧장 간다. 여기는 **대체 경로가 없다.**
- ★ **④ 슬라이스 대입도 같은 자리로 온다** — `r[1:3] = ["x", "y"]` 가
  `__setitem__(slice(1, 3, None), ['x', 'y'])` 다. 5번 답과 같은 규칙이다.
- ★★ **⑤ `r["b"] += 10` 은 두 메서드를 부른다** — 로그가 `__getitem__ 'b'` 다음 `__setitem__ 'b' = 12` 다.
  즉 **읽고 → 더하고 → 다시 쓰는** 세 걸음이다.
  그래서 **읽기만 가능한 컨테이너에는 `+=` 를 쓸 수 없다.** 마지막 걸음에서 막힌다.
- ★ **⑥ 내가 낸 예외는 그대로 나간다** — 없는 키를 지울 때 `__delitem__` 이 **먼저 찍히고** 그다음 `KeyError: 'zz'` 다.
  언어가 미리 막아 주지 않는다. **`__delitem__` 은 일단 불린다.**
- **⑦ `__setitem__` 이 없으면** `TypeError: 'ReadOnly' object does not support item assignment` 다.
  ★ 읽기 전용 컨테이너를 만들려면 **그냥 안 만들면 된다.** 막는 코드를 따로 쓸 필요가 없다.

### 8. 프레임은 하나이고, 예외를 낸 것은 `len()` 이다

**출력**

```python
# e32_len_neg_tb.py
class Neg:
    def __len__(self):
        return -1


print("len 을 부른다")
len(Neg())
```
```text
===== python3 - <e32_len_neg_tb.py =====
len 을 부른다
Traceback (most recent call last):
  File "<stdin>", line 7, in <module>
ValueError: __len__() should return >= 0
(exit 1)
```

**왜 그런가**

- ★ **프레임이 하나뿐이다** — `File "<stdin>", line 7, in <module>` 한 줄이고 그 아래 바로 예외 줄이다.
- ★★ **예외를 낸 것은 내 `__len__` 이 아니라 `len()` 이다.**
  내 `__len__` 은 `-1` 을 정상적으로 돌려주고 끝났고, **결과를 검사하던 `len()` 이 거부했다.**
  그래서 스택에 `__len__` 프레임이 없다 — **틀린 값을 만든 자리와 터진 자리가 다르다.**
- ★ **실행 중 예외라 소스 줄도 `^` 캐럿도 안 나온다.** `python3 - <파일` 로 던졌기 때문에
  경로가 `<stdin>` 으로 고정되고, 컴파일러가 그 시점에 소스를 안 들고 있어서 줄을 못 끼운다.
  `SyntaxError` 였다면 소스 줄과 캐럿이 둘 다 나왔을 것이다.
- **종료 코드는 `1`** 이다. 잡히지 않은 예외로 끝났다는 뜻이다.
- 진단이 원인에서 먼 자리이므로, `__len__` 을 뺄셈으로 계산한다면 **`max(0, ...)` 로 막거나 그 자리에서 직접 검사**하는 쪽이 낫다.

### 9. 16번 §4 가 정본이고, 끝은 `IndexError` 로 알며, `in` 에서는 `__iter__` 가 앞선다

**왜 그런가**

- **정본은** [16번](../16-iterator-protocol/2-summary.md) §4 「`__iter__` 가 없어도 `for` 가 돈다 — 낡은 프로토콜」이다.
  PEP 234 이전 호환으로 남은 경로이고, `iter()` 문서가 그 대체를 명시한다.
- **끝은 `IndexError` 로 안다.** 0·1·2… 로 부르다가 `IndexError` 가 나면 끝난 것으로 보고,
  그 예외는 `StopIteration` 으로 **번역돼** 바깥에 안 나온다.
  ★ 그래서 **엉뚱한 `IndexError` 가 나면 루프가 조용히 일찍 끝난다.**
- ★ **`in` 도 같은 경로를 타지만 우선순위가 다르다** — `in` 에서는 `__contains__` 가 맨 앞이고,
  그다음이 `__iter__`, 마지막이 `__getitem__` 이다.
  `for` 에는 `__contains__` 단계가 아예 없으므로 **두 단계뿐**이다.
- 2번 답의 로그가 그 차이를 그대로 보여 준다 — `iter+getitem` 인 줄에서 `in` 이 `__iter__` 를 골랐다.

### 10. 못 하는 것은 순회이고, 차이는 「돌게 해 주는 것」과 「메서드를 붙여 주는 것」이다

**왜 그런가**

- **`__contains__` 만 있는 객체가 못 하는 것은 순회**다 — `for`·`list()`·언패킹·컴프리헨션이 전부 막힌다.
  `TypeError: 'C' object is not iterable` 이다.
- ★ **정보량으로 보면 당연하다.** 「이 값이 있느냐」에 답하는 능력에서
  「전부 내놓아라」를 끌어낼 수 없다. 반대로 **전부 내놓을 수 있으면 있느냐는 훑어서 답할 수 있다.**
  그래서 **대체는 정보량이 많은 쪽으로만 흐른다.**
- ★★ **`collections.abc` 와 대체 경로는 층이 다르다.**

| | 대체 경로 | `collections.abc` 믹스인 |
|---|---|---|
| 누가 해 주나 | **언어 문법**이 부를 때만 | **클래스에 메서드가 실제로 붙는다** |
| 무엇을 얻나 | `in`·`for` 가 **돌기는 한다** | `index`·`count`·`__reversed__` 까지 |
| `isinstance` | ★ **안 비친다**(`Iterable` 이 거짓) | 참이 된다 |
| 안 채우면 | **아무 말 없이** 느리거나 막힌다 | **인스턴스화가 막힌다** |

- 그래서 **제대로 된 컨테이너는 ABC 를 물려받고, 빠르게 할 수 있는 것만 덮어쓴다.**
  ★ 믹스인은 **일반 구현**이라 `__contains__`·`index` 가 순회로 찾는다. 물려받았다고 빨라지지 않는다.
  (여기서도 **시간은 안 쟀다** — 「순회로 찾는다」는 구현의 성질이지 측정값이 아니다.)

### 11. 대체 순서는 언어 보장, 길이 힌트와 상한은 CPython 이다

**왜 그런가**

| 층 | 이 주제에서 해당하는 것 |
|---|---|
| **언어 보장** | `in` 의 세 단계 대체 순서(Membership test operations 가 글자로 적는다) · `for` 의 `__iter__`→`__getitem__` · `__bool__` 이 없고 `__len__` 이 0 이면 거짓 · `__len__` 은 0 이상의 정수 · 대괄호 안이 한 인자로 뭉치는 것 · 특수 메서드를 **타입에서** 찾는 것 · `Sequence` 가 둘을 요구하고 다섯을 주는 것 · 추상 메서드를 안 채우면 인스턴스화가 막히는 것 |
| **CPython 구현** | ★ `list(x)` 가 `__len__` 을 **한 번 더** 묻는 것(길이 힌트) · `reversed(x)` 가 두 번 묻는 것 · ★ 길이 상한이 `sys.maxsize` 라 `2 ** 63` 이 `OverflowError` 인 것(**문서가 구현 세부사항으로 명시**) · `__len__` 결과에 `__index__` 를 걸어 주는 것 · `in` 이 `__getitem__` 경로에서 찾자마자 멈추는 것 |
| **이 판(3.12.3)의 관찰** | 예외 **문구** 전부(`argument of type 'C' is not iterable` 과 `'C' object is not iterable` 이 **다른 것** 포함) · `Can't instantiate abstract class …` 문구(3.12 에서 바뀐 꼴) · `ellipsis` 가 소문자인 것 · `__getitem__` 이 `in` 에서 2번 `for` 에서 3번 불린 **횟수** |

- ★ **세 물음의 답을 한 줄씩으로** —
  `in` 의 대체 순서는 **언어 보장**, `list(x)` 의 길이 힌트는 **CPython 구현**,
  `2 ** 63` 의 `OverflowError` 는 **CPython 구현**(문서가 그렇게 표시한다).
- ★ 대체 **순서**는 명세지만 **횟수**는 결과의 부산물이다. 횟수를 근거로 쓸 때는 그 사실을 같이 적어야 한다.

### 12. 16번은 순회 계약, 32번은 대체 격자 — 그리고 둘이 갈리는 객체가 있다

**왜 그런가**

- **[16번](../16-iterator-protocol/2-summary.md)이 정본인 것** — `iter()`/`next()`/`StopIteration` 의 계약,
  이터러블과 이터레이터를 가르는 `iter(x) is x`, 소진된 것과 빈 것이 구분되지 않는 것,
  그리고 **`__getitem__` 낡은 프로토콜의 동작 자체.**
- **여기가 정본인 것** — **네 프로토콜이 서로를 대신하는 격자**(`in` 과 `for` 의 우선순위가 다르다는 것),
  `__len__` 이 `__bool__` 을 대신하는 것, 대괄호 인자가 한 덩어리인 것, `collections.abc` 의 믹스인.
- ★★★ **둘이 갈리는 객체는 `__getitem__` 만 가진 객체**다.
  `for` 는 도는데 `isinstance(o, Iterable)` 이 **거짓**이다.
  창 ①(정의된 메서드)·②(호출 로그)·③(예외 없음)이 전부 「된다」고 말하는데 **창 ④만 「아니다」라고 답한다.**
  **「돈다」와 「그 타입이다」는 다른 질문**이라는 것이 이 주제의 조용한 자리다.
- ★ **[30번](../30-repr-eq-hash-contracts/2-summary.md)의 `__eq__` 가 틀리면 `in` 이 같이 틀린다.**
  `__contains__` 가 없을 때의 대체 경로는 **`x is y[i] or x == y[i]`** 로 비교하기 때문이다(문서 문장 그대로).
  즉 **컨테이너를 고쳐도 안 고쳐지고 원소의 `__eq__` 를 고쳐야** 한다.
- ★ 그리고 사슬 전체의 대비 한 줄 — **30·31 은 계약을 어기면 자료구조가 조용히 틀렸고,
  32 는 계약을 반만 지켜도 언어가 나머지를 대신 채워 준다.**
  대신 **채워 준 것이 무엇인지 모르면** 느려지거나(`in` 이 전수 탐색) 엉뚱해진다(음수 인덱스).

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 네 프로토콜이 다 있을 때의 호출 로그 | `python3 - <e32_four.py` | 2(캡처 + 재대조) | 여덟 문법 전부 확인. `list` 가 `__len__` 을 추가로 묻는 것 관측 |
| 여덟 조합 × 두 물음 전수 격자 | `python3 - <e32_fallback.py` | 2 | 16줄 전부 동일. 대체 순서가 문서와 일치 |
| `__len__` → `__bool__` 대체 | `python3 - <e32_len_bool.py` | 2 | `__bool__` 이 있으면 `__len__` 이 안 불림 확인 |
| `__len__` 반환값 검증 다섯 갈래 | `python3 - <e32_len_bad.py` | 2 | `ValueError`·`OverflowError`·`TypeError` + 통과 둘 |
| 음수 길이 트레이스백 전문 | `python3 - <e32_len_neg_tb.py` | 2 | 프레임 1개 · `(exit 1)` |
| 대괄호 인자 아홉 가지 | `python3 - <e32_slice.py` | 2 | `slice`·`tuple`·`Ellipsis`·음수 미보정 확인 |
| 쓰기 쪽 프로토콜과 `+=` | `python3 - <e32_setitem.py` | 2 | `+=` 가 두 메서드를 부르는 것 확인 |
| `collections.abc` 믹스인과 `isinstance` | `python3 - <e32_abc.py` | 2 | 다섯이 따라옴 · `Old()` 가 `Iterable` 에 거짓인데 `for` 는 돎 |

**구현 의존 항목** — 판이 오르면 다시 돌려야 하는 것.

| 항목 | 왜 |
|---|---|
| `list(x)` 가 `__len__` 을 한 번 더 묻는 것 | CPython 의 길이 힌트. 언어 보장이 아니다 |
| `reversed(x)` 가 `__len__` 을 두 번 묻는 것 | 위와 같다 |
| `2 ** 63` 이 `OverflowError` 인 것 | 길이 상한이 `sys.maxsize` 라는 **CPython 구현 세부사항** |
| 예외 문구 전부 | 종류는 명세지만 문구는 아니다 |
| `Can't instantiate abstract class …` 문구 | 3.12 에서 바뀐 꼴이다 |
| `__getitem__` 호출 **횟수**(2번 대 3번) | 대체 **순서**만 명세다 |
| `isinstance(Duck(), Container)` 가 거짓인 것 | `__subclasshook__` 이 어느 ABC 에 붙었는지는 라이브러리 구현이다 |

★ **안 흔들리는 칸** — 대체 **순서** 자체, 어느 메서드가 **불렸나 안 불렸나**, `len()` 값,
`in` 의 참·거짓, `File "<stdin>", line N`, `(exit N)`.
이 주제의 블록에는 주소도 시간도 절대경로도 없어 **같은 판에서 다시 돌리면 한 글자도 안 변한다**(재대조로 확인).
