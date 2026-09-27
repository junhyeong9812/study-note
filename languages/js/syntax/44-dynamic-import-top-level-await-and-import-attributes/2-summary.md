# js/syntax/44 — 동적 `import`·최상위 `await`·import attributes: 「`import()` 는 부르는 순간 적재하고, 최상위 `await` 는 자기를 가져오는 쪽만 세우며, `with { type: "json" }` 은 판마다 다른 칸에서 막힌다」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> ★★★ **이 주제의 본체는 ① 평가 순서 로그다** — 모듈 본문이 **언제** 도는지는 값으로 안 보인다. 본문 첫 줄에 로그를 심고 **줄의 순서**로 읽는다(동작 (1)·(2)·(3)).
> ★★★ **import attributes 는 ② 판 격자로 본다** — 12행 × 세 판(node 20 · node 18 · Chrome 151)의 「**막힌 행 N / 12**」와 「**세 판이 다 같지는 않은 행 N / 12**」을 스크립트가 마지막 줄로 찍는다(동작 (4)).
> ★★ 보조로 **④ 예외의 이름 + 코드**(`ERR_IMPORT_ASSERTION_TYPE_MISSING` · `SyntaxError 「Unexpected token 'with'」`)를 쓴다.
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262 — Scripts and Modules](https://tc39.es/ecma262/multipage/ecmascript-language-scripts-and-modules.html) — `WithClause : with { WithEntries }`(키가 겹치면 `SyntaxError`) · `AllImportAttributesSupported` 가 거짓이면 「**a newly created SyntaxError object**」 · `HostGetSupportedImportAttributes`(어느 키를 받을지는 **호스트**가 정한다) · `HostLoadImportedModule` 의 「`type` 이 `"json"` 이면 결과는 **`ParseJSONModule`** 의 것이거나 throw」와 그 note 「**`type: "json"` 없이 JSON 모듈을 지원하는 것을 금하지는 않는다**」 · `ParseJSONModule` → `CreateDefaultExportSyntheticModule`(내보내기는 **`default` 하나**) · 평가 쪽의 `[[AsyncEvaluationOrder]]` · `[[PendingAsyncDependencies]]` · `ExecuteAsyncModule` · `GatherAvailableAncestors` · 이미 평가된 모듈은 `[[EvaluationError]]` 를 **그대로 다시** 돌려준다
> - ★ **이 명세 페이지에는 `assert` 라는 낱말이 한 번도 없다**(텍스트로 뽑아 센 값 0) — `assert { … }` 는 **ECMA-262 문법이 아니다.**
> - [TC39 finished proposals](https://github.com/tc39/proposals/blob/main/finished-proposals.md) — 판 경계(Top-level `await` **2022** · Import Attributes **2025** · JSON Modules **2025**). `import()` 는 42번 머리말의 **2020**.
> - [Node.js v20 — ECMAScript modules](https://nodejs.org/docs/latest-v20.x/api/esm.html) — 「Import attributes」 이력 「**v20.10.0 — Import Assertions 에서 Import Attributes 로**」 · 「**node 는 `type` 속성만** 받고, 값은 `'json'` 뿐」 · 「JSON 모듈에는 **`type: 'json'` 이 의무**」 · 「JSON 모듈은 **`default` 만** — 이름 있는 내보내기 없음」 · 「최상위 `await` 가 끝내 안 풀리면 **종료 코드 13**」
> - [Node.js v18 — ECMAScript modules](https://nodejs.org/docs/latest-v18.x/api/esm.html) — 같은 절의 이력 「**v18.20.0 — Import Attributes 로 전환**」. ★★★ **이 머신의 node 18 은 v18.19.1 이다** — 전환 **전** 판이다(동작 (4)가 그것을 보인다).
>
> **실행 검증** — 이 문서의 모든 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다.
> 배너의 `node20` 은 `~/.nvm/versions/node/v20.19.6/bin/node`, `node18` 은 기본 PATH 의 `node`(v18.19.1)다. `cd <디렉토리> && node20 <파일>` 꼴 배너는 **그 디렉토리 안에서 상대 경로로** 던졌다.
> ★★ **ES 모듈은 `file://` 페이지에서 CORS 로 막힌다 — Chrome 151 은 로컬 HTTP 서버로 띄웠다**(아래 하네스의 `--http` · `js44b-serve.py`). 이 묶음(44\~47)의 Chrome 블록은 전부 이 하네스에서 나왔다(40\~43 묶음의 하네스를 복사해 이름과 `--gc` 선택지만 바꿨다).
> ★★★ **성능은 재지 않았다** — 「동적 `import` 가 초기 로딩을 줄인다」를 **쓰지 않는다.** 이 문서가 보이는 것은 「**본문이 언제 도나**」의 순서뿐이다.
>
> **버전**
>
> | 무엇 | 판 | 이 머신에서 |
> |---|---|---|
> | 동적 `import()` | **ES2020** | 세 판 다(판별 블록 · 42번 동작 (5)) |
> | 최상위 `await` | **ES2022** | 세 판 다(동작 (2)) |
> | import attributes `with { … }` · `import(…, { with })` | **ES2025** | ★★★ **node 20 · Chrome 151 은 받고, node 18.19.1 은 `SyntaxError`**(동작 (4)) |
> | JSON 모듈 | **ES2025** | 세 판 다 — 단 **node 18 은 `assert` 로만**, Chrome 은 **`with` 로만** |
> | `assert { … }`(옛 import assertions) | ★ **표준에 없다** | node 18 · node 20 은 받고(경고) **Chrome 151 은 `SyntaxError`** |
>
> **★★★ 이 주제가 쓰는 창 — 그리고 부적용인 창**
>
> | 창 | 이 주제에서 무엇을 보나 |
> |---|---|
> | ★★★ **① 로그 심기**(본체) | 모듈 본문 첫 줄의 로그 — `import()` 가 부르는 순간 도는 것 · 두 번 불러도 한 번(동작 (1)) · 최상위 `await` 가 누구를 세우나(동작 (2)) · 실패한 모듈의 본문 횟수(동작 (3)) |
> | ★★★ **② 판 격자** | import attributes 12행 × 세 판 — `blocked rows` · `differ` 셋(동작 (4)) |
> | ★★ **④ 예외의 이름 + 코드** | `ERR_IMPORT_ASSERTION_TYPE_MISSING` 등 node 의 코드 · Chrome 의 `SyntaxError` 문구(동작 (4)) · 거부된 `import()` 의 `constructor.name`(동작 (3)) |
> | ★ **종료 코드** | 끝내 안 풀리는 최상위 `await` — **`exit 13` · 표준 오류 0 줄**(동작 (2)) |
> | ★ **부적용 — ③ 브랜드 태그** | 이름공간 객체의 `[object Module]` 은 42번이 쟀다. 이 주제는 **같은 객체인가**(`===`)만 본다 |
> | ★ **못 잰 것 — Chrome 이 거부한 「이유」** | 격자의 Chrome 칸은 `import()` 의 거부만 받는다. 정적 `import` 가 막힌 칸은 문구가 **「어느 모듈을 못 가져왔나」까지만** 말하고(`Failed to fetch dynamically imported module: <origin>/…/main.mjs`), 이유(MIME 형식 불일치 등)는 **DevTools 콘솔로만** 간다 — 이 하네스는 콘솔을 못 읽는다. 그래서 Chrome 칸은 **에러 이름**만 근거로 쓴다 |
> | ★ **안 쟀다 — 시간·크기** | 동적 적재가 무엇을 아끼는지는 재지 않았다 |
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 판별 블록의 판 문자열 · Chrome 문구의 **origin**(포트가 매번 바뀐다 — 블록 안에서 `<origin>` 으로 지웠다) · node 경고의 PID(블록 안에서 지웠다) | ★★★ 로그의 **줄 순서** · 격자의 모든 칸과 마지막 네 줄 · 에러의 **이름과 코드** · 종료 코드 |
> | ★ **이 주제의 탐침에는 재실행에서 흔들린 칸이 없다**(재대조 동일) | ★★ **판 사이의 차이**(`with` 대 `assert`)는 흔들림이 아니라 **판의 차이**다 — 그것이 격자의 절반이다 |
>
> **층** — `import()`·최상위 `await`·`with` 의 **문법과 평가 순서**는 **언어(ECMA-262)** 다. **어느 속성 키를 받나 · 모르는 `type` 값을 어떻게 거절하나 · JSON 을 속성 없이도 받나 · 파일을 읽어 오는 일**은 **호스트**다 — 명세가 `HostGetSupportedImportAttributes`·`HostLoadImportedModule` 로 문을 열어 두었다. `assert` 는 **어느 층에도 표준이 아니다** — 엔진(V8)이 옛 제안을 남겨 둔 것이다.
>
> **선행** — [42 — ESM 모듈](../42-esm-modules/2-summary.md)(직접 선행 — ★★★ **정적 `import` 의 연결 → 평가 · 깊이 우선 · 각 모듈은 한 번**이 거기 동작 (4)에 있다 · ★★ **`import()` 는 식이고 `Promise` 를 돌려주며, 두 번 불러도 같은 이름공간 객체 · 없는 파일은 node `ERR_MODULE_NOT_FOUND` · Chrome `TypeError`** 가 거기 동작 (5)에 있다 — 이 문서는 그것을 **다시 재지 않고** 「부르는 순간 · 실패 · 속성」 쪽만 넓힌다) ·
> [43 — CJS 와 ESM 상호운용](../43-cjs-and-esm-interop/2-summary.md)(★★★ **CommonJS 에서 `import()` 는 두 판 다 되고, 최상위 `await` 가 든 ESM 을 `require` 하면 node 18 `ERR_REQUIRE_ESM` · node 20 `ERR_REQUIRE_ASYNC_MODULE`** — 거기 동작 (1)) ·
> [39 — `async`/`await`](../39-async-await/2-summary.md)(★★ **최상위 `await` 는 ES 모듈에서만** — 거기 동작 (7)) ·
> [31 — JSON](../31-json/2-summary.md)(JSON 모듈의 값은 `ParseJSON` 의 결과다).
>
> ★★ **경계** — README 44행의 「기존 주제」 칸은 비어 있다(`—`). 연혁(import assertions → attributes 로 이름과 키워드가 바뀐 경위)은 **이 목록의 몫이 아니다**(README 「뺀 것과 이유」의 「버전별 신기능 나열 — `history/js/`」). 여기는 **그 전환이 지금 세 판의 어느 칸에 남았나**부터다.

하네스 — 페이지 · 헤드리스 Chrome 을 띄우는 스크립트 · 로컬 서버 · 판별 스크립트 둘.

```html
<!-- js44b-page.html -->
<!doctype html>
<meta charset="utf-8">
<title>js44b</title>
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
# js44b-browser.sh
#!/usr/bin/env bash
# Run probe scripts in headless Chrome and print what they logged.
#   usage: ./js44b-browser.sh [--gc] [--http] <script>[,<script>...]
# Default: file:// with --allow-file-access-from-files (without it a file:// script counts as cross-origin -- "muted errors").
# --http: through js44b-serve.py on 127.0.0.1 -- module scripts (.mjs) need it.
# --gc: start Chrome with --js-flags=--expose-gc, so the page has a global gc().
# --dump-dom writes HTML entities, so the last sed turns them back.
set -u -o pipefail
cd "$(dirname "$0")"
flags=()
if [ "$1" = "--gc" ]; then flags=(--js-flags=--expose-gc); shift; fi
if [ "$1" = "--http" ]; then
  shift
  pf="$(mktemp -p "$PWD" .port-XXXXXX)"
  python3 js44b-serve.py "$pf" > /dev/null 2>&1 &
  srv=$!
  for _ in $(seq 100); do [ -s "$pf" ] && break; sleep 0.05; done
  url="http://127.0.0.1:$(cat "$pf")/js44b-page.html?$1"
  rm -f "$pf"
else
  srv=
  url="file://$PWD/js44b-page.html?$1"
fi
google-chrome --headless --allow-file-access-from-files "${flags[@]}" --virtual-time-budget=60000 --dump-dom "$url" 2>/dev/null \
  | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' \
  | sed 's/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&amp;/\&/g'
rc=$?
[ -n "$srv" ] && kill "$srv"
exit $rc
```

```python
# js44b-serve.py
# A local HTTP server for the Chrome harness: ES modules do not load from file:// (CORS).
# Serves this directory on 127.0.0.1 at a free port and writes the port to the file named in argv[1].
import http.server, os, sys

class H(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map, ".mjs": "text/javascript", ".js": "text/javascript"}
    def log_message(self, *a):
        pass

os.chdir(os.path.dirname(os.path.abspath(__file__)))
s = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
s.daemon_threads = True
with open(sys.argv[1], "w") as f:
    f.write(str(s.server_address[1]))
s.serve_forever()
```

```js
// js44b-features.js
// Is each feature of this batch here? The same script goes to node18, node20 and Chrome.
// Syntax is asked through new Function, so a missing feature does not kill the whole script.
const has = (label, test) => {
  let r;
  try { r = test() ? "yes" : "no"; } catch (e) { r = "no (" + e.constructor.name + ")"; }
  console.log("  " + label.padEnd(50) + r);
};
const syntax = (src) => () => (new Function(src), true);
has("ES2015  Proxy / Reflect", () => typeof Proxy === "function" && typeof Reflect === "object");
has("ES2015  Proxy.revocable", () => typeof Proxy.revocable === "function");
has("ES2020  import() in a classic script", syntax("return import('./nothing.mjs').catch(() => 0)"));
has("ES2025  import() with a second argument", syntax("return import('./nothing.json', { with: { type: 'json' } }).catch(() => 0)"));
has("ES2021  WeakRef / FinalizationRegistry", () => typeof WeakRef === "function" && typeof FinalizationRegistry === "function");
has("        FinalizationRegistry cleanupSome", () => typeof FinalizationRegistry.prototype.cleanupSome === "function");
has("host    require (this script's scope)", () => typeof require === "function");
```

```js
// js44b-gc.js
// Is there a global gc() in this runtime?
console.log("typeof gc: " + typeof gc);
```

```sh
# js44b-versions.sh
#!/usr/bin/env bash
# Which runtime printed each block -- the feature table (js44b-features.js) in all three,
# then whether a global gc() exists with and without the flag that exposes it (js44b-gc.js).
set -u -o pipefail
cd "$(dirname "$0")"
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
for n in "$N18" "$N20"; do
  "$n" -e 'console.log("node " + process.versions.node + "  v8 " + process.versions.v8)'
  "$n" js44b-features.js
done
google-chrome --version | sed 's/ *$//'
./js44b-browser.sh js44b-features.js
echo "gc():"
printf '  %-30s%s\n' "node20" "$("$N20" js44b-gc.js)"
printf '  %-30s%s\n' "node20 --expose-gc" "$("$N20" --expose-gc js44b-gc.js)"
printf '  %-30s%s\n' "Chrome" "$(./js44b-browser.sh js44b-gc.js)"
printf '  %-30s%s\n' "Chrome --js-flags=--expose-gc" "$(./js44b-browser.sh --gc js44b-gc.js)"
```

```text
===== ./js44b-versions.sh (exit=0) =====
node 18.19.1  v8 10.2.154.26-node.28
  ES2015  Proxy / Reflect                           yes
  ES2015  Proxy.revocable                           yes
  ES2020  import() in a classic script              yes
  ES2025  import() with a second argument           yes
  ES2021  WeakRef / FinalizationRegistry            yes
          FinalizationRegistry cleanupSome          no
  host    require (this script's scope)             yes
node 20.19.6  v8 11.3.244.8-node.33
  ES2015  Proxy / Reflect                           yes
  ES2015  Proxy.revocable                           yes
  ES2020  import() in a classic script              yes
  ES2025  import() with a second argument           yes
  ES2021  WeakRef / FinalizationRegistry            yes
          FinalizationRegistry cleanupSome          no
  host    require (this script's scope)             yes
Google Chrome 151.0.7922.173
  ES2015  Proxy / Reflect                           yes
  ES2015  Proxy.revocable                           yes
  ES2020  import() in a classic script              yes
  ES2025  import() with a second argument           yes
  ES2021  WeakRef / FinalizationRegistry            yes
          FinalizationRegistry cleanupSome          no
  host    require (this script's scope)             no
gc():
  node20                        typeof gc: undefined
  node20 --expose-gc            typeof gc: function
  Chrome                        typeof gc: undefined
  Chrome --js-flags=--expose-gc typeof gc: function
```

세 판 대조기의 집계 줄 — 전문은 [3-answer.md](3-answer.md) 의 「실행 검증」에 있다.

`node18 vs node20: identical 7 · differs 2   ·   node20 vs Chrome 151: identical 8 · differs 0 · node only 1`

## 한눈에 — 쉽게 말하면

**정적 `import` 는 「입주 전에 이삿짐을 다 들여놓는 것」이고, `import()` 는 「필요할 때 창고에 전화해 가져오라고 하는 것」이다. 창고는 같은 물건을 두 번 보내지 않는다. 최상위 `await` 는 「짐 하나가 늦게 도착하는 방」이다 — 그 방을 기다려야 하는 사람만 기다리고, 옆방 사람은 먼저 입주한다. import attributes 는 소포에 붙이는 「내용물: JSON」 딱지다 — 관리인(호스트)마다 딱지를 읽는 법이 조금씩 다르다.**

- ★★★ **`import()` 는 부르는 순간 적재한다** — 파일 맨 위의 정적 `import` 와 달리, 그 줄에 닿기 전에는 상대 본문이 **안 돈다.** 두 번 불러도 본문은 **한 번**, 이름공간은 **같은 객체**다.
- ★★★ **최상위 `await` 는 그 모듈을 가져오는 쪽만 세운다** — 형제 모듈은 **안 기다린다.** 가져오는 쪽(`main` · 그 모듈을 `import` 한 형제)은 기다린다.
- ★★★ **`with { type: "json" }` 은 ES2025 문법이다** — node 20 · Chrome 151 은 받고, **node 18.19.1 은 `SyntaxError`**. 옛 `assert { … }` 는 **node 만** 받는다.
- ★★ **실패한 모듈은 실패한 채로 남는다** — 다시 `import()` 해도 본문은 **다시 안 돌고**, **같은 에러 객체**로 거부된다.

```text
   main 이 tla · dep · plain 을 차례로 가져온다 (tla 에 최상위 await, dep 은 tla 를 가져온다)

   시간 ─────────────────────────────────────────────────────────────▶
   tla    ■ before await ··········· 50 ms ··········· ■ after await
   plain         ■ body          ← tla 를 안 기다린다 (형제)
   dep                                                     ■ body   ← tla 를 가져오므로 기다린다
   main                                                          ■ body
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 입주 전에 다 들여놓는 짐 | 정적 `import` — 연결 → 평가, 본문보다 **먼저** | 42번 동작 (4) · 동작 (1)의 `stat44a` |
| 필요할 때 거는 전화 | `import()` — **그 줄에서** 적재·평가, `Promise` | 동작 (1)의 `dyn44a` |
| 같은 물건은 한 번만 보낸다 | 모듈 레코드는 지정자마다 하나 — 본문 한 번 · 이름공간 `===` | 동작 (1) |
| 늦게 오는 짐 | 최상위 `await` — 모듈 평가가 **비동기**가 된다(`[[AsyncEvaluationOrder]]`) | 동작 (2) |
| 기다려야 하는 사람만 기다린다 | 그 모듈에 **의존하는** 모듈만 `[[PendingAsyncDependencies]]` 로 멈춘다 | 동작 (2)의 `dep44b` 대 `plain44b` |
| 반송된 소포는 다시 안 보낸다 | 평가에 실패한 모듈은 `[[EvaluationError]]` 를 들고 남는다 | 동작 (3) |
| 「내용물: JSON」 딱지 | `with { type: "json" }` — **호스트가 읽는다** | 동작 (4) |

**똑같은 구조다** — 실무에서 물리는 자리도 굳어 있다.
「**설정 JSON 을 `import` 하다 node 18 에서 `Unexpected token 'with'`**」,
「**`import cfg from './x.json'` 이 `ERR_IMPORT_ASSERTION_TYPE_MISSING`**」,
「**옛 코드의 `assert { type: 'json' }` 이 브라우저에서 `SyntaxError`**」,
「**초기화 모듈의 최상위 `await` 가 앱 전체의 첫 줄을 늦춘다 — 그런데 옆 모듈은 이미 돌았다**」가 그것이다(동작 (2)·(4)).

> **import attributes** — `import … from "x" with { type: "json" }` 처럼 지정자 옆에 붙이는 **키-값 딱지**(ES2025). 동적 쪽은 `import("x", { with: { type: "json" } })`.\
> 예: `import cfg from "./config.json" with { type: "json" };`

## 이 주제가 답하려는 질문

1. **`import()` 는 언제 상대 본문을 돌리나** — 정적 `import` 와 견주면? 같은 파일을 두 번, 이미 정적으로 가져온 파일을 또 부르면?
2. **최상위 `await` 는 누구를 기다리게 하나** — 형제 모듈인가, 가져오는 쪽인가? 끝내 안 풀리면?
3. **import attributes 는 세 판에서 어느 칸이 통과하고 어느 칸이 무엇으로 막히나** — `with` 대 `assert`, 속성 없음, 모르는 값·키, 이름 있는 가져오기? 그리고 실패한 `import()` 는 무엇으로 거부되나?

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 출력으로 읽는다.

### (1) ★★★ `import()` 는 부르는 순간 — 두 번 불러도 본문은 한 번

**언제 쓰나** — 무거운 모듈을 「그 기능을 쓸 때」 가져오고 싶을 때 · 같은 모듈을 여러 곳에서 `import()` 할 때.

```js
// stat44a.mjs
// Imported statically by main44a.mjs. Prints when its body runs.
console.log("stat44a.mjs: body runs");
export const v = "stat";
```

```js
// dyn44a.mjs
// Only reached through import(). Prints when its body runs.
console.log("dyn44a.mjs: body runs");
export const v = "dyn";
```

```js
// main44a.mjs
// One static import, then import() twice for the same file and once for the statically imported one.
import * as stat from "./stat44a.mjs";
console.log("main44a.mjs: first line");
const p1 = import("./dyn44a.mjs");
const p2 = import("./dyn44a.mjs");
console.log("main44a.mjs: two import() calls made · p1 === p2 " + (p1 === p2));
const [a, b] = await Promise.all([p1, p2]);
console.log("namespace from p1 === namespace from p2 " + (a === b) + " · v = " + a.v);
console.log("import('./stat44a.mjs') === the static namespace " + ((await import("./stat44a.mjs")) === stat));
console.log("main44a.mjs: last line");
```

```text
===== cd js44b-44a && node20 main44a.mjs (exit=0) =====
stat44a.mjs: body runs
main44a.mjs: first line
main44a.mjs: two import() calls made · p1 === p2 false
dyn44a.mjs: body runs
namespace from p1 === namespace from p2 true · v = dyn
import('./stat44a.mjs') === the static namespace true
main44a.mjs: last line
```

Chrome 151 — 같은 파일을 로컬 서버로.

```text
===== ./js44b-browser.sh --http js44b-44a/main44a.mjs (exit=0) =====
stat44a.mjs: body runs
main44a.mjs: first line
main44a.mjs: two import() calls made · p1 === p2 false
dyn44a.mjs: body runs
namespace from p1 === namespace from p2 true · v = dyn
import('./stat44a.mjs') === the static namespace true
main44a.mjs: last line
```

```text
   main44a.mjs 가 돌기 전                main44a.mjs 본문
   ───────────────────────              ───────────────────────────────────────────────
   stat44a 본문  (정적 import — 먼저)     first line
                                        import() ×2   ── p1, p2 : 서로 다른 Promise
                                        (첫 await 에서 쉰다)
                                        ········ dyn44a 본문 — 여기서 한 번만
                                        a === b  (같은 이름공간)
                                        import('./stat44a.mjs') === 정적 이름공간 — 본문 다시 안 돎
                                        last line
```

- ★★★ **`stat44a.mjs: body runs` 가 `main44a.mjs: first line` 보다 먼저, `dyn44a.mjs: body runs` 는 `two import() calls made` 뒤**다. 정적 `import` 는 연결 정보라 **본문 전에**, `import()` 는 **그 식을 평가한 뒤에** 상대를 적재한다(42번 동작 (4)의 「`import` 는 먼저」와 한 쌍).
- ★★★ **두 번 부른 `import()` — `p1 === p2 false` 인데 `namespace from p1 === namespace from p2 true`, 그리고 `dyn44a.mjs: body runs` 는 한 줄**이다. 부를 때마다 **새 프라미스**를 돌려주지만 **모듈은 하나**다.
- ★★ **이미 정적으로 가져온 파일을 `import()` 하면 — `=== the static namespace true`, 본문 줄이 더 없다.** 정적이냐 동적이냐는 **적재 시점**만 바꾸고 모듈 레코드는 같다. 42번 동작 (5)가 잰 「두 번째 `import()` 도 같은 이름공간」을 **정적 쪽과 섞어도** 같다는 것까지 넓혔다.
- ★ **Chrome 151 도 한 글자도 같았다.**

### (2) ★★★ 최상위 `await` 는 가져오는 쪽만 세운다 — 형제는 안 기다린다

**언제 쓰나** — 초기화 모듈에서 설정을 `await` 로 읽을 때 · 그 모듈을 가져오는 쪽과 옆 모듈이 언제 도는지 궁금할 때.

```js
// tla44b.mjs
// A module with top-level await: it waits 50 ms in the middle of its body.
console.log("tla44b.mjs: before await");
await new Promise((r) => setTimeout(r, 50));
console.log("tla44b.mjs: after await");
export const s = "tla";
```

```js
// dep44b.mjs
// Imports tla44b.mjs itself.
import { s } from "./tla44b.mjs";
console.log("dep44b.mjs: body · s = " + s);
```

```js
// plain44b.mjs
// No top-level await, no imports.
console.log("plain44b.mjs: body");
```

```js
// main44b.mjs
// Imports three modules in this order: tla44b (top-level await), dep44b (imports tla44b), plain44b.
import "./tla44b.mjs";
import "./dep44b.mjs";
import "./plain44b.mjs";
console.log("main44b.mjs: body");
```

```text
===== cd js44b-44b && node20 main44b.mjs (exit=0) =====
tla44b.mjs: before await
plain44b.mjs: body
tla44b.mjs: after await
dep44b.mjs: body · s = tla
main44b.mjs: body
```

Chrome 151 — 같은 파일을 로컬 서버로.

```text
===== ./js44b-browser.sh --http js44b-44b/main44b.mjs (exit=0) =====
tla44b.mjs: before await
plain44b.mjs: body
tla44b.mjs: after await
dep44b.mjs: body · s = tla
main44b.mjs: body
```

```text
   가져오는 순서:  tla44b ─▶ dep44b ─▶ plain44b          (main44b 의 import 세 줄 순서)
   실제로 돈 순서:  tla44b(before) ─▶ plain44b ─▶ tla44b(after) ─▶ dep44b ─▶ main44b

   누가 누구를 기다리나 (가져오는 화살표를 거꾸로 따라간다)
     tla44b  ◀── dep44b   : dep44b 는 tla44b 를 가져온다   → 기다린다
     tla44b  ◀── main44b  : main44b 도 가져온다            → 기다린다
     tla44b      plain44b : 서로 가져오지 않는다            → 안 기다린다 — 먼저 돈다
```

- ★★★ **`plain44b.mjs: body` 가 `tla44b.mjs: after await` 보다 먼저**다. `main44b` 가 `plain44b` 를 **세 번째로** 가져오는데도 50 ms 를 안 기다렸다. 최상위 `await` 는 **자기 모듈의 평가를 비동기로 만들 뿐** 형제의 평가를 막지 않는다.
- ★★★ **`dep44b.mjs: body` 는 `after await` 뒤, `main44b.mjs: body` 는 맨 끝**이다. `tla44b` 를 **가져오는** 두 모듈만 기다렸다 — 명세의 `[[PendingAsyncDependencies]]`(아직 안 끝난 비동기 의존 수)가 0 이 되어야 `ExecuteAsyncModule` 로 돈다. 그 계산은 **가져오는 화살표**를 따라서만 한다 — 비동기 모듈이 끝나면 `GatherAvailableAncestors` 가 그 모듈의 `[[AsyncParentModules]]`(**자기를 가져온 모듈들**)만 돌며 수를 하나씩 줄인다.
- ★★ **node 20 · node 18 · Chrome 151 이 한 글자도 같았다** — 평가 순서는 **언어**가 정한다.
- ★ 42번 동작 (4)의 「깊이 우선 · 끝난 것부터」는 그대로다 — 다만 **「끝났다」가 50 ms 뒤로 밀린 모듈**이 있으면 그 모듈에 **매달린 쪽만** 뒤로 밀린다.

끝내 안 풀리는 최상위 `await` 는 어떻게 되나.

```js
// pending44b.mjs
// Top-level await on a promise that never settles.
console.log("pending44b.mjs: before await");
await new Promise(() => {});
console.log("pending44b.mjs: after await");
```

```js
// importer44b.mjs
// Imports pending44b.mjs.
import "./pending44b.mjs";
console.log("importer44b.mjs: body");
```

```sh
# js44b-44b-pending.sh
#!/usr/bin/env bash
# importer44b.mjs imports pending44b.mjs, whose top-level await never settles. Run on node20 and node18:
# standard output, how many lines went to standard error, and the exit code.
set -u -o pipefail
cd "$(dirname "$0")/js44b-44b" || exit 1
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
for v in 20 18; do
  [ $v = 18 ] && n="$N18" || n="$N20"
  echo "--- node$v importer44b.mjs"
  err="$(mktemp -p "$PWD" .err-XXXXXX)"
  "$n" importer44b.mjs 2>"$err"
  e=$?
  echo "(exit $e · standard error: $(grep -c '' "$err" || true) lines)"
  rm -f "$err"
done
```

```text
===== ./js44b-44b-pending.sh (exit=0) =====
--- node20 importer44b.mjs
pending44b.mjs: before await
(exit 13 · standard error: 0 lines)
--- node18 importer44b.mjs
pending44b.mjs: before await
(exit 13 · standard error: 0 lines)
```

- ★★★ **`pending44b.mjs: before await` 한 줄 · `exit 13` · 표준 오류 0 줄**(두 판 같음). `importer44b.mjs: body` 는 **끝내 안 찍혔다** — 가져오는 쪽이 영영 기다린 채 이벤트 루프가 비었다. node 문서 「**끝내 안 풀리면 종료 코드 13**」 그대로다.
- ★★ **경고가 한 줄도 없다** — 이 두 판에서는 **종료 코드만** 이 사실을 말한다. 「출력이 비었다」를 「정상 종료」로 읽으면 틀린다(18-A).
- ★ Chrome 151 에서는 `before await` 한 줄 뒤 **아무것도 안 온다**([3-answer.md](3-answer.md) 5번 — 페이지에는 종료 코드가 없다).

### (3) ★★ 실패한 `import()` — 파싱 실패 · 평가 중 예외 · 그리고 다시 부르면

**언제 쓰나** — 선택 기능을 `import()` 로 가져오다 실패했을 때 **다시 시도**하면 되는지 판단할 때.

```js
// broken44c.mjs
// A module with a syntax error on its second line.
console.log("broken44c.mjs: body runs");
export const x = ;
```

```js
// throws44c.mjs
// A module whose body throws while it is evaluated. It counts its own runs on globalThis.
globalThis.runs44c = (globalThis.runs44c || 0) + 1;
console.log("throws44c.mjs: body runs");
throw new RangeError("thrown while evaluating");
```

```js
// main44c.mjs
// import() of a module that does not parse, and twice of a module that throws.
const show = (e) => e.constructor.name + " 「" + e.message + "」";
try { await import("./broken44c.mjs"); } catch (e) { console.log("[1] import('./broken44c.mjs') rejected: " + show(e)); }
let first;
try { await import("./throws44c.mjs"); } catch (e) { first = e; console.log("[2] import('./throws44c.mjs') rejected: " + show(e)); }
try { await import("./throws44c.mjs"); } catch (e) { console.log("[3] again: " + show(e) + " · same error object " + (e === first)); }
console.log("[4] throws44c.mjs body ran " + globalThis.runs44c + " time(s)");
```

```text
===== cd js44b-44c && node20 main44c.mjs (exit=0) =====
[1] import('./broken44c.mjs') rejected: SyntaxError 「Unexpected token ';'」
throws44c.mjs: body runs
[2] import('./throws44c.mjs') rejected: RangeError 「thrown while evaluating」
[3] again: RangeError 「thrown while evaluating」 · same error object true
[4] throws44c.mjs body ran 1 time(s)
```

Chrome 151 — 같은 파일을 로컬 서버로.

```text
===== ./js44b-browser.sh --http js44b-44c/main44c.mjs (exit=0) =====
[1] import('./broken44c.mjs') rejected: SyntaxError 「Unexpected token ';'」
throws44c.mjs: body runs
[2] import('./throws44c.mjs') rejected: RangeError 「thrown while evaluating」
[3] again: RangeError 「thrown while evaluating」 · same error object true
[4] throws44c.mjs body ran 1 time(s)
```

```text
   import('./broken44c.mjs')   파싱 ✕ ─▶ SyntaxError 로 거부      본문 0 줄 (첫 줄 console.log 도 안 돎)
   import('./throws44c.mjs')   파싱 ○ · 연결 ○ · 평가 중 throw ─▶ RangeError 로 거부   본문 1 번
        다시 import()          모듈 레코드: 상태 evaluated · [[EvaluationError]] = 그 RangeError
                               ─▶ 같은 에러 객체로 거부 (true)                          본문 추가 0 번
```

- ★★★ **문법 오류 모듈 — `SyntaxError 「Unexpected token ';'」` 로 거부, 그 모듈의 첫 줄(`broken44c.mjs: body runs`)도 안 찍혔다.** 파싱이 본문보다 먼저다(42번 동작 (5)의 「블록 안 `import`」와 같은 단계).
- ★★★ **평가 중 던지는 모듈 — 첫 `import()` 는 `RangeError 「thrown while evaluating」`, 두 번째도 같은 문구에 `same error object true`, 본문은 `1 time(s)`.** 모듈은 **실패한 채 남는다** — 명세의 `[[EvaluationError]]` 를 **다시 돌려준다.** 「한 번 더 `import()` 하면 이번엔 될지도」는 **같은 지정자로는 안 된다.**
- ★★ **Chrome 151 도 한 글자도 같았다** — 문구까지(`Unexpected token ';'`). 없는 파일의 거부 모양만 호스트마다 달랐다(42번 동작 (5) — node `ERR_MODULE_NOT_FOUND` · Chrome `TypeError`).

### (4) ★★★ import attributes 판 격자 — 12행 × 세 판

**언제 쓰나** — JSON 파일을 모듈로 가져올 때 · 옛 코드의 `assert { … }` 를 옮길 때 · 여러 node 판과 브라우저를 함께 받아야 할 때.
★★★ 행마다 **새 디렉토리**에 `data.json`(`{"k": 1}`)·`code.mjs`·그 행의 `main.mjs` 를 쓰고 **이 node 로** 돌린다. Chrome 은 **같은 칸 디렉토리**의 `main.mjs` 를 `import()` 로 차례로 부른다.
★★ **두 행이 「같다」의 기준** — 둘 다 `ok` 이고 출력이 같거나, 둘 다 **같은 에러 이름**으로 막혔을 때다. **코드·문구·경고는 비교하지 않는다**(규칙 27 — 문구보다 칸).

```js
// js44b-44d-attributes-grid.js
// Import attributes, one row per cell: a fresh directory holding data.json ({"k": 1}), code.mjs and the row's main.mjs,
// run by this node binary. Prints one line per row: number <TAB> label <TAB> cell.
// cell = "ok " + what main.mjs printed (+ " + warning" if standard error was not empty),
//     or "blocked " + error name + (the [code], or for an error without a code its message).
// A row that printed a warning adds a line: "warning" <TAB> number <TAB> the warning without "(node:<pid>) ".
// The cell directory's file:// URL is replaced by <dir> in every message.
// Also writes js44b-44d-cells/rows.json, so the browser run (js44b-44d-attributes.web.js) loads the same cells.
const fs = require("fs"), path = require("path"), { spawnSync } = require("child_process");
const show = 'console.log(JSON.stringify(d));\n';
const rows = [
  ["static  with { type: 'json' }", 'import d from "./data.json" with { type: "json" };\n' + show],
  ["static  assert { type: 'json' }", 'import d from "./data.json" assert { type: "json" };\n' + show],
  ["static  no attributes", 'import d from "./data.json";\n' + show],
  ["static  with { type: 'css' }", 'import d from "./data.json" with { type: "css" };\n' + show],
  ["static  with { type: 'json', mode: 'x' }", 'import d from "./data.json" with { type: "json", mode: "x" };\n' + show],
  ["static  import { k } ... with { type: 'json' }", 'import { k } from "./data.json" with { type: "json" };\nconsole.log(k);\n'],
  ["static  code.mjs with { type: 'json' }", 'import d from "./code.mjs" with { type: "json" };\n' + show],
  ["import(..., { with: { type: 'json' } })", 'const d = (await import("./data.json", { with: { type: "json" } })).default;\n' + show],
  ["import(..., { assert: { type: 'json' } })", 'const d = (await import("./data.json", { assert: { type: "json" } })).default;\n' + show],
  ["import(...) with no options", 'const d = (await import("./data.json")).default;\n' + show],
  ["static  with { type: 'json', type: 'json' }", 'import d from "./data.json" with { type: "json", type: "json" };\n' + show],
  ["static and import() of the same JSON", 'import a from "./data.json" with { type: "json" };\nconst b = (await import("./data.json", { with: { type: "json" } })).default;\nconsole.log("same object " + (a === b));\n'],
];
const root = path.join(__dirname, "js44b-44d-cells");
fs.rmSync(root, { recursive: true, force: true });
rows.forEach(([label, main], i) => {
  const dir = path.join(root, String(i + 1));
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, "data.json"), '{"k": 1}\n');
  fs.writeFileSync(path.join(dir, "code.mjs"), 'export default "code";\n');
  fs.writeFileSync(path.join(dir, "main.mjs"), main);
  const r = spawnSync(process.execPath, ["main.mjs"], { cwd: dir, encoding: "utf8" });
  const err = r.stderr.split("file://" + dir).join("<dir>");
  let cell;
  if (r.status === 0) cell = "ok " + r.stdout.trim() + (err ? " + warning" : "");
  else {
    const m = err.match(/^(\w*Error)(?: \[(\w+)\])?: (.*)$/m);
    cell = "blocked " + (m ? m[1] + " " + (m[2] || "「" + m[3] + "」") : "?");
  }
  console.log(i + 1 + "\t" + label + "\t" + cell);
  if (r.status === 0 && err) console.log("warning\t" + (i + 1) + "\t" + err.split("\n")[0].replace(/^\(node:\d+\) /, ""));
});
fs.writeFileSync(path.join(root, "rows.json"), JSON.stringify(rows.map((r) => r[0])) + "\n");
```

```js
// js44b-44d-attributes.web.js
// The same cells in the browser: each row's main.mjs through import(), one after another.
// Prints number <TAB> label <TAB> cell, like js44b-44d-attributes-grid.js. The page origin is replaced by <origin>.
(async () => {
  const labels = await (await fetch("js44b-44d-cells/rows.json")).json();
  const log = console.log;
  for (let i = 1; i <= labels.length; i++) {
    const got = [];
    console.log = (...a) => got.push(a.join(" "));
    let cell;
    try { await import("./js44b-44d-cells/" + i + "/main.mjs"); cell = "ok " + got.join(" "); }
    catch (e) { cell = "blocked " + e.constructor.name + " 「" + e.message.split(location.origin).join("<origin>") + "」"; }
    console.log = log;
    console.log(i + "\t" + labels[i - 1] + "\t" + cell);
  }
})();
```

```sh
# js44b-44d-attributes.sh
#!/usr/bin/env bash
# The import-attributes grid on node20 and node18 (js44b-44d-attributes-grid.js), then the same cells in Chrome 151
# (js44b-44d-attributes.web.js) -- and the rows whose answers differ.
# Two rows "agree" when both are ok with the same output, or both are blocked by the same error name
# (error codes, messages and warnings are not compared).
set -u -o pipefail
cd "$(dirname "$0")"
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
a="$("$N20" js44b-44d-attributes-grid.js)" || exit 1
b="$("$N18" js44b-44d-attributes-grid.js)" || exit 1
c="$(./js44b-browser.sh --http js44b-44d-attributes.web.js)" || exit 1
printf '%s\n' "$a" "$b" "$c" | awk -F'\t' 'NF != 3 { print "!! a line without 3 tab-separated fields: " $0; bad = 1 } END { exit bad }' || exit 1
table() { printf '%s\n' "$1" | awk -F'\t' '$1 != "warning" { printf "%3s  %-46s %s\n", $1, $2, $3 }'; }
warnings() { printf '%s\n' "$1" | awk -F'\t' '$1 == "warning" { printf "  row %s: %s\n", $2, $3 }'; }
kinds() { printf '%s\n' "$1" | awk -F'\t' '$1 != "warning" { k = $3; sub(/ \+ warning$/, "", k); if (k ~ /^blocked /) { split(k, w, " "); k = "blocked " w[2] } print k }'; }
echo "--- node20"; table "$a"; warnings "$a"
echo "--- node18"; table "$b"; warnings "$b"
echo "--- Chrome 151"; table "$c"
paste <(kinds "$a") <(kinds "$b") <(kinds "$c") | awk -F'\t' '
  NF != 3 { print "!! rows do not line up"; exit 1 }
  { n++; if ($1 != $2) d12++; if ($1 != $3) d13++; if ($1 != $2 || $1 != $3) d++
    if ($1 ~ /^blocked/) b1++; if ($2 ~ /^blocked/) b2++; if ($3 ~ /^blocked/) b3++ }
  END { print ""
        printf "blocked rows: node20 %d / %d · node18 %d / %d · Chrome %d / %d\n", b1, n, b2, n, b3, n
        printf "rows where node18 and node20 differ: %d / %d\n", d12, n
        printf "rows where node20 and Chrome differ: %d / %d\n", d13, n
        printf "rows where the three do not all agree: %d / %d\n", d, n }'
```

```text
===== ./js44b-44d-attributes.sh (exit=0) =====
--- node20
  1  static  with { type: 'json' }                  ok {"k":1}
  2  static  assert { type: 'json' }                ok {"k":1} + warning
  3  static  no attributes                          blocked TypeError ERR_IMPORT_ASSERTION_TYPE_MISSING
  4  static  with { type: 'css' }                   blocked TypeError ERR_IMPORT_ASSERTION_TYPE_UNSUPPORTED
  5  static  with { type: 'json', mode: 'x' }       blocked TypeError ERR_IMPORT_ATTRIBUTE_UNSUPPORTED
  6  static  import { k } ... with { type: 'json' } blocked SyntaxError 「The requested module './data.json' does not provide an export named 'k'」
  7  static  code.mjs with { type: 'json' }         blocked TypeError ERR_IMPORT_ASSERTION_TYPE_FAILED
  8  import(..., { with: { type: 'json' } })        ok {"k":1}
  9  import(..., { assert: { type: 'json' } })      ok {"k":1} + warning
 10  import(...) with no options                    blocked TypeError ERR_IMPORT_ASSERTION_TYPE_MISSING
 11  static  with { type: 'json', type: 'json' }    blocked SyntaxError 「Import assertion has duplicate key 'type'」
 12  static and import() of the same JSON           ok same object true
  row 2: V8: <dir>/main.mjs:1 'assert' is deprecated in import statements and support will be removed in a future version; use 'with' instead
  row 9: V8: <dir>/main.mjs:1 'assert' is deprecated in import statements and support will be removed in a future version; use 'with' instead
--- node18
  1  static  with { type: 'json' }                  blocked SyntaxError 「Unexpected token 'with'」
  2  static  assert { type: 'json' }                ok {"k":1} + warning
  3  static  no attributes                          blocked TypeError ERR_IMPORT_ASSERTION_TYPE_MISSING
  4  static  with { type: 'css' }                   blocked SyntaxError 「Unexpected token 'with'」
  5  static  with { type: 'json', mode: 'x' }       blocked SyntaxError 「Unexpected token 'with'」
  6  static  import { k } ... with { type: 'json' } blocked SyntaxError 「Unexpected token 'with'」
  7  static  code.mjs with { type: 'json' }         blocked SyntaxError 「Unexpected token 'with'」
  8  import(..., { with: { type: 'json' } })        blocked TypeError ERR_IMPORT_ASSERTION_TYPE_MISSING
  9  import(..., { assert: { type: 'json' } })      ok {"k":1} + warning
 10  import(...) with no options                    blocked TypeError ERR_IMPORT_ASSERTION_TYPE_MISSING
 11  static  with { type: 'json', type: 'json' }    blocked SyntaxError 「Unexpected token 'with'」
 12  static and import() of the same JSON           blocked SyntaxError 「Unexpected token 'with'」
  row 2: ExperimentalWarning: Importing JSON modules is an experimental feature and might change at any time
  row 9: ExperimentalWarning: Importing JSON modules is an experimental feature and might change at any time
--- Chrome 151
  1  static  with { type: 'json' }                  ok {"k":1}
  2  static  assert { type: 'json' }                blocked SyntaxError 「Unexpected identifier 'assert'」
  3  static  no attributes                          blocked TypeError 「Failed to fetch dynamically imported module: <origin>/js44b-44d-cells/3/main.mjs」
  4  static  with { type: 'css' }                   blocked TypeError 「Failed to fetch dynamically imported module: <origin>/js44b-44d-cells/4/main.mjs」
  5  static  with { type: 'json', mode: 'x' }       blocked SyntaxError 「Invalid attribute key "mode".」
  6  static  import { k } ... with { type: 'json' } blocked SyntaxError 「The requested module './data.json' does not provide an export named 'k'」
  7  static  code.mjs with { type: 'json' }         blocked TypeError 「Failed to fetch dynamically imported module: <origin>/js44b-44d-cells/7/main.mjs」
  8  import(..., { with: { type: 'json' } })        ok {"k":1}
  9  import(..., { assert: { type: 'json' } })      blocked TypeError 「Failed to fetch dynamically imported module: <origin>/js44b-44d-cells/9/data.json」
 10  import(...) with no options                    blocked TypeError 「Failed to fetch dynamically imported module: <origin>/js44b-44d-cells/10/data.json」
 11  static  with { type: 'json', type: 'json' }    blocked SyntaxError 「Import attribute has duplicate key 'type'」
 12  static and import() of the same JSON           ok same object true

blocked rows: node20 7 / 12 · node18 10 / 12 · Chrome 9 / 12
rows where node18 and node20 differ: 6 / 12
rows where node20 and Chrome differ: 3 / 12
rows where the three do not all agree: 8 / 12
```

- ★★★ **마지막 네 줄 — 막힌 행 node 20 `7 / 12` · node 18 `10 / 12` · Chrome `9 / 12`, 세 판이 다 같지는 않은 행 `8 / 12`.** 세 판이 **다 같이 통과한 행은 하나도 없다**(행 1 `with` 는 node 18 이, 행 2 `assert` 는 Chrome 이 막았다). 다 같이 막힌 넷은 **속성 없음**(행 3·10) · **이름 있는 가져오기**(행 6) · **키 중복**(행 11)이다.
- ★★★ **`with` 대 `assert`(행 1·2 · 동적 8·9)** —
  node 20 은 **둘 다 통과**(`assert` 는 `V8: … 'assert' is deprecated in import statements …` 경고),
  node 18 은 **`with` 가 `SyntaxError 「Unexpected token 'with'」`, `assert` 만 통과**(`ExperimentalWarning: Importing JSON modules is an experimental feature …`),
  Chrome 151 은 **`with` 만 통과, `assert` 는 `SyntaxError 「Unexpected identifier 'assert'」`**.
  ★ 동적 쪽도 같은 방향이다 — node 18 은 `{ with: … }` 를 **못 읽고** 속성 없음으로 보아 `ERR_IMPORT_ASSERTION_TYPE_MISSING`(행 8), Chrome 은 `{ assert: … }` 를 **못 읽고** 같은 자리에서 막혔다(행 9).
- ★★★ **속성 없이 JSON — 세 판 다 막았다**(행 3·10). node 는 **`ERR_IMPORT_ASSERTION_TYPE_MISSING`**(코드 이름에 아직 **ASSERTION** 이 남아 있다), Chrome 은 `TypeError`. 명세는 **막으라고 하지 않는다**(note — 「`type: "json"` 없이 지원하는 것을 금하지 않는다」) — **막는 것은 호스트의 선택**이다.
- ★★ **모르는 값 `type: 'css'`(행 4)** — node 20 `ERR_IMPORT_ASSERTION_TYPE_UNSUPPORTED`, Chrome `TypeError`. Chrome 이 **무엇 때문에** 막았는지(값을 몰라서인지, JSON 파일을 그 값으로 받을 수 없어서인지)는 콘솔에만 있어 **못 쟀다**(머리말).
- ★★ **모르는 키 `mode`(행 5)** — ★★★ **node 20 은 `TypeError ERR_IMPORT_ATTRIBUTE_UNSUPPORTED`, Chrome 은 `SyntaxError 「Invalid attribute key "mode".」`** — 명세의 `AllImportAttributesSupported` 가 거짓이면 「**SyntaxError**」다. Chrome 은 그 모양이고 node 20 은 **다른 이름**으로 막았다(node 가 키를 엔진에 「지원한다」고 넘긴 뒤 자기 적재기에서 거절하는 것으로 보인다 — ★ 이것은 **해석**이다. node 문서는 「`type` 만 받는다」까지 적는다).
- ★★ **이름 있는 가져오기 `import { k }`(행 6)** — node 20 과 Chrome 은 `SyntaxError 「The requested module './data.json' does not provide an export named 'k'」`(42번의 「없는 이름」과 같은 문구) — **JSON 모듈의 내보내기는 `default` 하나**(`CreateDefaultExportSyntheticModule`). ★ node 18 도 `SyntaxError` 라 격자는 「같다」로 셌지만 **이유가 다르다**(`with` 를 못 읽었다) — **이름만 견주는 기준이 가리는 자리**다.
- ★★ **JS 파일에 `type: 'json'`(행 7)** — node 20 `ERR_IMPORT_ASSERTION_TYPE_FAILED`, Chrome `TypeError`. 딱지는 **요청**이 아니라 **검사**다 — 내용이 딱지와 다르면 막는다.
- ★★ **키 중복 `type` 두 번(행 11)** — Chrome `SyntaxError 「Import attribute has duplicate key 'type'」`, node 20 은 `SyntaxError 「Import assertion has duplicate key 'type'」` — 같은 V8 계열인데 **node 20(V8 11.3)의 문구에는 아직 `assertion`** 이 남아 있다. 둘 다 명세의 조기 오류(키가 겹치면 `SyntaxError`) 그대로다.
- ★★ **정적과 동적으로 같은 JSON(행 12)** — `same object true`(node 20 · Chrome). 딱지까지 같으면 **같은 모듈**이다.

```text
                       node 18.19.1              node 20.19.6                  Chrome 151
   with { type }       ✕ SyntaxError (with)      ○                             ○
   assert { type }     ○ + ExperimentalWarning   ○ + 'assert' is deprecated     ✕ SyntaxError (assert)
   (속성 없음)          ✕ ..._TYPE_MISSING        ✕ ..._TYPE_MISSING            ✕ TypeError
   import(x, {with})   ✕ ..._TYPE_MISSING        ○                             ○
   import(x, {assert}) ○                         ○ + 경고                        ✕ TypeError

   ○ 가 세 판 다에 있는 줄이 없다 — 세 판을 다 받으려면 `with` 도 `assert` 도 한 벌로는 안 된다
```

## 문법 — 형태와 규칙

★ 이 절은 **형태 표**다 — 모든 동작 주장은 위 동작 절의 캡처 블록에서만 한다.

| 형태 | 하는 일 | 판 | 어디서 봤나 |
|---|---|---|---|
| `import("./x.mjs")` | 그 줄에서 적재·평가 → **`Promise`**(이름공간) | ES2020 | 동작 (1) · 42번 |
| `await` (모듈 최상위) | 모듈 평가를 비동기로 — **가져오는 쪽만** 기다린다 | ES2022 | 동작 (2) |
| `import d from "./x.json" with { type: "json" }` | JSON 모듈 — **`default` 하나** | ES2025 | 동작 (4) 행 1·6 |
| `import("./x.json", { with: { type: "json" } })` | 동적 쪽 — 결과의 `.default` | ES2025 | 동작 (4) 행 8 |
| `… assert { type: "json" }` · `{ assert: … }` | ★ **표준 아님** — node 만(경고) | — | 동작 (4) 행 2·9 |

- **`with` 의 키가 겹치면 `SyntaxError`**(명세의 조기 오류) — 돌려 보지 않았다(명세 문장만).
- **JSON 모듈에서 이름 있는 가져오기는 없다** — `import { k }` 는 `SyntaxError`(동작 (4) 행 6).
- **`import()` 의 결과는 이름공간 객체다** — JSON 의 값은 **`.default`** 에 있다.

## 어디서 틀리나

### (1) ★★★ 「`import()` 로 바꾸면 초기 로딩이 줄어든다」를 근거로 쓴다

**이 문서는 재지 않았다.** 보인 것은 「**그 줄에 닿기 전에는 본문이 안 돈다**」는 **순서**뿐이다(동작 (1)). 무엇을 얼마나 아끼는지는 번들러·호스트·네트워크가 정한다.

### (2) ★★★ 최상위 `await` 가 「그 뒤의 모든 모듈」을 멈춘다고 믿는다

**가져오는 쪽만** 멈춘다 — 형제 `plain44b` 는 50 ms 를 안 기다리고 **먼저** 돌았다(동작 (2)). 「초기화가 끝난 뒤에 돌 것」을 기대하는 모듈은 그 초기화 모듈을 **직접 `import`** 해야 한다.

### (3) ★★★ node 18 에서 `with { type: "json" }` 을 쓴다

**`SyntaxError 「Unexpected token 'with'」`** — 파일 전체가 파싱 단계에서 죽는다(동작 (4) 행 1). node 문서 이력상 **v18.20.0** 에서 전환됐고 이 머신의 **v18.19.1** 은 그 전 판이다.

### (4) ★★★ 옛 `assert { type: "json" }` 을 그대로 둔다

node 20 은 **경고와 함께** 받지만 **Chrome 151 은 `SyntaxError`** 다(동작 (4) 행 2). 명세에 없는 문법이다.

### (5) ★★ JSON 을 속성 없이 `import` 한다

세 판 다 막았다 — node **`ERR_IMPORT_ASSERTION_TYPE_MISSING`**(동작 (4) 행 3·10). 명세가 금하지 않는데도 **호스트가** 막는다.

### (6) ★★ JSON 모듈에서 이름을 꺼낸다

`import { k } from "./x.json" with { type: "json" }` 은 **`SyntaxError`** — `default` 를 받아 구조 분해한다(동작 (4) 행 6).

### (7) ★★ 실패한 `import()` 를 같은 지정자로 다시 시도한다

**같은 에러 객체로 다시 거부되고 본문은 안 돈다**(동작 (3)). 모듈은 실패한 채 레코드에 남는다.

### (8) ★ 끝내 안 풀리는 최상위 `await` 를 「출력 없음 = 정상」으로 읽는다

**`exit 13`**, 경고 0 줄(동작 (2)). 종료 코드를 봐야 안다.

## 구현 세부사항 대 언어 보장

### 명세 보장(ECMA-262)

- ★★★ **`import()` 는 부르는 순간** 적재·연결·평가를 시작하고 **`Promise`** 를 돌려준다 · 같은 모듈이면 **같은 이름공간**.
- ★★★ **최상위 `await` 의 평가 순서** — 비동기 모듈에 **의존하는** 모듈만 `[[PendingAsyncDependencies]]` 로 멈춘다. 형제는 멈추지 않는다(동작 (2) — 세 판 같음).
- ★★ **평가에 실패한 모듈은 `[[EvaluationError]]` 를 다시 돌려준다** — 본문을 다시 돌리지 않는다(동작 (3)).
- ★★ **`with { … }` 문법**(ES2025) · 지원 안 하는 키는 **`SyntaxError`** · JSON 모듈의 내보내기는 **`default` 하나**.

### 호스트

- ★★★ **어느 속성 키를 받나** — `HostGetSupportedImportAttributes`. node 는 **`type` 만**(문서).
- ★★★ **속성 없는 JSON 을 막나** — 명세는 금하지 않는다. **세 판 다 막았다**(node `ERR_IMPORT_ASSERTION_TYPE_MISSING` · Chrome `TypeError`).
- ★★ **모르는 `type`·모르는 키의 거절 모양** — node 20 은 `TypeError` + `ERR_…` 코드, Chrome 은 모르는 키에 `SyntaxError`(명세의 모양).
- ★ **끝내 안 풀린 최상위 `await` 의 종료 코드 13** — node 의 것.

### 구현(V8) · 이 판의 관찰

- ★★★ **`assert { … }` 를 받는 것** — 표준이 아니다. node 18(V8 10.2)·node 20(V8 11.3)은 받았고 **Chrome 151 은 버렸다** — 경고 문구가 「**support will be removed in a future version**」라고 스스로 적는다.
- ★ node 의 에러 코드 이름 — `ASSERTION` 이 남은 `ERR_IMPORT_ASSERTION_TYPE_MISSING` 과 새 이름 `ERR_IMPORT_ATTRIBUTE_UNSUPPORTED` 가 **한 판에 섞여 있다.**

### 그래서 이렇게 적으면 틀린다

- ✗ 「최상위 `await` 는 모듈 그래프 전체를 멈춘다」 → ○ 「**그 모듈을 가져오는 쪽만** — 형제는 먼저 돈다」
- ✗ 「JSON 모듈은 ES2025 부터 표준이라 node 18 에서도 된다」 → ○ 「**node 18.19.1 은 `with` 를 파싱하지 못한다** — `assert` 로만 됐다」
- ✗ 「`type: "json"` 을 빼면 명세 위반이다」 → ○ 「명세는 **빼도 금하지 않는다** — 막는 것은 **호스트**다(세 판 다 막았다)」
- ✗ 「실패한 `import()` 는 다시 부르면 다시 시도된다」 → ○ 「**같은 에러로 거부**되고 본문은 안 돈다」

## 언제 쓰고 언제 안 쓰나

- **`import()`** — 조건·사용 시점에 따라 모듈을 고를 때 · CommonJS 에서 ESM 을 쓸 때(43번). 결과가 **프라미스**라는 비용을 받아들인다.
- **최상위 `await`** — 초기화가 **정말 비동기이고** 그 값을 쓰는 모듈이 **직접 가져올 때.** 옆 모듈이 기다려 주리라 기대하지 않는다.
- **JSON 모듈** — node 20 · 브라우저 대상이면 **`with { type: "json" }`**. node 18 까지 받아야 하면 **`fs` 로 읽고 `JSON.parse`**(31번) 쪽이 판을 안 탄다 — `with` 도 `assert` 도 **한 벌로 세 판을 못 덮었다**(동작 (4)의 그림).
- ★ **안 쓰는 자리** — `assert { … }` 새로 쓰기 · 실패한 `import()` 를 같은 지정자로 재시도하기 · 끝내 안 풀릴 수 있는 프라미스를 최상위에서 `await` 하기.

## 핵심 문장

1. ★★★ **`import()` 는 부르는 순간** 적재한다 — 정적 `import` 의 본문은 `first line` 전에, `import()` 의 본문은 그 호출 뒤에 돌았다. 두 번 불러도 **본문 한 번 · 같은 이름공간**(프라미스는 매번 새것).
2. ★★★ **최상위 `await` 는 가져오는 쪽만 세운다** — `tla(before) → plain → tla(after) → dep → main`. 끝내 안 풀리면 **`exit 13` · 경고 0 줄.**
3. ★★★ import attributes 격자 — 막힌 행 node 20 `7 / 12` · node 18 `10 / 12` · Chrome `9 / 12`, **세 판이 다 같지는 않은 행 `8 / 12`**. `with` 는 node 18 이, `assert` 는 Chrome 이 막았다.
4. ★★ **속성 없는 JSON 은 세 판 다 막았다** — 명세는 금하지 않으니 **호스트의 선택**이다. JSON 모듈의 내보내기는 **`default` 하나.**
5. ★★ 평가에 실패한 모듈은 **실패한 채 남는다** — 다시 `import()` 해도 **같은 에러 객체**, 본문은 안 돈다.

## 관련 자료

- [ECMA-262 — Scripts and Modules](https://tc39.es/ecma262/multipage/ecmascript-language-scripts-and-modules.html) · [TC39 finished proposals](https://github.com/tc39/proposals/blob/main/finished-proposals.md) · [Node.js v20 — ECMAScript modules](https://nodejs.org/docs/latest-v20.x/api/esm.html) · [Node.js v18 — ECMAScript modules](https://nodejs.org/docs/latest-v18.x/api/esm.html)
- [42 — ESM 모듈](../42-esm-modules/2-summary.md) — ★ **경계**: 정적 `import` 의 연결·평가·라이브 바인딩, `import()` 가 식이라는 것까지는 거기. 여기는 **부르는 순간 · 최상위 `await` 의 순서 · 실패 · 속성**부터.
- [43 — CJS 와 ESM 상호운용](../43-cjs-and-esm-interop/2-summary.md) — CommonJS 에서의 `import()` · 최상위 `await` 가 든 ESM 의 `require`.
- [39 — `async`/`await`](../39-async-await/2-summary.md) · [31 — JSON](../31-json/2-summary.md) · [36 — 이벤트 루프](../36-event-loop-and-microtasks/2-summary.md)(모듈 본문이 마이크로태스크를 비우는 중에 돈다).

## 용어 풀이

- **동적 `import()`** — 식으로 쓰는 가져오기. 지정자를 실행 중에 정하고 **`Promise`**(이름공간 객체)를 받는다(ES2020).
- **최상위 `await`(top-level await)** — 모듈 본문 최상위에서 쓰는 `await`(ES2022). 그 모듈의 평가가 **비동기**가 된다.
- **비동기 모듈 평가** — 최상위 `await` 가 있는 모듈과 그에 **의존하는** 모듈이 `[[AsyncEvaluationOrder]]` 으로 표시되어, 의존이 끝난 뒤 차례로 도는 명세의 규칙.
- **`[[EvaluationError]]`** — 평가에 실패한 모듈 레코드가 들고 있는 예외. 다시 평가를 요청하면 **이것을 그대로** 돌려준다.
- **import attributes** — 지정자 옆의 `with { 키: "값" }`(ES2025). 호스트가 어느 키를 받을지 정한다.
- **import assertions** — 같은 자리에 `assert { … }` 를 쓰던 **옛 제안**. 표준에 들어가지 않았다.
- **JSON 모듈** — `type: "json"` 으로 가져오는 JSON 파일. 내보내기는 **`default` 하나**(ES2025).
- **`ERR_IMPORT_ASSERTION_TYPE_MISSING`** — node 가 JSON 을 속성 없이 가져올 때 내는 코드.

## 더 들어가면

- **순환 + 최상위 `await`** — 순환 안에 비동기 모듈이 끼면 `[[CycleRoot]]` 가 평가 단위가 된다. 이 문서는 순환 없는 그래프만 돌렸다(순환은 42번 동작 (3)).
- **node 22 계열의 `assert` 제거** — 이 머신에 22 가 없어 **돌리지 않았다.** node 20 경고가 「future version」이라고만 적는다.
- **CSS 모듈(`type: "css"`)** — Chrome 의 호스트 기능이다. 격자 행 4 가 무엇으로 막혔는지는 콘솔로만 보인다.
