# python/syntax/36-dataclasses — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만.
> - [`dataclasses`](https://docs.python.org/3.12/library/dataclasses.html) — `@dataclass` 의 옵션 전부·`field`·`InitVar`·`__post_init__`
> - 같은 문서의 **mutable default** 문단 — *"will raise a ValueError if it detects an unhashable default parameter …
>   Unhashability is used to approximate mutability."* · *"This is a partial solution, but it does protect against many common errors."*
> - 같은 문서의 `kw_only`·`slots`(둘 다 **3.10** 신설) · `frozen` 이 `__setattr__`·`__delattr__` 를 더한다는 문단
> - [`inspect.signature`](https://docs.python.org/3.12/library/inspect.html#inspect.signature) — 생성된 `__init__` 을 **손으로 안 세고** 읽는 창
>
> **실행 검증** — 이 문서에 실린 출력은 전부 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.\
> ★ 던지는 형태를 하나로 고정했다 — `python3 - <파일` 로 던져 트레이스백이 `File "<stdin>", line N` 이 된다.\
> ★★★ **이 주제는 트레이스백을 한 블록도 싣지 않았다.** 던진 예외가 전부 `dataclasses.py` 를 지나
> **절대 경로가 박히기** 때문이다(직접 확인했다 — 프레임이 다섯이고 `/usr/lib/python3.12/dataclasses.py` 가 네 줄 박힌다).
> 전부 `except` 로 받아 **타입과 메시지만** 찍었다([30번](../30-repr-eq-hash-contracts/2-summary.md)이 같은 처방을 썼다).
> 그래서 이 문서에는 **줄 번호에 기대는 칸이 하나도 없다.**\
> **버전** — `dataclasses` 는 **3.7**(PEP 557)부터, **`kw_only`·`slots` 는 3.10** 부터다.
> 가변 기본값 판별 기준이 **3.11 에서 「`list`·`dict`·`set` 목록」에서 「해시 가능성」으로 바뀌었다**([20번](../20-mutable-default-args/2-summary.md)의 관찰).\
> ★ **구현 대 언어 보장 한 줄** — **무엇을 만들어 내는가와 옵션의 효과까지가 언어 보장**이고,
> **`_field_type` 같은 내부 이름·예외 문구·`<factory>` 라는 표기**는 CPython 쪽이다.\
> ★ **흔들리는 칸 / 안 흔들리는 칸** — 재대조에서 「고칠 것」과 「설계상 안 맞는 것」을 기계적으로 가르려고 미리 선언한다.
>
> | 흔들린다 | 안 흔들린다(근거로 써도 되는 칸) |
> |---|---|
> | ★ `MISSING` 의 기본 `repr` 에 **주소가 박힌다** — 그래서 **이름으로 바꿔 찍었다** | ★★ **`__dataclass_fields__` 의 순서** — `dict` 라 삽입 순서가 보장된다 |
> | `id()` 와 `0x…` 주소 — 그 한 자리를 죽여 **한 번도 안 찍었다** | `inspect.signature` 가 만든 **서명 문자열** |
> | 판이 오르면 예외 **문구**와 `_FIELD_INITVAR` 같은 **내부 이름** | 어느 던더가 **클래스 칸에 생겼나 안 생겼나** |
> | `getsizeof` 의 **바이트 수**(동작 8) — [33번](../33-property-descriptor-slots/2-summary.md)과 같은 규칙 | ★ **어느 쪽이 작나**라는 대소 관계 |
>
> ★ **이 주제의 블록에는 주소도 시간도 절대경로도 한 곳도 안 찍힌다.** 같은 판에서 다시 돌리면 **한 글자도 안 변한다**(재대조 전부 동일).\
> ★★ **순서가 보장 안 되는 출력은 하나도 없다** — 클래스 칸 비교는 전부 `sorted()` 로 찍었고,
> `__dataclass_fields__` 와 `fields()` 는 **원래 순서가 보장되는 것**이라 그대로 실었다.\
> **선행** — [20-mutable-default-args](../20-mutable-default-args/2-summary.md)(★★★ **가변 기본값의 정본**) ·
> [30-repr-eq-hash-contracts](../30-repr-eq-hash-contracts/2-summary.md)(★★★ **`__hash__` 가 어떻게 갈리는지의 정본**) ·
> [31-comparison-protocol-and-sortability](../31-comparison-protocol-and-sortability/2-summary.md)(`order=True` 가 만드는 넷과 대비) ·
> [33-property-descriptor-slots](../33-property-descriptor-slots/2-summary.md)(`slots=True` 가 만드는 것) ·
> [34-inheritance-mro-super](../34-inheritance-mro-super/2-summary.md)(상속한 필드가 줄을 서는 순서).\
> **이 사슬** — [20](../20-mutable-default-args/2-summary.md)·[30](../30-repr-eq-hash-contracts/2-summary.md)·[31](../31-comparison-protocol-and-sortability/2-summary.md)·[33](../33-property-descriptor-slots/2-summary.md)·[34](../34-inheritance-mro-super/2-summary.md)이 **전부 여기로 모인다.**
> **`dataclasses` 는 새 규칙이 아니라 앞 주제들의 결론을 자동으로 써 주는 장치다.**

## 한눈에 — 쉽게 말하면

**`@dataclass` 는 「내가 적은 필드 목록을 읽어 던더를 대신 써 주는 코드 생성기」다.**

* 내가 적는 것 — **클래스 몸통의 어노테이션** 몇 줄.
* 그것이 만드는 것 — `__init__`·`__repr__`·`__eq__`(+옵션에 따라 순서 넷·`__hash__`·`__setattr__`).
* 만든 것을 확인하는 법 — **`__dataclass_fields__` 덤프**와 **`inspect.signature`** 두 창.

```text
   @dataclass
   class Point:
       x: int                    ->  __dataclass_fields__ 에 Field 객체가 하나씩 쌓인다
       y: int = 0                     (선언 순서 그대로 — dict 라서 보장된다)
       tags: list = field(default_factory=list)
                                  |
                                  v
   생성되는 것                    확인하는 창

   __init__      ------------>   inspect.signature(Point.__init__)
   __repr__      ------------>   repr(p)
   __eq__        ------------>   p == Point(1, 2)
   __hash__ = None ---------->   ★ 30번이 정본이다
   __match_args__ ----------->   목록의 39번 주제

   ★ "무엇을 적으면 무엇이 생기나" 를 외우지 말고 이 두 창으로 읽는다
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 내가 낸 설계도 | 클래스 몸통의 어노테이션 | `Cls.__annotations__` |
| 생성기가 읽은 명세서 | `__dataclass_fields__` | 덤프하면 옵션 전부가 보인다 |
| 생성기가 뽑아낸 부품 | `__init__`·`__repr__`·`__eq__` … | `sorted(set(Cls.__dict__) - set(Plain.__dict__))` |
| 부품의 규격표 | `inspect.signature` | **손으로 안 세고 읽는다** |
| 「기본값」이 아니라 「기본값 만드는 법」 | `default_factory` | 인스턴스마다 다시 불린다 |
| 설계도에는 있는데 부품에는 없는 칸 | `InitVar` | `__init__` 서명에는 있고 `fields()` 에는 없다 |
| ★ **자물쇠를 갈아 끼운 문** | `frozen=True` | `__setattr__` 이 클래스 칸에 생긴다 |
| ★ **똑같이 생긴 새 집으로 이사** | `slots=True` | ★ 데코레이터가 **새 클래스를 돌려준다** |
| 조립 끝나고 부르는 검수원 | `__post_init__` | `__init__` 맨 끝에서 불린다 |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.\
「**`xs: list = []` 라고 썼더니 클래스가 아예 안 만들어진다**」와
「**`frozen=True` 인데 리스트 안이 바뀐다**」가 그것이다.\
앞엣것은 **[20번](../20-mutable-default-args/2-summary.md)의 함정을 에러로 승격시킨 것**이고, 뒤엣것은 **자물쇠가 얕은 것**이다.

> **필드(field)** — `@dataclass` 가 읽는 단위. **클래스 몸통의 어노테이션 한 줄**이 필드 하나다.\
> 예: 값만 대입하고 어노테이션을 안 붙이면 **필드가 아니다.**

> **`default_factory`** — 「기본값」이 아니라 「**기본값을 만드는 방법**」을 등록하는 것.\
> 예: 인스턴스마다 `list()` 가 새로 불린다. [20번](../20-mutable-default-args/2-summary.md)의 `None` 센티널과 같은 해법이다.

> **`InitVar`** — `__init__` 은 받지만 **필드가 아닌** 칸.\
> 예: `__post_init__` 의 인자로 오고 **인스턴스에는 안 남는다.**

### ★★ 이 주제가 쓰는 창 / 부적용인 창

**본체는 「무엇을 만들어 냈나」 창이다.** 산문으로 「이런 메서드가 생긴다」고 적지 않고,
**아무것도 안 붙인 클래스와 집합 차를 내어** 생긴 이름을 세고,
**`inspect.signature` 로 서명을 읽고**, **`__dataclass_fields__` 를 덤프**한다.

| 창 | 무엇을 말해 주나 | 못 보는 것 |
|---|---|---|
| ① ★★★ **클래스 칸 집합 차** | **무엇이 새로 생겼나** | 그것이 무엇을 하는지 |
| ② ★★ **`inspect.signature`** | 생성된 `__init__` 의 **정확한 서명** | 몸통에서 무슨 일이 나는지 |
| ③ ★★ **`__dataclass_fields__` 덤프 / `fields()`** | 생성기가 **무엇을 읽었나** — 옵션 전수 | `InitVar` 는 둘이 **갈린다** |
| ④ 예외 종류와 메시지 | **거부하는 자리** | 조용히 통과한 것 |
| ★ **부적용인 창** — 속도 측정 | — | ★ [33번](../33-property-descriptor-slots/2-summary.md)과 같은 규칙이다. **이 문서도 속도를 한 번도 안 쟀다** |

★★ **③이 이 주제의 네 번째 창이고 창 ②와 갈리는 자리가 있다.**
`InitVar` 는 **`__init__` 서명에는 있는데 `fields()` 에는 없다** —
그런데 **`__dataclass_fields__` 에는 있다**(동작 6). **세 창이 세 답을 준다.**

★ **제5의 상태 — 「같은 질문을 다른 창으로 물었다」.**
「`slots=True` 가 무엇을 하나」를 `__slots__` 유무로만 물을 수도 있었지만,
**`is` 로 객체 동일성을 묻는 창**으로 바꿔 물었다(동작 8).
그래야 「**새 클래스를 만들어 돌려준다**」는 것이 드러난다 — `__slots__` 만 봐서는 안 보인다.

먼저 판을 박아 둔다. 이 문서의 모든 출력은 아래 판에서 나왔다.

```python
# e36_version.py
import dataclasses
import sys

print("version_info   =", sys.version_info)
print("implementation =", sys.implementation.name)
print("platform       =", sys.platform)
print("dataclasses 에 있는 이름들 :",
      sorted(n for n in dir(dataclasses) if not n.startswith("_")))
print("kw_only 를 받나 (3.10+)    :", "kw_only" in dataclasses.dataclass.__kwdefaults__)
print("slots 를 받나   (3.10+)    :", "slots" in dataclasses.dataclass.__kwdefaults__)
```
```text
===== python3 - <e36_version.py =====
version_info   = sys.version_info(major=3, minor=12, micro=3, releaselevel='final', serial=0)
implementation = cpython
platform       = linux
dataclasses 에 있는 이름들 : ['Field', 'FrozenInstanceError', 'FunctionType', 'GenericAlias', 'InitVar', 'KW_ONLY', 'MISSING', 'abc', 'asdict', 'astuple', 'copy', 'dataclass', 'field', 'fields', 'functools', 'inspect', 'is_dataclass', 'itertools', 'keyword', 'make_dataclass', 're', 'replace', 'sys', 'types']
kw_only 를 받나 (3.10+)    : True
slots 를 받나   (3.10+)    : True
(exit 0)
```

★ `kw_only`·`slots` 가 **키워드 기본값에 실제로 있는지**를 물어봤다.
「3.10+ 다」를 기억으로 적지 않고 **이 판에 있는지 확인한 것**이다.

## 이 주제가 답하려는 질문

1. ★★★ **`@dataclass` 가 정확히 무엇을 만들어 내나** — 그리고 그것을 **어느 창으로 확인하나.**
2. ★★ **`field()` 를 어떻게 쓰나** — `default_factory`·`init`·`repr`·`compare`·`kw_only` 가 각각 무엇을 바꾸나.
3. **옵션이 켜지면 무엇이 더 생기나** — `order`·`frozen`·`slots` 가 클래스 칸에 무엇을 더 넣나.

★ 첫째·둘째가 이 주제의 인출 목표다.
「**생성된 `__init__` 의 서명을 손으로 안 세고 읽는 법**」을 대는 것이 아는 것과 들은 것의 경계다.

## 동작 방식

> 이 절이 본문이다. 그림이 먼저 오고 문장이 그 그림을 읽어 준다.

### 1. ★★★ 무엇이 생기나 — 집합 차 · 서명 · 필드 덤프

**언제 쓰나** — 이 주제의 출발점. 「`@dataclass` 를 붙이면 뭐가 생기지」를 **외우지 않고 보는 법**.

```text
   세 창을 한 블록에서 차례로 연다

   ① 아무것도 안 붙인 Plain 과 집합 차     -> 새로 생긴 이름 아홉
   ② inspect.signature(Point.__init__)   -> (self, x: int, y: int = 0, tags: list = <factory>)
   ③ __dataclass_fields__ 덤프            -> 필드마다 옵션 전수

   ★ ②의 <factory> 는 "기본값이 있다" 가 아니라 "만드는 법이 등록됐다" 는 표시다
   ★ ③은 dict 라서 선언 순서가 보장된다 — 12번 주제가 정본이다
```

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
print("   ★ MRO 를 거꾸로 훑어 모은다 — 정본은 목록의 34번 주제다")

print("⑦ asdict / astuple 은 재귀한다")
print("   asdict(Point3(1,2,[9],3))  :", dataclasses.asdict(Point3(1, 2, [9], 3)))
print("   astuple(Point3(1,2,[9],3)) :", dataclasses.astuple(Point3(1, 2, [9], 3)))
print("   replace(p, y=99)           :", dataclasses.replace(p, y=99))
```
```text
===== python3 - <e36_generated.py =====
① 클래스 칸에 무엇이 새로 생겼나
    ['__annotations__', '__dataclass_fields__', '__dataclass_params__', '__eq__', '__hash__', '__init__', '__match_args__', '__repr__', 'y']
② 생성된 __init__ 의 서명 — 손으로 안 셌다
    (self, x: int, y: int = 0, tags: list = <factory>) -> None
   Point 를 부르는 쪽 서명 : (x: int, y: int = 0, tags: list = <factory>) -> None
③ __dataclass_fields__ 덤프 — 선언 순서가 그대로다
   x      type=int          default=MISSING  factory=MISSING  init=True  repr=True  compare=True
   y      type=int          default=0        factory=MISSING  init=True  repr=True  compare=True
   tags   type=list         default=MISSING  factory=list     init=True  repr=True  compare=True
   ★ 이 순서는 dict 라서 보장된다 — 삽입 순서 보장은 12번이 정본이다
④ fields() 로 옵션을 전수로 본다
   [f.name for f in fields(Point)] : ['x', 'y', 'tags']
   MISSING 이 「기본값 없음」의 표식이다 : True
⑤ 만들어진 것이 실제로 도나
   repr(p)        : Point(x=1, y=2, tags=[])
   p == Point(1,2): True
   p == (1, 2)    : False  <- 다른 타입이면 NotImplemented 라 거짓이다
   __hash__       : None  <- 30번이 정본이다
⑥ 상속하면 부모 필드가 앞에 온다
   Point3 의 필드 : ['x', 'y', 'tags', 'z']
   Point3.__init__ : (self, x: int, y: int = 0, tags: list = <factory>, z: int = 0) -> None
   ★ MRO 를 거꾸로 훑어 모은다 — 정본은 목록의 34번 주제다
⑦ asdict / astuple 은 재귀한다
   asdict(Point3(1,2,[9],3))  : {'x': 1, 'y': 2, 'tags': [9], 'z': 3}
   astuple(Point3(1,2,[9],3)) : (1, 2, [9], 3)
   replace(p, y=99)           : Point(x=1, y=99, tags=[])
(exit 0)
```

그림 해설 — 일곱 덩어리가 「만든 것」에서 「쓰는 법」까지 간다.

* ★★ **①이 창 ①이다.** 새로 생긴 이름이 아홉 —
  `__annotations__`·`__dataclass_fields__`·`__dataclass_params__`·`__eq__`·`__hash__`·`__init__`·`__match_args__`·`__repr__`·`y`.
  ★ **`y` 가 섞여 있는 것**은 내가 기본값을 대입했기 때문이다(클래스 변수로 남는다).
  ★ **`__hash__` 가 생긴 것**이 [30번](../30-repr-eq-hash-contracts/2-summary.md)의 그 자리다 — 값이 `None` 이다(⑤).
  ★ `__match_args__` 는 `match` 문이 쓰는 것이고 정본은 목록의 **39번 주제** 다.
* ★★★ **②가 창 ②다.** 서명을 **손으로 안 세고 읽는다.**
  `(self, x: int, y: int = 0, tags: list = <factory>) -> None` 이다.
  ★ **`<factory>` 는 실제 기본값이 아니라 표시**다 — 「만드는 법이 등록됐다」는 뜻이고,
  이 표기 자체는 CPython 의 것이다.
  ★ `inspect.signature(Point)` 는 `self` 를 뺀 **부르는 쪽 서명**을 준다.
* ★★ **③이 창 ③이다.** 필드마다 옵션이 전수로 나온다.
  ★ `MISSING` 은 **「기본값 없음」의 표식**이고, **그 기본 `repr` 에는 주소가 박히므로 이름으로 바꿔 찍었다.**
  머리말의 「흔들리는 칸」 표가 그것을 미리 선언한 자리다.
* **④ — `fields()` 로도 같은 것을 읽는다.** `MISSING` 과의 `is` 비교가 「기본값 없음」의 정확한 판정식이다.
* ★ **⑤ — `p == (1, 2)` 가 거짓**이다. 생성된 `__eq__` 는 **`other.__class__` 가 같을 때만** 비교하고
  아니면 `NotImplemented` 를 준다([31번](../31-comparison-protocol-and-sortability/2-summary.md)의 반사 연산 규칙을 탄다).
  ★ **`__hash__` 가 `None`** 인 것은 [30번](../30-repr-eq-hash-contracts/2-summary.md)이 정본이라 여기서는 결론만 인용한다.
* ★★ **⑥이 [34번](../34-inheritance-mro-super/2-summary.md)으로 이어진다.** 상속하면 **부모 필드가 앞**에 온다.
  ★ 생성기가 **MRO 를 거꾸로 훑어** 필드를 모으기 때문이다. 동작 7이 그 결과의 함정을 다룬다.
* **⑦ — `asdict`·`astuple` 은 재귀하고 `replace` 는 새 객체를 만든다.**

**비용** — 코드를 안 써도 되는 값으로 **생성 규칙을 알아야** 한다.
★ **속도는 이 문서가 한 번도 안 쟀다** — 「`dataclass` 가 느리다/빠르다」는 여기 없다.

### 2. ★★★ 가변 기본값 — 거부당하고, 고치고, 그 방어가 반쪽인 것

**언제 쓰나** — [20번](../20-mutable-default-args/2-summary.md)의 직접 결론. **이 주제에서 가장 실무적인 자리다.**

[20번](../20-mutable-default-args/2-summary.md)이 「`def f(x=[])` 가 호출마다 같은 객체를 쓴다」를 정본으로 다뤘고,
**그 편의 「어디서 틀리나 (4)」가 이미 `dataclasses` 가 이것을 에러로 승격시켰다**고 적었다.
여기서는 그 에러를 **세 타입에 전수로** 던지고, 문서가 스스로 말한 「**반쪽**」까지 확인한다.

```text
   판별 기준이 "가변인가" 가 아니라 "해시할 수 있나" 다

   xs: list = []          -> 해시 못 한다 -> ValueError
   xs: dict = {}          -> 해시 못 한다 -> ValueError
   xs: set  = set()       -> 해시 못 한다 -> ValueError
   xs: tuple = ()         -> 해시 된다   -> 통과 (실제로 불변이라 맞다)
   m: MyMutable = MyMutable()
                          -> ★ 해시 된다 -> 통과. 그런데 가변이라 샌다

   ★ 문서가 스스로 partial solution 이라 적는다
     "Unhashability is used to approximate mutability"
```

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
```text
===== python3 - <e36_mutable.py =====
① 가변 기본값을 그냥 쓰면 — class 문에서 거부당한다
   list  -> ValueError | mutable default <class 'list'> for field xs is not allowed: use default_factory
   dict  -> ValueError | mutable default <class 'dict'> for field xs is not allowed: use default_factory
   set   -> ValueError | mutable default <class 'set'> for field xs is not allowed: use default_factory
② default_factory 로 고친다
   a.xs : [1] | b.xs : []
   a.xs is b.xs : False
   ★ 20번의 None 센티널과 같은 처방이다 — 만드는 시점을 호출 때로 옮긴 것
③ 팩토리는 인스턴스마다 불린다
   세 번 만든 뒤 팩토리 호출 횟수 : 3
④ 인자를 넘기면 팩토리는 안 불린다
   인자를 준 한 번의 호출 횟수 : 0
⑤ ★ 이 방어는 부분적이다 — 20번이 적은 그대로다
   MyMutable 이 해시되나 : True
   s1.m is s2.m          : True
   s2.m.items            : ['샜다']
   ★ 문서가 스스로 partial solution 이라 적는다 — 판별 기준이 해시 가능성이다
⑥ default 와 default_factory 를 같이 주면
   ValueError: cannot specify both default and default_factory
⑦ 튜플처럼 불변이면 그냥 통과한다
   Frozen().xs is Frozen().xs : True
   fields(Frozen)[0].default  : ()
(exit 0)
```

그림 해설 — 일곱 덩어리가 「막는다」에서 「반쪽이다」까지 간다.

* ★★ **①이 세 타입 전수다.** 문구가 **고치는 법까지 알려 준다** —
  `ValueError | mutable default <class 'list'> for field xs is not allowed: use default_factory`.
  ★ **`class` 문에서 막힌다** — 인스턴스를 만들지도 않았다.
* ★★ **②가 [20번](../20-mutable-default-args/2-summary.md)의 처방과 같은 것임을 보인다.**
  `a.xs is b.xs` 가 **거짓**이고 한쪽에 넣어도 다른 쪽이 안 는다.
  ★ 그쪽이 적은 그대로다 — 「**만드는 일을 `def` 시점에서 호출 시점으로 옮기는 것**」이고,
  `default_factory` 는 그 해법의 다른 표현이다.
* ★ **③·④가 팩토리의 정확한 뜻을 잰다.** 세 번 만들면 **세 번** 불리고,
  **인자를 주면 0번** 불린다. 「기본값을 만드는 법」이라는 말이 이 두 수치다.
* ★★★ **⑤가 이 절의 과녁이다.** 내가 만든 `MyMutable` 은 **가변인데 해시가 되므로 그냥 통과**한다.
  그 결과 `s1.m is s2.m` 이 참이고, 한쪽에 넣은 것이 **다른 쪽에 보인다.**
  ★ **[20번](../20-mutable-default-args/2-summary.md)이 「이 방어는 부분적」이라고 적은 자리를 여기서 던져 확인했다.**
  ★ 문서 자신이 그렇게 말한다 — *"This is a partial solution, but it does protect against many common errors."*
  ★★ 그래서 **「`dataclass` 를 쓰면 이 함정이 막힌다」는 틀린 문장**이다. **흔한 셋만 막는다.**
* **⑥ — `default` 와 `default_factory` 를 같이 주면 `ValueError`** 다.
* **⑦ — 튜플은 그냥 통과**하고 `is` 가 참이다. **불변이라 공유해도 안전**하므로 맞는 설계다.

**비용** — 흔한 셋을 공짜로 막아 준다. 대가는 **거짓 안심**이다 —
내 가변 클래스는 **통과하므로** 직접 `default_factory` 를 써야 한다.

### 3. ★★ `field()` 의 세 스위치 — 전수 격자

**언제 쓰나** — 필드 하나를 「받지만 안 보이게」 또는 「보이지만 비교에서 빼고」 싶을 때.

```text
   init · repr · compare 를 2x2x2 로 돌린다

   init=False     -> __init__ 서명에서 빠진다
   repr=False     -> repr 에서 빠진다
   compare=False  -> ★ 값이 달라도 == 가 참이 된다   <- 가장 조용한 스위치

   ★ 여덟 줄을 사람이 세지 않는다. itertools.product 로 돌려 표로 받는다
```

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
```text
===== python3 - <e36_grid.py =====
① init·repr·compare 세 스위치를 전수로 돌린다
   b 필드의 옵션        | __init__ 서명            | repr                  | a만 다를 때 ==
   --------------------------------------------------------------------------------------------
   init=True  repr=True  compare=True  | (a: int = 1, b: int = 2) -> None | G(a=1, b=2)           | False
   init=True  repr=True  compare=False | (a: int = 1, b: int = 2) -> None | G(a=1, b=2)           | True
   init=True  repr=False compare=True  | (a: int = 1, b: int = 2) -> None | G(a=1)                | False
   init=True  repr=False compare=False | (a: int = 1, b: int = 2) -> None | G(a=1)                | True
   init=False repr=True  compare=True  | (a: int = 1) -> None     | G(a=1, b=2)           | False
   init=False repr=True  compare=False | (a: int = 1) -> None     | G(a=1, b=2)           | True
   init=False repr=False compare=True  | (a: int = 1) -> None     | G(a=1)                | False
   init=False repr=False compare=False | (a: int = 1) -> None     | G(a=1)                | True

② 읽는 법 세 줄
   init=False  -> 서명에서 b 가 빠진다. 기본값이 없으면 아예 안 채워진다
   repr=False  -> repr 에서 b 가 빠진다
   compare=False -> b 가 달라도 == 가 참이다  <- 가장 조용한 스위치다

③ init=False 이고 기본값도 없으면 — 속성 자체가 안 생긴다
   NoInit(1) 이 만들어졌나 : NoInit
   vars(n)                : {'a': 1}
   n.b -> AttributeError: 'NoInit' object has no attribute 'b'
   repr(n) 을 부르면      : AttributeError: 'NoInit' object has no attribute 'b'

④ field() 에는 스위치가 더 있다
   Field 의 칸들 : ['name', 'type', 'default', 'default_factory', 'repr', 'hash', 'init', 'compare', 'metadata', 'kw_only', '_field_type']
(exit 0)
```

그림 해설.

* ★ **①의 여덟 줄이 세 스위치가 서로 독립임을 보인다.** 서명은 `init` 만, `repr` 은 `repr` 만,
  `==` 는 `compare` 만 바꾼다.
* ★★★ **`compare=False` 가 가장 위험하다.** `b` 가 `2` 와 `99` 로 **다른데 `==` 가 참**이다.
  ★ **예외도 경고도 없다.** [30번](../30-repr-eq-hash-contracts/2-summary.md)이 「계약을 어기면 조용히 틀린다」고 한 그 집안이고,
  여기는 **내가 스위치로 직접 그 상태를 만든 것**이다.
  ★ 의도한 것이면 맞는 도구다(캐시·타임스탬프 필드). 모르고 켜면 **`set`·`dict` 에서 값이 겹쳐 사라진다.**
* ★★ **③이 `init=False` 의 함정이다.** 기본값도 없으면 **속성 자체가 안 생긴다.**
  `vars(n)` 이 `{'a': 1}` 뿐이고 `n.b` 가 `AttributeError` 다.
  ★★ **그리고 `repr(n)` 까지 터진다** — 생성된 `__repr__` 이 `self.b` 를 읽기 때문이다.
  ★ **객체는 만들어졌는데 찍을 수조차 없는 상태**다. `__post_init__` 에서 채우라는 신호다(동작 6).
* ★ **④ — `Field` 가 들고 있는 칸이 열하나**다. 세 스위치 말고도 `hash`·`metadata`·`kw_only` 가 있고,
  `_field_type` 은 **내부 이름**이라 흔들리는 칸이다(동작 6에서 쓴다).

**비용** — 스위치가 싸다. 대가는 **`compare=False` 가 조용하다는 것** 하나다.

### 4. ★ `order=True` — 넷을 다 만들고, 타입이 다르면 막는다

**언제 쓰나** — 필드 순서대로 정렬하고 싶을 때. 그리고 [31번](../31-comparison-protocol-and-sortability/2-summary.md)의 `total_ordering` 과 견줄 때.

```text
   order=True 가 만드는 것과 total_ordering 이 채우는 것

   dataclass(order=True)          functools.total_ordering
   __lt__ __le__ __gt__ __ge__    __le__ __gt__ __ge__     <- __lt__ 는 내가 준다
   ★ 넷을 다 만든다               ★ 셋만 채운다
   __eq__ 도 만든다 (eq=True)     __eq__ 는 내가 준다
   __hash__ 는 None              ★ __hash__ 는 안 채운다 (31번 정본)

   비교 방식
   self  쪽 필드를 선언 순서대로 튜플로 묶고
   other 쪽 필드를 같은 순서로 묶어 튜플끼리 견준다
   ★ other.__class__ 가 다르면 NotImplemented -> TypeError
```

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
```text
===== python3 - <e36_order.py =====
① order=True 가 만드는 넷
   클래스 칸에 생긴 것 : ['__annotations__', '__dataclass_fields__', '__dataclass_params__', '__eq__', '__ge__', '__gt__', '__hash__', '__init__', '__le__', '__lt__', '__match_args__', '__repr__']
   __lt__   이 칸에 있나 : True
   __le__   이 칸에 있나 : True
   __gt__   이 칸에 있나 : True
   __ge__   이 칸에 있나 : True
   ★ 31번의 total_ordering 은 셋만 채운다 — 이쪽은 __lt__ 부터 넷을 다 만든다
② 비교는 필드 선언 순서대로 튜플을 만들어 견준다
   sorted -> [Ver(major=1, minor=2, tag=''), Ver(major=1, minor=2, tag='a'), Ver(major=1, minor=10, tag=''), Ver(major=2, minor=0, tag='')]
   Ver(1,2) < Ver(1,10) : True
   Ver(1,2) < Ver(1,2,'a') : True
   max(rows) -> Ver(major=2, minor=0, tag='')  <- 31번이 말한 대로 __gt__ 가 불린다
③ 타입이 다르면 TypeError 다
   Ver(1,2) < 1 -> TypeError: '<' not supported between instances of 'Ver' and 'int'
   Ver < Other  -> TypeError: '<' not supported between instances of 'Ver' and 'Other'  <- 모양이 같아도 막는다
④ ★ 생성된 __lt__ 가 무엇을 보는지 소스로 확인한다
   Ver.__lt__ 의 서명 : (self, other)
   Ver.__lt__ 의 코드 상수 : ('__class__', 'major', 'minor', 'tag', 'NotImplemented')
   ★ self 쪽 튜플과 other 쪽 튜플을 만들어 견준다
⑤ compare=False 인 필드는 그 튜플에서 빠진다
   Skip(1,'a') == Skip(1,'b') : True
   Skip(1,'z') <  Skip(2,'a') : True
⑥ eq=False 와 order=True 를 같이 주면
   ValueError: eq must be true if order is true
(exit 0)
```

그림 해설.

* ★ **①에서 넷이 다 클래스 칸에 있다.**
  ★★ [31번](../31-comparison-protocol-and-sortability/2-summary.md)이 정본인 `total_ordering` 은 **`__lt__` 를 내가 줘야 하고 셋만 채운다.**
  이쪽은 **필드 목록만 보고 넷을 다 만든다** — **적는 양이 다르다.**
  ★ 그쪽이 **`__hash__` 를 못 채운다**는 것도 정본이 거기이므로 여기서는 인용만 한다.
* **②가 사전식 비교를 보인다.** `Ver(1,2) < Ver(1,10)` 이 참이다 — `minor` 를 **문자열이 아니라 수로** 견준다.
  ★ `max(rows)` 가 도는 것도 [31번](../31-comparison-protocol-and-sortability/2-summary.md)의 결론대로다 — **`max` 는 `__gt__` 를 부른다.**
  생성기가 넷을 다 만들었으므로 그 경로가 막히지 않는다.
* ★★ **③이 두 갈래로 막힌다.** 정수와는 물론이고,
  ★ **필드 이름·순서·타입이 똑같은 다른 클래스 `Other` 와도 `TypeError`** 다.
  생성된 `__lt__` 가 **`other.__class__ is self.__class__` 를 보기** 때문이다 — **구조가 아니라 이름이 기준**이다.
  ★★ [35번](../35-abc-and-protocol/2-summary.md) 의 구조적 판정과 **정반대 축**이라는 것이 여기서 드러난다.
* ★ **④가 그것을 코드로 확인한다.** `Ver.__lt__.__code__.co_names` 에
  `('__class__', 'major', 'minor', 'tag', 'NotImplemented')` 가 들어 있다 —
  **무엇을 보는지 함수 자신이 들고 있다.**
* **⑤ — `compare=False` 는 그 튜플에서도 빠진다.** `==` 와 `<` 가 같은 목록을 쓴다.
* **⑥ — `eq=False` 와 `order=True` 는 같이 못 쓴다.** `eq must be true if order is true` 다.
  ★ 이 문구는 [30번](../30-repr-eq-hash-contracts/2-summary.md)이 이미 실측한 것이라 여기서는 **같은 값이 나오는지만** 확인했다.

**비용** — 넷을 공짜로 얻는 값으로 **필드 선언 순서가 곧 정렬 기준**이 된다.
★ 필드를 재배치하면 **정렬이 조용히 바뀐다.**

### 5. ★★ `frozen=True` — `__setattr__` 을 갈아끼운다

**언제 쓰나** — 값 객체를 만들 때. 그리고 「왜 대입만 막히고 리스트 안은 바뀌지」가 막힐 때.

```text
   frozen=True 가 클래스 칸에 더 넣는 것

   __setattr__   -> 무조건 FrozenInstanceError 를 던진다
   __delattr__   -> 같다

   ★ 별도 장치가 아니라 33번의 "클래스 칸에 무엇을 앉히나" 그대로다
   ★ 그래서 막는 것은 "이름을 다시 묶는 것" 뿐이다

   lk.x = 2        -> 막힌다
   lk.newone = 1   -> ★ 선언 안 한 이름도 막힌다 (__setattr__ 은 이름을 안 가린다)
   s.xs.append(1)  -> ★ 안 막힌다 (대입이 아니다)
```

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
```text
===== python3 - <e36_frozen.py =====
① frozen=True 가 클래스 칸에 무엇을 더 넣나
   frozen 쪽에만 있는 것 : ['__delattr__', '__setattr__']
   __setattr__ 이 칸에 있나 — Open : False | Locked : True
   Locked.__setattr__ 의 정체 : Locked.__setattr__
   ★ 별도 장치가 아니라 __setattr__ 을 갈아끼운 것이다
② 그래서 대입이 막힌다
   lk.x = 2 -> FrozenInstanceError: cannot assign to field 'x'
   del lk.x -> FrozenInstanceError: cannot delete field 'x'
   lk.newone = 1 -> FrozenInstanceError: cannot assign to field 'newone'
   ★ 선언 안 한 이름에도 막힌다 — __setattr__ 은 이름을 안 가린다
③ FrozenInstanceError 는 AttributeError 의 하위다
   issubclass(FrozenInstanceError, AttributeError) : True
④ ★ 얕다 — 담긴 가변 객체는 안 막는다
   s.xs : ['들어갔다']  <- frozen 인데 내용이 바뀌었다
   막는 것은 「이름을 다시 묶는 것」뿐이다
⑤ 해시는 되살아난다 — 30번이 정본이다
   Open.__hash__   : None
   Locked.__hash__ : 만들어져 있다
   {Locked(1): 0, Locked(1): 1} 의 키 개수 : 1
⑥ __post_init__ 에서 값을 넣으려면 우회해야 한다
   Derived('ab') -> Derived(raw='ab', upper='AB')
   ★ object.__setattr__ 로 갈아끼운 것을 건너뛴다
(exit 0)
```

그림 해설.

* ★★ **①이 장치의 정체다.** `frozen` 쪽에만 `__setattr__`·`__delattr__` 이 있다.
  ★ **별도 장치가 아니라 [33번](../33-property-descriptor-slots/2-summary.md)의 「클래스 칸에 무엇을 앉히나」 그대로**다.
  `Locked.__setattr__.__qualname__` 이 `Locked.__setattr__` 로 나오는 것이 그 증거다 — 생성기가 만든 함수다.
* ★ **②에서 세 가지가 다 막힌다.** 대입·삭제·**선언 안 한 새 이름**까지.
  ★ **`__setattr__` 은 이름을 안 가리므로** 오타로 새 속성을 만드는 것도 못 한다 —
  [33번](../33-property-descriptor-slots/2-summary.md)의 `__slots__` 와 **같은 부수 효과**인데 **다른 기전**이다.
* **③ — `FrozenInstanceError` 가 `AttributeError` 의 하위**다. 그래서 `except AttributeError` 로도 잡힌다.
* ★★★ **④가 가장 흔한 오해다.** `frozen` 인데 `s.xs.append(...)` 가 **된다.**
  ★ **막는 것은 「이름을 다시 묶는 것」뿐**이고, **담긴 객체를 고치는 것**은 아니다 —
  [03번](../03-mutability-and-copying/2-summary.md)의 「고치기와 새로 묶기」가 그대로 걸린다.
* ★ **⑤ — 해시가 되살아난다.** `Open.__hash__` 가 `None` 인데 `Locked` 는 만들어져 있고,
  같은 값 둘이 **키 하나**가 된다.
  ★ **[30번](../30-repr-eq-hash-contracts/2-summary.md)이 정본**이므로 여기서는 표를 다시 만들지 않고 **결론만 확인**했다.
* ★★ **⑥이 실무 관용구다.** `frozen` 에서 값을 채우려면 **`object.__setattr__` 로 갈아끼운 것을 건너뛴다.**
  ★ [29번](../29-classes-and-attribute-lookup/2-summary.md)이 `__getattribute__` 재귀를 피할 때 `object.__getattribute__` 를 쓴 것과 **같은 수법**이다.

**비용** — 불변을 얕게 얻는다. 대가는 **속을 못 막는다는 것**과
**`__post_init__` 에서 우회가 필요하다는 것** 둘이다.

### 6. ★ `__post_init__` 과 `InitVar` — 세 창이 세 답을 준다

**언제 쓰나** — 필드에서 파생된 값을 채우거나 검증할 때. 그리고 **초기화에만 쓰고 안 남길 값**이 있을 때.

```text
   InitVar 는 세 창에서 다르게 보인다

   inspect.signature(User.__init__)  -> db_key 가 "있다"
   fields(User)                      -> db_key 가 "없다"
   User.__dataclass_fields__         -> db_key 가 "있다"  ★ 세 답이 다르다
   vars(u)                           -> db_key 가 "없다"

   ★ 갈라 주는 것은 Field 의 _field_type 이다
     _FIELD  vs  _FIELD_INITVAR   (★ 내부 이름이다)
```

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
```text
===== python3 - <e36_postinit.py =====
① __post_init__ 은 __init__ 끝에 불린다
      __post_init__ 이 받은 것 : ('KEY', 7)
   repr(u) : User(name='준', token='준/KEY/7')
② InitVar 는 __init__ 서명에는 있고 필드 목록에는 없다
   서명                    : (self, name: str, db_key: dataclasses.InitVar[str], salt: dataclasses.InitVar[int] = 0) -> None
   fields()               : ['name', 'token']
   __dataclass_fields__   : ['name', 'db_key', 'salt', 'token']
   ★ 둘이 다르다 — fields() 는 InitVar 를 빼고 덤프는 들고 있다
   db_key 의 _field_type : _FIELD_INITVAR
   name   의 _field_type : _FIELD
③ 인스턴스에는 안 남는다
   vars(u) : {'name': '준', 'token': '준/KEY/7'}
   ★ db_key 도 salt 도 없다
④ InitVar 가 있는데 __post_init__ 이 없으면
   예외가 안 난다 — 받은 값이 그냥 버려진다 : {'a': 1}
⑤ __post_init__ 만 있고 InitVar 가 없으면 인자 없이 불린다
   Simple(3) -> Simple(a=3, doubled=6)
⑥ 검증을 넣는 자리도 여기다
   Positive(-1) -> ValueError: n 은 양수라야 한다: -1
   Positive(3)  -> Positive(n=3)
⑦ ★ 어노테이션을 읽기는 하는데 값이 그 타입인지는 안 본다
   Typed('정수가 아니다', 3.14) -> Typed(n='정수가 아니다', xs=3.14)
   fields 가 적은 타입 : [('n', 'int'), ('xs', 'list')]
   실제로 들어간 타입   : ['str', 'float']
   ★ 검증은 __post_init__ 에 내가 쓰는 것뿐이다
(exit 0)
```

그림 해설.

* ★ **①에서 `__post_init__` 이 `__init__` 끝에 불린다.** 로그가 `repr(u)` 보다 먼저 찍혔다.
* ★★★ **②가 이 절의 과녁이다.** 세 창이 **세 답**을 준다 —
  서명에는 `db_key`·`salt` 가 **있고**, `fields()` 에는 **없고**, `__dataclass_fields__` 에는 **있다.**
  ★ 갈라 주는 것은 `_field_type` 이고 `_FIELD_INITVAR` 대 `_FIELD` 다.
  ★ **`_` 로 시작하는 내부 이름**이라 흔들리는 칸이지만, **세 창이 갈린다는 사실 자체는 안 흔들린다.**
* ★ **③ — 인스턴스에는 안 남는다.** `vars(u)` 에 `name`·`token` 만 있다.
  「**초기화에만 쓰고 버리는 값**」이라는 것이 정확한 뜻이다.
* ★★ **④가 조용한 자리다.** `InitVar` 가 있는데 `__post_init__` 이 없으면 **예외가 안 난다.**
  받은 값이 **그냥 버려진다**(`vars` 가 `{'a': 1}`).
  ★ **문법은 맞는데 내가 쓴 값이 사라진다** — 예외도 경고도 없다.
* **⑤ — `InitVar` 가 없으면 `__post_init__` 이 인자 없이 불린다.** 파생 필드를 채우는 표준 자리다.
* ★ **⑥ — 검증을 넣는 자리도 여기다.** `__init__` 이 다 돈 뒤이므로 모든 필드를 볼 수 있다.
* ★★ **⑦이 왜 검증을 내가 써야 하는지 답한다.** `n: int` 자리에 **문자열**이, `xs: list` 자리에 **실수**가
  그냥 들어간다. `fields()` 는 `int`·`list` 라고 적어 두었는데 **실제로 들어간 것은 `str`·`float`** 다.
  ★ **어노테이션을 읽기는 하는데 값이 그 타입인지는 안 본다** — 두 일이 다르다.
  ★ [35번](../35-abc-and-protocol/2-summary.md) 과 같은 축이다 — **런타임이 안 보는 자리**이고, 보려면 사람이 써야 한다.

**비용** — 생성된 `__init__` 을 안 건드리고 뒤에 끼워 넣는다.
대가는 **④처럼 조용히 버려지는 자리**가 생긴다는 것이다.

### 7. ★ 상속 — 부모 필드가 앞이라 기본값 규칙이 걸린다

**언제 쓰나** — `dataclass` 를 상속할 때. 이 절의 `TypeError` 가 **가장 자주 부딪히는 것**이다.

```text
   필드는 "부모 먼저" 로 줄을 선다 (34번의 MRO 를 거꾸로 훑는다)

   @dataclass class Base: a: int = 0
   @dataclass class Sub(Base): b: int

   -> 줄이 (a=0, b) 가 된다
   -> def __init__(self, a=0, b) 는 파이썬 문법이 아니다
   -> TypeError 「non-default argument 'b' follows default argument」

   고치는 법 셋
   ① 자식에도 기본값을 준다
   ② kw_only=True (3.10) — 전부 키워드 전용이면 순서 제약이 사라진다
   ③ field(kw_only=True) — 필드 하나만 뒤로 뺀다
```

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
```text
===== python3 - <e36_inherit.py =====
① 부모에 기본값이 있고 자식에 없으면 — class 문에서 막힌다
   TypeError: non-default argument 'b' follows default argument
   ★ 필드가 「부모 먼저」로 줄을 서므로 (a=0, b) 가 되어 문법이 안 선다
② 자식에도 기본값을 주면 된다
   서명 : (self, a: int = 0, b: int = 0) -> None
③ ★ kw_only=True 면 그 제약이 사라진다 (3.10+)
   서명 : (self, *, a: int = 0, b: int) -> None
   KwSub(b=1) -> KwSub(a=0, b=1)
   KwSub(1) -> TypeError: KwSub.__init__() takes 1 positional argument but 2 were given
④ 필드 하나만 kw_only 로 돌릴 수도 있다
   서명 : (self, a: int = 0, *, b: int) -> None
   fields 의 kw_only : [('a', False), ('b', True)]
⑤ 같은 이름을 자식이 다시 적으면 자리는 그대로고 값만 바뀐다
   서명 : (self, a: int = 9, b: int = 1) -> None
   필드 순서 : ['a', 'b']
   Over() -> Over(a=9, b=1)
⑥ 부모가 dataclass 가 아니면 그 속성은 안 모인다
   fields(FromPlain) : ['a']
   FromPlain().z     : 1  <- 보통 상속으로는 보인다
(exit 0)
```

그림 해설.

* ★★ **①이 그 `TypeError` 다.** `non-default argument 'b' follows default argument` 는
  **`dataclasses` 가 만든 문구가 아니라 파이썬 함수 정의의 규칙**이다.
  ★ 생성기가 `__init__` 을 **소스로 만들어 컴파일하기** 때문에 그 규칙에 그대로 걸린다.
* ★★★ **③이 3.10 의 해법이다.** `kw_only=True` 면 서명이 `(self, *, a: int = 0, b: int)` 가 된다.
  ★ **`*` 뒤에는 순서 제약이 없다** — 키워드로만 받으므로 기본값 없는 것이 뒤에 와도 된다.
  ★ 대신 `KwSub(1)` 이 **`TypeError`** 다 — 위치 인자를 못 쓴다.
* **④ — 필드 하나만 `kw_only` 로 돌릴 수도 있다.** 서명이 `(self, a: int = 0, *, b: int)` 다.
  ★ `fields()` 가 `kw_only` 칸을 들고 있어 **누가 뒤로 갔는지** 읽을 수 있다.
* ★ **⑤ — 같은 이름을 자식이 다시 적으면 자리는 그대로고 값만 바뀐다.**
  필드 순서가 `['a', 'b']` 이고 `a` 의 기본값만 `9` 가 됐다.
  ★ [34번](../34-inheritance-mro-super/2-summary.md)의 「MRO 앞쪽이 이긴다」가 **값에만** 적용되고 **자리에는 안 적용**된다.
* ★ **⑥ — 부모가 `dataclass` 가 아니면 그 속성은 안 모인다.** `fields(FromPlain)` 이 `['a']` 뿐이다.
  ★ 그런데 **보통 상속으로는 보인다**(`FromPlain().z` 가 `1`).
  **「필드」와 「속성」이 갈리는 자리**다.

**비용** — 필드가 자동으로 합쳐지는 값으로 **순서를 내가 못 고른다.**
★ `kw_only` 가 3.10 에서 그 대가를 없앴다.

### 8. ★★ `slots=True` — 새 클래스를 만들어 돌려준다

**언제 쓰나** — 같은 모양의 객체를 아주 많이 만들 때.
그리고 **데코레이터가 「제자리에서 고치는 것」이 아닐 수도 있다**는 것을 볼 때.

```text
   보통 데코레이터                       slots=True

   @dataclass                            @dataclass(slots=True)
   class Row: ...                        class Row: ...

   받은 클래스를 고쳐서 그대로 돌려준다   ★ 새 클래스를 만들어 돌려준다
   dataclass(raw) is raw  -> True        dataclass(slots=True)(raw) is raw -> False

   ★ 평소에는 안 보인다 — class 문이 만든 이름에 결과가 다시 묶이기 때문이다(24번)
   ★ 데코레이터 "앞" 의 클래스를 붙잡아 둬야 보인다
```

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
```text
===== python3 - <e36_slots.py =====
① slots=True 는 ★ 새 클래스를 만들어 돌려준다 (3.10+)
   slots=True  : 데코레이터 뒤의 이름이 붙잡아 둔 것과 같은 객체인가 : False
   slots 기본값: 같은 객체인가 : True
   두 객체의 id 가 다른가 (slots 쪽) : True
   붙잡아 둔 쪽에 __slots__ 가 있나  : False
   돌려받은 쪽에 __slots__ 가 있나   : True
   ★ class 문이 만든 이름에 결과가 다시 묶이므로 평소에는 이 교체가 안 보인다
② 함수로 부르면 더 분명하다
   dataclass(slots=True)(raw) is raw : False
   raw 에 __slots__ 가 생겼나        : False
   wrapped.__slots__                : ('a', 'b')
   ★ 원본은 그대로 두고 복제본을 만든다
③ slots=False 는 제자리다
   dataclass()(raw2) is raw2 : True
④ 인스턴스에 __dict__ 가 없다
   slots 판에 __dict__ 가 있나 : False
   보통 판에 __dict__ 가 있나  : True
   s.extra = 1 -> AttributeError: 'Row' object has no attribute 'extra'
   S.__slots__ : ('a', 'b')
   클래스 칸의 a 의 정체 : member_descriptor
   ★ 33번이 실측한 member_descriptor 그대로다
⑤ 크기 — 어느 쪽이 작나만 본다
   보통 판 합계  : 344
   slots 판 합계 : 48
   어느 쪽이 작나 : slots
   ★ 속도는 이 문서가 한 번도 안 쟀다
⑥ frozen 과 같이 쓰면 둘 다 먹는다
   f.a = 1 -> FrozenInstanceError: cannot assign to field 'a'
   hasattr(f, '__dict__') : False
(exit 0)
```

그림 해설.

* ★★★ **①이 이 절의 과녁이다.** `@capture` 로 **`@dataclass` 가 받기 직전의 클래스**를 붙잡아 두니
  `Slotted is BEFORE["Slotted"]` 가 **거짓**이다. 같은 방식으로 붙잡은 `Normal` 은 **참**이다.
  ★ **붙잡아 둔 쪽에는 `__slots__` 가 없고 돌려받은 쪽에만 있다** — 원본은 그대로 두고 복제한 것이다.
  ★★ **평소에 안 보이는 이유**는 [24번](../24-decorators/2-summary.md)의 규칙 때문이다 —
  `class` 문이 만든 이름에 **데코레이터의 결과가 다시 묶이므로** 겉보기로는 같아 보인다.
* ★ **②가 함수 호출로 같은 것을 다시 보인다.** `dataclass(slots=True)(raw) is raw` 가 거짓이고
  `raw` 에는 `__slots__` 가 **안 생겼다.**
  ★★ **실무의 함정** — 데코레이터 앞뒤로 같은 클래스 객체를 들고 있다고 믿으면
  `isinstance` 검사나 등록이 **엉뚱한 클래스를 가리킨다.**
* **③ — `slots=False` 는 제자리다.** `dataclass(raw2) is raw2` 가 참이다. **`slots` 옵션만 다르다.**
* ★ **④가 [33번](../33-property-descriptor-slots/2-summary.md)과 이어진다.** 클래스 칸의 `a` 가 **`member_descriptor`** 다 —
  그 편이 실측한 것과 **같은 물건**이다. `__dict__` 가 없고 새 속성이 `AttributeError` 다.
* ★★ **⑤는 [33번](../33-property-descriptor-slots/2-summary.md)과 같은 규칙을 따른다** — **크기는 재고 속도는 안 잰다.**
  근거로 쓰는 것은 **「어느 쪽이 작나」** 한 줄뿐이고 바이트 수는 흔들리는 칸이다.
* **⑥ — `frozen` 과 같이 쓰면 둘 다 먹는다.**

**비용** — [33번](../33-property-descriptor-slots/2-summary.md)의 `__slots__` 를 손으로 안 써도 된다.
대가는 **클래스 객체가 바뀐다는 것** 하나이고, 그것이 이 절의 값이다.

### 9. ★★ 다른 언어와 견주면 — 무엇을 기준으로 읽나

**언제 쓰나** — 코틀린·자바를 아는 사람이 이 주제를 읽을 때.

Kotlin 갈래 목록([`kotlin/syntax/README.md`](../../../kotlin/syntax/README.md))의 **22번** 이 코틀린 `data class` 의 정본이고,
자바 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **14번** 이 `record` 의 정본이다.
★ **둘 다 그쪽 실측이므로 여기서는 인용만** 하고 다시 재지 않았다.

```text
                     Python @dataclass        Kotlin data class        Java record

   무엇을 읽나        클래스 몸통의 어노테이션  ★ 주 생성자 프로퍼티만    헤더의 컴포넌트
   본문 프로퍼티      ★ 어노테이션이면 필드     ★ 생기지만 아무도 안 읽는다  (헤더 밖은 필드 아님)
   가변 기본값        ★ ValueError 로 거부     (그런 개념이 없다)        (없다)
   빼는 법            field(compare=False)     ★ 본문으로 옮긴다 (암묵)   (못 뺀다)
   불변 강제          frozen=True (선택)       ★ var 도 허용 (가변 가능)  ★ 강제된다
   상속당하기         된다                     ★ 막힌다 (final)          ★ 막힌다
   순서               order=True 로 넷 생성    ★ 안 만들어 준다           안 만들어 준다
```

* ★★★ **가장 큰 차이는 「빼는 법」이다.** 코틀린은 **본문으로 옮기면 암묵적으로 빠지고**,
  파이썬은 **`field(compare=False)` 로 명시해야** 빠진다.
  ★ 코틀린 22번의 실측이 그 대가를 적었다 — 「본문 프로퍼티는 **생기지만 아무도 안 읽는 것**」이고
  `copy` 가 그것을 **초기값으로 되돌린다.**
  ★★ **파이썬 쪽은 그 사고가 안 난다** — 어노테이션을 붙이면 **반드시 필드**이기 때문이다.
  대신 **`compare=False` 를 켜면 같은 조용한 상태가 된다**(동작 3). **함정의 위치가 옮겨 갔을 뿐이다.**
* ★ **가변 기본값을 거부하는 것은 파이썬만의 자리**다. 코틀린·자바에는 **그 함정 자체가 없다** —
  기본값이 **선언 시점에 한 번 만들어지는 언어가 아니기** 때문이다([20번](../20-mutable-default-args/2-summary.md)이 정본).
* ★ **불변** — 자바 `record` 는 **강제**하고, 코틀린 `data class` 는 **`var` 를 허용**하며,
  파이썬은 **`frozen=True` 를 켜야** 한다. **방어선의 위치가 셋 다 다르다.**
* ★ **상속당하기** — 코틀린·자바는 **막고** 파이썬은 **된다**(동작 7).
  ★ 그래서 파이썬에만 **「부모 필드가 앞」 규칙과 그 `TypeError`** 가 있다.

## 문법 — 형태와 규칙

**형태 — 무엇을 적으면 무엇이 생기나**

```text
from dataclasses import dataclass, field, fields, InitVar

@dataclass(order=True, frozen=True, slots=True, kw_only=True)   # ★ slots 는 새 클래스를 돌려준다
class Row:
    a: int                                   # 필드 (어노테이션이 있어야 필드다)
    b: int = 0                               # 기본값 있는 필드
    xs: list = field(default_factory=list)   # ★ "기본값" 이 아니라 "만드는 법"
    hidden: int = field(init=False, default=0, repr=False, compare=False)
    key: InitVar[str] = ""                   # ★ 필드가 아니다. __post_init__ 으로 간다

    def __post_init__(self, key):            # InitVar 가 있으면 인자로 받는다
        object.__setattr__(self, "hidden", len(key))   # ★ frozen 이면 우회가 필요하다

옵션 기본값 — dataclass(init=True, repr=True, eq=True, order=False,
                        unsafe_hash=False, frozen=False,
                        match_args=True, kw_only=False, slots=False, weakref_slot=False)
```

```text
진단 — 무엇이 생겼나를 세 창으로 본다

sorted(set(Cls.__dict__) - set(Plain.__dict__))   ★ 새로 생긴 이름 전부
inspect.signature(Cls.__init__)                   ★ 생성된 서명. 손으로 안 센다
inspect.signature(Cls)                            부르는 쪽 서명 (self 가 빠진다)
Cls.__dataclass_fields__                          ★ InitVar 도 들어 있다 (순서 보장)
dataclasses.fields(Cls)                           ★ InitVar 는 빠진다
f.default is dataclasses.MISSING                  "기본값 없음" 의 정확한 판정식
Cls.__dataclass_params__                          켠 옵션들
Cls.__hash__                                      None 인가 (30번이 정본)
```

규칙 열둘.

1. ★ **어노테이션이 있어야 필드다.** 값만 대입하면 그냥 클래스 변수다.
2. ★★★ **가변 기본값은 `ValueError` 로 거부**된다. 판별 기준은 「**해시할 수 있나**」다.
3. ★★ **그 방어는 반쪽이다** — 해시 가능한 내 가변 클래스는 **그냥 통과**한다(문서가 *"partial solution"* 이라 적는다).
4. ★ **`default_factory` 는 인스턴스마다 불리고, 인자를 주면 안 불린다.**
5. ★ **`compare=False` 는 값이 달라도 `==` 를 참으로 만든다.** 가장 조용한 스위치다.
6. ★ **`init=False` 인데 기본값도 없으면 속성 자체가 안 생기고 `repr` 까지 터진다.**
7. ★ **`order=True` 는 넷을 다 만든다**([31번](../31-comparison-protocol-and-sortability/2-summary.md)의 `total_ordering` 은 셋만 채운다).
8. ★ **비교는 `self.__class__` 가 같을 때만** 한다. 모양이 같은 다른 클래스와도 `TypeError` 다.
9. ★★ **`frozen=True` 는 `__setattr__`·`__delattr__` 을 갈아끼운다.** 그래서 **얕다.**
10. ★ **`InitVar` 는 서명에는 있고 `fields()` 에는 없고 `__dataclass_fields__` 에는 있다.**
11. ★★ **상속하면 부모 필드가 앞**이라 기본값 규칙에 걸린다. **`kw_only=True`(3.10)가 그 제약을 없앤다.**
12. ★★ **`slots=True` 는 새 클래스를 만들어 돌려준다**(3.10). `is` 로 확인된다.

**금지 사례 — 문법은 맞는데 조용히 어긋나는 것들**

```text
@dataclass
class A:
    xs: list = []                  # ① class 문에서 ValueError — 고치는 법까지 알려 준다

@dataclass
class B:
    m: MyMutable = MyMutable()     # ② ★ 통과한다. 해시가 되기 때문이다. 조용히 공유된다

@dataclass
class C:
    a: int = 1
    b: int = field(compare=False)  # ③ b 가 달라도 == 가 참. set/dict 에서 겹쳐 사라진다

@dataclass
class D:
    a: int
    b: int = field(init=False)     # ④ b 가 안 채워진다. repr(D(1)) 까지 AttributeError

@dataclass
class E:
    a: int
    k: InitVar[int] = 0            # ⑤ __post_init__ 이 없다 — 받은 값이 조용히 버려진다

@dataclass(frozen=True)
class F:
    xs: list = field(default_factory=list)
                                   # ⑥ f.xs.append(1) 은 막히지 않는다. frozen 은 얕다

Saved = SomeClass
@dataclass(slots=True)             # ⑦ 데코레이터가 새 클래스를 돌려준다 — Saved 는 옛 것을 가리킨다
class SomeClass: ...
```

★ ②·③·⑤·⑥·⑦이 **아무 말이 없다.** ①과 ④만 터진다(④는 늦게).

## 어디서 틀리나

### (1) ★★★ 「`dataclass` 를 쓰면 가변 기본값 함정이 막힌다」로 안다

**흔한 셋만 막는다.** 판별 기준이 「해시할 수 있나」라서 **내 가변 클래스는 통과**한다(동작 2의 ⑤).\
★ 문서 자신이 *"a partial solution"* 이라 적는다. 정본은 [20번](../20-mutable-default-args/2-summary.md)이다.

### (2) ★★ `field(compare=False)` 를 가볍게 켠다

**값이 달라도 `==` 가 참**이 된다. 예외도 경고도 없다.\
★ `set`·`dict` 에 넣으면 **값이 겹쳐 하나가 사라진다** — [30번](../30-repr-eq-hash-contracts/2-summary.md)의 그 집안이다.

### (3) ★ `init=False` 에 기본값을 안 준다

**속성 자체가 안 생긴다.** 게다가 **`repr()` 까지 `AttributeError`** 다(동작 3의 ③).\
★ `__post_init__` 에서 채우거나 `default` 를 같이 준다.

### (4) ★★ `frozen=True` 면 속까지 불변이라고 믿는다

**얕다.** `f.xs.append(...)` 는 막히지 않는다.\
★ 막는 것은 「**이름을 다시 묶는 것**」뿐이다 — [03번](../03-mutability-and-copying/2-summary.md)의 구분 그대로다.

### (5) ★ `frozen` 안에서 `self.x = ...` 로 파생값을 채운다

`__post_init__` 안에서도 **막힌다.** `object.__setattr__(self, ...)` 로 우회한다(동작 5의 ⑥).

### (6) ★★ `InitVar` 를 쓰고 `__post_init__` 을 안 쓴다

**예외가 안 난다.** 받은 값이 **그냥 버려진다**(동작 6의 ④).\
★ 「내가 넘긴 인자가 어디로 갔지」가 안 풀리는 자리다.

### (7) ★ `fields()` 로 `InitVar` 를 찾는다

**없다.** `__dataclass_fields__` 에는 있다 — **세 창이 세 답을 준다**(동작 6의 ②).

### (8) ★★ 상속에서 자식 필드에 기본값을 안 준다

**`TypeError: non-default argument 'b' follows default argument`** 다.\
★ 그것은 `dataclasses` 의 문구가 아니라 **파이썬 함수 정의의 규칙**이다.
★ 3.10 부터는 `kw_only=True` 로 제약 자체를 없앨 수 있다.

### (9) ★ 모양이 같은 다른 dataclass 와 비교한다

**`TypeError`** 다. 생성된 비교는 **`self.__class__` 가 같을 때만** 한다(동작 4의 ③).\
★ **구조가 아니라 이름이 기준**이다 — [35번](../35-abc-and-protocol/2-summary.md) 의 구조적 판정과 정반대 축이다.

### (10) ★★ `slots=True` 를 붙이고 데코레이터 앞의 클래스를 들고 있는다

**다른 객체다.** `is` 가 거짓이다(동작 8의 ①).\
★ 등록·`isinstance` 검사가 **엉뚱한 클래스를 가리킨다.**

### (11) ★ 어노테이션 없이 값만 대입한다

**필드가 아니다.** `__init__` 에도 `repr` 에도 안 들어간다. 그냥 클래스 변수다.

### (12) ★ `@dataclass` 를 붙였으니 `set` 에 들어간다고 믿는다

**기본값은 해시 불가**다. 정본은 [30번](../30-repr-eq-hash-contracts/2-summary.md)이고, 키로 쓸 것이면 **`frozen=True`** 다.

### (13) ★ `order=True` 가 `total_ordering` 과 같은 일을 한다고 믿는다

**적는 양이 다르다.** `total_ordering` 은 **`__lt__` 를 내가 줘야 하고 셋만 채운다.**
`order=True` 는 **필드 목록만 보고 넷을 다 만든다.**\
★ 둘 다 `__hash__` 는 못 채운다는 것은 [31번](../31-comparison-protocol-and-sortability/2-summary.md)이 정본이다.

## 구현 세부사항 대 언어 보장

세 층으로 가른다. ★ **이 주제의 「언어 보장」은 표준 라이브러리 문서가 정한 것**이고,
`dataclasses` 는 언어 문법이 아니라 **모듈**이라는 점이 다른 주제와 갈린다 —
그래서 「언어 보장」이라기보다 「**이 모듈의 계약**」으로 읽어야 한다.

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **모듈 계약(언어 보장에 해당)** | `dataclasses` 문서가 정한 것 | 문서 문장을 열어서 인용 |
| **CPython 구현** | 이 구현이 그렇게 하는 것 | 실행 · 내부 이름 |
| **이 판(3.12.3)의 관찰** | 이 판에서 그랬을 뿐 | 예외 문구 · 바이트 수 |

### 모듈 계약

| 사실 | 근거 |
|---|---|
| 필드는 **클래스 몸통의 어노테이션**에서 모인다 | `dataclasses` 문서 |
| 가변(해시 불가) 기본값은 **`ValueError`** 로 거부된다 | *"will raise a ValueError if it detects an unhashable default parameter"* |
| ★★ 그 방어가 **부분적**이다 | *"This is a partial solution, but it does protect against many common errors."* |
| 판별이 **해시 가능성으로 가변성을 근사**한다 | *"Unhashability is used to approximate mutability."* |
| `default_factory` 는 **기본값이 필요할 때마다** 불린다 | 문서 |
| `order=True` 가 `__lt__`·`__le__`·`__gt__`·`__ge__` 넷을 만든다 | 문서 |
| 비교는 **같은 클래스일 때만**, 아니면 `NotImplemented` | 문서 |
| `eq=False` 에 `order=True` 면 `ValueError` | 문서 |
| `frozen=True` 가 `__setattr__`·`__delattr__` 을 더한다 | 문서 |
| `InitVar` 는 **필드가 아니고** `__post_init__` 으로 간다 | 문서 |
| 상속하면 **부모 필드가 앞**에 온다(MRO 를 거꾸로) | 문서 |
| `kw_only`·`slots` 는 **3.10** 신설 | 문서의 *Changed in version 3.10* |

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| ★ `MISSING` 의 기본 `repr` 에 **주소가 박히는 것** | 실행 — 그래서 **이름으로 바꿔 찍었다** |
| `<factory>` 라는 서명 표기 | 실행 — `inspect` 와 `dataclasses` 가 합의한 표기다 |
| `_FIELD`·`_FIELD_INITVAR` 라는 **내부 이름** | 실행 — `_` 로 시작한다 |
| `Field.__slots__` 가 열한 칸인 것 | 실행 |
| `Ver.__lt__.__code__.co_names` 로 **무엇을 보는지** 읽을 수 있는 것 | 실행 — 생성기가 소스를 만들어 컴파일하기 때문 |
| `non-default argument … follows default argument` 가 **파이썬 함수 규칙의 문구**인 것 | 실행 |
| `slots=True` 가 **새 클래스**를 돌려주는 것 | 실행 — ★ 문서는 「`__slots__` 를 더한다」까지만 적는다 |
| 예외 **문구** 전부 | 실행 |

### 이 판(3.12.3)의 관찰

| 관찰 | 어디가 흔들리나 |
|---|---|
| `getsizeof` 의 **바이트 수**(동작 8의 ⑤) | ★ 판·빌드가 바꾼다. **대소 관계만** 근거다 |
| 예외 문구 여섯 개 전부 | 종류는 계약, 문구는 아니다 |
| `dataclasses` 모듈이 노출하는 **이름 목록** | 판마다 늘어난다 |
| `_field_type` 의 값 이름 | 내부 이름이다 |
| `InitVar` 의 타입이 서명에 `dataclasses.InitVar[str]` 로 찍히는 것 | 표기의 일이다 |

### 그래서 이렇게 적으면 틀린다

* ✗ 「`dataclass` 를 쓰면 가변 기본값 함정이 막힌다」\
  ○ ★★★ **흔한 셋만 막는다.** 해시 가능한 내 가변 클래스는 통과한다. 문서가 *"partial solution"* 이라 적는다.
* ✗ 「판별 기준은 가변인가 아닌가다」\
  ○ **해시할 수 있나**다. 문서가 *"approximate"* 라는 낱말을 쓴다.
* ✗ 「`frozen=True` 면 속까지 불변이다」\
  ○ **얕다.** 막는 것은 이름을 다시 묶는 것뿐이다.
* ✗ 「`frozen` 은 특별한 불변 장치다」\
  ○ **`__setattr__` 을 갈아끼운 것**이다. [33번](../33-property-descriptor-slots/2-summary.md)의 규칙 위에 선다.
* ✗ 「`compare=False` 는 `repr` 에서만 뺀다」\
  ○ **`==` 와 `<` 에서 뺀다.** `repr` 은 `repr=False` 가 따로 있다.
* ✗ 「`InitVar` 는 `fields()` 에 나온다」\
  ○ **안 나온다.** `__dataclass_fields__` 에는 나온다.
* ✗ 「`InitVar` 를 쓰면 `__post_init__` 이 필수다」\
  ○ **없어도 안 터진다.** 값이 조용히 버려진다.
* ✗ 「`order=True` 는 `total_ordering` 과 같다」\
  ○ **넷을 다 만든다.** `total_ordering` 은 `__lt__` 를 받아 셋을 채운다([31번](../31-comparison-protocol-and-sortability/2-summary.md) 정본).
* ✗ 「모양이 같으면 비교된다」\
  ○ **`self.__class__` 가 같아야** 한다. 구조가 아니라 이름이 기준이다.
* ✗ 「`slots=True` 는 그 클래스에 `__slots__` 를 더한다」\
  ○ ★★ **새 클래스를 만들어 돌려준다.** `is` 로 확인된다.
* ✗ 「`@dataclass` 만 붙이면 `set` 에 들어간다」\
  ○ **기본값은 해시 불가**다([30번](../30-repr-eq-hash-contracts/2-summary.md) 정본).

**판정 기준 한 줄**: **「무엇이 생겼나」는 집합 차와 `inspect.signature` 로 보고,
「생성기가 무엇을 읽었나」는 `__dataclass_fields__` 로 본다. 그 둘이 갈리는 자리가 `InitVar` 다.**

## 언제 쓰고 언제 안 쓰나

| 상황 | 판정 |
|---|---|
| 필드 몇 개짜리 값 객체 | **`@dataclass`** — 세 던더가 공짜다 |
| `set`·`dict` 키로 쓴다 | **`@dataclass(frozen=True)`** — 정본은 [30번](../30-repr-eq-hash-contracts/2-summary.md) |
| 리스트·딕트 필드가 있다 | ★ **`field(default_factory=...)`** — 반드시 |
| 내가 만든 가변 클래스가 기본값이다 | ★★ **`default_factory` 를 직접 쓴다.** 언어가 안 막아 준다 |
| 필드 순서대로 정렬한다 | **`order=True`** — ★ 필드를 재배치하면 정렬이 바뀐다 |
| 비교 기준이 필드 순서와 다르다 | ★ **`__lt__` 를 직접 쓴다.** `order=True` 와 같이 쓰면 `TypeError` ([30번](../30-repr-eq-hash-contracts/2-summary.md) 실측) |
| 캐시·타임스탬프 필드를 비교에서 뺀다 | `field(compare=False)` — ★ **조용하다는 것을 안다** |
| 파생값을 채운다 | **`__post_init__`** — ★ `frozen` 이면 `object.__setattr__` |
| 초기화에만 쓰고 안 남길 값이 있다 | **`InitVar`** — ★ `__post_init__` 을 반드시 같이 쓴다 |
| 검증을 넣는다 | **`__post_init__`** — 모든 필드가 채워진 뒤다 |
| 아주 많이 만든다 | **`slots=True`**(3.10) — ★ **클래스 객체가 바뀐다** |
| 상속해서 필드를 더한다 | ★ **`kw_only=True`**(3.10) 가 순서 제약을 없앤다 |
| 튜플처럼 쓰고 싶다 | 목록의 **38번 주제** — `NamedTuple` 은 **런타임 정체가 튜플**이다 |
| 열거형이 필요하다 | 목록의 **37번 주제** |
| 검증·직렬화가 본업이다 | ★ `dataclasses` 는 **검증을 안 한다.** 외부 라이브러리 영역이다 |

## 핵심 문장

* ★★★ **`@dataclass` 는 새 규칙이 아니라 앞 주제들의 결론을 자동으로 써 주는 장치다** —
  [20번](../20-mutable-default-args/2-summary.md)의 가변 기본값, [30번](../30-repr-eq-hash-contracts/2-summary.md)의 `__hash__`,
  [31번](../31-comparison-protocol-and-sortability/2-summary.md)의 순서, [33번](../33-property-descriptor-slots/2-summary.md)의 `__slots__`,
  [34번](../34-inheritance-mro-super/2-summary.md)의 MRO 가 전부 여기로 모인다.
* ★★★ **무엇이 생겼는지는 외우지 말고 세 창으로 읽는다** —
  **클래스 칸 집합 차** · **`inspect.signature`** · **`__dataclass_fields__` 덤프.**
  그 셋이 갈리는 자리가 **`InitVar`** 다(서명에 있고 `fields()` 에 없고 덤프에 있다).
* ★★★ **가변 기본값을 `ValueError` 로 거부하는데 그 방어는 반쪽이다.**
  판별 기준이 「**해시할 수 있나**」라서 **해시 가능한 내 가변 클래스는 그냥 통과**한다.
  문서 자신이 *"partial solution"* 이라 적는다.
* ★★ **`default_factory`** 는 「기본값」이 아니라 「**기본값을 만드는 법**」이다 —
  인스턴스마다 불리고, **인자를 주면 안 불린다.**
* ★★ **`compare=False` 가 가장 조용한 스위치다.** 값이 달라도 `==` 가 참이 되고 예외도 경고도 없다.
* ★★ **`frozen=True` 는 `__setattr__` 을 갈아끼운 것**이라 **얕다.** 담긴 리스트 안은 안 막는다.
  대신 **선언 안 한 이름에도 막힌다** — `__setattr__` 은 이름을 안 가린다.
* ★ **`order=True` 는 넷을 다 만든다**([31번](../31-comparison-protocol-and-sortability/2-summary.md)의 `total_ordering` 은 셋만 채운다).
  비교는 **`self.__class__` 가 같을 때만** 한다 — **구조가 아니라 이름이 기준**이다.
* ★★ **상속하면 부모 필드가 앞**이라 「기본값 뒤에 무기본」이 되어 `TypeError` 다.
  **`kw_only=True`(3.10)가 그 제약을 없앤다** — `*` 뒤에는 순서 규칙이 없기 때문이다.
* ★★ **`slots=True` 는 새 클래스를 만들어 돌려준다**(3.10). 평소에는 안 보이고,
  **데코레이터 앞의 클래스를 붙잡아 둬야** `is` 로 드러난다.
* ★ **크기는 재고 속도는 안 쟀다** — [33번](../33-property-descriptor-slots/2-summary.md)과 같은 규칙이다.

## 관련 자료

* 목록: [python/syntax 주제 목록](../README.md) — 이 주제는 **36번**
* 선행·정본: [20-mutable-default-args](../20-mutable-default-args/2-summary.md) — ★★★ **가변 기본값의 정본.**\
  **경계**: 「`def` 가 실행되는 문장이라 기본값이 함수당 하나다」와 `None` 센티널은 그쪽까지,
  여기는 「**그 함정을 `dataclasses` 가 어떻게 에러로 승격시켰고 왜 반쪽인가**」부터다.
  ★ 그쪽이 「이어지는 곳」으로 이 주제를 가리키고 있고, **그 고리를 여기서 닫았다**(동작 2의 ⑤).
* 선행·정본: [30-repr-eq-hash-contracts](../30-repr-eq-hash-contracts/2-summary.md) — ★★★ **`__hash__` 가 어떻게 갈리는지의 정본.**\
  **경계**: 네 옵션 조합 표와 **데코레이터·내 메서드 충돌이 이름마다 다른 것**(`__hash__`·`__lt__` 는 터지고
  `__eq__`·`__repr__` 은 조용히 내 것이 이긴다)은 전부 그쪽이다.
  여기는 **`field`·`default_factory`·`order`·`frozen`·`slots` 까지** 넓혀 받고, `__hash__` 는 **결론만 인용**했다.
* 선행·정본: [31-comparison-protocol-and-sortability](../31-comparison-protocol-and-sortability/2-summary.md) — ★ **`total_ordering` 이 못 채우는 셋의 정본.**\
  **경계**: `__lt__` 하나로 정렬이 되는 것, `max` 가 `__gt__` 를 부르는 것은 그쪽,
  여기는 **`order=True` 가 넷을 다 만든다는 대비**만.
* 선행: [33-property-descriptor-slots](../33-property-descriptor-slots/2-summary.md) — `__slots__` 와 `member_descriptor`.\
  **경계**: `__slots__` 의 경계와 크기 측정 규칙은 그쪽, 여기는 **`slots=True` 가 새 클래스라는 것**만.
* 선행: [34-inheritance-mro-super](../34-inheritance-mro-super/2-summary.md) — 필드가 **MRO 를 거꾸로 훑어** 모이는 것.
* 선행: [03-mutability-and-copying](../03-mutability-and-copying/2-summary.md) — `frozen` 이 왜 얕은가.
* 함께 보는 곳: [12-dict-and-key-requirements](../12-dict-and-key-requirements/2-summary.md) —
  `__dataclass_fields__` 의 **순서가 보장되는 근거**가 그쪽이다.
* 이어지는 곳: 목록의 **38번 주제** 「`namedtuple`·`NamedTuple`·`TypedDict`」 —
  ★ **런타임 정체가 갈리는 대비**다. `NamedTuple` 은 진짜 튜플이고 `dataclass` 는 보통 클래스다.
* 이어지는 곳: 목록의 **37번 주제** 「`enum`」 · 목록의 **39번 주제** 「`match` 문」 —
  ★ `__match_args__` 가 이 주제에서 자동으로 생겼다(동작 1의 ①).
* 이어지는 곳: 목록의 **40번 주제** 「타입 힌트의 런타임 의미」 —
  ★★ **`dataclasses` 는 어노테이션을 실제로 읽는 드문 장치**다. 「힌트는 실행을 안 바꾼다」의 **예외**가 여기다.
* 대비: Kotlin 갈래 목록([`kotlin/syntax/README.md`](../../../kotlin/syntax/README.md))의 **22번** 「`data class`」 —
  ★ **빼는 법이 정반대**다. 코틀린은 **본문으로 옮기면 암묵적으로 빠지고** 파이썬은 **명시해야** 빠진다.\
  **경계**: 코틀린 쪽 실측(`copy` 가 본문 프로퍼티를 초기값으로 되돌리는 것 등)은 전부 그쪽이고 여기서는 인용만 했다.
* 대비: 자바 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **14번** 「`record`」 —
  ★ 자바는 **불변을 강제**하고 파이썬은 **`frozen=True` 를 켜야** 한다.
* 대비: C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **18번** 「`record`」 —
  같은 자리의 또 하나. ★ **아직 폴더가 없다.**
* 공식 문서: [`dataclasses`](https://docs.python.org/3.12/library/dataclasses.html) ·
  [`inspect.signature`](https://docs.python.org/3.12/library/inspect.html#inspect.signature) ·
  [PEP 557](https://peps.python.org/pep-0557/)

## 용어 풀이

* **필드(field)**: `@dataclass` 가 읽는 단위. **클래스 몸통의 어노테이션 한 줄**이 필드 하나다.\
  예: 값만 대입하면 필드가 아니라 그냥 클래스 변수다.
* **`Field` 객체**: 필드 하나의 옵션을 담은 객체. `fields()` 가 이것들을 준다.\
  예: `name`·`type`·`default`·`default_factory`·`repr`·`hash`·`init`·`compare`·`metadata`·`kw_only` 열 칸 + 내부 칸 하나.
* **`MISSING`**: 「기본값 없음」을 나타내는 표식 객체.\
  예: `f.default is MISSING` 이 정확한 판정식이다. ★ 기본 `repr` 에 **주소가 박힌다.**
* **`default_factory`**: 「기본값」이 아니라 「**기본값을 만드는 방법**」.\
  예: 인스턴스마다 불리고, 인자를 주면 안 불린다.
* **`InitVar`**: `__init__` 은 받지만 **필드가 아닌** 칸.\
  예: `__post_init__` 으로 가고 **인스턴스에는 안 남는다.**
* **`__post_init__`**: `__init__` 맨 끝에 불리는 갈고리.\
  예: 파생값 채우기와 검증의 자리다.
* **`frozen`**: `__setattr__`·`__delattr__` 을 갈아끼워 대입을 막는 옵션.\
  예: **얕다.** 담긴 리스트 안은 안 막는다.
* **`FrozenInstanceError`**: `frozen` 에서 대입할 때 나는 예외. **`AttributeError` 의 하위**다.
* **`kw_only`**(3.10): 필드를 **키워드 전용**으로 만드는 옵션.\
  예: `*` 뒤로 가므로 **기본값 순서 제약이 사라진다.**
* **`slots`**(3.10): `__slots__` 를 붙인 **새 클래스**를 만들어 돌려주는 옵션.\
  예: `is` 로 보면 원본과 다른 객체다.
* **얕은 불변(shallow immutability)**: 이름을 다시 묶는 것만 막고 담긴 객체는 안 막는 것.\
  예: `frozen=True` 가 그것이다.

## 더 들어가면

* ★ **`dataclasses.make_dataclass`** 로 런타임에 dataclass 를 만들 수 있다.
  동작 8의 ②가 그것과 가까운 일을 손으로 했다 — `type()` 으로 만든 클래스에 `dataclass(...)` 를 함수로 걸었다.
* ★ **`field(metadata={...})`** 는 생성기가 **안 보는 칸**이다. 직렬화 라이브러리가 쓰라고 비워 둔 자리이고,
  `Field.__slots__` 목록(동작 3의 ④)에 그 이름이 있다.
* ★★ **`dataclasses` 는 어노테이션을 실제로 읽는 드문 장치다.** 목록의 **40번 주제** 가
  「힌트는 실행을 안 바꾼다」의 정본인데, **이 모듈이 그 예외**다.
  ★ 그래서 `from __future__ import annotations` 를 쓰면 `f.type` 이 **문자열**이 된다 —
  이 문서의 블록은 그 import 를 안 썼으므로 `f.type.__name__` 이 실제 타입 이름을 줬다(동작 1의 ③).
* ★ **`weakref_slot`**(3.11)은 `slots=True` 와 같이 쓸 때 `__weakref__` 칸을 남긴다 —
  [33번](../33-property-descriptor-slots/2-summary.md)의 「더 들어가면」이 실측한 그 칸이다.
* ★ **`KW_ONLY` 센티널** — `_: KW_ONLY` 한 줄을 넣으면 **그 뒤 필드 전부**가 키워드 전용이 된다.
  동작 7의 ③·④가 클래스 단위와 필드 단위를 다뤘고, 이것은 **그 중간**이다.
* ★★ **`dataclass` 는 검증을 하지 않는다.** 타입 어노테이션을 **읽기는 하는데 값이 그 타입인지는 안 본다** —
  동작 6의 ⑦이 그 실측이다. `n: int` 자리에 문자열이, `xs: list` 자리에 실수가 그냥 들어간다.
  ★ 그 자리가 [35번](../35-abc-and-protocol/2-summary.md) 과 같은 축이다 — **런타임이 안 보는 것**이고, 보려면 `__post_init__` 에 직접 쓴다.
