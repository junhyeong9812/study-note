# python/syntax/11-tuple-and-unpacking — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만.
> - [6.2.3. Parenthesized forms](https://docs.python.org/3.12/reference/expressions.html#parenthesized-forms) — 「**괄호가 튜플을 만드는 게 아니다**」
> - [6.15. Expression lists](https://docs.python.org/3.12/reference/expressions.html#expression-lists) — 쉼표가 튜플을 만든다 · 한 원소 튜플의 쉼표
> - [7.2. Assignment statements](https://docs.python.org/3.12/reference/simple_stmts.html#assignment-statements) — 대상 목록·별표 대상의 규칙
> - [Tuples](https://docs.python.org/3.12/library/stdtypes.html#tuples) — `tuple(iterable)` 이 이미 튜플이면 그대로 돌려준다
> - [`collections.namedtuple`](https://docs.python.org/3.12/library/collections.html#collections.namedtuple) · [`typing.NamedTuple`](https://docs.python.org/3.12/library/typing.html#typing.NamedTuple)
>
> **실행 검증** — 이 문서에 실린 출력은 전부 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> **버전** — 별표 언패킹은 3.0(PEP 3132), 리터럴·호출 안의 `*`/`**` 확장은 3.5(PEP 448). `getsizeof`·바이트코드 명령 이름은 **이 판의 관찰**이다.
> **선행** — [01-object-and-name-binding](../01-object-and-name-binding/2-summary.md)(스왑의 `dis` 정본) ·
> [09-sequence-ops-and-slicing](../09-sequence-ops-and-slicing/2-summary.md)(시퀀스 공통 연산·`t[:]`) ·
> [03-mutability-and-copying](../03-mutability-and-copying/2-summary.md)(불변 안의 가변 정본).

## 한눈에 — 쉽게 말하면

**튜플을 만드는 것은 괄호가 아니라 쉼표다. 괄호는 「묶어 읽어라」는 표시일 뿐이다.**

```text
  (1)      ->  int 1          괄호는 그냥 "묶어 읽기"
  (1,)     ->  tuple (1,)     쉼표가 튜플을 만든다
   1,      ->  tuple (1,)     괄호가 없어도 된다
   1, 2    ->  tuple (1, 2)
  ()       ->  tuple ()       ★ 빈 튜플만은 괄호가 필수다 (쉼표를 쓸 자리가 없으니까)
```

문서가 그대로 적는다 — *"Note that **tuples are not formed by the parentheses, but rather by use of the comma**.
The exception is the empty tuple, for which parentheses are required."*

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 쉼표가 상자를 만든다 | `1,` · `1, 2` | `type(1,)` 이 `tuple` |
| 괄호는 묶어 읽으라는 표시 | `(1)` | `type((1))` 이 `int` |
| 빈 상자만은 괄호가 필요하다 | `()` | 쉼표를 쓸 자리가 없다 |
| 상자를 풀어 이름표를 나눠 준다 | 언패킹 `a, b = t` | 개수가 안 맞으면 `ValueError` |
| 남는 것은 **봉지**에 담는다 | 별표 `a, *rest = t` | `rest` 는 언제나 **`list`** |
| 봉지는 하나만 | `*a, *b = ...` | **`SyntaxError`** |
| 부르는 쪽의 `*` 는 **푸는** 것 | `f(*args)` | 여러 번 써도 된다 |
| 받는 쪽의 `*` 는 **모으는** 것 | `def f(*args)` | `args` 는 **`tuple`** |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.\
「**괄호를 쳤는데 튜플이 아니었다**」가 그것이다. `headers = ("Content-Type")` 은 문자열이고,
그 뒤에 `for h in headers:` 를 돌면 **글자가 하나씩** 나온다. 에러는 안 난다.

> **언패킹(unpacking)** — 한 덩어리를 풀어 여러 이름에 나눠 묶는 것.\
> `a, b = (1, 2)` 가 그것이고, **오른쪽이 이터러블이기만 하면** 튜플이 아니어도 된다.

## 이 주제가 답하려는 질문

1. **무엇이 튜플을 만드는가** — 괄호인가 쉼표인가, 그리고 한 원소짜리는 왜 특별한가.
2. **언패킹은 언제 어떤 예외를 내는가** — 「너무 많다」와 「모자란다」가 어떻게 갈리는가.
3. **`*` 는 자리마다 다른 일을 하는가** — 대입 왼쪽·호출 인자·리터럴 안에서 각각 무엇인가.

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 문장으로 읽는다.

### 1. ★ 쉼표가 튜플을 만든다

**언제 쓰나** — 값 하나를 튜플로 감싸야 할 때마다. 여기서 가장 자주 틀린다.

```python
for src in ("(1)", "(1,)", "1,", "1, 2", "()"):
    v = eval(src)
    print(f"{src:8} -> {v!r:10} {type(v).__name__}")
try:
    len((1))
except TypeError as e:
    print("len((1))  ->", type(e).__name__, e)
print("len((1,)) ->", len((1,)))
x = 1,
print("x = 1,    ->", repr(x), type(x).__name__)
print("((1)) =", repr(((1))), "| ((1,)) =", repr(((1,))))
```

```text
(1)      -> 1          int
(1,)     -> (1,)       tuple
1,       -> (1,)       tuple
1, 2     -> (1, 2)     tuple
()       -> ()         tuple
len((1))  -> TypeError object of type 'int' has no len()
len((1,)) -> 1
x = 1,    -> (1,) tuple
((1)) = 1 | ((1,)) = (1,)
```

그림 해설.

- **`(1)` 은 그냥 `1`** 이다. 괄호를 아무리 겹쳐도(`((1))`) 정수다.
- **쉼표 하나가 타입을 바꾼다.** `1,` 은 괄호 없이도 튜플이다.
- ★ **`()` 만 예외**다 — 쉼표를 놓을 자리가 없으니 괄호가 필수다. 문서가 그 예외를 직접 적는다.
- `return 1,` 도 **튜플을 돌려준다.** 쉼표 하나를 흘려 적으면 반환 타입이 바뀐다.

**★ 호출의 쉼표는 튜플이 아니다**

```python
def g(*a): return a
print("g(1)    ->", g(1))
print("g(1,)   ->", g(1,))
print("g((1,)) ->", g((1,)))
print("g(1, 2) ->", g(1, 2))
```

```text
g(1)    -> (1,)
g(1,)   -> (1,)
g((1,)) -> ((1,),)
g(1, 2) -> (1, 2)
```

★ **`g(1,)` 의 쉼표는 「꼬리 쉼표」라 무시된다** — 인자 하나다.
같은 쉼표가 **대입에서는 튜플을 만들고 호출에서는 안 만든다.** 문법이 다른 자리다.

**비용** — 쉼표 하나로 묶을 수 있어 `return a, b` 가 자연스럽다.\
대신 **쉼표를 잘못 흘리면 타입이 조용히 바뀐다.**

### 2. ★ 언패킹이 실패하는 두 가지 메시지

**언제 쓰나** — `a, b = ...` 를 쓸 때마다. 오른쪽 길이가 데이터에 달렸으면 반드시.

```text
 a, b = (1, 2, 3)     너무 많다  -> ValueError: too many values to unpack (expected 2)
 a, b, c = (1, 2)     모자란다   -> ValueError: not enough values to unpack (expected 3, got 2)
 a, b = 5             풀 수가 없다 -> TypeError: cannot unpack non-iterable int object

 ★ "몇 개를 받았나" 는 모자랄 때만 알려 준다 (got 2).
   너무 많을 때는 몇 개였는지 안 알려 준다 — 다 세어 보기 전에 멈추기 때문이다.
```

```python
for src in ("a, b = (1, 2, 3)", "a, b, c = (1, 2)", "a, b = (1,)",
            "a, b, *r = (1,)", "a, *r, b = ()", "a, b = 5",
            "a, b = 'xyz'", "a, b = None"):
    try:
        exec(src)
        print(f"{src:20} -> OK")
    except (ValueError, TypeError) as e:
        print(f"{src:20} -> {type(e).__name__}: {e}")
```

```text
a, b = (1, 2, 3)     -> ValueError: too many values to unpack (expected 2)
a, b, c = (1, 2)     -> ValueError: not enough values to unpack (expected 3, got 2)
a, b = (1,)          -> ValueError: not enough values to unpack (expected 2, got 1)
a, b, *r = (1,)      -> ValueError: not enough values to unpack (expected at least 2, got 1)
a, *r, b = ()        -> ValueError: not enough values to unpack (expected at least 2, got 0)
a, b = 5             -> TypeError: cannot unpack non-iterable int object
a, b = 'xyz'         -> ValueError: too many values to unpack (expected 2)
a, b = None          -> TypeError: cannot unpack non-iterable NoneType object
```

그림 해설.

- **`ValueError` 는 「개수가 안 맞는다」, `TypeError` 는 「풀 수가 없다」다**. 두 층이 다르다.
- ★ **별표가 있으면 `expected at least N`** 으로 바뀐다 — 「최소 몇 개」로 문구가 달라진다.
- ★ **`a, b = 'xyz'` 가 `TypeError` 가 아니다.** 문자열은 이터러블이라 풀리긴 하고, 개수만 안 맞는다.
- **`None` 은 `TypeError`** 다 — 「데이터가 없을 때」의 대표 사고가 여기서 난다.

문서가 규칙을 직접 정의한다 —
*"If the target list contains one target prefixed with an asterisk, called a "starred" target:
**The object must be an iterable with at least as many items as there are targets in the target list, minus one.**"*

**비용** — 길이가 맞는지 언어가 대신 검사해 준다(리스트 인덱싱과 달리 **조용히 넘어가지 않는다**).\
대신 데이터 길이가 들쭉날쭉하면 **실행 중에 터진다.**

### 3. ★ 별표가 받는 것은 언제나 `list` 다

**언제 쓰나** — 「앞의 둘과 나머지」처럼 개수가 정해지지 않은 것을 풀 때.

```text
 a, *rest = [1, 2, 3, 4]

   [ 1 | 2 | 3 | 4 ]
     ^   \_______/
     a      rest        rest = [2, 3, 4]   <- 리스트다

 *init, last = [1, 2, 3, 4]      init=[1,2,3]  last=4
 first, *mid, last = [...]       가운데를 봉지에
 a, *r = [1]                     r = []        <- 빈 리스트. 에러가 아니다
```

```python
a, *rest = [1, 2, 3, 4]
print("a, *rest = [1,2,3,4] ->", a, rest, type(rest).__name__)
*init, last = [1, 2, 3, 4]
print("*init, last          ->", init, last)
first, *mid, last = [1, 2, 3, 4]
print("first, *mid, last    ->", first, mid, last)
a, *r = [1]
print("a, *r = [1]          ->", a, r, " <- 빈 리스트")
a, *r = "hi"
print("a, *r = 'hi'         ->", a, r)
a, *r = (1, 2, 3)
print("a, *r = (1,2,3)      ->", a, r, type(r).__name__, " <- 원본이 튜플이어도 list")
a, *r = range(3)
print("a, *r = range(3)     ->", a, r)
a, *r = {"k": 1, "j": 2}
print("a, *r = dict         ->", a, r, " <- 키만")
```

```text
a, *rest = [1,2,3,4] -> 1 [2, 3, 4] list
*init, last          -> [1, 2, 3] 4
first, *mid, last    -> 1 [2, 3] 4
a, *r = [1]          -> 1 []  <- 빈 리스트
a, *r = 'hi'         -> h ['i']
a, *r = (1,2,3)      -> 1 [2, 3] list  <- 원본이 튜플이어도 list
a, *r = range(3)     -> 0 [1, 2]
a, *r = dict         -> k ['j']  <- 키만
```

★ **원본이 무엇이든 봉지는 `list`** 다. 문서가 *"A **list** of the remaining items in the iterable is then assigned to the starred target"* 라고 적는다.
튜플이 필요하면 `tuple(rest)` 로 직접 바꾼다.

**★ 별표는 한 번만**

```python
for src in ("a, *b, *c = [1,2,3]", "*a, *b = [1,2]", "a, *b = [1,2]"):
    try:
        exec(src)
        print(f"{src:22} -> OK")
    except SyntaxError as e:
        print(f"{src:22} -> SyntaxError: {e.msg}")
```

```text
a, *b, *c = [1,2,3]    -> SyntaxError: multiple starred expressions in assignment
*a, *b = [1,2]         -> SyntaxError: multiple starred expressions in assignment
a, *b = [1,2]          -> OK
```

★ **`SyntaxError` 다 — 실행 전에 걸린다.** 봉지가 둘이면 어디까지가 어느 봉지인지 정할 수 없기 때문이다.

**중첩 언패킹과 `_` 관용**

```python
(a, (b, c)) = (1, (2, 3))
print("(a,(b,c)) = (1,(2,3)) ->", a, b, c)
[a, [b, c]] = (1, [2, 3])
print("[a,[b,c]] = (1,[2,3]) ->", a, b, c, " <- 대괄호로 써도 된다")
name, _, score = ("김", "무시", 90)
print("name, _, score        ->", name, score, "| _ =", _)
head, *_, tail = [1, 2, 3, 4, 5]
print("head, *_, tail        ->", head, tail, "| _ =", _)
for k, (i, j) in [("x", (1, 2))]:
    print("for k,(i,j) in ...    ->", k, i, j)
```

```text
(a,(b,c)) = (1,(2,3)) -> 1 2 3
[a,[b,c]] = (1,[2,3]) -> 1 2 3  <- 대괄호로 써도 된다
name, _, score        -> 김 90 | _ = 무시
head, *_, tail        -> 1 5 | _ = [2, 3, 4]
for k,(i,j) in ...    -> x 1 2
```

★ **`_` 는 문법이 아니라 관용**이다 — 평범한 이름이라 값이 실제로 들어간다.
`*_` 로 쓰면 **리스트가 통째로 메모리에 올라간다**(큰 데이터면 의미가 있다).

**비용** — 인덱스를 세지 않아도 되어 읽기가 낫다.\
대신 **개수가 데이터에 달렸으면 실행 중에 터진다.**

### 4. ★ `*` 는 자리마다 다른 일을 한다

**언제 쓰나** — 함수에 인자를 넘길 때, 시그니처를 쓸 때, 리터럴을 조립할 때.

```text
  ┌ 대입 왼쪽 ─ a, *rest = x        "모은다"   rest 는 list.  한 번만
  ├ 시그니처 ── def f(*args)        "모은다"   args 는 tuple
  ├ 호출 인자 ── f(*seq)            "푼다"     여러 번 써도 된다
  └ 리터럴 안 ── [*a, *b] {**d1, **d2}  "푼다"  3.5+ (PEP 448)
```

```python
def show(a, b, c=0, **kw):
    return f"a={a} b={b} c={c} kw={kw}"
def gather(*a, **kw):
    return a, kw

args = (1, 2)
print("show(*args)           :", show(*args))
print("show(*args, 3)        :", show(*args, 3))
print("show(*'xy')           :", show(*"xy"))
print("show(**{'a':1,'b':2}) :", show(**{"a": 1, "b": 2}))
print("gather(1,2,k=3)       :", gather(1, 2, k=3), " <- a 는 tuple, kw 는 dict")
print("gather(*[1],*[2],*[3]):", gather(*[1], *[2], *[3]), " <- 호출에서는 여러 번 OK")
try:
    show(**{1: 2})
except TypeError as e:
    print("show(**{1:2})         -> TypeError:", e)
try:
    show(*1)
except TypeError as e:
    print("show(*1)              -> TypeError:", e)
```

```text
show(*args)           : a=1 b=2 c=0 kw={}
show(*args, 3)        : a=1 b=2 c=3 kw={}
show(*'xy')           : a=x b=y c=0 kw={}
show(**{'a':1,'b':2}) : a=1 b=2 c=0 kw={}
gather(1,2,k=3)       : ((1, 2), {'k': 3})  <- a 는 tuple, kw 는 dict
gather(*[1],*[2],*[3]): ((1, 2, 3), {})  <- 호출에서는 여러 번 OK
show(**{1:2})         -> TypeError: keywords must be strings
show(*1)              -> TypeError: __main__.show() argument after * must be an iterable, not int
```

★ **대입 왼쪽에서는 `*` 가 한 번뿐인데 호출에서는 여러 번 된다.** 같은 기호가 다른 규칙을 따른다.\
★ **모으는 쪽은 `tuple`, 푸는 쪽에서 남는 쪽은 `list`** 다 — `def f(*args)` 의 `args` 는 튜플, `a, *rest = x` 의 `rest` 는 리스트.

**리터럴 안의 `*` (PEP 448, 3.5+)**

```python
t = (1, 2)
print("[*t, 3] =", [*t, 3], "| (*t, 3) =", (*t, 3), "| {*t, 3} =", {*t, 3})
print("{**{'a':1}, 'b':2} =", {**{"a": 1}, "b": 2})
print("[*'ab'] =", [*"ab"])
```

```text
[*t, 3] = [1, 2, 3] | (*t, 3) = (1, 2, 3) | {*t, 3} = {1, 2, 3}
{**{'a':1}, 'b':2} = {'a': 1, 'b': 2}
[*'ab'] = ['a', 'b']
```

**비용** — 시퀀스를 그대로 인자로 흘려 보낼 수 있어 래퍼 함수가 짧아진다.\
대신 **`*` 앞의 것이 이터러블이 아니면 호출 시점에 터진다.**

### 5. ★ 스왑과 상수 튜플 — 컴파일러가 하는 일

**언제 쓰나** — `a, b = b, a` 를 쓸 때. 그리고 「튜플 만드는 비용」을 생각할 때.

스왑이 되는 이유(오른쪽을 먼저 다 평가한다)는 [01번](../01-object-and-name-binding/2-summary.md)이 정본이다. 여기서는 **그다음**을 본다.

```python
import dis
dis.dis(compile("a, b = b, a", "<2>", "exec"))
print("----- 네 개면")
dis.dis(compile("a, b, c, d = d, c, b, a", "<4>", "exec"))
```

```text
  0           0 RESUME                   0

  1           2 LOAD_NAME                0 (b)
              4 LOAD_NAME                1 (a)
              6 SWAP                     2
              8 STORE_NAME               1 (a)
             10 STORE_NAME               0 (b)
             12 RETURN_CONST             0 (None)
----- 네 개면
  0           0 RESUME                   0

  1           2 LOAD_NAME                0 (d)
              4 LOAD_NAME                1 (c)
              6 LOAD_NAME                2 (b)
              8 LOAD_NAME                3 (a)
             10 BUILD_TUPLE              4
             12 UNPACK_SEQUENCE          4
             16 STORE_NAME               3 (a)
             18 STORE_NAME               2 (b)
             20 STORE_NAME               1 (c)
             22 STORE_NAME               0 (d)
             24 RETURN_CONST             0 (None)
```

★ **두 개·세 개는 `SWAP` 으로 끝나고 튜플을 안 만든다. 네 개부터 `BUILD_TUPLE` 이 나온다.**
「스왑은 튜플을 만들었다 푼다」는 설명은 **작은 개수에서는 사실이 아니다** — 다만 이것은 **구현의 최적화**이지 보장이 아니다.

**상수 튜플은 컴파일 때 통째로 만들어진다**

```python
import dis
dis.dis(compile("x = (1, 2, 3)", "<const>", "exec"))
print("----- 안에 변수가 있으면")
dis.dis(compile("x = (1, a, 3)", "<var>", "exec"))
```

```text
  0           0 RESUME                   0

  1           2 LOAD_CONST               0 ((1, 2, 3))
              4 STORE_NAME               0 (x)
              6 RETURN_CONST             1 (None)
----- 안에 변수가 있으면
  0           0 RESUME                   0

  1           2 LOAD_CONST               0 (1)
              4 LOAD_NAME                0 (a)
              6 LOAD_CONST               1 (3)
              8 BUILD_TUPLE              3
             10 STORE_NAME               1 (x)
             12 RETURN_CONST             2 (None)
```

```python
def f():
    a = (1, 2, 3)
    b = (1, 2, 3)
    return a is b
print("함수 안 (1,2,3) is (1,2,3) :", f())
print("co_consts                 :", f.__code__.co_consts)
```

```text
함수 안 (1,2,3) is (1,2,3) : True
co_consts                 : (None, (1, 2, 3))
```

★ **같은 코드 객체 안의 같은 상수 튜플은 한 객체**다 — [02번](../02-is-vs-eq-interning/2-summary.md)의 **기계 ①**(컴파일 단위 상수 합치기)이 튜플에도 걸린다.
**이것은 구현이지 보장이 아니다.**

**비용** — 상수뿐인 튜플은 **실행 중에 만들지 않는다.**\
안에 변수가 하나라도 있으면 매번 `BUILD_TUPLE` 이다.

### 6. `tuple()` 은 이미 튜플이면 그대로 돌려준다

**언제 쓰나** — 「튜플로 만들어 둔다」를 방어적으로 쓸 때.

문서 — *"If iterable is already a tuple, **it is returned unchanged**."*

```python
import sys
t0 = (1, 2)
print("tuple(t0) is t0 :", tuple(t0) is t0, " <- 문서가 약속한다")
print("t0[:] is t0     :", t0[:] is t0, " <- 구현 세부사항")
print("list(t0) is t0  :", list(t0) is t0)
print("getsizeof (1,2,3) =", sys.getsizeof((1, 2, 3)), "| [1,2,3] =", sys.getsizeof([1, 2, 3]))
print("getsizeof ()      =", sys.getsizeof(()), "| [] =", sys.getsizeof([]))
```

```text
tuple(t0) is t0 : True  <- 문서가 약속한다
t0[:] is t0     : True  <- 구현 세부사항
list(t0) is t0  : False
getsizeof (1,2,3) = 64 | [1,2,3] = 88
getsizeof ()      = 40 | [] = 56
```

★ **`tuple(t) is t` 는 문서에 있고 `t[:] is t` 는 없다.** 겉보기가 같은 두 사실이 다른 층이다
([09번](../09-sequence-ops-and-slicing/2-summary.md)이 `[:]` 쪽을 정본으로 다룬다 — `range` 가 반례다).

### 7. 불변인데 안의 가변은 바뀐다 — 결론만

**정본은 [03번](../03-mutability-and-copying/2-summary.md)이다.** 여기서는 결론과 튜플 쪽 결과만 둔다.

```python
t = (1, [2, 3])
t[1].append(4)
print("t[1].append(4) ->", t)
try:
    t[0] = 9
except TypeError as e:
    print("t[0] = 9       ->", type(e).__name__, e)
try:
    hash(t)
except TypeError as e:
    print("hash(t)        ->", type(e).__name__, e)
```

```text
t[1].append(4) -> (1, [2, 3, 4])
t[0] = 9       -> TypeError 'tuple' object does not support item assignment
hash(t)        -> TypeError unhashable type: 'list'
```

- **튜플이 지키는 것은 「어느 칸이 어느 객체를 가리키나」뿐**이다. 그 객체 안까지는 안 지킨다.
- ★ **그래서 「불변이다」와 「해시 가능하다」가 다른 말**이다 — 뒤엣것은 **내용에 달렸다**([12번](../12-dict-and-key-requirements/2-summary.md)).
- `t[0] += [1]` 이 **에러를 내면서도 값을 바꾸는** 것은 [03번](../03-mutability-and-copying/2-summary.md)이 정본이다.

### 8. `namedtuple` 과 `NamedTuple` — 존재와 「튜플인가」

**언제 쓰나** — 자리 번호 대신 이름으로 읽고 싶을 때. 둘 다 **진짜 튜플**이다.

```python
from collections import namedtuple
from typing import NamedTuple

Point = namedtuple("Point", "x y")
class TPoint(NamedTuple):
    x: int
    y: int

p, q = Point(1, 2), TPoint(1, 2)
for n, v in (("namedtuple", p), ("NamedTuple", q)):
    print(f"{n:11} {v!r:18} isinstance tuple: {isinstance(v, tuple)}  MRO: {[c.__name__ for c in type(v).__mro__]}")
print("평범한 튜플과 ==   :", p == (1, 2), q == (1, 2), p == q)
print("해시도 같다        :", hash(p) == hash((1, 2)) == hash(q))
print("집합에 셋 다 넣으면 :", {p, q, (1, 2)})
print("인덱스도 이름도    :", p[0], p.x, p[:1])
print("_asdict / _replace :", p._asdict(), p._replace(x=9))
print("어노테이션은 강제 아님:", TPoint("문자열", None))
```

```text
namedtuple  Point(x=1, y=2)   isinstance tuple: True  MRO: ['Point', 'tuple', 'object']
NamedTuple  TPoint(x=1, y=2)  isinstance tuple: True  MRO: ['TPoint', 'tuple', 'object']
평범한 튜플과 ==   : True True True
해시도 같다        : True
집합에 셋 다 넣으면 : {Point(x=1, y=2)}
인덱스도 이름도    : 1 1 (1,)
_asdict / _replace : {'x': 1, 'y': 2} Point(x=9, y=2)
어노테이션은 강제 아님: TPoint(x='문자열', y=None)
```

★ **세 개를 집합에 넣었더니 하나가 됐다.** `Point(1,2)` 와 `TPoint(1,2)` 와 `(1,2)` 가 **같은 원소**다 —
`==` 도 `hash` 도 튜플의 것을 그대로 쓰기 때문이다([12번](../12-dict-and-key-requirements/2-summary.md)·[13번](../13-set-and-frozenset/2-summary.md)).

- **둘 다 `tuple` 의 서브클래스**다. 언패킹·인덱싱·슬라이싱이 그대로 된다.
- **타입은 다르다**(`Point` 와 `TPoint`) 지만 **값은 같다.**
- **어노테이션은 런타임에 강제되지 않는다** — `TPoint("문자열", None)` 이 그냥 만들어진다(목록의 **40번 주제**).
- 셋 중 무엇을 고를지는 목록의 **38번 주제**가 정본이다. 여기서는 **「튜플인가」까지**다.

## 문법 — 형태와 규칙

```python
()            # 빈 튜플 — 괄호가 필수
(1,)   1,     # 한 원소 — 쉼표가 필수
(1, 2) 1, 2   # 여러 원소 — 괄호는 선택
tuple(iterable)          # 이미 튜플이면 그대로 돌려준다

a, b = t                 # 개수가 정확히 맞아야 한다
a, *rest = t             # rest 는 list. 별표는 한 번만
(a, (b, c)) = t          # 중첩
a, b = b, a              # 스왑 — 오른쪽을 먼저 평가한다(01번)

def f(*args, **kw): ...  # 모으는 쪽 — args 는 tuple, kw 는 dict
f(*seq, **mapping)       # 푸는 쪽 — 여러 번 써도 된다
[*a, *b]  (*a, *b)  {*a, *b}  {**d1, **d2}   # 리터럴 안 (3.5+)
```

- **튜플 비교는 앞에서부터**다 — 첫 칸이 같으면 다음 칸을 본다. 그래서 **정렬 키**로 쓸 수 있다([10번](../10-list-methods-and-sort-key/2-summary.md)).

```python
print((1, 2) < (1, 3), (1, 2) < (2, 0), (1,) < (1, 0), (1, 2) == (1, 2))
try:
    (1, "a") < (1, 2)
except TypeError as e:
    print("(1,'a') < (1,2) ->", type(e).__name__, e)
print("정렬 키로 :", sorted([("b", 1), ("a", 2), ("a", 1)]))
```

```text
True True True True
(1,'a') < (1,2) -> TypeError '<' not supported between instances of 'str' and 'int'
정렬 키로 : [('a', 1), ('a', 2), ('b', 1)]
```

★ **첫 칸이 다르면 뒤는 안 본다.** `(1, "a") < (2, 0)` 은 되지만 `(1, "a") < (1, 2)` 는 터진다.

## 어디서 틀리나

### (1) 한 원소 튜플에 쉼표를 빼먹는다

`("Content-Type")` 은 문자열이다. `for h in headers:` 가 **글자를 하나씩** 돌아도 에러가 안 난다.\
고치는 법: `("Content-Type",)`. 리뷰에서 **쉼표 하나를 보는 습관**이 이 주제의 값이다.

### (2) 쉼표를 흘려 적어 반환 타입이 바뀐다

`return result,` 는 `(result,)` 를 돌려준다. 호출한 쪽이 `len()` 을 재면 언제나 1이다.

### (3) 괄호가 튜플을 만든다고 믿는다

`(1)` 은 `int` 다. **빈 튜플만 괄호가 만든다.**

### (4) 언패킹 길이를 데이터에 맡긴다

`a, b = line.split(",")` 는 줄에 쉼표가 둘이면 `too many values to unpack` 이다.\
고치는 법: `a, *rest = ...` 또는 `line.split(",", 1)`.

### (5) `None` 을 언패킹한다

「데이터가 없을 때」의 대표 사고다 — `TypeError: cannot unpack non-iterable NoneType object`.\
고치는 법: 함수가 실패 시 `None` 대신 **빈 튜플**을 돌려주게 하거나, 언패킹 전에 확인한다.

### (6) 별표 봉지를 튜플로 안다

`a, *rest = t` 의 `rest` 는 **`list`** 다. 딕셔너리 키로 쓰려다 `unhashable type: 'list'` 가 난다([12번](../12-dict-and-key-requirements/2-summary.md)).

### (7) 「튜플이니 해시된다」로 믿는다

**내용에 달렸다.** 안에 리스트가 하나라도 있으면 `unhashable type: 'list'` 다 — 그리고 **오류가 `tuple` 이 아니라 `list` 를 가리킨다**([03번](../03-mutability-and-copying/2-summary.md)).

### (8) 「튜플로 감쌌으니 안전하다」

안의 리스트는 그대로 바뀐다([03번](../03-mutability-and-copying/2-summary.md)).

### (9) `_` 가 값을 안 받는다고 믿는다

평범한 이름이다. `*_` 는 **리스트를 통째로** 만든다.

### (10) 호출의 `*` 와 대입의 `*` 를 같은 규칙으로 본다

호출에서는 여러 번 되고 대입에서는 **`SyntaxError`** 다.

## 구현 세부사항 대 언어 보장

세 층으로 가른다. ★ **이 주제는 문법 규칙이라 「언어 보장」이 가장 두껍다.**
관찰 층은 **바이트코드 명령 이름**과 **상수 합치기**, **`getsizeof`** 셋이다.

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **언어 보장** | 언어 레퍼런스·라이브러리 레퍼런스가 정한 것 | 공식 문서 문장을 열어서 인용 |
| **CPython 구현** | 이 구현이 그렇게 하는 것 | `dis`·`is` 로 확인 |
| **이 판·이 머신의 관찰** | 3.12.3 에서 그랬을 뿐 | 「관찰」로 명기 |

### 언어 보장

| 사실 | 근거 |
|---|---|
| **괄호가 아니라 쉼표가 튜플을 만든다.** 빈 튜플만 괄호가 필수 | 6.2.3 Parenthesized forms |
| 쉼표가 하나라도 있는 식 목록은 튜플을 낸다 · **한 원소 튜플에는 꼬리 쉼표가 필수** | 6.15 Expression lists |
| 별표 대상은 **「대상 수 − 1」개 이상**을 요구하고, 남은 것을 **`list`** 로 받는다 | 7.2 Assignment statements |
| 별표 없는 대상 목록은 **개수가 정확히 같아야** 한다 | 〃 |
| 대입은 **오른쪽을 먼저 평가**하고 왼쪽을 **왼쪽부터** 묶는다 | 6.16 Evaluation order · 7.2 |
| **`tuple(t)` 는 `t` 가 이미 튜플이면 그대로 돌려준다** | Tuples |
| 빈 튜플이 **같은 객체일 수도 아닐 수도 있다** | 6.2.3 (*"may or may not yield the same object"*) |
| 리터럴·호출 안의 `*`/`**` 확장은 **3.5(PEP 448)** | 6.15 |
| `namedtuple`·`NamedTuple` 은 **`tuple` 의 서브클래스** | collections · typing |

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| **2·3개 스왑은 `SWAP`, 4개부터 `BUILD_TUPLE`+`UNPACK_SEQUENCE`** | `dis` |
| 상수뿐인 튜플은 **`LOAD_CONST` 한 번**으로 끝난다 | `dis` · `co_consts` |
| 같은 코드 객체 안의 같은 상수 튜플이 **한 객체** | `a is b` 가 `True` |
| **`t[:] is t`** 가 참 | 문서에 없다. `range` 는 반례([09번](../09-sequence-ops-and-slicing/2-summary.md)) |
| 예외 문구(`too many values to unpack (expected 2)` 등) | 실행 |

### 이 판(3.12.3)·이 머신의 관찰

| 관찰 | 어디가 흔들리나 |
|---|---|
| `getsizeof((1,2,3))`=64 · `[1,2,3]`=88 · `()`=40 · `[]`=56 | 빌드·비트 폭에 달렸다 |
| `UNPACK_EX`·`SWAP`·`BUILD_TUPLE` 같은 명령 이름 | 판마다 바뀐다 |
| `SyntaxError` 문구(`multiple starred expressions in assignment`) | 문구는 판마다 바뀐다 |
| `namedtuple` 과 `tuple` 의 `getsizeof` 가 둘 다 56 | 구현 몫이다 |

### 그래서 이렇게 적으면 틀린다

- ✗ 「괄호가 튜플을 만든다」\
  ○ **쉼표**가 만든다. 문서가 *"tuples are not formed by the parentheses"* 라고 적는다. **빈 튜플만 예외**다.
- ✗ 「`(1)` 은 한 원소 튜플이다」\
  ○ `int` 다. `len((1))` 이 `TypeError` 다.
- ✗ 「언패킹 실패는 언제나 `ValueError` 다」\
  ○ **이터러블이 아니면 `TypeError`** 다(`None`·`int`). 문자열은 `ValueError` 쪽이다.
- ✗ 「`a, *rest = t` 의 `rest` 는 튜플이다」\
  ○ **`list`** 다. 문서가 그렇게 정한다.
- ✗ 「`*` 는 어디서나 여러 번 쓸 수 있다」\
  ○ **대입 왼쪽에서는 한 번**뿐이고 `SyntaxError` 다. 호출에서는 여러 번 된다.
- ✗ 「스왑은 튜플을 만들었다가 푼다」\
  ○ 2·3개는 **`SWAP`** 으로 끝난다(구현). 4개부터 튜플을 만든다.
- ✗ 「튜플이니까 딕셔너리 키가 된다」\
  ○ **내용이 전부 해시 가능해야** 한다([12번](../12-dict-and-key-requirements/2-summary.md)).
- ✗ 「튜플로 감쌌으니 안 바뀐다」\
  ○ 안의 리스트는 바뀐다([03번](../03-mutability-and-copying/2-summary.md)).

**판정 기준 한 줄**: 괄호가 보이면 **안에 쉼표가 있는지**부터 보라. 그것이 타입을 정한다.

## 언제 쓰고 언제 안 쓰나

| 쓰는 것 | 상황 |
|---|---|
| `(x,)` | 원소 하나짜리 튜플. **쉼표를 반드시** |
| `a, b = f()` | 함수가 값 둘을 돌려줄 때 |
| `a, *rest = x` | 앞 몇 개만 이름을 주고 나머지는 봉지로 |
| `*init, last = x` | 마지막 것만 따로 |
| `a, b = b, a` | 스왑. 임시 변수가 필요 없다 |
| `for k, (i, j) in ...` | 중첩된 구조를 풀며 돌 때 |
| `_` · `*_` | 안 쓸 자리를 표시할 때(**값은 들어간다**) |
| `f(*seq)` · `f(**mapping)` | 인자를 통째로 흘려 보낼 때 |
| `def f(*args, **kw)` | 받는 쪽에서 모을 때 |
| `[*a, *b]` · `{**d1, **d2}` | 리터럴을 조립할 때(3.5+) |
| `namedtuple`·`NamedTuple` | 자리 번호 대신 이름으로 읽고 싶을 때 |
| `tuple(lst)` | 해시 가능하게 얼릴 때([12번](../12-dict-and-key-requirements/2-summary.md)) |

**안 쓰는 자리**는 넷이다.\
**길이를 모르는 데이터를 고정 개수로 언패킹하지 마라** — `ValueError` 로 터진다.\
**실패 시 `None` 을 돌려주는 함수를 바로 언패킹하지 마라.**\
**별표 봉지를 딕셔너리 키로 쓰지 마라** — `list` 다.\
**「튜플이니 안전하다」로 방어 설계를 세우지 마라** — 안의 가변은 그대로다.

## 핵심 문장

- **튜플을 만드는 것은 쉼표다.** 괄호는 묶어 읽으라는 표시고, **빈 튜플만 괄호가 필수**다.
- `(1)` 은 `int`, `(1,)` 은 `tuple`. **쉼표 하나가 타입을 바꾼다.**
- **언패킹 실패는 두 메시지**다 — `too many values`(너무 많다)와 `not enough values ... got N`(모자란다).
  이터러블이 아니면 아예 **`TypeError`** 다.
- **별표는 대입 왼쪽에서 한 번뿐이고 봉지는 언제나 `list`** 다. 호출의 `*` 는 규칙이 다르다 — 여러 번 된다.
- **모으는 쪽은 `tuple`, 대입에서 남는 쪽은 `list`.** 같은 기호가 자리마다 다른 것을 만든다.
- **2·3개 스왑은 튜플을 안 만든다**(구현). 상수뿐인 튜플은 **컴파일 때** 만들어진다.
- **`tuple(t) is t` 는 문서에 있고 `t[:] is t` 는 없다.** 겉이 같아도 층이 다르다.
- **`namedtuple`·`NamedTuple` 은 진짜 튜플**이다 — `(1, 2)` 와 `==` 도 `hash` 도 같아 **집합에서 한 원소**가 된다.

## 관련 자료

- 목록: [python/syntax 주제 목록](../README.md) — 이 주제는 **11번**
- 선행: [01-object-and-name-binding](../01-object-and-name-binding/2-summary.md) — **스왑의 `dis` 와 「오른쪽 먼저」의 정본.**
- 선행: [09-sequence-ops-and-slicing](../09-sequence-ops-and-slicing/2-summary.md) — 시퀀스 공통 연산·`t[:]`·`t += (3,)` 의 정본.
- 선행: [03-mutability-and-copying](../03-mutability-and-copying/2-summary.md) — **불변 안의 가변과 `t[0] += [1]` 의 정본.**
- 선행: [02-is-vs-eq-interning](../02-is-vs-eq-interning/2-summary.md) — 컴파일 단위 상수 합치기(기계 ①).
- 이어지는 곳: [12-dict-and-key-requirements](../12-dict-and-key-requirements/2-summary.md) — 튜플이 **키가 되는 조건**.
- 이어지는 곳: [13-set-and-frozenset](../13-set-and-frozenset/2-summary.md) — 「같은 값이면 한 원소」.
- 이어지는 곳: [10-list-methods-and-sort-key](../10-list-methods-and-sort-key/2-summary.md) — 튜플을 **정렬 키**로 쓰는 법.
- 이어지는 곳: [목록의 **19번 주제**](../19-function-argument-rules/) 「함수 인자 규칙」 — `*`/`**`·`/`·키워드 전용 인자의 정본.
- 이어지는 곳: 목록의 **38번 주제** 「`namedtuple`·`NamedTuple`·`TypedDict`」 — **셋 중 무엇을 고르나**는 그쪽.
- 이어지는 곳: 목록의 **39번 주제** 「`match` 문」 — 시퀀스 패턴이 언패킹과 닮았지만 **소문자 이름이 캡처**가 되는 것.
- 이어지는 곳: 목록의 **40번 주제** 「타입 힌트의 런타임 의미」 — `NamedTuple` 의 어노테이션이 강제되지 않는 이유.
- 기존 노트: [`cs/foundations/python-basics/`](../../../../python-basics/) — 튜플을 「이렇게 쓴다」까지 다룬다.\
  **경계**: 그쪽은 사용 예시까지, 여기는 「**무엇이 튜플을 만들고 언패킹이 어떻게 실패하나**」부터다.
- 공식 문서: [Parenthesized forms](https://docs.python.org/3.12/reference/expressions.html#parenthesized-forms) · [Expression lists](https://docs.python.org/3.12/reference/expressions.html#expression-lists) · [Assignment statements](https://docs.python.org/3.12/reference/simple_stmts.html#assignment-statements) · [Tuples](https://docs.python.org/3.12/library/stdtypes.html#tuples)

## 용어 풀이

- **튜플(tuple)**: 불변 시퀀스. **쉼표로** 만든다. 내용이 전부 해시 가능하면 자기도 해시 가능하다.
- **언패킹(unpacking)**: 이터러블 하나를 풀어 여러 이름에 나눠 묶는 것. `a, b = t`.
- **별표 대상(starred target)**: `a, *rest = t` 의 `*rest`.\
  남은 것을 **`list`** 로 받고, 대상 목록에 **하나만** 올 수 있다.
- **반복 가능 객체 언패킹(iterable unpacking)**: 호출·리터럴 안의 `*`/`**`.\
  대입 왼쪽의 별표와 **규칙이 다르다** — 여러 번 쓸 수 있다.
- **꼬리 쉼표(trailing comma)**: 마지막 원소 뒤의 쉼표.\
  **한 원소 튜플에서만 의미가 있고** 나머지 자리에서는 선택이다. 함수 호출에서는 아무 뜻이 없다.
- **중첩 언패킹(nested unpacking)**: `(a, (b, c)) = ...` 처럼 구조를 따라 푸는 것. 대괄호로 써도 된다.
- **`namedtuple`**: 필드 이름이 붙은 튜플 서브클래스를 만들어 주는 팩토리(`collections`).
- **`NamedTuple`**: 같은 것을 클래스 문법으로 쓰게 해 주는 것(`typing`).\
  **어노테이션은 런타임에 강제되지 않는다.**

## 더 들어가면

- **`*args` 를 받는 함수에서 `args` 가 튜플인 이유**는 「호출마다 새로 만들어지는 불변 묶음」이 안전하기 때문이다 —
  가변이면 [20번](../20-mutable-default-args/2-summary.md)과 같은 종류의 사고가 난다.
- **`match` 문의 시퀀스 패턴**은 언패킹과 모양이 같지만 **소문자 이름이 비교가 아니라 캡처**다(목록의 **39번 주제**).
- **`typing.NamedTuple` 과 `dataclasses`** 중 무엇을 고를지는 목록의 **36·38번 주제**.
- **`operator.itemgetter`** 는 튜플 키를 만들어 준다([10번](../10-list-methods-and-sort-key/2-summary.md)).
- **`(x for x in ...)`** 은 튜플 컴프리헨션이 아니라 **제너레이터 표현식**이다([목록의 **15번 주제**](../15-generator-expressions-lazy-eval/)) —
  튜플이 필요하면 `tuple(x for x in ...)`.
