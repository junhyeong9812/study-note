# python/syntax/30-repr-eq-hash-contracts — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> 실행 환경: `python3` **3.12.3** · Linux. 던지는 형태는 `python3 - <파일` 로 고정했다.
>
> ★★ **이 주제에서는 「예외가 안 나는 것」이 답인 자리가 대부분이다.**
> 「터진다」로 답하면 거의 다 틀린다 — **어느 조회가 실패하고 어느 것이 멀쩡한지**를 짚어야 맞은 것이다.\
> ★★★ **해시값을 적지 마라.** `sys.flags.hash_randomization` 이 `True` 라 값은 실행마다 달라진다.
> 답에 쓸 수 있는 것은 「**해시가 같은가 다른가**」뿐이다.\
> ★ 트레이스백이 나오는 문항은 **세 줄**이다 — 실행 중 예외라 **소스 줄도 `^` 캐럿도 없다.**\
> ★ 이 주제는 [12번](../12-dict-and-key-requirements/1-question.md)·[02번](../02-is-vs-eq-interning/1-question.md)·[29번](../29-classes-and-attribute-lookup/1-question.md)을 쓴다.
> 막히면 그 셋 중 무엇이 안 잡힌 것인지부터 짚어라.\
> ★ **이 사슬은 [29](../29-classes-and-attribute-lookup/1-question.md) → 30 → [31](../31-comparison-protocol-and-sortability/1-question.md) → [32](../32-container-protocol/1-question.md)** 로 이어진다.
> 29 가 「속성이 어디서 오나」, 30 이 「같음」, 31 이 「순서」, 32 가 「담음」의 계약이다.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. 네 줄을 찍고 마지막에 해시를 구하면 (예측)

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

- 첫 두 줄 — **클래스 칸에 `__hash__` 가 있나**, 그리고 있다면 그 값은 무엇인가?
- `OnlyEq(1) == OnlyEq(1)` 은 무엇을 돌려주는가?
- ★ 마지막 줄에서 **무슨 일**이 일어나는가? 트레이스백이 나온다면 **몇 줄**이고 **어떤 줄들**인가?
- 종료 코드는 무엇인가?

### 2. 두 가지 처방을 나란히 돌리면 (예측)

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

- 두 클래스 각각에서 `a == b` 는 무엇인가?
- ★ 두 클래스 각각에서 **해시가 같은가**?
- ★★ 두 클래스 각각에서 **키 개수**는 몇이고, `남은 것` 에 무엇이 찍히는가?
- 마지막 줄의 `set` 두 개는 각각 몇인가?

### 3. 대소문자를 무시하는 키 (예측)

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

- `a == b` 와 「해시가 같은가」는 각각 무엇인가?
- ★★★ `d.get(a)` 와 `d.get(b)` 는 각각 무엇을 돌려주는가?
- ★ `CaseKey("KEY")` 를 또 넣은 뒤 `len(d)` 는 몇인가? 그리고 그때 `d.get(a)` 는?
- ★ `set` 에 둘을 넣으면 몇이고, `list` 의 `in` 은 무엇인가?
- 마지막 `Fixed` 판에서는 **무엇이 어떻게 달라지는가**?

### 4. 자기 자신과도 다른 키 (예측)

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

- ★★★ ① 에서 `d.get(k)` 는 무엇을 돌려주고, 그때 `__eq__` 줄이 **찍히는가**?
- ② 의 `k == k` 는 무엇인가?
- ③ 과 ④ 에서 `len` 은 몇이 되는가?
- ⑤⑥ 에서 `list` 와 `set` 은 ① 과 같은 길을 타는가?

### 5. 한쪽만 정의한 세 클래스 (예측)

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

- 세 클래스 각각에서 `repr(o)` 와 `str(o)` 가 **기본 꼴인가**?
- ★ 세 클래스 각각에서 `str(o) == repr(o)` 는 무엇인가?
- ★★ `[OnlyStr()]` 의 표현은 **기본 꼴인가**?
- `f'{o}'` 와 `f'{o!r}'` 은 `OnlyRepr` 에서 어떻게 갈리는가?

### 6. 네 가지 `dataclass` 선언 (예측)

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

- 네 판 각각에서 **클래스 칸에 `__hash__` 가 있나**, 있다면 **그 값이 `None` 인가**?
- ★★ 네 판 각각에서 `hash()` 가 되는가?
- ★ 해시가 되는 판들에서 `a == b` 와 **키 개수**는 각각 무엇인가?
- ④ 에서 무엇이 찍히는가?

### 7. 계약의 조항을 세어 보라 (왜)

- `__eq__` 와 `__hash__` 사이의 다리는 **몇 방향**이고, 그 방향은 무엇인가?
- ★ 그 다리 중에서 **언어가 실제로 강제하는 것**은 무엇 하나인가?
- 「해시가 같은데 `==` 가 다른 것」은 위반인가?

### 8. 해시값을 문서에 적으면 안 되는 이유 (왜)

- `hash('key')` 의 **값**을 근거로 쓰면 무엇이 깨지는가?
- ★ 그런데 `hash(1)` 은 왜 적을 수 있는가? 그것은 **어느 층**의 사실인가?
- 해시값을 파일이나 DB 에 저장하면 안 되는 이유는 위와 같은 이유인가?

### 9. `list` 는 멀쩡한데 `dict` 만 틀리는 이유 (왜)

- 계약을 어긴 키가 **왜 리스트에서는 찾아지는가**?
- ★ `dict` 에서 `__eq__` 가 **불리지도 않는** 상황은 어떤 경우인가?
- 이 비대칭이 진단을 어떻게 막는가?

### 10. 정적 언어 셋과 갈리는 자리 (연결)

- Rust·Java·파이썬 중 **계약 내용을 컴파일러가 강제하는 언어**가 있는가?
- ★★ 세 언어에서 **「짝을 안 맞춘 것」을 잡아 주는 시점**은 각각 언제인가?
- ★ 파이썬에서 **조용히 틀리려면 무엇을 일부러 해야 하는가**?
- ★ 파이썬에만 있는 칸 하나는 무엇이고, 그것은 **언어 보장인가 구현인가**?

### 11. 12번이 정본인 것과 여기가 정본인 것 (경계)

- [12번](../12-dict-and-key-requirements/1-question.md)이 정본으로 다루는 것 **셋**을 대라.
- ★ 이 주제가 정본으로 다루는 것 **둘**을 대라.
- `dataclasses` 의 나머지(`field`·`order`·`default_factory`)는 어느 주제인가?

### 12. 세 층 가르기 (경계)

- 다음 중 **언어 보장**은 어느 것인가 — ① `__eq__` 를 재정의하면 `__hash__` 가 `None` 이 된다
  ② `dict` 는 같은 객체면 `__eq__` 를 안 부른다 ③ `hash(1)` 은 `1` 이다 ④ `unhashable type: 'OnlyEq'` 라는 문구?
- ★ 나머지 셋은 각각 **CPython 구현**인가 **이 판의 관찰**인가?
- ★ 「계약을 어기면 키 개수가 2 가 된다」는 어느 층인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|---|---|---|---|
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |
