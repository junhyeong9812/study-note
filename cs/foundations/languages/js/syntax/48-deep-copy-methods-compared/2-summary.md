# js/syntax/48 — 깊은 복사 수단 비교: 「넷 중 셋은 명세가 정한 얕은 길이고 하나만 호스트가 준 깊은 길이다 — 그 깊은 길도 프로토타입·getter·심볼 키는 못 옮긴다」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> ★★★ **이 주제의 본체는 ② 보존 격자다** — 값 **17행**(브리핑의 16종 + 「중첩 평범한 객체」) × 수단 **넷**(JSON 왕복 · 스프레드 `{ ...o }` · `Object.assign({}, o)` · `structuredClone`) = **68칸**을 칸마다 `kept`(새 값으로 보존) · `shared`(원본의 **그 객체**를 그대로 — `===`) · `-> 무엇`(변형) · `throws 생성자/이름`(던짐) 넷 중 하나로 찍고, **스크립트가 마지막 두 줄로 센다**(동작 (1)). 판은 **node 18 · node 20 · Chrome 151** 셋이다.
> ★★ 보조로 **④ 예외의 이름 + 문구**(`DataCloneError` — 호스트마다 문구가 다르다 · 동작 (3)) · **① 로그 심기**(복사하는 동안 getter 를 몇 번 읽나 · 동작 (3)) · **교차 갈래 한 쌍**(CPython `copy.deepcopy` · 동작 (4))을 쓴다.
>
> **기준 소스** — 열어서 확인한 것만.
> - ★★★ **이 배치는 명세를 새로 열지 못했다**(외부 네트워크를 쓰지 않았다). 명세 층의 진술은 **형제 편이 연 판에서 확인한 연산 이름**을 인용한다 — [11 — 스프레드와 나머지](../11-spread-and-rest/2-summary.md)(객체 스프레드 = `CopyDataProperties`) · [27 — `Object` 정적 메서드](../27-object-static-methods/2-summary.md)(`Object.assign`) · [31 — `JSON`](../31-json/2-summary.md)(`SerializeJSONProperty` 등).
> - ★★ **`structuredClone` 은 ECMA-262 가 아니라 호스트 API 다** — 이 목록의 README 가 「MDN 은 호스트 API(`AbortController`·`structuredClone`)에서만 근거로 쓴다」고 적어 둔 그 API 다. ★ **HTML 표준의 해당 절(구조적 직렬화)은 이 문서가 읽지 않았다** — 그래서 `structuredClone` 칸은 전부 **세 호스트의 관찰**로만 적는다(아래 「창」 표의 제5의 상태).
>
> **실행 검증** — 이 문서의 모든 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다.
> 배너의 `node20` 은 v20.19.6, `node18` 은 v18.19.1, 파이썬은 `python3`(3.12.3). Chrome 은 아래 하네스(`--dump-dom`)로 돌렸다 — ★ **이 묶음(48\~52)의 하네스 소스는 이 머리말에 싣는다.**
> ★★★ **성능은 재지 않았다** — 「`structuredClone` 이 JSON 왕복보다 빠르다/느리다」를 **한 줄도 쓰지 않는다**(31번 · 27번과 같은 선).
>
> **버전** — 객체 스프레드 **ES2018** · `Object.assign` **ES2015** · `JSON` **ES5** · `Error` 의 `cause` **ES2022** · `structuredClone` 은 **언어 판이 없다**(호스트 API — 세 판 다 있다: 31번 판별 블록).
>
> **★★★ 층 — 이 문서의 결론이 기대는 세 층**
>
> | 층 | 무엇 | 어디서 |
> |---|---|---|
> | ★★★ **ECMA-262** | JSON 왕복 · 스프레드 · `Object.assign` 세 열 전부 — 얕다(`shared`) · getter 를 **읽어서** 데이터 속성으로 굳힌다 · 프로토타입을 안 옮긴다 · 심볼 키는 스프레드·`assign` 이 옮기고 JSON 은 뺀다 | 동작 (1)의 왼쪽 세 열 |
> | ★★ **HTML(호스트 API)** | `structuredClone` 열 — 깊다 · 공유와 순환을 지킨다 · 함수·심볼 값·`WeakMap`·`Promise` 는 `DOMException`(이름 `DataCloneError`) · `transfer` 선택지 | 동작 (1)의 `clone` 열 · 동작 (3) |
> | ★★ **구현(V8·호스트)의 관찰** | 예외 **문구**(Chrome 만 `Failed to execute 'structuredClone' on 'Window': ` 가 앞에 붙는다) · 복사본의 `stack` 이 원본과 같은 글자 · `Error` 하위 클래스가 `Error` 로 떨어지는 것 · `cause` 가 따라오는 것 | 동작 (3) |
>
> **★★★ 이 주제가 쓰는 창 — 그리고 부적용인 창**
>
> | 창 | 이 주제에서 무엇을 보나 |
> |---|---|
> | ★★★ **② 보존 격자**(본체의 도구) | 17행 × 4열 — 「`cells shared with the source (===): N / 68`」 · 「`cells not preserved (-> or throws): N / 68`」 · 열마다 센 줄 두 개 · 판 셋 비교 두 줄(동작 (1)) |
> | ★★ **④ 예외의 이름 + 문구** | `structuredClone` 이 거절하는 다섯 값 — 생성자 · `name` · `code` · 문구(동작 (3) `[1]`) |
> | ★ **① 로그 심기** | 복사하는 동안 getter 가 몇 번 불리나(`reads 1` — 동작 (3) `[3]`) |
> | ★★ **교차 갈래 한 쌍** | CPython `copy.deepcopy` — 클래스 · 예외 · 함수(동작 (4)) |
> | ★★★ **「못 잰 것」 이 아니라 「창을 바꿔 물었다」**(제5의 상태) | 「`structuredClone` 이 이 값을 어떻게 다뤄야 하나」는 원래 **HTML 명세를 읽어** 답할 질문인데 이 배치는 그 창을 못 열었다. 그래서 **같은 질문을 세 호스트에 던졌다**(node 18 · node 20 · Chrome 151 — 격자 68칸이 한 글자도 같았다). ★ **바꾼 창이 못 보는 것** — 세 호스트가 **모두 V8** 이라, 같은 답이 「HTML 이 그렇게 정했다」인지 「V8 이 그렇게 한다」인지는 **가르지 못한다**(특히 `Error` 의 `cause`·`stack` 칸) |
> | ★ **부적용 — 성능** | 시간도 바이트도 안 쟀다. 이 주제의 질문(「무엇을 잃나」)에는 필요 없는 창이다 |
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 판별 블록의 판 문자열 · `DataCloneError` 의 **문구**(호스트가 다르면 글자가 다르다 — node 와 Chrome 이 이미 달랐다) | ★★★ 격자 68칸 · 마지막 네 줄 · 판 비교 두 줄 · 동작 (3)의 생성자·`name`·`code`·참/거짓 · 동작 (4) — **재대조 동일** |
>
> **선행** — [31 — `JSON`](../31-json/2-summary.md)(직접 선행 — ★★★ **이미 쟀다**: JSON 왕복 대 `structuredClone` 13행 · node 20 · 「`rows where the two columns differ: 11 / 13`」 — 거기 동작 (5). ★ 이 문서는 그 13행을 **다시 따로 싣지 않고** 두 열을 더해(스프레드·`assign`) · 네 행을 더해(심볼 키 · `Error` · `Uint8Array` · 중첩 객체) · 판을 셋으로 늘린 **한 격자**로 다시 묻는다) ·
> [11 — 스프레드와 나머지](../11-spread-and-rest/2-summary.md)(「**얕다**」 — 거기 동작 (3)) ·
> [27 — `Object` 정적 메서드](../27-object-static-methods/2-summary.md)(★★ 복사 도구 넷 × 성질 여섯 격자 「`3 / 18`」 · **복사본의 `inner` 를 고치면 원본도 `99`** 가 거기 동작 (2) `[3]` 에 있다 — 이 문서는 그 쓰기 실험을 다시 하지 않는다) ·
> [25 — 배열 비변경·복사 메서드](../25-array-non-mutating-and-copy-methods/2-summary.md)(배열 쪽 「한 겹」) ·
> [16 — `class` 문법](../16-class-syntax/2-summary.md)(`structuredClone(inst)` 가 `#private` 필드를 안 옮긴다 — 거기 동작 (1) `[3]` 의 `{"field":"f"}`).
>
> ★★ **경계** — 워커 `postMessage` 가 무엇을 넘길 수 있나는 web-api 갈래 목록([`web-api/README.md`](../../../../web-api/README.md))의 **47번**, 전송(`Transferable`)과 공유 메모리는 같은 목록의 **48번**이 정본이다. 여기는 **한 스레드 안에서 복사본이 무엇을 잃나**만 다루고, `transfer` 는 동작 (3) `[4]` 의 세 줄로만 둔다.
>
> ★★ **교차 갈래** — [Python 03 — 가변성과 복사](../../../python/syntax/03-mutability-and-copying/2-summary.md)(「6. 깊은 복사와 순환 참조 — `memo` 가 하는 일」 — `deepcopy` 도 **공유와 순환을 지킨다** · 함수는 `is` 원본). 동작 (4)는 그 편이 안 본 **클래스·예외** 두 행만 더한다.

```text
===== ./js48b-versions.sh (exit=0) =====
node 18.19.1  v8 10.2.154.26-node.28  icu 74.2  tz 2023c  unicode 15.1  cldr 44.1
node 20.19.6  v8 11.3.244.8-node.33  icu 77.1  tz 2025b  unicode 16.0  cldr 47.0
Google Chrome 151.0.7922.173
```

이 묶음의 Chrome 하네스 — 페이지가 `console.log` 를 가로채 `<pre>` 에 쓰고, 셸 스크립트가 `--dump-dom` 으로 그 글자를 꺼낸다.

```sh
# js48b-browser.sh
#!/usr/bin/env bash
# Run probe scripts in headless Chrome and print what they logged.
#   usage: ./js48b-browser.sh [--gc] [--http] <script>[,<script>...]
# Default: file:// with --allow-file-access-from-files (without it a file:// script counts as cross-origin -- "muted errors").
# --http: through js48b-serve.py on 127.0.0.1 -- module scripts (.mjs) need it.
# --gc: start Chrome with --js-flags=--expose-gc, so the page has a global gc().
# Every run gets its own throwaway profile directory, so several runs can go at once.
# The page sees the TZ and LANG this script is started with.
# --dump-dom writes HTML entities, so the last sed turns them back.
set -u -o pipefail
cd "$(dirname "$0")"
flags=()
if [ "$1" = "--gc" ]; then flags=(--js-flags=--expose-gc); shift; fi
if [ "$1" = "--http" ]; then
  shift
  pf="$(mktemp -p "$PWD" .port-XXXXXX)"
  python3 js48b-serve.py "$pf" > /dev/null 2>&1 &
  srv=$!
  for _ in $(seq 100); do [ -s "$pf" ] && break; sleep 0.05; done
  url="http://127.0.0.1:$(cat "$pf")/js48b-page.html?$1"
  rm -f "$pf"
else
  srv=
  url="file://$PWD/js48b-page.html?$1"
fi
prof="$(mktemp -d -p "$PWD" .profile-XXXXXX)"
google-chrome --headless --user-data-dir="$prof" --allow-file-access-from-files "${flags[@]}" --virtual-time-budget=60000 --dump-dom "$url" 2>/dev/null \
  | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' \
  | sed 's/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&amp;/\&/g'
rc=$?
rm -rf "$prof"
[ -n "$srv" ] && kill "$srv"
exit $rc
```

```html
<!-- js48b-page.html -->
<!doctype html>
<meta charset="utf-8">
<title>js48b</title>
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

```python
# js48b-serve.py
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

## 한눈에 — 쉽게 말하면

**복사는 이삿짐 싸기다. JSON 왕복은 「모든 짐을 글로 적어 보내고 새 집에서 글을 보고 다시 사는 것」이라 글로 못 적는 물건(날짜 객체·`Map`·함수)은 모양이 바뀌거나 사라진다. 스프레드와 `Object.assign` 은 「상자 겉면의 목록만 새로 쓰고 안의 물건은 옛집 것을 그대로 가리키는 것」이다. `structuredClone` 은 「진짜로 물건을 하나하나 새로 만들어 옮기는 이삿짐센터」인데, 이 센터도 살아 있는 것(함수)은 안 받고, 집주인의 족보(프로토타입)와 자동 장치(getter)는 옮기지 않는다.**

- ★★★ **JSON 왕복은 17행 중 16행에서 잃는다** — 보존한 것은 **중첩 평범한 객체** 한 행뿐이다(동작 (1)).
- ★★★ **스프레드·`assign` 은 얕다** — 두 열 다 **10칸이 `shared`**(원본의 그 객체). 「잃은 것」으로 세면 두 칸뿐이라 **가장 잘 보존한 것처럼 보인다** — 그게 함정이다(동작 (2)).
- ★★★ **`structuredClone` 도 네 칸을 잃는다** — 함수(던짐) · 심볼 키 · 클래스 인스턴스의 프로토타입 · getter(동작 (1)).
- ★★ **넷 다 잃는 행이 둘** — 클래스 인스턴스(`-> plain {"x":1}`)와 getter(`-> data property 1`).

```text
                        JSON 왕복          스프레드 · assign        structuredClone
   Date·Map·Set·RegExp   -> 다른 모양        shared (같은 객체)       kept (새 객체)
   NaN · -0 · BigInt     -> null · 0 · 던짐   kept                    kept
   함수                   -> 키가 사라짐       shared                  throws DataCloneError
   심볼 키                -> 키가 사라짐       kept                    -> 키가 사라짐
   순환 · 같은 객체 두 번   던짐 · 두 객체       shared                  kept (모양까지)
   클래스 인스턴스 · getter  ─────────────── 넷 다 평범한 객체 · 데이터 속성 ───────────────
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 글로 적어 보내기 | `JSON.parse(JSON.stringify(o))` — 글자를 거쳐 다시 만든다 | 동작 (1) `JSON` 열 |
| 겉면 목록만 새로 쓰기 | `{ ...o }` · `Object.assign({}, o)` — 한 겹만 새 객체 | 동작 (1) `shared` 칸 · 동작 (2) |
| 이삿짐센터 | `structuredClone(o)` — 호스트 API, 그래프째 새로 만든다 | 동작 (1) `clone` 열 |
| 살아 있는 것은 안 받는다 | 함수·심볼 값·`WeakMap`·`Promise` → `DataCloneError` | 동작 (3) `[1]` |
| 족보는 안 옮긴다 | 프로토타입 — 넷 다 평범한 객체가 된다 | 동작 (1) `class instance` 행 |
| 자동 장치를 그 순간의 값으로 | getter 를 한 번 읽어 **데이터 속성**으로 | 동작 (1) `getter` 행 · 동작 (3) `[3]` |

**똑같은 구조다** — 실무에서 물리는 자리도 굳어 있다.
「**상태를 `{ ...state }` 로 복사해 두고 고쳤더니 안쪽 배열이 원본까지 바뀌었다**」,
「**`JSON.parse(JSON.stringify(x))` 로 복사한 뒤 `x.createdAt.getTime()` 이 `TypeError`**(문자열이 됐다)」,
「**`structuredClone` 으로 복사한 모델 객체에서 메서드가 사라졌다**(프로토타입을 잃었다)」가 그것이다.

> **깊은 복사(deep copy)** — 바깥 객체뿐 아니라 **안에 든 객체까지 새로 만든** 복사. 원본과 복사본이 **어떤 객체도 공유하지 않는다**.\
> 예: `const c = structuredClone(o); c.inner !== o.inner`

## 이 주제가 답하려는 질문

1. **네 수단은 각 값을 보존하나, 공유하나, 바꾸나, 던지나** — 칸마다, 그리고 판마다 같은가?
2. **「잃은 칸이 적다」와 「깊게 복사했다」는 같은 말인가** — 스프레드·`assign` 의 `shared` 칸은 무엇을 뜻하나?
3. **`structuredClone` 은 무엇을 거절하고, 받은 것 중 무엇을 떨어뜨리나** — `Error`·getter·프로토타입은? 그리고 그 답은 **누가** 정하나?

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 출력으로 읽는다.

### (1) ★★★ 보존 격자 — 17행 × 4수단 × 판 셋

**언제 쓰나** — 「이 객체를 복사하는데 무엇으로 하지」를 고를 때.
★★ 판정은 넷이다 — `kept` 는 **같은 값이되 원본의 객체가 아닌 것**(원시 값이면 같은 값), `shared` 는 **원본의 그 객체**(`===`), `-> 무엇` 은 **다른 것**, `throws` 는 복사 자체가 던진 것. ★ `shared` 를 따로 세는 이유 — 「값이 같다」로만 보면 **얕은 복사가 전부 합격**한다.

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

```text
===== ./js48b-48a-copy-grid.sh (exit=0) =====
--- node20
                     JSON                                  spread                 assign                 clone
Date                 -> string "1970-01-01T00:00:00.000Z"  shared                 shared                 kept
Map                  -> plain {}                           shared                 shared                 kept
Set                  -> plain {}                           shared                 shared                 kept
RegExp               -> plain {}                           shared                 shared                 kept
undefined property   -> key gone                           kept                   kept                   kept
NaN                  -> null                               kept                   kept                   kept
-0                   -> number 0                           kept                   kept                   kept
BigInt               throws TypeError/TypeError            kept                   kept                   kept
function             -> key gone                           shared                 shared                 throws DOMException/DataCloneError
symbol key           -> key gone                           kept                   kept                   -> key gone
cycle                throws TypeError/TypeError            shared (c.me === src)  shared (c.me === src)  kept
class instance       -> plain {"x":1}                      -> plain {"x":1}       -> plain {"x":1}       -> plain {"x":1}
getter               -> data property 1                    -> data property 1     -> data property 1     -> data property 1
same object twice    -> two objects                        shared                 shared                 kept
Error with cause     -> plain {}                           shared                 shared                 kept
Uint8Array           -> plain {"0":1,"1":2}                shared                 shared                 kept
nested plain object  kept                                  shared                 shared                 kept

per column, kept:          JSON 1 · spread 5 · assign 5 · clone 13
per column, shared:        JSON 0 · spread 10 · assign 10 · clone 0
per column, not preserved: JSON 16 · spread 2 · assign 2 · clone 4
cells shared with the source (===): 20 / 68
cells not preserved (-> or throws): 24 / 68

node18 prints the same as node20: yes
Chrome 151 prints the same as node20: yes
```

```text
                  kept    shared    ->/throws           (열마다 17칸)
   JSON             1       0         16
   spread          5       10         2       <- 잃은 칸은 적지만 10칸이 원본과 같은 객체
   assign          5       10         2       <- spread 와 한 칸도 다르지 않다
   clone          13        0         4       <- 공유 0 · 잃은 넷: 함수 · 심볼 키 · 프로토타입 · getter
                  ───────────────────────────
   68칸 중                  20         24     <- 마지막 두 줄
```

- ★★★ **마지막 두 줄 — `cells shared with the source (===): 20 / 68` · `cells not preserved (-> or throws): 24 / 68`.** 그림의 세 열은 출력의 「per column」 세 줄을 그대로 옮긴 것이다(`kept` 1 · 5 · 5 · 13).
- ★★★ **판 셋이 한 글자도 같았다** — `node18 prints the same as node20: yes` · `Chrome 151 prints the same as node20: yes`. ★ 「같았다」는 관찰이다 — 세 판이 **모두 V8** 이라는 점은 머리말 「창」 표에 적었다.
- ★★★ **JSON 열 — 잃은 칸 16.** 보존은 `nested plain object` 한 칸뿐이다. 31번이 13행에서 본 손실(`Date` → 문자열 · `Map`/`Set`/`RegExp` → `{}` · `undefined` 속성 → 키가 사라짐 · `NaN` → `null` · `-0` → `0` · `BigInt`·순환 → `TypeError` · 공유 → 두 객체)이 그대로이고, 새로 넣은 행도 전부 잃었다 — **심볼 키 → 키가 사라짐 · `Error` → `plain {}` · `Uint8Array` → `plain {"0":1,"1":2}`**.
- ★★★ **스프레드 · `assign` 열 — 한 칸도 서로 다르지 않다.** `NaN`·`-0`·`BigInt`·`undefined` 속성·심볼 키는 `kept`(값을 그대로 옮기니 당연하다), **객체가 든 열 칸은 전부 `shared`** 다 — 순환도 `shared (c.me === src)`, 즉 복사본의 `me` 가 **원본**을 가리킨다.
- ★★★ **`clone` 열 — 잃은 칸 4.** 함수는 **던지고**(`throws DOMException/DataCloneError`), **심볼 키는 조용히 빠지고**, 클래스 인스턴스와 getter 는 **넷 다 잃는 행**이다. 대신 `Date`·`Map`·`Set`·`RegExp`·`Error`·`Uint8Array`·순환·「같은 객체 두 번」이 **새 객체로 보존**됐다.
- ★★ **넷 다 잃는 행 둘** — `class instance -> plain {"x":1}` · `getter -> data property 1`. **프로토타입과 접근자는 네 수단 어느 것도 옮기지 않는다**(27번 격자의 「넷 다 `n`」 두 행과 같은 결론).

### (2) ★★★ 얕은 두 열 — `shared` 칸이 뜻하는 것

**언제 쓰나** — 「스프레드로 복사했으니 이제 따로 논다」고 믿고 싶을 때.

```text
   src = { v: new Date(0), me: <src> }                 c = { ...src }

   src ──▶ ┌──────────────┐                     c ──▶ ┌──────────────┐     (바깥 한 겹만 새 객체)
           │ v ───────────┼──┐                         │ v ───────────┼──┐
           │ me ─▶ src    │  │                         │ me ─▶ src    │  │  <- 복사본의 me 가 원본을 가리킨다
           └──────────────┘  │                         └──────────────┘  │
                             └──────────▶ Date(0) ◀──────────────────────┘  <- 하나의 Date 를 둘이 붙든다

   structuredClone(src)  ──▶ { v: Date(0)' , me: <자기 자신> }   <- Date 도 새것 · 순환도 새 그래프 안에서 닫힌다
```

- ★★★ **`shared` 는 「보존」이 아니다** — 복사본에서 `c.v.setTime(1)` 을 하면 **원본의 `v` 도 바뀐다**(같은 객체다). 그 쓰기 실험은 27번 동작 (2) `[3]` 이 이미 했다(`src.inner.deep 99`).
- ★★ **스프레드와 `assign` 이 얕은 것은 명세의 성질**이다 — 둘 다 **원본의 own 열거 가능 속성 값을 읽어 새 객체에 넣을 뿐** 그 값을 다시 복사하지 않는다(11번 · 27번이 연 연산 이름 — `CopyDataProperties` · `Object.assign`).
- ★ 원시 값 행(`NaN`·`-0`·`BigInt`)이 스프레드에서 `kept` 인 것도 같은 이유다 — **원시 값은 공유될 수 없으니** 값을 옮기면 곧 보존이다.

### (3) ★★ `structuredClone` 가까이 — 거절 · `Error` · 속성 수준 · `transfer`

**언제 쓰나** — `structuredClone` 을 골랐는데 「이 객체가 통과하나」·「통과하면 무엇이 남나」를 확인하고 싶을 때.

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

```text
===== node20 js48b-48b-clone-details.js (exit=0) =====
[1] values it refuses
  a function                          throws DOMException (name DataCloneError, code 25) 「function f() {} could not be cloned.」
  an arrow function                   throws DOMException (name DataCloneError, code 25) 「() => 1 could not be cloned.」
  a symbol value                      throws DOMException (name DataCloneError, code 25) 「Symbol(s) could not be cloned.」
  a WeakMap                           throws DOMException (name DataCloneError, code 25) 「#<WeakMap> could not be cloned.」
  a Promise                           throws DOMException (name DataCloneError, code 25) 「#<Promise> could not be cloned.」
  DOMException instanceof Error       true
[2] Error objects -- what the copy has
  new TypeError('m', { cause })
    constructor TypeError · name TypeError · message m · cause {"code":7} · cause is a new object true · extra undefined · stack is a string true · stack equal true
  new RangeError('m')
    constructor RangeError · name RangeError · message m · cause undefined · cause is a new object false · extra undefined · stack is a string true · stack equal true
  new MyError('m')  (subclass)
    constructor Error · name Error · message m · cause undefined · cause is a new object false · extra undefined · stack is a string true · stack equal true
[3] property-level things
  getter read during the copy         reads 1
  non-enumerable key copied           false
  frozen source -> copy frozen        false
  own property on a Date copied       undefined
  own property on an Array copied     x
[4] the transfer option
  source byteLength after transfer    0
  copy byteLength                     8
  source byteLength without transfer  8
```

Chrome 151 — `[1]` 의 문구만 다르다.

```text
===== ./js48b-browser.sh js48b-48b-clone-details.js (exit=0) =====
[1] values it refuses
  a function                          throws DOMException (name DataCloneError, code 25) 「Failed to execute 'structuredClone' on 'Window': function f() {} could not be cloned.」
  an arrow function                   throws DOMException (name DataCloneError, code 25) 「Failed to execute 'structuredClone' on 'Window': () => 1 could not be cloned.」
  a symbol value                      throws DOMException (name DataCloneError, code 25) 「Failed to execute 'structuredClone' on 'Window': Symbol(s) could not be cloned.」
  a WeakMap                           throws DOMException (name DataCloneError, code 25) 「Failed to execute 'structuredClone' on 'Window': #<WeakMap> could not be cloned.」
  a Promise                           throws DOMException (name DataCloneError, code 25) 「Failed to execute 'structuredClone' on 'Window': #<Promise> could not be cloned.」
  DOMException instanceof Error       true
[2] Error objects -- what the copy has
  new TypeError('m', { cause })
    constructor TypeError · name TypeError · message m · cause {"code":7} · cause is a new object true · extra undefined · stack is a string true · stack equal true
  new RangeError('m')
    constructor RangeError · name RangeError · message m · cause undefined · cause is a new object false · extra undefined · stack is a string true · stack equal true
  new MyError('m')  (subclass)
    constructor Error · name Error · message m · cause undefined · cause is a new object false · extra undefined · stack is a string true · stack equal true
[3] property-level things
  getter read during the copy         reads 1
  non-enumerable key copied           false
  frozen source -> copy frozen        false
  own property on a Date copied       undefined
  own property on an Array copied     x
[4] the transfer option
  source byteLength after transfer    0
  copy byteLength                     8
  source byteLength without transfer  8
```

- ★★★ **`[1]` — 거절은 전부 `DOMException`, 이름 `DataCloneError`, `code 25`** — 함수 · 화살표 함수 · 심볼 **값** · `WeakMap` · `Promise`. ★ `TypeError` 가 아니다 — **ECMA-262 의 예외 계층 밖에서 온다**(호스트가 만든 예외). 그래도 `DOMException instanceof Error` 는 `true` 였다.
- ★★ **문구는 호스트가 다르다** — node 18 · 20 은 `() => 1 could not be cloned.`, Chrome 151 은 앞에 `Failed to execute 'structuredClone' on 'Window': ` 가 붙는다. **문구를 문자열 비교하는 코드는 호스트를 옮기면 깨진다** — 가를 때는 `e.name === "DataCloneError"`.
- ★★ **심볼 키는 조용히 빠지는데(동작 (1)) 심볼 값은 던진다(`[1]`)** — 같은 「심볼」이라도 **자리**에 따라 실패의 모양이 다르다.
- ★★★ **`[2]` — `Error` 는 생성자가 표준 이름이면 그 생성자로 돌아온다**(`TypeError` · `RangeError`). **하위 클래스 `MyError` 는 `Error` 로 떨어지고**, 생성자에서 붙인 `name`(`MyError`)도 `extra`(`42`)도 **사라진다**. `cause` 는 **새 객체로** 따라왔고(`cause is a new object true`), `stack` 은 **원본과 같은 글자**였다.
  ★★ 이 줄들은 **세 판의 관찰**이다 — 이 문서는 HTML 의 해당 절을 읽지 않았으므로 「`cause` 를 옮겨야 한다」·「`stack` 을 옮겨야 한다」를 **보장으로 적지 않는다**(머리말 「창」 표).
- ★★ **`[3]` — getter 는 복사하는 동안 한 번 읽혔다(`reads 1`)** — 격자의 `-> data property 1` 이 그 결과다. **비열거 속성은 안 오고**(`false`) · **얼린 원본의 복사본은 얼어 있지 않고**(`false`) · **`Date` 에 붙인 속성은 사라지고**(`undefined`) · **배열에 붙인 속성은 따라왔다**(`x`). ★ 「객체에 붙인 여분의 속성」도 **그 객체의 종류**에 따라 갈린다.
- ★★ **`[4]` — `transfer` 에 넣은 `ArrayBuffer` 는 복사가 아니라 이동이다** — 원본 `byteLength` 가 `0`(떼어졌다), 복사본은 `8`. 넣지 않으면 원본은 그대로 `8`. 이 선택지의 쓰임새는 web-api 갈래 48번의 몫이다(머리말 경계).

### (4) ★★ CPython 과 한 쌍 — `copy.deepcopy` 는 클래스를 지킨다

**언제 쓰나** — 파이썬의 `deepcopy` 감각으로 JS 의 복사를 고를 때.

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

```text
===== python3 js48b-48d-python.py (exit=0) =====
[1] class instance: type(copy) is Point -> True · copy is p -> False
[2] property on the class: copy.doubled -> 2
[3] exception: type -> MyError · args -> ('m',) · extra -> 42 · __cause__ -> None
[4] function: deepcopy(f) is f -> True
```

```text
                         JS structuredClone              CPython copy.deepcopy
   클래스 인스턴스          평범한 객체 (프로토타입 잃음)        type(copy) is Point -> True
   접근자                  데이터 속성으로 굳음                클래스에 있으니 그대로 동작 (doubled -> 2)
   예외 하위 클래스         Error 로 떨어짐 · extra 사라짐       MyError · extra 42 유지
   예외의 원인              cause 가 따라옴                    __cause__ -> None (사라짐)
   함수                    DataCloneError                    deepcopy(f) is f -> True (같은 객체)
```

- ★★★ **클래스는 파이썬 쪽이 지킨다** — `type(copy) is Point -> True`. 접근자(`property`)는 **클래스에 붙어 있어서** 복사본에서도 그대로 동작한다(`doubled -> 2`). JS 의 getter 는 이 격자에서 **객체 자신의** 접근자였고, 넷 다 그것을 값으로 굳혔다.
- ★★★ **예외는 반대로 갈렸다** — 파이썬은 **하위 클래스와 `extra` 를 지키고 `__cause__` 를 잃었고**(`None`), JS `structuredClone` 은 **`cause` 를 지키고 하위 클래스와 `extra` 를 잃었다**. 「깊은 복사면 예외가 통째로 온다」는 **어느 쪽에서도 틀렸다.**
- ★★ **함수** — 파이썬은 **복사하지 않고 같은 객체를 돌려주고**(`is` — Python 03번에도 있다), JS 는 **던진다.**
- ★ 공유와 순환은 **둘 다 지킨다** — 파이썬 쪽은 Python 03번 「6」 의 `memo` 블록이 쟀다(`b[2] is b: True`), JS 쪽은 동작 (1)의 `cycle`·`same object twice` 행 `kept`.

## 문법 — 형태와 규칙

★ 이 절은 **형태 표**다 — 모든 동작 주장은 위 동작 절의 캡처 블록에서만 한다.

| 형태 | 깊이 | 누가 정하나 | 대표 손실 | 어디서 봤나 |
|---|---|---|---|---|
| `JSON.parse(JSON.stringify(o))` | 깊다(글자를 거쳐 새로 만든다) | ECMA-262 | 17행 중 16 — 타입이 글자로 표현되는 만큼만 남는다 | 동작 (1) |
| `{ ...o }` | **한 겹** | ECMA-262(ES2018) | 객체 값은 전부 `shared` · 프로토타입 · getter | 동작 (1)·(2) |
| `Object.assign({}, o)` | **한 겹** | ECMA-262(ES2015) | 스프레드와 이 격자에서 같은 답 | 동작 (1)·(2) |
| `structuredClone(o)` | 깊다(그래프째 · 공유·순환 유지) | **호스트**(HTML) | 함수 → 던짐 · 심볼 키 · 프로토타입 · getter | 동작 (1)·(3) |
| `structuredClone(o, { transfer: [buf] })` | 깊다 + 버퍼는 **이동** | 호스트 | 원본 버퍼가 떼어진다(`byteLength 0`) | 동작 (3) `[4]` |

## 어디서 틀리나

### (1) ★★★ 스프레드를 「복사」로 읽는다

**10칸이 원본과 같은 객체**다(동작 (1)). 「잃은 칸 2」만 보면 가장 좋은 수단처럼 보인다 — `shared` 를 따로 세야 드러난다(동작 (2)).

### (2) ★★★ JSON 왕복을 깊은 복사의 기본값으로 쓴다

**17행 중 16행을 잃고**, 그중 던지는 것은 `BigInt` · 순환 두 행뿐이다 — 나머지는 **에러 없이** 키가 사라지거나 모양이 바뀐다. `Date` 가 문자열이 되는 것은 **에러 없이** 지나간다.

### (3) ★★★ `structuredClone` 이면 모델 객체가 그대로 온다고 믿는다

**프로토타입을 잃는다**(`-> plain {"x":1}`) — 메서드가 없는 평범한 객체가 온다. `#private` 필드도 안 온다(16번).

### (4) ★★ 함수가 섞인 객체를 `structuredClone` 한다

**던진다**(`DataCloneError`). JSON 은 같은 자리에서 **키를 조용히 뺀다** — 한쪽은 시끄럽게, 한쪽은 조용히 실패한다.

### (5) ★★ `DataCloneError` 를 문구로 가른다

node 와 Chrome 의 문구가 **이미 다르다**(동작 (3) `[1]`). `e.name` 으로 가른다.

### (6) ★★ 「깊은 복사면 `Error` 가 통째로 온다」

JS `structuredClone` 은 **하위 클래스와 여분 속성을 잃고**, 파이썬 `deepcopy` 는 **`__cause__` 를 잃었다**(동작 (3) `[2]` · 동작 (4)).

### (7) ★ 「`structuredClone` 이 JSON 왕복보다 빠르다」

**이 문서는 재지 않았다.** 한 판의 시간은 근거가 못 된다(규칙 24) — 적으려면 판 격자와 신호 대 잡음부터 세워야 한다.

## 구현 세부사항 대 언어 보장

### 명세 보장(ECMA-262)

- ★★★ **스프레드와 `Object.assign` 은 한 겹이다** — 속성 값을 읽어 넣을 뿐 다시 복사하지 않는다. 그래서 객체 값은 `shared`(동작 (1)·(2)).
- ★★ **세 열 다 getter 를 읽어 데이터 속성으로 만들고 프로토타입을 옮기지 않는다** — 결과 객체가 새 평범한 객체다(11번 · 27번).
- ★★ **JSON 의 손실은 `JSON.stringify` 의 타입 매핑 그대로다** — 31번이 정본.

### 호스트(HTML) — 이 문서는 명세를 읽지 않았다

- ★★★ **`structuredClone` 자체** — ECMA-262 에 없다. 깊이 · 공유·순환 유지 · 거절 목록 · `DOMException`/`DataCloneError` · `transfer` 는 **호스트 API 의 동작**이고, 이 문서는 세 호스트의 관찰로만 적었다.

### 구현(V8·호스트) · 이 판의 관찰

- ★★ 예외 **문구**(Chrome 만 `Failed to execute … on 'Window': `) · 복사본 `stack` 이 원본과 같은 글자 · `Error` 하위 클래스가 `Error` 로 · `cause` 가 따라옴 · 격자 68칸이 세 판에서 같았던 것.
- ★ CPython `deepcopy` 의 예외 행 — **CPython 의 구현**(이 문서는 `copy` 모듈 문서를 다시 열지 않았다 · Python 03번이 연 문서를 인용한다).

### 그래서 이렇게 적으면 틀린다

- ✗ 「`{ ...o }` 는 객체를 복사한다」 → ○ 「**바깥 한 겹을** 복사한다 — 안의 객체는 원본과 같은 객체다」
- ✗ 「`structuredClone` 은 JS 의 깊은 복사 함수다」 → ○ 「**호스트 API** 다 — ECMA-262 에 없다」
- ✗ 「`structuredClone` 은 `Error` 를 `cause` 까지 옮긴다(명세)」 → ○ 「**이 세 판에서** 옮겼다 — 이 문서는 HTML 절을 확인하지 않았다」
- ✗ 「`structuredClone` 은 모든 것을 깊게 복사한다」 → ○ 「함수는 던지고, 심볼 키 · 프로토타입 · getter 는 잃는다」

## 언제 쓰고 언제 안 쓰나

- **스프레드 · `assign`** — 바깥 키만 바꾼 새 객체가 필요할 때(불변 갱신의 한 겹). **안쪽을 고칠 계획이면 쓰지 않는다.**
- **JSON 왕복** — 값이 **처음부터 JSON 으로 표현되는 것뿐일 때**(문자열 · 유한 숫자 · 불리언 · `null` · 배열 · 평범한 객체). 그 밖의 타입이 한 번이라도 섞일 수 있으면 쓰지 않는다.
- **`structuredClone`** — 데이터 그래프(`Date`·`Map`·`Set`·타입 배열·순환)를 통째로 떼어 낼 때. **함수 · 클래스 인스턴스 · getter** 가 든 객체에는 맞지 않는다 — 클래스는 **자기 복사 메서드**를 갖는 쪽이 낫다(설계 권고 — 이 문서는 돌려 비교하지 않았다).
- ★ **안 쓰는 자리** — 「복사가 빠를 것」을 이유로 고르기(안 쟀다) · 예외 객체를 복사해 원인 사슬을 보존하려 하기(동작 (3)·(4) — 양쪽 다 뭔가를 잃는다).

## 핵심 문장

1. ★★★ **보존 격자 68칸 — 공유 `20 / 68` · 잃음 `24 / 68`.** 열마다 잃은 칸은 JSON 16 · 스프레드 2 · `assign` 2 · `clone` 4, 공유는 스프레드·`assign` 에만 10씩. 세 판이 한 글자도 같았다.
2. ★★★ **스프레드·`assign` 은 얕다** — 잃은 칸이 적은 대신 객체가 든 칸은 전부 원본의 그 객체다. 「잃음」과 「공유」를 따로 세야 보인다.
3. ★★★ **`structuredClone` 은 호스트 API 다** — 깊고 공유·순환을 지키지만 함수는 `DataCloneError` 로 던지고, 심볼 키 · 프로토타입 · getter 는 잃는다.
4. ★★ **넷 다 잃는 것이 둘** — 프로토타입(`-> plain {"x":1}`)과 getter(`-> data property 1`).
5. ★★ **`Error` 는 어느 깊은 복사로도 통째로 오지 않는다** — JS 는 하위 클래스·여분 속성을, 파이썬은 `__cause__` 를 잃었다.

## 관련 자료

- [31 — `JSON`](../31-json/2-summary.md) — ★ **경계**: JSON 의 타입 매핑 · `toJSON`/`replacer`/`reviver` 는 거기. 여기는 **네 수단의 비교**만.
- [11 — 스프레드와 나머지](../11-spread-and-rest/2-summary.md) · [27 — `Object` 정적 메서드](../27-object-static-methods/2-summary.md) — ★ **경계**: 스프레드와 `assign` 의 **호출 과정**(getter·setter·`Proxy` 로그)은 그쪽. 여기는 **결과가 원본과 무엇을 공유하나**.
- [16 — `class` 문법](../16-class-syntax/2-summary.md) — `#private` 가 복사에 안 보이는 것.
- web-api 갈래 목록([`web-api/README.md`](../../../../web-api/README.md))의 **47번**(워커와 구조적 복제의 한계) · **48번**(전송과 공유 메모리) — ★ **경계**: 스레드를 건너는 복사는 그쪽.
- [Python 03 — 가변성과 복사](../../../python/syntax/03-mutability-and-copying/2-summary.md) — `deepcopy` 의 `memo`.

## 용어 풀이

- **얕은 복사(shallow copy)** — 바깥 객체만 새로 만들고 안의 값은 **같은 것을 가리키는** 복사.
- **깊은 복사(deep copy)** — 안의 객체까지 새로 만드는 복사. 원본과 객체를 공유하지 않는다.
- **`shared`(이 문서의 칸)** — 복사본이 원본과 **같은 객체**(`===`)를 쥔 칸.
- **JSON 왕복** — `JSON.stringify` 로 글자를 만들고 `JSON.parse` 로 다시 값을 만드는 것.
- **`structuredClone`** — 호스트(HTML·node)가 주는 전역 함수. 값의 그래프를 새로 만든다.
- **`DataCloneError`** — `structuredClone` 이 복사할 수 없는 값을 만났을 때 던지는 `DOMException` 의 `name`.
- **`DOMException`** — 호스트 API 가 던지는 예외 타입. `name`·`code` 로 종류를 가른다(ECMA-262 의 `TypeError` 계열이 아니다).
- **`transfer`** — `structuredClone` 의 선택지. 넣은 `ArrayBuffer` 를 **복사하지 않고 옮겨** 원본을 떼어 낸다.
- **프로토타입(prototype)** — 객체가 메서드를 찾아 올라가는 사슬의 다음 객체([15번](../15-prototype-chain/2-summary.md)). 네 수단 모두 복사본의 프로토타입을 `Object.prototype` 으로 둔다.

## 더 들어가면

- **HTML 의 구조적 직렬화 절** — 이 문서는 읽지 않았다. `Error` 의 `cause`·`stack` 이 명세의 요구인지 V8 의 선택인지는 **거기서** 갈린다(머리말 「창」 표).
- **V8 이 아닌 엔진** — 이 문서의 세 판은 모두 V8 이다. 다른 엔진에서 격자를 다시 돌리면 「HTML 층」과 「구현 층」이 조금 더 갈릴 것이다(돌리지 않았다).
- **클래스 인스턴스의 깊은 복사** — 클래스가 복사 메서드를 갖는 설계 · `Object.create(Object.getPrototypeOf(o))` 에 속성을 옮기는 수작업 — 이 문서는 격자에 넣지 않았다.
