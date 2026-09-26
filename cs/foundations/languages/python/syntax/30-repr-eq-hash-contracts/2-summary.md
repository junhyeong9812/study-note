# python/syntax/30-repr-eq-hash-contracts — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만.
> - [3.3.1. Basic customization — `object.__hash__`](https://docs.python.org/3.12/reference/datamodel.html#object.__hash__) — **`__eq__` 만 정의하면 `__hash__` 가 `None` 이 되는 규칙**과 되살리는 법
> - [`object.__repr__`](https://docs.python.org/3.12/reference/datamodel.html#object.__repr__) · [`object.__str__`](https://docs.python.org/3.12/reference/datamodel.html#object.__str__) — 「공식」과 「비공식」 표현, 그리고 **한쪽이 다른 쪽을 대신하는 방향**
> - [`object.__eq__`](https://docs.python.org/3.12/reference/datamodel.html#object.__eq__) — 사용자 정의 클래스의 기본 동작
> - [glossary — hashable](https://docs.python.org/3.12/glossary.html#term-hashable) — 해시 가능의 정의 세 조각
> - **이 머신의 표준 라이브러리 소스** `/usr/lib/python3.12/dataclasses.py` — `_hash_action` 표(8행)를 **직접 읽었다.** `dataclass` 절의 근거는 문서가 아니라 이 표다.
>
> **실행 검증** — 이 문서에 실린 출력은 전부 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.\
> ★ 던지는 형태를 하나로 고정했다 — `python3 - <파일` 로 던져 트레이스백이 `File "<stdin>", line N` 이 된다.\
> ★★ **캐럿은 예외 종류에 달렸다** — 실행 중 예외는 소스 줄도 `^` 캐럿도 안 나오고, `SyntaxError` 라야 둘 다 나온다.
> 이 문서의 트레이스백 두 벌은 전부 **실행 중 예외**라 **세 줄짜리**다.\
> ★ **`dataclass` 의 `FrozenInstanceError` 는 트레이스백 대신 타입·메시지로 찍었다** —
> 그 예외는 스택이 `dataclasses.py` 를 지나 **절대경로가 박히므로** 다른 머신에서 재현이 안 된다.\
> **버전** — 세 메서드의 계약 자체는 Python 3 내내 같다. 갈리는 것은 둘이다 —
> `dataclasses` 가 **3.7+**, `str`·`bytes` 해시 무작위화가 **기본 켜짐은 3.3+**(PEP 456 이전에는 `-R` 옵션이었다).\
> **구현 대 언어 보장 한 줄** — **「`==` 면 해시도 같아야 한다」는 계약과 `__eq__` 만 정의했을 때 `__hash__` 가 `None` 이 되는 것까지가 언어 보장**이고,
> **계약을 어겼을 때 정확히 무엇이 나오나(키 개수·어느 조회가 실패하나)와 `dict`·`set`·`list` 의 정체 지름길은 CPython 구현**이다.
>
> ★ **흔들리는 칸 / 안 흔들리는 칸** — 재대조에서 「고칠 것」과 「설계상 안 맞는 것」을 기계적으로 가르려고 미리 선언한다.
>
> | 흔들린다 | 안 흔들린다(근거로 써도 되는 칸) |
> |---|---|
> | `id()` 와 `0x…` 주소 — **그래서 이 주제는 한 번도 안 찍었다** | 예외 **종류** · `File "<stdin>", line N` · `(exit N)` |
> | **해시값 자체**(`hash('key')` — 실행마다 다르다) | 해시가 **「같은가 다른가」** |
> | 판이 오르면 예외 **문구**와 내부 타입 이름 | **호출 로그의 순서** · `__eq__` 가 **불렸나 안 불렸나** |
> | — | `len()` · **키 개수** · `sorted()` 한 결과 |
> | — | `dict` 의 **삽입 순서**(3.7+ 언어 보장) |
>
> ★★★ **이 주제는 해시값을 찍고 싶어지는 주제다.** 그런데 첫 블록이 `sys.flags.hash_randomization` 을 `True` 로 답했다 —
> **문자열 해시는 프로세스마다 소금이 다르다.** 그래서 이 문서는 값 대신 「**같은가 다른가**」만 근거로 쓴다.
> 예외는 **정수의 해시**뿐인데, 그것도 **CPython 구현**으로 따로 분류했다(동작 6).\
> ★ **순서가 보장 안 되는 출력은 한 곳도 없다** — `set` 을 찍은 자리는 전부 `len()` 이고, `dict` 의 키는 `sorted()` 를 거쳤다.
>
> **선행** — [12번](../12-dict-and-key-requirements/2-summary.md)(★★★ **키 요건의 정본.** 여기는 그 위에서 **클래스 쪽 계약**만) ·
> [02번](../02-is-vs-eq-interning/2-summary.md)(**`is` 와 `==` 의 정본** — 정체 지름길을 읽으려면 필요하다) ·
> [29번](../29-classes-and-attribute-lookup/2-summary.md)(**클래스 칸에 `__hash__` 가 `None` 으로 박힌다**는 것을 보려면 속성 탐색을 알아야 한다) ·
> [13번](../13-set-and-frozenset/2-summary.md)(같은 해시 기계의 「순서 없는」 쪽).\
> **이 사슬** — [29](../29-classes-and-attribute-lookup/2-summary.md) → 30 → [31](../31-comparison-protocol-and-sortability/2-summary.md) → [32](../32-container-protocol/2-summary.md).
> 29 가 「속성이 어디서 오나」를 깔고, 30 이 **「같음」의 계약**을, 31 이 **「순서」의 계약**을, 32 가 **「담음」의 계약**을 잇는다.\
> ★★★ **30·31·32 는 「프로토콜이 곧 계약」인 주제다** — 어기면 컴파일러가 아니라 **자료구조가 조용히 틀린다.** 그 점이 정적 언어와의 대비다.

## 한눈에 — 쉽게 말하면

**세 메서드는 하는 일이 다르고, 그중 둘만 한 몸이다.**

```text
   __repr__   이 물건이 무엇인지 사람에게 보여 주는 명찰      (혼자 산다)

   __eq__     이 둘이 같은 물건인가                    \
                                                       >  한 몸이다
   __hash__   이 물건을 어느 사물함에 넣을 것인가        /
```

- `__repr__` 을 잘못 써도 **아무것도 안 망가진다.** 사람이 헷갈릴 뿐이다.
- `__eq__` 와 `__hash__` 를 **어긋나게** 쓰면 **`dict` 와 `set` 이 조용히 틀린 답을 낸다.**
- ★★★ **예외가 안 난다.** 그것이 이 주제의 전부다.

**비유 — 사물함이 있는 물품보관소.**

```text
   물건을 맡긴다                          물건을 찾는다

   hash(물건)  ->  "7번 칸"                hash(물건)  ->  "7번 칸"
        |                                       |
        v                                       v
   +---+---+---+---+---+---+---+---+       7번 칸만 열어 본다
   | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |       그 안의 것과 == 로 대조
   +---+---+---+---+---+---+---+---+
                               ^
                            여기 넣는다

   ★ 칸 번호가 어긋나면 == 는 불릴 기회조차 없다
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 물건에 붙은 명찰 | `__repr__` | `repr(x)` 가 기본 꼴이 아니다 |
| 사람에게 읽어 주는 이름 | `__str__` | `str(x)` 가 `repr(x)` 와 다르다 |
| 이 둘이 같은 물건인가 | `__eq__` | `a == b` 가 참이다 |
| 몇 번 칸에 넣을 것인가 | `__hash__` | 두 해시가 **같은가 다른가** |
| ★ 칸 번호가 어긋났다 | `==` 는 참인데 해시가 다르다 | 넣은 것을 **같은 키로 못 꺼낸다** |
| ★ 맡기는 것 자체를 거부한다 | `__hash__` 가 `None` | `TypeError: unhashable type` |
| 창고를 통째로 뒤진다 | `list` 의 `in` | **계약을 어겨도 멀쩡하다** |
| ★ 맡긴 사람 얼굴을 먼저 본다 | 정체 지름길(`x is y`) | `__eq__` 가 **안 불린다** |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.\
「**대소문자를 무시해서 비교하자**」고 `__eq__` 만 고치고 `__hash__` 를 그대로 둔 것,\
그리고 「**`__eq__` 를 넣었더니 갑자기 `set` 에 안 들어간다**」가 그것이다.\
앞엣것은 **조용하고**, 뒤엣것은 **시끄럽다.** 언어가 반쪽만 막아 주기 때문이다.

> **해시 가능(hashable)** — 평생 안 바뀌는 해시값이 있고(`__hash__`), 다른 것과 비교할 수 있는(`__eq__`) 객체.\
> 예: `int`·`str`·`tuple`·`frozenset` 은 해시 가능하고 `list`·`dict`·`set` 은 아니다.

> **계약(contract)** — 언어가 문법으로 강제하지 않지만 **지킨다고 믿고 자료구조가 돌아가는 약속**.\
> 예: 「`a == b` 면 `hash(a) == hash(b)` 여야 한다」. 어겨도 컴파일 에러가 안 나고 **답만 틀린다.**

> **정체 지름길** — 두 이름이 **같은 객체**를 가리키면 `==` 를 부르지 않고 「같다」로 처리하는 것.\
> 예: `d.get(k)` 에서 `k` 가 넣을 때 쓴 바로 그 객체면 `__eq__` 가 아예 안 불린다.

먼저 이 문서를 돌린 판을 찍어 둔다. **`hash_randomization` 이 켜져 있다**는 사실이 이 주제의 모든 인용 방식을 정한다.

```python
# e30_version.py
import sys

print("version_info =", sys.version_info)
print("implementation =", sys.implementation.name)
print("platform =", sys.platform)
print("해시 무작위화 켜져 있나 :", bool(sys.flags.hash_randomization))
```

```text
===== python3 - <e30_version.py =====
version_info = sys.version_info(major=3, minor=12, micro=3, releaselevel='final', serial=0)
implementation = cpython
platform = linux
해시 무작위화 켜져 있나 : True
(exit 0)
```

## 이 주제가 답하려는 질문

1. **세 메서드의 계약이 정확히 무엇인가** — 무엇이 강제되고 무엇이 사람 몫인가.
2. **`__eq__` 만 정의하면 왜 해시가 깨지는가** — 그리고 고치는 두 방법 중 어느 쪽이 계약까지 지켜 주나.
3. **계약을 어기면 무엇이 어떻게 틀리는가** — 예외인가, 조용한 오답인가. 정적 타입 언어에서는 무엇이 다른가.

★ 셋째 질문이 이 주제의 인출 목표다.
**「`len` 과 순회에는 보이는데 조회만 실패한다」와 「`list` 는 멀쩡하다」를 대는 것**이 아는 것과 들은 것의 경계다.

## 동작 방식

> 이 절이 본문이다. 이 주제의 진단창은 넷이고, **네 번째가 결정적**이다.
>
> | 창 | 무엇을 묻나 | 어긴 타입에서 |
> |---|---|---|
> | ① `a == b` 가 참인가 | 「같다」고 말하나 | **참이다** — 여기는 정상으로 보인다 |
> | ② 해시가 **같은가**(값이 아니라 같음 여부) | 같은 칸에 가나 | **다르다** — 여기서 이미 깨졌다 |
> | ③ `len()` 과 순회에 보이나 | 자료가 들어 있나 | **보인다** — 여기도 정상으로 보인다 |
> | ★★★ ④ **조회가 되나** | 키로 닿을 수 있나 | **안 된다** — 여기서만 드러난다 |
>
> ★ **①③ 만 보면 아무 문제가 없다.** `print(d)` 도 `len(d)` 도 멀쩡하다.
> **②④ 를 일부러 물어야** 계약 위반이 보인다.\
> ★ ②를 「해시값을 찍어 보자」로 하면 **재현이 안 되는 근거**가 된다 — 반드시 「**같은가**」로 묻는다.

### 1. ★ 세 메서드의 자리 — 무엇이 강제되고 무엇이 사람 몫인가

**언제 쓰나** — 내 클래스를 `dict` 키나 `set` 원소로 쓸 때. 그리고 「셋 중 무엇까지 써야 하나」가 막힐 때.

문서가 계약을 한 문장으로 적는다 —
*"The only required property is that **objects which compare equal have the same hash value**;
it is advised to mix together the hash values of the components of the object that also play a part in comparison of objects
by packing them into a tuple and hashing the tuple."*

```text
   계약은 한 방향이다

     a == b   ================>   hash(a) == hash(b)     (지켜야 한다)
              <================
                이 방향은 아니다    (해시가 같아도 딴 값일 수 있다 — 그게 충돌이다)
```

| 메서드 | 약속하는 것 | 언어가 강제하나 |
|---|---|---|
| `__repr__` | 「공식」 표현. 가능하면 **다시 만들 수 있는 식** 꼴 | ✘ — 권고다 |
| `__str__` | 「비공식」 표현. 사람이 읽기 좋은 꼴 | ✘ — 권고다 |
| `__eq__` | 동치 관계(반사·대칭·추이) | ✘ — 사람이 지킨다 |
| `__hash__` | ★★★ **`a == b` 이면 `hash(a) == hash(b)`** · 평생 안 바뀐다 | ✘ — 사람이 지킨다 |
| `__eq__` 를 재정의하면 | `__hash__` 가 **`None` 으로 꺼진다** | ✔ — **언어가 강제하는 유일한 자리** |

- ★★★ **강제되는 것은 마지막 한 줄뿐이다.** 「`__eq__` 를 고쳤으면 `__hash__` 도 다시 생각하라」는
  **경고를 언어가 자동으로 켜 주는 것**이지, 내용이 맞는지 보는 것이 아니다.
- ★ **역방향은 계약이 아니다** — 해시가 같은데 `==` 가 다른 것은 **합법**이다(동작 6의 `AlwaysZero`).
  느려질 뿐 틀리지 않는다.
- ★ `__repr__` 과 `__str__` 은 **정확성에 관여하지 않는다.** 그런데 **진단을 어렵게 만든다** —
  `repr` 을 안 쓰면 계약이 깨진 객체가 `<... object at 0x...>` 로만 보여 **무엇이 두 개인지조차 모른다.**
  그래서 이 문서의 예제는 계약을 시험할 때 **반드시 `__repr__` 을 먼저 준다.**

**비용** — 없다. 판단 규칙이다.

### 2. ★★★ `__eq__` 만 정의하면 — 언어가 `__hash__` 를 꺼 버린다

**언제 쓰나** — 값이 같으면 같은 객체로 치고 싶어 `__eq__` 를 넣은 직후. 그리고 `unhashable type` 을 처음 봤을 때.

문서가 그 규칙을 직접 적는다 —
*"A class that overrides `__eq__()` and does not define `__hash__()` will have its `__hash__()` **implicitly set to `None`**."*

```text
   class OnlyEq:
       def __eq__(self, other): ...        <- 이 한 줄을 쓰면

   클래스 칸(__dict__) 에 언어가 몰래 한 줄을 더 넣는다

       OnlyEq.__dict__["__hash__"] = None  <- "여기서 끊어라" 라는 표지판

   ->  hash(OnlyEq(1))  는 object 의 __hash__ 까지 못 내려간다
```

```python
# e30_only_eq.py
class OnlyEq:
    def __init__(self, v):
        self.v = v

    def __eq__(self, other):
        return isinstance(other, OnlyEq) and self.v == other.v


print("클래스 칸에 __hash__ 가 있나 :", "__hash__" in OnlyEq.__dict__)
print("그 값                        :", OnlyEq.__dict__.get("__hash__"))
print("OnlyEq.__hash__              :", OnlyEq.__hash__)
print("object.__hash__ 는 있나      :", object.__hash__ is not None)
print("== 는 멀쩡히 된다            :", OnlyEq(1) == OnlyEq(1))
print("이제 해시를 구한다")
hash(OnlyEq(1))
```

```text
===== python3 - <e30_only_eq.py =====
클래스 칸에 __hash__ 가 있나 : True
그 값                        : None
OnlyEq.__hash__              : None
object.__hash__ 는 있나      : True
== 는 멀쩡히 된다            : True
이제 해시를 구한다
Traceback (most recent call last):
  File "<stdin>", line 15, in <module>
TypeError: unhashable type: 'OnlyEq'
(exit 1)
```

그림 해설.

- ★ **「잊어버린다」가 아니라 「언어가 끈다」.** `__hash__` 가 **클래스 칸에 `None` 으로 실제로 들어 있다** —
  첫 두 줄이 그것이다. 상속으로 `object.__hash__` 를 물려받는 길이 **`None` 이라는 표지판에 막힌 것**이다.
  ★ 이것은 [29번](../29-classes-and-attribute-lookup/2-summary.md)의 **속성 탐색이 인스턴스 → 클래스 → MRO 순서**라는 성질을 그대로 쓴 것이다.
  더 가까운 칸에 `None` 이 있으니 뒤의 `object.__hash__` 는 보이지도 않는다.
- **`==` 는 멀쩡히 된다.** 그래서 **`__eq__` 만 쓰고 한동안 잘 굴러간다** — `set` 이나 `dict` 에 넣는 순간 터진다.
- ★ **트레이스백이 세 줄이다.** `Traceback` 머리줄 · `File "<stdin>", line 15, in <module>` · `TypeError` 한 줄.
  **소스 줄도 `^` 캐럿도 없다** — 실행 중 예외라 그렇다(`SyntaxError` 라야 둘 다 나온다).
- **종료 코드가 `1` 이다.** 「예외로 끝났다」가 출력이다.

같은 일이 `dict` 키로 쓸 때도 똑같이 난다. **문구가 한 글자도 같다.**

```python
# e30_only_eq_dict.py
class OnlyEq:
    def __init__(self, v):
        self.v = v

    def __eq__(self, other):
        return isinstance(other, OnlyEq) and self.v == other.v


print("dict 키로 쓰면")
{OnlyEq(1): "값"}
```

```text
===== python3 - <e30_only_eq_dict.py =====
dict 키로 쓰면
Traceback (most recent call last):
  File "<stdin>", line 10, in <module>
TypeError: unhashable type: 'OnlyEq'
(exit 1)
```

- ★ **줄 번호만 다르다**(`line 15` 대 `line 10`). 예외 종류도 문구도 같다 —
  `dict` 키로 쓰는 것이 결국 `hash()` 를 부르는 것이기 때문이다.
- ★★ **이쪽은 시끄러운 실패다.** 이 주제에서 **예외가 나 주는 자리는 여기뿐**이고,
  나머지는 전부 조용하다. **그 비대칭이 이 주제에서 가장 헷갈리는 자리다.**

**비용** — 없다. 오히려 **언어가 공짜로 주는 방어선**이다.\
`__eq__` 만 고친 타입은 **애초에 키가 못 되므로**, 동작 4의 사고를 내려면 **`__hash__` 를 일부러 써야 한다.**

### 3. ★ 고치는 법 둘 — 그런데 하나는 계약을 안 지킨다

**언제 쓰나** — `unhashable type` 을 고칠 때. 검색하면 두 가지 처방이 같이 나온다.

문서가 둘째 처방을 적어 둔다 —
*"If a class that overrides `__eq__()` needs to retain the implementation of `__hash__()` from a parent class,
the interpreter must be told this explicitly by setting `__hash__ = <ParentClass>.__hash__`."*

```text
   ① 같이 정의한다                         ② object 의 것을 되살린다

   def __hash__(self):                     __hash__ = object.__hash__
       return hash(self.v)
        |                                        |
        v                                        v
   값이 같으면 해시도 같다                   객체마다 해시가 다르다
   -> 계약을 지킨다                          -> 해시는 되는데 계약은 깨진다
```

```python
# e30_two_fixes.py
class Fix1:                                  # ① __hash__ 를 같이 정의한다
    def __init__(self, v):
        self.v = v

    def __eq__(self, o):
        return isinstance(o, Fix1) and self.v == o.v

    def __hash__(self):
        return hash(self.v)

    def __repr__(self):
        return "Fix1(%r)" % self.v


class Fix2:                                  # ② object 의 것을 되살린다
    def __init__(self, v):
        self.v = v

    def __eq__(self, o):
        return isinstance(o, Fix2) and self.v == o.v

    __hash__ = object.__hash__

    def __repr__(self):
        return "Fix2(%r)" % self.v


for cls in (Fix1, Fix2):
    a, b = cls(1), cls(1)
    d = {a: "첫째"}
    d[b] = "둘째"
    print(cls.__name__,
          "| 해시가 되나 :", cls.__hash__ is not None,
          "| a == b :", a == b,
          "| 해시가 같은가 :", hash(a) == hash(b),
          "| 키 개수 :", len(d),
          "| 남은 것 :", d)

print()
print("② 의 해시는 정체 기준이다 — object.__hash__ 와 같은 것인가")
print("   Fix2.__hash__ is object.__hash__ :", Fix2.__hash__ is object.__hash__)
print("   같은 객체면 해시도 같다          :", (lambda x: hash(x) == hash(x))(Fix2(1)))
print("   set 으로 묶어도 :", len({Fix1(1), Fix1(1)}), "대", len({Fix2(1), Fix2(1)}))
```

```text
===== python3 - <e30_two_fixes.py =====
Fix1 | 해시가 되나 : True | a == b : True | 해시가 같은가 : True | 키 개수 : 1 | 남은 것 : {Fix1(1): '둘째'}
Fix2 | 해시가 되나 : True | a == b : True | 해시가 같은가 : False | 키 개수 : 2 | 남은 것 : {Fix2(1): '첫째', Fix2(1): '둘째'}

② 의 해시는 정체 기준이다 — object.__hash__ 와 같은 것인가
   Fix2.__hash__ is object.__hash__ : True
   같은 객체면 해시도 같다          : True
   set 으로 묶어도 : 1 대 2
(exit 0)
```

그림 해설.

- **`Fix1`** — `a == b` 가 참이고 해시도 같다. **키 개수가 1**, 남은 것은 `{Fix1(1): '둘째'}` 다.
  [12번](../12-dict-and-key-requirements/2-summary.md)이 정본으로 적은 그대로 — **키는 처음 것이 남고 값은 나중 것이 이긴다.**
- ★★★ **`Fix2`** — `a == b` 는 여전히 **참**인데 **해시는 다르다.** 그래서 **키 개수가 2** 가 되고
  남은 것이 `{Fix2(1): '첫째', Fix2(1): '둘째'}` 다.
  **똑같이 보이는 키가 둘 들어 있다.** 이 한 줄이 이 절의 그림 전부다.
- ★ **둘째 처방은 「해시 가능하게 만들기」이지 「계약 지키기」가 아니다.**
  `Fix2.__hash__ is object.__hash__` 가 참이고, 그 해시는 **정체 기준**이다.
  문서가 그 기본 동작을 적는다 — *"`x.__hash__()` returns an appropriate value such that `x == y` implies both that `x is y` and `hash(x) == hash(y)`."*
  ★ 그 문장은 **`__eq__` 도 기본인 경우**의 이야기다. `__eq__` 만 값 기준으로 바꿔 놓으면
  **전제가 깨져 결론(해시가 같다)이 안 따라온다.**
- **`set` 으로 묶어도 같다** — `1` 대 `2`.
- ★ **그래서 둘째 처방이 맞는 자리는 하나뿐이다** — **`__eq__` 를 정체 기준으로 두고 싶은데
  다른 이유로 `__eq__` 를 재정의한** 경우(예: 하위 클래스 검사를 덧붙였을 뿐인 경우).
  값 기준 `__eq__` 를 쓰면서 이 처방을 쓰면 **동작 4 와 같은 사고**가 난다.

**비용** — `Fix1` 쪽은 `hash(self.v)` 한 번이 는다.\
★ **어느 쪽이 빠른지는 안 쟀다** — 이 문서에 성능 주장은 없다.

### 4. ★★★ 계약을 어긴 키 — `dict` 가 값을 잃는다

**언제 쓰나** — 이 절이 이 주제의 본체다.
「**대소문자를 무시해서 비교하자**」는 아주 흔한 요구이고, `__eq__` 만 고치고 `__hash__` 를 안 고치면 바로 이 모양이 된다.

★★★ 이 실험은 **Rust 갈래의 같은 실험을 파이썬으로 옮긴 것**이다 —
[Rust 28 §(3)](../../../rust/syntax/28-partialeq-eq-partialord-ord-and-hash-contracts/2-summary.md)의 `CaseKey` 가 원본이다.
**두 언어에서 같은 코드를 던져 무엇이 같고 무엇이 다른지**를 동작 10 에서 표로 맞춘다.

```text
   넣을 때                               찾을 때

   hash("key")  ->  h1 칸              hash("KEY")  ->  h2 칸
        |                                    |
        v                                    v
   +------+------+------+              +------+------+------+
   | h1   | h2   | ...  |              | h1   | h2   | ...  |
   |CaseKey("key")|     |              |      | 비었다|     |
   +------+------+------+              +------+------+------+
                                          h2 칸만 본다 -> None
                                          h1 칸은 쳐다보지도 않는다
                                          __eq__ 는 불리지도 않는다

   ★ a == b 는 True 다.  그런데 답이 갈린다.
```

```python
# e30_contract_break.py
class CaseKey:
    def __init__(self, s):
        self.s = s

    def __eq__(self, o):                     # 대소문자를 무시하고 비교한다
        return isinstance(o, CaseKey) and self.s.lower() == o.s.lower()

    def __hash__(self):
        return hash(self.s)                  # ★ 원문 그대로 — 여기가 계약 위반이다

    def __repr__(self):
        return "CaseKey(%r)" % self.s


a, b = CaseKey("key"), CaseKey("KEY")
print("a == b 인가        :", a == b)
print("해시가 같은가      :", hash(a) == hash(b))      # ★ 값이 아니라 「같은가」만 본다

d = {}
d[CaseKey("key")] = 1
print("넣은 뒤 len        :", len(d))
print("a 로 꺼내면        :", d.get(a))
print("b 로 꺼내면        :", d.get(b))
print("b in d             :", b in d)
d[CaseKey("KEY")] = 2
print("또 넣은 뒤 len     :", len(d))
print("남아 있는 키들     :", sorted(k.s for k in d))
print("a 로 꺼내면        :", d.get(a))
print("set 에 둘을 넣으면 :", len({CaseKey("key"), CaseKey("KEY")}))
print("list 는 멀쩡하다   :", CaseKey("KEY") in [CaseKey("key")])
print()
print("고친 판 — hash 도 eq 가 보는 것과 같게 만든다")


class Fixed(CaseKey):
    def __hash__(self):
        return hash(self.s.lower())


fa, fb = Fixed("key"), Fixed("KEY")
print("   해시가 같은가 :", hash(fa) == hash(fb))
d2 = {Fixed("key"): 1}
print("   b 로 꺼내면   :", d2.get(fb))
d2[Fixed("KEY")] = 2
print("   또 넣은 뒤 len:", len(d2), "| 남은 값 :", list(d2.values()))
```

```text
===== python3 - <e30_contract_break.py =====
a == b 인가        : True
해시가 같은가      : False
넣은 뒤 len        : 1
a 로 꺼내면        : 1
b 로 꺼내면        : None
b in d             : False
또 넣은 뒤 len     : 2
남아 있는 키들     : ['KEY', 'key']
a 로 꺼내면        : 1
set 에 둘을 넣으면 : 2
list 는 멀쩡하다   : True

고친 판 — hash 도 eq 가 보는 것과 같게 만든다
   해시가 같은가 : True
   b 로 꺼내면   : 1
   또 넣은 뒤 len: 1 | 남은 값 : [2]
(exit 0)
```

그림 해설 — 진단 네 창으로 읽는다.

- ★ **창 ① — `a == b` 가 `True` 다.** 여기는 **정상으로 보인다.**
- ★★★ **창 ② — 해시가 다르다.** 계약이 깨진 지점이 **이 두 줄**이다.
  **해시값은 안 찍었다** — 흔들리는 칸이라 **「같은가」라는 논리값만** 근거로 쓴다.
- ★ **창 ③ — `len` 도 순회도 멀쩡하다.** 넣은 뒤 `len` 이 1 이고, 또 넣으면 2 이고, 키도 둘 다 보인다.
- ★★★ **창 ④ — 조회가 갈린다.** `d.get(a)` 는 `1` 인데 **`d.get(b)` 는 `None`** 이다.
  `a == b` 인데 답이 다르다. `b in d` 도 `False` 다.
  **표가 해시로 칸을 먼저 고르기 때문**이다 — 칸이 다르면 `__eq__` 를 **부를 기회조차 없다.**
- ★★ **같은 키가 둘이 된다.** `CaseKey("KEY")` 를 또 넣으니 `len` 이 **2** 가 됐다.
  `dict` 의 불변식(「같은 키는 하나」)이 **밖에서 깨진 것**이다.
  그래서 마지막에 `d.get(a)` 가 여전히 `1` 이다 — **덮어쓰기가 안 일어났다.**
- **`set` 도 같다** — 둘을 넣으니 `2` 다. 중복 제거가 안 된다.
- ★★★ **`list` 는 멀쩡하다.** `CaseKey("KEY") in [CaseKey("key")]` 가 `True` 다.
  **리스트는 해시를 안 쓰고 앞에서부터 `==` 로 훑기 때문**이다.
  이 비대칭이 진단을 어렵게 만든다 — 「`==` 는 맞게 썼는데 왜 `dict` 에서만?」
  ★ Java 갈래도 **똑같은 비대칭**을 실측했다([Java 27 「어디서 틀리나」 1번](../../../java/syntax/27-equals-hashcode-contract/2-summary.md)의 `List.contains : true`).
- ★ **처방은 하나다** — **`__eq__` 가 보는 것과 `__hash__` 가 섞는 것을 같게** 한다.
  `Fixed` 는 `hash(self.s.lower())` 한 줄만 바꿨고, 그러자 **해시가 같아지고 · 조회가 되고 · `len` 이 1 로 돌아왔다.**
  ★ 남은 값이 `[2]` 다 — 이제 **덮어쓰기가 제대로 일어난다.**

**비용** — 이 사고는 **예외가 안 난다.**\
계약을 지키는 비용은 `hash` 한 줄이고, 어긴 비용은 **언제 드러날지 모르는 오답**이다.

> **버킷(bucket)** — 해시 테이블에서 해시값으로 고른 칸.\
> 예: `hash(k) % 표크기` 로 정해진다. 칸을 먼저 고르므로 **칸이 틀리면 그 안의 `==` 는 안 돈다.**\
> ★ 원리는 [`cs/data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/)이 정본이다.
> **경계**: 그쪽은 「왜 평균 O(1) 인가」까지, 여기는 「**계약을 어기면 어디가 틀리나**」부터다.

### 5. ★★ 반사성을 깨면 — 그런데 파이썬에는 지름길이 있다

**언제 쓰나** — `__eq__` 가 **자기 자신과도 거짓**이 될 수 있는 타입을 만들 때.
`float('nan')` 이 실제로 그런 값이고, 그 성질을 흉내 낸 것이 아래 `Never` 다.

```text
   반사성이란     a == a  가 참이어야 한다는 것

   Never 는 그것을 깬다 — __eq__ 가 늘 False 를 돌려준다

   d = {k: "값"}       넣을 때는 아무 문제가 없다(해시는 정직하다)
   d.get(k)            ★ 여기서 파이썬과 Rust 가 갈린다
```

```python
# e30_reflexivity.py
class Never:
    def __init__(self, v):
        self.v = v

    def __eq__(self, o):
        print("      __eq__ 가 불렸다")
        return False                          # ★ 자기 자신과도 같지 않다

    def __hash__(self):
        return hash(self.v)

    def __repr__(self):
        return "Never(%r)" % self.v


k = Never(1)
d = {k: "값"}
print("① 넣을 때 쓴 바로 그 객체로 꺼내면")
print("   d.get(k) ->", d.get(k))
print("② 그런데 k == k 는")
print("   ->", k == k)
print("③ 값이 같은 딴 객체로 꺼내면")
print("   d.get(Never(1)) ->", d.get(Never(1)))
print("④ 같은 값을 또 넣으면")
d[Never(1)] = "둘째"
print("   len =", len(d), "| 값들 :", sorted(d.values()))
print("⑤ list 도 정체를 먼저 본다")
xs = [k]
print("   k in xs        ->", k in xs)
print("   Never(1) in xs ->", Never(1) in xs)
print("⑥ set 도 같은 지름길을 쓴다")
s = {k}
print("   k in s        ->", k in s)
print("   Never(1) in s ->", Never(1) in s)
print("   len({k, k}) =", len({k, k}), "| len({Never(1), Never(1)}) =", len({Never(1), Never(1)}))
```

```text
===== python3 - <e30_reflexivity.py =====
① 넣을 때 쓴 바로 그 객체로 꺼내면
   d.get(k) -> 값
② 그런데 k == k 는
      __eq__ 가 불렸다
   -> False
③ 값이 같은 딴 객체로 꺼내면
      __eq__ 가 불렸다
   d.get(Never(1)) -> None
④ 같은 값을 또 넣으면
      __eq__ 가 불렸다
   len = 2 | 값들 : ['값', '둘째']
⑤ list 도 정체를 먼저 본다
   k in xs        -> True
      __eq__ 가 불렸다
   Never(1) in xs -> False
⑥ set 도 같은 지름길을 쓴다
   k in s        -> True
      __eq__ 가 불렸다
   Never(1) in s -> False
      __eq__ 가 불렸다
   len({k, k}) = 1 | len({Never(1), Never(1)}) = 2
(exit 0)
```

그림 해설.

- ★★★ **① 에서 `__eq__` 줄이 한 줄도 안 찍혔다.** 그런데 `'값'` 이 나왔다.
  **넣을 때 쓴 바로 그 객체로 물으면 `dict` 가 `__eq__` 를 아예 안 부른다** — 이것이 **정체 지름길**이다.
  ★ CPython 의 비교 관문이 「두 포인터가 같으면 `Py_EQ` 에 대해 무조건 참」으로 답하기 때문이다.
  ★★ **이것은 CPython 구현이지 언어 보장이 아니다.** 「`dict` 는 정체를 먼저 본다」를 언어 사실로 적지 마라.
- **② 에서 `k == k` 는 `False` 다.** `__eq__` 는 정직하게 거짓을 돌려준다 — **지름길을 안 탄 자리**다.
- **③ 값이 같은 딴 객체로 물으면 `None`** 이다. 여기서는 `__eq__` 가 불렸고 거짓을 답했다.
- ★ **④ 같은 값을 또 넣으면 `len` 이 2** 가 된다. 동작 4 와 같은 모양이다 —
  **한 키가 여러 칸을 차지한다.**
- ★ **⑤⑥ `list` 와 `set` 도 같은 지름길을 쓴다.** `k in xs` 는 `__eq__` 없이 `True` 이고,
  `Never(1) in xs` 는 `__eq__` 를 부른 뒤 `False` 다. `len({k, k})` 가 1 인데 `len({Never(1), Never(1)})` 은 2 다.
- ★★★ **Rust 와 갈리는 자리가 여기다.**
  [Rust 28 §(4)](../../../rust/syntax/28-partialeq-eq-partialord-ord-and-hash-contracts/2-summary.md)의 실측은
  `get`·`contains_key`·`remove` 가 **전부 실패**했고 `remove` 뒤에도 `len` 이 줄지 않았다 —
  **넣은 값이 영영 갇혔다.** 다만 그 실험은 **넣은 객체와 다른 객체**로 물었으므로,
  파이썬의 ③ 과 **직접 대응**한다(파이썬도 ③ 은 `None` 이다).
  **파이썬만 가진 것은 ① 이다** — 같은 객체로 물으면 꺼내진다. 동작 10 의 표가 이 구분을 그대로 옮긴다.

**비용** — 지름길 덕분에 **사고의 절반이 우연히 가려진다.** 그래서 더 늦게 발견된다.\
★ **반사성이 깨지는 값을 키로 쓰지 않는 것**이 처방이다 — 파이썬은 Rust 와 달리 `float` 를 키로 **허용하므로**
`{float('nan'): 1}` 같은 것을 언어가 안 막는다.

### 6. ★ 해시값은 적지 않는다 — 「같은가」만 쓴다

**언제 쓰나** — 해시 관련 실험을 문서로 옮길 때. 그리고 「해시값을 캐시에 저장할까」가 떠올랐을 때.

문서가 이유를 적는다 —
*"By default, the `__hash__()` values of str and bytes objects are **"salted" with an unpredictable random value**.
Although they remain constant within an individual Python process, they are **not predictable between repeated invocations of Python**."*

```text
   같은 프로세스 안                     프로세스가 바뀌면

   hash("key") == hash("key")  참       hash("key") 의 값 자체가 달라진다
        |                                      |
        v                                      v
   근거로 써도 된다                       ★ 문서에 적으면 재현이 안 된다
```

```python
# e30_hash_values.py
import sys

print("① 이 문서에 해시값을 적으면 안 되는 이유")
print("   hash_randomization 플래그 :", bool(sys.flags.hash_randomization))
print("   같은 프로세스 안에서는 같다 :", hash("key") == hash("key"))
print("   그러나 값 자체는 실행마다 달라지므로 적지 않는다")

print("② 적어도 되는 것 — 「같은가 다른가」")
print("   hash(1) == hash(1.0) == hash(True) :", hash(1) == hash(1.0) == hash(True))
print("   그래서 셋은 한 칸이 된다           :", len({1: "a", 1.0: "b", True: "c"}))
print("   hash('key') == hash('KEY')         :", hash("key") == hash("KEY"))

print("③ 정수는 예외적으로 값이 고정돼 있다(CPython 구현)")
print("   hash(1) :", hash(1), "| hash(0) :", hash(0), "| hash(-1) :", hash(-1))
print("   hash(2**61 - 1) :", hash(2 ** 61 - 1))

print("④ 해시가 같아도 같은 값이 아니다 — 충돌은 합법이다")


class AlwaysZero:
    def __init__(self, v):
        self.v = v

    def __eq__(self, o):
        return isinstance(o, AlwaysZero) and self.v == o.v

    def __hash__(self):
        return 0

    def __repr__(self):
        return "AlwaysZero(%r)" % self.v


d = {AlwaysZero(1): "a", AlwaysZero(2): "b"}
print("   해시가 같은가 :", hash(AlwaysZero(1)) == hash(AlwaysZero(2)),
      "| 키 개수 :", len(d), "| 꺼내기 :", d[AlwaysZero(2)])
```

```text
===== python3 - <e30_hash_values.py =====
① 이 문서에 해시값을 적으면 안 되는 이유
   hash_randomization 플래그 : True
   같은 프로세스 안에서는 같다 : True
   그러나 값 자체는 실행마다 달라지므로 적지 않는다
② 적어도 되는 것 — 「같은가 다른가」
   hash(1) == hash(1.0) == hash(True) : True
   그래서 셋은 한 칸이 된다           : 1
   hash('key') == hash('KEY')         : False
③ 정수는 예외적으로 값이 고정돼 있다(CPython 구현)
   hash(1) : 1 | hash(0) : 0 | hash(-1) : -2
   hash(2**61 - 1) : 0
④ 해시가 같아도 같은 값이 아니다 — 충돌은 합법이다
   해시가 같은가 : True | 키 개수 : 2 | 꺼내기 : b
(exit 0)
```

그림 해설.

- ★★★ **`hash_randomization` 이 `True` 다.** 그래서 `hash('key')` 의 **값**은 이 문서 어디에도 없다.
  대신 `hash('key') == hash('KEY')` 가 `False` 라는 **논리값**만 썼다 — 그것은 안 흔들린다.
- **`hash(1) == hash(1.0) == hash(True)` 가 참**이고, 그래서 셋이 한 칸이 된다(키 개수 1).
  ★ 이 사실의 **정본**은 [12번](../12-dict-and-key-requirements/2-summary.md)이다 — 거기서 `Fraction`·`Decimal`·복소수까지 전수로 봤다.
  여기서는 **계약 쪽 결론만** 가져온다 — 「값이 같으면 해시가 같다」를 **타입을 가로질러** 지키는 것이 수 타입의 계약이다.
- ★ **정수의 해시는 값이 고정돼 있다** — `hash(1)` 이 `1`, `hash(0)` 이 `0`, `hash(-1)` 이 `-2`,
  그리고 `hash(2**61 - 1)` 이 `0` 이다. 무작위화는 `str`·`bytes` 에만 걸린다.
  ★★ **그런데 이것은 CPython 구현이다** — 정수 해시가 `2**61 - 1` 을 법으로 쓴다는 것도,
  `-1` 이 `-2` 가 되는 것(`-1` 은 C 층에서 오류 표시로 쓰여 피한다)도 언어 보장이 아니다.
- ★ **④ 충돌은 합법이다.** `AlwaysZero` 는 해시가 늘 `0` 인데 **키 개수가 2** 이고 조회도 제대로 된다.
  계약은 「`==` 면 해시가 같다」 **한 방향**뿐이고, 거꾸로는 요구하지 않는다.
  ★ 이 자리는 [Rust 28 §(2)](../../../rust/syntax/28-partialeq-eq-partialord-ord-and-hash-contracts/2-summary.md)의
  「역방향은 계약이 아니다」와 **한 글자도 같은 규칙**이다.

**비용** — 충돌이 뭉치면 조회가 선형으로 떨어진다.\
★ **얼마나 떨어지는지는 안 쟀다.** 이 문서에 수치는 없다.

### 7. ★ `__repr__` 대 `__str__` — 대신하는 방향이 한쪽뿐이다

**언제 쓰나** — 둘 중 하나만 쓸 때. 그리고 로그에 `<... object at ...>` 가 찍혀 무엇인지 모를 때.

문서가 방향을 적는다 —
*"If a class defines `__repr__()` but not `__str__()`, then **`__repr__()` is also used** when an "informal" string representation of instances of that class is required."*
그리고 반대쪽은 이렇게 적는다 — *"The default implementation defined by the built-in type `object` calls `object.__repr__()`."*

```text
   __repr__ 만 있다                    __str__ 만 있다

   repr(x) -> 내 것                     repr(x) -> 기본 꼴 (주소가 박힌다)
   str(x)  -> 내 것  (대신한다)          str(x)  -> 내 것
        |                                    |
        v                                    v
   ★ 하나만 쓸 거면 __repr__ 을 써라      ★ 컨테이너 안에서는 여전히 기본 꼴이다
```

```python
# e30_repr_str.py
class OnlyRepr:
    def __repr__(self):
        return "<repr 만 있다>"


class OnlyStr:
    def __str__(self):
        return "<str 만 있다>"


class Neither:
    pass


for cls in (OnlyRepr, OnlyStr, Neither):
    o = cls()
    r, s = repr(o), str(o)
    default = "<%s.%s object at 0x" % (cls.__module__, cls.__qualname__)
    print(cls.__name__)
    print("   repr(o) 가 기본 꼴인가 :", r.startswith(default))
    print("   str(o)  가 기본 꼴인가 :", s.startswith(default))
    print("   str(o) == repr(o)      :", s == r)

print()
print("① 컨테이너 안에서는 str 이 아니라 repr 이 쓰인다")
print("   [OnlyStr()] 의 repr 이 기본 꼴인가 :",
      repr([OnlyStr()]).startswith("[<__main__.OnlyStr object at 0x"))
print("   [OnlyRepr()] ->", [OnlyRepr()])
print("② f-string 은 기본이 str, !r 이 repr")
print("   f'{OnlyRepr()}'   ->", "%s" % (OnlyRepr(),))
print("   f'{OnlyRepr()!r}' ->", "%r" % (OnlyRepr(),))
print("③ print 는 str 을 쓴다")
print("   print(OnlyRepr()) ->", end=" ")
print(OnlyRepr())
```

```text
===== python3 - <e30_repr_str.py =====
OnlyRepr
   repr(o) 가 기본 꼴인가 : False
   str(o)  가 기본 꼴인가 : False
   str(o) == repr(o)      : True
OnlyStr
   repr(o) 가 기본 꼴인가 : True
   str(o)  가 기본 꼴인가 : False
   str(o) == repr(o)      : False
Neither
   repr(o) 가 기본 꼴인가 : True
   str(o)  가 기본 꼴인가 : True
   str(o) == repr(o)      : True

① 컨테이너 안에서는 str 이 아니라 repr 이 쓰인다
   [OnlyStr()] 의 repr 이 기본 꼴인가 : True
   [OnlyRepr()] -> [<repr 만 있다>]
② f-string 은 기본이 str, !r 이 repr
   f'{OnlyRepr()}'   -> <repr 만 있다>
   f'{OnlyRepr()!r}' -> <repr 만 있다>
③ print 는 str 을 쓴다
   print(OnlyRepr()) -> <repr 만 있다>
(exit 0)
```

그림 해설.

- ★ **`OnlyRepr`** — `repr` 도 `str` 도 기본 꼴이 아니고 **둘이 같다**(`str(o) == repr(o)` 가 참).
  `__repr__` 이 `__str__` 을 **대신한 것**이다.
- ★★ **`OnlyStr`** — `repr` 이 **기본 꼴**이다(`True`). 거꾸로는 안 대신한다.
- **`Neither`** — 둘 다 기본 꼴이고 서로 같다.
- ★★★ **컨테이너 안에서는 `repr` 이 쓰인다.** `[OnlyStr()]` 의 표현이 **기본 꼴**로 나온다.
  `print(리스트)` 는 `str(리스트)` 인데, 리스트의 `__str__` 이 **원소마다 `repr` 을 부르기** 때문이다.
  **그래서 `__str__` 만 쓰면 리스트에 담는 순간 무용지물이 된다.**
- **`f'{o}'` 는 `str`, `f'{o!r}'` 은 `repr`** 이다. `OnlyRepr` 에서는 둘이 같은 글자를 냈다 — 대신하고 있기 때문이다.
- ★ **주소는 한 번도 안 찍었다.** `0x…` 는 흔들리는 칸이라 **`startswith` 로 「기본 꼴인가」만 물었다.**
  이것이 이 주제 내내 쓴 인용 방식이다.
- ★ **그래서 규칙은 하나다** — **하나만 쓸 거면 `__repr__` 을 써라.**
  ★ 계약을 시험하는 코드에서는 **`__repr__` 이 진단 도구 자체**다. 동작 3 의 `{Fix2(1): '첫째', Fix2(1): '둘째'}` 가
  그렇게 읽힌 것이고, `__repr__` 이 없었으면 **주소 두 개**만 보였을 것이다.
- ★ Java 쪽도 같은 자리를 **권고**로 규정한다 —
  [Java 27 §(4)](../../../java/syntax/27-equals-hashcode-contract/2-summary.md)의 `toString` 은
  javadoc 이 「계약이 아니라 권고」이고 「실행 간에 안정적이지 않다」고 적어 둔 것을 인용했다.

**비용** — 없다. 다만 `__repr__` 에서 무거운 일을 하면 **디버거가 멈춘다.**

### 8. ★ `dataclass` 가 셋을 만드는 규칙 — 표가 소스에 있다

**언제 쓰나** — `@dataclass` 를 붙인 클래스를 `set` 이나 `dict` 에 넣으려 할 때.

★ 근거는 문서가 아니라 **이 머신의 표준 라이브러리 소스**다 —
`/usr/lib/python3.12/dataclasses.py` 의 `_hash_action` 표(8행)를 직접 읽었다.
축이 **넷**이다 — `unsafe_hash` · `eq` · `frozen` · **클래스 몸통에 `__hash__` 를 직접 썼나**.

```text
   소스의 표를 축 셋으로 줄여 옮긴 것 (직접 쓴 __hash__ 가 없을 때)

   unsafe_hash  eq     frozen   ->  __hash__ 에 무슨 일이
   -----------------------------------------------------------
   False        False  아무거나 ->  건드리지 않는다 (물려받은 것 그대로)
   False        True   False    ->  None 을 박는다  ★ 기본값이다
   False        True   True     ->  만들어 준다
   True         아무거나 아무거나 ->  만들어 준다
```

```python
# e30_dataclass.py
from dataclasses import dataclass


@dataclass                                     # 기본값 — eq=True, frozen=False
class D1:
    v: int


@dataclass(eq=False)
class D2:
    v: int


@dataclass(frozen=True)                        # frozen=True, eq=True
class D3:
    v: int


@dataclass(unsafe_hash=True)                   # eq=True, frozen=False 인데 해시를 만든다
class D4:
    v: int


rows = [("D1 기본(eq=True)", D1), ("D2 eq=False", D2),
        ("D3 frozen=True", D3), ("D4 unsafe_hash=True", D4)]

print("① 클래스 칸의 __hash__ 가 어떻게 갈리나")
for label, cls in rows:
    own = "__hash__" in cls.__dict__
    val = cls.__dict__.get("__hash__", "(칸에 없음)")
    print("   %-20s | 칸에 있나 %-5s | 그 값이 None 인가 %-5s | 해시가 되나 %s"
          % (label, own, (val is None) if own else "-", cls.__hash__ is not None))

print()
print("② 되는 것들은 값으로 묶이나")
for label, cls in rows:
    if cls.__hash__ is None:
        print("   %-20s | 해시 불가" % label)
        continue
    a, b = cls(1), cls(1)
    print("   %-20s | a == b %-5s | 해시가 같은가 %-5s | 키 개수 %d"
          % (label, a == b, hash(a) == hash(b), len({a: 0, b: 0})))

print()
print("③ __repr__ 은 어느 판이든 만들어 준다 :", repr(D1(1)), repr(D3(1)))
print("④ frozen=True 인 것을 고치면")
try:
    x = D3(1)
    x.v = 2
except Exception as ex:
    print("   ", type(ex).__name__, ":", ex)
print("⑤ eq=False 인 D2 는 == 도 정체 기준이다 :", D2(1) == D2(1))
```

```text
===== python3 - <e30_dataclass.py =====
① 클래스 칸의 __hash__ 가 어떻게 갈리나
   D1 기본(eq=True)       | 칸에 있나 True  | 그 값이 None 인가 True  | 해시가 되나 False
   D2 eq=False          | 칸에 있나 False | 그 값이 None 인가 -     | 해시가 되나 True
   D3 frozen=True       | 칸에 있나 True  | 그 값이 None 인가 False | 해시가 되나 True
   D4 unsafe_hash=True  | 칸에 있나 True  | 그 값이 None 인가 False | 해시가 되나 True

② 되는 것들은 값으로 묶이나
   D1 기본(eq=True)       | 해시 불가
   D2 eq=False          | a == b False | 해시가 같은가 False | 키 개수 2
   D3 frozen=True       | a == b True  | 해시가 같은가 True  | 키 개수 1
   D4 unsafe_hash=True  | a == b True  | 해시가 같은가 True  | 키 개수 1

③ __repr__ 은 어느 판이든 만들어 준다 : D1(v=1) D3(v=1)
④ frozen=True 인 것을 고치면
    FrozenInstanceError : cannot assign to field 'v'
⑤ eq=False 인 D2 는 == 도 정체 기준이다 : False
(exit 0)
```

그림 해설 — 네 판을 소스의 표와 맞춰 읽는다.

| 판 | `unsafe_hash` | `eq` | `frozen` | 클래스 칸의 `__hash__` | 해시가 되나 | 값으로 묶이나 |
|---|---|---|---|---|---|---|
| `D1` 기본 | `False` | `True` | `False` | **`None` 이 박힌다** | ✘ | — |
| `D2` `eq=False` | `False` | `False` | `False` | **칸에 없다**(물려받는다) | ✔ | ✘ — 정체 기준 |
| `D3` `frozen=True` | `False` | `True` | `True` | **만들어 준다** | ✔ | ✔ — 키 개수 1 |
| `D4` `unsafe_hash=True` | `True` | `True` | `False` | **만들어 준다** | ✔ | ✔ — 키 개수 1 |

- ★★★ **기본값이 「해시 불가」다.** `@dataclass` 만 붙이면 `eq=True` 가 켜지고,
  그것이 곧 **동작 2 의 상황**이다 — `__eq__` 가 생겼으니 `__hash__` 가 `None` 이 된다.
  **`dataclass` 가 특별히 심술을 부리는 게 아니라 언어 규칙을 그대로 따른 것이다.**
- ★ **`eq=False` 면 칸을 아예 안 건드린다** — 그래서 `object` 의 것을 물려받아 **해시는 되는데 정체 기준**이다.
  `D2(1) == D2(1)` 이 `False` 이고 키 개수가 2 다. **동작 3 의 `Fix2` 와 정확히 같은 모양**이다.
- ★ **`frozen=True` 가 「값 기준 키」의 정답이다.** 고칠 수 없으니 해시가 평생 안 바뀐다 —
  계약의 「평생 안 바뀐다」 조항을 **타입이 보장해 주는 것**이다.
  고치려 하면 `FrozenInstanceError` 에 `cannot assign to field 'v'` 가 나온다.
  ★ 그 예외는 **트레이스백 대신 타입·메시지로 찍었다** — 스택이 `dataclasses.py` 를 지나 절대경로가 박히기 때문이다.
- ★★ **`unsafe_hash=True` 의 이름이 경고다.** 해시는 만들어 주는데 **객체는 여전히 고칠 수 있다** —
  넣은 뒤에 고치면 [12번 동작 8](../12-dict-and-key-requirements/2-summary.md)의 조용한 사고가 그대로 난다.
  ★ 소스의 표에는 **`raise` 칸도 있다** — `unsafe_hash=True` 인데 클래스 몸통에 `__hash__` 를 직접 쓰면 거부한다.
  ★★ **그 칸은 다음 절에서 실제로 던졌다**(동작 9). 표와 실행이 맞았고,
  **던져 봤더니 표만으로는 안 보이던 것이 하나 더 나왔다** — 어떤 이름은 **조용히 넘어간다.**
- **`__repr__` 은 어느 판이든 만들어 준다** — `D1(v=1)`·`D3(v=1)`.

**비용** — `frozen=True` 는 대입을 막으므로 **만들 때 값을 다 정해야 한다.**\
★ **해시·비교의 비용은 안 쟀다.**

### 9. ★★ 데코레이터와 내 메서드가 부딪히면 — 터지는 넷과 조용한 둘

**언제 쓰나** — `@dataclass` 를 붙인 클래스 몸통에 특수 메서드를 직접 쓸 때.
그리고 「데코레이터가 만들어 주는 이름을 내가 또 쓰면 어떻게 되나」가 막힐 때.

★ 동작 8 에서 읽은 소스의 표에는 `raise` 칸이 있었다. **그 칸을 실제로 던지고, 같은 성격의 자리 다섯을 더 던졌다.**

```text
   @dataclass 가 만들려는 이름을 내가 몸통에 이미 써 두면

   __hash__  (unsafe_hash=True)  ->  터진다   TypeError
   __lt__    (order=True)        ->  터진다   TypeError
   __eq__    (eq=True 기본값)     ->  조용하다  내가 쓴 것이 남는다
   __repr__  (repr=True 기본값)   ->  조용하다  내가 쓴 것이 남는다

   ★ 규칙은 "덮어쓰면 터진다" 가 아니라 "이름마다 다르다" 다
```

```python
# e30_dataclass_raise.py
from dataclasses import dataclass

print("① unsafe_hash=True 인데 몸통에 __hash__ 를 직접 쓰면")
try:
    @dataclass(unsafe_hash=True)
    class Clash:
        v: int

        def __hash__(self):
            return 0
except Exception as ex:
    print("   ", type(ex).__name__, ":", ex)

print("② eq=False 인데 order=True 로 하면")
try:
    @dataclass(eq=False, order=True)
    class Bad:
        v: int
except Exception as ex:
    print("   ", type(ex).__name__, ":", ex)

print("③ order=True 인데 __lt__ 를 직접 쓰면")
try:
    @dataclass(order=True)
    class Clash2:
        v: int

        def __lt__(self, o):
            return True
except Exception as ex:
    print("   ", type(ex).__name__, ":", ex)

print("④ frozen 과 안 frozen 을 섞어 상속하면")
try:
    @dataclass(frozen=True)
    class Frozen:
        v: int

    @dataclass
    class Thawed(Frozen):
        w: int = 0
except Exception as ex:
    print("   ", type(ex).__name__, ":", ex)

print("⑤ 그냥 __eq__ 를 직접 쓰면? — eq=True 기본값과 부딪히는데")
try:
    @dataclass
    class Clash3:
        v: int

        def __eq__(self, o):
            return "내가 쓴 __eq__ 가 이겼다"
    print("    예외가 안 난다. 그럼 누가 이겼나 :", Clash3(1) == Clash3(2))
    print("    __hash__ 는 :", Clash3.__hash__)
except Exception as ex:
    print("   ", type(ex).__name__, ":", ex)

print("⑥ __repr__ 을 직접 쓰면?")
try:
    @dataclass
    class Clash4:
        v: int

        def __repr__(self):
            return "내가 쓴 repr"
    print("    예외 없음. repr(Clash4(1)) ->", repr(Clash4(1)))
except Exception as ex:
    print("   ", type(ex).__name__, ":", ex)

print("⑦ 그래서 「덮어쓰면 터진다」가 아니라 이름마다 다르다 — 이 판에서 던진 넷의 결과")
print("    터진 것   : __hash__(unsafe_hash=True) · __lt__(order=True)")
print("    조용한 것 : __eq__ · __repr__ — 내가 쓴 것이 그대로 남는다")
```

```text
===== python3 - <e30_dataclass_raise.py =====
① unsafe_hash=True 인데 몸통에 __hash__ 를 직접 쓰면
    TypeError : Cannot overwrite attribute __hash__ in class Clash
② eq=False 인데 order=True 로 하면
    ValueError : eq must be true if order is true
③ order=True 인데 __lt__ 를 직접 쓰면
    TypeError : Cannot overwrite attribute __lt__ in class Clash2. Consider using functools.total_ordering
④ frozen 과 안 frozen 을 섞어 상속하면
    TypeError : cannot inherit non-frozen dataclass from a frozen one
⑤ 그냥 __eq__ 를 직접 쓰면? — eq=True 기본값과 부딪히는데
    예외가 안 난다. 그럼 누가 이겼나 : 내가 쓴 __eq__ 가 이겼다
    __hash__ 는 : None
⑥ __repr__ 을 직접 쓰면?
    예외 없음. repr(Clash4(1)) -> 내가 쓴 repr
⑦ 그래서 「덮어쓰면 터진다」가 아니라 이름마다 다르다 — 이 판에서 던진 넷의 결과
    터진 것   : __hash__(unsafe_hash=True) · __lt__(order=True)
    조용한 것 : __eq__ · __repr__ — 내가 쓴 것이 그대로 남는다
(exit 0)
```

그림 해설 — 여섯 자리를 던져 **넷이 터지고 둘이 조용했다.**

- **① `unsafe_hash=True` 에 `__hash__` 를 직접 쓰면** `TypeError` 에
  `Cannot overwrite attribute __hash__ in class Clash` 가 나온다.
  ★ 동작 8 에서 소스의 표로만 읽었던 `raise` 칸이 **이 줄이다.** 표와 실행이 맞았다.
- **② `eq=False` 인데 `order=True`** 면 `ValueError` 에 `eq must be true if order is true` 가 나온다.
  **순서는 같음 위에 얹히는 것**이기 때문이다 — 31번으로 넘어가는 자리다.
- ★★ **③ `order=True` 에 `__lt__` 를 직접 쓰면** `TypeError` 인데
  **메시지가 처방까지 준다** — `Consider using functools.total_ordering`.
  ★ 그 도구가 무엇을 채우고 **무엇을 못 채우는지**는 [31번](../31-comparison-protocol-and-sortability/2-summary.md)이 정본이다.
- **④ frozen 에서 non-frozen 을 상속하면** `cannot inherit non-frozen dataclass from a frozen one` 이다.
  **불변이 상속으로 뚫리는 것을 막은 것**이고, 그래서 `frozen=True` 를 키의 안전장치로 믿을 수 있다(동작 8).
- ★★★ **⑤ 가 이 절의 값이다.** `__eq__` 를 직접 쓰면 **예외가 안 난다.**
  `Clash3(1) == Clash3(2)` 가 내가 쓴 문자열을 그대로 돌려준다 — **내 것이 이겼다.**
  ★ 그런데 **`__hash__` 는 `None`** 이다.
  **동작 2 의 본줄기가 `dataclass` 안에서 그대로 재현된 것**이다 —
  `__eq__` 를 몸통에 썼으니 `__hash__` 가 꺼졌고, `dataclass` 는 그것을 **되살려 주지 않는다.**
- **⑥ `__repr__` 도 조용하다** — 내가 쓴 것이 그대로 남는다.
- ★★ **조용한 쪽이 더 위험하다.** 터지는 넷은 **클래스를 만드는 순간** 알려 준다.
  조용한 둘 중 `__eq__` 는 **값 기준 비교를 손으로 써 놓은 `dataclass` 를 해시 불가인 채로 굴러가게** 만든다 —
  `set` 이나 `dict` 에 넣기 전까지 아무 신호가 없다.
- ★ **그래서 처방은 하나다** — `dataclass` 에 `__eq__` 를 직접 쓸 거면
  **`__hash__` 도 같이 쓰거나** 아예 **`eq=False` 로 선언해 의도를 드러내라.**

**비용** — 없다. 판단 규칙이다.\
★ **어느 쪽이 빠른지는 안 쟀다.**

### 10. ★★★ 정적 언어 셋과의 대비 — 무엇이 막아 주고 무엇이 안 막아 주나

**언제 쓰나** — 「타입이 엄격한 언어면 이 사고가 안 나겠지」라는 생각이 들 때. 그리고 언어를 옮겨 다닐 때.

★ 아래 표의 Rust·Java 칸은 **그 갈래 문서를 직접 읽고** 옮긴 것이다(링크는 「관련 자료」에 있다).
C# 칸은 **아직 폴더가 없어** 목록 행이 예고하는 범위까지만 적는다 — **실측이 아니다.**

| 축 | Python | Rust | Java | C# |
|---|---|---|---|---|
| 계약 문장 | 「`a == b` 면 `hash(a) == hash(b)`」 — 데이터 모델 문서 | 「`k1 == k2` 면 `hash(k1) == hash(k2)`」 — std 문서 | `equals` **5조항** + `hashCode` **3조항** — javadoc | `Equals`/`GetHashCode` 일관성 |
| 컴파일러가 내용을 강제하나 | ✘ | ✘ — `impl` 의 **존재**만 본다 | ✘ | ✘ |
| ★ 언어가 **반쪽이라도** 막아 주나 | ✔ — `__eq__` 만 정의하면 `__hash__` 가 **`None` 이 된다**(런타임 스위치) | ✔ — `HashMap` 키가 **타입 수준으로 `Eq + Hash` 를 요구**한다 | ✘ — `hashCode` 는 `Object` 것이 **그냥 남는다** | (폴더 없음 — 목록이 「어긋날 때 생기는 버그」를 예고한다) |
| ★ 그 방어선을 뚫으려면 | **`__hash__` 를 일부러 써야 한다** | **`impl Hash` 를 쓰거나 `#[derive(Hash)]` 를 붙여야 한다** | **아무것도 안 하면 된다** — 그래서 가장 쉽게 난다 | — |
| `Eq` 가 메서드 없는 표식인가 | 해당 없음 — 트레이트가 없다 | ✔ — `impl Eq for T {}` 의 몸통이 비어 있다 | 해당 없음 | 해당 없음 |
| 어겼을 때 증상 | **조용한 오답** | **조용한 오답**(std 가 「논리 오류」라 부른다 — UB 아님) | **조용한 오답** | — |
| `len`/순회에 보이나 | ✔ 보인다 | ✔ 보인다 | ✔ 보인다 | — |
| 같은 키가 둘이 되나 | ✔ — 키 개수 2 | ✔ — `len` 2 | ✔ — `HashSet size 2` | — |
| 배열·리스트는 멀쩡한가 | ✔ — `list` 의 `in` 은 `True` | ✔ — `Vec` 는 해시를 안 쓴다 | ✔ — `List.contains : true` | — |
| ★★ 넣을 때 쓴 **그 객체**로 꺼내지나 | ✔ — **정체 지름길**로 꺼내진다(CPython 구현) | 그 실험은 **딴 객체**로 물어 `None` 이었다 | (그 실험을 안 했다) | — |
| 해시값을 문서에 적을 수 있나 | ✘ — `str` 해시에 소금이 섞인다 | ✘ — `DefaultHasher` 도 안정 보장이 아니다 | ✘ — javadoc 이 「실행 간 일관 불필요」라 적는다 | — |
| 부동소수점을 키로 쓸 수 있나 | ✔ — 막지 않는다(`nan` 도 들어간다) | ✘ — `f64` 는 `Eq` 를 안 받아 **애초에 키가 못 된다** | ✔ — `Double` 은 키가 된다 | — |

```text
   막아 주는 자리가 언어마다 다르다

   Rust    타입 검사 때        ->  Eq + Hash 가 없으면 컴파일이 안 된다
   Python  hash() 를 부를 때   ->  __hash__ 가 None 이면 TypeError
   Java    아무 데서도         ->  Object 의 hashCode 가 조용히 쓰인다

   ★ 그런데 셋 다 "내용이 맞는지" 는 안 본다.
     막아 주는 것은 "짝을 안 맞췄을 때" 뿐이다.
```

- ★★★ **결론 하나** — **셋 다 계약 내용은 사람 몫이다.** 언어가 다른 것은 **「짝을 안 맞춘 것」을 언제 잡느냐**뿐이다.
- ★★ **Rust 가 가장 이르다** — 키 타입에 `Eq + Hash` 경계가 붙어 **컴파일 때** 걸린다.
  게다가 `f64` 에는 `Eq` 를 **안 주는 쪽**을 골라 반사성 사고를 **언어가 미리 막았다.**
- ★★ **파이썬은 중간이다** — `__eq__` 만 고친 타입은 **`TypeError` 로 시끄럽게** 막힌다(동작 2).
  **그래서 파이썬에서 조용히 틀리려면 `__hash__` 를 일부러 써야 한다** — 동작 4 가 정확히 그 코드다.
- ★★ **Java 가 가장 늦다** — `equals` 만 고쳐도 `Object.hashCode` 가 그냥 남아 **아무 신호가 없다.**
  Java 갈래의 실측이 그 모양을 그대로 보였다(`get` 이 `null`, `HashSet size 2`, 그런데 `List.contains` 는 `true`).
- ★ **파이썬만 가진 칸이 하나 있다** — **정체 지름길**이다.
  반사성을 깬 키도 **「넣을 때 쓴 그 객체로는」 꺼내진다**(동작 5 ①).
  Rust 쪽 실험은 딴 객체로 물어 전부 실패했고, **파이썬도 딴 객체로 물으면 실패한다**(동작 5 ③).
  ★★ 이 칸은 **CPython 구현**이다. 언어 보장으로 읽지 마라.

**비용** — 없다. 판단 규칙이다.\
★ **어느 언어가 빠른가는 이 문서의 관심이 아니고 재지도 않았다.**

## 문법 — 형태와 규칙

**형태 — 값 기준 클래스를 손으로 쓸 때의 표준 꼴**

```text
   class Point:
       __slots__ = ("x", "y")              # 선택 — 29번

       def __init__(self, x, y):
           self.x, self.y = x, y

       def __repr__(self):                 # ① 진단 도구부터 만든다
           return f"Point({self.x!r}, {self.y!r})"

       def __eq__(self, other):            # ② 같음
           if not isinstance(other, Point):
               return NotImplemented       # ★ False 가 아니다 — 31번
           return (self.x, self.y) == (other.x, other.y)

       def __hash__(self):                 # ③ 해시 — ②와 같은 칸을 본다
           return hash((self.x, self.y))   # ★ 문서가 권하는 "튜플로 묶어 해시" 꼴
```

- ★ **`__eq__` 가 보는 칸과 `__hash__` 가 섞는 칸을 나란히 적어라.** 두 줄이 붙어 있으면 한쪽만 고치기 어렵다.
- ★ **`NotImplemented` 를 돌려주는 것**이 `False` 보다 낫다 — 상대 타입에 기회를 준다.
  정본은 [31번](../31-comparison-protocol-and-sortability/2-summary.md)이다.
- ★ **`__hash__` 에는 「안 바뀌는 칸」만 넣는다.** 가변 필드를 넣으면 [12번 동작 8](../12-dict-and-key-requirements/2-summary.md)의 사고가 난다.

**만들어 주는 것에 맡기는 꼴 — 이쪽이 기본 선택이다**

```text
   from dataclasses import dataclass

   @dataclass(frozen=True)                 # ★ 키로 쓸 것이면 frozen
   class Point:
       x: int
       y: int

   ->  __init__ · __repr__ · __eq__ · __hash__ 를 전부 만들어 준다
```

**금지 사례 — 이렇게 쓰면 조용히 틀린다**

```text
   ① __eq__ 만 쓴다                         -> TypeError (시끄럽다. 그나마 낫다)

   ② __eq__ 는 값 기준인데 __hash__ 는 정체 기준
        __hash__ = object.__hash__          -> 키가 둘이 된다 (조용하다)

   ③ __eq__ 가 보는 칸과 __hash__ 가 섞는 칸이 다르다
        eq 는 s.lower() 를 보는데
        hash 는 s 를 섞는다                  -> 조회가 실패한다 (조용하다)

   ④ 해시에 가변 필드를 넣는다               -> 넣은 뒤 고치면 못 꺼낸다 (조용하다)

   ⑤ 해시값을 파일·DB 에 저장한다            -> 다음 실행에서 안 맞는다 (조용하다)
```

- ★ **①만 예외가 나고 나머지는 전부 조용하다.** 이 비율이 이 주제의 성격이다.

## 어디서 틀리나

### (1) 「`__eq__` 를 재정의하면 `__hash__` 도 물려받는다」로 안다

**꺼진다.** 클래스 칸에 `None` 이 박혀 `object.__hash__` 로 내려가는 길이 막힌다(동작 2).

### (2) `__hash__ = object.__hash__` 로 고치고 끝낸다

**해시 가능해질 뿐 계약은 안 지켜진다.** 값이 같은 두 객체가 **딴 키**가 된다(동작 3).\
값 기준 `__eq__` 를 쓰고 있다면 이 처방은 **틀린 처방**이다.

### (3) `__eq__` 가 보는 것과 `__hash__` 가 섞는 것이 다르다

**이 주제 최다 사고다.** 「대소문자 무시」·「공백 무시」·「일부 필드만 비교」가 전부 이 모양이 된다(동작 4).\
★ **`__eq__` 를 고칠 때마다 `__hash__` 를 같은 화면에서 읽어라.**

### (4) 「계약을 어기면 어디선가 터지겠지」로 안다

**안 터진다.** `len` 도 순회도 `print` 도 멀쩡하고 **조회만 틀린다.**

### (5) 해시값을 찍어서 근거로 쓴다

**실행마다 달라진다.** `str`·`bytes` 해시에 소금이 섞인다(동작 6).\
근거로 쓸 것은 「**같은가 다른가**」다.

### (6) 「해시가 같으면 같은 값이다」로 안다

**아니다.** 충돌은 합법이고, 그래서 `==` 로 다시 확인하는 것이다(동작 6 ④).

### (7) 키로 쓴 뒤에 그 객체를 고친다

**조용하다.** 이 사고의 정본은 [12번 동작 8](../12-dict-and-key-requirements/2-summary.md)이다 —
`len` 은 그대로인데 어떤 키로도 못 꺼낸다.\
★ 여기서의 처방은 **`frozen=True` 인 `dataclass`** 를 쓰는 것이다(동작 8).

### (8) `@dataclass` 를 붙였으니 `set` 에 들어갈 거라고 믿는다

**기본값은 해시 불가다.** `eq=True` 가 켜지고 그것이 곧 `__hash__ = None` 이다(동작 8).\
키로 쓸 것이면 **`frozen=True`**.

### (9) `dataclass` 에 `__eq__` 를 손으로 써 놓고 키로 쓴다

**조용하다.** 데코레이터는 그 자리를 **안 덮고 그냥 넘어가고**, 그러면서 `__hash__` 는 `None` 인 채로 남는다(동작 9 ⑤).\
★ `__lt__` 를 쓰면 `order=True` 에서 **터져 주는데** `__eq__` 는 안 터진다 — **이름마다 다르다.**\
★ 처방은 `__hash__` 를 같이 쓰거나 `eq=False` 로 의도를 드러내는 것이다.

### (10) `__str__` 만 정의하고 로그를 믿는다

**리스트·`dict` 에 담기는 순간 기본 꼴로 돌아간다.** 컨테이너는 원소의 `repr` 을 쓴다(동작 7).\
하나만 쓸 거면 **`__repr__`**.

### (11) `list` 로 검사했으니 `dict` 도 될 거라고 믿는다

**리스트는 해시를 안 쓴다.** 계약이 깨져도 `list` 의 `in` 은 멀쩡하다(동작 4).\
★ 이 비대칭 때문에 「내 `__eq__` 는 맞는데?」에서 진단이 막힌다.

### (12) 정체 지름길을 언어 사실로 안다

**CPython 구현이다.** 「같은 객체면 `__eq__` 를 안 부른다」를 설계의 전제로 삼지 마라(동작 5).

### (13) 「반사성은 당연하다」고 믿고 `float` 를 키로 쓴다

**`float('nan')` 은 자기 자신과도 다르다.** 파이썬은 그것을 **안 막는다** —
Rust 는 `f64` 에 `Eq` 를 안 줘서 **키가 되는 것 자체를 막았다**(동작 10).

## 구현 세부사항 대 언어 보장

### 언어 보장

- **`a == b` 이면 `hash(a) == hash(b)`** — 데이터 모델 문서가 「유일하게 요구되는 성질」이라 적는다.
  ★ **강제는 안 된다.** 「보장」은 「자료구조가 이것을 전제로 짜였다」는 뜻이다.
- **`__eq__` 를 재정의하고 `__hash__` 를 정의하지 않으면 `__hash__` 가 `None` 이 된다.**
  ★ 이것이 **언어가 실제로 강제하는 유일한 자리**다.
- **`__hash__ = <ParentClass>.__hash__` 로 되살릴 수 있다** — 문서가 그 방법을 명시한다.
- **`__hash__ = None` 을 직접 써서 해시를 끌 수 있다** — 문서가 그 용법도 명시한다.
- **`__repr__` 은 `__str__` 을 대신하고, 거꾸로는 `object.__str__` 이 `__repr__` 을 부르는 것**이다.
- **사용자 정의 클래스는 기본으로 `__eq__`·`__hash__` 를 `object` 에서 물려받고, 기본 `==` 는 정체 기준**이다.
- **`str`·`bytes` 해시는 소금이 섞이고 프로세스 간에 예측 불가**다.
- **`dict` 의 삽입 순서**(3.7+) — 이 문서가 키 목록을 찍을 때 기댄 유일한 순서 보장이다.

### CPython 구현 세부사항

- ★★ **`dict`·`set`·`list` 의 정체 지름길** — 두 포인터가 같으면 `==` 를 안 부른다.
  동작 5 ①⑤⑥ 가 전부 이것이다. **언어 레퍼런스는 이것을 약속하지 않는다.**
- **정수 해시가 값으로 고정된 것** — `hash(1) == 1` · `hash(-1) == -2` · `hash(2**61 - 1) == 0`.
  법이 `2**61 - 1` 이라는 것도 구현이다.
- **계약을 어겼을 때 정확히 무엇이 나오나** — 키 개수가 2 가 되는 것, 어느 조회가 실패하는지,
  `d.get(a)` 가 여전히 옛 값인 것. **「동작이 규정되지 않는다」가 정확한 표현**이고 위 관찰은 이 구현의 결과다.
- **`dataclasses` 의 `_hash_action` 표** — 표준 라이브러리 구현이다(문서에도 요약이 있지만 8행 표는 소스에 있다).
- ★★ **어느 이름이 부딪히면 터지고 어느 이름이 조용히 넘어가는가** — `dataclasses` 모듈이 이름마다 다르게 처리하는 것이고
  **언어 문법이 보장하는 것이 아니다**(동작 9). 단 **`__eq__` 를 쓰면 `__hash__` 가 `None` 이 되는 것**은
  모듈이 아니라 **언어 규칙**이라 층이 다르다 — 한 출력 안에 두 층이 섞여 있는 자리다.
- **`member_descriptor`·`FrozenInstanceError` 같은 내부 이름**.

### 이 판(3.12.3)의 관찰

- **예외 문구 전부** — `unhashable type: 'OnlyEq'` · `cannot assign to field 'v'` ·
  `Cannot overwrite attribute __hash__ in class Clash` · `eq must be true if order is true` ·
  `Consider using functools.total_ordering` · `cannot inherit non-frozen dataclass from a frozen one`.
- **트레이스백이 세 줄이고 소스 줄·캐럿이 없는 것** — 실행 중 예외 + `python3 - <파일` 조합의 결과다.
- **`sys.flags.hash_randomization` 이 `True`** — 이 머신의 기본값이다(`PYTHONHASHSEED=0` 이면 꺼진다).
- **`(exit 1)`** — 예외로 끝난 두 블록.

### 그래서 이렇게 적으면 틀린다

| 이렇게 적으면 | 왜 틀리나 | 바르게 |
|---|---|---|
| 「`__eq__` 를 쓰면 해시가 안 만들어진다」 | 안 만들어지는 게 아니라 **있던 것이 `None` 으로 꺼진다** | 클래스 칸에 `None` 이 박힌다 |
| 「`__hash__ = object.__hash__` 로 고치면 된다」 | 해시 가능해질 뿐 **계약은 안 지켜진다** | 값 기준이면 `__hash__` 를 직접 써라 |
| 「계약을 어기면 예외가 난다」 | **조용하다.** 예외가 나는 것은 `__eq__` 만 쓴 경우뿐 | 조회만 틀린다 |
| 「`dict` 는 같은 객체면 `==` 를 안 부른다」 | **CPython 구현**이다 | 이 판의 관찰로 적는다 |
| 「`hash('key')` 는 …이다」 | **실행마다 다르다** | 「같은가 다른가」로 적는다 |
| 「`hash(1)` 이 `1` 인 것은 언어 규칙이다」 | **CPython 구현**이다 | 구현으로 분류해 적는다 |
| 「`@dataclass` 면 `set` 에 들어간다」 | **기본값은 해시 불가**다 | `frozen=True` 가 필요하다 |
| 「`dataclass` 가 만드는 이름을 내가 쓰면 터진다」 | **이름마다 다르다** — `__eq__`·`__repr__` 은 조용하다 | 터지는 것과 조용한 것을 갈라 적는다 |
| 「`__str__` 만 써도 로그에 잘 나온다」 | 컨테이너 안에서는 `repr` 이다 | 하나만 쓸 거면 `__repr__` |
| 「Rust 는 계약을 컴파일러가 강제한다」 | **`impl` 의 존재만** 본다 | 내용은 Rust 도 사람 몫이다 |
| 「Java 도 `equals` 만 고치면 예외가 난다」 | **아무 신호가 없다** | `hashCode` 는 `Object` 것이 남는다 |

## 언제 쓰고 언제 안 쓰나

**세 메서드를 손으로 쓸 때**

- 값이 같으면 같은 것으로 치고 싶을 때 — `__eq__` + `__hash__` 를 **짝으로**.
- `dict` 키·`set` 원소로 쓸 때 — **해시에 넣을 칸은 안 바뀌는 것만.**
- 로그·디버깅이 중요할 때 — `__repr__` 을 **먼저**.

**만들어 주는 것에 맡길 때 — 이쪽이 기본이다**

- 필드 몇 개짜리 값 객체 — `@dataclass(frozen=True)`.
- 키로 안 쓸 것 — `@dataclass` 기본값으로 충분하다(해시 불가여도 상관없다).
- 튜플로 충분하면 튜플 — `namedtuple`·`NamedTuple` 은 `[목록의 **38번 주제**](../38-namedtuple-and-typeddict/)` 가 정본이다.

**안 쓰는 게 나을 때**

- **정체가 곧 같음인 객체** — 연결·세션·위젯처럼 「그 하나뿐인 것」은 `object` 의 기본이 정답이다.
  `__eq__` 를 쓰는 순간 해시까지 따라와야 하고, 실수할 여지만 는다.
- **가변 객체를 키로 쓰고 싶을 때** — 키로 쓰지 말고 **불변 스냅샷**(튜플·`frozen` dataclass)을 키로 써라.
- **해시를 캐시해 두고 싶을 때** — 프로세스를 넘기면 안 맞는다. 저장할 것은 **값 자체**다.

## 핵심 문장

- **계약은 한 방향이다** — 「`==` 면 해시도 같다」. 거꾸로는 요구하지 않는다(충돌은 합법이다).
- **언어가 강제하는 것은 한 자리뿐이다** — `__eq__` 를 재정의하면 `__hash__` 가 `None` 이 된다. **내용은 사람 몫이다.**
- ★★★ **어기면 예외가 아니라 조용한 오답이다** — `len` 과 순회에는 보이는데 **조회만 실패한다.**
- **`list` 는 멀쩡하고 `dict`·`set` 만 틀린다.** 리스트는 해시를 안 쓰기 때문이고, 이 비대칭이 진단을 막는다.
- **`__hash__ = object.__hash__` 는 「해시 가능하게」이지 「계약 지키게」가 아니다** — 키가 둘이 된다.
- **파이썬에서 조용히 틀리려면 `__hash__` 를 일부러 써야 한다** — 그 점에서 Java 보다 방어선이 하나 앞에 있다.
- **정체 지름길은 CPython 구현이다** — 넣을 때 쓴 그 객체로는 꺼내지지만, 그것에 기대면 안 된다.
- **해시값은 문서에도 파일에도 적지 않는다** — 소금이 섞인다. 적을 것은 「같은가 다른가」다.
- **`__repr__` 은 `__str__` 을 대신하지만 거꾸로는 아니다** — 하나만 쓸 거면 `__repr__`.
- **`@dataclass` 의 기본값은 해시 불가다** — 키로 쓸 것이면 `frozen=True`.
- ★ **`dataclass` 와 내 메서드가 부딪힐 때 「덮어쓰면 터진다」는 틀렸다** — 이름마다 다르고,
  **조용히 넘어가는 `__eq__` 쪽이 더 위험하다**(해시가 꺼진 채로 굴러간다).

## 관련 자료

- 목록: [python/syntax 주제 목록](../README.md) — 이 주제는 **30번**
- 선행: [12-dict-and-key-requirements](../12-dict-and-key-requirements/2-summary.md) — ★★★ **키 요건의 정본.**\
  **경계**: 그쪽은 「무엇이 키가 되나」와 `1`·`1.0`·`True` 가 한 칸인 것, **키는 처음 것이 남고 값은 나중 것이 이기는 것**,
  **넣은 뒤 키를 고치면 못 꺼내는 것**까지. 여기는 **내 클래스에서 세 메서드를 어떻게 쓰나**와 **어겼을 때의 언어 간 대비**부터다.
- 선행: [02-is-vs-eq-interning](../02-is-vs-eq-interning/2-summary.md) — **`is` 와 `==` 의 정본.**\
  동작 5 의 정체 지름길을 읽으려면 그쪽이 먼저다.
- 선행: [29-classes-and-attribute-lookup](../29-classes-and-attribute-lookup/2-summary.md) — **속성 탐색의 정본.**\
  `__hash__` 가 「클래스 칸에 `None` 으로 박힌다」는 말이 왜 상속을 막는지는 그쪽에서 본다.
- 이어지는 곳: [31-comparison-protocol-and-sortability](../31-comparison-protocol-and-sortability/2-summary.md) — **순서의 계약.**\
  `NotImplemented` 를 돌려주는 규칙과 `functools.total_ordering` 이 `__hash__` 를 **못 채우는 것**이 거기다.
- 이어지는 곳: [13-set-and-frozenset](../13-set-and-frozenset/2-summary.md) — 같은 해시 기계의 「순서 없는」 쪽.
- 이어지는 곳: `[목록의 **36번 주제**](../36-dataclasses/)` 「`dataclasses`」 — `field`·`default_factory`·`order` 까지 포함한 정본.
  여기서는 **`__hash__` 가 어떻게 갈리는지**만 봤다.
- 이어지는 곳: `[목록의 **38번 주제**](../38-namedtuple-and-typeddict/)` 「`namedtuple`·`NamedTuple`·`TypedDict`」 — 튜플이 이미 세 메서드를 갖춘 자리.
- ★ 대비: [`rust/syntax/28-partialeq-eq-partialord-ord-and-hash-contracts`](../../../rust/syntax/28-partialeq-eq-partialord-ord-and-hash-contracts/2-summary.md) — **이 주제의 직접 대비 대상.**\
  `CaseKey` 실험의 원본이 거기 있고, 반사성을 깬 키가 **영영 안 꺼내지는 것**도 거기서 봤다.\
  **경계**: 그쪽은 `PartialEq`/`Eq`/`PartialOrd`/`Ord`/`Hash` 다섯 트레이트의 관계까지, 여기는 **파이썬 세 메서드**만.
- ★ 대비: [`java/syntax/27-equals-hashcode-contract`](../../../java/syntax/27-equals-hashcode-contract/2-summary.md) — `equals` 5조항 + `hashCode` 3조항의 javadoc 원문과
  **`List` 는 멀쩡하고 `Map`/`Set` 만 틀리는 비대칭**의 실측.
- ★ 대비: C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **19번** 「동등성 규칙 — `Equals`/`GetHashCode`/`==`」 —
  **아직 폴더가 없다.** 동작 10 의 C# 칸은 그 행이 예고하는 범위까지만 적었고 **실측이 아니다.**
- 원리: [`cs/data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/) — **해시 테이블의 원리가 정본이다.**\
  **경계**: 버킷·충돌·리사이즈·로드 팩터는 그쪽, 여기는 「**계약을 어기면 어디가 틀리나**」부터.
- 공식 문서: [`object.__hash__`](https://docs.python.org/3.12/reference/datamodel.html#object.__hash__) ·
  [`object.__eq__`](https://docs.python.org/3.12/reference/datamodel.html#object.__eq__) ·
  [`object.__repr__`](https://docs.python.org/3.12/reference/datamodel.html#object.__repr__) ·
  [`object.__str__`](https://docs.python.org/3.12/reference/datamodel.html#object.__str__) ·
  [hashable](https://docs.python.org/3.12/glossary.html#term-hashable) ·
  [`dataclasses`](https://docs.python.org/3.12/library/dataclasses.html)

## 용어 풀이

- **해시 가능(hashable)** — 평생 안 바뀌는 해시값이 있고 다른 것과 비교할 수 있는 객체.
  `dict` 키와 `set` 원소가 되려면 필요하다.
- **계약(contract)** — 문법으로 강제되지 않지만 **자료구조가 지켜진다고 믿고 도는** 약속.
  어기면 컴파일 에러가 아니라 **틀린 답**이 나온다.
- **동치 관계(equivalence relation)** — 반사·대칭·추이를 만족하는 「같음」.
  이것이 성립해야 「같음」이 객체를 **겹치지 않는 묶음**으로 쪼갤 수 있다.
- **반사성(reflexivity)** — `a == a` 가 참인 성질. `float('nan')` 이 이것을 깨는 대표적인 값이다.
- **버킷(bucket)** — 해시값으로 고른 칸. **칸을 먼저 고르므로 칸이 틀리면 그 안의 `==` 는 안 돈다.**
- **충돌(collision)** — 다른 값이 같은 해시를 갖는 것. **합법이고** 표가 `==` 로 걸러 낸다.
- **해시 소금(hash salt)** — `str`·`bytes` 해시에 프로세스마다 섞이는 무작위값.
  `PYTHONHASHSEED` 로 고정할 수 있다.
- **정체 지름길** — 두 이름이 같은 객체를 가리키면 `==` 없이 「같다」로 처리하는 CPython 의 최적화.
- **조용한 오답(silent wrong answer)** — 예외도 경고도 없이 답만 틀린 상태.
  이 주제의 사고는 하나(`__eq__` 만 정의)를 빼면 전부 이것이다.
- **불변(immutable)** — 만든 뒤 값이 안 바뀌는 것. 키로 쓸 객체의 안전장치다(`frozen=True`).
- **표식 트레이트(marker trait)** — Rust 의 `Eq` 처럼 **메서드가 없고 「이 성질을 지킨다」고 선언만** 하는 트레이트.
  파이썬에는 대응물이 없다.
- **런타임 스위치** — 파이썬이 `__eq__` 재정의를 보고 `__hash__` 를 `None` 으로 꺼 버리는 것.
  **컴파일 때가 아니라 클래스를 만들 때** 일어난다.

## 더 들어가면

- **`__ne__` 는 거의 안 쓴다** — 파이썬 3 는 `__eq__` 의 결과를 뒤집어 `!=` 를 만들어 준다.
  ★ **블록은 [31번](../31-comparison-protocol-and-sortability/2-summary.md)에 있다** —
  거기서 `total_ordering` 이 `__ne__` 를 **안 채우는 것**과 한 화면에서 본다.
- **`__hash__` 가 돌려준 값은 잘린다** — CPython 은 `Py_hash_t`(플랫폼 워드 크기)로 맞춘다.
  그래서 큰 정수를 돌려줘도 그대로 쓰이지 않는다.
  ★ 폭과 법은 `sys.hash_info` 의 `width`·`modulus` 로 물을 수 있다 — **해시값 자체와 달리 흔들리지 않는 칸**이다.
- **`functools.total_ordering` 은 `__hash__` 를 안 채운다** — 비교를 채워 줘도 **해시는 여전히 `None`** 이다.
  실측은 [31번](../31-comparison-protocol-and-sortability/2-summary.md)에 있다. **이 두 주제가 맞물리는 자리다.**
- **`__eq__` 를 상속하면 `__hash__` 도 따라 꺼진다** — 부모가 `__eq__` 를 재정의했으면 자식도 영향을 받는다.
  ★ 동작 4 의 `Fixed` 가 그 자리를 우연히 보여 준다 — `CaseKey` 를 물려받아 `__hash__` 만 바꿨는데,
  `__eq__` 는 부모 것을 그대로 쓰면서도 해시가 되살아났다(자식 칸의 `__hash__` 가 더 가깝기 때문이다).
- **`Protocol`·ABC 로 「해시 가능함」을 타입으로 요구할 수 있나** — `typing.Hashable` 이 있다.
  ★ 정적 검사기가 잡아 주는 범위는 **안 확인했다**. 정본은 `[목록의 **35번 주제**](../35-abc-and-protocol/)`다.
- **`set` 의 순회 순서는 `PYTHONHASHSEED` 에 흔들린다** — 그래서 이 문서는 `set` 을 **`len()` 으로만** 찍었다.
  실측은 [13번](../13-set-and-frozenset/2-summary.md)에 있다.
