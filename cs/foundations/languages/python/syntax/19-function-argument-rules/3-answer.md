# python/syntax/19-function-argument-rules — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> [1-question.md](1-question.md)의 번호와 **1:1**로 대응한다. 질문 12개 = 답 12개.
>
> 이 파일의 모든 출력은 `python3` **3.12.3** 에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> 던지는 형태는 `python3 - <파일` 로 고정했다 — **실행 중 예외에는 소스 줄과 캐럿이 없고 `SyntaxError` 에는 있다**(전부는 아니다 — 2번 답).
> 단 **예외 문구·`__main__.` 접두·`co_flags` 값**은 구현에 달린 것이라 다른 판에서는 달라진다(11번 답).

## 정답

### 1. 한쪽은 프로그램이 안 뜨고 한쪽은 아무 일도 안 난다

**출력** — 첫 판.

```text
  File "<stdin>", line 4
    f(a=1, 2)
            ^
SyntaxError: positional argument follows keyword argument
```

둘째 판.

```text
여기는 찍힌다
끝까지 왔다
```

**왜 그런가**

★★ **첫 판에서 `여기까지는 찍힐까?` 가 안 찍혔다.** `print` 가 `if False:` **앞**에 있는데도 안 돌았다 —
**파일 전체가 컴파일에 실패해 한 줄도 실행되지 않았다.**\
둘째 판은 틀린 호출이 **실행되지 않아** 아무 일도 안 났다.

```text
   소스 파일 ──> ① 파서·컴파일러가 전부 읽는다 ──> ② 한 줄씩 실행한다
                    │                                 │
                    └ SyntaxError                     └ TypeError
                      (파일이 안 뜬다)                   (그 줄에 닿아야)
```

★ **한 문장** — 「**파서가 글자 배열만 보고 알 수 있느냐**」가 기준이다.

- `f(a=1, 2)` 는 **`f` 가 무엇인지 몰라도** 틀렸다고 알 수 있다. 키워드 뒤에 위치 인자가 오는 **배열 자체**가 금지다.
- `f(1, 2, 3, 4, 5)` 는 **`f` 라는 함수 객체를 봐야** 틀렸는지 안다. 그러려면 실행이 필요하다.

★★ **「정의는 `SyntaxError`, 호출은 `TypeError`」가 틀린 요약인 이유** — 바로 이 첫 판이 반례다.
`f(a=1, 2)` 는 **호출 자리**인데 `SyntaxError` 다.
층을 가르는 것은 **정의/호출**이 아니라 **파서가 보느냐 실행이 보느냐**다.

★ 실무적 결론 하나 — **`SyntaxError` 류는 정적 검사로 100% 잡히고 `TypeError` 류는 안 잡힌다.**
테스트가 안 지나가는 가지의 잘못된 호출은 **배포 뒤에** 터진다. 타입 체커가 필요해지는 이유가 정확히 여기다([목록의 **40번 주제**](../40-type-hints-at-runtime/)).

### 2. 여덟 개 전부 `SyntaxError` — 그런데 캐럿은 여섯 개만

**출력** — 여덟 개를 따로 던진 결과다.

```text
  File "<stdin>", line 1
    def f(a=1, b): pass
               ^
SyntaxError: parameter without a default follows parameter with a default
```

```text
  File "<stdin>", line 1
    def f(**kw, a): pass
                ^
SyntaxError: arguments cannot follow var-keyword argument
```

```text
  File "<stdin>", line 1
    def f(*a, *b): pass
              ^
SyntaxError: * argument may appear only once
```

```text
  File "<stdin>", line 1
    def f(*): pass
          ^
SyntaxError: named arguments must follow bare *
```

```text
  File "<stdin>", line 1
    def f(a, /, b, /): pass
                   ^
SyntaxError: / may appear only once
```

```text
  File "<stdin>", line 1
    def f(/, a): pass
          ^
SyntaxError: at least one argument must precede /
```

```text
  File "<stdin>", line 1
SyntaxError: duplicate argument 'a' in function definition
```

```text
  File "<stdin>", line 3
SyntaxError: keyword argument repeated: x
```

**왜 그런가**

★ **여덟 중 여섯은 소스 줄과 캐럿이 나오고 마지막 둘은 안 나온다.**

```text
   소스 글자 ──> 파서 ──────> AST ──> 심볼 테이블·컴파일 ──> 바이트코드
                   │                      │
                   │                      └ SyntaxError · 캐럿 없음
                   │                        · duplicate argument 'a'
                   │                        · keyword argument repeated: x
                   └ SyntaxError · 캐럿 있음
                     · parameter without a default follows ...
                     · / may appear only once ...
```

- **파서가 「이 자리에 이 토큰이 오면 안 된다」로 걸린 것**은 **그 자리를 정확히 안다** → 캐럿을 찍는다.
- ★ **「이름이 겹쳤다」는 토큰 하나만 봐서는 모른다.** 파라미터 목록을 **다 모아 비교해야** 알 수 있고,
  그 시점에는 이미 원래 위치 정보가 없어 **줄 번호만** 남는다.
- ★★ **둘 다 `SyntaxError` 이고 둘 다 실행 전에 걸린다** — 층 ①이 안에서 둘로 갈리는 것이지 층이 바뀌는 게 아니다.
  [18번](../18-loop-control-and-else/2-summary.md)의 `'break' outside loop` 도 **캐럿 없는 쪽**이다.

★ **`def f(*): pass` 의 문구가 무엇을 알려 주나** — *"named arguments must follow bare `*`"*.
**맨 `*` 뒤에는 이름 붙은 파라미터가 반드시 와야 한다**는 뜻이다.
즉 `*` 만 쓰는 목적이 「**여기부터 키워드 전용**」이므로, **그 뒤에 아무것도 없으면 아무 의미가 없어서** 금지한 것이다.
문구가 **규칙과 그 이유를 동시에** 말한다.

★ 여섯 문구를 규칙으로 되읽으면 이렇게 된다.

| 문구 | 규칙 |
|---|---|
| `parameter without a default follows parameter with a default` | 기본값은 **뒤에 몰려야** 한다(5번 답의 `__defaults__` 때문) |
| `arguments cannot follow var-keyword argument` | **`**kwargs` 가 맨 끝**이다 |
| `* argument may appear only once` | `*` 는 **한 번**뿐 |
| `named arguments must follow bare *` | 맨 `*` 뒤에는 **이름이 있어야** 한다 |
| `/ may appear only once` | `/` 도 **한 번**뿐 |
| `at least one argument must precede /` | `/` **앞에 최소 하나** 있어야 한다 |

### 3. 마지막 두 줄이 `/` 의 존재 이유다

**출력**

```text
def f(pos, /, both, *, kw)
  f(1, 2, kw=3)                      -> (1, 2, 3)
  f(1, both=2, kw=3)                 -> (1, 2, 3)
  f(1, 2, 3)                         -> TypeError: f() takes 2 positional arguments but 3 were given
  f(pos=1, both=2, kw=3)             -> TypeError: f() got some positional-only arguments passed as keyword arguments: 'pos'
  f(1, 2)                            -> TypeError: f() missing 1 required keyword-only argument: 'kw'
  f(1, 2, kw=3, extra=4)             -> TypeError: f() got an unexpected keyword argument 'extra'

def g(a, b=2, *args, **kwargs)
  g(1)                               -> (1, 2, (), {})
  g(1, 2, 3, x=9)                    -> (1, 2, (3,), {'x': 9})
  g(1, 1, b=2)                       -> TypeError: g() got multiple values for argument 'b'
  g(b=2)                             -> TypeError: g() missing 1 required positional argument: 'a'
  g(1, pos=0)                        -> (1, 2, (), {'pos': 0})

--- 같은 인자를 위치와 키워드로 동시에 ---
  h(1, x=2)                          -> TypeError: h() got multiple values for argument 'x'
  hp(1, x=2)  (x 가 위치 전용)            -> (1, {'x': 2})
```

**왜 그런가**

```text
   def h(x)             h(1, x=2)
                        ┌ 1 은 x 자리에 앉는다
                        └ 'x'=2 도 x 자리를 달라고 한다   -> 충돌 -> TypeError

   def hp(x, /, **kw)   hp(1, x=2)
                        ┌ 1 은 x 자리에 앉는다
                        └ 'x'=2 는 ★ x 자리를 못 노린다 (위치 전용이라 이름으로 못 준다)
                          -> 갈 곳이 kw 뿐이다 -> (1, {'x': 2})
```

★★ **`/` 는 「이름을 감추는」 장치가 아니라 「이름을 해방하는」 장치다.**
`x` 를 위치 전용으로 만들면 **`x` 라는 문자열이 파라미터 이름 공간에서 빠져나가** `**kwargs` 가 자유롭게 쓸 수 있다.
PEP 570 이 만들어진 이유이고, `dict.update(a=1)` 같은 표준 API 가 정확히 이 모양이다(8번 답).

★ **`g(1, pos=0)` 이 통과한 이유** — `g` 에 `pos` 라는 파라미터가 **없다.** 그래서 `kwargs` 로 들어간다.
**모르는 이름이 에러인지 아닌지는 `**kwargs` 의 유무가 정한다** — `f` 에는 없어서 `extra=4` 가 터졌고 `g` 에는 있어서 통과했다.

★ 나머지 문구를 규칙으로 되읽으면 이렇다.

| 문구 | 규칙 |
|---|---|
| `takes 2 positional arguments but 3 were given` | `*args` 가 없으면 **위치 자리가 상한**이다 |
| `got some positional-only arguments passed as keyword arguments: 'pos'` | `/` **왼쪽은 이름으로 못 준다** |
| `missing 1 required keyword-only argument: 'kw'` | `*` **오른쪽은 기본값이 없으면 필수**다 |
| `got an unexpected keyword argument 'extra'` | `**kwargs` 가 없으면 **모르는 이름은 거부** |
| `got multiple values for argument 'b'` | **한 자리에 두 번** 줬다 |
| `missing 1 required positional argument: 'a'` | 필수 위치를 안 줬다 |

### 4. 빈 것을 풀면 아무 일도 안 일어난다 — 그리고 접두가 층을 드러낸다

**출력**

```text
def f(a, b=2, *args, kw='K', **kwargs)
  f(*[], **{})                           -> TypeError: f() missing 1 required positional argument: 'a'
  f(1, *[], **{})                        -> (1, 2, (), 'K', {})
  f(*[1, 2, 3], **{'kw': 'X'})           -> (1, 2, (3,), 'X', {})
  f(*'ab')                               -> ('a', 'b', (), 'K', {})
  f(*range(2), *range(2))                -> (0, 1, (0, 1), 'K', {})
  f(1, **{'b': 9}, **{'z': 0})           -> (1, 9, (), 'K', {'z': 0})
  f(1, **{'b': 9}, **{'b': 8})           -> TypeError: __main__.f() got multiple values for keyword argument 'b'
  f(*1)                                  -> TypeError: __main__.f() argument after * must be an iterable, not int
  f(1, **[('b', 2)])                     -> TypeError: __main__.f() argument after ** must be a mapping, not list
  f(1, **{1: 2})                         -> TypeError: keywords must be strings
  f(1, **{'a': 9})                       -> TypeError: f() got multiple values for argument 'a'
```

**왜 그런가**

- ★ **`f(*[], **{})` 는 「인자를 안 준 것」과 똑같다.** 그래서 `a` 가 없다고 터졌다.
  별표 하나와 별표 둘은 **문법이지 인자가 아니다** — 빈 것을 풀면 **펼쳐지는 것이 없다.**
- **`f(*'ab')` 가 된다** — 푸는 쪽은 **아무 이터러블**이면 된다. `range` 도 되고 여러 번 써도 된다.

★★ **키가 겹친 두 `**` 가 [12번](../12-dict-and-key-requirements/2-summary.md)과 반대다.**

```text
   dict 를 만드는 자리        {**{'b': 9}, **{'b': 8}}   ->  {'b': 8}   ★ 뒤엣것이 이긴다
   함수를 부르는 자리         f(1, **{'b': 9}, **{'b': 8})  ->  TypeError  ★ 터진다
```

★ **같은 `**` 기호인데 한쪽은 덮어쓰기이고 한쪽은 에러다.**
dict 리터럴은 「합치기」가 목적이라 마지막 값이 이기는 것이 자연스럽고,
호출은 「**한 자리에 한 값**」이 계약이라 겹치면 어느 것이 옳은지 정할 수 없다.

★★ **`__main__.` 접두가 붙는 줄과 안 붙는 줄 — 호출 시점 안에서도 단계가 둘이다.**

| 줄 | 접두 | 누가 냈나 |
|---|---|---|
| `f() missing 1 required positional argument: 'a'` | 없음 | **앉히는 단계** — 함수 객체의 인자 붙이기 |
| `f() got multiple values for argument 'a'` | 없음 | 〃 |
| `__main__.f() got multiple values for keyword argument 'b'` | **있음** | ★ **푸는 단계** — 인자 목록을 만들다 겹친 것을 발견 |
| `__main__.f() argument after * must be an iterable, not int` | **있음** | ★ **푸는 단계** |
| `__main__.f() argument after ** must be a mapping, not list` | **있음** | ★ **푸는 단계** |
| `keywords must be strings` | **함수 이름 자체가 없다** | 〃 — 어느 함수인지 말하지도 않는다 |

```text
   f(1, **{'b': 9}, **{'b': 8})

   ① 푸는 단계      *·** 를 펼쳐 실제 인자 목록을 만든다   <- __main__. 접두가 붙는다
   ② 앉히는 단계    그 목록을 파라미터에 붙인다            <- 접두가 없다
```

★ **`got multiple values` 가 양쪽에 다 있는 것**이 재미있다 — `for argument 'a'`(②)와 `for keyword argument 'b'`(①).
**낱말이 한 개 다르다.** 같은 증상이 **어느 단계에서 걸렸느냐**로 갈린 것이다.\
★ 이것은 **문구의 관찰**이지 명세가 아니다. 판이 바뀌면 접두가 달라질 수 있다.

### 5. `co_argcount` 는 `*args`·`**kwargs` 를 안 센다

**출력**

```text
signature      : (pos, /, both=1, *args, kw, kw2='K', **kwargs)

이름       종류                     기본값
pos      POSITIONAL_ONLY        없음
both     POSITIONAL_OR_KEYWORD  1
args     VAR_POSITIONAL         없음
kw       KEYWORD_ONLY           없음
kw2      KEYWORD_ONLY           'K'
kwargs   VAR_KEYWORD            없음

__defaults__   : (1,)  <- 위치 인자의 기본값만, 뒤에서부터
__kwdefaults__ : {'kw2': 'K'}  <- 키워드 전용의 기본값
co_argcount            : 2
co_posonlyargcount     : 1
co_kwonlyargcount      : 2
co_varnames[:co_argcount+co_kwonlyargcount+2] : ('pos', 'both', 'kw', 'kw2', 'args', 'kwargs')
co_flags               : 15 = 0b1111
  CO_VARARGS  (0x04) 켜졌나 : True
  CO_VARKEYWORDS (0x08)     : True

def g(a, b) 는
  __defaults__   : None
  __kwdefaults__ : None
  co_flags       : 3 | CO_VARARGS : False
```

**왜 그런가**

```text
   def f(pos, /, both=1, *args, kw, kw2="K", **kwargs)
         ^^^^     ^^^^    ^^^^^  ^^  ^^^^^   ^^^^^^^^
         │        │       │      │   │       │
   co_posonlyargcount = 1 │      │   │       └ co_flags & 0x08
   co_argcount = 2 (pos, both)   │   │
                          │      └───┴ co_kwonlyargcount = 2
                          └ co_flags & 0x04
```

- ★ **`co_argcount` 가 `2`** 다 — `pos` 와 `both` 만 센다.
  **안 세는 것**: `*args`·`**kwargs`(플래그로 표시) 와 키워드 전용(`co_kwonlyargcount` 로 따로).
- ★ **`co_posonlyargcount` 가 `1`** — `/` 의 **위치가 개수로 저장**된다. 앞에서 몇 개가 위치 전용인지만 적는다.
- ★★ **`co_varnames` 의 순서가 소스와 다르다** — `('pos','both','kw','kw2','args','kwargs')`.
  소스에서는 `*args` 가 `kw` **앞**인데 이름 배치에서는 **뒤로 밀렸다.**
  **평범한 파라미터들 → 키워드 전용 → `*args` → `**kwargs`** 순서다. 컴파일러가 정한 배치라 소스 순서를 믿으면 안 된다.
- ★ **`__defaults__` 가 뒤에서부터 대응한다** — `(pos, both=1)` 에서 기본값이 하나뿐이라 `(1,)` 이고,
  그것이 **마지막 위치 파라미터 `both`** 에 붙는다.

★★ **이것이 「기본값은 뒤에 몰려야 한다」는 문법 규칙을 낳는다.**

```text
   __defaults__ = (d1, d2)   위치 파라미터 (a, b, c) 에 붙일 때
                             뒤에서부터 -> b=d1, c=d2

   만약 def f(a=1, b) 가 허용된다면?
   __defaults__ = (1,)  ->  뒤에서부터 붙이면 b=1 이 된다.  a 의 기본값이 사라진다.
   ★ 저장 구조가 "어느 파라미터의 것인지" 를 못 적으므로 구멍을 허용할 수 없다.
```

- ★ **`__kwdefaults__` 는 dict** 다 — 키워드 전용은 순서가 의미 없으므로 이름으로 적는다.
  그래서 **키워드 전용 쪽에는 그런 제약이 없다** — `def f(*, a=1, b)` 가 문법상 허용된다.
- ★ **기본값이 없으면 `None`** 이다(빈 튜플이 아니다). `len(g.__defaults__)` 는 터진다.
- **`co_flags` 가 `0b1111`** — 아래 두 비트는 다른 뜻이고 `0x04`·`0x08` 이 이 주제의 것이다.
  `def g(a, b)` 는 `3 = 0b11` 로 둘 다 꺼져 있다.

### 6. 판정은 같고 문구는 다르다

**출력**

```text
  f(*(1,), **{'kw': 2})                  OK  {'pos': 1, 'both': 1, 'args': (), 'kw': 2, 'kw2': 'K', 'kwargs': {}}
  f(*(1, 2, 3), **{'kw': 4, 'z': 5})     OK  {'pos': 1, 'both': 2, 'args': (3,), 'kw': 4, 'kw2': 'K', 'kwargs': {'z': 5}}
  f(*(1, 2), **{})                       TypeError: missing a required argument: 'kw'
  f(*(), **{'pos': 1, 'kw': 2})          TypeError: 'pos' parameter is positional only, but was passed as a keyword

--- 부르지 않고 미리 알아본 것과 실제로 부른 것이 같나 ---
  f(*(1,), **{'kw': 2})                  예측 OK         실제 OK         같나 True
  f(*(1, 2, 3), **{'kw': 4, 'z': 5})     예측 OK         실제 OK         같나 True
  f(*(1, 2), **{})                       예측 TypeError  실제 TypeError  같나 True
  f(*(), **{'pos': 1, 'kw': 2})          예측 TypeError  실제 TypeError  같나 True
```

**왜 그런가**

- ★ **네 판 모두 `같나 True`** 다 — **부르지 않고 판정할 수 있다.**
  프레임워크가 사용자 함수를 호출하기 전에 검사할 수 있는 근거가 이것이다.
- ★ **`bind()` 가 「어느 인자가 어디에 앉는지」를 글자로 보여 준다** —
  `f(1, 2, 3, kw=4, z=5)` 에서 `3` 이 `args` 로, `z` 가 `kwargs` 로 간 것이 dict 에 그대로 나온다.
  `apply_defaults()` 가 안 준 기본값(`both=1`·`kw2='K'`)까지 채운다.

★★ **다른 것은 문구다.**

| 호출 | `bind()` | 실제 호출 |
|---|---|---|
| `f(1, 2)` | `missing a required argument: 'kw'` | `f() missing 1 required keyword-only argument: 'kw'` |
| `f(pos=1, kw=2)` | `'pos' parameter is positional only, but was passed as a keyword` | `f() got some positional-only arguments passed as keyword arguments: 'pos'` |

- `bind` 는 **표준 라이브러리의 순수 파이썬 구현**이고, 실제 호출은 **인터프리터 C 코드**다.
  같은 규칙을 **두 곳이 따로 구현**하고 있어 문구가 따로 논다.
- ★★ **그 차이가 말하는 것 — 예외 문구로 테스트를 쓰지 마라.**
  같은 규칙 위반인데 경로에 따라 문구가 다르고, 판이 오르면 또 바뀐다.
  잡아야 할 것은 **`TypeError` 라는 종류**이지 문장이 아니다.
- ★ 부수적으로 얻는 것 하나 — **문구를 보면 어느 경로로 걸렸는지 알 수 있다.**
  4번 답의 `__main__.` 접두와 같은 성격의 단서다.

### 7. 기본값 없는 키워드 전용은 **필수**다

**출력**

```text
def kwonly(a, *, b)
  kwonly(1)                  -> TypeError: kwonly() missing 1 required keyword-only argument: 'b'
  kwonly(1, 2)               -> TypeError: kwonly() takes 1 positional argument but 2 were given
  kwonly(1, b=2)             -> (1, 2)
def varargs(a, *rest)
  varargs(1)                 -> (1, ())
  varargs(1, 2, 3)           -> (1, (2, 3))
  varargs(1, rest=2)         -> TypeError: varargs() got an unexpected keyword argument 'rest'
  varargs.__code__.co_kwonlyargcount : 0
  kwonly.__code__.co_kwonlyargcount  : 1
  kwonly.__kwdefaults__              : None
```

**왜 그런가**

```text
   def kwonly(a, *, b)        b 는 반드시 이름으로, 반드시 줘야 한다
        kwonly(1)     -> 없어서 TypeError
        kwonly(1, 2)  -> 위치로 줘서 TypeError ("takes 1 positional argument")
        kwonly(1,b=2) -> 된다

   def varargs(a, *rest)      rest 는 "나머지를 담는 통" 이다
        varargs(1)         -> 빈 튜플 () 이 들어간다. ★ 안 줘도 된다
        varargs(1, rest=2) -> rest 는 이름으로 못 준다 -> 모르는 키워드 취급
```

★ **`*args` 와 무엇이 다른가 — 셋이 다르다.**

| | 기본값 없는 키워드 전용(`*, b`) | `*args` |
|---|---|---|
| 안 주면 | ★ **`TypeError`(필수)** | **빈 튜플**이 들어간다 |
| 위치로 주면 | `TypeError` | 그게 정상 |
| 이름으로 주면 | 그게 정상 | ★ `TypeError` — **모르는 키워드** 취급 |

- ★ **`varargs(1, rest=2)` 의 문구가 `unexpected keyword argument 'rest'`** 다.
  「`rest` 는 위치로만 받는다」가 아니라 「**그런 키워드를 모른다**」고 말한다 —
  `*args` 의 이름은 **호출자에게 아예 안 보이는 이름**이다.
- ★ **`co_kwonlyargcount` 가 `1` 과 `0`** 으로 갈린다 — `*` 뒤에 이름이 있느냐가 그대로 수로 찍힌다.
- ★ **`kwonly.__kwdefaults__` 가 `None`** 이다 — 기본값이 하나도 없으면 dict 가 아니라 `None` 이다(5번 답).

### 8. `/` 는 이름을 감추는 게 아니라 해방한다

**출력**

```text
  h(1, x=2)                          -> TypeError: h() got multiple values for argument 'x'
  hp(1, x=2)  (x 가 위치 전용)            -> (1, {'x': 2})
```

**왜 그런가**

```text
   ** kwargs 로 "아무 이름이나" 받고 싶다
        +
   그런데 내 파라미터 이름이 그 아무 이름 중 하나일 수 있다
        ↓
   파라미터 이름을 계약에서 빼야 한다  =  위치 전용 (/)
```

★ **표준 라이브러리의 예** — `dict.update` 가 정확히 이 모양이다.
`d.update(self=1)` 을 할 수 있어야 하므로 `self` 가 **이름으로 잡히면 안 된다.**
`/` 가 없던 시절에는 **C 로 구현된 함수만** 이 성질을 가질 수 있었고,
순수 파이썬으로는 흉내 낼 수 없었다 — PEP 570 이 그 비대칭을 없앴다.

★ `/` 가 주는 것 셋.

1. **이름 충돌이 사라진다** — `**kwargs` 가 파라미터 이름과 같은 키를 받아도 된다(위 `hp`).
2. **파라미터 이름이 계약에서 빠진다** — 나중에 이름을 바꿔도 호출부가 안 깨진다.
3. **호출 형태가 하나로 고정된다** — 읽는 사람이 `f(1)` 과 `f(x=1)` 두 가지를 안 봐도 된다.

★★ **「이름을 감추려고」가 아닌 이유** — 이름은 여전히 `help()` 에도 `signature` 에도 **그대로 보인다**(5번 답의 `POSITIONAL_ONLY`).
감춰지는 것이 아니라 **「부를 때 쓰는 이름」에서만 빠지는 것**이다.

### 9. 두 층의 목록 — 그리고 호출 자리의 `SyntaxError` 셋

**출력** — 층 ①의 대표.

```text
  File "<stdin>", line 3
    f(**kw, *args)
          ^^^^^^^
SyntaxError: iterable argument unpacking follows keyword argument unpacking
```

층 ②의 대표.

```text
  f(*1)                                  -> TypeError: __main__.f() argument after * must be an iterable, not int
```

**왜 그런가**

**① 정의 시점 — `SyntaxError`. 프로그램이 시작조차 안 한다**

| 코드 | 문구 |
|---|---|
| `def f(a=1, b)` | `parameter without a default follows parameter with a default` |
| `def f(**kw, a)` | `arguments cannot follow var-keyword argument` |
| `def f(*a, *b)` | `* argument may appear only once` |
| `def f(*)` | `named arguments must follow bare *` |
| `def f(a, /, b, /)` | `/ may appear only once` |
| `def f(/, a)` | `at least one argument must precede /` |
| `def f(a, a)` | `duplicate argument 'a' in function definition` ★ 캐럿 없음 |
| ★ `f(a=1, 2)` | `positional argument follows keyword argument` |
| ★ `f(x=1, x=2)` | `keyword argument repeated: x` ★ 캐럿 없음 |
| ★ `f(**kw, *args)` | `iterable argument unpacking follows keyword argument unpacking` |

**② 호출 시점 — `TypeError`. 그 줄에 닿아야 난다**

| 코드 | 문구 |
|---|---|
| `f(1, 2, 3)` | `takes 2 positional arguments but 3 were given` |
| `f(pos=1, ...)` | `got some positional-only arguments passed as keyword arguments` |
| `f()` | `missing 1 required positional argument` |
| `f(1, 2)` (키워드 전용 누락) | `missing 1 required keyword-only argument` |
| `f(1, extra=2)` | `got an unexpected keyword argument` |
| `f(1, x=2)` | `got multiple values for argument 'x'` |
| `f(*1)` | `argument after * must be an iterable, not int` |
| `f(1, **[("b", 2)])` | `argument after ** must be a mapping, not list` |
| `f(1, **{1: 2})` | `keywords must be strings` |

★★ **호출 자리인데 `SyntaxError` 인 것 셋** — `f(a=1, 2)` · `f(x=1, x=2)` · `f(**kw, *args)`.

```text
   공통점: 셋 다 "함수가 무엇인지 몰라도" 틀렸다고 알 수 있다
           = 토큰의 배열 규칙만 어긴 것
           = 파서가 잡는다
```

- `f(a=1, 2)` — 키워드 뒤에 위치가 올 수 없다.
- `f(x=1, x=2)` — 같은 키워드가 **리터럴로** 두 번 나왔다. ★ `f(**{'x':1}, **{'x':2})` 는 **런타임에야** 알 수 있어 `TypeError` 다.
- `f(**kw, *args)` — `**` 뒤에 `*` 가 올 수 없다. 반대 순서는 된다.

★ **`f(x=1, x=2)` 와 `f(**{'x':1}, **{'x':2})` 의 대조가 이 층 구분의 가장 선명한 증거다** —
**뜻이 같은 두 코드가 다른 층에서 걸린다.** 앞엣것은 글자로 보이고 뒤엣것은 실행해야 보인다.

### 10. 가운데에 넣으면 조용히 깨지고, 키워드 전용으로 넣으면 안 깨진다

**출력**

```text
--- 원래: def api(a, b) — 호출부는 api(1, 2) ---
--- 고침 1: 가운데에 넣는다 ---
  api1(1, 2)  (옛 호출)                 -> (1, 2, None)
--- 고침 2: 키워드 전용으로 뒤에 넣는다 ---
  api2(1, 2)  (옛 호출)                 -> (1, 2, 0)
  api2(1, 2, mid=9)                  -> (1, 2, 9)
  api2(1, 2, 9)                      -> TypeError: api2() takes 2 positional arguments but 3 were given
```

**왜 그런가**

```text
   원래          def api(a, b)            api(1, 2)  ->  a=1, b=2

   고침 1        def api1(a, mid=0, b=None)
                 api1(1, 2)  ->  a=1, mid=2, b=None   ★★ 2 가 엉뚱한 자리에 앉았다
                                       ^^^^^           에러가 없다

   고침 2        def api2(a, b, *, mid=0)
                 api2(1, 2)  ->  a=1, b=2, mid=0      ★ 옛 호출이 그대로 맞는다
                 api2(1, 2, 9) -> TypeError            ★ 실수는 즉시 막힌다
```

★★ **고침 1 이 이 답의 핵심이다 — `api1(1, 2)` 가 `(1, 2, None)` 을 냈다.**
**예외가 하나도 안 났는데 `b` 가 `None` 이 됐다.** 옛 호출이 **조용히 다른 뜻**이 됐다.

- ★ **위치 인자의 「의미」는 순서로만 정해지므로, 순서를 건드리면 모든 옛 호출의 뜻이 바뀐다.**
  그리고 **타입이 우연히 맞으면 에러조차 안 난다.**
- ★ **고침 2 는 안 깨진다** — `*` 뒤에 넣었으니 **위치 자리를 안 건드린다.**
  게다가 `api2(1, 2, 9)` 처럼 **실수로 위치로 주면 즉시 `TypeError`** 다.

★ **그래서 규칙 하나** — **새 파라미터는 `*` 뒤에 키워드 전용 + 기본값으로 넣는다.**\
★★ **더 나은 것은 처음부터 `*` 를 넣어 두는 것**이다. `def api(a, b, *)` 는 문법 오류지만(2번 답),
`def api(a, b, *, )` 대신 **필요한 순간 키워드 전용 칸을 열 수 있도록** 설계 단계에서 인자 수를 줄여 두는 편이 낫다 —
인자가 계속 늘 것 같으면 **데이터클래스 하나로 묶는다**([목록의 **36번 주제**](../36-dataclasses/)).

### 11. 세 층

**출력** — 층을 가르는 근거로 쓴 것.

```text
co_flags               : 15 = 0b1111
  CO_VARARGS  (0x04) 켜졌나 : True
```

```text
  f(1, **{'b': 9}, **{'b': 8})           -> TypeError: __main__.f() got multiple values for keyword argument 'b'
```

**왜 그런가**

**언어 보장**

| 사실 | 근거 |
|---|---|
| 파라미터 순서 — 위치전용 `/` 둘다 `*args` 키워드전용 `**kwargs` | 8.7 Function definitions |
| 기본값 있는 파라미터 뒤에 **기본값 없는 것이 못 온다** | 8.7 |
| **`/` 왼쪽은 이름으로 못 준다**(3.8+) | PEP 570 |
| **`*` 오른쪽은 이름으로만** · 기본값이 없으면 **필수**(3.0+) | PEP 3102 · 8.7 |
| 호출에서 **위치 인자가 키워드보다 앞**에 와야 한다 | 6.3.4 Calls |
| **한 파라미터에 값이 두 번 들어가면 `TypeError`** | 6.3.4 |
| **`**kwargs` 없이 모르는 키워드를 주면 `TypeError`** | 6.3.4 |
| `*expr` 는 **이터러블**, `**expr` 는 **매핑**, 키는 **문자열** | 6.3.4 |
| 기본값은 **`def` 실행 때 한 번** 계산된다 | 8.7 — 정본은 [20번](../20-mutable-default-args/2-summary.md) |

**CPython 구현 세부사항**

| 사실 | 어떻게 확인했나 |
|---|---|
| `__defaults__` 는 **튜플**, 뒤에서부터 대응, 없으면 **`None`** | 실행 |
| `__kwdefaults__` 는 **dict**, 없으면 `None` | 실행 |
| `co_argcount`·`co_posonlyargcount`·`co_kwonlyargcount` 가 **개수만** 저장 | 실행 |
| `co_varnames` 에서 **`*args`·`**kwargs` 가 뒤로 밀린다** | 실행 |
| `co_flags` 의 `0x04`·`0x08` | 실행 — `0b1111` 대 `0b11` |
| 일부 `SyntaxError` 에 **캐럿이 없다** | 실행 — 파서 뒤 단계가 잡는다 |
| `Signature.bind` 의 **문구가 실제 호출과 다르다** | 실행 — 순수 파이썬 구현 |
| 일부 `TypeError` 에 **`__main__.` 접두**가 붙는다 | 실행 — 푸는 단계와 앉히는 단계 |

**이 판(3.12.3)의 관찰**

| 관찰 | 어디가 흔들리나 |
|---|---|
| `SyntaxError`·`TypeError` **문구 전부** | 종류는 명세, 문구는 아니다. 판마다 손본다 |
| `__main__.` 접두가 붙는 줄과 안 붙는 줄 | 어느 C 코드가 냈느냐의 결과 |
| `keywords must be strings` 가 **함수 이름을 안 말하는 것** | 위와 같다 |
| 캐럿이 있는 `SyntaxError` 와 없는 것의 갈림 | 진단 표시 방식 |
| `co_flags` 가 `15`(`0b1111`) | 다른 비트가 섞여 있다 |
| `bind()` 의 문구 | 표준 라이브러리 구현 |

★ **판정 기준 한 줄** — **규칙은 명세이고, 「그 규칙을 어겼을 때 무슨 문장이 나오나」와 「그 규칙이 어디에 저장되나」는 이 구현이다.**

### 12. 기본값의 경계

**출력** — 여기까지가 이 주제다.

```text
__defaults__   : (1,)  <- 위치 인자의 기본값만, 뒤에서부터
__kwdefaults__ : {'kw2': 'K'}  <- 키워드 전용의 기본값
```

**왜 그런가**

```text
   19번 (여기)                          20번 (정본 이웃)
   ─────────────────────────────       ─────────────────────────────
   기본값이 어디에 저장되나              기본값이 언제 만들어지나
   __defaults__ 는 튜플 · 뒤에서부터     def 문을 실행할 때 한 번
   __kwdefaults__ 는 dict               그래서 호출 사이에 공유된다
   없으면 None                          가변이면 상태가 새어 흐른다
   -> "기본값은 뒤에 몰려야 한다" 의 이유  -> None 센티널로 고친다
```

★ **한 줄로 긋는다** — **「어느 호출이 되나」까지가 19번, 「그 기본값이 호출 사이에 어떻게 되나」부터가 [20번](../20-mutable-default-args/2-summary.md)이다.**

- 여기서 `__defaults__` 를 본 것은 **문법 규칙의 이유**를 대기 위해서다(5번 답) — **뒤에서부터 붙는 튜플**이라 구멍을 허용할 수 없다.
- 20번이 같은 `__defaults__` 를 보는 것은 **그 안의 객체가 하나뿐**임을 보이기 위해서다. **같은 창, 다른 질문**이다.
- ★ 그래서 이 주제는 **「`def f(x=[])` 는 왜 나쁜가」에 답하지 않는다.** 그 답은 전부 20번에 있다.

★ 다른 이웃과의 경계도 한 줄씩.

| 주제 | 경계 |
|---|---|
| [11번](../11-tuple-and-unpacking/2-summary.md) | **대입문의 별표**(`a, *b = xs`)는 그쪽, **호출의 별표**(`f(*xs)`)는 여기 |
| [12번](../12-dict-and-key-requirements/2-summary.md) | `{**a, **b}` 의 **뒤엣것이 이기는** 규칙은 그쪽, **호출에서 겹치면 터지는** 것은 여기 |
| [16번](../16-iterator-protocol/2-summary.md) | `f(*it)` 로 풀면 **이터레이터가 소진되는** 것은 그쪽의 계약, 그것이 **인자가 되는** 것은 여기 |
| [18번](../18-loop-control-and-else/2-summary.md) | `'break' outside loop` 이 **캐럿 없는 `SyntaxError`** 인 것 — **층 구분의 정본은 여기**다 |
| [목록의 **24번 주제**](../24-decorators/) | `(*args, **kwargs)` 래퍼와 `functools.wraps` 는 그쪽 |
| [목록의 **40번 주제**](../40-type-hints-at-runtime/) | 시그니처에 붙는 **타입 힌트**는 그쪽 — 이 주제의 검사는 **개수와 이름**만 본다 |

## 실행 검증

이 문서와 [2-summary.md](2-summary.md)에 실린 출력은 전부 아래처럼 돌려서 얻었다.

| 무엇을 | 어떻게 | 몇 번 | 어디에 |
|---|---|---|---|
| 안 도는 가지 실험 2종 | `python3 - <ex.py` · 3.12.3 | 2회 | 1번 답 |
| 정의 시점 `SyntaxError` 6종 | 〃 — **각각 따로** | 6회 | 2번 답 |
| `duplicate argument` · `keyword argument repeated` | 〃 | 2회 | 2번 답 |
| `f(**kw, *args)` | 〃 | 1회 | 9번 답 |
| 다섯 칸 시그니처 호출 13종 | 〃 | 1회(한 파일) | 3번 답 |
| 풀어서 넘기기 11종 | 〃 | 1회 | 4번 답 |
| `signature`·`__defaults__`·`co_flags` | 〃 | 1회 | 5번 답 |
| `bind()` 대 실제 호출 4종 | 〃 | 1회 | 6번 답 |
| 키워드 전용 대 `*args` | 〃 | 1회 | 7번 답 |
| 시그니처 확장 2종 | 〃 | 1회 | 10번 답 |

**구현 의존 항목 — 버전이 오르면 다시 돌려야 할 것**

- **`SyntaxError`·`TypeError` 문구 전부**(2·3·4·7·9·10번 답) — 종류는 명세, 문구는 아니다.
- **`__main__.` 접두가 붙는 줄**(4번 답) — 어느 단계가 냈느냐의 결과라 판마다 바뀔 수 있다.
- **캐럿이 있는 `SyntaxError` 와 없는 것의 갈림**(2번 답) — 진단 표시 방식.
- **`co_flags` = `15`·`3`**(5번 답) — 다른 비트가 섞여 있다.
- **`co_varnames` 의 배치**(5번 답) — 컴파일러가 정하는 것이다.
- **`bind()` 의 문구**(6번 답) — 표준 라이브러리 구현.
