# python/syntax/13-set-and-frozenset — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만.
> - [Set Types — set, frozenset](https://docs.python.org/3.12/library/stdtypes.html#set-types-set-frozenset) — 순서 없음 · 연산 · 부분 순서 · 섞었을 때의 타입
> - [glossary — hashable](https://docs.python.org/3.12/glossary.html#term-hashable) — 원소 요건
> - [PYTHONHASHSEED](https://docs.python.org/3.12/using/cmdline.html#envvar-PYTHONHASHSEED) · [`-R` 옵션](https://docs.python.org/3.12/using/cmdline.html#cmdoption-R) — **무엇이 무작위화되나**
> - [Mapping Types — dict](https://docs.python.org/3.12/library/stdtypes.html#mapping-types-dict) — 대조군(삽입 순서)
>
> **실행 검증** — 이 문서에 실린 출력은 전부 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> ★ **순서에 관한 주장은 `PYTHONHASHSEED` 를 0·1·2 로 바꿔 던져 확인했다** — 「한 판에서 안 갈렸다」를 근거로 쓰지 않았다.
> 일부는 **3.11.15** 로 한 번 더 돌려 대조했고, 그 사실을 그 자리에 적었다.
> **수치** — 「비용」 절의 시간은 `timeit` 중앙값이 아니라 **`repeat=7` 의 최솟값**이고, 머신은 13th Gen Intel i7-13700HX 다.
> **절댓값이 아니라 「n 이 100배가 되면 어떻게 되나」라는 기울기만** 재현된다고 읽어야 한다.
> **버전** — `set`·`frozenset`·집합 리터럴·집합 컴프리헨션은 **이 노트가 다루는 범위(3.10\~3.13)에서 버전 차이가 없다.**
> 버전이 걸리는 것은 하나뿐이다 — **해시 무작위화가 기본으로 켜진 것이 3.3**(3.3 릴리스 문서: *"Hash randomization is switched on by default."*).
> **선행** — [12-dict-and-key-requirements](../12-dict-and-key-requirements/2-summary.md)(**해시·키 요건의 정본**) ·
> [11-tuple-and-unpacking](../11-tuple-and-unpacking/2-summary.md)(튜플이 원소가 되는 조건) ·
> [10-list-methods-and-sort-key](../10-list-methods-and-sort-key/2-summary.md)(집합이 든 리스트를 정렬하는 것).

## 한눈에 — 쉽게 말하면

**set 은 dict 에서 「값」과 「순서를 적어 두는 줄」을 뺀 것이다. 남은 건 해시 칸뿐이라 순서가 없다.**

```text
  dict                                   set
  ┌ 순서줄 ┐  ┌ 해시 칸 ┐                        ┌ 해시 칸 ┐
  │ c a b │  │ …키·값… │                (없음)  │ …원소… │
  └───────┘  └─────────┘                        └─────────┘
   돌 때 본다   찾을 때 본다                              돌 때도 이것을 본다

  ->  dict 는 "넣은 순서" 로 돈다 (3.7+ 언어 보장)
  ->  set 은 "칸에 놓인 순서" 로 돈다 = 해시에 달렸다 = 보장이 없다
```

★ **그래서 `PYTHONHASHSEED` 를 바꾸면 `set` 의 순서만 갈린다.** dict 는 안 갈린다.\
★ 그리고 **갈리는 것은 str·bytes 뿐**이다 — 정수는 해시가 값 그 자체라 시드를 타지 않는다(아래에서 던져 확인한다).

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 순서를 적는 줄이 없다 | 순서 미보장 | `PYTHONHASHSEED` 를 바꿔 본다 |
| 같은 이름표는 한 칸 | 중복 제거 | `{1, 1.0, True}` 의 크기가 1 |
| 이름표를 걸려면 해시가 있어야 | 원소는 해시 가능 | `{{1,2}}` 가 `TypeError` |
| 얼린 집합은 이름표가 된다 | `frozenset` | `{frozenset({1,2})}` 는 된다 |
| `<=` 는 「크기」가 아니라 「포함」 | 부분집합 | `{1,2} <= {3,4}` 도 `{1,2} >= {3,4}` 도 `False` |
| 연산자는 집합끼리만 | `&` `\|` `-` `^` | `set("abc") & "cbs"` 가 `TypeError` |
| 메서드는 아무 이터러블 | `.intersection("cbs")` | 된다 |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.\
「**`list(set(...))` 로 중복을 없앴더니 순서가 매번 달라졌다**」가 그것이다.
같은 코드가 같은 머신에서 **실행마다** 다른 순서를 낸다. 에러는 안 난다.

> **부분 순서(partial order)** — 두 값 중 **어느 쪽이 큰지 정할 수 없는 쌍이 있는** 순서.\
> 키가 크기라면 누가 크든 정해지지만, 「포함 관계」는 `{1,2}` 와 `{3,4}` 처럼 **아무 관계도 없는 쌍**이 생긴다.

## 이 주제가 답하려는 질문

1. **set 의 순서는 정말 없는가** — 「안 갈렸다」와 「보장된다」를 어떻게 가르나. 무엇이 갈리고 무엇이 안 갈리나.
2. **무엇이 원소가 될 수 있는가** — `set` 자신은 왜 원소가 못 되고 `frozenset` 은 되는가.
3. **`<=` 는 무엇을 비교하는가** — 크기인가 포함인가, 그리고 그 때문에 무엇이 조용히 틀리나.

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 문장으로 읽는다.

### 1. ★ 순서가 없다 — 「안 갈렸다」가 아니라 「갈리는 것을 봤다」로 적는다

**언제 쓰나** — `for x in s:` 를 쓸 때. `list(set(...))` 로 중복을 없앨 때.

문서가 못 박는다 — *"A set object is an **unordered** collection of distinct hashable objects."* /
*"Being an unordered collection, **sets do not record element position or order of insertion**.
Accordingly, sets do not support indexing, slicing, or other sequence-like behavior."*

★ **한 판만 돌려 보고 「이 순서다」로 적으면 안 된다.** 해시 무작위화를 끄고 켜 가며 던져야 한다.

```text
===== 소스: ex.py =====
print("문자열 :", list({"apple", "banana", "cherry", "date", "elderberry"}))
print("정수   :", list({1, 2, 3, 4, 5, 100, 200}))
print("섞으면 :", list({1, "a", 2, "b", (3, 4)}))
print("hash('a') =", hash("a"), "| hash(1) =", hash(1), "| hash((3,4)) =", hash((3, 4)))
```

```bash
for seed in 0 1 2; do echo "PYTHONHASHSEED=$seed"; PYTHONHASHSEED=$seed python3 ex.py; done
```

```text
PYTHONHASHSEED=0
문자열 : ['banana', 'apple', 'cherry', 'date', 'elderberry']
정수   : [1, 2, 3, 4, 5, 100, 200]
섞으면 : [1, 2, 'a', (3, 4), 'b']
hash('a') = 4644417185603328019 | hash(1) = 1 | hash((3,4)) = 1079245023883434373
PYTHONHASHSEED=1
문자열 : ['date', 'elderberry', 'cherry', 'apple', 'banana']
정수   : [1, 2, 3, 4, 5, 100, 200]
섞으면 : [1, 2, 'a', 'b', (3, 4)]
hash('a') = -3012895188637184397 | hash(1) = 1 | hash((3,4)) = 1079245023883434373
PYTHONHASHSEED=2
문자열 : ['elderberry', 'date', 'apple', 'banana', 'cherry']
정수   : [1, 2, 3, 4, 5, 100, 200]
섞으면 : [1, 'b', 2, (3, 4), 'a']
hash('a') = 6352457989142756797 | hash(1) = 1 | hash((3,4)) = 1079245023883434373
```

그림 해설.

- ★ **문자열 집합은 세 판이 전부 다르다.** 다섯 원소가 매번 다른 차례로 나온다.
- ★ **정수 집합은 세 판이 한 글자도 안 달랐다.** `hash(1)` 이 시드마다 `1` 이기 때문이다.
- ★ **`hash((3,4))` 도 안 갈린다**(정수만 든 튜플이므로). **그런데 섞인 집합에서 `(3, 4)` 의 자리는 갈렸다** —
  자기 해시가 안 변해도 **옆 원소들이 칸을 다르게 차지해** 밀려나기 때문이다.
- 문서가 무엇이 무작위화되는지 직접 적는다 — *"a random value is used to seed the hashes of **str and bytes** objects."*

★★ **그러므로 「정수 집합은 순서가 있다」로 적으면 안 된다.**
시드에 안 갈릴 뿐이고, **같은 원소라도 넣은 순서가 다르면 갈린다.**

```python
print("{1, 9} ->", list({1, 9}), "| {9, 1} ->", list({9, 1}), "| == :", {1, 9} == {9, 1})
```

```text
{1, 9} -> [1, 9] | {9, 1} -> [9, 1] | == : True
```

★ **같은 집합인데(`==` 가 `True`) 도는 차례가 다르다.** `1` 과 `9` 가 같은 칸을 놓고 다투다(충돌),
**먼저 온 쪽이 그 칸을 차지**하기 때문이다. 이 결과는 **시드를 0·1 로 바꿔도 같았다** — 정수라서 그렇다.

**dict 와의 대조군**

```bash
for seed in 0 1 2; do PYTHONHASHSEED=$seed python3 -c \
  'd={};[d.setdefault(k,i) for i,k in enumerate(["cherry","apple","banana","date"])];print("seed:",list(d))'; done
```

```text
seed: ['cherry', 'apple', 'banana', 'date']
seed: ['cherry', 'apple', 'banana', 'date']
seed: ['cherry', 'apple', 'banana', 'date']
```

★ **같은 문자열인데 dict 는 안 갈리고 set 은 갈린다.** 이 대조가 「순서줄이 있나 없나」의 증거다.

**★ 무작위화를 끄고 도로 켜기 — `PYTHONHASHSEED=0` 이 「끄는」 것이고 `-R` 이 「도로 켜는」 것이다**

문서가 그렇게 적는다 — *"This option only has an effect if the `PYTHONHASHSEED` environment variable is **set to 0**,
since hash randomization is **enabled by default**."*
기본으로 켜진 것은 **3.3** 부터다(3.3 릴리스 문서: *"Hash randomization is switched on by default."*).
`-R` 은 3.3\~3.6 에서는 무시됐고 **3.7 부터 무시되지 않는다**(*"The option is no longer ignored."*).

```bash
echo '--- 껐다 (PYTHONHASHSEED=0) ---'; for i in 1 2; do PYTHONHASHSEED=0 python3 -c 'print(hash("a"))'; done
echo '--- -R 로 도로 켰다 ---';        for i in 1 2; do PYTHONHASHSEED=0 python3 -R -c 'print(hash("a"))'; done
```

```text
--- 껐다 (PYTHONHASHSEED=0) ---
4644417185603328019
4644417185603328019
--- -R 로 도로 켰다 ---
-9055864142906961453
7614388158228933011
```

★ **끈 쪽 두 줄은 같고 도로 켠 쪽 두 줄은 다르다.** 뒤쪽 두 값은 **다시 돌리면 또 달라진다** —
대조할 것은 숫자가 아니라 「앞은 같고 뒤는 다르다」는 성질이다.

**비용** — 순서줄이 없어 **메모리가 덜 들고** 순회가 곧 칸 훑기다.\
대신 **출력에 순서가 드러나는 모든 자리**(로그·파일·API 응답·테스트 기댓값)가 흔들린다.
순서가 필요하면 **`sorted()` 로 못 박거나** `dict.fromkeys()` 를 쓴다.

### 2. ★ 원소 요건 — dict 키와 같다. 그래서 set 은 자기 자신의 원소가 못 된다

**언제 쓰나** — 집합의 집합이 필요할 때. 리스트를 원소로 넣으려다 막혔을 때.

문서 — *"Set elements, **like dictionary keys, must be hashable**."* /
*"The `set` type is mutable … **Since it is mutable, it has no hash value and cannot be used as either a dictionary key
or as an element of another set**. The `frozenset` type is immutable and hashable …"*

```text
   {1, 2}      가변  ->  해시 없음  ->  원소가 못 된다
   frozenset({1, 2})  불변  ->  해시 있음  ->  원소가 된다 · dict 키도 된다

   ★ "불변이라서" 가 아니라 "해시가 평생 안 바뀌어야 해서" 다.
     가변인 것에 해시를 주면 원소를 고치는 순간 잘못된 칸에 남는다 (동작 7).
```

```python
try:
    {{1, 2}}
except TypeError as e:
    print("{{1,2}}            -> TypeError:", e)
print("{frozenset({1,2})} ->", {frozenset({1, 2})})
print("dict 키로          ->", {frozenset({1, 2}): "값"})
print("set.__hash__       =", set.__hash__, "| frozenset.__hash__ is None :", frozenset.__hash__ is None)
```

```text
{{1,2}}            -> TypeError: unhashable type: 'set'
{frozenset({1,2})} -> {frozenset({1, 2})}
dict 키로          -> {frozenset({1, 2}): '값'}
set.__hash__       = None | frozenset.__hash__ is None : False
```

★ **`set.__hash__` 가 `None` 이다** — [12번](../12-dict-and-key-requirements/2-summary.md)에서 `__eq__` 만 정의한 클래스가 겪은 것과 **같은 장치**다.
언어는 「해시 못 함」을 **`__hash__` 를 `None` 으로 두는 것**으로 표현한다.

**그런데 찾을 때는 `set` 을 그대로 줘도 된다.**

```python
print("set 안에 set 을 찾을 때 :", {1, 2} in {frozenset({1, 2})})
```

```text
set 안에 set 을 찾을 때 : True
```

문서가 그 예외를 적는다 — *"the *elem* argument to the `__contains__`, `remove`, and `discard` methods **may be a set**.
To support searching for an equivalent frozenset, **a temporary one is created from elem**."*\
★ **넣을 수는 없는데 찾을 수는 있다.** 찾기용 임시 `frozenset` 을 언어가 대신 만들어 준다.

**비용** — `frozenset` 으로 얼리는 것은 **원소 수만큼의 새 집합**을 만드는 일이다. 루프 안에서 반복하면 그만큼 든다.

### 3. ★ 네 연산 — `&` `|` `-` `^`

**언제 쓰나** — 두 목록의 공통·합집합·차이를 구할 때.

```text
        a = {1, 2, 3, 4}        b = {3, 4, 5}

          a                  b
        ┌──────────┐
        │ 1  2 │ 3  4 │ 5  │      a & b  =  {3, 4}       가운데
        └──────┴──────────┘      a | b  =  {1,2,3,4,5}  전부
                                 a - b  =  {1, 2}       왼쪽만  ★ 방향이 있다
                                 b - a  =  {5}          오른쪽만
                                 a ^ b  =  {1, 2, 5}    가운데만 뺀 것
```

```python
a = {1, 2, 3, 4}
b = {3, 4, 5}
print("a & b :", sorted(a & b), "| a | b :", sorted(a | b))
print("a - b :", sorted(a - b), "| b - a :", sorted(b - a), " <- 방향이 있다")
print("a ^ b :", sorted(a ^ b))
print("isdisjoint :", a.isdisjoint({9}), a.isdisjoint(b))
```

```text
a & b : [3, 4] | a | b : [1, 2, 3, 4, 5]
a - b : [1, 2] | b - a : [5]  <- 방향이 있다
a ^ b : [1, 2, 5]
isdisjoint : True False
```

★ **출력을 `sorted()` 로 감쌌다.** 그냥 찍으면 그 줄이 **시드마다 달라져** 문서가 거짓말을 하게 된다(동작 1).
**집합 결과를 문서·로그·테스트에 남길 때는 `sorted()` 가 기본이다.**

| 연산자 | 메서드 | 제자리 연산 | 무엇을 하나 |
|---|---|---|---|
| `a \| b` | `a.union(b)` | `a \|= b` / `a.update(b)` | 합집합 |
| `a & b` | `a.intersection(b)` | `a &= b` / `a.intersection_update(b)` | 교집합 |
| `a - b` | `a.difference(b)` | `a -= b` / `a.difference_update(b)` | 차집합 — **방향이 있다** |
| `a ^ b` | `a.symmetric_difference(b)` | `a ^= b` / `a.symmetric_difference_update(b)` | 대칭차 |
| — | `a.isdisjoint(b)` | — | 겹치는 게 없나 |

**비용** — `&` 는 **작은 쪽**을 훑는다. `|` 는 둘을 합친 크기만큼 새로 만든다.\
제자리 연산(`|=`·`update`)은 새 집합을 안 만든다 — 루프에서 누적할 때는 이쪽이다.

### 4. ★ `<=` 는 크기가 아니라 포함이다 — 그래서 셋 다 `False` 인 쌍이 있다

**언제 쓰나** — 「이 권한들을 다 갖고 있나」를 물을 때. 그리고 집합을 정렬하려 할 때.

```text
   x = {1,2}   y = {1,2,3}          x <= y   True    x 가 y 안에 다 있다
                                    x <  y   True    게다가 같지 않다
                                    x >= y   False

   p = {1,2}   q = {3,4}            ★ 아무 관계도 없다
                                    p <  q   False
                                    p == q   False
                                    p >  q   False     <- 셋 다 False
                                    len 은 같다 (2, 2)
```

```python
x, y = {1, 2}, {1, 2, 3}
print("{1,2} <= {1,2,3} :", x <= y, "| < :", x < y, "| >= :", x >= y)
print("{1,2} <= {1,2}   :", x <= {1, 2}, "| < :", x < {1, 2})
p, q = {1, 2}, {3, 4}
print("겹치지 않는 둘 p={1,2} q={3,4}")
print("  p < q :", p < q, "| p == q :", p == q, "| p > q :", p > q, " <- 셋 다 False")
print("  p <= q:", p <= q, "| p >= q :", p >= q)
print("  len 은 같다 :", len(p) == len(q))
```

```text
{1,2} <= {1,2,3} : True | < : True | >= : False
{1,2} <= {1,2}   : True | < : False
겹치지 않는 둘 p={1,2} q={3,4}
  p < q : False | p == q : False | p > q : False  <- 셋 다 False
  p <= q: False | p >= q : False
  len 은 같다 : True
```

문서가 그 성질을 직접 적는다 —
*"**The subset and equality comparisons do not generalize to a total ordering function.**
For example, any two nonempty disjoint sets are not equal and are not subsets of each other,
so **all** of the following return `False`: `a<b`, `a==b`, or `a>b`."*

★★ **그리고 문서가 그 결과까지 적는다** —
*"Since sets only define partial ordering (subset relationships), **the output of the `list.sort()` method is undefined for lists of sets**."*

**그래서 집합이 든 리스트를 정렬하면 — 에러가 안 나고 결과가 틀린다**

```python
data = [{3}, {1, 2}, {1}, {2}]
print("정렬 전 :", data)
print("sorted  :", sorted(data), " <- 에러가 안 난다")
print("한 번 더 (입력 순서를 바꿔서) :", sorted([{1}, {2}, {1, 2}, {3}]))
print("{1} < {2} :", {1} < {2}, "| {2} < {1} :", {2} < {1})
```

```text
정렬 전 : [{3}, {1, 2}, {1}, {2}]
sorted  : [{3}, {1}, {2}, {1, 2}]  <- 에러가 안 난다
한 번 더 (입력 순서를 바꿔서) : [{1}, {2}, {1, 2}, {3}]
{1} < {2} : False | {2} < {1} : False
```

★ **두 번의 결과가 다르다.** 입력 순서가 바뀌었을 뿐인데 나온 차례가 달라졌다 —
정렬이 기대는 `<` 가 「작다」가 아니라 「**부분집합이다**」라서, 대부분의 쌍에서 `False` 가 나오고
[10번](../10-list-methods-and-sort-key/2-summary.md)의 **안정 정렬**이 원래 자리를 그대로 남겨 버리기 때문이다.

★ **`TypeError` 가 안 난다는 점이 가장 나쁘다.** 타입이 섞인 리스트를 정렬하면 터지는데([10번](../10-list-methods-and-sort-key/2-summary.md)),
집합끼리는 `<` 가 **정의되어 있어서** 통과한다. 고치는 법은 **키를 주는 것**이다 —
`sorted(data, key=len)` 이나 `sorted(data, key=sorted)`.

**비용** — 부분집합 판정은 작은 쪽 원소 수만큼 본다. `<=` 는 `issubset` 과 같은 일이다.

### 5. ★ 연산자는 집합만, 메서드는 아무 이터러블

**언제 쓰나** — 리스트·문자열과 집합을 섞어 쓸 때.

문서가 **이 비대칭이 의도된 것**이라고 적는다 —
*"the non-operator versions of `union()`, `intersection()`, `difference()`, `symmetric_difference()`, `issubset()`,
and `issuperset()` methods **will accept any iterable** as an argument.
In contrast, their operator based counterparts **require their arguments to be sets**.
This **precludes error-prone constructions** like `set('abc') & 'cbs'` in favor of the more readable `set('abc').intersection('cbs')`."*

```python
try:
    set("abc") & "cbs"
except TypeError as e:
    print("set('abc') & 'cbs'        -> TypeError:", e)
print("set('abc').intersection('cbs') ->", sorted(set("abc").intersection("cbs")))
try:
    {1, 2} | [2, 3]
except TypeError as e:
    print("{1,2} | [2,3]             -> TypeError:", e)
print("{1,2}.union([2,3])             ->", sorted({1, 2}.union([2, 3])))
s = {1, 2}
s |= {3}
print("s |= {3}   ->", sorted(s))
try:
    s |= [4]
except TypeError as e:
    print("s |= [4]   -> TypeError:", e)
s.update([4])
print("s.update([4]) ->", sorted(s), " <- update 는 받는다")
print("issubset 은 문자열도 :", set("ab").issubset("abc"))
```

```text
set('abc') & 'cbs'        -> TypeError: unsupported operand type(s) for &: 'set' and 'str'
set('abc').intersection('cbs') -> ['b', 'c']
{1,2} | [2,3]             -> TypeError: unsupported operand type(s) for |: 'set' and 'list'
{1,2}.union([2,3])             -> [1, 2, 3]
s |= {3}   -> [1, 2, 3]
s |= [4]   -> TypeError: unsupported operand type(s) for |=: 'set' and 'list'
s.update([4]) -> [1, 2, 3, 4]  <- update 는 받는다
issubset 은 문자열도 : True
```

★ **오류 문구가 `|=` 를 그대로 가리킨다** — `set` 은 `__ior__` 를 갖고 있고 **거기서 타입을 거부**하는 것이라
`|` 로 떨어지지 않는다.\
★ **[12번](../12-dict-and-key-requirements/2-summary.md)의 dict 와 반대다.** dict 는 `|=` 가 이터러블을 받아 주는데 set 은 안 받는다.
받아 주는 것은 **`update()`** 쪽이다. **두 타입에서 같은 기호가 다른 규칙을 탄다.**

| | `\|` / `\|=` | `.union()` / `.update()` |
|---|---|---|
| **set** | 집합만 | 아무 이터러블 |
| **dict** | `\|` 는 dict 만 · **`\|=` 는 이터러블도** | `update()` 는 이터러블·키워드도 |

**비용** — 없다. 이 비대칭은 성능이 아니라 **실수를 막으려고** 만든 것이다(문서가 그렇게 말한다).

### 6. ★ frozenset — 얼리면 키가 되고, 섞으면 왼쪽 타입이 나온다

**언제 쓰나** — 「태그 묶음」을 키로 쓸 때. 집합의 집합이 필요할 때.

문서 — *"Binary operations that mix `set` instances with `frozenset` **return the type of the first operand**.
For example: `frozenset('ab') | set('bc')` returns an instance of `frozenset`."* /
*"Instances of `set` are compared to instances of `frozenset` **based on their members**."*

```python
print("frozenset('ab') | set('bc') ->", type(frozenset("ab") | set("bc")).__name__)
print("set('ab') | frozenset('bc') ->", type(set("ab") | frozenset("bc")).__name__)
print("set('abc') == frozenset('abc') :", set("abc") == frozenset("abc"))
print("set('abc') in set([frozenset('abc')]) :", set("abc") in set([frozenset("abc")]))
print("hash 가 같나 :", hash(frozenset("abc")) == hash(frozenset("cba")))
print("type({}) =", type({}).__name__, "| type(set()) =", type(set()).__name__, "| type({1}) =", type({1}).__name__)
print("빈 set repr :", repr(set()), "| 빈 frozenset :", repr(frozenset()))
```

```text
frozenset('ab') | set('bc') -> frozenset
set('ab') | frozenset('bc') -> set
set('abc') == frozenset('abc') : True
set('abc') in set([frozenset('abc')]) : True
hash 가 같나 : True
type({}) = dict | type(set()) = set | type({1}) = set
빈 set repr : set() | 빈 frozenset : frozenset()
```

★ **`{}` 는 빈 dict 다.** 빈 집합 리터럴은 **없다** — `set()` 이라고 써야 한다.
그래서 `repr(set())` 도 `set()` 이다(`{}` 로 찍으면 dict 로 읽히기 때문).

★ **`set == frozenset` 이 `True`** 다. 타입이 아니라 **원소로** 비교한다 —
[11번](../11-tuple-and-unpacking/2-summary.md)의 `namedtuple` 이 평범한 튜플과 같았던 것과 같은 성격이다.

**태그 묶음을 키로 쓰는 실무 꼴**

```python
groups = {}
for item, tags in [("A", {"x", "y"}), ("B", {"y", "x"}), ("C", {"z"})]:
    groups.setdefault(frozenset(tags), []).append(item)
print({tuple(sorted(k)): v for k, v in groups.items()})
```

```text
{('x', 'y'): ['A', 'B'], ('z',): ['C']}
```

★ **`{"x","y"}` 와 `{"y","x"}` 가 한 키로 묶였다.** 튜플이었다면 순서가 달라 딴 키가 됐을 것이다.
**「순서를 무시한 묶음」이 키여야 할 때 `frozenset` 이 정답이다.**

**비용** — `frozenset(tags)` 는 매번 새 객체를 만든다. 반복 루프에서는 그만큼 든다.

### 7. ★ 같은 값이면 하나 — 그리고 원소를 고치면 사전과 똑같이 망가진다

**언제 쓰나** — 중복 제거를 쓸 때. 내 클래스를 원소로 넣을 때.

```python
print("{1, 1.0, True}       ->", {1, 1.0, True}, [type(x).__name__ for x in {1, 1.0, True}])
print("{True, 1.0, 1}       ->", {True, 1.0, 1}, [type(x).__name__ for x in {True, 1.0, 1}])
print("{1.0, 1, True}       ->", {1.0, 1, True}, [type(x).__name__ for x in {1.0, 1, True}])
s = {1}
s.add(True); s.add(1.0)
print("add 로 넣어도        ->", s, [type(x).__name__ for x in s])
print("{0, False} :", {0, False}, "| {False, 0} :", {False, 0})
```

```text
{1, 1.0, True}       -> {1} ['int']
{True, 1.0, 1}       -> {True} ['bool']
{1.0, 1, True}       -> {1.0} ['float']
add 로 넣어도        -> {1} ['int']
{0, False} : {0} | {False, 0} : {False}
```

★ **남는 것은 처음 들어온 것**이다. dict 에서 「키는 처음 것이 남는다」와 같은 규칙인데,
set 에는 값이 없으니 **「나중 것이 이긴다」는 쪽이 아예 없다** — 나중 것은 **그냥 버려진다.**

**원소를 넣은 뒤 고치면**

```python
class Box:
    def __init__(self, v): self.v = v
    def __eq__(self, o): return isinstance(o, Box) and self.v == o.v
    def __hash__(self): return hash(self.v)
    def __repr__(self): return f"Box({self.v})"

b = Box(1)
st = {b}
print("넣은 직후       :", st, "| b in st :", b in st)
b.v = 2
print("원소를 고친 뒤  :", st, "| b in st :", b in st, "| Box(2) in st :", Box(2) in st)
st.add(Box(2))
print("Box(2) 를 넣으면:", st, "| len =", len(st), " <- 같은 값이 둘")
```

```text
넣은 직후       : {Box(1)} | b in st : True
원소를 고친 뒤  : {Box(2)} | b in st : False | Box(2) in st : False
Box(2) 를 넣으면: {Box(2), Box(2)} | len = 2  <- 같은 값이 둘
```

★★ **집합에 같은 값이 둘 들어 있다.** 집합의 존재 이유가 깨졌는데 **예외도 경고도 없다.**
[12번](../12-dict-and-key-requirements/2-summary.md)의 dict 와 같은 사고이고, 여기서는 **눈에 더 잘 보이는 모양**으로 드러난다.

**순회 중 변경도 같다.**

```text
===== 소스 (python3 - <<'PY') =====
s = {"a", "b", "c"}
for x in s:
    s.add("d")
```

```text
Traceback (most recent call last):
  File "<stdin>", line 2, in <module>
RuntimeError: Set changed size during iteration
```

★ **문구가 dict 와 다르다** — `Set changed size during iteration`(대문자 `S`).
dict 쪽은 `dictionary changed size during iteration` 이다.

**비용** — 없다. 이 사고의 대가는 **비용이 아니라 조용한 오류**다.

### 8. 원소를 넣고 빼는 법 — `remove` 와 `discard` 가 갈리는 자리

```python
s = {1, 2}
try:
    s.remove(9)
except KeyError as e:
    print("s.remove(9)  -> KeyError:", e)
print("s.discard(9) ->", s.discard(9), "| s =", sorted(s), " <- 없어도 조용하다")
print("s.pop()      ->", s.pop(), "| 남은 것 :", sorted(s), " <- 어느 것이 나올지는 정해져 있지 않다")
try:
    set().pop()
except KeyError as e:
    print("set().pop()  -> KeyError:", e)
print("컴프리헨션 :", sorted({c for c in "abracadabra" if c not in "abc"}))
```

```text
s.remove(9)  -> KeyError: 9
s.discard(9) -> None | s = [1, 2]  <- 없어도 조용하다
s.pop()      -> 1 | 남은 것 : [2]  <- 어느 것이 나올지는 정해져 있지 않다
set().pop()  -> KeyError: 'pop from an empty set'
컴프리헨션 : ['d', 'r']
```

★ **`pop()` 은 「임의의」 원소를 뺀다** — 문서가 *"Remove and return an **arbitrary** element"* 라고 적는다.
위 판에서 `1` 이 나온 것은 **관찰이지 보장이 아니다.**\
★ **`remove` 는 없으면 터지고 `discard` 는 조용하다.** [10번](../10-list-methods-and-sort-key/2-summary.md)의 `list.remove` 는 조용한 짝이 없다.

### 9. 비용 — 재 본 것

★ 아래는 **이 머신에서 실제로 잰 값**이다(측정 조건은 머리말에 있다). **절댓값이 아니라 기울기를 읽는다.**

```python
import timeit
def bench(stmt, setup, n, r=7):
    return min(timeit.repeat(stmt, setup=setup, number=n, repeat=r)) / n * 1e9
for size, n in ((1000, 20000), (100000, 300)):
    st = f"L=list(range({size})); S=set(L); target={size-1}"
    l = bench("target in L", st, n)
    s = bench("target in S", st, 200000)
    print(f"n={size:6}  list 'in' {l:11.1f} ns   set 'in' {s:7.1f} ns   배율 {l/s:9.1f}x")
```

세 판을 돌린 결과다. ★ **이 수치는 다시 돌리면 또 달라진다** — 대조할 것은 숫자가 아니라 아래에 적은 기울기다.
(`--- 판 N ---` 줄은 세 판을 가르려고 붙인 것이고 스크립트가 찍는 것이 아니다.)

```text
--- 판 1 ---
n=  1000  list 'in'      6766.4 ns   set 'in'    22.6 ns   배율     300.0x
n=100000  list 'in'    718924.8 ns   set 'in'    20.2 ns   배율   35503.4x
--- 판 2 ---
n=  1000  list 'in'      7693.3 ns   set 'in'    24.4 ns   배율     315.0x
n=100000  list 'in'    672799.3 ns   set 'in'    18.5 ns   배율   36271.8x
--- 판 3 ---
n=  1000  list 'in'      6683.2 ns   set 'in'    26.3 ns   배율     253.9x
n=100000  list 'in'    751244.5 ns   set 'in'    23.3 ns   배율   32211.0x
```

★ **재현되는 것은 절댓값이 아니라 이것이다** — **n 을 100배로 늘리면 `list` 의 `in` 은 약 100배가 되고
`set` 의 `in` 은 안 변한다.** 배율 숫자는 판마다 10% 넘게 흔들렸다(`253.9x` ↔ `315.0x`).\
★ **최악을 골라 잰 것**이다(`target` 을 마지막 원소로). 앞쪽 원소를 찾으면 `list` 가 훨씬 빠르게 나온다 —
**「집합이 빠르다」는 찾는 자리에 달렸다.**\
★ 원리(왜 평균 O(1) 인가, 최악에 무엇이 일어나는가)는 [`cs/data-structure/`](../../../../../data-structure/)가 정본이다.

## 문법 — 형태와 규칙

```python
set()                 # ★ 빈 집합.  {} 는 빈 dict 다
{1, 2, 3}             # 비어 있지 않은 집합 리터럴
{x for x in xs if 조건}   # 집합 컴프리헨션 (14번)
set(iterable) · frozenset(iterable)

x in s · len(s)
s.add(x) · s.remove(x)(없으면 KeyError) · s.discard(x)(조용) · s.pop()(임의) · s.clear()
a | b · a & b · a - b · a ^ b          # ★ 양쪽이 집합이어야 한다
a.union(it) · a.intersection(it) · a.difference(it) · a.symmetric_difference(it)   # 아무 이터러블
a <= b(issubset) · a < b · a >= b(issuperset) · a > b · a.isdisjoint(b)
a |= b · a &= b · a -= b · a ^= b      # frozenset 에는 없다
a.update(it) · a.difference_update(it) · …                                        # 아무 이터러블
```

**금지 사례 — 에러가 나는 자리**

```python
{{1, 2}}                 # TypeError: unhashable type: 'set'
{[1, 2]}                 # TypeError: unhashable type: 'list'
set("abc") & "cbs"       # TypeError — 연산자는 집합만
{1, 2} | [2, 3]          # TypeError
s |= [4]                 # TypeError — update() 를 써야 한다
frozenset({1}).add(2)    # AttributeError — 불변이다
s[0]                     # TypeError — 첨자가 없다
```

```text
===== 소스 (python3 - <<'PY') =====
try:
    frozenset({1}).add(2)
except AttributeError as e:
    print("frozenset.add ->", type(e).__name__, e)
try:
    {1, 2}[0]
except TypeError as e:
    print("s[0]          ->", type(e).__name__, e)
try:
    {[1, 2]}
except TypeError as e:
    print("{[1,2]}       ->", type(e).__name__, e)
```

```text
<stdin>:6: SyntaxWarning: 'set' object is not subscriptable; perhaps you missed a comma?
frozenset.add -> AttributeError 'frozenset' object has no attribute 'add'
s[0]          -> TypeError 'set' object is not subscriptable
{[1,2]}       -> TypeError unhashable type: 'list'
```

★ **경고도 출력이다.** `{1, 2}[0]` 은 **컴파일 단계에서 `SyntaxWarning` 이 먼저 나온다** —
*"perhaps you missed a comma?"* 까지 붙는다(`{1, 2}[0]` 을 `{1, (2)[0]}` 로 쓰려던 것 아니냐는 뜻).
**예외가 나기 전에 경고가 먼저** 나오므로, `try/except` 로 감싸도 경고는 그대로 보인다.

**중복 제거 — 순서를 지켜야 하면 set 이 아니다**

```python
print("list(set) 로 중복 제거 :", sorted(set([3, 1, 2, 1])), " <- sorted 로 못 박았다")
print("순서를 지키려면        :", list(dict.fromkeys([3, 1, 2, 1])))
print("dict.fromkeys 의 값    :", dict.fromkeys([3, 1, 2, 1]))
```

```text
list(set) 로 중복 제거 : [1, 2, 3]  <- sorted 로 못 박았다
순서를 지키려면        : [3, 1, 2]
dict.fromkeys 의 값    : {3: None, 1: None, 2: None}
```

★ **`dict.fromkeys` 가 「순서를 지키는 중복 제거」의 관용구다** — dict 가 **삽입 순서를 보장**하기 때문에 성립한다([12번](../12-dict-and-key-requirements/2-summary.md)).
**3.7 이전에는 이 관용구가 성립하지 않았다.**

## 어디서 틀리나

### (1) `list(set(...))` 의 순서에 기댄다

**실행마다 달라진다**(문자열일 때). 테스트 기댓값·로그·파일 출력이 흔들린다.\
고치는 법: `sorted(...)` 로 못 박거나 `dict.fromkeys(...)` 로 삽입 순서를 지킨다.

### (2) 「한 판에서 안 갈렸으니 순서가 있다」로 적는다

★ **정수 집합은 시드에 안 갈린다.** 그렇다고 보장이 아니다 — **넣은 순서가 다르면 갈린다**(`{1,9}` 대 `{9,1}`).

### (3) `{}` 를 빈 집합으로 쓴다

**빈 dict** 다. `set()` 이라고 써야 한다.

### (4) `<=` 를 크기 비교로 읽는다

**부분집합**이다. 겹치지 않는 두 집합은 `<`·`==`·`>` 가 **전부 `False`** 다.

### (5) 집합이 든 리스트를 정렬한다

**에러가 안 나고 결과가 틀린다.** 문서가 *"undefined"* 라고 적는다. `key=` 를 줘야 한다.

### (6) `set("abc") & "cbs"` 를 쓴다

**연산자는 집합만** 받는다. 문서가 *"error-prone constructions"* 를 막으려고 일부러 그렇게 했다고 적는다.

### (7) `s |= [4]` 를 쓴다

**`update()`** 를 써야 한다. dict 의 `|=` 와 규칙이 다르다.

### (8) 집합을 집합의 원소로 넣는다

`frozenset` 으로 얼려야 한다. **찾을 때는 `set` 을 그대로 줘도 된다**(임시 frozenset 을 만들어 준다).

### (9) 원소를 넣은 뒤 고친다

**같은 값이 둘 들어간다.** 예외가 없다.

### (10) `pop()` 이 첫 원소를 준다고 믿는다

**임의의** 원소다. 문서가 그렇게 적는다.

### (11) `1`·`True` 를 다른 원소로 안다

**하나로 합쳐지고 처음 것이 남는다.** 타입까지 바뀐다.

### (12) 「집합이 빠르다」를 무조건으로 믿는다

**찾는 자리에 달렸다.** 앞쪽 원소를 찾으면 리스트가 빠르다. 만드는 비용도 든다.

## 구현 세부사항 대 언어 보장

세 층으로 가른다. ★ **이 주제는 「보장이 없다는 것이 보장」인 드문 자리다** — 순서는 **명세가 없음을 명시**한 것이고,
「이 판에서 어떤 순서가 나오나」는 통째로 관찰이다.

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **언어 보장** | 라이브러리 레퍼런스가 정한 것 | 공식 문서 문장을 열어서 인용 |
| **CPython 구현** | 이 구현이 그렇게 하는 것 | `dis`·실행 |
| **이 판·이 머신의 관찰** | 3.12.3 에서 그랬을 뿐 | **시드를 바꿔 던져서** 확인 |

### 언어 보장

| 사실 | 근거 |
|---|---|
| **집합은 순서가 없다** — 위치도 삽입 순서도 기록하지 않는다 | Set Types 첫 문단 |
| 그래서 **첨자·슬라이스가 없다** | 〃 |
| **원소는 해시 가능해야** 한다 | 〃 (*"like dictionary keys, must be hashable"*) |
| **`set` 은 가변이라 해시가 없고 원소·키가 못 된다** · **`frozenset` 은 된다** | 〃 |
| `__contains__`·`remove`·`discard` 의 인자로는 **`set` 을 줘도 된다**(임시 frozenset) | 〃 |
| **연산자는 집합만, 비연산자 메서드는 아무 이터러블** | 〃 (*"require their arguments to be sets"*) |
| **`<=`·`<`·`>=`·`>` 는 부분집합 관계**이고 **전순서가 아니다** | 〃 |
| 그래서 **집합 리스트의 `sort()` 결과는 정의되지 않는다** | 〃 (*"undefined"*) |
| **섞어 쓰면 첫 피연산자의 타입**이 나온다 | 〃 |
| `set` 과 `frozenset` 은 **원소로 비교**된다(`set('abc') == frozenset('abc')`) | 〃 |
| `pop()` 은 **임의의** 원소를 뺀다 · 빈 집합이면 `KeyError` | 〃 |
| `remove` 는 없으면 `KeyError` · `discard` 는 조용 | 〃 |
| **str·bytes 의 해시만** 무작위화된다 | PYTHONHASHSEED |

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| **`x in {1, 2, 3}` 의 리터럴이 `frozenset` 상수로 컴파일된다** | `dis` — 실행 중에 집합을 안 만든다 |
| **`s = {1, 2, 3}` 도 `BUILD_SET` + `SET_UPDATE`(frozenset 상수)** | `dis` |
| **`x in [1, 2, 3]` 은 튜플 상수**가 된다 | `dis` |
| 순회 중 변경 검사가 **크기만 본다** | 실행([12번](../12-dict-and-key-requirements/2-summary.md)의 dict 와 같은 성질) |
| `CONTAINS_OP`·`SET_UPDATE` 같은 **명령 이름** | `dis` — 3.11.15 에서는 뒤쪽 점프 명령이 달랐다 |
| 예외 **문구** 전부 | 실행 |

```python
import dis
print("===== 소스: if x in {1, 2, 3}: pass =====")
dis.dis(compile("if x in {1, 2, 3}: pass", "<inset>", "exec"))
print("===== 소스: if x in [1, 2, 3]: pass =====")
dis.dis(compile("if x in [1, 2, 3]: pass", "<inlist>", "exec"))
```

```text
===== 소스: if x in {1, 2, 3}: pass =====
  0           0 RESUME                   0

  1           2 LOAD_NAME                0 (x)
              4 LOAD_CONST               0 (frozenset({1, 2, 3}))
              6 CONTAINS_OP              0
              8 POP_JUMP_IF_FALSE        1 (to 12)
             10 RETURN_CONST             1 (None)
        >>   12 RETURN_CONST             1 (None)
===== 소스: if x in [1, 2, 3]: pass =====
  0           0 RESUME                   0

  1           2 LOAD_NAME                0 (x)
              4 LOAD_CONST               0 ((1, 2, 3))
              6 CONTAINS_OP              0
              8 POP_JUMP_IF_FALSE        1 (to 12)
             10 RETURN_CONST             1 (None)
        >>   12 RETURN_CONST             1 (None)
```

★ **`{1, 2, 3}` 이 `frozenset` 상수로 접혔다** — 멤버십 검사에 쓰이면 **실행 중에 집합을 만들지 않는다.**
`[1, 2, 3]` 은 **튜플**이 된다(리스트를 안 만든다). 둘 다 **구현의 최적화**이지 보장이 아니다.

### 이 판(3.12.3)·이 머신의 관찰

| 관찰 | 어디가 흔들리나 |
|---|---|
| `PYTHONHASHSEED=0` 일 때 문자열 집합의 순서 | **시드마다 다르다**(0·1·2 로 확인) |
| 시드 미지정일 때의 순서 | **같은 명령을 세 번 돌려도 매번 다르다** |
| **정수 집합의 순서가 시드에 안 갈리는 것** | 시드는 안 타지만 **넣은 순서는 탄다** |
| `{1, 9}` 대 `{9, 1}` 의 차례가 다른 것 | 충돌 해결 순서 — 구현 |
| `getsizeof(set(range(n)))` — n=0/1/5/10 이 **216 / 216 / 728 / 728** | 빌드·비트 폭·재해시 시점 |
| `s.pop()` 이 `1` 을 준 것 | **임의**다. 보장이 아니다 |
| `in` 비교 수치(약 20ns 대 최대 75만ns) | 머신·부하. **기울기만** 재현된다 |

```bash
for i in 1 2 3; do python3 -c 'print(list({"apple","banana","cherry","date","elderberry"}))'; done
```

```text
['banana', 'apple', 'elderberry', 'cherry', 'date']
['elderberry', 'banana', 'date', 'cherry', 'apple']
['elderberry', 'cherry', 'banana', 'date', 'apple']
```

★ **시드를 안 주면 같은 명령이 세 번 다 다르다.** 「버전이 아니라 실행마다」 바뀐다 —
**세 판을 비교하지 않으면 우연히 같은 값이 나와 「보장된다」로 오해한다.**\
★ **위 세 줄은 지금 다시 돌리면 또 다른 값이 나온다** — 재현되지 않는 것이 이 블록의 결론이므로
이 세 줄만은 「다시 던져 대조」의 대상이 아니다. 대조할 것은 「**세 줄이 서로 다르다**」는 성질이다.

**3.11.15 로 대조한 결과**

```bash
for seed in 0 1; do PYTHONHASHSEED=$seed python3.11 -c \
  'print(list({"apple","banana","cherry","date","elderberry"}), list({1,2,3,4,5,100,200}))'; done
```

```text
['banana', 'apple', 'cherry', 'date', 'elderberry'] [1, 2, 3, 4, 5, 100, 200]
['date', 'elderberry', 'cherry', 'apple', 'banana'] [1, 2, 3, 4, 5, 100, 200]
```

★★ **3.11 과 3.12 가 같은 시드에서 한 글자도 같았다.** 그래서 **더 위험하다** —
두 판이 같다고 「버전에 안 흔들린다」로 적으면 안 된다.
**같은 해시 알고리즘과 같은 테이블 배치를 쓰고 있을 뿐**이고, 둘 다 **보장이 아닌 관찰**이다.

### 그래서 이렇게 적으면 틀린다

- ✗ 「set 은 정렬된 순서로 돈다」\
  ○ **순서가 없다.** 작은 정수가 우연히 오름차순처럼 보일 뿐이다.
- ✗ 「정수 집합은 순서가 보장된다」\
  ○ **시드에 안 갈릴 뿐**이다. `{1,9}` 와 `{9,1}` 은 차례가 다르다.
- ✗ 「한 판에서 안 갈렸으니 안정적이다」\
  ○ **시드를 바꿔 던져야** 안다. 시드를 안 주면 실행마다 다르다.
- ✗ 「`{}` 는 빈 집합」 → **빈 dict** 다.
- ✗ 「`<=` 는 크기 비교」 → **부분집합**이다. 셋 다 `False` 인 쌍이 있다.
- ✗ 「집합 리스트를 정렬하면 에러가 난다」 → **안 난다.** 결과가 정의되지 않을 뿐이다.
- ✗ 「`|` 에 리스트를 넘겨도 된다」 → **집합만**이다. `.union()` 은 받는다.
- ✗ 「set 의 `|=` 는 dict 처럼 이터러블을 받는다」 → **안 받는다.** `update()` 를 쓴다.
- ✗ 「set 을 다른 set 에 넣을 수 있다」 → **`frozenset` 으로 얼려야** 한다.
- ✗ 「`frozenset` 은 `set` 과 다른 값이다」 → **원소로 비교**한다. `==` 가 `True` 다.
- ✗ 「`pop()` 은 첫 원소」 → **임의**다.
- ✗ 「집합은 언제나 빠르다」 → **찾는 자리와 만드는 비용**에 달렸다.

**판정 기준 한 줄**: 순서를 물으면 **「시드를 바꿔 던져 봤나」**, 비교를 물으면 「**크기가 아니라 포함이다**」를 보라.

## 언제 쓰고 언제 안 쓰나

| 쓰는 것 | 상황 |
|---|---|
| `set(xs)` | **포함 검사**를 여러 번 할 때 · 중복을 없애고 **순서가 상관없을 때** |
| `a & b` · `a - b` | 두 묶음의 공통·차이를 구할 때 |
| `a <= b` | 「필요한 권한을 다 갖고 있나」 |
| `a.isdisjoint(b)` | 「겹치는 게 하나도 없나」 — `not (a & b)` 보다 빠르고 뜻이 분명하다 |
| `frozenset(tags)` | **순서를 무시한 묶음**을 dict 키로 쓸 때 · 집합의 집합 |
| `.union(it)` · `.update(it)` | 오른쪽이 리스트·문자열일 때 |
| `sorted(s)` | **출력·로그·테스트**에 집합을 실을 때(반드시) |
| `dict.fromkeys(xs)` | **순서를 지키며** 중복 제거할 때([12번](../12-dict-and-key-requirements/2-summary.md)) |

**안 쓰는 자리**는 넷이다.\
**순서가 중요한 곳에 set 을 쓰지 마라** — 보장이 없다.\
**집합이 든 리스트를 그냥 정렬하지 마라** — 결과가 정의되지 않는다.\
**가변 객체를 원소로 쓰지 마라** — 고치면 같은 값이 둘이 된다.\
**한 번만 찾을 것을 위해 집합을 만들지 마라** — 만드는 비용이 찾는 비용보다 크다.

## 핵심 문장

- **set 은 dict 에서 값과 순서줄을 뺀 것**이다. 그래서 **순서가 없고** `PYTHONHASHSEED` 에 **갈린다.**
- **갈리는 것은 str·bytes 뿐**이다 — 정수 해시는 값 그 자체다. **그래도 보장은 아니다**(`{1,9}` ≠ 차례 `{9,1}`).
- **원소 요건은 dict 키와 같다.** `set` 은 가변이라 원소가 못 되고 **`frozenset` 은 된다** — 다만 **찾을 때는 `set` 을 줘도 된다.**
- **`<=` 는 크기가 아니라 포함**이다. 겹치지 않는 두 집합은 `<`·`==`·`>` 가 **전부 `False`** 다.
- **집합 리스트의 정렬 결과는 정의되지 않는다** — 문서가 그렇게 적는다. **에러가 안 나는 것이 가장 나쁘다.**
- **연산자는 집합만, 메서드는 아무 이터러블.** 이 비대칭은 실수를 막으려고 **일부러** 만든 것이다.
- **섞어 쓰면 첫 피연산자의 타입**이 나오고, **`set == frozenset` 은 원소로 비교**한다.
- **`x in {1,2,3}` 은 실행 중에 집합을 안 만든다**(frozenset 상수) — **구현의 최적화**다.

## 관련 자료

- 목록: [python/syntax 주제 목록](../README.md) — 이 주제는 **13번**
- 선행: [12-dict-and-key-requirements](../12-dict-and-key-requirements/2-summary.md) — **해시·키 요건·`__hash__` 계약의 정본.**\
  **경계**: 그쪽은 「무엇이 키가 되나」와 **삽입 순서 보장**까지, 여기는 **「순서가 없다는 것」과 집합 연산**부터다.
- 선행: [11-tuple-and-unpacking](../11-tuple-and-unpacking/2-summary.md) — 튜플이 원소가 되는 조건. `namedtuple` 이 평범한 튜플과 한 원소가 되는 것.
- 선행: [10-list-methods-and-sort-key](../10-list-methods-and-sort-key/2-summary.md) — **정렬의 정본.**
  「집합이 든 리스트를 정렬한다」의 결론을 여기서 문서 근거로 이어받는다.
- 선행: [03-mutability-and-copying](../03-mutability-and-copying/2-summary.md) — `frozenset` 의 복사가 자기 자신이 아닌 것.
- 이어지는 곳: [14-comprehensions](../14-comprehensions/2-summary.md) — 집합 컴프리헨션.
- 이어지는 곳: [목록의 **30번 주제**](../30-repr-eq-hash-contracts/) 「`__repr__`·`__eq__`·`__hash__` 계약」 — **집합 원소로 쓸 클래스 설계의 정본.**
- 이어지는 곳: [목록의 **43번 주제**](../43-collections/) 「`collections`」 — `Counter` 가 「중복을 세는」 쪽이다.
- 이어지는 곳: [목록의 **47번 주제**](../47-json/) 「`json`」 — **set 은 JSON 으로 못 나간다**(리스트로 바꿔야 한다).
- 원리: [`cs/data-structure/`](../../../../../data-structure/) — 해시 집합의 원리·충돌 해결·부하율은 그쪽이 정본이다.\
  **경계**: 그쪽은 **왜 평균 O(1) 인가**까지, 여기는 **그래서 파이썬 코드에서 무엇이 되고 안 되나**부터다.
- 기존 노트: [`cs/foundations/python-basics/`](../../../../python-basics/) — 집합을 「이렇게 쓴다」까지 다룬다.\
  **경계**: 그쪽은 메서드 사용 예시까지, 여기는 「**순서를 누가 보장 안 하고 무엇이 원소가 되나**」부터다.
- 공식 문서: [Set Types](https://docs.python.org/3.12/library/stdtypes.html#set-types-set-frozenset) · [hashable](https://docs.python.org/3.12/glossary.html#term-hashable) · [PYTHONHASHSEED](https://docs.python.org/3.12/using/cmdline.html#envvar-PYTHONHASHSEED)

## 용어 풀이

- **집합(set)**: 중복이 없고 **순서가 없는** 해시 가능한 원소들의 모음. 가변이라 **해시가 없다.**
- **`frozenset`**: 불변인 집합. **해시가 있어** dict 키·다른 집합의 원소가 될 수 있다.
- **부분집합(subset)**: `a <= b` — a 의 원소가 전부 b 에 있는 것. **진부분집합**은 `a < b`(게다가 같지 않다).
- **부분 순서(partial order)**: 어느 쪽이 큰지 **정할 수 없는 쌍이 있는** 순서. 집합의 포함 관계가 그렇다.
- **대칭차(symmetric difference)**: `a ^ b` — 둘 중 **한쪽에만** 있는 것.
- **서로소(disjoint)**: 겹치는 원소가 하나도 없는 것. `a.isdisjoint(b)`.
- **해시 무작위화(hash randomization)**: **str·bytes** 의 해시에 매 프로세스 무작위 소금을 섞는 것(3.2.3+, **3.3 부터 기본 켜짐**).
  `PYTHONHASHSEED` 로 고정하고, `0` 을 주면 아예 끈다.
- **상수 접기(constant folding)**: 컴파일 때 계산해 상수로 박아 두는 것. `x in {1,2,3}` 의 집합 리터럴이 그렇게 된다.

## 더 들어가면

- **왜 문자열만 무작위화하나** — 문서가 이유를 적는다: 악의적 입력으로 dict 생성을 **O(n²)** 로 만드는 DoS 방어다.
  공격 입력은 대개 문자열이므로 **정수는 대상이 아니다.** 그래서 **정수 집합은 시드에 안 갈린다.**
- **`-R` 옵션은 「켜는」 스위치가 아니라 「도로 켜는」 스위치다** — 무작위화는 **3.3 부터 기본으로 켜져 있다.**
  던져 본 것은 동작 1 의 「끄고 도로 켜기」에 있다.
- **`Counter`** 는 「중복을 세는」 쪽이다([목록의 **43번 주제**](../43-collections/)). 집합은 **있나 없나**만 안다.
- **`collections.abc.Set`** 은 「집합처럼 구는 것」의 프로토콜이다([목록의 **35번 주제**](../35-abc-and-protocol/)).
  `dict.keys()` 가 그 프로토콜을 따르기 때문에 `d.keys() & {...}` 가 되는 것이다([12번](../12-dict-and-key-requirements/2-summary.md)).
- **집합에 순서를 주고 싶으면** 표준 라이브러리에 `OrderedSet` 이 없다 — `dict.fromkeys()` 가 관용구다.
