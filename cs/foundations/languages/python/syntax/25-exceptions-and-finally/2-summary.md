# python/syntax/25-exceptions-and-finally — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만.
> - [8.4. The `try` statement](https://docs.python.org/3.12/reference/compound_stmts.html#the-try-statement) — 네 절의 실행 순서, `finally` 의 `return`·`break`·`continue`
> - [7.8. The `raise` statement](https://docs.python.org/3.12/reference/simple_stmts.html#the-raise-statement) — `from` 과 `__cause__`·`__context__`·`__suppress_context__`
> - [Built-in Exceptions](https://docs.python.org/3.12/library/exceptions.html) — 예외 계층도와 `BaseException` 의 네 직속 자식
> - [8.4.1. `except` clause](https://docs.python.org/3.12/reference/compound_stmts.html#except-clause) — `as` 로 받은 이름이 절 끝에서 **지워지는** 것
> - [PEP 3134 — Exception Chaining and Embedded Tracebacks](https://peps.python.org/pep-3134/) · [PEP 479](https://peps.python.org/pep-0479/)
> - [`dis`](https://docs.python.org/3.12/library/dis.html) — 바이트코드
>
> **실행 검증** — 이 문서에 실린 출력은 전부 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.\
> ★ **던지는 형태를 하나로 고정했다** — `python3 - <파일` 로 던져 트레이스백이 `File "<stdin>", line N` 이 된다.
> 이 주제의 예외는 전부 **실행 중 예외**라 소스 줄도 캐럿도 안 나온다
> (`SyntaxError` 는 둘 다 나오는데, 이 주제에는 하나도 없다 — [27번](../27-exception-groups-and-except-star/2-summary.md)에 둘 다 있다).\
> ★★ **이 묶음은 트레이스백이 본체다.** 연쇄 블록의 **빈 줄까지** 출력 그대로다 — 손으로 옮긴 것이 한 글자도 없고,
> 캡처 파일을 조립기로 끼워 넣었다.\
> **버전** — `try`/`except`/`else`/`finally` 와 `raise ... from` 은 이 노트 범위(3.10\~3.13)에서 안 바뀌었다.
> 갈리는 것 둘 — **`finally` 안의 `continue` 가 3.8 부터** 허용된다(그 전에는 `SyntaxError`) ·
> **제너레이터 안에서 샌 `StopIteration` 이 `RuntimeError` 가 되는 것이 3.7 부터**(PEP 479).
> 3.8 이전 판은 이 머신에 없어 **옛 동작은 직접 못 돌려 봤다** — 문서·PEP 근거다.\
> **구현 대 언어 보장 한 줄** — **「네 절의 실행 순서와 `finally` 가 언제나 돈다」까지가 언어 보장**이고,
> **`dis` 로 본 「`finally` 가 경로마다 복제된다」는 CPython 구현**이다. 두 층을 절마다 갈라 적었다.\
> **★ 흔들리는 칸 / 안 흔들리는 칸** — 재대조에서 「고칠 것」과 「설계상 안 맞는 것」을 기계적으로 가르려고 미리 선언한다.
>
> | 흔들린다 | 안 흔들린다(근거로 써도 되는 칸) |
> |---|---|
> | (판이 오르면) 바이트코드 **명령 이름·오프셋**·`ExceptionTable` 의 숫자 | `finally` 몸통의 **복제 개수 4** · 그것이 놓인 **경로의 종류** |
> | (판이 오르면) 예외 **메시지 문구** | 예외 **종류** · 연쇄 두 문구 · `File "<stdin>", line N` |
> | — | **실행 순서 마커**(①\~⑦) · `__cause__`·`__context__`·`__suppress_context__` 값 · **종료 코드** |
>
> ★ **이 주제의 블록에는 주소도 시간도 한 곳도 안 찍힌다.** 같은 판에서 다시 돌리면 **한 글자도 안 변한다**
> (`dis` 블록 하나만 판이 오르면 통째로 바뀐다).\
> **선행** — [16-iterator-protocol](../16-iterator-protocol/2-summary.md)(`StopIteration` 이 정상 신호라는 것 — **PEP 479 의 정본**) ·
> [18-loop-control-and-else](../18-loop-control-and-else/2-summary.md)(**`for` 의 `else` — 같은 「else」 개념**) ·
> [05-truthiness-and-short-circuit](../05-truthiness-and-short-circuit/2-summary.md)(진릿값).\
> **이 사슬** — 25 → [26](../26-eafp-vs-lbyl/2-summary.md) → [27](../27-exception-groups-and-except-star/2-summary.md) → [28](../28-context-managers-and-with/2-summary.md).
> 여기가 **문법의 정본**이고, 26 은 **고르는 법**, 27 은 **여러 개를 함께 나르는 법**, 28 은 **`finally` 를 객체로 굳힌 것**이다.

## 한눈에 — 쉽게 말하면

**`try` 문은 「불이 나도 가스 밸브는 잠그고 나간다」를 문법으로 만든 것이다.**

- `try` — 불이 날 수도 있는 일을 한다.
- `except` — 불이 **나면** 그 불에 맞는 소화기를 든다.
- `else` — 불이 **안 났을 때만** 하는 뒷일.
- `finally` — **불이 났든 안 났든**, 심지어 **창문으로 뛰어내리든**(`return`) 가스 밸브는 잠근다.

```text
        try 몸통
          |
     예외가 났나?
      /        \
    예            아니오
     |             |
  except        else
     |             |
     +------+------+
            |
         finally        <- 어느 길로 오든 반드시 지난다
            |
     try 문 다음 줄
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 불이 날 수도 있는 일 | `try` 몸통 | 마커 ①②가 찍히나 |
| 불에 맞는 소화기 | `except <타입>` | **위에서부터 처음 맞는 것 하나**만 돈다 |
| 불이 안 났을 때만 하는 뒷일 | `else` | `break` 없이 끝난 `for` 의 `else` 와 **같은 말** |
| 나가는 길목의 가스 밸브 | `finally` | 마커 ⑥이 **네 경로 전부**에서 찍힌다 |
| ★ **밸브 잠그다가 창문으로 뛰어내리면** | `finally` 안의 `return`·`break`·`continue` | **원래 예외가 사라진다** |
| 불이 난 자리를 적어 두는 수첩 | `__context__` | `except` 안에서 새로 던지면 자동으로 붙는다 |
| 「이 불이 저 불 때문이다」라고 손으로 적기 | `raise ... from e` → `__cause__` | 트레이스백 **문구가 바뀐다** |
| ★ **소화기로 못 끄는 것** | `SystemExit`·`KeyboardInterrupt` | `except Exception` 이 **안 잡는다** |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.\
「**`finally` 에 `return` 을 썼더니 예외가 사라져 장애 원인을 못 찾았다**」와
「**`except Exception` 으로 다 잡는 줄 알았는데 `Ctrl+C` 가 안 먹었다**」가 그것이다.\
둘 다 **에러가 안 난다** — 조용히 다르게 동작할 뿐이다.

> **예외(exception)** — 「여기서는 더 못 간다」를 값으로 만들어 **호출한 쪽으로 되던지는** 장치.\
> 예: `1 / 0` 이 `ZeroDivisionError` 라는 객체를 만들어 던진다.

> **전파(propagate)** — 잡히지 않은 예외가 **부른 쪽으로 한 칸씩 올라가는** 것.\
> 예: `inner` 에서 난 예외가 `outer` 로, 거기서도 안 잡히면 `<module>` 로 올라간다.

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

1. **네 절이 어떤 차례로 도는가** — `else` 는 무엇의 「아니면」인가, `finally` 는 정말 **언제나** 도는가.
2. **`except Exception` 은 무엇을 못 잡는가** — 「전부 잡는다」가 맞는 말인가.
3. **`finally` 에서 나가면 원래 예외는 어디로 가는가** — 그리고 그것을 **바이트코드로 확인할 수 있는가.**

★ 셋째 질문이 이 주제의 인출 목표다. **「`finally` 가 예외를 삼킬 수 있다」를 아는 것과, 「왜 그런 구조인지」를 대는 것**이 아는 것과 들은 것의 경계다.

## 동작 방식

> 이 절이 본문이다. 이 주제의 네 번째 창은 **`dis`** 다 —
> 「`finally` 가 언제나 돈다」는 소스만 보면 **한 덩어리로 보이는데**, 바이트코드에서는 **한 덩어리가 아니다.**
> 복제된 사본이 경로마다 하나씩 놓여 있고, **그 사실이 「`finally` 의 `return` 이 예외를 삼키는」 이유**다.

### 1. ★ 네 절의 실행 순서 — 마커를 찍어 전수로 본다

**언제 쓰나** — `try` 문을 쓸 때마다. 「`else` 는 뭐 하는 절이지」가 막힐 때.

레퍼런스가 순서를 그대로 적는다.

> If no exception occurs, the `except` clause is skipped and execution of the `try` statement is finished. …
> If the execution of the `try` clause raises an exception, … an `except` clause is selected depending on the class of the exception. …
> The optional `else` clause is executed if the control flow leaves the `try` suite, no exception was raised, and no `return`, `continue`, or `break` statement was executed.

```text
   예외 없음          ValueError         KeyError           아무도 안 잡음
   ---------          ----------         --------           -------------
   ① try 시작         ① try 시작          ① try 시작          ① try 시작
   ② try 끝            (예외)              (예외)              (예외)
   ⑤ else             ③ except Value     ④ except Except     (안 맞음)
   ⑥ finally          ⑥ finally          ⑥ finally          ⑥ finally
   ⑦ 다음 줄          ⑦ 다음 줄           ⑦ 다음 줄           (예외가 나간다)

   ★ ⑥은 네 칸 전부에 있고, ⑦은 마지막 칸에만 없다
```

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

- **`else` 는 「예외가 없었을 때만」** 돈다(⑤가 첫 칸에만 찍혔다).
- **`except` 는 위에서부터 처음 맞는 것 하나**만 돈다 — `KeyError` 는 `ValueError` 갈래를 건너뛰고 `Exception` 갈래로 갔다.
- **`finally`(⑥)는 세 칸 전부에서** 찍혔다.

네 번째 칸 — **아무 `except` 도 안 맞을 때**를 따로 던졌다.

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

- ★ **예외가 밖으로 나가는 길에도 `finally`(④)가 돈다.** 그러고 나서 트레이스백이 찍혔다.
- ⑤가 안 찍혔다 — `try` 문 **다음 줄**은 안 돈다. `finally` 는 「다음 줄」이 아니라 「**나가는 길목**」이다.

**비용** — 절이 넷이면 읽는 사람이 **네 경로를 머릿속에서 돌려야** 한다.
`else` 를 안 쓰면 절은 줄지만 `try` 몸통이 넓어진다(동작 2).

### 2. ★ `else` 는 「끝까지 갔으면」 — `for` 의 `else` 와 같은 말이다

**언제 쓰나** — `try` 몸통이 두 줄 이상일 때. 거의 언제나다.

[18번](../18-loop-control-and-else/2-summary.md)이 `for ... else` 를 「**`nobreak`** 라고 읽어야 맞는다」고 적었다.
`try ... else` 도 똑같다 — 「**탈출이 없었으면**」이다. 탈출의 종류만 다르다.

```text
   for ... else              try ... else
   ------------              ------------
   탈출 = break              탈출 = 예외
   탈출했으면 else 건너뜀     탈출했으면 else 건너뜀
   끝까지 갔으면 else 돈다     끝까지 갔으면 else 돈다
```

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

**그래서 `else` 가 왜 필요한가** — `try` 몸통을 **한 줄로 좁히기 위해서**다.
몸통이 넓으면 **엉뚱한 곳에서 난 같은 종류의 예외**를 잡아 거짓 보고를 한다.

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

- 첫 칸(키가 아예 없다)은 **둘이 같다.**
- ★★ 둘째 칸이 갈린다 — **`else` 없이 쓰면 `CODES[raw]` 가 낸 `KeyError` 까지 잡아**
  「code 키가 없다」라고 **거짓으로 보고**한다. 키는 멀쩡히 있었다.
- `else` 로 옮기면 **그 자리의 `KeyError` 는 위 `except` 가 안 잡는다** — 밖으로 나와 진짜 원인이 보인다.

★ **이것이 이 주제의 조용한 실패다.** 에러도 경고도 없고, **답만 틀린다.**

**비용** — 절이 하나 는다. 대신 **`try` 로 감싼 범위가 한 줄로 좁아진다** — 그 교환이 `else` 의 전부다.

### 3. ★★ `finally` 는 나가는 길마다 **복제된다** (CPython 구현)

**언제 쓰나** — 「`finally` 가 언제나 돈다」의 **이유**를 알고 싶을 때. 그리고 동작 4가 왜 그런지 물을 때.

소스에서는 `finally:` 가 **한 번** 적혀 있다. 그런데 나가는 길은 넷이다 —
**정상 종료 · `return` · `break` · 예외.** CPython 은 그 넷에 **사본을 하나씩 깔아 둔다.**

```text
   소스 (한 번 적는다)              바이트코드 (네 벌이 깔린다)
   --------------------            ------------------------------
   for x in xs:                     return 경로   -> finally 사본 ①
       try:                         break  경로   -> finally 사본 ②
           ... return / break /     정상   경로   -> finally 사본 ③
               raise                예외   경로   -> finally 사본 ④ + RERAISE
       finally:
           done = True              ★ "언제나 돈다" 는 런타임 검사가 아니라
                                      컴파일러가 네 벌을 깔아 둔 결과다
```

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

그림 해설 — 덤프에서 무엇을 읽나.

- 끝의 두 줄이 답이다 — **`done = True` 의 `STORE_FAST` 가 네 자리에 있다**(`[28, 48, 80, 92]`).
- 그 넷이 각각 `RETURN_CONST 'R'`(return) · `RETURN_CONST 'N'`(break 가 빠져나간 자리) ·
  `JUMP_BACKWARD`(다음 회차) · `RERAISE`(예외) **바로 앞**에 있다.
- 마지막 사본만 뒤에 **`RERAISE 0`** 이 붙어 있다 — **예외를 다시 던지는 일은 `finally` 사본이 끝난 뒤**다.
- `ExceptionTable` 의 세 줄(`14 to 22`·`34 to 42`·`54 to 74`)이 **`try` 몸통의 세 조각이 전부 88 번으로 간다**고 적는다.
  88 번이 예외 경로의 `finally` 사본이다.

★★ **`dis` 결과는 CPython 3.12.3 의 구현이지 언어 보장이 아니다.**
언어가 보장하는 것은 「`finally` 는 언제나 돈다」까지이고, **「네 벌을 깐다」는 이 구현의 사정**이다.
★ 판이 오르면 명령 이름도 오프셋도 바뀐다. **안 흔들리는 것**은 「복제 개수 4」와 「어느 경로에 놓였나」다.

**비용** — 코드 크기가 는다. `finally` 몸통이 크면 **그 몸통이 네 벌 복사**된다.

### 4. ★★ `finally` 에서 나가면 원래 예외가 **사라진다**

**언제 쓰나** — `finally` 안에 `return`·`break`·`continue` 를 쓰고 싶어질 때. **쓰지 마라**는 근거가 여기 있다.

레퍼런스가 못 박는다.

> If the `finally` clause executes a `return`, `break` or `continue` statement,
> the saved exception is discarded.

**「버려진다(discarded)」 — 언어 보장이다.** 동작 3의 그림이 그 이유를 설명한다 —
예외 경로의 `finally` 사본에서 `return` 을 만나면 **뒤에 오는 `RERAISE` 까지 못 간다.**

```text
   예외 경로의 finally 사본

   [ finally 몸통 ]  ->  RERAISE      <- 여기까지 와야 예외가 다시 던져진다
         |
         +-- return 을 만나면 여기서 함수 밖으로 나간다
             RERAISE 는 영영 안 돈다  -> 예외가 사라진다
```

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

- **`return`·`break`·`continue` 셋 다** 예외를 삼켰다. 던진 `ValueError`·`KeyError`·`IndexError` 가 **흔적도 없다.**
- 마지막 줄이 대조군이다 — **`finally` 가 `pass` 면** 예외가 그대로 나온다.
- ★ **`continue` 는 3.8 부터** 이 자리에 쓸 수 있다. 그 전에는 `SyntaxError` 였다 — **옛 판은 안 돌려 봤다.**

★★ **이것이 이 주제에서 가장 비싼 사고다.** 로그도 안 남고 트레이스백도 안 뜬다.
**「예외가 없었던 것처럼」** 보인다.

**비용** — 없다. **쓰지 않으면 된다.** `finally` 는 **정리만** 하고 흐름은 안 바꾼다.

### 5. `try` 의 `return` 값은 **먼저 계산되고**, `finally` 는 그 뒤에 돈다

**언제 쓰나** — 「`finally` 가 돌면 `return` 값이 바뀌나」가 궁금할 때.

```python
# e25_return_order.py
import sys

log = []


def value(tag):
    log.append(tag)
    return tag


def f():
    try:
        return value("try 의 return 값")
    finally:
        log.append("finally")


out = f()
print("돌려받은 것:", out)
print("찍힌 차례  :", log)
```

```text
===== python3 - <e25_return_order.py =====
돌려받은 것: try 의 return 값
찍힌 차례  : ['try 의 return 값', 'finally']
(exit 0)
```

- 찍힌 차례가 **`['try 의 return 값', 'finally']`** 다 — **값을 먼저 만들고** `finally` 가 돈다.
- 돌려받은 것은 그 값 그대로다. **`finally` 가 값을 덮어쓰지 않는다** — 덮어쓰려면 동작 4처럼 `finally` 안에서 **직접 `return`** 해야 한다.

**비용** — 없다. 다만 **`finally` 안에서 그 값을 고치려 들면** 동작 4의 사고로 넘어간다.

### 6. ★ 예외 계층 — `Exception` 은 `BaseException` 의 **일부**다

**언제 쓰나** — `except Exception` 을 쓸 때마다. 그리고 「`Ctrl+C` 가 안 먹는다」를 만났을 때.

```text
   BaseException                  <- 뿌리. 모든 예외가 여기 아래 있다
   ├── SystemExit                 <- sys.exit()
   ├── KeyboardInterrupt          <- Ctrl+C
   ├── GeneratorExit              <- 제너레이터 close()
   └── Exception                  <- "프로그램이 다루는 오류" 는 여기부터
       ├── ValueError · KeyError · ZeroDivisionError · StopIteration · ...
       └── ExceptionGroup         <- 27번. BaseExceptionGroup 을 거쳐 온다

   ★ except Exception 은 위 세 형제를 못 잡는다 — 일부러 그렇게 갈라 놓았다
```

```python
# e25_hierarchy.py
classes = [BaseException, Exception, SystemExit, KeyboardInterrupt,
           GeneratorExit, BaseExceptionGroup, ExceptionGroup,
           ValueError, KeyError, ZeroDivisionError, StopIteration]

print("%-20s %-16s %s" % ("이름", "Exception 인가", "상속 사슬(가까운 쪽부터)"))
for cls in classes:
    chain = " <- ".join(c.__name__ for c in cls.__mro__ if c is not object)
    print("%-20s %-18s %s" % (cls.__name__, issubclass(cls, Exception), chain))
```

```text
===== python3 - <e25_hierarchy.py =====
이름                   Exception 인가     상속 사슬(가까운 쪽부터)
BaseException        False              BaseException
Exception            True               Exception <- BaseException
SystemExit           False              SystemExit <- BaseException
KeyboardInterrupt    False              KeyboardInterrupt <- BaseException
GeneratorExit        False              GeneratorExit <- BaseException
BaseExceptionGroup   False              BaseExceptionGroup <- BaseException
ExceptionGroup       True               ExceptionGroup <- BaseExceptionGroup <- Exception <- BaseException
ValueError           True               ValueError <- Exception <- BaseException
KeyError             True               KeyError <- LookupError <- Exception <- BaseException
ZeroDivisionError    True               ZeroDivisionError <- ArithmeticError <- Exception <- BaseException
StopIteration        True               StopIteration <- Exception <- BaseException
(exit 0)
```

- **`SystemExit`·`KeyboardInterrupt`·`GeneratorExit` 이 `Exception` 이 아니다**(`False`).
  **끝내려는 뜻**을 담은 신호라서, 「오류를 다 잡는」 코드에 **안 걸리게** 갈라 놓은 것이다.
- ★ `ExceptionGroup` 의 사슬이 길다 — `BaseExceptionGroup` 을 **거쳐** `Exception` 에 닿는다([27번](../27-exception-groups-and-except-star/2-summary.md)).
- `StopIteration` 은 `Exception` 이다 — **정상 신호인데 예외 계층에 산다**([16번](../16-iterator-protocol/2-summary.md)).

실제로 던져 보면 이렇다.

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

- ①은 잡혔다. ②는 **`except Exception` 을 그냥 지나쳤고**, ③은 **안 찍혔다.**
- ★ **트레이스백이 없다.** `SystemExit` 은 조용히 인터프리터를 끝낸다 —
  **출력이 없다는 것 자체가 출력**이고, 그 증거가 **종료 코드 3**이다.

**비용** — `except Exception` 은 **좁은 그물**이다. 그게 장점이다.

### 7. ★ 빈 `except:` 는 그 셋까지 잡는다

**언제 쓰나** — 남의 코드에서 `except:` 를 봤을 때. 그리고 「왜 `Ctrl+C` 가 안 먹지」를 물을 때.

레퍼런스가 이름을 붙여 둔다 — **bare except**. `except BaseException:` 과 같은 뜻이다.

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

- ★ **빈 `except:` 가 `SystemExit` 을 잡았다.** 프로그램이 안 끝났다.
- `except Exception` 쪽은 못 잡아 그대로 나갔고, ③이 **안 찍혔다.** 종료 코드는 여전히 **3**이다.
- ★ 「그럼 빈 `except:` 는 절대 쓰면 안 되나」 — **다시 던질 거면 괜찮다.**
  `except: ... raise` 는 잡아서 기록하고 놓아 주는 것이라 흐름을 안 바꾼다. **삼키는 것이 문제**다.

**비용** — `Ctrl+C` 가 안 먹고, `sys.exit()` 가 안 먹는다. **끌 수 없는 프로그램**이 된다.

### 8. ★★ 연쇄 — `__context__` 는 자동, `__cause__` 는 손으로

**언제 쓰나** — 트레이스백 두 덩어리를 볼 때마다. **두 문구가 다르다는 것**이 이 절의 전부다.

`except` 안에서 새 예외를 던지면 파이썬이 **원래 예외를 자동으로 붙인다.** 문구는 이렇다.

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

**`During handling of the above exception, another exception occurred:`**
— 「저걸 처리하다가 이게 났다」. 인과를 **주장하지 않는다.**

같은 코드에 `from e` 만 붙이면 문구가 **바뀐다.**

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

**`The above exception was the direct cause of the following exception:`**
— 「저것이 이것의 **직접 원인**이다」. 이건 **내가 손으로 한 주장**이다.

`from None` 을 주면 **앞 덩어리가 통째로 사라진다.**

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

세 경우의 속성을 한 자리에서 찍었다.

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

★★ **표로 굳히면 이렇다** — 이 표가 이 절의 인출 목표다.

| 쓴 것 | `__cause__` | `__context__` | `__suppress_context__` | 트레이스백 문구 |
|---|---|---|---|---|
| `except` 안에서 그냥 `raise` | `None` | 원래 예외 | `False` | `During handling of the above exception, another exception occurred:` |
| `raise ... from e` | **원래 예외** | 원래 예외 | `True` | `The above exception was the direct cause of the following exception:` |
| `raise ... from None` | `None` | **원래 예외(남아 있다)** | `True` | **앞 덩어리가 안 찍힌다** |

- ★ **`from None` 이 `__context__` 를 지우는 것이 아니다.** 값은 그대로 있고
  **`__suppress_context__` 가 `True` 로 바뀌어 출력에서만 감춘다** — 디버거로는 여전히 보인다.
- ★ **`__cause__` 가 있으면 `__context__` 도 같이 채워진다.** 둘은 배타가 아니다.

```text
   raise B from A                    except A: raise B

   B.__cause__   = A   <- 내가 적었다    B.__cause__   = None
   B.__context__ = A   <- 자동            B.__context__ = A   <- 자동
   B.__suppress_context__ = True          ... = False

   출력: "the direct cause of"            출력: "During handling of"
```

**비용** — `from e` 는 **문서화 비용이 0인 주장**이다. 인과가 확실할 때만 쓴다.
확실하지 않으면 **그냥 `raise` 해도 원인은 붙는다.**

### 9. `finally` 안에서 새 예외가 나면 — 원래 것이 `__context__` 가 된다

**언제 쓰나** — 정리 코드(`close()`·롤백)가 터질 수 있을 때.

```python
# e25_finally_raises.py
def both():
    try:
        raise ValueError("try 가 던진 것")
    finally:
        raise KeyError("finally 가 던진 것")


both()
```

```text
===== python3 - <e25_finally_raises.py =====
Traceback (most recent call last):
  File "<stdin>", line 3, in both
ValueError: try 가 던진 것

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "<stdin>", line 8, in <module>
  File "<stdin>", line 5, in both
KeyError: 'finally 가 던진 것'
(exit 1)
```

- **밖으로 나온 것은 `finally` 쪽 `KeyError`** 다. 원래의 `ValueError` 는 **첫 덩어리로 남는다.**
- 문구는 **`During handling of ...`** — `from` 을 안 썼으니 자동 연쇄다.
- ★ **원래 예외가 사라지지는 않는다.** 동작 4(`return`)와 **결정적으로 다르다** —
  `finally` 에서 **예외로 나가면 원인이 남고**, **`return` 으로 나가면 지워진다.**

**비용** — 정리 코드의 실패가 **진짜 원인을 두 번째 줄로 밀어낸다.** 첫 덩어리를 읽는 습관이 필요하다.

### 10. ★ `except` 순서를 뒤집으면 — **경고가 없다**

**언제 쓰나** — `except` 를 여럿 쓸 때. 「순서가 중요한가」를 물을 때.

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

- ★★ **경고를 전부 에러로 올려 두고 돌렸는데도 통과했다.** 파이썬은 **도달 불가능한 `except` 절을 알려 주지 않는다.**
- 상위(`Exception`)를 먼저 두면 **아래 갈래는 영영 안 돈다.** 문법 오류도 아니고 경고도 아니다.
- 규칙은 하나다 — **좁은 것부터, 넓은 것은 마지막에.**

★ **자바와 다른 자리다.** 자바 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **25번**이 다루는
검사 예외 체계에서는 **도달 불가능한 `catch` 가 컴파일 에러**다.
파이썬은 검사 예외가 없고, 이 순서 문제도 **컴파일러가 안 본다.**

**비용** — 조용하다. **읽는 사람만이 잡을 수 있다.**

### 11. `as e` 로 받은 이름은 `except` 절을 나가면 **지워진다**

**언제 쓰나** — 예외 객체를 절 밖에서 쓰려 할 때.

레퍼런스가 그 이유까지 적는다.

> When an exception has been assigned using `as target`, it is cleared at the end of the `except` clause. …
> This is because with the traceback attached to them, they form a reference cycle with the stack frame,
> keeping all locals in that frame alive until the next garbage collection occurs.

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

- **`except` 를 나오면 `locals()` 에 `e` 가 없다**(`False`).
- 그 이름을 다시 읽으면 **`UnboundLocalError`** 가 난다 — 그리고 그것은 **`NameError` 의 하위**다
  ([21번](../21-scope-legb-global-nonlocal/2-summary.md)의 그 규칙 그대로다).
- 쓰려면 **다른 이름으로 빼 둔다**(`saved = e`).

**비용** — 이름 하나 더 쓴다. 대신 **프레임이 오래 살아 있는 것**을 막는다.

### 12. ★ [16번](../16-iterator-protocol/2-summary.md)과 잇는 자리 — 샌 `StopIteration` 은 `RuntimeError` 가 된다

**언제 쓰나** — 제너레이터 안에서 `next()` 를 맨손으로 쓸 때.

```python
# e25_pep479.py
import sys


def take_two(it):
    yield next(it)
    yield next(it)


print(list(take_two(iter([1, 2]))), file=sys.stderr)
print(list(take_two(iter([1]))), file=sys.stderr)
```

```text
===== python3 - <e25_pep479.py =====
[1, 2]
Traceback (most recent call last):
  File "<stdin>", line 6, in take_two
StopIteration

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "<stdin>", line 10, in <module>
RuntimeError: generator raised StopIteration
(exit 1)
```

- 연쇄 문구가 **`The above exception was the direct cause of`** 다 —
  파이썬이 **`from` 을 쓴 것과 같은 연결**을 스스로 만들었다는 뜻이다(동작 8의 표 둘째 줄).
- **3.6 이전에는 이것이 예외가 아니었다.** `list(...)` 가 조용히 `[1]` 을 돌려줬다.
  PEP 479 가 그 **무음 실패를 시끄러운 실패로 바꾼 것**이다.
- ★ **정본은 [16번](../16-iterator-protocol/2-summary.md)이다.** 여기서는 **연쇄 문구를 읽는 연습**으로만 쓴다.

**비용** — 없다. **옛 동작이 더 비쌌다.**

## 문법 — 형태와 규칙

**형태 — 네 절과 `raise` 세 꼴**

```python
# e25_forms.py
# ① 네 절 전부 — 순서가 문법으로 고정돼 있다
def all_four(x):
    try:
        y = 10 / x          # 예외가 날 수 있는 일
    except ValueError as e:
        print(e)            # 좁은 것부터
    except (KeyError, IndexError):
        print("묶어서")      # 튜플로 묶어 한 갈래에 여럿
    except Exception:
        print("넓은 것은 마지막")
    else:
        print("예외가 없었을 때만", y)
    finally:
        print("언제나")


# ② raise 세 꼴
def three_raises(mode, e=None):
    if mode == "새로":
        raise ValueError("메시지")
    if mode == "그대로":
        raise                              # except 안에서 "그대로 다시" 던진다
    if mode == "원인":
        raise RuntimeError("바깥") from e  # from None 이면 감춘다


# ③ except 절은 하나도 없어도 된다 — try/finally
def only_finally(fp):
    try:
        fp.read()
    finally:
        fp.close()
```

규칙 열.

1. **절의 순서는 `try` → `except`* → `else` → `finally`** 로 고정이다. `else` 는 **`except` 가 하나 이상 있어야** 쓸 수 있다.
2. **`except` 는 위에서부터 처음 맞는 것 하나만** 돈다. **좁은 것부터** 쓴다 — 어겨도 **경고가 없다.**
3. **`except` 에 쓰는 것은 `BaseException` 의 하위 클래스**여야 한다. 튜플로 여럿을 묶을 수 있다.
4. **`else` 는 예외가 없었을 때만** 돈다. 그 안에서 난 예외는 **위 `except` 가 안 잡는다.**
5. **`finally` 는 언제나 돈다** — 정상·예외·`return`·`break`·`continue` 전부.
6. ★ **`finally` 안의 `return`·`break`·`continue` 는 저장된 예외를 버린다.** `continue` 는 **3.8+**.
7. **`as e` 의 `e` 는 절이 끝나면 지워진다.** 밖에서 쓰려면 다른 이름으로 옮긴다.
8. **`except` 안의 맨 `raise` 는 「그대로 다시」** 던진다 — 트레이스백이 안 끊긴다.
9. **`raise B from A` 는 `__cause__` 를, 자동 연쇄는 `__context__` 를** 채운다. `from None` 은 **출력만** 감춘다.
10. **빈 `except:` 는 `except BaseException:`** 이다 — `SystemExit`·`KeyboardInterrupt` 까지 잡는다.

**금지 사례 — 문법은 맞는데 조용히 어긋나는 것들**

```python
# e25_pitfalls.py
# ① finally 에서 나간다 — 예외가 사라진다
def swallowed():
    try:
        raise ValueError("위험한 일")
    finally:
        return "완료"          # ★ 예외가 났어도 "완료" 가 돌아간다


# ② 넓은 것을 먼저 쓴다 — 아래 갈래가 영영 안 돈다 (경고 없음)
def unreachable(x):
    try:
        return 10 / x
    except Exception:
        return "넓은 것"
    except ZeroDivisionError:  # 도달 불가. 파이썬은 아무 말도 안 한다
        return "안 돈다"


# ③ 잡고 삼킨다 — 가장 오래 안 걸리는 버그
def silent(x):
    try:
        return 10 / x
    except Exception:
        pass                    # 무슨 일이 났는지 아무도 모른다


# ④ try 몸통이 넓다 — 엉뚱한 자리의 같은 예외를 잡는다
CODES = {"A": "승인"}


def too_wide(d):
    try:
        raw = d["code"]
        return CODES[raw]       # 이쪽 KeyError 까지 잡힌다
    except KeyError:
        return "code 키가 없다"  # 거짓 보고


# ⑤ 빈 except 로 삼킨다 — Ctrl+C 가 안 먹는다
def uninterruptible(일):
    while True:
        try:
            일()
        except:
            continue
```

## 어디서 틀리나

### (1) ★★ `finally` 에 `return` 을 쓴다

**예외가 사라진다.** 로그도 트레이스백도 없다. 동작 3의 바이트코드가 이유를 말한다 —
**예외 경로의 `finally` 사본 뒤에 있는 `RERAISE` 까지 못 가기 때문**이다.
`break`·`continue` 도 같다.

### (2) ★ 「`except Exception` 이 전부 잡는다」로 안다

★ **`SystemExit`·`KeyboardInterrupt`·`GeneratorExit` 은 못 잡는다.**
전부 잡으려면 `except BaseException` 이고, **그건 대개 쓰면 안 되는 것**이다.

### (3) 빈 `except:` 로 삼킨다

**`Ctrl+C` 가 안 먹는 프로그램**이 된다. 잡아서 **다시 던지는** 것은 괜찮다(`except: ... raise`).

### (4) ★ `except` 순서를 넓은 것부터 쓴다

**경고가 없다.** 아래 갈래가 도달 불가능해도 파이썬은 아무 말도 안 한다.
자바 갈래([`java/syntax/README.md`](../../../java/syntax/README.md))의 **25번**과 **여기가 갈린다.**

### (5) ★ `try` 몸통을 넓게 쓴다

**엉뚱한 자리의 같은 예외를 잡아 거짓 보고**를 한다. `else` 로 몸통을 좁힌다(동작 2).

### (6) `else` 를 「아니면」으로 읽는다

★ 「**끝까지 갔으면**」이다. [18번](../18-loop-control-and-else/2-summary.md)의 `for ... else` 와 **같은 개념**이고,
탈출의 종류만 `break` 에서 예외로 바뀐 것이다.

### (7) 두 연쇄 문구를 같은 것으로 안다

★ **`During handling of ...` 는 자동**(`__context__`), **`The above ... direct cause ...` 는 내가 적은 것**(`__cause__`)이다.
뒤엣것은 **주장**이다.

### (8) `from None` 이 원인을 지운다고 안다

★ **`__context__` 는 그대로 남아 있다.** `__suppress_context__` 가 **출력만** 막는다.

### (9) `as e` 를 절 밖에서 쓴다

**`UnboundLocalError`** 가 난다. 절이 끝나면 **이름이 지워진다** — 참조 순환을 끊으려는 설계다.

### (10) 예외를 흐름 제어로 남용한다

**성능이 상황에 달린다** — 성공률이 높으면 싸고 낮으면 비싸다.
숫자는 [26번](../26-eafp-vs-lbyl/2-summary.md)이 `timeit` 으로 잰다. **여기서 성능을 주장하지 않는다.**

### (11) 정리 코드를 `finally` 없이 쓴다

`try` 몸통 다음 줄에 적으면 **예외가 나가는 길에는 안 돈다**(동작 1의 ⑤).
객체로 굳힌 형태가 [28번](../28-context-managers-and-with/2-summary.md)의 `with` 다.

### (12) `dis` 결과를 언어 사실로 적는다

★ **「`finally` 가 네 벌 복제된다」는 CPython 3.12.3 의 구현**이다.
언어가 보장하는 것은 「**언제나 돈다**」까지다.

## 구현 세부사항 대 언어 보장

세 층으로 가른다. ★ **이 주제는 「언어 보장」이 두껍다** — 네 절의 순서도, `finally` 의 `return` 이 예외를 버리는 것도,
`as` 이름이 지워지는 것도 **레퍼런스에 그대로 적혀 있다.**\
구현 쪽에 남는 것은 **바이트코드의 모양**과 **예외 문구**다.

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **언어 보장** | 레퍼런스·PEP 가 정한 것 | 공식 문서 문장을 열어서 인용 |
| **CPython 구현** | 이 구현이 그렇게 하는 것 | `dis` 덤프 · 예외 메시지 문구 |
| **이 판(3.12.3)의 관찰** | 이 판에서 그랬을 뿐 | 명령 이름·오프셋 · `ExceptionTable` 모양 |

### 언어 보장

| 사실 | 근거 |
|---|---|
| 절의 순서는 `try` → `except`* → `else` → `finally`, `else` 는 `except` 가 있어야 쓴다 | 8.4 The `try` statement |
| **`except` 는 처음 맞는 하나만** 돈다 | 8.4 |
| **`else` 는 예외가 없었고 `return`·`continue`·`break` 도 없었을 때만** 돈다 | 8.4 |
| **`finally` 는 나가는 모든 길에서** 돈다 | 8.4 |
| ★ **`finally` 의 `return`·`break`·`continue` 는 저장된 예외를 버린다** | 8.4 — *"the saved exception is discarded"* |
| **`as` 로 받은 이름은 절 끝에서 지워진다** (참조 순환 때문) | 8.4.1 |
| `raise B from A` 가 **`__cause__`** 를, 자동 연쇄가 **`__context__`** 를 채운다 | 7.8 · PEP 3134 |
| `from None` 은 **`__suppress_context__`** 를 켠다 | 7.8 |
| **빈 `except:` = `except BaseException:`** | 8.4 |
| `SystemExit`·`KeyboardInterrupt`·`GeneratorExit` 이 **`Exception` 의 하위가 아니다** | Built-in Exceptions 계층도 |
| 제너레이터 밖으로 샌 `StopIteration` 이 **`RuntimeError`** 가 된다(3.7+) | PEP 479 |

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| `finally` 몸통이 **경로마다 복제**된다(이 예에서 네 벌) | `dis` — `STORE_FAST done` 이 `[28, 48, 80, 92]` |
| 예외 경로의 사본 뒤에 **`RERAISE`** 가 붙는다 | `dis` |
| `try` 몸통의 조각이 **`ExceptionTable`** 로 예외 경로에 이어진다 | `dis` |
| 예외 메시지 문구 — `cannot access local variable 'e' where it is not associated with a value` 등 | 실행 |
| `SystemExit` 이 **트레이스백 없이** 종료 코드만 남긴다 | 실행 — `(exit 3)` |

### 이 판(3.12.3)의 관찰

| 관찰 | 어디가 흔들리나 |
|---|---|
| 명령 이름(`RETURN_CONST`·`POP_JUMP_IF_FALSE`)과 오프셋 | **판마다 바뀐다.** 3.11 은 `RETURN_CONST` 가 없다 — **안 돌려 봤다** |
| `ExceptionTable` 의 표기(`lasti` 등) | 위와 같다 |
| 예외 **문구** 전부 | 종류는 명세, 문구는 아니다 |
| `__suppress_context__` 가 `from e` 에서도 `True` 인 것 | 레퍼런스가 `from` 전반에 대해 적는다 — **문구는 확인했고 다른 판은 안 돌려 봤다** |

### 그래서 이렇게 적으면 틀린다

- ✗ 「`except Exception` 이 모든 예외를 잡는다」\
  ○ **`BaseException` 의 세 형제는 못 잡는다.**
- ✗ 「`finally` 는 언제나 도니까 안전하다」\
  ○ **`finally` 안에서 나가면 예외가 버려진다.** 도는 것과 안전한 것은 다르다.
- ✗ 「`finally` 는 한 번 적었으니 한 벌이다」\
  ○ **CPython 은 경로마다 복제한다**(이 예에서 네 벌). 단 그것은 **구현**이다.
- ✗ 「`else` 는 `except` 의 반대다」\
  ○ 「**몸통이 끝까지 갔으면**」이다. `for` 의 `else` 와 같은 개념이다.
- ✗ 「`from None` 이 원인을 지운다」\
  ○ **`__context__` 는 남아 있다.** 출력만 감춘다.
- ✗ 「두 연쇄 문구는 표현만 다르다」\
  ○ 하나는 **자동**이고 하나는 **내가 한 주장**이다.
- ✗ 「`except` 순서를 틀리면 에러가 난다」\
  ○ **경고조차 없다.** 아래 갈래가 조용히 죽는다.
- ✗ 「`except ... as e` 의 `e` 는 함수 끝까지 산다」\
  ○ **절이 끝나면 지워진다.**
- ✗ 「예외는 느리니까 쓰면 안 된다」\
  ○ **상황에 달린다.** 숫자는 [26번](../26-eafp-vs-lbyl/2-summary.md)에 있다.

**판정 기준 한 줄**: **「이 길로 나가도 `finally` 가 도나」를 물으면 절의 계약이 갈리고,
「이 예외가 `Exception` 인가」를 물으면 그물의 크기가 갈린다.**

## 언제 쓰고 언제 안 쓰나

| 상황 | 판정 |
|---|---|
| 자원을 반드시 닫아야 한다 | ★ **`with` 를 먼저 본다**([28번](../28-context-managers-and-with/2-summary.md)) — `try/finally` 를 객체로 굳힌 것이다 |
| 예외가 날 자리와 뒷일이 섞여 있다 | ★ **`else` 로 뒷일을 옮긴다** — `try` 몸통을 한 줄로 좁힌다 |
| 무슨 예외가 날지 모르겠다 | **`except Exception`** 까지만. 빈 `except:` 는 **다시 던질 때만** |
| 잡아서 다른 예외로 바꿔 던진다 | `raise 새것 from e` — **원인이 확실할 때**. 아니면 그냥 `raise 새것` |
| 저수준 원인을 감추고 싶다(라이브러리 경계) | `from None` — **감추는 것이지 지우는 것이 아니다** |
| `finally` 에서 값을 바꾸고 싶다 | ★ **하지 마라.** 예외가 사라진다 |
| 정리 코드가 실패할 수 있다 | `finally` 안을 또 `try` 로 감싸거나, **원래 예외를 잃을 각오**를 한다(동작 9) |
| 검사와 실행 중 무엇을 고르나 | [26번](../26-eafp-vs-lbyl/2-summary.md) — **이 주제 밖이다** |
| 여러 실패를 **함께** 날라야 한다 | [27번](../27-exception-groups-and-except-star/2-summary.md) — `ExceptionGroup`(3.11+) |
| 예외 계층을 직접 만든다 | `목록의 **29번 주제**`(클래스) 를 먼저. `Exception` 을 상속하고 **`BaseException` 은 상속하지 않는다** |

## 핵심 문장

- ★★ **`finally` 는 「다음 줄」이 아니라 「나가는 길목」이다.** 정상·예외·`return`·`break`·`continue` 어느 길로 나가도 돈다 —
  **CPython 은 그 길마다 사본을 하나씩 깔아** 그 약속을 지킨다(이 예에서 **네 벌**, `[28, 48, 80, 92]`).
- ★★ **그래서 `finally` 안에서 `return` 하면 예외가 사라진다.** 예외 경로의 사본 뒤에 있는 **`RERAISE` 까지 못 가기 때문**이고,
  레퍼런스도 「**버려진다**」고 적는다. `break`·`continue` 도 같다.
- ★★ **`except Exception` 은 전부를 잡지 않는다** — `SystemExit`·`KeyboardInterrupt`·`GeneratorExit` 은
  **`BaseException` 의 직속 자식**이라 안 걸린다. 빈 `except:` 는 그것까지 잡아 **끌 수 없는 프로그램**을 만든다.
- ★★ **연쇄 문구 둘을 구분하라.** `During handling of the above exception, another exception occurred:` 는 **자동**(`__context__`)이고,
  `The above exception was the direct cause of the following exception:` 는 **`from e` 로 내가 한 주장**(`__cause__`)이다.
- ★ **`from None` 은 지우는 것이 아니라 감추는 것**이다 — `__context__` 는 남고 `__suppress_context__` 만 `True` 가 된다.
- ★ `else` 는 「**끝까지 갔으면**」이다. [18번](../18-loop-control-and-else/2-summary.md)의 `for ... else` 와 같은 개념이고,
  쓰는 이유는 **`try` 몸통을 한 줄로 좁혀 거짓 보고를 막는 것**이다.
- ★ **`except` 순서를 틀려도 아무 말이 없다.** 경고를 에러로 올려 두고 돌려도 통과했다 — **좁은 것부터**가 유일한 방어다.
- ★ **`as e` 의 `e` 는 절이 끝나면 지워진다**(참조 순환 때문). 다시 읽으면 `UnboundLocalError` 다.
- ★ **`try` 의 `return` 값은 먼저 계산되고 `finally` 가 그 뒤에 돈다** — `finally` 가 값을 덮어쓰지는 않는다.

## 관련 자료

- 목록: [python/syntax 주제 목록](../README.md) — 이 주제는 **25번**
- 선행: [16-iterator-protocol](../16-iterator-protocol/2-summary.md) — **PEP 479 의 정본.**\
  **경계**: 「`StopIteration` 이 무엇인가」와 소진 판정은 전부 그쪽. 여기는 **연쇄 문구를 읽는 예제**로만 쓴다.
- 선행: [18-loop-control-and-else](../18-loop-control-and-else/2-summary.md) — **`else` 의 짝.**\
  **경계**: `break`/`continue` 와 루프의 `else` 는 그쪽, **예외로 탈출하는 `else`** 는 여기다.
- 선행: [05-truthiness-and-short-circuit](../05-truthiness-and-short-circuit/2-summary.md) — 진릿값.\
  **경계**: [28번](../28-context-managers-and-with/2-summary.md)의 `__exit__` 반환값이 **`True` 가 아니라 참**이면 삼키는 이유가 거기 있다.
- 이어지는 곳: [26-eafp-vs-lbyl](../26-eafp-vs-lbyl/2-summary.md) — **고르는 법과 비용.**\
  **경계**: 「예외가 싼가 비싼가」의 **측정은 전부 그쪽**이다. 여기서는 성능을 주장하지 않는다.
- 이어지는 곳: [27-exception-groups-and-except-star](../27-exception-groups-and-except-star/2-summary.md) — **여러 예외를 함께 나르는 법**(3.11+).
- 이어지는 곳: [28-context-managers-and-with](../28-context-managers-and-with/2-summary.md) — **`try/finally` 를 객체로 굳힌 것.**
- 다른 갈래: 자바 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **25번**·**26번** — **검사 예외**와 try-with-resources.
  파이썬에는 검사 예외가 없고 `throws` 선언도 없다 — **잡지 않아도 컴파일이 통과한다.**
- 다른 갈래: Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **23번** — `panic!` 대 `Result`.
  Rust 는 **실패를 값으로** 돌려주는 길이 기본이라 이 주제의 절 구조가 아예 없다.
- 다른 갈래: Go 갈래 목록([`go/syntax/README.md`](../../../go/syntax/README.md))의 **23번**·**26번**·**27번** —
  `(T, error)` 관례 · `defer` · `panic`/`recover`. `defer` 가 여기의 `finally` 자리다.
- 공식 문서: [The `try` statement](https://docs.python.org/3.12/reference/compound_stmts.html#the-try-statement) ·
  [The `raise` statement](https://docs.python.org/3.12/reference/simple_stmts.html#the-raise-statement) ·
  [Built-in Exceptions](https://docs.python.org/3.12/library/exceptions.html) ·
  [PEP 3134](https://peps.python.org/pep-3134/)

## 용어 풀이

- **예외(exception)**: 「여기서는 더 못 간다」를 객체로 만들어 부른 쪽으로 되던지는 것.\
  예: `1 / 0` 이 `ZeroDivisionError` 객체를 만든다.
- **전파(propagate)**: 안 잡힌 예외가 부른 쪽으로 한 칸씩 올라가는 것.\
  예: 트레이스백의 줄 수가 올라온 칸 수다.
- **트레이스백(traceback)**: 예외가 지나온 프레임의 목록. **아래쪽이 터진 자리**다.\
  예: `File "<stdin>", line 2, in inner` 가 가장 아래.
- **`try` 몸통(try suite)**: `try:` 아래의 블록. **좁을수록 좋다.**\
  예: 한 줄로 좁히는 도구가 `else` 다.
- **`else` 절**: 예외가 **안 났을 때만** 도는 절. `for` 의 `else` 와 같은 개념.\
  예: 「끝까지 갔으면」이라고 읽는다.
- **`finally` 절**: 나가는 **모든 길**에서 도는 절.\
  예: 정상·예외·`return`·`break`·`continue` 전부.
- **bare except(빈 `except:`)**: 타입을 안 적은 `except`. **`except BaseException:`** 과 같다.\
  예: `Ctrl+C` 까지 잡아 버린다.
- **`BaseException`**: 예외 계층의 뿌리. `Exception` 은 그 **자식 중 하나**다.\
  예: `SystemExit` 은 `Exception` 이 아니다.
- **`__context__`**: `except` 안에서 새 예외를 던지면 **자동으로** 붙는 원래 예외.\
  예: 트레이스백이 `During handling of ...` 로 잇는다.
- **`__cause__`**: `raise ... from e` 로 **손으로 적은** 원인.\
  예: 트레이스백이 `... the direct cause of ...` 로 잇는다.
- **`__suppress_context__`**: 출력에서 앞 덩어리를 **감출지**의 플래그. `from` 을 쓰면 `True`.\
  예: `from None` 은 값을 남긴 채 감추기만 한다.
- **맨 `raise`(re-raise)**: `except` 안에서 인자 없이 쓰는 `raise`. **지금 처리 중인 예외를 그대로** 다시 던진다.\
  예: 기록만 하고 놓아 줄 때 쓴다.
- **예외 계층(exception hierarchy)**: 예외 클래스들의 상속 관계. **`except` 의 그물 크기가 여기서 정해진다.**\
  예: `KeyError` 는 `LookupError` 를 거쳐 `Exception` 에 닿는다.
- **`ExceptionTable`**: CPython 3.11+ 의 바이트코드 부록. **어느 구간의 예외가 어디로 가는지**를 적는다.\
  예: `14 to 22 -> 88` 은 「14\~22 번에서 터지면 88 번으로」라는 뜻이다.

## 더 들어가면

- **`sys.exc_info()` 와 `traceback` 모듈** — 잡은 예외를 **문자열로 찍는** 도구들. 이 주제에서는 안 돌려 봤다.
- **`contextlib.suppress`** — `try/except/pass` 를 한 줄로 만든 것. 정본은 [28번](../28-context-managers-and-with/2-summary.md)이다.
- ★ **`BaseExceptionGroup` 은 `except` 로도 잡힌다** — 별을 안 붙여도 **묶음 통째로** 하나 잡는다.
  그 차이는 [27번](../27-exception-groups-and-except-star/2-summary.md)이 다룬다.
- ★ **예외를 직접 만들 때** `Exception` 을 상속하고 **`BaseException` 은 상속하지 않는다.**
  상속하면 남의 `except Exception` 에 안 걸려 **조용히 프로그램을 끝낸다.** 여기서는 안 돌려 봤다.
- ★ **`try` 문이 도는 것 자체의 비용은 거의 0 이고, 비싼 것은 예외가 실제로 날 때**다.
  그 수치는 [26번](../26-eafp-vs-lbyl/2-summary.md)이 잰다 — **여기서 수치를 적지 않는다.**
