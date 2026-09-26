# js/syntax/51 — 명시적 자원 관리 `using`: 「블록을 떠나는 모든 길에서 역순으로 치운다 — 그런데 node 18·20 에는 문법이 없고, 거기 있는 `Symbol.dispose` 는 node 자신의 심볼이다」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> ★★★ **이 주제의 본체는 ② 지원 판별 격자다** — 판 셋(node 18 · node 20 · Chrome 151) × 기능 일곱(`using` 문법 · `await using` 문법 · `Symbol.dispose` · `Symbol.asyncDispose` · `DisposableStack` · `AsyncDisposableStack` · `SuppressedError`) = **21칸**을 스크립트가 채우고 **「supported cells: N / M」** 을 마지막 줄로 찍는다(동작 (1)). 「이 코드가 이 런타임에서 도나」 가 이 주제의 첫 질문이기 때문이다.
> ★★ 보조로 **① 로그 심기**(해제 순서 — 만들 때와 치울 때 한 줄씩 · 동작 (3)·(6)) · **④ 예외의 이름 + 문구**(`SyntaxError` 가 **선언이 설 수 없는 자리**를 가르는 것 · `SuppressedError` 의 모양 · 동작 (2)·(4))를 쓴다.
> ★★★ **node 에는 문법이 없으므로 「node 에서 `using` 이 어떻게 도나」 는 그 창으로는 못 잰다** — 같은 질문을 **다른 창 둘**로 다시 물었다(제5의 상태 — 아래 창 표): **손으로 쓴 `try`/`finally`**(동작 (7)) 와 **tsc 7.0.2 가 낮춰 쓴 코드**(동작 (8)).
>
> **기준 소스** — 열어서 확인한 것만. 이 배치가 앞서 받아 둔 **ECMA-262 초안 사본**(표제 「ECMAScript® 2027 Language Specification」, multipage)의 해당 절을 읽었다.
> - [ECMA-262 — Abstract Operations 7.5 Operations on Disposable Objects](https://tc39.es/ecma262/multipage/abstract-operations.html) — `AddDisposableResource`: 「**If value is either null or undefined and kind is sync-dispose, return unused.**」 · NOTE 「null·undefined 이고 async-dispose 이면 **나중에 여전히 Await 하도록** 기록한다」 · `GetDisposeMethod`: 「**If value is not an Object, throw a TypeError exception.**」 · `DisposeResources`: 「**For each element resource of disposableResourceStack, in reverse List order**」 · 앞의 완료가 throw 인데 또 throw 면 「**Let error be a newly created SuppressedError object.** … `"error"` 에 새 오류, `"suppressed"` 에 앞의 것」 — ★ **이 단계에는 `message` 가 없다**
> - [ECMA-262 — 14.3.1 Let, Const, Using, and Await Using Declarations](https://tc39.es/ecma262/multipage/ecmascript-language-statements-and-declarations.html) — 문법 `UsingDeclaration : using [no LineTerminator here] BindingList[…, ~Pattern] ;`(★ **구조 분해 패턴 없음**) · 「초기자가 없고 상수 선언이면 Syntax Error」 · 14.12.1 switch — 「**CaseClause : case Expression : StatementList — It is a Syntax Error if ContainsUsing of StatementList is true.**」(`DefaultClause` 도 같다)
> - [ECMA-262 — 16.1.1 Scripts: Static Semantics: Early Errors](https://tc39.es/ecma262/multipage/ecmascript-language-scripts-and-modules.html) — `ScriptBody : StatementList` 「**It is a Syntax Error if ContainsUsing of StatementList is true.**」
> - [ECMA-262 — 20.5.8 SuppressedError Objects](https://tc39.es/ecma262/multipage/fundamental-objects.html) — `SuppressedError ( error, suppressed, message )` — `message` 가 `undefined` 가 아니면 `"message"`, 그다음 `"error"`, `"suppressed"` 를 **열거 불가 데이터 속성**으로 만든다 · `[[Prototype]]` 은 `%Error%`
> - [ECMA-262 — 27.3 DisposableStack Objects](https://tc39.es/ecma262/multipage/control-abstraction-objects.html) — 「**Resources are added in the order they are initialized, and are disposed in reverse order.**」 · `use`·`move` — **이미 disposed 면 `ReferenceError`**
> - ★ **판 표기** — README 는 이 기능을 **ES2027** 로 적는다. 이 문서가 읽은 사본의 표제도 2027 초안이고, 같은 배치가 받아 둔 TC39 finished proposals 표의 이 행도 **2027** 이다. ★ **확정판 번호는 확인하지 않았다**(외부 네트워크를 쓰지 않았다).
>
> **실행 검증** — 이 문서의 모든 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다.
> 배너의 `node20` 은 v20.19.6, `node18` 은 v18.19.1(판별 블록). Chrome 은 `./js48b-browser.sh`(헤드리스 Chrome 151 · 소스는 아래) 로 돌렸다 — 페이지는 **고전 스크립트**로 탐침을 싣고, `.mjs` 만 `--http` 로 **모듈**로 싣는다. tsc 는 **7.0.2**.
> ★★★ **성능·메모리는 재지 않았다.** 「`using` 이 `try`/`finally` 보다 느리다/빠르다」 는 이 문서에 없다.
>
> **버전** — `using`·`await using`·`DisposableStack`·`SuppressedError` 는 README 표기 **ES2027** · **Chrome 151 에만 전부 있다** · node 18·20 에는 **문법이 없다**(동작 (1)).

```text
===== ./js48b-versions.sh (exit=0) =====
node 18.19.1  v8 10.2.154.26-node.28  icu 74.2  tz 2023c  unicode 15.1  cldr 44.1
node 20.19.6  v8 11.3.244.8-node.33  icu 77.1  tz 2025b  unicode 16.0  cldr 47.0
Google Chrome 151.0.7922.173
```

> **★★★ 층 — 이 문서의 결론이 기대는 네 층**
>
> | 층 | 무엇 | 어디서 |
> |---|---|---|
> | ★★★ **명세(ECMA-262 초안)** | **역순** 해제 · 블록을 떠나는 **모든 길**(끝·`return`·`throw`·`break`)에서 해제 · `null`/`undefined` 는 건너뜀 · 메서드는 **선언 때** 읽음 · 해제 중 예외는 `SuppressedError` 로 **감싸 둘 다** 남김 · 스크립트 최상위와 `case` 절 바로 밑은 **Syntax Error** | 동작 (2)·(3)·(4)·(6) — 단 **확인한 엔진은 Chrome 151 하나**다 |
> | ★★ **엔진(V8) 문구·선택** | `SyntaxError`·`TypeError` 의 **문구** · 해제가 만든 `SuppressedError` 의 **`message`**(명세 단계에는 없다) | 동작 (2)·(4) |
> | ★★★ **호스트(node)** | node 18·20 의 `Symbol.dispose` 는 **`Symbol.for("nodejs.dispose")`** — 전역 레지스트리에 등록된 **node 의 심볼**이다(명세의 well-known symbol 은 등록되지 않는다 — Chrome 은 `Symbol.keyFor` 가 `undefined`) | 동작 (1)의 `#` 두 줄 |
> | ★★ **도구(tsc)** | `--target es2022` 에서 `using` 을 **헬퍼 두 개**로 낮춘다 · 없는 `SuppressedError` 를 **`name` 만 바꾼 `Error`** 로 흉내 낸다 | 동작 (8) |

> **★★★ 이 주제가 쓰는 창 — 그리고 부적용인 창**
>
> | 창 | 이 주제에서 무엇을 보나 |
> |---|---|
> | ★★★ **② 지원 판별 격자**(본체의 도구) | 판 3 × 기능 7 = 21칸 — 「`supported cells: 11 / 21`」(동작 (1)) · 선언이 설 수 있는 자리 15곳 × Chrome · node(동작 (2)) |
> | ★★★ **① 로그 심기** | 만들 때 · 치울 때 한 줄씩 — 역순 · 떠나는 길 · `for...of` · `null` · 선언 때 읽는 메서드(동작 (3)) · `await using` 과 마이크로태스크 틱(동작 (6)) |
> | ★★ **④ 예외의 이름 + 문구** | 선언 자리의 `SyntaxError` 문구(동작 (2)) · `SuppressedError` 의 `.error`/`.suppressed` 중첩(동작 (4)) · `DisposableStack` 의 `ReferenceError`(동작 (5)) |
> | ★★★ **「못 잰 것」 이 아니라 「창을 바꿔 물었다」**(제5의 상태) | node 18·20 에서 **`using` 자체는 잴 수 없다**(문법이 없어 `SyntaxError` 로 끝난다). 같은 질문(「역순인가 · 두 오류가 다 남나」)을 **손으로 쓴 `try`/`finally`**(동작 (7)) 와 **tsc 가 낮춘 코드**(동작 (8))로 다시 물었다. ★ **바꾼 창이 못 보는 것** — 둘 다 **엔진의 `using` 이 아니다**: 손 코드는 내가 쓴 순서를, tsc 헬퍼는 **tsc 가 쓴 순서**를 보일 뿐이고, 헬퍼의 `SuppressedError` 는 **진짜 생성자가 아니다**(node 에서 `constructor Error`) |
> | ★ **부적용 — 양** | 해제에 드는 시간·바이트는 이 기능이 말하는 것이 아니다 — 재지 않았다 |
> | ★ **부적용 — GC** | `using` 은 **GC 와 무관**하다 — 블록 끝이라는 **문법상의 순간**에 부른다. 「언제 치워지나」 가 명세 밖이던 47번과 정반대 자리다 |

> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 판별 블록의 판 문자열 · tsc 판 문자열 · **tsc 가 쓴 헬퍼 코드의 모양**(판이 오르면 바뀔 수 있다 — 한 판의 관찰) · 오류 **문구**(엔진·판마다 다르다 — node 18 과 20 이 이미 다르다) | ★★★ 격자의 **모든 칸**과 마지막 줄 · 해제 로그의 **순서** · `SuppressedError` 의 **중첩 모양** · 틱 순서 — **재대조 동일**(실행마다 바뀌는 칸이 없다) |

> **선행** — [32 — 오류 처리와 `Error`](../32-error-handling-and-error/2-summary.md)(직접 선행 — ★★★ **이미 쟀다**: `finally` 에서 정리 중 던진 예외가 **원래 예외를 흔적 없이 지운다**(거기 동작 (2)의 `[4]` · 「어디서 틀리나 (2)」) · `try` 3 × `finally` 3 격자. 그 편은 「`using`·`SuppressedError` 는 51번의 몫」 이라고 경계를 그었다 — 이 문서가 그 자리다. ★ 이 문서의 동작 (7) `[2]` 는 32번의 그 결과를 **다시 재지 않고** 한 줄로 되짚는다) ·
> [20 — 제너레이터](../20-generators/2-summary.md)(★★ `return()` 은 「반드시 닫는다」가 아니라 **「멈춘 자리에서 `return` 을 일으킨다」** — 거기 동작 (3)) · [40 — 비동기 이터레이션](../40-async-iteration-and-for-await/2-summary.md)(`break`·`return`·`throw` 셋 다 `return()` 을 부르고 `for await` 는 그것을 **기다린다**) · [47 — `WeakRef`·`FinalizationRegistry`](../47-weakref-and-finalizationregistry/2-summary.md)(★★ 정리를 GC 콜백에 맡기면 **「언제」 가 명세 밖**이었다 — 그 편이 결정적 대안으로 이 주제를 가리켰다) · [22 — `Symbol`](../22-symbol-and-well-known-symbols/2-summary.md)(well-known symbol · `Symbol.for` 레지스트리).
>
> ★★ **경계** — `try`/`finally` 의 흐름 자체는 **32번**, 이터레이터를 닫는 `return()` 은 **19·20·40번**이 정본이다. 여기는 **`using` 이 무엇을 언제 부르나 · 어디에 설 수 있나 · 어느 런타임에 있나**만이다. TS 쪽 타입 검사(`Disposable` 인터페이스 · `lib` 설정)는 TS 갈래 목록([`ts/syntax/README.md`](../../../ts/syntax/README.md))의 버전 표 **5.2** 행이 「값 쪽 의미는 JS #51」 로 이 문서를 가리킨다 — 이 문서는 **방출물이 도는지**만 본다(동작 (8)).
>
> ★★ **교차 갈래** — [Python 28 — 컨텍스트 매니저와 `with`](../../../python/syntax/28-context-managers-and-with/2-summary.md) · [Java 26 — `try`-with-resources](../../../java/syntax/26-try-with-resources/2-summary.md) · C# 은 C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **37번**(`IDisposable` 과 `using` — 폴더 없음). 이 문서는 셋을 **돌리지 않았고** 각 편이 잰 것을 인용만 한다(동작 (9)).

Chrome 하네스 — 한 번 싣고 모든 `./js48b-browser.sh` 블록이 이것을 쓴다.

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

**`using` 은 「방을 나갈 때 켠 순서의 반대로 불을 끄는 관리인」 이다. 방에 장비를 들일 때마다(`using x = …`) 관리인이 장부에 적고, 어느 문으로 나가든(끝·`return`·`throw`·`break`) 장부를 맨 아래부터 거꾸로 읽으며 끈다. 끄다가 사고가 나면 원래 사고 보고서를 버리지 않고 새 보고서에 첨부한다(`SuppressedError`). 다만 이 관리인은 아직 모든 건물에 없다 — Chrome 151 에는 있고, node 18·20 에는 장부의 이름표(`Symbol.dispose`)만 붙어 있고 관리인이 없다.**

- ★★★ **Chrome 151 은 일곱 기능이 다 있고 node 18·20 은 둘뿐** — `supported cells: 11 / 21`. node 의 둘은 **`Symbol.dispose`·`Symbol.asyncDispose`** 이고, 그것도 `Symbol(nodejs.dispose)` — node 가 **`Symbol.for` 로 만든 자기 심볼**이다(동작 (1)).
- ★★★ **역순** — `using a, b, c` 는 `dispose c · dispose b · dispose a`. 선언이 여럿이어도, 안쪽 블록이 있어도 **블록마다 역순**(동작 (3)).
- ★★★ **두 오류가 다 남는다** — 본문이 던지고 해제도 던지면 `SuppressedError` 의 `.error` 에 **해제 쪽**, `.suppressed` 에 **본문 쪽**(동작 (4)). 손으로 쓴 `try`/`finally` 는 **본문 쪽을 잃는다**(동작 (7) — 32번과 같은 결과).
- ★★ **스크립트 최상위와 `case` 절 바로 밑에는 못 쓴다** — 둘 다 명세의 Syntax Error 이고, 블록으로 한 겹 감싸면 된다(동작 (2)).

```text
   {                                     장부 (DisposableResourceStack)
     using a = open("a");     ─────▶    [ a ]
     using b = open("b"),               [ a, b ]
           c = open("c");     ─────▶    [ a, b, c ]
     … 본문 …
   }  ← 끝 · return · throw · break  ─▶  거꾸로 읽는다:  c ▶ b ▶ a
                                         한 해제가 던져도 나머지는 계속 — 던진 것들은 SuppressedError 로 겹친다
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 장비를 들이며 장부에 적는다 | `using x = v` — 선언 때 `v[Symbol.dispose]` 를 **읽어 둔다** | 동작 (3)의 `[9]` |
| 장비가 아니면 들이지 않는다 | `null`·`undefined` 는 **건너뛴다** · 메서드 없는 객체는 **`TypeError`** | 동작 (3)의 `[7]`·`[8]` |
| 어느 문으로 나가든 끈다 | 블록을 떠나는 모든 완료 — 정상·`return`·`throw`·`break` | 동작 (3)의 `[3]`·`[4]`·`[6]` |
| 맨 아래부터 거꾸로 | 명세 「**in reverse List order**」 | 동작 (3)의 `[1]`·`[2]` |
| 사고 보고서에 첨부 | `SuppressedError` — `.error` = 새 오류 · `.suppressed` = 앞의 것 | 동작 (4) |
| 장부를 손으로 들고 다니기 | `DisposableStack` — `use`·`adopt`·`defer`·`move` | 동작 (5) |
| 끄는 데 시간이 걸리는 장비 | `await using` · `Symbol.asyncDispose` — 하나씩 **기다린다** | 동작 (6) |
| 이름표만 있고 관리인이 없는 건물 | node 18·20 — `Symbol.dispose` 는 있고 문법은 없다 | 동작 (1) |

**똑같은 구조다** — 실무에서 물리는 자리도 굳어 있다.
「**`finally` 에서 `close()` 를 불렀는데 `close()` 가 던져서 원래 오류가 로그에서 사라졌다**」(32번의 사고 · 동작 (7)),
「**연결을 열고 트랜잭션을 연 순서대로 닫아서 트랜잭션이 이미 닫힌 연결을 만졌다**」(역순 · 동작 (3)),
「**브라우저에서 되던 코드가 node 20 에서 `SyntaxError: Unexpected identifier 'x'` 로 로드조차 안 된다**」(동작 (1)·(2))가 그것이다.

> **`using` 선언** — 블록이 끝날 때 값의 `[Symbol.dispose]()` 를 **자동으로** 부르는 `const` 같은 선언(README 표기 ES2027).\
> 예: `{ using f = openFile(); f.read(); }  // 여기서 f[Symbol.dispose]()`

## 이 주제가 답하려는 질문

1. **이 코드는 어느 런타임에서 도나** — 문법 · 심볼 · 전역 객체가 판마다 어떻게 갈리고, node 에 있는 `Symbol.dispose` 는 무엇인가?
2. **해제는 언제 · 어떤 순서로 불리나** — 여러 선언 · 안쪽 블록 · 떠나는 길 · 루프 · `null` · 메서드를 바꿔치기하면? `await using` 은 무엇을 기다리나?
3. **해제가 던지면 무엇이 남나** — 손으로 쓴 `try`/`finally` 와 무엇이 다르고, `using` 이 없는 판에서는 어떻게 흉내 내나(tsc 는 무엇을 해 주나)?

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 출력으로 읽는다.

### (1) ★★★ 지원 판별 격자 — 판 셋 × 기능 일곱

**언제 쓰나** — 「이 라이브러리가 `using` 을 쓰는데 우리 런타임에서 도나」 를 판단할 때.
★ 문법은 `new Function(…)` 로 물어서, 없는 판에서도 스크립트가 죽지 않는다. `#` 로 시작하는 두 줄은 **칸으로 세지 않는** 설명 줄이다.

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

```text
===== ./js48b-51a-support.sh (exit=0) =====
                                     node18                 node20                 Chrome 151
using declaration in a block         no                     no                     yes
await using in an async function     no                     no                     yes
Symbol.dispose                       yes                    yes                    yes
Symbol.asyncDispose                  yes                    yes                    yes
DisposableStack                      no                     no                     yes
AsyncDisposableStack                 no                     no                     yes
SuppressedError                      no                     no                     yes
# String(Symbol.dispose)             Symbol(nodejs.dispose) Symbol(nodejs.dispose) Symbol(Symbol.dispose)
# Symbol.keyFor(Symbol.dispose)      nodejs.dispose         nodejs.dispose         undefined

supported cells: 11 / 21
```

```text
                         node18   node20   Chrome 151
   using 문법              ✗        ✗        ○
   await using 문법        ✗        ✗        ○
   Symbol.dispose          ○*       ○*       ○        * = Symbol.for("nodejs.dispose") — node 의 심볼
   Symbol.asyncDispose     ○*       ○*       ○
   DisposableStack         ✗        ✗        ○
   AsyncDisposableStack    ✗        ✗        ○
   SuppressedError         ✗        ✗        ○
                         ───────────────────────────
   supported cells         2        2        7        = 11 / 21
```

- ★★★ **`supported cells: 11 / 21`** — Chrome 151 이 **7 / 7**, node 18·20 이 각각 **2 / 7** 이다. 두 node 판이 **한 칸도 안 갈렸다.**
- ★★★ **node 의 두 「yes」 는 명세의 심볼이 아니다** — `String(Symbol.dispose)` 가 **`Symbol(nodejs.dispose)`**, `Symbol.keyFor(Symbol.dispose)` 가 **`nodejs.dispose`** — 전역 레지스트리(`Symbol.for`)에 등록된 심볼이다. Chrome 은 `Symbol(Symbol.dispose)` · `undefined` — 명세의 well-known symbol 은 **등록되지 않은** 심볼이다(22번). ★ 그래서 이 격자의 `Symbol.dispose yes` 는 「**그 이름의 심볼 속성이 있다**」 까지만 뜻한다 — 층은 **호스트**다.
- ★★ **「`Symbol.dispose` 가 있으니 `using` 도 되겠지」 가 틀리는 자리가 여기다** — 이름표는 있는데 관리인(문법)이 없다. 기능 검사를 **심볼로 하면 node 에서 거짓 양성**이 난다 — 문법은 **파싱으로** 물어야 한다(이 탐침의 `syntax(…)`).

### (2) ★★ 선언이 설 수 있는 자리 — 열다섯 자리 × 두 목표

**언제 쓰나** — `using` 을 파일 맨 위 · `switch` 안 · 루프 머리에 두려 할 때.
★ `new Function(text)` 는 **함수 몸통**으로, 간접 `eval` `(0, eval)(text)` 는 **스크립트 최상위**로 파싱한다.

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

```text
===== ./js48b-browser.sh js48b-51b-positions.js (exit=0) =====
  function body     { using x = R51; }                            parsed
  function body     using x = R51;                                parsed
  script top level  using x = R51;                                SyntaxError 「Unexpected identifier 'x'」
  script top level  { using x = R51; }                            parsed
  function body     for (using x of [R51]) {}                     parsed
  function body     for (using x = R51; false; ) {}               parsed
  function body     for (using x in { a: 1 }) {}                  SyntaxError 「Invalid 'using' in for-in loop」
  function body     switch (1) { case 1: using x = R51; }         SyntaxError 「Unexpected identifier 'x'」
  function body     switch (1) { case 1: { using x = R51; } }     parsed
  function body     using x;                                      SyntaxError 「Missing initializer in using declaration」
  function body     using { a } = R51;                            SyntaxError 「Unexpected token '{'」
  function body     using x = R51, y = R51;                       parsed
  function body     let using = 1; return using;                  parsed
  function body     return async () => { await using x = R51; };  parsed
  function body     await using x = R51;                          SyntaxError 「await is only valid in async functions and the top level bodies of modules」
```

node 20 — 전부 문법이 없는 쪽의 문구다.

```text
===== node20 js48b-51b-positions.js (exit=0) =====
  function body     { using x = R51; }                            SyntaxError 「Unexpected identifier 'x'」
  function body     using x = R51;                                SyntaxError 「Unexpected identifier 'x'」
  script top level  using x = R51;                                SyntaxError 「Unexpected identifier 'x'」
  script top level  { using x = R51; }                            SyntaxError 「Unexpected identifier 'x'」
  function body     for (using x of [R51]) {}                     SyntaxError 「Unexpected identifier 'x'」
  function body     for (using x = R51; false; ) {}               SyntaxError 「Unexpected identifier 'x'」
  function body     for (using x in { a: 1 }) {}                  SyntaxError 「Unexpected identifier 'x'」
  function body     switch (1) { case 1: using x = R51; }         SyntaxError 「Unexpected identifier 'x'」
  function body     switch (1) { case 1: { using x = R51; } }     SyntaxError 「Unexpected identifier 'x'」
  function body     using x;                                      SyntaxError 「Unexpected identifier 'x'」
  function body     using { a } = R51;                            SyntaxError 「Unexpected token '{'」
  function body     using x = R51, y = R51;                       SyntaxError 「Unexpected identifier 'x'」
  function body     let using = 1; return using;                  parsed
  function body     return async () => { await using x = R51; };  SyntaxError 「Unexpected identifier 'x'」
  function body     await using x = R51;                          SyntaxError 「await is only valid in async functions and the top level bodies of modules」
```

node 18 — 문구가 **식별자 없이** 짧다.

```text
===== node18 js48b-51b-positions.js (exit=0) =====
  function body     { using x = R51; }                            SyntaxError 「Unexpected identifier」
  function body     using x = R51;                                SyntaxError 「Unexpected identifier」
  script top level  using x = R51;                                SyntaxError 「Unexpected identifier」
  script top level  { using x = R51; }                            SyntaxError 「Unexpected identifier」
  function body     for (using x of [R51]) {}                     SyntaxError 「Unexpected identifier」
  function body     for (using x = R51; false; ) {}               SyntaxError 「Unexpected identifier」
  function body     for (using x in { a: 1 }) {}                  SyntaxError 「Unexpected identifier」
  function body     switch (1) { case 1: using x = R51; }         SyntaxError 「Unexpected identifier」
  function body     switch (1) { case 1: { using x = R51; } }     SyntaxError 「Unexpected identifier」
  function body     using x;                                      SyntaxError 「Unexpected identifier」
  function body     using { a } = R51;                            SyntaxError 「Unexpected token '{'」
  function body     using x = R51, y = R51;                       SyntaxError 「Unexpected identifier」
  function body     let using = 1; return using;                  parsed
  function body     return async () => { await using x = R51; };  SyntaxError 「Unexpected identifier」
  function body     await using x = R51;                          SyntaxError 「await is only valid in async functions and the top level bodies of modules」
```

모듈 최상위 — 고전 스크립트와 달리 되나(Chrome 151 · `--http` 로 모듈 스크립트로 싣는다).

```js
// js48b-51b-module.mjs
// A module whose top level holds a using declaration. Loaded as <script type="module">.
const log = [];
{
  using a = { [Symbol.dispose]() { log.push("dispose a"); } };
  log.push("block body");
}
using top = { [Symbol.dispose]() { console.log("  dispose top (module top level)"); } };
console.log("  module top level parsed · " + log.join(" · "));
```

```text
===== ./js48b-browser.sh --http js48b-51b-module.mjs (exit=0) =====
  module top level parsed · block body · dispose a
  dispose top (module top level)
```

```text
   Chrome 151 이 받은 자리                         Chrome 151 이 거절한 자리 (SyntaxError)
   함수 몸통 · 블록 안                               스크립트 최상위       ← 명세 16.1.1 ContainsUsing
   스크립트 최상위의 블록 안 { … }                    case 절 바로 밑       ← 명세 14.12.1 ContainsUsing
   for (using x of …) · for (using x = …; …; …)     for (using x in …)    ← 「Invalid 'using' in for-in loop」
   case 절 안의 블록 { … }                           초기자 없음 using x;  ← 「Missing initializer …」
   모듈 최상위                                       구조 분해 using { a } ← 문법에 패턴이 없다(~Pattern)
   async 함수 안 await using                         async 밖 await using
```

- ★★★ **스크립트 최상위는 안 되고 모듈 최상위는 된다** — `script top level  using x = R51;` 이 `Unexpected identifier 'x'`, 모듈은 `module top level parsed` 뒤 **모듈 평가가 끝날 때** `dispose top` 이 찍혔다. 명세 16.1.1 이 `ScriptBody` 에만 「**ContainsUsing 이면 Syntax Error**」 를 둔다.
- ★★★ **`case 1: using x = …` 는 안 되고 `case 1: { using x = …; }` 는 된다** — 명세 14.12.1. `case` 절들은 **한 블록을 나눠 쓰므로** 어느 `case` 로 들어왔느냐에 따라 선언이 실행됐는지가 갈린다 — 그 자리에서 장부를 막은 것으로 읽힌다(이 문장은 해석이다 · [52 — `switch`·라벨·흐름 제어](../52-switch-labels-and-control-flow/2-summary.md) 「`switch` 블록 하나가 스코프 하나」 와 같은 뿌리).
- ★★ **문구는 원인을 말하지 않을 때가 있다** — 스크립트 최상위와 `case` 절 둘 다 **`Unexpected identifier 'x'`** 라서 「`using` 을 모르는 엔진」 과 **글자가 같다**(node 20 의 첫 줄과 비교). 근거는 문구가 아니라 **같은 텍스트가 한 칸 옮기면 `parsed` 가 된다**는 대조다(규칙 27).
- ★★ **`let using = 1` 은 여전히 된다**(세 판 다) — `using` 은 **예약어가 아니다.** 그래서 `using x` 는 `using` 뒤에 **줄바꿈 없이 식별자**가 올 때만 선언으로 읽힌다(명세 `[no LineTerminator here]`) · `using { a }` 는 선언 문법에 패턴이 없어 `Unexpected token '{'`(node 20 · 18 도 같은 글자).
- ★ **`await using x` 를 async 밖에 쓰면** 세 판 모두 `await is only valid in async functions and the top level bodies of modules` — `using` 을 몰라도 **`await` 쪽에서 먼저** 걸린다.

### (3) ★★★ 해제 순서 — 로그를 심은 열 갈래

**언제 쓰나** — 연결 → 트랜잭션 → 커서처럼 **서로 기대는 자원**을 한 블록에서 열 때.
★ `res(name)` 이 만들 때 `make`, 치울 때 `dispose` 를 남긴다. 한 갈래 = 한 함수 = 한 블록.

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

```text
===== ./js48b-browser.sh js48b-51c-order.js (exit=0) =====
[1] one declaration, three bindings
    make a · make b · make c · body · dispose c · dispose b · dispose a  ->  returned undefined
[2] three declarations, the middle one in an inner block
    make a · make b · inner body · dispose b · make c · outer body · dispose c · dispose a  ->  returned undefined
[3] leaving by return
    make a · before return · dispose a  ->  returned r
[4] leaving by throw
    make a · dispose a  ->  threw Error 「from the body」
[5] inside try, with a finally
    make a · try body · dispose a · finally  ->  returned undefined
[6] loop: for (using x of ...)
    make p · make q · loop body · dispose p · loop body · dispose q  ->  returned undefined
[7] null and undefined as the value
    make c · body · dispose c  ->  returned undefined
[8] a value without Symbol.dispose
    make a · before the second declaration · dispose a  ->  threw TypeError 「Symbol(Symbol.dispose) is not a function」
[9] replacing the method after the declaration
    body · the method present at the declaration  ->  returned undefined
[10] assigning to the binding
    make a · make other · dispose a  ->  threw TypeError 「Assignment to using variable.」
```

```text
   [1] using a, b, c        make a · make b · make c · body ─▶ dispose c · dispose b · dispose a
   [2] a { b } c            a ── { b ── dispose b } ── c ── dispose c · dispose a     ← 블록마다 제 장부
   [3] return  [4] throw    떠나는 길이 달라도 dispose a 는 돈다 · 결과(반환값·예외)는 그대로 나간다
   [5] try { using } finally    dispose a ─▶ finally          ← 블록이 먼저 닫히고 finally 가 뒤
   [6] for (using x of …)   반복마다 한 번씩 — dispose p 다음에야 둘째 반복
   [7] null · undefined     장부에 안 적힌다 — dispose c 만
   [8] 메서드 없는 {}        그 선언에서 TypeError ─▶ 이미 적힌 a 는 치운다
   [9] 나중에 바꾼 메서드     선언 때 읽어 둔 쪽이 불린다
   [10] a = …               TypeError — using 바인딩은 상수
```

- ★★★ **`[1]` 역순 · `[2]` 블록마다 역순** — `dispose b` 는 **안쪽 블록이 끝나는 순간**, 그 뒤에 `make c`. 명세 「in reverse List order」 — 장부는 **블록의 환경 레코드마다** 따로 있다.
- ★★★ **`[3]`·`[4]` — 떠나는 길이 달라도 돈다** · 반환값 `r` 과 예외 `from the body` 가 **그대로** 호출자에게 간다. `[5]` — **`using` 의 해제가 `finally` 보다 먼저**(해제는 `try` 블록의 끝에 속한다).
- ★★★ **`[6]` 루프는 반복마다 해제** — `loop body · dispose p · loop body · dispose q`. ★ `make p · make q` 가 먼저인 것은 **배열 리터럴이 루프 전에 다 만들어졌기** 때문이다 — `using` 의 성질이 아니다.
- ★★ **`[7]` `null`·`undefined` 는 건너뛴다**(명세 `AddDisposableResource` — 「return unused」) · **`[8]` 메서드 없는 객체는 그 선언에서 `TypeError`** — `after the second declaration` 이 안 찍히고, **이미 적힌 `a` 는 치운다.** 문구 `Symbol(Symbol.dispose) is not a function` 은 V8 의 것이다.
- ★★ **`[9]` 메서드는 선언 때 읽는다** — 선언 뒤에 `r[Symbol.dispose]` 를 바꿔도 **처음 것**이 불렸다(명세 `CreateDisposableResource` 가 `GetDisposeMethod` 결과를 레코드에 담는다).
- ★ **`[10]`** — `Assignment to using variable.` — `const` 처럼 다시 대입할 수 없다.

### (4) ★★★ 해제 중 예외 — `SuppressedError` 가 겹치는 모양

**언제 쓰나** — `close()` 가 던질 수 있는 자원을 쓸 때 · 로그에 **무엇이 남을지** 판단할 때.

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

```text
===== ./js48b-browser.sh js48b-51d-errors.js (exit=0) =====
[1] the body throws, the one resource throws while disposing
    SuppressedError 「An error was suppressed during disposal」
      .error:
        Error 「dispose a」
      .suppressed:
        Error 「body」
[2] the body finishes, the one resource throws while disposing
    Error 「dispose a」
[3] the body throws, two resources throw while disposing
    SuppressedError 「An error was suppressed during disposal」
      .error:
        Error 「dispose a」
      .suppressed:
        SuppressedError 「An error was suppressed during disposal」
          .error:
            Error 「dispose b」
          .suppressed:
            Error 「body」
[4] the body finishes, b throws while disposing, a does not
    log: dispose a
    Error 「dispose b」
[5] new SuppressedError(x, y, 'm')
    .error x · .suppressed y · .message m · own keys message error suppressed · instanceof Error true
[6] own keys of the error that [1] threw
    message error suppressed · Object.hasOwn(e, 'message') true
```

```text
   [1] 본문 throw "body" · a 해제 throw           [3] 본문 throw · b 해제 throw · a 해제 throw

   SuppressedError                              SuppressedError                ← 마지막(a)이 겉
     .error      = Error "dispose a"   (새것)      .error      = Error "dispose a"
     .suppressed = Error "body"        (앞의 것)    .suppressed = SuppressedError  ← b 가 먼저 겹쳤다
                                                   .error      = Error "dispose b"
                                                   .suppressed = Error "body"   ← 본문은 맨 안쪽
```

- ★★★ **`[1]` — 둘 다 남는다.** `.error` 가 **해제 쪽**(`dispose a`), `.suppressed` 가 **본문 쪽**(`body`). ★ 이름이 헷갈리는 자리다 — **「억눌린(suppressed) 것」 이 원래 오류**이고, 겉에 드러나는 `.error` 가 **나중 오류**다(명세: 새 오류를 `"error"`, 앞의 완료를 `"suppressed"` 에).
- ★★★ **`[3]` — 해제마다 한 겹씩** — 역순으로 `b` 가 먼저 던져 `SuppressedError(b, body)` 가 되고, `a` 가 또 던져 **그것을 `.suppressed` 로 감싼다.** 본문 오류는 **맨 안쪽**에 있다.
- ★★ **`[2]` — 본문이 정상이면 감싸지 않는다** — 해제 오류 **그대로** `Error 「dispose a」`. `SuppressedError` 는 「**던진 것이 둘 이상**」 일 때만 생긴다(Java 26 의 「둘 다 던져야 한다」 와 같은 조건).
- ★★ **`[4]` — 한 해제가 던져도 나머지는 계속** — `b` 가 던졌는데 `log: dispose a` — 끝까지 치운 **뒤에** 던진다.
- ★★ **`[5]`·`[6]` — `message` 는 누구의 것인가** — 생성자로 만들면 `.message m`(명세 20.5.8.1.1). **해제가 만든 것**은 `An error was suppressed during disposal` 이고 own 속성 `message error suppressed` 가 있다 — ★ **이 문서가 읽은 `DisposeResources` 단계에는 `message` 가 없다** — 문구는 **V8 이 더한 것**이다(층: 엔진).

### (5) ★★ `DisposableStack` — 실행 중에 정해지는 장부

**언제 쓰나** — 자원이 **몇 개일지 실행 중에야** 알 때 · 생성자 안에서 열다가 중간에 실패하면 연 것만 치우고 싶을 때.

```js
// js48b-51e-stack.js
// DisposableStack: collect clean-up steps at run time and undo them in one go.
const log = [];
const res = (name) => ({ name, [Symbol.dispose]() { log.push("dispose " + name); } });
const run = (label, f) => {
  let r;
  try { r = "ok " + String(f()); } catch (e) { r = e.constructor.name + " 「" + e.message + "」"; }
  console.log("  " + label.padEnd(46) + r);
};
console.log("[1] use · adopt · defer, then dispose()");
const s = new DisposableStack();
run("s.use(res('a')).name", () => s.use(res("a")).name);
run("s.adopt('b', (v) => log.push('adopt ' + v))", () => s.adopt("b", (v) => log.push("adopt " + v)));
run("s.defer(() => log.push('defer c'))", () => s.defer(() => log.push("defer c")));
run("s.use(null)", () => s.use(null));
run("s.use({})", () => s.use({}));
run("s.disposed", () => s.disposed);
run("s.dispose()", () => s.dispose());
console.log("    log: " + log.join(" · "));
run("s.disposed", () => s.disposed);
run("s.dispose()   (again)", () => s.dispose());
run("s.use(res('d'))   (after dispose)", () => s.use(res("d")));
console.log("[2] move() hands the steps to a new stack");
log.length = 0;
const t = new DisposableStack();
t.use(res("e"));
const u = t.move();
run("t.disposed · u.disposed", () => t.disposed + " · " + u.disposed);
run("t.dispose()", () => t.dispose());
console.log("    log after t.dispose(): [" + log.join(" · ") + "]");
run("u.dispose()", () => u.dispose());
console.log("    log after u.dispose(): [" + log.join(" · ") + "]");
console.log("[3] a stack held by using");
log.length = 0;
{
  using st = new DisposableStack();
  st.use(res("f"));
  st.defer(() => log.push("defer g"));
  log.push("block body");
}
console.log("    log: " + log.join(" · "));
```

```text
===== ./js48b-browser.sh js48b-51e-stack.js (exit=0) =====
[1] use · adopt · defer, then dispose()
  s.use(res('a')).name                          ok a
  s.adopt('b', (v) => log.push('adopt ' + v))   ok b
  s.defer(() => log.push('defer c'))            ok undefined
  s.use(null)                                   ok null
  s.use({})                                     TypeError 「Symbol(Symbol.dispose) is not a function」
  s.disposed                                    ok false
  s.dispose()                                   ok undefined
    log: defer c · adopt b · dispose a
  s.disposed                                    ok true
  s.dispose()   (again)                         ok undefined
  s.use(res('d'))   (after dispose)             ReferenceError 「Cannot call DisposableStack.prototype.use on an already-disposed DisposableStack」
[2] move() hands the steps to a new stack
  t.disposed · u.disposed                       ok true · false
  t.dispose()                                   ok undefined
    log after t.dispose(): []
  u.dispose()                                   ok undefined
    log after u.dispose(): [dispose e]
[3] a stack held by using
    log: block body · defer g · dispose f
```

- ★★ **`[1]` — 넣은 역순**: `use(a)` · `adopt(b)` · `defer(c)` 순으로 넣었더니 `defer c · adopt b · dispose a`(명세 27.3 「disposed in reverse order」). `use` 는 **값을 그대로 돌려준다**(`ok a`) · `use(null)` 은 받고 · `use({})` 는 `using` 과 같은 `TypeError`.
- ★★ **두 번째 `dispose()` 는 조용히 `undefined`** · **dispose 뒤 `use` 는 `ReferenceError`**(명세 — 「If … disposed, throw a ReferenceError」). 이미 닫힌 장부에 **적는 것**만 막는다.
- ★★ **`[2]` `move()` — 장부를 통째로 넘긴다**: `t` 는 곧바로 `disposed true` 가 되고 `t.dispose()` 는 **아무것도 안 치운다**(`[]`). 「생성자에서 다 열 때까지는 내 장부 — 성공하면 `move()` 로 객체에게 넘긴다」 는 관용구가 이 동작이다.
- ★ **`[3]` — 스택 자체가 disposable** — `using st = new DisposableStack()` 이면 블록 끝에 스택이 **자기 장부를 역순으로** 치운다.

### (6) ★★ `await using` — 해제를 하나씩 기다린다 · `null` 도 한 틱

**언제 쓰나** — 닫는 데 비동기가 필요한 자원(스트림 · 원격 연결) · 「닫기를 기다렸나」 를 확인할 때.
★ 블록 안에서 마이크로태스크 `tick 1`\~`tick N` 을 미리 걸어 두고, **블록이 끝난 뒤** `after the block` 이 몇 번째 틱 뒤에 오는지 본다.

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

```text
===== ./js48b-browser.sh js48b-51f-await-using.js (exit=0) =====
[1] two async resources
    body · start async dispose b · tick 1 · end async dispose b · tick 2 · start async dispose a · tick 3 · end async dispose a · tick 4 · after the block
[2] a value with only Symbol.dispose
    body · sync dispose a · tick 1 · tick 2 · after the block · tick 3
[3] null as the value
    body · tick 1 · tick 2 · after the block · tick 3
[4] no await using at all
    body · tick 1 · after the block · tick 2 · tick 3
[5] plain using holding an object that has only Symbol.asyncDispose
    TypeError 「Symbol(Symbol.dispose) is not a function」 · after the block
```

```text
   [4] await using 없음         body · tick 1 · after the block · …
   [3] await using x = null     body · tick 1 · tick 2 · after the block      ← 한 틱 더 (명세 NOTE)
   [2] Symbol.dispose 만 있음    body · sync dispose a · tick 1 · tick 2 · after the block
   [1] async 둘                 body · start b · tick 1 · end b · tick 2 · start a · tick 3 · end a · tick 4 · after
```

- ★★★ **`[1]` — 역순 · 하나씩 기다린다**: `end async dispose b` 가 끝난 **뒤에야** `start async dispose a`. 둘이 겹치지 않는다(`Promise.all` 이 아니다).
- ★★★ **`[3]` — `null` 이어도 기다린다**: `[4]`(없음)은 `tick 1` 뒤에 끝나는데 `[3]` 은 **`tick 2` 뒤** — 명세 NOTE 「null·undefined 여도 **여전히 Await** 하도록 기록한다」 가 이 한 틱이다. ★ 「값이 없으면 공짜」 가 아니다 — `await using` 은 **값과 무관하게 비동기 경계를 만든다.**
- ★★ **`[2]` — `Symbol.dispose` 만 있으면 그것을 쓰고, 그래도 기다린다**(명세 `GetDisposeMethod` — async 쪽이 없으면 sync 메서드를 감싼다).
- ★★ **`[5]` — 반대는 안 된다**: 그냥 `using` 에 `Symbol.asyncDispose` 만 있는 객체를 주면 **`TypeError`**(`Symbol(Symbol.dispose) is not a function`). 동기 `using` 은 비동기 메서드를 **찾지 않는다.**

### (7) ★★ `using` 이 없는 판에서 — 손으로 쓴 `try`/`finally`

**언제 쓰나** — node 18·20 처럼 문법이 없는 곳에서 같은 보장을 흉내 낼 때.
★ 이 창은 **제5의 상태**다 — node 에서 `using` 을 못 재니, 같은 질문을 **손 코드**로 다시 물었다(머리말 창 표). 세 판에서 돌렸다.

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

```text
===== node20 js48b-51g-by-hand.js (exit=0) =====
[1] three resources, one try/finally each
    body · dispose c · dispose b · dispose a
[2] the body throws, the resource throws while disposing -- plain try/finally
    caught Error 「dispose r」
[3] the same, keeping both errors by hand
    caught SuppressedByHand 「kept both」 · .error dispose r · .suppressed body
```

Chrome 151 — `[3]` 의 생성자 이름만 다르다(진짜 `SuppressedError` 가 있어서 그쪽을 썼다).

```text
===== ./js48b-browser.sh js48b-51g-by-hand.js (exit=0) =====
[1] three resources, one try/finally each
    body · dispose c · dispose b · dispose a
[2] the body throws, the resource throws while disposing -- plain try/finally
    caught Error 「dispose r」
[3] the same, keeping both errors by hand
    caught SuppressedError 「kept both」 · .error dispose r · .suppressed body
```

- ★★ **`[1]` — 역순은 손으로도 나온다** — 중첩한 `try`/`finally` 가 **안쪽부터** 닫히니까. 대가는 **자원마다 한 겹**이다.
- ★★★ **`[2]` — 본문 오류가 사라진다**: `caught Error 「dispose r」`. **32번이 이미 잰 그 결과**다(`finally` 가 던지면 원래 예외는 흔적 없이 — 거기 동작 (2)의 `[4]`). `using` 의 동작 (4) `[1]` 과 **정확히 반대** 칸이다.
- ★★ **`[3]` — 둘 다 남기려면 손으로 잡아 두어야 한다** — 본문 오류를 변수에 받고 · 해제를 따로 `try` 하고 · 둘 다 있으면 감싼다. node 는 `SuppressedError` 가 없어 **이 파일의 클래스 `SuppressedByHand`** 를 썼다. `using` 이 해 주는 일이 **이만큼**이다.

### (8) ★★ tsc 7.0.2 는 `using` 을 낮추나 — 방출물을 세 판에서

**언제 쓰나** — TS 로 `using` 을 쓰고 node 18·20 에 배포할 때.
★ 설정 파일도 소스다(규칙 20) — `tsconfig.json` 을 같이 싣는다. 이 창도 **제5의 상태**다 — node 에서 `using` 을 **tsc 가 쓴 코드로** 물었다.

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

```text
===== ./js48b-51h-tsc.sh (exit=0) =====
tsc Version 7.0.2
tsc -p .   (target es2022) exit=0
  lines of out/in51h.js that contain 'using ': 0
  helpers defined: __addDisposableResource __disposeResources 
  TypeError messages in the helpers: "Object expected." "Symbol.asyncDispose is not defined." "Symbol.dispose is not defined." "Object not disposable." 
--- out/in51h.js after the two helpers
const log = [];
const res = (name, throws = false) => ({
    [Symbol.dispose]() { log.push("dispose " + name); if (throws)
        throw new Error("dispose " + name); },
});
function order() {
    const env_2 = { stack: [], error: void 0, hasError: false };
    try {
        const a = __addDisposableResource(env_2, res("a"), false), b = __addDisposableResource(env_2, res("b"), false), c = __addDisposableResource(env_2, res("c"), false);
        log.push("body");
    }
    catch (e_2) {
        env_2.error = e_2;
        env_2.hasError = true;
    }
    finally {
        __disposeResources(env_2);
    }
}
order();
console.log("[1] " + log.join(" · "));
try {
    const env_1 = { stack: [], error: void 0, hasError: false };
    try {
        const r = __addDisposableResource(env_1, res("r", true), false);
        throw new Error("body");
    }
    catch (e_1) {
        env_1.error = e_1;
        env_1.hasError = true;
    }
    finally {
        __disposeResources(env_1);
    }
}
catch (e) {
    console.log("[2] caught constructor " + e.constructor.name + " · name " + e.name + " · 「" + e.message + "」" +
        " · .error " + e.error?.message + " · .suppressed " + e.suppressed?.message);
}
console.log("[3] typeof SuppressedError " + typeof SuppressedError + " · String(Symbol.dispose) " + String(Symbol.dispose));
--- node18 out/in51h.js
[1] body · dispose c · dispose b · dispose a
[2] caught constructor Error · name SuppressedError · 「An error was suppressed during disposal.」 · .error dispose r · .suppressed body
[3] typeof SuppressedError undefined · String(Symbol.dispose) Symbol(nodejs.dispose)
--- node20 out/in51h.js
[1] body · dispose c · dispose b · dispose a
[2] caught constructor Error · name SuppressedError · 「An error was suppressed during disposal.」 · .error dispose r · .suppressed body
[3] typeof SuppressedError undefined · String(Symbol.dispose) Symbol(nodejs.dispose)
--- Chrome 151 out/in51h.js
[1] body · dispose c · dispose b · dispose a
[2] caught constructor SuppressedError · name SuppressedError · 「An error was suppressed during disposal.」 · .error dispose r · .suppressed body
[3] typeof SuppressedError function · String(Symbol.dispose) Symbol(Symbol.dispose)

tsc -p . --target esnext --outDir out-esnext   exit=0
  lines of out-esnext/in51h.js that contain 'using ': 2
  node18 parses out-esnext/in51h.js: SyntaxError 「Unexpected identifier」
  node20 parses out-esnext/in51h.js: SyntaxError 「Unexpected identifier 'a'」
```

```text
   in51h.ts ──tsc (target es2022)──▶ out/in51h.js
     using a = …, b = …, c = …;         const env = { stack: [], error: void 0, hasError: false };
                                        try   { const a = __addDisposableResource(env, …, false), … }
                                        catch (e) { env.error = e; env.hasError = true; }
                                        finally   { __disposeResources(env); }   ← stack.pop() 으로 역순

   in51h.ts ──tsc (target esnext)───▶ out-esnext/in51h.js     using 이 그대로 남는다 (2줄)
                                        node18 · node20: SyntaxError
```

- ★★★ **`--target es2022` 면 낮춘다** — 방출물에 `using ` 이 **0줄**, 헬퍼 **`__addDisposableResource`·`__disposeResources`** 두 개. node 18 · 20 에서 **역순 `dispose c · dispose b · dispose a`** 와 **두 오류가 다 남는 모양**(`.error dispose r · .suppressed body`)이 나왔다.
- ★★★ **그러나 node 의 `SuppressedError` 는 가짜다** — `caught constructor Error · name SuppressedError`. 헬퍼가 `typeof SuppressedError === "function"` 이 아니면 **`new Error(message)` 에 `name` 만 바꿔 단다.** 그래서 **`e instanceof SuppressedError` 는 node 에서 못 쓴다**(전역이 없다). Chrome 에서는 같은 방출물이 **진짜 생성자**를 쓴다(`constructor SuppressedError`).
- ★★ **헬퍼는 `Symbol.dispose` 를 그냥 읽는다** — node 에서 `String(Symbol.dispose) Symbol(nodejs.dispose)`. 입력 객체도 같은 `Symbol.dispose` 로 메서드를 달았으니 **둘이 맞아서** 돈다. ★ 헬퍼가 던지는 `TypeError` 문구 넷 중 하나가 **`Symbol.dispose is not defined.`** 다(블록의 `TypeError messages in the helpers` 줄 — 헬퍼 본문은 싣지 않았다). 헬퍼는 심볼이 **없으면 그 자리에서 던지게** 짜여 있고, 이 판들에서는 node 가 심볼을 가지고 있어 그 줄에 닿지 않았다.
- ★★ **`--target esnext` 면 안 낮춘다** — `using ` **2줄**이 그대로 남고 node 18 · 20 은 파싱부터 실패(`Unexpected identifier` · `Unexpected identifier 'a'`). **target 이 곧 「누가 `using` 을 실행하나」 의 선택**이다.
- ★ **메시지의 마침표** — 헬퍼가 넣는 문구는 `An error was suppressed during disposal.`(마침표 있음), Chrome 의 엔진 문구는 **마침표 없음**(동작 (4)). 문구로 판을 가르지 마라.

### (9) ★ 다른 갈래와 한 줄씩 — 인용만

| 갈래 | 선언 | 해제 순서 | 해제가 던지면 | 그 편이 잰 것 |
|---|---|---|---|---|
| JS `using` | `using x = v` · `await using` | 역순 | `SuppressedError` 로 **겹친다** | 이 문서 동작 (3)·(4) |
| [Python 28](../../../python/syntax/28-context-managers-and-with/2-summary.md) | `with` · `ExitStack` | 역순(「해제가 역순이라는 것」 을 언어 보장으로 적었다) | **`__context__` 사슬** — 묶음이 아니다(`BaseExceptionGroup` 이 네 경우 다 `False`) | 거기 3절 · 「어디서 틀리나 (10)」 |
| [Java 26](../../../java/syntax/26-try-with-resources/2-summary.md) | `try (R r = …)` | 연 역순 | 주 예외에 **`addSuppressed`** 로 첨부 · 둘 다 던져야 생긴다 · 손으로 쓴 `try`-`finally` 는 본문 예외를 **잃는다** | 거기 동작 (1)·(3)·(4) |
| C# | `using` 선언(C# 8) · `IAsyncDisposable` | — | — | C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **37번** — 아직 폴더가 없다 |

- ★★ **Java 와 가장 닮았다** — 「둘 다 던져야 첨부가 생긴다」 · 「손으로 쓴 `finally` 는 본문 예외를 잃는다」 가 동작 (4) `[2]` · 동작 (7) `[2]` 와 같은 칸이다. **다른 점은 모양** — Java 는 **주 예외에 매달고**(주인공은 본문 예외), JS 는 **새 `SuppressedError` 가 겉**이고 본문 오류는 `.suppressed` 안으로 **들어간다.**
- ★ 「언제 치우나」 가 **문법상의 순간**이라는 점은 세 갈래가 같다 — 47번의 GC 콜백과 다른 쪽이다.

## 문법 — 형태와 규칙

★ 이 절은 **형태 표**다 — 모든 동작 주장은 위 동작 절의 캡처 블록에서만 한다.

| 형태 | 하는 일 | 어디서 봤나 |
|---|---|---|
| `using x = v;` · `using a = v1, b = v2;` | 블록 끝에 `v[Symbol.dispose]()` · 여럿이면 **역순** · 바인딩은 **다시 대입 불가** | 동작 (3) |
| `await using x = v;` | async 함수·모듈 최상위에서만 · `Symbol.asyncDispose`(없으면 `Symbol.dispose`)를 **기다린다** | 동작 (2)·(6) |
| `for (using x of it)` · `for (using x = v; …; …)` | 반복마다 해제 · `for (using x in …)` 는 **Syntax Error** | 동작 (2)·(3) |
| `new DisposableStack()` — `use(v)` · `adopt(v, fn)` · `defer(fn)` · `move()` · `dispose()` · `disposed` | 실행 중에 쌓는 장부 · 역순 · 닫힌 뒤 `use`·`move` 는 `ReferenceError` | 동작 (5) |
| `new SuppressedError(error, suppressed, message)` | `.error` · `.suppressed` · `.message` — `Error` 를 잇는다 | 동작 (4)의 `[5]` |
| `obj[Symbol.dispose]()` · `async obj[Symbol.asyncDispose]()` | 자원 쪽이 구현하는 메서드 | 동작 (3)·(6) |

**못 쓰는 자리** — 컴파일이 안 되는 꼴이라 코드 펜스가 아니라 표로 적는다(규칙 28). 전부 동작 (2)의 Chrome 151 블록에 있다.

| 쓴 꼴 | Chrome 151 의 `SyntaxError` 문구 | 근거 |
|---|---|---|
| 고전 스크립트 최상위의 `using x = …;` | `Unexpected identifier 'x'` | 명세 16.1.1 |
| `case 1: using x = …;` | `Unexpected identifier 'x'` | 명세 14.12.1 |
| `for (using x in …)` | `Invalid 'using' in for-in loop` | V8 문구 |
| `using x;` | `Missing initializer in using declaration` | 명세 14.3.1.1 |
| `using { a } = …;` | `Unexpected token '{'` | 문법 `~Pattern` |
| async 밖의 `await using x = …;` | `await is only valid in async functions and the top level bodies of modules` | — |

## 어디서 틀리나

### (1) ★★★ `Symbol.dispose` 가 있으면 `using` 도 된다고 판단한다

node 18·20 은 **심볼만 있고 문법이 없다**(`11 / 21` 중 node 의 두 칸). 게다가 그 심볼은 `Symbol.for("nodejs.dispose")` 다. 문법 지원은 **파싱으로** 물어라(동작 (1)).

### (2) ★★★ `.error` 가 원래 오류라고 읽는다

**반대다** — `.error` 는 **해제가 던진 나중 오류**, 원래 본문 오류는 **`.suppressed`** 안에 있다. 여럿이 던지면 본문 오류는 **맨 안쪽**까지 파고들어야 나온다(동작 (4)의 `[3]`).

### (3) ★★★ `finally { r.close(); }` 로 `using` 과 같은 것을 얻었다고 믿는다

순서는 같지만 **해제가 던지면 본문 오류를 잃는다**(동작 (7) `[2]` · 32번). 둘 다 남기려면 동작 (7) `[3]` 만큼 써야 한다.

### (4) ★★ 파일 맨 위(고전 스크립트)나 `case` 바로 밑에 `using` 을 둔다

둘 다 **Syntax Error** — 문구가 「`using` 을 모르는 엔진」 과 **같아서** 원인을 잘못 짚기 쉽다. 블록 `{ … }` 으로 한 겹 감싸거나 모듈로 싣는다(동작 (2)).

### (5) ★★ 여러 자원을 연 순서대로 닫힌다고 믿는다

**역순**이다 — 뒤에 연 것이 앞에 연 것에 기대고 있을 수 있기 때문이다(동작 (3)의 `[1]`). 순서를 바꾸고 싶으면 선언 순서를 바꾼다.

### (6) ★★ `await using x = null` 은 아무 일도 안 한다고 믿는다

**한 틱을 기다린다**(동작 (6)의 `[3]`). 조건부로 자원을 여는 코드에서 `null` 이 들어가도 **비동기 경계는 생긴다.**

### (7) ★★ 선언 뒤에 `[Symbol.dispose]` 를 갈아 끼우면 새 것이 불린다고 믿는다

**선언 때 읽은 것**이 불린다(동작 (3)의 `[9]`). 해제 동작을 바꾸려면 선언 **전에** 바꾼다.

### (8) ★★ tsc 로 낮춘 코드에서 `e instanceof SuppressedError` 로 가른다

node 에는 전역 `SuppressedError` 가 **없고**(동작 (8)의 `[3] typeof SuppressedError undefined`), 헬퍼가 만든 것은 **`name` 만 `SuppressedError` 인 `Error`** 다(동작 (8)). `e.name === "SuppressedError"` 와 `"suppressed" in e` 로 가른다.

## 구현 세부사항 대 언어 보장

### 명세 보장(ECMA-262 초안 — 확인한 엔진은 Chrome 151 하나)

- ★★★ **역순** 해제 · 블록을 떠나는 모든 완료에서 해제 · `null`/`undefined` 건너뜀 · 객체가 아니면 `TypeError` · 메서드는 선언 때 읽음.
- ★★★ 해제 중 예외 — 앞의 완료가 throw 면 **`SuppressedError`**(`error` = 새것 · `suppressed` = 앞의 것) · 한 해제가 던져도 **나머지를 계속** 해제.
- ★★ `await using` 은 `null`/`undefined` 여도 **Await 한다** · async 쪽이 없으면 sync 메서드를 감싼다.
- ★★ **스크립트 최상위 · `case`/`default` 절 바로 밑은 Syntax Error** · 구조 분해 패턴 없음 · 초기자 필수.
- ★ `DisposableStack` — 역순 · 닫힌 뒤 `use`·`move` 는 `ReferenceError`.

### 엔진(V8) — 문구와 더한 것

- ★★ 모든 **문구**(`Unexpected identifier 'x'` · `Invalid 'using' in for-in loop` · `Assignment to using variable.` · `Symbol(Symbol.dispose) is not a function`) — node 18(V8 10.2)은 같은 자리에서 **식별자 없는** `Unexpected identifier` 를 냈다.
- ★★ 해제가 만든 `SuppressedError` 의 **`message`**(`An error was suppressed during disposal`) — 명세 단계에 없다.

### 호스트(node)

- ★★★ node 18·20 의 **`Symbol.dispose`·`Symbol.asyncDispose`** — `Symbol.for("nodejs.dispose")`·`Symbol.for("nodejs.asyncDispose")`. **node 가 정한 것**이고 명세의 well-known symbol 과 **다른 심볼**이다. ★ node 가 이 심볼을 왜·어디에 쓰는지는 이 문서가 **확인하지 않았다**(node 문서·소스를 안 읽었다).

### 도구(tsc 7.0.2)

- ★★ `--target es2022` 에서 헬퍼 두 개로 낮춘다 · `SuppressedError` 를 흉내 낸다 · `Symbol.dispose` 가 없으면 `TypeError("Symbol.dispose is not defined.")`. ★ **헬퍼 코드의 모양은 이 판의 관찰**이다.

### 그래서 이렇게 적으면 틀린다

- ✗ 「node 20 은 `Symbol.dispose` 를 지원하므로 `using` 을 쓸 수 있다」 → ○ 「**문법이 없다** — 심볼은 node 의 것이다」
- ✗ 「`SuppressedError.error` 에 원래 오류가 담긴다」 → ○ 「**`.suppressed`** 에 담긴다 — `.error` 는 해제 쪽」
- ✗ 「`using` 은 어디서나 `const` 대신 쓸 수 있다」 → ○ 「**고전 스크립트 최상위 · `case` 절 바로 밑**에서는 Syntax Error」
- ✗ 「해제 중 오류 메시지 『An error was suppressed during disposal』 은 명세가 정한다」 → ○ 「**V8 이 붙인 것** — 명세 단계에는 `message` 가 없다」

## 언제 쓰고 언제 안 쓰나

- **`using`** — 블록 하나에 **수명이 묶인** 자원(파일 핸들 · 락 · 임시 구독). Chrome 151 처럼 **문법이 있는 런타임**이거나, tsc 로 **낮춰서** 배포할 때.
- **`await using`** — 닫기가 비동기인 자원. `null` 도 한 틱이 든다는 것을 알고 쓴다.
- **`DisposableStack`** — 자원 수가 실행 중에 정해질 때 · 생성자에서 여럿을 열다 **실패하면 연 것만** 치우고, 성공하면 `move()` 로 넘길 때.
- **손으로 쓴 `try`/`finally`** — 문법이 없는 런타임에서 tsc 도 안 쓸 때. 해제가 던질 수 있으면 동작 (7) `[3]` 처럼 **본문 오류를 따로 잡아 둔다.**
- ★ **안 쓰는 자리** — GC 에 맡길 수명(47번의 `WeakRef` 캐시처럼 **비워져도 맞게 도는** 것) · 블록을 넘어 사는 자원(그때는 `DisposableStack` 을 `move()` 로 들고 나간다).

## 핵심 문장

1. ★★★ **`supported cells: 11 / 21`** — Chrome 151 은 일곱 기능이 다 있고, node 18·20 은 `Symbol.dispose`·`Symbol.asyncDispose` **둘뿐**이다 — 그것도 `Symbol.for("nodejs.dispose")` 인 **node 의 심볼**이다.
2. ★★★ 해제는 **역순** · **블록마다** · 떠나는 **모든 길**에서 — `null` 은 건너뛰고, 메서드는 **선언 때** 읽는다.
3. ★★★ 해제가 던지면 `SuppressedError` — **`.error` 가 나중(해제) · `.suppressed` 가 앞(본문)** · 여럿이면 한 겹씩. 손으로 쓴 `try`/`finally` 는 본문 오류를 **잃는다**(32번).
4. ★★ **고전 스크립트 최상위 · `case` 절 바로 밑은 Syntax Error** — 문구가 「모르는 엔진」 과 같아 헷갈린다. `await using` 은 `null` 이어도 **한 틱** 기다린다.
5. ★★ tsc 7.0.2 `--target es2022` 는 헬퍼로 **낮춰 node 18·20 에서 돈다** — 단 `SuppressedError` 는 **`name` 만 바꾼 `Error`** 다.

## 관련 자료

- [ECMA-262 — Operations on Disposable Objects](https://tc39.es/ecma262/multipage/abstract-operations.html) · [Declarations / switch](https://tc39.es/ecma262/multipage/ecmascript-language-statements-and-declarations.html) · [Scripts](https://tc39.es/ecma262/multipage/ecmascript-language-scripts-and-modules.html) · [SuppressedError](https://tc39.es/ecma262/multipage/fundamental-objects.html) · [DisposableStack](https://tc39.es/ecma262/multipage/control-abstraction-objects.html)
- [32 — 오류 처리와 `Error`](../32-error-handling-and-error/2-summary.md) — ★ **경계**: `try`/`finally` 의 흐름 · `finally` 가 던지면 원래 예외가 사라지는 것은 거기. 여기는 **`using` 이 그것을 어떻게 바꾸나.**
- [20 — 제너레이터](../20-generators/2-summary.md) · [40 — 비동기 이터레이션](../40-async-iteration-and-for-await/2-summary.md) — ★ **경계**: 이터레이터를 닫는 `return()` 은 거기. 여기의 `for (using x of …)` 는 **값**을 닫고, 이터레이터를 닫는 것은 여전히 그쪽 규칙이다.
- [47 — `WeakRef`·`FinalizationRegistry`](../47-weakref-and-finalizationregistry/2-summary.md) — GC 에 맡긴 정리(비결정) 대 이 문서(문법상의 순간).
- [22 — `Symbol`](../22-symbol-and-well-known-symbols/2-summary.md) · [52 — `switch`·라벨·흐름 제어](../52-switch-labels-and-control-flow/2-summary.md)(`switch` 블록과 스코프 — `case` 절에 `using` 이 못 서는 뿌리).
- [Python 28](../../../python/syntax/28-context-managers-and-with/2-summary.md) · [Java 26](../../../java/syntax/26-try-with-resources/2-summary.md) · TS 갈래 목록([`ts/syntax/README.md`](../../../ts/syntax/README.md))의 버전 표 **5.2** 행.

## 용어 풀이

- **`using` 선언** — 블록이 끝날 때 값의 `[Symbol.dispose]()` 를 부르게 하는 선언. 바인딩은 상수.
- **`await using`** — 같은 일을 비동기로 — `[Symbol.asyncDispose]()` 의 결과를 기다린다. async 함수·모듈 최상위에서만.
- **`Symbol.dispose` · `Symbol.asyncDispose`** — 자원이 구현하는 메서드의 키. 명세에서는 well-known symbol(등록 안 된 심볼).
- **`DisposableStack`** — 해제 단계를 실행 중에 쌓아 두는 객체. 역순으로 치운다.
- **`SuppressedError`** — 해제 중 오류와 그 앞의 오류를 함께 담는 오류 — `.error`(새것) · `.suppressed`(앞의 것).
- **disposable resource stack(장부)** — 명세가 블록의 환경 레코드마다 두는 목록. `using` 이 선언될 때 적고, 블록이 끝날 때 거꾸로 읽는다.
- **`Symbol.for` 레지스트리** — 문자열 키로 심볼을 나눠 쓰는 전역 목록. `Symbol.keyFor(s)` 가 그 키를 돌려준다(등록 안 된 심볼이면 `undefined`).
- **간접 `eval`** — `(0, eval)(text)` 처럼 부른 `eval` — 텍스트를 **전역 스크립트**로 파싱한다.
- **낮춰 쓰기(down-leveling)** — 새 문법을 옛 판에서 도는 코드로 바꿔 방출하는 것(tsc 의 `target`).

## 더 들어가면

- **`AsyncDisposableStack`** — Chrome 151 에 있다(동작 (1)). 이 문서는 격자 한 칸으로만 확인했다.
- **이터레이터 헬퍼의 `Iterator.prototype[Symbol.dispose]`** — 이 문서가 읽은 초안 목차(27.1.3.3.13)에 있다. 돌리지 않았다.
- **node 가 문법을 받는 판** — 이 머신의 node 는 18·20 뿐이라 **확인하지 않았다.** 그 판의 `Symbol.dispose` 가 여전히 `nodejs.dispose` 인지도 다시 재야 할 칸이다.
