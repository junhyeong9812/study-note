# python/syntax/26-eafp-vs-lbyl — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만.
> - [glossary — EAFP](https://docs.python.org/3.12/glossary.html#term-EAFP) · [glossary — LBYL](https://docs.python.org/3.12/glossary.html#term-LBYL) — **두 낱말의 정의와 경쟁 조건 경고가 거기 있다**
> - [`dict.get`](https://docs.python.org/3.12/library/stdtypes.html#dict.get) · [`dict.setdefault`](https://docs.python.org/3.12/library/stdtypes.html#dict.setdefault) · [`collections.defaultdict`](https://docs.python.org/3.12/library/collections.html#collections.defaultdict)
> - [`hasattr`](https://docs.python.org/3.12/library/functions.html#hasattr) · [`getattr`](https://docs.python.org/3.12/library/functions.html#getattr) — `hasattr` 가 **`AttributeError` 만** 삼킨다는 문장
> - [`str.isdigit`](https://docs.python.org/3.12/library/stdtypes.html#str.isdigit) · [`int`](https://docs.python.org/3.12/library/functions.html#int) — **두 판정 기준이 다르다**
> - [`timeit`](https://docs.python.org/3.12/library/timeit.html) — 측정 도구
>
> **실행 검증** — 이 문서에 실린 출력은 전부 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.\
> ★ **던지는 형태를 하나로 고정했다** — `python3 - <파일` 로 던져 트레이스백이 `File "<stdin>", line N` 이 된다.
> 이 주제의 예외는 전부 **실행 중 예외**라 소스 줄도 캐럿도 안 나온다.\
> **수치** — `timeit` 으로 쟀다. **한 판 = `repeat` 11 회의 중앙값**이고 **판을 셋** 낸다.
> 판마다 **버리는 예열 판**을 한 번 먼저 돌렸다. 머신은 Linux x86_64, 부하는 안 통제했다.\
> ★★ **신호 대 잡음** — 「성공률 0%」 쪽은 신호가 **5배 이상**이라 판 사이 흔들림(±5%)보다 훨씬 크다.
> 「성공률 100%」 쪽은 **0.75\~0.88배**라 신호가 작지만 **세 판 모두 1 미만**이었다.
> **손익분기 스캔의 5% 칸은 세 판이 `0.88 / 1.05 / 0.98` 로 1 을 넘나든다** — 그 칸 위에 결론을 세우지 않는다.
> ★★ **제출 직전 재측정에서는 맞붙는 칸이 10% 로 옮겨 갔다**(동작 5에 두 측정을 나란히 남겼다).\
> **버전** — EAFP·LBYL 은 관용구라 버전이 없다. 갈리는 것 하나 — **`hasattr` 가 `AttributeError` 만 삼키는 것이 3.2 부터**다
> (2.x 에서는 모든 예외를 삼켰다). 2.x 는 이 머신에 없어 **옛 동작은 안 돌려 봤다** — 문서 근거다.\
> **구현 대 언어 보장 한 줄** — **「어느 쪽이 맞나」는 언어가 정해 주지 않는다.** 이 문서의 판정은 전부
> **측정과 경쟁 조건 재현**에서 나온 것이고, **수치는 이 머신의 관찰**이다.\
> **★ 흔들리는 칸 / 안 흔들리는 칸** — 재대조에서 「고칠 것」과 「설계상 안 맞는 것」을 기계적으로 가르려고 미리 선언한다.
>
> | 흔들린다 | 안 흔들린다(근거로 써도 되는 칸) |
> |---|---|
> | `timeit` 의 **나노초·마이크로초 값** 전부 | **EAFP/LBYL 비의 부호**(성공률 100% 는 1 미만, 0% 는 4배 이상) |
> | 손익분기 표의 **5% 칸과 10% 칸의 비** — ★ **둘 다 1 을 넘나들고, 맞붙는 칸이 실행마다 옮겨 간다** | **0%·20%·50%·100% 칸의 대소** · 손익분기가 **5\~10% 사이**라는 것 |
> | (판이 오르면) 예외 **문구** | 예외 **종류** · `File "<stdin>", line N` · **종료 코드** |
> | — | 경쟁 조건 블록의 **①②③④ 네 줄 결과** — 순서를 고정해 재현했다 |
>
> ★ **대조할 것은 숫자가 아니라 성질이다** — `timeit` 두 블록은 다시 돌리면 또 달라진다.
> 「**성공률이 높으면 EAFP 가 빠르고 낮으면 몇 배 느리다**」와 「**손익분기가 한 자릿수 %대에 있다**」가 대조 대상이다.\
> **선행** — [25-exceptions-and-finally](../25-exceptions-and-finally/2-summary.md)(**예외 문법의 정본**) ·
> [12-dict-and-key-requirements](../12-dict-and-key-requirements/2-summary.md)(`get`·`setdefault`) ·
> [05-truthiness-and-short-circuit](../05-truthiness-and-short-circuit/2-summary.md)(단축 평가).\
> **이 사슬** — [25](../25-exceptions-and-finally/2-summary.md) → 26 → [27](../27-exception-groups-and-except-star/2-summary.md) → [28](../28-context-managers-and-with/2-summary.md).
> 25 가 **문법**이라면 여기는 **고르는 법**이다. **문법을 한 줄도 다시 설명하지 않는다.**

## 한눈에 — 쉽게 말하면

**LBYL 은 「손잡이를 만져 보고 문을 민다」이고, EAFP 는 「일단 밀고 안 열리면 그때 본다」이다.**

- 문이 **거의 항상 열려 있으면** 만져 보는 쪽이 손해다 — 두 번 일하는 셈이다.
- 문이 **거의 항상 잠겨 있으면** 미는 쪽이 손해다 — 부딪히는 값이 비싸다.
- ★★ **그리고 만져 본 뒤 미는 사이에 누가 문을 잠글 수 있다.** 이건 속도 문제가 아니라 **정확성 문제**다.

```text
   LBYL                            EAFP
   ----                            ----
   if key in d:      <- 검사        try:
       d[key]        <- 실행            d[key]     <- 실행(검사 없음)
   else:                            except KeyError:
       기본값                            기본값

   ★ 검사와 실행 사이에 틈이 있다      ★ 틈이 없다 — 한 번의 연산이다
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 손잡이를 만져 본다 | `in`·`hasattr`·`os.path.exists`·`isdigit` | 검사 한 번 + 실행 한 번 = **조회 두 번** |
| 일단 민다 | `try: ... except ...:` | 성공하면 **한 번**, 실패하면 예외 값 |
| ★ **만져 본 뒤 미는 사이의 틈** | TOCTOU 경쟁 조건 | 그 틈에 파일을 지워 **재현**한다 |
| ★ **손잡이 상태와 문 상태가 다르다** | `isdigit()` 은 참인데 `int()` 가 터진다 | 두 판정 기준이 **다른 집합**이다 |
| 문이 거의 열려 있다 | 성공률이 높다 | EAFP 가 **1 미만 비**로 빠르다 |
| 문이 거의 잠겨 있다 | 성공률이 낮다 | EAFP 가 **4배 이상** 느리다 |
| 미리 접어 둔 손잡이 | `dict.get`·`getattr(o, n, 기본)` | 둘 다 **한 번의 조회**로 접었다 |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.\
「**`os.path.exists` 로 확인하고 열었는데 `FileNotFoundError` 가 났다**」와
「**`isdigit()` 로 걸렀는데 `int()` 가 터졌다**」가 그것이다.\
둘 다 **검사를 통과하고 나서** 터진다 — LBYL 의 고유한 실패 모양이다.

> **EAFP** — *Easier to Ask Forgiveness than Permission*. 일단 하고, 안 되면 예외를 잡는 방식.\
> 예: `try: d[k] except KeyError: ...`

> **LBYL** — *Look Before You Leap*. 하기 전에 조건을 먼저 확인하는 방식.\
> 예: `if k in d: d[k]`

> **TOCTOU(time-of-check to time-of-use)** — **확인한 시점**과 **쓰는 시점** 사이에 세상이 바뀌어 생기는 버그.\
> 예: `exists()` 가 참을 답한 뒤 파일이 지워지면, 통과한 검사가 아무 뜻이 없어진다.

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

1. **두 관용구가 정말 같은 답을 내는가** — 아니라면 어디서 갈리나.
2. **예외는 싼가 비싼가** — 「비싸다」가 한 낱말로 답할 수 있는 말인가.
3. **어느 쪽을 고르나** — 고르는 기준이 속도인가 다른 것인가.

★ 둘째 질문이 이 주제의 인출 목표다. **「상황에 달린다」를 말로 하는 것과, 「몇 %에서 뒤집히는지」를 대는 것**이 아는 것과 들은 것의 경계다.

## 동작 방식

> 이 절이 본문이다. 이 주제의 네 번째 창은 **`timeit`** 이다 —
> 「예외가 비싸다」는 말은 **재 보기 전까지 참도 거짓도 아니다.**
> 그리고 이 주제에는 **창이 하나 더 있다** — **경쟁 조건은 시간이 아니라 순서로만 보인다.**

### 1. 같은 문제를 두 관용구로 나란히

**언제 쓰나** — 두 낱말을 처음 볼 때. 둘이 **같은 답을 내는 범위**를 먼저 못 박는다.

```python
# e26_side_by_side.py
CODES = {"A": "승인", "D": "거절"}


def lbyl(d, key):
    if key in d:
        return d[key]
    return "(없음)"


def eafp(d, key):
    try:
        return d[key]
    except KeyError:
        return "(없음)"


for key in ("A", "Z"):
    print("키 %-3r LBYL: %-6s EAFP: %-6s 같은가: %s"
          % (key, lbyl(CODES, key), eafp(CODES, key),
             lbyl(CODES, key) == eafp(CODES, key)))
```

```text
===== python3 - <e26_side_by_side.py =====
키 'A' LBYL: 승인     EAFP: 승인     같은가: True
키 'Z' LBYL: (없음)   EAFP: (없음)   같은가: True
(exit 0)
```

- **키가 있든 없든 두 관용구의 답이 같다**(`True`). 갈리는 것은 **답이 아니다.**
- 갈리는 것은 셋이다 — **경쟁 조건**(동작 2) · **검사의 정확성**(동작 3) · **비용**(동작 4).

**비용** — LBYL 은 **조회가 두 번**이다(`in` 한 번, `[]` 한 번). EAFP 는 성공하면 **한 번**이다.
그 차이가 동작 4의 수치로 나온다.

### 2. ★★ 경쟁 조건 — 시간이 아니라 **순서**로 보인다

**언제 쓰나** — 파일·네트워크·DB 처럼 **나 말고 다른 것이 건드리는 자원**을 다룰 때.

공식 용어집이 LBYL 항목에서 이것을 직접 경고한다.

> In a multi-threaded environment, the LBYL approach can risk introducing a race condition
> between "the looking" and "the leaping". For example, the code, `if key in mapping: return mapping[key]`
> can fail if another thread removes key from mapping after the test, but before the lookup.

★ **이것을 시간으로 보이려 하면 안 된다** — 스레드를 돌려 「가끔 터진다」를 보이는 것은 **재현이 안 된다.**
**검사와 실행 사이에 지우는 순서를 코드로 고정**하면 **매번 같은 출력**이 나온다.

```text
   LBYL                                  EAFP
   ----                                  ----
   exists(path) -> True                  open(path)  -> 열린 파일 객체
        |                                     |
   [ 여기서 다른 프로세스가 지운다 ]        [ 여기서 다른 프로세스가 지운다 ]
        |                                     |
   open(path)   -> FileNotFoundError     fp.read()   -> 내용 (★ 이미 열었다)

   ★ 틈이 검사 "뒤" 에 있으면 검사가 아무 뜻이 없다
```

```python
# e26_race.py
import os
import tempfile

tmp = tempfile.mkdtemp(prefix="e26_")
path = os.path.join(tmp, "data.txt")


def make():
    with open(path, "w", encoding="utf-8") as fp:
        fp.write("내용")


def other_process_deletes():
    os.remove(path)
    print("    [다른 프로세스] 파일을 지웠다")


def lbyl_read(gap):
    if not os.path.exists(path):
        return "(파일 없음)"
    gap()
    with open(path, encoding="utf-8") as fp:
        return fp.read()


def eafp_read(gap):
    try:
        fp = open(path, encoding="utf-8")
    except FileNotFoundError:
        return "(파일 없음)"
    gap()
    with fp:
        return fp.read()


def nothing():
    pass


print("① 틈이 없을 때")
make()
print("    LBYL:", lbyl_read(nothing))
make()
print("    EAFP:", eafp_read(nothing))

print("② exists() 와 open() 사이에 파일이 사라지면 — LBYL")
make()
try:
    print("    LBYL:", lbyl_read(other_process_deletes))
except FileNotFoundError as e:
    print("    LBYL:", type(e).__name__, "— 검사를 통과하고도 터졌다")

print("③ 같은 틈 — EAFP 는 이미 열어 둔 뒤다")
make()
print("    EAFP:", eafp_read(other_process_deletes))

os.rmdir(tmp)
print("④ 뒷정리 — 임시 폴더가 남았나:", os.path.exists(tmp))
```

```text
===== python3 - <e26_race.py =====
① 틈이 없을 때
    LBYL: 내용
    EAFP: 내용
② exists() 와 open() 사이에 파일이 사라지면 — LBYL
    [다른 프로세스] 파일을 지웠다
    LBYL: FileNotFoundError — 검사를 통과하고도 터졌다
③ 같은 틈 — EAFP 는 이미 열어 둔 뒤다
    [다른 프로세스] 파일을 지웠다
    EAFP: 내용
④ 뒷정리 — 임시 폴더가 남았나: False
(exit 0)
```

- ①에서 **틈이 없으면 둘 다 내용을 읽는다.** 대조군이다.
- ★★ ②에서 **LBYL 은 검사를 통과하고도 터진다.** `exists()` 가 참을 답한 그 값이 **이미 낡았다.**
- ★ ③에서 **EAFP 는 같은 틈에서도 내용을 읽는다** — `open()` 이 이미 파일을 잡았기 때문이다.
  유닉스 계열에서 **열린 파일은 이름이 지워져도 살아 있다.**
- ④는 뒷정리 확인이다 — **임시 폴더를 지웠고 남지 않았다**(`False`).

★ **이 블록은 시간이 안 들어가서 결정적이다.** 다시 돌려도 네 줄이 한 글자도 안 변한다.

**비용** — EAFP 가 **항상** 경쟁에 강한 것은 아니다. **자원을 잡는 연산이 원자적일 때만** 그렇다
(`open` 은 그렇다). 잡은 뒤에 또 검사하면 **같은 틈이 다시 생긴다.**

### 3. ★★ LBYL 의 검사가 **틀릴 수 있다** — 두 판정 기준이 다르다

**언제 쓰나** — 「검사 함수」를 고를 때마다. `isdigit`·`isnumeric`·`isascii`·`hasattr` 전부 해당한다.

```python
# e26_isdigit.py
import sys


def lbyl(s):
    if s.isdigit():
        return int(s)
    return "(숫자가 아니다)"


def eafp(s):
    try:
        return int(s)
    except ValueError:
        return "(숫자가 아니다)"


samples = ["12", "-3", " 7 ", "1_0", "\u0661\u0662", "\uff13\uff14", "12.0", "abc", "\u00b2"]
print("%-22s %-9s %-18s %s" % ("입력(ascii)", "isdigit", "LBYL", "EAFP"), file=sys.stderr)
for s in samples:
    print("%-22s %-9s %-18s %s" % (ascii(s), s.isdigit(), lbyl(s), eafp(s)), file=sys.stderr)
```

```text
===== python3 - <e26_isdigit.py =====
입력(ascii)              isdigit   LBYL               EAFP
'12'                   True      12                 12
'-3'                   False     (숫자가 아니다)          -3
' 7 '                  False     (숫자가 아니다)          7
'1_0'                  False     (숫자가 아니다)          10
'\u0661\u0662'         True      12                 12
'\uff13\uff14'         True      34                 34
'12.0'                 False     (숫자가 아니다)          (숫자가 아니다)
'abc'                  False     (숫자가 아니다)          (숫자가 아니다)
Traceback (most recent call last):
  File "<stdin>", line 20, in <module>
  File "<stdin>", line 6, in lbyl
ValueError: invalid literal for int() with base 10: '²'
(exit 1)
```

- ★★ **마지막 줄이 이 절의 전부다.** `'\u00b2'`(위 첨자 2)는 **`isdigit()` 이 참인데 `int()` 가 터진다.**
  LBYL 쪽 함수 안에서 `ValueError` 가 나 **밖으로 새어 나왔다.**
- 그 위 네 줄은 **검사가 지나치게 좁은** 쪽이다 — `'-3'`·`' 7 '`·`'1_0'` 을 `int()` 는 받는데 `isdigit()` 은 거부한다.
- `'\u0661\u0662'`(아라비아 인도 숫자)와 `'\uff13\uff14'`(전각 숫자)는 **둘 다 통과**한다.
- ★ 그래서 **`isdigit()` 이 참인 집합과 `int()` 가 받는 집합은 포함 관계가 아니다.** 서로 엇갈린다.

```text
   isdigit() 가 참인 것만   '\u00b2'
   둘 다 통과하는 것        '12' · '\u0661\u0662' · '\uff13\uff14'
   int() 가 받는 것만       '-3' · ' 7 ' · '1_0'
   둘 다 거부하는 것        '12.0' · 'abc'

   ★ 첫 줄과 셋째 줄이 동시에 있다 —
     어느 쪽도 다른 쪽을 포함하지 않는다. 서로 엇갈린다.
```


★ **「검사를 먼저 한다」의 값은 그 검사가 **실행과 같은 기준**일 때만 생긴다.**
기준이 다르면 LBYL 은 **막아야 할 것을 통과시키고 통과시켜야 할 것을 막는다.**

**비용** — 없다시피 하다. **`int()` 를 `try` 로 감싸면 기준이 하나**가 된다.

### 4. ★★ 비용 — 성공률이 높을 때와 낮을 때를 **둘 다** 잰다

**언제 쓰나** — 「예외는 비싸다」를 들었을 때. 그 말이 **반쪽**인 이유가 여기 있다.

```python
# e26_timeit.py
import statistics
import timeit

SETUP = """
d = {"A": 1}
def lbyl(key):
    if key in d:
        return d[key]
    return None
def eafp(key):
    try:
        return d[key]
    except KeyError:
        return None
lbyl("A"); lbyl("Z"); eafp("A"); eafp("Z")
"""

CASES = [
    ("성공률 100%", "LBYL", 'lbyl("A")'),
    ("성공률 100%", "EAFP", 'eafp("A")'),
    ("성공률 0%", "LBYL", 'lbyl("Z")'),
    ("성공률 0%", "EAFP", 'eafp("Z")'),
]

N = 200_000
print("timeit — 한 판 = repeat 11 회의 중앙값, number=%d." % N)
print("판을 셋 낸다. 판마다 버리는 예열 판을 한 번 먼저 돌린다.")
print()
print("%-14s %-8s %s" % ("상황", "관용구", "1회당 나노초 (판1 / 판2 / 판3)"))
result = {}
for label, kind, stmt in CASES:
    timeit.repeat(stmt, setup=SETUP, repeat=3, number=N)   # 예열 — 버린다
    rounds = []
    for _ in range(3):
        med = statistics.median(timeit.repeat(stmt, setup=SETUP, repeat=11, number=N))
        rounds.append(med / N * 1e9)
    result[(label, kind)] = rounds
    print("%-16s %-10s %6.1f / %6.1f / %6.1f" % (label, kind, *rounds))

print()
print("판마다의 EAFP / LBYL 비 — 1 보다 작으면 EAFP 가 빠르다")
for label in ("성공률 100%", "성공률 0%"):
    ratios = [e / l for e, l in zip(result[(label, "EAFP")], result[(label, "LBYL")])]
    print("%-16s %.2f / %.2f / %.2f" % (label, *ratios))
```

```text
===== python3 - <e26_timeit.py =====
timeit — 한 판 = repeat 11 회의 중앙값, number=200000.
판을 셋 낸다. 판마다 버리는 예열 판을 한 번 먼저 돌린다.

상황             관용구      1회당 나노초 (판1 / 판2 / 판3)
성공률 100%         LBYL         48.2 /   49.5 /   46.6
성공률 100%         EAFP         36.0 /   38.8 /   40.8
성공률 0%           LBYL         36.7 /   41.0 /   41.8
성공률 0%           EAFP        229.5 /  209.1 /  218.4

판마다의 EAFP / LBYL 비 — 1 보다 작으면 EAFP 가 빠르다
성공률 100%         0.75 / 0.78 / 0.88
성공률 0%           6.26 / 5.10 / 5.23
(exit 0)
```

★ **대조할 것은 숫자가 아니라 성질이다** — 다시 돌리면 나노초 값은 또 달라진다.
**대조 대상**은 마지막 두 줄의 비(比)다.

| 상황 | EAFP / LBYL 비 (판 셋) | 읽는 법 |
|---|---|---|
| 성공률 100% | `0.75 / 0.78 / 0.88` | **EAFP 가 빠르다** — 세 판 모두 1 미만. LBYL 은 조회를 두 번 한다 |
| 성공률 0% | `6.26 / 5.10 / 5.23` | **EAFP 가 5배 이상 느리다** — 예외 객체를 만들고 던지고 잡는 값 |

- ★ **LBYL 쪽 두 줄도 다르다** — 성공률 100% 가 0% 보다 느리다.
  **키가 있으면 `in` 다음에 `[]` 를 또 하기 때문**이다. 없으면 `in` 한 번으로 끝난다.
- ★★ **그래서 「예외가 비싸다」는 반쪽이다.** 비싼 것은 **예외가 실제로 날 때**이고,
  **안 날 때의 `try` 문 자체는 거의 공짜**다.
- ★ 신호 대 잡음 — 성공률 0% 쪽은 **5배 이상**이라 안전하고, 100% 쪽은 **0.75\~0.88** 로 신호가 작지만
  **세 판 모두 1 미만**이라 방향은 읽어도 된다. **배수는 읽지 않는다.**

**비용** — 측정 자체가 **이 머신·이 부하의 관찰**이다. 절댓값을 옮겨 적지 않는다.

### 5. ★ 손익분기 — 실패율 몇 %에서 뒤집히나

**언제 쓰나** — 「우리 코드의 실패율이 이 정도인데 어느 쪽인가」를 물을 때.

키 100개짜리 목록을 한 번 훑는 비용을 재면서 **없는 키의 비율만** 바꿨다.

```python
# e26_breakeven.py
import statistics
import timeit

SETUP = """
d = {"A": 1}
keys = ["A"] * (100 - MISS) + ["Z"] * MISS
def lbyl():
    for k in keys:
        if k in d:
            d[k]
def eafp():
    for k in keys:
        try:
            d[k]
        except KeyError:
            pass
lbyl(); eafp()
"""

N = 3000
print("키 100개짜리 목록을 한 번 훑는 비용. 그 중 MISS 개만 없는 키다.")
print("한 판 = repeat 11 회의 중앙값, number=%d. 판 셋." % N)
print()
print("%-8s %-28s %-28s %s" % ("MISS", "LBYL 마이크로초", "EAFP 마이크로초", "EAFP/LBYL"))
for miss in (0, 5, 10, 20, 50, 100):
    setup = "MISS = %d\n" % miss + SETUP
    row = {}
    for kind, stmt in (("LBYL", "lbyl()"), ("EAFP", "eafp()")):
        timeit.repeat(stmt, setup=setup, repeat=3, number=N)
        row[kind] = [statistics.median(
            timeit.repeat(stmt, setup=setup, repeat=11, number=N)) / N * 1e6
            for _ in range(3)]
    ratios = [e / l for e, l in zip(row["EAFP"], row["LBYL"])]
    print("%-8d %6.2f/%6.2f/%6.2f       %6.2f/%6.2f/%6.2f       %.2f/%.2f/%.2f"
          % (miss, *row["LBYL"], *row["EAFP"], *ratios))
```

```text
===== python3 - <e26_breakeven.py =====
키 100개짜리 목록을 한 번 훑는 비용. 그 중 MISS 개만 없는 키다.
한 판 = repeat 11 회의 중앙값, number=3000. 판 셋.

MISS     LBYL 마이크로초                   EAFP 마이크로초                   EAFP/LBYL
0          2.85/  2.76/  2.91         1.56/  1.76/  1.78       0.55/0.64/0.61
5          3.01/  2.61/  2.67         2.65/  2.75/  2.61       0.88/1.05/0.98
10         2.94/  2.81/  2.75         3.15/  2.87/  3.03       1.07/1.02/1.10
20         2.86/  2.76/  2.72         4.23/  4.31/  3.68       1.48/1.56/1.35
50         1.94/  2.02/  1.92         7.19/  7.16/  7.40       3.70/3.55/3.85
100        1.47/  1.50/  1.55        14.27/ 14.09/ 14.40       9.74/9.38/9.30
(exit 0)
```

```text
   EAFP/LBYL 비 (판 셋의 값)

   MISS  0% : 0.55 0.64 0.61   ##########            EAFP 압승
   MISS  5% : 0.88 1.05 0.98   ################      ★ 1 을 넘나든다
   MISS 10% : 1.07 1.02 1.10   ##################    LBYL 이 앞선다
   MISS 20% : 1.48 1.56 1.35   ##########################
   MISS 50% : 3.70 3.55 3.85   ###############################################
   MISS100% : 9.74 9.38 9.30   ####################################### x2
```

- **손익분기는 5\~10% 사이**다. 실패가 **한 자릿수 %** 면 EAFP, **두 자릿수** 면 LBYL 쪽이 싸다.
- ★★ **5% 칸은 세 판이 `0.88 / 1.05 / 0.98` 로 1 을 넘나든다.** 그 칸은 **비용이 비슷한 두 후보가 맞붙는 지점**이다 —
  **그 칸 위에 결론을 세우지 않는다.** 결론은 0%·50%·100% 처럼 **떨어져 있는 칸**에서 나온다.
★★ **제출 직전에 한 번 더 쟀다 — 그리고 맞붙는 칸이 움직였다.**
재실행에서 **5% 칸이 `0.77 / 0.96 / 0.83`(세 판 모두 1 미만)**, **10% 칸이 `0.98 / 1.01 / 1.09`(1 을 넘나든다)** 였다.
**처음 값을 지우지 않고 나란히 남긴다** — 움직였다는 사실 자체가 이 절의 결론이다.

| 칸 | 첫 측정(위 블록) | 제출 직전 재측정 | 여섯 판을 합치면 |
|---|---|---|---|
| MISS 5% | `0.88 / 1.05 / 0.98` | `0.77 / 0.96 / 0.83` | 여섯 중 **다섯 판이 1 미만** |
| MISS 10% | `1.07 / 1.02 / 1.10` | `0.98 / 1.01 / 1.09` | 여섯 중 **다섯 판이 1 초과** |

★ 그래서 적을 수 있는 것은 「**손익분기가 5\~10% 사이에 있다**」까지다.
**어느 한 칸을 「여기서 뒤집힌다」로 못 박으면 다음 실행에서 거짓이 된다.**

- ★ 이 표에서 흔들리지 않는 것은 **비의 단조 증가**다 — 세 판 모두 아래로 갈수록 커진다.

**비용** — 이 수치는 **`dict` 조회라는 가장 싼 연산**에서 잰 것이다.
실행이 무거우면(네트워크·디스크) **예외 비용의 비중이 작아져 손익분기가 올라간다.** **여기서 그건 안 쟀다.**

### 6. ★ 덕 타이핑과 `hasattr` — 둘의 실패 모양이 다르다

**언제 쓰나** — 「이 객체가 이 메서드를 갖고 있나」를 검사하고 싶을 때.

```python
# e26_hasattr.py
class Duck:
    def quack(self):
        return "꽥"


class Inner:
    def quack(self):
        return self.없는속성


class Broken:
    @property
    def quack(self):
        raise AttributeError("게터가 AttributeError 를 낸다")


def lbyl(obj):
    if hasattr(obj, "quack"):
        return obj.quack()
    return "(못 운다)"


def eafp(obj):
    try:
        return obj.quack()
    except AttributeError:
        return "(못 운다)"


for name, obj in (("Duck", Duck()), ("int 3", 3),
                  ("Inner", Inner()), ("Broken", Broken())):
    for kind, fn in (("LBYL(hasattr)", lbyl), ("EAFP(try)", eafp)):
        try:
            out = fn(obj)
        except Exception as e:
            out = "%s 가 밖으로 나왔다: %s" % (type(e).__name__, e)
        print("%-8s %-16s %s" % (name, kind, out))
```

```text
===== python3 - <e26_hasattr.py =====
Duck     LBYL(hasattr)    꽥
Duck     EAFP(try)        꽥
int 3    LBYL(hasattr)    (못 운다)
int 3    EAFP(try)        (못 운다)
Inner    LBYL(hasattr)    AttributeError 가 밖으로 나왔다: 'Inner' object has no attribute '없는속성'
Inner    EAFP(try)        (못 운다)
Broken   LBYL(hasattr)    (못 운다)
Broken   EAFP(try)        (못 운다)
(exit 0)
```

★★ **네 칸을 갈라 읽어야 한다** — 이 절의 값이 거기 있다.

| 대상 | LBYL(`hasattr`) | EAFP(`try`) | 무슨 일인가 |
|---|---|---|---|
| `Duck`(정상) | `꽥` | `꽥` | **같다** |
| `int 3`(정말 없다) | `(못 운다)` | `(못 운다)` | **같다** |
| ★ `Inner`(메서드 **몸통**에서 `AttributeError`) | **밖으로 나온다** | `(못 운다)` | ★★ **EAFP 가 진짜 버그를 삼킨다** |
| `Broken`(게터가 `AttributeError`) | `(못 운다)` | `(못 운다)` | **둘 다 숨긴다** |

- ★★ **`Inner` 칸이 이 주제에서 EAFP 가 지는 자리다.** `try` 그물이 **호출 안쪽까지 덮기 때문**에
  「메서드가 없다」와 「메서드 안이 망가졌다」를 **구분 못 한다.** `hasattr` 쪽은 진짜 오류를 드러냈다.
- ★ `Broken` 칸은 **둘 다 진다.** `hasattr` 는 **`AttributeError` 만** 삼키는데(3.2+),
  게터가 바로 그 예외를 내면 **「속성이 없다」로 읽힌다.**
- 처방은 하나다 — **`try` 의 범위를 속성을 꺼내는 데까지만** 좁힌다(`getattr(obj, "quack", None)` 로 꺼내 놓고 부른다).

**비용** — `hasattr` 는 속성을 **실제로 꺼내 본다**(프로퍼티면 게터가 돈다). 부작용이 있는 프로퍼티에서는 **두 번 돈다.**

### 7. `dict.get` 대 `try/KeyError` — 접어 둔 LBYL

**언제 쓰나** — dict 를 읽을 때마다. 가장 자주 만나는 선택이다.

```python
# e26_dict_get.py
import collections

d = {"A": 1, "N": None}


def with_get(key):
    return d.get(key)


def with_try(key):
    try:
        return d[key]
    except KeyError:
        return "(키가 없다)"


print("A = 값 1 · N = 값 None · Z = 키 자체가 없다")
for key in ("A", "N", "Z"):
    print("  %s  get(): %-8r try/KeyError: %r" % (key, with_get(key), with_try(key)))

print()
print("조회만 했을 때 dict 가 커지나 — 셋을 나란히")
plain = {"a": 1}
plain.get("b")
print("  get        :", sorted(plain), "· 길이", len(plain))

sd = {"a": 1}
sd.setdefault("b", 0)
print("  setdefault :", sorted(sd), "· 길이", len(sd))

dd = collections.defaultdict(int, {"a": 1})
dd["b"]
print("  defaultdict:", sorted(dd), "· 길이", len(dd))
```

```text
===== python3 - <e26_dict_get.py =====
A = 값 1 · N = 값 None · Z = 키 자체가 없다
  A  get(): 1        try/KeyError: 1
  N  get(): None     try/KeyError: None
  Z  get(): None     try/KeyError: '(키가 없다)'

조회만 했을 때 dict 가 커지나 — 셋을 나란히
  get        : ['a'] · 길이 1
  setdefault : ['a', 'b'] · 길이 2
  defaultdict: ['a', 'b'] · 길이 2
(exit 0)
```

- ★ **`get` 은 「키가 없다」와 「값이 `None` 이다」를 구분하지 못한다**(`N` 줄과 `Z` 줄이 같다).
  구분해야 하면 **`try/KeyError` 나 `in`** 을 쓴다.
- ★ **조회만으로 dict 가 커지는 것 둘** — `setdefault` 와 `defaultdict` 다.
  `get` 은 안 커진다. **읽기만 할 생각이면 `get`** 이다.
- `get` 은 **조회 한 번**이다 — LBYL 의 두 번 조회를 C 쪽에서 접어 둔 것이라, **속도로는 EAFP 와 겨룰 만하다.**
  (수치는 안 쟀다 — **동작 4·5 는 `in` + `[]` 형태를 쟀다.**)

**비용** — 기본값이 **매 호출 평가**된다. `d.get(k, 비싼함수())` 는 키가 있어도 `비싼함수()` 를 부른다.
그 자리에서는 `try/KeyError` 나 `setdefault` 대신 **`if` 로 분기**한다.

### 8. 그래서 어느 쪽을 고르나

**언제 쓰나** — 위 일곱 절을 하나로 접을 때.

```text
   ① 검사와 실행 사이에 남이 끼어들 수 있나?
        예 -> EAFP  (동작 2 — 정확성 문제다. 속도로 못 뒤집는다)
        아니오 |
   ② 검사가 실행과 "같은 기준" 인가?
        아니다 -> EAFP  (동작 3 — isdigit 은 int 의 기준이 아니다)
        그렇다 |
   ③ 실패율이 몇 % 인가?
        한 자릿수 -> EAFP   (동작 5 — 손익분기 5~10%)
        두 자릿수 -> LBYL
   ④ 표준 API 가 이미 접어 둔 것이 있나?
        있다 -> 그것을 쓴다  (dict.get · getattr(o, n, 기본) · contextlib.suppress)
```

★ **①과 ②는 속도와 무관한 판정이고, ③만 속도 판정이다.**
그래서 **성능 얘기부터 꺼내면 순서가 뒤집힌 것**이다.

**비용** — 없다. 판정 순서를 지키는 것뿐이다.

## 문법 — 형태와 규칙

**형태 — 네 가지뿐이다**

```python
# e26_forms.py
import contextlib

CODES = {"A": "승인"}


# ① LBYL — 먼저 보고 뛴다
def lbyl(d, key):
    if key in d:
        return d[key]
    return "(없음)"


# ② EAFP — 일단 뛰고 걸리면 잡는다
def eafp(d, key):
    try:
        return d[key]
    except KeyError:
        return "(없음)"


# ③ 그 둘을 표준 API 가 미리 접어 둔 것들
def folded(d, key, obj):
    d.get(key, "(없음)")                  # dict 전용 LBYL
    getattr(obj, "quack", None)           # 속성 전용 LBYL
    with contextlib.suppress(KeyError):   # try/except/pass 를 한 줄로
        d[key]


# ④ 예외를 좁게 잡는다 — 넓게 잡으면 EAFP 가 아니라 삼키기가 된다
def narrow(s):
    try:
        return int(s)
    except ValueError:        # ○ 이 호출이 낼 수 있는 것만
        return None


def too_broad(s):
    try:
        return int(s)
    except Exception:         # ✗ 오타로 난 NameError 까지 삼킨다
        return None
```

규칙 여덟.

1. **두 관용구는 같은 답을 낸다** — 갈리는 것은 답이 아니라 **경쟁 조건·검사 정확성·비용**이다.
2. ★ **검사와 실행 사이에 남이 끼어들 수 있으면 EAFP** 다. 이건 **정확성 판정**이라 속도로 못 뒤집는다.
3. ★ **검사가 실행과 같은 기준인지 확인한다.** `isdigit()` 은 `int()` 의 기준이 **아니다.**
4. **`try` 의 범위를 좁게, `except` 의 타입도 좁게.** `except Exception` 으로 넓히면 EAFP 가 아니라 **삼키기**다.
5. **실패율이 한 자릿수 %면 EAFP, 두 자릿수면 LBYL** 쪽이 싸다(이 머신의 `dict` 조회 기준).
6. **표준 API 가 접어 둔 것을 먼저 본다** — `dict.get`·`getattr(o, n, 기본)`·`contextlib.suppress`.
7. ★ **`get` 은 「없음」과 「`None`」을 구분하지 못한다.** 구분해야 하면 `in` 이나 `try/KeyError`.
8. ★ **`hasattr` 는 `AttributeError` 만 삼킨다**(3.2+). 게터가 그 예외를 내면 **「없음」으로 읽힌다.**

**금지 사례 — 문법은 맞는데 조용히 어긋나는 것들**

```python
# e26_pitfalls.py
import os

CODES = {"A": "승인"}


# ① 검사와 실행 사이에 세상이 바뀐다 (TOCTOU)
def toctou(path):
    if os.path.exists(path):
        return open(path, encoding="utf-8")   # ★ 그 사이에 지워질 수 있다
    return None


# ② 검사 자체가 틀렸다 — isdigit 은 int() 의 기준이 아니다
def wrong_test(s):
    if s.isdigit():
        return int(s)          # ★ '²' 는 isdigit 이 True 인데 int() 가 터진다
    return None


# ③ EAFP 로 써 놓고 그물을 넓게 친다
def swallow_all(d, key):
    try:
        return d[kye]          # ★ 오타. NameError 인데
    except Exception:
        return "(없음)"         #   "키가 없다" 로 보고된다


# ④ 검사를 두 번 한다 — LBYL 은 조회가 두 번이다
def double_lookup(d, key):
    if key in d:               # 한 번
        return d[key]          # 두 번
    return "(없음)"


# ⑤ 예외를 흐름 제어로 쓰면서 실패율이 높다
def hot_loop(d, keys):
    out = []
    for k in keys:
        try:
            out.append(d[k])   # ★ 대부분 없는 키라면 EAFP 가 훨씬 비싸다
        except KeyError:
            out.append(None)
    return out
```

## 어디서 틀리나

### (1) ★★ 「예외는 비싸니까 LBYL」로 외운다

★ **성공률이 높으면 EAFP 가 빠르다**(비 `0.75 / 0.78 / 0.88`).
비싼 것은 **예외가 실제로 날 때**이고, 안 날 때의 `try` 문은 거의 공짜다.

### (2) ★★ 경쟁 조건을 성능 문제로 읽는다

★ **정확성 문제다.** 검사를 통과하고도 터진다 — `exists()` 가 답한 값이 **그 순간 이미 낡았다.**
속도가 아무리 유리해도 **이 판정을 못 뒤집는다.**

### (3) ★ 검사 함수가 실행과 같은 기준이라고 믿는다

★ **`'\u00b2'` 는 `isdigit()` 이 참인데 `int()` 가 터진다.** 반대로 `'-3'`·`' 7 '`·`'1_0'` 은
`isdigit()` 이 거짓인데 `int()` 가 받는다. **두 집합이 엇갈린다.**

### (4) ★ EAFP 로 쓰면서 그물을 넓게 친다

`except Exception` 으로 감싸면 **오타로 난 `NameError` 까지** 「키가 없다」로 보고된다.
**EAFP 는 「좁게 잡는 것」까지가 한 벌**이다.

### (5) ★ `try` 범위를 호출 안쪽까지 넓힌다

`hasattr` 실험의 `Inner` 칸이 그 자리다 — **메서드 몸통에서 난 `AttributeError` 를 「메서드가 없다」로 읽는다.**
속성을 **꺼내는 데까지만** 감싼다.

### (6) `dict.get` 으로 「키가 있나」를 판정한다

★ **값이 `None` 이면 없는 것과 구분이 안 된다.** `in` 이나 `try/KeyError` 를 쓴다.

### (7) 조회만 할 자리에 `setdefault`·`defaultdict` 를 쓴다

**읽기만 해도 dict 가 커진다.** 실측에서 둘 다 길이가 1 에서 2 가 됐다.

### (8) `d.get(k, 비싼함수())` 를 쓴다

**기본값이 매 호출 평가된다.** 키가 있어도 `비싼함수()` 가 돈다 —
[05번](../05-truthiness-and-short-circuit/2-summary.md)의 단축 평가가 **여기서는 안 걸린다**(인자는 먼저 평가된다).

### (9) LBYL 의 조회 두 번을 잊는다

`if k in d: d[k]` 는 **해시를 두 번** 계산한다. 그래서 **성공률이 높으면 LBYL 이 진다.**

### (10) 손익분기 표의 흔들리는 칸 위에 결론을 세운다

★ **5% 칸은 세 판이 `0.88 / 1.05 / 0.98` 로 1 을 넘나든다.**
결론은 **떨어져 있는 칸**(0%·50%·100%)에서 세운다.

### (11) 이 수치를 다른 작업에 그대로 옮긴다

★ 이 표는 **`dict` 조회**라는 가장 싼 실행에서 잰 것이다.
실행이 무거우면 예외 비용의 비중이 작아져 **손익분기가 올라간다** — **여기서 안 쟀다.**

### (12) EAFP 가 언제나 경쟁에 강하다고 믿는다

**자원을 잡는 연산이 원자적일 때만** 그렇다. 잡은 뒤에 또 검사하면 **같은 틈이 다시 생긴다.**

## 구현 세부사항 대 언어 보장

세 층으로 가른다. ★ **이 주제는 「언어 보장」이 얇다** — 언어는 **어느 쪽을 쓰라고 정해 주지 않는다.**
보장에 해당하는 것은 **개별 API 의 계약**뿐이고, 판정은 전부 **측정과 재현**에서 나온다.

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **언어 보장** | 용어집·라이브러리 문서가 정한 개별 계약 | 공식 문서 문장을 열어서 인용 |
| **CPython 구현** | 이 구현이 그렇게 하는 것 | 예외 문구 · `hasattr` 의 삼키는 범위 |
| **이 판·이 머신의 관찰** | `timeit` 수치 전부 | 판 셋 · 예열 판 |

### 언어 보장

| 사실 | 근거 |
|---|---|
| **LBYL 은 검사와 실행 사이에 경쟁 조건을 만들 수 있다** | glossary — LBYL(문장 인용) |
| `dict.get(k[, d])` 는 **키가 없으면 기본값**을 돌려주고 **`KeyError` 를 안 낸다** | `dict.get` |
| `dict.setdefault` 는 **없으면 넣고** 돌려준다 — **쓰기 연산**이다 | `dict.setdefault` |
| `defaultdict` 는 **`__getitem__` 에서** 없는 키를 만든다 | `collections.defaultdict` |
| **`hasattr` 는 `AttributeError` 만 삼킨다**(3.2+) | `hasattr` |
| `str.isdigit()` 과 `int()` 의 판정 기준이 **다르다** | `str.isdigit` · `int` |
| `int()` 는 **앞뒤 공백과 밑줄 구분자**를 받는다 | `int` |

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| 예외 메시지 문구 — `invalid literal for int() with base 10: ...` 등 | 실행 |
| `'\u00b2'` 가 `isdigit()` 참인데 `int()` 가 거부하는 **구체적 사례** | 실행 |
| 열린 파일이 **이름이 지워져도 읽힌다**(이 OS 의 성질) | 실행 — 경쟁 조건 블록 ③ |

### 이 판(3.12.3)·이 머신의 관찰

| 관찰 | 어디가 흔들리나 |
|---|---|
| `timeit` 의 **나노초·마이크로초 값** 전부 | **다시 돌리면 또 달라진다.** 대조 대상은 **비의 부호**다 |
| 성공률 100% 의 비 `0.75 / 0.78 / 0.88` | 신호가 작다. **1 미만이라는 것만** 읽는다 |
| 성공률 0% 의 비 `6.26 / 5.10 / 5.23` | 신호가 5배 이상이라 안전하다 |
| 손익분기 **5\~10% 사이** | ★ **5% 칸은 1 을 넘나든다.** 그 위에 결론을 세우지 않는다 |

### 그래서 이렇게 적으면 틀린다

- ✗ 「예외는 비싸니까 검사부터 해라」\
  ○ **성공률이 높으면 EAFP 가 빠르다.** 비싼 것은 **예외가 날 때**다.
- ✗ 「파이썬은 EAFP 언어니까 언제나 EAFP」\
  ○ **실패율이 두 자릿수면 진다**(손익분기 5\~10%).
- ✗ 「경쟁 조건은 멀티스레드 얘기다」\
  ○ **다른 프로세스·다른 사용자·OS 전부 해당**한다. 이 문서의 재현은 **단일 스레드**다.
- ✗ 「`isdigit()` 로 거르면 `int()` 가 안 터진다」\
  ○ **`'\u00b2'` 에서 터진다.** 두 기준은 **서로 엇갈린다.**
- ✗ 「`hasattr` 가 참이면 부를 수 있다」\
  ○ **몸통에서 터질 수 있다.** 그리고 게터가 `AttributeError` 를 내면 **거짓이 나온다.**
- ✗ 「`get` 이 `None` 을 주면 키가 없는 것」\
  ○ **값이 `None` 인 경우와 구분이 안 된다.**
- ✗ 「`try` 로 감쌌으니 EAFP 다」\
  ○ **그물이 넓으면 삼키기**다. `except` 타입을 좁히는 것까지가 한 벌이다.
- ✗ 「이 표의 손익분기는 어디서나 5\~10% 다」\
  ○ **`dict` 조회 기준**이다. 실행이 무거우면 올라간다 — **안 쟀다.**

**판정 기준 한 줄**: **「검사와 실행 사이에 남이 끼어들 수 있나」를 물으면 정확성이 갈리고,
「실패율이 몇 %인가」를 물으면 비용이 갈린다. 앞엣것이 먼저다.**

## 언제 쓰고 언제 안 쓰나

| 상황 | 판정 |
|---|---|
| 파일·소켓·DB 처럼 **남이 건드리는 자원** | ★ **EAFP** — 경쟁 조건은 속도로 못 뒤집는다 |
| dict 에서 **거의 항상 있는 키**를 읽는다 | ★ **EAFP** 또는 **`dict.get`** — LBYL 은 조회가 두 번 |
| dict 에서 **대부분 없는 키**를 읽는다 | **LBYL**(`in`) — 손익분기 두 자릿수 쪽 |
| 「없음」과 「값이 `None`」을 **구분해야** 한다 | **`in` 이나 `try/KeyError`** — `get` 은 못 한다 |
| 속성이 있는지 본다 | `getattr(o, n, 기본)` — **꺼내는 데까지만** 감싼다 |
| 문자열이 숫자인지 본다 | ★ **`try: int(s)`** — `isdigit()` 은 기준이 다르다 |
| 기본값이 **비싼 계산**이다 | **`if` 로 분기**한다 — `get` 의 기본값은 매번 평가된다 |
| 읽기만 할 건데 `defaultdict` 를 쓴다 | ★ **안 된다** — 조회만으로 커진다 |
| 예외를 삼키고 넘어가고 싶다 | `contextlib.suppress(구체타입)` — 정본은 [28번](../28-context-managers-and-with/2-summary.md) |
| 실패를 **여럿 모아** 보고해야 한다 | [27번](../27-exception-groups-and-except-star/2-summary.md) — `ExceptionGroup`(3.11+) |

## 핵심 문장

- ★★ **두 관용구는 같은 답을 낸다.** 갈리는 것은 답이 아니라 **경쟁 조건 · 검사 정확성 · 비용** 셋이고,
  **앞의 둘은 속도로 못 뒤집는 판정**이다.
- ★★ **「예외는 비싸다」는 반쪽이다.** 성공률 100% 에서 EAFP/LBYL 비가 `0.75 / 0.78 / 0.88`(EAFP 가 빠르다),
  성공률 0% 에서 `6.26 / 5.10 / 5.23`(EAFP 가 5배 이상 느리다). **비싼 것은 예외가 실제로 날 때**다.
- ★★ **손익분기는 실패율 5\~10% 사이**다(이 머신의 `dict` 조회 기준).
  ★★ **맞붙는 칸은 실행마다 옮겨 간다** — 첫 측정에서는 5% 칸이, 제출 직전 재측정에서는 10% 칸이 1 을 넘나들었다.
  **어느 한 칸 위에도 결론을 세우지 않는다.**
- ★★ **경쟁 조건은 시간이 아니라 순서로 보인다.** 검사와 실행 사이에 파일을 지우는 순서를 고정하면
  **매번 같은 네 줄**이 나온다 — LBYL 은 **검사를 통과하고도 터지고**, EAFP 는 **이미 잡은 파일을 읽는다.**
- ★ **LBYL 의 검사가 틀릴 수 있다.** `'\u00b2'` 는 `isdigit()` 이 참인데 `int()` 가 터지고,
  `'-3'`·`' 7 '`·`'1_0'` 은 그 반대다 — **두 집합이 포함 관계가 아니라 엇갈린다.**
- ★ **`try` 범위를 넓히면 EAFP 가 아니라 삼키기가 된다.** 메서드 몸통의 `AttributeError` 를
  「메서드가 없다」로 읽은 `Inner` 칸이 그 증거다.
- ★ **`hasattr` 는 `AttributeError` 만 삼킨다**(3.2+). 게터가 그 예외를 내면 **「없다」가 나온다.**
- ★ **`dict.get` 은 「없음」과 「`None`」을 구분하지 못하고**, `setdefault`·`defaultdict` 는 **조회만으로 커진다.**
- ★ **고르는 순서는 ① 경쟁 조건 → ② 검사 기준 → ③ 실패율 → ④ 접어 둔 API** 다.
  **성능부터 꺼내면 순서가 뒤집힌 것**이다.

## 관련 자료

- 목록: [python/syntax 주제 목록](../README.md) — 이 주제는 **26번**
- 선행: [25-exceptions-and-finally](../25-exceptions-and-finally/2-summary.md) — **예외 문법의 정본.**\
  **경계**: `try`/`except`/`else`/`finally` 의 실행 순서와 연쇄는 전부 그쪽. 여기는 **고르는 법과 비용**뿐이다.
- 선행: [12-dict-and-key-requirements](../12-dict-and-key-requirements/2-summary.md) — `get`·`setdefault`·뷰.\
  **경계**: dict API 자체는 그쪽, **「어느 쪽을 고르나」** 만 여기다.
- 선행: [05-truthiness-and-short-circuit](../05-truthiness-and-short-circuit/2-summary.md) — 단축 평가.\
  **경계**: `d.get(k, 비싼함수())` 가 **단축 평가에 안 걸리는 이유**(인자는 먼저 평가된다)가 그 규칙의 적용이다.
- 함께 보는 곳: [16-iterator-protocol](../16-iterator-protocol/2-summary.md) — `next(it, 기본값)` 이
  **이 주제의 접어 둔 API** 에 해당한다.
- 이어지는 곳: [27-exception-groups-and-except-star](../27-exception-groups-and-except-star/2-summary.md) — 실패를 **여럿 모아** 나르는 법.
- 이어지는 곳: [28-context-managers-and-with](../28-context-managers-and-with/2-summary.md) — `contextlib.suppress` 의 정본.
- 이어지는 곳: `[목록의 **43번 주제**](../43-collections/)` — `collections.defaultdict`·`Counter` 의 정본.
- 이어지는 곳: `[목록의 **48번 주제**](../48-pathlib-and-file-io/)` — `pathlib` 와 파일 I/O. **경쟁 조건의 실무 자리**가 거기다.
- 다른 갈래: Go 갈래 목록([`go/syntax/README.md`](../../../go/syntax/README.md))의 **23번** — `(T, error)`.
  Go 는 **실패를 반환값으로** 받으므로 이 선택 자체가 생기지 않는다 — **언제나 「검사」 쪽**이다.
- 다른 갈래: Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **23번** — `panic!` 대 `Result`.
  `Result` 는 Go 와 같은 자리이고, `panic!` 은 **복구 대상이 아닌 쪽**이라 EAFP 와 성격이 다르다.
- 공식 문서: [EAFP](https://docs.python.org/3.12/glossary.html#term-EAFP) ·
  [LBYL](https://docs.python.org/3.12/glossary.html#term-LBYL) ·
  [`hasattr`](https://docs.python.org/3.12/library/functions.html#hasattr) ·
  [`timeit`](https://docs.python.org/3.12/library/timeit.html)

## 용어 풀이

- **EAFP**: 일단 하고 안 되면 예외를 잡는 방식(*Easier to Ask Forgiveness than Permission*).\
  예: `try: d[k] except KeyError: ...`
- **LBYL**: 하기 전에 조건을 확인하는 방식(*Look Before You Leap*).\
  예: `if k in d: d[k]`
- **TOCTOU**: 확인한 시점과 쓰는 시점 사이에 세상이 바뀌어 생기는 버그.\
  예: `exists()` 뒤에 파일이 지워지면 통과한 검사가 뜻을 잃는다.
- **경쟁 조건(race condition)**: 두 일의 **순서**에 따라 결과가 달라지는 상태.\
  예: 지우는 일이 검사 뒤·열기 앞에 끼면 LBYL 이 터진다.
- **덕 타이핑(duck typing)**: 타입이 아니라 **할 수 있는 일**로 판정하는 것.\
  예: `quack()` 이 되면 오리로 친다.
- **중앙값(median)**: 정렬해서 가운데 값. 평균과 달리 **한 번의 튄 값에 안 끌려간다.**\
  예: `repeat` 11 회 중 6번째 값.
- **예열 판(warm-up)**: 버릴 셈 치고 먼저 한 번 돌리는 측정.\
  예: 캐시·분기 예측이 자리 잡기 전의 값을 안 섞으려고 쓴다.
- **손익분기(break-even)**: 두 방법의 비용이 같아지는 지점.\
  예: 여기서는 실패율 5\~10% 사이.
- **신호 대 잡음**: 재려는 차이가 **흔들림보다 큰가**.\
  예: 5배는 안전하고, 1.03배는 못 읽는다.
- **`dict.get(k, d)`**: 없으면 기본값. **조회 한 번**이고 dict 를 안 바꾼다.\
  예: 「없음」과 「`None`」을 구분하지 못한다.
- **`dict.setdefault(k, d)`**: 없으면 **넣고** 돌려준다 — **쓰기 연산**이다.\
  예: 조회만 해도 길이가 는다.
- **`contextlib.suppress`**: `try/except/pass` 를 한 줄로 만든 컨텍스트 매니저.\
  예: 정본은 [28번](../28-context-managers-and-with/2-summary.md).
- **원자적(atomic)**: 중간 상태가 남에게 안 보이는 연산.\
  예: `open()` 은 이름 찾기와 잡기를 한 번에 한다.

## 더 들어가면

- ★ **실행이 무거우면 손익분기가 올라간다** — 예외 비용이 전체에서 차지하는 비중이 줄기 때문이다.
  **네트워크·디스크 작업으로는 안 쟀다.**
- ★ **`try` 문이 도는 것 자체의 비용**은 거의 0 이지만 **0 은 아니다.**
  3.11 의 zero-cost exception 이후로 특히 그렇다 — **판별 비교는 안 돌려 봤다**(이 머신에 3.10 이하가 없다).
- **`os.open` 의 `O_EXCL`·`O_CREAT`** — 경쟁 조건을 **OS 쪽에서** 없애는 길. 이 주제에서는 안 돌려 봤다.
- ★ **타입 힌트·정적 검사기는 LBYL 쪽을 편든다** — 검사 뒤의 좁힘(narrowing)을 읽을 수 있기 때문이다.
  그 이야기는 `[목록의 **40번 주제**](../40-type-hints-at-runtime/)`·`[목록의 **41번 주제**](../41-typing-and-generic-syntax/)` 다.
- ★ **`contextlib.suppress` 는 EAFP 를 한 줄로 접은 것**이지만, **`try/except/pass` 보다 조금 느리다**고
  알려져 있다 — **이 문서에서는 안 쟀다.** 재지 않은 것은 적지 않는다.
