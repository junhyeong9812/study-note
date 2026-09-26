# python/syntax/29-classes-and-attribute-lookup — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> [1-question.md](1-question.md)의 번호와 **1:1**로 대응한다. 질문 12개 = 답 12개.
>
> 이 파일의 모든 출력은 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> 던지는 형태는 `python3 - <파일` 로 고정했다.
> ★ **이 파일에는 트레이스백이 한 줄도 없다** — 던진 예외 셋을 전부 `except` 로 잡아
> **타입과 메시지만** 찍었기 때문이다.
> ★ 이 파일의 블록에는 **주소도 시간도 절대경로도 안 찍힌다** — 같은 판에서 다시 돌리면 **한 글자도 안 변한다.**
> 단 **예외 문구**와 **`member_descriptor` 같은 내부 타입 이름**은 구현·판에 달린 것이다(11번 답).

## 정답

### 1. 클래스 칸은 계단이고, 인스턴스 칸은 그 계단의 첫 칸이다

**출력**

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
```text
===== python3 - <e29_lookup.py =====
① 갓 만든 직후 — 두 칸을 갈라 본다
   인스턴스 칸 vars(d)        : {'name': '첫째'}
   Derived 칸에 kind 가 있나  : True -> derived
   Base 칸에 kind 가 있나     : True -> base
   d.kind                     -> derived
   d.name 은 어느 칸에 있나   : True | 클래스 칸: False
② 인스턴스에 같은 이름을 대입하면
   vars(d)       : {'name': '첫째', 'kind': '인스턴스가 덮었다'}
   d.kind        -> 인스턴스가 덮었다
   Derived.kind  -> derived   (클래스 칸은 그대로다)
③ 인스턴스 칸에서 지우면 다시 클래스가 보인다
   vars(d)       : {'name': '첫째'}
   d.kind        -> derived
④ 조상까지 내려가는 것 — Derived 칸의 kind 를 지우면
   d.kind        -> base   (Base 칸의 것)
   탐색이 지나간 길 : ['Derived', 'Base', 'object']
⑤ vars(d) 는 사본이 아니라 그 dict 자체다
   d.extra -> 42 | vars(d) is d.__dict__ -> True
(exit 0)
```

**왜 그런가**

- ①에서 **`d.kind` 는 `derived`** 다.\
  `Base` 칸에도 `base` 가 있지만 **`Derived` 칸이 계단에서 앞**이라 그쪽이 이긴다.\
  문서가 첫 칸을 못 박는다 — *"A class instance has a namespace implemented as a dictionary
  which is the **first place** in which attribute references are searched."*\
  ★ 그 문장은 **디스크립터가 없는 보통의 경우**를 말한 것이다. 전수 규칙은 4번 답의 네 층이다.
- **`name` 은 인스턴스 칸에만 있다.** `"name" in vars(d)` 가 `True` 이고 클래스 칸에는 `False` 다.\
  `__init__` 안의 `self.name = name` 이 한 일은 **그 칸에 넣은 것**뿐이다.
- ②를 지난 뒤에도 **`Derived.kind` 는 `derived` 그대로**다.\
  ★ **덮은 것이 아니라 가린 것**이다 — 인스턴스 칸에 같은 이름이 생겨 **앞을 막았을 뿐**이다.
- ★ ③에서 `del d.kind` 는 **인스턴스 칸에서만** 지운다.\
  클래스 칸의 것은 그대로 있으므로 `AttributeError` 가 아니라 **`derived` 가 다시 드러난다.**
- ★ ④에서 `del Derived.kind` 까지 하면 계단을 한 칸 더 올라가 **`base`** 가 나온다.\
  그 계단이 `['Derived', 'Base', 'object']` 이고, 그것이 곧 `type(d).__mro__` 다.
- ⑤의 **`vars(d) is d.__dict__` 는 `True`** 다.\
  ★ **진단창이 곧 저장소**라서 `vars(d)["extra"] = 42` 가 실제로 `d.extra` 를 만든다.

★ **한 줄 요약** — `obj.x` 는 **칸들의 사슬**을 훑는다. 인스턴스 칸은 그 사슬의 **첫 칸**일 뿐이고,
거기서 지운다고 속성이 사라지는 것이 아니라 **가림이 풀릴** 뿐이다.

### 2. `append` 는 한 개를 고치고, 대입은 새 칸을 만들고, `+=` 는 둘 다 한다

**출력**

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
```text
===== python3 - <e29_classvar.py =====
① append — 고치기
   a.items          : ['사과', '배']
   b.items          : ['사과', '배']
   Cart.items       : ['사과', '배']
   a.items is b.items : True
   vars(a) : {} | vars(b) : {}   <- 인스턴스 칸은 비어 있다
② 대입 — 새로 묶기
   c.items : ['사과'] | e.items : [] | Cart2.items : []
   vars(c) : {'items': ['사과']}
   vars(e) : {}
③ += 는 어느 쪽인가 — 리스트에서는 제자리 변경이다
   Cart3.items : ['감'] | vars(f) : {'items': ['감']}
(exit 0)
```

**왜 그런가**

- ★ ①에서 **`a.items` 와 `b.items` 가 둘 다 `['사과', '배']`** 다.\
  `self.items.append(x)` 는 **조회 + 고치기**다. 조회는 계단을 올라가 **클래스 칸의 그 한 개**를 찾고,
  `append` 는 **찾은 그 객체를 건드린다.** `a.items is b.items` 가 `True` 인 것이 그 증거다.
- ★★ **그런데 `vars(a)` 도 `vars(b)` 도 `{}`** 다.\
  **값은 인스턴스에 있는 것처럼 보이는데 인스턴스 칸은 비어 있다** — 증상과 진단이 어긋나는 자리다.\
  `vars()` 만 보고 「아무것도 없네」 하면 이 버그를 못 잡는다.
- ②의 `self.items = self.items + [x]` 는 **새로 묶기**다.\
  오른쪽에서 새 리스트를 만들고 그것을 **인스턴스 칸에 대입**하므로
  **`c.items` 는 `['사과']`, `Cart2.items` 는 `[]`** 이고 `vars(c)` 에 `items` 가 생긴다.\
  `e` 는 아무것도 안 했으므로 `vars(e)` 가 `{}` 이고 `e.items` 는 클래스 칸의 `[]` 를 본다.
- ★★ ③의 `self.items += [x]` 는 **둘 다 한다.**\
  리스트의 `+=` 는 **제자리 확장**이라 클래스 칸의 리스트가 늘어나고(**`Cart3.items` 가 `['감']`**),
  그 결과를 **다시 `self.items` 에 대입**하므로 인스턴스 칸도 생긴다(**`vars(f)` 가 `{'items': ['감']}`**).\
  ★ 「대입이니까 클래스 칸은 안전하겠지」가 여기서 깨진다.
- [03번](../03-mutability-and-copying/2-summary.md)의 고치기/새로 묶기 구분이 그대로 걸리는 자리다.

★ **고치는 법** — 가변 클래스 변수를 쓰지 말고 `__init__` 안에서 `self.items = []` 로 만든다.
[20번](../20-mutable-default-args/2-summary.md)의 `None` 센티널과 **같은 처방**이다(10번 답).

### 3. `__getattr__` 은 실패 갈고리, `__getattribute__` 는 무조건 갈고리다

**출력**

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
```text
===== python3 - <e29_getattr.py =====
① __getattr__ 만 있는 객체 — 있는 이름
   o.x -> 클래스 칸의 x
② __getattr__ 만 있는 객체 — 없는 이름
      __getattr__ 가 불렸다 : zzz
   o.zzz -> <없어서 만든 zzz>
③ 둘 다 있는 객체 — 있는 이름
      __getattribute__ 가 불렸다 : x
   e.x -> 클래스 칸의 x
④ 둘 다 있는 객체 — 없는 이름
      __getattribute__ 가 불렸다 : zzz
      __getattr__ 도 불렸다 : zzz
   e.zzz -> <없어서 만든 zzz>
⑤ hasattr 도 같은 길을 탄다
      __getattr__ 가 불렸다 : zzz
   hasattr(o, 'zzz') -> True
(exit 0)
```

**왜 그런가**

- ★ ①에서 **로그가 안 찍힌다.** `o.x` 는 클래스 칸에서 찾았으므로 `__getattr__` 이 **안 불린다.**\
  문서가 그대로 적는다 — *"Note that if the attribute is found through the normal mechanism,
  `__getattr__()` is **not called**."*\
  ★ **로그가 없다는 것 자체가 근거**다.
- ②에서는 `zzz` 가 아무 칸에도 없어 기본 탐색이 `AttributeError` 로 실패했고, 그때 갈고리가 걸렸다.
- ★ ③에서 **`__getattribute__` 는 있는 이름에도 불린다.** 문서가 *"Called **unconditionally**"* 라고 적는다.
- ★★ ④에서 **로그가 두 줄이고 순서가 `__getattribute__` → `__getattr__`** 이다.\
  둘은 경쟁이 아니라 **직렬**이다. `__getattribute__` 가 먼저 다 하고,
  그것이 `AttributeError` 를 내면 그제야 `__getattr__` 이 이어 불린다.
- ★ ⑤에서 **`hasattr(o, 'zzz')` 가 `True`** 다.\
  `hasattr` 는 실제로 접근해 보고 예외가 안 나면 참을 답하는데, `__getattr__` 이 **무엇을 물어도 만들어 주므로**
  **언제나 `True`** 가 된다.
- ★★ 그런데 **`vars(o)` 에는 아무것도 안 생긴다.**\
  값이 **어느 칸에도 없는데** 접근은 성공하는 것 — 이것이 서머리에서 말한 **제5의 상태**다.\
  세 창(`vars`·`__dict__`·`__mro__`)이 전부 「없음」을 답하는데 `hasattr` 만 「있음」이라고 한다.

★ **`__getattribute__` 안에서 `self.무엇` 을 쓰면 무한 재귀**다.
실험이 `object.__getattribute__(self, name)` 을 쓴 이유가 그것이다.

### 4. 데이터 디스크립터는 인스턴스 칸을 이기고, 비데이터는 진다

**출력**

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
```text
===== python3 - <e29_descriptor.py =====
① 데이터 디스크립터 — 인스턴스 칸에 값이 있어도
      DataDesc.__set__ 이 가로챘다 : 인스턴스 칸에 직접 넣은 값
   vars(c)            : {'slot': '인스턴스 칸에 직접 넣은 값'}
   vars(c)['slot']    -> 인스턴스 칸에 직접 넣은 값
   c.slot             -> 데이터 디스크립터가 답한다    <- 인스턴스 칸을 이겼다
② 비데이터 디스크립터 — 인스턴스 칸이 이긴다
   덮기 전 c.plain    -> 비데이터 디스크립터가 답한다
   vars(c)['plain']   -> 인스턴스 칸에 직접 넣은 값
   c.plain            -> 인스턴스 칸에 직접 넣은 값    <- 인스턴스 칸이 이겼다
③ 무엇이 데이터인가는 __set__/__delete__ 유무로 갈린다
   DataDesc     __get__:True __set__:True
   NonDataDesc  __get__:True __set__:False
④ 함수도 비데이터 디스크립터다 — 그래서 인스턴스 칸으로 덮인다
   m.go()             -> 클래스의 메서드
   덮은 뒤 m.go()     -> 인스턴스 칸의 함수
   function 에 __set__ 이 있나 : False
(exit 0)
```

**왜 그런가**

- ★★ ①에서 **`vars(c)['slot']` 과 `c.slot` 이 다르다.**\
  `vars(c)` 에는 `'인스턴스 칸에 직접 넣은 값'` 이 버젓이 있는데 `c.slot` 은 `데이터 디스크립터가 답한다` 를 준다.\
  문서가 우선순위를 한 문장으로 적는다 — *"**data descriptors take precedence over instance dictionaries**,
  instance dictionaries take precedence over non-data descriptors,
  and non-data descriptors take precedence over class variables."*
- ★ 대입조차 가로채였다 — `c.slot = ...` 가 `DataDesc.__set__` 을 먼저 불렀다.\
  데이터 디스크립터는 **읽기와 쓰기 양쪽**을 잡는다.
- ②에서 **`c.plain` 은 `인스턴스 칸에 직접 넣은 값`** 이다.\
  덮기 전에는 디스크립터가 답했지만, 인스턴스 칸에 값이 들어오는 순간 **진다.**
- ③의 갈림길을 한 낱말로 대면 **`__set__`** 이다(`__delete__` 도 같은 자격이다).\
  `DataDesc` 는 `__get__:True __set__:True`, `NonDataDesc` 는 `__get__:True __set__:False` 다.\
  ★ **두 경우의 `vars(c)` 는 똑같다.** 갈리는 것은 **클래스 칸에 놓인 물건의 성질** 하나뿐이다.
- ★★ ④가 매일 지나가는 자리다. **함수가 비데이터 디스크립터**다(`function` 에 `__set__` 이 없다).\
  그래서 `m.__dict__['go']` 를 덮으면 **인스턴스 칸이 이겨** `m.go()` 가 `인스턴스 칸의 함수` 를 부른다.\
  ★ 거꾸로 읽으면 **메서드를 인스턴스별로 갈아끼울 수 있는 것**이 이 우선순위 덕분이다.

★ **네 번째 창이 필요한 이유가 이 문항이다** — 세 창이 전부 정상인데 답이 다르다.
찾은 것에 `__set__` 이 있는지를 묻지 않으면 원리상 못 가른다.

### 5. `super()` 는 「그 인스턴스의 MRO 에서 내 다음」이다

**출력**

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
```text
===== python3 - <e29_super.py =====
① Left 의 「부모」는 글자 그대로 Base 다
   Left.__bases__ : ['Base']
   Left() 를 그냥 부르면
      Left.go   — super() 를 부른다
      Base.go
② 그런데 Both 안에서는 Left 의 super() 가 Right 로 간다
   Both.__mro__ : ['Both', 'Left', 'Right', 'Base', 'object']
   Both() 를 부르면
      Both.go   — super() 를 부른다
      Left.go   — super() 를 부른다
      Right.go  — super() 를 부른다
      Base.go
③ super() 는 「타입」이 아니라 「인스턴스의 MRO 에서 내 다음」을 가리킨다
   super(Left, Both()) 가 고른 go 의 주인 : Right
   super(Left, Left())  가 고른 go 의 주인 : Base
(exit 0)
```

**왜 그런가**

- ① `Left()` 를 부르면 로그가 **두 줄**이다 — `Left.go` → `Base.go`.\
  `Left.__bases__` 가 `['Base']` 이므로 **여기까지는 「부모」로 읽어도 맞는다.**
- ★★ ② `Both()` 를 부르면 로그가 **네 줄**이다 — `Both.go` → `Left.go` → **`Right.go`** → `Base.go`.\
  같은 `Left.go` 안의 **같은 `super().go()` 한 줄**인데 이번에는 `Right` 로 갔다.\
  `Right` 는 **`Left` 의 부모가 아니라 형제**다.
- 문서가 그 규칙을 예까지 들어 적는다 — *"The **search starts from the class right after the type**.
  For example, if `__mro__` of object-or-type is `D -> B -> C -> A -> object` and the value of type is `B`,
  then `super()` searches `C -> A -> object`."*\
  ★ 실험의 MRO 가 `Both Left Right Base object` 이고 `type` 이 `Left` 이므로 **다음은 `Right`** 다.
  문서의 예와 **글자만 다르고 모양이 같다.**
- ★ ②에서 **`Base.go` 는 딱 한 번** 찍힌다.\
  다이아몬드에서 공통 조상을 **한 번만** 거치는 것이 이 장치의 값이다.\
  ★ 그러려면 **모든 참여자가 `super()` 를 불러야** 한다. `Right.go` 가 안 불렀으면 `Base.go` 가 안 찍혔을 것이다.
- ③의 두 줄이 그것을 한 줄로 증명한다 —
  `super(Left, Both())` 가 고른 주인은 **`Right`**, `super(Left, Left())` 가 고른 주인은 **`Base`** 다.\
  ★ **왼쪽 인자는 같고 오른쪽 인스턴스만 다르다.** 「다음」을 정하는 것은 **인스턴스의 타입**이다.

### 6. `__slots__` 는 사물함을 없애고 그 자리에 데이터 디스크립터를 놓는다

**출력**

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
```text
===== python3 - <e29_slots.py =====
① __dict__ 가 있나
   WithDict  : True -> {'x': 1}
   WithSlots : False
② 클래스 칸에 무엇이 생겼나
   WithSlots.__slots__ : ('x',)
   클래스 칸의 이름들  : ['x']
   x 의 정체           : member_descriptor
   그것이 데이터 디스크립터인가 : True
③ 새 속성을 붙여 보면
   WithDict.extra  -> 1
   WithSlots       -> AttributeError: 'WithSlots' object has no attribute 'extra'
④ vars() 는 __dict__ 를 돌려주는 함수다
   vars(WithSlots 인스턴스) -> TypeError: vars() argument must have __dict__ attribute
⑤ 하위 클래스가 __slots__ 를 안 쓰면 __dict__ 가 되살아난다
   Child 인스턴스에 __dict__ 가 있나 : True
   Child.extra -> 1
(exit 0)
```

**왜 그런가**

- ① **`hasattr(b, '__dict__')` 가 `False`** 다. 인스턴스에 `dict` 가 아예 없다.\
  문서가 결과를 적는다 — *"Without a `__dict__` variable, instances cannot have new variables
  not listed in the `__slots__` definition."*
- ★★ ② 클래스 칸에 `x` 가 생겼고 그 타입 이름이 **`member_descriptor`** 이며
  **데이터 디스크립터다**(`__set__` 이 있다).\
  ★ 그래서 `__slots__` 는 **별도 장치가 아니라 디스크립터 한 벌**이다 — 4번 답의 우선순위 규칙이 그대로 적용된다.\
  ★ **이름 자체는 CPython 의 것**이다(11번 답). 안 흔들리는 것은 **성질** 쪽이다.
- ③ `b.extra = 1` 은 **`AttributeError`** 다.
  문구는 `'WithSlots' object has no attribute 'extra'` 이고, **오타를 잡아 주는 부수 효과**가 여기서 나온다.
- ★ ④ `vars(b)` 는 **`TypeError`** 다 — `vars() argument must have __dict__ attribute`.\
  **진단창 하나가 통째로 막히는 것**이므로 이런 객체는 `Cls.__dict__` 와 `__slots__` 로 본다.
- ★★ ⑤ **`Child` 인스턴스에는 `__dict__` 가 있다.**\
  하위 클래스가 `__slots__` 를 선언하지 않으면 **되살아난다.** 그래서 `c.extra = 1` 이 된다.\
  ★ **상속 사슬 전체가 선언해야** 효과가 남는다. 한 군데만 빠져도 조용히 풀린다.

★ 절약이 목적인 장치인데 **얼마나 아끼는지는 안 쟀다.** 대가 쪽은 출력이 전부 보여 준다.

### 7. C3 가 정하고, 공통 조상은 반드시 뒤로 간다

**출력**

```python
# e29_mro.py
class A:
    def who(self):
        return "A"


class B(A):
    def who(self):
        return "B"


class C(A):
    def who(self):
        return "C"


class D(B, C):
    pass


print("① 다이아몬드 — D(B, C), B(A), C(A)")
for i, k in enumerate(D.__mro__):
    print("   %d. %s" % (i, k.__name__))
print("   D().who() ->", D().who())
print("   D.mro() 와 D.__mro__ 가 같은가 :", D.mro() == list(D.__mro__))

print("② 같은 이름을 가진 조상이 여럿이어도 MRO 는 한 줄이다")
print("   B 가 C 보다 앞인가 :", D.__mro__.index(B) < D.__mro__.index(C))
print("   A 가 둘보다 뒤인가 :", D.__mro__.index(A) > D.__mro__.index(C))
print("   object 가 맨 끝인가 :", D.__mro__[-1] is object)

print("③ C3 가 못 만드는 순서 — class Bad(A, B) 는 A 가 B 의 조상이다")
try:
    class Bad(A, B):
        pass
except TypeError as ex:
    print("   TypeError:", ex)

print("④ 속성 탐색은 이 순서를 그대로 쓴다")
D.mark = "D 가 가진 것"
C.mark = "C 가 가진 것"
d = D()
print("   d.mark ->", d.mark)
del D.mark
print("   D 칸에서 지운 뒤 d.mark ->", d.mark)
```
```text
===== python3 - <e29_mro.py =====
① 다이아몬드 — D(B, C), B(A), C(A)
   0. D
   1. B
   2. C
   3. A
   4. object
   D().who() -> B
   D.mro() 와 D.__mro__ 가 같은가 : True
② 같은 이름을 가진 조상이 여럿이어도 MRO 는 한 줄이다
   B 가 C 보다 앞인가 : True
   A 가 둘보다 뒤인가 : True
   object 가 맨 끝인가 : True
③ C3 가 못 만드는 순서 — class Bad(A, B) 는 A 가 B 의 조상이다
   TypeError: Cannot create a consistent method resolution
order (MRO) for bases A, B
④ 속성 탐색은 이 순서를 그대로 쓴다
   d.mark -> D 가 가진 것
   D 칸에서 지운 뒤 d.mark -> C 가 가진 것
(exit 0)
```

**왜 그런가**

- 규칙의 이름은 **C3 선형화**다.
  문서가 직접 적는다 — *"This search of the base classes uses the **C3 method resolution order**
  which behaves correctly even in the presence of 'diamond' inheritance structures."*
- ★ **공통 조상 `A` 가 반드시 뒤로 가는 이유** — 그래야 `A` 의 것을 **한 번만** 거칠 수 있다.\
  `A` 가 `B` 보다 앞에 오면 `B` 가 재정의한 것이 **영영 안 불린다.**
  C3 는 「자식은 언제나 부모보다 앞」과 「적은 순서(`B` 다음 `C`)를 지킨다」 둘을 동시에 만족시키는 한 줄을 만든다.
- ② 가 그 성질 셋을 확인한다 — `B` 가 `C` 보다 앞, `A` 가 둘보다 뒤, `object` 가 맨 끝.
- ★ `class Bad(A, B)` 는 **클래스를 정의하는 시점에** `TypeError` 다. 인스턴스를 안 만들어도 터진다.\
  `A` 가 `B` 의 조상인데 `A` 를 먼저 적었으므로 「자식이 부모보다 앞」과 「적은 순서」가 **동시에 성립할 수 없다.**
- ★★ 그 문구가 **두 줄로 나오는 이유는 메시지 안에 개행이 박혀 있기 때문**이다.\
  출력을 접은 것이 아니라 `Cannot create a consistent method resolution` 과
  `order (MRO) for bases A, B` 사이에 **진짜 줄바꿈**이 들어 있다.
  ★ 블록을 손질하지 않고 그대로 실었다 — 규칙 19의 「한 글자도 더하거나 빼지 마라」다.
- ④ 가 「속성 탐색이 이 순서를 그대로 쓴다」를 잇는다.
  `D.mark` 를 지우니 **`B` 를 건너뛰고** `C.mark` 가 나왔다 — `B` 에는 `mark` 가 없기 때문이다.

### 8. `__new__` 가 만들고 `__init__` 이 채운다 — 그리고 건너뛸 수 있다

**출력**

```python
# e29_new_init.py
class Point:
    def __new__(cls, *args, **kwargs):
        print("      __new__  — 빈 객체를 만든다. cls =", cls.__name__, "| 받은 인자 =", args)
        obj = super().__new__(cls)
        print("      __new__  — 만든 것의 vars :", vars(obj))
        return obj

    def __init__(self, x):
        print("      __init__ — 이미 있는 객체를 채운다. 받은 인자 =", (x,))
        self.x = x


print("① Point(3) 은 두 단계다")
p = Point(3)
print("   p.x =", p.x)

print("② __new__ 가 그 클래스의 인스턴스를 안 돌려주면 __init__ 이 안 불린다")


class NotReturning:
    def __new__(cls, x):
        print("      __new__ 가 아무것도 안 돌려준다")

    def __init__(self, x):
        print("      __init__ 이 불렸다")
        self.x = x


n = NotReturning(3)
print("   NotReturning(3) ->", n)

print("③ 다른 타입을 돌려줘도 같다")


class Sneaky:
    def __new__(cls, x):
        return [x]

    def __init__(self, x):
        print("      __init__ 이 불렸다")


print("   Sneaky(3) ->", Sneaky(3), "| 타입 :", type(Sneaky(3)).__name__)
```
```text
===== python3 - <e29_new_init.py =====
① Point(3) 은 두 단계다
      __new__  — 빈 객체를 만든다. cls = Point | 받은 인자 = (3,)
      __new__  — 만든 것의 vars : {}
      __init__ — 이미 있는 객체를 채운다. 받은 인자 = (3,)
   p.x = 3
② __new__ 가 그 클래스의 인스턴스를 안 돌려주면 __init__ 이 안 불린다
      __new__ 가 아무것도 안 돌려준다
   NotReturning(3) -> None
③ 다른 타입을 돌려줘도 같다
   Sneaky(3) -> [3] | 타입 : list
(exit 0)
```

**왜 그런가**

- `Point(3)` 한 줄이 부르는 것은 **`__new__` 와 `__init__`** 이고, **객체를 만드는 쪽은 `__new__`** 다.\
  출력에서 `__new__` 가 먼저 불리고 그때 `vars(obj)` 가 **`{}`** 이며,
  그 다음에 `__init__` 이 **같은 인자 `(3,)`** 를 받아 채운다.
- ★ **`__new__` 가 cls 의 인스턴스를 안 돌려주면** `__init__` 이 안 불린다.\
  문서가 조건을 적는다 — *"If `__new__()` does not return an instance of cls,
  then the new instance's `__init__()` method will **not** be invoked."*\
  ② 에서 `NotReturning.__new__` 가 `return` 을 안 썼으므로 `None` 을 돌려준 셈이고,
  `__init__` 로그가 안 찍혔으며 **`NotReturning(3)` 의 결과가 `None`** 이다.
- ★ ③ 처럼 **다른 타입을 돌려줘도 같다.** `Sneaky(3)` 가 **`list`** 를 준다.
  클래스를 불렀는데 리스트가 나오는 것이다.
- ★★ **풀에서 꺼낸 기존 인스턴스를 돌려주면 `__init__` 은 불린다.**
  그것도 **cls 의 인스턴스**이기 때문이다.\
  그래서 싱글턴·풀을 `__new__` 로 만들면 **꺼낼 때마다 다시 초기화**된다 — 조용한 사고다.
- 속성 탐색과 이어지는 지점 — `__init__` 이 하는 일은 결국 **인스턴스 칸을 채우는 것**이므로,
  건너뛰면 **인스턴스 칸이 빈 채**로 객체가 산다.

### 9. 이름은 LEGB, 속성은 인스턴스 → 클래스 → MRO — 다른 탐색이다

**왜 그런가**

- **이름 탐색** — `x` 한 낱말은 **L**(지역) → **E**(둘러싼 함수) → **G**(모듈) → **B**(내장) 순서로 푼다.
  정본은 [21번](../21-scope-legb-global-nonlocal/2-summary.md)이다.
- **속성 탐색** — `obj.x` 는 **`type(obj)` 의 MRO** 를 훑고 **인스턴스 칸**과 견준다.
  정본은 이 주제다.
- ★ **컴파일 시점에 이미 정해져 있는 쪽은 이름 탐색**이다.\
  21번의 핵심 문장이 그것이다 — 블록 안 어디든 대입이 있으면 그 블록 전체에서 그 이름은 지역이다.\
  **속성 탐색은 전부 실행 시점**이다. `obj.x` 가 어느 칸에서 나올지는 그 줄을 실행해 봐야 안다.
- ★ 클래스 몸통에 쓴 `kind` 를 메서드 안에서 **그냥 `kind` 로 읽으면 `NameError`** 다.\
  ★ **클래스 몸통은 이름 사슬에서 빠지기 때문**이다 — 메서드는 둘러싼 클래스의 칸을 **이름으로는** 못 본다.
  `self.kind` 나 `C.kind` 처럼 **속성으로** 물어야 보인다.\
  이 사실 자체의 정본은 21번의 동작 7이므로 여기서는 결론만 적는다.
- **한 줄로 가르면** — 점(`.`)이 있으면 이 주제, 없으면 21번이다.

### 10. 둘 다 「한 번 만들어진 가변 객체를 나눠 쓰는 것」이다

**왜 그런가**

- **공통 성질 한 줄** — `def f(x=[])` 의 리스트도 `class C: items = []` 의 리스트도
  **딱 한 번 만들어져 계속 재사용된다.**\
  앞엣것은 `def` 문이 **실행될 때** 기본값이 만들어져 함수 객체에 붙고,
  뒤엣것은 `class` 몸통이 **실행될 때** 리스트가 만들어져 클래스 칸에 붙는다.
- ★ **처방이 같은 모양인 이유** — 둘 다 **만드는 시점을 뒤로 옮기면** 풀린다.\
  20번은 `None` 센티널로 **호출 시점**에 만들고, 여기는 `__init__` 안에서 **인스턴스마다** 만든다.
  고치는 원리가 하나라서 처방이 닮는다.
- ★ **증상이 간헐적인 이유는 서로 다르다.**\
  20번은 **인자를 넘긴 호출이 멀쩡하므로** 테스트가 늘 인자를 넘기면 영영 안 잡힌다.\
  여기는 **인스턴스가 하나뿐인 동안은 멀쩡하므로** 개발 중에는 안 보이고
  **둘째 인스턴스가 생기는 순간** 드러난다.
- ★ 한 가지가 더 있다 — **조회는 성공하는데 칸은 비어 있다.**
  `vars(obj)` 가 `{}` 라서 「인스턴스에 아무것도 없네」로 읽히고, 그 순간 진단이 어긋난다.
- 정본은 [20번](../20-mutable-default-args/2-summary.md)이므로 여기서는 **링크와 결론**만 남긴다.

### 11. 순서와 우선순위는 언어 보장, 들여다보는 창과 이름은 구현·판이다

**왜 그런가**

| 물음 | 층 | 근거 |
|---|---|---|
| 「인스턴스 칸이 먼저고 없으면 클래스, 없으면 조상」 | **언어 보장** | 3.2.11 Class instances · 3.2.10 Custom classes |
| 「데이터 디스크립터가 인스턴스 칸을 이긴다」 | **언어 보장** | 3.3.2.3 Invoking Descriptors 의 한 문장 |
| 「MRO 는 C3 다」 | **언어 보장** | 3.2.10 — *"uses the C3 method resolution order"* |
| 「`__getattr__` 은 실패했을 때만 불린다」 | **언어 보장** | 3.3.2 — *"is not called"* |
| 「`member_descriptor` 라는 타입 이름」 | ★ **이 판의 관찰** | 내부 타입 이름이다 |
| 「`vars(obj)` 에 값을 넣으면 속성이 된다」 | ★ **CPython 구현** | `vars(obj) is obj.__dict__` 가 참이라서 그렇다 |
| 「MRO 오류 문구가 두 줄이다」 | ★ **이 판의 관찰** | 메시지 안의 개행 위치 |
| 「예외 문구 넷」 | **이 판의 관찰** | 종류는 명세, 문구는 아니다 |

- ★ **가장 헷갈리는 자리** — `__mro__` 로 **보이는 것**은 구현이지만,
  **그 순서로 찾는다는 것**은 언어 보장이다. 둘을 한 덩어리로 읽으면 틀린다.
- ★ 같은 모양이 하나 더 있다 — `__slots__` 가 **데이터 디스크립터를 만든다는 성질**은 보장 쪽이고,
  **그 타입의 이름**은 관찰 쪽이다.
- ★ **그래서 이렇게 적으면 틀린다** — 「`vars()` 로 볼 수 있으니 인스턴스 칸은 `dict` 다」.\
  `dict` 로 구현된 것은 CPython 쪽이고, 보장되는 것은 **거기를 먼저 본다**는 것뿐이다.

### 12. 이름은 21번, 디스크립터 전체는 33번, MRO 전체는 34번이 정본이다

**왜 그런가**

- **이름이 풀리는 규칙의 정본은 [21번](../21-scope-legb-global-nonlocal/2-summary.md)** 이다.
  LEGB·`global`·`nonlocal`·`UnboundLocalError` 가 전부 그쪽이다.\
  여기는 **점이 붙은 것**만 다룬다.
- **`property`·디스크립터·`__slots__` 의 정본은 `[목록의 33번 주제](../33-property-descriptor-slots/)**`** 다.\
  ★ 여기서 그 일부만 다룬 이유는 **탐색 순서를 설명하려면 디스크립터를 안 보고는 안 되기 때문**이다.
  「인스턴스 칸이 지는 경우」가 있다는 사실 자체가 탐색 규칙의 일부다.\
  그쪽에서 다룰 것 — `property` 의 세 갈고리, `__set_name__`, `__slots__` 의 메모리 효과.
- **상속·MRO·`super()` 의 정본은 `[목록의 34번 주제](../34-inheritance-mro-super/)**`** 다.\
  여기서는 **C3 가 계단의 순서를 정하고 `super()` 가 그 위를 걷는다**는 것까지만 봤다.
- **`dataclasses` 는 `[목록의 36번 주제](../36-dataclasses/)**`** 다. 클래스 칸에 메서드를 **자동으로** 넣어 주는 장치라
  이 주제의 그림 위에 바로 올라탄다. 사슬의 [30번](../30-repr-eq-hash-contracts/2-summary.md)에서 먼저 만난다.
- ★★ **이 주제의 「특수 메서드는 클래스 칸에서 찾는다」가 사슬의 다음 셋에서 무엇이 되나.**

| 다음 주제 | 무엇으로 이어지나 |
|---|---|
| [30번](../30-repr-eq-hash-contracts/2-summary.md) | `__eq__`·`__hash__`·`__repr__` 을 **클래스 칸에 놓는 일이 계약**이 된다. `__hash__ = None` 이라는 값도 **클래스 칸에 놓인 것**이다 |
| [31번](../31-comparison-protocol-and-sortability/2-summary.md) | `__lt__` 하나가 클래스 칸에 있으면 `sorted` 가 돈다. `total_ordering` 은 **클래스 칸을 채우는 데코레이터**다 |
| [32번](../32-container-protocol/2-summary.md) | `__len__`·`__getitem__`·`__contains__`·`__iter__` 가 **클래스 칸에 있나 없나**로 대체 경로가 갈린다 |

- ★ 거꾸로 읽으면 이렇다 — **29번이 「어디를 보나」이고, 30\~32번은 「거기서 무엇을 찾나」다.**

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 인스턴스 칸과 클래스 칸의 분리 | `e29_lookup.py` 를 `python3 - <파일` 로 | 2회(캡처 + 재대조) | 한 글자도 같았다 |
| 클래스 변수 공유 세 갈래 | `e29_classvar.py` | 2회 | 한 글자도 같았다 |
| 두 갈고리의 호출 조건 | `e29_getattr.py` | 2회 | 한 글자도 같았다 |
| 디스크립터 우선순위 네 층 | `e29_descriptor.py` | 2회 | 한 글자도 같았다 |
| C3 와 다이아몬드 · 실패 문구 | `e29_mro.py` | 2회 | 한 글자도 같았다 |
| `super()` 의 다음 | `e29_super.py` | 2회 | 한 글자도 같았다 |
| `__slots__` 가 없애는 것과 만드는 것 | `e29_slots.py` | 2회 | 한 글자도 같았다 |
| `__new__` 와 `__init__` 의 갈림길 | `e29_new_init.py` | 2회 | 한 글자도 같았다 |
| 판 확인 | `e29_version.py` | 2회 | 3.12.3 · cpython · linux |

**구현 의존 항목** — 판이 오르면 **다시 던져 봐야 하는 것들**이다.

| 항목 | 왜 |
|---|---|
| `member_descriptor` 라는 타입 이름 | 내부 타입 이름이다. **성질**(데이터 디스크립터)은 안 흔들린다 |
| `vars() argument must have __dict__ attribute` | 문구다 |
| `'WithSlots' object has no attribute 'extra'` | 문구다 |
| MRO 실패 메시지의 **줄바꿈 위치** | 메시지 안의 개행이다 |
| `vars(obj) is obj.__dict__` 가 참인 것 | CPython 의 구현이다 |

**안 돌려 본 것** — 3.10·3.11·3.13 에서 같은지는 **확인하지 않았다.** 이 머신에 3.12.3 한 판뿐이다.\
★ 「여러 판에서 같았다」고 적을 근거가 없으므로 **이 판의 관찰로만** 적었다.
