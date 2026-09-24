# python/syntax/27-exception-groups-and-except-star — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> [1-question.md](1-question.md)의 번호와 **1:1**로 대응한다. 질문 12개 = 답 12개.
>
> 이 파일의 모든 출력은 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> 던지는 형태는 `python3 - <파일` 로 고정했다 — 트레이스백이 `File "<stdin>", line N` 으로 찍힌다.
> ★★ **`SyntaxError` 둘은 각각 따로 던져 캡처했다**(6번) — 한 블록에 묶으면 둘 중 하나가 반드시 거짓이 된다.
> ★ 이 파일의 블록에는 **주소도 시간도 한 곳도 안 찍힌다** — 같은 판에서 다시 돌리면 **한 글자도 안 변한다.**
> 단 **괘선 트레이스백의 모양**과 **예외·`SyntaxError` 문구**는 구현·판에 달린 것이다(12번 답).

## 정답

### 1. 트리는 다섯 줄 — 자식은 3, 잎은 4다

**출력**

```python
# e27_tree_walk.py
eg = ExceptionGroup("작업 넷이 깨졌다", [
    ValueError("v1"),
    TypeError("t1"),
    ExceptionGroup("안쪽 묶음", [KeyError("k1"), ValueError("v2")]),
])


def walk(exc, depth=0):
    pad = "    " * depth
    if isinstance(exc, BaseExceptionGroup):
        print("%s+ %s: %s  (자식 %d)"
              % (pad, type(exc).__name__, exc.args[0], len(exc.exceptions)))
        for child in exc.exceptions:
            walk(child, depth + 1)
    else:
        print("%s- %s: %s" % (pad, type(exc).__name__, exc))


def leaves(exc):
    if isinstance(exc, BaseExceptionGroup):
        return [leaf for child in exc.exceptions for leaf in leaves(child)]
    return [exc]


walk(eg)
print()
print("exceptions 의 타입 :", type(eg.exceptions).__name__)
print("맨 위 자식 수      :", len(eg.exceptions))
print("잎(진짜 예외) 수   :", len(leaves(eg)))
print("잎 목록            :", [type(e).__name__ for e in leaves(eg)])
```

```text
===== python3 - <e27_tree_walk.py =====
+ ExceptionGroup: 작업 넷이 깨졌다  (자식 3)
    - ValueError: v1
    - TypeError: t1
    + ExceptionGroup: 안쪽 묶음  (자식 2)
        - KeyError: 'k1'
        - ValueError: v2

exceptions 의 타입 : tuple
맨 위 자식 수      : 3
잎(진짜 예외) 수   : 4
잎 목록            : ['ValueError', 'TypeError', 'KeyError', 'ValueError']
(exit 0)
```

**왜 그런가**

```text
   ExceptionGroup("작업 넷이 깨졌다")        <- +  (자식 3)
   ├── ValueError("v1")                      <- -  잎
   ├── TypeError("t1")                       <- -  잎
   └── ExceptionGroup("안쪽 묶음")            <- +  (자식 2) — 잎이 아니다
       ├── KeyError("k1")                    <- -  잎
       └── ValueError("v2")                  <- -  잎
```

- 트리 그림은 **다섯 줄**이다. 묶음에는 `+`, 잎에는 `-` 를 붙였고 깊이마다 네 칸씩 들여썼다.
- ★★ **자식 수 3 과 잎 수 4 가 다르다.** 셋째 자식이 **또 묶음**이기 때문이다.
  **`len(eg.exceptions)` 를 「실패 개수」로 읽으면 틀린다.**
- **`exceptions` 는 튜플**이다 — 불변이고 순서가 보존된다.
- 잎을 세려면 **재귀**가 필요하다. 이 구분이 이 주제 내내 쓰인다.

### 2. 세 갈래가 전부 돈다 — 받는 것도 전부 `ExceptionGroup` 이다

**출력**

```python
# e27_except_star.py
def make():
    return ExceptionGroup("작업 넷이 깨졌다", [
        ValueError("v1"),
        TypeError("t1"),
        ExceptionGroup("안쪽 묶음", [KeyError("k1"), ValueError("v2")]),
    ])


order = []
try:
    raise make()
except* ValueError as group:
    order.append("ValueError")
    print("[ValueError 갈래] 받은 것:", type(group).__name__,
          "· 자식", len(group.exceptions))
    print("    잎:", sorted(str(e) for e in group.exceptions
                            if not isinstance(e, BaseExceptionGroup)))
except* TypeError as group:
    order.append("TypeError")
    print("[TypeError 갈래] 받은 것:", type(group).__name__,
          "· 잎:", [str(e) for e in group.exceptions])
except* KeyError as group:
    order.append("KeyError")
    print("[KeyError 갈래] 받은 것:", type(group).__name__,
          "· 자식", len(group.exceptions))

print("돈 갈래:", order, "— 한 try 문에서", len(order), "번 돌았다")
```

```text
===== python3 - <e27_except_star.py =====
[ValueError 갈래] 받은 것: ExceptionGroup · 자식 2
    잎: ['v1']
[TypeError 갈래] 받은 것: ExceptionGroup · 잎: ['t1']
[KeyError 갈래] 받은 것: ExceptionGroup · 자식 1
돈 갈래: ['ValueError', 'TypeError', 'KeyError'] — 한 try 문에서 3 번 돌았다
(exit 0)
```

**왜 그런가**

레퍼런스가 규칙을 적는다.

> Each `except*` clause is executed at most once, and handles all the exceptions that match its type.

- ★★ **한 `try` 문에서 세 갈래가 전부 돌았다** — 마지막 줄이 `['ValueError', 'TypeError', 'KeyError']` 다.
  **파이썬에서 절 하나가 여러 번 도는 자리는 여기뿐**이다.
- ★ **각 갈래가 받는 `group` 의 타입이 전부 `ExceptionGroup`** 이다. 잎 하나가 와도 **묶음으로 포장**된다.
- ★★ **`ValueError` 갈래의 자식이 2 인데 잎 목록은 `['v1']` 하나**다.
  나머지 하나가 **`안쪽 묶음` 을 감싼 채** 들어 있기 때문이다 — **중첩이 보존된다.**

```text
   원래                          ValueError 갈래가 받은 것
   작업 넷이 깨졌다 (3)           작업 넷이 깨졌다 (2)
   ├── ValueError v1      ──>    ├── ValueError v1
   ├── TypeError  t1             └── 안쪽 묶음 (1)
   └── 안쪽 묶음 (2)                  └── ValueError v2
       ├── KeyError   k1
       └── ValueError v2      ──>  ★ 경로가 그대로 복사된다
```

### 3. `except ExceptionGroup` 쪽만 돈다 — ②까지 찍힌다

**출력**

```python
# e27_except_plain.py
eg = ExceptionGroup("작업 넷이 깨졌다", [
    ValueError("v1"),
    TypeError("t1"),
])

print("① 별 없는 except 로 같은 것을 잡아 본다")
try:
    raise eg
except ValueError:
    print("  [ValueError 갈래] — 안 돈다")
except ExceptionGroup as g:
    print("  [ExceptionGroup 갈래] 통째로 하나 잡았다:", type(g).__name__,
          "· 자식", len(g.exceptions))
print("② 별 없는 except 는 갈래가 하나만 돈다")
```

```text
===== python3 - <e27_except_plain.py =====
① 별 없는 except 로 같은 것을 잡아 본다
  [ExceptionGroup 갈래] 통째로 하나 잡았다: ExceptionGroup · 자식 2
② 별 없는 except 는 갈래가 하나만 돈다
(exit 0)
```

**왜 그런가**

- ★ **`except ValueError` 갈래는 안 돈다.** 묶음 안에 `ValueError` 가 있어도
  별 없는 `except` 는 **묶음 자체의 타입**에만 맞춘다.
- `except ExceptionGroup` 이 **통째로 하나** 잡았다(자식 2). 갈래는 **한 번**만 돈다.
- ②까지 찍혔다 — **아무것도 밖으로 안 나갔다.**

★ **그래서 `TaskGroup` 을 쓰는 코드를 기존 `except ValueError` 로 받으면 안 걸린다**(10번 답).

### 4. 마지막 줄이 안 찍힌다 — 남은 것이 구조째 올라간다

**출력**

```python
# e27_leftover.py
import sys

eg = ExceptionGroup("작업 셋이 깨졌다", [
    ValueError("v1"),
    ExceptionGroup("안쪽 묶음", [KeyError("k1"), ValueError("v2")]),
])

print("ValueError 만 잡는다 — KeyError 는 아무도 안 잡는다", file=sys.stderr)
try:
    raise eg
except* ValueError as group:
    print("  [ValueError 갈래] 자식", len(group.exceptions), file=sys.stderr)
print("  이 줄은 안 돈다", file=sys.stderr)
```

```text
===== python3 - <e27_leftover.py =====
ValueError 만 잡는다 — KeyError 는 아무도 안 잡는다
  [ValueError 갈래] 자식 2
  + Exception Group Traceback (most recent call last):
  |   File "<stdin>", line 10, in <module>
  | ExceptionGroup: 작업 셋이 깨졌다 (1 sub-exception)
  +-+---------------- 1 ----------------
    | ExceptionGroup: 안쪽 묶음 (1 sub-exception)
    +-+---------------- 1 ----------------
      | KeyError: 'k1'
      +------------------------------------
(exit 1)
```

**왜 그런가**

- **`ValueError` 갈래는 돌았다**(자식 2). 그런데 **그 뒤 줄이 안 찍혔다.**
- ★★ 안 잡힌 `KeyError` 가 **묶음으로 다시 포장돼** 올라갔다.
  트레이스백에서 **바깥 묶음 → 안쪽 묶음 → `KeyError`** 로 **중첩 깊이 2** 가 그대로 살아 있고,
  양쪽 다 **`(1 sub-exception)`** 이다.
- 견주면 이렇다.

```text
   원래                         남은 것
   작업 셋이 깨졌다 (2)          작업 셋이 깨졌다 (1)
   ├── ValueError v1     ──잡힘──> (없다)
   └── 안쪽 묶음 (2)             └── 안쪽 묶음 (1)
       ├── KeyError k1               └── KeyError k1   <- ★ 경로가 보존된다
       └── ValueError v2   ──잡힘──> (없다)
```

- **없어진 것은 잡힌 잎 둘**이고, **남은 것은 경로와 메시지**다. 개수만 줄었다 — **가지치기**다.
- ★ 그래서 **`except*` 하나로는 대개 모자란다.** 남는 것을 밖에서 받을 계획이 필요하다.

### 5. 자식은 둘 — 새 예외가 1번 칸, 안 잡힌 `TypeError` 가 2번 칸이다

**출력**

```python
# e27_raise_inside.py
import sys


def body():
    raise ExceptionGroup("원래 묶음", [ValueError("v1"), TypeError("t1")])


print("① except* 안에서 새 예외를 raise 하면", file=sys.stderr)
try:
    body()
except* ValueError:
    raise RuntimeError("갈래가 낸 새 예외")
```

```text
===== python3 - <e27_raise_inside.py =====
① except* 안에서 새 예외를 raise 하면
  | ExceptionGroup:  (2 sub-exceptions)
  +-+---------------- 1 ----------------
    | Exception Group Traceback (most recent call last):
    |   File "<stdin>", line 10, in <module>
    |   File "<stdin>", line 5, in body
    | ExceptionGroup: 원래 묶음 (1 sub-exception)
    +-+---------------- 1 ----------------
      | ValueError: v1
      +------------------------------------
    | 
    | During handling of the above exception, another exception occurred:
    | 
    | Traceback (most recent call last):
    |   File "<stdin>", line 12, in <module>
    | RuntimeError: 갈래가 낸 새 예외
    +---------------- 2 ----------------
    | Exception Group Traceback (most recent call last):
    |   File "<stdin>", line 10, in <module>
    |   File "<stdin>", line 5, in body
    | ExceptionGroup: 원래 묶음 (1 sub-exception)
    +-+---------------- 1 ----------------
      | TypeError: t1
      +------------------------------------
(exit 1)
```

**왜 그런가**

- 맨 위 묶음의 자식은 **둘**이다(`ExceptionGroup:  (2 sub-exceptions)` — 메시지는 비어 있다).
- **1번 칸**이 `ValueError` 갈래에서 일어난 일이다. 원래 묶음(`ValueError: v1`)을 처리하다가
  `RuntimeError` 가 났고, 둘이 [25번](../25-exceptions-and-finally/2-summary.md)의
  **`During handling of the above exception, another exception occurred:`** 로 이어져 있다 —
  `from` 을 안 썼으니 **자동 연쇄**(`__context__`)다.
- ★ 그 연쇄 문구 위아래에 **`    | ` 만 있는 줄이 두 개** 있다. 괘선 안의 빈 줄이고,
  **한 글자도 손대면 안 되는 자리**다.
- **2번 칸**은 **아무도 안 잡은 `TypeError`** 다. 새 예외와 **나란히** 담겼다.
- ★★ 그래서 「바꿔치기」가 아니라 「**보태기**」다. 갈래가 던진 새 예외와 안 잡힌 나머지가
  **같은 봉투에** 들어간다 — **아무것도 안 잃는다**는 이 문법의 설계 목표 그대로다.

### 6. 첫째는 네 줄에 캐럿이 있고, 둘째는 두 줄에 캐럿이 없다

**출력** — `except` 와 `except*` 를 섞은 쪽.

```python
# e27_syntax_mix.py
try:
    pass
except* ValueError:
    pass
except TypeError:
    pass
```

```text
===== python3 - <e27_syntax_mix.py =====
  File "<stdin>", line 5
    except TypeError:
    ^^^^^^
SyntaxError: cannot have both 'except' and 'except*' on the same 'try'
(exit 1)
```

**출력** — `except*` 안에서 `return` 한 쪽.

```python
# e27_syntax_return.py
def f():
    try:
        pass
    except* ValueError:
        return 1
```

```text
===== python3 - <e27_syntax_return.py =====
  File "<stdin>", line 5
SyntaxError: 'break', 'continue' and 'return' cannot appear in an except* block
(exit 1)
```

**왜 그런가**

```text
   던진 것                          어느 단계가 잡나      소스 줄   캐럿   줄 수
   -----------------------------    ----------------     -------   ----   -----
   except 와 except* 를 섞는다       파서                  ★ 있다    ★ 있다   4
   except* 안의 return              심볼 테이블            없다      없다     2
```

- ★★ **캐럿이 있고 없고가 「어느 단계가 잡았나」를 그대로 말해 준다.**
  - **파서가 잡은 것**은 그 시점에 컴파일러가 **stdin 원문을 아직 들고 있어서**
    `except TypeError:` 한 줄과 `^^^^^^` 를 같이 찍는다.
  - **심볼 테이블 단계가 잡은 것**은 파싱이 이미 끝난 뒤라 **원문이 없다.** 줄 번호와 메시지뿐이다.
- ★ 첫째 출력의 줄 번호는 **5** 다 — **나중에 쓴 `except TypeError:` 쪽**을 가리킨다.
  파서는 **먼저 본 형태(`except*`)를 기준으로 삼고**, 그와 다른 것이 나오면 거기서 멈춘다.
- 금지되는 것은 **`break`·`continue`·`return` 셋**이다. 메시지가 그대로 적는다.

★★ **두 블록을 한 자리에 묶어 적으면 안 된다.** 한쪽의 캐럿을 다른 쪽에 옮겨 적는 사고가
이 갈래의 고정 실패 모드다 — **각각 따로 던져 캡처했다.**

### 7. `split` 은 둘, `subgroup` 은 하나 — 중첩은 보존되고 안 맞으면 `None`

**출력**

```python
# e27_split_subgroup.py
eg = ExceptionGroup("작업 넷이 깨졌다", [
    ValueError("v1"),
    TypeError("t1"),
    ExceptionGroup("안쪽 묶음", [KeyError("k1"), ValueError("v2")]),
])


def shape(exc):
    if exc is None:
        return "None"
    if isinstance(exc, BaseExceptionGroup):
        return "%s(%s)" % (exc.args[0], ", ".join(shape(c) for c in exc.exceptions))
    return type(exc).__name__


print("원본        :", shape(eg))
match, rest = eg.split(ValueError)
print("split 맞은 것:", shape(match))
print("split 남은 것:", shape(rest))
print("subgroup    :", shape(eg.subgroup(ValueError)))
print()
print("split 은 튜플을 돌려준다:", type(eg.split(ValueError)).__name__,
      "· 길이", len(eg.split(ValueError)))
print("아무것도 안 맞으면 subgroup:", shape(eg.subgroup(ZeroDivisionError)))
print("술어(함수)로도 가른다     :",
      shape(eg.subgroup(lambda e: "1" in str(e))))
print("원본은 그대로인가         :", shape(eg))
```

```text
===== python3 - <e27_split_subgroup.py =====
원본        : 작업 넷이 깨졌다(ValueError, TypeError, 안쪽 묶음(KeyError, ValueError))
split 맞은 것: 작업 넷이 깨졌다(ValueError, 안쪽 묶음(ValueError))
split 남은 것: 작업 넷이 깨졌다(TypeError, 안쪽 묶음(KeyError))
subgroup    : 작업 넷이 깨졌다(ValueError, 안쪽 묶음(ValueError))

split 은 튜플을 돌려준다: tuple · 길이 2
아무것도 안 맞으면 subgroup: None
술어(함수)로도 가른다     : 작업 넷이 깨졌다(ValueError, TypeError, 안쪽 묶음(KeyError))
원본은 그대로인가         : 작업 넷이 깨졌다(ValueError, TypeError, 안쪽 묶음(KeyError, ValueError))
(exit 0)
```

**왜 그런가**

- **`split` 은 `(맞은 것, 남은 것)` 튜플**을 돌려준다(`tuple · 길이 2`). **`subgroup` 은 맞은 것만** 돌려준다.
- ★★ **안쪽 껍데기가 복사된다** — `안쪽 묶음(ValueError)` 과 `안쪽 묶음(KeyError)` 로
  **같은 이름의 껍데기가 양쪽에 하나씩** 생겼다. 경로가 보존된다는 뜻이다.
- **아무것도 안 맞으면 `None`** 이다 — **빈 묶음이 아니다.**
  그래서 `len(eg.subgroup(T))` 를 바로 부르면 터진다.
- ★ **조건 자리에 술어(함수)도 줄 수 있다.** `lambda e: "1" in str(e)` 로 가르니
  `v1`·`t1`·`k1` 만 남았다 — **타입과 무관한 기준**으로 가를 수 있다.
- **원본은 안 바뀐다.** 마지막 줄이 그 확인이다.

### 8. `TypeError` · `ExceptionGroup` · `ValueError` · 잡는다

**출력**

```python
# e27_kinds.py
print("① BaseExceptionGroup 는 내용물에 따라 클래스를 바꿔 만든다")
b1 = BaseExceptionGroup("전부 Exception", [ValueError("v"), TypeError("t")])
print("   전부 Exception  ->", type(b1).__name__, "· Exception 인가:", isinstance(b1, Exception))
b2 = BaseExceptionGroup("KeyboardInterrupt 가 섞임", [ValueError("v"), KeyboardInterrupt()])
print("   BaseException 섞임 ->", type(b2).__name__, "· Exception 인가:", isinstance(b2, Exception))

print("② ExceptionGroup 에 BaseException 을 넣으면")
try:
    ExceptionGroup("안 된다", [KeyboardInterrupt()])
except TypeError as e:
    print("   TypeError:", e)

print("③ 맨 예외 하나만 던져도 except* 가 잡는다 — 묶어서 준다")
try:
    raise ValueError("묶이지 않은 하나")
except* ValueError as group:
    print("   받은 것:", type(group).__name__, "· 자식", len(group.exceptions),
          "·", [str(e) for e in group.exceptions])

print("④ 빈 리스트는 거부된다")
try:
    ExceptionGroup("빈 묶음", [])
except ValueError as e:
    print("   ValueError:", e)
```

```text
===== python3 - <e27_kinds.py =====
① BaseExceptionGroup 는 내용물에 따라 클래스를 바꿔 만든다
   전부 Exception  -> ExceptionGroup · Exception 인가: True
   BaseException 섞임 -> BaseExceptionGroup · Exception 인가: False
② ExceptionGroup 에 BaseException 을 넣으면
   TypeError: Cannot nest BaseExceptions in an ExceptionGroup
③ 맨 예외 하나만 던져도 except* 가 잡는다 — 묶어서 준다
   받은 것: ExceptionGroup · 자식 1 · ['묶이지 않은 하나']
④ 빈 리스트는 거부된다
   ValueError: second argument (exceptions) must be a non-empty sequence
(exit 0)
```

**왜 그런가**

- ①에서 **`BaseExceptionGroup(...)` 이 내용물을 보고 클래스를 고른다.**
  전부 `Exception` 이면 **`ExceptionGroup`**(그래서 `isinstance(_, Exception)` 이 `True`),
  `KeyboardInterrupt` 가 섞이면 **`BaseExceptionGroup`**(`False`)다.
- ②에서 `ExceptionGroup` 에 `BaseException` 을 넣으면
  **`TypeError: Cannot nest BaseExceptions in an ExceptionGroup`.**
- ★ ③에서 **묶이지 않은 `ValueError` 하나만 던져도 `except*` 가 잡는다** —
  **자식 1짜리 `ExceptionGroup` 으로 포장**해서 준다. 그래서 갈래 코드를 **한 벌로 통일**할 수 있다.
- ④에서 빈 시퀀스는 **`ValueError: second argument (exceptions) must be a non-empty sequence`.**

★ **클래스가 둘인 이유**는 [25번](../25-exceptions-and-finally/2-summary.md)의 계층과 같은 이야기다 —
`except Exception` 을 쓰는 코드가 **`KeyboardInterrupt` 가 든 묶음을 삼키면 안 되기 때문**이다.

```text
   BaseException
   └── BaseExceptionGroup      <- BaseException 이 섞이면 이쪽. except Exception 에 안 걸린다
       └── ExceptionGroup      <- Exception 만 담는다. except Exception 에 걸린다
```

### 9. 문법 오류가 아니고 둘째는 안 돈다 — `else`·`finally` 도 붙는다

**출력**

```python
# e27_star_shape.py
order = []

print("① 같은 타입을 except* 두 번 써도 문법 오류가 아니다")
try:
    raise ExceptionGroup("둘", [ValueError("v1"), ValueError("v2")])
except* ValueError as g:
    order.append(("첫째", len(g.exceptions)))
except* ValueError as g:
    order.append(("둘째", len(g.exceptions)))
print("   돈 갈래:", order)

print("② else 와 finally 도 붙는다")
try:
    pass
except* ValueError:
    print("   안 돈다")
else:
    print("   else 가 돌았다")
finally:
    print("   finally 가 돌았다")

print("③ 맞는 갈래가 하나도 없으면 묶음이 그대로 나간다")
try:
    try:
        raise ExceptionGroup("아무도 안 잡는다", [KeyError("k")])
    except* ValueError:
        print("   안 돈다")
except BaseExceptionGroup as eg:
    print("   바깥에서 잡힘:", type(eg).__name__, "· 자식", len(eg.exceptions))
```

```text
===== python3 - <e27_star_shape.py =====
① 같은 타입을 except* 두 번 써도 문법 오류가 아니다
   돈 갈래: [('첫째', 2)]
② else 와 finally 도 붙는다
   else 가 돌았다
   finally 가 돌았다
③ 맞는 갈래가 하나도 없으면 묶음이 그대로 나간다
   바깥에서 잡힘: ExceptionGroup · 자식 1
(exit 0)
```

**왜 그런가**

- ★ 같은 타입을 `except*` 로 **두 번 써도 문법 오류가 아니다.** 그런데 돈 갈래는 `[('첫째', 2)]` **하나뿐**이다 —
  **첫 갈래가 맞는 잎을 다 가져가** 둘째에 남을 것이 없다.
  [25번](../25-exceptions-and-finally/2-summary.md)의 `except` 순서 문제와 **같은 성격**이고, **경고도 없다.**
- **`else` 와 `finally` 도 붙는다.** 예외가 안 났으므로 둘 다 돌았다 —
  형태는 [25번](../25-exceptions-and-finally/2-summary.md)과 같다.
- ③에서 **맞는 갈래가 하나도 없으면 묶음이 통째로 나간다.** 밖의 `except BaseExceptionGroup` 이 받았다.

### 10. 실패가 동시에 여럿 나는데 하나만 고를 근거가 없어서다

**출력**

```python
# e27_taskgroup.py
import asyncio
import sys


async def boom(name, exc):
    await asyncio.sleep(0)
    raise exc(name)


async def main():
    async with asyncio.TaskGroup() as tg:
        tg.create_task(boom("첫째", ValueError))
        tg.create_task(boom("둘째", TypeError))


try:
    asyncio.run(main())
except BaseExceptionGroup as eg:
    print("TaskGroup 이 낸 것:", type(eg).__name__, file=sys.stderr)
    print("자식              :",
          sorted("%s(%s)" % (type(e).__name__, e) for e in eg.exceptions),
          file=sys.stderr)
    print("왜 묶음인가       : 두 태스크가 각각 실패했고 어느 하나만 고를 수 없다",
          file=sys.stderr)
```

```text
===== python3 - <e27_taskgroup.py =====
TaskGroup 이 낸 것: ExceptionGroup
자식              : ['TypeError(둘째)', 'ValueError(첫째)']
왜 묶음인가       : 두 태스크가 각각 실패했고 어느 하나만 고를 수 없다
(exit 0)
```

**왜 그런가**

- ★ **동기 한 줄** — 여러 태스크를 동시에 돌리면 **실패도 동시에 여럿** 나는데,
  예외 하나로는 **나머지를 버릴 수밖에 없었다.** PEP 654 의 출발점이 이것이다.
- 표준 라이브러리에서 처음 크게 쓴 것이 **`asyncio.TaskGroup`** 이고, **3.11 부터**다 — 문법과 같은 판이다.
- ★ **기존 `except ValueError` 가 안 맞는 이유**는 3번 답 그대로다 —
  밖으로 나오는 것은 **`ExceptionGroup` 한 개**이고, 별 없는 `except` 는 **그 묶음의 타입**만 본다.
  받으려면 **`except*` 나 `except BaseExceptionGroup`** 이다.
- 자식은 `sorted()` 로 찍었다 — **태스크 완료 순서는 보장이 없으므로** 정렬해야 출력이 결정적이다.

### 11. 문제의식은 같고, 담는 자리가 다르다

**왜 그런가**

| | 자바(try-with-resources 의 suppressed) | 파이썬(`ExceptionGroup`) | Go(`errors.Join`) |
|---|---|---|---|
| 무엇을 푸나 | **정리 중 난 예외를 잃지 않기** | **동시 실패를 잃지 않기** | **오류 여럿을 한 값으로** |
| 담는 자리 | **주 예외에 붙인다**(`getSuppressed()`) | **새 묶음을 만든다** | **새 error 값을 만든다** |
| 주·부가 있나 | ★ **있다** — 주 예외가 정해진다 | ★ **없다** — 자식이 대등하다 | 없다 |
| 잡는 쪽 | `catch` 는 주 예외만 본다 | `except*` 가 **갈래마다** 돈다 | `errors.Is`/`As` 가 훑는다 |

- ★ **자바 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 26번**과 같은 것은
  **「정리·동시 상황에서 예외를 잃는다」는 문제의식**이다.
  다른 것은 **주 예외를 정하느냐**다 — 자바는 정하고, 파이썬은 **대등하게 둔다.**
  병렬 태스크에서는 어느 하나를 「주」로 고를 근거가 없기 때문이다.
- ★ **Go 갈래 목록([`go/syntax/README.md`](../../../go/syntax/README.md))의 24번**의 `errors.Join`(1.20)은
  **파이썬 쪽에 가깝다** — 대등하게 묶고, 꺼낼 때 훑는다.
  다만 Go 는 **오류가 값**이라 던지고 잡는 문법이 없고, 파이썬은 **`except*` 라는 문법을 새로 만들었다.**

### 12. 세 층과 이웃 경계

**왜 그런가**

**언어 보장**(PEP 654·레퍼런스가 정한 것)

- `ExceptionGroup` 은 **`Exception` 만** 담고 `BaseExceptionGroup` 은 둘 다 담는다.
  **`BaseExceptionGroup(...)` 이 내용물에 따라 클래스를 고른다.**
- **`exceptions` 는 튜플**이고 자식이 또 묶음일 수 있다.
- ★ **`except*` 갈래는 최대 한 번씩 돌고, 맞는 잎을 모은 묶음을 받으며, 안 잡힌 것은 다시 raise 된다.**
- ★ **`except` 와 `except*` 를 섞을 수 없고, `except*` 안에서 `break`·`continue`·`return` 을 못 쓴다.**
- `subgroup`/`split` 이 **중첩을 보존**하고 **안 맞으면 `None`** 을 준다.
- **3.11 부터**다.

**CPython 구현 세부사항**

- ★ **괘선 트레이스백의 모양** — `+ Exception Group Traceback` · `+-+---------------- 1 ----------------` ·
  괘선 안의 **`    | ` 만 있는 줄**. **이것이 어느 층이냐고 물으면 구현이다** — 명세는 형식을 정하지 않는다.
- `(3 sub-exceptions)` / `(1 sub-exception)` 의 단수·복수 표기.
- `SyntaxError` 문구 둘과 예외 문구 전부.
- 섞기 오류가 **나중에 나온 절**을 가리키는 것.

**이 판(3.12.3)의 관찰**

- ★ **섞기 오류에 캐럿이 있고 `return` 오류에 없는 것** — 단계가 달라서다.
  **다른 판은 안 돌려 봤다.**
- 괘선의 가로 길이와 표기.
- `TaskGroup` 이 자식 둘을 모두 담는 것(완료 순서는 보장이 없어 **`sorted()` 로 찍었다**).

**이웃 경계 한 줄씩**

- **「예외 계층과 연쇄」는 [25번](../25-exceptions-and-finally/2-summary.md)이다.**
  `BaseException`/`Exception` 의 갈라짐도 `__context__`·`__cause__` 도 전부 그쪽이고,
  여기는 **그것이 괘선 안에서 어떻게 보이나**만 본다.
- **「`TaskGroup` 의 취소 전파·타임아웃」은 `목록의 **52번 주제**`** 다.
  여기서는 **왜 묶음이 필요했나**까지다.
- **실패가 하나일 때의 선택은 [26번](../26-eafp-vs-lbyl/2-summary.md)** 이다.
- **정리 중 난 예외 여럿**은 [28번](../28-context-managers-and-with/2-summary.md)의 `ExitStack` 자리다 —
  ★ 그쪽은 **묶음을 만들지 않는다.**

## 실행 검증

| 무엇 | 어디서 | 몇 번 | 구현 의존인가 |
|---|---|---|---|
| 묶음 트리(자식 3 · 잎 4) | `python3` 3.12.3 · Linux x86_64 | 캡처 + 제출 전 재실행 | **아니다** — `exceptions` 계약 |
| `except*` 세 갈래가 도는 것 | 〃 | 〃 | **아니다** — 8.4.2 |
| 별 없는 `except` 가 한 번만 도는 것 | 〃 | 〃 | **아니다** |
| 안 잡힌 것이 구조째 올라가는 것 | 〃 | 〃 | **아니다** |
| 갈래 안 `raise` 가 보태기인 것 | 〃 | 〃 | 동작은 명세, **괘선 모양은 구현** |
| `SyntaxError` 둘 — **캐럿 있음/없음** | 〃 (각각 따로 던짐) | 〃 | ★ **문구는 구현**, 단계 차이는 컴파일 구조 |
| `split`·`subgroup` | 〃 | 〃 | **아니다** |
| 묶음 생성 규칙 넷 | 〃 | 〃 | **아니다** — 문구만 구현 |
| `except*` 두 번·`else`·`finally` | 〃 | 〃 | **아니다** |
| `asyncio.TaskGroup` | 〃 | 〃 | **아니다**(3.11+). 완료 순서는 보장 없음 → `sorted()` |
| **안 돌려 본 것** | 3.10 이하(문법 자체가 없다) · `derive` 훅 · `exceptiongroup` 백포트 · `traceback` 모듈 직접 호출 | — | — |

★ **판이 오르면 다시 돌릴 것** — **괘선 트레이스백을 싣는 블록 넷**(4·5번과 그 짝)과 **`SyntaxError` 둘**이다.
나머지는 명세에 묶여 있다.
