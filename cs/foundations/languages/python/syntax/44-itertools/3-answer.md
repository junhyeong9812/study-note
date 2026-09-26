# python/syntax/44-itertools — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> [1-question.md](1-question.md)의 번호와 **1:1**로 대응한다. 질문 10개 = 답 10개.
>
> 이 파일의 모든 출력은 `python3` **3.12.3** 과 `python3.11` **3.11.15**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> 던지는 형태는 `python3 - <파일` 로 고정했다. ★ **시간·메모리 바이트는 한 번도 재지 않았다.**

## 정답

### 1. 정렬 전 여섯 그룹(`kim` 셋 · `lee` 둘) · 정렬 뒤 세 그룹 — `2 / 3` 대 `0 / 3`

**출력**

```python
# e44_groupby.py
from itertools import groupby

logs = [("kim", 3), ("lee", 1), ("kim", 5), ("park", 2), ("lee", 4), ("kim", 1)]


def user(row):
    return row[0]


def show(title, rows):
    print(title)
    seen = {}
    for key, grp in groupby(rows, key=user):
        items = [n for _, n in grp]
        seen[key] = seen.get(key, 0) + 1
        print("   %-5s %s" % (key, items))
    return seen


a = show("[1] 들어온 순서 그대로", logs)
b = show("[2] sorted(logs, key=user) 뒤", sorted(logs, key=user))
print("[3] 그룹이 둘 이상인 키 : 정렬 전 %d / %d · 정렬 뒤 %d / %d" % (
    sum(v > 1 for v in a.values()), len(a), sum(v > 1 for v in b.values()), len(b)))
```

```text
===== python3 - <e44_groupby.py =====
[1] 들어온 순서 그대로
   kim   [3]
   lee   [1]
   kim   [5]
   park  [2]
   lee   [4]
   kim   [1]
[2] sorted(logs, key=user) 뒤
   kim   [3, 5, 1]
   lee   [1, 4]
   park  [2]
[3] 그룹이 둘 이상인 키 : 정렬 전 2 / 3 · 정렬 뒤 0 / 3
(exit 0)
```

**왜 그런가**

* ★★★ `groupby` 는 **앞 원소와 키가 다를 때마다** 새 그룹을 연다. 입력이 `kim lee kim park lee kim` 이면 **매번 바뀌니** 그룹 여섯.
* ★★ 정렬 뒤에는 같은 키가 **붙어** 있어 세 그룹. `kim` 의 원소가 **`[3, 5, 1]`** 로 입력 순서 그대로인 것은 **안정 정렬**이기 때문이다.
* ★ 에러는 없다 — 정렬을 빠뜨리면 **그룹이 조용히 늘 뿐**이다.

### 2. 모아 둔 짝 셋은 전부 `[]` · `dict(groupby(...))` 도 전부 `[]` · 도는 동안 `list` 로 바꾸면 남는다

**출력**

```python
# e44_group_later.py
from itertools import groupby

rows = sorted(["apple", "avocado", "banana", "blueberry", "cherry"])

pairs = [(k, g) for k, g in groupby(rows, key=lambda w: w[0])]
print("[1] 모아 둔 짝 수 :", len(pairs))
for k, g in pairs:
    print("   ", k, list(g))

print("[2] dict(groupby(...)) 뒤에 읽으면")
d = dict(groupby(rows, key=lambda w: w[0]))
print("   ", {k: list(g) for k, g in d.items()})

print("[3] 도는 동안 list 로")
kept = {k: list(g) for k, g in groupby(rows, key=lambda w: w[0])}
print("   ", kept)
```

```text
===== python3 - <e44_group_later.py =====
[1] 모아 둔 짝 수 : 3
    a []
    b []
    c []
[2] dict(groupby(...)) 뒤에 읽으면
    {'a': [], 'b': [], 'c': []}
[3] 도는 동안 list 로
    {'a': ['apple', 'avocado'], 'b': ['banana', 'blueberry'], 'c': ['cherry']}
(exit 0)
```

**왜 그런가**

* ★★★ 그룹 이터레이터는 **`groupby` 와 원본을 공유**한다. 컴프리헨션이 다음 짝을 받으려고 `groupby` 를 나아가게 하면 **앞 그룹의 원소를 지나쳐** 버린다.
* ★★ **마지막 `c` 까지 빈 이유** — 컴프리헨션은 `c` 짝을 받은 뒤 **「다음 짝이 있나」를 한 번 더 묻는다.** 그 물음에 답하려고 `groupby` 가 **`c` 의 원소를 끝까지 당겨** 보고 끝을 확인했다.
* ★★ `dict(...)` 도 같은 일을 한다 — 짝을 **끝까지 받은 뒤**에 값을 읽으니 전부 `[]`.
* ★ `[3]` 처럼 **도는 동안** `list(g)` 로 바꾸면 전부 남는다.

### 3. 리스트판 `map 10 · filter 10` / 사슬판 만든 직후 `0` · `map 4 · filter 4` · 세로 순서 · `next#3` 은 아무것도 안 부른다 · 다시 돌면 `[]`

**출력**

```python
# e44_lazy.py
from itertools import islice

log = []


def map_fn(x):
    log.append(f"map({x})")
    return x * 10


def keep(y):
    log.append(f"filter({y})")
    return y % 20 == 0


def count(prefix):
    return sum(m.startswith(prefix) for m in log)


print("[1] 리스트로 단계마다 모으면")
log.clear()
mapped = [map_fn(x) for x in range(1, 11)]
kept = [y for y in mapped if keep(y)]
print("    result", kept[:2], "· map", count("map("), "· filter", count("filter("))

print("[2] map · filter · islice")
log.clear()
pipe = islice(filter(keep, map(map_fn, range(1, 11))), 2)
print("    만든 직후 로그", len(log))
print("    result", list(pipe), "· map", count("map("), "· filter", count("filter("))
print("    order ", " ".join(log))

print("[3] 한 번에 next 하나씩")
log.clear()
step = islice(filter(keep, map(map_fn, range(1, 11))), 2)
for i in range(1, 4):
    before = len(log)
    value = next(step, "끝")
    print("    next#%d %-4r 이 호출에서 : %s" % (i, value, " ".join(log[before:]) or "(없음)"))

print("[4] 다 쓴 pipe 를 다시 list 로 :", list(pipe))
```

```text
===== python3 - <e44_lazy.py =====
[1] 리스트로 단계마다 모으면
    result [20, 40] · map 10 · filter 10
[2] map · filter · islice
    만든 직후 로그 0
    result [20, 40] · map 4 · filter 4
    order  map(1) filter(10) map(2) filter(20) map(3) filter(30) map(4) filter(40)
[3] 한 번에 next 하나씩
    next#1 20   이 호출에서 : map(1) filter(10) map(2) filter(20)
    next#2 40   이 호출에서 : map(3) filter(30) map(4) filter(40)
    next#3 '끝'  이 호출에서 : (없음)
[4] 다 쓴 pipe 를 다시 list 로 : []
(exit 0)
```

**왜 그런가**

* ★★★ 리스트 컴프리헨션은 **단계마다 전부** 만든다 — `map` 열 번이 끝난 뒤 `filter` 열 번(가로).
* ★★★ `map`·`filter`·`islice` 는 **만들 때 아무것도 안 부른다**(`0`). `list(pipe)` 가 당기는 대로 **원소 하나씩 세 단계를 통과**한다(세로) — 두 개를 얻는 데 `4 · 4`.
* ★★ `next#3` — `islice(…, 2)` 는 두 개를 준 뒤 **원본을 더 안 당기고** 끝낸다 → `(없음)`, `'끝'`.
* ★ `[4]` — `pipe` 는 이미 소진된 **이터레이터**라 `[]`.

### 4. `a` 가 당긴 다섯을 `b` 가 원본 없이 받는다 · 원본에서 직접 꺼낸 `2` 는 `c`·`d` 둘 다 못 본다

**출력**

```python
# e44_tee.py
from itertools import tee

pulled = []


def source():
    for x in range(1, 6):
        pulled.append(x)
        yield x


a, b = tee(source())
print("[1] a 를 끝까지 :", list(a), "· 원본에서 당긴 수", len(pulled))
print("[2] b 를 끝까지 :", list(b), "· 원본에서 당긴 수", len(pulled))

pulled.clear()
src = source()
c, d = tee(src)
print("[3] c 에서 하나 :", next(c))
print("[4] 원본 src 에서 하나 :", next(src))
print("[5] c 의 나머지 :", list(c), "· d :", list(d))
```

```text
===== python3 - <e44_tee.py =====
[1] a 를 끝까지 : [1, 2, 3, 4, 5] · 원본에서 당긴 수 5
[2] b 를 끝까지 : [1, 2, 3, 4, 5] · 원본에서 당긴 수 5
[3] c 에서 하나 : 1
[4] 원본 src 에서 하나 : 2
[5] c 의 나머지 : [3, 4, 5] · d : [1, 3, 4, 5]
(exit 0)
```

**왜 그런가**

* ★★★ `a` 를 끝까지 돈 뒤 원본 당김 `5`, `b` 를 끝까지 돈 뒤에도 **`5` 그대로** — 그런데 `b` 가 다섯 값을 다 받았다. **`a` 가 당긴 값을 쌓아 둔 것**이다.
* ★★ `tee` 를 만든 뒤 **원본 `src` 에서 직접 `next`** 하면 그 값은 **`tee` 를 거치지 않았으니** 복제본들이 모른다 — `c` 는 `[3, 4, 5]`, `d` 는 `[1, 3, 4, 5]`.

### 5. 3.12 는 `batched` 가 있고 `strict=` 는 `TypeError` / 3.11 은 `batched` 가 없어 둘 다 `AttributeError`

**출력**

```python
# e44_version.py
import itertools
import sys

print("version_info =", sys.version_info[:3])
for name in ["batched", "pairwise", "accumulate", "chain", "groupby"]:
    print("hasattr(itertools, %-12r) : %s" % (name, hasattr(itertools, name)))
try:
    print("list(batched('ABCDEFG', 3)) :", list(itertools.batched("ABCDEFG", 3)))
except AttributeError as exc:
    print("batched ->", type(exc).__name__ + ":", exc)
try:
    list(itertools.batched("ABCDEFG", 3, strict=True))
except (AttributeError, TypeError) as exc:
    print("batched(strict=True) ->", type(exc).__name__ + ":", exc)
```

```text
===== python3 - <e44_version.py =====
version_info = (3, 12, 3)
hasattr(itertools, 'batched'   ) : True
hasattr(itertools, 'pairwise'  ) : True
hasattr(itertools, 'accumulate') : True
hasattr(itertools, 'chain'     ) : True
hasattr(itertools, 'groupby'   ) : True
list(batched('ABCDEFG', 3)) : [('A', 'B', 'C'), ('D', 'E', 'F'), ('G',)]
batched(strict=True) -> TypeError: batched() takes at most 2 arguments (3 given)
(exit 0)
```

```text
===== python3.11 - <e44_version_py311.py =====
version_info = (3, 11, 15)
hasattr(itertools, 'batched'   ) : False
hasattr(itertools, 'pairwise'  ) : True
hasattr(itertools, 'accumulate') : True
hasattr(itertools, 'chain'     ) : True
hasattr(itertools, 'groupby'   ) : True
batched -> AttributeError: module 'itertools' has no attribute 'batched'
batched(strict=True) -> AttributeError: module 'itertools' has no attribute 'batched'
(exit 0)
```

(3.11 블록의 소스는 위와 **한 글자도 같다** — 파일 이름만 `e44_version_py311.py` 다.)

**왜 그런가**

* ★★ `batched` 는 **3.12** 에 들어왔다 — 3.11 은 `hasattr` 이 `False`, 부르면 `AttributeError`.
* ★★ `strict=` 는 **3.13** 에 들어온다(문서) — 3.12 는 **`batched() takes at most 2 arguments (3 given)`** 로 인자 개수에서 거부한다.
* ★ 마지막 묶음 **`('G',)`** 는 짧다 — `strict` 가 없으니 조용히 짧게 낸다. ★ 3.13 의 `strict=True` 가 이것을 `ValueError` 로 만든다는 것은 **문서의 말**이다(못 잰 것).

### 6. 둘째 `list` 는 `[]` · `islice` 두 번은 이어서 · 끝없는 바깥도 앞 여섯 · 음수는 `ValueError`

**출력**

```python
# e44_misc.py
from itertools import chain, count, islice

print("[1] chain 은 한 번 쓰면")
c = chain([1, 2], (3, 4))
print("    첫 list :", list(c), "· 둘째 list :", list(c))

print("[2] 끝없는 원본")
evens = (x for x in count() if x % 2 == 0)
print("    islice(evens, 3)           :", list(islice(evens, 3)))
print("    islice(evens, 3) 한 번 더   :", list(islice(evens, 3)))

print("[3] chain.from_iterable 에 끝없는 바깥")
rows = ([i] * i for i in count(1))
print("    앞 6개 :", list(islice(chain.from_iterable(rows), 6)))

print("[4] 음수 끝")
try:
    islice([1, 2, 3], -1)
except ValueError as exc:
    print("    islice(..., -1) ->", type(exc).__name__ + ":", exc)
```

```text
===== python3 - <e44_misc.py =====
[1] chain 은 한 번 쓰면
    첫 list : [1, 2, 3, 4] · 둘째 list : []
[2] 끝없는 원본
    islice(evens, 3)           : [0, 2, 4]
    islice(evens, 3) 한 번 더   : [6, 8, 10]
[3] chain.from_iterable 에 끝없는 바깥
    앞 6개 : [1, 2, 2, 3, 3, 3]
[4] 음수 끝
    islice(..., -1) -> ValueError: Stop argument for islice() must be None or an integer: 0 <= x <= sys.maxsize.
(exit 0)
```

**왜 그런가**

* ★★ **`[1]`** — `chain` 도 이터레이터다. 한 번 쓰면 끝.
* ★★ **`[2]`** — `islice` 는 **원본을 당겨 간다.** 같은 `evens` 에 두 번 걸면 **이어서** 나온다.
* ★ **`[3]`** — `chain.from_iterable` 은 바깥도 **필요한 만큼만** 당긴다 — 바깥이 끝없어도 된다.
* ★ **`[4]`** — 이터레이터는 길이를 모르니 **끝에서 세는 음수**를 받을 수 없다.

### 7. 키가 바뀌면 끊으니 흩어진 같은 키는 여러 그룹 · 다음으로 가려면 원본을 당기니 앞 그룹이 빈다 — SQL 은 순서와 상관없이 모은다

**왜 그런가**

* ★★★ **「끊는다」** — `groupby` 는 **바로 앞 원소의 키**만 기억한다. 흩어진 `kim` 셋은 **사이에 다른 키가 끼어** 매번 새 그룹이 된다(1번).
* ★★★ **「원본을 공유한다」** — 그룹 이터레이터는 자기 원소를 **따로 들고 있지 않다.** `groupby` 가 다음 키를 찾으려고 원본을 당기면 **그 원소는 앞 그룹에서 사라진다**(2번).
* ★★ **마지막 그룹** — 「다음 키가 있나」를 확인하는 물음이 **마지막 그룹의 원소까지 당긴다.**
* ★ **SQL 의 `GROUP BY`** 는 **입력 순서와 상관없이** 같은 키를 모은다 — 문서가 그 차이를 직접 적고 `groupby` 를 **Unix 의 `uniq`** 에 견준다.

### 8. `['AB', 'AA', 'BA']` — 두 `A` 는 다른 자리라 다른 원소 · `n ** r` · `perm` · `comb` · `comb(n + r - 1, r)`

**출력**

```python
# e44_counts.py
import math
from itertools import combinations, combinations_with_replacement, permutations, product

items = "ABCDE"
n, r = len(items), 3
ROWS = [
    ("product(items, repeat=3)", product(items, repeat=r), n ** r),
    ("permutations(items, 3)", permutations(items, r), math.perm(n, r)),
    ("combinations(items, 3)", combinations(items, r), math.comb(n, r)),
    ("combinations_with_replacement(items, 3)", combinations_with_replacement(items, r), math.comb(n + r - 1, r)),
]
agree = 0
for label, it, formula in ROWS:
    got = sum(1 for _ in it)
    agree += got == formula
    print("%-42s 센 수 %4d · 공식 %4d" % (label, got, formula))
print("공식과 맞은 행 %d / %d" % (agree, len(ROWS)))
print("combinations 앞 셋 :", ["".join(t) for t in list(combinations(items, r))[:3]])
print("combinations('ABA', 2) :", ["".join(t) for t in combinations("ABA", 2)])
```

```text
===== python3 - <e44_counts.py =====
product(items, repeat=3)                   센 수  125 · 공식  125
permutations(items, 3)                     센 수   60 · 공식   60
combinations(items, 3)                     센 수   10 · 공식   10
combinations_with_replacement(items, 3)    센 수   35 · 공식   35
공식과 맞은 행 4 / 4
combinations 앞 셋 : ['ABC', 'ABD', 'ABE']
combinations('ABA', 2) : ['AB', 'AA', 'BA']
(exit 0)
```

**왜 그런가**

* ★★ **`combinations('ABA', 2)`** — 값이 아니라 **자리**로 고른다. 자리 0 의 `A` 와 자리 2 의 `A` 는 **다른 원소**라 `'AB'`(0·1)와 `'BA'`(1·2)가 **둘 다** 나온다.
  ★ 문서 — *"Elements are treated as unique based on their position, not on their value."*
* ★ 개수 대조 — **`공식과 맞은 행 4 / 4`**. `product(…, repeat=r)` 는 `n ** r`, `permutations` 는 `math.perm(n, r)`, `combinations` 는 `math.comb(n, r)`, 중복 조합은 `math.comb(n + r - 1, r)`.

### 9. 보장 · 구현 · 보장 — 「원본 당김 수가 안 늘었는데 값이 나왔다」로 보였다 · 바이트는 안 쟀다

**왜 그런가**

| 사실 | 층 | 근거 |
|---|---|---|
| `groupby` 는 **키가 바뀔 때마다** 새 그룹 | **라이브러리 보장** | `groupby` 절 |
| `batched(strict=True)` 의 **`takes at most 2 arguments`** | **CPython 구현**(문구) | 실행 — 인자를 거부하는 것 자체는 3.12 에 그 인자가 없어서다 |
| `tee` 는 **상당한 보조 저장**이 필요할 수 있다 | **라이브러리 보장** | `tee` 절 |

* ★★★ 「`tee` 가 쌓는다」의 근거는 4번의 **원본 당김 수**다 — `b` 가 다섯 값을 받는 동안 **원본을 한 번도 더 안 당겼다.** 그 값들은 어딘가에 **있어야** 한다.
  ★ **바이트 수·메모리 사용량은 재지 않았다** — 「얼마나 쓰나」는 이 문서가 답하지 않는다.

### 10. 만든 직후 `0` · `4 · 4` · 세로 순서 · `next#3` 빈손이 같다 — 내장 `map`·`filter` · 리스트판을 파이썬에서 직접 · `next` 하나씩이 한 칸 더 / 2번의 빈 그룹 · 6번의 둘째 `list`

**왜 그런가**

* ★★★ [JS 21번](../../../js/syntax/21-iterator-helpers/2-summary.md)의 헬퍼판, [Rust 36번](../../../rust/syntax/36-iterator-adapters-laziness-and-collect/2-summary.md)의 어댑터판, 이 주제의 사슬판이
  **만든 직후 로그 `0` · `map 4 · filter 4` · 원소마다 번갈아 · `next#3` 이 아무것도 안 부름** — 전부 같다. 리스트판·배열판·`Vec` 판은 전부 **`10 · 10`, 가로**.
* ★★ Rust 36번이 이미 **제너레이터 식 + `islice`** 로 파이썬 한 칸을 냈다. 이 주제가 **한 칸 더** 간 것 — **내장 `map`·`filter`**(함수) 로도 같은 로그 · **리스트판(10 · 10)을 파이썬에서 직접** · **`next` 를 하나씩** 불러 「누가 어느 일을 했나」(3번 `[3]`).
* ★★ [16번](../16-iterator-protocol/2-summary.md)의 「소진된 것과 빈 것은 구분되지 않는다」 — **2번의 `[]`**(원래 비었는지 지나쳐서 비었는지 출력으로는 모른다)와
  **6번 `[1]` 의 둘째 `list`**(그리고 3번 `[4]`).

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 정렬 전제 | `python3 - <e44_groupby.py` | 3(캡처 + 재대조 + `PYTHONHASHSEED` 바꾼 재캡처) | **2 / 3 → 0 / 3** |
| 나중에 읽기 | `python3 - <e44_group_later.py` | 3 | 전부 `[]` |
| 게으름 로그 | `python3 - <e44_lazy.py` | 3 | **10 · 10 / 4 · 4** |
| `tee` | `python3 - <e44_tee.py` | 3 | 원본 당김 `5` 그대로 |
| 개수 | `python3 - <e44_counts.py` | 3 | **4 / 4** |
| 판 격자 | `python3 - <e44_version.py` · `python3.11 - <e44_version_py311.py` | 3씩 | 3.11 `AttributeError` · 3.12 `strict` 는 `TypeError` |
| 나머지 | `python3 - <e44_misc.py` | 3 | `[]` · 이어서 · `ValueError` |

**구현 의존 항목** — 판이 오르면 다시 돌려야 하는 것.

| 항목 | 왜 |
|---|---|
| ★ 판 격자 | 3.13 에서 `strict=` 가 들어온다(문서) |
| 예외 **문구** | 구현이다 |

★ **안 흔들리는 칸** — 호출 로그의 수와 순서 · **「2 / 3」·「0 / 3」·「4 / 4」** · 그룹 · `(exit N)`.
★★ **이 주제가 한 번도 안 잰 것** — **시간·메모리 바이트**(부적용) · **3.13**(판 없음 — 못 잰 것).
