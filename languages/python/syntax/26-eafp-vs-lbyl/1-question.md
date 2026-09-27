# python/syntax/26-eafp-vs-lbyl — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> ★★ 이 주제에는 **수치 문항이 둘**(4·5) 있다. 거기서는 **숫자를 맞히는 것이 아니라
> 「어느 쪽이 크고 몇 배쯤인가」와 「어디서 뒤집히나」를 맞히는 것**이 답이다.
> ★ **흔들리는 칸 위에 답을 세우지 마라** — 5번 문항에 그 함정이 들어 있다.
>
> 실행 환경: `python3` **3.12.3** · Linux. 던지는 형태는 `python3 - <파일` 로 고정했다 —
> 트레이스백이 `File "<stdin>", line N` 으로 찍히고, **실행 중 예외에는 소스 줄도 캐럿도 안 나온다.**
> 측정은 `timeit` — **한 판 = `repeat` 11 회의 중앙값**, **판 셋**, **예열 판은 버린다.**
> ★ **이 주제는 [25번](../25-exceptions-and-finally/2-summary.md)의 문법을 전제한다.** 문법이 막히면 그쪽부터다.
> ★ **이 사슬은 [25](../25-exceptions-and-finally/1-question.md) → 26 → [27](../27-exception-groups-and-except-star/1-question.md) → [28](../28-context-managers-and-with/1-question.md)** 로 이어진다.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. 같은 dict 를 두 관용구로 읽으면 (예측)

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

- 두 줄이 각각 무엇을 찍는가? 마지막 칸은 무엇이 되는가?
- ★ 그렇다면 **두 관용구가 갈리는 것은 무엇인가** — 셋을 댈 수 있는가?

### 2. 검사와 실행 사이에 파일이 사라지면 (예측)

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

- ①②③ 이 각각 무엇을 찍는가?
- ★ **②와 ③ 이 갈리는 이유**를 한 줄로 댈 수 있는가?
- ④는 무엇을 확인하는 줄인가?

### 3. `isdigit()` 로 거른 뒤 `int()` 를 부르면 (예측)

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

- 아홉 줄 중 **두 관용구의 답이 다른 줄**은 몇 줄이고 어느 것인가?
- ★ 이 프로그램은 **끝까지 도는가**? 안 돈다면 어느 입력에서 멈추고 **어느 함수 안에서** 터지는가?
- ★ `isdigit()` 이 참인 집합과 `int()` 가 받는 집합은 **포함 관계인가**?

### 4. 성공률을 바꿔 가며 두 관용구를 재면 (예측)

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

- 네 줄의 **대소 관계**를 적어라 — 어느 것이 가장 빠르고 어느 것이 가장 느린가?
- ★ 마지막 두 줄의 **비가 1 보다 큰 쪽과 작은 쪽**은 각각 어느 상황인가? **몇 배쯤**인가?
- ★ **LBYL 쪽 두 줄끼리도 다르다.** 왜 그런가?

### 5. 실패율을 0 에서 100 까지 올리면 (예측)

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

- 마지막 열(`EAFP/LBYL`)이 **1 을 넘는 첫 행**은 어디쯤인가?
- ★★ **세 판이 서로 어긋나는 행이 있는가**? 있다면 그 행을 근거로 써도 되는가?
- 가장 아래 행의 비는 몇 배쯤인가?

### 6. `hasattr` 로 거른 쪽과 `try` 로 감싼 쪽 (예측)

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

- 여덟 줄 중 **두 관용구의 답이 다른 줄**은 몇 줄이고 어느 대상인가?
- ★ 그 줄에서 **어느 쪽이 진짜 버그를 드러내는가**?
- ★ **둘 다 같은 답을 내면서 둘 다 틀린** 대상이 있는가?

### 7. `dict.get` 이 못 하는 일 (경계)

- `d.get(k)` 가 `None` 을 돌려줬다. **키가 없는 것인가**?
- ★ `get`·`setdefault`·`defaultdict` 중 **조회만으로 dict 를 키우는 것**은 몇 개인가?
- `d.get(k, 비싼함수())` 에서 키가 **있을 때** `비싼함수()` 는 도는가?

### 8. 고르는 순서 (왜)

- 두 관용구를 고르는 기준 **넷**을 순서대로 댈 수 있는가?
- ★ 그중 **속도와 무관한 판정**은 몇 번째까지인가?
- 「성능 얘기부터 꺼내면 순서가 뒤집힌 것」이라는 말을 한 줄로 설명할 수 있는가?

### 9. 경쟁 조건을 어떻게 보일 것인가 (왜)

- 경쟁 조건을 **스레드를 여럿 돌려** 보이려 하면 무엇이 문제인가?
- ★ 이 문서는 그것을 **무엇으로 바꿔** 재현했는가?
- 「안 터졌다」가 「안전하다」가 아닌 이유를 이 주제에 붙여 말할 수 있는가?

### 10. `try` 의 범위와 `except` 의 타입 (경계)

- `except Exception` 으로 감싼 EAFP 는 **왜 EAFP 가 아닌가**?
- ★ `try` 범위를 **호출 안쪽까지** 넓히면 6번 문항의 어느 칸이 그 사고인가?
- 처방을 한 줄로 댈 수 있는가?

### 11. 표준 API 가 접어 둔 것 (연결)

- `dict.get`·`getattr(o, n, 기본)`·`next(it, 기본)`·`contextlib.suppress` 는 **네 가지 중 어느 관용구를 접은 것**인가?
- ★ `next(it, 기본)` 의 정본은 어느 주제인가?
- `contextlib.suppress` 의 정본은 어디인가?

### 12. 세 층 가르기와 이웃 경계 (경계)

- 이 주제에서 **언어 보장** · **CPython 구현 세부사항** · **이 판·이 머신의 관찰**에 해당하는 것을 각각 둘 이상 댈 수 있는가?
- ★ 이 주제의 **언어 보장이 얇은 이유**를 한 줄로 댈 수 있는가?
- **「예외 문법 자체」가 어디부터 [25번](../25-exceptions-and-finally/2-summary.md)이고, 「실패를 여럿 모으는 것」이 어디부터 [27번](../27-exception-groups-and-except-star/2-summary.md)인지** 그을 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
