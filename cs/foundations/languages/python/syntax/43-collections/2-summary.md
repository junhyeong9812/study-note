# python/syntax/43-collections — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만(문서 원본 `.rst` 를 받아 문장을 찾았다).
> - [`collections`(3.12)](https://docs.python.org/3.12/library/collections.html) —
>   `defaultdict.__missing__` 의 *"this value is inserted in the dictionary for the key, and returned"* · *"`__missing__()` is not called for any operations besides `__getitem__()`"* ·
>   `Counter` 의 *"return a zero count for missing items instead of raising a KeyError"* · *"the output will exclude results with counts of zero or less"* ·
>   `most_common` 의 *"Elements with equal counts are ordered in the order first encountered"* ·
>   `ChainMap` 의 *"writes, updates, and deletions only operate on the first mapping"* ·
>   `deque` 의 *"approximately the same O(1) performance in either direction"* · *"Indexed access is O(1) at both ends but slows to O(n) in the middle"* ·
>   `OrderedDict` 절의 *"The equality operation for OrderedDict checks for matching order"* 와 `dict` 와의 차이 목록
>
> **실행 검증** — 이 문서에 실린 출력은 전부 이 머신에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.\
> 판은 `python3` **3.12.3** 하나. 던지는 형태는 `python3 - <파일` 로 고정했고, 예외는 `except` 로 받아 **타입과 메시지만** 찍었다.\
> ★★★ **복잡도는 문서의 말이다** — 「`deque` 양끝 O(1)·가운데 O(n)」은 위 문장을 옮긴 것이고 **이 문서는 시간을 한 번도 재지 않았다.**
> 이 머신에서 잰 것은 **`len`·호출 횟수·출력 값**뿐이다. 「`deque` 가 `list` 보다 빠르다」는 **한 줄도 쓰지 않는다.**\
> **버전**(문서의 `versionadded` 표기) — `OrderedDict`·`Counter` **3.1**, `ChainMap` **3.3**, `deque.maxlen` 속성 **3.1**, `Counter` 의 단항 `+`·`-` **3.3**, `Counter.total()` **3.10**,
> `Counter` 의 `==` 가 **없는 원소를 0 으로 보는 것**은 **3.10** 부터(문서의 *"In equality tests, missing elements are treated as having zero counts"* 와 그 버전 표기). `dict` 의 삽입 순서 보장은 **3.7**.\
> ★ **구현 대 언어 보장 한 줄** — 위 문서 문장들이 보장이다. **`most_common` 의 동률 순서도 문서가 보장한다**(「처음 만난 순서」).
> 예외 **문구**(`deque already at its maximum size` 따위)는 CPython 의 것이다.\
> ★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다 | 안 흔들린다(근거로 써도 되는 칸) |
> |---|---|
> | 판이 오르면 예외 **문구** | ★★ 격자의 칸 · 마지막 줄 **「… N / M」** · `len` 전→후 · factory 호출 수 |
> | — (주소·시간·`set` 출력을 한 곳도 안 찍었다) | `dict`·`Counter` 의 **출력 순서** — 삽입 순서가 **3.7+ 언어 보장**이고 `most_common` 동률 순서도 문서 보장 |
>
> ★ `PYTHONHASHSEED` 를 바꿔 한 번 더 캡처해도 **한 글자도 같았다** — 순서가 해시에 기대는 출력이 없다는 뜻이다.\
> **선행** — [12-dict-and-key-requirements](../12-dict-and-key-requirements/2-summary.md)(★★★ **동작 6 이 「`defaultdict` 는 조회만 해도 키를 만든다」까지를 먼저 보였다 — 이 주제는 그 위에서 「어느 조회가, 몇 번, 무엇을 부르나」를 센다**).

## 한눈에 — 쉽게 말하면

**`collections` 는 「특수 용도 서랍장」 다섯 개다.** 기본 서랍장(`dict`·`list`)으로도 되지만, 서랍마다 **한 가지 버릇**이 붙어 있다.

* **`defaultdict`** — 없는 칸을 열면 **빈 봉투를 넣고** 연다. ★ **열어 보기만 해도 칸이 생긴다.**
* **`Counter`** — 없는 칸을 열면 **`0` 을 보여 주고 칸은 안 만든다.** 빼기는 **양수만 남긴다.**
* **`OrderedDict`** — 칸의 **순서까지** 같아야 같은 서랍장이다. 칸을 **맨 끝으로 옮기는** 손잡이가 있다.
* **`ChainMap`** — 서랍장 여러 개를 **겹쳐 보는** 창. 읽기는 위에서부터, ★ **쓰기는 맨 위 한 장에만.**
* **`deque`** — 양끝에 문이 있는 칸줄. `maxlen` 을 주면 **넘치는 쪽의 반대편이 밀려 나간다.**

```text
   d = defaultdict(list)                    c = Counter()
   d['z']          -> []   ★ 칸이 생겼다       c['z']       -> 0    칸은 안 생긴다
   d.get('z')      -> None  칸 안 생김         'z' in c     -> False
   'z' in d        -> False 칸 안 생김

   ★ 같은 「없는 키 조회」인데 한쪽은 쓰기이고 한쪽은 읽기다
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 없는 칸을 열면 빈 봉투를 넣는다 | `defaultdict.__missing__` → `default_factory()` 를 **넣고** 돌려준다 | `len` 이 늘고 factory 호출 수가 는다 |
| ★ **여는** 손잡이 / **엿보는** 창 | `d[k]` / `d.get(k)`·`k in d` | 앞만 `__missing__` 을 부른다 |
| 없는 칸은 `0` 으로 보여 준다 | `Counter.__missing__` → `0`(넣지 않음) | `len(c)` 그대로 |
| 순서까지 보는 서랍장 | `OrderedDict` 의 `==` | 같은 종류끼리만 순서를 본다 |
| 맨 위 한 장에만 쓰는 겹친 창 | `ChainMap` | 쓰면 `maps[0]` 만 바뀐다 |
| 넘치면 반대편이 밀려 나가는 칸줄 | `deque(maxlen=n)` | `append` 는 왼쪽을, `appendleft` 는 오른쪽을 민다 |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.\
「**`if counts[word]:` 로 확인만 했는데 결과 dict 에 빈 키가 수백 개 생겼다**」와
「**그래프를 `defaultdict(list)` 로 들고 순회하다 `dictionary changed size during iteration`**」이 그것이다.\
둘 다 **엿보려다 연 것**이다.

> **`__missing__`** — `dict` 의 하위 클래스가 정의하면, **`d[k]` 에서 키가 없을 때** 불리는 메서드.\
> 예: `defaultdict` 는 이것으로 factory 를 불러 **넣고** 돌려주고, `Counter` 는 **`0` 을 돌려주기만** 한다.

> **`default_factory`** — `defaultdict(list)` 의 `list` 처럼, 없는 키에 넣을 값을 **만드는 호출 가능 객체**.\
> 예: `defaultdict(int)` 는 없는 키에 `0` 을 넣는다.

### ★★ 이 주제가 쓰는 창 / 부적용인 창

**본체는 ① 「조회가 키를 만드나」 격자 창이다.** 조회 여덟 가지를 **새 `defaultdict` 마다** 던지고 **`len` 전→후 · factory 호출 수**를 찍어 **`len` 이 늘어난 칸을 스크립트가 센다.**

| 창 | 무엇을 말해 주나 | 못 보는 것 |
|---|---|---|
| ① ★★★ **조회 격자**(`len` 전→후 · factory 호출 수) | **어느 조회가 쓰기인가** | 속도 |
| ② ★★ **`dict` 대 `OrderedDict` 격자** | 3.7+ 에서도 **무엇이 아직 갈리나** | 재배열 비용 |
| ③ ★★ **값 출력**(`Counter` 연산 · `ChainMap` 의 두 dict · `deque` 의 칸) | 연산이 **무엇을 남기나 · 어디에 쓰나** | — |
| ④ ★ **문서 인용** | 복잡도 · 동률 순서 보장 | 이 머신의 실제 시간 |
| ★ **부적용인 창** — 시간 · 메모리 | — | ★★★ **한 번도 재지 않았다.** 복잡도는 전부 ④ |

★★ **①의 둘째 열(factory 호출 수)이 이 주제의 네 번째 창이다.** `len` 만 보면 **`setdefault` 와 `d[k]` 가 같은 칸**(둘 다 `1 → 2`)으로 보인다.
factory 호출 수를 같이 찍으면 **`setdefault` 는 factory 를 안 부르고 넣은 것**(`0`)이고 **`d[k]` 는 factory 를 불러 넣은 것**(`1`)이 갈린다.

## 이 주제가 답하려는 질문

1. ★★★ **`defaultdict` 의 어느 조회가 키를 만드나** — `d[k]`·`get`·`in`·`+=`·`if d[k]:` 를 **`len` 으로** 가른다. 그리고 그 부작용이 **순회 중에** 무엇을 부르나.
2. ★★ **`Counter` 는 무엇이 `dict` 와 다른가** — 없는 키 · 음수와 0 · `+`/`-` 가 양수만 남기는 것 · 동률 순서.
3. **3.7+ 에서 `OrderedDict`·`ChainMap`·`deque` 는 왜 남아 있나** — 무엇이 갈리고, 복잡도는 **문서가** 무엇을 말하나.

★ 첫째가 이 주제의 인출 목표다.
**「엿보는 것(`get`·`in`)과 여는 것(`[]`)을 가를 수 있는 것」** 이 아는 것과 들은 것의 경계다.

## 동작 방식

> 이 절이 본문이다. 그림이 먼저 오고 문장이 그 그림을 읽어 준다.

### 1. ★★★ `defaultdict` 조회 격자 — 여덟 가지 조회, 다섯이 키를 만든다

**언제 쓰나** — `defaultdict` 로 묶기를 짠 뒤 **결과에 이상한 빈 키**가 보일 때.

```text
   d['z']   ──▶ dict.__getitem__ ──▶ 키 없음 ──▶ __missing__('z') ──▶ factory() ──▶ d['z'] = 0 ──▶ 0
                                                                          ★ 넣는다
   d.get('z')  ──▶ dict.get      ──▶ 키 없음 ──▶ None      (__missing__ 을 안 탄다)
   'z' in d    ──▶ __contains__  ──▶ False                (__missing__ 을 안 탄다)

   ★ 「d[...]」 모양이면 읽기로 보여도 넣는다:   d['z'] += 1  ·  if d['z']:  ·  f'{d["z"]}'
```

```python
# e43_lookup.py
from collections import Counter, defaultdict

made = []


def factory():
    made.append(1)
    return 0


def fresh():
    made.clear()
    return defaultdict(factory, {"a": 1})


PROBES = [
    ("d['z']", lambda d: d["z"]),
    ("d.get('z')", lambda d: d.get("z")),
    ("'z' in d", lambda d: "z" in d),
    ("d.setdefault('z', 9)", lambda d: d.setdefault("z", 9)),
    ("d.pop('z', None)", lambda d: d.pop("z", None)),
    ("d['z'] += 1", lambda d: d.__setitem__("z", d["z"] + 1)),
    ("if d['z']: …", lambda d: bool(d["z"])),
    ("f'{d[\"z\"]}'", lambda d: f"{d['z']}"),
]

print("%-22s | %-6s | %-8s | %s" % ("조회", "결과", "len 전→후", "factory 호출"))
grew = 0
for label, op in PROBES:
    d = fresh()
    before = len(d)
    result = op(d)
    grew += len(d) > before
    print("%-22s | %-6r | %d → %d    | %d" % (label, result, before, len(d), len(made)))
print("len 이 늘어난 칸 %d / %d" % (grew, len(PROBES)))

print("--- 같은 조회를 Counter 에 ---")
c = Counter(a=1)
print("c['z'] =", c["z"], "· len(c) =", len(c), "· 'z' in c =", "z" in c)
print("--- default_factory 가 None 이면 ---")
n = defaultdict(None, {"a": 1})
try:
    n["z"]
except KeyError as exc:
    print("n['z'] ->", type(exc).__name__ + ":", exc)
```

```text
===== python3 - <e43_lookup.py =====
조회                     | 결과     | len 전→후  | factory 호출
d['z']                 | 0      | 1 → 2    | 1
d.get('z')             | None   | 1 → 1    | 0
'z' in d               | False  | 1 → 1    | 0
d.setdefault('z', 9)   | 9      | 1 → 2    | 0
d.pop('z', None)       | None   | 1 → 1    | 0
d['z'] += 1            | None   | 1 → 2    | 1
if d['z']: …           | False  | 1 → 2    | 1
f'{d["z"]}'            | '0'    | 1 → 2    | 1
len 이 늘어난 칸 5 / 8
--- 같은 조회를 Counter 에 ---
c['z'] = 0 · len(c) = 1 · 'z' in c = False
--- default_factory 가 None 이면 ---
n['z'] -> KeyError: 'z'
(exit 0)
```

그림 해설.

* ★★★ **마지막 줄 — `len 이 늘어난 칸 5 / 8`.** 늘어난 다섯 중 **넷이 `d['z']` 모양**이고 **factory 가 한 번씩** 불렸다.
  ★ 문서 — *"`__missing__()` is not called for any operations besides `__getitem__()`"*. **`d[...]` 로 읽는 모든 자리**가 `__getitem__` 이다.
* ★★★ **`if d['z']: …` 와 `f'{d["z"]}'` 도 키를 만들었다** — 「검사만 했다」·「출력만 했다」가 **쓰기**였다. 결과는 `False`·`'0'` 으로 **그럴듯하다.**
* ★★ **`d['z'] += 1`** — 읽기(`__getitem__` → factory → 넣기)와 쓰기가 **한 줄**에 있다. `defaultdict(int)` 로 세는 관용이 이것에 기댄다.
* ★★ **`setdefault` 도 `1 → 2`** 인데 **factory 호출 `0`** — **인자로 준 `9` 를 넣었다.** `len` 창만으로는 이 둘이 안 갈린다(네 번째 창).
* ★ **`get`·`in`·`pop(k, None)` 은 `1 → 1`** — `__missing__` 을 안 탄다. [12번](../12-dict-and-key-requirements/2-summary.md) 동작 6 이 `get`·`in` 을 먼저 보였다.
* ★★ **`Counter` 는 같은 `c['z']` 가 `0` 인데 `len(c)` 가 `1` 그대로**다 — `Counter` 의 `__missing__` 은 **넣지 않고 `0` 을 돌려주기만** 한다.
  ★ 문서 — *"return a zero count for missing items instead of raising a KeyError"*. **같은 `[]` 가 서랍마다 다르게 구는 것**이다.
* ★ **`default_factory` 가 `None`** 이면 **보통 `dict` 처럼 `KeyError: 'z'`** 다(문서의 첫 문단 그대로).

**비용** — `defaultdict` 는 **넣기를 한 줄로** 만든 대가로 **모든 `[]` 읽기를 쓰기로** 바꾼다. 읽기 전용 자리에서는 **`get`·`in`** 을 쓰거나, 다 만든 뒤 `dict(d)` 로 바꿔 넘긴다.

### 2. ★★★ 그 부작용이 순회 중이면 — `RuntimeError`

**언제 쓰나** — 인접 리스트를 `defaultdict(list)` 로 들고 **이웃의 이웃**을 볼 때.

```python
# e43_iterate.py
from collections import defaultdict

follows = defaultdict(list)
follows["kim"].append("lee")
follows["lee"].append("park")

print("[1] 순회 전 키 :", list(follows))
try:
    for user in follows:
        for friend in follows[user]:
            print("  ", user, "→", friend, "· 친구의 친구 수", len(follows[friend]))
except RuntimeError as exc:
    print("[2]", type(exc).__name__ + ":", exc)
print("[3] 순회 뒤 키 :", list(follows))
```

```text
===== python3 - <e43_iterate.py =====
[1] 순회 전 키 : ['kim', 'lee']
   kim → lee · 친구의 친구 수 1
   lee → park · 친구의 친구 수 0
[2] RuntimeError: dictionary changed size during iteration
[3] 순회 뒤 키 : ['kim', 'lee', 'park']
(exit 0)
```

```text
   순회 전 키   kim, lee
   for user in follows:           kim        lee
     follows[friend]              lee(있음)   park(★ 없음 -> 넣는다 -> 크기 2 -> 3)
   다음 원소로 가려는 순간           -> RuntimeError  dictionary changed size during iteration
   순회 뒤 키   kim, lee, park     ★ 예외가 났는데 키는 남았다
```

* ★★★ `lee → park · 친구의 친구 수 0` 까지 찍힌 뒤 **`RuntimeError: dictionary changed size during iteration`** — `len(follows["park"])` 의 **`follows["park"]` 가 키를 넣었다.**
* ★★ **예외가 났는데 `park` 키는 남았다**(`[3]`). 순회 중 크기 변경 규칙은 [12번](../12-dict-and-key-requirements/2-summary.md) 동작 5 가 정본이고, 여기서는 **읽기처럼 보이는 줄이 그 규칙을 밟는 것**만 보였다.
* ★ `park → …` 줄은 **없다** — 크기가 바뀐 것을 **다음 원소로 넘어갈 때** 알아챘다.

**비용** — 고치는 법은 **`follows.get(friend, [])`**(엿보기)이거나, 순회를 `list(follows)` 의 **사본 위에서** 도는 것이다.

### 3. ★★★ `Counter` — 음수·0, 그리고 양수만 남기는 연산

**언제 쓰나** — 재고·투표처럼 **빼기**가 있는 세기. 「`c - d` 와 `c.subtract(d)` 가 뭐가 다르지」가 막힐 때.

```text
   c = Counter(a=3, b=1)      d = Counter(a=1, b=2, c=1)

   c - d            a: 3-1=2   b: 1-2=-1 ✗   c: 0-1=-1 ✗    -> Counter({'a': 2})       ★ 0 이하를 버린다
   c.subtract(d)    a: 2       b: -1         c: -1          -> 음수까지 남는다 (제자리)

   f = Counter(a=2, b=0, c=-1)
   +f               -> Counter({'a': 2})      단항 + 는 "양수만 남기기"
   f.total()        -> 1                      ★ 음수까지 더한다 (2 + 0 - 1)
   f.elements()     -> ['a', 'a']             ★ 1 미만은 건너뛴다
```

```python
# e43_counter.py
from collections import Counter

c = Counter(a=3, b=1)
d = Counter(a=1, b=2, c=1)

print("[1] 빼기 두 가지")
print("  c - d          :", c - d)
e = c.copy()
e.subtract(d)
print("  c.subtract(d)  :", e)

print("[2] 음수·0 을 넣으면")
f = Counter(a=2, b=0, c=-1)
print("  f              :", f)
print("  +f             :", +f)
print("  f + Counter()  :", f + Counter())
print("  f.total()      :", f.total())
print("  list(f.elements()) :", list(f.elements()))

print("[3] 동률의 순서")
print("  Counter('bca' * 2).most_common() :", Counter("bca" * 2).most_common())
print("  Counter('abc' * 2).most_common() :", Counter("abc" * 2).most_common())

print("[4] dict 인가")
print("  isinstance(c, dict) :", isinstance(c, dict), "· c == {'a': 3, 'b': 1} :", c == {"a": 3, "b": 1})
print("  Counter(a=1) == Counter(a=1, b=0) :", Counter(a=1) == Counter(a=1, b=0))
print("  {'a': 1} == {'a': 1, 'b': 0}      :", {"a": 1} == {"a": 1, "b": 0})
```

```text
===== python3 - <e43_counter.py =====
[1] 빼기 두 가지
  c - d          : Counter({'a': 2})
  c.subtract(d)  : Counter({'a': 2, 'b': -1, 'c': -1})
[2] 음수·0 을 넣으면
  f              : Counter({'a': 2, 'b': 0, 'c': -1})
  +f             : Counter({'a': 2})
  f + Counter()  : Counter({'a': 2})
  f.total()      : 1
  list(f.elements()) : ['a', 'a']
[3] 동률의 순서
  Counter('bca' * 2).most_common() : [('b', 2), ('c', 2), ('a', 2)]
  Counter('abc' * 2).most_common() : [('a', 2), ('b', 2), ('c', 2)]
[4] dict 인가
  isinstance(c, dict) : True · c == {'a': 3, 'b': 1} : True
  Counter(a=1) == Counter(a=1, b=0) : True
  {'a': 1} == {'a': 1, 'b': 0}      : False
(exit 0)
```

그림 해설.

* ★★★ **`[1]`** — **`c - d` 는 `Counter({'a': 2})`**, **`c.subtract(d)` 는 `{'a': 2, 'b': -1, 'c': -1}`**. 연산자는 **새 객체를 만들고 0 이하를 버린다**, 메서드는 **제자리에서 음수까지** 남긴다.
  ★ 문서 — *"Each operation can accept inputs with signed counts, but the output will exclude results with counts of zero or less."*
* ★★ **`[2]`** — `Counter` 는 **음수와 0 을 담을 수 있다**(`f` 가 그대로 찍힌다). **`+f`·`f + Counter()`** 가 둘 다 **양수만** 남긴다.
  ★★ 그런데 **`total()` 은 `1`** — **음수까지** 더했다(`2 + 0 − 1`). **`elements()` 는 `['a', 'a']`** — 1 미만을 건너뛰었다. **한 객체의 세 연산이 음수를 세 가지로 다룬다.**
* ★★ **`[3]` 동률 순서** — 셋 다 2 번인데 **`'bca' * 2` 는 b, c, a**, **`'abc' * 2` 는 a, b, c** — **처음 만난 순서**다.
  ★★ **이것은 관찰이 아니라 문서 보장이다** — *"Elements with equal counts are ordered in the order first encountered"*. 정렬이 안정적이고([10번](../10-list-methods-and-sort-key/2-summary.md) 동작 3) `dict` 가 삽입 순서를 지키는(3.7+) 것 위에 선다.
* ★★ **`[4]`** — `Counter` 는 **`dict` 의 하위 클래스**다(`True`). 그런데 **`Counter(a=1) == Counter(a=1, b=0)` 은 `True`**, 같은 모양의 `dict` 비교는 **`False`** — `Counter` 끼리는 **없는 원소를 0 으로** 본다(3.10+).

**비용** — `Counter` 의 음수는 **어떤 연산을 거쳤느냐에 따라 사라지기도 남기도** 한다. 재고처럼 음수가 **오류 신호**인 곳에서는 `subtract` 뒤에 **직접** 검사해야 한다.

### 4. ★★ `OrderedDict` 는 왜 3.7+ 에서도 남았나 — 격자

**언제 쓰나** — 「`dict` 가 순서를 지키니 `OrderedDict` 는 필요 없지 않나」가 막힐 때.

```python
# e43_ordered.py
from collections import OrderedDict


def run(fn):
    try:
        return repr(fn())
    except Exception as exc:
        return type(exc).__name__


PROBES = [
    ("x == 순서만 다른 같은 종류", lambda T: T(a=1, b=2) == T(b=2, a=1)),
    ("x == 순서만 다른 dict", lambda T: T(a=1, b=2) == dict(b=2, a=1)),
    ("list(x)", lambda T: list(T(b=1, a=2))),
    ("list(reversed(x))", lambda T: list(reversed(T(b=1, a=2)))),
    ("x.move_to_end('a') 뒤 list(x)", lambda T: (x := T(a=1, b=2), x.move_to_end("a"), list(x))[2]),
    ("x.popitem(last=False)", lambda T: T(a=1, b=2).popitem(last=False)),
    ("x.popitem()", lambda T: T(a=1, b=2).popitem()),
    ("x | {'c': 3}", lambda T: type(T(a=1) | {"c": 3}).__name__),
]

print("%-30s | %-22s | %s" % ("탐침", "dict", "OrderedDict"))
split = 0
for label, fn in PROBES:
    a, b = run(lambda: fn(dict)), run(lambda: fn(OrderedDict))
    split += a != b
    print("%-30s | %-22s | %s" % (label, a, b))
print("갈린 칸 %d / %d" % (split, len(PROBES)))
```

```text
===== python3 - <e43_ordered.py =====
탐침                             | dict                   | OrderedDict
x == 순서만 다른 같은 종류              | True                   | False
x == 순서만 다른 dict               | True                   | True
list(x)                        | ['b', 'a']             | ['b', 'a']
list(reversed(x))              | ['a', 'b']             | ['a', 'b']
x.move_to_end('a') 뒤 list(x)   | AttributeError         | ['b', 'a']
x.popitem(last=False)          | TypeError              | ('a', 1)
x.popitem()                    | ('b', 2)               | ('b', 2)
x | {'c': 3}                   | 'dict'                 | 'OrderedDict'
갈린 칸 4 / 8
(exit 0)
```

```text
                                dict                         OrderedDict
   같은 종류끼리 == (순서만 다름)   True                          ★ False  (순서까지 본다)
   dict 와 ==                     True                          True     (한쪽이 dict 면 순서 안 봄)
   맨 끝으로 옮기기                 없다 (AttributeError)          move_to_end
   맨 앞에서 꺼내기                 popitem() 은 인자가 없다        popitem(last=False)
   삽입 순서 · reversed · popitem()  같다                          같다
```

그림 해설.

* ★★★ **마지막 줄 — `갈린 칸 4 / 8`.** 갈린 넷은 **`==`(같은 종류끼리) · `move_to_end` · `popitem(last=False)` · `|` 의 결과 타입.**
* ★★★ **`OrderedDict` 끼리의 `==` 는 순서를 본다**(`False`), 그런데 **한쪽이 `dict` 면 안 본다**(`True`).
  ★ 문서 — *"Equality tests between OrderedDict objects and other Mapping objects are order-insensitive like regular dictionaries."*
* ★★ **`move_to_end`** — `dict` 에는 **없다**. 문서는 `d[k] = d.pop(k)` 로 **맨 끝**은 흉내 낼 수 있지만 **맨 앞(`last=False`)은 `dict` 에 효율적인 대응이 없다**고 적는다.
  ★ 「최근에 쓴 것을 맨 끝으로」가 **LRU 캐시**의 핵심 동작이다 — 원리는 [자료구조 10번 LRU 캐시](../../../../../data-structure/10-lru-cache/2-summary.md)의 「동작 — 조회」 절이 정본이다.
* ★ **안 갈린 넷** — `dict` 와의 `==` · 삽입 순서 · `reversed`(`dict` 는 3.8+) · 인자 없는 `popitem()`(둘 다 **마지막** 것). `dict` 가 3.7·3.8 에서 **따라잡은 자리**다.

**비용** — 문서의 말로는 `OrderedDict` 가 **재배열에 강하고** `dict` 가 **매핑 연산에 강하다.** ★ 이 문서는 그 차이를 **재지 않았다.**

### 5. ★★ `ChainMap` — 읽기는 겹쳐서, 쓰기는 맨 위에만

**언제 쓰나** — 기본값·사용자 설정·명령줄 인자처럼 **층이 있는 설정**을 합칠 때.

```text
   cm = ChainMap(user, defaults)

   읽기  cm['color']   user ──(없음)──▶ defaults ──▶ 'red'
   쓰기  cm['color'] = 'blue'   ──▶ ★ user 에만 들어간다   (defaults 는 그대로)
   지우기 del cm['size']         ──▶ user 의 size 를 지운다 -> 이제 defaults 의 1 이 보인다
         del cm['size'] 한 번 더 ──▶ ★ user 에 없다 -> KeyError  (defaults 의 것은 안 지운다)
```

```python
# e43_chainmap.py
from collections import ChainMap

defaults = {"color": "red", "size": 1}
user = {"size": 3}
cm = ChainMap(user, defaults)

print("[1] 읽기 :", cm["color"], cm["size"], "· len :", len(cm), "· dict(cm) :", dict(cm))
cm["color"] = "blue"
print("[2] cm['color'] = 'blue' 뒤")
print("    user     :", user)
print("    defaults :", defaults)
try:
    del cm["size"]
    print("[3] del cm['size'] 뒤 cm['size'] :", cm["size"])
    del cm["size"]
except KeyError as exc:
    print("[4] 한 번 더 del ->", type(exc).__name__ + ":", exc)
child = cm.new_child({"size": 99})
print("[5] new_child :", child["size"], "· child.parents['size'] :", child.parents["size"])
defaults["font"] = "mono"
print("[6] defaults 에 넣은 뒤 cm['font'] :", cm["font"])
```

```text
===== python3 - <e43_chainmap.py =====
[1] 읽기 : red 3 · len : 2 · dict(cm) : {'color': 'red', 'size': 3}
[2] cm['color'] = 'blue' 뒤
    user     : {'size': 3, 'color': 'blue'}
    defaults : {'color': 'red', 'size': 1}
[3] del cm['size'] 뒤 cm['size'] : 1
[4] 한 번 더 del -> KeyError: "Key not found in the first mapping: 'size'"
[5] new_child : 99 · child.parents['size'] : 1
[6] defaults 에 넣은 뒤 cm['font'] : mono
(exit 0)
```

* ★★★ **`[2]`** — `cm['color'] = 'blue'` 가 **`user` 에만** 들어갔다. `defaults` 는 **`'red'` 그대로.**
  ★ 문서 — *"writes, updates, and deletions only operate on the first mapping."*
* ★★ **`[3]`·`[4]`** — 첫 `del` 은 `user` 의 `size` 를 지워 **`defaults` 의 `1` 이 드러났고**, 둘째 `del` 은 **`KeyError: "Key not found in the first mapping: 'size'"`** — 보이는 키인데 **못 지운다.**
* ★ **`[6]`** — `defaults` 에 **나중에 넣은 `font`** 가 `cm` 에서 보인다. `ChainMap` 은 **복사가 아니라 참조**다.
* ★ `[5]` — `new_child` 는 **맨 위에 한 장을 더 얹은 새 `ChainMap`**, `parents` 는 **맨 위를 뺀 것**이다.

### 6. ★★ `deque(maxlen=)` — 넘치면 반대편이 밀려 나간다

**언제 쓰나** — 최근 N 개만 들고 있고 싶을 때(`tail` 처럼).

```text
   deque([1, 2, 3], maxlen=3)
   append(4)        [1, 2, 3] + 4      -> 왼쪽 1 이 밀려 나간다   [2, 3, 4]
   appendleft(0)    0 + [2, 3, 4]      -> 오른쪽 4 가 밀려 나간다  [0, 2, 3]
   extend([7, 8])   하나씩 append      -> [3, 7, 8]
   insert(1, 99)    가득 찼다           -> IndexError   (밀어내지 않는다)
   d[1:2]           슬라이스           -> TypeError
```

```python
# e43_deque.py
from collections import deque

d = deque([1, 2, 3], maxlen=3)
print("[1]", d)
d.append(4)
print("[2] append(4)     :", d)
d.appendleft(0)
print("[3] appendleft(0) :", d)
d.extend([7, 8])
print("[4] extend([7, 8]) :", d)
d.rotate(1)
print("[5] rotate(1)     :", d)
print("[6] d[1] :", d[1], "· len :", len(d), "· maxlen :", d.maxlen)
try:
    d.insert(1, 99)
except IndexError as exc:
    print("[7] insert(1, 99) ->", type(exc).__name__ + ":", exc)
try:
    d[1:2]
except TypeError as exc:
    print("[8] d[1:2] ->", type(exc).__name__ + ":", exc)
```

```text
===== python3 - <e43_deque.py =====
[1] deque([1, 2, 3], maxlen=3)
[2] append(4)     : deque([2, 3, 4], maxlen=3)
[3] appendleft(0) : deque([0, 2, 3], maxlen=3)
[4] extend([7, 8]) : deque([3, 7, 8], maxlen=3)
[5] rotate(1)     : deque([8, 3, 7], maxlen=3)
[6] d[1] : 3 · len : 3 · maxlen : 3
[7] insert(1, 99) -> IndexError: deque already at its maximum size
[8] d[1:2] -> TypeError: sequence index must be integer, not 'slice'
(exit 0)
```

* ★★★ **`append` 는 왼쪽을, `appendleft` 는 오른쪽을** 민다 — 문서의 *"a corresponding number of items are discarded from the opposite end"* 그대로다.
* ★★ **`insert` 는 밀어내지 않고 `IndexError: deque already at its maximum size`** — 같은 「넣기」인데 **`append` 계열만** 밀어낸다.
* ★ **`d[1]` 은 되고 `d[1:2]` 는 `TypeError: sequence index must be integer, not 'slice'`** — 인덱스는 되고 **슬라이스는 없다.**
* ★★ **복잡도는 문서의 말이다** — *"approximately the same O(1) performance in either direction"* · *"Indexed access is O(1) at both ends but slows to O(n) in the middle. For fast random access, use lists instead."*
  ★★★ **이 문서는 시간을 재지 않았다** — 「`deque` 가 `list` 보다 빠르다」는 **여기서 나온 말이 아니다.** 원형 배열로 양끝을 O(1) 로 만드는 원리는 [자료구조 04번 큐·덱](../../../../../data-structure/04-queue-deque/2-summary.md)의 「구현 — CircularQueue」 절이 정본이다.

### 7. ★ 다섯 서랍을 한 장에

```text
                  없는 키 d[k]              순서                  고유한 것                        원리의 정본
   dict           KeyError                 삽입 순서 (3.7+)       —                               자료구조 05 해시맵
   defaultdict    ★ factory 를 넣고 돌려준다  삽입 순서               __missing__ 이 쓰기다             —
   Counter        0 (넣지 않는다)           삽입 순서 · 동률도      + - 가 양수만 · total 은 음수까지     —
   OrderedDict    KeyError                 삽입 순서              == 가 순서를 본다 · move_to_end     자료구조 10 LRU
   ChainMap       모든 층에 없으면 KeyError   첫 층 우선             쓰기는 maps[0] 에만                 —
   deque          (매핑이 아니다)            양끝                  maxlen · 양끝 O(1) (문서)          자료구조 04 큐·덱
```

## 문법 — 형태와 규칙

**형태**

```text
from collections import defaultdict, Counter, OrderedDict, ChainMap, deque

d = defaultdict(list)            # factory — 인자 없이 불린다.  defaultdict(None) 이면 보통 dict
c = Counter("hello")             # 이터러블을 센다.  Counter(a=2) · Counter({'a': 2}) 도 된다
c.most_common(2)                 # 많은 순. 동률은 처음 만난 순 (문서 보장)
o = OrderedDict(); o.move_to_end(k, last=False)
cm = ChainMap(user, defaults)    # 앞 매핑이 우선. cm.maps · cm.new_child() · cm.parents
q = deque(maxlen=3)              # append / appendleft / pop / popleft / rotate
```

규칙 열.

1. ★★★ **`defaultdict` 는 `__getitem__` 에서만 factory 를 부르고, 부르면 넣는다** — `get`·`in`·`pop` 은 안 부른다(동작 1 — 5 / 8).
2. ★★★ **`d[k]` 모양이면 읽기처럼 보여도 넣는다** — `if d[k]:` · f-string · `len(d[k])`.
3. ★★ **`Counter[k]` 는 `0` 을 주고 넣지 않는다.**
4. ★★ **`Counter` 의 `+`·`-`·단항 `+` 는 양수만 남긴다** — `subtract`·`total` 은 음수를 남기고 센다.
5. ★★ **`most_common` 의 동률은 처음 만난 순**(문서 보장).
6. ★★ **`OrderedDict` 끼리의 `==` 는 순서를 본다** — 한쪽이 `dict` 면 안 본다.
7. ★★ **`ChainMap` 의 쓰기·지우기는 첫 매핑에만.**
8. ★ **`deque(maxlen=)` 의 `append` 계열은 반대편을 밀고, `insert` 는 `IndexError`.**
9. ★ **복잡도는 문서의 말이다** — 이 문서는 시간을 재지 않았다.

## 어디서 틀리나

### (1) ★★★ `if counts[k]:` 로 「있나」를 검사한다

**키가 생긴다**(동작 1). `k in counts` 또는 `counts.get(k)`.

### (2) ★★★ `defaultdict` 를 순회하면서 `d[이웃]` 을 읽는다

**`RuntimeError`**, 그리고 **예외가 나도 키는 남는다**(동작 2).

### (3) ★★ `defaultdict` 를 그대로 반환해 호출자가 읽는다

**호출자의 읽기가 키를 만든다.** 다 만든 뒤 `dict(d)` 로 넘긴다.

### (4) ★★ `c - d` 로 재고를 빼고 음수를 기대한다

**음수가 사라진다**(동작 3). `subtract` 는 남긴다 — 대신 **`total()` 은 음수까지 더한다.**

### (5) ★★ 「`Counter` 는 `dict` 니까 `==` 도 같다」

**없는 원소를 0 으로 본다**(3.10+) — `Counter(a=1) == Counter(a=1, b=0)` 이 `True`.

### (6) ★★ 「3.7+ 에서 `OrderedDict` 는 쓸모없다」

**`==` 가 순서를 보고, `move_to_end`·`popitem(last=False)` 가 있다**(동작 4 — 4 / 8).

### (7) ★★ `ChainMap` 에 쓰면 기본값이 바뀐다고 믿는다 — 또는 지울 수 있다고 믿는다

**첫 매핑에만** 쓴다. 뒤 층에만 있는 키는 **`KeyError`** 로 못 지운다(동작 5).

### (8) ★ 가득 찬 `deque(maxlen=)` 에 `insert`

**`IndexError`**(동작 6).

### (9) ★★★ 「`deque` 는 `list` 보다 빠르다」

**이 문서는 재지 않았다.** 문서가 말하는 것은 **양끝 O(1) · 가운데 인덱스 O(n)** 이고, **가운데를 자주 보면 `list` 를 쓰라**는 것까지다.

## 구현 세부사항 대 언어 보장

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **라이브러리 보장** | `collections` 문서가 정한 것 | 문서 문장을 열어서 인용 |
| **CPython 구현** | 예외 문구 | 실행 |
| **이 판(3.12.3)의 관찰** | 이 판에서 그랬을 뿐 | 출력 |
| ★ **부적용** | 시간·메모리 | 재지 않았다 — 복잡도는 문서 |

### 라이브러리 보장

| 사실 | 근거 |
|---|---|
| `defaultdict` 는 `__getitem__` 에서만 factory 를 부르고 **넣는다** | `__missing__` 절 |
| `Counter` 는 없는 키에 **`0`**, `KeyError` 를 안 낸다 | `Counter` 절 |
| `Counter` 연산의 결과는 **0 이하를 버린다** | `Counter` 연산 절 |
| `most_common` 동률은 **처음 만난 순** | `most_common` 절 |
| `OrderedDict` 끼리의 `==` 는 **순서를 본다**, 다른 매핑과는 안 본다 | `OrderedDict` 절 |
| `ChainMap` 쓰기·갱신·삭제는 **첫 매핑에만** | `ChainMap` 절 |
| `deque` 양끝 **O(1)**, 가운데 인덱스 **O(n)** | `deque` 절 |

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| `deque` 가득 찬 `insert` 의 문구 **`deque already at its maximum size`** | 실행(동작 6) |
| `ChainMap` 삭제 실패 문구 **`Key not found in the first mapping`** | 실행(동작 5) |

### 그래서 이렇게 적으면 틀린다

* ✗ 「`defaultdict` 는 없는 키에 기본값을 **돌려준다**」\
  ○ **넣고** 돌려준다 — 그래서 `len` 이 는다(5 / 8).
* ✗ 「`most_common` 의 동률 순서는 구현 따라 다르다」\
  ○ **문서가 「처음 만난 순」을 보장한다.**
* ✗ 「`deque` 가 더 빠르다(재 봤다)」\
  ○ **이 문서는 시간을 재지 않았다.** 복잡도는 문서의 말이다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 키마다 리스트로 묶기 | `defaultdict(list)` | 넣기가 한 줄 — **읽을 때는 `get`/`in`** |
| 세기 · 가장 많은 것 | `Counter` | 없는 키가 `0` · `most_common` 동률 보장 |
| 재고처럼 **음수가 신호** | `Counter.subtract` + 직접 검사 | `-` 는 음수를 버린다 |
| 순서까지 같아야 같은 매핑 · 끝으로 옮기기 | `OrderedDict` | `==`·`move_to_end` |
| 설정 층 합치기(읽기 위주) | `ChainMap` | 복사 없이 겹쳐 본다 — 쓰기는 첫 층에만 |
| 최근 N 개 | `deque(maxlen=N)` | 반대편이 밀려 나간다 |
| 가운데를 자주 인덱싱 | `list` | 문서가 그렇게 권한다(`deque` 가운데는 O(n)) |

## 핵심 문장

1. **`defaultdict` 의 `d[k]` 는 쓰기다** — 없는 키면 factory 를 불러 **넣는다.** `if d[k]:`·f-string 까지 전부(5 / 8).
2. **그 쓰기가 순회 중이면 `RuntimeError`** 이고, 예외가 나도 키는 남는다.
3. **`Counter[k]` 는 `0` 을 주고 넣지 않는다** — `+`·`-` 는 양수만 남기고 `total()` 은 음수까지 더한다.
4. **`OrderedDict` 는 `==` 가 순서를 보고 `move_to_end` 가 있다** — 3.7+ 에서도 4 / 8 이 갈렸다.
5. **복잡도는 문서의 말이다** — 이 문서는 시간을 한 번도 재지 않았다.

## 관련 자료

* 선행: [12-dict-and-key-requirements](../12-dict-and-key-requirements/2-summary.md) — ★★★ **경계**: 그 편 동작 6 이 **「`get`·`setdefault`·`defaultdict` 중 어느 것이 키를 만드나」까지**를 보였고 43번을 정본으로 넘겼다.
  여기는 **「`d[...]` 모양의 모든 읽기」·「factory 호출 수」·「순회 중 부작용」** 부터. 순회 중 크기 변경 규칙(동작 5)과 삽입 순서 보장(동작 1)은 그쪽이 정본이다.
* 선행: [10-list-methods-and-sort-key](../10-list-methods-and-sort-key/2-summary.md) — 안정 정렬 보장. `most_common` 동률 순서가 그 위에 선다.
* 원리: [자료구조 04번 — 큐·덱](../../../../../data-structure/04-queue-deque/2-summary.md) — ★ **경계**: 양끝 O(1) 을 만드는 **원형 배열**(「구현 — CircularQueue」 절)은 그쪽,
  여기는 **`deque` API 가 무엇을 하나**만. [자료구조 10번 — LRU 캐시](../../../../../data-structure/10-lru-cache/2-summary.md) — 「동작 — 조회」·「동작 — 추가와 축출」 절이 `move_to_end` 의 쓰임이다.
  [자료구조 05번 — 해시맵](../../../../../data-structure/05-hashmap/2-summary.md) — `dict`·`Counter` 밑의 해시 테이블.
* 이어지는 곳: 목록의 **44번 주제** — [44-itertools](../44-itertools/2-summary.md). `groupby` 는 `defaultdict(list)` 묶기와 **다른 전제**(정렬)를 요구한다.
* 공식 문서: [`collections`](https://docs.python.org/3.12/library/collections.html)

## 용어 풀이

* **`defaultdict`**: 없는 키를 `d[k]` 로 읽으면 `default_factory()` 를 불러 **넣고** 돌려주는 `dict` 하위 클래스.
* **`__missing__`**: `dict.__getitem__` 이 키를 못 찾으면 부르는 메서드. `get`·`in` 은 안 부른다.
* **`Counter`**: 원소 → 개수의 `dict` 하위 클래스. 없는 키는 `0`, 음수·0 도 담는다.
* **다중 집합(multiset)**: 같은 원소가 여러 번 들어갈 수 있는 집합. `Counter` 의 `+`·`-`·`&`·`|` 가 그 연산이고 **양수만** 남긴다.
* **`OrderedDict`**: 순서를 다루는 연산(`move_to_end`·`popitem(last=)`)과 **순서를 보는 `==`** 가 있는 `dict` 하위 클래스.
* **`ChainMap`**: 여러 매핑을 **참조로** 겹쳐 보는 뷰. 읽기는 앞에서부터, 쓰기는 첫 매핑에만.
* **`deque`**(덱, double-ended queue): 양끝에서 넣고 빼는 시퀀스. `maxlen` 을 주면 **길이가 묶인다.**
* **LRU(least recently used)**: 가장 오래 안 쓴 것부터 버리는 캐시 정책. `move_to_end` 로 「방금 쓴 것」을 끝으로 보낸다.

## 더 들어가면

* ★ **`dict` 하위 클래스에 `__missing__` 만 정의**해도 `defaultdict` 와 같은 갈래가 생긴다 — `Counter` 가 바로 그렇게 만들어져 있다(**넣지 않는 쪽**). 이 문서는 직접 하위 클래스를 쓰지는 않았다.
* ★ **`Counter` 의 `&`(교집합 = 최솟값) · `|`(합집합 = 최댓값)** — 문서가 적고, 결과가 **양수만**인 것은 `+`·`-` 와 같다. 이 문서는 `+`·`-` 만 쟀다.
* ★ **스레드와 `deque`** — 문서가 *"thread-safe, memory efficient appends and pops"* 라 적는다. 동시성은 목록의 **53번 주제**에서 다룬다.
