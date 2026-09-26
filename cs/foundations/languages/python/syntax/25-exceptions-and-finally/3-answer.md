# python/syntax/25-exceptions-and-finally — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> [1-question.md](1-question.md)의 번호와 **1:1**로 대응한다. 질문 12개 = 답 12개.
>
> 이 파일의 모든 출력은 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> 던지는 형태는 `python3 - <파일` 로 고정했다 — 트레이스백이 `File "<stdin>", line N` 으로 찍히고,
> **실행 중 예외라 소스 줄도 캐럿도 안 나온다.**
> ★ 이 파일의 블록에는 **주소도 시간도 한 곳도 안 찍힌다** — 같은 판에서 다시 돌리면 **한 글자도 안 변한다.**
> 단 **바이트코드 덤프**(7번)와 **예외 문구**는 구현·판에 달린 것이라 다른 판에서는 달라진다(12번 답).

## 정답

### 1. ⑥은 세 묶음 전부, ⑤는 첫 묶음에만 — ②·③·④는 한 번씩

**출력**

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

```text
===== python3 - <e25_order.py =====
[ 예외 없음 ]
  ① try 몸통 시작
  ② try 몸통 끝
  ⑤ else — 예외가 없었다
  ⑥ finally — 언제나 돈다
  ⑦ try 문 다음 줄
[ ValueError — 첫 except 가 잡는다 ]
  ① try 몸통 시작
  ③ except ValueError: 터뜨린다
  ⑥ finally — 언제나 돈다
  ⑦ try 문 다음 줄
[ KeyError — 둘째 except 가 잡는다 ]
  ① try 몸통 시작
  ④ except Exception: KeyError
  ⑥ finally — 언제나 돈다
  ⑦ try 문 다음 줄
(exit 0)
```

**왜 그런가**

레퍼런스가 순서를 그대로 적는다.

> The optional `else` clause is executed if the control flow leaves the `try` suite,
> no exception was raised, and no `return`, `continue`, or `break` statement was executed.

- **첫 묶음(예외 없음)**: ① ② ⑤ ⑥ ⑦ — **`except` 를 건너뛰고 `else` 가 돈다.**
- **둘째 묶음(`ValueError`)**: ① ③ ⑥ ⑦ — ②가 **안 찍혔다.** 예외가 그 앞에서 몸통을 끊었다.
- **셋째 묶음(`KeyError`)**: ① ④ ⑥ ⑦ — `ValueError` 갈래를 **건너뛰고** `Exception` 갈래로 갔다.

★ **안 찍힌 것을 짚는 것이 답이다.**

- **②는 예외가 난 두 묶음에서 안 찍힌다** — 몸통의 나머지가 통째로 날아간다.
- **⑤(`else`)는 예외가 난 두 묶음에서 안 찍힌다** — 그것이 `else` 의 계약이다.
- **③과 ④는 서로 배타다.** `except` 는 **위에서부터 처음 맞는 하나**만 돈다.
- **⑥(`finally`)은 세 묶음 전부**에서 찍힌다.

### 2. ④는 찍히고 ⑤는 안 찍힌다 — 예외가 나가는 길에도 `finally` 는 돈다

**출력**

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

```text
===== python3 - <e25_order_escape.py =====
[ 아무 except 도 안 맞을 때 ]
  ① try 몸통 시작
  ④ finally — 예외가 나가는 길에도 돈다
Traceback (most recent call last):
  File "<stdin>", line 18, in <module>
  File "<stdin>", line 7, in run
RuntimeError: 아무도 안 잡는다
(exit 1)
```

**왜 그런가**

- ★ **④가 찍혔다.** `except` 가 하나도 안 맞아 예외가 밖으로 나가는 중인데도 `finally` 는 돈다.
- ★ **⑤는 안 찍혔다.** `try` 문 **다음 줄**은 예외가 나가면 안 돈다.
  **이 둘을 가르는 것이 이 문항의 전부다** — `finally` 는 「다음 줄」이 아니라 「나가는 길목」이다.
- ③(`else`)도 안 찍혔다. 예외가 났기 때문이다.
- 트레이스백은 **네 줄**이고(`Traceback ...` + 프레임 두 줄 + 예외 줄), 종료 코드는 **1**이다.
- 프레임이 **`<module>` → `run`** 두 개다. 예외가 올라온 칸 수가 그대로 보인다.

```text
   try 몸통에서 RuntimeError 발생
        |
   except ValueError  -> 안 맞는다 (건너뛴다)
        |
   else               -> 안 돈다 (예외가 났다)
        |
   finally            -> ★ 돈다  (④)
        |
   try 문 다음 줄      -> ★ 안 돈다 (⑤)
        |
   호출한 쪽으로 전파  -> 트레이스백 + exit 1
```

### 3. 앞 셋은 예외가 사라지고, 마지막만 예외가 나온다

**출력**

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

```text
===== python3 - <e25_finally_return.py =====
finally 의 return : finally 의 return
finally 의 break  : finally 의 break
finally 의 continue: finally 의 continue
finally 가 pass 면  : 예외가 그대로 나온다 — ValueError 원래 예외
(exit 0)
```

**왜 그런가**

★★ 레퍼런스가 못 박는다.

> If the `finally` clause executes a `return`, `break` or `continue` statement,
> the saved exception is discarded.

- **`return`·`break`·`continue` 셋 다** 예외를 버린다. 던진 `ValueError`·`KeyError`·`IndexError` 가 **흔적도 없다.**
- **마지막 줄이 대조군**이다 — `finally` 가 `pass` 면 예외가 그대로 나와 `except ValueError` 에 잡힌다.
  **`finally` 가 도는 것 자체는 예외를 안 건드린다.** 건드리는 것은 **거기서 나가는 것**이다.
- ★ `continue` 를 `finally` 에 쓰는 것은 **3.8+** 다. 그 전에는 `SyntaxError` 였고, **옛 판은 안 돌려 봤다.**

7번 답의 바이트코드가 **왜 그런지**를 말한다.

### 4. ①②까지 찍히고 ③은 안 찍힌다 — 트레이스백 없이 종료 코드 3

**출력**

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

```text
===== python3 - <e25_systemexit.py =====
① ValueError 를 던진다
  except Exception 이 잡았다: ValueError
② SystemExit 을 던진다 — except Exception 은 못 잡는다
(exit 3)
```

**왜 그런가**

- `SystemExit` 은 **`BaseException` 의 직속 자식**이고 **`Exception` 의 하위가 아니다.**
  그래서 `except Exception` 그물에 **안 걸린다.**
- ③이 **안 찍혔다** — `guarded` 를 지나 `<module>` 까지 올라가 인터프리터를 끝냈다.
- ★★ **트레이스백이 없다.** `SystemExit` 은 조용히 끝낸다 —
  **「출력이 없다」가 출력**이고, 그 증거가 **종료 코드 3**(`sys.exit(3)` 의 인자)이다.

```text
   BaseException
   ├── SystemExit          <- 여기. except Exception 이 못 잡는다
   ├── KeyboardInterrupt   <- Ctrl+C. 같은 이유로 못 잡는다
   ├── GeneratorExit
   └── Exception           <- except Exception 의 그물은 여기 아래뿐
       └── ValueError ...  <- ①은 여기라서 잡혔다
```

★ **일부러 그렇게 갈라 놓았다.** 「오류를 다 잡는」 코드가 **끝내려는 뜻**까지 삼키면 안 되기 때문이다.

### 5. 위쪽 함수의 몸통이 돈다 — ③은 안 찍히고 종료 코드는 4번과 같다

**출력**

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

```text
===== python3 - <e25_bare_except.py =====
① 빈 except:
  빈 except: 가 SystemExit 을 잡았다
② except Exception:
(exit 3)
```

**왜 그런가**

- **빈 `except:` 는 `except BaseException:`** 과 같다. 그래서 **`SystemExit` 을 잡았다** — 프로그램이 안 끝났다.
- 둘째 함수의 `except Exception` 은 못 잡아 그대로 나갔고, **③이 안 찍혔다.**
- 종료 코드는 **3** 으로 4번 문항과 **같다.** 첫 함수가 한 번 막았을 뿐,
  둘째 `sys.exit(3)` 이 결국 통과했기 때문이다.
- ★ **빈 `except:` 를 절대 쓰지 말라는 뜻은 아니다.** 잡아서 **다시 던지면**(`except: ... raise`) 흐름을 안 바꾼다.
  문제는 **삼키는 것**이다 — 그러면 `Ctrl+C` 도 `sys.exit()` 도 안 먹는 프로그램이 된다.

### 6. 다른 줄은 **한 줄** — 연쇄 문구뿐이다

**출력** — `from` 없이 던진 쪽.

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

```text
===== python3 - <e25_chain_implicit.py =====
Traceback (most recent call last):
  File "<stdin>", line 7, in outer
  File "<stdin>", line 2, in inner
ZeroDivisionError: division by zero

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "<stdin>", line 12, in <module>
  File "<stdin>", line 9, in outer
RuntimeError: 바깥 예외
(exit 1)
```

**출력** — `from e` 를 붙인 쪽.

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

```text
===== python3 - <e25_chain_explicit.py =====
Traceback (most recent call last):
  File "<stdin>", line 7, in outer
  File "<stdin>", line 2, in inner
ZeroDivisionError: division by zero

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "<stdin>", line 12, in <module>
  File "<stdin>", line 9, in outer
RuntimeError: 바깥 예외
(exit 1)
```

**출력** — `from None` 을 붙이면.

```python
# e25_chain_none.py
def inner():
    return 1 / 0


def outer():
    try:
        inner()
    except ZeroDivisionError:
        raise RuntimeError("바깥 예외") from None


outer()
```

```text
===== python3 - <e25_chain_none.py =====
Traceback (most recent call last):
  File "<stdin>", line 12, in <module>
  File "<stdin>", line 9, in outer
RuntimeError: 바깥 예외
(exit 1)
```

**왜 그런가**

- 두 프로그램이 **소스에서 `from e` 세 글자**만 다르고, **출력에서 한 줄**만 다르다.
  - `During handling of the above exception, another exception occurred:` — **자동**(`__context__`)
  - `The above exception was the direct cause of the following exception:` — **내가 한 주장**(`__cause__`)
- ★ `from None` 을 주면 **앞 덩어리가 통째로 사라져 네 줄**이 된다(11줄 → 4줄).

속성으로 보면 이렇다.

```python
# e25_chain_attrs.py
def implicit():
    try:
        1 / 0
    except ZeroDivisionError:
        raise RuntimeError("암묵")


def explicit():
    try:
        1 / 0
    except ZeroDivisionError as e:
        raise RuntimeError("명시") from e


def cut():
    try:
        1 / 0
    except ZeroDivisionError:
        raise RuntimeError("끊음") from None


for label, fn in (("except 안에서 그냥 raise", implicit),
                  ("raise ... from e", explicit),
                  ("raise ... from None", cut)):
    try:
        fn()
    except RuntimeError as e:
        print("[", label, "]")
        print("    __cause__            =", repr(e.__cause__))
        print("    __context__          =", repr(e.__context__))
        print("    __suppress_context__ =", e.__suppress_context__)
```

```text
===== python3 - <e25_chain_attrs.py =====
[ except 안에서 그냥 raise ]
    __cause__            = None
    __context__          = ZeroDivisionError('division by zero')
    __suppress_context__ = False
[ raise ... from e ]
    __cause__            = ZeroDivisionError('division by zero')
    __context__          = ZeroDivisionError('division by zero')
    __suppress_context__ = True
[ raise ... from None ]
    __cause__            = None
    __context__          = ZeroDivisionError('division by zero')
    __suppress_context__ = True
(exit 0)
```

| 쓴 것 | `__cause__` | `__context__` | `__suppress_context__` |
|---|---|---|---|
| `except` 안에서 그냥 `raise` | `None` | 원래 예외 | `False` |
| `raise ... from e` | **원래 예외** | 원래 예외 | `True` |
| `raise ... from None` | `None` | **원래 예외(그대로 있다)** | `True` |

★★ **`from None` 은 지우는 것이 아니라 감추는 것**이다 — 11번 답에서 다시 본다.

### 7. 네 벌이고, `return`·`break`·정상·예외 경로에 하나씩 놓인다

**출력**

```python
# e25_dis_finally.py
import dis


def f(xs):
    for x in xs:
        try:
            if x == 1:
                return "R"
            if x == 2:
                break
            if x == 3:
                raise ValueError
        finally:
            done = True
    return "N"


dis.dis(f)
print()
copies = [i.offset for i in dis.get_instructions(f)
          if i.opname == "STORE_FAST" and i.argval == "done"]
print("finally 몸통(done = True)이 놓인 자리:", copies)
print("복제 개수:", len(copies))
```

```text
===== python3 - <e25_dis_finally.py =====
  4           0 RESUME                   0

  5           2 LOAD_FAST                0 (xs)
              4 GET_ITER
        >>    6 FOR_ITER                37 (to 84)
             10 STORE_FAST               1 (x)

  6          12 NOP

  7          14 LOAD_FAST                1 (x)
             16 LOAD_CONST               1 (1)
             18 COMPARE_OP              40 (==)
             22 POP_JUMP_IF_FALSE        5 (to 34)

  8          24 NOP

 14          26 LOAD_CONST               2 (True)
             28 STORE_FAST               2 (done)
             30 POP_TOP
             32 RETURN_CONST             3 ('R')

  9     >>   34 LOAD_FAST                1 (x)
             36 LOAD_CONST               4 (2)
             38 COMPARE_OP              40 (==)
             42 POP_JUMP_IF_FALSE        5 (to 54)

 10          44 NOP

 14          46 LOAD_CONST               2 (True)
             48 STORE_FAST               2 (done)
             50 POP_TOP

 15          52 RETURN_CONST             6 ('N')

 11     >>   54 LOAD_FAST                1 (x)
             56 LOAD_CONST               5 (3)
             58 COMPARE_OP              40 (==)
             62 POP_JUMP_IF_FALSE        6 (to 76)

 12          64 LOAD_GLOBAL              0 (ValueError)
             74 RAISE_VARARGS            1

 11     >>   76 NOP

 14          78 LOAD_CONST               2 (True)
             80 STORE_FAST               2 (done)
             82 JUMP_BACKWARD           39 (to 6)

  5     >>   84 END_FOR

 15          86 RETURN_CONST             6 ('N')
        >>   88 PUSH_EXC_INFO

 14          90 LOAD_CONST               2 (True)
             92 STORE_FAST               2 (done)
             94 RERAISE                  0
        >>   96 COPY                     3
             98 POP_EXCEPT
            100 RERAISE                  1
ExceptionTable:
  14 to 22 -> 88 [1]
  34 to 42 -> 88 [1]
  54 to 74 -> 88 [1]
  88 to 94 -> 96 [2] lasti

finally 몸통(done = True)이 놓인 자리: [28, 48, 80, 92]
복제 개수: 4
(exit 0)
```

**왜 그런가**

- 덤프 끝의 두 줄이 답이다 — **`done = True` 의 `STORE_FAST` 가 네 자리**(`[28, 48, 80, 92]`)에 있다.
- 네 자리가 각각 이렇게 붙어 있다.

```text
   offset 28  ->  바로 뒤 RETURN_CONST 'R'      : return 경로
   offset 48  ->  바로 뒤 RETURN_CONST 'N'      : break 가 빠져나간 자리
   offset 80  ->  바로 뒤 JUMP_BACKWARD         : 정상 종료(다음 회차)
   offset 92  ->  바로 뒤 RERAISE 0             : 예외 경로
```

- ★ **예외 경로의 사본만 뒤에 `RERAISE` 가 붙어 있다.**
  예외를 **다시 던지는 일은 `finally` 사본이 다 끝난 뒤**라는 뜻이다.
- ★★ **그래서 3번 문항이 그렇게 된다** — 그 사본 안에서 `return` 을 만나면 **함수 밖으로 바로 나가고,
  뒤의 `RERAISE` 는 영영 안 돈다.** 예외가 「삼켜지는」 것이 아니라 **다시 던져질 기회를 못 얻는 것**이다.
- `ExceptionTable` 의 세 줄(`14 to 22`·`34 to 42`·`54 to 74` → `88`)은
  **`try` 몸통의 세 조각이 전부 예외 경로 사본으로 간다**고 적는다.

★★ **층을 갈라야 한다.**

- **언어 보장** — 「`finally` 는 나가는 모든 길에서 돈다」 · 「`finally` 의 `return`·`break`·`continue` 는 저장된 예외를 버린다」.
- **CPython 구현** — 「네 벌을 복제해 깐다」 · 「예외 경로 사본 뒤에 `RERAISE` 가 온다」.
- **이 판(3.12.3)의 관찰** — 명령 이름(`RETURN_CONST` 등)과 오프셋 숫자, `ExceptionTable` 표기.
  **다른 판은 안 돌려 봤다.**

### 8. 같은 개념이다 — 둘 다 「탈출 없이 끝까지 갔으면」

**출력**

```python
# e25_else_twins.py
def loop_else(xs, target):
    for x in xs:
        if x == target:
            return "for 몸통이 break 로 나갔다"
    else:
        return "for 의 else — 끝까지 갔다"


def try_else(x):
    try:
        10 / x
    except ZeroDivisionError:
        return "try 몸통이 예외로 나갔다"
    else:
        return "try 의 else — 끝까지 갔다"


print("for  — 찾음  :", loop_else([1, 2, 3], 2))
print("for  — 못 찾음:", loop_else([1, 2, 3], 9))
print("try  — 터짐  :", try_else(0))
print("try  — 안 터짐:", try_else(5))
```

```text
===== python3 - <e25_else_twins.py =====
for  — 찾음  : for 몸통이 break 로 나갔다
for  — 못 찾음: for 의 else — 끝까지 갔다
try  — 터짐  : try 몸통이 예외로 나갔다
try  — 안 터짐: try 의 else — 끝까지 갔다
(exit 0)
```

**왜 그런가**

[18번](../18-loop-control-and-else/2-summary.md)이 `for ... else` 를 **`nobreak`** 라고 읽으라고 적었다.
`try ... else` 도 같다 — **탈출의 종류만** `break` 에서 예외로 바뀐다.

```text
   for ... else              try ... else
   ------------              ------------
   탈출 = break              탈출 = 예외
   탈출하면   else 건너뜀      탈출하면   else 건너뜀
   안 하면    else 돈다        안 하면    else 돈다
```

★ **`else` 를 쓰는 실용적인 이유는 `try` 몸통을 좁히는 것**이다. 절이 하나 느는 값을 그것으로 갚는다.

```python
# e25_else_narrow.py
CODES = {"A": "승인", "D": "거절"}


def without_else(d):
    try:
        raw = d["code"]
        return CODES[raw]
    except KeyError:
        return "code 키가 없다"


def with_else(d):
    try:
        raw = d["code"]
    except KeyError:
        return "code 키가 없다"
    else:
        return CODES[raw]


def report(fn, d):
    try:
        return fn(d)
    except KeyError as e:
        return "KeyError 가 밖으로 나왔다: " + repr(e.args[0])


for label, d in (("키가 아예 없다", {}),
                 ("키는 있고 값이 CODES 에 없다", {"code": "Z"})):
    print("[", label, "]")
    print("    else 없이:", report(without_else, d))
    print("    else 로  :", report(with_else, d))
```

```text
===== python3 - <e25_else_narrow.py =====
[ 키가 아예 없다 ]
    else 없이: code 키가 없다
    else 로  : code 키가 없다
[ 키는 있고 값이 CODES 에 없다 ]
    else 없이: code 키가 없다
    else 로  : KeyError 가 밖으로 나왔다: 'Z'
(exit 0)
```

- 둘째 칸이 갈린다 — **`else` 없이 쓰면 `CODES[raw]` 가 낸 `KeyError` 까지 잡아**
  「code 키가 없다」라고 **거짓 보고**한다. 키는 멀쩡히 있었다.
- ★ **`else` 안에서 난 예외는 바로 위의 `except` 가 안 잡는다.** 그것이 이 절의 계약이고, 좁히기의 원리다.

### 9. 아무것도 안 난다 — 에러도 경고도 없다

**출력**

```python
# e25_except_order.py
import warnings

warnings.simplefilter("error")


def wrong_order(x):
    try:
        return 10 / x
    except Exception:
        return "Exception 이 먼저 잡았다"
    except ZeroDivisionError:
        return "이 갈래는 영원히 안 돈다"


def right_order(x):
    try:
        return 10 / x
    except ZeroDivisionError:
        return "ZeroDivisionError 가 잡았다"
    except Exception:
        return "Exception 이 잡았다"


print("경고를 전부 에러로 올려 두고 돌린다 — 컴파일도 실행도 통과했다.")
print("상위를 먼저 :", wrong_order(0))
print("하위를 먼저 :", right_order(0))
```

```text
===== python3 - <e25_except_order.py =====
경고를 전부 에러로 올려 두고 돌린다 — 컴파일도 실행도 통과했다.
상위를 먼저 : Exception 이 먼저 잡았다
하위를 먼저 : ZeroDivisionError 가 잡았다
(exit 0)
```

**왜 그런가**

- ★★ **`warnings.simplefilter("error")` 로 경고를 전부 에러로 올려 두고 돌렸는데도 통과했다.**
  파이썬은 **도달 불가능한 `except` 절을 알려 주지 않는다.**
- `except Exception` 이 먼저 맞았으므로 아래 `except ZeroDivisionError` 는 **영영 안 돈다.**
- 규칙은 하나다 — **좁은 것부터, 넓은 것은 마지막에.**

★ **자바와 갈리는 자리다.** 자바 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **25번**이 다루는
검사 예외 체계에서는 **도달 불가능한 `catch` 가 컴파일 에러**다.
갈리는 이유는 한 줄로 댈 수 있다 — **파이썬에는 검사 예외도 `throws` 선언도 없고,
어떤 예외가 날 수 있는지를 컴파일러가 알지 못한다.** 알지 못하면 도달 불가능도 판정할 수 없다.

### 10. 안 살아 있다 — `UnboundLocalError` 가 나고, 그것은 `NameError` 의 하위다

**출력**

```python
# e25_as_deleted.py
def keep():
    try:
        1 / 0
    except ZeroDivisionError as e:
        saved = e
        print("  except 안에서 :", repr(e))
    print("  except 를 나온 뒤 locals() 에 'e' 가 있나:", "e" in locals())
    return saved


def touch():
    try:
        1 / 0
    except ZeroDivisionError as e:
        pass
    return e


print("① 다른 이름으로 빼 두면")
print("  밖에서 쓸 수 있다:", repr(keep()))
print("② 이름 e 를 그대로 쓰면")
try:
    touch()
except NameError as ne:
    print("  터진다:", type(ne).__name__, "-", ne)
    print("  NameError 의 하위인가:", isinstance(ne, NameError))
```

```text
===== python3 - <e25_as_deleted.py =====
① 다른 이름으로 빼 두면
  except 안에서 : ZeroDivisionError('division by zero')
  except 를 나온 뒤 locals() 에 'e' 가 있나: False
  밖에서 쓸 수 있다: ZeroDivisionError('division by zero')
② 이름 e 를 그대로 쓰면
  터진다: UnboundLocalError - cannot access local variable 'e' where it is not associated with a value
  NameError 의 하위인가: True
(exit 0)
```

**왜 그런가**

레퍼런스가 이유까지 적는다.

> When an exception has been assigned using `as target`, it is cleared at the end of the `except` clause. …
> This is because with the traceback attached to them, they form a reference cycle with the stack frame,
> keeping all locals in that frame alive until the next garbage collection occurs.

- **예외 객체가 트레이스백을 물고 있고, 트레이스백은 프레임을 물고 있고, 프레임은 그 이름을 물고 있다.**
  고리가 닫히면 **그 프레임의 지역 변수 전부가 다음 GC 까지 살아남는다.**
  그래서 파이썬이 **절이 끝날 때 이름을 지운다.**
- 지워진 이름을 다시 읽으면 **`UnboundLocalError`** 다 —
  「함수 안에서 대입된 적이 있는 이름을 값이 붙기 전에 읽었다」는 뜻이고,
  이것은 [21번](../21-scope-legb-global-nonlocal/2-summary.md)의 규칙 그대로다.
  그리고 **`NameError` 의 하위**다(`True`).
- 쓰려면 **다른 이름으로 빼 둔다**(`saved = e`).

### 11. `None` 이 안 된다 — 바뀌는 것은 `__suppress_context__` 하나다

**출력** — 6번 답의 속성 블록이 그대로 근거다.

```python
# e25_chain_attrs.py
def implicit():
    try:
        1 / 0
    except ZeroDivisionError:
        raise RuntimeError("암묵")


def explicit():
    try:
        1 / 0
    except ZeroDivisionError as e:
        raise RuntimeError("명시") from e


def cut():
    try:
        1 / 0
    except ZeroDivisionError:
        raise RuntimeError("끊음") from None


for label, fn in (("except 안에서 그냥 raise", implicit),
                  ("raise ... from e", explicit),
                  ("raise ... from None", cut)):
    try:
        fn()
    except RuntimeError as e:
        print("[", label, "]")
        print("    __cause__            =", repr(e.__cause__))
        print("    __context__          =", repr(e.__context__))
        print("    __suppress_context__ =", e.__suppress_context__)
```

```text
===== python3 - <e25_chain_attrs.py =====
[ except 안에서 그냥 raise ]
    __cause__            = None
    __context__          = ZeroDivisionError('division by zero')
    __suppress_context__ = False
[ raise ... from e ]
    __cause__            = ZeroDivisionError('division by zero')
    __context__          = ZeroDivisionError('division by zero')
    __suppress_context__ = True
[ raise ... from None ]
    __cause__            = None
    __context__          = ZeroDivisionError('division by zero')
    __suppress_context__ = True
(exit 0)
```

**왜 그런가**

- **`from None` 을 써도 `__context__` 는 `ZeroDivisionError` 그대로**다.
  바뀐 것은 **`__suppress_context__` 가 `True` 가 된 것** 하나뿐이고, 그 플래그가 **출력만** 막는다.
- 그래서 **디버거나 로깅에서는 원인이 여전히 보인다.** 「지웠다」고 믿으면 그 자리에서 틀린다.
- `raise B from A` 를 쓰면 **둘 다 채워진다** — `__cause__` 와 `__context__` 가 **같은 객체**를 가리킨다.
  둘은 배타가 아니다.

```text
   raise B from A                    raise B from None
   ------------------                ------------------
   __cause__   = A                   __cause__   = None
   __context__ = A                   __context__ = A     <- ★ 남아 있다
   __suppress_context__ = True       __suppress_context__ = True

   출력: "the direct cause of"        출력: 앞 덩어리를 안 찍는다
```

### 12. 세 층과 이웃 경계

**왜 그런가**

**언어 보장**(레퍼런스·PEP 가 정한 것)

- 절의 순서와 `else`·`finally` 가 도는 조건(8.4).
- **`finally` 의 `return`·`break`·`continue` 는 저장된 예외를 버린다**(8.4).
- **`as` 로 받은 이름은 절 끝에서 지워진다**(8.4.1).
- `__cause__`/`__context__`/`__suppress_context__` 의 의미(7.8 · PEP 3134).
- `SystemExit`·`KeyboardInterrupt`·`GeneratorExit` 이 `Exception` 의 하위가 **아니다**(Built-in Exceptions).

**CPython 구현 세부사항**

- **`finally` 몸통이 경로마다 복제된다**(이 예에서 네 벌).
- 예외 경로 사본 뒤에 **`RERAISE`** 가 온다.
- `try` 몸통의 조각이 **`ExceptionTable`** 로 예외 경로에 이어진다.
- 예외 **메시지 문구** 전부.

**이 판(3.12.3)의 관찰**

- 명령 이름(`RETURN_CONST`·`POP_JUMP_IF_FALSE`)과 **오프셋 숫자**.
- `ExceptionTable` 의 표기(`lasti`).
- `finally` 안의 `continue` 가 허용되는 것 — **3.8+ 이고 옛 판은 안 돌려 봤다.**

**이웃 경계 한 줄씩**

- **「예외가 싼가 비싼가」는 [26번](../26-eafp-vs-lbyl/2-summary.md)부터다.** 여기는 **문법과 실행 순서**까지고,
  `timeit` 수치는 한 줄도 적지 않는다.
- **「여러 예외를 함께 나르는 것」은 [27번](../27-exception-groups-and-except-star/2-summary.md)부터다.**
  여기는 `ExceptionGroup` 이 **계층 어디에 있는지**만 본다.
- **`try/finally` 를 객체로 굳힌 것이 `with`** 이고, 정본은 [28번](../28-context-managers-and-with/2-summary.md)이다.
  `__exit__` 가 여기의 `finally` 자리에 해당한다.
- **`StopIteration` 이 무엇인가**는 [16번](../16-iterator-protocol/2-summary.md)이 정본이다.
  여기는 그 연쇄 문구를 읽는 예제로만 썼다.

## 실행 검증

| 무엇 | 어디서 | 몇 번 | 구현 의존인가 |
|---|---|---|---|
| 네 절의 실행 순서(마커 ①\~⑦) | `python3` 3.12.3 · Linux x86_64 | 캡처 + 제출 전 재실행 | **아니다** — 언어 보장 |
| `finally` 의 `return`·`break`·`continue` 가 예외를 버리는 것 | 〃 | 〃 | **아니다** — 레퍼런스 명문 |
| `finally` 의 **바이트코드 복제 네 벌** | 〃 | 〃 | ★ **그렇다** — CPython 3.12.3 |
| 예외 계층(`Exception` 인가 아닌가) | 〃 | 〃 | **아니다** — 계층도 |
| 연쇄 두 문구와 세 속성 | 〃 | 〃 | 의미는 명세, **문구는 구현** |
| 빈 `except:` 가 `SystemExit` 을 잡는 것 | 〃 | 〃 | **아니다** |
| `except` 순서가 경고 없이 통과하는 것 | 〃 (경고를 에러로 올려서) | 〃 | **아니다** |
| `as e` 가 절 끝에서 지워지는 것 | 〃 | 〃 | **아니다** — 8.4.1 |
| PEP 479 연쇄 | 〃 | 〃 | **아니다**(3.7+) |
| **안 돌려 본 것** | 3.7 이전 판 · 3.8 이전의 `finally` 안 `continue` · 3.11 이하의 바이트코드 | — | — |

★ **판이 오르면 다시 돌릴 것** — **7번의 `dis` 블록 하나**다. 나머지는 명세에 묶여 있다.
