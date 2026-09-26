# python/syntax/50-decimal-float-precision-and-round — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> [1-question.md](1-question.md)의 번호와 **1:1**로 대응한다. 질문 11개 = 답 11개.
>
> 이 파일의 모든 출력은 `python3` **3.12.3** 과 `python3.11` **3.11.15**(Linux, x86_64), 그리고 `node` **v18.19.1** 에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> 던지는 형태는 `python3 - <파일` 로 고정했다. ★ **시간은 한 번도 재지 않았다.**

## 정답

### 1. 합은 `0x1.3333333333334p-2` — `0.3` 의 **바로 다음 눈금**(1 ulp) · `repr` 은 최단인데 `float(repr(x)) == x` · `1e16` 근처 간격 `2.0` 이라 `+ 1` 이 사라진다

**출력**

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

```text
===== python3 - <e50_bits.py =====
[1] stored value of each literal
0.1       ;0x1.999999999999ap-4  ;0.1000000000000000055511151231257827021181583404541015625
0.2       ;0x1.999999999999ap-3  ;0.200000000000000011102230246251565404236316680908203125
0.1 + 0.2 ;0x1.3333333333334p-2  ;0.3000000000000000444089209850062616169452667236328125
0.3       ;0x1.3333333333333p-2  ;0.299999999999999988897769753748434595763683319091796875
[2] the sum against 0.3
s == 0.3                    : False
s == math.nextafter(0.3, 1) : True
(s - 0.3) / math.ulp(0.3)   : 1.0
[3] repr against 17 digits
repr 0.1                   ;.17g 0.10000000000000001   ;float(repr(x)) == x True
repr 0.3                   ;.17g 0.29999999999999999   ;float(repr(x)) == x True
repr 0.30000000000000004   ;.17g 0.30000000000000004   ;float(repr(x)) == x True
[4] spacing near 1e16
math.ulp(1e16) : 2.0
1e16 + 1 == 1e16 : True
1e16 + 2 == 1e16 : False
2.0 ** 53 + 1.0 : 9007199254740992.0 ; + 2.0 : 9007199254740994.0
math.ulp(2.0 ** 53) : 2.0
(exit 0)
```

**왜 그런가**

* ★★★ **`0.1 + 0.2` 는 `0.3` 과 눈금 한 칸 차이다** — `nextafter(0.3, 1)` 과 같고, 거리가 `1.0` ulp. `0.3` 을 적으면 **아래**(`0.2999…`)에, 합은 **위**(`0.3000…444`)에 붙었다.
* ★★ `repr` 은 **같은 눈금을 가리키는 가장 짧은 글자**다(3.1+ — `float_repr_style` 이 `'short'`). 17자리로 찍으면 `0.10000000000000001`.
* ★★ **`math.ulp(1e16)` 이 `2.0`** — 그 근처에는 홀수가 없다. `2.0 ** 53` 도 간격이 이미 `2.0` 이라 `+ 1.0` 이 사라진다.

### 2. 학교식과 갈린 칸 `7 / 11` = 동점(`same`) 4 + 저장값이 아래(`below`) 3 · `Decimal` 짝수 규칙과 갈린 칸 `2 / 11` 은 전부 표현 오차 · `2.665` 는 거꾸로 `2.67` 대 `2.66`

**출력**

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

```text
===== python3 - <e50_round_grid.py =====
literal;nd;stored vs literal;round(float);round(Decimal(literal));HALF_UP(literal)
0.5;0;same;0;0;1
1.5;0;same;2;2;2
2.5;0;same;2;2;3
-2.5;0;same;-2;-2;-3
0.125;2;same;0.12;0.12;0.13
0.375;2;same;0.38;0.38;0.38
2.675;2;below;2.67;2.68;2.68
1.005;2;below;1.00;1.00;1.01
0.285;2;below;0.28;0.28;0.29
2.665;2;above;2.67;2.66;2.67
1.675;2;above;1.68;1.68;1.68

round(float) vs HALF_UP differ : 7 / 11
  of these, stored same  : 4
  of these, stored below : 3
  of these, stored above : 0
round(float) vs round(Decimal(literal)) differ : 2 / 11
  of these, stored same  : 0
(exit 0)
```

**왜 그런가**

* ★★★ **`round` 는 리터럴이 아니라 저장값을 반올림한다.** 저장값이 **정확히 가운데**(`same` — `0.5`·`2.5`·`-2.5`·`0.125`)일 때만 짝수 규칙이 쓰이고, 그 넷이 학교식과 갈렸다.
* ★★★ **`below` 셋**(`2.675`·`1.005`·`0.285`)은 동점이 **아니다** — 가운데보다 아래라 가까운 쪽(아래)으로 갔다. 문서 note 가 *"This is not a bug"* 라고 적는 자리다.
* ★★ **같은 짝수 규칙을 10진 자로**(`round(Decimal(lit))`) 돌리면 `float` 과 갈리는 칸이 **`2.675`·`2.665` 둘** — 둘 다 `same` 이 아니다. **`2.665` 는 위로 비껴** `float` 이 `2.67`, `Decimal` 이 `2.66`(짝수 6).
* ★ `0.375` 는 동점인데 학교식과 같다 — 짝수 `8` 이 마침 위다.

### 3. 파이썬과 JS 가 갈린 칸 `4 / 11` — `0.5`·`2.5`·`-2.5`·`0.125`, 2번의 동점 넷 그대로 · 표현 오차 셋은 JS 도 같은 값

**출력**

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

```text
===== cd e50_js && node --version =====
v18.19.1
(exit 0)
```

```text
===== cd e50_js && node e50_tofixed.mjs > js.txt && python3 e50_pair.py js.txt =====
literal;nd;python round;js toFixed;js toFixed(20)
0.5;0;0;1;0.50000000000000000000
1.5;0;2;2;1.50000000000000000000
2.5;0;2;3;2.50000000000000000000
-2.5;0;-2;-3;-2.50000000000000000000
0.125;2;0.12;0.13;0.12500000000000000000
0.375;2;0.38;0.38;0.37500000000000000000
2.675;2;2.67;2.67;2.67499999999999982236
1.005;2;1.00;1.00;1.00499999999999989342
0.285;2;0.28;0.28;0.28499999999999997558
2.665;2;2.67;2.67;2.66500000000000003553
1.675;2;1.68;1.68;1.67500000000000004441

rows where python and js differ : 0.5, 2.5, -2.5, 0.125
differ : 4 / 11
(exit 0)
```

**왜 그런가**

* ★★★ **동점 규칙이 다른 언어**(`toFixed` 는 0 에서 먼 쪽 — [JS 03편](../../../js/syntax/03-numbers-and-bigint/2-summary.md))가 **동점 칸에서만** 파이썬과 갈렸다. 2번에서 「동점 탓」이라 가른 넷과 **한 칸도 다르지 않다.**
* ★★★ **`2.675`·`1.005`·`0.285` 는 두 언어가 같은 답**이다 — `toFixed(20)` 칸이 **같은 저장값**을 보인다. 표현 오차는 `double` 의 것이지 언어의 것이 아니다.
* ★ `0.375` 는 두 규칙이 같은 답을 주는 동점이라 안 갈렸다 — 「안 갈림 = 동점 아님」은 성립하지 않는다.

### 4. `Decimal(0.1)`·`from_float` 은 55자리 · `str()`·리터럴은 `0.1` · 합의 `repr` 은 `0.30000000000000004` · `prec 6` 에서도 생성은 11자리 그대로, `a + 0`·`+a` 가 `3.14159` · `4.00`·`3.7500` · `==` 는 `True` 인데 `str` 은 다르다

**출력**

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

```text
===== python3 - <e50_make.py =====
[1] five ways to build
Decimal('0.1')            ;0.1
Decimal(0.1)              ;0.1000000000000000055511151231257827021181583404541015625
Decimal(str(0.1))         ;0.1
Decimal.from_float(0.1)   ;0.1000000000000000055511151231257827021181583404541015625
Decimal(repr(0.1 + 0.2))  ;0.30000000000000004
[2] prec = 6, then build and add
Decimal('3.1415926535')      : 3.1415926535
a + 0                        : 3.14159
+a                           : 3.14159
a + Decimal('2.7182818285')  : 5.85987
create_decimal (prec 5, DOWN): 3.1415
[3] trailing zeros
2.50 + 1.50            : 4.00
2.50 * 1.50            : 3.7500
Decimal('1.30') == Decimal('1.3') : True
str of the two         : 1.30 1.3
normalize()            : 1.3 1E+2
(exit 0)
```

**왜 그런가**

* ★★ `float` 으로 들어가면 **눈금이 그대로** 온다. `str()` 경유는 최단 글자(`'0.1'`)를 거쳐 깨끗해지지만, **연산을 거친 값**은 최단 글자부터 이미 오염돼 있다.
* ★★★ 문서 — *"The significance of a new Decimal is determined solely by the number of digits input. Context precision and rounding only come into play during arithmetic operations."* 그래서 `prec 6` 은 **`+`·`+a`** 에서 처음 쓰인다. 생성 때부터 자르려면 `create_decimal`.
* ★ 끝자리 0 은 **지수**다 — 값 비교는 같고 글자는 다르다. `normalize()` 가 지운다(`100` 은 `1E+2`).

### 5. `prec 28` · `1/3*3` 은 `0.999…9`(28자리) · `prec 50` 은 `with` 안에서만 · `Inexact` 는 `1/3` 뒤 `True`, `1/4` 뒤 `False` · `HALF_EVEN` 대 `HALF_UP` 갈린 칸 `2 / 5` · 트랩 셋, `quantize` 초과도 `InvalidOperation`

**출력**

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

```text
===== python3 - <e50_context.py =====
[1] prec
prec, rounding : 28 ROUND_HALF_EVEN
1 / 3          : 0.3333333333333333333333333333
1 / 3 * 3      : 0.9999999999999999999999999999
inside prec 50 : 0.33333333333333333333333333333333333333333333333333
after the with : 0.3333333333333333333333333333
[2] flags after 1 / 3
Inexact, Rounded : True True
Inexact after 1 / 4 : False
[3] rounding modes, quantize to '1'
mode;2.5;3.5;-2.5;2.4;2.6
ROUND_HALF_EVEN;2;4;-2;2;3
ROUND_HALF_UP;3;4;-3;2;3
ROUND_HALF_DOWN;2;3;-2;2;3
ROUND_DOWN;2;3;-2;2;2
ROUND_UP;3;4;-3;3;3
ROUND_CEILING;3;4;-2;3;3
ROUND_FLOOR;2;3;-3;2;2
HALF_EVEN vs HALF_UP differ : 2 / 5
[4] traps
traps on : ['DivisionByZero', 'InvalidOperation', 'Overflow']
Decimal(1) / 0 -> DivisionByZero
Decimal(0) / 0 -> InvalidOperation
Decimal('1e30').quantize(Decimal('0.01')) -> InvalidOperation
traps off: 1/0 -> Infinity ; 0/0 -> NaN
(exit 0)
```

**왜 그런가**

* ★★ 컨텍스트는 **작업대**다 — `localcontext()` 는 복사본을 쓰고 원래 것으로 돌아온다(`after the with` 가 다시 28자리).
* ★★ 플래그는 **기록**이고 트랩은 **예외**다. 기본 트랩은 `DivisionByZero`·`InvalidOperation`·`Overflow` 셋 — `Inexact` 는 기록만 된다. `1e30` 을 소수 둘째 자리로 맞추면 33자리라 `prec 28` 을 넘어 `InvalidOperation`.
* ★ 모드 격자에서 `HALF_EVEN`·`HALF_UP` 은 **동점 열**(`2.5`·`-2.5`)에서만 갈린다. `ROUND_UP`(0 에서 먼 쪽)과 `ROUND_CEILING`(큰 쪽)은 **음수 열**에서 갈린다.

### 6. 연산 — `Decimal`+`float`·`Decimal`+`Fraction` 은 `TypeError`, `Fraction`+`float` 은 조용히 `float` · 비교 — `Decimal('0.1') == 0.1` 은 `False`, `Decimal(0.1) == 0.1` 은 `True`, `<` 는 `True` · 플래그 켜짐 · 트랩을 켜면 `==` 는 조용, `<`·`Decimal(0.1)` 은 `FloatOperation`, `from_float` 은 통과 · `Decimal('0.1') in {0.1}` 은 `False`

**출력**

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

```text
===== python3 - <e50_mix.py =====
[1] arithmetic across types
Decimal('0.1') + 1                ;Decimal;Decimal('1.1')
Decimal('0.1') + 0.1              ;TypeError;unsupported operand type(s) for +: 'decimal.Decimal' and 'float'
Decimal('0.1') + Fraction(1, 10)  ;TypeError;unsupported operand type(s) for +: 'decimal.Decimal' and 'Fraction'
Fraction(1, 10) + 0.1             ;float;0.2
Fraction(1, 10) + 1               ;Fraction;Fraction(11, 10)
[2] comparison across types
Decimal('0.1') == 0.1             ;False
Decimal(0.1) == 0.1               ;True
Decimal('0.1') < 0.1              ;True
Decimal('0.5') == 0.5             ;True
Fraction(1, 10) == 0.1            ;False
Decimal('0.1') == Fraction(1, 10) ;True
FloatOperation flag after [2] : True
[3] FloatOperation trapped
Decimal('0.1') == 0.1             ;False
Decimal('0.1') < 0.1              ;FloatOperation
Decimal(0.1)                      ;FloatOperation
Decimal.from_float(0.1)           ;0.1000000000000000055511151231257827021181583404541015625
[4] hash and set
hash(Decimal('0.5')) == hash(0.5) : True
Decimal('0.1') in {0.1}          : False
Decimal(0.1) in {0.1}            : True
(exit 0)
```

**왜 그런가**

* ★★★ 문서 — 생성자와 비교는 섞어도 허용되고 *"Both conversion and comparisons are exact."* **정확한 수끼리** 비교하니 `Decimal('0.1')` 과 `0.1`(=`0.1000…055`)은 다르고, `0.1` 쪽이 크다.
* ★★ 트랩을 켜면 *"only equality comparisons and explicit conversions are silent"* — `==` 와 `from_float` 만 지나가고 **생성자 `Decimal(0.1)` 도 막힌다.**
* ★★ **`Fraction` + `float` 은 `float`** 이다 — 정확한 타입이 조용히 부정확한 쪽으로 간다. `Decimal` 은 그 길을 **`TypeError` 로 막는다.**
* ★ 해시가 수 값을 따르므로 **`set`·`dict` 도 비교 규칙 그대로** 갈린다.

### 7. `float`·`Decimal` 둘 다 `99.99`(반올림한 몫을 다시 더한 절차 탓) · 센트는 `divmod` 로 나머지 1센트를 배정해 `10000` · `Fraction` 은 합 `100` 이지만 `10000/3` 센트라 못 준다 · 세금은 `float` `0.03` 대 정확한 `0.04` — 2번의 `below` 와 같은 원인

**출력**

```python
# e50_money.py
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction

print("[1] ten items of 0.10")
f = 0.0
for _ in range(10):
    f += 0.10
fs = sum([0.10] * 10)
c = sum([10] * 10)
d = sum([Decimal("0.10")] * 10)
q = sum([Fraction("0.10")] * 10)
print(f"float += ;{f!r};== 1 {f == 1}")
print(f"float sum;{fs!r};== 1 {fs == 1}")
print(f"cents    ;{c};== 100 {c == 100}")
print(f"Decimal  ;{d};== 1 {d == 1}")
print(f"Fraction ;{q};== 1 {q == 1}")

print("[2] split 100.00 three ways, then add the shares back")
TOTAL_CENTS = 10000
base, rest = divmod(TOTAL_CENTS, 3)
shares_c = [base + (1 if i < rest else 0) for i in range(3)]
cent = Decimal("0.01")
shares_d = [(Decimal("100.00") / 3).quantize(cent)] * 3
shares_q = [Fraction(100, 3)] * 3
shares_f = [round(100.00 / 3, 2)] * 3
results = [("float round", shares_f, sum(shares_f), sum(shares_f) == 100),
           ("cents divmod", shares_c, sum(shares_c), sum(shares_c) == TOTAL_CENTS),
           ("Decimal quantize", shares_d, sum(shares_d), sum(shares_d) == 100),
           ("Fraction", shares_q, sum(shares_q), sum(shares_q) == 100)]
for label, shares, s, ok in results:
    print(f"{label:<17};{', '.join(str(x) for x in shares)};sum {s};matches {ok}")
print("Fraction(100, 3) as cents :", Fraction(100, 3) * 100)

print("[3] tax 5% on 0.70, to cents")
tax_f = round(0.70 * 0.05, 2)
tax_d = (Decimal("0.70") * Decimal("0.05")).quantize(cent, rounding=ROUND_HALF_UP)
tax_c = (70 * 5 + 50) // 100
print("exact product  :", Decimal("0.70") * Decimal("0.05"))
print("float round    :", tax_f, "; stored product", Decimal(0.70 * 0.05))
print("Decimal HALF_UP:", tax_d)
print("cents integer  :", tax_c)

print()
print("totals equal to the input :", sum(1 for r in results if r[3]), "/", len(results))
```

```text
===== python3 - <e50_money.py =====
[1] ten items of 0.10
float += ;0.9999999999999999;== 1 False
float sum;1.0;== 1 True
cents    ;100;== 100 True
Decimal  ;1.00;== 1 True
Fraction ;1;== 1 True
[2] split 100.00 three ways, then add the shares back
float round      ;33.33, 33.33, 33.33;sum 99.99;matches False
cents divmod     ;3334, 3333, 3333;sum 10000;matches True
Decimal quantize ;33.33, 33.33, 33.33;sum 99.99;matches False
Fraction         ;100/3, 100/3, 100/3;sum 100;matches True
Fraction(100, 3) as cents : 10000/3
[3] tax 5% on 0.70, to cents
exact product  : 0.0350
float round    : 0.03 ; stored product 0.034999999999999996391775169968241243623197078704833984375
Decimal HALF_UP: 0.04
cents integer  : 4

totals equal to the input : 2 / 4
(exit 0)
```

**왜 그런가**

* ★★★ **입력 총액을 지킨 방식 `2 / 4`.** `Decimal` 도 틀린 것은 **정밀도가 아니라 절차** 때문이다 — 몫을 반올림하는 순간 0.01 이 셋으로 나뉘어 사라진다. **나머지를 배정**(`divmod`)해야 맞는다.
* ★★ 세금 — 정확한 곱은 `0.0350`(동점)인데 **저장된 곱이 `0.034999…`** 라 `round` 가 `0.03`. 2번의 `2.675` 와 같은 **표현 오차** 칸이다. `Decimal`·센트는 곱이 정확해 `HALF_UP` 으로 `0.04`.
* ★ `[1]` 에서 `+=` 는 `0.9999999999999999` 인데 **`sum()` 은 `1.0`** — 8번의 판 경계다.

### 8. 바뀌는 줄 — `sum(xs)`(`0.999…` → `1.0`) · `sum(ys)` 와 역순(`0.1`·`0.0` → `0.2`·`0.2`) · 마지막 줄 · 안 바뀌는 줄 — `+=` 루프 · `fsum` · 근거는 *"on most builds"*

**출력**

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

```text
===== python3 - <e50_sum.py =====
version    : (3, 12)
loop +=    : 0.9999999999999999
sum(xs)    : 1.0
math.fsum  : 1.0
sum(ys)    : 0.2 ; reversed 0.2
fsum(ys)   : 0.2
sum(xs) == 1.0 : True
(exit 0)
```

```text
===== python3.11 - <e50_sum_py311.py =====
version    : (3, 11)
loop +=    : 0.9999999999999999
sum(xs)    : 0.9999999999999999
math.fsum  : 1.0
sum(ys)    : 0.1 ; reversed 0.0
fsum(ys)   : 0.2
sum(xs) == 1.0 : False
(exit 0)
```

**왜 그런가**

* ★★★ 3.12 의 `sum()` 이 `float` 에 **Neumaier 보정 합**을 쓴다 — What's New 3.12 — *"improve accuracy and commutativity"*. 3.11 에서 `sum(ys)` 가 순서에 따라 `0.1`/`0.0` 이던 것이 **교환 법칙(commutativity)** 이 깨진 모습이다.
* ★★ **`+=` 루프는 안 바뀐다** — 바뀐 것은 `sum` 함수다. `fsum` 은 두 판 모두 정확(`1.0`·`0.2`).
* ★ 문서의 `sum` 절은 *"gives higher accuracy **on most builds**"* 라고 적는다 — **빌드에 달린 구현**이지 보장이 아니다. 테스트 기대값으로 박지 마라.

### 9. 표준 오류 3줄 · 마지막 줄 `TypeError: unsupported operand type(s) for *: 'decimal.Decimal' and 'float'` · 경로 없음(C 모듈) · 경계에서 `Decimal(str(x))` — 연산을 거친 `float` 에는 안 통한다

**출력**

```python
# e50_mix_throw.py
from decimal import Decimal

price = Decimal("19.99")
total = price * 1.1
```

```text
===== python3 - <e50_mix_throw.py =====
Traceback (most recent call last):
  File "<stdin>", line 4, in <module>
TypeError: unsupported operand type(s) for *: 'decimal.Decimal' and 'float'
(exit 1)
```

**왜 그런가**

* ★★ 스택은 `<stdin>` 의 4행 한 칸이다 — `Decimal.__mul__` 이 **C 로 구현**(`_decimal`)되어 있어 표준 라이브러리 `.py` 경로가 끼지 않는다.
* ★★ `Decimal(str(1.1))` 은 `Decimal('1.1')` — 리터럴 하나는 최단 글자로 깨끗해진다. `0.1 + 0.2` 처럼 **이미 연산을 거친 값**은 `'0.30000000000000004'` 가 된다(4번의 `[1]`).

### 10. 보장 · CPython 구현 · CPython 구현(판·플랫폼에 달림) · 이 판의 관찰(3.11 은 다르다) / `decimal` 이 C 판인 것은 CPython 구현 — `decimal.Decimal is not _pydecimal.Decimal`

**출력**

```python
# e50_impl.py
import decimal
import _pydecimal
import sys

print("float_info.mant_dig, radix :", sys.float_info.mant_dig, sys.float_info.radix)
print("float_repr_style           :", sys.float_repr_style)
print("decimal C version?         :", decimal.Decimal is not _pydecimal.Decimal, "; libmpdec", decimal.__libmpdec_version__)
print("MAX_PREC  C / pure         :", decimal.MAX_PREC, "/", _pydecimal.MAX_PREC)
print("MAX_EMAX  C / pure         :", decimal.MAX_EMAX, "/", _pydecimal.MAX_EMAX)
print("HAVE_CONTEXTVAR            :", decimal.HAVE_CONTEXTVAR)
print("same answer for 1/7        :", str(decimal.Decimal(1) / 7) == str(_pydecimal.Decimal(1) / 7))
```

```text
===== python3 - <e50_impl.py =====
float_info.mant_dig, radix : 53 2
float_repr_style           : short
decimal C version?         : True ; libmpdec 2.5.1
MAX_PREC  C / pure         : 999999999999999999 / 999999999999999999
MAX_EMAX  C / pure         : 999999999999999999 / 999999999999999999
HAVE_CONTEXTVAR            : True
same answer for 1/7        : True
(exit 0)
```

**왜 그런가**

* ★★★ `round` 의 짝수 동점은 `round()` 문서가 정한 **라이브러리 보장**이다.
* ★★★ **IEEE 754 binary64 는 구현의 사정**이다 — 문서가 *"almost all platforms map Python floats to IEEE 754 binary64"* 라고 「**거의 모든 플랫폼**」으로 한정한다. 이 머신은 `mant_dig 53`·`radix 2`.
* ★★ `repr` 의 최단 표기는 `float_repr_style` 이 `'short'` 인 빌드의 동작이다(문서가 `'legacy'` 값을 남겨 둔다).
* ★ `sum` 결과는 **이 판의 관찰**이다 — 3.11 에서 다르고(8번), 문서도 *"on most builds"*.
* ★ `decimal` 과 `_pydecimal` 이 둘 다 있고 `1/7` 이 같은 글자 — **같은 명세의 두 구현**이다.

### 11. `math.ulp(1e16)` 이 `2.0` — 그 근처에 홀수가 없다 · `2.0 ** 53` 도 간격 `2.0` 이라 `+ 1.0` 이 사라진다 / 글자는 같다(`0.9999999999999999999999999999`) · C# 은 16바이트 고정, 파이썬은 `prec` 을 컨텍스트로 고친다

**출력**

```text
===== python3 - <e50_bits.py =====
[1] stored value of each literal
0.1       ;0x1.999999999999ap-4  ;0.1000000000000000055511151231257827021181583404541015625
0.2       ;0x1.999999999999ap-3  ;0.200000000000000011102230246251565404236316680908203125
0.1 + 0.2 ;0x1.3333333333334p-2  ;0.3000000000000000444089209850062616169452667236328125
0.3       ;0x1.3333333333333p-2  ;0.299999999999999988897769753748434595763683319091796875
[2] the sum against 0.3
s == 0.3                    : False
s == math.nextafter(0.3, 1) : True
(s - 0.3) / math.ulp(0.3)   : 1.0
[3] repr against 17 digits
repr 0.1                   ;.17g 0.10000000000000001   ;float(repr(x)) == x True
repr 0.3                   ;.17g 0.29999999999999999   ;float(repr(x)) == x True
repr 0.30000000000000004   ;.17g 0.30000000000000004   ;float(repr(x)) == x True
[4] spacing near 1e16
math.ulp(1e16) : 2.0
1e16 + 1 == 1e16 : True
1e16 + 2 == 1e16 : False
2.0 ** 53 + 1.0 : 9007199254740992.0 ; + 2.0 : 9007199254740994.0
math.ulp(2.0 ** 53) : 2.0
(exit 0)
```

```text
===== python3 - <e50_context.py =====
[1] prec
prec, rounding : 28 ROUND_HALF_EVEN
1 / 3          : 0.3333333333333333333333333333
1 / 3 * 3      : 0.9999999999999999999999999999
inside prec 50 : 0.33333333333333333333333333333333333333333333333333
after the with : 0.3333333333333333333333333333
[2] flags after 1 / 3
Inexact, Rounded : True True
Inexact after 1 / 4 : False
[3] rounding modes, quantize to '1'
mode;2.5;3.5;-2.5;2.4;2.6
ROUND_HALF_EVEN;2;4;-2;2;3
ROUND_HALF_UP;3;4;-3;2;3
ROUND_HALF_DOWN;2;3;-2;2;3
ROUND_DOWN;2;3;-2;2;2
ROUND_UP;3;4;-3;3;3
ROUND_CEILING;3;4;-2;3;3
ROUND_FLOOR;2;3;-3;2;2
HALF_EVEN vs HALF_UP differ : 2 / 5
[4] traps
traps on : ['DivisionByZero', 'InvalidOperation', 'Overflow']
Decimal(1) / 0 -> DivisionByZero
Decimal(0) / 0 -> InvalidOperation
Decimal('1e30').quantize(Decimal('0.01')) -> InvalidOperation
traps off: 1/0 -> Infinity ; 0/0 -> NaN
(exit 0)
```

**왜 그런가**

* ★★ `1e16 + 1` 의 `1` 은 **눈금 간격(`2.0`)의 절반**이라 동점 → 짝수 가수 쪽(`1e16`)으로 붙는다. `+ 2` 는 한 칸이라 남는다. [47편](../47-json/2-summary.md)의 「`json` 이 잃은 것이 아니다」가 이것이다.
* ★ [데이터 표현](../../../../data-representation/README.md) 2.6 절의 주석은 `2.0 ** 53 + 1.0` 을 `9007199254740993.0` 이라 적는데, 이 머신 출력은 **`9007199254740992.0`** 이다(`[4]`).
* ★★ `[1]` 의 `1 / 3 * 3` 이 [C# 05편](../../../csharp/syntax/05-numeric-types-checked-decimal/2-summary.md)의 `1m / 3m * 3m` 과 같은 28자리 글자다. 차이는 **크기가 고정이냐**다 — C# `decimal` 은 16바이트, 파이썬은 `localcontext` 로 `prec 50` 이 된다(`MAX_PREC` 까지).

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 저장값·ulp | `python3 - <e50_bits.py` | 3(캡처 + 재대조 + `PYTHONHASHSEED` 바꾼 재캡처) | 1 ulp · 간격 `2.0` |
| `round` 격자 | `python3 - <e50_round_grid.py` | 3 | **7 / 11**(동점 4 · 아래 3) · **2 / 11** |
| JS 대조 | `cd e50_js && node e50_tofixed.mjs > js.txt && python3 e50_pair.py js.txt` | 3 | **4 / 11** |
| `Decimal` 생성 | `python3 - <e50_make.py` | 3 | 55자리 · `prec` 은 연산에서만 |
| 컨텍스트 | `python3 - <e50_context.py` | 3 | **2 / 5** · 트랩 셋 |
| 섞기 | `python3 - <e50_mix.py` · `python3 - <e50_mix_throw.py` | 3씩 | `TypeError` · 비교 정확 · `FloatOperation` |
| 금액 | `python3 - <e50_money.py` | 3 | **2 / 4** · `0.03` 대 `0.04` |
| 판 격자 | `python3 - <e50_sum.py` · `python3.11 - <e50_sum_py311.py` | 3씩 | 3.12 `1.0` · 3.11 `0.9999999999999999` |
| 구현 | `python3 - <e50_impl.py` | 3 | C 판 · `libmpdec 2.5.1` |

**구현 의존 항목** — 판이 오르면 다시 돌려야 하는 것.

| 항목 | 왜 |
|---|---|
| ★★ `sum` 판 격자 | 3.12 에서 이미 바뀌었다 — *"on most builds"* |
| 예외 **문구** · `libmpdec` 판 | 구현이다 |
| ★ `float` 이 binary64 인 것 | *"almost all platforms"* — 다른 플랫폼에서는 격자 전체가 달라질 수 있다(못 잰 것) |
| JS 대조 | `node` 판이 오르면 — 규칙은 ECMA-262 가 정하므로 같아야 한다(관찰로만 적는다) |

★ **안 흔들리는 칸** — 격자의 **「7 / 11」·「2 / 11」·「4 / 11」·「2 / 5」·「2 / 4」** · `Decimal(x)` 전 자릿수 · `float.hex()` · 예외 타입 · `(exit N)`.
★★ **이 주제가 한 번도 안 잰 것** — **시간**(부적용) · **IEEE 754 가 아닌 플랫폼 · 32비트 빌드**(못 잰 것).
