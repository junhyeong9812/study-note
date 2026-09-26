# js/syntax/16 — `class` 문법: 「메서드는 프로토타입에, 필드는 인스턴스에 정의된다」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> ★★★ **이 주제의 본체는 ② 전수 격자(「어디에 붙나」)다.**
> 클래스 몸통에 적는 멤버는 **일곱 종류**(메서드 · getter · 필드 · 정적 메서드 · 정적 필드 · `static {}` 가 붙인 것 · `#private`)이고,
> 붙을 수 있는 자리는 **셋**(프로토타입 · 인스턴스 · 생성자 함수)이다.
> `#private` 를 필드·메서드·정적 셋으로 쪼개 **9행 × 3열 = 27칸**을 전수로 찍었고, 스크립트가 직접 센 끝줄이 `cells with a property: 6 / 27` 이다.
> **이 문서의 결론은 전부 그 격자와 각 자리의 own 키 목록에서 나온다.**
> ★★ 나머지 창은 격자를 떠받친다 — ① 로그가 **필드 초기자가 언제 도나**를, ④ 예외가 **함수와 무엇이 다른가**를 말한다.
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262 최신 초안](https://tc39.es/ecma262/) — 받아 둔 사본에서 grep 해 확인했다.
>   `ClassDefinitionEvaluation` · `ClassElementEvaluation` · `DefineField` · `InitializeInstanceElements` · `PrivateElementFind` · `PrivateGet`
> - [TC39 완료 제안 목록](https://github.com/tc39/proposals/blob/main/finished-proposals.md) — 필드·`#private`·`static {}`·`#x in` 이 ES2022 인 것을 가릴 때
>
> ★★★ **명세 조항 번호는 인용하지 않는다.** 규칙 진술은 추상 연산 **이름**으로, **값·순서·예외 종류와 문구는 전부 실행으로** 접지했다.
>
> **실행 검증** — 이 문서의 모든 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮겨 적은 출력이 하나도 없다).
> 배너의 `node20` 은 `~/.nvm/versions/node/v20.19.6/bin/node`, 대조한 `node18` 은 기본 PATH 의 `node`(v18.19.1)다.
> ★★ **예외는 `try`/`catch` 로 받아 `e.constructor.name` 과 `e.message` 만 찍었다.** 스택트레이스는 한 줄도 없고, 표준 오류와 섞은 블록도 없다.
> ★★ **엄격 고정 블록은 `js16b-16d-define-vs-set.js` 하나다**(주석 뒤 첫 문장이 `"use strict"`). 나머지는 **파일은 비엄격, 클래스 몸통만 엄격**이다 —
> 16b 의 `[3]` 이 바로 그 차이를 잰다.
>
> **버전 — 판 경계**
>
> | 문법 | 판 |
> |---|---|
> | `class` 선언·식 · 메서드 · `get`/`set` · `static` 메서드 · `extends`·`super` | **ES2015** |
> | 공개 인스턴스 필드 · `static` 필드 · `#private` 필드·메서드·접근자 · `static {}` · `#x in obj` · `Object.hasOwn` | **ES2022** |
>
> ★ 아래 첫 블록이 두 판 모두 ES2022 클래스 문법을 받는다는 것을 `new Function` 으로 확인한다.
>
> **★★★ 이 주제가 쓰는 창 — 그리고 부적용인 창**
>
> | 창 | 이 주제에서 무엇을 보나 |
> |---|---|
> | ★★★ **② 전수 격자**(본체) | 멤버 **9행 × 자리 3열** · 각 자리의 own 키 **전체** · W/E/C 플래그 · `prototype` 유무 × `new` 가능 **5형태** |
> | ★★ **① 추상 연산에 로그 심기** | 필드 초기자·생성자 본문·`static` 부분의 **실행 순서 로그** · 부모 setter 의 **호출 로그** · `Proxy` 트랩 로그 |
> | ★★ **④ 예외의 `constructor.name` + `message`** | `new` 없는 호출 · 클래스 TDZ · 몸통의 암시적 전역 · 안쪽 이름 재대입 · 비쓰기 위 대입 · `#x` 가 없는 객체 · 클래스 밖 `#x`(`SyntaxError`) |
> | ★ **③ 브랜드 태그** | `#private` 가 있든 없든 `[object Object]` — 이 주제에서는 **차이를 못 보는 창**이다 |
> | ★★★ **창을 바꿔 물었다(제5의 상태) — `#private`** | 아래 따로 적는다 |
> | ★ **⑤ 두 판 대조기** | 이 주제의 블록은 **두 판에서 전부 identical** — 대조기 끝줄은 바로 아래 |
> | ★ **변형해 썼다 — 두 번 컴파일** | 엄격/비엄격을 두 번 컴파일하는 대신 **한 파일 안에서 클래스 몸통(엄격)과 바깥 함수(비엄격)를 나란히** 돌렸다. 엄격을 먼저, 탐침마다 전역 이름을 다르게, 끝에 `globalThis` 로 누수를 셌다 |
> | ★ **부적용 — 진단의 `(행,열)`**(18-C) | `SyntaxError` 는 있다(클래스 밖 `#x`). 그런데 묻는 것이 「**되나 안 되나**」라 종류와 문구로 끝난다. 값으로 못 가르는 결합·우선순위 같은 성질이 이 주제에 없다 — **잴 것이 없다** |
> | ★ **안 돌렸다 — 브라우저** | 이 주제는 브라우저에서 한 줄도 안 돌렸다 |
> | ★ **안 쟀다 — 성능** | 「`#private` 는 느리다」·「필드는 메모리를 더 먹는다」 같은 말을 **한 줄도 쓰지 않는다.** 안 쟀다 |
>
> ★★★ **`#private` 는 「잴 것이 없다」가 아니라 「있는데 안 보인다」다 — 그래서 창을 바꿔 물었다.**
> 값은 분명히 있다 — 클래스 안쪽의 `C.reveal(inst)` 가 `s,pm,ss` 를 돌려준다.
> 그런데 **①②③④ 창이 전부 눈이 멀었다** — `Reflect.ownKeys`·`getOwnPropertySymbols`·`JSON.stringify`·`Object.entries`·스프레드·`structuredClone`·`'#secret' in`(②),
> 브랜드 태그(③), 모든 트랩을 심은 `Proxy`(①, 트랩 로그 **0줄**), 그리고 클래스 밖에서는 **물어보는 문장 자체가 `SyntaxError`** 다(④).
> 부적용이었다면 「아무것도 없다」가 결론이어야 하는데 여기서는 **값이 돌아온다.** 그래서 「부적용」이 아니라 **제5의 상태**로 적는다 —
> **클래스 몸통 안쪽의 `#x in o` 와 `C.reveal`** 로 바꿔 물었다.
> ★ **바꾼 창이 못 보는 것** — ① **이름을 미리 알아야** 한다(목록을 뽑는 방법이 없다) · ② **그 클래스의 소스가 협조해야** 한다(`static` 메서드를 미리 심어 둬야 한다) ·
> ③ 같은 철자 `#x` 라도 **다른 클래스 몸통의 것은 못 묻는다**(동작 (5)의 `[4]`).
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 예외 **문구**(판이 오르면 바뀐다) | ★★★ **격자의 칸**(`.` 인가, `data W-C` 인가) · **own 키 목록과 그 순서** |
> | Node 스택트레이스의 절대 경로 — 한 줄도 싣지 않았다 | ★★★ **순서 로그의 번호** · setter 호출 횟수 |
> | `structuredClone` 의 동작(호스트 API) | ★★ **예외의 종류** · `true`/`false` |
>
> ★★ **이 주제의 블록에는 주소도 시간도 난수도 한 곳도 안 찍힌다.** 같은 판에서 다시 돌리면 한 글자도 안 변한다.
>
> **선행** — [15 — 프로토타입 체인](../15-prototype-chain/2-summary.md) · [14 — 프로퍼티 디스크립터와 동결](../14-property-descriptors-and-freezing/2-summary.md) ·
> [11 — 스프레드와 나머지](../11-spread-and-rest/2-summary.md) · [08 — 함수 정의 형태와 매개변수](../08-function-forms-and-parameters/2-summary.md) ·
> [07 — `this` 바인딩 네 규칙](../07-this-binding-four-rules/2-summary.md) · [05 — `var`·`let`·`const` 와 TDZ](../05-var-let-const-and-tdz/2-summary.md).
> ★★★ **15번 결론을 다시 재지 않는다.** 「읽기는 체인을 타고, 쓰기는 수신자에 내려앉는다」 · 쓰기 트랩 로그 `["C.set","B.set","A.set","C.gopd"]` ·
> 체인 위 setter 의 `this` 는 수신자라 **자식에** `_store` 가 생긴다 · `prototype` 과 `[[Prototype]]` 은 다른 칸이다 — 전부 15번에서 받아 쓴다.
> 여기서 새로 묻는 것은 **`class` 가 그 체인 위에 무엇을 어디에 얹나**다.
> **이어지는 곳** — [17 — 상속과 `super`](../17-inheritance-and-super/2-summary.md) · [18 — `for...in` 과 열거](../18-for-in-and-enumeration/2-summary.md) ·
> [목록의 **34번 주제**](../34-type-checking-idioms/) 「타입 검사 관용구」 · [목록의 **35번 주제**](../35-strict-mode/) 「엄격 모드」 · [목록의 **45번 주제**](../45-proxy/) 「`Proxy`」
>
> ★★ **경계 — `extends`·`super`·내장 객체 상속·`new.target` 은 17번이 정본이다.** 여기서 `extends` 는 **필드 순서를 재려고** 두 번 쓸 뿐이다.
> ★★ **경계 — 체인 자체는 15번이 정본이다.** 여기서는 **체인의 어느 칸에 무엇이 붙나**까지다.
> ★★ **경계 — `for...in` 과 열거 규칙은 18번이 정본이다.** 여기서는 **클래스 메서드가 비열거라는 사실 하나**가 무엇을 바꾸나까지다.
> ★ **경계 — `Proxy` 트랩 계약은 45번이 정본이다.** 여기서는 **`#x` 가 트랩에 안 걸린다**는 한 줄만 본다.

```sh
# js16b-versions.sh
#!/usr/bin/env bash
# 이 문서의 모든 출력이 어느 판에서 나왔는지 -- 그리고 ES2022 클래스 문법이 두 판에 다 있는지.
set -u -o pipefail
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
for n in "$N18" "$N20"; do
  "$n" -e 'const v = process.versions;
    const has = (src) => { try { new Function(src); return "yes"; } catch (e) { return "no"; } };
    console.log("node " + v.node + "  v8 " + v.v8 +
      "  fields " + has("class A { x = 1; static y = 2 }") +
      "  #private " + has("class A { #x; m(o) { return #x in o } }") +
      "  static{} " + has("class A { static { } }") +
      "  hasOwn " + typeof Object.hasOwn +
      "  errorCause " + String(new Error("m", { cause: 1 }).cause === 1));'
done
```

```text
===== ./js16b-versions.sh (exit=0) =====
node 18.19.1  v8 10.2.154.26-node.28  fields yes  #private yes  static{} yes  hasOwn function  errorCause true
node 20.19.6  v8 11.3.244.8-node.33  fields yes  #private yes  static{} yes  hasOwn function  errorCause true
```

두 판 대조기의 끝줄 — 이 배치 전체 블록을 센다. 갈린 블록은 19번 주제의 것이고, **이 주제의 블록은 두 판에서 전부 identical** 이다.
`identical 22  ·  differs 1  ·  total 23`

## 한눈에 — 쉽게 말하면

**`class` 는 새 물건이 아니라 15번의 체인을 짓는 설계도다.** 설계도에 적은 줄마다 **떨어지는 방이 정해져 있다.**

- **메서드와 getter** — **공용 거실**(프로토타입)에 한 벌 둔다. 모든 인스턴스가 빌려 쓴다.
- **필드** — 인스턴스가 태어날 때마다 **자기 방**(인스턴스)에 하나씩 **새로 놓는다.** 빌리는 것이 아니다.
- **`static` 붙은 것** — **설계도 자체**(생성자 함수)에 붙는다. 인스턴스는 모른다.
- **`#private`** — 자기 방에 있긴 한데 **벽장 안**이다. 방 밖에서는 **벽장이 있다는 것조차** 안 보인다.

```text
   class 몸통에 적은 것이 떨어지는 자리 -- 셋

   │ C   (생성자 함수 = 클래스 자신)
   │   staticMethod · reveal        <- static 메서드
   │   staticField · fromBlock      <- static 필드 · static {} 가 붙인 것
   │   [벽장] #staticSecret
   │
   │   C.prototype 로 이어진다
   v
   │ C.prototype
   │   constructor · method · acc   <- 메서드 · getter  (모든 인스턴스가 같이 빌려 본다)
   ^
   │   [[Prototype]] 로 올라간다
   │
   │ new C()   (인스턴스)
   │   field                        <- 필드  (인스턴스마다 하나씩 정의된다)
   │   [벽장] #secret · #privMethod  <- 방 밖의 어떤 창에도 안 보인다
```

★★★ **이 그림이 이 주제의 전부다** — 격자 27칸 중 차는 칸이 6칸인 것도, `#private` 세 행이 전부 `.` 인 것도 이 그림 그대로다.

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 설계도 | 클래스 = 생성자 함수 | `typeof C` 가 `function` |
| 공용 거실 | `C.prototype` | `Reflect.ownKeys(C.prototype)` |
| 자기 방 | 인스턴스의 own 프로퍼티 | `Reflect.ownKeys(new C())` |
| 설계도에 붙인 메모 | `static` 멤버 | `Reflect.ownKeys(C)` |
| 벽장 | `#private` | 클래스 **안쪽**의 `#x in o` 로만 |
| 거실 가구에 붙은 「안내판에 안 올림」 표시 | 클래스 메서드의 `enumerable: false` | `Object.keys(C.prototype)` 가 `[]` |
| 방에 가구를 **들여놓기** | 필드 = 정의 | 부모 setter 가 안 불린다 |
| 방에 가구를 **주문하기** | 생성자 안 `this.x = v` = 대입 | 부모 setter 가 가져간다 |

**똑같은 구조다** — 실무에서 이게 물리는 자리는 셋이다.
「**부모에 setter 가 있는데 자식 필드가 그것을 안 부른다**」 · 「**`JSON.stringify` 에 `#private` 가 안 나온다**」 · 「**`Proxy` 로 감쌌더니 메서드가 `TypeError`**」.

> **필드(field)** — 클래스 몸통에 `x = 값` 꼴로 적어 **인스턴스마다 own 프로퍼티로 정의되는** 멤버(ES2022).\
> 예: `class C { x = 1 }` 이면 `new C()` 의 own 키가 `["x"]` 다. 메서드와 달리 프로토타입에는 없다.

> **`#private`** — 이름이 `#` 로 시작하는 멤버. **프로퍼티가 아니라** 객체에 딸린 별도의 칸이다(명세의 `[[PrivateElements]]`).\
> 예: `class C { #s = 1 }` 의 인스턴스에서 `Reflect.ownKeys` 는 `#s` 를 모른다. 클래스 밖에서 `o.#s` 를 쓰면 `SyntaxError` 다.

> **정의(define) 대 대입(set)** — 정의는 「**이 객체에 이 모양의 칸을 만든다**」, 대입은 「**값을 바꾸겠다**」다.\
> 예: 11번의 스프레드(정의)와 `Object.assign`(대입)이 대상의 setter 에서 갈렸다. 필드와 생성자 대입이 **같은 갈림길**이다.

## 이 주제가 답하려는 질문

1. **클래스 몸통의 멤버 일곱 종류는 각각 어느 자리에 붙나** — 프로토타입인가, 인스턴스인가, 생성자인가? 그리고 **`#private` 는 어디에 있나**?
2. **`class` 는 함수 위에 무엇을 더 얹나** — `typeof` 가 `function` 인데 무엇이 평범한 함수와 다른가? 필드 초기자는 **언제** 도나?
3. **필드 `x = 1` 과 생성자의 `this.x = 1` 은 같은 것인가** — 부모 프로토타입에 setter·비쓰기 프로퍼티가 있으면 무엇이 갈리나?

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 출력으로 읽는다.

### (1) ★★★ 어디에 붙나 — 27칸 전수 격자

**언제 쓰나** — 「이 멤버는 인스턴스마다 생기나, 한 벌을 같이 쓰나」를 물을 때. 추측하지 말고 **세 자리의 own 키를 전부 찍으면 끝난다.**

```js
// js16b-16a-where.js
// ★ 이 주제의 본체 -- 클래스 몸통의 멤버 일곱 종이 「어디에 붙나」를 전수로 찍는다.
// 붙을 수 있는 자리는 셋: 프로토타입(C.prototype) / 인스턴스(new C()) / 생성자 함수(C 자신).
class C {
  method() { return "m"; }
  get acc() { return "g"; }
  field = "f";
  #secret = "s";
  #privMethod() { return "pm"; }
  static staticMethod() { return "sm"; }
  static staticField = "sf";
  static #staticSecret = "ss";
  static { C.fromBlock = "set in static {}"; }
  static reveal(o) { return [o.#secret, o.#privMethod(), C.#staticSecret].join(","); }
}
const inst = new C();
const places = [["prototype", C.prototype], ["instance", inst], ["constructor", C]];
const names = ["method", "acc", "field", "staticMethod", "staticField", "fromBlock",
               "#secret", "#privMethod", "#staticSecret"];

function flags(d) {
  const kind = "get" in d || "set" in d ? "accessor" : "data";
  const w = kind === "data" ? (d.writable ? "W" : "-") : " ";
  return kind.padEnd(9) + w + (d.enumerable ? "E" : "-") + (d.configurable ? "C" : "-");
}

console.log("[1] where does each member land?   (W=writable E=enumerable C=configurable)");
console.log("member".padEnd(15) + places.map(([p]) => p.padEnd(18)).join(""));
let found = 0;
for (const n of names) {
  let row = n.padEnd(15);
  for (const [, obj] of places) {
    const d = Object.getOwnPropertyDescriptor(obj, n);
    row += (d ? flags(d) : ".").padEnd(18);
    if (d) found++;
  }
  console.log(row);
}
console.log("cells with a property: " + found + " / " + names.length * places.length);

console.log("");
console.log("[2] the whole own-key list of each place (Reflect.ownKeys sees strings AND symbols)");
for (const [p, obj] of places) console.log(p.padEnd(13) + JSON.stringify(Reflect.ownKeys(obj)));

console.log("");
console.log("[3] #private -- what does each reflection API report?");
const views = [
  ["Reflect.ownKeys(inst)", () => JSON.stringify(Reflect.ownKeys(inst))],
  ["Object.getOwnPropertySymbols(inst)", () => JSON.stringify(Object.getOwnPropertySymbols(inst))],
  ["JSON.stringify(inst)", () => JSON.stringify(inst)],
  ["Object.entries(inst)", () => JSON.stringify(Object.entries(inst))],
  ["{ ...inst }", () => JSON.stringify({ ...inst })],
  ["structuredClone(inst)", () => JSON.stringify(structuredClone(inst))],
  ["'#secret' in inst", () => String("#secret" in inst)],
  ["C.reveal(inst)  (inside the class)", () => C.reveal(inst)],
];
for (const [label, f] of views) console.log(label.padEnd(38) + f());

console.log("");
console.log("[4] enumerable flag -- class members vs object-literal and old-style members");
const lit = { method() { return 1; }, get acc() { return 2; } };
function Old() {}
Old.prototype.method = function () { return 3; };
const rows = [
  ["class C { method() {} }", C.prototype, "method"],
  ["class C { get acc() {} }", C.prototype, "acc"],
  ["class C { static staticMethod() {} }", C, "staticMethod"],
  ["class C { field = ... }", inst, "field"],
  ["class C { static staticField = ... }", C, "staticField"],
  ["{ method() {} }  (literal)", lit, "method"],
  ["{ get acc() {} }  (literal)", lit, "acc"],
  ["Old.prototype.method = function", Old.prototype, "method"],
];
for (const [label, obj, k] of rows) console.log(label.padEnd(38) + "enumerable " + Object.getOwnPropertyDescriptor(obj, k).enumerable);
console.log("Object.keys(C.prototype)              " + JSON.stringify(Object.keys(C.prototype)));
console.log("Object.keys(Old.prototype)            " + JSON.stringify(Object.keys(Old.prototype)));
```

```text
===== node20 js16b-16a-where.js (exit=0) =====
[1] where does each member land?   (W=writable E=enumerable C=configurable)
member         prototype         instance          constructor       
method         data     W-C      .                 .                 
acc            accessor  -C      .                 .                 
field          .                 data     WEC      .                 
staticMethod   .                 .                 data     W-C      
staticField    .                 .                 data     WEC      
fromBlock      .                 .                 data     WEC      
#secret        .                 .                 .                 
#privMethod    .                 .                 .                 
#staticSecret  .                 .                 .                 
cells with a property: 6 / 27

[2] the whole own-key list of each place (Reflect.ownKeys sees strings AND symbols)
prototype    ["constructor","method","acc"]
instance     ["field"]
constructor  ["length","name","prototype","staticMethod","reveal","staticField","fromBlock"]

[3] #private -- what does each reflection API report?
Reflect.ownKeys(inst)                 ["field"]
Object.getOwnPropertySymbols(inst)    []
JSON.stringify(inst)                  {"field":"f"}
Object.entries(inst)                  [["field","f"]]
{ ...inst }                           {"field":"f"}
structuredClone(inst)                 {"field":"f"}
'#secret' in inst                     false
C.reveal(inst)  (inside the class)    s,pm,ss

[4] enumerable flag -- class members vs object-literal and old-style members
class C { method() {} }               enumerable false
class C { get acc() {} }              enumerable false
class C { static staticMethod() {} }  enumerable false
class C { field = ... }               enumerable true
class C { static staticField = ... }  enumerable true
{ method() {} }  (literal)            enumerable true
{ get acc() {} }  (literal)           enumerable true
Old.prototype.method = function       enumerable true
Object.keys(C.prototype)              []
Object.keys(Old.prototype)            ["method"]
```

**격자 해설 — 한 덩어리에 한 문장.**

```text
   [1] 을 세로로 읽으면 -- 한 멤버는 한 자리에만 떨어진다

                     prototype    instance    constructor
   method              ■            .            .
   acc (getter)        ■            .            .
   field               .            ■            .
   staticMethod        .            .            ■
   staticField         .            .            ■
   fromBlock           .            .            ■
   #secret             .            .            .      <- 세 자리 어디에도 own 키가 없다
   #privMethod         .            .            .
   #staticSecret       .            .            .

   ■ 가 6칸 · 행마다 ■ 는 많아야 1칸 · #private 세 행은 0칸
```

- ★★★ **한 멤버는 한 자리에만 떨어진다** — 행마다 채워진 칸이 **많아야 하나**다. 「메서드가 인스턴스에도 복사된다」는 일은 없다.
  **메서드·getter 는 프로토타입, 필드는 인스턴스, `static` 셋은 생성자**다.
- ★★★ **`#private` 세 행은 전부 `.` 이다** — `getOwnPropertyDescriptor(obj, "#secret")` 는 **`"#secret"` 이라는 문자열 키**를 찾을 뿐이고, 그런 키는 없다.
  「없다」가 아니라 「**프로퍼티가 아니다**」가 정확하다 — `[3]` 의 마지막 줄 `C.reveal(inst)` 가 `s,pm,ss` 를 돌려준다.
- ★★ **플래그가 자리마다 다르다.**
  메서드는 `data W-C`(쓸 수 있고, **열거 안 되고**, 지울 수 있다), getter 는 `accessor -C`, 필드와 정적 필드는 `data WEC` 다.
  ★ `fromBlock` 도 `WEC` 다 — `static {}` 안의 `C.fromBlock = …` 는 **평범한 대입**이라 평범한 프로퍼티를 만든다.
- ★★★ `[2]` **각 자리의 own 키 전체**가 격자의 반대 방향 증명이다 — 격자에 없는 키가 **숨어 있지 않다.**
  프로토타입은 `["constructor","method","acc"]`, 인스턴스는 `["field"]` 한 개다.
  ★ 생성자 쪽에 `length`·`name`·`prototype` 이 먼저 있다 — **클래스도 함수**라서 함수가 갖는 세 키를 그대로 갖는다.
- ★★ **생성자의 키 순서가 소스 순서와 다르다.** 소스는 `staticMethod` → `staticField` → `static {}` → `reveal` 순인데
  own 키는 `staticMethod`·`reveal`(메서드 둘) → `staticField`·`fromBlock`(필드·블록) 순이다.
  ★ **메서드는 클래스를 평가하는 도중에 먼저 전부 붙고, 정적 필드와 `static {}` 는 그 뒤에 선언 순서대로 돈다** — 명세 `ClassDefinitionEvaluation` 의
  "For each element elementRecord of staticElements, do" 루프가 **메서드 정의가 끝난 뒤에** 있다. 키 순서가 삽입 순서라는 것은 13번이 정본이다.
- ★★★ `[3]` **바깥 창 일곱 가지가 전부 `#private` 에 눈멀었다.** 문자열 키·심볼 키·JSON·`entries`·스프레드·`structuredClone` 이 전부 `field` 하나만 보고, `'#secret' in` 은 `false` 다. 여덟째 줄(클래스 안쪽)만 값을 돌려준다.
  ★ `'#secret' in inst` 가 `false` 인 것은 **문자열 `"#secret"` 을 물었기 때문**이다 — 진짜 브랜드 검사 `#secret in inst` 는 **따옴표가 없고 클래스 안에서만** 쓸 수 있다(동작 (5)).
- ★★★ `[4]` **클래스 메서드만 비열거다.** `method`·`acc`·`staticMethod` 가 `enumerable false`,
  **같은 모양의 객체 리터럴 메서드와 옛 방식 `Old.prototype.method = function` 은 `true`** 다.
  그래서 `Object.keys(C.prototype)` 는 `[]`, `Object.keys(Old.prototype)` 는 `["method"]` 다.
  ★ 명세가 그 `false` 를 직접 넘긴다 — `ClassElementEvaluation` 이 "MethodDefinitionEvaluation of MethodDefinition with arguments obj and false" 이고 그 `false` 가 열거 가능 여부다.
  ★★ 필드와 정적 필드는 **`true`** 다 — **필드는 메서드가 아니라 데이터**라서 평범한 프로퍼티처럼 보인다. 이 차이가 `for...in` 에 무엇을 주나는 동작 (6).

**비용** — 메서드를 프로토타입에 두는 것과 필드로 두는 것의 메모리·속도 차이는 **재지 않았다.**

### (2) ★★ 클래스는 함수다 — 그런데 평범한 함수가 아니다

**언제 쓰나** — 「`typeof` 가 `function` 이면 함수처럼 쓸 수 있나」를 물을 때. **던져 보면 다섯 군데에서 다르다.**

```js
// js16b-16b-rules.js
// class 가 「함수 위에 무엇을 더 얹나」 -- 던져서 확인한다. 예외는 종류 + 문구만 찍는다.
// ★ 이 파일은 "use strict" 가 없다. 클래스 몸통만 엄격이고 바깥은 비엄격이다.
const run = (label, fn) => {
  let r;
  try { r = "-> " + String(fn()); } catch (e) { r = "-> " + e.constructor.name + " " + e.message; }
  console.log(label.padEnd(44) + r);
};

console.log("[1] typeof, and calling without new");
class K { m() { return "m"; } static s() { return "s"; } }
function F() { return "called as a plain function"; }
run("typeof class {}", () => typeof class {});
run("typeof K", () => typeof K);
run("F()   (plain function, no new)", () => F());
run("K()   (class, no new)", () => K());
run("K.call({})", () => K.call({}));
run("new K() instanceof K", () => new K() instanceof K);

console.log("");
console.log("[2] using the name before the declaration line");
run("use before `class Late {}` in the block", () => { const v = new Late(); class Late {} return v; });
run("use before `function Early() {}`", () => { const v = typeof Early; function Early() {} return v; });

console.log("");
console.log("[3] implicit globals and detached this -- inside a class body vs a plain function");
// ★ 탐침마다 전역 이름이 다르다. 엄격(클래스)을 먼저 돌린다.
class StrictProbe { leak() { leakedFromClass = 1; return "assigned"; } }
function sloppyProbe() { leakedFromFunction = 1; return "assigned"; }
run("class method: leakedFromClass = 1", () => new StrictProbe().leak());
run("plain function: leakedFromFunction = 1", () => sloppyProbe());
run("'leakedFromClass' in globalThis", () => "leakedFromClass" in globalThis);
run("'leakedFromFunction' in globalThis", () => "leakedFromFunction" in globalThis);
const leaked = ["leakedFromClass", "leakedFromFunction"].filter((n) => n in globalThis);
console.log("globals leaked by the 2 probes: " + JSON.stringify(leaked) + "  (" + leaked.length + " / 2)");
class ThisProbe { who() { return this === undefined ? "undefined" : typeof this; } }
function sloppyWho() { return this === globalThis ? "globalThis" : typeof this; }
const w = new ThisProbe().who;
run("detached class method: this is", () => w());
run("detached plain function: this is", () => sloppyWho());

console.log("");
console.log("[4] reassigning the class name from inside");
class Named { rename() { Named = 1; } }
run("Named = 1  (inside a method)", () => new Named().rename());
let Outer = class Inner { static who() { return typeof Inner; } };
run("class expression's own name, from inside", () => Outer.who());
run("typeof Inner  (from outside)", () => typeof Inner);

console.log("");
console.log("[5] has .prototype? can it be new-ed? (see topic 08)");
const forms = [
  ["class K", K],
  ["function F", F],
  ["K.prototype.m  (class method)", K.prototype.m],
  ["K.s  (static method)", K.s],
  ["() => {}", () => {}],
];
for (const [label, f] of forms) {
  let canNew;
  try { new f(); canNew = "new ok"; } catch (e) { canNew = e.constructor.name; }
  console.log(label.padEnd(32) + ("has .prototype " + ("prototype" in f)).padEnd(22) + canNew);
}
console.log("K.prototype writable?  " + Object.getOwnPropertyDescriptor(K, "prototype").writable +
            "   F.prototype writable?  " + Object.getOwnPropertyDescriptor(F, "prototype").writable);
```

```text
===== node20 js16b-16b-rules.js (exit=0) =====
[1] typeof, and calling without new
typeof class {}                             -> function
typeof K                                    -> function
F()   (plain function, no new)              -> called as a plain function
K()   (class, no new)                       -> TypeError Class constructor K cannot be invoked without 'new'
K.call({})                                  -> TypeError Class constructor K cannot be invoked without 'new'
new K() instanceof K                        -> true

[2] using the name before the declaration line
use before `class Late {}` in the block     -> ReferenceError Cannot access 'Late' before initialization
use before `function Early() {}`            -> function

[3] implicit globals and detached this -- inside a class body vs a plain function
class method: leakedFromClass = 1           -> ReferenceError leakedFromClass is not defined
plain function: leakedFromFunction = 1      -> assigned
'leakedFromClass' in globalThis             -> false
'leakedFromFunction' in globalThis          -> true
globals leaked by the 2 probes: ["leakedFromFunction"]  (1 / 2)
detached class method: this is              -> undefined
detached plain function: this is            -> globalThis

[4] reassigning the class name from inside
Named = 1  (inside a method)                -> TypeError Assignment to constant variable.
class expression's own name, from inside    -> function
typeof Inner  (from outside)                -> undefined

[5] has .prototype? can it be new-ed? (see topic 08)
class K                         has .prototype true   new ok
function F                      has .prototype true   new ok
K.prototype.m  (class method)   has .prototype false  TypeError
K.s  (static method)            has .prototype false  TypeError
() => {}                        has .prototype false  TypeError
K.prototype writable?  false   F.prototype writable?  true
```

**해설.**

- ★★★ `[1]` **`typeof class {}` 는 `function` 이다** — 그런데 **`K()` 와 `K.call({})` 가 `TypeError`** 다(`Class constructor K cannot be invoked without 'new'`).
  평범한 함수 `F()` 는 그냥 불린다. ★ **클래스는 「`new` 로만 부를 수 있는 함수」다** — `typeof` 는 호출 방식을 말해 주지 않는다.
- ★★ `[2]` **클래스 선언은 TDZ 에 들어간다** — 선언 줄 앞에서 쓰면 `ReferenceError`, 함수 선언은 `function` 이 나온다.
  ★ 이 대비는 [05번](../05-var-let-const-and-tdz/2-summary.md)의 `[5]` 가 정본이고, 여기서는 **한 줄을 다시 확인**했을 뿐이다 — `class` 는 `function` 이 아니라 `let` 쪽이다.
- ★★★ `[3]` **클래스 몸통은 엄격이고 바깥 파일은 아니다.**
  같은 파일에서 클래스 메서드의 `leakedFromClass = 1` 은 `ReferenceError`, 바깥 함수의 `leakedFromFunction = 1` 은 **조용히 전역을 만든다.**
  `globalThis` 로 세면 **2개 탐침 중 1개만 샜다**(`["leakedFromFunction"]  (1 / 2)`) — 새는 것은 **비엄격 쪽 이름뿐**이다.
  ★ 명세 문장 그대로다 — "All parts of a ClassDeclaration or a ClassExpression are strict mode code."
  ★ **엄격을 먼저 돌리고 이름을 다르게 지었다**(규칙 22). 비엄격을 먼저 돌려 같은 이름을 썼으면 엄격 쪽이 그 전역을 읽어 **0 / 2 처럼 보였을 것**이다.
- ★★★ **떼어 낸 클래스 메서드의 `this` 는 `undefined`** 다. 떼어 낸 비엄격 함수는 `globalThis` 다.
  ★ 이것은 새 규칙이 아니라 **엄격 모드의 기본 바인딩**이다 — [07번](../07-this-binding-four-rules/2-summary.md)이 정본이고,
  그쪽에 「클래스 메서드는 떼면 `this` 를 잃고, **필드에 담은 화살표는 안 잃는다**」가 이미 실측돼 있다.
- ★★ `[4]` **클래스 이름은 안쪽에서 `const` 다** — 메서드 안의 `Named = 1` 이 `TypeError`(`Assignment to constant variable.`).
  ★ 클래스 식의 이름(`class Inner`)은 **안쪽에서만** 보이고 바깥에서는 `typeof Inner` 가 `undefined` 다.
- ★★★ `[5]` **`prototype` 이 있는지와 `new` 가 되는지는 따로 논다** — 08번의 격자가 정본이다.
  클래스는 둘 다 있고, **클래스 메서드와 정적 메서드는 `prototype` 도 없고 `new` 도 `TypeError`** 다 — 리터럴의 메서드 단축과 같다.
  ★ 08번에 **반례가 둘** 있다 — 제너레이터(`prototype` 있음 · `new` 안 됨)와 bound 함수(`prototype` 없음 · `new` 됨). 그러니 「`prototype` 이 있으면 `new` 가 된다」로 외우지 마라.
- ★★ **`K.prototype` 은 쓸 수 없고 `F.prototype` 은 쓸 수 있다**(`false` 대 `true`).
  ★ 15번이 `.prototype` 을 갈아끼워 `instanceof` 를 바꿨는데, **클래스에서는 그 대입 자체가 막힌다.**
  명세 `ClassDefinitionEvaluation` 이 생성자를 만들 때 `MakeConstructor(ctorFunc, false, proto)` 를 부른다 — 그 정의 본문은 받아 둔 사본 밖이라 **인자의 뜻은 출력 쪽으로만 확인했다.**

```text
   class 가 함수 위에 얹는 것 -- 이 블록이 던져서 확인한 다섯

   typeof           function 이다                    (함수다)
   K()              TypeError 로 막힌다               (new 로만 부른다)
   선언 앞에서 쓰기   ReferenceError 로 막힌다          (TDZ -- let 쪽이다)
   몸통 안           엄격 -- 암시적 전역이 막힌다        (파일이 비엄격이어도)
   안쪽 이름         const -- 재대입이 막힌다
   K.prototype      writable false                    (갈아끼울 수 없다)
```

### (3) ★★ 필드 초기자는 언제 도나 — 순서 로그와 3열 대비

**언제 쓰나** — 생성자 본문에서 필드를 읽을 때, 그리고 **부모 생성자가 자식 필드를 읽을 때.**
★ 순서는 값으로 안 보인다. 초기자마다 **로그를 심어** 번호로 찍었다(① 창).

```js
// js16b-16c-order.js
// 필드 초기자는 언제 도나 -- 생성자 본문과의 순서를 로그로 찍는다.
// ★ C# 12편(파생 필드 초기자가 제일 먼저)·C++ 13편(기반 → 파생)과 견줄 자리다.
const L = [];
const step = (msg, v) => { L.push(msg); return v; };

console.log("[1] one class -- field initializers vs the constructor body");
class One {
  a = step("field a initializer", 1);
  constructor() {
    step("constructor body starts  (this.a is " + this.a + ", this.b is " + this.b + ")");
    this.c = 3;
  }
  b = step("field b initializer  (sees this.a = " + this.a + ")", 2);
}
L.length = 0; new One();
L.forEach((m, i) => console.log("  " + (i + 1) + ". " + m));

console.log("");
console.log("[2] base and derived -- where do the derived fields go?");
class Base {
  baseField = step("Base field initializer", "B");
  constructor() { step("Base constructor body"); }
}
class Derived extends Base {
  derivedField = step("Derived field initializer", "D");
  constructor() {
    step("Derived constructor body -- before super()");
    super();
    step("Derived constructor body -- after super()  (derivedField is " + this.derivedField + ")");
  }
}
L.length = 0; new Derived();
L.forEach((m, i) => console.log("  " + (i + 1) + ". " + m));

console.log("");
console.log("[3] static parts -- when do they run?");
L.length = 0;
step("before the class");
class S {
  static first = step("static field first", 1);
  static { step("static {} block  (this === S: " + (this === S) + ", S.first set: " + (S.first === undefined ? "no" : "yes") + ")"); }
  static second = step("static field second  (this.name is " + this.name + ")");
  inst = step("instance field initializer  (only at new S())");
}
step("after the class");
new S();
step("after new S()");
L.forEach((m, i) => console.log("  " + (i + 1) + ". " + m));
```

```text
===== node20 js16b-16c-order.js (exit=0) =====
[1] one class -- field initializers vs the constructor body
  1. field a initializer
  2. field b initializer  (sees this.a = 1)
  3. constructor body starts  (this.a is 1, this.b is 2)

[2] base and derived -- where do the derived fields go?
  1. Derived constructor body -- before super()
  2. Base field initializer
  3. Base constructor body
  4. Derived field initializer
  5. Derived constructor body -- after super()  (derivedField is D)

[3] static parts -- when do they run?
  1. before the class
  2. static field first
  3. static {} block  (this === S: true, S.first set: yes)
  4. static field second  (this.name is S)
  5. after the class
  6. instance field initializer  (only at new S())
  7. after new S()
```

**해설.**

- ★★★ `[1]` **필드 초기자가 생성자 본문보다 먼저 돈다.** 생성자 본문이 시작할 때 `this.a` 는 `1`, `this.b` 는 `2` 다.
  ★★ **`b` 는 소스에서 생성자 아래에 적혀 있는데도** 본문보다 먼저 돌았다 — 필드는 **적힌 자리가 아니라 필드끼리의 선언 순서**로 돈다(`a` → `b`).
  ★ 뒤 필드의 초기자는 **앞 필드를 이미 본다**(`sees this.a = 1`).
- ★★★ `[2]` **기반과 파생이 섞이면 다섯 단계다.**
  파생 생성자 본문의 `super()` **앞부분** → 기반 필드 → 기반 생성자 본문 → **파생 필드** → 파생 생성자 본문의 `super()` **뒷부분**.
  ★★ **파생 필드는 `super()` 가 돌아오는 순간 채워진다** — 그래서 5번 줄에서 `derivedField` 가 이미 `D` 다.
  ★ 명세 쪽 이름은 `InitializeInstanceElements` 다 — 인스턴스에 `#private` 메서드를 먼저 붙이고("PrivateMethodOrAccessorAdd(obj, method)") 필드를 선언 순서대로 `DefineField` 한다.
  **`super()` 가 무엇을 하는가 자체는 17번이 정본**이다.
- ★★★ `[3]` **`static` 필드와 `static {}` 는 클래스를 정의하는 그 순간 한 번 돈다** — `before the class` 와 `after the class` 사이에 끼어 있다.
  ★ 선언 순서 그대로다 — `static first` → `static {}` → `static second`. 블록 안에서 `this === S` 가 `true` 이고 **앞의 `S.first` 는 이미 있다.**
  ★ 인스턴스 필드는 **정의 때가 아니라 `new S()` 때** 돈다(6번 줄).

**★★★ 3열 대비 — JS 는 어느 쪽과 같은가.**
C# 과 C++ 의 순서는 C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **12번** 정답 1·2번이 이미 실측했다(C++ 쪽 기반/파생 순서도 **그 문서의 2번**이 쟀다).

| 단계 | C++ (C# 12번 정답 2번) | C# (C# 12번 정답 1번) | JS (위 `[2]`) |
|---|---|---|---|
| 1 | 기반 멤버 초기자 | ★ **파생 필드 초기자** | 파생 생성자 본문 — `super()` 앞 |
| 2 | 기반 생성자 본문 | 기반 필드 초기자 | 기반 필드 초기자 |
| 3 | ★ **파생 멤버 초기자** | 기반 생성자 본문 | 기반 생성자 본문 |
| 4 | 파생 생성자 본문 | 파생 생성자 본문 | ★ **파생 필드 초기자** |
| 5 | — | — | 파생 생성자 본문 — `super()` 뒤 |

- ★★★ **필드 초기자 축으로 보면 JS 는 C++ 쪽이다** — 기반이 필드와 본문까지 다 끝난 **다음에** 파생 필드가 채워진다.
  C# 만 「**파생 필드가 제일 먼저**」다.
- ★★ **JS 에만 있는 칸이 1번이다** — 파생 생성자 본문이 `super()` **앞에서 먼저 돈다.** 그 자리에서 `this` 를 쓰면 무엇이 되나는 **여기서 안 던졌다**(17번).
- ★ **한 클래스 안의 「선언 순서」 규칙**은 C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md))의 **13번**이 정본이다(그 정답 2번 제목이 「`a` 가 먼저, `b` 가 나중 — **선언 순서**가 이긴다」).
  JS `[1]` 의 `a` → `b` 가 같은 모양이다. ★ 그 문서는 **상속을 다루지 않았다** — 기반/파생 순서는 C# 12번에서 가져왔다.

```text
   new Derived() -- JS 의 다섯 걸음

   Derived 본문  ── super() 앞 ──┐
                                 │ super()
                                 v
                   Base 필드 초기자
                   Base 생성자 본문
                                 │ super() 가 돌아오는 순간
                                 v
                   Derived 필드 초기자      <- ★ 기반이 다 끝난 뒤 (C++ 쪽)
                                 │
   Derived 본문  ── super() 뒤 ──┘         <- derivedField 가 이미 D
```

### (4) ★★★ 필드는 정의, 생성자 대입은 대입 — 부모에 setter 가 있으면 갈린다

**언제 쓰나** — 부모 클래스에 **같은 이름의 setter** 나 **비쓰기 프로퍼티**가 있을 때. 「필드로 적든 생성자에서 대입하든 같겠지」가 틀리는 자리다.
★ 이 블록은 **엄격 고정**이다(주석 뒤 첫 문장이 `"use strict"`).

```js
// js16b-16d-define-vs-set.js
// 필드 x = 1 과 생성자 안의 this.x = 1 -- 부모 프로토타입에 같은 이름이 있으면 둘은 같은 일을 하나.
// 11편의 「스프레드 대 Object.assign」과 견줄 자리다.
"use strict";
const calls = [];
class Parent {
  set x(v) { calls.push("Parent setter got " + v); this._x = v; }
  get x() { return "getter:" + this._x; }
}
class ByField extends Parent { x = 1; }
class ByAssign extends Parent { constructor() { super(); this.x = 1; } }

const show = (label, o) => {
  const d = Object.getOwnPropertyDescriptor(o, "x");
  console.log(label.padEnd(12) + "own keys " + JSON.stringify(Object.keys(o)).padEnd(10) +
    "own x " + (d ? JSON.stringify(d) : "none").padEnd(72) + "o.x " + o.x);
};

console.log("[1] a setter named x on the parent's prototype");
calls.length = 0; const f = new ByField();
show("x = 1", f);
console.log("            setter calls " + JSON.stringify(calls));
calls.length = 0; const a = new ByAssign();
show("this.x = 1", a);
console.log("            setter calls " + JSON.stringify(calls));

console.log("");
console.log("[2] a NON-writable x on the parent's prototype (strict)");
class Frozen {}
Object.defineProperty(Frozen.prototype, "x", { value: "locked", writable: false });
class FieldOverRO extends Frozen { x = 1; }
class AssignOverRO extends Frozen { constructor() { super(); this.x = 1; } }
for (const [label, C] of [["x = 1", FieldOverRO], ["this.x = 1", AssignOverRO]]) {
  try { const o = new C(); console.log(label.padEnd(12) + "ok, own x = " + o.x); }
  catch (e) { console.log(label.padEnd(12) + e.constructor.name + " " + e.message); }
}

console.log("");
console.log("[3] the same two operations outside classes (topic 11)");
const target = Object.create(Parent.prototype);
calls.length = 0;
Object.defineProperty(target, "x", { value: 2, writable: true, enumerable: true, configurable: true });
console.log("defineProperty  setter calls " + calls.length + "   own x? " + Object.hasOwn(target, "x"));
const target2 = Object.create(Parent.prototype);
calls.length = 0;
target2.x = 2;
console.log("plain  o.x = 2  setter calls " + calls.length + "   own x? " + Object.hasOwn(target2, "x"));
```

```text
===== node20 js16b-16d-define-vs-set.js (exit=0) =====
[1] a setter named x on the parent's prototype
x = 1       own keys ["x"]     own x {"value":1,"writable":true,"enumerable":true,"configurable":true}       o.x 1
            setter calls []
this.x = 1  own keys ["_x"]    own x none                                                                    o.x getter:1
            setter calls ["Parent setter got 1"]

[2] a NON-writable x on the parent's prototype (strict)
x = 1       ok, own x = 1
this.x = 1  TypeError Cannot assign to read only property 'x' of object '#<AssignOverRO>'

[3] the same two operations outside classes (topic 11)
defineProperty  setter calls 0   own x? true
plain  o.x = 2  setter calls 1   own x? false
```

**해설.**

- ★★★ `[1]` **필드 `x = 1` 은 부모 setter 를 한 번도 안 부른다**(`setter calls []`). 인스턴스에 **own 데이터 프로퍼티** `x` 가 생긴다 — `{"value":1,"writable":true,"enumerable":true,"configurable":true}`.
  ★ 그래서 `o.x` 는 **부모 getter 를 거치지 않고** `1` 이다 — own 이 체인 위의 접근자를 가린다.
- ★★★ **생성자 안 `this.x = 1` 은 부모 setter 가 가져간다**(`["Parent setter got 1"]`). own `x` 는 **없고** 대신 own `_x` 가 생긴다.
  `o.x` 는 부모 getter 를 거쳐 `getter:1` 이다.
  ★★ **`_x` 가 인스턴스에 생긴 이유는 15번이 이미 증명했다** — 체인 위 setter 안의 `this` 는 **수신자**다. 여기서 다시 재지 않는다.
- ★★★ `[2]` **부모 프로토타입에 비쓰기 `x` 가 있으면 필드는 통과하고 대입은 `TypeError`** 다
  (`Cannot assign to read only property 'x' of object '#<AssignOverRO>'`).
  ★ 15번 `[3]` 의 `kid.v = 'try'` 가 막히고 `defineProperty` 는 통과한 것과 **정확히 같은 갈림길**이다.
- ★★ `[3]` **클래스 밖에서도 같다** — `defineProperty` 는 setter 호출 0 에 own `true`, 평범한 `o.x = 2` 는 호출 1 에 own `false`.
  ★ 11번의 「**스프레드는 정의, `Object.assign` 은 대입**」(setter 호출 `0` 대 `1`)이 **클래스 문법 안에서 다시 나타난 것**이다.
- ★★★ **명세 근거** — `DefineField` 의 마지막 단계가 "Perform ? CreateDataPropertyOrThrow(receiver, fieldName, initValue)." 다.
  **대입(`Set`)이 아니라 데이터 프로퍼티 생성**이라 체인을 안 본다.

```text
   부모.prototype 에  set x(v)  가 있을 때 -- 같은 한 줄 "x 에 1" 이 두 길로 갈린다

   (가) 필드       class ByField extends Parent { x = 1 }
        DefineField = CreateDataPropertyOrThrow   -> 체인을 안 본다
        결과  own 키 ["x"] · setter 호출 0 · o.x -> 1   (own 이 부모 getter 를 가린다)

   (나) 생성자 대입  constructor() { super(); this.x = 1 }
        [[Set]] = 15번의 쓰기 경로                 -> 체인을 올라가 setter 를 찾는다
        setter 가 가져간다 · 그 안의 this 는 인스턴스
        결과  own 키 ["_x"] · setter 호출 1 · o.x -> getter:1
```

### (5) ★★★ `#private` 의 경계 — 누가 읽을 수 있고, 무엇이 막히나

**언제 쓰나** — 「이 객체가 정말 우리 클래스로 만든 것인가」를 물을 때, 그리고 **남의 객체·`Proxy`·`Object.create` 로 만든 가짜**를 받았을 때.

```js
// js16b-16e-private.js
// #private 의 경계 -- 누가 읽을 수 있고, 남의 객체에 들이대면 무엇이 나오나.
const run = (label, fn) => {
  let r;
  try { r = "-> " + String(fn()); } catch (e) { r = "-> " + e.constructor.name + " " + e.message; }
  console.log(label.padEnd(56) + r);
};

class Account {
  #balance;
  constructor(b) { this.#balance = b; }
  static isAccount(o) { return #balance in o; }
  static peek(o) { return o.#balance; }
  sameAs(other) { return this.#balance === other.#balance; }
}
class Lookalike { balance = 10; }
const a1 = new Account(10);
const a2 = new Account(10);

console.log("[1] #x in obj -- the brand check (ES2022)");
run("Account.isAccount(a1)", () => Account.isAccount(a1));
run("Account.isAccount(new Lookalike())", () => Account.isAccount(new Lookalike()));
run("Account.isAccount({})", () => Account.isAccount({}));
run("Account.isAccount(Object.create(Account.prototype))", () => Account.isAccount(Object.create(Account.prototype)));
run("Object.create(Account.prototype) instanceof Account", () => Object.create(Account.prototype) instanceof Account);
run("Account.isAccount(7)", () => Account.isAccount(7));

console.log("");
console.log("[2] reading #balance off something that lacks it");
run("Account.peek(a1)", () => Account.peek(a1));
run("a1.sameAs(a2)  (another instance, same class)", () => a1.sameAs(a2));
run("Account.peek(new Lookalike())", () => Account.peek(new Lookalike()));
run("Account.peek(Object.create(Account.prototype))", () => Account.peek(Object.create(Account.prototype)));
run("Account.peek(new Proxy(a1, {}))", () => Account.peek(new Proxy(a1, {})));

console.log("");
console.log("[3] #x written outside any class body");
run("new Function('o', 'return o.#balance')", () => new Function("o", "return o.#balance"));
run("new Function('class Q { m() { return this.#nope } }')", () => new Function("class Q { m() { return this.#nope } }"));
```

```text
===== node20 js16b-16e-private.js (exit=0) =====
[1] #x in obj -- the brand check (ES2022)
Account.isAccount(a1)                                   -> true
Account.isAccount(new Lookalike())                      -> false
Account.isAccount({})                                   -> false
Account.isAccount(Object.create(Account.prototype))     -> false
Object.create(Account.prototype) instanceof Account     -> true
Account.isAccount(7)                                    -> TypeError Cannot use 'in' operator to search for '#balance' in 7

[2] reading #balance off something that lacks it
Account.peek(a1)                                        -> 10
a1.sameAs(a2)  (another instance, same class)           -> true
Account.peek(new Lookalike())                           -> TypeError Cannot read private member #balance from an object whose class did not declare it
Account.peek(Object.create(Account.prototype))          -> TypeError Cannot read private member #balance from an object whose class did not declare it
Account.peek(new Proxy(a1, {}))                         -> TypeError Cannot read private member #balance from an object whose class did not declare it

[3] #x written outside any class body
new Function('o', 'return o.#balance')                  -> SyntaxError Private field '#balance' must be declared in an enclosing class
new Function('class Q { m() { return this.#nope } }')   -> SyntaxError Private field '#nope' must be declared in an enclosing class
```

**해설.**

- ★★★ `[1]` **`#balance in o` 는 브랜드 검사다** — 「이 객체에 **이 클래스의** `#balance` 칸이 있나」.
  모양이 같은 `Lookalike`(공개 `balance` 가 있다)도 `false`, `{}` 도 `false` 다.
- ★★★ **`Object.create(Account.prototype)` 은 `instanceof` 가 `true` 인데 브랜드는 `false`** 다.
  ★ `instanceof` 는 15번대로 **체인에 `Account.prototype` 이 있나**만 보고, 브랜드는 **생성자가 실제로 돌며 칸을 붙였나**를 본다.
  **둘은 다른 질문이다** — 체인은 누구나 꾸밀 수 있고 브랜드는 못 꾸민다.
- ★★ **원시값에 `#x in` 을 쓰면 `false` 가 아니라 `TypeError`** 다(`Cannot use 'in' operator to search for '#balance' in 7`). 평범한 `in` 과 같은 규칙이다.
- ★★★ `[2]` **같은 클래스라면 다른 인스턴스의 `#balance` 도 읽힌다**(`a1.sameAs(a2)` 가 `true`). **`#private` 는 인스턴스 단위가 아니라 클래스 몸통 단위의 비밀**이다.
- ★★★ **칸이 없는 객체에서 읽으면 `undefined` 가 아니라 `TypeError`** 다(`Cannot read private member #balance from an object whose class did not declare it`).
  ★ 15번의 「없는 프로퍼티는 `undefined`」와 **정반대**다. 명세 `PrivateGet` — "If entry is empty, throw a TypeError exception."
- ★★★ **`new Proxy(a1, {})` 도 `TypeError`** 다 — 트랩이 **하나도 없는** 투명 프록시인데 막힌다.
  ★ `PrivateElementFind` 가 "If obj.[[PrivateElements]] contains a PrivateElement entry …" 로 **그 객체 자신의 칸**을 보는데, 프록시는 **대상과 다른 객체**라 그 칸이 없다.
- ★★ `[3]` **클래스 밖의 `#x` 는 실행 전에 `SyntaxError`** 다 — 문자열로 `new Function` 에 넘겨 받아야만 잡을 수 있었다.
  ★ 클래스 안이어도 **선언 안 한 `#nope`** 는 같은 `SyntaxError` 다.

**한 번 더 — 네 창이 정말 다 눈멀었나.** 격자(`[3]`)가 ② 창을 닫았다. ①과 ③을 따로 물었고, 클래스 안쪽으로 창을 바꿔 답을 얻었다.

```js
// js16b-16f-private-windows.js
// #private 는 네 창에 다 안 보이나 -- 브랜드 태그(③)·Proxy 트랩 로그(①)로 한 번 더 묻고,
// 「있는데 안 보인다」는 것을 클래스 안쪽의 #x in 으로 답한다(창을 바꿔 물었다).
const run = (label, fn) => {
  let r;
  try { r = "-> " + String(fn()); } catch (e) { r = "-> " + e.constructor.name + " " + e.message; }
  console.log(label.padEnd(46) + r);
};

class WithPriv { #x = 1; field = "f"; static has(o) { return #x in o; } static bump(o) { o.#x += 1; return o.#x; } }
class NoPriv { field = "f"; }
const w = new WithPriv();

console.log("[1] window 3 -- the brand tag, with and without #x");
run("toString.call(new WithPriv())", () => Object.prototype.toString.call(w));
run("toString.call(new NoPriv())", () => Object.prototype.toString.call(new NoPriv()));
run("getOwnPropertyNames(new WithPriv())", () => JSON.stringify(Object.getOwnPropertyNames(w)));

console.log("");
console.log("[2] window 1 -- a Proxy that logs every trap");
const L = [];
const handler = {};
for (const t of ["get", "set", "has", "getOwnPropertyDescriptor", "defineProperty", "ownKeys", "getPrototypeOf"]) {
  handler[t] = (...a) => { L.push(t + (typeof a[1] === "string" ? "(" + a[1] + ")" : "")); return Reflect[t](...a); };
}
const p = new Proxy(w, handler);
L.length = 0; run("p.field", () => p.field); console.log("  trap log " + JSON.stringify(L));
L.length = 0; run("WithPriv.has(p)", () => WithPriv.has(p)); console.log("  trap log " + JSON.stringify(L));
L.length = 0; run("WithPriv.bump(p)", () => WithPriv.bump(p)); console.log("  trap log " + JSON.stringify(L));

console.log("");
console.log("[3] #x after Object.freeze");
Object.freeze(w);
run("Object.isFrozen(w)", () => Object.isFrozen(w));
run("WithPriv.bump(w)  (after freeze)", () => WithPriv.bump(w));
run("w.field = 'g'  (after freeze, sloppy file)", () => { w.field = "g"; return w.field; });

console.log("");
console.log("[4] two classes that both spell #x");
class Other { #x = 1; }
run("WithPriv.has(new Other())  (same spelling #x)", () => WithPriv.has(new Other()));
const make = () => class { #x = 1; static has(o) { return #x in o; } };
const K1 = make();
const K2 = make();
run("K1.has(new K1())", () => K1.has(new K1()));
run("K1.has(new K2())  (same source, 2nd eval)", () => K1.has(new K2()));
```

```text
===== node20 js16b-16f-private-windows.js (exit=0) =====
[1] window 3 -- the brand tag, with and without #x
toString.call(new WithPriv())                 -> [object Object]
toString.call(new NoPriv())                   -> [object Object]
getOwnPropertyNames(new WithPriv())           -> ["field"]

[2] window 1 -- a Proxy that logs every trap
p.field                                       -> f
  trap log ["get(field)"]
WithPriv.has(p)                               -> false
  trap log []
WithPriv.bump(p)                              -> TypeError Cannot read private member #x from an object whose class did not declare it
  trap log []

[3] #x after Object.freeze
Object.isFrozen(w)                            -> true
WithPriv.bump(w)  (after freeze)              -> 2
w.field = 'g'  (after freeze, sloppy file)    -> f

[4] two classes that both spell #x
WithPriv.has(new Other())  (same spelling #x) -> false
K1.has(new K1())                              -> true
K1.has(new K2())  (same source, 2nd eval)     -> false
```

- ★★★ `[1]` **브랜드 태그가 같다** — `#x` 가 있든 없든 `[object Object]` 다. ③ 창도 차이를 못 본다.
- ★★★ `[2]` **모든 트랩을 심은 `Proxy` 에서 `#x` 접근은 트랩 로그가 0줄**이다. 공개 `p.field` 는 `["get(field)"]` 한 줄을 남긴다.
  ★ `has(p)` 는 `false`, `bump(p)` 는 `TypeError` 인데 **둘 다 트랩을 한 번도 안 불렀다** — ① 창은 `#x` 를 **원리상** 못 본다.
- ★★★ `[3]` **`Object.freeze` 도 `#x` 를 못 막는다** — 얼린 뒤에도 `bump(w)` 가 `2` 다. 반면 공개 필드 대입은 **조용히 무시**된다(이 파일은 비엄격이다).
  ★ 14번의 동결은 **프로퍼티의 플래그**를 바꾸는 일인데, `#x` 는 **프로퍼티가 아니다.**
- ★★ `[4]` **같은 철자 `#x` 라도 클래스 몸통이 다르면 다른 이름이다** — `WithPriv.has(new Other())` 가 `false`.
  ★★ **같은 소스를 두 번 평가해도 다르다** — 팩토리가 만든 `K1` 과 `K2` 에서 `K1.has(new K2())` 가 `false` 다. 이름은 **소스 글자가 아니라 클래스 평가 한 번**에 묶인다.

```text
   #x 를 누가 볼 수 있나

   클래스 몸통 밖  ─── o.#x ──────────────▶ SyntaxError 로 막힌다 (실행 전)
                  ─── Reflect / JSON / 스프레드 / in / toString / Proxy 트랩 ──▶ 아무것도 안 보인다

   클래스 몸통 안  ─── #x in o  ──▶ true / false   (원시값이면 TypeError 로 막힌다)
                  ─── o.#x     ──▶ 값             (칸이 없으면 TypeError 로 막힌다)
                                                  ★ undefined 가 아니다

   "칸이 있다" 의 뜻 = 이 클래스 몸통의 이 평가가 만든 생성자가 그 객체 위에서 실제로 돌았다
                      (Object.create · Proxy · 모양만 같은 객체 · 다른 평가 -- 전부 칸이 없다)
```

### (6) ★ 클래스 메서드가 비열거라서 — `for...in` 한 줄

**언제 쓰나** — 옛 방식(`F.prototype.m = function`)을 클래스로 옮길 때 **순회 결과가 바뀌나**를 물을 때.
★ `for...in` 의 규칙 자체는 18번이 정본이다. 여기서는 두 방식이 갈리는지만 본다.

```js
// js16b-16g-forin.js
// 클래스 메서드가 enumerable:false 인 것이 for...in 에 무엇을 주나 -- 옛 방식(함수 + prototype 대입)과 견준다.
// for...in 의 규칙 자체는 18편이 정본이다. 여기서는 「두 방식이 갈리나」 한 줄만 본다.
class Modern {
  field = 1;
  method() { return "m"; }
}
function Old() { this.field = 1; }
Old.prototype.method = function () { return "m"; };

const keysOf = (o) => { const ks = []; for (const k in o) ks.push(k); return JSON.stringify(ks); };
console.log("for...in new Modern()        " + keysOf(new Modern()));
console.log("for...in new Old()           " + keysOf(new Old()));
console.log("Object.keys(new Modern())    " + JSON.stringify(Object.keys(new Modern())));
console.log("Object.keys(new Old())       " + JSON.stringify(Object.keys(new Old())));
console.log("'method' in new Modern()     " + ("method" in new Modern()));
```

```text
===== node20 js16b-16g-forin.js (exit=0) =====
for...in new Modern()        ["field"]
for...in new Old()           ["field","method"]
Object.keys(new Modern())    ["field"]
Object.keys(new Old())       ["field"]
'method' in new Modern()     true
```

- ★★★ **`for...in` 이 옛 방식에서는 프로토타입의 `method` 까지 줍고 클래스에서는 안 줍는다**(`["field","method"]` 대 `["field"]`).
  ★ `for...in` 은 체인을 타지만 **비열거는 건너뛴다** — 동작 (1)의 `[4]` 에서 본 `enumerable false` 가 그 차이를 만든다.
- ★★ **`Object.keys` 는 둘 다 `["field"]`** 다 — own 만 보므로 프로토타입의 열거 여부와 무관하다.
- ★ **`'method' in new Modern()` 은 `true`** 다 — `in` 은 열거 여부를 안 본다. **보이지 않을 뿐 거기 있다.**

## 문법 — 형태와 규칙

```text
   class C {
     x = 1;                    공개 필드         -> 인스턴스 own, 정의(define), WEC     (ES2022)
     #y = 2;                   private 필드      -> 인스턴스의 [[PrivateElements]]     (ES2022)
     constructor(a) { ... }    생성자           -> C 자신이 된다
     m() { }                   메서드           -> C.prototype, W-C (비열거)          (ES2015)
     get g() { }               접근자           -> C.prototype, accessor -C
     #pm() { }                 private 메서드    -> 인스턴스의 [[PrivateElements]]     (ES2022)
     static s() { }            정적 메서드       -> C, W-C                            (ES2015)
     static sf = 3;            정적 필드         -> C, WEC, 정의 시점에 한 번           (ES2022)
     static #ss = 4;           정적 private      -> C 의 [[PrivateElements]]          (ES2022)
     static { ... }            정적 블록         -> 정의 시점에 한 번, this 는 C        (ES2022)
     static has(o) { return #y in o; }            브랜드 검사                          (ES2022)
   }
```

- **메서드·접근자는 프로토타입에, 필드는 인스턴스에, `static` 은 생성자에 붙는다.** 한 멤버는 한 자리에만 떨어진다.
- ★★★ **필드는 정의(`DefineField` → `CreateDataPropertyOrThrow`)다.** 부모의 setter·비쓰기 프로퍼티를 안 본다.
  **생성자 안 `this.x = v` 는 대입**이다 — 15번의 쓰기 경로를 그대로 탄다.
- **필드 초기자는 생성자 본문보다 먼저, 필드끼리의 선언 순서로 돈다.** 파생 클래스에서는 `super()` 가 돌아오는 순간이다.
- **`static` 필드와 `static {}` 는 클래스 정의 때 선언 순서로 한 번 돈다.** `this` 는 클래스 자신이다.
- **클래스 메서드는 비열거다.** 리터럴 메서드와 옛 방식 대입은 열거된다.
- **클래스는 `new` 없이 못 부르고, TDZ 에 들어가며, 몸통이 엄격이고, 안쪽 이름이 `const` 이고, `.prototype` 이 쓰기 불가다.**
- **`#x` 는 프로퍼티가 아니다.** 리플렉션·JSON·스프레드·`Proxy`·동결이 전부 못 본다. 클래스 밖에서는 `SyntaxError`, 칸이 없으면 `TypeError` 다.
- **`#x in o` 는 브랜드 검사다.** `instanceof` 와 달리 체인을 꾸며서는 못 속인다.

## 어디서 틀리나

### (1) ★★★ 「필드로 적든 생성자에서 대입하든 같다」

**부모에 같은 이름의 setter 가 있으면 갈린다.** 필드는 setter 호출 0에 own `x`, 대입은 호출 1에 own `_x` 다.
★ 부모에 비쓰기 `x` 가 있으면 **필드는 통과하고 대입은 `TypeError`** 다. 동작 (4).
★ 트랜스파일러가 필드를 어떤 코드로 바꿔 내는지는 **이 문서가 안 돌렸다** — 빌드 도구를 거친다면 출력 코드를 직접 읽어 정의인지 대입인지 확인해라.

### (2) ★★★ `#private` 를 「이름만 숨긴 프로퍼티」로 읽는다

**프로퍼티가 아니다.** `Reflect.ownKeys` 에도 `JSON.stringify` 에도 스프레드에도 안 나오고, `Object.freeze` 도 못 막는다.
★ 그래서 **직렬화·복제·로그에서 조용히 빠진다** — 에러가 아니라 누락이다. `structuredClone` 결과에도 `field` 하나뿐이었다.

### (3) ★★★ `Proxy` 로 감싼 인스턴스에 메서드를 부른다

메서드 안에서 `this.#x` 를 읽으면 **`this` 가 프록시**라 `TypeError` 다 — 트랩이 하나도 없는 `new Proxy(a1, {})` 도 막혔다.
★ 트랩 로그가 0줄이니 **핸들러에서 고칠 길도 없다.** 객체를 프록시로 감싸 넘기는 코드와 `#private` 는 **같이 쓰기 어렵다**는 뜻이다.

### (4) ★★★ `instanceof` 로 「우리 클래스가 만든 것」을 판정한다

`Object.create(Account.prototype)` 은 `instanceof` 가 `true` 인데 **생성자가 안 돌아서 `#balance` 가 없다** — 메서드를 부르면 `TypeError` 다.
★ **진짜 판정은 `#balance in o`** 다. 체인은 누구나 꾸밀 수 있다(15번).

### (5) ★★ 클래스를 `typeof` 로 「함수니까 부를 수 있다」고 판정한다

`typeof K` 는 `function` 인데 `K()` 와 `K.call({})` 가 `TypeError` 다. **호출 가능과 생성 가능은 다른 자격이다**(08번).

### (6) ★★ 클래스 메서드를 떼어 콜백으로 넘긴다

떼어 낸 클래스 메서드의 `this` 는 **`undefined`** 다 — 몸통이 엄격이라 전역으로 떨어지지도 않는다.
★ 처방은 07번에 있다 — `bind`, 또는 **필드에 화살표를 담기**(인스턴스마다 하나씩 생긴다는 대가는 동작 (1)의 격자 그대로다).

### (7) ★★ 옛 방식을 클래스로 옮기고 `for...in` 결과가 같다고 믿는다

옛 방식은 프로토타입 메서드가 **열거**돼서 인스턴스의 `for...in` 에 끼어들었다. 클래스로 옮기면 **빠진다**(동작 (6)).
★ 대개는 좋은 쪽이지만, 그 끼어듦에 기대던 코드가 있으면 **조용히 결과가 줄어든다.**

### (8) ★★ 생성자 본문에서 필드가 아직 비었을 거라고 가정한다

**이미 채워져 있다** — 필드가 소스에서 생성자 **아래**에 적혀 있어도 그렇다(동작 (3)의 `[1]`).
★ 반대로 **기반 생성자 안에서는 파생 필드가 아직 없다**(`[2]` 의 3번과 4번 순서). C# 과 반대다.

### (9) ★ 「`#private` 는 느리다 / 필드는 메모리를 더 먹는다」를 옮긴다

★★★ **이 문서는 그 말을 하지 않는다 — 안 쟀다.** 말할 수 있는 것은 **어디에 붙나**(격자)뿐이다.

## 구현 세부사항 대 언어 보장

### 명세 보장 — 어느 엔진에서도 같아야 하는 것

- ★★★ **메서드·접근자는 프로토타입, 필드는 인스턴스, `static` 은 생성자에 붙는 것** · **클래스 메서드가 비열거인 것**(`ClassElementEvaluation` 의 `false`).
- ★★★ **필드가 `CreateDataPropertyOrThrow` 로 정의되는 것** — 부모 setter 를 안 부르고, 부모의 비쓰기 프로퍼티에 안 막히는 것.
- ★★ **필드 초기자가 선언 순서로, 생성자 본문보다 먼저 도는 것** · 파생에서는 `super()` 뒤에 도는 것 · `static` 부분이 정의 때 선언 순서로 한 번 도는 것.
- ★★ **클래스 몸통 전체가 엄격인 것** · 클래스 선언이 TDZ 에 들어가는 것 · `new` 없는 호출이 `TypeError` 인 것 · 안쪽 이름 재대입이 `TypeError` 인 것.
- ★★★ **`#x` 를 못 찾으면 `TypeError` 인 것**(`PrivateGet`) · 클래스 밖 `#x` 가 `SyntaxError` 인 것 · 프록시가 대상의 `#x` 칸을 안 갖는 것.
- **Own 키 순서가 삽입 순서인 것**(13번 — 문자열 키 기준).
- **예외의 종류**(`TypeError`·`ReferenceError`·`SyntaxError`) 전부.

### 엔진(V8) 구현 · 이 판의 관찰

- **예외 문구 전부** — `Class constructor K cannot be invoked without 'new'` · `Cannot access 'Late' before initialization` · `leakedFromClass is not defined` ·
  `Assignment to constant variable.` · `Cannot assign to read only property 'x' of object '#<AssignOverRO>'` ·
  `Cannot use 'in' operator to search for '#balance' in 7` · `Cannot read private member #balance from an object whose class did not declare it` ·
  `Private field '#balance' must be declared in an enclosing class`. **종류만 명세가 정한다.**
- ★ **두 판(18·20)이 이 주제에서 한 글자도 안 갈린 것** — 둘 다 V8 이기 때문이지 보장이 아니다.

### 호스트가 정하는 것 — ECMA-262 밖

- ★★ **`structuredClone`** — ECMA-262 가 아니라 **호스트 API**(HTML 표준 · Node 가 전역으로 제공)다. 그 결과에 `#private` 가 없는 것은 이 판의 관찰로 적는다.
- `console.log` 가 클래스 인스턴스를 **어떻게 그리나**는 Node 의 표기다 — 이 문서는 그 표기를 한 줄도 근거로 쓰지 않았다(전부 `JSON.stringify`·`Reflect.ownKeys` 로 찍었다).

### 그래서 이렇게 적으면 틀린다

- 「`class` 는 새로운 객체 모델이다」 — **아니다.** 15번의 체인을 짓는 문법이다. 격자의 세 자리가 전부 평범한 객체다.
- 「필드는 생성자에서 `this.x = v` 한 것과 같다」 — **아니다.** 정의 대 대입이다.
- 「`#private` 는 `_x` 관례의 강한 판이다」 — **종류가 다르다.** `_x` 는 프로퍼티이고 `#x` 는 프로퍼티가 아니다.
- 「`instanceof` 가 `true` 면 그 클래스의 메서드가 안전하게 돈다」 — **아니다.** `#x` 가 없으면 `TypeError` 다.
- 「`#private` 는 느리다」 — ★★★ **안 쟀다.**

## 언제 쓰고 언제 안 쓰나

- **`class`** — 생성자 함수 + `prototype` 손질을 쓸 자리면 **기본 선택**이다. `constructor` 다시 달기·비열거 처리·`new` 강제를 전부 문법이 해 준다.
- **공개 필드** — 인스턴스마다 따로 있어야 하는 **가변 상태**의 자리. ★ 15번의 「프로토타입에 배열을 올려 공유한다」 함정이 필드에서는 안 생긴다 — 인스턴스마다 정의되기 때문이다.
- ★ **부모에 setter 가 있는 이름이면 필드를 쓰지 않는다** — 생성자에서 대입해야 부모 setter 가 돈다. 의도가 그 반대면 필드가 맞다.
- **`#private`** — **바깥에서 정말 못 건드려야 하는** 상태, 그리고 **브랜드 검사**(`#x in o`)가 필요할 때.
  ★ **안 쓸 자리** — 프록시로 감쌀 객체 · 직렬화·복제될 객체 · 테스트에서 들여다봐야 하는 상태.
- **`static {}`** — 정적 필드 여럿을 **한 번에 계산**하거나 `try` 가 필요한 초기화. 클래스 정의 때 한 번뿐이다.
- **필드에 화살표 담기** — 떼어 넘길 콜백일 때만. 인스턴스마다 함수가 하나씩 생긴다(격자의 `instance` 열).

## 핵심 문장

1. ★★★ **메서드·getter 는 프로토타입, 필드는 인스턴스, `static` 은 생성자에 붙는다** — 27칸 중 6칸, 한 멤버는 한 자리에만.
2. ★★★ **필드는 정의이고 생성자의 `this.x = v` 는 대입이다** — 부모 setter 와 비쓰기 프로퍼티에서 갈린다(11번 「정의 대 대입」의 재등장).
3. ★★★ **`#private` 는 프로퍼티가 아니다** — 리플렉션·JSON·스프레드·`Proxy`·동결이 전부 못 보고, 클래스 안쪽의 `#x in o` 만 답한다.
4. ★★ **필드 초기자는 생성자 본문보다 먼저, 파생에서는 기반이 다 끝난 뒤에 돈다** — C++ 쪽이고 C# 과 반대다.
5. ★★ **클래스는 `new` 로만 부를 수 있는 엄격한 함수다** — TDZ · 안쪽 `const` 이름 · 쓰기 불가 `.prototype` · 비열거 메서드.

## 관련 자료

- [15 — 프로토타입 체인](../15-prototype-chain/2-summary.md) — **그쪽이 체인 조회·쓰기 경로와 setter `this` 의 정본**이다. 여기는 **체인의 어느 칸에 무엇이 붙나**부터.
- [14 — 프로퍼티 디스크립터와 동결](../14-property-descriptors-and-freezing/2-summary.md) — **그쪽이 W/E/C 플래그와 동결의 정본**이다. 여기는 **클래스가 어떤 플래그로 붙이나**와 동결이 `#x` 를 못 막는다는 것까지.
- [11 — 스프레드와 나머지](../11-spread-and-rest/2-summary.md) — **그쪽이 「정의 대 대입」을 처음 잰 곳**이다. 여기는 **필드와 생성자 대입**에서의 재등장.
- [08 — 함수 정의 형태와 매개변수](../08-function-forms-and-parameters/2-summary.md) — **그쪽이 `prototype` 유무 × `new` 가능 16형태 격자의 정본**이다. 여기는 클래스·클래스 메서드·정적 메서드 다섯 줄.
- [07 — `this` 바인딩 네 규칙](../07-this-binding-four-rules/2-summary.md) — **그쪽이 떼어 낸 메서드와 필드 화살표의 정본**이다.
- [05 — `var`·`let`·`const` 와 TDZ](../05-var-let-const-and-tdz/2-summary.md) — **그쪽이 클래스 TDZ 의 정본**이다. 여기는 한 줄 재확인.
- [13 — 객체 리터럴과 프로퍼티](../13-object-literals-and-properties/2-summary.md) — **그쪽이 리터럴 메서드와 키 순서의 정본**이다.
- [17 — 상속과 `super`](../17-inheritance-and-super/2-summary.md) — **그쪽이 `extends`·`super`·`new.target`·내장 상속의 정본**이다. 여기서 `extends` 는 순서 재기에만 썼다.
- [18 — `for...in` 과 열거](../18-for-in-and-enumeration/2-summary.md) — **그쪽이 열거 규칙의 정본**이다. 여기는 클래스 메서드 비열거가 주는 한 줄까지.
- [목록의 **35번 주제**](../35-strict-mode/) 「엄격 모드」 — **그쪽이 엄격 모드가 바꾸는 규칙 전체의 정본**이다. 여기는 **클래스 몸통이 늘 엄격**이라는 것까지.
- [목록의 **45번 주제**](../45-proxy/) 「`Proxy`」 — **그쪽이 트랩 계약의 정본**이다. 여기는 **`#x` 가 트랩에 안 걸린다**까지.
- C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **12번** — **필드 초기화 순서의 대비축**(C# 과 C++ 두 열을 거기서 가져왔다).
- C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md))의 **13번** — **한 클래스 안의 선언 순서 규칙**의 정본.
- Python 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **29번** — 클래스 속성과 인스턴스 속성의 탐색. 이 문서는 파이썬을 **안 돌렸다.**

## 용어 풀이

- **클래스(class)** — `new` 로만 부를 수 있는 엄격한 생성자 함수를 만드는 문법. 몸통의 멤버를 세 자리에 나눠 붙인다.
- **필드(field)** — 몸통에 `x = 값` 으로 적는 멤버. **인스턴스마다 정의**된다(ES2022).
- **정적 멤버(static)** — **생성자 함수 자신**에 붙는 멤버. 인스턴스는 모른다.
- **`static {}` 블록** — 클래스 정의 때 **한 번** 도는 코드. `this` 는 클래스 자신이다(ES2022).
- **`#private`** — 프로퍼티가 아닌 별도의 칸에 사는 멤버. 클래스 몸통 안에서만 이름을 쓸 수 있다.
- **브랜드 검사(brand check)** — `#x in o`. 「이 클래스 몸통이 만든 칸이 이 객체에 있나」를 묻는다(ES2022).
- **정의(define)** — 그 객체에 **칸을 바로 만드는** 것. 체인을 안 본다. `defineProperty`·스프레드·필드.
- **대입(set)** — **값을 바꾸겠다**는 요청. 체인을 올라가 setter·비쓰기를 본다. `=`·`Object.assign`.
- **초기자(initializer)** — 필드의 `=` 오른쪽 식. 필드마다 인스턴스를 만들 때 한 번 돈다.
- **TDZ** — 선언 줄에 닿기 전까지 이름이 있는데 못 쓰는 구간. 클래스 선언도 들어간다.
- **열거 가능(enumerable)** — `Object.keys`·`for...in`·스프레드에 보이나를 정하는 플래그. 클래스 메서드는 `false`.
- **`[[PrivateElements]]`** — 명세가 `#private` 를 담는 객체의 내부 목록. 프로퍼티 목록과 **따로** 있다.

## 더 들어가면

- **`#private` 가 「프로퍼티가 아니다」가 설계의 핵심이다.** 프로퍼티였다면 `Proxy`·`Reflect`·`defineProperty` 로 바깥에서 닿을 길이 생긴다.
  별도의 칸이라 **닿을 길이 문법 안쪽에만** 있고, 그래서 브랜드 검사가 믿을 만하다. 대가가 동작 (5)의 프록시 `TypeError` 다.
- **같은 소스를 두 번 평가하면 다른 `#x` 가 된다**(`K1`·`K2`)는 사실은 **클래스 팩토리·모듈 중복 로드**에서 물린다 —
  같은 라이브러리가 두 벌 로드되면 한쪽이 만든 객체를 다른 쪽의 `#x in` 이 `false` 로 본다. ★ 모듈 중복 로드 자체는 **이번에 안 돌려 봤다.**
- **필드가 왜 대입이 아니라 정의로 정해졌나**의 제안 논의 기록은 **이번에 안 열었다.**
  확인된 것은 결과뿐이다 — `DefineField` 가 `CreateDataPropertyOrThrow` 를 부른다. 그 까닭을 적으려면 TC39 제안 저장소를 따로 읽어야 한다.
- **`static` 멤버가 상속되는 이유**는 15번의 「`B` 의 윗집이 `A` 다」이고, `super` 로 부모의 정적 멤버를 부르는 일은 17번이다.
