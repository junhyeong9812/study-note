# python/syntax/35-abc-and-protocol — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만.
> - [`abc`](https://docs.python.org/3.12/library/abc.html) — `ABC`·`abstractmethod`·`register`·`__subclasshook__`
> - [`abc.ABCMeta.register`](https://docs.python.org/3.12/library/abc.html#abc.ABCMeta.register) — *"Register subclass as a 'virtual subclass'"*
> - [`typing.Protocol`](https://docs.python.org/3.12/library/typing.html#typing.Protocol) · [`typing.runtime_checkable`](https://docs.python.org/3.12/library/typing.html#typing.runtime_checkable)
>   — *"runtime_checkable() will check only the presence of the required methods, not their type signatures"*
> - [PEP 544 — Protocols: Structural subtyping](https://peps.python.org/pep-0544/) — 구조적 서브타이핑의 정의
> - [`collections.abc`](https://docs.python.org/3.12/library/collections.abc.html) — 어느 추상 메서드를 주면 어느 믹스인이 따라오나
>
> **실행 검증** — 이 문서에 실린 출력은 전부 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.\
> ★ 던지는 형태를 하나로 고정했다 — `python3 - <파일` 로 던져 트레이스백이 `File "<stdin>", line N` 이 된다.\
> ★★★ **이 주제는 트레이스백을 한 블록도 싣지 않았다.** 던진 예외가 전부 `abc`·`typing` 을 지나
> **절대 경로가 박히기** 때문이다. 전부 `except` 로 받아 **타입과 메시지만** 찍었다
> ([28](../28-context-managers-and-with/2-summary.md)·[30](../30-repr-eq-hash-contracts/2-summary.md)이 같은 처방을 썼다).
> 그래서 이 문서에는 **줄 번호에 기대는 칸이 하나도 없다.**\
> **버전** — `abc` 는 **2.6**(PEP 3119), `Protocol`·`runtime_checkable` 은 **3.8**(PEP 544)부터다.
> 3.12 에서 `__protocol_attrs__` 가 노출되고 `isinstance` 구현이 빨라졌다.\
> ★★★ **구현 대 언어 보장 한 줄** — 이 주제의 축은 「**런타임이 강제하는 것 / 타입 검사기만 보는 것**」이다.
> **ABC 의 인스턴스화 거부는 런타임 강제**이고, **`Protocol` 의 구조 판정은 타입 검사기만 본다.**
> `runtime_checkable` 은 그 사이에 있는데, **보는 것이 메서드 이름뿐**이라 반쪽이다.\
> ★ **흔들리는 칸 / 안 흔들리는 칸** — 재대조에서 「고칠 것」과 「설계상 안 맞는 것」을 기계적으로 가르려고 미리 선언한다.
>
> | 흔들린다 | 안 흔들린다(근거로 써도 되는 칸) |
> |---|---|
> | `id()` 와 `0x…` 주소 — **이 주제는 한 번도 안 찍었다** | 예외 **종류** · `(exit N)` |
> | 판이 오르면 예외 **문구**(3.12 가 ABC 문구를 바꿨다) | `isinstance`·`issubclass` 의 **참·거짓** |
> | `__protocol_attrs__` 라는 **내부 이름**(3.12 에서 노출) | `__mro__` 의 **순서**와 그 안에 무엇이 **있나 없나** |
> | 타입 검사기가 설치돼 있는지 — **이 머신에는 없다**(첫 블록) | `__abstractmethods__` 의 **내용**(정렬해서 찍었다) |
>
> ★ **순서가 보장 안 되는 출력은 이 문서에 하나도 없다** — `__abstractmethods__` 는 `frozenset` 이라
> **전부 `sorted()` 로 찍었고**, `__protocol_attrs__` 도 같다.\
> **선행** — [34-inheritance-mro-super](../34-inheritance-mro-super/2-summary.md)(ABC 가 그 줄 위에 선다) ·
> [32-container-protocol](../32-container-protocol/2-summary.md)(★★★ **`collections.abc` 믹스인의 정본**) ·
> [29-classes-and-attribute-lookup](../29-classes-and-attribute-lookup/2-summary.md)(클래스 칸과 MRO).\
> **이 사슬** — [32](../32-container-protocol/2-summary.md) → [34](../34-inheritance-mro-super/2-summary.md) → 35.
> **32 가 「프로토콜을 반만 지켜도 언어가 채워 준다」였다면, 35 는 「그 계약을 누가 강제하나」다.**

## 한눈에 — 쉽게 말하면

**둘 다 「이런 모양이어야 한다」는 약속인데, 그 약속을 지키라고 **누가** 말하느냐가 다르다.**

* **ABC** — 관리사무소가 있다. 서류를 안 채우면 **입주 자체를 막는다.**
* **`Protocol`** — 관리사무소가 없다. **설계도만 있고** 아무도 안 본다. 입주는 그냥 된다.
* **`runtime_checkable` 붙인 `Protocol`** — 경비원이 하나 있는데 **문패만 본다.** 안에 뭐가 있는지는 안 본다.

```text
   "언제 막히나" 가 세 갈래다

   ① abc.ABC + @abstractmethod
        class 문        -> 통과한다
        Cls()           -> ★ TypeError 로 막힌다 (남은 이름을 전부 나열해 준다)

   ② typing.Protocol
        class 문        -> 통과한다
        Cls()           -> ★ 통과한다. 메서드 몸통의 ... 이 그냥 돌아 None 을 준다
        함수에 넘기기    -> 통과한다. 힌트는 실행을 안 바꾼다
        ★ 런타임에 막는 자리가 한 곳도 없다

   ③ @runtime_checkable Protocol
        isinstance(o, P) -> ★ 이름이 있으면 True. 서명도 타입도 안 본다
        o.close()        -> 거기서야 TypeError

   ★ ①은 "만들 때", ③은 "물어볼 때", ②는 "아무 때도" 막지 않는다
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 서류를 안 채우면 입주를 막는 관리사무소 | `abc.ABC` + `@abstractmethod` | `Cls()` 가 `TypeError` |
| 아직 안 채운 서류 목록 | `__abstractmethods__` | `sorted(Cls.__abstractmethods__)` |
| 입주 안 했는데 명부에 이름만 올리기 | `register()` | `isinstance` 는 참인데 `__mro__` 에 없다 |
| 문패만 보고 들여보내는 경비원 | `@runtime_checkable` | 서명이 달라도 `True` |
| 아무도 안 보는 설계도 | `Protocol`(런타임) | 안 지켜도 그냥 돈다 |
| 설계도를 실제로 읽는 사람 | 타입 검사기 | ★ **이 머신에는 없다**(첫 블록) |
| 관리사무소가 끼워 주는 기본 가구 | `collections.abc` 믹스인 | 안 썼는데 `index`·`count` 가 있다 |
| ★ **명부에만 올리면 가구가 안 따라온다** | `register()` 한 클래스 | `hasattr(o, 'twice')` 가 거짓 |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.\
「**`Protocol` 을 썼는데 왜 런타임에 안 막지**」와
「**`isinstance` 가 참이었는데 부르니까 터졌다**」가 그것이다.\
앞엣것은 **관리사무소가 없는 것**이고, 뒤엣것은 **문패만 본 것**이다.

> **추상 베이스 클래스(ABC, abstract base class)** — 「이것은 반드시 구현해라」를 강제하는 부모 클래스.\
> 예: 안 채우면 **인스턴스를 만들 때** `TypeError` 가 난다.

> **구조적 서브타이핑(structural subtyping)** — 상속을 선언하지 않아도 **모양이 맞으면** 그 타입으로 치는 방식.\
> 예: `typing.Protocol` 이 그 장치이고, **판정은 타입 검사기가 한다.**

> **가상 서브클래스(virtual subclass)** — `register()` 로 「그렇게 치자」고 선언만 한 관계.\
> 예: `isinstance` 는 참인데 **`__mro__` 에는 없고 믹스인도 안 따라온다.**

### ★★ 이 주제가 쓰는 창 / 부적용인 창

**본체는 「언제 막히나」 창이다.** 같은 계약을 세 가지 장치로 적고,
**class 문 → 인스턴스화 → `isinstance` → 실제 호출** 네 지점에 각각 던져 **어디서 막히는지**를 본다.

| 창 | 무엇을 말해 주나 | 못 보는 것 |
|---|---|---|
| ① ★★★ **네 지점에 던져 보기** | **어느 지점이 막나** | 타입 검사기가 뭐라 할지 |
| ② `__abstractmethods__` / `__protocol_attrs__` | 장치가 **무엇을 요구한다고 들고 있나** | 요구가 실제로 강제되는지 |
| ③ `__mro__` / `__bases__` | **진짜 상속인가 명부인가** | `isinstance` 의 답 |
| ④ ★ **`isinstance` 대 `issubclass`** | 둘이 **갈리는 자리** | 왜 갈리는지 |
| ★ **부적용인 창** — 타입 검사기 출력 | — | ★★★ **이 머신에 `mypy`·`pyright` 가 없다**(첫 블록이 `PATH` 를 직접 물었다) |

★★★ **⑤번 창(타입 검사기)이 「부적용」이 아니라 「못 잰 것」이라는 점**이 이 주제의 특이한 자리다.
[33번](../33-property-descriptor-slots/2-summary.md)의 속도 창은 **안 열기로 한 것**(부적용)이지만,
여기는 **열고 싶은데 도구가 없다**(제3의 상태).
★ 규칙대로 **「없다」고 적기 전에 `PATH` 를 물어본 블록**을 남겼다 — 그 블록이 곧 판정의 근거다.

★★ **제5의 상태 — 「같은 질문을 다른 창으로 물었다」.**
「`Protocol` 을 안 지키면 무슨 일이 나나」를 타입 검사기로 물을 수 없으니,
**「그냥 돌려 보는」 창**으로 바꿔 물었다(동작 3). 답은 「**아무 일도 안 난다**」이고,
★ **그 「아무 일도 안 난다」가 이 주제의 결론**이다 — 침묵이 근거인 주제다.
★ 바꾼 창이 못 보는 것도 적는다 — **타입 검사기가 무엇을 잡아 줄지는 이 문서가 모른다.**

★★ **침묵을 수치로 선언한다** — 이 문서는 `Protocol` 에 **네 지점**(class 문 · 인스턴스화 · 함수 전달 · 명시적 상속)을 물었고
**막힌 곳은 한 곳뿐**이다(`Protocol()` 자체를 인스턴스화하는 것). 나머지 셋은 전부 통과했다.

먼저 판을 박아 둔다. 이 문서의 모든 출력은 아래 판에서 나왔고, **타입 검사기 유무도 여기서 확인했다.**

```python
# e35_version.py
import shutil
import sys
import typing

print("version_info   =", sys.version_info)
print("implementation =", sys.implementation.name)
print("platform       =", sys.platform)
print("typing.Protocol 이 있나          :", hasattr(typing, "Protocol"))
print("typing.runtime_checkable 이 있나 :", hasattr(typing, "runtime_checkable"))
print("이 머신에 타입 검사기가 있나 — PATH 를 직접 물어본다")
for tool in ("mypy", "pyright", "pyre", "pytype", "basedpyright"):
    print("   %-13s :" % tool, shutil.which(tool))
```
```text
===== python3 - <e35_version.py =====
version_info   = sys.version_info(major=3, minor=12, micro=3, releaselevel='final', serial=0)
implementation = cpython
platform       = linux
typing.Protocol 이 있나          : True
typing.runtime_checkable 이 있나 : True
이 머신에 타입 검사기가 있나 — PATH 를 직접 물어본다
   mypy          : None
   pyright       : None
   pyre          : None
   pytype        : None
   basedpyright  : None
(exit 0)
```

★★★ **다섯 도구가 전부 `None` 이다.** 그래서 이 문서의 어떤 문장도 「검사기가 이렇게 잡아 준다」로 적지 않았다.
★ [`shutil.which`](https://docs.python.org/3.12/library/shutil.html#shutil.which) 는 `PATH` 를 실제로 훑으므로
「기억으로 없다고 적은 것」이 아니라 「**물어봐서 없는 것**」이다.

## 이 주제가 답하려는 질문

1. ★★★ **같은 계약을 세 장치로 적으면 각각 어디서 막히나** — class 문인가, 만들 때인가, 물어볼 때인가, 아무 때도 아닌가.
2. ★★ **`runtime_checkable` 이 보는 것은 정확히 무엇인가** — 이름인가 서명인가 타입인가.
3. **ABC 와 `Protocol` 중 무엇을 고르나** — 그리고 **무엇이 공짜로 따라오나.**

★ 첫째가 이 주제의 인출 목표다.
**「`Protocol` 은 런타임에 아무것도 안 막는다」를 실행으로 댈 수 있는 것**이 아는 것과 들은 것의 경계다.

## 동작 방식

> 이 절이 본문이다. 그림이 먼저 오고 문장이 그 그림을 읽어 준다.

### 1. ★★★ ABC — 「만들 때」 막는다

**언제 쓰나** — 내가 베이스를 소유하고 있고, **하위 클래스가 계약을 지키도록 강제**하고 싶을 때.

```text
   class Storage(abc.ABC):
       @abc.abstractmethod
       def read(self, key): ...
       @abc.abstractmethod
       def write(self, key, value): ...
       def copy(self, src, dst): ...      <- 추상이 아니다. 믹스인이다

   Storage 자신도, 반만 채운 Half 도 "클래스는 만들어진다"

        class 문     -> 통과
        Storage()    -> TypeError  'read', 'write'
        Half()       -> TypeError  'write'          <- 남은 것만 나열한다
        Mem()        -> 만들어진다. copy 가 공짜로 따라온다

   ★ 막는 자리가 "정의" 가 아니라 "생성" 이다
   ★ 그래서 추상 클래스도 상속·조회는 자유롭다
```

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

그림 해설 — 여섯 덩어리가 「무엇을 들고 있나」에서 「어디서 막나」까지 간다.

* ★ **①이 창 ②다.** `__abstractmethods__` 가 `['read', 'write']` 를 들고 있다.
  ★ 이것은 `frozenset` 이라 **순서가 보장되지 않는다** — 그래서 `sorted()` 로 찍었다.
* ★★★ **②·③이 이 절의 과녁이다.** 문구가 **남은 이름을 전부 나열한다** —
  `without an implementation for abstract methods 'read', 'write'`.
  ★ 하나만 남으면 **단수형으로 바뀐다** — `abstract method 'write'`.
  **무엇을 더 채워야 하는지 메시지가 정확히 알려 준다**는 것이 이 장치의 값이다.
* ★ **④에서 믹스인이 따라온다.** `copy` 는 `Mem.__dict__` 에 **없는데**(출력이 `False`) 돈다 —
  [34번](../34-inheritance-mro-super/2-summary.md)의 MRO 로 올라가 `Storage` 것을 쓴다.
  **추상 메서드만 강제하고 나머지는 물려준다**는 것이 ABC 의 두 번째 값이다.
* ★★ **⑤가 「막히는 자리」를 못 박는다.** `Half` 라는 **클래스는 만들어졌고** 타입이 `ABCMeta` 다.
  ★ `ABCMeta` 는 [34번](../34-inheritance-mro-super/2-summary.md)의 「더 들어가면」이 말한 **메타클래스의 대표 사례**다.
  **`class` 문은 통과했고 `Half()` 한 줄에서만 막힌다.**
* ★ **⑥ — 추상 메서드라고 몸통이 없는 것이 아니다.** `Storage.read(None, "k")` 가 `None` 을 돌려준다.
  **클래스 쪽으로 직접 부르는 것은 아무도 안 막는다.**

★★ 그래서 ABC 의 한 줄은 이렇다 — **「런타임이 강제한다. 단 강제하는 지점은 인스턴스를 만들 때 한 곳뿐이다.」**

**비용** — 강제를 얻는 값으로 **상속을 요구한다.** 남의 클래스는 못 고치므로 그때가 동작 2다.

### 2. ★ `register()` — `isinstance` 는 참인데 상속이 아니다

**언제 쓰나** — **남이 만든 클래스**를 내 ABC 의 하위로 치고 싶을 때. 내장 타입을 등록하는 것이 대표 사례다.

문서가 낱말을 고른다 — *"Register subclass as a 'virtual subclass' of this ABC."*
「**가상(virtual)**」이 그 뜻이다.

```text
   Quacker.register(Duck) 가 하는 일과 안 하는 일

   하는 일                            안 하는 일
   isinstance(Duck(), Quacker) -> True    Duck.__mro__ 에 Quacker 를 안 넣는다
   issubclass(Duck, Quacker)   -> True    Duck.__bases__ 를 안 바꾼다
                                          믹스인을 안 물려준다
                                          ★ 추상 메서드를 채웠는지 안 본다
                                          Quacker.__subclasses__() 에 안 넣는다

   ★ "그렇게 치자" 는 선언일 뿐이고 아무것도 검사하지 않는다
```

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

그림 해설 — 여섯 덩어리가 「참인데 아닌」 상태를 전수로 보인다.

* **②에서 `isinstance` 와 `issubclass` 가 둘 다 참**이 된다.
* ★★★ **③이 과녁이다.** `Duck.__mro__` 가 `['Duck', 'object']` 다 — **`Quacker` 가 없다.**
  `__bases__` 도 `['object']` 다.
  ★ **`isinstance` 가 참인데 MRO 에 없다** — [32번](../32-container-protocol/2-summary.md)이 「돈다와 그 타입이다는 다르다」를 봤다면,
  여기는 「**그 타입이다와 그것을 물려받았다는 다르다**」이다.
* ★ **④가 그 대가다.** MRO 에 없으므로 **믹스인이 안 따라온다**(`hasattr(Duck(), 'twice')` 가 거짓).
  ★ ⑥의 마지막 줄이 대비다 — **진짜 상속한 `RealSub` 는 `twice()` 를 받는다.**
* ★★ **⑤가 가장 조용한 자리다.** `Rock` 은 `quack` 이 **아예 없는데** 등록이 받아들여졌고
  `isinstance` 가 참이다. **`register` 는 아무것도 검사하지 않는다.**
  ★ ABC 가 동작 1에서 보여 준 강제가 **이 경로로는 통째로 우회된다.**
* ★ **⑥ — `__subclasses__()` 에는 진짜 상속만 나온다.** 등록한 것은 안 보인다.
  **「누가 이 ABC 를 만족하나」를 묻는 창이 둘로 갈린다.**

**비용** — 남의 클래스를 고치지 않고 관계를 만들 수 있다. 대가는 **검사가 전혀 없다는 것**과
**믹스인을 못 받는다는 것** 둘이다.

### 3. ★★★ `Protocol` — 런타임에 안 막는다

**언제 쓰나** — 상속을 요구하고 싶지 않을 때. 그리고 **「이 주제의 축」을 확인할 때.**

PEP 544 가 목적을 적는다 — 구조적 서브타이핑은 **정적 타입 검사기를 위한 것**이다.
그 말의 런타임 쪽 뜻이 이 절이다.

```text
   Protocol 에 네 지점을 물었다 — 막힌 곳이 한 곳뿐이다

   ① class Polite: (Greeter 를 상속 안 함)   -> 통과. welcome(Polite()) 가 돈다
   ② welcome(Silent())                       -> 통과. AttributeError 는 "속성이 없어서" 난다
   ③ welcome(42)                             -> 통과. 힌트는 실행을 안 바꾼다
   ④ Greeter()                               -> ★ 여기만 막힌다 (Protocol 자체의 인스턴스화)
   ⑤ class Explicit(Greeter): pass 후 Explicit()
                                              -> ★ 통과한다. 게다가 e.greet() 가 None 을 준다

   ★ ⑤가 결정적이다 — 명시적으로 물려받고 아무것도 구현 안 했는데 막지 않는다
     같은 자리에서 ABC 는 TypeError 로 막았다 (동작 1)
```

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

그림 해설 — 다섯 덩어리 중 **막힌 것은 ④ 하나**다.

* ★★ **①이 구조적 서브타이핑의 값이다.** `Polite` 는 `Greeter` 를 **모른다**(`__mro__` 에 없다).
  그런데 힌트에 `Greeter` 라고 적은 함수에 넣으니 그냥 돈다 —
  **구현하는 쪽이 아무것도 import 하지 않아도 된다.**
* ★★ **②의 예외가 무엇인지가 중요하다.** `AttributeError: 'Silent' object has no attribute 'greet'` 다.
  ★ **「프로토콜 위반」이라는 예외가 아니다.** 그냥 **없는 속성을 읽은 것**이다.
  런타임은 `Greeter` 라는 이름을 **한 번도 안 봤다.**
* ★ **③이 그것을 못 박는다.** 힌트를 `Greeter` 로 적어 놓고 **정수 `42`** 를 넣어도 통과한다.
  ★ 「힌트는 실행을 안 바꾼다」는 목록의 **40번 주제** 가 정본이고, 여기서는 그 결과만 쓴다.
* **④ — `Protocols cannot be instantiated`.** 이것이 **유일하게 막히는 자리**다.
  ★ 그런데 이 자리는 **계약 위반과 아무 상관이 없다** — 프로토콜 객체 자체를 만들려 한 것뿐이다.
* ★★★ **⑤가 이 절의 과녁이다.** `class Explicit(Greeter): pass` 로 **명시적으로 물려받고
  아무것도 구현하지 않았는데** 인스턴스가 만들어진다.
  `__abstractmethods__` 가 **빈 `frozenset`** 이다.
  ★ 그리고 `e.greet("세계")` 가 **예외가 아니라 `None`** 을 준다 — **몸통의 `...` 이 그대로 돌았다.**
  ★★ 같은 자리에서 **ABC 는 `TypeError` 로 막았다**(동작 1의 ②).
  **세 갈래 중 가운데가 여기다.**

★★★ 그래서 판정 한 줄 — **「`Protocol` 은 런타임에 아무것도 강제하지 않는다.
강제하는 것은 타입 검사기이고, 이 머신에는 그것이 없다.」**

**비용** — 상속을 안 요구하는 값으로 **강제를 통째로 포기**한다.
그 대신 **`collections.abc` 가 주던 믹스인도 안 준다**(동작 6).

### 4. ★★ `runtime_checkable` — 이름만 본다

**언제 쓰나** — `Protocol` 로 `isinstance` 를 쓰고 싶을 때. **그리고 그것이 무엇을 못 보는지 알아야 할 때.**

문서가 한계를 직접 적는다 — *"`runtime_checkable()` will check only the presence of the required methods,
not their type signatures."*

```text
   @runtime_checkable class Closer(Protocol): def close(self) -> None: ...

   무엇을 보나                          무엇을 안 보나
   close 라는 이름이 있나                ★ 인자가 몇 개인가
                                        ★ 부를 수 있는 것인가 (정수여도 된다)
                                        ★ 반환 타입
                                        ★ 몸통에 무엇이 있나

   Good        close(self)        -> True   부른다 -> 된다
   WrongSig    close(self,a,b,c)  -> True   부른다 -> TypeError
   NotCallable close = 42         -> True   부른다 -> TypeError 'int' object is not callable
   Missing     (없음)              -> False

   ★ 셋이 True 인데 둘이 터진다. isinstance 가 통과한 뒤에 터진다
```

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

그림 해설 — 다섯 덩어리가 「반쪽짜리 경비원」을 전수로 보인다.

* ★★ **①이 과녁이다.** `WrongSig` 와 `NotCallable` **둘 다 `True`** 다.
  인자 개수가 달라도, 아예 **정수여도** 통과한다.
  ★ **경고도 없다** — `warnings.catch_warnings(record=True)` 로 잡아 보니 「**없음**」이다.
  ★ 이 문서가 경고를 **stderr 로 새게 두지 않고 잡아서 stdout 에 찍은 이유**가 그것이다.
  한 블록에 두 스트림이 섞이면 **순서가 어디로 받느냐에 달린다.**
* ★★★ **②가 대가를 보인다.** `isinstance` 를 통과한 둘이 **호출에서 터진다.**
  `WrongSig.close() missing 3 required positional arguments` 와 `'int' object is not callable` 이다.
  ★ **막는 지점이 계약에서 멀다** — 검사한 자리와 터지는 자리가 다르다.
* **③ — `runtime_checkable` 을 안 붙이면 `isinstance` 자체가 막힌다.**
  `Instance and class checks can only be used with @runtime_checkable protocols` 다.
  ★ **기본값**이 「**못 물어본다**」라는 것이 PEP 544 의 태도다.
* ★★★ **④가 이 절에서 가장 얄궂다.** 메서드 아닌 멤버(`name: str`)가 있는 프로토콜은
  **`isinstance` 는 되는데 `issubclass` 가 막힌다** —
  `Protocols with non-method members don't support issubclass()`.
  ★ **이유가 논리적이다** — 인스턴스는 **그 속성을 실제로 들고 있는지** 물어볼 수 있지만,
  클래스만 보고는 **인스턴스가 그 속성을 갖게 될지** 알 수 없다.
  ★ **둘이 갈리는 드문 자리**이므로 창 ④가 따로 필요하다.
* ★ **⑤ — 프로토콜이 무엇을 보는지 자기가 들고 있다.** `__protocol_attrs__` 가 `['close']`·`['name']` 이다.
  ★ 이 이름은 **3.12 에서 노출된 내부 이름**이라 흔들리는 칸이다.

**비용** — `isinstance` 를 쓸 수 있게 되는 값으로 **거짓 안심**을 산다.
★ 「`isinstance` 가 참이니 부를 수 있다」가 **이 주제에서 가장 비싼 오해**다.

### 5. ★ `__subclasshook__` — 갈고리를 직접 단다

**언제 쓰나** — 「이 메서드만 있으면 내 ABC 로 친다」를 **등록 없이** 하고 싶을 때.
그리고 [32번](../32-container-protocol/2-summary.md)의 `Iterable` 이 어떻게 그렇게 되는지 볼 때.

```text
   __subclasshook__(cls, C) 가 돌려줄 수 있는 셋

   True           -> 그 클래스는 하위다
   False          -> 아니다
   NotImplemented -> ★ 판단을 안 한다. 기본 판정(진짜 상속 + register)으로 떨어진다

   ★ cls is HasArea 를 확인하는 관용구가 필요한 이유
     그 확인이 없으면 "HasArea 를 물려받은 하위 ABC" 에도 같은 갈고리가 걸린다
```

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

그림 해설.

* ★ **①에서 `Circle` 이 상속도 등록도 안 했는데 `isinstance` 가 참**이다. `__mro__` 에는 없다.
  ★ 동작 2의 `register` 와 겉보기 결과가 같은데 **선언조차 안 했다는 것**이 다르다.
* ★★ **②가 [32번](../32-container-protocol/2-summary.md)을 인용만 한다.**
  `__iter__` 만 가진 오리가 `Iterable` 에는 참이고 `Sized`·`Sequence` 에는 거짓이다 —
  **한 메서드짜리 ABC 만 오리 판정을 한다.**
  ★ **그쪽이 정본이므로 여기서는 다시 재지 않았다.** 이 블록은 그 결론이 여전히 성립하는지만 건드린다.
* **③ — `NotImplemented` 를 돌려주면 기본 판정으로 떨어진다.**
  그래서 진짜 하위 클래스 `Sub` 는 그 경로로 참이 된다.
* ★★★ **④가 이 절의 과녁이다.** `Liar.area` 가 **문자열인데도 `isinstance` 가 참**이다.
  ★ **갈고리는 「이름이 있나」만 본다** — 동작 4의 `runtime_checkable` 과 **정확히 같은 한계**다.
  ★★ 즉 **ABC 쪽이든 `Protocol` 쪽이든, 「구조로 판정하는 길」은 전부 이름까지만 본다.**
* ★★ **⑤가 [30번](../30-repr-eq-hash-contracts/2-summary.md)이 남겨 둔 물음에 런타임 쪽 답을 준다.**
  `Hashable` 도 같은 오리 판정이고 **`__hash__` 하나만** 본다.
  ★ `__eq__` 만 정의해 `__hash__` 가 `None` 이 된 클래스는 **거짓**이 되고,
  아무것도 안 한 클래스는 **참**이다 — 그쪽 동작 2의 결론이 `isinstance` 에 그대로 비친다.
  ★ 다만 **정적 검사기 쪽 범위는 여전히 못 열었다**(도구 없음).

**비용** — 등록을 안 해도 되는 값으로 **검사의 정확도를 포기**한다.
★ 그리고 `__subclasshook__` 은 **하위 ABC 에도 걸리므로** `cls is HasArea` 확인이 필요하다.

### 6. ★★ 무엇을 고르나 — 공짜로 따라오는 것이 갈린다

**언제 쓰나** — 설계할 때. 이 절이 「언제 쓰고 언제 안 쓰나」의 근거다.

```text
   같은 "시퀀스 같은 것" 을 두 방법으로 적으면

   collections.abc.Sequence 상속        @runtime_checkable class SeqLike(Protocol)

   __len__ · __getitem__ 만 쓴다        __len__ · __getitem__ 만 쓴다
        |                                    |
   ★ 다섯이 따라온다                    ★ 아무것도 안 따라온다
     __contains__ __iter__                 index 를 부르면 AttributeError
     __reversed__ index count

   MRO : AbcSeq Sequence Reversible ...  MRO : ProtoSeq object
   안 채우면 : 인스턴스화 거부            안 채우면 : ★ 그냥 만들어진다
```

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

그림 해설 — 다섯 덩어리가 두 길의 대가를 나란히 놓는다.

* ★★★ **①이 가장 큰 차이다.** ABC 쪽은 **다섯이 따라오고** `Protocol` 쪽은 **아무것도 없다.**
  `p.index('c')` 가 `AttributeError` 다.
  ★ **`Protocol` 은 요구만 하고 주지 않는다** — 이름 그대로 「약속」일 뿐이다.
  ★ [32번](../32-container-protocol/2-summary.md) 동작 7이 「둘만 쓰면 다섯이 따라온다」의 정본이고, 여기서는 **그 반대쪽**을 더한다.
* ★ **②에서 둘 다 `isinstance` 가 참**이다 — 겉보기로는 구분이 안 된다.
  ★ 그런데 `isinstance(p, Sequence)` 는 **거짓**이다. `Sequence` 에는 `__subclasshook__` 이 없기 때문이다(동작 5의 ②).
* ★ **③ — MRO 가 다르다.** ABC 쪽은 여덟 개짜리 줄이고 `Protocol` 쪽은 `['ProtoSeq', 'object']` 다.
  **그 줄의 길이가 곧 물려받은 것의 양**이다([34번](../34-inheritance-mro-super/2-summary.md)의 줄).
* ★★ **④가 [32번](../32-container-protocol/2-summary.md)의 네 번째 창을 다시 건다.**
  `__getitem__` 만 가진 낡은 객체는 **양쪽 다 거짓인데 `for` 는 돈다.**
  ★ `SeqLike` 가 거짓인 이유는 **`__len__` 이 없어서**다 — 이름만 보기 때문이다.
  ★★ 즉 **「돈다」를 물으려면 여전히 `iter(x)` 를 걸어 봐야 한다.** `Protocol` 도 그 창이 아니다.
* ★★★ **⑤가 세 갈래를 한 블록에 요약한다.**
  같은 「안 채운 하위 클래스」인데 **ABC 는 `TypeError`, `Protocol` 은 그냥 만들어진다.**

**비용** — ABC 는 **강제 + 믹스인**을 주고 **상속을 요구**한다.
`Protocol` 은 **상속을 안 요구**하고 **아무것도 안 준다.** 고르는 축이 그 하나다.

### 7. ★★★ Go 의 암묵 구현과 견주면 — 같은 「구조」인데 강제하는 쪽이 다르다

**언제 쓰나** — 「`Protocol` 이 Go 인터페이스 같은 것 아닌가」가 나올 때. **가장 가까운 대비**다.

Go 갈래 목록([`go/syntax/README.md`](../../../go/syntax/README.md))의 **20번** 이 그 정본이고,
결론이 이 주제와 **절반만 같다.**

```text
                     Go 의 인터페이스            Python 의 Protocol

   구현 선언          ★ 없다 (implements 없음)    ★ 없다 (상속 없어도 된다)
   판정 기준          메서드 집합 (구조)          메서드 이름 (구조)
   누가 강제하나      ★★★ 컴파일러               ★★★ 타입 검사기 (있을 때만)
   안 지키면          쓰는 자리에서 컴파일 에러     ★ 아무 일도 안 난다
   서명을 보나        ★ 본다 (have/want 를 찍는다) ★ runtime_checkable 은 안 본다
   만족 목록을 주나   ★ 없다 (원리상 못 만든다)     isinstance 로 물어볼 수는 있다

   ★ 둘 다 "암묵" 인데, Go 는 빌드가 막고 파이썬은 아무도 안 막는다
```

* ★★★ **같은 것** — 둘 다 **구현 선언이 없다.** `implements` 도 상속도 안 적는다.
  그래서 둘 다 **구현하는 쪽이 인터페이스를 몰라도 된다** — 패키지·모듈 의존 방향이 한쪽으로만 흐른다.
* ★★★ **다른 것** — Go 는 **컴파일러가 강제한다.**
  Go 20번이 실측한 에러가 그 증거다 — `*Typo does not implement Handler (missing method Name)` 와
  `*WrongSig does not implement Handler (wrong type for method Handle)` 에 `have`/`want` 두 줄이 붙는다.
  ★ **Go 는 서명까지 본다.** 파이썬의 `runtime_checkable` 은 **이름까지만** 본다(동작 4).
* ★★ **그런데 Go 도 「적은 것만」 본다.** Go 20번의 결론이 그것이다 —
  `var _ Iface = (*T)(nil)` 같은 **컴파일 타임 단언을 적지 않으면 아무 일도 안 일어난다.**
  ★ 즉 「**선언 자리를 인공으로 만드는 관용구**」가 필요하다는 점에서 Go 도 절반은 파이썬 쪽이다.
  ★ 파이썬에서 그 자리에 해당하는 것이 **타입 검사기를 CI 에 붙이는 것**이다.
* ★ **만족 목록** — Go 20번은 「그 목록을 **원리상 못 만든다**」고 적었다.
  파이썬은 `runtime_checkable` 을 붙이면 **물어볼 수는 있다**(한 객체씩).
  ★ 다만 **「이 프로토콜을 만족하는 클래스 전부」를 세는 길은 파이썬에도 없다.**
* ★ **이 절은 던져서 재지 않았다** — Go 쪽 수치는 전부 Go 20번의 실측을 **인용한 것**이고,
  파이썬 쪽은 동작 3·4의 실측이다. **같은 배치에서 두 언어를 다시 재지 않는다**는 규칙을 지켰다.

★ 다른 대비 둘도 같은 축에 선다.
TS 갈래 목록([`ts/syntax/README.md`](../../../ts/syntax/README.md))의 **05번** 이 「구조적 타이핑은 **모든 타입의 기본값**이고
**방출된 JS 에는 아무것도 안 남는다**」를 실측했다 — 파이썬의 `Protocol` 은 **골라서 쓰는 것**이라는 점만 다르다.
자바 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **11번** 은 반대쪽 끝이다 —
**`implements` 를 적으므로 IDE 가 구현체 목록을 보여 줄 수 있다.**

## 문법 — 형태와 규칙

**형태 — 세 장치를 나란히**

```text
import abc
from typing import Protocol, runtime_checkable

class Storage(abc.ABC):                 # ① 런타임이 강제한다
    @abc.abstractmethod
    def read(self, key): ...            #   -> 안 채우면 Cls() 가 TypeError
    def copy(self, s, d): ...           #   -> 믹스인은 그냥 물려준다

Storage.register(남의클래스)            # ② "그렇게 치자" — 아무것도 검사 안 한다

class Greeter(Protocol):                # ③ 타입 검사기만 본다
    def greet(self, name: str) -> str: ...

@runtime_checkable                      # ④ isinstance 를 열되 이름만 본다
class Closer(Protocol):
    def close(self) -> None: ...

class HasArea(abc.ABC):                 # ⑤ 갈고리를 직접 단다
    @classmethod
    def __subclasshook__(cls, C):
        if cls is HasArea:              #   ★ 이 확인이 없으면 하위 ABC 에도 걸린다
            return any("area" in B.__dict__ for B in C.__mro__)
        return NotImplemented
```

```text
진단 — 무엇을 요구하고 무엇을 강제하나

sorted(Cls.__abstractmethods__)   아직 안 채운 추상 메서드 (frozenset 이라 sorted 필수)
sorted(P.__protocol_attrs__)      프로토콜이 보는 이름들 (3.12 에서 노출)
Cls.__mro__                       진짜 상속인가 — register 한 것은 여기 없다
Cls.__bases__                     글자 그대로 적은 부모
type(Cls).__name__                ABCMeta 인가
Cls.__subclasses__()              ★ 진짜 상속만 나온다. register 한 것은 안 보인다
isinstance(o, X) / issubclass(C,X) ★ 비메서드 멤버 프로토콜에서 둘이 갈린다
shutil.which("mypy")              ★ 검사기가 있나 — "없다" 고 적기 전에 물어본다
```

규칙 열둘.

1. ★★★ **ABC 는 「인스턴스를 만들 때」 막는다.** `class` 문은 통과한다.
2. ★ **거부 메시지가 남은 이름을 전부 나열한다.** 하나면 단수형으로 바뀐다.
3. **추상 메서드가 아닌 것은 믹스인으로 그냥 물려받는다.**
4. ★ **`register()` 는 아무것도 검사하지 않는다.** 추상 메서드를 안 채워도 받아 준다.
5. ★★ **`register()` 는 `__mro__` 를 안 바꾼다.** 그래서 **믹스인이 안 따라온다.**
6. ★ **`__subclasses__()` 에는 진짜 상속만** 나온다.
7. ★★★ **`Protocol` 은 런타임에 아무것도 강제하지 않는다.** 명시적으로 물려받고 안 채워도 만들어진다.
8. ★ **막히는 유일한 자리는 `Protocol` 자체를 인스턴스화하는 것**이고, 그것은 계약과 무관하다.
9. ★★ **`runtime_checkable` 은 메서드 이름만 본다.** 서명도, 부를 수 있는지도 안 본다.
10. ★ **`runtime_checkable` 없이는 `isinstance` 자체가 `TypeError`** 다.
11. ★★ **비메서드 멤버가 있는 프로토콜은 `isinstance` 는 되고 `issubclass` 는 막힌다.**
12. ★ **`__subclasshook__` 도 이름만 본다.** 값이 문자열이어도 참이 된다.

**금지 사례 — 문법은 맞는데 조용히 어긋나는 것들**

```text
class Impl(SomeProtocol):
    pass                            # ① 아무것도 구현 안 했는데 만들어진다. 메서드가 None 을 준다

@runtime_checkable
class Closer(Protocol):
    def close(self) -> None: ...
if isinstance(o, Closer):
    o.close()                       # ② isinstance 는 통과하고 호출에서 TypeError 가 난다

MyABC.register(SomeoneElse)         # ③ 추상 메서드를 안 채워도 통과한다. 아무도 안 본다

class Bad(abc.ABC):
    @classmethod
    def __subclasshook__(cls, C):
        return any(...)             # ④ cls is Bad 확인이 없다 — 하위 ABC 에도 같은 갈고리가 걸린다

class P(Protocol):
    name: str
issubclass(X, P)                    # ⑤ TypeError — 비메서드 멤버는 issubclass 를 못 쓴다

def f(g: Greeter): ...
f(42)                               # ⑥ 조용하다. 힌트는 실행을 안 바꾼다
```

★ ①·③·⑥이 **아무 말이 없다.** ②는 **늦게** 터지고 ④는 **엉뚱한 곳에서** 터진다.

## 어디서 틀리나

### (1) ★★★ 「`Protocol` 을 쓰면 런타임에 막아 준다」로 안다

**아무것도 안 막는다.** 명시적으로 물려받고 하나도 구현 안 해도 **인스턴스가 만들어지고**
메서드를 부르면 **예외가 아니라 `None`** 이 나온다(동작 3의 ⑤).\
★ 막는 것은 **타입 검사기**이고, **이 머신에는 그것이 없다**(첫 블록).

### (2) ★★ 「`isinstance` 가 참이니 부를 수 있다」로 안다

**이름만 봤다.** 인자 개수가 달라도, 그 이름이 **정수여도** 참이다(동작 4의 ①).\
★ 그 뒤 호출에서 `TypeError` 가 난다 — **검사한 자리와 터지는 자리가 다르다.**

### (3) ★★ ABC 가 「클래스를 정의할 때」 막는다고 믿는다

「**만들 때**」다. 반만 채운 클래스도 **정의는 된다**(동작 1의 ⑤).\
★ 그래서 추상 클래스를 **중간 단계로 상속해 가는 것**이 정상 설계다.

### (4) ★ `register()` 가 검사를 해 준다고 믿는다

**아무것도 안 한다.** 추상 메서드가 하나도 없는 클래스도 등록된다(동작 2의 ⑤).\
★ 이름 그대로 **「가상(virtual)」 서브클래스**다.

### (5) ★★ `register()` 한 클래스가 믹스인을 받는다고 믿는다

**안 받는다.** `__mro__` 에 안 들어가므로([34번](../34-inheritance-mro-super/2-summary.md)의 줄) 물려받을 길이 없다.

### (6) ★ `__subclasses__()` 로 「누가 만족하나」를 센다

**진짜 상속만 나온다.** 등록한 것도 갈고리로 걸린 것도 안 보인다.

### (7) ★★ 비메서드 멤버가 있는 프로토콜에 `issubclass` 를 쓴다

**`TypeError`** 다. `isinstance` 는 되는데 `issubclass` 가 막힌다(동작 4의 ④).\
★ 이유가 논리적이다 — 클래스만 보고는 **인스턴스가 그 속성을 갖게 될지 모른다.**

### (8) ★ `runtime_checkable` 을 안 붙이고 `isinstance` 를 쓴다

**`isinstance` 자체가 `TypeError`** 다.
`Instance and class checks can only be used with @runtime_checkable protocols`.

### (9) ★ `__subclasshook__` 에 `cls is X` 확인을 안 쓴다

**하위 ABC 에도 같은 갈고리가 걸린다.** 하위가 더 많은 것을 요구해도 부모의 판정이 이긴다.

### (10) ★★ 「구조로 판정하니 정확하겠지」로 믿는다

**ABC 쪽이든 `Protocol` 쪽이든 전부 이름까지만 본다.**
`__subclasshook__` 도 문자열 `area` 를 참으로 답했다(동작 5의 ④).

### (11) ★ `Protocol` 이 `collections.abc` 처럼 믹스인을 줄 거라고 믿는다

**아무것도 안 준다.** `index`·`count` 를 부르면 `AttributeError` 다(동작 6의 ①).\
★ **요구만 하고 주지 않는다.**

### (12) ★ 「이터러블인가」를 `Protocol` 로 검사한다

**여전히 놓친다.** `__getitem__` 만 가진 객체는 `SeqLike` 에도 거짓인데 `for` 는 돈다(동작 6의 ④).\
★ 바른 검사는 **`iter(x)` 를 걸고 `TypeError` 를 잡는 것**이고 정본은 [32번](../32-container-protocol/2-summary.md)이다.

### (13) ★★ Go 의 암묵 구현과 같은 것으로 안다

**「구현 선언이 없다」만 같고 「누가 강제하나」가 다르다.**
Go 는 **컴파일러가 서명까지 본다.** 파이썬은 **아무도 안 보거나 이름만 본다**(동작 7).

## 구현 세부사항 대 언어 보장

세 층으로 가른다. ★★★ **이 주제는 층이 하나 더 있다** — 「**타입 검사기가 보는 것**」이다.
그것은 언어 보장도 CPython 구현도 아니고 **PEP 와 각 검사기가 정하는 층**이며,
**이 배치에서는 그 층을 못 열었다**(도구 없음).

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **언어 보장** | 라이브러리 레퍼런스가 정한 것 | 문서 문장을 열어서 인용 |
| **CPython 구현** | 이 구현이 그렇게 하는 것 | 실행 · 내부 이름 |
| **이 판(3.12.3)의 관찰** | 이 판에서 그랬을 뿐 | 예외 문구 |
| ★ **타입 검사기 층** | PEP 544 가 정하고 검사기가 구현하는 것 | ★★★ **못 열었다 — 도구가 없다**(첫 블록) |

### 언어 보장

| 사실 | 근거 |
|---|---|
| 추상 메서드를 안 채운 ABC 하위 클래스는 **인스턴스화가 막힌다** | `abc` — 추상 메서드 규칙 |
| `register()` 는 **가상 서브클래스**를 만든다(상속이 아니다) | `ABCMeta.register` — *"as a 'virtual subclass'"* |
| `__subclasshook__` 이 `NotImplemented` 를 주면 **기본 판정**으로 떨어진다 | `abc.ABCMeta.__subclasshook__` |
| ★★ `runtime_checkable` 은 **메서드의 존재만** 보고 **서명은 안 본다** | `typing.runtime_checkable` — *"only the presence of the required methods, not their type signatures"* |
| `runtime_checkable` 없이는 프로토콜에 `isinstance` 를 못 쓴다 | `typing.Protocol` |
| 비메서드 멤버가 있는 프로토콜은 `issubclass` 를 **지원하지 않는다** | `typing.runtime_checkable` |
| ★★★ 구조적 서브타이핑은 **정적 타입 검사기를 위한 것**이다 | PEP 544 |
| `collections.abc` 의 ABC 가 어느 믹스인을 주는지 | `collections.abc` 표 ([32번](../32-container-protocol/2-summary.md)이 정본) |

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| `__protocol_attrs__` 라는 이름과 그 내용 | 실행 — **3.12 에서 노출된 내부 이름** |
| `Protocols cannot be instantiated` 라는 **문구** | 실행 |
| `Protocol` 을 명시적으로 물려받은 클래스의 `__abstractmethods__` 가 **비는 것** | 실행 — 문서가 이 경우를 안 적는다 |
| 안 채운 메서드가 **`None` 을 돌려주는 것** | 실행 — 몸통의 `...` 이 그대로 도는 것이다 |
| `type(Half).__name__` 이 `ABCMeta` 인 것 | 실행 |
| 예외 **문구** 전부 | 실행 |

### 이 판(3.12.3)의 관찰

| 관찰 | 어디가 흔들리나 |
|---|---|
| ABC 거부 문구가 `without an implementation for abstract method(s) …` 인 것 | **3.12 에서 바뀐 꼴**이다([32번](../32-container-protocol/2-summary.md)도 같은 관찰) |
| 그 문구가 **단수·복수로 갈리는 것** | 문구의 일이다 |
| `runtime_checkable` 검사 중 **경고가 0건**인 것 | 잡아서 확인했다. 판이 오르면 붙을 수 있다 |
| `__protocol_attrs__` 가 **존재하는 것** | 3.12 에서 생겼다. 그 전 판에는 없다 |
| ★★★ **타입 검사기가 이 머신에 없는 것** | 머신의 상태다. **문서의 결론이 아니다** |

### 그래서 이렇게 적으면 틀린다

* ✗ 「`Protocol` 은 런타임에 계약을 강제한다」\
  ○ ★★★ **아무것도 안 막는다.** 명시적으로 물려받고 안 채워도 만들어진다.
* ✗ 「`Protocol` 을 물려받으면 ABC 처럼 추상 메서드가 된다」\
  ○ `__abstractmethods__` 가 **빈다.** 메서드를 부르면 `None` 이 나온다.
* ✗ 「`isinstance` 가 참이면 그 메서드를 부를 수 있다」\
  ○ **이름만 봤다.** 정수여도 참이다.
* ✗ 「`runtime_checkable` 은 서명도 본다」\
  ○ **문서가 명시적으로 아니라고 적는다.**
* ✗ 「`register()` 는 계약을 확인한다」\
  ○ **아무것도 안 한다.** 메서드가 하나도 없어도 된다.
* ✗ 「`register()` 하면 믹스인도 따라온다」\
  ○ `__mro__` 에 안 들어가므로 **안 따라온다.**
* ✗ 「ABC 는 클래스를 정의할 때 막는다」\
  ○ **만들 때**다. 반만 채운 클래스도 정의는 된다.
* ✗ 「`issubclass` 는 `isinstance` 의 클래스 판이니 늘 같이 된다」\
  ○ **비메서드 멤버 프로토콜에서 갈린다.** 앞엣것만 된다.
* ✗ 「`Protocol` 이 `collections.abc` 를 대체한다」\
  ○ **믹스인을 안 준다.** 대체가 아니라 **다른 축의 물건**이다.
* ✗ 「Go 의 암묵 구현과 같은 것이다」\
  ○ **「선언이 없다」만 같다.** Go 는 **컴파일러가 서명까지** 본다.

**판정 기준 한 줄**: **「누가 강제하나」를 먼저 묻는다 —
ABC 는 런타임이 **만들 때**, `runtime_checkable` 은 런타임이 **이름까지만**,
`Protocol` 은 **타입 검사기만**. 셋은 같은 물건의 세 얼굴이 아니라 **다른 강제력**이다.**

## 언제 쓰고 언제 안 쓰나

| 상황 | 판정 |
|---|---|
| 내가 베이스를 소유하고 계약을 강제하고 싶다 | **`abc.ABC` + `@abstractmethod`** — 런타임이 막아 준다 |
| 공통 구현(믹스인)을 같이 주고 싶다 | **ABC** — `Protocol` 은 아무것도 안 준다 |
| 남의 클래스를 내 타입으로 치고 싶다 | **`register()`** — ★ 검사는 **전혀** 없다는 것을 안다 |
| 구현하는 쪽이 내 모듈을 import 하면 안 된다 | **`Protocol`** — 상속이 필요 없다 |
| 덕 타이핑 코드에 타입을 붙이고 싶다 | **`Protocol`** — ★ **CI 에 타입 검사기를 붙여야 뜻이 있다** |
| 런타임에 `isinstance` 로 골라야 한다 | `@runtime_checkable` — ★ **이름까지만 본다는 것을 안다** |
| 서명까지 맞는지 런타임에 확인해야 한다 | ★ **어느 장치도 안 해 준다.** `inspect.signature` 로 직접 본다 |
| 시퀀스·매핑 같은 표준 모양을 만든다 | **`collections.abc`** — 정본은 [32번](../32-container-protocol/2-summary.md) |
| 「이터러블인가」를 검사한다 | ★ **`iter(x)` 를 걸고 `TypeError` 를 잡는다.** 어느 장치도 못 잡는다 |
| 한 메서드만 있으면 되는 판정을 만든다 | `__subclasshook__` — ★ 이름만 본다 |
| 타입 검사기를 안 쓸 것이 확실하다 | ★ **`Protocol` 을 쓸 이유가 거의 없다.** 주석이 된다 |

## 핵심 문장

* ★★★ **「언제 막히나」가 세 갈래다** —
  **ABC 는 인스턴스를 만들 때**(그리고 남은 이름을 전부 나열해 준다),
  **`runtime_checkable` 은 물어볼 때**(그런데 이름까지만),
  **`Protocol` 은 아무 때도 안 막는다.**
* ★★★ **`Protocol` 은 런타임에 아무것도 강제하지 않는다.**
  명시적으로 물려받고 하나도 구현 안 해도 **만들어지고**, 메서드가 **예외가 아니라 `None`** 을 준다.
  강제하는 것은 **타입 검사기**이고 **이 머신에는 그것이 없다**(첫 블록이 `PATH` 를 물었다).
* ★★ **`runtime_checkable` 은 메서드 이름만 본다.** 서명도, 부를 수 있는지도 안 본다 —
  **정수 `42` 를 `close` 라는 이름에 넣어 두면 `isinstance` 가 참**이고 호출에서 터진다.
* ★★ **`register()` 는 「그렇게 치자」일 뿐 아무것도 검사하지 않는다.**
  그리고 `__mro__` 를 안 바꾸므로 **믹스인이 안 따라온다.**
* ★★ **비메서드 멤버가 있는 프로토콜은 `isinstance` 는 되고 `issubclass` 가 막힌다** —
  클래스만 보고는 인스턴스가 그 속성을 갖게 될지 알 수 없기 때문이다.
* ★★ **ABC 는 요구하고 주며, `Protocol` 은 요구만 한다.**
  같은 두 메서드를 써도 ABC 쪽은 다섯이 따라오고 `Protocol` 쪽은 아무것도 안 온다.
* ★★★ **Go 와의 대비는 절반만 같다** — 둘 다 **구현 선언이 없다.**
  그런데 **Go 는 컴파일러가 서명까지 보고**(`have`/`want`), 파이썬은 **아무도 안 보거나 이름만 본다.**
* ★ **구조로 판정하는 길은 전부 이름까지만 본다** — `runtime_checkable` 도 `__subclasshook__` 도 그렇다.
* ★ **「이터러블인가」는 여전히 `iter(x)` 로만 정확히 묻는다.** 어느 장치도 그 창이 아니다([32번](../32-container-protocol/2-summary.md) 정본).

## 관련 자료

* 목록: [python/syntax 주제 목록](../README.md) — 이 주제는 **35번**
* 선행·정본: [32-container-protocol](../32-container-protocol/2-summary.md) — ★★★ **`collections.abc` 믹스인의 정본.**\
  **경계**: 「둘만 쓰면 다섯이 따라온다」와 「`__subclasshook__` 이 한 메서드짜리 ABC 에만 있다」,
  「`isinstance(Old(), Iterable)` 이 거짓인데 `for` 는 돈다」는 전부 그쪽이다.
  여기는 「**그 계약을 누가 강제하나**」부터이고, 그쪽 결론은 **다시 재지 않고 인용만** 했다.
* 선행: [34-inheritance-mro-super](../34-inheritance-mro-super/2-summary.md) — ABC 의 믹스인이 **그 줄을 타고** 온다.\
  **경계**: MRO 계산과 `super()` 는 그쪽, 여기는 **`register` 가 그 줄에 안 들어간다는 결과**만.
* 선행: [29-classes-and-attribute-lookup](../29-classes-and-attribute-lookup/2-summary.md) — 클래스 칸과 탐색.
* 함께 보는 곳: [30-repr-eq-hash-contracts](../30-repr-eq-hash-contracts/2-summary.md) — ★ 그쪽 「더 들어가면」이
  **`typing.Hashable` 로 「해시 가능함」을 타입으로 요구할 수 있나**를 남겨 두고 **정적 검사기 범위는 확인 못 했다**고 적었다.\
  ★★ **이 주제가 그 물음의 런타임 쪽에 답한다**(동작 5의 ⑤) — `Hashable` 은 `__hash__` 하나만 보는 **오리 판정**이라
  `__eq__` 만 정의한 클래스가 **거짓**이 된다.\
  ★ **정적 검사기 쪽은 여전히 못 열었다** — 이 머신에 그 도구가 없다(첫 블록).
* 이어지는 곳: 목록의 **40번 주제** 「타입 힌트의 런타임 의미」 — ★ **「힌트가 실행을 안 바꾼다」의 정본**이다.
  여기서는 동작 3의 ③에서 그 결과만 썼다.
* 이어지는 곳: 목록의 **41번 주제** 「`typing` 과 제네릭 신문법」 — `Protocol` 의 제네릭 판과 `TypeIs`.
* 이어지는 곳: 목록의 **38번 주제** 「`namedtuple`·`NamedTuple`·`TypedDict`」 — **런타임 정체와 타입 의미가 갈리는** 같은 축의 주제.
* ★★★ 대비: Go 갈래 목록([`go/syntax/README.md`](../../../go/syntax/README.md))의 **20번** 「인터페이스 선언과 암묵 구현」 —
  **이 주제의 직접 대비 대상**이다. 둘 다 암묵인데 **Go 는 컴파일러가 강제하고 `Protocol` 은 타입 검사기만 본다.**\
  **경계**: Go 쪽 수치·에러 문구는 전부 그쪽 실측이고 여기서는 **인용만** 했다.
* 대비: TS 갈래 목록([`ts/syntax/README.md`](../../../ts/syntax/README.md))의 **05번** 「구조적 타이핑」 —
  ★ TS 는 구조적 타이핑이 **모든 타입의 기본값**이고, 파이썬은 **프로토콜마다 골라서** 쓴다.
  ★ 「검사 시각에만 있고 런타임에는 아무것도 아니다」는 결론은 **둘이 같다.**
* 대비: 자바 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **11번** 「인터페이스 — `default` 메서드」 —
  ★ **반대쪽 끝**이다. `implements` 를 적으므로 **IDE 가 구현체 목록을 만들 수 있다.**
* 원리: [`cs/foundations/oop-basics/`](../../../../oop-basics/) — 다형성·인터페이스 일반론.
* 공식 문서: [`abc`](https://docs.python.org/3.12/library/abc.html) ·
  [`typing.Protocol`](https://docs.python.org/3.12/library/typing.html#typing.Protocol) ·
  [`typing.runtime_checkable`](https://docs.python.org/3.12/library/typing.html#typing.runtime_checkable) ·
  [`collections.abc`](https://docs.python.org/3.12/library/collections.abc.html) ·
  [PEP 544](https://peps.python.org/pep-0544/)

## 용어 풀이

* **추상 베이스 클래스(ABC)**: 「이것은 반드시 구현해라」를 강제하는 부모 클래스.\
  예: 안 채우면 **인스턴스를 만들 때** `TypeError` 다.
* **추상 메서드(abstract method)**: `@abstractmethod` 를 붙인 메서드.\
  예: 몸통이 있어도 된다 — `Storage.read(None, 'k')` 가 실제로 돈다.
* **`__abstractmethods__`**: 아직 안 채운 추상 메서드 이름들. `frozenset` 이다.\
  예: **순서가 보장 안 되므로 `sorted()` 로 찍는다.**
* **가상 서브클래스(virtual subclass)**: `register()` 로 「그렇게 치자」고 선언만 한 관계.\
  예: `isinstance` 는 참인데 `__mro__` 에 없고 믹스인도 안 온다.
* **`__subclasshook__`**: 상속·등록 없이 `isinstance` 를 참으로 만드는 갈고리.\
  예: `NotImplemented` 를 주면 기본 판정으로 떨어진다.
* **구조적 서브타이핑(structural subtyping)**: 모양이 맞으면 그 타입으로 치는 방식.\
  예: `typing.Protocol` 이 그 장치이고 **판정은 타입 검사기가 한다.**
* **명목적 서브타이핑(nominal subtyping)**: 「그 타입이라고 **선언한** 것」만 그 자리에 넣는 방식.\
  예: 상속과 `register()` 가 그쪽이다.
* **`runtime_checkable`**: 프로토콜에 `isinstance` 를 열어 주는 데코레이터.\
  예: **메서드 이름만** 본다. 서명은 안 본다.
* **`__protocol_attrs__`**: 프로토콜이 보는 이름들. **3.12 에서 노출된 내부 이름**이다.\
  예: `Closer.__protocol_attrs__` 가 `{'close'}` 다.
* **비메서드 멤버(non-method member)**: 프로토콜에 적은 **속성 어노테이션**(`name: str`).\
  예: 있으면 `issubclass` 가 `TypeError` 다.
* **믹스인(mixin)**: 몇 개만 구현하면 나머지를 만들어 주는 메서드 묶음.\
  예: ABC 는 주고 `Protocol` 은 안 준다.

## 더 들어가면

* ★ **`ABCMeta` 가 메타클래스라 충돌이 난다.** ABC 와 다른 메타클래스를 같이 쓰려면
  둘을 합친 메타클래스를 만들어야 한다 — [34번](../34-inheritance-mro-super/2-summary.md)이 「메타클래스는 충돌이 난다」고 적은 그 자리다.
  ★ 이 배치에서는 충돌을 던지지 않았다 — **인출 대상 밖**이다.
* ★ **`abstractproperty`·`abstractclassmethod`·`abstractstaticmethod` 는 폐기됐다**(3.3+).
  지금은 `@property` 와 `@abstractmethod` 를 **겹쳐 쓴다**(`@abstractmethod` 가 안쪽).
  ★ [33번](../33-property-descriptor-slots/2-summary.md)의 디스크립터 규칙 위에 그대로 선다.
* ★ **프로토콜끼리 상속할 수 있다** — `class P2(P1, Protocol)` 처럼 `Protocol` 을 다시 적어야
  프로토콜로 남는다. 안 적으면 **보통 클래스**가 되고, 그것이 동작 3의 ⑤가 만든 상태다.
* ★★ **`typing.get_type_hints` 로 프로토콜의 서명을 읽어 직접 대조하는 길**이 있다.
  런타임에 서명까지 보려면 그 길밖에 없다 — 표준 장치는 아무것도 안 해 준다(동작 4).
  ★ 이 배치는 **`inspect.signature` 로 서명을 읽는 쪽**을 [36번](../36-dataclasses/2-summary.md) 이 실제로 쓴다.
* ★★★ **이 주제의 가장 큰 미완은 타입 검사기 층이다.** `mypy` 나 `pyright` 를 붙이면
  동작 3의 ②·③·⑤가 **전부 에러로 잡힐 것**이지만, **이 배치는 그것을 확인하지 못했다**(도구 없음).
  ★ 「못 잰 것」으로 적는다 — 「안 돌려 본 것」과 다르다.
  ★ **쪼개서 잰 조각** — 런타임 쪽은 전부 실측했고, `PATH` 조회로 **도구의 부재 자체도 출력으로** 남겼다.
