# python/syntax/29-classes-and-attribute-lookup — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만.
> - [3.2.10. Custom classes](https://docs.python.org/3.12/reference/datamodel.html#custom-classes) — 클래스 칸에서 못 찾으면 **조상으로 이어지는 것**, 그리고 그 순서가 **C3** 라는 것
> - [3.2.11. Class instances](https://docs.python.org/3.12/reference/datamodel.html#class-instances) — *"A class instance has a namespace implemented as a dictionary which is the **first place** in which attribute references are searched."*
> - [3.3.2. Customizing attribute access](https://docs.python.org/3.12/reference/datamodel.html#customizing-attribute-access) — `__getattr__` 은 **실패했을 때만**, `__getattribute__` 는 **무조건**
> - [3.3.2.3. Invoking Descriptors](https://docs.python.org/3.12/reference/datamodel.html#invoking-descriptors) — **우선순위 네 층**이 한 문장에 적혀 있다
> - [3.3.2.4. `__slots__`](https://docs.python.org/3.12/reference/datamodel.html#slots) · [`super()`](https://docs.python.org/3.12/library/functions.html#super) — *"The search starts from the class right after the type."*
>
> **실행 검증** — 이 문서에 실린 출력은 전부 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.\
> ★ 던지는 형태를 하나로 고정했다 — `python3 - <파일` 로 던져 트레이스백이 `File "<stdin>", line N` 이 된다.
> ★★ **캐럿은 예외 종류에 달렸다** — 실행 중 예외는 소스 줄도 `^` 캐럿도 안 나오고, `SyntaxError` 라야 둘 다 나온다.
> ★★ **다만 이 주제는 트레이스백을 한 블록도 싣지 않았다** — 던진 예외 셋을 전부 `except` 로 잡아
> **타입과 메시지만** 찍었기 때문이다. 그래서 이 문서에는 **줄 번호에 기대는 칸이 하나도 없다.**
> (사슬의 [30번](../30-repr-eq-hash-contracts/2-summary.md)·[32번](../32-container-protocol/2-summary.md)에는 트레이스백이 있다.)\
> **버전** — 여기 나오는 장치는 전부 2.x 시절에 들어온 것이다.
> 공식 문서가 C3 를 설명하며 가리키는 글의 제목이 **The Python 2.3 Method Resolution Order** 이고,
> `__slots__`·디스크립터·`__getattribute__` 는 새 스타일 클래스(2.2)와 함께 왔다.
> **3.10\~3.13 사이에서 갈리는지는 이번에 확인하지 않았다** — 이 머신에 3.12.3 한 판뿐이다.\
> **구현 대 언어 보장 한 줄** — **탐색 순서(인스턴스 → 클래스 → MRO)와 디스크립터 우선순위와 C3 까지가 언어 보장**이고,
> **그 칸들을 `vars()`·`__dict__`·`__mro__` 로 들여다볼 수 있다는 것과 거기 보이는 내부 타입 이름은 CPython 쪽**이다.\
> ★ **흔들리는 칸 / 안 흔들리는 칸** — 재대조에서 「고칠 것」과 「설계상 안 맞는 것」을 기계적으로 가르려고 미리 선언한다.
>
> | 흔들린다 | 안 흔들린다(근거로 써도 되는 칸) |
> |---|---|
> | `id()` 와 `0x…` 주소 — **그래서 이 배치는 한 번도 안 찍었다** | 예외 **종류** · `(exit N)` |
> | 해시값 자체 — 이 주제는 해시를 안 쓴다 | `vars()` 와 `__dict__` 의 **내용** |
> | 판이 오르면 예외 **문구**와 `member_descriptor` 같은 **내부 타입 이름** | **호출 로그의 순서** · 어느 갈고리가 **불렸나 안 불렸나** |
> | — | `__mro__` 의 **순서** · 어느 칸에서 답이 나왔나 |
>
> ★ **`sys.flags.hash_randomization` 이 `True` 다**(첫 블록에서 확인했다). 이 주제는 해시를 안 쓰지만
> 사슬의 [30번](../30-repr-eq-hash-contracts/2-summary.md)이 그 사실 위에 서 있다.\
> ★ **순서가 보장 안 되는 출력은 이 문서에 하나도 없다** — 찍은 `dict` 는 전부 삽입 순서가 보장되는 것이고
> ([12번](../12-dict-and-key-requirements/2-summary.md)), `set` 은 한 번도 안 찍었다.\
> **선행** — [01-object-and-name-binding](../01-object-and-name-binding/2-summary.md)(이름이 객체에 붙는 모델) ·
> [21-scope-legb-global-nonlocal](../21-scope-legb-global-nonlocal/2-summary.md)(**이름** 탐색의 정본 — 여기는 **속성** 탐색이라 다른 것이다) ·
> [20-mutable-default-args](../20-mutable-default-args/2-summary.md)(**클래스 변수 공유와 같은 집안**) ·
> [03-mutability-and-copying](../03-mutability-and-copying/2-summary.md)(고치기와 새로 묶기의 차이).\
> **이 사슬** — 29 → [30](../30-repr-eq-hash-contracts/2-summary.md) → [31](../31-comparison-protocol-and-sortability/2-summary.md) → [32](../32-container-protocol/2-summary.md).
> **여기가 사슬의 첫째다** — 「특수 메서드는 **클래스 칸**에서 찾는다」가 뒤의 셋을 전부 떠받친다.

## 한눈에 — 쉽게 말하면

**`obj.x` 는 「`obj` 안을 본다」가 아니라 「정해진 칸들을 정해진 순서로 훑는다」이다.**

건물에 비유하면 이렇다.

- **내 사물함** — 인스턴스 칸. 나만 쓴다. `vars(obj)` 로 연다.
- **우리 반 공용 선반** — 클래스 칸. 반 전체가 **한 개를 같이 쓴다.** `Cls.__dict__` 로 연다.
- **위층으로 가는 계단** — MRO. 반에 없으면 **선배 반**으로 올라간다. `type(obj).__mro__` 가 계단의 순서다.
- **선반에 앉아 있는 안내원** — 디스크립터. 물건 대신 **안내원이 답한다.**

```text
   obj.x 를 쓰면 무슨 일이 일어나나

   ① type(obj) 의 MRO 를 훑어 x 를 찾는다        <- 클래스 쪽을 먼저 본다
        찾았는데 그것이 데이터 디스크립터면  -> 그 자리에서 __get__ 이 답한다 (끝)
   ② 인스턴스 칸 vars(obj) 에 x 가 있나
        있으면  -> 그 값이 답이다 (끝)
   ③ ①에서 찾아 둔 것이 있으면
        비데이터 디스크립터면 -> __get__ 이 답한다
        그냥 값이면          -> 그 값이 답이다 (끝)
   ④ 아무 데도 없으면
        __getattr__ 이 있으면 -> 그것이 만들어 준다
        없으면               -> AttributeError
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 내 사물함 | 인스턴스 칸 | `vars(obj)` 또는 `obj.__dict__` |
| 우리 반 공용 선반 | 클래스 칸 | `Cls.__dict__` |
| 위층으로 가는 계단 | MRO | `type(obj).__mro__` |
| 계단 순서를 정하는 규칙 | C3 선형화 | `Cls.mro()` · 못 만들면 `TypeError` |
| 선반에 앉은 안내원 | 디스크립터 | 찾은 것에 `__get__` 이 있나 |
| ★ **사물함을 이기는 안내원** | 데이터 디스크립터 | 그것에 `__set__` 도 있나 |
| 사물함에 지는 안내원 | 비데이터 디스크립터 | `__get__` 만 있다 |
| 사물함 자체를 없앤 건물 | `__slots__` | `vars(obj)` 가 `TypeError` |
| 없으면 즉석에서 만들어 주는 직원 | `__getattr__` | 못 찾았을 때만 부른다 |
| 모든 요청을 먼저 받는 안내데스크 | `__getattribute__` | 무조건 부른다 |
| 내 다음 사람 | `super()` | **부모가 아니라 MRO 상 내 다음** |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.\
「**클래스 몸통에 `items = []` 를 써 놓고 인스턴스마다 따로인 줄 알았다**」와
「**`self.x = ...` 를 했는데 값이 안 바뀐다**」가 그것이다.\
앞엣것은 **한 개를 같이 쓰는 선반**이고, 뒤엣것은 **사물함을 이기는 안내원**이다.

> **속성(attribute)** — 점(`.`) 뒤에 오는 이름. `obj.x` 의 `x` 다.\
> 예: 변수 이름(`x = 1` 의 `x`)과는 **다른 탐색 규칙**을 쓴다. 이름 쪽은 [21번](../21-scope-legb-global-nonlocal/2-summary.md)이 정본이다.

> **MRO(method resolution order, 메서드 결정 순서)** — 조상을 훑을 순서를 한 줄로 편 것.\
> 예: `D(B, C)` 이고 `B(A)`·`C(A)` 면 `D → B → C → A → object` 한 줄이 된다.

> **디스크립터(descriptor)** — `__get__` 을 가진 객체. **클래스 칸에 놓이면** 속성 접근을 가로챈다.\
> 예: 우리가 매일 쓰는 **함수**가 바로 이것이다. 그래서 `obj.method` 가 「자기 자신이 묶인 메서드」로 나온다.

돌린 판은 이것이다.

```python
# e29_version.py
import sys

print("version_info =", sys.version_info)
print("implementation =", sys.implementation.name)
print("platform =", sys.platform)
print("해시 무작위화 켜져 있나 :", bool(sys.flags.hash_randomization))
```
```text
===== python3 - <e29_version.py =====
version_info = sys.version_info(major=3, minor=12, micro=3, releaselevel='final', serial=0)
implementation = cpython
platform = linux
해시 무작위화 켜져 있나 : True
(exit 0)
```

## 이 주제가 답하려는 질문

1. **`obj.x` 는 어디를 어떤 순서로 보나** — 인스턴스 칸이 먼저인가 클래스 칸이 먼저인가.
2. **어디에 썼느냐에 따라 무엇이 공유되나** — 같은 클래스의 두 인스턴스가 언제 한 물건을 같이 쓰게 되나.
3. **그 순서를 가로채는 장치는 무엇이고 누가 이기나** — 디스크립터·`__getattr__`·`__slots__` 중 누가 누구를 이기나.

★ 둘째·셋째가 이 주제의 인출 목표다.
**「클래스 변수는 한 개다」와 「데이터 디스크립터는 인스턴스 칸을 이긴다」를 대는 것**이 아는 것과 들은 것의 경계다.

## 동작 방식

> 이 절이 본문이다. 그림이 먼저 오고 문장이 그 그림을 읽어 준다.

### 0. ★★ 이 주제가 쓰는 창 — 셋으로는 안 끝난다

**언제 쓰나** — 「값이 왜 저것이지」가 안 풀릴 때. **어느 칸에서 나온 답인지**를 먼저 가른다.

| 창 | 무엇을 묻나 | 이 창만으로는 안 보이는 것 |
|---|---|---|
| `vars(obj)` | **인스턴스 칸**에 있나 | 클래스 칸에 같은 이름이 있는지 |
| `Cls.__dict__` | **이 클래스 칸**에 있나 | 조상 칸에 있는지 |
| `type(obj).__mro__` | **어느 순서**로 훑나 | 찾은 것이 가로채는 물건인지 |
| ★ **네 번째** — 찾은 것에 `__get__`/`__set__` 이 있나 | **디스크립터인가** | 아무 칸에도 없는 경우 |

★ **네 번째 창이 왜 필요한가** — 세 창이 전부 정상인데 답이 엉뚱한 자리에서 나오는 경우가 있다.\
데이터 디스크립터가 그렇다. `vars(obj)` 에 값이 **보이는데도** 답은 클래스 칸에서 나온다.\
`vars()` 만 보고 「인스턴스 칸에 있으니 그 값이겠지」 하면 틀린다.

★★ **제5의 상태가 가장 나쁘다 — 세 창이 전부 「없음」인데 값이 나온다.**\
`__getattr__` 이 그것이다. 인스턴스 칸에도 없고, 클래스 칸에도 없고, MRO 어디에도 없는데
`obj.zzz` 가 **문자열을 답한다.** 값이 어디서 왔는지 세 창 어디에도 자국이 없다.\
그래서 `hasattr` 로 「있나」를 물으면 **`True`** 가 나오고, `vars()` 에는 **아무것도 안 생긴다.**

★ 이 주제의 창은 **읽기 전용이 아니다** — `vars(obj)` 는 사본이 아니라 **그 `dict` 자체**라서
거기 값을 넣으면 실제로 속성이 된다. 동작 1의 ⑤가 그 실측이다.

### 1. ★ 두 칸 — 인스턴스와 클래스를 갈라 본다

**언제 쓰나** — 이 주제의 출발점. 「`self.x = 1` 과 클래스 몸통의 `x = 1` 이 어떻게 다른가」에 답할 때.

문서가 첫 칸을 못 박는다 — *"A class instance has a namespace implemented as a dictionary
which is the **first place** in which attribute references are searched.
When an attribute is not found there, and the instance's class has an attribute by that name,
the search continues with the class attributes."*\
그리고 클래스에서도 못 찾으면 — *"When the attribute name is not found there,
the attribute search continues in the base classes."*

```text
   Derived(Base) · d = Derived("첫째")

   인스턴스 칸  vars(d)          {'name': '첫째'}
        |  없으면
        v
   클래스 칸    Derived.__dict__ {'kind': 'derived', ...}
        |  없으면
        v
   조상 칸      Base.__dict__    {'kind': 'base', ...}
        |  없으면
        v
   object 칸                     -> 여기도 없으면 AttributeError
```

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

그림 해설 — 다섯 단계가 계단을 한 칸씩 내려간다.

- ★ **①에서 `d.kind` 가 `derived` 다.** `Base` 칸에도 `base` 가 있는데 **`Derived` 칸이 먼저**라서 그쪽이 이겼다.
- **`name` 은 인스턴스 칸에만 있다.** `__init__` 안의 `self.name = name` 이 한 일이 **그 칸에 넣은 것**뿐이다.
- ★ **②에서 인스턴스 칸에 같은 이름을 대입하니 그쪽이 이긴다.** 그런데 **클래스 칸은 그대로**다
  (`Derived.kind` 가 여전히 `derived`). **덮은 것이 아니라 가린 것**이다.
- **③에서 인스턴스 칸의 것을 지우니 다시 클래스 것이 보인다.** 가려져 있던 것이 드러난 것이다.
- ★ **④에서 `Derived` 칸의 것까지 지우니 `Base` 칸의 `base` 가 나온다.** 계단을 한 칸 더 올라간 것이고,
  그 계단이 `['Derived', 'Base', 'object']` 다.
- ★ **⑤ — `vars(d)` 는 사본이 아니라 그 `dict` 자체다.** 거기 `42` 를 넣으니 `d.extra` 가 됐고
  `vars(d) is d.__dict__` 가 `True` 다. **진단창이 곧 저장소**다.

**비용** — 조회는 MRO 길이에 비례해 최악까지 훑는다. 다만 **얼마나 비싼지는 안 쟀다.**

### 2. ★★ 탐색 경로 — 전수 그림

**언제 쓰나** — 이 주제를 한 장으로 붙들 때. 아래 네 갈래가 이 문서의 나머지를 전부 낳는다.

```text
   obj.x   (obj 는 인스턴스, C = type(obj))

   [1] C 의 MRO 를 앞에서부터 훑어 'x' 를 찾는다
         |
         +-- 찾음 & __get__ 과 __set__ 을 둘 다 가짐 (데이터 디스크립터)
         |        -> __get__(obj, C) 가 답한다.  ★ 인스턴스 칸을 안 본다
         |
         +-- 찾음 & 그 밖 / 못 찾음
                  |
                  v
   [2] vars(obj) 에 'x' 가 있나
         |
         +-- 있음 -> 그 값이 답이다
         |
         +-- 없음
                  |
                  v
   [3] [1] 에서 찾아 둔 것이 있나
         |
         +-- __get__ 만 가짐 (비데이터) -> __get__ 이 답한다
         +-- 그냥 값                    -> 그 값이 답이다
         +-- 없음
                  |
                  v
   [4] AttributeError 를 낸다
         |
         +-- 클래스에 __getattr__ 이 있으면 그것이 대신 답한다
         +-- 없으면 AttributeError 가 밖으로 나간다
```

문서가 그 우선순위를 한 문장으로 적는다 — *"data descriptors take precedence over instance dictionaries,
instance dictionaries take precedence over non-data descriptors,
and non-data descriptors take precedence over class variables."*

★ **이 그림에서 읽어야 할 것 넷.**

1. ★ **기계는 클래스 쪽(MRO)에서 먼저 찾아 두고**, 찾은 것의 성질에 따라 인스턴스 칸과 견준다.
   ★★ **문서가 두 자리에서 다르게 말하는 것처럼 보인다** — 3.2.11 은 인스턴스 칸이 *"the first place"* 라 하고,
   3.3.2.3 은 **데이터 디스크립터가 그보다 앞**이라 한다.
   **앞엣것은 디스크립터가 없는 보통의 경우**를 말한 것이고, **뒤엣것이 전수 규칙**이다. 둘은 안 부딪친다.
2. **데이터 디스크립터만 인스턴스 칸을 이긴다.** 나머지는 전부 진다.
3. **`__getattr__` 은 맨 끝**이다. 앞에서 찾으면 **안 불린다.**
4. ★ **`__getattribute__` 는 이 그림 전체를 감싼다.** 정의하면 [1] 부터가 아예 안 돌고 그 함수가 다 한다.

**비용** — 이 순서는 **언어 보장**이다. 다만 **얼마나 빠른지는 안 쟀다.**

### 3. ★★ 클래스 변수 공유 — 선반은 한 개다

**언제 쓰나** — 「인스턴스마다 따로인 줄 알았는데 같이 쓰더라」가 날 때.
[20번](../20-mutable-default-args/2-summary.md)의 가변 기본 인자와 **같은 집안**이다.

> **같은 집안인 이유 한 줄** — 둘 다 **「한 번만 만들어진 가변 객체」를 여럿이 나눠 쓰는 것**이다.\
> 20번은 `def` 가 실행될 때 기본값이 **한 번** 만들어지고, 여기는 `class` 몸통이 실행될 때
> 클래스 칸의 리스트가 **한 번** 만들어진다. 고치는 법도 같다 — **만드는 시점을 뒤로 옮긴다**
> (`None` 센티널 / `__init__` 안에서 `self.items = []`). 정본은 20번이므로 여기서는 결론만 쓴다.

```text
   Cart.items = []  를 클래스 몸통에 쓰면

        Cart 클래스 칸
        +-----------------+
        | items ---------------> [ ]   <- 리스트는 한 개다
        +-----------------+      ^  ^
                                 |  |
        a = Cart()  vars(a) {}  -+  |   a.items 는 계단을 올라가 이것을 본다
        b = Cart()  vars(b) {} -----+   b.items 도 같은 것을 본다

   a.add("사과") 가 self.items.append(...) 이면
        -> 계단을 올라가 그 한 개를 찾아 "그 객체를 고친다"
        -> b.items 에도 보인다
```

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

그림 해설 — 셋이 **각각 다른 일**을 한다.

- ★ **① `append` 는 고치기**다. `self.items` 로 **찾아 놓고** 그 객체를 건드린다.
  그래서 `a.items is b.items` 가 `True` 이고, **인스턴스 칸은 둘 다 비어 있다**(`vars(a)` 도 `vars(b)` 도 `{}`).
  ★ **증상과 진단이 어긋나는 자리다** — 값은 인스턴스에 있는 것처럼 보이는데 칸은 비어 있다.
- ★ **② 대입은 새로 묶기**다. `self.items = self.items + [x]` 는 **새 리스트를 만들어 인스턴스 칸에 넣는다.**
  그래서 `c.items` 만 바뀌고 `Cart2.items` 는 `[]` 그대로이며, `vars(c)` 에 `items` 가 생겼다.
- ★★ **③ `+=` 는 둘 다 한다.** 리스트에서 `+=` 는 제자리 확장이라 **클래스 칸의 리스트가 늘어나고**
  (`Cart3.items` 가 `['감']`), 그 결과를 **다시 대입**하므로 **인스턴스 칸도 생긴다**(`vars(f)` 가 `{'items': ['감']}`).
  **가장 헷갈리는 자리**이고, [03번](../03-mutability-and-copying/2-summary.md)의 고치기/새로 묶기 구분이 그대로 걸린다.

★ **고치는 법은 한 줄이다** — 가변 클래스 변수를 쓰지 말고 `__init__` 안에서 `self.items = []` 로 만든다.
그러면 **인스턴스마다 하나씩** 생긴다.

**비용** — 클래스 변수는 **메모리를 아낀다**(한 개뿐이니까). 그러나 **가변이면 공유가 버그가 된다.**
어느 쪽이 얼마나 싼지는 **안 쟀다.**

### 4. ★★ MRO 와 다이아몬드 — 계단은 한 줄이다

**언제 쓰나** — 다중 상속에서 「어느 조상의 것이 불리나」가 막힐 때.

문서가 규칙의 이름을 적는다 — *"This search of the base classes uses the **C3 method resolution order**
which behaves correctly even in the presence of 'diamond' inheritance structures."*

```text
   다이아몬드                     C3 가 편 한 줄

        A                          D -> B -> C -> A -> object
       / \
      B   C                    ★ 두 갈래가 한 줄이 된다
       \ /                     ★ 공통 조상 A 는 B·C 보다 반드시 뒤다
        D                      ★ object 는 반드시 맨 끝이다
```

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

그림 해설 — 네 덩어리가 각각 다른 것을 말한다.

- ★ **①에서 계단이 `D B C A object` 한 줄로 나왔다.** `D().who()` 가 `B` 인 것이 그 순서의 결과다.
  `D.mro()` 와 `D.__mro__` 는 같은 것을 준다(하나는 메서드, 하나는 튜플).
- **②가 C3 의 성질 셋을 확인한다** — 적은 순서대로 `B` 가 `C` 보다 앞이고,
  **공통 조상 `A` 는 둘보다 뒤**이며, `object` 가 맨 끝이다.
  ★ 「공통 조상은 마지막에」가 다이아몬드를 다루는 핵심이다 — 그래야 `A` 의 것을 **한 번만** 거친다.
- ★★ **③이 C3 가 「못 만드는 순서」를 보여 준다.** `class Bad(A, B)` 는 **`A` 가 `B` 의 조상인데
  `A` 를 먼저 적은 것**이라 모순이다. 답은 `TypeError` 이고 문구는
  `Cannot create a consistent method resolution order (MRO) for bases A, B` 다.
  ★ **이 문구는 줄바꿈이 박혀 두 줄로 나온다** — 블록에서 `resolution` 다음에 줄이 갈린다.
  **메시지 안에 개행이 들어 있는 것**이지 출력을 접은 것이 아니다. 그대로 실었다.
- **④가 「속성 탐색이 이 순서를 그대로 쓴다」를 잇는다.** `D.mark` 와 `C.mark` 를 둘 다 두면 `D` 것이 나오고,
  `D` 칸에서 지우면 **`B` 를 건너뛰고** `C` 것이 나온다. `B` 에는 `mark` 가 없기 때문이다.

**비용** — C3 는 **클래스를 만들 때 한 번** 계산해 둔다. 조회할 때마다 다시 풀지 않는다.
다만 **그 비용은 안 쟀다.**

### 5. ★★ `super()` 는 「부모」가 아니라 「MRO 다음」이다

**언제 쓰나** — 다중 상속에서 `super()` 가 엉뚱한 데로 가는 것처럼 보일 때.

문서가 그대로 적는다 — *"The **search starts from the class right after the type**.
For example, if `__mro__` of object-or-type is `D -> B -> C -> A -> object` and the value of type is `B`,
then `super()` searches `C -> A -> object`."*

```text
   Left 안에서 super().go() 를 부르면 — 답이 두 가지다

   (가) Left() 를 부른 경우            (나) Both() 를 부른 경우
        MRO: Left Base object              MRO: Both Left Right Base object
              ^    |                              ^    ^     |
              |    +-- 내 다음 = Base             |    |     +-- 내 다음 = Right
              나                                  |    나
                                                  시작

   ★ 같은 Left.go 안의 같은 super() 한 줄인데 다음이 달라진다
   ★ 무엇이 정하나 — "그 인스턴스의 타입" 의 MRO 다
```

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

그림 해설 — 세 덩어리가 「부모」와 「다음」을 가른다.

- **① `Left.__bases__` 는 글자 그대로 `['Base']` 다.** 「부모」를 묻는 창은 이것이고,
  `Left()` 를 그냥 부르면 실제로 `Left.go → Base.go` 로 간다. **여기까지는 「부모」로 읽어도 맞는다.**
- ★★ **② `Both()` 를 부르면 같은 `Left.go` 안의 `super()` 가 `Right` 로 간다.**
  체인이 `Both.go → Left.go → Right.go → Base.go` 다.
  `Right` 는 **`Left` 의 부모가 아니라 형제**인데도 그리로 간다 — MRO 에서 **바로 다음**이기 때문이다.
  ★ 그래서 `Base.go` 가 **딱 한 번만** 돈다. 다이아몬드에서 공통 조상을 한 번만 거치는 것이 이 장치의 값이다.
- ★ **③이 그것을 한 줄로 증명한다.** `super(Left, Both())` 가 고른 `go` 의 주인은 `Right` 이고,
  `super(Left, Left())` 가 고른 것은 `Base` 다. **왼쪽 인자는 같고 오른쪽 인스턴스만 다르다.**

★ **그래서 협력적 다중 상속에서는 모든 참여자가 `super()` 를 불러야 한다.** 한 군데라도 빼먹으면
그 뒤의 MRO 가 **통째로 안 돈다.** `Right.go` 가 `super().go()` 를 안 불렀다면 `Base.go` 가 안 찍혔을 것이다.

**비용** — `super()` 는 **인자 없이 쓰면** 컴파일러가 `__class__` 셀을 만들어 준다.
그 대가와 속도는 **안 쟀다.** 정본은 `[목록의 **34번 주제**](../34-inheritance-mro-super/)` 다.

### 6. ★ 두 갈고리 — `__getattr__` 과 `__getattribute__`

**언제 쓰나** — 「없는 속성을 만들어 주는」 객체를 쓰거나 쓸 때. 프록시·ORM·설정 객체가 전부 이 자리다.

문서가 둘을 정확히 가른다.\
`__getattr__` — *"Called when the default attribute access **fails** with an `AttributeError` …
Note that if the attribute is found through the normal mechanism, `__getattr__()` is **not called**."*\
`__getattribute__` — *"Called **unconditionally** to implement attribute accesses for instances of the class."*

```text
   obj.x 를 쓰면

   __getattribute__ 가 있나 -- 있다 --> 그것이 전부 한다 (무조건)
        |                                   |
        없다                                 그 안에서 AttributeError 가 나면
        |                                   |
        v                                   v
   기본 탐색(동작 2의 그림)  -- 실패 --> __getattr__ 이 있으면 그것이 답한다
        |                                              없으면 AttributeError
        성공 -> 값
                ★ 성공하면 __getattr__ 은 "안 불린다"
```

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

그림 해설 — 다섯 덩어리가 「언제 불리나」를 전수로 가른다.

- ★ **①에서 `__getattr__` 이 안 불렸다.** `o.x` 는 클래스 칸에서 찾았기 때문이다.
  **로그가 없다는 것 자체가 근거**다. 「못 찾았을 때만」이 여기서 증명된다.
- **②에서는 불렸다.** `zzz` 가 아무 데도 없으니 기본 탐색이 실패했고, 그 뒤에 갈고리가 걸렸다.
- ★ **③에서 `__getattribute__` 는 있는 이름에도 불린다.** `e.x` 가 성공하는데도 로그가 찍혔다 — **무조건**이다.
- ★★ **④에서 둘이 순서대로 불린다.** `__getattribute__` 가 먼저 불리고,
  그것이 `AttributeError` 를 내자 `__getattr__` 이 이어 불렸다. **둘은 경쟁이 아니라 직렬**이다.
- ★ **⑤ — `hasattr` 도 같은 길을 탄다.** `hasattr(o, 'zzz')` 가 `True` 를 답하는데
  **`vars(o)` 에는 아무것도 안 생긴다.** 이것이 제5의 상태다 —
  **세 창이 전부 「없음」인데 있다고 답한다.**

★ **`__getattribute__` 는 재귀가 쉽다.** 그 안에서 `self.anything` 을 쓰면 자기 자신을 다시 부른다.
실험이 `object.__getattribute__(self, name)` 을 쓴 이유가 그것이다.

**비용** — `__getattr__` 은 **실패 경로에만** 끼어들어 정상 경로를 건드리지 않는다.
`__getattribute__` 는 **모든 접근**을 지나간다. 값이 얼마나 다른지는 **안 쟀다.**

### 7. ★★★ 디스크립터 — 누가 인스턴스 칸을 이기나

**언제 쓰나** — `vars(obj)` 에 값이 보이는데 `obj.x` 가 다른 것을 답할 때. 이 절이 네 번째 창의 정본이다.

```text
   데이터 디스크립터 (__get__ 과 __set__)        비데이터 (__get__ 만)

   클래스 칸  slot -> [안내원]              클래스 칸  plain -> [안내원]
   인스턴스 칸 slot -> "직접 넣은 값"        인스턴스 칸 plain -> "직접 넣은 값"

   c.slot  -> 안내원이 답한다   (이김)       c.plain -> 직접 넣은 값   (짐)
   vars(c) -> "직접 넣은 값" 이 보인다       vars(c) -> "직접 넣은 값" 이 보인다

   ★ 두 경우의 vars(c) 가 똑같다. 갈리는 것은 "안내원에게 __set__ 이 있나" 뿐이다
```

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

그림 해설 — 네 덩어리가 우선순위 네 층을 전부 실측한다.

- ★★ **①이 이 절의 심장이다.** `vars(c)` 에 `'인스턴스 칸에 직접 넣은 값'` 이 **버젓이 있는데**
  `c.slot` 은 `데이터 디스크립터가 답한다` 를 준다. **세 창이 전부 정상인데 답이 다르다.**
  ★ 대입조차 가로채였다 — `__set__` 이 먼저 로그를 찍고 나서 인스턴스 칸에 넣었다.
- **②는 반대다.** 비데이터 디스크립터는 덮기 전에는 답하지만, 인스턴스 칸에 값이 들어오는 순간 **진다.**
- **③이 판별식이다** — 갈리는 것은 `__set__` 의 유무 하나뿐이다(`__delete__` 도 같은 자격이다).
- ★★ **④가 실무에서 매일 지나가는 자리다.** **함수가 비데이터 디스크립터**다
  (`function` 에 `__set__` 이 없다). 그래서 `m.__dict__['go']` 에 무언가를 넣으면
  **인스턴스 칸이 이겨** `m.go()` 가 그쪽을 부른다.
  ★ 거꾸로 읽으면 이렇다 — **메서드를 인스턴스별로 갈아끼울 수 있는 것**이 이 우선순위 덕분이다.

★ **`__slots__` 가 만드는 것도 데이터 디스크립터다**(동작 8). 그래서 두 절이 이어진다.
`property` 도 마찬가지인데, 그쪽 정본은 `[목록의 **33번 주제**](../33-property-descriptor-slots/)` 다.

**비용** — 디스크립터는 **접근마다 함수 호출**이 낀다. 얼마나 비싼지는 **안 쟀다.**

### 8. ★ `__slots__` — 사물함 자체를 없앤다

**언제 쓰나** — 같은 모양의 객체를 아주 많이 만들 때. 그리고 「왜 새 속성이 안 붙지」가 날 때.

문서가 결과를 적는다 — *"Without a `__dict__` variable, instances cannot have new variables
not listed in the `__slots__` definition. Attempts to assign to an unlisted variable name raises `AttributeError`."*

```text
   보통 클래스                      __slots__ = ("x",)

   인스턴스                          인스턴스
   +-----------+                    +-----------+
   | __dict__ ------> {'x': 1}      |  x 칸: 1  |   <- dict 가 아예 없다
   +-----------+                    +-----------+

   클래스 칸                         클래스 칸
   (특별한 것 없음)                   x -> member_descriptor  <- 데이터 디스크립터다

   a.extra = 1  -> 된다             b.extra = 1  -> AttributeError
   vars(a)      -> {'x': 1}         vars(b)      -> TypeError
```

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

그림 해설 — 다섯 덩어리가 「없앤 것」과 「생긴 것」을 갈라 보인다.

- **① `WithSlots` 인스턴스에는 `__dict__` 가 없다.** `hasattr` 가 `False` 를 답한다.
- ★★ **② 대신 클래스 칸에 `x` 가 생겼고 그 정체가 `member_descriptor` 다.**
  그리고 **그것이 데이터 디스크립터다**(`__set__` 이 있다) — 동작 7의 판별식을 그대로 통과한다.
  ★ 그래서 `__slots__` 는 **별도 장치가 아니라 디스크립터 한 벌**이다. 두 절이 한 규칙으로 묶인다.
  ★ `member_descriptor` 라는 **이름 자체는 CPython 의 것**이다. 판이 오르면 달라질 수 있다.
- **③ 새 속성을 붙이면 `AttributeError` 다.** 문구는 `'WithSlots' object has no attribute 'extra'` 이고,
  **오타를 잡아 주는 부수 효과**가 여기서 나온다.
- ★ **④ `vars()` 가 `TypeError` 를 낸다** — `vars() argument must have __dict__ attribute` 다.
  **진단창 하나가 통째로 막히는 것**이므로, 이런 객체는 `Cls.__dict__` 와 `__slots__` 로 봐야 한다.
- ★★ **⑤ 하위 클래스가 `__slots__` 를 안 쓰면 `__dict__` 가 되살아난다.**
  그래서 `Child` 인스턴스에는 새 속성이 붙는다. **상속 사슬 전체가 선언해야 효과가 남는다.**

**비용** — 메모리를 아끼는 것이 목적인 장치인데 **얼마나 아끼는지는 안 쟀다.**
대가는 분명하다 — 동적 속성 추가가 막히고, `vars()` 가 안 되며, 상속에서 한 군데만 빠져도 풀린다.

### 9. `__new__` 와 `__init__` — 만드는 것과 채우는 것

**언제 쓰나** — 불변 타입을 흉내 내거나 싱글턴을 만들 때. 그리고 「`__init__` 이 왜 안 불리지」가 날 때.

문서가 조건을 적는다 — *"If `__new__()` does not return an instance of cls,
then the new instance's `__init__()` method will not be invoked."*

```text
   Point(3) 한 줄이 하는 일

   type.__call__ 이 두 번 부른다
        |
        +--> __new__(Point, 3)      빈 객체를 만든다   -> obj
        |          vars(obj) 는 {}  (아직 아무것도 없다)
        |
        +--> isinstance(obj, Point) 인가?
                 예 --> __init__(obj, 3)   그 객체를 채운다
                 아니오 --> 건너뛴다        ★ 여기가 갈림길
```

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

그림 해설.

- **①이 두 단계를 눈으로 보인다.** `__new__` 가 먼저 불리고 그때 `vars(obj)` 가 `{}` 이며,
  그 다음에 `__init__` 이 같은 인자를 받아 채운다. **둘 다 `(3,)` 를 받는다.**
- ★ **② `__new__` 가 아무것도 안 돌려주면**(`None` 을 돌려준 셈) `__init__` 이 **안 불린다.**
  그리고 `NotReturning(3)` 의 결과가 `None` 이다.
- ★ **③ 다른 타입을 돌려줘도 같다.** `Sneaky(3)` 가 **리스트**를 준다. 클래스를 불렀는데 리스트가 나온 것이다.

★ **속성 탐색과 이어지는 지점** — `__init__` 이 하는 일은 결국 **인스턴스 칸을 채우는 것**뿐이다.
그래서 `__init__` 을 건너뛰면 **인스턴스 칸이 빈 채로** 객체가 살아 있게 된다.

**비용** — `__new__` 는 대부분 필요 없다. 필요한 자리는 **불변 타입 상속**과 **인스턴스 재사용** 둘이다.

## 문법 — 형태와 규칙

> ★ 아래 두 덩어리는 **형태 스케치**다. 돌린 프로그램은 위의 블록들이고,
> 여기서는 **어디에 무엇을 쓰면 어느 칸에 들어가는지**만 모아 둔다.

```text
class C(Base1, Base2):          # MRO 는 C3 로 이 순서에서 계산된다
    kind = "클래스 칸"           # 클래스 칸에 들어간다. 인스턴스 전부가 공유한다
    __slots__ = ("x",)          # 인스턴스의 __dict__ 를 없앤다(데이터 디스크립터가 생긴다)

    def __new__(cls, *a):       # 만든다. cls 인스턴스를 안 돌려주면 __init__ 이 안 돈다
        return super().__new__(cls)

    def __init__(self, x):
        self.x = x              # 인스턴스 칸에 들어간다

    def method(self):           # 클래스 칸에 들어간다(함수 = 비데이터 디스크립터)
        super().method()        # "부모" 가 아니라 "이 인스턴스 MRO 에서 C 다음"

    def __getattr__(self, name):        # 못 찾았을 때만 불린다
        raise AttributeError(name)

    def __getattribute__(self, name):   # 무조건 불린다. 재귀 주의
        return object.__getattribute__(self, name)
```

```text
진단 — 어느 칸에 있나

vars(obj)              인스턴스 칸.  obj.__dict__ 와 같은 것이고 사본이 아니다
C.__dict__             그 클래스 칸만. 조상 것은 안 보인다
type(obj).__mro__      훑을 순서. C.mro() 는 같은 것을 리스트로 준다
C.__bases__            글자 그대로의 부모. ★ super() 가 가는 곳과 다를 수 있다
type(C.__dict__[n])    찾은 것의 정체. member_descriptor · function · property …
hasattr(t, '__set__')  그것이 데이터 디스크립터인가(t 는 위의 타입)
```

규칙 열둘.

1. **클래스 몸통의 대입은 클래스 칸에**, **`self.x = ...` 는 인스턴스 칸에** 들어간다.
2. ★ **조회는 클래스 쪽(MRO)을 먼저 훑고**, 그 결과에 따라 인스턴스 칸과 견준다(동작 2의 그림).
3. ★ **데이터 디스크립터만 인스턴스 칸을 이긴다.** 판별식은 `__set__`(또는 `__delete__`)의 유무다.
4. **함수는 비데이터 디스크립터**다. 그래서 인스턴스 칸에 같은 이름을 넣으면 그쪽이 이긴다.
5. ★ **`obj.x = v` 는 탐색이 아니라 저장**이다. 데이터 디스크립터가 있으면 그 `__set__` 이 가로챈다.
6. **`del obj.x` 는 인스턴스 칸에서만 지운다.** 클래스 칸의 것은 그대로 남아 다시 드러난다.
7. ★ **`__getattr__` 은 실패했을 때만**, **`__getattribute__` 는 무조건** 불린다.
8. **`hasattr` 는 실제로 접근해 본다.** 갈고리가 있으면 `True` 가 나와도 칸에는 아무것도 없다.
9. ★ **MRO 는 C3 이고 못 만들면 `TypeError`** 다. 클래스를 **정의하는 시점**에 터진다.
10. ★ `super()` 는 **MRO 상 내 다음**이다. `__bases__` 와 다를 수 있다.
11. **`__slots__` 는 그 클래스에서만 효과가 있다.** 하위 클래스가 안 쓰면 `__dict__` 가 되살아난다.
12. **`__new__` 가 그 클래스의 인스턴스를 안 돌려주면 `__init__` 이 안 불린다.**

**금지 사례 — 문법은 맞는데 조용히 어긋나는 것들**

```text
class Cart:
    items = []                  # ① 가변 클래스 변수 — 모든 인스턴스가 한 개를 공유한다
    def add(self, x):
        self.items.append(x)    #    고치기라 클래스 칸의 그 한 개가 늘어난다

class Proxy:
    def __getattribute__(self, name):
        return self.__dict__[name]   # ② 자기 자신을 다시 부른다 — 무한 재귀

class Sized:
    __slots__ = ("w",)
class Sub(Sized):
    pass                        # ③ 하위에서 안 쓰면 __dict__ 가 되살아나 효과가 풀린다

class Bad(A, B):                # ④ A 가 B 의 조상인데 먼저 적었다 — 정의 시점에 TypeError
    pass

class Cached:
    def __new__(cls, k):
        return cls._pool[k]     # ⑤ 이미 있는 것을 돌려주면 __init__ 이 "또" 불린다
                                #    (cls 의 인스턴스이므로 조건을 통과한다)
```

★ ⑤가 특히 조용하다 — **`__new__` 가 그 클래스의 인스턴스를 돌려주면 `__init__` 이 반드시 불린다.**
풀에서 꺼낸 기존 객체가 **매번 다시 초기화**된다.

## 어디서 틀리나

### (1) ★★ 가변 클래스 변수를 인스턴스별인 줄 안다

**클래스 칸의 리스트는 한 개**다. `append` 는 그 한 개를 늘린다.\
★ **증상과 진단이 어긋난다** — 값은 인스턴스에 있는 것 같은데 `vars(obj)` 는 비어 있다.\
고치는 법은 `__init__` 안에서 만드는 것이고, [20번](../20-mutable-default-args/2-summary.md)과 같은 처방이다.

### (2) ★★ `vars(obj)` 에 값이 보이니 그 값이 답인 줄 안다

**데이터 디스크립터가 있으면 진다.** 동작 7의 ①이 그 실측이다.\
★ **네 번째 창을 봐야 한다** — 클래스 칸에서 찾은 것에 `__set__` 이 있나.

### (3) ★ `__getattr__` 이 모든 접근에 불리는 줄 안다

**못 찾았을 때만**이다. 있는 이름에는 **안 불린다.**\
모든 접근을 보고 싶으면 `__getattribute__` 인데, 그쪽은 **재귀가 쉽다.**

### (4) ★ `hasattr` 로 「진짜 있나」를 검사한다

**`__getattr__` 이 있으면 무엇을 물어도 `True`** 가 나온다.\
칸을 물으려면 `'이름' in vars(obj)` 나 `'이름' in type(obj).__dict__` 를 쓴다.

### (5) ★★ `super()` 를 「부모」로 읽는다

**MRO 상 다음**이다. 다중 상속에서 **형제**로 갈 수 있다.\
★ `Left.__bases__` 는 `['Base']` 인데 `Both()` 안에서는 `Right` 로 간다 — 동작 5의 ③.

### (6) ★ 협력 체인에서 한 군데만 `super()` 를 빼먹는다

**그 뒤의 MRO 가 통째로 안 돈다.** 예외도 경고도 없다.\
`Right.go` 가 `super().go()` 를 안 불렀으면 `Base.go` 가 안 찍혔을 것이다.

### (7) ★ 다중 상속의 순서를 스타일로 안다

**C3 가 못 푸는 순서가 있다.** `class Bad(A, B)` 에서 `A` 가 `B` 의 조상이면 **정의 시점에 `TypeError`** 다.\
★ 그 문구에는 **개행이 박혀 두 줄로** 나온다.

### (8) ★ `__slots__` 를 쓰면 무조건 `__dict__` 가 없는 줄 안다

**그 클래스에서만**이다. 하위 클래스가 `__slots__` 를 선언하지 않으면 **되살아난다.**\
★ 상속 사슬 전체가 선언해야 효과가 남는다.

### (9) `__slots__` 인 객체에 `vars()` 를 쓴다

**`TypeError: vars() argument must have __dict__ attribute`.**\
진단창 하나가 막히므로 `Cls.__dict__` 와 `__slots__` 로 본다.

### (10) ★ 인스턴스에 특수 메서드를 달아 둔다

**특수 메서드는 타입에서 찾는다.** [28번](../28-context-managers-and-with/2-summary.md)의 `__enter__` 와 같은 규칙이고,
사슬의 [30](../30-repr-eq-hash-contracts/2-summary.md)·[31](../31-comparison-protocol-and-sortability/2-summary.md)·[32](../32-container-protocol/2-summary.md)가 전부 이 위에 선다.

### (11) `+=` 를 대입으로만 안다

**리스트에서는 제자리 확장 + 대입 둘 다**다. 클래스 칸의 리스트가 늘어나고 인스턴스 칸도 생긴다.\
동작 3의 ③이 그 실측이다.

### (12) ★ `__new__` 를 「또 다른 `__init__`」으로 안다

**만드는 것**과 **채우는 것**은 다르다.\
그리고 **그 클래스의 인스턴스를 안 돌려주면 `__init__` 이 안 불린다.**

### (13) 이름 탐색(LEGB)과 속성 탐색을 같은 것으로 안다

**다른 탐색이다.** `x` 는 LEGB([21번](../21-scope-legb-global-nonlocal/2-summary.md)),
`obj.x` 는 인스턴스 → 클래스 → MRO 다.\
★ 그래서 **클래스 몸통의 이름을 메서드에서 이름으로 읽을 수 없다** — 그쪽은 21번의 정본이다.

### (14) `__mro__` 나 `__dict__` 의 모양을 언어 사실로 적는다

**보이는 방식은 CPython 쪽**이다. `member_descriptor` 같은 이름도 마찬가지다.\
★ 보장되는 것은 **순서와 우선순위**이지 **들여다보는 창의 모양**이 아니다.

## 구현 세부사항 대 언어 보장

세 층으로 가른다. ★ **이 주제는 「언어 보장」이 두껍다** — 탐색 순서도 디스크립터 우선순위도
`__getattr__` 의 호출 조건도 **레퍼런스에 한 문장씩 적혀 있다.**\
구현 쪽에 남는 것은 **그 칸을 들여다보는 창**과 **거기 보이는 이름들**이다.

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **언어 보장** | 레퍼런스가 정한 것 | 공식 문서 문장을 열어서 인용 |
| **CPython 구현** | 이 구현이 그렇게 하는 것 | `vars()`·`__dict__`·`__mro__` 로 들여다본 결과 |
| **이 판(3.12.3)의 관찰** | 이 판에서 그랬을 뿐 | 예외 문구 · 내부 타입 이름 |

### 언어 보장

| 사실 | 근거 |
|---|---|
| 인스턴스 칸이 **첫 자리**이고, 없으면 클래스, 없으면 조상으로 간다 | 3.2.11 Class instances · 3.2.10 Custom classes |
| 조상을 훑는 순서는 **C3** 이고 다이아몬드에서 옳게 동작한다 | 3.2.10 — *"uses the C3 method resolution order"* |
| **데이터 디스크립터 > 인스턴스 칸 > 비데이터 디스크립터 > 클래스 변수** | 3.3.2.3 Invoking Descriptors |
| `__getattr__` 은 **기본 접근이 `AttributeError` 로 실패했을 때만** 불린다 | 3.3.2 — *"if the attribute is found through the normal mechanism, `__getattr__()` is not called"* |
| `__getattribute__` 는 **무조건** 불린다 | 3.3.2 — *"Called unconditionally"* |
| `__slots__` 를 쓰면 `__dict__` 가 없고, 없는 이름에 대입하면 `AttributeError` | 3.3.2.4 `__slots__` |
| `super()` 는 **type 바로 다음 클래스부터** 찾는다 | `super()` — *"The search starts from the class right after the type."* |
| `__mro__` 는 `getattr()` 과 `super()` 가 **함께 쓰는** 순서다 | `super()` 문서 |
| `__new__` 가 **cls 의 인스턴스를 안 돌려주면** `__init__` 이 안 불린다 | 3.3.1 Basic customization |

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| `vars(obj) is obj.__dict__` 가 참이라 **거기 넣으면 속성이 된다** | 실행 — 동작 1의 ⑤ |
| `__slots__` 가 만드는 것의 타입 이름이 `member_descriptor` | 실행 — 동작 8의 ② |
| `vars()` 의 거부 문구가 `vars() argument must have __dict__ attribute` | 실행 — 동작 8의 ④ |
| MRO 실패 문구에 **개행이 박혀 두 줄로** 나오는 것 | 실행 — 동작 4의 ③ |
| `super(Left, obj).go.__qualname__` 으로 **고른 주인**을 읽을 수 있는 것 | 실행 — 동작 5의 ③ |
| `function` 에 `__set__` 이 없다는 것(= 비데이터) | 실행 — 동작 7의 ④ |

### 이 판(3.12.3)의 관찰

| 관찰 | 어디가 흔들리나 |
|---|---|
| 예외 **문구** 넷 전부 | 종류는 명세, 문구는 아니다 |
| `member_descriptor` 라는 이름 | 내부 타입 이름이다. **성질**(데이터 디스크립터)은 안 흔들린다 |
| MRO 오류 메시지의 **줄바꿈 위치** | 메시지 안의 개행이다. 판이 오르면 달라질 수 있다 |
| `sys.flags.hash_randomization` 이 `True` | 실행마다 씨앗이 다르다는 뜻 — 사슬의 [30번](../30-repr-eq-hash-contracts/2-summary.md)이 여기 기댄다 |

### 그래서 이렇게 적으면 틀린다

- ✗ 「`obj.x` 는 **언제나** 인스턴스 칸을 먼저 본다」\
  ○ **디스크립터가 없을 때만 그렇게 보인다.** 문서의 *"the first place"*(3.2.11)는 보통의 경우를 말한 것이고,
  전수 규칙은 3.3.2.3 의 네 층이다 — **데이터 디스크립터가 인스턴스 칸보다 앞**이다.
- ✗ 「`vars(obj)` 에 있으면 그 값이 답이다」\
  ○ **데이터 디스크립터가 있으면 진다.**
- ✗ 「디스크립터는 특별한 클래스를 만들어야 쓴다」\
  ○ **함수가 이미 디스크립터다.**
- ✗ 「`__getattr__` 은 속성 접근 갈고리다」\
  ○ **실패 갈고리**다. 성공하면 안 불린다.
- ✗ 「`hasattr` 가 참이면 그 칸에 있다」\
  ○ **만들어 준 것일 수 있다.** `vars()` 에는 아무것도 없다.
- ✗ 「`super()` 는 부모를 부른다」\
  ○ **MRO 상 다음**이다. 형제일 수 있다.
- ✗ 「`__slots__` 를 쓰면 상속해도 `__dict__` 가 없다」\
  ○ **하위 클래스가 안 쓰면 되살아난다.**
- ✗ 「`__mro__` 로 보이는 순서는 CPython 구현이다」\
  ○ **C3 라는 것과 그 순서로 찾는다는 것은 언어 보장**이다. 구현인 것은 **들여다보는 창**이다.
- ✗ 「`__new__` 를 정의하면 `__init__` 은 안 불린다」\
  ○ **cls 의 인스턴스를 돌려주면 불린다.** 안 돌려줄 때만 건너뛴다.

**판정 기준 한 줄**: **「이 값이 어느 칸에서 나왔나」를 물으면 탐색이 갈리고,
「찾은 것에 `__set__` 이 있나」를 물으면 인스턴스 칸이 이기는지가 갈린다.**

## 언제 쓰고 언제 안 쓰나

| 상황 | 판정 |
|---|---|
| 인스턴스마다 다른 값을 둔다 | **`__init__` 안에서 `self.x = ...`** |
| 모든 인스턴스가 같은 값을 본다 | 클래스 변수. ★ **불변인 것만**(`int`·`str`·`tuple`) |
| 모든 인스턴스가 같은 **가변** 물건을 본다 | ★ 대개 **버그**다. 정말 원하면 이름으로 의도를 드러내라 |
| 없는 속성을 만들어 주고 싶다 | **`__getattr__`** — 실패 경로만 건드린다 |
| 모든 접근을 기록하고 싶다 | `__getattribute__` — ★ **재귀 주의.** 되도록 피한다 |
| 속성 하나에 검증·계산을 붙인다 | `property` — 정본은 `[목록의 **33번 주제**](../33-property-descriptor-slots/)` |
| 같은 모양의 객체를 아주 많이 만든다 | `__slots__` — ★ 상속 사슬 전체가 선언해야 한다 |
| 다중 상속을 쓴다 | ★ **`__mro__` 를 먼저 찍어 본다.** 정본은 `[목록의 **34번 주제**](../34-inheritance-mro-super/)` |
| 불변 타입을 상속한다 | `__new__` — `__init__` 으로는 못 채운다 |
| 인스턴스를 재사용(풀·싱글턴)한다 | `__new__` — ★ **`__init__` 이 또 불린다**는 것을 잊지 마라 |
| 값 객체를 만든다 | 사슬의 [30번](../30-repr-eq-hash-contracts/2-summary.md) — `__repr__`·`__eq__`·`__hash__` |

## 핵심 문장

- ★★ **`obj.x` 는 클래스 쪽(MRO)을 먼저 훑는다.** 「인스턴스가 먼저」는 **결과**이지 절차가 아니고,
  그 차이가 드러나는 자리가 **데이터 디스크립터**다.
- ★★ **우선순위는 네 층이고 문서가 한 문장으로 적어 놓았다** —
  데이터 디스크립터 > 인스턴스 칸 > 비데이터 디스크립터 > 클래스 변수.
  판별식은 **`__set__` 의 유무** 하나다.
- ★★ **클래스 칸의 가변 객체는 한 개다.** `append` 는 그 한 개를 늘리고(인스턴스 칸은 **빈 채**),
  대입은 인스턴스 칸을 만들며, **`+=` 는 둘 다 한다.**
  [20번](../20-mutable-default-args/2-summary.md)의 가변 기본 인자와 **같은 집안**이고 처방도 같다.
- ★★ **`super()` 는 「부모」가 아니라 「그 인스턴스의 MRO 에서 내 다음」이다.**
  실측에서 같은 `Left.go` 안의 같은 한 줄이 `Left()` 에서는 `Base` 로, `Both()` 에서는 `Right` 로 갔다.
- ★ **`__getattr__` 은 실패했을 때만, `__getattribute__` 는 무조건 불린다.**
  그래서 `hasattr` 가 `True` 를 답해도 **`vars()` 에는 아무것도 없을 수 있다** — 제5의 상태다.
- ★ **`__slots__` 가 만드는 것은 데이터 디스크립터**다(`member_descriptor`).
  별도 장치가 아니라 **디스크립터 규칙의 한 사례**이고, 그래서 인스턴스 칸을 이긴다.
  **하위 클래스가 안 쓰면 효과가 풀린다.**
- ★ **MRO 는 C3 이고 못 만드는 순서가 있다.** `class Bad(A, B)` 는 **정의 시점에 `TypeError`** 이며
  그 문구에는 **개행이 박혀 두 줄로** 나온다.
- ★ **`__new__` 가 cls 의 인스턴스를 안 돌려주면 `__init__` 이 안 불린다.**
  거꾸로, 풀에서 꺼낸 **기존 객체를 돌려주면 `__init__` 이 또 불린다.**
- ★★ **특수 메서드는 클래스 칸에서 찾는다** — 이 한 줄이 사슬의 [30](../30-repr-eq-hash-contracts/2-summary.md)·[31](../31-comparison-protocol-and-sortability/2-summary.md)·[32](../32-container-protocol/2-summary.md)를 전부 떠받친다.

## 관련 자료

- 목록: [python/syntax 주제 목록](../README.md) — 이 주제는 **29번**
- 선행: [01-object-and-name-binding](../01-object-and-name-binding/2-summary.md) — 이름이 객체에 붙는 모델.\
  **경계**: 대입이 이름을 묶는다는 것은 그쪽, **속성 칸이 어디에 사는가**는 여기.
- 선행: [21-scope-legb-global-nonlocal](../21-scope-legb-global-nonlocal/2-summary.md) — **이름 탐색의 정본.**\
  **경계**: `x` 를 LEGB 로 푸는 것은 전부 그쪽이다. 여기는 **`obj.x` 를 인스턴스 → 클래스 → MRO 로 푸는 것**뿐이다.
  ★ **둘은 다른 탐색이다** — 클래스 몸통의 이름을 메서드가 이름으로 못 보는 이유도 그쪽에 있다.
- 선행: [20-mutable-default-args](../20-mutable-default-args/2-summary.md) — **가변 기본 인자의 정본.**\
  **경계**: 「한 번 만들어진 가변 객체를 나눠 쓴다」는 구조는 그쪽이 정본이고,
  여기는 **클래스 칸에서 같은 일이 일어난다**는 것만 링크로 잇는다.
- 선행: [03-mutability-and-copying](../03-mutability-and-copying/2-summary.md) — 고치기와 새로 묶기.\
  **경계**: `append` 와 대입의 차이는 그쪽, **그 차이가 어느 칸을 만드는가**는 여기.
- 함께 보는 곳: [12-dict-and-key-requirements](../12-dict-and-key-requirements/2-summary.md) —
  `__dict__` 가 그냥 `dict` 라서 **삽입 순서가 보장**된다. 그쪽이 정본이다.
- 이어지는 곳: [30-repr-eq-hash-contracts](../30-repr-eq-hash-contracts/2-summary.md) — **이 사슬의 다음.**
  클래스 칸에 특수 메서드를 놓는 일이 **계약**이 되는 자리다.
- 이어지는 곳: `[목록의 **33번 주제**](../33-property-descriptor-slots/)` — `property`·디스크립터·`__slots__` 의 정본.
  여기서는 **속성 탐색에 필요한 만큼만** 다뤘다.
- 이어지는 곳: `[목록의 **34번 주제**](../34-inheritance-mro-super/)` — 상속·MRO·`super()` 의 정본.
  여기서는 **탐색 순서를 설명하는 데 필요한 만큼만** 다뤘다.
- 이어지는 곳: `[목록의 **36번 주제**](../36-dataclasses/)` — `dataclasses`. 클래스 칸에 메서드를 **자동으로** 넣어 주는 장치다.
- 기존 주제: [`../../../../oop-basics/`](../../../../oop-basics/) — 클래스·객체 일반론.
  여기는 그 일반론을 **파이썬의 칸 구조로** 좁혀 받는다.
- 다른 갈래: 자바 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **09번** — 상속과 오버라이딩.
  자바는 **단일 상속**이라 MRO 가 필요 없고, 필드는 **가리기**(hiding)이지 오버라이딩이 아니다.
- 다른 갈래: C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **18번** — `record`.
  클래스 칸에 멤버를 자동 생성한다는 점이 `dataclasses` 와 같은 자리다.
- 공식 문서: [Custom classes](https://docs.python.org/3.12/reference/datamodel.html#custom-classes) ·
  [Class instances](https://docs.python.org/3.12/reference/datamodel.html#class-instances) ·
  [Customizing attribute access](https://docs.python.org/3.12/reference/datamodel.html#customizing-attribute-access) ·
  [Invoking Descriptors](https://docs.python.org/3.12/reference/datamodel.html#invoking-descriptors) ·
  [`super()`](https://docs.python.org/3.12/library/functions.html#super)

## 용어 풀이

- **속성(attribute)**: 점 뒤에 오는 이름. `obj.x` 의 `x`.\
  예: 변수 이름과는 **탐색 규칙이 다르다.**
- **인스턴스 칸(instance dictionary)**: 그 객체만의 `dict`. `vars(obj)` 로 연다.\
  예: `self.x = 1` 이 여기에 넣는다.
- **클래스 칸(class dictionary)**: 클래스 하나가 가진 `dict`. `Cls.__dict__` 로 연다.\
  예: 클래스 몸통의 대입과 `def` 가 여기에 들어간다.
- **MRO(method resolution order)**: 조상을 훑을 순서를 한 줄로 편 것.\
  예: `D(B, C)` 에서 `D → B → C → A → object`.
- **C3 선형화(C3 linearization)**: MRO 를 만드는 규칙. **못 만드는 순서가 있다.**\
  예: `class Bad(A, B)` 에서 `A` 가 `B` 의 조상이면 `TypeError`.
- **디스크립터(descriptor)**: `__get__` 을 가진 객체. **클래스 칸에 놓이면** 접근을 가로챈다.\
  예: 함수가 바로 이것이다.
- **데이터 디스크립터(data descriptor)**: `__get__` 과 함께 `__set__`(또는 `__delete__`)을 가진 것.\
  예: **인스턴스 칸을 이긴다.** `property` 와 `__slots__` 의 칸이 여기 속한다.
- **비데이터 디스크립터(non-data descriptor)**: `__get__` 만 가진 것.\
  예: 함수. **인스턴스 칸에 지면** 그쪽이 불린다.
- **`__getattr__`**: 기본 탐색이 **실패했을 때만** 불리는 갈고리.\
  예: 있는 이름에는 안 불린다.
- **`__getattribute__`**: **무조건** 불리는 갈고리.\
  예: 그 안에서 `self.x` 를 쓰면 무한 재귀가 된다.
- **`__slots__`**: 인스턴스의 `__dict__` 를 없애고 **고정된 칸**만 두는 선언.\
  예: 클래스 칸에 `member_descriptor` 가 생긴다.
- **`super()`**: **MRO 상 내 다음**에게 넘기는 프록시.\
  예: 부모가 아니라 형제일 수 있다.
- **`__new__`**: 객체를 **만드는** 단계. `__init__` 은 **채우는** 단계.\
  예: cls 의 인스턴스를 안 돌려주면 `__init__` 이 안 불린다.
- **가리기(shadowing)**: 앞 칸의 이름이 뒤 칸의 같은 이름을 덮어 보이지 않게 하는 것.\
  예: 인스턴스 칸의 `kind` 가 클래스 칸의 `kind` 를 가린다. **지우면 다시 드러난다.**
- **협력적 다중 상속(cooperative multiple inheritance)**: 모든 참여자가 `super()` 를 불러 체인을 잇는 방식.\
  예: 한 군데만 빼먹어도 그 뒤가 통째로 안 돈다.

## 더 들어가면

- ★ **`__set_name__`(3.6+)** — 디스크립터가 **자기가 어느 이름으로 놓였는지** 알게 해 주는 갈고리다.
  이것이 없던 시절에는 이름을 손으로 넘겨야 했다. **이 주제에서는 안 돌려 봤다.**
- ★ **`__getattr__` 과 `__setattr__` 의 비대칭** — 문서가 그것을 **의도한 비대칭**이라고 밝힌다
  (*"This is an intentional asymmetry"*). `__setattr__` 은 **무조건** 불린다.
  그래서 대입 쪽 갈고리는 `__getattribute__` 와 같은 재귀 위험을 갖는다. **안 돌려 봤다.**
- ★ **메타클래스** — 클래스 자신도 객체이므로 `Cls.x` 역시 **`type(Cls)` 의 MRO** 를 탄다.
  즉 이 문서의 그림이 **한 층 위에서 한 번 더** 적용된다. **안 돌려 봤다.**
- ★ **`__mro_entries__`(PEP 560)** — 제네릭 별칭을 베이스에 쓸 수 있게 해 주는 장치다.
  MRO 계산 **앞단**에 끼어든다. **안 돌려 봤다.**
- ★ **`__slots__` 와 `__weakref__`** — `__slots__` 를 쓰면 약한 참조 칸도 사라진다.
  필요하면 `'__weakref__'` 를 목록에 넣는다. **안 돌려 봤다.**
- ★ **`object.__getattribute__` 를 읽는 것이 이 주제의 끝이다** — 동작 2의 그림이 결국 그 함수 하나의 흐름이다.
  CPython 에서는 `Objects/object.c` 의 일반 속성 조회 함수가 그 자리이고,
  **거기서 데이터 디스크립터 검사가 인스턴스 칸 조회보다 먼저 온다**고 문서가 말한다.
  ★ **소스는 이번에 안 읽었다** — 읽은 것은 3.3.2.3 의 문장 하나뿐이다.
