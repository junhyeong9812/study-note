# js/syntax/32 — 오류 처리와 `Error`: 「`finally` 가 끝을 바꿔 쥐면 `try` 의 끝은 사라진다 · `cause` 는 손으로 잇는 사슬이다」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> ★★★ **이 주제의 본체는 ② 전수 격자다** — `try` 가 끝나는 세 방식 × `finally` 가 끝나는 세 방식 = **9칸**을 스크립트가 전부 돌리고,
> **`try` 자신의 끝(반환값·예외)이 호출자에게 닿지 못한 칸을 스크립트가 센다**(동작 (1)).
> ★★ 보조로 **④ 예외의 `constructor.name` + `message`**(언어가 고르는 생성자 · `cause` 사슬의 층마다의 이름 · 삼켜진 예외)와
> **① 추상 연산에 로그 심기**(`new Error(m, options)` 가 `options` 를 **어떤 순서로** 읽나 — 트랩을 다 심은 `Proxy`)를 쓴다.
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262 — The `try` Statement](https://tc39.es/ecma262/multipage/ecmascript-language-statements-and-declarations.html#sec-try-statement) — `TryStatement : try Block Finally` 의 평가(「**F 가 정상 완료면 F 를 B 로 바꾼다**」)
> - [ECMA-262 — Error Objects](https://tc39.es/ecma262/multipage/fundamental-objects.html#sec-error-objects) — `InstallErrorCause` · `Error.isError` · Native Error Types · `AggregateError`
> - [TC39 finished proposals](https://github.com/tc39/proposals/blob/main/finished-proposals.md) — 판 경계(`Promise.any` 2021 · Error Cause 2022 · `Error.isError` 2026)
> - 명세 문장은 이 배치가 받아 둔 **ES2026 판 HTML** 에서 읽었다(알고리즘 단계를 옮기지 않고 연산 이름과 짧은 인용만 싣는다).
>
> ★★★ **명세 조항 번호는 인용하지 않는다.** 규칙 진술은 **추상 연산 이름**으로, 값·호출 로그·예외 타입과 메시지는 **전부 실행으로** 접지했다.
>
> **실행 검증** — 이 문서의 모든 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮겨 적은 출력이 하나도 없다).
> 배너의 `node20` 은 `~/.nvm/versions/node/v20.19.6/bin/node`, `node18` 은 기본 PATH 의 `node`(v18.19.1)다.
> ★★ **예외는 `try`/`catch` 로 받아 `이름 「메시지」` 꼴로** 찍었다. ★★ **`stack` 은 첫 줄 또는 「있나」만** 찍었다 — 둘째 줄부터는 파일 경로와 줄 번호가 박힌다.
> ★★ 단 하나, **아무도 안 받은 `throw` 를 node 가 어떻게 적나**(동작 (6))만은 표준 오류 전문을 실었다 — `node -e` 로 던져 경로 대신 `[eval]` 이 찍히게 했다.
> ★★★ **`Error.isError`(ES2026)는 두 node 판에 없다**(아래 판별 블록). 그 탐침은 **Google Chrome 151 을 헤드리스로** 돌렸다 — 배너가 `google-chrome --headless` 로 시작하는 블록이다.
> ★★ **이 주제에서 두 node 판이 갈린 탐침은 없다**(대조기 — 이 배치 전체 `identical 12`).
>
> **버전** — 판별 블록이 세 판(node 18 · node 20 · Chrome 151)에 같은 스크립트를 던진다.
>
> | 무엇 | 판 | 이 머신에서 |
> |---|---|---|
> | `throw` · `try`/`catch`/`finally` · `Error` 와 여섯 하위 생성자 | ES3 | 세 판 다 있다 |
> | `catch { }` — 바인딩 없는 `catch`(optional catch binding) | ES2019 | 세 판 다 있다 |
> | `AggregateError` · `Promise.any` | **ES2021** | 세 판 다 있다 |
> | `new Error(message, { cause })` — Error Cause | **ES2022** | 세 판 다 있다 |
> | `Error.isError` | **ES2026** | ★ **두 node 판에 없다** — Chrome 151 로만 돌렸다 |
> | `stack` · `Error.captureStackTrace` · `Error.stackTraceLimit` | — **ECMA-262 밖**(V8) | 세 판 다 있다 — ★ **그런데 `stack` 이 붙는 모양이 node 20 과 Chrome 151 에서 다르다**(동작 (6)·(7)) |
>
> ★★ **판 경계는 TC39 finished proposals 표와 이 목록의 README 를 대조했다** — 32행의 `cause`(ES2022)·`Error.isError`(ES2026)는 표와 같다. README 에 `AggregateError` 의 판은 적혀 있지 않다(표에서 `Promise.any` 가 2021).
>
> **★★★ 이 주제가 쓰는 창 — 그리고 부적용인 창**
>
> | 창 | 이 주제에서 무엇을 보나 |
> |---|---|
> | ★★★ **② 전수 격자**(본체) | `try` 3 × `finally` 3 = **9칸** — 호출자가 받은 것과 **`try` 의 끝이 닿았나**를 칸마다 찍고 **닿지 못한 칸을 스크립트가 센다**(동작 (1)) |
> | ★★ **④ 예외의 `constructor.name` + `message`** | 언어가 스스로 고르는 생성자(동작 (3)) · `cause` 사슬의 층마다의 이름(동작 (4)) · **바꿔치기된 예외에 원래 예외의 흔적이 있나**(동작 (2)) |
> | ★★ **① 추상 연산에 로그 심기** | `new RangeError(m, options)` 가 `options` 에 **`has cause` → `get cause`** 순으로 묻는 것(동작 (4)의 `[3]`) |
> | ★ **③ 브랜드 태그** | 보조 — 하위 생성자 일곱이 **전부 `[object Error]`** 인 것(동작 (3)) · 다른 realm 의 오류도 `[object Error]` 인 것(동작 (7)). ★ 판정의 정본은 34번이다 |
> | ★ **창을 바꿔 물었다**(제5의 상태) | node 에는 `Error.isError` 가 없어서, **같은 질문(「다른 realm 의 오류도 오류로 보나」)을 node 의 호스트 함수 `util.types.isNativeError` 로** 물었다(동작 (7)). 그 함수는 ECMA-262 가 아니다 |
> | ★ **부적용 — 두 번 컴파일**(엄격/비엄격) | 이 주제의 규칙은 모드를 안 탄다. 엄격 모드가 바꾸는 규칙은 35번이 정본이다 |
> | ★ **안 쟀다 — 성능** | ★★★ **「`try`/`catch` 는 느리다」를 한 줄도 쓰지 않는다.** 시간을 안 쟀다 |
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ★★ **`stack` 의 둘째 줄부터** — 파일 경로·줄·칸이 박힌다. 그래서 **첫 줄 또는 「있나」만** 찍었다 | ★★★ 9칸 격자의 **칸 글자**와 「닿지 못한 칸 N / M」 · `cause` 사슬의 **층 수와 이름** |
> | 동작 (6)의 표준 오류 블록의 **`node:internal/…:줄:칸`** — 실행마다가 아니라 **node 판마다** 바뀐다(판을 고정했으므로 재실행에서는 같다) | 예외의 **종류**(`TypeError`·`RangeError`…) — 명세가 어느 생성자를 쓰라고 정한다 |
> | 예외 **문구**(`Cannot read properties of null (reading 'stack')` 등) — V8 의 글자다 | `Error.isError` 와 `instanceof Error` 가 **갈리는 행** · ★★ **이 주제의 탐침에는 재실행에서 흔들린 칸이 없다**(재대조 동일) |
>
> **선행** — [01 — 값의 종류와 `typeof`](../01-value-types-and-typeof/2-summary.md)(직접 선행 — `throw` 는 **아무 값이나** 던진다는 것이 거기서 이어진다) ·
> [20 — 제너레이터](../20-generators/2-summary.md)(★★★ **`finally` 가 흐름을 가로채는 또 한 자리** — `g.return()` 이 `finally` 를 돌리고, **`finally` 안의 `yield` 가 `return()` 을 멈추고**, `finally` 의 `return "F"` 가 반환값을 바꾼다. 거기가 정본이다) ·
> [19 — 이터러블 프로토콜과 `for...of`](../19-iterable-protocol-and-for-of/2-summary.md)(본문이 던지면 `return()` 이 불린다 — 예외 조기 종료) ·
> [21 — 이터레이터 헬퍼](../21-iterator-helpers/2-summary.md)(헬퍼가 인자 검사에서 던질 때 **원본을 닫는다**) ·
> [31 — `JSON`](../31-json/2-summary.md)(★★ 순환 참조 `TypeError` 의 **여러 줄 문구가 경로를 말해 준다** — 문구가 V8 의 것이라는 판정이 거기 있다) ·
> [17 — 상속과 `super`](../17-inheritance-and-super/2-summary.md)(★ **옛 방식 `Error.call(this, m)` 이 `message` 를 잃는 것** — 거기가 정본).
>
> ★★ **경계 — 비동기 오류**(프로미스 거부 · `await` 의 `try`/`catch` · 미처리 거부)는 목록의 **37번 주제**와 **39번 주제**가 정본이다. 여기서는 `Promise.any` 가 **`AggregateError` 로 거부한다**는 한 줄만 쓴다.
> ★★ **경계 — 판정 방법**(`instanceof` · 브랜드 · realm)은 [34번](../34-type-checking-idioms/2-summary.md)이 정본이다. 여기서는 **`Error.isError` 가 무엇을 오류로 보나**까지다.
> ★ **경계 — 자원 정리**(`using` · `SuppressedError`)는 목록의 **51번 주제**의 몫이다.

```sh
# js32b-versions.sh
#!/usr/bin/env bash
# 이 문서의 모든 출력이 어느 판에서 나왔는지 -- 그리고 판별 기능 표(js32b-features.js)를 세 판에 던진다.
set -u -o pipefail
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
for n in "$N18" "$N20"; do
  "$n" -e 'console.log("node " + process.versions.node + "  v8 " + process.versions.v8)'
  "$n" js32b-features.js
done
google-chrome --version | sed 's/ *$//'
google-chrome --headless --virtual-time-budget=2000 --dump-dom "file://$PWD/js32b-page.html?js32b-features.js" 2>/dev/null \
  | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' \
  | sed 's/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&amp;/\&/g'
python3 --version
```

```js
// js32b-features.js
// 이 문서의 기능이 이 판에 있나 -- 판마다 같은 스크립트를 던진다(node 두 판 · Chrome).
// 문법 기능은 new Function 으로 물어서, 없는 판에서도 스크립트 전체가 죽지 않게 한다.
const has = (label, test) => {
  let r;
  try { r = test() ? "yes" : "no"; } catch (e) { r = "no (" + e.constructor.name + ")"; }
  console.log("  " + label.padEnd(52) + r);
};
const syntax = (src) => () => (new Function(src), true);
has("ES5     strict mode (this is undefined in a call)", () => new Function('"use strict"; return (function () { return this; })()')() === undefined);
has("ES5     Array.isArray", () => typeof Array.isArray === "function");
has("ES2015  Object.is", () => typeof Object.is === "function");
has("ES2015  Symbol.hasInstance / Symbol.toStringTag", () => typeof Symbol.hasInstance === "symbol" && typeof Symbol.toStringTag === "symbol");
has("ES2016  Array.prototype.includes / TypedArray", () => typeof [].includes === "function" && typeof new Float64Array(1).includes === "function");
has("ES2019  optional catch binding  catch { }", syntax("try {} catch {}"));
has("ES2021  AggregateError / Promise.any", () => typeof AggregateError === "function" && typeof Promise.any === "function");
has("ES2022  Error cause  new Error(m, { cause })", () => new Error("m", { cause: 1 }).cause === 1);
has("ES2022  private brand check  #x in o", syntax("class C { #x; static h(o) { return #x in o; } }"));
has("ES2024  Map.groupBy", () => typeof Map.groupBy === "function");
has("ES2026  Error.isError", () => typeof Error.isError === "function");
has("V8      Error.captureStackTrace (not ECMA-262)", () => typeof Error.captureStackTrace === "function");
```

```text
===== ./js32b-versions.sh (exit=0) =====
node 18.19.1  v8 10.2.154.26-node.28
  ES5     strict mode (this is undefined in a call)   yes
  ES5     Array.isArray                               yes
  ES2015  Object.is                                   yes
  ES2015  Symbol.hasInstance / Symbol.toStringTag     yes
  ES2016  Array.prototype.includes / TypedArray       yes
  ES2019  optional catch binding  catch { }           yes
  ES2021  AggregateError / Promise.any                yes
  ES2022  Error cause  new Error(m, { cause })        yes
  ES2022  private brand check  #x in o                yes
  ES2024  Map.groupBy                                 no
  ES2026  Error.isError                               no
  V8      Error.captureStackTrace (not ECMA-262)      yes
node 20.19.6  v8 11.3.244.8-node.33
  ES5     strict mode (this is undefined in a call)   yes
  ES5     Array.isArray                               yes
  ES2015  Object.is                                   yes
  ES2015  Symbol.hasInstance / Symbol.toStringTag     yes
  ES2016  Array.prototype.includes / TypedArray       yes
  ES2019  optional catch binding  catch { }           yes
  ES2021  AggregateError / Promise.any                yes
  ES2022  Error cause  new Error(m, { cause })        yes
  ES2022  private brand check  #x in o                yes
  ES2024  Map.groupBy                                 no
  ES2026  Error.isError                               no
  V8      Error.captureStackTrace (not ECMA-262)      yes
Google Chrome 151.0.7922.173
  ES5     strict mode (this is undefined in a call)   yes
  ES5     Array.isArray                               yes
  ES2015  Object.is                                   yes
  ES2015  Symbol.hasInstance / Symbol.toStringTag     yes
  ES2016  Array.prototype.includes / TypedArray       yes
  ES2019  optional catch binding  catch { }           yes
  ES2021  AggregateError / Promise.any                yes
  ES2022  Error cause  new Error(m, { cause })        yes
  ES2022  private brand check  #x in o                yes
  ES2024  Map.groupBy                                 yes
  ES2026  Error.isError                               yes
  V8      Error.captureStackTrace (not ECMA-262)      yes
Python 3.12.3
```

두 node 판 대조기의 집계 줄(이 배치의 모든 node 탐침) — 전문은 [3-answer.md](3-answer.md) 의 「실행 검증」에 있다.

`identical 12  ·  differs 0  ·  total 12`

## 한눈에 — 쉽게 말하면

**`finally` 는 「건물 출구의 검문소」다. 어느 문으로 나가든 — 걸어 나가든(정상), 물건을 들고 나가든(`return`), 경보가 울리며 뛰어나가든(`throw`) — 반드시 여기를 지난다.**

- ★★★ **검문소가 아무 말도 안 하면**, 나가던 사람은 **들고 있던 것 그대로** 나간다.
- ★★★ **검문소가 「이 문으로 나가라」고 직접 지시하면**(`finally` 안의 `return`·`throw`·`break`), 들고 있던 것은 **압수된다** — 반환값이든 **울리던 경보(예외)든**.
- ★★ 압수된 경보는 **기록도 안 남는다** — 새 경보에는 옛 경보를 가리키는 표시가 없다(파이썬과 다른 자리).
- ★★ **`cause` 는 사건 보고서에 붙이는 「원인: 첨부 보고서」 스테이플**이다. 언어가 자동으로 붙이지 않는다 — **보고서를 새로 쓰는 사람이 손으로 붙인다.**

```text
   try 블록이 끝나는 방식          finally 블록이 끝나는 방식          호출자가 받는 것

   return 'T'   ─┐              ┌─ (아무 말 없음)              ──▶  try 의 것 그대로
   throw E('T') ─┼──▶ finally ──┤
   흘러내림      ─┘              └─ return / throw / break     ──▶  finally 의 것 — try 의 것은 사라진다
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 출구의 검문소 | `finally` 블록 — 어느 완료(정상·`return`·`throw`)로 끝나도 돈다 | 동작 (1)의 `log` 열 |
| 들고 나가던 것 | `try` 블록의 **완료 기록**(completion) — 명세의 `B` | 동작 (1)의 `try's own ending` 열 |
| 검문소의 지시 | `finally` 의 **비정상 완료**(`return`·`throw`·`break`·`continue`) — 명세의 `F` | 동작 (1)·(2) |
| 압수 | 「**`F` 가 정상 완료면 `F` 를 `B` 로 바꾼다**」 — 거꾸로 말하면 **`F` 가 비정상이면 `B` 를 버린다** | 동작 (1)의 그림 |
| 원인 첨부 스테이플 | `new Error(message, { cause })` — `cause` 라는 **비열거 own 프로퍼티** | 동작 (4) |
| 여러 사건을 한 봉투에 | `AggregateError` 의 `errors` 배열 | 동작 (5) |

**똑같은 구조다** — 실무에서 물리는 자리도 굳어 있다.
「**정리 코드를 `finally` 에 넣으면서 `return true` 를 같이 넣었더니, DB 오류가 났는데도 함수가 `true` 를 돌려줬다**」와
「**오류를 감싸 다시 던졌더니 로그에 원래 원인이 안 보였다**」(감쌀 때 `cause` 를 안 넘겼다)가 그것이다(동작 (1)·(4)).

> **완료 기록(completion record)** — 명세가 「문장 하나가 어떻게 끝났나」를 적는 값. 종류가 정상·`return`·`throw`·`break`·`continue` 다섯이다.\
> 예: `return 1;` 의 완료 기록은 「`return` 종류, 값 1」.

> **`cause`** — 이 오류를 일으킨 **앞선 오류**를 가리키는 프로퍼티(ES2022). 생성자의 둘째 인자 `{ cause }` 로만 붙는다.\
> 예: `new Error("load failed", { cause: e }).cause === e`.

## 이 주제가 답하려는 질문

1. **`try` 와 `finally` 가 각각 어떻게 끝나면 호출자는 무엇을 받나** — `try` 의 반환값·예외가 **사라지는 칸은 몇 개**이고, 왜 사라지나?
2. **오류를 감싸 다시 던질 때 원인을 어떻게 이어 붙이나** — `cause` 는 무엇을 만들고, 사슬을 어떻게 끝까지 따라가나? `AggregateError` 는 그것과 어떻게 다른가?
3. **「이것이 오류인가」를 무엇으로 묻나** — `Error` 가 아닌 값이 던져질 때와 **다른 realm 에서 온 오류**일 때, `instanceof`·`Error.isError`·`stack` 은 각각 무엇을 말하나?

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 출력으로 읽는다.

### (1) ★★★ `try` 3 × `finally` 3 격자 — 이 주제의 본체

**언제 쓰나** — `finally` 에 정리 코드를 넣을 때 · 누가 `finally` 에 `return` 을 넣어 둔 코드를 읽을 때.
★★★ 칸마다 **호출자가 받은 것**과 **`try` 자신의 끝이 그대로 닿았나**를 찍는다. `try` 가 흘러내리면 `try` 뒤의 `return "after"` 까지 가야 「닿았다」다.

```js
// js32b-32a-finally-grid.js
// try 블록이 끝나는 세 방식 x finally 블록이 끝나는 세 방식 -- 호출자가 받는 것은 무엇인가.
// 칸마다: 호출자가 받은 것 / try 블록 자신의 끝(return 값 또는 던진 예외)이 호출자에게 닿았나.
const TRY = {
  "return 'T'": () => "T",
  "throw E('T')": () => { throw new Error("T"); },
  "(falls through)": () => undefined,
};
const FIN = {
  "return 'F'": "return",
  "throw E('F')": "throw",
  "(nothing)": "none",
};
const show = (r) => (r.threw ? r.value.constructor.name + " 「" + r.value.message + "」" : "value " + JSON.stringify(r.value));

function run(tryKind, finKind) {
  const log = [];
  const f = () => {
    try {
      log.push("try");
      const v = TRY[tryKind]();
      if (tryKind !== "(falls through)") return v;
    } finally {
      log.push("finally");
      if (FIN[finKind] === "return") return "F";
      if (FIN[finKind] === "throw") throw new Error("F");
    }
    log.push("after");
    return "after";
  };
  let r;
  try { r = { threw: false, value: f() }; } catch (e) { r = { threw: true, value: e }; }
  return { r, log };
}

console.log("[1] try x finally -- what the caller receives");
console.log("  " + "try ends with".padEnd(18) + "finally ends with".padEnd(19) + "try's own ending reached the caller?".padEnd(38) + "log".padEnd(24) + "caller receives");
let noAll = 0, cells = 0, noThrow = 0, throwCells = 0;
for (const t of Object.keys(TRY)) {
  for (const k of Object.keys(FIN)) {
    const { r, log } = run(t, k);
    // try 자신의 끝이 그대로 닿았나: return 'T' 면 값 "T", throw 면 메시지 "T" 인 예외, 흘러내리면 "after".
    let own;
    if (t === "return 'T'") own = !r.threw && r.value === "T";
    else if (t === "throw E('T')") own = r.threw && r.value.message === "T";
    else own = !r.threw && r.value === "after";
    cells += 1; if (!own) noAll += 1;
    if (t === "throw E('T')") { throwCells += 1; if (!own) noThrow += 1; }
    console.log("  " + t.padEnd(18) + k.padEnd(19) + (own ? "yes" : "no").padEnd(38) + log.join(" > ").padEnd(24) + show(r));
  }
}
console.log("");
console.log("rows where try threw and the caller never saw that exception: " + noThrow + " / " + throwCells);
console.log("cells where the try block's own ending did not reach the caller: " + noAll + " / " + cells);
```

```text
===== node20 js32b-32a-finally-grid.js (exit=0) =====
[1] try x finally -- what the caller receives
  try ends with     finally ends with  try's own ending reached the caller?  log                     caller receives
  return 'T'        return 'F'         no                                    try > finally           value "F"
  return 'T'        throw E('F')       no                                    try > finally           Error 「F」
  return 'T'        (nothing)          yes                                   try > finally           value "T"
  throw E('T')      return 'F'         no                                    try > finally           value "F"
  throw E('T')      throw E('F')       no                                    try > finally           Error 「F」
  throw E('T')      (nothing)          yes                                   try > finally           Error 「T」
  (falls through)   return 'F'         no                                    try > finally           value "F"
  (falls through)   throw E('F')       no                                    try > finally           Error 「F」
  (falls through)   (nothing)          yes                                   try > finally > after   value "after"

rows where try threw and the caller never saw that exception: 2 / 3
cells where the try block's own ending did not reach the caller: 6 / 9
```

```text
   명세 — TryStatement : try Block Finally 의 평가

   ① B = Block 을 평가한 완료 기록          (return 'T' / throw E('T') / 정상)
   ② F = Finally 를 평가한 완료 기록        (return 'F' / throw E('F') / 정상)
   ③ F 가 정상 완료면  F = B               ← finally 가 조용하면 try 의 것을 넘긴다
   ④ F 를 돌려준다                          ← finally 가 무엇이든 끝을 쥐면, B 는 여기서 버려진다

                         finally 정상        finally return        finally throw
   try return 'T'   ─▶   B  (value T)        F  (value F)          F  (Error F)
   try throw E('T') ─▶   B  (Error T)        F  (value F) ★삼킴    F  (Error F) ★바꿔치기
   try 정상          ─▶   B  → after          F  (value F)          F  (Error F)
```

- ★★★ **집계 줄 — `cells where the try block's own ending did not reach the caller: 6 / 9`.** `finally` 가 **아무 말 없이 끝난 세 칸만** `try` 의 끝이 닿았다.
  **`finally` 가 `return`·`throw` 로 끝난 여섯 칸은 전부 `finally` 의 것**이 나간다 — `try` 가 무엇이었든 상관없다(위 그림의 ③·④).
- ★★★ **`try` 가 던진 세 행 중 둘에서 그 예외가 사라졌다**(`rows where try threw and the caller never saw that exception: 2 / 3`).
  `finally` 의 `return 'F'` 는 예외를 **조용히 삼키고**(호출자는 `value "F"` 를 받는다 — 예외가 있었다는 것조차 모른다),
  `finally` 의 `throw E('F')` 는 예외를 **바꿔치기**한다(호출자는 `Error 「F」` 를 받는다).
- ★★ **`log` 열은 전부 `try > finally` 로 시작한다** — `finally` 는 **아홉 칸 모두에서 돌았다.** 「`finally` 가 도나」는 질문이 아니다. **「`finally` 가 끝을 쥐나」가 질문이다.**
- ★★ **`try` 가 흘러내린 행에서 `after` 는 한 칸에서만 찍혔다** — `finally` 가 `return`·`throw` 로 끝나면 `try` **뒤의 문장도 안 돈다.**
- ★ 명세는 이것을 **한 문장**으로 정한다 — 「**If F is a normal completion, set F to B.**」 예외를 삼키는 특별 규칙이 따로 있는 것이 아니라, **「`finally` 의 완료가 정상일 때만 `try` 의 완료를 되살린다」** 는 규칙의 뒷면이다.

### (2) ★★ `finally` 가 흐름에 끼어드는 자리 넷 — 반환값의 시점 · `break` · `catch` 와의 순서 · 흔적

**언제 쓰나** — `finally` 안에서 반환할 변수를 고치거나, 루프 안의 `try` 에 `finally { continue; }` 를 쓰려 할 때.

```js
// js32b-32b-finally-details.js
// finally 가 흐름에 끼어드는 자리 넷 -- 반환값이 정해지는 시점 · 루프의 break · catch 와의 순서 · 바꿔치기된 예외에 남는 것.
const show = (f) => {
  try { return "value " + JSON.stringify(f()); }
  catch (e) { return e.constructor.name + " 「" + e.message + "」"; }
};
const row = (label, v) => console.log("  " + label.padEnd(46) + v);

console.log("[1] return x, then finally changes x");
row("primitive: return n; finally n = 2", show(() => { let n = 1; try { return n; } finally { n = 2; } }));
row("object: return o; finally o.v = 2", show(() => { const o = { v: 1 }; try { return o; } finally { o.v = 2; } }));
row("order of evaluation", show(() => {
  const log = [];
  const val = () => { log.push("return expr"); return "R"; };
  try { return val(); } finally { log.push("finally"); console.log("    log: " + log.join(" > ")); }
}));

console.log("[2] break / continue inside finally, with an exception in flight");
row("for: try throw; finally break", show(() => {
  for (let i = 0; i < 1; i++) { try { throw new Error("T"); } finally { break; } }
  return "after loop";
}));
row("for: try throw; finally continue", show(() => {
  let n = 0;
  for (let i = 0; i < 3; i++) { try { n++; throw new Error("T"); } finally { continue; } }
  return "after loop, n=" + n;
}));
row("label: try return; finally break out", show(() => {
  out: { try { return "T"; } finally { break out; } }
  return "after block";
}));

console.log("[3] catch and finally together");
const order = [];
row("try throw; catch returns; finally logs", show(() => {
  try { order.push("try"); throw new Error("T"); }
  catch (e) { order.push("catch"); return "C"; }
  finally { order.push("finally"); }
}));
row("  order", order.join(" > "));
row("try throw; catch throws; finally returns", show(() => {
  try { throw new Error("T"); } catch (e) { throw new Error("C"); } finally { return "F"; }
}));
row("try throw; catch throws; finally (nothing)", show(() => {
  try { throw new Error("T"); } catch (e) { throw new Error("C"); } finally { }
}));

console.log("[4] the replacing exception -- does it point back to the one it replaced?");
let caught;
try { try { throw new Error("T"); } finally { throw new Error("F"); } } catch (e) { caught = e; }
row("caught.message", caught.message);
row("'cause' in caught", "cause" in caught);
row("own keys of caught", JSON.stringify(Reflect.ownKeys(caught)));
```

```text
===== node20 js32b-32b-finally-details.js (exit=0) =====
[1] return x, then finally changes x
  primitive: return n; finally n = 2            value 1
  object: return o; finally o.v = 2             value {"v":2}
    log: return expr > finally
  order of evaluation                           value "R"
[2] break / continue inside finally, with an exception in flight
  for: try throw; finally break                 value "after loop"
  for: try throw; finally continue              value "after loop, n=3"
  label: try return; finally break out          value "after block"
[3] catch and finally together
  try throw; catch returns; finally logs        value "C"
    order                                       try > catch > finally
  try throw; catch throws; finally returns      value "F"
  try throw; catch throws; finally (nothing)    Error 「C」
[4] the replacing exception -- does it point back to the one it replaced?
  caught.message                                F
  'cause' in caught                             false
  own keys of caught                            ["stack","message"]
```

```text
   return n;  이 하는 일          finally { n = 2; } 가 하는 일

   ① n 을 읽어 값 1 을 완료 기록에 담는다        ② 변수 n 을 2 로 바꾼다
      [return, 1]                                  (완료 기록 안의 1 은 그대로)
   ③ finally 가 정상으로 끝났다 → [return, 1] 이 나간다      -> value 1

   객체면 완료 기록에 담기는 것이 「같은 객체」라서 ② 의 o.v = 2 가 보인다  -> value {"v":2}
```

- ★★★ **`[1]` `return n` 의 값은 `finally` 가 돌기 전에 정해진다** — 원시값이면 `finally` 에서 변수를 고쳐도 **`value 1`**, 객체면 **같은 객체**를 담았으므로 고친 것이 보인다(`{"v":2}`).
  로그 `return expr > finally` 가 순서를 보여 준다 — **식을 먼저 평가하고 그다음 `finally`** 다.
- ★★★ **`[2]` `break`·`continue` 도 끝을 쥔다** — `finally { break; }` 는 날아가던 `Error 「T」` 를 **삼키고 루프를 빠져나가** `after loop` 을 돌려준다.
  `finally { continue; }` 는 **세 번 던져진 예외를 세 번 다 삼키고** 루프를 끝까지 돈다(`n=3`). 라벨 블록의 `break out` 은 **`return "T"` 를 삼켰다.**
- ★★ **`[3]` `catch` 가 먼저, `finally` 가 나중**이다(`try > catch > finally`). `catch` 가 돌려준 `"C"` 도 `finally` 가 조용하면 그대로 나가고,
  `catch` 가 던진 `Error 「C」` 는 `finally` 가 `return "F"` 하면 **삼켜진다.** — 동작 (1)의 규칙이 `catch` 의 완료에도 그대로 걸린다(명세의 `C` 가 `B` 자리에 들어간다).
- ★★★ **`[4]` 바꿔치기한 예외에는 원래 예외의 흔적이 없다** — `'cause' in caught` 가 `false`, own 키는 `["stack","message"]` 뿐이다.
  ★★ **파이썬은 여기서 다르다** — 같은 모양에서 새 예외의 `__context__` 에 옛 예외가 **자동으로** 붙는다(동작 (8)). JS 는 **자동 연결이 없다.** 이으려면 `cause` 를 **손으로** 넘겨야 한다(동작 (4)).
- ★ **제너레이터에서는 한 겹이 더 있다** — `g.return()` 이 `finally` 를 돌리고, **`finally` 안의 `yield` 가 그 `return()` 을 멈추고**, `finally` 의 `return "F"` 가 반환값을 바꾼다. [20번](../20-generators/2-summary.md) 동작 (3)이 정본이다 — **같은 집안의 규칙**이다(여기의 ③·④와 같은 모양).

### (3) ★★ `Error` 계층 — 언어가 스스로 고르는 생성자와 가족 트리

**언제 쓰나** — `catch` 에서 종류로 갈라 처리할 때 · 자기 오류 클래스를 만들 때.

```js
// js32b-32d-hierarchy.js
// Error 계층 -- 언어가 스스로 던지는 종류는 무엇이고, 무엇이 이어져 있나.
const row = (label, v) => console.log("  " + label.padEnd(40) + v);
const tag = (v) => Object.prototype.toString.call(v);
const catchIt = (f) => { try { f(); return "(no throw)"; } catch (e) { return e; } };

console.log("[1] which constructor the language itself picks");
const cases = [
  ["null.x", () => null.x],
  ["new Array(-1)", () => new Array(-1)],
  ["JSON.parse('{')", () => JSON.parse("{")],
  ["notDeclaredAnywhere", () => notDeclaredAnywhere],
  ["decodeURIComponent('%')", () => decodeURIComponent("%")],
  ["(1).toFixed(101)", () => (1).toFixed(101)],
  ["Symbol() + ''", () => Symbol() + ""],
  ["new Function('return (')", () => new Function("return (")],
];
for (const [label, f] of cases) {
  const e = catchIt(f);
  row(label, e.constructor.name.padEnd(16) + "instanceof Error " + (e instanceof Error));
}

console.log("[2] the family tree");
const ctors = [TypeError, RangeError, SyntaxError, ReferenceError, EvalError, URIError, AggregateError];
for (const C of ctors) {
  row(C.name, "proto of ctor: " + Object.getPrototypeOf(C).name + "   name on prototype: " + Object.hasOwn(C.prototype, "name") + "   tag " + tag(new C(C === AggregateError ? [] : undefined)));
}

console.log("[3] message, name, and String(e)");
row("new Error().message", JSON.stringify(new Error().message));
row("hasOwn(new Error(), 'message')", Object.hasOwn(new Error(), "message"));
row("new Error(42).message", JSON.stringify(new Error(42).message));
row("String(new TypeError('bad'))", String(new TypeError("bad")));
row("String(new TypeError())", String(new TypeError()));
class NotFound extends Error {}
row("new NotFound('x').name", new NotFound("x").name);
class NotFound2 extends Error { constructor(m, o) { super(m, o); this.name = new.target.name; } }
row("new NotFound2('x').name", new NotFound2("x").name);
row("String(new NotFound2('x'))", String(new NotFound2("x")));
row("new NotFound2('x', { cause: 1 }).cause", new NotFound2("x", { cause: 1 }).cause);

console.log("[4] AggregateError -- one error holding several");
const ag = new AggregateError([new RangeError("r"), new TypeError("t", { cause: "deep" })], "two failed", { cause: "top" });
row("ag.message", ag.message);
row("ag.errors.length", ag.errors.length);
row("ag.errors kinds", ag.errors.map((e) => e.constructor.name).join(", "));
row("ag.errors[1].cause", ag.errors[1].cause);
row("ag.cause", ag.cause);
row("Array.isArray(ag.errors)", Array.isArray(ag.errors));
row("descriptor of errors", JSON.stringify(Object.getOwnPropertyDescriptor(ag, "errors"), (k, v) => (k === "value" ? "[...]" : v)));
const src = [1, 2];
const ag2 = new AggregateError(src);
src.push(3);
row("errors copied from the iterable?", ag2.errors.length + " (source now " + src.length + ")");
Promise.any([Promise.reject(new Error("a")), Promise.reject("b")]).catch((e) => {
  row("Promise.any rejects with", e.constructor.name + " 「" + e.message + "」");
  row("  its errors", JSON.stringify(e.errors.map((x) => (x instanceof Error ? "Error " + x.message : x))));
});
```

```text
===== node20 js32b-32d-hierarchy.js (exit=0) =====
[1] which constructor the language itself picks
  null.x                                  TypeError       instanceof Error true
  new Array(-1)                           RangeError      instanceof Error true
  JSON.parse('{')                         SyntaxError     instanceof Error true
  notDeclaredAnywhere                     ReferenceError  instanceof Error true
  decodeURIComponent('%')                 URIError        instanceof Error true
  (1).toFixed(101)                        RangeError      instanceof Error true
  Symbol() + ''                           TypeError       instanceof Error true
  new Function('return (')                SyntaxError     instanceof Error true
[2] the family tree
  TypeError                               proto of ctor: Error   name on prototype: true   tag [object Error]
  RangeError                              proto of ctor: Error   name on prototype: true   tag [object Error]
  SyntaxError                             proto of ctor: Error   name on prototype: true   tag [object Error]
  ReferenceError                          proto of ctor: Error   name on prototype: true   tag [object Error]
  EvalError                               proto of ctor: Error   name on prototype: true   tag [object Error]
  URIError                                proto of ctor: Error   name on prototype: true   tag [object Error]
  AggregateError                          proto of ctor: Error   name on prototype: true   tag [object Error]
[3] message, name, and String(e)
  new Error().message                     ""
  hasOwn(new Error(), 'message')          false
  new Error(42).message                   "42"
  String(new TypeError('bad'))            TypeError: bad
  String(new TypeError())                 TypeError
  new NotFound('x').name                  Error
  new NotFound2('x').name                 NotFound2
  String(new NotFound2('x'))              NotFound2: x
  new NotFound2('x', { cause: 1 }).cause  1
[4] AggregateError -- one error holding several
  ag.message                              two failed
  ag.errors.length                        2
  ag.errors kinds                         RangeError, TypeError
  ag.errors[1].cause                      deep
  ag.cause                                top
  Array.isArray(ag.errors)                true
  descriptor of errors                    {"value":"[...]","writable":true,"enumerable":false,"configurable":true}
  errors copied from the iterable?        2 (source now 3)
  Promise.any rejects with                AggregateError 「All promises were rejected」
    its errors                            ["Error a","b"]
```

```text
   Error ◀── 생성자의 [[Prototype]] 이 Error 인 일곱
     ├─ TypeError        null.x · Symbol() + '' · (값의 종류가 틀렸다)
     ├─ RangeError       new Array(-1) · (1).toFixed(101) · (값이 범위 밖)
     ├─ SyntaxError      JSON.parse('{') · new Function('return (') · (글자를 코드·데이터로 못 읽었다)
     ├─ ReferenceError   선언 안 된 이름을 읽었다
     ├─ URIError         decodeURIComponent('%')
     ├─ EvalError        ★ 이 목록의 식 중 이것을 던진 것은 없다 — 호환을 위해 남아 있다
     └─ AggregateError   여러 오류를 errors 배열로 든다 (ES2021)

   일곱 모두  instanceof Error · 브랜드 태그 [object Error] · name 은 각자의 prototype 에
```

- ★★ **`[1]` 여덟 식의 생성자는 명세가 정한다** — 종류는 보장이고 **문구는 V8 의 것**이다. 여덟 모두 `instanceof Error` 가 `true`.
- ★★ **`[2]` 일곱 하위 생성자는 전부 `Error` 를 부모로** 갖고(`proto of ctor: Error`), **`name` 은 각자의 `prototype` 에** 있으며, 브랜드는 **모두 `[object Error]`** 다 — 브랜드 태그로는 **종류를 못 가른다.**
- ★★★ **`[3]` `message` 를 안 주면 own `message` 가 없다**(`hasOwn … false` — `""` 는 `Error.prototype.message` 를 읽은 것이다). `42` 는 `"42"` 로 바뀐다.
  `String(e)` 는 **`name: message`**, `message` 가 비면 **`name` 만**이다.
- ★★★ **`class NotFound extends Error {}` 의 `name` 은 `"Error"`** 다 — `name` 은 `Error.prototype` 에서 읽히기 때문이다. 클래스 이름을 쓰고 싶으면 **`this.name = new.target.name`** 을 직접 넣는다(`NotFound2`).
  ★ `super(m, o)` 로 옵션을 넘기면 **`cause` 도 그대로 붙는다**(`1`). 옛 방식 `Error.call(this, m)` 이 `message` 를 잃는 것은 [17번](../17-inheritance-and-super/2-summary.md)이 정본이다.
- ★★ **`[4]` `AggregateError`** 는 동작 (5)에서 읽는다.

### (4) ★★★ `cause` 사슬 — 무엇이 붙고, 끝까지 따라가면 무엇이 보이나

**언제 쓰나** — 아래층 오류를 잡아 **더 뜻 있는 오류로 감싸 다시 던질 때**(「설정 파일 파싱 실패」 → 「설정을 못 읽음」 → 「앱 시작 실패」).

```js
// js32b-32c-cause-chain.js
// Error 의 두 번째 인자 { cause } -- 무엇이 붙고, 사슬을 끝까지 따라가면 무엇이 보이나.
const name = (e) => (e instanceof Error ? e.constructor.name + " 「" + e.message + "」" : typeof e + " " + JSON.stringify(e));
const row = (label, v) => console.log("  " + label.padEnd(56) + v);

console.log("[1] three layers, each wrapping the one below");
function readConfig() { throw new SyntaxError("Unexpected token } in config.json"); }
function loadSettings() {
  try { return readConfig(); } catch (e) { throw new Error("settings could not be loaded", { cause: e }); }
}
function startApp() {
  try { return loadSettings(); } catch (e) { throw new TypeError("app failed to start", { cause: e }); }
}
let top;
try { startApp(); } catch (e) { top = e; }
let depth = 0;
for (let e = top; e !== undefined; e = e.cause) {
  console.log("  " + "  ".repeat(depth) + "depth " + depth + "  " + name(e));
  depth += 1;
  if (!(e instanceof Error)) break;
}

console.log("[2] what the option actually creates");
const d = (o, k) => JSON.stringify(Object.getOwnPropertyDescriptor(o, k));
row("new Error('m', { cause: 1 }) -> cause", d(new Error("m", { cause: 1 }), "cause"));
row("hasOwn(new Error('m'), 'cause')", Object.hasOwn(new Error("m"), "cause"));
row("hasOwn(new Error('m', {}), 'cause')", Object.hasOwn(new Error("m", {}), "cause"));
row("hasOwn(new Error('m', { cause: undefined }), 'cause')", Object.hasOwn(new Error("m", { cause: undefined }), "cause"));
row("new Error('m', 'text').cause", String(new Error("m", "text").cause));
row("JSON.stringify(new Error('m', { cause: 1 }))", JSON.stringify(new Error("m", { cause: 1 })));

console.log("[3] how the constructor reads the option (a Proxy logs every trap)");
const log = [];
const opts = new Proxy({ cause: "c" }, {
  has(t, k) { log.push("has " + String(k)); return Reflect.has(t, k); },
  get(t, k, r) { log.push("get " + String(k)); return Reflect.get(t, k, r); },
});
new RangeError("m", opts);
row("traps", log.join(" > "));

console.log("[4] a cause that is not an Error, and a cause chain that loops");
const s = new Error("outer", { cause: "just a string" });
row("typeof s.cause", typeof s.cause);
const a = new Error("a"), b = new Error("b", { cause: a });
a.cause = b;
const seen = new Set();
const walk = [];
for (let e = b; e instanceof Error; e = e.cause) {
  if (seen.has(e)) { walk.push("(seen before: " + e.message + ")"); break; }
  seen.add(e); walk.push(e.message);
}
row("walk with a seen-set", walk.join(" -> "));
```

```text
===== node20 js32b-32c-cause-chain.js (exit=0) =====
[1] three layers, each wrapping the one below
  depth 0  TypeError 「app failed to start」
    depth 1  Error 「settings could not be loaded」
      depth 2  SyntaxError 「Unexpected token } in config.json」
[2] what the option actually creates
  new Error('m', { cause: 1 }) -> cause                   {"value":1,"writable":true,"enumerable":false,"configurable":true}
  hasOwn(new Error('m'), 'cause')                         false
  hasOwn(new Error('m', {}), 'cause')                     false
  hasOwn(new Error('m', { cause: undefined }), 'cause')   true
  new Error('m', 'text').cause                            undefined
  JSON.stringify(new Error('m', { cause: 1 }))            {}
[3] how the constructor reads the option (a Proxy logs every trap)
  traps                                                   has cause > get cause
[4] a cause that is not an Error, and a cause chain that loops
  typeof s.cause                                          string
  walk with a seen-set                                    b -> a -> (seen before: b)
```

```text
   startApp  catch(e) → throw new TypeError("app failed to start", { cause: e })
                                           │ cause
   loadSettings catch(e) → throw new Error("settings could not be loaded", { cause: e })
                                           │ cause
   readConfig  throw new SyntaxError("Unexpected token } in config.json")
                                           │ cause
                                       undefined   ← 여기서 멈춘다

   걷는 법:  for (let e = top; e !== undefined; e = e.cause) { … }
   ★ 사슬이다 — 한 오류의 cause 는 값 하나. 여러 갈래(트리)는 AggregateError 의 errors 가 맡는다(동작 (5))
```

- ★★★ **`[1]` 사슬은 세 층**이고, 맨 위부터 **`TypeError` → `Error` → `SyntaxError`**, 그 아래 `cause` 는 `undefined` 다.
  **언어는 이 사슬을 자동으로 만들지 않는다** — `catch` 에서 `{ cause: e }` 를 **넘긴 사람만** 이어진다(동작 (2)의 `[4]` — 바꿔치기에는 흔적이 없었다).
- ★★★ **`[2]` `cause` 는 비열거 own 데이터 프로퍼티**다(`enumerable:false`). 그래서 **`JSON.stringify(err)` 는 `{}`** 다 — `message` 도 `stack` 도 비열거라 아무것도 안 나온다(31번의 격자 규칙).
- ★★★ **옵션 객체에 `cause` 키가 있어야만 붙는다** — `{}` 면 `hasOwn … false`, **`{ cause: undefined }` 면 `true`**(값이 `undefined` 인 own 프로퍼티가 생긴다). 둘째 인자가 문자열이면 **무시된다**(`undefined`).
- ★★ **`[3]` 생성자는 `options` 에 두 번 묻는다 — `has cause > get cause`.** 명세의 `InstallErrorCause` 가 「**`HasProperty` 가 참이면 `Get`**」이기 때문이다. `has` 가 먼저라서 **키의 존재**와 **값**이 따로 판정된다(위의 `{ cause: undefined }` 가 그 결과다).
- ★★ **`[4]` `cause` 에는 아무 값이나 들어간다** — 문자열이면 `typeof s.cause` 가 `string`. 사슬을 걷는 코드가 `e.cause.message` 를 믿으면 거기서 멈춘다.
  ★★ **사슬은 고리가 될 수 있다** — `a.cause = b` 로 되감으면 **`seen` 집합 없이 걷는 루프는 끝나지 않는다.** 위 걷기는 `b -> a -> (seen before: b)` 에서 멈췄다.
- ★ **Go 의 래핑과 같은 일, 다른 모양** — Go 는 `fmt.Errorf("…: %w", err)` 로 감싸고 `errors.Unwrap` 을 `nil` 까지 돈다. [Go 24](../../../go/syntax/24-error-wrapping-and-errors-is-as-join/2-summary.md)의 본체 창이 바로 「`Unwrap` 을 `nil` 까지 돌며 층마다 찍는 창」이다. **JS 의 `for (e = top; e; e = e.cause)` 가 그 짝**이다. 다른 점은 아래 표.

| | Go `%w` | JS `cause` |
|---|---|---|
| 감싸는 법 | `fmt.Errorf("…: %w", err)` — 메시지에 원인 글자가 **붙는다** | `new Error("…", { cause: e })` — 메시지는 **그대로**, 원인은 **프로퍼티** |
| 사슬을 걷는 법 | `errors.Unwrap` 을 `nil` 까지 | `.cause` 를 `undefined` 까지(직접 쓴다) |
| 「사슬 안에 이것이 있나」 | `errors.Is`·`errors.As` 가 **표준** | ★ **표준 함수가 없다** — 직접 걷는다 |
| 여러 원인 | `errors.Join` — **트리** | `AggregateError` 의 `errors` — 배열(동작 (5)) |

### (5) ★★ `AggregateError` — 한 오류가 여럿을 든다

**언제 쓰나** — 여러 작업이 **각각 실패한 것을 한 번에** 보고할 때 · `Promise.any` 가 전부 실패했을 때.

동작 (3)의 블록 `[4]` 가 이것이다.

```text
   ag = AggregateError  "two failed"   cause "top"
          │ errors  (배열 — 생성할 때 이터러블을 복사해 만든다)
          ├─ RangeError "r"
          └─ TypeError  "t"   cause "deep"

   ★ 두 축이 따로다 — errors(여러 갈래) 와 cause(한 줄 사슬). 둘 다 달 수 있다
```

- ★★ **`errors` 는 배열**(`Array.isArray … true`)이고 **비열거 own 프로퍼티**다. **생성할 때 이터러블을 복사해** 만든다 — 원본에 `push` 해도 `2 (source now 3)`.
- ★★ **`cause` 도 따로 달 수 있다**(`ag.cause` 가 `top`) — `errors` 안의 각 오류도 **자기 `cause`** 를 가진다(`deep`). **여러 갈래(`errors`) × 한 줄 사슬(`cause`)** 의 두 축이 겹쳐 트리가 된다.
- ★★ **`Promise.any` 가 전부 거부되면 `AggregateError 「All promises were rejected」`** 로 거부한다. `errors` 에는 거부 이유가 **그대로** 들어간다 — 문자열 `"b"` 도 그대로다.
- ★ **대비 둘** — Go `errors.Join` 도 트리를 만든다([Go 24](../../../go/syntax/24-error-wrapping-and-errors-is-as-join/2-summary.md) 동작 (7)). 파이썬 `ExceptionGroup` 은 **빈 리스트를 거절**하는데([Python 27](../../../python/syntax/27-exception-groups-and-except-star/2-summary.md) 어디서 틀리나 (9)), **`new AggregateError([])` 는 통과한다**(동작 (3)의 `[2]` 가 `[]` 로 만들었다).

### (6) ★★ `Error` 가 아닌 값을 던지면 — 그리고 `stack` 은 누구의 것인가

**언제 쓰나** — 남의 라이브러리가 **문자열을 던질 때** · 로그에 `e.stack` 을 찍는 코드가 `undefined` 를 찍을 때.

```js
// js32b-32e-thrown-values.js
// throw 는 아무 값이나 던진다 -- catch 가 받는 것, 그리고 stack 이 있나(첫 줄만 찍는다 -- 나머지 줄에는 경로가 박힌다).
const row = (label, v) => console.log("  " + label.padEnd(34) + v);
const firstLine = (s) => (typeof s === "string" ? JSON.stringify(s.split("\n")[0]) : String(s));

console.log("[1] what catch receives");
const values = [
  ["throw 'disk full'", () => { throw "disk full"; }],
  ["throw 404", () => { throw 404; }],
  ["throw { code: 'E1' }", () => { throw { code: "E1" }; }],
  ["throw null", () => { throw null; }],
  ["throw undefined", () => { throw undefined; }],
  ["throw new Error('disk full')", () => { throw new Error("disk full"); }],
];
for (const [label, f] of values) {
  try { f(); } catch (e) {
    const kind = e === null ? "null" : typeof e;
    let st;
    try { st = firstLine(e.stack); } catch (x) { st = x.constructor.name + " 「" + x.message + "」"; }
    row(label, "typeof " + kind.padEnd(10) + "e.stack -> " + st);
  }
}

console.log("[2] where stack lives on a real Error (V8)");
const e = new Error("m");
const d = Object.getOwnPropertyDescriptor(e, "stack");
row("hasOwn(e, 'stack')", Object.hasOwn(e, "stack"));
row("descriptor kind", d ? ("value" in d ? "data" : "accessor") + ", enumerable " + d.enumerable : "(none)");
row("'stack' in Error.prototype", "stack" in Error.prototype);
row("typeof Error.captureStackTrace", typeof Error.captureStackTrace);
row("Error.stackTraceLimit", Error.stackTraceLimit);
const plain = { message: "not an error" };
Error.captureStackTrace(plain);
row("after captureStackTrace(plain)", firstLine(plain.stack));
```

```text
===== node20 js32b-32e-thrown-values.js (exit=0) =====
[1] what catch receives
  throw 'disk full'                 typeof string    e.stack -> undefined
  throw 404                         typeof number    e.stack -> undefined
  throw { code: 'E1' }              typeof object    e.stack -> undefined
  throw null                        typeof null      e.stack -> TypeError 「Cannot read properties of null (reading 'stack')」
  throw undefined                   typeof undefined e.stack -> TypeError 「Cannot read properties of undefined (reading 'stack')」
  throw new Error('disk full')      typeof object    e.stack -> "Error: disk full"
[2] where stack lives on a real Error (V8)
  hasOwn(e, 'stack')                true
  descriptor kind                   data, enumerable false
  'stack' in Error.prototype        false
  typeof Error.captureStackTrace    function
  Error.stackTraceLimit             10
  after captureStackTrace(plain)    "Error: not an error"
```

- ★★★ **`throw` 는 아무 값이나 던진다** — `catch` 는 **던진 값 그대로**를 받는다(문자열이면 `typeof string`). **`stack` 은 `Error` 객체에만** 있다 — 문자열·숫자·평범한 객체는 `undefined`.
  ★★ **`throw null`·`throw undefined` 를 받은 `catch` 에서 `e.stack` 을 읽으면 그 자리에서 `TypeError`** 다 — 오류를 로그로 남기려던 코드가 **새 오류를 던진다.**
- ★★★ **`[2]` `stack` 은 ECMA-262 에 없다**(ES2026 판 HTML 에 `prototype.stack` 이라는 글자가 0번 나온다) — V8 이 붙인다. 이 node 20 에서는 **own 데이터 프로퍼티**, 비열거다.
  ★★★ **그런데 Chrome 151 의 V8 에서는 own 접근자 프로퍼티다**(동작 (7)의 `[3]` — `accessor, enumerable false`). **같은 V8 계열인데 판마다 모양이 다르다** — 명세 밖이라 고칠 수 있는 자리다.
- ★★ `Error.captureStackTrace`·`Error.stackTraceLimit`(기본 `10`)도 **V8 의 것**이다. `captureStackTrace` 는 **평범한 객체에도** `stack` 을 심는다(`"Error: not an error"`).

아무도 안 받은 `throw` 는 node 가 표준 오류에 적는다(표준 출력은 버렸다).

```sh
# js32b-32i-uncaught.sh
#!/usr/bin/env bash
# 아무도 안 받은 throw -- node 가 표준 오류에 무엇을 적나. 문자열 · 평범한 객체 · Error 셋.
# (node -e 로 던지면 경로 대신 [eval] 이 찍힌다. 이 블록은 표준 오류만 받는다.)
set -u -o pipefail
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
for src in 'throw "disk full"' 'throw { code: "E1" }' 'throw new Error("disk full")'; do
  echo "--- node20 -e '$src'"
  "$N20" -e "$src" 2>&1 >/dev/null
  echo "(exit $?)"
done
```

```text
===== ./js32b-32i-uncaught.sh (exit=0) =====
--- node20 -e 'throw "disk full"'

[eval]:1
throw "disk full"
^
disk full
(Use `node --trace-uncaught ...` to show where the exception was thrown)

Node.js v20.19.6
(exit 1)
--- node20 -e 'throw { code: "E1" }'
[eval]:1
throw { code: "E1" }
^

{ code: 'E1' }

Node.js v20.19.6
(exit 1)
--- node20 -e 'throw new Error("disk full")'
[eval]:1
throw new Error("disk full")
^

Error: disk full
    at [eval]:1:7
    at runScriptInThisContext (node:internal/vm:209:10)
    at node:internal/process/execution:118:14
    at [eval]-wrapper:6:24
    at runScript (node:internal/process/execution:101:62)
    at evalScript (node:internal/process/execution:133:3)
    at node:internal/main/eval_string:51:3

Node.js v20.19.6
(exit 1)
```

- ★★ **셋 다 `exit 1`** 이고 소스 줄과 `^` 가 찍힌다. 그런데 **던진 값 아래가 다르다** — 문자열은 **값 한 줄 + ``(Use `node --trace-uncaught ...` …)`` 안내**, 객체는 `{ code: 'E1' }`, `Error` 는 **`Error: disk full` + `at …` 줄들**(= `stack`).
  **문자열에는 호출 경로가 없어서** node 가 「어디서 던졌는지 보려면 이 플래그를 켜라」고 따로 알려 준다. **`Error` 를 던져야 하는 이유가 이 블록 하나에 있다.**
- ★ 이 블록의 모양(안내 문구 · `node:internal/…` 줄)은 **node 의 것**이다 — 브라우저는 콘솔에 다르게 적는다.

### (7) ★★★ `Error.isError`(ES2026) — 다른 realm 의 오류도 오류로 보나

**언제 쓰나** — iframe·`vm`·워커처럼 **다른 전역에서 만든 오류**를 받을 때 · `instanceof Error` 가 `false` 인데 로그에는 분명히 오류일 때.
★★★ **두 node 판에는 없다**(판별 블록의 `ES2026` 줄). 그래서 **node 에서는 같은 질문을 호스트 함수로** 묻고, **Chrome 151 에서 `Error.isError` 로** 물었다.

```js
// js32b-32g-iserror-node.js
// Error.isError(ES2026) 가 이 node 판에 있나 -- 그리고 다른 realm 에서 만든 오류를 무엇으로 가리나.
const vm = require("node:vm");
const util = require("node:util");
const row = (label, v) => console.log("  " + label.padEnd(44) + v);

row("typeof Error.isError", typeof Error.isError);
try { Error.isError(new Error("x")); } catch (e) { row("Error.isError(new Error('x'))", e.constructor.name + " 「" + e.message + "」"); }

const other = vm.runInNewContext("new TypeError('from another realm')");
row("other instanceof Error", other instanceof Error);
row("other instanceof TypeError", other instanceof TypeError);
row("other.constructor === TypeError", other.constructor === TypeError);
row("Object.prototype.toString.call(other)", Object.prototype.toString.call(other));
row("util.types.isNativeError(other)  (host)", util.types.isNativeError(other));
row("other.name / other.message", other.name + " / " + other.message);
```

```text
===== node20 js32b-32g-iserror-node.js (exit=0) =====
  typeof Error.isError                        undefined
  Error.isError(new Error('x'))               TypeError 「Error.isError is not a function」
  other instanceof Error                      false
  other instanceof TypeError                  false
  other.constructor === TypeError             false
  Object.prototype.toString.call(other)       [object Error]
  util.types.isNativeError(other)  (host)     true
  other.name / other.message                  TypeError / from another realm
```

```js
// js32b-32h-iserror.web.js
// Error.isError(ES2026) -- 무엇을 오류로 보나. 다른 realm(iframe)에서 만든 오류 · 흉내 낸 객체 · Proxy · 호스트의 DOMException.
const row = (label, v) => console.log("  " + label.padEnd(50) + v);
const frame = document.createElement("iframe");
document.body.appendChild(frame);
const W = frame.contentWindow;

console.log("[1] one question, three ways to ask it");
const cands = [
  ["new Error('x')", new Error("x")],
  ["new (class E2 extends Error {})()", new (class E2 extends Error {})()],
  ["new AggregateError([])", new AggregateError([])],
  ["iframe: new W.TypeError('x')", new W.TypeError("x")],
  ["Object.create(Error.prototype)", Object.create(Error.prototype)],
  ["{ name: 'Error', message: 'x' }", { name: "Error", message: "x" }],
  ["{ [Symbol.toStringTag]: 'Error' }", { [Symbol.toStringTag]: "Error" }],
  ["new Proxy(new Error('x'), {})", new Proxy(new Error("x"), {})],
  ["new DOMException('x')  (host)", new DOMException("x")],
];
console.log("  " + "".padEnd(50) + "Error.isError  instanceof Error  toString");
for (const [label, v] of cands) {
  row(label, String(Error.isError(v)).padEnd(15) + String(v instanceof Error).padEnd(18) + Object.prototype.toString.call(v));
}

console.log("[2] non-objects");
row("Error.isError('Error: x') / (null) / ()", Error.isError("Error: x") + " / " + Error.isError(null) + " / " + Error.isError());

console.log("[3] where stack lives on a real Error (this V8)");
const e = new Error("m");
const d = Object.getOwnPropertyDescriptor(e, "stack");
row("hasOwn(e, 'stack')", Object.hasOwn(e, "stack"));
row("descriptor kind", d ? ("value" in d ? "data" : "accessor") + ", enumerable " + d.enumerable : "(none)");
row("'stack' in Error.prototype", "stack" in Error.prototype);
row("first line of e.stack", JSON.stringify(e.stack.split("\n")[0]));
```

```text
===== google-chrome --headless --virtual-time-budget=2000 --dump-dom 'js32b-page.html?js32b-32h-iserror.web.js' | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' | sed 's/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&amp;/\&/g' (exit=0) =====
[1] one question, three ways to ask it
                                                    Error.isError  instanceof Error  toString
  new Error('x')                                    true           true              [object Error]
  new (class E2 extends Error {})()                 true           true              [object Error]
  new AggregateError([])                            true           true              [object Error]
  iframe: new W.TypeError('x')                      true           false             [object Error]
  Object.create(Error.prototype)                    false          true              [object Object]
  { name: 'Error', message: 'x' }                   false          false             [object Object]
  { [Symbol.toStringTag]: 'Error' }                 false          false             [object Error]
  new Proxy(new Error('x'), {})                     false          true              [object Object]
  new DOMException('x')  (host)                     true           true              [object DOMException]
[2] non-objects
  Error.isError('Error: x') / (null) / ()           false / false / false
[3] where stack lives on a real Error (this V8)
  hasOwn(e, 'stack')                                true
  descriptor kind                                   accessor, enumerable false
  'stack' in Error.prototype                        false
  first line of e.stack                             "Error: m"
```

```text
   Error.isError(v)                    v instanceof Error
   ① v 가 객체가 아니면 false           v 의 프로토타입 사슬에 「이 realm 의」 Error.prototype 이 있나
   ② [[ErrorData]] 슬롯이 없으면 false
   ③ true                              → 다른 realm 의 오류: 사슬에 「그쪽」 Error.prototype 뿐 → false
                                       → Object.create(Error.prototype): 슬롯은 없는데 사슬에 있다 → true
   → realm 을 안 본다. 사슬도 안 본다.
```

- ★★★ **다른 realm 에서 만든 오류는 `instanceof Error` 가 `false`, `Error.isError` 는 `true`** 다 — node `vm` 에서도(`other instanceof Error false`), Chrome iframe 에서도(`iframe: new W.TypeError('x')` 행) 같았다.
  ★ node 의 `util.types.isNativeError(other)` 는 `true` — **같은 질문을 호스트 함수로 물은 답**이다(제5의 상태). `constructor === TypeError` 도 `false` 다 — **생성자부터 다른 물건**이다.
- ★★★ **`[1]` 앞의 두 열(`Error.isError` · `instanceof Error`)이 갈린 행은 셋**이다 — 다른 realm(`true`/`false`), `Object.create(Error.prototype)`(`false`/`true`), `Proxy`(`false`/`true`). 나머지 여섯 행은 같다.
  ★★ **`Proxy` 는 `Error.isError` 가 `false`** 다 — `[[ErrorData]]` 는 **대상에 있지 프록시에 없다.** 34번의 `Array.isArray` 는 **프록시를 뚫고 대상을 본다**(명세의 `IsArray`) — **이름이 닮은 두 함수가 여기서 갈린다.**
- ★★ **흉내 둘은 둘 다 `false`** 다 — `{ name, message }` 도, `Symbol.toStringTag` 로 **브랜드를 `[object Error]` 로 위조한 것**도([22번](../22-symbol-and-well-known-symbols/2-summary.md)의 위조가 `Error.isError` 에는 안 통한다).
- ★★ **`DOMException` 은 `true`** 다(`instanceof Error` 도 `true`). **호스트 객체**라 ECMA-262 가 답을 정하지 않는다 — Chrome 151 의 관찰이다.
- ★ **`[3]` Chrome 151 의 `stack` 은 own 접근자**다 — node 20 은 데이터였다(동작 (6)). **명세 밖의 칸은 판마다 모양이 바뀐다.**

### (8) ★★ 파이썬·자바와의 대비 — `finally` 의 `return` · 바꿔치기의 흔적 · 원인 사슬

**언제 쓰나** — 다른 언어에서 오류 처리 관용구를 옮겨 올 때 「같은 모양이 같은 뜻인가」를 볼 때.

```sh
# js32b-32f-python-contrast.sh
#!/usr/bin/env bash
# 파이썬과 같은 질문 -- 이 머신의 파이썬 판들, 그리고 finally 의 return 에 경고가 나는가(-W error 로 경고를 예외로 올린다).
set -u -o pipefail
for p in python3.14 python3.13 python3.12 python3.11; do
  if command -v "$p" >/dev/null; then echo "$p: $("$p" --version)"; else echo "$p: not found"; fi
done
echo "--- python3.12 -W error - < js32b-32-h-pyerr.py"
python3.12 -W error - < js32b-32-h-pyerr.py 2>&1
echo "(exit $?)"
```

```python
# js32b-32-h-pyerr.py
# 같은 질문을 파이썬 3 에 -- raise ... from 의 사슬 · finally 가 예외를 바꿔치기할 때 남는 것 · finally 의 return.
def name(e):
    return type(e).__name__ + " 「" + str(e) + "」"

print("[1] raise ... from e -- walk __cause__ to the end")
def read_config():
    raise SyntaxError("Unexpected token } in config.json")
def load_settings():
    try:
        read_config()
    except SyntaxError as e:
        raise RuntimeError("settings could not be loaded") from e
def start_app():
    try:
        load_settings()
    except RuntimeError as e:
        raise TypeError("app failed to start") from e
try:
    start_app()
except TypeError as top:
    e, depth = top, 0
    while e is not None:
        print("  " + "  " * depth + "depth", depth, name(e))
        e, depth = e.__cause__, depth + 1

print("[2] finally raises while another exception is in flight")
try:
    try:
        raise ValueError("T")
    finally:
        raise KeyError("F")
except KeyError as caught:
    print("  caught        ", name(caught))
    print("  __cause__     ", caught.__cause__)
    print("  __context__   ", name(caught.__context__))

print("[3] return inside finally, with an exception in flight")
def swallow():
    try:
        raise ValueError("T")
    finally:
        return "F"
print("  swallow() ->", repr(swallow()))
```

```text
===== ./js32b-32f-python-contrast.sh (exit=0) =====
python3.14: not found
python3.13: not found
python3.12: Python 3.12.3
python3.11: Python 3.11.15
--- python3.12 -W error - < js32b-32-h-pyerr.py
[1] raise ... from e -- walk __cause__ to the end
  depth 0 TypeError 「app failed to start」
    depth 1 RuntimeError 「settings could not be loaded」
      depth 2 SyntaxError 「Unexpected token } in config.json」
[2] finally raises while another exception is in flight
  caught         KeyError 「'F'」
  __cause__      None
  __context__    ValueError 「T」
[3] return inside finally, with an exception in flight
  swallow() -> 'F'
(exit 0)
```

```text
   같은 질문, 세 언어의 답

                          JS                        Python 3.12               Java (25번 편)
   원인 잇기               new E(m, { cause: e })    raise E(m) from e         new E(m, e)  (getCause)
   finally 의 return       삼킨다 · 경고 없음         삼킨다 · 경고 없음(3.12)   삼킨다 · javac -Xlint 경고
   finally 가 던지면        흔적 없음                  __context__ 에 자동 연결    getCause null · suppressed 0
   여러 오류 한 봉투        AggregateError            ExceptionGroup            (없음)
```

- ★★★ **원인 사슬은 세 언어가 같은 모양**이다 — 파이썬 `[1]` 도 **`TypeError` → `RuntimeError` → `SyntaxError`** 세 층을 `__cause__` 로 걸었다.
- ★★★ **바꿔치기의 흔적이 다르다** — 파이썬 `[2]` 는 `__cause__` 가 `None` 인데 **`__context__` 에 `ValueError 「T」` 가 자동으로** 남았다. JS 는 동작 (2)의 `[4]` 에서 **아무것도 없었다.**
- ★★ **`finally` 의 `return` 은 파이썬도 삼킨다**(`swallow() -> 'F'`). **`-W error` 로 경고를 예외로 올려도 3.12 는 조용했다**(`exit 0`).
  ★★ **파이썬 3.14 에서는 경고가 난다고 알려져 있다(PEP 765) — 이 머신에는 3.14 가 없어 못 쟀다**(판 목록 블록의 `python3.14: not found` — 제3의 상태). 파이썬 쪽 정본은 [Python 25](../../../python/syntax/25-exceptions-and-finally/2-summary.md)다.
- ★★ **자바는 컴파일러가 경고한다** — `javac -Xlint` 의 `finally clause cannot complete normally`. 바꿔치기 뒤 `getCause = null / suppressed 개수 = 0` 도 거기서 쟀다([Java 25](../../../java/syntax/25-exceptions/2-summary.md) 동작 (5)). **JS 는 엔진도 도구도 이 자리를 안 알려 준다** — 린터(ESLint `no-unsafe-finally`)의 몫이다(이 문서는 린터를 돌리지 않았다).

## 문법 — 형태와 규칙

★ 이 절은 **형태 표**다 — 모든 동작 주장은 위 동작 절의 캡처 블록에서만 한다(규칙 28 — 돌리지 않은 코드 펜스를 싣지 않는다).

| 형태 | 하는 일 | 판 | 어디서 봤나 |
|---|---|---|---|
| `throw 식` | **아무 값이나** 던진다 — `Error` 가 아니면 `stack` 이 없다 | ES3 | 동작 (6) |
| `try { } catch (e) { } finally { }` | `catch` 가 먼저, `finally` 가 나중 — `finally` 가 끝을 쥐면 앞의 완료를 버린다 | ES3 | 동작 (1)·(2) |
| `catch { }` | 받은 값을 안 쓸 때 바인딩 생략 | ES2019 | 판별 블록 |
| `new Error(message, { cause })` | 비열거 own `cause` — 옵션에 **키가 있을 때만** | **ES2022** | 동작 (4) |
| `new AggregateError(iterable, message, { cause })` | 이터러블을 **복사한** `errors` 배열 | **ES2021** | 동작 (5) |
| `Error.isError(v)` | `[[ErrorData]]` 슬롯이 있나 — realm·사슬·프록시 무관 | **ES2026** | 동작 (7) — Chrome 만 |
| `e.stack` · `Error.captureStackTrace(o)` | 호출 경로 글자 — **ECMA-262 밖**(V8) | — | 동작 (6) |

- **`finally` 가 조용하면** `try`(또는 `catch`)의 완료가 나간다. **`finally` 가 `return`·`throw`·`break`·`continue` 로 끝나면 그것이 나간다.**
- **원인은 손으로 잇는다** — `catch (e) { throw new X("…", { cause: e }); }`. 바꿔치기에는 자동 연결이 없다.
- **자기 오류 클래스는 `name` 을 직접 넣는다** — `this.name = new.target.name`.

## 어디서 틀리나

### (1) ★★★ `finally` 에 `return` 을 넣는다

**`try` 의 예외가 사라진다**(동작 (1)의 `throw E('T') × return 'F'` 칸 — 호출자는 `value "F"`). 정리 코드는 `finally` 에, **반환은 `try` 안에서만** 한다.

### (2) ★★★ `finally` 에서 정리 중 던진 예외가 원래 예외 옆에 남을 것이라 믿는다

**원래 예외는 흔적 없이 사라진다**(동작 (2)의 `[4]` — `'cause' in caught false`). 정리 코드가 던질 수 있으면 `finally` 안에서 **따로 `try`/`catch`** 로 감싼다.

### (3) ★★★ 루프 안 `finally { continue; }` 로 「어쨌든 다음 차례로」를 쓴다

**예외를 매번 삼킨다**(동작 (2)의 `n=3`). 실패를 셀 방법도 사라진다.

### (4) ★★ `return x` 뒤 `finally` 에서 `x` 를 고치면 반환값이 바뀐다고 믿는다

**원시값이면 안 바뀐다**(`value 1`) — 값은 `finally` 전에 정해진다. **객체면 바뀐 것이 보인다**(같은 객체다).

### (5) ★★★ 오류를 감싸 다시 던지면서 원인이 이어질 것이라 믿는다

**`{ cause: e }` 를 안 넘기면 안 이어진다.** 파이썬의 `__context__` 같은 자동 연결이 없다(동작 (8)).

### (6) ★★ `class MyError extends Error {}` 의 `name` 이 `"MyError"` 일 것이라 믿는다

**`"Error"`** 다(동작 (3)의 `[3]`). `String(e)`·로그가 전부 `Error: …` 로 나온다. `this.name = new.target.name`.

### (7) ★★ `catch (e)` 에서 `e.message`·`e.stack` 을 무조건 읽는다

`throw "문자열"` 이면 둘 다 **`undefined`**, `throw null` 이면 **읽는 순간 `TypeError`** 다(동작 (6)). 로그 코드는 `e instanceof Error` 가 아니라 **값의 종류부터** 본다.

### (8) ★★ `e instanceof Error` 로 「오류인가」를 가른다

**다른 realm 의 오류에서 `false`** 다(동작 (7)). ES2026 이 되는 곳이면 `Error.isError`, 아니면 34번의 판정 방법을 쓴다.

### (9) ★★ `e.stack` 의 모양에 기대 파싱한다

**`stack` 은 명세 밖**이다 — node 20 과 Chrome 151 에서 **프로퍼티 종류부터 다르다**(데이터 대 접근자). 글자 모양은 더 자주 바뀐다.

### (10) ★ `JSON.stringify(err)` 로 오류를 로그에 남긴다

**`{}`** 다(동작 (4)의 `[2]`) — `message`·`stack`·`cause` 가 전부 비열거다. 필요한 칸을 골라 직접 담는다.

## 구현 세부사항 대 언어 보장

### 명세 보장 — 어느 엔진에서도 같아야 하는 것

- ★★★ `TryStatement` 의 평가 — **`finally` 의 완료가 정상이면 앞(`try` 또는 `catch`)의 완료를 되살리고, 아니면 `finally` 의 완료가 나간다.** 동작 (1)의 9칸이 전부 여기서 나온다.
- ★★★ `return 식` 은 **식을 먼저 평가해 완료 기록에 담는다** — `finally` 는 그 뒤에 돈다.
- ★★ `InstallErrorCause` — 옵션이 객체이고 **`HasProperty(options, "cause")` 가 참일 때만** `Get` 해서 **비열거** own `cause` 를 만든다.
- ★★ `AggregateError` — 이터러블을 `IteratorToList` 로 **복사해** 비열거 `errors` 배열을 만든다.
- ★★ `Error.isError` — **객체이고 `[[ErrorData]]` 슬롯이 있으면 `true`.** 프록시·realm·사슬을 보지 않는다.
- 언어가 스스로 던지는 **오류의 종류**(`TypeError`·`RangeError`·`SyntaxError`·`ReferenceError`·`URIError`) · 일곱 하위 생성자의 부모가 `Error` 인 것 · 브랜드가 `[object Error]` 인 것.

### 엔진(V8) 구현 · 이 판의 관찰

- ★★★ **`stack` 전부** — 있는지, 어디에 붙는지(node 20 은 own 데이터 · Chrome 151 은 own 접근자), 글자 모양. `Error.captureStackTrace` · `Error.stackTraceLimit`.
- 예외 **문구 전부** — `Cannot read properties of null (reading 'stack')` · `All promises were rejected` 등.
- 이 주제 node 탐침이 두 판에서 **한 글자도 같았다**는 것 — 관찰이다.

### 호스트가 정하는 것 — ECMA-262 밖

- ★★ **다른 realm 을 만드는 법** — node 의 `vm.runInNewContext`, 브라우저의 iframe. 둘이 같은 답을 냈지만 `vm` 이 명세의 realm 과 같은 것인지는 **이 문서가 확인하지 않았다**(22번과 같은 단서).
- ★★ **`util.types.isNativeError`**(node) · **`DOMException`**(웹) — 호스트의 것이다.
- ★★ **아무도 안 받은 `throw` 를 어떻게 적나**(동작 (6)의 표준 오류 블록) — node 의 것이다.

### 그래서 이렇게 적으면 틀린다

- ✗ 「`finally` 는 예외를 막지 못한다(예외는 항상 올라간다)」 → ○ 「**`finally` 가 `return`·`throw`·`break`·`continue` 로 끝나면** 예외가 사라지거나 바뀐다 — 9칸 중 **6칸**에서 `try` 의 끝이 안 닿았다」
- ✗ 「새 오류를 던지면 원래 오류는 `cause` 로 남는다」 → ○ 「**손으로 `{ cause: e }` 를 넘길 때만**」
- ✗ 「`stack` 은 표준 프로퍼티다」 → ○ 「**ECMA-262 에 없다** — V8 의 것이고 판마다 모양이 다르다」
- ✗ 「`Error.isError` 는 ES2025」 → ○ 「**ES2026** — finished proposals 의 `Error.isError` 가 2026 이다」
- ✗ 「`try`/`catch` 는 느리다」 → ○ **안 쟀다**

## 언제 쓰고 언제 안 쓰나

- **`finally`** — 자원 정리·잠금 해제·타이머 정리. **`return`·`throw`·`break`·`continue` 를 넣지 않는다.** 정리가 던질 수 있으면 `finally` 안에서 따로 잡는다.
- **`cause`** — 아래층 오류를 **뜻 있는 오류로 감쌀 때마다.** 사슬을 걷는 코드는 **`seen` 집합**과 **`Error` 가 아닌 `cause`** 를 같이 다룬다.
- **`AggregateError`** — 여러 독립 작업의 실패를 **한 번에** 보고할 때. `Promise.any` 는 이미 이것으로 거부한다.
- **자기 오류 클래스** — `catch` 에서 **종류로 갈라야** 할 때만. 만들면 `this.name = new.target.name`.
- **`Error.isError`** — ES2026 이 되는 런타임에서 **realm 을 넘어온 값**을 가를 때(이 머신의 node 두 판에는 없다).
- ★ **안 쓰는 자리** — **`throw "문자열"`**(`stack` 이 없다 — 동작 (6)의 node 안내 문구가 그 증거) · **`finally` 로 흐름 바꾸기**.

## 핵심 문장

1. ★★★ `finally` 는 어느 길로 나가도 돌지만, **`finally` 가 `return`·`throw`·`break`·`continue` 로 끝나면 `try`(와 `catch`)의 끝을 버린다** — 9칸 격자에서 **`6 / 9`** 칸이 그랬고, `try` 가 던진 행은 **`2 / 3`** 에서 예외가 사라졌다.
2. ★★★ 명세의 한 문장 — 「**`F` 가 정상 완료면 `F` 를 `B` 로 바꾼다**」. 예외를 삼키는 특별 규칙은 없다. 바꿔치기한 예외에는 **원래 예외의 흔적이 없다**(파이썬은 `__context__` 로 남긴다).
3. ★★★ `cause` 는 **옵션에 `cause` 키가 있을 때만**(`has` → `get`) 붙는 **비열거 own 프로퍼티**다. 언어는 사슬을 자동으로 잇지 않는다 — `.cause` 를 `undefined` 까지 걸어 층을 본다.
4. ★★ `throw` 는 아무 값이나 던지고, **`stack` 은 `Error` 에만 있으며 ECMA-262 밖**이다 — node 20 은 데이터, Chrome 151 은 접근자였다.
5. ★★★ 다른 realm 의 오류는 **`instanceof Error` 가 `false`, `Error.isError`(ES2026) 는 `true`** 다 — node `vm` 과 Chrome iframe 이 같은 답을 냈다. 프록시는 반대로 `Error.isError` 가 `false`.

## 관련 자료

- [ECMA-262 — The `try` Statement](https://tc39.es/ecma262/multipage/ecmascript-language-statements-and-declarations.html#sec-try-statement) · [Error Objects](https://tc39.es/ecma262/multipage/fundamental-objects.html#sec-error-objects)
- [TC39 finished proposals](https://github.com/tc39/proposals/blob/main/finished-proposals.md) — 판 경계
- [20 — 제너레이터](../20-generators/2-summary.md) — ★ **경계**: 그쪽은 **`g.return()` 이 `finally` 를 돌리고 `finally` 의 `yield` 가 그것을 멈추는 것**까지, 여기는 **평범한 함수의 `finally` 가 끝을 쥐는 9칸**부터.
- [19 — 이터러블 프로토콜과 `for...of`](../19-iterable-protocol-and-for-of/2-summary.md) · [21 — 이터레이터 헬퍼](../21-iterator-helpers/2-summary.md) — 예외가 이터레이터를 **닫는** 자리.
- [31 — `JSON`](../31-json/2-summary.md) — 순환 참조 `TypeError` 의 여러 줄 문구(V8 의 것) · 비열거 프로퍼티가 `stringify` 에서 빠지는 규칙.
- [34 — 타입 검사 관용구](../34-type-checking-idioms/2-summary.md) — ★ **경계**: 그쪽이 **realm·프로토타입 조작에서 어느 판정이 깨지나**의 정본, 여기는 **`Error.isError` 한 함수**.
- 목록의 **37번 주제**(Promise 상태 모델) · 목록의 **39번 주제**(`async`/`await`) — 비동기 오류의 정본. 목록의 **51번 주제**(`using`) — 자원 정리와 `SuppressedError`.
- [Go 24 — 오류 래핑 `%w` 와 `errors.Is`/`As`/`Join`](../../../go/syntax/24-error-wrapping-and-errors-is-as-join/2-summary.md) — 사슬 걷기 창의 정본.
- [Python 25 — 예외와 `finally`](../../../python/syntax/25-exceptions-and-finally/2-summary.md) · [Python 27 — 예외 그룹과 `except*`](../../../python/syntax/27-exception-groups-and-except-star/2-summary.md) · [Java 25 — 예외](../../../java/syntax/25-exceptions/2-summary.md).

## 용어 풀이

- **완료 기록(completion record)** — 문장이 어떻게 끝났나(정상·`return`·`throw`·`break`·`continue`)와 그 값을 담는 명세의 값.
- **비정상 완료(abrupt completion)** — 정상이 아닌 네 종류. `finally` 가 이것으로 끝나면 앞의 완료를 버린다.
- **삼킴 / 바꿔치기** — 이 문서의 말. `finally` 의 `return` 이 예외를 없애는 것 / `finally` 의 `throw` 가 예외를 다른 예외로 갈아 끼우는 것.
- **`cause`** — 이 오류의 원인인 앞선 오류(ES2022). 옵션 `{ cause }` 로만 붙는다.
- **`InstallErrorCause`** — 옵션에 `cause` 가 있으면 비열거 own `cause` 를 만드는 명세 연산.
- **`AggregateError`** — 여러 오류를 `errors` 배열로 드는 오류(ES2021).
- **`[[ErrorData]]`** — `Error` 생성자가 만든 객체에만 있는 내부 슬롯. `Error.isError` 와 브랜드 태그 `[object Error]` 가 이것을 본다.
- **realm** — 전역 객체와 내장 객체 한 벌. iframe·`vm` 컨텍스트가 각자 갖는다. 그래서 `Error` 생성자도 realm 마다 따로다.
- **`stack`** — 호출 경로를 적은 글자. **ECMA-262 밖**, V8 이 붙인다.
- **`__context__` / `__cause__`** — 파이썬의 자동 연결 / 명시 연결(`raise … from`).

## 더 들어가면

- **`SuppressedError` 와 `using`** — 정리 중 던진 예외가 원래 예외를 **덮지 않고 함께** 담기는 장치. 목록의 **51번 주제**의 몫이다(이 문서는 돌리지 않았다).
- **`Error.captureStackTrace` 의 표준화** — 지금은 V8 등의 확장이다. 이 문서는 **node 20 의 모양 하나**만 봤다.
- **린터** — ESLint `no-unsafe-finally` 가 동작 (1)의 여섯 칸을 잡는다고 알려져 있다. **이 문서는 돌리지 않았다.**
