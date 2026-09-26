# js/syntax/34 — 타입 검사 관용구: 「`instanceof` 는 족보를, 브랜드 검사는 출생 기록을 본다 — realm 을 넘으면 족보가 끊긴다」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> ★★★ **이 편은 「이미 곳곳에서 조각으로 잰 것을 한데 모으는 정본」 편이다.** 판정 방법 하나하나는 앞 편들이 이미 쟀다 —
> [15번](../15-prototype-chain/2-summary.md) **`instanceof` 가 사슬을 탄다 · `Symbol.hasInstance`** ·
> [16번](../16-class-syntax/2-summary.md) ★ **`Object.create(Account.prototype)` 은 `instanceof` 가 참인데 `#balance in` 은 거짓**(브랜드 검사) ·
> [17번](../17-inheritance-and-super/2-summary.md) **`Array.call(this)` 로 만든 객체는 브랜드 `[object Object]` 인데 `instanceof Array` 가 참** ·
> [22번](../22-symbol-and-well-known-symbols/2-summary.md) ★ **`Symbol.toStringTag` 로 브랜드를 위조한다(`7 / 7`)** · [01번](../01-value-types-and-typeof/2-summary.md) **`typeof`**.
> ★★★ **다시 재지 않는다.** 새로 잰 빈 칸은 **realm** 하나다 — **다른 realm(node `vm` · Chrome iframe)에서 만든 값**에 같은 판정들을 던졌다.
>
> ★★★ **이 주제의 본체는 ② 전수 격자다** — **내장 타입 5 × 조건 5 × 판정 방법 5**. 조건은 **같은 realm · 다른 realm · 프로토타입 교체 · `Object.create(proto)` · `toStringTag` 위조**,
> 칸마다 그 방법의 답이 **「진짜인가」와 맞는지**를 찍고 **어긋난 칸을 스크립트가 센다**(동작 (1)).
> ★★ **③ 브랜드 태그는 이 격자의 한 열**이다 — 22번의 위조를 **조건 한 행**으로 넣어 다른 방법들과 나란히 채점한다.
> ★★ **같은 격자를 두 창에서** 돌렸다 — **node 의 `vm.runInNewContext`** 와 **Chrome 151 의 같은 출처 iframe**. 둘이 같은 답을 냈나가 이 편의 둘째 질문이다.
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262](https://tc39.es/ecma262/) — `InstanceofOperator` · `OrdinaryHasInstance` · `IsArray` · `Object.prototype.toString` · `Error.isError` · `Date.prototype.getTime`(`thisTimeValue`) · `RegExpBuiltinExec` · `Promise.prototype.then`(`IsPromise`)
> - 명세 문장은 이 배치가 받아 둔 **ES2026 판 HTML** 에서 읽었다(연산 이름과 짧은 인용만 싣는다).
> - `vm.runInNewContext`(node)·iframe(웹)은 **호스트 API** 다 — 명세의 realm 을 **어떻게** 만드는지는 이 문서가 확인하지 않았다(22번과 같은 단서).
>
> **실행 검증** — 이 문서의 새 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다.
> 배너의 `node20` 은 `~/.nvm/versions/node/v20.19.6/bin/node`, `node18` 은 기본 PATH 의 `node`(v18.19.1)다.
> ★★★ **격자 코드는 한 파일**(`js32b-34-h-realm-core.js`)이고, node 판과 Chrome 판은 **다른 realm 을 만드는 법**과 **오류 슬롯 검사 함수**만 넘겨준다.
> ★★ **`Error.isError`(ES2026)는 두 node 판에 없다** — node 판의 오류 슬롯 열은 **호스트 함수 `util.types.isNativeError`** 로 물었다(제5의 상태 — 창을 바꿔 물었다). Chrome 판은 `Error.isError` 다.
> ★★ **이 주제에서 두 node 판이 갈린 탐침은 없다**(대조기 — 이 배치 전체 `identical 12`).
>
> **버전**
>
> | 무엇 | 판 | 이 머신에서 |
> |---|---|---|
> | `instanceof` · `typeof` · `Object.prototype.toString` | ES1\~ES3 | 세 판 다 있다 |
> | `Array.isArray` | ES5 | 세 판 다 있다 |
> | `Symbol.hasInstance` · `Symbol.toStringTag` · `Proxy` | ES2015 | 세 판 다 있다 |
> | `#x in o`(프라이빗 브랜드 검사) | ES2022 | 세 판 다 있다 |
> | `Error.isError` | **ES2026** | ★ **두 node 판에 없다** — Chrome 151 로만 |
>
> **★★★ 이 주제가 쓰는 창 — 그리고 부적용인 창**
>
> | 창 | 이 주제에서 무엇을 보나 |
> |---|---|
> | ★★★ **② 전수 격자**(본체) | 타입 5 × 조건 5 × 방법 5 — **어긋난 칸 N / M** 을 방법별 · 조건별 · 전체로 스크립트가 센다(동작 (1)) |
> | ★★★ **③ 브랜드 태그** | 격자의 한 열(`toString tag`) + 22번의 위조를 **조건 한 행**으로(동작 (1)) |
> | ★★ **창을 바꿔 물었다**(제5의 상태) | node 에는 `Error.isError` 가 없어 **`util.types.isNativeError`(호스트)** 로 같은 질문을 물었다 — 그 열만 node 와 Chrome 의 **함수가 다르다** |
> | ★ **④ 예외의 `constructor.name` + `message`** | **보조** — 「슬롯을 두드리는 메서드」 열이 **던지나 안 던지나**로 답한다(문구는 싣지 않았다) |
> | ★ **① 추상 연산에 로그 심기** | **부적용** — 이 편의 판정은 사용자 코드를 안 부른다(`Symbol.hasInstance` 로 끼어드는 것은 15번이 쟀다) |
> | ★ **부적용 — 두 번 컴파일** | 판정 결과가 모드를 안 탄다 |
> | ★ **안 쟀다 — 성능** | 「`instanceof` 가 빠르다」 같은 문장을 쓰지 않는다 |
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 오류 슬롯 열이 **어느 함수인가**(node 는 호스트 함수, Chrome 은 ES2026 함수) — 판과 호스트의 사정 | ★★★ 격자의 **`y`/`n`/`*`** 과 「어긋난 칸 N / M」(방법별 · 조건별 · 전체) |
> | `Proxy` 행(동작 (2)) — **채점하지 않았다.** 「프록시가 진짜인가」에 답이 하나가 아니다 | ★★ **node `vm` 과 Chrome iframe 의 격자가 칸 글자까지 같았다**(둘째 줄 — 오류 슬롯 열에 쓴 함수의 이름 — 만 다르다) · 재대조 동일 |
>
> **선행** — [15 — 프로토타입 체인](../15-prototype-chain/2-summary.md)(직접 선행 — ★★★ **`instanceof` 는 사슬에 `C.prototype` 이 있나**만 본다 · `Symbol.hasInstance` 로 답을 바꾼다 · 우변이 틀리면 `TypeError` 둘) ·
> [16 — `class` 문법](../16-class-syntax/2-summary.md)(★★★ **`#x in o` 브랜드 검사** — 이 편의 다섯째 방법의 사용자 클래스 판) ·
> [17 — 상속과 `super`](../17-inheritance-and-super/2-summary.md)(★★ **내장 상속의 판정 창이 브랜드 태그**다) ·
> [22 — `Symbol` 과 잘 알려진 심볼](../22-symbol-and-well-known-symbols/2-summary.md)(★★★ **위조와 은폐 `7 / 7`** · `vm` 의 새 realm 에서 `Symbol.for` 를 물은 것) ·
> [01 — 값의 종류와 `typeof`](../01-value-types-and-typeof/2-summary.md)(`typeof null` 이 `"object"` · 배열도 `"object"`).
> **같은 배치** — [32 — 오류 처리와 `Error`](../32-error-handling-and-error/2-summary.md)(★★ **`Error.isError` 가 다른 realm 의 오류를 `true`, 프록시를 `false` 로** 본 것) · [33 — 동등성 세 종류](../33-equality-three-kinds/2-summary.md) · [35 — 엄격 모드](../35-strict-mode/2-summary.md).
>
> ★★ **경계 — `instanceof` 가 사슬을 어떻게 걷나**는 15번이 정본이다. 여기서는 **realm·조작 앞에서 몇 칸이 틀리나**만 센다.
> ★★ **경계 — `Proxy` 자체**는 [목록의 **45번 주제**](../45-proxy/)의 몫이다. 여기서는 **판정 다섯이 프록시를 어떻게 보나**(채점 없음)까지다.

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

**「이 사람이 우리 가문 사람인가」를 묻는 방법은 여럿이다 — 그리고 방법마다 속는 자리가 다르다.**

- ★★★ **족보 확인(`instanceof`)** — 「이 사람의 조상 목록에 **우리 가문 시조**가 있나」. **다른 나라(realm)에 있는 같은 이름 가문**의 자손은 조상 목록에 **그 나라의 시조**가 있어서 「**아니다**」가 나온다. 족보를 **위조**(`Object.create(proto)`)하면 속는다.
- ★★★ **출생 기록 확인(`Array.isArray`·`Error.isError`·슬롯을 두드리는 메서드)** — 「**그 가문의 산부인과에서 태어났나**」. 나라를 안 가리고, 족보를 고쳐도 안 속는다.
- ★★ **명찰 확인(`Object.prototype.toString`)** — 대부분 출생 기록에서 명찰을 만들지만, **본인이 명찰을 직접 달면(`Symbol.toStringTag`) 그것을 믿는다.** `Promise` 는 출생 기록이 명찰 목록에 아예 없어 **가문의 공용 명찰**을 빌려 단다.
- ★★ **행동 확인(덕 타이핑)** — 「우리 가문처럼 **행동하나**」. 나라는 안 가리지만 **족보를 지우면(프로토타입 교체) 행동도 같이 사라지고**, 족보를 위조하면 **행동도 따라온다.**

```text
                       같은 realm   다른 realm   proto 교체   Object.create   toStringTag 위조
                       (진짜)       (진짜)       (진짜)       (가짜)          (가짜)
   instanceof           맞다         ✗ 아니다     ✗ 아니다     ✗ 맞다          아니다
   isArray / isError    맞다         맞다         맞다         아니다          아니다
   toString 태그        맞다         맞다         (Promise ✗)  (Promise ✗)     ✗ 맞다
   덕 타이핑            맞다         맞다         ✗ 아니다     ✗ 맞다          아니다
   슬롯 두드리기        맞다         맞다         맞다         아니다          아니다

   ✗ = 진실과 어긋난 칸.  출생 기록(isArray/isError · 슬롯)만 한 칸도 안 틀린다 — 동작 (1)이 이것을 센다
```

**비유 대응표**

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 족보의 시조 | `C.prototype` — `OrdinaryHasInstance` 가 사슬에서 이것을 찾는다 | `instanceof` 열 |
| 다른 나라 | **다른 realm** — 전역 객체와 내장 객체 한 벌. `Array.prototype` 도 realm 마다 따로다 | `other realm` 행 |
| 출생 기록 | **내부 슬롯**(`[[ErrorData]]`·`[[DateValue]]`·`[[RegExpMatcher]]`·`[[PromiseState]]`) · 배열 이국 객체(Array exotic) | `isArray/isError`·`slot via method` 열 |
| 명찰 | `Object.prototype.toString` 의 `[object X]` — 슬롯에서 만든 `builtinTag` 를 **`Symbol.toStringTag` 가 덮는다** | `toString tag` 열 · 22번 |
| 행동 | 덕 타이핑 — `typeof v.then === "function"` 같은 모양 검사 | `duck typing` 열 |
| 족보 위조 | `Object.create(X.prototype)` — 슬롯 없이 사슬만 있다 | `Object.create(proto)` 행 |

**똑같은 구조다** — 실무에서 물리는 자리.
「**iframe 에서 받은 배열을 `instanceof Array` 로 검사했더니 `false` 여서 입력 검증이 거절했다**」와
「**라이브러리가 넘겨준 프로미스를 `instanceof Promise` 로 걸렀더니 다른 구현(realm)의 프로미스가 빠졌다**」가 같은 칸(`other realm` × `instanceof`)이다(동작 (1)).

> **realm** — 전역 객체와 내장 객체(`Array`·`Error`·`Object.prototype` …) 한 벌. iframe 하나, node `vm` 컨텍스트 하나가 각자 갖는다.\
> 예: iframe 의 `Array` 와 바깥의 `Array` 는 **다른 함수**다 — `W.Array === Array` 가 `false`.

> **내부 슬롯(internal slot)** — 명세가 객체에 붙이는 **보이지 않는 칸**. 그 생성자가 만들 때만 생긴다.\
> 예: `new Date(0)` 에는 `[[DateValue]]` 가 있고 `Object.create(Date.prototype)` 에는 없다.

## 이 주제가 답하려는 질문

1. **판정 다섯(`instanceof` · `Array.isArray`/`Error.isError` · `Object.prototype.toString` · 덕 타이핑 · 슬롯 두드리기)은 각각 무엇을 보나** — 그래서 **realm · 프로토타입 조작 · 위조** 앞에서 **몇 칸이 틀리나**?
2. **다른 realm 을 만드는 두 창(node `vm` · Chrome iframe)은 같은 답을 내나?**
3. **「무엇을 묻고 싶은가」마다 어느 판정을 골라야 하나?**

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 출력으로 읽는다.

### (1) ★★★ 타입 5 × 조건 5 × 방법 5 — 이 주제의 본체

**언제 쓰나** — 함수 인자·메시지·라이브러리 반환값의 **종류를 판정하는 코드**를 짤 때. 특히 그 값이 **다른 전역(iframe·워커·`vm`)** 에서 올 수 있을 때.
★★★ 「진짜」 = **그 타입의 생성자가 만든 것**(내부 슬롯이 있다). 어느 realm 에서 만들었는지는 묻지 않는다.
**`-`** 는 그 타입에 그 방법이 없다는 뜻이다 — `Array.isArray`·`Error.isError` 는 배열·오류에만 있고, 「슬롯을 두드리는 메서드」(`Date.prototype.getTime.call(v)` 가 던지나)는 **배열·오류에는 대응하는 것이 따로 없다**(위 두 함수가 그 몫이다).

```js
// js32b-34-h-realm-core.js
// 타입 검사 다섯 방법 x 진짜/가짜 다섯 조건 x 내장 타입 다섯 -- 칸마다 그 방법의 답이 「진짜인가」와 맞나.
// 「진짜」 = 그 타입의 생성자가 만든 것(내부 슬롯이 있다). 어느 realm 에서 만들었는지는 묻지 않는다.
// node(vm) 와 Chrome(iframe) 이 이 파일을 같이 쓴다 -- 다른 realm 을 만드는 법과 오류 슬롯 검사만 넘겨받는다.
globalThis.realmGrid = function realmGrid(otherEval, errorSlot, errorSlotName) {
  const tagOf = (v) => Object.prototype.toString.call(v);
  const noThrow = (f) => { try { f(); return true; } catch (e) { return false; } };
  const TYPES = [
    { name: "Array", C: Array, src: "[1, 2]",
      isX: (v) => Array.isArray(v),
      duck: (v) => typeof v.length === "number" && typeof v.push === "function",
      brand: null },
    { name: "Error", C: Error, src: "new Error('x')",
      isX: errorSlot,
      duck: (v) => typeof v.message === "string" && typeof v.name === "string",
      brand: null },
    { name: "Date", C: Date, src: "new Date(0)",
      isX: null,
      duck: (v) => typeof v.getTime === "function",
      brand: (v) => noThrow(() => Date.prototype.getTime.call(v)) },
    { name: "RegExp", C: RegExp, src: "/a/",
      isX: null,
      duck: (v) => typeof v.exec === "function",
      brand: (v) => noThrow(() => RegExp.prototype.exec.call(v, "")) },
    { name: "Promise", C: Promise, src: "Promise.resolve(1)",
      isX: null,
      duck: (v) => typeof v.then === "function",
      brand: (v) => noThrow(() => Promise.prototype.then.call(v, undefined, () => {})) },
  ];
  const CONDS = [
    ["same realm", true, (T) => (0, eval)(T.src)],
    ["other realm", true, (T) => otherEval(T.src)],
    ["proto swapped", true, (T) => Object.setPrototypeOf((0, eval)(T.src), Object.prototype)],
    ["Object.create(proto)", false, (T) => Object.create(T.C.prototype)],
    ["toStringTag forged", false, (T) => ({ [Symbol.toStringTag]: T.name })],
  ];
  const METHODS = [
    ["instanceof", (T, v) => v instanceof T.C],
    ["isArray/isError", (T, v) => (T.isX ? T.isX(v) : null)],
    ["toString tag", (T, v) => tagOf(v) === "[object " + T.name + "]"],
    ["duck typing", (T, v) => T.duck(v)],
    ["slot via method", (T, v) => (T.brand ? T.brand(v) : null)],
  ];
  console.log("[1] y/n = the method's answer to 'is this a genuine <type>?'   * = differs from the truth   - = no such method");
  console.log("    isArray/isError column for Error uses: " + errorSlotName);
  console.log("  " + "type".padEnd(9) + "condition".padEnd(22) + "truth".padEnd(7) + METHODS.map(([n]) => n.padEnd(17)).join("").trimEnd());
  const off = METHODS.map(() => 0), asked = METHODS.map(() => 0);
  const offByCond = CONDS.map(() => 0);
  for (const T of TYPES) {
    CONDS.forEach(([cname, truth, make], ci) => {
      const v = make(T);
      const cells = METHODS.map(([, m], mi) => {
        const a = m(T, v);
        if (a === null) return "-";
        asked[mi] += 1;
        if (a !== truth) { off[mi] += 1; offByCond[ci] += 1; return (a ? "y" : "n") + "*"; }
        return a ? "y" : "n";
      });
      console.log(("  " + T.name.padEnd(9) + cname.padEnd(22) + (truth ? "y" : "n").padEnd(7) + cells.map((c) => c.padEnd(17)).join("")).trimEnd());
    });
  }
  console.log("");
  console.log("  per method (cells that differ from the truth / cells asked):");
  METHODS.forEach(([n], i) => console.log("    " + n.padEnd(18) + off[i] + " / " + asked[i]));
  console.log("  per condition:");
  CONDS.forEach(([n], i) => console.log("    " + n.padEnd(22) + offByCond[i] + " / " + asked.reduce((a, b) => a + b, 0) / CONDS.length));
  console.log("cells that differ from the truth: " + off.reduce((a, b) => a + b, 0) + " / " + asked.reduce((a, b) => a + b, 0));
  console.log("");
  console.log("[2] not graded -- a Proxy with no traps around a genuine value (is a Proxy 'genuine'? the question has no single answer)");
  for (const T of TYPES) {
    const p = new Proxy((0, eval)(T.src), {});
    const cells = METHODS.map(([, m]) => { const a = m(T, p); return a === null ? "-" : a ? "y" : "n"; });
    console.log(("  " + T.name.padEnd(9) + "new Proxy(v, {})".padEnd(29) + cells.map((c) => c.padEnd(17)).join("")).trimEnd());
  }
};
```

```js
// js32b-34a-realm-grid.js
// 다른 realm = node:vm 의 새 컨텍스트. 오류 슬롯 검사는 Error.isError 가 없는 판이라 호스트 함수로 대신 묻는다.
const vm = require("node:vm");
const util = require("node:util");
require("./js32b-34-h-realm-core.js");
realmGrid((src) => vm.runInNewContext(src), (v) => util.types.isNativeError(v), "util.types.isNativeError (node host API)");
```

```text
===== node20 js32b-34a-realm-grid.js (exit=0) =====
[1] y/n = the method's answer to 'is this a genuine <type>?'   * = differs from the truth   - = no such method
    isArray/isError column for Error uses: util.types.isNativeError (node host API)
  type     condition             truth  instanceof       isArray/isError  toString tag     duck typing      slot via method
  Array    same realm            y      y                y                y                y                -
  Array    other realm           y      n*               y                y                y                -
  Array    proto swapped         y      n*               y                y                n*               -
  Array    Object.create(proto)  n      y*               n                n                y*               -
  Array    toStringTag forged    n      n                n                y*               n                -
  Error    same realm            y      y                y                y                y                -
  Error    other realm           y      n*               y                y                y                -
  Error    proto swapped         y      n*               y                y                n*               -
  Error    Object.create(proto)  n      y*               n                n                y*               -
  Error    toStringTag forged    n      n                n                y*               n                -
  Date     same realm            y      y                -                y                y                y
  Date     other realm           y      n*               -                y                y                y
  Date     proto swapped         y      n*               -                y                n*               y
  Date     Object.create(proto)  n      y*               -                n                y*               n
  Date     toStringTag forged    n      n                -                y*               n                n
  RegExp   same realm            y      y                -                y                y                y
  RegExp   other realm           y      n*               -                y                y                y
  RegExp   proto swapped         y      n*               -                y                n*               y
  RegExp   Object.create(proto)  n      y*               -                n                y*               n
  RegExp   toStringTag forged    n      n                -                y*               n                n
  Promise  same realm            y      y                -                y                y                y
  Promise  other realm           y      n*               -                y                y                y
  Promise  proto swapped         y      n*               -                n*               n*               y
  Promise  Object.create(proto)  n      y*               -                y*               y*               n
  Promise  toStringTag forged    n      n                -                y*               n                n

  per method (cells that differ from the truth / cells asked):
    instanceof        15 / 25
    isArray/isError   0 / 10
    toString tag      7 / 25
    duck typing       10 / 25
    slot via method   0 / 15
  per condition:
    same realm            0 / 20
    other realm           5 / 20
    proto swapped         11 / 20
    Object.create(proto)  11 / 20
    toStringTag forged    5 / 20
cells that differ from the truth: 32 / 100

[2] not graded -- a Proxy with no traps around a genuine value (is a Proxy 'genuine'? the question has no single answer)
  Array    new Proxy(v, {})             y                y                y                y                -
  Error    new Proxy(v, {})             y                n                n                y                -
  Date     new Proxy(v, {})             y                -                n                y                n
  RegExp   new Proxy(v, {})             y                -                n                y                n
  Promise  new Proxy(v, {})             y                -                y                y                n
```

```text
   같은 질문 「이것이 진짜 X 인가」 -- 방법마다 무엇을 보나

   instanceof X            v 의 [[Prototype]] 사슬에 「이 realm 의」 X.prototype 이 있나      ← 사슬 (고칠 수 있다)
   Array.isArray(v)        v 가 배열 이국 객체인가 (Proxy 면 대상을 본다)                   ← 출생
   Error.isError(v)        v 에 [[ErrorData]] 가 있나                                     ← 출생
   X.prototype.m.call(v)   메서드가 슬롯을 요구한다 -- 없으면 TypeError                     ← 출생
   toString                슬롯으로 builtinTag 를 정한 뒤 v[Symbol.toStringTag] 가 문자열이면 그것  ← 출생 + 자칭
                           (builtinTag 목록에 Promise · Map · Set 은 없다 -- 그들은 프로토타입의 자칭뿐)
   덕 타이핑                v.then · v.push … 가 함수인가                                  ← 사슬 (행동은 사슬에 산다)
```

- ★★★ **집계 줄 — `cells that differ from the truth: 32 / 100`.** 방법별로 **`instanceof` `15 / 25` · 덕 타이핑 `10 / 25` · `toString` 태그 `7 / 25` · `isArray/isError` `0 / 10` · 슬롯 두드리기 `0 / 15`**.
  ★★★ **출생 기록을 보는 두 열만 한 칸도 안 틀렸다.** 사슬을 보는 두 열(`instanceof`·덕 타이핑)이 틀린 칸의 대부분이다.
- ★★★ **`instanceof` 는 다른 realm 에서 다섯 타입 모두 `n*`** 다 — 그쪽 값의 사슬에는 **그쪽 realm 의 `X.prototype`** 이 있고, 이쪽의 `X.prototype` 은 **다른 객체**다. 명세 `OrdinaryHasInstance` 가 사슬의 객체를 **`SameValue`** 로 견준다(33번 동작 (1)의 마지막 불릿).
  **프로토타입 교체에서도 다섯 모두 `n*`**, **`Object.create(proto)` 에서는 다섯 모두 `y*`** — 사슬만 보므로 **사슬을 고치면 답이 따라간다.** 셋 × 다섯 = **15칸**.
- ★★★ **`toString` 태그는 위조 다섯 칸에서 전부 `y*`** — 22번의 `7 / 7` 과 같은 성질이다. **그리고 `Promise` 만 두 칸 더 틀린다** — 교체하면 `n*`, `Object.create` 면 `y*`.
  명세 `Object.prototype.toString` 의 `builtinTag` 목록(`Array`·`Arguments`·`Function`·`Error`·`Boolean`·`Number`·`String`·`Date`·`RegExp`)에 **`Promise` 가 없다** — `Promise` 의 명찰은 **`Promise.prototype[Symbol.toStringTag]`** 뿐이라 **사슬을 따라다닌다.**
- ★★ **덕 타이핑은 다른 realm 에서 안 틀린다**(메서드가 그쪽 사슬에 다 있다). 대신 **교체 다섯 칸은 `n*`**(행동이 사슬과 함께 사라졌다 — `Error` 는 `name` 이 없어졌다), **`Object.create` 다섯 칸은 `y*`**(행동이 사슬과 함께 따라왔다).
- ★★ **조건별 — `other realm` `5 / 20` · `proto swapped` `11 / 20` · `Object.create(proto)` `11 / 20` · `toStringTag forged` `5 / 20` · `same realm` `0 / 20`.** realm 하나만 넘어도 **다섯 칸**(전부 `instanceof`)이 틀린다.

### (2) ★★ 트랩 없는 `Proxy` — 채점하지 않은 행

**언제 쓰나** — 값을 `Proxy` 로 감싸 넘기는 라이브러리(반응형 상태 등)를 쓸 때.
★★ **채점하지 않는다** — 「프록시가 진짜 배열인가」에는 답이 하나가 아니다(`Date.prototype.getTime` 은 프록시에서 던진다 — 쓸 수 없는 `Date` 다).

동작 (1)의 블록 `[2]` 가 이것이다.

- ★★★ **`Array.isArray` 는 프록시를 뚫는다**(`y`) — 명세 `IsArray` 가 「**Proxy 면 대상을 다시 `IsArray`**」다. **`Error.isError`(Chrome)·`isNativeError`(node) 는 못 뚫는다**(`n`) — 슬롯이 **대상에** 있기 때문이다. **이름이 닮은 두 함수가 여기서 갈린다**(32번 동작 (7)).
- ★★ **`instanceof` 는 다섯 모두 `y`** — 프록시의 `getPrototypeOf` 가 대상의 사슬을 그대로 돌려준다.
- ★★ **`toString` 은 `Array` 와 `Promise` 만 `y`** — 배열은 `IsArray` 가 뚫어서, `Promise` 는 **자칭 명찰이 사슬에 있어서**다. `Error`·`Date`·`RegExp` 는 `n`(슬롯이 프록시에 없다).
- ★★ **슬롯 두드리기는 셋 다 `n`** — `Date.prototype.getTime.call(proxy)` 는 던진다. 16번의 「`#private` 가 있는 인스턴스를 `Proxy` 로 감싸면 메서드가 던진다」와 **같은 이유**다.

### (3) ★★★ node `vm` 과 Chrome iframe — 두 창이 같은 답을 냈나

**언제 쓰나** — 「node 에서 잰 realm 결과를 브라우저에 옮겨도 되나」를 물을 때.

```text
   realm 둘 = 내장 객체가 두 벌

   이쪽 realm                                   다른 realm (vm 컨텍스트 · iframe)
   ┌──────────────────────────┐                 ┌──────────────────────────┐
   │ Array ─ prototype ─▶ AP1 │                 │ Array ─ prototype ─▶ AP2 │
   │ Error ─ prototype ─▶ EP1 │                 │ Error ─ prototype ─▶ EP2 │
   └──────────────────────────┘                 └──────────────────────────┘
                                                  v = [1, 2]   v 의 사슬:  AP2 ─▶ OP2 ─▶ null

   v instanceof Array   → 사슬에서 AP1 을 찾는다 → 없다 → false        (AP1 ≠ AP2)
   Array.isArray(v)     → v 가 배열 이국 객체인가 → 그렇다 → true       (realm 을 안 본다)
   v.push 가 함수인가    → AP2 에 push 가 있다 → true                    (덕 타이핑도 넘는다)
```

```js
// js32b-34b-realm-grid.web.js
// 같은 격자를 Chrome 에서 -- 다른 realm = 같은 출처의 iframe. 오류 슬롯 검사는 Error.isError(ES2026).
const frame = document.createElement("iframe");
document.body.appendChild(frame);
realmGrid((src) => frame.contentWindow.eval(src), (v) => Error.isError(v), "Error.isError (ES2026)");
```

```text
===== google-chrome --headless --virtual-time-budget=2000 --dump-dom 'js32b-page.html?js32b-34-h-realm-core.js,js32b-34b-realm-grid.web.js' | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' | sed 's/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&amp;/\&/g' (exit=0) =====
[1] y/n = the method's answer to 'is this a genuine <type>?'   * = differs from the truth   - = no such method
    isArray/isError column for Error uses: Error.isError (ES2026)
  type     condition             truth  instanceof       isArray/isError  toString tag     duck typing      slot via method
  Array    same realm            y      y                y                y                y                -
  Array    other realm           y      n*               y                y                y                -
  Array    proto swapped         y      n*               y                y                n*               -
  Array    Object.create(proto)  n      y*               n                n                y*               -
  Array    toStringTag forged    n      n                n                y*               n                -
  Error    same realm            y      y                y                y                y                -
  Error    other realm           y      n*               y                y                y                -
  Error    proto swapped         y      n*               y                y                n*               -
  Error    Object.create(proto)  n      y*               n                n                y*               -
  Error    toStringTag forged    n      n                n                y*               n                -
  Date     same realm            y      y                -                y                y                y
  Date     other realm           y      n*               -                y                y                y
  Date     proto swapped         y      n*               -                y                n*               y
  Date     Object.create(proto)  n      y*               -                n                y*               n
  Date     toStringTag forged    n      n                -                y*               n                n
  RegExp   same realm            y      y                -                y                y                y
  RegExp   other realm           y      n*               -                y                y                y
  RegExp   proto swapped         y      n*               -                y                n*               y
  RegExp   Object.create(proto)  n      y*               -                n                y*               n
  RegExp   toStringTag forged    n      n                -                y*               n                n
  Promise  same realm            y      y                -                y                y                y
  Promise  other realm           y      n*               -                y                y                y
  Promise  proto swapped         y      n*               -                n*               n*               y
  Promise  Object.create(proto)  n      y*               -                y*               y*               n
  Promise  toStringTag forged    n      n                -                y*               n                n

  per method (cells that differ from the truth / cells asked):
    instanceof        15 / 25
    isArray/isError   0 / 10
    toString tag      7 / 25
    duck typing       10 / 25
    slot via method   0 / 15
  per condition:
    same realm            0 / 20
    other realm           5 / 20
    proto swapped         11 / 20
    Object.create(proto)  11 / 20
    toStringTag forged    5 / 20
cells that differ from the truth: 32 / 100

[2] not graded -- a Proxy with no traps around a genuine value (is a Proxy 'genuine'? the question has no single answer)
  Array    new Proxy(v, {})             y                y                y                y                -
  Error    new Proxy(v, {})             y                n                n                y                -
  Date     new Proxy(v, {})             y                -                n                y                n
  RegExp   new Proxy(v, {})             y                -                n                y                n
  Promise  new Proxy(v, {})             y                -                y                y                n
```

- ★★★ **칸 글자까지 같다** — `32 / 100` · 방법별 · 조건별 · `[2]` 의 프록시 행까지 전부. **다른 것은 둘째 줄(오류 슬롯 열에 쓴 함수의 이름) 하나**다.
  ★★ node 판의 그 열은 **`util.types.isNativeError`(호스트)**, Chrome 판은 **`Error.isError`(ES2026)** — **함수가 달라도 그 열의 답이 같았다** — 오류 행 다섯 칸(`[1]`)과 프록시 한 칸(`[2]`).
- ★★ **「`vm` 이 명세의 realm 과 같은 것인가」는 이 문서가 확인하지 않았다** — 다만 **판정 다섯이 보는 것**(사슬의 객체 · 슬롯)에 관해서는 **두 창이 같은 결과**를 냈다. 22번이 「레지스트리 심볼은 `vm` 을 넘어도 같다」를 잰 것과 같은 결의 관찰이다.

### (4) ★★ 배열처럼 보이는 것들 — `typeof` 와 판정 셋을 한 줄에

**언제 쓰나** — `arguments`·형식화 배열·`NodeList` 류를 「배열인가」로 거를 때.

```js
// js32b-34c-array-edges.js
// 배열처럼 보이는 것들 -- typeof · Array.isArray · instanceof Array · 브랜드 태그를 한 줄에.
const row = (label, v) => console.log(("  " + label.padEnd(30) + v.map((x) => String(x).padEnd(18)).join("")).trimEnd());
function argsOf() { return arguments; }
class List extends Array {}
console.log("  " + "".padEnd(30) + "typeof".padEnd(18) + "Array.isArray".padEnd(18) + "instanceof Array".padEnd(18) + "tag");
const items = [
  ["[1, 2]", [1, 2]],
  ["new List()", new List()],
  ["Array.prototype", Array.prototype],
  ["argsOf(1, 2)", argsOf(1, 2)],
  ["new Uint8Array(2)", new Uint8Array(2)],
  ["{ length: 0 }", { length: 0 }],
  ["'ab'", "ab"],
];
for (const [label, v] of items) {
  row(label, [typeof v, Array.isArray(v), v instanceof Array, Object.prototype.toString.call(v)]);
}
```

```text
===== node20 js32b-34c-array-edges.js (exit=0) =====
                                typeof            Array.isArray     instanceof Array  tag
  [1, 2]                        object            true              true              [object Array]
  new List()                    object            true              true              [object Array]
  Array.prototype               object            true              false             [object Array]
  argsOf(1, 2)                  object            false             false             [object Arguments]
  new Uint8Array(2)             object            false             false             [object Uint8Array]
  { length: 0 }                 object            false             false             [object Object]
  'ab'                          string            false             false             [object String]
```

- ★★★ **`Array.prototype` 은 배열이다** — `Array.isArray` `true`, 브랜드 `[object Array]`, 그런데 **`instanceof Array` 는 `false`**(자기 자신이 사슬에 없다). 명세가 `Array.prototype` 을 **배열 이국 객체**로 만든다.
- ★★ **`arguments` 는 `[object Arguments]`**(08번) · **`Uint8Array` 는 배열이 아니다**(`false` · `[object Uint8Array]`) · `{ length: 0 }` 은 셋 다 아니다.
- ★★ **`typeof` 는 여섯 객체 모두 `"object"`** — 배열을 못 가른다(01번 어디서 틀리나 (6)). 문자열만 `"string"`.
- ★ **`class List extends Array` 는 세 판정 모두 `true`** — 파생 클래스는 **`super()` 에서 `Array` 가 집을 짓는다**(17번 동작 (2)). 옛 방식 `Array.call(this)` 는 `instanceof` 만 `true` 였다(17번 동작 (5)).

## 문법 — 형태와 규칙

★ 이 절은 **판정 선택표**다 — 모든 동작 주장은 위 동작 절의 캡처 블록과 인용한 편의 블록에서만 한다.

| 묻고 싶은 것 | 쓸 것 | realm 을 넘나 | 조작에 속나 | 어디서 봤나 |
|---|---|---|---|---|
| 배열인가 | `Array.isArray(v)` | 넘는다 | 안 속는다(프록시는 대상을 본다) | 동작 (1)·(2)·(4) |
| 오류인가 | `Error.isError(v)` — ES2026 | 넘는다 | 안 속는다(프록시는 `false`) | 동작 (1)·(2) · 32번 |
| `Date`·`RegExp`·`Promise`·`Map` 인가 | 그 타입의 메서드를 `call` 해 던지나 | 넘는다 | 안 속는다 | 동작 (1) · 22번 |
| **내 클래스**가 만들었나 | `#brand in v`(ES2022) | — | 안 속는다 | [16번](../16-class-syntax/2-summary.md) 동작 (5) |
| 이 realm 의 이 클래스 계층인가 | `v instanceof C` | **안 넘는다** | 속는다(사슬을 고치면) | 동작 (1) · 15번 |
| 원시값의 종류 | `typeof v` — `null` 은 따로 | — | — | 01번 |
| 이 동작을 할 수 있나 | 덕 타이핑 | 넘는다 | 속는다 | 동작 (1) |
| 스스로 무엇이라고 부르나(표시용) | `Object.prototype.toString.call(v)` | 넘는다 | **속는다**(`toStringTag`) | 동작 (1) · 22번 |

- **「진짜인가」는 출생 기록으로**, **「이 계층인가」는 `instanceof` 로**, **「할 수 있나」는 덕 타이핑으로** 묻는다 — 셋은 **다른 질문**이다.

## 어디서 틀리나

### (1) ★★★ `v instanceof Array` 로 배열을 거른다

**다른 realm 의 배열에서 `false`**(동작 (1)·(3)). `Array.isArray` 를 쓴다.

### (2) ★★★ `Object.prototype.toString.call(v) === "[object Date]"` 를 타입 판정의 정본으로 쓴다

**`Symbol.toStringTag` 하나로 위조된다**(동작 (1)의 `toStringTag forged` 다섯 칸 — 22번 `7 / 7`). 표시·로그용이다.

### (3) ★★★ `typeof v.then === "function"` 이면 진짜 프로미스라고 믿는다

**`Object.create(Promise.prototype)` 도 통과한다**(`y*`). 다만 언어 자신도 `await`·`Promise.resolve` 에서 **이 덕 타이핑(thenable)** 을 쓴다 — 「프로미스인가」와 「기다릴 수 있나」는 다른 질문이다([목록의 **37번 주제**](../37-promise-state-model/)).

### (4) ★★ `instanceof` 가 `true` 면 그 생성자가 만들었다고 믿는다

**사슬만 본다** — `Object.create(X.prototype)` 이 다섯 타입 모두 `y*`(동작 (1)) · 16번의 `Object.create(Account.prototype)` · 17번의 `Array.call(this)`.

### (5) ★★ `Object.setPrototypeOf` 로 프로토타입을 바꾼 값을 여전히 그 타입으로 다룬다

**`instanceof`·덕 타이핑은 버린다**(`n*`) — 슬롯은 남아 있어서 `Array.isArray`·슬롯 두드리기는 여전히 `y` 다.

### (6) ★★ `Array.isArray` 와 `Error.isError` 가 프록시를 똑같이 다룬다고 믿는다

**`Array.isArray` 는 뚫고, `Error.isError` 는 못 뚫는다**(동작 (2)).

### (7) ★ `Array.prototype instanceof Array` 가 `true` 일 것이라 믿는다

**`false`** 다 — 그런데 `Array.isArray(Array.prototype)` 는 `true`(동작 (4)).

## 구현 세부사항 대 언어 보장

### 명세 보장 — 어느 엔진에서도 같아야 하는 것

- ★★★ `OrdinaryHasInstance` — 사슬의 각 객체를 `C.prototype` 과 **`SameValue`** 로 견준다. realm 마다 `C.prototype` 이 다른 객체이므로 **realm 을 넘으면 `false`**.
- ★★★ `IsArray` — 배열 이국 객체면 `true`, **`Proxy` 면 대상으로 재귀**. `Error.isError` — **`[[ErrorData]]` 슬롯**만 본다(프록시에는 없다).
- ★★★ `Object.prototype.toString` — `builtinTag` 를 **슬롯으로** 정하고(`Promise`·`Map`·`Set` 은 목록에 없다), **`Symbol.toStringTag` 가 문자열이면 그것으로 덮는다.**
- ★★ `Date.prototype.getTime` · `RegExp.prototype.exec` · `Promise.prototype.then` 이 **슬롯이 없는 `this` 에 `TypeError`** 를 던지는 것.
- ★ `Array.prototype` 이 배열 이국 객체인 것.

### 엔진(V8) 구현 · 이 판의 관찰

- 슬롯 두드리기가 던지는 **문구** — 이 편은 싣지 않았다(던지나만 봤다).
- 이 주제 node 탐침이 두 판에서 **한 글자도 같았다**는 것 — 관찰이다.

### 호스트가 정하는 것 — ECMA-262 밖

- ★★★ **다른 realm 을 만드는 법** — `vm.runInNewContext`(node) · iframe(웹). **두 창의 격자가 같았다** — 관찰이다.
- ★★ **`util.types.isNativeError`** — node 의 함수다. `Error.isError` 가 없는 판에서 **같은 질문을 대신 물은** 창이다.

### 그래서 이렇게 적으면 틀린다

- ✗ 「`instanceof` 는 타입 검사다」 → ○ 「**사슬 검사**다 — 같은 realm·안 고친 사슬에서만 타입 검사처럼 보인다(`15 / 25`)」
- ✗ 「`Object.prototype.toString` 은 내부 `[[Class]]` 를 읽어 속일 수 없다」 → ○ 「**`[[Class]]` 는 ES2015 에서 없어졌고**, 지금은 슬롯 태그를 **`Symbol.toStringTag` 가 덮는다**」
- ✗ 「`Array.isArray` 와 `Error.isError` 는 같은 규칙이다」 → ○ 「**프록시에서 갈린다**」
- ✗ 「`instanceof` 가 `Array.isArray` 보다 빠르다」 → ○ **안 쟀다**

## 언제 쓰고 언제 안 쓰나

- **`Array.isArray`** — 배열 판정의 기본. realm·프록시 모두 넘는다.
- **`Error.isError`** — ES2026 이 되는 런타임에서 오류 판정. 안 되면 **오류를 넘기는 쪽과 판정 규약을 정한다**(이 편은 폴리필을 재지 않았다).
- **슬롯 두드리기** — `Date`·`RegExp`·`Map` 등을 **엄밀히** 가를 때. 대신 **호출이 부작용을 가질 수 있다**(`then.call` 은 새 프로미스를 만든다).
- **`#brand in v`** — **내 클래스의 인스턴스**를 가를 때(16번).
- **`instanceof`** — **한 realm 안의 내 클래스 계층**에서 분기할 때.
- **덕 타이핑** — 「이 동작을 할 수 있나」가 진짜 질문일 때(이터러블·thenable).
- ★ **안 쓰는 자리** — `toString` 태그로 **보안·입력 검증**을 하는 것.

## 핵심 문장

1. ★★★ 타입 5 × 조건 5 × 방법 5 격자에서 **`32 / 100`** 칸이 진실과 어긋났다 — **`instanceof` `15 / 25` · 덕 타이핑 `10 / 25` · `toString` `7 / 25` · `isArray/isError` `0 / 10` · 슬롯 두드리기 `0 / 15`**.
2. ★★★ **출생 기록**(슬롯·배열 이국 객체)을 보는 판정만 realm·교체·위조에 안 속는다. **사슬**을 보는 `instanceof`·덕 타이핑은 사슬을 고치면 따라간다.
3. ★★★ realm 을 넘으면 **`instanceof` 만 다섯 타입 모두** 틀린다(`other realm 5 / 20`) — node `vm` 과 Chrome iframe 이 **칸 글자까지 같은** 격자를 냈다.
4. ★★ `toString` 태그는 **위조에 다섯 칸 모두** 속고, **`Promise`** 는 `builtinTag` 가 없어 교체·`Object.create` 에서도 속는다.
5. ★★ `Array.isArray` 는 **프록시를 뚫고** `Error.isError` 는 **못 뚫는다** — 이름이 닮은 두 함수의 차이다.

## 관련 자료

- [ECMA-262](https://tc39.es/ecma262/) — `OrdinaryHasInstance` · `IsArray` · `Object.prototype.toString` · `Error.isError`
- [15 — 프로토타입 체인](../15-prototype-chain/2-summary.md) — ★ **경계**: 그쪽이 **`instanceof` 가 사슬을 걷는 법 · `Symbol.hasInstance`** 의 정본, 여기는 **그 판정이 realm·조작에서 몇 칸 틀리나**.
- [16 — `class` 문법](../16-class-syntax/2-summary.md) — `#x in o` 브랜드 검사의 정본(동작 (5)).
- [17 — 상속과 `super`](../17-inheritance-and-super/2-summary.md) — 내장 상속과 브랜드 태그(동작 (5)).
- [22 — `Symbol` 과 잘 알려진 심볼](../22-symbol-and-well-known-symbols/2-summary.md) — ★ **경계**: 그쪽이 **`toStringTag` 위조·은폐 `7 / 7`** 의 정본, 여기는 **그 위조를 조건 한 행으로 다른 판정과 나란히** 채점한 것.
- [32 — 오류 처리와 `Error`](../32-error-handling-and-error/2-summary.md) — `Error.isError` 한 함수의 정본(동작 (7)).
- [01 — 값의 종류와 `typeof`](../01-value-types-and-typeof/2-summary.md) — `typeof` 의 여덟 답.
- [목록의 **45번 주제**](../45-proxy/)(`Proxy`) — 프록시 자체의 정본. [목록의 **37번 주제**](../37-promise-state-model/)(Promise 상태 모델) — thenable 을 언어가 어떻게 기다리나.

## 용어 풀이

- **realm** — 전역 객체와 내장 객체 한 벌. iframe·`vm` 컨텍스트마다 따로다.
- **내부 슬롯** — 명세가 붙이는 보이지 않는 칸(`[[ErrorData]]`·`[[DateValue]]` …). 생성자가 만들 때만 생긴다.
- **배열 이국 객체(Array exotic object)** — `length` 가 인덱스와 함께 움직이는 특별한 객체. `Array.isArray` 가 이것을 본다.
- **브랜드 태그** — `Object.prototype.toString.call(v)` 의 `[object X]`. 슬롯으로 정하고 `Symbol.toStringTag` 로 덮인다.
- **브랜드 검사** — 「이 생성자가 만들었나」를 슬롯으로 묻는 것. `Array.isArray`·`Error.isError`·메서드 `call`·`#x in o`.
- **덕 타이핑** — 모양(메서드가 있나)으로 판정하는 것.
- **`OrdinaryHasInstance`** — `instanceof` 의 기본 알고리즘. 사슬에서 `C.prototype` 을 찾는다.
- **thenable** — `then` 메서드가 있는 값. 언어가 `await` 에서 덕 타이핑으로 받아들인다.

## 더 들어가면

- **`Symbol.hasInstance` 로 realm 을 넘는 `instanceof` 만들기** — 가능하지만 **15번의 도구**다. 이 편은 재지 않았다.
- **워커(Worker)·`structuredClone` 으로 건너온 값** — realm 을 넘는다기보다 **복제**다. [목록의 **48번 주제**](../48-deep-copy-methods-compared/)의 몫이다.
