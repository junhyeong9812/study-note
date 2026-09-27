# python/syntax/50-decimal-float-precision-and-round — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> ★★★ 2번은 **열한 행을 전부** 적고, 마지막 여섯 줄의 수까지 세어야 맞은 것이다.
> ★★ 이 주제는 **속도를 묻지 않는다** — 한 번도 재지 않았다.
>
> 실행 환경: `python3` **3.12.3** · Linux x86_64(8번은 `python3.11` 3.11.15 도 함께 · 3번은 `node` v18.19.1). 던지는 형태는 `python3 - <파일` 이다.
> ★ 선행 — [04](../04-numeric-types-and-division/1-question.md)(`float` 은 이진 분수 · `round` 기본 · `Decimal(0.1)`) · [47](../47-json/1-question.md)(float 왕복).

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ 네 리터럴의 저장값과 눈금 간격 (예측)

```python
# e50_bits.py
import math
from decimal import Decimal

print("[1] stored value of each literal")
for label, x in [("0.1", 0.1), ("0.2", 0.2), ("0.1 + 0.2", 0.1 + 0.2), ("0.3", 0.3)]:
    print(f"{label:<10};{x.hex():<22};{Decimal(x)}")

print("[2] the sum against 0.3")
s = 0.1 + 0.2
print("s == 0.3                    :", s == 0.3)
print("s == math.nextafter(0.3, 1) :", s == math.nextafter(0.3, 1))
print("(s - 0.3) / math.ulp(0.3)   :", (s - 0.3) / math.ulp(0.3))

print("[3] repr against 17 digits")
for x in [0.1, 0.3, s]:
    print(f"repr {repr(x):<22};.17g {format(x, '.17g'):<22};float(repr(x)) == x {float(repr(x)) == x}")

print("[4] spacing near 1e16")
print("math.ulp(1e16) :", math.ulp(1e16))
print("1e16 + 1 == 1e16 :", 1e16 + 1 == 1e16)
print("1e16 + 2 == 1e16 :", 1e16 + 2 == 1e16)
print("2.0 ** 53 + 1.0 :", repr(2.0 ** 53 + 1.0), "; + 2.0 :", repr(2.0 ** 53 + 2.0))
print("math.ulp(2.0 ** 53) :", math.ulp(2.0 ** 53))
```

### 2. ★★★ 열한 리터럴 × 세 가지 반올림 (예측)

```python
# e50_round_grid.py
from decimal import Decimal, ROUND_HALF_UP

CASES = [("0.5", 0), ("1.5", 0), ("2.5", 0), ("-2.5", 0),
         ("0.125", 2), ("0.375", 2),
         ("2.675", 2), ("1.005", 2), ("0.285", 2),
         ("2.665", 2), ("1.675", 2)]
REL = {0: "same", -1: "below", 1: "above"}

print("literal;nd;stored vs literal;round(float);round(Decimal(literal));HALF_UP(literal)")
rows = []
for lit, nd in CASES:
    x = float(lit)
    rel = REL[int(Decimal(x).compare(Decimal(lit)))]
    q = Decimal(1).scaleb(-nd)
    r_float = Decimal(repr(round(x, nd))).quantize(q)
    r_dec = round(Decimal(lit), nd)
    r_up = Decimal(lit).quantize(q, rounding=ROUND_HALF_UP)
    rows.append((rel, r_float, r_dec, r_up))
    print(f"{lit};{nd};{rel};{r_float};{r_dec};{r_up}")

n = len(rows)
vs_up = [r for r in rows if r[1] != r[3]]
vs_dec = [r for r in rows if r[1] != r[2]]
print()
print("round(float) vs HALF_UP differ :", len(vs_up), "/", n)
print("  of these, stored same  :", sum(1 for r in vs_up if r[0] == "same"))
print("  of these, stored below :", sum(1 for r in vs_up if r[0] == "below"))
print("  of these, stored above :", sum(1 for r in vs_up if r[0] == "above"))
print("round(float) vs round(Decimal(literal)) differ :", len(vs_dec), "/", n)
print("  of these, stored same  :", sum(1 for r in vs_dec if r[0] == "same"))
```

### 3. ★★ 같은 열한 리터럴을 JS `toFixed` 로 (예측)

```text
JS 탐침이 행마다 toFixed 결과를 파일에 쓰고, 파이썬 짝이 그것을 읽어 파이썬 round 와 나란히 찍는다. 열한 행과 마지막 두 줄을 적는다.
```

```javascript
// e50_tofixed.mjs
const CASES = [["0.5", 0], ["1.5", 0], ["2.5", 0], ["-2.5", 0],
  ["0.125", 2], ["0.375", 2],
  ["2.675", 2], ["1.005", 2], ["0.285", 2],
  ["2.665", 2], ["1.675", 2]];
for (const [lit, nd] of CASES) {
  console.log(`${lit};${nd};${Number(lit).toFixed(nd)};${Number(lit).toFixed(20)}`);
}
```

```python
# e50_pair.py
import sys
from decimal import Decimal

print("literal;nd;python round;js toFixed;js toFixed(20)")
rows = 0
differ = []
for line in open(sys.argv[1]):
    lit, nd, fixed, fixed20 = line.rstrip("\n").split(";")
    nd = int(nd)
    q = Decimal(1).scaleb(-nd)
    py = str(Decimal(repr(round(float(lit), nd))).quantize(q))
    rows += 1
    if py != fixed:
        differ.append(lit)
    print(f"{lit};{nd};{py};{fixed};{fixed20}")
print()
print("rows where python and js differ :", ", ".join(differ))
print("differ :", len(differ), "/", rows)
```

### 4. ★★ `Decimal` 을 만드는 다섯 길과 정밀도 6 (예측)

```python
# e50_make.py
from decimal import Decimal, getcontext, Context, ROUND_DOWN

print("[1] five ways to build")
for label, d in [("Decimal('0.1')", Decimal("0.1")),
                 ("Decimal(0.1)", Decimal(0.1)),
                 ("Decimal(str(0.1))", Decimal(str(0.1))),
                 ("Decimal.from_float(0.1)", Decimal.from_float(0.1)),
                 ("Decimal(repr(0.1 + 0.2))", Decimal(repr(0.1 + 0.2)))]:
    print(f"{label:<26};{d}")

print("[2] prec = 6, then build and add")
getcontext().prec = 6
a = Decimal("3.1415926535")
print("Decimal('3.1415926535')      :", a)
print("a + 0                        :", a + 0)
print("+a                           :", +a)
print("a + Decimal('2.7182818285')  :", a + Decimal("2.7182818285"))
print("create_decimal (prec 5, DOWN):", Context(prec=5, rounding=ROUND_DOWN).create_decimal("3.1415926535"))
getcontext().prec = 28

print("[3] trailing zeros")
x, y = Decimal("2.50"), Decimal("1.50")
print("2.50 + 1.50            :", x + y)
print("2.50 * 1.50            :", x * y)
print("Decimal('1.30') == Decimal('1.3') :", Decimal("1.30") == Decimal("1.3"))
print("str of the two         :", str(Decimal("1.30")), str(Decimal("1.3")))
print("normalize()            :", Decimal("1.30").normalize(), Decimal("100").normalize())
```

### 5. ★★ 컨텍스트 — 자릿수 · 플래그 · 반올림 모드 · 트랩 (예측)

```python
# e50_context.py
from decimal import (Decimal, getcontext, localcontext, Inexact, Rounded,
                     DivisionByZero, InvalidOperation,
                     ROUND_HALF_EVEN, ROUND_HALF_UP, ROUND_HALF_DOWN,
                     ROUND_DOWN, ROUND_UP, ROUND_CEILING, ROUND_FLOOR)

print("[1] prec")
ctx = getcontext()
print("prec, rounding :", ctx.prec, ctx.rounding)
print("1 / 3          :", Decimal(1) / 3)
print("1 / 3 * 3      :", Decimal(1) / 3 * 3)
with localcontext() as lc:
    lc.prec = 50
    print("inside prec 50 :", Decimal(1) / 3)
print("after the with :", Decimal(1) / 3)

print("[2] flags after 1 / 3")
ctx.clear_flags()
Decimal(1) / 3
print("Inexact, Rounded :", bool(ctx.flags[Inexact]), bool(ctx.flags[Rounded]))
ctx.clear_flags()
Decimal(1) / 4
print("Inexact after 1 / 4 :", bool(ctx.flags[Inexact]))

print("[3] rounding modes, quantize to '1'")
MODES = [ROUND_HALF_EVEN, ROUND_HALF_UP, ROUND_HALF_DOWN, ROUND_DOWN, ROUND_UP, ROUND_CEILING, ROUND_FLOOR]
VALUES = ["2.5", "3.5", "-2.5", "2.4", "2.6"]
print("mode;" + ";".join(VALUES))
for m in MODES:
    print(m + ";" + ";".join(str(Decimal(v).quantize(Decimal("1"), rounding=m)) for v in VALUES))
even = [Decimal(v).quantize(Decimal("1"), rounding=ROUND_HALF_EVEN) for v in VALUES]
up = [Decimal(v).quantize(Decimal("1"), rounding=ROUND_HALF_UP) for v in VALUES]
print("HALF_EVEN vs HALF_UP differ :", sum(1 for a, b in zip(even, up) if a != b), "/", len(VALUES))

print("[4] traps")
print("traps on :", sorted(k.__name__ for k, v in ctx.traps.items() if v))
for label, fn in [("Decimal(1) / 0", lambda: Decimal(1) / 0),
                  ("Decimal(0) / 0", lambda: Decimal(0) / 0),
                  ("Decimal('1e30').quantize(Decimal('0.01'))", lambda: Decimal("1e30").quantize(Decimal("0.01")))]:
    try:
        print(label, "->", fn())
    except Exception as e:
        print(label, "->", type(e).__name__)
with localcontext() as lc:
    lc.traps[DivisionByZero] = False
    lc.traps[InvalidOperation] = False
    print("traps off: 1/0 ->", Decimal(1) / 0, "; 0/0 ->", Decimal(0) / 0)
```

### 6. ★★★ `Decimal`·`float`·`Fraction` 을 섞어 계산하고 비교하면 (예측)

```python
# e50_mix.py
from decimal import Decimal, getcontext, localcontext, FloatOperation
from fractions import Fraction

print("[1] arithmetic across types")
pairs = [("Decimal('0.1') + 1", lambda: Decimal("0.1") + 1),
         ("Decimal('0.1') + 0.1", lambda: Decimal("0.1") + 0.1),
         ("Decimal('0.1') + Fraction(1, 10)", lambda: Decimal("0.1") + Fraction(1, 10)),
         ("Fraction(1, 10) + 0.1", lambda: Fraction(1, 10) + 0.1),
         ("Fraction(1, 10) + 1", lambda: Fraction(1, 10) + 1)]
for label, fn in pairs:
    try:
        v = fn()
        print(f"{label:<34};{type(v).__name__};{v!r}")
    except Exception as e:
        print(f"{label:<34};{type(e).__name__};{e}")

print("[2] comparison across types")
ctx = getcontext()
ctx.clear_flags()
for label, fn in [("Decimal('0.1') == 0.1", lambda: Decimal("0.1") == 0.1),
                  ("Decimal(0.1) == 0.1", lambda: Decimal(0.1) == 0.1),
                  ("Decimal('0.1') < 0.1", lambda: Decimal("0.1") < 0.1),
                  ("Decimal('0.5') == 0.5", lambda: Decimal("0.5") == 0.5),
                  ("Fraction(1, 10) == 0.1", lambda: Fraction(1, 10) == 0.1),
                  ("Decimal('0.1') == Fraction(1, 10)", lambda: Decimal("0.1") == Fraction(1, 10))]:
    print(f"{label:<34};{fn()}")
print("FloatOperation flag after [2] :", bool(ctx.flags[FloatOperation]))

print("[3] FloatOperation trapped")
with localcontext() as lc:
    lc.traps[FloatOperation] = True
    for label, fn in [("Decimal('0.1') == 0.1", lambda: Decimal("0.1") == 0.1),
                      ("Decimal('0.1') < 0.1", lambda: Decimal("0.1") < 0.1),
                      ("Decimal(0.1)", lambda: Decimal(0.1)),
                      ("Decimal.from_float(0.1)", lambda: Decimal.from_float(0.1))]:
        try:
            print(f"{label:<34};{fn()}")
        except Exception as e:
            print(f"{label:<34};{type(e).__name__}")

print("[4] hash and set")
print("hash(Decimal('0.5')) == hash(0.5) :", hash(Decimal("0.5")) == hash(0.5))
print("Decimal('0.1') in {0.1}          :", Decimal("0.1") in {0.1})
print("Decimal(0.1) in {0.1}            :", Decimal(0.1) in {0.1})
```

### 7. ★★★ 100.00 을 셋이 나누는 네 가지 방법 (왜)

* 각자 몫을 소수 둘째 자리로 반올림한 뒤 다시 더하면 `float` 과 `Decimal` 은 각각 **얼마**가 되나 — 둘이 다르다면 **왜**, 같다면 **왜**?
* 정수 센트로 할 때 합을 지키려면 어떤 연산 하나가 필요하고, `Fraction` 은 합은 지키는데 **무엇이 모자라나**?
* 세금 5% × `0.70` 을 `round(0.70 * 0.05, 2)` 로 구하면 정확한 곱(`0.035`)과 비교해 무엇이 나오나 — 2번 격자의 **어느 행과 같은 원인**인가?

### 8. ★★ 같은 `sum()` 소스를 두 판에서 (경계)

```python
# e50_sum.py
import math
import sys

xs = [0.1] * 10
acc = 0.0
for x in xs:
    acc += x
print("version    :", sys.version_info[:2])
print("loop +=    :", repr(acc))
print("sum(xs)    :", repr(sum(xs)))
print("math.fsum  :", repr(math.fsum(xs)))
ys = [1e100, 0.1, -1e100, 0.1]
print("sum(ys)    :", repr(sum(ys)), "; reversed", repr(sum(reversed(ys))))
print("fsum(ys)   :", repr(math.fsum(ys)))
print("sum(xs) == 1.0 :", sum(xs) == 1.0)
```

* 이 소스를 `python3.11` 과 `python3`(3.12) 로 던지면 **어느 줄이 바뀌고 어느 줄이 안 바뀌나**?
* `sum(ys)` 와 `sum(reversed(ys))` 가 3.11 에서 다르다면 **무엇 때문**이고, 그 성질을 문서는 어떤 낱말로 부르나?
* 이것을 **라이브러리 보장**으로 적으면 왜 틀리나 — 문서의 어느 두 낱말이 그 근거인가?

### 9. ★★ 예외째 끝까지 던지면 (경계)

```python
# e50_mix_throw.py
from decimal import Decimal

price = Decimal("19.99")
total = price * 1.1
```

* 이 블록의 표준 오류는 몇 줄이고 마지막 줄은 무엇인가 — 스택에 **표준 라이브러리 경로가 박히나**, 왜?
* 설정 파일에서 온 `1.1` 을 이 곱셈에 쓰려면 **경계에서** 무엇으로 바꾸나 — 그 처방이 **통하지 않는** 입력은 무엇인가?

### 10. 층 가르기 (경계)

* 「`round` 는 동점을 짝수 쪽으로 보낸다」·「파이썬 `float` 은 IEEE 754 binary64 다」·「`repr(0.1)` 이 `'0.1'` 이다」·「`sum([0.1] * 10)` 이 `1.0` 이다」 —
  각각 **라이브러리 보장 · CPython 구현 · 이 판의 관찰** 중 어디인가?
* ★ 「`decimal` 은 C 로 짜여 있다」는 어느 층이고, 그것을 **실행으로** 어떻게 확인하나?

### 11. 이웃 주제와의 경계 (연결)

* ★ [47번](../47-json/2-summary.md)이 「`1e16 + 1` 은 `json` 에 가기 전에 이미 `1e16`」이라 했다 — **어느 수 하나**가 그 까닭을 말하나? 같은 수가 `2.0 ** 53 + 1.0` 에 대해서는 무엇을 말하나?
* ★ [C# 05편](../../../csharp/syntax/05-numeric-types-checked-decimal/2-summary.md)의 `1m / 3m * 3m` 과 파이썬 기본 컨텍스트의 `Decimal(1) / 3 * 3` 은 같은 글자인가 — 두 `decimal` 의 **결정적 차이**는 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|---|---|---|---|
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |
