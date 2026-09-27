# python/syntax/44-itertools — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만(문서 원본 `.rst` 를 받아 문장을 찾았다).
> - [`itertools`(3.12)](https://docs.python.org/3.12/library/itertools.html) —
>   `groupby` 의 *"Generally, the iterable needs to already be sorted on the same key function"* · *"It generates a break or new group every time the value of the key function changes"* ·
>   *"That behavior differs from SQL's GROUP BY which aggregates common elements regardless of their input order"* ·
>   *"when the `groupby()` object is advanced, the previous group is no longer visible"* ·
>   `tee` 의 *"This itertool may require significant auxiliary storage"* 와 파이썬으로 적은 동등 코드
> - `combinations`·`permutations` 의 *"Elements are treated as unique based on their position, not on their value"*
> - [`itertools`(3.13)](https://docs.python.org/3.13/library/itertools.html) — `batched` 의 *"versionadded 3.12"* · *"versionchanged 3.13: Added the strict option"*. ★ **3.13 은 이 머신에 없다.**
>
> **실행 검증** — 이 문서에 실린 출력은 전부 이 머신에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.\
> 판은 `python3` **3.12.3** 이 본판이고, 판 경계를 위해 `python3.11` **3.11.15** 로 한 블록을 더 던졌다.\
> ★★★ **이 문서가 잰 것은 「원본을 당긴 수」·「콜백 호출 수」·「그룹 수」·「개수」뿐이다** — 시간·메모리는 한 번도 재지 않았다.
> `tee` 가 「메모리에 쌓는다」는 것도 **바이트가 아니라 「원본을 다시 안 당겼는데 값이 나온다」로** 보였다.\
> **버전**(문서의 `versionadded` 표기) — `combinations_with_replacement` **3.1**, `pairwise` **3.10**, `batched` **3.12**, `batched(strict=)` **3.13**. 이 문서가 쓴 나머지(`chain`·`islice`·`groupby`·`tee`·`product`·`combinations`·`permutations`)는 3.12 문서에 추가 판 표기가 없다.\
> ★ **구현 대 언어 보장 한 줄** — 위 문서 문장들과 **「이터레이터를 돌려준다」** 가 보장이고, 예외 **문구**는 CPython 의 것이다.\
> ★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다 | 안 흔들린다(근거로 써도 되는 칸) |
> |---|---|
> | 판이 오르면 예외 **문구**(`batched(strict=True)` 가 3.13 에서 받아들여질 것 — 문서) | ★★ 호출 로그의 **수와 순서** · 마지막 줄 **「… N / M」** |
> | — (주소·시간·`set` 출력을 한 곳도 안 찍었다) | 그룹의 키와 원소 · 개수 |
>
> **선행** — [16-iterator-protocol](../16-iterator-protocol/2-summary.md)(★★★ **`itertools` 는 전부 이터레이터를 돌려준다 — 한 번 쓰면 끝이고, 소진된 것과 빈 것은 구분되지 않는다**) ·
> [10-list-methods-and-sort-key](../10-list-methods-and-sort-key/2-summary.md)(★★ **`groupby` 앞의 정렬 — 안정 정렬 보장**) ·
> [15-generator-expressions-lazy-eval](../15-generator-expressions-lazy-eval/2-summary.md)(게으른 평가).

## 한눈에 — 쉽게 말하면

**`itertools` 는 「컨베이어 벨트 부품 상자」다.** 벨트(이터레이터) 위로 물건이 **하나씩** 흘러오고, 부품은 **흘러오는 대로** 처리한다 — 창고에 쌓아 두지 않는다.

* `chain` — 벨트 둘을 **이어 붙인다.** `islice` — **앞의 몇 개만** 흘려보내고 멈춘다.
* `product`·`combinations`·`permutations` — 조합을 **하나씩** 만들어 흘린다.
* ★ **`groupby` 는 「옆에 붙은 같은 것」만** 한 상자에 담는다 — 벨트가 **정렬돼 있지 않으면** 같은 물건이 여러 상자로 나뉜다.
* ★ `tee` 는 벨트를 **둘로 복제**하는데, 한쪽이 앞서 가면 **뒤처진 쪽을 위해 창고에 쌓는다.**

```text
   입력 벨트  kim lee kim park lee kim           정렬 뒤  kim kim kim lee lee park
   groupby    [kim][lee][kim][park][lee][kim]              [kim kim kim][lee lee][park]
              ★ 키가 바뀔 때마다 새 상자                       ★ 같은 키가 붙어 있어 한 상자

   SQL GROUP BY 는 순서와 상관없이 모은다 — groupby 는 Unix 의 uniq 와 같다 (문서)
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 컨베이어 벨트 | 이터레이터 | 한 번 흘러간 것은 다시 안 온다 |
| 흘러오는 대로 처리하는 부품 | `itertools` 의 함수들 | 만든 직후 **콜백 호출 0** |
| 옆에 붙은 같은 것만 한 상자 | `groupby` | 정렬 전 **같은 키가 여러 그룹** |
| ★ 다음 상자로 넘어가면 앞 상자가 빈다 | 그룹 이터레이터가 **원본을 공유** | 모아 두고 나중에 읽으면 `[]` |
| 복제 벨트와 창고 | `tee` | 한쪽이 앞서 가도 다른 쪽이 **원본을 다시 안 당기고** 전부 받는다 |
| 앞의 몇 개만 | `islice` | 필요한 만큼만 원본을 당긴다 |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.\
「**로그를 사용자별로 `groupby` 했는데 같은 사용자가 세 번 나온다**」와
「**`groupby` 결과를 `dict(...)` 로 만들어 뒀더니 값이 전부 비어 있다**」가 그것이다.\
앞엣것은 **벨트를 정렬하지 않은 것**이고, 뒤엣것은 **상자를 다음으로 넘긴 뒤에 열어 본 것**이다.

> **이터레이터(iterator)** — `next()` 로 값을 **하나씩** 꺼내는 객체. 다 꺼내면 끝이다.\
> 예: `list(c)` 를 두 번 하면 두 번째는 `[]`([16번](../16-iterator-protocol/2-summary.md)).

> **게으른 평가(lazy evaluation)** — 값이 **필요할 때** 계산하는 것.\
> 예: `map(f, …)` 는 만들 때 `f` 를 한 번도 안 부른다.

### ★★ 이 주제가 쓰는 창 / 부적용인 창

**본체는 ① 「groupby 가 정렬을 전제한다」 재현 창이다.** 같은 데이터를 **정렬 전 / 정렬 뒤**로 넣어 **그룹이 둘 이상인 키를 스크립트가 센다.**
그리고 ② **호출 로그**(콜백이 부를 때마다 한 줄)가 게으름과 `tee` 의 저장을 보인다.

| 창 | 무엇을 말해 주나 | 못 보는 것 |
|---|---|---|
| ① ★★★ **정렬 전 / 뒤 그룹 수** | `groupby` 가 **어디서 끊나** | — |
| ② ★★★ **호출 로그**(콜백·원본 당김) | **언제 · 몇 번 · 어떤 순서로** 일하나 | 시간 |
| ③ ★★ **「나중에 읽기」 창** | 그룹 이터레이터가 **언제 비나** | — |
| ④ ★ **`math.comb`·`math.perm` 대조** | 조합 함수의 **개수** | — |
| ⑤ ★ **판 격자**(3.11 대 3.12) | `batched` 가 **몇 판부터** 있나 | 3.13 의 `strict` |
| ★ **못 잰 것** — 3.13 의 `batched(strict=True)` | — | ★★★ 이 머신에 3.13 이 없다([41번](../41-typing-and-generic-syntax/2-summary.md) 첫 블록) |
| ★ **부적용인 창** — 시간 · 메모리 바이트 | — | 「`islice` 가 빠르다」·「`tee` 가 N 바이트 쓴다」를 **한 번도 재지 않았다** |

★★ **②가 이 주제의 네 번째 창이다.** 값 창(결과 리스트)만 보면 **리스트판과 이터레이터판이 같은 `[20, 40]`** 을 낸다.
**콜백이 부를 때마다 한 줄을 남기면** 「같은 값을 **다른 양의 일**로 얻었다」가 드러난다 — [JS 21번](../../../js/syntax/21-iterator-helpers/2-summary.md)·[Rust 36번](../../../rust/syntax/36-iterator-adapters-laziness-and-collect/2-summary.md)이 쓴 **같은 창**이다.

## 이 주제가 답하려는 질문

1. ★★★ **`groupby` 는 왜 정렬을 전제하나** — 정렬 안 한 입력에서 **같은 키가 몇 그룹으로** 나뉘나. 그리고 **그룹을 나중에 읽으면** 왜 비나.
2. ★★ **`itertools` 사슬은 일을 얼마나 하나** — 리스트로 단계마다 모으는 판과 `map`·`filter`·`islice` 판의 **호출 수**. JS·Rust 와 같은 표가 나오나.
3. **`tee`·조합 함수·`batched` 는 무엇을 대가로 무엇을 주나** — 저장 · 개수 · 판.

★ 첫째가 이 주제의 인출 목표다.
**「`groupby` 는 모으는 것이 아니라 끊는 것」이라는 한 문장으로 두 함정(정렬 · 나중에 읽기)을 설명할 수 있는 것**이 아는 것과 들은 것의 경계다.

## 동작 방식

> 이 절이 본문이다. 그림이 먼저 오고 문장이 그 그림을 읽어 준다.

### 1. ★★★ `groupby` 는 끊는다 — 정렬하지 않으면 같은 키가 여러 그룹

**언제 쓰나** — 「키별로 묶기」를 `groupby` 로 짤 때.

```text
   groupby 가 하는 일 — 앞 원소의 키와 지금 원소의 키가 다르면 "끊는다". 그게 전부다

   입력      (kim,3) (lee,1) (kim,5) (park,2) (lee,4) (kim,1)
   키        kim  ≠  lee  ≠  kim  ≠  park  ≠  lee  ≠  kim         -> 끊기 5번 -> 그룹 6개
                                                                   kim 이 3 그룹, lee 가 2 그룹
   sorted    (kim,3) (kim,5) (kim,1) (lee,1) (lee,4) (park,2)
   키        kim = kim = kim  ≠  lee = lee  ≠  park                -> 끊기 2번 -> 그룹 3개
                  ★ 원래 순서 3, 5, 1 이 그대로 — 안정 정렬 (10번)
```

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

그림 해설.

* ★★★ **`[3]` — 그룹이 둘 이상인 키 : 정렬 전 `2 / 3` · 정렬 뒤 `0 / 3`.** 정렬 전에는 **`kim` 이 세 그룹, `lee` 가 두 그룹**으로 나뉘었다.
  ★ 문서 — *"It generates a break or new group every time the value of the key function changes … That behavior differs from SQL's GROUP BY which aggregates common elements regardless of their input order."*
* ★★ **정렬 뒤 `kim` 의 원소가 `[3, 5, 1]`** — 입력에서의 순서 그대로다. `sorted` 가 **안정 정렬**이라 같은 키 안의 순서를 안 바꾼다([10번](../10-list-methods-and-sort-key/2-summary.md) 동작 3 — 언어 보장).
* ★ **정렬의 `key` 와 `groupby` 의 `key` 가 같은 함수(`user`)** 다. 다른 키로 정렬하면 다시 흩어진다 — 문서가 *"sorted on the same key function"* 이라 적는 이유.
* ★★ **에러가 없다.** 정렬을 빠뜨린 `groupby` 는 **그럴듯한 그룹을 조용히 더 많이** 낸다 — 이 주제의 조용한 실패다.

**비용** — 정렬이 **전체를 한 번 모은다**(게으름이 깨진다). 「순서 상관없이 모으기」가 목적이면 `groupby` 보다 **`defaultdict(list)`**([43번](../43-collections/2-summary.md))가 맞다.

### 2. ★★★ 그룹 이터레이터는 다음 그룹으로 넘어가면 빈다

**언제 쓰나** — `groupby` 결과를 **리스트·`dict` 로 모아 두고** 나중에 쓸 때.

```text
   groupby 객체 ──(원본 이터레이터를 하나 들고 있다)──▶ rows
       │
       ├─ ('a', 그룹 a) ─┐
       ├─ ('b', 그룹 b) ─┤   ★ 세 그룹이 전부 같은 원본을 공유한다
       └─ ('c', 그룹 c) ─┘
   다음 키로 가려면 원본을 당겨야 한다 -> 앞 그룹의 원소를 지나쳐 버린다 -> 앞 그룹은 빈다
   마지막 그룹도 — 「다음 키가 있나」를 보려고 원본을 끝까지 당겼으니 빈다
```

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

그림 해설.

* ★★★ **`[1]`** — 짝을 **3개** 모았는데 나중에 `list(g)` 를 하니 **셋 다 `[]`** 다. **마지막 그룹 `c` 까지** 비었다.
  ★ 문서 — *"when the `groupby()` object is advanced, the previous group is no longer visible. So, if that data is needed later, it should be stored as a list."*
* ★★★ **`[2]`** — `dict(groupby(...))` 도 **값이 전부 `[]`** — `dict` 가 짝을 받으며 `groupby` 를 **끝까지 돌렸기** 때문이다. 이것이 흔히 밟는 모양이다.
* ★★ **`[3]`** — **도는 동안** `list(g)` 로 바꾸면 전부 남는다. 고치는 법은 이 한 줄이다.
* ★ 에러가 없다 — **빈 리스트는 「원래 없었다」와 구분되지 않는다**([16번](../16-iterator-protocol/2-summary.md) 동작 6 「소진된 것과 빈 것은 구분되지 않는다」의 한 사례).

**비용** — 그룹을 원본과 공유하는 덕에 `groupby` 는 **그룹을 복사하지 않는다.** 대가가 이 함정이다.

### 3. ★★★ 게으름 로그 — JS 21 · Rust 36 과 같은 파이프라인

**언제 쓰나** — 「이 사슬이 **일을 얼마나 하나**」를 물을 때.

원본 `1..10`, `map` 은 `x * 10`, `filter` 는 **20 의 배수만**, **앞의 두 개**. [JS 21번](../../../js/syntax/21-iterator-helpers/2-summary.md)과 [Rust 36번](../../../rust/syntax/36-iterator-adapters-laziness-and-collect/2-summary.md)이 쓴 **같은 파이프라인**이다.

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

```text
   리스트판   map(1) … map(10) │ filter(10) … filter(100) │ [:2]      <- 단계별(가로) 10 · 10
   itertools  (만든 순간 0)  map(1) filter(10) map(2) filter(20) │ map(3) filter(30) map(4) filter(40) │ 끝
                              └──────── next#1 ───────────────┘ └──────── next#2 ───────────────┘  next#3: (없음)
```

그림 해설.

* ★★★ **`[1]` 리스트판은 `map 10 · filter 10`**, **`[2]` `map`·`filter`·`islice` 판은 만든 직후 `0`, 끝나고 `map 4 · filter 4`**, 순서는 **원소마다 번갈아.**
* ★★★ **`[3]`** — `next#1` 이 `map(1) filter(10) map(2) filter(20)` 을, `next#2` 가 `map(3) … filter(40)` 을 했고 **`next#3` 은 콜백을 하나도 안 부르고 끝났다.**
  `islice(…, 2)` 가 두 개를 준 뒤 **원본을 더 안 당겼다** — 그래서 `map(5)` 가 영영 없다.
* ★★ **`[4]`** — 다 쓴 `pipe` 를 다시 `list` 로 하면 **`[]`**. `islice` 가 돌려준 것도 **이터레이터**다([16번](../16-iterator-protocol/2-summary.md)).

**세 언어를 나란히.**

| | JS 배열 메서드 | JS 이터레이터 헬퍼 | Rust 단계마다 `Vec` | Rust 어댑터 사슬 | Python 리스트 | ★ Python `map`·`filter`·`islice` |
|---|---|---|---|---|---|---|
| 만든 직후 로그 | — | **0** | — | **0** | — | **0** |
| `map` 호출 | 10 | **4** | 10 | **4** | 10 | **4** |
| `filter` 호출 | 10 | **4** | 10 | **4** | 10 | **4** |
| 순서 | 가로 | 세로 | 가로 | 세로 | 가로 | 세로 |
| `next#3` 이 한 일 | — | (none) | — | (none) | — | (없음) |

* ★★★ **여섯 칸의 수와 순서가 같다.** JS·Rust 쪽 수치는 **그 편의 블록을 인용**했다 — 이 문서는 브라우저·`rustc` 를 다시 돌리지 않았다.
* ★★ [Rust 36번](../../../rust/syntax/36-iterator-adapters-laziness-and-collect/2-summary.md)은 이미 **파이썬 제너레이터 식 + `islice`** 로 같은 로그를 냈다. 여기서 **한 칸 더** 간 것은
  **내장 `map`·`filter`**(제너레이터 식이 아니라 함수)로 같은 로그가 나온다는 것과, **리스트판(10 · 10)을 파이썬에서 직접** 찍은 것, 그리고 **`next` 를 하나씩** 부른 `[3]` 이다.

**비용** — 게으른 사슬은 **한 번만** 돈다(`[4]`). 두 번 써야 하면 `list` 로 한 번 물질화하거나 `tee`(동작 4).

### 4. ★★ `tee` — 복제 벨트는 창고에 쌓는다

**언제 쓰나** — 한 이터레이터를 **두 곳에서** 읽어야 할 때.

```text
   source() ── tee ──┬── a : 끝까지 당긴다   원본 당김 1 2 3 4 5   (5)
                    │         └─ 당긴 값을 b 를 위해 쌓아 둔다  [1 2 3 4 5]
                    └── b : 끝까지         ★ 원본을 다시 안 당긴다 (5 그대로) — 창고에서 꺼낸다

   c, d = tee(src)  뒤에  next(src)  ──▶  ★ 원본을 직접 당기면 c·d 둘 다 그 값을 못 본다
```

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

* ★★★ **`[1]`·`[2]`** — `a` 를 끝까지 돈 뒤 **원본에서 당긴 수 `5`**, `b` 를 끝까지 돌고도 **`5` 그대로.** 그런데 `b` 는 **다섯 값을 전부** 받았다 —
  **`a` 가 당긴 값을 `b` 를 위해 쌓아 둔 것**이다. ★ 문서 — *"This itertool may require significant auxiliary storage"* · *"if one iterator uses most or all of the data before another iterator starts, it is faster to use `list()` instead of `tee()`."*
  ★★ **이 문서는 바이트를 재지 않았다** — 「쌓는다」의 근거는 **「원본을 다시 안 당겼는데 값이 나왔다」** 라는 **호출 수**다.
* ★★ **`[3]`~`[5]`** — `tee` 를 만든 뒤 **원본 `src` 에서 직접** `next` 하면 그 값(`2`)은 **`c` 도 `d` 도 못 본다** — `c` 는 `[3, 4, 5]`, `d` 는 `[1, 3, 4, 5]`.
  **`tee` 뒤에는 원본을 건드리지 않는다.**

### 5. ★ 조합 함수의 개수 — `math` 로 대조

```text
   items = A B C D E (n = 5),  r = 3

   product(repeat=3)                  A A A, A A B, …     순서 O · 중복 O    -> n ** r
   permutations(3)                    A B C, A C B, …     순서 O · 중복 X    -> math.perm(n, r)
   combinations(3)                    A B C, A B D, …     순서 X · 중복 X    -> math.comb(n, r)
   combinations_with_replacement(3)   A A A, A A B, …     순서 X · 중복 O    -> math.comb(n + r - 1, r)

   ★ "중복" 은 값이 아니라 자리의 중복이다 — 'ABA' 의 두 A 는 다른 자리
```

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

* ★ **`공식과 맞은 행 4 / 4`** — `product` 는 `n ** r`, `permutations` 는 `math.perm`, `combinations` 는 `math.comb`, 중복 조합은 `math.comb(n + r - 1, r)`.
* ★★ **`combinations('ABA', 2)` 는 `['AB', 'AA', 'BA']`** — **값이 아니라 자리**로 고른다. 같은 `A` 가 두 자리에 있으면 **중복 없는 조합이 아니다.**
  ★ 문서 — *"Elements are treated as unique based on their position, not on their value."*
* ★ `combinations` 는 **입력 순서를 지킨 사전순**으로 나온다(`ABC`·`ABD`·`ABE` …).

### 6. ★★ 판 격자 — `batched` 는 3.12, `strict` 는 3.13

```text
   batched('ABCDEFG', 3)     A B C │ D E F │ G         마지막 묶음이 짧다 -> ('G',)
                             ───── ─────  ─
   strict=True  (3.13, 문서)  짧은 마지막 묶음에서 ValueError 로 바뀐다   ★ 이 머신에서 못 잰 것
   3.12 에 strict= 를 주면     인자 개수에서 거부 (TypeError)
   3.11                      batched 자체가 없다 (AttributeError)
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

| | 3.11 | 3.12 | ★ 3.13 |
|---|---|---|---|
| `itertools.batched` | ★ **`AttributeError`** | 있다 | 있다(문서) |
| `batched(…, strict=True)` | — | ★ **`TypeError`**(인자 셋) | ★ 된다(문서 — *"Added the strict option"*) |
| `pairwise` | 있다(3.10+) | 있다 | 있다 |
| **근거** | 실측 | 실측 | ★★ **문서만** |

* ★★ 3.12 의 **`batched() takes at most 2 arguments (3 given)`** — 3.13 에서 받아들여질 인자를 3.12 가 **개수로** 거부한다.
* ★ 마지막 묶음 `('G',)` 가 **짧게** 나왔다 — `strict` 가 없는 판에서는 **조용히 짧은 묶음**을 낸다.

### 7. ★ 한 번 쓰면 끝 · 끝없는 원본 · 음수

```text
   evens = 0 2 4 6 8 10 12 …        (끝없는 원본)
   islice(evens, 3)   당긴다 ─▶ 0 2 4        evens 의 자리는 이제 6 앞
   islice(evens, 3)   당긴다 ─▶ 6 8 10       ★ 처음부터가 아니라 이어서
   islice(…, -1)      끝에서 하나 빼기 = 끝을 알아야 한다 -> 이터레이터는 모른다 -> ValueError
```

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

* ★★ **`[1]`** — `chain` 의 두 번째 `list` 는 **`[]`**([16번](../16-iterator-protocol/2-summary.md)).
* ★★ **`[2]`** — 같은 `evens` 에 `islice` 를 두 번 걸면 **이어서** 나온다(`[0, 2, 4]` → `[6, 8, 10]`). `islice` 는 **원본을 당겨 간다.**
* ★ **`[3]`** — 바깥이 **끝없는** `chain.from_iterable` 도 `islice` 로 끊으면 된다 — 바깥을 **필요한 만큼만** 당긴다.
* ★ **`[4]`** — `islice` 는 **음수를 안 받는다**(`ValueError`). 끝에서 세려면 **길이를 알아야** 하는데 이터레이터는 모른다.

## 문법 — 형태와 규칙

**형태**

```text
from itertools import chain, islice, groupby, tee, product, combinations, permutations, batched

chain(a, b)                      # 이어 붙이기.  chain.from_iterable(바깥) — 바깥도 게으르게
islice(it, stop) / (it, start, stop, step)   # 음수 불가
groupby(sorted(xs, key=k), key=k)            # ★ 같은 key 로 먼저 정렬
{k: list(g) for k, g in groupby(...)}        # ★ 도는 동안 list 로
a, b = tee(it)                   # 뒤에 it 를 직접 쓰지 않는다
product(xs, repeat=r) · permutations(xs, r) · combinations(xs, r)
batched(xs, n)                   # 3.12+.  strict= 는 3.13+
```

규칙 열.

1. ★★★ **`itertools` 는 이터레이터를 돌려준다** — 만들 때 일을 안 하고, **한 번 쓰면 끝**이다.
2. ★★★ **`groupby` 는 키가 바뀔 때 끊는다** — 모으지 않는다. **같은 키로 먼저 정렬**한다(정렬 전 2 / 3 · 뒤 0 / 3).
3. ★★★ **그룹 이터레이터는 원본을 공유한다** — 다음 그룹으로 가면 앞 그룹이 빈다. **도는 동안 `list` 로.**
4. ★★ **`islice` 는 필요한 만큼만 원본을 당긴다** — 리스트판 10 · 10, 사슬판 4 · 4.
5. ★★ **`tee` 는 앞서 간 쪽이 당긴 값을 쌓는다** — 한쪽이 거의 다 쓴 뒤 다른 쪽이 시작하면 `list` 가 낫다(문서).
6. ★ **`combinations` 는 자리로 고른다** — 값이 같아도 다른 자리면 다른 원소.
7. ★ **`batched` 는 3.12+** — 3.11 에서 `AttributeError`.

## 어디서 틀리나

### (1) ★★★ 정렬 없이 `groupby` 로 키별 합계를 낸다

**같은 키가 여러 그룹**으로 나와 합계가 쪼개진다(동작 1). 에러가 없다.

### (2) ★★★ `dict(groupby(...))` 로 묶어 둔다

**값이 전부 `[]`**(동작 2). `{k: list(g) for k, g in groupby(...)}`.

### (3) ★★ 정렬 키와 `groupby` 키가 다르다

다시 흩어진다 — 문서의 *"on the same key function"*.

### (4) ★★ `itertools` 결과를 두 번 돈다

두 번째는 **`[]`**(동작 3 의 `[4]`, 동작 7 의 `[1]`).

### (5) ★★ `tee` 뒤에 원본을 계속 쓴다

**그 값은 복제본들이 못 본다**(동작 4).

### (6) ★★ `tee` 를 「공짜 복제」로 안다

**앞서 간 만큼 쌓는다**(동작 4) — 한쪽이 거의 다 쓴 뒤 다른 쪽을 쓰면 `list` 와 다를 바 없다(문서).

### (7) ★ `combinations` 로 「서로 다른 값의 조합」을 기대한다

**자리로 고른다** — `'ABA'` 에서 `'AB'`·`'BA'` 가 둘 다 나온다(동작 5).

### (8) ★ `islice(it, -1)` 로 마지막을 뺀다

**`ValueError`**(동작 7).

### (9) ★ 3.11 코드에서 `batched` 를 쓴다

**`AttributeError`**(동작 6). 3.12 에서도 **`strict=` 는 `TypeError`**.

## 구현 세부사항 대 언어 보장

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **라이브러리 보장** | `itertools` 문서가 정한 것 | 문서 문장을 열어서 인용 |
| **CPython 구현** | 예외 문구 | 실행 |
| **이 판(3.12.3 · 3.11.15)의 관찰** | 이 판에서 그랬을 뿐 | 출력 |
| ★ **못 잰 것** | 3.13 의 `strict` | 판이 없다 |
| ★ **부적용** | 시간·메모리 바이트 | 재지 않았다 |

### 라이브러리 보장

| 사실 | 근거 |
|---|---|
| `groupby` 는 키가 **바뀔 때마다** 새 그룹 — SQL `GROUP BY` 와 다르다 | `groupby` 절 |
| 앞 그룹은 `groupby` 가 **나아가면 안 보인다** | `groupby` 절 |
| `tee` 는 **상당한 보조 저장**이 필요할 수 있다 | `tee` 절 |
| `batched` **3.12**, `strict` **3.13** | `batched` 절(3.13 문서) |

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| `batched(strict=True)` 가 3.12 에서 **`takes at most 2 arguments`** | 실행(동작 6) |
| `islice` 음수의 **문구** | 실행(동작 7) |

### 그래서 이렇게 적으면 틀린다

* ✗ 「`groupby` 는 같은 키를 모은다」\
  ○ **옆에 붙은 같은 키만** 모은다 — 정렬 전 `kim` 이 세 그룹이었다.
* ✗ 「`tee` 는 메모리를 N 바이트 쓴다(재 봤다)」\
  ○ **바이트는 재지 않았다.** 잰 것은 **원본 당김 수**다.
* ✗ 「`islice` 가 리스트 슬라이스보다 빠르다」\
  ○ **시간은 재지 않았다.** 잰 것은 **콜백 호출 수(4 대 10)** 다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 이미 정렬된 스트림을 키별로 끊기 | `groupby` | 모으지 않고 흘려보낸다 |
| 순서 상관없이 키별로 모으기 | `defaultdict(list)`([43번](../43-collections/2-summary.md)) | `groupby` 는 정렬을 요구한다 |
| 앞의 몇 개만 | `islice` | 필요한 만큼만 당긴다(4 · 4) |
| 두 곳에서 읽기 — 나란히 진행 | `tee` | 쌓는 양이 작다 |
| 두 곳에서 읽기 — 한쪽이 다 쓴 뒤 | `list` | 문서가 그렇게 권한다 |
| 조합·순열 | `combinations`·`permutations`·`product` | 개수는 `math.comb`·`math.perm` 과 같다 |
| 묶음 단위 처리 | `batched`(3.12+) | 3.11 은 `islice` 루프로 |

## 핵심 문장

1. **`groupby` 는 모으지 않고 끊는다** — 정렬 전 **2 / 3** 키가 여러 그룹, 정렬 뒤 **0 / 3**.
2. **그룹 이터레이터는 원본을 공유한다** — 모아 두고 나중에 읽으면 마지막 그룹까지 `[]`.
3. **`map`·`filter`·`islice` 사슬은 필요한 만큼만 일한다** — 리스트판 10 · 10, 사슬판 4 · 4. JS·Rust 와 같은 표다.
4. **`tee` 는 앞서 간 쪽이 당긴 값을 쌓는다** — 원본 당김 수가 안 늘었는데 값이 나왔다.
5. **`batched` 는 3.12 부터, `strict` 는 3.13 부터**(문서) — 시간·메모리는 한 번도 재지 않았다.

## 관련 자료

* 선행: [16-iterator-protocol](../16-iterator-protocol/2-summary.md) — ★★★ **경계**: `iter`/`next`/`StopIteration` 과 「소진된 것과 빈 것은 구분되지 않는다」는 그쪽이 정본. 여기는 **그 위의 부품들**부터.
* 선행: [10-list-methods-and-sort-key](../10-list-methods-and-sort-key/2-summary.md) — 안정 정렬 보장(동작 3). `groupby` 앞의 정렬이 그룹 안 순서를 지키는 근거.
* 선행: [15-generator-expressions-lazy-eval](../15-generator-expressions-lazy-eval/2-summary.md) · [17-generators-yield](../17-generators-yield/2-summary.md) — 게으른 평가의 다른 얼굴.
* 이웃: [43-collections](../43-collections/2-summary.md) — `defaultdict(list)` 묶기. 정렬 전제가 없다.
* 대비: [JS 21번 — 이터레이터 헬퍼](../../../js/syntax/21-iterator-helpers/2-summary.md) · [Rust 36번 — 어댑터·게으름·`collect`](../../../rust/syntax/36-iterator-adapters-laziness-and-collect/2-summary.md) —
  ★ **경계**: 호출 로그 방법과 JS·Rust 쪽 수치는 그쪽이다. 여기서는 **같은 파이프라인을 파이썬 내장 함수로 던져** 같은 표를 얻었다.
  ★ JS 21번이 「파이썬 쪽을 돌리지 않았다 — 그쪽 편의 실측을 인용할 자리」라 적어 둔 자리가 동작 3 이다. JS 헬퍼에는 **`tee` 같은 갈래 복제가 없다**고 그 편이 적었다.
* 공식 문서: [`itertools`(3.12)](https://docs.python.org/3.12/library/itertools.html) · [`itertools`(3.13)](https://docs.python.org/3.13/library/itertools.html)

## 용어 풀이

* **이터레이터(iterator)**: `next()` 로 하나씩 꺼내는 객체. 다 꺼내면 끝.
* **게으른 평가(lazy evaluation)**: 필요할 때 계산. `itertools` 는 만들 때 일을 안 한다.
* **물질화(materialize)**: 이터레이터를 `list` 따위로 **한 번에 다 꺼내 담는 것.**
* **`groupby`**: 키가 **바뀔 때마다** 끊어 `(키, 그룹 이터레이터)` 를 내는 함수.
* **그룹 이터레이터**: `groupby` 가 주는 각 그룹. **원본을 공유**해서 다음 그룹으로 가면 빈다.
* **`tee`**: 이터레이터 하나를 **여럿으로 복제**. 앞서 간 쪽이 당긴 값을 뒤처진 쪽을 위해 쌓는다.
* **`islice`**: 이터레이터의 **슬라이스**. 음수를 안 받는다.
* **조합(combination) / 순열(permutation)**: 순서 없이 / 순서 있게 r 개 고르기. 개수는 `math.comb` / `math.perm`.
* **`batched`**(3.12+): n 개씩 묶어 튜플로 내는 함수. 마지막 묶음은 짧을 수 있다.

## 더 들어가면

* ★ **`accumulate`·`pairwise`(3.10)·`zip_longest`·`starmap`** — 이 문서는 재지 않았다. 문서 끝의 **레시피 절**이 조합 예를 싣는다.
* ★ **`groupby` 와 `defaultdict` 의 선택** — 입력이 **이미 정렬된 거대한 스트림**이면 `groupby` 는 **한 그룹씩만** 들고 간다. 메모리 차이는 **재지 않았다.**
* ★ **3.13 을 설치하게 되면 다시 돌릴 것** — 동작 6 의 판 격자. 문서대로면 `strict=True` 가 **짧은 마지막 묶음에서 `ValueError`** 를 낸다 — ★ **예측이지 측정이 아니다.**
