# js/syntax/29 — 정규식 기본: 「`g` 정규식은 상태를 들고 다닌다 · `match` 는 `g` 로 모양이 바뀐다 · 리터럴은 평가마다 새 객체다」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> ★★★ **이 주제의 본체는 ① 추상 연산에 로그 심기다.**
> `/a/g.test('a')` 를 **같은 입력에 네 번** 부르면 답이 `true` · `false` · `true` · `false` 로 번갈아 나온다. 입력도 정규식도 안 바꿨는데 답이 바뀐다 —
> 그 이유는 **정규식 객체 안의 `lastIndex`** 다. 그래서 **호출 전과 후의 `lastIndex` 를 매번 찍는 로그**를 심었다(동작 (1)).
> ★★ 보조로 **② 전수 격자**(`match` 의 반환 모양 — `g` 유무 · 명명 그룹 · 실패 × 속성 일곱 — 동작 (2))와 **③ 브랜드 태그**(`matchAll` 이 돌려주는 것 — 동작 (3)), **④ 예외의 이름·문구**(동작 (3)·(6)·(7))를 쓴다.
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262 — RegExp (Regular Expression) Objects](https://tc39.es/ecma262/multipage/text-processing.html#sec-regexp-regular-expression-objects) —
>   `RegExpBuiltinExec` · `RegExpExec` · `RegExp.prototype.test`/`exec` · `RegExp.prototype [ %Symbol.match% ]`/`[ %Symbol.matchAll% ]`/`[ %Symbol.replace% ]`/`[ %Symbol.search% ]` · `get RegExp.prototype.flags` · `RegExp ( pattern, flags )` · `%RegExpStringIteratorPrototype%`
> - [ECMA-262 — String.prototype.match / matchAll / replace / search](https://tc39.es/ecma262/multipage/text-processing.html#sec-string.prototype.match)
> - [ECMA-262 — Regular Expression Literals](https://tc39.es/ecma262/multipage/ecmascript-language-lexical-grammar.html#sec-literals-regular-expression-literals) — 리터럴의 조기 오류 · 평가마다 `RegExpCreate`
> - [TC39 finished proposals](https://github.com/tc39/proposals/blob/main/finished-proposals.md)(2026-09-26 받아 둔 사본) — 판 경계(`s` 플래그·명명 그룹 2018 · `matchAll` 2020 · `replaceAll` 2021 · Match Indices(`d`) 2022 · `v` 플래그 2024)
>
> ★★★ **명세 조항 번호는 인용하지 않는다.** 규칙 진술은 **추상 연산 이름**으로, 값·호출 로그·예외 타입과 메시지는 **전부 실행으로** 접지했다.
> ★★ **정규식의 매칭 알고리즘은 이 주제가 아니다** — 명세는 패턴이 **무엇과 맞는가(의미)** 를 정하고, 그것을 **어떻게 찾나**는 엔진(V8 은 Irregexp)의 몫이다. 알고리즘은 [`cs/algorithm/25-string-matching/`](../../../../../algorithm/25-string-matching/2-summary.md)과 30번이다.
>
> **실행 검증** — 이 문서의 모든 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮겨 적은 출력이 하나도 없다).
> 배너의 `node20` 은 `~/.nvm/versions/node/v20.19.6/bin/node`, `node18` 은 기본 PATH 의 `node`(v18.19.1)다.
> ★★ **예외는 `try`/`catch` 로 받아 `e.constructor.name` 과 `e.message` 만** `이름 「메시지」` 꼴로 찍었다 — 스택트레이스에는 절대 경로가 박혀 재현이 안 된다.
> ★★ **이 주제의 node 탐침 일곱 개 중 두 판이 갈린 것은 하나**(`js28b-29f-flags.js`)이고, 갈린 줄은 **`v` 플래그(ES2024) 한 줄**이다.
> ★ 파이썬 대비(동작 (8))는 `python3 - <<'PY'` 꼴의 셸 탐침이다. 예외는 같은 꼴로 받아 트레이스백이 없다.
>
> **버전** — 판별 블록이 세 판(node 18 · node 20 · Chrome 151)에 같은 스크립트를 던진다.
>
> | 무엇 | 판 | 이 머신에서 |
> |---|---|---|
> | 리터럴 · `test` · `exec` · `match` · `replace` · `search` · 플래그 `g` `i` `m` | ES5 이하 | 세 판 다 있다 |
> | ★ 리터럴이 **평가마다 새 객체** | **ES5** 부터(ES3 은 리터럴 하나에 객체 하나였다) | 세 판 다 그렇다(동작 (5)) |
> | 플래그 `u` · `y` · `flags` 접근자 | **ES2015** | 세 판 다 있다 |
> | 플래그 `s` · 명명 그룹 `(?<n>…)` | **ES2018** | 세 판 다 있다 |
> | `matchAll` | **ES2020** | 세 판 다 있다 |
> | `replaceAll` | **ES2021** | 세 판 다 있다(28번) |
> | 플래그 `d`(`hasIndices`) | **ES2022** | 세 판 다 있다 |
> | 플래그 `v`(`unicodeSets`) | **ES2024** | ★ **node 18 에 없다** — 동작 (6)의 한 줄이 갈린다(뜻은 30번) |
>
> **★★★ 이 주제가 쓰는 창 — 그리고 부적용인 창**
>
> | 창 | 이 주제에서 무엇을 보나 |
> |---|---|
> | ★★★ **① 추상 연산에 로그 심기**(본체) | 호출마다 **전과 후의 `lastIndex`**(동작 (1)) · `replace` 콜백이 받는 **인자의 개수와 순서**(동작 (4)) · `RegExp.prototype.exec` 을 감싸 **`matchAll` 이 언제 · 어느 객체로** 찾나(동작 (3)) |
> | ★★ **② 전수 격자** | `match` 의 여섯 경우 × 속성 일곱 — `g` 짝과 **갈린 칸을 스크립트가 센다**(동작 (2)) |
> | ★★ **③ 브랜드 태그** | `matchAll` 이 돌려준 것에 `Object.prototype.toString.call` 이 **`[object RegExp String Iterator]`** — 배열이 아니다(동작 (3)) |
> | ★★ **④ 예외의 `constructor.name` + `message`** | `g` 없는 `matchAll` 의 `TypeError` · 잘못된 플래그의 `SyntaxError` · 잘못된 패턴이 **리터럴이면 파싱 때** 나는 `SyntaxError`(동작 (6)·(7)) |
> | ★ **⑤ 두 판 대조기** | 이 주제의 node 탐침 중 **하나만** `DIFFERS` 이고, 그 차이는 **`v` 플래그의 유무** 한 줄이다 |
> | ★ **부적용 — 진단의 `(행,열)`**(18-C) | 리터럴의 조기 오류는 **「언제 났나」**(파싱 때, 죽은 코드 안에서도)가 요점이지 열이 요점이 아니다. `new Function` 으로 던져 **종류·문구·통과 여부**만 본다 |
> | ★ **안 쟀다 — 성능** | 「리터럴을 함수 밖으로 빼면 빠르다」·「`test` 가 `match` 보다 빠르다」를 **한 줄도 쓰지 않는다.** 시간을 한 번도 안 쟀다 — 센 것은 **호출 횟수**뿐이다(동작 (3)의 `exec` 네 번) |
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 예외 **문구** — V8 의 글자다(`String.prototype.matchAll called with a non-global RegExp argument` · `Invalid flags supplied to RegExp constructor 'gg'` · `Invalid regular expression: missing /`). **종류**(`TypeError`·`SyntaxError`)만 명세가 정한다 | ★★★ **`lastIndex` 의 값과 `test` 의 참/거짓 순서** · 격자의 칸과 「**N / M**」 · 콜백 인자의 **개수와 순서** · `exec` 호출 로그 · `flags` 의 **글자 순서** |
> | 대조기 블록의 **다른 주제 줄**(같은 배치가 한 대조기를 공유한다) | ★★ **이 주제의 탐침에는 재실행에서 흔들린 칸이 하나도 없다**(재대조 동일) |
>
> **선행** — [28 — `String` 메서드와 템플릿 리터럴](../28-string-methods-and-template-literals/2-summary.md)(★★★ 직접 선행 — **치환 문자열의 `$` 표기**와 `split` 이 `lastIndex` 를 안 쓰는 것은 거기서 쟀다) ·
> [19 — 이터러블 프로토콜과 `for...of`](../19-iterable-protocol-and-for-of/2-summary.md)(★★ 소비자가 **`return()` 을 부르는 자리**) ·
> [20 — 제너레이터](../20-generators/2-summary.md) · [21 — 이터레이터 헬퍼](../21-iterator-helpers/2-summary.md)(★ 한 번 소비한 이터레이터는 다시 안 돈다) ·
> [22 — `Symbol` 과 잘 알려진 심볼](../22-symbol-and-well-known-symbols/2-summary.md)(`Symbol.match`·`Symbol.replace` 가 문자열 메서드를 정규식에 넘기는 통로).
> **같은 배치** — [30 — 정규식 심화](../30-regexp-advanced/2-summary.md) · [31 — `JSON`](../31-json/2-summary.md).
>
> ★★ **경계 — 문자열 매칭 알고리즘은 [`cs/algorithm/25-string-matching/`](../../../../../algorithm/25-string-matching/2-summary.md)이 정본이다.** 그쪽은 **KMP 처럼 「어떻게 찾나」**, 여기는 **JS API 가 「무엇을 돌려주고 무슨 상태를 남기나」**.
> ★★ **경계 — 캡처·명명 그룹의 문법·룩어라운드·`u`/`v`·`d`·백트래킹은 30번이 정본이다.** 여기서는 **명명 그룹이 반환 모양을 어떻게 바꾸나**만 본다.
> ★ **경계 — 치환 문자열의 `$` 표기는 28번이 정본이다.** 여기서는 **치환 함수가 받는 인자**를 본다.

```sh
# js28b-versions.sh
#!/usr/bin/env bash
# 이 문서의 모든 출력이 어느 판에서 나왔는지 -- 그리고 판별 기능 표(js28b-features.js)를 세 판에 던진다.
# 대비에 쓰는 go · python3 의 판도 여기서 찍는다(도구가 없다고 적기 전에 버전 호출을 블록으로).
set -u -o pipefail
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
for n in "$N18" "$N20"; do
  "$n" -e 'console.log("node " + process.versions.node + "  v8 " + process.versions.v8 + "  unicode " + process.versions.unicode)'
  "$n" js28b-features.js
done
google-chrome --version | sed 's/ *$//'
google-chrome --headless --virtual-time-budget=2000 --dump-dom "file://$PWD/js28b-page.html?js28b-features.js" 2>/dev/null \
  | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' \
  | sed 's/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&amp;/\&/g'
"$HOME/.local/opt/go/bin/go" version
python3 --version
```
```js
// js28b-features.js
// 이 문서의 기능이 이 판에 있나 -- 판마다 같은 스크립트를 던진다(node 두 판 · Chrome).
// 문법 기능은 new RegExp / new Function 으로 물어서, 없는 판에서도 스크립트 전체가 죽지 않게 한다.
const has = (label, test) => {
  let r;
  try { r = test() ? "yes" : "no"; } catch (e) { r = "no (" + e.constructor.name + ")"; }
  console.log("  " + label.padEnd(52) + r);
};
const re = (src, flags) => () => (new RegExp(src, flags), true);
has("ES2015  String.raw / tagged templates", () => typeof String.raw === "function" && new Function("return String.raw`a`")() === "a");
has("ES2015  regexp flags u / y", () => re("a", "u")() && re("a", "y")());
has("ES2017  padStart / padEnd", () => typeof "".padStart === "function" && typeof "".padEnd === "function");
has("ES2018  regexp flag s (dotAll)", re(".", "s"));
has("ES2018  named groups (?<n>...)", re("(?<n>a)"));
has("ES2018  lookbehind (?<=...)", re("(?<=a)b"));
has("ES2018  unicode property \\p{...}", re("\\p{L}", "u"));
has("ES2018  bad escape allowed in tagged template", () => new Function("return ((s) => s[0])`\\unicode`")() === undefined);
has("ES2019  trimStart / trimEnd", () => typeof "".trimStart === "function" && typeof "".trimEnd === "function");
has("ES2019  well-formed JSON.stringify", () => JSON.stringify(String.fromCharCode(0xd800)) === '"\\ud800"');
has("ES2020  matchAll", () => typeof "".matchAll === "function");
has("ES2021  replaceAll", () => typeof "".replaceAll === "function");
has("ES2022  regexp flag d (hasIndices)", re("a", "d"));
has("ES2022  String.prototype.at", () => typeof "".at === "function");
has("ES2024  regexp flag v (unicodeSets)", re("[\\p{L}--[a-z]]", "v"));
has("ES2024  isWellFormed / toWellFormed", () => typeof "".isWellFormed === "function");
has("ES2025  RegExp.escape", () => typeof RegExp.escape === "function");
has("ES2025  duplicate named groups", re("(?<y>a)|(?<y>b)"));
has("ES2025  regexp modifiers (?i:...)", re("(?i:a)b"));
has("ES2026  JSON.rawJSON / JSON.isRawJSON", () => typeof JSON.rawJSON === "function" && typeof JSON.isRawJSON === "function");
has("ES2026  reviver receives context.source", () => { let s; JSON.parse("1", (k, v, c) => { s = c && c.source; return v; }); return s === "1"; });
has("host    structuredClone", () => typeof structuredClone === "function");
```
```text
===== ./js28b-versions.sh (exit=0) =====
node 18.19.1  v8 10.2.154.26-node.28  unicode 15.1
  ES2015  String.raw / tagged templates               yes
  ES2015  regexp flags u / y                          yes
  ES2017  padStart / padEnd                           yes
  ES2018  regexp flag s (dotAll)                      yes
  ES2018  named groups (?<n>...)                      yes
  ES2018  lookbehind (?<=...)                         yes
  ES2018  unicode property \p{...}                    yes
  ES2018  bad escape allowed in tagged template       yes
  ES2019  trimStart / trimEnd                         yes
  ES2019  well-formed JSON.stringify                  yes
  ES2020  matchAll                                    yes
  ES2021  replaceAll                                  yes
  ES2022  regexp flag d (hasIndices)                  yes
  ES2022  String.prototype.at                         yes
  ES2024  regexp flag v (unicodeSets)                 no (SyntaxError)
  ES2024  isWellFormed / toWellFormed                 no
  ES2025  RegExp.escape                               no
  ES2025  duplicate named groups                      no (SyntaxError)
  ES2025  regexp modifiers (?i:...)                   no (SyntaxError)
  ES2026  JSON.rawJSON / JSON.isRawJSON               no
  ES2026  reviver receives context.source             no
  host    structuredClone                             yes
node 20.19.6  v8 11.3.244.8-node.33  unicode 16.0
  ES2015  String.raw / tagged templates               yes
  ES2015  regexp flags u / y                          yes
  ES2017  padStart / padEnd                           yes
  ES2018  regexp flag s (dotAll)                      yes
  ES2018  named groups (?<n>...)                      yes
  ES2018  lookbehind (?<=...)                         yes
  ES2018  unicode property \p{...}                    yes
  ES2018  bad escape allowed in tagged template       yes
  ES2019  trimStart / trimEnd                         yes
  ES2019  well-formed JSON.stringify                  yes
  ES2020  matchAll                                    yes
  ES2021  replaceAll                                  yes
  ES2022  regexp flag d (hasIndices)                  yes
  ES2022  String.prototype.at                         yes
  ES2024  regexp flag v (unicodeSets)                 yes
  ES2024  isWellFormed / toWellFormed                 yes
  ES2025  RegExp.escape                               no
  ES2025  duplicate named groups                      no (SyntaxError)
  ES2025  regexp modifiers (?i:...)                   no (SyntaxError)
  ES2026  JSON.rawJSON / JSON.isRawJSON               no
  ES2026  reviver receives context.source             no
  host    structuredClone                             yes
Google Chrome 151.0.7922.173
  ES2015  String.raw / tagged templates               yes
  ES2015  regexp flags u / y                          yes
  ES2017  padStart / padEnd                           yes
  ES2018  regexp flag s (dotAll)                      yes
  ES2018  named groups (?<n>...)                      yes
  ES2018  lookbehind (?<=...)                         yes
  ES2018  unicode property \p{...}                    yes
  ES2018  bad escape allowed in tagged template       yes
  ES2019  trimStart / trimEnd                         yes
  ES2019  well-formed JSON.stringify                  yes
  ES2020  matchAll                                    yes
  ES2021  replaceAll                                  yes
  ES2022  regexp flag d (hasIndices)                  yes
  ES2022  String.prototype.at                         yes
  ES2024  regexp flag v (unicodeSets)                 yes
  ES2024  isWellFormed / toWellFormed                 yes
  ES2025  RegExp.escape                               yes
  ES2025  duplicate named groups                      yes
  ES2025  regexp modifiers (?i:...)                   yes
  ES2026  JSON.rawJSON / JSON.isRawJSON               yes
  ES2026  reviver receives context.source             yes
  host    structuredClone                             yes
go version go1.27.1 linux/amd64
Python 3.12.3
```

두 node 판 대조기의 집계 줄(이 배치의 모든 node 탐침) — 이 주제의 탐침(`js28b-29?-*.js`) 중 `DIFFERS` 는 `js28b-29f-flags.js` 하나다. 전문은 [3-answer.md](3-answer.md) 의 「실행 검증」에 있다.

`identical 19  ·  differs 6  ·  total 25`

## 한눈에 — 쉽게 말하면

**`g` 가 붙은 정규식은 「책갈피를 꽂아 두는 독자」다.**
한 번 찾으면 **찾은 자리 바로 뒤에 책갈피(`lastIndex`)를 꽂는다.** 다음에 같은 책을 주면 **책갈피부터** 읽는다.
끝까지 읽고도 못 찾으면 **책갈피를 빼고(`0`) 「없다」고 답한다.** 그래서 같은 책을 같은 독자에게 주면 **「있다 · 없다 · 있다 · 없다」** 가 번갈아 나온다.

- ★★★ **책갈피는 독자(정규식 객체)가 들고 있다** — 책(입력 문자열)이 아니다. 다른 책을 줘도 **같은 책갈피 위치부터** 읽는다.
- ★★★ **`g` 없는 독자는 책갈피를 안 쓴다** — 매번 처음부터 읽고 책갈피를 안 꽂는다.
- ★★ **정규식 리터럴 `/a/g` 는 「그 줄을 지날 때마다 새로 오는 독자」다.** 함수 안에 적어 두면 부를 때마다 새 독자라 책갈피가 없다. **모듈 맨 위에 한 번** 만들어 두면 모든 호출이 **한 독자를 돌려쓴다.**
- ★★ **`match` 는 독자에게 「한 번 찾아 줘」(`g` 없음)와 「전부 모아 줘」(`g`)를 다른 서식으로 받는다** — 앞은 상세 보고서(`index`·`groups`), 뒤는 찾은 글자 목록뿐이다.

```text
   const re = /a/g;          입력 "a"  (길이 1)

   call 1   책갈피 0 에서 읽는다   0 번에서 "a" 찾음   -> true    책갈피를 1 에 꽂는다
   call 2   책갈피 1 에서 읽는다   1 부터 끝까지 없음   -> false   책갈피를 뺀다 (0)
   call 3   책갈피 0 에서 읽는다   0 번에서 "a" 찾음   -> true    책갈피를 1 에 꽂는다
   call 4   책갈피 1 에서 읽는다   없음               -> false   책갈피를 뺀다 (0)

   /a/ (g 없음)   책갈피를 안 본다 · 안 꽂는다   -> true true true ...
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 책갈피 | 정규식 객체의 **`lastIndex`** 프로퍼티 | 동작 (1)의 `lastIndex` 열 |
| 책갈피부터 읽는 독자 | `g` 또는 `y` 가 있는 정규식 — `RegExpBuiltinExec` 가 `lastIndex` 를 읽고 쓴다 | 동작 (1)의 `[1]` 대 `[2]` |
| 못 찾으면 책갈피를 뺀다 | 실패하면 `lastIndex` 를 **`0`** 으로 | `call 2 … -> lastIndex 0` |
| 줄을 지날 때마다 새 독자 | 리터럴은 **평가마다** `RegExpCreate` | 동작 (5)의 `make() === make()` |
| 한 독자를 돌려쓴다 | 모듈 수준의 `g` 정규식을 여러 호출이 공유 | 동작 (1)의 `[4]` · 동작 (5)의 `[2]` |
| 상세 보고서 / 글자 목록 | `match` 의 `g` 없음 = `exec` 결과 · `g` = 찾은 글자 배열 | 동작 (2)의 격자 |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.
「**입력 검증용 정규식을 `/…/g` 로 모듈 맨 위에 두고 `list.filter(s => re.test(s))` 를 했더니 멀쩡한 값이 번갈아 빠졌다**」가 그것이다(동작 (1)의 `[4]` — 넷 중 둘만 남았다). 예외가 안 나고, **입력 순서에 따라 빠지는 값이 달라진다.**

> **`lastIndex`** — 정규식 객체의 데이터 프로퍼티. `g`·`y` 가 있으면 `exec`·`test` 가 **여기서부터** 찾고, 끝나면 **찾은 끝 위치**(실패면 `0`)를 여기에 적는다.\
> 예: `const r = /a/g; r.test("a"); r.lastIndex` 가 `1`.

> **플래그(flag)** — 정규식 뒤에 붙는 글자(`/a/gi` 의 `g`·`i`). 찾는 방식을 바꾼다. `flags` 프로퍼티가 전부를 한 문자열로 준다.\
> 예: `/a/yig.flags` 가 `"giy"`(정해진 순서로 다시 적힌다).

## 이 주제가 답하려는 질문

1. **같은 `g` 정규식으로 같은 입력을 여러 번 검사하면 왜 답이 바뀌나** — `lastIndex` 는 누가 읽고 누가 쓰나, `g` 없는 정규식과 무엇이 다른가?
2. **`match`·`matchAll`·`replace` 콜백은 무엇을 돌려주고 무엇을 받나** — `g` 유무 · 명명 그룹 · 실패에 따라 모양이 어떻게 바뀌나?
3. **정규식 객체는 언제 새로 만들어지나** — 리터럴 · `RegExp()` · `new RegExp()` · 복사에서, 그리고 상태(`lastIndex`)는 어디에 남나?

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 출력으로 읽는다.

### (1) ★★★ `lastIndex` 로그 — 이 주제의 본체

**언제 쓰나** — `g` 정규식으로 `test`·`exec` 를 **여러 번** 부를 때. 일부러는 `while ((m = re.exec(s)))` 루프로 **모든 매치를 차례로** 꺼낼 때 쓰고, 실수로는 **검증 함수에서 `g` 정규식을 돌려쓸 때** 만난다.
★★★ 결과(`true`/`false`)만 찍으면 「왜 번갈아 나오나」가 안 보인다. 그래서 **호출 전과 후의 `lastIndex`** 를 한 줄에 찍었다.

```js
// js28b-29a-lastindex.js
// A regexp object with the g flag carries state between calls. Watch lastIndex around each call.
const step = (label, re, input) => {
  const before = re.lastIndex;
  const r = re.test(input);
  console.log("  " + label.padEnd(28) + "lastIndex " + String(before).padEnd(3) + "-> test " + String(r).padEnd(6) + "-> lastIndex " + re.lastIndex);
};

console.log("[1] one regexp /a/g, the same input 'a', four calls");
const g = /a/g;
for (let i = 1; i <= 4; i++) step("call " + i + "  test('a')", g, "a");

console.log("");
console.log("[2] the same without g");
const plain = /a/;
for (let i = 1; i <= 3; i++) step("call " + i + "  test('a')", plain, "a");

console.log("");
console.log("[3] /a/g on the input 'aa', four calls");
const g2 = /a/g;
for (let i = 1; i <= 4; i++) step("call " + i + "  test('aa')", g2, "aa");

console.log("");
console.log("[4] a validator shared across a list -- filter(s => re.test(s))");
const valid = /^[a-z]+$/g;
const words = ["one", "two", "three", "four"];
const kept = words.filter((w) => valid.test(w));
console.log("  input  " + JSON.stringify(words));
console.log("  kept   " + JSON.stringify(kept));
const kept2 = words.filter((w) => /^[a-z]+$/.test(w));
console.log("  kept, literal without g inside the callback  " + JSON.stringify(kept2));

console.log("");
console.log("[5] setting lastIndex by hand, and an input shorter than lastIndex");
const g3 = /a/g;
g3.lastIndex = 5;
step("lastIndex = 5, test('aaa')", g3, "aaa");
g3.lastIndex = 1;
step("lastIndex = 1, test('ab')", g3, "ab");
step("then test('ba')", g3, "ba");
```
```text
===== node20 js28b-29a-lastindex.js (exit=0) =====
[1] one regexp /a/g, the same input 'a', four calls
  call 1  test('a')           lastIndex 0  -> test true  -> lastIndex 1
  call 2  test('a')           lastIndex 1  -> test false -> lastIndex 0
  call 3  test('a')           lastIndex 0  -> test true  -> lastIndex 1
  call 4  test('a')           lastIndex 1  -> test false -> lastIndex 0

[2] the same without g
  call 1  test('a')           lastIndex 0  -> test true  -> lastIndex 0
  call 2  test('a')           lastIndex 0  -> test true  -> lastIndex 0
  call 3  test('a')           lastIndex 0  -> test true  -> lastIndex 0

[3] /a/g on the input 'aa', four calls
  call 1  test('aa')          lastIndex 0  -> test true  -> lastIndex 1
  call 2  test('aa')          lastIndex 1  -> test true  -> lastIndex 2
  call 3  test('aa')          lastIndex 2  -> test false -> lastIndex 0
  call 4  test('aa')          lastIndex 0  -> test true  -> lastIndex 1

[4] a validator shared across a list -- filter(s => re.test(s))
  input  ["one","two","three","four"]
  kept   ["one","three"]
  kept, literal without g inside the callback  ["one","two","three","four"]

[5] setting lastIndex by hand, and an input shorter than lastIndex
  lastIndex = 5, test('aaa')  lastIndex 5  -> test false -> lastIndex 0
  lastIndex = 1, test('ab')   lastIndex 1  -> test false -> lastIndex 0
  then test('ba')             lastIndex 0  -> test true  -> lastIndex 2
```

```text
   RegExpBuiltinExec(R, S) 가 lastIndex 를 다루는 법

   g 나 y 가 있나?
     아니다 -> lastIndex 를 0 으로 보고 찾는다.  lastIndex 프로퍼티는 읽기만 하고 안 쓴다
     그렇다 -> lastIndex 를 읽는다
                lastIndex > S.length  ?  -> lastIndex = 0 을 쓰고 null
                거기서부터 찾는다
                  찾았다   -> lastIndex = 찾은 끝 위치 를 쓴다
                  못 찾았다 -> lastIndex = 0 을 쓴다
```

- ★★★ **`[1]` 이 `true` · `false` · `true` · `false`** 다. `call 1` 뒤 `lastIndex` 가 `1` 이 되고, `call 2` 는 **1 번 위치부터** 찾아 없으니 `false` 를 내고 `lastIndex` 를 **`0` 으로 되돌린다.** 그래서 `call 3` 은 다시 처음이다.
- ★★★ **`[2]` `g` 가 없으면 세 번 다 `true` 이고 `lastIndex` 는 끝까지 `0`** 이다. `g`·`y` 가 없으면 명세가 **`lastIndex` 를 0 으로 보고, 끝나도 안 쓴다.**
- ★★ **`[3]` 입력 `'aa'`** — `true` · `true` · `false` · `true`. 찾을 것이 두 개면 **두 번 참**이고 세 번째에 끝에 닿아 `0` 으로 돌아간다. 「번갈아 나온다」가 아니라 **「매치 개수만큼 참, 그다음 한 번 거짓」** 이 규칙이다.
- ★★★ **`[4]` 검증기를 목록에 돌려쓰면 넷 중 둘만 남는다**(`["one","three"]`).
  `"one"` 이 참이고 `lastIndex` 가 **3** 이 된다. `"two"` 는 **3 번 위치부터** `^[a-z]+$` 를 찾는다 — `^` 는 0 번 자리라 못 찾고 `false`, `lastIndex` 가 `0` 으로. `"three"` 는 참이고 `lastIndex` 가 **5**. `"four"` 는 길이 4 인데 `lastIndex` 5 라 **바로** `false`.
  ★ 같은 콜백에 **`g` 없는 리터럴**을 쓰면 넷 다 남는다.
- ★★ **`[5]` `lastIndex` 는 손으로도 쓸 수 있다** — `5` 로 두고 길이 3 인 입력을 주면 **찾아보지도 않고** `false` 에 `0`. `1` 로 두면 `'ab'` 의 1 번부터 찾아 `a` 가 없어 `false`.
  ★ 그다음 `'ba'` 는 `lastIndex 0` 에서 시작해 **1 번의 `a`** 를 찾았다 — `g` 는 **앞으로 훑어 가며** 찾는다(1 번에서 딱 붙어야 하는 것은 `y`, 동작 (6)).

### (2) ★★★ `match` 의 반환 모양 — `g` 가 서식을 바꾼다

**언제 쓰나** — 문자열에서 **첫 매치의 상세**(위치·캡처·명명 그룹)를 얻거나 **모든 매치의 글자**를 모을 때.

```text
   "a1b22".match(/(\d)/)             "a1b22".match(/(\d)/g)
   -------------------------         -------------------------
   ["1", "1"]                        ["1", "2", "2"]
    ↑     ↑                           ↑    ↑    ↑
    전체  캡처 1                       매치마다 전체 글자만  (캡처는 버린다)
   .index  1                         .index   없음
   .input  "a1b22"                   .input   없음
   .groups undefined (명명 그룹 없음)  .groups  없음
   = RegExpExec 의 결과 그대로          = 새 배열 -- 찾은 글자만 모은 것

   못 찾으면 둘 다 null   (빈 배열이 아니다)
```

```js
// js28b-29b-match-shape.js
// String.prototype.match -- what comes back, with and without the g flag. The script counts the cells.
const J = (x) => (x === undefined ? "undefined" : JSON.stringify(x));
const input = "a1b22";
const columns = [
  ["/(\\d)/", () => input.match(/(\d)/)],
  ["/(\\d)/g", () => input.match(/(\d)/g)],
  ["/(?<n>\\d)/", () => input.match(/(?<n>\d)/)],
  ["/(?<n>\\d)/g", () => input.match(/(?<n>\d)/g)],
  ["/x/", () => input.match(/x/)],
  ["/x/g", () => input.match(/x/g)],
];
const rows = [
  ["returned", (m) => (m === null ? "null" : Array.isArray(m) ? "array" : typeof m)],
  ["length", (m) => (m === null ? "-" : J(m.length))],
  ["[0]", (m) => (m === null ? "-" : J(m[0]))],
  ["[1]", (m) => (m === null ? "-" : J(m[1]))],
  ["index", (m) => (m === null ? "-" : J(m.index))],
  ["input", (m) => (m === null ? "-" : J(m.input))],
  ["groups", (m) => (m === null ? "-" : J(m.groups))],
];

console.log("[1] '" + input + "'.match(re)");
console.log(("  " + "".padEnd(10) + columns.map(([n]) => n.padEnd(14)).join("")).trimEnd());
const results = columns.map(([, f]) => f());
const table = rows.map(([, read]) => results.map(read));
rows.forEach(([name], i) => console.log(("  " + name.padEnd(10) + table[i].map((c) => c.padEnd(14)).join("")).trimEnd()));

console.log("");
console.log("[2] the same regexps through exec, for comparison");
const e1 = /(\d)/.exec(input), e2 = /(\d)/g.exec(input);
console.log("  /(\\d)/.exec    " + J([...e1]) + "  index " + e1.index);
console.log("  /(\\d)/g.exec   " + J([...e2]) + "  index " + e2.index);

console.log("");
console.log("[3] match with a string argument");
console.log("  'a.c'.match('.')    " + J([..."a.c".match(".")]) + "  index " + "a.c".match(".").index);
console.log("  'abc'.match()       " + J([..."abc".match()]));

let differ = 0, total = 0;
for (const row of table) for (const [a, b] of [[0, 1], [2, 3], [4, 5]]) { total += 1; if (row[a] !== row[b]) differ += 1; }
console.log("");
console.log("cells where the g column differs from its pair without g: " + differ + " / " + total);
```
```text
===== node20 js28b-29b-match-shape.js (exit=0) =====
[1] 'a1b22'.match(re)
            /(\d)/        /(\d)/g       /(?<n>\d)/    /(?<n>\d)/g   /x/           /x/g
  returned  array         array         array         array         null          null
  length    2             3             2             3             -             -
  [0]       "1"           "1"           "1"           "1"           -             -
  [1]       "1"           "2"           "1"           "2"           -             -
  index     1             undefined     1             undefined     -             -
  input     "a1b22"       undefined     "a1b22"       undefined     -             -
  groups    undefined     undefined     {"n":"1"}     undefined     -             -

[2] the same regexps through exec, for comparison
  /(\d)/.exec    ["1","1"]  index 1
  /(\d)/g.exec   ["1","1"]  index 1

[3] match with a string argument
  'a.c'.match('.')    ["a"]  index 0
  'abc'.match()       [""]

cells where the g column differs from its pair without g: 9 / 21
```

- ★★★ **마지막 줄이 `9 / 21`** — `g` 없는 열과 `g` 열을 짝지어(세 짝 × 일곱 행) 비교하니 21칸 중 9칸이 갈렸다.
- ★★★ **`g` 없으면 길이 2(`[0]` 전체 + `[1]` 캡처), `g` 면 길이 3(매치 셋의 전체 글자)** 이다. **`[1]` 의 뜻이 바뀐다** — 앞은 **첫 캡처**, 뒤는 **두 번째 매치**.
- ★★★ **`g` 면 `index`·`input`·`groups` 가 전부 `undefined`** 다 — 결과가 **평범한 배열**이라 그 프로퍼티가 없다. 명명 그룹 `(?<n>\d)` 을 써도 `g` 면 `groups` 를 잃는다.
- ★★ **못 찾으면 `g` 유무와 상관없이 `null`** 이다(`/x/`·`/x/g` 열). `m.length` 를 바로 읽으면 `TypeError` 다 — 흔한 방어는 `(s.match(re) ?? [])`.
- ★★ **`[2]` `exec` 는 `g` 가 있어도 상세 보고서**다(`["1","1"]  index 1`). 「전부」는 `exec` 를 **여러 번** 부르거나(동작 (1)) `matchAll`(동작 (3))로 얻는다.
- ★★ **`[3]` 문자열 인자는 정규식으로 바뀐다** — `'a.c'.match('.')` 는 `.` 을 **아무 글자**로 읽어 첫 글자 `"a"` 를 찾았다. 인자 없는 `match()` 는 빈 패턴이라 `[""]`.

### (3) ★★★ `matchAll` — `g` 필수, 이터레이터, 복제본으로 찾는다

**언제 쓰나** — 매치마다 **캡처·`index`·`groups` 까지** 필요할 때. `g` 의 `match` 는 글자만 주고, `exec` 루프는 `lastIndex` 를 손으로 다뤄야 한다.

```text
   input.matchAll(passed)            passed = /\d/g   (lastIndex 2)

   1. passed 에 g 가 있나?  없으면 TypeError
   2. matcher = new RegExp(passed, passed.flags)    <- 복제본 (species 생성자)
      matcher.lastIndex = passed.lastIndex         <- 책갈피 위치만 옮겨 적는다
   3. RegExp String Iterator 를 돌려준다           <- 아직 한 번도 안 찾았다
   4. next() 할 때마다  matcher 로 exec 한 번
                         찾으면 { value: 매치, done: false }
                         못 찾으면 { done: true }  -- 그 뒤로는 계속 done

   passed.lastIndex 는 한 번도 안 바뀐다
```

```js
// js28b-29c-matchall.js
// matchAll -- what it returns, what it needs, and what it does to the regexp it was given.
const J = (x) => (x === undefined ? "undefined" : JSON.stringify(x));
const show = (label, f) => {
  try { console.log("  " + label.padEnd(44) + f()); }
  catch (e) { console.log("  " + label.padEnd(44) + e.constructor.name + " 「" + e.message + "」"); }
};
const input = "a1b22";

console.log("[1] the argument");
show("matchAll(/\\d/g)  first match", () => J([...[...input.matchAll(/\d/g)][0]]));
show("matchAll(/\\d/)", () => J([...input.matchAll(/\d/)].length));
show("matchAll('\\\\d')", () => J([...input.matchAll("\\d")].map((m) => m[0])));
show("matchAll('.')", () => J([..."a.c".matchAll(".")].map((m) => m[0])));

console.log("");
console.log("[2] what comes back");
const it = input.matchAll(/(\d)/g);
show("Object.prototype.toString.call(it)", () => Object.prototype.toString.call(it));
show("Array.isArray(it)", () => Array.isArray(it));
show("typeof it.next / it.return", () => typeof it.next + " / " + typeof it.return);
show("it[Symbol.iterator]() === it", () => it[Symbol.iterator]() === it);
show("each element", () => J([...it].map((m) => ({ all: m[0], one: m[1], index: m.index }))));
show("spread the same iterator again", () => J([...it]));

console.log("");
console.log("[3] the regexp object that was passed in");
const re = /\d/g;
re.lastIndex = 2;
const it2 = input.matchAll(re);
show("re.lastIndex right after matchAll()", () => re.lastIndex);
show("first match from the iterator", () => J(it2.next().value[0]));
show("re.lastIndex after pulling one", () => re.lastIndex);
show("remaining", () => J([...it2].map((m) => m[0])));

console.log("");
console.log("[4] when does the search run, and on which object? (RegExp.prototype.exec wrapped with a counter)");
const calls = [];
const origExec = RegExp.prototype.exec;
const passed = /\d/g;
RegExp.prototype.exec = function (s) { calls.push(this === passed ? "passed object" : "another object"); return origExec.call(this, s); };
const it3 = input.matchAll(passed);
show("exec calls after matchAll()", () => J(calls));
it3.next();
show("exec calls after one next()", () => J(calls));
[...it3];
show("exec calls after spreading the rest", () => J(calls));
RegExp.prototype.exec = origExec;
```
```text
===== node20 js28b-29c-matchall.js (exit=0) =====
[1] the argument
  matchAll(/\d/g)  first match                ["1"]
  matchAll(/\d/)                              TypeError 「String.prototype.matchAll called with a non-global RegExp argument」
  matchAll('\\d')                             ["1","2","2"]
  matchAll('.')                               ["a",".","c"]

[2] what comes back
  Object.prototype.toString.call(it)          [object RegExp String Iterator]
  Array.isArray(it)                           false
  typeof it.next / it.return                  function / undefined
  it[Symbol.iterator]() === it                true
  each element                                [{"all":"1","one":"1","index":1},{"all":"2","one":"2","index":3},{"all":"2","one":"2","index":4}]
  spread the same iterator again              []

[3] the regexp object that was passed in
  re.lastIndex right after matchAll()         2
  first match from the iterator               "2"
  re.lastIndex after pulling one              2
  remaining                                   ["2"]

[4] when does the search run, and on which object? (RegExp.prototype.exec wrapped with a counter)
  exec calls after matchAll()                 []
  exec calls after one next()                 ["another object"]
  exec calls after spreading the rest         ["another object","another object","another object","another object"]
```

- ★★★ **`g` 없는 정규식은 `TypeError 「String.prototype.matchAll called with a non-global RegExp argument」`** 다. 문자열 인자는 **`g` 를 붙인 정규식**으로 바뀐다(`'\\d'` → 셋 다 찾음 · `'.'` → 글자 셋).
- ★★★ **돌려받는 것은 배열이 아니다** — 태그가 **`[object RegExp String Iterator]`**, `Array.isArray` 는 `false`, `next` 는 있고 **`return` 은 없다.** `it[Symbol.iterator]() === it` — 이터레이터가 자기 자신을 이터러블로 준다(19번의 계약).
- ★★★ **한 번 펼치면 끝이다** — 같은 `it` 을 다시 펼치면 `[]`. 21번이 헬퍼 이터레이터로 본 「한 번 소비」와 같다. 다시 돌려면 `matchAll` 을 **다시 부른다.**
- ★★★ **`[3]` 넘긴 정규식의 `lastIndex` 가 시작점이 된다** — `re.lastIndex = 2` 로 넘기자 첫 매치가 **3 번의 `"2"`** 다(1 번의 `"1"` 을 건너뛰었다). 그런데 **`re.lastIndex` 는 끝까지 `2`** 다 — 찾는 것은 **복제본**이다.
- ★★★ **`[4]` `exec` 로그** — `matchAll()` 을 부른 직후 **`[]`**(아직 안 찾았다) → `next()` 한 번에 **한 번** → 나머지를 펼치자 **네 번**(매치 셋 + 끝을 알린 한 번). 그리고 전부 **`"another object"`** — 넘긴 객체가 아니라 **복제본**으로 찾았다.

### (4) ★★ `replace` 콜백이 받는 인자 — 자리로 읽는다

**언제 쓰나** — 찾은 것을 **계산해서** 바꿀 때(`s.replace(/\d+/g, n => n * 2)`). 치환 문자열의 `$` 표기로 안 되는 일.

```text
   "x1a y2".replace(/(\d)(?<L>[a-z])?/g, fn)

   fn( 찾은 전체 , 캡처 1 , 캡처 2 ... , 위치 , 원본 문자열 , groups )
        "1a"       "1"      "a"          1      "x1a y2"      { L: "a" }
        "2"        "2"      undefined    5      "x1a y2"      { L: undefined }
                                                              ↑ 명명 그룹이 하나라도 있을 때만 붙는다

   캡처 개수가 패턴마다 다르므로  "위치"는 끝에서 셋째(명명 그룹 없으면 끝에서 둘째) 로 찾아야 한다
```

```js
// js28b-29d-replace-callback.js
// The arguments a replace callback receives -- by position, for four kinds of pattern.
const J = (x) => JSON.stringify(x, (k, v) => (v === undefined ? "<undefined>" : v));
const spy = (label, run) => {
  const calls = [];
  const out = run((...args) => { calls.push(args); return "_"; });
  console.log("  " + label);
  calls.forEach((args, i) => console.log("    call " + (i + 1) + "  " + args.length + " args  " + J(args)));
  console.log("    result " + J(out));
};

console.log("[1] a string pattern");
spy("'x1y2'.replace('1', fn)", (fn) => "x1y2".replace("1", fn));

console.log("");
console.log("[2] a regexp with no groups, g flag");
spy("'x1y2'.replace(/\\d/g, fn)", (fn) => "x1y2".replace(/\d/g, fn));

console.log("");
console.log("[3] two numbered groups, the second optional");
spy("'x1a y2'.replace(/(\\d)([a-z])?/g, fn)", (fn) => "x1a y2".replace(/(\d)([a-z])?/g, fn));

console.log("");
console.log("[4] the same with a named group");
spy("'x1a y2'.replace(/(\\d)(?<L>[a-z])?/g, fn)", (fn) => "x1a y2".replace(/(\d)(?<L>[a-z])?/g, fn));

console.log("");
console.log("[5] what the callback returns");
const back = (v) => "x1y2".replace(/\d/g, () => v);
for (const [label, v] of [["undefined", undefined], ["null", null], ["42", 42], ["{ toString: () => 'T' }", { toString: () => "T" }], ["'$&'", "$&"]]) {
  console.log("    returns " + label.padEnd(24) + "-> " + J(back(v)));
}
```
```text
===== node20 js28b-29d-replace-callback.js (exit=0) =====
[1] a string pattern
  'x1y2'.replace('1', fn)
    call 1  3 args  ["1",1,"x1y2"]
    result "x_y2"

[2] a regexp with no groups, g flag
  'x1y2'.replace(/\d/g, fn)
    call 1  3 args  ["1",1,"x1y2"]
    call 2  3 args  ["2",3,"x1y2"]
    result "x_y_"

[3] two numbered groups, the second optional
  'x1a y2'.replace(/(\d)([a-z])?/g, fn)
    call 1  5 args  ["1a","1","a",1,"x1a y2"]
    call 2  5 args  ["2","2","<undefined>",5,"x1a y2"]
    result "x_ y_"

[4] the same with a named group
  'x1a y2'.replace(/(\d)(?<L>[a-z])?/g, fn)
    call 1  6 args  ["1a","1","a",1,"x1a y2",{"L":"a"}]
    call 2  6 args  ["2","2","<undefined>",5,"x1a y2",{"L":"<undefined>"}]
    result "x_ y_"

[5] what the callback returns
    returns undefined               -> "xundefinedyundefined"
    returns null                    -> "xnullynull"
    returns 42                      -> "x42y42"
    returns { toString: () => 'T' } -> "xTyT"
    returns '$&'                    -> "x$&y$&"
```

- ★★★ **인자 수는 패턴마다 다르다** — 문자열 패턴과 그룹 없는 정규식은 **셋**(전체 · 위치 · 원본), 그룹 둘이면 **다섯**, 거기에 명명 그룹이 있으면 **여섯**(맨 끝에 `groups`).
- ★★★ **참여하지 않은 그룹은 `undefined`** 로 자리를 지킨다(`call 2` 의 `"<undefined>"`) — 인자 수는 줄지 않는다. `groups` 안의 값도 `undefined` 다.
- ★★ **`g` 가 있으면 매치마다 한 번**, 없으면 첫 매치에 **한 번**이다. 위치 인자는 **원본 기준**이다(치환으로 길이가 바뀌어도 `5`).
- ★★ **`[5]` 반환값은 `ToString`** — `undefined` 는 글자 `"undefined"`, `null` 은 `"null"`, 객체는 `toString` 결과. **`'$&'` 를 돌려주면 글자 그대로**다 — 28번 동작 (1)의 넷째 열과 같은 규칙이다.
- ★ 이름 있는 매개변수로 받으려면 **나머지 매개변수**로 받아 끝에서 읽는다: `(...args) => { const groups = args.at(-1); … }` — 명명 그룹이 있을 때만 맞는 방법이다(이 형태는 이 문서가 따로 안 돌렸다 — 위 로그의 인자 배열이 근거다).

### (5) ★★★ 리터럴은 평가마다 새 객체다 — 상태가 어디에 남나

**언제 쓰나** — 정규식을 **어디에 적을지** 정할 때. 함수 안 · 루프 안 · 모듈 맨 위.

```text
   function make() { return /a/g; }        make() === make()   -> false
     리터럴을 평가할 때마다 RegExpCreate      (ES5 부터. ES3 에서는 리터럴 하나에 객체 하나였다)

   const SHARED = /a/g;                    한 객체를 모든 호출이 쓴다  -> lastIndex 가 호출 사이로 샌다
   const hasShared = (s) => SHARED.test(s);
   const hasLocal  = (s) => /a/g.test(s);  부를 때마다 새 객체        -> lastIndex 가 늘 0 에서 시작

   RegExp(r)       -> r 그 자체 (플래그를 안 주고, r.constructor 가 RegExp 면)
   new RegExp(r)   -> 새 객체, 같은 source · flags, lastIndex 는 0
```

```js
// js28b-29e-literal-identity.js
// A regexp literal -- one object per evaluation? And where lastIndex state can live.
const show = (label, f) => {
  try { console.log("  " + label.padEnd(44) + String(f())); }
  catch (e) { console.log("  " + label.padEnd(44) + e.constructor.name + " 「" + e.message + "」"); }
};

console.log("[1] identity");
const make = () => /a/g;
show("make() === make()", () => make() === make());
const seen = [];
for (let i = 0; i < 2; i++) seen.push(/a/g);
show("the literal in two loop turns: same object?", () => seen[0] === seen[1]);
const r = /a/g;
show("RegExp(r) === r", () => RegExp(r) === r);
show("new RegExp(r) === r", () => new RegExp(r) === r);
show("RegExp(r, 'g') === r", () => RegExp(r, "g") === r);

console.log("");
console.log("[2] a regexp at module level vs a literal inside the function");
const SHARED = /a/g;
const hasShared = (s) => SHARED.test(s);
const hasLocal = (s) => /a/g.test(s);
show("hasShared('a') x3", () => [hasShared("a"), hasShared("a"), hasShared("a")].join(" "));
show("hasLocal('a')  x3", () => [hasLocal("a"), hasLocal("a"), hasLocal("a")].join(" "));

console.log("");
console.log("[3] copying a regexp -- does lastIndex come along?");
const src = /a/g;
src.lastIndex = 3;
show("new RegExp(src).lastIndex", () => new RegExp(src).lastIndex);
show("new RegExp(src).flags", () => new RegExp(src).flags);
show("new RegExp(src, 'i').flags", () => new RegExp(src, "i").flags);

console.log("");
console.log("[4] search -- given a g regexp with lastIndex set");
const b = /b/g;
b.lastIndex = 3;
show("'abcb'.search(b)", () => "abcb".search(b));
show("b.lastIndex afterwards", () => b.lastIndex);
show("b.exec('abcb').index   (for comparison)", () => { b.lastIndex = 3; return b.exec("abcb").index; });
```
```text
===== node20 js28b-29e-literal-identity.js (exit=0) =====
[1] identity
  make() === make()                           false
  the literal in two loop turns: same object? false
  RegExp(r) === r                             true
  new RegExp(r) === r                         false
  RegExp(r, 'g') === r                        false

[2] a regexp at module level vs a literal inside the function
  hasShared('a') x3                           true false true
  hasLocal('a')  x3                           true true true

[3] copying a regexp -- does lastIndex come along?
  new RegExp(src).lastIndex                   0
  new RegExp(src).flags                       g
  new RegExp(src, 'i').flags                  i

[4] search -- given a g regexp with lastIndex set
  'abcb'.search(b)                            1
  b.lastIndex afterwards                      3
  b.exec('abcb').index   (for comparison)     3
```

- ★★★ **`make() === make()` 가 `false`, 루프 두 바퀴도 `false`** — 리터럴은 **지날 때마다 새 객체**다. 28번의 태그 템플릿(자리마다 하나)과 **반대**다.
- ★★★ **`[2]` 모듈 수준 `SHARED` 는 `true false true`, 함수 안 리터럴은 `true true true`** — 상태는 **객체에** 산다. 객체를 공유하면 상태도 공유된다.
- ★★ **`RegExp(r) === r` 은 `true`** — `new` 없이 정규식을 주면 **그대로 돌려준다**(플래그를 주면 새것 — `RegExp(r, 'g') === r` 은 `false`). **`new RegExp(r)` 은 늘 새것**이다.
- ★★ **`[3]` 복사본의 `lastIndex` 는 `0`** — `source` 와 `flags` 만 옮기고 **책갈피는 안 옮긴다.** 플래그를 주면 원래 플래그를 **대체한다**(`'i'` 만 남는다 — 합치지 않는다).
- ★★★ **`[4]` `search` 는 `lastIndex` 와 `g` 를 무시한다** — `lastIndex = 3` 인 `/b/g` 로도 **첫 `b` 의 위치 `1`** 을 준다. 그리고 **`lastIndex` 를 `3` 으로 되돌려 둔다.**
  같은 정규식의 `exec` 는 `3` 부터 찾아 `index 3`. 명세 `@@search` 는 **`lastIndex` 를 저장 → 0 으로 → 찾기 → 원래 값으로 복원**한다.

### (6) ★★ 플래그 — 글자, 프로퍼티, 순서, 거절

**언제 쓰나** — 정규식을 **문자열로 조립**할 때(`new RegExp(src, flags)`) · 받은 정규식이 **어떤 모드인지** 물을 때.

```text
   flags 글자와 프로퍼티              flags 접근자가 다시 적는 순서
   d  hasIndices   (ES2022)          d g i m s u v y
   g  global                         ↑ 명세의 get flags 가 이 순서로 프로퍼티를 하나씩 물어 이어 붙인다
   i  ignoreCase                     그래서 'ymgi' 로 만들어도  flags 는 "gimy"
   m  multiline
   s  dotAll       (ES2018)          거절 -- 모르는 글자 · 같은 글자 두 번 · u 와 v 를 함께
   u  unicode      (ES2015)                  -> SyntaxError
   v  unicodeSets  (ES2024)
   y  sticky       (ES2015)
```

```js
// js28b-29f-flags.js
// The flags -- each letter, its property name, and what the constructor accepts.
const show = (label, f) => {
  try { console.log("  " + label.padEnd(36) + String(f())); }
  catch (e) { console.log("  " + label.padEnd(36) + e.constructor.name + " 「" + e.message + "」"); }
};
const props = ["hasIndices", "global", "ignoreCase", "multiline", "dotAll", "unicode", "unicodeSets", "sticky"];

console.log("[1] one letter at a time -- .flags and the property that turns true");
for (const f of ["g", "i", "m", "s", "u", "y", "d", "v"]) {
  show("new RegExp('a', '" + f + "')", () => {
    const re = new RegExp("a", f);
    return re.flags.padEnd(4) + props.filter((p) => re[p] === true).join(",");
  });
}

console.log("");
console.log("[2] several letters -- the order of .flags");
show("new RegExp('a', 'ymgi').flags", () => new RegExp("a", "ymgi").flags);
show("/a/yigm.flags", () => /a/yigm.flags);
show("new RegExp('a', 'dgimsuy').flags", () => new RegExp("a", "dgimsuy").flags);

console.log("");
console.log("[3] letters the constructor may refuse");
show("new RegExp('a', 'gg')", () => new RegExp("a", "gg").flags);
show("new RegExp('a', 'x')", () => new RegExp("a", "x").flags);
show("new RegExp('a', 'uv')", () => new RegExp("a", "uv").flags);
show("new RegExp('a', 'G')", () => new RegExp("a", "G").flags);

console.log("");
console.log("[4] what four of them change -- i, m, s, y");
show("/B/.test('abc')  /B/i.test('abc')", () => /B/.test("abc") + "  " + /B/i.test("abc"));
show("'a\\nb'.match(/^b/)  /^b/m", () => String("a\nb".match(/^b/)) + "  " + String("a\nb".match(/^b/m)));
show("/a.b/.test('a\\nb')  /a.b/s", () => /a.b/.test("a\nb") + "  " + /a.b/s.test("a\nb"));
const y = /b/y, g = /b/g;
show("/b/y.test('ab')  /b/g.test('ab')", () => y.test("ab") + "  " + g.test("ab"));
y.lastIndex = 1;
show("/b/y lastIndex=1 .test('ab')", () => y.test("ab"));

console.log("");
console.log("[5] a subclass whose flags getter returns 'gi'");
class Loud extends RegExp { get flags() { return "gi"; } }
show("new Loud('a').flags", () => new Loud("a").flags);
show("new Loud('a').global", () => new Loud("a").global);
show("new RegExp(new Loud('a')).flags", () => new RegExp(new Loud("a")).flags);
```
```text
===== node20 js28b-29f-flags.js (exit=0) =====
[1] one letter at a time -- .flags and the property that turns true
  new RegExp('a', 'g')                g   global
  new RegExp('a', 'i')                i   ignoreCase
  new RegExp('a', 'm')                m   multiline
  new RegExp('a', 's')                s   dotAll
  new RegExp('a', 'u')                u   unicode
  new RegExp('a', 'y')                y   sticky
  new RegExp('a', 'd')                d   hasIndices
  new RegExp('a', 'v')                v   unicodeSets

[2] several letters -- the order of .flags
  new RegExp('a', 'ymgi').flags       gimy
  /a/yigm.flags                       gimy
  new RegExp('a', 'dgimsuy').flags    dgimsuy

[3] letters the constructor may refuse
  new RegExp('a', 'gg')               SyntaxError 「Invalid flags supplied to RegExp constructor 'gg'」
  new RegExp('a', 'x')                SyntaxError 「Invalid flags supplied to RegExp constructor 'x'」
  new RegExp('a', 'uv')               SyntaxError 「Invalid flags supplied to RegExp constructor 'uv'」
  new RegExp('a', 'G')                SyntaxError 「Invalid flags supplied to RegExp constructor 'G'」

[4] what four of them change -- i, m, s, y
  /B/.test('abc')  /B/i.test('abc')   false  true
  'a\nb'.match(/^b/)  /^b/m           null  b
  /a.b/.test('a\nb')  /a.b/s          false  true
  /b/y.test('ab')  /b/g.test('ab')    false  true
  /b/y lastIndex=1 .test('ab')        true

[5] a subclass whose flags getter returns 'gi'
  new Loud('a').flags                 gi
  new Loud('a').global                false
  new RegExp(new Loud('a')).flags     
```

- ★★ **`[1]` 한 글자마다 켜지는 프로퍼티가 정확히 하나**다(`g` → `global` … `v` → `unicodeSets`). `d` 는 `hasIndices`, `y` 는 `sticky` — 글자와 이름이 안 닮은 둘을 외워 둔다.
- ★★ **node 18 에는 `v` 가 없다** — 아래 블록의 `SyntaxError 「Invalid flags supplied to RegExp constructor 'v'」`. 나머지 줄은 두 판이 같다. `v` 의 뜻은 30번이 정본이다.
- ★★ **`[2]` `flags` 는 늘 정해진 순서**로 다시 적힌다 — `'ymgi'` 로 만들어도, 리터럴 `/a/yigm` 도 **`"gimy"`**.
- ★★★ **`[3]` 같은 글자 두 번 · 모르는 글자 · `u` 와 `v` 를 함께 · 대문자는 전부 `SyntaxError`** 다. 조용히 무시하는 일은 없다.
- ★★ **`[4]` 네 플래그의 뜻** — `i` 대소문자 무시 · `m` 이면 `^`/`$` 가 **줄마다** · `s` 면 `.` 이 **줄바꿈까지** · `y` 는 **`lastIndex` 자리에 딱 붙어야** 찾는다(`/b/y.test('ab')` 는 0 번에 `b` 가 없어 `false`, `lastIndex = 1` 이면 `true`). `g` 는 앞으로 훑는다(`true`).
- ★ **`[5]` 하위 클래스가 `flags` 접근자를 덮어도** `global` 은 `false` 이고, `new RegExp(그것)` 의 `flags` 는 **빈 글자**다. 각 플래그 프로퍼티와 복사는 **내부 슬롯 `[[OriginalFlags]]`** 를 읽기 때문이다 — 덮어쓴 `flags` 접근자는 그 슬롯을 안 바꾼다.

```text
===== node18 js28b-29f-flags.js (exit=0) =====
[1] one letter at a time -- .flags and the property that turns true
  new RegExp('a', 'g')                g   global
  new RegExp('a', 'i')                i   ignoreCase
  new RegExp('a', 'm')                m   multiline
  new RegExp('a', 's')                s   dotAll
  new RegExp('a', 'u')                u   unicode
  new RegExp('a', 'y')                y   sticky
  new RegExp('a', 'd')                d   hasIndices
  new RegExp('a', 'v')                SyntaxError 「Invalid flags supplied to RegExp constructor 'v'」

[2] several letters -- the order of .flags
  new RegExp('a', 'ymgi').flags       gimy
  /a/yigm.flags                       gimy
  new RegExp('a', 'dgimsuy').flags    dgimsuy

[3] letters the constructor may refuse
  new RegExp('a', 'gg')               SyntaxError 「Invalid flags supplied to RegExp constructor 'gg'」
  new RegExp('a', 'x')                SyntaxError 「Invalid flags supplied to RegExp constructor 'x'」
  new RegExp('a', 'uv')               SyntaxError 「Invalid flags supplied to RegExp constructor 'uv'」
  new RegExp('a', 'G')                SyntaxError 「Invalid flags supplied to RegExp constructor 'G'」

[4] what four of them change -- i, m, s, y
  /B/.test('abc')  /B/i.test('abc')   false  true
  'a\nb'.match(/^b/)  /^b/m           null  b
  /a.b/.test('a\nb')  /a.b/s          false  true
  /b/y.test('ab')  /b/g.test('ab')    false  true
  /b/y lastIndex=1 .test('ab')        true

[5] a subclass whose flags getter returns 'gi'
  new Loud('a').flags                 gi
  new Loud('a').global                false
  new RegExp(new Loud('a')).flags     
```

### (7) ★★ 리터럴과 `new RegExp` — 같은 패턴을 두 번 적는 법, 그리고 오류가 나는 때

**언제 쓰나** — 패턴을 **문자열에서** 만들어야 할 때(사용자 입력 · 설정 파일 · 조립).

```text
   소스에 적은 글자          문자열 리터럴이 읽은 값      정규식이 읽은 패턴
   /\d/                     (문자열을 안 거친다)          \d   숫자 하나
   new RegExp('\\d')        \d                           \d   숫자 하나
   new RegExp('\d')         d   (\d 는 문자열에서 그냥 d)   d    글자 d 하나      <- 조용히 틀린다

   잘못된 패턴이 드러나는 때
   리터럴 /(/               스크립트를 파싱할 때 (그 줄이 실행되지 않아도)  SyntaxError
   new RegExp('(')          그 줄을 실행할 때                               SyntaxError
```

```js
// js28b-29h-literal-vs-constructor.js
// A literal and the constructor -- the same pattern written two ways, and when a bad pattern is reported.
const J = (x) => JSON.stringify(x);
const show = (label, f) => {
  try { console.log("  " + label.padEnd(40) + f()); }
  catch (e) { console.log("  " + label.padEnd(40) + e.constructor.name + " 「" + e.message + "」"); }
};

console.log("[1] backslashes in a literal and in a string");
show("/\\d/.source", () => /\d/.source);
show("new RegExp('\\\\d').source", () => new RegExp("\\d").source);
show("new RegExp('\\d').source", () => new RegExp("\d").source);
show("new RegExp('\\d').test('7')", () => new RegExp("\d").test("7"));
show("new RegExp('\\d').test('d')", () => new RegExp("\d").test("d"));
show("new RegExp(String.raw`\\d`).test('7')", () => new RegExp(String.raw`\d`).test("7"));

console.log("");
console.log("[2] source and toString");
show("new RegExp('a/b').source", () => new RegExp("a/b").source);
show("String(new RegExp('a/b', 'g'))", () => String(new RegExp("a/b", "g")));
show("new RegExp('').source", () => new RegExp("").source);
show("new RegExp('\\n').source", () => J(new RegExp("\n").source));

console.log("");
console.log("[3] a user string used as a pattern");
const user = "1+1";
show("new RegExp(user).test('1+1')", () => new RegExp(user).test("1+1"));
show("new RegExp(user).test('11')", () => new RegExp(user).test("11"));
show("new RegExp('(').test('(')", () => new RegExp("(").test("("));

console.log("");
console.log("[4] a bad pattern in a literal -- when is it reported?");
show("new Function('return 1; /(/')", () => { new Function("return 1; /(/"); return "compiled"; });
show("new Function('if (false) /[/;')", () => { new Function("if (false) /[/;"); return "compiled"; });
```
```text
===== node20 js28b-29h-literal-vs-constructor.js (exit=0) =====
[1] backslashes in a literal and in a string
  /\d/.source                             \d
  new RegExp('\\d').source                \d
  new RegExp('\d').source                 d
  new RegExp('\d').test('7')              false
  new RegExp('\d').test('d')              true
  new RegExp(String.raw`\d`).test('7')    true

[2] source and toString
  new RegExp('a/b').source                a\/b
  String(new RegExp('a/b', 'g'))          /a\/b/g
  new RegExp('').source                   (?:)
  new RegExp('\n').source                 "\\n"

[3] a user string used as a pattern
  new RegExp(user).test('1+1')            false
  new RegExp(user).test('11')             true
  new RegExp('(').test('(')               SyntaxError 「Invalid regular expression: /(/: Unterminated group」

[4] a bad pattern in a literal -- when is it reported?
  new Function('return 1; /(/')           SyntaxError 「Invalid regular expression: /(/: Unterminated group」
  new Function('if (false) /[/;')         SyntaxError 「Invalid regular expression: missing /」
```

- ★★★ **`new RegExp('\d')` 는 `d` 한 글자**다 — 문자열 리터럴이 `\d` 를 먼저 `d` 로 읽는다. 그래서 `'7'` 에 `false`, `'d'` 에 `true`. **예외도 경고도 없다.** 문자열로 적을 때는 백슬래시를 **두 번**(`'\\d'`) 쓰거나 `String.raw` 를 쓴다(28번).
- ★★ **`[2]` `source` 는 다시 리터럴로 쓸 수 있는 꼴**이다 — `/` 는 `\/` 로, 빈 패턴은 **`(?:)`** 로, 줄바꿈은 **`\n` 두 글자**로 적힌다.
- ★★★ **`[3]` 사용자 문자열을 그대로 패턴으로 쓰면 뜻이 바뀐다** — `"1+1"` 이 「1 이 하나 이상, 그다음 1」이 되어 `'1+1'` 에 `false`, `'11'` 에 `true`. `"("` 은 `SyntaxError`. 글자 그대로 찾으려면 **이스케이프**가 필요하다 — `RegExp.escape`(ES2025)는 30번이 정본이다.
- ★★★ **`[4]` 리터럴의 잘못된 패턴은 파싱 때 난다** — `return 1;` 뒤라 **실행될 일이 없는** `/(/` 도, `if (false)` 안의 `/[/` 도 `new Function` 자체가 `SyntaxError` 다. 리터럴의 패턴 검사는 **조기 오류**다.

### (8) ★★ 파이썬 `re` 와의 대비 — 어디서 찾나 · 상태가 있나 · 명명 그룹

**언제 쓰나** — 두 언어 사이에서 정규식 코드를 옮길 때. **같은 이름의 개념이 다른 곳에 있다.**

```text
                        JS                                 Python re
   「앞에서만」            /^a/  (또는 y + lastIndex 0)         re.match   (앞에 붙어야)
   「어디서나」            /a/.test · exec · search           re.search
   「전체가」              /^a$/                              re.fullmatch
   상태                  g/y 정규식 객체의 lastIndex           없다 -- 패턴 객체는 상태가 없다 (위치는 인자로)
   전부 모으기             match(/g/) -> 전체 글자 배열          findall -> 그룹이 있으면 그룹의 튜플
   이터레이터             matchAll -> 한 번 소비               finditer -> 한 번 소비 (같다)
   명명 그룹              (?<n>…)                            (?P<n>…)   -- (?<n>…) 는 오류
```

```sh
# js28b-29g-python.sh
#!/usr/bin/env bash
# 같은 질문을 파이썬 re 에 던진다 -- 어디서부터 찾나 · 같은 패턴 객체를 여러 번 쓰면 · 명명 그룹 문법.
set -u -o pipefail
python3 - <<'PY'
import re
def show(label, f):
    try:
        print("  " + label.ljust(40) + repr(f()))
    except Exception as e:
        print("  " + label.ljust(40) + type(e).__name__ + " 「" + str(e) + "」")

print("[1] match / search / fullmatch on 'xa'")
show("re.match('a', 'xa')", lambda: re.match("a", "xa"))
show("re.search('a', 'xa').span()", lambda: re.search("a", "xa").span())
show("re.fullmatch('x', 'xa')", lambda: re.fullmatch("x", "xa"))

print("")
print("[2] one compiled pattern, the same input, three calls")
p = re.compile("a")
show("p.search('a') x3", lambda: [bool(p.search("a")) for _ in range(3)])
show("hasattr(p, 'lastIndex')", lambda: hasattr(p, "lastIndex"))
show("p.search('aa', 1).span()", lambda: p.search("aa", 1).span())

print("")
print("[3] findall / finditer -- the counterparts of match(/g/) and matchAll")
show("re.findall(r'\\d', 'a1b22')", lambda: re.findall(r"\d", "a1b22"))
show("re.findall(r'(\\d)(\\d)?', 'a1b22')", lambda: re.findall(r"(\d)(\d)?", "a1b22"))
it = re.finditer(r"\d", "a1b22")
show("[m.group() for m in it]", lambda: [m.group() for m in it])
show("the same iterator again", lambda: [m.group() for m in it])

print("")
print("[4] named groups")
show("re.search('(?P<n>\\d)', 'a1').group('n')", lambda: re.search(r"(?P<n>\d)", "a1").group("n"))
show("re.search('(?<n>\\d)', 'a1')", lambda: re.search(r"(?<n>\d)", "a1"))
PY
```
```text
===== ./js28b-29g-python.sh (exit=0) =====
[1] match / search / fullmatch on 'xa'
  re.match('a', 'xa')                     None
  re.search('a', 'xa').span()             (1, 2)
  re.fullmatch('x', 'xa')                 None

[2] one compiled pattern, the same input, three calls
  p.search('a') x3                        [True, True, True]
  hasattr(p, 'lastIndex')                 False
  p.search('aa', 1).span()                (1, 2)

[3] findall / finditer -- the counterparts of match(/g/) and matchAll
  re.findall(r'\d', 'a1b22')              ['1', '2', '2']
  re.findall(r'(\d)(\d)?', 'a1b22')       [('1', ''), ('2', '2')]
  [m.group() for m in it]                 ['1', '2', '2']
  the same iterator again                 []

[4] named groups
  re.search('(?P<n>\d)', 'a1').group('n') '1'
  re.search('(?<n>\d)', 'a1')             error 「unknown extension ?<n at position 1」
```

- ★★★ **파이썬 `re.match` 는 「앞에서만」** 이라 `'xa'` 에 `None`, **어디서나는 `re.search`** 다. JS 의 `test`·`exec` 는 **어디서나**다 — 이름만 보고 옮기면 뜻이 뒤집힌다.
- ★★★ **파이썬 패턴 객체에는 상태가 없다** — 같은 입력에 세 번 `search` 해도 `[True, True, True]`, `lastIndex` 같은 속성이 없다. 시작 위치는 **인자**로 준다(`p.search('aa', 1)` → `(1, 2)`). JS `g` 정규식의 **책갈피를 객체 밖으로 뺀** 설계다.
- ★★ **`findall` 은 그룹이 있으면 그룹을 준다** — `(\d)(\d)?` 에 `[('1', ''), ('2', '2')]`. 참여 안 한 그룹이 **`''`**(JS 는 `undefined`). JS `match(/…/g)` 는 그룹과 상관없이 **전체 글자**만 준다(동작 (2)).
- ★ **`finditer` 도 한 번 소비**다(두 번째는 `[]`) — `matchAll` 과 같다.
- ★★ **명명 그룹 문법이 다르다** — 파이썬은 `(?P<n>…)`, JS 의 `(?<n>…)` 를 파이썬 3.12 에 주면 `error 「unknown extension ?<n at position 1」`.
- ★ 파이썬 `re` 는 파이썬 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **46번**이 정본이다(아직 폴더가 없다). 여기서는 같은 질문을 던진 결과만 싣는다.

## 문법 — 형태와 규칙

★ 이 절은 **형태 표**다 — 모든 동작 주장은 위 동작 절의 캡처 블록에서만 한다(규칙 28 — 돌리지 않은 코드 펜스를 싣지 않는다).

| 형태 | 돌려주는 것 | `lastIndex` | 어디서 봤나 |
|---|---|---|---|
| `re.test(s)` | 불리언 | `g`·`y` 면 **읽고 쓴다** | 동작 (1) |
| `re.exec(s)` | 매치 배열(`index`·`input`·`groups`) 또는 `null` | `g`·`y` 면 **읽고 쓴다** | 동작 (1)·(2) |
| `s.match(re)` — `g` 없음 | `re.exec(s)` 와 같은 것 | `exec` 와 같다 | 동작 (2) |
| `s.match(re)` — `g` | 찾은 **글자**의 배열 또는 `null` | 0 으로 두고 시작, 끝나면 0 | 동작 (2) |
| `s.matchAll(re)` | `RegExp String Iterator` — 매치 배열을 하나씩 · **`g` 필수** | **복제본**이 넘긴 값에서 시작 · 원래 것은 안 바뀐다 | 동작 (3) |
| `s.replace(re, fn)` | 새 문자열 — `fn(전체, …캡처, 위치, 원본[, groups])` | `g` 면 0 부터 전부 | 동작 (4) |
| `s.search(re)` | 첫 매치 위치 또는 `-1` | **무시하고 복원** | 동작 (5) |
| `/…/flags` | 평가마다 **새** 객체 · 잘못된 패턴은 **조기 오류** | 0 | 동작 (5)·(7) |
| `RegExp(p, f)` · `new RegExp(p, f)` | `RegExp(re)` 만 `re` 자신 · 나머지는 새 객체 | 0 | 동작 (5) |

- **플래그** — `d g i m s u v y`. `flags` 는 이 순서로 다시 적힌다. 같은 글자 두 번 · 모르는 글자 · `u`+`v` 는 `SyntaxError`.
- **`g` 대 `y`** — `g` 는 `lastIndex` 부터 **앞으로 훑고**, `y` 는 `lastIndex` 자리에 **딱 붙어야** 한다.

## 어디서 틀리나

### (1) ★★★ 모듈 맨 위의 `g` 정규식으로 검증한다

`re.test` 가 **호출 사이에 `lastIndex` 를 남긴다**(동작 (1)의 `[4]` — 넷 중 둘만 남았다). 검증에는 `g` 가 **필요 없다** — 떼면 끝이다. 꼭 공유해야 하면 매번 `re.lastIndex = 0` 을 먼저 쓴다.

### (2) ★★★ `test` 가 순수 함수라고 믿는다

`g`·`y` 가 있으면 **`test` 도 상태를 바꾼다**(동작 (1)). 이름이 「검사」라서 부작용이 없을 것 같지만, 명세상 `test` 는 **`exec` 를 부르고 결과가 `null` 인지만 본다** — `exec` 의 `lastIndex` 쓰기가 그대로 일어난다.

### (3) ★★★ `match(/…/g)` 에서 캡처나 `index` 를 읽는다

`g` 면 **글자 배열**이다 — `index`·`groups` 가 `undefined`, `[1]` 은 **두 번째 매치**다(동작 (2)). 캡처가 필요하면 `matchAll`.

### (4) ★★ `match` 가 못 찾으면 빈 배열일 것이라 믿는다

**`null`** 이다(동작 (2)). `s.match(re).length` 는 입력에 따라 `TypeError`. `(s.match(re) ?? []).length` 로 막는다.

### (5) ★★★ `matchAll` 의 결과를 두 번 돈다 — 또는 배열처럼 인덱스로 읽는다

**이터레이터**라서 두 번째는 **비어 있고**(동작 (3)의 `[2]`), `it[0]` 은 없다. 여러 번 쓰려면 `[...s.matchAll(re)]` 로 **한 번 배열로** 받는다.

### (6) ★★ `matchAll(/x/)` 가 첫 매치 하나를 줄 것이라 믿는다

**`TypeError`** 다(동작 (3)). `replaceAll` 과 같은 규칙이다(28번) — 「전부」 메서드는 `g` 없는 정규식을 거절한다.

### (7) ★★ `new RegExp('\d+')` 로 숫자를 찾는다

**`d` 가 하나 이상**을 찾는다(동작 (7)). 문자열 리터럴이 백슬래시를 먼저 먹는다. `'\\d+'` 나 `` String.raw`\d+` ``.

### (8) ★★ 사용자 입력을 그대로 `new RegExp(input)` 에 넣는다

`+`·`(`·`.` 같은 글자가 **패턴으로 읽혀** 뜻이 바뀌거나 `SyntaxError` 다(동작 (7)의 `[3]`). 글자 그대로 찾을 거면 `includes`/`indexOf`(28번), 정규식이 꼭 필요하면 **이스케이프**(30번의 `RegExp.escape`).

### (9) ★★ `search` 가 `lastIndex` 부터 찾을 것이라 믿는다

**처음부터** 찾고 `lastIndex` 를 **복원**한다(동작 (5)의 `[4]`). 위치를 이어 가려면 `exec` 나 `y`.

### (10) ★ 파이썬의 `re.match` 를 JS `test` 로 옮긴다

파이썬 `match` 는 **앞에서만**이다(동작 (8)). JS 로 옮기면 `^` 를 붙여야 같다. 반대로 JS `test` 를 파이썬으로 옮기면 `search` 다.

## 구현 세부사항 대 언어 보장

### 명세 보장 — 어느 엔진에서도 같아야 하는 것

- ★★★ **`RegExpBuiltinExec`** 의 `lastIndex` 규칙 — `g`·`y` 가 없으면 0 에서 찾고 **안 쓴다** · 있으면 읽고, 길이를 넘으면 0 을 쓰고 `null` · 찾으면 **끝 위치**를, 못 찾으면 **0** 을 쓴다. `test` 는 `RegExpExec` 의 결과가 `null` 인지만 본다.
- ★★★ `@@match` 가 `g` 면 `lastIndex` 를 0 으로 두고 **글자만 모은 새 배열**(없으면 `null`)을, 아니면 `RegExpExec` 결과를 돌려주는 것.
- ★★★ `matchAll` 이 `g` 없는 정규식에 **`TypeError`** · `@@matchAll` 이 **species 생성자로 복제본**을 만들고 원래 것의 `lastIndex` 를 옮겨 적는 것 · `%RegExpStringIteratorPrototype%` 에 `next` 와 `@@toStringTag`("RegExp String Iterator")만 있는 것(`return` 이 없다).
- ★★ `replace` 콜백의 인자 순서(전체 · 캡처들 · 위치 · 원본 · 명명 캡처가 있으면 `groups`) · 반환값의 `ToString`.
- ★★ `@@search` 가 `lastIndex` 를 저장·0·복원하는 것.
- ★★★ 정규식 리터럴이 **평가마다 새 객체**(ES5 부터) · 패턴 오류가 **조기 오류**인 것 · `RegExp(re)` 가 조건이 맞으면 `re` 를 돌려주는 것 · 새 객체의 `lastIndex` 가 0 인 것.
- ★★ `get flags` 가 `d g i m s u v y` 순서로 각 플래그 프로퍼티를 읽어 잇는 것 · 생성자가 잘못된 플래그 문자열에 `SyntaxError`.
- 예외의 **종류**(`TypeError`·`SyntaxError`).

### 엔진(V8) 구현 · 이 판의 관찰

- 예외 **문구 전부** — `String.prototype.matchAll called with a non-global RegExp argument` · `Invalid flags supplied to RegExp constructor 'gg'` ·
  `Invalid regular expression: /(/: Unterminated group` · `Invalid regular expression: missing /`.
- ★★ **패턴을 어떤 알고리즘으로 찾나** — V8 의 Irregexp(백트래킹 엔진)다. 명세는 결과(어떤 부분 문자열이 맞나)만 정한다. 30번과 [`cs/algorithm/25-string-matching/`](../../../../../algorithm/25-string-matching/2-summary.md)의 몫.
- 두 node 판이 **`v` 한 줄만** 갈린 것 — 관찰이다.

### 파이썬 쪽 — 다른 언어의 보장

- `re.match`/`search`/`fullmatch` 의 뜻 · 패턴 객체에 상태가 없는 것 · `findall` 이 그룹을 주는 것 · `(?P<n>…)` 는 **CPython 3.12 의 문서화된 동작**이다. 예외 문구는 CPython 의 글자다.

### 그래서 이렇게 적으면 틀린다

- ✗ 「`test` 는 부작용이 없다」 → ○ 「**`g`·`y` 면 `lastIndex` 를 쓴다**」
- ✗ 「`/a/g.test('a')` 는 늘 `true` 다」 → ○ 「**같은 객체면 매치 개수만큼 참, 그다음 한 번 거짓**」
- ✗ 「`match` 는 늘 `index` 를 준다」 → ○ 「**`g` 면 글자 배열** — `index`·`groups` 가 없다」
- ✗ 「`matchAll` 은 넘긴 정규식의 `lastIndex` 를 옮긴다」 → ○ 「**복제본**이 거기서 시작하고, 원래 것은 안 바뀐다」
- ✗ 「리터럴은 한 번만 만들어진다」 → ○ 「**평가마다 새 객체**(ES5 부터)」
- ✗ 「`new RegExp('\d')` 는 숫자를 찾는다」 → ○ 「**글자 `d`** 를 찾는다」
- ✗ 「리터럴을 함수 밖으로 빼면 빠르다」 → ○ **안 쟀다**

## 언제 쓰고 언제 안 쓰나

- **`re.test(s)`**(`g` 없이) — 「있나?」 검사의 기본값. `g` 를 **붙이지 않는다.**
- **`s.match(re)`**(`g` 없이) · **`re.exec(s)`** — 첫 매치의 상세.
- **`s.matchAll(re)`** — 모든 매치의 **캡처·위치·`groups`**. 한 번 돌 거면 `for...of`, 여러 번이면 스프레드로 배열에.
- **`s.match(re)`**(`g`) — 모든 매치의 **글자만**.
- **`y`** — 토크나이저처럼 **정해진 자리에서만** 이어 붙여 찾을 때.
- ★ **안 쓰는 자리** — 글자 그대로 찾기(`includes`·`indexOf`·`replaceAll(문자열)` — 28번) · 같은 `g` 정규식을 **여러 호출이 공유**하는 검증 · 사용자 입력을 이스케이프 없이 패턴으로.

## 핵심 문장

1. ★★★ `g`·`y` 정규식은 **`lastIndex` 라는 상태를 객체에 들고** 있어서, 같은 입력을 같은 객체로 `test` 하면 **매치 개수만큼 참, 그다음 한 번 거짓**이 되풀이된다(`true false true false`).
2. ★★★ `match` 는 `g` 가 없으면 **`exec` 의 상세 보고서**, 있으면 **글자 배열**이다 — 격자에서 **9 / 21 칸**이 갈렸고, 못 찾으면 둘 다 `null` 이다.
3. ★★★ `matchAll` 은 `g` 가 없으면 `TypeError` 이고, **복제본으로** 찾는 **한 번 소비 이터레이터**를 돌려준다 — 원래 정규식의 `lastIndex` 는 안 바뀐다.
4. ★★★ 정규식 **리터럴은 평가마다 새 객체**다 — 함수 안의 리터럴은 상태가 안 새고, 모듈 수준의 `g` 정규식은 호출 사이로 샌다.
5. ★★ `search` 는 `lastIndex` 를 무시하고 복원한다 · `new RegExp('\d')` 는 글자 `d` 다 · 파이썬 `re.match` 는 「앞에서만」이고 패턴 객체에 상태가 없다.

## 관련 자료

- [ECMA-262 — RegExp Objects](https://tc39.es/ecma262/multipage/text-processing.html#sec-regexp-regular-expression-objects)(`RegExpBuiltinExec` · `@@match` · `@@matchAll` · `@@search` · `get flags`)
- [TC39 finished proposals](https://github.com/tc39/proposals/blob/main/finished-proposals.md) — 판 경계
- [`cs/algorithm/25-string-matching/`](../../../../../algorithm/25-string-matching/2-summary.md) — ★ **경계**: 그쪽은 **본문에서 패턴을 찾는 알고리즘(나이브·KMP)**, 여기는 **JS 정규식 API 의 반환값과 상태**.
- [28 — `String` 메서드와 템플릿 리터럴](../28-string-methods-and-template-literals/2-summary.md) — ★ **경계**: 그쪽이 **치환 문자열의 `$` 표기 · `replaceAll` · `split`**, 여기는 **정규식 객체와 콜백**.
- [30 — 정규식 심화](../30-regexp-advanced/2-summary.md) — ★ **경계**: 그쪽이 **캡처·명명 그룹 문법 · 룩어라운드 · `u`/`v` · `d` · `RegExp.escape` · 백트래킹**, 여기는 **플래그의 글자와 프로퍼티까지**.
- [19 — 이터러블 프로토콜과 `for...of`](../19-iterable-protocol-and-for-of/2-summary.md) · [21 — 이터레이터 헬퍼](../21-iterator-helpers/2-summary.md) — `matchAll` 의 이터레이터가 따르는 계약.
- 파이썬 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **46번**(`re`) — 동작 (8)의 대비.

## 용어 풀이

- **`lastIndex`** — 정규식 객체의 데이터 프로퍼티. `g`·`y` 정규식이 다음 검색을 시작할 위치.
- **`RegExpBuiltinExec`** — `exec`·`test` 가 실제로 찾는 명세 연산. `lastIndex` 를 읽고 쓰는 규칙이 여기 있다.
- **`g`(global)** — 「전부」. `lastIndex` 부터 앞으로 훑어 찾고 위치를 기억한다.
- **`y`(sticky)** — 「딱 붙어서」. `lastIndex` 자리에서 시작하는 매치만 찾는다.
- **매치 배열** — `exec` 가 돌려주는 배열. `[0]` 전체, `[1]…` 캡처, `index` · `input` · `groups` 프로퍼티.
- **명명 그룹** — `(?<이름>…)`. 매치 배열의 `groups` 객체에 이름으로 들어간다(문법은 30번).
- **`RegExp String Iterator`** — `matchAll` 이 돌려주는 이터레이터의 태그. `next` 만 있다.
- **species 생성자** — 파생 객체를 만들 때 쓸 생성자를 `constructor[Symbol.species]` 로 고르는 규칙(22번).
- **조기 오류(early error)** — 코드를 **실행하기 전**, 파싱 단계에서 나는 오류. 잘못된 정규식 리터럴이 그렇다.
- **`[[OriginalFlags]]`** — 정규식 객체가 만들어질 때의 플래그 문자열을 담은 내부 슬롯. `global` 같은 프로퍼티가 이것을 읽는다.
- **`re.match` / `re.search`**(파이썬) — 앞에서만 / 어디서나 찾는 함수.

## 더 들어가면

- **`@@match`·`@@replace` 가 「`g` 인가」를 `flags` 로 묻나 `global` 로 묻나** — 하위 클래스가 `flags` 접근자를 덮으면(동작 (6)의 `[5]`) 둘이 어긋난다. 이 문서는 그 자리의 명세 문장을 **확인하지 않았고** 실험도 **싣지 않았다.**
- **`lastIndex` 가 쓰기 불가일 때** — `Object.freeze(/a/g).test('a')` 는 `lastIndex` 를 못 쓴다. 이 문서는 **안 돌렸다.**
- **`d` 플래그의 `indices`** — 30번의 몫이다.
