# js/syntax/22 — `Symbol` 과 잘 알려진 심볼: 「심볼은 이름이 겹칠 수 없는 키이고, 잘 알려진 심볼은 언어가 먼저 들여다보는 키다」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> ★★★ **이 주제의 본체는 ① 추상 연산에 로그 심기다.**
> `Symbol.toPrimitive`·`Symbol.hasInstance`·`Symbol.species` 는 **언어가 연산 도중에 몰래 읽는 키**다.
> 연산의 결과(`8`·`true`·`Array`)만 보면 그 키가 **읽혔는지, 무슨 인자로 불렸는지** 한 글자도 안 남는다.
> 그래서 세 자리에 로그를 심고 연산자·내장 메서드를 차례로 들이댔다. **hint 가 무엇으로 오나는 오직 그 로그로만 보인다.**
> ★★ 거기에 **② 전수 격자**가 둘 붙는다 — 심볼 키 격자(18편 격자에 심볼 줄을 늘린 것)와 「브랜드 태그 대 내부 슬롯」 격자.
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262 2026 — multipage](https://tc39.es/ecma262/2026/multipage/) — 추상 연산 `ToPrimitive` · `OrdinaryToPrimitive` · `InstanceofOperator` ·
>   `ArraySpeciesCreate` · `CanBeHeldWeakly` · `SymbolDescriptiveString` · `IsRegExp` · 함수 `String ( value )` · `Symbol ( [ description ] )` ·
>   `Object.prototype.toString ( )` · `Date.prototype [ %Symbol.toPrimitive% ] ( hint )` · 잘 알려진 심볼 표(Well-known Symbols)
> - [TC39 finished proposals](https://github.com/tc39/proposals/blob/main/finished-proposals.md) — `Symbol.prototype.description`(2019) · Symbols as WeakMap keys(2023) · Explicit Resource Management(2027) 의 판을 가릴 때
>
> ★★★ **명세 조항 번호는 인용하지 않는다.** 규칙 진술은 위 문서의 **추상 연산 이름**으로, **값·호출 로그·예외 타입과 메시지는 전부 실행으로** 접지했다.
>
> **실행 검증** — 이 문서의 모든 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮겨 적은 출력이 하나도 없다).
> 배너의 `node20` 은 `~/.nvm/versions/node/v20.19.6/bin/node`, `node18` 은 기본 PATH 의 `node`(v18.19.1)다.
> 브라우저 블록은 **Google Chrome 151** 의 `--headless --dump-dom` 으로 받았다(아래 판별 블록 끝).
> ★★ **예외는 `try`/`catch` 로 받아 `이름 「메시지」` 꼴로만** 찍었다 — 스택트레이스에는 절대 경로가 박혀 재현이 안 된다.
> ★ **이 주제의 블록에는 주소도 시간도 난수도 없다.** 같은 판에서 다시 돌리면 한 글자도 안 변한다.
>
> **버전 — 판 경계**
>
> | 무엇 | 판 | 이 머신에서 |
> |---|---|---|
> | `Symbol()` · `Symbol.for` · 잘 알려진 심볼(`iterator`·`toPrimitive`·`hasInstance`·`toStringTag`·`species`·`isConcatSpreadable`·`match`·`unscopables` …) | **ES2015** | 세 판 전부 있다 |
> | `Symbol.prototype.description` | **ES2019** | 세 판 전부 있다 |
> | 배열 복사 메서드(`toSorted`·`toReversed`·`with`·`toSpliced`) — species 를 **안 읽는** 쪽 | **ES2023** | ★ **node18 에 없다**(동작 (5)) |
> | 심볼을 `WeakMap` 키·`WeakRef` 대상으로(Symbols as WeakMap keys) | **ES2023** | ★ **node18 에 없다**(판별 블록 · 동작 (6)) |
> | `Symbol.dispose`·`Symbol.asyncDispose` · `using` 선언(Explicit Resource Management) | **ES2027**(finished proposals 표) | ★ 심볼은 **세 판 다** 있는데 `using` 문법은 **Chrome 151 만** 컴파일한다(더 들어가면) |
>
> **★★★ 이 주제가 쓰는 창 — 그리고 부적용인 창**
>
> | 창 | 이 주제에서 무엇을 보나 |
> |---|---|
> | ★★★ **① 추상 연산에 로그 심기**(본체) | `[Symbol.toPrimitive](hint)` 가 받는 **hint** 를 연산 24가지에서 · `static [Symbol.hasInstance](v)` 가 받는 인자 · `static get [Symbol.species]()` 를 **읽은 메서드** 14가지 · `Date` 의 자체 `toPrimitive` 를 감싸서 |
> | ★★★ **② 전수 격자** | 키 종류 5 × 키를 늘어놓는 문법 10 — 「**갈린 칸 N / M**」을 스크립트가 센다 · 변환 여섯 가지 중 던지는 칸 · 「브랜드 태그 대 슬롯 판별」이 어긋나는 칸 |
> | ★★★ **③ 브랜드 태그** — ★ **이 주제에서는 창 자체가 과녁이다** | `Object.prototype.toString.call(v)` 가 **`Symbol.toStringTag` 한 프로퍼티로 바꿔치기된다.** 이 창을 다른 편에서 판별 도구로 썼다면, 여기서 그 창이 **어디까지 믿을 만한지**를 잰다(동작 (4)) |
> | ★★ **④ 예외의 `constructor.name` + `message`** | 심볼의 암묵 변환 · `new Symbol` · `instanceof` 우변 · species 가 생성자가 아닐 때 · 레지스트리 심볼을 `WeakMap` 키로 |
> | ★★ **⑤ 두 판 대조기** | 이 주제의 탐침 넷이 **두 판에서 갈린다** — 전부 **ES2023 기능의 유무**와 문구 한 줄이다(실행 검증 표) |
> | ★ **창을 바꿔 물었다**(제5의 상태) | 「레지스트리 심볼은 판 경계를 넘나?」 — 브라우저 iframe 을 쓰는 대신 **`node:vm` 의 새 realm** 으로 물었다(동작 (6) `[3]`). ★ **`vm` 은 호스트 API** 라 ECMA-262 가 보장하는 「realm」 과 같은 것인지는 이 문서가 확인하지 않았다 |
> | ★ **부적용 — 진단의 `(행,열)`**(18-C) | `SyntaxError` 는 두 줄(`with`·`using`)뿐이고 **어느 쪽으로 묶이나**를 가를 일이 없다 — 잴 것이 없다 |
> | ★ **반쯤 부적용 — `Symbol.unscopables`** | 그 심볼이 바꾸는 것은 **`with` 문 하나**인데 `with` 는 **엄격 모드에서 컴파일조차 안 된다**(동작 (5) `[5]`). 비엄격 한 줄로 동작만 확인하고 문항은 (경계) 하나로 줄였다 |
> | ★ **안 쟀다 — 성능** | 「심볼 키는 느리다/빠르다」류의 말을 **한 줄도 쓰지 않는다.** 안 쟀다 |
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 예외 **문구** — `using` 의 `Unexpected identifier` 는 **판마다 실제로 갈렸다** | ★★★ **hint 문자열**(`default`·`number`·`string`)과 **불렸나/안 불렸나** |
> | `unscopables` 객체의 **키 순서** — 판마다 다르다(두 판 대조기 참고) | ★★★ **예외의 종류**(`TypeError`·`SyntaxError`) |
> | 판마다 있는 메서드가 달라지는 줄(ES2023 이전 판) | ★★ 격자의 `o`/`.` 과 「갈린 칸 N / M」 · `Reflect.ownKeys` 의 **순서** |
>
> **선행** — [19 — 이터러블 프로토콜과 `for...of`](../19-iterable-protocol-and-for-of/2-summary.md)(★★★ 직접 선행 — `Symbol.iterator` 하나의 계약) ·
> [02 — 강제 변환과 `==` 대 `===`](../02-coercion-and-loose-equality/2-summary.md)(★★ `ToPrimitive`) ·
> [13 — 객체 리터럴과 프로퍼티](../13-object-literals-and-properties/2-summary.md)(심볼 키가 열거 순서의 셋째 덩어리) ·
> [15 — 프로토타입 체인](../15-prototype-chain/2-summary.md)(`instanceof`) · [17 — 상속과 `super`](../17-inheritance-and-super/2-summary.md)(`Symbol.species`) ·
> [18 — `for...in` 과 열거](../18-for-in-and-enumeration/2-summary.md)(여섯 종 × 아홉 문법 격자).
> **이어지는 곳** — [23 — `Map`·`Set` 과 약한 컬렉션](../23-map-set-and-weak-collections/2-summary.md) · 목록의 **40번 주제** 「비동기 이터레이션」(`Symbol.asyncIterator`) ·
> 목록의 **45번 주제** 「`Proxy`」 · 목록의 **51번 주제** 「명시적 자원 관리 `using`」(`Symbol.dispose`).
>
> ★★★ **19편이 `Symbol.iterator` 하나를 끝까지 팠다.** 여기서는 그것을 **일반화**한다 —
> 「언어가 **어떤 연산 도중에** 객체의 **어떤 심볼 키**를 읽고, 그 값으로 **무엇을 바꾸나**」.
> ★★ **경계 — `Symbol.iterator` 의 호출 순서·`return()` 규칙은 19편이 정본이다.** 여기서는 그 키를 **지우거나 바꿨을 때 누가 따라 바뀌나**만 본다.
> ★★ **경계 — `ToPrimitive` 가 `valueOf`/`toString` 을 고르는 순서는 02편이 정본이다.** 여기서는 **`Symbol.toPrimitive` 가 그 절차를 가로챌 때 받는 hint** 를 전수로 본다.
> ★★ **경계 — `extends Array` 의 결과 생성자는 17편이 정본이다**(`map`·`filter`·`slice`·`from` 이 `Stack`, `static get [Symbol.species]() { return Array }` 로 되돌리기).
> 여기서는 **species 를 읽는 메서드와 안 읽는 메서드**를 가른다.
> ★ **경계 — 약한 컬렉션의 수명 의미는 23편이 정본이다.** 여기서는 「**어떤 심볼이 약한 키가 될 수 있나**」라는 심볼 쪽 성질만.

```sh
# js20b-versions.sh
#!/usr/bin/env bash
# 이 문서의 모든 출력이 어느 판에서 나왔는지 -- 그리고 판별 기능 표(js20b-features.js)를 세 판에 던진다.
set -u -o pipefail
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
for n in "$N18" "$N20"; do
  "$n" -e 'console.log("node " + process.versions.node + "  v8 " + process.versions.v8)'
  "$n" js20b-features.js
done
google-chrome --version | sed 's/ *$//'
google-chrome --headless --dump-dom "file://$PWD/js20b-page.html?js20b-features.js" 2>/dev/null \
  | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d'
```
```js
// js20b-features.js
// 이 문서의 기능이 이 판에 있나 -- 판마다 같은 스크립트를 던진다(node 두 판 · Chrome).
const has = (label, test) => {
  let r;
  try { r = test() ? "yes" : "no"; } catch (e) { r = "no (" + e.constructor.name + ")"; }
  console.log("  " + label.padEnd(44) + r);
};
const compiles = (src) => () => { new Function(src); return true; };
has("ES2015  function* / yield*", compiles("function* g() { yield* [1]; }"));
has("ES2015  Symbol.toPrimitive", () => typeof Symbol.toPrimitive === "symbol");
has("ES2015  Map / Set / WeakMap / WeakSet", () => [Map, Set, WeakMap, WeakSet].every((f) => typeof f === "function"));
has("ES2021  WeakRef / FinalizationRegistry", () => typeof WeakRef === "function" && typeof FinalizationRegistry === "function");
has("ES2023  symbols as WeakMap keys", () => { new WeakMap().set(Symbol("k"), 1); return true; });
has("ES2025  Iterator (global)", () => typeof Iterator === "function");
has("ES2025  Iterator.prototype.map / take", () => typeof [].values().map === "function" && typeof [].values().take === "function");
has("ES2025  Iterator.from", () => typeof Iterator.from === "function");
has("ES2025  Set.prototype.union / isSubsetOf", () => typeof new Set().union === "function" && typeof new Set().isSubsetOf === "function");
has("ES2026  Map.prototype.getOrInsert", () => typeof new Map().getOrInsert === "function");
has("ES2026  Map.prototype.getOrInsertComputed", () => typeof new Map().getOrInsertComputed === "function");
has("ES2026  WeakMap.prototype.getOrInsert", () => typeof new WeakMap().getOrInsert === "function");
```
```text
===== ./js20b-versions.sh (exit=0) =====
node 18.19.1  v8 10.2.154.26-node.28
  ES2015  function* / yield*                  yes
  ES2015  Symbol.toPrimitive                  yes
  ES2015  Map / Set / WeakMap / WeakSet       yes
  ES2021  WeakRef / FinalizationRegistry      yes
  ES2023  symbols as WeakMap keys             no (TypeError)
  ES2025  Iterator (global)                   no
  ES2025  Iterator.prototype.map / take       no
  ES2025  Iterator.from                       no (ReferenceError)
  ES2025  Set.prototype.union / isSubsetOf    no
  ES2026  Map.prototype.getOrInsert           no
  ES2026  Map.prototype.getOrInsertComputed   no
  ES2026  WeakMap.prototype.getOrInsert       no
node 20.19.6  v8 11.3.244.8-node.33
  ES2015  function* / yield*                  yes
  ES2015  Symbol.toPrimitive                  yes
  ES2015  Map / Set / WeakMap / WeakSet       yes
  ES2021  WeakRef / FinalizationRegistry      yes
  ES2023  symbols as WeakMap keys             yes
  ES2025  Iterator (global)                   no
  ES2025  Iterator.prototype.map / take       no
  ES2025  Iterator.from                       no (ReferenceError)
  ES2025  Set.prototype.union / isSubsetOf    no
  ES2026  Map.prototype.getOrInsert           no
  ES2026  Map.prototype.getOrInsertComputed   no
  ES2026  WeakMap.prototype.getOrInsert       no
Google Chrome 151.0.7922.173
  ES2015  function* / yield*                  yes
  ES2015  Symbol.toPrimitive                  yes
  ES2015  Map / Set / WeakMap / WeakSet       yes
  ES2021  WeakRef / FinalizationRegistry      yes
  ES2023  symbols as WeakMap keys             yes
  ES2025  Iterator (global)                   yes
  ES2025  Iterator.prototype.map / take       yes
  ES2025  Iterator.from                       yes
  ES2025  Set.prototype.union / isSubsetOf    yes
  ES2026  Map.prototype.getOrInsert           yes
  ES2026  Map.prototype.getOrInsertComputed   yes
  ES2026  WeakMap.prototype.getOrInsert       yes
```

## 한눈에 — 쉽게 말하면

**심볼은 「세상에 하나뿐인 자물쇠 번호」로 만든 서랍 이름표**다.
글자 이름표(`"size"`)는 누가 붙여도 같은 이름이면 **같은 서랍**을 연다. 남의 코드와 이름이 겹치면 서로의 물건을 덮는다.
심볼 이름표는 만들 때마다 **새 번호**가 찍혀 나온다. 설명(`description`)에 똑같이 `"size"` 라고 적어도 **다른 서랍**이다.

그리고 **언어 자신이 쓰는 이름표 한 벌**이 있다 — 잘 알려진 심볼(`Symbol.iterator`·`Symbol.toPrimitive` …).
관리인(엔진)은 어떤 일을 하기 직전에 **그 이름표가 붙은 서랍부터 열어 본다.** 거기 무엇이 들어 있으면 **자기 방식 대신 그것을 따른다.**

- ★★★ `for...of` 직전에는 `Symbol.iterator` 서랍을, `+` 직전에는 `Symbol.toPrimitive` 서랍을, `instanceof` 직전에는 `Symbol.hasInstance` 서랍을 연다.
- ★★ 글자 이름표를 늘어놓는 도구들(`Object.keys`·`for...in`·`JSON.stringify`)은 **심볼 이름표를 못 본 척**한다. 못 보는 것이지 **숨겨진 것은 아니다** — `Object.getOwnPropertySymbols` 가 다 보여 준다.
- ★ 「**같은 번호를 모두가 공유하는 이름표**」도 만들 수 있다 — `Symbol.for("app")` 는 전역 장부에서 번호를 찾아 준다.

```text
   이름표 종류                         같은 설명으로 두 번 만들면     관리인이 먼저 열어 보나
   ─────────────────────────────────  ───────────────────────────  ──────────────────────────
   "size"          (문자열 키)         같은 서랍                    아니다
   Symbol("size")  (심볼)              다른 서랍                    아니다
   Symbol.for("size") (레지스트리)     같은 서랍 (장부에서 찾는다)  아니다
   Symbol.toPrimitive (잘 알려진 심볼) 하나뿐 (Symbol 에 붙어 있다) ★ 그렇다 -- + · == · `${}` 직전에

   ★ 잘 알려진 심볼이 특별한 것은 「값」이 아니라 「언어가 그 키를 읽는 자리」다
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 새 번호가 찍힌 이름표 | `Symbol("설명")` | `Symbol('a') === Symbol('a')` 가 `false` |
| 이름표에 적힌 메모 | `description` | `Symbol('a').description` 은 `"a"` — **정체가 아니다** |
| 전역 번호 장부 | 전역 심볼 레지스트리 · `Symbol.for` / `Symbol.keyFor` | `Symbol.keyFor(Symbol.for('app'))` 가 `"app"` |
| 관리인이 먼저 열어 보는 서랍 | 잘 알려진 심볼 키 | 그 키에 로그를 심으면 **언제 읽혔나**가 찍힌다 |
| 관리인이 서랍에 넣어 주는 쪽지 | `toPrimitive` 의 hint · `hasInstance` 의 인자 | 로그의 `default` / `number` / `string` |
| 글자 이름표만 세는 도구 | `Object.keys`·`for...in`·`JSON.stringify`·`getOwnPropertyNames` | 격자의 `.` |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.
「**라이브러리가 붙인 메타데이터 키가 사용자 객체의 필드와 겹쳤다**」는 문자열 키의 사고이고,
「**`JSON.stringify` 했더니 심볼로 붙인 필드가 통째로 사라졌다**」는 심볼 키의 사고다.
앞엣것은 심볼을 쓰면 없어지고, 뒤엣것은 심볼을 쓰면 생긴다.

> **심볼(symbol)** — `Symbol()` 이 만드는 원시값. 만들 때마다 **다른 값**이고 프로퍼티 키로 쓸 수 있다.\
> 예: `const k = Symbol("k"); o[k] = 1;`

> **잘 알려진 심볼(well-known symbol)** — `Symbol` 생성자에 붙어 있는 심볼 값들. 명세가 「**이 연산은 이 키를 읽는다**」고 정해 둔 것.\
> 예: `Symbol.iterator`(`for...of` 가 읽는다) · `Symbol.toPrimitive`(원시값 변환이 읽는다).

> **hint** — `ToPrimitive` 가 `Symbol.toPrimitive` 메서드에 넘기는 문자열 인자. `"default"`·`"number"`·`"string"` 셋 중 하나.\
> 예: `+x` 는 `"number"`, `` `${x}` `` 는 `"string"`.

## 이 주제가 답하려는 질문

1. **심볼 키는 어느 문법에 보이고 어느 문법에 안 보이나** — 그리고 「보이지 않는다」는 「비공개」인가?
2. **잘 알려진 심볼은 언어의 어떤 연산을 어디서 가로채나** — `toPrimitive` 의 hint 는 연산자마다 무엇으로 오고, `hasInstance`·`toStringTag`·`species` 는 무엇을 바꾸나?
3. **심볼 자신은 어떻게 변환되고 비교되나** — `String(s)` 은 되는데 `` `${s}` `` 는 왜 안 되고, `Symbol.for` 는 `Symbol()` 과 무엇이 다른가?

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 출력으로 읽는다.

### (1) ★★★ 심볼 키 격자 — 18편의 격자에 심볼 줄을 늘린다

**언제 쓰나** — 「이 객체를 복사/직렬화/순회했더니 **심볼로 붙인 키가 사라졌다(또는 따라왔다)**」를 물을 때.

★★ **18편과 무엇이 다른가** — 18편은 프로퍼티 **여섯 종**(own 셋 · 상속 셋) × 아홉 문법을 댔고, 심볼은 own 한 줄 · 상속 한 줄이었다.
여기서는 **own 만** 남기고 심볼 쪽을 네 줄로 늘렸다 — **보통 심볼 · 비열거 심볼 · `Symbol.for` 심볼 · 잘 알려진 심볼**.
그리고 18편에 없던 **`getOwnPropertySymbols`** 와 **`Object.hasOwn`** 열을 넣었다.

```js
// js20b-22b-key-grid.js
// 심볼 키의 성질 격자 -- 키 종류 × 키를 늘어놓는(또는 복사하는) 문법. 누가 무엇을 보나를 전수로 찍는다.
// 18편의 격자(프로퍼티 여섯 종 × 아홉 문법)에서 own 줄만 떼어 심볼 쪽 줄을 늘렸다.
const sEnum = Symbol("sEnum");
const sHidden = Symbol("sHidden");
const sReg = Symbol.for("sReg");
const o = {};
o.str = 1;
o[sEnum] = 1;
Object.defineProperty(o, sHidden, { value: 1, enumerable: false });
o[sReg] = 1;
o[Symbol.iterator] = function* () {};

const kinds = [
  ["string key", "str"],
  ["symbol key", sEnum],
  ["symbol key, non-enumerable", sHidden],
  ["Symbol.for key", sReg],
  ["Symbol.iterator key", Symbol.iterator],
];
const forIn = (x) => { const r = []; for (const k in x) r.push(k); return r; };
const views = [
  ["for-in", (x) => forIn(x)],
  ["keys", (x) => Object.keys(x)],
  ["entries", (x) => Object.entries(x).map(([k]) => k)],
  ["JSON", (x) => Object.keys(JSON.parse(JSON.stringify(x)))],
  ["gOPN", (x) => Object.getOwnPropertyNames(x)],
  ["gOPS", (x) => Object.getOwnPropertySymbols(x)],
  ["ownKeys", (x) => Reflect.ownKeys(x)],
  ["{...}", (x) => Reflect.ownKeys({ ...x })],
  ["assign", (x) => Reflect.ownKeys(Object.assign({}, x))],
  ["hasOwn", (x) => kinds.map(([, k]) => k).filter((k) => Object.hasOwn(x, k))],
];
console.log("[1] who sees what   (o = sees it, . = does not)");
console.log(("".padEnd(28) + views.map(([n]) => n.padEnd(9)).join("")).trimEnd());
const seen = views.map(([, f]) => f(o));
const grid = kinds.map(([, k]) => seen.map((s) => s.includes(k)));
kinds.forEach(([label], i) => {
  console.log((label.padEnd(28) + grid[i].map((b) => (b ? "o" : ".").padEnd(9)).join("")).trimEnd());
});

console.log("");
console.log("[2] row 'symbol key' against row 'string key', column by column");
const differ = views.filter((_, j) => grid[0][j] !== grid[1][j]).map(([n]) => n);
console.log("  columns that differ " + JSON.stringify(differ));
const sameAs = (a, b) => grid[a].every((v, j) => v === grid[b][j]);
console.log("  'Symbol.for key' row equals 'symbol key' row       " + sameAs(3, 1));
console.log("  'Symbol.iterator key' row equals 'symbol key' row  " + sameAs(4, 1));

console.log("");
console.log("[3] Reflect.ownKeys order -- keys added as: sym1, b, 2, sym2, a, 1");
const q = {};
const sym1 = Symbol("sym1"), sym2 = Symbol("sym2");
q[sym1] = 1; q.b = 1; q[2] = 1; q[sym2] = 1; q.a = 1; q[1] = 1;
console.log("  " + JSON.stringify(Reflect.ownKeys(q).map(String)));

console.log("");
console.log("differing cells (string key vs symbol key) " + differ.length + " / " + views.length);
```
```text
===== node20 js20b-22b-key-grid.js (exit=0) =====
[1] who sees what   (o = sees it, . = does not)
                            for-in   keys     entries  JSON     gOPN     gOPS     ownKeys  {...}    assign   hasOwn
string key                  o        o        o        o        o        .        o        o        o        o
symbol key                  .        .        .        .        .        o        o        o        o        o
symbol key, non-enumerable  .        .        .        .        .        o        o        .        .        o
Symbol.for key              .        .        .        .        .        o        o        o        o        o
Symbol.iterator key         .        .        .        .        .        o        o        o        o        o

[2] row 'symbol key' against row 'string key', column by column
  columns that differ ["for-in","keys","entries","JSON","gOPN","gOPS"]
  'Symbol.for key' row equals 'symbol key' row       true
  'Symbol.iterator key' row equals 'symbol key' row  true

[3] Reflect.ownKeys order -- keys added as: sym1, b, 2, sym2, a, 1
  ["1","2","b","a","Symbol(sym1)","Symbol(sym2)"]

differing cells (string key vs symbol key) 6 / 10
```

```text
   [1] 을 「글자 줄 대 심볼 줄」로 접으면

                     글자만 센다                              심볼만 센다   둘 다        키 하나를 묻는다
               ┌──────────────────────────────────┐        ┌──────┐   ┌──────────────────┐   ┌──────┐
               for-in  keys  entries  JSON  gOPN            gOPS       ownKeys {...} assign    hasOwn
   글자 키        o      o      o       o     o               .           o      o     o          o
   심볼 키        .      .      .       .     .               o           o      o     o          o
   ───────────────────────────────────────────────────────────────────────────────────────────────────
   갈린 열        ★      ★      ★       ★     ★               ★           -      -     -          -

   ★ 비열거 심볼은 {...} · assign 에서도 빠진다 -- 거기는 「열거 가능」도 본다
```

**그림 해설 — 한 덩어리에 한 문장.**

- ★★★ **집계 줄이 `6 / 10`** 이다 — 글자 키와 심볼 키가 **열 개 중 여섯 열에서 반대로** 답한다.
  `for-in`·`keys`·`entries`·`JSON`·`gOPN` 다섯은 **글자만**, `gOPS` 하나는 **심볼만** 본다.
- ★★★ **안 갈린 네 열이 「심볼은 비공개가 아니다」의 증거다.** `Reflect.ownKeys`·스프레드·`Object.assign`·`Object.hasOwn` 은 심볼 키를 **그대로** 본다.
  스프레드와 `assign` 은 **심볼 키를 복사해 간다** — 「심볼로 숨겼다」는 복사 한 번에 무너진다.
- ★★ **`Symbol.for` 줄도 `Symbol.iterator` 줄도 보통 심볼 줄과 같다**(`[2]` 의 두 `true`). **키로서는 심볼 종류를 안 가린다.** 종류가 갈리는 곳은 약한 참조뿐이다(동작 (6)).
- ★★ **비열거 심볼 줄**은 스프레드·`assign` 에서도 `.` 이다 — 그 둘은 「**own ∧ 열거 가능**」을 본다(18편의 결론과 같다). 심볼이냐는 그 둘의 기준에 **없다.**
- ★★ **`[3]` — 넣은 순서가 `sym1, b, 2, sym2, a, 1` 인데 나온 순서는 `["1","2","b","a","Symbol(sym1)","Symbol(sym2)"]`** 다.
  13편의 세 덩어리(정수 오름차순 → 문자열 삽입순 → **심볼 삽입순**) 그대로다 — **심볼을 먼저 넣어도 끝으로 간다.**

★★ **값 쪽도 한 줄 보탠다** — 키가 아니라 **값이 심볼이면** `JSON.stringify` 는 그 프로퍼티를 **지우고**, 배열 안이면 **`null` 로 바꾼다**
(동작 (3)의 `JSON.stringify({ v: s })` → `"{}"` · `JSON.stringify([s])` → `"[null]"`). **키든 값이든 JSON 에는 심볼 자리가 없다.**

### (2) ★★★ `Symbol.toPrimitive` 의 hint 로그 — 연산자 24가지

**언제 쓰나** — 「이 연산자가 내 객체를 **숫자로 원하나, 문자열로 원하나, 모르겠다고 하나**」를 물을 때.
★★★ 결과값으로는 답이 안 나온다 — `x + 1` 이 `8` 인 것은 hint 가 `default` 여도 `number` 여도 같다.

02편은 이 절차의 **안쪽**(`valueOf`·`toString` 중 누가 먼저)을 로그로 봤고, `[5]` 에서 세 자리(`o + 1`·`` `${o}` ``·`o * 2`)의 hint 를 찍었다.
여기서는 **hint 하나만 찍는 메서드**를 달아 **24가지 연산**을 전수로 돈다.

```text
   ToPrimitive(x, 원하는 타입?)                         -- 명세의 추상 연산

   ① x[Symbol.toPrimitive] 를 GetMethod 로 읽는다
        │
        ├─ undefined 또는 null  ──▶ 없는 셈 친다 -> OrdinaryToPrimitive (02편: valueOf / toString)
        ├─ 함수가 아니다        ──▶ TypeError
        └─ 함수다
             │   hint = 원하는 타입이 없으면 "default"
             │          string 이면 "string" · number 면 "number"
             ▼
   ② 그 함수를 (x, hint) 로 부른다
        ├─ 원시값을 돌려주면  ──▶ 그것이 답 (★ 심볼이어도 원시값이다)
        └─ 객체를 돌려주면    ──▶ TypeError
```

```js
// js20b-22c-toprimitive-hints.js
// Symbol.toPrimitive 에 로그를 심고 연산자·내장 함수마다 hint 가 무엇으로 오나를 찍는다.
// 02편의 ToPrimitive 탐침(valueOf/toString 순서)을 이 한 메서드로 가로챈 판이다.
const L = [];
const x = { [Symbol.toPrimitive](hint) { L.push(hint); return hint === "string" ? "S" : 7; } };
let counting = true;
const tally = { default: 0, number: 0, string: 0, "(no call)": 0 };
const show = (v) => (typeof v === "string" ? JSON.stringify(v) : typeof v === "bigint" ? v + "n" : String(v));
function probe(label, run) {
  L.length = 0;
  let r;
  try { r = show(run()); } catch (e) { r = e.constructor.name + " 「" + e.message + "」"; }
  const hints = L.length ? L.join(",") : "(no call)";
  if (counting) for (const h of L.length ? L : ["(no call)"]) tally[h]++;
  console.log("  " + label.padEnd(24) + hints.padEnd(26) + r);
}

console.log("[1] expression               hint(s)                   result");
probe("x + 1", () => x + 1);
probe("x + ''", () => x + "");
probe("`${x}`", () => `${x}`);
probe("x == 7", () => x == 7);
probe("x != 'S'", () => x != "S");
probe("x === 7", () => x === 7);
probe("x < 8", () => x < 8);
probe("x * 1", () => x * 1);
probe("+x", () => +x);
probe("-x", () => -x);
probe("x ** 1", () => x ** 1);
probe("x | 0", () => x | 0);
probe("String(x)", () => String(x));
probe("Number(x)", () => Number(x));
probe("BigInt(x)", () => BigInt(x));
probe("[x].join()", () => [x].join());
probe("({})[x] = 1 -> key", () => { const t = {}; t[x] = 1; return Object.keys(t)[0]; });
probe("x in {S: 1}", () => x in { S: 1 });
probe("new Date(x).getTime()", () => new Date(x).getTime());
probe("isNaN(x)", () => isNaN(x));
probe("'aSb'.includes(x)", () => "aSb".includes(x));
probe("!x", () => !x);
probe("x ? 'y' : 'n'", () => (x ? "y" : "n"));
probe("JSON.stringify(x)", () => JSON.stringify(x));

console.log("");
console.log("[2] hint tally " + JSON.stringify(tally));
counting = false;

console.log("");
console.log("[3] what the method returns, or what it is");
const spy = (f) => function (hint) { L.push("@@toPrimitive(" + hint + ")"); return f(); };
const bad = (label, v) => probe(label, () => { const o = { [Symbol.toPrimitive]: v, valueOf() { L.push("valueOf"); return 1; }, toString() { L.push("toString"); return "T"; } }; return o + 1; });
bad("returns an object", spy(() => ({})));
bad("returns a symbol", spy(() => Symbol("r")));
bad("is the number 1", 1);
bad("is null", null);
bad("is undefined", undefined);
probe("returns a symbol, `${}`", () => `${{ [Symbol.toPrimitive]: spy(() => Symbol("r")) }}`);

console.log("");
console.log("[4] Date carries its own Symbol.toPrimitive -- spy on it");
const dproto = Date.prototype;
const orig = dproto[Symbol.toPrimitive];
const d = new Date(0);
Object.defineProperty(d, Symbol.toPrimitive, { value(hint) { L.push(hint); return orig.call(this, hint); } });
probe("typeof (d + 1)", () => typeof (d + 1));
probe("typeof (d - 1)", () => typeof (d - 1));
probe("d == d.toString()", () => d == d.toString());
probe("d < 1", () => d < 1);
console.log("  own descriptor on Date.prototype: " + JSON.stringify(Object.getOwnPropertyDescriptor(dproto, Symbol.toPrimitive), (k, v) => (typeof v === "function" ? "fn" : v)));
```
```text
===== node20 js20b-22c-toprimitive-hints.js (exit=0) =====
[1] expression               hint(s)                   result
  x + 1                   default                   8
  x + ''                  default                   "7"
  `${x}`                  string                    "S"
  x == 7                  default                   true
  x != 'S'                default                   true
  x === 7                 (no call)                 false
  x < 8                   number                    true
  x * 1                   number                    7
  +x                      number                    7
  -x                      number                    -7
  x ** 1                  number                    7
  x | 0                   number                    7
  String(x)               string                    "S"
  Number(x)               number                    7
  BigInt(x)               number                    7n
  [x].join()              string                    "S"
  ({})[x] = 1 -> key      string                    "S"
  x in {S: 1}             string                    true
  new Date(x).getTime()   default                   7
  isNaN(x)                number                    false
  'aSb'.includes(x)       string                    true
  !x                      (no call)                 false
  x ? 'y' : 'n'           (no call)                 "y"
  JSON.stringify(x)       (no call)                 "{}"

[2] hint tally {"default":5,"number":9,"string":6,"(no call)":4}

[3] what the method returns, or what it is
  returns an object       @@toPrimitive(default)    TypeError 「Cannot convert object to primitive value」
  returns a symbol        @@toPrimitive(default)    TypeError 「Cannot convert a Symbol value to a number」
  is the number 1         (no call)                 TypeError 「number 1 is not a function」
  is null                 valueOf                   2
  is undefined            valueOf                   2
  returns a symbol, `${}` @@toPrimitive(string)     TypeError 「Cannot convert a Symbol value to a string」

[4] Date carries its own Symbol.toPrimitive -- spy on it
  typeof (d + 1)          default                   "string"
  typeof (d - 1)          number                    "number"
  d == d.toString()       default                   true
  d < 1                   number                    true
  own descriptor on Date.prototype: {"value":"fn","writable":false,"enumerable":false,"configurable":true}
```

```text
   [1] 을 hint 로 묶으면

   "default"  (5)   x + 1 · x + '' · x == 7 · x != 'S' · new Date(x)
   "number"   (9)   x < 8 · x * 1 · +x · -x · x ** 1 · x | 0 · Number(x) · BigInt(x) · isNaN(x)
   "string"   (6)   `${x}` · String(x) · [x].join() · 키 자리 t[x] · x in {...} · 'aSb'.includes(x)
   안 부른다  (4)   x === 7 · !x · x ? : · JSON.stringify(x)

   ★ 「+ 는 문자열 연산자」가 아니다 -- + 와 == 는 "default" 를 준다
   ★ Date 만 "default" 를 "string" 처럼 다룬다 ([4])
```

**그림 해설.**

- ★★★ **`x + ''` 가 `"default"` 를 받고 결과가 `"7"`** 이다. `+` 는 **어느 쪽을 원하는지 말하지 않는다** — 원시값을 얻은 **다음에** 문자열이 끼면 이어 붙일 뿐이다.
  그래서 메서드가 `default` 에 `7` 을 주자 **`"S"` 가 아니라 `"7"`** 이 됐다. 02편 `[3]` 의 「`o + 'x'` 가 `valueOf` 를 부른다」와 **같은 사실의 다른 창**이다.
- ★★★ **`` `${x}` `` 는 `"string"` 이고 `x + ''` 는 `"default"`** 다. 둘 다 「문자열로 만들기」로 쓰이지만 **엔진에게 하는 말이 다르다.**
- ★★ **`x == 7` 과 `x != 'S'` 는 `"default"`**, **`x < 8` 은 `"number"`** 다. 느슨한 같음은 원하는 타입을 **말하지 않고**, 대소 비교는 **숫자를 원한다고 말한다.**
- ★★ **`new Date(x)` 는 `"default"`** 다 — 인자 하나짜리 `Date` 는 **원하는 타입을 말하지 않고** 원시값을 구한다.
- ★★ **키 자리 `t[x]` · `x in {...}` · `'aSb'.includes(x)` 가 `"string"`** 이다. 키 자리는 `ToPropertyKey`(13편), `includes` 는 인자를 `ToString` 한다.
- ★★ **`BigInt(x)` 는 `"number"`** 이고 결과가 `7n` 이다 — `BigInt` 도 숫자 쪽으로 묻는다.
- ★★★ **안 부른 넷** — `===` 는 변환을 **아예 안 한다.** `!x` 와 `x ? :` 는 **ToBoolean** 이라 객체면 무조건 참이다 — **진릿값에는 훅이 없다.**
  `JSON.stringify(x)` 는 `toJSON` 을 볼 뿐 `toPrimitive` 를 안 읽어 `"{}"` 이다.
- ★ **집계 줄 `{"default":5,"number":9,"string":6,"(no call)":4}`** — 이 수는 **탐침이 고른 24가지의 분포**이지 언어의 성질이 아니다. 성질은 **줄마다의 hint** 다.

**`[3]` — 메서드가 이상한 것을 돌려주거나, 메서드가 아니면.**

- ★★★ **`null`·`undefined` 면 「없는 셈」** 이다 — `valueOf` 로 넘어가 `2` 가 나왔다. 명세의 `GetMethod` 가 둘을 **없음**으로 읽기 때문이다.
  ★ **`1` 이면 `TypeError 「number 1 is not a function」`** 이다 — 「없음」이 아니라 「**잘못 있음**」이다. **`null` 과 `1` 이 반대로 갈린다.**
- ★★ **객체를 돌려주면 `TypeError 「Cannot convert object to primitive value」`** — 02편 `[4]` 의 「둘 다 객체」와 **같은 문구**다. `valueOf`/`toString` 으로 **재시도하지 않는다.**
- ★★ **심볼을 돌려주면 변환 자체는 통과한다** — 심볼도 원시값이다. 터지는 것은 **그다음**이다: `+ 1` 은 숫자로, `` `${}` `` 는 문자열로 만들려다
  `Cannot convert a Symbol value to a number` / `to a string` 이 된다(동작 (3) 과 같은 문구).

**`[4]` — `Date` 는 자기 `Symbol.toPrimitive` 를 갖고 있다.**

- ★★★ **`d + 1` 은 hint `"default"` 를 받고 문자열이 된다**(`typeof` 가 `"string"`). 명세 문장 그대로다 —
  "Dates are unique among built-in ECMAScript object in that they treat "default" as being equivalent to "string"".
  **다른 내장 객체는 `default` 를 `number` 처럼** 다룬다(02편 `[3]` 의 기본 객체가 그랬다).
- ★ **`d - 1` 과 `d < 1` 은 `"number"`** — 산술·대소 비교는 `Date` 여도 숫자다.
- ★ **그 메서드는 `Date.prototype` 에 `writable: false` · `configurable: true`** 로 붙어 있다. 그래서 탐침은 대입이 아니라 `defineProperty` 로 **인스턴스에** 감쌌다.

### (3) ★★ 심볼 자신의 변환 — 「명시적이면 된다」가 아니다

**언제 쓰나** — 로그·에러 메시지에 **심볼 키를 찍으려다** `TypeError` 가 났을 때.

```js
// js20b-22a-basics.js
// Symbol() 한 개의 성질 -- 만들기 · 설명 · 같음 · 변환. 예외는 이름과 메시지로 찍는다.
const row = (label, v) => console.log("  " + label.padEnd(36) + v);
const attempt = (label, run) => {
  let r;
  try { r = run(); r = typeof r === "string" ? JSON.stringify(r) : String(r); }
  catch (e) { r = e.constructor.name + " 「" + e.message + "」"; }
  row(label, r);
};

console.log("[1] making symbols");
attempt("typeof Symbol('a')", () => typeof Symbol("a"));
attempt("Symbol('a') === Symbol('a')", () => Symbol("a") === Symbol("a"));
attempt("new Symbol('a')", () => new Symbol("a"));
attempt("typeof Object(Symbol('a'))", () => typeof Object(Symbol("a")));
attempt("Object(s) == s  (same s)", () => { const s = Symbol("a"); return Object(s) == s; });

console.log("");
console.log("[2] description");
attempt("Symbol('a').description", () => Symbol("a").description);
attempt("Symbol('').description", () => Symbol("").description);
attempt("Symbol().description", () => Symbol().description);
attempt("Symbol(undefined).description", () => Symbol(undefined).description);
attempt("Symbol(42).description", () => Symbol(42).description);
attempt("Symbol({}).description", () => Symbol({}).description);

console.log("");
console.log("[3] String() · .toString() · Boolean() · a symbol key under Object.keys");
const s = Symbol("k");
attempt("String(s)", () => String(s));
attempt("s.toString()", () => s.toString());
attempt("Boolean(s) / !!s", () => Boolean(s) + " / " + !!s);
attempt("Object.keys({ [s]: 1 }).length", () => Object.keys({ [s]: 1 }).length);

console.log("");
console.log("[4] operators · concat · join · Number() · JSON");
attempt("s + ''", () => s + "");
attempt("`${s}`", () => `${s}`);
attempt("'x'.concat(s)", () => "x".concat(s));
attempt("[s].join()", () => [s].join());
attempt("+s", () => +s);
attempt("Number(s)", () => Number(s));
attempt("s + 1", () => s + 1);
attempt("s == 'Symbol(k)'", () => s == "Symbol(k)");
attempt("s < 1", () => s < 1);
attempt("JSON.stringify(s)", () => JSON.stringify(s));
attempt("JSON.stringify({ v: s })", () => JSON.stringify({ v: s }));
attempt("JSON.stringify([s])", () => JSON.stringify([s]));

console.log("");
const cells = [];
for (const [label, f] of [["String(s)", () => String(s)], ["s + ''", () => s + ""], ["`${s}`", () => `${s}`],
  ["[s].join()", () => [s].join()], ["Number(s)", () => Number(s)], ["+s", () => +s]]) {
  try { f(); cells.push(label + ":ok"); } catch (e) { cells.push(label + ":" + e.constructor.name); }
}
console.log("[5] six conversions: " + cells.join("  "));
console.log("throwing cells " + cells.filter((c) => !c.endsWith(":ok")).length + " / " + cells.length);
```
```text
===== node20 js20b-22a-basics.js (exit=0) =====
[1] making symbols
  typeof Symbol('a')                  "symbol"
  Symbol('a') === Symbol('a')         false
  new Symbol('a')                     TypeError 「Symbol is not a constructor」
  typeof Object(Symbol('a'))          "object"
  Object(s) == s  (same s)            true

[2] description
  Symbol('a').description             "a"
  Symbol('').description              ""
  Symbol().description                undefined
  Symbol(undefined).description       undefined
  Symbol(42).description              "42"
  Symbol({}).description              "[object Object]"

[3] String() · .toString() · Boolean() · a symbol key under Object.keys
  String(s)                           "Symbol(k)"
  s.toString()                        "Symbol(k)"
  Boolean(s) / !!s                    "true / true"
  Object.keys({ [s]: 1 }).length      0

[4] operators · concat · join · Number() · JSON
  s + ''                              TypeError 「Cannot convert a Symbol value to a string」
  `${s}`                              TypeError 「Cannot convert a Symbol value to a string」
  'x'.concat(s)                       TypeError 「Cannot convert a Symbol value to a string」
  [s].join()                          TypeError 「Cannot convert a Symbol value to a string」
  +s                                  TypeError 「Cannot convert a Symbol value to a number」
  Number(s)                           TypeError 「Cannot convert a Symbol value to a number」
  s + 1                               TypeError 「Cannot convert a Symbol value to a number」
  s == 'Symbol(k)'                    false
  s < 1                               TypeError 「Cannot convert a Symbol value to a number」
  JSON.stringify(s)                   undefined
  JSON.stringify({ v: s })            "{}"
  JSON.stringify([s])                 "[null]"

[5] six conversions: String(s):ok  s + '':TypeError  `${s}`:TypeError  [s].join():TypeError  Number(s):TypeError  +s:TypeError
throwing cells 5 / 6
```

```text
   심볼 s 를 문자열로

   String(s)        ── 명세의 String( value ) ──▶ 「value 가 Symbol 이면 SymbolDescriptiveString」 ──▶ "Symbol(k)"
   s.toString()     ── Symbol.prototype.toString ─────────────────────────────────────────────▶ "Symbol(k)"

   s + ''  `${s}`  'x'.concat(s)  [s].join()
                    ── 전부 추상 연산 ToString(s) ──▶ 「Symbol 이면 TypeError」
                                                       -> TypeError 「Cannot convert a Symbol value to a string」

   심볼 s 를 숫자로
   +s  Number(s)  s + 1  s < 1    ── ToNumber(s) ──▶ -> TypeError 「Cannot convert a Symbol value to a number」

   ★ 문자열 쪽에만 「String() 이 먼저 심볼을 걸러 내는」 샛길이 있다. 숫자 쪽에는 없다
```

**그림 해설.**

- ★★★ **집계 줄 `throwing cells 5 / 6`** — 여섯 변환 중 **`String(s)` 하나만** 된다.
  ★★★ **「명시적 변환은 되고 암묵적 변환만 막힌다」는 틀린 요약이다** — `Number(s)` 는 명시적인데 **던진다.**
  갈리는 기준은 「명시적이냐」가 아니라 「**`String` 함수가 심볼을 따로 챙기느냐**」다(명세: "If NewTarget is undefined and value is a Symbol, return SymbolDescriptiveString(value).").
- ★★ **`` `${s}` `` 가 던진다** — 템플릿 리터럴은 `ToString` 을 부른다. **로그 문자열에 심볼을 끼워 넣는 것은 `String(s)` 이나 `s.description` 으로** 해야 한다.
- ★★ **`[s].join()` 도 던진다** — 원소마다 `ToString` 이다. 02편의 「배열은 원소마다 `String()` 을 부른다」는 **문자 그대로는 틀린 줄**이 여기서 드러난다:
  원소에는 함수 `String` 이 아니라 **추상 연산 `ToString`** 이 붙는다(그래서 심볼 샛길이 없다).
- ★★ **`s == 'Symbol(k)'` 는 던지지 않고 `false`** 다. 느슨한 같음에서 한쪽이 심볼이면 **변환 없이 다르다**고 답한다. 대소 비교(`s < 1`)는 숫자로 바꾸려다 던진다.
- ★ **`new Symbol('a')` 는 `TypeError 「Symbol is not a constructor」`** — 명세의 `Symbol` 함수 첫 줄이 "If NewTarget is not undefined, throw a TypeError exception." 이다.
  ★ 그런데 **`Object(Symbol('a'))` 는 된다**(`"object"`) — 래퍼 객체를 **`new` 없이** 만드는 길이다. 01편의 임시 래핑과 같은 래퍼다.
- ★ **`description`** — `Symbol()` 과 `Symbol(undefined)` 는 `undefined`, `Symbol('')` 은 `""` 다. **없음과 빈 문자열이 갈린다.**
  인자는 `ToString` 을 거치므로 `Symbol(42)` 는 `"42"`, `Symbol({})` 는 `"[object Object]"` 다.

### (4) ★★★ `Symbol.toStringTag` — 브랜드 태그 창 ③이 얼마나 믿을 만한가

**언제 쓰나** — `Object.prototype.toString.call(v) === "[object Array]"` 같은 **타입 검사 관용구**를 믿어도 되나를 물을 때.
★ 이 갈래는 **③ 브랜드 태그**를 판별 창으로 써 왔다. 여기서는 **그 창을 과녁으로** 놓는다.

```text
   Object.prototype.toString.call(v)                     -- 명세 그대로

   ① 내부 슬롯을 본다 → builtinTag
        IsArray        -> "Array"
        [[ParameterMap]] -> "Arguments"   [[Call]] -> "Function"   [[ErrorData]] -> "Error"
        [[BooleanData]] · [[NumberData]] · [[StringData]] · [[DateValue]] · [[RegExpMatcher]]
        그 밖          -> "Object"
   ② v[Symbol.toStringTag] 를 읽는다 → tag
        문자열이면 tag 를 쓴다  ★ ①을 덮어쓴다
        문자열이 아니면 builtinTag
   ③ "[object " + 그것 + "]"

   ★ Map · Set · Promise 는 ①의 목록에 없다 -- 그들의 "Map" 은 프로토타입에 붙은 toStringTag 프로퍼티다
```

```js
// js20b-22e-tostringtag.js
// Symbol.toStringTag 로 브랜드 태그 창 ③(Object.prototype.toString.call)을 바꿔치기한다.
// 같은 값에 내부 슬롯을 보는 판별을 나란히 대서 두 창이 갈리는 칸을 센다.
const tag = (v) => Object.prototype.toString.call(v);
const slot = {
  Array: (v) => Array.isArray(v),
  Map: (v) => { try { Map.prototype.has.call(v, 1); return true; } catch { return false; } },
  Date: (v) => { try { Date.prototype.getTime.call(v); return true; } catch { return false; } },
  Promise: (v) => { try { Promise.prototype.then.call(v, () => {}); return true; } catch { return false; } },
};

console.log("[1] brand tags of built-ins, as they come");
for (const [label, v] of [["[]", []], ["new Map()", new Map()], ["new Date(0)", new Date(0)], ["Promise.resolve()", Promise.resolve()],
  ["new Error('e')", new Error("e")], ["function(){}", function () {}], ["null", null], ["{}", {}], ["Symbol()", Symbol()]]) {
  console.log("  " + label.padEnd(26) + tag(v));
}

console.log("");
console.log("[2] a string-valued Symbol.toStringTag, and a slot check on the same value");
console.log("  value".padEnd(40) + "toString tag".padEnd(20) + "slot check");
const cases = [
  ["{ tag 'Array' }", { [Symbol.toStringTag]: "Array" }, "Array"],
  ["{ tag 'Map' }", { [Symbol.toStringTag]: "Map" }, "Map"],
  ["{ tag 'Date' }", { [Symbol.toStringTag]: "Date" }, "Date"],
  ["{ tag 'Promise' }", { [Symbol.toStringTag]: "Promise" }, "Promise"],
  ["[] with tag 'Foo'", Object.assign([], { [Symbol.toStringTag]: "Foo" }), "Array"],
  ["new Map() with tag 'Foo'", Object.defineProperty(new Map(), Symbol.toStringTag, { value: "Foo" }), "Map"],
  ["new Date(0) with tag 'Foo'", Object.assign(new Date(0), { [Symbol.toStringTag]: "Foo" }), "Date"],
];
let split = 0;
for (const [label, v, kind] of cases) {
  const t = tag(v);
  const says = t === "[object " + kind + "]";
  const s = slot[kind](v);
  if (says !== s) split++;
  console.log(("  " + label).padEnd(40) + t.padEnd(20) + kind + " slot " + s);
}

console.log("");
console.log("[3] a tag that is not a string");
console.log("  { tag 42 }".padEnd(40) + tag({ [Symbol.toStringTag]: 42 }));
console.log("  { tag undefined }".padEnd(40) + tag({ [Symbol.toStringTag]: undefined }));

console.log("");
console.log("[4] where Map's tag lives -- and after deleting it");
console.log("  descriptor on Map.prototype  " + JSON.stringify(Object.getOwnPropertyDescriptor(Map.prototype, Symbol.toStringTag)));
const arrDesc = Object.getOwnPropertyDescriptor(Array.prototype, Symbol.toStringTag);
console.log("  descriptor on Array.prototype " + JSON.stringify(arrDesc === undefined ? "none" : arrDesc));
delete Map.prototype[Symbol.toStringTag];
console.log("  after delete: tag(new Map()) " + tag(new Map()));

console.log("");
console.log("cells where the toString tag and the slot check disagree " + split + " / " + cases.length);
```
```text
===== node20 js20b-22e-tostringtag.js (exit=0) =====
[1] brand tags of built-ins, as they come
  []                        [object Array]
  new Map()                 [object Map]
  new Date(0)               [object Date]
  Promise.resolve()         [object Promise]
  new Error('e')            [object Error]
  function(){}              [object Function]
  null                      [object Null]
  {}                        [object Object]
  Symbol()                  [object Symbol]

[2] a string-valued Symbol.toStringTag, and a slot check on the same value
  value                                 toString tag        slot check
  { tag 'Array' }                       [object Array]      Array slot false
  { tag 'Map' }                         [object Map]        Map slot false
  { tag 'Date' }                        [object Date]       Date slot false
  { tag 'Promise' }                     [object Promise]    Promise slot false
  [] with tag 'Foo'                     [object Foo]        Array slot true
  new Map() with tag 'Foo'              [object Foo]        Map slot true
  new Date(0) with tag 'Foo'            [object Foo]        Date slot true

[3] a tag that is not a string
  { tag 42 }                            [object Object]
  { tag undefined }                     [object Object]

[4] where Map's tag lives -- and after deleting it
  descriptor on Map.prototype  {"value":"Map","writable":false,"enumerable":false,"configurable":true}
  descriptor on Array.prototype "none"
  after delete: tag(new Map()) [object Object]

cells where the toString tag and the slot check disagree 7 / 7
```

**그림 해설.**

- ★★★ **집계 줄 `7 / 7`** — 태그를 붙인 일곱 칸 **전부에서** 브랜드 태그와 슬롯 판별이 **어긋났다.**
  - **위조**(평범한 객체에 태그 `'Array'`·`'Map'`·`'Date'`·`'Promise'`) — 태그는 `[object Array]` 라고 말하는데 `Array.isArray` 는 `false`, `Map.prototype.has.call` 은 던진다.
  - **은폐**(진짜 배열·`Map`·`Date` 에 태그 `'Foo'`) — 태그는 `[object Foo]` 라고 말하는데 슬롯 판별은 `true` 다.
  ★★★ **태그는 「무엇인가」가 아니라 「무엇이라고 자칭하나」다.**
- ★★ **배열도 은폐된다** — `Array` 는 ①의 목록에 **있는데도**(`IsArray`) ②가 문자열이면 덮어쓴다. 슬롯이 있는 타입도 **태그 앞에서는 보호받지 못한다.**
- ★★ **`[4]` — `Map` 의 태그는 `Map.prototype` 의 프로퍼티**(`value: "Map"` · `writable: false` · `configurable: true`)다. 지우자 `new Map()` 이 **`[object Object]`** 가 됐다.
  **`Array.prototype` 에는 그런 프로퍼티가 없다**(`"none"`) — 배열의 `"Array"` 는 ①에서 온다. **같은 `[object X]` 가 두 가지 출처를 갖는다.**
- ★ **태그가 문자열이 아니면 무시된다**(`42`·`undefined` → `[object Object]`).
- ★★ **그래서 판별은 슬롯을 두드리는 쪽이 정본이다** — `Array.isArray` · 메서드를 `call` 해 보기(`Map.prototype.has.call`). 이것은 목록의 **34번 주제** 「타입 검사 관용구」가 이어받는다.

### (5) ★★ 언어가 읽는 다른 키들 — `hasInstance` · `species` · `iterator` · `isConcatSpreadable` · `match` · `unscopables`

#### (5-a) `Symbol.hasInstance` — `instanceof` 는 우변에게 묻는다

15편 `[4]` 가 `Never`·`Always` 두 클래스로 「`hasInstance` 를 달면 체인 순회가 안 일어난다」를 이미 보였다. 여기서는 **무엇이 전달되고, 무엇이 돌아오고, 어디에 달 수 있나**를 본다.

```text
   V instanceof target                                   -- InstanceofOperator

   ① target 이 객체가 아니면              -> TypeError 「... is not an object」
   ② h = GetMethod(target, Symbol.hasInstance)
        함수가 아니면                     -> TypeError
   ③ h 가 있으면  ToBoolean( h.call(target, V) )   ★ 돌려준 값을 불리언으로 접는다
   ④ 없고 target 을 부를 수 없으면       -> TypeError 「... is not callable」
   ⑤ 있고 부를 수 있으면  OrdinaryHasInstance -- 체인 순회 (15편)

   ★ 보통 함수에는 ③ 이 늘 있다: Function.prototype[Symbol.hasInstance] 를 물려받기 때문이다
```

```js
// js20b-22d-hasinstance.js
// Symbol.hasInstance -- instanceof 가 오른쪽 피연산자에게 무엇을 묻나. 15편 [4] 의 뒤를 잇는다.
const row = (label, v) => console.log("  " + label.padEnd(50) + v);
const attempt = (label, run) => {
  let r;
  try { r = String(run()); } catch (e) { r = e.constructor.name + " 「" + e.message + "」"; }
  row(label, r);
};

console.log("[1] a logging hasInstance -- what it receives, what instanceof returns");
const L = [];
class Even { static [Symbol.hasInstance](v) { L.push("hasInstance(" + JSON.stringify(v) + ")"); return v % 2 === 0 ? "yes" : 0; } }
attempt("4 instanceof Even", () => 4 instanceof Even);
attempt("3 instanceof Even", () => 3 instanceof Even);
attempt("typeof (4 instanceof Even)", () => typeof (4 instanceof Even));
row("log", JSON.stringify(L));

console.log("");
console.log("[2] the right-hand side");
attempt("({}) instanceof { [Symbol.hasInstance]: () => true }", () => ({}) instanceof { [Symbol.hasInstance]: () => true });
attempt("({}) instanceof {}", () => ({}) instanceof {});
attempt("({}) instanceof { [Symbol.hasInstance]: 1 }", () => ({}) instanceof { [Symbol.hasInstance]: 1 });
attempt("({}) instanceof 1", () => ({}) instanceof 1);

console.log("");
console.log("[3] Function.prototype[Symbol.hasInstance] -- its descriptor");
row("descriptor", JSON.stringify(Object.getOwnPropertyDescriptor(Function.prototype, Symbol.hasInstance), (k, v) => (typeof v === "function" ? "fn" : v)));

console.log("");
console.log("[4] putting a hasInstance on a plain function F");
function F() {}
attempt("sloppy  F[Symbol.hasInstance] = () => true", () => { F[Symbol.hasInstance] = () => true; return "no throw"; });
attempt("  then ({}) instanceof F", () => ({}) instanceof F);
attempt("  then hasOwn(F, Symbol.hasInstance)", () => Object.hasOwn(F, Symbol.hasInstance));
attempt("strict  F[Symbol.hasInstance] = () => true", () => { "use strict"; F[Symbol.hasInstance] = () => true; return "no throw"; });
attempt("defineProperty(F, Symbol.hasInstance, ...)", () => { Object.defineProperty(F, Symbol.hasInstance, { value: () => true }); return "no throw"; });
attempt("  then ({}) instanceof F", () => ({}) instanceof F);

console.log("");
console.log("[5] the default path for comparison -- Function.prototype[Symbol.hasInstance].call");
class A {}
const a = new A();
attempt("Function.prototype[@@hasInstance].call(A, a)", () => Function.prototype[Symbol.hasInstance].call(A, a));
attempt("Function.prototype[@@hasInstance].call(A, {})", () => Function.prototype[Symbol.hasInstance].call(A, {}));
```
```text
===== node20 js20b-22d-hasinstance.js (exit=0) =====
[1] a logging hasInstance -- what it receives, what instanceof returns
  4 instanceof Even                                 true
  3 instanceof Even                                 false
  typeof (4 instanceof Even)                        boolean
  log                                               ["hasInstance(4)","hasInstance(3)","hasInstance(4)"]

[2] the right-hand side
  ({}) instanceof { [Symbol.hasInstance]: () => true }true
  ({}) instanceof {}                                TypeError 「Right-hand side of 'instanceof' is not callable」
  ({}) instanceof { [Symbol.hasInstance]: 1 }       TypeError 「number 1 is not a function」
  ({}) instanceof 1                                 TypeError 「Right-hand side of 'instanceof' is not an object」

[3] Function.prototype[Symbol.hasInstance] -- its descriptor
  descriptor                                        {"value":"fn","writable":false,"enumerable":false,"configurable":false}

[4] putting a hasInstance on a plain function F
  sloppy  F[Symbol.hasInstance] = () => true        no throw
    then ({}) instanceof F                          false
    then hasOwn(F, Symbol.hasInstance)              false
  strict  F[Symbol.hasInstance] = () => true        TypeError 「Cannot assign to read only property 'Symbol(Symbol.hasInstance)' of function 'function F() {}'」
  defineProperty(F, Symbol.hasInstance, ...)        no throw
    then ({}) instanceof F                          true

[5] the default path for comparison -- Function.prototype[Symbol.hasInstance].call
  Function.prototype[@@hasInstance].call(A, a)      true
  Function.prototype[@@hasInstance].call(A, {})     false
```

- ★★ **`[1]` — 메서드는 좌변(`4`·`3`)을 그대로 받고**, 돌려준 `"yes"`·`0` 은 **`true`·`false` 로 접힌다**(`typeof` 가 `boolean`). ③의 `ToBoolean` 이다.
- ★ **`[2]` — 우변은 클래스일 필요가 없다.** `hasInstance` 를 가진 **평범한 객체**도 우변이 된다. 없으면 `not callable`, 값이 `1` 이면 `number 1 is not a function`, 우변이 원시값이면 `not an object` — **세 문구가 ①·②·④ 에 하나씩** 대응한다.
- ★★★ **`[4]` — 보통 함수 `F` 에 대입으로 `hasInstance` 를 달면 비엄격은 조용히 무시되고 엄격은 `TypeError` 다.**
  이유는 `[3]` 한 줄이다 — `Function.prototype[Symbol.hasInstance]` 가 **`writable: false`**.
  15편의 「대입은 체인 위의 **읽기 전용** 프로퍼티에 막힌다」가 **심볼 키에서 그대로** 선다. `hasOwn` 이 `false` 인 것이 「아무것도 안 생겼다」의 증거다.
  ★ **`defineProperty` 는 체인을 안 보므로** 된다 — 그 뒤 `({}) instanceof F` 가 `true` 다. `class` 의 `static [Symbol.hasInstance]()` 가 되는 것도 **정의**이지 대입이 아니라서다.
- ★ **`[5]` — 기본 경로는 이름 붙은 메서드로 직접 부를 수 있다.** `Function.prototype[Symbol.hasInstance].call(A, a)` 가 `instanceof` 와 같은 답이다.

#### (5-b) `Symbol.species` — 어느 메서드가 읽나

17편은 `extends Array` 의 `map`·`filter`·`slice`·`from` 결과가 자식 클래스라는 것과, species 를 `Array` 로 돌리는 법까지 보였다.
여기서는 **species getter 에 로그를 심어** 메서드 14가지가 **그 키를 읽나**를 센다.

```js
// js20b-22f-species.js
// Symbol.species -- 어느 메서드가 그것을 읽나. 17편은 map/filter/slice/from 의 결과 생성자까지 봤다.
// 여기서는 species getter 에 로그를 심어 메서드마다 읽었나를 센다(ES2023 복사 메서드 포함).
const L = [];
class Tracked extends Array {
  static get [Symbol.species]() { L.push("species"); return Array; }
}
const t = Tracked.from([3, 1, 2]);
const methods = [
  ["map", (a) => a.map((x) => x)],
  ["filter", (a) => a.filter(() => true)],
  ["slice", (a) => a.slice()],
  ["splice", (a) => a.splice(0, 0)],
  ["concat", (a) => a.concat([])],
  ["flat", (a) => a.flat()],
  ["flatMap", (a) => a.flatMap((x) => [x])],
  ["toSorted", (a) => a.toSorted()],
  ["toReversed", (a) => a.toReversed()],
  ["with", (a) => a.with(0, 9)],
  ["toSpliced", (a) => a.toSpliced(0, 0)],
  ["Array.from(a)", (a) => Array.from(a)],
  ["[...a]", (a) => [...a]],
  ["sort", (a) => a.sort()],
];
console.log("[1] method          species read?   result constructor");
let read = 0, total = 0;
for (const [label, f] of methods) {
  L.length = 0;
  let r;
  try { r = f(Tracked.from(t)).constructor.name; } catch (e) { r = e.constructor.name + " 「" + e.message + "」"; }
  total++; if (L.length) read++;
  console.log("  " + label.padEnd(18) + (L.length ? "read x" + L.length : "-").padEnd(16) + r);
}
console.log("methods that read species " + read + " / " + total);

console.log("");
console.log("[2] species values other than a constructor");
const withSpecies = (v) => { class S extends Array { static get [Symbol.species]() { return v; } } return S.from([1, 2]); };
for (const [label, v] of [["undefined", undefined], ["null", null], ["42", 42], ["function returning {}", function () { return {}; }]]) {
  let r;
  try { const m = withSpecies(v).map((x) => x); r = (m.constructor && m.constructor.name) + " " + JSON.stringify(m); } catch (e) { r = e.constructor.name + " 「" + e.message + "」"; }
  console.log("  species = " + label.padEnd(20) + r);
}

console.log("");
console.log("[3] Promise.prototype.then and species");
const P = [];
class TP extends Promise { static get [Symbol.species]() { P.push("species"); return Promise; } }
const tp = TP.resolve(1);
const th = tp.then((x) => x);
console.log("  tp.then(...) constructor " + th.constructor.name + "   species reads " + P.length);
P.length = 0;
const fin = tp.finally(() => {});
console.log("  tp.finally(...) constructor " + fin.constructor.name + "   species reads " + P.length);
```
```text
===== node20 js20b-22f-species.js (exit=0) =====
[1] method          species read?   result constructor
  map               read x1         Array
  filter            read x1         Array
  slice             read x1         Array
  splice            read x1         Array
  concat            read x1         Array
  flat              read x1         Array
  flatMap           read x1         Array
  toSorted          -               Array
  toReversed        -               Array
  with              -               Array
  toSpliced         -               Array
  Array.from(a)     -               Array
  [...a]            -               Array
  sort              -               Tracked
methods that read species 7 / 14

[2] species values other than a constructor
  species = undefined           Array [1,2]
  species = null                Array [1,2]
  species = 42                  TypeError 「object.constructor[Symbol.species] is not a constructor」
  species = function returning {}Object {"0":1,"1":2}

[3] Promise.prototype.then and species
  tp.then(...) constructor Promise   species reads 1
  tp.finally(...) constructor Promise   species reads 2
```

```text
   새 배열을 만드는 메서드                  species 를 읽나
   ──────────────────────────────────────  ─────────────────────
   map · filter · slice · splice · concat   읽는다 (ArraySpeciesCreate)
   flat · flatMap                           읽는다
   toSorted · toReversed · with · toSpliced 안 읽는다 -- 늘 Array (ES2023)
   Array.from(a) · [...a]                   안 읽는다 -- 생성자는 호출한 쪽(Array)
   sort                                     새 배열을 안 만든다 -- 원본(Tracked)

   ★ 7 / 14 -- 「새 배열을 돌려주는 메서드는 species 를 따른다」는 절반만 맞다
```

- ★★★ **집계 줄 `7 / 14`.** ES2015 계열의 일곱은 species 를 **정확히 한 번** 읽고, **ES2023 복사 메서드 넷은 한 번도 안 읽는다** — 늘 `Array` 다.
  ★ **이 줄은 node18 에서 다르다** — 네 메서드가 **없어서** `TypeError 「a.toSorted is not a function」` 이다(판이 갈린 블록, 실행 검증 표).
- ★★ **`[2]` — species 가 `undefined`·`null` 이면 `Array`** 로 돌아간다(`ArraySpeciesCreate`: "If C is null, set C to undefined." → `ArrayCreate`).
  **`42` 면 `TypeError`**, **아무 객체나 돌려주는 함수면 결과가 배열이 아니다**(`Object {"0":1,"1":2}`) — 명세 문장 그대로 "It does not enforce that the constructor function returns an Array."
- ★ **`[3]` — `Promise` 도 species 를 읽는다.** `then` 은 한 번, `finally` 는 **두 번**(`finally` 가 species 를 읽고, 안에서 `then` 을 불러 또 읽는다).

#### (5-c) `Symbol.iterator` · `isConcatSpreadable` · `match` · `unscopables`

```js
// js20b-22g-other-hooks.js
// 잘 알려진 심볼 넷 -- 값 하나를 바꾸면 어느 언어 동작·내장 함수가 따라 바뀌나.
// Symbol.iterator(19편) · Symbol.isConcatSpreadable · Symbol.match · Symbol.unscopables
const row = (label, v) => console.log("  " + label.padEnd(50) + v);
const attempt = (label, run) => {
  let r;
  try { r = JSON.stringify(run()); } catch (e) { r = e.constructor.name + " 「" + e.message + "」"; }
  row(label, r);
};

console.log("[1] an array whose own Symbol.iterator yields 'x' once");
const arr = [1, 2, 3];
arr[Symbol.iterator] = function* () { yield "x"; };
attempt("[...arr]", () => [...arr]);
attempt("Array.from(arr)", () => Array.from(arr));
attempt("const [a, b] = arr", () => { const [a, b] = arr; return [a, b ?? "<undefined>"]; });
attempt("for-of collects", () => { const r = []; for (const v of arr) r.push(v); return r; });
attempt("arr.map(v => v)", () => arr.map((v) => v));
attempt("arr.join('')", () => arr.join(""));
attempt("Math.max.apply(null, arr)", () => Math.max.apply(null, arr));
attempt("JSON.stringify(arr)", () => arr);

console.log("");
console.log("[2] the same array with Symbol.iterator set to undefined");
arr[Symbol.iterator] = undefined;
attempt("[...arr]", () => [...arr]);
attempt("Array.from(arr)", () => Array.from(arr));
attempt("for-of", () => { for (const v of arr) {} return "ran"; });
attempt("arr.map(v => v)", () => arr.map((v) => v));

console.log("");
console.log("[3] Symbol.isConcatSpreadable");
attempt("[0].concat([1, 2])", () => [0].concat([1, 2]));
attempt("[0].concat(array with flag false)", () => [0].concat(Object.assign([1, 2], { [Symbol.isConcatSpreadable]: false })).length);
attempt("[0].concat({0:'a', length:1})", () => [0].concat({ 0: "a", length: 1 }).length);
attempt("[0].concat({0:'a', length:1, flag true})", () => [0].concat({ 0: "a", length: 1, [Symbol.isConcatSpreadable]: true }));

console.log("");
console.log("[4] Symbol.match -- what String methods decide is a RegExp");
attempt("'/a/b'.startsWith(/a/)", () => "/a/b".startsWith(/a/));
attempt("re[Symbol.match] = false; '/a/b'.startsWith(re)", () => { const re = /a/; re[Symbol.match] = false; return "/a/b".startsWith(re); });
attempt("'xa'.includes({ [Symbol.match]: true })", () => "xa".includes({ [Symbol.match]: true }));

console.log("");
console.log("[5] Symbol.unscopables on Array.prototype -- its keys");
row("keys", JSON.stringify(Object.keys(Array.prototype[Symbol.unscopables])));
row("prototype of that object", String(Object.getPrototypeOf(Array.prototype[Symbol.unscopables])));
const keys = "outer keys";
let seen;
with ([1, 2]) { seen = [typeof keys, typeof length === "number" ? "length " + length : "?"]; }
row("sloppy: with ([1, 2]) { keys / length }", JSON.stringify(seen));
attempt("strict: compile a with statement", () => { new Function('"use strict"; with ({}) {}'); return "compiled"; });
```
```text
===== node20 js20b-22g-other-hooks.js (exit=0) =====
[1] an array whose own Symbol.iterator yields 'x' once
  [...arr]                                          ["x"]
  Array.from(arr)                                   ["x"]
  const [a, b] = arr                                ["x","<undefined>"]
  for-of collects                                   ["x"]
  arr.map(v => v)                                   [1,2,3]
  arr.join('')                                      "123"
  Math.max.apply(null, arr)                         3
  JSON.stringify(arr)                               [1,2,3]

[2] the same array with Symbol.iterator set to undefined
  [...arr]                                          TypeError 「arr is not iterable」
  Array.from(arr)                                   [1,2,3]
  for-of                                            TypeError 「arr is not iterable」
  arr.map(v => v)                                   [1,2,3]

[3] Symbol.isConcatSpreadable
  [0].concat([1, 2])                                [0,1,2]
  [0].concat(array with flag false)                 2
  [0].concat({0:'a', length:1})                     2
  [0].concat({0:'a', length:1, flag true})          [0,"a"]

[4] Symbol.match -- what String methods decide is a RegExp
  '/a/b'.startsWith(/a/)                            TypeError 「First argument to String.prototype.startsWith must not be a regular expression」
  re[Symbol.match] = false; '/a/b'.startsWith(re)   true
  'xa'.includes({ [Symbol.match]: true })           TypeError 「First argument to String.prototype.includes must not be a regular expression」

[5] Symbol.unscopables on Array.prototype -- its keys
  keys                                              ["at","copyWithin","entries","fill","find","findIndex","findLast","findLastIndex","flat","flatMap","includes","keys","values","toReversed","toSorted","toSpliced"]
  prototype of that object                          null
  sloppy: with ([1, 2]) { keys / length }           ["string","length 2"]
  strict: compile a with statement                  SyntaxError 「Strict mode code may not include a with statement」
```

- ★★★ **`[1]` — 배열 인스턴스의 `Symbol.iterator` 를 바꾸면 이터러블 소비자 넷만 따라간다.**
  스프레드·`Array.from`·구조 분해·`for...of` 는 `["x"]` 이고, `map`·`join`·`apply`·`JSON` 은 **인덱스로 읽어** `[1,2,3]` 그대로다.
  11편의 「세 자리의 문」(`apply` 는 유사 배열만, 스프레드는 이터러블만)이 **같은 배열 안에서** 갈라진 셈이다.
- ★★★ **`[2]` — `undefined` 로 지우면 `for...of`·스프레드는 `TypeError 「arr is not iterable」`, `Array.from` 은 `[1,2,3]`** 이다.
  `Array.from` 은 `GetMethod` 가 `undefined` 를 주면 **유사 배열 경로로 넘어간다** — 19편 동작 (4)의 「유사 배열에는 `for...of` 대체 경로가 없다」와 짝이 되는 줄이다.
- ★★ **`[3]` — `isConcatSpreadable`** 은 `concat` 이 인자를 **펼칠지**를 바꾼다. 배열에 `false` 를 주면 통째로 한 원소(`length` 2), 유사 배열에 `true` 를 주면 펼쳐진다(`[0,"a"]`).
- ★★ **`[4]` — `Symbol.match` 는 「이것이 정규식인가」의 판별 키**다(명세 `IsRegExp`). `startsWith(/a/)` 는 던지는데, 그 정규식의 `Symbol.match` 를 `false` 로 두면 **문자열 `"/a/"` 로 취급돼** `true` 가 된다.
  거꾸로 **평범한 객체에 `Symbol.match: true`** 만 붙여도 `includes` 가 「정규식을 주지 마라」로 던진다. ★ **브랜드 태그와 같은 꼴** — 판별이 슬롯이 아니라 **키 하나**에 걸려 있다.
- ★ **`[5]` — `Symbol.unscopables`** 는 `with` 문이 **어느 이름을 객체에서 찾지 말지**를 정한다. `with ([1, 2])` 안에서 `keys` 는 **바깥 변수**(`"string"`)를, `length` 는 배열의 것(`2`)을 읽었다.
  ★ **그 `with` 는 엄격 모드에서 `SyntaxError 「Strict mode code may not include a with statement」`** — 모듈·`class` 몸통은 늘 엄격이므로 **현대 코드에서 이 심볼이 일할 자리는 거의 없다.** 창 표에서 「반쯤 부적용」으로 둔 이유다.

### (6) ★★ `Symbol.for` 전역 레지스트리 — 그리고 약한 키가 될 수 있나

**언제 쓰나** — **여러 모듈·여러 realm 이 같은 심볼을 공유**해야 할 때(그리고 그 대가).

```js
// js20b-22h-registry.js
// Symbol.for 전역 레지스트리 대 Symbol() -- 같음 · keyFor · 잘 알려진 심볼 · 약한 참조의 키가 될 수 있나.
const row = (label, v) => console.log("  " + label.padEnd(52) + v);
const attempt = (label, run) => {
  let r;
  try { r = String(run()); } catch (e) { r = e.constructor.name + " 「" + e.message + "」"; }
  row(label, r);
};

console.log("[1] same description, three ways");
attempt("Symbol.for('app') === Symbol.for('app')", () => Symbol.for("app") === Symbol.for("app"));
attempt("Symbol('app') === Symbol('app')", () => Symbol("app") === Symbol("app"));
attempt("Symbol.for('app') === Symbol('app')", () => Symbol.for("app") === Symbol("app"));
attempt("Symbol.for('app').description", () => Symbol.for("app").description);

console.log("");
console.log("[2] Symbol.keyFor");
attempt("Symbol.keyFor(Symbol.for('app'))", () => Symbol.keyFor(Symbol.for("app")));
attempt("Symbol.keyFor(Symbol('app'))", () => Symbol.keyFor(Symbol("app")));
attempt("Symbol.keyFor(Symbol.iterator)", () => Symbol.keyFor(Symbol.iterator));
attempt("Symbol.keyFor('app')", () => Symbol.keyFor("app"));
attempt("Symbol.iterator === Symbol.for('Symbol.iterator')", () => Symbol.iterator === Symbol.for("Symbol.iterator"));

console.log("");
console.log("[3] across realms -- a fresh vm context (node:vm)");
const vm = require("node:vm");
const other = vm.runInNewContext("({ reg: Symbol.for('app'), it: Symbol.iterator, plain: Symbol('app') })");
attempt("other.reg === Symbol.for('app')", () => other.reg === Symbol.for("app"));
attempt("other.it === Symbol.iterator", () => other.it === Symbol.iterator);
attempt("other.plain === Symbol('app')", () => other.plain === Symbol("app"));

console.log("");
console.log("[4] as a WeakMap key / WeakRef target");
const kinds = [["Symbol('k')", Symbol("k")], ["Symbol.for('k')", Symbol.for("k")], ["Symbol.iterator", Symbol.iterator]];
let ok = 0;
for (const [label, s] of kinds) {
  attempt("new WeakMap().set(" + label + ", 1)", () => { new WeakMap().set(s, 1); ok++; return "ok"; });
  attempt("new WeakRef(" + label + ")", () => { new WeakRef(s); return "ok"; });
}
console.log("");
console.log("symbol kinds accepted as a WeakMap key " + ok + " / " + kinds.length);
```
```text
===== node20 js20b-22h-registry.js (exit=0) =====
[1] same description, three ways
  Symbol.for('app') === Symbol.for('app')             true
  Symbol('app') === Symbol('app')                     false
  Symbol.for('app') === Symbol('app')                 false
  Symbol.for('app').description                       app

[2] Symbol.keyFor
  Symbol.keyFor(Symbol.for('app'))                    app
  Symbol.keyFor(Symbol('app'))                        undefined
  Symbol.keyFor(Symbol.iterator)                      undefined
  Symbol.keyFor('app')                                TypeError 「app is not a symbol」
  Symbol.iterator === Symbol.for('Symbol.iterator')   false

[3] across realms -- a fresh vm context (node:vm)
  other.reg === Symbol.for('app')                     true
  other.it === Symbol.iterator                        true
  other.plain === Symbol('app')                       false

[4] as a WeakMap key / WeakRef target
  new WeakMap().set(Symbol('k'), 1)                   ok
  new WeakRef(Symbol('k'))                            ok
  new WeakMap().set(Symbol.for('k'), 1)               TypeError 「Invalid value used as weak map key」
  new WeakRef(Symbol.for('k'))                        TypeError 「WeakRef: invalid target」
  new WeakMap().set(Symbol.iterator, 1)               ok
  new WeakRef(Symbol.iterator)                        ok

symbol kinds accepted as a WeakMap key 2 / 3
```

```text
   Symbol("app")        매번 새 값           keyFor -> undefined     약한 키  ○ (ES2023+)
   Symbol.for("app")    장부에서 찾는다      keyFor -> "app"         약한 키  ✕ -- 장부가 영원히 쥐고 있다
   Symbol.iterator      Symbol 에 붙은 값    keyFor -> undefined     약한 키  ○ (명세: 그래도 허용한다)

   CanBeHeldWeakly(v)  =  v 가 객체  이거나  (v 가 심볼 ∧ KeyForSymbol(v) 가 undefined)
```

- ★★★ **`[1]` — 설명이 같아도 `Symbol()` 끼리는 다르고, `Symbol.for` 끼리는 같다.** `Symbol.for` 와 `Symbol()` 도 다르다 — **장부 밖의 심볼은 장부의 것과 영영 만나지 않는다.**
- ★★ **`[2]` — `keyFor` 는 장부 심볼에만 이름을 돌려준다.** 잘 알려진 심볼도 `undefined` — **`Symbol.iterator` 는 장부에 없다**(`Symbol.for('Symbol.iterator')` 와 다르다).
  심볼이 아닌 것을 넣으면 `TypeError 「app is not a symbol」`.
- ★★ **`[3]` — `node:vm` 의 새 realm 에서 만든 `Symbol.for('app')` 도, 거기서 읽은 `Symbol.iterator` 도 이쪽 것과 `===`** 이고, `Symbol('app')` 은 아니다.
  ★ **창을 바꿔 물은 자리다**(제5의 상태) — 브라우저의 iframe 대신 Node 호스트의 `vm` 으로 물었다. `vm` 이 만든 것이 명세의 realm 과 같은 것인지는 **이 문서가 확인하지 않았다.**
- ★★★ **`[4]` — 집계 줄이 node20 은 `2 / 3`, node18 은 `0 / 3`** 이다. **판이 갈린 블록**이다(ES2023 이 node18 에 없다 — 판별 블록의 `symbols as WeakMap keys` 줄과 같다).
  node20 에서 **장부 심볼만 거절된다**(`Invalid value used as weak map key`). 명세 `CanBeHeldWeakly` 의 둘째 줄 그대로이고, 그 note 가 이유를 적는다 —
  "A Symbol value produced by Symbol.for, unlike other Symbol values, does not have language identity and is unsuitable for use as a weak reference."
  **누구나 `Symbol.for("k")` 로 다시 만들 수 있으니 「더 이상 아무도 못 가리킨다」가 성립하지 않는다**는 뜻이다. 수명의 의미 자체는 23편이 잇는다.
  ★ **잘 알려진 심볼은 허용된다** — 명세 note 는 "likely to never be collected, but are nonetheless treated as" 약한 대상으로 적는다.

node18 판 — 다른 곳은 한 글자도 같고 `[4]` 만 갈린다.

```text
===== node18 js20b-22h-registry.js (exit=0) =====
[1] same description, three ways
  Symbol.for('app') === Symbol.for('app')             true
  Symbol('app') === Symbol('app')                     false
  Symbol.for('app') === Symbol('app')                 false
  Symbol.for('app').description                       app

[2] Symbol.keyFor
  Symbol.keyFor(Symbol.for('app'))                    app
  Symbol.keyFor(Symbol('app'))                        undefined
  Symbol.keyFor(Symbol.iterator)                      undefined
  Symbol.keyFor('app')                                TypeError 「app is not a symbol」
  Symbol.iterator === Symbol.for('Symbol.iterator')   false

[3] across realms -- a fresh vm context (node:vm)
  other.reg === Symbol.for('app')                     true
  other.it === Symbol.iterator                        true
  other.plain === Symbol('app')                       false

[4] as a WeakMap key / WeakRef target
  new WeakMap().set(Symbol('k'), 1)                   TypeError 「Invalid value used as weak map key」
  new WeakRef(Symbol('k'))                            TypeError 「WeakRef: target must be an object」
  new WeakMap().set(Symbol.for('k'), 1)               TypeError 「Invalid value used as weak map key」
  new WeakRef(Symbol.for('k'))                        TypeError 「WeakRef: target must be an object」
  new WeakMap().set(Symbol.iterator, 1)               TypeError 「Invalid value used as weak map key」
  new WeakRef(Symbol.iterator)                        TypeError 「WeakRef: target must be an object」

symbol kinds accepted as a WeakMap key 0 / 3
```

## 문법 — 형태와 규칙

| 쓴 꼴 | 무엇 | 어디에 단다 |
|---|---|---|
| `const k = Symbol("k")` | 새 심볼 — `new Symbol()` 은 `TypeError` | — |
| `{ [k]: 1 }` · `o[k]` | 심볼 키 쓰기·읽기 — `o.k` 는 문자열 키 `"k"` | 객체 |
| `k.description` | 메모 문자열(ES2019) | — |
| `Symbol.for("app")` · `Symbol.keyFor(s)` | 전역 레지스트리 | — |
| `static [Symbol.hasInstance](v) { … }` | `instanceof` 를 바꾼다 | **생성자** |
| `static get [Symbol.species]() { … }` | `map`·`filter` 가 쓸 생성자 | **생성자** |
| `{ [Symbol.toPrimitive](hint) { … } }` | 원시값 변환을 가로챈다 | 인스턴스 또는 프로토타입 |
| `{ [Symbol.toStringTag]: "X" }` | `[object X]` 의 X — 문자열일 때만 | 인스턴스 또는 프로토타입 |
| `o[Symbol.iterator] = function* () { … }` | 이터러블(19편) | 인스턴스 또는 프로토타입 |

★ 이 표의 꼴은 전부 동작 절의 캡처 소스(22a · 22b · 22c · 22d · 22e · 22f · 22g · 22h) 안에 실제로 쓰여 돌아갔다 — 표는 그 꼴을 모은 것이다.

- **심볼 키는 대괄호로만** 쓴다. `o.k` 는 문자열 키 `"k"` 다.
- **`static [Symbol.hasInstance]`·`static get [Symbol.species]`** 는 **생성자**에, `toPrimitive`·`toStringTag`·`iterator` 는 **인스턴스(프로토타입)** 에 단다 — 언어가 **어디서 읽는지**가 다르다.
- **`toPrimitive` 는 원시값을 돌려줘야 한다.** 객체면 `TypeError`, `null`/`undefined` 로 두면 「없음」.
- **`toStringTag` 는 문자열일 때만** 효력이 있다.
- **대입으로 못 다는 자리가 있다** — `Function.prototype[Symbol.hasInstance]`·`Date.prototype[Symbol.toPrimitive]` 는 `writable: false` 라서 보통 함수·`Date` 인스턴스에 **대입하면 막힌다.** `defineProperty` 나 `class` 정의를 쓴다.

## 어디서 틀리나

### (1) ★★★ 「심볼 키는 비공개다」

`Object.keys`·`for...in`·`JSON.stringify` 에 안 보여서 그렇게 믿는다. 격자에서 **`Reflect.ownKeys`·스프레드·`Object.assign`·`hasOwn` 은 심볼을 본다** — 스프레드 한 번이면 복사된다.
비공개가 필요하면 `#필드`(16편)다. **심볼은 「이름 충돌 방지」이지 「숨김」이 아니다.**

### (2) ★★★ 「`+` 는 문자열 연산자니까 `toPrimitive` 가 `"string"` 을 받는다」

`x + ''` 는 **`"default"`** 를 받는다. `"string"` 을 원하면 **템플릿 리터럴이나 `String(x)`** 다.
`toPrimitive` 에서 `default` 를 `string` 처럼 처리할지는 **작성자가 고르는 것**이고, 내장 객체 중 그렇게 고른 것은 **`Date` 하나**다.

### (3) ★★★ 「명시적 변환은 심볼에도 된다」

`String(s)` 은 되지만 **`Number(s)` 는 던진다.** 문자열 쪽에만 `String` 함수의 샛길이 있다. `` `${s}` ``·`s + ''`·`[s].join()` 은 전부 던진다.
★ 로그 문자열을 만드는 헬퍼가 키를 템플릿 리터럴로 찍으면 **심볼 키를 만나는 순간 로그 자체가 예외를 낸다.**

### (4) ★★★ `Object.prototype.toString.call` 로 타입을 판별한다

`Symbol.toStringTag` 하나로 **위조도 은폐도 된다**(`7 / 7`). 배열이면 `Array.isArray`, 나머지는 **메서드를 `call` 해 슬롯을 두드리는** 쪽이 정본이다.

### (5) ★★ `JSON.stringify` 가 심볼을 「문자열로 바꿔」 줄 거라 믿는다

키든 값이든 **지운다**(배열 안의 값은 `null`). 에러도 안 난다 — **조용히 사라진다.**

### (6) ★★ 보통 함수에 `F[Symbol.hasInstance] = …` 를 대입한다

비엄격에서는 **아무 일도 안 일어나고 에러도 없다**(`hasOwn` 이 `false`). 물려받은 `writable: false` 가 막는다. `defineProperty` 나 `class` 의 `static` 을 쓴다.

### (7) ★★ 「`Array` 하위 클래스의 새 배열은 전부 하위 클래스다」

`map`·`filter` 는 그렇지만 **`toSorted`·`toReversed`·`with`·`toSpliced` 는 늘 `Array`** 다(species 를 안 읽는다). 스프레드와 `Array.from(a)` 도 `Array` 다.

### (8) ★★ `Symbol.for` 심볼을 `WeakMap` 키로 쓴다

node20 에서 **`TypeError`** 다. 약한 키가 될 수 있는 심볼은 **장부 밖의 것**뿐이고, 그것도 **node18 에서는 전부 안 된다**(ES2023).

### (9) ★ `Symbol.iterator` 를 지우면 「배열처럼 쓰는 모든 것」이 깨진다고 믿는다

깨지는 것은 **이터러블 소비자**(`for...of`·스프레드·구조 분해)뿐이다. `map`·`join`·`apply` 는 멀쩡하고, **`Array.from` 은 유사 배열 경로로 우회한다.**

## 구현 세부사항 대 언어 보장

### 명세 보장 — 어느 엔진에서도 같아야 하는 것

- **`Symbol()` 이 매번 다른 값인 것 · `new Symbol` 이 `TypeError` 인 것 · `description` 이 `undefined` 와 `""` 를 가르는 것.**
- **`String(sym)` 만 되고 `ToString`·`ToNumber` 를 부르는 자리는 전부 `TypeError`** 인 것(`String ( value )` · `SymbolDescriptiveString`).
- **심볼 키가 `for...in`·`Object.keys`·`JSON.stringify`·`getOwnPropertyNames` 에 안 나오고 `Reflect.ownKeys`·스프레드·`assign` 에는 나오는 것 · 심볼 키가 own 키 순서의 끝인 것**(13편).
- **hint 가 `"default"`/`"number"`/`"string"` 중 무엇으로 오나** — `ToPrimitive` 를 부르는 쪽이 원하는 타입을 **명세에 적어 두었다.** `null`/`undefined` 는 「없음」, 객체 결과는 `TypeError`.
- **`Date` 가 `default` 를 `string` 처럼 다루는 것**(명세 문장).
- **`instanceof` 가 `hasInstance` 를 먼저 보고 결과를 `ToBoolean` 하는 것 · `Function.prototype[Symbol.hasInstance]` 가 `writable: false` 인 것.**
- **`Object.prototype.toString` 이 슬롯 태그를 `Symbol.toStringTag` 문자열로 덮는 것.**
- **`ArraySpeciesCreate` 를 쓰는 메서드와 안 쓰는 메서드의 구분 · species 가 `null`/`undefined` 면 `Array`.**
- **`Symbol.for` 가 같은 문자열에 같은 심볼을 주는 것 · 장부 심볼이 약한 키가 될 수 없는 것**(ES2023 `CanBeHeldWeakly`).

### 엔진(V8) 구현 · 이 판의 관찰

- **예외 문구 전부** — `Cannot convert a Symbol value to a string` · `Symbol is not a constructor` · `Right-hand side of 'instanceof' is not callable` ·
  `Invalid value used as weak map key` · `WeakRef: invalid target`(node20) / `WeakRef: target must be an object`(node18) 등. **종류만 명세가 정한다.**
- **`Array.prototype[Symbol.unscopables]` 객체의 키 순서** — 두 판이 다르게 찍었다(두 판 대조기).
- **node18 에 ES2023 기능(배열 복사 메서드 · 심볼 약한 키)이 없는 것** — 그 판의 사정이다.

### 호스트가 정하는 것 — ECMA-262 밖

- **`node:vm`**(동작 (6) `[3]`) · **`structuredClone`** — 이 문서는 전자만 썼다.
- **`Symbol.dispose`·`Symbol.asyncDispose`** 가 node18·20 에 있는 것 — ES2026 본문에는 그 이름이 **없다**(아래 더 들어가면). 누가 붙였는지(엔진인가 호스트인가)는 **이 문서가 확인하지 않았다.**

### 그래서 이렇게 적으면 틀린다

- 「심볼 키는 비공개다」 — 틀린다. **이름 충돌 방지**일 뿐이다.
- 「명시적 변환은 심볼에도 된다」 — 틀린다. **`String()` 만** 된다.
- 「`+` 는 hint `string` 을 준다」 — 틀린다. **`default`** 다.
- 「`[object Array]` 면 배열이다」 — 틀린다. **태그는 자칭**이다.
- 「`WeakMap` 키는 객체만 된다」 — **판에 따라** 틀린다(ES2023 부터 장부 밖 심볼도 된다 · node18 에서는 맞는 말이다).

## 언제 쓰고 언제 안 쓰나

- **쓴다** — 라이브러리가 **사용자 객체에 메타데이터를 붙일 때**(문자열 키와 안 겹친다) · **언어 동작에 끼어들 때**(이터러블 · `toPrimitive` · `toStringTag`).
- **쓴다** — 모듈·realm 을 넘어 **같은 키를 공유해야 하면** `Symbol.for`. 대신 **약한 키가 될 수 없고**, 이름만 알면 누구나 같은 키를 만든다.
- **안 쓴다** — **숨기려고.** 비공개는 `#필드`다.
- **안 쓴다** — **JSON 으로 나갈 데이터의 키로.** 조용히 사라진다.
- **조심해서 쓴다** — `Symbol.hasInstance`·`Symbol.toStringTag` 로 판별을 바꾸는 것. **남의 판별 코드를 속이는** 효과가 있다(동작 (4)의 `7 / 7`).
- **쓸 일이 거의 없다** — `Symbol.unscopables`(엄격 모드에 `with` 가 없다).

## 핵심 문장

1. **심볼은 만들 때마다 다른 원시값이고, 키로 쓰면 글자 이름과 겹치지 않는다** — 격자에서 글자 키와 **`6 / 10` 열이 갈린다.**
2. **심볼 키는 숨겨진 게 아니다** — `Reflect.ownKeys`·스프레드·`assign`·`hasOwn` 이 본다.
3. **잘 알려진 심볼은 「언어가 연산 도중에 읽는 키」다** — `+` 앞의 `toPrimitive`, `instanceof` 앞의 `hasInstance`, `map` 앞의 `species`.
4. **`toPrimitive` 의 hint 는 연산자가 정한다** — `+`·`==` 는 `default`, 산술·대소는 `number`, 템플릿·키·`String()` 은 `string`, `===`·`!` 는 부르지도 않는다.
5. **`Object.prototype.toString` 은 자칭이다** — `Symbol.toStringTag` 하나로 위조도 은폐도 된다.

## 관련 자료

- [19 — 이터러블 프로토콜과 `for...of`](../19-iterable-protocol-and-for-of/2-summary.md) — 그쪽은 `Symbol.iterator` 의 **호출 계약**(몇 번 읽고 언제 닫나)까지, 여기는 **그 키를 바꾸면 누가 따라가나**부터.
- [02 — 강제 변환과 `==` 대 `===`](../02-coercion-and-loose-equality/2-summary.md) — 그쪽은 `ToPrimitive` 안의 **`valueOf`/`toString` 순서**까지, 여기는 **`toPrimitive` 가 가로챌 때의 hint 전수**부터.
- [13 — 객체 리터럴과 프로퍼티](../13-object-literals-and-properties/2-summary.md) · [18 — `for...in` 과 열거](../18-for-in-and-enumeration/2-summary.md) — 그쪽은 **열거 순서·체인 순회**까지, 여기는 **심볼 줄을 늘린 own 격자**.
- [15 — 프로토타입 체인](../15-prototype-chain/2-summary.md) — 그쪽은 `instanceof` 의 **체인 순회와 `hasInstance` 로 끊기**까지, 여기는 **인자·`ToBoolean`·대입이 막히는 자리**.
- [17 — 상속과 `super`](../17-inheritance-and-super/2-summary.md) — 그쪽은 **결과 생성자**까지, 여기는 **species 를 읽는 메서드 목록**.
- [23 — `Map`·`Set` 과 약한 컬렉션](../23-map-set-and-weak-collections/2-summary.md) — 그쪽이 **약한 참조의 수명**의 정본, 여기는 **어떤 심볼이 약한 키가 될 수 있나**만.
- Python 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **32번**(컨테이너 프로토콜)과 **05번**(진릿값과 단축 평가) —
  파이썬은 언어 동작을 바꾸는 훅이 **이름(`__iter__`·`__bool__`)** 이고, JS 는 **심볼 키**다. 그리고 파이썬의 `__bool__` 에 해당하는 것이 **JS 에는 없다**(동작 (2)의 `!x` 가 `(no call)`).

## 용어 풀이

- **심볼(symbol)** — 매번 새로 만들어지는 원시값. 프로퍼티 키로 쓸 수 있다.
- **`description`** — 심볼에 붙은 메모 문자열. 정체(같음)와 무관하다. ES2019.
- **전역 심볼 레지스트리** — `Symbol.for(문자열)` 이 찾아보는 장부. 같은 문자열이면 같은 심볼. `Symbol.keyFor` 가 역으로 찾는다.
- **잘 알려진 심볼** — `Symbol.iterator` 처럼 `Symbol` 에 붙은 심볼. 명세가 「이 연산이 이 키를 읽는다」고 정해 둔 것.
- **`ToPrimitive`** — 객체를 원시값으로 바꾸는 명세의 추상 연산. `Symbol.toPrimitive` 가 있으면 그것을 hint 와 함께 부른다.
- **hint** — `ToPrimitive` 가 넘기는 `"default"`/`"number"`/`"string"`.
- **`GetMethod`** — 프로퍼티를 읽어 `undefined`/`null` 이면 「없음」, 함수가 아니면 `TypeError` 로 보는 명세의 추상 연산.
- **`InstanceofOperator`** — `instanceof` 의 명세 절차. `hasInstance` 를 먼저 본다.
- **브랜드 태그** — `Object.prototype.toString.call(v)` 이 돌려주는 `[object X]`.
- **`ArraySpeciesCreate`** — `map`·`filter` 등이 결과 배열을 만들 때 `constructor[Symbol.species]` 를 보는 명세의 추상 연산.
- **`CanBeHeldWeakly`** — 약한 키·약한 참조 대상이 될 수 있나를 가르는 명세의 추상 연산(ES2023 부터 장부 밖 심볼 포함).
- **realm** — 전역 객체와 내장 객체 한 벌. iframe·`vm` 컨텍스트가 각자 갖는다.

## 더 들어가면

**이 판의 잘 알려진 심볼 목록 — 세 판이 같다**(블록은 [3-answer.md](3-answer.md) 11번 — node20 · node18 · Chrome 151 이 **15개 한 글자도 같다**).

- ★★ **15개 중 `dispose`·`asyncDispose` 둘은 ES2026 명세 본문에 없다** — 내려받은 ES2026 본문에서 `dispose` 가 **한 번도** 안 나오고, finished proposals 표는 Explicit Resource Management 를 **2027** 로 적는다.
  그런데 **세 판 다 그 심볼을 갖고 있다.** ★★★ **「심볼이 있다」와 「문법이 있다」는 다른 질문이다** — `using` 선언은 **node 두 판에서 `SyntaxError`** 이고 **Chrome 151 만 컴파일한다.**
  이 문법의 정본은 목록의 **51번 주제**다.
- ★ **`using` 의 문구가 두 판에서 갈린다**(`Unexpected identifier` / `Unexpected identifier 'r'`) — 이 주제에서 **문구만** 갈린 블록이다.
- ★ `Symbol.iterator` 자신은 `Symbol` 에 **`writable: false` · `configurable: false`** 로 붙어 있다 — 잘 알려진 심볼은 **바꿀 수 없는 상수**다. 바꿀 수 있는 것은 **각 객체의 그 키에 무엇을 두느냐**다.

**두 판 대조기** — 이 배치의 node 탐침이 두 판에서 갈렸나를 스크립트가 센다(전문은 [3-answer.md](3-answer.md) 의 실행 검증). 이 주제의 것은 `22f`·`22g`·`22h`·`22i` 넷이고, 배치 전체의 집계 줄은 다음과 같다.

`identical 18  ·  differs 6  ·  total 24`
