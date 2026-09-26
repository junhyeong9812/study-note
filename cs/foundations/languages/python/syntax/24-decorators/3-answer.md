# python/syntax/24-decorators — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> [1-question.md](1-question.md)의 번호와 **1:1**로 대응한다. 질문 12개 = 답 12개.
>
> 이 파일의 모든 출력은 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> 던지는 형태는 `python3 - <파일` 로 고정했다 — 트레이스백이 `File "<stdin>", line N` 으로 찍히고,
> **실행 중 예외라 소스 줄도 캐럿도 안 나온다.**
> ★ 이 주제의 블록에는 **주소가 한 곳도 안 찍힌다** — `is` 판정과 이름·개수만 찍게 짜서 **다시 돌려도 한 글자도 안 변한다.**
> 단 **예외 문구**와 **`WRAPPER_ASSIGNMENTS` 의 내용**은 구현·판에 달린 것이라 다른 판에서는 달라진다(12번 답).

## 정답

### 1. `@deco` 는 `f = deco(f)` 다 — 두 쪽이 똑같이 찍는다

**출력**

```python
# e24_desugar.py
def deco(fn):
    print("  deco 가 돈다:", fn.__name__)
    return fn


print("① @ 문법")


@deco
def a():
    pass


print("② 손으로 푼 것")


def b():
    pass


b = deco(b)
print("③ 둘이 같은 일인가:", a is not None and b is not None)
```

```text
===== python3 - <e24_desugar.py =====
① @ 문법
  deco 가 돈다: a
② 손으로 푼 것
  deco 가 돈다: b
③ 둘이 같은 일인가: True
(exit 0)
```

**왜 그런가**

★★ **`@deco` 는 새 문법이 아니라 줄임**이다. 레퍼런스가 등가식을 그대로 준다.

> `@f1(arg)` `@f2` `def func(): pass` is roughly equivalent to
> `def func(): pass` / `func = f1(arg)(f2(func))`
> except that the original function is not temporarily bound to the name func.

- ①에서 `@deco` 를 지나며 `deco 가 돈다: a` 가 찍혔다.
- ②에서 `b = deco(b)` 를 지나며 `deco 가 돈다: b` 가 찍혔다. **같은 일이다.**
- ③은 둘 다 멀쩡한 함수로 남았다는 확인이다.

★ **다른 점은 딱 하나**, 인용문의 `except that …` 이다 —
**`@` 쪽은 원래 함수가 이름 `a` 에 잠시도 묶이지 않는다.**

```text
   손으로 푼 쪽                       @ 로 붙인 쪽
   -----------------------            ---------------------------
   def b(): ...                       def a(): ...  (이름 a 는 아직 없다)
   -> 이름 b 가 원래 함수를 가리킴      -> 함수 객체가 곧장 deco 로 간다
   b = deco(b)                        -> 돌려받은 것이 이름 a 에 묶인다
   -> 이름 b 가 결과를 가리킴

   ★ deco 가 예외를 던지면 갈린다
     손으로 푼 쪽: 이름 b 가 원래 함수를 가리킨 채 남는다
     @ 쪽       : 이름 a 가 아예 안 생긴다
```

이것은 **언어 보장**이다(8.7 Function definitions).

### 2. 정의 시점에 한 번, 호출 시점에 부른 횟수만큼

**출력**

```python
# e24_define_time.py
def deco(fn):
    print("  [정의 시점] deco 실행 — 받은 것:", fn.__name__)

    def wrapper(*a, **k):
        print("  [호출 시점] wrapper 실행")
        return fn(*a, **k)

    return wrapper


print("① def 문을 만나기 전")


@deco
def work():
    return "결과"


print("② def 문을 지난 뒤 — 아직 한 번도 안 불렀다")
print("③ 첫 호출:", work())
print("④ 둘째 호출:", work())
```

```text
===== python3 - <e24_define_time.py =====
① def 문을 만나기 전
  [정의 시점] deco 실행 — 받은 것: work
② def 문을 지난 뒤 — 아직 한 번도 안 불렀다
  [호출 시점] wrapper 실행
③ 첫 호출: 결과
  [호출 시점] wrapper 실행
④ 둘째 호출: 결과
(exit 0)
```

**왜 그런가**

★★ **`[정의 시점]` 은 한 번, `[호출 시점]` 은 두 번**이다. 차례는 ① → 정의 → ② → 호출 → ③ → 호출 → ④.

레퍼런스가 그대로 적는다.

> Decorator expressions are evaluated when the function is defined, in the scope that contains
> the function definition. The result must be a callable, which is invoked with the function
> object as the only argument.

- **함수 몸통이 처음 도는 것은 ② 뒤**다. ①②는 아직 몸통을 한 줄도 안 돌렸다 —
  `deco` 가 받은 것은 **함수 객체**일 뿐 결과가 아니다.
- **부를 때 도는 것은 `deco` 가 아니라 `wrapper`** 다. 이 구분을 놓치면 「데코레이터가 매번 돈다」는 오해가 생긴다.

★★ **[20번](../20-mutable-default-args/2-summary.md)의 기본값이 정확히 같은 시점**이다 —
`def` 문을 **실행할 때** 한 번. **그 성질의 정본은 20번**이므로 여기서 다시 설명하지 않는다.
외울 것은 하나다 — **`def` 문은 실행되는 문장이다.**

★ 그래서 **데코레이터 안의 준비 코드는 임포트 시간에 전부 치러진다.**

### 3. 적용은 아래에서 위로, 호출은 위에서 아래로 — 여섯 줄이 대칭이다

**출력**

```python
# e24_stack_order.py
def make(tag):
    def deco(fn):
        print("  적용:", tag)

        def wrapper(*a, **k):
            print("  들어감:", tag)
            r = fn(*a, **k)
            print("  나옴  :", tag)
            return r

        return wrapper

    return deco


print("① 적용 순서 (def 문을 지날 때)")


@make("바깥")
@make("가운데")
@make("안쪽")
def f():
    print("  몸통")
    return 1


print("② 호출 순서")
f()
```

```text
===== python3 - <e24_stack_order.py =====
① 적용 순서 (def 문을 지날 때)
  적용: 안쪽
  적용: 가운데
  적용: 바깥
② 호출 순서
  들어감: 바깥
  들어감: 가운데
  들어감: 안쪽
  몸통
  나옴  : 안쪽
  나옴  : 가운데
  나옴  : 바깥
(exit 0)
```

**왜 그런가**

- `적용:` 은 **안쪽 → 가운데 → 바깥.** `def` 에 **가장 가까운 것이 먼저** 원본을 받는다.
- 호출 쪽은 **`들어감` 3줄 + `몸통` 1줄 + `나옴` 3줄 = 일곱 줄**이고,
  `들어감`·`나옴` **여섯 줄이 몸통을 가운데 두고 대칭**이다.

```text
   @바깥      <- 3번째로 적용            들어감: 바깥     1
   @가운데    <- 2번째로 적용              들어감: 가운데  2
   @안쪽      <- 1번째로 적용                들어감: 안쪽  3
   def f                                         몸통      4
                                              나옴: 안쪽   5
                                            나옴: 가운데   6
                                          나옴: 바깥       7

   결국 이 모양이다:  바깥( 가운데( 안쪽( f ) ) )
```

★★ **외우지 말고 괄호로 풀어 써라** — `@A @B def f` 는 `A(B(f))` 다.
레퍼런스의 한마디가 이것을 한꺼번에 설명한다 — *"Multiple decorators are applied in nested fashion."*

★ 그래서 **바깥에 둔 것이 먼저 보고 나중에 놓는다.** 캐시를 인증 바깥에 두느냐 안쪽에 두느냐가
「캐시된 응답도 인증을 거치나」를 통째로 가른다 — **쌓는 순서는 주석이 아니라 계약이다.**

### 4. 세 층 중 둘은 정의 시점, 하나만 호출 시점

**출력**

```python
# e24_args_deco.py
import functools


def repeat(times):
    print("  [1층] repeat 가 돈다 — times =", times)

    def deco(fn):
        print("  [2층] deco 가 돈다 — fn =", fn.__name__)

        @functools.wraps(fn)
        def wrapper(*a, **k):
            print("  [3층] wrapper 가 돈다")
            out = [fn(*a, **k) for _ in range(times)]
            return out

        return wrapper

    return deco


print("① def 문을 지난다")


@repeat(3)
def hello(name):
    return "안녕 " + name


print("② 호출한다")
print("결과:", hello("파이썬"))
```

```text
===== python3 - <e24_args_deco.py =====
① def 문을 지난다
  [1층] repeat 가 돈다 — times = 3
  [2층] deco 가 돈다 — fn = hello
② 호출한다
  [3층] wrapper 가 돈다
결과: ['안녕 파이썬', '안녕 파이썬', '안녕 파이썬']
(exit 0)
```

**왜 그런가**

- **`[1층]`·`[2층]` 은 ① 뒤**(둘 다 정의 시점), **`[3층]` 만 ② 뒤**(호출 시점)다.
- 결과는 세 번 반복된 리스트다.

```text
   @repeat(3)
   def hello(name): ...

   ① repeat(3)          -> deco 를 돌려준다       def 문을 지날 때, 즉시
   ② deco(hello)        -> wrapper 를 돌려준다    그 직후, 즉시
   ③ wrapper("파이썬")   -> 결과                  부를 때만

   인자 없는 데코레이터는 이 가운데 ①이 없는 것뿐이다.
```

★ `@` 뒤에는 **식**이 올 수 있고, `repeat(3)` 은 **먼저 계산돼** 그 결과가 데코레이터로 쓰인다.
그래서 「데코레이터를 만들어 주는 함수」가 한 겹 더 필요하다.

★★ **`times` 는 1층의 지역 이름인데 3층에서 읽힌다** — [22번](../22-closures-and-late-binding/2-summary.md)의 클로저다.
데코레이터 인자를 담아 두는 통이 **셀**이고, 그것을 직접 꺼내 본 것이 11번 답이다.

### 5. 여섯 칸 중 다섯이 바뀌고 `__module__` 만 그대로다

**출력**

```python
# e24_wraps_missing.py
def deco(fn):
    def wrapper(*a, **k):
        return fn(*a, **k)

    return wrapper


def target(a, b: int = 1) -> int:
    """이 함수가 하는 일."""
    return a + b


target.retries = 3

wrapped = deco(target)

for attr in ("__name__", "__qualname__", "__doc__", "__module__",
             "__annotations__", "__dict__"):
    print("%-15s 원본: %-34r 감싼 뒤: %r"
          % (attr, getattr(target, attr), getattr(wrapped, attr)))
print("%-15s 원본: %-34r 감싼 뒤: %r"
      % ("__wrapped__", getattr(target, "__wrapped__", "(없음)"),
         getattr(wrapped, "__wrapped__", "(없음)")))
```

```text
===== python3 - <e24_wraps_missing.py =====
__name__        원본: 'target'                           감싼 뒤: 'wrapper'
__qualname__    원본: 'target'                           감싼 뒤: 'deco.<locals>.wrapper'
__doc__         원본: '이 함수가 하는 일.'                      감싼 뒤: None
__module__      원본: '__main__'                         감싼 뒤: '__main__'
__annotations__ 원본: {'b': <class 'int'>, 'return': <class 'int'>} 감싼 뒤: {}
__dict__        원본: {'retries': 3}                     감싼 뒤: {}
__wrapped__     원본: '(없음)'                             감싼 뒤: '(없음)'
(exit 0)
```

**왜 그런가**

★★ 칸별로 갈린다 — **「전부 잃는다」가 틀린 요약**인 이유가 이 출력에 그대로 있다.

| 칸 | 원본 | 감싼 뒤 | 판정 |
|---|---|---|---|
| `__name__` | `'target'` | `'wrapper'` | **잃는다** |
| `__qualname__` | `'target'` | `'deco.<locals>.wrapper'` | **잃는다** |
| `__doc__` | 독스트링 | `None` | **잃는다** |
| `__module__` | `'__main__'` | `'__main__'` | ★ **안 잃는다** |
| `__annotations__` | `{'b': int, 'return': int}` | `{}` | **잃는다** |
| `__dict__` | `{'retries': 3}` | `{}` | **잃는다** |
| `__wrapped__` | 없다 | 없다 | ★ **애초에 없다** |

★ **같은 값이 나오는 칸은 `__module__` 이다.** 이유는 간단하다 —
**래퍼도 원본과 같은 모듈(`__main__`)에서 정의됐기 때문**이다.
`wraps` 가 지켜 준 것이 아니라 **처음부터 같은 값**이었다.
(★ 다른 모듈에서 정의된 데코레이터였으면 어땠는지는 **여기서 안 돌려 봤다.**)

★ **`__wrapped__` 는 양쪽 다 없다.** 원본에도 없던 것이라 **잃을 수가 없다** — 7번 답에서 이어진다.

★ 실무에서 이것이 물리는 자리는 늘 같다 — **`help()`·문서 생성기·로깅이 함수 이름을 `wrapper` 로 찍고,
타입 힌트를 읽는 도구가 `{}` 를 본다.** 프레임워크가 `fn.<표시>` 로 붙여 둔 표식(`__dict__`)도 사라진다.

### 6. `wraps` 가 있으면 원본 시그니처, 없으면 `(*a, **k)` — 그리고 그 이유

**출력**

```python
# e24_signature.py
import functools
import inspect


def plain_deco(fn):
    def wrapper(*a, **k):
        return fn(*a, **k)

    return wrapper


def wraps_deco(fn):
    @functools.wraps(fn)
    def wrapper(*a, **k):
        return fn(*a, **k)

    return wrapper


def target(a, b=1, *, c):
    return a + b


print("원본                :", inspect.signature(target))
print("wraps 없이 감싼 것    :", inspect.signature(plain_deco(target)))
print("wraps 로 감싼 것      :", inspect.signature(wraps_deco(target)))
print("follow_wrapped=False :", inspect.signature(wraps_deco(target), follow_wrapped=False))
print("unwrap 으로 벗기면    :", inspect.unwrap(wraps_deco(target)) is target)
print("도움말이 보는 이름    :", wraps_deco(target).__name__, "대", plain_deco(target).__name__)
```

```text
===== python3 - <e24_signature.py =====
원본                : (a, b=1, *, c)
wraps 없이 감싼 것    : (*a, **k)
wraps 로 감싼 것      : (a, b=1, *, c)
follow_wrapped=False : (*a, **k)
unwrap 으로 벗기면    : True
도움말이 보는 이름    : target 대 wrapper
(exit 0)
```

**왜 그런가**

- **`wraps` 없이 감싼 것은 `(*a, **k)`** — 래퍼가 실제로 그렇게 생겼으니 정직한 답이다.
- **`wraps` 로 감싼 것은 원본 그대로** `(a, b=1, *, c)`.
- ★★ **`follow_wrapped=False` 를 주면 `wraps` 가 있어도 다시 `(*a, **k)`** 가 된다 —
  **`wraps` 없이 감싼 줄과 같아진다.**

```text
   inspect.signature(wrapper)

     wrapper 에 __wrapped__ 가 있나?
        |                     |
        아니오                  예   (기본값 follow_wrapped=True)
        |                     |
        v                     v
     래퍼의 시그니처          __wrapped__ 를 따라가 원본을 읽는다
     (*a, **k)             (a, b=1, *, c)

   follow_wrapped=False 는 이 화살표를 끊는다 -> 다시 (*a, **k)
```

★★ **그래서 증명되는 것은 「`wraps` 가 시그니처를 복사하지 않았다」는 것**이다.
`signature` 가 **`__wrapped__` 를 따라가서** 원본을 읽어 온 것뿐이다.
`inspect.unwrap` 이 **원본 객체 자체**를 돌려주는 것(`True`)이 같은 이야기다.

★ 마지막 줄 — `wraps` 쪽은 `target`, 없는 쪽은 `wrapper` 다. **도움말이 보는 이름**이 그렇게 갈린다.

★ 주의 — **보이는 것과 실제로 되는 것은 다르다.** `signature` 가 `(a, b=1, *, c)` 라고 답해도
래퍼는 여전히 `(*a, **k)` 라 **무엇이든 받아서** 넘긴다. 실제 인자 검사는 **원본이 불릴 때** 난다
([19번](../19-function-argument-rules/2-summary.md)의 층 구분이 그대로 적용된다).

### 7. 여섯 칸은 대입, `__dict__` 한 칸은 합치기, `__wrapped__` 는 신규

**출력**

```python
# e24_wraps_present.py
import functools


def deco(fn):
    @functools.wraps(fn)
    def wrapper(*a, **k):
        return fn(*a, **k)

    return wrapper


def target(a, b: int = 1) -> int:
    """이 함수가 하는 일."""
    return a + b


target.retries = 3

wrapped = deco(target)

for attr in ("__name__", "__qualname__", "__doc__", "__module__",
             "__annotations__"):
    print("%-15s 원본: %-34r 감싼 뒤: %r"
          % (attr, getattr(target, attr), getattr(wrapped, attr)))
print("%-15s 원본: %-34s 감싼 뒤: %s"
      % ("__dict__ 키", sorted(target.__dict__), sorted(wrapped.__dict__)))
print("%-15s 감싼 뒤가 원본을 가리키나: %s"
      % ("__wrapped__", wrapped.__wrapped__ is target))
print("옮기는 목록 WRAPPER_ASSIGNMENTS:", functools.WRAPPER_ASSIGNMENTS)
print("합치는 목록 WRAPPER_UPDATES    :", functools.WRAPPER_UPDATES)
```

```text
===== python3 - <e24_wraps_present.py =====
__name__        원본: 'target'                           감싼 뒤: 'target'
__qualname__    원본: 'target'                           감싼 뒤: 'target'
__doc__         원본: '이 함수가 하는 일.'                      감싼 뒤: '이 함수가 하는 일.'
__module__      원본: '__main__'                         감싼 뒤: '__main__'
__annotations__ 원본: {'b': <class 'int'>, 'return': <class 'int'>} 감싼 뒤: {'b': <class 'int'>, 'return': <class 'int'>}
__dict__ 키      원본: ['retries']                        감싼 뒤: ['__wrapped__', 'retries']
__wrapped__     감싼 뒤가 원본을 가리키나: True
옮기는 목록 WRAPPER_ASSIGNMENTS: ('__module__', '__name__', '__qualname__', '__doc__', '__annotations__', '__type_params__')
합치는 목록 WRAPPER_UPDATES    : ('__dict__',)
(exit 0)
```

**왜 그런가**

`functools` 문서가 목록으로 준다.

> The default values for these arguments are the module level constants WRAPPER_ASSIGNMENTS
> (which assigns to the wrapper function's `__module__`, `__name__`, `__qualname__`,
> `__annotations__`, `__type_params__`, and `__doc__`) and WRAPPER_UPDATES (which updates the
> wrapper function's `__dict__`). … this function automatically adds a `__wrapped__` attribute
> to the wrapper that refers to the function being wrapped.

- **잃는 것을 이름으로 전부** 대면 — `__name__` · `__qualname__` · `__doc__` · `__annotations__` · `__dict__`.
  ★ **`__module__` 은 빼야 한다**(래퍼도 같은 모듈이라 원래 같았다 — 5번 답).
- ★ **`__wrapped__` 를 「잃는 것」에 넣으면 틀린다** — **원본에도 없던 것**이고,
  `wraps` 가 **새로 만들어 붙이는** 것이다(3.2+). 출력에서 래퍼의 `__dict__` 키에 `__wrapped__` 가 들어 있는 것이 그 증거다 —
  특별한 슬롯이 아니라 **그냥 속성 하나**다.
- ★ **`__dict__` 만 다른 방식인 것을 말해 주는 상수는 `WRAPPER_UPDATES`** 다. 출력에 `('__dict__',)` 하나로 찍혔다.
  나머지 여섯은 `WRAPPER_ASSIGNMENTS` 로 **대입**된다.

`update` 라는 말이 정확히 무엇을 뜻하는지는 따로 돌려 봤다.

```python
# e24_wraps_dict.py
import functools


def deco(fn):
    @functools.wraps(fn)
    def wrapper(*a, **k):
        return fn(*a, **k)

    wrapper.added_by_wrapper = "래퍼가 나중에 붙인 것"
    return wrapper


def target(a):
    return a


target.retries = 3
target.owner = "billing"

wrapped = deco(target)
print("원본 __dict__ 키 :", sorted(target.__dict__))
print("래퍼 __dict__ 키 :", sorted(wrapped.__dict__))
print("같은 dict 객체인가:", wrapped.__dict__ is target.__dict__)
print("원본에도 번졌나  :", "added_by_wrapper" in target.__dict__)
print("원본 retries 값  :", target.retries, "· 래퍼 retries 값:", wrapped.retries)
wrapped.retries = 99
print("래퍼 쪽만 바꾸면 — 원본:", target.retries, "· 래퍼:", wrapped.retries)
```

```text
===== python3 - <e24_wraps_dict.py =====
원본 __dict__ 키 : ['owner', 'retries']
래퍼 __dict__ 키 : ['__wrapped__', 'added_by_wrapper', 'owner', 'retries']
같은 dict 객체인가: False
원본에도 번졌나  : False
원본 retries 값  : 3 · 래퍼 retries 값: 3
래퍼 쪽만 바꾸면 — 원본: 3 · 래퍼: 99
(exit 0)
```

```text
   target.__dict__                  wrapper.__dict__
   +-------------------+            +-----------------------+
   | retries: 3        | --복사-->  | retries: 3            |
   | owner : 'billing' | --복사-->  | owner  : 'billing'    |
   +-------------------+            | added_by_wrapper: ... |  <- 래퍼만 갖는다
                                    | __wrapped__: target   |  <- wraps 가 붙였다
                                    +-----------------------+

   ★ 화살표는 한 방향이고 감쌀 때 딱 한 번이다. 그 뒤로 둘은 남남이다.
```

- **같은 dict 객체가 아니다**(`False`).
- **래퍼가 나중에 붙인 것은 원본에 안 번진다.**
- **래퍼 쪽 값을 바꿔도 원본은 `3` 그대로다.**

★ 그래서 **감싼 뒤에 원본에 붙인 표시는 래퍼에 안 보인다.** 복사는 **감쌀 때 한 번뿐**이다.
★ 얕은 복사라 **값이 가변 객체면 둘이 같은 객체를 가리킨다**([03번](../03-mutability-and-copying/2-summary.md)).

### 8. 정의 때 조용히 지나가고, 두 번째 호출에서 엉뚱한 줄이 터진다

**출력**

```python
# e24_missing_call.py
import functools


def repeat(times):
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*a, **k):
            return [fn(*a, **k) for _ in range(times)]

        return wrapper

    return deco


@repeat
def hello(name):
    return "안녕 " + name


print("hello 의 정체 :", hello.__name__, "·", type(hello).__name__)
print("한 번 부르면  :", hello("파이썬").__qualname__)
print("그것을 또 부르면 —")
hello("파이썬")()
```

```text
===== python3 - <e24_missing_call.py =====
hello 의 정체 : deco · function
한 번 부르면  : repeat.<locals>.deco.<locals>.wrapper
그것을 또 부르면 —
Traceback (most recent call last):
  File "<stdin>", line 23, in <module>
  File "<stdin>", line 8, in wrapper
TypeError: 'function' object cannot be interpreted as an integer
(exit 1)
```

**왜 그런가**

★ **정의하는 순간에는 아무 일도 안 난다.** 그게 이 실수의 고약한 점이다.

```text
   @repeat            -> repeat(hello) 가 불린다
   def hello(...)        times 자리에 hello 함수가 들어앉는다
                         돌려받은 것은 deco 다 -> 이름 hello 가 deco 를 가리킨다

   hello("파이썬")     -> deco(fn="파이썬") 이 불린다 -> wrapper 를 돌려준다
                         ★ 여기서도 안 터진다 (에러가 아니라 함수가 나온다)

   그것을 또 부르면     -> wrapper 안에서 range(times) 를 하는데 times 가 함수다
                      -> TypeError: 'function' object cannot be interpreted as an integer
```

- `hello.__name__` 이 **`deco`** 다 — **이름만 찍어 봐도 어긋난 것이 보인다.**
- 한 번 불렀더니 나온 것은 `repeat.<locals>.deco.<locals>.wrapper` — **함수**다.
- 예외는 **두 번째 호출**에서, **`range(times)` 를 쓰는 줄**에서 났다(`line 8`).
  ★★ **틀린 곳(`@repeat` 줄)과 터지는 곳(`range` 줄)이 다르다.**

★ **진단법** — 데코레이터를 붙인 뒤 `f.__name__` 을 찍어 봐라.
`wraps` 를 제대로 쓴 데코레이터라면 **원래 이름**이 나와야 한다.

### 9. 정의는 통과하고, 부를 때 `not callable` 이 난다

**출력**

```python
# e24_returns_nonfunction.py
def to_string(fn):
    return "함수가 아니라 문자열을 돌려줬다"


@to_string
def f():
    return 1


print("f 는 무엇인가:", repr(f), "· 타입:", type(f).__name__)
f()
```

```text
===== python3 - <e24_returns_nonfunction.py =====
f 는 무엇인가: '함수가 아니라 문자열을 돌려줬다' · 타입: str
Traceback (most recent call last):
  File "<stdin>", line 11, in <module>
TypeError: 'str' object is not callable
(exit 1)
```

**왜 그런가**

- ★ **정의는 통과한다.** `f` 가 그냥 **문자열**이 됐다(`type` 이 `str`).
- `f()` 하는 순간 `TypeError: 'str' object is not callable`.

★★ 레퍼런스의 "The result must be a callable, which is invoked with the function object as the only argument"
는 **데코레이터 자리에 오는 것**에 대한 제약이다 — **`@` 뒤의 식이 호출 가능해야** 한다는 말이지,
**그것이 돌려주는 값**에 대한 말이 아니다. 돌려주는 값은 **검사되지 않는다.**

★ **가장 흔한 형태는 `return` 을 빼먹는 것**이다 — 그러면 `None` 이 돌아가
`'NoneType' object is not callable` 이 난다. **같은 사고의 다른 얼굴**이다.
★ 래퍼 안에서 `return` 을 빼먹는 것은 더 나쁘다 — **예외도 없이 모든 호출이 `None` 을 돌려준다.**

### 10. 체인 길이는 2, `unwrap` 은 끝까지 따라간다

**출력**

```python
# e24_unwrap_chain.py
import functools
import inspect


def tag(label):
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*a, **k):
            return label + ":" + fn(*a, **k)

        return wrapper

    return deco


@tag("바깥")
@tag("안쪽")
def base():
    return "몸통"


print("결과            :", base())
print("__name__        :", base.__name__)
print("한 겹 벗기면     :", base.__wrapped__.__name__, base.__wrapped__())
print("두 겹 벗기면     :", base.__wrapped__.__wrapped__())
print("inspect.unwrap  :", inspect.unwrap(base)())
depth = 0
f = base
while hasattr(f, "__wrapped__"):
    f = f.__wrapped__
    depth += 1
print("체인 길이        :", depth, "· 맨 밑:", f.__qualname__)
```

```text
===== python3 - <e24_unwrap_chain.py =====
결과            : 바깥:안쪽:몸통
__name__        : base
한 겹 벗기면     : base 안쪽:몸통
두 겹 벗기면     : 몸통
inspect.unwrap  : 몸통
체인 길이        : 2 · 맨 밑: base
(exit 0)
```

**왜 그런가**

```text
   base ---__wrapped__---> (안쪽 wrapper) ---__wrapped__---> 원래 base
     ^                           ^                              ^
     바깥 wrapper                한 겹 벗긴 것                    맨 밑

   inspect.unwrap(base) 는 이 화살표를 끝까지 따라간다  -> 체인 길이 2
```

- `base()` 가 `바깥:안쪽:몸통` 을 냈다 — **바깥이 먼저 손대고 안쪽이 나중**(3번 답의 순서 그대로).
- **`__wrapped__` 를 두 번** 따라가야 원본에 닿는다. `inspect.unwrap` 은 그 일을 한 번에 한다.
- 체인 길이가 `2`, 맨 밑의 `__qualname__` 이 `base` 다.

★ **`unwrap` 으로 꺼낸 함수를 그냥 부르면 래퍼가 하던 일이 전부 사라진다** —
로그도 캐시도 인증도 안 걸리고 여기서는 `바깥:`·`안쪽:` 접두가 안 붙는다.
**들여다보는 도구**이지 **부르는 도구**가 아니다.

★ **겹 중 하나가 `wraps` 를 안 붙였으면 거기서 체인이 끊긴다** — `__wrapped__` 가 없으니
`unwrap` 이 그 자리에서 멈춘다. 체인은 **겹마다 `wraps` 를 붙였을 때만** 끝까지 이어진다.

### 11. 실체는 22번의 셀이다 — `fn` 셀이 곧 `__wrapped__` 가 가리키는 것

**출력**

```python
# e24_closure_view.py
import functools


def limit(n):
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*a, **k):
            return fn(*a, **k)[:n]

        return wrapper

    return deco


@limit(2)
def letters():
    return ["a", "b", "c", "d"]


print("결과:", letters())
print("co_freevars      :", letters.__code__.co_freevars)
print("셀 개수          :", len(letters.__closure__))
cells = dict(zip(letters.__code__.co_freevars, letters.__closure__))
print("fn 셀이 가리키는 것:", cells["fn"].cell_contents.__name__)
print("n 셀이 가리키는 것 :", cells["n"].cell_contents)
print("__wrapped__ 와 같나:", cells["fn"].cell_contents is letters.__wrapped__)
```

```text
===== python3 - <e24_closure_view.py =====
결과: ['a', 'b']
co_freevars      : ('fn', 'n')
셀 개수          : 2
fn 셀이 가리키는 것: letters
n 셀이 가리키는 것 : 2
__wrapped__ 와 같나: True
(exit 0)
```

**왜 그런가**

- `co_freevars` 가 **`('fn', 'n')`** — 래퍼가 바깥에서 빌려 쓰는 이름이 **정확히 둘**이다.
- **셀은 2개.** `fn` 셀에 원본 함수가, `n` 셀에 `2` 가 들어 있다.
- ★★ **`fn` 셀의 내용과 `__wrapped__` 는 같은 객체다**(`True`).
  **`__wrapped__` 는 그 셀을 밖에서 읽게 해 주는 손잡이**인 셈이다.

```text
     letters (이름)
        |
        v
     wrapper 함수 객체
        __code__.co_freevars = ('fn', 'n')
        __closure__ = ( 셀A , 셀B )
                         |      |
                         v      v
                    원래 letters  2
                         ^
                         __wrapped__ 도 여기를 가리킨다 (같은 객체)
```

★ 한 줄로 이으면 — **데코레이터는 「바깥 함수의 지역 이름을 안쪽 함수가 계속 읽는 것」,
즉 [22번](../22-closures-and-late-binding/2-summary.md)의 클로저를 쓰는 한 가지 형태일 뿐**이다.
새 저장소는 없다. 데코레이터 인자(`n`)도 원본(`fn`)도 **전부 셀에 들어 있다.**

★★ **단 `__closure__`·`co_freevars` 는 CPython 구현이다.** 클로저가 있다는 것은
[21번](../21-scope-legb-global-nonlocal/2-summary.md)의 이름 해소 규칙이 보장하지만,
**그것이 「셀」이라는 객체로 보이는 것은 이 구현의 사정**이다. 셀의 정본은 22번이다.

★ 부수 효과 하나 — **셀이 원본을 붙들고 있으므로 감싼 쪽이 살아 있는 한 원본도 산다.**

### 12. 세 층과 이웃 경계

**세 층 가르기**

| 층 | 이 주제에서 |
|---|---|
| **언어 보장** | `@deco` 가 `f = deco(f)` 와 같다는 등가식과 **「이름에 잠시도 안 묶인다」** · **정의 시점 평가** · **중첩 적용** · 데코레이터 자리는 **호출 가능**해야 한다 · 클래스에도 같은 문법(8.8) · `wraps` 의 `WRAPPER_ASSIGNMENTS`/`WRAPPER_UPDATES`/`__wrapped__`(문서) · `signature` 가 `__wrapped__` 를 따라간다 |
| **CPython 구현** | `__closure__` 가 **셀 튜플**이고 `co_freevars` 에 이름이 있다 · `__qualname__` 이 `deco.<locals>.wrapper` 꼴 · 예외 **문구**(`'function' object cannot be interpreted as an integer` · `'str' object is not callable`) · `__wrapped__` 가 래퍼의 `__dict__` 키로 보이는 것 |
| **이 판(3.12.3)의 관찰** | `WRAPPER_ASSIGNMENTS` 가 **여섯 개**이고 `__type_params__` 를 포함하는 것(3.12 의 타입 파라미터 문법 PEP 695 — **다른 판은 안 돌려 봤다**) · `WRAPPER_UPDATES` 가 `('__dict__',)` 하나인 것 · `__module__` 이 양쪽 다 `'__main__'` 인 것(**같은 파일에서 정의했기 때문**) |

★ **가장 자주 뒤섞는 자리** — 「클로저가 있다」는 보장, 「셀이 2개다」는 구현.
둘을 같은 문장에 쓰지 마라.

**「`def` 문이 돌 때 한 번」의 경계**

★ 한 줄로 긋는다 — **「데코레이터가 정의 시점에 한 번 돈다」까지가 24번, 「그 시점에 만들어진 값이 호출 사이에 어떻게 되나」부터가 [20번](../20-mutable-default-args/2-summary.md)이다.**

- 20번은 **기본값 객체 하나가 호출 사이에 공유되는 것**(가변 기본값 함정과 `None` 센티널)이 본체다.
- 24번은 **그 시점에 데코레이터가 불려 이름이 갈아 끼워지는 것**이 본체다.
- ★ **같은 시점, 다른 질문**이다. 그래서 이 주제는 「`def f(x=[])` 는 왜 나쁜가」에 답하지 않는다.

**클래스 데코레이터**

```python
# e24_class_deco.py
def tag(cls):
    cls.tagged = True
    return cls


@tag
class C:
    pass


print("클래스도 같은 문법으로 감싼다:", C.tagged, "· 타입:", type(C).__name__)
```

```text
===== python3 - <e24_class_deco.py =====
클래스도 같은 문법으로 감싼다: True · 타입: type
(exit 0)
```

★ **문법은 똑같다.** 받는 것이 함수 객체 대신 **클래스 객체**일 뿐이고, 돌려준 것이 그 이름에 묶인다(2.6+).

★ **여기서는 이름만 세운다** — 클래스 쪽 정본은 `[목록의 **29번 주제**](../29-classes-and-attribute-lookup/)`(클래스 기초)와
`[목록의 **33번 주제**](../33-property-descriptor-slots/)`(디스크립터·속성)다. `functools.lru_cache`·`cached_property` 는 `목록의 **45번 주제**` 다.

★ 다른 이웃과의 경계도 한 줄씩.

| 주제 | 경계 |
|---|---|
| [19번](../19-function-argument-rules/2-summary.md) | 「어떤 호출이 되나」는 그쪽, 「감싼 뒤에도 그 시그니처가 보이나」는 여기 |
| [20번](../20-mutable-default-args/2-summary.md) | **「`def` 문이 돌 때 한 번」의 정본**은 그쪽, 여기는 그 시점을 빌려 쓰는 것 |
| [21번](../21-scope-legb-global-nonlocal/2-summary.md) | 데코레이터 식이 **정의를 감싸는 스코프**에서 평가된다는 것이 그 규칙의 적용 |
| [22번](../22-closures-and-late-binding/2-summary.md) | **셀의 정본**은 그쪽, 여기는 래퍼의 셀 둘을 꺼내 보는 것까지 |
| [23번](../23-lambda-and-higher-order-functions/2-summary.md) | 데코레이터는 **고차 함수에 문법 설탕이 붙은 것** |
| `목록의 **45번 주제**` | `lru_cache`·`cached_property`·`partial` 은 그쪽 |

## 실행 검증

이 문서와 [2-summary.md](2-summary.md)에 실린 출력은 전부 아래처럼 돌려서 얻었다.

| 무엇을 | 어떻게 | 몇 번 | 어디에 |
|---|---|---|---|
| 판·구현·플랫폼 확인 | `python3 - <v_version.py` · 3.12.3 | 1회 | 2-summary 머리말 뒤 |
| `@deco` 대 `f = deco(f)` | `python3 - <ex.py` · 3.12.3 | 1회 | 1번 답 |
| 정의 시점 대 호출 시점 | 〃 | 1회 | 2번 답 |
| 기본 데코레이터(`*args`·`**kwargs`) | 〃 | 1회 | 2-summary 동작 3 |
| 세 겹 스택 순서 | 〃 | 1회 | 3번 답 |
| 인자 있는 데코레이터 3층 | 〃 | 1회 | 4번 답 |
| `wraps` 없이 일곱 칸 | 〃 | 1회 | 5번 답 |
| `wraps` 있이 일곱 칸 + 두 상수 | 〃 | 1회 | 7번 답 |
| `__dict__` 가 합쳐지는 것 | 〃 | 1회 | 7번 답 |
| `signature` 네 판 + `unwrap` | 〃 | 1회 | 6번 답 |
| 괄호 빠뜨림(`TypeError`) | 〃 | 1회 | 8번 답 |
| 함수 아닌 것 돌려주기(`TypeError`) | 〃 | 1회 | 9번 답 |
| `__wrapped__` 체인 두 겹 | 〃 | 1회 | 10번 답 |
| 셀·`co_freevars` | 〃 | 1회 | 11번 답 |
| 클래스 데코레이터 | 〃 | 1회 | 12번 답 |

★ **블록은 전부 캡처 파일에서 그대로 붙였다** — 사람이 출력을 옮겨 적은 자리가 없다.\
★ **예외로 끝나는 블록 둘**(8·9번 답)은 `print` 한 줄들 뒤에 트레이스백이 온다 —
CPython 이 종료 전에 stdout 을 flush 해 **파이프로 받아도 순서가 유지된다.**

**구현 의존 항목 — 버전이 오르면 다시 돌려야 할 것**

- **`WRAPPER_ASSIGNMENTS` 의 내용**(7번 답) — 이 판은 여섯 개이고 `__type_params__` 를 포함한다.
  **다른 판은 안 돌려 봤다.**
- **예외 문구**(8·9번 답) — 종류는 명세, 문구는 아니다.
- **`__qualname__` 표기**(8번 답의 `repeat.<locals>.deco.<locals>.wrapper`) — CPython 이 정하는 형식.
- **`__closure__`·`co_freevars`**(11번 답) — CPython 의 내성 인터페이스다. 클로저는 명세, 셀의 모양은 아니다.
- **`__module__` 이 양쪽 다 `'__main__'` 인 것**(5번 답) — 같은 파일에서 정의한 결과다.
  다른 모듈에서 정의한 데코레이터는 **안 돌려 봤다.**
