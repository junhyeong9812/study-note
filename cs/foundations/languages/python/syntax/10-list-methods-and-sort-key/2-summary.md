# python/syntax/10-list-methods-and-sort-key — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만.
> - [Lists — `list.sort`](https://docs.python.org/3.12/library/stdtypes.html#list.sort) — `key`·`reverse`·안정성·CPython 주
> - [`sorted`](https://docs.python.org/3.12/library/functions.html#sorted) — 새 리스트를 돌려주는 쪽
> - [Mutable Sequence Types](https://docs.python.org/3.12/library/stdtypes.html#mutable-sequence-types) — `append`·`extend`·`remove`·`pop`·`+=` 의 정의
> - [Sorting Techniques](https://docs.python.org/3.12/howto/sorting.html) — 정렬 HOW TO
> - [Set Types](https://docs.python.org/3.12/library/stdtypes.html#set-types-set-frozenset) — 「집합 리스트의 `sort` 결과는 정의되지 않는다」
>
> **실행 검증** — 이 문서에 실린 출력은 전부 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> **버전** — `sort`/`sorted` 의 `key`·`reverse`·안정성은 Python 3 전체 공통. 비교 횟수·`getsizeof` 값은 **이 판의 관찰**이다.
> **선행** — [09-sequence-ops-and-slicing](../09-sequence-ops-and-slicing/2-summary.md)(슬라이스·`[:]`·`*`·`+` 의 정본) ·
> [01-object-and-name-binding](../01-object-and-name-binding/2-summary.md)(`+=` 가 같은 객체를 바꾼다는 것) ·
> [03-mutability-and-copying](../03-mutability-and-copying/2-summary.md)(얕은 복사).

## 한눈에 — 쉽게 말하면

**`sort` 는 「방을 치우는 것」이고 `sorted` 는 「치운 사진을 새로 찍는 것」이다.**\
치우는 사람에게 「치운 방을 줘」라고 하면 아무것도 못 받는다 — 그래서 `x = lst.sort()` 는 `None` 이다.

```text
  lst.sort()                         sorted(lst)
  +-------------------+              +-------------------+
  | lst 를 제자리에서   |              | lst 는 그대로 두고  |
  | 줄 세운다          |              | 새 list 를 만든다   |
  +-------------------+              +-------------------+
        |                                   |
        v                                   v
     돌려주는 것: None                 돌려주는 것: 새 list

  x = lst.sort()   ->  x 는 None       x = sorted(lst)  ->  x 는 정렬된 사본
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 방을 치운다 | `lst.sort()` | 돌려주는 것이 **`None`** |
| 사진을 새로 찍는다 | `sorted(lst)` | 원본이 그대로 |
| 물건마다 붙이는 이름표 | `key` 함수 | 원소당 **정확히 한 번** 불린다 |
| 같은 이름표끼리는 원래 줄 순서 | **안정 정렬** | 문서가 *"guaranteed to be stable"* 이라고 적는다 |
| 줄을 통째로 거꾸로 세운다 | `reverse=True` | 동점 무리 **안의** 순서는 안 뒤집힌다 |
| 사진을 뒤집어 본다 | `sorted(...)[::-1]` | 동점 무리 **안까지** 뒤집힌다 |
| 생김새로 찾아 버린다 | `list.remove(x)` | `==` 로 찾는다 — `True` 로 `1` 을 지운다 |
| 몇 번째 자리를 비운다 | `del lst[i]` · `lst.pop(i)` | 자리로 지운다 |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.\
「**정렬했는데 `None` 이 응답으로 나갔다**」가 그것이다. `return items.sort()` 한 줄이면 끝난다.
에러는 그 자리에서 안 나고, 그 값을 **쓰는 곳**에서 `'NoneType' object is not subscriptable` 로 뒤늦게 터진다.

> **제자리(in place)** — 새 객체를 만들지 않고 원래 객체의 내용을 바꾸는 것.\
> 그래서 그 객체를 가리키는 **다른 이름에서도 변화가 보인다**([01번](../01-object-and-name-binding/2-summary.md)).

## 이 주제가 답하려는 질문

1. **무엇이 `None` 을 돌려주고 무엇이 값을 돌려주는가** — 그리고 왜 그렇게 정했는가.
2. **`key` 는 몇 번 불리는가** — 그것이 보장인가 관찰인가. `cmp_to_key` 와 무엇이 다른가.
3. **안정 정렬은 무엇을 약속하는가** — `reverse=True` 와 「뒤집기」가 왜 다른가.

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 문장으로 읽는다.

### 1. ★ 바꾸는 메서드는 `None` 을 돌려준다

**언제 쓰나** — 리스트를 건드리는 모든 자리. 그리고 그 결과를 변수에 받으려 할 때마다.

문서가 이유까지 적어 두었다 —\
*"This method modifies the sequence in place for economy of space when sorting a large sequence. **To remind users that it operates by side effect, it does not return the sorted sequence** (use `sorted()` to explicitly request a new sorted list instance)."*

```text
 "돌려주는 것" 으로 두 무리를 가른다

  바꾸는 것(제자리)            ->  None
   sort  reverse  append  extend  insert  remove  clear

  꺼내는 것 / 새로 만드는 것    ->  값
   pop -> 꺼낸 원소            index -> 자리
   count -> 개수               copy -> 새 리스트
   sorted(...) -> 새 리스트
```

```python
x = [3, 1, 2]
for call in ("x.sort()", "x.append(9)", "x.extend([8])", "x.insert(0, 7)",
             "x.remove(7)", "x.reverse()", "x.clear()"):
    print(f"{call:15} ->", repr(eval(call)))
y = [3, 1, 2]
print(f"{'y.pop()':15} ->", repr(y.pop()), "| y =", y)
print(f"{'y.copy()':15} ->", repr(y.copy()))
print(f"{'sorted(y)':15} ->", repr(sorted(y)), "| y =", y)
```

```text
x.sort()        -> None
x.append(9)     -> None
x.extend([8])   -> None
x.insert(0, 7)  -> None
x.remove(7)     -> None
x.reverse()     -> None
x.clear()       -> None
y.pop()         -> 2 | y = [3, 1]
y.copy()        -> [3, 1]
sorted(y)       -> [1, 3] | y = [3, 1]
```

**★ 그래서 조용한 실패가 난다**

```python
words = ["pear", "fig", "apple"]
res = words.sort()
print("res = words.sort() ->", repr(res), "| words =", words)
try:
    res[0]
except TypeError as e:
    print("res[0]          ->", type(e).__name__, e)
try:
    ["b", "a"].sort().reverse()
except AttributeError as e:
    print("sort().reverse()->", type(e).__name__, e)
```

```text
res = words.sort() -> None | words = ['apple', 'fig', 'pear']
res[0]          -> TypeError 'NoneType' object is not subscriptable
sort().reverse()-> AttributeError 'NoneType' object has no attribute 'reverse'
```

그림 해설.

- ★ **`words.sort()` 줄에서는 에러가 안 난다.** 정렬도 제대로 됐다 — 틀린 것은 **받은 값**뿐이다.
- 터지는 자리는 `res` 를 **쓰는 곳**이다. 호출한 줄과 터지는 줄이 멀어지는 것이 이 함정의 값이다.
- **메서드 체인이 안 된다.** `lst.sort().reverse()` 는 `None.reverse()` 다.
- `pop` 만 값을 돌려주는 이유는 **꺼내 오는 것**이 그 메서드의 목적이기 때문이다.

**비용** — 큰 리스트를 복사하지 않아 메모리를 아낀다.\
대신 **원본이 바뀌고**, 결과를 받으려던 코드가 `None` 을 받는다.

### 2. ★ `key` 는 원소당 정확히 한 번 불린다 — 문서가 그렇게 정한다

**언제 쓰나** — 원소 자체가 아니라 「원소에서 뽑은 무엇」으로 줄 세울 때.

문서의 문장이 곧 보장이다 —\
*"`key` specifies a function of one argument that is used to extract a comparison key from each list element... **The key corresponding to each item in the list is calculated once and then used for the entire sorting process.**"*

```text
 sorted(data, key=f) 가 하는 일

   1) 원소마다 f 를 "한 번씩" 불러 이름표를 만든다     <- n 번
        [("김",3), ("이",1)]  --f-->  [3, 1]
   2) 그 이름표들끼리 "<" 로 비교하며 줄 세운다        <- 약 n log n 번
   3) 줄 세운 결과는 "원소" 로 돌려준다 (이름표가 아니다)
```

세어 보면 그대로다.

```python
def count_key(data, label):
    calls = []
    def k(x):
        calls.append(x)
        return x
    sorted(data, key=k)
    print(f"{label:22} n={len(data):3}  key 호출 {len(calls):3}회  호출 순서가 원본 순서인가: {calls == list(data)}")

count_key([3, 1, 2], "무작위 3개")
count_key(list(range(10)), "이미 정렬된 10개")
count_key(list(range(10))[::-1], "역순 10개")
count_key([1] * 50, "전부 같은 값 50개")
count_key([], "빈 리스트")
```

```text
무작위 3개               n=  3  key 호출   3회  호출 순서가 원본 순서인가: True
이미 정렬된 10개           n= 10  key 호출  10회  호출 순서가 원본 순서인가: True
역순 10개                n= 10  key 호출  10회  호출 순서가 원본 순서인가: True
전부 같은 값 50개          n= 50  key 호출  50회  호출 순서가 원본 순서인가: True
빈 리스트                 n=  0  key 호출   0회  호출 순서가 원본 순서인가: True
```

**★ 비교 횟수는 다르다 — 그쪽은 데이터에 달렸고 보장도 아니다**

```python
class Probe:
    lt = 0
    def __init__(self, v): self.v = v
    def __lt__(self, other):
        Probe.lt += 1
        return self.v < other.v

import random
random.seed(0)
d = [random.randrange(1000) for _ in range(100)]
for n, data in (("정렬된 10", list(range(10))), ("역순 10", list(range(10))[::-1]),
                ("무작위 100", d)):
    Probe.lt = 0
    sorted([Probe(v) for v in data])
    print(f"{n:12} -> __lt__ {Probe.lt}회")
```

```text
정렬된 10       -> __lt__ 9회
역순 10        -> __lt__ 9회
무작위 100      -> __lt__ 532회
```

★ **이미 정렬된 10개와 역순 10개가 똑같이 9회**다 — 구현이 「이어진 오름차순·내림차순 구간」을 알아본다는 뜻이다.
**이 수치는 보장이 아니라 이 구현의 관찰**이다. `key` 호출 횟수만 문서가 약속한다.

**★ `cmp_to_key` 와 대비하면 차이가 보인다**

```python
import functools, random
random.seed(1)
data = [random.randrange(1000) for _ in range(100)]

kcalls = []
def k(x):
    kcalls.append(x); return x
sorted(data, key=k)

def cmp(a, b):
    cmp.n += 1
    return (a > b) - (a < b)
cmp.n = 0
sorted(data, key=functools.cmp_to_key(cmp))

print(f"key=k           -> 함수 호출 {len(kcalls)}회  (원소 {len(data)}개)")
print(f"cmp_to_key(cmp) -> cmp 호출 {cmp.n}회")
```

```text
key=k           -> 함수 호출 100회  (원소 100개)
cmp_to_key(cmp) -> cmp 호출 539회
```

그림 해설.

- **`key` 는 「원소당 한 번」이고 `cmp` 는 「비교할 때마다」다.** 그래서 비싼 계산일수록 `key` 쪽이 유리하다.
- ★ **`key` 호출 순서는 원본 순서**였다 — 다섯 경우 전부. 다만 **그 순서는 문서가 약속한 것이 아니다**(횟수만 약속한다).
- `cmp_to_key` 가 필요한 때는 **「두 원소를 봐야만 정해지는 순서」**뿐이다. 한 원소에서 뽑을 수 있으면 `key` 가 맞다.

**비용** — `key` 는 이름표 n 개를 **메모리에 들고** 있는 대신 계산을 n 번으로 끝낸다.\
`cmp_to_key` 는 메모리를 덜 쓰는 대신 **비교마다** 파이썬 함수를 부른다.

### 3. ★ 안정 정렬은 「언어 보장」이다

**언제 쓰나** — 기준이 둘 이상일 때. 그리고 「동점이면 원래 순서」를 지켜야 할 때.

★ **이것이 이 주제에서 층을 가르는 가장 중요한 자리다.**
「파이썬은 Timsort 를 쓴다」는 **구현**이지만, 「**안정 정렬이다**」는 **문서가 약속한 보장**이다.

- `list.sort` — *"The `sort()` method is **guaranteed to be stable**. A sort is stable if it guarantees not to change the relative order of elements that compare equal — this is helpful for sorting in multiple passes (for example, sort by department, then by salary grade)."*
- `sorted` — *"The built-in `sorted()` function is **guaranteed to be stable**."*

★ **두 문장 다 라이브러리 레퍼런스에 있다.** 알고리즘 이름은 어디에도 없다.

```text
 안정 정렬이 약속하는 것

  원본   a(2)  b(1)  c(2)  d(1)  e(2)
              점수로 정렬
  결과   b(1)  d(1)  a(2)  c(2)  e(2)
         ^^^^^^^^^^  ^^^^^^^^^^^^^^^^
         1점 무리 안에서 b 가 d 보다 앞   <- 원본에서도 b 가 앞이었다
         2점 무리 안에서 a c e 순서       <- 원본 순서 그대로
```

그래서 **여러 번 나눠 정렬**할 수 있다 — 덜 중요한 기준부터 먼저.

```python
people = [("최", "영업", 3), ("김", "개발", 1), ("이", "영업", 1),
          ("박", "개발", 3), ("정", "개발", 1)]
tmp = sorted(people, key=lambda p: p[0])   # 3순위: 이름
tmp = sorted(tmp, key=lambda p: p[2])      # 2순위: 등급
tmp = sorted(tmp, key=lambda p: p[1])      # 1순위: 부서
print("세 번 나눠 :", tmp)
print("튜플 키 한 번:", sorted(people, key=lambda p: (p[1], p[2], p[0])))
```

```text
세 번 나눠 : [('김', '개발', 1), ('정', '개발', 1), ('박', '개발', 3), ('이', '영업', 1), ('최', '영업', 3)]
튜플 키 한 번: [('김', '개발', 1), ('정', '개발', 1), ('박', '개발', 3), ('이', '영업', 1), ('최', '영업', 3)]
```

그림 해설.

- **덜 중요한 기준을 먼저** 돌린다. 마지막에 돌린 기준이 가장 세다.
- 튜플 키 한 번이면 같은 결과다 — **키를 만들 수 있으면 튜플 쪽이 싸다**(정렬이 한 번뿐).
- 나눠 정렬이 필요한 때는 **기준마다 방향이 다를 때**다(다음 절).

**비용** — 안정성이 보장되니 「원래 순서」를 보조 키로 따로 만들 필요가 없다.\
대신 나눠 정렬하면 **정렬을 여러 번** 하게 된다.

### 4. ★ `reverse=True` 와 「정렬한 뒤 뒤집기」는 다르다

**언제 쓰나** — 내림차순이 필요할 때. 세 가지 방법이 있고 **하나만 다르다.**

문서가 `reverse` 를 이렇게 정의한다 — *"`reverse` is a boolean value. If set to `True`, then the list elements are sorted **as if each comparison were reversed**."*\
★ **「비교를 뒤집는다」이지 「결과를 뒤집는다」가 아니다.** 안정성은 그대로 유지된다.

```text
 원본   a(2)  b(1)  c(2)  d(1)  e(2)

 reverse=True          ->  a(2) c(2) e(2) | b(1) d(1)
 key=lambda r: -r[1]   ->  a(2) c(2) e(2) | b(1) d(1)      <- 같다
 sorted(...)[::-1]     ->  e(2) c(2) a(2) | d(1) b(1)      <- 동점 무리 "안" 까지 뒤집혔다
                           ^^^^^^^^^^^^^
                           원본의 a c e 가 e c a 로 뒤집혔다
```

```python
rows = [("a", 2), ("b", 1), ("c", 2), ("d", 1), ("e", 2)]
print("원본           :", rows)
print("key=점수       :", sorted(rows, key=lambda r: r[1]))
print("reverse=True   :", sorted(rows, key=lambda r: r[1], reverse=True))
print("key=-점수      :", sorted(rows, key=lambda r: -r[1]))
print("정렬 뒤 [::-1] :", sorted(rows, key=lambda r: r[1])[::-1])
```

```text
원본           : [('a', 2), ('b', 1), ('c', 2), ('d', 1), ('e', 2)]
key=점수       : [('b', 1), ('d', 1), ('a', 2), ('c', 2), ('e', 2)]
reverse=True   : [('a', 2), ('c', 2), ('e', 2), ('b', 1), ('d', 1)]
key=-점수      : [('a', 2), ('c', 2), ('e', 2), ('b', 1), ('d', 1)]
정렬 뒤 [::-1] : [('e', 2), ('c', 2), ('a', 2), ('d', 1), ('b', 1)]
```

★ **`reverse=True` 와 `key=-점수` 는 같은 답을 냈다.** 둘 다 안정성을 유지하기 때문이다.\
갈리는 것은 **`[::-1]`** 쪽 하나뿐이다 — 이것만 **동점 무리 안의 순서까지 뒤집는다.**

> ★ **이 절은 처음 세운 예상이 틀린 자리다.** 「`reverse=True` 와 키를 음수로 뒤집는 것은 안정성 때문에 다르다」로
> 적으려다 실제로 돌려 보니 **둘이 같았다.** 다른 것은 세 번째(`[::-1]`)였다.

**★ 그래서 「부서는 오름, 등급은 내림」은 `reverse` 로 못 한다**

```python
people = [("최", "영업", 3), ("김", "개발", 1), ("이", "영업", 1),
          ("박", "개발", 3), ("정", "개발", 1)]
print("reverse=True 통째로 :", sorted(people, key=lambda p: (p[1], p[2]), reverse=True))
print("등급만 음수로       :", sorted(people, key=lambda p: (p[1], -p[2])))
print("두 번 나눠(등급 먼저):", sorted(sorted(people, key=lambda p: p[2], reverse=True),
                                      key=lambda p: p[1]))
```

```text
reverse=True 통째로 : [('최', '영업', 3), ('이', '영업', 1), ('박', '개발', 3), ('김', '개발', 1), ('정', '개발', 1)]
등급만 음수로       : [('박', '개발', 3), ('김', '개발', 1), ('정', '개발', 1), ('최', '영업', 3), ('이', '영업', 1)]
두 번 나눠(등급 먼저): [('박', '개발', 3), ('김', '개발', 1), ('정', '개발', 1), ('최', '영업', 3), ('이', '영업', 1)]
```

그림 해설.

- `reverse=True` 는 **모든 기준을 함께** 뒤집는다 — 부서까지 내림차순이 됐다.
- **기준마다 방향이 다르면** ① 숫자면 키를 음수로 ② 아니면 **나눠 정렬**(안정성에 기댄다) 둘뿐이다.
- 문자열은 음수로 못 만든다 — 그래서 **문자열이 섞이면 나눠 정렬이 유일한 방법**이다.

**비용** — `reverse=True` 는 사본을 안 만든다.\
`[::-1]` 은 **리스트를 한 벌 더 만들고**, 동점 순서까지 뒤집어 놓는다.

### 5. ★ 정렬 중의 리스트는 「비어 보인다」 — CPython 구현

**언제 쓰나** — `key` 함수가 그 리스트를 들여다보거나 건드릴 때. 사고로 그렇게 되기 쉽다.

문서가 **구현 세부사항**으로 못을 박는다 —\
*"**CPython implementation detail:** While a list is being sorted, the effect of attempting to mutate, or even inspect, the list is undefined. The C implementation of Python **makes the list appear empty for the duration**, and raises `ValueError` if it can detect that the list has been mutated during a sort."*

```python
data = [3, 1, 2]
seen = []
def peek(x):
    seen.append(list(data))
    return x
data.sort(key=peek)
print("정렬 중에 본 data :", seen)
print("정렬 뒤 data      :", data)

d2 = [3, 1, 2]
def mutate(x):
    d2.append(99)
    return x
try:
    d2.sort(key=mutate)
except ValueError as e:
    print("d2.sort(key=mutate) ->", type(e).__name__, e)
print("d2 =", d2)
```

```text
정렬 중에 본 data : [[], [], []]
정렬 뒤 data      : [1, 2, 3]
d2.sort(key=mutate) -> ValueError list modified during sort
d2 = [1, 2, 3]
```

그림 해설.

- ★ **`key` 안에서 본 `data` 가 전부 `[]`** 다. 원소가 셋인데 빈 리스트로 보인다.
- 이것은 **버그가 아니라 문서에 적힌 CPython 의 동작**이다. 다른 구현은 다르게 해도 된다.
- 바꾸려 하면 `ValueError` 가 난다 — 다만 문서가 *"if it can detect"* 라고 적는다. **잡아 준다는 보장이 아니다.**
- `sorted` 를 쓰면 이 문제가 없다. 정렬 대상이 **새 리스트**이기 때문이다.

**비용** — C 구현이 리스트 포인터를 잠시 떼어 두어 **정렬 중 재진입이 안전**해진다.\
대신 `key` 안에서 그 리스트를 읽으면 **에러 없이 빈 것이 보인다.**

### 6. ★ `remove` 는 `==` 로 찾고 `del`·`pop` 은 자리로 지운다

**언제 쓰나** — 원소 하나를 뺄 때. 「무엇을」 뺄지와 「어디를」 뺄지가 다른 일이다.

```text
  lst.remove(x)         "x 와 == 인 첫 원소" 를 찾아 지운다
                        없으면 ValueError
  del lst[i]            i 번 자리를 지운다.  문(statement) 이라 값이 없다
  lst.pop(i)            i 번 자리를 지우고 "그 원소를 돌려준다"
  del lst[i:j]          구간을 지운다 (09번)
```

```python
a = [0, 1, 2, True, 1.0]
print("원본         :", a)
a.remove(True)
print("remove(True) :", a, " <- 무엇이 지워졌나")
print("index(True)  :", [0, 1, 2].index(True))
print("count(1)     :", [0, 1, 1.0, True].count(1))
c = [3, 1, 2, 1]
c.remove(1)
print("[3,1,2,1].remove(1) ->", c, " <- 첫 것만")
try:
    [1, 2].remove(9)
except ValueError as e:
    print("remove(9)    ->", type(e).__name__, e)
```

```text
원본         : [0, 1, 2, True, 1.0]
remove(True) : [0, 2, True, 1.0]  <- 무엇이 지워졌나
index(True)  : 1
count(1)     : 3
[3,1,2,1].remove(1) -> [3, 2, 1]  <- 첫 것만
remove(9)    -> ValueError list.remove(x): x not in list
```

그림 해설.

- ★ **`remove(True)` 가 지운 것은 `True` 가 아니라 `1`** 이다. `True == 1` 이고 그게 **앞에 있었기** 때문이다.
- `index`·`count`·`in` 도 전부 `==` 다 — `[0, 1, 1.0, True].count(1)` 이 **3**이다([02번](../02-is-vs-eq-interning/2-summary.md)).
- ★ **12·13번의 「`1`·`1.0`·`True` 가 한 키」와 같은 뿌리**다. 그쪽은 해시까지 같아야 하고, 여기는 `==` 만으로 충분하다.

```python
d = [10, 20, 30, 40]
del d[1]
print("del d[1]   ->", d, "  (문이라 돌려주는 값이 없다)")
e = [10, 20, 30, 40]
print("e.pop(1)   ->", e.pop(1), "| e =", e)
print("e.pop()    ->", e.pop(), "| e =", e)
try:
    [1, 2].pop(9)
except IndexError as ex:
    print("pop(9)     ->", type(ex).__name__, ex)
try:
    g = [1, 2]; del g[9]
except IndexError as ex:
    print("del g[9]   ->", type(ex).__name__, ex)
```

```text
del d[1]   -> [10, 30, 40]   (문이라 돌려주는 값이 없다)
e.pop(1)   -> 20 | e = [10, 30, 40]
e.pop()    -> 40 | e = [10, 30]
pop(9)     -> IndexError pop index out of range
del g[9]   -> IndexError list assignment index out of range
```

- **없는 값이면 `ValueError`, 없는 자리면 `IndexError`** 다. 예외 종류가 「무엇으로 찾았나」를 말해 준다.
- **예외 문구까지 다르다** — `pop index out of range` 와 `list assignment index out of range`.

**비용** — `remove` 는 찾아야 하므로 값을 모를 때 쓴다.\
자리를 알면 `del`·`pop` 이 맞다. **앞쪽 삽입·삭제의 비용은 여기서 다루지 않는다** — 자료구조 갈래가 정본이다.

### 7. ★ `+=` 는 `extend` 와 같은 일을 한다

**언제 쓰나** — 리스트를 이어 붙일 때. `+` 와 `+=` 가 **다른 일**이다.

```text
  lst += other     ->  lst.extend(other)   같은 객체를 늘린다
                       other 는 "아무 이터러블" 이어도 된다

  lst = lst + other ->  새 리스트를 만들어 이름을 다시 묶는다
                        other 는 "list" 여야 한다
```

```python
a = [1, 2]; keep = a
a += "xy"
print("a += 'xy'      ->", a, "| 같은 객체:", a is keep)
b = [1, 2]; keep_b = b
b.extend("xy")
print("b.extend('xy') ->", b, "| 같은 객체:", b is keep_b)
try:
    c = [1, 2]; c = c + "xy"
except TypeError as e:
    print("c = c + 'xy'   ->", type(e).__name__, e)
f = [1, 2]; f += range(3)
print("f += range(3)  ->", f)
e2 = [1, 2]; e2 += {"k": 1}
print("e2 += {'k':1}  ->", e2, " <- dict 는 키만")
```

```text
a += 'xy'      -> [1, 2, 'x', 'y'] | 같은 객체: True
b.extend('xy') -> [1, 2, 'x', 'y'] | 같은 객체: True
c = c + 'xy'   -> TypeError can only concatenate list (not "str") to list
f += range(3)  -> [1, 2, 0, 1, 2]
e2 += {'k':1}  -> [1, 2, 'k'] <- dict 는 키만
```

`dis` 가 보여 주는 것은 **연산 하나의 차이**뿐이고, 갈리는 것은 그 연산의 의미다.

```python
import dis
def plus_eq(x): x += [1]
def plus(x): x = x + [1]
dis.dis(plus_eq)
print("-----")
dis.dis(plus)
```

```text
  1           0 RESUME                   0
              2 LOAD_FAST                0 (x)
              4 LOAD_CONST               1 (1)
              6 BUILD_LIST               1
              8 BINARY_OP               13 (+=)
             12 STORE_FAST               0 (x)
             14 RETURN_CONST             0 (None)
-----
  1           0 RESUME                   0
              2 LOAD_FAST                0 (x)
              4 LOAD_CONST               1 (1)
              6 BUILD_LIST               1
              8 BINARY_OP                0 (+)
             12 STORE_FAST               0 (x)
             14 RETURN_CONST             0 (None)
```

★ **그래서 다른 이름에서 보인다.**

```python
shared = [1]; alias = shared
shared += [2]
print("+= 뒤 alias =", alias, "| is:", alias is shared)
shared2 = [1]; alias2 = shared2
shared2 = shared2 + [2]
print("+  뒤 alias2 =", alias2, "| is:", alias2 is shared2)
```

```text
+= 뒤 alias = [1, 2] | is: True
+  뒤 alias2 = [1] | is: False
```

그림 해설.

- **`+=` 는 제자리**다. 다른 이름이 그 리스트를 가리키고 있으면 **그쪽에서도 보인다**([01번](../01-object-and-name-binding/2-summary.md)).
- **`+=` 는 문자열·`range`·`dict` 도 받는다.** `+` 는 `list` 만 받는다 — 이게 가장 자주 놀라는 자리다.
- 튜플의 `+=` 는 **새 객체를 만든다**(불변이라 제자리가 없다) — [09번](../09-sequence-ops-and-slicing/2-summary.md)이 이미 쟀다.

**비용** — `+=` 는 복사가 없어 반복문 안에서 싸다.\
대신 **공유가 드러난다.** 사본을 원하면 `lst = lst + other` 나 `lst[:] ` 로 명시한다.

### 8. 정렬이 실패하면 리스트가 반쯤 바뀐 채 남는다

**언제 쓰나** — 타입이 섞인 데이터를 정렬할 때. JSON 을 읽어 오면 흔하다.

문서 —\
*"This method sorts the list in place, using only `<` comparisons between items. **Exceptions are not suppressed** - if any comparison operations fail, the entire sort operation will fail (**and the list will likely be left in a partially modified state**)."*

```python
m = [3, "a", 1]
try:
    m.sort()
except TypeError as e:
    print("[3,'a',1].sort()   ->", type(e).__name__, e)
print("  실패 뒤 m  =", m)
m2 = [3, 1, 2, "a"]
try:
    m2.sort()
except TypeError as e:
    print("[3,1,2,'a'].sort() ->", type(e).__name__, e)
print("  실패 뒤 m2 =", m2, " <- 이쪽은 바뀌었다")
print("None 이 섞이면     :", end=" ")
try:
    sorted([1, None])
except TypeError as e:
    print(type(e).__name__, e)
print("bool 과 int 는 된다:", sorted([True, 0, 2, False]))
```

```text
[3,'a',1].sort()   -> TypeError '<' not supported between instances of 'str' and 'int'
  실패 뒤 m  = [3, 'a', 1]
[3,1,2,'a'].sort() -> TypeError '<' not supported between instances of 'str' and 'int'
  실패 뒤 m2 = [1, 2, 3, 'a']
None 이 섞이면     : TypeError '<' not supported between instances of 'NoneType' and 'int'
bool 과 int 는 된다: [0, False, True, 2]
```

그림 해설.

- **같은 예외인데 한쪽은 원본 그대로이고 한쪽은 바뀌었다.** 「부분적으로 바뀐 상태」가 이것이다.
- ★ **되돌려 주지 않는다.** 원본을 지켜야 하면 `sorted` 를 쓰거나 `lst[:]` 로 사본을 뜬다.
- **`bool` 은 `int` 라 섞여도 된다** — `[0, False, True, 2]` 에서 `0` 과 `False` 가 동점이고 **원본 순서**로 남았다(안정 정렬).

**비용** — 예외를 삼키지 않아 타입 오염이 드러난다.\
대신 **원본이 이미 망가졌을 수 있다.**

## 문법 — 형태와 규칙

```python
lst.sort(*, key=None, reverse=False)      # 제자리. None 을 돌려준다. list 에만 있다
sorted(iterable, /, *, key=None, reverse=False)   # 새 list. 아무 이터러블이나 받는다

lst.append(x)      lst.extend(iterable)   lst.insert(i, x)
lst.remove(x)      lst.pop([i])           lst.clear()
lst.index(x[, start[, end]])              lst.count(x)
lst.reverse()      lst.copy()
lst += iterable                            # extend 와 같다
del lst[i]         del lst[i:j]            # 문(statement)
```

- **`key`·`reverse` 는 키워드 전용**이다. `lst.sort(len)` 은 `TypeError` 다.
- **`sort` 는 `list` 에만 있다.** `tuple`·`str`·`set`·`dict`·`bytearray`·`range` 전부 없다.
- **`sorted` 는 무엇이든 받고 언제나 `list` 를 돌려준다.**

```python
for o in ((1, 2), "ab", {1, 2}, {1: 2}, bytearray(b"ba"), range(3)):
    print(f"  {type(o).__name__:10} hasattr 'sort': {hasattr(o, 'sort')}")
print("sorted('banana')      :", sorted("banana"))
print("sorted({'b':1,'a':2}) :", sorted({"b": 1, "a": 2}), " <- 키만")
print("sorted(range(3,0,-1)) :", sorted(range(3, 0, -1)))
print("돌려주는 타입         :", type(sorted("ab")).__name__)
```

```text
  tuple      hasattr 'sort': False
  str        hasattr 'sort': False
  set        hasattr 'sort': False
  dict       hasattr 'sort': False
  bytearray  hasattr 'sort': False
  range      hasattr 'sort': False
sorted('banana')      : ['a', 'a', 'a', 'b', 'n', 'n']
sorted({'b':1,'a':2}) : ['a', 'b'] <- 키만
sorted(range(3,0,-1)) : [1, 2, 3]
돌려주는 타입         : list
```

## 어디서 틀리나

### (1) `x = lst.sort()` 로 받는다

`None` 이 들어간다. 에러는 **그 값을 쓰는 곳**에서 난다.\
고치는 법: 사본이 필요하면 `sorted(lst)`, 제자리면 `lst.sort()` 를 **문으로만** 쓴다.

### (2) `return items.sort()` 로 API 가 `None` 을 뱉는다

(1)의 실전형이다. 테스트가 「예외 없음」만 보면 안 걸린다.\
고치는 법: `items.sort(); return items` 또는 `return sorted(items)`.

### (3) 내림차순을 `sorted(...)[::-1]` 로 만든다

동점 무리 **안의 순서까지 뒤집힌다.** 「동점이면 먼저 등록한 순」 같은 요구사항이 조용히 깨진다.\
고치는 법: `reverse=True`.

### (4) 기준마다 방향이 다른데 `reverse=True` 를 쓴다

`reverse` 는 **모든 기준**을 뒤집는다.\
고치는 법: 숫자면 키를 음수로, 아니면 **나눠 정렬**(덜 중요한 기준부터).

### (5) `key` 안에서 그 리스트를 읽는다

CPython 에서는 **빈 리스트로 보인다.** 에러도 안 난다.\
고치는 법: `key` 는 원소 하나만 보게 만든다.

### (6) `remove` 로 `True`/`1`/`1.0` 을 지우려 한다

`==` 로 찾으므로 **먼저 나온 동등한 값**이 지워진다.\
고치는 법: 자리를 알면 `del`·`pop`, 타입까지 맞춰야 하면 직접 훑는다.

### (7) `lst = lst + other` 와 `lst += other` 를 같은 것으로 본다

앞엣것은 새 객체, 뒤엣것은 제자리다. 그리고 **받는 타입이 다르다.**\
고치는 법: 공유가 싫으면 `lst = lst + list(other)`, 제자리면 `extend` 로 의도를 드러낸다.

### (8) 타입이 섞인 데이터를 `sort` 로 바로 정렬한다

`TypeError` 가 나고 **원본이 반쯤 바뀌어** 있을 수 있다.\
고치는 법: `key` 로 타입을 통일하거나 `sorted` 로 사본에서 시도한다.

### (9) 집합이 든 리스트를 정렬한다

**에러가 안 난다.** 문서가 *"the output of the `list.sort()` method is undefined for lists of sets"* 라고 적는다([13번](../13-set-and-frozenset/2-summary.md)).\
고치는 법: `key=len`·`key=sorted` 처럼 **전순서가 있는 키**를 준다.

## 구현 세부사항 대 언어 보장

세 층으로 가른다. ★ **이 주제는 「언어 보장」이 두껍다** — `key` 호출 횟수도 안정성도 문서가 문장으로 약속한다.
관찰 층은 **비교 횟수**와 **`getsizeof` 값** 둘이다.

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **언어 보장** | 라이브러리 레퍼런스가 정한 것 | 공식 문서 문장을 열어서 인용 |
| **CPython 구현** | 문서가 「구현 세부사항」이라 못 박은 것 | 실행으로 확인 |
| **이 판·이 머신의 관찰** | 3.12.3 에서 그랬을 뿐 | 「관찰」로 명기 |

### 언어 보장

| 사실 | 근거 |
|---|---|
| `sort()` 는 정렬된 열을 **돌려주지 않는다** — 부작용임을 알리려고 그렇게 했다 | `list.sort` |
| **`key` 는 원소당 한 번 계산되고** 그 값이 정렬 내내 쓰인다 | 〃 |
| `key`·`reverse` 는 **키워드 전용** | 〃 시그니처 |
| `reverse=True` 는 **「비교를 뒤집은 것처럼」** 정렬한다 | 〃 |
| **`sort()` 는 안정 정렬이 보장된다** | 〃 |
| **`sorted()` 도 안정 정렬이 보장된다** | `sorted` |
| 정렬은 **`<` 비교만** 쓴다 | `list.sort` · `sorted` |
| 비교가 실패하면 정렬 전체가 실패하고 **리스트가 부분적으로 바뀐 채 남을 수 있다** | `list.sort` |
| `s[i:j] = t`·`del s[i:j]`·`s += t`(= `extend`)·`remove`·`pop` 의 정의 | Mutable Sequence Types |
| **집합이 든 리스트의 `sort` 결과는 정의되지 않는다** | Set Types |

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| **정렬 중에는 그 리스트가 비어 보인다** — 문서가 「CPython implementation detail」로 표시 | `key` 안에서 `list(data)` 가 `[]` |
| 정렬 중 변경을 **감지하면** `ValueError: list modified during sort` | 실행 |
| `key` 호출 **순서**가 원본 순서 | 다섯 경우 전부. **문서는 횟수만 약속한다** |
| 예외 문구(`list.remove(x): x not in list` 등) | 실행 |

### 이 판(3.12.3)·이 머신의 관찰

| 관찰 | 어디가 흔들리나 |
|---|---|
| 비교 횟수 — 정렬된 10개와 역순 10개가 **똑같이 9회**, 무작위 100개가 532회 | **구현의 알고리즘에 달렸다.** 보장이 아니다 |
| `cmp_to_key` 의 `cmp` 호출 539회 | 〃 |
| `list` 의 `getsizeof` 가 `len` 1·5·9·17 에서 계단으로 뛰는 것 | 여유 공간 전략은 구현 몫이다 |
| `list(range(17))` 은 200, `[0] * 17` 은 192, `append` 로 키운 것은 248 | 〃 — **만드는 방법마다 다르다** |
| 바이트코드 명령 이름(`BINARY_OP 13 (+=)`) | 판마다 바뀐다 |

```python
import sys
L = []
prev = sys.getsizeof(L)
print(f"len=0  getsizeof={prev}")
for i in range(1, 18):
    L.append(i)
    s = sys.getsizeof(L)
    if s != prev:
        print(f"len={len(L):<3} getsizeof={s}")
        prev = s
print("list(range(17)) :", sys.getsizeof(list(range(17))))
print("[0]*17          :", sys.getsizeof([0] * 17))
```

```text
len=0  getsizeof=56
len=1   getsizeof=88
len=5   getsizeof=120
len=9   getsizeof=184
len=17  getsizeof=248
list(range(17)) : 200
[0]*17          : 192
```

### 그래서 이렇게 적으면 틀린다

- ✗ 「파이썬의 정렬이 안정적인 것은 Timsort 이기 때문이다」\
  ○ 알고리즘은 **구현**이고, 안정성은 **문서가 약속한 보장**이다. 두 문장이 다른 층이다.
- ✗ 「`key` 가 비교할 때마다 불린다」\
  ○ **원소당 한 번**이다. 문서가 *"calculated once"* 라고 적고 세어 보면 정확히 n 회다.
- ✗ 「`reverse=True` 는 정렬한 뒤 뒤집는 것이다」\
  ○ **비교를 뒤집는 것**이라 동점 순서가 유지된다. `[::-1]` 만 동점까지 뒤집는다.
- ✗ 「`reverse=True` 와 키를 음수로 주는 것은 다르다」\
  ○ **같았다**(실측). 갈리는 것은 `[::-1]` 쪽이다.
- ✗ 「`lst.sort()` 는 정렬된 리스트를 돌려준다」\
  ○ **`None`** 이다. 그리고 문서가 그렇게 만든 이유까지 적어 두었다.
- ✗ 「`lst += x` 는 `lst = lst + x` 와 같다」\
  ○ 앞엣것은 `extend`(제자리·아무 이터러블), 뒤엣것은 새 객체(`list` 만).
- ✗ 「`remove` 는 그 객체를 지운다」\
  ○ **`==` 인 첫 원소**를 지운다. `remove(True)` 가 `1` 을 지운다.
- ✗ 「정렬하다 실패해도 원본은 그대로다」\
  ○ 문서가 *"partially modified state"* 라고 적고, 실측에서 실제로 바뀐 판이 있었다.

**판정 기준 한 줄**: 어떤 코드가 「정렬 결과를 **받아서**」 쓰고 있으면, 그 자리가 `sort` 인지 `sorted` 인지부터 확인하라.

## 언제 쓰고 언제 안 쓰나

| 쓰는 것 | 상황 |
|---|---|
| `lst.sort()` | 원본을 그대로 정렬해도 될 때. **문으로만** 쓴다 |
| `sorted(x)` | 원본을 지켜야 할 때 · 이터러블이 `list` 가 아닐 때 |
| `sorted(lst)` 로 사본 | 정렬 실패 시 원본을 지키고 싶을 때 |
| `key=함수` | 원소에서 뽑은 값으로 줄 세울 때 |
| `key=튜플` | 기준이 여럿이고 **방향이 같을** 때 |
| **나눠 정렬** | 기준마다 **방향이 다를** 때(덜 중요한 것부터) |
| `reverse=True` | 내림차순. **동점 순서를 지키고 싶을 때** |
| `sorted(...)[::-1]` | 동점 순서까지 뒤집고 싶을 때 — **의도할 때만** |
| `operator.itemgetter`/`attrgetter` | `lambda` 대신. 읽기가 낫다 |
| `functools.cmp_to_key` | **두 원소를 봐야만** 순서가 정해질 때 |
| `lst.append`/`extend` | 뒤에 붙일 때. `+=` 와 같은 일 |
| `lst.remove(x)` | **값**으로 지울 때 |
| `del lst[i]` · `lst.pop(i)` | **자리**로 지울 때. 값이 필요하면 `pop` |
| `lst[:]` · `list(lst)` | 얕은 복사([03번](../03-mutability-and-copying/2-summary.md)) |

**안 쓰는 자리**는 넷이다.\
**`sort()` 의 반환값을 받지 마라** — 언제나 `None` 이다.\
**`key` 안에서 정렬 중인 리스트를 보지 마라** — 비어 보인다.\
**동점 순서가 의미 있으면 `[::-1]` 을 쓰지 마라.**\
**타입이 섞였을 수 있으면 원본을 `sort` 하지 마라** — 반쯤 바뀐 채 남는다.

## 핵심 문장

- **`sort` 는 `None` 을 돌려준다.** 문서가 「부작용임을 알리려고」 그렇게 했다고 적는다 — 실수가 아니라 설계다.
- **`key` 는 원소당 정확히 한 번** 불린다. 이것은 **보장**이고, 비교 횟수는 **관찰**이다.
- **안정 정렬은 언어 보장**이다. 「Timsort 라서」가 아니다.
- 그 보장 덕에 **덜 중요한 기준부터 나눠 정렬**할 수 있다 — 방향이 섞인 다중 기준의 유일한 일반해다.
- **`reverse=True` 는 비교를 뒤집고**, `[::-1]` 은 **결과를 뒤집는다.** 동점 무리 안에서 갈린다.
- **정렬 중의 리스트는 CPython 에서 비어 보인다.** 문서가 구현 세부사항으로 못 박아 두었다.
- **`remove` 는 `==`, `del`·`pop` 은 자리.** `remove(True)` 가 `1` 을 지운다.
- **`+=` 는 `extend`** 다 — 제자리이고 아무 이터러블이나 받는다. `+` 는 새 객체이고 `list` 만 받는다.

## 관련 자료

- 목록: [python/syntax 주제 목록](../README.md) — 이 주제는 **10번**
- 선행: [09-sequence-ops-and-slicing](../09-sequence-ops-and-slicing/2-summary.md) — 슬라이스·`s[:]`·`+`·`*`·순회 중 삭제의 정본. **여기서는 다시 재지 않는다.**
- 선행: [01-object-and-name-binding](../01-object-and-name-binding/2-summary.md) — `+=` 가 같은 객체를 바꾼다는 것의 정본.
- 선행: [03-mutability-and-copying](../03-mutability-and-copying/2-summary.md) — 얕은 복사 네 형태.
- 선행: [02-is-vs-eq-interning](../02-is-vs-eq-interning/2-summary.md) — `True == 1` 이 되는 이유.
- 이어지는 곳: [11-tuple-and-unpacking](../11-tuple-and-unpacking/2-summary.md) — 정렬 키로 쓰는 튜플이 무엇인지.
- 이어지는 곳: [13-set-and-frozenset](../13-set-and-frozenset/2-summary.md) — 집합이 든 리스트의 `sort` 가 정의되지 않는 이유.
- 이어지는 곳: 목록의 **31번 주제** 「비교 프로토콜과 정렬 가능성」 — `__lt__` 하나로 정렬이 되는 이유·`total_ordering`.
- 이어지는 곳: 목록의 **23번 주제** 「`lambda` 와 고차 함수」 — 정렬 `key` 로 쓰는 `lambda`.
- 이어지는 곳: 목록의 **44번 주제** 「`itertools`」 — `groupby` 가 정렬을 전제한다는 것.
- 이어지는 곳: 목록의 **45번 주제** 「`functools`」 — `cmp_to_key` 의 본거지.
- 기존 노트: [`cs/foundations/python-basics/`](../../../../python-basics/) — 리스트 메서드를 「이렇게 쓴다」까지 다룬다.\
  **경계**: 그쪽은 사용 예시까지, 여기는 「**무엇이 `None` 을 돌려주고 무엇이 보장인가**」부터다.
- 자료구조의 원리(동적 배열·정렬 알고리즘의 복잡도)는 여기가 아니다: [`cs/data-structure/`](../../../../../data-structure/) · [`cs/algorithm/`](../../../../../algorithm/)
- 공식 문서: [`list.sort`](https://docs.python.org/3.12/library/stdtypes.html#list.sort) · [`sorted`](https://docs.python.org/3.12/library/functions.html#sorted) · [Sorting Techniques](https://docs.python.org/3.12/howto/sorting.html) · [Mutable Sequence Types](https://docs.python.org/3.12/library/stdtypes.html#mutable-sequence-types)

## 용어 풀이

- **제자리(in place)**: 새 객체를 만들지 않고 원래 객체의 내용을 바꾸는 것.\
  `sort`·`reverse`·`append`·`extend`·`+=` 가 그렇다. 다른 이름에서도 변화가 보인다.
- **안정 정렬(stable sort)**: `==` 로 같은 원소들의 **상대 순서가 안 바뀌는** 정렬.\
  파이썬에서는 **언어 보장**이다.
- **`key` 함수**: 원소에서 「비교할 값」을 뽑는 함수. **원소당 한 번** 불린다.
- **`cmp` 함수**: 두 원소를 받아 음수·0·양수를 돌려주는 옛 방식.\
  `functools.cmp_to_key` 로 감싸야 쓸 수 있고, **비교할 때마다** 불린다.
- **다중 기준 정렬**: 기준이 여럿인 정렬. 방향이 같으면 **튜플 키**, 다르면 **나눠 정렬**.
- **부분적으로 바뀐 상태(partially modified state)**: 정렬이 예외로 중단됐을 때 리스트가 남는 상태.\
  문서가 이 표현을 쓴다. **되돌려 주지 않는다.**
- **부작용(side effect)**: 값을 돌려주는 대신 **무언가를 바꾸는** 것.\
  문서가 `sort` 의 반환값을 `None` 으로 정한 이유로 이 말을 쓴다.

## 더 들어가면

- **`operator.itemgetter(1, 0)`** 은 튜플 키를 만들어 준다 — `lambda r: (r[1], r[0])` 과 같은 일이고 읽기가 낫다.
- **`functools.total_ordering`** 은 `__lt__`·`__eq__` 만으로 여섯 비교를 채워 준다(목록의 **31번 주제**).
- **`sorted` 의 `key` 에 `str.casefold`** 를 쓰면 `str.lower` 보다 넓은 대소문자 동일시가 된다([07번](../07-string-methods/2-summary.md)).
- **`heapq.nsmallest`/`nlargest`** 는 전체 정렬 없이 상위 k 개를 뽑는다 — 비용 비교는 여기서 **재지 않았다.**
- **`list.sort` 의 알고리즘 이름과 복잡도**는 이 문서의 범위가 아니다: [`cs/algorithm/`](../../../../../algorithm/)
