# python/syntax/35-abc-and-protocol — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> [1-question.md](1-question.md)의 번호와 **1:1**로 대응한다. 질문 12개 = 답 12개.
>
> 이 파일의 모든 출력은 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> 던지는 형태는 `python3 - <파일` 로 고정했다.
> ★★★ **트레이스백이 한 블록도 없다.** 던진 예외가 전부 `abc`·`typing` 을 지나
> **절대 경로가 박히기** 때문에 전부 `except` 로 받아 **타입과 메시지만** 찍었다.
> 그래서 이 파일에는 **줄 번호에 기대는 칸이 하나도 없다.**
> ★ `frozenset` 인 `__abstractmethods__`·`__protocol_attrs__` 는 **전부 `sorted()`** 로 찍었다.

## 정답

### 1. 복수형과 단수형으로 갈리고, `copy` 는 칸에 없는데 돈다

**출력**

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
```text
===== python3 - <e35_abc.py =====
① 추상 메서드가 무엇인지는 클래스가 들고 있다
   Storage.__abstractmethods__ : ['read', 'write']
② 하나도 안 채우면 — 인스턴스화가 거부된다
   TypeError: Can't instantiate abstract class Storage without an implementation for abstract methods 'read', 'write'
③ 하나만 채워도 거부된다 — 남은 이름을 전부 나열해 준다
   Half.__abstractmethods__ : ['write']
   TypeError: Can't instantiate abstract class Half without an implementation for abstract method 'write'
④ 다 채우면 만들어지고 믹스인이 따라온다
   Mem.__abstractmethods__ : [] (비었다)
   copy 를 안 썼는데 되나   : False -> {'a': 1, 'b': 1}
⑤ ★ 막히는 자리는 「정의할 때」가 아니라 「만들 때」다
   Half 라는 클래스는 만들어졌나 : Half | 타입 : ABCMeta
   Storage 가 Half 의 MRO 에 있나 : True
   ★ class 문은 통과했고 Half() 한 줄에서만 막힌다
⑥ 클래스 쪽으로는 부를 수 있다 — 추상이라고 몸통이 없는 게 아니다
   Storage.copy 가 있나 : True
   Storage.read(None, 'k') -> None
(exit 0)
```

**왜 그런가**

* ★★ **②와 ③의 차이는 남은 개수다.**
  둘이면 `without an implementation for abstract methods 'read', 'write'`,
  하나면 `without an implementation for abstract method 'write'` —
  **`methods` 가 `method` 로 바뀐다.**
  ★ **무엇을 더 채워야 하는지 메시지가 정확히 알려 준다**는 것이 ABC 의 첫 번째 값이다.
* ★ **④에서 `"copy" in Mem.__dict__` 가 `False` 인데 `m.copy(...)` 가 돌았다.**
  [34번](../34-inheritance-mro-super/2-summary.md)의 MRO 를 타고 `Storage` 것을 쓴 것이다.
  ★ **추상 메서드만 강제하고 나머지는 그냥 물려준다** — 이것이 ABC 의 두 번째 값이고,
  `Protocol` 이 못 주는 바로 그것이다(6번 답).
* ★★★ **⑤가 막히는 자리를 못 박는다.** `Half` 라는 **클래스는 만들어졌고** 타입이 `ABCMeta` 다.
  `Storage` 도 `Half.__mro__` 에 있다.
  **`class` 문은 통과했고 `Half()` 한 줄에서만 막힌다.**
* ★ **⑥ — 추상 메서드라고 몸통이 없는 것이 아니다.** `Storage.read(None, "k")` 가 `None` 을 돌려준다.
  **클래스 쪽으로 직접 부르는 것은 아무도 안 막는다.**

### 2. `__mro__` 에 없고, 믹스인도 안 오고, 아무것도 안 검사한다

**출력**

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
```text
===== python3 - <e35_register.py =====
① 등록 전
   isinstance(Duck(), Quacker) : False
② register 로 가짜 서브클래스로 만든다
   isinstance(Duck(), Quacker)  : True
   issubclass(Duck, Quacker)    : True
③ ★ 그런데 상속은 아니다 — MRO 에 없다
   Duck.__mro__    : ['Duck', 'object']
   Duck.__bases__  : ['object']
   Quacker in Duck.__mro__ : False
④ 그래서 믹스인이 안 따라온다
   hasattr(Duck(), 'twice') : False
⑤ 추상 메서드를 안 채워도 등록은 받아 준다
   isinstance(Rock(), Quacker) : True
   Rock 에 quack 이 있나        : False
   ★ register 는 「그렇게 치자」는 선언일 뿐 아무것도 검사하지 않는다
⑥ 어느 쪽 목록에 나오나
   Quacker.__subclasses__() : ['RealSub']
   ★ 진짜 상속만 여기 나온다 — register 한 Duck 과 Rock 은 안 보인다
   RealSub 는 믹스인을 받나 : 진짜진짜
(exit 0)
```

**왜 그런가**

* ★★★ **③이 과녁이다.** `Duck.__mro__` 가 `['Duck', 'object']` — **`Quacker` 가 없다.**
  `__bases__` 도 `['object']` 다.
  ★ 문서의 낱말이 그것을 말한다 — *"Register subclass as a 'virtual subclass'"*.
  「**가상(virtual)**」은 **명부에만 있다**는 뜻이다.
* ★ **④가 그 대가다.** `hasattr(Duck(), 'twice')` 가 **거짓**이다.
  MRO 에 없으니 물려받을 길이 없다 — [34번](../34-inheritance-mro-super/2-summary.md)의 줄이 곧 물려받는 통로이기 때문이다.
  ★ ⑥의 마지막 줄이 대비다 — **진짜 상속한 `RealSub` 는 `twice()` 를 받는다**(`진짜진짜`).
* ★★ **⑤가 가장 조용한 자리다.** `Rock` 은 `quack` 이 **아예 없는데** 등록이 받아들여지고
  `isinstance` 가 참이다.
  ★★★ **동작 1이 보여 준 ABC 의 강제가 이 경로로 통째로 우회된다.**
  「ABC 를 쓰면 계약이 지켜진다」가 여기서 깨진다.
* ★ **⑥ — `__subclasses__()` 에는 진짜 상속만 나온다**(`['RealSub']`).
  **「누가 만족하나」를 묻는 창이 둘로 갈린다** — `isinstance` 는 등록을 보고 `__subclasses__()` 는 못 본다.

### 3. 막히는 것은 ④ 하나뿐 — `Explicit()` 는 만들어지고 `greet` 은 `None` 을 준다

**출력**

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
```text
===== python3 - <e35_protocol.py =====
① 상속 없이 만족한다 — 힌트에 Greeter 라고 적었는데 그냥 돈다
   welcome(Polite()) -> 안녕 세계
   Greeter in Polite.__mro__ : False
② ★ 만족하지 않는 것을 넣어도 런타임은 아무 말이 없다
   welcome(Silent()) -> AttributeError: 'Silent' object has no attribute 'greet'
   ★ 막힌 것은 「프로토콜 위반」이 아니라 「없는 속성을 읽었다」다
③ 힌트를 아예 거짓말로 적어도 실행은 안 막힌다
   welcome.__annotations__ : {'g': 'Greeter', 'return': 'str'}
   welcome(42) 를 부르면 : AttributeError: 'int' object has no attribute 'greet'
④ Protocol 자체는 인스턴스로 못 만든다
   TypeError: Protocols cannot be instantiated
⑤ ★★ 그런데 명시적으로 물려받고 아무것도 구현 안 해도 막지 않는다
   Explicit() 가 만들어졌나       : Explicit
   Explicit.__abstractmethods__ : [] (비었다)
   e.greet('세계') -> None
   ★ 예외가 아니라 None 이 나온다 — 몸통의 ... 이 그대로 돌았다
   ★ 35번의 세 갈래 중 가운데다 — ABC 는 여기서 TypeError 로 막았다
(exit 0)
```

**왜 그런가**

* ★★★ **다섯 지점 중 막힌 것은 ④ 하나**이고, 그것은 **계약과 아무 상관이 없다** —
  프로토콜 객체 자체를 만들려 한 것뿐이다(`Protocols cannot be instantiated`).
* ★★ **②의 예외 이름이 중요하다.** `AttributeError: 'Silent' object has no attribute 'greet'` —
  ★ **「프로토콜 위반」이라는 예외가 아니다.** 그냥 **없는 속성을 읽은 것**이다.
  런타임은 `Greeter` 라는 이름을 **한 번도 안 봤다.**
  ★ 힌트를 지우고 코드를 돌려도 **한 글자도 안 바뀐다**는 뜻이다.
* ★ **③이 그것을 못 박는다.** 힌트가 `Greeter` 인데 **정수 `42`** 를 넣어도 같은 자리까지 간다.
  ★ 「힌트는 실행을 안 바꾼다」는 목록의 **40번 주제** 가 정본이고 여기서는 결과만 쓴다.
* ★★★ **⑤가 이 문항의 과녁이다.** `class Explicit(Greeter): pass` — **명시적으로 물려받고
  아무것도 구현 안 했는데** 인스턴스가 만들어진다.
  `Explicit.__abstractmethods__` 가 **빈 `frozenset`** 이다.
  ★ 그리고 `e.greet("세계")` 가 **예외가 아니라 `None`** 을 준다 — **몸통의 `...` 이 그대로 돌았다.**
  ★★ **같은 자리에서 ABC 는 `TypeError` 로 막았다**(1번 답의 ②).
  세 갈래 중 **가운데가 여기**다.

★★★ **판정 한 줄** — **`Protocol` 은 런타임에 아무것도 강제하지 않는다.
강제하는 것은 타입 검사기이고, 이 머신에는 그것이 없다**(머리말의 첫 블록).

### 4. `close = 42` 도 참이고, 경고는 0건, `issubclass` 만 막힌다

**출력**

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
```text
===== python3 - <e35_runtime.py =====
① 이름이 있으면 참이다
   isinstance(Good        (), Closer) : True
   isinstance(WrongSig    (), Closer) : True
   isinstance(NotCallable (), Closer) : True
   isinstance(Missing     (), Closer) : False
   ★ 던지는 동안 잡힌 경고 : 없음
   ★ WrongSig 는 인자 개수가 다른데 True 다 — 서명은 안 본다
   ★ NotCallable 은 정수인데 True 다 — 부를 수 있는지도 안 본다
② 그래서 isinstance 를 통과하고 호출에서 터진다
   WrongSig     isinstance:True  -> TypeError: WrongSig.close() missing 3 required positional arguments: 'a', 'b', and 'c'
   NotCallable  isinstance:True  -> TypeError: 'int' object is not callable
③ runtime_checkable 을 안 붙이면 isinstance 자체가 막힌다
   TypeError: Instance and class checks can only be used with @runtime_checkable protocols
④ ★ 메서드 아닌 멤버가 있으면 — isinstance 는 되고 issubclass 가 막힌다
   isinstance(Named(), HasName) : True
   issubclass(Named, HasName) -> TypeError: Protocols with non-method members don't support issubclass()
   ★ 둘이 갈린다 — 인스턴스는 속성을 들고 있는지 물어볼 수 있지만 클래스는 아니다
⑤ 무엇을 보는지 프로토콜 자신이 들고 있다
   Closer.__protocol_attrs__  : ['close']
   HasName.__protocol_attrs__ : ['name']
(exit 0)
```

**왜 그런가**

* ★★★ **①에서 `WrongSig` 와 `NotCallable` 둘 다 `True`** 다.
  인자 개수가 셋이나 달라도, 아예 **정수여도** 통과한다. 거짓인 것은 `Missing` 하나뿐이다.
  ★ 문서가 한계를 직접 적는다 — *"only the presence of the required methods, not their type signatures"*.
* ★ **경고는 `없음`** 이다. `warnings.catch_warnings(record=True)` 로 잡아 확인했다.
  ★★ **잡아서 stdout 에 찍은 이유**가 있다 — 안 잡으면 경고가 **stderr 로 새어**
  한 블록 안에서 **순서가 어디로 받느냐에 달리게** 된다. 「없음」도 출력이므로 결정적으로 만들어 찍었다.
* ★★ **②가 대가를 보인다.** `isinstance` 를 통과한 둘이 **호출에서 터진다** —
  `WrongSig.close() missing 3 required positional arguments: 'a', 'b', and 'c'` 와
  `'int' object is not callable`.
  ★ **검사한 자리와 터지는 자리가 다르다.**
* **③ — 안 붙이면 `isinstance` 자체가 막힌다.**
  `Instance and class checks can only be used with @runtime_checkable protocols`.
  ★ **기본값**이 「**못 물어본다**」라는 것이 PEP 544 의 태도다.
* ★★★ **④에서 둘이 갈린다.** `isinstance(Named(), HasName)` 는 **참**인데
  `issubclass(Named, HasName)` 는 `Protocols with non-method members don't support issubclass()` 로 막힌다.
  ★ **이유가 논리적이다** — 인스턴스는 **그 속성을 실제로 들고 있는지** 물어볼 수 있지만,
  클래스만 보고는 **인스턴스가 그 속성을 갖게 될지** 알 수 없다.
  ★ `__init__` 안에서 붙이는 속성은 **클래스 칸에 없기** 때문이다([29번](../29-classes-and-attribute-lookup/2-summary.md)의 두 칸).
* ★ **⑤ — 프로토콜이 무엇을 보는지 자기가 들고 있다.** 다만 `__protocol_attrs__` 는
  **3.12 에서 노출된 내부 이름**이라 흔들리는 칸이다.

### 5. `Liar` 도 참이고, `__eq__` 만 정의한 클래스는 `Hashable` 에 거짓이다

**출력**

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
```text
===== python3 - <e35_hook.py =====
① 상속도 등록도 안 했는데 isinstance 가 참이다
   isinstance(Circle(), HasArea) : True
   isinstance(Point(),  HasArea) : False
   HasArea in Circle.__mro__     : False
② collections.abc 가 그 갈고리를 쓴다 — 32번이 실측한 자리를 인용만 한다
   isinstance(OnlyIter(), Iterable) : True
   isinstance(OnlyIter(), Sized   ) : False
   isinstance(OnlyIter(), Sequence) : False
   ★ 한 메서드짜리 ABC 만 오리 판정을 한다 — 정본은 32번이다
③ NotImplemented 를 돌려주면 기본 판정으로 떨어진다
   Sub 는 진짜 하위 클래스인가 : True
   isinstance(Sub(), HasArea)  : True
④ ★ 갈고리는 「이름이 있나」만 본다 — 서명도 몸통도 안 본다
   isinstance(Liar(), HasArea) : True
   type(Liar.area).__name__    : str
⑤ ★ 30번이 남겨 둔 물음 — typing.Hashable 은 런타임에 무엇을 보나
   OnlyEq.__hash__                : None
   isinstance(OnlyEq(), Hashable) : False
   isinstance(Plain2(), Hashable) : True
   Hashable 이 보는 것            : __hash__ 하나 — Iterable 과 같은 오리 판정이다
(exit 0)
```

**왜 그런가**

* ★★★ **④에서 `Liar.area` 가 문자열인데 `isinstance` 가 참**이다.
  내가 쓴 갈고리가 `"area" in B.__dict__` 만 보기 때문이다 —
  ★ **`runtime_checkable` 과 정확히 같은 한계**다(4번 답).
  ★★ 즉 **ABC 쪽이든 `Protocol` 쪽이든, 구조로 판정하는 길은 전부 이름까지만 본다.**
* **①에서 `Circle` 이 상속도 등록도 안 했는데 참**이다. `__mro__` 에는 없다.
  ★ `register` 와 결과가 같은데 **선언조차 안 했다**는 것이 다르다.
* ★★ **②는 [32번](../32-container-protocol/2-summary.md)의 결론을 인용만 한 것**이다 —
  `__iter__` 만 가진 오리가 `Iterable` 에는 참이고 `Sized`·`Sequence` 에는 거짓이다.
  **한 메서드짜리 ABC 만 오리 판정을 한다.** 그쪽이 정본이므로 여기서 다시 재지 않았다.
* **③ — `NotImplemented` 를 주면 기본 판정으로 떨어진다.** 그래서 진짜 하위 `Sub` 가 그 경로로 참이 된다.
* ★★ **⑤가 [30번](../30-repr-eq-hash-contracts/2-summary.md)이 남겨 둔 물음의 런타임 쪽 답이다.**
  `OnlyEq.__hash__` 가 `None` 이고 `isinstance(OnlyEq(), Hashable)` 이 **거짓**,
  아무것도 안 한 `Plain2` 는 **참**이다.
  ★ 그쪽 동작 2의 「`__eq__` 만 정의하면 언어가 `__hash__` 를 꺼 버린다」가
  **`isinstance` 에 그대로 비친다.** 판정 구조는 `Iterable` 과 같은 오리 판정이다.
  ★ **정적 검사기 쪽 범위는 여전히 못 열었다** — 도구가 없다.

### 6. 다섯 대 영 — 낡은 객체는 양쪽 다 거짓인데 `for` 는 돌고, 안 채우면 한쪽만 막는다

**출력**

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
```text
===== python3 - <e35_choose.py =====
① 무엇이 공짜로 따라오나
   ABC      쪽 : ['__contains__', '__iter__', '__reversed__', 'index', 'count']
   Protocol 쪽 : 아무것도 없음
   a.index('c') -> 2
   p.index('c') -> AttributeError: 'ProtoSeq' object has no attribute 'index'
② 둘 다 isinstance 는 참이다 — 답이 같아 보이는 자리
   isinstance(a, Sequence) : True
   isinstance(p, SeqLike)  : True
   isinstance(p, Sequence) : False  <- ABC 쪽은 거짓이다
③ MRO 가 다르다 — ABC 는 진짜 조상이고 Protocol 은 아니다
   AbcSeq.__mro__   : ['AbcSeq', 'Sequence', 'Reversible', 'Collection', 'Sized', 'Iterable', 'Container', 'object']
   ProtoSeq.__mro__ : ['ProtoSeq', 'object']
④ 그런데 낡은 프로토콜은 양쪽 다 놓친다 — 32번이 실측한 자리다
   isinstance(Old(), Sequence) : False
   isinstance(Old(), SeqLike)  : False
   그런데 for 는 돈다          : ['a', 'b']
   ★ SeqLike 는 __len__ 이 없어 거짓이다 — 이름만 보기 때문이다
⑤ 어느 쪽이 「만들 때」 막나
   ABC      : TypeError: Can't instantiate abstract class AbcBroken without an implementation for abstract methods '__getitem__', '__len__'
   Protocol : ProtoBroken() 이 만들어졌다 -> ProtoBroken
(exit 0)
```

**왜 그런가**

* ★★★ **①이 가장 큰 차이다.** ABC 쪽은 `['__contains__', '__iter__', '__reversed__', 'index', 'count']`
  **다섯**이 따라오고, `Protocol` 쪽은 **`아무것도 없음`** 이다.
  `p.index('c')` 가 `AttributeError` 다.
  ★ **`Protocol` 은 요구만 하고 주지 않는다** — 이름 그대로 「약속」일 뿐이다.
  ★ [32번](../32-container-protocol/2-summary.md) 동작 7이 「둘만 쓰면 다섯이 따라온다」의 정본이고, 여기서는 **그 반대쪽**을 더한다.
* ★ **②에서 겉보기로는 구분이 안 된다** — 둘 다 `isinstance` 가 참이다.
  ★ 그런데 `isinstance(p, Sequence)` 는 **거짓**이다. `Sequence` 에는 `__subclasshook__` 이 없기 때문이다(5번 답의 ②).
* ★ **③ — MRO 의 길이가 곧 물려받은 것의 양**이다.
  `AbcSeq` 는 여덟 개짜리 줄이고 `ProtoSeq` 는 `['ProtoSeq', 'object']` 다.
* ★★ **④가 [32번](../32-container-protocol/2-summary.md)의 네 번째 창을 다시 건다.**
  `__getitem__` 만 가진 낡은 객체는 **양쪽 다 거짓인데 `for` 는 돈다**(`['a', 'b']`).
  ★ `SeqLike` 가 거짓인 이유는 **`__len__` 이 없어서**다 — 이름만 보기 때문이다.
  ★★ 즉 **「돈다」를 물으려면 여전히 `iter(x)` 를 걸어 봐야 한다.** `Protocol` 도 그 창이 아니다.
* ★★★ **⑤가 세 갈래를 한 블록에 요약한다.**
  같은 「안 채운 하위 클래스」인데 **ABC 는 `TypeError`, `Protocol` 은 그냥 만들어진다.**

### 7. 중간 단계 클래스를 가능하게 하려고

**왜 그런가**

* ★ **정의를 막으면 추상 클래스를 만들 수 없다.** `Storage` 자신이 그 예다 —
  추상 메서드가 둘 있는 클래스를 **정의는 해야** 하위가 그것을 물려받는다.
* ★★ **중간 단계가 그 설계의 값이다.** `Half` 처럼 **일부만 채운 클래스**를 두고
  그것을 다시 물려받아 나머지를 채우는 계층이 정상 설계다.
  ★ 정의 시점에 막으면 **`Half` 같은 층이 원리상 못 생긴다.**
* ★ 그리고 **클래스 쪽으로 부르는 것은 막을 이유가 없다** — `Storage.read(None, 'k')` 가 도는 것이 그것이다(1번 답의 ⑥).
* ★★ 대비로 읽으면 더 분명하다 — [34번](../34-inheritance-mro-super/2-summary.md)의 MRO 실패는 **정의 시점**에 터진다.
  ★ 그쪽은 **줄 자체를 못 세우므로** 클래스를 만들 방법이 아예 없고,
  이쪽은 **줄은 멀쩡한데 서류가 덜 찬 것**이라 나중에 채울 여지가 있다. **막는 시점이 그 차이를 따른다.**

### 8. 하는 일 둘, 안 하는 일 넷 — 그리고 만족을 묻는 창은 셋이다

**왜 그런가**

| `register()` 가 | 무엇 |
|---|---|
| **하는 일** | `isinstance` 를 참으로 만든다 · `issubclass` 를 참으로 만든다 |
| **안 하는 일** | `__mro__` 에 안 넣는다 · `__bases__` 를 안 바꾼다 · **믹스인을 안 준다** · **추상 메서드를 채웠는지 안 본다** |

* ★ 그래서 `register()` 는 「**명부에 이름을 올리는 것**」이고 **입주가 아니다.**
* ★★ **「누가 이 ABC 를 만족하나」를 묻는 창이 셋**이고 각각 다른 것을 놓친다.

| 창 | 보는 것 | 놓치는 것 |
|---|---|---|
| `isinstance(o, ABC)` | 상속 + `register` + `__subclasshook__` | **클래스 목록을 못 준다** — 객체 하나씩만 |
| `issubclass(C, ABC)` | 위와 같다 | 비메서드 멤버 프로토콜에서는 **아예 막힌다**(4번 답) |
| `ABC.__subclasses__()` | ★ **진짜 상속만** | `register` 한 것 · 갈고리로 걸린 것 |

* ★★★ **세 창 어디에도 「이 ABC 를 만족하는 것 전부」는 없다.**
  Go 20번이 「그 목록은 **원리상 못 만든다**」고 적은 것과 같은 자리다(10번 답).

### 9. 셋을 안 본다 — 그리고 서명을 보려면 `inspect` 로 직접 봐야 한다

**왜 그런가**

* ★ **`runtime_checkable` 이 안 보는 것 셋** —
  ① **인자의 개수와 이름**(`WrongSig` 가 참) ② **부를 수 있는 것인지**(`close = 42` 가 참)
  ③ **반환 타입과 몸통**.
  ★ 문서가 ①을 명시적으로 적고(*"not their type signatures"*), ②·③은 실측으로 드러났다.
* ★ **`__subclasshook__` 도 같은 한계**다. 5번 답의 ④가 그 증거다 —
  `Liar.area` 가 **문자열인데 참**이다.
  ★★ **ABC 쪽이든 `Protocol` 쪽이든, 구조로 판정하는 길은 전부 이름까지만 본다.**
* ★ **런타임에 서명까지 보려면 표준 장치가 없다.**
  `inspect.signature` 로 두 서명을 읽어 직접 대조하거나
  `typing.get_type_hints` 로 어노테이션을 읽어 견줘야 한다.
  ★ 이 배치에서 `inspect.signature` 를 실제로 쓰는 것은 [36번](../36-dataclasses/2-summary.md) 다 —
  생성된 `__init__` 의 서명을 손으로 안 세고 읽는다.

### 10. 「선언이 없다」만 같고, 「누가 강제하나」가 다르다

**왜 그런가**

| | Go 인터페이스 | Python `Protocol` |
|---|---|---|
| 구현 선언 | ★ **없다**(`implements` 없음) | ★ **없다**(상속 없어도 된다) |
| 판정 기준 | 메서드 집합(구조) | 메서드 **이름**(구조) |
| ★★★ 누가 강제하나 | **컴파일러** | **타입 검사기** — 있을 때만 |
| 안 지키면 | 쓰는 자리에서 **컴파일 에러** | ★ **아무 일도 안 난다** |
| 서명을 보나 | ★ **본다**(`have`/`want` 두 줄) | ★ `runtime_checkable` 은 **안 본다** |
| 만족 목록 | 없다(원리상 못 만든다) | 객체 하나씩은 물어볼 수 있다 |

* ★★★ **같은 것** — 둘 다 **구현하는 쪽이 인터페이스를 몰라도 된다.**
  그래서 의존 방향이 한쪽으로만 흐르고, **인터페이스를 쓰는 쪽에 둘 수 있다.**
* ★★★ **다른 것** — Go 는 **컴파일러가 서명까지 본다.**
  Go 20번의 실측이 그 증거다 — `*Typo does not implement Handler (missing method Name)` ·
  `*WrongSig does not implement Handler (wrong type for method Handle)` + `have`/`want`.
  파이썬의 `runtime_checkable` 은 **이름까지만** 본다(4번 답).
* ★★ **그런데 Go 도 「적은 것만」 본다.** Go 20번의 결론이 그것이다 —
  `var _ Iface = (*T)(nil)` 같은 **컴파일 타임 단언을 적지 않으면 아무 일도 안 일어난다**
  (그 편에서 `go vet` 이 0줄에 exit 0 이었다).
  ★★ 그 관용구에 해당하는 것이 파이썬에서는 「**타입 검사기를 CI 에 붙이는 것**」이다.
  둘 다 **「보게 만드는 자리를 사람이 만들어야」** 한다는 점에서 같다.
* ★ **이 문항은 던져서 재지 않았다** — Go 쪽 수치는 전부 Go 20번의 실측을 **인용**한 것이다.
  같은 배치에서 두 언어를 다시 재지 않는다.

### 11. 문서가 적은 것은 보장, 내부 이름은 구현 — 그리고 못 연 층은 「못 잰 것」으로 적는다

**왜 그런가**

| 사실 | 층 | 근거 |
|---|---|---|
| 추상 메서드를 안 채우면 인스턴스화가 막힌다 | **언어 보장** | `abc` 문서 |
| `register()` 가 **가상** 서브클래스를 만든다 | **언어 보장** | *"as a 'virtual subclass'"* |
| ★★ **`runtime_checkable` 이 서명을 안 본다** | **언어 보장** | *"not their type signatures"* — 문서가 직접 적는다 |
| 비메서드 멤버 프로토콜이 `issubclass` 를 지원 안 한다 | **언어 보장** | `typing` 문서 |
| 구조적 서브타이핑이 **정적 검사기를 위한 것**이다 | **언어 보장** | PEP 544 |
| `__protocol_attrs__` 라는 **이름** | **CPython 구현** | 3.12 에서 노출 |
| `Protocol` 하위의 `__abstractmethods__` 가 **비는 것** | **CPython 구현** | 문서가 이 경우를 안 적는다 |
| 안 채운 메서드가 **`None` 을 돌려주는 것** | **CPython 구현** | 몸통의 `...` 이 그대로 도는 것이다 |
| ABC 거부 문구의 **단수·복수** | **이 판의 관찰** | 3.12 에서 바뀐 꼴이다 |
| ★★★ **타입 검사기가 잡아 주는 범위** | ★ **못 연 층** | **도구가 이 머신에 없다** |

* ★★★ **못 연 층은 「안 돌려 본 것」이 아니라 「못 잰 것」(제3의 상태)으로 적는다.**
  ★ 그리고 **「없다」고 적기 전에 `PATH` 를 물어본 블록**을 남겼다(머리말의 첫 블록) —
  `shutil.which` 가 다섯 도구에 전부 `None` 을 답했다. **그 블록이 곧 판정의 근거다.**
* ★ **쪼개서 잰 조각** — 런타임 쪽은 **전부 실측**했고, 못 잰 것은 정적 쪽 하나뿐이다.
  그래서 이 문서의 어떤 문장도 「검사기가 이렇게 잡아 준다」로 적지 않았다.

### 12. 32 는 「언어가 채워 준다」, 35 는 「누가 강제하나」

**왜 그런가**

* ★ **경계 한 줄씩** —
  [32번](../32-container-protocol/2-summary.md)은 **컨테이너 프로토콜의 대체 경로와 `collections.abc` 믹스인**이 정본이다
  (둘만 쓰면 다섯이 따라오는 것 · `__subclasshook__` 이 한 메서드짜리에만 있는 것 ·
  `isinstance(Old(), Iterable)` 이 거짓인데 `for` 는 도는 것).
  **35번은 그 계약을 누가 언제 강제하나**가 정본이다(ABC 대 `Protocol` 대 `runtime_checkable`).
* ★ **「이터러블인가」는 `Protocol` 로도 못 검사한다**(6번 답의 ④).
  `SeqLike` 가 `__len__` 이 없다는 이유로 거짓인데 `for` 는 돈다.
  ★ **바른 검사는 여전히 `iter(x)` 를 걸고 `TypeError` 를 잡는 것**이고 정본은 [32번](../32-container-protocol/2-summary.md)이다.
  ★★ 즉 **이 주제가 그 문제를 해결해 주지 않는다** — 창이 하나 더 생겼을 뿐이다.
* ★ **[30번](../30-repr-eq-hash-contracts/2-summary.md)의 `typing.Hashable` 물음에는 절반 답했다**(5번 답의 ⑤).
  **런타임 쪽**은 나왔다 — `__hash__` 하나만 보는 오리 판정이라
  `__eq__` 만 정의한 클래스가 거짓이 된다.
  ★ **정적 검사기 쪽은 그쪽 문서가 「확인 못 했다」고 적은 그대로 남았다** — 이 머신에 도구가 없다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 판 + **타입 검사기 유무** | `python3 - <e35_version.py` | 2(캡처 + 재대조) | 다섯 도구 전부 `None` |
| ABC 가 막는 시점과 문구 | `python3 - <e35_abc.py` | 2 | 복수·단수로 갈림 · `class` 문은 통과 |
| `register()` 의 하는 일과 안 하는 일 | `python3 - <e35_register.py` | 2 | `__mro__` 에 없음 · 믹스인 없음 · 검사 없음 |
| `Protocol` 네 지점 | `python3 - <e35_protocol.py` | 2 | 막힌 곳 **1/5** · `Explicit()` 가 만들어짐 |
| `runtime_checkable` 이 보는 것 | `python3 - <e35_runtime.py` | 2 | `close = 42` 도 참 · **경고 0건** · `issubclass` 만 막힘 |
| `__subclasshook__` + `Hashable` | `python3 - <e35_hook.py` | 2 | 문자열 `area` 도 참 · `OnlyEq` 는 `Hashable` 거짓 |
| ABC 대 `Protocol` 격자 | `python3 - <e35_choose.py` | 2 | 다섯 대 영 · 낡은 객체는 양쪽 다 거짓 |

★★ **침묵을 수치로** — `Protocol` 에 **다섯 지점**을 물어 **막힌 곳은 하나**,
`runtime_checkable` 검사 중 **잡힌 경고는 0건**.
★ 「안 물어본 것」과 「물었는데 조용한 것」을 가르려고 **지점 수를 세어 적었다.**

**구현 의존 항목** — 판이 오르면 다시 돌려야 하는 것.

| 항목 | 왜 |
|---|---|
| ABC 거부 문구와 그 **단수·복수** | **3.12 에서 바뀐 꼴**이다 |
| `__protocol_attrs__` 라는 이름과 존재 | **3.12 에서 노출**됐다 |
| `Protocol` 하위의 `__abstractmethods__` 가 비는 것 | 문서가 이 경우를 안 적는다 |
| 안 채운 메서드가 `None` 을 주는 것 | 몸통의 `...` 이 그대로 도는 것이다 |
| `runtime_checkable` 검사 중 **경고 0건** | 판이 오르면 붙을 수 있다 |
| 예외 **문구** 전부 | 종류는 명세, 문구는 아니다 |
| ★★★ **이 머신에 검사기가 없는 것** | 머신의 상태다. **문서의 결론이 아니다** |

★ **안 흔들리는 칸** — `isinstance`·`issubclass` 의 **참·거짓**,
`__mro__` 의 **순서**와 그 안에 무엇이 **있나 없나**,
`sorted(__abstractmethods__)` 의 **내용**, 예외 **종류**, `(exit N)`.
★★ **이 주제가 못 연 창** — **타입 검사기.** 그래서 「검사기가 잡아 준다」는 문장이 한 줄도 없다.
