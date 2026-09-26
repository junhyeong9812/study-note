# js/syntax/24 — 배열 변형 메서드: 「무엇이 원본을 바꾸고 무엇을 돌려주나 — 그리고 `sort` 는 무엇으로 비교하나」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v18.19.1(기본 PATH) · v20.19.6(nvm) · Google Chrome 151.0.7922.173(판별 블록만) · x86-64 Linux.
> 배너의 `node20` 은 v20.19.6 이다. ★ 이 주제의 탐침은 **두 node 판에서 한 글자도 같았다**(판 대조기 — [2-summary.md](2-summary.md) 머리말).
>
> ★★★ **이 주제의 본체는 ② 전수 격자다.**
> 메서드마다 「반환값이 원본 그 자체인가 · 원본의 내용이 달라졌나 · `length` 가 달라졌나」를 묻고, **y 칸을 스크립트가 센다.** **1번 문항이 이 주제의 중심이다.**
>
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① ★★★ **무엇이 원본을 바꾸고, 무엇을 돌려주나**(반환값이 원본이면 체이닝이 원본을 바꾼다)
> ② ★★★ **`sort` 는 무엇으로 비교하나**(비교 함수가 없을 때 · 비교 함수가 규칙을 어길 때 · `undefined` 와 구멍)
> ③ **무엇이 명세 보장이고 무엇이 이 엔진(V8)의 관찰인가**(안정 정렬 · 「구현 정의」 순서).
>
> ★★ **예외는 타입과 메시지로만 답한다.**
>
> **선행** — [01 — 값의 종류와 `typeof`](../01-value-types-and-typeof/2-summary.md) · [14 — 프로퍼티 디스크립터와 동결](../14-property-descriptors-and-freezing/2-summary.md) ·
> [11 — 스프레드와 나머지](../11-spread-and-rest/2-summary.md) · [04 — 문자열과 UTF-16](../04-strings-and-utf16/2-summary.md)(문자열 비교가 코드 유닛 순서인 것).

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1 · 2 · 3 · 4 · 5 · 6)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **1번은 칸 하나하나에 y/n 을 적고, 마지막 줄의 수까지 세어 본다.** 메서드 이름만 보고 짐작하지 마라.
- ★★ **6번은 「던지나 / 안 던지나」를 먼저, 던지면 문구까지** 적어라.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이것은 명세인가, 이 엔진(V8)의 사정인가, 이 판의 관찰인가**」.
- ★★★ **속도·메모리에 관한 답은 하나도 없다.** 「`push` 가 `concat` 보다 빠르다」가 떠오르면 「**안 쟀다**」라고 적어라.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 메서드마다 「원본을 바꾸나」를 물으면 (예측) ★★★ 이 주제의 축

```js
// js24b-24a-mutation-grid.js
// 메서드마다 세 가지를 묻는다 -- 반환값이 원본 그 자체인가 · 원본의 내용이 달라졌나 · length 가 달라졌나.
// 스크립트가 y 칸을 직접 센다.
const rows = [
  ["push(9)", (a) => a.push(9)],
  ["pop()", (a) => a.pop()],
  ["shift()", (a) => a.shift()],
  ["unshift(9)", (a) => a.unshift(9)],
  ["splice(1, 1)", (a) => a.splice(1, 1)],
  ["splice(1, 0, 9)", (a) => a.splice(1, 0, 9)],
  ["sort()", (a) => a.sort()],
  ["reverse()", (a) => a.reverse()],
  ["fill(0)", (a) => a.fill(0)],
  ["copyWithin(0, 2)", (a) => a.copyWithin(0, 2)],
  ["slice(1)", (a) => a.slice(1)],
  ["concat([9])", (a) => a.concat([9])],
  ["map(x => x)", (a) => a.map((x) => x)],
  ["filter(x => x > 1)", (a) => a.filter((x) => x > 1)],
  ["join()", (a) => a.join()],
];
const snap = (a) => JSON.stringify(a);
console.log("start value for every row: [3,1,2]");
console.log("");
console.log("method".padEnd(20) + "returns".padEnd(12) + "same?".padEnd(7) + "content".padEnd(9) + "length".padEnd(8) + "after");
let yes = 0, cells = 0, rowsChanged = 0, both = 0;
for (const [name, run] of rows) {
  const a = [3, 1, 2];
  const before = snap(a), len0 = a.length;
  const r = run(a);
  const same = r === a, content = snap(a) !== before, length = a.length !== len0;
  const yn = (b) => (b ? "y" : "n");
  for (const b of [same, content, length]) { cells++; if (b) yes++; }
  if (content) rowsChanged++;
  if (same && length) both++;
  const shown = r === a ? "(arr)" : snap(r);
  console.log(name.padEnd(20) + String(shown).padEnd(12) + yn(same).padEnd(7) + yn(content).padEnd(9) + yn(length).padEnd(8) + snap(a));
}
console.log("");
console.log("rows whose content column is y: " + rowsChanged + " / " + rows.length);
console.log("rows where same? and length are both y: " + both + " / " + rows.length);
console.log("cells answering y: " + yes + " / " + cells);
```

- ★★★ 행마다 `returns` · `same?` · `content` · `length` · `after` 를 적어라.
- ★★ `same?` 열과 `length` 열이 **둘 다 y** 인 행이 있나?
- ★ 마지막 세 줄의 수는?

### 2. 넣고 빼는 메서드와 `splice` 가 돌려주는 것 (예측) ★★★

```js
// js24b-24b-return-values.js
// 넣고 빼는 네 메서드와 splice 는 무엇을 돌려주나 -- 원본은 옆에 찍는다.
const show = (label, a, r) => console.log(label.padEnd(28) + "-> " + JSON.stringify(r) + "   arr " + JSON.stringify(a));

console.log("[1] push / pop / unshift / shift");
let a = [1, 2];
show("a.push(3, 4)", a, a.push(3, 4));
show("a.pop()", a, a.pop());
show("a.unshift(0)", a, a.unshift(0));
show("a.shift()", a, a.shift());
const e = [];
console.log("[].pop()".padEnd(28) + "-> " + String(e.pop()));
console.log("[].shift()".padEnd(28) + "-> " + String(e.shift()));
console.log("[].push()".padEnd(28) + "-> " + String(e.push()));

console.log("");
console.log("[2] splice(start, deleteCount, ...items)");
const fresh = () => ["a", "b", "c", "d", "e"];
let b;
b = fresh(); show("splice(1, 2)", b, b.splice(1, 2));
b = fresh(); show("splice(1, 0, 'x')", b, b.splice(1, 0, "x"));
b = fresh(); show("splice(1, 2, 'x', 'y', 'z')", b, b.splice(1, 2, "x", "y", "z"));
b = fresh(); show("splice(-2)", b, b.splice(-2));
b = fresh(); show("splice(2)", b, b.splice(2));
b = fresh(); show("splice()", b, b.splice());
b = fresh(); show("splice(1, 99)", b, b.splice(1, 99));
b = fresh(); show("splice(9, 1, 'x')", b, b.splice(9, 1, "x"));

console.log("");
console.log("[3] push with an array argument");
const c = [1];
show("c.push([2, 3])", c, c.push([2, 3]));
const d = [1];
show("d.push(...[2, 3])", d, d.push(...[2, 3]));
```

- ★★★ `[1]` 의 일곱 줄 — 특히 `push` 와 `unshift` 는 **무엇을** 돌려주나?
- ★★★ `[2]` 의 여덟 줄 — 반환값과 `arr` 을 둘 다.
- ★ `[3]` 두 줄의 반환값과 `arr` 은?

### 3. 비교 함수 없이, 그리고 불리언을 돌려주는 비교 함수로 (예측) ★★★

```js
// js24b-24c-default-order.js
// 비교 함수 없이 sort() 를 부르면 무엇을 기준으로 줄 세우나.
const show = (label, r) => console.log(label.padEnd(48) + "-> " + JSON.stringify(r));

console.log("[1] no comparator");
show("[10, 9, 1].sort()", [10, 9, 1].sort());
show("[5, 25, 100, 1].sort()", [5, 25, 100, 1].sort());
show("[-1, -2, 3, -10].sort()", [-1, -2, 3, -10].sort());
show("[3, 'a', 1, 'B', true].sort()", [3, "a", 1, "B", true].sort());
show("['b', 'a', 'C', 'A'].sort()", ["b", "a", "C", "A"].sort());
show("[0.5, 1e21, 2, 1e-7].sort()", [0.5, 1e21, 2, 1e-7].sort());

console.log("");
console.log("[2] what each element is compared as");
for (const x of [10, 9, 1, -10, 1e21, 1e-7, true]) {
  console.log("  " + String(x).padEnd(8) + "String(x) = " + JSON.stringify(String(x)));
}

console.log("");
console.log("[3] with a numeric comparator");
show("[10, 9, 1].sort((a, b) => a - b)", [10, 9, 1].sort((a, b) => a - b));
show("[5, 25, 100, 1].sort((a, b) => a - b)", [5, 25, 100, 1].sort((a, b) => a - b));
show("[5, 25, 100, 1].sort((a, b) => b - a)", [5, 25, 100, 1].sort((a, b) => b - a));
show("['b','a','C','A'].sort(localeCompare)", ["b", "a", "C", "A"].sort((x, y) => x.localeCompare(y, "en")));

console.log("");
console.log("[4] a comparator that returns a boolean");
const boolCmp = (a, b) => a > b;
for (const arr of [[3, 1, 2], [1, 3, 2], [2, 1], [5, 1, 4, 2, 3], [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]]) {
  const input = JSON.stringify(arr);
  show("  " + input + ".sort((a, b) => a > b)", arr.sort(boolCmp));
}

console.log("");
console.log("[5] a comparator argument that is not a function");
for (const [label, arg] of [["sort(undefined)", undefined], ["sort(null)", null], ["sort(1)", 1], ["sort('desc')", "desc"]]) {
  try {
    console.log(label.padEnd(48) + "-> " + JSON.stringify([2, 1].sort(arg)));
  } catch (e) {
    console.log(label.padEnd(48) + "-> " + e.constructor.name + " 「" + e.message + "」");
  }
}
```

- ★★★ `[1]` 여섯 줄의 결과. `[2]` 가 힌트다.
- ★★★ `[4]` 다섯 줄 — 입력과 결과를 나란히 적어라.
- ★★ `[5]` 네 줄 — 통과하나, 던지나?

### 4. `undefined` 와 빈 자리가 섞인 배열을 정렬하면 (예측) ★★★

```js
// js24b-24g-undefined-and-holes.js
// undefined 와 구멍(빈 자리)이 섞인 배열을 sort 하면 -- 결과 · 각 자리가 구멍인가 · 비교 함수가 무엇을 받았나.
const describe = (a) => "[" + Array.from({ length: a.length }, (_, i) => (i in a ? String(a[i]) : "<hole>")).join(", ") + "]  length " + a.length;

console.log("[1] no comparator");
const a = [3, undefined, 1, , 2, undefined, , 10];
console.log("before  " + describe(a));
a.sort();
console.log("after   " + describe(a));

console.log("");
console.log("[2] numeric comparator, logging every call");
const b = [3, undefined, 1, , 2];
const seen = [];
b.sort((x, y) => { seen.push(String(x) + "," + String(y)); return x - y; });
console.log("after   " + describe(b));
console.log("calls   " + seen.length + "   " + seen.join(" | "));
console.log("any call received undefined? " + (seen.some((s) => s.includes("undefined")) ? "y" : "n"));

console.log("");
console.log("[3] a comparator that returns -1 when x is undefined");
const c = [2, undefined, 1];
c.sort((x, y) => (x === undefined ? -1 : y === undefined ? 1 : x - y));
console.log("after   " + describe(c));

console.log("");
console.log("[4] null and undefined in one array");
const d = [2, null, 1, undefined];
d.sort();
console.log("after   " + describe(d));
const e2 = [2, null, 1, undefined];
e2.sort((x, y) => x - y);
console.log("numeric " + describe(e2));
```

- ★★★ `[1]` 의 `after` 줄을 자리마다 적어라 — 값인가, `undefined` 인가, `<hole>` 인가.
- ★★★ `[2]` 에서 비교 함수가 받은 인자 쌍에 `undefined` 가 있나?
- ★★ `[3]` 의 결과 — 비교 함수의 뜻대로 되나?
- ★ `[4]` 두 줄.

### 5. 반환값을 새 이름으로 받아 쓰면 (예측) ★★★

```js
// js24b-24h-same-array.js
// 원본을 돌려주는 메서드의 반환값을 「새 배열」로 받아 쓰면 -- 두 이름이 무엇을 가리키나.
const j = (x) => JSON.stringify(x);

console.log("[1] rev = orig.reverse()");
const orig = [1, 2, 3];
const rev = orig.reverse();
console.log("rev  " + j(rev) + "   orig " + j(orig) + "   rev === orig " + (rev === orig));

console.log("");
console.log("[2] four chains");
const scores = [30, 10, 20];
const top = scores.sort((a, b) => b - a).slice(0, 2);
console.log("top    " + j(top) + "   scores " + j(scores));
const names = ["c", "a", "b"];
const last = names.sort().reverse()[0];
console.log("last   " + j(last) + "   names " + j(names));
const src = [3, 1, 2];
const copied = src.slice().sort();
console.log("copied " + j(copied) + "   src " + j(src));
const spread = [...src].reverse();
console.log("spread " + j(spread) + "   src " + j(src));

console.log("");
console.log("[3] fill with an object");
const grid = Array(3).fill([]);
grid[0].push("x");
console.log("grid " + j(grid));
console.log("grid[0] === grid[1] " + (grid[0] === grid[1]) + "   grid[1] === grid[2] " + (grid[1] === grid[2]));
const rows = Array.from({ length: 3 }, () => []);
rows[0].push("x");
console.log("rows " + j(rows) + "   rows[0] === rows[1] " + (rows[0] === rows[1]));
const fresh = Array(3);
console.log("Array(3)            length " + fresh.length + "   0 in it " + (0 in fresh));
console.log("Array(3).fill(0)    " + j(Array(3).fill(0)));
console.log("[1,2,3,4].fill(9, 1, 3)  " + j([1, 2, 3, 4].fill(9, 1, 3)));
console.log("[1,2,3,4].fill(9, -1)    " + j([1, 2, 3, 4].fill(9, -1)));

console.log("");
console.log("[4] copyWithin(target, start, end)");
for (const [label, args] of [["copyWithin(0, 3)", [0, 3]], ["copyWithin(1, 0)", [1, 0]], ["copyWithin(0, 1, 3)", [0, 1, 3]], ["copyWithin(-2, 0)", [-2, 0]], ["copyWithin(2, 0, 2)", [2, 0, 2]]]) {
  const a = [1, 2, 3, 4, 5];
  const r = a.copyWithin(...args);
  console.log("  [1,2,3,4,5]." + label.padEnd(22) + "-> " + j(r) + "   length " + a.length + "   same " + (r === a));
}

console.log("");
console.log("[5] assigning to length");
const t = [1, 2, 3, 4, 5];
const alias = t;
t.length = 2;
console.log("after length = 2   t " + j(t) + "   alias " + j(alias) + "   t[3] " + t[3]);
t.length = 4;
console.log("after length = 4   t.length " + t.length + "   2 in t " + (2 in t) + "   t[2] " + t[2]);
alias.length = 0;
console.log("after alias.length = 0   t " + j(t));
for (const v of [-1, 1.5, 2 ** 32]) {
  try { const x = [1]; x.length = v; console.log("length = " + String(v).padEnd(12) + "-> " + x.length); }
  catch (e) { console.log("length = " + String(v).padEnd(12) + "-> " + e.constructor.name + " 「" + e.message + "」"); }
}
```

- ★★★ `[1]` 과 `[2]` 의 네 줄 — 원본(`orig` · `scores` · `names` · `src`)은 각각 어떻게 남나?
- ★★★ `[3]` 의 `grid` 와 `rows` 는?
- ★★ `[4]` 다섯 줄.
- ★★ `[5]` — `alias` 는 무엇을 보나? `length` 를 늘리면 새 자리는 값인가 구멍인가? 마지막 세 줄은?

### 6. 동결된 배열에 부르면 (예측) ★★

```js
// js24b-24i-frozen-target.js
"use strict";
// 동결된 배열에 변형 메서드를 부르면 -- 던지나, 던지면 무엇을. 원본은 어떻게 남나.
const calls = [
  ["push(9)", (a) => a.push(9)],
  ["pop()", (a) => a.pop()],
  ["shift()", (a) => a.shift()],
  ["unshift(9)", (a) => a.unshift(9)],
  ["splice(0, 1)", (a) => a.splice(0, 1)],
  ["sort()", (a) => a.sort()],
  ["reverse()", (a) => a.reverse()],
  ["fill(0)", (a) => a.fill(0)],
  ["copyWithin(0, 1)", (a) => a.copyWithin(0, 1)],
  ["length = 0", (a) => { a.length = 0; }],
  ["slice()", (a) => a.slice()],
];
for (const input of [[3, 1, 2], [1, 2, 3], []]) {
  console.log("frozen " + JSON.stringify(input));
  for (const [label, run] of calls) {
    const a = Object.freeze(input.slice());
    let r;
    try { run(a); r = "no throw"; }
    catch (e) { r = e.constructor.name + " 「" + e.message + "」"; }
    console.log("  " + label.padEnd(18) + r.padEnd(70) + "  after " + JSON.stringify(a));
  }
}
```

- ★★★ `frozen [3,1,2]` 의 열한 줄 — 던지나? 던지면 문구는 **몇 가지**인가?
- ★★★ `frozen [1,2,3]` 에서 `sort()` 는? **이미 정렬돼 있다.**
- ★★ `frozen []` 에서 **던지지 않는** 메서드는 어느 것인가? 그 가름의 기준을 한 문장으로.

### 7. 안정 정렬은 언제부터 명세의 약속인가 — 그리고 두 node 판으로는 그 경계를 왜 못 보나 (경계) ★★★

- ★★★ ES2018(9판)과 ES2019(10판)의 `Array.prototype.sort` 첫 문장은 각각 무엇이라 적나?
- ★★ 최신 초안은 그 문장을 어디로 옮겼나 — `SortIndexedProperties` 의 어느 조건이 「안정」인가?
- ★★ 이 머신의 두 node 판은 경계의 어느 쪽인가? 그래서 이 문서는 안정성을 **무엇으로** 보였나?

### 8. 비교 함수가 규칙을 어기면 명세는 결과를 무엇이라 부르나 (왜) ★★★

- ★★★ 명세가 「consistent comparator」에 요구하는 조건 가운데 `(a, b) => a > b` 가 어기는 것은?
- ★★★ 그때의 정렬 순서를 명세는 무엇이라 부르나? 그러면 3번 `[4]` 의 결과는 **어느 층의 사실**인가?
- ★★ 난수를 돌려주는 비교 함수로 같은 입력을 2만 번 정렬하면 **서로 다른 결과가 몇 가지** 나올까? 그 수는 흔들리나?

### 9. 파이썬 `list.sort` 와 JS `sort` — 무엇을 돌려주고, 기본은 무엇으로 비교하나 (연결) ★★★

- ★★★ 파이썬 갈래 10번에서 `x.sort()` 는 무엇을 돌려줬나? JS 의 `a.sort()` 는?
- ★★★ 그래서 **체이닝에서 생기는 사고의 모양**이 두 언어에서 어떻게 다른가?
- ★★ `[3, 'a', 1]` 을 기본 정렬하면 파이썬은? JS 는?
- ★ 안정성은 두 언어에서 각각 **누가** 약속하나?

### 10. `sort` 는 이미 정렬된 배열도 왜 다시 쓰나 (왜) ★★

- ★★ 명세 `Array.prototype.sort` 는 정렬한 목록을 원본에 **어떻게** 되돌려 놓나?
- ★★ 그것이 6번의 `frozen [1,2,3]` 과 `frozen []` 을 어떻게 설명하나?
- ★ 구멍은 그 과정의 어디서 빠지고 어디서 다시 생기나?
- ★★ 6번 소스의 첫 줄(`"use strict"`)을 빼면 `push`·`sort` 는 던지나? `a.length = 0` 과 `a[0] = 9` 는?

### 11. `push`·`pop`·`shift`·`unshift` 와 스택·큐 — 어디까지가 이 주제인가 (경계) ★★

- ★★ 넷 중 **스택**을 만드는 짝과 **큐**를 만드는 짝은?
- ★★ 「`shift` 가 느리다」는 이 문서에서 어느 칸에 들어가나?
- ★ `cs/foundations/data-structures-basics/` 가 **끝내는 것**과 이 주제가 **시작하는 것**을 한 줄씩.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
