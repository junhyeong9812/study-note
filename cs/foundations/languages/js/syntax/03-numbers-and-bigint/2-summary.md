# js/syntax/03 — 숫자와 `BigInt`: 「수 타입이 하나뿐이라는 것」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262 최신 초안](https://tc39.es/ecma262/) — Number 타입(IEEE 754 배정밀도)·BigInt 타입·`toFixed`·`Math.round` 의 규정
> - [ECMA-262 판별 아카이브](https://262.ecma-international.org/) — `BigInt` 가 들어온 판(ES2020)을 가릴 때
> - [MDN — `Number`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Number) · [MDN — `BigInt`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/BigInt)
>
> ★★★ **명세 조항 번호는 인용하지 않는다.** 규칙 진술은 위 문서로, **값·예외 타입과 메시지는 전부 실행으로** 접지했다.
>
> **실행 검증** — 이 문서의 모든 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다.
> 배너의 `node20` 은 `~/.nvm/versions/node/v20.19.6/bin/node`, `node18` 은 기본 PATH 의 `node`(v18.19.1)다.
> **어느 판에서 나왔는지는 아래 첫 블록**에 있다.

```sh
// js01b-versions.sh
#!/usr/bin/env bash
# 이 문서의 모든 출력이 어느 판에서 나왔는지 — 첫 블록에 싣는다.
set -u -o pipefail
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
for n in "$N18" "$N20"; do
  "$n" -e 'const v = process.versions;
    console.log("node " + v.node + "  v8 " + v.v8 + "  icu " + v.icu + "  unicode " + v.unicode +
                "  Intl.Segmenter " + typeof Intl.Segmenter +
                "  isWellFormed " + typeof String.prototype.isWellFormed);'
done
google-chrome --version 2>/dev/null
```

```text
===== ./js01b-versions.sh (exit=0) =====
node 18.19.1  v8 10.2.154.26-node.28  icu 74.2  unicode 15.1  Intl.Segmenter function  isWellFormed undefined
node 20.19.6  v8 11.3.244.8-node.33  icu 77.1  unicode 16.0  Intl.Segmenter function  isWellFormed function
Google Chrome 151.0.7922.173 
```

> ★★ **던지는 형태를 하나로 고정했다** — 예외는 `try`/`catch` 로 받아 **`e.constructor.name` 과 `e.message` 만** 찍는다.
> Node 의 스택트레이스에는 **절대 경로**가 박히기 때문이다. 이 주제의 블록은 전부 표준 출력이다.
> ★★ **저장된 값을 볼 때는 `toFixed(20)`** 을 쓴다 — `console.log` 가 보여 주는 것은 **가장 짧은 표기**이지 저장된 값이 아니다.
>
> **버전** — `Number` 는 초판부터. **`BigInt` 는 ES2020**, `Number.isInteger`·`isSafeInteger`·`EPSILON`·`MAX_SAFE_INTEGER` 는 **ES2015** 다.
> `**`(거듭제곱)은 ES2016 이고 `BigInt` 에도 쓸 수 있다.
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | Node 스택트레이스의 **절대 경로** — 한 줄도 싣지 않았다 | **모든 수치** — IEEE 754 배정밀도는 비트까지 정해져 있다 |
> | 예외 **문구**(판이 오르면 바뀐다) | **예외의 타입** — `TypeError`·`RangeError`·`SyntaxError` |
> | `console.log(-0)` 이 `-0` 으로 보이는 것 — **Node 의 표시 규칙**이다 | **`String(-0)` 이 `"0"` 인 것** — 이쪽이 명세다 |
> | 브라우저 UA 문자열의 뒷자리 | `toFixed`·`Math.round` 의 반올림 방향 · 32비트 절단 결과 · 종료 코드 |
>
> ★★★ **이 주제는 수치가 본체인데 그 수치가 전부 안 흔들린다.** 부동소수점 연산이 **비트 단위로 규정**돼 있기 때문이다.
> 「측정」이 아니라 「계산」이라 머신·부하와 무관하다 — 그래서 이 문서에는 **시간도 반복 횟수도 안 나온다.**
>
> **선행** — [01 — 값의 종류와 `typeof`](../01-value-types-and-typeof/2-summary.md)(`"number"` 와 `"bigint"` 두 칸) ·
> [02 — 강제 변환과 `==` 대 `===`](../02-coercion-and-loose-equality/2-summary.md)(**`0n == 0` 이 참인 이유**·`Object.is`)
> **이어지는 곳** — [04 — 문자열과 UTF-16](../04-strings-and-utf16/2-summary.md)
>
> ★★ **경계 — 부동소수점의 원리는 여기가 아니다.** [`cs/foundations/data-representation/`](../../../../data-representation/)가
> 「부호·지수·가수가 비트에 어떻게 앉나」의 정본이다. **여기는 「JS 에 수 타입이 둘뿐이고 하나가 double 이라는 것이 코드에서 무엇을 만드나」부터다.**

## 한눈에 — 쉽게 말하면

**JS 의 숫자는 오랫동안 하나뿐이었고, 그 하나가 「자가 굵은 줄자」다.**

줄자에 눈금이 있다. 0 근처에서는 눈금이 촘촘하고, 멀리 갈수록 성기다.
그래서 **잴 수 있는 값이 정해져 있고**, 그 사이의 값은 **가장 가까운 눈금으로 끌려간다.**

- `0.1` 은 **눈금 위에 없다.** 가장 가까운 눈금이 `0.1000000000000000055…` 이고 그것이 저장된다.
- 아주 먼 곳(`2**53` 너머)에서는 **눈금 간격이 1보다 커져서** 정수 두 개가 한 눈금에 얹힌다.
- 그래서 **`9007199254740992 + 1` 이 자기 자신**이다.

```text
   0 근처                              2**53 근처

   |·|·|·|·|·|·|·|·|·|·|·|            |     |     |     |
    촘촘하다. 정수는 전부 눈금 위        눈금 간격이 2 다.
    0.1 은 눈금 사이 -> 끌려간다         홀수는 눈금 위에 없다

   ★ 0.1 + 0.2 != 0.3  은 "버그" 가 아니라
     세 수가 전부 눈금에 끌려간 결과다.

   ★ BigInt 는 줄자가 아니라 "자릿수를 늘려 가며 적는 종이" 다.
     느리지만 눈금이 없다.
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 눈금이 있는 줄자 | IEEE 754 배정밀도(double) | `(0.1).toFixed(20)` 이 `0.1` 이 아니다 |
| 가장 가까운 눈금으로 끌려간다 | 반올림(round to nearest) | `0.1 + 0.2` 가 `0.30000000000000004` |
| 눈금 간격이 1 을 넘는 지점 | `2**53` (안전 정수 한계) | `2**53 === 2**53 + 1` 이 참 |
| 화면에 보이는 짧은 숫자 | 「가장 짧은 표기」 | `toFixed(20)` 으로 걷어 낸다 |
| 자릿수를 늘려 적는 종이 | `BigInt` | `2n ** 64n` 이 정확히 나온다 |
| 줄자와 종이를 섞어 재기 | `1n + 1` | ★ `TypeError` — 언어가 막는다 |
| 32칸짜리 짧은 자 | 비트 연산자 | `3000000000 \| 0` 이 음수가 된다 |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 하나로 굳어 있다.
**돈**을 소수로 더하면 `0.1 + 0.2` 가 그대로 나오고, **DB 의 64비트 ID** 를 `JSON.parse` 로 받으면 **끝자리가 조용히 바뀐다.**
둘 다 **에러가 안 나고 값만 틀린다** — 이 주제의 값이 전부 거기 있다.

> **IEEE 754 배정밀도(double)** — 64비트에 부호 1 · 지수 11 · 가수 52 비트를 담는 실수 표현.
> 예: JS 의 `Number` 가 전부 이것이다. 정수도 실수도 같은 상자에 담긴다.

> **안전 정수(safe integer)** — **자기 말고 다른 정수와 값이 겹치지 않는** 정수.
> 예: `2**53 - 1` 까지가 안전하다. 그 너머에서는 두 정수가 한 값이 된다.

## 이 주제가 답하려는 질문

1. **`0.1 + 0.2` 가 왜 `0.3` 이 아닌가** — 그리고 화면에 보이는 숫자가 저장된 값이 아니라는 것.
2. **정수는 어디까지 믿을 수 있는가** — 그 너머에서 무엇이 조용히 깨지는가.
3. **`BigInt` 는 왜 섞이지 않는가** — 그리고 어디서만 섞이는가.

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 문장으로 읽는다.

### (1) `0.1 + 0.2` — 화면에 보이는 것은 저장된 값이 아니다

**언제 쓰나** — 소수를 더하거나 비교하는 모든 자리.

```text
   소스에 적은 것        실제로 저장된 것 (toFixed(20) 으로 본 것)

   0.1        ->     0.10000000000000000555
   0.2        ->     0.20000000000000001110
                     ------------------------ 더하면
                     0.30000000000000004441

   0.3        ->     0.29999999999999998890   <- 이것과 다르다

   ★ 셋이 전부 눈금에 끌려갔고, 끌려간 방향이 달랐다.
   ★ console.log 는 "그 값을 되살릴 수 있는 가장 짧은 표기" 를 보여 준다.
     그래서 0.1 은 0.1 로 보인다 — 저장된 값이 0.1 이라서가 아니다.
```

```js
// js01b-03a-float.js
// 숫자가 하나뿐인 언어 — 그 하나가 배정밀도 부동소수점이라는 것의 결과.
console.log("[1] 유명한 자리");
console.log("  0.1 + 0.2            =", 0.1 + 0.2);
console.log("  0.1 + 0.2 === 0.3    =", 0.1 + 0.2 === 0.3);
console.log("  0.1 + 0.2 - 0.3      =", 0.1 + 0.2 - 0.3);
console.log("  Number.EPSILON       =", Number.EPSILON);
console.log("  차이 < EPSILON 인가   =", Math.abs(0.1 + 0.2 - 0.3) < Number.EPSILON);

console.log("");
console.log("[2] 화면에 보이는 것은 '가장 짧은 표기' 이지 저장된 값이 아니다");
for (const n of [0.1, 0.2, 0.3, 0.1 + 0.2])
  console.log("  " + String(n).padEnd(22) + " toFixed(20) = " + n.toFixed(20) +
              "  toPrecision(17) = " + n.toPrecision(17));

console.log("");
console.log("[3] 그래서 결합 법칙이 깨진다");
console.log("  (0.1 + 0.2) + 0.3    =", (0.1 + 0.2) + 0.3);
console.log("  0.1 + (0.2 + 0.3)    =", 0.1 + (0.2 + 0.3));
console.log("  둘이 같은가           =", (0.1 + 0.2) + 0.3 === 0.1 + (0.2 + 0.3));
console.log("  0.1 * 3              =", 0.1 * 3);
console.log("  0.1 + 0.1 + 0.1      =", 0.1 + 0.1 + 0.1);

console.log("");
console.log("[4] 정확히 표현되는 소수도 있다 — 2 의 거듭제곱 분모면 된다");
for (const n of [0.5, 0.25, 0.125, 0.75, 1.5])
  console.log("  " + String(n).padEnd(8) + " toFixed(20) = " + n.toFixed(20));

console.log("");
console.log("[5] 돈은 정수로 — 그것이 처방이다");
console.log("  0.1 + 0.2 를 원 단위로 :", (0.1 * 10 + 0.2 * 10) / 10);
console.log("  10*0.1 + 10*0.2        :", 10 * 0.1 + 10 * 0.2, "(정수 3 이 나온다)");
console.log("  Number((0.1+0.2).toFixed(2)) :", Number((0.1 + 0.2).toFixed(2)));
```

```text
===== node20 js01b-03a-float.js (exit=0) =====
[1] 유명한 자리
  0.1 + 0.2            = 0.30000000000000004
  0.1 + 0.2 === 0.3    = false
  0.1 + 0.2 - 0.3      = 5.551115123125783e-17
  Number.EPSILON       = 2.220446049250313e-16
  차이 < EPSILON 인가   = true

[2] 화면에 보이는 것은 '가장 짧은 표기' 이지 저장된 값이 아니다
  0.1                    toFixed(20) = 0.10000000000000000555  toPrecision(17) = 0.10000000000000001
  0.2                    toFixed(20) = 0.20000000000000001110  toPrecision(17) = 0.20000000000000001
  0.3                    toFixed(20) = 0.29999999999999998890  toPrecision(17) = 0.29999999999999999
  0.30000000000000004    toFixed(20) = 0.30000000000000004441  toPrecision(17) = 0.30000000000000004

[3] 그래서 결합 법칙이 깨진다
  (0.1 + 0.2) + 0.3    = 0.6000000000000001
  0.1 + (0.2 + 0.3)    = 0.6
  둘이 같은가           = false
  0.1 * 3              = 0.30000000000000004
  0.1 + 0.1 + 0.1      = 0.30000000000000004

[4] 정확히 표현되는 소수도 있다 — 2 의 거듭제곱 분모면 된다
  0.5      toFixed(20) = 0.50000000000000000000
  0.25     toFixed(20) = 0.25000000000000000000
  0.125    toFixed(20) = 0.12500000000000000000
  0.75     toFixed(20) = 0.75000000000000000000
  1.5      toFixed(20) = 1.50000000000000000000

[5] 돈은 정수로 — 그것이 처방이다
  0.1 + 0.2 를 원 단위로 : 0.3
  10*0.1 + 10*0.2        : 3 (정수 3 이 나온다)
  Number((0.1+0.2).toFixed(2)) : 0.3
```

그림 해설 (한 단계씩).

- ★★★ **`toFixed(20)` 이 이 절의 창이다.** `console.log(0.1)` 은 `0.1` 로 보이지만
  저장된 값은 `0.10000000000000000555` 다 — **화면이 값을 감추고 있었다.**
  ★ 「가장 짧은 표기」란 **그 문자열을 다시 읽으면 같은 double 이 되는** 가장 짧은 것이다.
- ★★★ **`0.1 + 0.2 - 0.3` 이 `0` 이 아니라 `5.551115123125783e-17`** 이다.
  그 크기가 `Number.EPSILON`(`2.22e-16`)보다 작아서 「**EPSILON 보다 작으면 같다고 보자**」가 실무 처방이 된다.
  ★ 다만 그 처방은 **큰 수에서는 안 맞는다** — 눈금 간격이 값에 비례해 커지기 때문이다.
- ★★★ **결합 법칙이 깨진다.** `(0.1 + 0.2) + 0.3` 과 `0.1 + (0.2 + 0.3)` 이 다르다.
  ★ **더하는 순서가 결과를 바꾼다** — 합계를 내는 코드에서 정렬을 바꾸면 값이 달라질 수 있다는 뜻이다.
- ★★ **정확히 저장되는 소수도 있다.** `0.5`·`0.25`·`0.125` 는 **분모가 2 의 거듭제곱**이라 눈금 위에 정확히 앉는다.
  ★ 「소수는 다 부정확하다」는 틀리다.
- ★ **처방은 정수로 옮기는 것**이다. `10 * 0.1 + 10 * 0.2` 가 정확히 `3` 이다 — **돈은 원 단위 정수로 다룬다.**

**비용** — 수 타입이 하나뿐이라 **정수와 실수를 나눠 생각할 필요가 없다.**
대신 **소수 연산이 언제나 근사**이고, `===` 로 비교하면 틀린다.

### (2) 안전 정수 한계 — 다른 두 정수가 같아진다

**언제 쓰나** — ID·타임스탬프·카운터처럼 **큰 정수**를 다루는 자리.

```text
   ... 2**53-1   2**53   2**53+1   2**53+2 ...
        |         |        (없다)      |
        |         |                    |
      눈금       눈금                 눈금
      간격 1     여기부터 간격이 2

   ★ 2**53 + 1 은 눈금 위에 없다 -> 가장 가까운 2**53 으로 끌려간다
   ★ 그래서 2**53 === 2**53 + 1 이 참이다
   ★ 소스에 9007199254740993 이라고 적어도 이미 바뀐 값이 들어온다
```

```js
// js01b-03b-safe-integer.js
// 정수의 한계 — 어디서부터 "다른 두 정수가 같아지나".
console.log("[1] 한계 상수");
console.log("  Number.MAX_SAFE_INTEGER =", Number.MAX_SAFE_INTEGER, "(2**53 - 1)");
console.log("  Number.MIN_SAFE_INTEGER =", Number.MIN_SAFE_INTEGER);
console.log("  Number.MAX_VALUE        =", Number.MAX_VALUE);
console.log("  Number.MAX_VALUE * 2    =", Number.MAX_VALUE * 2);

console.log("");
console.log("[2] 경계를 한 걸음 넘으면 두 정수가 한 값이 된다");
const M = Number.MAX_SAFE_INTEGER;
console.log("  M          =", M);
console.log("  M + 1      =", M + 1);
console.log("  M + 2      =", M + 2);
console.log("  M + 1 === M + 2 :", M + 1 === M + 2);
console.log("  M + 3      =", M + 3, "  <- 여기서는 다시 갈린다");
console.log("  2**53 === 2**53 + 1 :", 2 ** 53 === 2 ** 53 + 1);
console.log("  2**53 + 2 === 2**53 :", 2 ** 53 + 2 === 2 ** 53);

console.log("");
console.log("[3] 소스에 적은 리터럴부터 이미 바뀐다");
console.log("  9007199254740993       =", 9007199254740993);
console.log("  9007199254740993n      =", String(9007199254740993n) + "n");
console.log("  JSON.parse('{\"id\":9007199254740993}').id =",
            JSON.parse('{"id":9007199254740993}').id);
console.log("  JSON.stringify 로 되돌리면 :", JSON.stringify(JSON.parse('{"id":9007199254740993}')));

console.log("");
console.log("[4] isInteger 와 isSafeInteger 는 다른 질문이다");
console.log("n".padEnd(24) + "Number.isInteger".padEnd(18) + "Number.isSafeInteger");
console.log("-".repeat(24 + 18 + 20));
for (const [label, n] of [["1", 1], ["1.0", 1.0], ["1.5", 1.5], ["2**53 - 1", 2 ** 53 - 1],
                          ["2**53", 2 ** 53], ["1e21", 1e21], ["Infinity", Infinity],
                          ["NaN", NaN], ['"1" (a string)', "1"]])
  console.log(label.padEnd(24) + String(Number.isInteger(n)).padEnd(18) + String(Number.isSafeInteger(n)));

console.log("");
console.log("[5] 큰 수가 필요하면 BigInt 로 간다");
console.log("  BigInt(M) + 1n + 1n     =", String(BigInt(M) + 1n + 1n) + "n");
console.log("  2n ** 64n               =", String(2n ** 64n) + "n");
console.log("  2 ** 64 (Number)        =", 2 ** 64);
```

```text
===== node20 js01b-03b-safe-integer.js (exit=0) =====
[1] 한계 상수
  Number.MAX_SAFE_INTEGER = 9007199254740991 (2**53 - 1)
  Number.MIN_SAFE_INTEGER = -9007199254740991
  Number.MAX_VALUE        = 1.7976931348623157e+308
  Number.MAX_VALUE * 2    = Infinity

[2] 경계를 한 걸음 넘으면 두 정수가 한 값이 된다
  M          = 9007199254740991
  M + 1      = 9007199254740992
  M + 2      = 9007199254740992
  M + 1 === M + 2 : true
  M + 3      = 9007199254740994   <- 여기서는 다시 갈린다
  2**53 === 2**53 + 1 : true
  2**53 + 2 === 2**53 : false

[3] 소스에 적은 리터럴부터 이미 바뀐다
  9007199254740993       = 9007199254740992
  9007199254740993n      = 9007199254740993n
  JSON.parse('{"id":9007199254740993}').id = 9007199254740992
  JSON.stringify 로 되돌리면 : {"id":9007199254740992}

[4] isInteger 와 isSafeInteger 는 다른 질문이다
n                       Number.isInteger  Number.isSafeInteger
--------------------------------------------------------------
1                       true              true
1.0                     true              true
1.5                     false             false
2**53 - 1               true              true
2**53                   true              false
1e21                    true              false
Infinity                false             false
NaN                     false             false
"1" (a string)          false             false

[5] 큰 수가 필요하면 BigInt 로 간다
  BigInt(M) + 1n + 1n     = 9007199254740993n
  2n ** 64n               = 18446744073709551616n
  2 ** 64 (Number)        = 18446744073709552000
```

그림 해설.

- ★★★ **`M + 1 === M + 2` 가 참**이다. 두 개의 **다른 정수**가 **같은 값**이 됐다.
  ★ 그런데 **`M + 3` 에서는 다시 갈린다** — 눈금 간격이 2 이므로 **짝수는 살아 있고 홀수만 없다.**
- ★★★ **소스에 적은 리터럴부터 이미 바뀐다.** `9007199254740993` 을 그대로 쳐도 `...992` 가 나온다.
  ★★ **`JSON.parse` 도 마찬가지**다 — 서버가 보낸 64비트 ID 가 **파싱되는 순간 조용히 바뀌고**,
  `JSON.stringify` 로 되돌리면 **바뀐 값이 나간다.** 예외도 경고도 없다.
- ★★ **`Number.isInteger` 와 `Number.isSafeInteger` 는 다른 질문**이다.
  `2**53` 은 정수이지만 안전하지 않고, `1e21` 도 마찬가지다. **「정수인가」로 큰 수를 방어할 수 없다.**
- ★★ **`Number.MAX_VALUE * 2` 는 `Infinity`** 다 — 넘치면 예외가 아니라 `Infinity` 가 된다(3번 절).
- ★ **처방은 `BigInt`** 다. `BigInt(M) + 1n + 1n` 이 `9007199254740993n` 으로 정확히 나온다.
  ★ 다만 **`JSON` 은 `BigInt` 를 모른다**(4번 절) — 그래서 큰 ID 는 **문자열로 주고받는** 것이 실무 답이다.

**비용** — `2**53` 까지는 정수 연산이 정확하고 빠르다. 웬만한 카운터·인덱스에는 충분하다.
대신 **그 너머에서 아무 신호 없이 틀린다** — 검사하지 않으면 영원히 모른다.

### (3) `NaN`·`Infinity`·`-0` — 숫자인데 숫자가 아닌 값들

**언제 쓰나** — 나눗셈·파싱·반올림 결과를 받는 모든 자리.

```text
   0 으로 나눠도 예외가 안 난다

   1 / 0   -> Infinity        ★ 예외가 아니다
   0 / 0   -> NaN             ★ 예외가 아니다
   1n / 0n -> RangeError      ★ BigInt 는 터진다

   NaN 의 성질:  x !== x 인 유일한 값

   -0 의 성질 :  === 로는 0 과 같다
                 Object.is 로는 다르다
                 1 / -0 이 -Infinity 라서 들킨다
```

```js
// js01b-03c-nan-zero.js
// NaN · Infinity · -0 — "숫자인데 숫자가 아닌" 값들.
console.log("[1] 나눗셈이 던지지 않는다");
console.log("  1 / 0      =", 1 / 0);
console.log("  -1 / 0     =", -1 / 0);
console.log("  0 / 0      =", 0 / 0);
console.log("  1 % 0      =", 1 % 0);
console.log("  1n / 0n 은 ? -> " + (() => { try { return String(1n / 0n); } catch (e) { return e.constructor.name + ": " + e.message; } })());

console.log("");
console.log("[2] NaN 은 자기 자신과도 다르다 — 그것이 판별법이다");
console.log("  typeof NaN            =", typeof NaN);
console.log("  NaN === NaN           =", NaN === NaN);
console.log("  x !== x 로 판별       =", ((x) => x !== x)(NaN));
console.log("  Number.isNaN('abc')   =", Number.isNaN("abc"));
console.log("  isNaN('abc')          =", isNaN("abc"), "  <- 전역 isNaN 은 먼저 숫자로 바꾼다");
console.log("  isNaN('')             =", isNaN(""), " | Number.isNaN('') =", Number.isNaN(""));

console.log("");
console.log("[3] -0 은 === 로는 안 보이고 나눗셈과 Object.is 로만 보인다");
console.log("  -0 === 0              =", -0 === 0);
console.log("  Object.is(-0, 0)      =", Object.is(-0, 0));
console.log("  String(-0)            =", JSON.stringify(String(-0)));
console.log("  (-0).toFixed(2)       =", JSON.stringify((-0).toFixed(2)));
console.log("  JSON.stringify(-0)    =", JSON.stringify(-0));
console.log("  1 / -0                =", 1 / -0, "  <- 이것이 실무 판별법");
console.log("  Math.sign(-0)         =", Math.sign(-0), "| Object.is(Math.sign(-0), -0) =", Object.is(Math.sign(-0), -0));
console.log("  -0 + 0                =", -0 + 0, "| Object.is(-0 + 0, 0) =", Object.is(-0 + 0, 0));
console.log("  -0 * 1                =", -0 * 1, "| Object.is(-0 * 1, -0) =", Object.is(-0 * 1, -0));

console.log("");
console.log("[4] -0 을 만드는 흔한 자리");
for (const [label, v] of [["Math.round(-0.4)", Math.round(-0.4)], ["Math.trunc(-0.5)", Math.trunc(-0.5)],
                          ["Math.ceil(-0.5)", Math.ceil(-0.5)], ["parseInt('-0')", parseInt("-0")],
                          ["Number('-0')", Number("-0")], ["-1 * 0", -1 * 0], ["[-0].sort()[0]", [-0].sort()[0]]])
  console.log("  " + label.padEnd(20) + " -> 보이는 값 " + String(v).padEnd(4) + " | -0 인가: " + Object.is(v, -0));

console.log("");
console.log("[5] 세 동등성이 갈리는 자리는 딱 두 칸이다");
console.log("  compare    " + "NaN vs NaN".padEnd(14) + "0 vs -0");
console.log("  ===        " + String(NaN === NaN).padEnd(14) + (0 === -0));
console.log("  Object.is  " + String(Object.is(NaN, NaN)).padEnd(14) + Object.is(0, -0));
console.log("  includes   " + String([NaN].includes(NaN)).padEnd(14) + [0].includes(-0));
console.log("  indexOf    " + String([NaN].indexOf(NaN) !== -1).padEnd(14) + ([0].indexOf(-0) !== -1));
console.log("  Set key    " + String(new Set([NaN, NaN]).size === 1).padEnd(14) + (new Set([0, -0]).size === 1));
```

```text
===== node20 js01b-03c-nan-zero.js (exit=0) =====
[1] 나눗셈이 던지지 않는다
  1 / 0      = Infinity
  -1 / 0     = -Infinity
  0 / 0      = NaN
  1 % 0      = NaN
  1n / 0n 은 ? -> RangeError: Division by zero

[2] NaN 은 자기 자신과도 다르다 — 그것이 판별법이다
  typeof NaN            = number
  NaN === NaN           = false
  x !== x 로 판별       = true
  Number.isNaN('abc')   = false
  isNaN('abc')          = true   <- 전역 isNaN 은 먼저 숫자로 바꾼다
  isNaN('')             = false  | Number.isNaN('') = false

[3] -0 은 === 로는 안 보이고 나눗셈과 Object.is 로만 보인다
  -0 === 0              = true
  Object.is(-0, 0)      = false
  String(-0)            = "0"
  (-0).toFixed(2)       = "0.00"
  JSON.stringify(-0)    = 0
  1 / -0                = -Infinity   <- 이것이 실무 판별법
  Math.sign(-0)         = -0 | Object.is(Math.sign(-0), -0) = true
  -0 + 0                = 0 | Object.is(-0 + 0, 0) = true
  -0 * 1                = -0 | Object.is(-0 * 1, -0) = true

[4] -0 을 만드는 흔한 자리
  Math.round(-0.4)     -> 보이는 값 0    | -0 인가: true
  Math.trunc(-0.5)     -> 보이는 값 0    | -0 인가: true
  Math.ceil(-0.5)      -> 보이는 값 0    | -0 인가: true
  parseInt('-0')       -> 보이는 값 0    | -0 인가: true
  Number('-0')         -> 보이는 값 0    | -0 인가: true
  -1 * 0               -> 보이는 값 0    | -0 인가: true
  [-0].sort()[0]       -> 보이는 값 0    | -0 인가: true

[5] 세 동등성이 갈리는 자리는 딱 두 칸이다
  compare    NaN vs NaN    0 vs -0
  ===        false         true
  Object.is  true          false
  includes   true          true
  indexOf    false         true
  Set key    true          true
```

그림 해설.

- ★★★ **`Number` 의 나눗셈은 안 터지는데 `BigInt` 의 나눗셈은 터진다.**
  같은 연산자가 타입에 따라 **「값」과 「예외」로 갈린다** — `RangeError: Division by zero`.
- ★★★ **`NaN` 은 `x !== x` 인 유일한 값**이고 그것이 판별법이다.
  ★ **전역 `isNaN` 과 `Number.isNaN` 은 다르다** — 전역 쪽은 **먼저 숫자로 바꾸므로** `isNaN("abc")` 가 참이다.
  「이 값이 `NaN` 인가」를 물었는데 「이 값을 숫자로 바꾸면 `NaN` 인가」가 답으로 온다.
- ★★★ **`-0` 은 `String` 으로도 `JSON` 으로도 `0` 이다.** `===` 로도 `0` 과 같다.
  드러나는 곳은 **`Object.is` 와 `1 / -0` 둘뿐**이다.
- ★★ **`-0` 을 만드는 자리가 생각보다 많다** — `Math.round(-0.4)`·`Math.trunc(-0.5)`·`parseInt("-0")`·`-1 * 0` 이 전부 `-0` 이다.
  ★ 화면에는 `0` 으로 보이므로 **로그를 봐서는 절대 못 찾는다.**
- ★★ **`-0 + 0` 은 `0` 이 되고 `-0 * 1` 은 `-0` 으로 남는다.** 연산마다 부호가 살거나 죽는다.
- ★★★ **세 동등성이 갈리는 자리는 딱 두 칸**이다 — `NaN` 과 `±0`.
  `indexOf` 만 `===` 를 쓰고 `includes`·`Set` 은 SameValueZero 를 써서 **`NaN` 을 찾아낸다.**
  ★ 같은 배열에 `indexOf` 는 `-1` 을, `includes` 는 `true` 를 돌려준다 — 02번 주제에서 본 그 갈림이다.

**비용** — 나눗셈이 안 터져서 파이프라인이 안 멈춘다.
대신 **`NaN` 이 한 번 섞이면 그 뒤의 모든 연산이 `NaN`** 이 되고, **어디서 들어왔는지는 안 남는다.**

### (4) ★★★ `BigInt` 를 섞으면 — 전부 `TypeError` 인데 구멍이 하나 있다

**언제 쓰나** — 64비트 ID·큰 정수 계산.

```text
   BigInt 와 Number 를 섞으면

   산술 ( + - * / ** | << )  ->  ★ TypeError  (전부)
   단항 +                     ->  ★ TypeError  (단항 - 는 된다)
   비교 ( == != < > <= >= )   ->  된다. 수학적 값으로 견준다
   ===                        ->  된다. 그런데 ★ 언제나 false (타입이 다르다)
   문자열과 +                  ->  ★ 된다 — 유일한 구멍

   ★ "섞으면 터진다" 인데 1n + '1' 은 "11" 이다.
```

```js
// js01b-03d-bigint-mix.js
// BigInt 와 Number 를 섞으면 어디서 터지고 어디서 통과하나 — 전수로 던진다.
function t(expr, f) {
  let r;
  try { const v = f(); r = typeof v === "bigint" ? v + "n" : JSON.stringify(v) ?? String(v); }
  catch (e) { r = e.constructor.name + ": " + e.message; }
  console.log("  " + expr.padEnd(26) + " -> " + r);
}

console.log("[1] 산술은 섞으면 전부 TypeError 다");
t("1n + 2n",  () => 1n + 2n);
t("1n + 1",   () => 1n + 1);
t("1 + 1n",   () => 1 + 1n);
t("1n - 1",   () => 1n - 1);
t("1n * 2",   () => 1n * 2);
t("1n / 2",   () => 1n / 2);
t("1n ** 2",  () => 1n ** 2);
t("-1n",      () => -1n);
t("+1n",      () => +1n);
t("1n | 0",   () => 1n | 0);
t("1n << 1",  () => 1n << 1);

console.log("");
console.log("[2] 그런데 '+' 가 문자열을 만나면 통과한다 — 유일한 구멍이다");
t("1n + '1'",     () => 1n + "1");
t("'1' + 1n",     () => "1" + 1n);
t("`${1n}`",      () => `${1n}`);
t("String(1n)",   () => String(1n));
t("[1n].join()",  () => [1n].join());

console.log("");
console.log("[3] 비교는 섞어도 된다 — == 와 관계 연산자만");
t("1n == 1",      () => 1n == 1);
t("1n === 1",     () => 1n === 1);
t("1n != 1",      () => 1n != 1);
t("1n < 2",       () => 1n < 2);
t("2n > 1.5",     () => 2n > 1.5);
t("1n == '1'",    () => 1n == "1");
t("0n == false",  () => 0n == false);
t("Object.is(1n, 1n)", () => Object.is(1n, 1n));
t("new Set([1n,1]).size", () => new Set([1n, 1]).size);

console.log("");
console.log("[4] 다리를 놓는 두 함수와 그 한계");
t("Number(9007199254740993n)", () => Number(9007199254740993n));
t("BigInt(1)",     () => BigInt(1));
t("BigInt(1.5)",   () => BigInt(1.5));
t("BigInt('1.5')", () => BigInt("1.5"));
t("BigInt('0x10')", () => BigInt("0x10"));
t("BigInt('')",    () => BigInt(""));
t("BigInt(null)",  () => BigInt(null));

console.log("");
console.log("[5] 다른 곳에서도 막힌다");
t("Math.abs(-1n)",      () => Math.abs(-1n));
t("Math.max(1n, 2n)",   () => Math.max(1n, 2n));
t("JSON.stringify(1n)", () => JSON.stringify(1n));
t("parseInt('1n')",     () => parseInt("1n"));
t("(1n).toString(2)",   () => (1n).toString(2));
t("5n / 2n",            () => 5n / 2n);
t("-5n / 2n",           () => -5n / 2n);
t("5n % 3n",            () => 5n % 3n);
```

```text
===== node20 js01b-03d-bigint-mix.js (exit=0) =====
[1] 산술은 섞으면 전부 TypeError 다
  1n + 2n                    -> 3n
  1n + 1                     -> TypeError: Cannot mix BigInt and other types, use explicit conversions
  1 + 1n                     -> TypeError: Cannot mix BigInt and other types, use explicit conversions
  1n - 1                     -> TypeError: Cannot mix BigInt and other types, use explicit conversions
  1n * 2                     -> TypeError: Cannot mix BigInt and other types, use explicit conversions
  1n / 2                     -> TypeError: Cannot mix BigInt and other types, use explicit conversions
  1n ** 2                    -> TypeError: Cannot mix BigInt and other types, use explicit conversions
  -1n                        -> -1n
  +1n                        -> TypeError: Cannot convert a BigInt value to a number
  1n | 0                     -> TypeError: Cannot mix BigInt and other types, use explicit conversions
  1n << 1                    -> TypeError: Cannot mix BigInt and other types, use explicit conversions

[2] 그런데 '+' 가 문자열을 만나면 통과한다 — 유일한 구멍이다
  1n + '1'                   -> "11"
  '1' + 1n                   -> "11"
  `${1n}`                    -> "1"
  String(1n)                 -> "1"
  [1n].join()                -> "1"

[3] 비교는 섞어도 된다 — == 와 관계 연산자만
  1n == 1                    -> true
  1n === 1                   -> false
  1n != 1                    -> false
  1n < 2                     -> true
  2n > 1.5                   -> true
  1n == '1'                  -> true
  0n == false                -> true
  Object.is(1n, 1n)          -> true
  new Set([1n,1]).size       -> 2

[4] 다리를 놓는 두 함수와 그 한계
  Number(9007199254740993n)  -> 9007199254740992
  BigInt(1)                  -> 1n
  BigInt(1.5)                -> RangeError: The number 1.5 cannot be converted to a BigInt because it is not an integer
  BigInt('1.5')              -> SyntaxError: Cannot convert 1.5 to a BigInt
  BigInt('0x10')             -> 16n
  BigInt('')                 -> 0n
  BigInt(null)               -> TypeError: Cannot convert null to a BigInt

[5] 다른 곳에서도 막힌다
  Math.abs(-1n)              -> TypeError: Cannot convert a BigInt value to a number
  Math.max(1n, 2n)           -> TypeError: Cannot convert a BigInt value to a number
  JSON.stringify(1n)         -> TypeError: Do not know how to serialize a BigInt
  parseInt('1n')             -> 1
  (1n).toString(2)           -> "1"
  5n / 2n                    -> 2n
  -5n / 2n                   -> -2n
  5n % 3n                    -> 2n
```

그림 해설.

- ★★★ **산술은 전부 `TypeError: Cannot mix BigInt and other types, use explicit conversions`** 다.
  ★ 자동 변환을 **일부러 막아 둔 것**이다 — 섞어서 조용히 정밀도를 잃는 것보다 터지는 쪽을 골랐다.
- ★★★ **단항 `-1n` 은 되는데 단항 `+1n` 은 `TypeError`** 다.
  단항 `+` 는 **언제나 `Number` 를 만드는** 연산자로 규정돼 있어서 BigInt 에 쓸 수가 없다.
  ★ **부호를 바꾸는 것과 숫자로 바꾸는 것이 다른 일**이라는 뜻이다.
- ★★★ **`1n + '1'` 은 `"11"`** 이다 — **유일한 구멍**이다. `+` 가 문자열을 만나면 이어붙이기로 가고,
  그 경로에는 BigInt 금지가 없다. ★ 02번 주제의 「`+` 만 문자열로 기운다」가 여기서 다시 나온다.
- ★★★ **`1n == 1` 은 참인데 `1n === 1` 은 거짓**이다. 02번 격자의 `0n` 행이 `0` 행과 같았던 이유가 이것이다.
  ★ 그래서 **`new Set([1n, 1]).size` 가 `2`** 다 — `Set` 은 SameValueZero 라 타입을 본다.
- ★★ **`BigInt(1.5)` 는 `RangeError`, `BigInt("1.5")` 는 `SyntaxError`** 다.
  같은 「1.5」인데 **숫자로 주면 범위 오류, 문자열로 주면 문법 오류**다 — 경로가 다르다.
  ★ **`BigInt("")` 는 `0n`** 이고 **`BigInt(null)` 은 `TypeError`** 다. 규칙이 촘촘하다.
- ★★ **`Number(9007199254740993n)` 은 조용히 `...992`** 가 된다. **되돌아가는 다리는 안전하지 않다.**
- ★★ **`JSON.stringify(1n)` 은 `TypeError: Do not know how to serialize a BigInt`** 다.
  ★ 그래서 큰 ID 는 **문자열로 주고받는다** — `BigInt` 를 쓰더라도 경계에서는 문자열이다.
- ★ **`5n / 2n` 은 `2n`** 이다. BigInt 나눗셈은 **0 쪽으로 버린다** — `-5n / 2n` 이 `-2n` 인 것이 그 증거다.

**비용** — 정수가 정확해지고, 섞으면 **바로 터져서** 조용한 사고가 안 난다.
대신 **기존 코드와 안 섞이고**, `Math` 도 `JSON` 도 못 쓴다 — **자기들만의 섬**이다.

### (5) 반올림이 기대와 어긋나는 자리

**언제 쓰나** — 금액·비율을 화면에 찍는 모든 자리.

```js
// js01b-03e-rounding.js
// 반올림이 기대와 어긋나는 자리 — 원인은 함수가 아니라 저장된 값이다.
console.log("[1] toFixed 가 '내림' 처럼 보이는 자리");
console.log("n".padEnd(10) + "toFixed(2)".padEnd(12) + "실제로 저장된 값 (toFixed(20))");
console.log("-".repeat(10 + 12 + 30));
for (const n of [1.005, 2.675, 8.345, 1.015, 1.045, 1.055])
  console.log(String(n).padEnd(10) + n.toFixed(2).padEnd(12) + n.toFixed(20));

console.log("");
console.log("[2] .5 는 어느 쪽으로 가나 — toFixed 와 Math.round 가 다르다");
console.log("n".padEnd(8) + "toFixed(0)".padEnd(12) + "Math.round".padEnd(12) +
            "Math.trunc".padEnd(12) + "Math.floor");
console.log("-".repeat(8 + 12 + 12 + 12 + 11));
for (const n of [0.5, 1.5, 2.5, 3.5, -0.5, -1.5, -2.5])
  console.log(String(n).padEnd(8) + n.toFixed(0).padEnd(12) + String(Math.round(n)).padEnd(12) +
              String(Math.trunc(n)).padEnd(12) + String(Math.floor(n)));
console.log("");
console.log("  toFixed  : 0 에서 먼 쪽으로 (2.5 -> 3 · -2.5 -> -3)");
console.log("  Math.round: 큰 쪽으로      (2.5 -> 3 · -2.5 -> -2)  <- 음수에서 갈린다");

console.log("");
console.log("[3] 경계에 아슬아슬한 값");
console.log("  Math.round(0.49999999999999994) =", Math.round(0.49999999999999994));
console.log("  0.49999999999999994 + 0.5       =", 0.49999999999999994 + 0.5, " <- 더하면 1 이 된다");
console.log("  Math.floor(0.49999999999999994 + 0.5) =", Math.floor(0.49999999999999994 + 0.5));
console.log("  ★ 'floor(x + 0.5)' 로 구현했으면 1 이 나왔을 자리다");

console.log("");
console.log("[4] toFixed 의 다른 함정");
console.log("  (1e21).toFixed(2)     =", (1e21).toFixed(2), " <- 지수 표기로 새어 나간다");
console.log("  typeof (1.5).toFixed(2) =", typeof (1.5).toFixed(2), " <- 문자열이다");
console.log("  (1.5).toFixed(2) + 1  =", (1.5).toFixed(2) + 1);
let e;
try { (1.5).toFixed(101); } catch (err) { e = err.constructor.name + ": " + err.message; }
console.log("  (1.5).toFixed(101)    =", e);
console.log("  (1.5).toFixed(100).length =", (1.5).toFixed(100).length);
console.log("  (1234.5678).toPrecision(6) =", (1234.5678).toPrecision(6));
console.log("  (0.000001234).toPrecision(2) =", (0.000001234).toPrecision(2));
```

```text
===== node20 js01b-03e-rounding.js (exit=0) =====
[1] toFixed 가 '내림' 처럼 보이는 자리
n         toFixed(2)  실제로 저장된 값 (toFixed(20))
----------------------------------------------------
1.005     1.00        1.00499999999999989342
2.675     2.67        2.67499999999999982236
8.345     8.35        8.34500000000000063949
1.015     1.01        1.01499999999999990230
1.045     1.04        1.04499999999999992895
1.055     1.05        1.05499999999999993783

[2] .5 는 어느 쪽으로 가나 — toFixed 와 Math.round 가 다르다
n       toFixed(0)  Math.round  Math.trunc  Math.floor
-------------------------------------------------------
0.5     1           1           0           0
1.5     2           2           1           1
2.5     3           3           2           2
3.5     4           4           3           3
-0.5    -1          0           0           -1
-1.5    -2          -1          -1          -2
-2.5    -3          -2          -2          -3

  toFixed  : 0 에서 먼 쪽으로 (2.5 -> 3 · -2.5 -> -3)
  Math.round: 큰 쪽으로      (2.5 -> 3 · -2.5 -> -2)  <- 음수에서 갈린다

[3] 경계에 아슬아슬한 값
  Math.round(0.49999999999999994) = 0
  0.49999999999999994 + 0.5       = 1  <- 더하면 1 이 된다
  Math.floor(0.49999999999999994 + 0.5) = 1
  ★ 'floor(x + 0.5)' 로 구현했으면 1 이 나왔을 자리다

[4] toFixed 의 다른 함정
  (1e21).toFixed(2)     = 1e+21  <- 지수 표기로 새어 나간다
  typeof (1.5).toFixed(2) = string  <- 문자열이다
  (1.5).toFixed(2) + 1  = 1.501
  (1.5).toFixed(101)    = RangeError: toFixed() digits argument must be between 0 and 100
  (1.5).toFixed(100).length = 102
  (1234.5678).toPrecision(6) = 1234.57
  (0.000001234).toPrecision(2) = 0.0000012
```

그림 해설.

- ★★★ **`(1.005).toFixed(2)` 가 `1.00`** 이다. 「반올림이 틀렸다」가 아니라
  **저장된 값이 `1.00499999999999989342`** 라서 내림이 맞다. ★ 옆 칸에 그 값을 같이 찍어 **원인을 같은 블록 안에서** 보인다.
- ★★★ **`toFixed` 와 `Math.round` 가 음수에서 갈린다.**
  `(-2.5).toFixed(0)` 은 `-3` 이고 `Math.round(-2.5)` 는 `-2` 다.
  **`toFixed` 는 0 에서 먼 쪽으로, `Math.round` 는 큰 쪽으로** 간다.
  ★ 양수만 보고 「둘이 같다」고 결론 내면 이 자리를 놓친다.
- ★★★ **`Math.round(0.49999999999999994)` 가 `0`** 이다.
  `floor(x + 0.5)` 로 구현했다면 `1` 이 나왔을 자리다 — **더하는 순간 `1` 로 끌려가기 때문**이다.
  ★ 같은 블록에서 `0.49999999999999994 + 0.5` 가 `1` 이라는 것을 함께 찍어 **그 차이를 보인다.**
  ★★ 명세가 이 자리를 **따로 규정**한다 — 「0.5 보다 작고 0 이상이면 `+0`」. **엔진의 재량이 아니다.**
- ★★ **`toFixed` 는 문자열을 돌려준다.** `(1.5).toFixed(2) + 1` 이 `"1.501"` 이다 — 02번의 `+` 규칙이 여기서 물린다.
- ★★ **`(1e21).toFixed(2)` 는 `"1e+21"`** 이다. 큰 수에서는 **고정 소수 표기를 포기**하고 지수 표기로 샌다.
- ★ **`toFixed` 의 인자는 0\~100** 이고 넘으면 `RangeError` 다.

**비용** — `toFixed` 한 줄로 자리를 맞출 수 있다.
대신 **반올림 방향이 함수마다 다르고**, 근본 원인이 **값 자체**라서 함수를 바꿔도 안 고쳐진다.

### (6) 비트 연산은 32비트로 자른다 — 숫자가 64비트인데도

**언제 쓰나** — 플래그·해시·「빠른 정수 변환」 관용구.

```text
   Number 는 64비트 double 인데

   비트 연산자( & | ^ ~ << >> >>> )는
       (1) 먼저 ToInt32 / ToUint32 로 자르고
       (2) 32비트 정수로 계산한 뒤
       (3) 다시 Number 로 돌려준다

   3000000000 | 0   ->  -1294967296    ★ 부호까지 바뀐다
   3000000000 >>> 0 ->  3000000000     ★ 이쪽은 살아남는다
   1 << 32          ->  1              ★ 시프트 횟수도 32 로 나눈 나머지
```

```js
// js01b-03f-bitwise32.js
// 비트 연산자는 피연산자를 32비트 정수로 자른 뒤에 일한다 — double 이 아니다.
console.log("[1] 32비트를 넘으면 잘린다");
console.log("expr".padEnd(22) + "result".padEnd(16) + "원래 값");
console.log("-".repeat(22 + 16 + 22));
for (const [label, out, orig] of [
  ["2**31 | 0",      2 ** 31 | 0,      2 ** 31],
  ["2**32 | 0",      2 ** 32 | 0,      2 ** 32],
  ["2**32 + 5 | 0",  2 ** 32 + 5 | 0,  2 ** 32 + 5],
  ["4294967295 | 0", 4294967295 | 0,   4294967295],
  ["1e10 | 0",       1e10 | 0,         1e10],
  ["1e21 | 0",       1e21 | 0,         1e21],
  ["NaN | 0",        NaN | 0,          NaN],
  ["Infinity | 0",   Infinity | 0,     Infinity],
  ["3.9 | 0",        3.9 | 0,          3.9],
  ["-3.9 | 0",       -3.9 | 0,         -3.9],
]) console.log(label.padEnd(22) + String(out).padEnd(16) + String(orig));

console.log("");
console.log("[2] 시프트 횟수도 32 로 나눈 나머지가 된다");
for (const [label, v] of [["1 << 0", 1 << 0], ["1 << 31", 1 << 31], ["1 << 32", 1 << 32],
                          ["1 << 33", 1 << 33], ["1 << -1", 1 << -1]])
  console.log("  " + label.padEnd(12) + "= " + v);

console.log("");
console.log("[3] >>> 만 부호 없는 32비트로 읽는다");
for (const [label, v] of [["-1 >> 0", -1 >> 0], ["-1 >>> 0", -1 >>> 0],
                          ["~0", ~0], ["~~3.9", ~~3.9], ["~~-3.9", ~~-3.9]])
  console.log("  " + label.padEnd(16) + "= " + v);
let e;
try { -1 >>> 0n; } catch (err) { e = err.constructor.name + ": " + err.message; }
console.log("  -1 >>> 0n       = " + e);
try { 1n >>> 1n; } catch (err) { e = err.constructor.name + ": " + err.message; }
console.log("  1n >>> 1n       = " + e, " <- BigInt 에는 >>> 가 아예 없다");

console.log("");
console.log("[4] BigInt 의 비트 연산에는 32비트 한계가 없다");
console.log("  (2n ** 40n) >> 8n  =", String((2n ** 40n) >> 8n) + "n");
console.log("  1n << 100n         =", String(1n << 100n) + "n");
console.log("  -1n & 0xffn        =", String(-1n & 0xffn) + "n");
console.log("  Number 로 하면      :", 1 << 100);

console.log("");
console.log("[5] 그래서 '빠른 정수 변환' 관용구가 32비트를 넘으면 조용히 틀린다");
const id = 3000000000;
console.log("  id                  =", id);
console.log("  id | 0              =", id | 0, "  <- 음수가 됐다");
console.log("  ~~id                =", ~~id);
console.log("  id >>> 0            =", id >>> 0, "  <- 이건 맞다");
console.log("  Math.trunc(id)      =", Math.trunc(id), "  <- 이것이 안전한 쪽");
```

```text
===== node20 js01b-03f-bitwise32.js (exit=0) =====
[1] 32비트를 넘으면 잘린다
expr                  result          원래 값
------------------------------------------------------------
2**31 | 0             -2147483648     2147483648
2**32 | 0             0               4294967296
2**32 + 5 | 0         5               4294967301
4294967295 | 0        -1              4294967295
1e10 | 0              1410065408      10000000000
1e21 | 0              -559939584      1e+21
NaN | 0               0               NaN
Infinity | 0          0               Infinity
3.9 | 0               3               3.9
-3.9 | 0              -3              -3.9

[2] 시프트 횟수도 32 로 나눈 나머지가 된다
  1 << 0      = 1
  1 << 31     = -2147483648
  1 << 32     = 1
  1 << 33     = 2
  1 << -1     = -2147483648

[3] >>> 만 부호 없는 32비트로 읽는다
  -1 >> 0         = -1
  -1 >>> 0        = 4294967295
  ~0              = -1
  ~~3.9           = 3
  ~~-3.9          = -3
  -1 >>> 0n       = TypeError: Cannot mix BigInt and other types, use explicit conversions
  1n >>> 1n       = TypeError: BigInts have no unsigned right shift, use >> instead  <- BigInt 에는 >>> 가 아예 없다

[4] BigInt 의 비트 연산에는 32비트 한계가 없다
  (2n ** 40n) >> 8n  = 4294967296n
  1n << 100n         = 1267650600228229401496703205376n
  -1n & 0xffn        = 255n
  Number 로 하면      : 16

[5] 그래서 '빠른 정수 변환' 관용구가 32비트를 넘으면 조용히 틀린다
  id                  = 3000000000
  id | 0              = -1294967296   <- 음수가 됐다
  ~~id                = -1294967296
  id >>> 0            = 3000000000   <- 이건 맞다
  Math.trunc(id)      = 3000000000   <- 이것이 안전한 쪽
```

그림 해설.

- ★★★ **`2**32 | 0` 이 `0`** 이다. 위쪽 비트가 통째로 버려진다.
  `4294967295 | 0` 이 `-1` 인 것은 **최상위 비트가 부호로 읽히기** 때문이다.
- ★★★ **`1e21 | 0` 이 `-559939584`** 다. **아무 관계 없어 보이는 수**가 나온다 —
  `2**32` 로 나눈 나머지를 부호 있는 32비트로 읽은 결과다. ★ **경고가 없다.**
- ★★ **시프트 횟수도 32 로 나눈 나머지**다. `1 << 32` 가 `1`, `1 << 33` 이 `2` 다.
  ★ `1 << -1` 이 `-2147483648` 인 것도 같은 규칙이다(`-1` 을 부호 없는 5비트로 읽으면 31).
- ★★ **`>>>` 만 부호 없이 읽는다.** `-1 >>> 0` 이 `4294967295` 다. 그래서 **32비트 부호 없는 정수를 얻는 관용구**가 된다.
- ★★★ **`BigInt` 에는 `>>>` 가 아예 없다** — `TypeError: BigInts have no unsigned right shift, use >> instead`.
  ★ 「무한히 긴 정수」에는 **부호 없는 시프트라는 개념이 성립하지 않기** 때문이다.
- ★★ **`BigInt` 의 비트 연산에는 32비트 한계가 없다.** `1n << 100n` 이 정확히 나온다.
- ★★★ **`id | 0` 과 `~~id` 는 30억에서 음수가 된다.** 「빠른 정수 변환」 관용구가 **32비트를 넘는 순간 조용히 틀린다.**
  ★ **`Math.trunc` 가 안전한 쪽**이다 — 한계가 없다.

**비용** — 비트 연산이 32비트로 고정돼 있어 **엔진이 빠르게 만들 수 있고** 결과가 이식 가능하다.
대신 **64비트 값에 쓰면 조용히 잘린다** — 예외도 경고도 없다.

### (7) 두 판과 브라우저에서 — 갈리는 자리가 없다

**언제 쓰나** — 「이 수치가 이 판에서만 그런 건 아닐까」를 물을 때.

```sh
// js01b-vdiff.sh
#!/usr/bin/env bash
# 이 주제의 모든 스크립트를 두 판으로 돌려 한 글자라도 다른지 본다.
# 쓰는 법: ./js01b-vdiff.sh <주제번호>
set -u -o pipefail
N18=node                                        # v18.19.1 (기본 PATH)
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"  # v20.19.6 (nvm)
printf '%-34s %s\n' "script" "node v18.19.1 대 v20.19.6"
printf '%-34s %s\n' "----------------------------------" "-------------------------"
for f in js01b-"$1"*.js; do
  case "$f" in *-browser.js|*-forms.js) continue;; esac   # 브라우저용·형태만 모은 것은 뺀다
  a=$("$N18" "$f" 2>&1); b=$("$N20" "$f" 2>&1)
  if [ "$a" = "$b" ]; then printf '%-34s 같다 (한 글자도)\n' "$f"
  else printf '%-34s ★ 다르다 — 다른 줄 %s개\n' "$f" "$(diff <(printf '%s\n' "$a") <(printf '%s\n' "$b") | grep -c '^[<>]')"
  fi
done
```

```text
===== ./js01b-vdiff.sh 03 (exit=0) =====
script                             node v18.19.1 대 v20.19.6
---------------------------------- -------------------------
js01b-03a-float.js                 같다 (한 글자도)
js01b-03b-safe-integer.js          같다 (한 글자도)
js01b-03c-nan-zero.js              같다 (한 글자도)
js01b-03d-bigint-mix.js            같다 (한 글자도)
js01b-03e-rounding.js              같다 (한 글자도)
js01b-03f-bitwise32.js             같다 (한 글자도)
```

```text
<!doctype html><meta charset="utf-8"><title>numbers in the browser</title>
<p>이 페이지는 값을 찍기만 한다.</p>
<pre id="out"></pre>
<script src="js01b-03g-browser.js"></script>
```

```js
// js01b-03g-browser.js
const rows = [
  ["엔진",                       navigator.userAgent.replace(/^.*(Chrome\/[\d.]+).*$/, "$1")],
  ["0.1 + 0.2",                  0.1 + 0.2],
  ["(0.1+0.2).toFixed(20)",      (0.1 + 0.2).toFixed(20)],
  ["Number.MAX_SAFE_INTEGER",    Number.MAX_SAFE_INTEGER],
  ["MAX_SAFE_INTEGER + 1 === +2", Number.MAX_SAFE_INTEGER + 1 === Number.MAX_SAFE_INTEGER + 2],
  ["(2.675).toFixed(2)",         (2.675).toFixed(2)],
  ["(2.5).toFixed(0)",           (2.5).toFixed(0)],
  ["Math.round(-2.5)",           Math.round(-2.5)],
  ["Math.round(0.49999999999999994)", Math.round(0.49999999999999994)],
  ["1e21 | 0",                   1e21 | 0],
  ["String(-0)",                 String(-0)],
  ["Object.is(-0, 0)",           Object.is(-0, 0)],
  ["1n + 1 의 예외",              (() => { try { return eval("1n + 1"); } catch (e) { return e.constructor.name + ": " + e.message; } })()],
  ["typeof 1n",                  typeof 1n],
];
document.getElementById("out").textContent =
  rows.map(([k, v]) => k.padEnd(36) + " : " + String(v)).join("\n");
```

```text
===== google-chrome --headless --disable-gpu --no-sandbox --dump-dom js01b-03g-browser.html 2>/dev/null | sed -n '/^<pre id="out">/,/<\/pre>/p' (exit=0) =====
<pre id="out">엔진                                   : Chrome/151.0.0.0
0.1 + 0.2                            : 0.30000000000000004
(0.1+0.2).toFixed(20)                : 0.30000000000000004441
Number.MAX_SAFE_INTEGER              : 9007199254740991
MAX_SAFE_INTEGER + 1 === +2          : true
(2.675).toFixed(2)                   : 2.67
(2.5).toFixed(0)                     : 3
Math.round(-2.5)                     : -2
Math.round(0.49999999999999994)      : 0
1e21 | 0                             : -559939584
String(-0)                           : 0
Object.is(-0, 0)                     : false
1n + 1 의 예외                          : TypeError: Cannot mix BigInt and other types, use explicit conversions
typeof 1n                            : bigint</pre>
```

그림 해설.

- **여섯 스크립트가 두 판에서 한 글자도 같았고**, Chrome 151 도 같은 답을 냈다.
- ★★★ **여기서 「같았다」는 다른 주제보다 강한 뜻**이다 — 부동소수점 연산이 **비트 단위로 규정**돼 있어
  **엔진이 고를 여지가 아예 없다.** ★ 그래도 **보장의 근거는 명세**이지 이 관찰이 아니다.
- ★★ **Chrome 과 Node 는 같은 V8** 이라 「다른 엔진에서도 같다」의 근거는 못 된다.
  다만 **IEEE 754 를 따르는 어떤 엔진에서도 같아야 한다**는 것은 명세가 말해 준다.
- ★ 브라우저 블록에 **`1n + 1` 의 예외 문구**를 넣어 두었다 — 문구까지 같았다.

## 문법 — 형태와 규칙

**형태 — 이것이 전부다.** 출력이 없는 파일이라 `--check` 로 문법만 확인했다(「진단 0줄」도 블록으로 싣는다).

```js
// js01b-03x-forms.js
// 형태만 모아 둔 파일 — 출력은 없다. `node --check` 로 문법만 확인한다.
const n = 1.5, big = 10n;

Number.MAX_SAFE_INTEGER;      // 9007199254740991 — 여기까지만 정수가 유일하다
Number.EPSILON;               // 1 과 그다음 double 사이의 거리
Number.isInteger(n);          // 정수인가
Number.isSafeInteger(n);      // 정수이면서 안전 범위인가 — 다른 질문이다
Number.isNaN(n);              // ★ 전역 isNaN 과 다르다(전역은 먼저 숫자로 바꾼다)
Object.is(n, -0);             // -0 을 가리는 법. 1 / n === -Infinity 도 같은 답

n.toFixed(2);                 // ★ 문자열을 돌려준다. 0 에서 먼 쪽으로 반올림
n.toPrecision(3);             // 유효숫자 기준
Math.round(n);                // ★ 큰 쪽으로 반올림 — 음수에서 toFixed 와 갈린다
Math.trunc(n);                // 0 쪽으로 버린다

big + 1n;                     // BigInt 끼리만 된다
Number(big) + 1;              // 섞으려면 한쪽을 바꾼다 — 큰 값은 정밀도를 잃는다
BigInt(1);                    // 정수만 받는다. 1.5 는 RangeError
big == 1;                     // ★ 느슨한 비교는 된다
big === 1;                    // ★ 엄격 비교는 언제나 false (타입이 다르다)

n | 0;                        // ★ 32비트로 자른다. 3000000000 이 음수가 된다
n >>> 0;                      // 부호 없는 32비트
Math.trunc(n);                // 32비트 한계 없이 정수로 — 이것이 안전한 쪽
```

```text
===== node20 --check js01b-03x-forms.js (exit=0) =====

```

규칙은 아홉이다.

1. **수 타입은 둘**이다 — `Number`(IEEE 754 배정밀도)와 `BigInt`(임의 정밀도 정수).
2. **`Number` 에는 정수 타입이 따로 없다.** 정수도 실수와 같은 상자에 담긴다.
3. **안전 정수는 `2**53 - 1` 까지**다. 그 너머에서는 서로 다른 정수가 같은 값이 된다.
4. **넘치면 예외가 아니라 `Infinity`**, 정의되지 않으면 `NaN` 이다. **`Number` 의 나눗셈은 안 터진다.**
5. **`NaN` 은 자기 자신과도 다르다.** `Number.isNaN` 과 전역 `isNaN` 은 **다른 함수**다.
6. **`-0` 은 `===`·`String`·`JSON` 으로는 안 보이고 `Object.is` 와 `1 / x` 로만 보인다.**
7. **`BigInt` 와 `Number` 의 산술은 전부 `TypeError`** 다. 비교는 되고, **문자열과의 `+` 만 통과**한다.
8. **`toFixed` 는 0 에서 먼 쪽, `Math.round` 는 큰 쪽**으로 반올림한다. 음수에서 갈린다.
9. **비트 연산자는 32비트로 자른다.** `>>>` 만 부호 없이 읽고, **`BigInt` 에는 `>>>` 가 없다.**

## 어디서 틀리나

### (1) ★★★ 돈을 소수로 더한다

`0.1 + 0.2` 가 그대로 나온다. **원 단위 정수**로 다루거나 정수 기반 십진 라이브러리를 쓴다.
`toFixed` 로 덮으면 화면만 맞고 누적 오차는 남는다.

### (2) ★★★ 64비트 ID 를 `JSON.parse` 로 받는다

`9007199254740993` 이 `...992` 가 된다. **예외도 경고도 없다.**
서버와 **문자열로 주고받는다** — `BigInt` 를 쓰더라도 경계에서는 문자열이다.

### (3) ★★ `Number.isInteger` 로 큰 정수를 방어한다

`2**53` 도 `1e21` 도 정수다. **`Number.isSafeInteger`** 를 써야 한계를 본다.

### (4) ★★ 전역 `isNaN` 을 쓴다

`isNaN("abc")` 가 참이다 — **먼저 숫자로 바꾸기** 때문이다.
「이 값이 `NaN` 인가」를 물으려면 `Number.isNaN` 이나 `x !== x` 다.

### (5) ★★ `x === NaN` 으로 거른다

**언제나 거짓**이다. `NaN` 은 자기 자신과도 다르다.

### (6) ★★ `-0` 을 `0` 으로 본다

`Math.round(-0.4)` 가 `-0` 이고 화면에는 `0` 으로 보인다.
나중에 `1 / x` 를 하면 `-Infinity` 가 나온다. **로그로는 절대 못 찾는다.**

### (7) ★★★ `id | 0` 이나 `~~id` 로 「정수로 만든다」

**32비트를 넘으면 부호까지 바뀐다.** `3000000000 | 0` 이 `-1294967296` 이다.
`Math.trunc` 를 쓴다.

### (8) ★★ `toFixed` 의 반올림을 「함수 버그」로 읽는다

`(1.005).toFixed(2)` 가 `1.00` 인 것은 **저장된 값이 `1.00499…`** 이기 때문이다.
함수를 바꿔도 안 고쳐진다 — **값 자체가 그렇다.**

### (9) ★★ `toFixed` 의 결과를 숫자로 쓴다

**문자열**이다. `(1.5).toFixed(2) + 1` 이 `"1.501"` 이다.

### (10) ★★ `BigInt` 를 기존 코드에 섞어 넣는다

`Math` 도 `JSON` 도 못 쓰고 산술이 전부 `TypeError` 다.
**경계를 정해 놓고** 그 안에서만 쓴다.

### (11) ★ `1n === 1` 이 참일 거라 본다

**타입이 다르므로 언제나 거짓**이다. `1n == 1` 은 참이다 — 02번 격자에서 본 자리다.

### (12) ★ 「부동소수점은 다 부정확하다」로 외운다

`0.5`·`0.25`·`2**53` 은 **정확하다.** 부정확한 것은 **2 의 거듭제곱 분모로 못 쓰는 소수**와 **안전 범위 밖 정수**다.

## 구현 세부사항 대 언어 보장

세 층으로 가른다. ★★★ **이 주제는 수치가 본체인데 그 수치가 전부 명세 칸**이다 — IEEE 754 가 비트까지 정해 놓았다.

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **명세(ECMA-262 + IEEE 754) 보장** | 어느 엔진에서도 같아야 하는 것 | 기준 소스 + 실행으로 재확인 |
| **엔진(V8) 구현** | V8 이 그렇게 하는 것 | 두 판 대조 + Chrome 151 |
| **이 판의 관찰** | 이 판에서 그랬을 뿐 | 「관찰」로 명기 |

### 명세 보장

| 사실 | 어떻게 확인했나 |
|---|---|
| `Number` 는 **IEEE 754 배정밀도**다 | `toFixed(20)` 으로 저장값을 본 것 |
| **`0.1 + 0.2` 의 정확한 값** `0.30000000000000004` | 실행 + 저장값 대조 |
| **`Number.EPSILON`·`MAX_SAFE_INTEGER`·`MAX_VALUE` 의 값** | 상수를 찍음 |
| **`2**53 === 2**53 + 1`** | 실행 |
| 넘치면 **`Infinity`**, `0/0` 은 **`NaN`** — 예외가 아니다 | 실행 |
| **`1n / 0n` 은 `RangeError`** — BigInt 는 터진다 | 실행 |
| **`NaN !== NaN`** 이고 `Object.is(NaN, NaN)` 은 참 | 실행 |
| **`String(-0)` 이 `"0"`**, `Object.is(-0, 0)` 이 거짓, `1 / -0` 이 `-Infinity` | 실행 |
| **BigInt 와 Number 의 산술은 `TypeError`**, 비교는 되고, **문자열 `+` 만 통과** | 전수로 던짐 |
| **단항 `+` 는 BigInt 에 못 쓴다** | 실행 |
| **`toFixed` 는 0 에서 먼 쪽, `Math.round` 는 큰 쪽** | 일곱 값을 던져 대조 |
| **`Math.round(0.49999999999999994)` 가 `0`** — 명세가 이 자리를 따로 규정한다 | 실행 |
| **비트 연산자는 32비트로 자르고 시프트 횟수는 32 로 나눈 나머지** | 전수로 던짐 |
| **BigInt 에는 `>>>` 가 없다** | 실행(전용 메시지) |

### 엔진(V8) 구현

| 사실 | 어떻게 확인했나 |
|---|---|
| 여섯 스크립트가 **두 판에서 한 글자도 같았다** | `js01b-vdiff.sh 03` |
| Chrome 151 이 **Node 20 과 같은 답**을 냈다 | 같은 식을 양쪽에서 던짐 |
| **`console.log(-0)` 이 `-0` 으로 보이는 것** | Node 의 표시 규칙이다 — `String(-0)` 은 `"0"` 이다 |

★ 마지막 줄이 이 절의 안전선이다 — **같은 값을 어떻게 보여 줄지는 런타임의 재량**이다.

### 이 판의 관찰

| 관찰 | 어디가 흔들리나 |
|---|---|
| 예외 **문구** — `Cannot mix BigInt and other types, use explicit conversions` 등 | **종류는 명세**, 문구는 V8 의 것이다 |
| `console.log` 가 `-0` 을 `-0` 으로 찍는 것 | Node 의 `util.inspect` 규칙이다 |
| UA 가 `Chrome/151.0.0.0` 인 것 | 브라우저가 축약한 값이다 |

### 그래서 이렇게 적으면 틀린다

- ✗ 「`0.1 + 0.2 !== 0.3` 은 JS 의 버그다」
  ○ **IEEE 754 를 쓰는 모든 언어에서 같다.** 파이썬도 자바도 C 도 같은 값이다.
- ✗ 「JS 에는 정수 타입이 없다」
  ○ **`BigInt` 가 정수 타입**이다(ES2020). 없는 것은 **고정 폭 정수**다.
- ✗ 「부동소수점은 다 부정확하다」
  ○ `0.5`·`0.25`·`2**53` 은 **정확하다.**
- ✗ 「`toFixed` 는 반올림이 틀렸다」
  ○ **값이 그렇다.** `(1.005).toFixed(20)` 을 찍어 보면 `1.00499…` 다.
- ✗ 「`toFixed` 와 `Math.round` 는 같은 반올림이다」
  ○ **음수에서 갈린다.** `-2.5` 가 `-3` 과 `-2` 로 나뉜다.
- ✗ 「`x | 0` 은 정수로 만드는 빠른 방법이다」
  ○ **32비트로 자른다.** 30억에서 음수가 된다.
- ✗ 「`BigInt` 와 `Number` 는 아예 안 섞인다」
  ○ **비교는 되고 문자열 `+` 도 된다.** 막힌 것은 산술이다.
- ✗ 「`console.log(-0)` 이 `-0` 이니 `-0` 은 화면에 보인다」
  ○ **Node 의 표시 규칙**이다. `String(-0)` 은 `"0"` 이고 그쪽이 명세다.

**판정 기준 한 줄**: 어떤 코드가 **큰 정수나 소수를 `===` 로 비교하거나 비트 연산에 넣고 있으면** 그 자리는 한계를 확인해야 하는 자리다.

## 언제 쓰고 언제 안 쓰나

| 쓰는 것 | 상황 |
|---|---|
| `Number` | **기본값.** 안전 범위 안의 정수와 보통의 실수 |
| `BigInt` | **`2**53` 을 넘는 정수가 정확해야** 할 때. 암호·큰 ID 계산 |
| 정수로 환산 | **돈**. 원·센트 단위 정수로 다룬 뒤 화면에서만 나눈다 |
| `Number.isSafeInteger` | 바깥에서 온 정수를 **받을 때 검사** |
| `Number.isNaN` / `x !== x` | `NaN` 판별 |
| `Object.is(x, -0)` / `1 / x === -Infinity` | `-0` 판별 |
| `Math.trunc` | 정수 부분만 필요할 때 — **32비트 한계가 없다** |
| `Math.abs(a - b) < 허용오차` | 소수 비교. **허용오차는 값의 크기에 맞춰** 잡는다 |

**안 쓰는 자리**는 넷이다.
**돈을 `Number` 소수로 더하지 마라.**
**64비트 ID 를 `Number` 로 받지 마라** — 문자열로 주고받는다.
**`x | 0`·`~~x` 로 정수 변환을 하지 마라** — 32비트를 넘으면 조용히 틀린다.
**`toFixed` 로 부동소수점 문제를 덮지 마라** — 화면만 맞고 값은 그대로다.

## 핵심 문장

- **JS 의 수 타입은 둘이고, 오래 쓰던 하나가 IEEE 754 배정밀도다.** 정수 타입이 따로 없다는 것이 이 주제의 뿌리다.
- **화면에 보이는 숫자는 저장된 값이 아니다.** `toFixed(20)` 이 그것을 걷어 내는 창이다.
- **안전 정수는 `2**53 - 1` 까지**이고, 그 너머에서는 **다른 두 정수가 한 값**이 된다.
- **넘쳐도 0 으로 나눠도 예외가 안 난다** — `Infinity` 와 `NaN` 이 값으로 나온다. **`BigInt` 만 터진다.**
- **`-0` 은 `===`·`String`·`JSON` 으로 안 보인다.** `Object.is` 와 `1 / x` 로만 보인다.
- **`BigInt` 는 섞이지 않는다 — 문자열 `+` 하나만 빼고.** 막은 것이지 못 한 것이 아니다.
- **비트 연산은 32비트로 자른다.** 숫자가 64비트인데도 그렇다 — **이 주제에서 가장 조용한 사고**다.

## 관련 자료

- 목록: [js/syntax 주제 목록](../README.md) — 이 주제는 **03번**
- 선행: [01 — 값의 종류와 `typeof`](../01-value-types-and-typeof/2-summary.md) — `typeof NaN` 이 `"number"` 인 것, `"bigint"` 가 별도 칸인 것.
- 선행: [02 — 강제 변환과 `==` 대 `===`](../02-coercion-and-loose-equality/2-summary.md) — **`0n == 0` 은 참인데 `0n === 0` 은 거짓**인 것의 격자.
  **경계**: 그쪽은 「타입이 섞일 때 표를 어떻게 읽나」까지, 여기는 「**그 표의 BigInt 줄이 왜 그렇게 생겼나**」부터다.
- 이어지는 곳: [04 — 문자열과 UTF-16](../04-strings-and-utf16/2-summary.md) — 큰 ID 를 문자열로 주고받을 때 그 문자열이 무엇인가.
- 이어지는 곳: 목록의 **33번 주제** 「동등성 세 종류」 — `NaN`·`±0` 에서 네 규칙이 갈리는 것의 정본.
- 이어지는 곳: [목록의 **31번 주제**](../31-json/) 「`JSON`」 — `BigInt` 직렬화 실패와 큰 수 파싱의 정본.
- 이어지는 곳: 목록의 **50번 주제** 「`Intl` 국제화 포맷」 — **금액을 화면에 찍는** 제대로 된 방법.
- 기존 노트: [`cs/foundations/data-representation/`](../../../../data-representation/) — 부동소수점의 **원리**(부호·지수·가수의 비트 배치).
  **경계**: 그쪽은 「비트가 어떻게 생겼나」까지, 여기는 「**JS 의 수 타입이 그것 하나라는 사실이 코드에서 무엇을 만드나**」부터다.
- 경계 — 다른 언어의 같은 자리: [`python/syntax/04-numeric-types-and-division`](../../../python/syntax/04-numeric-types-and-division/2-summary.md) —
  ★ **가장 날카로운 대비**다. 파이썬은 **정수에 한계가 없고**(임의 정밀도가 기본), `/` 와 `//` 가 나뉘어 있으며,
  `decimal`·`fractions` 가 표준 라이브러리에 있다. JS 는 **`BigInt` 를 나중에 덧붙였고 기본은 여전히 double** 이다.
- 연혁은 여기가 아니다: [`history/js/`](../../../../../../history/js/) — `BigInt` 가 ES2020 에 들어온 경위.

## 용어 풀이

- **IEEE 754 배정밀도(double)**: 64비트에 부호 1·지수 11·가수 52 비트를 담는 실수 표현. JS 의 `Number` 가 전부 이것이다.
- **안전 정수(safe integer)**: 다른 정수와 값이 겹치지 않는 정수. `-(2**53 - 1)` 부터 `2**53 - 1` 까지다.
- **`Number.EPSILON`**: `1` 과 그다음 double 사이의 거리(`2.22e-16`). **모든 값에서의 오차 한계가 아니다** — 값이 커지면 간격도 커진다.
- **`NaN` (Not a Number)**: 「수가 아님」을 나타내는 `Number` 값. **자기 자신과도 다르다.** `typeof` 는 `"number"` 다.
- **`Infinity`**: 넘쳤거나 0 으로 나눈 결과. 예외가 아니라 **값**이다.
- **`-0`**: 음의 영. `===` 로는 `0` 과 같고 `Object.is` 로는 다르다. `1 / -0` 이 `-Infinity` 라서 들킨다.
- **`BigInt`**: 임의 정밀도 정수 타입(ES2020). 리터럴 끝에 `n` 을 붙인다. **`Number` 와 산술로 못 섞는다.**
- **`ToInt32` / `ToUint32`**: 비트 연산자가 피연산자를 32비트 정수로 자르는 절차. `>>>` 만 뒤엣것을 쓴다.
- **가장 짧은 표기(shortest round-trip representation)**: 다시 읽으면 같은 double 이 되는 가장 짧은 십진 문자열.
  `console.log` 가 보여 주는 것이 이것이라 **저장된 값과 다르게 보인다.**

## 더 들어가면

- **`Number.EPSILON` 을 고정 허용오차로 쓰면 큰 수에서 틀린다.** 눈금 간격이 값에 비례해 커지므로
  `Math.abs(a - b) < Number.EPSILON * Math.max(Math.abs(a), Math.abs(b))` 같은 **상대 오차**가 필요하다.
  이 문서에서는 상대 오차 쪽을 던지지 않았다.
- **`Math.round` 가 `floor(x + 0.5)` 가 아닌 이유**가 명세에 따로 적혀 있다 — 그래서 `0.49999999999999994` 가 `0` 이다.
  **구현 재량이 아니라 규정**이다.
- **`0.1 + 0.2 !== 0.3` 은 JS 만의 일이 아니다.** IEEE 754 를 쓰는 모든 언어가 같다 —
  다만 파이썬은 `decimal` 을, 자바는 `BigDecimal` 을 **표준으로** 갖고 있고 JS 는 없다.
  ECMA-402 의 `Intl.NumberFormat` 이 **표시**는 해결해 주지만 **계산**은 아니다.
- **십진 소수 제안(Decimal)이 TC39 에 있다.** 아직 확정 전이라 이 머신에서 실행 검증이 불가하고, 이 문서에서는 다루지 않았다.
- **`BigInt` 의 나눗셈이 0 쪽으로 버리는 것**은 C 계열의 정수 나눗셈과 같다. 파이썬의 `//` 는 **아래로** 버려서 음수에서 갈린다.
  이 문서에서는 파이썬을 던지지 않았다 — 형제 문서를 링크만 했다.
