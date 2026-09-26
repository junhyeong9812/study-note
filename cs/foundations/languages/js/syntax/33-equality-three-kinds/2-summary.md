# js/syntax/33 — 동등성 세 종류: 「`NaN` 과 `-0` 두 행만 가르면 된다 — 쓰는 곳마다 어느 알고리즘인지 한 장에」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> ★★★ **이 편은 「이미 곳곳에서 조각으로 잰 것을 한데 모으는 정본」 편이다.** 격자의 대부분은 앞 편들이 이미 쟀다 —
> [02번](../02-coercion-and-loose-equality/2-summary.md)의 `==`·`===`·`Object.is` **225칸 격자** · [23번](../23-map-set-and-weak-collections/2-summary.md)의 **비교 자리 여덟 곳 × 값의 짝 여덟 개(`9 / 56`)** 와 **`Map` 이 `-0` 을 `+0` 으로 바꿔 저장하는 것** ·
> [26번](../26-array-search-flatten-and-create/2-summary.md)의 **`-0` 은 `indexOf`/`includes` 를 안 가른다**와 **구멍 격자**.
> ★★★ **그래서 다시 재지 않는다.** 동작 (1)의 **정본 표**가 그 조각들을 「**알고리즘 × 쓰는 곳**」 한 장으로 묶고 **칸마다 어느 편에서 쟀나**를 단다.
> **새로 잰 것은 그 표의 빈 칸뿐**이다 — `switch` · `findIndex(x => x === b)` · `Object.defineProperty` 의 재정의 · `Map.groupBy`(ES2024) · 형식화 배열(TypedArray) · `String.prototype.includes`(부적용).
>
> ★★★ **이 주제의 본체는 ② 전수 격자다** — 다만 **새 열만** 돌린다. 23번과 **같은 짝 여덟 개**를 새 자리에 던지고, 열마다 여덟 답의 **서명**(`y`/`n` 여덟 글자)을 뽑아
> **기준 비교 넷(`===` · `Object.is` · `includes` · `==`)의 서명과 같은지를 스크립트가 가른다**(동작 (2)). 사람이 「이것은 `===` 가족」이라고 손으로 분류하지 않는다.
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262 — Testing and Comparison Operations](https://tc39.es/ecma262/multipage/abstract-operations.html#sec-testing-and-comparison-operations) — `IsStrictlyEqual` · `IsLooselyEqual` · `SameValue` · `SameValueZero`
> - 같은 명세의 `CaseClauseIsSelected`(`switch`) · `ValidateAndApplyPropertyDescriptor`(재정의) · `AddValueToKeyedGroup`(`Map.groupBy`) · `%TypedArray%.prototype.includes`/`indexOf` · `OrdinaryHasInstance`
> - 명세 문장은 이 배치가 받아 둔 **ES2026 판 HTML** 에서 읽었다(연산 이름과 짧은 인용만 싣는다).
>
> **실행 검증** — 이 문서의 새 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다.
> 배너의 `node20` 은 `~/.nvm/versions/node/v20.19.6/bin/node`, `node18` 은 기본 PATH 의 `node`(v18.19.1)다.
> ★★★ **`Map.groupBy`(ES2024)는 두 node 판에 없다**(판별 블록). 그래서 같은 격자 파일을 **Chrome 151 에서 한 번 더** 돌려 그 열을 채웠다.
> ★★ **이 주제에서 두 node 판이 갈린 탐침은 없다**(대조기 — 이 배치 전체 `identical 12`).
>
> **버전**
>
> | 무엇 | 판 | 이 머신에서 |
> |---|---|---|
> | `===` · `==` · `switch` · `indexOf` | ES1 · ES3 | 세 판 다 있다 |
> | `Object.is` · `Map`/`Set` · TypedArray `indexOf` | ES2015 | 세 판 다 있다 |
> | `Array.prototype.includes` · TypedArray `includes` | ES2016 | 세 판 다 있다 |
> | `Map.groupBy` | **ES2024** | ★ **두 node 판에 없다** — Chrome 151 로만 돌렸다 |
>
> **★★★ 이 주제가 쓰는 창 — 그리고 부적용인 창**
>
> | 창 | 이 주제에서 무엇을 보나 |
> |---|---|
> | ★★★ **② 전수 격자**(본체) | 새 자리 넷 × 값의 짝 8 — 열마다 서명을 뽑아 **기준 비교와 같은 열 N / M** 을 스크립트가 센다(동작 (2)) |
> | ★★ **④ 예외의 `constructor.name` + `message`** | `Object.defineProperty` 재정의가 **값이 「다르다」고 판정되면** 던지는 `TypeError` — 그 판정이 곧 비교의 답이다(동작 (3)) |
> | ★ **① 추상 연산에 로그 심기** | **부적용** — 네 비교 알고리즘은 사용자 코드를 한 번도 안 부른다(`==` 의 `ToPrimitive` 는 02번이 로그로 쟀다) |
> | ★ **③ 브랜드 태그** | **부적용** — 비교는 값의 종류가 아니라 값 자체를 본다 |
> | ★ **부적용 — 두 번 컴파일**(엄격/비엄격) | 비교 규칙은 모드를 안 탄다 |
> | ★ **안 쟀다 — 성능** | 「`Object.is` 가 `===` 보다 느리다」 같은 문장을 쓰지 않는다 |
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 예외 **문구**(`Cannot redefine property: k`) — V8 의 글자 | ★★★ 격자의 **`y`/`n`** 과 서명 · 「같은 열 N / M」 · 저장된 키가 `-0` 인가 |
> | `Map.groupBy` 열이 **어느 엔진에 있나** — 판의 사정(node 두 판 `(absent)`) | ★★ **이 주제의 탐침에는 재실행에서 흔들린 칸이 없다**(재대조 동일) |
>
> **선행** — [02 — 강제 변환과 `==` 대 `===`](../02-coercion-and-loose-equality/2-summary.md)(직접 선행 — ★★★ **`==`·`===`·`Object.is` 의 675칸**, `===` 와 `Object.is` 가 **정확히 두 칸**에서 갈린다) ·
> [23 — `Map`·`Set` 과 약한 컬렉션](../23-map-set-and-weak-collections/2-summary.md)(★★★ **비교 자리 여덟 곳의 격자 `9 / 56`** · `-0` 을 `+0` 으로 **바꿔 저장** · 집합 연산과 Upsert 의 `-0`) ·
> [26 — 배열 탐색·평탄화·생성](../26-array-search-flatten-and-create/2-summary.md)(★★ **`-0` 은 `indexOf`/`includes` 를 안 가른다** · `lastIndexOf` · 구멍 · `findIndex(Number.isNaN)`) ·
> [14 — 프로퍼티 디스크립터와 동결](../14-property-descriptors-and-freezing/2-summary.md)(재정의가 막히는 27칸 — 동작 (3)의 무대).
> **같은 배치** — [32 — 오류 처리와 `Error`](../32-error-handling-and-error/2-summary.md) · [34 — 타입 검사 관용구](../34-type-checking-idioms/2-summary.md) · [35 — 엄격 모드](../35-strict-mode/2-summary.md).
>
> ★★ **경계 — `==` 의 강제 변환 표는 02번이 정본이다.** 여기서는 `==` 를 **기준 서명 하나**로만 쓴다.
> ★★ **경계 — `switch` 의 나머지 규칙**(fall-through · 라벨)은 목록의 **52번 주제**의 몫이다. 여기서는 **`case` 가 무엇으로 견주나**만 본다.

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

**JS 에는 「같다」를 재는 자가 넷 있다. 그런데 넷이 서로 다른 답을 내는 값은 사실상 둘뿐이다 — `NaN` 과 `-0`.**
(`==` 는 여기에 **타입을 가로지르는 강제 변환**이 더 붙는다 — 그 표는 02번의 것이다.)

- ★★★ **`===`(엄격한 자)** — `NaN` 은 자기 자신과도 **다르다**고 하고, `+0` 과 `-0` 은 **같다**고 한다.
- ★★★ **`Object.is`(가장 고지식한 자, SameValue)** — `NaN` 은 `NaN` 과 **같고**, `+0` 과 `-0` 은 **다르다.** 비트 하나까지 본다.
- ★★★ **SameValueZero(열쇠 보관함의 자)** — `NaN` 은 **같고**, `+0` 과 `-0` 도 **같다.** 「찾기」에 가장 편한 자다.
- ★★ 그래서 **어떤 자를 쓰는 곳인지만 알면** 답이 나온다 — `Map` 키·`Set`·`includes` 는 SameValueZero, `indexOf`·`switch` 는 `===`, `Object.defineProperty` 는 SameValue.

```text
                    NaN, NaN        0, -0         쓰는 곳 (대표)
                    --------        -----
   SameValue        같다            다르다        Object.is · defineProperty 재정의
   SameValueZero    같다            같다          Map 키 · Set · includes · Map.groupBy
   IsStrictlyEqual  다르다          같다          === · indexOf · switch
   IsLooselyEqual   다르다          같다          == (+ '1'==1 · null==undefined 같은 강제 변환)

   ★ 이 두 열만 외우면 된다. 나머지 행(1 과 1.0 · 같은 객체 · 다른 두 객체)은 넷이 다 같다(== 의 강제 변환 제외)
```

**비유 대응표**

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 엄격한 자 | `IsStrictlyEqual` — `===`·`indexOf`·`switch` | 서명 `nynynnny` |
| 가장 고지식한 자 | `SameValue` — `Object.is`·재정의 판정 | 서명 `ynnynnny` |
| 열쇠 보관함의 자 | `SameValueZero` — `Map`·`Set`·`includes`·`groupBy` | 서명 `yynynnny` |
| 헐거운 자 | `IsLooselyEqual` — `==` | 서명 `nyyyyyny` |
| 보관함 입구에서 부호를 지운다 | `Map`/`Set`/`groupBy` 가 **`-0` 을 `+0` 으로 바꿔 저장** — 배열은 안 바꾼다 | 23번 동작 (2) · 이 편 동작 (4) |

**똑같은 구조다** — 실무에서 물리는 자리.
「**계산 결과가 `NaN` 인 원소를 `indexOf` 로 찾았더니 `-1` 이었다**」와
「**`switch (x) { case NaN: … }` 가 한 번도 안 걸렸다**」가 같은 자(`===`)의 같은 행에서 나온다(동작 (1)·(2)).

> **서명(signature)** — 이 문서의 말. 값의 짝 여덟 개를 한 비교에 던진 `y`/`n` 여덟 글자. **서명이 같으면 같은 알고리즘으로 본다.**\
> 예: `===` 의 서명은 `nynynnny` — 첫 글자가 `NaN, NaN`, 둘째가 `0, -0`.

## 이 주제가 답하려는 질문

1. **`===`·`Object.is`·SameValueZero(그리고 `==`)는 정확히 어느 값에서 갈리나** — 그리고 **언어의 어느 자리가 어느 것을 쓰나**?
2. **「찾기」 계열은 왜 `NaN` 에서 서로 다른 답을 내나** — `indexOf`/`includes`/`switch`/`findIndex`/TypedArray 를 한 표로 읽을 수 있나?
3. **비교가 「저장」까지 바꾸는 자리는 어디인가** — `-0` 을 넣으면 무엇이 남나?

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 출력으로 읽는다.

### (1) ★★★ 정본 표 — 알고리즘 × 쓰는 곳, 칸마다 「어디서 쟀나」

**언제 쓰나** — 「이 자리는 `NaN` 을 찾나 · `-0` 을 가르나」를 물을 때. **외울 것은 이 표 하나다.**
★★★ **인용 행**은 앞 편의 블록이 근거다(링크의 동작 번호). **새 행**은 이 편 동작 (2)\~(4)가 근거다.

| 쓰는 곳 | 알고리즘 | `NaN, NaN` | `0, -0` | 저장이 바뀌나 | 어디서 쟀나 |
|---|---|---|---|---|---|
| `a === b` | IsStrictlyEqual | 다르다 | 같다 | — | 인용 — [02](../02-coercion-and-loose-equality/2-summary.md) 동작 (3)(225칸) · [23](../23-map-set-and-weak-collections/2-summary.md) 동작 (1) |
| `a == b` | IsLooselyEqual | 다르다 | 같다 | — | 인용 — 02 동작 (3) · 23 동작 (1) |
| `Object.is(a, b)` | SameValue | 같다 | 다르다 | — | 인용 — 02 동작 (3) · 23 동작 (1) |
| `Map` 키 · `Set` 원소 | SameValueZero | 같다 | 같다 | ★ **`-0` → `+0`** | 인용 — 23 동작 (1)·(2) |
| `Set` 집합 연산(`intersection` 등) | SameValueZero | 같다 | 같다 | — | 인용 — 23 동작 (7)(`[NaN,0]`) |
| `Map.prototype.getOrInsertComputed` | SameValueZero | — | 같다 | ★ **콜백이 받는 키가 `+0`** | 인용 — 23 동작 (8) |
| `Array.prototype.includes` | SameValueZero | 같다 | 같다 | — (배열은 `-0` 그대로) | 인용 — 23 동작 (1) · [26](../26-array-search-flatten-and-create/2-summary.md) 동작 (2) |
| `Array.prototype.indexOf` · `lastIndexOf` | IsStrictlyEqual | 다르다 | 같다 | — | 인용 — 23 동작 (1) · 26 동작 (2) |
| `findIndex(Number.isNaN)` · `x !== x` | 사용자 함수 | 찾는다 | — | — | 인용 — 26 동작 (2) |
| 평범한 객체의 키 | 비교가 아니라 **글자로 바꾼 뒤** | 같다(`"NaN"`) | 같다(`"0"`) | 키가 글자 | 인용 — 23 동작 (1)(`object key` 열) |
| ★ **`switch` 의 `case`** | IsStrictlyEqual | 다르다 | 같다 | — | **새로** — 동작 (2) |
| ★ **`findIndex(x => x === b)`** | IsStrictlyEqual(사용자가 쓴 `===`) | 다르다 | 같다 | — | **새로** — 동작 (2) |
| ★ **`Object.defineProperty` 재정의**(쓰기 불가·설정 불가) | SameValue | 같다(통과) | 다르다(`TypeError`) | — | **새로** — 동작 (2)·(3) |
| ★ **`Map.groupBy` 의 키** | SameValueZero | 같다 | 같다 | ★ **`-0` → `+0`** | **새로** — 동작 (2)·(4)(Chrome) |
| ★ **TypedArray `includes`** | SameValueZero | 같다 | 같다 | `Float64Array` 는 `-0` 그대로 · `Int32Array` 는 정수로 | **새로** — 동작 (3) |
| ★ **TypedArray `indexOf`** | IsStrictlyEqual | 다르다 | — | — | **새로** — 동작 (3) |
| ★ **`String.prototype.includes`** | **부적용** — 비교가 아니라 `ToString` 뒤 부분 문자열 | (`'NaN'.includes(NaN)` 참) | (`String(-0)` 이 `"0"`) | — | **새로** — 동작 (3) |

- ★★★ **인용 10행 · 새로 잰 7행**이다. 새 7행 중 **6행은 비교 알고리즘 하나로 떨어지고**, `String.prototype.includes` 한 행은 **비교가 아님**을 보였다(부적용).
- ★★★ **`NaN` 을 찾는 자리와 못 찾는 자리가 한 줄로 갈린다** — SameValueZero·SameValue 쪽(`includes`·`Map`·`Set`·`groupBy`·`Object.is`)은 찾고, `===` 쪽(`indexOf`·`switch`·`findIndex(x => x === b)`)은 못 찾는다.
- ★★★ **`-0` 을 가르는 자리는 SameValue 둘뿐**이다 — `Object.is` 와 **`Object.defineProperty` 의 재정의 판정**. 나머지는 전부 `+0` 과 같다고 본다.
- ★★ **저장까지 바꾸는 자리는 「키를 보관하는」 셋** — `Map`·`Set`·`Map.groupBy`. **배열(`includes`)은 비교만 SameValueZero 이고 저장은 그대로**다(26번).
- ★ `instanceof` 도 명세상 **SameValue** 를 쓴다(`OrdinaryHasInstance` 가 프로토타입 객체를 `SameValue` 로 견준다) — 그러나 **객체끼리의 비교라 `===` 와 구별할 방법이 없다.** 잴 것이 없어 표에 넣지 않았다(부적용).

### (2) ★★★ 새 자리 넷 × 값의 짝 여덟 — 서명으로 가족을 가른다

**언제 쓰나** — 「이 API 는 어느 자를 쓰나」를 **문서를 안 보고** 알아낼 때. 같은 짝 여덟 개를 던지고 **서명을 기준과 대조**한다.
★★★ 짝 여덟 개는 **23번 동작 (1)과 똑같다** — 그래야 23번의 여덟 열과 이 편의 네 열이 **한 격자**로 이어진다.

```js
// js32b-33-h-equality-core.js
// 23번 격자와 같은 값의 짝 여덟 개를, 23번이 안 물은 자리들에 던진다.
// 자리마다 y/n 서명을 뽑아 기준 비교 넷(===, Object.is, [a].includes(b), ==)의 서명과 견준다.
// node 와 Chrome 이 이 파일을 같이 쓴다(Map.groupBy 를 못 찾으면 그 열은 (absent) 로 찍는다).
globalThis.equalityGrid = function equalityGrid() {
  const one = { a: 1 };
  const pairs = [
    ["NaN, NaN", NaN, NaN],
    ["0, -0", 0, -0],
    ["'1', 1", "1", 1],
    ["1, 1.0", 1, 1.0],
    ["true, 1", true, 1],
    ["null, undefined", null, undefined],
    ["{a:1}, {a:1}  (two objects)", one, { a: 1 }],
    ["o, o  (one object)", one, one],
  ];
  const refs = [
    ["===", (a, b) => a === b],
    ["Object.is", (a, b) => Object.is(a, b)],
    ["includes", (a, b) => [a].includes(b)],
    ["==", (a, b) => a == b],
  ];
  const cols = [
    ["switch", (a, b) => { switch (a) { case b: return true; default: return false; } }],
    ["findIndex===", (a, b) => [a].findIndex((x) => x === b) !== -1],
    ["redefine", (a, b) => {
      const o = Object.defineProperty({}, "k", { value: a, writable: false, configurable: false });
      try { Object.defineProperty(o, "k", { value: b }); return true; } catch (e) { return false; }
    }],
    ["groupBy", typeof Map.groupBy === "function"
      ? (a, b) => Map.groupBy([a, b], (x) => x).size === 1
      : null],
  ];
  const sig = (f) => pairs.map(([, a, b]) => (f(a, b) ? "y" : "n")).join("");
  const refSig = refs.map(([n, f]) => [n, sig(f)]);
  console.log(("  " + "".padEnd(30) + cols.map(([n]) => n.padEnd(14)).join("")).trimEnd());
  const colSig = cols.map(([, f]) => (f ? sig(f) : null));
  pairs.forEach(([label], i) => {
    console.log(("  " + label.padEnd(30) + colSig.map((s) => (s ? s[i] : "(absent)").padEnd(14)).join("")).trimEnd());
  });
  console.log("");
  console.log("  which reference comparison gives the same eight answers:");
  let asked = 0, matched = 0;
  cols.forEach(([n], i) => {
    if (!colSig[i]) { console.log("    " + n.padEnd(22) + "(absent in this runtime)"); return; }
    asked += 1;
    const same = refSig.filter(([, s]) => s === colSig[i]).map(([r]) => r);
    if (same.length) matched += 1;
    console.log("    " + n.padEnd(22) + colSig[i] + "   " + (same.length ? same.join(" / ") : "(none)"));
  });
  refSig.forEach(([n, s]) => console.log("    " + ("reference " + n).padEnd(22) + s));
  console.log("new columns whose signature equals a reference column: " + matched + " / " + asked);
};
```

```js
// js32b-33a-new-places.js
// 23번이 안 물은 비교 자리들 -- 격자는 js32b-33-h-equality-core.js 에 있다(Chrome 판은 js32b-33b-new-places.web.js).
require("./js32b-33-h-equality-core.js");
equalityGrid();
```

```text
===== node20 js32b-33a-new-places.js (exit=0) =====
                                switch        findIndex===  redefine      groupBy
  NaN, NaN                      n             n             y             (absent)
  0, -0                         y             y             n             (absent)
  '1', 1                        n             n             n             (absent)
  1, 1.0                        y             y             y             (absent)
  true, 1                       n             n             n             (absent)
  null, undefined               n             n             n             (absent)
  {a:1}, {a:1}  (two objects)   n             n             n             (absent)
  o, o  (one object)            y             y             y             (absent)

  which reference comparison gives the same eight answers:
    switch                nynynnny   ===
    findIndex===          nynynnny   ===
    redefine              ynnynnny   Object.is
    groupBy               (absent in this runtime)
    reference ===         nynynnny
    reference Object.is   ynnynnny
    reference includes    yynynnny
    reference ==          nyyyyyny
new columns whose signature equals a reference column: 3 / 3
```

```js
// js32b-33b-new-places.web.js
// 같은 격자를 Chrome 에서 -- 이어서 Map.groupBy 가 -0 에 대해 저장하는 키.
equalityGrid();
console.log("");
console.log("[2] the key Map.groupBy stores for -0");
const k = [...Map.groupBy([-0], (x) => x).keys()][0];
console.log("  Object.is(stored key, -0)   " + Object.is(k, -0));
console.log("  Object.is(stored key, +0)   " + Object.is(k, 0));
```

```text
===== google-chrome --headless --virtual-time-budget=2000 --dump-dom 'js32b-page.html?js32b-33-h-equality-core.js,js32b-33b-new-places.web.js' | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' | sed 's/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&amp;/\&/g' (exit=0) =====
                                switch        findIndex===  redefine      groupBy
  NaN, NaN                      n             n             y             y
  0, -0                         y             y             n             y
  '1', 1                        n             n             n             n
  1, 1.0                        y             y             y             y
  true, 1                       n             n             n             n
  null, undefined               n             n             n             n
  {a:1}, {a:1}  (two objects)   n             n             n             n
  o, o  (one object)            y             y             y             y

  which reference comparison gives the same eight answers:
    switch                nynynnny   ===
    findIndex===          nynynnny   ===
    redefine              ynnynnny   Object.is
    groupBy               yynynnny   includes
    reference ===         nynynnny
    reference Object.is   ynnynnny
    reference includes    yynynnny
    reference ==          nyyyyyny
new columns whose signature equals a reference column: 4 / 4

[2] the key Map.groupBy stores for -0
  Object.is(stored key, -0)   false
  Object.is(stored key, +0)   true
```

```text
   서명 = 여덟 짝에 대한 y/n 여덟 글자        ( NaN · 0/-0 · '1'/1 · 1/1.0 · true/1 · null/undef · 두 객체 · 한 객체 )

   switch          n y n y n n n y   ─┐
   findIndex===    n y n y n n n y   ─┴─ = ===         의 서명
   redefine        y n n y n n n y   ─── = Object.is   의 서명
   groupBy         y y n y n n n y   ─── = includes    의 서명  (SameValueZero)

   ★ 네 열이 모두 기준 넷 중 하나와 글자까지 같다 -- 새 알고리즘은 없다
```

- ★★★ **집계 줄 — node 20 은 `3 / 3`, Chrome 151 은 `4 / 4`** 다(`new columns whose signature equals a reference column`). node 판에는 `Map.groupBy` 가 없어 **그 열이 `(absent)`** 로 빠졌다.
- ★★★ **`switch` 는 `===`** 다 — `NaN, NaN` 에서 `n`(`case NaN:` 은 절대 안 걸린다), `0, -0` 에서 `y`. 명세 `CaseClauseIsSelected` 가 **`IsStrictlyEqual(input, clauseSelector)`** 를 돌려준다.
- ★★ **`findIndex(x => x === b)` 도 `===`** 다 — 당연하다. **비교를 쓴 것이 사용자이기 때문이다.** 26번의 `findIndex(Number.isNaN)` 이 `NaN` 을 찾은 것은 **술어가 다른 자를 썼기 때문**이다.
- ★★★ **`Object.defineProperty` 재정의는 SameValue** 다 — `NaN, NaN` 은 통과(`y`), **`0, -0` 은 거절(`n`)** — 동작 (3)에서 그 거절이 `TypeError` 로 보인다.
- ★★★ **`Map.groupBy` 는 SameValueZero**(Chrome 151). 그리고 `[2]` — **저장된 키가 `+0`** 이다(`Object.is(stored key, -0) false`). 23번의 `Map` 과 같은 입구다(동작 (4)).
- ★ `reference` 네 줄은 **23번이 이미 잰 네 열을 이 격자 안에서 기준으로 다시 뽑은 것**이다 — 새 결과가 아니다(23번 격자의 `===`·`Object.is`·`includes`·`==` 열과 글자가 같다).

### (3) ★★ 격자 밖 세 자리 — TypedArray · 문자열의 `includes` · 재정의의 예외

**언제 쓰나** — 숫자 버퍼(`Float64Array`)에서 `NaN` 을 찾을 때 · 문자열 검색에 숫자를 넘길 때 · 동결된 객체의 값을 「같은 값으로」 다시 정의할 때.

```js
// js32b-33c-typed-and-string.js
// 23번 격자 밖의 찾기 셋 -- 형식화 배열(TypedArray) · 문자열의 includes · 그리고 Object.defineProperty 가 값을 견주는 자리.
const row = (label, v) => console.log("  " + label.padEnd(48) + v);
const shot = (f) => { try { return String(f()); } catch (e) { return e.constructor.name + " 「" + e.message + "」"; } };

console.log("[1] TypedArray -- the same two methods as on arrays");
row("new Float64Array([NaN]).indexOf(NaN)", new Float64Array([NaN]).indexOf(NaN));
row("new Float64Array([NaN]).includes(NaN)", new Float64Array([NaN]).includes(NaN));
row("new Float64Array([-0]).includes(0)", new Float64Array([-0]).includes(0));
row("Object.is(new Float64Array([-0])[0], -0)", Object.is(new Float64Array([-0])[0], -0));
row("Object.is(new Int32Array([-0])[0], -0)", Object.is(new Int32Array([-0])[0], -0));
row("new Float64Array([1]).includes('1')", new Float64Array([1]).includes("1"));
row("new Float64Array([1]).indexOf('1')", new Float64Array([1]).indexOf("1"));

console.log("[2] String.prototype.includes -- given a number");
row("'NaN'.includes(NaN)", "NaN".includes(NaN));
row("'-0'.includes(-0)", "-0".includes(-0));
row("'10'.includes(1)", "10".includes(1));
row("String(-0)", JSON.stringify(String(-0)));

console.log("[3] Object.defineProperty on a non-writable, non-configurable property");
const mk = (v) => Object.defineProperty({}, "k", { value: v, writable: false, configurable: false });
row("value 0, redefine with -0", shot(() => (Object.defineProperty(mk(0), "k", { value: -0 }), "ok")));
row("value NaN, redefine with 0/0", shot(() => (Object.defineProperty(mk(NaN), "k", { value: 0 / 0 }), "ok")));
row("value 0, redefine with 0", shot(() => (Object.defineProperty(mk(0), "k", { value: 0 }), "ok")));
row("frozen { k: 0 }, redefine with -0", shot(() => (Object.defineProperty(Object.freeze({ k: 0 }), "k", { value: -0 }), "ok")));
```

```text
===== node20 js32b-33c-typed-and-string.js (exit=0) =====
[1] TypedArray -- the same two methods as on arrays
  new Float64Array([NaN]).indexOf(NaN)            -1
  new Float64Array([NaN]).includes(NaN)           true
  new Float64Array([-0]).includes(0)              true
  Object.is(new Float64Array([-0])[0], -0)        true
  Object.is(new Int32Array([-0])[0], -0)          false
  new Float64Array([1]).includes('1')             false
  new Float64Array([1]).indexOf('1')              -1
[2] String.prototype.includes -- given a number
  'NaN'.includes(NaN)                             true
  '-0'.includes(-0)                               true
  '10'.includes(1)                                true
  String(-0)                                      "0"
[3] Object.defineProperty on a non-writable, non-configurable property
  value 0, redefine with -0                       TypeError 「Cannot redefine property: k」
  value NaN, redefine with 0/0                    ok
  value 0, redefine with 0                        ok
  frozen { k: 0 }, redefine with -0               TypeError 「Cannot redefine property: k」
```

- ★★★ **`[1]` TypedArray 는 배열과 같은 짝을 쓴다** — `indexOf(NaN)` 은 `-1`, `includes(NaN)` 은 `true`. 명세가 TypedArray `includes` 를 **SameValueZero** 로, `indexOf` 를 **IsStrictlyEqual** 로 적는다.
  ★★ **`'1'` 은 못 찾는다**(`false` · `-1`) — 저장할 때는 숫자로 바꾸지만 **찾는 값은 안 바꾼다.**
- ★★ **`-0` 은 원소 타입이 정한다** — `Float64Array` 는 **`-0` 그대로**(`true`), `Int32Array` 는 **정수로 바꿔 `+0`**(`false`). 비교가 아니라 **저장 형식**의 이야기다.
- ★★★ **`[2]` `String.prototype.includes` 는 동등성이 아니다** — 인자를 **글자로 바꾼 뒤 부분 문자열**을 찾는다. `'NaN'.includes(NaN)` 이 `true` 인 것은 `NaN` 이 `"NaN"` 이 되기 때문이고, **`'10'.includes(1)` 도 `true`** 다. `String(-0)` 이 `"0"` 이라 `'-0'.includes(-0)` 도 `true`. **정본 표에서 부적용 행**이다.
- ★★★ **`[3]` 재정의 판정은 SameValue** — 값이 `0` 인 쓰기 불가·설정 불가 프로퍼티를 **`-0` 으로 재정의하면 `TypeError 「Cannot redefine property: k」`**, `NaN` 을 **다른 식으로 만든 `NaN`(`0/0`)으로 재정의하면 `ok`**, `0` 을 `0` 으로는 `ok`. `Object.freeze` 한 객체도 같다.
  ★ 명세 `ValidateAndApplyPropertyDescriptor` 가 「**`SameValue(Desc.[[Value]], current.[[Value]])` 를 돌려준다**」이고, 바로 위 NOTE 가 이유를 적는다 — 「SameValue returns true for NaN values which may be distinguishable by other means」. **`NaN` 들은 비트가 달라도 같은 값으로 보고, `+0`/`-0` 은 다른 값으로 본다.** 14번의 재정의 격자가 이 판정 위에 서 있다.

### (4) ★★ 비교가 저장을 바꾸는 자리 — `-0` 을 넣으면 무엇이 남나

**언제 쓰나** — 계산 결과(`-0` 이 나올 수 있다)를 키로 쓰고, **꺼낸 키**를 다시 부호에 민감한 곳에 넘길 때.

```text
   넣은 것 -0              무엇이 남나                     근거
   ─────────────────────────────────────────────────────────────────────
   Map.set(-0, …)          +0  (입구에서 접힌다)            23번 동작 (2)  — CanonicalizeKeyedCollectionKey
   new Set([-0])           +0                              23번 동작 (2)
   Map.groupBy([-0], id)   +0                              이 편 동작 (2)의 [2] (Chrome)
   getOrInsertComputed(-0) 콜백이 받는 키가 +0             23번 동작 (8)
   [-0]                    -0  (배열은 그대로)              26번 동작 (2)
   new Float64Array([-0])  -0                              이 편 동작 (3)
   new Int32Array([-0])    +0  (정수 저장 형식)              이 편 동작 (3)
   { [-0]: 1 }             "0" (키는 글자)                  23번 동작 (1)의 object key 열
```

- ★★★ **「키를 보관하는」 자리는 `-0` 을 `+0` 으로 바꿔 저장한다** — 비교를 SameValueZero 로 하는 **대신** 입구에서 부호를 지운다. 명세의 `GroupBy` 는 `Map.groupBy` 의 키를 **`Map` 과 같은 연산 `CanonicalizeKeyedCollectionKey`** 에 통과시킨다(「key 가 `-0` 이면 `+0` 을 돌려준다」).
- ★★ **배열은 비교(`includes`)만 SameValueZero 이고 저장은 그대로다** — 「`includes` 가 `-0` 을 `0` 과 같다고 했으니 배열에도 `0` 이 들어 있다」는 틀린다.

## 문법 — 형태와 규칙

★ 이 절은 **형태 표**다 — 모든 동작 주장은 위 동작 절의 캡처 블록과 인용한 편의 블록에서만 한다.

| 형태 | 알고리즘 | `NaN` 을 찾나 | `-0` 을 가르나 | 어디서 봤나 |
|---|---|---|---|---|
| `a === b` · `switch` · `indexOf` · `lastIndexOf` · TypedArray `indexOf` | IsStrictlyEqual | 아니다 | 아니다 | 02 · 23 · 26 · 동작 (2)·(3) |
| `Object.is(a, b)` · `defineProperty` 재정의 | SameValue | 찾는다 | **가른다** | 02 · 23 · 동작 (2)·(3) |
| `includes` · `Map` · `Set` · `Map.groupBy` · TypedArray `includes` | SameValueZero | 찾는다 | 아니다 | 23 · 26 · 동작 (2)·(3) |
| `a == b` | IsLooselyEqual | 아니다 | 아니다 | 02 |

- **`NaN` 을 찾고 싶으면** `includes` · `Number.isNaN` · `Object.is`. **인덱스가 필요하면** `findIndex(Number.isNaN)`(26번).
- **`-0` 을 가르고 싶으면** `Object.is` 하나뿐이다.

## 어디서 틀리나

### (1) ★★★ `switch (x) { case NaN: … }` 로 `NaN` 을 거른다

**절대 안 걸린다**(동작 (2) — `switch` 의 서명이 `===` 와 같다). `if (Number.isNaN(x))` 를 먼저 둔다.

### (2) ★★★ `indexOf` 를 `includes` 로(또는 거꾸로) 바꿔도 같다고 믿는다

**`NaN` 행에서 갈린다**(23번 · 26번). 게다가 **구멍 행에서도** 갈린다(26번 동작 (1)).

### (3) ★★★ `Object.is` 를 「더 엄격한 `===`」로 읽는다

**두 칸이 서로 반대로** 갈린다 — `NaN` 은 `Object.is` 가 같다, `-0` 은 `===` 가 같다(02번 · 이 편 동작 (1)).

### (4) ★★ `Map` 에서 꺼낸 키가 넣은 `-0` 그대로일 것이라 믿는다

**`+0` 이다** — `Map`·`Set`·`Map.groupBy` 가 전부(동작 (4)).

### (5) ★★ 배열의 `includes(0)` 이 참이면 배열 안에 `+0` 이 있다고 믿는다

**`-0` 일 수 있다** — 배열은 부호를 그대로 담는다(26번).

### (6) ★★ `'10'.includes(1)` 을 「`1` 이 있나」로 읽는다

**문자열 검색**이다 — 동등성이 아니다(동작 (3)의 `[2]`).

### (7) ★ 동결된 객체를 「같은 값으로」 다시 정의하면 늘 통과한다고 믿는다

**`0` 을 `-0` 으로 재정의하면 `TypeError`** 다 — 재정의 판정은 SameValue(동작 (3)의 `[3]`).

## 구현 세부사항 대 언어 보장

### 명세 보장 — 어느 엔진에서도 같아야 하는 것

- ★★★ 네 알고리즘의 정의 — `IsStrictlyEqual` · `IsLooselyEqual` · `SameValue` · `SameValueZero` 가 `NaN`·`±0` 에서 갈리는 방식.
- ★★★ **어느 자리가 어느 알고리즘을 부르나** — `CaseClauseIsSelected` 의 `IsStrictlyEqual` · `ValidateAndApplyPropertyDescriptor` 의 `SameValue` · `Map.groupBy` 의 `CanonicalizeKeyedCollectionKey` + `AddValueToKeyedGroup` 의 `SameValue`(키를 먼저 `+0` 으로 접은 뒤 — 결과적으로 SameValueZero) · TypedArray `includes`/`indexOf` · `Array.prototype.includes`/`indexOf`.
- ★★ `Map`/`Set`/`Map.groupBy` 가 **`-0` 을 `+0` 으로 접어 저장하는 것**.

### 엔진(V8) 구현 · 이 판의 관찰

- 재정의 실패의 **문구**(`Cannot redefine property: k`).
- `Map.groupBy` 가 **node 18·20 에 없고 Chrome 151 에 있는 것** — 판의 사정.

### 호스트가 정하는 것 — ECMA-262 밖

- ★ **라이브러리·프레임워크의 비교**(상태 변경 감지에 `Object.is` 를 쓰는 UI 라이브러리 등) — **언어 밖**이다. 이 문서는 **언어 안의 자리만** 표에 넣었다(부적용).

### 그래서 이렇게 적으면 틀린다

- ✗ 「동등성은 `==` 와 `===` 두 가지다」 → ○ 「**알고리즘이 넷**이고, 언어의 자리마다 그중 하나를 쓴다」
- ✗ 「`switch` 는 `==` 로 견준다」 → ○ 「**`===`**(`IsStrictlyEqual`)」
- ✗ 「`Map` 은 SameValueZero 라서 `-0` 키를 `-0` 으로 들고 있다」 → ○ 「**`+0` 으로 접혀 들어간다**」(23번)
- ✗ 「`Object.is` 는 느리다」 → ○ **안 쟀다**

## 언제 쓰고 언제 안 쓰나

- **`===`** — 기본값. `NaN`·`-0` 이 섞일 수 없는 자리.
- **`Number.isNaN` / `includes`** — `NaN` 을 찾아야 할 때.
- **`Object.is`** — **`-0` 을 가려야 할 때**(부호가 뜻을 갖는 수치 코드) · 「정말 같은 값인가」를 물을 때.
- **`Map`/`Set`** — `NaN` 을 키로 써도 된다. 단 **`-0` 은 `+0` 으로 돌아온다.**
- ★ **안 쓰는 자리** — `switch` 로 `NaN` 거르기 · `String.prototype.includes` 에 숫자를 넘겨 「값이 있나」 묻기.

## 핵심 문장

1. ★★★ 동등성 알고리즘은 **넷**(IsStrictlyEqual · IsLooselyEqual · SameValue · SameValueZero)이고, `==` 의 강제 변환을 빼면 **`NaN` 과 `-0` 두 행에서만** 갈린다.
2. ★★★ **`NaN` 을 찾는 자리**는 SameValue·SameValueZero 쪽(`Object.is`·`includes`·`Map`·`Set`·`groupBy`)이고, **`-0` 을 가르는 자리**는 SameValue 둘(`Object.is`·`defineProperty` 재정의)뿐이다.
3. ★★★ 새로 잰 네 열(`switch`·`findIndex(===)`·재정의·`groupBy`)은 **전부 기준 넷 중 하나와 서명이 글자까지 같았다**(node `3 / 3` · Chrome `4 / 4`).
4. ★★ `Map`·`Set`·`Map.groupBy` 는 **`-0` 을 `+0` 으로 바꿔 저장**하고, 배열과 `Float64Array` 는 그대로 담는다.
5. ★★ `String.prototype.includes` 는 동등성이 아니다 — **글자로 바꾼 뒤의 부분 문자열 검색**이다.

## 관련 자료

- [ECMA-262 — Testing and Comparison Operations](https://tc39.es/ecma262/multipage/abstract-operations.html#sec-testing-and-comparison-operations)
- [02 — 강제 변환과 `==` 대 `===`](../02-coercion-and-loose-equality/2-summary.md) — ★ **경계**: 그쪽이 **`==` 의 강제 변환 225칸**의 정본, 여기는 `==` 를 **서명 하나**로만.
- [23 — `Map`·`Set` 과 약한 컬렉션](../23-map-set-and-weak-collections/2-summary.md) — ★ **경계**: 그쪽이 **여덟 자리 격자 `9 / 56`** 과 **`-0` 저장**의 정본, 여기는 **그 격자에 네 열을 더하고 한 장으로 묶는 것**.
- [26 — 배열 탐색·평탄화·생성](../26-array-search-flatten-and-create/2-summary.md) — `-0` · 구멍 · `lastIndexOf` · `findIndex(Number.isNaN)` 의 정본.
- [14 — 프로퍼티 디스크립터와 동결](../14-property-descriptors-and-freezing/2-summary.md) — 재정의가 막히는 격자(동작 (3)의 무대).
- 목록의 **52번 주제**(`switch`·라벨·흐름 제어 세부) — `switch` 의 나머지 규칙.
- 파이썬의 「같은 키」 규칙(정체 먼저, 그다음 `==`)과의 대비는 **23번 동작 (9)** 가 정본이다 — 이 편은 다시 돌리지 않았다.

## 용어 풀이

- **IsStrictlyEqual** — `===`. 타입이 다르면 다르다. `NaN` 은 자기와 다르고 `+0`/`-0` 은 같다.
- **IsLooselyEqual** — `==`. 타입이 다르면 강제 변환 뒤 다시 견준다(02번).
- **SameValue** — `Object.is`. `NaN` 끼리 같고 `+0`/`-0` 은 다르다.
- **SameValueZero** — `NaN` 끼리 같고 `+0`/`-0` 도 같다. 「찾기」와 「키」가 쓴다.
- **서명** — 이 문서의 말. 짝 여덟 개에 대한 `y`/`n` 여덟 글자.
- **`CaseClauseIsSelected`** — `switch` 의 `case` 가 걸리나를 정하는 명세 연산. `IsStrictlyEqual` 을 돌려준다.
- **`ValidateAndApplyPropertyDescriptor`** — `defineProperty` 가 기존 프로퍼티를 바꿔도 되나를 정하는 명세 연산. 값은 `SameValue` 로 견준다.
- **형식화 배열(TypedArray)** — `Float64Array`·`Int32Array` 처럼 한 가지 숫자 형식으로 저장하는 배열.

## 더 들어가면

- **Record·Tuple 같은 「값으로 비교되는 복합 값」** — 제안 단계의 이야기다. 이 문서는 다루지 않는다.
- **`NaN` 의 비트 패턴** — `NaN` 은 여러 비트 패턴이 있다. `defineProperty` 의 NOTE 가 그 사실을 언급한다. 이 문서는 비트를 찍지 않았다(`0/0` 과 리터럴 `NaN` 이 재정의에서 같다는 것만 봤다).
