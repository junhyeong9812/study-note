# python/syntax/29-classes-and-attribute-lookup — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> ★★ 이 주제에서는 **「어느 칸에서 나온 답인가」가 물음의 전부다.**
> 값만 맞히고 칸을 못 대면 반만 맞은 것이다 — `vars(obj)` 와 `Cls.__dict__` 를 **갈라서** 적어라.
> ★ 이 주제의 블록에는 **트레이스백이 한 줄도 없다.** 던진 예외 셋을 전부 `except` 로 잡아
> **타입과 메시지만** 찍었기 때문이다. 그래서 줄 번호를 외울 필요가 없다.
> ★ **주소(`0x…`)와 `id()` 는 한 번도 안 찍었다.** 예측에 주소가 필요한 문항은 없다.
>
> 실행 환경: `python3` **3.12.3** · Linux. 던지는 형태는 `python3 - <파일` 로 고정했다.
> ★ **이 주제는 [01번](../01-object-and-name-binding/1-question.md)·[03번](../03-mutability-and-copying/1-question.md)·[20번](../20-mutable-default-args/1-question.md)·[21번](../21-scope-legb-global-nonlocal/1-question.md)을 쓴다.**
> 막히면 그 넷 중 어느 것이 안 잡힌 것인지부터 짚어라.
> ★ **이 사슬은 29 → [30](../30-repr-eq-hash-contracts/1-question.md) → [31](../31-comparison-protocol-and-sortability/1-question.md) → [32](../32-container-protocol/1-question.md)** 로 이어지고, **여기가 첫째**다.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. 두 칸을 갈라 보면 (예측)

```python
# e29_lookup.py
class Base:
    kind = "base"                 # 클래스 칸에 산다
    def __init__(self, name):
        self.name = name          # 인스턴스 칸에 산다


class Derived(Base):
    kind = "derived"


d = Derived("첫째")
print("① 갓 만든 직후 — 두 칸을 갈라 본다")
print("   인스턴스 칸 vars(d)        :", vars(d))
print("   Derived 칸에 kind 가 있나  :", "kind" in Derived.__dict__, "->", Derived.__dict__.get("kind"))
print("   Base 칸에 kind 가 있나     :", "kind" in Base.__dict__, "->", Base.__dict__.get("kind"))
print("   d.kind                     ->", d.kind)
print("   d.name 은 어느 칸에 있나   :", "name" in vars(d), "| 클래스 칸:", "name" in Derived.__dict__)

print("② 인스턴스에 같은 이름을 대입하면")
d.kind = "인스턴스가 덮었다"
print("   vars(d)       :", vars(d))
print("   d.kind        ->", d.kind)
print("   Derived.kind  ->", Derived.kind, "  (클래스 칸은 그대로다)")

print("③ 인스턴스 칸에서 지우면 다시 클래스가 보인다")
del d.kind
print("   vars(d)       :", vars(d))
print("   d.kind        ->", d.kind)

print("④ 조상까지 내려가는 것 — Derived 칸의 kind 를 지우면")
del Derived.kind
print("   d.kind        ->", d.kind, "  (Base 칸의 것)")
print("   탐색이 지나간 길 :", [k.__name__ for k in type(d).__mro__])

print("⑤ vars(d) 는 사본이 아니라 그 dict 자체다")
vars(d)["extra"] = 42
print("   d.extra ->", d.extra, "| vars(d) is d.__dict__ ->", vars(d) is d.__dict__)
```

- ①에서 `d.kind` 는 무엇인가?
- ②를 지난 뒤 `Derived.kind` 는 무엇인가?
- ★ ③에서 `del d.kind` 를 한 뒤 `d.kind` 는 왜 `AttributeError` 가 아닌가?
- ★ ④에서 `del Derived.kind` 까지 한 뒤 `d.kind` 는 무엇인가?
- ⑤의 `vars(d) is d.__dict__` 는 무엇인가?

### 2. 장바구니 둘에 하나씩 넣으면 (예측)

```python
# e29_classvar.py
class Cart:
    items = []                     # ★ 클래스 칸에 사는 리스트 — 한 개뿐이다
    def add(self, x):
        self.items.append(x)       # 조회한 뒤 그 객체를 직접 고친다


a, b = Cart(), Cart()
a.add("사과")
b.add("배")
print("① append — 고치기")
print("   a.items          :", a.items)
print("   b.items          :", b.items)
print("   Cart.items       :", Cart.items)
print("   a.items is b.items :", a.items is b.items)
print("   vars(a) :", vars(a), "| vars(b) :", vars(b), "  <- 인스턴스 칸은 비어 있다")


class Cart2:
    items = []
    def add(self, x):
        self.items = self.items + [x]      # ★ 대입 — 인스턴스 칸이 생긴다


c, e = Cart2(), Cart2()
c.add("사과")
print("② 대입 — 새로 묶기")
print("   c.items :", c.items, "| e.items :", e.items, "| Cart2.items :", Cart2.items)
print("   vars(c) :", vars(c))
print("   vars(e) :", vars(e))

print("③ += 는 어느 쪽인가 — 리스트에서는 제자리 변경이다")
class Cart3:
    items = []
    def add(self, x):
        self.items += [x]

f = Cart3()
f.add("감")
print("   Cart3.items :", Cart3.items, "| vars(f) :", vars(f))
```

- ①에서 `a.items` 와 `b.items` 는 각각 무엇인가?
- ★ ①에서 `vars(a)` 와 `vars(b)` 에는 무엇이 들어 있나?
- ②에서 `c.items` 와 `Cart2.items` 는 각각 무엇인가?
- ★★ ③의 `+=` 가 지난 뒤 `Cart3.items` 와 `vars(f)` 는 각각 무엇인가?

### 3. 두 갈고리 중 무엇이 언제 불리나 (예측)

```python
# e29_getattr.py
class OnlyMissing:
    x = "클래스 칸의 x"

    def __getattr__(self, name):
        print("      __getattr__ 가 불렸다 :", name)
        return "<없어서 만든 %s>" % name


class Everything:
    x = "클래스 칸의 x"

    def __getattribute__(self, name):
        print("      __getattribute__ 가 불렸다 :", name)
        return object.__getattribute__(self, name)

    def __getattr__(self, name):
        print("      __getattr__ 도 불렸다 :", name)
        return "<없어서 만든 %s>" % name


o = OnlyMissing()
print("① __getattr__ 만 있는 객체 — 있는 이름")
print("   o.x ->", o.x)
print("② __getattr__ 만 있는 객체 — 없는 이름")
print("   o.zzz ->", o.zzz)

e = Everything()
print("③ 둘 다 있는 객체 — 있는 이름")
print("   e.x ->", e.x)
print("④ 둘 다 있는 객체 — 없는 이름")
print("   e.zzz ->", e.zzz)

print("⑤ hasattr 도 같은 길을 탄다")
print("   hasattr(o, 'zzz') ->", hasattr(o, "zzz"))
```

- ①에서 `__getattr__` 로그가 찍히는가?
- ★ ④에서 로그가 **몇 줄** 찍히고 그 순서는 무엇인가?
- ★ ⑤에서 `hasattr(o, 'zzz')` 는 무엇을 답하는가?
- ⑤를 지난 뒤 `vars(o)` 에는 무엇이 들어 있겠는가?

### 4. 인스턴스 칸과 클래스 칸에 같은 이름이 있으면 (예측)

```python
# e29_descriptor.py
class DataDesc:                      # __get__ 과 __set__ 이 둘 다 있으면 데이터 디스크립터
    def __get__(self, obj, objtype=None):
        return "데이터 디스크립터가 답한다"

    def __set__(self, obj, value):
        print("      DataDesc.__set__ 이 가로챘다 :", value)
        obj.__dict__["slot"] = value      # 인스턴스 칸에 넣기는 한다


class NonDataDesc:                   # __get__ 만 있으면 비데이터 디스크립터
    def __get__(self, obj, objtype=None):
        return "비데이터 디스크립터가 답한다"


class C:
    slot = DataDesc()
    plain = NonDataDesc()


c = C()
print("① 데이터 디스크립터 — 인스턴스 칸에 값이 있어도")
c.slot = "인스턴스 칸에 직접 넣은 값"
print("   vars(c)            :", vars(c))
print("   vars(c)['slot']    ->", vars(c)["slot"])
print("   c.slot             ->", c.slot, "   <- 인스턴스 칸을 이겼다")

print("② 비데이터 디스크립터 — 인스턴스 칸이 이긴다")
print("   덮기 전 c.plain    ->", c.plain)
c.__dict__["plain"] = "인스턴스 칸에 직접 넣은 값"
print("   vars(c)['plain']   ->", vars(c)["plain"])
print("   c.plain            ->", c.plain, "   <- 인스턴스 칸이 이겼다")

print("③ 무엇이 데이터인가는 __set__/__delete__ 유무로 갈린다")
for nm, cls in (("DataDesc", DataDesc), ("NonDataDesc", NonDataDesc)):
    print("   %-12s __get__:%s __set__:%s" % (nm, hasattr(cls, "__get__"), hasattr(cls, "__set__")))

print("④ 함수도 비데이터 디스크립터다 — 그래서 인스턴스 칸으로 덮인다")
class M:
    def go(self): return "클래스의 메서드"

m = M()
print("   m.go()             ->", m.go())
m.__dict__["go"] = lambda: "인스턴스 칸의 함수"
print("   덮은 뒤 m.go()     ->", m.go())
print("   function 에 __set__ 이 있나 :", hasattr(type(M.go), "__set__"))
```

- ①에서 `vars(c)['slot']` 과 `c.slot` 이 같은가?
- ★ ②에서 `c.plain` 은 무엇인가?
- ③의 두 줄을 보고 「무엇이 갈림길인가」를 한 낱말로 대라.
- ★★ ④에서 `m.__dict__['go']` 를 덮은 뒤 `m.go()` 는 무엇을 부르는가?

### 5. 같은 `super()` 한 줄을 두 곳에서 부르면 (예측)

```python
# e29_super.py
class Base:
    def go(self):
        print("      Base.go")


class Left(Base):
    def go(self):
        print("      Left.go   — super() 를 부른다")
        super().go()


class Right(Base):
    def go(self):
        print("      Right.go  — super() 를 부른다")
        super().go()


class Both(Left, Right):
    def go(self):
        print("      Both.go   — super() 를 부른다")
        super().go()


print("① Left 의 「부모」는 글자 그대로 Base 다")
print("   Left.__bases__ :", [k.__name__ for k in Left.__bases__])
print("   Left() 를 그냥 부르면")
Left().go()

print("② 그런데 Both 안에서는 Left 의 super() 가 Right 로 간다")
print("   Both.__mro__ :", [k.__name__ for k in Both.__mro__])
print("   Both() 를 부르면")
Both().go()

print("③ super() 는 「타입」이 아니라 「인스턴스의 MRO 에서 내 다음」을 가리킨다")
s = super(Left, Both())
print("   super(Left, Both()) 가 고른 go 의 주인 :", s.go.__qualname__.split(".")[0])
s2 = super(Left, Left())
print("   super(Left, Left())  가 고른 go 의 주인 :", s2.go.__qualname__.split(".")[0])
```

- ①에서 `Left()` 를 부르면 로그가 몇 줄이고 무엇인가?
- ★★ ②에서 `Both()` 를 부르면 로그가 몇 줄이고 무엇인가?
- ★ ②에서 `Base.go` 는 **몇 번** 찍히는가?
- ③의 두 줄은 각각 무엇을 답하는가?

### 6. `__slots__` 를 단 객체에 이것저것 해 보면 (예측)

```python
# e29_slots.py
class WithDict:
    def __init__(self, x):
        self.x = x


class WithSlots:
    __slots__ = ("x",)

    def __init__(self, x):
        self.x = x


a, b = WithDict(1), WithSlots(1)
print("① __dict__ 가 있나")
print("   WithDict  :", hasattr(a, "__dict__"), "->", getattr(a, "__dict__", None))
print("   WithSlots :", hasattr(b, "__dict__"))

print("② 클래스 칸에 무엇이 생겼나")
print("   WithSlots.__slots__ :", WithSlots.__slots__)
print("   클래스 칸의 이름들  :", sorted(k for k in WithSlots.__dict__ if not k.startswith("__")))
print("   x 의 정체           :", type(WithSlots.__dict__["x"]).__name__)
print("   그것이 데이터 디스크립터인가 :", hasattr(type(WithSlots.__dict__["x"]), "__set__"))

print("③ 새 속성을 붙여 보면")
a.extra = 1
print("   WithDict.extra  ->", a.extra)
try:
    b.extra = 1
except AttributeError as ex:
    print("   WithSlots       -> AttributeError:", ex)

print("④ vars() 는 __dict__ 를 돌려주는 함수다")
try:
    vars(b)
except TypeError as ex:
    print("   vars(WithSlots 인스턴스) -> TypeError:", ex)

print("⑤ 하위 클래스가 __slots__ 를 안 쓰면 __dict__ 가 되살아난다")
class Child(WithSlots):
    pass

c = Child(1)
print("   Child 인스턴스에 __dict__ 가 있나 :", hasattr(c, "__dict__"))
c.extra = 1
print("   Child.extra ->", c.extra)
```

- ①에서 `hasattr(b, '__dict__')` 는 무엇인가?
- ★ ②에서 `WithSlots.__dict__["x"]` 의 타입 이름은 무엇이고, 그것이 데이터 디스크립터인가?
- ③에서 `b.extra = 1` 은 어떤 예외를 내는가?
- ★ ④에서 `vars(b)` 는 어떤 예외를 내는가?
- ★★ ⑤에서 `Child` 인스턴스에 `__dict__` 가 있는가?

### 7. 다이아몬드의 한 줄을 누가 정하나 (왜)

- `D(B, C)`·`B(A)`·`C(A)` 일 때 `D.__mro__` 가 `D B C A object` 가 되는 규칙의 이름은 무엇이고, **공통 조상 `A` 가 반드시 뒤로 가는 이유**는 무엇인가?
- ★ `class Bad(A, B)` 처럼 **조상을 먼저 적으면** 언제 무엇이 터지는가?
- ★ 그 오류 메시지가 **한 줄이 아닌** 이유는 무엇인가?

### 8. `__init__` 앞에 무엇이 있나 (경계)

- `Point(3)` 한 줄이 부르는 두 메서드는 무엇이고, **둘 중 어느 것이 객체를 만드나**?
- ★ `__new__` 가 **무엇을 돌려줄 때** `__init__` 이 안 불리는가?
- ★ 풀에서 꺼낸 **기존 인스턴스**를 `__new__` 가 돌려주면 `__init__` 은 불리는가?

### 9. 이름 탐색과 속성 탐색은 어떻게 다른가 (연결)

- `x` 를 찾는 규칙(LEGB)과 `obj.x` 를 찾는 규칙은 각각 어디를 어떤 순서로 보는가?
- ★ 둘 중 **어느 쪽이 「컴파일 시점에 이미 정해져 있는」 것**인가?
- ★ 클래스 몸통에 쓴 `kind` 를 메서드 안에서 **그냥 `kind` 로** 읽으면 무슨 일이 일어나는가?

### 10. 20번의 가변 기본값과 같은 집안인 이유 (연결)

- `def f(x=[])` 의 리스트와 `class C: items = []` 의 리스트가 **공통으로 가진 성질** 한 줄은 무엇인가?
- ★ 두 경우의 처방이 같은 모양인 이유는 무엇인가?
- ★ 증상이 **간헐적으로** 보이는 이유는 각각 무엇인가?

### 11. 세 층 가르기 (경계)

- 「인스턴스 칸이 먼저고 없으면 클래스, 없으면 조상」은 **언어 보장인가 CPython 구현인가**?
- 「데이터 디스크립터가 인스턴스 칸을 이긴다」는 어느 층인가?
- ★ 「`__slots__` 가 만드는 것의 타입 이름이 `member_descriptor` 다」는 어느 층인가?
- ★ 「`vars(obj)` 에 값을 넣으면 속성이 된다」는 어느 층인가?

### 12. 이웃 주제와의 경계 (연결)

- **이름**이 풀리는 규칙은 어느 주제가 정본인가?
- `property`·디스크립터·`__slots__` 의 **정본**은 어느 주제인가? 여기서는 왜 그 일부만 다루나?
- ★ 이 주제의 「**특수 메서드는 클래스 칸에서 찾는다**」가 사슬의 다음 셋에서 각각 무엇으로 이어지는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|---|---|---|---|
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |

> 채점 기준 — **값을 맞혔더라도 「어느 칸에서 나온 답인가」를 못 대면 틀린 것으로 적는다.**
> 이 주제의 인출 목표가 값이 아니라 **경로**이기 때문이다.
