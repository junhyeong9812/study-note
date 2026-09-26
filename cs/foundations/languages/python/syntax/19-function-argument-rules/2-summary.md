# python/syntax/19-function-argument-rules — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만.
> - [8.7. Function definitions](https://docs.python.org/3.12/reference/compound_stmts.html#function-definitions) — 파라미터 문법 · `/` · `*`
> - [6.3.4. Calls](https://docs.python.org/3.12/reference/expressions.html#calls) — 인자 붙이기 규칙 · `*`·`**` 풀기
> - [`inspect.signature`](https://docs.python.org/3.12/library/inspect.html#inspect.signature) · [`Signature.bind`](https://docs.python.org/3.12/library/inspect.html#inspect.Signature.bind) · [`Parameter.kind`](https://docs.python.org/3.12/library/inspect.html#inspect.Parameter.kind)
> - [PEP 570 — Positional-Only Parameters](https://peps.python.org/pep-0570/) · [PEP 3102 — Keyword-Only Arguments](https://peps.python.org/pep-3102/)
> - [`inspect` — Types and members](https://docs.python.org/3.12/library/inspect.html#types-and-members) — `__defaults__`·`__kwdefaults__`·`co_flags`
>
> **실행 검증** — 이 문서에 실린 출력은 전부 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.\
> ★ **던지는 형태를 하나로 고정했다** — `python3 - <파일` 로 던져 트레이스백이 `File "<stdin>", line N` 이 된다.
> ★★ **그래서 실행 중 예외에는 소스 줄과 캐럿이 없고, `SyntaxError` 에는 있다** —
> 이 주제는 그 두 층이 **본체**라 그 차이가 그대로 교재가 된다. 다만 `SyntaxError` 중에도 **캐럿이 안 나오는 것**이 있다(동작 3).\
> **버전** — 키워드 전용(`*`)은 **3.0+**(PEP 3102), **위치 전용(`/`)은 3.8+**(PEP 570).
> 그 밖의 인자 규칙은 이 노트 범위(3.10\~3.13)에서 안 바뀌었다.
> 다만 **예외 문구는 판마다 손본다** — 3.11.15 와 대조해 갈린 자리를 아래에 적었다.\
> **★ 흔들리는 칸 / 안 흔들리는 칸** — 재대조에서 「고칠 것」과 「설계상 안 맞는 것」을 기계적으로 가르려고 미리 선언한다.
>
> | 흔들린다 | 안 흔들린다(근거로 써도 되는 칸) |
> |---|---|
> | (판이 오르면) `SyntaxError`·`TypeError` **문구** | 예외 **종류**와 **어느 층에서 나나** |
> | (판이 오르면) `__main__.` **접두**가 붙는 줄 | 「푸는 단계와 앉히는 단계가 다르다」는 사실 |
> | (판이 오르면) **캐럿 줄의 유무** | `File "<stdin>", line N` |
> | (판이 오르면) `co_flags` = `15`·`3` · `co_varnames` 배치 | `co_argcount`·`co_posonlyargcount`·`co_kwonlyargcount` 가 **세는 대상** |
>
> ★ **이 주제의 실행 출력은 전부 결정적이다** — 같은 판에서 다시 돌리면 한 글자도 안 변한다(수치·주소를 안 찍는다).\
> ★ **stdout 과 stderr 가 섞인 블록은 없다** — 잡은 `TypeError` 는 전부 `print` 로 stdout 에 찍고,
> `SyntaxError` 블록은 **stderr 한 줄기뿐**이라 순서가 실행 환경을 안 탄다.
>
> **선행** — [11-tuple-and-unpacking](../11-tuple-and-unpacking/2-summary.md)(별표 언패킹) ·
> [12-dict-and-key-requirements](../12-dict-and-key-requirements/2-summary.md)(`**` 가 푸는 것).\
> **정본 이웃** — [20-mutable-default-args](../20-mutable-default-args/2-summary.md)가 **기본값의 정본**이다.
> 「기본값이 `def` 실행 때 한 번 만들어진다」와 그 함정·고침(`None` 센티널)은 전부 그쪽이고,
> 여기는 **「어떤 호출이 되고 안 되나」** 만 다룬다.

## 한눈에 — 쉽게 말하면

**시그니처는 「좌석표」이고 호출은 「입장」이다. 그리고 검사가 두 번, 다른 문지기에게 일어난다.**

```text
   ① 정의 시점 — 파서가 읽을 때          SyntaxError
      "좌석표 자체가 말이 안 된다"         ★ 그 줄이 안 도는 자리에 있어도
      def f(a=1, b)                        프로그램이 시작조차 안 한다

   ② 호출 시점 — 인자를 좌석에 앉힐 때    TypeError
      "좌석표는 멀쩡한데 손님이 안 맞는다"  ★ 그 줄에 닿아야 난다
      f(1, 2, 3)
```

★★ **이 층 구분이 이 주제의 본체다.** 같은 「인자가 틀렸다」인데 **언제 걸리느냐**가 갈린다.

**좌석표의 다섯 칸**

```text
   def f( pos , / , both , * args , kw , ** kwargs )
          ^^^^   ^   ^^^^   ^^^^^^   ^^   ^^^^^^^^
          위치     │  둘 다   나머지   키워드  나머지
          전용     │  가능    위치     전용    키워드
                   └ 이 왼쪽은 이름으로 못 부른다
                            * 의 오른쪽은 이름으로만 부른다
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 좌석표가 말이 안 된다 | 정의 시점 오류 | **`SyntaxError`** — 안 도는 가지에 둬도 난다 |
| 손님이 좌석에 안 맞는다 | 호출 시점 오류 | **`TypeError`** — 그 줄에 닿아야 난다 |
| `/` 왼쪽 = 번호석 | 위치 전용 | 이름으로 부르면 `TypeError` |
| `*` 오른쪽 = 지정석 | 키워드 전용 | 위치로 주면 `TypeError` |
| 남는 손님을 담는 통 | `*args`·`**kwargs` | `co_flags` 의 비트로 보인다 |
| 앉히기 전에 자리 배치를 계산해 본다 | `inspect.signature().bind()` | **부르지 않고** 되는지 알 수 있다 |
| ★ **같은 사람이 번호석과 지정석을 동시에** | 위치 + 키워드 중복 | `got multiple values for argument` |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.\
「**인자 하나 추가했더니 호출하는 쪽이 전부 깨졌다**」와 「**`**kwargs` 로 넘겼더니 이름이 충돌했다**」가 그것이다.
앞엣것은 `*`·`/` 로 미리 막을 수 있고, 뒤엣것은 `/` 가 **유일한** 해법이다(동작 5).

> **위치 전용(positional-only)** — `/` 의 왼쪽에 있는 파라미터. **이름으로는 못 준다.**\
> 예: `def f(x, /)` 에서 `f(x=1)` 은 `TypeError` 다. 덕분에 `x` 라는 이름을 `**kwargs` 에 자유롭게 쓸 수 있다.

> **키워드 전용(keyword-only)** — `*` 나 `*args` 의 오른쪽에 있는 파라미터. **이름으로만 줄 수 있다.**\
> 예: `def f(a, *, verbose)` 에서 `f(1, True)` 는 `TypeError` 다. 호출부가 읽히도록 강제한다.

## 이 주제가 답하려는 질문

1. **언제 걸리나** — 「인자가 틀렸다」가 `SyntaxError` 인 자리와 `TypeError` 인 자리를 무엇이 가르나.
2. **어떤 호출이 되나** — 다섯 칸짜리 시그니처에 어떤 호출이 붙고 어떤 것이 튕기나.
3. **부르지 않고 알 수 있나** — `inspect.signature` 로 **호출 전에** 판정할 수 있나. 판정이 실제와 같나.

## 동작 방식

> 이 절이 본문이다. 이 주제의 네 번째 창은 **시그니처 객체**다 —
> `inspect.signature` · `__defaults__` · `__kwdefaults__` · `co_flags`.
> **어떤 호출이 되는지는 던져서**, **왜 되는지는 시그니처로** 본다.

### 1. ★★ 두 층 — 안 도는 가지에 둬 보면 갈린다

**언제 쓰나** — 이 주제의 핵심. 「이 에러는 왜 실행 전에 났지」를 물을 때.

문법 오류는 **파일 전체를 컴파일할 때** 걸리고, 인자 붙이기 오류는 **그 호출을 실행할 때** 걸린다.
그것을 가르는 실험은 하나다 — **절대 안 도는 가지에 넣어 보는 것.**

```text
===== 소스: ex.py =====
def f(*a, **k): pass
print("여기까지는 찍힐까?")
if False:
    f(a=1, 2)
```

```text
  File "<stdin>", line 4
    f(a=1, 2)
            ^
SyntaxError: positional argument follows keyword argument
```

★★ **`여기까지는 찍힐까?` 가 안 찍혔다.** 첫 줄도 안 돌았다 —
**파일 전체가 컴파일에 실패해 프로그램이 시작조차 못 했다.**

```text
===== 소스: ex.py =====
def f(a, b): pass
print("여기는 찍힌다")
if False:
    f(1, 2, 3, 4, 5)
print("끝까지 왔다")
```

```text
여기는 찍힌다
끝까지 왔다
```

★★ **이쪽은 아무 일도 안 났다.** `f(1,2,3,4,5)` 는 **틀린 호출인데** `if False:` 안이라 **실행되지 않았고**,
인자 검사는 **실행할 때만** 하기 때문이다.

```text
   같은 파일, 같은 "인자가 틀렸다"

   f(a=1, 2)          파서가 읽는 순간 실패   ->  프로그램이 안 뜬다
   f(1, 2, 3, 4, 5)   읽기는 멀쩡            ->  그 줄에 닿아야 실패
```

그림 해설.

- ★ **`SyntaxError` 는 「이 글이 파이썬이 아니다」는 말이다.** 함수가 무엇인지 보지도 않는다 —
  `f` 가 `*a, **k` 를 받든 말든 `f(a=1, 2)` 는 **글자 배열이 규칙에 안 맞다.**
- ★ **`TypeError` 는 「글은 맞는데 이 함수엔 안 맞는다」는 말이다.** **함수 객체를 봐야** 알 수 있으므로 실행이 필요하다.
- ★★ **그래서 테스트가 안 지나가는 가지의 `TypeError` 는 영영 안 잡힌다.** 반대로 `SyntaxError` 는 **100% 잡힌다.**
  **정적 검사로 잡히는 것과 안 잡히는 것의 경계**가 정확히 여기다.

**비용** — 파서가 미리 잡아 주는 덕에 오타류가 실행 전에 걸린다.\
대신 **인자 개수·이름 오류는 실행해야만** 걸린다 — 그래서 타입 체커(목록의 **40번 주제**)가 필요해진다.

### 2. ★ 정의 시점에 걸리는 것들 — 좌석표 자체가 말이 안 되는 경우

**언제 쓰나** — 시그니처를 쓰다가 빨간 줄이 났을 때. 규칙을 외우지 말고 **에러 문구로 기억**한다.

각각 따로 던졌다. **여덟 개 전부 `SyntaxError` 이고 프로그램이 시작조차 안 한다.**

```text
===== 소스: ex.py =====
def f(a=1, b): pass
```

```text
  File "<stdin>", line 1
    def f(a=1, b): pass
               ^
SyntaxError: parameter without a default follows parameter with a default
```

```text
===== 소스: ex.py =====
def f(**kw, a): pass
```

```text
  File "<stdin>", line 1
    def f(**kw, a): pass
                ^
SyntaxError: arguments cannot follow var-keyword argument
```

```text
===== 소스: ex.py =====
def f(*a, *b): pass
```

```text
  File "<stdin>", line 1
    def f(*a, *b): pass
              ^
SyntaxError: * argument may appear only once
```

```text
===== 소스: ex.py =====
def f(*): pass
```

```text
  File "<stdin>", line 1
    def f(*): pass
          ^
SyntaxError: named arguments must follow bare *
```

```text
===== 소스: ex.py =====
def f(a, /, b, /): pass
```

```text
  File "<stdin>", line 1
    def f(a, /, b, /): pass
                   ^
SyntaxError: / may appear only once
```

```text
===== 소스: ex.py =====
def f(/, a): pass
```

```text
  File "<stdin>", line 1
    def f(/, a): pass
          ^
SyntaxError: at least one argument must precede /
```

★ **여기까지 여섯 개는 소스 줄과 캐럿이 나온다.** 아래 둘은 **안 나온다.**

```text
===== 소스: ex.py =====
def f(a, a): pass
```

```text
  File "<stdin>", line 1
SyntaxError: duplicate argument 'a' in function definition
```

```text
===== 소스: ex.py =====
def f(*a, **k): pass
kw = {}; args = ()
f(x=1, x=2)
```

```text
  File "<stdin>", line 3
SyntaxError: keyword argument repeated: x
```

그림 해설 — **캐럿이 있느냐 없느냐가 또 하나의 층이다.**

```text
   소스 글자 ──> 파서 ──────> AST ──> 심볼 테이블·컴파일 ──> 바이트코드
                   │                      │
                   │                      └ SyntaxError (캐럿 없음)
                   │                        · duplicate argument 'a'
                   │                        · keyword argument repeated: x
                   └ SyntaxError (캐럿 있음)
                     · parameter without a default follows ...
                     · / may appear only once  ...
```

- ★ **파서가 「글자 배열」을 보다 걸린 것은 그 위치를 정확히 안다** → 줄과 캐럿을 찍는다.
- ★ **이름이 겹쳤다는 것은 글자 배열만 봐서는 모른다.** 파싱을 끝내고 **파라미터 목록을 모아 봐야** 안다 →
  위치가 없어 줄 번호만 찍는다.
- ★★ **둘 다 `SyntaxError` 이고 둘 다 실행 전에 걸린다.** 층 ①의 안쪽이 또 둘로 갈리는 것이지 층이 바뀌는 게 아니다.
  [18번](../18-loop-control-and-else/2-summary.md)의 `'break' outside loop` 도 **캐럿이 없는 쪽**이다.

★ **`def f(*): pass` 의 문구가 특히 쓸모 있다** — *"named arguments must follow bare `*`"*.
**맨 `*` 뒤에는 이름이 반드시 와야 한다**는 뜻이라, 「키워드 전용을 만들려면 뒤에 뭘 써야 한다」를 문구가 직접 알려 준다.

**비용** — 실행 전에 전부 잡힌다.\
대신 **한 곳만 틀려도 파일 전체가 안 뜬다** — 모듈 import 사슬에서 이것이 나면 무관한 기능까지 멈춘다.

### 3. ★ 호출 시점에 걸리는 것들 — 좌석표는 멀쩡한데 손님이 안 맞는 경우

**언제 쓰나** — 다섯 칸짜리 시그니처에 무엇이 붙는지 판정할 때.

```text
===== 소스: ex.py =====
def f(pos, /, both, *, kw):
    return pos, both, kw

def show(label, thunk):
    try:
        print(f"  {label:<34} -> {thunk()}")
    except TypeError as e:
        print(f"  {label:<34} -> TypeError: {e}")

print("def f(pos, /, both, *, kw)")
show("f(1, 2, kw=3)",        lambda: f(1, 2, kw=3))
show("f(1, both=2, kw=3)",   lambda: f(1, both=2, kw=3))
show("f(1, 2, 3)",           lambda: f(1, 2, 3))
show("f(pos=1, both=2, kw=3)", lambda: f(pos=1, both=2, kw=3))
show("f(1, 2)",              lambda: f(1, 2))
show("f(1, 2, kw=3, extra=4)", lambda: f(1, 2, kw=3, extra=4))

print()
def g(a, b=2, *args, **kwargs):
    return a, b, args, kwargs
print("def g(a, b=2, *args, **kwargs)")
show("g(1)",                 lambda: g(1))
show("g(1, 2, 3, x=9)",      lambda: g(1, 2, 3, x=9))
show("g(1, 1, b=2)",         lambda: g(1, 1, b=2))
show("g(b=2)",               lambda: g(b=2))
show("g(1, pos=0)",          lambda: g(1, pos=0))

print()
print("--- 같은 인자를 위치와 키워드로 동시에 ---")
def h(x): return x
show("h(1, x=2)",            lambda: h(1, x=2))
def hp(x, /, **kw): return x, kw
show("hp(1, x=2)  (x 가 위치 전용)", lambda: hp(1, x=2))
```

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

그림 해설 — **문구가 곧 규칙이다.**

| 문구 | 무엇을 어겼나 |
|---|---|
| `takes 2 positional arguments but 3 were given` | **위치 자리가 모자란다** — `*args` 가 없으니 넘치면 터진다 |
| `got some positional-only arguments passed as keyword arguments: 'pos'` | **`/` 왼쪽을 이름으로 불렀다** |
| `missing 1 required keyword-only argument: 'kw'` | **`*` 오른쪽을 안 줬다** — 기본값이 없으면 **필수**다 |
| `got an unexpected keyword argument 'extra'` | **`**kwargs` 가 없는데 모르는 이름을 줬다** |
| `got multiple values for argument 'b'` | ★ **같은 자리에 위치와 키워드를 둘 다 줬다** |
| `missing 1 required positional argument: 'a'` | **필수 위치를 안 줬다** |

★★ **`h(1, x=2)` 와 `hp(1, x=2)` 의 대조가 이 절의 결론이다.**

```text
   def h(x)            h(1, x=2)   ->  x 자리에 1 도 2 도 들어가려 한다  ->  TypeError
   def hp(x, /, **kw)  hp(1, x=2)  ->  1 은 x 자리, 'x'=2 는 kw 로 간다  ->  (1, {'x': 2})
                              ^
                        / 덕분에 이름 'x' 가 파라미터 이름과 충돌하지 않는다
```

★ **이것이 `/` 가 존재하는 진짜 이유다**(PEP 570). 「이름을 감추려고」가 아니라
**`**kwargs` 에 임의의 키를 받을 때 파라미터 이름과 부딪히지 않게** 하려는 것이다.
`dict.update(a=1)` 같은 표준 API 가 정확히 이 모양이다.

★ **`g(1, pos=0)` 이 통과한 것**도 같은 성질이다 — `g` 에 `pos` 라는 파라미터가 없으니 `kwargs` 로 들어간다.
**모르는 이름이 에러인지 아닌지는 `**kwargs` 의 유무가 정한다.**

**비용** — 문구가 친절해 원인을 바로 안다.\
대신 **전부 실행 시점**이다. 안 도는 경로의 잘못된 호출은 배포 뒤에 터진다.

### 4. ★ 풀어서 넘기기 — `f(*[], **{})` 부터

**언제 쓰나** — 인자를 모아 두었다가 넘길 때. 래퍼 함수를 쓸 때.

```text
===== 소스: ex.py =====
def f(a, b=2, *args, kw="K", **kwargs):
    return a, b, args, kw, kwargs

def show(label, thunk):
    try:
        print(f"  {label:<38} -> {thunk()}")
    except TypeError as e:
        print(f"  {label:<38} -> TypeError: {e}")

print("def f(a, b=2, *args, kw='K', **kwargs)")
show("f(*[], **{})",              lambda: f(*[], **{}))
show("f(1, *[], **{})",           lambda: f(1, *[], **{}))
show("f(*[1, 2, 3], **{'kw': 'X'})", lambda: f(*[1, 2, 3], **{"kw": "X"}))
show("f(*'ab')",                  lambda: f(*"ab"))
show("f(*range(2), *range(2))",   lambda: f(*range(2), *range(2)))
show("f(1, **{'b': 9}, **{'z': 0})", lambda: f(1, **{"b": 9}, **{"z": 0}))
show("f(1, **{'b': 9}, **{'b': 8})", lambda: f(1, **{"b": 9}, **{"b": 8}))
show("f(*1)",                     lambda: f(*1))
show("f(1, **[('b', 2)])",        lambda: f(1, **[("b", 2)]))
show("f(1, **{1: 2})",            lambda: f(1, **{1: 2}))
show("f(1, **{'a': 9})",          lambda: f(1, **{"a": 9}))
```

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

그림 해설 — 읽을 것이 셋이다.

- ★ **`f(*[], **{})` 는 「인자를 안 준 것」과 똑같다.** 빈 것을 풀면 **아무 일도 안 일어난다** —
  그래서 `a` 가 없다고 터졌다. 별표 하나와 별표 둘은 **문법이지 인자가 아니다.**
- ★ **`f(*'ab')` 가 된다.** 푸는 쪽은 **아무 이터러블**이면 된다 — 문자열도 `range` 도. 별표는 **여러 번** 쓸 수 있다.
- ★ **`**` 를 여러 번 쓸 때 키가 겹치면 터진다**(`b` 가 두 번). 겹치지 않으면 합쳐진다.
  ★ [12번](../12-dict-and-key-requirements/2-summary.md)의 `{**a, **b}` 와 **다르다** — 그쪽은 **뒤엣것이 이긴다.**
  **같은 `**` 기호가 호출 자리에서는 충돌을 에러로 만든다.**
- ★ **`f(1, **{'a': 9})` 가 「중복」이다** — `1` 이 이미 `a` 에 앉았는데 이름으로 또 준 것. 3번 절의 `h(1, x=2)` 와 같은 사고다.

★★ **문구에 `__main__.` 이 붙는 줄과 안 붙는 줄이 있다.**

| 문구 | 접두 | 누가 냈나 |
|---|---|---|
| `f() missing 1 required positional argument` | 없음 | **함수 객체의 인자 붙이기**가 낸다 |
| `__main__.f() argument after * must be an iterable, not int` | **있음** | **호출을 실행하는 쪽**(인터프리터)이 푸는 단계에서 낸다 |
| `keywords must be strings` | 함수 이름 자체가 없다 | 〃 — 어느 함수인지 말하지도 않는다 |

★ **즉 「호출 시점」 안에서도 단계가 둘이다** — **푸는 단계**(`*`·`**` 를 펼쳐 실제 인자 목록을 만든다)와
**앉히는 단계**(그 목록을 파라미터에 붙인다). 문구의 접두가 그 갈림을 드러낸다.\
★ 이것은 **문구의 관찰**이지 명세가 아니다 — 판이 바뀌면 접두가 달라질 수 있다.

**비용** — 래퍼·데코레이터가 `(*args, **kwargs)` 한 줄로 아무 함수나 감쌀 수 있다.\
대신 **시그니처가 사라진다** — 무엇을 받는지 읽는 사람도 도구도 모른다(그 대가를 줄이는 것이 `functools.wraps`, [목록의 **24번 주제**](../24-decorators/)).

### 5. ★ 시그니처 객체 — 부르지 않고 알아본다

**언제 쓰나** — 「왜 이 호출이 되나」를 설명할 때. 프레임워크가 함수를 들여다볼 때.

```text
===== 소스: ex.py =====
import inspect

def f(pos, /, both=1, *args, kw, kw2="K", **kwargs):
    pass

print("signature      :", inspect.signature(f))
print()
print(f"{'이름':<8} {'종류':<22} {'기본값'}")
for name, p in inspect.signature(f).parameters.items():
    d = "없음" if p.default is inspect.Parameter.empty else repr(p.default)
    print(f"{name:<8} {p.kind.name:<22} {d}")

print()
c = f.__code__
print("__defaults__   :", f.__defaults__,   " <- 위치 인자의 기본값만, 뒤에서부터")
print("__kwdefaults__ :", f.__kwdefaults__, " <- 키워드 전용의 기본값")
print("co_argcount            :", c.co_argcount)
print("co_posonlyargcount     :", c.co_posonlyargcount)
print("co_kwonlyargcount      :", c.co_kwonlyargcount)
print("co_varnames[:co_argcount+co_kwonlyargcount+2] :", c.co_varnames[:c.co_argcount + c.co_kwonlyargcount + 2])
print("co_flags               :", c.co_flags, "=", bin(c.co_flags))
print("  CO_VARARGS  (0x04) 켜졌나 :", bool(c.co_flags & inspect.CO_VARARGS))
print("  CO_VARKEYWORDS (0x08)     :", bool(c.co_flags & inspect.CO_VARKEYWORDS))

def g(a, b):
    pass
print()
print("def g(a, b) 는")
print("  __defaults__   :", g.__defaults__)
print("  __kwdefaults__ :", g.__kwdefaults__)
print("  co_flags       :", g.__code__.co_flags, "| CO_VARARGS :", bool(g.__code__.co_flags & inspect.CO_VARARGS))
```

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

그림 해설 — 네 창이 같은 것을 다르게 말한다.

```text
   def f(pos, /, both=1, *args, kw, kw2="K", **kwargs)

   ┌ signature ─────────────────────────────────────────┐
   │ 다섯 종류를 이름으로 준다 (POSITIONAL_ONLY ...)      │  읽기용
   └────────────────────────────────────────────────────┘
   ┌ __defaults__ / __kwdefaults__ ─────────────────────┐
   │ (1,)          {'kw2': 'K'}                         │  ★ 값 자체를 들고 있다
   └────────────────────────────────────────────────────┘
   ┌ co_argcount / co_posonlyargcount / co_kwonlyargcount┐
   │    2               1                  2            │  개수만
   └────────────────────────────────────────────────────┘
   ┌ co_flags = 0b1111 ─────────────────────────────────┐
   │ 0x04 CO_VARARGS · 0x08 CO_VARKEYWORDS               │  *args / **kwargs 유무
   └────────────────────────────────────────────────────┘
```

- ★ **`__defaults__` 는 튜플이고 「뒤에서부터」 붙는다.** `(pos, both=1)` 에서 기본값이 하나뿐이라 `(1,)` 이고,
  그것이 **마지막 위치 파라미터**에 대응한다. 그래서 **기본값 있는 것이 뒤에 몰려야 한다**는 규칙(동작 2의 첫 `SyntaxError`)이 나온다.
- ★ **`__kwdefaults__` 는 dict** 다 — 키워드 전용은 순서가 의미 없어서다. `kw` 는 기본값이 없어 **안 들어 있다.**
- ★ **`co_argcount` 가 `2`** 다 — **`pos` 와 `both`** 를 센다. `co_posonlyargcount` 는 그중 **앞 1개**가 위치 전용임을 말한다.
  즉 **`/` 의 위치는 「개수」로 저장**된다. `*args`·`**kwargs` 는 이 수에 **안 들어간다.**
- ★ **`co_varnames` 의 순서가 소스 순서와 다르다** — `('pos','both','kw','kw2','args','kwargs')`.
  **`*args`·`**kwargs` 가 뒤로 밀린다.** 이름 배치는 **컴파일러가 정한 것**이라 소스 순서를 그대로 믿으면 안 된다.
- ★ **`co_flags` 가 `0b1111`** 이다. 아래 두 비트(`0x01`·`0x02`)는 다른 뜻이고,
  **`0x04`(`*args`)·`0x08`(`**kwargs`)** 가 이 주제의 것이다. `def g(a, b)` 는 `3 = 0b11` 이라 둘 다 꺼져 있다.
- ★ **기본값이 없으면 `__defaults__` 가 `None`** 이다 — 빈 튜플이 아니다. `if f.__defaults__:` 로 검사하면 둘 다 거짓이라 우연히 맞지만,
  `len(f.__defaults__)` 는 **터진다.**

★ **기본값이 「언제 만들어지나」와 그 함정은 [20번](../20-mutable-default-args/2-summary.md)이 정본이다.**
여기서는 **그 값이 어디에 저장되나**(`__defaults__`·`__kwdefaults__`)까지만 본다.

**비용** — 함수를 부르지 않고 규칙을 읽을 수 있다.\
대신 **`__defaults__`·`co_flags` 는 CPython 의 내성 인터페이스**다. `inspect.signature` 쪽이 이식성이 높다.

### 6. ★ `bind()` — 부르지 않고 「되나 안 되나」를 판정한다

**언제 쓰나** — 프레임워크가 사용자 함수를 호출하기 전에 검사할 때. 그리고 이 주제를 **스스로 채점할 때.**

```text
===== 소스: ex.py =====
import inspect

def f(pos, /, both=1, *args, kw, kw2="K", **kwargs):
    return "돌았다"

sig = inspect.signature(f)
calls = [
    ((1,), {"kw": 2}),
    ((1, 2, 3), {"kw": 4, "z": 5}),
    ((1, 2), {}),
    ((), {"pos": 1, "kw": 2}),
]
for args, kwargs in calls:
    label = f"f(*{args}, **{kwargs})"
    try:
        b = sig.bind(*args, **kwargs)
        b.apply_defaults()
        print(f"  {label:<38} OK  {dict(b.arguments)}")
    except TypeError as e:
        print(f"  {label:<38} TypeError: {e}")

print()
print("--- 부르지 않고 미리 알아본 것과 실제로 부른 것이 같나 ---")
for args, kwargs in calls:
    label = f"f(*{args}, **{kwargs})"
    try:
        sig.bind(*args, **kwargs); pred = "OK"
    except TypeError:
        pred = "TypeError"
    try:
        f(*args, **kwargs); real = "OK"
    except TypeError:
        real = "TypeError"
    print(f"  {label:<38} 예측 {pred:<10} 실제 {real:<10} 같나 {pred == real}")
```

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

그림 해설.

- ★ **`bind()` 가 「어느 인자가 어느 파라미터에 앉는지」를 dict 로 보여 준다.**
  `f(1, 2, 3, kw=4, z=5)` 에서 `3` 이 `args` 로, `z` 가 `kwargs` 로 간 것이 **글자로 보인다.**
  `apply_defaults()` 를 부르면 안 준 기본값(`both=1`·`kw2='K'`)까지 채워 준다.
- ★ **네 판 모두 예측과 실제가 같았다**(`같나 True` 넷). 즉 **부르지 않고 판정할 수 있다.**
- ★★ **그런데 문구는 다르다.**

| 호출 | `bind()` 의 문구 | 실제 호출의 문구 |
|---|---|---|
| `f(1, 2)` | `missing a required argument: 'kw'` | `f() missing 1 required keyword-only argument: 'kw'` |
| `f(pos=1, kw=2)` | `'pos' parameter is positional only, but was passed as a keyword` | `f() got some positional-only arguments passed as keyword arguments: 'pos'` |

★ **판정은 같고 문구는 다르다** — `bind` 는 **순수 파이썬 구현**이고 실제 호출은 **인터프리터 C 코드**라 메시지가 따로 논다.
**문구로 두 경로를 구분할 수 있다는 뜻**이고, 동시에 **문구에 기대어 테스트를 쓰면 안 된다는 뜻**이다.

★ 이 대조가 **이 주제의 자기 채점 도구**다 — 3번·4번 절의 모든 호출을 `bind()` 로 미리 돌려 보면
**「되나 안 되나」를 실행 없이 확인**할 수 있다.

**비용** — 실행 없이 판정하고, 어디에 앉는지까지 보여 준다.\
대신 **`bind` 는 파이썬 구현이라 느리다** — 핫 경로에 넣을 것이 아니다.

## 문법 — 형태와 규칙

```python
def f(pos, /, both, *args, kw, **kwargs): ...
#     └위치전용┘ └둘다┘ └나머지위치┘ └키워드전용┘ └나머지키워드┘

def f(a, *, b): ...        # * 뒤는 키워드 전용. *args 를 안 받고 싶을 때
def f(a, /): ...           # 3.8+ (PEP 570)
def f(a, b=2): ...         # 기본값은 뒤에 몰려야 한다

f(1, 2)          f(a=1)          f(*[1, 2])        f(**{"a": 1})
f(*it)           # 아무 이터러블 · 여러 번 가능
f(**m)           # 매핑 · 여러 번 가능 · 키가 겹치면 TypeError
```

규칙 일곱.

1. **순서가 고정**이다 — 위치전용 `/` 둘다 `*args` 키워드전용 `**kwargs`.
2. **기본값 있는 위치 파라미터는 뒤에 몰려야** 한다. 어기면 `SyntaxError`.
3. **키워드 전용은 기본값이 없어도 된다** — 그러면 **필수**다.
4. **모르는 키워드는 `**kwargs` 가 있으면 통과**, 없으면 `TypeError`.
5. **같은 파라미터에 위치와 키워드를 동시에** 주면 `TypeError` — 단 그 이름이 **위치 전용이면** `**kwargs` 로 간다.
6. **`*`·`**` 로 푸는 것은 문법이지 인자가 아니다.** 빈 것을 풀면 아무 일도 안 일어난다.
7. **정의가 틀리면 `SyntaxError`(실행 전), 호출이 틀리면 `TypeError`(실행 중).**

**금지 사례 — 두 층으로 갈라 적는다**

```python
# ① 정의 시점 — SyntaxError. 프로그램이 시작조차 안 한다
def f(a=1, b): ...          # parameter without a default follows parameter with a default
def f(**kw, a): ...         # arguments cannot follow var-keyword argument
def f(*a, *b): ...          # * argument may appear only once
def f(*): ...               # named arguments must follow bare *
def f(a, /, b, /): ...      # / may appear only once
def f(/, a): ...            # at least one argument must precede /
def f(a, a): ...            # duplicate argument 'a' in function definition
f(a=1, 2)                   # positional argument follows keyword argument   ★ 호출 자리인데 SyntaxError 다
f(x=1, x=2)                 # keyword argument repeated: x
f(**kw, *args)              # iterable argument unpacking follows keyword argument unpacking

# ② 호출 시점 — TypeError. 그 줄에 닿아야 난다
f(1, 2, 3)                  # takes N positional arguments but M were given
f(pos=1)                    # got some positional-only arguments passed as keyword arguments
f()                         # missing 1 required positional argument
f(1, 2)                     # missing 1 required keyword-only argument
f(1, extra=2)               # got an unexpected keyword argument
f(1, x=2)                   # got multiple values for argument 'x'
f(*1)                       # argument after * must be an iterable, not int
f(1, **[("b", 2)])          # argument after ** must be a mapping, not list
f(1, **{1: 2})              # keywords must be strings
```

★★ **`f(a=1, 2)` 가 ①에 있는 것이 이 표의 핵심이다.**
**호출 자리에도 정의 시점 오류가 있다** — 「정의 대 호출」이 아니라 「**파서가 보는 것 대 실행이 보는 것**」이 층의 기준이다.

```text
===== 소스: ex.py =====
def f(*a, **k): pass
kw = {}; args = ()
f(**kw, *args)
```

```text
  File "<stdin>", line 3
    f(**kw, *args)
          ^^^^^^^
SyntaxError: iterable argument unpacking follows keyword argument unpacking
```

★ **`**` 뒤에 `*` 를 쓸 수 없다** — 반대 순서(`f(*args, **kw)`)는 된다. 이것도 **글자 배열의 규칙**이라 파서가 잡는다.

## 어디서 틀리나

### (1) 「인자 오류는 다 `TypeError`」로 안다

★ **`f(a=1, 2)`·`f(x=1, x=2)`·`f(**kw, *args)` 는 `SyntaxError`** 다. **호출 자리인데도** 그렇다.

### (2) 「정의는 `SyntaxError`, 호출은 `TypeError`」로 외운다

★ **기준은 「정의냐 호출이냐」가 아니라 「파서가 보느냐 실행이 보느냐」다.**
`f(a=1, 2)` 가 그 반례다.

### (3) 안 도는 가지의 잘못된 호출이 잡힐 것이라 믿는다

**안 잡힌다.** 실행돼야 검사한다. 실측에서 `f(1,2,3,4,5)` 가 `if False:` 안에 있어 **아무 일도 안 났다.**

### (4) 기본값 있는 파라미터를 앞에 둔다

`SyntaxError` 다. `__defaults__` 가 **뒤에서부터** 대응하는 튜플이라 그 규칙이 필요하다.

### (5) 키워드 전용에 기본값이 필수라고 안다

**아니다.** 기본값 없는 키워드 전용은 **필수 인자**가 된다 — `missing 1 required keyword-only argument`.

### (6) 같은 인자를 위치와 키워드로 동시에 준다

`got multiple values for argument` 다.\
★ **그 이름이 위치 전용이면 안 터진다** — `**kwargs` 로 간다. `/` 가 있는 이유다.

### (7) `**` 를 여러 번 쓰면서 키가 겹친다

**`TypeError`** 다. ★ [12번](../12-dict-and-key-requirements/2-summary.md)의 `{**a, **b}` 와 **반대다** — 그쪽은 뒤엣것이 이긴다.

### (8) `f(*[], **{})` 가 무언가를 준다고 믿는다

**아무것도 안 준다.** 「인자를 안 준 것」과 똑같다.

### (9) `__defaults__` 를 무조건 튜플로 안다

**기본값이 없으면 `None`** 이다. `len()` 을 걸면 터진다.

### (10) `co_varnames` 의 순서를 소스 순서로 안다

★ **`*args`·`**kwargs` 가 뒤로 밀린다.** 실측에서 `('pos','both','kw','kw2','args','kwargs')` 였다.

### (11) 예외 문구로 테스트를 쓴다

★ **`bind()` 와 실제 호출의 문구가 다르다.** 판정은 같고 문구는 다르다 — 문구는 보장이 아니다.

### (12) `(*args, **kwargs)` 래퍼를 남발한다

**시그니처가 사라진다.** 읽는 사람도 타입 체커도 IDE 도 무엇을 받는지 모른다.

## 구현 세부사항 대 언어 보장

세 층으로 가른다. ★ **이 주제는 「언어 보장」이 두껍다** — 문법과 인자 붙이기 규칙이 전부 레퍼런스에 있다.\
구현 쪽에 남는 것은 **진단 문구**와 **내성 속성의 모양**이다.

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **언어 보장** | 언어 레퍼런스·PEP 가 정한 것 | 공식 문서 문장을 열어서 인용 |
| **CPython 구현** | 이 구현이 그렇게 하는 것 | `__defaults__`·`co_flags`·`bind` 대조 |
| **이 판의 관찰** | 3.12.3 에서 그랬을 뿐 | 예외 문구 · 접두 |

### 언어 보장

| 사실 | 근거 |
|---|---|
| 파라미터 순서 — 위치전용 `/` 둘다 `*args` 키워드전용 `**kwargs` | 8.7 Function definitions |
| **기본값 있는 파라미터 뒤에 기본값 없는 것이 못 온다** | 8.7 — 어기면 `SyntaxError` |
| **`/` 왼쪽은 이름으로 못 준다**(3.8+) | PEP 570 |
| **`*` 오른쪽은 이름으로만 줄 수 있다**(3.0+) · 기본값이 없으면 필수 | PEP 3102 · 8.7 |
| 호출에서 **위치 인자가 키워드 인자보다 앞**에 와야 한다 | 6.3.4 Calls — 어기면 `SyntaxError` |
| **같은 파라미터에 값이 두 번 들어가면 `TypeError`** | 6.3.4 |
| **모르는 키워드는 `**kwargs` 가 없으면 `TypeError`** | 6.3.4 |
| `*expr` 는 **이터러블**, `**expr` 는 **매핑**이어야 한다 | 6.3.4 |
| `**` 로 푼 키는 **문자열**이어야 한다 | 6.3.4 |
| 기본값은 **`def` 를 실행할 때 한 번** 계산된다 | 8.7 — 정본은 [20번](../20-mutable-default-args/2-summary.md) |

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| `__defaults__` 는 **튜플**이고 뒤에서부터 대응 · 없으면 **`None`** | 실행 |
| `__kwdefaults__` 는 **dict** · 없으면 `None` | 실행 |
| `co_argcount`·`co_posonlyargcount`·`co_kwonlyargcount` 로 **개수만** 저장 | 실행 |
| `co_varnames` 에서 **`*args`·`**kwargs` 가 뒤로 밀린다** | 실행 |
| `co_flags` 의 `0x04`(`CO_VARARGS`)·`0x08`(`CO_VARKEYWORDS`) | 실행 — `0b1111` 대 `0b11` |
| **일부 `SyntaxError` 에 캐럿이 없다**(`duplicate argument`·`keyword argument repeated`) | 실행 — 파서 뒤 단계가 잡기 때문 |
| `inspect.Signature.bind` 의 **문구가 실제 호출과 다르다** | 실행 — 순수 파이썬 구현 |
| 일부 `TypeError` 문구에 **`__main__.` 접두**가 붙는다 | 실행 — 푸는 단계와 앉히는 단계가 다르다 |

### 이 판(3.12.3)의 관찰

| 관찰 | 어디가 흔들리나 |
|---|---|
| `SyntaxError`·`TypeError` **문구 전부** | 예외 **종류**는 명세지만 문구는 아니다. 판마다 손본다 |
| `__main__.f()` 접두가 붙는 줄과 안 붙는 줄 | 어느 C 코드가 냈느냐의 결과 |
| `keywords must be strings` 가 **함수 이름을 안 말하는 것** | 위와 같다 |
| 캐럿이 있는 `SyntaxError` 와 없는 것의 갈림 | 진단 표시 방식 |
| `co_flags` 가 `15`(`0b1111`)인 것 | 다른 비트가 섞여 있다 |
| `bind()` 의 문구 | 표준 라이브러리 구현 |

### 그래서 이렇게 적으면 틀린다

- ✗ 「인자 관련 오류는 전부 `TypeError`」\
  ○ **`f(a=1, 2)` 는 `SyntaxError`** 다. 호출 자리에도 정의 시점 오류가 있다.
- ✗ 「정의는 `SyntaxError`, 호출은 `TypeError`」\
  ○ 기준은 「**파서가 보느냐 실행이 보느냐**」다.
- ✗ 「`SyntaxError` 는 항상 캐럿이 나온다」\
  ○ **`duplicate argument`·`keyword argument repeated` 는 안 나온다.** 파서 뒤 단계가 잡는다.
- ✗ 「키워드 전용은 기본값이 있어야 한다」\
  ○ **없어도 된다.** 그러면 **필수**다.
- ✗ 「같은 이름을 위치와 키워드로 주면 무조건 터진다」\
  ○ **위치 전용이면 안 터진다** — `**kwargs` 로 간다. `/` 의 존재 이유다.
- ✗ 「`**` 로 두 dict 를 풀면 뒤엣것이 이긴다」\
  ○ **호출 자리에서는 `TypeError`** 다. `{**a, **b}` 와 **반대**다.
- ✗ 「`bind()` 가 실제 호출과 같은 에러를 낸다」\
  ○ **판정만 같고 문구는 다르다.**
- ✗ 「`__defaults__` 로 기본값 개수를 세면 된다」\
  ○ **없으면 `None`** 이라 `len()` 이 터진다.
- ✗ 「`dis` 나 `co_flags` 로 봤으니 어느 파이썬에서나 그렇다」\
  ○ **CPython 의 내성 인터페이스**다. 규칙은 명세, 그 저장 모양은 아니다.

**판정 기준 한 줄**: **「안 도는 가지에 넣어도 터지나」를 물으면 층이 갈리고, 「이름이 위치 전용인가」를 물으면 중복 에러가 갈린다.**

## 언제 쓰고 언제 안 쓰나

| 상황 | 판정 |
|---|---|
| 인자가 셋 이상이고 뜻이 헷갈린다 | ★ **`*` 로 키워드 전용**으로 만든다 — 호출부가 읽힌다 |
| 불리언 플래그를 받는다 | ★ **키워드 전용** — `f(x, True, False)` 는 읽을 수 없다 |
| `**kwargs` 로 임의의 키를 받는다 | ★ **앞쪽 파라미터를 `/` 로 위치 전용**으로 — 이름 충돌이 사라진다 |
| 나중에 파라미터 이름을 바꿀 수도 있다 | **`/`** — 이름이 계약에서 빠진다 |
| 래퍼·데코레이터를 쓴다 | `(*args, **kwargs)` + **`functools.wraps`**([목록의 **24번 주제**](../24-decorators/)) |
| 인자 몇 개를 미리 고정하고 싶다 | **`functools.partial`**(목록의 **45번 주제**) — 새 함수를 만들어 준다 |
| 호출 전에 되는지 알아야 한다 | **`inspect.signature().bind()`** |
| 인자가 아주 많아진다 | ★ **데이터클래스 하나로 묶는다**([목록의 **36번 주제**](../36-dataclasses/)) — 시그니처를 늘리는 것이 답이 아니다 |
| 기본값에 리스트·dict 를 쓰고 싶다 | ★ **쓰지 않는다** — [20번](../20-mutable-default-args/2-summary.md)이 정본이다 |

## 핵심 문장

- ★★ **층이 둘이다** — **파서가 보는 것은 `SyntaxError`(실행 전)**, **인자를 파라미터에 앉히는 것은 `TypeError`(실행 중)**.
  「정의냐 호출이냐」가 아니다 — **`f(a=1, 2)` 는 호출 자리인데 `SyntaxError`** 다.
- **안 도는 가지에 넣어 보면 층이 갈린다.** `SyntaxError` 는 프로그램을 못 띄우고, `TypeError` 는 아무 일도 안 난다.
- ★ **`SyntaxError` 안에서도 캐럿이 있는 것과 없는 것이 갈린다** — 이름이 겹쳤다는 판정은 **파싱을 끝내야** 알 수 있어 위치가 없다.
- **키워드 전용은 기본값이 없어도 된다** — 그러면 **필수**다.
- ★ **같은 이름을 위치와 키워드로 주면 `got multiple values` 인데, 그 이름이 위치 전용이면 `**kwargs` 로 들어간다.**
  이것이 `/` 가 존재하는 이유다(PEP 570).
- ★ **`**` 를 두 번 써서 키가 겹치면 `TypeError`** — `{**a, **b}` 와 **반대**다.
- **`f(*[], **{})` 는 인자를 안 준 것과 똑같다.** `*`·`**` 는 문법이지 인자가 아니다.
- ★ **`inspect.signature().bind()` 로 부르지 않고 판정할 수 있다** — 네 판 모두 실제와 같았다.
  **판정은 같고 문구는 다르다**(순수 파이썬 구현이라서).
- **`__defaults__` 는 뒤에서부터 대응하는 튜플**이고, 그래서 「기본값은 뒤에 몰려야 한다」는 규칙이 나온다. 없으면 **`None`** 이다.

## 관련 자료

- 목록: [python/syntax 주제 목록](../README.md) — 이 주제는 **19번**
- 정본 이웃: [20-mutable-default-args](../20-mutable-default-args/2-summary.md) — **기본값의 정본.**\
  **경계**: 「기본값이 `def` 실행 때 한 번 만들어진다」와 가변 기본값 함정·`None` 센티널은 전부 그쪽이다.
  여기는 **그 값이 `__defaults__`·`__kwdefaults__` 에 어떻게 저장되나**까지만.
- 선행: [11-tuple-and-unpacking](../11-tuple-and-unpacking/2-summary.md) — 별표 언패킹.\
  **경계**: 그쪽은 **대입문의 별표**, 여기는 **호출의 별표**다.
- 선행: [12-dict-and-key-requirements](../12-dict-and-key-requirements/2-summary.md) — `**` 가 푸는 매핑, 키가 문자열이어야 하는 것.\
  **경계**: `{**a, **b}` 의 **뒤엣것이 이기는** 규칙은 그쪽, **호출에서 겹치면 터지는** 것은 여기다.
- 함께 보는 곳: [16-iterator-protocol](../16-iterator-protocol/2-summary.md) — `f(*it)` 로 풀면 이터레이터가 **소진된다.**
- 함께 보는 곳: [18-loop-control-and-else](../18-loop-control-and-else/2-summary.md) — `'break' outside loop` 도 **캐럿 없는 `SyntaxError`** 다.
- 함께 보는 곳: [15-generator-expressions-lazy-eval](../15-generator-expressions-lazy-eval/2-summary.md) — `sum(x for x in xs, 0)` 이 `SyntaxError` 인 것이 같은 층이다.
- 이어지는 곳: [목록의 **21번 주제**](../21-scope-legb-global-nonlocal/) 「스코프 LEGB」 — 파라미터가 만드는 지역 이름.
- 이어지는 곳: [목록의 **24번 주제**](../24-decorators/) 「데코레이터」 — `(*args, **kwargs)` 래퍼와 `functools.wraps`.
- 이어지는 곳: 목록의 **40번 주제** 「타입 힌트의 런타임 의미」 — 시그니처에 붙는 주석이 **실행을 안 바꾸는** 것.
- 이어지는 곳: 목록의 **45번 주제** 「`functools`」 — `partial` 로 인자를 미리 고정하는 것.
- 기존 노트: [`cs/foundations/python-basics/`](../../../../python-basics/) — 함수를 「이렇게 정의한다」까지가 그쪽이다.\
  **경계**: 여기는 「**어떤 호출이 되고, 안 되면 언제 걸리나**」부터다.
- 공식 문서: [Function definitions](https://docs.python.org/3.12/reference/compound_stmts.html#function-definitions) · [Calls](https://docs.python.org/3.12/reference/expressions.html#calls) · [PEP 570](https://peps.python.org/pep-0570/) · [PEP 3102](https://peps.python.org/pep-3102/)

## 용어 풀이

- **파라미터(parameter)**: 정의 쪽의 이름. **인자(argument)** 는 호출 쪽의 값.\
  예: `def f(a)` 의 `a` 가 파라미터, `f(1)` 의 `1` 이 인자.
- **위치 전용(positional-only)**: `/` 의 왼쪽. **이름으로는 못 준다.** 3.8+(PEP 570).\
  예: 덕분에 `**kwargs` 에 같은 이름을 받아도 안 부딪힌다.
- **키워드 전용(keyword-only)**: `*` 나 `*args` 의 오른쪽. **이름으로만 준다.** 3.0+(PEP 3102).\
  예: 기본값이 없으면 **필수 인자**다.
- **`*args`**: 남는 위치 인자를 **튜플**로 받는 것. `co_flags` 의 `0x04`.
- **`**kwargs`**: 남는 키워드 인자를 **dict** 로 받는 것. `co_flags` 의 `0x08`.
- **푼다(unpack)**: 호출 자리의 `*`·`**`. 이터러블·매핑을 인자 목록으로 펼친다.\
  예: 빈 것을 풀면 **아무 일도 안 일어난다.**
- **`__defaults__`**: 위치 파라미터의 기본값 **튜플**. **뒤에서부터** 대응한다. 없으면 **`None`**.
- **`__kwdefaults__`**: 키워드 전용의 기본값 **dict**. 없으면 `None`.
- **`co_flags`**: 코드 객체의 비트 플래그. `0x04` 가 `*args`, `0x08` 이 `**kwargs` 유무.
- **`inspect.signature(f)`**: 시그니처를 객체로 읽는 것. `parameters` 에 종류와 기본값이 들어 있다.
- **`Signature.bind(*a, **k)`**: **부르지 않고** 인자를 파라미터에 앉혀 보는 것.\
  예: 안 맞으면 `TypeError` 를 내는데 **문구가 실제 호출과 다르다.**
- **`SyntaxError`**: 파서·컴파일러 단계의 오류. **그 줄이 안 도는 자리에 있어도** 프로그램이 시작조차 안 한다.
- **`TypeError`**: 실행 중의 오류. **그 줄에 닿아야** 난다.

## 더 들어가면

- **`functools.partial`** 은 인자 일부를 미리 고정한 **새 호출 가능 객체**를 만든다. 목록의 **45번 주제**가 정본이다.
  ★ 여기서 알 것 하나 — `partial` 로 고정한 위치 인자는 **앞에서부터** 붙으므로, 뒤쪽만 고정하려면 키워드로 줘야 한다.
- **`/` 가 생기기 전**에는 C 로 짠 내장 함수만 위치 전용이었다 — 그래서 `len(obj=[])` 가 `TypeError` 인데
  순수 파이썬으로는 같은 것을 흉내 낼 수 없었다. PEP 570 이 그 비대칭을 없앴다.
- **타입 힌트는 이 규칙을 하나도 안 바꾼다** — `def f(a: int)` 에 문자열을 줘도 **실행은 된다**(목록의 **40번 주제**).
  이 주제의 검사는 **개수와 이름**만 본다.
- **`*` 를 시그니처 중간에 나중에 넣는 것은 호환을 깬다** — 기존 호출이 위치로 주고 있었다면 전부 `TypeError` 가 된다.
  반대로 **처음부터 `*` 를 넣어 두면** 나중에 파라미터를 추가·재배치해도 안 깨진다.
- **데코레이터가 시그니처를 가린다** — `functools.wraps` 가 `__wrapped__` 를 남기고,
  `inspect.signature` 는 그것을 따라가 **원래 시그니처**를 보여 준다([목록의 **24번 주제**](../24-decorators/)).
