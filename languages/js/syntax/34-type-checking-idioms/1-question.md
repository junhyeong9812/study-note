# js/syntax/34 — 타입 검사 관용구: 「무엇을 보고 판정하나 · realm 을 넘으면 무엇이 남나」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v18.19.1(기본 PATH) · v20.19.6(nvm) · Google Chrome 151.0.7922.173(헤드리스) · x86-64 Linux.
> 배너의 `node20` 은 v20.19.6 이다. ★ **4번의 소스(`.web.js`)는 Chrome 에서만** 돌렸다.
>
> ★★★ **이 편은 정본 모음 편이다.** 1번은 **앞 편들에서 잰 것을 떠올리는** 문항이고, 2\~5번이 **이 편이 새로 잰 칸**(realm)이다.
> ★★★ **이 주제의 본체는 ② 전수 격자다** — 내장 타입 5 × 조건 5 × 판정 방법 5. **2번 문항이 이 주제의 중심이다.**
>
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① ★★★ **판정 방법마다 무엇을 보나**(사슬 · 출생 기록 · 자칭 · 모양)
> ② **realm · 프로토타입 조작 · 위조 앞에서 어느 방법이 틀리나**
> ③ **묻고 싶은 것마다 무엇을 골라야 하나.**
>
> **선행** — [15 — 프로토타입 체인](../15-prototype-chain/2-summary.md) · [16 — `class` 문법](../16-class-syntax/2-summary.md) · [17 — 상속과 `super`](../17-inheritance-and-super/2-summary.md) · [22 — `Symbol` 과 잘 알려진 심볼](../22-symbol-and-well-known-symbols/2-summary.md) · [32 — 오류 처리와 `Error`](../32-error-handling-and-error/2-summary.md).
> ★★★ **22번 4번의 위조 격자를 먼저 떠올려라** — `Symbol.toStringTag` 하나로 무엇이 바뀌었나.

## 이 파일을 푸는 법

- ★★ **예측형 네 문항(2 · 3 · 4 · 5)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **2번은 스물다섯 행 × 다섯 열의 칸마다 `y`/`n` 을 적고, 진실과 어긋나는 칸에 `*` 를 붙인 뒤** 방법별 · 조건별 수를 센다.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이것은 명세인가, 호스트(`vm`·iframe)의 것인가, 이 판의 관찰인가**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 앞 편들이 잰 판정 조각 (연결) ★★★

- ★★★ 15번에서 `instanceof` 는 무엇을 보았나? `static [Symbol.hasInstance]() { return true; }` 를 달면 `'a string' instanceof K2` 는?
- ★★★ 16번에서 `Object.create(Account.prototype)` 에 `instanceof Account` 와 `#balance in` 은 각각?
- ★★ 17번에서 `Array.call(this)` 로 만든 객체의 브랜드 · `Array.isArray` · `instanceof Array` 는?
- ★★ 22번에서 `Symbol.toStringTag` 는 브랜드 태그를 몇 칸 중 몇 칸 바꿨나?
- ★ 01번에서 `typeof null` 은?

### 2. 타입 다섯 × 조건 다섯 × 방법 다섯 — node `vm` (예측) ★★★ 이 주제의 축

```js
// js32b-34-h-realm-core.js
// 타입 검사 다섯 방법 x 진짜/가짜 다섯 조건 x 내장 타입 다섯 -- 칸마다 그 방법의 답이 「진짜인가」와 맞나.
// 「진짜」 = 그 타입의 생성자가 만든 것(내부 슬롯이 있다). 어느 realm 에서 만들었는지는 묻지 않는다.
// node(vm) 와 Chrome(iframe) 이 이 파일을 같이 쓴다 -- 다른 realm 을 만드는 법과 오류 슬롯 검사만 넘겨받는다.
globalThis.realmGrid = function realmGrid(otherEval, errorSlot, errorSlotName) {
  const tagOf = (v) => Object.prototype.toString.call(v);
  const noThrow = (f) => { try { f(); return true; } catch (e) { return false; } };
  const TYPES = [
    { name: "Array", C: Array, src: "[1, 2]",
      isX: (v) => Array.isArray(v),
      duck: (v) => typeof v.length === "number" && typeof v.push === "function",
      brand: null },
    { name: "Error", C: Error, src: "new Error('x')",
      isX: errorSlot,
      duck: (v) => typeof v.message === "string" && typeof v.name === "string",
      brand: null },
    { name: "Date", C: Date, src: "new Date(0)",
      isX: null,
      duck: (v) => typeof v.getTime === "function",
      brand: (v) => noThrow(() => Date.prototype.getTime.call(v)) },
    { name: "RegExp", C: RegExp, src: "/a/",
      isX: null,
      duck: (v) => typeof v.exec === "function",
      brand: (v) => noThrow(() => RegExp.prototype.exec.call(v, "")) },
    { name: "Promise", C: Promise, src: "Promise.resolve(1)",
      isX: null,
      duck: (v) => typeof v.then === "function",
      brand: (v) => noThrow(() => Promise.prototype.then.call(v, undefined, () => {})) },
  ];
  const CONDS = [
    ["same realm", true, (T) => (0, eval)(T.src)],
    ["other realm", true, (T) => otherEval(T.src)],
    ["proto swapped", true, (T) => Object.setPrototypeOf((0, eval)(T.src), Object.prototype)],
    ["Object.create(proto)", false, (T) => Object.create(T.C.prototype)],
    ["toStringTag forged", false, (T) => ({ [Symbol.toStringTag]: T.name })],
  ];
  const METHODS = [
    ["instanceof", (T, v) => v instanceof T.C],
    ["isArray/isError", (T, v) => (T.isX ? T.isX(v) : null)],
    ["toString tag", (T, v) => tagOf(v) === "[object " + T.name + "]"],
    ["duck typing", (T, v) => T.duck(v)],
    ["slot via method", (T, v) => (T.brand ? T.brand(v) : null)],
  ];
  console.log("[1] y/n = the method's answer to 'is this a genuine <type>?'   * = differs from the truth   - = no such method");
  console.log("    isArray/isError column for Error uses: " + errorSlotName);
  console.log("  " + "type".padEnd(9) + "condition".padEnd(22) + "truth".padEnd(7) + METHODS.map(([n]) => n.padEnd(17)).join("").trimEnd());
  const off = METHODS.map(() => 0), asked = METHODS.map(() => 0);
  const offByCond = CONDS.map(() => 0);
  for (const T of TYPES) {
    CONDS.forEach(([cname, truth, make], ci) => {
      const v = make(T);
      const cells = METHODS.map(([, m], mi) => {
        const a = m(T, v);
        if (a === null) return "-";
        asked[mi] += 1;
        if (a !== truth) { off[mi] += 1; offByCond[ci] += 1; return (a ? "y" : "n") + "*"; }
        return a ? "y" : "n";
      });
      console.log(("  " + T.name.padEnd(9) + cname.padEnd(22) + (truth ? "y" : "n").padEnd(7) + cells.map((c) => c.padEnd(17)).join("")).trimEnd());
    });
  }
  console.log("");
  console.log("  per method (cells that differ from the truth / cells asked):");
  METHODS.forEach(([n], i) => console.log("    " + n.padEnd(18) + off[i] + " / " + asked[i]));
  console.log("  per condition:");
  CONDS.forEach(([n], i) => console.log("    " + n.padEnd(22) + offByCond[i] + " / " + asked.reduce((a, b) => a + b, 0) / CONDS.length));
  console.log("cells that differ from the truth: " + off.reduce((a, b) => a + b, 0) + " / " + asked.reduce((a, b) => a + b, 0));
  console.log("");
  console.log("[2] not graded -- a Proxy with no traps around a genuine value (is a Proxy 'genuine'? the question has no single answer)");
  for (const T of TYPES) {
    const p = new Proxy((0, eval)(T.src), {});
    const cells = METHODS.map(([, m]) => { const a = m(T, p); return a === null ? "-" : a ? "y" : "n"; });
    console.log(("  " + T.name.padEnd(9) + "new Proxy(v, {})".padEnd(29) + cells.map((c) => c.padEnd(17)).join("")).trimEnd());
  }
};
```

```js
// js32b-34a-realm-grid.js
// 다른 realm = node:vm 의 새 컨텍스트. 오류 슬롯 검사는 Error.isError 가 없는 판이라 호스트 함수로 대신 묻는다.
const vm = require("node:vm");
const util = require("node:util");
require("./js32b-34-h-realm-core.js");
realmGrid((src) => vm.runInNewContext(src), (v) => util.types.isNativeError(v), "util.types.isNativeError (node host API)");
```

- ★★★ `[1]` 의 `other realm` 다섯 행 — 어느 열이 `*` 를 받나?
- ★★★ `proto swapped` 와 `Object.create(proto)` 행에서 `instanceof` 와 `duck typing` 열은?
- ★★★ `toString tag` 열에서 `*` 가 붙는 칸은 어디인가? `Promise` 행은 다른 타입과 같은가?
- ★★ 방법별 · 조건별 집계 줄과 마지막 줄의 수는?

### 3. 같은 소스의 `[2]` — 트랩 없는 `Proxy` (예측) ★★

- ★★★ `Array` 행과 `Error` 행의 둘째 열(`isArray/isError`)은 각각?
- ★★ `toString tag` 열이 `y` 인 행은?
- ★ `slot via method` 열은?

### 4. 같은 격자를 Chrome 151 iframe 에서 (예측) ★★★

```js
// js32b-34b-realm-grid.web.js
// 같은 격자를 Chrome 에서 -- 다른 realm = 같은 출처의 iframe. 오류 슬롯 검사는 Error.isError(ES2026).
const frame = document.createElement("iframe");
document.body.appendChild(frame);
realmGrid((src) => frame.contentWindow.eval(src), (v) => Error.isError(v), "Error.isError (ES2026)");
```

- ★★★ node 판과 다른 줄이 있나? 있다면 어느 줄인가?
- ★★ 마지막 줄의 수는?

### 5. 배열처럼 보이는 것들 (예측) ★★

```js
// js32b-34c-array-edges.js
// 배열처럼 보이는 것들 -- typeof · Array.isArray · instanceof Array · 브랜드 태그를 한 줄에.
const row = (label, v) => console.log(("  " + label.padEnd(30) + v.map((x) => String(x).padEnd(18)).join("")).trimEnd());
function argsOf() { return arguments; }
class List extends Array {}
console.log("  " + "".padEnd(30) + "typeof".padEnd(18) + "Array.isArray".padEnd(18) + "instanceof Array".padEnd(18) + "tag");
const items = [
  ["[1, 2]", [1, 2]],
  ["new List()", new List()],
  ["Array.prototype", Array.prototype],
  ["argsOf(1, 2)", argsOf(1, 2)],
  ["new Uint8Array(2)", new Uint8Array(2)],
  ["{ length: 0 }", { length: 0 }],
  ["'ab'", "ab"],
];
for (const [label, v] of items) {
  row(label, [typeof v, Array.isArray(v), v instanceof Array, Object.prototype.toString.call(v)]);
}
```

- ★★★ `Array.prototype` 행의 네 칸은?
- ★★ `argsOf(1, 2)` · `new Uint8Array(2)` 행의 브랜드는?
- ★ `typeof` 열에서 `"object"` 가 아닌 행은?

### 6. `instanceof` 는 사슬에서 무엇을 찾나 (왜) ★★★

- ★★★ `OrdinaryHasInstance` 는 사슬의 객체를 무엇과 무엇으로 견주나?
- ★★ 다른 realm 에서 만든 배열의 사슬에는 어느 `Array.prototype` 이 있나?
- ★★ 덕 타이핑은 다른 realm 의 값에서 무엇을 보게 되나?

### 7. `Object.prototype.toString` 은 명찰을 어디서 만드나 (왜) ★★

- ★★★ `Object.prototype.toString` 의 `builtinTag` 목록에는 무엇이 있고, 무엇이 없나?
- ★★ `Promise` 의 `[object Promise]` 는 어디에서 오나? 그래서 프로토타입을 바꾸거나 `Object.create` 하면?
- ★ 프록시로 감싼 `Promise` 의 태그 칸(3번)도 같은 까닭으로 설명되나?

### 8. 묻고 싶은 것마다 무엇을 쓰나 (연결) ★★★

- ★★★ 「배열인가」「오류인가」「`Date` 인가」「내 클래스가 만들었나」를 각각 무엇으로 묻나?
- ★★ `instanceof` 가 맞는 질문은 무엇인가?
- ★★ 덕 타이핑이 맞는 질문은? 언어 자신이 덕 타이핑을 쓰는 자리는?

### 9. 이 편이 확인하지 않은 것 (경계) ★★

- ★★ `vm.runInNewContext` 가 만든 것이 명세의 realm 과 같은 것인지 이 문서는 확인했나? 무엇을 관찰했나?
- ★★ node 판의 오류 슬롯 열은 어느 함수로 물었고, 그것은 ECMA-262 인가?
- ★ `Proxy` 자체 · 워커로 건너온 값은 목록의 몇 번 주제의 몫인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
