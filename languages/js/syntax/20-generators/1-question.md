# js/syntax/20 — 제너레이터: 「`next(값)` 은 대답을 넣고 다음 질문을 받는 무전이다 — 첫 무전은 아무도 안 듣는다」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v18.19.1(기본 PATH) · v20.19.6(nvm) · x86-64 Linux. 브라우저는 판별 블록 말고는 **안 돌렸다.**
> 배너의 `node20` 은 v20.19.6, `node18` 은 v18.19.1 이다.
>
> ★★★ **이 주제의 본체는 ① 추상 연산에 로그 심기 — 양방향 흐름의 로그다.**
> `next(값)` 으로 들여보낸 값이 **어느 `yield` 에 닿았나**는 결과 객체에 흔적이 없다.
> 그래서 본문 안에 「`yield` 식이 무엇으로 평가됐나」를 찍고 바깥의 호출과 한 줄에 나란히 찍었다. **1번 문항이 이 주제의 중심이다.**
>
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① ★★★ **`next(값)` 의 값이 어디에 닿나**(첫 값 포함)
> ② **`return()`·`throw()` 가 상태마다 무엇을 일으키나**(`finally` 가 도나)
> ③ **`yield*` 가 무엇을 넘기고 무엇을 받아 오나.**
>
> ★★★ **답을 적을 때 결과 객체만 적으면 절반도 못 맞힌 것이다.** 1\~5번은 줄마다 **본문 로그**를 같이 적어야 답이다.
> ★★ **예외는 타입과 메시지로만 답한다.** ★ **메시지는 판마다 다를 수 있다** — 6번에 그런 줄이 하나 있다.
>
> **선행** — [19 — 이터러블 프로토콜과 `for...of`](../19-iterable-protocol-and-for-of/2-summary.md)(★★★ 직접 선행) ·
> [08 — 함수 정의 형태와 매개변수](../08-function-forms-and-parameters/2-summary.md).
> ★★★ **19번의 호출표를 먼저 떠올려라** — 소비자가 `return()` 을 부르는 자리가 몇 곳이었나, `done: true` 의 값을 누가 읽었나.

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1\~6)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **1번은 「무엇이 나오나」보다 「본문이 무엇을 받았나」를 묻는다.** 호출마다 본문 로그를 먼저 적어라.
- ★★ **2·3번은 결과 객체가 같은 줄끼리 본문 로그로 갈라라.**
- ★ 각 문항 끝에서 스스로 물어라 — 「**이것은 명세인가, 이 엔진(V8)의 사정인가**」.
- ★★★ **속도·메모리에 관한 답은 하나도 없다.** 「메모리를 아낀다」가 떠오르면 「**안 쟀다**」라고 적어라.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 네 번의 `next(값)` — 바깥이 받는 것과 본문이 받는 것 (예측) ★★★ 이 주제의 축

```js
// js20b-20b-two-way.js
// next(값) 의 값은 어디로 가나 -- 본문이 받은 값과 바깥이 받은 값을 한 줄씩 찍는다.
const L = [];
const J = (v) => JSON.stringify(v, (k, x) => (x === undefined ? "<undefined>" : x));
function* echo() {
  L.push("body starts (arguments.length " + arguments.length + ")");
  const a = yield "out-1";
  L.push("yield#1 evaluated to " + J(a));
  const b = yield "out-2";
  L.push("yield#2 evaluated to " + J(b));
  return "done with " + J([a, b]);
}

console.log("[1] next('A'), next('B'), next('C'), next('D')");
const g = echo();
for (const arg of ["A", "B", "C", "D"]) {
  const r = g.next(arg);
  console.log("  next(" + J(arg) + ")  ->  " + J(r).padEnd(40) + " body: " + (L.length ? L.join(" / ") : "(no log)"));
  L.length = 0;
}

console.log("");
console.log("[2] a running total -- priming next() first, then values");
function* total() {
  let sum = 0;
  while (true) {
    const x = yield sum;
    sum += x;
  }
}
const t = total();
const steps = [["next()", () => t.next()], ["next(10)", () => t.next(10)], ["next(5)", () => t.next(5)], ["next(1)", () => t.next(1)]];
for (const [label, run] of steps) console.log("  " + label.padEnd(10) + J(run()));

console.log("");
console.log("[3] the same, without priming -- next(10) first");
const t2 = total();
for (const x of [10, 5, 1]) console.log("  " + ("next(" + x + ")").padEnd(10) + J(t2.next(x)));
```

- `[1]` 네 줄에서 **결과 객체**와 **본문 로그**를 각각 적어라. `"A"` 는 어느 줄의 로그에 나오나?
- `[2]` 와 `[3]` 의 누산 결과를 적어라. 두 목록이 같은가?

### 2. `return('R')` 을 부르는 네 가지 상황 (예측) ★★★

```js
// js20b-20c-return-finally.js
// gen.return(v) -- 어느 상태에서 부르느냐에 따라 finally 가 도나, 무엇을 돌려받나.
const L = [];
const J = (v) => JSON.stringify(v, (k, x) => (x === undefined ? "<undefined>" : x));
const log = (label, r) => { console.log("  " + label.padEnd(36) + J(r).padEnd(34) + " body: " + (L.length ? L.join(" / ") : "(no log)")); L.length = 0; };

function* withFinally() {
  try {
    L.push("try");
    yield 1;
    yield 2;
  } finally {
    L.push("finally");
  }
}

console.log("[1] return('R') in three states");
let g = withFinally();
log("before the first next: return('R')", g.return("R"));
log("  then next()", g.next());
g = withFinally(); g.next(); L.length = 0;
log("paused at yield 1: return('R')", g.return("R"));
log("  then next()", g.next());
g = withFinally(); [...g]; L.length = 0;
log("after completion: return('R')", g.return("R"));

console.log("");
console.log("[2] a finally block that itself yields");
function* yieldsInFinally() {
  try {
    yield 1;
  } finally {
    L.push("finally starts");
    yield "from finally";
    L.push("finally ends");
  }
}
g = yieldsInFinally(); g.next(); L.length = 0;
log("return('R')", g.return("R"));
log("next()", g.next());
log("next()", g.next());

console.log("");
console.log("[3] a finally block with its own return");
function* returnsInFinally() {
  try { yield 1; } finally { L.push("finally returns 'F'"); return "F"; }
}
g = returnsInFinally(); g.next(); L.length = 0;
log("return('R')", g.return("R"));

console.log("");
console.log("[4] break in for-of over withFinally()");
for (const x of withFinally()) { L.push("loop got " + x); break; }
log("after the loop", "-");
```

- `[1]` 세 상태에서 **돌려받는 것**과 **본문 로그**를 적어라. 셋 중 무엇이 같고 무엇이 다른가?
- `[2]` 의 세 호출이 돌려받는 것의 `done` 을 차례로 적어라.
- `[3]` 은 `R` 과 `F` 중 무엇을 돌려받나?

### 3. `throw()` — 감싼 본문 · 안 감싼 본문 · 시작 전 (예측) ★★

```js
// js20b-20d-throw.js
// gen.throw(e) -- 예외가 어디서 생기나, 본문이 잡으면 무엇을 돌려받나.
const L = [];
const J = (v) => JSON.stringify(v, (k, x) => (x === undefined ? "<undefined>" : x));
const E = (e) => e.constructor.name + " 「" + e.message + "」";
const attempt = (label, run) => {
  let r;
  try { r = J(run()); } catch (e) { r = "caught outside: " + E(e); }
  console.log("  " + label.padEnd(30) + r.padEnd(44) + " body: " + (L.length ? L.join(" / ") : "(no log)"));
  L.length = 0;
};

function* catchesAround() {
  let n = 0;
  while (true) {
    try {
      L.push("yield " + n);
      yield n++;
    } catch (e) {
      L.push("caught inside: " + E(e));
    }
  }
}
console.log("[1] a body that catches around its yield");
let g = catchesAround();
attempt("next()", () => g.next());
attempt("throw(new Error('X'))", () => g.throw(new Error("X")));
attempt("next()", () => g.next());

console.log("");
console.log("[2] a body with no catch");
function* noCatch() {
  try { yield 1; yield 2; } finally { L.push("finally"); }
}
g = noCatch();
attempt("next()", () => g.next());
attempt("throw(new Error('X'))", () => g.throw(new Error("X")));
attempt("next()", () => g.next());

console.log("");
console.log("[3] throw() before the first next()");
g = catchesAround();
attempt("throw(new Error('early'))", () => g.throw(new Error("early")));
attempt("next()", () => g.next());
```

- 여덟 줄마다 **호출이 던지나 값을 돌려주나**, 돌려준다면 무엇을, 그리고 본문 로그를 적어라.

### 4. `yield*` 를 지나는 `next`·`throw`·`return` (예측) ★★★

```js
// js20b-20e-delegate.js
// yield* -- 식의 값은 무엇인가, next(값) · throw · return 이 안쪽까지 가나.
const L = [];
const J = (v) => JSON.stringify(v, (k, x) => (x === undefined ? "<undefined>" : x));
const E = (e) => e.constructor.name + " 「" + e.message + "」";
const step = (label, run) => {
  let r;
  try { r = J(run()); } catch (e) { r = "caught outside: " + E(e); }
  console.log("  " + label.padEnd(24) + r.padEnd(36) + " log: " + (L.length ? L.join(" / ") : "(none)"));
  L.length = 0;
};

function* inner() {
  try {
    const a = yield "i1";
    L.push("inner got " + J(a));
    const b = yield "i2";
    L.push("inner got " + J(b));
    return "inner-R";
  } catch (e) {
    L.push("inner caught " + E(e));
    yield "i-after-catch";
    return "inner-R2";
  } finally {
    L.push("inner finally");
  }
}
function* outer() {
  const got = yield* inner();
  L.push("outer: yield* evaluated to " + J(got));
  yield "o1";
}

console.log("[1] next(value) through yield*");
let g = outer();
step("next('ignored')", () => g.next("ignored"));
step("next('A')", () => g.next("A"));
step("next('B')", () => g.next("B"));
step("next()", () => g.next());
console.log("  [...outer()]            " + J([...outer()]));
L.length = 0;

console.log("");
console.log("[2] throw() through yield*");
g = outer();
step("next()", () => g.next());
step("throw(new Error('X'))", () => g.throw(new Error("X")));
step("next()", () => g.next());

console.log("");
console.log("[3] return() through yield*");
g = outer();
step("next()", () => g.next());
step("return('R')", () => g.return("R"));

console.log("");
console.log("[4] yield* over an array iterator -- then throw()");
function* overArray() {
  try { yield* [1, 2, 3]; } finally { L.push("overArray finally"); }
}
g = overArray();
step("next()", () => g.next());
step("throw(new Error('X'))", () => g.throw(new Error("X")));
step("next()", () => g.next());

console.log("");
console.log("[5] a hand-written iterator under yield* -- which methods are called");
const handMade = {
  [Symbol.iterator]() {
    let i = 0;
    return {
      next(v) { L.push("hand next(" + J(v) + ")"); i++; return i <= 2 ? { value: "h" + i, done: false } : { value: "hand-R", done: true }; },
      return(v) { L.push("hand return(" + J(v) + ")"); return { value: v, done: true }; },
    };
  },
};
function* overHand() { const r = yield* handMade; L.push("overHand got " + J(r)); }
g = overHand();
step("next('a')", () => g.next("a"));
step("next('b')", () => g.next("b"));
step("next('c')", () => g.next("c"));
g = overHand();
step("next()", () => g.next());
step("return('R')", () => g.return("R"));
g = overHand();
step("next()", () => g.next());
step("throw(new Error('X'))", () => g.throw(new Error("X")));
```

- `[1]` 에서 `got` 은 무엇이 되나? `[...outer()]` 의 결과에 `"inner-R"` 이 있나?
- `[2]` 의 `throw()` 는 던지나 값을 돌려주나?
- `[4]`·`[5]` 의 `throw()` 가 바깥으로 올리는 예외는 **내가 던진 `Error 「X」` 인가**? `[5]` 에서 손으로 짠 이터레이터의 어느 메서드가 불리나?
- `[5]` 의 첫 줄에서 손으로 짠 이터레이터의 `next` 는 무엇을 인자로 받나?

### 5. 세 메서드 × 세 상태 — 본문 코드가 도는 칸 (예측) ★★★

```js
// js20b-20g-grid.js
// 세 메서드 x 세 상태 -- 칸마다 결과와 본문 로그를 찍고, 본문 코드가 돈 칸을 센다.
const J = (v) => JSON.stringify(v, (k, x) => (x === undefined ? "<undefined>" : x));
const E = (e) => e.constructor.name + " 「" + e.message + "」";
let L = [];
function* subject() {
  try {
    L.push("try");
    yield "y";
    L.push("after yield");
  } catch (e) {
    L.push("catch");
  } finally {
    L.push("finally");
  }
}
const states = {
  "suspendedStart": () => subject(),
  "suspendedYield": () => { const g = subject(); g.next(); return g; },
  "completed": () => { const g = subject(); [...g]; return g; },
};
const calls = {
  "next('v')": (g) => g.next("v"),
  "return('R')": (g) => g.return("R"),
  "throw(err)": (g) => g.throw(new Error("err")),
};
let ran = 0, total = 0;
for (const [sname, make] of Object.entries(states)) {
  console.log(sname);
  for (const [cname, call] of Object.entries(calls)) {
    const g = make();
    L = [];
    let r;
    try { r = J(call(g)); } catch (e) { r = "throws " + E(e); }
    total++;
    if (L.length) ran++;
    console.log("  " + cname.padEnd(12) + r.padEnd(32) + " body log " + J(L));
  }
}
console.log("");
console.log("cells where body code ran: " + ran + " / " + total);
```

- 아홉 칸의 결과와 본문 로그를 적고, 마지막 줄의 수를 적어라.

### 6. `new` · 형태 다섯 · 재진입 · 빌린 메서드 (예측) ★★

```js
// js20b-20f-errors.js
// 제너레이터에서 막히는 자리 -- 예외의 종류와 문구.
const J = (v) => JSON.stringify(v);
const E = (e) => e.constructor.name + " 「" + e.message + "」";
const row = (label, run) => {
  let r;
  try { r = String(run()); } catch (e) { r = E(e); }
  console.log("  " + label.padEnd(52) + r);
};

console.log("[1] new on a generator function");
function* gen() { yield 1; }
row("typeof gen.prototype", () => typeof gen.prototype);
row("Object.getPrototypeOf(gen()) === gen.prototype", () => Object.getPrototypeOf(gen()) === gen.prototype);
row("new gen()", () => new gen());

console.log("");
console.log("[2] five forms passed to new Function");
const compile = (src) => () => { new Function(src); return "compiles"; };
row("const g = *() => { yield 1; };", compile("const g = *() => { yield 1; };"));
row("const g = () => { yield 1; };", compile("const g = () => { yield 1; };"));
row("function* g() { [1].forEach(x => { yield x; }); }", compile("function* g() { [1].forEach(x => { yield x; }); }"));
row("const o = { *m() { yield 1; } };", compile("const o = { *m() { yield 1; } };"));
row("class C { static *m() { yield 1; } }", compile("class C { static *m() { yield 1; } }"));

console.log("");
console.log("[3] calling next() from inside the running body");
let self;
function* reenter() { yield self.next(); }
self = reenter();
row("self.next() inside the body", () => J(self.next()));
row("then self.next()", () => J(self.next()));

console.log("");
console.log("[4] next / return borrowed onto a plain object");
const proto = Object.getPrototypeOf(gen());
const GenProto = Object.getPrototypeOf(proto);
row("GenProto.next.call({})", () => GenProto.next.call({}));
row("GenProto.return.call({})", () => GenProto.return.call({}));
```

- 줄마다 `compiles`·값·예외(`이름 「메시지」`) 중 무엇이 나오나?
- ★ `[2]` 의 둘째 줄이 막힌다면 **어느 토큰**에서 막히나? 왜 그 토큰인가?
- ★ 두 node 판에서 문구가 달라지는 줄이 하나 있다 — 어느 줄일 것 같나?

### 7. 첫 `next(값)` 의 값은 왜 어디에도 안 닿나 (왜) ★★★

명세의 어느 연산이 그 이유를 적고 있나? 파이썬은 같은 자리에서 무엇을 하나?

### 8. 제너레이터를 불렀을 뿐인데 매개변수 기본값의 부수 효과는 찍힌다 — 왜 (경계) ★★

본문과 매개변수 목록은 **각각 언제** 평가되나? 인자 검사를 본문 첫 줄에 두면 실패가 언제 나나?

### 9. 제너레이터의 `return` 값을 받는 소비자는 누구인가 (연결) ★★

19번의 소비자 넷(`for...of`·스프레드·`Array.from`·구조 분해)과 `yield*` 를 나란히 놓고 답하라.

### 10. 끝없는 `naturals()` 에 `take(map(…), 3)` 을 붙이면 넷째는 왜 안 만들어지나 (왜) ★★

닫기가 **어느 경로로** `naturals` 의 `finally` 까지 가나? 이 결과로 「메모리를 아낀다」를 말할 수 있나?

### 11. `finally` 안에 `yield` 가 있으면 `return()` 이 「닫기」가 아니게 되는 이유 (왜) ★★★

`return()` 은 정확히 무엇을 일으키는 호출인가? 19번의 `for...of` + `break` 가 이 제너레이터를 만나면 무슨 일이 날 것 같나 — 이 문서는 그 조합을 돌렸나?

### 12. 경계 — 어디까지가 이 주제인가 (연결) ★

19번 · 21번 · 40번과 이 주제는 각각 어디서 갈리나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
