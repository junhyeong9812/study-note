# js/syntax/26 — 배열 탐색·평탄화·생성: 「구멍을 누가 건너뛰고 누가 읽나 · 찾기는 무엇으로 비교하나 · 배열을 만드는 입구 넷」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v18.19.1(기본 PATH) · v20.19.6(nvm) · Google Chrome 151.0.7922.173(헤드리스) · x86-64 Linux.
> 배너의 `node20` 은 v20.19.6 이다. ★ **8번(`Array.fromAsync`)은 Chrome 에서만** 돌렸다 — 두 node 판에서 되는지는 7번이 묻는다.
>
> ★★★ **이 주제의 본체는 ② 전수 격자다.**
> 구멍 하나짜리 배열 `[, 1]` 을 **배열 연산 스물아홉 줄**에 들이대고, 「ES5 까지의 메서드는 건너뛰고 ES2015 부터는 `undefined` 로 읽는다」는 **통설과 어긋난 줄을 스크립트가 센다.** **1번 문항이 이 주제의 중심이다.**
>
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① ★★★ **구멍(프로퍼티가 없는 칸)을 누가 건너뛰고 누가 읽나**
> ② **찾기 메서드가 무엇으로 비교하고 어디서 멈추나**(`NaN` · `-0` · 방문한 인덱스)
> ③ **배열을 만드는 세 입구**(`Array(n)` · `Array.of` · `Array.from`)와 비동기 입구 `Array.fromAsync`.
>
> ★★ **예외는 타입과 메시지로만 답한다.** ★ 메시지는 엔진의 문구다 — 종류만 명세가 정한다.
>
> **선행** — [23 — `Map`·`Set` 과 약한 컬렉션](../23-map-set-and-weak-collections/2-summary.md)(★★★ `indexOf` 와 `includes` 가 `NaN` 에서 갈리는 것은 거기서 이미 쟀다) ·
> [21 — 이터레이터 헬퍼](../21-iterator-helpers/2-summary.md) · [19 — 이터러블 프로토콜과 `for...of`](../19-iterable-protocol-and-for-of/2-summary.md) ·
> [18 — `for...in` 과 열거](../18-for-in-and-enumeration/2-summary.md) · [11 — 스프레드와 나머지](../11-spread-and-rest/2-summary.md) ·
> [24 — 배열 변형 메서드](../24-array-mutating-methods/2-summary.md).

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1 · 2 · 3 · 4 · 5 · 6)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **1번은 줄마다 `skips`/`reads` 를 적고, 통설 열과 어긋나는 줄을 직접 세어 본다.** 판 이름만 보고 짐작하지 마라.
- ★★ **5번·6번은 「되는 것」과 「터지는 것」을 갈라서** 적어라. 터지면 종류와 문구까지.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이것은 명세인가, 이 엔진(V8)의 사정인가, 이 판의 관찰인가**」.
- ★★★ **속도에 관한 답은 하나도 없다.** 「`find` 가 `filter` 보다 빠르다」가 떠오르면 「**호출 횟수는 셌고 시간은 안 쟀다**」라고 적어라.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 구멍 하나짜리 배열 `[, 1]` 을 배열 연산마다 넣으면 (예측) ★★★ 이 주제의 축

```js
// js24b-26a-hole-grid.js
// arr = [, 1] -- index 0 is a hole (no property at all), index 1 holds 1.
// Each row asks the same question of one operation: at the hole, does it skip, or does it read undefined?
// The "rule" column is the folk rule under test: edition <= ES5 -> skips, ES2015 or later -> reads.
const make = () => [, 1];
const show = (a) => "[" + Array.from({ length: a.length }, (_, i) => (i in a ? String(a[i]) : "<hole>")).join(",") + "]";
const visits = (run) => { const seen = []; run((v, i) => { seen.push(i); }); return seen.includes(0) ? "reads" : "skips"; };
const kept = (r) => (0 in r ? "reads" : "skips");

const rows = [
  // [operation, edition, measure() -> "reads" | "skips", detail()]
  ["forEach",            "ES5",    () => visits((f) => make().forEach(f)),                          () => ""],
  ["map",                "ES5",    () => kept(make().map((x) => x)),                                () => show(make().map((x) => x))],
  ["filter",             "ES5",    () => visits((f) => make().filter((v, i) => { f(v, i); return true; })), () => show(make().filter(() => true))],
  ["some",               "ES5",    () => visits((f) => make().some((v, i) => { f(v, i); return false; })),  () => ""],
  ["every",              "ES5",    () => visits((f) => make().every((v, i) => { f(v, i); return true; })),  () => ""],
  ["reduce",             "ES5",    () => visits((f) => make().reduce((acc, v, i) => { f(v, i); return acc; }, 0)), () => ""],
  ["indexOf(undefined)", "ES5",    () => (make().indexOf(undefined) === 0 ? "reads" : "skips"),     () => String(make().indexOf(undefined))],
  ["lastIndexOf(undef)", "ES5",    () => (make().lastIndexOf(undefined) === 0 ? "reads" : "skips"), () => String(make().lastIndexOf(undefined))],
  ["slice()",            "ES3",    () => kept(make().slice()),                                      () => show(make().slice())],
  ["concat()",           "ES3",    () => kept(make().concat()),                                     () => show(make().concat())],
  ["reverse()",          "ES3",    () => kept(make().reverse().reverse()),                          () => show(make().reverse())],
  ["sort()",             "ES3",    () => { const r = make().sort(); return r.length - 1 in r ? "reads" : "skips"; }, () => show(make().sort())],
  ["join('-')",          "ES3",    () => "(n/a)",                                                   () => JSON.stringify(make().join("-"))],
  ["for-in",             "ES3",    () => { const ks = []; for (const k in make()) ks.push(k); return ks.includes("0") ? "reads" : "skips"; }, () => ""],
  ["find",               "ES2015", () => visits((f) => make().find((v, i) => { f(v, i); return false; })),  () => ""],
  ["findIndex",          "ES2015", () => visits((f) => make().findIndex((v, i) => { f(v, i); return false; })), () => ""],
  ["fill(0)",            "ES2015", () => kept(make().fill(0)),                                      () => show(make().fill(0))],
  ["copyWithin(1, 0)",   "ES2015", () => { const r = make().copyWithin(1, 0); return 1 in r ? "reads" : "skips"; }, () => show(make().copyWithin(1, 0))],
  ["keys()",             "ES2015", () => ([...make().keys()].includes(0) ? "reads" : "skips"),     () => JSON.stringify([...make().keys()])],
  ["entries()",          "ES2015", () => ([...make().entries()].some(([i]) => i === 0) ? "reads" : "skips"), () => JSON.stringify([...make().entries()])],
  ["for-of",             "ES2015", () => { const vs = []; for (const v of make()) vs.push(v); return vs.length === 2 ? "reads" : "skips"; }, () => ""],
  ["[...arr]",           "ES2015", () => kept([...make()]),                                         () => show([...make()])],
  ["Array.from(arr)",    "ES2015", () => kept(Array.from(make())),                                  () => show(Array.from(make()))],
  ["includes(undefined)","ES2016", () => (make().includes(undefined) ? "reads" : "skips"),         () => String(make().includes(undefined))],
  ["flat()",             "ES2019", () => (make().flat().length === 2 ? "reads" : "skips"),                                       () => show(make().flat())],
  ["flatMap(x => [x])",  "ES2019", () => visits((f) => make().flatMap((v, i) => { f(v, i); return [v]; })),                          () => show(make().flatMap((x) => [x]))],
  ["at(0)",              "ES2022", () => "(n/a)",                                                   () => String(make().at(0))],
  ["findLast",           "ES2023", () => visits((f) => make().findLast((v, i) => { f(v, i); return false; })), () => ""],
  ["findLastIndex",      "ES2023", () => visits((f) => make().findLastIndex((v, i) => { f(v, i); return false; })), () => ""],
];

const ruleOf = (ed) => (ed === "ES3" || ed === "ES5" ? "skips" : "reads");
console.log("arr = [, 1]   (0 in arr) = " + (0 in make()) + "   length = " + make().length);
console.log("");
console.log("operation            edition  measured  rule    detail");
let asked = 0, off = 0;
for (const [name, ed, measure, detail] of rows) {
  const m = measure();
  const r = ruleOf(ed);
  let mark = "";
  if (m !== "(n/a)") { asked++; if (m !== r) { off++; mark = "  <- differs"; } }
  console.log(name.padEnd(21) + ed.padEnd(9) + m.padEnd(10) + r.padEnd(8) + (detail() + mark).trim());
}
console.log("");
console.log("rows where the edition rule misses: " + off + " / " + asked);
```

- ★★★ 줄마다 `measured` 칸에 `skips` 인지 `reads` 인지 적어라. `detail` 칸(돌려받은 배열·값)도.
- ★★ 특히 **`map` · `slice()` · `sort()` 가 돌려주는 배열에 구멍이 남나**, **`[...arr]` · `Array.from(arr)` 은**?
- ★★★ **ES2015 이후 판인데 `skips` 인 줄**이 있나? 있으면 어느 것인가?
- ★ 마지막 줄 「N / M」의 N 과 M 은?

### 2. `-0` 과 `NaN` 을 찾는 메서드들 (예측) ★★

```js
// js24b-26b-zero-and-nan.js
// Three searches, three signed/unsigned zero arrangements, and NaN.
// Each line prints the raw return value -- no interpretation.
const row = (label, v) => console.log("  " + label.padEnd(44) + String(v));

console.log("[1] searching for -0 in [0]");
row("[0].indexOf(-0)", [0].indexOf(-0));
row("[0].lastIndexOf(-0)", [0].lastIndexOf(-0));
row("[0].includes(-0)", [0].includes(-0));

console.log("[2] searching for 0 in [-0]");
row("[-0].indexOf(0)", [-0].indexOf(0));
row("[-0].includes(0)", [-0].includes(0));

console.log("[3] which zero comes back");
const found = [-0].find((x) => x === 0);
row("Object.is([-0].find(x => x === 0), -0)", Object.is(found, -0));
row("Object.is([-0].at(0), -0)", Object.is([-0].at(0), -0));
row("[0, -0].findIndex(x => Object.is(x, -0))", [0, -0].findIndex((x) => Object.is(x, -0)));

console.log("[4] NaN, and the ways to find it");
row("[NaN].indexOf(NaN)", [NaN].indexOf(NaN));
row("[NaN].lastIndexOf(NaN)", [NaN].lastIndexOf(NaN));
row("[NaN].includes(NaN)", [NaN].includes(NaN));
row("[NaN].findIndex(Number.isNaN)", [NaN].findIndex(Number.isNaN));
row("[NaN].findIndex(x => x !== x)", [NaN].findIndex((x) => x !== x));

console.log("[5] fromIndex -- the second argument");
row("[1, 2, 1].indexOf(1, 1)", [1, 2, 1].indexOf(1, 1));
row("[1, 2, 1].indexOf(1, -1)", [1, 2, 1].indexOf(1, -1));
row("[1, 2, 1].lastIndexOf(1, -2)", [1, 2, 1].lastIndexOf(1, -2));
row("[1, 2, 1].includes(1, 3)", [1, 2, 1].includes(1, 3));
row("[1, 2, 1].includes(1, -100)", [1, 2, 1].includes(1, -100));

console.log("[6] strict comparison, no coercion");
row("['1'].indexOf(1)", ["1"].indexOf(1));
row("['1'].includes(1)", ["1"].includes(1));
row("[[1]].includes([1])", [[1]].includes([1]));
```

- ★★ `[1]`·`[2]` 다섯 줄 — `indexOf` 와 `includes` 가 **`-0` 에서도** 갈리나?
- ★★★ `[3]` — 배열은 `-0` 을 **그대로** 들고 있나, `+0` 으로 바꿔 들고 있나?
- ★★ `[4]` — `NaN` 을 찾는 방법 가운데 **인덱스를 돌려주는** 것은?
- ★ `[5]` 음수 `fromIndex` 다섯 줄.

### 3. `find` 형제들이 방문하는 인덱스 (예측) ★★

```js
// js24b-26c-find-family.js
// find / findIndex / findLast / findLastIndex on the same array, with a logging predicate.
const arr = [5, 12, 8, 130, 44];
const run = (name, call) => {
  const log = [];
  const pred = (v, i) => { log.push(i); return v > 10; };
  const result = call(pred);
  console.log("  " + name.padEnd(16) + "result " + String(result).padEnd(12) + "visited indexes " + JSON.stringify(log));
};

console.log("[1] predicate v > 10 on " + JSON.stringify(arr));
run("find", (p) => arr.find(p));
run("findIndex", (p) => arr.findIndex(p));
run("findLast", (p) => arr.findLast(p));
run("findLastIndex", (p) => arr.findLastIndex(p));
run("filter", (p) => JSON.stringify(arr.filter(p)));

console.log("[2] nothing matches");
const none = () => false;
console.log("  find           " + String(arr.find(none)));
console.log("  findIndex      " + String(arr.findIndex(none)));
console.log("  findLast       " + String(arr.findLast(none)));
console.log("  findLastIndex  " + String(arr.findLastIndex(none)));

console.log("[3] a matching element whose value is undefined");
const withUndef = [1, undefined, 3];
console.log("  find(v => v === undefined)       " + String(withUndef.find((v) => v === undefined)));
console.log("  findIndex(v => v === undefined)  " + String(withUndef.findIndex((v) => v === undefined)));

console.log("[4] the array grows during find -- how many calls?");
const grow = [1, 2, 3];
let calls = 0;
const r4 = grow.find((v) => { calls++; if (grow.length < 6) grow.push(v * 10); return false; });
console.log("  result " + String(r4) + "   calls " + calls + "   array now " + JSON.stringify(grow));

console.log("[5] an element is deleted during find");
const del = [1, 2, 3];
const seen = [];
del.find((v, i) => { seen.push(String(v)); if (i === 0) delete del[1]; return false; });
console.log("  values the predicate saw " + JSON.stringify(seen));
```

- ★★★ `[1]` 다섯 줄의 `result` 와 `visited indexes`.
- ★★ `[2]` — 못 찾았을 때 네 메서드가 돌려주는 값.
- ★★ `[3]` — `find` 의 답만으로 「찾았다」를 판정할 수 있나?
- ★★ `[4]` 콜백 호출 수와 배열의 끝 상태 · `[5]` 콜백이 본 값 셋.

### 4. `at(i)` 와 `arr[i]` (예측) ★★

```js
// js24b-26d-at.js
// at(i) against bracket access arr[i], on the same array.
const arr = ["a", "b", "c"];
const row = (label, v) => console.log("  " + label.padEnd(52) + JSON.stringify(v === undefined ? "<undefined>" : v));

console.log("[1] negative and out-of-range indexes");
for (const i of [0, 2, -1, -3, -4, 3]) {
  console.log("  i = " + String(i).padEnd(4) + "at(i) " + String(arr.at(i)).padEnd(12) + "arr[i] " + String(arr[i]));
}

console.log("[2] non-integer arguments");
row("arr.at(1.7)", arr.at(1.7));
row("arr.at(-1.7)", arr.at(-1.7));
row("arr.at('1')", arr.at("1"));
row("arr.at(NaN)", arr.at(NaN));
row("arr.at()", arr.at());
row("arr.at(-0)", arr.at(-0));
row("arr['1.7']", arr["1.7"]);

console.log("[3] what arr[-1] = v does");
const w = ["a", "b", "c"];
w[-1] = "z";
console.log("  length " + w.length + "   keys " + JSON.stringify(Object.keys(w)) + "   at(-1) " + w.at(-1));

console.log("[4] the same method on other receivers");
row("'abc'.at(-1)", "abc".at(-1));
row("new Uint8Array([7, 8]).at(-1)", new Uint8Array([7, 8]).at(-1));
row("Array.prototype.at.call({ length: 2, 1: 'x' }, -1)", Array.prototype.at.call({ length: 2, 1: "x" }, -1));
```

- ★★ `[1]` 여섯 줄의 두 열.
- ★★ `[2]` 일곱 줄 — 정수가 아닌 인자를 `at` 은 어떻게 읽나?
- ★★ `[3]` — `w[-1] = "z"` 뒤의 `length` · 키 목록 · `at(-1)`.
- ★ `[4]` — 배열이 아닌 수신자 셋.

### 5. `flat` 의 깊이와 `flatMap` 이 펴는 겹 수 (예측) ★★

```js
// js24b-26e-flat.js
// flat(depth) and flatMap on one nested array.
const nested = [1, [2, [3, [4, [5]]]]];
const J = JSON.stringify;
console.log("nested = " + J(nested));
console.log("[1] depth argument");
for (const d of [undefined, 0, 1, 2, -1, Infinity, "2", NaN]) {
  console.log("  flat(" + (typeof d === "string" ? J(d) : String(d)).padEnd(9) + ") " + J(d === undefined ? nested.flat() : nested.flat(d)));
}

console.log("[2] flatMap -- callback returns");
const src = [1, 2];
console.log("  flatMap(x => [x, x * 10])     " + J(src.flatMap((x) => [x, x * 10])));
console.log("  flatMap(x => [[x]])           " + J(src.flatMap((x) => [[x]])));
console.log("  flatMap(x => x)               " + J(src.flatMap((x) => x)));
console.log("  flatMap(x => [])              " + J(src.flatMap(() => [])));
console.log("  map(x => [[x]]).flat(2)       " + J(src.map((x) => [[x]]).flat(2)));

console.log("[3] what counts as an array to flatten");
const spreadable = { length: 2, 0: "p", 1: "q", [Symbol.isConcatSpreadable]: true };
console.log("  [[1], 'ab', spreadable].flat()   " + J([[1], "ab", spreadable].flat().map((x) => (x === spreadable ? "<the object>" : x))));
console.log("  [[1], 'ab', spreadable] concat   " + J([].concat([1], "ab", spreadable)));
console.log("  [new Set([1, 2])].flat()         " + J([new Set([1, 2])].flat().map((x) => (x instanceof Set ? "<the Set>" : x))));

console.log("[4] holes inside the nested arrays");
console.log("  [[1, , 3], , [5]].flat()         " + J([[1, , 3], , [5]].flat()));

console.log("[5] a very deep array with flat(Infinity)");
let deep = [0];
for (let i = 0; i < 100000; i++) deep = [deep];
try {
  console.log("  length " + deep.flat(Infinity).length);
} catch (e) {
  console.log("  " + e.constructor.name + " 「" + e.message + "」");
}
```

- ★★ `[1]` 여덟 줄 — 특히 `flat(-1)` · `flat("2")` · `flat(NaN)`.
- ★★★ `[2]` — `flatMap(x => [[x]])` 의 결과는?
- ★★ `[3]` — `Symbol.isConcatSpreadable` 을 켠 객체와 `Set` 을 `flat` 이 펴나? `concat` 은?
- ★★ `[4]` 결과 · `[5]` 결과(되나, 터지나).

### 6. 배열을 만드는 입구들 — `Array(n)` · `Array.of` · `Array.from` (예측) ★★★

```js
// js24b-26f-create.js
// Making arrays: the Array constructor, Array.of, Array.from.
const J = JSON.stringify;
const V = (v) => (v === undefined ? "undefined" : J(v));
const show = (a) => "[" + Array.from({ length: a.length }, (_, i) => (i in a ? V(a[i]) : "<hole>")).join(",") + "]";
const row = (label, f) => {
  let out;
  try { out = f(); } catch (e) { out = e.constructor.name + " 「" + e.message + "」"; }
  console.log("  " + label.padEnd(40) + out);
};

console.log("[1] one argument to Array vs Array.of");
row("Array(3)", () => show(Array(3)));
row("Array.of(3)", () => show(Array.of(3)));
row("Array('3')", () => show(Array("3")));
row("Array(3, 4)", () => show(Array(3, 4)));
row("Array.of(3, 4)", () => show(Array.of(3, 4)));
row("Array(2.5)", () => show(Array(2.5)));
row("Array(-1)", () => show(Array(-1)));
row("Array.of()", () => show(Array.of()));

console.log("[2] filling the slots of Array(3)");
let calls = 0;
row("Array(3).map(() => 0)", () => show(Array(3).map(() => { calls++; return 0; })));
row("  callback calls", () => String(calls));
row("Array(3).fill(0)", () => show(Array(3).fill(0)));
row("[...Array(3)]", () => show([...Array(3)]));
row("Array.from(Array(3))", () => show(Array.from(Array(3))));
row("Array.from({ length: 3 })", () => show(Array.from({ length: 3 })));
row("Array.from({ length: 3 }, (_, i) => i)", () => show(Array.from({ length: 3 }, (_, i) => i)));
row("Array.apply(null, Array(3))", () => show(Array.apply(null, Array(3))));

console.log("[3] what Array.from accepts");
row("Array.from('abc')", () => show(Array.from("abc")));
row("Array.from(new Set([1, 1, 2]))", () => show(Array.from(new Set([1, 1, 2]))));
row("Array.from(new Map([[1, 'a']]))", () => show(Array.from(new Map([[1, "a"]]))));
row("Array.from({ length: 2, 0: 'x' })", () => show(Array.from({ length: 2, 0: "x" })));
row("Array.from({ 0: 'x' })", () => show(Array.from({ 0: "x" })));
row("Array.from(5)", () => show(Array.from(5)));
row("Array.from(null)", () => show(Array.from(null)));
row("Array.from([1, 2], 'x')", () => show(Array.from([1, 2], "x")));

console.log("[4] an object that is both iterable and array-like");
const both = { length: 2, 0: "index-0", 1: "index-1", *[Symbol.iterator]() { yield "iter-a"; } };
row("Array.from(both)", () => show(Array.from(both)));

console.log("[5] the mapping function -- arguments and this");
const log = [];
Array.from({ length: 2, 0: "p", 1: "q" }, function (v, i) { log.push(J([v, i, arguments.length, this && this.tag])); return v; }, { tag: "T" });
for (const line of log) console.log("  " + line);

console.log("[6] Array.from called on a subclass");
class Tagged extends Array {}
row("Tagged.from([1]) instanceof Tagged", () => String(Tagged.from([1]) instanceof Tagged));
row("Tagged.of(1) instanceof Tagged", () => String(Tagged.of(1) instanceof Tagged));
```

- ★★★ `[1]` 여덟 줄 — 되나, 터지나. 특히 **`Array(3)` 과 `Array.of(3)`**.
- ★★★ `[2]` — `Array(3).map(...)` 의 결과와 콜백 호출 수. 나머지 여섯 줄에는 구멍이 남나?
- ★★ `[3]` 여덟 줄 · `[4]` 이터러블이면서 유사 배열인 객체.
- ★ `[5]` 매핑 함수가 받는 인자 수와 `this` · `[6]` 두 줄.

### 7. `Array.fromAsync` 가 이 판에 있나 — 무엇으로 판별하나 (경계) ★★

- ★★★ node 18 · node 20 · Chrome 151 가운데 **어디에 있나**? 판별 블록의 어느 줄이 근거인가?
- ★★ 없는 판에서 부르면 **무슨 예외**인가? 그 문구만으로 「메서드가 없다」를 판정해도 되나?
- ★ `Array.fromAsync` 는 **몇 판(ES20xx)** 기능인가? 목록 README 의 표기와 같은가?

### 8. `Array.fromAsync` 가 원본의 `next` 를 부르는 시점 (왜) ★★★

```js
// js24b-26g-fromasync.web.js
// Array.fromAsync (Chrome only in this batch). Every line is a log event, in the order it happened.
// Timers are virtual (--virtual-time-budget), so the order below does not depend on machine speed.
const J = JSON.stringify;
const later = (ms, v, log, tag) => new Promise((res) => setTimeout(() => { log.push("settle " + tag); res(v); }, ms));

(async () => {
  console.log("[1] return value of the call");
  const p = Array.fromAsync([1, Promise.resolve(2), 3]);
  console.log("  instanceof Promise  " + (p instanceof Promise));
  console.log("  resolved to         " + J(await p));

  console.log("[2] a sync iterable whose items settle 30, 20, 10 ms after they are made");
  const run = async (label, consume) => {
    const log = [];
    function* source() {
      const delays = [30, 20, 10];
      for (let i = 0; i < 3; i++) { log.push("next " + i); yield later(delays[i], "v" + i, log, i); }
    }
    const out = await consume(source());
    console.log("  " + label.padEnd(26) + J(out));
    console.log("  " + "".padEnd(26) + log.join(" | "));
  };
  await run("Array.fromAsync(gen())", (it) => Array.fromAsync(it));
  await run("Promise.all([...gen()])", (it) => Promise.all([...it]));

  console.log("[3] an async generator");
  const pulls = [];
  async function* agen() { for (let i = 0; i < 3; i++) { pulls.push(i); yield i * 10; } }
  console.log("  result " + J(await Array.fromAsync(agen())) + "   pulled " + J(pulls));

  console.log("[4] the mapping function");
  const margs = [];
  const mapped = await Array.fromAsync([Promise.resolve("a"), "b"], async (v, i) => { margs.push(J([v, i])); return v + v; });
  console.log("  result " + J(mapped) + "   mapper saw " + margs.join(" "));

  console.log("[5] an array-like of promises");
  console.log("  " + J(await Array.fromAsync({ length: 2, 0: Promise.resolve("x"), 1: "y" })));

  console.log("[6] one item rejects -- what reaches the caller, and how far did it pull");
  const log6 = [];
  function* withReject() {
    try {
      log6.push("next 0"); yield Promise.resolve(0);
      log6.push("next 1"); yield Promise.reject(new Error("item 1"));
      log6.push("next 2"); yield Promise.resolve(2);
    } finally { log6.push("finally ran"); }
  }
  try { await Array.fromAsync(withReject()); console.log("  resolved"); }
  catch (e) { console.log("  " + e.constructor.name + " 「" + e.message + "」"); }
  console.log("  log " + J(log6));

  console.log("[7] a bad mapper -- thrown now, or a rejected promise?");
  let sync = "no exception during the call";
  let q;
  try { q = Array.fromAsync([1], 5); } catch (e) { sync = "thrown during the call: " + e.constructor.name; }
  console.log("  " + sync);
  if (q) { try { await q; } catch (e) { console.log("  rejected: " + e.constructor.name + " 「" + e.message + "」"); } }

  console.log("[8] not iterable, not array-like");
  try { await Array.fromAsync(null); } catch (e) { console.log("  " + e.constructor.name + " 「" + e.message + "」"); }
  console.log("  " + J(await Array.fromAsync(5)));
  console.log("done");
})();
```

- ★★★ `[2]` 두 줄의 로그 — `next` 와 `settle` 이 어떤 순서로 섞이나? 왜 `Promise.all` 과 다르나?
- ★★ `[6]` 에서 항목 하나가 거부되면 `next 2` 가 찍히나? `finally` 는 도나? 명세의 어느 연산이 그것을 정하나?
- ★★ `[7]` — 매핑 함수가 함수가 아니면 **호출하는 순간 던지나, 거부된 프라미스를 돌려주나**? 명세가 이 메서드를 무엇이라 부르기 때문인가?

### 9. `includes` 와 `indexOf` — 명세 note 가 적는 두 차이 (왜) ★★★

- ★★★ 명세 `Array.prototype.includes` 의 note 는 `indexOf` 와 **두 가지가 다르다**고 적는다. 둘은 무엇인가?
- ★★ 두 알고리즘의 반복 단계에서 **한 줄이 다르다.** `indexOf` 에만 있는 연산은?
- ★ 그 연산이 있느냐로 1번 격자의 **모든 줄**을 다시 설명할 수 있나?

### 10. 「ES5 는 건너뛰고 ES2015 는 읽는다」 를 1번 격자로 판정하면 (경계) ★★★

- ★★★ 1번 격자에서 통설과 어긋난 줄이 있다면 그 줄들의 **공통점**은? 명세 알고리즘의 어느 한 줄로 설명되나?
- ★★ 통설을 명세 연산 이름으로 다시 말하면 — 한 문장으로.
- ★ 이 격자가 **못 보는 것**은 무엇인가(구멍이 **프로토타입에서 값을 얻는** 경우)?

### 11. 배열의 `-0` 과 `Map` 의 `-0` (연결) ★★

- ★★★ 23번에서 `Map` 에 `-0` 을 넣고 꺼낸 키는 무엇이었나? 2번의 `[-0].at(0)` 은?
- ★★ 그 차이는 **어느 명세 연산이 있고 없어서**인가?

### 12. 3번의 방문 인덱스를 21번의 콜백 격자와 이어 보면 (연결) ★★

- ★★ 3번 `[1]` 의 `visited indexes` 와 21번의 **`find(x > 3)` 줄**은 같은 사실을 말하나?
- ★★ `findLast` 가 어느 쪽 끝에서 도는지 로그의 어느 칸으로 판정하나?
- ★ 「`find` 가 빠르다」는 이 문서에서 어느 칸에 들어가나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
