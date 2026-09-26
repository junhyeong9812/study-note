# python/syntax/50-decimal-float-precision-and-round — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만(문서 원본 `.rst` 를 받아 문장을 찾았다).
> - [`round()`(3.12)](https://docs.python.org/3.12/library/functions.html#round) — *"if two multiples are equally close, rounding is done toward the even choice"* · note *"`round(2.675, 2)` gives `2.67` instead of the expected `2.68`. This is not a bug: it's a result of the fact that most decimal fractions can't be represented exactly as a float."*
> - [Floating-Point Arithmetic: Issues and Limitations](https://docs.python.org/3.12/tutorial/floatingpoint.html) — *"almost all platforms map Python floats to IEEE 754 binary64 "double precision" values"* · *"Starting with Python 3.1, Python (on most systems) is now able to choose the shortest of these and simply display `0.1`."*
> - [`decimal`(3.12)](https://docs.python.org/3.12/library/decimal.html) — *"The significance of a new Decimal is determined solely by the number of digits input. Context precision and rounding only come into play during arithmetic operations."* ·
>   `FloatOperation` 절 *"mixing floats and Decimals is permitted in the `Decimal` constructor, `create_decimal()` and all comparison operators. Both conversion and comparisons are exact."* · *"Otherwise (the signal is trapped), only equality comparisons and explicit conversions are silent. All other mixed operations raise `FloatOperation`."* ·
>   기본 컨텍스트 *"`Context.prec` = `28`"* · `MAX_PREC` 표(32비트 `425000000` · 64비트 `999999999999999999`)
> - [`sum()`(3.12)](https://docs.python.org/3.12/library/functions.html#sum) — *"Summation of floats switched to an algorithm that gives higher accuracy on most builds."*(3.12) · [What's New 3.12](https://docs.python.org/3.12/whatsnew/3.12.html) — *"`sum()` now uses Neumaier summation to improve accuracy and commutativity when summing floats or mixed ints and floats."*
> - [`sys.float_repr_style`](https://docs.python.org/3.12/library/sys.html#sys.float_repr_style) — *"If the string has value `'short'` then for a finite float `x`, `repr(x)` aims to produce a short string with the property that `float(repr(x)) == x`."*(3.1)
> - [`fractions`](https://docs.python.org/3.12/library/fractions.html) · [`float.hex`](https://docs.python.org/3.12/library/stdtypes.html#float.hex)
>
> **실행 검증** — 이 문서에 실린 출력은 전부 이 머신(Linux x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.\
> 판은 `python3` **3.12.3** 이 본판이고, 판 경계를 위해 `python3.11` **3.11.15** 로 한 블록(`sum`)을 더 던졌다. 교차 갈래 대비로 `node` **v18.19.1** 한 블록.\
> ★★★ **이 문서는 시간을 한 번도 재지 않았다** — 「`Decimal` 은 느리다」·「`float` 이 빠르다」 같은 말은 하지 않는다. 잰 것은 **값이 무엇이 되나**뿐이다.\
> **버전** — `repr` 최단 표기 **3.1** · `Decimal` 과 수 타입의 섞어 비교 전면 지원 **3.2** · `FloatOperation`·C 구현(`_decimal`) **3.3** · `math.ulp`·`math.nextafter` **3.9** · `sum()` 의 Neumaier 합 **3.12**.\
> ★ **구현 대 언어 보장 한 줄** — `round` 의 짝수 쪽 동점 처리와 `Decimal` 의 컨텍스트 규칙이 **라이브러리 보장**이고, **`float` 이 IEEE 754 binary64 인 것은 CPython 이 C `double` 을 쓰는 구현의 사정**(문서가 *"almost all platforms"* 라고 적는다)이다. 이 머신의 `mant_dig 53` 은 관찰이다.\
> ★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다 | 안 흔들린다(근거로 써도 되는 칸) |
> |---|---|
> | 판이 오르면 **예외 문구**(`unsupported operand type(s) for …`) · `libmpdec` 판 번호 · `node --version` | ★★ 격자 마지막 줄 **「… N / M」** · `Decimal(x)` 로 찍은 **저장값 전 자릿수** · `float.hex()` |
> | ★ 판 경계 — **`sum()` 의 결과**(3.11 과 3.12 가 이미 다르다 — 동작 8) | 예외 **타입** · `(exit N)` · `round` 결과 |
> | — (주소·시간·`set` 순서를 한 곳도 안 찍었다. `hash` 는 **같은가만** 찍었다 — 수의 해시는 `PYTHONHASHSEED` 를 안 탄다) | 컨텍스트 기본값(`prec 28`·`ROUND_HALF_EVEN`) |
>
> **선행** — [04-numeric-types-and-division](../04-numeric-types-and-division/2-summary.md)(★★★ **`0.1 + 0.2`·`round` 기본·`Decimal(0.1)`·`Fraction` 첫 만남은 그쪽이 먼저 쟀다** — 동작 5·6 절. 여기는 그 위에 **원인을 가르는 격자 · 컨텍스트 · 섞기 · 금액**을 쌓는다) ·
> [47-json](../47-json/2-summary.md)(★ float 왕복 **7 / 7** — `json` 은 float 을 잃지 않았다).

## 한눈에 — 쉽게 말하면

**`float` 은 「눈금이 2진으로 새겨진 자」이고, `Decimal` 은 「10진 눈금 자」다.**

* 2진 자에는 `0.5`·`0.25`·`0.125` 눈금은 있지만 **`0.1` 눈금이 없다.** 그래서 `0.1` 을 재면 **가장 가까운 눈금**(`0.1000000000000000055…`)에 붙는다.
* 화면에 `0.1` 이라고 보이는 것은 「**이 눈금을 다른 눈금과 헷갈리지 않게 부르는 가장 짧은 이름**」이다. 눈금 자체는 `0.1` 이 아니다.
* `round` 는 **「딱 가운데면 짝수 눈금 쪽으로」** 붙인다. 그런데 **자가 이미 가운데에서 살짝 비껴 있으면** 가운데 규칙은 쓰일 일도 없다.
* 10진 자(`Decimal`)는 `0.1` 눈금이 **있다.** 대신 **자 길이(유효 자릿수 `prec`)와 끝자리 처리법(`rounding`)** 을 **작업대(컨텍스트)** 에 적어 두고 쓴다.

```text
   같은 "2.675" 를 두 자로 잰 뒤 둘째 자리에서 반올림

   2진 자 (float)   2.67499999999999982236…  ← 가운데(2.675)보다 아래에 붙었다
                    round(…, 2) -> 2.67       ★ 가운데 규칙이 아니라 "아래라서" 내림

   10진 자(Decimal) 2.675                     ← 정확히 가운데
                    round(…, 2) -> 2.68       ★ 가운데 규칙: 짝수(8) 쪽
                    HALF_UP      -> 2.68      ★ 학교식: 위로

   ★ 같은 글자 "2.675" 인데 결과가 갈린 것은 반올림 규칙이 아니라 자가 달라서다
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 2진 눈금 자 | `float` — IEEE 754 binary64(이 머신) | `float.hex()` · `Decimal(x)`(동작 1) |
| 가장 가까운 눈금에 붙는다 | 리터럴 → 가장 가까운 `double` | `Decimal(0.1)` 의 55자리 |
| 눈금을 부르는 가장 짧은 이름 | `repr` 최단 표기(3.1+) | `float(repr(x)) == x`(동작 1) |
| 딱 가운데면 짝수 쪽 | `round` 의 짝수 동점 처리 | 격자의 `same` 행(동작 2) |
| 자가 가운데에서 비껴 있다 | **표현 오차** — 저장값이 리터럴의 위/아래 | 격자의 `below`·`above` 행(동작 2) |
| 10진 눈금 자 | `decimal.Decimal` | `Decimal('0.1')`(동작 4) |
| 작업대에 적어 둔 자 길이·끝자리 처리법 | **컨텍스트**의 `prec`·`rounding` | `getcontext()`(동작 5) |
| 두 자를 한 계산에 섞지 못하게 하는 규칙 | `Decimal` + `float` 은 `TypeError` | 동작 6 |

**똑같은 구조다** — 실무에서 물리는 자리도 굳어 있다.\
「**`round(x, 2)` 로 세금을 반올림했는데 1원(센트)씩 모자란다**」·
「**`Decimal(price)` 로 바꿨는데도 끝자리가 `…0000000055` 로 지저분하다**」·
「**100 을 셋으로 나눠 각자 반올림했더니 합이 99.99 다**」가 그것이다.\
첫째는 **저장값이 가운데 아래에 붙은** 것이고, 둘째는 **`float` 을 거쳐 만든** 것이고, 셋째는 **반올림을 나눈 뒤에 따로 한** 것이다.

> **표현 오차(representation error)** — 10진 리터럴을 2진 `float` 에 담을 때 **가장 가까운 눈금으로 바뀌면서 생기는 차이.**\
> 예: `2.675` 는 `2.67499999999999982236…` 로 저장된다.

> **동점(tie)** — 반올림할 값이 두 후보의 **정확히 한가운데**인 경우.\
> 예: `2.5` 는 `2` 와 `3` 의 한가운데 — `round` 는 짝수인 `2` 를 고른다.

### ★★ 이 주제가 쓰는 창 / 부적용인 창

**본체는 ① 「저장값 대 리터럴」 비교 창이다.** `Decimal(float(lit)).compare(Decimal(lit))` 가 **`same`·`below`·`above`** 를 답하고, **그 한 칸이 `round` 의 결과가 동점 규칙 탓인지 표현 오차 탓인지를 가른다**(동작 2 — 스크립트가 센다).

| 창 | 무엇을 말해 주나 | 못 보는 것 |
|---|---|---|
| ① ★★★ **저장값 대 리터럴 비교**(`Decimal(x).compare(Decimal(lit))`) | 리터럴이 **정확히 담겼나 · 위/아래로 비꼈나** | 연산 도중의 오차 누적 |
| ② ★★★ **`Decimal(x)`·`float.hex()` 전 자릿수 창** | 저장값 그 자체(가수·지수 · 십진 전 자릿수) | — |
| ③ ★★ **ulp 창**(`math.ulp`·`math.nextafter`) | 두 값이 **눈금 몇 칸** 떨어졌나 · 1 이 사라지는 자리 | — |
| ④ ★★ **컨텍스트 창**(`flags`·`traps`) | `Decimal` 연산이 **잘랐나(`Inexact`)** · 무엇을 예외로 올리나 | — |
| ⑤ ★ **판 격자**(3.11 대 3.12) | `sum()` 이 판에 따라 **다른 값**을 낸다 | 3.13 이후 |
| ★ **제5의 상태** — 「동점 규칙 탓인가」를 **다른 언어의 다른 동점 규칙**으로 물었다 | JS `toFixed` 는 **같은 `double`** 을 동점에서 **0 에서 먼 쪽**으로 보낸다 — 파이썬과 **갈린 칸이 곧 동점 칸**, 안 갈린 칸이 곧 표현 오차 칸(동작 3) | ★ 그 창은 **「JS 도 같은 `double` 을 쓴다」를 전제**한다 — `toFixed(20)` 으로 저장값이 같음을 같은 블록에서 보였다 |
| ★ **못 잰 것** — IEEE 754 가 아닌 `float` · 32비트 빌드의 `MAX_PREC` | — | 이 머신에 그런 플랫폼이 없다 — 문서 인용만 |
| ★ **부적용** — 시간·속도 | — | 한 번도 재지 않았다 |

★★ **①이 이 주제의 네 번째 창이다.** `round` 의 결과만 보면 `round(2.5)` 의 `2` 와 `round(2.675, 2)` 의 `2.67` 이 **똑같이 「기대보다 작다」** 로 보인다.
**저장값이 리터럴과 같으냐**를 따로 물어야 둘이 **다른 원인**임이 드러난다.

## 이 주제가 답하려는 질문

1. ★★★ **`round` 가 기대와 다른 값을 낼 때 원인은 무엇인가** — 짝수 동점 규칙인가, 저장값이 가운데에서 비낀 표현 오차인가. **한 칸씩 가를 수 있나.**
2. ★★ **`Decimal` 은 무엇을 고쳐 주고 무엇은 못 고치나** — 만드는 법(문자열 대 `float`) · 컨텍스트의 `prec`·`rounding` · `float` 과 섞을 때.
3. ★★ **금액은 무엇으로 계산하나** — 정수 센트 · `Decimal` · `Fraction` 이 같은 문제(합계 · 3등분 · 세금)에서 각각 무엇을 내나.

★ 첫째가 이 주제의 인출 목표다.
**「`round` 는 저장값을 반올림한다 — 저장값이 정확히 가운데일 때만 짝수 규칙이 쓰이고, 아니면 가까운 쪽이다」 한 문장으로 격자의 갈린 칸 7개를 둘로 나눌 수 있는 것**이 아는 것과 들은 것의 경계다.

## 동작 방식

> 이 절이 본문이다. 그림이 먼저 오고 문장이 그 그림을 읽어 준다.
> ★ 04편이 이미 잰 것(`0.1 + 0.2 == 0.3` 이 `False` · `f"{0.1:.20f}"` · `round(0.5)` 가 `0` · `Decimal(0.1)` 55자리 · `Fraction(0.1)`)은 **다시 재지 않고 인용**한다. 여기서 새로 잰 것은 **원인을 가르는 칸**들이다.

### 1. ★★ `0.1 + 0.2` — 저장값을 세 창으로 본다

**언제 쓰나** — 「float 이 부정확하다」를 **얼마나, 어디서**로 바꿔 말해야 할 때.

```text
   2진 눈금 자에서 0.3 근처 — 눈금 간격(ulp) 하나를 확대하면

      0.29999999999999998889…   0.30000000000000004440…
            │                          │
   ─────────┼──────────────────────────┼─────────
            ▲                          ▲
         0.3 을 적으면               0.1 + 0.2 의 결과
         여기에 붙는다               (한 칸 위)

   ★ "0.1 + 0.2 는 0.3 과 다르다" = "바로 옆 눈금이다" — 딱 1 ulp
```

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

그림 해설.

* ★★ **`[1]` 가수가 끝자리에서 갈린다** — `0.3` 은 `0x1.3333333333333p-2`, 합은 `0x1.3333333333334p-2`. **16진 한 자리 차이**다.
  `Decimal(x)` 칸은 그 눈금의 **십진 전 자릿수**다 — `0.3` 은 `0.2999…` 로 **리터럴보다 아래**, 합은 `0.3000…444` 로 **위**.
* ★★★ **`[2]` 합은 `0.3` 의 바로 다음 눈금이다** — `s == math.nextafter(0.3, 1)` 이 `True`, 떨어진 거리가 **`1.0` ulp**. 「오차가 생겼다」의 정확한 크기가 **눈금 한 칸**이다.
* ★★ **`[3]` `repr` 은 최단 표기다** — `0.1` 의 17자리는 `0.10000000000000001` 인데 `repr` 은 `0.1` 이고, **그래도 `float(repr(x)) == x` 가 셋 다 `True`**. 보이는 글자가 짧다고 저장값이 `0.1` 인 것이 아니다(04편·[JS 03편](../../../js/syntax/03-numbers-and-bigint/2-summary.md)이 `toFixed(20)` 으로 같은 것을 보였다).
* ★★ **`[4]` `1e16` 근처는 눈금 간격이 `2.0` 이다** — 그래서 `1e16 + 1` 은 `1e16` 으로 되돌아가고 `+ 2` 는 남는다. [47편](../47-json/2-summary.md)이 「`1e16 + 1` 은 `json` 에 가기 전에 이미 `1e16`」이라고 적은 까닭이 **이 한 줄**이다.
  ★ **`2.0 ** 53 + 1.0` 도 `9007199254740992.0`** 이다 — 거기서도 간격이 이미 `2.0` 이다(동점이라 짝수 가수 쪽으로 붙는다).

**비용** — `float` 의 오차는 **없앨 수 없고 크기만 잴 수 있다.** 비교는 `math.isclose`(04편이 쟀다), 금액은 동작 7 로 간다.

> **ulp(unit in the last place)** — 그 값 근처에서 **바로 옆 `float` 까지의 거리.** 눈금 간격이다.\
> 예: `math.ulp(1e16)` 은 `2.0` — 그 근처에서는 홀수를 담을 수 없다.

### 2. ★★★ `round` 격자 — 동점 규칙과 표현 오차를 가른다

**언제 쓰나** — `round` 가 「틀린」 값을 냈다고 느낄 때마다. **원인이 둘인데 증상이 같다.**

```text
   한 행을 채우는 법

   literal            리터럴 글자 (예: "2.675")
   stored vs literal  Decimal(float(lit)) 를 Decimal(lit) 와 compare
                        same  = 저장값이 리터럴 그 자체   (0.5 · 0.125 처럼 2진으로 딱 떨어짐)
                        below = 저장값이 리터럴보다 아래
                        above = 저장값이 리터럴보다 위
   round(float)       round(float(lit), nd)            ← 파이썬이 실제로 하는 것
   round(Decimal)     round(Decimal(lit), nd)          ← 같은 규칙(짝수)을 10진 자로
   HALF_UP            Decimal(lit).quantize(…, ROUND_HALF_UP)  ← 학교식

   ★ round(float) 과 HALF_UP 이 갈린 칸 → 원인은 stored 칸이 말한다
        same  이면  동점 → 짝수 규칙
        below 이면  가운데보다 아래 → 가까운 쪽(아래)
```

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

그림 해설.

* ★★★ **학교식과 갈린 칸 `7 / 11` — 그중 `same` 이 4, `below` 가 3, `above` 가 0.** 스크립트가 원인을 **센** 것이다.
  - **`same` 넷**(`0.5`·`2.5`·`-2.5`·`0.125`) — 저장값이 리터럴 그 자체라 **진짜 동점**이고, 짝수 쪽으로 갔다. `0.125` 는 `0.12`(2가 짝수).
    문서 — *"if two multiples are equally close, rounding is done toward the even choice"*.
  - **`below` 셋**(`2.675`·`1.005`·`0.285`) — **동점이 아니다.** 저장값이 가운데보다 아래라 **가까운 쪽(아래)** 으로 갔을 뿐이다. 짝수 규칙은 **쓰이지도 않았다.**
    문서 — *"This is not a bug: it's a result of the fact that most decimal fractions can't be represented exactly as a float."*
* ★★★ **`round(float)` 과 `round(Decimal(lit))` 이 갈린 칸 `2 / 11` — 그중 `same` 은 0.** 같은 짝수 규칙을 **10진 자에서** 돌리면 달라지는 칸은 **전부 표현 오차 칸**이다.
  - `2.675` — `float` 은 `2.67`, `Decimal` 은 `2.68`(정확히 가운데 → 짝수 8).
  - ★★ **`2.665` 가 반대 방향이다** — 저장값이 **위**(`above`)라 `float` 은 `2.67`, `Decimal` 은 짝수 규칙으로 **`2.66`**. **표현 오차가 늘 내림 쪽인 것은 아니다.**
* ★ **`0.375` 는 동점인데 학교식과 같다** — 짝수(`8`)가 마침 위쪽이라서다. `1.675` 는 `above` 인데 학교식과 같다 — 위로 비꼈으니 위로 간다.
* ★ `round(float)` 칸은 `Decimal(repr(round(x, nd))).quantize(…)` 로 **자릿수를 맞춰 찍었다**(`1.0` 을 `1.00` 으로) — 값은 `round` 가 낸 그대로다.

**비용** — **「`round` 는 은행가 반올림이라 이상하다」로 외우면 `below` 셋을 설명하지 못한다.** 04편이 `2.675` 한 칸으로 경고한 것을 격자가 **칸 수로** 보인다.

### 3. ★★ 같은 `double` 을 JS `toFixed` 가 반올림하면 — 다른 동점 규칙으로 가른다

**언제 쓰나** — 「동점 규칙 탓」이라는 판정을 **독립적으로** 확인하고 싶을 때. JS 도 같은 IEEE 754 `double` 을 쓰지만 `toFixed` 는 **동점에서 0 에서 먼 쪽**으로 간다([JS 03편](../../../js/syntax/03-numbers-and-bigint/2-summary.md)이 `(-2.5).toFixed(0)` 이 `-3` 인 것까지 이미 쟀다).

```text
   두 언어 · 같은 저장값 · 다른 동점 규칙

                   저장값이 정확히 가운데      저장값이 가운데에서 비낌
   python round    짝수 쪽                     가까운 쪽
   js toFixed      0 에서 먼 쪽                가까운 쪽

   ★ 두 언어가 갈리는 칸 = 동점 칸 (규칙이 다르니까)
   ★ 두 언어가 같은 칸   = 동점이 아닌 칸 (규칙이 쓰이지 않으니까)
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

그림 해설.

* ★★★ **갈린 칸 `4 / 11` — `0.5`·`2.5`·`-2.5`·`0.125`.** 동작 2 의 **`same` 이면서 학교식과 갈린 넷과 한 칸도 다르지 않다.**
  파이썬만 보고 세운 판정(「이 넷은 동점 규칙 탓」)을 **다른 규칙을 가진 언어가 독립적으로** 확인해 준 것이다.
* ★★★ **`2.675`·`1.005`·`0.285` 는 JS 도 `2.67`·`1.00`·`0.28`** — `toFixed(20)` 칸이 **파이썬 `Decimal(x)` 와 같은 저장값**(`2.67499999999999982236`)을 보인다. **표현 오차는 언어를 안 가린다.**
* ★ **`0.375` 는 두 규칙이 같은 답**(`0.38` — 짝수이면서 0 에서 먼 쪽)이라 동점인데도 안 갈렸다. 「안 갈렸다 = 동점 아님」은 **한 방향으로만** 읽는다.
* ★ JS 쪽 소스는 **`toFixed` 한 가지만** 부른다 — `Math.round` 는 음수에서 또 다르게 가고(JS 03편: `Math.round(-2.5)` 가 `-2`), 여기서는 섞지 않았다.

### 4. ★★ `Decimal` 을 만드는 다섯 길 — 정밀도는 연산에서만 쓰인다

**언제 쓰나** — 외부 입력(문자열·`float`·DB 값)을 `Decimal` 로 바꾸는 한 줄을 쓸 때.

```text
   Decimal 로 들어가는 문

   "0.1"  ──────────────────────────▶ Decimal('0.1')        글자 그대로
   0.1 ─────(float 눈금)────────────▶ 0.1000…0555…(55자리)  눈금 그대로 — 오염까지 정확히
   0.1 ─str()─▶ "0.1" ──────────────▶ Decimal('0.1')        최단 이름을 거친다
   0.1+0.2 ─repr()─▶ "0.30000000000000004" ─▶ 그 글자 그대로 ← 이미 오염된 값의 이름

   ★ 컨텍스트 prec 은 이 문을 통과할 때는 안 쓰인다 — 연산(+, *, 단항 +)에서만
```

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

그림 해설.

* ★★ **`[1]` `Decimal(0.1)` 과 `Decimal.from_float(0.1)` 은 같은 55자리**다 — 둘 다 **눈금을 정확히** 옮긴다(04편이 `Decimal(0.1)` 을 쟀다). **`str(0.1)` 을 거치면 `0.1`** — `repr` 최단 이름을 거쳐 들어가기 때문이다.
  ★ 그러나 **이미 오염된 합**(`0.1 + 0.2`)은 `repr` 을 거쳐도 `0.30000000000000004` 다. `str()` 경유는 **「리터럴 하나를 바로 옮길 때」만** 통한다.
* ★★★ **`[2]` `prec = 6` 인데 `Decimal('3.1415926535')` 는 11자리 그대로다.** 문서 — *"The significance of a new Decimal is determined solely by the number of digits input. Context precision and rounding only come into play during arithmetic operations."*
  **`a + 0`·`+a` 에서 비로소 `3.14159`** — 단항 `+` 가 「컨텍스트로 한 번 다듬기」다. 만들 때부터 자르려면 `Context.create_decimal`(`ROUND_DOWN` 으로 `3.1415`).
* ★★ **`[3]` 끝자리 0 이 산다** — `2.50 + 1.50` 은 `4.00`, 곱은 `3.7500`(자릿수가 더해진다). **`Decimal('1.30') == Decimal('1.3')` 은 `True` 인데 `str` 은 다르다** — 값은 같고 **지수(자릿수)가 다르다.** `normalize()` 는 `1.3`·`1E+2`.

**비용** — 끝자리 0 이 사는 것은 **금액 표기에는 이점**(`4.00`)이지만, **`str` 으로 키를 만들면 같은 값이 두 키**가 된다.

### 5. ★★ 컨텍스트 — `prec`·`rounding`·플래그·트랩

**언제 쓰나** — `Decimal` 계산의 **자릿수와 끝자리 처리법**을 정할 때, 그리고 **잘린 것을 알아채야** 할 때.

```text
   컨텍스트 = 스레드(정확히는 contextvar)마다 하나 있는 작업대

   ┌──────────── getcontext() ────────────┐
   │ prec     = 28          (유효 자릿수)  │
   │ rounding = ROUND_HALF_EVEN            │
   │ flags    = { Inexact, Rounded, … }    │ ← 연산이 "무슨 일이 있었나"를 적는다(쌓인다)
   │ traps    = { DivisionByZero,          │ ← 이 신호는 예외로 올린다
   │              InvalidOperation,        │
   │              Overflow }               │
   └───────────────────────────────────────┘
        with localcontext() as lc:   ← 복사본을 잠깐 쓰고 나오면 원래 작업대로
```

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

그림 해설.

* ★★ **`[1]` 기본 `prec 28`** — `1 / 3 * 3` 이 **`0.9999999999999999999999999999`**. 이 28자리 글자는 [C# 05편](../../../csharp/syntax/05-numeric-types-checked-decimal/2-summary.md)의 `1m / 3m * 3m` 과 **한 글자도 같다.**
  ★★ **차이는 자리 수를 고칠 수 있느냐다** — C# `decimal` 은 **16바이트 고정 크기**(그쪽 (7) 절)이고, 파이썬 `Decimal` 은 `localcontext` 안에서 **`prec 50`** 이 바로 되고(50자리), `with` 를 나오면 **28 로 돌아온다.**
* ★★ **`[2]` 플래그가 「잘렸나」를 말한다** — `1 / 3` 뒤 `Inexact`·`Rounded` 가 `True`, `1 / 4` 뒤 `Inexact` 는 `False`. **값만 봐서는 잘린 줄 모른다** — 이 창이 알려 준다.
* ★★★ **`[3]` 반올림 모드 격자 — `HALF_EVEN` 과 `HALF_UP` 이 갈린 칸 `2 / 5`**(`2.5` 와 `-2.5`). `3.5` 는 짝수(4)가 마침 위라 안 갈렸다. `2.4`·`2.6` 은 동점이 아니라 **모든 `HALF_*` 가 같다.**
  ★ `ROUND_UP` 은 「0 에서 먼 쪽」(`-2.5` → `-3`), `ROUND_CEILING` 은 「큰 쪽」(`-2.5` → `-2`)이다 — 이름이 비슷해 헷갈리는 두 칸이 음수 열에서 갈린다.
* ★★ **`[4]` 기본 트랩 셋 — `DivisionByZero`·`InvalidOperation`·`Overflow`.** `1/0` 은 `DivisionByZero`, `0/0` 은 `InvalidOperation`, **자릿수가 `prec` 을 넘는 `quantize` 도 `InvalidOperation`**(`1e30` 을 소수 둘째 자리로 → 33자리). 트랩을 끄면 `Infinity`·`NaN` 이 **조용히** 나온다.

**비용** — 컨텍스트는 **전역처럼 보이는 상태**다. `getcontext().prec = 6` 을 함수 안에서 바꾸면 **같은 스레드의 뒤 코드가 전부** 영향을 받는다(동작 4 의 소스가 끝에서 `28` 로 되돌린 까닭). 바꿀 때는 `localcontext()` 다.

> **컨텍스트(context)** — `Decimal` 연산의 정밀도·반올림·플래그·트랩을 담은 객체. `getcontext()` 가 현재 것을 준다.\
> 예: `getcontext().prec` 은 기본 `28`.

### 6. ★★★ `Decimal` 과 `float` 섞기 — 연산은 막고 비교는 연다

**언제 쓰나** — 기존 `float` 코드에 `Decimal` 을 들여올 때. **어디서 터지고 어디서 조용히 지나가나**가 갈린다.

```text
   섞었을 때 — 기본 컨텍스트(FloatOperation 트랩 꺼짐)

                     Decimal ⊕ float   Decimal ⊕ int   Decimal ⊕ Fraction   Fraction ⊕ float
   + - * /           TypeError         Decimal         TypeError            float (조용히)
   == < >            된다(정확히)       된다            된다                 된다

   ★ "비교가 된다" = 두 값을 정확한 수로 보고 비교한다
      Decimal('0.1') 과 0.1(=0.1000…055) 은 다른 수다
```

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

그림 해설.

* ★★★ **`[1]` 연산은 `Decimal` + `float` 과 `Decimal` + `Fraction` 둘 다 `TypeError`** — 그런데 **`Fraction` + `float` 은 조용히 `float` 이 된다**(`0.2`). 정확한 타입이 **부정확한 쪽으로 끌려 내려가는** 자리는 `Fraction` 쪽이다.
* ★★★ **`[2]` 비교는 된다 — 그리고 정확하다.** `Decimal('0.1') == 0.1` 은 **`False`**, `Decimal(0.1) == 0.1` 은 **`True`**, `Decimal('0.1') < 0.1` 은 **`True`**(`0.1` 의 눈금이 위라서). `0.5` 는 2진으로 딱 떨어져 `True`.
  문서 — *"Both conversion and comparisons are exact."* · `Fraction(1, 10) == 0.1` 도 `False` 다 — 같은 원리다.
  ★ 그리고 **비교만으로 `FloatOperation` 플래그가 켜졌다**(`True`) — 트랩이 꺼져 있어 **예외 없이 기록만** 됐다.
* ★★ **`[3]` 트랩을 켜면 `==` 는 조용하고 `<` 는 `FloatOperation`** — 문서 — *"only equality comparisons and explicit conversions are silent"*. **`Decimal(0.1)` 생성자도 막히고 `from_float` 은 통과한다** — 「명시적 변환」은 `from_float` 쪽이다.
* ★★ **`[4]` 해시가 수 값을 따른다** — `hash(Decimal('0.5')) == hash(0.5)` 가 `True`. 그래서 **`Decimal('0.1') in {0.1}` 은 `False`**(다른 수), `Decimal(0.1) in {0.1}` 은 `True`. `set`·`dict` 키에 두 타입을 섞으면 **비교 규칙 그대로** 갈린다([12편](../12-dict-and-key-requirements/2-summary.md)의 키 요건).

같은 섞기를 **예외째 끝까지** 던지면 이렇다 — 트레이스백은 `decimal` 이 C 모듈이라 **표준 라이브러리 경로가 안 박힌다.**

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

* ★ 4행 — `Decimal('19.99') * 1.1`. **곱셈 하나**가 `TypeError`. 실무에서는 `1.1` 이 설정 파일·`float` 필드에서 오는 일이 많다 — **그 경계에서 `Decimal(str(x))` 로 바꾼다**(동작 4 의 `[1]`).

### 7. ★★★ 금액 — 정수 센트 · `Decimal` · `Fraction`

**언제 쓰나** — 돈. 세 가지 문제(합계 · 나누기 · 세금 반올림)를 **같은 입력으로 네 방식**에 돌려 무엇이 **입력 총액을 지키나** 본다.

```text
   100.00 을 셋이 나눈다

   각자 반올림        33.33  33.33  33.33   합 99.99   ★ 0.01 이 증발
   (float·Decimal)

   정수 센트 divmod   3334   3333   3333    합 10000   ★ 나머지 1센트를 누군가에게
                     └ divmod(10000, 3) = (3333, 1)

   Fraction          100/3  100/3  100/3   합 100     ★ 정확하지만 — 지급은 센트로 해야 한다
                                                         (10000/3 센트는 못 준다)
```

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

그림 해설.

* ★★ **`[1]` 열 번 더하기 — `+=` 루프만 `0.9999999999999999`.** 그런데 **`sum()` 은 `1.0`** 이다 — ★★★ 3.12 에서 `sum` 의 알고리즘이 바뀌었다(동작 8). **「`float` 을 더하면 틀린다」도 판에 따라 결과가 다르다.** 센트·`Decimal`·`Fraction` 은 판과 무관하게 정확하다.
* ★★★ **`[2]` 3등분 — 입력 총액과 같은 방식 `2 / 4`.** `float` 과 `Decimal` 이 **똑같이 `99.99`** 로 틀렸다. ★ **`Decimal` 이 이 문제를 못 푼 것은 정밀도 탓이 아니다** — **몫을 반올림한 뒤 합을 다시 만든** 절차 탓이다.
  정수 센트는 `divmod` 로 **나머지를 명시적으로 배정**해서 맞췄다(`3334, 3333, 3333`). `Fraction` 은 합은 맞지만 **`10000/3` 센트**라 그대로는 못 준다 — 결국 배정 규칙이 필요하다.
* ★★ **`[3]` 세금 5% × `0.70` — 정확한 곱은 `0.0350`(동점)인데 `float` 은 `0.03`.** 저장된 곱이 `0.034999…` 로 **아래**라서다(동작 2 의 `below` 와 같은 원인). `Decimal` `HALF_UP` 과 정수 센트(`(70 * 5 + 50) // 100`)는 `0.04`·`4`.
  ★ 정수 센트 식은 **양수일 때만** `HALF_UP` 이다 — 음수(환불)에서는 `//` 가 아래로 내림(04편)이라 규칙을 따로 적어야 한다.

**비용** — 정수 센트는 **곱셈·비율 계산마다 반올림 규칙을 손으로** 써야 한다. `Decimal` 은 그 규칙을 `rounding=` 으로 적지만 **배정(나머지 몫)은 대신 안 해 준다.** 어느 쪽이든 **「언제 반올림하나」가 설계 결정**이다.

### 8. ★ 판 경계 — 3.12 의 `sum()` 이 바뀌었다

**언제 쓰나** — `float` 을 `sum()` 으로 더한 결과를 **테스트의 기대값**으로 박을 때. 판을 올리면 기대값이 바뀐다.

```text
   같은 소스, 두 판

                        3.11                   3.12
   loop +=              0.9999999999999999     0.9999999999999999   (루프는 안 바뀜)
   sum(xs)              0.9999999999999999     1.0                  ★ 바뀜
   sum(ys) / reversed   0.1 / 0.0              0.2 / 0.2            ★ 순서 의존이 사라짐
   math.fsum            1.0 · 0.2              1.0 · 0.2            (원래 정확)
```

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

그림 해설.

* ★★★ **3.11 의 `sum(ys)` 는 `0.1`, 거꾸로 더하면 `0.0`** — `1e100` 이 `0.1` 을 **삼켰다가 뱉은** 순서에 따라 달라진다. **3.12 는 둘 다 `0.2`** — What's New 3.12 의 *"improve accuracy and commutativity"* 가 이 칸이다.
* ★★ **`+=` 루프는 두 판 모두 `0.9999999999999999`** — 바뀐 것은 **`sum` 이라는 함수**지 `float` 덧셈이 아니다.
* ★ 문서의 `sum` 절은 *"on most builds"* 라고 적는다 — **빌드에 달린 구현**이다(라이브러리 보장이 아니다).
* ★ 소스는 두 판에서 **한 글자도 같다**(`e50_sum.py` 와 `e50_sum_py311.py` — 캡처가 판을 파일명으로 고른다).

> **Neumaier 합(Neumaier summation)** — 더하면서 **잃은 끝자리를 따로 모아** 마지막에 돌려주는 보정 합. 3.12 `sum()` 이 `float` 에 쓴다.\
> 예: `sum([0.1] * 10)` 이 3.12 에서 `1.0`.

## 문법 — 형태와 규칙

```text
   round(x)            -> int        (동점은 짝수)
   round(x, nd)        -> x 와 같은 타입 (float 이면 float, Decimal 이면 Decimal)
   Decimal("1.23")     글자 그대로 · Decimal(1.23) 은 float 눈금 그대로
   d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)   자릿수 고정 + 규칙 명시
   with localcontext() as ctx: ctx.prec = 50              잠깐만 바꾸기
   Fraction(1, 3) · Fraction("0.1")                       유리수 — 분모가 커진다
   math.isclose(a, b) · math.ulp(x) · math.nextafter(x, y) · math.fsum(xs)
```

* ★★ **`round` 는 `__round__` 에 위임한다** — `Decimal` 에 `round(d, 2)` 를 부르면 **`Decimal` 의 컨텍스트 반올림**(기본 짝수)으로 **`Decimal` 을 돌려준다**(동작 2 의 `round(Decimal)` 열).
* ★ **`Decimal` 은 문자열로 만든다** — `float` 이 들어오는 경계에서는 `Decimal(str(x))`(리터럴 하나일 때만 통한다 — 동작 4).
* ★ **`quantize` 의 인자는 「자릿수 견본」이다** — `Decimal("0.01")` 은 「소수 둘째 자리」, `Decimal("1")` 은 「정수」.
* ★ **`Decimal` + `int` 는 되고 `Decimal` + `float` 은 `TypeError`** — 비교는 둘 다 된다(동작 6).

## 어디서 틀리나

### (1) ★★★ `round(2.675, 2)` 와 `round(2.5)` 를 같은 원인으로 설명한다

「둘 다 은행가 반올림 탓」은 **절반만 맞다.** 격자에서 학교식과 갈린 7칸 중 **4칸만 동점**이고 3칸은 **저장값이 아래**라서다(동작 2). JS `toFixed` 가 **동점 4칸에서만** 갈린 것이 독립 확인이다(동작 3).

### (2) ★★★ 「표현 오차는 늘 내림 쪽으로 나온다」

`2.665` 는 저장값이 **위**라 `round` 가 `2.67` 을 냈다 — `Decimal` 의 짝수 규칙이면 `2.66` 이다(동작 2). 방향은 **리터럴마다 다르다.**

### (3) ★★ `Decimal(x)` 로 `float` 을 고친다

`Decimal(0.1)` 은 **눈금을 정확히** 옮길 뿐이다(04편 · 동작 4). 고치려면 **글자로** 들어가야 한다 — 그리고 `str()` 경유도 **이미 연산을 거친 값**(`0.1 + 0.2`)은 못 살린다.

### (4) ★★ `getcontext().prec = 6` 이면 `Decimal('3.1415926535')` 가 6자리가 된다

**안 된다** — 만들 때는 글자 수 그대로다. 연산·단항 `+`·`create_decimal` 에서만 `prec` 이 쓰인다(동작 4 의 `[2]`).

### (5) ★★★ `Decimal('0.1') == 0.1` 이 `True` 일 거라 믿는다

**`False`** 다 — 비교는 **정확한 수끼리**다(동작 6). 반대로 `Decimal(0.1) == 0.1` 은 `True`. 그리고 `set`·`dict` 키에서도 같은 규칙이다.

### (6) ★★ 「`Decimal` 을 쓰면 3등분도 맞는다」

**`99.99`** 로 `float` 과 똑같이 틀렸다(동작 7 의 `[2]`). 문제는 정밀도가 아니라 **몫을 반올림한 뒤 합을 다시 만든 절차**다. 나머지를 **배정**해야 한다.

### (7) ★★ `sum()` 결과를 테스트 기대값으로 박는다

3.11 과 3.12 가 **다른 값**을 낸다(동작 8). 기대값은 `math.isclose` 로, 또는 합 자체를 `math.fsum`·정수로.

### (8) ★ `ROUND_UP` 을 「학교식 반올림」으로 안다

`ROUND_UP` 은 **「0 에서 먼 쪽으로 올림」** 이라 `2.4` 도 `3` 이다(동작 5 의 `[3]`). 학교식은 **`ROUND_HALF_UP`**.

### (9) ★ 함수 안에서 `getcontext()` 를 바꾸고 안 되돌린다

같은 스레드의 **뒤 코드 전부**가 그 `prec`·`rounding` 으로 돈다. `localcontext()` 를 쓴다(동작 5).

## 구현 세부사항 대 언어 보장

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **라이브러리 보장** | `round`·`decimal`·`fractions`·`sum` 문서가 정한 것 | 문서 문장을 열어서 인용 |
| **CPython 구현** | `float` = C `double`(IEEE 754 binary64) · C `_decimal`(libmpdec) · `repr` 최단 표기 방식 · `sum` 의 보정 합 | 실행 + `sys`·`decimal` 상수 |
| **이 판(3.12.3 · 3.11.15)·이 머신의 관찰** | 이 판·이 빌드에서 그랬을 뿐 | 출력 |
| ★ **못 잰 것** | IEEE 754 가 아닌 `float` · 32비트 `MAX_PREC` | 플랫폼이 없다 |
| ★ **부적용** | 시간·속도 | 재지 않았다 |

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

* ★★ **`decimal` 은 C 판이다** — `decimal.Decimal is not _pydecimal.Decimal` 이 `True`, `libmpdec 2.5.1`. **순수 파이썬 판(`_pydecimal`)도 같은 표준 라이브러리에 있고 `1/7` 이 같은 글자**다 — 두 구현이 **같은 명세**(General Decimal Arithmetic)를 따른다.
* ★ **`MAX_PREC` 이 `999999999999999999`** — 문서 표의 **64비트** 값이다(32비트는 `425000000` — 못 잰 것).
* ★ `float_repr_style` 이 **`short`** — 3.1 이후의 **보통 동작**이지만, 문서가 `'legacy'` 값의 존재를 적는 만큼 **플랫폼에 달린 구현**이다.

### 라이브러리 보장

| 사실 | 근거 |
|---|---|
| `round` 는 동점을 **짝수 쪽**으로 · `ndigits` 가 없으면 `int` · 있으면 **같은 타입** | `round()` |
| `round(2.675, 2)` 가 `2.67` 인 것은 **버그가 아니라 float 표현의 결과** | `round()` note |
| `Decimal` 은 **입력 자릿수 그대로** 만들어지고 `prec`·`rounding` 은 **연산에서만** | `decimal` — *"The significance of a new Decimal…"* |
| 기본 컨텍스트 `prec 28`·`ROUND_HALF_EVEN` · 기본 트랩 `DivisionByZero`·`InvalidOperation`·`Overflow` | `decimal` — 컨텍스트 절 |
| `Decimal` 과 `float` 의 **생성자·비교는 허용되고 정확하다** · 트랩을 켜면 **`==` 와 명시 변환만** 조용하다 | `FloatOperation` 절 |
| 수 타입 사이의 섞어 비교 전면 지원(3.2) | `decimal` — versionchanged 3.2 |
| `repr` 은 `float(repr(x)) == x` 인 **짧은 문자열을 목표**로 한다(`'short'` 일 때) | `sys.float_repr_style` |

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| ★★★ **`float` 이 IEEE 754 binary64** — 문서의 말로 *"almost all platforms map Python floats to IEEE 754 binary64"* | `mant_dig 53`·`radix 2`(이 절 첫 블록 · 04편도 쟀다) |
| `decimal` 이 C 판(`_decimal`, libmpdec) | `decimal.Decimal is not _pydecimal.Decimal` |
| `sum()` 의 `float` 보정 합(3.12) — 문서가 *"on most builds"* | 3.11 대 3.12 판 격자(동작 8) |
| 예외 **문구** 전부 — `unsupported operand type(s) for +: 'decimal.Decimal' and 'float'` | 실행 |
| JS 쪽 — 같은 binary64 저장값 · `toFixed` 의 동점 규칙은 JS 03편이 정본 | `toFixed(20)` 칸(동작 3) |

### 이 판(3.12.3)의 관찰

- **격자의 11행 값 전부** — 저장값의 위/아래는 binary64 에서 **정해진 것**이지만, 이 문서가 확인한 것은 이 머신의 출력이다.
- **`sum([0.1] * 10)` 이 `1.0`** — 3.11.15 에서는 `0.9999999999999999`(동작 8).
- **`libmpdec 2.5.1`·`node v18.19.1`** — 판 번호.
- ★ 이웃 문서와 어긋나는 관찰이 하나 있다 — [데이터 표현](../../../../data-representation/README.md) 2.6 절의 주석은 `2.0 ** 53 + 1.0` 을 `9007199254740993.0` 이라 적는데, **이 머신 출력은 `9007199254740992.0`** 이다(동작 1 의 `[4]` — 간격이 이미 `2.0`). 그 주석은 그 문서의 몫이라 이 문서는 **출력만** 적는다.

### 그래서 이렇게 적으면 틀린다

* ✗ 「파이썬 `float` 은 IEEE 754 배정밀도다(언어 보장)」\
  ○ **CPython 이 C `double` 을 쓰는 구현의 사정**이다 — 문서가 *"almost all platforms"* 라고 한정한다.
* ✗ 「`round(2.675, 2)` 는 은행가 반올림 때문에 `2.67`」\
  ○ **동점이 아니다** — 저장값이 아래다(`below`). 짝수 규칙은 **`same` 행에서만** 쓰였다.
* ✗ 「`Decimal` 을 쓰면 반올림 문제가 사라진다」\
  ○ **3등분 합은 `99.99` 로 똑같이 틀렸다.** `Decimal` 은 **표현 오차**를 없애지 **절차**를 고치지 않는다.
* ✗ 「`float` 열 개를 더하면 `0.9999999999999999`」\
  ○ **`sum()` 은 3.12 에서 `1.0`** 이다. `+=` 루프는 그대로다.
* ✗ 「`Decimal` 이 더 느리다」\
  ○ **시간은 재지 않았다.** 이 문서가 잰 것은 **값**이다.

## 언제 쓰고 언제 안 쓰나

```text
   무엇을 계산하나?
      │
      ├─ 측정값·과학 계산 · 오차를 허용 ─────────▶ float  (+ math.isclose · math.fsum)
      │
      ├─ 돈 ─┬─ 더하기·빼기·센트 단위로 끝남 ──────▶ 정수 센트 (int) — 나누기는 divmod 로 배정
      │      └─ 비율·세율·환율·자릿수 규칙이 있음 ─▶ Decimal (문자열로 만들고 quantize + rounding 명시)
      │
      └─ 1/3 같은 비율을 끝까지 정확히 ───────────▶ Fraction — 마지막에 한 번 반올림
```

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 금액 합계·차감 | 정수 센트 | 연산이 전부 정확 · 판과 무관(동작 7) |
| 세금·이자·환율(자릿수와 반올림 규칙이 규정에 있다) | `Decimal` + `quantize(…, rounding=…)` | 규칙을 코드에 **적을 수** 있다 |
| 나누어 떨어지지 않는 배분 | 정수 센트 + `divmod` 로 **나머지 배정** | 반올림만으로는 합이 안 맞는다(`2 / 4`) |
| 비율을 끝까지 정확히 유지 | `Fraction` | 분모가 커지는 대가 · 지급 전 반올림은 따로 |
| 외부에서 `float` 이 들어온다 | 경계에서 `Decimal(str(x))` | 리터럴 하나일 때만 깨끗하다 |
| `float` 끼리 같은가 | `math.isclose` | `==` 는 1 ulp 에 진다(동작 1) |
| `float` 을 많이 더한다 | `math.fsum`(판 무관) | `sum` 은 판에 따라 결과가 다르다(동작 8) |
| 표시용 반올림 | f-string `:.2f` | ★ 이것도 **저장값**을 반올림한다 — 원인은 동작 2 와 같다 |

## 핵심 문장

1. **`round` 는 저장값을 반올림한다** — 학교식과 갈린 칸 **7 / 11** 중 **동점 4 · 저장값이 아래 3**. 짝수 규칙은 **저장값이 정확히 가운데일 때만** 쓰인다.
2. **같은 `double` 을 JS `toFixed` 로 돌리면 동점 4칸에서만 갈린다(4 / 11)** — 표현 오차는 언어를 안 가린다.
3. **`Decimal` 은 문자열로 만든다** — `Decimal(0.1)` 은 눈금 55자리. `prec` 은 **만들 때가 아니라 연산에서** 쓰인다.
4. **`Decimal` 과 `float` 은 연산이 `TypeError`, 비교는 정확하다** — `Decimal('0.1') == 0.1` 은 `False`.
5. **돈은 정수 센트 또는 `Decimal` — 그러나 3등분은 둘 다 배정이 필요하다**(`99.99` · 맞은 방식 **2 / 4**). 3.12 의 `sum()` 은 `float` 합도 바꿨다.

## 관련 자료

* 목록: [python/syntax 주제 목록](../README.md) — 이 주제는 **50번**
* 선행: [04-numeric-types-and-division](../04-numeric-types-and-division/2-summary.md) — ★★★ **경계**: `float` 이 이진 분수라는 것 · `0.1 + 0.2` · `round` 기본 · `Decimal(0.1)` · `Fraction` · `isclose` 첫 측정은 그쪽(동작 5·6 절). 여기는 **원인을 가르는 격자 · 컨텍스트 · 섞기 · 금액**부터.
* 정본 경계: [데이터 표현 — 진수·부동소수점·문자 인코딩](../../../../data-representation/README.md) — ★★ **경계**: 부동소수점의 **비트 배치**(2 절 — 2.2 `sys.float_info` · 2.4 엡실론 · 2.5 `0.1 + 0.2 != 0.3` · 2.6 2^53 · 2.7 비트 분해와 엔디안)는 그쪽이 정본. 여기는 **파이썬 코드에서 그것을 어떻게 다루나**(`round`·`Decimal`·금액)부터. ★ 2.6 절 주석과 이 머신 출력이 다른 칸 하나는 「이 판의 관찰」 절에 적었다.
* 함께 보는 곳: [47-json](../47-json/2-summary.md) — float 왕복 **7 / 7**, `1e16 + 1` 이 이미 `1e16`(여기 동작 1 의 `[4]` 가 그 까닭 — 간격 `2.0`). `Decimal` 을 JSON 으로 내보내는 `default=` 는 그쪽.
* 함께 보는 곳: [12-dict-and-key-requirements](../12-dict-and-key-requirements/2-summary.md) — 해시·동등 요건. 동작 6 의 `[4]` 가 수 타입을 섞은 키의 사례다.
* 다른 갈래: [C# 05 — 숫자 타입·`checked`·`decimal`](../../../csharp/syntax/05-numeric-types-checked-decimal/2-summary.md) — C# `decimal` 은 **16바이트 고정 크기의 10진 부동소수**(그쪽 (6)·(7) 절). 파이썬 `Decimal` 은 **자릿수를 컨텍스트로 고친다**(`MAX_PREC` 까지). 기본 28자리의 `1/3*3` 글자는 두 언어가 같다.
* 다른 갈래: [JS 03 — 숫자와 BigInt](../../../js/syntax/03-numbers-and-bigint/2-summary.md) — JS 도 같은 binary64 · `toFixed` 와 `Math.round` 의 동점 규칙은 그쪽이 정본. 여기 동작 3 은 **같은 격자 11행**을 `toFixed` 로 돌려 파이썬과 대조한 것이다.
* 공식 문서: [`round()`](https://docs.python.org/3.12/library/functions.html#round) · [Floating-Point Arithmetic](https://docs.python.org/3.12/tutorial/floatingpoint.html) · [`decimal`](https://docs.python.org/3.12/library/decimal.html) · [`fractions`](https://docs.python.org/3.12/library/fractions.html) · [`sum()`](https://docs.python.org/3.12/library/functions.html#sum) · [What's New 3.12](https://docs.python.org/3.12/whatsnew/3.12.html)

## 용어 풀이

* **IEEE 754 binary64(배정밀도)**: 가수 53비트 · 지수 11비트의 2진 부동소수 형식. CPython `float` 이 거의 모든 플랫폼에서 이것이다.\
  예: `sys.float_info.mant_dig` 가 `53`.
* **표현 오차(representation error)**: 10진 리터럴이 가장 가까운 2진 눈금으로 바뀌며 생기는 차이.\
  예: `2.675` → `2.67499999999999982236…`.
* **ulp**: 그 값 근처의 눈금 간격.\
  예: `0.1 + 0.2` 는 `0.3` 에서 **1 ulp** 위.
* **최단 표기(shortest repr)**: `float(repr(x)) == x` 를 지키는 가장 짧은 십진 글자(3.1+).\
  예: 저장값이 `0.1000…055` 인데 `repr` 은 `0.1`.
* **동점 / 짝수 쪽 반올림(round half to even)**: 정확히 가운데면 짝수 후보로. `round` 와 `Decimal` 의 기본.\
  예: `round(2.5)` 는 `2`, `round(0.125, 2)` 는 `0.12`.
* **`ROUND_HALF_UP`**: 정확히 가운데면 0 에서 먼 쪽으로(학교식).\
  예: `Decimal('2.5').quantize(Decimal('1'), rounding=ROUND_HALF_UP)` 는 `3`.
* **`Decimal`**: 10진 부동소수. 자릿수와 반올림은 컨텍스트가 정한다.\
  예: `Decimal('0.1') + Decimal('0.2')` 는 `0.3`.
* **컨텍스트(context)**: `Decimal` 연산의 `prec`·`rounding`·`flags`·`traps`.\
  예: `localcontext()` 로 잠깐 `prec = 50`.
* **`quantize`**: 지수(소수 자릿수)를 견본에 맞추는 반올림.\
  예: `Decimal('0.0350').quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)` 는 `0.04`.
* **플래그 / 트랩(flag / trap)**: 연산이 일으킨 신호를 **기록만** 하나 / **예외로 올리나**.\
  예: `1/3` 뒤 `Inexact` 플래그 · `1/0` 은 `DivisionByZero` 트랩.
* **`FloatOperation`**: `Decimal` 과 `float` 을 섞은 것을 알리는 신호(3.3+). 기본은 기록만.\
  예: 트랩을 켜면 `Decimal('0.1') < 0.1` 이 예외.
* **`Fraction`**: 분자·분모 정수로 된 유리수. 사칙연산이 정확하다.\
  예: `Fraction(1, 3) * 3 == 1`.
* **정수 센트(integer cents)**: 금액을 최소 단위의 정수로 담는 관용.\
  예: `100.00` 을 `10000` 으로.
* **Neumaier 합**: 잃은 끝자리를 따로 모아 돌려주는 보정 합. 3.12 `sum()`.\
  예: 3.12 에서 `sum([0.1] * 10)` 이 `1.0`.

## 더 들어가면

* ★ **`Decimal` 은 General Decimal Arithmetic 명세를 따른다** — 문서 첫머리가 그 명세와 IEEE 854 를 가리킨다. `_pydecimal` 과 C 판이 같은 답을 낸 것(`1/7`)이 그 한 조각이다.
* ★ **스레드와 코루틴의 컨텍스트** — `HAVE_CONTEXTVAR` 가 `True`(구현 절 블록)이고, 문서는 그 값이 `False` 인 빌드에서만 *"the C version uses a thread-local rather than a coroutine-local context"* 라고 적는다 — 이 빌드의 `Decimal` 컨텍스트는 **코루틴 단위**라는 뜻이다. 코루틴 사이에서 실제로 어떻게 갈리는지는 이 문서가 재지 않았다([51](../51-asyncio-coroutine-basics/2-summary.md)·[52](../52-asyncio-concurrency-structure/2-summary.md)가 코루틴의 무대다).
* ★ **배정 알고리즘** — 3등분의 나머지 1센트를 **누구에게** 주나(첫째 · 큰 몫 · 무작위)는 회계 규정의 몫이다. 동작 7 은 「첫째부터」 하나만 보였다.
* ★ **`numpy`·DB 의 `NUMERIC`** — 이 문서의 창 밖이다. DB 의 `NUMERIC(p, s)` 는 `Decimal` 로 오고 가는 것이 드라이버의 관용이다.
* ★ **32비트 빌드에서 다시 돌릴 것** — `MAX_PREC` 이 `425000000` 이 될 것이라는 말은 **문서 표의 말**이다(이 머신은 64비트 — 못 잰 것).
