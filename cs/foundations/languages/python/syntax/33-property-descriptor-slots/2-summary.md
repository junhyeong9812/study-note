# python/syntax/33-property-descriptor-slots — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만.
> - [3.3.2.3. Invoking Descriptors](https://docs.python.org/3.12/reference/datamodel.html#invoking-descriptors) — 우선순위 네 층이 한 문장에 적혀 있다
> - [3.3.2.2. Implementing Descriptors](https://docs.python.org/3.12/reference/datamodel.html#implementing-descriptors) — `__get__`·`__set__`·`__delete__` 의 서명
> - [`object.__set_name__`](https://docs.python.org/3.12/reference/datamodel.html#object.__set_name__) — **클래스가 만들어질 때** 불린다
> - [3.3.2.4. `__slots__`](https://docs.python.org/3.12/reference/datamodel.html#slots) — 없앤 것·생긴 것·상속 규칙
> - [`property`](https://docs.python.org/3.12/library/functions.html#property) — 세 칸과 `getter`/`setter`/`deleter`
> - [`inspect.getattr_static`](https://docs.python.org/3.12/library/inspect.html#inspect.getattr_static) — *"Retrieve attributes without triggering dynamic lookup via the descriptor protocol"*
>
> **실행 검증** — 이 문서에 실린 출력은 전부 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.\
> ★ 던지는 형태를 하나로 고정했다 — `python3 - <파일` 로 던져 트레이스백이 `File "<stdin>", line N` 이 된다.\
> ★★ **캐럿은 예외 종류에 달렸다** — 실행 중 예외는 소스 줄도 `^` 캐럿도 안 나오고, `SyntaxError` 라야 둘 다 나온다.
> 이 문서의 트레이스백은 **한 덩어리뿐이고 실행 중 예외**라 세 줄짜리다. 나머지 예외는 전부 `except` 로 받아 **타입과 메시지만** 찍었다.\
> **버전** — 세 장치 전부 **새 스타일 클래스(2.2)** 와 함께 온 것이고 이 노트 범위(3.10\~3.13)에서 안 바뀌었다.
> 하나만 나중이다 — **`__set_name__` 은 3.6** 부터다(PEP 487).\
> **구현 대 언어 보장 한 줄** — **우선순위 네 층·`property` 의 세 칸·`__slots__` 가 `__dict__` 를 없앤다는 것까지가 언어 보장**이고,
> ★★★ **`__slots__` 가 메모리를 얼마나 아끼는지는 CPython 구현**이다. 그 수치를 언어 사실로 적으면 틀린다.\
> ★ **흔들리는 칸 / 안 흔들리는 칸** — 재대조에서 「고칠 것」과 「설계상 안 맞는 것」을 기계적으로 가르려고 미리 선언한다.
>
> | 흔들린다 | 안 흔들린다(근거로 써도 되는 칸) |
> |---|---|
> | ★★★ **`sys.getsizeof` 의 절댓값** — 판·빌드·플랫폼이 바꾼다 | ★ **어느 쪽이 작나**라는 대소 관계 |
> | `id()` 와 `0x…` 주소 — **이 주제는 한 번도 안 찍었다** | 예외 **종류** · `File "<stdin>", line N` · `(exit N)` |
> | 판이 오르면 예외 **문구**와 `member_descriptor` 같은 **내부 타입 이름** | **호출 로그의 순서** · 어느 갈고리가 **불렸나 안 불렸나** |
> | — | `vars()` 의 **내용** · `fget`/`fset`/`fdel` 이 **찼나 비었나** |
>
> ★ **이 주제의 블록에는 주소도 시간도 절대경로도 한 곳도 안 찍힌다.** 같은 판에서 다시 돌리면 **한 글자도 안 변한다**(재대조 34블록 전부 동일).\
> **선행** — [29-classes-and-attribute-lookup](../29-classes-and-attribute-lookup/2-summary.md)(★★★ **우선순위 네 층의 정본**) ·
> [24-decorators](../24-decorators/2-summary.md)(`@` 가 이름에 결과를 다시 묶는 것) ·
> [03-mutability-and-copying](../03-mutability-and-copying/2-summary.md)(고치기와 새로 묶기).\
> **이 사슬** — [29](../29-classes-and-attribute-lookup/2-summary.md) → 33 → [34번](../34-inheritance-mro-super/2-summary.md) .
> **29 가 「어느 칸에서 답이 나오나」였다면 33 은 「그 칸에 무엇을 앉혀 두나」다.**

## 한눈에 — 쉽게 말하면

**세 장치는 전부 「클래스 칸에 앉아 대신 답하는 것」이고, 다른 것은 「누가 앉느냐」뿐이다.**

* `property` — **내가 쓴 함수 셋**을 앉힌다. 가장 싸고 가장 흔하다.
* 디스크립터 — **내가 만든 클래스**를 앉힌다. 여러 속성에 **재사용**된다.
* `__slots__` — **언어가 만든 칸**을 앉힌다. 대신 **사물함(`__dict__`)을 없앤다.**

```text
   obj.x 를 쓰면 무엇이 답하나 — 29번이 정한 네 층

   ① 클래스 칸(MRO)에서 찾은 것이 데이터 디스크립터인가
        예 -> 그것이 답한다            <- property · __slots__ 의 칸 · __set__ 있는 디스크립터
   ② 인스턴스 칸 vars(obj) 에 있나
        예 -> 그 값이 답한다
   ③ ①에서 찾은 것이 비데이터 디스크립터인가
        예 -> 그것이 답한다            <- 함수 · __get__ 만 있는 디스크립터
   ④ 그냥 값이면 그 값이 답한다

   ★ 이 주제는 ①·③ 에 무엇을 앉히느냐의 이야기다
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 선반에 앉은 안내원 | 디스크립터 | 클래스 칸의 그것에 `__get__` 이 있나 |
| 손님을 되돌려 보낼 수 있는 안내원 | 데이터 디스크립터 | `__set__` 또는 `__delete__` 도 있나 |
| 안내 창구 세 개짜리 데스크 | `property` 의 `fget`·`fset`·`fdel` | `Cls.__dict__['x'].fget` 이 비었나 |
| ★ 창구를 하나 더 달면 **데스크를 통째로 새로 짜는 것** | `@x.setter` 가 새 `property` 를 만든다 | `is` 로 견줘 본다 |
| 사물함을 없애고 벽에 붙박이 칸을 판 건물 | `__slots__` | `vars(obj)` 가 `TypeError` |
| 붙박이 칸마다 배치된 언어의 안내원 | `member_descriptor` | `type(Cls.__dict__['x']).__name__` |
| ★ **안내원을 부르지 않고 선반만 들여다보는 창** | `inspect.getattr_static` | 로그가 **안 찍힌다** |
| 안내원이 자기 이름표를 받는 순간 | `__set_name__` | `class` 문이 끝나기 **전에** 불린다 |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.\
「**`@property` 를 붙였는데 대입이 `AttributeError` 가 난다**」와
「**`__slots__` 를 썼는데 하위 클래스에서 아무 속성이나 붙는다**」가 그것이다.\
앞엣것은 **창구를 안 단 데스크**이고, 뒤엣것은 **한 층만 붙박이로 판 건물**이다.

> **디스크립터(descriptor)** — `__get__`·`__set__`·`__delete__` 중 하나라도 가진 객체.
> **클래스 칸에 놓였을 때만** 속성 접근을 가로챈다.\
> 예: `property` 도 `__slots__` 의 칸도 우리가 매일 쓰는 **함수**도 전부 디스크립터다.

> **`property`** — `fget`·`fset`·`fdel` 세 칸을 가진, 표준 라이브러리가 주는 디스크립터.\
> 예: `@property` 는 `fget` 만 채운 객체를 만든다.

> **`__slots__`** — 인스턴스의 `__dict__` 를 없애고 **고정된 칸**만 두는 선언.\
> 예: 클래스 칸에 이름마다 `member_descriptor` 가 하나씩 생긴다.

### ★★ 이 주제가 쓰는 창 / 부적용인 창

**본체는 「누가 답했나」 로그 창이다.** 세 장치를 한 클래스에 얹고 각자 `print` 를 심어,
**어느 줄이 찍히고 어느 줄이 안 찍히는지**로 답을 얻는다.

| 창 | 무엇을 말해 주나 | 못 보는 것 |
|---|---|---|
| ① ★ **호출 로그** — 각 갈고리 안의 `print` | 실제로 **누가 답했나** | 아무도 안 앉은 이름 |
| ② `type(Cls.__dict__[n]).__name__` | 그 칸에 **무엇이 앉아 있나** | 그것이 실제로 불리는지 |
| ③ `hasattr(t, '__set__')` | **데이터인가 비데이터인가** | 우선순위가 실제로 뒤집히는지 |
| ④ ★★ **`inspect.getattr_static`** | 「**답한 것**」이 아니라 「**거기 앉은 것**」 | 값이 계산되면 그 값 |
| ⑤ `vars(obj)` / `Cls.__dict__` | 어느 칸에 무엇이 들었나 | `__slots__` 인 객체에는 **아예 안 열린다** |
| ★ **부적용인 창** — `timeit` 류 속도 측정 | — | **이 문서는 속도를 한 번도 안 쟀다.** 「`__slots__` 가 빠르다」는 **여기 없다** |

★★ **④가 이 주제의 네 번째 창이다.** 「무엇이 거기 있나」와 「무엇이 답하나」를 가른다 —
29번이 세 창으로 「어느 칸에서 나왔나」를 물었다면, 이 창은 **그 칸을 열어 보되 안내원을 부르지 않는다.**

★ **제5의 상태 — 「같은 질문을 다른 창으로 물었다」.**
「`__slots__` 가 무엇을 아끼나」를 속도 창으로 물을 수도 있었지만 **그 창을 안 열었다**(재지 않은 성능 주장을 안 하려고).
대신 **`sys.getsizeof` 라는 크기 창**으로 물었고, 그 창이 무엇을 못 보는지도 같이 적는다 —
**`getsizeof` 는 얕아서 인스턴스 껍데기만 잰다.** 옆에 달린 `__dict__` 는 따로 세야 한다(동작 6).

먼저 판을 박아 둔다. 이 문서의 모든 출력은 아래 판에서 나왔다.

```python
# e33_version.py
import inspect
import sys

print("version_info   =", sys.version_info)
print("implementation =", sys.implementation.name)
print("platform       =", sys.platform)
print("inspect.getattr_static 가 있나 :", hasattr(inspect, "getattr_static"))
print("sys.getsizeof 가 있나          :", hasattr(sys, "getsizeof"))
```
```text
===== python3 - <e33_version.py =====
version_info   = sys.version_info(major=3, minor=12, micro=3, releaselevel='final', serial=0)
implementation = cpython
platform       = linux
inspect.getattr_static 가 있나 : True
sys.getsizeof 가 있나          : True
(exit 0)
```

## 이 주제가 답하려는 질문

1. **세 장치가 각각 어디에 서 있나** — `property`·손으로 만든 디스크립터·`__slots__` 의 칸이 29번의 네 층 중 **어느 층**인가.
2. ★★★ **한 클래스에 셋을 다 얹으면 누가 답하나** — 그리고 **누가 로그를 안 남기나.**
3. **`__slots__` 는 무엇을 막고 무엇을 아끼나** — 막는 것은 언어 보장이고 **아끼는 것은 무엇의 이야기인가.**

★ 둘째가 이 주제의 인출 목표다. **「property 와 `__slots__` 가 같은 규칙의 두 사례」라고 말할 수 있는 것**이 아는 것과 들은 것의 경계다.

## 동작 방식

> 이 절이 본문이다. 그림이 먼저 오고 문장이 그 그림을 읽어 준다.

### 1. ★★★ 세 장치를 한 클래스에 얹는다 — 「누가 답했나」 로그

**언제 쓰나** — 이 주제의 출발점. 셋을 따로따로 배우면 **같은 규칙의 세 사례라는 것**이 안 보인다.

```text
   class Sensor:
       __slots__ = ("raw", "_tag")      <- ③ 언어가 칸을 판다
       tag = Logged()                   <- ② 내가 만든 디스크립터
       @property
       def celsius(self): ...           <- ① 내가 쓴 함수 셋

   Sensor 의 클래스 칸

   +-------------------------------------------------+
   | celsius -> property          (fget·fset 가 찼다) |
   | tag     -> Logged            (__get__·__set__)   |
   | raw     -> member_descriptor (언어가 만든 것)     |
   | _tag    -> member_descriptor                     |
   +-------------------------------------------------+
              ^                ^                  ^
              |                |                  |
            내 함수         내 클래스           언어

   ★ 셋 다 클래스 칸에 앉았고 셋 다 데이터 디스크립터다
   ★ 다른 것은 "누가 그것을 만들었나" 뿐이다
```

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
```text
===== python3 - <e33_three.py =====
① 세 장치가 한 클래스 칸에 나란히 있다
      [디스크립터] __set__ 이 가로챈다 : tag <- '실외'
   celsius  -> property
   tag      -> Logged
   raw      -> member_descriptor
   _tag     -> member_descriptor
② 누가 답하나 — 읽기
      [property] fget 이 답한다
   s.celsius -> 23.5
      [디스크립터] __get__ 이 답한다 : tag
   s.tag     -> 실외
   s.raw     -> 235   <- member_descriptor 는 로그를 안 남긴다
③ 누가 답하나 — 쓰기
      [property] fset 이 받는다
      [디스크립터] __set__ 이 가로챈다 : tag <- '실내'
   다시 읽으면 : 210 | 실내
④ 셋 다 데이터 디스크립터인가 — 29번의 판별식을 그대로 건다
   celsius  __get__:True  __set__:True  __delete__:True
   tag      __get__:True  __set__:True  __delete__:False
   raw      __get__:True  __set__:True  __delete__:True
⑤ ★ getattr_static 은 디스크립터를 「부르지 않고」 거기 앉은 것을 본다
   getattr_static(s, 'celsius') -> property
   getattr_static(s, 'tag'    ) -> Logged
   getattr_static(s, 'raw'    ) -> member_descriptor
   ★ 위 세 줄에 [property]·[디스크립터] 로그가 한 줄도 없다
⑥ 인스턴스 칸은 아예 없다
   hasattr(s, '__dict__') : False
   vars(s) -> TypeError: vars() argument must have __dict__ attribute
(exit 0)
```

그림 해설 — 여섯 덩어리가 각각 다른 것을 말한다.

* ★★ **①이 이 절의 심장이다.** 클래스 칸에 `property`·`Logged`·`member_descriptor` 가 **나란히** 앉아 있다.
  세 장치가 **다른 층에 있는 것이 아니라 같은 선반의 세 자리**다.
* ★ **②에서 `s.raw` 만 로그가 없다.** `member_descriptor` 는 **C 로 된 칸**이라 `print` 를 심을 자리가 없다.
  **「조용한 것」이 「안 지나간 것」이 아니다** — 이 줄이 그 구분을 만든다.
* **③에서 쓰기도 각자에게 간다.** `s.celsius = 21.0` 이 `fset` 으로, `s.tag = "실내"` 가 `Logged.__set__` 으로 갔다.
* ★★★ **④가 셋을 한 규칙으로 묶는다.** 29번의 판별식(`__set__` 이 있나)을 그대로 걸면 **셋 다 데이터 디스크립터**다.
  ★ `Logged` 만 `__delete__` 가 없고 나머지 둘은 있다 — 그래도 **데이터 자격에는 차이가 없다**(둘 중 하나만 있으면 된다).
* ★★ **⑤가 네 번째 창이다.** `inspect.getattr_static` 으로 셋을 물으니 **로그가 한 줄도 안 찍혔다.**
  「무엇이 거기 앉아 있나」만 답하고 **안내원을 부르지 않는다.** 동작 7이 그 창의 정본이다.
* **⑥ — `__slots__` 를 썼으므로 인스턴스 칸이 아예 없다.** `vars(s)` 가 `TypeError` 다(29번 동작 8).

★ 그래서 이 주제의 한 줄은 이렇다 — **「셋은 서로 다른 기능이 아니라, 클래스 칸에 데이터 디스크립터를 앉히는 세 가지 방법이다.」**

**비용** — 셋 다 **접근마다 함수 호출 또는 C 레벨 접근**이 낀다.
★ **그 비용이 얼마인지는 이 문서가 안 쟀다** — 속도 창을 열지 않았다(위의 「부적용인 창」).

### 2. ★★ `property` 의 세 칸 — `@x.setter` 는 새 객체를 만든다

**언제 쓰나** — 「`@property` 만 붙였는데 왜 대입이 막히지」가 날 때. 그리고 데코레이터가 무엇을 하는지 볼 때.

```text
   @property
   def celsius(self): ...          ->  property(fget=celsius, fset=None, fdel=None)
                                        |
   @celsius.setter                      | ★ 이 객체를 고치는 게 아니다
   def celsius(self, v): ...       ->  property(fget=celsius, fset=celsius, fdel=None)
                                        ^
                                        +-- 새 객체다. 클래스 칸의 이름이 그쪽으로 다시 묶인다

   ★ 앞의 객체를 다른 이름으로 붙잡아 두면 두 개가 나란히 남는다
     only_getter -> fset 이 빈 property
     celsius     -> fset 이 찬 property
```

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
```text
===== python3 - <e33_property.py =====
① property 의 세 칸 — fget·fset·fdel
   only_getter fget:celsius  fset:None     fdel:None
   celsius     fget:celsius  fset:celsius  fdel:celsius
② ★ @celsius.setter 는 그 자리를 고치는 게 아니라 새 property 를 만든다
   only_getter is celsius : False
   둘 다 property 인가     : property property
   두 fget 이 같은 함수인가 : True
   only_getter 에 fset 이 있나 : False
③ 그래서 only_getter 쪽으로 대입하면 막힌다
   t.only_getter -> 20.0
   t.only_getter = 30.0 -> AttributeError: property 'only_getter' of 'Temp' object has no setter
④ celsius 쪽은 대입이 되고 검증도 돈다
   t.celsius -> 30.0
   t.celsius = -300.0 -> ValueError: 절대영도 아래는 못 넣는다: -300.0
⑤ del 은 fdel 로 간다
      fdel 이 불렸다
   t.celsius -> None
⑥ ★ property 는 클래스 칸에 놓여야 먹는다 — 인스턴스에 붙이면 그냥 객체다
   type(p.x)        : property
   p.x 가 문자열인가 : False
   p.x.fget 을 손으로 부르면 : 인스턴스에 붙인 것
   클래스 칸에 놓은 뒤 p.y  : 클래스 칸에 놓으니 불린다
   type(p.y)        : str
(exit 0)
```

그림 해설 — 여섯 덩어리가 「세 칸」과 「새 객체」를 가른다.

* ★ **①이 세 칸을 표로 보인다.** `only_getter` 는 `fget` 만 찼고, `celsius` 는 셋이 다 찼다.
  ★ **세 칸의 함수 이름이 전부 `celsius` 다** — `def` 를 세 번 같은 이름으로 썼기 때문이다.
* ★★ **②가 이 절의 과녁이다.** `only_getter is celsius` 가 **`False`** 다 —
  `@celsius.setter` 는 **그 자리를 고치는 게 아니라 새 `property` 를 만들어 돌려준다.**
  ★ 그런데 **두 `fget` 은 같은 함수**다(`is` 가 참). **함수는 물려주고 껍데기만 새로 짠 것**이다.
  ★ 이것이 [24번](../24-decorators/2-summary.md)의 「데코레이터는 이름에 결과를 다시 묶는다」의 한 사례다.
* **③ — `fset` 이 빈 쪽으로 대입하면 `AttributeError` 다.**
  문구가 `property 'only_getter' of 'Temp' object has no setter` 로 **어느 칸이 비었는지**를 말해 준다.
* **④ — 찬 쪽은 대입이 되고 내가 쓴 검증도 돈다.** `ValueError` 가 **내 함수에서** 나왔다.
* **⑤ — `del t.celsius` 가 `fdel` 로 간다.** 로그 `fdel 이 불렸다` 가 그 증거다.
* ★★ **⑥이 이 절의 둘째 과녁이다.** `property` 를 **인스턴스에 붙이면 안 먹는다.**
  `p.x` 가 `property` 객체 **그 자체**로 나오고 문자열이 아니다. `p.x.fget(p)` 로 **손으로 불러야** 값이 나온다.
  같은 객체를 **클래스 칸에 놓으니**(`Plain.y`) 그때부터 `p.y` 가 문자열을 답한다.
  ★ 이유는 29번의 네 층 그대로다 — **디스크립터 프로토콜은 클래스 칸에서 찾은 것에만 걸린다.**

**비용** — `property` 는 **가장 싼 길**이다. 클래스를 따로 만들 필요가 없다.
대신 **재사용이 안 된다** — 속성 열 개에 같은 검증을 걸려면 함수를 열 벌 써야 한다. 그때가 동작 3이다.

### 3. ★ 디스크립터 프로토콜 셋 + `__set_name__`

**언제 쓰나** — 같은 검증·변환을 **속성 여러 개에** 걸 때. ORM 필드·설정 스키마가 전부 이 자리다.

```text
   디스크립터가 가질 수 있는 갈고리 넷

   __set_name__(self, owner, name)   class 문이 끝나기 "전에" 한 번   <- 3.6+
   __get__(self, obj, objtype=None)  obj.x 를 읽을 때
   __set__(self, obj, value)         obj.x = v 를 할 때
   __delete__(self, obj)             del obj.x 를 할 때

   ★ __get__ 만 있으면 비데이터, __set__ 이나 __delete__ 가 하나라도 있으면 데이터

   __get__ 의 obj 자리가 갈린다

        obj.x        ->  __get__(desc, obj,  type(obj))
        Cls.x        ->  __get__(desc, None, Cls)        <- obj 가 None 이다
```

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
```text
===== python3 - <e33_descriptor.py =====
① class 문이 끝나기 전에 __set_name__ 이 먼저 불린다
      __set_name__ : owner = Box | name = a
      __set_name__ : owner = Box | name = b
② 그 덕에 이름을 손으로 안 넘겨도 된다
   Box.__dict__['a'].name : a
   Box.__dict__['b'].name : b
③ 읽기·쓰기·지우기가 각각 다른 갈고리로 간다
      __get__   : 인스턴스에서 꺼냈다
   bx.a -> (아직 없음)
      __set__   : 7
   vars(bx) : {'a': 7}
      __get__   : 인스턴스에서 꺼냈다
   bx.a -> 7
      __delete__ 가 불렸다
   vars(bx) : {}
④ 클래스에서 꺼내면 obj 자리에 None 이 들어온다
      __get__   : 클래스에서 꺼냈다 (obj 가 None)
   type(Box.a).__name__ : Traced
⑤ ★ 디스크립터 하나가 인스턴스 여럿을 상대한다 — 상태를 자기 안에 두면 새어 나간다
      __set__   : 'p 의 값'
      __set__   : 'q 의 값'
      __get__   : 인스턴스에서 꺼냈다
   p.b -> p 의 값
      __get__   : 인스턴스에서 꺼냈다
   q.b -> q 의 값
   vars(p) : {'b': 'p 의 값'}
   vars(q) : {'b': 'q 의 값'}
   ★ 값은 인스턴스 칸에 넣었기 때문에 안 섞인다. 디스크립터 자신에게 넣으면 섞인다
⑥ ★ __set_name__ 은 class 문이 만들 때만 불린다 — 나중에 붙이면 안 불린다
   Box.c 를 붙인 뒤 late 에 name 이 있나 : False
      __get__   : 인스턴스에서 꺼냈다
   그래서 Box().c 를 읽으면 -> AttributeError: 'Traced' object has no attribute 'name'
(exit 0)
```

그림 해설 — 여섯 덩어리가 네 갈고리를 전수로 건드린다.

* ★★ **①이 `__set_name__` 의 시점을 못 박는다.** `class Box:` 문이 **끝나기 전에** 두 번 불렸고,
  그 덕에 ②에서 `Box.__dict__['a'].name` 이 `a` 다. **이름을 손으로 안 넘겨도 된다.**
  ★ 이것이 29번이 「**이 주제에서는 안 돌려 봤다**」고 적어 둔 자리다. 여기서 돌렸다.
* **③이 읽기·쓰기·지우기를 각자 다른 갈고리로 보낸다.** 로그가 `__get__` → `__set__` → `__get__` → `__delete__` 순이다.
* ★ **④ — 클래스에서 꺼내면 `obj` 자리에 `None` 이 온다.** 그래서 `Box.a` 가 디스크립터 자기 자신을 돌려줬다
  (`type(Box.a).__name__` 이 `Traced`). **이 분기를 안 쓰면 `Cls.x` 가 터진다.**
* ★★ **⑤가 실무의 함정이다.** 디스크립터는 **클래스 칸에 하나뿐**인데 인스턴스는 여럿이다.
  값을 `obj.__dict__` 에 넣었으므로 `p.b` 와 `q.b` 가 **안 섞였다.**
  ★ 거꾸로 **디스크립터 자신에게(`self.value = ...`) 넣으면 모든 인스턴스가 한 값을 나눠 쓴다** —
  [29번](../29-classes-and-attribute-lookup/2-summary.md) 동작 3의 **클래스 변수 공유와 같은 집안**이다.
* ★ **⑥ — `__set_name__` 은 `class` 문이 만들 때만 불린다.** 나중에 `Box.c = late` 로 붙이면 **안 불리고**,
  그래서 `late` 에 `name` 이 없어 읽는 순간 `AttributeError` 가 난다.
  **동적으로 붙이는 디스크립터는 이름을 손으로 넘겨야 한다.**

**비용** — 클래스를 하나 더 만드는 값으로 **속성 여러 개에 재사용**된다.
대신 **값을 어디 두느냐를 내가 정해야** 하고, 그 선택이 ⑤의 함정을 만든다.

### 4. ★★ 비데이터를 데이터로 바꾸면 — 29번 결론의 역방향

**언제 쓰나** — 「왜 인스턴스 칸이 이기지 / 지지」가 막힐 때. 이 절은 29번이 잰 것을 **거꾸로 던진다.**

[29번](../29-classes-and-attribute-lookup/2-summary.md)은 **두 클래스를 만들어** 데이터와 비데이터를 견줬다.
여기서는 **한 클래스를 그대로 두고 `__set__` 만 붙였다 뗐다** 한다 — 인스턴스도 값도 한 글자도 안 건드린다.

```text
   Holder.x 에 Answers() 를 앉혀 두고, h.__dict__['x'] 에 값도 넣어 둔다

   Answers 에 __set__ 이 없을 때          Answers.__set__ = ... 를 붙인 뒤

   클래스 칸  x -> [Answers]              클래스 칸  x -> [Answers]   (같은 객체다)
   인스턴스 칸 x -> "인스턴스 칸의 값"      인스턴스 칸 x -> "인스턴스 칸의 값" (안 건드렸다)

   h.x -> "인스턴스 칸의 값"   (짐)        h.x -> "디스크립터가 답한다"  (이김)

   ★ 바뀐 것은 인스턴스도 클래스 칸의 물건도 아니라 "그 물건의 타입" 이다
```

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
```text
===== python3 - <e33_flip.py =====
① 지금은 비데이터 디스크립터다 — 29번의 결론대로 인스턴스 칸이 이긴다
   Answers 에 __set__ 이 있나 : False
   vars(h)['x']              -> 인스턴스 칸의 값
   h.x                       -> 인스턴스 칸의 값
② ★ 역방향 실험 — 클래스에 __set__ 을 나중에 붙여 데이터 디스크립터로 바꾼다
   Answers 에 __set__ 이 있나 : True
   vars(h)['x']              -> 인스턴스 칸의 값   <- 인스턴스 칸은 한 글자도 안 건드렸다
   h.x                       -> 디스크립터가 답한다   <- 우선순위가 뒤집혔다
③ 떼면 그대로 돌아온다
   Answers 에 __set__ 이 있나 : False
   h.x                       -> 인스턴스 칸의 값
④ ★ __delete__ 만 붙여도 데이터 디스크립터가 된다
   __set__:False __delete__:True
   h.x                       -> 디스크립터가 답한다
   그런데 대입은 못 한다 : AttributeError: __set__
⑤ 바뀐 것은 인스턴스가 아니라 「디스크립터의 타입」이다
   type(Holder.__dict__['x']).__name__ : Answers
   vars(h) : {'x': '인스턴스 칸의 값'}
(exit 0)
```

그림 해설 — 다섯 덩어리가 우선순위를 **왕복**시킨다.

* **①이 출발점이다.** `__set__` 이 없으니 비데이터이고, 29번의 결론대로 **인스턴스 칸이 이긴다.**
* ★★★ **②가 이 절의 과녁이다.** `Answers.__set__` 을 **나중에 붙이자** `h.x` 의 답이 바뀌었다.
  `vars(h)['x']` 는 **한 글자도 안 변했다.** 즉 **우선순위는 값이 아니라 타입의 성질이 정한다.**
* **③ — 떼면 그대로 돌아온다.** 되돌릴 수 있다는 것이 「타입의 성질」임을 한 번 더 못 박는다.
* ★ **④ — `__delete__` 만 붙여도 데이터가 된다.** 읽기는 디스크립터가 이기는데
  **대입은 `AttributeError: __set__`** 이다. 「데이터 디스크립터인데 `__set__` 이 없는」 상태다.
  ★ 문서의 판별식이 `__set__` **또는** `__delete__` 인 이유가 이 자리다.
* **⑤ — 바뀐 것은 클래스 칸의 물건도 아니다.** `type(Holder.__dict__['x']).__name__` 이 내내 `Answers` 였다.

★★ 그래서 판정 한 줄 — **「무엇이 이기나」는 그 객체가 아니라 그 객체의 **타입**에 `__set__`/`__delete__` 가 있나로 정해진다.**
읽기(`__get__`)는 인스턴스 쪽을 봐도 되지만 **판별은 타입에서만** 한다.

**비용** — 이 실험 자체는 실무에서 쓸 일이 없다. **판별식을 눈으로 보려고** 만든 것이다.
다만 **몽키 패치로 `__set__` 을 붙이는 라이브러리**가 있다면 그것이 조용히 우선순위를 뒤집는다는 뜻이다.

### 5. ★★ `inspect.getattr_static` — 「거기 있는 것」과 「답하는 것」을 가른다

**언제 쓰나** — 디버거·직렬화기·문서 생성기를 만들 때. 그리고 **읽기만 했는데 부작용이 도는** 것을 막을 때.

문서가 목적을 적는다 — *"Retrieve attributes without triggering dynamic lookup via the descriptor protocol,
`__getattr__()` or `__getattribute__()`."*

```text
   같은 이름에 세 답이 있을 수 있다

   vars(n)['computed']              "인스턴스 칸에 몰래 넣은 값"   <- 칸에 있는 것
   n.computed                       "property 가 계산한 값"       <- 답한 것
   inspect.getattr_static(n, ...)   <property 객체>               <- 거기 앉은 것

   ★ 셋이 전부 다르다. 세 창이 각각 다른 질문에 답한다
```

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
```text
===== python3 - <e33_static_window.py =====
① 보통 클래스에서 두 창을 견준다
   shared    getattr -> 클래스 칸의 값                     getattr_static 의 타입 -> str
   own       getattr -> 인스턴스 칸의 값                    getattr_static 의 타입 -> str
   computed  getattr -> property 가 계산한 값             getattr_static 의 타입 -> property
   method    getattr -> (메서드 객체)                     getattr_static 의 타입 -> function
② ★ computed 한 줄이 이 창의 값어치다
   vars(n)['computed']          : 인스턴스 칸에 몰래 넣은 값
   n.computed                   : property 가 계산한 값
   getattr_static 이 본 것의 타입 : property
   ★ 세 답이 전부 다르다 — 「칸에 있는 것」·「답한 것」·「거기 앉은 것」이 셋 다 다르다
③ 갈고리가 있는 객체에서는 차이가 더 벌어진다
   g.zzz                : <zzz 를 즉석에서 만들었다>
   hasattr(g, 'zzz')    : True
   getattr_static(g,'zzz') -> AttributeError: zzz
   ★ 29번이 「제5의 상태」라 부른 자리를 이 창은 없다고 답한다
(exit 0)
```

그림 해설.

* **①이 네 종류를 한 표로 견준다.** 보통 값은 `getattr` 과 `getattr_static` 이 같은 것을 주고,
  `computed` 와 `method` 만 갈린다 — **디스크립터가 앉은 자리에서만 갈린다.**
* ★★★ **②가 이 창의 값어치다.** 한 이름에 **세 답**이 나왔다.
  `property` 는 데이터 디스크립터라 인스턴스 칸을 이기므로, **`vars()` 에 값이 보이는데도 답은 다른 것**이다
  (29번 동작 7의 그 자리). 그리고 `getattr_static` 은 **둘 다 아닌 세 번째**를 답한다.
* ★ **③이 차이를 더 벌린다.** `__getattr__` 이 있는 객체에서 `g.zzz` 는 문자열을 답하고 `hasattr` 도 참인데,
  **`getattr_static` 은 `AttributeError` 다.** 29번이 「**제5의 상태**」라 부른 자리를
  이 창은 **「없다」로 정확히 답한다.**

★★ 그래서 이 창의 쓸모는 하나다 — **「읽었는데 코드가 돌았다」를 피하는 것.**
`property` 안에 DB 조회가 있으면 평범한 `getattr` 한 줄이 조회를 돌린다. 이 창은 안 돌린다.
★ 대신 **이 창은 값을 모른다** — 계산되는 값을 얻으려면 결국 안내원을 불러야 한다.

**비용** — MRO 를 손으로 훑는 함수라 **보통 접근보다 하는 일이 많다.** ★ 다만 **얼마나 비싼지는 안 쟀다.**

### 6. ★★ `__slots__` 가 아끼는 것 — 절댓값이 아니라 대소만 본다

**언제 쓰나** — 같은 모양의 객체를 아주 많이 만들 때. **그리고 그 근거를 적어야 할 때.**

★★★ **이 절은 규칙을 하나 지킨다 — 크기는 재고 속도는 안 잰다.**
「`__slots__` 가 빠르다」는 이 문서에 **한 줄도 없다.** 안 쟀기 때문이다.

```text
   getsizeof 는 얕다 — 가리키는 곳까지 안 따라간다

   보통 클래스                        __slots__ = ("x", "y")

   인스턴스 [48바이트]                인스턴스 [48바이트]
       |                                  x 칸 · y 칸이 이 안에 있다
       +--> __dict__ [따로 달린 객체]
                 ^
                 +-- getsizeof(인스턴스) 에는 "안 들어간다"

   ★ 그래서 둘을 합쳐 세야 비교가 성립한다
   ★ 그리고 그 합계의 절댓값이 아니라 "어느 쪽이 작나" 만 근거로 쓴다
```

```python
# e33_slots_size.py
import sys


class WithDict:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class WithSlots:
    __slots__ = ("x", "y")

    def __init__(self, x, y):
        self.x = x
        self.y = y


a = WithDict(1, 2)
b = WithSlots(1, 2)

print("① getsizeof 는 얕다 — 인스턴스 껍데기만 잰다")
print("   getsizeof(WithDict 인스턴스)  :", sys.getsizeof(a))
print("   getsizeof(WithSlots 인스턴스) :", sys.getsizeof(b))
print("   ★ 두 값이 같다 — 여기까지만 보면 아낀 것이 없어 보인다")

print("② dict 판은 옆에 __dict__ 가 따로 달려 있다")
print("   getsizeof(a.__dict__)         :", sys.getsizeof(a.__dict__))
print("   slots 판에 __dict__ 가 있나    :", hasattr(b, "__dict__"))

print("③ 그래서 합쳐 세야 한다")
tot_d = sys.getsizeof(a) + sys.getsizeof(a.__dict__)
tot_s = sys.getsizeof(b)
print("   dict 판 합계  :", tot_d)
print("   slots 판 합계 :", tot_s)
print("   어느 쪽이 작나 :", "slots" if tot_s < tot_d else "dict")
print("   정수 몫       :", tot_d // tot_s)

print("④ 칸이 늘면 어떻게 되나 — 여덟 칸짜리로 다시")
names = tuple("abcdefgh")
Big = type("Big", (), {})
BigSlots = type("BigSlots", (), {"__slots__": names})
big = Big()
bigs = BigSlots()
for i, nm in enumerate(names):
    setattr(big, nm, i)
    setattr(bigs, nm, i)
print("   dict 판 합계  :", sys.getsizeof(big) + sys.getsizeof(big.__dict__))
print("   slots 판 합계 :", sys.getsizeof(bigs))

print("⑤ 잰 것과 안 잰 것")
print("   잰 것   : 위 수치 — 이 판·이 머신의 바이트 수")
print("   안 잰 것 : 속도. 이 문서는 __slots__ 가 빠른지 느린지 한 번도 안 쟀다")
```
```text
===== python3 - <e33_slots_size.py =====
① getsizeof 는 얕다 — 인스턴스 껍데기만 잰다
   getsizeof(WithDict 인스턴스)  : 48
   getsizeof(WithSlots 인스턴스) : 48
   ★ 두 값이 같다 — 여기까지만 보면 아낀 것이 없어 보인다
② dict 판은 옆에 __dict__ 가 따로 달려 있다
   getsizeof(a.__dict__)         : 296
   slots 판에 __dict__ 가 있나    : False
③ 그래서 합쳐 세야 한다
   dict 판 합계  : 344
   slots 판 합계 : 48
   어느 쪽이 작나 : slots
   정수 몫       : 7
④ 칸이 늘면 어떻게 되나 — 여덟 칸짜리로 다시
   dict 판 합계  : 344
   slots 판 합계 : 96
⑤ 잰 것과 안 잰 것
   잰 것   : 위 수치 — 이 판·이 머신의 바이트 수
   안 잰 것 : 속도. 이 문서는 __slots__ 가 빠른지 느린지 한 번도 안 쟀다
(exit 0)
```

그림 해설 — 다섯 덩어리가 **측정의 함정**을 먼저 보이고 결론을 나중에 낸다.

* ★★ **①이 함정이다.** 두 인스턴스의 `getsizeof` 가 **같다.** 여기서 멈추면 「아낀 것이 없다」가 된다.
  ★ **창이 얕다는 것을 모르고 한 판만 재면 정반대 결론이 나온다.**
* **②가 이유를 보인다.** `dict` 판은 `__dict__` 가 **옆에 따로 달려 있고** `slots` 판에는 그것이 없다.
* ★ **③이 결론이다.** 합쳐 세면 **`slots` 쪽이 작다.**
  ★★★ **근거로 쓰는 것은 「어느 쪽이 작나」 한 줄뿐이다.** 수치 자체는 **이 판·이 머신의 것**이고,
  정수 몫도 **판이 바뀌면 달라진다.** 머리말의 「흔들리는 칸」 표가 그것을 미리 선언해 둔 이유다.
* ★ **④가 대소 관계가 유지되는지 한 번 더 본다.** 칸을 여덟으로 늘려도 **`slots` 쪽이 여전히 작다.**
  ★ 다만 `dict` 판의 합계가 두 경우에 **같은 수**로 나왔다 — `dict` 의 용량이 계단식이라 그렇다.
  **이것도 관찰이지 보장이 아니다.**
* ★★ **⑤가 잰 것과 안 잰 것을 문서가 스스로 선언한다.** 속도는 **한 번도 안 쟀다.**

★★★ **그래서 이렇게 적으면 틀린다** — 「`__slots__` 를 쓰면 메모리가 7배 준다」.
○ **이 판에서 이 두 클래스의 합계가 그랬다**가 전부다. 칸 수·값의 종류·판이 바뀌면 달라진다.

**비용** — 아끼는 것은 메모리이고 **대가는 동적 속성**이다. 그 대가의 목록이 다음 절이다.

### 7. ★ `__slots__` 의 경계 다섯

**언제 쓰나** — `__slots__` 를 실제로 쓸 때. 여기 다섯이 전부 **선언하는 순간 터지거나 조용히 풀리는** 자리다.

```text
   __slots__ 를 쓸 때 걸리는 다섯 자리

   ① 같은 이름을 클래스 변수로도 쓰면        -> 정의 시점에 ValueError
   ② 둘 다 비지 않은 __slots__ 를 다중 상속  -> 정의 시점에 TypeError
   ③ 한쪽이 비어 있으면                      -> 된다
   ④ 목록에 '__dict__' 를 넣으면             -> 사물함이 되살아난다
   ⑤ 문자열 하나를 주면                      -> 글자 단위가 아니라 이름 하나다
   ⑥ 선언은 했지만 아직 안 넣은 칸           -> AttributeError
```

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
```text
===== python3 - <e33_slots_edge.py =====
① __slots__ 에 적은 이름을 클래스 변수로도 쓰면
   ValueError: 'x' in __slots__ conflicts with class variable
② 둘 다 비지 않은 __slots__ 를 다중 상속하면
   TypeError: multiple bases have instance lay-out conflict
③ 한쪽이 비어 있으면 된다
   Both2 인스턴스에 __dict__ 가 있나 : False
   o.a, o.c -> 1 3
④ ★ __slots__ 에 '__dict__' 를 넣으면 사물함이 되살아난다
   vars(h) : {'anything': 2}   <- fixed 는 여기 없다
   h.fixed -> 1 | h.anything -> 2
   클래스 칸의 fixed 의 정체 : member_descriptor
⑤ 문자열 하나를 주면 글자 단위가 아니라 이름 하나다
   OneName.__slots__  : 'only'
   클래스 칸의 이름들 : ['only']
⑥ 선언한 이름이라도 넣기 전에 읽으면 없다
   AttributeError: 'Lazy' object has no attribute 'v'
   넣었다 지운 뒤에도 -> AttributeError: 'Lazy' object has no attribute 'v'
(exit 0)
```

그림 해설 — 여섯 덩어리 중 **둘이 정의 시점에 터진다.**

* ★ **① `ValueError: 'x' in __slots__ conflicts with class variable`** 이다.
  ★ 이유가 그림으로 설명된다 — `__slots__` 는 클래스 칸에 `x` 라는 `member_descriptor` 를 놓으려 하는데
  **클래스 몸통의 `x = 1` 이 이미 그 자리를 차지했다.** 두 물건이 한 칸에 못 앉는다.
* ★ **② `TypeError: multiple bases have instance lay-out conflict`** 다.
  두 부모가 **각자 자기 칸의 자리(레이아웃)를 정해 놓았는데** 그것을 겹칠 방법이 없다.
* **③ 한쪽이 비어 있으면 된다.** `__slots__ = ()` 인 쪽은 자리를 안 잡았으므로 충돌이 없다.
  ★ **믹스인에 `__slots__ = ()` 를 적는 관용구**가 여기서 나온다.
* ★★ **④가 가장 얄궂다.** 목록에 `'__dict__'` 를 넣으면 **사물함이 되살아난다.**
  `h.anything = 2` 가 되고 `vars(h)` 가 열린다 — **그런데 `fixed` 는 거기 없다.**
  ★ **한 객체가 두 저장소를 동시에 쓰는 상태**다. 아끼려던 것을 도로 내놓은 셈이라 대개는 안 쓴다.
* **⑤ 문자열 하나는 이름 하나다.** `__slots__ = "only"` 가 `o`·`n`·`l`·`y` 네 칸이 아니라 `only` 한 칸이다.
  ★ 문자열이 이터러블이라 **글자로 쪼개질 것 같은데 안 그렇다** — 언어가 문자열을 특별히 가려 받는다.
* ★ **⑥ 선언한 이름이라도 넣기 전에 읽으면 `AttributeError`** 다. 그리고 **넣었다 지운 뒤에도 같다.**
  즉 `__slots__` 의 칸은 「**비어 있을 수 있는 칸**」이지 「기본값이 있는 칸」이 아니다.

①의 트레이스백 전문은 이렇다.

```python
# e33_slots_conflict_tb.py
print("__slots__ 에 적은 이름을 클래스 몸통에서 또 대입한다")


class Conflict:
    __slots__ = ("x",)
    x = 1
```
```text
===== python3 - <e33_slots_conflict_tb.py =====
__slots__ 에 적은 이름을 클래스 몸통에서 또 대입한다
Traceback (most recent call last):
  File "<stdin>", line 4, in <module>
ValueError: 'x' in __slots__ conflicts with class variable
(exit 1)
```

* ★ **실행 중 예외라 소스 줄도 캐럿도 없다.** `File "<stdin>", line 4, in <module>` 한 줄 다음 바로 예외 줄이다.
* ★ **프레임이 하나뿐이다** — `class` 문을 실행하다 난 것이지 어느 메서드 안에서 난 것이 아니다.
  ★ 막히는 시점이 「인스턴스를 만들 때」가 아니라 「**클래스를 만들 때**」라는 것이 이 한 줄에 있다.

**비용** — 다섯 중 둘은 **정의 시점에 터지므로 싸다.** 위험한 것은 조용한 쪽이다 —
**하위 클래스가 `__slots__` 를 안 쓰면 효과가 풀리는 것**(29번 동작 8의 ⑤)은 예외도 경고도 없다.

## 문법 — 형태와 규칙

**형태 — 어디에 무엇을 쓰면 누가 답하나**

```text
class C:
    __slots__ = ("raw",)            # 인스턴스의 __dict__ 를 없앤다
                                    #   -> 클래스 칸에 raw = member_descriptor (데이터)

    tag = MyDescriptor()            # 클래스 칸에 놓아야 먹는다
                                    #   -> __set_name__ 이 여기서 한 번 불린다

    @property                       # property(fget=x, fset=None, fdel=None)
    def x(self): ...

    @x.setter                       # ★ 새 property 를 만들어 이름에 다시 묶는다
    def x(self, v): ...

    @x.deleter
    def x(self): ...

    def method(self): ...           # 함수 = 비데이터 디스크립터
```

```text
진단 — 어느 창으로 무엇을 묻나

type(C.__dict__[n]).__name__          그 칸에 무엇이 앉았나 (property · member_descriptor · 내 클래스)
hasattr(type(C.__dict__[n]),'__set__')  데이터인가 (__delete__ 도 같은 자격)
C.__dict__['x'].fget / fset / fdel    property 의 세 칸 중 무엇이 비었나
inspect.getattr_static(obj, 'x')      ★ 안내원을 안 부르고 거기 앉은 것만 본다
vars(obj)                             인스턴스 칸. __slots__ 면 TypeError
C.__slots__                           그 클래스가 선언한 칸 이름들
```

규칙 열둘.

1. ★ **디스크립터는 클래스 칸에 놓여야 먹는다.** 인스턴스에 붙이면 그냥 객체다(동작 2의 ⑥).
2. ★ **데이터 디스크립터는 `__set__` **또는** `__delete__` 를 가진 것**이다. 둘 중 하나면 된다(동작 4의 ④).
3. ★ **판별은 그 객체가 아니라 그 객체의 타입에서** 한다. 타입에 나중에 붙여도 뒤집힌다(동작 4).
4. **`property` 는 `fget`·`fset`·`fdel` 세 칸짜리 디스크립터**다. 빈 칸으로 가면 `AttributeError` 다.
5. ★ **`@x.setter` 는 새 `property` 를 만든다.** 앞의 것을 고치지 않는다. `fget` 은 물려준다.
6. ★ **`__set_name__` 은 `class` 문이 클래스를 만들 때 한 번** 불린다(3.6+). 나중에 붙이면 **안 불린다.**
7. **`__get__` 의 `obj` 자리는 클래스에서 꺼낼 때 `None`** 이다. 그 분기를 안 쓰면 `Cls.x` 가 터진다.
8. ★ **디스크립터는 클래스 칸에 하나뿐이다.** 값을 자기 안에 두면 인스턴스끼리 새어 나간다.
9. ★ **`__slots__` 가 만드는 것은 `member_descriptor` 이고 데이터 디스크립터**다(29번 동작 8).
10. **`__slots__` 와 같은 이름을 클래스 변수로 쓰면 `ValueError`**, **둘 다 비지 않은 다중 상속은 `TypeError`** 다.
11. **`__slots__` 는 그 클래스에서만 효과가 있다.** 하위 클래스가 안 쓰면 `__dict__` 가 되살아난다(29번 정본).
12. ★ **`inspect.getattr_static` 은 디스크립터도 `__getattr__` 도 안 부른다.** 「거기 있는 것」만 답한다.

**금지 사례 — 문법은 맞는데 조용히 어긋나는 것들**

```text
class Bad1:
    def __init__(self):
        self.x = property(lambda s: 1)   # ① 인스턴스에 붙였다 — 안 먹는다. 그냥 객체다

class Bad2:
    @property
    def x(self): return self._x          # ② setter 를 안 달았는데 self.x = v 를 쓴다
    def __init__(self): self.x = 1       #    -> AttributeError 로 막힌다

class Bad3:
    def __init__(self): ...
    val = MyDesc()
class Bad3b:
    val = MyDesc()                       # ③ 디스크립터 안에 self.value 로 값을 두면
                                         #    모든 인스턴스가 한 값을 나눠 쓴다 (29번 동작 3과 같은 집안)

class Bad4:
    __slots__ = ("x",)
    x = 1                                # ④ 정의 시점에 ValueError

class Bad5(HasSlotsA, HasSlotsB):        # ⑤ 둘 다 비지 않으면 정의 시점에 TypeError
    __slots__ = ()

class Bad6:
    __slots__ = ("x",)
class Bad6Sub(Bad6):
    pass                                 # ⑥ 조용하다 — __dict__ 가 되살아나 효과가 풀린다
```

★ ⑥만 **아무 말이 없다.** 나머지 다섯은 정의 시점이나 첫 접근에서 막힌다.

## 어디서 틀리나

### (1) ★★ `@property` 만 붙여 놓고 `self.x = v` 를 쓴다

`fset` 이 비었으므로 `AttributeError: property 'x' of 'C' object has no setter` 다.\
★ **`__init__` 안에서도 똑같이 막힌다** — 「생성자는 예외겠지」가 안 통한다.

### (2) ★ `@x.setter` 가 앞의 `property` 를 고친다고 안다

**새 객체를 만든다.** 앞의 것을 다른 이름으로 붙잡아 두면 **둘이 나란히 남는다**(동작 2의 ②).\
★ 그래서 `@x.setter` 를 `@property` **위에** 적으면 `x` 가 아직 없어 `NameError` 다.

### (3) ★★ `property` 를 인스턴스에 붙인다

**안 먹는다.** `p.x` 가 `property` 객체 자체로 나온다(동작 2의 ⑥).\
★ 디스크립터 프로토콜은 **클래스 칸에서 찾은 것**에만 걸린다 — [29번](../29-classes-and-attribute-lookup/2-summary.md)의 네 층 그대로다.

### (4) ★ 데이터 디스크립터의 판별식을 `__set__` 하나로 외운다

**`__delete__` 만 있어도 데이터**다(동작 4의 ④).\
★ 그때는 읽기가 이기고 **대입은 `AttributeError: __set__`** 이라는 어중간한 상태가 된다.

### (5) ★★ 디스크립터 안에 값을 둔다

`self.value = v` 로 두면 **클래스 칸에 하나뿐인 디스크립터**가 모든 인스턴스의 값을 겹쳐 쓴다.\
★ [29번](../29-classes-and-attribute-lookup/2-summary.md) 동작 3의 **클래스 변수 공유와 같은 집안**이고,
[20번](../20-mutable-default-args/2-summary.md)의 가변 기본 인자와도 같은 집안이다.\
고치는 법은 같다 — **값을 인스턴스 쪽에 둔다**(`obj.__dict__[self.name]`).

### (6) ★ `__set_name__` 이 언제나 불린다고 믿는다

**`class` 문이 만들 때만**이다. `Cls.attr = Desc()` 로 나중에 붙이면 **안 불리고** 이름이 안 채워진다(동작 3의 ⑥).

### (7) ★ `__get__` 에서 `obj is None` 분기를 안 쓴다

`Cls.x` 로 꺼내면 `obj` 가 `None` 이라 `getattr(None, ...)` 같은 것이 터진다.\
★ 관용구는 **`if obj is None: return self`** 다 — 그래야 `help()` 나 문서 생성기가 디스크립터를 볼 수 있다.

### (8) ★★★ 「`__slots__` 가 빠르다」고 적는다

**이 문서는 속도를 한 번도 안 쟀다.** 잰 것은 **크기**이고, 근거로 쓴 것은 **어느 쪽이 작나**뿐이다.\
★ 「메모리를 N배 아낀다」도 같다 — **그 수치는 이 판·이 두 클래스의 것**이다.

### (9) ★ `getsizeof` 한 번으로 결론을 낸다

**창이 얕다.** 두 인스턴스의 값이 **같게 나온다**(동작 6의 ①).\
★ `__dict__` 를 따로 세서 합쳐야 비교가 성립한다.

### (10) ★ `__slots__` 를 쓰면 상속해도 `__dict__` 가 없다고 믿는다

**하위 클래스가 안 쓰면 되살아난다.** 정본은 [29번](../29-classes-and-attribute-lookup/2-summary.md) 동작 8의 ⑤다.\
★ 예외도 경고도 없는 **유일한 조용한 자리**다.

### (11) ★ `__slots__` 에 적은 이름을 클래스 변수로도 쓴다

**정의 시점에 `ValueError`** 다. 두 물건이 클래스 칸의 한 자리를 다툰다.\
★ 기본값을 주고 싶으면 `__init__` 에서 넣거나 `property` 로 감싼다.

### (12) ★ `vars(obj)` 에 보이니 그 값이 답이라고 믿는다

**데이터 디스크립터가 있으면 진다.** [29번](../29-classes-and-attribute-lookup/2-summary.md) 동작 7이 정본이고,
여기서는 **한 이름에 세 답이 나오는 것**까지 보인다(동작 5의 ②).

### (13) ★ `getattr_static` 이 값을 준다고 믿는다

**거기 앉은 것**을 준다. `property` 면 `property` 객체이지 계산된 값이 아니다.\
★ `__getattr__` 이 만들어 주던 이름에는 **`AttributeError`** 를 낸다 — 그것이 이 창의 정확한 뜻이다.

## 구현 세부사항 대 언어 보장

세 층으로 가른다. ★ **이 주제는 「구현」 칸에 유난히 무거운 것이 하나 있다** — **메모리 절감**이다.
동작 순서·우선순위는 전부 레퍼런스에 적혀 있지만, **얼마나 아끼는가는 한 줄도 안 적혀 있다.**

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **언어 보장** | 레퍼런스가 정한 것 | 공식 문서 문장을 열어서 인용 |
| **CPython 구현** | 이 구현이 그렇게 하는 것 | 실행 로그 · `getsizeof` · 내부 타입 이름 |
| **이 판(3.12.3)의 관찰** | 이 판·이 머신에서 그랬을 뿐 | 바이트 수 · 예외 문구 |

### 언어 보장

| 사실 | 근거 |
|---|---|
| **데이터 디스크립터 > 인스턴스 칸 > 비데이터 디스크립터 > 클래스 변수** | 3.3.2.3 Invoking Descriptors |
| 데이터 디스크립터는 `__set__` **또는** `__delete__` 를 가진 것 | 3.3.2.2 Implementing Descriptors |
| 디스크립터는 **클래스 칸에 놓여야** 걸린다 | 3.3.2.3 — *"the class dictionary of the owner"* |
| `__set_name__` 은 **클래스가 만들어질 때** 불린다(3.6+) | `object.__set_name__` · PEP 487 |
| `property` 가 `fget`·`fset`·`fdel` 세 칸을 갖고 빈 칸이면 `AttributeError` | `property` 문서 |
| `getter`/`setter`/`deleter` 가 **복사본을 돌려준다** | `property` — *"Returns a new property object"* |
| `__slots__` 를 쓰면 `__dict__` 가 없고, 목록 밖 이름 대입은 `AttributeError` | 3.3.2.4 `__slots__` |
| `__slots__` 에 `'__dict__'` 를 넣으면 `__dict__` 가 생긴다 | 3.3.2.4 |
| `__slots__` 가 **클래스 변수와 충돌하면 `ValueError`** | 3.3.2.4 — *"raise ValueError"* |
| 하위 클래스가 `__slots__` 를 선언 안 하면 `__dict__` 가 **되살아난다** | 3.3.2.4 |
| `inspect.getattr_static` 은 **디스크립터 프로토콜을 안 태운다** | `inspect` 문서 |

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| ★★★ **`__slots__` 가 메모리를 아끼는 정도** | 실행 — `getsizeof` 합계. **문서에 수치가 없다** |
| `getsizeof` 가 얕아서 `__dict__` 를 안 세는 것 | 실행 — 동작 6의 ① |
| `__slots__` 가 만드는 것의 타입 이름이 `member_descriptor` | 실행 — 동작 1의 ① |
| 다중 상속 충돌 문구가 `multiple bases have instance lay-out conflict` 인 것 | 실행 — 동작 7의 ② |
| `member_descriptor` 에 `__delete__` 가 있어 세 갈고리를 다 갖춘 것 | 실행 — 동작 1의 ④ |
| 예외 **문구** 전부 | 실행 |

### 이 판(3.12.3)의 관찰

| 관찰 | 어디가 흔들리나 |
|---|---|
| `getsizeof` 의 **바이트 수 자체** | ★★★ 판·빌드·플랫폼이 바꾼다. **대소 관계만 근거로 쓴다** |
| 칸을 여덟으로 늘려도 `dict` 판 합계가 **안 바뀐 것** | `dict` 용량이 계단식이라 그렇다. 성질이 아니다 |
| `property 'x' of 'C' object has no setter` 문구 | 종류는 명세, 문구는 아니다 |
| `member_descriptor`·`ABCMeta` 같은 **내부 타입 이름** | 이름은 구현, **성질**(데이터 디스크립터)은 보장 |
| `__slots__ = "only"` 가 이름 하나가 되는 것 | 문서가 「문자열도 받는다」고만 적는다. **쪼개지지 않는 것**은 관찰이다 |

### 그래서 이렇게 적으면 틀린다

* ✗ 「`@property` 를 붙이면 읽기와 쓰기가 다 된다」\
  ○ **`fget` 만 찬다.** 쓰기는 `@x.setter` 를 따로 달아야 한다.
* ✗ 「`@x.setter` 는 그 `property` 에 `fset` 을 채운다」\
  ○ **새 `property` 를 만들어 이름에 다시 묶는다.** 앞의 것은 그대로 남는다.
* ✗ 「`property` 를 인스턴스에 붙여도 된다」\
  ○ **안 먹는다.** 클래스 칸에서 찾은 것만 디스크립터로 취급된다.
* ✗ 「데이터 디스크립터는 `__set__` 이 있는 것이다」\
  ○ **`__delete__` 만 있어도 데이터**다.
* ✗ 「`__set_name__` 은 디스크립터를 붙일 때마다 불린다」\
  ○ **`class` 문이 만들 때만**이다.
* ✗ 「`__slots__` 는 빠르다」\
  ○ ★★★ **이 문서는 속도를 안 쟀다.** 잰 것은 크기이고 근거는 **대소 관계**뿐이다.
* ✗ 「`__slots__` 는 메모리를 7배 아낀다」\
  ○ **이 판에서 이 두 클래스의 합계**가 그랬을 뿐이다. 언어가 보장한 적이 없다.
* ✗ 「`getsizeof` 로 두 인스턴스를 견주면 차이가 보인다」\
  ○ **같게 나온다.** 창이 얕아 `__dict__` 를 안 센다.
* ✗ 「`__slots__` 를 쓰면 하위 클래스도 `__dict__` 가 없다」\
  ○ **하위가 선언 안 하면 되살아난다.**
* ✗ 「`getattr_static` 은 빠른 `getattr` 이다」\
  ○ **다른 질문에 답하는 다른 창**이다. 값이 아니라 **거기 앉은 것**을 준다.

**판정 기준 한 줄**: **「누가 답하나」를 물으면 클래스 칸의 그 물건의 **타입**을 보고,
「무엇이 거기 있나」를 물으면 `getattr_static` 을 본다. 둘은 같은 질문이 아니다.**

## 언제 쓰고 언제 안 쓰나

| 상황 | 판정 |
|---|---|
| 속성 하나에 검증·계산을 붙인다 | **`property`** — 가장 싸다 |
| 읽기 전용으로 두고 싶다 | **`@property` 만 달고 setter 를 안 단다.** 막는 코드는 필요 없다 |
| 같은 검증을 속성 **여럿**에 건다 | **손으로 만든 디스크립터** + `__set_name__` |
| 그 값을 어디 둘지 정해야 한다 | ★ **인스턴스 칸에 둔다**(`obj.__dict__[self.name]`). 디스크립터 안은 공유다 |
| 클래스에서 꺼내도 터지면 안 된다 | `__get__` 에 **`if obj is None: return self`** |
| 같은 모양의 객체를 아주 많이 만든다 | **`__slots__`** — ★ 상속 사슬 전체가 선언해야 한다 |
| 믹스인을 만든다 | **`__slots__ = ()`** — 레이아웃 충돌을 안 만든다 |
| 오타로 속성이 새로 생기는 것을 막고 싶다 | `__slots__` — ★ 부수 효과이지 목적은 아니다 |
| 동적으로 속성을 붙여야 한다 | **`__slots__` 를 쓰지 않는다.** 정말 섞으려면 목록에 `'__dict__'` |
| 읽기만 하고 부작용은 피하고 싶다 | **`inspect.getattr_static`** |
| 없는 속성을 만들어 준다 | `__getattr__` — 정본은 [29번](../29-classes-and-attribute-lookup/2-summary.md) |
| 필드 여럿짜리 값 객체를 만든다 | ★ [36번](../36-dataclasses/2-summary.md) — `@dataclass(slots=True)` 가 이 주제를 대신 써 준다 |

## 핵심 문장

* ★★★ **세 장치는 서로 다른 기능이 아니라, 클래스 칸에 데이터 디스크립터를 앉히는 세 가지 방법이다.**
  `property` 는 내 함수 셋을, 디스크립터는 내 클래스를, `__slots__` 는 언어가 만든 칸을 앉힌다.
* ★★ **디스크립터는 클래스 칸에 놓여야 먹는다.** 인스턴스에 붙인 `property` 는 그냥 객체다.
* ★★ **우선순위는 값이 아니라 타입의 성질이 정한다.** 같은 객체·같은 인스턴스 칸을 두고
  `__set__` 만 붙였다 떼자 답이 왕복했다 — **`__delete__` 만 있어도 데이터다.**
* ★ **`@x.setter` 는 새 `property` 를 만든다.** `fget` 은 물려주고 껍데기만 새로 짠다.
* ★ **`__set_name__` 은 `class` 문이 만들 때 한 번** 불린다(3.6+). 나중에 붙이면 안 불린다.
* ★★ **`inspect.getattr_static` 이 이 주제의 네 번째 창이다** — 「무엇이 거기 있나」와 「무엇이 답하나」를 가른다.
  한 이름에 **세 답**(칸에 있는 값 · 답한 값 · 앉은 물건)이 나오는 자리가 있다.
* ★★★ **`__slots__` 가 무엇을 막는지는 언어 보장이고, 무엇을 아끼는지는 CPython 의 이야기다.**
  이 문서는 **크기만 재고 속도는 안 쟀다.** 근거로 쓰는 것은 **「어느 쪽이 작나」** 한 줄뿐이다.
* ★ **`__slots__` 의 경계는 정의 시점에 둘이 터지고 하나가 조용하다** —
  클래스 변수 충돌은 `ValueError`, 둘 다 비지 않은 다중 상속은 `TypeError`,
  **하위 클래스가 선언 안 하면 아무 말 없이 풀린다.**

## 관련 자료

* 목록: [python/syntax 주제 목록](../README.md) — 이 주제는 **33번**
* 선행·정본: [29-classes-and-attribute-lookup](../29-classes-and-attribute-lookup/2-summary.md) — ★★★ **우선순위 네 층의 정본.**\
  **경계**: 「`obj.x` 가 어느 칸에서 답을 얻나」와 「데이터 디스크립터가 인스턴스 칸을 이긴다」는 그쪽까지,
  여기는 「**그 칸에 무엇을 어떻게 앉히나**」부터다. `__slots__` 의 기본 동작과
  **하위 클래스에서 `__dict__` 가 되살아나는 것**도 그쪽이 정본이라 여기서는 결론만 인용했다.
* 선행: [24-decorators](../24-decorators/2-summary.md) — `@` 가 **이름에 결과를 다시 묶는** 것.\
  **경계**: 데코레이터 일반은 그쪽, 여기는 **`@x.setter` 가 새 객체를 돌려준다는 결과**만.
* 선행: [20-mutable-default-args](../20-mutable-default-args/2-summary.md) — **「한 번 만들어진 것을 여럿이 나눠 쓴다」의 정본.**\
  ★ 디스크립터 안에 값을 두면 **같은 사고**가 난다. 처방도 같다 — 만드는 시점을 인스턴스 쪽으로 옮긴다.
* 함께 보는 곳: [03-mutability-and-copying](../03-mutability-and-copying/2-summary.md) — 고치기와 새로 묶기.
* 이어지는 곳: [34-inheritance-mro-super](../34-inheritance-mro-super/2-summary.md) — 「상속·MRO·`super()`」 — ★ 이 주제가 「클래스 칸 **하나**」를 다뤘다면 그쪽은 **여러 칸을 훑는 순서**다.
* 이어지는 곳: [36-dataclasses](../36-dataclasses/2-summary.md) — 「`dataclasses`」 — ★ `@dataclass(slots=True)` 가 이 주제의 `__slots__` 를 **대신 써 준다**(3.10+).
* 이어지는 곳: [목록의 **45번 주제**](../45-functools/) 「`functools`」 — `cached_property` 가 **비데이터 디스크립터**라서
  첫 접근 뒤 인스턴스 칸에 지는 장치다. 이 문서의 네 층으로 바로 읽힌다.
* 다른 갈래: Kotlin 갈래 목록([`kotlin/syntax/README.md`](../../../kotlin/syntax/README.md))의 **16번** 「프로퍼티 — backing field」 —
  코틀린은 **프로퍼티가 문법 기본값**이고 필드가 예외다. 파이썬은 반대로 **필드가 기본값이고 `property` 가 덧칠**이다.
* 다른 갈래: Kotlin 갈래 목록([`kotlin/syntax/README.md`](../../../kotlin/syntax/README.md))의 **17번** 「위임 프로퍼티」 —
  `by` 가 파이썬의 디스크립터와 **가장 가까운 물건**이다. 코틀린은 **컴파일러가 규약을 검사**하고 파이썬은 안 한다.
* 원리: [`cs/foundations/oop-basics/`](../../../../oop-basics/) — 캡슐화 일반론.
  여기는 그 일반론을 **파이썬의 클래스 칸 구조로** 좁혀 받는다.
* 공식 문서: [Invoking Descriptors](https://docs.python.org/3.12/reference/datamodel.html#invoking-descriptors) ·
  [Implementing Descriptors](https://docs.python.org/3.12/reference/datamodel.html#implementing-descriptors) ·
  [`__slots__`](https://docs.python.org/3.12/reference/datamodel.html#slots) ·
  [`property`](https://docs.python.org/3.12/library/functions.html#property) ·
  [`inspect.getattr_static`](https://docs.python.org/3.12/library/inspect.html#inspect.getattr_static)

## 용어 풀이

* **디스크립터(descriptor)**: `__get__`·`__set__`·`__delete__` 중 하나라도 가진 객체.
  **클래스 칸에 놓였을 때만** 속성 접근을 가로챈다.\
  예: `property`·함수·`__slots__` 의 칸이 전부 이것이다.
* **데이터 디스크립터(data descriptor)**: `__get__` 과 함께 `__set__` **또는** `__delete__` 를 가진 것.\
  예: **인스턴스 칸을 이긴다.**
* **비데이터 디스크립터(non-data descriptor)**: `__get__` 만 가진 것.\
  예: 함수. **인스턴스 칸에 같은 이름이 들어오면 진다.**
* **`property`**: `fget`·`fset`·`fdel` 세 칸을 가진 표준 디스크립터.\
  예: `@property` 는 `fget` 만 채운 객체를 만든다.
* **`fget`·`fset`·`fdel`**: `property` 의 세 칸. 읽기·쓰기·지우기에 쓸 함수를 담는다.\
  예: 빈 칸으로 가면 `AttributeError` 다.
* **`__set_name__`**: 디스크립터가 **자기가 어느 이름으로 놓였는지** 받는 갈고리(3.6+).\
  예: `class` 문이 클래스를 만들 때 한 번 불린다.
* **`__slots__`**: 인스턴스의 `__dict__` 를 없애고 고정된 칸만 두는 선언.\
  예: 클래스 칸에 이름마다 `member_descriptor` 가 하나씩 생긴다.
* **`member_descriptor`**: `__slots__` 가 만드는 칸의 타입 이름. **CPython 의 이름**이다.\
  예: 성질은 데이터 디스크립터다.
* **레이아웃 충돌(instance lay-out conflict)**: 두 부모가 각자 정한 인스턴스 칸 배치를 겹칠 수 없을 때 나는 오류.\
  예: 둘 다 비지 않은 `__slots__` 를 다중 상속하면 `TypeError` 다.
* **`inspect.getattr_static`**: 디스크립터도 `__getattr__` 도 **안 부르고** 칸에 앉은 것만 꺼내 오는 함수.\
  예: `property` 면 계산값이 아니라 `property` 객체를 준다.
* **얕은 크기(shallow size)**: 그 객체 자신의 바이트 수. 가리키는 곳은 안 센다.\
  예: `sys.getsizeof` 가 재는 것이 이것이라 `__dict__` 를 따로 세야 한다.

## 더 들어가면

아래 다섯은 인출 대상 밖이지만 **전부 던져서 확인했다.** 하나(⑥)만 「못 잰 것」이다.

```python
# e33_more.py
import functools
import weakref


class Costly:
    def __init__(self):
        self.n = 0

    @functools.cached_property
    def value(self):
        self.n += 1
        print("      계산했다 (%d 번째)" % self.n)
        return 42


print("① cached_property 는 비데이터 디스크립터다")
t = functools.cached_property
print("   __get__:%s __set__:%s" % (hasattr(t, "__get__"), hasattr(t, "__set__")))
c = Costly()
print("   첫 접근 :", c.value)
print("   vars(c) :", vars(c))
print("   둘째 접근 :", c.value, " <- 로그가 없다. 인스턴스 칸이 이겼다")

print("② ★ 그래서 __slots__ 인 클래스에는 못 쓴다 — 넣을 칸이 없다")


class Slotted:
    __slots__ = ("n",)

    @functools.cached_property
    def value(self):
        return 1


try:
    Slotted().value
except TypeError as ex:
    print("   TypeError:", ex)

print("③ classmethod·staticmethod 도 디스크립터다")
for nm, t in (("function", type(lambda: 0)), ("classmethod", classmethod),
              ("staticmethod", staticmethod), ("property", property),
              ("cached_property", functools.cached_property)):
    print("   %-16s __get__:%-5s __set__:%-5s -> %s"
          % (nm, hasattr(t, "__get__"), hasattr(t, "__set__"),
             "데이터" if hasattr(t, "__set__") else "비데이터"))

print("④ ★ 내장 타입의 속성은 C 로 된 디스크립터다 — 그런데 한 종류가 아니다")
for owner, nm in ((complex, "real"), (BaseException, "__suppress_context__"),
                  (BaseException, "args"), (type, "__mro__"), (type, "__basicsize__")):
    t2 = type(vars(owner)[nm])
    print("   %-13s.%-20s -> %-18s __set__:%s"
          % (owner.__name__, nm, t2.__name__, hasattr(t2, "__set__")))
print("   ★ 고정 칸은 member_descriptor, 계산해서 답하는 것은 getset_descriptor 다")
print("   ★ 둘 다 데이터 디스크립터다 — 29번의 판별식을 그대로 통과한다")

print("⑤ __slots__ 를 쓰면 약한 참조 칸도 사라진다")


class NoRef:
    __slots__ = ("x",)


class WithRef:
    __slots__ = ("x", "__weakref__")


try:
    weakref.ref(NoRef())
except TypeError as ex:
    print("   weakref.ref(NoRef())   -> TypeError:", ex)
print("   weakref.ref(WithRef()) -> 만들어졌다 :", type(weakref.ref(WithRef())).__name__)

print("⑥ __slots__ 에 적은 순서가 무엇을 바꾸나 — getsizeof 로는 못 잰다")
import sys


class Ab:
    __slots__ = ("a", "b")


class Ba:
    __slots__ = ("b", "a")


x, y = Ab(), Ba()
x.a = x.b = y.a = y.b = 1
print("   getsizeof 가 같은가 :", sys.getsizeof(x) == sys.getsizeof(y))
print("   클래스 칸의 순서    :", Ab.__slots__, "|", Ba.__slots__)
print("   ★ 칸이 인스턴스 안에 있어 합계가 같다 — 이 창으로는 배치를 못 본다")
```
```text
===== python3 - <e33_more.py =====
① cached_property 는 비데이터 디스크립터다
   __get__:True __set__:False
      계산했다 (1 번째)
   첫 접근 : 42
   vars(c) : {'n': 1, 'value': 42}
   둘째 접근 : 42  <- 로그가 없다. 인스턴스 칸이 이겼다
② ★ 그래서 __slots__ 인 클래스에는 못 쓴다 — 넣을 칸이 없다
   TypeError: No '__dict__' attribute on 'Slotted' instance to cache 'value' property.
③ classmethod·staticmethod 도 디스크립터다
   function         __get__:True  __set__:False -> 비데이터
   classmethod      __get__:True  __set__:False -> 비데이터
   staticmethod     __get__:True  __set__:False -> 비데이터
   property         __get__:True  __set__:True  -> 데이터
   cached_property  __get__:True  __set__:False -> 비데이터
④ ★ 내장 타입의 속성은 C 로 된 디스크립터다 — 그런데 한 종류가 아니다
   complex      .real                 -> member_descriptor  __set__:True
   BaseException.__suppress_context__ -> member_descriptor  __set__:True
   BaseException.args                 -> getset_descriptor  __set__:True
   type         .__mro__              -> getset_descriptor  __set__:True
   type         .__basicsize__        -> member_descriptor  __set__:True
   ★ 고정 칸은 member_descriptor, 계산해서 답하는 것은 getset_descriptor 다
   ★ 둘 다 데이터 디스크립터다 — 29번의 판별식을 그대로 통과한다
⑤ __slots__ 를 쓰면 약한 참조 칸도 사라진다
   weakref.ref(NoRef())   -> TypeError: cannot create weak reference to 'NoRef' object
   weakref.ref(WithRef()) -> 만들어졌다 : ReferenceType
⑥ __slots__ 에 적은 순서가 무엇을 바꾸나 — getsizeof 로는 못 잰다
   getsizeof 가 같은가 : True
   클래스 칸의 순서    : ('a', 'b') | ('b', 'a')
   ★ 칸이 인스턴스 안에 있어 합계가 같다 — 이 창으로는 배치를 못 본다
(exit 0)
```

* ★★ **`functools.cached_property` 는 비데이터 디스크립터다**(①). 첫 접근 때 계산해 **인스턴스 칸에 넣고**,
  그 뒤로는 네 층 규칙에 따라 **인스턴스 칸이 이겨** 다시 안 계산된다 — 둘째 접근에 로그가 없다.
  ★ 그래서 **`__slots__` 인 클래스에는 못 쓴다**(②). 문구가 그 이유를 그대로 말한다 —
  `No '__dict__' attribute on 'Slotted' instance to cache 'value' property.`
  **캐시를 둘 칸이 없는 것**이다. 정본은 [목록의 **45번 주제**](../45-functools/)다.
* ★ **`classmethod`·`staticmethod` 도 디스크립터**다(③). 다섯을 한 표로 견주면
  **데이터인 것은 `property` 하나뿐**이고 나머지 넷은 전부 비데이터다.
  즉 **메서드류는 전부 인스턴스 칸에 진다** — [29번](../29-classes-and-attribute-lookup/2-summary.md) 동작 7의 ④가 그 결과다.
* ★★ **내장 타입의 속성은 C 로 된 디스크립터인데 한 종류가 아니다**(④).
  **고정된 칸은 `member_descriptor`**(`complex.real`·`type.__basicsize__`)이고,
  **계산해서 답하는 것은 `getset_descriptor`**(`BaseException.args`·`type.__mro__`)다.
  ★ 그런데 **둘 다 `__set__` 을 가져 데이터 디스크립터**다 — 판별식은 그대로 통과한다.
  ★ **`type.__mro__` 가 `getset_descriptor` 라는 것**은 [34번](../34-inheritance-mro-super/2-summary.md) 으로 바로 이어진다.
* ★ **`__slots__` 를 쓰면 약한 참조 칸도 사라진다**(⑤). `weakref.ref` 가
  `cannot create weak reference to 'NoRef' object` 로 막힌다.
  목록에 `'__weakref__'` 를 넣으면 다시 된다.
* ★ **`__slots__` 에 적은 순서가 메모리 배치를 정하나 — 이 창으로는 못 잰다**(⑥).
  「안 쟀다」가 아니라 「**잴 수 없다**」(제3의 상태)다 — 칸이 인스턴스 **안에** 있으므로
  `('a','b')` 판과 `('b','a')` 판의 `getsizeof` 가 **같게 나온다.**
  ★ **쪼개서 잰 조각** — 클래스 칸의 `__slots__` 튜플 순서는 적은 대로 남는다(출력의 마지막 줄).
  배치 자체를 보려면 C 구조체를 들여다보는 다른 창이 필요하고, **그 창은 이 배치에서 안 열었다.**
* ★ **메타클래스의 `__prepare__`** 로 클래스 칸 자체를 갈아끼우면 `__set_name__` 이 불리는 시점을 직접 볼 수 있다.
  ★ 이 주제에서는 **`class` 문이 끝나기 전**이라는 것만 로그로 확인했다(동작 3의 ①) — 메타클래스는 다루지 않았다.
