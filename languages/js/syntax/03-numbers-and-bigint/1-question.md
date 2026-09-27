# js/syntax/03 — 숫자와 `BigInt`: 「수 타입이 하나뿐이라는 것」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v18.19.1(기본 PATH) · v20.19.6(nvm) · Google Chrome 151.0.7922.173 · x86-64 Linux.
>
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① **화면에 보이는 숫자와 저장된 값이 다르다** ② **정수는 어디까지 믿을 수 있나** ③ **`BigInt` 는 어디서 막히고 어디서 새나**.
> ★★★ **수치를 답해야 하는 문항이 많다.** 이 주제의 수치는 **전부 안 흔들린다** — 비트까지 규정돼 있기 때문이다.
> ★★ **예외는 타입과 메시지로만 답한다** — 이 문서의 블록에는 스택트레이스가 한 줄도 없다.
> ★ **`console.log` 가 보여 주는 것과 `toFixed(20)` 이 보여 주는 것을 갈라 적어라.**
>
> **선행** — [01 — 값의 종류와 `typeof`](../01-value-types-and-typeof/2-summary.md) ·
> [02 — 강제 변환과 `==` 대 `===`](../02-coercion-and-loose-equality/2-summary.md)(**`0n == 0` 격자**).

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1·2·3·4·5·6)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **1번은 「보이는 값」이 아니라 「저장된 값」을 적어야** 답이다.
- ★★★ **4번은 「터진다/안 터진다」를 스물몇 줄에 대해 가려야** 답이다. 구멍이 하나 있다.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이것이 JS 만의 일인가 IEEE 754 를 쓰는 모든 언어의 일인가**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 같은 수를 두 가지로 찍으면 (예측) ★★★

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

- 다섯 묶음의 출력을 각각 적으면?
- ★★★ `0.1`·`0.2`·`0.3` 의 **저장된 값**은 각각 무엇인가? 셋이 끌려간 방향이 같은가?
- ★★★ `console.log(0.1)` 이 `0.1` 로 보이는데 저장된 값은 다른 이유는?
- ★★ `0.1 + 0.2 - 0.3` 은 무엇이고 `Number.EPSILON` 과 견주면?
- ★★ **결합 법칙이 깨지는 것**을 어느 줄이 보여 주는가? 실무에서 어디에 물리는가?
- ★ **정확히 저장되는 소수**가 있는가? 그 기준은?
- ★ 처방 한 줄은?

### 2. 정수의 한계 (예측) ★★★

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

- 다섯 묶음의 출력을 각각 적으면?
- ★★★ `M + 1 === M + 2` 는 무엇인가? **`M + 3` 에서는 어떤가**? 왜 그런가?
- ★★★ 소스에 `9007199254740993` 을 그대로 쳤는데 무엇이 찍히는가?
- ★★★ `JSON.parse('{"id":9007199254740993}')` 의 결과는? **경고가 있는가**?
- ★★ `Number.isInteger` 와 `Number.isSafeInteger` 는 어느 줄에서 갈리는가?
- ★ `Number.MAX_VALUE * 2` 는 무엇인가? 예외인가?
- ★ 큰 ID 를 다루는 **실무 답**은 무엇인가?

### 3. 숫자인데 숫자가 아닌 값들 (예측) ★★★

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

- 다섯 묶음의 출력을 각각 적으면?
- ★★★ `1 / 0` 과 `1n / 0n` 이 갈리는 이유는?
- ★★★ `Number.isNaN("abc")` 와 `isNaN("abc")` 가 다른 이유는?
- ★★★ `-0` 이 **드러나는 자리 둘**과 **안 드러나는 자리 셋**을 각각 대면?
- ★★ `[4]` 의 일곱 줄 중 **`-0` 을 만드는 것은 몇 개**인가?
- ★★ `[5]` 에서 **세 동등성이 갈리는 칸은 몇 개**이고 어디인가?
- ★ `[NaN].indexOf(NaN)` 과 `[NaN].includes(NaN)` 이 다른 이유는?

### 4. `BigInt` 를 섞으면 (예측) ★★★ 본체

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

- 다섯 묶음의 출력을 각각 적으면?
- ★★★ `[1]` 에서 **터지지 않는 줄이 하나** 있다 — 어느 것이고 왜인가?
- ★★★ `[2]` 는 왜 전부 통과하는가? 이것을 **「구멍」이라 부를 수 있나**?
- ★★★ `1n == 1` 과 `1n === 1` 이 다른 이유는? `new Set([1n, 1]).size` 는?
- ★★ `BigInt(1.5)` 와 `BigInt("1.5")` 의 **예외 종류가 다른** 이유는?
- ★★ `BigInt("")` 와 `BigInt(null)` 은 각각 무엇인가?
- ★★ `JSON.stringify(1n)` 은? 그 사실이 실무에 무엇을 강제하는가?
- ★ `5n / 2n` 과 `-5n / 2n` 은? 어느 쪽으로 버리는가?

### 5. 반올림 (예측) ★★★

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

- 네 묶음의 출력을 각각 적으면?
- ★★★ `(1.005).toFixed(2)` 가 `1.00` 인 이유를 **같은 블록의 어느 칸**이 설명하는가?
- ★★★ `toFixed(0)` 과 `Math.round` 가 **갈리는 줄**은 어느 것인가? 양수만 보면 어떻게 되는가?
- ★★★ `Math.round(0.49999999999999994)` 는 무엇인가? `floor(x + 0.5)` 였다면?
- ★★ `(1.5).toFixed(2) + 1` 은 무엇인가? 왜 그런가?
- ★ `(1e21).toFixed(2)` 는? `toFixed(101)` 은?

### 6. 비트 연산 (예측) ★★★

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

- 다섯 묶음의 출력을 각각 적으면?
- ★★★ `1e21 | 0` 이 `-559939584` 인 이유를 설명하면?
- ★★★ `1 << 32` 가 `1` 인 이유는? `1 << -1` 은?
- ★★ `-1 >>> 0` 과 `-1 >> 0` 이 다른 이유는?
- ★★ **`BigInt` 에 `>>>` 가 없는** 이유는? 예외 메시지는?
- ★★★ `id | 0` · `~~id` · `id >>> 0` · `Math.trunc(id)` 를 30억에 던지면 각각 무엇인가?
- ★ 그래서 **안전한 쪽**은 어느 것인가?

### 7. 두 판과 브라우저 (경계) ★

- 여섯 스크립트에서 **갈린 것이 있는가**?
- ★★ 이 주제에서 「같았다」가 **다른 주제보다 강한 뜻**을 갖는 이유는?
- ★★ 그래도 **보장의 근거**는 무엇인가?
- ★ Chrome 과 Node 가 같은 답을 낸 것으로 **무엇을 말할 수 없는가**?

### 8. 보장인가 사정인가 (연결) ★★★ 이 갈래의 축

- ★★★ 이 주제에서 **명세 보장** 칸에 들어가는 것 다섯을 대면?
- ★★★ **`console.log(-0)` 이 `-0` 으로 보이는 것**은 어느 칸인가? `String(-0)` 은?
- ★★ **이 판의 관찰** 칸에는 무엇이 들어가는가?
- ★★ 이 주제의 수치가 **안 흔들리는 이유**는?
- ★ 「측정」이 아니라 「계산」이라는 말이 무엇을 뜻하는가?

### 9. 경계 — 어디까지가 이 주제인가 (연결) ★★

- **부동소수점의 비트 배치** · **동등성 세 종류** · **`JSON` 직렬화** · **금액 표시**는 각각 어느 문서가 정본인가?
- ★★★ **파이썬의 수 타입과 어떻게 갈리는가**? 세 가지를 대면.
- ★★ `0n == 0` 은 어느 형제 주제에서 이미 봤는가?
- ★ 이 주제가 **끝까지 책임지는 것** 세 가지를 대면?

### 10. 이 갈래의 창 (연결) ★★

- ★★★ 이 주제에서 쓴 **창**은 무엇인가? 1번 절의 창을 특히.
- ★★ **`toFixed(20)` 을 옆 칸에 같이 찍은** 이유는?
- ★★ 이 문서에 **시간도 반복 횟수도 안 나오는** 이유는?
- ★ 이 주제에서 「**안 돌려 본 것**」은 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
