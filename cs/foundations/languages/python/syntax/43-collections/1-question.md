# python/syntax/43-collections — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> ★★★ 1번은 **행마다 `len` 전→후와 factory 호출 수**까지 적고 마지막 줄의 숫자를 적는다.
> ★★ 이 주제는 **속도를 묻지 않는다** — 시간을 한 번도 재지 않았다. 복잡도는 문서의 말이다.
>
> 실행 환경: `python3` **3.12.3** · Linux. 던지는 형태는 `python3 - <파일` 로 고정했다.
> ★ 선행 — [12](../12-dict-and-key-requirements/1-question.md)(`dict`·`get`·`setdefault`) · [10](../10-list-methods-and-sort-key/1-question.md)(안정 정렬).

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 새 `defaultdict` 에 조회 여덟 가지 (예측)

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

### 2. ★★★ 이웃의 이웃을 세는 순회 (예측)

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

### 3. ★★ `Counter` 의 빼기·음수·동률 (예측)

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

### 4. ★★ `dict` 와 `OrderedDict` 에 같은 탐침 (예측)

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

### 5. ★★ 겹쳐 본 두 설정 (예측)

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

### 6. ★★ 길이가 묶인 덱 (예측)

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

### 7. ★★ 격자에 factory 호출 수 열이 따로 있는 이유 (왜)

* 1번 격자가 `len` 전→후 말고 **factory 호출 수**를 따로 찍는 이유는? 그 열이 없으면 **무엇을 잘못 읽을 수 있나**?
* 그 열로 확인되는 **문서 문장**은 무엇인가?

### 8. ★★ 보장인가 관찰인가 (경계)

* `Counter("bca" * 2).most_common()` 의 동률 순서는 **문서가 보장하는 것**인가, **이 판에서 그랬을 뿐**인가? 근거 문장은?
* 「`deque` 는 `list` 보다 빠르다」 — 이 문서가 **말할 수 있는 것과 없는 것**을 갈라라.

### 9. 층 가르기 (경계)

* 「`defaultdict` 는 `__getitem__` 에서만 factory 를 부른다」·「`ChainMap` 이 지우기에 실패할 때의 문구」·「`Counter` 끼리의 `==` 가 값이 0 인 원소를 다루는 방식」 —
  각각 **라이브러리 보장 · CPython 구현** 중 어디인가? 셋째는 **몇 판부터**인가?

### 10. 이웃 주제와의 경계 (연결)

* ★ [12번](../12-dict-and-key-requirements/2-summary.md) 동작 6 이 이미 보인 것과 이 주제의 1번이 **새로 보인 것**을 갈라라.
* ★ `move_to_end` 는 [자료구조 10번 LRU 캐시](../../../../../data-structure/10-lru-cache/2-summary.md)의 **어느 동작**에 해당하나? 그 편이 직접 만든 구조는 무엇이고, `OrderedDict` 는 그중 무엇을 대신하나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|---|---|---|---|
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |
