# python/syntax/30-repr-eq-hash-contracts — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> [1-question.md](1-question.md)의 번호와 **1:1**로 대응한다. 질문 12개 = 답 12개.
>
> 이 파일의 모든 출력은 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> 던지는 형태는 `python3 - <파일` 로 고정했다.\
> ★★★ **이 파일에는 해시값이 한 개도 없다** — `sys.flags.hash_randomization` 이 `True` 라 실행마다 달라지기 때문이다.
> 근거로 쓴 것은 전부 「**해시가 같은가 다른가**」라는 논리값이다.
> 예외는 **정수의 해시**뿐이고(8번 답), 그것은 **CPython 구현**으로 따로 분류했다.\
> ★ 이 파일의 블록에는 **주소도 시간도 절대경로도 안 찍힌다** — 같은 판에서 다시 돌리면 **한 글자도 안 변한다.**
> 단 **예외 문구**와 **내부 예외 타입 이름**은 판에 달린 것이다(12번 답).\
> ★ `dataclass` 의 `FrozenInstanceError` 는 **트레이스백 대신 타입·메시지**로 찍었다 —
> 그 스택이 `dataclasses.py` 를 지나 **절대경로가 박히기** 때문이다.

## 정답

### 1. 클래스 칸에 `None` 이 박혀 있고, 마지막 줄은 세 줄짜리 `TypeError` 로 끝난다

**출력**

```python
# e30_only_eq.py
class OnlyEq:
    def __init__(self, v):
        self.v = v

    def __eq__(self, other):
        return isinstance(other, OnlyEq) and self.v == other.v


print("클래스 칸에 __hash__ 가 있나 :", "__hash__" in OnlyEq.__dict__)
print("그 값                        :", OnlyEq.__dict__.get("__hash__"))
print("OnlyEq.__hash__              :", OnlyEq.__hash__)
print("object.__hash__ 는 있나      :", object.__hash__ is not None)
print("== 는 멀쩡히 된다            :", OnlyEq(1) == OnlyEq(1))
print("이제 해시를 구한다")
hash(OnlyEq(1))
```

```text
===== python3 - <e30_only_eq.py =====
클래스 칸에 __hash__ 가 있나 : True
그 값                        : None
OnlyEq.__hash__              : None
object.__hash__ 는 있나      : True
== 는 멀쩡히 된다            : True
이제 해시를 구한다
Traceback (most recent call last):
  File "<stdin>", line 15, in <module>
TypeError: unhashable type: 'OnlyEq'
(exit 1)
```

**왜 그런가**

- ★★★ **`__hash__` 가 클래스 칸에 `None` 으로 실제로 들어 있다.**
  「안 만들어진 것」이 아니라 **있던 것이 꺼진 것**이다.
  문서가 그 규칙을 직접 적는다 —
  *"A class that overrides `__eq__()` and does not define `__hash__()` will have its `__hash__()` **implicitly set to `None`**."*
- ★ **그래서 상속이 막힌다.** `object.__hash__` 는 멀쩡히 있는데(`True`),
  속성 탐색이 **인스턴스 → 클래스 → MRO** 순서라 **더 가까운 칸의 `None`** 에서 멈춘다.
  탐색 순서의 정본은 [29번](../29-classes-and-attribute-lookup/2-summary.md)이다.
- **`==` 는 멀쩡히 된다.** `__eq__` 는 내가 쓴 그대로 돈다 —
  그래서 `set`·`dict` 에 넣기 전까지는 아무 문제가 없어 보인다.
- ★ **트레이스백이 세 줄이다** — `Traceback (most recent call last):` · `File "<stdin>", line 15, in <module>` · `TypeError: unhashable type: 'OnlyEq'`.
  **소스 줄도 `^` 캐럿도 없다.** 실행 중 예외라 그렇다(`SyntaxError` 라야 둘 다 나온다).
- **종료 코드는 `1`** 이다. 「예외로 끝났다」도 출력이다.

★ **`dict` 키로 써도 똑같다.** 줄 번호만 다르고 예외 종류도 문구도 한 글자도 같다.

```python
# e30_only_eq_dict.py
class OnlyEq:
    def __init__(self, v):
        self.v = v

    def __eq__(self, other):
        return isinstance(other, OnlyEq) and self.v == other.v


print("dict 키로 쓰면")
{OnlyEq(1): "값"}
```

```text
===== python3 - <e30_only_eq_dict.py =====
dict 키로 쓰면
Traceback (most recent call last):
  File "<stdin>", line 10, in <module>
TypeError: unhashable type: 'OnlyEq'
(exit 1)
```

- `dict` 키로 쓰는 것이 결국 `hash()` 를 부르는 것이기 때문이다.
- ★★ **이 주제에서 예외가 나 주는 자리는 여기뿐이다.** 나머지 사고는 전부 조용하다.
  **그 비대칭이 이 주제에서 가장 헷갈리는 자리다.**

### 2. `Fix1` 은 키가 하나, `Fix2` 는 키가 둘 — 똑같이 보이는 키가 둘 남는다

**출력**

```python
# e30_two_fixes.py
class Fix1:                                  # ① __hash__ 를 같이 정의한다
    def __init__(self, v):
        self.v = v

    def __eq__(self, o):
        return isinstance(o, Fix1) and self.v == o.v

    def __hash__(self):
        return hash(self.v)

    def __repr__(self):
        return "Fix1(%r)" % self.v


class Fix2:                                  # ② object 의 것을 되살린다
    def __init__(self, v):
        self.v = v

    def __eq__(self, o):
        return isinstance(o, Fix2) and self.v == o.v

    __hash__ = object.__hash__

    def __repr__(self):
        return "Fix2(%r)" % self.v


for cls in (Fix1, Fix2):
    a, b = cls(1), cls(1)
    d = {a: "첫째"}
    d[b] = "둘째"
    print(cls.__name__,
          "| 해시가 되나 :", cls.__hash__ is not None,
          "| a == b :", a == b,
          "| 해시가 같은가 :", hash(a) == hash(b),
          "| 키 개수 :", len(d),
          "| 남은 것 :", d)

print()
print("② 의 해시는 정체 기준이다 — object.__hash__ 와 같은 것인가")
print("   Fix2.__hash__ is object.__hash__ :", Fix2.__hash__ is object.__hash__)
print("   같은 객체면 해시도 같다          :", (lambda x: hash(x) == hash(x))(Fix2(1)))
print("   set 으로 묶어도 :", len({Fix1(1), Fix1(1)}), "대", len({Fix2(1), Fix2(1)}))
```

```text
===== python3 - <e30_two_fixes.py =====
Fix1 | 해시가 되나 : True | a == b : True | 해시가 같은가 : True | 키 개수 : 1 | 남은 것 : {Fix1(1): '둘째'}
Fix2 | 해시가 되나 : True | a == b : True | 해시가 같은가 : False | 키 개수 : 2 | 남은 것 : {Fix2(1): '첫째', Fix2(1): '둘째'}

② 의 해시는 정체 기준이다 — object.__hash__ 와 같은 것인가
   Fix2.__hash__ is object.__hash__ : True
   같은 객체면 해시도 같다          : True
   set 으로 묶어도 : 1 대 2
(exit 0)
```

**왜 그런가**

- **`Fix1`** — `a == b` 가 참이고 **해시도 같다.** 그래서 **키 개수 1**, 남은 것이 `{Fix1(1): '둘째'}` 다.
  ★ **키는 처음 것이 남고 값은 나중 것이 이긴다** — 이 규칙의 정본은 [12번](../12-dict-and-key-requirements/2-summary.md)이다.
- ★★★ **`Fix2`** — `a == b` 는 여전히 **참**인데 **해시가 다르다.**
  그래서 **키 개수 2**, 남은 것이 `{Fix2(1): '첫째', Fix2(1): '둘째'}` 다.
  **똑같이 보이는 키가 둘 들어 있다.** 이 한 줄이 이 문항의 답 전부다.
- ★ **둘째 처방은 「해시 가능하게 만들기」이지 「계약 지키기」가 아니다.**
  문서가 그 처방을 적어 두긴 한다 —
  *"If a class that overrides `__eq__()` needs to **retain the implementation of `__hash__()` from a parent class**,
  the interpreter must be told this explicitly by setting `__hash__ = <ParentClass>.__hash__`."*
  ★ 핵심은 「**retain**」이다 — **부모의 것을 그대로 유지**하라는 말이지 「이걸로 고쳐라」가 아니다.
- ★ **`object.__hash__` 는 정체 기준**이다. `Fix2.__hash__ is object.__hash__` 가 참이고,
  같은 객체면 해시가 같지만 **딴 객체면 다르다.**
  문서의 기본 동작 문장이 그 전제를 적는다 —
  *"`x.__hash__()` returns an appropriate value such that `x == y` implies both that **`x is y`** and `hash(x) == hash(y)`."*
  ★★ 그 문장은 **`__eq__` 도 기본일 때**의 이야기다. `__eq__` 만 값 기준으로 바꾸면 **전제가 깨져 결론이 안 따라온다.**
- **`set` 도 같다** — `1` 대 `2`.
- ★ **그래서 둘째 처방이 맞는 자리는 하나뿐이다** — **`__eq__` 를 값 기준으로 바꾸지 않았는데**
  다른 이유로 재정의한 경우다. 값 기준 `__eq__` 를 쓰면서 이 처방을 쓰면 3번 답과 같은 사고가 난다.

### 3. `a == b` 는 참인데 `d.get(b)` 만 `None` — 그리고 같은 키가 둘이 된다

**출력**

```python
# e30_contract_break.py
class CaseKey:
    def __init__(self, s):
        self.s = s

    def __eq__(self, o):                     # 대소문자를 무시하고 비교한다
        return isinstance(o, CaseKey) and self.s.lower() == o.s.lower()

    def __hash__(self):
        return hash(self.s)                  # ★ 원문 그대로 — 여기가 계약 위반이다

    def __repr__(self):
        return "CaseKey(%r)" % self.s


a, b = CaseKey("key"), CaseKey("KEY")
print("a == b 인가        :", a == b)
print("해시가 같은가      :", hash(a) == hash(b))      # ★ 값이 아니라 「같은가」만 본다

d = {}
d[CaseKey("key")] = 1
print("넣은 뒤 len        :", len(d))
print("a 로 꺼내면        :", d.get(a))
print("b 로 꺼내면        :", d.get(b))
print("b in d             :", b in d)
d[CaseKey("KEY")] = 2
print("또 넣은 뒤 len     :", len(d))
print("남아 있는 키들     :", sorted(k.s for k in d))
print("a 로 꺼내면        :", d.get(a))
print("set 에 둘을 넣으면 :", len({CaseKey("key"), CaseKey("KEY")}))
print("list 는 멀쩡하다   :", CaseKey("KEY") in [CaseKey("key")])
print()
print("고친 판 — hash 도 eq 가 보는 것과 같게 만든다")


class Fixed(CaseKey):
    def __hash__(self):
        return hash(self.s.lower())


fa, fb = Fixed("key"), Fixed("KEY")
print("   해시가 같은가 :", hash(fa) == hash(fb))
d2 = {Fixed("key"): 1}
print("   b 로 꺼내면   :", d2.get(fb))
d2[Fixed("KEY")] = 2
print("   또 넣은 뒤 len:", len(d2), "| 남은 값 :", list(d2.values()))
```

```text
===== python3 - <e30_contract_break.py =====
a == b 인가        : True
해시가 같은가      : False
넣은 뒤 len        : 1
a 로 꺼내면        : 1
b 로 꺼내면        : None
b in d             : False
또 넣은 뒤 len     : 2
남아 있는 키들     : ['KEY', 'key']
a 로 꺼내면        : 1
set 에 둘을 넣으면 : 2
list 는 멀쩡하다   : True

고친 판 — hash 도 eq 가 보는 것과 같게 만든다
   해시가 같은가 : True
   b 로 꺼내면   : 1
   또 넣은 뒤 len: 1 | 남은 값 : [2]
(exit 0)
```

**왜 그런가** — 진단 네 창으로 읽는다.

```text
   넣을 때                               찾을 때

   hash("key")  ->  h1 칸              hash("KEY")  ->  h2 칸
        |                                    |
        v                                    v
   +------+------+------+              +------+------+------+
   | h1   | h2   | ...  |              | h1   | h2   | ...  |
   |CaseKey("key")|     |              |      | 비었다|     |
   +------+------+------+              +------+------+------+
                                          h2 칸만 본다 -> None
                                          h1 칸은 쳐다보지도 않는다
                                          __eq__ 는 불리지도 않는다
```

- **창 ① `a == b` 가 `True`** 다 — 여기는 **정상으로 보인다.**
- ★★★ **창 ② 해시가 다르다** — 계약이 깨진 지점이 이 두 줄이다.
  **해시값은 안 찍었다.** 흔들리는 칸이라 「같은가」라는 논리값만 근거로 쓴다.
- **창 ③ `len` 도 순회도 멀쩡하다** — 넣은 뒤 1, 또 넣으면 2, 키 목록에 둘 다 보인다.
- ★★★ **창 ④ 조회가 갈린다** — `d.get(a)` 는 `1` 인데 **`d.get(b)` 는 `None`** 이다.
  `a == b` 인데 답이 다르다. `b in d` 도 `False` 다.
  **표가 해시로 칸을 먼저 고르므로** 칸이 다르면 `__eq__` 를 **부를 기회조차 없다.**
- ★★ **같은 키가 둘이 된다** — `CaseKey("KEY")` 를 또 넣으니 `len` 이 **2** 다.
  `dict` 의 불변식(「같은 키는 하나」)이 **밖에서 깨진 것**이고,
  그래서 마지막 `d.get(a)` 가 여전히 `1` 이다 — **덮어쓰기가 안 일어났다.**
- **`set` 도 2** 다. 중복 제거가 안 된다.
- ★★★ **`list` 는 멀쩡하다** — `CaseKey("KEY") in [CaseKey("key")]` 가 `True` 다.
  **리스트는 해시를 안 쓰고 앞에서부터 `==` 로 훑기 때문**이다.
- ★ **`Fixed` 가 전부 되돌린다** — `hash(self.s.lower())` 한 줄만 바꿨더니
  해시가 같아지고 · `d2.get(fb)` 가 `1` 이 되고 · 또 넣어도 `len` 이 1 이고 · 남은 값이 `[2]` 다.
  **처방은 「`__eq__` 가 보는 것과 `__hash__` 가 섞는 것을 같게」 하나뿐이다.**
- ★ 이 실험은 [Rust 28 §(3)](../../../rust/syntax/28-partialeq-eq-partialord-ord-and-hash-contracts/2-summary.md)의 `CaseKey` 를 파이썬으로 옮긴 것이고,
  **출력의 모양이 거의 같다**(10번 답의 표).

### 4. 넣을 때 쓴 그 객체로는 꺼내진다 — `__eq__` 가 아예 안 불린다

**출력**

```python
# e30_reflexivity.py
class Never:
    def __init__(self, v):
        self.v = v

    def __eq__(self, o):
        print("      __eq__ 가 불렸다")
        return False                          # ★ 자기 자신과도 같지 않다

    def __hash__(self):
        return hash(self.v)

    def __repr__(self):
        return "Never(%r)" % self.v


k = Never(1)
d = {k: "값"}
print("① 넣을 때 쓴 바로 그 객체로 꺼내면")
print("   d.get(k) ->", d.get(k))
print("② 그런데 k == k 는")
print("   ->", k == k)
print("③ 값이 같은 딴 객체로 꺼내면")
print("   d.get(Never(1)) ->", d.get(Never(1)))
print("④ 같은 값을 또 넣으면")
d[Never(1)] = "둘째"
print("   len =", len(d), "| 값들 :", sorted(d.values()))
print("⑤ list 도 정체를 먼저 본다")
xs = [k]
print("   k in xs        ->", k in xs)
print("   Never(1) in xs ->", Never(1) in xs)
print("⑥ set 도 같은 지름길을 쓴다")
s = {k}
print("   k in s        ->", k in s)
print("   Never(1) in s ->", Never(1) in s)
print("   len({k, k}) =", len({k, k}), "| len({Never(1), Never(1)}) =", len({Never(1), Never(1)}))
```

```text
===== python3 - <e30_reflexivity.py =====
① 넣을 때 쓴 바로 그 객체로 꺼내면
   d.get(k) -> 값
② 그런데 k == k 는
      __eq__ 가 불렸다
   -> False
③ 값이 같은 딴 객체로 꺼내면
      __eq__ 가 불렸다
   d.get(Never(1)) -> None
④ 같은 값을 또 넣으면
      __eq__ 가 불렸다
   len = 2 | 값들 : ['값', '둘째']
⑤ list 도 정체를 먼저 본다
   k in xs        -> True
      __eq__ 가 불렸다
   Never(1) in xs -> False
⑥ set 도 같은 지름길을 쓴다
   k in s        -> True
      __eq__ 가 불렸다
   Never(1) in s -> False
      __eq__ 가 불렸다
   len({k, k}) = 1 | len({Never(1), Never(1)}) = 2
(exit 0)
```

**왜 그런가**

- ★★★ **① 에서 `__eq__` 줄이 한 줄도 안 찍혔는데 `'값'` 이 나왔다.**
  **정체 지름길**이다 — 두 포인터가 같으면 CPython 의 비교 관문이 `Py_EQ` 에 대해 **무조건 참**으로 답한다.
  ★★ **이것은 CPython 구현이지 언어 보장이 아니다.**
- **② `k == k` 는 `False`** 다. `__eq__` 는 정직하게 거짓을 답한다 — **지름길을 안 탄 자리**다.
  즉 **반사성이 깨져 있다.**
- **③ 값이 같은 딴 객체로 물으면 `None`** 이다. 여기서는 `__eq__` 가 불렸고 거짓이었다.
- ★ **④ 같은 값을 또 넣으면 `len` 이 2** 다. 3번 답과 같은 모양이다 — **한 키가 여러 칸을 차지한다.**
- ★ **⑤⑥ `list` 와 `set` 도 같은 지름길을 쓴다.**
  `k in xs` 는 `__eq__` 없이 `True`, `Never(1) in xs` 는 `__eq__` 를 부른 뒤 `False`.
  `len({k, k})` 가 1 인데 `len({Never(1), Never(1)})` 은 2 다.
- ★★★ **Rust 와 갈리는 자리가 ① 이다.**
  [Rust 28 §(4)](../../../rust/syntax/28-partialeq-eq-partialord-ord-and-hash-contracts/2-summary.md)의 실측은
  `get`·`contains_key`·`remove` 가 **전부 실패**했고 `remove` 뒤에도 `len` 이 안 줄었다.
  다만 그 실험은 **넣은 객체와 다른 객체**로 물었으므로 파이썬의 ③ 과 대응하고, **파이썬도 ③ 은 `None`** 이다.
  **파이썬만 가진 것은 ①** 이다.
- ★ `float('nan')` 이 실제로 이 성질을 가진 값이고, **파이썬은 그것을 키로 쓰는 것을 안 막는다.**
  Rust 는 `f64` 에 `Eq` 를 안 줘서 **키가 되는 것 자체를 막았다.**

### 5. `__repr__` 은 `__str__` 을 대신하고, 거꾸로는 안 대신한다

**출력**

```python
# e30_repr_str.py
class OnlyRepr:
    def __repr__(self):
        return "<repr 만 있다>"


class OnlyStr:
    def __str__(self):
        return "<str 만 있다>"


class Neither:
    pass


for cls in (OnlyRepr, OnlyStr, Neither):
    o = cls()
    r, s = repr(o), str(o)
    default = "<%s.%s object at 0x" % (cls.__module__, cls.__qualname__)
    print(cls.__name__)
    print("   repr(o) 가 기본 꼴인가 :", r.startswith(default))
    print("   str(o)  가 기본 꼴인가 :", s.startswith(default))
    print("   str(o) == repr(o)      :", s == r)

print()
print("① 컨테이너 안에서는 str 이 아니라 repr 이 쓰인다")
print("   [OnlyStr()] 의 repr 이 기본 꼴인가 :",
      repr([OnlyStr()]).startswith("[<__main__.OnlyStr object at 0x"))
print("   [OnlyRepr()] ->", [OnlyRepr()])
print("② f-string 은 기본이 str, !r 이 repr")
print("   f'{OnlyRepr()}'   ->", "%s" % (OnlyRepr(),))
print("   f'{OnlyRepr()!r}' ->", "%r" % (OnlyRepr(),))
print("③ print 는 str 을 쓴다")
print("   print(OnlyRepr()) ->", end=" ")
print(OnlyRepr())
```

```text
===== python3 - <e30_repr_str.py =====
OnlyRepr
   repr(o) 가 기본 꼴인가 : False
   str(o)  가 기본 꼴인가 : False
   str(o) == repr(o)      : True
OnlyStr
   repr(o) 가 기본 꼴인가 : True
   str(o)  가 기본 꼴인가 : False
   str(o) == repr(o)      : False
Neither
   repr(o) 가 기본 꼴인가 : True
   str(o)  가 기본 꼴인가 : True
   str(o) == repr(o)      : True

① 컨테이너 안에서는 str 이 아니라 repr 이 쓰인다
   [OnlyStr()] 의 repr 이 기본 꼴인가 : True
   [OnlyRepr()] -> [<repr 만 있다>]
② f-string 은 기본이 str, !r 이 repr
   f'{OnlyRepr()}'   -> <repr 만 있다>
   f'{OnlyRepr()!r}' -> <repr 만 있다>
③ print 는 str 을 쓴다
   print(OnlyRepr()) -> <repr 만 있다>
(exit 0)
```

**왜 그런가**

```text
   __repr__ 만 있다                    __str__ 만 있다

   repr(x) -> 내 것                     repr(x) -> 기본 꼴 (주소가 박힌다)
   str(x)  -> 내 것  (대신한다)          str(x)  -> 내 것
        |                                    |
        v                                    v
   ★ 하나만 쓸 거면 __repr__            ★ 컨테이너 안에서는 여전히 기본 꼴
```

- ★ **`OnlyRepr`** — 둘 다 기본 꼴이 아니고 `str(o) == repr(o)` 가 **참**이다.
  문서가 그 방향을 적는다 —
  *"If a class defines `__repr__()` but not `__str__()`, then **`__repr__()` is also used** when an "informal" string representation ... is required."*
- ★★ **`OnlyStr`** — `repr` 이 **기본 꼴**(`True`)이고 `str(o) == repr(o)` 가 **거짓**이다.
  거꾸로는 안 대신한다. 문서는 그 자리를 이렇게 적는다 —
  *"The default implementation defined by the built-in type `object` **calls `object.__repr__()`**."*
  즉 **`__str__` 의 기본이 `__repr__` 을 부르는 것**이지, `__str__` 이 `__repr__` 을 대신하는 게 아니다.
- **`Neither`** — 둘 다 기본 꼴이고 서로 같다.
- ★★★ **컨테이너 안에서는 `repr` 이 쓰인다.** `[OnlyStr()]` 의 표현이 **기본 꼴**이다.
  리스트의 `__str__` 이 원소마다 `repr` 을 부르기 때문이다.
  **그래서 `__str__` 만 쓰면 리스트에 담는 순간 무용지물이 된다.**
- **`f'{o}'` 는 `str`, `f'{o!r}'` 은 `repr`** 이고, `OnlyRepr` 에서는 대신하고 있으므로 둘이 같은 글자를 냈다.
- ★ **주소는 한 번도 안 찍었다.** `startswith` 로 「기본 꼴인가」만 물었다 —
  `0x…` 는 흔들리는 칸이기 때문이다. **이것이 이 주제 내내 쓴 인용 방식이다.**
- ★ 계약을 시험하는 코드에서는 **`__repr__` 이 진단 도구 자체**다.
  2번 답의 `{Fix2(1): '첫째', Fix2(1): '둘째'}` 가 그래서 읽혔다 — 없었으면 주소 두 개만 보였다.

### 6. 기본값은 해시 불가, `frozen=True`·`unsafe_hash=True` 라야 생긴다

**출력**

```python
# e30_dataclass.py
from dataclasses import dataclass


@dataclass                                     # 기본값 — eq=True, frozen=False
class D1:
    v: int


@dataclass(eq=False)
class D2:
    v: int


@dataclass(frozen=True)                        # frozen=True, eq=True
class D3:
    v: int


@dataclass(unsafe_hash=True)                   # eq=True, frozen=False 인데 해시를 만든다
class D4:
    v: int


rows = [("D1 기본(eq=True)", D1), ("D2 eq=False", D2),
        ("D3 frozen=True", D3), ("D4 unsafe_hash=True", D4)]

print("① 클래스 칸의 __hash__ 가 어떻게 갈리나")
for label, cls in rows:
    own = "__hash__" in cls.__dict__
    val = cls.__dict__.get("__hash__", "(칸에 없음)")
    print("   %-20s | 칸에 있나 %-5s | 그 값이 None 인가 %-5s | 해시가 되나 %s"
          % (label, own, (val is None) if own else "-", cls.__hash__ is not None))

print()
print("② 되는 것들은 값으로 묶이나")
for label, cls in rows:
    if cls.__hash__ is None:
        print("   %-20s | 해시 불가" % label)
        continue
    a, b = cls(1), cls(1)
    print("   %-20s | a == b %-5s | 해시가 같은가 %-5s | 키 개수 %d"
          % (label, a == b, hash(a) == hash(b), len({a: 0, b: 0})))

print()
print("③ __repr__ 은 어느 판이든 만들어 준다 :", repr(D1(1)), repr(D3(1)))
print("④ frozen=True 인 것을 고치면")
try:
    x = D3(1)
    x.v = 2
except Exception as ex:
    print("   ", type(ex).__name__, ":", ex)
print("⑤ eq=False 인 D2 는 == 도 정체 기준이다 :", D2(1) == D2(1))
```

```text
===== python3 - <e30_dataclass.py =====
① 클래스 칸의 __hash__ 가 어떻게 갈리나
   D1 기본(eq=True)       | 칸에 있나 True  | 그 값이 None 인가 True  | 해시가 되나 False
   D2 eq=False          | 칸에 있나 False | 그 값이 None 인가 -     | 해시가 되나 True
   D3 frozen=True       | 칸에 있나 True  | 그 값이 None 인가 False | 해시가 되나 True
   D4 unsafe_hash=True  | 칸에 있나 True  | 그 값이 None 인가 False | 해시가 되나 True

② 되는 것들은 값으로 묶이나
   D1 기본(eq=True)       | 해시 불가
   D2 eq=False          | a == b False | 해시가 같은가 False | 키 개수 2
   D3 frozen=True       | a == b True  | 해시가 같은가 True  | 키 개수 1
   D4 unsafe_hash=True  | a == b True  | 해시가 같은가 True  | 키 개수 1

③ __repr__ 은 어느 판이든 만들어 준다 : D1(v=1) D3(v=1)
④ frozen=True 인 것을 고치면
    FrozenInstanceError : cannot assign to field 'v'
⑤ eq=False 인 D2 는 == 도 정체 기준이다 : False
(exit 0)
```

**왜 그런가**

★ 근거는 문서가 아니라 **이 머신의 표준 라이브러리 소스**다 —
`/usr/lib/python3.12/dataclasses.py` 의 `_hash_action` 표(8행)를 직접 읽었다.
축이 **넷**이다 — `unsafe_hash` · `eq` · `frozen` · **클래스 몸통에 `__hash__` 를 직접 썼나**.

| 판 | `unsafe_hash` | `eq` | `frozen` | 클래스 칸의 `__hash__` | 해시가 되나 | 값으로 묶이나 |
|---|---|---|---|---|---|---|
| `D1` 기본 | `False` | `True` | `False` | **`None` 이 박힌다** | ✘ | — |
| `D2` `eq=False` | `False` | `False` | `False` | **칸에 없다**(물려받는다) | ✔ | ✘ — 정체 기준 |
| `D3` `frozen=True` | `False` | `True` | `True` | **만들어 준다** | ✔ | ✔ — 키 개수 1 |
| `D4` `unsafe_hash=True` | `True` | `True` | `False` | **만들어 준다** | ✔ | ✔ — 키 개수 1 |

- ★★★ **기본값이 「해시 불가」다.** `@dataclass` 만 붙이면 `eq=True` 가 켜지고, 그것이 곧 1번 답의 상황이다.
  **`dataclass` 가 심술을 부리는 게 아니라 언어 규칙을 그대로 따른 것이다.**
- ★ **`eq=False` 면 칸을 아예 안 건드린다** — `object` 의 것을 물려받아 **해시는 되는데 정체 기준**이다.
  `D2(1) == D2(1)` 이 `False` 이고 키 개수가 2 다. **2번 답의 `Fix2` 와 정확히 같은 모양**이다.
- ★ **`frozen=True` 가 「값 기준 키」의 정답이다.** 고칠 수 없으니 해시가 평생 안 바뀐다 —
  계약의 「평생 안 바뀐다」 조항을 **타입이 보장해 주는 것**이다.
  고치려 하면 `FrozenInstanceError` 에 `cannot assign to field 'v'` 가 나온다.
- ★★ **`unsafe_hash=True` 는 이름이 경고다.** 해시는 만들어 주는데 **객체는 여전히 고칠 수 있다** —
  넣은 뒤 고치면 [12번 동작 8](../12-dict-and-key-requirements/2-summary.md)의 조용한 사고가 그대로 난다.
- **`__repr__` 은 어느 판이든 만들어 준다** — `D1(v=1)`·`D3(v=1)`.

★★ **소스의 표에는 `raise` 칸도 있었다 — 그것까지 던져 봤다.**
같은 성격의 자리 여섯을 던지니 **넷이 터지고 둘이 조용했다.**

```python
# e30_dataclass_raise.py
from dataclasses import dataclass

print("① unsafe_hash=True 인데 몸통에 __hash__ 를 직접 쓰면")
try:
    @dataclass(unsafe_hash=True)
    class Clash:
        v: int

        def __hash__(self):
            return 0
except Exception as ex:
    print("   ", type(ex).__name__, ":", ex)

print("② eq=False 인데 order=True 로 하면")
try:
    @dataclass(eq=False, order=True)
    class Bad:
        v: int
except Exception as ex:
    print("   ", type(ex).__name__, ":", ex)

print("③ order=True 인데 __lt__ 를 직접 쓰면")
try:
    @dataclass(order=True)
    class Clash2:
        v: int

        def __lt__(self, o):
            return True
except Exception as ex:
    print("   ", type(ex).__name__, ":", ex)

print("④ frozen 과 안 frozen 을 섞어 상속하면")
try:
    @dataclass(frozen=True)
    class Frozen:
        v: int

    @dataclass
    class Thawed(Frozen):
        w: int = 0
except Exception as ex:
    print("   ", type(ex).__name__, ":", ex)

print("⑤ 그냥 __eq__ 를 직접 쓰면? — eq=True 기본값과 부딪히는데")
try:
    @dataclass
    class Clash3:
        v: int

        def __eq__(self, o):
            return "내가 쓴 __eq__ 가 이겼다"
    print("    예외가 안 난다. 그럼 누가 이겼나 :", Clash3(1) == Clash3(2))
    print("    __hash__ 는 :", Clash3.__hash__)
except Exception as ex:
    print("   ", type(ex).__name__, ":", ex)

print("⑥ __repr__ 을 직접 쓰면?")
try:
    @dataclass
    class Clash4:
        v: int

        def __repr__(self):
            return "내가 쓴 repr"
    print("    예외 없음. repr(Clash4(1)) ->", repr(Clash4(1)))
except Exception as ex:
    print("   ", type(ex).__name__, ":", ex)

print("⑦ 그래서 「덮어쓰면 터진다」가 아니라 이름마다 다르다 — 이 판에서 던진 넷의 결과")
print("    터진 것   : __hash__(unsafe_hash=True) · __lt__(order=True)")
print("    조용한 것 : __eq__ · __repr__ — 내가 쓴 것이 그대로 남는다")
```

```text
===== python3 - <e30_dataclass_raise.py =====
① unsafe_hash=True 인데 몸통에 __hash__ 를 직접 쓰면
    TypeError : Cannot overwrite attribute __hash__ in class Clash
② eq=False 인데 order=True 로 하면
    ValueError : eq must be true if order is true
③ order=True 인데 __lt__ 를 직접 쓰면
    TypeError : Cannot overwrite attribute __lt__ in class Clash2. Consider using functools.total_ordering
④ frozen 과 안 frozen 을 섞어 상속하면
    TypeError : cannot inherit non-frozen dataclass from a frozen one
⑤ 그냥 __eq__ 를 직접 쓰면? — eq=True 기본값과 부딪히는데
    예외가 안 난다. 그럼 누가 이겼나 : 내가 쓴 __eq__ 가 이겼다
    __hash__ 는 : None
⑥ __repr__ 을 직접 쓰면?
    예외 없음. repr(Clash4(1)) -> 내가 쓴 repr
⑦ 그래서 「덮어쓰면 터진다」가 아니라 이름마다 다르다 — 이 판에서 던진 넷의 결과
    터진 것   : __hash__(unsafe_hash=True) · __lt__(order=True)
    조용한 것 : __eq__ · __repr__ — 내가 쓴 것이 그대로 남는다
(exit 0)
```

```text
   @dataclass 가 만들려는 이름을 내가 몸통에 이미 써 두면

   __hash__  (unsafe_hash=True)  ->  터진다   TypeError
   __lt__    (order=True)        ->  터진다   TypeError
   __eq__    (eq=True 기본값)     ->  조용하다  내가 쓴 것이 남는다
   __repr__  (repr=True 기본값)   ->  조용하다  내가 쓴 것이 남는다

   ★ 규칙은 "덮어쓰면 터진다" 가 아니라 "이름마다 다르다" 다
```

- **① 표의 `raise` 칸이 실제로 이 줄이다** — `Cannot overwrite attribute __hash__ in class Clash`.
  **표를 읽은 것과 던져 본 것이 맞았다.**
- **② `eq=False` 에 `order=True`** 는 `ValueError` 에 `eq must be true if order is true` —
  **순서는 같음 위에 얹힌다.**
- ★★ **③ `order=True` 에 `__lt__` 를 쓰면** 메시지가 처방까지 준다 —
  `Consider using functools.total_ordering`. 그 도구의 정본은 [31번](../31-comparison-protocol-and-sortability/2-summary.md)이다.
- **④ frozen 에서 non-frozen 을 상속하면** `cannot inherit non-frozen dataclass from a frozen one` 이다.
- ★★★ **⑤ 가 표만으로는 안 보이던 자리다.** `__eq__` 를 직접 쓰면 **예외가 안 나고 내 것이 이긴다.**
  그런데 **`__hash__` 는 `None`** 이다 — **1번 답의 본줄기가 `dataclass` 안에서 그대로 재현된 것**이고,
  `dataclass` 는 그것을 **되살려 주지 않는다.**
- **⑥ `__repr__` 도 조용하다.**
- ★★ **조용한 쪽이 더 위험하다** — 터지는 넷은 클래스를 만드는 순간 알려 주는데,
  `__eq__` 쪽은 **`set`·`dict` 에 넣기 전까지 아무 신호가 없다.**

### 7. 다리는 한 방향이고, 언어가 강제하는 것은 「스위치」 하나뿐이다

**왜 그런가**

```text
   계약은 한 방향이다

     a == b   ================>   hash(a) == hash(b)     (지켜야 한다)
              <================
                이 방향은 아니다    (해시가 같아도 딴 값일 수 있다 — 그게 충돌이다)
```

- **다리는 한 방향이다.** 문서가 그렇게 적는다 —
  *"The only required property is that **objects which compare equal have the same hash value**."*
- ★★★ **언어가 실제로 강제하는 것은 딱 하나다** — **`__eq__` 를 재정의하고 `__hash__` 를 정의하지 않으면
  `__hash__` 가 `None` 이 되는 것.** 이것은 「내용이 맞나」를 보는 것이 아니라
  **「짝을 안 맞췄다」는 신호를 언어가 자동으로 켜 주는 것**이다.
- **역방향은 위반이 아니다.** 해시가 같은데 `==` 가 다른 것은 **충돌**이고 합법이다 — 8번 답의 `AlwaysZero` 가 그 실측이다.
  느려질 뿐 틀리지 않는다.
- ★ **나머지 조항(반사·대칭·추이, 평생 불변)은 전부 사람 몫이다.**
  Java 는 그것을 javadoc 에 **`equals` 5조항 + `hashCode` 3조항**으로 적어 두었고
  ([Java 27](../../../java/syntax/27-equals-hashcode-contract/2-summary.md)),
  Rust 는 「**논리 오류**」라 부르며 UB 는 아니라고 명시한다
  ([Rust 28 §(2)](../../../rust/syntax/28-partialeq-eq-partialord-ord-and-hash-contracts/2-summary.md)).
  **세 언어가 문서에 적는 방식만 다르고 강제하지 않는 것은 같다.**
- ★ `__repr__`·`__str__` 은 **계약이 아니라 권고**다. 어겨도 정확성은 안 깨진다 — **진단만 어려워진다.**

### 8. 값은 소금이 섞여 달라지고, 「같은가」만 안 흔들린다

**출력**

```python
# e30_hash_values.py
import sys

print("① 이 문서에 해시값을 적으면 안 되는 이유")
print("   hash_randomization 플래그 :", bool(sys.flags.hash_randomization))
print("   같은 프로세스 안에서는 같다 :", hash("key") == hash("key"))
print("   그러나 값 자체는 실행마다 달라지므로 적지 않는다")

print("② 적어도 되는 것 — 「같은가 다른가」")
print("   hash(1) == hash(1.0) == hash(True) :", hash(1) == hash(1.0) == hash(True))
print("   그래서 셋은 한 칸이 된다           :", len({1: "a", 1.0: "b", True: "c"}))
print("   hash('key') == hash('KEY')         :", hash("key") == hash("KEY"))

print("③ 정수는 예외적으로 값이 고정돼 있다(CPython 구현)")
print("   hash(1) :", hash(1), "| hash(0) :", hash(0), "| hash(-1) :", hash(-1))
print("   hash(2**61 - 1) :", hash(2 ** 61 - 1))

print("④ 해시가 같아도 같은 값이 아니다 — 충돌은 합법이다")


class AlwaysZero:
    def __init__(self, v):
        self.v = v

    def __eq__(self, o):
        return isinstance(o, AlwaysZero) and self.v == o.v

    def __hash__(self):
        return 0

    def __repr__(self):
        return "AlwaysZero(%r)" % self.v


d = {AlwaysZero(1): "a", AlwaysZero(2): "b"}
print("   해시가 같은가 :", hash(AlwaysZero(1)) == hash(AlwaysZero(2)),
      "| 키 개수 :", len(d), "| 꺼내기 :", d[AlwaysZero(2)])
```

```text
===== python3 - <e30_hash_values.py =====
① 이 문서에 해시값을 적으면 안 되는 이유
   hash_randomization 플래그 : True
   같은 프로세스 안에서는 같다 : True
   그러나 값 자체는 실행마다 달라지므로 적지 않는다
② 적어도 되는 것 — 「같은가 다른가」
   hash(1) == hash(1.0) == hash(True) : True
   그래서 셋은 한 칸이 된다           : 1
   hash('key') == hash('KEY')         : False
③ 정수는 예외적으로 값이 고정돼 있다(CPython 구현)
   hash(1) : 1 | hash(0) : 0 | hash(-1) : -2
   hash(2**61 - 1) : 0
④ 해시가 같아도 같은 값이 아니다 — 충돌은 합법이다
   해시가 같은가 : True | 키 개수 : 2 | 꺼내기 : b
(exit 0)
```

**왜 그런가**

- ★★★ **`hash_randomization` 이 `True`** 다. 문서가 이유를 적는다 —
  *"By default, the `__hash__()` values of str and bytes objects are **"salted" with an unpredictable random value**.
  Although they remain constant within an individual Python process, they are **not predictable between repeated invocations of Python**."*
- **같은 프로세스 안에서는 같다**(`hash("key") == hash("key")` 가 참) — 그래서 **한 실행 안에서의 비교**는 근거가 된다.
  **다른 실행과 비교하는 것**이 안 되는 것이다.
- **`hash(1) == hash(1.0) == hash(True)` 가 참**이라 셋이 한 칸이 된다(키 개수 1).
  ★ 이 사실의 **정본**은 [12번](../12-dict-and-key-requirements/2-summary.md)이다 —
  거기서 `Fraction`·`Decimal`·복소수까지 전수로 봤다.
  여기서 가져오는 결론은 하나다 — **수 타입은 「값이 같으면 해시가 같다」를 타입을 가로질러 지킨다.**
- ★ **정수의 해시는 값이 고정돼 있다** — `hash(1)` 이 `1`, `hash(0)` 이 `0`, `hash(-1)` 이 `-2`,
  `hash(2**61 - 1)` 이 `0`.
  ★★ **그런데 이것은 CPython 구현이다.** 법이 `2**61 - 1` 인 것도, `-1` 이 `-2` 가 되는 것
  (`-1` 은 C 층에서 오류 표시라 피한다)도 **언어 보장이 아니다.**
  그래서 「적을 수 있다」는 것은 「**구현으로 분류해 적을 수 있다**」는 뜻이다.
- ★ **④ 충돌은 합법이다.** `AlwaysZero` 는 해시가 늘 `0` 인데 키 개수가 **2** 이고 조회도 제대로 된다.
- ★ **파일·DB 에 저장하면 안 되는 이유도 같다.** 다음 실행에서 소금이 바뀐다.
  Java 의 javadoc 도 같은 말을 한다 — *"This integer need not remain consistent from one execution ... to another execution."*
  ([Java 27 §(2)](../../../java/syntax/27-equals-hashcode-contract/2-summary.md))

### 9. 리스트는 해시를 안 쓴다 — 칸이 틀리면 `__eq__` 는 불리지도 않는다

**왜 그런가**

```text
   dict / set  — 칸을 먼저 고른다              list — 앞에서부터 다 본다

   hash(k) -> 칸 h2                            [e0, e1, e2, ...]
        |                                        |   |   |
        v                                        v   v   v
   h2 칸만 열어 본다                            k is e? k == e?  (전부)
   비었으면 끝 -> None                          하나라도 참이면 True

   ★ 칸이 틀리면 __eq__ 를 부를 기회조차 없다   ★ 해시를 안 쓰므로 계약과 무관하다
```

- ★★★ **리스트는 해시를 안 쓴다.** 그래서 `__hash__` 가 어떻게 망가져 있어도
  `in`·`index`·`count` 는 **`__eq__` 만으로** 정확히 답한다.
  3번 답에서 `CaseKey("KEY") in [CaseKey("key")]` 가 `True` 였던 것이 그것이다.
- ★★ **`dict`·`set` 은 칸을 먼저 고른다.** 칸이 틀리면 그 칸에 있는 것과만 비교하므로
  **진짜 키는 쳐다보지도 않는다.** `__eq__` 가 **불리지도 않는** 것이 이 경우다.
- ★ **`__eq__` 가 안 불리는 경우가 하나 더 있다** — **정체 지름길**이다(4번 답 ①).
  이쪽은 「비교를 건너뛰고 참」이고, 위쪽은 「비교 자체를 안 함」이라 **결과가 반대**다.
  **둘을 갈라 놓지 않으면 로그를 잘못 읽는다.**
- ★★ **이 비대칭이 진단을 막는다.** 개발자는 보통 리스트로 먼저 확인한다 —
  거기서 통과하니 「내 `__eq__` 는 맞다」로 결론 내고 **`dict` 쪽을 안 의심한다.**
  Java 갈래도 같은 자리를 실측으로 남겼다 — `get` 은 `null` 인데 `List.contains` 는 `true`
  ([Java 27 「어디서 틀리나」 1번](../../../java/syntax/27-equals-hashcode-contract/2-summary.md)).
- ★ 처방은 「**해시 쪽 창을 일부러 여는 것**」이다 — 「해시가 같은가」와 「조회가 되는가」 두 창이
  이 사고를 보이는 유일한 자리다.

### 10. 셋 다 내용은 사람 몫이고, 다른 것은 「언제 잡아 주느냐」뿐이다

**왜 그런가**

★ 아래 표의 Rust·Java 칸은 **그 갈래 문서를 직접 읽고** 옮긴 것이다.
C# 칸은 **아직 폴더가 없어** 목록 행이 예고하는 범위까지만 적는다 — **실측이 아니다.**

| 축 | Python | Rust | Java | C# |
|---|---|---|---|---|
| 계약 문장 | 「`a == b` 면 `hash(a) == hash(b)`」 | 「`k1 == k2` 면 `hash(k1) == hash(k2)`」 | `equals` **5조항** + `hashCode` **3조항** | `Equals`/`GetHashCode` 일관성 |
| 컴파일러가 내용을 강제하나 | ✘ | ✘ — `impl` 의 **존재**만 본다 | ✘ | ✘ |
| ★ 언어가 **반쪽이라도** 막아 주나 | ✔ — `__eq__` 만 정의하면 `__hash__` 가 **`None`** | ✔ — `HashMap` 키가 **타입 수준으로 `Eq + Hash`** 를 요구 | ✘ — `Object.hashCode` 가 **그냥 남는다** | (폴더 없음) |
| ★ 그 방어선을 뚫으려면 | **`__hash__` 를 일부러 써야 한다** | **`impl Hash` 나 `#[derive(Hash)]`** 를 써야 한다 | **아무것도 안 하면 된다** | — |
| 잡아 주는 시점 | **`hash()` 를 부를 때**(런타임) | **타입 검사 때**(컴파일) | **아무 데서도 안 잡는다** | — |
| `Eq` 가 메서드 없는 표식인가 | 해당 없음 | ✔ — `impl Eq for T {}` 의 몸통이 비어 있다 | 해당 없음 | 해당 없음 |
| 어겼을 때 증상 | **조용한 오답** | **조용한 오답**(std 가 「논리 오류」라 부른다 — UB 아님) | **조용한 오답** | — |
| `len`/순회에 보이나 | ✔ | ✔ | ✔ | — |
| 같은 키가 둘이 되나 | ✔ 키 개수 2 | ✔ `len` 2 | ✔ `HashSet size 2` | — |
| 배열·리스트는 멀쩡한가 | ✔ `list` 의 `in` 은 `True` | ✔ `Vec` 는 해시를 안 쓴다 | ✔ `List.contains : true` | — |
| ★★ 넣을 때 쓴 **그 객체**로 꺼내지나 | ✔ **정체 지름길**(CPython 구현) | 그 실험은 **딴 객체**로 물어 전부 실패 | (그 실험을 안 했다) | — |
| 해시값을 문서에 적을 수 있나 | ✘ `str` 해시에 소금 | ✘ `DefaultHasher` 도 안정 보장 아님 | ✘ javadoc 이 「실행 간 일관 불필요」 | — |
| 부동소수점을 키로 쓸 수 있나 | ✔ 안 막는다(`nan` 도 들어간다) | ✘ `f64` 는 `Eq` 를 안 받아 **키가 못 된다** | ✔ `Double` 은 키가 된다 | — |

```text
   막아 주는 자리가 언어마다 다르다

   Rust    타입 검사 때        ->  Eq + Hash 가 없으면 컴파일이 안 된다
   Python  hash() 를 부를 때   ->  __hash__ 가 None 이면 TypeError
   Java    아무 데서도         ->  Object 의 hashCode 가 조용히 쓰인다

   ★ 그런데 셋 다 "내용이 맞는지" 는 안 본다.
     막아 주는 것은 "짝을 안 맞췄을 때" 뿐이다.
```

- ★★★ **컴파일러가 계약 내용을 강제하는 언어는 셋 중 없다.**
- ★★ **Rust 가 가장 이르고 Java 가 가장 늦다.** 파이썬은 중간이다 —
  `__eq__` 만 고친 타입은 `TypeError` 로 **시끄럽게** 막힌다.
- ★★★ **그래서 파이썬에서 조용히 틀리려면 `__hash__` 를 일부러 써야 한다.**
  3번 답의 코드가 정확히 그것이다 — `__hash__` 를 손으로 쓰지 않았다면 그 사고는 **애초에 안 난다.**
  Rust 쪽에서 같은 자리는 `impl Hash` 를 손으로 쓰거나 `#[derive(Hash)]` 를 붙이는 것이다.
- ★ **파이썬에만 있는 칸은 정체 지름길**이고, 그것은 **CPython 구현**이다. 언어 보장으로 읽지 마라.
- ★ **Rust 가 `f64` 에 `Eq` 를 안 준 것**은 이 표에서 유일하게 **언어가 사고를 미리 막은 자리**다.
  파이썬은 `float('nan')` 을 키로 쓰는 것을 안 막는다.

### 11. 12번은 「무엇이 키가 되나」, 여기는 「내 클래스에서 어떻게 쓰나」와 「어겼을 때의 대비」

**왜 그런가**

| 정본 | 어디까지 그쪽 | 여기부터 이쪽 |
|---|---|---|
| [12번](../12-dict-and-key-requirements/2-summary.md) | ① `hash()` 와 `__eq__` 가 한 쌍인 것 ② `1`·`1.0`·`True` 가 **한 칸**인 것 ③ **키는 처음 것이 남고 값은 나중 것이 이기는 것** ④ 넣은 뒤 키를 고치면 못 꺼내는 것 | ① **세 메서드를 내 클래스에서 어떻게 쓰나** ② **계약을 어겼을 때 언어별로 무엇이 다른가** |
| [02번](../02-is-vs-eq-interning/2-summary.md) | `is` 와 `==` 의 구분 · 인터닝 | 정체 지름길을 **계약의 맥락에서** 읽는 것 |
| [29번](../29-classes-and-attribute-lookup/2-summary.md) | 속성 탐색 순서 · 클래스 칸과 인스턴스 칸 | `__hash__` 가 **클래스 칸에 `None` 으로 박혀** 상속을 막는 것 |
| [31번](../31-comparison-protocol-and-sortability/2-summary.md) | `__lt__`·반사 연산·`total_ordering` | 30 은 **같음**까지, 31 은 **순서**부터 |
| [13번](../13-set-and-frozenset/2-summary.md) | `set` 의 순서 없음과 `PYTHONHASHSEED` | 30 은 `set` 을 **`len()` 으로만** 썼다 |

- ★ **12번이 정본인 셋** — 「`1`·`1.0`·`True` 가 한 칸」, 「키는 처음 것·값은 나중 것」,
  「넣은 뒤 키를 고치면 못 꺼낸다」. 이 문서는 **링크하고 결론만** 적었다.
- ★ **여기가 정본인 둘** — 「세 메서드를 어떻게 쓰나(표준 꼴·두 처방·`dataclass`)」와
  「**계약 위반의 언어 간 대비**」.
  12번 자신이 그렇게 넘겨 준다 — 「이어지는 곳: 목록의 **30번 주제** … **세 메서드 계약의 정본**이다」.
- **`dataclasses` 의 나머지**(`field`·`default_factory`·`order`)는 `목록의 **36번 주제**` 다.
  여기서는 **`__hash__` 가 어떻게 갈리는지**만 봤다.
- **해시 테이블의 원리**는 [`cs/data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/)이 정본이다.
  버킷·충돌·리사이즈는 그쪽, 여기는 **계약을 어기면 어디가 틀리나**부터.

### 12. 언어 보장은 ① 하나뿐이다 — ②는 구현, ③도 구현, ④는 이 판의 관찰

**왜 그런가**

| 항목 | 어느 층인가 | 근거 |
|---|---|---|
| ① `__eq__` 를 재정의하면 `__hash__` 가 `None` 이 된다 | ★ **언어 보장** | 데이터 모델 문서가 명시 · 1번 답의 실측 |
| ② `dict` 는 같은 객체면 `__eq__` 를 안 부른다 | ★ **CPython 구현** | 4번 답 ① 의 관찰 — 레퍼런스는 약속하지 않는다 |
| ③ `hash(1)` 은 `1` 이다 | ★ **CPython 구현** | 8번 답 ③ — 법이 `2**61 - 1` 인 것도 구현이다 |
| ④ `unhashable type: 'OnlyEq'` 라는 **문구** | ★ **이 판(3.12.3)의 관찰** | 1번 답 — 판이 오르면 문구가 바뀔 수 있다 |
| ★ 「계약을 어기면 키 개수가 2 가 된다」 | ★ **CPython 구현** | 정확한 표현은 「동작이 규정되지 않는다」이고, `2` 는 **이 구현의 결과**다 |
| `a == b` 이면 `hash(a) == hash(b)` | ★ **언어 보장**(계약) — 강제는 없다 | 문서의 「유일하게 요구되는 성질」 |
| `__repr__` 이 `__str__` 을 대신하는 방향 | ★ **언어 보장** | 문서가 양쪽을 모두 명시 |
| `str` 해시에 소금이 섞이는 것 | ★ **언어 보장** | 문서가 「프로세스 간 예측 불가」라 명시 |
| `dataclasses` 의 `_hash_action` 8행 표 | ★ **CPython 구현**(표준 라이브러리) | 소스를 직접 읽었다 |
| ★ 어느 이름이 부딪히면 **터지고** 어느 이름이 **조용한가** | ★ **CPython 구현**(`dataclasses` 모듈의 동작) — 언어 문법 보장이 아니다 | 6번 답의 실측 |
| 그 예외들의 **문구** | ★ **이 판의 관찰** | 6번 답 |
| `FrozenInstanceError` 라는 타입 이름 | ★ **이 판의 관찰** | 6번 답 |
| `(exit 1)` | ★ **이 판의 관찰** | 1번 답의 두 블록 |

- ★★★ **가장 자주 틀리는 분류가 ② 다.** 「파이썬 `dict` 는 정체를 먼저 본다」는 문장이 널리 쓰이는데,
  **언어 레퍼런스에는 그런 약속이 없다.** 다른 구현에서 `__eq__` 가 불릴 수 있다.
- ★★ **「어기면 무엇이 나오나」 전체가 구현 층이다.** 「`len` 이 2 가 된다」·「`d.get(a)` 가 옛 값이다」는
  **이 구현에서 이렇게 되더라**이지 언어가 약속한 것이 아니다.
  Rust 갈래도 같은 분류를 했다 — 「계약을 어겼을 때 **정확히 무엇이 나오나**」는 구현 세부라고 적어 두었다
  ([Rust 28 「구현 세부사항 대 언어 보장」](../../../rust/syntax/28-partialeq-eq-partialord-ord-and-hash-contracts/2-summary.md)).
- ★ **언어 보장인 것은 「규칙」이고 구현인 것은 「증상」이다.** 이 한 줄로 가르면 거의 안 틀린다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 판 확인 | `python3 - <e30_version.py` | 1 | 3.12.3 · cpython · linux · `hash_randomization` `True` |
| `__eq__` 만 정의 → `hash()` | `python3 - <e30_only_eq.py` | 1 | 클래스 칸에 `None` · 세 줄 트레이스백 · `(exit 1)` |
| `__eq__` 만 정의 → `dict` 키 | `python3 - <e30_only_eq_dict.py` | 1 | 같은 예외·같은 문구 · `(exit 1)` |
| 고치는 법 둘 | `python3 - <e30_two_fixes.py` | 1 | 키 개수 `1` 대 `2` · `set` `1` 대 `2` |
| ★ 계약 위반과 복구 | `python3 - <e30_contract_break.py` | 1 | `d.get(b)` 가 `None` · `len` 2 · `list` 는 `True` · `Fixed` 는 전부 정상 |
| 반사성 위반 | `python3 - <e30_reflexivity.py` | 1 | ① 은 `__eq__` 없이 꺼내짐 · ③ 은 `None` · `len` 2 |
| `repr` 대 `str` | `python3 - <e30_repr_str.py` | 1 | `__repr__` 만 대신한다 · 컨테이너는 `repr` |
| `dataclass` 네 판 | `python3 - <e30_dataclass.py` | 1 | 기본은 해시 불가 · `frozen`·`unsafe_hash` 는 생성 |
| ★ `dataclass` 와 내 메서드의 충돌 여섯 자리 | `python3 - <e30_dataclass_raise.py` | 1 | **터진 넷 · 조용한 둘** · 조용한 `__eq__` 쪽은 `__hash__` 가 `None` |
| 해시값 인용 규칙 | `python3 - <e30_hash_values.py` | 1 | 소금 켜짐 · 정수 해시는 고정 · 충돌은 합법 |
| ★ 재대조 | `capture.sh` 를 처음부터 다시 돌려 `diff` | 2 | **전 블록 동일 · 흔들린 칸 0** |

**구현 의존 항목** — 판이 오르면 **다시 돌려야 하는 것**들이다.

| 항목 | 왜 흔들릴 수 있나 |
|---|---|
| 예외 **문구** 전부 | 판마다 문구가 바뀐다 |
| `FrozenInstanceError` 같은 **내부 타입 이름** | 표준 라이브러리의 구현이다 |
| **정체 지름길** — ① 에서 `__eq__` 가 안 불리는 것 | CPython 의 비교 관문이 하는 일이다 |
| **정수 해시의 값** — `hash(-1)` 이 `-2`, `hash(2**61-1)` 이 `0` | CPython 의 해시 알고리즘이다 |
| `dataclasses` 의 `_hash_action` 표 | 표준 라이브러리 소스다 |
| **어느 이름이 터지고 어느 이름이 조용한가** | `dataclasses` 모듈이 이름마다 다르게 처리한다 |
| 계약 위반 시의 **키 개수·조회 결과** | 「동작이 규정되지 않는다」의 이 구현에서의 모습이다 |

**안 흔들리는 것** — `hash_randomization` 이 켜진 한 **해시값은 늘 흔들리고**,
**「같은가 다른가」는 늘 안 흔들린다.** 이 문서는 그 경계 위에만 근거를 세웠다.
