# python/syntax/43-collections — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> [1-question.md](1-question.md)의 번호와 **1:1**로 대응한다. 질문 10개 = 답 10개.
>
> 이 파일의 모든 출력은 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> 던지는 형태는 `python3 - <파일` 로 고정했다. ★ **시간은 한 번도 재지 않았다.**

## 정답

### 1. `len 이 늘어난 칸 5 / 8` — `d[...]` 모양 넷과 `setdefault`

**출력**

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

**왜 그런가**

* ★★★ **`d['z']`·`d['z'] += 1`·`if d['z']: …`·`f'{d["z"]}'`** — 넷 다 `__getitem__` 이라 **`__missing__` → factory → 넣기.** `len` 이 `1 → 2`, factory `1`.
  ★ 결과(`0`·`None`·`False`·`'0'`)는 그럴듯한데 **전부 키를 만들었다.**
* ★★ **`setdefault('z', 9)`** 도 `1 → 2` 인데 **factory `0`** — 인자 `9` 를 넣었다.
* ★ **`get`·`in`·`pop(k, None)`** 은 `1 → 1` — `__missing__` 을 안 탄다.
* ★★ **`Counter` 의 `c['z']`** 는 `0` 인데 `len(c)` 는 `1` 그대로, `'z' in c` 는 `False` — **넣지 않는다.**
* ★ **`defaultdict(None)`** 은 보통 `dict` 처럼 **`KeyError: 'z'`**.

### 2. 두 줄 찍고 `RuntimeError` — 그리고 `park` 키가 남는다

**출력**

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

**왜 그런가**

* ★★★ `lee → park` 줄의 `len(follows[friend])` 가 **`follows["park"]` 를 넣었다** — 순회 중에 크기가 `2 → 3`.
  다음 원소로 넘어가려는 순간 **`RuntimeError: dictionary changed size during iteration`**.
* ★★ **예외가 났는데 `park` 는 남았다**(`[3]`). 「읽었을 뿐」인 줄이 **순회 규칙을 밟고, 흔적까지 남긴다.**
* ★ 고치는 법 — `len(follows.get(friend, []))`, 또는 `for user in list(follows):`.

### 3. `-` 는 양수만 · `subtract` 는 음수까지 · `total` 은 `1` · `elements` 는 `['a', 'a']` · 동률은 처음 만난 순 · `Counter` 끼리는 없는 원소를 0 으로

**출력**

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

**왜 그런가**

* ★★★ **`[1]`** — `c - d` 는 **새 `Counter` 에서 0 이하를 버린다** → `{'a': 2}`. `subtract` 는 **제자리에서 음수까지** → `{'a': 2, 'b': -1, 'c': -1}`.
* ★★ **`[2]`** — **담을 때는 음수·0 을 그대로** 담는다. `+f`·`f + Counter()` 는 **양수만**, `total()` 은 **음수까지 더해 `1`**, `elements()` 는 **1 미만을 건너뛴다.**
* ★★ **`[3]`** — 동률 셋의 순서는 **입력에서 처음 만난 순**(`b c a` / `a b c`). **문서 보장**이다(8번).
* ★★ **`[4]`** — `Counter` 는 `dict` 의 하위 클래스(`True`)이고 `dict` 와도 `==` 가 된다. 그런데 **`Counter` 끼리는 `b=0` 을 없는 것과 같게** 본다 — `dict` 끼리는 `False`.

### 4. `갈린 칸 4 / 8` — `==`(같은 종류끼리) · `move_to_end` · `popitem(last=False)` · `|` 의 타입

**출력**

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

**왜 그런가**

* ★★★ **`OrderedDict` 끼리의 `==` 는 순서를 본다**(`False`) — 한쪽이 `dict` 면 안 본다(`True`).
* ★★ `dict` 에는 **`move_to_end` 가 없고**(`AttributeError`), **`popitem` 이 인자를 안 받는다**(`TypeError`).
* ★ `|` 는 **왼쪽 타입을 따른다** — `dict | {...}` 는 `dict`, `OrderedDict | {...}` 는 `OrderedDict`.
* ★ **안 갈린 넷** — `list(x)`·`reversed`·인자 없는 `popitem()`·(`dict` 와의) `==`. 3.7·3.8 에서 `dict` 가 따라잡은 자리다.

### 5. 쓰기는 `user` 에만 · 첫 `del` 은 `defaults` 를 드러내고 둘째 `del` 은 `KeyError` · 나중에 넣은 것도 보인다

**출력**

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

**왜 그런가**

* ★★★ **`[2]`** — 쓰기는 **첫 매핑 `user` 에만.** `defaults` 는 그대로.
* ★★ **`[3]`·`[4]`** — 지우기도 첫 매핑에만. 둘째 `del` 은 `user` 에 `size` 가 없어 **`KeyError: "Key not found in the first mapping: 'size'"`** — `cm['size']` 로는 **보이는데** 못 지운다.
* ★ **`[6]`** — `ChainMap` 은 **참조**라 `defaults` 에 나중에 넣은 `font` 가 보인다.

### 6. `append` 는 왼쪽을, `appendleft` 는 오른쪽을 민다 · `insert` 는 `IndexError` · 슬라이스는 `TypeError`

**출력**

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

**왜 그런가**

* ★★★ 가득 찬 `deque` 에 넣으면 **넣은 쪽의 반대편**이 밀려 나간다 — `[2]`·`[3]`·`[4]`.
* ★★ **`insert` 는 밀어내지 않는다** → `IndexError: deque already at its maximum size`.
* ★ `rotate(1)` 은 오른쪽 끝을 왼쪽으로 한 칸. `d[1]` 은 되고 **`d[1:2]` 는 `TypeError`**.

### 7. `setdefault` 와 `d['z']` — factory 호출 수(`0` / `1`)가 가른다

**왜 그런가**

* ★★ 두 행 모두 **`len` 이 `1 → 2`** 다. 그런데 `setdefault('z', 9)` 는 **factory 를 안 부르고 인자 `9` 를 넣었고**(`0`), `d['z']` 는 **factory 를 불러 `0` 을 넣었다**(`1`).
* ★★★ factory 호출 수를 안 찍었다면 **「`setdefault` 도 `defaultdict` 의 `__missing__` 을 탄다」** 로 잘못 읽었을 것이다. 문서는 **`__getitem__` 에서만** 부른다고 적는다 —
  **`len` 창 하나로는 그 문장을 확인할 수 없고, 둘째 창이 있어야 확인된다.**

### 8. 보장이다 — 「처음 만난 순」 문장 / 문서는 복잡도를 말하고, 이 문서는 시간을 재지 않았다

**왜 그런가**

* ★★★ `most_common` 의 동률 순서는 **문서 보장**이다 — *"Elements with equal counts are ordered in the order first encountered"*. 이 판에서 그렇게 나온 것은 그 보장의 **관찰**일 뿐 근거가 아니다.
* ★★★ `deque` 에 대해 이 문서가 **말할 수 있는 것** — 문서의 복잡도 문장(**양끝 O(1) · 가운데 인덱스 O(n)**)과, `maxlen`·`insert`·슬라이스의 **동작**(실행).
  **말할 수 없는 것** — 「`list` 보다 빠르다」. **시간을 한 번도 재지 않았고**, 복잡도가 같은 자리(예: 끝에 붙이기)에서 어느 쪽이 빠른지는 복잡도로 답이 안 나온다.

### 9. 보장 · 구현 · 보장(3.10+)

**왜 그런가**

| 사실 | 층 | 근거 |
|---|---|---|
| `defaultdict` 는 **`__getitem__` 에서만** factory 를 부른다 | **라이브러리 보장** | `__missing__` 절 — *"not called for any operations besides `__getitem__()`"* |
| 삭제 실패 문구 `Key not found in the first mapping` | **CPython 구현** | 실행 — 문서에 없는 문구 |
| `Counter` 끼리 `==` 는 **없는 원소를 0** 으로 본다 | **라이브러리 보장** | `Counter` 절의 **3.10** 변경 표기 — *"Formerly, `Counter(a=3)` and `Counter(a=3, b=0)` were considered distinct."* |

### 10. 12번은 `get`·`setdefault`·`[]` 세 갈래까지 — 여기는 `[]` 모양의 모든 읽기와 호출 수와 순회 / `move_to_end` 는 「조회」의 「방금 씀으로 옮기기」

**왜 그런가**

* ★★ [12번](../12-dict-and-key-requirements/2-summary.md) 동작 6 은 **「조회만 해도 키가 생긴다 · `get`·`in` 은 안 만든다」** 까지를 보였다.
  이 주제의 1번이 **새로 보인 것** — `+=`·`if d[k]:`·f-string 처럼 **읽기로 보이는 `[]` 전부가 쓰기**라는 것(5 / 8), **factory 호출 수**로 `setdefault` 와 가른 것, 그리고 2번의 **순회 중 부작용.**
* ★★ [자료구조 10번](../../../../../data-structure/10-lru-cache/2-summary.md)은 **해시맵 + 이중 연결 리스트**를 직접 붙여 LRU 를 만든다. 「동작 — 조회」 절의 **`get` 이 그 항목을 맨 뒤(방금 씀)로 옮기는 것**이 `move_to_end(key)` 자리다.
  `OrderedDict` 는 **그 두 구조를 한 객체로** 대신한다 — 키로 찾기(`dict`)와 순서 옮기기(`move_to_end`)·오래된 것 꺼내기(`popitem(last=False)`).
  ★ 그 편은 이것을 **「읽기처럼 보이는 쓰기」** 라 불렀다 — 이 주제의 `defaultdict` 와 **같은 말**이다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 조회 격자 | `python3 - <e43_lookup.py` | 3(캡처 + 재대조 + `PYTHONHASHSEED` 바꾼 재캡처) | **5 / 8** |
| 순회 중 부작용 | `python3 - <e43_iterate.py` | 3 | `RuntimeError` · 키가 남는다 |
| `Counter` | `python3 - <e43_counter.py` | 3 | 양수만 / 음수까지 / 동률은 처음 만난 순 |
| `dict` 대 `OrderedDict` | `python3 - <e43_ordered.py` | 3 | **4 / 8** |
| `ChainMap` · `deque` | `python3 - <e43_chainmap.py` · `<e43_deque.py` | 3씩 | 첫 매핑에만 · 반대편을 민다 |

**구현 의존 항목** — 판이 오르면 다시 돌려야 하는 것.

| 항목 | 왜 |
|---|---|
| 예외 **문구** | 구현이다 |

★ **안 흔들리는 칸** — 격자 칸 · **「5 / 8」·「4 / 8」** · `len` 전→후 · factory 호출 수 · `(exit N)`.
★★ **이 주제가 한 번도 안 잰 것** — **시간·메모리**(부적용). 복잡도는 전부 문서 문장이다.
