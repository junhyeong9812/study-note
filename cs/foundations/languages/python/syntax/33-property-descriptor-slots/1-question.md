# python/syntax/33-property-descriptor-slots — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> ★★ 이 주제에서는 **「어느 갈고리가 불렸나」와 「무엇이 로그를 안 남겼나」가 답인 자리가 많다.**
> 결과값만 맞히고 **호출 로그를 못 맞히면 틀린 것**으로 친다.
> ★★★ 그리고 **수치를 묻는 문항이 하나도 없다** — 이 주제는 **「어느 쪽이 작나」만 근거로 쓴다.**
> 「몇 바이트인가」로 답을 적었으면 그것부터 틀린 것이다.
>
> 실행 환경: `python3` **3.12.3** · Linux. 던지는 형태는 `python3 - <파일` 로 고정했다.
> ★ **이 주제는 [29번](../29-classes-and-attribute-lookup/1-question.md)을 전부 쓴다** — 우선순위 네 층이 거기 정본이다.
> 막히면 그것이 안 잡힌 것인지부터 짚어라.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. 세 장치를 한 클래스에 얹고 읽고 쓰면 (예측)

```python
# e33_three.py
import inspect


class Logged:                       # ② 손으로 만든 디스크립터
    def __set_name__(self, owner, name):
        self.public = name          # ★ 이름을 자동으로 받는다
        self.private = "_" + name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        print("      [디스크립터] __get__ 이 답한다 :", self.public)
        return getattr(obj, self.private)

    def __set__(self, obj, value):
        print("      [디스크립터] __set__ 이 가로챈다 :", self.public, "<-", repr(value))
        setattr(obj, self.private, value)


class Sensor:
    __slots__ = ("raw", "_tag")     # ③ __slots__ — member_descriptor 두 개가 생긴다

    tag = Logged()

    @property                       # ① property
    def celsius(self):
        print("      [property] fget 이 답한다")
        return self.raw / 10

    @celsius.setter
    def celsius(self, v):
        print("      [property] fset 이 받는다")
        self.raw = round(v * 10)

    def __init__(self, raw, tag):
        self.raw = raw              # member_descriptor 가 받는다 — 조용하다
        self.tag = tag


print("① 세 장치가 한 클래스 칸에 나란히 있다")
s = Sensor(235, "실외")
for nm in ("celsius", "tag", "raw", "_tag"):
    print("   %-8s -> %s" % (nm, type(Sensor.__dict__[nm]).__name__))

print("② 누가 답하나 — 읽기")
print("   s.celsius ->", s.celsius)
print("   s.tag     ->", s.tag)
print("   s.raw     ->", s.raw, "  <- member_descriptor 는 로그를 안 남긴다")

print("③ 누가 답하나 — 쓰기")
s.celsius = 21.0
s.tag = "실내"
print("   다시 읽으면 :", end=" ")
print(s.raw, "|", getattr(s, "_tag"))

print("④ 셋 다 데이터 디스크립터인가 — 29번의 판별식을 그대로 건다")
for nm in ("celsius", "tag", "raw"):
    t = type(Sensor.__dict__[nm])
    print("   %-8s __get__:%-5s __set__:%-5s __delete__:%s"
          % (nm, hasattr(t, "__get__"), hasattr(t, "__set__"), hasattr(t, "__delete__")))

print("⑤ ★ getattr_static 은 디스크립터를 「부르지 않고」 거기 앉은 것을 본다")
for nm in ("celsius", "tag", "raw"):
    got = inspect.getattr_static(s, nm)
    print("   getattr_static(s, %-9s) -> %s" % (repr(nm), type(got).__name__))
print("   ★ 위 세 줄에 [property]·[디스크립터] 로그가 한 줄도 없다")

print("⑥ 인스턴스 칸은 아예 없다")
print("   hasattr(s, '__dict__') :", hasattr(s, "__dict__"))
try:
    vars(s)
except TypeError as ex:
    print("   vars(s) -> TypeError:", ex)
```

* 읽기 세 줄(`s.celsius`·`s.tag`·`s.raw`) 중 **로그가 안 찍히는 줄**은 어느 것이고 **왜**인가?
* ④에서 셋의 `__get__`/`__set__`/`__delete__` 표는 **어떻게** 나오는가?
* ★ ⑤에서 `getattr_static` 을 세 번 부르면 로그가 **몇 줄** 찍히는가?

### 2. `@x.setter` 를 붙이기 전의 객체를 붙잡아 두면 (예측)

```python
# e33_property.py
class Temp:
    def __init__(self, c):
        self._c = c

    @property
    def celsius(self):
        return self._c

    only_getter = celsius          # ★ setter 를 붙이기 전의 그 객체를 따로 붙잡아 둔다

    @celsius.setter
    def celsius(self, v):
        if v < -273.15:
            raise ValueError("절대영도 아래는 못 넣는다: %r" % v)
        self._c = v

    @celsius.deleter
    def celsius(self):
        print("      fdel 이 불렸다")
        self._c = None


print("① property 의 세 칸 — fget·fset·fdel")
for nm in ("only_getter", "celsius"):
    p = Temp.__dict__[nm]
    print("   %-11s fget:%-8s fset:%-8s fdel:%s"
          % (nm,
             p.fget.__name__ if p.fget else None,
             p.fset.__name__ if p.fset else None,
             p.fdel.__name__ if p.fdel else None))

print("② ★ @celsius.setter 는 그 자리를 고치는 게 아니라 새 property 를 만든다")
print("   only_getter is celsius :", Temp.__dict__["only_getter"] is Temp.__dict__["celsius"])
print("   둘 다 property 인가     :",
      type(Temp.__dict__["only_getter"]).__name__, type(Temp.__dict__["celsius"]).__name__)
print("   두 fget 이 같은 함수인가 :",
      Temp.__dict__["only_getter"].fget is Temp.__dict__["celsius"].fget)
print("   only_getter 에 fset 이 있나 :", Temp.__dict__["only_getter"].fset is not None)

print("③ 그래서 only_getter 쪽으로 대입하면 막힌다")
t = Temp(20.0)
print("   t.only_getter ->", t.only_getter)
try:
    t.only_getter = 30.0
except AttributeError as ex:
    print("   t.only_getter = 30.0 -> AttributeError:", ex)

print("④ celsius 쪽은 대입이 되고 검증도 돈다")
t.celsius = 30.0
print("   t.celsius ->", t.celsius)
try:
    t.celsius = -300.0
except ValueError as ex:
    print("   t.celsius = -300.0 -> ValueError:", ex)

print("⑤ del 은 fdel 로 간다")
del t.celsius
print("   t.celsius ->", t.celsius)

print("⑥ ★ property 는 클래스 칸에 놓여야 먹는다 — 인스턴스에 붙이면 그냥 객체다")


class Plain:
    pass


p = Plain()
p.x = property(lambda self: "인스턴스에 붙인 것")
print("   type(p.x)        :", type(p.x).__name__)
print("   p.x 가 문자열인가 :", isinstance(p.x, str))
print("   p.x.fget 을 손으로 부르면 :", p.x.fget(p))
Plain.y = property(lambda self: "클래스 칸에 놓으니 불린다")
print("   클래스 칸에 놓은 뒤 p.y  :", p.y)
print("   type(p.y)        :", type(p.y).__name__)
```

* ②의 `only_getter is celsius` 는 참인가 거짓인가?
* ★ 두 `property` 의 `fget` 은 **같은 함수인가 다른 함수인가**?
* ⑥에서 `type(p.x)` 와 `type(p.y)` 는 각각 무엇인가?

### 3. 클래스에 `__set__` 을 나중에 붙이면 (예측)

```python
# e33_flip.py
class Answers:
    def __get__(self, obj, objtype=None):
        return "디스크립터가 답한다"


class Holder:
    x = Answers()


h = Holder()
h.__dict__["x"] = "인스턴스 칸의 값"

print("① 지금은 비데이터 디스크립터다 — 29번의 결론대로 인스턴스 칸이 이긴다")
print("   Answers 에 __set__ 이 있나 :", hasattr(Answers, "__set__"))
print("   vars(h)['x']              ->", vars(h)["x"])
print("   h.x                       ->", h.x)

print("② ★ 역방향 실험 — 클래스에 __set__ 을 나중에 붙여 데이터 디스크립터로 바꾼다")
Answers.__set__ = lambda self, obj, value: obj.__dict__.__setitem__("x", value)
print("   Answers 에 __set__ 이 있나 :", hasattr(Answers, "__set__"))
print("   vars(h)['x']              ->", vars(h)["x"], "  <- 인스턴스 칸은 한 글자도 안 건드렸다")
print("   h.x                       ->", h.x, "  <- 우선순위가 뒤집혔다")

print("③ 떼면 그대로 돌아온다")
del Answers.__set__
print("   Answers 에 __set__ 이 있나 :", hasattr(Answers, "__set__"))
print("   h.x                       ->", h.x)

print("④ ★ __delete__ 만 붙여도 데이터 디스크립터가 된다")
Answers.__delete__ = lambda self, obj: None
print("   __set__:%s __delete__:%s" % (hasattr(Answers, "__set__"), hasattr(Answers, "__delete__")))
print("   h.x                       ->", h.x)
print("   그런데 대입은 못 한다 :", end=" ")
try:
    h.x = "새 값"
except AttributeError as ex:
    print("AttributeError:", ex)

print("⑤ 바뀐 것은 인스턴스가 아니라 「디스크립터의 타입」이다")
print("   type(Holder.__dict__['x']).__name__ :", type(Holder.__dict__["x"]).__name__)
print("   vars(h) :", vars(h))
```

* ②에서 `vars(h)['x']` 와 `h.x` 는 각각 무엇을 답하는가?
* ★ ④에서 `__delete__` 만 붙이면 읽기와 쓰기가 **각각** 어떻게 되는가?
* ⑤에서 `type(Holder.__dict__['x']).__name__` 은 무엇으로 나오는가?

### 4. 디스크립터의 네 갈고리를 전수로 건드리면 (예측)

```python
# e33_descriptor.py
class Traced:
    def __set_name__(self, owner, name):
        print("      __set_name__ : owner =", owner.__name__, "| name =", name)
        self.name = name

    def __get__(self, obj, objtype=None):
        if obj is None:
            print("      __get__   : 클래스에서 꺼냈다 (obj 가 None)")
            return self
        print("      __get__   : 인스턴스에서 꺼냈다")
        return obj.__dict__.get(self.name, "(아직 없음)")

    def __set__(self, obj, value):
        print("      __set__   :", repr(value))
        obj.__dict__[self.name] = value

    def __delete__(self, obj):
        print("      __delete__ 가 불렸다")
        obj.__dict__.pop(self.name, None)


print("① class 문이 끝나기 전에 __set_name__ 이 먼저 불린다")


class Box:
    a = Traced()
    b = Traced()


print("② 그 덕에 이름을 손으로 안 넘겨도 된다")
print("   Box.__dict__['a'].name :", Box.__dict__["a"].name)
print("   Box.__dict__['b'].name :", Box.__dict__["b"].name)

bx = Box()
print("③ 읽기·쓰기·지우기가 각각 다른 갈고리로 간다")
print("   bx.a ->", bx.a)
bx.a = 7
print("   vars(bx) :", vars(bx))
print("   bx.a ->", bx.a)
del bx.a
print("   vars(bx) :", vars(bx))

print("④ 클래스에서 꺼내면 obj 자리에 None 이 들어온다")
print("   type(Box.a).__name__ :", type(Box.a).__name__)

print("⑤ ★ 디스크립터 하나가 인스턴스 여럿을 상대한다 — 상태를 자기 안에 두면 새어 나간다")
p, q = Box(), Box()
p.b = "p 의 값"
q.b = "q 의 값"
print("   p.b ->", p.b)
print("   q.b ->", q.b)
print("   vars(p) :", vars(p))
print("   vars(q) :", vars(q))
print("   ★ 값은 인스턴스 칸에 넣었기 때문에 안 섞인다. 디스크립터 자신에게 넣으면 섞인다")

print("⑥ ★ __set_name__ 은 class 문이 만들 때만 불린다 — 나중에 붙이면 안 불린다")
late = Traced()
Box.c = late
print("   Box.c 를 붙인 뒤 late 에 name 이 있나 :", hasattr(late, "name"))
try:
    Box().c
except AttributeError as ex:
    print("   그래서 Box().c 를 읽으면 -> AttributeError:", ex)
```

* ①의 `__set_name__` 로그는 **몇 줄**이고, `class Box:` 문이 **끝나기 전인가 후인가**?
* ★ ④에서 `Box.a` 를 읽으면 `__get__` 의 `obj` 자리에 무엇이 오는가?
* ★ ⑥에서 `Box.c = late` 로 나중에 붙이면 **무엇이 안 일어나고** 그 결과 무엇이 터지는가?

### 5. `__slots__` 의 경계 여섯을 던지면 (예측)

```python
# e33_slots_edge.py
print("① __slots__ 에 적은 이름을 클래스 변수로도 쓰면")
try:
    class Conflict:
        __slots__ = ("x",)
        x = 1
except ValueError as ex:
    print("   ValueError:", ex)

print("② 둘 다 비지 않은 __slots__ 를 다중 상속하면")


class L1:
    __slots__ = ("a",)


class R1:
    __slots__ = ("b",)


try:
    class Both1(L1, R1):
        __slots__ = ()
except TypeError as ex:
    print("   TypeError:", ex)

print("③ 한쪽이 비어 있으면 된다")


class R2:
    __slots__ = ()


class Both2(L1, R2):
    __slots__ = ("c",)


o = Both2()
o.a, o.c = 1, 3
print("   Both2 인스턴스에 __dict__ 가 있나 :", hasattr(o, "__dict__"))
print("   o.a, o.c ->", o.a, o.c)

print("④ ★ __slots__ 에 '__dict__' 를 넣으면 사물함이 되살아난다")


class Hybrid:
    __slots__ = ("fixed", "__dict__")


h = Hybrid()
h.fixed = 1
h.anything = 2
print("   vars(h) :", vars(h), "  <- fixed 는 여기 없다")
print("   h.fixed ->", h.fixed, "| h.anything ->", h.anything)
print("   클래스 칸의 fixed 의 정체 :", type(Hybrid.__dict__["fixed"]).__name__)

print("⑤ 문자열 하나를 주면 글자 단위가 아니라 이름 하나다")


class OneName:
    __slots__ = "only"


n = OneName()
n.only = 5
print("   OneName.__slots__  :", repr(OneName.__slots__))
print("   클래스 칸의 이름들 :", sorted(k for k in OneName.__dict__ if not k.startswith("__")))

print("⑥ 선언한 이름이라도 넣기 전에 읽으면 없다")


class Lazy:
    __slots__ = ("v",)


z = Lazy()
try:
    z.v
except AttributeError as ex:
    print("   AttributeError:", ex)
z.v = 1
del z.v
try:
    z.v
except AttributeError as ex:
    print("   넣었다 지운 뒤에도 -> AttributeError:", ex)
```

* ①과 ②는 **각각 어느 시점에** 터지는가 — 클래스를 정의할 때인가 인스턴스를 만들 때인가?
* ★ ④에서 `vars(h)` 에는 무엇이 들어 있고 **무엇이 없는가**?
* ⑤에서 `__slots__ = "only"` 는 칸을 **몇 개** 만드는가?

### 6. 한 이름에 세 답이 나오는 자리 (예측)

```python
# e33_static_window.py
import inspect


class Normal:
    shared = "클래스 칸의 값"

    def __init__(self):
        self.own = "인스턴스 칸의 값"

    @property
    def computed(self):
        return "property 가 계산한 값"

    def method(self):
        return "메서드"


n = Normal()
n.__dict__["computed"] = "인스턴스 칸에 몰래 넣은 값"

print("① 보통 클래스에서 두 창을 견준다")
rows = ("shared", "own", "computed", "method")
for nm in rows:
    live = getattr(n, nm)
    stat = inspect.getattr_static(n, nm)
    print("   %-9s getattr -> %-28s getattr_static 의 타입 -> %s"
          % (nm, live if not callable(live) else "(메서드 객체)", type(stat).__name__))

print("② ★ computed 한 줄이 이 창의 값어치다")
print("   vars(n)['computed']          :", vars(n)["computed"])
print("   n.computed                   :", n.computed)
print("   getattr_static 이 본 것의 타입 :", type(inspect.getattr_static(n, "computed")).__name__)
print("   ★ 세 답이 전부 다르다 — 「칸에 있는 것」·「답한 것」·「거기 앉은 것」이 셋 다 다르다")

print("③ 갈고리가 있는 객체에서는 차이가 더 벌어진다")


class Ghost:
    def __getattr__(self, name):
        return "<%s 를 즉석에서 만들었다>" % name


g = Ghost()
print("   g.zzz                :", g.zzz)
print("   hasattr(g, 'zzz')    :", hasattr(g, "zzz"))
try:
    inspect.getattr_static(g, "zzz")
except AttributeError as ex:
    print("   getattr_static(g,'zzz') -> AttributeError:", ex)
print("   ★ 29번이 「제5의 상태」라 부른 자리를 이 창은 없다고 답한다")
```

* ②에서 `vars(n)['computed']`·`n.computed`·`getattr_static(n,'computed')` 이 각각 무엇을 답하는가?
* ★ ③에서 `hasattr(g,'zzz')` 와 `getattr_static(g,'zzz')` 의 답이 **왜 갈리는가**?

### 7. `property` 가 클래스 칸에 놓여야 먹는 이유 (왜)

* 인스턴스에 붙인 `property` 는 **왜** 안 먹는가 — [29번](../29-classes-and-attribute-lookup/2-summary.md)의 어느 규칙 때문인가?
* ★ `p.x.fget(p)` 로 손으로 부르면 값이 나오는 것은 무엇을 말해 주는가?

### 8. 데이터 디스크립터의 판별식 (경계)

* 무엇이 있으면 데이터 디스크립터인가 — **몇 가지**를 대야 답이 완성되는가?
* ★ 하나만 있고 다른 하나가 없으면 어떤 어중간한 상태가 되는가?
* ★ 그 판별은 **객체에서 하는가 타입에서 하는가**?

### 9. 디스크립터가 값을 어디에 두어야 하나 (왜)

* 디스크립터 자신에게(`self.value = v`) 값을 두면 무엇이 잘못되는가?
* ★ 그것이 [20번](../20-mutable-default-args/2-summary.md)·[29번](../29-classes-and-attribute-lookup/2-summary.md)의 어느 사고와 **같은 집안**인가?

### 10. `__slots__` 가 아끼는 것을 어떻게 재야 하나 (경계)

* `getsizeof` 로 두 인스턴스를 바로 견주면 **왜 차이가 안 보이는가**?
* ★★ 잰 결과 중 **근거로 써도 되는 것**은 무엇이고 **쓰면 안 되는 것**은 무엇인가?
* ★★★ 이 주제가 **한 번도 안 잰 것**은 무엇인가?

### 11. 세 층 가르기 (경계)

* 「데이터 디스크립터가 인스턴스 칸을 이긴다」는 **언어 보장인가 CPython 구현인가**?
* ★ 「`__slots__` 가 메모리를 아낀다」는 어느 층인가?
* `member_descriptor` 라는 **이름**과 그것이 **데이터 디스크립터라는 성질**은 같은 층인가?

### 12. 이웃 주제와의 경계 (연결)

* [29번](../29-classes-and-attribute-lookup/2-summary.md)이 정본인 것과 이 주제가 정본인 것을 한 줄씩으로 가르면?
* ★ `functools.cached_property` 가 **두 번째 접근에 안 계산되는** 이유를 이 주제의 네 층으로 설명하면?
* ★ [36번](../36-dataclasses/1-question.md) 의 `@dataclass(slots=True)` 는 이 주제의 무엇을 대신해 주는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|---|---|---|---|
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |
