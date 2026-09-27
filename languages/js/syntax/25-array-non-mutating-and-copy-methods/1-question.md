# js/syntax/25 — 배열 비변형·복사 메서드: 「원본에는 쓰기가 한 번도 안 닿는다 — 단 얕게, 그리고 콜백은 예외다」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v18.19.1(기본 PATH) · v20.19.6(nvm) · Google Chrome 151.0.7922.173(판별 블록만) · x86-64 Linux.
> 배너의 `node20` 은 v20.19.6, `node18` 은 v18.19.1 이다. ★ **복사 메서드 넷은 node 18 에 없다** — 소스는 node 20 기준으로 읽어라.
>
> ★★★ **이 주제의 본체는 ① 추상 연산에 로그 심기 — `Proxy` 쓰기 트랩이다.**
> 원본 배열을 `Proxy` 로 감싸 메서드마다 **쓰기 트랩이 몇 번 불리나**를 세고, 마지막 두 줄의 「N / M」을 **스크립트가 센다.** **1번 문항이 이 주제의 중심이다.**
>
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① ★★★ **원본에 쓰기가 닿았나**(결과가 아니라 과정으로)
> ② **복사 메서드 넷과 짝이 되는 변형 메서드의 차이**(반환값 · 범위 · 구멍 · species)
> ③ **비변형이어도 틀리는 자리**(얕은 복사 · 콜백 · `reduce` 초기값 · `map(parseInt)`).
>
> ★★ **예외는 타입과 메시지로만 답한다.** ★ **메시지는 판마다 다를 수 있다.**
>
> **선행** — [24 — 배열 변형 메서드](../24-array-mutating-methods/2-summary.md) · [22 — `Symbol` 과 잘 알려진 심볼](../22-symbol-and-well-known-symbols/2-summary.md) ·
> [17 — 상속과 `super`](../17-inheritance-and-super/2-summary.md) · [08 — 함수 정의 형태와 매개변수](../08-function-forms-and-parameters/2-summary.md) · [11 — 스프레드와 나머지](../11-spread-and-rest/2-summary.md).
> ★★★ **24번의 변형 메서드 반환값을 먼저 떠올려라** — `sort`·`reverse` 가 무엇을 돌려주고, `splice` 가 무엇을 돌려주나.

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1 · 2 · 3 · 4 · 5 · 6)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **1번은 행마다 쓰기 트랩 세 열의 수를 적고, 마지막 두 줄의 N 까지 세어 본다.** 메서드 이름만 보고 「비변형이니 0」으로 짐작하지 마라 — 행을 끝까지 읽어라.
- ★★ **3번·4번은 「값이 나오는 것」과 「터지는 것」을 갈라서** 적어라. 터지면 종류와 문구까지.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이것은 명세인가, 이 엔진(V8)의 사정인가, 이 판의 관찰인가**」.
- ★★★ **속도·메모리에 관한 답은 하나도 없다.** 「`toSorted` 는 느리다」가 떠오르면 「**안 쟀다**」라고 적어라.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 원본을 `Proxy` 로 감싸고 메서드 열일곱을 부르면 (예측) ★★★ 이 주제의 축

```js
// js24b-25a-trap-grid.js
// 배열을 Proxy 로 감싸고 메서드마다 쓰기 트랩(set · defineProperty · deleteProperty)이 몇 번 불리는지 센다.
// 메서드는 this 가 Proxy 인 채로 부른다 -- 원본에 무엇을 하는지가 트랩에 전부 찍힌다.
const probe = (label, run) => {
  const n = { get: 0, set: 0, defineProperty: 0, deleteProperty: 0 };
  const target = [3, 1, 2];
  const p = new Proxy(target, {
    get(t, k, r) { n.get++; return Reflect.get(t, k, r); },
    set(t, k, v, r) { n.set++; return Reflect.set(t, k, v, r); },
    defineProperty(t, k, d) { n.defineProperty++; return Reflect.defineProperty(t, k, d); },
    deleteProperty(t, k) { n.deleteProperty++; return Reflect.deleteProperty(t, k); },
  });
  let result, threw = false;
  try { result = run(p); } catch (e) { threw = true; result = e.constructor.name + " 「" + e.message + "」"; }
  const writes = n.set + n.defineProperty + n.deleteProperty;
  const shown = typeof result === "string" ? result : (result === p ? "<the proxy itself>" : JSON.stringify(result));
  console.log(
    "  " + label.padEnd(28) + String(n.set).padStart(4) + String(n.defineProperty).padStart(8) +
    String(n.deleteProperty).padStart(8) + String(n.get).padStart(6) + "   " + JSON.stringify(target).padEnd(12) + shown
  );
  return threw ? "threw" : writes;
};

console.log("  method                       set  define  delete   get   target after returned");
const rows = [
  ["map(x => x * 10)", (p) => p.map((x) => x * 10)],
  ["filter(x => x > 1)", (p) => p.filter((x) => x > 1)],
  ["reduce((a, x) => a + x)", (p) => p.reduce((a, x) => a + x)],
  ["slice(1)", (p) => p.slice(1)],
  ["concat([9])", (p) => p.concat([9])],
  ["toSorted()", (p) => p.toSorted()],
  ["toReversed()", (p) => p.toReversed()],
  ["toSpliced(0, 1)", (p) => p.toSpliced(0, 1)],
  ["with(0, 9)", (p) => p.with(0, 9)],
  ["sort()", (p) => p.sort()],
  ["reverse()", (p) => p.reverse()],
  ["splice(0, 1)", (p) => p.splice(0, 1)],
  ["push(9)", (p) => p.push(9)],
  ["fill(0)", (p) => p.fill(0)],
  ["shift()", (p) => p.shift()],
  ["copyWithin(0, 1)", (p) => p.copyWithin(0, 1)],
  ["map((x, i, a) => a[i] = 0)", (p) => p.map((x, i, a) => (a[i] = 0))],
];
let zero = 0, threw = 0;
for (const [label, run] of rows) {
  const w = probe(label, run);
  if (w === "threw") threw++; else if (w === 0) zero++;
}
console.log("");
console.log("methods that threw: " + threw + " / " + rows.length);
console.log("methods that returned with zero write traps: " + zero + " / " + rows.length);
```

- ★★★ 행마다 `set` · `define` · `delete` 세 열의 수는? `target after` 열은?
- ★★★ 마지막 행(`map` 의 콜백이 세 번째 인자에 쓰는 것)은 0 인가?
- ★★ `set` 열과 `define` 열은 서로 어떤 관계인가?
- ★ 마지막 두 줄의 N 은? 같은 소스를 **node 18** 에 던지면 두 줄이 어떻게 되나?

### 2. 짝 넷 — 돌려준 값, 원본과 같은 객체인가, 원본 (예측) ★★★

```js
// js24b-25b-pairs.js
// 짝 넷 -- 바꾸는 쪽과 복사하는 쪽에 같은 일을 시키고 (돌려준 값 · 그것이 원본과 같은 객체인가 · 원본) 을 찍는다.
// 배열은 칸마다 찍는다 -- 구멍은 <hole>, undefined 값은 undefined (JSON.stringify 는 둘 다 null 로 뭉갠다).
const cell = (a, i) => (i in a ? (a[i] === undefined ? "undefined" : JSON.stringify(a[i])) : "<hole>");
const show = (v) => (Array.isArray(v) ? "[" + Array.from({ length: v.length }, (_, i) => cell(v, i)).join(",") + "]" : String(v));
const attempt = (run) => { try { return run(); } catch (e) { return e.constructor.name + " 「" + e.message + "」"; } };

const pair = (label, run) => {
  const arr = [30, 10, 20];
  let r, same;
  try { r = run(arr); same = r === arr; r = show(r); } catch (e) { r = e.constructor.name + " 「" + e.message + "」"; same = "-"; }
  console.log("  " + label.padEnd(22) + "returned " + r.padEnd(14) + "  === arr " + String(same).padEnd(6) + "  arr " + show(arr));
};
console.log("[1] four pairs on [30, 10, 20]");
pair("sort()", (a) => a.sort());
pair("toSorted()", (a) => a.toSorted());
pair("reverse()", (a) => a.reverse());
pair("toReversed()", (a) => a.toReversed());
pair("splice(1, 1, 99)", (a) => a.splice(1, 1, 99));
pair("toSpliced(1, 1, 99)", (a) => a.toSpliced(1, 1, 99));
pair("a[1] = 99", (a) => (a[1] = 99));
pair("with(1, 99)", (a) => a.with(1, 99));

console.log("");
console.log("[2] a chain that starts from a copy");
const base = [30, 10, 20];
console.log("  base.toSorted().reverse()       " + attempt(() => show(base.toSorted().reverse())) + "   base " + show(base));
console.log("  base.slice().sort().reverse()   " + attempt(() => show(base.slice().sort().reverse())) + "   base " + show(base));

console.log("");
console.log("[3] how deep is the copy");
const rows = [{ id: 2 }, { id: 1 }];
console.log(attempt(() => {
  const sorted = rows.toSorted((a, b) => a.id - b.id);
  const out = [];
  out.push("  sorted === rows            " + (sorted === rows));
  out.push("  sorted[1] === rows[0]      " + (sorted[1] === rows[0]));
  sorted[1].id = 200;
  out.push("  after sorted[1].id = 200   rows " + JSON.stringify(rows));
  return out.join("\n");
}));

console.log("");
console.log("[4] holes in the receiver [3, <hole>, 1]");
const row4 = (label, run) => console.log("  " + label.padEnd(22) + attempt(run));
row4("toSorted()", () => show([3, , 1].toSorted()));
row4("sort()", () => { const d = [3, , 1]; d.sort(); return show(d); });
row4("toReversed()", () => show([3, , 1].toReversed()));
row4("reverse()", () => { const d = [3, , 1]; d.reverse(); return show(d); });
row4("with(0, 9)", () => show([3, , 1].with(0, 9)));
row4("slice()", () => show([3, , 1].slice()));
row4("map(x => x)", () => show([3, , 1].map((x) => x)));
```

- ★★★ `[1]` 여덟 줄의 `returned` · `=== arr` · `arr`. 특히 **`splice` 와 `toSpliced` 가 돌려주는 것**.
- ★★ `[2]` 두 사슬 뒤의 `base` 는?
- ★★★ `[3]` 세 줄 — `sorted[1] === rows[0]` 은? 마지막 줄의 `rows` 는?
- ★★★ `[4]` 일곱 줄 — 어느 줄에 `<hole>` 이 남고 어느 줄에 `undefined` 가 들어가나?

### 3. 같은 인덱스를 `with` 와 대입에 주면 (예측) ★★★

```js
// js24b-25c-index-range.js
// 범위 밖 인덱스 -- with(i, v) 와 대입 a[i] = v 에 같은 인덱스를 준다. 원본 길이는 3.
const cell = (a, i) => (i in a ? JSON.stringify(a[i]) : "<hole>");
const show = (a) => "[" + Array.from({ length: a.length }, (_, i) => cell(a, i)).join(",") + "]";
const idx = [2, 3, 5, -1, -3, -4, 1.5, "1"];

console.log("[1] a.with(i, 9)");
for (const i of idx) {
  const a = [0, 1, 2];
  let r;
  try { const c = a.with(i, 9); r = show(c) + "  length " + c.length; } catch (e) { r = e.constructor.name + " 「" + e.message + "」"; }
  console.log("  i = " + JSON.stringify(i).padEnd(6) + r + "   a " + show(a));
}

console.log("");
console.log("[2] a[i] = 9");
for (const i of idx) {
  const a = [0, 1, 2];
  let r;
  try { a[i] = 9; r = show(a) + "  length " + a.length + "  own keys " + JSON.stringify(Object.keys(a)); } catch (e) { r = e.constructor.name + " 「" + e.message + "」"; }
  console.log("  i = " + JSON.stringify(i).padEnd(6) + r);
}

console.log("");
console.log("[3] at(i) and with(i) read the same index");
const a = [0, 1, 2];
for (const i of [-1, -3, -4, 3]) {
  let w;
  try { w = show(a.with(i, 9)); } catch (e) { w = e.constructor.name; }
  console.log("  i = " + String(i).padEnd(4) + "at " + String(a.at(i)).padEnd(10) + "with " + w);
}
```

- ★★★ `[1]` 여덟 줄 — 던지는 인덱스가 있나? 있으면 종류와 문구는?
- ★★★ `[2]` 여덟 줄 — `length` 와 `own keys`. 특히 `5` · `-1` · `1.5`.
- ★★ `[3]` 네 줄 — `at` 이 `undefined` 인 자리에서 `with` 는?

### 4. `reduce` 에 초기값을 주거나 안 주면 (예측) ★★★

```js
// js24b-25d-reduce.js
// reduce -- 초기값이 있을 때와 없을 때, 콜백이 몇 번 불리고 무엇을 받나.
const run = (label, f) => {
  const calls = [];
  let r;
  try { r = JSON.stringify(f(calls)); } catch (e) { r = e.constructor.name + " 「" + e.message + "」"; }
  console.log("  " + label.padEnd(34) + "result " + String(r).padEnd(62) + "calls " + calls.length + "  " + calls.join(" "));
};
const add = (calls) => (acc, x, i) => { calls.push("(" + acc + "," + x + ",i" + i + ")"); return acc + x; };

console.log("[1] reduce");
run("[1, 2, 3].reduce(f)", (c) => [1, 2, 3].reduce(add(c)));
run("[1, 2, 3].reduce(f, 0)", (c) => [1, 2, 3].reduce(add(c), 0));
run("[7].reduce(f)", (c) => [7].reduce(add(c)));
run("[].reduce(f, 0)", (c) => [].reduce(add(c), 0));
run("[].reduce(f)", (c) => [].reduce(add(c)));
run("[, , 5].reduce(f)", (c) => [, , 5].reduce(add(c)));
run("[, ,].reduce(f)", (c) => [, ,].reduce(add(c)));
run("[].reduce(f, undefined)", (c) => [].reduce(add(c), undefined));

console.log("");
console.log("[2] reduceRight");
run("[1, 2, 3].reduceRight(f)", (c) => [1, 2, 3].reduceRight(add(c)));
run("[].reduceRight(f)", (c) => [].reduceRight(add(c)));

console.log("");
console.log("[3] string accumulator -- same callback, which side starts");
run("['a','b','c'].reduce(f)", (c) => ["a", "b", "c"].reduce(add(c)));
run("['a','b','c'].reduce(f, '')", (c) => ["a", "b", "c"].reduce(add(c), ""));
run("['a','b','c'].reduce(f, 0)", (c) => ["a", "b", "c"].reduce(add(c), 0));
```

- ★★★ `[1]` 여덟 줄의 `result` 와 `calls`. 던지는 줄이 있나? 있으면 문구는?
- ★★ `[, , 5]` 와 `[, ,]` 는 각각 어떻게 되나?
- ★★ `[3]` 세 줄의 결과 문자열은?

### 5. `['1','2','3'].map(parseInt)` (예측) ★★★

```js
// js24b-25e-map-parseint.js
// map(parseInt) -- map 이 콜백에 무엇을 넘기는지 먼저 찍고, 그것을 parseInt 에 그대로 준다.
console.log("[1] what map passes to its callback");
["1", "2", "3"].map((...args) => { console.log("  args " + JSON.stringify(args)); return 0; });

console.log("");
console.log("[2] the same arguments given to parseInt");
for (const [s, i] of [["1", 0], ["2", 1], ["3", 2]]) {
  console.log("  parseInt(" + JSON.stringify(s) + ", " + i + ")".padEnd(4) + "-> " + parseInt(s, i));
}
console.log("  parseInt.length       " + parseInt.length);

console.log("");
console.log("[3] map(parseInt) and the alternatives");
const show = (label, v) => console.log("  " + label.padEnd(40) + JSON.stringify(v.map((x) => (Number.isNaN(x) ? "NaN" : x))));
show("['1','2','3'].map(parseInt)", ["1", "2", "3"].map(parseInt));
show("['10','10','10','10'].map(parseInt)", ["10", "10", "10", "10"].map(parseInt));
show("['1','2','3'].map(Number)", ["1", "2", "3"].map(Number));
show("['1','2','3'].map(s => parseInt(s, 10))", ["1", "2", "3"].map((s) => parseInt(s, 10)));
show("['1.5','2px'].map(Number)", ["1.5", "2px"].map(Number));
show("['1.5','2px'].map(s => parseInt(s, 10))", ["1.5", "2px"].map((s) => parseInt(s, 10)));
show("['1','2','3'].map(parseFloat)", ["1", "2", "3"].map(parseFloat));
console.log("  parseFloat.length     " + parseFloat.length + "   Number.length " + Number.length);
```

- ★★★ `[1]` 세 줄 — 콜백이 받는 인자는?
- ★★★ `[3]` 첫 줄과 둘째 줄의 배열은? 왜 그런지 `[2]` 로 설명해라.
- ★★ `'2px'` 에서 `Number` 와 `parseInt(s, 10)` 은 같은 답인가?

### 6. 비교 함수가 도중에 던지면 원본은 (예측) ★★★

```js
// js24b-25f-comparator-throws.js
// 비교 함수가 도중에 던지면 -- sort 와 toSorted 의 원본은 어떻게 남나. 원본은 [5, 4, 3, 2, 1].
const attempt = (run) => { try { run(); return "returned"; } catch (e) { return e.constructor.name + " 「" + e.message + "」"; } };

console.log("[0] how many times the comparator is called when nothing throws");
let calls = 0;
[5, 4, 3, 2, 1].sort((a, b) => { calls++; return a - b; });
console.log("  sort     " + calls);
calls = 0;
attempt(() => [5, 4, 3, 2, 1].toSorted((a, b) => { calls++; return a - b; }));
console.log("  toSorted " + calls);

console.log("");
console.log("[1] the comparator throws at call k");
const cmpThrowingAt = (k) => { let n = 0; return (a, b) => { if (++n === k) throw new Error("call " + k); return a - b; }; };
for (const k of [1, 2, 4]) {
  const a = [5, 4, 3, 2, 1];
  const r = attempt(() => a.sort(cmpThrowingAt(k)));
  console.log("  sort     k=" + k + "   " + r.padEnd(22) + "a " + JSON.stringify(a));
  const b = [5, 4, 3, 2, 1];
  const r2 = attempt(() => b.toSorted(cmpThrowingAt(k)));
  console.log("  toSorted k=" + k + "   " + r2.padEnd(22) + "b " + JSON.stringify(b));
}

console.log("");
console.log("[2] 30 elements in a fixed shuffled order, the comparator throws at call k");
const mixed30 = () => Array.from({ length: 30 }, (_, i) => (i * 7) % 30);
const orig = JSON.stringify(mixed30());
let total = 0;
mixed30().sort((x, y) => { total++; return x - y; });
console.log("  comparator calls when nothing throws: " + total);
for (const k of [1, Math.floor(total / 2), total]) {
  const a = mixed30();
  const r = attempt(() => a.sort(cmpThrowingAt(k)));
  console.log("  sort     k=" + String(k).padEnd(4) + r.padEnd(22) + "a unchanged " + (JSON.stringify(a) === orig));
}

console.log("");
console.log("[3] a comparator that is not a function");
for (const cmp of [undefined, null, "desc", 1]) {
  const a = [2, 1];
  console.log("  " + String(JSON.stringify(cmp)).padEnd(10) + "sort     " + attempt(() => a.sort(cmp)));
  console.log("  " + "".padEnd(10) + "toSorted " + attempt(() => a.toSorted(cmp)));
}
```

- ★★★ `[1]` 여섯 줄 — `sort` 쪽 `a` 는 바뀌나?
- ★★★ `[2]` — 비교 함수가 첫 호출 · 가운데 · **마지막 호출**에서 던질 때 `a unchanged` 는 각각?
- ★★ `[3]` — `null` · `"desc"` · `1` 은 두 메서드에서 같은 답인가?
- ★ `[0]` 의 두 수는 명세가 정한 것인가?

### 7. 쓰기 한 번에 트랩이 왜 둘 불리나 (왜) ★★

- ★★ 1번 격자에서 `set` 과 `define` 이 늘 같은 수인 이유 — 트랩이 `Reflect.set` 에 **무엇을** 넘겼기 때문인가?
- ★ 그렇다면 쓰기를 셀 때는 **어느 열**만 보면 되나?

### 8. `extends Array` 에 `map` 과 `toSorted` 를 부르면 결과는 어느 클래스인가 — 왜 둘이 다른가 (연결) ★★★

- ★★★ 22번의 species 격자는 **몇 / 몇**이었나? 복사 메서드 넷은 그 표에서 어느 쪽이었나?
- ★★ 복사 메서드 넷은 결과를 **어느 명세 연산**으로 만드나? `map` 은?
- ★ 그래서 하위 클래스의 메서드를 `toSorted` 결과에서 부르면?

### 9. 복사 메서드는 어느 판인가 — 그리고 두 node 판이 갈린 블록 (연결) ★★

- ★★★ finished proposals 표에서 Change Array by Copy 는 **몇 년**인가? 목록 README 는 무엇이라 적었나?
- ★★ 이 주제에서 두 판이 갈린 탐침은 **몇 개**이고, 갈린 이유는 **몇 종류**인가?
- ★★★ node 18 의 1번 격자에서 「쓰기 트랩 0」으로 끝난 행 가운데 **실제로는 돌지도 않은 행**은 어느 것인가? 그것을 어떻게 갈랐나?

### 10. 「복사한다」는 어디까지 복사하나 (경계) ★★

- ★★ `toSorted` · `slice` · `map` 이 새로 만드는 것은 무엇이고, **새로 안 만드는 것**은 무엇인가?
- ★ 중첩 객체까지 새로 만들려면 무엇을 봐야 하나 — 이 편과 어느 주제의 경계인가?
- ★ 「비변형 메서드」 가 막지 **못하는** 원본 쓰기는 어디서 오나?

### 11. 파이썬 `sort`/`sorted` 와 JS `sort`/`toSorted` (연결) ★★★

- ★★ 파이썬 갈래 10번에서 `sorted(y)` 뒤의 `y` 는? JS 의 어느 메서드가 그 짝인가?
- ★★★ 파이썬 10번에서 정렬이 `TypeError` 로 끝난 뒤 리스트는 어떻게 남았나? JS `sort` 는 비교가 던지면?
- ★★ 그 차이는 **구현**의 차이인가, **명세**가 정한 것인가?

### 12. `slice` 와 `concat` 의 인자 규칙 — 음수, 범위 밖, 몇 겹 (경계) ★

- ★★ `slice(-2)` · `slice(3, 1)` · `slice(10)` — 던지나, 무엇을 돌려주나? `with` 와 무엇이 반대인가?
- ★★ `[1].concat(2, [3], [[4]])` 는? 문자열과 유사 배열은 펼치나? 펼칠지 정하는 기준은?
- ★ 콜백이 전부 통과시킨 `filter` 는 원본과 `===` 인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
