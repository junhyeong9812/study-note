# js/syntax/02 — 강제 변환과 `==` 대 `===`: 「엔진이 무엇을 먼저 부르나」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v18.19.1(기본 PATH) · v20.19.6(nvm) · Google Chrome 151.0.7922.173 · x86-64 Linux.
>
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① **`ToPrimitive` 가 무엇을 어느 순서로 부르나** ② **`==` 표의 이상한 칸이 어디서 오나** ③ **`==` 를 써도 되는 자리**.
> ★★★ **1번이 이 주제의 본체다** — 「어떤 값이 나오나」가 아니라 「**무엇이 먼저 불렸나**」를 적어야 답이다.
> ★★★ **3번은 225칸 격자다.** 전부 채울 필요는 없지만 **행 단위의 규칙**은 말할 수 있어야 한다.
> ★★ **예외는 타입과 메시지로만 답한다** — 이 문서의 블록에는 스택트레이스가 한 줄도 없다.
>
> **선행** — [01 — 값의 종류와 `typeof`](../01-value-types-and-typeof/2-summary.md)(원시 7종·falsy 목록·`document.all`).

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1·2·3·4·5·6)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **1번은 「부른 것」 칸을 적어야 답이다.** 결과값만 맞히면 절반이다.
- ★★★ **3번은 「참인 칸이 몇 개인가」와 「`===` 와 `Object.is` 가 갈리는 칸이 어디인가」를 적어야** 답이다.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이것은 표에 적힌 것인가 엔진이 고른 것인가**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 로그를 심은 객체를 연산자에 던지면 (예측) ★★★ 이 주제의 본체

```js
// js01b-02a-toprimitive-spy.js
// 객체를 원시 값으로 바꿀 때 엔진이 무엇을 어느 순서로 부르는지 로그로 찍는다.
// ★ 명세의 추상 연산(ToPrimitive)에는 이름이 없지만, 그것이 부르는 메서드에는 로그를 심을 수 있다.
function makeSpy({ valueOfResult, toStringResult, symbolResult }) {
  const log = [];
  const o = {
    valueOf()  { log.push("valueOf()");  return valueOfResult; },
    toString() { log.push("toString()"); return toStringResult; },
  };
  if (symbolResult !== undefined) {
    o[Symbol.toPrimitive] = (hint) => {
      log.push("[Symbol.toPrimitive](\"" + hint + "\")");
      return symbolResult;
    };
  }
  return [o, log];
}

function run(label, opts, use) {
  const [o, log] = makeSpy(opts);
  let out;
  try { out = String(use(o)); }
  catch (e) { out = e.constructor.name + ": " + e.message; }
  console.log("  " + label.padEnd(22) + " => " + out.padEnd(18) + " | 부른 것: " + (log.join(" -> ") || "(없음)"));
}

const N = { valueOfResult: 7, toStringResult: "S" };

console.log("[1] 힌트가 number 인 자리 — valueOf 가 먼저다");
run("o * 2",        N, (o) => o * 2);
run("o - 0",        N, (o) => o - 0);
run("o < 1",        N, (o) => o < 1);
run("Number(o)",    N, (o) => Number(o));
run("+o",           N, (o) => +o);

console.log("");
console.log("[2] 힌트가 string 인 자리 — toString 이 먼저다");
run("`${o}`",       N, (o) => `${o}`);
run("String(o)",    N, (o) => String(o));
run("({})[o] = 1",  N, (o) => { const t = {}; t[o] = 1; return Object.keys(t)[0]; });
run("[o] + ''",     N, (o) => [o] + "");

console.log("");
console.log("[3] 힌트가 default 인 자리 — 기본 객체는 number 처럼 군다");
run("o + 1",        N, (o) => o + 1);
run("o + 'x'",      N, (o) => o + "x");
run("o == 7",       N, (o) => o == 7);

console.log("");
console.log("[4] 첫 메서드가 원시 값을 안 돌려주면 다음 것을 부른다");
run("valueOf -> obj",   { valueOfResult: {}, toStringResult: "S" }, (o) => o + 1);
run("toString -> obj",  { valueOfResult: 7,  toStringResult: {} },  (o) => `${o}`);
run("both -> obj",      { valueOfResult: {}, toStringResult: {} },  (o) => o + 1);

console.log("");
console.log("[5] Symbol.toPrimitive 가 있으면 나머지 둘은 아예 안 불린다");
run("o + 1",        { ...N, symbolResult: 99 }, (o) => o + 1);
run("`${o}`",       { ...N, symbolResult: 99 }, (o) => `${o}`);
run("o * 2",        { ...N, symbolResult: 99 }, (o) => o * 2);
```

- 다섯 묶음의 **결과값**과 **부른 것** 칸을 각각 적으면?
- ★★★ `o + 1` 은 `valueOf` 와 `toString` 중 **무엇을 먼저** 부르는가? 왜 그런가?
- ★★★ `` `${o}` `` 와 `[o] + ''` 는 왜 같은 쪽을 부르는가?
- ★★★ `[4]` 의 셋째 줄은 **무엇을 몇 개 부른 뒤** 터지는가? 예외의 **타입과 메시지**는?
- ★★ `[5]` 에서 `valueOf` 는 **몇 번** 불렸는가?
- ★★ `Symbol.toPrimitive` 가 받은 **힌트 문자열 세 가지**는 무엇인가?
- ★ `o == 7` 이 `valueOf` 를 부르는 것은 `o + 1` 과 **같은 이유**인가?

### 2. `Date` 를 연산자에 던지면 (예측) ★★★

```js
// js01b-02b-date-hint.js
// Date 는 왜 반대로 구는가 — "valueOf 와 toString 의 순서가 바뀐 것" 이 아니다.
class Logged extends Date {
  valueOf()  { console.log("      valueOf() 가 불렸다");  return super.valueOf(); }
  toString() { console.log("      toString() 이 불렸다"); return super.toString(); }
}

console.log("[1] Date 는 무엇을 부르나");
const d = new Logged(0);
console.log("  d + 1   ->"); void (d + 1);
console.log("  d * 1   ->"); void (d * 1);
console.log("  d - 0   ->"); void (d - 0);
console.log("  `${d}`  ->"); void `${d}`;

console.log("");
console.log("[2] 그래서 같은 연산자가 타입을 다르게 낸다");
const plain = new Date(0);
console.log("  typeof (date + 1) :", typeof (plain + 1));
console.log("  typeof (date - 0) :", typeof (plain - 0));
console.log("  typeof ({} + 1)   :", typeof ({ valueOf: () => 1 } + 1));

console.log("");
console.log("[3] 진짜 이유 — Date 에는 제 Symbol.toPrimitive 가 있다");
console.log("  typeof Date.prototype[Symbol.toPrimitive] :", typeof Date.prototype[Symbol.toPrimitive]);
console.log("  typeof Object.prototype[Symbol.toPrimitive]:", typeof Object.prototype[Symbol.toPrimitive]);
const f = Date.prototype[Symbol.toPrimitive];
console.log('  hint "default" 로 직접 부르면 타입이 :', typeof f.call(plain, "default"));
console.log('  hint "number"  로 직접 부르면 타입이 :', typeof f.call(plain, "number"));
console.log('  hint "string"  로 직접 부르면 타입이 :', typeof f.call(plain, "string"));
let bad;
try { f.call(plain, "nope"); } catch (e) { bad = e.constructor.name + ": " + e.message; }
console.log('  hint "nope"    로 부르면 :', bad);
```

- 세 묶음의 출력을 각각 적으면?
- ★★★ 「`Date` 는 `valueOf`/`toString` 순서가 반대다」는 **어디가 틀렸는가**?
- ★★★ `Date.prototype[Symbol.toPrimitive]` 를 힌트 세 가지로 직접 부르면 **각각 어떤 타입**이 나오는가?
- ★★ 없는 힌트를 주면 무슨 일이 나는가? 그것이 무엇을 말해 주는가?
- ★★ `typeof (date + 1)` 과 `typeof (date - 0)` 이 다른 이유는?
- ★ `Object.prototype[Symbol.toPrimitive]` 는 있는가?

### 3. 225칸을 세 번 던지면 (예측) ★★★

```js
// js01b-02c-equality-grids.js
// == · === · Object.is 를 같은 15개 값으로 전수 대조한다. 한 격자가 225칸이다.
// ★ 값은 매번 새로 만든다(thunk) — 그래야 [] 끼리가 "다른 객체" 로 비교된다.
const V = [
  ["undef", () => undefined], ["null", () => null],
  ["false", () => false],     ["true", () => true],
  ["0", () => 0],             ["-0", () => -0],        ["1", () => 1],
  ['""', () => ""],           ['"0"', () => "0"],      ['"1"', () => "1"],
  ["NaN", () => NaN],
  ["[]", () => []],           ["[0]", () => [0]],      ["{}", () => ({})],
  ["0n", () => 0n],
];
const W = 6, C = 6;

function grid(title, cmp) {
  console.log("[" + title + "]  T = 참 · . = 거짓 · ! = 예외");
  console.log(" ".repeat(W) + V.map(([n]) => n.padStart(C)).join(""));
  let yes = 0, cells = 0, thrown = 0;
  for (const [an, af] of V) {
    let row = an.padEnd(W);
    for (const [, bf] of V) {
      let mark;
      try { mark = cmp(af(), bf()) ? "T" : "."; }
      catch { mark = "!"; thrown++; }
      if (mark === "T") yes++;
      cells++;
      row += mark.padStart(C);
    }
    console.log(row);
  }
  console.log("  " + cells + "칸 중 참 " + yes + "칸 · 예외 " + thrown + "칸");
  console.log("");
  return cells;
}

let total = 0;
total += grid("==",        (a, b) => a == b);
total += grid("===",       (a, b) => a === b);
total += grid("Object.is", (a, b) => Object.is(a, b));
console.log("던진 칸 합계: " + total);
```

- ★★★ 세 격자에서 **참인 칸의 개수**를 각각 적으면?
- ★★★ `===` 와 `Object.is` 가 **갈리는 칸은 몇 개**이고 어디인가?
- ★★★ `==` 격자에서 **가장 넓은 행**은 어느 것인가? 왜 그런가?
- ★★ `undefined` 와 `null` 의 두 행은 어떤 모양인가? 그것을 한 문장으로 하면?
- ★★ `[]` 열과 `[]` 행이 만나는 칸은 무엇인가? **`[] == 0` 과 왜 다른가**?
- ★★ `0n` 행은 어느 행과 똑같은가? `===` 격자에서는 어떤가?
- ★ **예외가 난 칸은 몇 개**인가? 그 사실이 왜 중요한가?
- ★ 값 목록을 **매번 새로 만드는 함수(thunk)** 로 둔 이유는?

### 4. 유명한 식들 (예측) ★★

```js
// js01b-02d-famous.js
// 유명한 식들을 "중간 단계까지" 찍어 한 줄씩 무너뜨린다.
const show = (expr, value, steps) =>
  console.log("  " + expr.padEnd(20) + " = " + String(value).padEnd(7) + " | " + steps);

console.log("[1] [] == false");
show("![]",        ![],        "ToBoolean([]) 은 true 라서 !true = false");
show("[] == false", [] == false, "false -> 0 · [] -> ToPrimitive -> '' -> 0");
show("[].toString()", JSON.stringify([].toString()), "빈 배열의 toString 은 빈 문자열");
show("Number('')",  Number(""),  "빈 문자열의 ToNumber 는 0");
show("[] == ![]",  [] == ![],   "오른쪽이 false 가 되므로 위와 같은 식이 된다");
show("[] == []",   [] == [],    "둘 다 객체라 ToPrimitive 를 안 하고 참조만 본다");

console.log("");
console.log("[2] null 과 undefined 는 서로만 같다");
for (const [e, v] of [["null == undefined", null == undefined], ["null === undefined", null === undefined],
                      ["null == 0", null == 0], ["null >= 0", null >= 0], ["null > 0", null > 0],
                      ["null <= 0", null <= 0], ["undefined == 0", undefined == 0], ["Number(null)", Number(null)],
                      ["Number(undefined)", Number(undefined)]])
  console.log("  " + e.padEnd(20) + " = " + v);

console.log("");
console.log("[3] NaN 은 자기 자신과도 다르다");
for (const [e, v] of [["NaN == NaN", NaN == NaN], ["NaN === NaN", NaN === NaN],
                      ["Object.is(NaN,NaN)", Object.is(NaN, NaN)], ["[NaN].includes(NaN)", [NaN].includes(NaN)],
                      ["[NaN].indexOf(NaN)", [NaN].indexOf(NaN)], ["new Set([NaN,NaN]).size", new Set([NaN, NaN]).size]])
  console.log("  " + e.padEnd(24) + " = " + v);

console.log("");
console.log("[4] + 는 한쪽이 문자열이면 문자열로 기운다 — 나머지는 안 그렇다");
for (const [e, v] of [["1 + '2'", 1 + "2"], ["1 - '2'", 1 - "2"], ["1 * '2'", 1 * "2"],
                      ["'3' + null", "3" + null], ["3 - null", 3 - null],
                      ["[1,2] + [3]", [1, 2] + [3]], ["{} + []", ({}) + []],
                      ["1 + 2 + '3'", 1 + 2 + "3"], ["'1' + 2 + 3", "1" + 2 + 3],
                      ["true + true", true + true], ["'b' + 'a' + +'a' + 'a'", "b" + "a" + +"a" + "a"]])
  console.log("  " + e.padEnd(24) + " = " + JSON.stringify(v));

console.log("");
console.log("[5] 관계 연산자는 문자열 둘이면 사전순이다");
for (const [e, v] of [["'10' < '9'", "10" < "9"], ["10 < 9", 10 < 9], ["'10' < 9", "10" < 9],
                      ["[] < [1]", [] < [1]], ["'a' < 'b'", "a" < "b"],
                      ["NaN < 1", NaN < 1], ["NaN >= 1", NaN >= 1]])
  console.log("  " + e.padEnd(24) + " = " + v);
```

- 다섯 묶음의 출력을 각각 적으면?
- ★★★ `[] == ![]` 가 참인 이유를 **두 규칙으로 쪼개면**?
- ★★★ `null == 0` 은 거짓인데 `null >= 0` 은 참인 이유는?
- ★★ `[NaN].includes(NaN)` 과 `[NaN].indexOf(NaN)` 이 갈리는 이유는? 규칙이 **몇 가지**인가?
- ★★ `1 + 2 + '3'` 과 `'1' + 2 + 3` 이 다른 이유는?
- ★ `'10' < '9'` 가 참인 이유는?
- ★ `NaN < 1` 과 `NaN >= 1` 이 **둘 다 거짓**인 이유는?

### 5. 세 방향으로 바꾸면 (예측) ★★

```js
// js01b-02e-conversion-table.js
// 같은 값을 세 방향으로 바꿔 본다 — ToNumber · ToString · ToBoolean.
// ★ "falsy 목록" 과 "== false 인 목록" 이 같지 않다는 것이 이 표의 요점이다.
// ★ Date 는 일부러 뺐다 — String(new Date(0)) 이 시간대·로캘에 달려 흔들리는 칸이기 때문이다.
const V = [
  ["undefined", undefined], ["null", null], ["true", true], ["false", false],
  ["0", 0], ["-0", -0], ["1", 1], ["NaN", NaN], ["Infinity", Infinity],
  ['""', ""], ['" "', " "], ['"0"', "0"], ['"12"', "12"], ['"0x10"', "0x10"],
  ['"1e3"', "1e3"], ['"12px"', "12px"], ['"Infinity"', "Infinity"],
  ["[]", []], ["[7]", [7]], ["[1,2]", [1, 2]], ["{}", {}],
  ["0n", 0n], ["1n", 1n],
];
const cell = (f) => { try { return String(f()); } catch (e) { return "!" + e.constructor.name; } };

console.log("value".padEnd(12) + "Number()".padEnd(14) + "String()".padEnd(24) +
            "Boolean()".padEnd(11) + "== false");
console.log("-".repeat(12 + 14 + 24 + 11 + 8));
let falsy = 0, eqFalse = 0;
for (const [label, v] of V) {
  const b = Boolean(v), e = cell(() => v == false);
  if (!b) falsy++;
  if (e === "true") eqFalse++;
  console.log(label.padEnd(12) +
              cell(() => Number(v)).padEnd(14) +
              JSON.stringify(cell(() => String(v))).padEnd(24) +
              String(b).padEnd(11) + e);
}
console.log("");
const falsyOnly  = V.filter(([, v]) => !Boolean(v) && !(v == false)).map(([n]) => n);
const eqFalseOnly = V.filter(([, v]) => Boolean(v) && (v == false)).map(([n]) => n);
const both        = V.filter(([, v]) => !Boolean(v) && (v == false)).map(([n]) => n);
console.log("falsy 인데 `== false` 는 거짓 :", falsyOnly.join(" "));
console.log("truthy 인데 `== false` 가 참   :", eqFalseOnly.join(" "));
console.log("둘 다 인 것                    :", both.join(" "));
console.log("");
console.log("★ 두 목록은 같지 않다. `if (x)` 와 `x == false` 는 다른 질문이다.");
```

- 표의 각 행을 적으면?
- ★★★ **falsy 목록과 `== false` 목록이 어긋나는 칸**은 각각 무엇인가?
- ★★ `"0x10"` 이 `16` 인 것은 `parseInt` 와 **같은가 다른가**?
- ★★ `" "`(공백 하나)이 `0` 인 것이 실무에서 어디서 물리는가?
- ★★ `[7]` 은 `7` 인데 `[1,2]` 는 `NaN` 인 이유는?
- ★ **`Date` 를 이 표에서 뺀 이유**는 무엇인가?

### 6. `==` 를 쓸 수 있는 자리가 있나 (예측) ★★

```js
// js01b-02f-loose-eq-safe.js
// == 를 써도 되는 좁은 자리 하나 — `x == null` 은 "null 이거나 undefined" 를 한 번에 묻는다.
const VALUES = [
  ["undefined", undefined], ["null", null], ["0", 0], ['""', ""],
  ["false", false], ["NaN", NaN], ["0n", 0n], ["[]", []], ["{}", {}],
];

console.log("value".padEnd(12) + "x == null".padEnd(12) +
            "x === null || x === undefined".padEnd(32) + "두 칸이 같은가");
console.log("-".repeat(12 + 12 + 32 + 14));
let same = true;
for (const [label, v] of VALUES) {
  const a = v == null, b = v === null || v === undefined;
  if (a !== b) same = false;
  console.log(label.padEnd(12) + String(a).padEnd(12) + String(b).padEnd(32) + (a === b ? "같다" : "★ 다르다"));
}
console.log("");
console.log("아홉 줄 전부 같은가:", same);

console.log("");
console.log("★ 그런데 `x == null` 과 `!x` 는 전혀 다른 질문이다");
console.log("value".padEnd(12) + "x == null".padEnd(12) + "!x".padEnd(8) + "x ?? 'D'".padEnd(12) + "x || 'D'");
console.log("-".repeat(12 + 12 + 8 + 12 + 10));
for (const [label, v] of VALUES.slice(0, 7))
  console.log(label.padEnd(12) + String(v == null).padEnd(12) + String(!v).padEnd(8) +
              String(v ?? "D").padEnd(12) + String(v || "D"));
```

- 두 표를 각각 적으면?
- ★★★ `x == null` 이 안전한 이유를 **표의 어느 줄로** 설명하는가?
- ★★★ `x == null` 과 `!x` 는 **몇 줄에서 갈리는가**?
- ★★ `??` 와 `||` 는 각각 위 둘 중 어느 편인가?
- ★ 그래서 `==` 에 대한 실무 규칙 한 줄은?

### 7. 두 판과 브라우저 (경계) ★

- 여섯 스크립트에서 **갈린 것이 있는가**?
- ★★ Chrome 과 Node 가 같은 답을 낸 것이 **「다른 엔진에서도 같다」의 근거가 되는가**? 왜인가?
- ★★ 브라우저에서만 나오는 세 줄은 무엇인가? 그것이 `==` 표에 무엇을 더하는가?
- ★ 「두 판에서 같았다」로 **주장할 수 있는 것**과 **없는 것**은?

### 8. 보장인가 사정인가 (연결) ★★★ 이 갈래의 축

- ★★★ 이 주제에서 **명세 보장** 칸에 들어가는 것 다섯을 대면?
- ★★★ **이 판의 관찰** 칸에는 무엇이 들어가는가?
- ★★ `==` 표가 **엔진마다 다를 수 있는가**? 675칸을 던져 무엇을 보였는가?
- ★★ `==` 는 예외를 던지는가? **정확히 답하면**?
- ★ 이 주제에서 「엔진 구현」 칸이 **얇은 이유**는?

### 9. 경계 — 어디까지가 이 주제인가 (연결) ★★

- **`??` 와 `||`** · **동등성 세 종류** · **`Symbol.toPrimitive` 자체** · **엄격 모드** 는 각각 어느 주제가 정본인가?
- ★★★ **TypeScript 갈래와 어떻게 갈리는가**? 한 문장으로.
- ★★ `0n == 0` 과 `'10' < '9'` 는 각각 어느 형제 주제로 이어지는가?
- ★ 이 주제가 **끝까지 책임지는 것** 세 가지를 대면?

### 10. 이 갈래의 창 (연결) ★★★

- ★★★ 이 주제에서 **새로 연 창**은 무엇인가? 다른 갈래에는 없는 것이다.
- ★★★ 「추상 연산은 이름으로 못 부른다」인데 **어떻게 관찰했는가**?
- ★★ 격자를 **손으로 채우지 않고 전수로 던진** 이유는?
- ★★ `Date` 를 변환표에서 뺀 것은 **어느 규칙**을 따른 것인가?
- ★ 이 주제에서 「**안 돌려 본 것**」은 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
