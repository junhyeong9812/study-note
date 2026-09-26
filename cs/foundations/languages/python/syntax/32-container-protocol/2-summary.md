# python/syntax/32-container-protocol — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만.
> - [3.3.7. Emulating container types](https://docs.python.org/3.12/reference/datamodel.html#emulating-container-types) — `__len__`·`__getitem__`·`__setitem__`·`__delitem__`·`__iter__`·`__contains__` 의 계약
> - [6.10.2. Membership test operations](https://docs.python.org/3.12/reference/expressions.html#membership-test-operations) — ★ `in` 의 **대체 순서**가 여기 글자로 적혀 있다
> - [Truth Value Testing](https://docs.python.org/3.12/library/stdtypes.html#truth-value-testing) · [`object.__bool__`](https://docs.python.org/3.12/reference/datamodel.html#object.__bool__) — `__len__` 이 `__bool__` 을 대신하는 규칙
> - [`collections.abc`](https://docs.python.org/3.12/library/collections.abc.html) — 어느 추상 메서드를 주면 어느 믹스인이 따라오나
> - [3.3.1. Special method lookup](https://docs.python.org/3.12/reference/datamodel.html#special-method-lookup) — 특수 메서드는 **인스턴스가 아니라 타입에서** 찾는다
>
> **실행 검증** — 이 문서에 실린 출력은 전부 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.\
> ★ 던지는 형태를 하나로 고정했다 — `python3 - <파일` 로 던져 트레이스백이 `File "<stdin>", line N` 이 된다.\
> ★★ **캐럿은 예외 종류에 달렸다** — 실행 중 예외는 소스 줄도 `^` 캐럿도 안 나오고, `SyntaxError` 라야 둘 다 나온다.
> 이 문서의 트레이스백은 **한 덩어리뿐이고 실행 중 예외**라 세 줄짜리다.\
> **버전** — 여섯 특수 메서드는 전부 **Python 3 내내 있던 것**이고 이 노트 범위(3.10\~3.13)에서 안 바뀌었다.
> 갈리는 것은 둘이다 — `collections.abc` 가 `collections` 에서 **3.3 에 갈라져 나온 것**(3.10 부터는 `collections` 에서 못 import 한다)과,
> 추상 클래스 인스턴스화 실패 **문구**가 3.12 에서 `without an implementation for abstract methods` 꼴로 바뀐 것이다.\
> **구현 대 언어 보장 한 줄** — **어느 메서드가 어느 메서드를 대신하는가의 순서까지가 언어 보장**이고,
> **`list()` 가 길이를 미리 묻는 것·`2**63` 이 `OverflowError` 가 되는 것·예외 문구**는 CPython 쪽이다.\
> ★ **흔들리는 칸 / 안 흔들리는 칸** — 재대조에서 「고칠 것」과 「설계상 안 맞는 것」을 기계적으로 가르려고 미리 선언한다.
>
> | 흔들린다 | 안 흔들린다(근거로 써도 되는 칸) |
> |---|---|
> | `id()` 와 `0x…` 주소 — 그래서 이 주제는 한 번도 안 찍었다 | 예외 **종류** · `File "<stdin>", line N` · `(exit N)` |
> | 판이 오르면 예외 **문구**와 내부 타입 이름 | **호출 로그의 순서** · 어느 특수 메서드가 **불렸나 안 불렸나** |
> | 판이 오르면 `list()` 가 길이를 미리 묻는지 여부 | `len()` 값 · `in` 의 참·거짓 · `sorted()` 한 결과 |
> | — | **여덟 조합의 격자 전체** — 대체 순서는 명세다 |
>
> ★ **이 주제의 블록에는 주소도 시간도 절대경로도 한 곳도 안 찍힌다.** 같은 판에서 다시 돌리면 **한 글자도 안 변한다.**\
> **선행** — [16-iterator-protocol](../16-iterator-protocol/2-summary.md)(★★★ **`__iter__`/`__next__`/`StopIteration` 과 `__getitem__` 낡은 프로토콜의 정본**) ·
> [09-sequence-ops-and-slicing](../09-sequence-ops-and-slicing/2-summary.md)(내장 시퀀스의 슬라이싱) ·
> [13-set-and-frozenset](../13-set-and-frozenset/2-summary.md)(내장 쪽 `in` 의 비용) ·
> [29-classes-and-attribute-lookup](../29-classes-and-attribute-lookup/2-summary.md)(특수 메서드를 **어디서** 찾나).\
> **이 사슬** — [29](../29-classes-and-attribute-lookup/2-summary.md) → [30](../30-repr-eq-hash-contracts/2-summary.md) → [31](../31-comparison-protocol-and-sortability/2-summary.md) → 32.
> **여기가 사슬의 끝이다** — 29 가 「속성을 어디서 찾나」, 30·31 이 「계약을 어기면 자료구조가 조용히 틀린다」였다면,
> 32 는 「**계약을 반만 지켜도 언어가 나머지를 대신 채워 준다**」다. 대신 채워 주는 그 자리가 이 주제의 값이다.

## 한눈에 — 쉽게 말하면

**컨테이너 프로토콜은 「내 객체에 붙일 수 있는 네 개의 창구」다.**

- `__len__` — 「몇 개요?」 창구. `len(x)` 가 여기로 온다.
- `__getitem__` — 「N번 주세요」 창구. `x[N]` 이 여기로 온다.
- `__contains__` — 「이거 있어요?」 창구. `x in y` 가 여기로 온다.
- `__iter__` — 「처음부터 훑을게요」 창구. `for` 가 여기로 온다.

★★ 그런데 **창구를 다 열지 않아도 가게는 돈다.**\
손님이 닫힌 창구에 가면 **언어가 옆 창구로 데려간다** — 그 옆길이 이 주제의 본체다.

```text
   손님의 요구            열린 창구가 있으면         없으면 언어가 데려가는 곳
   ---------------------------------------------------------------------
   len(x)                 __len__                    (없음 — 바로 TypeError)
   x[i]                   __getitem__                (없음 — 바로 TypeError)
   if x:                  __bool__                   __len__  ->  0 인가 아닌가
   y in x                 __contains__               __iter__  ->  __getitem__
   for v in x             __iter__                   __getitem__ (0부터)

   ★ 화살표는 한 방향뿐이다.
     __contains__ 만 열어 두면 `in` 은 되는데 `for` 는 안 된다.
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 몇 개요 창구 | `__len__` | 로그에 `__len__` 이 찍힌다 |
| N번 주세요 창구 | `__getitem__` | 로그에 `__getitem__ 0` 이 찍힌다 |
| 이거 있어요 창구 | `__contains__` | 로그에 `__contains__` 가 찍힌다 |
| 처음부터 훑을게요 창구 | `__iter__` | 로그에 `__iter__` 가 찍힌다 |
| ★ **닫힌 창구에서 옆으로 데려가기** | 대체 경로(fallback) | **다른 메서드 이름이 로그에 찍힌다** |
| ★ 옆길이 **한 방향뿐인 것** | `in` 은 순회로 떨어지지만 `for` 는 `__contains__` 로 못 떨어진다 | `TypeError: 'C' object is not iterable` |
| 셔터를 아예 안 올린 가게 | 아무 메서드도 없는 클래스 | `TypeError` 두 가지가 **다른 문구**로 난다 |
| 프랜차이즈 본사 매뉴얼 | `collections.abc` 믹스인 | 둘만 쓰면 다섯이 따라온다 |
| ★ **간판과 실제 영업이 다른 가게** | `isinstance(o, Iterable)` 은 거짓인데 `for` 는 도는 객체 | 이 주제의 **조용한 자리** |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.\
「**`__getitem__` 만 만들어 놓고 `in` 이 왜 이렇게 느리지 했더니 전수 탐색이었다**」와
「**음수 인덱스가 리스트처럼 뒤에서 세어 줄 줄 알았는데 그대로 `-1` 이 왔다**」가 그것이다.\
둘 다 **예외가 안 난다.** 그래서 테스트가 통과한 채로 틀린다.

> **컨테이너 프로토콜(container protocol)** — `len()`·대괄호·`in`·`for` 같은 **내장 문법**이
> 객체의 어느 특수 메서드를 부를지 정해 둔 약속.\
> 예: `len(x)` 는 언제나 `type(x).__len__(x)` 를 부른다.

> **대체 경로(fallback)** — 찾던 특수 메서드가 없을 때 언어가 **대신 쓰기로 정해 둔** 다른 메서드.\
> 예: `__contains__` 가 없으면 `in` 은 객체를 처음부터 순회해서 찾는다.

> **믹스인(mixin)** — 「이것만 주면 나머지는 내가 만들어 준다」는 방식으로 물려주는 메서드 묶음.\
> 예: `collections.abc.Sequence` 에 `__len__`·`__getitem__` 둘만 주면 `index`·`count` 등이 따라온다.

먼저 판을 박아 둔다. 이 문서의 모든 출력은 아래 판에서 나왔다.

```python
# e32_version.py
import sys

print("version_info =", sys.version_info)
print("implementation =", sys.implementation.name)
print("platform =", sys.platform)
```
```text
===== python3 - <e32_version.py =====
version_info = sys.version_info(major=3, minor=12, micro=3, releaselevel='final', serial=0)
implementation = cpython
platform = linux
(exit 0)
```

## 이 주제가 답하려는 질문

1. **네 창구가 다 열려 있으면 어느 문법이 어느 창구로 가나** — `len`·대괄호·`in`·`for`·`bool`·`reversed`·슬라이스가 각각 무엇을 부르나.
2. ★★★ **창구 하나를 닫으면 언어가 무엇으로 대신하나** — 그리고 **대신하지 못하는 조합은 무엇인가.**
3. **반만 구현했을 때 「되는 것」과 「그 타입인 것」이 갈리나** — `for` 는 도는데 `isinstance` 가 거짓인 객체가 있나.

★ 둘째 질문이 이 주제의 인출 목표다. **여덟 조합을 머릿속에서 채울 수 있는 것**이 아는 것과 들은 것의 경계다.

## 동작 방식

> 이 절이 본문이다. 이 주제의 진단창은 넷이다 —
> ① **정의된 특수 메서드 목록**(`'__iter__' in C.__dict__`) ② **호출 로그**(무엇이 대신 불렸나)
> ③ **예외 종류와 문구** ④ ★ **`isinstance(o, 컬렉션 ABC)`**.
> ★★ 앞의 셋이 전부 「된다」고 말하는데 ④만 「아니다」라고 답하는 자리가 있다.
> **「돈다」와 「그 타입이다」가 갈리는 것**이 이 주제의 조용한 자리다.

| 창 | 무엇을 말해 주나 | 못 보는 것 |
|---|---|---|
| ① 정의된 특수 메서드 목록 | 내가 **무엇을 썼나** | 언어가 **무엇으로 대신할지**는 모른다 |
| ② 호출 로그 | 실제로 **무엇이 불렸나** — 대체가 일어났는지 | 안 불린 것이 **없어서인지 안 쓰여서인지**는 모른다 |
| ③ 예외 종류와 문구 | **막힌 자리**와 막힌 이유 | 막히지 않고 **조용히 느려진 것**은 모른다 |
| ④ `isinstance(o, ABC)` | 라이브러리·타입 검사기가 **뭐라고 볼 것인가** | **실제로 도는지**는 모른다 |

### 1. ★ 넷이 다 열려 있을 때 — 어느 문법이 어느 창구로 가나

**언제 쓰나** — 컨테이너를 처음 만들 때. 그리고 「`list(x)` 가 왜 `__len__` 을 부르지?」가 막힐 때.

먼저 네 메서드를 다 정의해 두고, 여덟 가지 문법을 하나씩 던져 **로그로 받는다.**

```text
   문법            ->  불린 것
   -------------------------------------------
   len(f)              __len__
   f[0]                __getitem__ 0
   'a' in f            __contains__ a
   for v in f          __iter__
   list(f)             __iter__ 다음에 __len__      <- ★ 둘이다
   bool(f)             __len__
   reversed(f)         __len__ 두 번 + __getitem__ 1, 0
   f[0:2]              __getitem__ slice(0, 2, None) <- ★ 한 번이다
```

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

그림 해설 — 여덟 줄 중 **놀라는 것이 셋**이다.

- ★ **`list(f)` 가 `__iter__` 다음에 `__len__` 을 한 번 더 묻는다.**
  값을 얻는 데 필요해서가 아니라 **결과 리스트를 몇 칸으로 잡을지 미리 알아보려는 것**이다.
  ★★ **이것은 CPython 의 구현이다** — 언어가 「`list()` 는 길이를 묻는다」고 약속한 적이 없다.
  그래서 `__len__` 안에 부작용을 넣으면 **`list()` 만 했는데 그 부작용이 도는** 일이 생긴다.
- ★ **`reversed(f)` 가 `__len__` 을 두 번 묻는다.** `__reversed__` 가 없으면 「길이를 알아내서 뒤에서부터 `__getitem__`」으로 떨어지는데,
  그 경로가 길이를 두 번 확인한다. 로그를 보면 `__getitem__ 1` 다음에 `__getitem__ 0` 으로 **거꾸로** 불린다.
  ★ [16번](../16-iterator-protocol/2-summary.md) 에서 `reversed` 가 `__len__` 이 없어 `TypeError` 를 냈던 그 자리의 **반대 판**이다.
- ★ **슬라이스는 `__getitem__` 이 한 번만 불린다.** `f[0:2]` 가 「0번 달라, 1번 달라」로 쪼개지지 않는다.
  **`slice` 객체 하나가 통째로 인자로 온다** — 아래 5절이 그것이다.

**비용** — 네 창구를 다 열면 각 문법이 **곧장 한 번**에 도착한다. 대체 경로를 타지 않으므로 군더더기가 없다.
다만 `__len__` 은 **내가 안 부른 자리에서도 불린다**(`bool`·`list`·`reversed`). 싸게 만들어야 한다.

### 2. ★★★ 창구를 닫으면 무엇이 대신하나 — 여덟 조합 전수

**언제 쓰나** — 이 절이 이 주제의 본체다. 남의 클래스가 왜 `in` 은 되고 `for` 는 안 되는지 설명할 때.

문서가 `in` 의 대체 순서를 **글자로** 적는다 —
*"For user-defined classes which define the `__contains__()` method, `x in y` returns True if `y.__contains__(x)` returns a true value ...
For user-defined classes which do not define `__contains__()` but do define `__iter__()`, `x in y` is True if some value z ... is produced while iterating over y ...
For user-defined classes which define `__getitem__()`, `x in y` is True if and only if there is a non-negative integer index i such that `x is y[i] or x == y[i]`, and no lower integer index raises the `IndexError` exception."*

그 문장을 그림으로 옮기면 이렇다.

```text
   y in x  의 대체 사슬                    for v in x  의 대체 사슬

   __contains__ 있나?                      __iter__ 있나?
        | 있다 -> 그것을 부른다                  | 있다 -> 그것을 부른다
        | 없다                                  | 없다
        v                                       v
   __iter__ 있나?                          __getitem__ 있나?
        | 있다 -> 0번부터 훑어 == 로 비교        | 있다 -> 0, 1, 2, ... IndexError 까지
        | 없다                                  | 없다
        v                                       v
   __getitem__ 있나?                       TypeError 로 막힌다
        | 있다 -> 0번부터 훑어 == 로 비교          ("'C' object is not iterable")
        | 없다
        v
   TypeError 로 막힌다
     ("argument of type 'C' is not iterable")
```

★★ **두 사슬을 겹쳐 보면 비대칭이 보인다.**

```text
                  __contains__    __iter__    __getitem__
   in    을 만족   O               O           O
   for   를 만족   X               O           O
                  ^
                  +-- 여기만 비어 있다. 대체는 "아래로"만 흐른다.
```

여덟 조합을 전수로 던져 **무엇이 불렸는지 로그로 받았다.**
`__len__` 은 전부 뺐고, 데이터는 전부 `['a', 'b']`, 찾는 값은 `'b'` 로 고정했다.

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

그림 해설 — 열여섯 줄에서 읽히는 규칙은 **다섯 줄**이다.

- ★ **`in` 의 우선순위는 `__contains__` → `__iter__` → `__getitem__` 이다.**
  `iter+getitem` 조합에서 `__iter__` 가 불렸고 `__getitem__` 은 한 번도 안 불렸다 — **둘 다 있으면 순회 쪽이 이긴다.**
- ★ **`for` 의 우선순위는 `__iter__` → `__getitem__` 둘뿐이다.**
  `__contains__` 는 그 사슬에 아예 안 들어온다. `contains` 만 가진 줄에서 `TypeError: 'C' object is not iterable` 이 났다.
- ★★ **대체는 한 방향뿐이다.** `in` 은 순회로 떨어질 수 있지만 **`for` 는 `__contains__` 로 떨어질 수 없다.**
  당연하다 — 「있느냐」를 아는 것과 「전부 내놓는 것」은 다른 능력이다. **정보량이 많은 쪽으로만 떨어진다.**
- ★ **같은 `__getitem__` 인데 호출 횟수가 다르다.**
  `in` 은 `__getitem__(0) __getitem__(1)` 에서 **찾자마자 멈추고**,
  `for` 는 `__getitem__(2)` 까지 가서 **`IndexError` 로 끝을 안다.** 한 번 차이가 로그에 그대로 있다.
  ★ 끝을 알리는 그 `IndexError` 가 `StopIteration` 으로 번역되는 것은 [16번](../16-iterator-protocol/2-summary.md) §4 가 정본이다.
- ★ **막힐 때도 두 문구가 다르다.** `in` 은 `argument of type 'C' is not iterable`,
  `for` 는 `'C' object is not iterable` 이다. **어느 문법에서 막혔는지가 문구로 갈린다.**

★★★ 그래서 실무 판정은 이 한 줄이다 — **`in` 이 된다고 이터러블인 것이 아니고, 이터러블이면 `in` 은 반드시 된다.**

**비용** — 여기가 조용히 비싸지는 자리다.
`__contains__` 를 안 만들면 `in` 이 **전수 탐색**으로 떨어진다. 예외도 경고도 없다.
`dict`·`set` 이 `__contains__` 를 따로 가진 이유가 그것이다([13번](../13-set-and-frozenset/2-summary.md)).
★ 이 문서는 **비용의 성질만 적고 시간은 안 쟀다** — 재지 않은 수치는 쓰지 않는다.

### 3. ★ `__len__` 이 `__bool__` 을 대신한다

**언제 쓰나** — `if my_container:` 를 쓸 때. 그리고 「빈 것인데 왜 참이지?」가 막힐 때.

문서가 규칙을 직접 적는다 — *"an object that doesn't define a `__bool__()` method and whose `__len__()` method returns zero is considered to be false in a Boolean context"* —
즉 **`__bool__` 이 없고 `__len__` 이 0 을 돌려줄 때만** 거짓이다.

```text
   if x:  가 묻는 순서

   __bool__ 있나? ---- 있다 ----> 그 결과를 그대로 쓴다 (__len__ 은 안 본다)
        |
       없다
        v
   __len__ 있나? ----- 있다 ----> 0 이면 거짓, 그 밖이면 참
        |
       없다
        v
   무조건 참
```

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

그림 해설.

- ★ **`__bool__` 이 이기면 `__len__` 은 아예 안 불린다.** ②에서 로그에 `__bool__` 한 줄만 찍혔다.
  「둘 다 정의했더니 둘 다 불리더라」가 아니다 — **하나만 불린다.**
- ★ **아무것도 없으면 늘 참이다.** ③의 `Nothing()` 이 그것이다.
  그래서 「빈 컨테이너인데 `if` 가 참이었다」는 대개 **`__len__` 을 안 만든 것**이다.
- ★ `not` 도 같은 길을 탄다(④). `if`·`while`·`not`·`and`/`or` 가 전부 이 한 길이다([05번](../05-truthiness-and-short-circuit/2-summary.md)).
- ★ **`bool` 은 「0 인가 아닌가」만 본다**(⑤). 길이가 1 이든 1000 이든 참이다.

**비용** — `__len__` 하나로 진릿값까지 공짜로 얻는다.
다만 **`__len__` 이 비싸면 `if x:` 한 줄이 비싸진다.** 길이를 세는 데 순회가 필요한 자료구조라면 `__bool__` 을 따로 두는 쪽이 낫다.

### 4. ★ `__len__` 이 돌려준 값도 검사받는다

**언제 쓰나** — `__len__` 을 계산해서 돌려줄 때. 특히 뺄셈이 들어가 **음수가 날 수 있을 때.**

문서가 요구한다 — *"Should return the length of the object, an integer >= 0."*\
그 요구를 **누가 강제하는지**가 이 절의 내용이다.

```text
   len(x) 가 통과시키는 관문

   __len__() 결과
        |
        +-- 정수가 아니면?      -> __index__ 가 있으면 그것을 쓴다, 없으면 TypeError
        +-- 음수면?             -> ValueError
        +-- 너무 크면?          -> OverflowError   (CPython 의 상한)
        +-- True / False 면?    -> bool 은 int 라서 그냥 통과 (1 / 0)
        v
   호출한 쪽으로 나간다
```

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

그림 해설 — 다섯 줄이 **세 층으로 갈린다.**

- **음수는 `ValueError`** 다. 문서의 「0 이상」이라는 요구를 **런타임이 실제로 막는다.**
- **너무 큰 값은 `OverflowError: cannot fit 'int' into an index-sized integer`** 다 — `2 ** 63` 을 돌려준 줄이 그것이다.
  ★★ 문서가 이것을 **CPython 구현 세부사항으로 명시**한다 — 길이의 상한이 `sys.maxsize` 라는 것.
  다른 구현에서 같은 예외가 난다고 기대하면 안 된다.
- **`1.5` 는 `TypeError`** 다. 「길이는 정수」라는 요구가 여기서 걸린다.
- ★ **`True` 는 통과한다** — `bool` 이 `int` 의 하위 타입이라 길이 `1` 이 된다([04번](../04-numeric-types-and-division/2-summary.md)).
  **의도치 않게 통과하는 자리**이므로 `return bool(...)` 을 `__len__` 에 쓰면 안 된다.
- ★ **`__index__` 를 가진 객체도 통과한다** — 정수 자체가 아니어도 「정수로 쓸 수 있는 것」이면 받아 준다.

★★ 그리고 마지막 줄이 중요하다 — **`bool()` 로 물어도 같은 자리에서 막힌다.**
`bool(Neg())` 이 `ValueError` 다. 3절의 대체 경로가 **검증까지 물려받는다**는 뜻이다.
「`len` 은 안 쓰고 `if` 만 쓰니까 괜찮겠지」가 안 통한다.

음수일 때의 트레이스백 전문은 이렇다.

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

- ★ **실행 중 예외라 소스 줄도 캐럿도 없다.** `File "<stdin>", line 7, in <module>` 한 줄 다음 바로 예외 줄이다.
- ★ **프레임이 하나뿐이다** — `__len__` 안에서 난 예외가 아니라 **`len()` 이 결과를 검사하다 낸** 예외이기 때문이다.
  내 `__len__` 은 정상적으로 `-1` 을 돌려주고 끝났다. **틀린 값을 만든 자리와 터진 자리가 다르다.**

**비용** — 검증이 `len()` 쪽에 있으므로 내 `__len__` 은 아무것도 안 해도 된다.
대신 **터지는 자리가 원인에서 멀다** — 스택만 보면 어느 계산이 음수를 만들었는지 안 나온다.

### 5. ★ 대괄호 안의 것은 통째로 한 인자다

**언제 쓰나** — 슬라이싱을 지원하는 컨테이너를 만들 때. 그리고 `x[1:5]` 가 왜 `__getitem__` 한 번인지 볼 때.

```text
   x[1:5:2]  를 파이썬이 하는 일

   1:5:2  ------>  slice(1, 5, 2) 라는 객체 하나를 만든다
                          |
                          v
                   x.__getitem__( slice(1, 5, 2) )   <- 인자는 언제나 하나다

   x[1, 2]   ---->  tuple (1, 2) 하나
   x[...]    ---->  Ellipsis 하나
   x[1:5, ::2] --->  tuple (slice(1,5,None), slice(None,None,2)) 하나
```

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

그림 해설.

- ★ **콜론이 있으면 `slice` 객체가 온다.** `p[:]` 조차 `slice(None, None, None)` 이다 — 빈 것이 아니라 **셋 다 `None` 인 슬라이스**다.
- ★ **쉼표가 있으면 튜플이 온다.** `p[1, 2]` 는 인자 둘이 아니라 **튜플 하나**다.
  `numpy` 의 `a[i, j]` 가 이 규칙 위에 서 있다.
- ★ **`...` 은 `Ellipsis` 라는 내장 객체**다. 타입 이름이 `ellipsis` 로 소문자다.
- ★ **둘을 섞으면 슬라이스가 든 튜플**이 온다(`p[1:5, ::2]`).
- **`slice.indices(길이)` 가 `range` 인자 셋을 계산해 준다.** `slice(1, 9, 3).indices(5)` 가 `(1, 5, 3)` 이고
  그것을 `range` 에 풀면 `[1, 4]` 다. **내가 경계를 손으로 자르지 않아도 된다.**
  `p[::-1]` 이 준 `slice(None, None, -1)` 은 길이 5 에서 `(4, -1, -1)` 이 된다 — 역순 순회의 정확한 경계다.

★★ 그리고 마지막 두 줄이 **직접 쓴 컨테이너에서 가장 흔한 버그**다.

- ★★ **음수 인덱스를 언어가 고쳐 주지 않는다.** `p[-1]` 은 `-1` 이 **그대로** 온다.
  「뒤에서 첫 번째」로 바꿔 주는 것은 **리스트가 스스로 하는 일**이지 문법의 일이 아니다.
  내가 `self.data[i]` 로 그냥 넘기면 리스트가 대신 고쳐 주지만, 인덱스로 계산을 하는 순간 음수가 그대로 새어 들어간다.
- 그래서 직접 쓰는 `__getitem__` 은 **세 갈래를 명시적으로 갈라야** 한다 —
  `isinstance(key, slice)` 이면 `indices()` 로, 정수면 음수 보정 후 범위 검사, 그 밖이면 `TypeError`.

**비용** — 인자가 하나로 통일되므로 `__getitem__` 의 시그니처가 단순하다.
대신 **갈라 받는 일을 내가 한다.** 그 일을 안 하면 음수·슬라이스가 조용히 엉뚱한 값을 낸다.

### 6. `__setitem__`·`__delitem__` — 쓰기 쪽 창구

**언제 쓰나** — 읽기만 되는 컨테이너에 쓰기를 열 때. 그리고 `x[k] += 1` 이 무엇을 부르는지 볼 때.

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

그림 해설.

- **`x[k] = v` 는 `__setitem__`, `del x[k]` 는 `__delitem__`** 으로 곧장 간다. 대체 경로가 없다.
- ★ **슬라이스 대입도 같은 자리로 온다.** `r[1:3] = ["x", "y"]` 가 `__setitem__(slice(1, 3, None), ['x', 'y'])` 다.
  5절과 같은 규칙이다 — **대괄호 안은 언제나 한 인자.**
- ★★ **`+=` 는 `__getitem__` 과 `__setitem__` 을 둘 다 부른다.**
  로그가 `__getitem__ 'b'` 다음 `__setitem__ 'b' = 12` 로 찍혔다.
  즉 `r["b"] += 10` 은 **읽고 → 더하고 → 다시 쓰는** 세 걸음이다.
  ★ 그래서 **읽기만 가능한 컨테이너에는 `+=` 를 쓸 수 없다.** `__getitem__` 만 있으면 마지막 걸음에서 막힌다.
- ★ **내가 낸 예외는 그대로 나간다.** 없는 키를 지울 때 `KeyError: 'zz'` 가 `__delitem__` 이 찍힌 **다음에** 났다.
  언어가 미리 막아 주지 않는다 — **`__delitem__` 은 일단 불린다.**
- **`__setitem__` 이 없으면** `TypeError: 'ReadOnly' object does not support item assignment` 다.
  읽기 전용 컨테이너를 만들려면 **그냥 안 만들면 된다.** 막는 코드를 따로 쓸 필요가 없다.

**비용** — 쓰기 창구는 읽기와 완전히 분리돼 있다. 하나만 열면 그 방향만 열린다.
대신 `+=` 같은 **복합 대입은 두 창구를 다 요구**한다.

### 7. ★★ `collections.abc` — 둘을 주면 다섯이 따라온다

**언제 쓰나** — 제대로 된 시퀀스·매핑을 만들 때. 그리고 「`index`·`count` 까지 손으로 써야 하나?」가 막힐 때.

```text
   내가 쓰는 것            ABC 가 얹어 주는 것
   ------------------------------------------------------
   Sequence
     __len__       ---->   __contains__   (순회로 찾는다)
     __getitem__   ---->   __iter__       (0부터 IndexError 까지)
                   ---->   __reversed__   (길이를 알아 뒤에서부터)
                   ---->   index          (없으면 ValueError)
                   ---->   count
```

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

그림 해설 — 다섯 덩어리로 갈린다.

- ★ **둘만 쓰면 다섯이 따라온다.** ②가 `['__contains__', '__iter__', '__reversed__', 'index', 'count']` 다.
  2절의 대체 경로가 「언어가 대신해 주는 것」이라면, 이쪽은 「**진짜 메서드를 만들어 붙여 주는 것**」이다.
  대체 경로는 `index`·`count` 를 안 준다 — **그 차이가 ABC 를 쓰는 이유**다.
- ★ **추상 메서드를 안 채우면 인스턴스를 만들 수조차 없다**(③).
  `TypeError: Can't instantiate abstract class Broken without an implementation for abstract methods '__getitem__', '__len__'` 이다.
  ★★ 30·31 이 「어겨도 아무 말 없이 자료구조가 틀린다」였던 것과 **정반대**다 — 여기는 **만들 때 막힌다.**
  ABC 는 파이썬에서 몇 안 되는 **앞당겨 터지는** 장치다.
- ★★ **`__subclasshook__` 의 경계가 좁다**(④). `__iter__` 만 가진 오리는
  `Iterable` 에는 참이지만 `Container`·`Sized`·`Sequence` 에는 **거짓**이다.
  즉 **한 메서드짜리 ABC 만 오리 판정을 한다.** `Sequence` 처럼 여러 개가 필요한 ABC 는 **등록하거나 상속해야** 참이 된다.
  그래서 `isinstance((1,), MutableSequence)` 도 거짓이다 — 튜플은 쓰기를 지원하지 않으니 맞는 답이다.
- ★★★ **그리고 마지막 두 줄이 이 주제의 네 번째 창이다**(⑤).
  `__getitem__` 만 가진 옛 객체는 **`isinstance(o, Iterable)` 이 `False` 인데 `for` 는 돈다.**
  창 ①(정의된 메서드)·②(호출 로그)·③(예외 없음)이 전부 「된다」고 말하는데 **창 ④만 「아니다」라고 답한다.**
  ★ [16번](../16-iterator-protocol/2-summary.md) 이 「`hasattr(x, '__iter__')` 로 검사하면 틀린 답을 얻는다」고 한 자리의 **ABC 판**이다.
  `Iterable` 이 보는 것은 `__iter__` 하나뿐이고, **대체 경로는 그 창에 안 비친다.**

★★ 그래서 판정 한 줄 — **「이터러블인가」를 물으려면 `isinstance` 도 `hasattr` 도 아니라 `iter(x)` 를 걸어 보고 `TypeError` 를 잡아야 한다.**

**비용** — ABC 가 주는 믹스인은 **일반 구현**이다. `__contains__` 는 순회로 찾고 `index` 도 순회로 찾는다.
내 자료구조가 더 빨리 할 수 있으면 **덮어써야** 한다. 물려받았다고 빨라지지 않는다.
★ 여기서도 **시간은 안 쟀다** — 「순회로 찾는다」는 구현의 성질이지 측정값이 아니다.

## 문법 — 형태와 규칙

**형태 — 여섯 메서드의 시그니처**

이 절은 코드펜스 대신 표로 적는다. 실제로 돌린 소스는 전부 위 블록에 있다.

| 문법 | 부르는 것 | 시그니처 | 안 돌려주면 |
|---|---|---|---|
| `len(x)` | `__len__` | `(self) -> int >= 0` | `TypeError` |
| `x[k]` | `__getitem__` | `(self, key)` — key 는 **언제나 하나** | `TypeError` |
| `x[k] = v` | `__setitem__` | `(self, key, value)` | `TypeError: … does not support item assignment` |
| `del x[k]` | `__delitem__` | `(self, key)` | `TypeError: … doesn't support item deletion` |
| `v in x` | `__contains__` | `(self, value) -> 참·거짓` | 대체 경로로 간다 |
| `for v in x` | `__iter__` | `(self) -> 이터레이터` | 대체 경로로 간다 |
| `bool(x)` | `__bool__` | `(self) -> bool` | `__len__` 으로 간다 |
| `reversed(x)` | `__reversed__` | `(self) -> 이터레이터` | `__len__` + `__getitem__` 으로 간다 |

**규칙 불릿**

- ★ **대괄호 안은 언제나 한 인자**로 뭉친다 — 콜론은 `slice`, 쉼표는 `tuple`, `...` 은 `Ellipsis`.
- ★ **음수 인덱스 보정은 언어가 안 한다.** 내가 한다.
- ★ **`__len__` 의 결과는 `len()` 이 검사한다** — 음수면 `ValueError`, 정수가 아니면 `TypeError`.
- ★ **`__contains__` 가 없으면 `in` 이 조용히 전수 탐색이 된다.** 예외도 경고도 없다.
- ★ **`__iter__` 가 없어도 `__getitem__` 이 있으면 `for` 가 돈다** — 정본은 [16번](../16-iterator-protocol/2-summary.md) §4 다.
- ★ **특수 메서드는 인스턴스가 아니라 타입에서 찾는다**(문서 3.3.1).
  `obj.__len__ = ...` 로 인스턴스 칸에 넣어도 `len(obj)` 는 그것을 안 본다.
  ★ **속성 탐색이 인스턴스 칸을 먼저 보는 것과 다른 규칙**이다 — 그 대비는 [29번](../29-classes-and-attribute-lookup/2-summary.md)이 정본이다.

**금지 사례 — 이렇게 쓰면 막힌다**

| 쓴 것 | 결과 |
|---|---|
| `__contains__` 만 정의하고 `for` | `TypeError: 'C' object is not iterable` |
| 아무것도 정의 안 하고 `in` | `TypeError: argument of type 'C' is not iterable` |
| `__len__` 이 `-1` 반환 | `ValueError: __len__() should return >= 0` |
| `__len__` 이 `1.5` 반환 | `TypeError: 'float' object cannot be interpreted as an integer` |
| `__getitem__` 만 있는데 `x[0] = 1` | `TypeError: … does not support item assignment` |
| `Sequence` 상속 후 `__len__` 미구현 | 인스턴스화 자체가 `TypeError` |

## 어디서 틀리나

### (1) 「`in` 이 되니까 이터러블이다」로 안다

`__contains__` 만 있으면 `in` 은 되는데 `for` 는 `TypeError` 다.\
★ **역방향은 참이다** — 이터러블이면 `in` 은 반드시 된다. **한 방향만 성립한다.**

### (2) 「`__getitem__` 만 만들었으니 `for` 는 안 되겠지」로 안다

돈다. 0부터 `IndexError` 까지 부른다([16번](../16-iterator-protocol/2-summary.md) §4 가 정본).\
★ 그래서 **엉뚱한 `IndexError` 가 나면 루프가 조용히 일찍 끝난다.**

### (3) `isinstance(x, Iterable)` 로 「돌 수 있나」를 검사한다

★★ `__getitem__` 만 있는 객체는 **거짓인데 돈다.** 블록 ⑤가 그 증거다.\
**`iter(x)` 를 걸어 보고 `TypeError` 를 잡는 것**만이 바른 검사다.

### (4) 음수 인덱스를 리스트처럼 처리해 줄 거라고 믿는다

`p[-1]` 은 `-1` 그대로 온다. 보정은 **리스트가 하는 일**이지 문법의 일이 아니다.\
★ 내부에 리스트를 두고 그냥 넘기면 우연히 맞고, 인덱스로 계산을 시작하면 조용히 틀린다.

### (5) 슬라이스가 `__getitem__` 을 여러 번 부를 거라고 믿는다

한 번이다. `slice` 객체 하나가 온다.\
★ 그래서 **슬라이스를 안 다루는 `__getitem__` 은 `x[1:3]` 에서 엉뚱한 예외를 낸다** — 내부 리스트가 대신 처리해 주면 그나마 도는 정도다.

### (6) `__len__` 에 비싼 계산을 넣는다

`bool(x)`·`list(x)`·`reversed(x)` 가 **내가 안 불렀는데도 부른다.**\
★ 특히 `list(x)` 가 부르는 것은 **CPython 의 길이 힌트**다 — 판에 따라 없어질 수도 있는 호출이니 부작용을 넣으면 안 된다.

### (7) 빈 컨테이너인데 `if x:` 가 참이다

`__len__` 을 안 만든 것이다. 아무것도 없으면 **무조건 참**이다.\
★ `__bool__` 과 `__len__` 이 둘 다 있으면 `__bool__` 이 이기고 `__len__` 은 **안 불린다.**

### (8) `__len__` 에서 `return bool(...)` 을 쓴다

`bool` 은 `int` 라 **통과한다.** 길이가 언제나 0 아니면 1 이 된다 — 예외가 안 나서 더 나쁘다.

### (9) `__contains__` 를 안 만들고 「`in` 은 빠르겠지」라고 믿는다

★ 순회로 떨어진다. **예외도 경고도 없다.**\
`dict`·`set` 이 상수 시간인 것은 **그들이 `__contains__` 를 따로 가졌기 때문**이지 `in` 이라는 문법 덕이 아니다([13번](../13-set-and-frozenset/2-summary.md)).

### (10) `collections.abc` 를 물려받았으니 빨라졌다고 믿는다

믹스인은 **일반 구현**이다. `__contains__`·`index` 가 순회로 찾는다.\
★ 내 자료구조가 더 빨리 할 수 있으면 **덮어써야** 한다.

### (11) 인스턴스에 특수 메서드를 꽂아 바꾸려 한다

`obj.__len__ = lambda: 3` 은 `len(obj)` 에 안 먹는다 — **타입에서 찾기** 때문이다(문서 3.3.1).\
★ 속성 탐색은 인스턴스 칸을 먼저 보는데 특수 메서드는 안 그렇다. 그 대비는 [29번](../29-classes-and-attribute-lookup/2-summary.md)이 정본이다.

### (12) `ReadOnly` 컨테이너에 `+=` 가 될 거라고 믿는다

`+=` 는 `__getitem__` 과 `__setitem__` 을 **둘 다** 부른다. 마지막 걸음에서 막힌다.

## 구현 세부사항 대 언어 보장

세 층으로 가른다. ★ **이 주제는 「언어 보장」이 유난히 두껍다** — 대체 순서 자체가 명세에 글자로 적혀 있기 때문이다.
구현 쪽에 남는 것은 **누가 길이를 미리 묻느냐**와 **상한·문구**다.

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **언어 보장** | 언어 레퍼런스·표준 라이브러리 문서가 정한 것 | 문서 문장을 열어서 인용 |
| **CPython 구현** | 이 구현이 그렇게 하는 것 | 실행 로그 + 문서의 「CPython implementation detail」 표시 |
| **이 판(3.12.3)의 관찰** | 이번에 돌려서 본 것 | 「관찰」로 명기 |

### 언어 보장

| 사실 | 근거 |
|---|---|
| `in` 은 `__contains__` → `__iter__` → `__getitem__` 순으로 떨어진다 | Membership test operations — 세 문단이 그 순서로 적혀 있다 |
| `for` 는 `__iter__` → `__getitem__`(0부터) 로만 떨어진다 | `iter()` 의 시퀀스 프로토콜 대체 ([16번](../16-iterator-protocol/2-summary.md)이 정본) |
| `__bool__` 이 없고 `__len__` 이 0 이면 거짓 | Truth Value Testing |
| `__len__` 은 **0 이상의 정수**를 돌려줘야 한다 | `object.__len__` — *"an integer >= 0"* |
| `__len__` 이 없고 `__bool__` 도 없으면 **참** | Truth Value Testing — 기본값이 참 |
| 대괄호 안은 **한 인자**로 뭉친다(슬라이스·튜플·`Ellipsis`) | 3.3.7 Emulating container types · 슬라이싱 문법 |
| 특수 메서드는 **타입에서** 찾는다 | 3.3.1 Special method lookup |
| `Sequence` 는 `__len__`·`__getitem__` 을 요구하고 나머지 다섯을 믹스인으로 준다 | `collections.abc` 표 |
| 추상 메서드를 안 채운 ABC 하위 클래스는 **인스턴스화가 막힌다** | `abc` — 추상 메서드 규칙 |

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| `list(x)` 가 `__iter__` 다음 `__len__` 을 **한 번 더** 묻는 것 | 실행 로그 — **길이 힌트**다. 언어가 약속한 적 없다 |
| `reversed(x)` 가 `__len__` 을 **두 번** 묻는 것 | 실행 로그 |
| 길이의 상한이 `sys.maxsize` 라서 `2 ** 63` 이 `OverflowError` 인 것 | 문서가 **CPython implementation detail 로 명시** |
| `__len__` 결과에 `__index__` 를 걸어 주는 것 | 실행 — `Indexy` 가 통과했다 |
| `in` 이 `__getitem__` 경로에서 **찾자마자 멈추는** 것 | 실행 로그 — 짧은 회로는 자연스럽지만 횟수는 구현의 것 |
| 예외 **문구** 전부 | 실행 |

### 이 판(3.12.3)의 관찰

| 관찰 | 어디가 흔들리나 |
|---|---|
| `TypeError: argument of type 'C' is not iterable` 와 `TypeError: 'C' object is not iterable` 이 **다른 문구**인 것 | 예외 **종류**는 명세지만 문구는 아니다 |
| `Can't instantiate abstract class Broken without an implementation for abstract methods '__getitem__', '__len__'` | 3.12 에서 바뀐 문구다 |
| `ValueError: __len__() should return >= 0` 문구 | 위와 같다 |
| `ellipsis` 가 **소문자 타입 이름**인 것 | 내부 타입 이름 |
| `__getitem__` 이 `in` 에서 **2번**, `for` 에서 **3번** 불린 것 | 횟수는 결과의 부산물이다 — 대체 **순서**만 명세다 |
| `isinstance(Duck(), Container)` 가 거짓인 것 | `__subclasshook__` 이 어느 ABC 에 붙어 있는지는 라이브러리 구현이다 |

### 그래서 이렇게 적으면 틀린다

- ✗ 「`in` 이 되면 `for` 도 된다」\
  ○ **한 방향뿐이다.** `__contains__` 만 있으면 `in` 만 된다.
- ✗ 「`__getitem__` 만 있으면 `for` 는 안 된다」\
  ○ **돈다.** 0부터 `IndexError` 까지 부른다.
- ✗ 「`isinstance(x, Iterable)` 이 거짓이면 `for` 에 못 넣는다」\
  ○ **넣을 수 있다.** 대체 경로는 그 창에 안 비친다.
- ✗ 「`list(x)` 는 `__iter__` 만 부른다」\
  ○ `__len__` 도 묻는다. **다만 그것은 CPython 의 길이 힌트**이지 언어 보장이 아니다.
- ✗ 「`__len__` 이 음수를 돌려주면 그 값이 그대로 나온다」\
  ○ **`ValueError`** 다. 검사는 `len()` 쪽에 있다.
- ✗ 「`2 ** 63` 이 `OverflowError` 인 것은 언어 규칙이다」\
  ○ **CPython 의 상한**이다. 문서가 구현 세부사항으로 표시한다.
- ✗ 「음수 인덱스는 파이썬이 알아서 뒤에서 세어 준다」\
  ○ **리스트가 하는 일**이다. 내 `__getitem__` 에는 `-1` 이 그대로 온다.
- ✗ 「`x[1:3]` 은 `__getitem__` 을 두 번 부른다」\
  ○ **한 번**이다. `slice` 객체 하나가 인자로 온다.
- ✗ 「`collections.abc` 를 물려받으면 `in` 이 빨라진다」\
  ○ 믹스인 `__contains__` 는 **순회**다. 빨라지려면 덮어써야 한다.
- ✗ 「인스턴스에 `__len__` 을 꽂으면 `len()` 이 바뀐다」\
  ○ **타입에서 찾는다.** 안 바뀐다.

**판정 기준 한 줄**: **「되나?」를 물으면 호출 로그를 보고, 「그 타입인가?」를 물으면 `isinstance` 를 보라. 둘은 같은 질문이 아니다.**

## 언제 쓰고 언제 안 쓰나

| 상황 | 판정 |
|---|---|
| 그냥 `for` 에 넣을 수 있으면 된다 | **`__iter__` 하나.** 제너레이터 함수로 쓰면 가장 짧다 |
| `len()` 과 `if x:` 가 필요하다 | **`__len__` 하나.** 진릿값이 공짜로 따라온다 |
| 인덱싱·슬라이싱이 필요하다 | **`__getitem__`** — 단 `slice`·음수·그 밖의 타입을 **내가 갈라 받는다** |
| `in` 이 자주 불린다 | ★ **`__contains__` 를 반드시 따로 만든다.** 안 만들면 조용히 전수 탐색이다 |
| 제대로 된 시퀀스를 만든다 | **`collections.abc.Sequence` 상속** — 둘만 쓰면 다섯이 따라온다 |
| 빠른 `in` 이 필요한 시퀀스 | `Sequence` 를 물려받고 **`__contains__` 만 덮어쓴다** |
| 읽기 전용으로 두고 싶다 | **`__setitem__`·`__delitem__` 을 안 만든다.** 막는 코드는 필요 없다 |
| 길이 계산이 비싸다 | **`__bool__` 을 따로** 둔다. 안 그러면 `if x:` 한 줄이 비싸진다 |
| 「이터러블인가」를 검사해야 한다 | **`iter(x)` 를 걸고 `TypeError` 를 잡는다.** `hasattr` 도 `isinstance` 도 놓친다 |
| 낡은 `__getitem__` 프로토콜을 새로 쓴다 | **쓰지 않는다.** 읽는 사람이 못 알아본다([16번](../16-iterator-protocol/2-summary.md)과 같은 판정) |

## 핵심 문장

- **컨테이너 프로토콜은 네 창구이고, 닫힌 창구가 있으면 언어가 옆으로 데려간다.** 그 옆길의 순서가 명세다.
- **`in` 은 `__contains__` → `__iter__` → `__getitem__` 으로 떨어지고, `for` 는 `__iter__` → `__getitem__` 둘뿐**이다.
  **대체는 한 방향으로만 흐른다** — `for` 는 `__contains__` 로 못 떨어진다.
- **`__len__` 은 `__bool__` 을 대신하지만 그 반대는 없다.** 둘 다 있으면 `__bool__` 이 이기고 `__len__` 은 안 불린다.
- **`__len__` 이 돌려준 값은 `len()` 이 검사한다** — 음수는 `ValueError`, 정수가 아니면 `TypeError`.
  ★ **터지는 자리가 원인에서 멀다.**
- **대괄호 안은 언제나 한 인자**다 — 콜론은 `slice`, 쉼표는 `tuple`, `...` 은 `Ellipsis`.
  ★ **음수 보정은 언어가 안 한다.**
- **`collections.abc` 는 대체 경로와 다르다** — 대체는 문법을 돌게만 해 주고, ABC 는 `index`·`count` 같은 **진짜 메서드를 붙여** 준다.
- ★★ **ABC 는 이 배치에서 유일하게 앞당겨 터지는 장치다.** 추상 메서드를 안 채우면 **인스턴스를 못 만든다**
  (30·31 은 어겨도 아무 말 없이 자료구조가 틀렸다).
- ★★★ **「돈다」와 「그 타입이다」는 다른 질문이다.** `__getitem__` 만 있는 객체는 `for` 가 도는데 `isinstance(o, Iterable)` 이 거짓이다.

## 관련 자료

- 목록: [python/syntax 주제 목록](../README.md) — 이 주제는 **32번**
- 선행·정본: [16-iterator-protocol](../16-iterator-protocol/2-summary.md) — ★★★ **`__iter__`/`__next__`/`StopIteration` 과 `__getitem__` 낡은 프로토콜의 정본.**\
  **경계**: 그쪽은 「**그 객체가 지켜야 하는 순회 계약**」까지, 여기는 「**네 프로토콜이 서로를 대신하는 격자**」부터다.
  낡은 프로토콜의 동작 자체는 그쪽에서 보고, 여기서는 **`in` 과 `for` 의 우선순위가 다르다는 것**만 더한다.
- 선행: [09-sequence-ops-and-slicing](../09-sequence-ops-and-slicing/2-summary.md) — 내장 시퀀스의 슬라이싱·음수 인덱스.\
  **경계**: 그쪽은 **리스트가 해 주는 일**까지, 여기는 「**내 클래스에서는 그것을 내가 해야 한다**」부터다.
- 함께 보는 곳: [13-set-and-frozenset](../13-set-and-frozenset/2-summary.md) — `set` 의 `in` 이 왜 다른가.\
  **경계**: 해시 기반 `in` 의 비용은 그쪽, 여기는 **`__contains__` 를 안 만들면 순회로 떨어진다**는 것만.
- 함께 보는 곳: [12-dict-and-key-requirements](../12-dict-and-key-requirements/2-summary.md) — 매핑 쪽 `in` 이 **키**를 본다는 것.
- 사슬 앞: [29-classes-and-attribute-lookup](../29-classes-and-attribute-lookup/2-summary.md) — **특수 메서드를 어디서 찾나.**\
  **경계**: 속성 탐색 일반은 그쪽, 여기는 **컨테이너 문법이 타입에서 찾는다는 결론**만 쓴다.
- 사슬 앞: [30-repr-eq-hash-contracts](../30-repr-eq-hash-contracts/2-summary.md) — `in` 이 `==` 로 비교한다는 것.\
  ★ **`__contains__` 를 안 만들면 순회하며 `==` 를 부른다** — 그 `__eq__` 가 틀리면 `in` 도 틀린다.
- 사슬 앞: [31-comparison-protocol-and-sortability](../31-comparison-protocol-and-sortability/2-summary.md) — `sorted(내컨테이너)` 가 이 프로토콜로 원소를 꺼낸 뒤 그쪽 프로토콜로 비교한다.
- 이어지는 곳: [목록의 **33번 주제**](../33-property-descriptor-slots/) 「`property`·디스크립터·`__slots__`」 — 속성 쪽 가로채기.
- 이어지는 곳: [목록의 **35번 주제**](../35-abc-and-protocol/) 「추상 베이스 클래스와 `Protocol`」 — ★ `collections.abc` 와 `typing.Protocol` 중 무엇을 고르나가 그쪽 정본이다.
- 이어지는 곳: 목록의 **43번 주제** 「`collections`」 — `UserList`·`UserDict` 로 내장을 물려받는 길.
- 원리: [`cs/data-structure/`](../../../../../data-structure/) — 시퀀스·해시 자료구조의 원리와 복잡도는 그쪽이 정본이다.
- 공식 문서: [3.3.7 Emulating container types](https://docs.python.org/3.12/reference/datamodel.html#emulating-container-types) · [Membership test operations](https://docs.python.org/3.12/reference/expressions.html#membership-test-operations) · [`collections.abc`](https://docs.python.org/3.12/library/collections.abc.html)

## 용어 풀이

- **컨테이너 프로토콜(container protocol)**: 내장 문법이 어느 특수 메서드를 부를지 정해 둔 약속.\
  예: `len(x)` 는 `type(x).__len__(x)` 를 부른다.
- **특수 메서드(special method / dunder)**: 이름 앞뒤에 밑줄 둘이 붙은 메서드. 언어 문법이 부르는 자리.\
  예: `__len__`·`__getitem__`. **인스턴스가 아니라 타입에서 찾는다.**
- **대체 경로(fallback)**: 찾던 특수 메서드가 없을 때 언어가 대신 쓰는 다른 메서드.\
  예: `__contains__` 가 없으면 `in` 이 순회로 떨어진다.
- **멤버십 검사(membership test)**: `in`·`not in` 연산. 세 단계 대체 순서가 문서에 적혀 있다.
- **진릿값 검사(truth value testing)**: `if x:`·`not x` 가 객체를 참·거짓으로 판정하는 것.\
  예: `__bool__` → `__len__` → **무조건 참** 순서다.
- **`slice` 객체**: `a:b:c` 표기가 만드는 객체. `start`·`stop`·`step` 세 칸을 가진다.\
  예: `x[1:5]` 는 `__getitem__(slice(1, 5, None))` 이다.
- **`slice.indices(길이)`**: 그 길이에 맞춰 잘라낸 `(start, stop, step)` 을 돌려주는 메서드.\
  예: `range(*s.indices(5))` 로 순회할 인덱스를 얻는다.
- **`Ellipsis`**: `...` 표기가 가리키는 내장 객체. 타입 이름이 `ellipsis` 로 소문자다.
- **믹스인(mixin)**: 몇 개만 구현하면 나머지를 만들어 주는 메서드 묶음.\
  예: `Sequence` 에 `__len__`·`__getitem__` 을 주면 `index`·`count` 가 따라온다.
- **추상 베이스 클래스(ABC, abstract base class)**: 「이것은 반드시 구현해라」를 강제하는 부모 클래스.\
  예: 안 채우면 **인스턴스를 만들 때** `TypeError` 가 난다.
- **`__subclasshook__`**: 상속·등록 없이도 `isinstance` 를 참으로 만드는 갈고리.\
  예: `Iterable` 은 `__iter__` 하나만 보고 참을 낸다. **`Sequence` 에는 그런 갈고리가 없다.**
- **길이 힌트(length hint)**: 결과 컨테이너의 크기를 미리 잡으려고 **묻기만 하는** 길이.\
  예: `list(x)` 가 `__len__` 을 한 번 더 부르는 것. **CPython 의 구현이다.**
- **오리 타입(duck typing)**: 「이 메서드가 있으면 그것으로 친다」는 판정 방식.\
  예: `__iter__` 만 있으면 `Iterable` 로 쳐 주는 것. ★ **범위가 좁다** — `Sequence` 는 안 쳐 준다.

## 더 들어가면

- **매핑 쪽 프로토콜**은 같은 `__getitem__` 을 쓰지만 `in` 이 **키**를 본다.
  `Mapping` ABC 를 물려받으면 `keys`·`items`·`values`·`get`·`__eq__` 까지 따라온다([12번](../12-dict-and-key-requirements/2-summary.md)).
- **`__missing__`** 은 `dict` 하위 클래스에서만 불리는 갈고리다 — `defaultdict` 가 그 위에 서 있다(목록의 **43번 주제**).
- **`__length_hint__`** 는 `__len__` 이 없는 이터레이터가 「대충 몇 개 남았다」를 알려 주는 창이다.
  ★ **보장이 아니다** — 정본은 [16번](../16-iterator-protocol/2-summary.md)이다.
- **`__getitem__` 이 제네릭 문법에도 쓰인다** — `list[int]` 는 `type.__getitem__` 이고,
  내 클래스에 `__class_getitem__` 을 두면 `MyBox[int]` 가 된다(PEP 560, 목록의 **41번 주제**).
- **`UserList`·`UserDict`** 는 내장을 상속할 때 생기는 문제(내부 메서드가 서로를 안 부르는 것)를 피하려고 만든 래퍼다(목록의 **43번 주제**).
- **`typing.Protocol`** 은 `collections.abc` 와 달리 **상속 없이** 구조로만 맞추는 길이다.
  런타임 강제 여부가 갈리는 지점은 [목록의 **35번 주제**](../35-abc-and-protocol/)가 정본이다.
- ★ **비동기 판**은 `__aiter__`/`__anext__` 이고 `async for` 가 그것을 쓴다(PEP 492, 목록의 **51번 주제**).
  ★ **비동기에는 `__getitem__` 대체 경로가 없다** — 낡은 프로토콜은 동기 쪽에만 남아 있는 유산이다.
