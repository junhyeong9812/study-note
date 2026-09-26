# python/syntax/31-comparison-protocol-and-sortability — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만.
> - [3.3.1. Basic customization — rich comparison methods](https://docs.python.org/3.12/reference/datamodel.html#object.__lt__) — **반사 짝**과 **하위 클래스 우선권**의 정본
> - [`NotImplemented`](https://docs.python.org/3.12/library/constants.html#NotImplemented) — 돌려주면 언어가 무엇을 하나 · 진릿값 평가는 **3.9 부터 폐기 예정**
> - [`functools.total_ordering`](https://docs.python.org/3.12/library/functools.html#functools.total_ordering) — 무엇을 요구하고 무엇을 채우나
> - [Sorting Techniques HOWTO](https://docs.python.org/3.12/howto/sorting.html) — *"The sort routines use `<` when comparing two objects."*
> - [`list.sort` · `sorted`](https://docs.python.org/3.12/library/stdtypes.html#list.sort) — **안정 정렬 보장**
>
> **실행 검증** — 이 문서에 실린 출력은 전부 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.\
> ★ 던지는 형태를 하나로 고정했다 — `python3 - <파일` 로 던져 트레이스백이 `File "<stdin>", line N` 이 된다.
> ★★ **캐럿은 예외 종류에 달렸다** — 실행 중 예외는 소스 줄도 `^` 캐럿도 안 나오고, `SyntaxError` 라야 둘 다 나온다.
> 이 주제는 예외를 전부 `except` 로 받아 **한 줄로 찍었으므로** 트레이스백이 한 블록도 없다.\
> ★★ **`DeprecationWarning` 을 `warnings.catch_warnings` 로 잡아 찍었다.** 그냥 두면 그 한 줄이 **표준 오류로 새서**
> 파이프에서 맨 앞으로 몰리고 **블록의 줄 순서가 뒤집힌다**(실측에서 그렇게 한 번 뒤집혔다).
> 잡아서 **표준 출력에 목록으로 찍으면** 순서가 고정된다.\
> **버전** — 이 주제의 규칙은 대부분 Python 3.0 이후 그대로다. 갈리는 것 둘 —
> `functools.total_ordering` 이 **2.7 · 3.2 부터**이고, **`NotImplemented` 의 진릿값 평가가 3.9 부터 폐기 예정**이다
> (지금은 `DeprecationWarning` 과 함께 참이고, 문서가 *"It will raise a `TypeError` in a future version of Python"* 이라고 적는다).\
> **구현 대 언어 보장 한 줄** — **어느 특수 메서드가 불리는 규칙**(반사 짝·하위 클래스 우선·`NotImplemented` 처리)과
> **안정 정렬**·**`key` 가 원소당 한 번**은 **언어 보장**이고,
> **`__lt__` 가 몇 번 불렸는가**와 **`max` 가 `__gt__` 를 쓰는 것**은 **CPython 구현**이다.
> ★★ **「계약 위반을 검사하지 않는다」도 보장이 아니라 관찰이다**((9)) — 문서는 검사한다고도 안 한다고도 적지 않았다.\
> ★ **흔들리는 칸 / 안 흔들리는 칸** — 재대조에서 「고칠 것」과 「설계상 안 맞는 것」을 기계적으로 가르려고 미리 선언한다.
>
> | 흔들린다 | 안 흔들린다(근거로 써도 되는 칸) |
> |---|---|
> | `id()` 와 `0x…` 주소 — **그래서 이 배치는 한 번도 안 찍었다** | 예외 **종류** · `File "<stdin>", line N` · `(exit N)` |
> | **해시값 자체**(`hash('key')` — 실행마다 다르다) | 해시가 **「같은가 다른가」** |
> | 판이 오르면 예외 **문구**와 내부 타입 이름 | **호출 로그의 순서** · 어느 특수 메서드가 **불렸나 안 불렸나** |
> | 판이 오르면 `__lt__` 호출 **횟수**(TimSort 의 성질) | `len()`·키 개수·`sorted()` 한 결과 |
> | — | `set`·`dict` 를 **정렬해서 찍은** 것 |
> | — | ★ (9)의 흔들리는 비교자도 **`random.seed(0)` 으로 고정**해 안 흔들리는 쪽에 둔다 |
>
> ★★★ **이 주제에서 가장 조심할 칸이 「횟수」다.** 「세 원소에 `__lt__` 가 네 번」은 **이 판의 관찰**이고,
> 「`sorted` 가 `<` 만 묻는다」는 **보장**이다. 둘을 같은 문장에 섞어 적으면 나중에 판이 오를 때 통째로 틀린다.\
> **선행** — [10번](../10-list-methods-and-sort-key/2-summary.md)(**정렬 키의 정본** — `sort`/`sorted`·`key=`·`reverse=`·안정성의 쓰는 법) ·
> [30번](../30-repr-eq-hash-contracts/2-summary.md)(**`__eq__` 를 정의하면 `__hash__` 가 꺼지는 것** — 여기서 그대로 물린다) ·
> [02번](../02-is-vs-eq-interning/2-summary.md)(`True == 1` 이 되는 이유) ·
> [04번](../04-numeric-types-and-division/2-summary.md)(`float` 의 성질).\
> **이 사슬** — [29](../29-classes-and-attribute-lookup/2-summary.md) → [30](../30-repr-eq-hash-contracts/2-summary.md) → 31 → [32](../32-container-protocol/2-summary.md).
> 29 가 **속성이 어디서 풀리나**, 30 이 **같음의 계약**, 31 이 **순서의 계약**, 32 가 **컨테이너의 계약**이다.
> ★ **30 과 31 은 한 몸이다** — `__eq__` 를 정의한 클래스에 `total_ordering` 을 붙이면 **정렬은 되는데 dict 키는 못 되는** 물건이 나온다((5)).

## 한눈에 — 쉽게 말하면

**비교 프로토콜은 「자 하나만 주면 줄을 세워 준다」는 거래다.**

키 순으로 학생을 세울 때, 선생이 묻는 것은 딱 한 가지다 — 「**너희 둘 중 누가 더 작니**」.\
「누가 더 크니」도 「누가 같니」도 안 묻는다. 그 한 질문만 답할 수 있으면 줄은 선다.

```text
   sorted(data) 가 객체에게 묻는 것

   +-----------+        "a < b 니?"        +-----------+
   |  정렬 루틴 |  --------------------->  |  내 객체   |
   |  (TimSort) |  <---------------------  | __lt__     |
   +-----------+        True / False       +-----------+

   ★ 묻는 것은 "<" 하나뿐이다.
     ">" 도 "==" 도 안 묻는다 — 그래서 __lt__ 하나로 sorted 가 된다.
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 선생이 묻는 한 가지 질문 | `__lt__` | 호출 로그에 `__lt__` 만 찍힌다 |
| 「나는 그 애랑은 못 재겠는데요」 | `NotImplemented` 를 돌려주는 것 | 언어가 상대에게 다시 묻는다 |
| 상대에게 거꾸로 물어보기 | **반사 연산** — `a < b` 가 `b.__gt__(a)` 로 | 로그의 `self=2 other=1` |
| 둘 다 모른다고 하면 | `TypeError` | `'<' not supported between instances of …` |
| 키를 재지 말고 **이름표**를 붙여 세우기 | `key=` | 원소의 `__lt__` 가 **한 번도 안 불린다** |
| 자 하나로 나머지 눈금을 파 주는 기계 | `functools.total_ordering` | `__dict__` 에 셋이 새로 생긴다 |
| ★ **그 기계가 못 파는 눈금** | `__hash__` · `__ne__` · `__eq__` | `After.__hash__` 가 `None` 이다 |
| 자가 고장 났는데 아무도 안 알려 주는 것 | `nan` 이 섞인 정렬 | 예외 없이 **안 정렬된 결과** |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.\
「**정렬은 되는데 `set` 에 못 넣는 객체**」와 「**`None` 이 섞인 컬럼을 정렬하다 나는 `TypeError`**」가 그것이다.\
둘 다 **평소에는 멀쩡하다가** 데이터가 한 줄 달라지는 날 드러난다.

> **비교 프로토콜(rich comparison protocol)** — `<`·`<=`·`>`·`>=`·`==`·`!=` 여섯 연산자가
> 각각 `__lt__`·`__le__`·`__gt__`·`__ge__`·`__eq__`·`__ne__` 여섯 특수 메서드로 내려가는 규칙.\
> 예: `a < b` 는 먼저 `a.__lt__(b)` 를 부른다.

> **반사 연산(reflected operation)** — 왼쪽이 답을 못 하면 **오른쪽에게 짝이 되는 질문을 거꾸로** 하는 것.\
> 예: `a < b` 가 안 되면 `b.__gt__(a)` 를 부른다. **인자가 뒤집힌다.**

> **전순서(total order)** — 어느 두 값이든 `<`·`==`·`>` 중 **정확히 하나**가 성립하는 순서.\
> 예: 정수는 전순서다. `float` 은 `nan` 때문에 **전순서가 아니다** — `nan` 은 셋 다 거짓이다.

먼저 판을 못 박는다. 이 문서의 모든 출력은 아래 한 줄에서 나왔다.

```python
# e31_version.py
import sys

print("version_info =", sys.version_info)
print("implementation =", sys.implementation.name)
print("platform =", sys.platform)
```

```text
===== python3 - <e31_version.py =====
version_info = sys.version_info(major=3, minor=12, micro=3, releaselevel='final', serial=0)
implementation = cpython
platform = linux
(exit 0)
```

## 이 주제가 답하려는 질문

1. ★★★ **왜 `__lt__` 하나로 `sorted` 가 되나** — 그리고 `__gt__` 를 정의해 두면 그것도 쓰이나((1)·(2)).
   이 주제의 본체가 여기다. 「된다」가 아니라 「**호출 로그에 무엇이 찍히나**」로 안다.
2. ★★ **왼쪽이 답을 못 하면 무슨 일이 일어나나** — 반사 연산과 `NotImplemented`((3)·(4)).
3. ★★ **계약을 어기면 무엇이 망가지나** — 파이썬은 **예외를 안 던지고 틀린 순서를 준다**((8)·(9)).
   **원소 10만 개까지 조용했다**((9)). 정적 언어와의 대비가 여기서 가장 날카롭다.

★ **[10번](../10-list-methods-and-sort-key/2-summary.md)이 「정렬을 어떻게 쓰나」였다면 여기는 「정렬이 내 객체에게 무엇을 묻나」다.**
`key=`·`reverse=`·안정성의 **쓰는 법**은 그쪽이 정본이고, 이 문서는 그것을 **호출 로그로 다시 볼 때만** 인용한다.

## 동작 방식

### (0) 이 주제가 쓰는 네 창

정렬은 **틀려도 예외가 안 나는** 주제라 창을 미리 세워 둔다.

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| **정의된 특수 메서드 목록** — `Cls.__dict__` | 무엇을 내가 썼고 무엇을 언어·데코레이터가 채웠나((1)·(5)) | ★ `total_ordering` 을 가르는 유일한 창 |
| ★★ **호출 로그** — 메서드 안에서 `print` | **무엇이 불렸나**((1)·(2)·(3)·(7)) | ★ 이 주제의 본체 |
| **결과값** | 줄이 어떻게 섰나 | 기본 |
| ★★★ **「예외가 났나 안 났나」** | **셋이 전부 정상인데 순서만 틀린 자리**((8)) | ★ 이 주제의 네 번째 창 |

★★★ **네 번째 창이 왜 필요한가** — 앞의 세 창은 `nan` 앞에서 전부 통과한다.\
`__lt__` 는 정의돼 있고, 호출 로그도 정상이고, 결과값도 리스트로 나온다.\
**틀린 것은 「그 리스트가 정렬돼 있지 않다」는 것뿐**이고 그것은 **예외로 알려지지 않는다**((8)).

★★ **「부적용인 창」도 하나 있다** — **비교 횟수**다.\
숫자는 찍히지만 **TimSort 의 성질**이라 판이 오르면 달라진다. 그래서 **근거로 안 쓰고 「순서」만 쓴다.**\
★★★ **네 번째 창을 원소 수 축으로 한 번 더 돌렸다**((9)) — **10 · 100 · 2000 · 10000 · 100000 전부 예외가 없었다.**
Java 쪽은 [Java 28번](../../../java/syntax/28-comparable-comparator/2-summary.md)이 같은 축을 6만 회로 재 두었고
**`n=2000` 부터 던졌다.** 두 실측이 같은 축 위에 나란히 놓인다.

### 1. ★★ `__lt__` 하나로 줄이 선다

**언제 쓰나** — 내 클래스를 `sorted` 에 넣고 싶을 때. 그리고 「여섯 개를 다 써야 하나」가 막힐 때.

문서가 자로 무엇을 쓰는지 직접 적는다 — *"The sort routines use `<` when comparing two objects.
So, it is easy to add a standard sort order to a class by defining an `__lt__()` method."*

```text
   내가 쓴 것            언어가 쓰는 것

   __lt__  ----------->  sorted / list.sort / heapq / min
      |
      +-- 반사로 -----> ">" 도 된다  (b.__lt__(a) 를 거꾸로)
      |
      +-- 안 생기는 것 -> "<=" 는 TypeError
                          ">=" 는 TypeError

   ★ "<" 와 ">" 는 짝이라 하나만 써도 둘 다 되고
     "<=" 와 ">=" 는 다른 짝이라 하나도 안 생긴다.
```

```python
# e31_lt_only.py
class V:
    def __init__(self, n):
        self.n = n

    def __repr__(self):
        return "V(%d)" % self.n

    def __lt__(self, other):
        print("      __lt__  %d < %d" % (self.n, other.n))
        return self.n < other.n


data = [V(3), V(1), V(2)]
print("① 정의된 비교 메서드 :", [m for m in ("__lt__", "__le__", "__gt__", "__ge__", "__eq__") if m in V.__dict__])
print("② sorted 를 부른다 — 아래가 호출 로그다")
out = sorted(data)
print("   결과 :", out)
print("③ 세 원소를 정렬하는 데 __lt__ 가 몇 번 불렸나 : 위 줄을 세어라")
print("④ 다른 비교는 어떻게 되나")
for expr, fn in (("V(1) <= V(2)", lambda: V(1) <= V(2)),
                 ("V(1) > V(2)", lambda: V(1) > V(2)),
                 ("V(1) == V(2)", lambda: V(1) == V(2))):
    try:
        print("   %-13s ->" % expr, fn())
    except TypeError as ex:
        print("   %-13s -> TypeError:" % expr, ex)
```

```text
===== python3 - <e31_lt_only.py =====
① 정의된 비교 메서드 : ['__lt__']
② sorted 를 부른다 — 아래가 호출 로그다
      __lt__  1 < 3
      __lt__  2 < 1
      __lt__  2 < 3
      __lt__  2 < 1
   결과 : [V(1), V(2), V(3)]
③ 세 원소를 정렬하는 데 __lt__ 가 몇 번 불렸나 : 위 줄을 세어라
④ 다른 비교는 어떻게 되나
   V(1) <= V(2)  -> TypeError: '<=' not supported between instances of 'V' and 'V'
      __lt__  2 < 1
   V(1) > V(2)   -> False
   V(1) == V(2)  -> False
(exit 0)
```

그림 해설.

- ① **정의된 비교 메서드는 `__lt__` 하나뿐**이다. 창 하나로 먼저 못 박는다.
- ② **`sorted` 가 그 하나만 물었다.** 로그에 `__lt__` 말고는 아무것도 없다.
- ★ ③ 세 원소에 **네 줄**이 찍혔다. **이 숫자는 근거로 쓰지 않는다** — TimSort 가 같은 결과를 더 적은 비교로 낼 수도 있다.
  **근거로 쓰는 것은 「`__lt__` 만 찍혔다」는 사실**이다.
- ★★ ④ 가 이 절의 과녁이다. 셋이 각각 다르게 끝난다.
  - `` V(1) <= V(2) `` — **`TypeError`**. `__le__` 는 `__lt__` 에서 자동으로 안 생긴다.
  - `` V(1) > V(2) `` — **된다.** 그런데 로그를 보면 `__lt__  2 < 1` 이다. **반사 연산**으로 `` V(2).__lt__(V(1)) `` 이 불린 것이다((3)).
  - `` V(1) == V(2) `` — **`False`**. `__eq__` 를 안 썼으니 `object` 의 **정체 기준**이고, 두 객체는 딴것이라 거짓이다.
- ★ 그래서 「`__lt__` 하나면 충분하다」는 **정렬 루틴에 대해서만** 참이다((2)가 그 범위를 잰다).
  여섯 연산자를 다 쓰고 싶으면 (5)로 간다.

**비용** — 메서드 하나로 정렬이 된다. 대신 **`<=`·`>=` 가 조용히 빠진 채** 남고, 그것을 쓰는 코드가 나중에 `TypeError` 로 터진다.

### 2. ★ 정렬 루틴은 `<` 만 쓴다 — 그런데 `max`·`min` 은 다르다

**언제 쓰나** — 「`__gt__` 도 써 뒀으니 내림차순은 그쪽이 쓰이겠지」를 점검할 때.

```python
# e31_gt_ignored.py
class Both:
    def __init__(self, n):
        self.n = n

    def __repr__(self):
        return "Both(%d)" % self.n

    def __lt__(self, o):
        print("      __lt__  %d %d" % (self.n, o.n))
        return self.n < o.n

    def __gt__(self, o):
        print("      __gt__  %d %d" % (self.n, o.n))
        return self.n > o.n


def fresh():
    return [Both(3), Both(1), Both(2)]


print("① sorted")
print("   결과 :", sorted(fresh()))
print("② sorted(reverse=True) — 「큰 것부터」인데 무엇이 불리나")
print("   결과 :", sorted(fresh(), reverse=True))
print("③ list.sort 도 같나")
xs = fresh()
xs.sort()
print("   결과 :", xs)
print("④ max / min 은 다르다")
print("   max :", max(fresh()))
print("   min :", min(fresh()))
print("⑤ heapq 는?")
import heapq
h = fresh()
heapq.heapify(h)
print("   heappop :", heapq.heappop(h))
```

```text
===== python3 - <e31_gt_ignored.py =====
① sorted
      __lt__  1 3
      __lt__  2 1
      __lt__  2 3
      __lt__  2 1
   결과 : [Both(1), Both(2), Both(3)]
② sorted(reverse=True) — 「큰 것부터」인데 무엇이 불리나
      __lt__  1 2
      __lt__  3 1
      __lt__  3 2
   결과 : [Both(3), Both(2), Both(1)]
③ list.sort 도 같나
      __lt__  1 3
      __lt__  2 1
      __lt__  2 3
      __lt__  2 1
   결과 : [Both(1), Both(2), Both(3)]
④ max / min 은 다르다
      __gt__  1 3
      __gt__  2 3
   max : Both(3)
      __lt__  1 3
      __lt__  2 1
   min : Both(1)
⑤ heapq 는?
      __lt__  1 2
      __lt__  3 1
      __lt__  2 3
   heappop : Both(1)
(exit 0)
```

그림 해설 — 로그에 **무엇이 찍혔나**로 읽는다.

- ① **`sorted`** — `__gt__` 를 정의해 뒀는데도 `__lt__` 만 찍혔다.
- ★★ ② **`reverse=True`** — 여기서도 `__lt__` 만 찍혔다. **내림차순이라고 `__gt__` 로 갈아타지 않는다.**
  ★ 그런데 **로그가 ①과 다르다.** ①은 `1 3` · `2 1` · `2 3` · `2 1` 네 줄이고 ②는 `1 2` · `3 1` · `3 2` 세 줄이다.
  **같은 자를 들고 다른 질문을 한 것**이고, 그래서 `reverse=True` 는 **「정렬한 뒤 뒤집기」가 아니다**((6)에서 결과로 확인한다).
- ③ **`list.sort`** — ①과 한 글자도 같다. 둘은 같은 루틴이다.
- ★★ ④ **`max` 와 `min` 은 다르다.** `max` 가 **`__gt__`** 를, `min` 이 **`__lt__`** 를 불렀다.
  「파이썬은 늘 `__lt__` 만 쓴다」로 외우면 **여기서 틀린다.**
  ★ 그래서 `__lt__` 만 정의한 (1)의 `V` 는 `sorted` 는 되고 **`max` 는 반사 연산에 기대게 된다.**
- ⑤ **`heapq`** 도 `__lt__` 만 쓴다. 로그가 그것을 그대로 보인다.

★★ **이 절의 결론은 두 겹이다.**\
**「정렬 루틴은 `<` 만 쓴다」는 문서가 적은 보장**이고,\
**「`max` 가 `__gt__` 를 쓴다」는 이 판에서 로그로 본 CPython 의 선택**이다. 문서는 `max` 가 어느 연산자를 쓰는지 안 적는다.

**비용** — `__lt__` 하나로 정렬·힙·`min` 이 공짜로 붙는다. `max` 는 **반사 연산을 한 번 더 거친다.**

### 3. ★ 반사 연산 — 왼쪽이 못 하면 오른쪽에게 거꾸로 묻는다

**언제 쓰나** — 「내 클래스에 `__lt__` 가 없는데 왜 `<` 가 되지」가 막힐 때.

문서가 규칙을 통째로 적는다 —
*"there are no swapped-argument versions of these methods … rather, `__lt__()` and `__gt__()` are each other's reflection,
`__le__()` and `__ge__()` are each other's reflection, and `__eq__()` and `__ne__()` are their own reflection.
… If the operands are of different types, and right operand's type is a direct or indirect subclass of the left operand's type,
the reflected method of the right operand has priority, otherwise the left operand's method has priority."*

```text
   a < b 를 만났을 때 언어가 하는 일

   b 의 타입이 a 의 타입의 하위 클래스인가?
        |
        +-- 예 --> b.__gt__(a)  먼저   --(NotImplemented)--> a.__lt__(b)
        |
        +-- 아니오 --> a.__lt__(b) 먼저 --(없거나 NotImplemented)--> b.__gt__(a)
                                                |
                                     둘 다 안 되면 TypeError
   ★ 짝은 이렇게 고정돼 있다
       "<"  <-> ">"        "<=" <-> ">="        "==" <-> "=="       "!=" <-> "!="
```

```python
# e31_reflected.py
class NoLt:
    def __init__(self, n):
        self.n = n

    def __repr__(self):
        return "NoLt(%d)" % self.n

    def __gt__(self, o):
        print("      NoLt.__gt__ 가 불렸다 : self=%d other=%d" % (self.n, o.n))
        return self.n > o.n


class OnlyLt:
    def __init__(self, n):
        self.n = n

    def __repr__(self):
        return "OnlyLt(%d)" % self.n

    def __lt__(self, o):
        print("      OnlyLt.__lt__ 가 불렸다 : self=%d other=%d" % (self.n, o.n))
        return self.n < o.n


print("① NoLt(1) < NoLt(2) — 왼쪽에 __lt__ 가 없다")
print("   결과 :", NoLt(1) < NoLt(2))
print("② OnlyLt(1) > OnlyLt(2) — 왼쪽에 __gt__ 가 없다")
print("   결과 :", OnlyLt(1) > OnlyLt(2))
print("③ 둘 다 없으면")


class Bare:
    def __init__(self, n):
        self.n = n


try:
    Bare(1) < Bare(2)
except TypeError as ex:
    print("   TypeError:", ex)

print("④ 오른쪽이 왼쪽의 하위 클래스면 오른쪽이 먼저 불린다")


class P:
    def __lt__(self, o):
        print("      P.__lt__")
        return True


class Q(P):
    def __gt__(self, o):
        print("      Q.__gt__  (하위 클래스가 먼저다)")
        return True


print("   P() < Q() ->", P() < Q())
print("   P() < P() ->", P() < P())
print("⑤ 반사 짝은 정해져 있다 : < ↔ > · <= ↔ >= · == ↔ == · != ↔ !=")
print("   NoLt(1) <= NoLt(2) 는?")
try:
    print("   ->", NoLt(1) <= NoLt(2))
except TypeError as ex:
    print("   TypeError:", ex)
```

```text
===== python3 - <e31_reflected.py =====
① NoLt(1) < NoLt(2) — 왼쪽에 __lt__ 가 없다
      NoLt.__gt__ 가 불렸다 : self=2 other=1
   결과 : True
② OnlyLt(1) > OnlyLt(2) — 왼쪽에 __gt__ 가 없다
      OnlyLt.__lt__ 가 불렸다 : self=2 other=1
   결과 : False
③ 둘 다 없으면
   TypeError: '<' not supported between instances of 'Bare' and 'Bare'
④ 오른쪽이 왼쪽의 하위 클래스면 오른쪽이 먼저 불린다
      Q.__gt__  (하위 클래스가 먼저다)
   P() < Q() -> True
      P.__lt__
   P() < P() -> True
⑤ 반사 짝은 정해져 있다 : < ↔ > · <= ↔ >= · == ↔ == · != ↔ !=
   NoLt(1) <= NoLt(2) 는?
   TypeError: '<=' not supported between instances of 'NoLt' and 'NoLt'
(exit 0)
```

그림 해설.

- ★ ① **`NoLt` 에는 `__gt__` 만 있는데 `<` 가 된다.** 로그의 `self=2 other=1` 이 결정적이다 —
  **인자가 뒤집혀** `` NoLt(2).__gt__(NoLt(1)) `` 이 불린 것이다. 「2가 1보다 큰가」가 「1이 2보다 작은가」의 답이 된다.
- ② 거꾸로도 같다. `` OnlyLt(1) > OnlyLt(2) `` 가 `` OnlyLt(2).__lt__(OnlyLt(1)) `` 로 갔고, `2 < 1` 이 거짓이라 `False` 다.
- ③ **둘 다 없으면 `TypeError`** 다. 문구가 `'<' not supported between instances of 'Bare' and 'Bare'` 로, **연산자와 두 타입 이름**을 다 적는다.
- ★ ④ **하위 클래스가 먼저다.** `` P() < Q() `` 에서 `Q.__gt__` 가 먼저 불렸다 — `Q` 가 `P` 의 하위 클래스이기 때문이다.
  같은 타입끼리인 `` P() < P() `` 는 평범하게 `P.__lt__` 다.
  **이 규칙이 있어야 하위 클래스가 상위 클래스의 비교를 덮을 수 있다.**
- ★★ ⑤ **반사 짝은 정해져 있어서 건너뛰지 않는다.** `NoLt` 에 `__gt__` 가 있어도 `<=` 는 **`__ge__` 를 찾지 `__gt__` 로 가지 않는다.**
  그래서 `` NoLt(1) <= NoLt(2) `` 는 `TypeError` 다. (1)의 `V` 가 `<=` 에서 막힌 것과 **같은 이유**다.

**비용** — 한쪽만 써도 두 방향이 된다. 대신 **호출 로그를 안 보면 누가 불렸는지 모르고**,
`self` 와 `other` 가 바뀐 채 들어오므로 **메서드 안에서 로그를 찍을 때 방향을 오해하기 쉽다.**

### 4. ★ `NotImplemented` — 「나는 못 재겠다」를 돌려주는 자리

**언제 쓰나** — 내 클래스가 **모르는 타입**과 비교당할 때 무엇을 돌려줄지 정할 때.

```text
   __lt__ 가 돌려줄 수 있는 세 가지

   True / False      -> 그 값이 그대로 답이 된다
   NotImplemented    -> "나는 모른다". 언어가 상대에게 다시 묻는다
                         상대도 모르면 TypeError 로 바꾼다
   그 밖의 아무 값    -> 그대로 답이 된다 (진릿값으로 읽힌다)  <- 사고가 여기서 난다
```

```python
# e31_notimplemented.py
import warnings


class Strict:
    def __init__(self, n):
        self.n = n

    def __repr__(self):
        return "Strict(%d)" % self.n

    def __lt__(self, o):
        print("      Strict.__lt__ 가 불렸다. 상대의 타입 :", type(o).__name__)
        if not isinstance(o, Strict):
            return NotImplemented
        return self.n < o.n


print("① 같은 타입끼리")
print("   Strict(1) < Strict(2) ->", Strict(1) < Strict(2))
print("② 다른 타입과 — 돌려준 NotImplemented 가 무엇이 되나")
try:
    Strict(1) < 2
except TypeError as ex:
    print("   TypeError:", ex)
print("③ 메서드를 직접 부르면 그 값이 그대로 나온다")
r = Strict.__lt__(Strict(1), 2)
print("   돌려받은 것 :", r, "| 타입 :", type(r).__name__)
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    b = bool(r)
print("   bool(NotImplemented) ->", b)
print("   그때 난 경고 :", [(x.category.__name__, str(x.message)) for x in w])
print("④ 정렬 안에서 나면")
try:
    sorted([Strict(1), 2])
except TypeError as ex:
    print("   TypeError:", ex)
print("⑤ NotImplemented 를 「안 된다」는 뜻의 False 로 쓰면 조용히 틀린다")
with warnings.catch_warnings(record=True) as w2:
    warnings.simplefilter("always")
    verdict = "참" if Strict.__lt__(Strict(1), 2) else "거짓"
print("   if 로 쓰면 이렇게 읽힌다 :", verdict)
print("   그때 난 경고 :", [(x.category.__name__, str(x.message)) for x in w2])
```

```text
===== python3 - <e31_notimplemented.py =====
① 같은 타입끼리
      Strict.__lt__ 가 불렸다. 상대의 타입 : Strict
   Strict(1) < Strict(2) -> True
② 다른 타입과 — 돌려준 NotImplemented 가 무엇이 되나
      Strict.__lt__ 가 불렸다. 상대의 타입 : int
   TypeError: '<' not supported between instances of 'Strict' and 'int'
③ 메서드를 직접 부르면 그 값이 그대로 나온다
      Strict.__lt__ 가 불렸다. 상대의 타입 : int
   돌려받은 것 : NotImplemented | 타입 : NotImplementedType
   bool(NotImplemented) -> True
   그때 난 경고 : [('DeprecationWarning', 'NotImplemented should not be used in a boolean context')]
④ 정렬 안에서 나면
   TypeError: '<' not supported between instances of 'int' and 'Strict'
⑤ NotImplemented 를 「안 된다」는 뜻의 False 로 쓰면 조용히 틀린다
      Strict.__lt__ 가 불렸다. 상대의 타입 : int
   if 로 쓰면 이렇게 읽힌다 : 참
   그때 난 경고 : [('DeprecationWarning', 'NotImplemented should not be used in a boolean context')]
(exit 0)
```

그림 해설.

- ① 같은 타입끼리는 평범하다.
- ★★ ② **`NotImplemented` 를 돌려주면 그 자리에서 `TypeError` 가 된다.** 로그를 보면 `__lt__` 는 **불리긴 했다** —
  값을 보고 언어가 **상대(`int`)에게 다시 물었고**, `int` 도 `Strict` 를 모르니 **예외로 바꾼** 것이다.
  ★ **예외 문구가 내 메서드 이야기를 한 마디도 안 한다** — `'<' not supported between instances of 'Strict' and 'int'` 뿐이다.
- ★ ③ **메서드를 직접 부르면 `NotImplemented` 가 그대로 나온다.** 타입 이름은 `NotImplementedType` 이다.
  그리고 **`bool(NotImplemented)` 은 `True`** 이고 `DeprecationWarning` 이 따라온다.
  문서가 *"It will raise a `TypeError` in a future version of Python"* 이라고 적었으니 **언젠가 예외가 된다.**
- ★ ④ **정렬 안에서 나면 두 타입 이름이 뒤바뀌어 나온다** — `'int' and 'Strict'`.
  TimSort 가 `` 2 < Strict(1) `` 쪽을 물었기 때문이다. **왼쪽이 누구인지는 정렬 루틴이 정한다.**
- ★★★ ⑤ 가 이 절에서 가장 나쁜 자리다. `NotImplemented` 를 **「안 된다」는 뜻의 거짓으로 읽으면 조용히 틀린다** —
  `if` 에 넣으면 **참**이다. 경고는 나지만 **기본 설정에서 안 보인다**(여기서는 일부러 잡아 찍었다).

**비용** — `NotImplemented` 를 제대로 돌려주면 **상대 타입이 나중에 협조할 여지**가 남는다.\
`False` 를 돌려주면 그 길이 막히고, **`a < b` 와 `b > a` 가 다른 답을 내는** 비대칭이 생긴다.

### 5. ★★ `functools.total_ordering` — 무엇을 채우고 무엇을 안 채우나

**언제 쓰나** — 여섯 연산자를 다 쓰고 싶은데 메서드를 여섯 개 쓰기는 싫을 때.

문서가 요구 사항을 적는다 — *"The class must define one of `__lt__()`, `__le__()`, `__gt__()`, or `__ge__()`.
In addition, the class should supply an `__eq__()` method."*

```text
   total_ordering 이 채우는 칸과 안 채우는 칸

   내가 준다   __lt__   __eq__
                 |        |
                 v        v
   채운다      __le__   __gt__   __ge__        <- 클래스 칸에 새로 생긴다
   안 채운다   __ne__                          <- object 가 __eq__ 에서 만들어 준다
   안 채운다   __hash__                        <- ★ __eq__ 때문에 None 인 채로 남는다
   안 채운다   __eq__                          <- 내가 준 것 그대로
```

```python
# e31_total_ordering.py
import functools


class Before:
    def __init__(self, n):
        self.n = n

    def __repr__(self):
        return "Before(%d)" % self.n

    def __eq__(self, o):
        return isinstance(o, Before) and self.n == o.n

    def __lt__(self, o):
        return self.n < o.n


@functools.total_ordering
class After:
    def __init__(self, n):
        self.n = n

    def __repr__(self):
        return "After(%d)" % self.n

    def __eq__(self, o):
        return isinstance(o, After) and self.n == o.n

    def __lt__(self, o):
        return self.n < o.n


names = ("__lt__", "__le__", "__gt__", "__ge__", "__eq__", "__ne__", "__hash__")
print("① 클래스 칸에 무엇이 들어 있나")
print("   %-10s | %-12s | %s" % ("이름", "데코레이터 전", "후"))
for nm in names:
    print("   %-10s | %-12s | %s" % (nm, nm in Before.__dict__, nm in After.__dict__))

print()
print("② 채워진 것들의 정체 — 어느 함수가 들어갔나")
print("   ", [(nm, After.__dict__[nm].__name__) for nm in ("__le__", "__gt__", "__ge__")])

print()
print("③ 못 채우는 것 — __hash__")
print("   Before.__hash__ :", Before.__hash__)
print("   After.__hash__  :", After.__hash__)
try:
    {After(1): 0}
except TypeError as ex:
    print("   {After(1): 0} -> TypeError:", ex)

print()
print("④ 채운 것은 실제로 도나")
print("   After(1) <= After(1) :", After(1) <= After(1))
print("   After(2) >= After(1) :", After(2) >= After(1))
print("   Before(1) <= Before(1) 는?")
try:
    print("   ->", Before(1) <= Before(1))
except TypeError as ex:
    print("   TypeError:", ex)

print()
print("⑤ 무엇도 안 주면 데코레이터가 거부한다")
try:
    @functools.total_ordering
    class Nothing:
        pass
except ValueError as ex:
    print("   ", type(ex).__name__, ":", ex)

print()
print("⑥ __eq__ 가 없으면? — object 의 것(정체 기준)으로 그냥 돈다")


@functools.total_ordering
class NoEq:
    def __init__(self, n):
        self.n = n

    def __lt__(self, o):
        return self.n < o.n


print("   NoEq.__eq__ is object.__eq__ :", NoEq.__eq__ is object.__eq__)
print("   NoEq(1) <= NoEq(1) :", NoEq(1) <= NoEq(1))
print("   NoEq(1) == NoEq(1) :", NoEq(1) == NoEq(1))
```

```text
===== python3 - <e31_total_ordering.py =====
① 클래스 칸에 무엇이 들어 있나
   이름         | 데코레이터 전      | 후
   __lt__     | True         | True
   __le__     | False        | True
   __gt__     | False        | True
   __ge__     | False        | True
   __eq__     | True         | True
   __ne__     | False        | False
   __hash__   | True         | True

② 채워진 것들의 정체 — 어느 함수가 들어갔나
    [('__le__', '__le__'), ('__gt__', '__gt__'), ('__ge__', '__ge__')]

③ 못 채우는 것 — __hash__
   Before.__hash__ : None
   After.__hash__  : None
   {After(1): 0} -> TypeError: unhashable type: 'After'

④ 채운 것은 실제로 도나
   After(1) <= After(1) : True
   After(2) >= After(1) : True
   Before(1) <= Before(1) 는?
   TypeError: '<=' not supported between instances of 'Before' and 'Before'

⑤ 무엇도 안 주면 데코레이터가 거부한다
    ValueError : must define at least one ordering operation: < > <= >=

⑥ __eq__ 가 없으면? — object 의 것(정체 기준)으로 그냥 돈다
   NoEq.__eq__ is object.__eq__ : True
   NoEq(1) <= NoEq(1) : False
   NoEq(1) == NoEq(1) : False
(exit 0)
```

그림 해설 — **`__dict__` 창**으로만 갈린다. 겉으로는 안 보인다.

- ① **채워진 것은 셋이다** — `__le__`·`__gt__`·`__ge__` 가 `False` 에서 `True` 로 바뀌었다.
  `__lt__`·`__eq__` 는 내가 준 것이고, **`__ne__` 는 전도 후도 `False`** 다.
- ★ **`__ne__` 를 왜 안 채우나** — 채울 필요가 없다. `object.__ne__` 가 **`__eq__` 의 결과를 뒤집어** 주기 때문이다.
  그래서 「채워야 할 여섯 중 셋만 채운다」가 아니라 「**비어 있던 셋을 채운다**」가 맞다.
- ★ ② 채워진 것들의 이름이 각각 `__le__`·`__gt__`·`__ge__` 다. **데코레이터가 만든 함수에 그 이름이 붙어 있다.**
- ★★★ ③ 이 이 절의 과녁이다. **`__hash__` 는 안 채운다.** `Before` 도 `After` 도 `None` 이고,
  `After` 를 dict 키로 쓰면 `TypeError: unhashable type: 'After'` 다.
  **`__eq__` 를 정의한 순간 `__hash__` 가 꺼지는 것**은 [30번](../30-repr-eq-hash-contracts/2-summary.md)이 정본이고,
  `total_ordering` 은 **그 자리를 건드리지 않는다.**
  ★ 그래서 「**정렬은 되는데 `set`·`dict` 에는 못 넣는 객체**」가 이 데코레이터의 흔한 산출물이다.
- ④ 채운 것은 실제로 돈다. **안 붙인 `Before` 는 `<=` 에서 `TypeError`** 다 — (1)의 `V` 와 같은 자리다.
- ⑤ **순서 연산을 하나도 안 주면 데코레이터가 거부한다** — `ValueError: must define at least one ordering operation: < > <= >=`.
  ★ **이것은 클래스를 만드는 순간 난다.** 계약 위반 중 **유일하게 일찍 잡히는 것**이다.
- ★★ ⑥ **`__eq__` 는 없어도 통과한다** — 문서의 낱말이 `must` 가 아니라 `should` 였다.
  그러면 `object.__eq__` 즉 **정체 기준**으로 돌고, `` NoEq(1) <= NoEq(1) `` 이 **`False`** 가 된다.
  ★ **왜 거짓인가** — 데코레이터가 만든 `__le__` 는 `a < b or a == b` 꼴이다.
  두 `NoEq(1)` 은 **딴 객체**라 `==` 가 거짓이고 `<` 도 거짓이라 둘 다 거짓이다.
  **같은 객체 하나로 `x <= x` 를 물으면 참**이다 — 정체가 같으니 `==` 가 참이기 때문이다.
  결과가 「반사성이 깨진 순서」이고, **아무도 안 알려 준다.**

**비용** — 메서드 둘로 여섯 연산자를 얻는다.\
★ 문서가 스스로 주의를 적어 두었다 — *"it does come at the cost of slower execution and more complex stack traces
for the derived comparison methods."*\
★★ **그 비용은 이 배치가 안 쟀다.** 문서의 말을 옮긴 것이지 내 측정이 아니다.

### 6. ★ 안정성은 「보장」이다 — 여기서는 `__lt__` 가 무엇을 보았나로 본다

**언제 쓰나** — 동점이 있는 데이터를 정렬할 때. 그리고 내림차순을 만드는 방법을 고를 때.

★★ **이 절의 정본은 [10번](../10-list-methods-and-sort-key/2-summary.md)이다.**
「안정 정렬이 언어 보장이라는 것」과 「나눠 정렬」과 「`reverse=True` 대 `[::-1]`」은 **전부 그쪽에서 읽는다.**\
여기서는 **그 보장이 객체 쪽에서 어떻게 보이나**만 덧붙인다 — 즉 **`__lt__` 가 무엇을 물었나**이다.

```python
# e31_stable.py
rows = [("b", 1), ("a", 2), ("c", 1), ("a", 1), ("b", 2)]
print("원래 순서 :", rows)
by_num = sorted(rows, key=lambda r: r[1])
print("두 번째 칸으로만 정렬 :", by_num)

print()
print("① 같은 키끼리 원래 순서가 유지되나")
for k in (1, 2):
    print("   키 %d : 원래 %s -> 정렬 후 %s"
          % (k, [r[0] for r in rows if r[1] == k], [r[0] for r in by_num if r[1] == k]))

print()
print("② 안정성을 쓰면 다중 기준 정렬이 두 번의 정렬이 된다 (뒤 기준부터)")
tmp = sorted(rows, key=lambda r: r[0])
print("   ① 이름으로     :", tmp)
print("   ② 그 다음 수로 :", sorted(tmp, key=lambda r: r[1]))
print("   한 번에 튜플로  :", sorted(rows, key=lambda r: (r[1], r[0])))

print()
print("③ reverse=True 도 안정적이다 — 같은 키끼리 뒤집히지 않는다")
rev = sorted(rows, key=lambda r: r[1], reverse=True)
print("   결과 :", rev)
for k in (2, 1):
    print("   키 %d : 원래 %s -> 정렬 후 %s"
          % (k, [r[0] for r in rows if r[1] == k], [r[0] for r in rev if r[1] == k]))
print("   reversed(sorted(...)) 와 같은가 :", rev == list(reversed(by_num)))
```

```text
===== python3 - <e31_stable.py =====
원래 순서 : [('b', 1), ('a', 2), ('c', 1), ('a', 1), ('b', 2)]
두 번째 칸으로만 정렬 : [('b', 1), ('c', 1), ('a', 1), ('a', 2), ('b', 2)]

① 같은 키끼리 원래 순서가 유지되나
   키 1 : 원래 ['b', 'c', 'a'] -> 정렬 후 ['b', 'c', 'a']
   키 2 : 원래 ['a', 'b'] -> 정렬 후 ['a', 'b']

② 안정성을 쓰면 다중 기준 정렬이 두 번의 정렬이 된다 (뒤 기준부터)
   ① 이름으로     : [('a', 2), ('a', 1), ('b', 1), ('b', 2), ('c', 1)]
   ② 그 다음 수로 : [('a', 1), ('b', 1), ('c', 1), ('a', 2), ('b', 2)]
   한 번에 튜플로  : [('a', 1), ('b', 1), ('c', 1), ('a', 2), ('b', 2)]

③ reverse=True 도 안정적이다 — 같은 키끼리 뒤집히지 않는다
   결과 : [('a', 2), ('b', 2), ('b', 1), ('c', 1), ('a', 1)]
   키 2 : 원래 ['a', 'b'] -> 정렬 후 ['a', 'b']
   키 1 : 원래 ['b', 'c', 'a'] -> 정렬 후 ['b', 'c', 'a']
   reversed(sorted(...)) 와 같은가 : False
(exit 0)
```

그림 해설.

- ① **같은 키끼리 원래 순서가 그대로다.** 키 1 의 무리가 원래도 `['b', 'c', 'a']` 이고 정렬 후에도 같다.
  ★ 이것은 **문서가 약속한 보장**이지 TimSort 의 부수 효과가 아니다.
- ② 그 보장 덕에 **나눠 정렬**이 된다. 세부는 [10번](../10-list-methods-and-sort-key/2-summary.md)이 정본이다.
- ★★★ ③ 이 이 절의 과녁이다. **`reverse=True` 도 안정적이다.**
  키 2 의 무리가 `['a', 'b']` 로 **원래 순서 그대로**이고, 키 1 도 `['b', 'c', 'a']` 다.
  **동점 무리가 뒤집히지 않는다.**
- ★★ 그래서 마지막 줄이 **`False`** 다 — `` sorted(..., reverse=True) `` 와 `` list(reversed(sorted(...))) `` 가 **다르다.**
  뒤엣것은 동점 무리까지 뒤집어 `['a', 'c', 'b']` 로 만들기 때문이다.
- ★ (2)의 로그가 이것을 미리 설명해 두었다 — `reverse=True` 는 **비교 자체를 다르게 하지** 결과를 뒤집지 않는다.
  **두 절이 같은 사실의 앞뒷면**이다.

**비용** — 「원래 순서」를 보조 키로 따로 만들 필요가 없다.\
대신 **내림차순을 `[::-1]` 로 만들면 동점 무리 안에서 조용히 달라진다.**

### 7. ★ `key=` 를 주면 원소의 `__lt__` 는 안 불린다

**언제 쓰나** — 「`key` 를 줬는데 왜 내 `__lt__` 에 로그가 안 찍히지」가 막힐 때.

```text
   sorted(data, key=f) 가 줄을 세우는 자리

   data:   Loud(3)   Loud(1)   Loud(2)
              | f        | f       | f          <- 원소당 정확히 한 번
              v          v         v
   이름표:     3          1         2
              \__________/_________/
                     int 의 __lt__ 로 비교한다   <- ★ Loud.__lt__ 는 안 불린다
                          |
                          v
   결과:   Loud(1)   Loud(2)   Loud(3)          <- 돌려주는 것은 "원소" 다
```

```python
# e31_key_vs_lt.py
class Loud:
    def __init__(self, n):
        self.n = n

    def __repr__(self):
        return "Loud(%d)" % self.n

    def __lt__(self, o):
        print("      Loud.__lt__ 가 불렸다")
        return self.n < o.n


def fresh():
    return [Loud(3), Loud(1), Loud(2)]


print("① key 없이")
print("   결과 :", sorted(fresh()))
print("② key= 로 정수를 뽑아 쓰면")
print("   결과 :", sorted(fresh(), key=lambda x: x.n))
print("③ key 가 돌려준 것의 __lt__ 가 쓰인다 — key 를 -n 으로")
print("   결과 :", sorted(fresh(), key=lambda x: -x.n))
print("④ key 는 원소마다 정확히 한 번 불린다")
calls = []


def k(x):
    calls.append(x.n)
    return x.n


sorted(fresh(), key=k)
print("   key 가 불린 횟수 :", len(calls), "| 불린 순서 :", calls)
print("⑤ key 를 쓰면 원소의 __lt__ 는 아예 안 쓰이므로, 비교 불가 타입도 정렬된다")


class NoCompare:
    def __init__(self, n):
        self.n = n

    def __repr__(self):
        return "NoCompare(%d)" % self.n


try:
    sorted([NoCompare(2), NoCompare(1)])
except TypeError as ex:
    print("   key 없이 -> TypeError:", ex)
print("   key 로   ->", sorted([NoCompare(2), NoCompare(1)], key=lambda x: x.n))
```

```text
===== python3 - <e31_key_vs_lt.py =====
① key 없이
      Loud.__lt__ 가 불렸다
      Loud.__lt__ 가 불렸다
      Loud.__lt__ 가 불렸다
      Loud.__lt__ 가 불렸다
   결과 : [Loud(1), Loud(2), Loud(3)]
② key= 로 정수를 뽑아 쓰면
   결과 : [Loud(1), Loud(2), Loud(3)]
③ key 가 돌려준 것의 __lt__ 가 쓰인다 — key 를 -n 으로
   결과 : [Loud(3), Loud(2), Loud(1)]
④ key 는 원소마다 정확히 한 번 불린다
   key 가 불린 횟수 : 3 | 불린 순서 : [3, 1, 2]
⑤ key 를 쓰면 원소의 __lt__ 는 아예 안 쓰이므로, 비교 불가 타입도 정렬된다
   key 없이 -> TypeError: '<' not supported between instances of 'NoCompare' and 'NoCompare'
   key 로   -> [NoCompare(1), NoCompare(2)]
(exit 0)
```

그림 해설.

- ① `key` 없이 정렬하면 `Loud.__lt__` 가 네 줄 찍힌다.
- ★★ ② **`key` 를 주자 로그가 통째로 비었다.** 비교는 `key` 가 돌려준 `int` 끼리 한 것이고,
  `Loud.__lt__` 는 **한 번도 안 불렸다.**
- ③ **이름표를 `-n` 으로 만들면 내림차순이 된다.** 비교되는 것은 어디까지나 **이름표**다.
- ★ ④ **`key` 는 원소마다 정확히 한 번**, 그리고 **원본 순서대로** 불렸다 — `[3, 1, 2]`.
  이것은 **문서가 약속한 보장**이고, 정본은 [10번](../10-list-methods-and-sort-key/2-summary.md)이다.
- ★★ ⑤ 그래서 **비교 메서드가 아예 없는 타입도 `key` 로는 정렬된다.**
  `key` 없이는 `TypeError` 인데 `key` 를 주면 그냥 선다.
  **「이 객체는 정렬 가능한가」라는 질문 자체가 `key` 앞에서는 의미가 없다.**

**비용** — `key` 는 원소당 함수 호출 한 번을 더한다. 대신 **비교가 `int`·`str` 같은 내장 타입에서 일어난다.**\
★ 둘 중 어느 쪽이 빠른지는 **이 배치가 안 쟀다.**

### 8. ★★ 섞이면 — 예외가 나는 자리와 안 나는 자리

**언제 쓰나** — 외부에서 읽어 온 데이터를 정렬하기 직전. 그리고 「정렬은 됐는데 순서가 이상하다」를 만났을 때.

```text
   두 종류의 실패

   ① 타입이 안 맞는다        1 < "a"
        -> TypeError 로 즉시 터진다              <- 시끄러운 실패. 그나마 낫다

   ② 타입은 맞는데 자가 고장났다   nan < 1.0 도 거짓, nan > 1.0 도 거짓
        -> 예외 없이 "안 정렬된 리스트" 가 나온다  <- ★ 조용한 실패
           입력 순서만 바뀌어도 결과가 달라진다
```

```python
# e31_uncomparable.py
print("① 정수와 문자열")
try:
    sorted([1, "a"])
except TypeError as ex:
    print("   TypeError:", ex)

print("② None 과 정수")
try:
    sorted([1, None])
except TypeError as ex:
    print("   TypeError:", ex)

print("③ == 는 되는데 < 는 안 된다")
print("   1 == 'a'        ->", 1 == "a")
print("   [1, 2] == (1, 2) ->", [1, 2] == (1, 2))
try:
    [1, 2] < (1, 2)
except TypeError as ex:
    print("   [1, 2] < (1, 2) -> TypeError:", ex)

print("④ bool 은 int 라 섞인다 :", sorted([True, 0, 2, False]))

print("⑤ nan 이 섞이면 — 예외 없이 틀린 답이 나온다")
nan = float("nan")
print("   nan < 1.0 :", nan < 1.0, "| nan > 1.0 :", nan > 1.0, "| nan == nan :", nan == nan)
print("   sorted([3.0, 1.0, nan, 2.0]) :", sorted([3.0, 1.0, nan, 2.0]))
print("   sorted([nan, 3.0, 1.0, 2.0]) :", sorted([nan, 3.0, 1.0, 2.0]))
print("   정렬됐는지 검사하면 :", all(a <= b for a, b in zip(sorted([3.0, 1.0, nan, 2.0]),
                                                        sorted([3.0, 1.0, nan, 2.0])[1:])))
print("   nan in [nan] :", nan in [nan], "  (정체 지름길)")
```

```text
===== python3 - <e31_uncomparable.py =====
① 정수와 문자열
   TypeError: '<' not supported between instances of 'str' and 'int'
② None 과 정수
   TypeError: '<' not supported between instances of 'NoneType' and 'int'
③ == 는 되는데 < 는 안 된다
   1 == 'a'        -> False
   [1, 2] == (1, 2) -> False
   [1, 2] < (1, 2) -> TypeError: '<' not supported between instances of 'list' and 'tuple'
④ bool 은 int 라 섞인다 : [0, False, True, 2]
⑤ nan 이 섞이면 — 예외 없이 틀린 답이 나온다
   nan < 1.0 : False | nan > 1.0 : False | nan == nan : False
   sorted([3.0, 1.0, nan, 2.0]) : [1.0, 2.0, 3.0, nan]
   sorted([nan, 3.0, 1.0, 2.0]) : [nan, 1.0, 2.0, 3.0]
   정렬됐는지 검사하면 : False
   nan in [nan] : True   (정체 지름길)
(exit 0)
```

그림 해설.

- ① ② **타입이 섞이면 `TypeError`** 다. 문구가 **어느 두 타입인지** 적어 준다.
  ★ `sorted([1, "a"])` 의 문구가 `'str' and 'int'` 인 것에 주의하라 — **왼쪽이 `str`** 이다.
  TimSort 가 `` "a" < 1 `` 쪽을 물었기 때문이고, (4)④와 **같은 자리**다.
- ★ ③ **`==` 는 되는데 `<` 는 안 된다.** `1 == 'a'` 는 조용히 `False` 이고 `` [1, 2] == (1, 2) `` 도 `False` 다.
  같음은 「**모르면 거짓**」이고 순서는 「**모르면 예외**」다. 이 비대칭이 이 주제에서 가장 자주 사람을 놓친다.
- ④ **`bool` 은 `int` 의 하위 타입**이라 섞인다. `[0, False, True, 2]` 에서 **`0` 이 `False` 보다 앞**인데,
  그것이 곧 (6)의 안정성이다 — 둘은 동점이고 원본 순서가 그렇다([02번](../02-is-vs-eq-interning/2-summary.md)).
- ★★★ ⑤ 가 이 주제의 네 번째 창이 잡아내는 자리다.
  `nan` 은 `<`·`>`·`==` **셋 다 거짓**이라 **전순서가 아니다.**
  그런데 `sorted` 는 **예외를 안 던진다** — `[1.0, 2.0, 3.0, nan]` 과 `[nan, 1.0, 2.0, 3.0]` 이
  **입력 순서만 바꿨는데 다른 자리에 `nan` 을 둔다.**
  ★ 그리고 `` all(a <= b …) `` 로 검사하면 **`False`** 다. **스스로 정렬됐다고 주장하지도 못하는 결과**를 돌려준 것이다.
- ★ 마지막 줄의 `nan in [nan]` 이 `True` 인 것은 **`==` 가 아니라 정체를 먼저 보는 CPython 의 지름길** 때문이다
  ([30번](../30-repr-eq-hash-contracts/2-summary.md)에서 같은 지름길을 다룬다).

- ★ **처방은 자를 고치는 것**이다 — `` key=lambda x: (math.isnan(x), x) `` 처럼 `nan` 을 **한쪽 끝으로 몰아**
  전순서를 만들어 준다((7)의 이름표가 그 자리다).
- ★★ 「**그러면 원소가 많아지면 파이썬도 던지나**」가 다음 질문이고, (9)가 그것을 잰다.

**비용** — 아무 검사도 없으니 **정상 경로가 가장 빠르다.**\
대신 **틀린 순서가 시스템을 그대로 통과해** 맨 마지막 화면에서 드러난다.

### 9. ★★★ 계약을 어겨도 파이썬은 검사하지 않는다 — 10만 개까지 조용했다

**언제 쓰나** — 「작은 데이터로 테스트했는데 운영에서도 안 터진다」를 설명할 때.
그리고 **정적 언어에서 오는 사람에게 이 갈래의 성격을 한 번에 보일 때.**

(8)은 `nan` 이라는 **값** 쪽 결함이었다. 여기서는 **자 자체가 흔들리는** 경우를 던진다 —
`__lt__` 가 물을 때마다 다른 답을 주는 `Shaky` 다.
★ **Java 28편이 같은 모양의 비교자로 예외를 받은 바로 그 실험**이라 두 편의 수치가 같은 축 위에 놓인다.

```text
   같은 결함을 원소 수 축으로 놓으면

   n =      10     100    2000    10000   100000
   Java     통과    통과    throw   throw   throw     <- MIN_MERGE(32) 를 넘고 병합에 들어가면 검사한다
   Python   통과    통과    통과    통과    통과      <- ★ 검사하는 코드가 없다

   ★ 두 언어 다 "작으면 조용하다". 갈리는 것은 "커지면 시끄러워지나" 다.
```

```python
# e31_no_check.py
import random


class Shaky:
    """비일관 비교 — 자기가 흔들린다. Java 갈래 28편이 같은 실험으로 예외를 받았다."""

    def __init__(self, n):
        self.n = n

    def __repr__(self):
        return "Shaky(%d)" % self.n

    def __lt__(self, other):
        return random.random() < 0.5          # ★ 물을 때마다 답이 달라진다


def sorted_properly(xs):
    return all(not (b < a) for a, b in zip(xs, xs[1:]))


for n in (10, 100, 2000, 10000, 100000):
    random.seed(0)                            # 같은 수열을 쓰도록 고정한다
    data = [Shaky(i) for i in range(n)]
    try:
        out = sorted(data)
        print("n=%-7d 예외 없음 | 길이 %-7d | 정말 정렬됐나 %s"
              % (n, len(out), sorted_properly(out)))
    except Exception as ex:
        print("n=%-7d %s: %s" % (n, type(ex).__name__, ex))

print()
print("비교가 아예 예외를 던지면? — 그때는 그 예외가 그대로 나간다")


class Boom:
    def __lt__(self, other):
        raise RuntimeError("비교 중에 터졌다")


try:
    sorted([Boom(), Boom()])
except Exception as ex:
    print("  ", type(ex).__name__, ":", ex)

print()
print("리스트는 어떤 상태로 남나 — 예외가 난 sort 뒤의 원본")
xs = [Boom(), Boom(), Boom()]
try:
    xs.sort()
except RuntimeError:
    pass
print("   길이 :", len(xs), "| 전부 Boom 인가 :", all(isinstance(v, Boom) for v in xs))
```

```text
===== python3 - <e31_no_check.py =====
n=10      예외 없음 | 길이 10      | 정말 정렬됐나 False
n=100     예외 없음 | 길이 100     | 정말 정렬됐나 False
n=2000    예외 없음 | 길이 2000    | 정말 정렬됐나 False
n=10000   예외 없음 | 길이 10000   | 정말 정렬됐나 False
n=100000  예외 없음 | 길이 100000  | 정말 정렬됐나 False

비교가 아예 예외를 던지면? — 그때는 그 예외가 그대로 나간다
   RuntimeError : 비교 중에 터졌다

리스트는 어떤 상태로 남나 — 예외가 난 sort 뒤의 원본
   길이 : 3 | 전부 Boom 인가 : True
(exit 0)
```

그림 해설.

- ★★★ **다섯 크기 전부 `예외 없음` 이다.** `n=100000` 까지 갔는데도 한 줄도 안 던졌다.
  Java 는 **계약을 어긴 비교자**(추이성을 깬 것)에 **`n=2000` 부터**
  `IllegalArgumentException: Comparison method violates its general contract!` 를 던졌다
  ([Java 28번](../../../java/syntax/28-comparable-comparator/2-summary.md)의 실측 — 그쪽은 `n=1000` 까지는 **조용한 오답**이었다).
  ★ **자의 모양이 서로 다르므로 「같은 입력에서 갈렸다」가 아니다** — 갈린 것은 「**검사하는 코드가 있느냐**」다.
- ★★ **그런데 결과는 정말 안 정렬돼 있다** — `정말 정렬됐나 False` 가 **다섯 줄 전부**다.
  「예외가 없다」가 「답이 맞다」가 아니라는 것을 **같은 줄에서 동시에** 보여 준다.
- ★ **길이는 보존된다.** `길이 100000` 이 그대로다 — 원소를 잃지도 만들지도 않는다.
  **틀린 것은 순서 하나뿐**이고, 그래서 `len()` 이나 개수 검사로는 **절대 안 잡힌다.**
- ★★ **「검사를 안 한다」이지 「예외를 삼킨다」가 아니다** — `Boom` 의 `__lt__` 가 `RuntimeError` 를 던지자
  그 예외가 **그대로 밖으로 나왔다**. 정렬 루틴은 비교의 **결과를 검사하지 않을 뿐** 예외는 안 건드린다.
- ★ **예외로 끝난 `sort` 뒤에도 원본은 길이·원소가 보존된다** — `길이 : 3 | 전부 Boom 인가 : True`.
  ★ 다만 **순서는 보장되지 않는다.** 정렬이 중간까지 진행된 상태로 남는다는 것은
  [10번](../10-list-methods-and-sort-key/2-summary.md)이 정본이다.
- ★★★ **층을 조심해라** — 「검사하지 않는다」는 **언어가 약속한 것이 아니다.**
  문서는 「검사한다」고도 「안 한다」고도 적지 않았다. 이 다섯 줄은 **CPython 이 지금 그렇게 한다**는 관찰이다.
  **「명세가 보장한다」로 쓰면 틀린다.**

#### ★★★ 세 언어 대비 — 같은 결함이 어디서 잡히나

순서 계약을 어긴다는 사실은 세 언어가 똑같이 안고 있다. **잡히는 시점만 다르다.**

| 언어 | 계약을 어긴 자로 정렬하면 | 무엇이 막아 주나 | 언제 알게 되나 |
|---|---|---|---|
| **Rust** | `` v.sort() `` 가 **컴파일 안 된다**(`f64`) — `the trait bound f64: Ord is not satisfied` | **타입 시스템**. `f64` 는 `PartialOrd` 까지만 구현한다 | **컴파일 시점** |
| **Rust**(우회) | `` sort_by(\|a, b\| a.partial_cmp(b).unwrap()) `` 는 **패닉** | `unwrap` 이 `None` 에서 죽는다 | **실행 시점 · 시끄럽게** |
| **Java** | **`n=2000` 부터** `IllegalArgumentException: Comparison method violates its general contract!` | TimSort 의 **병합 단계 검사**(`MIN_MERGE` 미만이면 그 코드에 도달조차 안 한다) | **실행 시점 · 원소 수에 달림** |
| **Python** | ★ **`n=100000` 까지 아무 일도 안 난다.** 안 정렬된 리스트를 돌려준다 | ★ **아무것도 안 막는다** | ★ **아무도 안 알려 준다** |

- ★★★ **이것이 「프로토콜이 곧 계약」인 주제의 얼굴이다.** 계약을 어기면 **컴파일러가 아니라 자료구조가 조용히 틀린다.**
- ★ **Rust 는 「그 자를 쓸 수 없다」를 타입으로 말한다** — 전순서를 빌려 오려면 `` f64::total_cmp `` 를 명시해야 한다
  ([Rust 28번](../../../rust/syntax/28-partialeq-eq-partialord-ord-and-hash-contracts/2-summary.md)).
- ★ **Java 는 중간이다** — 던지기는 하는데 **원소가 적으면 던질 코드에 도달조차 안 한다.**
  그 축의 실측(원소 수를 바꿔 가며 6만 회)은 [Java 28번](../../../java/syntax/28-comparable-comparator/2-summary.md)이 정본이다.
- ★★ **파이썬에는 그 검사가 아예 없다** — 원소 수를 5,000배로 키워도 결과가 안 바뀌었다.
  **「테스트 데이터가 작아서 안 터진 것」이 아니다.**
- ★ 그래서 **파이썬에서 유일한 창은 결과를 직접 검사하는 것**이다 —
  `` all(not (b < a) for a, b in zip(xs, xs[1:])) `` 한 줄이 블록의 `정말 정렬됐나` 칸이다.

**비용** — 검사가 없으니 **정상 경로에 군더더기가 없다.**\
대신 **틀린 순서가 시스템을 그대로 통과한다.** 계약을 지키는 책임이 100% 사람에게 있다.

## 문법 — 형태와 규칙

**여섯 연산자와 여섯 메서드**

| 연산자 | 메서드 | 반사 짝 | `object` 가 주는 기본값 |
|---|---|---|---|
| `<` | `__lt__` | `__gt__` | 없음 — `TypeError` |
| `<=` | `__le__` | `__ge__` | 없음 — `TypeError` |
| `>` | `__gt__` | `__lt__` | 없음 — `TypeError` |
| `>=` | `__ge__` | `__le__` | 없음 — `TypeError` |
| `==` | `__eq__` | `__eq__` | **정체 비교**(`is`) |
| `!=` | `__ne__` | `__ne__` | **`__eq__` 를 뒤집는다** |

- ★ **순서 넷은 기본값이 없고 같음 둘은 있다.** 그래서 아무것도 안 쓴 클래스도 `==` 는 되고 `<` 는 안 된다((8)③).
- ★ 반사 짝은 **연산자 모양이 아니라 표대로**다. `<=` 의 짝은 `>=` 이지 `>` 가 아니다((3)⑤).

**최소 형태 — 정렬만 되면 될 때**

정렬만 필요하면 `__lt__` 하나다((1)의 `V`). 비교할 수 없는 상대에는 `NotImplemented` 를 돌려준다((4)의 `Strict`).

**여섯을 다 원할 때 — 두 가지 길**

| 길 | 내가 쓰는 것 | 얻는 것 | 안 얻는 것 |
|---|---|---|---|
| 손으로 여섯 개 | `__eq__` + 순서 넷 | 여섯 연산자 전부 | `__hash__`(`__eq__` 때문에 꺼진다) |
| `@total_ordering` | `__eq__` + 순서 **하나** | 여섯 연산자 전부 | `__hash__` · `__ne__` 는 `object` 몫 |

★ **어느 길이든 `__hash__` 는 내 몫이다.** 정본은 [30번](../30-repr-eq-hash-contracts/2-summary.md)이다.

**정렬하는 쪽의 세 손잡이**

- `key=` — 이름표를 만들어 **그것끼리** 비교한다. 원소의 `__lt__` 는 안 쓰인다((7)).
- `reverse=True` — **비교를 뒤집는다.** 결과를 뒤집는 것이 아니다((6)).
- `functools.cmp_to_key` — 옛 `cmp` 함수를 `key` 로 바꾼다. 본거지는 [목록의 **45번 주제**](../45-functools/)다.

**금지 사례 — 이렇게 쓰면 터지거나 조용히 틀린다**

- `__lt__` 만 쓰고 `<=` 를 쓰는 코드 — `TypeError`((1)④).
- `__eq__` 와 순서 메서드를 **다른 필드**로 쓰는 것 — 동점 판정이 어긋나 안정성이 무의미해진다.
- `__lt__` 안에서 모르는 타입에 `False` 를 돌려주는 것 — `a < b` 와 `b > a` 가 **둘 다 거짓**이 된다((4)).
- `nan` 이 섞일 수 있는 `float` 리스트를 그냥 `sorted` 에 넣는 것((8)⑤).

## 어디서 틀리나

### (1) 「`__lt__` 하나면 여섯 연산자가 다 된다」로 안다

`sorted` 와 `min` 과 `heapq` 는 된다. **`<=` 와 `>=` 는 안 된다**((1)④).\
★ 그리고 `>` 가 되는 것은 **반사 연산 덕**이지 메서드가 생긴 것이 아니다.

### (2) 「내림차순이면 `__gt__` 가 쓰이겠지」로 안다

`reverse=True` 도 **`__lt__` 만 쓴다**((2)②). `__gt__` 를 아무리 잘 써 놔도 정렬에는 안 쓰인다.

### (3) ★ 「파이썬은 늘 `__lt__` 만 쓴다」로 외운다

**`max` 는 `__gt__` 를 쓴다**((2)④). 「정렬 루틴은 `<`」가 맞는 문장이고 `max`·`min` 은 그 문장 밖이다.

### (4) ★ `reverse=True` 와 `[::-1]` 을 같은 것으로 본다

동점이 없으면 같고 **동점이 있으면 다르다**((6)③). 블록이 그것을 `False` 한 글자로 찍었다.\
정본은 [10번](../10-list-methods-and-sort-key/2-summary.md)이다.

### (5) ★★ `total_ordering` 을 붙이면 dict 키가 될 줄 안다

**`__hash__` 는 안 채운다**((5)③). 오히려 `__eq__` 를 쓴 순간 꺼져 있다.\
★ 「정렬은 되는데 `set` 에 못 넣는 객체」가 이 실수의 얼굴이다.

### (6) ★ `total_ordering` 에 `__eq__` 를 안 준다

문서의 낱말이 `should` 라 **통과는 한다**((5)⑥). 그러면 정체 기준으로 돌아
`` NoEq(1) <= NoEq(1) `` 이 **거짓**이 된다. **아무 경고도 없다.**

### (7) ★★ `NotImplemented` 를 거짓으로 읽는다

`if` 에 넣으면 **참**이다((4)⑤). 「비교할 수 없으니 `False` 겠지」는 **정반대**다.\
★ 돌려줄 때도 `False` 가 아니라 `NotImplemented` 를 돌려줘야 언어가 반사 연산을 시도한다.

### (8) ★ `__lt__` 안의 로그를 `self` 가 왼쪽이라고 읽는다

반사 연산이면 **인자가 뒤집혀** 들어온다((3)①). `self=2 other=1` 이 곧 「`1 < 2` 를 물은 것」이다.

### (9) ★★ 「섞여 있으면 예외가 나니까 괜찮다」로 안다

**타입이 섞이면** 난다. **`nan` 은 안 난다**((8)⑤). 둘은 다른 실패다.\
★★ 그리고 **비일관 비교자는 원소를 10만 개로 키워도 안 난다**((9)).
Java 를 쓰다 온 사람이 「크면 `IllegalArgumentException` 이 나겠지」로 기대하는 자리인데, **파이썬에는 그 검사가 없다.**

### (10) ★ 비교 횟수를 성질로 적는다

세 원소에 네 번은 **이 판의 관찰**이다. TimSort 가 바뀌면 달라진다.\
근거로 쓸 것은 「**무엇이 불렸나**」와 「**순서**」뿐이다.

### (11) ★ `key` 를 줘 놓고 `__lt__` 를 고친다

`key` 가 있으면 **원소의 `__lt__` 는 아예 안 불린다**((7)②). 고쳐도 아무 일이 안 일어난다.

### (12) ★★ 「정렬됐다」를 확인 안 한다

파이썬은 결과가 정렬됐는지 **검사하지 않는다** — (9)가 다섯 크기로 그것을 못 박았다.\
의심스러운 데이터라면 `` all(not (b < a) for a, b in zip(r, r[1:])) `` 를 **직접 돌려 보는 것**이 유일한 창이다.\
★ **길이는 멀쩡하다는 것도 같이 기억해라**((9)) — 개수 검사로는 절대 안 잡힌다.

### (13) ★ 「검사를 안 한다」와 「예외를 삼킨다」를 같은 것으로 본다

비교가 **예외를 던지면 그 예외는 그대로 나간다**((9)의 `RuntimeError`).
정렬 루틴은 비교의 **결과를 검사하지 않을 뿐**이지 예외를 먹지 않는다.

## 구현 세부사항 대 언어 보장

### 언어 보장

- **반사 짝이 정해져 있다** — `__lt__` ↔ `__gt__`, `__le__` ↔ `__ge__`, `__eq__` 와 `__ne__` 는 자기 자신.
- **오른쪽이 왼쪽의 하위 클래스면 오른쪽의 반사 메서드가 먼저** 불린다.
- **`NotImplemented` 를 돌려주면 언어가 반사 연산을 시도하고, 그것도 안 되면 예외를 낸다.**
- **`NotImplemented` 의 진릿값 평가는 폐기 예정**이며 문서가 *"will raise a `TypeError` in a future version"* 이라고 적는다.
- **`object.__ne__` 는 `__eq__` 의 결과를 뒤집는다**(`NotImplemented` 가 아닐 때).
- **정렬 루틴은 `<` 를 쓴다** — Sorting HOWTO 의 문장.
- **`list.sort` 와 `sorted` 는 안정 정렬**이다. **`key` 는 원소당 정확히 한 번** 불린다.
- **`total_ordering` 은 순서 연산 하나와 `__eq__` 를 요구하고 나머지 순서 연산을 채운다.**

### CPython 구현 세부사항

- **`max` 가 `__gt__` 를, `min` 이 `__lt__` 를 쓰는 것** — 문서에 없다. 로그로 본 것이다((2)④).
- **비교의 횟수와 순서** — TimSort 가 정한다. 같은 결과를 다른 비교로 낼 수 있다.
- **`reverse=True` 가 결과를 뒤집는 대신 비교를 뒤집는 방식** — 관찰 가능한 결과(안정성)는 보장이지만, 로그의 모양은 구현이다.
- **`in` 과 `dict`·`list` 의 정체 지름길** — `nan in [nan]` 이 참인 이유((8)).
- **`heapq` 가 `__lt__` 만 쓰는 것** — 문서가 「최소 힙」이라고만 적는다.
- ★★★ **정렬이 비교 계약 위반을 검사하지 않는 것**((9)) — **문서는 검사한다고도 안 한다고도 적지 않았다.**
  「안 던진다」에 기대는 코드를 쓰면 안 되고, 「던질 것」이라고 기대해도 안 된다.
- **비교가 던진 예외가 그대로 전파되는 것**과 **예외로 끝난 `sort` 뒤 원본의 길이가 보존되는 것**((9)).

### 이 판(3.12.3)의 관찰

- 예외 문구 전부 — `'<' not supported between instances of 'Bare' and 'Bare'` ·
  `must define at least one ordering operation: < > <= >=` · `unhashable type: 'After'`.
- `NotImplemented` 의 타입 이름이 `NotImplementedType` 인 것.
- 경고 문구가 `NotImplemented should not be used in a boolean context` 인 것.
- 세 원소 정렬에 `__lt__` 가 **네 번**, `reverse=True` 에 **세 번** 불린 것.
- `` sorted([3.0, 1.0, nan, 2.0]) `` 가 `[1.0, 2.0, 3.0, nan]` 이고
  `` sorted([nan, 3.0, 1.0, 2.0]) `` 가 `[nan, 1.0, 2.0, 3.0]` 인 것 — **입력 순서에 달린 한 판의 결과**다.
- ★★ **흔들리는 비교자가 10 · 100 · 2000 · 10000 · 100000 에서 전부 예외 없이 끝난 것**((9)).
  `random.seed(0)` 으로 고정했으므로 **다시 돌려도 같은 줄이 나온다.**
  ★ 다섯 크기를 봤다는 것이지 **모든 크기를 봤다는 뜻은 아니다.**

### 그래서 이렇게 적으면 틀린다

| 틀린 문장 | 맞는 문장 |
|---|---|
| 「`__lt__` 하나면 여섯 연산자가 다 된다」 | 「정렬 루틴과 `min`·`heapq` 가 된다. `<=`·`>=` 는 안 된다」 |
| 「파이썬은 비교에 `__lt__` 만 쓴다」 | 「**정렬 루틴**이 `<` 를 쓴다. `max` 는 `__gt__` 를 쓴다」 |
| 「세 원소 정렬에 `__lt__` 가 네 번 불린다」 | 「이 판에서 네 번 불렸다. 횟수는 TimSort 의 성질이다」 |
| 「`total_ordering` 이 여섯 개를 만들어 준다」 | 「비어 있던 순서 셋을 채운다. `__ne__`·`__hash__`·`__eq__` 는 안 채운다」 |
| 「`NotImplemented` 는 거짓이다」 | 「참이다. 그리고 진릿값 평가는 폐기 예정이다」 |
| 「비교 불가면 예외가 난다」 | 「타입이 안 맞으면 난다. `nan` 은 안 난다」 |
| 「`reverse=True` 는 정렬 후 뒤집기다」 | 「비교를 뒤집는다. 동점 무리는 원래 순서 그대로다」 |
| 「데이터가 커지면 파이썬도 계약 위반을 던진다」 | 「10만 개까지 안 던졌다. 그 검사가 없다」 |
| 「파이썬 명세가 검사하지 않는다고 보장한다」 | ★ 「명세는 아무 말도 안 한다. **CPython 의 관찰**이다」 |

## 언제 쓰고 언제 안 쓰나

**`__lt__` 하나만 쓴다** — 내부에서 `sorted`·`min`·`heapq` 에만 쓰는 값 객체.\
가장 싸고, 안 되는 것(`<=`)이 **예외로 드러난다.**

**`@total_ordering` 을 쓴다** — 남이 쓰는 API 라서 여섯 연산자가 다 돌아야 할 때.\
★ **`__hash__` 를 같이 정하는 것을 잊지 마라**([30번](../30-repr-eq-hash-contracts/2-summary.md)).

**여섯을 손으로 쓴다** — 문서가 적은 주의(느린 실행·복잡한 스택 트레이스)가 문제가 될 때.\
★ **그 판단은 재 보고 한다.** 이 배치는 안 쟀다.

**`key=` 를 쓴다** — 남의 타입을 정렬할 때. 기준이 여럿일 때. `nan`·`None` 을 한쪽으로 몰 때.\
★ **원소에 프로토콜을 안 붙여도 되는 유일한 길**이다((7)⑤).

**`dataclass(order=True)` 를 쓴다** — 필드 선언 순서대로 사전식 비교가 필요할 때.\
정본은 [목록의 **36번 주제**](../36-dataclasses/)다.

**안 쓴다** — 순서에 뜻이 없는 값. 억지로 `__lt__` 를 붙이면 **틀린 정렬이 조용히 돌아간다.**\
정렬이 필요하면 **`key` 로 그때그때 기준을 밝히는 쪽**이 읽기 쉽다.

★★ **어느 길을 골랐든 계약은 테스트로 지킨다.** 파이썬은 (9)에서 본 대로 **아무것도 안 검사한다.**\
`__lt__` 를 손으로 쓴 클래스에는 **추이성 검사 한 줄**을 테스트에 넣어 두는 것이 유일한 방어선이다 —
`` all(not (b < a) for a, b in zip(r, r[1:])) `` 로 **정렬 결과를 되읽는 것**이 가장 싸다.

## 핵심 문장

- **정렬 루틴은 `<` 하나만 묻는다.** 그래서 `__lt__` 하나로 `sorted` 가 되고, 그것은 **문서가 적은 보장**이다.
- **그러나 `max` 는 `__gt__` 를 쓴다** — 「늘 `__lt__`」로 외우면 거기서 틀린다.
- **`>` 가 되는 것은 메서드가 생긴 것이 아니라 반사 연산**이다. 인자가 뒤집혀 들어온다.
- **반사 짝은 `<`↔`>` · `<=`↔`>=` 로 고정**이라 `__lt__` 로는 `<=` 가 절대 안 생긴다.
- **`NotImplemented` 는 「모른다」이지 「거짓」이 아니다.** `if` 에 넣으면 참이고, 그 평가는 폐기 예정이다.
- **`total_ordering` 은 비어 있던 순서 셋을 채우고 `__hash__` 는 건드리지 않는다** — 정렬은 되는데 dict 키는 못 되는 물건이 나온다.
- **`reverse=True` 는 비교를 뒤집지 결과를 뒤집지 않는다** — 동점 무리가 살아 있어 `[::-1]` 과 다르다.
- **`key` 를 주면 원소의 `__lt__` 는 한 번도 안 불린다** — 비교는 이름표끼리 한다.
- ★★★ **계약을 어겨도 파이썬은 안 던진다** — 흔들리는 비교자를 **10만 개**에 물려도 조용했고, 결과는 정말 안 정렬돼 있었다.
  Rust 는 컴파일에서, Java 는 `n=2000` 부터 잡는데 **파이썬은 아무도 안 알려 준다.**
- ★★ 그런데 **「검사를 안 한다」이지 「예외를 삼킨다」가 아니다** — 비교가 던진 예외는 그대로 나간다.
- ★ **그 「안 던진다」조차 보장이 아니라 관찰이다.** 문서는 검사 여부를 한 마디도 안 적는다.

## 관련 자료

- 목록: [python/syntax 주제 목록](../README.md) — 이 주제는 **31번**
- 선행: [10-list-methods-and-sort-key](../10-list-methods-and-sort-key/2-summary.md) — **정렬 키의 정본.**\
  **경계**: 그쪽은 「`sort`/`sorted` 를 어떻게 쓰나」(`key=`·`reverse=`·안정성·나눠 정렬)까지,
  여기는 「**정렬이 내 객체에게 무엇을 묻나**」부터다. 안정 정렬 보장의 근거 문장은 **그쪽에서 읽는다.**
- 선행: [30-repr-eq-hash-contracts](../30-repr-eq-hash-contracts/2-summary.md) — **`__eq__` 를 정의하면 `__hash__` 가 꺼지는 것의 정본.**\
  **경계**: 그쪽은 「같음의 계약」까지, 여기는 「**순서의 계약**」부터. 둘이 만나는 자리는 (5)③ 하나다.
- 선행: [02-is-vs-eq-interning](../02-is-vs-eq-interning/2-summary.md) — `True == 1` 이 되는 이유((8)④).
- 선행: [04-numeric-types-and-division](../04-numeric-types-and-division/2-summary.md) — `float` 의 성질.
- 이어지는 곳: [32-container-protocol](../32-container-protocol/2-summary.md) — **같은 「프로토콜이 곧 계약」 주제의 컨테이너 판.**
- 이어지는 곳: [13-set-and-frozenset](../13-set-and-frozenset/2-summary.md) — 집합이 든 리스트의 정렬이 정의되지 않는 이유.
- 이어지는 곳: [목록의 **36번 주제**](../36-dataclasses/) 「`dataclasses`」 — `order=True` 가 순서 넷을 만들어 주는 것.
- 이어지는 곳: [목록의 **45번 주제**](../45-functools/) 「`functools`」 — `cmp_to_key` 의 본거지.
- 이어지는 곳: [목록의 **44번 주제**](../44-itertools/) 「`itertools`」 — `groupby` 가 정렬을 전제한다는 것.
- 이어지는 곳: [목록의 **50번 주제**](../50-decimal-float-precision-and-round/) 「`decimal`·float 정밀도」 — `nan` 이 어디서 생기나.
- 대비: [Rust 28번](../../../rust/syntax/28-partialeq-eq-partialord-ord-and-hash-contracts/2-summary.md) —
  **`f64` 가 `Ord` 가 아니라 `sort()` 가 컴파일조차 안 되는 것.** 같은 결함을 **타입으로** 막는 판이다.
- 대비: [Java 28번](../../../java/syntax/28-comparable-comparator/2-summary.md) —
  **`Comparable` 계약과 TimSort 의 `IllegalArgumentException`.**\
  ★ **두 편이 같은 축(원소 수)을 잰다** — Java 는 `n=2000` 부터 던지고 파이썬은 `n=100000` 까지 조용하다((9)).
  `MIN_MERGE` 가 왜 경계인지는 그 편이 정본이다.
- 대비: C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **19번** — `Equals`/`GetHashCode` 의 동등성 쪽 대비.
- 원리: [`cs/algorithm/01-elementary-sort/`](../../../../../algorithm/01-elementary-sort/) — **정렬 알고리즘 자체는 그쪽이 정본이다.**\
  TimSort 가 왜 run 을 쌓는지는 거기서 읽고, 여기서는 **「무엇을 묻나」만** 쓴다.

## 용어 풀이

> **비교 프로토콜(rich comparison protocol)** — 여섯 연산자가 여섯 특수 메서드로 내려가는 규칙.\
> 예: `a < b` 는 `a.__lt__(b)` 를 먼저 부른다.

> **반사 연산(reflected operation)** — 왼쪽이 못 하면 오른쪽에게 짝이 되는 질문을 **인자를 뒤집어** 하는 것.\
> 예: `a < b` 가 `b.__gt__(a)` 가 된다.

> **반사 짝(reflection pair)** — 어느 메서드가 어느 메서드의 거울인가. `<`↔`>`, `<=`↔`>=`, `==`↔`==`, `!=`↔`!=`.\
> 예: `__lt__` 만 써 두면 `>` 는 되고 `<=` 는 안 된다.

> **`NotImplemented`** — 「이 조합은 내가 못 다룬다」를 뜻하는 특별한 값.\
> 예: `__lt__` 가 그것을 돌려주면 언어가 상대에게 다시 묻고, 그것도 안 되면 `TypeError` 를 낸다.

> **전순서(total order)** — 어느 둘이든 `<`·`==`·`>` 중 정확히 하나가 성립하는 순서.\
> 예: `float` 은 `nan` 때문에 전순서가 아니다.

> **안정 정렬(stable sort)** — 비교해서 같은 원소들의 **원래 순서를 바꾸지 않는** 정렬.\
> 예: 점수로 정렬해도 동점자끼리는 명단 순서 그대로다.

> **동점 무리(tie group)** — 비교해서 같다고 판정된 원소들의 덩어리.\
> 예: `reverse=True` 는 이 덩어리 안을 안 뒤집고, `[::-1]` 은 뒤집는다.

> **정렬 키(sort key)** — 원소에서 뽑아낸 **비교용 이름표**.\
> 예: `key=len` 은 문자열 대신 길이끼리 비교하게 만든다.

> **`functools.total_ordering`** — 순서 연산 하나와 `__eq__` 를 보고 **나머지 순서 연산을 채워 주는** 클래스 데코레이터.\
> 예: `__lt__` 만 주면 `__le__`·`__gt__`·`__ge__` 가 클래스 칸에 생긴다.

> **하위 클래스 우선권(subclass priority)** — 오른쪽 피연산자의 타입이 왼쪽의 하위 클래스면 **오른쪽의 반사 메서드가 먼저** 불리는 규칙.\
> 예: `P() < Q()` 에서 `Q` 가 `P` 의 하위면 `Q.__gt__` 가 먼저다.

> **TimSort** — CPython 과 JVM 이 쓰는 정렬 알고리즘. **이 문서에서는 이름만 쓰고 원리는 안 다룬다.**\
> 예: 비교 횟수가 데이터에 따라 달라지는 것이 이 알고리즘의 성질이다.

> **조용한 실패(silent failure)** — 예외도 경고도 없이 답만 틀리는 실패.\
> 예: `nan` 이 섞인 리스트를 정렬하면 안 정렬된 리스트가 아무 말 없이 나온다.

## 더 들어가면

- **`__eq__` 와 순서가 어긋나면** — 파이썬에는 Java 의 `TreeMap` 처럼 「`compareTo` 가 0 이면 같은 것」으로 보는
  표준 자료구조가 없어서, 그 사고는 **정렬의 안정성이 무의미해지는** 모양으로만 나타난다.
  `__eq__` 가 「같다」는 둘을 `__lt__` 가 「다르다」고 하면 **동점 무리 자체가 생기지 않는다.**
- **`functools.cmp_to_key`** — 두 원소를 받아 음수·0·양수를 돌려주는 옛 `cmp` 함수를 `key` 로 감싼다.
  반환된 객체가 `__lt__` 를 구현하고 있어서 **(7)의 이름표 자리에 그대로 들어간다.** 정본은 [목록의 **45번 주제**](../45-functools/)다.
- **`dataclass(order=True)`** — 필드 선언 순서대로 튜플을 만들어 비교하는 순서 넷을 생성한다.
  `total_ordering` 과 달리 **`__lt__` 부터 넷을 다 만든다.** 정본은 [목록의 **36번 주제**](../36-dataclasses/)다.
- **`bisect` 와 `heapq`** — 둘 다 `<` 만 쓴다. 그래서 `__lt__` 하나만 있는 객체도 **이진 탐색과 힙에 그대로 들어간다.**
- **`sorted` 에 `key` 와 `reverse` 를 같이 주면** — 이름표를 만든 뒤 그 이름표 비교를 뒤집는다.
  기준마다 방향이 다르면 **나눠 정렬**이 유일한 일반해이고, 그 세부는 [10번](../10-list-methods-and-sort-key/2-summary.md)이 정본이다.
- **`Enum` 의 비교** — 기본 `Enum` 은 순서가 없고 `IntEnum` 은 `int` 라서 섞인다. [목록의 **37번 주제**](../37-enum/).
