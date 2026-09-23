# python/syntax/12-dict-and-key-requirements — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> [1-question.md](1-question.md)의 번호와 **1:1**로 대응한다. 질문 11개 = 답 11개.
>
> 이 파일의 모든 출력은 `python3` **3.12.3** 에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> 단 **`getsizeof`·바이트코드 명령 이름·`hash(nan)` 의 값**은 구현·판·실행에 달린 것이라
> 다른 구현·다른 판에서는 달라진다(10번 답).

## 정답

### 1. 넣은 순서 그대로 — 덮어쓰기는 자리를 안 옮기고 지우고 넣기는 맨 뒤로 보낸다

**출력**

```text
세 번 넣고 출력     : {'c': 1, 'a': 2, 'b': 3} | ['c', 'a', 'b']
있는 키에 다시 대입 : ['c', 'a', 'b']
지우고 다시 넣으면  : ['a', 'b', 'c']
== 는 순서를 안 본다: True
list()는 순서를 본다: False
reversed(d)         : ['c', 'b', 'a']
popitem()           : ('z', 3)
```

**왜 그런가**

```text
  d["c"]=1  d["a"]=2  d["b"]=3        순서줄:  c  a  b

  d["c"] = 99        값만 바꾼다       순서줄:  c  a  b     <- 자리 그대로
  del d["c"]         자리를 뺀다       순서줄:  a  b
  d["c"] = 1         새로 넣는다       순서줄:  a  b  c     <- 맨 뒤
```

문서가 세 문장으로 정확히 그렇게 적는다 —
*"Dictionaries preserve insertion order. Note that **updating a key does not affect the order**.
**Keys added after deletion are inserted at the end**."*

**어디까지가 언어 보장인가**

| 결과 | 층 | 근거 · 언제부터 |
|---|---|---|
| 삽입 순서 유지 · 덮어쓰기는 자리 불변 · 지우고 넣기는 맨 뒤 | **언어 보장** | Mapping Types · **3.7** |
| `==` 가 순서를 안 본다 | **언어 보장** | *"regardless of ordering"* |
| `reversed(d)` 가 된다 | **언어 보장** | **3.8** 부터 |
| `popitem()` 이 **마지막** 것을 뺀다(LIFO) | **언어 보장** | **3.7** 부터 |
| 3.6 에서도 순서가 유지된 것 | **CPython 구현** | 3.6 릴리스 문서가 「기대지 말라」고 적었다 |

★ **`==` 가 `True` 인데 `list()` 비교는 `False`** 다. 그래서 **순서 사고는 `==` 테스트로 안 잡힌다** —
순서를 지켜야 하는 코드의 테스트는 `list(d1) == list(d2)` 나 `list(d.items())` 로 써야 한다.

### 2. 키는 먼저 들어온 것이 남고 값은 나중에 쓴 것이 이긴다

**출력**

```text
hash : 1 1 1 1
d = {1: '불리언'} | len = 1 | 키의 타입 = ['int']
d2 = {True: '나중 정수'} | 키 타입: ['bool'] | d2[1.0] = 나중 정수
0 과 False : {0: '거짓'}
'1' 은     : {1: '정수', '1': '문자열'}
Decimal    : {1: 'c'}
```

**왜 그런가**

```text
  {1: "정수",  1.0: "실수",  True: "불리언"}

    hash 가 전부 1  ->  같은 칸을 본다
    1 == 1.0 == True ->  "이미 있는 키" 로 판정된다

    그래서 새 키를 넣는 게 아니라 "값을 덮어쓴다"
      -> 키는 처음 것(int 1) 이 남고
      -> 값은 마지막에 쓴 것("불리언") 이 이긴다
```

문서가 이 셋을 **예시로 직접** 든다 —
*"Values that compare equal (such as `1`, `1.0`, and `True`) **can be used interchangeably to index the same dictionary entry**."*

- ★ **`d2` 의 키 타입이 `bool`** 이다 — 먼저 들어간 것이 `True` 였기 때문이다.
  `json.dumps({True: 1})` 을 하면 `{"true": 1}` 이 나간다. **「숫자 키였는데」가 여기서 조용히 어긋난다.**
- **`0` 과 `False`** 도 한 칸이다.
- **`Decimal("1")` 도 한 칸**이다 — 파이썬 수 타입은 「값이 같으면 해시도 같다」를 **타입을 가로질러** 지킨다.
- **`"1"` 은 다른 칸**이다. 문자열은 수와 `==` 가 아니다.

★ **한 문장으로**: **키는 처음, 값은 나중.** 두 규칙이 **반대 방향**이라 헷갈린다.

### 3. 뷰는 창이다 — `values()` 만 집합 연산이 안 되는 이유

**출력**

```text
받아 둔 직후 : dict_keys(['a', 'b']) dict_values([1, 2]) dict_items([('a', 1), ('b', 2)])
원본을 바꾼 뒤: dict_keys(['b', 'c']) dict_values([2, 3]) dict_items([('b', 2), ('c', 3)]) | len(ks) = 2
ks[0] -> TypeError 'dict_keys' object is not subscriptable
집합 연산 : ['b'] {('b', 2)}
values() & {1} -> TypeError unsupported operand type(s) for &: 'dict_values' and 'set'
values 끼리 == : False
```

**왜 그런가**

문서 — *"They provide a **dynamic view** on the dictionary's entries,
which means that **when the dictionary changes, the view reflects these changes**."*

```text
   ks = d.keys()

   ks 는 d 의 사본이 아니라 d 를 들여다보는 창이다.
   d 가 바뀌면 ks 도 바뀐다.  len(ks) 도 바뀐다.
   창에는 "몇 번째" 라는 개념이 없다  ->  ks[0] 은 TypeError
```

**`keys()`·`items()` 는 되고 `values()` 는 안 되는 이유**

| 뷰 | 원소가 | 집합 연산 | `==` |
|---|---|---|---|
| `keys()` | **유일**하고 **해시 가능** | 된다(`&` `\|` `-` `^`) | 집합처럼 비교 |
| `items()` | 키가 유일 · **값이 해시 가능하면** | 된다 | 〃 |
| `values()` | **중복 가능** · 해시 보장 없음 | **안 된다** | **언제나 `False`** |

★ **집합 연산은 「원소가 유일하고 해시 가능하다」 위에서만 성립한다.**
값은 둘 다 아니다 — 그래서 `&` 가 없고, `==` 도 원소 비교로 안 내려가 **`object` 의 정체 비교**로 떨어진다.
그래서 **같은 사전의 `values()` 끼리도 `False`** 다.

★ **`items() & {("b", 2)}` 가 되는 것**은 값이 해시 가능할 때뿐이다. 값이 리스트면 그 순간 `TypeError` 가 난다.

### 4. (가)는 터지고 (나)는 조용히 틀린다

**출력 — (가)**

```text
Traceback (most recent call last):
  File "<stdin>", line 2, in <module>
RuntimeError: dictionary changed size during iteration
```

**출력 — (나)**

```text
돌았다: a
돌았다: b
돌았다: z
끝: {'a': 1, 'b': 2, 'z': 9}
```

**왜 그런가**

★ **예외가 난 줄은 `for k in d:` 다**(2번째 줄). `d["d"] = 4` 가 아니다 —
**다음 원소를 꺼내려는 순간** 이터레이터가 크기를 다시 세어 보고 거기서 터진다.

```text
  (가)  크기 3 -> 4      크기가 변했다   ->  RuntimeError

  (나)  del d["c"]  크기 3 -> 2
        d["z"] = 9  크기 2 -> 3         ★ 다음 검사 시점에는 3 그대로

        -> 검사를 통과한다.
        -> 'c' 는 자리에서 사라졌으니 한 번도 안 돌고
           'z' 는 'c' 가 비운 뒤의 자리에 들어가 돌아진다.
```

문서가 **두 갈래를 다 적는다** —
*"Iterating views while adding or deleting entries in the dictionary
**may raise a RuntimeError or fail to iterate over all entries**."*

★★ **「순회 중 변경하면 예외가 난다」만 외우면 (나)를 놓친다.**
(나)에는 **예외도 경고도 없고**, `'c'` 를 빠뜨렸다는 흔적이 결과 어디에도 없다.
검사가 보는 것은 **크기뿐**이기 때문이다.

**막는 법**

```python
for k in list(d):     # 열쇠를 먼저 떠낸다
    ...
d = {k: v for k, v in d.items() if 조건}   # 또는 새 dict 를 만든다
```

**값만 바꾸는 것은 안전하다** — 크기가 안 변하고 자리도 안 변한다.

### 5. 값은 오른쪽이 이기고 자리는 왼쪽이 남는다

**출력**

```text
a | b : {'x': 1, 'y': 20, 'z': 30}
b | a : {'y': 2, 'z': 30, 'x': 1}
{**a,**b} : {'x': 1, 'y': 20, 'z': 30}
c |= [(k,9),(y,0)] : {'x': 1, 'y': 0, 'k': 9}
a | [...] -> TypeError unsupported operand type(s) for |: 'dict' and 'list'
```

**왜 그런가**

```text
  b | a       b = {"y":20, "z":30}   a = {"x":1, "y":2}

   1) b 를 그대로 복사한다        ->  y(20)  z(30)
   2) a 를 update 한다
        x 는 새 키   ->  맨 뒤에 붙는다
        y 는 있는 키 ->  ★ 덮어쓰기다.  자리는 그대로, 값만 2 로

   ->  {'y': 2, 'z': 30, 'x': 1}
```

★ **`y` 가 0번 자리인데 값이 `2`다.** 「덮어쓰기는 자리를 안 옮긴다」(1번 답)가 여기서 그대로 작동한다.
**자리는 왼쪽이 정하고 값은 오른쪽이 정한다** — 한 연산 안에서 방향이 둘로 갈린다.

| 쓰는 법 | 새 dict 인가 | 오른쪽에 무엇을 받나 | 버전 |
|---|---|---|---|
| `a \| b` | 새로 만든다 | **dict 만** (*"which must both be dictionaries"*) | 3.9 |
| `a \|= b` | a 를 고친다 | 매핑 **또는 (키,값) 이터러블** | 3.9 |
| `{**a, **b}` | 새로 만든다 | **매핑**(`keys()` 가 있으면 된다) | 3.5 |
| `a.update(b)` | a 를 고친다 | dict · 이터러블 · 키워드 인자 | 오래됨 |

★ **`|` 와 `|=` 가 받는 것이 다르다** — 이것은 **문서가 갈라 놓은 것**이지 우연이 아니다.
`c |= [("k",9),("y",0)]` 에서 `y` 의 자리가 그대로인 것도 같은 규칙이다.

★ **전부 얕은 병합**이다. 값이 dict 면 **통째로 교체**된다 — 중첩 설정에는 못 쓴다.

### 6. `Plain` 2개 · `OnlyEq` 불가 · `Both` 1개 · `Liar` 2개

**출력**

```text
Plain  : 2
OnlyEq : __hash__ = None
Both   : {Both(1): '둘째'}
Liar   : 2
```

**왜 그런가**

| 클래스 | `__eq__` | `__hash__` | 결과 | 왜 |
|---|---|---|---|---|
| `Plain` | 없음(정체) | `object` 의 것 | 키 **2개** | 값이 같아도 **다른 객체**라 `==` 가 거짓 |
| `OnlyEq` | 있음 | **`None`** | **키가 못 된다** | 언어가 꺼 버린다 |
| `Both` | 있음 | 있음 | 키 **1개**, 값은 `'둘째'` | 같은 값 = 같은 키 |
| `Liar` | 있음 | **늘 0** | 키 **2개** | 해시가 같아도 `==` 가 다르면 딴 키 |

문서가 `OnlyEq` 의 규칙을 직접 적는다 —
*"A class that overrides `__eq__` and does not define `__hash__`
will have its `__hash__` **implicitly set to None**."*

★ **이것은 「깜빡했다」가 아니라 언어가 막은 것이다.** `__eq__` 를 바꿨다는 건 「같음의 기준을 바꿨다」는 뜻인데,
해시를 안 바꾸면 **「`==` 면 해시도 같다」 계약이 깨지기** 때문이다. 깨진 채 쓰이느니 **못 쓰게 한다.**

★ **`Liar` 가 합법인 이유 — 계약은 한 방향뿐이다.**

```text
   계약:  x == y   ->   hash(x) == hash(y)        ★ 이것만 요구한다

   거꾸로는 요구하지 않는다:
          hash(x) == hash(y)  ->  x == y          ✗ 필요 없다

   그래서 "해시가 전부 0" 은 계약을 어기지 않는다.
   결과가 틀리지 않고 "느려질" 뿐이다 (모든 키가 한 칸에 몰려 선형 탐색이 된다).
```

`Both` 에서 남은 키가 **먼저 것**(`Both(1)`)이고 값이 **나중 것**(`'둘째'`)인 것은 2번 답과 같은 규칙이다.

### 7. 3.6 까지는 구현 세부, 3.7 부터 언어 보장 — 문서가 승격을 기록해 두었다

세 문장이 세 시점을 말한다.

**① 3.6 — 구현이 그렇게 하게 됐지만 기대면 안 된다** (What's New In Python 3.6, "New dict implementation")

*"The order-preserving aspect of this new implementation is **considered an implementation detail and should not be relied upon**
(this may change in the future, but it is desired to have this new dict implementation in the language for a few releases
**before changing the language spec to mandate order-preserving semantics** for all current and future Python implementations;
this also helps preserve backwards-compatibility with older versions of the language where random iteration order is still in effect, e.g. Python 3.5)."*

**② 3.7 — 명세의 일부로 선언** (What's New In Python 3.7, Summary – Release Highlights)

*"the insertion-order preservation nature of dict objects **has been declared to be an official part of the Python language spec**."*

**③ 지금의 라이브러리 레퍼런스 — 승격 사실까지 남겨 둔다** (Mapping Types — dict)

*"Changed in version 3.7: Dictionary order is guaranteed to be insertion order.
**This behavior was an implementation detail of CPython from 3.6**."*

```text
   3.5 이하        3.6                        3.7 이후
  ┌────────┐    ┌───────────────┐        ┌──────────────┐
  │ 순서 없음 │ -> │ CPython 구현   │  승격 -> │ 언어 보장      │
  └────────┘    │ "기대하지 말 것" │        │ 모든 구현이 지켜야 │
                └───────────────┘        └──────────────┘
```

★ **이 주제가 「세 층」의 가장 좋은 본보기인 이유**가 여기 있다 —
**동작은 한 글자도 안 바뀌었는데 「누가 보장하나」가 바뀌었다.**
3.6 에서 이 순서에 기댄 코드는 **그때는 틀린 코드**였고 지금은 맞는 코드다.

★ 뒤집어 말하면: **지금 관찰되는 것 중에도 3.6 의 dict 순서 같은 것이 있다.**
그래서 관찰은 관찰로 적고 보장은 문서로만 적는다.

### 8. 키를 만드는 것은 `setdefault` 와 `defaultdict[k]` 둘뿐이다

| 쓰는 법 | 없는 키를 만드나 | 돌려주는 것 |
|---|---|---|
| `d.get(k)` · `d.get(k, 기본)` | **안 만든다** | `None` · 기본값 |
| `k in d` | **안 만든다** | `bool` |
| `d.setdefault(k, 기본)` | ★ **만든다** | 있으면 기존 값, 없으면 넣은 기본값 |
| `defaultdict(list)[k]` | ★ **만든다** | 팩토리가 만든 값 |
| `defaultdict(list).get(k)` | **안 만든다** | `None` — `get` 은 `__missing__` 을 안 탄다 |

**출력**

```text
★ 조회만 해도 키가 생긴다: [] | {'영업': ['김', '박'], '개발': ['이'], '없는부서': []}
  get 은 안 만든다        : None | ['영업', '개발', '없는부서']
  in 도 안 만든다         : False | ['영업', '개발', '없는부서']
```

**어떤 사고가 나나**

- **`defaultdict` 를 읽기 경로에 쓰면** 오타 한 번마다 키가 하나씩 는다.
  그 사전을 그대로 직렬화하면 **없던 항목이 파일·응답에 섞여 나간다.** 예외는 없다.
- **`d.setdefault(k, 무거운것())`** 은 **키가 이미 있어도 인자를 평가한다.** `defaultdict` 는 없을 때만 팩토리를 부른다.
- 거꾸로 **`setdefault` 는 쓰기 한 줄로 묶기를 끝낼 수 있고** 일반 `dict` 라 **읽기 경로가 안전하다.**

★ **`setdefault` 라는 이름이 거짓말이다** — 「기본값을 설정한다」가 아니라 「**없으면 넣고 어쨌든 돌려준다**」다.

### 9. `len` 은 1인데 어떤 키로도 못 꺼낸다 — 그리고 예외가 아니다

**출력**

```text
넣은 직후 : {Box(1): '값'} | k in d : True
키를 고친 뒤 : {Box(2): '값'} | k in d : False | Box(2) in d : False | Box(1) in d : False
그런데 순회하면 보인다 : [(Box(2), '값')]
len = 1
d[k] -> KeyError: Box(2)
```

**왜 그런가**

```text
   넣을 때   hash(Box(1)) = h1   ->  h1 칸에 넣었다
   고친 뒤   hash(Box(2)) = h2

   조회 d[k]      hash(k)=h2  ->  h2 칸만 본다  ->  비어 있다   ->  KeyError
   조회 Box(1)    hash=h1     ->  h1 칸을 본다  ->  거기 Box(2) 가 있는데
                                   ★ == 가 거짓이라 "다른 키" 로 판정  ->  없다
   순회           칸을 처음부터 끝까지 훑는다     ->  보인다
```

★ **찾는 길과 도는 길이 다르기 때문**이다(「한눈에」의 그림). 조회는 해시로 **한 칸만** 보고, 순회는 **전부** 훑는다.

**왜 예외가 아닌가**

파이썬은 **키가 고쳐졌는지 감시하지 않는다.** 감시하려면 매 조회마다 해시를 다시 계산해 비교해야 하고,
그것은 dict 의 존재 이유(평균 한 번에 찾기)를 깨뜨린다.
그래서 언어는 **감시 대신 계약**을 건다 — glossary 의 *"a hash value which **never changes during its lifetime**"* 이 그것이고,
`object.__hash__` 문서가 결과까지 미리 적어 둔다 — *"if the object's hash value changes, **it will be in the wrong hash bucket**."*

★ **계약을 어긴 쪽이 대가를 치른다.** 언어는 안 막아 준다.
막는 법은 **키를 불변으로 만드는 것**뿐이다 — `tuple`·`frozenset`·`frozen=True` dataclass,
또는 **안 바뀌는 필드만** 해시에 넣기.

### 10. 세 층 가르기

**언어 보장**

| 사실 | 근거 | 언제부터 |
|---|---|---|
| 삽입 순서 유지 · 덮어쓰기는 자리 불변 · 지우고 넣으면 맨 뒤 | Mapping Types | **3.7** |
| `==` 는 순서를 안 본다 · `<`·`<=`·`>`·`>=` 는 `TypeError` | 〃 | — |
| 키는 **해시 가능**해야 한다 | 〃 · glossary | — |
| `1`·`1.0`·`True` 가 **같은 칸** | 〃 (*"interchangeably"*) | — |
| `__eq__` 만 재정의 → `__hash__` 가 **`None`** | `object.__hash__` | 파이썬 3 전체 |
| 해시는 **평생 불변**이어야 한다 | glossary | — |
| `keys()`·`values()`·`items()` 는 **동적 뷰** | Dictionary view objects | 파이썬 3 전체 |
| 순회 중 변경은 **`RuntimeError` 또는 전부 돌지 못함** | 〃 | — |
| 뷰의 `reversed()` | 〃 | **3.8** |
| `d \| other`(dict 만) · `d \|= other`(이터러블도) · **오른쪽 값이 이긴다** | Mapping Types | **3.9** |
| `popitem()` 은 **마지막** 것(LIFO) | 〃 | **3.7** |
| **str·bytes 의 해시만** 무작위화된다 | PYTHONHASHSEED | 3.2.3 |

**CPython 구현 세부사항**

| 사실 | 어떻게 확인했나 |
|---|---|
| **3.6 에서의 삽입 순서 유지** | 3.6 릴리스 문서가 「기대지 말라」고 직접 적는다 |
| **크기가 같으면 순회 중 변경이 안 잡힌다** | 실행(4번 답) — 검사가 크기만 본다 |
| `{**a, **b}` 가 **`BUILD_MAP` + `DICT_UPDATE` ×2** | `dis` |
| `a \| b` 가 **`BINARY_OP 7 (\|)`** | `dis` |
| `RETURN_CONST` 같은 명령 이름 | `dis` — **3.11.15 에서는 `LOAD_CONST` + `RETURN_VALUE`** 였다 |
| 예외 **문구** 전부(`dictionary changed size during iteration` 등) | 실행 |

**이 판(3.12.3)·이 머신의 관찰**

| 관찰 | 어디가 흔들리나 |
|---|---|
| `getsizeof(dict.fromkeys(range(n)))` = **64 / 224 / 224 / 352**(n=0/1/5/10) | 빌드·비트 폭·재해시 시점 |
| `hash(float("nan"))` 의 **값** | **같은 시드로도 판마다 다르다** — 3.10+ 에서 정체 기반이다. 아래 두 줄은 **다시 돌리면 또 달라진다** |
| 문자열 해시의 구체적 수치 | 시드마다 다르다 |

```python
import sys
print("dict 0/1/5/10 :", [sys.getsizeof(dict.fromkeys(range(i))) for i in (0, 1, 5, 10)])
```

```text
dict 0/1/5/10 : [64, 224, 224, 352]
```

```bash
for i in 1 2; do PYTHONHASHSEED=0 python3 -c 'print(hash(float("nan")))'; done
```

```text
8023777811245
8652895139629
```

★ **시드를 고정해도 안 굳는 것이 있다.** `PYTHONHASHSEED` 는 **str·bytes** 만 잡는다.

**그래서 이렇게 적으면 틀린다**

- ✗ 「dict 순서는 CPython 구현 세부사항」 → **3.6 까지**의 이야기다. 3.7 부터 명세다.
- ✗ 「dict 는 원래 순서가 없다」 → **3.5 이하**의 이야기다.
- ✗ 「`1` 과 `True` 는 다른 키」 → 같은 칸. **키는 먼저, 값은 나중.**
- ✗ 「`d.keys()` 는 목록」 → **동적 뷰.** 첨자도 못 쓴다.
- ✗ 「순회 중 변경하면 `RuntimeError`」 → **크기가 같으면 안 난다. 대신 빠뜨린다.**
- ✗ 「`setdefault` 는 읽기」 → **키를 만든다.**
- ✗ 「`defaultdict` 를 읽어도 된다」 → **`dd[k]` 는 키를 만든다.**
- ✗ 「병합은 왼쪽이 이긴다」 → **값은 오른쪽, 자리는 왼쪽.**
- ✗ 「`__eq__` 를 만들었으니 키로 쓸 수 있다」 → **`__hash__` 가 꺼진다.**
- ✗ 「해시가 같으면 같은 키」 → **`==` 도 봐야 한다**(`Liar`).
- ✗ 「dict 순서도 `PYTHONHASHSEED` 에 흔들린다」 → **안 흔들린다.** 그건 `set` 이다([13번](../13-set-and-frozenset/2-summary.md)).

### 11. 조용한 실패 세 자리

| 자리 | 무엇이 조용히 틀리나 | 무엇으로 막나 |
|---|---|---|
| **순회 중 「크기가 같은」 변경** | 예외 없이 **원소를 빠뜨리고 안 넣은 것을 돈다**(4번 답) | `for k in list(d)` · 새 dict 를 만든다 |
| **`1`·`1.0`·`True` 키** | 칸이 하나로 합쳐지는데 **에러가 없다.** 키 타입까지 바뀐다 | 키를 한 타입으로 정규화 · `len` 을 확인 |
| **키를 넣은 뒤 고치기** | `len` 은 그대로인데 **못 꺼낸다**(9번 답) | 키를 불변으로 · 해시에 안 바뀌는 필드만 |
| (보태기) **`defaultdict` 읽기** | 조회가 **키를 만든다** | `dd.get(k)` · `k in dd` |
| (보태기) **`dict.fromkeys(ks, [])`** | 모든 키가 **한 리스트를 공유**한다 | `{k: [] for k in ks}` |
| (보태기) **`==` 로 순서 검사** | 순서가 달라도 **`True`** 다 | `list(d1) == list(d2)` |

막는 코드는 이렇게 생겼다.

```python
for k in list(d):                       # 열쇠를 먼저 떠낸다
    if 조건(k):
        del d[k]

def normalize_key(k):                   # 숫자 키를 한 타입으로
    return str(k) if isinstance(k, (int, float, bool)) else k

from dataclasses import dataclass
@dataclass(frozen=True)                 # 키로 쓸 값은 얼린다
class Point:
    x: int
    y: int

counts = {k: [] for k in keys}          # fromkeys(keys, []) 를 쓰지 않는다
```

## 실행 검증

```text
$ python3 --version
Python 3.12.3
$ python3 -c "import sys; print(sys.implementation.name)"
cpython
$ python3.11 --version
Python 3.11.15
```

| 문항 | 무엇을 돌렸나 | 몇 번 |
|---|---|---|
| 1 | 삽입 순서 **7형태**(삽입·덮어쓰기·삭제 후 재삽입·`==`·`list`·`reversed`·`popitem`) | 각 1회 |
| 1 | `PYTHONHASHSEED` **0·1·2** 로 dict 순서 대조 | 3회 |
| 2 | 수 키 **8형태**(`int`·`float`·`bool`·`complex`·`Fraction`·`Decimal`·`0`/`False`·`"1"`) | 각 1회 |
| 3 | 뷰 **12항목**(3종 뷰 · 추가·삭제 반영 · `len` · 첨자 · 집합 연산 4 · `values` 실패 · `==`) | 각 1회 |
| 4 | 순회 중 변경 **5형태**(추가·삭제·크기 유지·값만·`list()` 로 뜨기) + 뷰 이터레이터 1 | 각 1회 |
| 5 | 병합 **8형태**(`\|` 양방향 · `{**}` · `\|=` dict · `\|=` 이터러블 · `\|` 실패 · `update` · 원본 불변) | 각 1회 |
| 5 | `dis` — `a \| b` · `{**a, **b}` · `a \|= b` | 각 1회 |
| 6 | 클래스 **4종** × (해시 가능 여부 · 키 개수 · 남는 키/값) | 각 1회 |
| 8 | `get`·`setdefault`·`defaultdict[k]`·`defaultdict.get`·`in` **9항목** | 각 1회 |
| 9 | 가변 키 **7항목**(`in` 3형태 · 순회 · `len` · `d[k]`) | 각 1회 |
| 10 | `getsizeof` 4종 · `hash(nan)` 시드 고정 2판 · `nan`/`-0.0` 키 8항목 | 표기한 횟수 |
| 10 | **3.11.15** 로 2·1번 블록과 `dis` 대조 | 각 1회 |

**★ 한 판으로 결론이 안 나는 것을 여러 판 던진 자리**

- ★★ **4번** — `d["d"] = 4` 하나만 던지면 「순회 중 변경은 `RuntimeError`」로 결론이 선다.
  **지운 만큼 다시 넣어 크기를 맞춘 판**을 던져야 **예외 없이 원소를 빠뜨리는** 쪽이 드러난다.
  문서의 *"or fail to iterate over all entries"* 가 그제야 읽힌다.
- **2번** — `{1: ..., True: ...}` 만 보면 「합쳐진다」로 끝난다.
  **순서를 뒤집어** `{True: ..., 1: ...}` 를 던져야 **키 타입이 `bool` 로 남는 것**이 드러난다.
- **5번** — `a | b` 만 보면 「오른쪽이 이긴다」로 끝난다.
  **`b | a`** 를 던져야 **자리는 왼쪽, 값은 오른쪽**이라는 두 방향이 드러난다.
- **6번** — `Both` 만 보면 「`__eq__`+`__hash__` 면 된다」로 끝난다.
  **`Liar`**(해시가 늘 0)를 던져야 **계약이 한 방향뿐**이라는 것이 드러난다.
- **1번** — 한 판만 보면 「순서가 유지된다」가 실행에서 나온 결론처럼 보인다.
  **시드를 0·1·2 로 바꿔** 던져 「해시와 무관하다」를 따로 확인했다([13번](../13-set-and-frozenset/3-answer.md)의 `set` 과 대조군이다).
- **10번** — `hash(nan)` 은 `PYTHONHASHSEED=0` 으로 **고정해도** 판마다 달랐다. 2판을 던져 확인했다.

**「에러가 안 난 것」이 근거인 자리**

- 4번 (나) — **예외도 경고도 없이** 세 줄이 찍힌 것이 「검사가 크기만 본다」의 증거다.
- 2번 — `{1: ..., True: ...}` 가 **예외 없이** 하나로 합쳐진 것이 「같은 칸」의 증거다.
- 9번 — `len(d)` 가 **1을 그대로 돌려준 것**이 「언어가 감시하지 않는다」의 증거다.
- 6번 `Liar` — **예외 없이** 만들어진 것이 「계약은 한 방향」의 증거다.

**구현 의존 항목 — 버전이 오르면 다시 찍을 것**

| 다시 찍을 것 | 왜 |
|---|---|
| 5번의 `dis` 명령 이름 | **3.11.15 에서 이미 달랐다**(`RETURN_CONST` ↔ `LOAD_CONST`+`RETURN_VALUE`) |
| 10번의 `getsizeof` 값 전부 | 빌드·비트 폭·재해시 시점에 달렸다 |
| 10번의 `hash(nan)` | 3.10 부터 정체 기반이라 **실행마다** 다르다 |
| 4번 (나)의 「안 터진다」 | **구현이 크기만 보기 때문**이다. 검사가 강해지면 터질 수 있다 |
| 예외 **문구** 전부 | 예외 종류는 명세지만 문구는 아니다 |

나머지(삽입 순서 보장, 덮어쓰기와 재삽입의 차이, `1`·`1.0`·`True` 가 한 칸, `__eq__` 만 정의하면 `__hash__` 가 `None`,
뷰의 동적 성질, 병합의 승자 규칙, `|` 와 `|=` 가 받는 것의 차이)는 **언어 보장**이므로 어떤 구현에서도 같아야 한다.
