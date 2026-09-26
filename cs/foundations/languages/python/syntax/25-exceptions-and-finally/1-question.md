# python/syntax/25-exceptions-and-finally — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> ★★ 이 주제에서는 **「무엇이 찍히나」만큼 「몇 번째 줄이 안 찍히나」가 답인 자리가 많다.**
> **안 찍힌 줄을 못 짚으면 반만 맞은 것이다.**
> ★★ **트레이스백이 본체인 묶음이다** — 연쇄 두 문구 중 **어느 쪽이 나오는지**까지 적어야 답이다.
>
> 실행 환경: `python3` **3.12.3** · Linux. 던지는 형태는 `python3 - <파일` 로 고정했다 —
> 트레이스백이 `File "<stdin>", line N` 으로 찍히고, **실행 중 예외에는 소스 줄도 캐럿도 안 나온다.**
> ★ **이 주제는 [16번](../16-iterator-protocol/2-summary.md)·[18번](../18-loop-control-and-else/2-summary.md)을 쓴다.**
> 막히면 「`else` 가 무엇의 짝인가」부터 짚어라.
> ★ **이 사슬은 25 → [26](../26-eafp-vs-lbyl/1-question.md) → [27](../27-exception-groups-and-except-star/1-question.md) → [28](../28-context-managers-and-with/1-question.md)** 로 이어진다.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. 네 절에 마커를 박고 세 번 돌리면 (예측)

```python
# e25_order.py
def run(label, boom, catch):
    print("[", label, "]")
    try:
        print("  ① try 몸통 시작")
        if boom:
            raise catch("터뜨린다")
        print("  ② try 몸통 끝")
    except ValueError as e:
        print("  ③ except ValueError:", e)
    except Exception as e:
        print("  ④ except Exception:", type(e).__name__)
    else:
        print("  ⑤ else — 예외가 없었다")
    finally:
        print("  ⑥ finally — 언제나 돈다")
    print("  ⑦ try 문 다음 줄")


run("예외 없음", False, ValueError)
run("ValueError — 첫 except 가 잡는다", True, ValueError)
run("KeyError — 둘째 except 가 잡는다", True, KeyError)
```

- 세 묶음에서 **각각 몇 줄이 어떤 차례로** 찍히는가?
- ★ **한 번도 안 찍히는 마커**가 있는가? 있다면 어느 것이고 왜 그런가?

### 2. 아무 `except` 도 안 맞을 때 (예측)

```python
# e25_order_escape.py
import sys


def run():
    try:
        print("  ① try 몸통 시작", file=sys.stderr)
        raise RuntimeError("아무도 안 잡는다")
    except ValueError:
        print("  ② except ValueError", file=sys.stderr)
    else:
        print("  ③ else", file=sys.stderr)
    finally:
        print("  ④ finally — 예외가 나가는 길에도 돈다", file=sys.stderr)
    print("  ⑤ 이 줄은 안 돈다", file=sys.stderr)


print("[ 아무 except 도 안 맞을 때 ]", file=sys.stderr)
run()
```

- ④와 ⑤ 중 **찍히는 것과 안 찍히는 것**은?
- 트레이스백은 **몇 줄**이고 종료 코드는 무엇인가?

### 3. `finally` 에서 빠져나가는 세 가지 (예측)

```python
# e25_finally_return.py
def swallow_return():
    try:
        raise ValueError("원래 예외")
    finally:
        return "finally 의 return"


def swallow_break():
    for _ in range(1):
        try:
            raise KeyError("원래 예외")
        finally:
            break
    return "finally 의 break"


def swallow_continue():
    for _ in range(1):
        try:
            raise IndexError("원래 예외")
        finally:
            continue
    return "finally 의 continue"


def keep():
    try:
        raise ValueError("원래 예외")
    finally:
        pass


print("finally 의 return :", swallow_return())
print("finally 의 break  :", swallow_break())
print("finally 의 continue:", swallow_continue())
try:
    keep()
except ValueError as e:
    print("finally 가 pass 면  : 예외가 그대로 나온다 —", type(e).__name__, e)
```

- 네 줄이 각각 무엇을 찍는가?
- ★ 마지막 줄이 **대조군**이다. 앞 셋과 무엇이 다른가?

### 4. `except Exception` 이 쳐 놓은 그물 (예측)

```python
# e25_systemexit.py
import sys


def boom_value():
    raise ValueError("보통 예외")


def boom_exit():
    sys.exit(3)


def guarded(what):
    try:
        what()
    except Exception as e:
        print("  except Exception 이 잡았다:", type(e).__name__, file=sys.stderr)
    else:
        print("  아무 일도 없었다", file=sys.stderr)


print("① ValueError 를 던진다", file=sys.stderr)
guarded(boom_value)

print("② SystemExit 을 던진다 — except Exception 은 못 잡는다", file=sys.stderr)
guarded(boom_exit)

print("③ 이 줄은 안 돈다", file=sys.stderr)
```

- ①②③ 중 **찍히는 것**은 어디까지인가?
- ★ 이 프로그램의 **종료 코드**는 무엇이고, **트레이스백은 나오는가**?

### 5. 타입을 안 적은 `except` (예측)

```python
# e25_bare_except.py
import sys


def with_bare_except():
    try:
        sys.exit(3)
    except:
        print("  빈 except: 가 SystemExit 을 잡았다", file=sys.stderr)


def with_exception():
    try:
        sys.exit(3)
    except Exception:
        print("  이 줄은 안 찍힌다", file=sys.stderr)


print("① 빈 except:", file=sys.stderr)
with_bare_except()
print("② except Exception:", file=sys.stderr)
with_exception()
print("③ 이 줄은 안 돈다", file=sys.stderr)
```

- 두 함수 중 **몸통이 도는 쪽**은 어디인가?
- ★ ③은 찍히는가? 종료 코드는 4번 문항과 같은가 다른가?

### 6. 한 줄만 다른 두 프로그램 (예측)

```python
# e25_chain_implicit.py
def inner():
    return 1 / 0


def outer():
    try:
        inner()
    except ZeroDivisionError:
        raise RuntimeError("바깥 예외")


outer()
```

```python
# e25_chain_explicit.py
def inner():
    return 1 / 0


def outer():
    try:
        inner()
    except ZeroDivisionError as e:
        raise RuntimeError("바깥 예외") from e


outer()
```

- 두 출력에서 **다른 줄은 정확히 몇 줄**이고 무엇인가?
- ★ 마지막 줄에 `from None` 을 쓰면 출력이 **몇 줄로 줄어드는가**?

### 7. `finally` 가 바이트코드에서 몇 벌인가 (왜)

- 소스에는 `finally:` 가 한 번 적혀 있다. CPython 이 **몇 벌**을 깔고, 그 벌들은 **어느 경로**에 하나씩 놓이는가?
- ★ 그 사실이 **「`finally` 의 `return` 이 예외를 삼킨다」를 어떻게 설명**하는가?
- ★ 이 설명 중 **언어 보장인 부분과 CPython 구현인 부분**을 갈라 말할 수 있는가?

### 8. `else` 는 무엇의 짝인가 (연결)

- `try ... else` 의 `else` 와 [18번](../18-loop-control-and-else/2-summary.md)의 `for ... else` 는 **같은 개념인가 다른 개념인가**?
- ★ `else` 를 쓰는 **실용적인 이유**를 한 줄로 댈 수 있는가 — 절이 하나 느는 값을 무엇으로 갚는가?
- `else` 안에서 난 예외는 **바로 위의 `except` 가 잡는가**?

### 9. `except` 를 넓은 것부터 쓰면 (경계)

- `except Exception:` 을 `except ZeroDivisionError:` **위에** 뒀다. **정의 때 무엇이 나는가** — 에러? 경고? 아무것도?
- ★ 경고를 전부 에러로 올려 두고 돌리면 달라지는가?
- 자바 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **25번**과 **여기가 갈리는 이유**를 한 줄로 댈 수 있는가?

### 10. `as e` 로 받은 이름의 수명 (경계)

- `except ValueError as e:` 절을 **빠져나온 뒤** 이름 `e` 는 살아 있는가?
- ★ 그것을 읽으면 **무슨 예외**가 나고, 그 예외는 **어느 예외의 하위**인가?
- 레퍼런스가 든 **그렇게 만든 이유**를 댈 수 있는가?

### 11. `from None` 이 지우는 것 (경계)

- `raise B from None` 을 쓰면 `B.__context__` 는 **`None` 이 되는가**?
- ★ 그러면 **무엇이 바뀌어서** 앞 덩어리가 안 보이는가?
- `raise B from A` 를 쓰면 `__cause__` 와 `__context__` 중 **몇 개가** 채워지는가?

### 12. 세 층 가르기와 이웃 경계 (경계)

- 이 주제에서 **언어 보장** · **CPython 구현 세부사항** · **이 판(3.12.3)의 관찰**에 해당하는 것을 각각 둘 이상 댈 수 있는가?
- **「예외가 싼가 비싼가」가 어디부터 [26번](../26-eafp-vs-lbyl/2-summary.md)이고, 「여러 예외를 함께 나르는 것」이 어디부터 [27번](../27-exception-groups-and-except-star/2-summary.md)인지** 한 줄로 그을 수 있는가?
- `try/finally` 를 **객체로 굳힌 것**이 무엇이고 그 정본은 어디인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
