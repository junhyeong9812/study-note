# python/syntax/35-abc-and-protocol — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> ★★★ 이 주제의 답은 **대부분** 「참·거짓」과 「**막히나 안 막히나**」다.
> 그래서 **「막힐 것 같다」를 「막힌다」로 적으면 틀린다** — 이 주제에서 가장 많이 틀리는 자리가 그것이다.
> ★★ 그리고 **「아무 일도 안 난다」가 정답인 문항이 하나 있다**(3번). 침묵이 근거인 주제다.
>
> 실행 환경: `python3` **3.12.3** · Linux. 던지는 형태는 `python3 - <파일` 로 고정했다.
> ★★★ **이 머신에 `mypy`·`pyright` 가 없다.** 그래서 「타입 검사기가 이렇게 잡아 준다」는 답은
> 이 주제에 **하나도 없다.** 물음도 전부 **런타임** 쪽이다.
> ★ **이 주제는 [32번](../32-container-protocol/1-question.md)을 전부 쓴다** — `collections.abc` 믹스인이 거기 정본이다.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. ABC 에 세 번 던지면 (예측)

```python
# e35_abc.py
import abc


class Storage(abc.ABC):
    @abc.abstractmethod
    def read(self, key): ...

    @abc.abstractmethod
    def write(self, key, value): ...

    def copy(self, src, dst):          # 믹스인 — 추상이 아니다
        self.write(dst, self.read(src))


print("① 추상 메서드가 무엇인지는 클래스가 들고 있다")
print("   Storage.__abstractmethods__ :", sorted(Storage.__abstractmethods__))

print("② 하나도 안 채우면 — 인스턴스화가 거부된다")
try:
    Storage()
except TypeError as ex:
    print("   TypeError:", ex)

print("③ 하나만 채워도 거부된다 — 남은 이름을 전부 나열해 준다")


class Half(Storage):
    def read(self, key):
        return None


print("   Half.__abstractmethods__ :", sorted(Half.__abstractmethods__))
try:
    Half()
except TypeError as ex:
    print("   TypeError:", ex)

print("④ 다 채우면 만들어지고 믹스인이 따라온다")


class Mem(Storage):
    def __init__(self):
        self.d = {}

    def read(self, key):
        return self.d.get(key)

    def write(self, key, value):
        self.d[key] = value


m = Mem()
m.write("a", 1)
m.copy("a", "b")
print("   Mem.__abstractmethods__ :", sorted(Mem.__abstractmethods__), "(비었다)")
print("   copy 를 안 썼는데 되나   :", "copy" in Mem.__dict__, "->", m.d)

print("⑤ ★ 막히는 자리는 「정의할 때」가 아니라 「만들 때」다")
print("   Half 라는 클래스는 만들어졌나 :", Half.__name__, "| 타입 :", type(Half).__name__)
print("   Storage 가 Half 의 MRO 에 있나 :", Storage in Half.__mro__)
print("   ★ class 문은 통과했고 Half() 한 줄에서만 막힌다")

print("⑥ 클래스 쪽으로는 부를 수 있다 — 추상이라고 몸통이 없는 게 아니다")
print("   Storage.copy 가 있나 :", callable(Storage.copy))
print("   Storage.read(None, 'k') ->", Storage.read(None, "k"))
```

* ②와 ③의 두 메시지는 **어떻게 다른가** — 무엇이 단수·복수로 갈리는가?
* ★ ④에서 `copy` 가 `Mem.__dict__` 에 있는가, 그런데 도는가?
* ★★ ⑤가 묻는 것 — `Half` 라는 **클래스는 만들어졌는가**?

### 2. `register()` 를 하면 무엇이 바뀌고 무엇이 안 바뀌나 (예측)

```python
# e35_register.py
import abc


class Quacker(abc.ABC):
    @abc.abstractmethod
    def quack(self): ...

    def twice(self):
        return self.quack() + self.quack()


class Duck:                      # 상속도 등록도 아직 안 했다
    def quack(self):
        return "꽥"


class Rock:                      # quack 이 아예 없다
    pass


print("① 등록 전")
print("   isinstance(Duck(), Quacker) :", isinstance(Duck(), Quacker))
print("② register 로 가짜 서브클래스로 만든다")
Quacker.register(Duck)
print("   isinstance(Duck(), Quacker)  :", isinstance(Duck(), Quacker))
print("   issubclass(Duck, Quacker)    :", issubclass(Duck, Quacker))
print("③ ★ 그런데 상속은 아니다 — MRO 에 없다")
print("   Duck.__mro__    :", [k.__name__ for k in Duck.__mro__])
print("   Duck.__bases__  :", [k.__name__ for k in Duck.__bases__])
print("   Quacker in Duck.__mro__ :", Quacker in Duck.__mro__)
print("④ 그래서 믹스인이 안 따라온다")
print("   hasattr(Duck(), 'twice') :", hasattr(Duck(), "twice"))
print("⑤ 추상 메서드를 안 채워도 등록은 받아 준다")
Quacker.register(Rock)
print("   isinstance(Rock(), Quacker) :", isinstance(Rock(), Quacker))
print("   Rock 에 quack 이 있나        :", hasattr(Rock(), "quack"))
print("   ★ register 는 「그렇게 치자」는 선언일 뿐 아무것도 검사하지 않는다")
print("⑥ 어느 쪽 목록에 나오나")


class RealSub(Quacker):
    def quack(self):
        return "진짜"


print("   Quacker.__subclasses__() :", [k.__name__ for k in Quacker.__subclasses__()])
print("   ★ 진짜 상속만 여기 나온다 — register 한 Duck 과 Rock 은 안 보인다")
print("   RealSub 는 믹스인을 받나 :", RealSub().twice())
```

* ③에서 `Duck.__mro__` 는 어떻게 나오는가?
* ★ ④에서 `hasattr(Duck(), 'twice')` 는 참인가 거짓인가 — **왜**인가?
* ★★ ⑤에서 `quack` 이 아예 없는 `Rock` 을 등록하면 어떻게 되는가?

### 3. ★★ `Protocol` 에 네 지점을 던지면 (예측)

```python
# e35_protocol.py
from typing import Protocol


class Greeter(Protocol):
    def greet(self, name: str) -> str: ...


class Polite:                      # Greeter 를 모른다. import 조차 안 했다고 치자
    def greet(self, name: str) -> str:
        return "안녕 " + name


class Silent:                      # greet 이 없다
    pass


def welcome(g: Greeter) -> str:    # ★ 힌트일 뿐이다
    return g.greet("세계")


print("① 상속 없이 만족한다 — 힌트에 Greeter 라고 적었는데 그냥 돈다")
print("   welcome(Polite()) ->", welcome(Polite()))
print("   Greeter in Polite.__mro__ :", Greeter in Polite.__mro__)

print("② ★ 만족하지 않는 것을 넣어도 런타임은 아무 말이 없다")
try:
    print("   welcome(Silent()) ->", welcome(Silent()))
except AttributeError as ex:
    print("   welcome(Silent()) -> AttributeError:", ex)
print("   ★ 막힌 것은 「프로토콜 위반」이 아니라 「없는 속성을 읽었다」다")

print("③ 힌트를 아예 거짓말로 적어도 실행은 안 막힌다")
print("   welcome.__annotations__ :",
      {k: getattr(v, "__name__", v) for k, v in welcome.__annotations__.items()})
print("   welcome(42) 를 부르면 :", end=" ")
try:
    welcome(42)
except AttributeError as ex:
    print("AttributeError:", ex)

print("④ Protocol 자체는 인스턴스로 못 만든다")
try:
    Greeter()
except TypeError as ex:
    print("   TypeError:", ex)

print("⑤ ★★ 그런데 명시적으로 물려받고 아무것도 구현 안 해도 막지 않는다")


class Explicit(Greeter):
    pass


e = Explicit()
print("   Explicit() 가 만들어졌나       :", type(e).__name__)
print("   Explicit.__abstractmethods__ :", sorted(Explicit.__abstractmethods__), "(비었다)")
print("   e.greet('세계') ->", repr(e.greet("세계")))
print("   ★ 예외가 아니라 None 이 나온다 — 몸통의 ... 이 그대로 돌았다")
print("   ★ 35번의 세 갈래 중 가운데다 — ABC 는 여기서 TypeError 로 막았다")
```

* ①\~⑤ 중 **막히는 것은 몇 개**이고 어느 것인가?
* ★ ②에서 나는 예외는 무엇이고, 그 이름이 **왜 「프로토콜 위반」이 아닌가**?
* ★★★ ⑤에서 `Explicit()` 가 만들어지는가, 그리고 `e.greet('세계')` 는 **무엇을 돌려주는가**?

### 4. ★★ `runtime_checkable` 이 보는 것 (예측)

```python
# e35_runtime.py
import warnings
from typing import Protocol, runtime_checkable


@runtime_checkable
class Closer(Protocol):
    def close(self) -> None: ...


class Good:
    def close(self) -> None:
        pass


class WrongSig:
    def close(self, a, b, c):          # 인자 셋을 받는다
        pass


class NotCallable:
    close = 42                          # 함수가 아니다


class Missing:
    pass


print("① 이름이 있으면 참이다")
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    rows = [(cls.__name__, isinstance(cls(), Closer)) for cls in (Good, WrongSig, NotCallable, Missing)]
for nm, ok in rows:
    print("   isinstance(%-12s(), Closer) : %s" % (nm, ok))
print("   ★ 던지는 동안 잡힌 경고 :", [str(w.message) for w in caught] or "없음")
print("   ★ WrongSig 는 인자 개수가 다른데 True 다 — 서명은 안 본다")
print("   ★ NotCallable 은 정수인데 True 다 — 부를 수 있는지도 안 본다")

print("② 그래서 isinstance 를 통과하고 호출에서 터진다")
for cls in (WrongSig, NotCallable):
    o = cls()
    print("   %-12s isinstance:%-5s ->" % (cls.__name__, isinstance(o, Closer)), end=" ")
    try:
        o.close()
        print("호출 성공")
    except TypeError as ex:
        print("TypeError:", ex)

print("③ runtime_checkable 을 안 붙이면 isinstance 자체가 막힌다")


class Plain(Protocol):
    def close(self) -> None: ...


try:
    isinstance(Good(), Plain)
except TypeError as ex:
    print("   TypeError:", ex)

print("④ ★ 메서드 아닌 멤버가 있으면 — isinstance 는 되고 issubclass 가 막힌다")


@runtime_checkable
class HasName(Protocol):
    name: str


class Named:
    name = "이름"


print("   isinstance(Named(), HasName) :", isinstance(Named(), HasName))
try:
    issubclass(Named, HasName)
except TypeError as ex:
    print("   issubclass(Named, HasName) -> TypeError:", ex)
print("   ★ 둘이 갈린다 — 인스턴스는 속성을 들고 있는지 물어볼 수 있지만 클래스는 아니다")

print("⑤ 무엇을 보는지 프로토콜 자신이 들고 있다")
print("   Closer.__protocol_attrs__  :", sorted(Closer.__protocol_attrs__))
print("   HasName.__protocol_attrs__ :", sorted(HasName.__protocol_attrs__))
```

* ①의 네 줄은 각각 참인가 거짓인가 — `close = 42` 인 클래스는?
* ★ 그 동안 **경고가 몇 건** 잡혔는가?
* ★★ ④에서 `isinstance` 와 `issubclass` 의 답이 **갈리는가** — 갈린다면 어느 쪽이 막히는가?

### 5. 갈고리를 직접 달면 (예측)

```python
# e35_hook.py
import abc
from collections.abc import Iterable, Sized, Sequence


class HasArea(abc.ABC):
    @classmethod
    def __subclasshook__(cls, C):
        if cls is HasArea:
            return any("area" in B.__dict__ for B in C.__mro__)
        return NotImplemented


class Circle:
    def area(self): return 3


class Point:
    pass


print("① 상속도 등록도 안 했는데 isinstance 가 참이다")
print("   isinstance(Circle(), HasArea) :", isinstance(Circle(), HasArea))
print("   isinstance(Point(),  HasArea) :", isinstance(Point(), HasArea))
print("   HasArea in Circle.__mro__     :", HasArea in Circle.__mro__)

print("② collections.abc 가 그 갈고리를 쓴다 — 32번이 실측한 자리를 인용만 한다")


class OnlyIter:
    def __iter__(self):
        return iter(())


for abc_cls in (Iterable, Sized, Sequence):
    print("   isinstance(OnlyIter(), %-8s) : %s" % (abc_cls.__name__, isinstance(OnlyIter(), abc_cls)))
print("   ★ 한 메서드짜리 ABC 만 오리 판정을 한다 — 정본은 32번이다")

print("③ NotImplemented 를 돌려주면 기본 판정으로 떨어진다")


class Sub(HasArea):
    def area(self): return 1


print("   Sub 는 진짜 하위 클래스인가 :", HasArea in Sub.__mro__)
print("   isinstance(Sub(), HasArea)  :", isinstance(Sub(), HasArea))

print("④ ★ 갈고리는 「이름이 있나」만 본다 — 서명도 몸통도 안 본다")


class Liar:
    area = "이건 함수가 아니라 문자열이다"


print("   isinstance(Liar(), HasArea) :", isinstance(Liar(), HasArea))
print("   type(Liar.area).__name__    :", type(Liar.area).__name__)

print("⑤ ★ 30번이 남겨 둔 물음 — typing.Hashable 은 런타임에 무엇을 보나")
from collections.abc import Hashable


class OnlyEq:
    def __eq__(self, other):
        return True


class Plain2:
    pass


print("   OnlyEq.__hash__                :", OnlyEq.__hash__)
print("   isinstance(OnlyEq(), Hashable) :", isinstance(OnlyEq(), Hashable))
print("   isinstance(Plain2(), Hashable) :", isinstance(Plain2(), Hashable))
print("   Hashable 이 보는 것            : __hash__ 하나 — Iterable 과 같은 오리 판정이다")
```

* ④에서 `Liar.area` 가 **문자열인데** `isinstance` 는 참인가 거짓인가?
* ★ ⑤에서 `__eq__` 만 정의한 클래스가 `Hashable` 에 참인가 거짓인가?

### 6. 같은 모양을 두 장치로 적으면 (예측)

```python
# e35_choose.py
import abc
from collections.abc import Sequence
from typing import Protocol, runtime_checkable


class AbcSeq(Sequence):              # ① ABC — 둘만 주면 다섯이 따라온다
    def __init__(self, d):
        self.d = list(d)

    def __len__(self):
        return len(self.d)

    def __getitem__(self, i):
        return self.d[i]


@runtime_checkable
class SeqLike(Protocol):             # ② Protocol — 같은 모양을 요구만 한다
    def __len__(self) -> int: ...
    def __getitem__(self, i): ...


class ProtoSeq:
    def __init__(self, d):
        self.d = list(d)

    def __len__(self):
        return len(self.d)

    def __getitem__(self, i):
        return self.d[i]


a, p = AbcSeq("abc"), ProtoSeq("abc")
print("① 무엇이 공짜로 따라오나")
free = ("__contains__", "__iter__", "__reversed__", "index", "count")
print("   ABC      쪽 :", [n for n in free if hasattr(a, n)])
print("   Protocol 쪽 :", [n for n in free if hasattr(p, n)] or "아무것도 없음")
print("   a.index('c') ->", a.index("c"))
try:
    p.index("c")
except AttributeError as ex:
    print("   p.index('c') -> AttributeError:", ex)

print("② 둘 다 isinstance 는 참이다 — 답이 같아 보이는 자리")
print("   isinstance(a, Sequence) :", isinstance(a, Sequence))
print("   isinstance(p, SeqLike)  :", isinstance(p, SeqLike))
print("   isinstance(p, Sequence) :", isinstance(p, Sequence), " <- ABC 쪽은 거짓이다")

print("③ MRO 가 다르다 — ABC 는 진짜 조상이고 Protocol 은 아니다")
print("   AbcSeq.__mro__   :", [k.__name__ for k in AbcSeq.__mro__])
print("   ProtoSeq.__mro__ :", [k.__name__ for k in ProtoSeq.__mro__])

print("④ 그런데 낡은 프로토콜은 양쪽 다 놓친다 — 32번이 실측한 자리다")


class Old:
    def __getitem__(self, i):
        return ["a", "b"][i]


print("   isinstance(Old(), Sequence) :", isinstance(Old(), Sequence))
print("   isinstance(Old(), SeqLike)  :", isinstance(Old(), SeqLike))
print("   그런데 for 는 돈다          :", [v for v in Old()])
print("   ★ SeqLike 는 __len__ 이 없어 거짓이다 — 이름만 보기 때문이다")

print("⑤ 어느 쪽이 「만들 때」 막나")


class AbcBroken(Sequence):
    pass


try:
    AbcBroken()
except TypeError as ex:
    print("   ABC      :", type(ex).__name__ + ":", ex)


class ProtoBroken(SeqLike):
    pass


print("   Protocol : ProtoBroken() 이 만들어졌다 ->", type(ProtoBroken()).__name__)
```

* ①에서 **각각 몇 개**가 공짜로 따라오는가?
* ★ ④에서 `__getitem__` 만 가진 낡은 객체는 **양쪽 다** 어떻게 판정되는가 — 그런데 `for` 는 도는가?
* ★★ ⑤에서 안 채운 하위 클래스를 만들면 **두 장치가 어떻게 갈리는가**?

### 7. ABC 가 막는 시점 (왜)

* ABC 는 **왜** 「정의할 때」가 아니라 「만들 때」 막는가?
* ★ 그 설계가 **무엇을 가능하게 하는가** — 중간 단계 클래스를 생각해 보라.

### 8. `register()` 의 대가 (경계)

* `register()` 가 **하는 일 둘**과 **안 하는 일 넷**을 각각 대면?
* ★ 「누가 이 ABC 를 만족하나」를 묻는 창이 **몇 개**이고 각각 무엇을 놓치는가?

### 9. ★★ 이름까지만 보는 것들 (경계)

* `runtime_checkable` 이 **안 보는 것 셋**을 대면?
* ★ `__subclasshook__` 도 같은 한계를 갖는가 — 어느 출력이 그것을 말하는가?
* ★ 런타임에 **서명까지** 확인하려면 무엇을 써야 하는가?

### 10. ★★★ Go 의 암묵 구현과 견주면 (연결)

* Go 갈래 목록([`go/syntax/README.md`](../../../go/syntax/README.md))의 **20번** 과 이 주제가 **같은 것**은 무엇인가?
* ★★ **다른 것**은 무엇인가 — 「누가 강제하나」와 「서명을 보나」로 답하라.
* ★ Go 에서 `var _ Iface = (*T)(nil)` 이 하는 일에 해당하는 것이 파이썬에는 무엇인가?

### 11. 층 가르기 (경계)

* 「`runtime_checkable` 은 서명을 안 본다」는 **언어 보장인가 구현인가**?
* ★ `__protocol_attrs__` 라는 이름은 어느 층인가?
* ★★★ 이 주제에서 **못 연 층**은 무엇이고, 그것을 **어떻게 적어야** 하는가?

### 12. 이웃 주제와의 경계 (연결)

* [32번](../32-container-protocol/2-summary.md)이 정본인 것과 이 주제가 정본인 것을 한 줄씩으로 가르면?
* ★ 「이터러블인가」를 `Protocol` 로 검사할 수 있는가 — 안 되면 무엇으로 하는가?
* ★ [30번](../30-repr-eq-hash-contracts/2-summary.md)이 남겨 둔 `typing.Hashable` 물음에 이 주제가 **어디까지** 답했는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|---|---|---|---|
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |
