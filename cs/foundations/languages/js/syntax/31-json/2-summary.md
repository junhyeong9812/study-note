# js/syntax/31 — `JSON`: 「같은 값도 놓인 자리에 따라 다른 글자가 된다」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> ★★★ **이 주제의 본체는 ② 전수 격자다.**
> `JSON.stringify` 가 값을 무엇으로 바꾸는지는 **값만 보고는 답이 안 나온다** — 같은 `undefined` 가 **객체의 속성이면 키째 사라지고, 배열의 원소면 `null` 이 되고, 맨 위면 문자열조차 아닌 `undefined`** 가 된다.
> 그래서 값 **14종** × 자리 **셋**(속성 · 배열 원소 · 최상위)을 스크립트가 전부 찍고, **세 자리가 갈린 행을 스크립트가 센다**(동작 (1)).
> ★★ 보조로 **① 추상 연산에 로그 심기**(`toJSON`·`replacer`·`reviver` 가 **어떤 순서로 누구에게** 불리나 — 동작 (3)·(4))와 **④ 예외의 이름·문구**(순환 참조 · `BigInt` · 파싱 실패 — 동작 (2)·(4))를 쓴다.
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262 — The JSON Object](https://tc39.es/ecma262/multipage/structured-data.html#sec-json-object) —
>   `JSON.parse` · `InternalizeJSONProperty` · `JSON.stringify` · `SerializeJSONProperty` · `SerializeJSONObject` · `SerializeJSONArray` · `JSON.rawJSON`
> - [TC39 finished proposals](https://github.com/tc39/proposals/blob/main/finished-proposals.md) — 판 경계(Well-formed `JSON.stringify` 2019 · JSON superset 2019 · **JSON.parse source text access 2026**)
> - 명세 문장은 이 배치가 받아 둔 **ES2026 판 HTML 에서 읽었다**(알고리즘 단계를 옮기지 않고 연산 이름과 짧은 인용만 싣는다).
> - `structuredClone` 은 ECMA-262 가 아니라 **HTML 표준의 호스트 API** 다. 이 문서는 그 명세를 읽지 않았고 **node 20 에서 비교 열 하나**로만 돌렸다.
>
> ★★★ **명세 조항 번호는 인용하지 않는다.** 규칙 진술은 **추상 연산 이름**으로, 값·호출 로그·예외 타입과 메시지는 **전부 실행으로** 접지했다.
>
> **실행 검증** — 이 문서의 모든 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮겨 적은 출력이 하나도 없다).
> 배너의 `node20` 은 `~/.nvm/versions/node/v20.19.6/bin/node`, `node18` 은 기본 PATH 의 `node`(v18.19.1)다.
> ★★ **예외는 `try`/`catch` 로 받아 `e.constructor.name` 과 `e.message` 만** 찍었다 — 스택트레이스에는 절대 경로가 박혀 재현이 안 된다.
> ★★ **순환 참조 메시지는 여러 줄**이라, 탐침이 **줄마다 `| ` 를 앞에 붙여** 한 줄도 자르지 않고 찍는다(동작 (2)).
> ★★★ **`JSON.rawJSON` 과 `reviver` 의 셋째 인자(ES2026)는 두 node 판에 없다**(아래 판별 블록). 그 탐침은 **Google Chrome 151 을 헤드리스로** 돌렸다 — 배너가 `google-chrome --headless` 로 시작하는 블록이다.
> ★★ **이 주제에서 두 node 판이 갈린 탐침은 하나다** — `JSON.parse` 의 **실패 문구**(동작 (4)의 `[4]`). 값·순서·예외 종류는 전부 같았다.
>
> **버전** — 판별 블록이 세 판(node 18 · node 20 · Chrome 151)에 같은 스크립트를 던진다.
>
> | 무엇 | 판 | 이 머신에서 |
> |---|---|---|
> | `JSON.parse` · `JSON.stringify` · `toJSON` · `replacer` · `reviver` · `space` | ES5 | 세 판 다 있다 |
> | 짝 없는 서로게이트를 `\ud800` 으로 이스케이프(Well-formed `JSON.stringify`) | **ES2019** | 세 판 다 있다 |
> | JSON superset(문자열 안의 U+2028·U+2029 를 JS 도 받는다) | ES2019 | 이 문서는 돌리지 않았다 |
> | `structuredClone` | — **호스트 API**(HTML) | 세 판 다 있다 |
> | `JSON.rawJSON` · `JSON.isRawJSON` · `reviver` 의 `context.source`(JSON.parse source text access) | **ES2026** | ★ **두 node 판에 없다** — Chrome 151 로만 돌렸다 |
>
> **★★★ 이 주제가 쓰는 창 — 그리고 부적용인 창**
>
> | 창 | 이 주제에서 무엇을 보나 |
> |---|---|
> | ★★★ **② 전수 격자**(본체) | 값 **14종** × 자리 **3** — 세 자리가 **갈린 행을 스크립트가 센다**(동작 (1)) · 깊은 복사 대용 두 가지 × 값 **13종** — 두 열이 **갈린 행**(동작 (5)) |
> | ★★ **① 추상 연산에 로그 심기** | `toJSON` 과 `replacer` 가 **어느 쪽이 먼저, 어떤 `this` 로** 불리나(동작 (3)) · `reviver` 가 **어느 키부터** 불리나(동작 (4)) |
> | ★★ **④ 예외의 `constructor.name` + `message`** | 순환 참조의 **여러 줄 메시지** · `BigInt` · `JSON.parse` 의 실패 문구(★ 두 node 판이 **갈린** 유일한 자리) · `structuredClone` 의 `DOMException` |
> | ★ **③ 브랜드 태그** | **부적용** — 이 주제는 `Object.prototype.toString` 으로 가를 것이 없다. 결과가 **글자**라 글자 자체가 답이다 |
> | ★ **⑤ 두 판 대조기** | 이 주제의 node 탐침 가운데 **`JSON.parse` 실패 문구 하나만** `DIFFERS` — 그 블록만 node18 판을 따로 실었다 |
> | ★ **부적용 — 진단의 `(행,열)`**(18-C) | `SyntaxError` 가 **코드의 문법 오류가 아니라 입력 글자의 오류**다. 위치는 메시지 안의 `position N` 으로만 나오고 그것도 node18/20 에서 표기가 다르다 |
> | ★ **안 쟀다 — 성능** | 「JSON 왕복이 `structuredClone` 보다 빠르다」를 **한 줄도 쓰지 않는다.** 시간도 바이트도 안 쟀다 |
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ★★ **`JSON.parse` 실패 문구** — node18(V8 10.2)과 node20(V8 11.3)이 **실제로 다르다**(동작 (4)의 `[4]`). 다른 엔진은 또 다르게 적는다 | ★★★ 격자의 **칸 글자**와 「갈린 행 N / M」 · 호출 로그의 **순서와 개수** · 예외의 **종류**(`TypeError`·`SyntaxError`) |
> | 순환 참조 메시지의 **모양**(`-->`·`\|`·`---` 로 경로를 그리는 것) — V8 의 것이다. 명세는 「`TypeError` 를 던진다」까지만 정한다 | 순환 참조가 **`TypeError`** 인 것 · `BigInt` 가 **`TypeError`** 인 것(명세) |
> | 대조기 블록의 **다른 주제 줄**(같은 배치가 한 대조기를 공유한다) | ★★ **이 주제의 탐침에는 재실행에서 흔들린 칸이 없다**(재대조 동일) |
>
> **선행** — [27 — `Object` 정적 메서드](../27-object-static-methods/2-summary.md)(직접 선행 — ★★★ **복사 도구 격자 `3 / 18` 과 `"__proto__"` 를 `fromEntries`·`assign` 에 넣는 실험은 거기서 쟀다**) ·
> [23 — `Map`·`Set` 과 약한 컬렉션](../23-map-set-and-weak-collections/2-summary.md)(★★ **`JSON.stringify(map)` 이 `{}`** 인 것과 `[...map]` 으로 우회하는 것은 거기가 정본) ·
> [22 — `Symbol` 과 잘 알려진 심볼](../22-symbol-and-well-known-symbols/2-summary.md)(★ **`JSON.stringify(x)` 는 `Symbol.toPrimitive` 를 안 부른다** — 그 표의 `(no call)` 줄) ·
> [13 — 객체 리터럴과 프로퍼티](../13-object-literals-and-properties/2-summary.md)(리터럴 `__proto__:` 의 다섯 형태 · 정수 키 순서) ·
> [03 — 숫자와 `BigInt`](../03-numbers-and-bigint/2-summary.md)(`NaN`·`-0`·안전 정수 한계) · [04 — 문자열과 UTF-16](../04-strings-and-utf16/2-summary.md)(짝 없는 서로게이트).
> **같은 배치** — [28 — `String` 메서드와 템플릿 리터럴](../28-string-methods-and-template-literals/2-summary.md) · [29 — 정규식 기본](../29-regexp-basics/2-summary.md) · [30 — 정규식 심화](../30-regexp-advanced/2-summary.md).
>
> ★★ **경계 — 깊은 복사는** 목록의 **48번 주제**가 정본이다. 여기서는 `structuredClone` 을 **격자의 비교 열 하나**로만 둔다.
> ★★ **경계 — `Map` 을 JSON 으로 옮기는 법은 23번이 정본이다.** 여기서는 격자의 **한 행**으로만 둔다.

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

두 node 판 대조기의 집계 줄(이 배치의 모든 node 탐침) — 이 주제의 탐침(`js28b-31?-*.js`) 가운데 `DIFFERS` 는 `js28b-31d-parse-reviver.js` 하나다. 전문은 [3-answer.md](3-answer.md) 의 「실행 검증」에 있다.

`identical 19  ·  differs 6  ·  total 25`

## 한눈에 — 쉽게 말하면

**`JSON.stringify` 는 「택배 포장 기사」다. 상자에 들어갈 수 있는 것은 글자·숫자·참거짓·빈칸(`null`)·상자(객체)·줄 선 상자(배열)뿐이다.**
포장할 수 없는 물건(함수·`undefined`·심볼)을 만나면 기사는 **그 물건이 어디에 있었느냐**에 따라 다르게 한다.

- ★★★ **이름표가 붙은 칸**(객체의 속성)에 있었으면 — **이름표째 뺀다.** 받는 쪽은 그런 칸이 있었는지도 모른다.
- ★★★ **줄 선 칸**(배열의 원소)에 있었으면 — **빈칸(`null`)을 채운다.** 칸을 빼면 뒤 칸의 번호가 당겨지기 때문이다.
- ★★★ **상자 자체**(최상위)가 그것이면 — **송장을 안 쓴다**(`undefined` — 문자열이 아니다).
- ★★ **숫자는 셀 수 있는 것만 싣는다** — `NaN`·`Infinity` 는 `null`, `-0` 은 `0`. **`BigInt` 는 아예 거절한다**(`TypeError`).
- ★★ **상자 안에서 자기 자신을 만나면**(순환 참조) 포장을 멈추고 **어디서 돌았는지 경로를 적어 돌려준다**(V8 의 메시지).

```text
   같은 undefined 를 세 자리에 놓는다

   { k: undefined }        [ undefined ]          undefined
        │                        │                     │
   SerializeJSONObject     SerializeJSONArray     (감싸개 {"": v})
   속성마다 SerializeJSONProperty  → undefined 가 돌아온다
        │                        │                     │
   undefined 면 건너뛴다     undefined 면 "null"     그대로 돌려준다
        ▼                        ▼                     ▼
      "{}"                   "[null]"             undefined (문자열이 아니다)
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 포장 못 하는 물건 | `SerializeJSONProperty` 가 **`undefined`** 를 돌려주는 값 — `undefined`·함수·심볼 | 동작 (1)의 `[1]` 셋째\~다섯째 행 |
| 이름표째 뺀다 | `SerializeJSONObject` — `strP` 가 `undefined` 면 **멤버를 안 만든다** | `(key gone)` |
| 빈칸을 채운다 | `SerializeJSONArray` — `undefined` 면 **`"null"` 을 넣는다** | 배열 원소 열의 `null` |
| 송장을 안 쓴다 | 최상위에서 `undefined` 가 그대로 반환된다 | `(undefined)` |
| 포장 전에 물건이 스스로 모양을 바꾼다 | **`toJSON`** — `replacer` 보다 **먼저** 불린다 | 동작 (3)의 로그 |
| 기사가 한 번 더 손본다 | **`replacer`** — `this` 는 **그 값을 들고 있던 객체** | 동작 (3)의 `this=` |
| 풀 때는 안쪽 상자부터 | **`reviver`** — 잎부터 부르고 뿌리 `""` 가 마지막 | 동작 (4)의 `[1]` |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.
「**API 응답에 `{ nickname: undefined }` 를 실었더니 받는 쪽에서 `nickname` 키가 아예 없었다**」와
「**`JSON.parse(JSON.stringify(state))` 로 상태를 복사했더니 `Date` 가 문자열이 되어 `.getTime()` 이 `TypeError` 였다**」가 그것이다(동작 (1)·(5)).

> **직렬화(serialization)** — 메모리 안의 값을 글자(또는 바이트)의 열로 바꾸는 것. 되돌리는 것이 역직렬화(파싱).\
> 예: `JSON.stringify({ a: 1 })` 가 `'{"a":1}'`.

> **`toJSON`** — 값이 스스로 「나는 JSON 으로 이렇게 보여라」를 정하는 메서드. `Date` 가 기본으로 갖고 있다.\
> 예: `new Date(0).toJSON()` 이 `"1970-01-01T00:00:00.000Z"`.

## 이 주제가 답하려는 질문

1. **`JSON.stringify` 는 값을 무엇으로 바꾸나** — 그리고 **같은 값이 자리(속성 · 배열 원소 · 최상위)에 따라 왜 다르게 되나**?
2. **`toJSON`·`replacer`·`reviver` 는 어떤 순서로 누구에게 불리나** — 무엇을 지우고 무엇을 바꿀 수 있나?
3. **`JSON.parse(JSON.stringify(x))` 를 깊은 복사로 쓰면 무엇을 잃나** — `structuredClone` 과는 어디서 갈리나?

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 출력으로 읽는다.

### (1) ★★★ 자리별 타입 매핑 격자 — 이 주제의 본체

**언제 쓰나** — API 응답·로그·저장 파일에 객체를 JSON 으로 내보낼 때. 「이 필드가 빠졌나, `null` 이 됐나」를 가를 때.
★★★ 값 하나를 **세 자리**에 놓고 각각 `JSON.stringify` 한다. 칸에는 **그 값이 된 글자만** 적는다(속성 자리는 `{"k":…}` 의 `…`, 배열 자리는 `[…]` 의 `…`).
키가 사라졌으면 `(key gone)`, 결과가 문자열조차 아니면 `(undefined)`, 던졌으면 예외 이름이다.

```js
// js28b-31a-type-grid.js
// JSON.stringify -- the same value in three places: as an object property, as an array element, at the top level.
// Each cell prints what that value became. The script counts the rows at the end.
const cell = (f) => {
  try {
    const r = f();
    return r === undefined ? "(undefined)" : r;
  } catch (e) { return e.constructor.name; }
};
const asProp = (v) => cell(() => {
  const s = JSON.stringify({ k: v });
  return s === "{}" ? "(key gone)" : s.slice(5, -1);
});
const asElem = (v) => cell(() => JSON.stringify([v]).slice(1, -1));
const asTop = (v) => cell(() => JSON.stringify(v));

const bare = Object.create(null); bare.a = 1;
const values = [
  ["null", null],
  ["'s'", "s"],
  ["undefined", undefined],
  ["() => 1", () => 1],
  ["Symbol('s')", Symbol("s")],
  ["NaN", NaN],
  ["Infinity", Infinity],
  ["-0", -0],
  ["1n", 1n],
  ["new Date(0)", new Date(0)],
  ["new Map([[1, 2]])", new Map([[1, 2]])],
  ["new Set([1])", new Set([1])],
  ["Object.create(null) + a:1", bare],
  ["new Boolean(false)", new Boolean(false)],
];

console.log("[1] value" + " ".repeat(22) + "as property".padEnd(28) + "as array element".padEnd(28) + "top level");
let differ = 0;
for (const [label, v] of values) {
  const row = [asProp(v), asElem(v), asTop(v)];
  if (new Set(row).size > 1) differ += 1;
  console.log(("  " + label.padEnd(28) + row.map((c) => c.padEnd(28)).join("")).trimEnd());
}

console.log("");
console.log("[2] a hole in a sparse array, next to an explicit undefined");
console.log("  JSON.stringify([1, , 3])          " + JSON.stringify([1, , 3]));
console.log("  JSON.stringify([1, undefined, 3]) " + JSON.stringify([1, undefined, 3]));
console.log("  JSON.stringify(new Array(2))      " + JSON.stringify(new Array(2)));

console.log("");
console.log("[3] keys that are not plain strings");
const sym = Symbol("key");
console.log("  { [sym]: 1, a: 2 }        " + JSON.stringify({ [sym]: 1, a: 2 }));
console.log("  { 2: 'x', 1: 'y', b: 0 }  " + JSON.stringify({ 2: "x", 1: "y", b: 0 }));
const hidden = Object.defineProperty({ a: 1 }, "h", { value: 2, enumerable: false });
console.log("  non-enumerable h          " + JSON.stringify(hidden));
class P { constructor() { this.own = 1; } }
P.prototype.inherited = 2;
console.log("  class instance            " + JSON.stringify(new P()));

console.log("");
console.log("rows whose three positions do not all agree: " + differ + " / " + values.length);
```
```text
===== node20 js28b-31a-type-grid.js (exit=0) =====
[1] value                      as property                 as array element            top level
  null                        null                        null                        null
  's'                         "s"                         "s"                         "s"
  undefined                   (key gone)                  null                        (undefined)
  () => 1                     (key gone)                  null                        (undefined)
  Symbol('s')                 (key gone)                  null                        (undefined)
  NaN                         null                        null                        null
  Infinity                    null                        null                        null
  -0                          0                           0                           0
  1n                          TypeError                   TypeError                   TypeError
  new Date(0)                 "1970-01-01T00:00:00.000Z"  "1970-01-01T00:00:00.000Z"  "1970-01-01T00:00:00.000Z"
  new Map([[1, 2]])           {}                          {}                          {}
  new Set([1])                {}                          {}                          {}
  Object.create(null) + a:1   {"a":1}                     {"a":1}                     {"a":1}
  new Boolean(false)          false                       false                       false

[2] a hole in a sparse array, next to an explicit undefined
  JSON.stringify([1, , 3])          [1,null,3]
  JSON.stringify([1, undefined, 3]) [1,null,3]
  JSON.stringify(new Array(2))      [null,null]

[3] keys that are not plain strings
  { [sym]: 1, a: 2 }        {"a":2}
  { 2: 'x', 1: 'y', b: 0 }  {"1":"y","2":"x","b":0}
  non-enumerable h          {"a":1}
  class instance            {"own":1}

rows whose three positions do not all agree: 3 / 14
```

```text
   값이 무엇이 되나 — SerializeJSONProperty 의 갈래

   값 ─┬─ 객체이거나 BigInt 면 toJSON 을 찾아 부른다      (Date 는 여기서 문자열이 된다)
       ├─ replacer 가 있으면 부른다
       ├─ Number·String·Boolean 래퍼면 원시값으로 푼다       (new Boolean(false) -> false)
       │
       ├─ null / true / false   -> "null" / "true" / "false"
       ├─ 문자열                 -> 따옴표로 감싼다
       ├─ 숫자   유한하면 ToString   (-0 -> "0")
       │         아니면 "null"       (NaN · Infinity)
       ├─ BigInt                 -> TypeError
       ├─ 호출 불가능한 객체      -> 배열이면 SerializeJSONArray, 아니면 SerializeJSONObject
       └─ 그 밖(undefined · 함수 · 심볼) -> undefined       ← 이것을 받은 쪽이 자리마다 다르게 처리한다
```

- ★★★ **갈린 행은 `3 / 14`** 다 — **`undefined` · 함수 · 심볼** 셋. 셋 다 속성 자리에서 **`(key gone)`**, 배열 자리에서 **`null`**, 최상위에서 **`(undefined)`** 로 **세 자리가 전부 다르다.**
  나머지 11행은 **세 자리가 한 글자도 같다** — 값이 무엇이 되는지는 자리와 상관없고, **「못 싣는 값」을 받았을 때의 처리만** 자리가 정한다(위 그림의 마지막 줄).
- ★★★ **최상위의 `(undefined)` 는 `"undefined"` 라는 글자가 아니다.** `JSON.stringify(undefined)` 의 반환값 자체가 **`undefined`** 다 — 그대로 `JSON.parse` 에 넘기면 `"undefined"` 라는 글자를 파싱하다 `SyntaxError` 다(동작 (4)의 `[4]`).
- ★★ **`NaN`·`Infinity` 는 세 자리 모두 `null`** 이다 — 「못 싣는 값」이 아니라 **「숫자이지만 유한하지 않다」** 는 다른 갈래라서, 속성에서도 **키가 남는다.**
- ★★ **`-0` 은 `0`** 이다. 부호가 사라진다(`Number::toString` 이 `-0` 을 `"0"` 으로 쓴다 — 03번).
- ★★ **`1n` 은 세 자리 모두 `TypeError`** 다. 문구는 동작 (2).
- ★★ **`new Date(0)` 은 문자열**이다 — `Date.prototype.toJSON` 이 먼저 불려 ISO 문자열이 된다. 되돌릴 때 **`Date` 로 안 돌아온다**(동작 (4)의 `[2]` · (5)).
- ★★ **`Map`·`Set` 은 `{}`** 다 — 항목은 own 프로퍼티가 아니라 내부 슬롯에 있어서 `EnumerableOwnProperties` 가 **아무것도 못 본다.** `Map` 쪽 정본은 23번이다.
- ★ **`Object.create(null)` 은 평범하게 `{"a":1}`** 이다 — `stringify` 는 `toString` 같은 프로토타입 메서드를 **안 쓴다**(27번의 `groupBy` 결과를 찍을 때 `JSON.stringify` 를 권한 이유).
- ★ **`new Boolean(false)` 는 `false`** — 래퍼는 풀린다. 객체인데도 **참 같은 값이 아니다.**
- ★★★ **`[2]` 희소 배열의 구멍도 `null`** 이다 — `[1, , 3]` 과 `[1, undefined, 3]` 이 **같은 글자**(`[1,null,3]`)가 된다. 구멍인지 `undefined` 였는지는 **JSON 에 남지 않는다.**
- ★★ **`[3]` 키 쪽** — 심볼 키는 **빠지고**, 정수 키는 **앞으로 간다**(13번의 순서), 비열거 키는 **빠지고**, 클래스 인스턴스는 **own 키만**(`inherited` 없음) 나온다.

### (2) ★★★ 순환 참조와 `BigInt` — 무엇을 거절하고, 무엇을 말해 주나

**언제 쓰나** — 부모 포인터가 있는 트리·그래프를 로그로 찍으려다 터질 때. ID 가 `BigInt` 인 레코드를 내보낼 때.

```js
// js28b-31b-throws.js
// What JSON.stringify refuses -- the exception type and the whole message.
// A message can span several lines; each line is printed with a "| " prefix so nothing is trimmed.
const show = (label, f) => {
  try { console.log("  " + label.padEnd(32) + "returned " + f()); }
  catch (e) {
    console.log("  " + label.padEnd(32) + e.constructor.name);
    for (const line of e.message.split("\n")) console.log("    | " + line);
  }
};

console.log("[1] cycles");
const self = {}; self.me = self;
show("self.me = self", () => JSON.stringify(self));
const a = { name: "a", b: { c: {} } }; a.b.c.back = a;
show("a.b.c.back = a", () => JSON.stringify(a));
const arr = [1, [2]]; arr[1].push(arr);
show("arr[1][1] = arr", () => JSON.stringify(arr));
class Node2 { constructor() { this.next = null; } }
const n1 = new Node2(); const n2 = new Node2(); n1.next = n2; n2.next = n1;
show("class instances, n1 <-> n2", () => JSON.stringify(n1));

console.log("");
console.log("[2] one object reached through two keys");
const shared = { v: 1 };
show("{ x: shared, y: shared }", () => JSON.stringify({ x: shared, y: shared }));

console.log("");
console.log("[3] BigInt");
show("1n", () => JSON.stringify(1n));
show("{ id: 10n }", () => JSON.stringify({ id: 10n }));
show("replacer: bigint -> toString()", () => JSON.stringify({ id: 10n }, (k, v) => (typeof v === "bigint" ? v.toString() : v)));
BigInt.prototype.toJSON = function () { return this.toString() + "n"; };
show("BigInt.prototype.toJSON set", () => JSON.stringify({ id: 10n }));
delete BigInt.prototype.toJSON;

console.log("");
console.log("[4] a.b.c.back = a again, with a WeakSet replacer");
const seen = new WeakSet();
show("WeakSet replacer", () => JSON.stringify(a, (k, v) => {
  if (typeof v === "object" && v !== null) { if (seen.has(v)) return "[seen]"; seen.add(v); }
  return v;
}));
```
```text
===== node20 js28b-31b-throws.js (exit=0) =====
[1] cycles
  self.me = self                  TypeError
    | Converting circular structure to JSON
    |     --> starting at object with constructor 'Object'
    |     --- property 'me' closes the circle
  a.b.c.back = a                  TypeError
    | Converting circular structure to JSON
    |     --> starting at object with constructor 'Object'
    |     |     property 'b' -> object with constructor 'Object'
    |     |     property 'c' -> object with constructor 'Object'
    |     --- property 'back' closes the circle
  arr[1][1] = arr                 TypeError
    | Converting circular structure to JSON
    |     --> starting at object with constructor 'Array'
    |     |     index 1 -> object with constructor 'Array'
    |     --- index 1 closes the circle
  class instances, n1 <-> n2      TypeError
    | Converting circular structure to JSON
    |     --> starting at object with constructor 'Node2'
    |     |     property 'next' -> object with constructor 'Node2'
    |     --- property 'next' closes the circle

[2] one object reached through two keys
  { x: shared, y: shared }        returned {"x":{"v":1},"y":{"v":1}}

[3] BigInt
  1n                              TypeError
    | Do not know how to serialize a BigInt
  { id: 10n }                     TypeError
    | Do not know how to serialize a BigInt
  replacer: bigint -> toString()  returned {"id":"10"}
  BigInt.prototype.toJSON set     returned {"id":"10n"}

[4] a.b.c.back = a again, with a WeakSet replacer
  WeakSet replacer                returned {"name":"a","b":{"c":{"back":"[seen]"}}}
```

```text
   a = { name, b: { c: { back: a } } }        stack(명세의 [[Stack]]) 을 따라가 본다

   SerializeJSONObject(a)       stack [a]
     b -> SerializeJSONObject    stack [a, a.b]
       c -> SerializeJSONObject  stack [a, a.b, a.b.c]
         back -> a               a 가 stack 에 있다 -> TypeError

   V8 메시지의 네 줄은 그 stack 을 차례로 읽은 것이다
     둘째 줄   시작 객체 a 의 생성자 이름            <- stack 의 a
     셋째 줄   키 b 를 지나 만난 객체의 생성자 이름    <- a.b
     넷째 줄   키 c 를 지나 만난 객체의 생성자 이름    <- a.b.c
     다섯째 줄 고리를 닫은 키 back                   <- 다시 a 로
```

- ★★★ **순환 참조는 `TypeError`** 이고, ★★ **V8 의 메시지는 경로를 말해 준다** — 시작 객체의 생성자 이름, 거쳐 간 키, **고리를 닫은 키**까지.
  `a.b.c.back = a` 는 **다섯 줄**, 자기 자신을 가리키는 `self.me = self` 는 거쳐 간 칸이 없어 **세 줄**이다.
  배열은 `property` 대신 **`index 1`** 로 적고, 클래스 인스턴스는 **`constructor 'Node2'`** 처럼 **클래스 이름**을 적는다.
- ★★★ **메시지의 모양은 V8 의 것이다.** 명세(`SerializeJSONObject`·`SerializeJSONArray`)는 「**stack 에 이미 있으면 `TypeError`**」까지만 정한다 — 경로를 그리라는 말이 없다. **문구로 분기하는 코드를 쓰지 마라.**
- ★★★ **`[2]` 같은 객체를 두 키가 가리키는 것은 순환이 아니다** — 통과하고, 결과에 **`{"v":1}` 이 두 번** 들어간다. 되살리면 **두 개의 다른 객체**다(동작 (5)의 `same object twice` 행).
  stack 은 **지금 내려가고 있는 길**만 들고 있어서, 옆 가지에서 이미 본 객체는 안 걸린다.
- ★★★ **`[3]` `BigInt` 는 `TypeError 「Do not know how to serialize a BigInt」`** 다. **속성 안에 있어도 똑같다** — `undefined` 처럼 조용히 빠지지 않는다.
  ★ **`replacer` 로 문자열로 바꾸면 통과**하고, **`BigInt.prototype.toJSON` 을 달아도 통과**한다 — 명세가 `toJSON` 을 찾는 조건이 「**객체이거나 BigInt**」이기 때문이다(동작 (1)의 그림 첫 줄). 전역 프로토타입을 고치는 쪽은 권하지 않는다.
- ★★ **`[4]` `replacer` 로 순환을 끊을 수 있다** — 이미 본 객체면 `"[seen]"` 을 돌려주게 했더니 `back` 이 글자가 되어 통과했다. 단 이 `WeakSet` 판은 **순환이 아닌 공유**(`[2]`)도 `"[seen]"` 으로 바꾼다 — **stack 과 「본 적 있음」은 다른 집합**이다.

### (3) ★★★ `toJSON` 과 `replacer` — 누가 먼저, 누구를 `this` 로

**언제 쓰나** — 비밀번호 필드를 빼거나, `BigInt`·`Map` 을 글자로 바꾸거나, 특정 클래스를 원하는 모양으로 내보낼 때.

```js
// js28b-31c-tojson-replacer.js
// JSON.stringify(value, replacer) -- who is called first for each key, toJSON or the replacer?
// And what does the replacer see: the key, the value, and `this`.
const log = [];
const J = JSON.stringify;
const t = (v) => (v === null ? "null" : Array.isArray(v) ? "array" : typeof v);

const inner = {
  x: 1,
  toJSON(key) { log.push("toJSON(key=" + J(key) + ")"); return { swapped: true }; },
};
const root = { a: inner, b: [10, new Date(0)] };

function replacer(key, value) {
  const holder = this === root ? "root" : this === inner ? "inner" : Array.isArray(this) ? "array" :
    J(Object.keys(this)) === '[""]' ? '{"": root}' : "{" + Object.keys(this).join(",") + "}";
  log.push("replacer(key=" + J(key) + ", value:" + t(value) + ", this=" + holder + ")");
  return value;
}

console.log("[1] call log");
const out = J(root, replacer);
for (const line of log) console.log("  " + line);
console.log("  result " + out);

console.log("");
console.log("[2] toJSON on the root object itself");
log.length = 0;
const r2 = J({ toJSON(k) { log.push("root toJSON(key=" + J(k) + ")"); return 42; } }, (k, v) => { log.push("replacer(key=" + J(k) + ", value " + J(v) + ")"); return v; });
for (const line of log) console.log("  " + line);
console.log("  result " + r2);

console.log("");
console.log("[3] what the replacer returns");
console.log("  undefined for key b        " + J({ a: 1, b: 2 }, (k, v) => (k === "b" ? undefined : v)));
console.log("  undefined for key \"\"       " + J({ a: 1 }, (k, v) => (k === "" ? undefined : v)));
console.log("  undefined for index 1      " + J([1, 2, 3], (k, v) => (k === "1" ? undefined : v)));
console.log("  typeof key for an index    " + (() => { let seen; J([7], function (k, v) { if (k !== "") seen = typeof k; return v; }); return seen; })());

console.log("");
console.log("[4] replacer as an array -- an allow-list of keys");
const deep = { id: 1, name: "n", meta: { id: 2, secret: "s", name: "m" }, list: [{ id: 3, x: 0 }] };
console.log("  ['id', 'meta']             " + J(deep, ["id", "meta"]));
console.log("  ['id', 'meta', 'list']     " + J(deep, ["id", "meta", "list"]));
console.log("  [1, 'id', 'id']            " + J({ 1: "one", id: 1 }, [1, "id", "id"]));
console.log("  ['0'] on an array          " + J(["a", "b"], ["0"]));

console.log("");
console.log("[5] the space argument");
const sp = (s) => J(J({ a: [1] }, null, s));
console.log("  2          " + sp(2));
console.log("  10         " + sp(10));
console.log("  20         " + sp(20));
console.log("  -1         " + sp(-1));
console.log("  '--'       " + sp("--"));
console.log("  'abcdefghijklmnop'  " + sp("abcdefghijklmnop"));
console.log("  length of the indent for 20         " + J({ a: 1 }, null, 20).split("\n")[1].indexOf('"'));
```
```text
===== node20 js28b-31c-tojson-replacer.js (exit=0) =====
[1] call log
  replacer(key="", value:object, this={"": root})
  toJSON(key="a")
  replacer(key="a", value:object, this=root)
  replacer(key="swapped", value:boolean, this={swapped})
  replacer(key="b", value:array, this=root)
  replacer(key="0", value:number, this=array)
  replacer(key="1", value:string, this=array)
  result {"a":{"swapped":true},"b":[10,"1970-01-01T00:00:00.000Z"]}

[2] toJSON on the root object itself
  root toJSON(key="")
  replacer(key="", value 42)
  result 42

[3] what the replacer returns
  undefined for key b        {"a":1}
  undefined for key ""       undefined
  undefined for index 1      [1,null,3]
  typeof key for an index    string

[4] replacer as an array -- an allow-list of keys
  ['id', 'meta']             {"id":1,"meta":{"id":2}}
  ['id', 'meta', 'list']     {"id":1,"meta":{"id":2},"list":[{"id":3}]}
  [1, 'id', 'id']            {"1":"one","id":1}
  ['0'] on an array          ["a","b"]

[5] the space argument
  2          "{\n  \"a\": [\n    1\n  ]\n}"
  10         "{\n          \"a\": [\n                    1\n          ]\n}"
  20         "{\n          \"a\": [\n                    1\n          ]\n}"
  -1         "{\"a\":[1]}"
  '--'       "{\n--\"a\": [\n----1\n--]\n}"
  'abcdefghijklmnop'  "{\nabcdefghij\"a\": [\nabcdefghijabcdefghij1\nabcdefghij]\n}"
  length of the indent for 20         10
```

```text
   SerializeJSONProperty(state, key, holder) 한 번 = 한 키

   ① value = holder[key]
   ② value 가 객체(또는 BigInt)이고 toJSON 이 있으면   value = value.toJSON(key)      ← 먼저
   ③ replacer 가 있으면                              value = replacer.call(holder, key, value)   ← 그 다음, 바뀐 value 를 받는다
   ④ 그 value 를 글자로 만든다 (객체면 그 안의 키마다 ①부터 다시)

   맨 처음 한 번은 감싸개 { "": root } 를 holder 로, key 를 "" 로 부른다
```

- ★★★ **`toJSON` 이 먼저, `replacer` 가 그 다음**이다 — 로그 둘째·셋째 줄이 `toJSON(key="a")` → `replacer(key="a", value:object, …)` 이고,
  넷째 줄의 `replacer` 는 **`swapped`** 를 받았다 — 원래의 `x` 가 아니다. **`replacer` 는 `toJSON` 이 바꾼 결과만 본다.**
- ★★★ **`Date` 도 같다** — 마지막 줄 `replacer(key="1", value:string, …)` 은 `Date` 가 **이미 문자열이 된 뒤**에 `replacer` 가 받은 것이다. `replacer` 안에서 `value instanceof Date` 는 **거짓**이다(원본은 `this[key]` 로 읽는다).
- ★★★ **첫 호출은 `key=""`, `this={"": root}`** 다 — 명세가 만든 **감싸개 객체**다. 그래서 `replacer` 는 **루트 값도 한 번 받는다.**
- ★★ **`toJSON` 은 자기 키를 인자로 받는다**(`toJSON(key="a")`). 루트에서는 `""` 다(`[2]`). 루트의 `toJSON` 이 `42` 를 돌려주면 결과 전체가 **`42`** 다.
- ★★ **`this` 는 그 값을 들고 있던 객체**(holder)다 — `a`·`b` 는 `root`, `swapped` 는 **`toJSON` 이 돌려준 새 객체**, 배열 원소는 배열.
- ★★★ **`[3]` `replacer` 가 `undefined` 를 돌려주면 동작 (1)의 규칙 그대로다** — 속성은 **빠지고**, 배열 원소는 **`null`**, 루트(`key ""`)면 결과가 **`undefined`**. 배열의 키도 **문자열**(`"1"`)로 온다.
- ★★★ **`[4]` `replacer` 가 배열이면 허용 목록**이다 — **모든 깊이의 객체 키에 같은 목록이 적용된다**(`meta` 안에서도 `id` 만 남고, 목록에 `name` 이 없으니 `name` 도 빠진다).
  `list` 를 목록에 넣어야 배열이 나오고, 그 안의 객체에도 또 목록이 적용된다(`[{"id":3}]`). **배열의 인덱스에는 적용되지 않는다**(`['0']` 을 줘도 `["a","b"]` 전부).
  숫자 `1` 은 `"1"` 로 바뀌고 중복 `'id'` 는 한 번만 센다.
- ★★★ **`[5]` `space` 의 상한은 10** 이다 — `10` 과 `20` 이 **한 글자도 같고**, 들여쓰기 칸 수가 `10` 이다. 문자열이면 **앞의 10글자만** 쓴다(`abcdefghij`). `1` 보다 작으면 들여쓰기 없음.

### (4) ★★★ `JSON.parse` 와 `reviver` — 안쪽부터 부르고, 뿌리가 마지막

**언제 쓰나** — ISO 문자열을 `Date` 로 되살리거나, 특정 키를 지우거나 값을 바꾸며 파싱할 때.

```js
// js28b-31d-parse-reviver.js
// JSON.parse(text, reviver) -- in which order is the reviver called, and what can it change?
const J = JSON.stringify;
const text = '{"a":{"b":1,"c":[2,3]},"d":4}';

console.log("[1] call order");
const log = [];
JSON.parse(text, function (key, value) {
  log.push(J(key) + (typeof value === "object" && value !== null ? " (object)" : " = " + J(value)));
  return value;
});
log.forEach((l, i) => console.log("  " + String(i + 1).padStart(2) + ". " + l));

console.log("");
console.log("[2] returning undefined, and returning something else");
console.log("  drop key b       " + J(JSON.parse(text, (k, v) => (k === "b" ? undefined : v))));
console.log("  drop index 0     " + J(JSON.parse(text, (k, v) => (k === "0" ? undefined : v))));
console.log("  double numbers   " + J(JSON.parse(text, (k, v) => (typeof v === "number" ? v * 2 : v))));
console.log("  drop key \"\"      " + String(JSON.parse(text, (k, v) => (k === "" ? undefined : v))));
const iso = '{"when":"1970-01-01T00:00:00.000Z"}';
const plain = JSON.parse(iso);
const revived = JSON.parse(iso, (k, v) => (k === "when" ? new Date(v) : v));
console.log("  without reviver  typeof when = " + typeof plain.when);
console.log("  with reviver     when instanceof Date = " + (revived.when instanceof Date));

console.log("");
console.log("[3] the key \"__proto__\" in JSON text, next to the same key in an object literal");
const fromText = JSON.parse('{"__proto__": {"marker": 1}}');
const fromLiteral = { "__proto__": { marker: 1 } };
for (const [n, o] of [["JSON.parse", fromText], ["object literal", fromLiteral]]) {
  console.log("  " + n.padEnd(16) + "own keys " + J(Object.keys(o)).padEnd(16) +
    "o.marker " + String(o.marker).padEnd(11) + "prototype is Object.prototype " + (Object.getPrototypeOf(o) === Object.prototype));
}

console.log("");
console.log("[4] texts at the edge of the grammar");
const bad = ["{'a': 1}", '{"a": 1,}', "[1, 2,]", "{a: 1}", "NaN", "undefined", "01", ""];
for (const s of bad) {
  try { console.log("  " + J(s).padEnd(18) + "-> " + J(JSON.parse(s))); }
  catch (e) { console.log("  " + J(s).padEnd(18) + "-> " + e.constructor.name + " 「" + e.message + "」"); }
}
console.log("  " + J(' [1] ').padEnd(18) + "-> " + J(JSON.parse(" [1] ")));
console.log("  " + J('{"a":1,"a":2}').padEnd(18) + "-> " + J(JSON.parse('{"a":1,"a":2}')));
```
```text
===== node20 js28b-31d-parse-reviver.js (exit=0) =====
[1] call order
   1. "b" = 1
   2. "0" = 2
   3. "1" = 3
   4. "c" (object)
   5. "a" (object)
   6. "d" = 4
   7. "" (object)

[2] returning undefined, and returning something else
  drop key b       {"a":{"c":[2,3]},"d":4}
  drop index 0     {"a":{"b":1,"c":[null,3]},"d":4}
  double numbers   {"a":{"b":2,"c":[4,6]},"d":8}
  drop key ""      undefined
  without reviver  typeof when = string
  with reviver     when instanceof Date = true

[3] the key "__proto__" in JSON text, next to the same key in an object literal
  JSON.parse      own keys ["__proto__"]   o.marker undefined  prototype is Object.prototype true
  object literal  own keys []              o.marker 1          prototype is Object.prototype false

[4] texts at the edge of the grammar
  "{'a': 1}"        -> SyntaxError 「Expected property name or '}' in JSON at position 1」
  "{\"a\": 1,}"     -> SyntaxError 「Expected double-quoted property name in JSON at position 8」
  "[1, 2,]"         -> SyntaxError 「Unexpected token ']', "[1, 2,]" is not valid JSON」
  "{a: 1}"          -> SyntaxError 「Expected property name or '}' in JSON at position 1」
  "NaN"             -> SyntaxError 「"NaN" is not valid JSON」
  "undefined"       -> SyntaxError 「"undefined" is not valid JSON」
  "01"              -> SyntaxError 「Unexpected number in JSON at position 1」
  ""                -> SyntaxError 「Unexpected end of JSON input」
  " [1] "           -> [1]
  "{\"a\":1,\"a\":2}"-> {"a":2}
```

```text
   '{"a":{"b":1,"c":[2,3]},"d":4}'    InternalizeJSONProperty(holder, name) 는
                                     「자식을 전부 먼저 돌고, 마지막에 자기 이름으로 reviver 를 부른다」
          ""  ⑦
         /   \
      "a" ⑤   "d" ⑥
      /   \
   "b" ①  "c" ④
          /   \
       "0" ②  "1" ③          ① → ⑦ : 후위 순회(post-order). 뿌리 "" 가 마지막
```

- ★★★ **`[1]` 순서가 `b, 0, 1, c, a, d, ""`** 다 — **잎이 먼저, 그 부모가 나중, 뿌리 `""` 가 맨 끝.** `reviver` 가 부모를 받는 시점에는 **자식이 이미 되살려져 있다.**
- ★★★ **`[2]` `undefined` 를 돌려주면 지운다** — 객체면 키째(`b` 가 없다), ★★ **배열이면 구멍**이 생겨 다시 `stringify` 하면 `null` 이다(`[null,3]` — 길이가 안 줄었다).
  뿌리에서 `undefined` 를 돌려주면 결과 전체가 **`undefined`**.
- ★★ **`Date` 는 저절로 안 돌아온다** — `reviver` 없이 `typeof when` 은 `string`. **글자 모양을 보고 되살리는 것은 `reviver` 의 몫**이다.
- ★★★ **`[3]` JSON 글자 안의 `"__proto__"` 는 그냥 데이터 키**다 — `JSON.parse` 결과는 own 키 `["__proto__"]` 를 갖고 **프로토타입은 그대로** `Object.prototype` 이다.
  같은 글자를 **객체 리터럴**로 쓰면 own 키가 없고 **프로토타입이 바뀐다**(`o.marker` 가 `1`). 리터럴 쪽 다섯 형태는 13번, 그 결과를 `Object.assign` 에 넣으면 프로토타입이 바뀌는 것은 27번 `[4]` 가 정본이다.
  명세의 note 가 이 차이를 적어 둔다 — 「`ParseJSON` 동안에는 속성 정의 의미가 **다르게** 동작해서 같은 글자가 다른 결과를 낸다」.
- ★★★ **`[4]` 문법 가장자리** — 작은따옴표 · 끝 쉼표 · 따옴표 없는 키 · `NaN` · `undefined` · 앞자리 `0` · 빈 문자열은 **전부 `SyntaxError`** 다(JSON 은 JS 리터럴보다 **좁다**).
  앞뒤 공백은 통과하고, ★ **중복 키는 뒤의 것이 이긴다**(`{"a":2}` — 에러가 아니다).
- ★★★ **실패 문구는 두 node 판이 다르다** — 아래 node18 판과 위 node20 판을 견줘 보라. node18 은 「`Unexpected token ' in JSON at position 1`」, node20 은 「`Expected property name or '}' in JSON at position 1`」이다. **종류(`SyntaxError`)와 위치 숫자는 같다.**

```text
===== node18 js28b-31d-parse-reviver.js (exit=0) =====
[1] call order
   1. "b" = 1
   2. "0" = 2
   3. "1" = 3
   4. "c" (object)
   5. "a" (object)
   6. "d" = 4
   7. "" (object)

[2] returning undefined, and returning something else
  drop key b       {"a":{"c":[2,3]},"d":4}
  drop index 0     {"a":{"b":1,"c":[null,3]},"d":4}
  double numbers   {"a":{"b":2,"c":[4,6]},"d":8}
  drop key ""      undefined
  without reviver  typeof when = string
  with reviver     when instanceof Date = true

[3] the key "__proto__" in JSON text, next to the same key in an object literal
  JSON.parse      own keys ["__proto__"]   o.marker undefined  prototype is Object.prototype true
  object literal  own keys []              o.marker 1          prototype is Object.prototype false

[4] texts at the edge of the grammar
  "{'a': 1}"        -> SyntaxError 「Unexpected token ' in JSON at position 1」
  "{\"a\": 1,}"     -> SyntaxError 「Unexpected token } in JSON at position 8」
  "[1, 2,]"         -> SyntaxError 「Unexpected token ] in JSON at position 6」
  "{a: 1}"          -> SyntaxError 「Unexpected token a in JSON at position 1」
  "NaN"             -> SyntaxError 「Unexpected token N in JSON at position 0」
  "undefined"       -> SyntaxError 「Unexpected token u in JSON at position 0」
  "01"              -> SyntaxError 「Unexpected number in JSON at position 1」
  ""                -> SyntaxError 「Unexpected end of JSON input」
  " [1] "           -> [1]
  "{\"a\":1,\"a\":2}"-> {"a":2}
```

- ★★ **이 블록이 이 주제에서 두 판이 갈린 유일한 자리**다(대조기의 `DIFFERS`). 갈린 것은 **`[4]` 의 문구 여섯 줄뿐**이고 `[1]`\~`[3]` 은 한 글자도 같다.

### (5) ★★★ 깊은 복사 대용의 손실 — JSON 왕복 대 `structuredClone`

**언제 쓰나** — 「상태를 통째로 복사해 두자」에서 `JSON.parse(JSON.stringify(x))` 를 떠올릴 때.
★★ **깊은 복사 수단 비교의 정본은 목록의 48번 주제**다. 여기서는 **JSON 왕복이 무엇을 잃나**를 보고, `structuredClone` 은 **비교 열 하나**로만 둔다.

```js
// js28b-31e-deep-copy.js
// JSON.parse(JSON.stringify(x)) as a deep copy, next to structuredClone(x) -- what comes back for each kind of value?
// structuredClone is a host API (HTML), not ECMA-262. The script counts the rows at the end.
const J = JSON.stringify;
const viaJSON = (x) => JSON.parse(JSON.stringify(x));
const viaClone = (x) => structuredClone(x);
const run = (copy, make, test) => {
  try { return test(copy(make())); } catch (e) { return e.constructor.name; }
};

class Point { constructor() { this.x = 1; } }
const rows = [
  ["Date", () => ({ v: new Date(0) }), (c) => (c.v instanceof Date ? "Date" : typeof c.v)],
  ["Map", () => ({ v: new Map([["k", 1]]) }), (c) => (c.v instanceof Map ? "Map size " + c.v.size : J(c.v))],
  ["Set", () => ({ v: new Set([1]) }), (c) => (c.v instanceof Set ? "Set size " + c.v.size : J(c.v))],
  ["undefined property", () => ({ v: undefined }), (c) => ("v" in c ? "key kept" : "key gone")],
  ["NaN", () => ({ v: NaN }), (c) => String(c.v)],
  ["-0", () => ({ v: -0 }), (c) => (Object.is(c.v, -0) ? "-0" : String(c.v))],
  ["BigInt", () => ({ v: 1n }), (c) => typeof c.v],
  ["RegExp", () => ({ v: /a/g }), (c) => (c.v instanceof RegExp ? "RegExp " + c.v : J(c.v))],
  ["class instance", () => new Point(), (c) => (c instanceof Point ? "Point" : "plain " + J(c))],
  ["function property", () => ({ v: () => 1 }), (c) => typeof c.v],
  ["same object twice", () => { const s = {}; return { a: s, b: s }; }, (c) => (c.a === c.b ? "still one object" : "two objects")],
  ["cycle", () => { const o = {}; o.me = o; return o; }, (c) => (c.me === c ? "cycle kept" : "?")],
  ["getter", () => ({ get v() { return 1; } }), (c) => (typeof Object.getOwnPropertyDescriptor(c, "v").get === "function" ? "getter" : "data " + c.v)],
];

console.log("[1] kind of value            " + "JSON round trip".padEnd(24) + "structuredClone");
let differ = 0;
for (const [label, make, test] of rows) {
  const a = run(viaJSON, make, test);
  const b = run(viaClone, make, test);
  if (a !== b) differ += 1;
  console.log("  " + label.padEnd(26) + a.padEnd(24) + b);
}

console.log("");
console.log("[2] the two exceptions -- constructor, name, and the first line of the message");
for (const [n, f] of [["JSON round trip   cycle", () => viaJSON((() => { const o = {}; o.me = o; return o; })())],
                      ["structuredClone   function", () => viaClone({ v: () => 1 })]]) {
  try { f(); console.log("  " + n + "   no exception"); }
  catch (e) { console.log("  " + n.padEnd(28) + e.constructor.name + " (name " + e.name + ") 「" + e.message.split("\n")[0] + "」"); }
}

console.log("");
console.log("rows where the two columns differ: " + differ + " / " + rows.length);
```
```text
===== node20 js28b-31e-deep-copy.js (exit=0) =====
[1] kind of value            JSON round trip         structuredClone
  Date                      string                  Date
  Map                       {}                      Map size 1
  Set                       {}                      Set size 1
  undefined property        key gone                key kept
  NaN                       null                    NaN
  -0                        0                       -0
  BigInt                    TypeError               bigint
  RegExp                    {}                      RegExp /a/g
  class instance            plain {"x":1}           plain {"x":1}
  function property         undefined               DOMException
  same object twice         two objects             still one object
  cycle                     TypeError               cycle kept
  getter                    data 1                  data 1

[2] the two exceptions -- constructor, name, and the first line of the message
  JSON round trip   cycle     TypeError (name TypeError) 「Converting circular structure to JSON」
  structuredClone   function  DOMException (name DataCloneError) 「() => 1 could not be cloned.」

rows where the two columns differ: 11 / 13
```

```text
   JSON 왕복 = 동작 (1)의 격자를 한 번 지나고, 글자에서 다시 만든다

   값 ──stringify──▶  글자  ──parse──▶  새 값
   Date        toJSON        "1970-…Z"            문자열로 남는다
   Map / Set   own 키 없음     {}                  빈 객체
   undefined   속성이면 빠짐    (없음)               키가 없다
   NaN / -0    유한 아님 / 부호  null / 0            다른 값
   공유 객체    두 번 쓴다      {..}, {..}          두 객체가 된다
   순환         stack 에 걸림   TypeError            복사 자체가 실패
```

- ★★★ **두 열이 갈린 행은 `11 / 13`** 이다. **안 갈린 두 행은 `class instance` 와 `getter`** — 둘 다 **두 도구가 똑같이 잃는다**(프로토타입은 `plain {"x":1}`, getter 는 `data 1`).
- ★★★ JSON 왕복의 손실 — **`Date` → 문자열 · `Map`/`Set` → `{}` · `undefined` 속성 → 키가 없음 · `NaN` → `null` · `-0` → `0` · `BigInt` → `TypeError` · `RegExp` → `{}` · 공유 객체 → 둘로 갈라짐 · 순환 → `TypeError`.**
- ★★ **`structuredClone` 은 그 대부분을 지킨다** — `Date`·`Map`·`Set`·`RegExp`·`NaN`·`-0`·`BigInt`·**공유(`still one object`)·순환(`cycle kept`)**.
  ★★ 그러나 **함수가 있으면 던진다** — `DOMException`(이름 `DataCloneError`). JSON 왕복은 함수 속성을 **조용히 뺀다**(`undefined`). **한쪽은 조용히 잃고, 한쪽은 시끄럽게 거절한다.**
- ★★ **예외 문구는 첫 줄만** 찍었다(탐침의 `split("\n")[0]`) — 순환 참조의 전문은 동작 (2)에 있다.

### (6) ★★ 원문 접근 — `JSON.rawJSON` 과 `reviver` 의 셋째 인자(ES2026)

**언제 쓰나** — 20자리 ID 처럼 **double 에 안 들어가는 숫자**를 잃지 않고 읽고 쓰고 싶을 때.
★★★ **두 node 판에는 없다**(판별 블록의 `ES2026` 두 줄 · 아래 node 탐침). 그래서 **Chrome 151 에서만** 돌렸다.

```text
   글자 "12345678901234567890"

   ES5 까지의 길      JSON.parse ──▶ Number 12345678901234567000 ──▶ reviver(key, value)
                                     (double 로 반올림된 뒤라 원래 글자는 이미 없다)

   ES2026 의 길      JSON.parse ──▶ Number …7000 ──▶ reviver(key, value, { source: "…7890" })
                                                          └─ 원문 글자로 BigInt 를 만든다
                     JSON.stringify({ id: JSON.rawJSON("…7890") }) ──▶ 글자를 그대로 끼운다
```

```js
// js28b-31x-node-rawjson.js
// The same two features asked of node -- do they exist on this build?
const J = JSON.stringify;
console.log("typeof JSON.rawJSON      " + typeof JSON.rawJSON);
console.log("typeof JSON.isRawJSON    " + typeof JSON.isRawJSON);
let args;
JSON.parse("12345678901234567890", function (k, v, ctx) { args = arguments.length; return v; });
console.log("reviver arguments.length " + args);
try { J({ id: JSON.rawJSON("1") }); console.log("JSON.rawJSON('1')        no exception"); }
catch (e) { console.log("JSON.rawJSON('1')        " + e.constructor.name + " 「" + e.message + "」"); }
```
```text
===== node20 js28b-31x-node-rawjson.js (exit=0) =====
typeof JSON.rawJSON      undefined
typeof JSON.isRawJSON    undefined
reviver arguments.length 2
JSON.rawJSON('1')        TypeError 「JSON.rawJSON is not a function」
```

```js
// js28b-31f-rawjson.web.js
// JSON.rawJSON and the reviver's third argument (source text access) -- Chrome only; node probe is js28b-31x-node-rawjson.js.
const J = JSON.stringify;
const show = (label, f) => {
  try { console.log("  " + label.padEnd(46) + f()); }
  catch (e) { console.log("  " + label.padEnd(46) + e.constructor.name + " 「" + e.message + "」"); }
};
const big = "12345678901234567890";

console.log("[1] a number with more digits than a double holds");
show("JSON.parse(big)", () => String(JSON.parse(big)));
show("reviver: value, context.source", () => {
  let seen;
  JSON.parse(big, (k, v, ctx) => { seen = [String(v), J(ctx)]; return v; });
  return seen.join("   ");
});
show("reviver returns BigInt(context.source)", () => String(JSON.parse(big, (k, v, ctx) => BigInt(ctx.source))) + "n");

console.log("");
console.log("[2] which keys get a source");
JSON.parse('{"n": 1.50, "s": "x", "o": {"t": true}, "a": [null]}', (k, v, ctx) => {
  console.log("  key " + J(k).padEnd(6) + "context " + J(ctx));
  return v;
});

console.log("");
console.log("[3] JSON.rawJSON");
show("JSON.stringify({ id: JSON.rawJSON(big) })", () => J({ id: JSON.rawJSON(big) }));
show("JSON.stringify({ id: 12345678901234567890 })", () => J({ id: 12345678901234567890 }));
show("JSON.stringify({ n: JSON.rawJSON('1.50') })", () => J({ n: JSON.rawJSON("1.50") }));
show("JSON.isRawJSON(JSON.rawJSON('1'))", () => JSON.isRawJSON(JSON.rawJSON("1")));
show("Object.isFrozen(JSON.rawJSON('1'))", () => Object.isFrozen(JSON.rawJSON("1")));
show("Object.getPrototypeOf(JSON.rawJSON('1'))", () => String(Object.getPrototypeOf(JSON.rawJSON("1"))));
show("JSON.rawJSON('{}')", () => J(JSON.rawJSON("{}")));
show("JSON.rawJSON(' 1')", () => J(JSON.rawJSON(" 1")));
show("JSON.rawJSON('abc')", () => J(JSON.rawJSON("abc")));
show("replacer returns rawJSON for a BigInt", () => J({ id: 10n ** 20n }, (k, v) => (typeof v === "bigint" ? JSON.rawJSON(v.toString()) : v)));
```
```text
===== google-chrome --headless --virtual-time-budget=2000 --dump-dom 'js28b-page.html?js28b-31f-rawjson.web.js' | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' | sed 's/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&amp;/\&/g' (exit=0) =====
[1] a number with more digits than a double holds
  JSON.parse(big)                               12345678901234567000
  reviver: value, context.source                12345678901234567000   {"source":"12345678901234567890"}
  reviver returns BigInt(context.source)        12345678901234567890n

[2] which keys get a source
  key "n"   context {"source":"1.50"}
  key "s"   context {"source":"\"x\""}
  key "t"   context {"source":"true"}
  key "o"   context {}
  key "0"   context {"source":"null"}
  key "a"   context {}
  key ""    context {}

[3] JSON.rawJSON
  JSON.stringify({ id: JSON.rawJSON(big) })     {"id":12345678901234567890}
  JSON.stringify({ id: 12345678901234567890 })  {"id":12345678901234567000}
  JSON.stringify({ n: JSON.rawJSON('1.50') })   {"n":1.50}
  JSON.isRawJSON(JSON.rawJSON('1'))             true
  Object.isFrozen(JSON.rawJSON('1'))            true
  Object.getPrototypeOf(JSON.rawJSON('1'))      null
  JSON.rawJSON('{}')                            SyntaxError 「Unexpected token '{', "{}" is not valid JSON」
  JSON.rawJSON(' 1')                            SyntaxError 「Unexpected token ' ', " 1" is not valid JSON」
  JSON.rawJSON('abc')                           SyntaxError 「Unexpected token 'a', "abc" is not valid JSON」
  replacer returns rawJSON for a BigInt         {"id":100000000000000000000}
```

- ★★★ **node 쪽은 `typeof JSON.rawJSON` 이 `undefined` 이고 `reviver` 는 인자를 둘만 받는다**(`arguments.length 2`). 부르면 `TypeError 「JSON.rawJSON is not a function」`.
- ★★★ **Chrome 쪽 `[1]`** — 그냥 파싱하면 `12345678901234567000` 으로 **끝자리가 뭉개지지만**, `reviver` 의 셋째 인자 `context.source` 에는 **원래 글자 `"12345678901234567890"`** 이 남아 있어 `BigInt` 로 되살릴 수 있다.
- ★★ **`[2]` `source` 는 원시값에만 있다** — 객체·배열·뿌리의 `context` 는 `{}` 다. `"1.50"` 은 **글자 그대로**(`1.5` 가 아니다).
- ★★ **`[3]` `JSON.rawJSON` 은 원시 JSON 글자 하나를 감싼 동결된 null 프로토타입 객체**이고, `stringify` 는 그 글자를 **그대로 끼운다**(`1.50` · 20자리 숫자). `{}`·앞 공백·`abc` 는 `SyntaxError` — **원시값 하나**만 받는다.

### (7) ★★ 파이썬 `json` 과의 대비

**언제 쓰나** — 파이썬 서비스와 JSON 을 주고받을 때 「같은 값이 양쪽에서 같은 글자가 되나」를 볼 때.
파이썬 쪽은 Python 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **47번**(`json`)이 정본인데 **아직 폴더가 없어**, 같은 질문을 **직접 던졌다**(python3 3.12.3).

```sh
# js28b-31g-python-contrast.sh
#!/usr/bin/env bash
# 파이썬 json 에 같은 질문을 던진다 -- 소스는 js28b-31-h-pyjson.py 에 있다.
set -u -o pipefail
python3 js28b-31-h-pyjson.py
```
```python
# js28b-31-h-pyjson.py
# Python json.dumps / json.loads asked the same questions as the JS probes -- exceptions print as name 「message」.
import json, math

def show(label, f):
    try:
        print("  " + label.ljust(44) + repr(f()))
    except Exception as e:
        print("  " + label.ljust(44) + type(e).__name__ + " 「" + str(e) + "」")

print("[1] the values of the JS grid, and dict keys")
show("json.dumps(float('nan'))", lambda: json.dumps(float("nan")))
show("json.dumps(math.inf)", lambda: json.dumps(math.inf))
show("json.dumps(nan, allow_nan=False)", lambda: json.dumps(float("nan"), allow_nan=False))
show("json.dumps(None)", lambda: json.dumps(None))
show("json.dumps({'k': None})", lambda: json.dumps({"k": None}))
show("json.dumps(-0.0)", lambda: json.dumps(-0.0))
show("json.dumps({1: 'a', 2: 'b'})", lambda: json.dumps({1: "a", 2: "b"}))
show("json.dumps({1: 'a', '1': 'b'})", lambda: json.dumps({1: "a", "1": "b"}))
show("json.dumps({(1, 2): 'a'})", lambda: json.dumps({(1, 2): "a"}))
show("json.dumps({1, 2})", lambda: json.dumps({1, 2}))
show("json.dumps(10 ** 20)", lambda: json.dumps(10 ** 20))
show("json.dumps(lambda: 1)", lambda: json.dumps(lambda: 1))

print()
print("[2] cycle")
d = {}
d["me"] = d
show("d['me'] = d", lambda: json.dumps(d))

print()
print("[3] default= -- when is it called?")
calls = []
def default(o):
    calls.append(type(o).__name__)
    return sorted(o) if isinstance(o, set) else str(o)
show("dumps({'s': {2, 1}, 'n': 1}, default=...)", lambda: json.dumps({"s": {2, 1}, "n": 1}, default=default))
print("  default called for                          " + repr(calls))

print()
print("[4] loads")
show("json.loads('NaN')", lambda: json.loads("NaN"))
show("json.loads('12345678901234567890')", lambda: json.loads("12345678901234567890"))
show("json.loads('{\"a\":1,\"a\":2}')", lambda: json.loads('{"a":1,"a":2}'))
show("json.loads('[1,]')", lambda: json.loads("[1,]"))
```
```text
===== ./js28b-31g-python-contrast.sh (exit=0) =====
[1] the values of the JS grid, and dict keys
  json.dumps(float('nan'))                    'NaN'
  json.dumps(math.inf)                        'Infinity'
  json.dumps(nan, allow_nan=False)            ValueError 「Out of range float values are not JSON compliant: nan」
  json.dumps(None)                            'null'
  json.dumps({'k': None})                     '{"k": null}'
  json.dumps(-0.0)                            '-0.0'
  json.dumps({1: 'a', 2: 'b'})                '{"1": "a", "2": "b"}'
  json.dumps({1: 'a', '1': 'b'})              '{"1": "a", "1": "b"}'
  json.dumps({(1, 2): 'a'})                   TypeError 「keys must be str, int, float, bool or None, not tuple」
  json.dumps({1, 2})                          TypeError 「Object of type set is not JSON serializable」
  json.dumps(10 ** 20)                        '100000000000000000000'
  json.dumps(lambda: 1)                       TypeError 「Object of type function is not JSON serializable」

[2] cycle
  d['me'] = d                                 ValueError 「Circular reference detected」

[3] default= -- when is it called?
  dumps({'s': {2, 1}, 'n': 1}, default=...)   '{"s": [1, 2], "n": 1}'
  default called for                          ['set']

[4] loads
  json.loads('NaN')                           nan
  json.loads('12345678901234567890')          12345678901234567890
  json.loads('{"a":1,"a":2}')                 {'a': 2}
  json.loads('[1,]')                          JSONDecodeError 「Expecting value: line 1 column 4 (char 3)」
```

```text
   같은 질문, 두 언어의 답

                       JS  JSON.stringify            Python json.dumps
   NaN / Infinity      null                          NaN / Infinity  (JSON 이 아닌 글자 -- allow_nan=False 면 ValueError)
   -0                  0                             -0.0
   큰 정수              BigInt 는 TypeError            10**20 그대로
   집합                 {}  (조용히)                   TypeError       (시끄럽게)
   함수                 속성이면 빠진다                  TypeError
   순환                 TypeError + 경로               ValueError 「Circular reference detected」
   손보는 문            replacer -- 모든 키에 불린다     default= -- 직렬화 못 하는 값에만 불린다
```

- ★★★ **파이썬은 거절이 기본, JS 는 조용한 변환이 기본**이다 — 집합·함수에서 파이썬은 `TypeError`, JS 는 `{}`·키 삭제.
- ★★★ **파이썬의 `NaN` 기본값은 JSON 이 아닌 글자**(`'NaN'`)를 낸다 — JS `JSON.parse('NaN')` 은 `SyntaxError` 이므로(동작 (4)) **파이썬이 쓴 것을 JS 가 못 읽는다.** `allow_nan=False` 라야 막힌다.
- ★★ **`default=` 는 「못 싣는 값」에만 불린다**(`['set']` 한 번) — JS `replacer` 는 **모든 키에** 불린다(동작 (3)).
- ★★ **파이썬 `json.dumps({1: 'a', '1': 'b'})` 는 키가 중복된 JSON 을 낸다** — JS 가 그것을 읽으면 **뒤의 것이 이긴다**(동작 (4)의 `[4]`).

## 문법 — 형태와 규칙

★ 이 절은 **형태 표**다 — 모든 동작 주장은 위 동작 절의 캡처 블록에서만 한다(규칙 28 — 돌리지 않은 코드 펜스를 싣지 않는다).

| 형태 | 돌려주는 것 | 판 | 어디서 봤나 |
|---|---|---|---|
| `JSON.stringify(value)` | 문자열 — **또는 `undefined`**(최상위가 `undefined`·함수·심볼일 때) | ES5 | 동작 (1) |
| `JSON.stringify(value, fn)` | `fn.call(holder, key, value)` 를 키마다 — `toJSON` **다음에** | ES5 | 동작 (3) |
| `JSON.stringify(value, ["a", 1])` | 허용 목록 — **모든 깊이의 객체 키**에 적용, 배열 인덱스에는 아님 | ES5 | 동작 (3)의 `[4]` |
| `JSON.stringify(value, null, space)` | 들여쓰기 — 숫자는 **최대 10칸**, 문자열은 **앞 10글자** | ES5 | 동작 (3)의 `[5]` |
| `x.toJSON(key)` | 직렬화 **전에** 값을 바꾼다 — 객체·`BigInt` 에서 찾는다 | ES5 | 동작 (2)·(3) |
| `JSON.parse(text)` | 값 — 문법이 틀리면 `SyntaxError` | ES5 | 동작 (4) |
| `JSON.parse(text, fn)` | `fn.call(holder, key, value)` 를 **후위 순서로** — `undefined` 면 지운다 | ES5 | 동작 (4)의 `[1]` |
| `fn(key, value, context)` · `JSON.rawJSON(text)` · `JSON.isRawJSON(o)` | 원시값의 원문 글자 · 원문을 그대로 끼우는 동결 객체 | **ES2026** | 동작 (6) — Chrome 만 |
| `structuredClone(v)` | 깊은 복사 — **호스트 API**(ECMA-262 밖) | — | 동작 (5) · 목록의 **48번 주제** |

- **자리가 정한다** — 못 싣는 값(`undefined`·함수·심볼)은 **속성이면 빠지고, 배열이면 `null`, 최상위면 `undefined`.**
- **숫자** — 유한하지 않으면 `null`, `-0` 은 `0`, `BigInt` 는 `TypeError`.
- **순서** — `stringify` 는 한 키마다 `toJSON` → `replacer`, `parse` 의 `reviver` 는 잎 → 뿌리.

## 어디서 틀리나

### (1) ★★★ `undefined` 인 필드가 `null` 로 나갈 것이라 믿는다

**키째 빠진다**(동작 (1)의 `(key gone)`). 받는 쪽이 「키 없음」과 「`null`」을 다르게 다루면 여기서 갈린다. `null` 을 보내려면 `null` 을 넣어라.

### (2) ★★★ 배열에서 `undefined`·함수를 빼면 배열이 짧아질 것이라 믿는다

**`null` 로 채워진다**(`[null]`). 인덱스를 지키려는 규칙이다 — 희소 배열의 구멍도 같다(동작 (1)의 `[2]`).

### (3) ★★★ `JSON.stringify(x)` 가 늘 문자열이라 믿는다

**`x` 가 `undefined`·함수·심볼이면 `undefined`** 다. 결과에 `.length` 를 읽거나 그대로 전송하면 거기서 터진다.

### (4) ★★★ `JSON.parse(JSON.stringify(x))` 가 깊은 복사라 믿는다

**`Date` → 문자열 · `Map` → `{}` · `undefined` → 키 없음 · `NaN` → `null` · 공유 → 둘로 · 순환 → `TypeError`**(동작 (5) — 두 열이 `11 / 13` 행에서 갈린다). 깊은 복사 수단의 선택은 목록의 **48번 주제**.

### (5) ★★★ `replacer` 에서 `value instanceof Date` 로 날짜를 잡는다

**이미 문자열이다** — `toJSON` 이 먼저 돈다(동작 (3)). 원본은 `this[key]` 로 읽는다.

### (6) ★★ `replacer` 배열이 맨 위 키에만 적용된다고 믿는다

**모든 깊이의 객체 키**에 적용된다 — 안쪽 객체에서 필요한 키를 목록에 안 넣으면 **안쪽이 텅 빈다**(동작 (3)의 `[4]`).

### (7) ★★ `BigInt` 가 속성 안에 있으면 조용히 빠질 것이라 믿는다

**`TypeError`** 다(동작 (2)의 `[3]`). `replacer` 로 문자열로 바꾸거나, ES2026 이 되는 곳이면 `JSON.rawJSON` 으로 숫자째 싣는다(동작 (6)).

### (8) ★★ 파싱 실패 메시지로 분기한다

**판마다 다르다** — node18 과 node20 이 같은 입력에 **다른 문구**를 낸다(동작 (4)의 `[4]`). 믿을 것은 **`SyntaxError` 라는 종류**뿐이다.

### (9) ★★ 20자리 ID 를 숫자로 파싱한다

**끝자리가 뭉개진다**(`12345678901234567000` — 동작 (6)의 `[1]`). 문자열로 보내게 하거나, `context.source` 로 원문을 읽는다.

### (10) ★ JSON 에서 온 `"__proto__"` 키가 프로토타입을 바꿀 것이라 믿는다

`JSON.parse` 만으로는 **안 바뀐다** — 그냥 own 키다(동작 (4)의 `[3]`). 위험한 것은 그 결과를 **대입으로 합칠 때**다(27번 `[4]` 의 `Object.assign`).

## 구현 세부사항 대 언어 보장

### 명세 보장 — 어느 엔진에서도 같아야 하는 것

- ★★★ `SerializeJSONProperty` 가 **`toJSON` → `replacer` → 래퍼 풀기 → 타입별 글자** 순으로 도는 것, 그리고 `undefined`·함수·심볼에 **`undefined`** 를 돌려주는 것.
- ★★★ 그 `undefined` 를 **`SerializeJSONObject` 는 건너뛰고, `SerializeJSONArray` 는 `"null"` 로 바꾸는 것** · 최상위는 그대로 돌려주는 것. 그래서 자리마다 다르다.
- 유한하지 않은 숫자가 `"null"` · `BigInt` 가 `TypeError` · 순환이 **`TypeError`**(stack 에 있으면).
- `space` 가 **`min(10, …)`** · 문자열은 앞 10글자 · 허용 목록이 **`PropertyList`** 로 모든 객체에 적용되는 것.
- ★★★ `InternalizeJSONProperty` 가 **자식을 먼저 돌고 마지막에 자기 이름으로 `reviver` 를 부르는 것**(후위) · `undefined` 면 `[[Delete]]`.
- `ParseJSON` 동안 `"__proto__"` 가 **정의**로 처리되는 것(note).
- (ES2026) `reviver` 가 원시값에 `context.source` 를 받는 것 · `JSON.rawJSON` 이 **동결된 null 프로토타입 객체**를 만드는 것.

### 엔진(V8) 구현 · 이 판의 관찰

- 예외 **문구 전부** — ★★ 순환 참조의 **여러 줄 경로 그림**(`-->`·`|`·`---`) · `Do not know how to serialize a BigInt` · `JSON.parse` 의 실패 문구(★ **node18 과 node20 이 다르다**).
- 그 밖의 이 주제 node 탐침이 두 판에서 **한 글자도 같았다**는 것 — 관찰이다.

### 호스트가 정하는 것 — ECMA-262 밖

- ★★ **`structuredClone`** 과 그 `DOMException`(`DataCloneError`) — HTML 표준이다. 이 문서는 **node 20 에서 한 열**로만 돌렸다.
- `console.log` 가 객체를 어떻게 보여 주는지 — 이 문서는 전부 `JSON.stringify` 로 찍어 그 영향을 피했다.

### 그래서 이렇게 적으면 틀린다

- ✗ 「`undefined` 는 JSON 에서 `null` 이 된다」 → ○ 「**배열 원소일 때만** `null` — 속성이면 빠지고, 최상위면 `undefined`」
- ✗ 「순환 참조 메시지가 경로를 보여 준다(그러니 파싱해서 쓴다)」 → ○ 「**V8 이 그렇게 적을 뿐**이다 — 명세는 `TypeError` 만 정한다」
- ✗ 「`replacer` 가 원래 값을 받는다」 → ○ 「**`toJSON` 이 바꾼 값**을 받는다」
- ✗ 「`reviver` 는 위에서 아래로 돈다」 → ○ 「**잎부터, 뿌리 `""` 가 마지막**」
- ✗ 「`JSON.rawJSON` 은 ES2025」 → ○ 「**ES2026** — finished proposals 의 JSON.parse source text access 가 2026 이다」
- ✗ 「JSON 왕복이 `structuredClone` 보다 빠르다/느리다」 → ○ **안 쟀다**

## 언제 쓰고 언제 안 쓰나

- **`JSON.stringify`** — 원시값·평범한 객체·배열로 된 **데이터**를 글자로 내보낼 때. 넣기 전에 `undefined`·`Date`·`BigInt`·`Map` 이 섞였는지 떠올린다.
- **`toJSON`** — **자기 클래스**가 JSON 에서 어떻게 보일지 정할 때. 남의 프로토타입(`BigInt.prototype`)에는 달지 않는다.
- **`replacer` 함수** — 호출하는 쪽에서 한 번만 바꿀 때(비밀 필드 빼기 · `BigInt` → 문자열). **배열 `replacer`** 는 모든 깊이에 적용됨을 알고 쓴다.
- **`reviver`** — `Date`·`BigInt` 를 되살릴 때. 부모가 자식보다 **나중**에 불린다는 것을 전제로 짠다.
- **`context.source`·`JSON.rawJSON`** — ES2026 이 되는 런타임에서만(이 머신의 node 두 판에는 없다).
- ★ **안 쓰는 자리** — **깊은 복사**(동작 (5) — 목록의 **48번 주제**) · 순환이 있을 수 있는 그래프 · 함수를 담은 설정 객체.

## 핵심 문장

1. ★★★ `JSON.stringify` 는 `undefined`·함수·심볼을 **속성이면 빼고, 배열 원소면 `null`, 최상위면 `undefined`** 로 만든다 — 값 14종 × 자리 3 의 격자에서 **갈린 행이 `3 / 14`** 였고, 셋이 정확히 그 값들이다.
2. ★★★ 숫자는 유한하지 않으면 `null`, `-0` 은 `0`, **`BigInt` 는 자리와 상관없이 `TypeError`** 다. `Date` 는 `toJSON` 으로 문자열, `Map`·`Set` 은 `{}`.
3. ★★★ 한 키마다 **`toJSON` 이 먼저, `replacer` 가 그 다음**이고 `replacer` 의 `this` 는 그 값을 들고 있던 객체다. 첫 호출은 감싸개 `{"": root}` 에 `key ""`.
4. ★★★ `reviver` 는 **후위 순서**(잎 → 뿌리 `""`)로 불리고, `undefined` 를 돌려주면 지운다(배열이면 구멍).
5. ★★★ 순환 참조는 **`TypeError`** 이고, V8 은 **경로를 그려 준다** — 그 모양은 엔진의 것이다. JSON 왕복은 `structuredClone` 과 **`11 / 13` 행**에서 갈렸다.

## 관련 자료

- [ECMA-262 — The JSON Object](https://tc39.es/ecma262/multipage/structured-data.html#sec-json-object)(`SerializeJSONProperty` · `SerializeJSONObject` · `SerializeJSONArray` · `InternalizeJSONProperty` · `JSON.rawJSON`)
- [TC39 finished proposals](https://github.com/tc39/proposals/blob/main/finished-proposals.md) — 판 경계
- [27 — `Object` 정적 메서드](../27-object-static-methods/2-summary.md) — ★ **경계**: 그쪽은 **복사 도구 넷의 얕음 격자(`3 / 18`)와 `"__proto__"` 를 `assign` 할 때**까지, 여기는 **JSON 왕복이라는 다섯째 도구가 무엇을 잃나**부터.
- [23 — `Map`·`Set` 과 약한 컬렉션](../23-map-set-and-weak-collections/2-summary.md) — ★ **경계**: 그쪽이 **`Map` 을 JSON 으로 옮기는 법**(`[...map]`·`fromEntries`)의 정본, 여기는 격자의 `{}` 한 행.
- [22 — `Symbol` 과 잘 알려진 심볼](../22-symbol-and-well-known-symbols/2-summary.md) — `JSON.stringify(x)` 가 `toPrimitive` 를 안 부르는 것(`(no call)`).
- [13 — 객체 리터럴과 프로퍼티](../13-object-literals-and-properties/2-summary.md) — 리터럴 `__proto__:` 의 정본 · 정수 키 순서(동작 (1)의 `[3]`).
- [03 — 숫자와 `BigInt`](../03-numbers-and-bigint/2-summary.md) — `-0`·`NaN`·안전 정수(동작 (6)의 20자리 숫자).
- 목록의 **48번 주제**(깊은 복사 수단 비교) — ★ **경계**: 그쪽이 **`structuredClone`·JSON 왕복·스프레드의 선택**의 정본, 여기는 **JSON 왕복의 손실과 비교 열 하나**.
- Python 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **47번**(`json`) — 동작 (7)의 대비. 폴더가 아직 없어 직접 던졌다.

## 용어 풀이

- **직렬화 / 역직렬화** — 값을 글자로 / 글자를 값으로. `stringify` / `parse`.
- **`SerializeJSONProperty`** — 키 하나의 값을 글자로 만드는 명세 연산. `toJSON`·`replacer` 를 부르고, 못 싣는 값에 `undefined` 를 돌려준다.
- **`SerializeJSONObject` / `SerializeJSONArray`** — 객체 / 배열 하나를 글자로 만드는 명세 연산. `undefined` 를 받으면 각각 **건너뛴다 / `"null"` 을 넣는다.**
- **감싸개(wrapper)** — `stringify`·`parse` 가 루트를 `{"": 값}` 에 넣고 시작하는 객체. 그래서 첫 `replacer`·마지막 `reviver` 의 키가 `""` 다.
- **holder** — 지금 직렬화·복원하는 값을 **들고 있는 객체**. `replacer`·`reviver` 의 `this`.
- **`toJSON`** — 직렬화 전에 값을 바꾸는 메서드. `Date` 가 기본으로 갖는다.
- **`replacer`** — `stringify` 의 둘째 인자. 함수면 키마다 불리고, 배열이면 허용 목록.
- **`reviver`** — `parse` 의 둘째 인자. 후위 순서로 키마다 불린다.
- **후위 순회(post-order)** — 자식을 전부 방문한 뒤 부모를 방문하는 순서.
- **순환 참조** — 객체를 따라 내려가다 자기 조상을 다시 만나는 구조.
- **`[[Stack]]`** — `stringify` 가 지금 내려가고 있는 객체들의 목록. 여기에 있는 객체를 또 만나면 순환이다.
- **허용 목록(allow-list)** — 배열 `replacer`. 이 키만 싣는다.
- **`structuredClone`** — HTML 표준의 깊은 복사 함수. ECMA-262 밖이다.
- **`context.source` · `JSON.rawJSON`** — ES2026 의 원문 접근. 원시값의 원래 글자를 읽고 / 그대로 쓴다.

## 더 들어가면

- **JSON superset(ES2019)** — 문자열 안의 U+2028·U+2029 가 JS 문자열 리터럴에서도 허용된 변화. 이 문서는 **돌리지 않았다.**
- **Well-formed `JSON.stringify`(ES2019)** — 짝 없는 서로게이트를 `\ud800` 으로 이스케이프. 판별 블록에 한 줄로만 있다(04번의 주제).
- **JSON 모듈(`import … with { type: "json" }`, ES2025)** — 목록의 **44번 주제**의 몫이다.
