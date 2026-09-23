# python/syntax/10-list-methods-and-sort-key — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> [1-question.md](1-question.md)의 번호와 **1:1**로 대응한다. 질문 11개 = 답 11개.
>
> 이 파일의 모든 출력은 `python3` **3.12.3** 에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> 단 **비교 횟수와 `getsizeof` 값은 구현에 달린 것**이라 다른 구현·다른 판에서는 달라진다(2·10번 답).

## 정답

### 1. 바꾸는 것은 `None`, 꺼내는 것은 값

**출력**

```text
x.sort()        -> None
x.append(9)     -> None
x.extend([8])   -> None
x.insert(0, 7)  -> None
x.remove(7)     -> None
x.reverse()     -> None
x.clear()       -> None
y.pop()         -> 2 | y = [3, 1]
sorted(y)       -> [1, 3] | y = [3, 1]
res = None | words = ['apple', 'fig', 'pear']
res[0] -> TypeError 'NoneType' object is not subscriptable
```

**왜 그런가**

```text
 "돌려주는 것" 으로 두 무리를 가른다

  바꾸는 것(제자리)   ->  None
   sort  reverse  append  extend  insert  remove  clear

  꺼내는 것 / 만드는 것 ->  값
   pop -> 꺼낸 원소     index -> 자리    count -> 개수
   copy -> 새 리스트    sorted(...) -> 새 리스트
```

문서가 이유까지 적어 두었다 —\
*"This method modifies the sequence in place for economy of space when sorting a large sequence.
**To remind users that it operates by side effect, it does not return the sorted sequence** (use `sorted()` to explicitly request a new sorted list instance)."*

**에러가 나는 줄은 마지막 줄뿐이다**

```text
 res = words.sort()   <- 여기서는 아무 일도 안 난다.
                         정렬도 제대로 됐다. 틀린 것은 "받은 값" 뿐이다.
 print(res, words)    <- None 과 정렬된 리스트가 그대로 찍힌다.
 res[0]               <- 여기서 터진다.  None[0]
```

★ **호출한 줄과 터지는 줄이 멀다.** 이것이 이 함정의 값이다 —
`return items.sort()` 로 API 가 `None` 을 내보내면, 터지는 곳은 그 응답을 **쓰는 쪽**이다.

`sorted(y)` 는 새 리스트를 돌려주고 `y` 는 그대로다 — 그래서 `y = [3, 1]` 이 두 번 같은 값으로 찍혔다.

### 2. `key` 는 원소당 정확히 한 번 — 이것은 보장이다

**출력**

```text
무작위 3개           n=  3  호출   3회
정렬된 10개          n= 10  호출  10회
역순 10개           n= 10  호출  10회
같은 값 50개         n= 50  호출  50회
```

**왜 그런가 — 문서의 문장이 곧 보장이다**

*"`key` specifies a function of one argument that is used to extract a comparison key from each list element...
**The key corresponding to each item in the list is calculated once and then used for the entire sorting process.**"*

```text
 sorted(data, key=f) 가 하는 일

   1) 원소마다 f 를 한 번씩 불러 이름표를 만든다      <- n 번  (보장)
   2) 그 이름표들끼리 "<" 로 비교하며 줄 세운다       <- 데이터에 달렸다 (관찰)
   3) 줄 세운 "원소" 를 돌려준다 (이름표가 아니다)
```

**★ 비교 횟수는 다르다 — 그쪽은 보장이 아니다**

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

★ **정렬된 10개와 역순 10개가 똑같이 9회**다. 구현이 이어진 구간을 알아본다는 뜻인데, **이것은 관찰이지 보장이 아니다.**

| | 몇 번 | 어느 층 |
|---|---|---|
| `key` 호출 | **원소당 1회** | **언어 보장** — 문서가 *"calculated once"* |
| `key` 호출 **순서** | 원본 순서였다(5경우 전부) | **관찰** — 문서는 횟수만 약속한다 |
| `<` 비교 | 데이터에 달렸다(9\~532회) | **관찰** |

**`cmp_to_key` 와 대비**

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

**`key` 는 「원소당 한 번」, `cmp` 는 「비교할 때마다」다.** 한 원소에서 뽑을 수 있으면 언제나 `key` 가 맞다.

### 3. 혼자 다른 것은 마지막 줄이다

**출력**

```text
[('b', 1), ('d', 1), ('a', 2), ('c', 2), ('e', 2)]
[('a', 2), ('c', 2), ('e', 2), ('b', 1), ('d', 1)]
[('a', 2), ('c', 2), ('e', 2), ('b', 1), ('d', 1)]
[('e', 2), ('c', 2), ('a', 2), ('d', 1), ('b', 1)]
```

**왜 그런가**

```text
 원본   a(2)  b(1)  c(2)  d(1)  e(2)

 reverse=True        ->  a c e | b d      동점 무리 "안" 은 원본 순서
 key=-점수           ->  a c e | b d      같다
 정렬 뒤 [::-1]      ->  e c a | d b      동점 무리 "안" 까지 뒤집혔다
                         ^^^^^
```

문서가 `reverse` 를 이렇게 정의한다 —
*"`reverse` is a boolean value. If set to `True`, then the list elements are sorted **as if each comparison were reversed**."*\
★ **「비교를 뒤집는다」이지 「결과를 뒤집는다」가 아니다.** 안정성이 그대로 유지된다.

> ★ **이 문항은 처음 세운 예상이 틀린 자리다.**
> 「`reverse=True` 와 키를 음수로 주는 것이 안정성 때문에 다르다」로 적으려 했는데,
> 실제로 돌려 보니 **둘이 같았다.** 갈리는 것은 세 번째(`[::-1]`) 하나였다.
> **한 판만 보고 「다르다」로 적었으면 틀렸을 자리다.**

**그래서 실무에서 물리는 곳**

「점수 높은 순, 동점이면 먼저 등록한 순」이 요구사항이면 `reverse=True` 가 맞고, `sorted(...)[::-1]` 은 **조용히 어긴다.**
에러가 안 나고 동점이 없는 테스트 데이터에서는 통과한다.

### 4. `key` 안에서 본 리스트는 비어 있다

**출력**

```text
정렬 중에 본 data : [[], [], []]
정렬 뒤 data      : [1, 2, 3]
ValueError list modified during sort
```

**왜 그런가 — 문서가 구현 세부사항으로 못 박아 두었다**

*"**CPython implementation detail:** While a list is being sorted, the effect of attempting to mutate, or even inspect,
the list is undefined. The C implementation of Python **makes the list appear empty for the duration**,
and raises `ValueError` if it can detect that the list has been mutated during a sort."*

```text
 data.sort(key=peek) 가 도는 동안

   data ->  [ 비어 보인다 ]        <- C 구현이 잠시 떼어 둔다
   peek 가 list(data) 를 찍으면  []
   정렬이 끝나면 제자리에 돌려놓는다  ->  [1, 2, 3]
```

- ★ **에러가 안 난다.** 빈 리스트가 정직한 값처럼 돌아온다 — **조용한 실패**다.
- 바꾸려 하면 `ValueError` 가 나지만 문서는 *"if it can detect"* 라고만 적는다. **언제나 잡아 준다는 보장이 아니다.**
- **`sorted` 에는 이 문제가 없다.** 정렬 대상이 새로 만든 리스트이기 때문이다.
- 이것은 **CPython 구현 층**이다. 다른 구현은 다르게 해도 된다.

### 5. `remove` 는 `==`, `del`·`pop` 은 자리

**출력**

```text
[0, 2, True, 1.0]
1 3
[10, 30, 40]
20 [10, 30, 40]
ValueError list.remove(x): x not in list
IndexError pop index out of range
```

**왜 그런가**

```text
 a = [0, 1, 2, True, 1.0]
      ^   ^          ^
      |   |          +-- 1.0 == True 이지만 뒤에 있다
      |   +------------- 1 == True 이고 "앞" 에 있다  <- 이것이 지워진다
      +----------------- 0 != True

 a.remove(True)  ->  [0, 2, True, 1.0]
```

- ★ **`remove(True)` 가 지운 것은 `True` 가 아니라 `1`** 이다. `==` 로 **앞에서부터** 찾기 때문이다.
- `index`·`count`·`in` 도 전부 `==` 다 — `[0, 1, 1.0, True].count(1)` 이 **3**이다([02번](../02-is-vs-eq-interning/2-summary.md)).
- `del d[1]` 은 **문**이라 돌려주는 값이 없고, `e.pop(1)` 은 **꺼낸 원소**를 돌려준다.

**두 예외의 종류가 다른 이유 — 「무엇으로 찾았나」가 다르다**

| 호출 | 무엇으로 찾나 | 없으면 |
|---|---|---|
| `lst.remove(x)` | **값**(`==`) | `ValueError: list.remove(x): x not in list` |
| `lst.pop(i)` | **자리**(인덱스) | `IndexError: pop index out of range` |
| `del lst[i]` | **자리** | `IndexError: list assignment index out of range` |

★ **예외 문구까지 다르다** — `pop` 과 `del` 이 같은 `IndexError` 인데 문구가 갈린다.
**문구는 관찰**이고 예외 종류가 명세다.

### 6. `+=` 는 `extend`, `+` 는 새 객체

**출력**

```text
[1, 2, 'x', 'y'] True
TypeError can only concatenate list (not "str") to list
[1, 2, 0, 1, 2]
[1, 2] True
[1] False
```

**왜 그런가**

```text
  lst += other        ==  lst.extend(other)
     제자리로 늘린다.  other 는 "아무 이터러블" 이면 된다
     -> 같은 객체.  다른 이름에서도 보인다

  lst = lst + other
     새 리스트를 만들어 이름을 다시 묶는다.  other 는 "list" 여야 한다
     -> 다른 객체.  다른 이름은 옛 리스트를 계속 본다
```

| | 받는 타입 | 같은 객체인가 | 다른 이름에서 보이나 |
|---|---|---|---|
| `lst += x` | **아무 이터러블**(`str`·`range`·`dict`…) | **그렇다** | **보인다** |
| `lst = lst + x` | **`list` 만** | 아니다 | 안 보인다 |

`dis` 로 보면 다른 것은 **연산 하나**뿐이고, 갈리는 것은 그 연산의 의미다.

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

★ **`f += range(3)` 이 `[1, 2, 0, 1, 2]` 가 된 것**이 「아무 이터러블」의 증거다.
`f = f + range(3)` 이었다면 `TypeError` 다.

튜플에서 `+=` 가 새 객체를 만드는 것은 [09번](../09-sequence-ops-and-slicing/2-summary.md)이 이미 쟀고,
`t[0] += [1]` 이 **에러를 내면서도 값을 바꾸는** 것은 [03번](../03-mutability-and-copying/2-summary.md)이 정본이다.

### 7. 안정 정렬은 언어 보장이다

**답 — 보장이다. 라이브러리 레퍼런스 두 곳이 같은 말을 적는다.**

- `list.sort` — *"The `sort()` method is **guaranteed to be stable**. A sort is stable if it guarantees not to change
  the relative order of elements that compare equal — this is helpful for sorting in multiple passes
  (for example, sort by department, then by salary grade)."*
- `sorted` — *"The built-in `sorted()` function is **guaranteed to be stable**."*

★ **두 문장 어디에도 알고리즘 이름이 없다.**

```text
  "Timsort 를 쓴다"        ->  구현 (바뀔 수 있다)
  "안정 정렬이 보장된다"     ->  언어 보장 (어느 구현에서도 같아야 한다)

  두 문장을 한 문장으로 섞으면 ("Timsort 라서 안정적이다") 층이 무너진다.
```

같은 페이지가 **무엇이 구현인지도** 표시해 둔다 — 정렬 중 리스트가 비어 보이는 것은
`CPython implementation detail:` 이라는 딱지가 붙어 있다(4번 답). **문서가 층을 직접 갈라 준 주제**다.

그 보장 덕에 **나눠 정렬**이 성립한다 — 문서가 예까지 든다(*"sort by department, then by salary grade"*).

```python
people = [("최", "영업", 3), ("김", "개발", 1), ("이", "영업", 1),
          ("박", "개발", 3), ("정", "개발", 1)]
tmp = sorted(people, key=lambda p: p[0])
tmp = sorted(tmp, key=lambda p: p[2])
tmp = sorted(tmp, key=lambda p: p[1])
print("세 번 나눠 :", tmp)
print("튜플 키    :", sorted(people, key=lambda p: (p[1], p[2], p[0])))
```

```text
세 번 나눠 : [('김', '개발', 1), ('정', '개발', 1), ('박', '개발', 3), ('이', '영업', 1), ('최', '영업', 3)]
튜플 키    : [('김', '개발', 1), ('정', '개발', 1), ('박', '개발', 3), ('이', '영업', 1), ('최', '영업', 3)]
```

### 8. 방향이 섞이면 `reverse` 로 못 한다

**답 — `reverse=True` 는 「모든 비교」를 뒤집기 때문이다.**

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

- `reverse=True` 는 **부서까지** 내림차순으로 만들었다(영업이 개발보다 앞).
- **쓸 수 있는 두 방법** — ① 숫자 키를 **음수로** ② **나눠 정렬**(중요도가 낮은 기준부터, 안정성에 기댄다).
- ★ **문자열은 음수로 못 만든다.** 그래서 문자열 기준이 내림차순이면 **나눠 정렬이 유일한 일반해**다.

### 9. 실패하면 반쯤 바뀐 채 남는다 — 그리고 그것이 문서의 표현이다

**출력**

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
print("  실패 뒤 m2 =", m2)
```

```text
[3,'a',1].sort()   -> TypeError '<' not supported between instances of 'str' and 'int'
  실패 뒤 m  = [3, 'a', 1]
[3,1,2,'a'].sort() -> TypeError '<' not supported between instances of 'str' and 'int'
  실패 뒤 m2 = [1, 2, 3, 'a']
```

★ **같은 예외인데 한쪽은 그대로이고 한쪽은 바뀌었다.**

문서 — *"Exceptions are not suppressed - if any comparison operations fail, the entire sort operation will fail
(**and the list will likely be left in a partially modified state**)."*

- 「부분적으로 바뀐 상태로 남는다」는 **문서가 적은 것**이지만, *"likely"* 가 붙어 있다 —
  **「어떻게 남는가」는 보장이 아니다.** 위의 두 결과가 그 증거다.
- ★ **한 판(`m`)만 재고 「원본은 안 바뀐다」로 결론을 세웠다면 틀렸을 자리다.**
- 원본을 지켜야 하면 `sorted` 를 쓰거나 `lst[:]` 로 사본을 뜬다.

### 10. 세 층 가르기

**언어 보장**

| 사실 | 근거 |
|---|---|
| `sort()` 는 정렬된 열을 **돌려주지 않는다**(부작용임을 알리려고) | `list.sort` |
| **`key` 는 원소당 한 번** 계산되어 정렬 내내 쓰인다 | 〃 |
| `key`·`reverse` 는 **키워드 전용** | 〃 |
| `reverse=True` = **「비교를 뒤집은 것처럼」** | 〃 |
| **`sort()`·`sorted()` 는 안정 정렬이 보장된다** | `list.sort` · `sorted` |
| 정렬은 **`<` 비교만** 쓴다 | 〃 |
| 실패하면 **부분적으로 바뀐 채** 남을 수 있다 | `list.sort` |
| `+=` 는 `extend` 와 같다 · `remove` 는 `==` 로 찾는다 | Mutable Sequence Types |
| **집합이 든 리스트의 `sort` 결과는 정의되지 않는다** | Set Types |

**CPython 구현 세부사항**

| 사실 | 어떻게 확인했나 |
|---|---|
| **정렬 중에는 그 리스트가 비어 보인다** — 문서가 그렇게 표시 | `key` 안의 `list(data)` 가 `[]` |
| 변경을 **감지하면** `ValueError: list modified during sort` | 실행 |
| `key` 호출 **순서**가 원본 순서 | 다섯 경우 전부 — **문서는 횟수만 약속한다** |
| 예외 문구 전부 | 실행 |

**이 판(3.12.3)·이 머신의 관찰**

| 관찰 | 어디가 흔들리나 |
|---|---|
| 비교 횟수 9 / 9 / 532 | 알고리즘에 달렸다. **보장이 아니다** |
| `cmp_to_key` 의 539회 | 〃 |
| `getsizeof` 가 `len` 1·5·9·17 에서 뛰는 것 | 여유 공간 전략은 구현 몫 |
| `list(range(17))`=200 · `[0]*17`=192 · `append` 로 키운 것=248 | **만드는 방법마다 다르다** |
| 바이트코드 명령 이름 | 판마다 바뀐다 |

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

★ **같은 17개짜리 리스트가 세 가지 크기**다. 「리스트는 이만큼 쓴다」는 말이 성립하지 않는다.

**그래서 이렇게 적으면 틀린다**

- ✗ 「Timsort 라서 안정적이다」 → 안정성은 **문서가 약속한 보장**, 알고리즘은 구현.
- ✗ 「`key` 는 비교마다 불린다」 → **원소당 한 번**(보장).
- ✗ 「`reverse=True` 는 뒤집는 것이다」 → **비교를 뒤집는 것**이라 동점 순서가 유지된다.
- ✗ 「`reverse=True` 와 음수 키는 다르다」 → **같았다**(실측).
- ✗ 「`lst += x` 는 `lst = lst + x` 와 같다」 → 제자리 여부도 받는 타입도 다르다.
- ✗ 「정렬 실패해도 원본은 그대로」 → **바뀐 판이 있었다.**

### 11. 조용한 실패 세 자리

| 자리 | 무엇이 조용히 틀리나 | 무엇으로 막나 |
|---|---|---|
| **`x = lst.sort()`** | `None` 을 받고 **정렬은 제대로 된다.** 터지는 곳이 멀다 | `sort()` 는 문으로만. 값이 필요하면 `sorted` |
| **`sorted(...)[::-1]`** | 동점 무리 안 순서가 뒤집힌다. 동점 없는 테스트는 통과 | `reverse=True` |
| **`key` 안에서 그 리스트 읽기** | CPython 에서 **빈 리스트**가 보인다. 에러 없음 | `key` 는 원소 하나만 보게 |
| (보태기) **집합이 든 리스트 `sort`** | 입력 순서에 따라 결과가 다르다. 에러 없음 | 전순서가 있는 `key` 를 준다([13번](../13-set-and-frozenset/2-summary.md)) |
| (보태기) **`remove(True)`** | `1` 이 지워진다 | 자리를 알면 `del`·`pop` |

막는 코드는 이렇게 생겼다.

```python
def sort_items(items):
    items.sort()
    return items                  # sort() 의 반환값을 쓰지 않는다

def desc_by_score(rows):
    return sorted(rows, key=lambda r: r["score"], reverse=True)   # [::-1] 이 아니다

def safe_sort(items, key=None):
    out = list(items)             # 실패해도 원본이 안 망가진다
    out.sort(key=key)
    return out
```

## 실행 검증

```text
$ python3 --version
Python 3.12.3
$ python3 -c "import sys; print(sys.implementation.name)"
cpython
```

| 문항 | 무엇을 돌렸나 | 몇 번 |
|---|---|---|
| 1 | 변경 메서드 7종 + `pop`·`copy`·`sorted`, `res[0]`·`sort().reverse()` | 각 1회 |
| 2 | `key` 호출 세기 **6가지 데이터**, `__lt__` 세기 3가지, `cmp_to_key` 대비 | 각 1회 |
| 3 | 동점 데이터로 **정렬 4형태**, 다중 기준 3형태 | 각 1회 |
| 4 | 정렬 중 `list(data)` 찍기, 정렬 중 `append` | 각 1회 |
| 5 | `remove`/`index`/`count`/`in` 8식, `del`/`pop` 5식, 예외 3종 | 각 1회 |
| 6 | `+=` 5종(`str`·`range`·`dict`·`tuple`·`list`), `+` 2종, `dis` 2개, 공유 2식 | 각 1회 |
| 8 | 방향이 섞인 다중 기준 3형태 | 각 1회 |
| 9 | 타입 섞인 리스트 **2가지 배치**, `None` 섞기, `bool` 섞기 | 각 1회 |
| 10 | `getsizeof` **append 17단계 + 두 가지 생성법**, `hasattr('sort')` 6타입 | 각 1회 |

**★ 한 판으로 결론이 안 나는 것을 여러 판 던진 자리**

- **3번** — `reverse=True` 와 `key=-x` **둘만** 비교했으면 「다르다」는 예상이 확인될 수도 없고 반증될 수도 없었다.
  **세 번째(`[::-1]`)를 같이 던져야** 「갈리는 것은 이쪽」이 드러난다.
  ★ 브리핑의 전제가 여기서 뒤집혔다.
- **9번** — `[3, "a", 1]` 만 재면 **원본이 그대로**여서 「안 바뀐다」로 결론이 선다.
  **`[3, 1, 2, "a"]`** 를 던져야 `[1, 2, 3, "a"]` 로 **바뀐 것**이 나온다.
- **2번** — `[3,1,2]` 하나만 재면 「n 번」이 우연일 수 있다. **정렬된·역순·전부 같은 값·빈 리스트**까지 다섯 경우를 던졌다.
  반대로 **비교 횟수**는 정렬된 10과 역순 10이 **똑같이 9회**라, 두 판만 보면 「언제나 9회」로 오해한다.
- **10번** — `append` 로만 재면 「17개는 248바이트」로 결론이 선다.
  **`list(range(17))`(200)과 `[0]*17`(192)** 을 던져야 **만드는 방법마다 다른 것**이 드러난다.

**「에러가 안 난 것」이 근거인 자리**

- 1번 — `res = words.sort()` 줄에서 **예외가 없는 것**이 「조용히 지나간다」의 증거다.
- 4번 — 정렬 중 `list(data)` 가 **예외 없이 `[]`** 를 주는 것이 「비어 보인다」의 증거다.
- 3번 — `[::-1]` 이 **예외 없이** 동점 순서를 뒤집는 것이 조용한 실패의 증거다.

**구현 의존 항목 — 버전이 오르면 다시 찍을 것**

| 다시 찍을 것 | 왜 |
|---|---|
| 2번의 `__lt__` 횟수·`cmp` 횟수 | 알고리즘에 달렸다 |
| 2번의 `key` 호출 **순서** | 문서는 횟수만 약속한다 |
| 4번의 「비어 보인다」·`ValueError` 문구 | 문서가 **CPython 구현**이라 표시 |
| 10번의 `getsizeof` 값 전부 | 여유 공간 전략은 구현 몫 |
| 6번의 바이트코드 명령 이름 | 판마다 바뀐다 |
| 예외 **문구** 전부 | 예외 종류는 명세지만 문구는 아니다 |

나머지(`None` 반환, `key` 호출 **횟수**, 안정성, `reverse` 의 의미, `+=` = `extend`,
`remove` 가 `==` 로 찾는 것, 실패 시 부분 변경)는 **언어 보장**이므로 어떤 구현에서도 같아야 한다.
