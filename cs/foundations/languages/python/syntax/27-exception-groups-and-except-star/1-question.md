# python/syntax/27-exception-groups-and-except-star — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> ★★ 이 주제에서는 **「몇 개인가」와 「몇 번 도는가」가 답인 자리가 많다.**
> **자식 수와 잎 수를 구분해 적어야** 맞은 것이다.
> ★★ **트레이스백이 본체인 묶음이다** — 이 주제의 트레이스백에는 **괘선**(`+`·`|`)이 붙는다.
> 그 안에 연쇄가 들어가면 **`| ` 만 있는 줄**까지 생긴다. 모양째 예측해 보라.
>
> 실행 환경: `python3` **3.12.3** · Linux. 던지는 형태는 `python3 - <파일` 로 고정했다.
> ★★ **이 주제에는 `SyntaxError` 가 둘 있고 둘의 모양이 다르다**(6번 문항) —
> **소스 줄과 캐럿이 나오는 쪽과 안 나오는 쪽**을 갈라 적어야 답이다.
> ★ **이 주제는 3.11+ 다.** 그 아래에서는 문법 자체가 없다.
> ★ **이 사슬은 [25](../25-exceptions-and-finally/1-question.md) → [26](../26-eafp-vs-lbyl/1-question.md) → 27 → [28](../28-context-managers-and-with/1-question.md)** 로 이어진다.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. 묶음을 재귀로 훑으면 (예측)

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

- 트리 그림이 **몇 줄** 찍히고 들여쓰기가 어떻게 되는가?
- ★ 아래 네 줄에서 **`맨 위 자식 수` 와 `잎 수` 가 같은가**? 다르다면 왜 다른가?
- `exceptions` 의 타입은 무엇인가?

### 2. `except*` 를 세 갈래 쓰면 (예측)

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

- **몇 개의 갈래가 도는가**? 마지막 줄에 무엇이 찍히는가?
- ★ 각 갈래가 받는 `group` 의 **타입**은 무엇인가?
- ★ `ValueError` 갈래의 **자식 수**와 **잎 목록**이 왜 어긋나는가?

### 3. 별을 뗀 `except` 로 같은 묶음을 잡으면 (예측)

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

- 두 갈래 중 **도는 것**은 어느 쪽인가?
- ★ ②까지 찍히는가?

### 4. 한 갈래만 써 두면 (예측)

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

- **마지막 줄이 찍히는가**?
- ★ 트레이스백에 남은 묶음의 **중첩 깊이**는 얼마이고, `(N sub-exception)` 의 N 은 얼마인가?
- ★ 원래 묶음과 견주면 **무엇이 없어지고 무엇이 남았는가**?

### 5. 갈래 안에서 새 예외를 던지면 (예측)

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

- 맨 위 묶음의 **자식이 몇 개**인가?
- ★ 그중 **새로 던진 것**은 몇 번 칸에 있고, 원래 예외와 **어떤 문구**로 이어져 있는가?
- ★ 나머지 칸에는 무엇이 들어 있는가 — 「바꿔치기」인가 「보태기」인가?

### 6. `except*` 를 쓴 두 프로그램 (예측)

```python
# e27_syntax_mix.py
try:
    pass
except* ValueError:
    pass
except TypeError:
    pass
```

```python
# e27_syntax_return.py
def f():
    try:
        pass
    except* ValueError:
        return 1
```

- 두 출력이 **각각 몇 줄**인가?
- ★★ **소스 줄과 캐럿이 나오는 쪽은 어느 쪽**이고, 왜 갈리는가?
- ★ 첫째 출력의 **줄 번호**는 몇이고, 그것이 가리키는 것은 **먼저 쓴 절인가 나중에 쓴 절인가**?

### 7. `split` 과 `subgroup` (경계)

- 둘이 돌려주는 것의 **개수**가 어떻게 다른가?
- ★ 중첩된 묶음을 가르면 **안쪽 껍데기는 어떻게 되는가**?
- 아무것도 안 맞으면 무엇이 나오는가 — 빈 묶음인가 `None` 인가?
- 조건 자리에 **타입 말고** 무엇을 줄 수 있는가?

### 8. 봉투에 무엇을 담을 수 있나 (경계)

- `ExceptionGroup` 에 `KeyboardInterrupt` 를 넣으면 무엇이 나는가?
- ★ `BaseExceptionGroup("...", [ValueError()])` 를 부르면 **무슨 클래스**가 만들어지는가?
- 빈 리스트로 만들면?
- ★ **묶이지 않은 예외 하나**를 던졌을 때 `except*` 가 잡는가?

### 9. `except*` 의 나머지 규칙 (경계)

- 같은 타입을 `except*` 로 **두 번** 쓰면 문법 오류인가? 오류가 아니라면 **둘 다 도는가**?
- ★ `else` 와 `finally` 를 붙일 수 있는가?
- 맞는 갈래가 **하나도 없으면** 어떻게 되는가?

### 10. 왜 만들었나 (연결)

- 이 문법이 생긴 **동기**를 한 줄로 댈 수 있는가?
- ★ 표준 라이브러리에서 이것을 처음 크게 쓴 것은 무엇이고 **몇 판부터**인가?
- 그 도구를 쓰는 코드를 호출할 때 **기존 `except ValueError` 는 왜 안 맞는가**?

### 11. 다른 갈래는 같은 문제를 어떻게 푸나 (연결)

- 자바 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **26번**이 다루는 **suppressed exception** 과
  이 주제는 **무엇이 같고 무엇이 다른가**?
- ★ Go 갈래 목록([`go/syntax/README.md`](../../../go/syntax/README.md))의 **24번**의 `errors.Join` 은 어느 쪽에 가까운가?

### 12. 세 층 가르기와 이웃 경계 (경계)

- 이 주제에서 **언어 보장** · **CPython 구현 세부사항** · **이 판(3.12.3)의 관찰**에 해당하는 것을 각각 둘 이상 댈 수 있는가?
- ★ **괘선 트레이스백은 어느 층**인가?
- **「예외 계층과 연쇄」가 어디부터 [25번](../25-exceptions-and-finally/2-summary.md)이고, 「`TaskGroup` 의 취소 전파」가 어디부터인지** 한 줄로 그을 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
