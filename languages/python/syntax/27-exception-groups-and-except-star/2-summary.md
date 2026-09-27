# python/syntax/27-exception-groups-and-except-star — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만.
> - [PEP 654 — Exception Groups and `except*`](https://peps.python.org/pep-0654/) — **이 주제의 정본**
> - [`ExceptionGroup`·`BaseExceptionGroup`](https://docs.python.org/3.12/library/exceptions.html#exception-groups) — `exceptions`·`subgroup`·`split`·`derive`
> - [8.4.2. `except*` clause](https://docs.python.org/3.12/reference/compound_stmts.html#except-star) — 섞어 쓸 수 없는 것, `break`/`continue`/`return` 금지
> - [`asyncio.TaskGroup`](https://docs.python.org/3.12/library/asyncio-task.html#task-groups) — **이 문법을 만든 동기**
>
> **실행 검증** — 이 문서에 실린 출력은 전부 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.\
> ★ **던지는 형태를 하나로 고정했다** — `python3 - <파일` 로 던져 트레이스백이 `File "<stdin>", line N` 이 된다.\
> ★★ **이 주제에는 `SyntaxError` 가 둘 있고, 둘의 모양이 다르다** — 이 사실 자체가 주제의 한 축이다.
> **파서가 잡는 것은 소스 줄과 캐럿이 나오고**(`cannot have both 'except' and 'except*'`),
> **심볼 테이블 단계가 잡는 것은 둘 다 안 나온다**(`'break', 'continue' and 'return' cannot appear in an except* block`).
> **두 블록을 섞어 적지 않았다** — 각각 따로 던져 캡처했다.\
> ★★ **묶음 트레이스백은 형태가 완전히 다르다** — `+`·`|`·`+-+----- 1 -----` 같은 **괘선**이 붙는다.
> 연쇄가 그 안에 들어가면 **`| ` 만 있는 줄**까지 생긴다(동작 6). **한 글자도 손대지 않았다 — 캡처를 조립기로 끼웠다.**\
> **버전** — **3.11 부터**다(PEP 654). `ExceptionGroup`·`BaseExceptionGroup`·`except*` 셋 다.
> **3.10 이하는 이 머신에 없어 「그 판에서는 `SyntaxError`」를 직접 못 돌려 봤다** — PEP 근거다.
> 표준 라이브러리에서 이것을 처음 크게 쓴 것이 **`asyncio.TaskGroup`(3.11)** 이다.\
> **구현 대 언어 보장 한 줄** — **`exceptions` 튜플·`split`/`subgroup` 의 계약과 `except*` 의 분배 규칙까지가 언어 보장**이고,
> **괘선 트레이스백의 생김새와 예외 문구는 CPython 구현**이다.\
> **★ 흔들리는 칸 / 안 흔들리는 칸** — 재대조에서 「고칠 것」과 「설계상 안 맞는 것」을 기계적으로 가르려고 미리 선언한다.
>
> | 흔들린다 | 안 흔들린다(근거로 써도 되는 칸) |
> |---|---|
> | (판이 오르면) 괘선 트레이스백의 **모양**과 `(N sub-exceptions)` 표기 | **트리의 구조** — 자식 수·중첩 깊이·어느 잎이 어느 갈래로 갔나 |
> | (판이 오르면) `SyntaxError` **문구** | **캐럿이 있나 없나** — 파서 단계인가 심볼 테이블 단계인가 |
> | (판이 오르면) 예외 **문구** 전부 | 예외 **종류** · `File "<stdin>", line N` · **종료 코드** |
> | — | `except*` 갈래가 **몇 번 도나** · `split`/`subgroup` 이 **중첩을 보존하는 것** |
>
> ★ **이 주제의 블록에는 주소도 시간도 한 곳도 안 찍힌다.** 같은 판에서 다시 돌리면 **한 글자도 안 변한다.**\
> **선행** — [25-exceptions-and-finally](../25-exceptions-and-finally/2-summary.md)(**예외 계층과 연쇄의 정본**) ·
> [26-eafp-vs-lbyl](../26-eafp-vs-lbyl/2-summary.md)(실패가 **하나**일 때의 선택).\
> **이 사슬** — [25](../25-exceptions-and-finally/2-summary.md) → [26](../26-eafp-vs-lbyl/2-summary.md) → 27 → [28](../28-context-managers-and-with/2-summary.md).
> 25·26 이 **실패 하나**를 다뤘다면 여기는 **실패 여럿을 잃지 않고 나르는 법**이다.

## 한눈에 — 쉽게 말하면

**`ExceptionGroup` 은 「불평 여러 건을 한 봉투에 넣어 올려 보내는 것」이고, `except*` 는 「봉투를 열어 종류별로 나눠 주는 것」이다.**

- 보통 `raise` 는 **불평을 하나만** 올려 보낸다 — 나머지는 **버려진다.**
- 병렬로 세 가지 일을 시켰는데 **둘이 실패**하면, 어느 하나만 고를 근거가 없다.
- `except*` 는 봉투를 뜯어 **종류별로 나눠** 각 담당자에게 준다 — 그래서 **갈래가 여러 번 돈다.**
- ★ 나눠 주고 **남은 것은 다시 봉투에 담겨 위로 올라간다.**

```text
   raise 하나                          ExceptionGroup

   ValueError  ──> 위로                 ┌ ValueError ┐
   TypeError   ──> 버려진다              │ TypeError  │──> 봉투 하나로 위로
   KeyError    ──> 버려진다              └ KeyError   ┘

                                       except* ValueError: ──> 잎 1개짜리 새 봉투
                                       except* TypeError : ──> 잎 1개짜리 새 봉투
                                       (안 잡힌 KeyError) ──> 남은 봉투가 계속 올라간다
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 봉투 | `ExceptionGroup` | `exceptions` 가 **튜플**이다 |
| 봉투 안의 봉투 | 중첩된 묶음 | 재귀로 훑어야 **잎**이 나온다 |
| 종류별로 나눠 준다 | `except*` | **한 `try` 문에서 갈래가 여러 번 돈다** |
| ★ **나눠 줘도 봉투에 담아 준다** | 갈래가 받는 것도 `ExceptionGroup` | `type(group).__name__` 을 찍어 보면 안다 |
| 남은 것은 다시 올라간다 | 안 잡힌 잎 | **구조를 유지한 채** 새 묶음이 된다 |
| 봉투째 하나로 받는다 | 별 없는 `except` | 갈래가 **한 번**만 돈다 |
| ★ **봉투에 못 넣는 것** | `BaseException`(`KeyboardInterrupt` 등) | `ExceptionGroup` 이 **`TypeError`** 를 낸다 |
| 봉투를 손으로 가른다 | `split`·`subgroup` | **중첩이 보존된다** |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.\
「**태스크 다섯 중 둘이 실패했는데 로그에 하나만 남았다**」와
「**`except*` 를 하나만 써 놓고 다 잡은 줄 알았다**」가 그것이다.\
앞엣것이 `asyncio.TaskGroup` 이 이 문법을 만든 이유고, 뒤엣것은 **남은 봉투**가 조용히 올라간 것이다.

> **예외 그룹(exception group)** — 예외 여럿을 **자식으로 품는** 예외 하나.\
> 예: `ExceptionGroup("셋이 깨졌다", [ValueError("v"), TypeError("t")])`

> **잎(leaf)** — 묶음 트리에서 **더 안 쪼개지는** 진짜 예외.\
> 예: 자식이 또 묶음이면 잎이 아니다 — 재귀로 내려가야 한다.

```python
# v_version.py
import sys

print("version_info =", sys.version_info)
print("implementation =", sys.implementation.name)
print("platform =", sys.platform)
```

```text
===== python3 - <v_version.py =====
version_info = sys.version_info(major=3, minor=12, micro=3, releaselevel='final', serial=0)
implementation = cpython
platform = linux
(exit 0)
```

## 이 주제가 답하려는 질문

1. **왜 예외 하나로는 모자랐는가** — 무엇이 버려지고 있었나.
2. **`except*` 는 무엇을 받아 무엇을 돌려보내는가** — 갈래가 몇 번 도나.
3. **`except` 와 `except*` 를 왜 못 섞는가** — 그리고 그 금지는 **어느 단계**가 잡는가.

★ 둘째 질문이 이 주제의 인출 목표다. **「갈래가 여러 번 돈다」를 아는 것과, 「받는 것도 묶음이고 남은 것도 묶음이다」를 대는 것**이 아는 것과 들은 것의 경계다.

## 동작 방식

> 이 절이 본문이다. 이 주제의 네 번째 창은 **`exceptions` 속성을 직접 훑는 것**이다 —
> 트레이스백의 괘선은 **보기에는 예쁜데 프로그램이 읽을 수 없다.**
> **구조를 확인하는 유일한 길은 `exceptions` 를 재귀로 내려가는 것**이고, 이 문서는 그 결과를 매번 같이 싣는다.

### 1. ★ 묶음은 트리다 — `exceptions` 로 직접 훑는다

**언제 쓰나** — 묶음을 처음 받았을 때. 「자식이 몇 개냐」로는 모자라는 이유가 여기 있다.

```text
   ExceptionGroup("작업 넷이 깨졌다")
   ├── ValueError("v1")                      <- 잎
   ├── TypeError("t1")                       <- 잎
   └── ExceptionGroup("안쪽 묶음")            <- 잎이 아니다
       ├── KeyError("k1")                    <- 잎
       └── ValueError("v2")                  <- 잎

   맨 위 자식 수 = 3        잎 수 = 4      ★ 두 수가 다르다
```

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

- **`exceptions` 는 튜플**이다 — 불변이고, 순서가 그대로 보존된다.
- ★★ **맨 위 자식이 3 인데 잎은 4** 다. **`len(eg.exceptions)` 를 「실패 개수」로 읽으면 틀린다.**
- 잎을 세려면 **재귀로 내려가야** 한다. 그 구분이 이 주제 내내 쓰인다.

**비용** — 재귀 한 벌을 늘 들고 다녀야 한다. 대신 **깊이가 몇이든 같은 코드**로 읽힌다.

### 2. ★★ `except*` 는 갈래가 **여러 번** 돈다

**언제 쓰나** — 묶음을 처리할 때마다. 이것이 `except` 와 갈리는 첫째 자리다.

레퍼런스가 규칙을 적는다.

> In an `except*` clause, the exception type is matched against the group's sub-exceptions …
> Each `except*` clause is executed at most once, and handles all the exceptions that match its type.

```text
   try:
       raise 묶음(v1, t1, 안쪽묶음(k1, v2))

   except* ValueError  ->  ExceptionGroup(v1, 안쪽묶음(v2))   <- 1번 돈다
   except* TypeError   ->  ExceptionGroup(t1)                <- 1번 돈다
   except* KeyError    ->  ExceptionGroup(안쪽묶음(k1))       <- 1번 돈다

   ★ 한 try 문에서 세 갈래가 다 돌았다 — except 였다면 하나만 돈다
```

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

- ★★ **한 `try` 문에서 세 갈래가 전부 돌았다**(`['ValueError', 'TypeError', 'KeyError']`).
- ★ **갈래가 받는 것도 `ExceptionGroup`** 이다 — 잎 하나가 와도 **묶음으로 포장**돼서 온다.
- ★ **중첩이 보존된다.** `ValueError` 갈래의 자식이 **2** 인데 잎은 `['v1']` 하나다 —
  나머지 하나가 **`안쪽 묶음` 을 감싼 채** 들어 있다.

같은 묶음을 **별 없는 `except`** 로 잡으면 이렇게 된다.

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

- ★ **`except ValueError` 갈래는 안 돈다.** 묶음 안에 `ValueError` 가 있어도 **묶음 자체의 타입**에만 맞춘다.
- `except ExceptionGroup` 이 **통째로 하나** 잡았다. 갈래는 **한 번**만 돈다.

**비용** — `except*` 를 쓰면 **갈래가 몇 번 돌지 코드만 봐서는 모른다.** 그 대신 **아무 실패도 안 잃는다.**

### 3. ★ 안 잡힌 것은 **구조를 유지한 채** 다시 올라간다

**언제 쓰나** — `except*` 를 몇 개만 쓸 때. 「다 잡았다」고 착각하기 쉬운 자리다.

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

- **`ValueError` 갈래는 돌았다**(자식 2). 그런데 **그 뒤 줄이 안 찍혔다.**
- ★★ **남은 `KeyError` 가 묶음으로 다시 포장돼 올라갔다.** 트레이스백을 보면
  **바깥 묶음 → 안쪽 묶음 → `KeyError`** 로 **원래 중첩이 그대로** 살아 있다.
- 메시지도 그대로고 `(1 sub-exception)` 로 **개수만** 줄었다 — **가지치기**된 것이다.

```text
   원래                         남은 것
   작업 셋이 깨졌다 (2)          작업 셋이 깨졌다 (1)
   ├── ValueError v1     ──잡힘──> (없다)
   └── 안쪽 묶음 (2)             └── 안쪽 묶음 (1)
       ├── KeyError k1               └── KeyError k1   <- ★ 경로가 보존된다
       └── ValueError v2   ──잡힘──> (없다)
```

**비용** — **`except*` 하나로는 대개 모자란다.** 남는 것을 밖에서 받을 계획이 필요하다.

### 4. ★ `split` 과 `subgroup` — 손으로 가르면 중첩이 보존된다

**언제 쓰나** — `except*` 문법을 안 쓰고 코드로 가르고 싶을 때. 로깅·분류에서 흔하다.

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

- **`split` 은 `(맞은 것, 남은 것)` 튜플**을 돌려준다. `subgroup` 은 **맞은 것만** 돌려준다.
- ★★ **양쪽 다 중첩이 보존된다** — `안쪽 묶음(ValueError)` 과 `안쪽 묶음(KeyError)` 로 **껍데기가 복사**됐다.
- **아무것도 안 맞으면 `None`** 이다 — 빈 묶음이 아니다.
- **술어(함수)도 받는다** — 타입이 아니라 조건으로 가를 수 있다.
- ★ **원본은 안 바뀐다.** 마지막 줄이 그 확인이다.

**비용** — 껍데기를 복사하므로 **깊으면 그만큼 객체가 는다.** 대신 **원본이 온전히 남는다.**

### 5. ★ 무엇을 봉투에 넣을 수 있나 — `ExceptionGroup` 과 `BaseExceptionGroup`

**언제 쓰나** — 묶음을 직접 만들 때. 그리고 **왜 클래스가 둘인지** 물을 때.

```text
   BaseException
   └── BaseExceptionGroup          <- BaseException 도 담을 수 있다
       └── ExceptionGroup          <- Exception 만 담는다 (Exception 의 하위이기도 하다)

   ★ BaseExceptionGroup(...) 을 부르면 내용물을 보고 둘 중 하나를 만들어 준다
```

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

- ★★ **`BaseExceptionGroup(...)` 은 내용물에 따라 클래스를 바꿔 만든다.**
  전부 `Exception` 이면 **`ExceptionGroup`**, `BaseException` 이 섞이면 **`BaseExceptionGroup`** 이다.
- **`ExceptionGroup` 에 `BaseException` 을 넣으면 `TypeError`** 다
  (`Cannot nest BaseExceptions in an ExceptionGroup`).
- ★ **묶이지 않은 예외 하나만 던져도 `except*` 가 잡는다** — **묶어서** 준다(자식 1).
  그래서 `except*` 는 **묶음이 아닌 것도 처리할 수 있다.**
- **빈 시퀀스는 거부된다**(`ValueError: second argument (exceptions) must be a non-empty sequence`).

★ **클래스가 둘인 이유**는 [25번](../25-exceptions-and-finally/2-summary.md)의 계층과 같은 이야기다 —
`except Exception` 을 쓰는 코드가 **`KeyboardInterrupt` 가 든 묶음을 삼키면 안 되기 때문**이다.

**비용** — 만들 때 클래스가 바뀔 수 있으므로 **`type()` 으로 분기하는 코드는 위험**하다. `isinstance` 를 쓴다.

### 6. ★★ `except*` 안에서 `raise` 하면 — 새 예외도 묶음에 담긴다

**언제 쓰나** — 갈래에서 예외를 바꿔 던질 때. 출력이 가장 낯선 자리다.

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

그림 해설 — 괘선 트레이스백을 어떻게 읽나.

- 맨 위가 **바깥 묶음**이다(`ExceptionGroup:  (2 sub-exceptions)` — 메시지가 비어 있다).
- **1번 칸**이 `ValueError` 갈래에서 일어난 일이다 — 원래 묶음(`ValueError: v1`)을 처리하다가
  **`RuntimeError` 가 났고**, 그 둘이 [25번](../25-exceptions-and-finally/2-summary.md)의
  **`During handling of the above exception, another exception occurred:`** 로 이어져 있다.
- ★ 그 연쇄 문구 위아래의 **`    | ` 두 줄**이 괘선 안의 빈 줄이다. **한 글자도 손대면 안 되는 자리**다.
- **2번 칸**은 **안 잡힌 `TypeError`** 다. 새 예외와 **나란히** 담겼다.
- ★★ 그래서 `except*` 안의 `raise` 는 「바꿔치기」가 아니라 「**보태기**」다.
  잡힌 쪽의 새 예외와 **안 잡힌 나머지**가 같은 봉투에 들어간다.

**비용** — 출력이 깊어진다. 대신 **아무것도 안 잃는다** — 이 문법의 설계 목표 그대로다.

### 7. `except*` 의 나머지 문법 규칙

**언제 쓰나** — `except*` 를 쓰기 직전에. 세 가지만 기억하면 된다.

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

- ★ **같은 타입을 `except*` 로 두 번 써도 문법 오류가 아니다.** 다만 **첫 갈래가 다 가져가** 둘째는 안 돈다
  (`[('첫째', 2)]` — 한 쌍만 찍혔다). `except` 의 순서 문제와 **같은 성격**이고, 역시 **경고가 없다.**
- **`else` 와 `finally` 도 붙는다.** 형태는 [25번](../25-exceptions-and-finally/2-summary.md)과 같다.
- **맞는 갈래가 하나도 없으면 묶음이 통째로 나간다** — 밖에서 `except BaseExceptionGroup` 이 받았다.

**비용** — 없다. 다만 **같은 타입을 두 번 쓸 이유가 없다.**

### 8. ★★ `except` 와 `except*` 는 못 섞는다 — 그리고 두 `SyntaxError` 의 모양이 다르다

**언제 쓰나** — 기존 `try` 에 `except*` 를 한 줄 보탤 때. 이 주제에서 가장 자주 부딪힌다.

레퍼런스가 못 박는다.

> It is not possible to mix `except` and `except*` in the same `try`.

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

- ★ **소스 줄과 캐럿이 둘 다 나온다.** `except` 라는 여섯 글자 위에 `^^^^^^` 가 놓인다.
  **파서가 잡은 것**이라 그렇다 — 그 시점에 컴파일러가 stdin 을 아직 들고 있다.
- **줄 번호가 5**다. 즉 **먼저 나온 `except*` 가 아니라 나중에 나온 `except` 쪽**을 가리킨다 —
  파서는 **먼저 본 형태를 기준으로 삼는다.**

같은 `except*` 안에서 `return` 을 쓰면 **모양이 다른 `SyntaxError`** 가 난다.

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

- ★★ **소스 줄도 캐럿도 없다.** 파일 이름과 줄 번호, 그리고 메시지 한 줄뿐이다.
- **파서는 이 문장을 정상으로 읽는다.** 걸린 것은 **그 뒤의 심볼 테이블 단계**이고,
  그 단계는 **소스 원문을 더 이상 안 들고 있다.**
- 금지되는 것은 **`break`·`continue`·`return` 셋**이다. 메시지가 그대로 적는다.

```text
   던진 것                          어느 단계가 잡나      소스 줄   캐럿
   -----------------------------    ----------------     -------   ----
   except 와 except* 를 섞는다       파서                  ★ 있다    ★ 있다
   except* 안의 return              심볼 테이블            없다      없다

   ★ 같은 SyntaxError 인데 출력 모양이 다르다 — 섞어 적으면 재현이 안 된다
```

★★ **두 블록을 각각 따로 던져 캡처했다.** 한 블록에 묶어 적으면 **둘 중 하나는 반드시 거짓**이 된다.

**비용** — 섞을 수 없으니 **기존 `try` 를 통째로 바꿔야** 한다. 그것이 이 문법 도입의 실무 비용이다.

### 9. 왜 만들었나 — `asyncio.TaskGroup`

**언제 쓰나** — 「이걸 어디서 실제로 만나나」를 물을 때.

**한 줄로는 이렇다** — **여러 태스크를 동시에 돌리면 실패도 동시에 여럿 나는데, 예외 하나로는 나머지를 버릴 수밖에 없었다.**

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

- 두 태스크가 각각 다른 예외로 실패했고, **`TaskGroup` 이 `ExceptionGroup` 으로 묶어** 냈다.
- ★ **어느 하나만 고를 근거가 없다** — 그래서 묶음이 필요했다. PEP 654 의 동기가 정확히 이것이다.
- 자식을 `sorted()` 로 찍었다 — **태스크 완료 순서는 보장되지 않으므로** 정렬해야 출력이 결정적이다.

**비용** — 호출하는 쪽이 **`except*` 나 `except BaseExceptionGroup`** 으로 받아야 한다.
기존 `except ValueError` 코드는 **안 맞는다.**

## 문법 — 형태와 규칙

**형태 — 네 가지뿐이다**

```python
# e27_forms.py
# ① 묶음을 만든다 — 메시지 + 비어 있지 않은 시퀀스
def make():
    return ExceptionGroup("작업 셋이 깨졌다", [
        ValueError("v1"),
        TypeError("t1"),
        ExceptionGroup("안쪽 묶음", [KeyError("k1")]),   # 중첩된다
    ])


# ② except* — 갈래마다 "맞는 잎만 모은 새 묶음" 을 받는다
def handle():
    try:
        raise make()
    except* ValueError as group:      # group 은 ExceptionGroup 이다
        print("ValueError 쪽", len(group.exceptions))
    except* (TypeError, KeyError) as group:   # 튜플로 여럿
        print("TypeError·KeyError 쪽", len(group.exceptions))
    else:
        print("묶음이 안 왔다")
    finally:
        print("언제나")


# ③ 별 없는 except 로도 잡힌다 — 통째로 하나
def handle_plain():
    try:
        raise make()
    except ExceptionGroup as eg:
        print("통째로 하나", len(eg.exceptions))


# ④ 손으로 가른다 — split 은 (맞은 것, 남은 것), subgroup 은 맞은 것만
def sort_out(eg):
    match, rest = eg.split(ValueError)
    only = eg.subgroup(lambda e: "1" in str(e))   # 술어도 받는다
    return match, rest, only
```

규칙 아홉.

1. **`ExceptionGroup(메시지, 시퀀스)`** 로 만든다. **시퀀스는 비어 있으면 안 된다**(`ValueError`).
2. **`ExceptionGroup` 은 `Exception` 만** 담는다. `BaseException` 을 넣으면 **`TypeError`**.
3. **`BaseExceptionGroup(...)` 은 내용물을 보고 둘 중 하나를 만들어 준다.**
4. **`exceptions` 는 튜플**이고, 자식이 **또 묶음일 수 있다** — 잎을 세려면 재귀다.
5. ★ **`except*` 는 갈래가 여러 번 돈다.** 각 갈래는 **최대 한 번**이고, 받는 것도 **묶음**이다.
6. ★ **안 잡힌 것은 구조를 유지한 채 다시 올라간다.**
7. ★ **`except*` 안에서는 `break`·`continue`·`return` 을 못 쓴다**(`SyntaxError`, **캐럿 없음**).
8. ★ **한 `try` 에 `except` 와 `except*` 를 섞을 수 없다**(`SyntaxError`, **캐럿 있음**).
9. **`split(조건)` 은 `(맞은 것, 남은 것)`**, **`subgroup(조건)` 은 맞은 것만.** 조건은 **타입 또는 술어**,
   안 맞으면 **`None`**, **중첩은 보존**되고 **원본은 안 바뀐다.**

**금지 사례 — 문법은 맞는데 조용히 어긋나는 것들**

```python
# e27_pitfalls.py
# ① 별 없는 except 로 잡으면 갈래가 하나만 돈다
def only_one(eg):
    try:
        raise eg
    except ValueError:            # ★ 묶음 안에 ValueError 가 있어도 안 맞는다
        return "안 돈다"
    except ExceptionGroup:        #   묶음 자체의 타입에만 맞는다
        return "통째로 하나"


# ② 맞는 갈래가 없으면 남은 것이 그대로 나간다 — 잡았다고 착각한다
def leftover(eg):
    try:
        raise eg
    except* ValueError:
        pass                      # ★ KeyError 는 여기서 안 잡혀 밖으로 나간다
    return "여기까지 못 올 수 있다"


# ③ 자식이 하나뿐이어도 묶음은 묶음이다
def unwrap_forgotten(eg):
    return eg.exceptions[0]       # ★ 이것이 또 묶음일 수 있다 — 재귀로 훑어야 한다


# ④ ExceptionGroup 에 BaseException 을 넣는다
def bad_group():
    return ExceptionGroup("안 된다", [KeyboardInterrupt()])   # ★ TypeError


# ⑤ 빈 시퀀스로 만든다
def empty_group():
    return ExceptionGroup("빈 묶음", [])                      # ★ ValueError
```

## 어디서 틀리나

### (1) ★★ `except ValueError` 로 묶음 안의 `ValueError` 를 잡으려 한다

**안 맞는다.** 별 없는 `except` 는 **묶음 자체의 타입**에만 맞춘다.
실측에서 `except ValueError` 갈래가 안 돌고 `except ExceptionGroup` 이 통째로 하나 잡았다.

### (2) ★★ `except*` 하나로 다 잡은 줄 안다

★ **안 잡힌 잎은 묶음으로 다시 포장돼 올라간다.** 실측에서 그 뒤 줄이 **안 찍혔다.**

### (3) `len(eg.exceptions)` 를 「실패 개수」로 읽는다

★ **자식 수와 잎 수가 다르다**(실측: 3 대 4). 자식이 또 묶음일 수 있다.

### (4) 갈래가 받는 것을 **잎 하나**로 안다

★ **묶음이 온다.** 잎 하나뿐이어도 `ExceptionGroup` 으로 포장돼 온다.

### (5) ★ `except` 와 `except*` 를 섞는다

**`SyntaxError`** 다 — **캐럿이 있는 쪽**이고, 파서가 잡는다. 기존 `try` 를 통째로 바꿔야 한다.

### (6) ★ `except*` 안에서 `return` 을 쓴다

**`SyntaxError`** 다 — **캐럿이 없는 쪽**이고, 심볼 테이블 단계가 잡는다.
`break`·`continue` 도 같다. **값을 밖으로 내려면 변수에 담는다.**

### (7) 두 `SyntaxError` 의 출력 모양을 같은 것으로 안다

★★ **파서가 잡는 것은 소스 줄과 캐럿이 나오고, 심볼 테이블이 잡는 것은 안 나온다.**
한 블록에 섞어 적으면 **둘 중 하나가 반드시 거짓**이 된다.

### (8) `ExceptionGroup` 에 `KeyboardInterrupt` 를 넣는다

**`TypeError: Cannot nest BaseExceptions in an ExceptionGroup`.**
`BaseExceptionGroup` 을 써야 하고, 그러면 **`except Exception` 에 안 걸린다.**

### (9) 빈 리스트로 묶음을 만든다

**`ValueError: second argument (exceptions) must be a non-empty sequence`.**

### (10) `except*` 안의 `raise` 를 「바꿔치기」로 안다

★ **보태기다.** 새 예외와 **안 잡힌 나머지**가 같은 봉투에 나란히 담긴다.

### (11) 같은 타입을 `except*` 로 두 번 쓴다

**문법 오류는 아닌데 둘째가 안 돈다.** [25번](../25-exceptions-and-finally/2-summary.md)의
`except` 순서 문제와 같은 성격이고, **경고도 없다.**

### (12) `subgroup` 이 안 맞으면 빈 묶음을 준다고 안다

★ **`None` 이다.** `if eg.subgroup(T):` 로 쓰면 되지만 `len()` 을 바로 부르면 터진다.

### (13) 3.10 이하에서 쓴다

**없는 문법이다**(3.11+). 이 머신에 3.10 이하가 없어 **그 판의 출력은 안 돌려 봤다.**

## 구현 세부사항 대 언어 보장

세 층으로 가른다. ★ **이 주제는 「언어 보장」이 두껍다** — PEP 654 와 레퍼런스가
분배 규칙·금지 사항·`split`/`subgroup` 의 계약을 **전부 글로 적어 두었다.**\
구현 쪽에 남는 것은 **괘선 트레이스백의 생김새**와 **예외 문구**다.

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **언어 보장** | PEP 654·레퍼런스가 정한 것 | 공식 문서 문장을 열어서 인용 |
| **CPython 구현** | 이 구현이 그렇게 하는 것 | 괘선 트레이스백 · 예외·`SyntaxError` 문구 |
| **이 판(3.12.3)의 관찰** | 이 판에서 그랬을 뿐 | 캐럿의 유무 · `(N sub-exceptions)` 표기 |

### 언어 보장

| 사실 | 근거 |
|---|---|
| `ExceptionGroup(메시지, 시퀀스)` — **비어 있지 않은 시퀀스**여야 한다 | Exception groups |
| **`ExceptionGroup` 은 `Exception` 만** 담고, `BaseExceptionGroup` 은 둘 다 담는다 | 〃 |
| **`BaseExceptionGroup(...)` 이 내용물에 따라 클래스를 고른다** | 〃 |
| **`exceptions` 는 튜플**이고 자식이 또 묶음일 수 있다 | 〃 |
| `subgroup`/`split` 이 **중첩 구조를 보존**하고 **안 맞으면 `None`** 을 준다 | 〃 |
| ★ **`except*` 갈래는 최대 한 번씩 돌고, 맞는 잎을 모은 묶음을 받는다** | 8.4.2 `except*` clause |
| ★ **안 잡힌 것은 다시 raise 된다** | 〃 · PEP 654 |
| ★ **`except` 와 `except*` 를 한 `try` 에 섞을 수 없다** | 8.4.2 |
| ★ **`except*` 안에서 `break`·`continue`·`return` 을 못 쓴다** | 8.4.2 |
| **묶이지 않은 예외 하나도 `except*` 가 잡는다**(묶어서 준다) | 8.4.2 |
| `asyncio.TaskGroup` 이 **실패를 `ExceptionGroup` 으로** 낸다 | `asyncio` Task Groups |
| 3.11 부터다 | PEP 654 |

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| 괘선 트레이스백의 모양 — `+ Exception Group Traceback` · `+-+---------------- 1 ----------------` | 실행 |
| 괘선 안의 연쇄가 **막대 하나에 공백만 있는 줄**을 만든다 | 실행 — 동작 6 |
| `(3 sub-exceptions)` / `(1 sub-exception)` 단수·복수 표기 | 실행 |
| `SyntaxError` 문구 둘 | 실행 |
| **섞기 오류가 「나중에 나온 쪽」을 가리킨다**(줄 5) | 실행 |
| 예외 문구 — `Cannot nest BaseExceptions in an ExceptionGroup` 등 | 실행 |

### 이 판(3.12.3)의 관찰

| 관찰 | 어디가 흔들리나 |
|---|---|
| ★ **섞기 오류에 캐럿이 있고 `return` 오류에 없는 것** | **단계가 달라서**다. 판이 오르면 메시지가 바뀔 수 있다 — **다른 판은 안 돌려 봤다** |
| 괘선의 가로 길이와 표기 | 판마다 바뀔 수 있다 |
| `TaskGroup` 이 **자식 둘을 모두** 담는 것 | 완료 순서는 보장이 없어 **`sorted()` 로 찍었다** |

### 그래서 이렇게 적으면 틀린다

- ✗ 「`except ValueError` 가 묶음 안의 `ValueError` 를 잡는다」\
  ○ **안 맞는다.** 별 없는 `except` 는 **묶음 자체의 타입**만 본다.
- ✗ 「`except*` 갈래는 하나만 돈다」\
  ○ **맞는 갈래가 전부** 돈다(실측 세 갈래).
- ✗ 「`except*` 갈래는 잎을 하나 받는다」\
  ○ **묶음을 받는다.** 잎 하나여도 포장돼 온다.
- ✗ 「`except*` 를 썼으니 다 잡혔다」\
  ○ **안 잡힌 것은 구조를 유지한 채 올라간다.**
- ✗ 「`len(eg.exceptions)` 가 실패 개수다」\
  ○ **자식 수일 뿐**이다. 잎은 재귀로 센다.
- ✗ 「`except*` 안에서 `return` 은 그냥 안 쓰는 게 좋다」\
  ○ **`SyntaxError` 다.** 쓸 수가 없다.
- ✗ 「두 `SyntaxError` 는 같은 모양으로 나온다」\
  ○ **캐럿이 있는 쪽과 없는 쪽이 있다.** 잡는 단계가 다르다.
- ✗ 「`subgroup` 이 안 맞으면 빈 묶음」\
  ○ **`None`** 이다.
- ✗ 「`split` 이 원본을 바꾼다」\
  ○ **안 바꾼다.** 껍데기를 복사한다.
- ✗ 「`ExceptionGroup` 에 아무 예외나 넣을 수 있다」\
  ○ **`BaseException` 은 못 넣는다**(`TypeError`).

**판정 기준 한 줄**: **「이 갈래가 받는 것이 잎인가 묶음인가」를 물으면 `except` 와 `except*` 가 갈리고,
「이 `SyntaxError` 에 캐럿이 있나」를 물으면 잡은 단계가 갈린다.**

## 언제 쓰고 언제 안 쓰나

| 상황 | 판정 |
|---|---|
| 병렬 작업 여럿이 **각각** 실패할 수 있다 | ★ **`ExceptionGroup`** — `asyncio.TaskGroup` 이 이미 그렇게 낸다 |
| 실패가 **언제나 하나**다 | **쓰지 않는다** — 보통 `raise` 가 읽기 쉽다 |
| 입력을 **전부 검사하고** 문제를 모아 보고한다 | ★ **`ExceptionGroup`** — 첫 오류에서 멈추지 않는다 |
| `TaskGroup` 을 쓰는 코드를 호출한다 | ★ **`except*` 또는 `except BaseExceptionGroup`** — 기존 `except ValueError` 는 안 맞는다 |
| 묶음에서 **종류별로** 처리한다 | `except*` — 갈래가 여러 번 돈다 |
| 묶음을 **코드로** 가른다 | `split`·`subgroup` — 중첩이 보존된다 |
| 갈래에서 **값을 밖으로** 내야 한다 | ★ **`return` 을 못 쓴다** — 변수에 담는다 |
| `KeyboardInterrupt` 가 섞일 수 있다 | **`BaseExceptionGroup`** — 그러면 `except Exception` 에 안 걸린다 |
| 3.10 이하를 지원해야 한다 | ★ **못 쓴다**(3.11+). 백포트 패키지는 **이 노트 범위 밖**이다 |
| 실패가 하나일 때 **검사냐 예외냐** | [26번](../26-eafp-vs-lbyl/2-summary.md) — 이 주제 밖이다 |

## 핵심 문장

- ★★ **`except*` 는 갈래가 여러 번 돈다.** 한 `try` 문에서 세 갈래가 전부 돌았고,
  **별 없는 `except` 는 한 번**만 돈다 — 묶음 **자체의 타입**에만 맞추기 때문이다.
- ★★ **갈래가 받는 것도 묶음이고, 안 잡힌 것도 묶음으로 다시 올라간다.**
  올라갈 때 **원래 중첩 경로가 보존**되고 개수만 줄어든다.
- ★★ **`len(eg.exceptions)` 는 실패 개수가 아니다.** 실측에서 **자식 3, 잎 4** 였다 —
  자식이 또 묶음일 수 있으므로 **재귀로 훑어야** 한다.
- ★★ **`SyntaxError` 가 둘인데 모양이 다르다.**
  **섞기 금지**는 파서가 잡아 **소스 줄과 캐럿이 나오고**,
  **`except*` 안의 `return` 금지**는 심볼 테이블 단계가 잡아 **둘 다 안 나온다.**
- ★ **`except*` 안의 `raise` 는 바꿔치기가 아니라 보태기**다 — 새 예외와 **안 잡힌 나머지**가 같은 봉투에 담긴다.
- ★ **`BaseExceptionGroup(...)` 은 내용물을 보고 클래스를 고른다.** 전부 `Exception` 이면 `ExceptionGroup` 이고,
  `BaseException` 이 섞이면 `BaseExceptionGroup` 이라 **`except Exception` 에 안 걸린다.**
- ★ **`split` 은 `(맞은 것, 남은 것)`, `subgroup` 은 맞은 것만.** 안 맞으면 **`None`** 이고,
  **중첩은 보존되며 원본은 안 바뀐다.** 술어(함수)로도 가른다.
- ★ **묶이지 않은 예외 하나도 `except*` 가 잡는다** — 묶어서 준다. 그래서 갈래 코드가 **한 벌로 통일**된다.
- ★ **이 문법이 생긴 이유는 `asyncio.TaskGroup`** 이다 — 태스크 둘이 각각 실패했을 때
  **어느 하나만 고를 근거가 없기 때문**이다.

## 관련 자료

- 목록: [python/syntax 주제 목록](../README.md) — 이 주제는 **27번**
- 선행: [25-exceptions-and-finally](../25-exceptions-and-finally/2-summary.md) — **예외 계층과 연쇄의 정본.**\
  **경계**: `BaseException`/`Exception` 의 갈라짐과 `__context__`·`__cause__` 는 전부 그쪽.
  여기는 **그것이 괘선 안에서 어떻게 보이나**만 본다.
- 선행: [26-eafp-vs-lbyl](../26-eafp-vs-lbyl/2-summary.md) — 실패가 **하나**일 때의 선택.\
  **경계**: 검사냐 예외냐는 그쪽, **실패가 여럿일 때 어떻게 나르나**는 여기다.
- 이어지는 곳: [28-context-managers-and-with](../28-context-managers-and-with/2-summary.md) —
  `ExitStack` 이 **정리 중 난 예외 여럿**을 다루는 자리다.
- 이어지는 곳: `[목록의 **52번 주제**](../52-asyncio-concurrency-structure/)` — `asyncio.TaskGroup` 의 정본.\
  **경계**: 여기서는 **왜 묶음이 필요했나**만 보이고, 취소 전파·타임아웃은 전부 그쪽이다.
- 다른 갈래: 자바 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **26번** —
  try-with-resources 의 **suppressed exception**. 「정리 중 난 예외를 잃지 않는다」는 같은 문제의식이고,
  자바는 **주 예외에 붙이는 방식**, 파이썬은 **묶음을 새로 만드는 방식**이다.
- 다른 갈래: Go 갈래 목록([`go/syntax/README.md`](../../../go/syntax/README.md))의 **24번** —
  `errors.Join`(1.20). 오류 여럿을 **하나의 값으로 묶는** 같은 자리다.
- 공식 문서: [PEP 654](https://peps.python.org/pep-0654/) ·
  [Exception groups](https://docs.python.org/3.12/library/exceptions.html#exception-groups) ·
  [`except*` clause](https://docs.python.org/3.12/reference/compound_stmts.html#except-star) ·
  [`asyncio.TaskGroup`](https://docs.python.org/3.12/library/asyncio-task.html#task-groups)

## 용어 풀이

- **예외 그룹(exception group)**: 예외 여럿을 자식으로 품는 예외 하나.\
  예: `ExceptionGroup("셋이 깨졌다", [ValueError("v"), TypeError("t")])`
- **`BaseExceptionGroup`**: `BaseException` 까지 담을 수 있는 묶음. **`Exception` 의 하위가 아니다.**\
  예: `KeyboardInterrupt` 가 섞이면 이쪽으로 만들어진다.
- **`ExceptionGroup`**: `Exception` 만 담는 묶음. **`BaseExceptionGroup` 의 하위이자 `Exception` 의 하위**다.\
  예: `except Exception` 에 걸린다.
- **잎(leaf)**: 트리에서 더 안 쪼개지는 진짜 예외.\
  예: 자식이 또 묶음이면 잎이 아니다.
- **`exceptions`**: 묶음의 **직계 자식 튜플**. 잎의 목록이 아니다.\
  예: 실측에서 자식 3, 잎 4.
- **`except*`**: 묶음을 뜯어 **종류별로** 처리하는 절(3.11+).\
  예: 한 `try` 에서 갈래가 여러 번 돈다.
- **분배(distribution)**: 묶음의 잎을 갈래마다 나눠 담는 일.\
  예: 갈래는 **맞는 잎만 모은 새 묶음**을 받는다.
- **가지치기(pruning)**: 잡힌 잎을 뺀 나머지로 **구조를 유지한 채** 새 묶음을 만드는 일.\
  예: 자식 수만 줄고 경로는 그대로다.
- **`subgroup(조건)`**: 맞는 것만 모은 묶음. 안 맞으면 **`None`**.\
  예: 조건은 타입 또는 술어(함수).
- **`split(조건)`**: `(맞은 것, 남은 것)` 튜플.\
  예: 양쪽 다 중첩이 보존된다.
- **괘선 트레이스백(exception group traceback)**: `+`·`|`·`+-+----- 1 -----` 로 트리를 그리는 출력 형식.\
  예: 그 안에 연쇄가 들어가면 `| ` 만 있는 줄이 생긴다.
- **심볼 테이블 단계**: 파싱이 끝난 뒤 이름과 스코프를 정리하는 컴파일 단계.\
  예: 여기서 난 `SyntaxError` 에는 **소스 줄도 캐럿도 없다.**
- **`asyncio.TaskGroup`**: 여러 태스크를 묶어 돌리고 **실패를 묶음으로** 내는 도구(3.11+).\
  예: 이 문법이 생긴 동기다.

## 더 들어가면

- **`derive`** — 묶음의 **껍데기를 복사**해 자식만 바꾸는 훅. 사용자 정의 묶음 클래스가
  `split`/`subgroup` 에서 **자기 타입을 유지**하게 하는 장치다. 이 주제에서는 **안 돌려 봤다.**
- ★ **`traceback` 모듈은 묶음을 재귀로 찍는다** — 괘선은 그 결과다. **직접 호출해 보지는 않았다.**
- ★ **정리 중 난 예외 여럿은 묶음이 되지 않는다** — `with` 도 `ExitStack` 도 **마지막에 닫히는 것 하나**만 올린다.
  나머지는 `__context__` 로 이어지는데, ★★ **`ExitStack` 은 몸통이 멀쩡할 때 그 연결마저 잃는다**(실측).
  그 확인은 [28번](../28-context-managers-and-with/2-summary.md) 동작 10에 있다.
- **백포트** — `exceptiongroup` 패키지가 3.7\~3.10 에 이 API 를 준다.
  표준 라이브러리 밖이라 **이 노트 범위가 아니고, 안 돌려 봤다.**
- ★ **`except*` 는 `try` 문의 모양을 바꾸는 유일한 문법**이다 — 절 하나가 **여러 번 도는** 자리가 파이썬에 달리 없다.
  루프의 몸통과는 다르다. 이 성질 때문에 `break`·`continue`·`return` 이 금지된 것이다.
