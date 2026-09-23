# python/syntax/14-comprehensions — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만.
> - [6.2.4. Displays for lists, sets and dictionaries](https://docs.python.org/3.12/reference/expressions.html#displays-for-lists-sets-and-dictionaries) — 감춰진 스코프, 가장 왼쪽 `for` 의 iterable
> - [6.2.8. Generator expressions](https://docs.python.org/3.12/reference/expressions.html#generator-expressions) — 지연 평가와 즉시 평가되는 부분
> - [PEP 572 — Assignment Expressions](https://peps.python.org/pep-0572/) — 왈러스가 바깥 스코프에 바인딩된다
> - [PEP 709 — Inlined comprehensions](https://peps.python.org/pep-0709/) — 3.12 의 인라인화
>
> **실행 검증** — 이 문서에 실린 출력은 전부 `python3` **3.12.3**(Linux)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> **버전** — 리스트 컴프리헨션은 2.0+, dict/set 컴프리헨션은 2.7/3.0+, 왈러스(`:=`)는 3.8+.\
>   **3.12 에서 list·dict·set 컴프리헨션이 인라인화됐다**(PEP 709) — 스택 트레이스에서 `<listcomp>` 프레임이 사라진다. 제너레이터 표현식은 인라인 대상이 아니다.
> **구현 대 명세** — 스코프 규칙과 평가 시점은 **언어 보장**이다. PEP 709 의 속도 향상과 프레임 소멸은 **CPython 3.12 의 구현 변화**다.
>
> **기존 노트와의 경계** — [`cs/foundations/python-basics/`](../../../../python-basics/README.md) 「1. 리스트」가 `[e for e in range(1, 101)]` 와 `if` 를 붙이는 **쓰는 법**을 이미 다룬다.\
>   이 주제는 그 위에서 「**무엇을 못 하고 어디서 틀리나**」만 간다 — 평가 시점, 스코프, 예외가 터지는 자리.

## 한눈에 — 쉽게 말하면

**주문한 음식을 한꺼번에 받느냐, 나올 때마다 받느냐.**

- `[...]` **리스트 컴프리헨션** — 주방이 **전부 다 만들 때까지 기다렸다가** 쟁반째 받는다.\
  다 받았으니 몇 개인지 셀 수 있고, 다시 볼 수 있고, 아무 접시나 집을 수 있다.\
  대신 **다 만들어질 때까지 못 먹고**, 쟁반을 놓을 자리(메모리)가 필요하다.
- `(...)` **제너레이터 표현식** — 주방에 **주문표만 걸어 둔다.** 달라고 할 때마다 한 접시씩 나온다.\
  첫 접시를 바로 먹을 수 있고 자리도 안 든다.\
  대신 **몇 개인지 모르고**, 지나간 접시는 다시 못 보고, 안 달라고 하면 **한 접시도 안 만들어진다.**

```text
[mark(n) for n in (1,2,3)]            (mark(n) for n in (1,2,3))
 만드는 줄에서 세 번 다 계산           만드는 줄에서는 아무것도 계산 안 함
        |                                     |
    +---+---+---+                         주문표 하나
    | 1 | 4 | 9 |                             |
    +---+---+---+                     next() 할 때마다 한 개씩 계산
    리스트 객체가 손에 있다
```

**괄호 하나 차이**가 이 전부를 가른다.\
실무에서 이 선택이 갈리는 자리는 늘 같다 — **1억 줄짜리 파일·API 페이지·DB 커서**를 다룰 때.

> **컴프리헨션(comprehension)** — `for` 루프로 컨테이너를 만드는 일을 식 하나로 쓰는 문법.\
> 예: `out = []` + `for` + `append` 세 줄을 `out = [f(x) for x in xs]` 한 줄로 쓴다.

> **평가 시점(evaluation time)** — 어떤 식이 실제로 계산되는 시점.\
> 예: 리스트 컴프리헨션은 **그 줄에서** 전부, 제너레이터 표현식은 **꺼낼 때** 하나씩 계산한다.

## 이 주제가 답하려는 질문

1. **언제 계산되나** — 대괄호와 소괄호가 갈라 놓는 것은 「무엇을 만드나」가 아니라 「**언제 만드나**」다.
2. **이름이 어디까지 보이나** — 타깃은 안 새는데 왈러스는 새고, 클래스 몸통에서는 `NameError` 가 나는 이유.
3. **예외와 부작용이 어느 줄에서 일어나나** — `try` 를 만드는 줄에 둬야 하나 꺼내는 줄에 둬야 하나.

## 동작 방식

### 1. ★ 괄호 하나가 계산 시점을 바꾼다

**언제 쓰나** — 이 주제의 핵심. 두 형태의 차이를 정확히 볼 때.

계산이 언제 일어나는지 보려고, 계산할 때마다 찍는 함수 하나를 썼다.

```python
def mark(n):
    print("   계산:", n)
    return n * n

print("리스트 만들기 시작")
squares = [mark(n) for n in (1, 2, 3)]
print("리스트 완성:", squares)

print("제너레이터 만들기 시작")
lazy = (mark(n) for n in (1, 2, 3))
print("제너레이터 완성:", lazy)
print("첫 개 꺼냄:", next(lazy))
print("둘째 꺼냄:", next(lazy))
print("나머지:", list(lazy))
```

```text
리스트 만들기 시작
   계산: 1
   계산: 2
   계산: 3
리스트 완성: [1, 4, 9]
제너레이터 만들기 시작
제너레이터 완성: <generator object <genexpr> at 0x7720fb2579f0>
   계산: 1
첫 개 꺼냄: 1
   계산: 2
둘째 꺼냄: 4
   계산: 3
나머지: [9]
```

이 출력을 시간 축으로 펴면 이렇다.

```text
리스트 컴프리헨션                       제너레이터 표현식
 ── 시간 ──────────────>                ── 시간 ──────────────>

 [만드는 줄]                            [만드는 줄]
   계산:1 계산:2 계산:3                   (아무것도 안 함)
   -> [1,4,9] 완성                       -> 주문표만 생김

 [쓰는 줄]                              [next() 첫 번째]
   이미 다 있다                            계산:1  -> 1
                                        [next() 두 번째]
                                          계산:2  -> 4
                                        [list() 로 나머지]
                                          계산:3  -> [9]
```

그림 해설 — 출력의 어느 줄이 그림의 어디인지.

- 리스트 쪽은 `리스트 만들기 시작` 과 `리스트 완성` **사이에** 계산 세 줄이 전부 들어갔다.
- 제너레이터 쪽은 `제너레이터 완성` 까지 **계산이 한 줄도 없다.**
- `계산: 1` 이 `첫 개 꺼냄:` **보다 먼저** 찍혔다 → 값을 돌려주기 직전에야 계산한다.
- `나머지: [9]` — 이미 두 개를 꺼냈으므로 남은 것은 하나뿐이다. **되감기가 없다.**

**비용** — 리스트는 전부를 메모리에 올린다. 제너레이터는 안 올린다.

```python
import sys
big_list = [n for n in range(100000)]
big_gen = (n for n in range(100000))
print("list  getsizeof:", sys.getsizeof(big_list))
print("genexp getsizeof:", sys.getsizeof(big_gen))
```

```text
list  getsizeof: 800984
genexp getsizeof: 192
```

- 10만 개 리스트는 약 **800 KB**, 제너레이터는 **192 바이트**다.
- 제너레이터 쪽이 원소 수와 **무관하다**는 것이 요점이다 — 값을 들고 있지 않고 "만드는 방법"만 들고 있으니까.
- 단 `getsizeof` 는 **그 객체 자체의 크기**만 잰다. 리스트 안에 든 정수 객체들의 크기는 안 들어 있다. 실제 차이는 더 크다.

### 2. 네 가지 형태 — 괄호와 콜론으로 갈린다

**언제 쓰나** — 무엇을 만들지 정할 때.

```text
[ 식 for x in it ]           -> list
{ 키: 값 for x in it }        -> dict     (콜론이 있으면 dict)
{ 식 for x in it }           -> set      (콜론이 없으면 set)
( 식 for x in it )           -> generator  (컴프리헨션이 아니라 "표현식")
```

```python
print([n * 2 for n in range(5)])
print({n: n * 2 for n in range(5)})
print({n % 3 for n in range(5)})
print(type((n * 2 for n in range(5))))
```

```text
[0, 2, 4, 6, 8]
{0: 0, 1: 2, 2: 4, 3: 6, 4: 8}
{0, 1, 2}
<class 'generator'>
```

그림 해설.

- **빈 `{}` 는 set 이 아니라 dict** 다. 빈 set 은 `set()` 뿐이다(기존 노트 「4. 집합」).
- set 컴프리헨션은 **중복을 지운다** — `range(5)` 의 `n % 3` 은 0,1,2,0,1 인데 결과가 `{0, 1, 2}` 다.
- dict 컴프리헨션은 **같은 키가 나오면 뒤엣것이 이긴다.**

```python
pairs = [("a", 1), ("b", 2), ("a", 3)]
print({k: v for k, v in pairs})
```

```text
{'a': 3, 'b': 2}
```

- `'a'` 가 **3** 이다. 조용히 덮어썼다. 개수가 줄어든 것을 아무도 안 알려 준다.
- 위치는 **처음 넣은 자리**를 유지한다(`'a'` 가 앞에 있다) — dict 의 삽입 순서 보장은 3.7+ 언어 보증이다(목록의 12번 주제).

**비용** — 중복 제거가 공짜로 따라온다.\
대신 **잃어버린 데이터가 조용히 사라진다.** 중복이 의미 있으면 `collections.defaultdict(list)` 로 모아야 한다.

### 3. 조건이 들어가는 자리는 둘이고 뜻이 다르다

**언제 쓰나** — "거르기"와 "바꾸기"를 구분할 때. 가장 흔한 혼동이다.

```text
[ n      for n in range(6) if n % 2 == 0 ]     for 뒤 -> 거른다 (개수가 준다)
  ^                          ^^^^^^^^^^^^^
[ n if n % 2 == 0 else "홀"  for n in range(6) ]  식 자리 -> 바꾼다 (개수 그대로)
  ^^^^^^^^^^^^^^^^^^^^^^^^
```

```python
print([n for n in range(6) if n % 2 == 0])
print([n if n % 2 == 0 else "홀" for n in range(6)])
```

```text
[0, 2, 4]
[0, '홀', 2, '홀', 4, '홀']
```

그림 해설.

- 위: 원소 6개 → **3개**. `for` 뒤의 `if` 는 **필터**다. `else` 를 쓸 수 없다.
- 아래: 원소 6개 → **6개**. 앞자리의 것은 조건 **표현식**이라 `else` 가 필수다.
- 둘 다 쓸 수도 있다 — `[a if c else b for x in xs if d]`. 읽기 어려워지는 지점이다.

**비용** — 필터는 뒤 단계의 일을 줄인다.\
대신 **개수가 달라지므로** 입력과 출력을 짝지어 쓰던 코드가 어긋난다.

### 4. 중첩은 `for` 문을 쓴 순서 그대로다

**언제 쓰나** — 중첩 컴프리헨션의 순서가 헷갈릴 때.

```text
[(a, b) for a in "xy" for b in (1, 2)]

   풀어 쓰면 — 쓴 순서 그대로 위에서 아래로 중첩한다
   for a in "xy":
       for b in (1, 2):
           결과에 (a, b) 추가
```

```python
print([(a, b) for a in "xy" for b in (1, 2)])
rows = [[1, 2], [3, 4]]
print([v for row in rows for v in row])
print([[v * 10 for v in row] for row in rows])
```

```text
[('x', 1), ('x', 2), ('y', 1), ('y', 2)]
[1, 2, 3, 4]
[[10, 20], [30, 40]]
```

그림 해설.

- 첫 줄: 왼쪽 `for` 가 **바깥 루프**다. `a='x'` 가 고정된 채 `b` 가 1,2 를 돈다.
- 둘째 줄: **평탄화**. `for row in rows` 가 먼저, `for v in row` 가 그 안이다.
- 셋째 줄: **안쪽 컴프리헨션**은 대괄호가 한 겹 더 있다. 결과가 중첩 리스트로 남는다.
- 둘째와 셋째의 차이가 "평탄화냐 유지냐"다. **대괄호의 위치가 결정한다.**

**비용** — 두 겹까지는 읽힌다.\
세 겹이 되거나 `if` 가 여럿 섞이면 **`for` 문으로 되돌리는 편이 낫다.** 컴프리헨션은 짧게 쓰려는 문법이 아니라 **「목록을 만든다」는 의도를 드러내는** 문법이다.

### 5. 루프 변수가 바깥으로 안 샌다

**언제 쓰나** — `for` 문과 컴프리헨션의 차이를 물을 때.

```text
for 문                              컴프리헨션
 바깥 스코프에서 돈다                 감춰진 스코프 안에서 돈다
 +--------------------+             +---------------------------+
 | for i in range(3): |             | [ j for j in range(3) ]   |
 |     ...            |             |   j 는 이 안에서만 산다     |
 | i 가 남는다 -> 2    |             +---------------------------+
 +--------------------+              바깥에서 j 를 부르면 NameError
```

```python
for i in range(3):
    pass
print("for 뒤의 i =", i)

sq = [j for j in range(3)]
print(j)
```

```text
for 뒤의 i = 2
NameError: name 'j' is not defined
```

바깥에 같은 이름이 있어도 **덮어쓰지 않는다.**

```python
i = "원래 값"
_ = [i for i in range(3)]
print("컴프리헨션 뒤의 i =", repr(i))
```

```text
컴프리헨션 뒤의 i = '원래 값'
```

그림 해설.

- 문서가 규정한다 — "**가장 왼쪽 `for` 절의 iterable 식을 빼면**, 컴프리헨션은 별도의 감춰진 중첩 스코프에서 실행된다. 이것은 타깃 목록에 대입된 이름이 바깥 스코프로 **새지 않게** 보장한다."
- 그래서 `i`, `j`, `x` 같은 흔한 이름을 마음 놓고 쓸 수 있다.
- **3.12 의 인라인화(PEP 709) 이후에도 이 성질은 그대로다.** 속도를 위해 별도 프레임을 없앴지만 **이름 격리는 유지한다.**

**비용** — 이름 오염이 없다.\
대신 **컴프리헨션 안에서 만든 값을 바깥으로 꺼내려면** 결과를 받는 것 말고는 길이 없다 — 하나만 빼고(다음 절).

### 6. 왈러스(`:=`)는 샌다

**언제 쓰나** — 컴프리헨션 안에서 계산한 중간값을 바깥에서 쓸 때. 그리고 그것이 사고가 될 때.

```text
[ (y := n * 2) for n in range(3) ]

  n  -> 감춰진 스코프 (안 샌다)
  y  -> 바깥 스코프  (샌다!)  ... 마지막 값 하나만 남는다
```

```python
total = [(y := n * 2) for n in range(3)]
print(total, "| y =", y)
```

```text
[0, 2, 4] | y = 4
```

그림 해설.

- `n` 은 안 새는데 `y` 는 **샌다.** 같은 대괄호 안인데 두 이름의 운명이 다르다.
- PEP 572 가 그렇게 정했다 — 왈러스의 타깃은 **컴프리헨션을 감싸고 있는 스코프**에 바인딩된다.
- 남는 것은 **마지막 값 하나**다. `y = 4`.
- 쓸모는 있다 — `[y for n in xs if (y := f(n)) > 0]` 처럼 **필터와 결과에서 같은 계산을 두 번 안 하게** 할 수 있다.
- 위험도 있다 — 바깥의 같은 이름을 **조용히 덮어쓴다.**

**비용** — 계산 한 번을 아낀다.\
대신 **이름 격리라는 컴프리헨션의 약속에 구멍**을 낸다. 이름을 흔한 것(`x`·`i`)으로 두면 사고가 난다.

### 7. 예외가 터지는 시점도 갈린다

**언제 쓰나** — `try`/`except` 를 어디에 둘지 정할 때.

```text
리스트 컴프리헨션                      제너레이터 표현식
 만드는 그 줄에서 터진다                만들 때는 조용하다
 try 를 만드는 줄에 두면 잡힌다          try 를 꺼내는 줄에 둬야 잡힌다

 [10 // n for n in [1,0,2]]           (10 // n for n in [1,0,2])
    ↓ 그 줄에서 ZeroDivisionError        ↓ 아무 일 없음
                                       next()  -> 10
                                       next()  -> ZeroDivisionError
```

```python
data = [1, 0, 2]
try:
    bad = [10 // n for n in data]
except ZeroDivisionError as e:
    print("리스트: 만드는 중에 터짐 —", e)

lazy = (10 // n for n in data)
print("제너레이터: 만들 때는 조용함 —", lazy)
print("첫 값:", next(lazy))
try:
    next(lazy)
except ZeroDivisionError as e:
    print("꺼낼 때 터짐 —", e)
```

```text
리스트: 만드는 중에 터짐 — integer division or modulo by zero
제너레이터: 만들 때는 조용함 — <generator object <genexpr> at 0x714e6e5af9f0>
첫 값: 10
꺼낼 때 터짐 — integer division or modulo by zero
```

그림 해설.

- 같은 식인데 **예외가 나는 줄이 다르다.**
- 제너레이터를 만든 함수가 `try` 를 감싸고 있어도, 예외는 **소비하는 쪽**에서 난다.\
  그래서 `with open(...) as f: return (line for line in f)` 가 위험하다 — 꺼낼 때쯤 파일이 닫혀 있다.
- 단 **가장 왼쪽 `for` 의 iterable 은 즉시 평가된다.** 거기서 나는 에러는 만드는 줄에서 난다.\
  문서 표현 — "가장 왼쪽 `for` 절의 iterable 식은 즉시 평가되므로, 그것이 내는 에러는 **제너레이터 표현식이 정의된 자리**에서 나온다."

**비용** — 지연 덕에 필요 없는 계산을 안 한다.\
대신 **예외와 부작용의 위치가 코드 순서와 어긋난다.**

## 문법 — 형태와 규칙

```python
[식 for 타깃 in iterable]                       # 기본
[식 for 타깃 in iterable if 조건]                # 필터
[식1 if 조건 else 식2 for 타깃 in iterable]       # 값 바꾸기 (else 필수)
[식 for a in A for b in B]                      # 중첩 (쓴 순서 = 루프 순서)
{k: v for k, v in pairs}                        # dict
{식 for x in it}                                # set
(식 for x in it)                                # 제너레이터 표현식
f(식 for x in it)                               # 인자가 하나뿐이면 괄호 생략 가능
```

규칙 다섯.

1. **가장 왼쪽 `for` 의 iterable 만 바깥 스코프에서, 즉시 평가된다.** 나머지는 감춰진 스코프에서 평가된다.
2. **타깃 이름은 바깥으로 안 샌다.** 단 **왈러스 타깃은 샌다.**
3. **`for` 뒤의 `if` 는 필터**(else 불가), **식 자리의 `if`/`else` 는 조건 표현식**(else 필수).
4. **콜론이 있으면 dict, 없으면 set.** 빈 `{}` 는 dict.
5. **소괄호는 제너레이터 표현식이다.** 컴프리헨션이 아니고, 결과가 리스트가 아니다.

## 어디서 틀리나

### (1) 클래스 몸통 안에서 클래스 변수가 안 보인다

```python
class Table:
    factor = 10
    rows = [1, 2, 3]
    scaled = [r * factor for r in rows]
```

```text
NameError: name 'factor' is not defined
```

- `rows` 는 보이는데 `factor` 는 안 보인다. **`rows` 가 가장 왼쪽 `for` 의 iterable 이라 바깥 스코프(= 클래스 몸통)에서 평가되기 때문이다.**
- `factor` 는 감춰진 스코프 안에서 찾아야 하는데, **클래스 몸통은 중첩 스코프의 이름 탐색 경로에 들어가지 않는다.**
- 고치는 법: 값을 직접 쓰거나(`r * 10`), 클래스 밖에서 만들어 대입하거나, **가장 왼쪽 `for` 의 iterable 에 실어 보낸다** —\
  `[r * f for r, f in zip(rows, [factor] * len(rows))]` 는 `[10, 20, 30]` 을 낸다(실행 확인). 그 자리만 클래스 몸통에서 평가되기 때문이다.
- ✗ **기본 인자로 밀어 넣는 우회는 안 된다** — `[(lambda r, f=factor: r * f)(r) for r in rows]` 도 같은 `NameError` 다(실행 확인).\
  `lambda` 의 기본값 식 역시 **감춰진 스코프 안에서** 평가되기 때문이다.

```python
class TableOK:
    factor = 10
    rows = [1, 2, 3]
    scaled = [r * 10 for r in rows]
print(TableOK.scaled)     # [10, 20, 30]
```

### (2) 제너레이터를 한 번 더 쓰려다 빈 결과를 얻는다

```python
g = (n for n in range(5))
print(3 in g)
print(3 in g)
print(list(g))
```

```text
True
False
[]
```

- 첫 `3 in g` 가 0,1,2,3 을 **먹어 치웠다.** 찾자마자 멈추므로 4는 남았다.
- 둘째 `3 in g` 는 남은 4만 보고 `False`.
- `list(g)` 는 **빈 리스트**. 예외가 아니다.
- **리스트라면 세 줄 다 같은 답**이 나온다. 제너레이터로 바꾼 것만으로 결과가 바뀐다.

### (3) 부작용을 제너레이터 표현식으로 짜면 안 돈다

```python
rows = (save(x) for x in items)     # 아무도 소비 안 하면 save 가 한 번도 안 불린다
```

**값을 만드는 데**가 아니라 **일을 시키는 데** 컴프리헨션을 쓰면 안 된다.\
그리고 리스트 컴프리헨션을 부작용 목적으로 쓰는 것(`[save(x) for x in items]`)도 나쁘다 — 쓰지도 않을 리스트를 만든다. 그때는 `for` 문을 쓴다.

### (4) 필터와 변환을 헷갈린다

```python
[n if n > 2 for n in range(5)]
```

```text
SyntaxError: expected 'else' after 'if' expression
```

앞자리의 `if` 는 조건 표현식이라 `else` 가 필수다.\
거르고 싶었다면 `[n for n in range(5) if n > 2]` 다.

### (5) dict 컴프리헨션이 데이터를 조용히 줄인다

```python
{k: v for k, v in pairs}
```

키가 겹치면 뒤엣것만 남는다. **개수가 줄어도 경고가 없다.**\
중복이 의미 있으면 `defaultdict(list)` 로 모은다(목록의 43번 주제).

### (6) 3.12 부터 스택 트레이스 모양이 달라졌다 (PEP 709)

같은 `ZeroDivisionError` 인데 두 형태의 트레이스백이 다르다.

```python
def build(data):
    return [10 // n for n in data]
build([1, 0])
```

```text
Traceback (most recent call last):
  File ".../t14_tb.py", line 3, in <module>
    build([1, 0])
  File ".../t14_tb.py", line 2, in build
    return [10 // n for n in data]
            ~~~^^~~
ZeroDivisionError: integer division or modulo by zero
```

```python
def build(data):
    return list(10 // n for n in data)
build([1, 0])
```

```text
Traceback (most recent call last):
  File ".../t14_tb2.py", line 3, in <module>
    build([1, 0])
  File ".../t14_tb2.py", line 2, in build
    return list(10 // n for n in data)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File ".../t14_tb2.py", line 2, in <genexpr>
    return list(10 // n for n in data)
                ~~~^^~~
ZeroDivisionError: integer division or modulo by zero
```

- 리스트 컴프리헨션에는 **프레임 줄이 없다.**\
  PEP 709 가 "컴프리헨션은 더 이상 스택 트레이스에서 자기 전용 프레임을 갖지 않는다"고 밝힌 변화다 — 3.11 이하 실행본이 이 머신에 없어 **이전 모양은 직접 확인하지 못했다**(PEP 근거).
- 제너레이터 표현식에는 **`in <genexpr>` 줄이 그대로 있다.** PEP 709 의 인라인 대상이 아니기 때문이다.
- 그래서 **3.11 이전 기준으로 외운 트레이스백 모양이 3.12 에서 안 맞는다.**
- PEP 709 가 밝힌 다른 관측 가능한 변화 — 컴프리헨션 안에서 `locals()` 를 부르면 **바깥 함수의 지역 변수까지** 보이고, `sys.settrace` 로 보던 호출/반환 이벤트가 사라진다.

> **인라인화(inlining)** — 별도의 함수 호출로 처리하던 것을 부르는 쪽 코드에 그대로 펴 넣는 최적화.\
> 예: 컴프리헨션마다 만들던 프레임을 없애서 호출 비용을 지웠다. PEP 709 가 밝힌 수치는 마이크로벤치마크 **1.96배**, 실제 코드 기반 벤치마크 **11%** 향상이다.

## 구현 세부사항 대 언어 보장

세 층으로 가른다. ★ **이 주제는 「스코프와 평가 시점」이 전부 명세에 있고, 「얼마나 빠른가·스택에 무엇이 남나」가 전부 구현이다.**

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **언어 보장** | 언어·라이브러리 레퍼런스와 PEP 가 정한 것 | 공식 문서 문장을 열어서 인용 |
| **CPython 구현** | 이 구현이 그렇게 하는 것 | 실행 + 트레이스백·`locals()` 로 확인 |
| **이 판의 관찰** | 3.12.3·이 머신에서 그랬을 뿐 | 「관찰」로 명기 |

### 언어 보장

| 사실 | 근거 |
|---|---|
| 가장 왼쪽 `for` 의 iterable 식을 빼면, 컴프리헨션은 **별도의 감춰진 중첩 스코프**에서 실행된다 | 언어 레퍼런스 6.2.4 — *"aside from the iterable expression in the leftmost for clause, the comprehension is executed in a separate implicitly nested scope"* |
| 가장 왼쪽 `for` 의 iterable 은 **바깥 스코프에서 직접 평가되어** 그 스코프에 인자로 넘어간다 | 6.2.4 — *"is evaluated directly in the enclosing scope and then passed as an argument to the implicitly nested scope"* |
| 제너레이터 표현식 안의 변수는 `__next__()` 가 불릴 때 **지연 평가**된다 | 6.2.8 — *"Variables used in the generator expression are evaluated lazily when the `__next__()` method is called"* |
| 그러나 가장 왼쪽 `for` 의 iterable 은 **즉시 평가**되므로, 거기서 난 에러는 **정의된 자리**에서 나온다 | 6.2.8 — *"immediately evaluated, so that an error produced by it will be emitted at the point where the generator expression is defined"* |
| 컴프리헨션 안의 대입식(`:=`)은 **감싸는 스코프**에 타깃을 바인딩한다 | PEP 572 — *"binds the target in the containing scope, honoring a nonlocal or global declaration for the target in that scope, if one exists"* |
| 왈러스 타깃 이름은 같은 컴프리헨션의 `for` 타깃 이름과 **같을 수 없다** | PEP 572 — for 타깃은 *"local to the comprehension in which they appear"* |
| dict 의 **삽입 순서 보존은 언어 명세의 일부**다(3.7+) | What's New in 3.7 — *"the insertion-order preservation nature of dict objects has been declared to be an official part of the Python language spec"* |
| `sys.getsizeof` 는 **그 객체에 직접 귀속된 메모리만** 센다 | `sys.getsizeof` — *"Only the memory consumption directly attributed to the object is accounted for, not the memory consumption of objects it refers to"* |

★ 그래서 「타깃은 안 새고 왈러스는 샌다」·「클래스 몸통에서 `NameError` 가 난다」는 **구현 얘기가 아니라 명세의 귀결**이다.

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| 3.12 가 **list·dict·set 컴프리헨션을 인라인**한다. 제너레이터 표현식은 대상이 **아니다** | PEP 709 — *"Generator expressions are currently not inlined in the reference implementation of this PEP."* |
| 그래서 컴프리헨션이 **스택 트레이스에서 자기 프레임을 갖지 않는다** | PEP 709 — *"a comprehension will no longer have its own dedicated frame in a stack trace"* + 실행한 트레이스백에 `in <listcomp>` 줄이 없고, 제너레이터 쪽에는 `in <genexpr>` 줄이 남아 있다(위 「(6)」) |
| 컴프리헨션 안에서 `locals()` 를 부르면 **바깥 함수의 지역 변수까지** 보인다 | 실행 확인 — 아래 |
| `sys.settrace`·`setprofile` 이 보던 호출·반환 이벤트가 사라진다 | PEP 709 가 밝힌 변화다. **이 문서에서는 직접 재지 않았다** |
| 컴프리헨션이 `for`+`append` 보다 빠른 것 | 바이트코드가 `append` 를 매번 찾아 부르지 않기 때문이다. **속도는 전부 구현 소관**이다 |

```python
def f():
    lst = [1, 2]
    other = "바깥 지역변수"
    return [sorted(locals().keys()) for x in lst][0]

print(f())
```

```text
['lst', 'other', 'x']
```

- 바깥 함수의 `lst`·`other` 가 **컴프리헨션 안의 `locals()` 에 같이 보인다.** 3.11 이하에서는 안 보이던 것이다.
- **이름 격리는 그대로다** — 보이는 것과 새는 것은 다른 얘기다. 바깥에서 `x` 를 부르면 여전히 `NameError` 다.

### 이 판(3.12.3)·이 머신의 관찰

| 관찰 | 어디가 흔들리나 |
|---|---|
| `getsizeof` 가 10만 원소 리스트에 `800984`, 1000만에 `89095160`, 제너레이터는 둘 다 `192` | 리스트의 성장 전략과 객체 내부 표현에 달렸다. **비례한다/안 한다**가 요점이고 숫자 자체는 아니다 |
| `timeit` 네 줄의 usec 값 | **머신·부하에 달렸다.** 같은 머신에서 다시 돌리니 리스트 컴프리헨션이 16.9 → 18.5 → 19.7 → 22.2 usec 로 흔들렸다. 볼 것은 **순서**지 값이 아니다 |
| `{0, 1, 2}` 가 오름차순으로 보인다 | **정렬 보장이 아니다.** 5판을 돌려도 정수 집합은 같았지만, **문자열 집합은 5판이 전부 달랐다**(`PYTHONHASHSEED` 무작위화). 정수 쪽이 안 변해서 더 위험하다 |
| `<generator object <genexpr> at 0x...>` 의 주소 숫자 | 실행할 때마다 다르다 |
| `SyntaxError: expected 'else' after 'if' expression` 문구 | 예외 **종류**는 명세지만 **문구**는 아니다 |
| 트레이스백의 `~~~^^~~` 캐럿 표시 | 3.11 이 넣은 세밀한 위치 표시다. 모양은 판마다 바뀐다 |

### 그래서 이렇게 적으면 틀린다

- ✗ 「3.12 에서 컴프리헨션이 빨라졌으니 제너레이터 표현식도 빨라졌다」\
  → PEP 709 는 **제너레이터 표현식을 인라인하지 않는다.** 트레이스백에 `in <genexpr>` 줄이 남아 있는 것이 그 확인이다.
- ✗ 「인라인화됐으니 이름도 새게 됐다」\
  → **이름 격리는 유지된다.** 바깥에서 타깃을 부르면 여전히 `NameError` 다.
- ✗ 「set 은 `{0, 1, 2}` 처럼 정렬돼 나온다」\
  → **정수라서 그렇게 보일 뿐이다.** 문자열 집합은 실행마다 순서가 달랐다.
- ✗ 「`getsizeof` 로 메모리 차이를 다 쟀다」\
  → 문서가 *"not the memory consumption of objects it refers to"* 라고 적는다. 안에 든 정수 객체는 안 세어졌다.
- ✗ 「클래스 몸통 문제는 `lambda` 기본 인자로 우회된다」\
  → **안 된다.** `lambda` 의 기본값 식도 감춰진 스코프에서 평가된다(실행 확인, 위 「(1)」).
- ✗ 「컴프리헨션이 `for` 문보다 빠른 것은 언어의 성질이다」\
  → **이 구현의 바이트코드 얘기다.** 명세는 속도를 말하지 않는다.

**판정 기준 한 줄**: **「언제·어느 스코프에서 평가되나」는 명세에 있고, 「얼마나 빠른가·스택에 무엇이 남나·몇 바이트인가」는 이 구현에 있다.**

## 언제 쓰고 언제 안 쓰나

측정은 이 머신에서 `timeit` 으로 직접 돌렸다(원소 1000개).

```text
$ python3 -m timeit -s "data=list(range(1000))" "[n*2 for n in data]"
20000 loops, best of 5: 16.9 usec per loop

$ python3 -m timeit -s "data=list(range(1000))" "out=[]
for n in data: out.append(n*2)"
10000 loops, best of 5: 23.1 usec per loop

$ python3 -m timeit -s "data=list(range(1000))" "list(map(lambda n: n*2, data))"
5000 loops, best of 5: 38.3 usec per loop

$ python3 -m timeit -s "data=list(range(1000))" "(n*2 for n in data)"
2000000 loops, best of 5: 113 nsec per loop
```

- 컴프리헨션이 `for`+`append` 보다 빠르다 — `append` 를 매번 **찾아서 호출**하는 비용이 없기 때문이다.
- `map` + `lambda` 는 더 느리다 — 원소마다 파이썬 함수 호출이 하나씩 더 붙는다.
- 마지막 줄의 **113 나노초**는 "빠르다"가 아니라 "**아무 일도 안 했다**"는 뜻이다. 제너레이터 객체만 만들었다.

| 상황 | 고를 것 |
|---|---|
| 결과를 여러 번 쓴다 · `len` · 인덱싱 · 정렬 | **리스트 컴프리헨션** |
| 원소가 적고(수천 이하) 바로 다 쓴다 | **리스트 컴프리헨션** — 단순한 쪽이 낫다 |
| 원소가 아주 많거나 무한하다 | **제너레이터 표현식** |
| `sum`·`any`·`all`·`max` 에 바로 넣는다 | **제너레이터 표현식** — 중간 리스트가 필요 없다 |
| 앞쪽 몇 개만 볼 수도 있다 | **제너레이터 표현식** — 나머지는 계산조차 안 한다 |
| 파일·DB 커서처럼 흘려보낸다 | **제너레이터 표현식** |
| 부작용이 목적이다(저장·전송·출력) | **둘 다 아니다 — `for` 문** |
| 세 겹 이상 중첩 · `if` 가 여럿 | **`for` 문** — 읽히는 쪽이 이긴다 |

## 핵심 문장

- 대괄호와 소괄호의 차이는 모양이 아니라 **언제 계산하느냐**다. 리스트는 그 줄에서 전부, 제너레이터는 꺼낼 때 하나씩.
- 그 차이가 **메모리·예외가 나는 줄·부작용이 일어나는 시점·재사용 가능 여부**를 전부 바꾼다.
- 컴프리헨션은 **감춰진 스코프**에서 돈다. 타깃 이름은 안 새고, 가장 왼쪽 `for` 의 iterable 만 바깥에서 평가된다. 예외는 왈러스 타깃 하나다.
- 클래스 몸통 안의 컴프리헨션이 클래스 변수를 못 보는 것은 이 스코프 규칙의 직접적 귀결이다.
- 컴프리헨션은 **짧게 쓰는 문법이 아니라 「목록을 만든다」는 의도를 드러내는 문법**이다. 의도가 「일을 시킨다」면 `for` 문을 쓴다.

## 관련 자료

- 목록: [python/syntax 주제 목록](../README.md) — 이 주제는 **14번**
- 선행: 목록의 **09번** 「시퀀스 공통 연산과 슬라이싱」(폴더 아직 없음)
- 이어지는 곳: [17-generators-yield](../17-generators-yield/2-summary.md) — 제너레이터 표현식이 만드는 그 객체가 무엇인지, 어디서 멈추고 재개하는지
- 목록의 **15번** 「제너레이터 표현식과 지연 평가」, **16번** 「이터레이터 프로토콜」(폴더 아직 없음)
- 기존 노트: [`cs/foundations/python-basics/`](../../../../python-basics/README.md) 「1. 리스트」 — 컴프리헨션을 **쓰는 법**과 `if` 붙이기.\
  이 주제는 거기서 **평가 시점·스코프·예외 자리**로만 간다.
- 공식 문서: [6.2.4. Displays](https://docs.python.org/3.12/reference/expressions.html#displays-for-lists-sets-and-dictionaries) · [6.2.8. Generator expressions](https://docs.python.org/3.12/reference/expressions.html#generator-expressions) · [PEP 709](https://peps.python.org/pep-0709/)

## 용어 풀이

- **컴프리헨션(comprehension)**: `for` 로 컨테이너를 만드는 일을 식 하나로 쓰는 문법.\
  list·dict·set 세 가지가 있다.
- **제너레이터 표현식(generator expression)**: 소괄호로 쓴 형태.\
  컨테이너를 만들지 않고 **제너레이터 객체**를 만든다.
- **평가 시점(evaluation time)**: 식이 실제로 계산되는 시점.\
  리스트는 그 줄에서 전부, 제너레이터는 꺼낼 때 하나씩.
- **지연 평가(lazy evaluation)**: 미리 다 만들지 않고 요청받을 때 하나씩 만드는 방식.
- **물질화(materialize)**: 지연된 것을 `list()`·`tuple()` 로 전부 꺼내 실제 자료구조로 만드는 것.
- **감춰진 스코프(implicitly nested scope)**: 컴프리헨션이 도는 별도의 이름 공간.\
  안에서 대입한 이름이 바깥으로 안 새게 해 준다.
- **타깃(target)**: `for` 뒤에 오는 변수 이름.\
  `[x for x in xs]` 의 `x` 가 타깃이다.
- **필터(filter)**: `for` 뒤에 붙는 `if`.\
  개수를 줄인다. `else` 를 쓸 수 없다.
- **조건 표현식(conditional expression)**: `A if 조건 else B`.\
  값을 고르는 식이라 `else` 가 필수다.
- **왈러스 연산자(`:=`, assignment expression)**: 식 안에서 이름에 값을 묶는 연산자(3.8+).\
  컴프리헨션 안에서 쓰면 그 이름은 **바깥 스코프**에 남는다.
- **평탄화(flatten)**: 중첩된 리스트를 한 겹으로 펴는 것.\
  `[v for row in rows for v in row]`.
- **인라인화(inlining)**: 별도 호출로 처리하던 것을 부르는 쪽에 펴 넣는 최적화.\
  3.12 가 list·dict·set 컴프리헨션에 적용했다(PEP 709).
- **`sys.getsizeof`**: 객체 **자체**가 차지하는 바이트 수.\
  안에 든 객체들의 크기는 포함하지 않는다.
- **조용한 실패(silent failure)**: 에러 없이 정상처럼 끝나는데 결과만 틀린 것.\
  dict 컴프리헨션의 키 중복과 소진된 제너레이터가 이 갈래다.
