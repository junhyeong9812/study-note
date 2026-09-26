# js/syntax/28 — `String` 메서드와 템플릿 리터럴: 「치환 문자열은 작은 언어다 · 태그는 같은 종이를 받는다 · 자르기 셋은 음수에서 갈린다」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> ★★★ **이 주제의 본체는 ② 전수 격자다.**
> `replace` 의 두 번째 인자는 그냥 문자열이 아니다 — **`$` 로 시작하는 표기를 읽는 작은 언어**다.
> 그 표기 열한 가지를 **네 가지 자리**(문자열 패턴 · 번호 그룹만 있는 정규식 · 명명 그룹이 있는 정규식 · 함수 치환)에 전부 넣어 보고,
> **「표기가 글자 그대로 남지 않은 칸」을 스크립트가 마지막 줄로 센다**(동작 (1)).
> ★★ 나머지 절은 창이 바뀐다 — 태그 템플릿은 **태그 함수가 받은 객체의 동일성**(`===`)으로, `replaceAll` 은 **콜백이 받은 인자 로그**로, 자르기 셋은 **같은 인자 격자**로 본다.
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262 — Text Processing: String Objects](https://tc39.es/ecma262/multipage/text-processing.html#sec-string-objects) —
>   `String.prototype.replace` · `replaceAll` · `split` · `slice` · `substring` · `at` · `padStart`/`padEnd` · `trim` · `includes` · `startsWith` · `String.raw` · 추상 연산 `GetSubstitution` · `IsRegExp`
> - [ECMA-262 — Template Literals](https://tc39.es/ecma262/multipage/ecmascript-language-expressions.html#sec-template-literals) — `GetTemplateObject` · `[[TemplateMap]]` · 태그 템플릿의 `NotEscapeSequence`
> - [ECMA-262 — Annex B](https://tc39.es/ecma262/multipage/additional-ecmascript-features-for-web-browsers.html) — `String.prototype.substr`(부록이다 — 본문 기능이 아니다)
> - [TC39 finished proposals](https://github.com/tc39/proposals/blob/main/finished-proposals.md)(2026-09-26 받아 둔 사본) — 판 경계(String padding 2017 · Lifting template literal restriction 2018 · `trimStart`/`trimEnd` 2019 · `replaceAll` 2021 · `.at()` 2022 · Well-Formed Unicode Strings 2024)
>
> ★★★ **명세 조항 번호는 인용하지 않는다.** 규칙 진술은 **추상 연산 이름**으로, 값·호출 로그·예외 타입과 메시지는 **전부 실행으로** 접지했다.
>
> **실행 검증** — 이 문서의 모든 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮겨 적은 출력이 하나도 없다).
> 배너의 `node20` 은 `~/.nvm/versions/node/v20.19.6/bin/node`, `node18` 은 기본 PATH 의 `node`(v18.19.1)다.
> ★★ **예외는 `try`/`catch` 로 받아 `e.constructor.name` 과 `e.message` 만** `이름 「메시지」` 꼴로 찍었다 — 스택트레이스에는 절대 경로가 박혀 재현이 안 된다.
> ★★ **이 주제의 node 탐침 여섯 개 중 두 판이 갈린 것은 하나**(`js28b-28d-slice-substring.js`)이고, 갈린 줄은 **`isWellFormed`(ES2024) 한 줄**이다 — node 18 에 그 메서드가 없다.
> ★ 파이썬 대비(동작 (7))는 `python3 - <<'PY'` 꼴의 셸 탐침이다. 예외는 같은 꼴(`이름 「메시지」`)로 받아 트레이스백이 없다.
>
> **버전** — 판별 블록이 세 판(node 18 · node 20 · Chrome 151)에 같은 스크립트를 던진다.
>
> | 무엇 | 판 | 이 머신에서 |
> |---|---|---|
> | `slice` · `substring` · `split` · `replace` · `indexOf` · `trim` | ES5 이하 | 세 판 다 있다 |
> | `substr` | **부록 B**(웹 호환용) | 세 판 다 있다 — 명세 본문 기능이 아니다 |
> | 템플릿 리터럴 · 태그 템플릿 · `String.raw` · `includes` · `startsWith` | **ES2015** | 세 판 다 있다 |
> | `padStart` · `padEnd` | **ES2017** | 세 판 다 있다 |
> | 태그 템플릿의 잘못된 이스케이프 허용(`cooked` 가 `undefined`) | **ES2018** | 세 판 다 있다 |
> | `trimStart` · `trimEnd` | **ES2019** | 세 판 다 있다 |
> | `replaceAll` | **ES2021** | 세 판 다 있다 |
> | `at` | **ES2022** | 세 판 다 있다 |
> | `isWellFormed` · `toWellFormed` | **ES2024** | ★ **node 18 에 없다** — 동작 (4)의 한 줄이 갈린다(정본은 [04번](../04-strings-and-utf16/2-summary.md)) |
>
> **★★★ 이 주제가 쓰는 창 — 그리고 부적용인 창**
>
> | 창 | 이 주제에서 무엇을 보나 |
> |---|---|
> | ★★★ **② 전수 격자**(본체) | `$` 표기 **11가지** × 자리 **4가지** — 「표기가 글자 그대로 남지 않은 칸」을 스크립트가 센다(동작 (1)) · 자르기 셋 × 인자 열 벌 — `slice` 와 `substring` 이 **갈린 줄**을 센다(동작 (4)) |
> | ★★ **① 추상 연산에 로그 심기** | `replaceAll` 콜백이 **몇 번 · 무슨 인자로** 불리나(동작 (2)) · 태그 함수가 **무엇을** 받나(동작 (3)) |
> | ★★ **④ 예외의 `constructor.name` + `message`** | `replaceAll` 에 `g` 없는 정규식 · `includes`/`startsWith` 에 정규식 · 태그 없는 템플릿의 잘못된 이스케이프(`SyntaxError`) · 얼린 `strings` 에 쓰기 |
> | ★ **⑤ 두 판 대조기** | 이 주제의 node 탐침 중 **하나만** `DIFFERS` 이고, 그 차이는 **ES2024 메서드의 유무** 한 줄이다 |
> | ★ **부적용 — ③ 브랜드 태그** | 이 주제에서 「이것이 무엇인가」를 태그로 물을 자리가 없다. 태그 함수가 받는 `strings` 는 `Array.isArray` 가 `true` 인 **평범한 배열**이다(동작 (3)) — **잴 것이 없다** |
> | ★ **부적용 — 진단의 `(행,열)`**(18-C) | `SyntaxError` 는 한 번 나오지만(태그 없는 `\unicode`) 그 **위치**가 답을 바꾸는 성질이 아니다. `new Function` 으로 던져 **종류와 문구만** 본다 |
> | ★ **안 쟀다 — 성능** | 「`replaceAll` 이 `split().join()` 보다 빠르다」·「템플릿 리터럴이 `+` 보다 빠르다」를 **한 줄도 쓰지 않는다.** 시간을 한 번도 안 쟀다 |
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 예외 **문구** — V8 의 글자다(`String.prototype.replaceAll called with a non-global RegExp argument` · `Invalid Unicode escape sequence`). 다른 엔진은 다르게 적는다. **종류**(`TypeError`·`SyntaxError`)만 명세가 정한다 | ★★★ 격자의 칸 값과 「**N / M**」 · 콜백 인자의 **개수와 순서** · `===` 의 참/거짓 · 잘린 문자열 · 코드 유닛 16진 값 |
> | 대조기 블록의 **다른 주제 줄**(같은 배치가 한 대조기를 공유한다) | ★★ **이 주제의 탐침에는 재실행에서 흔들린 칸이 하나도 없다**(재대조 동일) |
>
> **선행** — [04 — 문자열과 UTF-16](../04-strings-and-utf16/2-summary.md)(★★★ 직접 선행 — **`length` 는 코드 유닛 수**이고 서로게이트 한 쌍을 가운데서 자르면 **예외 없이 반쪽이 남는다**. 거기서 쟀다) ·
> [22 — `Symbol` 과 잘 알려진 심볼](../22-symbol-and-well-known-symbols/2-summary.md)(★★ **`` `${x}` `` 의 hint 는 `string`**, `x + ''` 는 `default` — 거기서 스물네 연산으로 쟀다) ·
> [02 — 강제 변환과 `==` 대 `===`](../02-coercion-and-loose-equality/2-summary.md)(`ToString` 이 `valueOf`/`toString` 을 고르는 순서).
> **같은 배치** — [29 — 정규식 기본](../29-regexp-basics/2-summary.md) · [30 — 정규식 심화](../30-regexp-advanced/2-summary.md) · [31 — `JSON`](../31-json/2-summary.md).
>
> ★★ **경계 — 정규식의 문법·플래그·`lastIndex` 는 29번이 정본이다.** 여기서는 **`replace`·`split` 이 정규식을 받았을 때 치환 문자열과 결과 배열이 어떻게 되나**까지만 본다.
> ★★ **경계 — 코드 유닛·서로게이트·well-formed 는 04번이 정본이다.** 여기서는 **자르기 메서드가 그 위에서 무엇을 하나**만 한 블록으로 본다.
> ★ **경계 — 템플릿 리터럴의 `${x}` 가 부르는 hint 는 22번이 정본이다.** 여기서는 **태그 템플릿**을 본다.

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

두 node 판 대조기의 집계 줄(이 배치의 모든 node 탐침) — 이 주제의 탐침(`js28b-28?-*.js`) 중 `DIFFERS` 는 `js28b-28d-slice-substring.js` 하나다. 전문은 [3-answer.md](3-answer.md) 의 「실행 검증」에 있다.

`identical 19  ·  differs 6  ·  total 25`

## 한눈에 — 쉽게 말하면

**`replace` 의 두 번째 인자는 「편지 양식」이다.**
양식에 `$&` 라고 적어 두면 **찾은 글자**가, `` $` `` 라고 적어 두면 **그 앞 글자**가 그 자리에 채워진다. 양식을 채우는 사람은 **`$` 로 시작하는 칸만** 본다.
그런데 양식 대신 **「직접 쓴 편지」(함수)** 를 건네면 아무도 칸을 채우지 않는다 — 함수가 돌려준 글자가 **그대로** 들어간다.

- ★★★ **양식은 받는 사람이 누구냐에 따라 채울 수 있는 칸이 다르다.** 패턴이 문자열이면 `$1` 은 채울 게 없어 **글자 그대로** 남는다. 명명 그룹이 있어야 `$<g>` 가 채워진다.
- ★★★ **바깥에서 온 글자를 양식에 넣으면 사고가 난다.** 가격 `"$&0"` 을 양식으로 넣으면 `$&` 가 **찾은 글자**로 바뀐다(동작 (1)의 `[3]`).
- ★★ **태그 템플릿은 「같은 자리에서 뜯은 같은 종이」다.** 소스의 한 자리에 적힌 태그 템플릿은 몇 번을 불려도 **같은 `strings` 객체**를 받는다 — 그리고 그 종이는 **코팅(동결)** 돼 있다.
- ★★ **자르기 셋은 음수에서 갈린다.** `slice` 는 음수를 **뒤에서 센다**, `substring` 은 **0 으로 깎고 인자를 뒤집는다**, `substr` 은 두 번째 인자가 **길이**다.

```text
   "abc".replace(/(?<g>b)/, 양식)                    "abc".replace(/(?<g>b)/, () => 양식)
   ------------------------------                    ------------------------------------
   찾은 것  "b"  at 1                                  찾은 것  "b"  at 1
   양식을 읽는다 (GetSubstitution)                      함수를 부른다 -> 돌려준 값을 ToString
     $&  -> "b"      $`  -> "a"     $'  -> "c"          "$&" 는 그냥 두 글자 '$' '&'
     $1  -> "b"      $<g> -> "b"    $$  -> "$"
     $9  -> 그룹 9 가 없다 -> 글자 그대로 "$9"
   결과  "a" + 채운 양식 + "c"                         결과  "a" + 돌려준 글자 + "c"
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 편지 양식 | 치환 **문자열** — `GetSubstitution` 이 `$` 표기를 읽는다 | 동작 (1)의 앞 세 열 |
| 직접 쓴 편지 | 치환 **함수** — 돌려준 값을 `ToString` 만 한다 | 동작 (1)의 넷째 열 |
| 채울 게 없는 칸 | 없는 그룹 번호 · 명명 그룹이 없는데 `$<…>` | `$9` · `$0` · 문자열 패턴의 `$1` |
| 같은 자리에서 뜯은 종이 | `GetTemplateObject` — 소스 자리마다 **한 번** 만들어 캐시 | 동작 (3)의 `site() === site()` |
| 코팅 | `strings` 와 `strings.raw` 가 **동결** | 동작 (3)의 `Object.isFrozen` · 쓰기의 `TypeError` |
| 뒤에서 센다 / 0 으로 깎는다 | `slice` 의 음수 = `길이 + n` · `substring` 의 음수 = `0` | 동작 (4)의 `(-2)` 줄 |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.
「**사용자가 입력한 문자열을 `replace` 의 두 번째 인자로 넣었더니 `$&`·`` $` `` 가 섞인 입력에서 글자가 바뀌었다**」와
「**모든 자리를 바꾸려고 `replace('-', '+')` 를 썼는데 첫 자리만 바뀌었다**」가 그것이다(동작 (1)·(2)). 둘 다 예외가 안 난다.

> **치환 문자열(replacement string)** — `replace`·`replaceAll` 의 두 번째 인자로 준 문자열. `$` 로 시작하는 표기를 명세 연산 `GetSubstitution` 이 읽어 채운다.\
> 예: `"abc".replace("b", "[$&]")` 가 `"a[b]c"`.

> **태그 템플릿(tagged template)** — 템플릿 리터럴 앞에 함수 이름을 붙인 호출식. 함수는 **글자 조각 배열**과 **`${}` 의 값들**을 따로 받는다.\
> 예: ``tag`a${1}b` `` 에서 `tag` 는 `(["a","b"], 1)` 을 받는다.

## 이 주제가 답하려는 질문

1. **`replace` 의 치환 문자열에서 `$` 표기는 언제 읽히고 언제 글자 그대로 남나** — 패턴이 문자열일 때 · 정규식일 때 · 명명 그룹이 있을 때 · 함수를 넘겼을 때.
2. **태그 함수가 받는 `strings` 는 어떤 객체인가** — 부를 때마다 새로 만드나, 고칠 수 있나, 잘못된 이스케이프는 어떻게 받나?
3. **자르기·찾기 메서드는 경계 인자(음수·뒤집힌 범위·빈 문자열·정규식)를 어떻게 다루나** — 예외 없이 무엇을 돌려주나?

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 출력으로 읽는다.

### (1) ★★★ `$` 치환 격자 — 이 주제의 본체

**언제 쓰나** — `replace`·`replaceAll` 로 **찾은 글자를 살려서** 바꿀 때(`"[$&]"`) · 캡처한 조각을 **재배치**할 때(`"$2-$1"`) · 그리고 **바깥에서 온 문자열**을 두 번째 인자로 넣을 때.
★★★ 두 번째 인자가 **문자열이면 표기를 읽고, 함수면 안 읽는다.** 그 규칙을 칸 44개로 전부 찍었다.

```text
   치환 문자열 "[$1]" 이 어떻게 읽히나 -- 패턴이 무엇이냐에 따라

   패턴                 캡처 목록         명명 캡처        "$1" 은        "$<g>" 는
   ------------------   --------------   -------------   ------------   ---------------
   "b"   (문자열)        없음 (0개)        없음(undefined)  그룹 1 없음     명명 캡처 없음
                                                          -> "$1"        -> "$<g>"
   /(b)/                ["b"]  (1개)      없음(undefined)  -> "b"         명명 캡처 없음
                                                                         -> "$<g>"
   /(?<g>b)/            ["b"]  (1개)      { g: "b" }      -> "b"         -> "b"
                                                                         ($<x> 는 "" -- 이름이 없으면 빈 글자)
   /(?<g>b)/ + 함수      (함수가 받는다)    (함수가 받는다)    읽지 않는다     읽지 않는다
```

```js
// js28b-28a-dollar-grid.js
// String.prototype.replace -- how the replacement string is read, in four settings.
// Input "abc", the part being replaced is "b". The script prints every cell, then counts.
const J = (x) => JSON.stringify(x);
const templates = ["[$&]", "[$`]", "[$']", "[$$]", "[$1]", "[$01]", "[$10]", "[$9]", "[$0]", "[$<g>]", "[$<x>]"];
const settings = [
  ["string pattern", (t) => "abc".replace("b", t)],
  ["/(b)/", (t) => "abc".replace(/(b)/, t)],
  ["/(?<g>b)/", (t) => "abc".replace(/(?<g>b)/, t)],
  ["/(?<g>b)/ + fn", (t) => "abc".replace(/(?<g>b)/, () => t)],
];

console.log("[1] replacement  " + settings.map(([n]) => n.padEnd(17)).join("").trimEnd());
let changed = 0, total = 0;
for (const t of templates) {
  const literal = "a" + t + "c";
  const cells = settings.map(([, f]) => f(t));
  for (const c of cells) { total += 1; if (c !== literal) changed += 1; }
  console.log(("    " + t.padEnd(13) + cells.map((c) => J(c).padEnd(17)).join("")).trimEnd());
}

console.log("");
console.log("[2] the same template through replaceAll and split-join");
console.log("    'a.b.c'.replaceAll('.', '$&$&')     " + J("a.b.c".replaceAll(".", "$&$&")));
console.log("    'a.b.c'.split('.').join('$&$&')     " + J("a.b.c".split(".").join("$&$&")));

console.log("");
console.log("[3] a replacement that comes from outside -- a price string");
const price = "$5";
console.log("    'cost: X'.replace('X', price)        " + J("cost: X".replace("X", price)));
const price2 = "$&0";
console.log("    'cost: X'.replace('X', '$&0')        " + J("cost: X".replace("X", price2)));
console.log("    'cost: X'.replace('X', () => '$&0')  " + J("cost: X".replace("X", () => price2)));

console.log("");
console.log("cells where the output differs from the plain text of the template: " + changed + " / " + total);
```
```text
===== node20 js28b-28a-dollar-grid.js (exit=0) =====
[1] replacement  string pattern   /(b)/            /(?<g>b)/        /(?<g>b)/ + fn
    [$&]         "a[b]c"          "a[b]c"          "a[b]c"          "a[$&]c"
    [$`]         "a[a]c"          "a[a]c"          "a[a]c"          "a[$`]c"
    [$']         "a[c]c"          "a[c]c"          "a[c]c"          "a[$']c"
    [$$]         "a[$]c"          "a[$]c"          "a[$]c"          "a[$$]c"
    [$1]         "a[$1]c"         "a[b]c"          "a[b]c"          "a[$1]c"
    [$01]        "a[$01]c"        "a[b]c"          "a[b]c"          "a[$01]c"
    [$10]        "a[$10]c"        "a[b0]c"         "a[b0]c"         "a[$10]c"
    [$9]         "a[$9]c"         "a[$9]c"         "a[$9]c"         "a[$9]c"
    [$0]         "a[$0]c"         "a[$0]c"         "a[$0]c"         "a[$0]c"
    [$<g>]       "a[$<g>]c"       "a[$<g>]c"       "a[b]c"          "a[$<g>]c"
    [$<x>]       "a[$<x>]c"       "a[$<x>]c"       "a[]c"           "a[$<x>]c"

[2] the same template through replaceAll and split-join
    'a.b.c'.replaceAll('.', '$&$&')     "a..b..c"
    'a.b.c'.split('.').join('$&$&')     "a$&$&b$&$&c"

[3] a replacement that comes from outside -- a price string
    'cost: X'.replace('X', price)        "cost: $5"
    'cost: X'.replace('X', '$&0')        "cost: X0"
    'cost: X'.replace('X', () => '$&0')  "cost: $&0"

cells where the output differs from the plain text of the template: 20 / 44
```

```text
   두 자리 숫자 "$10" 은 어떻게 읽히나 -- 그룹이 1개뿐일 때

   "$10"   ->  두 자리 "10" 번 그룹이 있나?   없다 (그룹은 1개)
           ->  한 자리 "1" 번 그룹이 있나?    있다 -> "b" + 남은 글자 "0"   => "b0"
   "$01"   ->  두 자리 "01" = 1 번 그룹       있다 -> "b"                 => "b"
   "$9"    ->  두 자리 "9?" 아님, 한 자리 9 번  없다 -> 글자 그대로          => "$9"
   "$0"    ->  0 번은 그룹 번호가 아니다                  -> 글자 그대로          => "$0"
```

- ★★★ **마지막 줄이 `20 / 44`** 다. 44칸 중 20칸에서 표기가 **다른 글자로 바뀌었고**, 24칸은 **글자 그대로** 남았다.
- ★★★ **넷째 열(함수)은 11줄 전부 글자 그대로**다 — `"a[$&]c"` · `"a[$$]c"` 까지. 함수가 돌려준 값은 **`ToString` 만** 거치고 `GetSubstitution` 을 안 거친다.
- ★★★ **`$&`·`` $` ``·`$'`·`$$` 넷은 앞 세 열에서 같다** — 패턴이 문자열이어도 읽힌다. 이 넷은 **캡처가 없어도 뜻이 있는 표기**다(찾은 것 · 앞 · 뒤 · `$` 자신).
- ★★★ **`$1`·`$01`·`$10` 은 문자열 패턴에서 글자 그대로**다. 문자열 패턴에는 캡처가 없다.
  정규식에 그룹이 **하나**일 때 `$10` 은 `"b0"` — **두 자리를 먼저 보고, 그 번호의 그룹이 없으면 한 자리**로 읽는다(위 그림).
- ★★ **`$9`·`$0` 은 세 열 다 글자 그대로**다 — 없는 그룹 번호는 **예외도 빈 글자도 아니고 그대로 남는다.**
- ★★★ **`$<g>` 는 명명 그룹이 있는 셋째 열에서만 `"b"`** 이고, **`$<x>`(없는 이름)는 셋째 열에서 빈 글자 `"a[]c"`** 다.
  명명 그룹이 **하나라도 있으면** `$<…>` 를 이름으로 찾고, 없는 이름은 `undefined` → **빈 글자**다. 명명 그룹이 **아예 없으면** 글자 그대로다.
- ★★ **`[2]`** — `replaceAll` 도 같은 양식을 읽는다(`"a..b..c"`). `split().join()` 은 **양식을 안 읽는다**(`"a$&$&b$&$&c"`) — `join` 은 치환 문자열이 아니다.
- ★★★ **`[3]` 바깥에서 온 문자열** — `"$5"` 는 그룹 5 가 없어서 **우연히** 그대로 남았다(`"cost: $5"`). `"$&0"` 은 **`"cost: X0"`** — `$&` 가 찾은 글자 `X` 로 바뀌었다.
  **함수로 감싸면**(`() => price2`) 그대로 `"cost: $&0"` 다. 바깥 문자열은 **함수로 넘긴다.**

### (2) ★★★ `replace` 와 `replaceAll` — 몇 곳을 바꾸나, 무엇을 거절하나

**언제 쓰나** — 문자열 안의 **모든** 구분자를 바꿀 때. ES2021 전에는 `split(x).join(y)` 나 `/x/g` 가 관용구였다.

```text
   "a-b-c" 에서 "-" 를 "+" 로

   replace("-", "+")        첫 자리 하나      a + b - c   -> "a+b-c"
   replace(/-/, "+")        첫 자리 하나      a + b - c   -> "a+b-c"
   replace(/-/g, "+")       전부              a + b + c   -> "a+b+c"
   replaceAll("-", "+")     전부              a + b + c   -> "a+b+c"
   replaceAll(/-/g, "+")    전부              a + b + c   -> "a+b+c"
   replaceAll(/-/, "+")     g 가 없다          TypeError (아무것도 안 바꾼다)
```

```js
// js28b-28b-replace-all.js
// replace and replaceAll -- how many places, and what each accepts as the pattern.
const J = (x) => JSON.stringify(x);
const show = (label, f) => {
  try { console.log("  " + label.padEnd(38) + J(f())); }
  catch (e) { console.log("  " + label.padEnd(38) + e.constructor.name + " 「" + e.message + "」"); }
};

console.log("[1] a string pattern");
show("'a-b-c'.replace('-', '+')", () => "a-b-c".replace("-", "+"));
show("'a-b-c'.replaceAll('-', '+')", () => "a-b-c".replaceAll("-", "+"));
show("'a-b-c'.split('-').join('+')", () => "a-b-c".split("-").join("+"));

console.log("");
console.log("[2] a regexp pattern, with and without g");
show("'a-b-c'.replace(/-/, '+')", () => "a-b-c".replace(/-/, "+"));
show("'a-b-c'.replace(/-/g, '+')", () => "a-b-c".replace(/-/g, "+"));
show("'a-b-c'.replaceAll(/-/g, '+')", () => "a-b-c".replaceAll(/-/g, "+"));
show("'a-b-c'.replaceAll(/-/, '+')", () => "a-b-c".replaceAll(/-/, "+"));

console.log("");
console.log("[3] the empty string as the pattern");
show("'abc'.replace('', '-')", () => "abc".replace("", "-"));
show("'abc'.replaceAll('', '-')", () => "abc".replaceAll("", "-"));

console.log("");
console.log("[4] overlapping candidates -- 'aaa' with 'aa'");
show("'aaa'.replaceAll('aa', 'X')", () => "aaa".replaceAll("aa", "X"));
show("'aaa'.split('aa')", () => "aaa".split("aa"));

console.log("");
console.log("[5] what the replacer function receives for a string pattern");
const calls = [];
"x-y-z".replaceAll("-", (...args) => { calls.push(args); return "+"; });
show("calls", () => calls);

console.log("");
console.log("[6] the pattern is not a string or a regexp");
show("'a1b1'.replaceAll(1, '_')", () => "a1b1".replaceAll(1, "_"));
show("'anullb'.replace(null, '_')", () => "anullb".replace(null, "_"));
show("'a.b'.replaceAll('.', undefined)", () => "a.b".replaceAll(".", undefined));
```
```text
===== node20 js28b-28b-replace-all.js (exit=0) =====
[1] a string pattern
  'a-b-c'.replace('-', '+')             "a+b-c"
  'a-b-c'.replaceAll('-', '+')          "a+b+c"
  'a-b-c'.split('-').join('+')          "a+b+c"

[2] a regexp pattern, with and without g
  'a-b-c'.replace(/-/, '+')             "a+b-c"
  'a-b-c'.replace(/-/g, '+')            "a+b+c"
  'a-b-c'.replaceAll(/-/g, '+')         "a+b+c"
  'a-b-c'.replaceAll(/-/, '+')          TypeError 「String.prototype.replaceAll called with a non-global RegExp argument」

[3] the empty string as the pattern
  'abc'.replace('', '-')                "-abc"
  'abc'.replaceAll('', '-')             "-a-b-c-"

[4] overlapping candidates -- 'aaa' with 'aa'
  'aaa'.replaceAll('aa', 'X')           "Xa"
  'aaa'.split('aa')                     ["","a"]

[5] what the replacer function receives for a string pattern
  calls                                 [["-",1,"x-y-z"],["-",3,"x-y-z"]]

[6] the pattern is not a string or a regexp
  'a1b1'.replaceAll(1, '_')             "a_b_"
  'anullb'.replace(null, '_')           "a_b"
  'a.b'.replaceAll('.', undefined)      "aundefinedb"
```

- ★★★ **`replace` 는 문자열 패턴이면 첫 자리 하나**다(`"a+b-c"`). 정규식이어도 **`g` 가 없으면** 하나다.
- ★★★ **`replaceAll(/-/, '+')` 는 `TypeError 「String.prototype.replaceAll called with a non-global RegExp argument」`** 다.
  `replaceAll` 은 정규식이 오면 **`flags` 에 `g` 가 있는지 먼저 묻고** 없으면 던진다 — 아무 자리도 바꾸기 전이다.
- ★★ **`[3]` 빈 패턴** — `replace('', '-')` 는 **맨 앞 한 곳**(`"-abc"`), `replaceAll('', '-')` 는 **글자 사이사이와 양 끝 네 곳**(`"-a-b-c-"`)이다.
- ★★ **`[4]` 겹치는 후보** — `'aaa'.replaceAll('aa', 'X')` 는 `"Xa"` 다. **찾은 뒤 그 길이만큼 건너뛰고** 다음을 찾는다 — 겹친 자리는 안 본다. `split` 도 같다(`["","a"]`).
- ★★ **`[5]` 문자열 패턴의 콜백은 인자 셋**이다 — `["-",1,"x-y-z"]`(찾은 글자 · 위치 · 원본). 캡처가 없으니 그 사이에 끼는 것이 없다. 정규식의 콜백 인자는 29번이 정본이다.
- ★ **`[6]`** — 패턴이 문자열도 정규식도 아니면 **`ToString`** 한다(`1` → `"1"`, `null` → `"null"`). 치환 인자가 `undefined` 면 글자 `"undefined"` 가 들어간다.

### (3) ★★★ 태그 템플릿 — 태그가 받는 것, 그리고 같은 객체인가

**언제 쓰나** — SQL·HTML 을 **안전하게 조립**하는 태그(`` sql`…` `` 꼴) · 국제화 태그 · `String.raw` 로 **백슬래시를 살린** 경로·정규식 문자열을 쓸 때.

```text
   keep`a${1}b${"two"}c`

   소스 글자     a  ${1}  b  ${"two"}  c
                 │   │    │    │       │
   strings    [ "a",    "b",         "c" ]      <- 조각 3개 (항상 값 개수 + 1)
   subs            [ 1,      "two" ]             <- 값 2개
   strings.raw [ "a",    "b",         "c" ]      <- 이스케이프를 풀기 전 글자

   이 배열은 이 소스 자리 하나에 한 번 만들어진다 --
     같은 자리를 다시 지나가면 (함수를 또 부르면, 루프를 또 돌면)  같은 객체
     글자가 같아도 다른 자리에 적혀 있으면                          다른 객체
```

```js
// js28b-28c-tagged.js
// Tagged templates -- what the tag function receives, and whether it is the same object each time.
const J = (x) => JSON.stringify(x);
const show = (label, f) => {
  try { console.log("  " + label.padEnd(48) + f()); }
  catch (e) { console.log("  " + label.padEnd(48) + e.constructor.name + " 「" + e.message + "」"); }
};
const keep = (strings, ...subs) => ({ strings, subs });
const T = (v) => (typeof v === "string" ? "[" + v + "]" : String(v));   // text in brackets, no JSON escaping

console.log("[1] what the tag receives");
const r = keep`a${1}b${"two"}c`;
show("strings", () => J(r.strings));
show("strings.raw", () => J(r.strings.raw));
show("subs", () => J(r.subs));
show("strings.length vs subs.length", () => r.strings.length + " vs " + r.subs.length);
show("Array.isArray(strings)", () => Array.isArray(r.strings));
show("Object.isFrozen(strings)", () => Object.isFrozen(r.strings));
show("Object.isFrozen(strings.raw)", () => Object.isFrozen(r.strings.raw));
show("keep`${1}`.strings", () => J(keep`${1}`.strings));

console.log("");
console.log("[2] the strings object across calls");
const site = () => keep`same ${0} text`.strings;
show("site() === site()", () => site() === site());
const other = () => keep`same ${0} text`.strings;
show("site() === other()   (same text, other place)", () => site() === other());
const seen = [];
for (let i = 0; i < 3; i++) seen.push(keep`loop ${i}`.strings);
show("three loop turns, same object?", () => seen[0] === seen[1] && seen[1] === seen[2]);
const viaFn = () => new Function("keep", "return keep`same ${0} text`.strings")(keep);
show("new Function each time: equal?", () => viaFn() === viaFn());
show("writing strings[0]", () => { "use strict"; const s = site(); s[0] = "changed"; return J(s[0]); });

console.log("");
console.log("[3] String.raw");
show("String.raw`a\\nb`.length", () => String.raw`a\nb`.length);
show("`a\\nb`.length", () => `a\nb`.length);
show("String.raw`C:\\dir\\${'x'}`", () => T(String.raw`C:\dir\${"x"}`));
show("String.raw({ raw: ['x', 'y', 'z'] }, 1, 2, 3)", () => T(String.raw({ raw: ["x", "y", "z"] }, 1, 2, 3)));
show("String.raw({ raw: 'abc' }, '-', '-')", () => T(String.raw({ raw: "abc" }, "-", "-")));

console.log("");
console.log("[4] an escape that is not a valid escape");
const bad = "\\" + "unicode and \\" + "xZ";
show("tag receives -- cooked", () => T(new Function("keep", "return keep`" + bad + "`.strings[0]")(keep)));
show("tag receives -- raw", () => T(new Function("keep", "return keep`" + bad + "`.strings.raw[0]")(keep)));
show("the same text without a tag", () => T(new Function("return `" + bad + "`")()));
show("String.raw with it", () => T(new Function("return String.raw`" + bad + "`")()));
```
```text
===== node20 js28b-28c-tagged.js (exit=0) =====
[1] what the tag receives
  strings                                         ["a","b","c"]
  strings.raw                                     ["a","b","c"]
  subs                                            [1,"two"]
  strings.length vs subs.length                   3 vs 2
  Array.isArray(strings)                          true
  Object.isFrozen(strings)                        true
  Object.isFrozen(strings.raw)                    true
  keep`${1}`.strings                              ["",""]

[2] the strings object across calls
  site() === site()                               true
  site() === other()   (same text, other place)   false
  three loop turns, same object?                  true
  new Function each time: equal?                  false
  writing strings[0]                              TypeError 「Cannot assign to read only property '0' of object '[object Array]'」

[3] String.raw
  String.raw`a\nb`.length                         4
  `a\nb`.length                                   3
  String.raw`C:\dir\${'x'}`                       [C:\dir\${"x"}]
  String.raw({ raw: ['x', 'y', 'z'] }, 1, 2, 3)   [x1y2z]
  String.raw({ raw: 'abc' }, '-', '-')            [a-b-c]

[4] an escape that is not a valid escape
  tag receives -- cooked                          undefined
  tag receives -- raw                             [\unicode and \xZ]
  the same text without a tag                     SyntaxError 「Invalid Unicode escape sequence」
  String.raw with it                              [\unicode and \xZ]
```

- ★★★ **`strings` 는 조각 3개, `subs` 는 값 2개**다(`3 vs 2`). `${}` 로 시작·끝나도 빈 조각이 생긴다 — ``keep`${1}` `` 의 `strings` 는 `["",""]`.
- ★★★ **`site() === site()` 가 `true`** 다. 태그 함수가 받는 배열은 **그 소스 자리에 딱 하나** 있다 — 함수를 두 번 불러도, 루프를 세 번 돌아도(`three loop turns, same object? true`) **같은 객체**다.
  ★★ **글자가 같아도 자리가 다르면 `false`**(`site() === other()`). `new Function` 은 **부를 때마다 새 소스를 파싱**하므로 자리도 매번 새것이다(`false`).
- ★★★ **`strings` 도 `strings.raw` 도 동결**돼 있다(`Object.isFrozen` 둘 다 `true`). 엄격 코드에서 `s[0] = …` 는 **`TypeError 「Cannot assign to read only property '0' of object '[object Array]'」`** 다.
  캐시해서 모두가 같은 객체를 받으니, 얼려 두지 않으면 **한 호출이 고친 것을 다음 호출이 받는다**(설계 이유는 명세 문장이 아니라 내 추론이다).
- ★★ **`Array.isArray(strings)` 는 `true`** — 특수한 객체가 아니라 **얼린 평범한 배열**에 `raw` 프로퍼티를 단 것이다.
- ★★★ **`[3]` `String.raw`** — ``String.raw`a\nb` `` 는 **4 글자**(`\` 와 `n` 이 따로), 그냥 템플릿은 **3 글자**(줄바꿈 하나).
  ★ ``String.raw`C:\dir\${"x"}` `` 는 **`${` 가 치환이 안 됐다** — `\$` 가 `$` 를 이스케이프해서 `${"x"}` 가 **글자**로 남았다. 경로 끝의 백슬래시는 `String.raw` 로도 못 쓴다.
  ★ `String.raw({ raw: … }, …)` 로 **함수처럼** 부를 수 있다 — `raw` 가 문자열 `"abc"` 여도 글자마다 조각으로 읽는다(`[a-b-c]`).
- ★★★ **`[4]` 잘못된 이스케이프** — 태그 템플릿에서는 `\unicode`·`\xZ` 가 **문법 오류가 아니다.** 태그는 **`cooked` 칸에 `undefined`** 를, **`raw` 칸에 원래 글자**를 받는다.
  **태그가 없으면 `SyntaxError 「Invalid Unicode escape sequence」`** 다. ES2018 의 「Lifting template literal restriction」이 **태그 템플릿에서만** 제한을 풀었다 — 태그는 `raw` 를 읽으면 되니 `cooked` 를 못 만들어도 쓸모가 있다.

```text
   `\unicode`   (태그 없음)       ->  cooked 를 만들어야 한다  ->  만들 수 없다  ->  SyntaxError (파싱 때)
   tag`\unicode`                 ->  cooked = undefined         raw = "\unicode"  ->  tag 가 알아서 고른다
```

### (4) ★★★ 자르기 셋과 `at` — 같은 인자, 다른 규칙

**언제 쓰나** — 문자열의 앞뒤를 잘라 낼 때. 세 메서드의 **음수·뒤집힌 인자 규칙이 다르다.**

```text
   "abcdef"      a   b   c   d   e   f
   인덱스         0   1   2   3   4   5   (6)
   음수 slice    -6  -5  -4  -3  -2  -1

   slice(2, -1)      -1 -> 6 + (-1) = 5        [2, 5)  -> "cde"
   substring(2, -1)  -1 -> 0 으로 깎는다        [2, 0) -> 뒤집는다 [0, 2) -> "ab"
   substr(2, -1)     두 번째 인자는 길이 -1 -> 0  길이 0  -> ""
```

```js
// js28b-28d-slice-substring.js
// slice / substring / substr on the same string and the same arguments. The script counts the cells.
const s = "abcdef";
const J = (x) => (x === undefined ? "undefined" : JSON.stringify(x));
const args = [[2], [-2], [2, 4], [4, 2], [-3, -1], [2, -1], [-1, 2], [NaN, 3], [undefined, 3], [2, 100]];
const fmt = (a) => "(" + a.map((v) => (v === undefined ? "undefined" : String(v))).join(", ") + ")";

console.log("[1] 'abcdef' -- slice / substring / substr");
console.log("  args            slice      substring  substr");
let differ = 0;
for (const a of args) {
  const sl = s.slice(...a), su = s.substring(...a), sb = s.substr(...a);
  if (sl !== su) differ += 1;
  console.log("  " + fmt(a).padEnd(16) + J(sl).padEnd(11) + J(su).padEnd(11) + J(sb));
}

console.log("");
console.log("[2] at and bracket access");
for (const i of [0, 5, 6, -1, -6, -7, 1.7, "1"]) {
  console.log("  " + ("i = " + J(i)).padEnd(12) + "at " + J(s.at(i)).padEnd(12) + "s[i] " + J(s[i]));
}

console.log("");
console.log("[3] the same calls on a string with a code point outside the BMP (built with fromCodePoint)");
const e = "a" + String.fromCodePoint(0x1F600) + "b";
const hex = (t) => [...Array(t.length).keys()].map((i) => t.charCodeAt(i).toString(16)).join(" ");
console.log("  length " + e.length + "   code units " + hex(e));
console.log("  slice(0, 2)  code units " + hex(e.slice(0, 2)) + "   isWellFormed " + (typeof e.isWellFormed === "function" ? e.slice(0, 2).isWellFormed() : "(no method)"));
console.log("  at(1)        code units " + hex(e.at(1)));
console.log("  at(-2)       code units " + hex(e.at(-2)));

console.log("");
console.log("rows where slice and substring disagree: " + differ + " / " + args.length);
```
```text
===== node20 js28b-28d-slice-substring.js (exit=0) =====
[1] 'abcdef' -- slice / substring / substr
  args            slice      substring  substr
  (2)             "cdef"     "cdef"     "cdef"
  (-2)            "ef"       "abcdef"   "ef"
  (2, 4)          "cd"       "cd"       "cdef"
  (4, 2)          ""         "cd"       "ef"
  (-3, -1)        "de"       ""         ""
  (2, -1)         "cde"      "ab"       ""
  (-1, 2)         ""         "ab"       "f"
  (NaN, 3)        "abc"      "abc"      "abc"
  (undefined, 3)  "abc"      "abc"      "abc"
  (2, 100)        "cdef"     "cdef"     "cdef"

[2] at and bracket access
  i = 0       at "a"         s[i] "a"
  i = 5       at "f"         s[i] "f"
  i = 6       at undefined   s[i] undefined
  i = -1      at "f"         s[i] undefined
  i = -6      at "a"         s[i] undefined
  i = -7      at undefined   s[i] undefined
  i = 1.7     at "b"         s[i] undefined
  i = "1"     at "b"         s[i] "b"

[3] the same calls on a string with a code point outside the BMP (built with fromCodePoint)
  length 4   code units 61 d83d de00 62
  slice(0, 2)  code units 61 d83d   isWellFormed false
  at(1)        code units d83d
  at(-2)       code units de00

rows where slice and substring disagree: 5 / 10
```

- ★★★ **마지막 줄이 `5 / 10`** — 인자 열 벌 중 다섯 벌에서 `slice` 와 `substring` 이 갈렸다. 갈린 줄은 **전부 음수가 있거나 앞 인자가 더 큰 줄**이다.
- ★★★ **`(-2)`** — `slice` 는 `"ef"`(뒤에서 둘), `substring` 은 **`"abcdef"`**(음수가 0 이 되어 처음부터).
- ★★★ **`(4, 2)`** — `slice` 는 **빈 글자**(시작이 끝보다 뒤면 빈 것), `substring` 은 **`"cd"`**(작은 쪽을 앞으로 뒤집는다).
- ★★ **`substr` 의 두 번째 인자는 길이**다 — `(2, 4)` 가 `"cdef"`(2부터 4글자). 부록 B 의 함수라 새 코드에는 쓰지 않는다.
- ★★ **`NaN`·`undefined` 시작은 셋 다 `0`** 이다(`"abc"`). 끝이 길이를 넘으면 셋 다 **길이에서 멈춘다**(`(2, 100)` → `"cdef"`) — 예외가 없다.
- ★★★ **`[2]` `at` 과 대괄호** — `at(-1)` 은 `"f"`, **`s[-1]` 은 `undefined`** 다. 대괄호는 **`"-1"` 이라는 이름의 프로퍼티**를 찾는다(없다).
  ★ `at(1.7)` 은 `"b"`(정수로 깎는다), **`s[1.7]` 은 `undefined`**(`"1.7"` 이라는 이름) · `s["1"]` 은 `"b"`. 범위를 벗어나면 `at` 도 `undefined` 다(`at(6)`·`at(-7)`).
- ★★ **`[3]` BMP 밖 글자** — `String.fromCodePoint(0x1F600)` 을 끼운 `"a…b"` 는 **길이 4**, 코드 유닛 `61 d83d de00 62`.
  `slice(0, 2)` 는 **`61 d83d`**(반쪽에서 잘렸다) · `at(1)` 은 **`d83d`**, `at(-2)` 는 **`de00`** — **`at` 도 코드 유닛 단위**다.
  ★★ 이 줄의 `isWellFormed` 만 **node 18 에서 `(no method)`** 이다(아래 블록) — ES2024 메서드가 없다. 반쪽이 남는다는 사실 자체와 well-formed 판정은 [04번](../04-strings-and-utf16/2-summary.md)이 정본이다.

```text
===== node18 js28b-28d-slice-substring.js (exit=0) =====
[1] 'abcdef' -- slice / substring / substr
  args            slice      substring  substr
  (2)             "cdef"     "cdef"     "cdef"
  (-2)            "ef"       "abcdef"   "ef"
  (2, 4)          "cd"       "cd"       "cdef"
  (4, 2)          ""         "cd"       "ef"
  (-3, -1)        "de"       ""         ""
  (2, -1)         "cde"      "ab"       ""
  (-1, 2)         ""         "ab"       "f"
  (NaN, 3)        "abc"      "abc"      "abc"
  (undefined, 3)  "abc"      "abc"      "abc"
  (2, 100)        "cdef"     "cdef"     "cdef"

[2] at and bracket access
  i = 0       at "a"         s[i] "a"
  i = 5       at "f"         s[i] "f"
  i = 6       at undefined   s[i] undefined
  i = -1      at "f"         s[i] undefined
  i = -6      at "a"         s[i] undefined
  i = -7      at undefined   s[i] undefined
  i = 1.7     at "b"         s[i] undefined
  i = "1"     at "b"         s[i] "b"

[3] the same calls on a string with a code point outside the BMP (built with fromCodePoint)
  length 4   code units 61 d83d de00 62
  slice(0, 2)  code units 61 d83d   isWellFormed (no method)
  at(1)        code units d83d
  at(-2)       code units de00

rows where slice and substring disagree: 5 / 10
```

### (5) ★★ `split` — 정규식 구분자와 캡처 그룹

**언제 쓰나** — 구분자로 나누되 **구분자 자체도 남기고** 싶을 때(토크나이저) · 여러 종류의 구분자로 나눌 때.

```text
   "a1b22c".split(/(\d)/)

   a  1  b  2  (빈)  2  c
   │  ↑  │  ↑   │   ↑  │
   │  캡처 │  캡처  │  캡처 │        <- 캡처 그룹이 잡은 것이 결과 배열 사이에 끼어든다
   ▼     ▼      ▼      ▼
   ["a", "1", "b", "2", "", "2", "c"]      두 "2" 사이는 빈 글자

   "a1b-c".split(/(\d)|(-)/)   -- 그룹이 둘, 매번 하나만 참여
   ["a", "1", undefined, "b", undefined, "-", "c"]     참여 안 한 그룹 자리는 undefined
```

```js
// js28b-28e-split.js
// split -- a string separator, a regexp separator, and a regexp with capture groups.
const J = (x) => JSON.stringify(x, (k, v) => (v === undefined ? "<undefined>" : v));
const show = (label, f) => {
  try { console.log("  " + label.padEnd(36) + J(f())); }
  catch (e) { console.log("  " + label.padEnd(36) + e.constructor.name + " 「" + e.message + "」"); }
};

console.log("[1] separators");
show("'a1b22c'.split('2')", () => "a1b22c".split("2"));
show("'a1b22c'.split(/\\d/)", () => "a1b22c".split(/\d/));
show("'a1b22c'.split(/\\d+/)", () => "a1b22c".split(/\d+/));
show("'a1b22c'.split(/(\\d)/)", () => "a1b22c".split(/(\d)/));
show("'a1b22c'.split(/(\\d)+/)", () => "a1b22c".split(/(\d)+/));
show("'a1b-c'.split(/(\\d)|(-)/)", () => "a1b-c".split(/(\d)|(-)/));
show("'a1b-c'.split(/(?:\\d|-)/)", () => "a1b-c".split(/(?:\d|-)/));

console.log("");
console.log("[2] ends, empties and limits");
show("',a,,b,'.split(',')", () => ",a,,b,".split(","));
show("''.split(',')", () => "".split(","));
show("''.split('')", () => "".split(""));
show("'abc'.split('')", () => "abc".split(""));
show("'abc'.split()", () => "abc".split());
show("'a,b,c'.split(',', 2)", () => "a,b,c".split(",", 2));
show("'a1b2c'.split(/(\\d)/, 2)", () => "a1b2c".split(/(\d)/, 2));
show("'abc'.split(/(?:)/)", () => "abc".split(/(?:)/));

console.log("");
console.log("[3] does split look at lastIndex or the g flag?");
const g = /,/g;
g.lastIndex = 3;
show("'a,b,c'.split(/,/g)  lastIndex=3", () => "a,b,c".split(g));
show("  g.lastIndex afterwards", () => g.lastIndex);
```
```text
===== node20 js28b-28e-split.js (exit=0) =====
[1] separators
  'a1b22c'.split('2')                 ["a1b","","c"]
  'a1b22c'.split(/\d/)                ["a","b","","c"]
  'a1b22c'.split(/\d+/)               ["a","b","c"]
  'a1b22c'.split(/(\d)/)              ["a","1","b","2","","2","c"]
  'a1b22c'.split(/(\d)+/)             ["a","1","b","2","c"]
  'a1b-c'.split(/(\d)|(-)/)           ["a","1","<undefined>","b","<undefined>","-","c"]
  'a1b-c'.split(/(?:\d|-)/)           ["a","b","c"]

[2] ends, empties and limits
  ',a,,b,'.split(',')                 ["","a","","b",""]
  ''.split(',')                       [""]
  ''.split('')                        []
  'abc'.split('')                     ["a","b","c"]
  'abc'.split()                       ["abc"]
  'a,b,c'.split(',', 2)               ["a","b"]
  'a1b2c'.split(/(\d)/, 2)            ["a","1"]
  'abc'.split(/(?:)/)                 ["a","b","c"]

[3] does split look at lastIndex or the g flag?
  'a,b,c'.split(/,/g)  lastIndex=3    ["a","b","c"]
    g.lastIndex afterwards            3
```

- ★★★ **캡처 그룹이 있으면 캡처가 결과에 끼어든다** — `split(/(\d)/)` 가 `["a","1","b","2","","2","c"]`. 그룹이 없으면(`/\d/`) 구분자는 사라진다.
- ★★ **반복 그룹 `(\d)+` 는 마지막 반복만** 남긴다 — `"22"` 가 한 구분자이고 캡처는 `"2"` 하나(`["a","1","b","2","c"]`).
- ★★★ **참여하지 않은 그룹은 `undefined` 로 끼어든다** — `/(\d)|(-)/` 에서 **매 구분자마다 두 칸**이 들어가고 그중 하나는 `undefined` 다. 이게 싫으면 **비캡처 `(?:…)`** 다.
- ★★ **`[2]`** — 양 끝의 구분자는 **빈 글자**를 만든다(`["","a","","b",""]`) · **`''.split(',')` 는 `[""]`(원소 하나)**, `''.split('')` 는 `[]` · 인자 없는 `split()` 은 `["abc"]`.
  **`limit` 은 캡처까지 센다** — `'a1b2c'.split(/(\d)/, 2)` 가 `["a","1"]`.
- ★★ **`[3]` `split` 은 `lastIndex` 와 `g` 를 안 본다** — `lastIndex = 3` 으로 둔 `/,/g` 로도 처음부터 나눴고(`["a","b","c"]`), **원래 객체의 `lastIndex` 는 `3` 그대로**다.
  명세 `split` 은 `@@split` 에서 **`y` 플래그를 붙인 새 정규식**을 만들어 쓴다 — 원래 객체는 건드리지 않는다.

### (6) ★★ 채우기 · 다듬기 · 찾기 — 경계 인자

**언제 쓰나** — 자리수 맞추기(`padStart`) · 입력 정리(`trim`) · 부분 문자열 확인(`includes`·`startsWith`).

```text
   "7".padStart(6, "ab")      채울 칸 5  ->  "ab" 를 되풀이해 5칸  "ababa"  ->  "ababa7"
   "1234".padStart(3, "0")    이미 3 보다 길다  ->  그대로 "1234" (자르지 않는다)
   "7".padStart(3, "")        채울 글자가 없다  ->  그대로 "7"

   trim 이 지우는 것 = WhiteSpace + LineTerminator
     WhiteSpace  = TAB VT FF ZWNBSP(U+FEFF) + 유니코드 Space_Separator(Zs) 전부 (U+0020 U+00A0 U+3000 ...)
     U+200B(zero width space) 는 Cf 이고 목록에 없다  ->  안 지운다   (U+FEFF 도 Cf 지만 목록에 있다)
```

```js
// js28b-28f-pad-trim-search.js
// padStart / trim / includes / startsWith / indexOf -- the edge arguments.
const J = (x) => (x === undefined ? "undefined" : JSON.stringify(x));
const show = (label, f) => {
  try { console.log("  " + label.padEnd(44) + J(f())); }
  catch (e) { console.log("  " + label.padEnd(44) + e.constructor.name + " 「" + e.message + "」"); }
};

console.log("[1] padStart / padEnd");
show("'7'.padStart(3, '0')", () => "7".padStart(3, "0"));
show("'7'.padStart(6, 'ab')", () => "7".padStart(6, "ab"));
show("'1234'.padStart(3, '0')", () => "1234".padStart(3, "0"));
show("'7'.padStart(3, '')", () => "7".padStart(3, ""));
show("'7'.padStart(3)", () => "7".padStart(3));
show("'7'.padEnd(3, 'xyz')", () => "7".padEnd(3, "xyz"));

console.log("");
console.log("[2] trim -- the first character's general category, and the code units (hex) before and after");
const hex = (t) => [...Array(t.length).keys()].map((i) => t.charCodeAt(i).toString(16).padStart(4, "0")).join(" ");
const cases = [
  ["space tab newline", " \t\nx\n"],
  ["U+00A0 no-break space", String.fromCharCode(0xa0) + "x"],
  ["U+3000 ideographic space", String.fromCharCode(0x3000) + "x"],
  ["U+FEFF byte order mark", String.fromCharCode(0xfeff) + "x"],
  ["U+200B zero width space", String.fromCharCode(0x200b) + "x"],
  ["U+2028 line separator", String.fromCharCode(0x2028) + "x"],
];
const cat = (t) => ["Zs", "Zl", "Cf", "Cc"].find((c) => new RegExp("^\\p{" + c + "}", "u").test(t)) || "-";
for (const [name, t] of cases) console.log("  " + name.padEnd(26) + "category " + cat(t).padEnd(4) + "before " + hex(t).padEnd(26) + "after trim " + hex(t.trim()));
show("'  x  '.trimStart()", () => "  x  ".trimStart());
show("'  x  '.trimEnd()", () => "  x  ".trimEnd());

console.log("");
console.log("[3] includes / startsWith / endsWith / indexOf");
show("'abc'.includes('')", () => "abc".includes(""));
show("'abc'.indexOf('')", () => "abc".indexOf(""));
show("'abc'.indexOf('', 10)", () => "abc".indexOf("", 10));
show("'abc'.startsWith('b', 1)", () => "abc".startsWith("b", 1));
show("'abc'.endsWith('b', 2)", () => "abc".endsWith("b", 2));
show("'abc'.includes('A')", () => "abc".includes("A"));
show("'a.c'.includes('.')", () => "a.c".includes("."));
show("'abc'.includes(/b/)", () => "abc".includes(/b/));
show("'abc'.startsWith(/a/)", () => "abc".startsWith(/a/));
const r = /b/;
r[Symbol.match] = false;
show("'/b/'.includes(r)  r[Symbol.match]=false", () => "/b/".includes(r));
show("'abc'.includes(undefined)", () => "abc".includes(undefined));
show("'undefined'.includes()", () => "undefined".includes());
```
```text
===== node20 js28b-28f-pad-trim-search.js (exit=0) =====
[1] padStart / padEnd
  '7'.padStart(3, '0')                        "007"
  '7'.padStart(6, 'ab')                       "ababa7"
  '1234'.padStart(3, '0')                     "1234"
  '7'.padStart(3, '')                         "7"
  '7'.padStart(3)                             "  7"
  '7'.padEnd(3, 'xyz')                        "7xy"

[2] trim -- the first character's general category, and the code units (hex) before and after
  space tab newline         category Zs  before 0020 0009 000a 0078 000a  after trim 0078
  U+00A0 no-break space     category Zs  before 00a0 0078                 after trim 0078
  U+3000 ideographic space  category Zs  before 3000 0078                 after trim 0078
  U+FEFF byte order mark    category Cf  before feff 0078                 after trim 0078
  U+200B zero width space   category Cf  before 200b 0078                 after trim 200b 0078
  U+2028 line separator     category Zl  before 2028 0078                 after trim 0078
  '  x  '.trimStart()                         "x  "
  '  x  '.trimEnd()                           "  x"

[3] includes / startsWith / endsWith / indexOf
  'abc'.includes('')                          true
  'abc'.indexOf('')                           0
  'abc'.indexOf('', 10)                       3
  'abc'.startsWith('b', 1)                    true
  'abc'.endsWith('b', 2)                      true
  'abc'.includes('A')                         false
  'a.c'.includes('.')                         true
  'abc'.includes(/b/)                         TypeError 「First argument to String.prototype.includes must not be a regular expression」
  'abc'.startsWith(/a/)                       TypeError 「First argument to String.prototype.startsWith must not be a regular expression」
  '/b/'.includes(r)  r[Symbol.match]=false    true
  'abc'.includes(undefined)                   false
  'undefined'.includes()                      true
```

- ★★ **`padStart` 는 자르지 않는다**(`"1234"`) · 채울 글자를 **되풀이하다 자른다**(`"ababa7"` · `"7xy"`) · **빈 채움 글자면 그대로**(`"7"`) · 채움 글자를 안 주면 **공백**이다.
- ★★★ **`trim` 은 `U+00A0`·`U+3000`·`U+FEFF`·`U+2028` 을 지우고 `U+200B` 는 안 지운다**(`200b 0078` 이 남았다).
  명세의 공백은 **`WhiteSpace`(Zs 전부 + TAB·VT·FF·ZWNBSP) + `LineTerminator`** 다. 첫 열의 분류가 그 근거다 —
  `U+200B` 는 이름에 「space」가 있어도 **`Cf`** 이고 목록에 따로 적혀 있지도 않아 남는다. ★ **`U+FEFF` 도 `Cf` 인데 지워진다** — `WhiteSpace` 에 **ZWNBSP 로 따로 적혀** 있다. 분류만 보고 판단하면 이 한 줄을 틀린다.
- ★★ **빈 문자열은 어디에나 있다** — `includes('')` 는 `true`, `indexOf('')` 는 `0`, **`indexOf('', 10)` 은 `3`**(위치가 길이로 깎인다).
- ★★★ **`includes(/b/)`·`startsWith(/a/)` 는 `TypeError`** 다(`First argument to String.prototype.includes must not be a regular expression`).
  명세가 인자에 **`IsRegExp`** 를 물어 참이면 던진다 — 정규식을 넘기면 「패턴 검색」을 기대했을 것이라 **조용히 문자열로 바꾸지 않는다.**
  ★ **`IsRegExp` 는 `Symbol.match` 를 먼저 본다** — `r[Symbol.match] = false` 로 두면 정규식인데도 통과하고, `ToString(r)` 인 `"/b/"` 를 찾아 `true` 다. 22번의 「잘 알려진 심볼이 언어 동작을 바꾼다」의 한 자리다.
- ★ **`includes(undefined)` 는 `"undefined"` 라는 글자를 찾는다** — `'undefined'.includes()` 가 `true`.

### (7) ★★ 파이썬과의 대비 — `replace` 가 바꾸는 곳 · 치환 표기 · 음수 자르기

**언제 쓰나** — 두 언어를 오가며 문자열 코드를 옮길 때. **같은 이름의 메서드가 기본값이 반대**다.

```text
                         JS                                 Python
   "a-b-c".replace("-")  첫 자리 하나 "a+b-c"                  전부 "a+b+c"  (count 로 제한)
   치환 문자열 표기        $& $1 $<g>                           \1 \g<g>   ($ 는 그냥 글자)
   없는 그룹 $9 / \9      글자 그대로 "$9"                       re.error
   함수 치환              $ 를 안 읽는다                          \ 를 안 읽는다 (같다)
   음수 자르기            slice(-2) = s[-2:]                   같다
                         substring(-2) = 전체                  (대응하는 것이 없다)
```

```sh
# js28b-28g-python.sh
#!/usr/bin/env bash
# 같은 질문을 파이썬에 던진다 -- replace 가 몇 곳을 바꾸나 · 치환 문자열의 특수 표기 · 자르기의 음수 인자.
set -u -o pipefail
python3 - <<'PY'
import re
def show(label, f):
    try:
        print("  " + label.ljust(44) + repr(f()))
    except Exception as e:
        print("  " + label.ljust(44) + type(e).__name__ + " 「" + str(e) + "」")

print("[1] str.replace")
show("'a-b-c'.replace('-', '+')", lambda: "a-b-c".replace("-", "+"))
show("'a-b-c'.replace('-', '+', 1)", lambda: "a-b-c".replace("-", "+", 1))
show("'abc'.replace('', '-')", lambda: "abc".replace("", "-"))
show("'abc'.replace('b', '[$&]')", lambda: "abc".replace("b", "[$&]"))

print("")
print("[2] re.sub -- the replacement template")
show("re.sub('(b)', r'[\\1]', 'abc')", lambda: re.sub("(b)", r"[\1]", "abc"))
show("re.sub('(?P<g>b)', r'[\\g<g>]', 'abc')", lambda: re.sub("(?P<g>b)", r"[\g<g>]", "abc"))
show("re.sub('(b)', '[$1]', 'abc')", lambda: re.sub("(b)", "[$1]", "abc"))
show("re.sub('(b)', r'[\\9]', 'abc')", lambda: re.sub("(b)", r"[\9]", "abc"))
show("re.sub('b', lambda m: r'[\\1]', 'abc')", lambda: re.sub("b", lambda m: r"[\1]", "abc"))

print("")
print("[3] slicing with negative and reversed bounds")
s = "abcdef"
show("s[-2:]", lambda: s[-2:])
show("s[4:2]", lambda: s[4:2])
show("s[2:-1]", lambda: s[2:-1])
PY
```
```text
===== ./js28b-28g-python.sh (exit=0) =====
[1] str.replace
  'a-b-c'.replace('-', '+')                   'a+b+c'
  'a-b-c'.replace('-', '+', 1)                'a+b-c'
  'abc'.replace('', '-')                      '-a-b-c-'
  'abc'.replace('b', '[$&]')                  'a[$&]c'

[2] re.sub -- the replacement template
  re.sub('(b)', r'[\1]', 'abc')               'a[b]c'
  re.sub('(?P<g>b)', r'[\g<g>]', 'abc')       'a[b]c'
  re.sub('(b)', '[$1]', 'abc')                'a[$1]c'
  re.sub('(b)', r'[\9]', 'abc')               error 「invalid group reference 9 at position 2」
  re.sub('b', lambda m: r'[\1]', 'abc')       'a[\\1]c'

[3] slicing with negative and reversed bounds
  s[-2:]                                      'ef'
  s[4:2]                                      ''
  s[2:-1]                                     'cde'
```

- ★★★ **파이썬 `str.replace` 는 기본이 「전부」**(`'a+b+c'`)이고 세 번째 인자 `count` 로 줄인다. JS `replace` 는 기본이 「**첫 하나**」다. 이름이 같은데 기본값이 반대다.
- ★★ **파이썬 `str.replace` 는 치환 표기를 안 읽는다**(`'a[$&]c'`). 표기는 `re.sub` 의 몫이고 **`\1`·`\g<g>`** 꼴이다 — `$1` 은 파이썬에서 그냥 글자다.
- ★★★ **없는 그룹 번호에서 갈린다** — JS 는 `$9` 를 **글자 그대로** 두고, 파이썬 `re.sub` 는 **`error 「invalid group reference 9 at position 2」`** 로 던진다.
  JS 에서 오타가 **조용히 출력에 섞이는** 자리다.
- ★ **함수 치환은 두 언어 다 표기를 안 읽는다** — 파이썬도 람다가 돌려준 `r'[\1]'` 을 그대로 넣었다(`'a[\\1]c'` 는 `repr` 이 백슬래시를 두 개로 보인 것이다).
- ★ **빈 패턴** — 파이썬 `replace('', '-')` 는 `'-a-b-c-'` 로 JS 의 `replaceAll('', '-')` 과 같다.
- ★ 파이썬의 문자열 메서드는 파이썬 갈래 [07 — 문자열 메서드](../../../python/syntax/07-string-methods/2-summary.md)가, `re` 는 파이썬 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **46번**이 정본이다. 여기서는 **같은 질문을 던진 결과**만 싣는다.

## 문법 — 형태와 규칙

★ 이 절은 **형태 표**다 — 모든 동작 주장은 위 동작 절의 캡처 블록에서만 한다(규칙 28 — 돌리지 않은 코드 펜스를 싣지 않는다).

| 형태 | 돌려주는 것 | 판 | 어디서 봤나 |
|---|---|---|---|
| `s.replace(pattern, 문자열)` | 새 문자열 — **첫 자리 하나**(정규식에 `g` 가 있으면 전부) · 치환 문자열의 `$` 표기를 읽는다 | ES5 이하 | 동작 (1)·(2) |
| `s.replace(pattern, 함수)` | 새 문자열 — 함수의 반환값을 `ToString` 해서 **그대로** | ES5 이하 | 동작 (1)의 넷째 열 |
| `s.replaceAll(pattern, …)` | 새 문자열 — **전부** · 정규식이면 **`g` 필수**(없으면 `TypeError`) | **ES2021** | 동작 (2) |
| ``tag`…${v}…` `` | `tag(strings, ...values)` 의 반환값 — `strings` 는 **자리마다 하나**, 동결 | ES2015 | 동작 (3) |
| ``String.raw`…` `` · `String.raw({ raw }, ...subs)` | 이스케이프를 **안 푼** 문자열 | ES2015 | 동작 (3)의 `[3]` |
| `s.slice(a, b)` | 음수는 **뒤에서**, `a ≥ b` 면 빈 글자 | ES5 이하 | 동작 (4) |
| `s.substring(a, b)` | 음수·`NaN` 은 **0**, **작은 쪽이 앞** | ES5 이하 | 동작 (4) |
| `s.substr(a, 길이)` | 두 번째가 **길이** | **부록 B** | 동작 (4) |
| `s.at(i)` | 음수는 뒤에서 · 범위 밖은 `undefined` · **코드 유닛** 하나 | **ES2022** | 동작 (4)의 `[2]`·`[3]` |
| `s.split(sep, limit)` | 배열 — 정규식의 **캡처가 끼어든다** · `limit` 은 캡처까지 센다 | ES5 이하 | 동작 (5) |
| `s.padStart(n, fill)` · `padEnd` | 길이 `n` 까지 채운 문자열 — **자르지 않는다** | **ES2017** | 동작 (6) |
| `s.trim()` · `trimStart` · `trimEnd` | `WhiteSpace`·`LineTerminator` 를 지운 문자열 | ES5 · **ES2019** | 동작 (6) |
| `s.includes(x)` · `startsWith` · `endsWith` | 불리언 — **정규식이면 `TypeError`** | ES2015 | 동작 (6) |

- **치환 표기** — `$$` · `$&` · `` $` `` · `$'` · `$n`/`$nn` · `$<이름>`. 앞의 넷은 **언제나**, `$n` 은 **그 번호의 그룹이 있을 때만**, `$<이름>` 은 **명명 그룹이 하나라도 있을 때만** 읽힌다.
- **태그 템플릿의 이스케이프** — 태그가 있으면 잘못된 이스케이프가 **허용**되고 `cooked` 가 `undefined`(ES2018). 태그가 없으면 **`SyntaxError`**.

## 어디서 틀리나

### (1) ★★★ 바깥에서 온 문자열을 `replace` 의 두 번째 인자로 넣는다

`$&`·`` $` ``·`$'`·`$$`·`$1` 이 섞이면 **조용히 다른 글자**가 된다(동작 (1)의 `[3]` — `"$&0"` 이 `"X0"`). 예외가 없어서 테스트 데이터에 `$` 가 없으면 영영 안 드러난다.
★ 처방 — **함수로 감싼다**(`() => userText`). 동작 (1)의 `[3]` 마지막 줄이 그 처방의 실측이다.

### (2) ★★★ `replace('-', '+')` 가 전부 바꿀 것이라 믿는다

**첫 자리 하나**다(동작 (2)의 `[1]`). 파이썬 `str.replace` 와 기본값이 반대라서(동작 (7)) 두 언어를 오가면 특히 잘 틀린다. 전부면 `replaceAll` 이나 `/-/g`.

### (3) ★★★ `replaceAll(/x/, …)` 를 쓴다

**`TypeError`** 다(동작 (2)의 `[2]`). `replaceAll` 에 정규식을 주면 **`g` 가 필수**다. 반대로 `replace(/x/g, …)` 는 전부 바꾼다 — 「전부」를 정하는 것은 메서드 이름이 아니라 **`g`** 다.

### (4) ★★★ 치환 함수가 돌려준 `$&` 도 읽힐 것이라 믿는다

**안 읽힌다**(동작 (1)의 넷째 열 11줄 전부). 함수를 쓰면 **찾은 것·캡처·위치를 인자로** 받아 직접 조립한다. 반대로, 표기를 쓰려고 함수 안에서 `'$1'` 을 돌려주면 글자 `$1` 이 나온다.

### (5) ★★ 없는 그룹 `$9` 가 빈 글자가 될 것이라 믿는다 — 또는 `$<x>` 가 늘 글자 그대로일 것이라 믿는다

`$9` 는 **글자 그대로**(`"a[$9]c"`) · `$<x>` 는 **명명 그룹이 있는 정규식에서만 빈 글자**, 없으면 글자 그대로다(동작 (1)). 그룹이 1개일 때 `$10` 은 **`$1` + `"0"`** 이다.

### (6) ★★★ `substring` 과 `slice` 를 바꿔 쓴다

음수와 뒤집힌 인자에서 **열 벌 중 다섯 벌**이 갈린다(동작 (4)). `substring(-2)` 는 **문자열 전체**다 — 「끝 두 글자」를 원했다면 조용히 틀린다. 새 코드는 `slice` 와 `at` 으로 통일한다.

### (7) ★★ `s[-1]` 로 마지막 글자를 읽는다

**`undefined`** 다(동작 (4)의 `[2]`). 음수 인덱스는 `at(-1)` 만 받는다.

### (8) ★★ `split` 의 정규식에 괄호를 쳤더니 결과가 불었다

**캡처 그룹은 결과에 끼어든다**(동작 (5)). 묶기만 하려면 `(?:…)`. 참여 안 한 그룹은 **`undefined` 로** 들어가서 뒤이은 `map(s => s.trim())` 이 `TypeError` 를 낸다.

### (9) ★★ 태그 함수 안에서 `strings` 를 고친다 — 또는 매번 새 배열이라 믿고 `WeakMap` 캐시를 안 쓴다

**얼어 있다**(엄격 코드면 `TypeError`, 동작 (3)). 그리고 **같은 자리면 같은 객체**라서 `strings` 를 `WeakMap` 의 키로 삼아 **파싱 결과를 캐시**할 수 있다(이 캐시는 이 문서가 안 돌렸다 — 동일성만 쟀다).

### (10) ★ `trim()` 이 모든 「보이지 않는 글자」를 지울 것이라 믿는다

`U+200B`(zero width space)는 **안 지운다**(동작 (6)의 `[2]`). 복사·붙여넣기로 들어온 입력은 지울 글자를 **정규식으로 명시해** 지운다(유니코드 표기는 30번 — 이 문서는 그 정규식을 안 돌렸다).

## 구현 세부사항 대 언어 보장

### 명세 보장 — 어느 엔진에서도 같아야 하는 것

- ★★★ **`GetSubstitution`** 이 치환 **문자열**의 `$$`·`$&`·`` $` ``·`$'`·`$n`/`$nn`·`$<이름>` 을 읽는 규칙 — 없는 번호는 글자 그대로 · 두 자리를 먼저 보고 한 자리로 물러나는 것 · 명명 캡처가 `undefined` 면 `$<` 가 글자 그대로 · 이름이 없으면 빈 글자.
- ★★★ 치환 **함수**의 반환값은 `ToString` 만 거치고 `GetSubstitution` 을 안 거친다.
- ★★★ `replaceAll` 이 정규식 인자에 `flags` 를 읽어 `g` 가 없으면 **`TypeError`** · 문자열 패턴이면 겹치지 않는 모든 자리(빈 패턴은 **모든 위치**).
- ★★★ **`GetTemplateObject`** — 템플릿 객체는 realm 의 `[[TemplateMap]]` 에 **소스 자리(Parse Node)마다 하나**로 캐시되고, `strings` 와 `raw` 가 **동결**된다.
- ★★ 태그 템플릿에서만 `NotEscapeSequence` 가 허용되고 `cooked` 가 `undefined`(ES2018) · 태그 없는 템플릿은 **조기 오류**(`SyntaxError`).
- ★★ `slice`·`substring`·`substr`·`at` 의 인자 규칙 · `split` 이 캡처를 끼워 넣고 `limit` 이 그것까지 세는 것 · `@@split` 이 `y` 를 붙인 **새 정규식**을 쓰는 것.
- ★★ `trim` 이 지우는 집합(`WhiteSpace` + `LineTerminator`) · `includes`/`startsWith`/`endsWith` 가 `IsRegExp` 로 거절하는 것 · `IsRegExp` 가 `Symbol.match` 를 먼저 보는 것.
- 예외의 **종류**(`TypeError`·`SyntaxError`).

### 엔진(V8) 구현 · 이 판의 관찰

- 예외 **문구 전부** — `String.prototype.replaceAll called with a non-global RegExp argument` · `First argument to String.prototype.includes must not be a regular expression` ·
  `Invalid Unicode escape sequence` · `Cannot assign to read only property '0' of object '[object Array]'`.
- `trim` 결과는 명세가 정하지만 **어느 글자가 Zs 인가는 유니코드 판**에 매인다 — 이 머신은 node 18 이 Unicode 15.1, node 20 이 16.0 이고(판별 블록) 이 문서가 쓴 글자는 두 판에서 같았다.
- 두 node 판이 **`isWellFormed` 한 줄만** 갈린 것 — 관찰이다(판이 같아서 보장이라는 뜻이 아니다).

### 파이썬 쪽 — 다른 언어의 보장

- `str.replace` 의 기본 「전부」·`count` · `re.sub` 의 `\1`/`\g<n>` · 없는 그룹의 `re.error` 는 **CPython 3.12 의 문서화된 동작**이다. 예외 문구는 CPython 의 글자다.

### 그래서 이렇게 적으면 틀린다

- ✗ 「`replace` 는 전부 바꾼다」 → ○ 「**첫 자리 하나**다 — 전부는 `replaceAll` 이나 `g`」
- ✗ 「`$1` 은 언제나 첫 그룹이다」 → ○ 「**그룹이 있을 때만** — 문자열 패턴·함수 치환에서는 글자 그대로」
- ✗ 「없는 그룹 `$9` 는 빈 글자가 된다」 → ○ 「**글자 그대로** 남는다」
- ✗ 「태그 함수는 부를 때마다 새 배열을 받는다」 → ○ 「**소스 자리마다 하나** — 같은 자리면 같은 동결 배열」
- ✗ 「템플릿 리터럴에 잘못된 이스케이프는 언제나 문법 오류다」 → ○ 「**태그가 있으면** 허용되고 `cooked` 가 `undefined`」
- ✗ 「`substring` 은 `slice` 의 옛 이름이다」 → ○ 「**음수와 뒤집힌 인자**에서 다르다(열 벌 중 다섯)」
- ✗ 「`replaceAll` 이 `split().join()` 보다 빠르다」 → ○ **안 쟀다**

## 언제 쓰고 언제 안 쓰나

- **`replaceAll(문자열, 함수)`** — 바깥에서 온 글자로 모든 자리를 바꿀 때. `$` 걱정이 없다.
- **`replace(/…/g, "$1…")`** — 캡처를 재배치할 때. 치환 문자열이 **소스에 박힌 상수**일 때만.
- **태그 템플릿** — 조각과 값을 **따로 받아야 하는** 조립(SQL 매개변수 · HTML 이스케이프). 조각 배열을 **캐시 키로** 쓸 수 있다.
- **`String.raw`** — 백슬래시가 많은 문자열(정규식 원문 · 윈도 경로). 단 **끝 백슬래시 뒤에 `${`** 를 못 붙인다.
- **`slice` · `at`** — 자르기와 한 글자 읽기의 기본값. `substring`·`substr` 은 **읽을 줄만** 알면 된다.
- ★ **안 쓰는 자리** — 글자(서로게이트 쌍·결합 문자)를 **사람이 보는 글자 단위**로 잘라야 할 때(`slice`·`at` 은 코드 유닛이다 — 04번의 `Intl.Segmenter`) · 복잡한 패턴 치환(29·30번의 정규식).

## 핵심 문장

1. ★★★ 치환 **문자열**은 `$` 표기를 읽는 작은 언어이고, 치환 **함수**의 반환값은 안 읽힌다 — 표기 11가지 × 자리 4가지에서 **20 / 44 칸**이 바뀌었고 함수 열은 전부 글자 그대로였다.
2. ★★★ `$&`·`` $` ``·`$'`·`$$` 는 언제나 읽히고, `$n` 은 **그 그룹이 있을 때만**, `$<이름>` 은 **명명 그룹이 있을 때만** 읽힌다 — 없는 번호는 **글자 그대로**다.
3. ★★★ `replace` 는 **첫 하나**, `replaceAll` 은 **전부**이고 정규식이면 `g` 가 없을 때 `TypeError` 다.
4. ★★★ 태그 함수의 `strings` 는 **소스 자리마다 하나 · 동결**이다 — 같은 자리는 `===`, 태그가 있으면 잘못된 이스케이프가 `cooked: undefined` 로 허용된다.
5. ★★ `slice` 는 음수를 뒤에서 세고, `substring` 은 0 으로 깎고 뒤집는다 — 열 벌 중 **5 / 10** 이 갈렸다. `split` 의 캡처는 결과에 끼어든다.

## 관련 자료

- [ECMA-262 — String Objects](https://tc39.es/ecma262/multipage/text-processing.html#sec-string-objects)(`GetSubstitution` · `replaceAll` · `split`) · [Template Literals](https://tc39.es/ecma262/multipage/ecmascript-language-expressions.html#sec-template-literals)(`GetTemplateObject`)
- [TC39 finished proposals](https://github.com/tc39/proposals/blob/main/finished-proposals.md) — 판 경계
- [04 — 문자열과 UTF-16](../04-strings-and-utf16/2-summary.md) — ★ **경계**: 그쪽은 **코드 유닛·서로게이트·well-formed·`Intl.Segmenter`** 까지, 여기는 **자르기 메서드가 그 위에서 무엇을 돌려주나**부터.
- [22 — `Symbol` 과 잘 알려진 심볼](../22-symbol-and-well-known-symbols/2-summary.md) — ★ **경계**: 그쪽은 **`` `${x}` `` 의 hint(`string`)와 `Symbol.match` 같은 심볼의 전수**, 여기는 **태그 템플릿**과 `IsRegExp` 가 `Symbol.match` 를 보는 한 자리.
- [29 — 정규식 기본](../29-regexp-basics/2-summary.md) — ★ **경계**: 그쪽이 **플래그·`lastIndex`·`match`/`matchAll`·정규식 `replace` 콜백의 인자**의 정본, 여기는 **치환 문자열의 표기**.
- [30 — 정규식 심화](../30-regexp-advanced/2-summary.md) — 명명 그룹 문법·유니코드 표기.
- 파이썬 갈래 [07 — 문자열 메서드](../../../python/syntax/07-string-methods/2-summary.md) · [08 — f-string 과 format spec](../../../python/syntax/08-fstrings-and-format-spec/2-summary.md) — 동작 (7)의 대비. `re` 는 파이썬 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **46번**.

## 용어 풀이

- **치환 문자열** — `replace`·`replaceAll` 의 두 번째 인자로 준 문자열. `GetSubstitution` 이 `$` 표기를 읽는다.
- **`GetSubstitution`** — 치환 문자열을 채우는 명세 연산. 찾은 글자·위치·캡처 목록·명명 캡처 객체를 받는다.
- **캡처 그룹** — 정규식의 `( )`. 찾은 조각을 번호(1부터)로 기억한다. 명명 그룹 `(?<이름>…)` 은 이름으로도 기억한다.
- **비캡처 그룹** — `(?:…)`. 묶기만 하고 기억하지 않는다.
- **태그 템플릿** — ``tag`…` `` 꼴의 호출. 조각 배열과 값들을 따로 넘긴다.
- **cooked / raw** — 이스케이프를 **푼** 조각(`"\n"` → 줄바꿈) / **안 푼** 조각(`"\n"` → 백슬래시와 n).
- **`GetTemplateObject`** — 태그 템플릿의 조각 배열을 만들고 **자리마다 캐시**하는 명세 연산.
- **동결(freeze)** — 프로퍼티를 추가·삭제·변경할 수 없게 한 상태. 14번이 정본이다.
- **코드 유닛** — UTF-16 의 16비트 한 칸. `length`·`slice`·`at` 이 세는 단위. 04번이 정본이다.
- **`WhiteSpace` / `LineTerminator`** — 명세의 공백 문자 집합과 줄 끝 문자 집합. `trim` 이 이 둘을 지운다.
- **`IsRegExp`** — 값이 정규식처럼 다뤄져야 하나를 묻는 명세 연산. `Symbol.match` 를 먼저 보고, 없으면 내부 슬롯을 본다.
- **부록 B(Annex B)** — 웹 호환 때문에 남겨 둔 기능을 모은 명세의 부록. `substr` 이 여기 있다.

## 더 들어가면

- **`$<이름>` 과 중복 명명 그룹**(ES2025) — 같은 이름이 두 갈래에 있으면 `$<이름>` 이 무엇을 채우나. 30번의 몫이고 이 문서는 **안 돌렸다.**
- **`localeCompare`·`normalize`·`toLocaleUpperCase`** — 로케일과 유니코드 정규화는 04번과 [목록의 **50번 주제**](../50-intl-formatting/)(`Intl`)의 몫이다.
- **태그 템플릿 캐시와 가비지 수집** — 템플릿 객체가 자리마다 영구히 사는가는 명세가 realm 의 `[[TemplateMap]]` 으로 정하지만, 메모리 동작은 **안 쟀다.**
