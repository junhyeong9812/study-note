# js/syntax/30 — 정규식 심화: 「그룹·둘러보기·유니코드 — 그리고 같은 패턴이 어떤 엔진에서는 끝나지 않는다」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> ★★★ **이 주제의 본체는 ② 전수 격자다 — 「입력 길이 × 엔진」 완료 격자와, V8 에게 센 「되돌이 수」 표.**
> 백트래킹 폭발은 **재지 않은 성능 주장 금지** 규칙과 가장 세게 부딪치는 주제다. 그래서 경과 시간을 **한 숫자도 싣지 않는다.**
> 대신 두 창으로 묻는다 —
> ① **「2초 안에 끝났나」의 참/거짓 격자**(엔진 여섯 × n 다섯 — 동작 (7)) ·
> ② **V8 의 「되돌이를 K 번 넘기면 선형 엔진으로 갈아타라」 플래그로 K 를 이분 탐색한 표**(동작 (8)). 이쪽은 **시간이 아니라 되돌이 횟수**이고, 두 node 판에서 한 글자도 같았다.
> ★★ 보조로 **④ 예외의 이름·문구**(`SyntaxError` 가 이 주제의 절반이다 — 문법이 없는 판·플래그·엔진)를 쓴다.
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262 — RegExp (Regular Expression) Objects](https://tc39.es/ecma262/multipage/text-processing.html#sec-regexp-regular-expression-objects) — Pattern 문법 · Pattern Semantics(매처·연속) · `groups` 객체를 만드는 단계 · 플래그 `d`·`u`·`v`
> - [TC39 finished proposals](https://github.com/tc39/proposals/blob/main/finished-proposals.md) — 판 경계(2026-09-26 받아 둔 사본으로 확인)
> - `go doc regexp`(go1.27.1) — RE2 의 선형 시간 보장 문장 · `node --v8-options`(두 판) — V8 의 선형 엔진 스위치 이름과 설명
>
> ★★★ **명세 조항 번호는 인용하지 않는다.** 규칙 진술은 **추상 연산·문법 이름**으로, 값·예외·격자는 **전부 실행으로** 접지했다.
>
> **실행 검증** — 이 문서의 모든 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 하나도 없다).
> 배너의 `node20` 은 `~/.nvm/versions/node/v20.19.6/bin/node`, `node18` 은 기본 PATH 의 `node`(v18.19.1)다.
> ★★★ **ES2025 의 세 가지(`RegExp.escape`·중복 명명 그룹·수정자)는 두 node 판에 없다**(아래 판별 블록). 그 탐침은 **Google Chrome 151 을 헤드리스로** 돌렸다 — 배너가 `google-chrome --headless` 로 시작하는 블록이다.
> ★★ **셸 탐침**(배너 `./js28b-30?-….sh`)은 `timeout`·`go`·`python3` 을 부른다 — 셸이 결과를 **참/거짓으로만** 거른다(Go 갈래 목록([`go/syntax/README.md`](../../../go/syntax/README.md))의 **28번**이 쓴 방식이다).
> ★★ **예외는 `try`/`catch` 로 받아 `e.constructor.name` 과 `e.message` 만** `이름 「메시지」` 꼴로 찍었다.
> ★ **astral 글자는 문서에 한 글자도 없다** — `String.fromCodePoint(0x1f600)` 으로 **실행 중에** 만들고 **코드 유닛 16진수와 길이만** 찍었다(04편과 같은 방식).
>
> **버전** — 판별 블록이 세 판(node 18 · node 20 · Chrome 151)에 같은 스크립트를 던진다.
>
> | 무엇 | 판 | 이 머신에서 |
> |---|---|---|
> | 캡처·비캡처 `(?:)` · 역참조 `\1` · 룩어헤드 `(?=)` `(?!)` | ES3 | 세 판 다 있다 |
> | `u` 플래그 · `\u{…}` | ES2015 | 세 판 다 있다 |
> | 명명 그룹 `(?<n>)` · 룩비하인드 `(?<=)` `(?<!)` · `\p{…}` · `s` 플래그 | **ES2018** | 세 판 다 있다 |
> | `d` 플래그(`indices`) | **ES2022** | 세 판 다 있다 |
> | `v` 플래그(집합 연산 · 글자열 속성) | **ES2024** | ★ **node18 에 없다** — node20 · Chrome 에 있다 |
> | `RegExp.escape` · 중복 명명 그룹 · 수정자 `(?i:…)` | **ES2025** | ★ **두 node 판에 없다** — Chrome 151 로만 돌렸다 |
>
> ★ README 의 이 주제 행(`v` 플래그 ES2024 · `RegExp.escape` ES2025)은 finished proposals 표와 **같다.** 표가 더 적는 것은 **중복 명명 그룹과 수정자도 ES2025** 라는 것이다.
>
> **★★★ 이 주제가 쓰는 창 — 그리고 부적용인 창**
>
> | 창 | 이 주제에서 무엇을 보나 |
> |---|---|
> | ★★★ **② 전수 격자**(본체) | n 다섯 × 엔진 여섯의 **「2초 안에 끝났나」**(동작 (7)) · **되돌이 한도 이분 탐색 표**(동작 (8)) · 같은 패턴 열두 개 × 엔진 셋의 **받나/거절하나**(동작 (9)) · 플래그 없음/`u`/`v` × 패턴 일곱(동작 (3)) — 마지막 줄의 「N / M」을 스크립트가 센다 |
> | ★★ **④ 예외의 `constructor.name` + `message`** | 없는 판의 `SyntaxError` · `v` 가 거절하는 글자 · 선형 엔진의 `Cannot be executed in linear time` · RE2·파이썬의 거절 문구 |
> | ★★ **⑤ 두 판 대조기** | `v` 가 없는 node18 에서 **판이 갈린 블록 셋**(동작 (1)·(3)·(4)) — 대조기가 센다 |
> | ★ **제5의 상태 — 창을 바꿔 물었다** | 「폭발하나」를 **시간으로 재지 않고** ① 제한 시간 참/거짓 ② **V8 이 센 되돌이 수**로 물었다. ★ 두 번째 창은 **V8 한 엔진의 계수기**라서 RE2·파이썬에는 없다 — 그쪽은 ① 만으로 답한다 |
> | ★ **부적용 — ① 추상 연산에 로그 심기** | 매칭 **안쪽**에는 사용자 코드가 끼어들 훅이 없다(`replace` 콜백은 매칭이 **끝난 뒤** 불린다 — 29편의 몫). 그래서 로그 대신 되돌이 계수기를 창으로 삼았다 |
> | ★ **부적용 — ③ 브랜드 태그** | 매치 결과는 배열이고 `groups` 는 null 프로토타입 객체다. 브랜드로 가를 대상이 없다 |
> | ★ **안 쟀다 — 속도** | 「`v` 가 `u` 보다 느리다」·「`RegExp.escape` 는 비싸다」를 **한 줄도 쓰지 않는다** |
>
> **★ 흔들리는 칸 / 안 흔들리는 칸 / 싣지 않는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) | ★★★ 싣지 않는다 |
> |---|---|---|
> | 예외 **문구** — V8 의 것이다. ★ 같은 V8 이라도 **node18 은 문구에 플래그를 안 붙이고 node20 은 붙인다**(`/\k<z>/` 대 `/\k<z>/u`) | 격자의 참/거짓 · 「N / M」 · **되돌이 한도 K 의 값과 비율** · 매치 배열 · 예외의 **종류** | ★★★ **경과 시간** — 흔들리는 칸이 아니라 **아예 안 싣는 칸**이다. 셸이 `timeout 2` 의 종료 코드(124)만 보고 참/거짓으로 바꾼다 |
> | 대조기 블록의 **다른 주제 줄**(같은 배치가 한 대조기를 공유한다) | ★ **「처음 끝나지 않은 n」은 격자 해상도(10 간격) 위에서만** 안 흔들린다 — 그래서 **자릿수**로만 말한다 | V8 추적 줄의 **주소**(`0x…`) — 셸이 「추적 줄이 나왔나」 하나로 줄인다 |
>
> **선행** — [29 — 정규식 기본](../29-regexp-basics/2-summary.md)(★★★ 직접 선행 — 플래그 전수·`lastIndex`·`match`/`matchAll` 은 거기서 쟀다) ·
> [04 — 문자열과 UTF-16](../04-strings-and-utf16/2-summary.md)(★★★ `length` 가 코드 유닛 · 서로게이트 · `split(/(?:)/u)` 는 거기서 쟀다) ·
> [28 — `String` 메서드와 템플릿 리터럴](../28-string-methods-and-template-literals/2-summary.md)(`replace` 의 `$` 치환 규칙) ·
> [27 — `Object` 정적 메서드](../27-object-static-methods/2-summary.md)(`groupBy` 의 null 프로토타입 결과 — `groups` 와 같은 모양) · [15 — 프로토타입 체인](../15-prototype-chain/2-summary.md)(`Object.create(null)` 의 증상).
>
> ★★ **경계 — 플래그 전수와 `lastIndex` 상태는 29편이 정본이다.** 여기서는 **패턴 안쪽**(그룹·둘러보기·유니코드)과 **엔진이 어떻게 찾느냐**만 본다.
> ★★ **경계 — 매칭 알고리즘의 원리**(백트래킹 대 상태 집합 시뮬레이션)는 알고리즘 갈래의 몫이다 — [`algorithm/25-string-matching`](../../../../../algorithm/25-string-matching/2-summary.md) 이 그 자리인데, 지금은 **나이브 검색과 KMP 까지만** 다룬다(확인했다). 여기서는 **「이 엔진에서 끝나나」와 「무엇을 포기하면 끝나나」까지만**.

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

두 node 판 대조기의 집계 줄(이 배치의 모든 node 탐침). 이 주제의 탐침 중 판이 갈린 것은 `js28b-30a`·`30c`·`30d` 셋이다. 전문은 [3-answer.md](3-answer.md) 의 「실행 검증」에 있다.

`identical 19  ·  differs 6  ·  total 25`

## 한눈에 — 쉽게 말하면

**백트래킹 엔진은 「갈림길마다 한쪽을 골라 끝까지 가 보고, 막히면 돌아와 다른 쪽을 가 보는 탐험가」다.**
미로의 갈림길이 한 줄로 이어져 있으면 탐험가는 금방 끝낸다. 그런데 **갈림길 안에 갈림길이 겹쳐 있고, 출구가 아예 없으면** 탐험가는 **모든 갈래를 다 가 봐야** 「없다」고 말할 수 있다.
`/^(a+)+$/` 에 `"aaa…a!"` 를 주면 바로 그 미로다 — 안쪽 `a+` 와 바깥 `+` 가 **같은 `a` 들을 나눠 먹는 방법**이 전부 갈래가 되고, 끝의 `!` 때문에 출구가 없다.

- ★★★ **Go 의 RE2 는 「탐험가 한 명」이 아니라 「갈림길마다 무리를 나눠 보내 동시에 걷는 무리」다.** 같은 자리에 선 무리는 하나로 합친다 — 그래서 **입력 길이만큼만 걷는다.**
- ★★★ **그 대신 RE2 는 「아까 지나온 길과 같은 글자인가」(역참조)와 「앞을 미리 보고 오기」(둘러보기)를 못 한다.** 무리를 합치려면 **지나온 길을 기억하지 않아야** 하기 때문이다.
- ★★ **V8 에도 「무리」 엔진이 숨어 있다** — `l` 플래그와 「되돌이를 너무 많이 하면 갈아타기」 스위치. 둘 다 **기본값이 꺼져 있다**(동작 (8)·(10)).
- ★★ **명세(ECMA-262)는 탐험가를 정하지 않는다.** 「어느 답을 찾아야 하나」(왼쪽부터, 욕심 많은 쪽 먼저)를 정할 뿐이고, **어떻게 찾나는 엔진의 일**이다.

```text
   /^(a+)+$/  를  "aaaa!"  에                 같은 입력을 RE2 에
   -------------------------                 ----------------
   바깥 +  : 몇 덩어리로 나누나?                 한 글자씩 읽으며 「지금 설 수 있는 자리」 집합을 갱신
   안쪽 a+ : 덩어리마다 몇 글자?                  a -> {a+ 안}  a -> {a+ 안}  ...  ! -> { }  (빈 집합)
     [aaaa]                                    집합의 크기는 패턴 길이로 묶인다
     [aaa][a]   [a][aaa]                       -> 글자 수만큼 걷고 끝
     [aa][aa]   [aa][a][a]   ...
     [a][a][a][a]
   전부 $ 앞에서 ! 를 만나 실패 -> 전부 되돌아와 다시
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 갈림길마다 한쪽을 먼저 가 보는 탐험가 | **백트래킹 엔진** — V8 의 Irregexp · 파이썬 `re` | 동작 (7)의 node·python 열 |
| 되돌아온 횟수 | V8 의 **되돌이(backtrack) 계수** | 동작 (8)의 K 표 |
| 동시에 걷는 무리 | **상태 집합 시뮬레이션** — Go `regexp`(RE2) · V8 의 실험 엔진 | 동작 (7)의 go·`l` 열 |
| 지나온 길을 기억해야 하는 요구 | 역참조 `\1` · 둘러보기 `(?=)` `(?<=)` | 동작 (9)·(10)의 거절 목록 |
| 출구 규칙만 적은 지도 | 명세의 **Pattern Semantics** — 무엇을 찾을지만 정한다 | 「구현 세부사항 대 언어 보장」 |
| 봉투에 이름 붙여 담기 | 명명 그룹 — `m.groups` | 동작 (1) |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.
「**사용자가 입력한 이메일을 `/^([a-z0-9]+)*@…$/` 같은 패턴으로 검사했더니, 특정 입력 한 줄에 서버 스레드가 멈췄다**」(ReDoS — 정규식 서비스 거부)와
「**`/./` 로 한 글자씩 잘랐더니 이모지가 반으로 쪼개져 깨진 글자가 나왔다**」(동작 (3))가 그것이다.

> **백트래킹(backtracking)** — 선택지 중 하나를 골라 진행하다 실패하면 **마지막 선택 지점으로 돌아가** 다른 선택지를 시도하는 탐색.\
> 예: `/a+b/` 가 `"aaac"` 에서 `a+` 를 셋·둘·하나로 줄여 가며 `b` 를 찾는 것.

> **ReDoS** — 정규식 하나가 특정 입력에서 끝나지 않아 서비스를 멈추게 하는 공격·사고.\
> 예: 검증 패턴에 중첩 수량자 `(x+)+` 가 있고 입력 끝이 어긋나 있을 때.

## 이 주제가 답하려는 질문

1. **그룹과 둘러보기는 매치 결과에 무엇을 남기나** — `groups` 는 어떤 객체이고, 참여하지 않은 그룹·반복 안의 그룹·룩비하인드 안의 그룹은 무엇을 담나?
2. **`u` 와 `v` 는 무엇을 바꾸나** — 서로게이트 한 쌍을 한 글자로 보나, `v` 는 `u` 위에 무엇을 더하고 무엇을 거절하나?
3. ★★★ **같은 패턴이 어떤 엔진에서는 끝나지 않는 것은 왜인가** — 명세의 몫과 엔진의 몫은 어디서 갈리고, 끝나게 하려면 무엇을 포기해야 하나?

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 출력으로 읽는다.

### (1) ★★ 그룹 — 캡처·비캡처·명명, 그리고 `groups` 객체

**언제 쓰나** — 날짜·키=값처럼 **한 매치 안에서 조각을 꺼낼 때**.

```text
   /(?<y>\d{4})-(?<mo>\d{2})-(?<d>\d{2})/.exec("2026-09-26")

   배열 칸      [0] "2026-09-26"   [1] "2026"   [2] "09"   [3] "26"     <- 번호는 여는 괄호 순서
   groups      { y: "2026", mo: "09", d: "26" }                     <- 같은 문자열을 이름으로 한 번 더
                 └ 프로토타입이 null 인 객체

   (?:…) 는 칸을 만들지 않는다  -> 배열이 짧아진다
```

```js
// js28b-30a-groups.js
// Capturing, non-capturing and named groups -- what does the match object hold?
const J = (x) => JSON.stringify(x);
const U = (a) => [...a].map((v) => (v === undefined ? "<undefined>" : v));
const show = (label, f) => {
  try { console.log("  " + label.padEnd(46) + f()); }
  catch (e) { console.log("  " + label.padEnd(46) + e.constructor.name + " 「" + e.message + "」"); }
};
const s = "2026-09-26";

console.log("[1] the same date, grouped three ways");
show("/(\\d+)-(\\d+)-(\\d+)/.exec(s)", () => J(U(/(\d+)-(\d+)-(\d+)/.exec(s))));
show("/(?:\\d+)-(\\d+)-(?:\\d+)/.exec(s)", () => J(U(/(?:\d+)-(\d+)-(?:\d+)/.exec(s))));
const m = /(?<y>\d{4})-(?<mo>\d{2})-(?<d>\d{2})/.exec(s);
show("named -- the array part", () => J(U(m)));
show("named -- m.groups", () => J(m.groups));
show("named -- m.groups.mo", () => m.groups.mo);

console.log("");
console.log("[2] the groups object itself");
show("Object.getPrototypeOf(m.groups) === null", () => Object.getPrototypeOf(m.groups) === null);
show("'toString' in m.groups", () => "toString" in m.groups);
show("String(m.groups)", () => String(m.groups));
show("JSON.stringify(m.groups)", () => J(m.groups));
show("groups when the pattern has no named group", () => String(/(\d+)/.exec(s).groups));
show("key order of /(?<b>x)(?<a>y)/", () => J(Object.keys(/(?<b>x)(?<a>y)/.exec("xy").groups)));

console.log("");
console.log("[3] an optional group -- /(?<a>a)?(?<b>b)/.exec('b')");
const opt = /(?<a>a)?(?<b>b)/.exec("b");
show("array", () => J(U(opt)));
show("Object.keys(groups)", () => J(Object.keys(opt.groups)));
show("groups.a", () => String(opt.groups.a));
show("'a' in groups", () => "a" in opt.groups);

console.log("");
console.log("[4] a group inside a quantifier");
show("/(\\w)+/.exec('abc')", () => J(U(/(\w)+/.exec("abc"))));
show("/(?:(a)|b)+/.exec('ab')", () => J(U(/(?:(a)|b)+/.exec("ab"))));
show("/(?:(a)|(b))+/.exec('ab')", () => J(U(/(?:(a)|(b))+/.exec("ab"))));

console.log("");
console.log("[5] referring back to a group");
show("/(?<q>['\"]).*?\\k<q>/.exec(`say \"hi\" 'yo'`)", () => J(U(/(?<q>['"]).*?\k<q>/.exec(`say "hi" 'yo'`))));
show("/(a)|\\1b/.exec('b')", () => J(U(/(a)|\1b/.exec("b"))));
show("s.replace(named, '$<d>.$<mo>.$<y>')", () => s.replace(/(?<y>\d{4})-(?<mo>\d{2})-(?<d>\d{2})/, "$<d>.$<mo>.$<y>"));
show("callback -- typeof the last argument", () => {
  let last;
  s.replace(/(?<y>\d{4})/, (...args) => { last = args[args.length - 1]; return ""; });
  return typeof last + " " + J(last);
});

console.log("");
console.log("[6] \\k and group names at the edges");
show("new RegExp('\\\\k<z>').test('k<z>')", () => new RegExp("\\k<z>").test("k<z>"));
show("new RegExp('\\\\k<z>', 'u')", () => String(new RegExp("\\k<z>", "u")));
show("new RegExp('(?<a>x)\\\\k<z>')", () => String(new RegExp("(?<a>x)\\k<z>")));
show("new RegExp('(?<a>x)(?<a>y)')", () => String(new RegExp("(?<a>x)(?<a>y)")));
show("new RegExp('(?<1a>x)')", () => String(new RegExp("(?<1a>x)")));
```

```text
===== node20 js28b-30a-groups.js (exit=0) =====
[1] the same date, grouped three ways
  /(\d+)-(\d+)-(\d+)/.exec(s)                   ["2026-09-26","2026","09","26"]
  /(?:\d+)-(\d+)-(?:\d+)/.exec(s)               ["2026-09-26","09"]
  named -- the array part                       ["2026-09-26","2026","09","26"]
  named -- m.groups                             {"y":"2026","mo":"09","d":"26"}
  named -- m.groups.mo                          09

[2] the groups object itself
  Object.getPrototypeOf(m.groups) === null      true
  'toString' in m.groups                        false
  String(m.groups)                              TypeError 「Cannot convert object to primitive value」
  JSON.stringify(m.groups)                      {"y":"2026","mo":"09","d":"26"}
  groups when the pattern has no named group    undefined
  key order of /(?<b>x)(?<a>y)/                 ["b","a"]

[3] an optional group -- /(?<a>a)?(?<b>b)/.exec('b')
  array                                         ["b","<undefined>","b"]
  Object.keys(groups)                           ["a","b"]
  groups.a                                      undefined
  'a' in groups                                 true

[4] a group inside a quantifier
  /(\w)+/.exec('abc')                           ["abc","c"]
  /(?:(a)|b)+/.exec('ab')                       ["ab","<undefined>"]
  /(?:(a)|(b))+/.exec('ab')                     ["ab","<undefined>","b"]

[5] referring back to a group
  /(?<q>['"]).*?\k<q>/.exec(`say "hi" 'yo'`)    ["\"hi\"","\""]
  /(a)|\1b/.exec('b')                           ["b","<undefined>"]
  s.replace(named, '$<d>.$<mo>.$<y>')           26.09.2026
  callback -- typeof the last argument          object {"y":"2026"}

[6] \k and group names at the edges
  new RegExp('\\k<z>').test('k<z>')             true
  new RegExp('\\k<z>', 'u')                     SyntaxError 「Invalid regular expression: /\k<z>/u: Invalid named capture referenced」
  new RegExp('(?<a>x)\\k<z>')                   SyntaxError 「Invalid regular expression: /(?<a>x)\k<z>/: Invalid named capture referenced」
  new RegExp('(?<a>x)(?<a>y)')                  SyntaxError 「Invalid regular expression: /(?<a>x)(?<a>y)/: Duplicate capture group name」
  new RegExp('(?<1a>x)')                        SyntaxError 「Invalid regular expression: /(?<1a>x)/: Invalid capture group name」
```

- ★★ **비캡처 `(?:…)` 는 칸을 만들지 않는다** — 같은 날짜가 `["2026-09-26","09"]` 두 칸이다. 묶기만 하고 꺼낼 필요가 없을 때 쓴다.
- ★★★ **명명 그룹은 번호 칸도 그대로 만든다** — 배열 부분이 번호 그룹과 **한 글자도 같다**. `groups` 는 **덧붙은 이름표**다.
- ★★★ **`groups` 의 프로토타입은 `null` 이다**(`true`) — `'toString' in m.groups` 가 `false` 이고 `String(m.groups)` 가 **`TypeError 「Cannot convert object to primitive value」`** 다.
  27편의 `Object.groupBy` 결과 · 15편의 `Object.create(null)` 과 **같은 증상**이다. 찍을 때는 `JSON.stringify`.
  ★ 명명 그룹이 없는 패턴이면 `groups` 가 **`undefined`** 다 — 빈 객체가 아니다.
- ★★ **`[3]` 참여하지 않은 그룹도 키는 있다** — `Object.keys` 가 `["a","b"]`, `'a' in groups` 가 `true`, 값만 `undefined`.
- ★★★ **`[4]` 반복 안의 그룹은 마지막 반복의 것만 남는다** — `/(\w)+/` 는 `"c"`.
  ★★★ 그리고 **반복마다 안쪽 캡처가 비워진다** — `/(?:(a)|b)+/.exec('ab')` 의 1번 칸이 **`<undefined>`** 다. 첫 반복에서 `a` 를 잡았지만 둘째 반복(`b`)이 시작될 때 지워졌다.
  (「마지막으로 잡은 값이 남는다」로 외우면 여기서 틀린다 — 남는 것은 **마지막 반복에서** 잡은 값이다.)
- ★★ **`[5]`** — `\k<q>` 는 **앞에서 잡은 글자와 같은 글자**를 요구한다(여는 따옴표와 같은 따옴표로 닫힌 `"hi"`).
  **참여하지 않은 그룹의 역참조는 빈 문자열처럼 통과한다** — `/(a)|\1b/.exec('b')` 가 `["b","<undefined>"]` 다.
  `replace` 의 `$<d>` 는 이름으로 꺼내고(`26.09.2026` — 28편의 `$` 치환 규칙), 콜백은 **마지막 인자로 `groups` 객체**를 받는다.
- ★★★ **`[6]` `\k<z>` 는 모드에 따라 뜻이 바뀐다** — 명명 그룹도 `u` 도 없으면 **그냥 글자 `k<z>`** 라서 `true`,
  `u` 가 있거나 **패턴 안에 명명 그룹이 하나라도 있으면** `SyntaxError 「… Invalid named capture referenced」` 다.
  ★ 같은 이름을 **한 갈래 안에 두 번** 쓰면 `Duplicate capture group name` — 이것은 ES2025 에서도 막힌다(동작 (6)).
- ★ **이 블록은 두 판이 한 줄 갈렸다** — 문구의 `/\k<z>/` 가 node20 에서 `/\k<z>/u` 다(플래그를 붙여 적는다). **종류는 같다.**

### (2) ★★ 둘러보기 — 무엇을 보고, 얼마나 먹고, 어느 쪽으로 읽나

**언제 쓰나** — 「뒤에 USD 가 오는 숫자만」·「천 단위 쉼표를 넣을 자리」처럼 **조건은 걸되 그 글자는 결과에 넣고 싶지 않을 때**.

```text
   "30 USD, 45 EUR, $12, 7"

   \d+(?= USD)      30 ──┐ 뒤에 " USD" 가 있나?  보기만 하고 안 먹는다
   (?<=\$)\d+       $12 ─┘ 앞에 "$" 가 있나?     ↓
                          매치 결과 = "30" · "12"  (USD · $ 는 결과 밖)

   룩비하인드 안은 오른쪽에서 왼쪽으로 읽는다
   (?<=(\d+)(\d+))$  on "1053"
        ◀────────── 뒤의 (\d+) 가 먼저 욕심껏 -> "053", 앞의 (\d+) 는 남은 "1"
```

```js
// js28b-30b-lookaround.js
// Lookahead and lookbehind -- what they match, what they consume, and which direction they read.
const J = (x) => JSON.stringify(x);
const U = (a) => (a === null ? null : [...a].map((v) => (v === undefined ? "<undefined>" : v)));
const show = (label, f) => {
  try { console.log("  " + label.padEnd(44) + f()); }
  catch (e) { console.log("  " + label.padEnd(44) + e.constructor.name + " 「" + e.message + "」"); }
};
const t = "30 USD, 45 EUR, $12, 7";

console.log("[1] four lookarounds on t = " + J(t));
show("t.match(/\\d+(?= USD)/g)", () => J(t.match(/\d+(?= USD)/g)));
show("t.match(/\\b\\d+\\b(?! USD)/g)", () => J(t.match(/\b\d+\b(?! USD)/g)));
show("t.match(/(?<=\\$)\\d+/g)", () => J(t.match(/(?<=\$)\d+/g)));
show("t.match(/(?<!\\$)\\b\\d+/g)", () => J(t.match(/(?<!\$)\b\d+/g)));

console.log("");
console.log("[2] how much does a lookaround consume?");
const z = /(?=b)/.exec("abc");
show("/(?=b)/.exec('abc') -- index, [0]", () => z.index + " " + J(z[0]));
show("'abc'.replace(/(?=b)/, '|')", () => "abc".replace(/(?=b)/, "|"));
show("'1234567'.replace(/\\B(?=(\\d{3})+$)/g, ',')", () => "1234567".replace(/\B(?=(\d{3})+$)/g, ","));
show("/(?=(a+))/.exec('baaa')", () => J(U(/(?=(a+))/.exec("baaa"))));

console.log("");
console.log("[3] lookbehind of varying length");
show("/(?<=\\$\\d+\\.)\\d+/.exec('cost $12.50')", () => J(U(/(?<=\$\d+\.)\d+/.exec("cost $12.50"))));
show("/(?<=^a+)b/.test('aaaab')", () => /(?<=^a+)b/.test("aaaab"));
show("/(?<=a|bc)x/g on 'ax bcx cx'", () => J("ax bcx cx".match(/(?<=a|bc)x/g)));

console.log("");
console.log("[4] groups inside a lookbehind -- '1053'");
show("/(?<=(\\d+)(\\d+))$/.exec('1053')", () => J(U(/(?<=(\d+)(\d+))$/.exec("1053"))));
show("/(?<=(\\d+?)(\\d+))$/.exec('1053')", () => J(U(/(?<=(\d+?)(\d+))$/.exec("1053"))));
show("/((\\d+)(\\d+))$/.exec('1053')", () => J(U(/((\d+)(\d+))$/.exec("1053"))));

console.log("");
console.log("[5] several conditions on one string: /^(?=.*\\d)(?=.*[a-z])\\S{6,}$/");
const rule = /^(?=.*\d)(?=.*[a-z])\S{6,}$/;
for (const w of ["abc123", "abcdef", "123456", "ab1", "ABC123", "abc 123"]) show(J(w), () => rule.test(w));
```

```text
===== node20 js28b-30b-lookaround.js (exit=0) =====
[1] four lookarounds on t = "30 USD, 45 EUR, $12, 7"
  t.match(/\d+(?= USD)/g)                     ["30"]
  t.match(/\b\d+\b(?! USD)/g)                 ["45","12","7"]
  t.match(/(?<=\$)\d+/g)                      ["12"]
  t.match(/(?<!\$)\b\d+/g)                    ["30","45","7"]

[2] how much does a lookaround consume?
  /(?=b)/.exec('abc') -- index, [0]           1 ""
  'abc'.replace(/(?=b)/, '|')                 a|bc
  '1234567'.replace(/\B(?=(\d{3})+$)/g, ',')  1,234,567
  /(?=(a+))/.exec('baaa')                     ["","aaa"]

[3] lookbehind of varying length
  /(?<=\$\d+\.)\d+/.exec('cost $12.50')       ["50"]
  /(?<=^a+)b/.test('aaaab')                   true
  /(?<=a|bc)x/g on 'ax bcx cx'                ["x","x"]

[4] groups inside a lookbehind -- '1053'
  /(?<=(\d+)(\d+))$/.exec('1053')             ["","1","053"]
  /(?<=(\d+?)(\d+))$/.exec('1053')            ["","1","053"]
  /((\d+)(\d+))$/.exec('1053')                ["1053","1053","105","3"]

[5] several conditions on one string: /^(?=.*\d)(?=.*[a-z])\S{6,}$/
  "abc123"                                    true
  "abcdef"                                    false
  "123456"                                    false
  "ab1"                                       false
  "ABC123"                                    false
  "abc 123"                                   false
```

- ★★ **`[1]` 네 가지가 보는 방향과 부정** — `(?= USD)` 는 `["30"]`, `(?! USD)` 는 `["45","12","7"]`, `(?<=\$)` 는 `["12"]`, `(?<!\$)` 는 `["30","45","7"]`.
  ★ `\b\d+\b(?! USD)` 에서 `30` 이 빠진 것은 **`\b` 두 개가 `\d+` 를 `3` 으로 줄여 빠져나갈 길을 막았기** 때문이다(`3` 과 `0` 사이는 단어 경계가 아니다).
- ★★★ **`[2]` 둘러보기는 한 글자도 안 먹는다** — `(?=b)` 의 매치는 **길이 0**(`""`, index `1`)이고, `replace` 가 그 **자리**에 `|` 를 끼운다(`a|bc`).
  천 단위 쉼표 `1,234,567` 이 이 성질 하나로 된다. ★ `(?=(a+))` 처럼 **둘러보기 안의 캡처는 남는다**(`["","aaa"]`) — 먹지는 않았는데 잡기는 했다.
- ★★★ **`[3]` JS 의 룩비하인드는 길이가 변해도 된다** — `(?<=\$\d+\.)` 가 `["50"]`, `(?<=^a+)` 가 `true`, `(?<=a|bc)` 가 두 번 걸린다.
  ★★ **파이썬 `re` 는 이것을 거절한다**(`look-behind requires fixed-width pattern` — 동작 (9)). 두 언어가 갈리는 대표 자리다.
- ★★★ **`[4]` 룩비하인드 안의 캡처는 오른쪽부터 채워진다** — 같은 `(\d+)(\d+)` 가 **앞으로 읽으면** `"105"`·`"3"` 인데 **룩비하인드 안에서는** `"1"`·`"053"` 이다.
  명세가 룩비하인드를 **역방향(backward)으로 평가**하게 적어 두었기 때문이다 — 욕심을 먼저 부리는 것은 **오른쪽** 그룹이다.
  ★ 앞 그룹을 게으르게(`\d+?`) 바꿔도 답이 같다 — 오른쪽이 이미 다 가져간 뒤라 앞에 남은 것이 `"1"` 뿐이다.
- ★★ **`[5]` 조건 여러 개를 한 줄에** — 룩어헤드 둘을 `^` 뒤에 겹쳐 「숫자 하나 이상 **그리고** 소문자 하나 이상」을 건다. 여섯 입력 중 `"abc123"` 만 `true`.
  ★ 둘러보기는 **자리를 옮기지 않으므로** 겹쳐 놓은 조건이 전부 **같은 자리(문자열 처음)** 에서 검사된다.

### (3) ★★★ `u` 와 `v` — 서로게이트 한 쌍을 한 글자로 보나

**언제 쓰나** — 이모지·한자 확장 같은 **BMP 밖 글자가 들어올 수 있는 텍스트**를 정규식으로 자르거나 셀 때.

```text
   face = String.fromCodePoint(0x1f600)      length 2     코드 유닛 [d83d de00]   (04편)

   플래그 없음                  u / v
   ------------                ------
   글자 = 코드 유닛 하나         글자 = 코드 포인트 하나
   .   -> [d83d] 만 먹는다       .   -> [d83d de00] 둘을 한 번에
   ^.$ -> false                 ^.$ -> true
   ^..$ -> true                 ^..$ -> false
   [face] = 칸 두 개짜리 집합     [face] = 글자 하나짜리 집합
```

```js
// js28b-30c-unicode.js
// One astral character against a regexp -- without a flag, with u, with v.
// The character is built at run time and printed only as code units, so this file holds no astral text.
const J = (x) => JSON.stringify(x);
const units = (s) => (s === null || s === undefined ? String(s)
  : "[" + Array.from({ length: s.length }, (_, i) => s.charCodeAt(i).toString(16)).join(" ") + "]");
const mk = (src, flags) => { try { return new RegExp(src, flags); } catch (e) { return e; } };
const show = (label, f) => {
  try { console.log("  " + label.padEnd(44) + f()); }
  catch (e) { console.log("  " + label.padEnd(44) + e.constructor.name + " 「" + e.message + "」"); }
};
const face = String.fromCodePoint(0x1f600);
const hi = face.slice(0, 1);
let rows = 0, split = 0;
const test3 = (src, input) => {
  const cells = ["", "u", "v"].map((fl) => {
    const r = mk(src, fl);
    return r instanceof Error ? r.constructor.name : String(r.test(input));
  });
  rows += 1; if (cells[0] !== cells[1]) split += 1;
  return ["-", "u", "v"].map((fl, i) => fl + ":" + cells[i]).join("  ");
};

console.log("[1] the input");
show("face = String.fromCodePoint(0x1f600)", () => "length " + face.length + "  units " + units(face));

console.log("");
console.log("[2] the same pattern, three flag settings (no flag / u / v)");
show("^.$ on face", () => test3("^.$", face));
show("^..$ on face", () => test3("^..$", face));
show("^[face]$ on face", () => test3("^[" + face + "]$", face));
show("^face{2}$ on face+face", () => test3("^" + face + "{2}$", face + face));
show("^\\S$ on face", () => test3("^\\S$", face));
show("high half alone, on face", () => test3(hi, face));
show("^.$ on the high half alone", () => test3("^.$", hi));
console.log("  rows where no-flag and u differ: " + split + " / " + rows);

console.log("");
console.log("[3] what did . take?");
show("face.match(/./)[0]", () => units(face.match(/./)[0]));
show("face.match(/./u)[0]", () => units(face.match(/./u)[0]));
show("(face + 'x').match(/./g).length", () => (face + "x").match(/./g).length);
show("(face + 'x').match(/./gu).length", () => (face + "x").match(/./gu).length);
show("face.split(/(?:)/)", () => face.split(/(?:)/).map(units).join(" "));
show("face.split(/(?:)/u)", () => face.split(/(?:)/u).map(units).join(" "));

console.log("");
console.log("[4] the escape \\u{1F600}");
show("/\\u{1F600}/u.test(face)", () => /\u{1F600}/u.test(face));
show("/\\u{1F600}/.test(face)", () => /\u{1F600}/.test(face));
show("/\\u{1F600}/.test('u{1F600}')", () => /\u{1F600}/.test("u{1F600}"));
show("/^\\u{3}$/.test('uuu')", () => /^\u{3}$/.test("uuu"));

console.log("");
console.log("[5] unicode property escapes \\p{...}");
const hangul = String.fromCharCode(0xd55c);
const eAcute = String.fromCharCode(0xe9);
show("/\\p{L}/u on 'a' / e-acute / hangul / '1'", () => ["a", eAcute, hangul, "1"].map((c) => /\p{L}/u.test(c)).join(" "));
show("/\\p{Script=Hangul}/u on hangul / 'a'", () => [hangul, "a"].map((c) => /\p{Script=Hangul}/u.test(c)).join(" "));
show("/\\p{L}/ (no flag) on 'p{L}' / 'a'", () => ["p{L}", "a"].map((c) => /\p{L}/.test(c)).join(" "));
show("new RegExp('\\\\p{Nope}', 'u')", () => String(new RegExp("\\p{Nope}", "u")));
show("/^\\p{Emoji}$/u on face / '1'", () => [face, "1"].map((c) => /^\p{Emoji}$/u.test(c)).join(" "));
```

```text
===== node20 js28b-30c-unicode.js (exit=0) =====
[1] the input
  face = String.fromCodePoint(0x1f600)        length 2  units [d83d de00]

[2] the same pattern, three flag settings (no flag / u / v)
  ^.$ on face                                 -:false  u:true  v:true
  ^..$ on face                                -:true  u:false  v:false
  ^[face]$ on face                            -:false  u:true  v:true
  ^face{2}$ on face+face                      -:false  u:true  v:true
  ^\S$ on face                                -:false  u:true  v:true
  high half alone, on face                    -:true  u:false  v:false
  ^.$ on the high half alone                  -:true  u:true  v:true
  rows where no-flag and u differ: 6 / 7

[3] what did . take?
  face.match(/./)[0]                          [d83d]
  face.match(/./u)[0]                         [d83d de00]
  (face + 'x').match(/./g).length             3
  (face + 'x').match(/./gu).length            2
  face.split(/(?:)/)                          [d83d] [de00]
  face.split(/(?:)/u)                         [d83d de00]

[4] the escape \u{1F600}
  /\u{1F600}/u.test(face)                     true
  /\u{1F600}/.test(face)                      false
  /\u{1F600}/.test('u{1F600}')                true
  /^\u{3}$/.test('uuu')                       true

[5] unicode property escapes \p{...}
  /\p{L}/u on 'a' / e-acute / hangul / '1'    true true true false
  /\p{Script=Hangul}/u on hangul / 'a'        true false
  /\p{L}/ (no flag) on 'p{L}' / 'a'           true false
  new RegExp('\\p{Nope}', 'u')                SyntaxError 「Invalid regular expression: /\p{Nope}/u: Invalid property name」
  /^\p{Emoji}$/u on face / '1'                true true
```

- ★★★ **`[2]` 일곱 줄 중 여섯 줄에서 플래그 없음과 `u` 가 갈렸다**(`rows where no-flag and u differ: 6 / 7`) — 스크립트가 센 수다.
  플래그가 없으면 **글자 = 코드 유닛**이라 `.` 이 반쪽만 먹고(`^.$` 가 `false`, `^..$` 가 `true`), `[face]` 는 **반쪽 둘의 집합**이며, `face{2}` 의 `{2}` 는 **뒤쪽 반쪽에만** 붙는다.
  `u` 는 **글자 = 코드 포인트**라 전부 뒤집힌다. ★★ **`v` 열은 `u` 열과 일곱 줄 전부 같다** — 서로게이트를 보는 방식에서 `v` 는 `u` 와 한 편이다.
- ★★★ **`u` 는 쌍을 쪼개지 않는다** — `high half alone, on face` 가 플래그 없이는 `true`(반쪽이 반쪽을 찾았다), `u`·`v` 에서는 **`false`** 다. 쌍의 앞쪽만 따로 찾을 수 없다.
  ★ 그런데 **짝 없는 반쪽 하나만 있는 문자열**에서는 셋 다 `^.$` 가 `true` 다 — `u` 에서도 **외톨이 서로게이트는 그 자체로 한 글자**다.
- ★★ **`[3]` `.` 이 가져간 것** — 플래그 없이 `[d83d]`, `u` 로 `[d83d de00]`. `(face + 'x')` 를 `/./g` 로 세면 `3`, `/./gu` 로 세면 `2`.
  `split(/(?:)/)` 과 `split(/(?:)/u)` 의 차이는 **04편의 쪼개기 그림 그대로**다(여기서는 코드 유닛 16진수로 다시 봤을 뿐이다).
- ★★★ **`[4]` `\u{1F600}` 은 `u` 가 있을 때만 그 뜻이다** — 플래그가 없으면 `\u` 는 **그냥 글자 `u`** 이고 `{1F600}` 은 수량자로 읽히지 않아 **글자 그대로** 남는다 — `'u{1F600}'` 에 `true`.
  ★ 더 얄궂은 것은 `/^\u{3}$/` — 플래그가 없으면 `{3}` 이 **진짜 수량자**가 되어 `'uuu'` 에 `true` 다.
- ★★ **`[5]` `\p{…}` 도 `u`(또는 `v`) 가 있어야 한다** — 없으면 `\p` 가 그냥 글자 `p` 라서 `/\p{L}/` 이 **글자 `p{L}` 을 찾는다**(`'p{L}'` 에 `true`, `'a'` 에 `false`). **에러가 안 난다**는 것이 함정이다.
  `u` 가 있으면 `\p{L}` 이 `a`·é·한글에 `true`, `1` 에 `false` 다. 모르는 속성 이름은 `SyntaxError 「… Invalid property name」`.
  ★ `\p{Emoji}` 는 숫자 `'1'` 에도 `true` 다 — 유니코드의 `Emoji` 속성은 **키캡 이모지의 재료가 되는 숫자**까지 포함한다. 「이모지만」 고르려면 동작 (4)의 `RGI_Emoji` 를 본다.
- ★★ **node18 은 `v` 열이 전부 `SyntaxError`** 다 — 판이 갈린 블록이다(node18 블록은 [3-answer.md](3-answer.md) 3번에 있다).

### (4) ★★ `v` 플래그(ES2024) — 집합 연산, 글자열 속성, 그리고 더 엄격한 문법

**언제 쓰나** — 「글자인데 ASCII 는 아닌 것」처럼 **문자 집합끼리 빼고 겹칠 때**, 그리고 **여러 코드 포인트로 된 이모지 하나**를 한 덩어리로 잡을 때.

```text
   [\p{L}--\p{ASCII}]      \p{L} ████████████████          뺄셈  --
                           \p{ASCII}  ████                 교집합 &&
                           결과          ████████████      중첩  [[a-z]--[aeiou]]

   \p{RGI_Emoji}  = 「글자열」의 집합      family = 코드 유닛 8칸 (사람 셋 + 잇개 둘)
                                          u 의 \p{Emoji} 는 코드 포인트 하나만 -> family 에 false
                                          v 의 \p{RGI_Emoji} 는 여덟 칸을 한 원소로 -> true
```

```js
// js28b-30d-vflag.js
// The v flag -- set operations, strings inside a class, and what v refuses that u accepts.
// Every v pattern is built with new RegExp so that an engine without v still runs the whole file.
const units = (s) => "[" + Array.from({ length: s.length }, (_, i) => s.charCodeAt(i).toString(16)).join(" ") + "]";
const show = (label, f) => {
  try { console.log("  " + label.padEnd(46) + f()); }
  catch (e) { console.log("  " + label.padEnd(46) + e.constructor.name + " 「" + e.message + "」"); }
};
const eAcute = String.fromCharCode(0xe9);
const hangul = String.fromCharCode(0xd55c);
const face = String.fromCodePoint(0x1f600);
const family = String.fromCodePoint(0x1f468, 0x200d, 0x1f469, 0x200d, 0x1f467);
const on = (src, flags, inputs) => { const r = new RegExp(src, flags); return inputs.map((c) => r.test(c)).join(" "); };

console.log("[1] set operations -- inputs 'a' / e-acute / hangul / '1'");
const four = ["a", eAcute, hangul, "1"];
show("^[\\p{L}--\\p{ASCII}]$  v", () => on("^[\\p{L}--\\p{ASCII}]$", "v", four));
show("^[\\p{L}&&\\p{ASCII}]$  v", () => on("^[\\p{L}&&\\p{ASCII}]$", "v", four));
show("^[\\p{L}--\\p{ASCII}]$  u", () => on("^[\\p{L}--\\p{ASCII}]$", "u", four));
show("^[[a-z]--[aeiou]]+$  v   on 'rhythm' / 'rain'", () => on("^[[a-z]--[aeiou]]+$", "v", ["rhythm", "rain"]));

console.log("");
console.log("[2] strings in a class -- family = " + units(family) + "  (length " + family.length + ")");
show("^\\p{RGI_Emoji}$  v   on family / face", () => on("^\\p{RGI_Emoji}$", "v", [family, face]));
show("^\\p{Emoji}$      u   on family / face", () => on("^\\p{Emoji}$", "u", [family, face]));
show("^\\p{RGI_Emoji}$  u", () => on("^\\p{RGI_Emoji}$", "u", [family]));
show("^[\\q{abc|d}]$    v   on 'abc' / 'd' / 'a'", () => on("^[\\q{abc|d}]$", "v", ["abc", "d", "a"]));
show("family.match(v)[0]  for [\\p{RGI_Emoji}]", () => units(family.match(new RegExp("[\\p{RGI_Emoji}]", "v"))[0]));

console.log("");
console.log("[3] the same source under u and under v");
let total = 0, onlyU = 0;
for (const src of ["[(]", "[a-]", "[|]", "[a&&&b]", "[\\-]"]) {
  const r = (fl) => { try { new RegExp(src, fl); return "ok"; } catch (e) { return e.constructor.name; } };
  total += 1; if (r("u") === "ok" && r("v") !== "ok") onlyU += 1;
  show(src, () => "u:" + r("u") + "  v:" + r("v"));
}
console.log("  sources accepted under u but not under v: " + onlyU + " / " + total);
show("new RegExp('[(]', 'v') -- message", () => String(new RegExp("[(]", "v")));
show("new RegExp('a', 'uv')", () => String(new RegExp("a", "uv")));

console.log("");
console.log("[4] the flag's properties");
show("new RegExp('a', 'v').unicodeSets / .unicode", () => { const r = new RegExp("a", "v"); return r.unicodeSets + " / " + r.unicode; });
show("new RegExp('a', 'v').flags", () => new RegExp("a", "v").flags);
```

```text
===== node20 js28b-30d-vflag.js (exit=0) =====
[1] set operations -- inputs 'a' / e-acute / hangul / '1'
  ^[\p{L}--\p{ASCII}]$  v                       false true true false
  ^[\p{L}&&\p{ASCII}]$  v                       true false false false
  ^[\p{L}--\p{ASCII}]$  u                       SyntaxError 「Invalid regular expression: /^[\p{L}--\p{ASCII}]$/u: Invalid character class」
  ^[[a-z]--[aeiou]]+$  v   on 'rhythm' / 'rain' true false

[2] strings in a class -- family = [d83d dc68 200d d83d dc69 200d d83d dc67]  (length 8)
  ^\p{RGI_Emoji}$  v   on family / face         true true
  ^\p{Emoji}$      u   on family / face         false true
  ^\p{RGI_Emoji}$  u                            SyntaxError 「Invalid regular expression: /^\p{RGI_Emoji}$/u: Invalid property name」
  ^[\q{abc|d}]$    v   on 'abc' / 'd' / 'a'     true true false
  family.match(v)[0]  for [\p{RGI_Emoji}]       [d83d dc68 200d d83d dc69 200d d83d dc67]

[3] the same source under u and under v
  [(]                                           u:ok  v:SyntaxError
  [a-]                                          u:ok  v:SyntaxError
  [|]                                           u:ok  v:SyntaxError
  [a&&&b]                                       u:ok  v:SyntaxError
  [\-]                                          u:ok  v:ok
  sources accepted under u but not under v: 4 / 5
  new RegExp('[(]', 'v') -- message             SyntaxError 「Invalid regular expression: /[(]/v: Invalid character in character class」
  new RegExp('a', 'uv')                         SyntaxError 「Invalid flags supplied to RegExp constructor 'uv'」

[4] the flag's properties
  new RegExp('a', 'v').unicodeSets / .unicode   true / false
  new RegExp('a', 'v').flags                    v
```

- ★★★ **`[1]` 집합 연산** — `[\p{L}--\p{ASCII}]` 는 é·한글만 `true`(`false true true false`), `&&` 는 `a` 만.
  `[[a-z]--[aeiou]]+` 로 모음 없는 낱말(`rhythm`)만 걸린다.
  ★★ **같은 글자를 `u` 로 쓰면 조용히 다르게 되는 것이 아니라 `SyntaxError 「… Invalid character class」`** 다 — `u` 모드에서 `\p{L}-` 는 「속성으로 범위를 시작한」 잘못된 범위다.
- ★★★ **`[2]` 글자열 속성** — `\p{RGI_Emoji}` 는 **코드 유닛 여덟 칸**(`[d83d dc68 200d d83d dc69 200d d83d dc67]`)짜리 가족 이모지를 **한 원소**로 잡는다(`true`).
  `u` 의 `\p{Emoji}` 는 **코드 포인트 하나**짜리만 보므로 가족 전체에는 `false` 다. 그리고 `\p{RGI_Emoji}` 를 `u` 로 쓰면 `Invalid property name` — **`v` 에만 있는 속성**이다.
  ★ `\q{abc|d}` 는 클래스 안에 **글자열**을 넣는 문법이다 — `'abc'` 와 `'d'` 에 `true`, `'a'` 에 `false`.
- ★★★ **`[3]` `v` 는 `u` 가 받던 것을 거절한다** — 다섯 중 넷(`sources accepted under u but not under v: 4 / 5`).
  `[(]`·`[a-]`·`[|]`·`[a&&&b]` 처럼 **클래스 안의 구두점을 이스케이프 없이 쓴 것**이 전부 `SyntaxError 「… Invalid character in character class」` 다. `[\-]` 처럼 **이스케이프하면 통과**한다.
  ★ 집합 연산자(`--`·`&&`)와 헷갈리지 않게 문법을 좁힌 것이다. **`u` 패턴에 `v` 만 바꿔 달면 깨질 수 있다.**
- ★★ **`u` 와 `v` 는 같이 못 단다** — `new RegExp('a', 'uv')` 가 `Invalid flags supplied to RegExp constructor 'uv'`. `v` 를 달면 `unicode` 는 `false`, `unicodeSets` 가 `true` 다.
- ★★ **node18 은 이 블록의 `v` 줄이 전부 `Invalid flags supplied to RegExp constructor 'v'`** 다 — `v` 가 ES2024 이고 node18(V8 10.2)에 없다.

### (5) ★ `d` 플래그(ES2022) — 그룹마다 어디서 시작해 어디서 끝났나

**언제 쓰나** — 하이라이트·에디터처럼 **찾은 조각의 위치**가 필요할 때. `index` 는 매치 전체의 시작만 준다.

```text
   "a=1; key=val"      /(?<k>\w+)=(?<v>\w+)/d
    0123456789...
    a = 1               indices     [[0,3], [0,1], [2,3]]      [시작, 끝)  끝은 안 포함
    └┘ └┘               indices.groups  { k: [0,1], v: [2,3] }
                        slice(...indices.groups.v) -> "1"
```

```js
// js28b-30e-indices.js
// The d flag -- where each group started and ended.
const J = (x) => JSON.stringify(x);
const show = (label, f) => {
  try { console.log("  " + label.padEnd(40) + f()); }
  catch (e) { console.log("  " + label.padEnd(40) + e.constructor.name + " 「" + e.message + "」"); }
};
const line = "a=1; key=val";
const re = /(?<k>\w+)=(?<v>\w+)/d;

console.log("[1] one match with d -- input " + J(line));
const m = re.exec(line);
show("m[0] / m.index", () => J(m[0]) + " / " + m.index);
show("m.indices", () => J(m.indices));
show("m.indices.groups", () => J(m.indices.groups));
show("Object.getPrototypeOf(m.indices.groups)", () => String(Object.getPrototypeOf(m.indices.groups)));
show("line.slice(...m.indices.groups.v)", () => J(line.slice(...m.indices.groups.v)));

console.log("");
console.log("[2] the same pattern without d");
const plain = /(?<k>\w+)=(?<v>\w+)/.exec(line);
show("plain.indices", () => String(plain.indices));
show("'indices' in plain", () => "indices" in plain);

console.log("");
console.log("[3] every match, and an optional group");
show("matchAll(/(\\w+)=(\\w+)/dg) -> indices", () => J([...line.matchAll(/(\w+)=(\w+)/dg)].map((x) => x.indices)));
show("/(a)?b/d.exec('b').indices", () => J([.../(a)?b/d.exec("b").indices].map((v) => (v === undefined ? "<undefined>" : v))));

console.log("");
console.log("[4] the numbers count code units -- input: face + 'x=1'");
const face = String.fromCodePoint(0x1f600);
show("/(\\w)=(\\d)/d.exec(face + 'x=1').indices", () => J(/(\w)=(\d)/d.exec(face + "x=1").indices));
show("same with du", () => J(/(\w)=(\d)/du.exec(face + "x=1").indices));

console.log("");
console.log("[5] the flag's properties");
show("re.hasIndices / re.flags", () => re.hasIndices + " / " + re.flags);
show("new RegExp('a', 'ygsmid').flags", () => new RegExp("a", "ygsmid").flags);
```

```text
===== node20 js28b-30e-indices.js (exit=0) =====
[1] one match with d -- input "a=1; key=val"
  m[0] / m.index                          "a=1" / 0
  m.indices                               [[0,3],[0,1],[2,3]]
  m.indices.groups                        {"k":[0,1],"v":[2,3]}
  Object.getPrototypeOf(m.indices.groups) null
  line.slice(...m.indices.groups.v)       "1"

[2] the same pattern without d
  plain.indices                           undefined
  'indices' in plain                      false

[3] every match, and an optional group
  matchAll(/(\w+)=(\w+)/dg) -> indices    [[[0,3],[0,1],[2,3]],[[5,12],[5,8],[9,12]]]
  /(a)?b/d.exec('b').indices              [[0,1],"<undefined>"]

[4] the numbers count code units -- input: face + 'x=1'
  /(\w)=(\d)/d.exec(face + 'x=1').indices [[2,5],[2,3],[4,5]]
  same with du                            [[2,5],[2,3],[4,5]]

[5] the flag's properties
  re.hasIndices / re.flags                true / d
  new RegExp('a', 'ygsmid').flags         dgimsy
```

- ★★ **`indices` 는 `[시작, 끝)` 쌍의 배열**이고 `groups` 와 같은 이름으로 `indices.groups` 가 있다 — 그 객체도 **프로토타입이 `null`** 이다.
  `line.slice(...m.indices.groups.v)` 로 곧장 잘라 쓴다.
- ★★ **`d` 가 없으면 `indices` 는 아예 없다**(`'indices' in plain` 이 `false`) — 계산 비용 때문에 **달라고 해야 준다**는 설계다(비용은 안 쟀다).
- ★★ **참여하지 않은 그룹의 칸은 `undefined`** 다(`[[0,1],"<undefined>"]`).
- ★★★ **숫자는 코드 유닛을 센다** — 앞에 `face`(두 칸)를 붙이면 `x` 가 **2** 에서 시작한다. **`u` 를 달아도 같다**(`du`) — `u` 는 「무엇을 한 글자로 보나」를 바꾸지 **자리를 세는 단위를 바꾸지 않는다.** 04편의 「`length` 는 코드 유닛」과 같은 단위다.
- ★ `flags` 는 **넣은 순서와 상관없이 정해진 순서**로 나온다 — `'ygsmid'` 가 `dgimsy`.

### (6) ★★ ES2025 — `RegExp.escape` · 중복 명명 그룹 · 수정자

**언제 쓰나** — 사용자 입력을 **글자 그대로** 패턴에 넣을 때 · 두 형식을 한 이름으로 받을 때 · 패턴 **일부만** 대소문자를 무시할 때.

```text
   RegExp.escape("a.b*c")  ->  \x61\.b\*c
                               └──┘ 첫 글자가 영숫자면 \x 로          <- 앞에 무엇이 붙어도 뜻이 안 바뀌게
                                    \. \*  구두점은 \ 로

   /(?<y>\d{4})-\d\d|\d\d\/(?<y>\d{4})/     같은 이름 y 가 두 갈래에   (ES2025 부터)
     "2026-09"  -> groups.y = "2026"         한 매치에서 참여하는 것은 한 갈래뿐
     "09/2026"  -> groups.y = "2026"
```

```js
// js28b-30f-es2025.web.js
// ES2025 regexp additions -- RegExp.escape, duplicate named groups, modifiers. Chrome only (neither node has them).
const J = (x) => JSON.stringify(x);
const show = (label, f) => {
  try { console.log("  " + label.padEnd(46) + f()); }
  catch (e) { console.log("  " + label.padEnd(46) + e.constructor.name + " 「" + e.message + "」"); }
};

console.log("[1] RegExp.escape");
for (const s of ["a.b*c", "1+1=2", "$5 (approx)", "x|y", "- ,", "foo_bar"]) show("RegExp.escape(" + J(s) + ")", () => RegExp.escape(s));
const user = "a.b";
show("new RegExp(user).test('axb')", () => new RegExp(user).test("axb"));
show("new RegExp(RegExp.escape(user)).test('axb')", () => new RegExp(RegExp.escape(user)).test("axb"));
show("new RegExp(RegExp.escape(user)).test('a.b')", () => new RegExp(RegExp.escape(user)).test("a.b"));
show("RegExp.escape(12)", () => RegExp.escape(12));

console.log("");
console.log("[2] one name in two alternatives");
const date = /(?<y>\d{4})-\d\d|\d\d\/(?<y>\d{4})/;
show("date.exec('2026-09').groups", () => J(date.exec("2026-09").groups));
show("date.exec('09/2026').groups", () => J(date.exec("09/2026").groups));
show("date.exec('09/2026') -- array", () => J([...date.exec("09/2026")].map((v) => (v === undefined ? "<undefined>" : v))));
show("'09/2026'.replace(date, '[$<y>]')", () => "09/2026".replace(date, "[$<y>]"));
show("new RegExp('(?<y>a)(?<y>b)')", () => String(new RegExp("(?<y>a)(?<y>b)")));
show("new RegExp('(?:(?<y>a)|(?<y>b))\\\\k<y>').exec('bb')", () => J([...new RegExp("(?:(?<y>a)|(?<y>b))\\k<y>").exec("bb")].map((v) => (v === undefined ? "<undefined>" : v))));

console.log("");
console.log("[3] modifiers -- a flag for part of a pattern");
const mod = /a(?i:b)c/;
for (const s of ["abc", "aBc", "ABc", "abC"]) show("/a(?i:b)c/.test(" + J(s) + ")", () => mod.test(s));
show("/a(?-i:b)c/i.test('AbC') / ('ABC')", () => /a(?-i:b)c/i.test("AbC") + " / " + /a(?-i:b)c/i.test("ABC"));
show("new RegExp('(?g:a)')", () => String(new RegExp("(?g:a)")));
```

```text
===== google-chrome --headless --virtual-time-budget=2000 --dump-dom 'js28b-page.html?js28b-30f-es2025.web.js' | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' | sed 's/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&amp;/\&/g' (exit=0) =====
[1] RegExp.escape
  RegExp.escape("a.b*c")                        \x61\.b\*c
  RegExp.escape("1+1=2")                        \x31\+1\x3d2
  RegExp.escape("$5 (approx)")                  \$5\x20\(approx\)
  RegExp.escape("x|y")                          \x78\|y
  RegExp.escape("- ,")                          \x2d\x20\x2c
  RegExp.escape("foo_bar")                      \x66oo_bar
  new RegExp(user).test('axb')                  true
  new RegExp(RegExp.escape(user)).test('axb')   false
  new RegExp(RegExp.escape(user)).test('a.b')   true
  RegExp.escape(12)                             TypeError 「input argument must be a string」

[2] one name in two alternatives
  date.exec('2026-09').groups                   {"y":"2026"}
  date.exec('09/2026').groups                   {"y":"2026"}
  date.exec('09/2026') -- array                 ["09/2026","<undefined>","2026"]
  '09/2026'.replace(date, '[$<y>]')             [2026]
  new RegExp('(?<y>a)(?<y>b)')                  SyntaxError 「Invalid regular expression: /(?<y>a)(?<y>b)/: Duplicate capture group name」
  new RegExp('(?:(?<y>a)|(?<y>b))\\k<y>').exec('bb')["bb","<undefined>","b"]

[3] modifiers -- a flag for part of a pattern
  /a(?i:b)c/.test("abc")                        true
  /a(?i:b)c/.test("aBc")                        true
  /a(?i:b)c/.test("ABc")                        false
  /a(?i:b)c/.test("abC")                        false
  /a(?-i:b)c/i.test('AbC') / ('ABC')            true / false
  new RegExp('(?g:a)')                          SyntaxError 「Invalid regular expression: /(?g:a)/: Invalid group」
```

- ★★★ **`RegExp.escape` 는 첫 글자가 영숫자면 `\x..` 로 바꾼다** — `"a.b*c"` 가 `\x61\.b\*c`, `"1+1=2"` 가 `\x31\+1\x3d2`. 가운데 영숫자는 그대로다.
  ★ 왜 첫 글자만 그렇게 하는지는 이 문서가 **확인하지 않았다** — 출력으로 본 것은 「첫 영숫자만 `\x` 가 된다」까지다.
  ★★ 공백·쉼표·`-`·`=` 도 `\x20`·`\x2c`·`\x2d`·`\x3d` 로 바뀐다. 결과를 사람이 읽을 것이라 기대하지 마라.
- ★★★ **그 효과** — `user = "a.b"` 를 그대로 넣으면 `.` 이 아무 글자라서 `'axb'` 에 `true`, 이스케이프하면 `false`·`'a.b'` 에만 `true`.
  문자열이 아니면 `TypeError 「input argument must be a string」`(숫자를 문자열로 바꿔 주지 않는다).
- ★★ **중복 명명 그룹은 「다른 갈래」에서만** — 두 형식이 다 `groups.y = "2026"` 이고, 배열에는 **칸이 둘**(참여 안 한 쪽은 `<undefined>`). 같은 갈래 안의 중복은 여전히 `Duplicate capture group name`.
  `$<y>` 치환과 `\k<y>` 역참조는 **참여한 쪽**을 가리킨다(`bb` 가 매치).
- ★★ **수정자 `(?i:…)`** — 괄호 안만 대소문자를 무시한다(`aBc` 는 `true`, `ABc` 는 `false`). `(?-i:…)` 는 반대로 끈다. 켤 수 있는 것은 `i`·`m`·`s` 셋이고 `(?g:…)` 는 `Invalid group` 이다.
- ★★ **두 node 판에서 같은 세 줄은** `TypeError 「RegExp.escape is not a function」` · 중복 이름 `Duplicate capture group name` · 수정자 `Invalid group` 이다([3-answer.md](3-answer.md) 8번 블록).
  ★ 셋 다 **「기능이 없다」가 아니라 「문법 오류」나 「함수가 아니다」로** 보인다 — **없는 판에서 이 문구를 보고 「패턴이 틀렸다」로 읽으면 안 된다.**

### (7) ★★★ 입력 길이 × 엔진 — 「2초 안에 끝났나」 격자 (본체 1)

**언제 쓰나** — **사용자 입력에 정규식을 거는 모든 곳**. 특히 중첩 수량자 `(x+)+` · 겹치는 갈래 `(a|a)+` 가 있을 때.

```text
   /^(a+)+$/  on  "a" * n + "!"      셸이 timeout 2 로 감싸 종료 코드만 본다
                                    124 (잘렸다)  -> no
                                    0   (끝났다)  -> yes (그리고 답)

   n        10    20    30    40    1000
   ──────── ───── ───── ───── ───── ─────
   백트래킹   끝남  끝남   ?     ?     ?
   상태집합   끝남  끝남  끝남  끝남  끝남      <- 이것이 예측인가 실측인가는 아래 블록이 말한다
```

```js
// js28b-30-h-explode.js
// 인자 n 과 플래그로 /^(a+)+$/ 를 "a" * n + "!" 에 한 번 던진다. js28b-30x-explode.sh 가 시간 제한을 걸고 부른다.
const n = Number(process.argv[2]);
const flags = process.argv[3] || "";
console.log(new RegExp("^(a+)+$", flags).test("a".repeat(n) + "!"));
```

```go
// js28b-30-h-re2.go
// 인자 n 으로 같은 패턴을 Go 의 regexp(RE2)에 한 번 던진다. js28b-30x-explode.sh 가 빌드해서 부른다.
package main

import (
	"fmt"
	"os"
	"regexp"
	"strconv"
	"strings"
)

func main() {
	n, _ := strconv.Atoi(os.Args[1])
	re := regexp.MustCompile(`^(a+)+$`)
	fmt.Println(re.MatchString(strings.Repeat("a", n) + "!"))
}
```

```python
# js28b-30-h-re.py
# 인자 n 으로 같은 패턴을 파이썬 re 에 한 번 던진다. js28b-30x-explode.sh 가 시간 제한을 걸고 부른다.
import re
import sys

n = int(sys.argv[1])
print(re.search(r"^(a+)+$", "a" * n + "!") is not None)
```

```sh
# js28b-30x-explode.sh
#!/usr/bin/env bash
# /^(a+)+$/ 를 "a" * n + "!" 에 -- 엔진마다 n 을 늘려 「2초 안에 끝났나」만 참거짓으로 적는다.
# ★ 경과 시간은 찍지 않는다. 끝난 칸은 답(매치 여부)도 함께 확인한다.
set -u -o pipefail
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
GO="$HOME/.local/opt/go/bin/go"
LIMIT=2
BIN="$PWD/build-30"
mkdir -p "$BIN"
"$GO" build -o "$BIN/re2" js28b-30-h-re2.go || { echo "go build failed"; exit 1; }

cols=("node18" "node20" "node20 l-flag" "node20 fallback" "go RE2" "python3 re")
run() {   # run <열 번호> <n>
  case $1 in
    0) timeout "$LIMIT" "$N18" js28b-30-h-explode.js "$2" ;;
    1) timeout "$LIMIT" "$N20" js28b-30-h-explode.js "$2" ;;
    2) timeout "$LIMIT" "$N20" --enable-experimental-regexp-engine js28b-30-h-explode.js "$2" l ;;
    3) timeout "$LIMIT" "$N20" --enable-experimental-regexp-engine-on-excessive-backtracks js28b-30-h-explode.js "$2" ;;
    4) timeout "$LIMIT" "$BIN/re2" "$2" ;;
    5) timeout "$LIMIT" python3 js28b-30-h-re.py "$2" ;;
  esac
}
NS="10 20 30 40 1000"
printf '  %-6s' "n"; for c in "${cols[@]}"; do printf '%-17s' "$c"; done; echo
declare -A first
done_cells=0; cut_cells=0; wrong=0
for n in $NS; do
  printf '  %-6s' "$n"
  for i in 0 1 2 3 4 5; do
    out="$(run "$i" "$n" 2>&1)"; rc=$?
    if [ "$rc" -eq 124 ]; then cell="no"; cut_cells=$((cut_cells + 1)); [ -z "${first[$i]:-}" ] && first[$i]="$n"
    elif [ "$rc" -eq 0 ]; then cell="yes ($out)"; done_cells=$((done_cells + 1)); case $out in false|False) ;; *) wrong=$((wrong + 1)) ;; esac
    else cell="exit $rc"; fi
    printf '%-17s' "$cell"
  done
  echo
done
echo ""
for i in 0 1 2 3 4 5; do printf '  %-17s first n that did not finish: %s\n' "${cols[$i]}" "${first[$i]:-none}"; done
echo ""
echo "finished within ${LIMIT}s: $done_cells / $((done_cells + cut_cells))   ·   finished with a wrong answer: $wrong"
```

```text
===== ./js28b-30x-explode.sh (exit=0) =====
  n     node18           node20           node20 l-flag    node20 fallback  go RE2           python3 re       
  10    yes (false)      yes (false)      yes (false)      yes (false)      yes (false)      yes (False)      
  20    yes (false)      yes (false)      yes (false)      yes (false)      yes (false)      yes (False)      
  30    no               no               yes (false)      yes (false)      yes (false)      no               
  40    no               no               yes (false)      yes (false)      yes (false)      no               
  1000  no               no               yes (false)      yes (false)      yes (false)      no               

  node18            first n that did not finish: 30
  node20            first n that did not finish: 30
  node20 l-flag     first n that did not finish: none
  node20 fallback   first n that did not finish: none
  go RE2            first n that did not finish: none
  python3 re        first n that did not finish: 30

finished within 2s: 21 / 30   ·   finished with a wrong answer: 0
```

- ★★★ **백트래킹 엔진 셋(node18 · node20 · 파이썬 `re`)은 `n = 20` 까지 끝났고 `n = 30` 부터 2초 안에 안 끝났다.** 상태 집합 쪽 셋(V8 `l` · V8 되돌이 초과 시 갈아타기 · Go RE2)은 **`n = 1000` 까지 전부 끝났다.**
  스크립트의 집계 — `finished within 2s: 21 / 30` · 끝난 칸 중 **틀린 답 0**(전부 `false` — `!` 때문에 매치가 없다).
- ★★★ **「처음 끝나지 않은 n」은 자릿수로만 말한다 — 「두 자릿수, 이 격자의 해상도에서 20 과 30 사이」.**
  격자 간격이 10 이라 그 사이 어디인지는 이 블록이 말하지 않는다. 그리고 **어느 n 에서 잘리느냐는 머신과 제한 시간에 달린다** — 그래서 경계 **값**이 아니라 **「두 자릿수 n 에서 이미 잘린다」는 성질**이 결론이다.
- ★★★ **경과 시간은 이 블록 어디에도 없다.** 「몇 배 느려지나」·「지수적으로 느려진다」를 **이 머신의 수치로 주장하지 않는다** — 증가의 **모양**은 다음 동작 (8)이 **시간이 아니라 되돌이 수로** 보인다.
- ★★ **답은 같다** — 여섯 엔진이 끝난 칸에서 전부 `false` 다. **엔진이 바꾸는 것은 답이 아니라 「답을 내기까지 걷는 길」이다**(명세는 답만 정한다 — 「구현 세부사항 대 언어 보장」).
- ★★ **Go 쪽은 `go build` 로 한 번 만든 실행 파일을 `timeout` 으로 감싼다** — `go run` 을 매번 부르면 **컴파일 시간이 제한 시간을 먹는다.** 창의 조건을 엔진끼리 맞춘 것이다.

### (8) ★★★ 시간 대신 「되돌이 수」 — V8 에게 K 를 이분 탐색시킨 표 (본체 2)

**언제 쓰나** — 「느려진다」를 **시간 없이** 증명해야 할 때. V8 한 엔진에서만 열리는 창이다.

```text
   node --enable-experimental-regexp-engine-on-excessive-backtracks
        --regexp-backtracks-before-fallback=K
        --trace-experimental-regexp-engine

   되돌이가 K 를 넘으면 -> 선형 엔진으로 갈아탄다 -> 추적 줄 「Experimental execution …」 이 찍힌다
                                                   (주소가 박혀 있어 셸이 「나왔나」 하나로 줄인다)
   K 를 1 .. 2^22 에서 이분 탐색  ->  「갈아타지 않는 가장 작은 K」 = 그 입력이 쓴 되돌이 수의 경계

       n=1   n=2   n=3   ...   n=12
        │     │     │           │
        K     K     K           K        옆 행과의 비율도 스크립트가 나눈다
```

```js
// js28b-30-h-steps.js
// 인자 (패턴, n) -- 패턴을 "a" * n + "!" 에 한 번 던진다. js28b-30y-steps.sh 가 V8 의 되돌이 한도 플래그를 걸고 부른다.
console.log(new RegExp(process.argv[2]).test("a".repeat(Number(process.argv[3])) + "!"));
```

```sh
# js28b-30y-steps.sh
#!/usr/bin/env bash
# 시간 대신 「스텝」 -- V8 에게 「되돌이(backtrack)를 K 번 넘기면 선형 엔진으로 갈아타라」고 시키고,
# 갈아탔다는 추적 줄이 나왔나(참거짓)만 본다. K 를 이분 탐색해 「갈아타지 않는 가장 작은 K」를 n 마다 찾는다.
# ★ 추적 줄에는 주소가 박히므로 줄 자체는 싣지 않는다 -- 나왔나/안 나왔나만 쓴다.
set -u -o pipefail
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
fell_back() {   # fell_back <node> <K> <패턴> <n>  -> 0 이면 갈아탔다
  local out
  out="$("$1" --enable-experimental-regexp-engine-on-excessive-backtracks --regexp-backtracks-before-fallback="$2" \
         --trace-experimental-regexp-engine js28b-30-h-steps.js "$3" "$4" 2>&1)"
  case $out in *"Experimental execution"*) return 0 ;; *) return 1 ;; esac
}
smallest_k() {  # smallest_k <node> <패턴> <n>   (1 .. 2^22 범위)
  local lo=0 hi=4194304 mid
  while [ $((hi - lo)) -gt 1 ]; do
    mid=$(((lo + hi) / 2))
    if fell_back "$1" "$mid" "$2" "$3"; then lo=$mid; else hi=$mid; fi
  done
  echo "$hi"
}
table() {       # table <node> <패턴> <n 목록>
  local prev="" k
  printf '  %-7s %-28s %s\n' "n" "smallest K with no fallback" "ratio to the row above"
  for n in $3; do
    k="$(smallest_k "$1" "$2" "$n")"
    if [ -n "$prev" ]; then r="$(awk -v a="$k" -v b="$prev" 'BEGIN { printf "%.2f", a / b }')"; else r="-"; fi
    printf '  %-7s %-28s %s\n' "$n" "$k" "$r"
    prev="$k"
  done
}
echo "[1] node20  /^(a+)+\$/"
t20="$(table "$N20" '^(a+)+$' "1 2 3 4 5 6 7 8 9 10 11 12")"; printf '%s\n' "$t20"
echo ""
echo "[2] node20  /^a+\$/  (the same language, no nested quantifier)"
table "$N20" '^a+$' "1 10 100 1000 10000"
echo ""
echo "[3] node18  /^(a+)+\$/ -- is the table the same as [1]?"
t18="$(table "$N18" '^(a+)+$' "1 2 3 4 5 6 7 8 9 10 11 12")"
if [ "$t18" = "$t20" ]; then echo "  identical to [1]"; else printf '%s\n' "$t18"; fi
echo ""
echo "[4] K = 1000, 10000, 100000, 1000000 -- the first n (1..30) that falls back, node20  /^(a+)+\$/"
for K in 1000 10000 100000 1000000; do
  f="none"
  for n in $(seq 1 30); do if fell_back "$N20" "$K" '^(a+)+$' "$n"; then f="$n"; break; fi; done
  printf '  K = %-9s first n = %s\n' "$K" "$f"
done
```

```text
===== ./js28b-30y-steps.sh (exit=0) =====
[1] node20  /^(a+)+$/
  n       smallest K with no fallback  ratio to the row above
  1       5                            -
  2       8                            1.60
  3       14                           1.75
  4       26                           1.86
  5       50                           1.92
  6       98                           1.96
  7       194                          1.98
  8       386                          1.99
  9       770                          1.99
  10      1538                         2.00
  11      3074                         2.00
  12      6146                         2.00

[2] node20  /^a+$/  (the same language, no nested quantifier)
  n       smallest K with no fallback  ratio to the row above
  1       3                            -
  10      3                            1.00
  100     3                            1.00
  1000    3                            1.00
  10000   3                            1.00

[3] node18  /^(a+)+$/ -- is the table the same as [1]?
  identical to [1]

[4] K = 1000, 10000, 100000, 1000000 -- the first n (1..30) that falls back, node20  /^(a+)+$/
  K = 1000      first n = 10
  K = 10000     first n = 13
  K = 100000    first n = 17
  K = 1000000   first n = 20
```

- ★★★ **`[1]` `/^(a+)+$/` 는 n 이 하나 늘 때마다 K 가 거의 두 배가 된다** — 스크립트가 나눈 비율이 `1.60 → 1.75 → … → 2.00` 으로 **2 에 붙는다**(`n = 10` 부터 `2.00`).
  이것은 **시간이 아니라 V8 이 센 되돌이 수**라서 머신이 바뀌어도 **같아야 할** 칸이다 — `[3]` 이 **node18 에서 한 글자도 같았다**(`identical to [1]`).
- ★★★ **`[2]` 같은 언어를 받는 `/^a+$/` 는 n 이 1 에서 10000 이 돼도 K 가 `3` 이다.** 두 패턴은 **같은 문자열 집합**을 받는다 — 폭발은 **언어가 아니라 패턴의 모양**(중첩 수량자)에서 나온다.
- ★★★ **`[4]` K 를 열 배씩 올리면 처음 갈아타는 n 이 `10 → 13 → 17 → 20`** 이다 — **K 가 곱으로 늘 때 n 은 덧셈으로만** 따라간다.
  ★ 동작 (7)에서 「두 자릿수 n 에서 이미 잘린다」가 나온 이유가 이 표다 — 되돌이 수가 n 에 대해 **곱으로** 불어나면, 제한을 아무리 넉넉히 줘도 **n 은 몇 칸 더 못 간다.**
- ★★ **이 창이 못 보는 것** — V8 이 **무엇을 「되돌이 한 번」으로 세는지**는 V8 내부 정의다(`--v8-options` 의 설명은 `number of backtracks during regexp execution` 한 줄뿐이다). 그래서 **K 의 절댓값에 뜻을 두지 않고 비율과 추세만** 읽는다.
  그리고 이 계수기는 **V8 에만 있다** — RE2·파이썬에는 같은 창이 없어 동작 (7)의 참/거짓만으로 답했다(**제5의 상태**).
- ★ 「두 배씩 는다」를 **손으로 유도하지 않았다** — 비율은 **스크립트가 나눈 값**이다. 알고리즘 차원의 설명(갈래 수가 분할의 가짓수만큼 늘어난다)은 알고리즘 갈래의 몫이다.

### (9) ★★ 같은 패턴 열두 개를 세 엔진에 — 무엇을 받고 무엇을 거절하나

**언제 쓰나** — 다른 언어의 정규식을 JS 로 옮기거나 반대로 옮길 때. **같은 문법처럼 보여도 엔진마다 받는 것이 다르다.**


```js
// js28b-30-h-syntax-v8.js
// 인자로 받은 패턴을 u 플래그로 컴파일만 한다 -- 받으면 accept, 아니면 reject 와 문구. js28b-30u-syntax.sh 가 부른다.
for (const src of process.argv.slice(2)) {
  try { new RegExp(src, "u"); console.log("accept"); }
  catch (e) { console.log("reject\t" + e.constructor.name + " 「" + e.message + "」"); }
}
```

```go
// js28b-30-h-syntax-re2.go
// 인자로 받은 패턴을 Go 의 regexp(RE2)로 컴파일만 한다. js28b-30u-syntax.sh 가 부른다.
package main

import (
	"fmt"
	"os"
	"regexp"
)

func main() {
	for _, src := range os.Args[1:] {
		if _, err := regexp.Compile(src); err != nil {
			fmt.Printf("reject\t%T 「%v」\n", err, err)
		} else {
			fmt.Println("accept")
		}
	}
}
```

```python
# js28b-30-h-syntax-re.py
# 인자로 받은 패턴을 파이썬 re 로 컴파일만 한다. js28b-30u-syntax.sh 가 부른다.
import re
import sys

for src in sys.argv[1:]:
    try:
        re.compile(src)
        print("accept")
    except re.error as e:
        print("reject\t" + type(e).__name__ + " 「" + str(e) + "」")
```

```sh
# js28b-30u-syntax.sh
#!/usr/bin/env bash
# 같은 패턴 열두 개를 세 엔진에 컴파일만 시킨다 -- V8(node20, u 플래그) · Go regexp(RE2) · 파이썬 re.
# 패턴 목록은 여기 한 곳에만 있고, 세 보조 파일은 인자로 받는다.
set -u -o pipefail
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
GO="$HOME/.local/opt/go/bin/go"
BIN="$PWD/build-30"
mkdir -p "$BIN"
"$GO" build -o "$BIN/syntax" js28b-30-h-syntax-re2.go || { echo "go build failed"; exit 1; }
P=('^(a+)+$' '(a)\1' '(?=a)a' '(?<=a)b' '(?<=a+)b' '(?<n>a)' '(?P<n>a)' '(?<n>a)\k<n>' '\p{L}' '(?i:a)b' 'a++' '(?>a+)')
mapfile -t js < <("$N20" js28b-30-h-syntax-v8.js "${P[@]}")
mapfile -t go < <("$BIN/syntax" "${P[@]}")
mapfile -t py < <(python3 js28b-30-h-syntax-re.py "${P[@]}")
printf '  %-16s %-8s %-8s %s\n' "pattern" "V8" "RE2" "python re"
split=0
for i in "${!P[@]}"; do
  a="${js[$i]%%$'\t'*}"; b="${go[$i]%%$'\t'*}"; c="${py[$i]%%$'\t'*}"
  printf '  %-16s %-8s %-8s %s\n' "${P[$i]}" "$a" "$b" "$c"
  if [ "$a" != "$b" ] || [ "$b" != "$c" ]; then split=$((split + 1)); fi
done
echo ""
echo "  messages of the rejections:"
for i in "${!P[@]}"; do
  for pair in "V8:${js[$i]}" "RE2:${go[$i]}" "py:${py[$i]}"; do
    case $pair in *reject*) printf '  %-16s %-4s %s\n' "${P[$i]}" "${pair%%:*}" "${pair#*$'\t'}" ;; esac
  done
done
echo ""
echo "patterns on which the three engines do not all agree: $split / ${#P[@]}"
```

```text
===== ./js28b-30u-syntax.sh (exit=0) =====
  pattern          V8       RE2      python re
  ^(a+)+$          accept   accept   accept
  (a)\1            accept   reject   accept
  (?=a)a           accept   reject   accept
  (?<=a)b          accept   reject   accept
  (?<=a+)b         accept   reject   reject
  (?<n>a)          accept   accept   reject
  (?P<n>a)         reject   accept   accept
  (?<n>a)\k<n>     accept   reject   reject
  \p{L}            accept   accept   reject
  (?i:a)b          reject   accept   accept
  a++              reject   reject   accept
  (?>a+)           reject   reject   accept

  messages of the rejections:
  (a)\1            RE2  *syntax.Error 「error parsing regexp: invalid escape sequence: `\1`」
  (?=a)a           RE2  *syntax.Error 「error parsing regexp: invalid or unsupported Perl syntax: `(?=`」
  (?<=a)b          RE2  *syntax.Error 「error parsing regexp: invalid named capture: `(?<=a)b`」
  (?<=a+)b         RE2  *syntax.Error 「error parsing regexp: invalid named capture: `(?<=a+)b`」
  (?<=a+)b         py   error 「look-behind requires fixed-width pattern」
  (?<n>a)          py   error 「unknown extension ?<n at position 1」
  (?P<n>a)         V8   SyntaxError 「Invalid regular expression: /(?P<n>a)/u: Invalid group」
  (?<n>a)\k<n>     RE2  *syntax.Error 「error parsing regexp: invalid escape sequence: `\k`」
  (?<n>a)\k<n>     py   error 「unknown extension ?<n at position 1」
  \p{L}            py   error 「bad escape \p at position 0」
  (?i:a)b          V8   SyntaxError 「Invalid regular expression: /(?i:a)b/u: Invalid group」
  a++              V8   SyntaxError 「Invalid regular expression: /a++/u: Nothing to repeat」
  a++              RE2  *syntax.Error 「error parsing regexp: invalid nested repetition operator: `++`」
  (?>a+)           V8   SyntaxError 「Invalid regular expression: /(?>a+)/u: Invalid group」
  (?>a+)           RE2  *syntax.Error 「error parsing regexp: invalid or unsupported Perl syntax: `(?>`」

patterns on which the three engines do not all agree: 11 / 12
```

- ★★★ **열두 중 열하나에서 세 엔진이 다 같지는 않았다**(`11 / 12`). 셋이 전부 받은 것은 **폭발하는 그 패턴 `^(a+)+$` 하나뿐**이다 — **문법으로는 폭발을 못 막는다.**
- ★★★ **RE2 가 거절한 것은 역참조·둘러보기 전부**다 — `invalid escape sequence: \1` · `invalid or unsupported Perl syntax: (?=` · 룩비하인드는 `invalid named capture` 로(파서가 `(?<` 를 이름 붙이기로 읽었다).
  ★ **`go doc regexp` 는 이 대가를 이렇게 적는다** — 「The regexp implementation provided by this package is guaranteed to run in time linear in the size of the input.」 **선형 보장과 역참조 포기는 한 결정의 두 얼굴이다.**
- ★★ **명명 그룹 문법이 세 가지로 갈린다** — JS 는 `(?<n>)` 만, 파이썬 `re` 는 `(?P<n>)` 만(`(?<n>` 은 `unknown extension`), Go 는 **둘 다** 받는다.
- ★★ **`\p{L}` 은 파이썬 `re` 가 거절한다**(`bad escape \p`) — 표준 `re` 에는 유니코드 속성 이스케이프가 없다.
- ★★★ **소유 수량자 `a++`·원자 그룹 `(?>…)` 는 파이썬 3.12 만 받았다** — **백트래킹을 끊는 문법**이다. JS 에는 없다(`Nothing to repeat` · `Invalid group`). JS 에서 같은 효과가 필요하면 **패턴을 다시 짜거나** 동작 (10)의 선형 엔진을 쓴다.
- ★ `(?i:a)b` 를 node20 이 거절한 것은 **판의 사정**이다(ES2025 — Chrome 151 은 받는다, 동작 (6)).

### (10) ★ V8 의 선형 엔진 — 있나, 무엇을 거절하나

**언제 쓰나** — JS 에서 **폭발하지 않는 정규식이 꼭 필요할 때** 쓸 수 있는 것이 있는지 판단할 때.

```text
   node --v8-options  에게 묻는다          두 판 다 있다
      --enable-experimental-regexp-engine                    l 플래그를 알아듣게 한다
      --enable-experimental-regexp-engine-on-excessive-backtracks   되돌이가 많으면 갈아탄다
   기본값은 전부 꺼져 있다   -> 스위치 없이 /x/l 은 SyntaxError
   켜도 l 이 받는 것은 좁다  -> 역참조·둘러보기·i·\p 를 거절 (Cannot be executed in linear time)
```

- ★★★ **두 node 판 모두 스위치가 있다**(판별 블록과 거절 목록은 [3-answer.md](3-answer.md) 11번) — 없다고 적기 전에 `--v8-options` 에게 물었다.
- ★★★ **스위치 없이는 `l` 플래그 자체가 `SyntaxError 「Invalid flags supplied to RegExp constructor 'l'」`** 이다 — 표준 플래그가 아니다(**ECMA-262 에 `l` 은 없다**).
- ★★★ **켜도 받는 것은 열하나 중 여섯** — 역참조·룩어헤드·룩비하인드뿐 아니라 **`i` 플래그와 `\p{L}` 까지** `Cannot be executed in linear time` 으로 거절했다(이 두 판에서). 동작 (9)의 RE2 보다도 좁다.
- ★★ **그래서 실무의 답은 「이 엔진에 기대라」가 아니라 「폭발하는 모양을 안 쓴다 · 입력 길이를 자른다 · 신뢰할 수 없는 패턴을 받지 않는다」다**. 선형 엔진은 V8 의 **실험 플래그**이고 명세도 호스트도 보장하지 않는다.

## 문법 — 형태와 규칙

★ 이 절은 **형태 표**다 — 모든 동작 주장은 위 동작 절의 캡처 블록에서만 한다.

| 형태 | 뜻 | 판 | 어디서 봤나 |
|---|---|---|---|
| `(…)` · `(?:…)` | 캡처(번호 칸) · 비캡처(칸 없음) | ES3 | 동작 (1) |
| `(?<name>…)` · `\k<name>` · `$<name>` | 명명 그룹 · 역참조 · 치환 | ES2018 | 동작 (1) |
| `(?=…)` · `(?!…)` | 룩어헤드 · 부정 룩어헤드 — 안 먹는다 | ES3 | 동작 (2) |
| `(?<=…)` · `(?<!…)` | 룩비하인드 — **길이 가변 허용**, 역방향 평가 | ES2018 | 동작 (2) |
| `u` | 글자 = 코드 포인트 · `\u{…}` · `\p{…}` · 엄격한 이스케이프 | ES2015 · `\p` 는 ES2018 | 동작 (3) |
| `v` | `u` + 집합 연산 `--` `&&` · 중첩 클래스 · `\q{…}` · 글자열 속성 | **ES2024** | 동작 (4) |
| `d` | `indices` · `indices.groups` — `[시작, 끝)` 코드 유닛 | ES2022 | 동작 (5) |
| `RegExp.escape(s)` | 글자 그대로 쓰는 패턴 조각 | **ES2025** | 동작 (6) |
| `(?<y>…)\|…(?<y>…)` | 다른 갈래의 같은 이름 | **ES2025** | 동작 (6) |
| `(?i:…)` · `(?-i:…)` | 일부에만 `i`·`m`·`s` | **ES2025** | 동작 (6) |

**금지 사례** — 컴파일이 안 되는 것은 코드 펜스가 아니라 표로 적는다(규칙 28).

| 쓴 꼴 | 나온 것 | 어디서 |
|---|---|---|
| `(?<a>x)(?<a>y)` | `SyntaxError` `Duplicate capture group name` | 동작 (1) · (6) |
| `(?<a>x)\k<z>` | `SyntaxError` `Invalid named capture referenced` | 동작 (1) |
| `[\p{L}--\p{ASCII}]` 를 `u` 로 | `SyntaxError` `Invalid character class` | 동작 (4) |
| `[(]` 를 `v` 로 | `SyntaxError` `Invalid character in character class` | 동작 (4) |
| `\p{RGI_Emoji}` 를 `u` 로 | `SyntaxError` `Invalid property name` | 동작 (4) |
| 플래그 `uv` · `l`(스위치 없이) | `SyntaxError` `Invalid flags supplied to RegExp constructor` | 동작 (4) · (10) |
| `a++` · `(?>…)` · `(?P<n>…)` | `SyntaxError` — JS 에 없는 문법 | 동작 (9) |

## 어디서 틀리나

### (1) ★★★ 「입력이 짧으니 괜찮다」고 믿는다

**두 자릿수 n 에서 이미 잘린다**(동작 (7) — 20 과 30 사이). 되돌이 수는 n 이 하나 늘 때 **거의 두 배**였다(동작 (8)). 짧은 입력 한 줄이 서버를 멈춘다.
처방 — 중첩 수량자 `(x+)+`·`(x*)*` 와 **겹치는 갈래** `(a|a)+` 를 쓰지 않는다 · 입력 길이를 먼저 자른다 · 사용자에게 패턴을 받지 않는다.

### (2) ★★★ 「테스트에서 빨랐으니 괜찮다」고 믿는다

폭발은 **매치가 실패할 때** 난다 — 동작 (7)의 입력은 끝에 `!` 가 붙어 **출구가 없는** 입력이다. 맞는 입력만 넣은 테스트는 **첫 갈래에서 바로 성공해** 아무것도 드러내지 않는다(성공하는 입력의 되돌이 수는 이 문서가 **안 쟀다**).

### (3) ★★★ 플래그 없이 이모지를 `.` 으로 센다

**반쪽만 먹는다**(동작 (3)) — `(face + 'x').match(/./g).length` 가 `3`. 글자 단위로 다루는 정규식에는 `u`(또는 `v`)를 단다.
★ 그래도 **자소(사람이 보는 한 글자)** 는 아니다 — 가족 이모지는 코드 포인트 여럿을 이어 만든 것이라(`String.fromCodePoint` 에 다섯 개를 넘겼다) `u` 의 `.` 한 번으로는 안 된다. 그 단위는 동작 (4)의 `\p{RGI_Emoji}` 나 04편의 `Intl.Segmenter` 다.

### (4) ★★★ `\p{L}` 을 `u` 없이 쓴다

**에러가 안 난다** — 글자 `p{L}` 을 찾는 패턴이 된다(동작 (3)의 `[5]`). 「안 걸리는데 왜 그러지」로만 드러난다.

### (5) ★★ `groups` 를 평범한 객체로 다룬다

**프로토타입이 `null`** 이라 `String(m.groups)`·템플릿 리터럴이 `TypeError` 다(동작 (1)). `hasOwnProperty` 도 없다 — `Object.hasOwn` 이나 `in` 을 쓴다.

### (6) ★★ 반복 안의 그룹에 「지금까지 잡은 것」이 남을 것이라 믿는다

**마지막 반복의 것만** 남고, **반복마다 비워진다** — `/(?:(a)|b)+/.exec('ab')[1]` 이 `undefined`(동작 (1)). 반복마다 값이 필요하면 `matchAll` 로 한 조각씩 돈다(29편).

### (7) ★★ 룩비하인드 안의 캡처가 앞에서부터 채워질 것이라 믿는다

**오른쪽부터** 채워진다(동작 (2)의 `[4]` — `"1"`·`"053"`).

### (8) ★★ `u` 패턴에 `v` 를 그냥 바꿔 단다

클래스 안의 맨 구두점 `(`·`|`·`-` 가 **`SyntaxError`** 가 된다(동작 (4)의 `[3]`). 이스케이프하고 옮긴다.

### (9) ★★ 파이썬·Go 정규식을 그대로 옮긴다

명명 그룹 문법이 다르고(`(?P<n>)`), 파이썬은 **가변 룩비하인드**를, RE2 는 **역참조·둘러보기**를 거절한다(동작 (9)). 반대로 파이썬의 `a++`·`(?>…)` 는 JS 에 없다.

### (10) ★ `RegExp.escape` 결과를 사람이 읽을 것이라 기대한다

첫 영숫자와 공백·쉼표까지 `\x..` 가 된다(동작 (6)). 로그에 찍을 값이 아니라 **패턴에 넣을 값**이다. 그리고 **두 node 판에는 없다** — 없는 판의 문구는 `RegExp.escape is not a function` 이다.

## 구현 세부사항 대 언어 보장

### 명세 보장 — 어느 엔진에서도 같아야 하는 것

- ★★★ **매치 결과** — 어느 매치를 찾아야 하는가(왼쪽 우선, 수량자는 욕심 쪽을 먼저, 갈래는 왼쪽 먼저)는 **Pattern Semantics** 가 정한다. 명세는 패턴을 **매처(Matcher)** 와 **연속(Continuation)** 이라는 추상 함수로 풀어 적는다 — 실패하면 **다른 선택지로 다시 부르는** 모양이라 **의미 자체가 백트래킹의 순서**를 따른다.
- ★★★ 그러나 **알고리즘은 정하지 않는다** — 같은 답을 내기만 하면 어떤 방식으로 찾아도 된다. 그래서 **「폭발한다」는 명세의 성질이 아니다.** 명세에는 시간도 되돌이 수도 없다.
- `groups` 가 `OrdinaryObjectCreate(null)` 로 만들어지는 것 · 명명 그룹이 없으면 `groups` 가 `undefined` 인 것 · 반복마다 안쪽 캡처를 비우는 것 · 룩비하인드를 역방향으로 평가하는 것.
- `u`/`v` 가 입력을 **코드 포인트 열**로 읽는 것 · `u` 와 `v` 를 함께 못 다는 것 · `v` 의 집합 연산과 `\q{}`·글자열 속성 · `d` 의 `indices` 가 코드 유닛 위치인 것 · `flags` 의 순서.
- ES2025 의 `RegExp.escape` 알고리즘(첫 영숫자를 `\x` 로) · 중복 이름은 **다른 갈래**에서만 · 수정자는 `i`·`m`·`s` 만.
- 예외의 **종류**(`SyntaxError`·`TypeError`) — 조기 오류(early error)로 정해진 것들.

### 엔진(V8) 구현 · 이 판의 관찰

- ★★★ **Irregexp 가 백트래킹 엔진이라는 것**과 그 **되돌이 수**(동작 (8)) — V8 의 설계다.
- ★★★ **선형 엔진과 그 스위치**(`l` 플래그 · 되돌이 초과 시 갈아타기) — V8 의 **실험 플래그**다. 기본값이 꺼져 있고, 받는 문법이 판마다 다를 수 있다(이 두 판에서는 같았다).
- 예외 **문구 전부** — `Invalid named capture referenced` · `Duplicate capture group name` · `Invalid character in character class` · `Cannot be executed in linear time` 등. ★ **node18 은 문구에 플래그를 안 붙이고 node20 은 붙인다.**
- 「두 자릿수 n 에서 2초를 넘긴다」 — **이 머신 · 이 제한 시간의 관찰**이다.

### 호스트·다른 언어가 정하는 것 — ECMA-262 밖

- ★★ **Go `regexp` 의 선형 보장** — Go 표준 라이브러리 문서의 약속이다(`go doc regexp`). ★ **파이썬 `re`** 는 백트래킹이고 소유 수량자·원자 그룹을 받는다 — 둘 다 **이 머신의 판(3.12)에서 본 것**이다.

### 그래서 이렇게 적으면 틀린다

- ✗ 「JS 정규식은 지수 시간이다」 → ○ 「**명세는 시간을 정하지 않는다** — V8 의 Irregexp 가 백트래킹이라 **이 패턴에서** 되돌이 수가 n 마다 거의 두 배가 됐다」
- ✗ 「`u` 를 달면 이모지 하나가 한 글자다」 → ○ 「**코드 포인트 하나**가 한 글자다 — 여러 코드 포인트짜리 이모지는 `v` 의 `\p{RGI_Emoji}` 나 `Intl.Segmenter`」
- ✗ 「`groups` 는 평범한 객체다」 → ○ 「**null 프로토타입**이다」
- ✗ 「JS 룩비하인드는 고정 길이만」 → ○ 「**가변 길이를 받는다** — 파이썬 `re` 가 고정 길이만이다」
- ✗ 「V8 에는 선형 엔진이 없다」 → ○ 「**있다 — 실험 플래그로, 기본값이 꺼져 있고 받는 문법이 좁다**」
- ✗ 「`v` 가 `u` 보다 느리다」 → ○ **안 쟀다**

## 언제 쓰고 언제 안 쓰나

- **명명 그룹** — 조각이 셋 이상이거나 패턴이 바뀔 수 있을 때(번호가 밀려도 이름은 안 밀린다). 찍을 때는 `JSON.stringify(m.groups)`.
- **비캡처 `(?:…)`** — 묶기만 할 때의 기본값. 번호 칸을 아끼고 `split` 에 캡처가 끼는 것(28편)을 막는다.
- **둘러보기** — 조건은 걸되 결과에서 빼고 싶을 때 · 「그 자리」에 끼워 넣을 때(천 단위 쉼표).
- **`u`** — 사람이 쓴 텍스트에 거는 정규식의 기본값. **`v`** — 집합 연산·이모지가 필요하고 **ES2024 이후 엔진만** 상대할 때.
- **`d`** — 위치가 필요할 때만(달라고 해야 준다).
- **`RegExp.escape`** — 사용자 입력을 패턴에 넣을 때. **없는 판**을 상대하면 대체가 필요하다(이 문서는 대체 구현을 싣지 않는다).
- ★★★ **안 쓰는 자리** — **신뢰할 수 없는 입력에 중첩 수량자 패턴**(동작 (7)) · **사용자가 준 패턴을 그대로 실행**(ReDoS) · 정규식으로 **중첩 구조 파싱**(괄호 짝 맞추기는 정규 언어가 아니다 — 원리는 알고리즘 갈래).

## 핵심 문장

1. ★★★ 명세는 **어느 매치를 찾을지(의미)** 만 정하고 **어떻게 찾을지(알고리즘)** 는 엔진에 맡긴다 — 「폭발」은 엔진의 성질이다.
2. ★★★ `/^(a+)+$/` 는 백트래킹 엔진 셋에서 **두 자릿수 n 에 이미 2초를 넘겼고**, V8 이 센 **되돌이 수는 n 이 하나 늘 때 거의 두 배**였다(두 node 판 동일). 같은 언어의 `/^a+$/` 는 되돌이 수가 변하지 않았다.
3. ★★★ Go RE2 · V8 `l` 은 **n = 1000 까지 전부 끝났다** — 대가로 **역참조·둘러보기**를 거절한다(`l` 은 `i`·`\p` 까지).
4. ★★★ 플래그가 없으면 글자 = **코드 유닛**, `u`/`v` 면 **코드 포인트** — 일곱 패턴 중 여섯에서 답이 갈렸다. `v` 는 여기에 **집합 연산·글자열 속성**을 더하고 **클래스 안의 맨 구두점을 거절**한다.
5. ★★ `groups` 는 **null 프로토타입**이고, 반복 안의 캡처는 **반복마다 비워지며**, 룩비하인드 안의 캡처는 **오른쪽부터** 채워진다.

## 관련 자료

- [ECMA-262 — RegExp (Regular Expression) Objects](https://tc39.es/ecma262/multipage/text-processing.html#sec-regexp-regular-expression-objects) — Pattern 문법 · Pattern Semantics
- [TC39 finished proposals](https://github.com/tc39/proposals/blob/main/finished-proposals.md) — 판 경계
- [29 — 정규식 기본](../29-regexp-basics/2-summary.md) — ★ **경계**: 그쪽은 **플래그 전수 · `lastIndex` · `match`/`matchAll`/`replace` 의 반환 모양**까지, 여기는 **패턴 안쪽과 엔진**부터.
- [04 — 문자열과 UTF-16](../04-strings-and-utf16/2-summary.md) — ★ **경계**: 그쪽이 **코드 유닛·서로게이트·자소**의 정본, 여기는 **정규식 플래그가 그것을 어떻게 보나**만.
- [28 — `String` 메서드와 템플릿 리터럴](../28-string-methods-and-template-literals/2-summary.md) — `$<name>` 을 포함한 `$` 치환 규칙과 `split` 의 캡처는 그쪽.
- [27 — `Object` 정적 메서드](../27-object-static-methods/2-summary.md) · [15 — 프로토타입 체인](../15-prototype-chain/2-summary.md) — null 프로토타입 객체의 증상.
- [`algorithm/25-string-matching`](../../../../../algorithm/25-string-matching/2-summary.md) — ★ **경계**: 문자열 매칭 알고리즘의 자리. 지금은 **나이브·KMP 까지**이고 정규식 엔진(백트래킹 대 상태 집합)의 원리는 **아직 정본이 없다** — 여기서는 원리를 적지 않고 **관찰과 대가**만 적는다.
- 파이썬 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **46번**(`re`) — 동작 (7)·(9)의 파이썬 열. 폴더가 아직 없어 이 문서가 **직접 던졌다**.
- Go — 갈래 목록에 정규식 주제가 없다. `regexp` 는 이 문서가 **직접 던졌다**(동작 (7)·(9)).
- Rust — `regex` 는 외부 크레이트라 Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))이 다루지 않는다 — **부적용**.

## 용어 풀이

- **캡처 그룹** — `(…)`. 매치된 부분을 번호 칸에 담는다. **비캡처** `(?:…)` 는 묶기만 한다.
- **명명 그룹** — `(?<name>…)`. 번호 칸에 더해 `groups.name` 으로도 꺼낸다.
- **역참조** — `\1`·`\k<name>`. 앞에서 잡은 **바로 그 글자열**을 다시 요구한다.
- **둘러보기(lookaround)** — `(?=)`·`(?!)`·`(?<=)`·`(?<!)`. 조건만 검사하고 글자를 먹지 않는다.
- **코드 유닛 / 코드 포인트** — UTF-16 의 16비트 칸 / 유니코드의 글자 번호. 04편이 정본.
- **서로게이트 쌍** — BMP 밖 코드 포인트 하나를 담는 코드 유닛 두 칸.
- **글자열 속성(property of strings)** — `\p{RGI_Emoji}` 처럼 **여러 코드 포인트로 된 글자열**을 원소로 갖는 집합. `v` 에만 있다.
- **백트래킹 엔진** — 선택지를 하나씩 시도하고 실패하면 되돌아가는 엔진. V8 Irregexp · 파이썬 `re`.
- **상태 집합 시뮬레이션** — 가능한 자리를 전부 한꺼번에 들고 한 글자씩 나아가는 방식. Go RE2 · V8 실험 엔진.
- **되돌이(backtrack) 수** — 백트래킹 엔진이 선택 지점으로 돌아간 횟수. 이 문서는 V8 의 계수기로 셌다.
- **ReDoS** — 정규식 하나가 끝나지 않아 서비스가 멈추는 사고·공격.
- **Pattern Semantics** — 명세가 패턴의 **뜻**을 매처·연속이라는 추상 함수로 정의한 부분. 알고리즘이 아니다.
- **Irregexp** — V8 의 정규식 엔진 이름.

## 더 들어가면

- **백트래킹 대 상태 집합의 원리**(NFA 시뮬레이션 · 역참조가 정규 언어 밖인 이유) — 알고리즘 갈래가 받을 자리다. `go doc regexp` 가 가리키는 Russ Cox 의 글이 출발점이다(**이 문서는 그 글을 확인하지 않았다**).
- **성공하는 입력의 되돌이 수 · 겹치는 갈래 `(a|a)+` 의 되돌이 수** — 이 문서는 **중첩 수량자 한 가지만** 쟀다. 같은 창(동작 (8))으로 다른 모양도 잴 수 있다.
- **`RegExp.escape` 가 없는 판의 대체** · **`\p{…}` 속성 이름 전체** — 싣지 않았다.
