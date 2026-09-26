# python/syntax/36-dataclasses — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> ★★★ 이 주제의 1번은 **생성된 `__init__` 의 서명을 글자 그대로 적어야** 한다.
> 「대충 이런 인자를 받는다」로는 맞은 것이 아니다.
> ★★ 그리고 **「조용히 통과한다」가 정답인 문항이 셋**이다(2번·5번·6번).
> 「막힐 것 같다」를 「막힌다」로 적으면 틀린다.
>
> 실행 환경: `python3` **3.12.3** · Linux. 던지는 형태는 `python3 - <파일` 로 고정했다.
> ★★★ **이 주제는 앞 주제 다섯을 전부 쓴다** —
> [20](../20-mutable-default-args/1-question.md)(가변 기본값) · [30](../30-repr-eq-hash-contracts/1-question.md)(`__hash__`) ·
> [31](../31-comparison-protocol-and-sortability/1-question.md)(순서) · [33](../33-property-descriptor-slots/1-question.md)(`__slots__`) ·
> [34](../34-inheritance-mro-super/1-question.md)(MRO). 막히면 그중 무엇이 안 잡힌 것인지부터 짚어라.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 무엇이 생기고 서명은 어떻게 되나 (예측)

```python
# e36_generated.py
import dataclasses
import inspect
from dataclasses import dataclass, field


class Plain:
    pass


@dataclass
class Point:
    x: int
    y: int = 0
    tags: list = field(default_factory=list)


print("① 클래스 칸에 무엇이 새로 생겼나")
made = sorted(set(Point.__dict__) - set(Plain.__dict__))
print("   ", made)

print("② 생성된 __init__ 의 서명 — 손으로 안 셌다")
print("   ", inspect.signature(Point.__init__))
print("   Point 를 부르는 쪽 서명 :", inspect.signature(Point))

print("③ __dataclass_fields__ 덤프 — 선언 순서가 그대로다")
def show(v):                       # MISSING 은 repr 에 주소가 박히므로 이름으로 바꾼다
    if v is dataclasses.MISSING:
        return "MISSING"
    return getattr(v, "__name__", repr(v))


for name, f in Point.__dataclass_fields__.items():
    print("   %-6s type=%-12s default=%-8s factory=%-8s init=%-5s repr=%-5s compare=%s"
          % (name, f.type.__name__, show(f.default), show(f.default_factory),
             f.init, f.repr, f.compare))
print("   ★ 이 순서는 dict 라서 보장된다 — 삽입 순서 보장은 12번이 정본이다")

print("④ fields() 로 옵션을 전수로 본다")
print("   [f.name for f in fields(Point)] :", [f.name for f in dataclasses.fields(Point)])
print("   MISSING 이 「기본값 없음」의 표식이다 :",
      dataclasses.fields(Point)[0].default is dataclasses.MISSING)

print("⑤ 만들어진 것이 실제로 도나")
p = Point(1, 2)
print("   repr(p)        :", repr(p))
print("   p == Point(1,2):", p == Point(1, 2))
print("   p == (1, 2)    :", p == (1, 2), " <- 다른 타입이면 NotImplemented 라 거짓이다")
print("   __hash__       :", Point.__hash__, " <- 30번이 정본이다")

print("⑥ 상속하면 부모 필드가 앞에 온다")


@dataclass
class Point3(Point):
    z: int = 0


print("   Point3 의 필드 :", [f.name for f in dataclasses.fields(Point3)])
print("   Point3.__init__ :", inspect.signature(Point3.__init__))
print("   ★ MRO 를 거꾸로 훑어 모은다 — 정본은 [목록의 **34번 주제**](../34-inheritance-mro-super/)다")

print("⑦ asdict / astuple 은 재귀한다")
print("   asdict(Point3(1,2,[9],3))  :", dataclasses.asdict(Point3(1, 2, [9], 3)))
print("   astuple(Point3(1,2,[9],3)) :", dataclasses.astuple(Point3(1, 2, [9], 3)))
print("   replace(p, y=99)           :", dataclasses.replace(p, y=99))
```

* ①에서 새로 생긴 이름은 **몇 개**이고, 던더가 아닌 것이 **하나 섞여 있는데** 무엇이고 왜인가?
* ★★ ②의 `__init__` 서명을 **글자 그대로** 적어라 — 세 번째 인자의 기본값 자리에 무엇이 찍히는가?
* ★ ⑤에서 `p == (1, 2)` 는 참인가 거짓인가, 그리고 `Point.__hash__` 는 무엇인가?
* ★ ⑥에서 `Point3` 의 필드 순서는 어떻게 되는가?

### 2. ★★ 가변 기본값을 세 타입에 던지면 (예측)

```python
# e36_mutable.py
from dataclasses import dataclass, field, fields


print("① 가변 기본값을 그냥 쓰면 — class 문에서 거부당한다")
for typ in (list, dict, set):
    try:
        @dataclass
        class Bad:
            xs: typ = typ()
    except ValueError as ex:
        print("   %-5s -> %s | %s" % (typ.__name__, type(ex).__name__, ex))

print("② default_factory 로 고친다")


@dataclass
class Good:
    xs: list = field(default_factory=list)


a, b = Good(), Good()
a.xs.append(1)
print("   a.xs :", a.xs, "| b.xs :", b.xs)
print("   a.xs is b.xs :", a.xs is b.xs)
print("   ★ 20번의 None 센티널과 같은 처방이다 — 만드는 시점을 호출 때로 옮긴 것")

print("③ 팩토리는 인스턴스마다 불린다")
CALLS = []


def make():
    CALLS.append(len(CALLS))
    return []


@dataclass
class Counted:
    xs: list = field(default_factory=make)


Counted(); Counted(); Counted()
print("   세 번 만든 뒤 팩토리 호출 횟수 :", len(CALLS))

print("④ 인자를 넘기면 팩토리는 안 불린다")
CALLS.clear()
Counted([1, 2])
print("   인자를 준 한 번의 호출 횟수 :", len(CALLS))

print("⑤ ★ 이 방어는 부분적이다 — 20번이 적은 그대로다")


class MyMutable:
    def __init__(self):
        self.items = []


@dataclass
class Sneaky:
    m: MyMutable = MyMutable()      # 가변인데 해시가 되므로 통과한다


s1, s2 = Sneaky(), Sneaky()
s1.m.items.append("샜다")
print("   MyMutable 이 해시되나 :", hash(MyMutable()) is not None)
print("   s1.m is s2.m          :", s1.m is s2.m)
print("   s2.m.items            :", s2.m.items)
print("   ★ 문서가 스스로 partial solution 이라 적는다 — 판별 기준이 해시 가능성이다")

print("⑥ default 와 default_factory 를 같이 주면")
try:
    @dataclass
    class Both:
        xs: list = field(default=None, default_factory=list)
except ValueError as ex:
    print("   ValueError:", ex)

print("⑦ 튜플처럼 불변이면 그냥 통과한다")


@dataclass
class Frozen:
    xs: tuple = ()


print("   Frozen().xs is Frozen().xs :", Frozen().xs is Frozen().xs)
print("   fields(Frozen)[0].default  :", repr(fields(Frozen)[0].default))
```

* ①의 세 줄은 각각 어떤 예외이고 **어느 시점**에 나는가?
* ★ ③과 ④의 두 수치는 각각 무엇인가?
* ★★★ ⑤에서 `MyMutable` 은 **막히는가 통과하는가** — 그리고 `s2.m.items` 는 무엇인가?

### 3. 세 스위치를 전수로 돌리면 (예측)

```python
# e36_grid.py
import itertools
from dataclasses import dataclass, field, fields


print("① init·repr·compare 세 스위치를 전수로 돌린다")
print("   b 필드의 옵션        | __init__ 서명            | repr                  | a만 다를 때 ==")
print("   " + "-" * 92)
import inspect

for init, rep, cmp in itertools.product([True, False], repeat=3):
    @dataclass
    class G:
        a: int = 1
        b: int = field(default=2, init=init, repr=rep, compare=cmp)

    sig = str(inspect.signature(G.__init__)).replace("self, ", "")
    g1, g2 = G(), G()
    g2.b = 99
    opt = "init=%-5s repr=%-5s compare=%-5s" % (init, rep, cmp)
    print("   %s | %-24s | %-21s | %s" % (opt, sig, repr(g1), g1 == g2))

print()
print("② 읽는 법 세 줄")
print("   init=False  -> 서명에서 b 가 빠진다. 기본값이 없으면 아예 안 채워진다")
print("   repr=False  -> repr 에서 b 가 빠진다")
print("   compare=False -> b 가 달라도 == 가 참이다  <- 가장 조용한 스위치다")

print()
print("③ init=False 이고 기본값도 없으면 — 속성 자체가 안 생긴다")


@dataclass
class NoInit:
    a: int
    b: int = field(init=False)


n = NoInit(1)
print("   NoInit(1) 이 만들어졌나 :", type(n).__name__)
print("   vars(n)                :", vars(n))
try:
    n.b
except AttributeError as ex:
    print("   n.b -> AttributeError:", ex)
print("   repr(n) 을 부르면      :", end=" ")
try:
    print(repr(n))
except AttributeError as ex:
    print("AttributeError:", ex)

print()
print("④ field() 에는 스위치가 더 있다")
print("   Field 의 칸들 :", [s for s in fields(NoInit)[1].__slots__])
```

* ①의 여덟 줄 중 **`==` 가 참이 되는 것은 몇 줄**이고 어느 스위치 때문인가?
* ★★ ③에서 `n.b` 와 `repr(n)` 은 각각 어떻게 되는가?

### 4. `order=True` 가 만드는 것 (예측)

```python
# e36_order.py
import inspect
from dataclasses import dataclass


class Plain:
    pass


@dataclass(order=True)
class Ver:
    major: int
    minor: int
    tag: str = ""


print("① order=True 가 만드는 넷")
made = sorted(n for n in set(Ver.__dict__) - set(Plain.__dict__) if n.startswith("__"))
print("   클래스 칸에 생긴 것 :", made)
for n in ("__lt__", "__le__", "__gt__", "__ge__"):
    print("   %-8s 이 칸에 있나 : %s" % (n, n in Ver.__dict__))
print("   ★ 31번의 total_ordering 은 셋만 채운다 — 이쪽은 __lt__ 부터 넷을 다 만든다")

print("② 비교는 필드 선언 순서대로 튜플을 만들어 견준다")
rows = [Ver(1, 2), Ver(1, 10), Ver(2, 0), Ver(1, 2, "a")]
print("   sorted ->", sorted(rows))
print("   Ver(1,2) < Ver(1,10) :", Ver(1, 2) < Ver(1, 10))
print("   Ver(1,2) < Ver(1,2,'a') :", Ver(1, 2) < Ver(1, 2, "a"))
print("   max(rows) ->", max(rows), " <- 31번이 말한 대로 __gt__ 가 불린다")

print("③ 타입이 다르면 TypeError 다")
try:
    Ver(1, 2) < 1
except TypeError as ex:
    print("   Ver(1,2) < 1 -> TypeError:", ex)


@dataclass(order=True)
class Other:
    major: int
    minor: int
    tag: str = ""


try:
    Ver(1, 2) < Other(1, 2)
except TypeError as ex:
    print("   Ver < Other  -> TypeError:", ex, " <- 모양이 같아도 막는다")

print("④ ★ 생성된 __lt__ 가 무엇을 보는지 소스로 확인한다")
print("   Ver.__lt__ 의 서명 :", inspect.signature(Ver.__lt__))
print("   Ver.__lt__ 의 코드 상수 :", Ver.__lt__.__code__.co_names)
print("   ★ self 쪽 튜플과 other 쪽 튜플을 만들어 견준다")

print("⑤ compare=False 인 필드는 그 튜플에서 빠진다")
from dataclasses import field


@dataclass(order=True)
class Skip:
    major: int
    memo: str = field(default="", compare=False)


print("   Skip(1,'a') == Skip(1,'b') :", Skip(1, "a") == Skip(1, "b"))
print("   Skip(1,'z') <  Skip(2,'a') :", Skip(1, "z") < Skip(2, "a"))

print("⑥ eq=False 와 order=True 를 같이 주면")
try:
    @dataclass(eq=False, order=True)
    class Nope:
        x: int
except ValueError as ex:
    print("   ValueError:", ex)
```

* ①에서 **어느 넷**이 클래스 칸에 생기는가?
* ★★ ③에서 필드 이름·순서·타입이 **똑같은** `Other` 와 비교하면 어떻게 되는가 — **왜**인가?
* ★ ④의 `co_names` 에 무엇이 들어 있는가?

### 5. `frozen=True` 가 막는 것과 안 막는 것 (경계)

```python
# e36_frozen.py
import dataclasses
from dataclasses import dataclass, field


class Plain:
    pass


@dataclass
class Open:
    x: int = 1
    xs: tuple = ()


@dataclass(frozen=True)
class Locked:
    x: int = 1
    xs: tuple = ()


print("① frozen=True 가 클래스 칸에 무엇을 더 넣나")
open_names = set(Open.__dict__) - set(Plain.__dict__)
lock_names = set(Locked.__dict__) - set(Plain.__dict__)
print("   frozen 쪽에만 있는 것 :", sorted(lock_names - open_names))
print("   __setattr__ 이 칸에 있나 — Open :", "__setattr__" in Open.__dict__,
      "| Locked :", "__setattr__" in Locked.__dict__)
print("   Locked.__setattr__ 의 정체 :", Locked.__setattr__.__qualname__)
print("   ★ 별도 장치가 아니라 __setattr__ 을 갈아끼운 것이다")

print("② 그래서 대입이 막힌다")
lk = Locked(1)
try:
    lk.x = 2
except dataclasses.FrozenInstanceError as ex:
    print("   lk.x = 2 ->", type(ex).__name__ + ":", ex)
try:
    del lk.x
except dataclasses.FrozenInstanceError as ex:
    print("   del lk.x ->", type(ex).__name__ + ":", ex)
try:
    lk.newone = 1
except dataclasses.FrozenInstanceError as ex:
    print("   lk.newone = 1 ->", type(ex).__name__ + ":", ex)
print("   ★ 선언 안 한 이름에도 막힌다 — __setattr__ 은 이름을 안 가린다")

print("③ FrozenInstanceError 는 AttributeError 의 하위다")
print("   issubclass(FrozenInstanceError, AttributeError) :",
      issubclass(dataclasses.FrozenInstanceError, AttributeError))

print("④ ★ 얕다 — 담긴 가변 객체는 안 막는다")


@dataclass(frozen=True)
class Shallow:
    xs: list = field(default_factory=list)


s = Shallow()
s.xs.append("들어갔다")
print("   s.xs :", s.xs, " <- frozen 인데 내용이 바뀌었다")
print("   막는 것은 「이름을 다시 묶는 것」뿐이다")

print("⑤ 해시는 되살아난다 — 30번이 정본이다")
print("   Open.__hash__   :", Open.__hash__)
print("   Locked.__hash__ :", "만들어져 있다" if Locked.__hash__ else Locked.__hash__)
print("   {Locked(1): 0, Locked(1): 1} 의 키 개수 :", len({Locked(1): 0, Locked(1): 1}))

print("⑥ __post_init__ 에서 값을 넣으려면 우회해야 한다")


@dataclass(frozen=True)
class Derived:
    raw: str
    upper: str = field(init=False)

    def __post_init__(self):
        object.__setattr__(self, "upper", self.raw.upper())


print("   Derived('ab') ->", Derived("ab"))
print("   ★ object.__setattr__ 로 갈아끼운 것을 건너뛴다")
```

* ①에서 `frozen` 쪽에만 생긴 던더 **둘**은 무엇인가?
* ★ ②에서 **선언 안 한 이름** `lk.newone = 1` 은 막히는가?
* ★★★ ④에서 `s.xs.append('들어갔다')` 는 막히는가 — **왜**인가?

### 6. `InitVar` 를 세 창으로 보면 (예측)

```python
# e36_postinit.py
import inspect
from dataclasses import dataclass, field, fields, InitVar


@dataclass
class User:
    name: str
    db_key: InitVar[str]                    # ★ 필드가 아니다
    salt: InitVar[int] = 0
    token: str = field(init=False, default="")

    def __post_init__(self, db_key, salt):
        print("      __post_init__ 이 받은 것 :", (db_key, salt))
        self.token = "%s/%s/%d" % (self.name, db_key, salt)


print("① __post_init__ 은 __init__ 끝에 불린다")
u = User("준", "KEY", 7)
print("   repr(u) :", repr(u))

print("② InitVar 는 __init__ 서명에는 있고 필드 목록에는 없다")
print("   서명                    :", inspect.signature(User.__init__))
print("   fields()               :", [f.name for f in fields(User)])
print("   __dataclass_fields__   :", list(User.__dataclass_fields__))
print("   ★ 둘이 다르다 — fields() 는 InitVar 를 빼고 덤프는 들고 있다")
print("   db_key 의 _field_type :", User.__dataclass_fields__["db_key"]._field_type.name)
print("   name   의 _field_type :", User.__dataclass_fields__["name"]._field_type.name)

print("③ 인스턴스에는 안 남는다")
print("   vars(u) :", vars(u))
print("   ★ db_key 도 salt 도 없다")

print("④ InitVar 가 있는데 __post_init__ 이 없으면")
try:
    @dataclass
    class NoHook:
        a: int
        b: InitVar[int] = 0

    NoHook(1, 2)
except TypeError as ex:
    print("   TypeError:", ex)
else:
    print("   예외가 안 난다 — 받은 값이 그냥 버려진다 :", vars(NoHook(1, 2)))

print("⑤ __post_init__ 만 있고 InitVar 가 없으면 인자 없이 불린다")


@dataclass
class Simple:
    a: int
    doubled: int = field(init=False, default=0)

    def __post_init__(self):
        self.doubled = self.a * 2


print("   Simple(3) ->", Simple(3))

print("⑥ 검증을 넣는 자리도 여기다")


@dataclass
class Positive:
    n: int

    def __post_init__(self):
        if self.n <= 0:
            raise ValueError("n 은 양수라야 한다: %r" % self.n)


try:
    Positive(-1)
except ValueError as ex:
    print("   Positive(-1) -> ValueError:", ex)
print("   Positive(3)  ->", Positive(3))

print("⑦ ★ 어노테이션을 읽기는 하는데 값이 그 타입인지는 안 본다")


@dataclass
class Typed:
    n: int
    xs: list


t = Typed("정수가 아니다", 3.14)
print("   Typed('정수가 아니다', 3.14) ->", t)
print("   fields 가 적은 타입 :", [(f.name, f.type.__name__) for f in fields(Typed)])
print("   실제로 들어간 타입   :", [type(v).__name__ for v in (t.n, t.xs)])
print("   ★ 검증은 __post_init__ 에 내가 쓰는 것뿐이다")
```

* ②에서 `db_key` 가 **서명·`fields()`·`__dataclass_fields__`** 각각에 **있는가 없는가**?
* ★★ ④에서 `InitVar` 만 쓰고 `__post_init__` 을 안 쓰면 무엇이 터지는가?
* ★★ ⑦에서 `n: int` 자리에 문자열을 넣으면 어떻게 되는가?

### 7. 상속이 기본값 순서에 거는 제약 (경계)

```python
# e36_inherit.py
import inspect
from dataclasses import dataclass, field, fields


print("① 부모에 기본값이 있고 자식에 없으면 — class 문에서 막힌다")


@dataclass
class Base:
    a: int = 0


try:
    @dataclass
    class Sub(Base):
        b: int
except TypeError as ex:
    print("   TypeError:", ex)
print("   ★ 필드가 「부모 먼저」로 줄을 서므로 (a=0, b) 가 되어 문법이 안 선다")

print("② 자식에도 기본값을 주면 된다")


@dataclass
class Sub2(Base):
    b: int = 0


print("   서명 :", inspect.signature(Sub2.__init__))

print("③ ★ kw_only=True 면 그 제약이 사라진다 (3.10+)")


@dataclass(kw_only=True)
class KwBase:
    a: int = 0


@dataclass(kw_only=True)
class KwSub(KwBase):
    b: int


print("   서명 :", inspect.signature(KwSub.__init__))
print("   KwSub(b=1) ->", KwSub(b=1))
try:
    KwSub(1)
except TypeError as ex:
    print("   KwSub(1) -> TypeError:", ex)

print("④ 필드 하나만 kw_only 로 돌릴 수도 있다")


@dataclass
class Mixed:
    a: int = 0
    b: int = field(kw_only=True)


print("   서명 :", inspect.signature(Mixed.__init__))
print("   fields 의 kw_only :", [(f.name, f.kw_only) for f in fields(Mixed)])

print("⑤ 같은 이름을 자식이 다시 적으면 자리는 그대로고 값만 바뀐다")


@dataclass
class Over(Base):
    a: int = 9
    b: int = 1


print("   서명 :", inspect.signature(Over.__init__))
print("   필드 순서 :", [f.name for f in fields(Over)])
print("   Over() ->", Over())

print("⑥ 부모가 dataclass 가 아니면 그 속성은 안 모인다")


class PlainBase:
    z = 1


@dataclass
class FromPlain(PlainBase):
    a: int = 0


print("   fields(FromPlain) :", [f.name for f in fields(FromPlain)])
print("   FromPlain().z     :", FromPlain().z, " <- 보통 상속으로는 보인다")
```

* ①에서 무엇이 터지고, 그 문구는 **`dataclasses` 의 것인가 파이썬 함수 규칙의 것인가**?
* ★ ③의 `kw_only=True` 서명에는 무엇이 하나 더 들어가고, `KwSub(1)` 은 왜 막히는가?
* ★ ⑥에서 `fields(FromPlain)` 과 `FromPlain().z` 가 **왜 다른 답**을 주는가?

### 8. ★★ `slots=True` 가 무엇을 돌려주나 (예측)

```python
# e36_slots.py
import dataclasses
from dataclasses import dataclass


def build(**kw):
    @dataclass(**kw)
    class Row:
        a: int = 0
        b: int = 0
    return Row


print("① slots=True 는 ★ 새 클래스를 만들어 돌려준다 (3.10+)")
BEFORE = {}


def capture(cls):                  # @dataclass 가 받기 직전의 클래스를 붙잡아 둔다
    BEFORE[cls.__name__] = cls
    return cls


@dataclass(slots=True)
@capture
class Slotted:
    a: int = 0


@dataclass
class Normal:
    a: int = 0


Normal = capture(Normal)           # 비교를 맞추려고 같은 방식으로 한 번 더 붙잡는다
print("   slots=True  : 데코레이터 뒤의 이름이 붙잡아 둔 것과 같은 객체인가 :",
      Slotted is BEFORE["Slotted"])
print("   slots 기본값: 같은 객체인가 :", Normal is BEFORE["Normal"])
print("   두 객체의 id 가 다른가 (slots 쪽) :", Slotted is not BEFORE["Slotted"])
print("   붙잡아 둔 쪽에 __slots__ 가 있나  :", "__slots__" in BEFORE["Slotted"].__dict__)
print("   돌려받은 쪽에 __slots__ 가 있나   :", "__slots__" in Slotted.__dict__)
print("   ★ class 문이 만든 이름에 결과가 다시 묶이므로 평소에는 이 교체가 안 보인다")

print("② 함수로 부르면 더 분명하다")
raw = type("Raw", (), {"__annotations__": {"a": int, "b": int}, "a": 0, "b": 0})
wrapped = dataclass(slots=True)(raw)
print("   dataclass(slots=True)(raw) is raw :", wrapped is raw)
print("   raw 에 __slots__ 가 생겼나        :", "__slots__" in raw.__dict__)
print("   wrapped.__slots__                :", wrapped.__dict__.get("__slots__"))
print("   ★ 원본은 그대로 두고 복제본을 만든다")

print("③ slots=False 는 제자리다")
raw2 = type("Raw2", (), {"__annotations__": {"a": int}, "a": 0})
print("   dataclass()(raw2) is raw2 :", dataclass(raw2) is raw2)

print("④ 인스턴스에 __dict__ 가 없다")
S, N = build(slots=True), build()
s, n = S(), N()
print("   slots 판에 __dict__ 가 있나 :", hasattr(s, "__dict__"))
print("   보통 판에 __dict__ 가 있나  :", hasattr(n, "__dict__"))
try:
    s.extra = 1
except AttributeError as ex:
    print("   s.extra = 1 -> AttributeError:", ex)
print("   S.__slots__ :", S.__dict__.get("__slots__"))
print("   클래스 칸의 a 의 정체 :", type(S.__dict__["a"]).__name__)
print("   ★ 33번이 실측한 member_descriptor 그대로다")

print("⑤ 크기 — 어느 쪽이 작나만 본다")
import sys
print("   보통 판 합계  :", sys.getsizeof(n) + sys.getsizeof(n.__dict__))
print("   slots 판 합계 :", sys.getsizeof(s))
print("   어느 쪽이 작나 :",
      "slots" if sys.getsizeof(s) < sys.getsizeof(n) + sys.getsizeof(n.__dict__) else "보통")
print("   ★ 속도는 이 문서가 한 번도 안 쟀다")

print("⑥ frozen 과 같이 쓰면 둘 다 먹는다")
F = build(slots=True, frozen=True)
f = F()
try:
    f.a = 1
except dataclasses.FrozenInstanceError as ex:
    print("   f.a = 1 ->", type(ex).__name__ + ":", ex)
print("   hasattr(f, '__dict__') :", hasattr(f, "__dict__"))
```

* ①에서 `Slotted is BEFORE["Slotted"]` 는 참인가 거짓인가 — `Normal` 쪽은?
* ★ 평소에는 **왜 그 교체가 안 보이는가**?
* ★ ④에서 클래스 칸의 `a` 의 타입 이름은 무엇이고, 그것이 어느 주제의 실측과 같은가?

### 9. 어노테이션과 필드 (경계)

* 어노테이션 없이 값만 대입하면 그것이 필드인가?
* ★ `dataclasses` 가 어노테이션을 **읽는다**는 것과 **값이 그 타입인지 본다**는 것은 같은 말인가?

### 10. ★★★ 방어가 반쪽인 이유 (왜)

* 가변 기본값 판별 기준이 **정확히 무엇**인가 — 문서의 낱말로 답하라.
* ★ 문서가 스스로 그 방어를 무엇이라 부르는가?
* ★★ 그래서 **어떤 기본값이 조용히 새어 나가는가**?

### 11. 층 가르기 (경계)

* 「`order=True` 가 넷을 만든다」는 **모듈 계약인가 CPython 구현인가**?
* ★ 「`slots=True` 가 새 클래스를 돌려준다」는 어느 층인가 — 문서가 그것을 적는가?
* ★ `MISSING` 의 기본 `repr` 을 이 문서가 **왜 그대로 안 찍었는가**?

### 12. 이웃 주제와의 경계 (연결)

* [20](../20-mutable-default-args/2-summary.md)·[30](../30-repr-eq-hash-contracts/2-summary.md)·[31](../31-comparison-protocol-and-sortability/2-summary.md)·[33](../33-property-descriptor-slots/2-summary.md)·[34](../34-inheritance-mro-super/2-summary.md) 가 이 주제에 **각각 무엇을 대 주는가** — 한 줄씩.
* ★ Kotlin 갈래 목록([`kotlin/syntax/README.md`](../../../kotlin/syntax/README.md))의 **22번** 과 견주면 「비교에서 필드를 빼는 법」이 어떻게 다른가?
* ★ 목록의 **40번 주제** 의 「힌트는 실행을 안 바꾼다」에 이 주제가 **어떤 예외**인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|---|---|---|---|
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |
