# js/syntax/33 — 동등성 세 종류: 「쓰는 곳마다 어느 자로 재나」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v18.19.1(기본 PATH) · v20.19.6(nvm) · Google Chrome 151.0.7922.173(헤드리스) · x86-64 Linux.
> 배너의 `node20` 은 v20.19.6 이다. ★ **3번의 소스(`.web.js`)는 Chrome 에서만** 돌렸다.
>
> ★★★ **이 편은 정본 모음 편이다.** 1번은 **앞 편들에서 잰 것을 떠올리는** 문항이고, 2\~4번이 **이 편이 새로 잰 칸**이다.
> ★★★ **이 주제의 본체는 ② 전수 격자** — 새 자리마다 **서명**(짝 여덟 개에 대한 `y`/`n` 여덟 글자)을 뽑아 기준 비교와 대조한다.
>
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① ★★★ **`NaN` 과 `-0` 두 행에서 네 알고리즘이 어떻게 갈리나**
> ② **언어의 어느 자리가 어느 알고리즘을 쓰나**
> ③ **비교가 저장까지 바꾸는 자리는 어디인가.**
>
> **선행** — [02 — 강제 변환과 `==` 대 `===`](../02-coercion-and-loose-equality/2-summary.md) · [23 — `Map`·`Set` 과 약한 컬렉션](../23-map-set-and-weak-collections/2-summary.md) · [26 — 배열 탐색·평탄화·생성](../26-array-search-flatten-and-create/2-summary.md).
> ★★★ **23번 1번의 여덟 × 여덟 격자를 먼저 떠올려라** — `Map` 키와 같은 답을 낸 열은 어느 것이었나.

## 이 파일을 푸는 법

- ★★ **예측형 세 문항(2 · 3 · 4)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **2번·3번은 열마다 여덟 글자의 서명을 먼저 적고**, 그것이 기준 넷 중 어느 것과 같은지 본다.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이것은 명세인가, 이 엔진(V8)의 사정인가, 이 판의 관찰인가**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 앞 편들이 잰 칸을 한 표로 (연결) ★★★ 이 주제의 축

- ★★★ `===` · `==` · `Object.is` · `Map` 키 · `includes` · `indexOf` 는 각각 `NaN, NaN` 과 `0, -0` 에서 「같다」·「다르다」 중 무엇인가?
- ★★★ 23번 격자에서 `Map` 키와 **여덟 답이 전부 같았던** 열은 어느 것이었나?
- ★★ 26번에서 `[0].indexOf(-0)` 과 `[-0].includes(0)` 은? 배열은 `-0` 을 그대로 담나?
- ★★ 02번의 225칸 격자에서 `===` 와 `Object.is` 가 갈린 칸은 몇 개이고 어디인가?

### 2. 23번이 안 물은 자리에 같은 짝을 던지면 — node 20 (예측) ★★★

```js
// js32b-33-h-equality-core.js
// 23번 격자와 같은 값의 짝 여덟 개를, 23번이 안 물은 자리들에 던진다.
// 자리마다 y/n 서명을 뽑아 기준 비교 넷(===, Object.is, [a].includes(b), ==)의 서명과 견준다.
// node 와 Chrome 이 이 파일을 같이 쓴다(Map.groupBy 를 못 찾으면 그 열은 (absent) 로 찍는다).
globalThis.equalityGrid = function equalityGrid() {
  const one = { a: 1 };
  const pairs = [
    ["NaN, NaN", NaN, NaN],
    ["0, -0", 0, -0],
    ["'1', 1", "1", 1],
    ["1, 1.0", 1, 1.0],
    ["true, 1", true, 1],
    ["null, undefined", null, undefined],
    ["{a:1}, {a:1}  (two objects)", one, { a: 1 }],
    ["o, o  (one object)", one, one],
  ];
  const refs = [
    ["===", (a, b) => a === b],
    ["Object.is", (a, b) => Object.is(a, b)],
    ["includes", (a, b) => [a].includes(b)],
    ["==", (a, b) => a == b],
  ];
  const cols = [
    ["switch", (a, b) => { switch (a) { case b: return true; default: return false; } }],
    ["findIndex===", (a, b) => [a].findIndex((x) => x === b) !== -1],
    ["redefine", (a, b) => {
      const o = Object.defineProperty({}, "k", { value: a, writable: false, configurable: false });
      try { Object.defineProperty(o, "k", { value: b }); return true; } catch (e) { return false; }
    }],
    ["groupBy", typeof Map.groupBy === "function"
      ? (a, b) => Map.groupBy([a, b], (x) => x).size === 1
      : null],
  ];
  const sig = (f) => pairs.map(([, a, b]) => (f(a, b) ? "y" : "n")).join("");
  const refSig = refs.map(([n, f]) => [n, sig(f)]);
  console.log(("  " + "".padEnd(30) + cols.map(([n]) => n.padEnd(14)).join("")).trimEnd());
  const colSig = cols.map(([, f]) => (f ? sig(f) : null));
  pairs.forEach(([label], i) => {
    console.log(("  " + label.padEnd(30) + colSig.map((s) => (s ? s[i] : "(absent)").padEnd(14)).join("")).trimEnd());
  });
  console.log("");
  console.log("  which reference comparison gives the same eight answers:");
  let asked = 0, matched = 0;
  cols.forEach(([n], i) => {
    if (!colSig[i]) { console.log("    " + n.padEnd(22) + "(absent in this runtime)"); return; }
    asked += 1;
    const same = refSig.filter(([, s]) => s === colSig[i]).map(([r]) => r);
    if (same.length) matched += 1;
    console.log("    " + n.padEnd(22) + colSig[i] + "   " + (same.length ? same.join(" / ") : "(none)"));
  });
  refSig.forEach(([n, s]) => console.log("    " + ("reference " + n).padEnd(22) + s));
  console.log("new columns whose signature equals a reference column: " + matched + " / " + asked);
};
```

```js
// js32b-33a-new-places.js
// 23번이 안 물은 비교 자리들 -- 격자는 js32b-33-h-equality-core.js 에 있다(Chrome 판은 js32b-33b-new-places.web.js).
require("./js32b-33-h-equality-core.js");
equalityGrid();
```

- ★★★ `switch` · `findIndex===` · `redefine` 세 열의 여덟 글자를 적어라. `groupBy` 열에는 무엇이 찍히나?
- ★★★ `which reference comparison …` 아래에서 세 열은 각각 어느 기준과 같다고 나오나?
- ★ 마지막 줄의 N 과 M 은?

### 3. 같은 격자를 Chrome 151 에서 (예측) ★★

```js
// js32b-33b-new-places.web.js
// 같은 격자를 Chrome 에서 -- 이어서 Map.groupBy 가 -0 에 대해 저장하는 키.
equalityGrid();
console.log("");
console.log("[2] the key Map.groupBy stores for -0");
const k = [...Map.groupBy([-0], (x) => x).keys()][0];
console.log("  Object.is(stored key, -0)   " + Object.is(k, -0));
console.log("  Object.is(stored key, +0)   " + Object.is(k, 0));
```

- ★★★ `groupBy` 열의 서명은? 어느 기준과 같나?
- ★★ `[2]` 두 줄은? 23번의 `Map` 과 같은가?
- ★ 마지막 줄은 2번과 무엇이 다른가?

### 4. 격자 밖 세 자리 — 형식화 배열 · 문자열 · 재정의 (예측) ★★★

```js
// js32b-33c-typed-and-string.js
// 23번 격자 밖의 찾기 셋 -- 형식화 배열(TypedArray) · 문자열의 includes · 그리고 Object.defineProperty 가 값을 견주는 자리.
const row = (label, v) => console.log("  " + label.padEnd(48) + v);
const shot = (f) => { try { return String(f()); } catch (e) { return e.constructor.name + " 「" + e.message + "」"; } };

console.log("[1] TypedArray -- the same two methods as on arrays");
row("new Float64Array([NaN]).indexOf(NaN)", new Float64Array([NaN]).indexOf(NaN));
row("new Float64Array([NaN]).includes(NaN)", new Float64Array([NaN]).includes(NaN));
row("new Float64Array([-0]).includes(0)", new Float64Array([-0]).includes(0));
row("Object.is(new Float64Array([-0])[0], -0)", Object.is(new Float64Array([-0])[0], -0));
row("Object.is(new Int32Array([-0])[0], -0)", Object.is(new Int32Array([-0])[0], -0));
row("new Float64Array([1]).includes('1')", new Float64Array([1]).includes("1"));
row("new Float64Array([1]).indexOf('1')", new Float64Array([1]).indexOf("1"));

console.log("[2] String.prototype.includes -- given a number");
row("'NaN'.includes(NaN)", "NaN".includes(NaN));
row("'-0'.includes(-0)", "-0".includes(-0));
row("'10'.includes(1)", "10".includes(1));
row("String(-0)", JSON.stringify(String(-0)));

console.log("[3] Object.defineProperty on a non-writable, non-configurable property");
const mk = (v) => Object.defineProperty({}, "k", { value: v, writable: false, configurable: false });
row("value 0, redefine with -0", shot(() => (Object.defineProperty(mk(0), "k", { value: -0 }), "ok")));
row("value NaN, redefine with 0/0", shot(() => (Object.defineProperty(mk(NaN), "k", { value: 0 / 0 }), "ok")));
row("value 0, redefine with 0", shot(() => (Object.defineProperty(mk(0), "k", { value: 0 }), "ok")));
row("frozen { k: 0 }, redefine with -0", shot(() => (Object.defineProperty(Object.freeze({ k: 0 }), "k", { value: -0 }), "ok")));
```

- ★★★ `[1]` 일곱 줄 — 배열의 `indexOf`/`includes` 와 같은 답인가? `Int32Array` 줄은?
- ★★★ `[2]` 네 줄 — 이것은 동등성 비교인가?
- ★★★ `[3]` 네 줄 — 어느 줄이 던지나? 무엇으로 견준 결과인가?

### 5. 네 알고리즘은 정확히 무엇이 다른가 (왜) ★★★

- ★★★ `IsStrictlyEqual` · `SameValue` · `SameValueZero` 를 `NaN, NaN` 과 `0, -0` 두 칸으로 적으면?
- ★★ `IsLooselyEqual` 은 거기에 무엇이 더 붙나?
- ★★ SameValueZero 는 왜 따로 있나 — 「찾기」와 「키」에 `Object.is` 를 쓰면 무엇이 불편한가?

### 6. `switch` 와 재정의는 왜 그 알고리즘인가 (왜) ★★

- ★★★ `CaseClauseIsSelected` 는 무엇을 돌려주나?
- ★★★ `ValidateAndApplyPropertyDescriptor` 는 값을 무엇으로 견주나? 그 옆 NOTE 는 `NaN` 에 대해 무엇이라 적나?
- ★ `instanceof` 도 명세상 `SameValue` 를 쓰는데 왜 정본 표에 행이 없나?

### 7. 넣은 `-0` 은 무엇으로 남나 (연결) ★★★

- ★★★ `Map` · `Set` · `Map.groupBy` · 배열 · `Float64Array` · `Int32Array` · 평범한 객체의 키 — 각각 `-0` 을 넣으면 무엇이 남나?
- ★★ 「키를 보관하는」 셋이 공통으로 부르는 명세 연산은?
- ★ 23번 `getOrInsertComputed(-0, cb)` 에서 콜백이 받은 키는?

### 8. 어디까지가 언어의 동등성인가 (경계) ★★

- ★★ `String.prototype.includes` 는 정본 표에서 어떤 행인가?
- ★★ UI 라이브러리가 상태 변화를 `Object.is` 로 감지하는 것은 이 표에 들어가나?
- ★ `switch` 의 fall-through · 라벨은 목록의 몇 번 주제가 정본인가?
- ★ 파이썬 `dict` 가 `nan` 두 개를 두 칸으로 두는 것은 어느 편의 어느 절이 정본인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
