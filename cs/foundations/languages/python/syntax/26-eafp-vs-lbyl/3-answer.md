# python/syntax/26-eafp-vs-lbyl — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> [1-question.md](1-question.md)의 번호와 **1:1**로 대응한다. 질문 12개 = 답 12개.
>
> 이 파일의 모든 출력은 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> 던지는 형태는 `python3 - <파일` 로 고정했다 — 트레이스백이 `File "<stdin>", line N` 으로 찍히고,
> **실행 중 예외라 소스 줄도 캐럿도 안 나온다.**
> ★★ **4·5번의 수치는 흔들리는 칸이다** — 다시 돌리면 또 달라진다.
> **대조할 것**은 숫자가 아니라 「비의 부호」와 「어디서 뒤집히나」다.
> 나머지 블록은 **시간이 안 들어가서 결정적**이다 — 같은 판에서 다시 돌리면 한 글자도 안 변한다.

## 정답

### 1. 두 줄 다 같다 — 답은 안 갈린다

**출력**

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

**왜 그런가**

- 있는 키(`'A'`)도 없는 키(`'Z'`)도 **두 관용구가 같은 값**을 냈다(`같은가: True`).
- ★ **갈리는 것은 답이 아니라 셋이다.**
  - **경쟁 조건** — 검사와 실행 사이에 남이 끼어들 수 있나(2번 답).
  - **검사 정확성** — 검사가 실행과 같은 기준인가(3번 답).
  - **비용** — 실패율이 몇 %인가(4·5번 답).
- ★ 비용 쪽 실마리가 이 블록에 이미 있다 — **LBYL 은 `in` 한 번 + `[]` 한 번으로 조회가 두 번**이다.

### 2. ②에서 LBYL 만 터진다 — 검사를 통과하고도 터진다

**출력**

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

**왜 그런가**

용어집이 LBYL 항목에서 이것을 직접 경고한다.

> In a multi-threaded environment, the LBYL approach can risk introducing a race condition
> between "the looking" and "the leaping".

- ①은 **대조군**이다. 틈이 없으면 둘 다 내용을 읽는다.
- ★★ ②에서 **LBYL 이 `FileNotFoundError` 로 터졌다.** `exists()` 가 참을 답한 그 값이 **이미 낡았다** —
  검사가 아무 뜻이 없어진 것이다.
- ★ ③에서 **EAFP 는 같은 틈에서도 내용을 읽었다.** 갈리는 이유는 한 줄이다 —
  **`open()` 이 이미 파일을 잡았고, 유닉스 계열에서 열린 파일은 이름이 지워져도 살아 있다.**
- ④는 **뒷정리 확인**이다. 임시 폴더를 지웠고 남지 않았다(`False`).

```text
   LBYL                                  EAFP
   exists(path) -> True                  open(path)  -> 파일 객체를 잡았다
        |                                     |
   [ 지워진다 ]                           [ 지워진다 ]
        |                                     |
   open(path)   -> FileNotFoundError     fp.read()   -> 내용
```

### 3. 다른 줄은 **세 줄**이고, 끝까지 안 돈다 — 마지막 입력에서 `lbyl` 안이 터진다

**출력**

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

**왜 그런가**

- 두 관용구의 답이 다른 줄은 **`'-3'`·`' 7 '`·`'1_0'` 세 줄**이다.
  `int()` 는 **부호·앞뒤 공백·밑줄 구분자**를 받는데 `isdigit()` 은 전부 거짓을 답한다.
- ★★ **끝까지 안 돈다.** 마지막 입력 `'\u00b2'`(위 첨자 2)에서 멈춘다 —
  트레이스백의 아래쪽 프레임이 **`in lbyl`** 이다. **LBYL 쪽 함수 안에서** `ValueError` 가 난 것이다.
- ★ 두 집합은 **포함 관계가 아니다.** 서로 엇갈린다.

```text
   isdigit() 가 참인 것만   '\u00b2'
   둘 다 통과하는 것        '12' · '\u0661\u0662' · '\uff13\uff14'
   int() 가 받는 것만       '-3' · ' 7 ' · '1_0'
   둘 다 거부하는 것        '12.0' · 'abc'

   ★ 첫 줄과 셋째 줄이 동시에 있다 —
     어느 쪽도 다른 쪽을 포함하지 않는다. 서로 엇갈린다.
```


- ★ **「검사를 먼저 한다」의 값은 그 검사가 실행과 같은 기준일 때만 생긴다.**
  기준이 다르면 LBYL 은 **막아야 할 것을 통과시키고 통과시켜야 할 것을 막는다.**

### 4. 성공률 100% 면 EAFP 가 빠르고, 0% 면 5배 이상 느리다

**출력**

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

**왜 그런가**

★ **대조할 것은 숫자가 아니라 마지막 두 줄의 비다.**

| 상황 | EAFP / LBYL 비(판 셋) | 읽는 법 |
|---|---|---|
| 성공률 100% | `0.75 / 0.78 / 0.88` | **EAFP 가 빠르다** — 세 판 모두 1 미만 |
| 성공률 0% | `6.26 / 5.10 / 5.23` | **EAFP 가 5배 이상 느리다** |

- 가장 빠른 것은 **성공률 100% 의 EAFP**(조회 한 번), 가장 느린 것은 **성공률 0% 의 EAFP**(예외를 만들고 던지고 잡는다).
- ★ **LBYL 쪽 두 줄끼리도 다르다** — **성공률 100% 가 0% 보다 느리다.**
  키가 있으면 `in` 다음에 `[]` 를 **또** 하기 때문이고, 없으면 `in` 한 번으로 끝난다.
- ★★ 그래서 **「예외는 비싸다」는 반쪽**이다. 비싼 것은 **예외가 실제로 날 때**이고,
  **안 날 때의 `try` 문 자체는 거의 공짜**다.
- ★ **신호 대 잡음** — 0% 쪽은 5배 이상이라 안전하고, 100% 쪽은 `0.75~0.88` 로 신호가 작다.
  **방향(1 미만)만 읽고 배수는 읽지 않는다.**

### 5. 이 판에서는 10% 부터 — 그런데 그 경계가 실행마다 옮겨 간다

**출력**

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

**왜 그런가**

```text
   EAFP/LBYL 비 (판 셋의 값)

   MISS  0% : 0.55 0.64 0.61   EAFP 압승
   MISS  5% : 0.88 1.05 0.98   ★ 1 을 넘나든다 — 근거로 쓸 수 없다
   MISS 10% : 1.07 1.02 1.10   여기부터 LBYL 이 앞선다
   MISS 20% : 1.48 1.56 1.35
   MISS 50% : 3.70 3.55 3.85
   MISS100% : 9.74 9.38 9.30   약 9배
```

- **이 판에서 세 판이 전부 1 을 넘는 첫 행은 10%** 다. ★ 다만 **그 「첫 행」이 고정된 값이 아니다**(아래).
- ★★ **5% 행은 세 판이 `0.88 / 1.05 / 0.98` 로 1 을 넘나든다.**
  **비용이 비슷한 두 후보가 맞붙는 지점**이라, 한 판이 우연히 어느 쪽으로 떨어질 수 있다.
  **그 행 위에 결론을 세우면 안 된다** — 결론은 **떨어져 있는 행**(0%·50%·100%)에서 나온다.
- 그래서 적을 수 있는 것은 「**손익분기는 5\~10% 사이**」까지다. 「정확히 7%」 같은 말은 **안 잰 것**이다.
★★ **제출 직전에 한 번 더 쟀다 — 그리고 맞붙는 칸이 움직였다.**
재실행에서 **5% 칸이 `0.77 / 0.96 / 0.83`(세 판 모두 1 미만)**, **10% 칸이 `0.98 / 1.01 / 1.09`(1 을 넘나든다)** 였다.
**처음 값을 지우지 않고 나란히 남긴다** — 움직였다는 사실 자체가 이 절의 결론이다.

| 칸 | 첫 측정(위 블록) | 제출 직전 재측정 | 여섯 판을 합치면 |
|---|---|---|---|
| MISS 5% | `0.88 / 1.05 / 0.98` | `0.77 / 0.96 / 0.83` | 여섯 중 **다섯 판이 1 미만** |
| MISS 10% | `1.07 / 1.02 / 1.10` | `0.98 / 1.01 / 1.09` | 여섯 중 **다섯 판이 1 초과** |

★ 그래서 적을 수 있는 것은 「**손익분기가 5\~10% 사이에 있다**」까지다.
**어느 한 칸을 「여기서 뒤집힌다」로 못 박으면 다음 실행에서 거짓이 된다.**

- 가장 아래 행은 **약 9배**다.
- ★ 이 표에서 흔들리지 않는 것 하나 — **비가 단조 증가**한다. 세 판 모두 아래로 갈수록 커진다.

### 6. 다른 줄은 **`Inner` 두 줄**이고, 거기서는 LBYL 이 진짜 버그를 드러낸다

**출력**

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

**왜 그런가**

| 대상 | LBYL(`hasattr`) | EAFP(`try`) | 무슨 일인가 |
|---|---|---|---|
| `Duck`(정상) | `꽥` | `꽥` | 같다 |
| `int 3`(정말 없다) | `(못 운다)` | `(못 운다)` | 같다 |
| ★ `Inner`(메서드 **몸통**에서 `AttributeError`) | **밖으로 나온다** | `(못 운다)` | ★★ **EAFP 가 버그를 삼킨다** |
| `Broken`(게터가 `AttributeError`) | `(못 운다)` | `(못 운다)` | ★ **둘 다 숨긴다** |

- ★★ **`Inner` 가 이 주제에서 EAFP 가 지는 자리**다. `try` 그물이 **호출 안쪽까지 덮기 때문**에
  「메서드가 없다」와 「메서드 안이 망가졌다」를 **구분 못 한다.**
  `hasattr` 쪽은 `obj.quack()` 을 `try` 밖에서 불러 **진짜 오류를 드러냈다.**
- ★ **`Broken` 은 둘 다 틀린다.** `hasattr` 는 **`AttributeError` 만** 삼키는데(3.2+),
  게터가 바로 그 예외를 내니 **「속성이 없다」로 읽힌다.**
- 처방은 하나다 — **속성을 꺼내는 데까지만** 감싼다(`getattr(obj, "quack", None)` 로 꺼내 놓고 부른다).

### 7. `None` 은 「키가 없다」를 뜻하지 않는다

**출력**

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

**왜 그런가**

- ★ **`N`(값이 `None`) 줄과 `Z`(키가 없다) 줄의 `get()` 결과가 똑같이 `None`** 이다.
  **`get` 은 둘을 구분하지 못한다.** 구분해야 하면 **`in` 이나 `try/KeyError`** 다.
- **조회만으로 dict 를 키우는 것은 둘**이다 — `setdefault` 와 `defaultdict`(길이가 1 에서 2 가 됐다).
  **`get` 은 안 키운다.**
- ★ **`d.get(k, 비싼함수())` 는 키가 있어도 `비싼함수()` 가 돈다.**
  인자는 **호출 전에 평가**되기 때문이고, [05번](../05-truthiness-and-short-circuit/2-summary.md)의 단축 평가는
  **여기서 안 걸린다.** 그 자리에서는 `if` 로 분기한다.

### 8. 넷을 순서대로 — 앞의 둘은 속도와 무관하다

**왜 그런가**

```text
   ① 검사와 실행 사이에 남이 끼어들 수 있나?
        예 -> EAFP        (정확성 판정)
   ② 검사가 실행과 "같은 기준" 인가?
        아니다 -> EAFP     (정확성 판정)
   ③ 실패율이 몇 % 인가?
        한 자릿수 -> EAFP  (비용 판정)
        두 자릿수 -> LBYL
   ④ 표준 API 가 이미 접어 둔 것이 있나?
        있다 -> 그것을 쓴다
```

- ★ **속도와 무관한 판정은 ②까지**다. ③만 속도 판정이고, ④는 「직접 쓰지 마라」는 실무 규칙이다.
- 「성능 얘기부터 꺼내면 순서가 뒤집힌 것」이라는 말은 이렇게 읽는다 —
  **①이나 ②에 걸린 코드는 아무리 빨라도 틀린 답을 낸다.** 틀린 답은 속도로 못 갚는다.

### 9. 스레드로 보이면 재현이 안 된다 — 순서로 바꿔야 한다

**왜 그런가**

- 스레드를 여럿 돌려 「가끔 터진다」를 보이면 **두 가지가 동시에 깨진다.**
  - **재현이 안 된다** — 돌릴 때마다 결과가 다르고, 문서에 실을 출력이 정해지지 않는다.
  - ★★ **「안 터졌다」가 「안전하다」로 읽힌다** — 경쟁이 걸린 주제에서는 **통과한 실행이 가장 위험한 근거**다.
- 그래서 이 문서는 **검사와 실행 사이에 파일을 지우는 순서를 코드로 고정**했다(2번 답의 `gap()` 인자).
  「다른 프로세스가 지운다」를 **함수 호출 한 줄로 못 박은 것**이고, 그래서 **매번 같은 네 줄**이 나온다.
- ★ 이 주제에 붙여 말하면 — **경쟁 조건은 「확률」이 아니라 「틈의 존재」가 사실이다.**
  틈이 있다는 것만 보이면 되고, 그것은 **한 번의 결정적 실행으로 보일 수 있다.**

### 10. 그물이 넓으면 EAFP 가 아니라 삼키기다

**왜 그런가**

- EAFP 의 계약은 「**일단 하고, 그 연산이 낼 수 있는 예외만 잡는다**」이다.
  `except Exception` 으로 넓히면 **오타로 난 `NameError` 까지** 「키가 없다」로 보고된다 —
  **실패의 원인이 지워지는 것**이라 EAFP 가 아니다.
- ★ `try` 범위를 **호출 안쪽까지** 넓힌 사고가 6번 문항의 **`Inner` 칸**이다.
  `try: obj.quack()` 은 **속성을 찾는 일과 그 몸통이 도는 일**을 한 그물에 담는다.
- 처방 한 줄 — **`try` 의 범위는 「실패할 수 있는 그 한 연산」까지, `except` 의 타입은 「그 연산이 낼 수 있는 것」까지.**

### 11. 넷 다 LBYL 을 한 번의 연산으로 접은 것이다

**왜 그런가**

- `dict.get(k, 기본)`·`getattr(o, n, 기본)`·`next(it, 기본)`·`contextlib.suppress(타입)` —
  **전부 「검사 + 실행」을 한 번의 호출로 접었다.**
  겉보기는 LBYL(기본값을 준다)인데 **조회는 한 번**이라 EAFP 의 비용 이점도 같이 갖는다.
- ★ `next(it, 기본)` 의 **정본은 [16번](../16-iterator-protocol/2-summary.md)** 이다.
  거기서 「제너레이터 안에서 맨손 `next()` 를 쓰지 마라」의 처방으로 나온다.
- `contextlib.suppress` 의 **정본은 [28번](../28-context-managers-and-with/2-summary.md)** 이다.
  `try/except/pass` 를 컨텍스트 매니저로 굳힌 것이다.
- ★ 그래서 규칙 하나가 더 붙는다 — **직접 고르기 전에 접어 둔 것이 있는지 먼저 본다.**

### 12. 세 층과 이웃 경계

**왜 그런가**

**언어 보장**(용어집·라이브러리 문서가 정한 개별 계약)

- **LBYL 이 검사와 실행 사이에 경쟁 조건을 만들 수 있다**(glossary — LBYL).
- `dict.get` 이 **`KeyError` 를 안 낸다** · `setdefault` 가 **쓰기 연산**이다 · `defaultdict` 가 **`__getitem__` 에서** 만든다.
- **`hasattr` 는 `AttributeError` 만 삼킨다**(3.2+).
- `str.isdigit()` 과 `int()` 의 **판정 기준이 다르다** — `int()` 는 앞뒤 공백과 밑줄을 받는다.

**CPython 구현 세부사항**

- 예외 **메시지 문구** 전부(`invalid literal for int() with base 10: ...`).
- `'\u00b2'` 가 `isdigit()` 참인데 `int()` 가 거부하는 **구체적 사례**.
- 열린 파일이 **이름이 지워져도 읽히는 것**(이 OS 의 성질).

**이 판·이 머신의 관찰**

- **`timeit` 수치 전부** — 나노초·마이크로초 값.
- 비 `0.75 / 0.78 / 0.88`(성공률 100%)와 `6.26 / 5.10 / 5.23`(성공률 0%).
- **손익분기 5\~10% 사이**, 그리고 **5% 행이 1 을 넘나드는 것.**

★ **언어 보장이 얇은 이유** 한 줄 — **언어는 어느 쪽을 쓰라고 정하지 않는다.**
용어집이 두 낱말을 **이름 붙여 설명할 뿐**이고, 판정의 근거는 전부 **측정과 재현**에서 온다.

**이웃 경계 한 줄씩**

- **「예외 문법 자체」는 [25번](../25-exceptions-and-finally/2-summary.md)이다.**
  `try`/`except`/`else`/`finally` 의 순서·연쇄·계층은 전부 그쪽이고,
  여기는 **한 줄도 다시 설명하지 않는다.**
- **「실패를 여럿 모으는 것」은 [27번](../27-exception-groups-and-except-star/2-summary.md)부터다.**
  여기의 두 관용구는 **실패가 하나일 때의 선택**이다.
- **`contextlib.suppress` 의 정본은 [28번](../28-context-managers-and-with/2-summary.md)** 이다.
- **dict API 자체는 [12번](../12-dict-and-key-requirements/2-summary.md)**, `defaultdict`·`Counter` 는 `목록의 **43번 주제**` 다.

## 실행 검증

| 무엇 | 어디서 | 몇 번 | 구현·머신 의존인가 |
|---|---|---|---|
| 두 관용구가 같은 답을 내는 것 | `python3` 3.12.3 · Linux x86_64 | 캡처 + 제출 전 재실행 | **아니다** |
| 경쟁 조건 재현(①\~④) | 〃 | 〃 | **아니다** — 순서를 고정해 결정적 |
| `isdigit()` 과 `int()` 의 기준 차이 | 〃 | 〃 | **아니다** — 문서 계약 |
| `timeit` **성공률 100%·0%** | 〃 | **한 판 = repeat 11 의 중앙값 · 판 셋 · 예열 버림** | ★★ **그렇다 — 수치는 이 머신** |
| `timeit` **손익분기 스캔**(6행) | 〃 | 〃 | ★★ **그렇다.** ★ **제출 직전 재측정에서 맞붙는 행이 5% → 10% 로 옮겨 갔다**(5번 답에 두 측정을 나란히 남겼다) |
| `hasattr` 네 칸 | 〃 | 캡처 + 재실행 | **아니다** |
| `get`·`setdefault`·`defaultdict` | 〃 | 〃 | **아니다** |
| **안 돌려 본 것** | 3.2 이전의 `hasattr` · 무거운 실행(네트워크·디스크)의 손익분기 · `suppress` 대 `try/except/pass` 의 비용 · 3.10 이하의 예외 비용 | — | — |

★ **판이 올라도 다시 돌릴 필요가 없는 것** — 경쟁 조건·`isdigit`·`hasattr`·`dict` 블록.
**판이나 머신이 바뀌면 다시 재야 하는 것** — `timeit` 두 블록.
