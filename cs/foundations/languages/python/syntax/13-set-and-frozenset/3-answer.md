# python/syntax/13-set-and-frozenset — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> [1-question.md](1-question.md)의 번호와 **1:1**로 대응한다. 질문 11개 = 답 11개.
>
> 이 파일의 모든 출력은 `python3` **3.12.3** 에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> ★ **순서에 관한 답은 `PYTHONHASHSEED` 를 바꿔 던져서 얻은 것**이다 — 한 판의 결과를 결론으로 쓰지 않았다.
> 단 **집합의 순서·`getsizeof`·바이트코드 명령 이름·시간 수치**는 구현·판·실행에 달린 것이라 다른 판에서는 달라진다(10번 답).

## 정답

### 1. 문자열은 갈리고 정수는 안 갈린다 — 그래도 정수가 「보장」인 것은 아니다

**출력**

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

**왜 그런가**

| 줄 | 세 판이 | 왜 |
|---|---|---|
| **문자열** | **전부 다르다** | `hash("a")` 가 시드마다 다르다 |
| **정수** | **한 글자도 안 달랐다** | `hash(1)` 이 시드와 무관하게 `1` 이다 |
| **섞은 것** | **전부 다르다** | 문자열 원소가 칸을 다르게 차지해 **나머지를 밀어낸다** |
| `hash((3,4))` | **안 달랐다** | 정수만 든 튜플이라 문자열 해시를 안 탄다 |

★ **`hash((3,4))` 는 안 변했는데 `(3, 4)` 의 「자리」는 판마다 달랐다.**
자기 해시가 같아도 **옆 원소가 먼저 그 칸을 차지하면 밀려나기** 때문이다 — 순서는 **집합 전체의 함수**다.

문서가 무엇이 무작위화되는지 적는다 —
*"If this variable is not set or set to `random`, a random value is used to seed the hashes of **str and bytes** objects."*
그 목적도 적는다 — 악의적 입력으로 **dict 생성을 O(n²)** 로 만드는 DoS 방어다. 공격 입력은 대개 문자열이다.

**★ 「안 갈렸다」는 「보장된다」가 아니다 — 반증하는 법**

정수 집합이 세 판에서 같았다고 「정수 집합은 순서가 있다」로 적으면 틀린다. **축을 바꿔 던지면 갈린다.**

```python
print("{1, 9} ->", list({1, 9}), "| {9, 1} ->", list({9, 1}), "| == :", {1, 9} == {9, 1})
```

```text
{1, 9} -> [1, 9] | {9, 1} -> [9, 1] | == : True
```

★ **같은 집합인데(`==` 가 `True`) 차례가 다르다.** `1` 과 `9` 가 **같은 칸을 놓고 다투고**(8칸짜리 표에서 `1 % 8 == 1`, `9 % 8 == 1`),
**먼저 온 쪽이 그 칸을 차지**하기 때문이다.
**시드는 이 축을 안 건드린다** — 그래서 시드만 바꿔서는 절대 안 드러난다.

★★ **결론: 반증은 축을 바꿔 가며 해야 한다.** 이 주제에서 던져 본 축은 셋이다 —
**① 시드**(문자열이 갈린다) **② 넣은 순서**(정수도 갈린다) **③ 시드 미지정 반복 실행**(매번 갈린다).

**대조군 — dict 는 어느 축에서도 안 갈린다**

```text
seed: ['cherry', 'apple', 'banana', 'date']
seed: ['cherry', 'apple', 'banana', 'date']
seed: ['cherry', 'apple', 'banana', 'date']
```

dict 는 **순서를 따로 적어 두기** 때문이다([12번](../12-dict-and-key-requirements/2-summary.md)). set 에는 그 줄이 없다.

### 2. 네 연산 — 그리고 `sorted()` 로 감싼 이유

**출력**

```text
a & b : [3, 4] | a | b : [1, 2, 3, 4, 5]
a - b : [1, 2] | b - a : [5]
a ^ b : [1, 2, 5]
isdisjoint : True False
```

**왜 그런가**

```text
        a = {1, 2, 3, 4}        b = {3, 4, 5}

          a                  b
        ┌──────────┐
        │ 1  2 │ 3  4 │ 5  │      a & b  =  {3, 4}        가운데
        └──────┴──────────┘      a | b  =  {1,2,3,4,5}   전부
                                 a - b  =  {1, 2}        왼쪽만   ★ 방향이 있다
                                 b - a  =  {5}           오른쪽만
                                 a ^ b  =  {1, 2, 5}     가운데만 뺀 것
```

- **`-` 만 방향이 있다.** `&`·`|`·`^` 는 좌우를 바꿔도 같다.
- **`isdisjoint`** 는 `not (a & b)` 와 뜻이 같지만 **교집합을 만들지 않고** 하나만 찾으면 멈춘다.

★ **`sorted()` 로 감싼 이유 — 감싸지 않으면 이 문서가 거짓말을 하게 된다.**
`print(a & b)` 를 그냥 쓰면 그 줄이 **시드마다·실행마다 달라진다**(1번 답).
문서·로그·테스트 기댓값에 집합을 실을 때는 **`sorted()` 가 기본**이다.
여기서는 원소가 정수라 마침 안 갈렸겠지만, **「마침 안 갈리는 것」에 기대는 것이 바로 1번 답이 경고한 습관**이다.

### 3. `<=` 는 포함이다 — 그래서 셋 다 `False` 인 쌍이 생긴다

**출력**

```text
{1,2} <= {1,2,3} : True | < : True | >= : False
{1,2} <= {1,2}   : True | < : False
  p < q : False | p == q : False | p > q : False
  p <= q: False | p >= q : False
  len 은 같다 : True
```

**왜 그런가**

```text
   x = {1,2}   y = {1,2,3}         x <= y  True   x 의 원소가 전부 y 안에 있다
                                   x <  y  True   게다가 같지 않다 (진부분집합)
                                   x >= y  False  y 의 원소가 전부 x 안에 있지는 않다

   x = {1,2}   {1,2}               x <= x  True   자기 자신은 자기의 부분집합
                                   x <  x  False  "같지 않다" 를 못 만족

   p = {1,2}   q = {3,4}           ★ 포함 관계가 아예 없다
                                   p < q · p == q · p > q  -> 전부 False
                                   len 은 둘 다 2
```

문서가 그 성질에 이름을 준다 —
*"**The subset and equality comparisons do not generalize to a total ordering function.**
For example, any two nonempty disjoint sets are not equal and are not subsets of each other,
so **all** of the following return `False`: `a<b`, `a==b`, or `a>b`."*

★ 이름은 「**부분 순서(partial order)**」다 — 어느 쪽이 큰지 **정할 수 없는 쌍이 있는** 순서.
숫자·문자열은 **전순서(total order)** 라 아무 두 값이든 셋 중 하나가 반드시 참이다. **집합은 아니다.**

★ **그래서 `not (p < q)` 를 「p 가 q 이상」으로 읽으면 틀린다.** 숫자에서는 맞고 집합에서는 틀리다.
「부분집합이 아니다」와 「상위집합이다」는 **다른 말**이다.

[12번](../12-dict-and-key-requirements/2-summary.md)의 dict 는 **`<` 가 아예 `TypeError`** 다 —
**dict 는 막아 놓았고 set 은 뜻을 바꿔 놓았다.** 이 차이가 4번 답의 사고를 만든다.

### 4. 예외가 안 난다 — 결과가 「정의되지 않는다」

**출력**

```text
정렬 전 : [{3}, {1, 2}, {1}, {2}]
sorted  : [{3}, {1}, {2}, {1, 2}]
한 번 더 (입력 순서를 바꿔서) : [{1}, {2}, {1, 2}, {3}]
{1} < {2} : False | {2} < {1} : False
```

**왜 그런가**

문서가 낱말을 정해 준다 —
*"Since sets only define partial ordering (subset relationships),
**the output of the `list.sort()` method is undefined for lists of sets**."*

★ **「에러가 난다」가 아니라 「정의되지 않는다(undefined)」다.** 두 말이 아주 다르다 —
에러는 잡히고, **정의되지 않은 것은 그럴듯한 답으로 나온다.**

```text
   정렬은 "<" 로 비교한다.

   {3} 과 {1,2} 를 비교  ->  {3} < {1,2} 는 False       (포함 관계가 없다)
                            {1,2} < {3} 도 False

   즉 정렬 입장에서는 "둘이 동점" 이다.
   동점이면 10번 주제의 안정 정렬이 원래 자리를 그대로 남긴다.

   ->  결과는 "정렬된 것" 이 아니라 "입력 순서가 거의 그대로 남은 것"
   ->  입력 순서가 바뀌면 출력도 바뀐다     ★ 두 판이 다른 이유
```

- **첫 판** `[{3}, {1,2}, {1}, {2}]` → `[{3}, {1}, {2}, {1,2}]` — `{3}` 이 그대로 맨 앞이다.
- **둘째 판** `[{1}, {2}, {1,2}, {3}]` → `[{1}, {2}, {1,2}, {3}]` — **하나도 안 움직였다.**
- 움직인 자리가 있는 것은 **포함 관계가 실제로 있는 쌍**(`{1} < {1,2}`)에서만 비교가 뜻을 갖기 때문이다.

★ **[10번](../10-list-methods-and-sort-key/2-summary.md)의 「타입이 섞이면 `TypeError`」와 정확히 갈리는 자리다** —
`[3, "a"]` 는 터지는데 `[{3}, {1}]` 은 안 터진다. **`<` 가 정의되어 있어서** 통과한다.

**고치는 법 — 키를 준다**

```python
data = [{3}, {1, 2}, {1}, {2}]
print("key=len    :", sorted(data, key=len))
print("key=sorted :", sorted(data, key=sorted))
print("key=(len,…):", sorted(data, key=lambda s: (len(s), sorted(s))))
```

```text
key=len    : [{3}, {1}, {2}, {1, 2}]
key=sorted : [{1}, {1, 2}, {2}, {3}]
key=(len,…): [{1}, {2}, {3}, {1, 2}]
```

★ **세 키가 세 가지 답을 준다.** 「집합을 정렬한다」는 말 자체가 **무엇을 기준으로 할지 정해야 성립**한다 —
`key=` 를 주는 순간 정렬은 다시 **전순서** 위로 올라온다.\
★ `key=sorted` 는 **원소를 사전순으로 늘어놓은 리스트**끼리 비교하므로 `{1,2}` 가 `{2}` 보다 앞이다.
「크기순」을 원했다면 `key=len` 이고, 둘 다 원하면 `(len, sorted(s))` 처럼 **튜플 키**를 쓴다([10번](../10-list-methods-and-sort-key/2-summary.md)).

### 5. 처음 들어온 것이 남고, 차례는 넣은 순서가 정한다

**출력**

```text
{1, 1.0, True} -> {1} ['int']
{True, 1.0, 1} -> {True} ['bool']
{1.0, 1, True} -> {1.0} ['float']
{0, False} : {0} | {False, 0} : {False}
{1, 9} -> [1, 9] | {9, 1} -> [9, 1] | == : True
```

**왜 그런가**

```text
   {1, 1.0, True}

     hash 가 셋 다 1  ->  같은 칸을 본다
     1 == 1.0 == True ->  "이미 있는 원소" 로 판정된다

     set 에는 값이 없다.  ->  나중 것은 그냥 버려진다.
     ->  남는 것은 "처음 들어온 객체"  ->  타입까지 그것을 따른다
```

- ★ **세 줄의 타입이 전부 다르다**(`int`·`bool`·`float`). **넣은 차례만 바꿨을 뿐이다.**
- [12번](../12-dict-and-key-requirements/2-summary.md)의 dict 와 견주면 **규칙이 반쪽**이다 —
  dict 는 「키는 처음, **값은 나중**」인데 set 은 **값이 없으니 「처음」만 남는다.**
- `{0, False}` 도 같다.

**마지막 줄 — `==` 가 `True` 인데 차례가 다른 이유**

```text
   작은 집합의 표는 8칸이다.

   1 -> 1번 칸       9 -> 9 % 8 = 1번 칸  ★ 같은 칸을 원한다 (충돌)

   {1, 9}  :  1 이 먼저 와서 1번 칸을 차지  ->  9 는 옆 칸으로 밀린다  ->  [1, 9]
   {9, 1}  :  9 가 먼저 와서 1번 칸을 차지  ->  1 이 옆 칸으로 밀린다  ->  [9, 1]

   원소의 "집합" 은 같으므로 ==  는 True.
   "칸 배치" 는 다르므로 도는 차례가 다르다.
```

★ **`==` 는 원소만 보고 순서를 안 본다.** 그래서 **순서 사고는 `==` 테스트로 안 잡힌다** —
dict 에서와 같은 결론이다([12번](../12-dict-and-key-requirements/3-answer.md) 1번 답).

### 6. 성능 때문이 아니라 실수를 막으려고 갈라 놓았다

**출력**

```text
set('abc') & 'cbs' -> TypeError unsupported operand type(s) for &: 'set' and 'str'
set('abc').intersection('cbs') -> ['b', 'c']
s |= [4] -> TypeError unsupported operand type(s) for |=: 'set' and 'list'
s.update([4]) -> [1, 2, 4]
issubset 은 문자열도 : True
```

**왜 그런가**

문서가 **이유를 직접 적는다** —
*"the non-operator versions of `union()`, `intersection()`, `difference()`, `symmetric_difference()`, `issubset()`,
and `issuperset()` methods **will accept any iterable** as an argument.
In contrast, their operator based counterparts **require their arguments to be sets**.
**This precludes error-prone constructions** like `set('abc') & 'cbs'` in favor of the more readable `set('abc').intersection('cbs')`."*

★ **성능이 아니다.** `set('abc') & 'cbs'` 를 허용하면 **문자열을 집합으로 조용히 바꿔** 읽는 셈이 되고,
`'cbs'` 가 `{'c','b','s'}` 로 해석된다는 것을 코드만 봐서는 알 수 없다. **읽는 사람이 틀리는 것**을 막으려고 갈랐다.

★ **오류 문구가 `|=` 를 그대로 가리킨다** — `set` 은 `__ior__` 를 갖고 있고 거기서 타입을 거부하기 때문에
`|` 로 떨어지지 않는다(`set.__ior__` 는 슬롯 래퍼로 존재하고, `frozenset` 에는 없다).

**dict 와 무엇이 다른가**

| | `\|` | `\|=` | 비연산자 메서드 |
|---|---|---|---|
| **set** | 집합만 | **집합만** | `union`·`update` 는 아무 이터러블 |
| **dict** | dict 만 | **매핑 또는 (키,값) 이터러블** | `update` 는 이터러블·키워드도 |

★ **같은 기호가 두 타입에서 다른 규칙을 탄다.** dict 의 `|=` 는 받아 주는데 set 의 `|=` 는 안 받는다.
**「`|=` 는 느슨하다」로 외우면 set 에서 틀린다.**

### 7. 「불변이라서」가 아니라 「해시가 평생 안 바뀌어야 해서」다

문서 — *"The `set` type is mutable … **Since it is mutable, it has no hash value** and cannot be used as either a dictionary key
or as an element of another set. The `frozenset` type is **immutable and hashable** …"*

```text
   왜 가변이면 해시를 주면 안 되나

     s = {1, 2}
     어떤 집합 안에 s 를 넣었다  ->  hash(s) 가 가리킨 칸에 놓였다
     s.add(3)                   ->  hash 가 바뀐다
     ->  s 는 "틀린 칸" 에 남는다.  찾을 수 없고, 같은 값이 둘 들어갈 수 있다 (9번 답)

   ★ 그래서 요건은 "불변" 이 아니라 "해시가 평생 안 바뀔 것" 이다.
     glossary 가 그렇게 적는다 — "a hash value which never changes during its lifetime".
     불변은 그 요건을 만족시키는 가장 쉬운 방법일 뿐이다.
```

★ 거꾸로 **불변인데도 해시가 없는 것**이 있다 — 안에 리스트가 든 튜플이다([11번](../11-tuple-and-unpacking/2-summary.md)).
**「불변 = 해시 가능」이 아니다.**

```python
try:
    {{1, 2}}
except TypeError as e:
    print("{{1,2}}            -> TypeError:", e)
print("{frozenset({1,2})} ->", {frozenset({1, 2})})
print("set.__hash__       =", set.__hash__, "| frozenset.__hash__ is None :", frozenset.__hash__ is None)
print("set 안에 set 을 찾을 때 :", {1, 2} in {frozenset({1, 2})})
```

```text
{{1,2}}            -> TypeError: unhashable type: 'set'
{frozenset({1,2})} -> {frozenset({1, 2})}
set.__hash__       = None | frozenset.__hash__ is None : False
set 안에 set 을 찾을 때 : True
```

★ **`set.__hash__` 가 `None`** 이다 — [12번](../12-dict-and-key-requirements/2-summary.md)에서 `__eq__` 만 정의한 클래스가 겪은 것과
**같은 장치**다. 언어는 「해시 못 함」을 이 한 가지 방식으로 표현한다.

**그런데 찾을 수는 있는 이유**

문서가 예외를 적는다 — *"the *elem* argument to the `__contains__`, `remove`, and `discard` methods **may be a set**.
To support searching for an equivalent frozenset, **a temporary one is created from elem**."*

★ **넣을 때는 「평생」이 걸리지만 찾을 때는 그 순간만 있으면 된다.**
그래서 언어가 **임시 `frozenset` 을 대신 만들어** 검색만 통과시킨다. `in`·`remove`·`discard` 세 곳뿐이다.

### 8. 첫 피연산자의 타입 · 그리고 `==` 는 원소로 본다

**출력**

```text
frozenset('ab') | set('bc') -> frozenset
set('ab') | frozenset('bc') -> set
set('abc') == frozenset('abc') : True
set('abc') in set([frozenset('abc')]) : True
hash 가 같나 : True
```

**왜 그런가**

문서가 둘 다 적는다 —
*"Binary operations that mix `set` instances with `frozenset` **return the type of the first operand**.
For example: `frozenset('ab') | set('bc')` returns an instance of `frozenset`."* /
*"Instances of `set` are compared to instances of `frozenset` **based on their members**.
For example, `set('abc') == frozenset('abc')` returns `True` and so does `set('abc') in set([frozenset('abc')])`."*

```text
   왼쪽이 frozenset  ->  결과도 frozenset   (얼어 있다.  add 가 없다)
   왼쪽이 set        ->  결과도 set         (고칠 수 있다)

   ★ 함수가 집합을 받아 | 로 합쳐 돌려주면,
     돌려준 것의 타입이 "호출자가 무엇을 줬느냐" 에 달린다.
     받는 쪽에서 .add() 를 부르면 어떤 날은 되고 어떤 날은 AttributeError 다.
```

★ **이것이 이 규칙의 실무 위험**이다. 타입을 못 박으려면 `set(a | b)` 나 `frozenset(a | b)` 로 **명시**한다.

★ **`==` 는 타입을 안 본다.** [11번](../11-tuple-and-unpacking/2-summary.md)의 `namedtuple` 이 평범한 튜플과 같았던 것,
[12번](../12-dict-and-key-requirements/2-summary.md)의 `1`·`True` 가 한 키였던 것과 **같은 집안**이다 —
파이썬은 「**값이 같으면 같은 것**」을 타입을 가로질러 지킨다.

### 9. `len` 이 2가 된다 — 집합인데 같은 값이 둘 들어 있다

**출력**

```text
넣은 직후       : {Box(1)} | b in st : True
원소를 고친 뒤  : {Box(2)} | b in st : False | Box(2) in st : False
Box(2) 를 넣으면: {Box(2), Box(2)} | len = 2  <- 같은 값이 둘
```

**왜 그런가**

```text
   넣을 때   hash(Box(1)) = h1  ->  h1 칸에 놓였다
   고친 뒤   hash(Box(2)) = h2

   Box(2) in st   ->  h2 칸을 본다  ->  비어 있다  ->  False
   st.add(Box(2)) ->  h2 칸이 비었으니 "새 원소" 로 판단  ->  넣는다

   ->  표에는 h1 칸의 Box(2) 와 h2 칸의 Box(2) 가 나란히 있다
   ->  len = 2.  repr 은 {Box(2), Box(2)}
```

**[12번](../12-dict-and-key-requirements/3-answer.md) 9번 답과 같은 점과 다른 점**

| | dict | set |
|---|---|---|
| 원인 | 같다 — **해시가 바뀌었다** | 〃 |
| 예외 | **없다** | **없다** |
| 드러나는 모양 | `len` 은 1인데 **못 꺼낸다** | **`len` 이 늘어난다 — 같은 값이 둘** |
| 눈에 띄는 정도 | 조회할 때까지 모른다 | ★ **`print(s)` 에 바로 보인다** |

★ **set 쪽이 더 잘 보인다.** `{Box(2), Box(2)}` 는 **집합의 정의 자체를 어긴 모습**이라 눈에 띈다.
dict 쪽은 `{Box(2): '값'}` 이라 **겉으로는 멀쩡해 보인다.**

★ **막는 법은 같다** — 원소·키로 쓸 값을 **불변으로** 만든다(`tuple`·`frozenset`·`frozen=True` dataclass),
또는 **안 바뀌는 필드만** 해시에 넣는다.

### 10. 세 층 가르기

**언어 보장**

| 사실 | 근거 |
|---|---|
| **집합은 순서가 없다** — 위치도 삽입 순서도 기록하지 않는다 | Set Types 첫 문단 |
| 첨자·슬라이스가 **없다** | 〃 |
| **원소는 해시 가능해야** 한다(dict 키와 같은 요건) | 〃 · glossary |
| **`set` 은 가변이라 해시가 없다** · **`frozenset` 은 해시가 있다** | 〃 |
| `in`·`remove`·`discard` 의 인자로는 **`set` 을 줘도 된다**(임시 frozenset) | 〃 |
| **연산자는 집합만 · 비연산자 메서드는 아무 이터러블** — *"precludes error-prone constructions"* | 〃 |
| `<=`·`<`·`>=`·`>` 는 **부분집합 관계**이고 **전순서가 아니다** | 〃 |
| **집합 리스트의 `sort()` 결과는 정의되지 않는다**(*"undefined"*) | 〃 |
| 섞어 쓰면 **첫 피연산자의 타입** | 〃 |
| `set` 과 `frozenset` 은 **원소로 비교**된다 | 〃 |
| `pop()` 은 **임의의** 원소 · 빈 집합이면 `KeyError` | 〃 |
| `remove` 는 `KeyError` · `discard` 는 조용 | 〃 |
| **str·bytes 의 해시만** 무작위화된다 | PYTHONHASHSEED |

**CPython 구현 세부사항**

| 사실 | 어떻게 확인했나 |
|---|---|
| **`x in {1,2,3}` 의 리터럴이 `frozenset` 상수로 접힌다** | `dis` — 실행 중에 집합을 안 만든다 |
| **`x in [1,2,3]` 은 튜플 상수**가 된다 | `dis` |
| `s = {1,2,3}` 이 **`BUILD_SET` + `SET_UPDATE`**(frozenset 상수) | `dis` |
| 순회 중 변경 검사가 **크기만** 본다 | 실행 |
| `set.__ior__` 가 **존재하고 거기서 타입을 거부**한다(`frozenset` 에는 없다) | 실행 |
| `CONTAINS_OP`·`SET_UPDATE`·`POP_JUMP_IF_FALSE` 같은 **명령 이름** | `dis` — **3.11.15 에서는 `POP_JUMP_FORWARD_IF_FALSE`** 였다 |
| 예외·경고 **문구** 전부 | 실행 |

**이 판(3.12.3)·이 머신의 관찰**

| 관찰 | 어디가 흔들리나 |
|---|---|
| 문자열 집합의 **구체적 순서** | 시드마다 · 실행마다 |
| **정수 집합이 시드에 안 갈리는 것** | 시드는 안 타지만 **넣은 순서는 탄다** |
| `{1,9}` 와 `{9,1}` 의 차례가 다른 것 | 충돌 해결 순서 |
| `getsizeof(set(range(n)))` = **216 / 216 / 728 / 728**(n=0/1/5/10) | 빌드·비트 폭·재해시 시점 |
| `s.pop()` 이 `1` 을 준 것 | **임의**다 |
| `in` 비교 수치 | 머신·부하. **기울기만** 재현된다 |
| **3.11.15 와 3.12.3 의 집합 순서가 같았던 것** | ★ **둘 다 관찰이다.** 같다고 보장이 되는 게 아니다 |

```bash
for seed in 0 1; do PYTHONHASHSEED=$seed python3.11 -c \
  'print(list({"apple","banana","cherry","date","elderberry"}), list({1,2,3,4,5,100,200}))'; done
```

```text
['banana', 'apple', 'cherry', 'date', 'elderberry'] [1, 2, 3, 4, 5, 100, 200]
['date', 'elderberry', 'cherry', 'apple', 'banana'] [1, 2, 3, 4, 5, 100, 200]
```

★★ **두 판이 한 글자도 같았다 — 그래서 더 위험하다.**
같은 해시 알고리즘과 같은 테이블 배치를 쓰고 있을 뿐이고, **둘 다 문서에 없는 관찰**이다.
「두 버전에서 같았으니 안정적이다」는 이 주제에서 **가장 위험한 결론**이다.

**그래서 이렇게 적으면 틀린다**

- ✗ 「set 은 정렬된 순서로 돈다」 → **순서가 없다.** 작은 정수가 우연히 그렇게 보일 뿐.
- ✗ 「정수 집합은 순서가 보장된다」 → **시드에 안 갈릴 뿐.** 넣은 순서가 다르면 갈린다.
- ✗ 「한 판에서 안 갈렸으니 안정적」 → **축을 바꿔 던져야** 안다(시드·삽입 순서·반복 실행).
- ✗ 「3.11 과 3.12 가 같았으니 버전에 안 흔들린다」 → **둘 다 관찰**이다.
- ✗ 「`{}` 는 빈 집합」 → **빈 dict** 다.
- ✗ 「`<=` 는 크기 비교」 → **부분집합**이다.
- ✗ 「`not (a < b)` 면 `a >= b`」 → **집합에서는 틀리다.** 셋 다 `False` 인 쌍이 있다.
- ✗ 「집합 리스트 정렬은 에러」 → **안 난다.** *"undefined"* 다.
- ✗ 「`|` 에 리스트를 넘겨도 된다」 → **집합만.** `.union()` 은 받는다.
- ✗ 「set 의 `|=` 도 dict 처럼 이터러블을 받는다」 → **안 받는다.**
- ✗ 「set 을 집합의 원소로 넣을 수 있다」 → **`frozenset` 으로 얼려야** 한다. 단 **찾기는 된다.**
- ✗ 「`frozenset` 은 `set` 과 다른 값」 → **원소로 비교**한다.
- ✗ 「불변이면 해시 가능」 → **`(1, [2])` 가 반례**다([11번](../11-tuple-and-unpacking/2-summary.md)).
- ✗ 「`pop()` 은 첫 원소」 → **임의**다.

### 11. 조용한 실패 세 자리

| 자리 | 무엇이 조용히 틀리나 | 무엇으로 막나 |
|---|---|---|
| **`list(set(...))` 의 순서** | **실행마다 달라진다.** 테스트·로그·파일 출력이 흔들린다 | `sorted(...)` · `dict.fromkeys(...)` |
| **집합이 든 리스트 정렬** | **예외 없이** 「정렬 안 된 것」이 나오고 **입력 순서에 따라 결과가 바뀐다** | `key=len` · `key=sorted` |
| **원소를 넣은 뒤 고치기** | **같은 값이 둘** 들어간다 | 원소를 불변으로 · 해시에 안 바뀌는 필드만 |
| (보태기) **`1`·`True` 혼용** | 하나로 합쳐지고 **타입까지 처음 것**을 따른다 | 원소 타입을 정규화 · `len` 확인 |
| (보태기) **`set` ↔ `frozenset` 혼용** | `a \| b` 의 **결과 타입이 왼쪽에 달린다** | `set(...)`·`frozenset(...)` 으로 못 박기 |
| (보태기) **`not (a < b)` 를 `a >= b` 로 읽기** | 겹치지 않는 쌍에서 **둘 다 `False`** | `a.issuperset(b)` 를 직접 쓴다 |

막는 코드는 이렇게 생겼다.

```python
print(sorted(tags))                        # 출력에 집합을 실을 때는 반드시
unique = list(dict.fromkeys(items))        # 순서를 지키는 중복 제거

groups = sorted(list_of_sets, key=sorted)  # 집합 정렬에는 키를 준다

from dataclasses import dataclass
@dataclass(frozen=True)                    # 원소로 쓸 값은 얼린다
class Tag:
    name: str

def merge(a, b) -> set:
    return set(a | b)                      # 결과 타입을 못 박는다
```

## 실행 검증

```text
$ python3 --version
Python 3.12.3
$ python3 -c "import sys; print(sys.implementation.name)"
cpython
$ python3.11 --version
Python 3.11.15
$ nproc
24
$ grep -m1 'model name' /proc/cpuinfo
model name	: 13th Gen Intel(R) Core(TM) i7-13700HX
```

| 문항 | 무엇을 돌렸나 | 몇 번 |
|---|---|---|
| 1 | 집합 순서 — **시드 0·1·2** × (문자열·정수·섞인 것·해시 4종) | **3판** |
| 1 | 시드 **미지정**으로 같은 명령 반복 | **3판** |
| 1 | `{1,9}` 대 `{9,1}` — 시드 **0·1** | 2판 |
| 1 | dict 대조군 — 시드 **0·1·2** | 3판 |
| 2 | 집합 연산 **6항목**(`&`·`\|`·`-` 양방향·`^`·`isdisjoint` 2) | 각 1회 |
| 3 | 비교 **10항목**(`<=`·`<`·`>=` × 3쌍 + `len`) | 각 1회 |
| 4 | 집합 리스트 정렬 — **입력 순서 2가지** + `<` 2형태 + `key=` **3형태** | 각 1회 |
| 5 | 같은 값 합치기 **5형태**(넣은 차례 3 + `add` + `0`/`False` 2) | 각 1회 |
| 6 | 연산자/메서드 **8형태**(`&` 실패·`intersection`·`\|` 실패·`union`·`\|=` 성공/실패·`update`·`issubset`) | 각 1회 |
| 7 | 해시 요건 **5항목**(`{{1,2}}`·`frozenset` 원소·dict 키·`__hash__` 2·임시 frozenset) | 각 1회 |
| 8 | 섞어 쓰기 **7항목**(타입 2 · `==` · `in` · `hash` · 빈 것 3) | 각 1회 |
| 9 | 가변 원소 **6항목**(`in` 3형태 · `add` 후 `len`·`repr`) | 각 1회 |
| 10 | `dis` 3형태 · `getsizeof` 4종 · `__ior__` 3종 · **3.11.15 대조** 2판 | 각 1회 |
| 10 | `remove`/`discard`/`pop` **5항목** · 컴프리헨션 1 | 각 1회 |
| 비용 | `timeit` — n=1000·100000 × (list·set) | **`repeat=7` 최솟값 × 3판** |

**★ 한 판으로 결론이 안 나는 것을 여러 판 던진 자리 — 이 주제의 값이 전부 여기 있다**

- ★★ **1번** — **기본 실행 한 판**만 보면 「집합 순서는 이렇다」로 적게 된다.
  **시드를 0·1·2 로 바꿔** 던져야 문자열이 갈리는 것이 보인다.
  그런데 **거기서 멈추면 두 번째 잘못**을 저지른다 — 정수가 세 판에서 같았다고 「정수는 순서가 있다」로 적게 된다.
  **축을 바꿔**(`{1,9}` 대 `{9,1}`) 던져야 그것도 갈린다는 것이 드러난다. **축 셋을 다 던져야 결론이 선다.**
- ★ **1번(대조군)** — set 만 보면 「해시 자료구조라 순서가 없다」로 끝난다.
  **같은 시드로 dict 를 던져** 봐야 「순서줄이 따로 있느냐」가 진짜 이유라는 것이 드러난다.
- ★ **4번** — **한 번만** 정렬하면 `[{3}, {1}, {2}, {1,2}]` 가 「어떤 규칙의 결과」처럼 보인다.
  **입력 순서를 바꿔** 한 번 더 던져야 **결과가 입력에 딸려 온다**는 것이 드러난다.
- **5번** — `{1, 1.0, True}` 만 보면 「int 가 남는다」로 결론이 선다.
  **넣는 차례를 세 가지로** 바꿔야 「**처음 것**이 남는다」가 드러난다(타입이 `bool`·`float` 로도 남는다).
- **8번** — `frozenset | set` 만 보면 「frozenset 이 이긴다」로 읽힌다.
  **좌우를 바꿔** 던져야 「**첫 피연산자**」가 규칙이라는 것이 드러난다.
- **10번** — 3.12 만 보면 명령 이름을 사실처럼 적게 된다. **3.11.15 로 대조**하니 점프 명령이 달랐다.
  그런데 **집합 순서는 두 판이 같았다** — 그래서 「같다」를 결론으로 쓰지 않았다.
- **비용** — 한 판만 재면 배율을 단정하게 된다. **3판**을 재니 `253.9x`\~`315.0x` 로 흔들렸다.
  **재현되는 것은 배율이 아니라 「n 이 100배면 list 는 100배, set 은 그대로」라는 기울기**다.

**「에러가 안 난 것」이 근거인 자리**

- 4번 — `sorted(list_of_sets)` 가 **예외 없이** 결과를 준 것이 *"undefined"* 의 증거다.
- 9번 — `st.add(Box(2))` 가 **예외 없이** 통과해 `len` 이 2가 된 것이 「언어가 감시하지 않는다」의 증거다.
- 7번 — `{1,2} in {frozenset({1,2})}` 가 **예외 없이 `True`** 인 것이 「임시 frozenset」의 증거다.
- 5번 — `{1, 1.0, True}` 가 **예외 없이** 하나가 된 것이 「같은 칸」의 증거다.

**구현 의존 항목 — 버전이 오르면 다시 찍을 것**

| 다시 찍을 것 | 왜 |
|---|---|
| 1번의 **모든 순서 출력** | 시드·실행·구현에 달렸다. **애초에 보장이 없다** |
| 10번의 `dis` 명령 이름 | **3.11.15 에서 이미 달랐다** |
| 10번의 `getsizeof` 값 전부 | 빌드·비트 폭·재해시 시점 |
| `{1,9}` 대 `{9,1}` 의 차례 | 충돌 해결 순서는 구현이다 |
| `s.pop()` 이 준 값 | **임의**라고 문서가 적는다 |
| 비용 수치 전부 | 머신·부하. **기울기만** 남긴다 |
| 예외·경고 **문구** 전부 | 종류는 명세지만 문구는 아니다 |

나머지(순서가 없다는 것 자체, 원소의 해시 요건, `set`/`frozenset` 의 해시 가능 여부, 임시 frozenset 검색,
연산자와 메서드의 비대칭, 부분 순서와 `sort` 의 미정의, 첫 피연산자 타입 규칙, `set == frozenset`)는
**언어 보장**이므로 어떤 구현에서도 같아야 한다.
