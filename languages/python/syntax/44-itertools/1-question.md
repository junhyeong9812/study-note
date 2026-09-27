# python/syntax/44-itertools — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> ★★★ 3번은 **콜백 로그의 순서와 `next` 마다 한 일**까지 적어야 맞은 것이다.
> ★★ 이 주제는 **속도·메모리 바이트를 묻지 않는다** — 한 번도 재지 않았다.
>
> 실행 환경: `python3` **3.12.3** · Linux(5번은 `python3.11` 3.11.15 도 함께). 던지는 형태는 `python3 - <파일` 로 고정했다.
> ★ 선행 — [16](../16-iterator-protocol/1-question.md)(이터레이터 프로토콜) · [10](../10-list-methods-and-sort-key/1-question.md)(안정 정렬).

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 사용자별로 끊기 — 정렬 전과 뒤 (예측)

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

### 2. ★★★ 모아 둔 그룹을 나중에 읽으면 (예측)

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

### 3. ★★★ 같은 파이프라인 두 벌 (예측)

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

### 4. ★★ 복제한 두 이터레이터와 원본 (예측)

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

### 5. ★★ 한 소스를 두 판에 (예측)

```text
같은 소스를 python3 과 python3.11 에 각각 먹인다. 두 출력을 따로 적는다.
```

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

### 6. ★ 한 번 쓰는 것 · 끝없는 것 · 음수 (예측)

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

### 7. ★★★ `groupby` 가 원소를 다루는 방식 (왜)

* 1번의 정렬 전 결과와 2번의 `[1]`·`[2]` 결과를 **`groupby` 가 무엇을 기억하고 원본을 어떻게 당기는지**로 각각 설명하라.
* 2번에서 **마지막 그룹**의 결과가 그렇게 나온 이유는? 그리고 **SQL 의 `GROUP BY`** 와는 무엇이 다른가?

### 8. ★★ 자리로 고르는 조합 (경계)

* `combinations('ABA', 2)` 는 무엇을 내나 — **값이 같은 `A` 둘**은 어떻게 취급되나?
* `product`·`permutations`·`combinations`·`combinations_with_replacement` 의 개수를 **`math` 로 대조**하면 각각 어느 식인가?

### 9. 층 가르기 (경계)

* 「`groupby` 는 키가 바뀔 때마다 새 그룹」·「`batched(strict=True)` 를 3.12 가 거부할 때의 문구」·「`tee` 는 상당한 보조 저장이 필요할 수 있다」 —
  각각 **라이브러리 보장 · CPython 구현** 중 어디인가?
* ★ 이 문서가 「`tee` 는 메모리에 쌓는다」를 **무엇으로** 보였나 — 무엇은 재지 않았나?

### 10. 이웃 주제와의 경계 (연결)

* ★ [JS 21번](../../../js/syntax/21-iterator-helpers/2-summary.md)·[Rust 36번](../../../rust/syntax/36-iterator-adapters-laziness-and-collect/2-summary.md)과 3번을 나란히 놓으면 **어느 칸이 같고**, 이 주제가 **한 칸 더** 간 것은 무엇인가?
* ★ [16번](../16-iterator-protocol/2-summary.md)의 「소진된 것과 빈 것은 구분되지 않는다」는 이 주제의 **어느 두 블록**에서 다시 나오나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|---|---|---|---|
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |
