# python/syntax/09-sequence-ops-and-slicing — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만.
> - [Common Sequence Operations](https://docs.python.org/3.12/library/stdtypes.html#common-sequence-operations) — 공통 연산 표와 주
> - [Mutable Sequence Types](https://docs.python.org/3.12/library/stdtypes.html#mutable-sequence-types) — 슬라이스 대입·`del`
> - [Ranges](https://docs.python.org/3.12/library/stdtypes.html#ranges) — `range` 가 시퀀스인 것
> - [6.3.3. Subscriptions](https://docs.python.org/3.12/reference/expressions.html#subscriptions) · [6.3.4. Slicings](https://docs.python.org/3.12/reference/expressions.html#slicings) — 언어 레퍼런스
> - [`slice`](https://docs.python.org/3.12/library/functions.html#slice) — `slice` 객체와 `indices()`
>
> **실행 검증** — 이 문서에 실린 출력은 전부 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> **버전** — 공통 시퀀스 연산은 Python 3 전체 공통. 시간 측정값은 **이 머신의 관찰**이다.
> **선행** — [01-object-and-name-binding](../01-object-and-name-binding/2-summary.md)(대입은 이름을 묶는 것) ·
> [03-mutability-and-copying](../03-mutability-and-copying/2-summary.md)(얕은 복사 정본).

## 한눈에 — 쉽게 말하면

**인덱스는 「칸을 가리키고」 슬라이스는 「칸 사이의 금을 가리킨다」. 그래서 하나는 터지고 하나는 안 터진다.**

```text
        0   1   2   3   4          <- 인덱스: 칸을 가리킨다
      +---+---+---+---+---+
      |10 |20 |30 |40 |50 |
      +---+---+---+---+---+
      0   1   2   3   4   5        <- 슬라이스: 칸 사이의 금을 가리킨다
     -5  -4  -3  -2  -1

  s[5]   -> IndexError    (5번 칸이 없다)
  s[5:]  -> []            (5번 금은 맨 끝. 그 뒤는 아무것도 없을 뿐)
  s[99:] -> []            (금이 없으면 맨 끝으로 접어 준다)
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 칸을 가리키는 손가락 | 인덱싱 `s[i]` | 범위 밖이면 **`IndexError`** |
| 칸 사이의 금 | 슬라이싱 `s[i:j]` | 범위 밖이어도 **안 터진다** |
| 금을 적어 둔 쪽지 | `slice` 객체 | `s[1:4:2]` 와 `s[slice(1,4,2)]` 가 같다 |
| 쪽지를 길이에 맞춰 접기 | `slice.indices(len)` | 범위 밖이 여기서 접힌다 |
| 바구니를 새로 짜되 물건은 그대로 | 얕은 복사 `s[:]` | 안쪽은 **같은 객체** |
| 같은 물건을 세 번 가리키기 | `[[]] * 3` | 한 칸을 바꾸면 **셋 다** 바뀐다 |
| 계산으로 답하는 목록 | `range` | `in` 이 **거의 즉시** 끝난다 |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.\
「**빈 결과가 나왔는데 에러가 안 났다**」가 그것이다. 오프셋 계산이 틀려 `s[5:]` 가 `[]` 가 돼도
프로그램은 멀쩡히 돌고, 페이지가 빈 채로 응답된다. **인덱싱이었다면 그 자리에서 터졌을 것**이다.

> **시퀀스(sequence)** — 순서가 있고 정수 인덱스로 꺼낼 수 있는 것.\
> `list`·`tuple`·`str`·`bytes`·`bytearray`·`range` 가 그렇다. `set`·`dict` 는 아니다.

## 이 주제가 답하려는 질문

1. **왜 인덱싱은 터지고 슬라이싱은 안 터지는가** — 그리고 그것이 왜 위험한가.
2. **대괄호 안에 무엇이 들어가는가** — `s[1:4:2]` 가 실제로 무엇을 만들어 넘기는가.
3. **`+`·`*`·`[:]` 가 무엇을 새로 만들고 무엇을 공유하는가** — `[[]] * 3` 이 그 답이다.

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 문장으로 읽는다.

### 1. ★ 인덱싱은 터지고 슬라이싱은 안 터진다

**언제 쓰나** — 오프셋·페이지 번호를 계산해서 꺼낼 때마다.

문서가 슬라이스의 **접기 규칙**을 직접 정의한다 —\
*"The slice of s from i to j is defined as the sequence of items with index k such that `i <= k < j`. **If i or j is greater than `len(s)`, use `len(s)`.** If i is omitted or None, use 0. If j is omitted or None, use `len(s)`. **If i is greater than or equal to j, the slice is empty.**"*

```text
        0   1   2   3   4
      +---+---+---+---+---+
      |10 |20 |30 |40 |50 |     len = 5
      +---+---+---+---+---+
      0   1   2   3   4   5

  s[4]    -> 50            4번 칸이 있다
  s[5]    -> IndexError    5번 칸이 없다
  s[5:]   -> []            5번 금은 맨 끝. 거기서 끝까지 = 빈 것
  s[99:]  -> []            ★ 99 는 len(s)=5 로 접힌다
  s[-99:] -> 전체           ★ -99 는 0 으로 접힌다
  s[3:1]  -> []            시작이 끝보다 뒤 -> 빈 것
```

```python
s = [10, 20, 30, 40, 50]
print("s[4]    =", s[4])
for bad in (5, -6):
    try:
        s[bad]
    except IndexError as e:
        print(f"s[{bad}]   ->", type(e).__name__, e)
print("s[5:]   =", s[5:])
print("s[5:99] =", s[5:99])
print("s[99:]  =", s[99:])
print("s[-99:] =", s[-99:])
print("s[3:1]  =", s[3:1])
print("'abc'[9:] =", repr("abc"[9:]), "| (1,2)[9:] =", (1, 2)[9:], "| range(3)[9:] =", range(3)[9:])
```

```text
s[4]    = 50
s[5]   -> IndexError list index out of range
s[-6]   -> IndexError list index out of range
s[5:]   = []
s[5:99] = []
s[99:]  = []
s[-99:] = [10, 20, 30, 40, 50]
s[3:1]  = []
'abc'[9:] = '' | (1,2)[9:] = () | range(3)[9:] = range(3, 3)
```

그림 해설.

- **인덱싱은 「그 칸이 있느냐」를 묻는다.** 없으면 답할 것이 없으니 예외다.
- 슬라이싱은 「**이 구간과 겹치는 것을 달라**」다. 안 겹치면 **빈 것**이 정직한 답이다.
- ★ **`s[-99:]` 가 전체다.** 음수도 접힌다 — `len(s) + (-99)` 가 음수면 0 으로 친다.
- **어떤 시퀀스든 같다.** `str`·`tuple`·`range` 전부 빈 것을 돌려준다(타입은 자기 타입 그대로).

**★ 그래서 조용한 실패가 난다**

```python
def page(items, n, size=10):
    return items[n * size : (n + 1) * size]

data = list(range(25))
print("2페이지  :", page(data, 2))
print("9페이지  :", page(data, 9), "<- 빈 것. 에러는 안 난다")
print("-1페이지 :", page(data, -1), "<- 빈 것")
print("-2페이지 :", page(data, -2), "<- ★ 엉뚱한 구간이 나온다")
```

```text
2페이지  : [20, 21, 22, 23, 24]
9페이지  : [] <- 빈 것. 에러는 안 난다
-1페이지 : [] <- 빈 것
-2페이지 : [5, 6, 7, 8, 9, 10, 11, 12, 13, 14] <- ★ 엉뚱한 구간이 나온다
```

★ **음수 페이지에서 두 가지가 다르게 난다.**\
`-1` 은 `data[-10:0]` 이라 **빈 것**이고(시작이 끝보다 뒤), `-2` 는 `data[-20:-10]` 이라
**뒤에서 센 엉뚱한 데이터 10개**가 나온다. 둘 다 예외가 아니다.\
★ **한 판(`-1`)만 재고 「음수면 빈 것」으로 결론을 세웠다면 틀렸을 자리다.**\
`n` 이 음수일 수 있는지를 **슬라이스가 대신 검사해 주지 않는다.**

> **조용한 실패(silent failure)** — 에러 없이 정상처럼 끝나는데 결과만 틀린 것.\
> 여기서는 빈 페이지와 음수 오프셋이 그것이다. 로그도 안 남는다.

**비용** — 경계 검사를 안 써도 되어 코드가 짧아진다(`s[:n]` 이 `n > len(s)` 여도 안전하다).\
대신 **오프셋 버그가 예외로 드러나지 않는다.** 입력이 범위 안인지는 **직접** 검사해야 한다.

### 2. 세 수 — 음수와 step, 그리고 `s[::-1]`

**언제 쓰나** — 뒤집기·건너뛰기·끝에서 세기.

```text
 s[start : stop : step]

   start  포함    (생략하면 step>0 이면 처음, step<0 이면 끝)
   stop   제외    (생략하면 step>0 이면 끝 다음, step<0 이면 처음 앞)
   step   걸음    (생략하면 1. 0 이면 ValueError)
```

```python
s = [10, 20, 30, 40, 50]
print("s[-1] =", s[-1], "| s[-3:] =", s[-3:], "| s[:-3] =", s[:-3])
print("s[-1:-3] =", s[-1:-3], "| s[-3:-1] =", s[-3:-1])
print("s[::2]  =", s[::2], "| s[1::2] =", s[1::2])
print("s[::-1] =", s[::-1], "| s[::-2] =", s[::-2])
print("s[3:0:-1] =", s[3:0:-1], "| s[3::-1] =", s[3::-1])
try:
    s[::0]
except ValueError as e:
    print("s[::0] ->", type(e).__name__, e)
```

```text
s[-1] = 50 | s[-3:] = [30, 40, 50] | s[:-3] = [10, 20]
s[-1:-3] = [] | s[-3:-1] = [30, 40]
s[::2]  = [10, 30, 50] | s[1::2] = [20, 40]
s[::-1] = [50, 40, 30, 20, 10] | s[::-2] = [50, 30, 10]
s[3:0:-1] = [40, 30, 20] | s[3::-1] = [40, 30, 20, 10]
s[::0] -> ValueError slice step cannot be zero
```

**★ `s[::-1]` 이 왜 뒤집나 — 기본값이 뒤집히기 때문이다**

```text
 step 이 양수일 때                    step 이 음수일 때
   start 생략 -> 0                     start 생략 -> len(s)-1  (맨 끝)
   stop  생략 -> len(s)                stop  생략 -> "처음보다 앞"

 s[::-1] 은 s[len-1 : (0보다 앞) : -1]
   4번 -> 3번 -> 2번 -> 1번 -> 0번 을 지나 멈춘다
   = 전체를 거꾸로
```

★ **`s[-1:0:-1]` 로 쓰면 첫 원소가 빠진다** — `stop` 은 언제나 제외이기 때문이다.

```python
s = [10, 20, 30, 40, 50]
print("s[::-1]     =", s[::-1])
print("s[-1:0:-1]  =", s[-1:0:-1], " <- 10 이 빠졌다")
print("s[-1::-1]   =", s[-1::-1], " <- stop 을 생략해야 전부")
```

```text
s[::-1]     = [50, 40, 30, 20, 10]
s[-1:0:-1]  = [50, 40, 30, 20]  <- 10 이 빠졌다
s[-1::-1]   = [50, 40, 30, 20, 10]  <- stop 을 생략해야 전부
```

★ **「0 번 원소를 포함하는 역순 슬라이스」는 `stop` 으로 못 쓴다.** 0 보다 앞을 가리킬 방법이 없기 때문이다.\
`-1` 을 쓰면 **맨 끝**을 뜻하게 되어 빈 결과가 나온다.

```python
print("s[-1:-1:-1] =", s[-1:-1:-1], " <- -1 은 '맨 끝'이라 빈 것")
```

```text
s[-1:-1:-1] = []  <- -1 은 '맨 끝'이라 빈 것
```

**`s[::-1]` 대신 쓸 것들**

```python
s = [10, 20, 30]
print("s[::-1]           :", s[::-1], "  (새 리스트)")
print("list(reversed(s)) :", list(reversed(s)), "  (이터레이터 -> 리스트)")
t = s[:]
t.reverse()
print("t.reverse()       :", t, "  (제자리. 리스트만)")
print("원본 s            :", s)
```

```text
s[::-1]           : [30, 20, 10]   (새 리스트)
list(reversed(s)) : [30, 20, 10]   (이터레이터 -> 리스트)
t.reverse()       : [30, 20, 10]   (제자리. 리스트만)
원본 s            : [10, 20, 30]
```

| | 무엇을 돌려주나 | 메모리 | 어디에 쓰나 |
|---|---|---|---|
| `s[::-1]` | **새 시퀀스**(같은 타입) | 전체 복사 | 문자열·튜플도 된다 |
| `reversed(s)` | **이터레이터** | 거의 안 쓴다 | `for` 로만 돌 때 |
| `s.reverse()` | `None`(제자리) | 안 쓴다 | 리스트만. 원본을 바꾼다 |

**비용** — 슬라이스는 항상 **새 객체**라 원본이 안전하다(문자열·튜플에도 쓸 수 있다).\
대신 **전체를 복사**한다. 그냥 훑기만 할 거면 `reversed` 가 싸다.

### 3. 대괄호 안에 무엇이 들어가나 — `slice` 객체

**언제 쓰나** — 슬라이스를 변수에 담고 싶을 때. 그리고 `__getitem__` 을 직접 구현할 때.

```text
 s[1:4:2]  를 만나면 파이썬은

   slice(1, 4, 2)  라는 "객체" 를 만들어서
   s.__getitem__(그 객체)  를 부른다

  ★ 콜론은 문법이고, 넘어가는 것은 객체 하나다.
```

```python
class Show:
    def __getitem__(self, k):
        print(f"  __getitem__ 이 받은 것: {k!r}  ({type(k).__name__})")

x = Show()
x[1]
x[1:4]
x[1:4:2]
x[::-1]
x[1, 2]
x[1:2, 3]
x[...]
```

```text
  __getitem__ 이 받은 것: 1  (int)
  __getitem__ 이 받은 것: slice(1, 4, None)  (slice)
  __getitem__ 이 받은 것: slice(1, 4, 2)  (slice)
  __getitem__ 이 받은 것: slice(None, None, -1)  (slice)
  __getitem__ 이 받은 것: (1, 2)  (tuple)
  __getitem__ 이 받은 것: (slice(1, 2, None), 3)  (tuple)
  __getitem__ 이 받은 것: Ellipsis  (ellipsis)
```

그림 해설.

- **생략한 자리는 `None`** 이다. `0` 이 아니다 — `s[0:]` 과 `s[:]` 은 다른 `slice` 객체를 만든다(결과는 같다).
- ★ **쉼표를 쓰면 튜플이 된다.** `x[1, 2]` 가 `x[(1, 2)]` 다 — numpy·pandas 의 `df[a, b]` 가 이 문법 위에 서 있다.
- **`...`(Ellipsis)도 넘어간다.** 내장 시퀀스는 안 받지만 문법은 허용한다.

**`slice` 객체는 변수에 담을 수 있다**

```python
FIRST_THREE = slice(0, 3)
LAST_TWO = slice(-2, None)
row = "2026-09-24-부산-맑음"
print(row[FIRST_THREE], "|", row.split("-")[FIRST_THREE], "|", row.split("-")[LAST_TWO])
print("slice(3) =", slice(3), "| start,stop,step =", slice(3).start, slice(3).stop, slice(3).step)
```

```text
202 | ['2026', '09', '24'] | ['부산', '맑음']
slice(3) = slice(None, 3, None) | start,stop,step = None 3 None
```

★ **고정 폭 레코드를 파싱할 때 자리마다 이름을 붙일 수 있다.** 매직 넘버가 사라진다.

**★ `indices()` 가 「접기」를 눈에 보이게 한다**

```python
print("slice(1, 99, 2).indices(5)   =", slice(1, 99, 2).indices(5))
print("slice(None, None, -1).indices(5) =", slice(None, None, -1).indices(5))
print("slice(99, 200).indices(5)    =", slice(99, 200).indices(5))
print("뽑히는 자리:", list(range(*slice(1, 99, 2).indices(5))))
print("역순의 자리:", list(range(*slice(None, None, -1).indices(5))))
```

```text
slice(1, 99, 2).indices(5)   = (1, 5, 2)
slice(None, None, -1).indices(5) = (4, -1, -1)
slice(99, 200).indices(5)    = (5, 5, 1)
뽑히는 자리: [1, 3]
역순의 자리: [4, 3, 2, 1, 0]
```

그림 해설.

- **1번 절의 「접기」가 여기서 일어난다.** `99` 가 `5` 로, `200` 이 `5` 로 접혀 `(5, 5, 1)` — 그래서 빈 결과다.
- ★ **역순의 `stop` 이 `-1`** 이다. 「0 보다 앞」을 나타내는 유일한 방법이고,
  그래서 2번 절에서 **`s[-1:-1:-1]` 로는 그것을 못 쓴다**(`-1` 을 쓰면 「맨 끝」으로 해석되니까).
- `range(*indices)` 로 풀면 **실제로 뽑히는 자리 목록**이 나온다 — 슬라이스를 디버깅하는 가장 확실한 방법이다.

**비용** — 슬라이스를 이름 붙여 재사용할 수 있고, 사용자 정의 컨테이너가 같은 문법을 받을 수 있다.\
대신 **`__getitem__` 을 만들 때 `int` 와 `slice` 를 갈라 처리해야 한다.**

### 4. 슬라이스 대입과 `del` — 길이가 달라도 된다

**언제 쓰나** — 리스트의 한 구간을 통째로 갈 때. **가변 시퀀스에만** 있다.

문서의 표 —\
`s[i:j] = t` → *"slice of s from i to j is replaced by the contents of the iterable t"*\
`del s[i:j]` → *"same as `s[i:j] = []`"*

```text
 a = [1, 2, 3, 4, 5]
 a[1:3] = ["X"]

  전                          후
  +---+---+---+---+---+       +---+---+---+---+
  | 1 | 2 | 3 | 4 | 5 |       | 1 | X | 4 | 5 |
  +---+---+---+---+---+       +---+---+---+---+
      ^^^^^^^^                    ^^^
      2칸을 빼고                   1칸을 넣었다
                                ★ 길이가 5 -> 4 로 줄었다
```

```python
a = [1, 2, 3, 4, 5]
a[1:3] = ["X"]
print("a[1:3] = ['X']   ->", a, "len", len(a))
a[1:2] = ["p", "q", "r"]
print("a[1:2] = 3개     ->", a)
a[0:0] = ["앞"]
print("a[0:0] = 끼워넣기 ->", a)
b = [1, 2, 3]
i0 = id(b)
b[:] = [9, 9, 9, 9]
print("b[:] = 4개       ->", b, "| 같은 객체인가:", id(b) == i0)
```

```text
a[1:3] = ['X']   -> [1, 'X', 4, 5] len 4
a[1:2] = 3개     -> [1, 'p', 'q', 'r', 4, 5]
a[0:0] = 끼워넣기 -> ['앞', 1, 'p', 'q', 'r', 4, 5]
b[:] = 4개       -> [9, 9, 9, 9] | 같은 객체인가: True
```

★ `b[:] = ...` 는 「**내용만 통째로 갈기**」다. 객체는 그대로라 **다른 이름으로도 그 변화가 보인다**([01번](../01-object-and-name-binding/2-summary.md)).\
`b = [9,9,9,9]` 였다면 이름만 새 객체에 옮겨 붙었을 것이다 — **완전히 다른 일**이다.

**★ step 이 있으면 길이가 맞아야 한다**

```python
c = [1, 2, 3, 4, 5, 6]
c[::2] = ["a", "b", "c"]
print("c[::2] = 3개 ->", c)
try:
    c[::2] = ["a", "b"]
except ValueError as e:
    print("개수가 다르면 ->", type(e).__name__, e)
```

```text
c[::2] = 3개 -> ['a', 2, 'b', 4, 'c', 6]
개수가 다르면 -> ValueError attempt to assign sequence of size 2 to extended slice of size 3
```

```text
 연속 슬라이스  a[1:3] = t     길이가 달라도 된다 (구간을 통째로 갈아 끼운다)
 확장 슬라이스  a[::2] = t     ★ 개수가 정확히 맞아야 한다 (자리가 정해져 있다)
```

문서가 두 줄을 따로 적는 이유가 이것이다 — `s[i:j] = t` 와 `s[i:j:k] = t` 는 **다른 연산**이다.

**오른쪽은 이터러블이면 된다**

```python
d = [1, 2, 3]
d[0:1] = "XY"
print("문자열을 주면:", d)
d2 = [1, 2, 3]
d2[0:1] = range(3)
print("range 를 주면:", d2)
try:
    d3 = [1, 2, 3]; d3[0:1] = 9
except TypeError as e:
    print("정수를 주면 ->", type(e).__name__, e)
```

```text
문자열을 주면: ['X', 'Y', 2, 3]
range 를 주면: [0, 1, 2, 2, 3]
정수를 주면 -> TypeError can only assign an iterable
```

★ **문자열을 주면 글자로 풀린다.** `d[0:1] = "XY"` 가 `['X','Y',...]` 다 — 의도한 것이 아닐 때가 많다.

**`del` 도 같은 규칙이다**

```python
e = list(range(10))
del e[2:5]
print("del e[2:5] ->", e)
del e[::2]
print("del e[::2] ->", e)
del e[0]
print("del e[0]   ->", e)
```

```text
del e[2:5] -> [0, 1, 5, 6, 7, 8, 9]
del e[::2] -> [1, 6, 8]
del e[0]   -> [6, 8]
```

**불변 시퀀스는 전부 거부한다**

```python
for name, obj, op in [("tuple", (1, 2, 3), "slice"), ("str", "abc", "slice")]:
    try:
        if name == "tuple":
            obj[0:1] = (9,)
        else:
            obj[0:1] = "X"
    except TypeError as ex:
        print(f"{name:10} ->", type(ex).__name__, ex)
ba = bytearray(b"abcdef")
ba[1:3] = b"XYZ"
print("bytearray 는 가변 :", ba)
```

```text
tuple      -> TypeError 'tuple' object does not support item assignment
str        -> TypeError 'str' object does not support item assignment
bytearray 는 가변 : bytearray(b'aXYZdef')
```

★ **`bytearray` 만 바이너리 쪽의 가변 시퀀스**다([06번](../06-strings-bytes-unicode/2-summary.md)).

**비용** — 구간 교체·삽입·삭제를 한 줄로 한다(`a[len(a):] = [x]` 가 `append` 와 같다).\
대신 **앞쪽을 건드리면 뒤를 전부 밀어야** 한다 — 리스트는 연속 메모리라 O(n) 이다.

### 5. `s[:]` 가 얕은 복사인 것 — 타입마다 다르다

**언제 쓰나** — 리스트를 따로 들고 싶을 때. 그리고 순회 중에 바꿔야 할 때.

```python
l, t, s2, b, ba, r = [1, 2, 3], (1, 2, 3), "abc", b"ab", bytearray(b"ab"), range(3)
for name, o in [("list", l), ("tuple", t), ("str", s2), ("bytes", b), ("bytearray", ba), ("range", r)]:
    print(f"{name:10} o[:] is o -> {o[:] is o}")
```

```text
list       o[:] is o -> False
tuple      o[:] is o -> True
str        o[:] is o -> True
bytes      o[:] is o -> True
bytearray  o[:] is o -> False
range      o[:] is o -> False
```

★ **불변 타입은 `[:]` 가 자기 자신을 돌려준다** — 새로 만들 이유가 없기 때문이다.\
★ 단 이것은 **CPython 의 최적화**다. 문서가 약속하지 않는다.
★ **`range` 는 불변인데도 새 객체**를 만든다 — 규칙이 「불변이면 자기 자신」이 아니라는 증거다.

**얕다는 뜻**

```text
 nested = [[1,2],[3,4]]
 shallow = nested[:]

   nested  ---> [ * , * ]          겉바구니는 둘
                  |   |
   shallow ---> [ * , * ]          ★ 안의 리스트는 같은 객체 하나씩
                  |   |
                  v   v
               [1,2] [3,4]
```

```python
nested = [[1, 2], [3, 4]]
shallow = nested[:]
print("겉은 다른 객체:", shallow is nested)
print("안은 같은 객체:", shallow[0] is nested[0])
shallow[0][0] = 99
print("한쪽 안을 바꾸면:", nested)
shallow[1] = "새것"
print("겉 칸을 바꾸면  :", nested, shallow)
```

```text
겉은 다른 객체: False
안은 같은 객체: True
한쪽 안을 바꾸면: [[99, 2], [3, 4]]
겉 칸을 바꾸면  : [[99, 2], [3, 4]] [[99, 2], '새것']
```

문서의 정의 그대로다 — 얕은 복사는 *"inserts **references** into it to the objects found in the original"*.\
깊은 복사와 `copy` 모듈은 **[03번 주제](../03-mutability-and-copying/2-summary.md)가 정본**이다. 여기서는 슬라이스가 그 네 형태 중 하나라는 것만 짚는다.

**★ 순회 중 변경을 막는 관용구**

```python
items = [1, 2, 4, 5]
for x in items[:]:          # 복사본을 돈다
    if x % 2 == 0:
        items.remove(x)
print("복사본을 돌면:", items)

items = [1, 2, 4, 5]
for x in items:             # 원본을 돈다
    if x % 2 == 0:
        items.remove(x)
print("원본을 돌면  :", items, " <- ★ 4 가 안 지워졌다")
```

```text
복사본을 돌면: [1, 5]
원본을 돌면  : [1, 4, 5]  <- ★ 4 가 안 지워졌다
```

```text
 원본을 돌 때 일어나는 일

  i=0  items=[1,2,4,5]  x=items[0]=1   지나간다
  i=1  items=[1,2,4,5]  x=items[1]=2   지운다 -> [1,4,5]
  i=2  items=[1,4,5]    x=items[2]=5   ★ 4 를 건너뛰었다 (뒤가 당겨졌으니까)
  i=3  범위 밖 -> 멈춘다
```

★ **에러가 안 난다.** 인덱스가 밀려서 한 칸을 건너뛸 뿐이다 — 또 하나의 조용한 실패다.\
★ **테스트 데이터를 잘못 고르면 이 버그가 안 보인다.** `[1,2,3,4]` 로 재면 우연히 `[1,3]` 이 나와
「잘 된다」로 읽힌다 — **짝수가 이웃해 있어야** 드러난다.

**비용** — `[:]` 는 짧고 어떤 시퀀스에도 쓸 수 있다.\
대신 **안쪽은 공유**하고, 큰 리스트에서는 전체 복사 비용이 든다.

### 6. `+`·`*` 는 새 객체를 만든다 — 그리고 `[[]] * 3`

**언제 쓰나** — 초기값 만들기. 2차원 격자 만들기. **여기서 사고가 난다.**

문서가 두 문장을 따로 못 박는다 —\
*"Concatenating immutable sequences always results in a new object."*\
*"Note that items in the sequence s are **not copied**; they are referenced multiple times. **This often haunts new Python programmers**."*

```text
 [[]] * 3

        [ * , * , * ]       칸은 셋
          |   |   |
          +---+---+
              |
              v
             [ ]            ★ 리스트는 하나
```

```python
grid = [[]] * 3
print("만든 직후:", grid)
print("세 칸이 같은 객체인가:", grid[0] is grid[1] is grid[2])
grid[0].append("X")
print("한 칸에 넣으면:", grid)

ok = [[] for _ in range(3)]
ok[0].append("X")
print("컴프리헨션으로:", ok, "| 같은 객체:", ok[0] is ok[1])
```

```text
만든 직후: [[], [], []]
세 칸이 같은 객체인가: True
한 칸에 넣으면: [['X'], ['X'], ['X']]
컴프리헨션으로: [['X'], [], []] | 같은 객체: False
```

★ **문서가 이 예를 그대로 싣는다.** `lists = [[]] * 3` → `lists[0].append(3)` → `[[3], [3], [3]]`.

**★ 숫자는 왜 안 걸리나**

```python
nums = [0] * 3
nums[0] = 9
print(nums, " <- 대입은 그 칸의 이름을 다시 묶을 뿐")
```

```text
[9, 0, 0]  <- 대입은 그 칸의 이름을 다시 묶을 뿐
```

```text
 nums[0] = 9        ★ 칸이 가리키는 곳을 바꾼다 (다른 칸은 그대로)
 grid[0].append(X)  ★ 칸이 가리키는 "그 객체" 를 바꾼다 (셋이 같은 객체라 셋 다 보인다)

  ★ 문제는 * 가 아니라 "안에 든 것이 가변인가" 다.
    0 은 불변이라 append 같은 것이 아예 없다.
```

[01번](../01-object-and-name-binding/2-summary.md)의 「대입은 이름을 묶는다」와 [03번](../03-mutability-and-copying/2-summary.md)의 「가변·불변」이 여기서 만난다.

**2차원은 두 겹이 다 걸린다**

```python
bad = [[0] * 2] * 2
bad[0][0] = 9
print("[[0]*2]*2 :", bad)
good = [[0] * 2 for _ in range(2)]
good[0][0] = 9
print("컴프리헨션  :", good)
```

```text
[[0]*2]*2 : [[9, 0], [9, 0]]
컴프리헨션  : [[9, 0], [0, 0]]
```

**안쪽 `[0]*2` 는 괜찮다**(원소가 불변) — 바깥 `* 2` 만 문제다.

**`+` 와 `+=` 는 리스트에서 다르다**

```python
a = [1, 2]
b = a + [3]
print("a + [3] 이 a 인가:", b is a, "| a 는 그대로:", a)

a2 = a
a += [3]
print("a += [3] 뒤 a2   :", a2, "| 같은 객체:", a2 is a)

t1 = (1, 2); t2 = t1
t1 += (3,)
print("튜플의 += 뒤 t2  :", t2, "| 같은 객체:", t1 is t2)
```

```text
a + [3] 이 a 인가: False | a 는 그대로: [1, 2]
a += [3] 뒤 a2   : [1, 2, 3] | 같은 객체: True
튜플의 += 뒤 t2  : (1, 2) | 같은 객체: False
```

```text
 리스트의 +=   제자리 확장 (extend) -> 같은 객체. 다른 이름에도 보인다
 튜플의 +=     새 튜플을 만들어 이름을 다시 묶는다 -> 다른 객체

  ★ 같은 연산자가 타입에 따라 "제자리" 와 "새 객체" 로 갈린다.
```

**`* n` 에서 `n` 이 0 이하면**

```python
print(repr([1, 2] * 0), repr([1, 2] * -1), repr("abc" * -5), repr((1,) * 0))
```

```text
[] [] '' ()
```

문서 — *"Values of n less than `0` are treated as `0`."* **에러가 아니다.**

**비용** — `*` 로 초기 격자를 한 줄에 만든다. 원소가 불변이면 안전하고 빠르다.\
대신 **가변 원소에 쓰면 전부 같은 객체**가 된다. 그리고 `+` 를 루프에서 반복하면 **제곱 비용**이다(문서가 명시한다).

### 7. `in` 은 타입마다 묻는 것이 다르다

**언제 쓰나** — 포함 검사. 문자열과 리스트가 다르게 동작한다.

문서가 특례로 적는다 —\
*"While the `in` and `not in` operations are used only for simple containment testing in the general case, **some specialised sequences (such as str, bytes and bytearray) also use them for subsequence testing**."*

```text
 "bc" in "abcd"        ★ 부분 "열" 을 찾는다  -> True
 [2,3] in [1,2,3,4]    원소를 찾는다          -> False
 [2,3] in [[2,3],1]    원소로 있으면          -> True
 b"bc" in b"abcd"      ★ bytes 도 부분 열      -> True
```

```python
print("'bc' in 'abcd'     :", "bc" in "abcd")
print("'' in 'abcd'       :", "" in "abcd", " <- 빈 것은 언제나 들어 있다")
print("[2,3] in [1,2,3,4] :", [2, 3] in [1, 2, 3, 4], " <- 원소로 본다")
print("[2,3] in [[2,3],1] :", [2, 3] in [[2, 3], 1])
print("(2,3) in (1,2,3)   :", (2, 3) in (1, 2, 3))
print("b'bc' in b'abcd'   :", b"bc" in b"abcd", " <- bytes 도 부분 열")
print("98 in b'abcd'      :", 98 in b"abcd", " <- 정수도 받는다")
try:
    "a" in b"abcd"
except TypeError as e:
    print("'a' in b'abcd'     ->", type(e).__name__, e)
```

```text
'bc' in 'abcd'     : True
'' in 'abcd'       : True  <- 빈 것은 언제나 들어 있다
[2,3] in [1,2,3,4] : False  <- 원소로 본다
[2,3] in [[2,3],1] : True
(2,3) in (1,2,3)   : False
b'bc' in b'abcd'   : True  <- bytes 도 부분 열
98 in b'abcd'      : True  <- 정수도 받는다
'a' in b'abcd'     -> TypeError a bytes-like object is required, not 'str'
```

★ **`bytes` 의 `in` 은 두 가지를 받는다** — `bytes`(부분 열)와 `int`(바이트 하나).\
[06번](../06-strings-bytes-unicode/2-summary.md)의 「`b[0]` 은 정수」가 여기서도 이어진다.

**비교의 순서와 `is` 우선은 [02번](../02-is-vs-eq-interning/2-summary.md)·[05번](../05-truthiness-and-short-circuit/2-summary.md)이 정본**이다 —
컨테이너의 `x in y` 는 `any(x is e or x == e for e in y)` 와 같다.

**비용** — 문자열에서는 부분 문자열 검사가 공짜로 된다.\
대신 **리스트에서는 O(n)** 이고, 「부분 열 검사」를 기대하면 조용히 `False` 가 나온다.

### 8. `range` 가 시퀀스인 것 — `in` 이 훑지 않는다

**언제 쓰나** — 큰 범위를 다룰 때. 「이 값이 범위 안인가」를 물을 때.

문서 — *"Ranges implement all of the common sequence operations except concatenation and repetition."*

```python
r = range(0, 10_000_000, 3)
print("len:", len(r), "| r[2]:", r[2], "| r[-1]:", r[-1], "| r[2:5]:", r[2:5], list(r[2:5]))
print("index/count:", r.index(9), r.count(9))
try:
    r + r
except TypeError as e:
    print("r + r ->", type(e).__name__, e)
```

```text
len: 3333334 | r[2]: 6 | r[-1]: 9999999 | r[2:5]: range(6, 15, 3) [6, 9, 12]
index/count: 3 1
r + r -> TypeError unsupported operand type(s) for +: 'range' and 'range'
```

★ **`range` 를 슬라이스하면 `range` 가 나온다.** 리스트로 펴지 않는다 — 메모리를 안 쓴다.

**★ `in` 이 훑지 않는다 — 단 정수일 때만**

```python
import time
def med(fn, n=5):
    ts = []
    for _ in range(n):
        t0 = time.perf_counter(); fn(); ts.append(time.perf_counter() - t0)
    ts.sort(); return ts[n // 2]

r10 = range(10**7)
l10 = list(range(10**7))
for label, fn in [
    ("range(10**7) 에 9999999 (int)",   lambda: 9999999 in r10),
    ("list(10**7) 에 9999999",          lambda: 9999999 in l10),
    ("range(10**7) 에 9999999.0 (float)", lambda: 9999999.0 in r10),
    ("range(10**7) 에 0.5",             lambda: 0.5 in r10),
    ("range(10**7) 에 -1 (없는 int)",    lambda: -1 in r10),
]:
    print(f"{label:36} 중앙값 {med(fn)*1e6:12.1f}us")
```

```text
range(10**7) 에 9999999 (int)         중앙값          0.4us
list(10**7) 에 9999999                중앙값      81027.4us
range(10**7) 에 9999999.0 (float)     중앙값     338348.1us
range(10**7) 에 0.5                   중앙값     331697.7us
range(10**7) 에 -1 (없는 int)           중앙값          0.3us
```

```text
 range 의 in

   값이 int (또는 bool) 이면   ->  산술로 판정한다. 길이와 무관하게 거의 즉시
   그 밖이면                  ->  ★ 하나하나 꺼내 == 비교한다. 리스트와 같다

  ★ 타입 하나로 5자리 이상 갈린다.
```

★ **측정 조건** — 같은 프로세스에서 각 5회, 중앙값. **신호 대 잡음이 5\~6자리**라 순서가 뒤집힐 여지가 없다.\

★ **제출 직전에 다시 찍었다 — 그리고 움직였다.** 처음 값을 지우지 않고 나란히 둔다.

```text
 무엇                              처음     재측정 1   재측정 2   재측정 3
 --------------------------------  -------  ---------  ---------  ---------
 range 에 9999999 (int)              0.4us     0.3us      0.2us      0.1us
 list 에 9999999                 81027us    79115us    75357us    69125us
 range 에 9999999.0 (float)     338348us   280183us   278842us   301828us
 range 에 0.5                   331698us   315924us   307314us   316745us
 range 에 -1 (없는 int)              0.3us     0.2us     0.1us      0.1us
```

★ **흔들리는 칸과 안 흔들리는 칸** — 절댓값은 판마다 10\~20% 움직이는데,
**「정수는 마이크로초, 정수 아닌 것은 수십만 마이크로초」라는 자릿수 구분은 네 판 전부 같았다.**\
결론은 그 자릿수 위에 세운 것이지 절댓값 위에 세운 것이 아니다.

★ **절댓값은 이 머신의 관찰**이다. 재현되는 것은 **자릿수 차이**이지 구체적 수가 아니다.

★ **이 실험은 한 판으로 결론이 안 섰다.** 처음 `3.0 in range(10**7)` 로 재니 **1us 미만**이 나왔다 —
「float 도 빠르다」로 보였지만, **3.0 은 3번 자리에서 바로 찾아서** 빠른 것이었다.\
**끝에 있는 `9999999.0`** 으로 다시 재야 33만 us 가 나온다. **찾는 위치를 경계로 옮겨야** 갈림이 드러났다.

```python
print("3.0 in range(10**7)     :", f"{med(lambda: 3.0 in r10)*1e6:.1f}us  <- 3번 자리에서 바로 찾는다")
print("9999999.0 in range(10**7):", f"{med(lambda: 9999999.0 in r10)*1e6:.1f}us  <- 끝까지 훑는다")
```

```text
3.0 in range(10**7)     : 0.4us  <- 3번 자리에서 바로 찾는다
9999999.0 in range(10**7): 322917.1us  <- 끝까지 훑는다
```

**`range` 는 시퀀스이고 `set`·`dict` 는 아니다**

```python
import collections.abc as abc
for name, obj in [("list", [1]), ("tuple", (1,)), ("str", "a"), ("range", range(1)),
                  ("bytes", b"a"), ("bytearray", bytearray(b"a")), ("set", {1}), ("dict", {1: 1})]:
    print(f"{name:10} Sequence={isinstance(obj, abc.Sequence)!s:6} MutableSequence={isinstance(obj, abc.MutableSequence)!s:6} Reversible={isinstance(obj, abc.Reversible)}")
```

```text
list       Sequence=True   MutableSequence=True   Reversible=True
tuple      Sequence=True   MutableSequence=False  Reversible=True
str        Sequence=True   MutableSequence=False  Reversible=True
range      Sequence=True   MutableSequence=False  Reversible=True
bytes      Sequence=True   MutableSequence=False  Reversible=True
bytearray  Sequence=True   MutableSequence=True   Reversible=True
set        Sequence=False  MutableSequence=False  Reversible=False
dict       Sequence=False  MutableSequence=False  Reversible=True
```

★ **`dict` 가 `Reversible` 이다**(3.8+, 삽입 순서 보장 위에서) — 하지만 **시퀀스는 아니다.** 정수 인덱스로 못 꺼낸다.

**비용** — `range` 는 길이와 무관하게 상수 메모리이고 정수 `in` 이 O(1) 이다.\
대신 **`+`·`*` 가 없고**, 정수가 아닌 값의 `in` 은 리스트만큼 느리다.

### 9. 네 타입이 공유하는 연산

**언제 쓰나** — 「이 연산이 이 타입에도 있나」를 물을 때.

```python
objs = {"list": [1, 2, 3, 2], "tuple": (1, 2, 3, 2), "str": "1232",
        "range": range(1, 5), "bytes": b"\x01\x02\x03\x02"}
ops = [
    ("len(s)", lambda s: len(s)), ("s[0]", lambda s: s[0]), ("s[1:3]", lambda s: s[1:3]),
    ("s + s", lambda s: s + s), ("s * 2", lambda s: s * 2), ("s * -1", lambda s: s * -1),
    ("min(s)", lambda s: min(s)), ("max(s)", lambda s: max(s)),
    ("s.index(3)", lambda s: s.index(3)), ("s.count(2)", lambda s: s.count(2)),
    ("list(reversed(s))", lambda s: list(reversed(s))),
]
for label, fn in ops:
    row = []
    for name, o in objs.items():
        try:
            row.append(f"{name}={fn(o)!r}")
        except Exception as e:
            row.append(f"{name}={type(e).__name__}")
    print(f"{label:20} " + "  ".join(row))
```

```text
len(s)               list=4  tuple=4  str=4  range=4  bytes=4
s[0]                 list=1  tuple=1  str='1'  range=1  bytes=1
s[1:3]               list=[2, 3]  tuple=(2, 3)  str='23'  range=range(2, 4)  bytes=b'\x02\x03'
s + s                list=[1, 2, 3, 2, 1, 2, 3, 2]  tuple=(1, 2, 3, 2, 1, 2, 3, 2)  str='12321232'  range=TypeError  bytes=b'\x01\x02\x03\x02\x01\x02\x03\x02'
s * 2                list=[1, 2, 3, 2, 1, 2, 3, 2]  tuple=(1, 2, 3, 2, 1, 2, 3, 2)  str='12321232'  range=TypeError  bytes=b'\x01\x02\x03\x02\x01\x02\x03\x02'
s * -1               list=[]  tuple=()  str=''  range=TypeError  bytes=b''
min(s)               list=1  tuple=1  str='1'  range=1  bytes=1
max(s)               list=3  tuple=3  str='3'  range=4  bytes=3
s.index(3)           list=2  tuple=2  str=TypeError  range=2  bytes=2
s.count(2)           list=2  tuple=2  str=TypeError  range=1  bytes=2
list(reversed(s))    list=[2, 3, 2, 1]  tuple=[2, 3, 2, 1]  str=['2', '3', '2', '1']  range=[4, 3, 2, 1]  bytes=[2, 3, 2, 1]
```

★ **같은 이름의 연산이 타입마다 다른 것을 돌려준다.**

| 연산 | 걸리는 자리 |
|---|---|
| `s[0]` | **`str` 은 `str`, `bytes` 는 `int`**([06번](../06-strings-bytes-unicode/2-summary.md)) |
| `s[1:3]` | 언제나 **자기 타입** — `range` 도 `range` 를 준다 |
| `s + s` · `s * 2` | **`range` 에는 없다**(문서가 예외로 적는다) |
| `s.index(3)` | **`str` 은 `int` 를 못 받는다** — 인자도 `str` 이어야 한다 |
| `reversed(s)` | 이터레이터. `list()` 로 펴야 보인다 |

**가변 시퀀스에만 있는 것**

```python
for name, obj in [("list", [1, 2, 3]), ("bytearray", bytearray(b"abc")), ("tuple", (1, 2, 3))]:
    have = [m for m in ("append", "extend", "insert", "pop", "remove", "reverse", "clear", "sort") if hasattr(obj, m)]
    print(f"{name:10} {have}")
```

```text
list       ['append', 'extend', 'insert', 'pop', 'remove', 'reverse', 'clear', 'sort']
bytearray  ['append', 'extend', 'insert', 'pop', 'remove', 'reverse', 'clear']
tuple      []
```

★ **`sort` 는 `list` 에만 있다.** `bytearray` 는 나머지를 다 갖췄는데 정렬만 없다.

**비용** — 공통 연산 덕에 코드가 타입에 덜 묶인다(`len`·슬라이스·`in` 은 어디서나 같다).\
대신 **반환 타입과 원소 타입이 달라지는** 자리가 있어 그대로 옮겨 쓰면 터진다.

## 문법 — 형태와 규칙

```python
s[i]                 # 인덱싱 — 범위 밖이면 IndexError
s[i:j]               # 슬라이싱 — 범위 밖이어도 안 터진다
s[i:j:k]             # step. k 가 0 이면 ValueError
s[::-1]              # 역순 (새 객체)
s[:]                 # 얕은 복사 (불변 타입은 자기 자신을 줄 수도 있다)

s + t                # 새 객체 (range 에는 없다)
s * n                # 새 객체. n <= 0 이면 빈 것. ★ 원소는 복사되지 않는다
x in s               # str/bytes/bytearray 는 부분 열, 그 밖은 원소
len(s) min(s) max(s)
s.index(x[, i[, j]]) # 없으면 ValueError
s.count(x)

# 가변 시퀀스만
s[i:j] = iterable    # 길이가 달라도 된다
s[i:j:k] = iterable  # ★ 개수가 정확히 맞아야 한다
del s[i:j]           # s[i:j] = [] 와 같다
s[:] = iterable      # 내용만 통째로 갈기 (객체는 그대로)

# slice 객체
sl = slice(1, 4, 2)
s[sl]                # s[1:4:2] 와 같다
sl.indices(len(s))   # (start, stop, step) 으로 접어 준다
```

규칙은 여덟이다.

1. **인덱싱은 `IndexError` 를 내고 슬라이싱은 안 낸다.** 범위 밖은 **`len(s)` 로 접힌다.**
2. **`stop` 은 언제나 제외**다. 그래서 역순에서 0번 원소를 `stop` 으로 포함시킬 방법이 없다.
3. **`s[i:j:k]` 는 `slice` 객체 하나를 `__getitem__` 에 넘긴다.** 생략한 자리는 `None` 이다.
4. **슬라이스 대입은 길이를 바꾼다** — 단 **확장 슬라이스(step 있음)는 개수가 맞아야** 한다.
5. **`s[:] = ...` 는 객체를 바꾸지 않고 내용만 간다.** `s = ...` 와 완전히 다른 일이다.
6. **`+`·`*` 는 새 객체를 만들되 원소는 복사하지 않는다.** `[[]] * 3` 이 그 결과다.
7. **`in` 은 `str`·`bytes`·`bytearray` 에서만 부분 열 검사**다. 그 밖은 원소 검사.
8. **`range` 는 시퀀스지만 `+`·`*` 가 없고**, `in` 은 **정수일 때만** 산술로 판정한다.

## 어디서 틀리나

### (1) 슬라이스가 빈 것을 돌려줘도 에러가 안 난다

```python
data = list(range(25))
print(data[100:110])      # []   <- 오프셋이 틀렸는데 에러가 없다
print(data[-1000:-990])   # []
```

인덱싱이었다면 터졌을 것이다. **범위 검사를 직접** 해야 한다.

### (2) 음수 오프셋이 뒤에서 센다

```python
def page(items, n, size=10):
    return items[n * size : (n + 1) * size]
print(page(list(range(25)), -1))   # [15, 16, 17, 18, 19]
```

빈 것도 예외도 아니고 **엉뚱한 데이터**다. `n < 0` 을 막아야 한다.

### (3) 역순 슬라이스에서 첫 원소가 빠진다

```python
s = [10, 20, 30]
print(s[-1:0:-1])   # [30, 20]   <- 10 이 없다
print(s[::-1])      # [30, 20, 10]
```

`stop` 은 제외이고 `-1` 은 「맨 끝」이라 쓸 수 없다.

### (4) `[[0]*3]*3` 로 격자를 만든다

```python
g = [[0] * 3] * 3
g[0][0] = 1
print(g)            # [[1, 0, 0], [1, 0, 0], [1, 0, 0]]
```

**바깥 `*` 가 같은 리스트를 세 번 가리킨다.** `[[0]*3 for _ in range(3)]`.

### (5) `s[:] = x` 와 `s = x` 를 같은 것으로 본다

```python
a = [1, 2]; b = a
a[:] = [9]
print(b)            # [9]    <- b 에도 보인다
a = [8]
print(b)            # [9]    <- 이번엔 안 보인다
```

앞엣것은 **객체를 바꾸고** 뒤엣것은 **이름을 옮긴다**([01번](../01-object-and-name-binding/2-summary.md)).

### (6) 순회하면서 원소를 지운다

```python
items = [1, 2, 4, 5]
for x in items:
    if x % 2 == 0:
        items.remove(x)
print(items)        # [1, 4, 5]   <- 4 가 남았다
```

**에러가 안 난다.** `items[:]` 를 돌거나 새 리스트를 만든다.

### (7) `in` 이 부분 열을 찾아 줄 거라 믿는다

```python
print([2, 3] in [1, 2, 3, 4])   # False
```

문자열만 부분 열이다. 리스트의 부분 열은 직접 짜야 한다.

### (8) `range` 에 `+` 를 쓴다

```python
try:
    range(3) + range(3)
except TypeError as e:
    print(e)        # unsupported operand type(s) for +: 'range' and 'range'
```

`itertools.chain` 이나 `list(range(3)) + list(range(3))`.

### (9) 확장 슬라이스 대입에서 개수를 안 맞춘다

```python
c = [1, 2, 3, 4, 5, 6]
try:
    c[::2] = ["a", "b"]
except ValueError as e:
    print(e)        # attempt to assign sequence of size 2 to extended slice of size 3
```

연속 슬라이스는 되는데 step 이 있으면 안 된다.

## 구현 세부사항 대 언어 보장

세 층으로 가른다. ★ **이 주제는 「언어 보장」이 두껍다** — 슬라이스의 접기 규칙과 공통 연산은 문서가 표로 정한다.
관찰 층은 **`[:]` 의 객체 재사용**과 **시간 측정값** 둘이다.

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **언어 보장** | 라이브러리·언어 레퍼런스가 정한 것 | 공식 문서 문장을 열어서 인용 |
| **CPython 구현** | 이 구현이 그렇게 하는 것 | 실행 + `is` 로 확인 |
| **이 판·이 머신의 관찰** | 3.12.3 에서 그랬을 뿐 | 「관찰」로 명기 |

### 언어 보장

| 사실 | 근거 |
|---|---|
| `i` 나 `j` 가 `len(s)` 보다 크면 **`len(s)` 를 쓴다** | Common Sequence Operations 주 3 |
| `i` 가 `j` 이상이면 **빈 슬라이스** | 〃 |
| 음수 인덱스는 `len(s) + i` 로 바뀐다. **단 `-0` 은 여전히 `0`** | 〃 주 4 |
| `n` 이 0 미만이면 **0 으로 친다** | 〃 주 2 |
| **`s * n` 의 원소는 복사되지 않고 여러 번 참조된다** — 문서가 `[[]] * 3` 예까지 싣는다 | 〃 주 2 |
| 불변 열의 이어 붙이기는 **언제나 새 객체**이고 반복하면 **제곱 비용** | 〃 주 6 |
| `str`·`bytes`·`bytearray` 는 `in` 을 **부분 열 검사**로도 쓴다 | 〃 주 1 |
| `s[i:j] = t` 는 구간을 `t` 의 내용으로 **교체**하고 `del s[i:j]` 는 `s[i:j] = []` 와 같다 | Mutable Sequence Types 표 |
| `range` 는 **이어 붙이기와 반복을 뺀** 모든 공통 연산을 구현한다 | Ranges |
| `s[i:j:k]` 는 `slice` 객체를 `__getitem__` 에 넘긴다 | 언어 레퍼런스 6.3.4 |
| `slice.indices(len)` 이 `(start, stop, step)` 을 돌려준다 | `slice` |

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| **불변 시퀀스의 `s[:]` 가 자기 자신을 돌려준다**(`tuple`·`str`·`bytes`) | `t[:] is t` 가 `True` |
| 그런데 **`range` 는 불변인데도 새 객체**를 만든다 | `r[:] is r` 가 `False` |
| **`range` 의 `in` 이 정수일 때 산술로 판정**한다 | 길이 `10**7` 에서 0.4us 대 33만 us |
| 그 빠른 길에 **`bool` 도 들어간다** | `True in range(2)` 가 즉시 참 |
| 예외 문구(`list index out of range` 등) | 실행 |

### 이 판(3.12.3)·이 머신의 관찰

| 관찰 | 어디가 흔들리나 |
|---|---|
| `in` 의 시간 수치(0.3\~34만 us) | **머신·부하에 달렸다.** 재현되는 것은 **자릿수 차이**이지 절댓값이 아니다 |
| `list(10**7)` 의 `in` 이 약 8만 us | 〃 |
| 슬라이스의 예외 문구·`ValueError` 문구 | 예외 종류는 명세지만 문구는 아니다 |
| `bytearray` 에 `sort` 가 없는 것 | 문서가 `MutableSequence` 를 구현한다고만 적는다 |

★ **측정 조건** — 같은 프로세스에서 각 5회, 중앙값. **신호가 5\~6자리**라 순서가 뒤집힐 여지가 없다.
반대로 「`list` 가 8만이고 `range` 의 float 가 33만」 같은 **비슷한 두 값 사이의 대소**는 이 실험의 결론이 아니다.

### 그래서 이렇게 적으면 틀린다

- ✗ 「범위를 넘은 슬라이스는 에러가 난다」\
  ○ **안 난다.** 문서가 *"If i or j is greater than len(s), use len(s)"* 라고 정한다.
- ✗ 「`s[::-1]` 은 `s[-1:0:-1]` 과 같다」\
  ○ **첫 원소가 빠진다.** `stop` 은 언제나 제외다.
- ✗ 「`*` 는 원소를 복사한다」\
  ○ **참조를 여러 번 넣는다.** 문서가 *"not copied; they are referenced multiple times"* 라고 적고 `[[]] * 3` 예까지 싣는다.
- ✗ 「`s[:] = x` 는 `s = x` 와 같다」\
  ○ 앞엣것은 **객체의 내용을 바꾸고** 뒤엣것은 **이름을 다른 객체에 묶는다.**
- ✗ 「`[:]` 는 언제나 새 객체를 만든다」\
  ○ 불변 타입은 자기 자신을 돌려주기도 한다 — 단 그것은 **구현 세부사항**이고 `range` 는 또 다르다.
- ✗ 「`in` 은 부분 열을 찾는다」\
  ○ **`str`·`bytes`·`bytearray` 에서만** 그렇다.
- ✗ 「`range` 는 게으른 이터레이터다」\
  ○ **시퀀스**다. `len`·인덱싱·슬라이싱·`index`·`count` 가 전부 된다. 없는 것은 `+`·`*` 다.
- ✗ 「`x in range(n)` 은 O(1) 이다」\
  ○ **`x` 가 정수일 때만** 그렇다. 그 밖이면 훑는다.

**판정 기준 한 줄**: 어떤 코드가 「**범위를 넘으면 에러가 나겠지**」에 기대고 있으면, 그 자리가 슬라이스인지 인덱싱인지 확인하라.

## 언제 쓰고 언제 안 쓰나

| 쓰는 것 | 상황 |
|---|---|
| `s[i]` | 그 자리가 **반드시 있어야** 할 때 — 없으면 터지는 게 맞다 |
| `s[i:j]` | 구간을 꺼낼 때. **범위는 직접 검사**한다 |
| `s[:n]` | 「최대 n 개」 — 모자라도 안전하다 |
| `s[::-1]` | 역순 사본이 필요할 때(문자열·튜플 포함) |
| `reversed(s)` | 역순으로 **훑기만** 할 때 — 복사가 없다 |
| `s.reverse()` | 리스트를 **제자리**에서 뒤집을 때 |
| `s[:]` | 얕은 복사. **순회 중 변경**의 관용구 |
| `list(s)` | 얕은 복사 + **타입 고정**(`range`·`tuple` 을 리스트로) |
| `s[i:j] = t` | 구간 교체·삽입·삭제 |
| `s[:] = t` | **같은 객체를 유지한 채** 내용을 갈 때 |
| `slice(...)` 변수 | 고정 폭 레코드의 자리에 **이름을 붙일 때** |
| `[x for _ in range(n)]` | 가변 원소를 n 개 만들 때 — **`[x] * n` 을 쓰지 않는다** |
| `x in range(a, b)` | 「범위 안인가」 — **x 가 정수일 때** |
| `a <= x < b` | 〃 — x 가 정수가 아닐 수 있으면 이쪽 |

**안 쓰는 자리**는 셋이다.\
**가변 원소에 `* n` 을 쓰지 마라** — 같은 객체가 n 번 들어간다.\
**순회 중에 원본을 지우지 마라** — 에러 없이 건너뛴다.\
**슬라이스가 범위 검사를 대신해 줄 거라 기대하지 마라** — 조용히 빈 것을 준다.

## 핵심 문장

- **인덱싱은 칸을 가리키고 슬라이싱은 칸 사이의 금을 가리킨다.** 그래서 하나는 `IndexError` 를 내고 하나는 **빈 것**을 준다.
- 그 관대함이 **조용한 실패의 통로**다 — 오프셋이 틀려도 빈 페이지가, 음수면 **엉뚱한 구간**이 나온다.
- **`stop` 은 언제나 제외**다. 그래서 역순에서 0번 원소를 `stop` 으로 포함시킬 방법이 없고, `s[::-1]` 이 그 유일한 관용구다.
- **`s[1:4:2]` 는 `slice(1,4,2)` 객체 하나를 넘긴다.** `indices(len)` 가 「접기」를 눈에 보이게 한다.
- **슬라이스 대입은 길이를 바꾸고** step 이 붙으면 **개수가 맞아야** 한다. `s[:] = t` 는 객체를 유지한 채 내용만 간다.
- **`*` 는 원소를 복사하지 않는다.** 문서가 `[[]] * 3` 을 예로 싣는다 — 문제는 `*` 가 아니라 **안에 든 것이 가변인가**다.
- **`in` 은 `str`·`bytes`·`bytearray` 에서만 부분 열**이다. 리스트에서는 원소 검사다.
- **`range` 는 이터레이터가 아니라 시퀀스**다. 정수 `in` 은 산술로 즉시 답하고, **정수가 아니면 끝까지 훑는다.**

## 관련 자료

- 목록: [python/syntax 주제 목록](../README.md) — 이 주제는 **09번**
- 선행: [01-object-and-name-binding](../01-object-and-name-binding/2-summary.md) — `s[:] = t` 와 `s = t` 가 다른 이유의 정본.
- 선행: [03-mutability-and-copying](../03-mutability-and-copying/2-summary.md) — **얕은 복사 네 형태의 정본**. `s[:]` 가 그중 하나다. 깊은 복사는 그쪽이다.
- 이어지는 곳: [06-strings-bytes-unicode](../06-strings-bytes-unicode/2-summary.md) — `bytes[0]` 이 정수인 것, `bytearray` 가 가변인 것.
- 이어지는 곳: [07-string-methods](../07-string-methods/2-summary.md) — `str` 의 `index`/`count` 는 인자도 `str` 이어야 한다.
- 이어지는 곳: [02-is-vs-eq-interning](../02-is-vs-eq-interning/2-summary.md)·[05-truthiness-and-short-circuit](../05-truthiness-and-short-circuit/2-summary.md) — `in` 이 `is` 를 먼저 본다는 규정.
- 이어지는 곳: [14-comprehensions](../14-comprehensions/2-summary.md) — `[[] for _ in range(3)]` 이 `[[]] * 3` 의 해법인 이유.
- 이어지는 곳: 목록의 **10번 주제** 「list 메서드와 정렬 키」 — `sort` 대 `sorted`, 그리고 `s[:]` 로 정렬본을 따로 들기.
- 이어지는 곳: 목록의 **11번 주제** 「tuple 과 언패킹」 — 별표 언패킹이 슬라이스와 겹치는 자리.
- 이어지는 곳: 목록의 **18번 주제** 「반복 제어」 — 순회 중 컨테이너 변경.
- 이어지는 곳: 목록의 **32번 주제** 「컨테이너 프로토콜」 — `__getitem__` 에서 `int` 와 `slice` 를 갈라 받는 법.
- 이어지는 곳: 목록의 **43번 주제** 「`collections`」 — 앞쪽 삽입·삭제가 잦으면 `deque`.
- 기존 노트: [`cs/foundations/python-basics/`](../../../../python-basics/) — 리스트·인덱싱을 「이렇게 쓴다」까지 다룬다.\
  **경계**: 그쪽은 사용 예시까지, 여기는 「**무엇이 안 터지고 무엇이 공유되나**」부터다.
- 자료구조의 원리(동적 배열의 증폭·복잡도)는 여기가 아니다: [`cs/data-structure/`](../../../../../data-structure/)
- 공식 문서: [Common Sequence Operations](https://docs.python.org/3.12/library/stdtypes.html#common-sequence-operations) · [Mutable Sequence Types](https://docs.python.org/3.12/library/stdtypes.html#mutable-sequence-types) · [Ranges](https://docs.python.org/3.12/library/stdtypes.html#ranges) · [`slice`](https://docs.python.org/3.12/library/functions.html#slice)

## 용어 풀이

- **시퀀스(sequence)**: 순서가 있고 정수 인덱스로 꺼낼 수 있는 것.\
  `list`·`tuple`·`str`·`bytes`·`bytearray`·`range`. `set`·`dict` 는 아니다.
- **가변 시퀀스(mutable sequence)**: 원소 대입·삽입·삭제가 되는 시퀀스. `list` 와 `bytearray` 둘뿐이다(내장 중).
- **인덱싱(subscription)**: `s[i]` — **칸 하나**를 가리킨다. 범위 밖이면 `IndexError`.
- **슬라이싱(slicing)**: `s[i:j:k]` — **구간**을 가리킨다. 범위 밖은 `len(s)` 로 접힌다.
- **`slice` 객체**: `s[1:4:2]` 가 실제로 만들어 `__getitem__` 에 넘기는 객체.\
  생략한 자리는 `None` 이고 `indices(len)` 으로 실제 자리를 얻는다.
- **확장 슬라이스(extended slice)**: step 이 있는 슬라이스.\
  대입할 때 **개수가 정확히 맞아야** 한다는 점에서 연속 슬라이스와 다르다.
- **얕은 복사(shallow copy)**: 새 컨테이너를 만들되 **안의 객체는 그대로 참조**하는 복사.\
  `s[:]`·`list(s)`·`copy.copy(s)`·`s.copy()` 가 같은 일을 한다([03번](../03-mutability-and-copying/2-summary.md)).
- **`Ellipsis` (`...`)**: `x[...]` 로 넘길 수 있는 내장 상수. 내장 시퀀스는 안 받지만 문법은 허용한다.
- **조용한 실패(silent failure)**: 에러 없이 정상처럼 끝나는데 결과만 틀린 것.\
  범위 밖 슬라이스·음수 오프셋·순회 중 삭제가 이 주제의 셋이다.
- **제곱 비용(quadratic cost)**: 불변 열을 반복해 이어 붙일 때 드는 비용.\
  문서가 *"quadratic runtime cost in the total sequence length"* 라고 적는다.

## 더 들어가면

- **`itertools.islice`** 는 이터레이터에 슬라이스를 흉내 낸다 — 단 **음수 인덱스와 음수 step 을 못 받는다**(앞에서부터 세는 수밖에 없다).
- **`memoryview`** 를 쓰면 `bytes` 의 슬라이스가 **복사 없이** 된다([06번](../06-strings-bytes-unicode/2-summary.md)).
- **`list.insert(0, x)` 와 `del s[0]` 은 O(n)** 이다. 앞쪽이 잦으면 `collections.deque`(목록의 **43번 주제**).
- **numpy 의 슬라이스는 뷰**다 — 파이썬 리스트의 슬라이스가 복사인 것과 정반대라, 옮겨 쓸 때 가장 크게 어긋나는 자리다(이 환경에 `numpy` 가 없어 **실행 검증하지 않았다**).
- **`s[i:j]` 의 반환 타입을 사용자 클래스에서 정하려면** `__getitem__` 안에서 `isinstance(k, slice)` 를 갈라 처리한다(목록의 **32번 주제**).
