# js/syntax/51 — 명시적 자원 관리 `using`: 「이 런타임에서 도나 · 무엇을 어떤 순서로 치우나 · 치우다 던지면 무엇이 남나」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v18.19.1 · v20.19.6 · Google Chrome 151(헤드리스 — 하네스는 2-summary 머리말) · tsc 7.0.2 · x86-64 Linux.
>
> ★★★ **이 주제의 본체는 지원 판별 격자다** — 판 셋 × 기능 일곱. **1번 문항이 이 주제의 중심이고, 3번 · 4번이 그다음이다.**
>
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① ★★★ **어느 런타임에 무엇이 있나 · 선언이 어디에 설 수 있나**
> ② ★★★ **해제는 언제 · 어떤 순서로 불리나**(동기 · 비동기)
> ③ ★★ **해제가 던지면 무엇이 남나 · 문법이 없는 판에서는 어떻게 하나.**
>
> **선행** — [32](../32-error-handling-and-error/2-summary.md) · [20](../20-generators/2-summary.md) · [40](../40-async-iteration-and-for-await/2-summary.md) · [47](../47-weakref-and-finalizationregistry/2-summary.md).

## 이 파일을 푸는 법

- ★★ **예측형 문항(1 · 2 · 3 · 4 · 6 · 8)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **1번은 칸마다 yes / no 만** 먼저 적어도 된다 — 그리고 `#` 두 줄에 무엇이 찍힐지 따로 적어라.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이 줄은 명세가 정한 것인가, 엔진 · 호스트 · 도구가 정한 것인가**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 판 × 기능 격자 (예측) ★★★ 이 주제의 축

```js
// js48b-51a-support.js
// Is each piece of explicit resource management here? One line per feature: label, a tab, then yes or no.
// Syntax is asked through new Function (a function body) and an async function inside it,
// so a missing piece does not stop the script. The last two lines describe Symbol.dispose itself.
const has = (label, test) => {
  let r;
  try { r = test() ? "yes" : "no"; } catch (e) { r = "no"; }
  console.log(label + "\t" + r);
};
const syntax = (src) => () => (new Function(src), true);
has("using declaration in a block", syntax("{ using x = null; }"));
has("await using in an async function", syntax("return async () => { await using x = null; };"));
has("Symbol.dispose", () => typeof Symbol.dispose === "symbol");
has("Symbol.asyncDispose", () => typeof Symbol.asyncDispose === "symbol");
has("DisposableStack", () => typeof DisposableStack === "function");
has("AsyncDisposableStack", () => typeof AsyncDisposableStack === "function");
has("SuppressedError", () => typeof SuppressedError === "function");
console.log("# String(Symbol.dispose)\t" + String(Symbol.dispose));
console.log("# Symbol.keyFor(Symbol.dispose)\t" + String(Symbol.keyFor(Symbol.dispose)));
```

```sh
# js48b-51a-support.sh
#!/usr/bin/env bash
# The support table (js48b-51a-support.js) on node18, node20 and Chrome 151, side by side.
# Each probe line is "label<TAB>value"; a line with another number of fields stops the script.
# Rows starting with "#" are descriptions, not counted as cells.
set -u -o pipefail
cd "$(dirname "$0")" || exit 1
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
a="$("$N18" js48b-51a-support.js)" || exit 1
b="$("$N20" js48b-51a-support.js)" || exit 1
c="$(./js48b-browser.sh js48b-51a-support.js)" || exit 1
printf '%-36s %-22s %-22s %s\n' "" "node18" "node20" "Chrome 151"
yes=0; cells=0
while IFS= read -r i; do
  la="$(printf '%s\n' "$a" | sed -n "${i}p")"; lb="$(printf '%s\n' "$b" | sed -n "${i}p")"; lc="$(printf '%s\n' "$c" | sed -n "${i}p")"
  for l in "$la" "$lb" "$lc"; do
    [ "$(printf '%s' "$l" | awk -F'\t' '{print NF}')" = 2 ] || { echo "bad line: $l"; exit 2; }
  done
  label="${la%%$'\t'*}"
  va="${la#*$'\t'}"; vb="${lb#*$'\t'}"; vc="${lc#*$'\t'}"
  printf '%-36s %-22s %-22s %s\n' "$label" "$va" "$vb" "$vc"
  case $label in "#"*) continue ;; esac
  for v in "$va" "$vb" "$vc"; do cells=$((cells + 1)); [ "$v" = yes ] && yes=$((yes + 1)); done
done < <(seq "$(printf '%s\n' "$a" | wc -l)")
echo ""
echo "supported cells: $yes / $cells"
```

- ★★★ 21칸 각각은 yes 인가 no 인가? 마지막 줄의 `N / 21` 은?
- ★★ `#` 로 시작하는 두 줄은 판마다 무엇을 찍나?

### 2. 선언을 둘 자리 (예측) ★★

```js
// js48b-51b-positions.js
// Where may a using declaration stand? Each source text is parsed in one of two goals:
//   "function body" -- new Function(text)      "script top level" -- indirect eval (0, eval)(text)
// and the line prints "parsed" or the SyntaxError message.
const R = { [Symbol.dispose]() {} };
globalThis.R51 = R;
const tries = [
  ["function body", "{ using x = R51; }"],
  ["function body", "using x = R51;"],
  ["script top level", "using x = R51;"],
  ["script top level", "{ using x = R51; }"],
  ["function body", "for (using x of [R51]) {}"],
  ["function body", "for (using x = R51; false; ) {}"],
  ["function body", "for (using x in { a: 1 }) {}"],
  ["function body", "switch (1) { case 1: using x = R51; }"],
  ["function body", "switch (1) { case 1: { using x = R51; } }"],
  ["function body", "using x;"],
  ["function body", "using { a } = R51;"],
  ["function body", "using x = R51, y = R51;"],
  ["function body", "let using = 1; return using;"],
  ["function body", "return async () => { await using x = R51; };"],
  ["function body", "await using x = R51;"],
];
for (const [goal, text] of tries) {
  let r;
  try {
    if (goal === "function body") new Function(text); else (0, eval)(text);
    r = "parsed";
  } catch (e) { r = e.constructor.name + " 「" + e.message + "」"; }
  console.log("  " + goal.padEnd(18) + text.padEnd(46) + r);
}
```

- ★★ Chrome 151 에서 `parsed` 가 되는 줄은 어느 것이고, 나머지 줄의 문구는?
- ★ node 20 에서는 어느 줄이 `parsed` 인가?

### 3. 갈래마다의 로그 (예측) ★★★

```js
// js48b-51c-order.js
// In what order do resources get disposed, and when? res(name) logs when it is made and when it is disposed.
// Each numbered part runs one block and prints the log it left.
let log = [];
const res = (name) => { log.push("make " + name); return { [Symbol.dispose]() { log.push("dispose " + name); } }; };
const part = (title, f) => {
  log = [];
  let end;
  try { end = "returned " + String(f()); } catch (e) { end = "threw " + e.constructor.name + " 「" + e.message + "」"; }
  console.log(title);
  console.log("    " + log.join(" · ") + "  ->  " + end);
};
part("[1] one declaration, three bindings", () => {
  using a = res("a"), b = res("b"), c = res("c");
  log.push("body");
});
part("[2] three declarations, the middle one in an inner block", () => {
  using a = res("a");
  {
    using b = res("b");
    log.push("inner body");
  }
  using c = res("c");
  log.push("outer body");
});
part("[3] leaving by return", () => {
  using a = res("a");
  log.push("before return");
  return "r";
});
part("[4] leaving by throw", () => {
  using a = res("a");
  throw new Error("from the body");
});
part("[5] inside try, with a finally", () => {
  try {
    using a = res("a");
    log.push("try body");
  } finally {
    log.push("finally");
  }
});
part("[6] loop: for (using x of ...)", () => {
  for (using x of [res("p"), res("q")]) log.push("loop body");
});
part("[7] null and undefined as the value", () => {
  using a = null, b = undefined, c = res("c");
  log.push("body");
});
part("[8] a value without Symbol.dispose", () => {
  using a = res("a");
  log.push("before the second declaration");
  using b = {};
  log.push("after the second declaration");
});
part("[9] replacing the method after the declaration", () => {
  const r = { [Symbol.dispose]() { log.push("the method present at the declaration"); } };
  using a = r;
  r[Symbol.dispose] = () => log.push("the method put there afterwards");
  log.push("body");
});
part("[10] assigning to the binding", () => {
  using a = res("a");
  a = res("other");
});
```

- ★★★ Chrome 151 에서 `[1]`\~`[10]` 각각의 로그 줄과 `->` 뒤는?

### 4. 치우다 던질 때 (예측) ★★★

```js
// js48b-51d-errors.js
// What reaches the caller when disposal throws? show() walks .error / .suppressed and prints the shape.
const bad = (name) => ({ [Symbol.dispose]() { throw new Error("dispose " + name); } });
const good = (name, log) => ({ [Symbol.dispose]() { log.push("dispose " + name); } });
const show = (e, pad) => {
  if (e instanceof SuppressedError) {
    console.log(pad + "SuppressedError 「" + e.message + "」");
    console.log(pad + "  .error:"); show(e.error, pad + "    ");
    console.log(pad + "  .suppressed:"); show(e.suppressed, pad + "    ");
  } else console.log(pad + e.constructor.name + " 「" + e.message + "」");
};
const part = (title, f) => {
  console.log(title);
  try { f(); console.log("    no exception"); } catch (e) { show(e, "    "); }
};
part("[1] the body throws, the one resource throws while disposing", () => {
  using a = bad("a");
  throw new Error("body");
});
part("[2] the body finishes, the one resource throws while disposing", () => {
  using a = bad("a");
});
part("[3] the body throws, two resources throw while disposing", () => {
  using a = bad("a"), b = bad("b");
  throw new Error("body");
});
part("[4] the body finishes, b throws while disposing, a does not", () => {
  const log = [];
  try {
    using a = good("a", log), b = bad("b");
  } finally { console.log("    log: " + log.join(" · ")); }
});
console.log("[5] new SuppressedError(x, y, 'm')");
const s = new SuppressedError("x", "y", "m");
console.log("    .error " + s.error + " · .suppressed " + s.suppressed + " · .message " + s.message +
  " · own keys " + Object.getOwnPropertyNames(s).filter((k) => k !== "stack").join(" ") +
  " · instanceof Error " + (s instanceof Error));
console.log("[6] own keys of the error that [1] threw");
try { using a = bad("a"); throw new Error("body"); } catch (e) {
  console.log("    " + Object.getOwnPropertyNames(e).filter((k) => k !== "stack").join(" ") +
    " · Object.hasOwn(e, 'message') " + Object.hasOwn(e, "message"));
}
```

- ★★★ `[1]`\~`[4]` 에서 호출자가 받는 것의 모양(겹쳤다면 어느 쪽이 `.error`, 어느 쪽이 `.suppressed` 인가)은?
- ★ `[5]` 와 `[6]` 은?

### 5. `DisposableStack` 의 네 메서드 (경계) ★★

- ★★ `use` · `adopt` · `defer` 는 각각 무엇을 받고 무엇을 장부에 적나? 세 개를 차례로 넣고 `dispose()` 하면 어떤 순서로 불리나?
- ★★ `dispose()` 를 두 번 부르면? 닫힌 스택에 `use` 하면? `move()` 뒤 원래 스택을 `dispose()` 하면?

### 6. `await using` 과 마이크로태스크 틱 (예측) ★★

```js
// js48b-51f-await-using.js
// await using: when does each asynchronous disposal finish, compared with other queued work?
// A microtask "tick N" is queued before each block ends, so the log shows how many turns the exit took.
const log = [];
const ares = (name) => ({
  async [Symbol.asyncDispose]() { log.push("start async dispose " + name); await null; log.push("end async dispose " + name); },
});
const sres = (name) => ({ [Symbol.dispose]() { log.push("sync dispose " + name); } });
const ticks = (n) => { let p = Promise.resolve(); for (let i = 1; i <= n; i++) p = p.then(() => log.push("tick " + i)); };
const part = async (title, f) => {
  log.length = 0;
  await f();
  log.push("after the block");
  await new Promise((r) => setTimeout(r, 0));
  console.log(title);
  console.log("    " + log.join(" · "));
};
(async () => {
  await part("[1] two async resources", async () => {
    await using a = ares("a"), b = ares("b");
    ticks(4);
    log.push("body");
  });
  await part("[2] a value with only Symbol.dispose", async () => {
    await using a = sres("a");
    ticks(3);
    log.push("body");
  });
  await part("[3] null as the value", async () => {
    await using a = null;
    ticks(3);
    log.push("body");
  });
  await part("[4] no await using at all", async () => {
    ticks(3);
    log.push("body");
  });
  await part("[5] plain using holding an object that has only Symbol.asyncDispose", async () => {
    try { using a = ares("a"); log.push("body"); } catch (e) { log.push(e.constructor.name + " 「" + e.message + "」"); }
  });
})();
```

- ★★ `[1]`\~`[5]` 각각의 로그 줄은? 특히 `[3]` 과 `[4]` 에서 `after the block` 은 몇 번째 `tick` 뒤에 오나?

### 7. 손으로 쓴 `try`/`finally` (왜) ★★

```js
// js48b-51g-by-hand.js
// The same two questions without using: nested try/finally, written by hand.
// Plain statements only, so every runtime of this batch can run it.
const log = [];
const res = (name, throws) => ({
  [Symbol.dispose]() { log.push("dispose " + name); if (throws) throw new Error("dispose " + name); },
});
const shape = (e) => e.constructor.name + " 「" + e.message + "」" +
  ("suppressed" in e ? " · .error " + e.error.message + " · .suppressed " + e.suppressed.message : "");
console.log("[1] three resources, one try/finally each");
const a = res("a");
try {
  const b = res("b");
  try {
    const c = res("c");
    try { log.push("body"); } finally { c[Symbol.dispose](); }
  } finally { b[Symbol.dispose](); }
} finally { a[Symbol.dispose](); }
console.log("    " + log.join(" · "));
console.log("[2] the body throws, the resource throws while disposing -- plain try/finally");
try {
  const r = res("r", true);
  try { throw new Error("body"); } finally { r[Symbol.dispose](); }
} catch (e) { console.log("    caught " + shape(e)); }
console.log("[3] the same, keeping both errors by hand");
const Suppressed = typeof SuppressedError === "function" ? SuppressedError
  : class SuppressedByHand extends Error { constructor(error, suppressed, m) { super(m); this.error = error; this.suppressed = suppressed; } };
try {
  const r = res("r", true);
  let bodyError, failed = false;
  try { throw new Error("body"); } catch (e) { bodyError = e; failed = true; }
  try { r[Symbol.dispose](); } catch (e) { if (failed) throw new Suppressed(e, bodyError, "kept both"); throw e; }
  if (failed) throw bodyError;
} catch (e) { console.log("    caught " + shape(e)); }
```

- ★★ `[2]` 의 호출자는 왜 `body` 를 못 보나? 32번의 어느 결과와 같은 칸인가?
- ★ `[3]` 은 node 20 과 Chrome 151 에서 어느 글자가 다르고, 왜 다른가?

### 8. tsc 가 낮춘 코드 (예측) ★★

```ts
// in51h.ts
// The order and error questions of this topic, written with using, for tsc to compile.
declare const console: { log(s: string): void };
const log: string[] = [];
const res = (name: string, throws = false) => ({
  [Symbol.dispose]() { log.push("dispose " + name); if (throws) throw new Error("dispose " + name); },
});
function order() {
  using a = res("a"), b = res("b"), c = res("c");
  log.push("body");
}
order();
console.log("[1] " + log.join(" · "));
try {
  using r = res("r", true);
  throw new Error("body");
} catch (e: any) {
  console.log("[2] caught constructor " + e.constructor.name + " · name " + e.name + " · 「" + e.message + "」" +
    " · .error " + e.error?.message + " · .suppressed " + e.suppressed?.message);
}
console.log("[3] typeof SuppressedError " + typeof SuppressedError + " · String(Symbol.dispose) " + String(Symbol.dispose));
```

```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "es2022",
    "module": "commonjs",
    "lib": ["es2022", "esnext.disposable"],
    "types": [],
    "outDir": "out",
    "strict": true
  },
  "files": ["in51h.ts"]
}
```

```sh
# js48b-51h-tsc.sh
#!/usr/bin/env bash
# Does tsc lower using? Compile js48b-51h/in51h.ts with js48b-51h/tsconfig.json (target es2022),
# then the same project with --target esnext, and run what comes out on node18, node20 and Chrome 151.
set -u -o pipefail
cd "$(dirname "$0")/js48b-51h" || exit 1
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
rm -rf out out-esnext
echo "tsc $(tsc --version)"
tsc -p .; echo "tsc -p .   (target es2022) exit=$?"
echo "  lines of out/in51h.js that contain 'using ': $(grep -c 'using ' out/in51h.js)"
echo "  helpers defined: $(grep -o '^var __[A-Za-z]*' out/in51h.js | sed 's/^var //' | tr '\n' ' ')"
echo "  TypeError messages in the helpers: $(grep -o 'throw new TypeError("[^"]*")' out/in51h.js | sed 's/throw new TypeError(//; s/)$//' | tr '\n' ' ')"
echo "--- out/in51h.js after the two helpers"
sed -n '/^const log/,$p' out/in51h.js
echo "--- node18 out/in51h.js"; "$N18" out/in51h.js || exit 1
echo "--- node20 out/in51h.js"; "$N20" out/in51h.js || exit 1
echo "--- Chrome 151 out/in51h.js"; ../js48b-browser.sh js48b-51h/out/in51h.js || exit 1
echo ""
tsc -p . --target esnext --outDir out-esnext; echo "tsc -p . --target esnext --outDir out-esnext   exit=$?"
echo "  lines of out-esnext/in51h.js that contain 'using ': $(grep -c 'using ' out-esnext/in51h.js)"
for n in node18:"$N18" node20:"$N20"; do
  printf '  %s parses out-esnext/in51h.js: ' "${n%%:*}"
  "${n#*:}" -e 'try { new Function(require("fs").readFileSync(process.argv[1], "utf8")); console.log("yes"); }
    catch (e) { console.log(e.constructor.name + " 「" + e.message + "」"); }' out-esnext/in51h.js
done
```

- ★★ `target es2022` 의 방출물에 `using ` 이 들어간 줄은 몇 줄인가? 헬퍼는 무엇인가?
- ★★ 그 방출물을 node 18 · node 20 · Chrome 151 에서 돌리면 `[2]` 의 `constructor` 와 `name` 은 각각? `[3]` 은?
- ★ `target esnext` 의 방출물을 node 18 · 20 이 파싱하면?

### 9. node 의 `Symbol.dispose` (왜) ★★★

- ★★★ node 18·20 은 `Symbol.dispose` 가 `symbol` 인데 왜 `using` 을 못 쓰나? 그 심볼은 명세의 `Symbol.dispose` 와 같은 것인가 — 무엇으로 확인하나? 기능 검사를 어떻게 써야 하나?

### 10. 이터레이터의 `return()` 과 견주면 (연결) ★★

- ★★ 20·40번의 `return()` 도 「루프를 떠나는 모든 길에서 불린다」. `for (using x of it)` 에서 **값의 해제**와 **이터레이터의 닫기**는 각각 누구의 규칙인가? 47번의 `FinalizationRegistry` 와는 무엇이 정반대인가?

### 11. 세 갈래의 해제 오류 (연결) ★★

- ★★ Python `with` · Java `try`-with-resources · JS `using` 은 해제 중 오류를 각각 어떤 모양으로 남기나? 「주인공」 이 되는 것은 어느 오류인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
