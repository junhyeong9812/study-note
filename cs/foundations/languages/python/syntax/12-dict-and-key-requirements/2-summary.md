# python/syntax/12-dict-and-key-requirements — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만.
> - [Mapping Types — dict](https://docs.python.org/3.12/library/stdtypes.html#mapping-types-dict) — 키 요건 · 삽입 순서 · `|`/`|=` · 뷰
> - [Dictionary view objects](https://docs.python.org/3.12/library/stdtypes.html#dict-views) — 「**동적 뷰**」와 순회 중 변경
> - [glossary — hashable](https://docs.python.org/3.12/glossary.html#term-hashable) — 해시 가능의 정의
> - [`object.__hash__`](https://docs.python.org/3.12/reference/datamodel.html#object.__hash__) — `__eq__` 를 재정의하면 `__hash__` 가 `None` 이 되는 규칙
> - [What's New In Python 3.6 — New dict implementation](https://docs.python.org/3.12/whatsnew/3.6.html#new-dict-implementation) · [What's New In Python 3.7](https://docs.python.org/3.12/whatsnew/3.7.html) — ★ **순서 보장이 층을 옮긴 자리**
> - [`collections.defaultdict`](https://docs.python.org/3.12/library/collections.html#collections.defaultdict) · [`collections.OrderedDict`](https://docs.python.org/3.12/library/collections.html#collections.OrderedDict)
> - [PYTHONHASHSEED](https://docs.python.org/3.12/using/cmdline.html#envvar-PYTHONHASHSEED) — 무엇이 무작위화되나
>
> **실행 검증** — 이 문서에 실린 출력은 전부 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> 일부는 **3.11.15** 로 한 번 더 돌려 대조했고, 그 사실을 그 자리에 적었다.
> **버전** — 삽입 순서 보장은 **3.7**(3.6 은 CPython 구현 세부) · 병합 연산자 `|`/`|=` 는 **3.9** · 뷰의 `reversed()` 는 **3.8**.
> **선행** — [02-is-vs-eq-interning](../02-is-vs-eq-interning/2-summary.md)(`is` 와 `==` 의 정본) ·
> [11-tuple-and-unpacking](../11-tuple-and-unpacking/2-summary.md)(튜플이 키가 되는 조건) ·
> [03-mutability-and-copying](../03-mutability-and-copying/2-summary.md)(불변 안의 가변).

## 한눈에 — 쉽게 말하면

**dict 는 「이름표가 붙은 사물함」이다. 이름표를 거는 자리는 해시가 정하고, 순서는 「들어온 순서」로 따로 적어 둔다.**

```text
   넣은 순서를 적어 두는 줄                해시가 정하는 칸
   +---+---+---+                       +----+----+----+----+----+----+----+----+
   | 0 | 1 | 2 |  ...                  |    | #2 |    | #0 |    |    | #1 |    |
   +---+---+---+                       +----+----+----+----+----+----+----+----+
     |   |   |                            찾을 때는 이쪽만 본다 (평균 한 번에)
     v   v   v
    "c" "a" "b"   <- 돌 때는 이쪽만 본다 (넣은 순서 그대로)
```

★ **찾는 길과 도는 길이 다르다.** 그래서 「순서가 있다」와 「해시로 찾는다」가 한 자료구조 안에 같이 있다.\
`set` 은 **앞의 줄이 없다** — 그래서 순서가 없다([13번](../13-set-and-frozenset/2-summary.md)).

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 이름표를 걸 칸을 해시가 정한다 | `hash(key)` | `hash(1) == hash(1.0) == hash(True)` |
| 이름표가 같은지는 눈으로 한 번 더 본다 | `__eq__` | 해시가 같아도 `==` 가 다르면 딴 칸 |
| 넣은 순서를 따로 적어 둔다 | 삽입 순서 보장(3.7+) | `list(d)` |
| 이름표를 바꿔 달아도 자리는 그대로 | `d[k] = v` 재대입 | 순서가 안 바뀐다 |
| 뺐다가 다시 걸면 줄 맨 뒤 | `del` 후 재삽입 | 순서가 맨 뒤로 |
| 사물함을 들여다보는 창 | `d.keys()`·`values()`·`items()` | 원본이 바뀌면 창도 바뀐다 |
| 창을 들여다보는 중에 칸 수를 바꾸면 | 순회 중 `del`·추가 | `RuntimeError` **또는 조용히 빠뜨림** |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.\
「**`1` 로 넣었는데 `True` 로 덮어써졌다**」가 그것이다. `{1: "정수", True: "불리언"}` 은 **칸이 하나**다.
에러는 안 난다.

> **해시 가능(hashable)** — 문서의 정의는 셋이다.\
> **① 평생 안 바뀌는 해시값이 있다**(`__hash__`) **② 다른 객체와 비교할 수 있다**(`__eq__`)
> **③ `==` 인 것끼리는 해시값이 같다.**\
> 이 셋이 있어야 dict 의 키·set 의 원소가 될 수 있다.

## 이 주제가 답하려는 질문

1. **dict 의 순서는 누가 약속하는가** — 언어인가 CPython 인가. 그리고 **언제 바뀌었는가.**
2. **무엇이 키가 될 수 있는가** — `hash()` 와 `__eq__` 가 각각 어떤 일을 하고, `1`·`1.0`·`True` 가 왜 한 칸인가.
3. **뷰는 사본인가** — `d.keys()` 를 받아 두고 원본을 바꾸면 무슨 일이 나는가.

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 문장으로 읽는다.

### 1. ★ 삽입 순서 — 세 층 사이를 실제로 옮겨 다닌 사실

**언제 쓰나** — dict 를 `for` 로 돌 때마다. 그리고 「순서에 기대도 되나」를 판단할 때.

이 주제가 **「세 층」의 가장 좋은 본보기**인 이유는, 같은 사실이 **판을 건너 층을 옮겼기** 때문이다.

```text
  Python 3.5 이하   순서가 없다 (돌 때마다 달라질 수 있다)
        |
        v
  Python 3.6        CPython 이 새 dict 구조로 순서를 지키게 됐다
                    ★ 그러나 "구현 세부사항이며 기대면 안 된다" 고 문서가 못 박았다
        |
        v
  Python 3.7        "언어 명세의 공식 일부" 로 선언됐다
                    ★ 같은 동작이 CPython 구현 -> 언어 보장 으로 승격
```

3.6 의 릴리스 문서가 **기대지 말라고** 직접 적는다 —
*"The order-preserving aspect of this new implementation is **considered an implementation detail and should not be relied upon**
(this may change in the future, but it is desired to have this new dict implementation in the language for a few releases
before changing the language spec to mandate order-preserving semantics …)"*

3.7 의 릴리스 문서가 **승격을 선언한다** —
*"the insertion-order preservation nature of dict objects **has been declared to be an official part of the Python language spec**."*

그리고 지금의 라이브러리 레퍼런스가 그 결과를 이렇게 적는다 —
*"Dictionaries preserve insertion order. Note that **updating a key does not affect the order**.
**Keys added after deletion are inserted at the end**."* / *"Changed in version 3.7: Dictionary order is guaranteed to be insertion order.
**This behavior was an implementation detail of CPython from 3.6**."*

★ **마지막 문장이 이 주제의 핵심이다** — 문서가 「이건 3.6 에서는 구현 세부였다」를 **스스로 기록해 두었다.**

```python
import sys
print("sys.version_info =", sys.version_info)
d = {}
d["c"] = 1; d["a"] = 2; d["b"] = 3
print("세 번 넣고 출력     :", d, "|", list(d))
d["c"] = 99
print("있는 키에 다시 대입 :", list(d))
del d["c"]; d["c"] = 1
print("지우고 다시 넣으면  :", list(d))
print("== 는 순서를 안 본다:", {"a":1,"b":2} == {"b":2,"a":1})
print("list()는 순서를 본다:", list({"a":1,"b":2}) == list({"b":2,"a":1}))
print("reversed(d)         :", list(reversed(d)))
print("popitem()           :", dict(x=1,y=2,z=3).popitem())
```

```text
sys.version_info = sys.version_info(major=3, minor=12, micro=3, releaselevel='final', serial=0)
세 번 넣고 출력     : {'c': 1, 'a': 2, 'b': 3} | ['c', 'a', 'b']
있는 키에 다시 대입 : ['c', 'a', 'b']
지우고 다시 넣으면  : ['a', 'b', 'c']
== 는 순서를 안 본다: True
list()는 순서를 본다: False
reversed(d)         : ['c', 'b', 'a']
popitem()           : ('z', 3)
```

그림 해설.

- **넣은 순서 그대로** 나온다. `'c'` 가 첫 자리다.
- ★ **값만 바꾸면 자리는 안 움직인다.** `d["c"] = 99` 뒤에도 `'c'` 가 맨 앞이다.
- ★ **지웠다가 다시 넣으면 맨 뒤**다. 「덮어쓰기」와 「지우고 넣기」가 **순서에서 다르다.**
- **`==` 는 순서를 안 본다.** 문서가 *"Dictionaries compare equal if and only if they have the same `(key, value)` pairs (**regardless of ordering**)"* 라고 적는다.
  **그래서 테스트가 순서 사고를 안 잡아 준다** — `list(d)` 로 비교해야 잡힌다.
- `reversed(d)` 는 **3.8** 부터다. `popitem()` 은 **마지막 것**을 뺀다(3.7 부터 LIFO 로 명세).

★ **시드를 바꿔도 dict 순서는 안 갈린다** — 순서가 해시에서 오지 않기 때문이다([13번](../13-set-and-frozenset/2-summary.md)의 `set` 과 정확히 반대다).

```bash
for seed in 0 1 2; do PYTHONHASHSEED=$seed python3 -c \
  'd={};[d.setdefault(k,i) for i,k in enumerate(["cherry","apple","banana","date"])];print("seed:",list(d))'; done
```

```text
seed: ['cherry', 'apple', 'banana', 'date']
seed: ['cherry', 'apple', 'banana', 'date']
seed: ['cherry', 'apple', 'banana', 'date']
```

**비용** — 순서를 적어 두는 줄이 따로 있으니 **메모리를 조금 더** 쓰고, 그 대가로 삽입 순서 순회가 공짜다.

### 2. ★ 키가 되는 조건 — `hash()` 와 `__eq__` 는 한 쌍이다

**언제 쓰나** — 내 클래스를 키·원소로 쓸 때. 그리고 「왜 리스트는 키가 안 되나」를 설명할 때.

```text
  d[key] 를 찾는 두 단계

   1) hash(key)  ->  어느 칸을 볼지 정한다        (빠른 1차 선별)
   2) 그 칸의 키와 ==  ->  진짜 같은 것인지 확인    (정확한 2차 확인)

   ★ 1) 만으로는 못 정한다. 다른 값이 같은 칸에 올 수 있기 때문이다.
   ★ 그래서 "== 인 것은 hash 도 같아야 한다" 가 계약이 된다.
     (거꾸로 hash 가 같은데 == 가 다른 것은 합법이다 — 그냥 느려질 뿐이다)
```

문서가 셋을 다 적는다 — *"An object is hashable if it has a hash value which **never changes during its lifetime**
(it needs a `__hash__()` method), and **can be compared to other objects** (it needs an `__eq__()` method).
**Hashable objects which compare equal must have the same hash value.**"*

```python
class Plain:
    def __init__(self, v): self.v = v

class OnlyEq:
    def __init__(self, v): self.v = v
    def __eq__(self, o): return isinstance(o, OnlyEq) and self.v == o.v

class Both:
    def __init__(self, v): self.v = v
    def __eq__(self, o): return isinstance(o, Both) and self.v == o.v
    def __hash__(self): return hash(self.v)
    def __repr__(self): return f"Both({self.v})"

class Liar:
    def __init__(self, v): self.v = v
    def __eq__(self, o): return isinstance(o, Liar) and self.v == o.v
    def __hash__(self): return 0            # 늘 같은 해시 — 합법이다
    def __repr__(self): return f"Liar({self.v})"

p1, p2 = Plain(1), Plain(1)
print("Plain  : __hash__ =", Plain.__hash__ is not None, "| p1 == p2 :", p1 == p2, "| 키 2개:", len({p1: 0, p2: 0}))
print("OnlyEq : __hash__ =", OnlyEq.__hash__)
try:
    {OnlyEq(1): 0}
except TypeError as e:
    print("         {OnlyEq(1):0} -> TypeError:", e)
b1, b2 = Both(1), Both(1)
print("Both   : 키 몇 개 :", {b1: "첫째", b2: "둘째"}, "| len =", len({b1: 0, b2: 0}))
l1, l2 = Liar(1), Liar(2)
print("Liar   : 해시가 같아도 == 가 다르면 둘 :", {l1: "a", l2: "b"}, "| len =", len({l1: 0, l2: 0}))
print("불변이어도 안에 가변이 있으면 :", end=" ")
try:
    {(1, [2]): 0}
except TypeError as e:
    print("TypeError:", e)
print("내장 타입의 __hash__ :", [t.__name__ for t in (int, str, tuple, frozenset, list, dict, set) if t.__hash__ is not None])
print("해시 못 하는 내장    :", [t.__name__ for t in (int, str, tuple, frozenset, list, dict, set) if t.__hash__ is None])
```

```text
Plain  : __hash__ = True | p1 == p2 : False | 키 2개: 2
OnlyEq : __hash__ = None
         {OnlyEq(1):0} -> TypeError: unhashable type: 'OnlyEq'
Both   : 키 몇 개 : {Both(1): '둘째'} | len = 1
Liar   : 해시가 같아도 == 가 다르면 둘 : {Liar(1): 'a', Liar(2): 'b'} | len = 2
불변이어도 안에 가변이 있으면 : TypeError: unhashable type: 'list'
내장 타입의 __hash__ : ['int', 'str', 'tuple', 'frozenset']
해시 못 하는 내장    : ['list', 'dict', 'set']
```

그림 해설.

- **`Plain`** — 아무것도 정의 안 하면 `object` 의 것을 물려받아 **정체(identity) 기준**이다. 값이 같아도 **딴 키**다.
- ★ **`OnlyEq`** — `__eq__` 만 정의하면 **`__hash__` 가 `None` 으로 꺼진다.**
  문서가 그 규칙을 직접 적는다 — *"A class that overrides `__eq__` and does not define `__hash__`
  will have its `__hash__` **implicitly set to None**."*
  **이것이 「계약이 언어에 박힌」 자리다** — 잊어버리는 게 아니라 언어가 꺼 버린다.
- **`Both`** — 둘 다 주면 **값이 같으면 한 칸**이다. 그리고 **남은 키는 처음 것**(`Both(1)`), **값은 나중 것**(`'둘째'`)이다.
- ★ **`Liar`** — 해시가 늘 `0` 인데도 **합법**이다. 계약은 「`==` 면 해시가 같다」 한 방향뿐이다.
  거꾸로는 요구하지 않는다 — **느려질 뿐 틀리지는 않는다.**
- **`(1, [2])`** — 튜플은 불변인데도 못 쓴다. **오류가 `tuple` 이 아니라 `list` 를 가리킨다**([11번](../11-tuple-and-unpacking/2-summary.md)).

**비용** — 찾기가 평균 한 번이다(해시가 고르게 퍼진다는 전제에서). `Liar` 처럼 해시가 뭉치면 **선형으로 떨어진다.**

### 3. ★ 같은 값이면 한 칸 — `1`·`1.0`·`True`

**언제 쓰나** — 키가 숫자일 때. JSON·CSV 에서 읽은 값을 키로 쓸 때.

문서가 이것도 직접 적는다 —
*"Values that compare equal (such as `1`, `1.0`, and `True`) **can be used interchangeably to index the same dictionary entry**."*

```python
print("hash :", hash(1), hash(1.0), hash(True), hash(1+0j))
print("==   :", 1 == 1.0 == True == (1+0j))
d = {1: "정수", 1.0: "실수", True: "불리언"}
print("d          =", d)
print("len(d)     =", len(d))
print("키의 타입  =", [type(k).__name__ for k in d])
d2 = {True: "먼저 불리언", 1: "나중 정수"}
print("d2         =", d2, "| 키 타입:", [type(k).__name__ for k in d2])
print("d2[1.0]    =", d2[1.0])
print("0 과 False :", {0: "영", False: "거짓"})
print("1 과 1+0j  :", {1: "정수", 1+0j: "복소"})
print("'1' 은 다르다:", {1: "정수", "1": "문자열"})
print("Fraction/Decimal :")
from fractions import Fraction
from decimal import Decimal
print("  hash(Fraction(1,1)) =", hash(Fraction(1, 1)), "| hash(Decimal('1')) =", hash(Decimal("1")))
print("  {1:'a', Fraction(1,1):'b', Decimal('1'):'c'} =", {1: "a", Fraction(1, 1): "b", Decimal("1"): "c"})
print("  Decimal('1.0') == 1 :", Decimal("1.0") == 1, "| hash =", hash(Decimal("1.0")))
```

```text
hash : 1 1 1 1
==   : True
d          = {1: '불리언'}
len(d)     = 1
키의 타입  = ['int']
d2         = {True: '나중 정수'} | 키 타입: ['bool']
d2[1.0]    = 나중 정수
0 과 False : {0: '거짓'}
1 과 1+0j  : {1: '복소'}
'1' 은 다르다: {1: '정수', '1': '문자열'}
Fraction/Decimal :
  hash(Fraction(1,1)) = 1 | hash(Decimal('1')) = 1
  {1:'a', Fraction(1,1):'b', Decimal('1'):'c'} = {1: 'c'}
  Decimal('1.0') == 1 : True | hash = 1
```

그림 해설.

```text
  {1: "정수",  1.0: "실수",  True: "불리언"}

    hash(1)=1   hash(1.0)=1   hash(True)=1     같은 칸
    1 == 1.0 == True                           같은 키

   ->  칸은 하나.  남는 키는 "처음 들어간 것",  값은 "마지막에 쓴 것"

       {1: '불리언'}       <- 키는 int 1,  값은 True 로 쓴 것
```

- ★ **키는 처음 것이 남고 값은 나중 것이 이긴다.** 두 규칙이 **반대 방향**이라 헷갈린다.
- ★ **`{True: ..., 1: ...}` 는 키 타입이 `bool`** 이다 — 먼저 들어간 것이 `True` 였기 때문이다.
  `json.dumps` 로 내보내면 `"true"` 가 나온다. **숫자 키를 썼다고 믿은 코드가 여기서 조용히 어긋난다.**
- **`1+0j`·`Fraction(1,1)`·`Decimal("1")`·`Decimal("1.0")` 도 전부 같은 칸**이다.
  파이썬의 수 타입은 「값이 같으면 해시가 같다」를 **타입을 가로질러** 지키기 때문이다.
- **`"1"` 은 다르다.** 문자열은 수와 `==` 가 아니다.
- **`0` 과 `False` 도 같은 칸**이다.

**비용** — 숫자 키가 섞인 자료에서는 **키를 명시적으로 정규화**해야 한다(`str(k)` 나 `int(k)` 로 한 번 통일).

### 4. ★ 뷰는 사본이 아니다 — 원본을 바꾸면 따라 변한다

**언제 쓰나** — `d.keys()` 를 변수에 담을 때. 함수에 넘길 때.

문서 — *"The objects returned by `dict.keys()`, `dict.values()` and `dict.items()` are view objects.
They provide a **dynamic view on the dictionary's entries**, which means that **when the dictionary changes, the view reflects these changes**."*

```text
   ks = d.keys()        ks 는 사본이 아니라 "창" 이다

   d  +---------+                 ks  ---> (d 를 그대로 들여다본다)
      | a b     |
      +---------+
   d["c"]=3 하면
      +---------+                 ks  ---> a b c   (따라 변한다)
      | a b c   |
      +---------+
```

```python
d = {"a": 1, "b": 2}
ks, vs, its = d.keys(), d.values(), d.items()
print("뷰를 먼저 받아 두고 :", ks, vs, its)
d["c"] = 3
print("원본에 c 를 넣은 뒤 :", ks, vs, its)
del d["a"]
print("원본에서 a 를 지운 뒤:", ks, vs, its)
print("len 도 따라 변한다   :", len(ks))
print("타입                :", type(ks).__name__, type(vs).__name__, type(its).__name__)
print("리스트가 아니다      :", isinstance(ks, list))
try:
    ks[0]
except TypeError as e:
    print("ks[0]               -> TypeError:", e)
print("keys 는 집합처럼 쓴다 :", sorted(d.keys() & {"b", "z"}), sorted(d.keys() | {"z"}), sorted(d.keys() - {"b"}), sorted(d.keys() ^ {"b", "z"}))
print("items 도 집합 연산   :", d.items() & {("b", 2), ("b", 9)})
try:
    d.values() & {1}
except TypeError as e:
    print("values() & {1}      -> TypeError:", e)
print("values 는 == 도 이상 :", {"a": 1}.values() == {"a": 1}.values())
```

```text
뷰를 먼저 받아 두고 : dict_keys(['a', 'b']) dict_values([1, 2]) dict_items([('a', 1), ('b', 2)])
원본에 c 를 넣은 뒤 : dict_keys(['a', 'b', 'c']) dict_values([1, 2, 3]) dict_items([('a', 1), ('b', 2), ('c', 3)])
원본에서 a 를 지운 뒤: dict_keys(['b', 'c']) dict_values([2, 3]) dict_items([('b', 2), ('c', 3)])
len 도 따라 변한다   : 2
타입                : dict_keys dict_values dict_items
리스트가 아니다      : False
ks[0]               -> TypeError: 'dict_keys' object is not subscriptable
keys 는 집합처럼 쓴다 : ['b'] ['b', 'c', 'z'] ['c'] ['c', 'z']
items 도 집합 연산   : {('b', 2)}
values() & {1}      -> TypeError: unsupported operand type(s) for &: 'dict_values' and 'set'
values 는 == 도 이상 : False
```

★ **`keys()`·`items()` 는 집합처럼 쓸 수 있고 `values()` 는 못 쓴다.**
값은 중복될 수 있고 해시 가능하다는 보장도 없기 때문이다. 같은 이유로 **`values()` 끼리의 `==` 는 언제나 `False`** 다
(원소 비교가 아니라 `object` 의 정체 비교로 떨어진다).

★ **뷰는 첨자를 못 쓴다.** `ks[0]` 이 `TypeError` 다 — 「첫 키」가 필요하면 `next(iter(d))` 나 `list(d)[0]`.

**비용** — 뷰는 **원소를 복사하지 않는다.** 큰 dict 에서 `list(d.keys())` 를 습관적으로 쓰면 그만큼을 새로 만든다.\
대신 **원본이 바뀌면 같이 바뀐다** — 「그 시점의 키 목록」이 필요하면 **일부러 `list()` 로 떠야** 한다.

### 5. ★ 순회 중 변경 — `RuntimeError`, 그리고 그보다 나쁜 것

**언제 쓰나** — `for k in d:` 안에서 `d` 를 건드릴 때. **여기가 이 주제에서 가장 위험한 자리다.**

문서가 **두 갈래**를 다 적는다 —
*"Iterating views while adding or deleting entries in the dictionary **may raise a RuntimeError or fail to iterate over all entries**."*

★ **뒤엣말이 핵심이다.** 「예외가 난다」만 외우면 **조용한 쪽을 놓친다.**

**(가) 크기가 변하면 — `RuntimeError`**

```text
===== 소스 (python3 - <<'PY') =====
d = {"a": 1, "b": 2, "c": 3}
for k in d:
    if k == "a":
        d["d"] = 4
```

```text
Traceback (most recent call last):
  File "<stdin>", line 2, in <module>
RuntimeError: dictionary changed size during iteration
```

지우는 쪽도 같다.

```text
===== 소스 (python3 - <<'PY') =====
d = {"a": 1, "b": 2, "c": 3}
for k in d:
    if k == "a":
        del d[k]
```

```text
Traceback (most recent call last):
  File "<stdin>", line 2, in <module>
RuntimeError: dictionary changed size during iteration
```

★ **터지는 줄이 `for k in d:` 다.** `del` 한 줄이 아니라 **다음 원소를 꺼내는 순간** 잡힌다.

**(나) ★ 크기가 그대로면 — 아무 일도 안 난다. 그리고 결과가 틀린다**

```python
d = {"a": 1, "b": 2, "c": 3}
for k in d:
    if k == "a":
        del d["c"]
        d["z"] = 9        # 지운 만큼 다시 넣어 크기가 같다
    print("돌았다:", k)
print("끝:", d)
```

```text
돌았다: a
돌았다: b
돌았다: z
끝: {'a': 1, 'b': 2, 'z': 9}
```

★ **`'c'` 를 한 번도 안 돌았고, 넣지도 않은 `'z'` 를 돌았다. 예외는 없었다.**\
검사가 보는 것은 **크기뿐**이기 때문이다. 이것이 문서가 말한 *"fail to iterate over all entries"* 다.

**(다) 값만 바꾸는 것은 안전하다 · 열쇠를 먼저 떠내면 안전하다**

```python
d = {"a": 1, "b": 2, "c": 3}
for k in d:
    d[k] = 0          # 값만 바꾼다
print("값만 바꾸면 :", d)
d2 = {"a": 1, "b": 2, "c": 3}
for k in list(d2):    # 열쇠를 먼저 떠낸다
    if k == "a":
        del d2[k]
print("list(d2) 로 뜨면 :", d2)
```

```text
값만 바꾸면 : {'a': 0, 'b': 0, 'c': 0}
list(d2) 로 뜨면 : {'b': 2, 'c': 3}
```

**뷰에서 꺼낸 이터레이터도 같은 규칙을 탄다.**

```text
===== 소스 (python3 - <<'PY') =====
d = {"a": 1, "b": 2}
ks = d.keys()
it = iter(ks)
print(next(it))
d["c"] = 3
print(next(it))
```

```text
a
Traceback (most recent call last):
  File "<stdin>", line 6, in <module>
RuntimeError: dictionary changed size during iteration
```

**비용** — `list(d)` 를 뜨면 키 개수만큼 메모리를 더 쓴다. **그 값으로 사는 것이 「빠뜨리지 않음」이다.**

### 6. `get` · `setdefault` · `defaultdict` — 어느 것이 키를 만드나

**언제 쓰나** — 없는 키를 다룰 때. 「묶기(grouping)」를 짤 때.

```text
  d.get(k)              없으면 None.  ★ 키를 안 만든다
  d.get(k, 기본)         없으면 기본.  ★ 키를 안 만든다
  d.setdefault(k, 기본)  없으면 넣고 그 값을 돌려준다.  ★ 키를 만든다
  defaultdict(list)[k]  없으면 만들어 넣고 돌려준다.    ★ 조회만 해도 키를 만든다
  defaultdict(list).get(k)  ★ 안 만든다  (get 은 __missing__ 을 안 탄다)
```

```python
from collections import defaultdict
d = {"a": 1}
print("get 없는 키        :", d.get("z"), "|", d.get("z", 0))
print("get 은 키를 안 만든다:", d)
print("setdefault 있는 키  :", d.setdefault("a", 99), "|", d)
print("setdefault 없는 키  :", d.setdefault("z", 0), "|", d, " <- 키가 생겼다")

groups = {}
for name, dept in [("김", "영업"), ("이", "개발"), ("박", "영업")]:
    groups.setdefault(dept, []).append(name)
print("setdefault 로 묶기 :", groups)

dd = defaultdict(list)
for name, dept in [("김", "영업"), ("이", "개발"), ("박", "영업")]:
    dd[dept].append(name)
print("defaultdict 로 묶기:", dict(dd))
print("★ 조회만 해도 키가 생긴다:", dd["없는부서"], "|", dict(dd))
print("  get 은 안 만든다        :", dd.get("또없는부서"), "|", list(dd))
print("  in 도 안 만든다         :", "세번째" in dd, "|", list(dd))
print("defaultdict 는 dict 인가:", isinstance(dd, dict), type(dd).__mro__[:3])
```

```text
get 없는 키        : None | 0
get 은 키를 안 만든다: {'a': 1}
setdefault 있는 키  : 1 | {'a': 1}
setdefault 없는 키  : 0 | {'a': 1, 'z': 0}  <- 키가 생겼다
setdefault 로 묶기 : {'영업': ['김', '박'], '개발': ['이']}
defaultdict 로 묶기: {'영업': ['김', '박'], '개발': ['이']}
★ 조회만 해도 키가 생긴다: [] | {'영업': ['김', '박'], '개발': ['이'], '없는부서': []}
  get 은 안 만든다        : None | ['영업', '개발', '없는부서']
  in 도 안 만든다         : False | ['영업', '개발', '없는부서']
defaultdict 는 dict 인가: True (<class 'collections.defaultdict'>, <class 'dict'>, <class 'object'>)
```

- ★ **`setdefault` 는 이름이 거짓말이다.** 「기본값을 정한다」가 아니라 「**없으면 넣고 어쨌든 돌려준다**」다.
- ★ **`setdefault(k, [])` 는 없는 키에도 빈 리스트를 매번 만든다** — 있는 키일 때도 인자는 평가된다.
  `defaultdict` 는 **없을 때만** 팩토리를 부른다.
- ★★ **`defaultdict` 는 조회만 해도 키가 생긴다.** 오타 한 번이 키를 늘린다.
  `dd.get(k)` 와 `k in dd` 는 안 만든다 — **읽기만 할 때는 이 둘을 쓴다.**
- 자세한 것은 목록의 **43번 주제**(`collections`)가 정본이다. 여기서는 **「키를 만드나」까지**다.

**비용** — `setdefault` 는 조회 한 번, `dd[k]` 도 한 번. `if k not in d: d[k] = []` 는 **두 번** 본다.

### 7. 병합 — `|` · `|=` · `{**a, **b}` · `update`

**언제 쓰나** — 기본 설정 위에 사용자 설정을 얹을 때.

```python
a = {"x": 1, "y": 2}
b = {"y": 20, "z": 30}
print("a | b     :", a | b, " <- 오른쪽이 이긴다")
print("b | a     :", b | a)
print("{**a,**b} :", {**a, **b})
print("a 는 그대로:", a)
c = dict(a)
c |= b
print("c |= b    :", c)
c2 = dict(a)
c2 |= [("k", 9), ("y", 0)]
print("|= 는 이터러블도 :", c2)
try:
    a | [("k", 9)]
except TypeError as e:
    print("a | [...]  -> TypeError:", e)
u = dict(a); u.update(b)
print("update    :", u)
```

```text
a | b     : {'x': 1, 'y': 20, 'z': 30}  <- 오른쪽이 이긴다
b | a     : {'y': 2, 'z': 30, 'x': 1}
{**a,**b} : {'x': 1, 'y': 20, 'z': 30}
a 는 그대로: {'x': 1, 'y': 2}
c |= b    : {'x': 1, 'y': 20, 'z': 30}
|= 는 이터러블도 : {'x': 1, 'y': 0, 'k': 9}
a | [...]  -> TypeError: unsupported operand type(s) for |: 'dict' and 'list'
update    : {'x': 1, 'y': 20, 'z': 30}
```

★ **`b | a` 를 보라 — `y` 가 첫 자리에 있는데 값은 `2`다.**

```text
  b | a   에서 y 가 겪는 일

    자리(순서)  <- 왼쪽 b 의 것을 따른다        y 는 0번 자리
    값          <- 오른쪽 a 의 것이 이긴다      y 는 2

   ->  {'y': 2, 'z': 30, 'x': 1}
```

**「자리는 왼쪽, 값은 오른쪽」** — 이것이 「지우고 다시 넣기가 아니라 덮어쓰기」라서 생기는 결과다(동작 1).

| 쓰는 법 | 새 dict 를 만드나 | 오른쪽에 무엇을 받나 | 버전 |
|---|---|---|---|
| `a \| b` | 만든다 | **dict 만** | 3.9 |
| `a \|= b` | 아니다(a 를 고친다) | dict **또는 (키, 값) 이터러블** | 3.9 |
| `{**a, **b}` | 만든다 | **매핑**(`keys()` 가 있으면 됨) | 3.5 |
| `a.update(b)` | 아니다 | dict · 이터러블 · **키워드 인자** | 오래됨 |

★ **`|` 와 `|=` 가 받는 것이 다르다** — 문서가 `|` 쪽에만 *"which must both be dictionaries"* 라고 적는다.\
★ **병합은 전부 얕다.** 값이 dict 면 **통째로 교체**된다 — 중첩 설정 병합에는 못 쓴다.

**컴파일된 모양도 다르다**(구현).

```python
import dis
print("===== 소스: c = a | b =====")
dis.dis(compile("c = a | b", "<merge>", "exec"))
print("===== 소스: c = {**a, **b} =====")
dis.dis(compile("c = {**a, **b}", "<unpack>", "exec"))
```

```text
===== 소스: c = a | b =====
  0           0 RESUME                   0

  1           2 LOAD_NAME                0 (a)
              4 LOAD_NAME                1 (b)
              6 BINARY_OP                7 (|)
             10 STORE_NAME               2 (c)
             12 RETURN_CONST             0 (None)
===== 소스: c = {**a, **b} =====
  0           0 RESUME                   0

  1           2 BUILD_MAP                0
              4 LOAD_NAME                0 (a)
              6 DICT_UPDATE              1
              8 LOAD_NAME                1 (b)
             10 DICT_UPDATE              1
             12 STORE_NAME               2 (c)
             14 RETURN_CONST             0 (None)
```

★ `{**a, **b}` 는 **빈 dict 를 만들고 두 번 `update`** 하는 것이다 — 그래서 `dict` 가 아닌 매핑도 받는다.

**비용** — `|` 는 매번 새 dict 를 만든다. 루프 안에서 누적할 때는 `|=`·`update` 가 맞다.

### 8. ★ 키를 넣은 뒤에 고치면 — 사전이 조용히 망가진다

**언제 쓰나** — 내 클래스를 키로 쓸 때. 「해시는 평생 안 바뀌어야 한다」가 왜 계약인지 볼 때.

```python
class Box:
    def __init__(self, v): self.v = v
    def __eq__(self, o): return isinstance(o, Box) and self.v == o.v
    def __hash__(self): return hash(self.v)
    def __repr__(self): return f"Box({self.v})"

k = Box(1)
d = {k: "값"}
print("넣은 직후 :", d, "| k in d :", k in d)
k.v = 2                       # 키를 넣은 뒤 해시가 바뀌게 고친다
print("키를 고친 뒤 :", d, "| k in d :", k in d, "| Box(2) in d :", Box(2) in d, "| Box(1) in d :", Box(1) in d)
print("그런데 순회하면 보인다 :", list(d.items()))
print("len =", len(d))
try:
    print("d[k] ->", d[k])
except KeyError as e:
    print("d[k] -> KeyError:", e)
```

```text
넣은 직후 : {Box(1): '값'} | k in d : True
키를 고친 뒤 : {Box(2): '값'} | k in d : False | Box(2) in d : False | Box(1) in d : False
그런데 순회하면 보인다 : [(Box(2), '값')]
len = 1
d[k] -> KeyError: Box(2)
```

```text
   넣을 때   hash(Box(1)) = h1   ->  h1 칸에 넣었다
   고친 뒤   hash(Box(2)) = h2   ->  찾을 때는 h2 칸을 본다   ->  거기 없다

   순회는 칸을 처음부터 훑으므로 "보인다"
   조회는 해시로 한 칸만 보므로 "없다"
   ->  len 은 1 인데 어떤 키로도 못 꺼낸다
```

★ **`len(d)` 는 `1`, `list(d)` 에는 보이는데, `Box(1)` 로도 `Box(2)` 로도 못 꺼낸다.**
문서가 미리 경고한 그대로다 — *"if the object's hash value changes, **it will be in the wrong hash bucket**."*

**비용** — 이 사고는 **예외가 안 난다.** 키로 쓸 클래스는 **불변으로 만들거나**(`frozen=True` 인 dataclass),
해시에 **안 바뀌는 필드만** 넣어야 한다.

## 문법 — 형태와 규칙

```python
{}                      # 빈 dict.  ★ 빈 set 이 아니다
{"a": 1, "b": 2}
{k: v for k, v in pairs}          # 컴프리헨션 (14번)
dict(a=1, b=2)                    # 키워드 — 키는 문자열만
dict([("a", 1), ("b", 2)])        # (키, 값) 쌍의 이터러블
dict.fromkeys(["a", "b"])         # 값은 전부 None
dict.fromkeys(["a", "b"], [])     # ★ 한 리스트를 공유한다 (20번과 같은 함정)

d[k]            # 없으면 KeyError
d.get(k, 기본)   # 없으면 기본. 키를 안 만든다
d.setdefault(k, 기본)   # 없으면 넣는다
d.pop(k, 기본) · d.popitem()      # popitem 은 마지막 것 (3.7+ LIFO)
k in d          # ★ 키를 본다. 값이 아니다
d.keys() · d.values() · d.items() # 동적 뷰
d | other  ·  d |= other          # 3.9+
```

```python
d = {"a": 1}
try:
    d["z"]
except KeyError as e:
    print("d['z']       -> KeyError:", e, "| args =", e.args)
print("d.pop('a')   ->", d.pop("a"), "| d =", d)
print("d.pop('z',0) ->", d.pop("z", 0))
try:
    d.pop("z")
except KeyError as e:
    print("d.pop('z')   -> KeyError:", e)
try:
    {}.popitem()
except KeyError as e:
    print("{}.popitem() -> KeyError:", e)
print("중복 키 리터럴 :", {"a": 1, "a": 2})
print("컴프리헨션도 뒤가 이긴다 :", {k: v for k, v in [("a", 1), ("a", 2)]})
print("dict(pairs) 도           :", dict([("a", 1), ("a", 2)]))
print("키 순서는 처음 자리      :", {k: v for k, v in [("a", 1), ("b", 9), ("a", 2)]})
```

```text
d['z']       -> KeyError: 'z' | args = ('z',)
d.pop('a')   -> 1 | d = {}
d.pop('z',0) -> 0
d.pop('z')   -> KeyError: 'z'
{}.popitem() -> KeyError: 'popitem(): dictionary is empty'
중복 키 리터럴 : {'a': 2}
컴프리헨션도 뒤가 이긴다 : {'a': 2}
dict(pairs) 도           : {'a': 2}
키 순서는 처음 자리      : {'a': 2, 'b': 9}
```

★ **`KeyError` 의 인자는 키 자체**다(`e.args == ('z',)`) — 그래서 `print(e)` 가 `'z'` 로 **따옴표째** 나온다.
`popitem()` 의 빈 사전 오류만 **문장**이다.\
★ **중복 키는 에러가 아니다.** 「값은 뒤가 이기고 자리는 앞이 남는다」가 여기서도 같다.

**비교 연산은 `==` 뿐이다.**

```python
from collections import OrderedDict
d = {"a": 1, "b": 2}
print("in 은 키를 본다 :", "a" in d, "| 1 in d :", 1 in d, "| 1 in d.values() :", 1 in d.values())
try:
    {"a": 1} < {"a": 1, "b": 2}
except TypeError as e:
    print("dict < dict     -> TypeError:", e)
o1, o2 = OrderedDict(a=1, b=2), OrderedDict(b=2, a=1)
print("OrderedDict == 는 순서를 본다 :", o1 == o2)
print("평범한 dict 는 안 본다        :", dict(a=1, b=2) == dict(b=2, a=1))
print("OrderedDict == dict           :", o1 == dict(a=1, b=2), "|", o1 == dict(b=2, a=1))
print("move_to_end 는 dict 에 없다   :", hasattr(o1, "move_to_end"), hasattr(d, "move_to_end"))
```

```text
in 은 키를 본다 : True | 1 in d : False | 1 in d.values() : True
dict < dict     -> TypeError: '<' not supported between instances of 'dict' and 'dict'
OrderedDict == 는 순서를 본다 : False
평범한 dict 는 안 본다        : True
OrderedDict == dict           : True | True
move_to_end 는 dict 에 없다   : True False
```

★ **`<` 는 없다.** 문서가 *"Order comparisons ('<', '<=', '>=', '>') raise `TypeError`"* 라고 적는다 —
**부분집합 비교가 있는 `set` 과 정확히 갈리는 자리다**([13번](../13-set-and-frozenset/2-summary.md)).\
★ **`OrderedDict` 는 아직 쓸모가 있다** — `==` 가 **순서를 본다**. 다만 **평범한 dict 와 비교할 때는 순서를 안 본다**(양쪽 다 `True`).
「순서까지 같은가」를 테스트하려면 **양쪽 다 `OrderedDict`** 이거나 `list(d1) == list(d2)` 여야 한다.

## 어디서 틀리나

### (1) 「`1` 과 `True` 는 다른 키」로 안다

같은 칸이다. **키는 먼저 들어간 것이 남고 값은 나중 것이 이긴다.** 에러는 없다.

### (2) `d.keys()` 를 목록으로 안다

뷰다. 받아 둔 뒤 원본을 바꾸면 **따라 변한다.** 그 시점의 목록이 필요하면 `list(d)`.

### (3) 「순회 중 변경하면 예외가 난다」로만 안다

**크기가 그대로면 예외가 없고 결과가 틀린다**(동작 5-나). 문서도 *"or fail to iterate over all entries"* 라고 적는다.

### (4) `setdefault` 를 「기본값 선언」으로 안다

**키를 만든다.** 읽기만 할 생각이면 `get` 이다.

### (5) `defaultdict` 를 읽기에 쓴다

**조회만 해도 키가 생긴다.** 오타 한 번이 사전을 늘린다. 읽기는 `.get(k)` 나 `k in dd`.

### (6) `dict.fromkeys(keys, [])` 로 묶기를 시작한다

**모든 키가 한 리스트를 공유한다.** [20번](../20-mutable-default-args/2-summary.md)과 같은 집안이다.

```python
bad = dict.fromkeys(["a", "b"], [])
bad["a"].append(1)
print("dict.fromkeys(keys, []) :", bad, " <- 한 리스트를 공유한다")
```

```text
dict.fromkeys(keys, []) : {'a': [1], 'b': [1]}  <- 한 리스트를 공유한다
```

### (7) 키로 쓸 클래스에 `__eq__` 만 정의한다

**`__hash__` 가 `None` 으로 꺼져** `unhashable type` 이 난다. 다행히 **조용하지 않다.**

### (8) 키로 쓴 뒤에 그 객체를 고친다

**조용하다.** `len` 은 그대로인데 어떤 키로도 못 꺼낸다(동작 8).

### (9) `k in d` 가 값을 본다고 믿는다

**키를 본다.** 값이면 `k in d.values()`.

### (10) `==` 가 순서 사고를 잡아 줄 거라고 믿는다

**dict 의 `==` 는 순서를 안 본다.** 순서를 검사하려면 `list(d1) == list(d2)`.

### (11) 병합의 승자를 「왼쪽」으로 외운다

**값은 오른쪽이 이기고 자리는 왼쪽이 남는다.** 두 규칙이 방향이 반대다.

### (12) 중첩 설정을 `|` 로 병합한다

**얕다.** 값이 dict 면 통째로 교체된다.

## 구현 세부사항 대 언어 보장

세 층으로 가른다. ★ **이 주제가 세 층의 가장 좋은 본보기인 이유는, 삽입 순서가 「구현 → 보장」으로 실제로 옮겨 갔기 때문이다.**

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **언어 보장** | 언어·라이브러리 레퍼런스가 정한 것 | 공식 문서 문장을 열어서 인용 |
| **CPython 구현** | 이 구현이 그렇게 하는 것 | `dis`·바이트코드·실행 |
| **이 판·이 머신의 관찰** | 3.12.3 에서 그랬을 뿐 | 「관찰」로 명기 |

### 언어 보장

| 사실 | 근거 | 언제부터 |
|---|---|---|
| **삽입 순서가 유지된다** | Mapping Types — *"Dictionaries preserve insertion order"* | **3.7** (3.6 은 구현) |
| **키를 덮어써도 자리가 안 바뀐다** · **지우고 다시 넣으면 맨 뒤** | 〃 | 3.7 |
| **`==` 는 순서를 보지 않는다** · `<`·`<=`·`>`·`>=` 는 `TypeError` | 〃 | — |
| **키는 해시 가능해야** 한다 | *"A mapping object maps hashable values to arbitrary objects"* | — |
| **`==` 인 값(`1`·`1.0`·`True`)은 같은 칸을 가리킨다** | *"can be used interchangeably to index the same dictionary entry"* | — |
| **`__eq__` 만 재정의하면 `__hash__` 가 `None` 이 된다** | `object.__hash__` | 파이썬 3 전체 |
| **해시는 평생 안 바뀌어야 한다**(안 지키면 「잘못된 버킷」) | glossary · `object.__hash__` | — |
| **`keys()`·`values()`·`items()` 는 동적 뷰** | Dictionary view objects | 파이썬 3 전체 |
| **순회 중 추가·삭제는 `RuntimeError` 또는 「전부 돌지 못함」** | 〃 — *"may raise a RuntimeError **or fail to iterate over all entries**"* | — |
| 뷰가 **역순 순회 가능** | 〃 | **3.8** |
| **`d \| other` 는 양쪽이 dict 여야 하고 오른쪽 값이 이긴다** | `d \| other` | **3.9** |
| **`d \|= other` 는 매핑 **또는** (키,값) 이터러블을 받는다** | `d \|= other` | **3.9** |
| `popitem()` 은 **마지막** 쌍을 뺀다(LIFO) | Mapping Types | 3.7 |
| **str·bytes 의 해시만 무작위화된다** | PYTHONHASHSEED | 3.2.3 |

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| **3.6 에서 삽입 순서가 유지된 것**(당시에는 기대면 안 되는 것) | 3.6 릴리스 문서가 직접 그렇게 적는다 |
| `{**a, **b}` 가 **`BUILD_MAP` + `DICT_UPDATE` 두 번**으로 컴파일된다 | `dis` |
| `a \| b` 가 **`BINARY_OP 7 (\|)`** 한 번 | `dis` |
| `RETURN_CONST` 같은 **명령 이름** | `dis` — 3.11 에서는 `LOAD_CONST`+`RETURN_VALUE` 였다 |
| **크기가 같으면 순회 중 변경이 안 잡히는 것** | 실행 — 검사가 크기만 본다 |
| 예외·경고 **문구** 전부 | 실행 |

### 이 판(3.12.3)·이 머신의 관찰

| 관찰 | 어디가 흔들리나 |
|---|---|
| `getsizeof(dict.fromkeys(range(n)))` — n=0/1/5/10 이 **64 / 224 / 224 / 352** | 빌드·비트 폭·재해시 시점에 달렸다 |
| `hash(float("nan"))` 의 **값** | **판마다 다르다** — 아래 참조 |
| 문자열 해시의 **구체적 수치** | 시드마다 다르다 |

```python
import sys
print("dict 0/1/5/10 :", [sys.getsizeof(dict.fromkeys(range(i))) for i in (0, 1, 5, 10)])
```

```text
dict 0/1/5/10 : [64, 224, 224, 352]
```

★ **`hash(nan)` 은 시드를 고정해도 판마다 다르다** — 3.10 부터 `nan` 의 해시가 **객체 정체 기반**이기 때문이다.
그래서 `PYTHONHASHSEED=0` 으로 고정해도 안 굳는다.\
★ **아래 두 값은 지금 다시 돌리면 또 다른 값이 나온다** — 재현되지 않는 것이 이 블록의 결론이므로
대조할 것은 숫자가 아니라 「**두 줄이 서로 다르다**」는 성질이다.

```bash
for i in 1 2; do PYTHONHASHSEED=0 python3 -c 'print(hash(float("nan")))'; done
```

```text
8023777811245
8652895139629
```

그 결과가 키에서 이렇게 드러난다.

```python
n = float("nan")
print("n == n :", n == n)
s = {n, float("nan")}
print("{n, float('nan')} 의 크기 :", len(s))
dn = {n: "첫째"}
print("dn[n]            :", dn[n], " <- 같은 객체라 찾힌다")
print("n in dn          :", n in dn, "| float('nan') in dn :", float("nan") in dn)
dn[float("nan")] = "둘째"
print("다른 nan 을 넣으면:", len(dn), dn)
print("0.0 과 -0.0      :", {0.0: "양", -0.0: "음"}, "| hash 같나:", hash(0.0) == hash(-0.0), "| == :", 0.0 == -0.0)
```

```text
n == n : False
{n, float('nan')} 의 크기 : 2
dn[n]            : 첫째  <- 같은 객체라 찾힌다
n in dn          : True | float('nan') in dn : False
다른 nan 을 넣으면: 2 {nan: '첫째', nan: '둘째'}
0.0 과 -0.0      : {0.0: '음'} | hash 같나: True | == : True
```

★ **`0.0` 과 `-0.0` 도 한 칸**이다 — `==` 이고 해시가 같기 때문이다. **남은 키는 `0.0`, 값은 `'음'`** 이다.

★ **`nan` 은 자기 자신과도 `==` 가 아니다.** 그래서 dict 는 **먼저 정체(`is`)로 한 번 보고** `==` 로 본다 —
**같은 객체면 찾히고 다른 `nan` 이면 못 찾는다.** 키가 두 개로 늘어난다.

### 그래서 이렇게 적으면 틀린다

- ✗ 「파이썬 dict 는 원래 순서가 없다」\
  ○ **3.7 부터 언어 보장**이다. 3.6 에서는 CPython 구현 세부였고, 3.5 이하에서는 없었다.
- ✗ 「dict 순서는 CPython 구현 세부사항이다」\
  ○ **3.6 까지의 이야기**다. 지금은 명세다 — 문서가 승격을 기록해 두었다.
- ✗ 「`1` 과 `True` 는 다른 키다」\
  ○ **같은 칸**이다. 문서가 예시로 그 셋을 든다.
- ✗ 「`d.keys()` 는 키 목록이다」\
  ○ **동적 뷰**다. 첨자도 못 쓴다.
- ✗ 「순회 중 변경하면 `RuntimeError` 가 난다」\
  ○ **크기가 안 변하면 안 난다.** 그리고 **원소를 빠뜨린다.**
- ✗ 「`setdefault` 는 기본값만 정한다」\
  ○ **키를 만든다.**
- ✗ 「`defaultdict` 를 읽는 것은 안전하다」\
  ○ **`dd[k]` 는 키를 만든다.** `get`·`in` 은 안 만든다.
- ✗ 「병합은 왼쪽이 이긴다」\
  ○ **값은 오른쪽**이 이기고 **자리는 왼쪽**이 남는다.
- ✗ 「`a | b` 에 리스트를 넘겨도 된다」\
  ○ `|` 는 **dict 만**, `|=` 는 이터러블도 받는다.
- ✗ 「`__eq__` 를 만들었으니 키로 쓸 수 있다」\
  ○ **`__hash__` 가 꺼진다.** 둘을 같이 정의해야 한다.
- ✗ 「dict 는 시드에 따라 순서가 달라진다」\
  ○ **안 달라진다.** 그건 `set` 이다([13번](../13-set-and-frozenset/2-summary.md)).

**판정 기준 한 줄**: 순서를 물으면 **「넣은 순서」**, 키를 물으면 「**`==` 와 `hash` 가 한 쌍인가**」를 보라.

## 언제 쓰고 언제 안 쓰나

| 쓰는 것 | 상황 |
|---|---|
| `d.get(k, 기본)` | 없을 수 있는 키를 **읽기만** 할 때 |
| `d.setdefault(k, []).append(v)` | 묶기를 dict 하나로 끝낼 때 |
| `defaultdict(list)` | 묶기가 루프에서 반복될 때(**쓰기 전용**으로) |
| `d \|= other` | 설정을 누적할 때(새 객체를 안 만든다) |
| `{**a, **b}` | 매핑까지 받아야 할 때 · 3.9 미만을 지원할 때 |
| `list(d)` | **순회 중 지울** 때 · 그 시점 키 목록이 필요할 때 |
| `dict.fromkeys(xs)` | **순서를 지키며** 중복 제거할 때([13번](../13-set-and-frozenset/2-summary.md)) |
| `OrderedDict` | `==` 로 **순서까지** 비교할 때 · `move_to_end` 가 필요할 때 |
| `frozen=True` dataclass · `tuple` | 키로 쓸 값을 얼릴 때 |

**안 쓰는 자리**는 넷이다.\
**`defaultdict` 를 읽기 경로에 쓰지 마라** — 조회가 키를 만든다.\
**가변 객체를 키로 쓰지 마라** — 고치는 순간 조용히 못 찾게 된다.\
**`|` 로 중첩 설정을 병합하지 마라** — 얕다.\
**`==` 로 순서를 검사하지 마라** — 순서를 안 본다.

## 핵심 문장

- **dict 순서는 3.7 부터 언어 보장**이다. 3.6 에서는 **CPython 구현 세부**였고, 문서가 그 승격을 기록해 두었다 —
  **이 주제가 「세 층」이 실제로 움직인 사례다.**
- **덮어쓰면 자리가 그대로, 지우고 넣으면 맨 뒤.** 두 가지가 다르다.
- **키 요건은 `hash()` 와 `__eq__` 한 쌍**이다. `__eq__` 만 정의하면 언어가 `__hash__` 를 **`None` 으로 꺼 버린다.**
- **`1`·`1.0`·`True` 는 한 칸.** **키는 처음 것이 남고 값은 나중 것이 이긴다.**
- **뷰는 사본이 아니다.** 원본이 바뀌면 따라 변하고 첨자는 못 쓴다.
- **순회 중 변경은 `RuntimeError` 「또는」 조용히 빠뜨림**이다. 검사는 **크기만** 본다.
- **병합은 값이 오른쪽, 자리가 왼쪽.** `|` 는 dict 만 받고 `|=` 는 이터러블도 받는다.
- **dict 순서는 `PYTHONHASHSEED` 에 안 흔들린다.** 순서가 해시에서 오지 않기 때문이다.

## 관련 자료

- 목록: [python/syntax 주제 목록](../README.md) — 이 주제는 **12번**
- 선행: [02-is-vs-eq-interning](../02-is-vs-eq-interning/2-summary.md) — **`is` 와 `==` 의 정본.** 여기서는 `==` 와 `hash` 의 **계약**만 본다.
- 선행: [11-tuple-and-unpacking](../11-tuple-and-unpacking/2-summary.md) — **튜플이 키가 되는 조건**과 `namedtuple` 이 평범한 튜플과 한 키가 되는 것.
- 선행: [03-mutability-and-copying](../03-mutability-and-copying/2-summary.md) — 불변 안의 가변. **얕은 복사**의 정본.
- 이어지는 곳: [13-set-and-frozenset](../13-set-and-frozenset/2-summary.md) — **같은 해시 기계의 「순서 없는」 쪽.**
  `PYTHONHASHSEED` 로 실제로 갈리는 것은 그쪽이다.
- 이어지는 곳: [14-comprehensions](../14-comprehensions/2-summary.md) — dict 컴프리헨션.
- 이어지는 곳: [20-mutable-default-args](../20-mutable-default-args/2-summary.md) — `dict.fromkeys(keys, [])` 와 같은 집안의 함정.
- 이어지는 곳: [목록의 **30번 주제**](../30-repr-eq-hash-contracts/) 「`__repr__`·`__eq__`·`__hash__` 계약」 — **세 메서드 계약의 정본**이다.
  여기서는 「키가 되나 안 되나」까지만 본다.
- 이어지는 곳: 목록의 **43번 주제** 「`collections`」 — `defaultdict`·`OrderedDict`·`Counter`·`ChainMap` 의 정본.
- 이어지는 곳: 목록의 **47번 주제** 「`json`」 — **dict 키가 문자열로 바뀌는 것**. `{True: ...}` 가 `"true"` 로 나가는 자리다.
- 원리: [`cs/data-structure/`](../../../../../data-structure/) — 해시 테이블의 원리·충돌 해결·재해시 비용은 그쪽이 정본이다.\
  **경계**: 그쪽은 **왜 평균 O(1) 인가**까지, 여기는 **그래서 파이썬 코드에서 무엇이 되고 안 되나**부터다.
- 기존 노트: [`cs/foundations/python-basics/`](../../../../python-basics/) — 딕셔너리를 「이렇게 쓴다」까지 다룬다.\
  **경계**: 그쪽은 메서드 사용 예시까지, 여기는 「**무엇이 키가 되고 순서를 누가 약속하나**」부터다.
- 공식 문서: [Mapping Types](https://docs.python.org/3.12/library/stdtypes.html#mapping-types-dict) · [Dictionary view objects](https://docs.python.org/3.12/library/stdtypes.html#dict-views) · [hashable](https://docs.python.org/3.12/glossary.html#term-hashable) · [`object.__hash__`](https://docs.python.org/3.12/reference/datamodel.html#object.__hash__)

## 용어 풀이

- **매핑(mapping)**: 키를 값에 대응시키는 객체. 표준 매핑 타입은 **`dict` 하나**뿐이다.
- **해시 가능(hashable)**: ① 평생 안 바뀌는 해시값이 있고 ② 비교할 수 있고 ③ `==` 인 것끼리 해시가 같은 것.
- **해시 충돌(hash collision)**: 다른 값이 같은 칸으로 떨어지는 것. **틀림이 아니라 느려짐**이다.
- **버킷(bucket)**: 해시가 가리키는 칸. 해시가 바뀌면 **잘못된 버킷**에 남는다.
- **뷰 객체(view object)**: `keys()`·`values()`·`items()` 가 돌려주는 것. **사본이 아니라 창**이다.
- **삽입 순서(insertion order)**: 처음 키가 들어온 순서. **덮어쓰기는 안 바꾸고 지우고 넣기는 맨 뒤로** 보낸다.
- **`__missing__`**: `d[k]` 가 실패할 때 불리는 훅. `defaultdict` 가 이것으로 키를 만든다.
  **`get` 과 `in` 은 이 훅을 안 탄다.**
- **해시 무작위화(hash randomization)**: **str·bytes** 의 해시에 매 프로세스 무작위 소금을 섞는 것(3.2.3+, 3.3 부터 기본 켜짐).
  DoS 방어가 목적이다. `PYTHONHASHSEED` 로 고정할 수 있다.

## 더 들어가면

- **왜 str 만 무작위화하나** — 문서가 이유를 적는다: 악의적 입력으로 **dict 생성을 O(n²)** 로 만드는 DoS 방어다.
  공격 입력은 대개 문자열이라 **정수는 대상이 아니다**([13번](../13-set-and-frozenset/2-summary.md)에서 실측한다).
- **`Counter`·`ChainMap`** 은 목록의 **43번 주제**. `Counter` 는 없는 키에 `0` 을 돌려주는데 **키를 안 만든다** — `defaultdict` 와 다르다.
- **`TypedDict`** 는 목록의 **38번 주제** — 런타임에는 **그냥 dict** 다.
- **`__slots__` 와 인스턴스 `__dict__`** 는 [목록의 **33번 주제**](../33-property-descriptor-slots/).
- **키를 정규화하는 실무 패턴** — 들어오는 키를 `str()` 로 한 번 통일하거나, 「숫자 키 금지」를 계약으로 박는다.
  `1`·`True` 혼용은 **테스트가 `==` 로는 못 잡는다.**
