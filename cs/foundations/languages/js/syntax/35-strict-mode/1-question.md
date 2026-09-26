# js/syntax/35 — 엄격 모드: 「무엇을 바꾸고, 어디서 켜지나」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v18.19.1(기본 PATH) · v20.19.6(nvm) · x86-64 Linux. 배너의 `node20` 은 v20.19.6 이다.
>
> ★★★ **이 편은 정본 모음 편이다.** 1번은 **앞 편들에서 잰 것을 떠올리는** 문항이고, 2\~4번이 **이 편이 새로 잰 칸**이다.
> ★★★ **이 주제의 본체는 두 번 컴파일 격자다** — 엄격을 먼저 · 탐침마다 고유 전역 · 끝에 누수 확인. **2번 문항이 이 주제의 중심이다.**
>
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① ★★★ **엄격이 바꾸는 규칙은 무엇이고, 각각 컴파일에서 거절하나 실행에서 거절하나**
> ② **`"use strict"` 는 어디에 어떻게 써야 효력이 있나**
> ③ **늘 엄격인 곳은 어디이고, 그 경계는 어디까지인가.**
>
> **선행** — [05](../05-var-let-const-and-tdz/2-summary.md) · [07](../07-this-binding-four-rules/2-summary.md) · [08](../08-function-forms-and-parameters/2-summary.md) · [10](../10-destructuring-assignment/2-summary.md) · [12](../12-optional-chaining-nullish-and-logical-assignment/2-summary.md) · [14](../14-property-descriptors-and-freezing/2-summary.md) · [16](../16-class-syntax/2-summary.md) · [24](../24-array-mutating-methods/2-summary.md).
> ★★★ **10번에서 거짓 `0 / 12` 가 나온 이유를 먼저 떠올려라** — 무엇을 먼저 돌렸나.

## 이 파일을 푸는 법

- ★★ **예측형 세 문항(2 · 3 · 4)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **2번은 탐침마다 두 줄(엄격 · 비엄격)을 적고**, 예외면 **`COMPILE` 이 붙는지**까지 적어라. 마지막에 남는 전역 이름도.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이것은 명세인가, 이 엔진(V8)의 사정인가, 호스트(node)의 것인가**」.
- ★★★ **속도에 관한 답은 하나도 없다.** 「엄격 모드가 빠르다」가 떠오르면 「**안 쟀다**」라고 적어라.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 앞 편들이 두 번 컴파일로 잰 칸 (연결) ★★★

- ★★★ 07번 `this` 격자와 08번 `arguments` 격자의 「설정에 달린 칸」 수는?
- ★★★ 12번에서 선언 안 된 이름에 `G ??= 1` 을 하면 두 모드는 각각?
- ★★ 14번 격자의 수는? 24번에서 동결 배열에 `push` 를 하면 비엄격은?
- ★★ 16번에서 클래스 몸통과 바깥 비엄격 함수를 나란히 돌렸을 때 샌 전역은 몇 중 몇?
- ★ 13번 — 객체 리터럴의 중복 키는 지금 엄격 모드에서 막히나?

### 2. 새 탐침 열넷을 두 번 컴파일하면 (예측) ★★★ 이 주제의 축

```js
// js32b-35a-new-cells.js
// 앞 편들이 안 잰 엄격 모드 칸 -- 같은 탐침 본문을 두 번 컴파일한다(앞에 "use strict"; 를 붙여 / 그대로).
// 규칙 둘: (1) 엄격을 먼저 전부 돌린다  (2) 탐침마다 전역 이름을 다르게 준다(G -> js35_<번호>_<모드>).
// 끝에 globalThis 에 남은 js35_ 이름을 찍는다 -- 무엇이 실제로 전역에 샜나.
const PROBES = [
  ["eval('var G = 1'), then typeof G", "eval('var G = 1'); return typeof G;"],
  ["eval('function G() {}'), then typeof G", "eval('function G() {}'); return typeof G;"],
  ["eval('let G = 1'), then typeof G", "eval('let G = 1'); return typeof G;"],
  ["(0, eval)('var G = 1'), then typeof G", "(0, eval)('var G = 1'); return typeof G;"],
  ["with ({ v: 1 }) { return v; }", "with ({ v: 1 }) { return v; }"],
  ["return 010;", "return 010;"],
  ["return 08;", "return 08;"],
  ["return '\\101';", "return '\\101';"],
  ["return 0o10;", "return 0o10;"],
  ["var v = 1; return delete v;", "var v = 1; return delete v;"],
  ["undefined = 1; return typeof undefined;", "undefined = 1; return typeof undefined;"],
  ["'ab'.len = 1; return 'ab'.len;", "'ab'.len = 1; return String('ab'.len);"],
  ["var implements = 1; return implements;", "var implements = 1; return implements;"],
  ["var let = 1; return let;", "var let = 1; return let;"],
];
const show = (e) => e.constructor.name + " 「" + e.message + "」";
function run(i, body, mode) {
  const gname = "js35_" + i + "_" + mode;
  const src = (mode === "strict" ? '"use strict";\n' : "") + body.replace(/\bG\b/g, gname);
  let f;
  try { f = new Function(src); } catch (e) { return "COMPILE " + show(e); }
  try { return String(f()); } catch (e) { return show(e); }
}
const strict = PROBES.map(([, body], i) => run(i, body, "strict"));   // ★ 엄격 먼저
const sloppy = PROBES.map(([, body], i) => run(i, body, "sloppy"));
let differ = 0;
PROBES.forEach(([label], i) => {
  const d = strict[i] !== sloppy[i];
  if (d) differ += 1;
  console.log(label + (d ? "   <-- DIFFERENT" : ""));
  console.log("    strict  " + strict[i]);
  console.log("    sloppy  " + sloppy[i]);
});
console.log("");
const left = Object.keys(globalThis).filter((k) => k.startsWith("js35_")).sort();
console.log("globals left behind: " + JSON.stringify(left));
console.log("settings-dependent cells " + differ + " / " + PROBES.length);
```

- ★★★ 탐침 0\~3(`eval` 넷) — 모드마다 `typeof G` 는?
- ★★★ `with` · `010` · `08` · `'\101'` · `delete v` · 예약어 둘 — 엄격 쪽은 컴파일에서 던지나 실행에서 던지나?
- ★★ `undefined = 1` · `'ab'.len = 1` 의 두 모드는?
- ★★★ `globals left behind` 에는 어떤 이름이 남나? 마지막 줄의 N 과 M 은?

### 3. `"use strict"` 를 여러 자리에 두면 (예측) ★★★

```js
// js32b-35b-directive.js
// "use strict" 는 어디에 어떻게 써야 효력이 있나 -- 본문마다 new Function 으로 컴파일하고 안쪽 함수의 this 로 모드를 읽는다.
// (전역에 아무것도 만들지 않는 판별이다 -- 암시적 전역을 쓰지 않는다.)
const TEST = 'return (function () { return this === undefined ? "strict" : "sloppy"; })();';
const BODIES = [
  ['"use strict"; ...', '"use strict"; ' + TEST],
  ["'use strict'; ...", "'use strict'; " + TEST],
  ['"hello"; "use strict"; ...', '"hello"; "use strict"; ' + TEST],
  ['// note  NEWLINE  "use strict"; ...', '// note\n"use strict"; ' + TEST],
  ['"use strict"  NEWLINE  return ...', '"use strict"\n' + TEST],
  ['var a; "use strict"; ...', 'var a; "use strict"; ' + TEST],
  ['("use strict"); ...', '("use strict"); ' + TEST],
  ['"use\\x20strict"; ...', '"use\\x20strict"; ' + TEST],
  ['"USE STRICT"; ...', '"USE STRICT"; ' + TEST],
];
const show = (e) => e.constructor.name + " 「" + e.message + "」";
const shot = (src) => { try { return String(new Function(src)()); } catch (e) { return show(e); } };
console.log("[1] where the directive sits");
for (const [label, src] of BODIES) console.log("  " + label.padEnd(40) + shot(src));

console.log("[2] a directive inside a function whose parameter list is not simple");
const FORMS = [
  ["function (a = 1) { 'use strict'; }", "(function (a = 1) { 'use strict'; });"],
  ["(a = 1) => { 'use strict'; }", "((a = 1) => { 'use strict'; });"],
  ["({ m(...r) { 'use strict'; } })", "({ m(...r) { 'use strict'; } });"],
  ["class { m({ a }) { 'use strict'; } }", "(class { m({ a }) { 'use strict'; } });"],
  ["class { m(a) { 'use strict'; } }", "(class { m(a) { 'use strict'; } });"],
];
for (const [label, src] of FORMS) {
  let r;
  try { new Function(src); r = "compiles"; } catch (e) { r = "COMPILE " + show(e); }
  console.log("  " + label.padEnd(40) + r);
}
```

- ★★★ `[1]` 아홉 본문 각각은 `strict` 인가 `sloppy` 인가?
- ★★★ `[2]` 다섯 형태 중 컴파일되는 것은?

### 4. 같은 파일을 모듈과 CommonJS 로 (예측) ★★★

```js
// js32b-35-h-mode.mjs
// 같은 글자를 모듈로 한 번, 스크립트(CommonJS)로 한 번 -- 파일 첫머리에 "use strict" 는 없다.
const row = (label, v) => console.log("  " + label.padEnd(52) + v);
const shot = (f) => { try { return String(f()); } catch (e) { return e.constructor.name + " 「" + e.message + "」"; } };
row("top-level this === undefined", this === undefined);
row("plain call: this === undefined", (function () { return this === undefined; })());
row("assign to an undeclared name", shot(() => { js35_mod_leak = 1; return "assigned"; }));
row("direct eval('010')", shot(() => eval("010")));
row("indirect (0, eval)('010')", shot(() => (0, eval)("010")));
row("new Function(...): plain call this === undefined", new Function("return (function () { return this === undefined; })();")());
row("globals left behind", JSON.stringify(Object.keys(globalThis).filter((k) => k.startsWith("js35_"))));
```

```sh
# js32b-35c-module.sh
#!/usr/bin/env bash
# 같은 파일을 모듈로(.mjs 확장자) 한 번, CommonJS 스크립트로(표준 입력 + --input-type=commonjs) 한 번 돌린다.
set -u -o pipefail
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
echo "--- node20 js32b-35-h-mode.mjs"
"$N20" js32b-35-h-mode.mjs
echo "(exit $?)"
echo "--- node20 --input-type=commonjs < js32b-35-h-mode.mjs"
"$N20" --input-type=commonjs < js32b-35-h-mode.mjs
echo "(exit $?)"
```

- ★★★ 두 실행에서 일곱 줄은 각각?
- ★★ 모듈 판에서 `new Function(...)` 줄과 간접 `eval` 줄은?

### 5. 엄격이 「컴파일에서」 거절하는 것과 「실행에서」 거절하는 것 (왜) ★★★

- ★★★ early error 란 무엇이고, 그 코드는 몇 줄이 도나?
- ★★ 2번의 거절들을 둘로 가르면? 암시적 전역과 동결 쓰기는 어느 쪽인가?
- ★ 비엄격에서 실패하는 쓰기는 무엇을 돌려주고, 엄격은 그것을 어떻게 바꾸나(14번)?

### 6. eval 코드는 언제 엄격이 되나 (왜) ★★★

- ★★★ eval 코드가 엄격이 되는 두 조건은?
- ★★ `PerformEval` 에서 `strictEval` 이면 `varEnv` 는 무엇이 되나?
- ★★ 엄격 호출자 안에서 간접 `eval` 을 부르면 그 eval 코드는 두 조건 중 어느 것에 걸리나? 만든 `var` 는 어디로 가나?

### 7. `"use strict"` 의 효력 조건과 금지 조건 (왜) ★★

- ★★★ Use Strict Directive 가 되려면 문자열이 어디에, 어떤 글자로 있어야 하나?
- ★★ 비단순 매개변수 목록과 함께 쓰면 안 되는 규칙은 「엄격이 되나」를 보나, 「지시어가 있나」를 보나?
- ★ 번들러가 파일을 이어 붙이면 둘째 파일의 `"use strict"` 는?

### 8. 명세가 「늘 엄격」이라 적는 곳 (연결) ★★

- ★★★ 명세가 「늘 엄격」이라고 적는 코드 두 가지는?
- ★★ 모듈 안에서 `new Function`·간접 `eval` 이 만든 코드는 어느 모드인가?
- ★ 05번이 「안 돌려 본 것」으로 남긴 빈 칸 가운데 이 편이 채운 것은?

### 9. 어디까지가 이 주제인가 (경계) ★★

- ★★ 어느 파일이 모듈인지는 누가 정하나 — 명세인가 호스트인가?
- ★★ `import`/`export` 와 CJS 상호운용은 목록의 몇 번 주제가 정본인가?
- ★ Annex C 의 항목 중 이 편이 재지 않은 것이 있나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
