# js/syntax/42 — ESM 모듈: 「`import` 는 값이 아니라 이름을 빌려 온다 — 실행 전에 연결되고, 순환에서는 『아직 초기화 전』이 보인다」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> ★★★ **이 주제의 본체는 ② 전수 격자다** — `a.mjs` ↔ `b.mjs` 순환에서 **`a` 가 내보내는 모양 8가지 × `main` 이 가져오는 순서 2 × `b` 가 읽는 때 2 = 32칸**을 칸마다 **새 디렉토리 · 새 프로세스**로 돌리고, 마지막 줄에 「**`"A"` 를 못 읽은 칸 N / M**」을 스크립트가 찍는다(동작 (3)).
> ★★ 보조로 **① 추상 연산에 로그 심기**(모듈 본문의 첫 줄 · `import` 뒤의 줄 · 평가 순서 — 동작 (4)) · **③ 브랜드 태그**(모듈 이름공간 객체의 `[object Module]` — 동작 (2)) · **④ 예외의 `constructor.name` + `message`**(가져온 이름에 대입 → `TypeError` · 연결 단계의 `SyntaxError` — 동작 (2)·(5))를 쓴다.
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262 — Source Text Module Records · `InitializeEnvironment`](https://tc39.es/ecma262/multipage/ecmascript-language-scripts-and-modules.html) — 「가져온 이름마다 `ResolveExport` → **null 이거나 모호하면 `SyntaxError`** → `CreateImportBinding`」 · 「`var` 이름은 `CreateMutableBinding` + **`InitializeBinding(name, undefined)`**」 · 「렉시컬 선언은 바인딩만 만들고, **함수 선언이면 `InstantiateFunctionObject` 로 곧바로 초기화**한다」
> - [ECMA-262 — `CreateImportBinding`](https://tc39.es/ecma262/multipage/executable-code-and-execution-contexts.html) — 「**초기화된 불변 간접 바인딩**을 만든다 … 새 바인딩의 값에 접근하면 **대상 바인딩의 값을 간접으로** 읽는다」
> - [TC39 finished proposals](https://github.com/tc39/proposals/blob/main/finished-proposals.md) — 판 경계(`import()` **2020** · `import.meta` **2020** · Top-level `await` **2022**). `import`/`export` 문 자체는 **ES2015 본문**이다(제안 표에 없다).
> - [Node.js v20 — Modules: Packages · 「Determining module system」](https://nodejs.org/docs/latest-v20.x/api/packages.html) — 「`.mjs` · `"type": "module"` 인 `.js` · `--input-type=module` 은 ES 모듈」
>
> ★★★ **명세 조항 번호는 인용하지 않는다.** 규칙 진술은 **추상 연산 이름**으로, 순서·값·예외는 **전부 실행으로** 접지했다.
>
> **실행 검증** — 이 문서의 모든 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다.
> 배너의 `node20` 은 `~/.nvm/versions/node/v20.19.6/bin/node`, `node18` 은 기본 PATH 의 `node`(v18.19.1)다. `cd <디렉토리> && node20 <파일>` 꼴 배너는 **그 디렉토리 안에서 상대 경로로** 던졌다.
> ★★★ **ES 모듈은 `file://` 페이지에서 CORS 로 막힌다 — Chrome 151 은 로컬 HTTP 서버로 띄웠다**(아래 하네스의 `--http` · `js40b-serve.py`). 이 묶음(40\~43)의 Chrome 블록은 전부 이 하네스에서 나왔다.
> ★★ **node 의 에러에는 파일의 절대 경로가 박힌다** — 그 블록은 스크립트 안에서 **`sed "s#$PWD#<dir>#g"`** 로 지웠다(소스에 그 줄이 보인다).
> ★★★ **성능은 재지 않았다** — 「ESM 이 빠르다」·「트리 셰이킹으로 작아진다」를 **쓰지 않는다.**
>
> **버전**
>
> | 무엇 | 판 | 이 머신에서 |
> |---|---|---|
> | `import`/`export` 문 · 라이브 바인딩 · 모듈은 늘 엄격 | **ES2015** | 세 판 다 |
> | 동적 `import()` | **ES2020** | 세 판 다(판별 블록 · 동작 (5)) |
> | `import.meta` | **ES2020** | 세 판 다 — 그 **속성**은 호스트가 채운다(43번) |
> | 최상위 `await` | **ES2022** | 39번 동작 (7) |
>
> ★★ **판 경계는 TC39 finished proposals 표와 이 목록의 README 를 대조했다.** README 42행은 판을 적지 않는다.
>
> **★★★ 이 주제가 쓰는 창 — 그리고 부적용인 창**
>
> | 창 | 이 주제에서 무엇을 보나 |
> |---|---|
> | ★★★ **② 전수 격자**(본체) | 순환 32칸 — `A` / `undefined` / `ReferenceError` · 마지막 줄 「`did not read "A": N / 32`」(동작 (3)) |
> | ★★ **① 추상 연산에 로그 심기** | 모듈 본문의 첫 줄 · `import` 뒤의 줄 · 여러 모듈의 평가 순서(동작 (4)) · 라이브 바인딩의 전후 값(동작 (1)) |
> | ★★ **③ 브랜드 태그** | 이름공간 객체 — `Object.prototype.toString` 이 `[object Module]` · 프로토타입 `null` · 확장 불가(동작 (2)) |
> | ★★ **④ 예외의 `constructor.name` + `message`** | 가져온 이름에 대입 → `TypeError` · 블록 안 `import` · 없는 이름 `import` → `SyntaxError`(동작 (2)·(5)) |
> | ★ **안 쟀다 — 성능·번들 크기** | 정적 구조가 **도구에게** 무엇을 허락하나는 연혁 문서의 몫이다. 이 문서는 **실행이 보이는 것**만 적는다 |
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 판별 블록의 판 문자열 · 에러 첫 줄의 **절대 경로**(블록 안에서 `<dir>` 로 지웠다) | ★★★ 격자의 모든 칸 · 로그의 **줄 순서** · 종료 코드 · `standard output had N lines` · 에러의 **종류와 문구** |
> | ★ **이 주제의 탐침에는 재실행에서 흔들린 칸이 없다**(재대조 동일) | ★★ **판 사이의 문구 차이**(Chrome 의 `Cannot assign to property …`)는 흔들림이 아니라 **판의 차이**다 |
>
> **층** — `import`/`export` 의 **연결(Link)·평가(Evaluate)·바인딩 규칙**은 **언어(ECMA-262)** 다. **「이 글자가 어느 파일인가」(모듈 지정자 해석)·「어느 파일이 모듈인가」·파일을 읽어 오는 일은 호스트**(HTML · node)다 — 명세의 `HostLoadImportedModule` 이 그 문이다. CommonJS 는 **명세 밖**이다(43번).
>
> **선행** — [35 — 엄격 모드](../35-strict-mode/2-summary.md)(직접 선행 — ★★★ **모듈은 늘 엄격**을 **`.mjs` 로 증명**했다 — 여기서 가져온 이름에 대입하면 `TypeError` 인 것이 그 엄격함 위에 선다) ·
> [05 — `var`·`let`·`const` 와 TDZ](../05-var-let-const-and-tdz/2-summary.md)(★★★ **순환에서의 `ReferenceError` 는 TDZ 다** — 「줄이 아니라 시간」이 모듈 사이로 넓어진 것) ·
> [36 — 이벤트 루프](../36-event-loop-and-microtasks/2-summary.md)(★★ **같은 파일이 ES 모듈이면 `nextTick` 이 4위에서 9위로** — 모듈 본문이 「이미 마이크로태스크를 비우는 중」에 돈다) ·
> [39 — `async`/`await`](../39-async-await/2-summary.md)(최상위 `await` 는 **모듈 코드인가**가 기준 — 확장자가 아니다).
>
> ★★★ **파이썬 42번과 나란히** — [Python 42 — 모듈·패키지·import](../../../python/syntax/42-modules-packages-and-import/2-summary.md)가 **순환 import 격자 `깨진 칸 7 / 24`** 를 쟀고, 그 편 7절이 node 18 로 **ESM 은 `ReferenceError: Cannot access 'TAG' before initialization`, CommonJS 는 조용히 `f>g>undefined` + 경고 한 줄**을 이미 던졌다. 여기서는 **그 JS 쪽을 격자로 전면에** 세운다(동작 (3)). **Go 는 순환 import 가 빌드에서 거부된다**([Go 01](../../../go/syntax/01-packages-imports-main-and-init/2-summary.md) — 파이썬 42번 7절의 `import cycle not allowed`).
>
> ★★ **경계 — 연혁**(CommonJS·AMD 에서 ESM 표준으로)은 [`history/js/02-ES6-모던.md`](../../../../../../history/js/02-ES6-모던.md) 의 **「모듈 (import / export)」** 절이 정본이다. 그 절은 「**정적 구조라 빌드 도구가 트리 셰이킹을 할 수 있다**」를 원문의 인과로 적는다 — 이 문서는 **그 정적 구조가 실행에서 어떻게 보이나**(블록 안 `import` 는 문법 오류 · 없는 이름은 **본문이 한 줄도 돌기 전에** 막힌다)부터 쓰고, 크기·속도는 **재지 않았다.**
> ★ **CommonJS 와 ESM 이 서로 부르는 것**은 [43번](../43-cjs-and-esm-interop/2-summary.md), **동적 `import`·최상위 `await` 의 평가 순서·import attributes** 는 목록의 **44번 주제**다.

**이 묶음(40\~43)의 Chrome 하네스** — 페이지 하나 · 셸 하나 · 로컬 서버 하나.

```html
<!-- js40b-page.html -->
<!doctype html>
<meta charset="utf-8">
<title>js40b</title>
<pre id="o"></pre>
<script>
// Runs the probe scripts named after "?" in the address (comma-separated, in that order).
// A name ending in .mjs is loaded as a module script (<script type="module">), the rest as classic scripts.
// console.log is replaced: every call appends a line and rewrites <pre>, so lines printed
// after promises and timers are present when --dump-dom writes the page out.
const __lines = [];
const __render = () => {
  document.getElementById("o").textContent = "==" + "=OUT===\n" + __lines.join("\n") + "\n===END" + "===";
};
console.log = (...a) => { __lines.push(a.join(" ")); __render(); };
window.addEventListener("error", (e) => { __lines.push("uncaught " + e.message); __render(); });
window.addEventListener("unhandledrejection", (e) => { __lines.push("unhandledrejection " + String(e.reason && e.reason.message)); __render(); });
__render();
for (const f of location.search.slice(1).split(",")) {
  const t = f.endsWith(".mjs") ? ' type="module"' : "";
  document.write('<script' + t + ' src="' + f + '"><\/script>');
}
</script>
```

```sh
# js40b-browser.sh
#!/usr/bin/env bash
# Run probe scripts in headless Chrome and print what they logged.
#   usage: ./js40b-browser.sh [--http] <script>[,<script>...]
# Default: file:// with --allow-file-access-from-files (without it a file:// script counts as cross-origin -- "muted errors").
# --http: through js40b-serve.py on 127.0.0.1 -- module scripts (.mjs) and fetch() need it.
# --dump-dom writes HTML entities, so the last sed turns them back.
set -u -o pipefail
cd "$(dirname "$0")"
if [ "$1" = "--http" ]; then
  shift
  pf="$(mktemp -p "$PWD" .port-XXXXXX)"
  python3 js40b-serve.py "$pf" > /dev/null 2>&1 &
  srv=$!
  for _ in $(seq 100); do [ -s "$pf" ] && break; sleep 0.05; done
  url="http://127.0.0.1:$(cat "$pf")/js40b-page.html?$1"
  rm -f "$pf"
else
  srv=
  url="file://$PWD/js40b-page.html?$1"
fi
google-chrome --headless --allow-file-access-from-files --virtual-time-budget=5000 --dump-dom "$url" 2>/dev/null \
  | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' \
  | sed 's/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&amp;/\&/g'
rc=$?
[ -n "$srv" ] && kill "$srv"
exit $rc
```

```python
# js40b-serve.py
# A local HTTP server for the Chrome harness: ES modules do not load from file:// (CORS).
# Serves this directory on 127.0.0.1 at a free port and writes the port to the file named in argv[1].
# /hang answers only after 2 seconds -- a request that is still in flight when a probe aborts it.
import http.server, os, sys, time

class H(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map, ".mjs": "text/javascript", ".js": "text/javascript"}
    def do_GET(self):
        if self.path.startswith("/hang"):
            time.sleep(2)
            self.send_response(200); self.send_header("Content-Length", "2"); self.end_headers(); self.wfile.write(b"ok")
            return
        super().do_GET()
    def log_message(self, *a):
        pass

os.chdir(os.path.dirname(os.path.abspath(__file__)))
s = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
s.daemon_threads = True
with open(sys.argv[1], "w") as f:
    f.write(str(s.server_address[1]))
s.serve_forever()
```

**판별 블록** — 같은 기능 표를 세 판에 던진다.

```js
// js40b-features.js
// Is each feature of this batch here? The same script goes to node18, node20 and Chrome.
// Syntax is asked through new Function, so a missing feature does not kill the whole script.
const has = (label, test) => {
  let r;
  try { r = test() ? "yes" : "no"; } catch (e) { r = "no (" + e.constructor.name + ")"; }
  console.log("  " + label.padEnd(50) + r);
};
const syntax = (src) => () => (new Function(src), true);
has("ES2018  async function* / for await", syntax("return async function* () { for await (const x of []) yield x; }"));
has("ES2018  Symbol.asyncIterator", () => typeof Symbol.asyncIterator === "symbol");
has("ES2020  import() in a classic script", syntax("return import('./nothing.mjs').catch(() => 0)"));
has("ES2026  Array.fromAsync", () => typeof Array.fromAsync === "function");
has("host    AbortController", () => typeof AbortController === "function");
has("host    AbortSignal.abort", () => typeof AbortSignal.abort === "function");
has("host    AbortSignal.timeout", () => typeof AbortSignal.timeout === "function");
has("host    AbortSignal.any", () => typeof AbortSignal.any === "function");
has("host    AbortSignal.prototype.throwIfAborted", () => typeof AbortSignal.prototype.throwIfAborted === "function");
has("host    DOMException", () => typeof DOMException === "function");
has("host    fetch", () => typeof fetch === "function");
has("host    require (this script's scope)", () => typeof require === "function");
```

```text
===== ./js40b-versions.sh (exit=0) =====
node 18.19.1  v8 10.2.154.26-node.28
  ES2018  async function* / for await               yes
  ES2018  Symbol.asyncIterator                      yes
  ES2020  import() in a classic script              yes
  ES2026  Array.fromAsync                           no
  host    AbortController                           yes
  host    AbortSignal.abort                         yes
  host    AbortSignal.timeout                       yes
  host    AbortSignal.any                           yes
  host    AbortSignal.prototype.throwIfAborted      yes
  host    DOMException                              yes
  host    fetch                                     yes
  host    require (this script's scope)             yes
node 20.19.6  v8 11.3.244.8-node.33
  ES2018  async function* / for await               yes
  ES2018  Symbol.asyncIterator                      yes
  ES2020  import() in a classic script              yes
  ES2026  Array.fromAsync                           no
  host    AbortController                           yes
  host    AbortSignal.abort                         yes
  host    AbortSignal.timeout                       yes
  host    AbortSignal.any                           yes
  host    AbortSignal.prototype.throwIfAborted      yes
  host    DOMException                              yes
  host    fetch                                     yes
  host    require (this script's scope)             yes
Google Chrome 151.0.7922.173
  ES2018  async function* / for await               yes
  ES2018  Symbol.asyncIterator                      yes
  ES2020  import() in a classic script              yes
  ES2026  Array.fromAsync                           yes
  host    AbortController                           yes
  host    AbortSignal.abort                         yes
  host    AbortSignal.timeout                       yes
  host    AbortSignal.any                           yes
  host    AbortSignal.prototype.throwIfAborted      yes
  host    DOMException                              yes
  host    fetch                                     yes
  host    require (this script's scope)             no
```

세 판 대조기의 집계 줄 — 전문은 [3-answer.md](3-answer.md) 의 「실행 검증」에 있다.

`node18 vs node20: identical 7 · differs 2   ·   node20 vs Chrome 151: identical 3 · differs 3 · node only 3`

## 한눈에 — 쉽게 말하면

**ESM 의 `import` 는 「이웃집 창문을 들여다보는 권리」다. 물건(값)을 복사해 오는 게 아니라 그 집 창문(바인딩)을 내 집에서 보게 연결한다. 이웃이 창가의 물건을 바꾸면 나도 바뀐 것을 본다(라이브 바인딩). 대신 내가 그 창문 너머에 손을 넣어 바꿀 수는 없다(대입하면 `TypeError`).**

- ★★★ **창문은 이사 오기 전에 뚫는다** — 모든 `import` 는 **어느 모듈의 본문도 돌기 전에** 연결된다. 없는 이름을 가져오면 **첫 줄도 안 돌고** `SyntaxError` 다.
- ★★★ **파일 중간에 적어도 먼저다** — `import` 문은 파일 어디에 있든 **그 파일의 본문보다 먼저** 상대 모듈을 돌린다.
- ★★★ **순환이면 이웃이 아직 이사 중일 수 있다** — 창문은 뚫렸는데 **물건이 아직 안 들어온** 상태를 보면 `ReferenceError`(TDZ). 단 **`function` 선언은 이사 전에 먼저 들여놓는다** — 순환에서도 쓸 수 있다.
- ★★ **CommonJS 는 창문이 아니라 사진이다** — `require` 로 받은 값은 **그때 찍은 사진**이라 이웃이 바꿔도 안 바뀐다(43번에서 자세히).

```text
   counter.mjs                                   main.mjs
   ┌──────────────────────────┐                  ┌───────────────────────────────┐
   │ export let n = 0;   ◀────┼──── 같은 칸 ─────┼── import { n } from ...        │
   │ export function inc(){   │                  │                               │
   │   n++;  ── 칸의 값을 바꾼다│                  │   n   → 0 → (inc 뒤) 1 → 2    │
   │ }                        │                  │   n = 5  → TypeError (읽기 전용)│
   └──────────────────────────┘                  └───────────────────────────────┘

   CommonJS:  module.exports = { n }   ──▶  그 순간의 0 을 담은 새 객체 ──▶ require 쪽은 끝까지 0
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 이웃집 창문 | **가져온 바인딩**(`CreateImportBinding` — 내 환경에 만든, 저쪽 바인딩을 가리키는 **불변 간접 바인딩**) | 동작 (1) |
| 창가의 물건이 바뀐다 | 내보낸 모듈이 `n++` — 가져온 쪽의 `n` 도 새 값 | 동작 (1)의 `after inc()` |
| 손을 넣을 수 없다 | 가져온 이름에 대입 → `TypeError` · 이름공간 객체 쓰기 → `TypeError` | 동작 (2) |
| 이사 전에 창문을 뚫는다 | **연결(Link)** 이 **평가(Evaluate)** 보다 먼저 — 없는 이름은 연결에서 `SyntaxError` | 동작 (5) |
| 이사 중인 이웃 | 순환에서 **아직 평가되지 않은** 모듈의 `let`/`const`/`class` → TDZ | 동작 (3) |
| 먼저 들여놓는 가구 | `function` 선언 — `InitializeEnvironment` 에서 곧바로 초기화 | 동작 (3) |
| 사진 | CommonJS `module.exports` 의 값 복사 | 동작 (1)의 CJS 블록 · 43번 |

**똑같은 구조다** — 실무에서 물리는 자리도 굳어 있다.
「**설정 모듈의 값을 바꿨는데 다른 파일에서 `const { x } = require(...)` 로 받은 쪽은 옛 값이었다**」,
「**`utils` 와 `models` 가 서로를 import 하자 `Cannot access 'X' before initialization`**」,
「**import 아래에 둔 초기화 코드가 import 한 모듈보다 먼저 돌 줄 알았다**」가 그것이다(동작 (1)·(3)·(4)).

> **라이브 바인딩(live binding)** — 가져온 이름이 **값의 복사가 아니라 내보낸 쪽 변수 그 자체를 가리키는** 것. 내보낸 쪽이 바꾸면 가져온 쪽도 새 값을 본다.\
> 예: `export let n = 0; export function inc() { n++; }` 를 가져와 `inc()` 한 뒤 `n` 을 읽으면 `1`.

## 이 주제가 답하려는 질문

1. **가져온 이름은 값인가 이름인가** — 내보낸 쪽이 바꾸면 보이나, 내가 대입하면 어떻게 되나, 이름공간 객체는 무엇인가?
2. **순환 의존에서 무엇이 `undefined` 이고 무엇이 `ReferenceError` 이고 무엇이 멀쩡한가** — 내보내는 모양 · 가져오는 순서 · 읽는 때에 따라?
3. **`import` 는 언제 도나** — 파일 중간의 `import` · 여러 모듈의 평가 순서 · 블록 안의 `import` · 없는 이름 · 동적 `import()` 는?

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 출력으로 읽는다.

### (1) ★★★ 라이브 바인딩 — 그리고 CommonJS 의 복사와 한 쌍

**언제 쓰나** — 모듈이 **상태**(카운터·설정·캐시)를 내보낼 때 · CommonJS 코드를 ESM 으로 옮길 때.
★★ 같은 카운터를 ESM 과 CommonJS 로 한 번씩 쓴다. 바꾸는 것은 **내보낸 모듈 자신**(`inc()`)이다.

```js
// counter42a.mjs
// A module that owns a counter and changes it itself.
export let n = 0;
export function inc() { n++; }
```

```js
// main42a.mjs
// Reads the counter by name, through the namespace object, and after inc() changed it inside its own module.
import { n, inc } from "./counter42a.mjs";
import * as ns from "./counter42a.mjs";
console.log("[1] before inc()  n = " + n + " · ns.n = " + ns.n);
inc();
console.log("[2] after inc()   n = " + n + " · ns.n = " + ns.n);
inc();
console.log("[3] after inc()   n = " + n + " · ns.n = " + ns.n);
```

```text
===== cd js40b-42a && node20 main42a.mjs (exit=0) =====
[1] before inc()  n = 0 · ns.n = 0
[2] after inc()   n = 1 · ns.n = 1
[3] after inc()   n = 2 · ns.n = 2
```

```js
// counter42a.cjs
// The same counter as a CommonJS module.
let n = 0;
function inc() { n++; }
module.exports = { n, inc };
```

```js
// main42a.cjs
// The same reads, through require().
const { n, inc } = require("./counter42a.cjs");
const m = require("./counter42a.cjs");
console.log("[1] before inc()  n = " + n + " · m.n = " + m.n);
inc();
console.log("[2] after inc()   n = " + n + " · m.n = " + m.n);
inc();
console.log("[3] after inc()   n = " + n + " · m.n = " + m.n);
```

```text
===== cd js40b-42a && node20 main42a.cjs (exit=0) =====
[1] before inc()  n = 0 · m.n = 0
[2] after inc()   n = 0 · m.n = 0
[3] after inc()   n = 0 · m.n = 0
```

Chrome 151 — 같은 ESM 두 파일을 로컬 서버로.

```text
===== ./js40b-browser.sh --http js40b-42a/main42a.mjs (exit=0) =====
[1] before inc()  n = 0 · ns.n = 0
[2] after inc()   n = 1 · ns.n = 1
[3] after inc()   n = 2 · ns.n = 2
```

- ★★★ **ESM — `n = 0 → 1 → 2`, `ns.n` 도 같다.** `import { n }` 은 값을 복사하지 않고 **`counter42a.mjs` 의 `n` 바인딩을 가리킨다.** 명세의 `CreateImportBinding` 이 「**저쪽 모듈의 바인딩을 가리키는** 불변 간접 바인딩」을 만든다.
- ★★★ **CommonJS — 세 줄 다 `0`**. `module.exports = { n, inc }` 는 그 순간의 `n`(0)을 **새 객체의 속성으로 복사**했다. 모듈 안의 `n++` 는 **지역 변수**만 바꾼다 — `m.n` 도 안 바뀐다.
- ★★ 두 node 판과 Chrome 151 이 ESM 쪽을 한 글자도 같게 냈다. **CommonJS 쪽의 더 긴 격자**(`exports.n` 을 다시 써 넣으면 · ESM 이 CJS 를 가져오면)는 [43번](../43-cjs-and-esm-interop/2-summary.md) 동작 (3)이다.

### (2) ★★★ 가져온 이름에 대입하면 — 그리고 이름공간 객체의 브랜드

**언제 쓰나** — 가져온 설정값을 「고쳐 쓰려」 할 때 · `import * as ns` 로 받은 객체를 다른 코드에 넘길 때.

```js
// value42b.mjs
// A module with one mutable export.
export let v = 1;
export function setV(x) { v = x; }
```

```js
// main42b.mjs
// Writes to an imported binding and to the namespace object -- and asks what kind of object the namespace is.
import { v, setV } from "./value42b.mjs";
import * as ns from "./value42b.mjs";
const show = (e) => e.constructor.name + " 「" + e.message + "」";
const tryIt = (label, f) => { let r; try { r = "ok " + JSON.stringify(f()); } catch (e) { r = show(e); } console.log("  " + label.padEnd(34) + r); };
console.log("[1] writes");
tryIt("v = 2", () => { v = 2; return v; });
tryIt("ns.v = 2", () => { ns.v = 2; return ns.v; });
tryIt("ns.w = 2 (a new property)", () => { ns.w = 2; return ns.w; });
tryIt("delete ns.v", () => delete ns.v);
tryIt("setV(3), then read v", () => { setV(3); return v; });
console.log("[2] the namespace object");
tryIt("Object.prototype.toString.call(ns)", () => Object.prototype.toString.call(ns));
tryIt("ns[Symbol.toStringTag]", () => ns[Symbol.toStringTag]);
tryIt("Object.getPrototypeOf(ns)", () => Object.getPrototypeOf(ns));
tryIt("Object.isExtensible(ns)", () => Object.isExtensible(ns));
tryIt("Object.isFrozen(ns)", () => Object.isFrozen(ns));
tryIt("descriptor of v", () => Object.getOwnPropertyDescriptor(ns, "v"));
tryIt("this at the top level", () => String(this));
```

```text
===== cd js40b-42b && node20 main42b.mjs (exit=0) =====
[1] writes
  v = 2                             TypeError 「Assignment to constant variable.」
  ns.v = 2                          TypeError 「Cannot assign to read only property 'v' of object '[object Module]'」
  ns.w = 2 (a new property)         TypeError 「Cannot add property w, object is not extensible」
  delete ns.v                       TypeError 「Cannot delete property 'v' of [object Module]」
  setV(3), then read v              ok 3
[2] the namespace object
  Object.prototype.toString.call(ns)ok "[object Module]"
  ns[Symbol.toStringTag]            ok "Module"
  Object.getPrototypeOf(ns)         ok null
  Object.isExtensible(ns)           ok false
  Object.isFrozen(ns)               ok false
  descriptor of v                   ok {"value":3,"writable":true,"enumerable":true,"configurable":false}
  this at the top level             ok "undefined"
```

Chrome 151 — **종류는 같고 문구 둘이 다르다.**

```text
===== ./js40b-browser.sh --http js40b-42b/main42b.mjs (exit=0) =====
[1] writes
  v = 2                             TypeError 「Assignment to constant variable.」
  ns.v = 2                          TypeError 「Cannot assign to property 'v' of [object Module]」
  ns.w = 2 (a new property)         TypeError 「Cannot assign to property 'w' of [object Module]」
  delete ns.v                       TypeError 「Cannot delete property 'v' of [object Module]」
  setV(3), then read v              ok 3
[2] the namespace object
  Object.prototype.toString.call(ns)ok "[object Module]"
  ns[Symbol.toStringTag]            ok "Module"
  Object.getPrototypeOf(ns)         ok null
  Object.isExtensible(ns)           ok false
  Object.isFrozen(ns)               ok false
  descriptor of v                   ok {"value":3,"writable":true,"enumerable":true,"configurable":false}
  this at the top level             ok "undefined"
```

```text
   가져온 쪽에서 쓰려 하면                        내보낸 쪽이 쓰면
   v = 2       → TypeError (불변 간접 바인딩)      setV(3) → v 바인딩이 3 ─▶ 가져온 쪽 v 도 3
   ns.v = 2    → TypeError (이름공간 [[Set]] 은 늘 거절)
   ns.w = 2    → TypeError (확장 불가)
   delete ns.v → TypeError
                               모듈은 늘 엄격(35번) ─▶ 조용히 무시하지 않고 던진다
```

- ★★★ **`v = 2` 는 `TypeError 「Assignment to constant variable.」`** — 내보낸 쪽은 `let` 인데도 그렇다. 가져온 바인딩은 **불변**(`CreateImportBinding`)이고, 모듈 코드는 **늘 엄격**이라(35번) 조용히 무시하지 않고 던진다.
- ★★★ **`setV(3)` 뒤의 `v` 는 `3`** — 바꾸는 길은 **내보낸 모듈의 함수**뿐이다.
- ★★ **이름공간 객체의 브랜드 — `[object Module]` · `Symbol.toStringTag` 는 `"Module"` · 프로토타입 `null` · 확장 불가.** 그런데 **`isFrozen` 은 `false`** 이고 속성 서술자는 **`writable: true`** 다 — 값이 바뀔 수 있으니(라이브) 동결은 아니다. 그래도 **쓰기는 늘 `TypeError`** 다.
- ★ **모듈 최상위의 `this` 는 `undefined`**(`"undefined"`). CommonJS 는 `this === module.exports` 였다(43번 동작 (4)).
- ★ Chrome 151 은 `ns.v = 2`·`ns.w = 2` 를 둘 다 `Cannot assign to property '…' of [object Module]` 로 적었다 — node 의 V8(10.2·11.3)은 `read only property` · `not extensible` 로 **갈라서** 적었다. 근거는 **`TypeError` 라는 종류**다.

### (3) ★★★ 순환 의존 격자 — 32칸

**언제 쓰나** — 두 모듈이 서로를 `import` 할 때(모델 ↔ 유틸 · 이벤트 버스 ↔ 핸들러).
★★★ `a.mjs` 는 `b.mjs` 를 가져오고(순환의 한쪽), `X` 를 **여덟 모양** 중 하나로 내보낸다. `b.mjs` 는 `X` 를 가져와 **자기 최상위에서** 한 번, **함수 안에서 나중에** 한 번 읽는다. `main.mjs` 는 **`a` 를 먼저** 또는 **`b` 를 먼저** 가져온다. 칸마다 새 디렉토리 · 새 프로세스다.

```js
// js40b-42c-cycle-grid.js
// Circular import grid: a.mjs <-> b.mjs. b reads a's export X twice -- at its own top level, and later inside a function.
//   8 ways a exports X  x  2 import orders in main.mjs  x  2 moments of reading  = 32 cells
// Each (form, order) pair is a fresh directory and a fresh node process (this same node binary).
// A cell prints the value read, or the exception as constructor.name 「message」.
const fs = require("fs"), path = require("path"), { execFileSync } = require("child_process");
const forms = [
  ["export let X", 'export let X = "A";', "{ X }", "X"],
  ["export const X", 'export const X = "A";', "{ X }", "X"],
  ["export var X", 'export var X = "A";', "{ X }", "X"],
  ["export function X", 'export function X() { return "A"; }', "{ X }", "X()"],
  ["export class X", 'export class X { static v = "A"; }', "{ X }", "X.v"],
  ["export default expression", 'export default "A";', "X", "X"],
  ["export default function", 'export default function () { return "A"; }', "X", "X()"],
  ["export default class", 'export default class { static v = "A"; }', "X", "X.v"],
];
const orders = { "a first": 'import "./a.mjs";\nimport { atTop, later } from "./b.mjs";', "b first": 'import { atTop, later } from "./b.mjs";\nimport "./a.mjs";' };
const guard = (expr) => '(() => { try { return String(' + expr + '); } catch (e) { return e.constructor.name + " 「" + e.message + "」"; } })()';
const root = path.join(__dirname, "js40b-42c-cells");
fs.rmSync(root, { recursive: true, force: true });
let broken = 0, total = 0, i = 0;
console.log("form".padEnd(28) + "main imports".padEnd(14) + "b reads at its top level".padEnd(60) + "b reads later, inside a function");
for (const [label, exportLine, importClause, read] of forms) {
  for (const [order, mainText] of Object.entries(orders)) {
    const dir = path.join(root, String(++i));
    fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(path.join(dir, "a.mjs"), 'import "./b.mjs";\n' + exportLine + "\n");
    fs.writeFileSync(path.join(dir, "b.mjs"), "import " + importClause + ' from "./a.mjs";\nexport const atTop = ' + guard(read) + ";\nexport function later() { return " + guard(read) + "; }\n");
    fs.writeFileSync(path.join(dir, "main.mjs"), mainText + '\nconsole.log(atTop + "\\n" + later());\n');
    const [top, late] = execFileSync(process.execPath, ["main.mjs"], { cwd: dir, encoding: "utf8" }).trimEnd().split("\n");
    for (const v of [top, late]) { total++; if (v !== "A") broken++; }
    console.log(label.padEnd(28) + order.padEnd(14) + top.padEnd(60) + late);
  }
}
console.log("");
console.log("cells that did not read \"A\": " + broken + " / " + total);
```

한 칸(`export let X` · `a first`)이 실제로 쓴 세 파일:

```text
===== cd js40b-42c-cells/1 && head -n 20 a.mjs b.mjs main.mjs (exit=0) =====
==> a.mjs <==
import "./b.mjs";
export let X = "A";

==> b.mjs <==
import { X } from "./a.mjs";
export const atTop = (() => { try { return String(X); } catch (e) { return e.constructor.name + " 「" + e.message + "」"; } })();
export function later() { return (() => { try { return String(X); } catch (e) { return e.constructor.name + " 「" + e.message + "」"; } })(); }

==> main.mjs <==
import "./a.mjs";
import { atTop, later } from "./b.mjs";
console.log(atTop + "\n" + later());
```

```text
===== node20 js40b-42c-cycle-grid.js (exit=0) =====
form                        main imports  b reads at its top level                                    b reads later, inside a function
export let X                a first       ReferenceError 「Cannot access 'X' before initialization」    A
export let X                b first       A                                                           A
export const X              a first       ReferenceError 「Cannot access 'X' before initialization」    A
export const X              b first       A                                                           A
export var X                a first       undefined                                                   A
export var X                b first       A                                                           A
export function X           a first       A                                                           A
export function X           b first       A                                                           A
export class X              a first       ReferenceError 「Cannot access 'X' before initialization」    A
export class X              b first       A                                                           A
export default expression   a first       ReferenceError 「Cannot access 'X' before initialization」    A
export default expression   b first       A                                                           A
export default function     a first       A                                                           A
export default function     b first       A                                                           A
export default class        a first       ReferenceError 「Cannot access 'X' before initialization」    A
export default class        b first       A                                                           A

cells that did not read "A": 6 / 32
```

Chrome 151 — 같은 16개 디렉토리를 `import()` 로 차례로 불렀다(번호는 위 격자의 줄 순서).

```js
// js40b-42c-cycle.web.js
// The 16 cell directories that js40b-42c-cycle-grid.js wrote, loaded in Chrome one after another with import().
// Each main.mjs prints two lines: b's read at its top level, then b's read inside a function.
(async () => {
  let broken = 0, total = 0;
  const seen = [];
  const log = console.log;
  for (let i = 1; i <= 16; i++) {
    console.log = (s) => seen.push(s);
    await import("./js40b-42c-cells/" + i + "/main.mjs");
    console.log = log;
    const [top, late] = seen.pop().split("\n");
    for (const v of [top, late]) { total++; if (v !== "A") broken++; }
    console.log(String(i).padStart(2) + "  " + top.padEnd(60) + late);
  }
  console.log("");
  console.log("cells that did not read \"A\": " + broken + " / " + total);
})();
```

```text
===== ./js40b-browser.sh --http js40b-42c-cycle.web.js (exit=0) =====
 1  ReferenceError 「Cannot access 'X' before initialization」    A
 2  A                                                           A
 3  ReferenceError 「Cannot access 'X' before initialization」    A
 4  A                                                           A
 5  undefined                                                   A
 6  A                                                           A
 7  A                                                           A
 8  A                                                           A
 9  ReferenceError 「Cannot access 'X' before initialization」    A
10  A                                                           A
11  ReferenceError 「Cannot access 'X' before initialization」    A
12  A                                                           A
13  A                                                           A
14  A                                                           A
15  ReferenceError 「Cannot access 'X' before initialization」    A
16  A                                                           A

cells that did not read "A": 6 / 32
```

```text
   main 이 a 를 먼저 가져올 때 — 평가 순서는 「깊이 우선, 끝난 것부터」

   main ──▶ a ──▶ b ──▶ (a 는 이미 「평가 중」 — 다시 안 들어간다)
                  │
                  ├ b 의 본문이 먼저 돈다: 최상위에서 X 를 읽는다
                  │     a 의 본문은 아직 한 줄도 안 돌았다
                  │       let / const / class / default 식 / default class  → 바인딩만 있다 → ReferenceError (TDZ)
                  │       var                                               → undefined 로 초기화돼 있다 → undefined
                  │       function / default function                       → 이미 함수로 초기화 → "A"
                  ▼
                 a 의 본문이 돈다 (X = "A")
                  ▼
                 main 이 later() 를 부른다 ─▶ 이제는 전부 "A"

   main 이 b 를 먼저 가져올 때 ─▶ a 가 먼저 끝까지 돈다 ─▶ b 가 읽을 때는 전부 "A"
```

- ★★★ **마지막 줄 — `did not read "A": 6 / 32`.** 깨진 여섯 칸은 **전부 `a first` · 최상위 읽기** 열이다.
  **`let`·`const`·`class`·`default` 식·`default class` 다섯은 `ReferenceError 「Cannot access 'X' before initialization」`**, **`var` 하나는 조용히 `undefined`** 다.
- ★★★ **`export function X` 와 `export default function` 은 `a first` 최상위에서도 `A`** — 순환에서도 쓸 수 있다. 명세의 `InitializeEnvironment` 가 **함수 선언만은 `InstantiateFunctionObject` 로 곧바로 초기화**하고(모듈 본문이 돌기 전), `var` 는 **`undefined` 로 초기화**하고, 나머지 렉시컬 선언은 **바인딩만 만든다**(초기화 전 = TDZ).
- ★★★ **`b first` 열과 「나중에 읽기」 열은 16칸 전부 `A`** — 읽는 **때**가 `a` 의 본문이 끝난 뒤면 모양과 상관없다. **05번의 「TDZ 는 줄이 아니라 시간이다」가 모듈 사이로 넓어진 것**이다.
- ★★ **`export default "A"` 도 TDZ** 이고, 문구는 **가져온 쪽의 이름**(`'X'`)을 댄다. `export default class` 도 TDZ 인데 `export default function` 은 멀쩡하다 — **「default 냐」가 아니라 「함수 선언이냐」가 갈랐다.**
- ★★ 두 node 판과 Chrome 151 이 **32칸을 한 글자도 같게** 냈다(node 18 대조 동일 · Chrome 도 `6 / 32`).

**파이썬 42번 격자와 나란히** — 두 격자는 **축이 다르다**(파이썬은 「어떻게 import 했나」, 여기는 「어떻게 export 했나」). 수를 견주지 말고 **깨지는 모양**을 견준다.

```text
                    순환에서 아직 덜 된 상대를 읽으면                    깨진 칸            어디서 알게 되나
   Python 42번      반쯤 찬 모듈 객체 → ImportError / AttributeError      7 / 24            실행 중, 그 줄에서
                    (함수 안 import 열은 전부 통과)
   JS ESM (이 문서)  바인딩은 있는데 초기화 전 → ReferenceError (TDZ)      6 / 32            실행 중, 그 줄에서
                    ★ var 는 undefined · function 선언은 멀쩡             (a first · 최상위 열만)
                    (나중에 읽는 열은 전부 통과)
   JS CommonJS      반쯤 찬 exports 객체 → undefined + 경고 한 줄         (파이썬 42번 7절의    ★ 값이 틀린 채 계속 간다
                                                                        node 18 탐침)
   Go               만날 수 없다 — import cycle not allowed                —                 빌드 때 (exit 1)
```

- ★★ **공통점** — 두 언어 모두 **「읽는 때를 뒤로 미루면(함수 안) 전부 통과」** 했다. 순환 자체가 아니라 **최상위에서 상대의 값을 읽는 것**이 깨뜨린다.
- ★★ **차이** — 파이썬은 **모듈 객체의 속성**을 찾다 실패하고(`AttributeError`/`ImportError`), ESM 은 **이름은 연결돼 있는데 초기화 전**이라 실패한다. ESM 에서 **`var` 만 `undefined` 로 새는 것**은 CommonJS 의 `undefined` 와 같은 「조용한」 부류다.

### (4) ★★★ `import` 는 먼저 돈다 — 파일 중간에 있어도

**언제 쓰나** — `import` 위에 둔 코드(환경 변수 설정·폴리필)가 **import 한 모듈보다 먼저** 돌 거라 기대할 때.

```js
// dep42d.mjs
// Prints when its body runs.
console.log("dep42d.mjs: body runs");
export const x = "x";
```

```js
// main42d.mjs
// An import statement in the middle of the file.
console.log("main42d.mjs: first line");
import { x } from "./dep42d.mjs";
console.log("main42d.mjs: line after the import · x = " + x);
```

```text
===== cd js40b-42d && node20 main42d.mjs (exit=0) =====
dep42d.mjs: body runs
main42d.mjs: first line
main42d.mjs: line after the import · x = x
```

```js
// dep42d.cjs
// Prints when its body runs.
console.log("dep42d.cjs: body runs");
exports.x = "x";
```

```js
// main42d.cjs
// A require() call in the middle of the file.
console.log("main42d.cjs: first line");
const { x } = require("./dep42d.cjs");
console.log("main42d.cjs: line after the require · x = " + x);
```

```text
===== cd js40b-42d && node20 main42d.cjs (exit=0) =====
main42d.cjs: first line
dep42d.cjs: body runs
main42d.cjs: line after the require · x = x
```

평가 순서 — `top` 이 `left`·`right` 를 가져오고, `left` 도 `right` 를 가져온다.

```js
// top42d.mjs
// top imports left and right; left imports right as well. Each body prints once it runs.
import "./left42d.mjs";
import "./right42d.mjs";
console.log("top42d.mjs: body");
```

```js
// left42d.mjs
import "./right42d.mjs";
console.log("left42d.mjs: body");
```

```js
// right42d.mjs
console.log("right42d.mjs: body");
```

```text
===== cd js40b-42d && node20 top42d.mjs (exit=0) =====
right42d.mjs: body
left42d.mjs: body
top42d.mjs: body
```

Chrome 151 — `main42d.mjs` 와 `top42d.mjs` 를 한 페이지에서.

```text
===== ./js40b-browser.sh --http js40b-42d/main42d.mjs,js40b-42d/top42d.mjs (exit=0) =====
dep42d.mjs: body runs
main42d.mjs: first line
main42d.mjs: line after the import · x = x
right42d.mjs: body
left42d.mjs: body
top42d.mjs: body
```

```text
   ESM                                            CommonJS
   ① 연결: main42d 가 dep42d 를 가져온다           ① main42d.cjs 첫 줄
   ② 평가: dep42d 본문   ◀── 먼저                 ② require() 줄에서 dep42d.cjs 본문
   ③ 평가: main42d 본문 — first line · after       ③ main42d.cjs 다음 줄
      (import 줄은 본문의 「실행」에 없다)

   top ─▶ left ─▶ right      평가: right · left · top   (깊이 우선 · 끝난 것부터 · right 는 한 번만)
      └──────────▶ right
```

- ★★★ **ESM — `dep42d.mjs: body runs` 가 `main42d.mjs: first line` 보다 먼저**다. `import` 문은 **실행되는 문장이 아니라** 모듈의 **연결 정보**라, 파일 어디에 있든 상대 모듈이 **먼저 평가**된다.
- ★★★ **CommonJS — `first line` 이 먼저, 그다음 `require` 줄에서 `dep42d.cjs: body runs`.** `require` 는 **그 줄에서 도는 함수 호출**이다.
- ★★ **평가 순서는 `right · left · top`** — 깊이 우선으로 내려가 **끝난 것부터** 평가하고, `right` 는 두 번 가져와도 **한 번만** 돈다. Chrome 151 도 같았다.
- ★ 36번에서 **같은 파일이 ES 모듈이면 `nextTick` 이 4위에서 9위**로 밀린 것도 「모듈 본문이 어디서 도나」의 차이였다 — 36번은 그것을 「**모듈 본문 자체가 『이미 마이크로태스크를 비우는 중』에 돈다**」로 적었다(node 문서 인용).

### (5) ★★ 정적 구조 — 블록 안의 `import` · 없는 이름 · 그리고 `import()`

**언제 쓰나** — 조건에 따라 모듈을 고르고 싶을 때 · 오타 난 이름을 `import` 했을 때.

```js
// has42e.mjs
// Exports one name.
console.log("has42e.mjs: body runs");
export const yes = 1;
```

```js
// inblock42e.mjs
// An import statement inside a block.
console.log("inblock42e.mjs: first line");
if (true) {
  import { yes } from "./has42e.mjs";
}
```

```js
// missing42e.mjs
// Imports a name the other module does not export.
console.log("missing42e.mjs: first line");
import { nope } from "./has42e.mjs";
console.log(nope);
```

```sh
# js40b-42e-static.sh
#!/usr/bin/env bash
# Two files that break the static structure (js40b-42e/inblock42e.mjs, js40b-42e/missing42e.mjs), on node20 and node18.
# Standard output: how many lines. Standard error: from its first line down to the line that names the error,
# with this directory's absolute path replaced by <dir>.
set -u -o pipefail
cd "$(dirname "$0")/js40b-42e"
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
for f in inblock42e.mjs missing42e.mjs; do
  for v in 20 18; do
    [ $v = 18 ] && n="$N18" || n="$N20"
    echo "--- node$v $f"
    out="$("$n" "$f" 2>/dev/null)"
    err="$("$n" "$f" 2>&1 >/dev/null)"
    e=$?
    printf '%s\n' "$err" | sed "s#$PWD#<dir>#g" | sed -n '1,/^[A-Za-z]*Error/p'
    echo "(exit $e · standard output had $(printf '%s' "$out" | grep -c '' || true) lines)"
  done
done
```

```text
===== ./js40b-42e-static.sh (exit=0) =====
--- node20 inblock42e.mjs
file://<dir>/inblock42e.mjs:4
  import { yes } from "./has42e.mjs";
         ^

SyntaxError: Unexpected token '{'
(exit 1 · standard output had 0 lines)
--- node18 inblock42e.mjs
file://<dir>/inblock42e.mjs:4
  import { yes } from "./has42e.mjs";
         ^

SyntaxError: Unexpected token '{'
(exit 1 · standard output had 0 lines)
--- node20 missing42e.mjs
file://<dir>/missing42e.mjs:3
import { nope } from "./has42e.mjs";
         ^^^^
SyntaxError: The requested module './has42e.mjs' does not provide an export named 'nope'
(exit 1 · standard output had 0 lines)
--- node18 missing42e.mjs
file://<dir>/missing42e.mjs:3
import { nope } from "./has42e.mjs";
         ^^^^
SyntaxError: The requested module './has42e.mjs' does not provide an export named 'nope'
(exit 1 · standard output had 0 lines)
```

Chrome 151 — 같은 두 파일(페이지의 `error` 리스너가 받은 것).

```text
===== ./js40b-browser.sh --http js40b-42e/inblock42e.mjs (exit=0) =====
uncaught Uncaught SyntaxError: Unexpected token '{'
```

```text
===== ./js40b-browser.sh --http js40b-42e/missing42e.mjs (exit=0) =====
uncaught Uncaught SyntaxError: The requested module './has42e.mjs' does not provide an export named 'nope'
```

```js
// dynamic42e.mjs
// import() as an expression: inside a block, twice, and for a file that does not exist.
console.log("dynamic42e.mjs: first line");
if (true) {
  const p = import("./has42e.mjs");
  console.log("import() returned " + p.constructor.name);
  const ns = await p;
  console.log("yes = " + ns.yes + " · same namespace object the second time: " + (ns === (await import("./has42e.mjs"))));
}
try { await import("./nothing-here42e.mjs"); } catch (e) { console.log("missing file: rejected with " + e.constructor.name + " · code " + e.code); }
```

```text
===== cd js40b-42e && node20 dynamic42e.mjs (exit=0) =====
dynamic42e.mjs: first line
import() returned Promise
has42e.mjs: body runs
yes = 1 · same namespace object the second time: true
missing file: rejected with Error · code ERR_MODULE_NOT_FOUND
```

```js
// dynamic42e.cjs
// import() from CommonJS.
import("./has42e.mjs").then((ns) => console.log("from CommonJS: import() gave yes = " + ns.yes + " · typeof require " + typeof require));
```

```text
===== cd js40b-42e && node20 dynamic42e.cjs (exit=0) =====
has42e.mjs: body runs
from CommonJS: import() gave yes = 1 · typeof require function
```

Chrome 151 — `dynamic42e.mjs` 를 로컬 서버로.

```text
===== ./js40b-browser.sh --http js40b-42e/dynamic42e.mjs (exit=0) =====
dynamic42e.mjs: first line
import() returned Promise
has42e.mjs: body runs
yes = 1 · same namespace object the second time: true
missing file: rejected with TypeError · code undefined
```

```text
   모듈 한 벌이 도는 세 단계

   파싱 ─── 블록 안 import → SyntaxError 「Unexpected token '{'」           (본문 0 줄)
     ▼
   연결 ─── ResolveExport 가 null → SyntaxError 「… does not provide an export named 'nope'」
     ▼                                                                    (has42e 의 본문도 0 줄)
   평가 ─── 여기서부터 첫 줄이 돈다 · import() 는 이 단계에서 부르는 「식」이다 → Promise
```

- ★★★ **블록 안 `import` — `SyntaxError 「Unexpected token '{'」` · 표준 출력 0 줄** — `import` 선언은 **모듈의 최상위에만** 쓸 수 있는 문법이다. 캐럿이 `{` 를 가리킨다.
- ★★★ **없는 이름 — `SyntaxError 「The requested module './has42e.mjs' does not provide an export named 'nope'」` · 표준 출력 0 줄.** `missing42e.mjs` 의 첫 줄도, **`has42e.mjs` 의 `body runs` 도** 안 찍혔다 — **어느 본문도 돌기 전**(연결 단계)에 막혔다. 명세 `InitializeEnvironment` 의 「`ResolveExport` 가 **null 이면 `SyntaxError`**」다.
- ★★ **`import()` 는 식이다** — 블록 안에서 돌고, **`Promise`** 를 돌려주고, 두 번 불러도 **같은 이름공간 객체**(`true`)다. **CommonJS 에서도** 된다(`typeof require function` 인 채로).
- ★★ **없는 파일의 `import()`** — node 는 `Error · code ERR_MODULE_NOT_FOUND`, Chrome 151 은 `TypeError · code undefined` 로 거부했다. **파일을 찾는 일은 호스트**라 거부의 모양도 호스트마다 다르다.

## 문법 — 형태와 규칙

★ 이 절은 **형태 표**다 — 모든 동작 주장은 위 동작 절의 캡처 블록에서만 한다.

| 형태 | 하는 일 | 판 | 어디서 봤나 |
|---|---|---|---|
| `export let/const/var x` · `export function f` · `export class C` | 이름을 내보낸다 — 가져간 쪽에는 **라이브 바인딩** | ES2015 | 동작 (1)·(3) |
| `export default 식` · `export default function` · `export default class` | `default` 라는 이름으로 내보낸다 — **함수 선언만** 미리 초기화 | ES2015 | 동작 (3) |
| `import { x } from "./m.mjs"` · `import d from …` · `import * as ns from …` | 연결 단계에서 **불변 간접 바인딩**을 만든다 | ES2015 | 동작 (1)·(2) |
| `import "./m.mjs"` | 가져올 이름 없이 **평가만** 시킨다 | ES2015 | 동작 (3)·(4) |
| `import("./m.mjs")` | **식** — 이름공간 객체로 이행하는 `Promise` · 스크립트·CommonJS 에서도 | **ES2020** | 동작 (5) |
| `import.meta` | 모듈마다 하나 — **속성은 호스트가 채운다** | **ES2020** | 43번 동작 (4) |

- **`import`/`export` 선언은 모듈 최상위에만** — 블록 안이면 파싱 단계의 `SyntaxError` 다.
- **없는 이름을 가져오면 연결 단계의 `SyntaxError`** — 어느 본문도 안 돈다.
- **가져온 이름은 읽기 전용** — 바꾸려면 내보낸 모듈이 함수를 내준다.

## 어디서 틀리나

### (1) ★★★ 「`import { n }` 은 그 순간의 값을 받는다」

**이름을 받는다** — 내보낸 쪽이 바꾸면 `0 → 1 → 2` 로 따라간다(동작 (1)). **값을 받는 것은 CommonJS**(`0 · 0 · 0`)다.

### (2) ★★★ 순환 의존에서 「그냥 `undefined` 가 나온다」

**모양에 따라 셋으로 갈린다** — `let`/`const`/`class`/`default` 식/`default class` 는 **`ReferenceError`**, `var` 는 **`undefined`**, `function` 선언은 **멀쩡**(동작 (3)). 그리고 **가져오는 순서**와 **읽는 때**가 바뀌면 전부 멀쩡하다.

### (3) ★★★ 순환을 풀려고 `var` 로 바꾼다

**에러가 사라지는 대신 `undefined` 가 조용히 흐른다**(`export var X` · `a first` · 최상위 = `undefined`). 읽는 때를 **함수 안으로 미루거나**, 순환을 끊는다.

### (4) ★★★ `import` 위에 둔 초기화 코드가 먼저 돈다고 믿는다

**import 한 모듈이 먼저 돈다**(`dep42d.mjs: body runs` 가 첫 줄보다 앞 — 동작 (4)). 먼저 돌아야 하는 코드는 **별도 모듈로 떼어 먼저 `import`** 한다.

### (5) ★★ 가져온 설정값을 그 자리에서 고친다

**`TypeError 「Assignment to constant variable.」`** — 내보낸 쪽이 `let` 이어도 그렇다(동작 (2)).

### (6) ★★ `import * as ns` 는 평범한 객체라 믿는다

**`[object Module]` · 프로토타입 `null` · 확장 불가 · 쓰기는 전부 `TypeError`** 다(동작 (2)).

### (7) ★★ 조건부로 `import` 문을 쓴다

**파싱 `SyntaxError`** — 조건부 적재는 **`import()`** 로 한다(동작 (5)).

### (8) ★ 「ESM 이 빠르다」·「정적 구조라 번들이 작아진다」를 근거로 쓴다

**이 문서는 재지 않았다.** 정적 구조가 **실행에서** 보이는 것은 「블록 안 `import` 가 문법 오류」·「없는 이름이 본문 전에 막힘」까지다.

## 구현 세부사항 대 언어 보장

### 명세 보장(ECMA-262)

- ★★★ **`InitializeEnvironment`** — 가져온 이름마다 `ResolveExport` 로 찾고 **없으면 `SyntaxError`**, 있으면 **`CreateImportBinding`**(불변 간접 바인딩). `var` 는 **`undefined` 로 초기화**, 렉시컬 선언은 **바인딩만**, **함수 선언은 곧바로 함수로 초기화** — 이 셋이 순환 격자의 세 모양이다.
- ★★ **모듈 코드는 늘 엄격**(35번) — 불변 바인딩 대입이 **`TypeError`** 로 드러난다.
- ★★ **평가는 깊이 우선** — 각 모듈은 **한 번만** 평가된다(동작 (4)).
- ★★ **`import()`** 는 식이고 **`Promise`** 를 돌려준다(ES2020).

### 호스트

- ★★★ **모듈 지정자 해석·파일 읽기·「어느 파일이 모듈인가」** — node(`.mjs`·`"type"`·확장자 규칙 — 43번)와 브라우저(URL · `<script type="module">` · **`file://` 에서 CORS 로 막힌다**)가 각자 정한다.
- ★★ **없는 파일의 `import()` 거부 모양** — node `ERR_MODULE_NOT_FOUND` · Chrome `TypeError`.
- ★ 모듈 본문이 이벤트 루프의 어디서 도나 — 36번의 `nextTick` 4위 대 9위(node 의 것).

### 구현(V8) · 이 판의 관찰

- ★ 문구 — `Cannot access 'X' before initialization` · `Assignment to constant variable.` · 이름공간 쓰기 문구는 **Chrome 151 과 node 가 달랐다.**
- ★ 32칸 격자는 세 판이 같았다.

### 그래서 이렇게 적으면 틀린다

- ✗ 「`import` 는 호이스팅된다」 → ○ 「`import` 는 **실행되는 문장이 아니다** — 연결 정보라서 상대 모듈이 **본문보다 먼저** 평가된다」
- ✗ 「순환 import 에서는 `undefined` 가 나온다」 → ○ 「**`var` 만** `undefined` — `let`·`const`·`class`·`default` 식은 **TDZ**, 함수 선언은 **멀쩡**」
- ✗ 「`export default` 는 순환에서 안전하다/위험하다」 → ○ 「**함수 선언이냐**가 가른다 — `default function` 은 멀쩡, `default class`·`default 식` 은 TDZ」

## 언제 쓰고 언제 안 쓰나

- **`export function`** — 순환이 생길 수 있는 모듈 사이의 **호출 통로**(순환에서도 쓸 수 있다).
- **상태는 `export let` + 바꾸는 함수** — 가져간 쪽이 라이브로 본다. 가져간 쪽은 **바꾸지 않는다.**
- **`import()`** — 조건부·지연 적재. CommonJS 에서 ESM 을 쓰는 길이기도 하다(43번).
- ★ **안 쓰는 자리** — 순환 속에서 **최상위에서 상대의 값을 읽기** · 에러를 없애려 `var` 로 바꾸기 · import 순서에 기대는 부작용.

## 핵심 문장

1. ★★★ ESM 의 `import` 는 **이름(바인딩)** 을 빌려 온다 — 내보낸 쪽의 `n++` 가 `0 → 1 → 2` 로 보이고, CommonJS 는 **`0` 에 멈춘다.**
2. ★★★ 가져온 이름은 **불변** — `v = 2` 는 `TypeError`. 이름공간 객체는 `[object Module]` · 프로토타입 `null` · 쓰기 전부 `TypeError`.
3. ★★★ 순환 격자 **`6 / 32`** — `a first` · 최상위 읽기에서 `let`·`const`·`class`·`default` 식·`default class` 는 **TDZ**, `var` 는 **`undefined`**, **함수 선언은 멀쩡.** 순서나 읽는 때를 바꾸면 전부 `A`.
4. ★★★ `import` 는 **연결 → 평가** 순서라 파일 중간에 있어도 **먼저** 돌고, 없는 이름은 **본문이 한 줄도 돌기 전에** `SyntaxError` 다. 평가는 깊이 우선 · 한 번만.
5. ★★ `import()` 는 **식**이다 — `Promise` · 블록 안 · CommonJS 에서도. 없는 파일의 거부 모양은 **호스트**가 정한다.

## 관련 자료

- [ECMA-262 — Scripts and Modules](https://tc39.es/ecma262/multipage/ecmascript-language-scripts-and-modules.html) · [TC39 finished proposals](https://github.com/tc39/proposals/blob/main/finished-proposals.md) · [Node.js v20 — Packages](https://nodejs.org/docs/latest-v20.x/api/packages.html)
- [`history/js/02-ES6-모던.md`](../../../../../../history/js/02-ES6-모던.md) — ★ **경계**: 그쪽은 **「모듈 (import / export)」 절의 연혁과 「정적 구조 → 트리 셰이킹」 인과**, 여기는 **그 정적 구조가 실행에서 보이는 모양**(연결·평가·바인딩)부터.
- [35 — 엄격 모드](../35-strict-mode/2-summary.md) · [05 — TDZ](../05-var-let-const-and-tdz/2-summary.md) · [36 — 이벤트 루프](../36-event-loop-and-microtasks/2-summary.md) · [39 — `async`/`await`](../39-async-await/2-summary.md).
- [Python 42 — 모듈·패키지·import](../../../python/syntax/42-modules-packages-and-import/2-summary.md) — 순환 격자 `7 / 24` · ESM/CJS 첫 대비. [Go 01 — 패키지·import](../../../go/syntax/01-packages-imports-main-and-init/2-summary.md) — 순환은 빌드 거부.
- [43 — CJS 와 ESM 상호운용](../43-cjs-and-esm-interop/2-summary.md) · 목록의 **44번 주제**(동적 `import`·최상위 `await`·import attributes).

## 용어 풀이

- **ESM(ECMAScript 모듈)** — `import`/`export` 로 잇는 언어 표준 모듈.
- **바인딩** — 이름과 그 값이 사는 칸의 연결.
- **라이브 바인딩** — 가져온 이름이 내보낸 쪽 칸을 그대로 가리키는 것.
- **불변 간접 바인딩** — `CreateImportBinding` 이 만드는, **읽기만** 되는 가져온 이름.
- **이름공간 객체(module namespace object)** — `import * as ns` 가 주는 객체. `[object Module]`.
- **연결(Link) / 평가(Evaluate)** — 모듈 그래프의 이름을 먼저 전부 잇는 단계 / 본문을 실제로 돌리는 단계.
- **TDZ** — 바인딩은 있는데 아직 초기화 전이라 읽으면 `ReferenceError` 인 구간(05번).
- **순환 의존** — 모듈 A 가 B 를, B 가 A 를(직접이든 건너서든) 가져오는 것.
- **모듈 지정자** — `from` 뒤의 문자열(`"./m.mjs"`). 무엇을 가리키나는 호스트가 정한다.

## 더 들어가면

- **최상위 `await` 가 순환·평가 순서에 끼면** — 목록의 **44번 주제**다. 이 문서는 돌리지 않았다.
- **`export * from` 의 이름 충돌(모호한 내보내기)** — `ResolveExport` 가 `ambiguous` 를 돌려주는 자리. 재지 않았다.
- **브라우저의 import map** — 지정자 해석을 페이지가 정하는 장치. 호스트 쪽이라 이 문서 밖이다.
