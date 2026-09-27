# js/syntax/48 — 깊은 복사 수단 비교: 「네 수단은 값마다 무엇을 보존하고, 무엇을 원본과 나눠 갖고, 무엇을 잃나」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v18.19.1 · v20.19.6 · Google Chrome 151 · Python 3.12.3 · x86-64 Linux.
>
> ★★★ **이 주제의 본체는 보존 격자다** — 값 17행 × 수단 넷 × 판 셋. **1번 · 6번 · 7번 문항이 이 주제의 중심이다.**
>
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① ★★★ **네 수단이 값마다 보존하나 · 공유하나 · 바꾸나 · 던지나**
> ② ★★★ **「잃은 칸이 적다」와 「깊다」가 왜 다른 말인가**
> ③ ★★ **`structuredClone` 이 거절하는 것 · 떨어뜨리는 것 · 그 답을 누가 정하나.**
>
> **선행** — [31](../31-json/2-summary.md) · [11](../11-spread-and-rest/2-summary.md) · [27](../27-object-static-methods/2-summary.md).

## 이 파일을 푸는 법

- ★★ **예측형 문항(1\~5)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **1번은 칸마다 `kept` · `shared` · `->` · `throws` 넷 중 하나**만 먼저 적어도 된다 — `->` 와 `throws` 의 뒷말은 그다음이다.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이 칸은 ECMA-262 가 정했나, 호스트가 정했나**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 보존 격자 (예측) ★★★ 이 주제의 축

```js
// js48b-48a-copy-grid.js
// Four ways to copy an object, and one kind of value per row. What does the copy hold?
//   JSON      JSON.parse(JSON.stringify(src))
//   spread    { ...src }
//   assign    Object.assign({}, src)
//   clone     structuredClone(src)          (a host API -- HTML, not ECMA-262)
// A cell is one of
//   kept         the copy has an equal value that is not the source's object (or an equal primitive)
//   shared       the copy holds the very object the source holds (===)
//   -> what      the copy holds something else
//   throws X     the copy threw; X is the exception's constructor name and its name
// The last lines count the cells.
const means = [
  ["JSON", (s) => JSON.parse(JSON.stringify(s))],
  ["spread", (s) => ({ ...s })],
  ["assign", (s) => Object.assign({}, s)],
  ["clone", (s) => structuredClone(s)],
];
const kind = (x) => {
  if (x === null) return "null";
  if (typeof x !== "object") return typeof x === "string" ? "string " + JSON.stringify(x) : typeof x + " " + String(x);
  const p = Object.getPrototypeOf(x);
  return (p === Object.prototype ? "plain " : (p && p.constructor ? p.constructor.name + " " : "null-proto ")) + JSON.stringify(x);
};
// each row: [label, make() -> src, judge(copy, src) -> cell text or null for "kept"]
const obj = (src, c, test) => (c.v === src.v ? "shared" : test(c.v) ? null : "-> " + ("v" in c ? kind(c.v) : "key gone"));
class Point { constructor() { this.x = 1; } }
const s = Symbol("s");
const rows = [
  ["Date", () => ({ v: new Date(0) }), (c, src) => obj(src, c, (v) => v instanceof Date && v.getTime() === 0)],
  ["Map", () => ({ v: new Map([["k", 1]]) }), (c, src) => obj(src, c, (v) => v instanceof Map && v.get("k") === 1)],
  ["Set", () => ({ v: new Set([1]) }), (c, src) => obj(src, c, (v) => v instanceof Set && v.has(1))],
  ["RegExp", () => ({ v: /a/g }), (c, src) => obj(src, c, (v) => v instanceof RegExp && String(v) === "/a/g")],
  ["undefined property", () => ({ v: undefined }), (c) => ("v" in c ? null : "-> key gone")],
  ["NaN", () => ({ v: NaN }), (c) => (Object.is(c.v, NaN) ? null : "-> " + kind(c.v))],
  ["-0", () => ({ v: -0 }), (c) => (Object.is(c.v, -0) ? null : "-> " + kind(c.v))],
  ["BigInt", () => ({ v: 1n }), (c) => (c.v === 1n ? null : "-> " + kind(c.v))],
  ["function", () => ({ v: () => 1 }), (c, src) => (c.v === src.v ? "shared" : "-> " + ("v" in c ? kind(c.v) : "key gone"))],
  ["symbol key", () => ({ [s]: 1 }), (c) => (c[s] === 1 ? null : "-> key gone")],
  ["cycle", () => { const o = {}; o.me = o; return o; }, (c, src) => (c.me === c ? null : c.me === src ? "shared (c.me === src)" : "-> " + kind(c.me))],
  ["class instance", () => new Point(), (c) => (Object.getPrototypeOf(c) === Point.prototype ? null : "-> " + kind(c))],
  ["getter", () => ({ get v() { return 1; } }), (c) => (typeof Object.getOwnPropertyDescriptor(c, "v").get === "function" ? null : "-> data property " + c.v)],
  ["same object twice", () => { const t = {}; return { a: t, b: t }; }, (c, src) => (c.a === src.a ? "shared" : c.a === c.b ? null : "-> two objects")],
  ["Error with cause", () => ({ v: new TypeError("m", { cause: "c" }) }),
    (c, src) => obj(src, c, (v) => v instanceof TypeError && v.message === "m" && v.cause === "c")],
  ["Uint8Array", () => ({ v: new Uint8Array([1, 2]) }), (c, src) => obj(src, c, (v) => v instanceof Uint8Array && v.join() === "1,2")],
  ["nested plain object", () => ({ v: { d: 1 } }), (c, src) => obj(src, c, (v) => v.d === 1)],
];
const cellOf = (make, copy, judge) => {
  const src = make();
  let c;
  try { c = copy(src); } catch (e) { return "throws " + e.constructor.name + "/" + e.name; }
  return judge(c, src) ?? "kept";
};
const table = rows.map(([label, make, judge]) => [label, means.map(([, copy]) => cellOf(make, copy, judge))]);
const W = means.map((_, j) => Math.max(...table.map(([, cells]) => cells[j].length)) + 2);
const line = (label, cells) => console.log((label.padEnd(21) + cells.map((t, j) => t.padEnd(W[j])).join("")).trimEnd());
line("", means.map(([m]) => m));
let notKept = 0, shared = 0, total = 0;
for (const [label, cells] of table) {
  for (const t of cells) { total += 1; if (t.startsWith("->") || t.startsWith("throws")) notKept += 1; else if (t.startsWith("shared")) shared += 1; }
  line(label, cells);
}
const per = (pred) => means.map(([m], j) => m + " " + table.filter(([, cells]) => pred(cells[j])).length).join(" · ");
console.log("");
console.log("per column, kept:          " + per((t) => t === "kept"));
console.log("per column, shared:        " + per((t) => t.startsWith("shared")));
console.log("per column, not preserved: " + per((t) => t.startsWith("->") || t.startsWith("throws")));
console.log("cells shared with the source (===): " + shared + " / " + total);
console.log("cells not preserved (-> or throws): " + notKept + " / " + total);
```

```sh
# js48b-48a-copy-grid.sh
#!/usr/bin/env bash
# The copy grid (js48b-48a-copy-grid.js) in node20 in full, then whether node18 and Chrome 151 print the same.
set -u -o pipefail
cd "$(dirname "$0")" || exit 1
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
a="$("$N20" js48b-48a-copy-grid.js)" || exit 1
b="$("$N18" js48b-48a-copy-grid.js)" || exit 1
c="$(./js48b-browser.sh js48b-48a-copy-grid.js)" || exit 1
echo "--- node20"; printf '%s\n' "$a"
echo ""
[ "$b" = "$a" ] && r=yes || r=no
echo "node18 prints the same as node20: $r"
[ "$c" = "$a" ] && r=yes || r=no
echo "Chrome 151 prints the same as node20: $r"
```

- ★★★ `JSON` 열의 17칸은 각각? 이 열에서 `kept` 인 행은?
- ★★★ `spread` 열과 `assign` 열은 서로 몇 칸이 다른가? `shared` 가 아닌 행은 어느 것인가?
- ★★★ `clone` 열에서 `kept` 가 아닌 칸은 어느 행이고 각각 무엇인가?
- ★★ 「per column」 세 줄과 마지막 두 줄의 `N / 68` 은? 비교 두 줄은?

### 2. `structuredClone` 이 받지 않는 값 (예측) ★★

```js
// js48b-48b-clone-details.js
// structuredClone up close: what it refuses (and with what message), what an Error keeps,
// what it does with property-level things, and what the transfer option does to an ArrayBuffer.
const show = (label, f) => {
  let r;
  try { r = f(); } catch (e) { r = "throws " + e.constructor.name + " (name " + e.name + ", code " + e.code + ") 「" + e.message + "」"; }
  console.log("  " + label.padEnd(36) + r);
};
console.log("[1] values it refuses");
show("a function", () => structuredClone({ v: function f() {} }));
show("an arrow function", () => structuredClone({ v: () => 1 }));
show("a symbol value", () => structuredClone({ v: Symbol("s") }));
show("a WeakMap", () => structuredClone({ v: new WeakMap() }));
show("a Promise", () => structuredClone({ v: Promise.resolve(1) }));
show("DOMException instanceof Error", () => { try { structuredClone(() => 1); } catch (e) { return String(e instanceof Error); } });

console.log("[2] Error objects -- what the copy has");
class MyError extends Error { constructor(m) { super(m); this.name = "MyError"; this.extra = 42; } }
const errs = [
  ["new TypeError('m', { cause })", () => new TypeError("m", { cause: { code: 7 } })],
  ["new RangeError('m')", () => new RangeError("m")],
  ["new MyError('m')  (subclass)", () => new MyError("m")],
];
for (const [label, make] of errs) {
  const e = make();
  const c = structuredClone(e);
  console.log("  " + label);
  console.log("    constructor " + c.constructor.name + " · name " + c.name + " · message " + c.message +
    " · cause " + JSON.stringify(c.cause) + " · cause is a new object " + (c.cause !== undefined && c.cause !== e.cause) +
    " · extra " + c.extra + " · stack is a string " + (typeof c.stack === "string") + " · stack equal " + (c.stack === e.stack));
}

console.log("[3] property-level things");
let reads = 0;
const src = {};
Object.defineProperty(src, "counted", { get() { reads += 1; return reads; }, enumerable: true });
Object.defineProperty(src, "hidden", { value: 1, enumerable: false });
const frozen = Object.freeze({ a: 1 });
show("getter read during the copy", () => { structuredClone(src); return "reads " + reads; });
show("non-enumerable key copied", () => String(Object.hasOwn(structuredClone(src), "hidden")));
show("frozen source -> copy frozen", () => String(Object.isFrozen(structuredClone(frozen))));
const d = new Date(0); d.note = "x";
show("own property on a Date copied", () => String(structuredClone(d).note));
const arr = [1, 2]; arr.extra = "x";
show("own property on an Array copied", () => String(structuredClone(arr).extra));

console.log("[4] the transfer option");
const buf = new ArrayBuffer(8);
const moved = structuredClone({ buf }, { transfer: [buf] });
show("source byteLength after transfer", () => String(buf.byteLength));
show("copy byteLength", () => String(moved.buf.byteLength));
const buf2 = new ArrayBuffer(8);
structuredClone({ buf2 });
show("source byteLength without transfer", () => String(buf2.byteLength));
```

- ★★ `[1]` 다섯 줄의 생성자 이름 · `name` · `code` 는? 여섯째 줄은?
- ★★ 같은 소스를 Chrome 151 에서 돌리면 `[1]` 의 무엇이 달라지나?

### 3. `Error` 를 복사하면 (예측) ★★★

- ★★★ 2번 소스의 `[2]` — 세 오류 각각의 `constructor` · `name` · `cause` · `extra` · `stack` 두 칸은?

### 4. 속성 수준의 것들과 `transfer` (예측) ★★

- ★★ 2번 소스의 `[3]` 다섯 줄과 `[4]` 세 줄은?

### 5. CPython 에서 같은 행들 (예측) ★★

```python
# js48b-48d-python.py
# The same rows asked of CPython's copy.deepcopy: a class instance, a property, an exception with a cause, a function.
import copy


class Point:
    def __init__(self):
        self.x = 1

    @property
    def doubled(self):
        return self.x * 2


class MyError(Exception):
    pass


p = Point()
c = copy.deepcopy(p)
print("[1] class instance: type(copy) is Point ->", type(c) is Point, "· copy is p ->", c is p)
print("[2] property on the class: copy.doubled ->", c.doubled)

e = MyError("m")
e.__cause__ = ValueError("c")
e.extra = 42
ce = copy.deepcopy(e)
print("[3] exception: type ->", type(ce).__name__, "· args ->", ce.args, "· extra ->", getattr(ce, "extra", None),
      "· __cause__ ->", repr(ce.__cause__))


def f():
    return 1


print("[4] function: deepcopy(f) is f ->", copy.deepcopy(f) is f)
```

- ★★ 네 줄의 참/거짓과 값은? 그중 1번 격자의 `clone` 열과 **반대로** 나오는 것은 어느 행인가?

### 6. `shared` 칸을 어떻게 셀까 (왜) ★★★

- ★★★ 1번 격자의 `shared` 칸을 「보존」으로 세면 네 열의 순위가 어떻게 바뀌나? 그렇게 세면 왜 틀리나 — 어떤 쓰기 한 줄이 그것을 드러내나?

### 7. 칸마다 누가 정하나 (경계) ★★★

- ★★★ 1번 격자의 네 열과 2번의 출력 가운데, **ECMA-262** 가 정한 것 · **호스트(HTML)** 가 정한 것 · **이 판의 구현**으로만 말할 수 있는 것을 갈라라. 세 판이 같았다는 사실은 이 구분을 얼마나 도와주나?

### 8. 조용한 실패와 시끄러운 실패 (왜) ★★

- ★★ 함수 속성을 만났을 때 JSON 왕복과 `structuredClone` 의 실패 모양은 어떻게 다른가? 같은 「심볼」이라도 키와 값에서 `structuredClone` 의 실패가 갈리는 것은?

### 9. 네 수단이 함께 잃는 것 (경계) ★★

- ★★ 1번 격자에서 네 수단 모두 잃는 행은 무엇이고, 그 행들에 공통인 것은? 클래스 인스턴스를 깊이 복사해야 하면 무엇에 기대야 하나?

### 10. 「더 빠르다」를 적지 않는 이유 (연결) ★

- ★ 「`structuredClone` 이 JSON 왕복보다 빠르다」를 이 문서에 적으려면 무엇을 먼저 세워야 하나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
