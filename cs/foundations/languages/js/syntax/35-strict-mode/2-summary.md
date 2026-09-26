# js/syntax/35 — 엄격 모드: 「조용한 실패를 시끄럽게 만들고, 몇몇 문법을 닫는다 — 모듈과 클래스는 늘 엄격이다」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> ★★★ **이 편은 「이미 곳곳에서 조각으로 잰 것을 한데 모으는 정본」 편이다.** 엄격 모드가 바꾸는 규칙의 절반 이상은 앞 편들이 **두 번 컴파일 격자**로 이미 쟀다 —
> [07번](../07-this-binding-four-rules/2-summary.md) `this` 격자 `9 / 14` · [08번](../08-function-forms-and-parameters/2-summary.md) ★★ **`arguments` 연동 격자 `7 / 12`** 와 매개변수 형태 `7 / 20` · [10번](../10-destructuring-assignment/2-summary.md) `2 / 12` ·
> [12번](../12-optional-chaining-nullish-and-logical-assignment/2-summary.md) `6 / 11`(★ **`??=` 는 두 모드 다 `ReferenceError`**) · [14번](../14-property-descriptors-and-freezing/2-summary.md) `9 / 13` ·
> [24번](../24-array-mutating-methods/2-summary.md)(★ **변형 메서드는 비엄격에서도 던진다**) · [16번](../16-class-syntax/2-summary.md)(★ **클래스 몸통은 늘 엄격**).
> ★★★ **다시 재지 않는다.** 동작 (1)의 **정본 표**가 그 조각들을 「**엄격이 바꾸는 규칙**」 한 장으로 모으고 **칸마다 어느 편에서 쟀나**를 단다.
> **새로 잰 것은 그 표의 빈 칸뿐**이다 — `eval` 의 변수 누출 · `with` · 8진수 리터럴 · `delete 식별자` · 읽기 전용 전역 · 원시값에 쓰기 · 예약어 · **`"use strict"` 가 효력을 갖는 자리** · **모듈은 늘 엄격**.
>
> ★★★ **이 주제의 본체는 「두 번 컴파일」 격자(② 전수 격자의 모드 판)다** — 같은 탐침 본문을 **`"use strict";` 를 붙여 한 번, 그대로 한 번** 컴파일한다.
> ★★★ **규칙 22 를 지켰다** — ① **엄격을 먼저 전부** 돌리고 ② **탐침마다 고유한 전역 이름**(`js35_<번호>_<모드>`)을 주고 ③ **끝에 `globalThis` 에 남은 이름을 찍는다**(누수 확인).
> 이 편이 그 격자의 본고장이다 — 앞 편들이 한 번씩 겪은 「비엄격을 먼저 돌려 거짓 `0 / 12` 가 나온」 사고(10번)가 여기서 정본 처방이 된다.
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262 — Strict Mode Code](https://tc39.es/ecma262/multipage/ecmascript-language-source-code.html#sec-strict-mode-code) — 「**Module code is always strict mode code.**」 · 「**All parts of a ClassDeclaration or a ClassExpression are strict mode code.**」 · eval 코드와 함수 코드가 엄격이 되는 조건
> - 같은 명세의 **Directive Prologue**(「`"use strict"` 또는 `'use strict'` 의 **정확한 코드 포인트 열** — 이스케이프·줄 이음 불가」) · 함수 정의의 early error(「`FunctionBodyContainsUseStrict` 가 참이고 `IsSimpleParameterList` 가 거짓이면 Syntax Error」) · `PerformEval`(「`strictEval` 이면 `varEnv` 를 `lexEnv` 로」) · **Annex C — The Strict Mode of ECMAScript**(제한 목록)
> - 명세 문장은 이 배치가 받아 둔 **ES2026 판 HTML** 에서 읽었다(연산 이름과 짧은 인용만 싣는다 — Annex C 를 옮기지 않는다).
>
> **실행 검증** — 이 문서의 새 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다.
> 배너의 `node20` 은 `~/.nvm/versions/node/v20.19.6/bin/node`, `node18` 은 기본 PATH 의 `node`(v18.19.1)다.
> ★★ 격자는 **`new Function(소스)` 로 두 번 컴파일**한다 — 파일로 던지면 진단에 경로가 박힌다(07·08번과 같은 방식). 컴파일 단계의 예외는 **`COMPILE`** 을 앞에 붙였다.
> ★★ **모듈은 `.mjs` 로 증명했다** — 같은 파일을 **`.mjs`(모듈)** 로 한 번, **표준 입력 + `--input-type=commonjs`(스크립트)** 로 한 번 돌렸다. 한 글자도 다르지 않은 소스가 두 모드로 갈린다.
> ★★ **이 주제에서 두 node 판이 갈린 탐침은 없다**(대조기 — 이 배치 전체 `identical 12`).
>
> **버전** — **엄격 모드는 ES5**. 모듈(ES2015)·클래스(ES2015)는 처음부터 엄격이다. `0o10` 같은 8진수 표기는 ES2015.
>
> **★★★ 이 주제가 쓰는 창 — 그리고 부적용인 창**
>
> | 창 | 이 주제에서 무엇을 보나 |
> |---|---|
> | ★★★ **두 번 컴파일**(엄격 먼저 · 고유 전역 · 누수 확인 — 본체) | 새 탐침 **14개**에서 **설정에 달린 칸 N / M** 을 스크립트가 센다 · **`globalThis` 에 남은 이름**(동작 (2)) |
> | ★★ **④ 예외의 `constructor.name` + `message`** | **컴파일에서 던지나(`COMPILE SyntaxError`) · 실행에서 던지나(`TypeError`·`ReferenceError`)** 가 갈린다 — 엄격 모드가 바꾸는 것이 **문법**인지 **동작**인지가 여기서 보인다 |
> | ★★ **판별 탐침**(전역을 안 건드리는 모드 판정) | `"use strict"` 가 효력을 갖나 — **안쪽 함수의 `this` 가 `undefined` 인가**로 묻는다(동작 (3)). 암시적 전역을 쓰지 않아 **누수가 원리상 없다** |
> | ★ **③ 브랜드 태그** | **부적용** — 모드는 값의 종류를 안 바꾼다(`this` 의 박싱은 07·09번이 태그로 쟀다) |
> | ★ **① 추상 연산에 로그 심기** | **부적용** — 모드가 바꾸는 것은 사용자 코드를 부르는 순서가 아니다 |
> | ★ **안 쟀다 — 성능** | ★★★ **「엄격 모드가 빠르다」를 한 줄도 쓰지 않는다.** 시간을 안 쟀다 |
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 예외 **문구**(`Octal literals are not allowed in strict mode.` 등) — V8 의 글자다 | ★★★ 「설정에 달린 칸 N / M」 · 칸마다 **값인가 / 실행 예외인가 / `COMPILE` 예외인가** · 남은 전역 이름 목록 |
> | — | ★★ **이 주제의 탐침에는 재실행에서 흔들린 칸이 없다**(재대조 동일) |
>
> **선행** — [05 — `var`·`let`·`const` 와 TDZ](../05-var-let-const-and-tdz/2-summary.md)(직접 선행 — 중복 매개변수 · 동결의 조용한 실패가 처음 나온 곳. ★ **「ESM 최상위를 안 돌려 봤다」고 적어 둔 빈 칸**을 이 편이 채운다) ·
> [06 — 스코프와 클로저](../06-scope-and-closures/2-summary.md)(`with` 와 직접 `eval` 이 스코프를 바꾸는 자리를 **35번에 미뤘다**) ·
> [07](../07-this-binding-four-rules/2-summary.md) · [08](../08-function-forms-and-parameters/2-summary.md) · [09](../09-call-apply-bind/2-summary.md) · [10](../10-destructuring-assignment/2-summary.md) · [12](../12-optional-chaining-nullish-and-logical-assignment/2-summary.md) · [13](../13-object-literals-and-properties/2-summary.md) · [14](../14-property-descriptors-and-freezing/2-summary.md) · [16](../16-class-syntax/2-summary.md) · [24](../24-array-mutating-methods/2-summary.md) — 정본 표의 인용 행.
> **같은 배치** — [32 — 오류 처리와 `Error`](../32-error-handling-and-error/2-summary.md) · [33 — 동등성 세 종류](../33-equality-three-kinds/2-summary.md) · [34 — 타입 검사 관용구](../34-type-checking-idioms/2-summary.md).
>
> ★★ **경계 — 모듈 자체**(`import`/`export`·로딩·최상위 `await`)는 목록의 **42번 주제**(ESM)와 **43번 주제**(CJS 상호운용)의 몫이다. 여기서는 **「모듈 코드는 늘 엄격」** 한 줄을 잰다.

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

**엄격 모드는 「조용히 넘어가던 실수를 그 자리에서 멈춰 세우는 감독관」이다. 그리고 감독관이 서 있는 곳이 따로 정해져 있다.**

- ★★★ **조용한 실패를 시끄럽게** — 선언 안 한 이름에 대입(전역이 몰래 생긴다) · 얼린 객체에 쓰기(말없이 버려진다) · 원시값에 프로퍼티 쓰기(말없이 사라진다)가 **예외가 된다.**
- ★★★ **헷갈리는 문법을 닫는다** — `with` · 8진수 `010` · `delete 이름` · 중복 매개변수 · `eval`/`arguments` 를 이름으로 쓰기 · 예약어(`let`·`implements` …)를 이름으로 쓰기가 **컴파일에서 거절된다.**
- ★★ **`this` 와 `arguments` 를 덜 마법적으로** — 그냥 부른 함수의 `this` 가 전역이 아니라 `undefined`, `arguments` 가 매개변수와 따로 논다.
- ★★ **감독관이 서는 자리** — 파일·함수 **맨 앞의 `"use strict"`**, 그리고 **모듈과 클래스는 늘**. 맨 앞이 아니면 **감독관은 없다.**

```text
   같은 소스, 두 모드                                       무엇이 바뀌나

   G = 1                         비엄격 → 전역 G 가 생긴다          엄격 → ReferenceError          (동작)
   frozen.a = 2                  비엄격 → 말없이 버린다             엄격 → TypeError               (동작)
   with (o) { … } · 010          비엄격 → 된다                     엄격 → COMPILE SyntaxError     (문법)
   eval("var x = 1")             비엄격 → x 가 바깥으로 샌다        엄격 → eval 안에 갇힌다          (스코프)
   (function(){ return this })() 비엄격 → globalThis              엄격 → undefined               (this)

   감독관이 서는 곳:  "use strict" 가 파일·함수의 「첫 문장들(지시어 머리말)」 안에 있을 때 · 모듈 · 클래스 몸통
```

**비유 대응표**

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 조용한 실패를 멈춰 세운다 | 실패하는 쓰기가 `false` 를 돌려주는 대신 `TypeError` · 미해결 이름 대입이 `ReferenceError` | 동작 (2)의 실행 예외 칸 · 14번 |
| 헷갈리는 문법을 닫는다 | **early error** — 엄격 코드에서만 Syntax Error 인 생성 규칙 | 동작 (2)의 `COMPILE` 칸 |
| 감독관이 서는 자리 | **Directive Prologue** 안의 Use Strict Directive · 모듈 코드 · 클래스 코드 | 동작 (3)·(4) |
| 맨 앞이 아니면 없다 | `var a; "use strict";` 의 문자열은 **그냥 식 문장** | 동작 (3) |

**똑같은 구조다** — 실무에서 물리는 자리.
「**오래된 스크립트 앞에 다른 파일을 이어 붙였더니(번들) 첫 파일의 `"use strict"` 가 맨 앞이 아니게 되어 효력을 잃었다**」와
「**`.mjs` 로 옮겼더니 선언 안 한 변수 대입이 갑자기 `ReferenceError` 를 냈다**」가 같은 규칙의 앞뒤다(동작 (3)·(4)).

> **지시어 머리말(Directive Prologue)** — 함수·스크립트 본문 **맨 앞에 연달아 오는 문자열 식 문장들**. 그 안에 정확히 `"use strict"` 가 있으면 엄격이 된다.\
> 예: `"hello"; "use strict";` 는 둘 다 머리말이라 엄격이다. `var a; "use strict";` 는 아니다.

## 이 주제가 답하려는 질문

1. **엄격 모드가 바꾸는 규칙은 무엇무엇이고, 각각 문법(컴파일)인가 동작(실행)인가** — 앞 편들이 잰 것과 새로 잰 것을 한 표로 모으면?
2. **`"use strict"` 는 어디에 어떻게 써야 효력이 있나** — 그리고 쓸 수 **없는** 자리는?
3. **모듈은 정말 늘 엄격인가** — 모듈 안에서도 엄격이 아닌 코드가 있나?

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 출력으로 읽는다.

### (1) ★★★ 정본 표 — 엄격이 바꾸는 규칙, 칸마다 「어디서 쟀나」

**언제 쓰나** — 「이 코드가 엄격인가」에 따라 답이 바뀌는지를 볼 때 · 비엄격 코드를 엄격으로 옮길 때 무엇이 깨질지 셀 때. **외울 것은 이 표 하나다.**
★★★ **인용 행**은 앞 편의 블록이 근거다(링크의 동작 번호). **새 행**은 이 편 동작 (2)\~(4)가 근거다. 「종류」 칸은 **엄격 쪽이 언제 거절하나** — `컴파일`(early error) · `실행`(예외) · `값`(다른 값).

| 규칙 | 비엄격 | 엄격 | 종류 | 어디서 쟀나 |
|---|---|---|---|---|
| **이름과 전역** | | | | |
| 선언 안 된 이름에 대입 `G = 1` | 전역이 생긴다 | `ReferenceError` | 실행 | 인용 — [07](../07-this-binding-four-rules/2-summary.md) 동작 (2) · [14](../14-property-descriptors-and-freezing/2-summary.md) 동작 (4) · [16](../16-class-syntax/2-summary.md) 동작 (2)(누수 `1 / 2`) |
| 선언 안 된 이름에 구조 분해 대입 | 전역이 생긴다 | `ReferenceError` | 실행 | 인용 — [10](../10-destructuring-assignment/2-summary.md) 동작 (4) |
| 선언 안 된 이름에 `??=`·`\|\|=` | `ReferenceError` | `ReferenceError` | — **모드 무관** | 인용 — [12](../12-optional-chaining-nullish-and-logical-assignment/2-summary.md) 동작 (4) |
| ★ 읽기 전용 전역에 대입 `undefined = 1` | 말없이 버린다 | `TypeError` | 실행 | **새로** — 동작 (2) |
| ★ `delete 식별자` | `false` | `SyntaxError` | 컴파일 | **새로** — 동작 (2) |
| ★ 직접 `eval("var …")`·`eval("function …")` | 바깥 함수로 샌다 | eval 안에 갇힌다 | 스코프 | **새로** — 동작 (2) |
| ★ 직접 `eval("let …")` | 갇힌다 | 갇힌다 | — **모드 무관** | **새로** — 동작 (2) |
| ★ 간접 `(0, eval)("var …")` | **전역에 샌다** | **전역에 샌다** | — **모드 무관** | **새로** — 동작 (2) |
| ★ `with` | 된다 | `SyntaxError` | 컴파일 | **새로** — 동작 (2) |
| ★ 예약어를 이름으로(`implements`·`let` …) | 된다 | `SyntaxError` | 컴파일 | **새로** — 동작 (2) |
| 블록 안 함수 선언이 블록 밖에서 보이나 | 보인다 | 안 보인다 | 스코프 | 인용 — [08](../08-function-forms-and-parameters/2-summary.md) 동작 (2) |
| **`this`** | | | | |
| 그냥 부른 함수의 `this` | `globalThis` | `undefined` | 값 | 인용 — 07 동작 (2)(`9 / 14`) |
| `call(7)`·`call(null)` 의 `this` | 감싼다 · 전역 | 그대로 | 값 | 인용 — 07 동작 (2) · [09](../09-call-apply-bind/2-summary.md) 동작 (1) |
| **함수와 매개변수** | | | | |
| `arguments` 와 매개변수의 연동 | 한 몸 | 끊긴다 | 값 | 인용 — 08 동작 (4)(`7 / 12`) |
| `arguments.callee` | 된다 | `TypeError` | 실행 | 인용 — 08 동작 (4) |
| 중복 매개변수 `f(a, a)` | 된다(뒤가 이긴다) | `SyntaxError` | 컴파일 | 인용 — [05](../05-var-let-const-and-tdz/2-summary.md) 동작 (5) · 08 동작 (6) |
| `eval`·`arguments`·`yield` 를 이름으로 | 된다 | `SyntaxError` | 컴파일 | 인용 — 08 동작 (6)(`7 / 20`) |
| 비단순 매개변수 목록 + `"use strict"` | `SyntaxError` | `SyntaxError` | — **모드 무관** | 인용 — 08 동작 (6) · 10 동작 (4) + ★ **새로**(화살표·메서드·클래스 메서드) — 동작 (3) |
| 기명 함수 표현식 안에서 자기 이름에 대입 | 말없이 버린다 | `TypeError` | 실행 | 인용 — 08 동작 (3) |
| **쓰기 실패** | | | | |
| 동결·쓰기 불가·getter 만·확장 불가 객체에 대입 | 말없이 버린다 | `TypeError` | 실행 | 인용 — 14 동작 (4)(`9 / 13`) · 12 동작 (4) · 05 |
| 설정 불가 프로퍼티 `delete` | `false` | `TypeError` | 실행 | 인용 — 12 동작 (4) · 14 동작 (4) |
| 동결 배열에 `push`·`sort` 등 메서드 | `TypeError` | `TypeError` | — **모드 무관** | 인용 — [24](../24-array-mutating-methods/2-summary.md) 동작 (8) · 14 동작 (4) |
| ★ 원시값에 프로퍼티 쓰기 `'ab'.len = 1` | 말없이 사라진다 | `TypeError` | 실행 | **새로** — 동작 (2)(비엄격 쪽은 [01](../01-value-types-and-typeof/2-summary.md) 동작 (3)도 봤다) |
| **리터럴** | | | | |
| ★ 옛 8진수 `010` · 앞자리 0 십진수 `08` | `8` · `8` | `SyntaxError` | 컴파일 | **새로** — 동작 (2) |
| ★ 8진 이스케이프 `'\101'` | `"A"` | `SyntaxError` | 컴파일 | **새로** — 동작 (2) |
| ★ `0o10` | `8` | `8` | — **모드 무관** | **새로** — 동작 (2) |
| 객체 리터럴의 중복 키 | 뒤가 이긴다 | 뒤가 이긴다 | — **ES2015 부터 모드 무관** | 인용 — [13](../13-object-literals-and-properties/2-summary.md) 어디서 틀리나 (4) |
| **어디가 엄격인가** | | | | |
| ★ `"use strict"` 의 자리 | 지시어 머리말 안에서만 효력 | | 컴파일 | **새로** — 동작 (3) |
| 클래스 몸통 | 늘 엄격 | | | 인용 — 16 동작 (2) |
| ★ 모듈 코드 | 늘 엄격 | | | **새로** — 동작 (4) |
| ★ 모듈 안의 `new Function` · 간접 `eval` | **비엄격**(스스로 지시어가 없으면) | | | **새로** — 동작 (4) |

- ★★★ **인용 17행(그중 1행은 이 편이 형태를 넓혔다) · 새로 잰 14행**이다. 앞 편들이 격자로 잰 것이 **`this`·`arguments`·쓰기 실패·매개변수** 쪽에 몰려 있고, **리터럴·`eval`·`with`·「어디가 엄격인가」** 가 비어 있었다.
- ★★★ **「모드 무관」 행이 일곱이나 된다** — `??=` 의 `ReferenceError` · 직접 `eval` 의 `let` · 간접 `eval` · 비단순 목록 + `"use strict"` · 동결 배열의 메서드 · `0o10` · ES2015 이후의 중복 키. **엄격을 켜도 안 바뀌는 자리를 아는 것**도 이 표의 몫이다.
- ★★ **거절의 종류가 둘로 갈린다** — **`컴파일`**(early error — 그 코드가 **한 줄도 안 돈다**)과 **`실행`**(그 줄에 닿아야 던진다). `with`·`010`·`delete 이름`·중복 매개변수는 컴파일, 암시적 전역·동결 쓰기·원시값 쓰기는 실행이다.

### (2) ★★★ 두 번 컴파일 격자 — 새 탐침 열넷, 엄격 먼저 · 고유 전역 · 누수 확인

**언제 쓰나** — 정본 표의 새 행을 **한 블록에서** 고정할 때.
★★★ **엄격을 먼저 전부 돌린다**(`const strict = …` 가 먼저) · **`G` 를 탐침마다 `js35_<번호>_<모드>` 로 바꾼다** · **끝에 `globalThis` 에 남은 `js35_` 이름을 찍는다.**

```js
// js32b-35a-new-cells.js
// 앞 편들이 안 잰 엄격 모드 칸 -- 같은 탐침 본문을 두 번 컴파일한다(앞에 "use strict"; 를 붙여 / 그대로).
// 규칙 둘: (1) 엄격을 먼저 전부 돌린다  (2) 탐침마다 전역 이름을 다르게 준다(G -> js35_<번호>_<모드>).
// 끝에 globalThis 에 남은 js35_ 이름을 찍는다 -- 무엇이 실제로 전역에 샜나.
const PROBES = [
  ["eval('var G = 1'), then typeof G", "eval('var G = 1'); return typeof G;"],
  ["eval('function G() {}'), then typeof G", "eval('function G() {}'); return typeof G;"],
  ["eval('let G = 1'), then typeof G", "eval('let G = 1'); return typeof G;"],
  ["(0, eval)('var G = 1'), then typeof G", "(0, eval)('var G = 1'); return typeof G;"],
  ["with ({ v: 1 }) { return v; }", "with ({ v: 1 }) { return v; }"],
  ["return 010;", "return 010;"],
  ["return 08;", "return 08;"],
  ["return '\\101';", "return '\\101';"],
  ["return 0o10;", "return 0o10;"],
  ["var v = 1; return delete v;", "var v = 1; return delete v;"],
  ["undefined = 1; return typeof undefined;", "undefined = 1; return typeof undefined;"],
  ["'ab'.len = 1; return 'ab'.len;", "'ab'.len = 1; return String('ab'.len);"],
  ["var implements = 1; return implements;", "var implements = 1; return implements;"],
  ["var let = 1; return let;", "var let = 1; return let;"],
];
const show = (e) => e.constructor.name + " 「" + e.message + "」";
function run(i, body, mode) {
  const gname = "js35_" + i + "_" + mode;
  const src = (mode === "strict" ? '"use strict";\n' : "") + body.replace(/\bG\b/g, gname);
  let f;
  try { f = new Function(src); } catch (e) { return "COMPILE " + show(e); }
  try { return String(f()); } catch (e) { return show(e); }
}
const strict = PROBES.map(([, body], i) => run(i, body, "strict"));   // ★ 엄격 먼저
const sloppy = PROBES.map(([, body], i) => run(i, body, "sloppy"));
let differ = 0;
PROBES.forEach(([label], i) => {
  const d = strict[i] !== sloppy[i];
  if (d) differ += 1;
  console.log(label + (d ? "   <-- DIFFERENT" : ""));
  console.log("    strict  " + strict[i]);
  console.log("    sloppy  " + sloppy[i]);
});
console.log("");
const left = Object.keys(globalThis).filter((k) => k.startsWith("js35_")).sort();
console.log("globals left behind: " + JSON.stringify(left));
console.log("settings-dependent cells " + differ + " / " + PROBES.length);
```

```text
===== node20 js32b-35a-new-cells.js (exit=0) =====
eval('var G = 1'), then typeof G   <-- DIFFERENT
    strict  undefined
    sloppy  number
eval('function G() {}'), then typeof G   <-- DIFFERENT
    strict  undefined
    sloppy  function
eval('let G = 1'), then typeof G
    strict  undefined
    sloppy  undefined
(0, eval)('var G = 1'), then typeof G
    strict  number
    sloppy  number
with ({ v: 1 }) { return v; }   <-- DIFFERENT
    strict  COMPILE SyntaxError 「Strict mode code may not include a with statement」
    sloppy  1
return 010;   <-- DIFFERENT
    strict  COMPILE SyntaxError 「Octal literals are not allowed in strict mode.」
    sloppy  8
return 08;   <-- DIFFERENT
    strict  COMPILE SyntaxError 「Decimals with leading zeros are not allowed in strict mode.」
    sloppy  8
return '\101';   <-- DIFFERENT
    strict  COMPILE SyntaxError 「Octal escape sequences are not allowed in strict mode.」
    sloppy  A
return 0o10;
    strict  8
    sloppy  8
var v = 1; return delete v;   <-- DIFFERENT
    strict  COMPILE SyntaxError 「Delete of an unqualified identifier in strict mode.」
    sloppy  false
undefined = 1; return typeof undefined;   <-- DIFFERENT
    strict  TypeError 「Cannot assign to read only property 'undefined' of object '#<Object>'」
    sloppy  undefined
'ab'.len = 1; return 'ab'.len;   <-- DIFFERENT
    strict  TypeError 「Cannot create property 'len' on string 'ab'」
    sloppy  undefined
var implements = 1; return implements;   <-- DIFFERENT
    strict  COMPILE SyntaxError 「Unexpected strict mode reserved word」
    sloppy  1
var let = 1; return let;   <-- DIFFERENT
    strict  COMPILE SyntaxError 「Unexpected strict mode reserved word」
    sloppy  1

globals left behind: ["js35_3_sloppy","js35_3_strict"]
settings-dependent cells 11 / 14
```

```text
   직접 eval 과 간접 eval 이 변수를 어디에 두나 (탐침 0·3)

   function probe() {                                   전역 (globalThis)
     eval("var G = 1")      ← 직접 eval                    ▲
        비엄격: G 는 probe 의 var 가 된다 (바깥 함수로 샌다)  │
        엄격  : G 는 eval 자기 스코프에 갇힌다                │
     (0, eval)("var G = 1") ← 간접 eval ────────────────────┘ 모드와 상관없이 전역 var 가 된다
   }                                                   (간접 eval 은 전역 코드로 돈다 -- 호출자의 모드를 안 물려받는다)
```

- ★★★ **집계 줄 — `settings-dependent cells 11 / 14`.** 모드와 무관한 세 칸은 **`eval('let …')`**(두 모드 다 갇힌다) · **`(0, eval)('var …')`**(두 모드 다 전역) · **`0o10`**(두 모드 다 `8`)이다.
- ★★★ **누수 확인 — `globals left behind: ["js35_3_sloppy","js35_3_strict"]`.** 남은 것은 **간접 `eval` 탐침 하나의 두 모드**뿐이다.
  ★★ **엄격 쪽도 샜다** — 간접 `eval` 은 **호출자가 엄격이어도 전역 코드로 돈다**(명세 — eval 코드가 엄격이 되는 조건은 「**스스로 지시어를 갖거나, 엄격 코드 안의 직접 eval**」 둘뿐). **「엄격이면 전역이 안 샌다」는 간접 `eval` 앞에서 틀린다.**
  ★ **직접 `eval` 의 비엄격 `number`/`function` 은 전역이 아니라 `probe` 함수의 변수**다 — 그래서 누수 목록에 안 나온다. 「새는 곳」이 **바깥 함수**다.
- ★★★ **컴파일에서 거절된 칸이 일곱** — `with` · `010` · `08` · `'\101'` · `delete v` · `implements` · `let`. 전부 `COMPILE SyntaxError` 다 — **그 본문은 한 줄도 안 돌았다.**
- ★★ **실행에서 거절된 칸이 둘** — `undefined = 1` 은 `TypeError 「Cannot assign to read only property 'undefined' …」`, `'ab'.len = 1` 은 `TypeError 「Cannot create property 'len' on string 'ab'」`. 비엄격은 **둘 다 말없이 넘어가고** 값이 그대로다(`undefined` · `undefined`).
- ★★ **순서가 중요했나** — 이 격자에서 전역을 만드는 탐침은 간접 `eval` 하나이고 **이름이 모드마다 달라** 서로 못 읽는다. 엄격을 먼저 돌린 것은 **처방을 지킨 것**이지, 이 격자에서 순서를 바꿔 보지는 않았다.

### (3) ★★★ `"use strict"` 가 효력을 갖는 자리 — 그리고 쓸 수 없는 자리

**언제 쓰나** — 파일 앞에 주석·배너·다른 파일이 붙을 때 · 함수 하나만 엄격으로 만들고 싶을 때.

```js
// js32b-35b-directive.js
// "use strict" 는 어디에 어떻게 써야 효력이 있나 -- 본문마다 new Function 으로 컴파일하고 안쪽 함수의 this 로 모드를 읽는다.
// (전역에 아무것도 만들지 않는 판별이다 -- 암시적 전역을 쓰지 않는다.)
const TEST = 'return (function () { return this === undefined ? "strict" : "sloppy"; })();';
const BODIES = [
  ['"use strict"; ...', '"use strict"; ' + TEST],
  ["'use strict'; ...", "'use strict'; " + TEST],
  ['"hello"; "use strict"; ...', '"hello"; "use strict"; ' + TEST],
  ['// note  NEWLINE  "use strict"; ...', '// note\n"use strict"; ' + TEST],
  ['"use strict"  NEWLINE  return ...', '"use strict"\n' + TEST],
  ['var a; "use strict"; ...', 'var a; "use strict"; ' + TEST],
  ['("use strict"); ...', '("use strict"); ' + TEST],
  ['"use\\x20strict"; ...', '"use\\x20strict"; ' + TEST],
  ['"USE STRICT"; ...', '"USE STRICT"; ' + TEST],
];
const show = (e) => e.constructor.name + " 「" + e.message + "」";
const shot = (src) => { try { return String(new Function(src)()); } catch (e) { return show(e); } };
console.log("[1] where the directive sits");
for (const [label, src] of BODIES) console.log("  " + label.padEnd(40) + shot(src));

console.log("[2] a directive inside a function whose parameter list is not simple");
const FORMS = [
  ["function (a = 1) { 'use strict'; }", "(function (a = 1) { 'use strict'; });"],
  ["(a = 1) => { 'use strict'; }", "((a = 1) => { 'use strict'; });"],
  ["({ m(...r) { 'use strict'; } })", "({ m(...r) { 'use strict'; } });"],
  ["class { m({ a }) { 'use strict'; } }", "(class { m({ a }) { 'use strict'; } });"],
  ["class { m(a) { 'use strict'; } }", "(class { m(a) { 'use strict'; } });"],
];
for (const [label, src] of FORMS) {
  let r;
  try { new Function(src); r = "compiles"; } catch (e) { r = "COMPILE " + show(e); }
  console.log("  " + label.padEnd(40) + r);
}
```

```text
===== node20 js32b-35b-directive.js (exit=0) =====
[1] where the directive sits
  "use strict"; ...                       strict
  'use strict'; ...                       strict
  "hello"; "use strict"; ...              strict
  // note  NEWLINE  "use strict"; ...     strict
  "use strict"  NEWLINE  return ...       strict
  var a; "use strict"; ...                sloppy
  ("use strict"); ...                     sloppy
  "use\x20strict"; ...                    sloppy
  "USE STRICT"; ...                       sloppy
[2] a directive inside a function whose parameter list is not simple
  function (a = 1) { 'use strict'; }      COMPILE SyntaxError 「Illegal 'use strict' directive in function with non-simple parameter list」
  (a = 1) => { 'use strict'; }            COMPILE SyntaxError 「Illegal 'use strict' directive in function with non-simple parameter list」
  ({ m(...r) { 'use strict'; } })         COMPILE SyntaxError 「Illegal 'use strict' directive in function with non-simple parameter list」
  class { m({ a }) { 'use strict'; } }    COMPILE SyntaxError 「Illegal 'use strict' directive in function with non-simple parameter list」
  class { m(a) { 'use strict'; } }        compiles
```

```text
   지시어 머리말 = 본문 맨 앞에 연달아 오는 「문자열 식 문장」들

   "hello"; "use strict";  return …     ← 둘 다 머리말 → 엄격
   // 주석  "use strict";  return …     ← 주석은 문장이 아니다 → 엄격
   "use strict"  (줄바꿈)  return …      ← 자동 세미콜론 → 엄격
   var a;   "use strict";  return …     ← 머리말이 이미 끝났다 → 그냥 식 문장 → 비엄격
   ("use strict");                      ← 괄호 식은 머리말이 아니다 → 비엄격
   "use\x20strict";                      ← 이스케이프가 있으면 지시어가 아니다 → 비엄격
   "USE STRICT";                         ← 정확한 글자가 아니다 → 비엄격
```

- ★★★ **`[1]` 아홉 본문 중 엄격이 된 것은 앞의 다섯**이다 — 따옴표 종류 · 앞선 다른 지시어(`"hello"`) · 앞선 주석 · 세미콜론 없는 줄바꿈은 **효력을 안 막는다.**
  **`var a;` 뒤 · 괄호로 감싼 것 · 이스케이프(`\x20`) · 대문자**는 **말없이 비엄격**이다 — 에러도 경고도 없다.
  명세 — 「Use Strict Directive 는 Directive Prologue 안의 식 문장으로, 그 문자열이 **정확히** `"use strict"` 또는 `'use strict'` 인 것 — **EscapeSequence 나 LineContinuation 을 담을 수 없다**」.
- ★★★ **`[2]` 비단순 매개변수 목록이 있으면 `"use strict"` 자체를 쓸 수 없다** — 기본값(`a = 1`) · 화살표 · 나머지(`...r`) · 구조 분해(`{ a }`) 네 형태가 전부 `COMPILE SyntaxError 「Illegal 'use strict' directive in function with non-simple parameter list」`.
  ★★ **클래스 메서드는 이미 엄격인데도 거절된다**(`class { m({ a }) { 'use strict'; } }`) — 규칙이 「엄격이 되나」가 아니라 **「그 본문에 지시어가 있나 × 목록이 단순한가」** 를 보기 때문이다. 단순 목록(`m(a)`)이면 **중복 지시어라도 통과**한다.
  ★ 함수 선언(`function f(a = 1)`) 한 형태는 [08번](../08-function-forms-and-parameters/2-summary.md) 동작 (6)과 [10번](../10-destructuring-assignment/2-summary.md) 동작 (4)가 이미 쟀다 — 이 편은 **화살표·메서드·클래스 메서드**로 넓혔다.

### (4) ★★★ 모듈은 늘 엄격 — 같은 파일을 `.mjs` 와 CommonJS 로

**언제 쓰나** — 스크립트를 ESM(`.mjs`·`"type": "module"`)으로 옮길 때.

```js
// js32b-35-h-mode.mjs
// 같은 글자를 모듈로 한 번, 스크립트(CommonJS)로 한 번 -- 파일 첫머리에 "use strict" 는 없다.
const row = (label, v) => console.log("  " + label.padEnd(52) + v);
const shot = (f) => { try { return String(f()); } catch (e) { return e.constructor.name + " 「" + e.message + "」"; } };
row("top-level this === undefined", this === undefined);
row("plain call: this === undefined", (function () { return this === undefined; })());
row("assign to an undeclared name", shot(() => { js35_mod_leak = 1; return "assigned"; }));
row("direct eval('010')", shot(() => eval("010")));
row("indirect (0, eval)('010')", shot(() => (0, eval)("010")));
row("new Function(...): plain call this === undefined", new Function("return (function () { return this === undefined; })();")());
row("globals left behind", JSON.stringify(Object.keys(globalThis).filter((k) => k.startsWith("js35_"))));
```

```sh
# js32b-35c-module.sh
#!/usr/bin/env bash
# 같은 파일을 모듈로(.mjs 확장자) 한 번, CommonJS 스크립트로(표준 입력 + --input-type=commonjs) 한 번 돌린다.
set -u -o pipefail
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
echo "--- node20 js32b-35-h-mode.mjs"
"$N20" js32b-35-h-mode.mjs
echo "(exit $?)"
echo "--- node20 --input-type=commonjs < js32b-35-h-mode.mjs"
"$N20" --input-type=commonjs < js32b-35-h-mode.mjs
echo "(exit $?)"
```

```text
===== ./js32b-35c-module.sh (exit=0) =====
--- node20 js32b-35-h-mode.mjs
  top-level this === undefined                        true
  plain call: this === undefined                      true
  assign to an undeclared name                        ReferenceError 「js35_mod_leak is not defined」
  direct eval('010')                                  SyntaxError 「Octal literals are not allowed in strict mode.」
  indirect (0, eval)('010')                           8
  new Function(...): plain call this === undefined    false
  globals left behind                                 []
(exit 0)
--- node20 --input-type=commonjs < js32b-35-h-mode.mjs
  top-level this === undefined                        false
  plain call: this === undefined                      false
  assign to an undeclared name                        assigned
  direct eval('010')                                  8
  indirect (0, eval)('010')                           8
  new Function(...): plain call this === undefined    false
  globals left behind                                 ["js35_mod_leak"]
(exit 0)
```

- ★★★ **같은 소스가 모듈로는 엄격, CommonJS 로는 비엄격**이다 — 최상위 `this` · 그냥 부른 함수의 `this` · 선언 안 된 이름 대입 · 직접 `eval('010')` **네 줄이 갈렸고**, 끝줄의 누수 목록도 갈렸다(동작 줄 넷 + 누수 줄 하나). 파일 첫머리에 `"use strict"` 는 **없다.**
  명세 — 「**Module code is always strict mode code.**」 05번이 「ESM 최상위는 안 돌려 봤다」고 남긴 빈 칸이 여기서 채워진다.
- ★★★ **모듈 안에도 비엄격 코드가 있다** — **`new Function(...)` 이 만든 함수**는 `this === undefined` 가 **`false`**(비엄격)이고, **간접 `(0, eval)('010')`** 은 `8` 이다. 둘 다 **호출자의 모드를 물려받지 않는다** — 스스로 `"use strict"` 를 가져야 엄격이다.
  ★ 직접 `eval('010')` 은 **모듈의 엄격을 물려받아** `SyntaxError` 다 — 직접 `eval` 과 간접 `eval` 이 **여기서도** 갈린다(동작 (2)).
- ★★ **누수 확인** — 모듈 판은 `[]`, CommonJS 판은 `["js35_mod_leak"]`. 두 실행은 **다른 프로세스**라 서로 오염시키지 않는다(모듈을 먼저 돌렸다).
- ★ 최상위 `this` 가 CommonJS 에서 `undefined` 가 아닌 것은 **node 의 모듈 래퍼** 사정이다(호스트) — 이 편은 그 값을 찍지 않았다.

## 문법 — 형태와 규칙

★ 이 절은 **형태 표**다 — 모든 동작 주장은 위 동작 절의 캡처 블록과 인용한 편의 블록에서만 한다.

| 형태 | 효력 | 어디서 봤나 |
|---|---|---|
| 스크립트·함수 본문의 **지시어 머리말 안** `"use strict";` / `'use strict';` | 그 스크립트·함수(와 안쪽 전부)가 엄격 | 동작 (3) |
| 머리말 밖 · 괄호 · 이스케이프 · 대소문자 다름 | **효력 없음 — 에러도 경고도 없다** | 동작 (3) |
| 비단순 매개변수 목록인 함수 안의 `"use strict"` | **`SyntaxError`**(모드 무관) | 동작 (3) · 08 · 10 |
| 모듈 코드(`.mjs` · `type="module"`) | 늘 엄격 | 동작 (4) |
| 클래스 선언·표현식의 모든 부분 | 늘 엄격 | 16 |
| `new Function(body)` · 간접 `eval(src)` | body/src 가 **스스로** 지시어를 가질 때만 엄격 | 동작 (2)·(4) |
| 직접 `eval(src)` | 호출자가 엄격이거나 src 가 지시어를 가지면 엄격 | 동작 (2)·(4) |

- **엄격은 안쪽으로 번지고 바깥으로는 안 번진다** — 엄격 함수 안의 함수는 엄격, 엄격 함수를 부른 바깥은 그대로.
- **거절은 둘** — 컴파일(early error)과 실행(예외). 정본 표의 「종류」 칸.

## 어디서 틀리나

### (1) ★★★ 파일 맨 위가 아닌 곳에 `"use strict"` 를 둔다

**말없이 비엄격**이다(동작 (3)) — 번들러가 파일을 이어 붙이거나, 누가 앞에 `var` 한 줄을 넣으면 효력이 사라진다. **모듈로 쓰면 이 문제가 없다.**

### (2) ★★★ 엄격 모드면 전역이 절대 안 샌다고 믿는다

**간접 `eval` 은 엄격 호출자 안에서도 전역 `var` 를 만든다**(동작 (2)의 `js35_3_strict`). 모듈 안의 `new Function` 도 비엄격이다(동작 (4)).

### (3) ★★★ `.mjs` 로 옮겨도 동작이 같을 것이라 믿는다

**모듈은 늘 엄격** — 암시적 전역이 `ReferenceError`, 그냥 부른 함수의 `this` 가 `undefined` 가 된다(동작 (4)). 정본 표의 「엄격」 열 전체가 한꺼번에 켜진다.

### (4) ★★ 기본값 매개변수가 있는 함수에 `"use strict"` 를 넣는다

**`SyntaxError`** 다 — 클래스 메서드 안이어도(동작 (3)의 `[2]`). 파일·모듈 단위로 올린다.

### (5) ★★ 엄격 모드면 모든 조용한 실패가 예외가 된다고 믿는다

**모드 무관 행이 일곱**이다(동작 (1)) — 반대로 **동결 배열의 메서드는 비엄격에서도 던진다**(24번).

### (6) ★★ `010` 을 10 으로 읽는다

**비엄격에서는 8** 이고, **엄격에서는 컴파일이 안 된다**(동작 (2)). 8진수가 필요하면 `0o10`.

### (7) ★ `delete x` 로 변수를 지운다

**비엄격 `false`(안 지워진다), 엄격 `SyntaxError`**(동작 (2)). 변수는 지우는 것이 아니다.

## 구현 세부사항 대 언어 보장

### 명세 보장 — 어느 엔진에서도 같아야 하는 것

- ★★★ **모듈 코드는 늘 엄격 · 클래스의 모든 부분은 엄격**(Strict Mode Code 절).
- ★★★ **Use Strict Directive 의 조건** — 지시어 머리말 안 · 정확한 두 글자열 · 이스케이프·줄 이음 불가.
- ★★★ **비단순 목록 + 지시어 = Syntax Error**(함수 정의의 early error) — 모드와 무관.
- ★★ eval 코드가 엄격이 되는 두 조건 · **`strictEval` 이면 `varEnv` 를 eval 자기 환경으로**(`PerformEval`) · 간접 `eval` 은 전역 환경에서 돈다.
- ★★ `with` · 옛 8진수 리터럴·이스케이프 · `delete 식별자` · 예약어가 엄격에서 early error 인 것. 전체 목록은 **Annex C**.

### 엔진(V8) 구현 · 이 판의 관찰

- 예외 **문구 전부**(`Octal literals are not allowed in strict mode.` · `Delete of an unqualified identifier in strict mode.` · `Illegal 'use strict' directive …`).
- 이 주제 node 탐침이 두 판에서 **한 글자도 같았다**는 것 — 관찰이다.

### 호스트가 정하는 것 — ECMA-262 밖

- ★★ **어느 파일이 모듈인가**(`.mjs`·`--input-type`·`package.json` 의 `"type"`) — node 가 정한다. 명세는 「모듈 코드면 엄격」까지다.
- CommonJS 최상위의 `this` — node 의 모듈 래퍼의 것이다.

### 그래서 이렇게 적으면 틀린다

- ✗ 「`"use strict"` 는 파일 어디에 둬도 된다」 → ○ 「**지시어 머리말 안에서만** — 밖이면 말없이 무시된다」
- ✗ 「엄격 모드에서는 `eval` 이 전역을 못 만든다」 → ○ 「**직접 `eval` 만** 갇힌다 — 간접 `eval` 은 전역 `var` 를 만든다」
- ✗ 「모듈 안의 코드는 전부 엄격이다」 → ○ 「**모듈 코드는** 엄격 — `new Function`·간접 `eval` 이 만든 코드는 스스로 지시어가 없으면 비엄격」
- ✗ 「엄격 모드가 더 빠르다」 → ○ **안 쟀다**

## 언제 쓰고 언제 안 쓰나

- **모듈로 쓴다** — 새 코드는 ESM 이면 엄격이 저절로 켜진다. 지시어의 자리를 신경 쓸 일이 없다.
- **스크립트에는 파일 맨 앞 `"use strict"`** — 주석은 앞에 와도 되지만 **문장은 안 된다.**
- **함수 단위 엄격** — 단순 목록인 함수에서만 가능하다. 기본값·구조 분해·나머지가 있으면 **파일 단위로** 올린다.
- ★ **안 쓰는 자리** — 옛 코드에 **검증 없이** 지시어를 얹는 것. 정본 표의 「비엄격」 열에 기대던 코드(`this` 가 전역 · 암시적 전역 · 조용한 쓰기 실패)가 **예외를 내기 시작한다**(07번 「비용」 문단).

## 핵심 문장

1. ★★★ 엄격 모드는 **조용한 실패를 예외로**(실행), **헷갈리는 문법을 거절로**(컴파일) 바꾼다 — 정본 표 **인용 17행 · 새로 14행**, 그중 **모드 무관이 일곱**이다.
2. ★★★ 새 탐침 열넷의 두 번 컴파일 격자에서 **설정에 달린 칸은 `11 / 14`** 였고, 엄격 먼저 · 고유 전역으로 돌린 뒤 **남은 전역은 간접 `eval` 탐침의 두 모드**뿐이었다 — **엄격 쪽도 샜다.**
3. ★★★ `"use strict"` 는 **지시어 머리말 안에서 정확한 글자로만** 효력이 있고, 아니면 **말없이 무시**된다. 비단순 매개변수 목록이 있으면 **쓸 수조차 없다**(클래스 메서드 안에서도).
4. ★★★ **모듈 코드는 늘 엄격**이다 — 같은 파일이 `.mjs` 로는 엄격, CommonJS 로는 비엄격이었다. 단 모듈 안의 **`new Function`·간접 `eval`** 은 비엄격이다.
5. ★★ 직접 `eval` 은 비엄격에서 `var` 를 **바깥 함수로** 새게 하고 엄격에서 가둔다. 간접 `eval` 은 **모드와 상관없이 전역**이다.

## 관련 자료

- [ECMA-262 — Strict Mode Code](https://tc39.es/ecma262/multipage/ecmascript-language-source-code.html#sec-strict-mode-code) · Directive Prologues · Annex C
- [07 — `this` 바인딩 네 규칙](../07-this-binding-four-rules/2-summary.md) — ★ **경계**: 그쪽이 **`this` 쪽 `9 / 14`** 의 정본.
- [08 — 함수 정의 형태와 매개변수](../08-function-forms-and-parameters/2-summary.md) — ★ **경계**: 그쪽이 **`arguments` `7 / 12` · 매개변수 형태 `7 / 20`** 의 정본.
- [10](../10-destructuring-assignment/2-summary.md) · [12](../12-optional-chaining-nullish-and-logical-assignment/2-summary.md) · [14](../14-property-descriptors-and-freezing/2-summary.md) · [24](../24-array-mutating-methods/2-summary.md) — 쓰기 실패와 모드의 정본들.
- [16 — `class` 문법](../16-class-syntax/2-summary.md) — 클래스 몸통이 늘 엄격인 것 · 누수 `1 / 2`.
- 목록의 **42번 주제**(ESM 모듈) · 목록의 **43번 주제**(CJS 와 ESM 상호운용) — 모듈 자체의 정본.

## 용어 풀이

- **엄격 모드(strict mode)** — `"use strict"` 로 켜는 더 깐깐한 규칙 집합(ES5). 모듈·클래스는 늘 엄격.
- **지시어 머리말(Directive Prologue)** — 본문 맨 앞에 연달아 오는 문자열 식 문장들.
- **Use Strict Directive** — 머리말 안의 정확한 `"use strict"`/`'use strict'`.
- **early error** — 코드를 돌리기 전에(컴파일에서) 내는 오류. 그 코드는 한 줄도 안 돈다.
- **직접 `eval` / 간접 `eval`** — `eval(…)` 로 바로 부른 것 / `(0, eval)(…)` 처럼 다른 경로로 부른 것. 간접은 전역 코드로 돈다.
- **비단순 매개변수 목록** — 기본값·구조 분해·나머지 중 하나라도 있는 목록.
- **암시적 전역** — 선언 없이 대입해 비엄격 모드가 몰래 만드는 전역 프로퍼티.

## 더 들어가면

- **Annex C 의 나머지 항목** — `arguments`·`caller` 접근 제한 등. 정본 표에 없는 항목은 **이 문서가 재지 않았다.**
- **브라우저의 `<script type="module">`** — 이 편은 node `.mjs` 로만 잰다. 명세 문장이 같으므로 같은 결과가 기대되지만 **돌리지 않았다.**
