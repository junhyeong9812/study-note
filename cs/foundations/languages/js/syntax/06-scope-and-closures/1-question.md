# js/syntax/06 — 스코프와 클로저: 「이 함수는 어느 칸을 몇 개 붙들고 있나」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v18.19.1(기본 PATH) · v20.19.6(nvm) · x86-64 Linux.
> 배너의 `node20` 은 v20.19.6, `node18` 은 v18.19.1 이다.
>
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① **이름을 정의된 자리에서 찾는다는 것** ② ★★★ **루프 클로저의 원인이 「값」이 아니라 「서로 다른 변수 개수」라는 것**
> ③ **클로저가 붙드는 것이 값이 아니라 칸이라는 것**.
> ★★★ **2번이 이 주제의 축**이다 — [05번 4번 절](../05-var-let-const-and-tdz/2-summary.md)이 값으로 보인 것을 **개수로 다시 센다.**
> ★★ **예외는 타입과 메시지로만 답한다** — 이 문서의 블록에는 스택트레이스가 한 줄도 없다.
> ★ **6번은 「관찰」이다.** GC 시점은 명세가 정하지 않는다 — 답을 보장으로 적으면 틀린다.
>
> **선행** — [05 — `var`·`let`·`const` 와 TDZ](../05-var-let-const-and-tdz/2-summary.md).
> 블록 스코프·TDZ·`const` 의 규칙은 **전부 그쪽이 정본**이다. 여기서 다시 묻지 않는다.
>
> ★★ **`this` 는 이 주제가 아니다.** 이름 규칙을 `this` 에 적용하면 07번의 사고가 전부 여기서 시작한다.

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1\~6)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **2번은 「함수 개수」와 「변수 개수」를 따로 적어야** 답이다. 값만 적으면 절반이다.
- ★★★ **3번은 「칸이 새것이다」와 「값이 이어진다」를 둘 다** 적어야 답이다.
- ★★ **6번은 「대조군이 왜 필요한가」까지** 적어야 답이다.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이것은 명세인가, 이 엔진의 사정인가, 이 판의 관찰인가**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 같은 이름이 네 층에 있을 때 (예측) ★★

```js
// js06b-06a-lexical-scope.js
// 이름을 어디서 찾나 — 정의된 자리인가 부른 자리인가.
// 라벨은 전부 ASCII 다 — 한글을 padEnd 격자에 넣으면 칸이 어긋난다.
function probe(label, run) {
  let r;
  try { r = JSON.stringify(run()); }
  catch (e) { r = e.constructor.name + ": " + e.message; }
  console.log("  " + label.padEnd(36) + " -> " + r);
}

const where = "module";

console.log("[1] 이름은 정의된 자리에서 바깥으로 올라가며 찾는다");
function outer() {
  const where = "outer";
  function middle() {
    function inner() { return where; }
    return inner();
  }
  return middle();
}
probe("inner() finds it in outer", outer);
probe("no local at all -> module level", () => { function f() { return where; } return f(); });
probe("missing name", () => { function f() { return nowhere; } return f(); });

console.log("");
console.log("[2] 부른 자리의 지역 변수는 안 보인다 -- 동적 스코프가 아니다");
function readsWhere() { return where; }
function callerWithOwn() { const where = "caller"; return readsWhere(); }
probe("caller has its own `where`", callerWithOwn);

console.log("");
console.log("[3] 정의된 자리가 다르면 같은 소스라도 답이 다르다");
function makeReader() { const where = "inside makeReader"; return () => where; }
probe("reader defined inside", () => makeReader()());
probe("reader defined outside", () => (() => where)());

console.log("");
console.log("[4] 스코프 체인은 몇 겹이든 올라간다 -- 가장 가까운 것이 이긴다");
function depth() {
  const seen = [];
  const n = "L0";
  { const n = "L1"; { const n = "L2"; { seen.push(n); } } }
  { const n = "L1b"; seen.push(n); }
  seen.push(n);
  return seen;
}
probe("nearest wins at each level", depth);

console.log("");
console.log("[5] 함수 몸통은 자기 스코프를 만들고 블록도 만든다");
probe("block does not leak let", () => { { let b = 1; } return typeof b; });
probe("function does not leak var", () => { function f() { var v = 1; } f(); return typeof v; });
probe("inner sees outer, not the reverse", () => {
  const outerName = "o";
  function f() { const innerName = "i"; return outerName + innerName; }
  return [f(), typeof innerName];
});
```

- 다섯 묶음의 출력을 각각 적으면?
- ★★★ `[2]` 에서 **부른 쪽에 `where = "caller"` 가 있는데도** 무엇이 나오는가? 그것이 무엇을 증명하는가?
- ★★ `[3]` 의 두 줄은 **소스가 거의 같은데** 왜 답이 다른가?
- ★★ `[4]` 의 세 값을 각각 적고, 그 셋을 한 문장의 규칙으로 줄이면?
- ★ `[5]` 마지막 줄이 `["oi", ...]` 뒤에 무엇을 붙이는가? 길이 몇 방향인가?

### 2. 함수는 셋인데 변수는 몇 개인가 (예측) ★★★ 이 주제의 축

```js
// js06b-06b-box-count.js
// 루프 클로저를 「값」이 아니라 「서로 다른 변수 개수」로 가른다.
// JS 에는 파이썬의 __closure__ 도 Go 의 포인터도 없다 -- 잡힌 변수에 손잡이가 없다.
// 그래서 개수를 **쓰기 탐침**으로 센다: 한 함수로 써서 다른 함수의 읽기가 따라 바뀌면 같은 변수다.
// 라벨은 전부 ASCII 다.

// 쓰기 탐침 -- handles[a] 로 써서 값이 따라 바뀐 것들을 한 무리로 묶는다.
// 무리의 개수가 곧 「서로 다른 변수 개수」다. 주소를 한 번도 안 쓴다.
// ★ 쓰기가 아예 안 먹는 경우(const)는 세지 않고 "n/a" 로 돌려준다 -- 잴 것이 없는 것과 안 잰 것은 다르다.
function countBoxes(handles) {
  const group = new Array(handles.length).fill(-1);
  let boxes = 0;
  for (let a = 0; a < handles.length; a++) {
    if (group[a] !== -1) continue;
    const mark = "probe-" + a;
    handles[a].set(mark);
    if (handles[a].get() !== mark) return { boxes: "n/a", group: "write refused" };
    for (let b = a; b < handles.length; b++) {
      if (group[b] === -1 && handles[b].get() === mark) group[b] = boxes;
    }
    boxes += 1;
  }
  return { boxes, group: JSON.stringify(group) };
}

const builders = [
  ["for (var i)", () => { const h = []; for (var i = 0; i < 3; i++) h.push({ get: () => i, set: (v) => { i = v; } }); return h; }],
  ["for (let i)", () => { const h = []; for (let i = 0; i < 3; i++) h.push({ get: () => i, set: (v) => { i = v; } }); return h; }],
  ["var + IIFE", () => { const h = []; for (var i = 0; i < 3; i++) (function (j) { h.push({ get: () => j, set: (v) => { j = v; } }); })(i); return h; }],
  ["var + let copy in body", () => { const h = []; for (var i = 0; i < 3; i++) { let j = i; h.push({ get: () => j, set: (v) => { j = v; } }); } return h; }],
  ["for (let x of ...)", () => { const h = []; for (let x of [0, 1, 2]) h.push({ get: () => x, set: (v) => { x = v; } }); return h; }],
  ["for (const x of ...)", () => { const h = []; for (const x of [0, 1, 2]) h.push({ get: () => x, set: (v) => { try { x = v; } catch (e) { return e; } } }); return h; }],
  ["while + let outside", () => { const h = []; let i = 0; while (i < 3) { h.push({ get: () => i, set: (v) => { i = v; } }); i++; } return h; }],
  ["while + let inside", () => { const h = []; let i = 0; while (i < 3) { let j = i; h.push({ get: () => j, set: (v) => { j = v; } }); i++; } return h; }],
  ["factory make(i)", () => { const make = (j) => ({ get: () => j, set: (v) => { j = v; } }); const h = []; for (var i = 0; i < 3; i++) h.push(make(i)); return h; }],
];

console.log("[1] 함수는 늘 셋이다 -- 갈리는 것은 그 셋이 보는 변수의 개수다");
console.log("  " + "how the loop declares".padEnd(24) + "fns".padEnd(5) + "boxes".padEnd(7) + "which box".padEnd(15) + "read");
console.log("  " + "-".repeat(24) + "-".repeat(5) + "-".repeat(7) + "-".repeat(15) + "-".repeat(9));
for (const [label, build] of builders) {
  const read = JSON.stringify(build().map((h) => h.get()));
  const n = build().length;
  const { boxes, group } = countBoxes(build());
  console.log("  " + label.padEnd(24) + String(n).padEnd(5) + String(boxes).padEnd(7) + group.padEnd(15) + read);
}

console.log("");
console.log("[2] 탐침이 무엇을 했는지 한 짝만 펼쳐 본다");
function pair(label, build) {
  const h = build();
  const before = h.map((x) => x.get());
  h[0].set("WRITTEN");
  const after = h.map((x) => x.get());
  console.log("  " + label.padEnd(14) + " before " + JSON.stringify(before).padEnd(12) +
              " after writing through fn0 " + JSON.stringify(after));
}
pair("for (var i)", builders[0][1]);
pair("for (let i)", builders[1][1]);

console.log("");
console.log("[3] const 줄은 쓰기 탐침이 부적용이다 -- 그 자리는 for (let x of) 로 잰다");
const constHandles = builders[5][1]();
let what;
const thrown = constHandles[0].set("x");
what = thrown ? thrown.constructor.name + ": " + thrown.message : "no error";
console.log("  writing through a `const` handle -> " + what + ", still reads " + JSON.stringify(constHandles[0].get()));
```

- 아홉 줄의 `boxes`·`which box`·`read` 를 각각 적으면?
- ★★★ **`read` 가 같은데 `boxes` 가 다른 줄**이 있는가? 반대는?
- ★★★ `while + let outside` 가 `for (let i)` 와 갈리는 이유는? 이 한 줄이 무엇을 반박하는가?
- ★★ `var + IIFE` 와 `var + let copy in body` 와 `factory make(i)` 가 **같은 답을 내는 이유**는?
- ★★ `for (const x of ...)` 줄만 왜 `n/a` 인가? 그것은 「안 쟀다」인가 「잴 것이 없다」인가?
- ★ 이 탐침이 **주소를 한 번도 안 쓰는 것**이 왜 중요한가?

### 3. `for` 헤더의 `let` 이 회차마다 하는 일 (예측) ★★★

```js
// js06b-06c-per-iteration.js
// for 헤더의 let 이 회차마다 새 칸을 만드는 것을 명세 용어 없이 관찰로 보인다.
// 창은 넷이다: ① 쓰기 탐침 ② 값이 이어지나 ③ 회차 안에서 쓰면 다음 회차가 보나 ④ 어느 문법이 그 일을 하나
function probe(label, run) {
  let r;
  try { r = JSON.stringify(run()); }
  catch (e) { r = e.constructor.name + ": " + e.message; }
  console.log("  " + label.padEnd(40) + " -> " + r);
}

console.log("[1] 칸이 새로 생겼다는 것 -- 한 회차에서 쓴 값이 다른 회차에 안 번진다");
probe("let: write in fn0 leaks to fn1?", () => {
  const set = [], get = [];
  for (let i = 0; i < 3; i++) { set.push((v) => { i = v; }); get.push(() => i); }
  set[0]("X");
  return get.map((g) => g());
});
probe("var: write in fn0 leaks to fn1?", () => {
  const set = [], get = [];
  for (var i = 0; i < 3; i++) { set.push((v) => { i = v; }); get.push(() => i); }
  set[0]("X");
  return get.map((g) => g());
});

console.log("");
console.log("[2] 그런데 값은 이어진다 -- 새 칸이 앞 회차의 값을 받아 온다");
probe("body sets i = 1 on the first pass", () => {
  const seen = [];
  for (let i = 0; i < 3; i++) { seen.push(i); if (i === 0) i = 1; }
  return seen;
});
probe("same with var", () => {
  const seen = [];
  for (var i = 0; i < 3; i++) { seen.push(i); if (i === 0) i = 1; }
  return seen;
});

console.log("");
console.log("[3] 회차 안에서 바꾼 값이 그 회차의 클로저에 남는다");
probe("let: change i after pushing the fn", () => {
  const fns = [];
  for (let i = 0; i < 3; i++) { fns.push(() => i); i += 10; }
  return fns.map((f) => f());
});
probe("how many passes did it make", () => {
  let count = 0;
  for (let i = 0; i < 3; i++) { count++; i += 10; }
  return count;
});

console.log("");
console.log("[4] 그 일을 하는 것은 let 이 아니라 for 헤더의 let 이다");
probe("for (let i;;) header", () => { const f = []; for (let i = 0; i < 3; i++) f.push(() => i); return f.map((g) => g()); });
probe("while + let declared outside", () => { const f = []; let i = 0; while (i < 3) { f.push(() => i); i++; } return f.map((g) => g()); });
probe("do..while + let outside", () => { const f = []; let i = 0; do { f.push(() => i); i++; } while (i < 3); return f.map((g) => g()); });
probe("for (;;) with let outside header", () => { const f = []; let i; for (i = 0; i < 3; i++) f.push(() => i); return f.map((g) => g()); });
probe("for..of with let", () => { const f = []; for (let x of [0, 1, 2]) f.push(() => x); return f.map((g) => g()); });
probe("for..in with let", () => { const f = []; for (let k in { a: 0, b: 1 }) f.push(() => k); return f.map((g) => g()); });
probe("forEach callback param", () => { const f = []; [0, 1, 2].forEach((x) => f.push(() => x)); return f.map((g) => g()); });

console.log("");
console.log("[5] 헤더의 이름과 몸통의 같은 이름은 다른 칸이다");
probe("body shadows the header name", () => {
  const f = [];
  for (let i = 0; i < 3; i++) { let i = "body"; f.push(() => i); }
  return f.map((g) => g());
});
probe("and the loop still counts", () => { let n = 0; for (let i = 0; i < 3; i++) { let i = "body"; n++; } return n; });
```

- 다섯 묶음의 출력을 각각 적으면?
- ★★★ `[1]` 과 `[2]` 가 **서로 반대되는 것처럼 보인다** — 어떻게 둘 다 참인가?
- ★★★ `[3]` 에서 루프가 **몇 번** 도는가? 그 회차의 함수가 보는 값은?
- ★★ `[4]` 의 일곱 줄을 **두 무리로 갈라라.** 무엇이 갈림의 기준인가?
- ★★ 「`let` 을 쓰면 루프 클로저가 고쳐진다」를 이 출력으로 **반박하면**?
- ★ `[5]` 에서 몸통이 헤더의 이름을 가려도 루프가 그대로 도는 이유는?

### 4. 만든 뒤에 바꾸면 (예측) ★★

```js
// js06b-06d-variable-not-value.js
// 클로저가 붙드는 것은 값의 사본이 아니라 그 변수 자체다.
function probe(label, run) {
  let r;
  try { r = JSON.stringify(run()); }
  catch (e) { r = e.constructor.name + ": " + e.message; }
  console.log("  " + label.padEnd(38) + " -> " + r);
}

console.log("[1] 만든 뒤에 바꿔도 따라온다 -- 값이었다면 안 따라온다");
probe("changed after the fn was made", () => {
  let v = "before";
  const read = () => v;
  const first = read();
  v = "after";
  return [first, read()];
});
probe("the fn was even called in between", () => {
  let v = 0;
  const read = () => v;
  const seen = [read()];
  v = 1; seen.push(read());
  v = 2; seen.push(read());
  return seen;
});

console.log("");
console.log("[2] 두 함수가 한 변수를 나눠 쓴다 -- 하나로 쓰면 다른 하나가 본다");
probe("read/write pair", () => {
  function make() { let n = 0; return { read: () => n, write: (v) => { n = v; } }; }
  const a = make();
  const out = [a.read()];
  a.write(42);
  out.push(a.read());
  return out;
});
probe("two calls to make() do not share", () => {
  function make() { let n = 0; return { read: () => n, write: (v) => { n = v; } }; }
  const a = make(), b = make();
  a.write(42);
  return [a.read(), b.read()];
});

console.log("");
console.log("[3] 그 변수는 함수가 끝난 뒤에도 산다");
probe("counter survives the call that made it", () => {
  function makeCounter() { let n = 0; return () => ++n; }
  const tick = makeCounter();
  return [tick(), tick(), tick()];
});
probe("two counters are independent", () => {
  function makeCounter() { let n = 0; return () => ++n; }
  const a = makeCounter(), b = makeCounter();
  return [a(), a(), b()];
});

console.log("");
console.log("[4] 인자로 받은 것도 같은 성질이다 -- 다만 이름이 회차마다 새로 생긴다");
probe("param is a fresh name per call", () => {
  function make(x) { return { read: () => x, write: (v) => { x = v; } }; }
  const a = make(1), b = make(2);
  a.write(99);
  return [a.read(), b.read()];
});
probe("object arg: box fresh, contents shared", () => {
  const shared = { n: 0 };
  function make(o) { return () => o.n; }
  const r = make(shared);
  shared.n = 5;
  return r();
});

console.log("");
console.log("[5] 「값을 박아 두고 싶다」는 다른 도구다");
probe("copy into a new name at make time", () => {
  let v = "before";
  const snapshot = ((copy) => () => copy)(v);
  v = "after";
  return [snapshot(), v];
});
probe("bind freezes the argument", () => {
  let v = "before";
  const show = (x) => x;
  const bound = show.bind(null, v);
  v = "after";
  return [bound(), v];
});
```

- 다섯 묶음의 출력을 각각 적으면?
- ★★★ `[1]` 의 답이 `["before","before"]` 가 아닌 것이 **무엇을 배제하는가**?
- ★★ `[2]` 의 두 줄이 갈리는 이유는? 두 번째 줄이 2번 문항의 어느 줄과 같은 사실인가?
- ★★ `[4]` 의 두 줄에서 「칸」과 「내용물」이 어떻게 갈리는가?
- ★ `[5]` 의 두 도구가 공통으로 하는 일을 한 문장으로?

### 5. 밖에서 안 보이는 상태 (예측) ★★

```js
// js06b-06e-module-pattern.js
// 모듈 패턴 -- 클로저로 비공개 상태를 만드는 관용구. 무엇이 감춰지고 무엇이 안 감춰지나.
function probe(label, run) {
  let r;
  try { r = JSON.stringify(run()); }
  catch (e) { r = e.constructor.name + ": " + e.message; }
  console.log("  " + label.padEnd(38) + " -> " + r);
}

function makeAccount(start) {
  let balance = start;              // 비공개 -- 밖에서 이름으로 못 건드린다
  const history = [];
  return {
    deposit(n) { balance += n; history.push(n); return balance; },
    read() { return balance; },
    size() { return history.length; },
  };
}

console.log("[1] 밖에서는 이름이 아예 안 보인다");
const acc = makeAccount(100);
probe("acc.read()", () => acc.read());
probe("Object.keys(acc)", () => Object.keys(acc));
probe("acc.balance", () => acc.balance);
probe('"balance" in acc', () => "balance" in acc);
probe("JSON.stringify(acc)", () => JSON.stringify(acc));
probe("getOwnPropertyNames", () => Object.getOwnPropertyNames(acc));

console.log("");
console.log("[2] 인스턴스마다 자기 칸이다");
probe("two accounts do not share", () => {
  const a = makeAccount(0), b = makeAccount(0);
  a.deposit(10);
  return [a.read(), b.read()];
});
probe("methods of one account share", () => {
  const a = makeAccount(0);
  a.deposit(10); a.deposit(20);
  return [a.read(), a.size()];
});

console.log("");
console.log("[3] 한 번만 만들고 싶으면 IIFE 로 즉시 부른다 -- 같은 기계다");
const single = (function () {
  let hits = 0;
  return { hit: () => ++hits, count: () => hits };
})();
probe("IIFE module: hit twice", () => { single.hit(); single.hit(); return single.count(); });
probe("typeof the IIFE result", () => typeof single);

console.log("");
console.log("[4] 감춰지는 것은 이름이지 값이 아니다");
probe("a leaked object is still reachable", () => {
  function make() { const secret = { k: 1 }; return { peek: () => secret }; }
  const m = make();
  const got = m.peek();
  got.k = 999;
  return m.peek();
});
probe("a leaked primitive is a copy", () => {
  function make() { let n = 1; return { peek: () => n, read: () => n }; }
  const m = make();
  let got = m.peek();
  got = 999;
  return m.read();
});

console.log("");
console.log("[5] 같은 일을 하는 다른 도구 -- 클래스의 # 필드");
class Acct {
  #balance = 0;
  deposit(n) { this.#balance += n; return this.#balance; }
  read() { return this.#balance; }
}
const k = new Acct();
probe("class #field: deposit then read", () => { k.deposit(7); return k.read(); });
probe("Object.keys of the instance", () => Object.keys(k));
probe("reading #balance from outside", () => new Function("o", "return o.#balance;"));
```

- 다섯 묶음의 출력을 각각 적으면?
- ★★★ `[1]` 에서 `balance` 를 찾는 창이 **몇 개** 실패하는가? 왜 전부 실패하는가?
- ★★ `[4]` 의 두 줄이 「감춰지는 것은 무엇인가」를 어떻게 가르는가?
- ★★ `[5]` 의 마지막 줄은 클로저 쪽과 **에러의 종류가 다르다** — 무엇이 다르고 왜 그런가?
- ★ 이 패턴의 대가는 무엇인가? (재지 않고 말할 수 있는 것만)

### 6. 아무도 안 쓰는 것처럼 보이는데 (예측) ★

```js
// js06b-06f-retain.js
// 클로저는 잡은 것을 살려 둔다 -- 「잰다」가 아니라 「수거됐나 아직 살아 있나」만 본다.
// ★ 이 블록만 --expose-gc 로 던진다. GC 시점은 명세가 정하지 않으므로 아래는 전부 「관찰」이다.
function kept(label, build) {
  const [fn, obj] = build();
  return [label, fn, new WeakRef(obj)];
}

const rows = [
  kept("nobody reads it", () => { const big = { tag: "big" }; return [() => "small", big]; }),
  kept("the returned fn reads it", () => { const big = { tag: "big" }; return [() => big.tag, big]; }),
  kept("only a sibling fn reads it", () => {
    const big = { tag: "big" };
    const sibling = () => big.tag;       // 만들기만 하고 돌려주지는 않는다
    return [() => "small", big];
  }),
  kept("copy out the one field it needs", () => {
    const big = { tag: "big" };
    const tag = big.tag;                 // 큰 것 대신 조각 하나만 들고 나간다
    return [() => tag, big];
  }),
];

setTimeout(() => {
  globalThis.gc();
  globalThis.gc();
  console.log("  " + "what the returned closure does".padEnd(32) + "the captured object is");
  console.log("  " + "-".repeat(32) + "-".repeat(22));
  for (const [label, fn, ref] of rows) {
    console.log("  " + label.padEnd(32) + (ref.deref() === undefined ? "collected" : "still alive").padEnd(14) +
                "fn() = " + JSON.stringify(fn()));
  }
  console.log("");
  console.log("[함수가 끝났는데 그 지역 변수를 아직 읽을 수 있다 -- 그것이 「잡고 있다」의 뜻이다]");
  function makeReader() { const rows2 = Array.from({ length: 1000 }, (_, i) => i); return () => rows2.length; }
  const r = makeReader();
  console.log("  makeReader() returned long ago, r() = " + r());
  console.log("  ten readers made the same way, sum = " +
    Array.from({ length: 10 }, () => makeReader()).reduce((s, f) => s + f(), 0));
}, 10);
```

- 네 줄의 `collected` / `still alive` 를 각각 적으면?
- ★★★ **첫 줄이 `collected` 여야 하는 이유**는? 전부 `still alive` 였다면 이 표는 무엇을 말하는가?
- ★★★ **셋째 줄**이 이 주제의 교재다 — 무엇이 무엇을 살려 두는가?
- ★★ 이 표의 어느 칸이 **명세 보장**이고 어느 칸이 **V8 의 사정**인가?
- ★ 아래 두 줄은 GC 없이도 성립한다 — 그 두 줄이 말하는 것은?

### 7. 「나중에 읽어서」가 왜 부족한가 (왜) ★★★

- ★★★ 이 설명이 **설명하지 못하는 것**은 무엇인가?
- ★★★ 「칸이 셋이었다면 어땠을까」로 되물으면 무엇이 드러나는가?
- ★★ 「값」과 「개수」 중 **원인**은 어느 쪽인가? 나머지 하나는 무엇인가?
- ★★ JS 에서 그 개수를 **어떻게** 세는가? 파이썬·Go 와 도구가 왜 다른가?
- ★ 이 주제가 05번에서 **정확히 무엇을 이어받았는가**? 한 문장으로.

### 8. 같은 결함, 세 언어의 세 가지 답 (경계) ★★★

- ★★★ 파이썬([`22번`](../../../python/syntax/22-closures-and-late-binding/2-summary.md))·Go([`13번`](../../../go/syntax/13-closures-variable-capture-and-loop-variable-change/2-summary.md))·JS 는 **같은 결함**을 각각 어떻게 다뤘는가?
- ★★★ 셋이 「서로 다른 상자 개수」를 세는 **도구가 각각 무엇**인가? 왜 다른가?
- ★★ 세 답 중 **옛 코드의 의미를 바꾼 것**은 어느 것인가? 안 바꾼 것은?
- ★★ JS 가 `var` 의 의미를 안 고치고 `let` 을 새로 만든 대가는 무엇인가?
- ★ 파이썬의 「고침 세 가지」 중 JS 에 그대로 있는 것은?

### 9. 보장인가 구현인가 관찰인가 (연결) ★★★ 이 갈래의 축

- ★★★ 이 주제에서 **명세 보장** 칸에 들어가는 것 다섯을 대면?
- ★★★ 「**형제 클로저가 읽으면 같이 산다**」는 어느 칸인가? 왜 그 칸인가?
- ★★ 예외의 **종류**와 **문구**는 같은 칸인가?
- ★★ 「두 판에서 한 글자도 같았다」는 어느 칸의 근거가 되는가? 어느 칸은 못 되는가?
- ★ 이 주제에서 **부적용인 창**은 무엇이고, 그 사실 자체가 무엇을 말하는가?

### 10. 경계 — 어디까지가 이 주제인가 (연결) ★★

- **블록 스코프** · **TDZ** · **`this`** · **`WeakRef`** · **`#` 필드** 는 각각 어느 주제가 정본인가?
- ★★★ 07번이 이 주제에서 **무엇을 뒤집는가**? 한 문장으로.
- ★★ 08번이 이 주제에서 **무엇을 이어받는가**?
- ★ 파이썬에는 블록 스코프가 없다 — 그쪽 갈래와 어떻게 갈리는가?
- ★ 이 주제가 **끝까지 책임지는 것** 세 가지를 대면?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
