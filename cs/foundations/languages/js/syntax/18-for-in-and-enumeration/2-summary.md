# js/syntax/18 — `for...in` 과 열거: 「체인을 걷는 열거는 `for...in` 하나뿐이다」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> ★★★ **이 주제의 본체는 ② 전수 격자(체인 순회 격자)다.**
> 프로퍼티 여섯 종(자기 열거 가능 · 자기 비열거 · 자기 심볼 · 상속 열거 가능 · 상속 비열거 · 상속 심볼)에
> 「키를 늘어놓는 문법」 아홉 개를 전부 대 봤다. **체인 위의 칸에 닿는 열은 `for-in` 과 `in` 둘뿐이고,
> 그중 목록을 내놓는 것은 `for-in` 하나다.** 이 문서의 결론은 전부 그 격자에서 나온다.
> ① 트랩 로그는 **보조**다 — `for...in` 이 체인을 **어떻게** 걷는지(어느 트랩을 어느 칸에) 보여 주지만,
> ★ 그 **순서**는 V8 의 관찰이다. 명세의 알고리즘을 손으로 옮긴 생성기와 나란히 돌려 **순서가 다르다**는 것까지 찍었다.
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262 최신 초안](https://tc39.es/ecma262/) — `EnumerateObjectProperties` · `CreateForInIterator` ·
>   `%ForInIteratorPrototype%.next` · `ForIn/OfHeadEvaluation`
>   (멀티페이지: [문과 선언 장](https://tc39.es/ecma262/multipage/ecmascript-language-statements-and-declarations.html))
> - [ECMA-262 판별 아카이브](https://262.ecma-international.org/) · [TC39 완료 제안 목록](https://github.com/tc39/proposals/blob/main/finished-proposals.md) — 판 경계를 가릴 때
> - [TC39 — for-in order 제안](https://tc39.es/proposal-for-in-order/) — `for...in` 순서가 못 박힌 판(13편이 인용한 것을 그대로 받는다)
>
> ★★★ **명세 조항 번호는 인용하지 않는다.** 규칙은 추상 연산 **이름**으로, **값·순서·예외는 전부 실행으로** 접지했다.
>
> **실행 검증** — 이 문서의 모든 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 없다).
> 배너의 `node20` 은 `~/.nvm/versions/node/v20.19.6/bin/node` 다. 대조 판은 기본 PATH 의 `node`(v18.19.1)다.
> ★★ 예외는 `try`/`catch` 로 받아 `e.constructor.name` 과 `e.message` 만 찍었다. **표준 출력뿐이고 스택트레이스는 한 줄도 없다.**
> ★ **이 주제의 탐침은 전부 비엄격 스크립트다**(`"use strict"` 없음). 엄격에서 따로 돌리지 않았다 — 아래 창 표에 올렸다.
>
> **버전 — 판 경계**
>
> | 무엇 | 판 | 근거 |
> |---|---|---|
> | `for...in` 문 자체 | **초판부터** | — |
> | `for...in` 의 **순서**가 명세로 못 박힘 | **ES2020** | for-in order 제안([13편](../13-object-literals-and-properties/2-summary.md)의 인용) |
> | `Object.keys` | **ES5** | — |
> | `Object.keys` 의 **순서**(own 키 세 덩어리) | **ES2015** | 13편의 인용 |
> | `Object.hasOwn` | **ES2022** | [15편](../15-prototype-chain/2-summary.md)의 인용 |
>
> ★ 두 판(18·20) 모두 `Object.hasOwn` 이 있다(판 정보 블록의 `hasOwn function`). **이 표의 어느 줄도 두 판 사이에서 갈릴 자리가 없다.**
>
> **★★★ 이 주제가 쓰는 창 — 그리고 부적용인 창**
>
> | 창 | 이 주제에서 무엇을 보나 |
> |---|---|
> | ★★★ **② 전수 격자**(본체) | 프로퍼티 **6종 × 문법 9열** · `for-in` 순서(own 뒤에 부모) · 가리기 · 배열의 함정 · 순회 중 추가/삭제 **7행** |
> | ★★ **① 추상 연산에 로그 심기**(보조) | 두 칸 체인에 `Proxy` 를 씌워 `for-in` 이 부르는 트랩을 찍는다 — `ownKeys`·`getPrototypeOf`·`gopd`. ★ `Object.keys` 는 `ownKeys`+`gopd` 로 끝난다. **트랩 순서는 V8 관찰** |
> | ★★ **④ 예외의 `constructor.name` + `message`** | `TypeError` **세 줄**(`hasOwnProperty` 가 함수가 아님 ×2 · `Object.keys(null)`) — ★★★ 그리고 **예외가 안 나는 자리**: `for-in null`·`for-in undefined` 는 몸통이 한 번도 안 돈다 |
> | ★ **⑤ 두 판 대조기** | 이 주제의 블록은 **두 판에서 identical** 이다 |
> | ★ **부적용 — ③ 브랜드 태그** | **잴 것이 없다.** 열거의 답은 키 목록이고 키 목록은 `JSON.stringify` 로 전부 찍힌다. 평소 창이 닫히는 자리가 없다(`Object.create(null)` 에도 `for-in` 은 된다) |
> | ★ **부적용 — 진단의 `(행,열)`**(18-C) | `SyntaxError` 가 한 줄도 없다. 열거는 전부 런타임 의미다 |
> | ★ **안 돌렸다 — 두 번 컴파일**(엄격/비엄격) | 이 주제의 탐침은 전부 비엄격이다. **엄격에서 답이 바뀌는 칸이 있는지 확인하지 않았다** |
> | ★ **안 돌렸다 — 브라우저** | Node 두 판만 돌렸다 |
> | ★★★ **안 쟀다 — 성능** | 「`for...in` 은 느리다」·「`Object.keys` 가 빠르다」 같은 말을 **이 문서는 한 줄도 쓰지 않는다. 안 쟀다** |
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 예외 **문구**(`o.hasOwnProperty is not a function` 등 — V8) | ★★★ 격자의 `o`/`.` · **예외의 종류** |
> | ★★ **`Proxy` 가 낀 체인에서의 트랩 순서** — 명세가 묶지 않는다 | ★★★ **Proxy 없는 체인의 `for-in` 순서**(ES2020) |
> | ★★ **순회 중 추가/삭제에서 명세가 보장하지 않는 행**(표로 갈랐다) | ★★ 명세가 보장하는 행 — 처리 전 삭제는 무시 · 평범한 객체 자신에 추가한 키는 안 나온다 |
>
> ★★ **이 주제의 블록에는 주소도 시간도 난수도 안 찍힌다.** 같은 판에서 다시 돌리면 한 글자도 안 변한다.
> ★★ **두 판 대조** — 이 주제의 블록은 두 판에서 identical 이다(대조기 끝줄은 판 정보 블록 바로 뒤에 싣는다. 갈린 하나는 19편의 스프레드 문구다).
>
> **선행** — [13 — 객체 리터럴과 프로퍼티](../13-object-literals-and-properties/2-summary.md) ·
> [14 — 프로퍼티 디스크립터와 동결](../14-property-descriptors-and-freezing/2-summary.md) ·
> [15 — 프로토타입 체인](../15-prototype-chain/2-summary.md) · [11 — 스프레드와 나머지](../11-spread-and-rest/2-summary.md).
> ★★★ **이 주제는 13·15편의 결론이다.** 13편이 own 키의 **순서**를, 14편이 `enumerable` **플래그**를,
> 15편이 **조회가 체인을 탄다**는 것을 세웠다. 여기서 더하는 것은 하나 — **「체인 순회」, 즉 체인을 걷는 열거**다.
> **이어지는 곳** — [16 — `class` 문법](../16-class-syntax/2-summary.md)(클래스 메서드가 비열거라 `for...in` 에 안 나온다) ·
> [19 — 이터러블 프로토콜과 `for...of`](../19-iterable-protocol-and-for-of/2-summary.md) ·
> 목록의 **22번 주제** 「`Symbol` 과 잘 알려진 심볼」 · 목록의 **27번 주제** 「`Object` 정적 메서드」 ·
> 목록의 **31번 주제** 「`JSON`」 · 목록의 **45번 주제** 「`Proxy`」
>
> ★★ **경계 — own 키 순서 세 덩어리(배열 인덱스 → 문자열 → 심볼)와 정수 키 판정은 13편이 정본이다.** 여기서는 그 순서가 **체인 위에서 어떻게 이어지나**까지다.
> ★★ **경계 — `enumerable` 플래그를 어떻게 바꾸나(`defineProperty`·`freeze`)는 14편이 정본이다.** 여기서는 그 플래그가 **열거에서 무엇을 하나**만 본다.
> ★★ **경계 — 조회(`[[Get]]`)가 체인을 타는 규칙은 15편이 정본이다.** 여기서는 **열거가** 체인을 타는 규칙을 본다.
> ★★ **경계 — `for...of` 와 이터러블 프로토콜은 19편이 정본이다.** 여기서는 **배열에서 둘이 갈리는 자리**까지다.
> ★★ **경계 — `Object.keys`/`entries`/`assign` 의 쓰임은 목록의 27번 주제, `Proxy` 트랩 계약은 45번 주제가 정본이다.**

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

배치 전체의 두 판 대조기 끝줄 —
`identical 22  ·  differs 1  ·  total 23`

## 한눈에 — 쉽게 말하면

15편의 비유를 그대로 쓴다 — **객체는 자기 서랍을 갖고 있고, 없으면 윗집으로 올라가 본다.**
이 주제는 「**서랍 속 물건 목록을 만들어 달라**」는 부탁이다. 조사원이 여럿이고, **조사원마다 목록에 올리는 기준이 다르다.**

- 물건마다 **스티커**가 붙어 있다 — 「**목록에 올려도 됨**」(`enumerable: true`) 또는 「**목록에서 빼**」(`enumerable: false`).
- 이름표가 **글자가 아닌 물건**(심볼 키)도 있다.
- ★★★ **윗집까지 올라가 목록을 만드는 조사원은 `for...in` 한 명뿐이다.** 나머지는 전부 **내 서랍에서 멈춘다.**
- ★★ `for...in` 은 **글자 이름표이고 「올려도 됨」 스티커인 것**만 적는다. 그리고 **이미 본 이름은 윗집에서 다시 안 적는다** —
  내 서랍의 같은 이름 물건이 「목록에서 빼」였더라도 그렇다.

```text
   for (const k in o)  -- 윗집까지 올라가며 목록을 만든다

   o           [ ownEnum    올려도 됨 ]  -> 적는다
   (내 서랍)   [ ownHidden  목록에서 빼 ]  -> 안 적는다  (이름만 "봤다" 로 기억)
               [ Symbol()   글자 아님  ]  -> 안 적는다
                    │
                    v  윗집
   proto       [ inheritedEnum    올려도 됨 ] -> 적는다   (처음 보는 이름이면)
               [ inheritedHidden  목록에서 빼 ] -> 안 적는다
               [ Symbol()         글자 아님  ] -> 안 적는다
                    │
                    v
   Object.prototype  전부 "목록에서 빼" -> 하나도 안 적는다
                    │
                    v
                  null  끝

   결과  ["ownEnum", "inheritedEnum"]
   Object.keys(o) 는 첫 칸에서 멈춘다  ->  ["ownEnum"]
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 내 서랍 | own 프로퍼티 | `Object.hasOwn(o, k)` |
| 윗집 | `[[Prototype]]` | `Object.getPrototypeOf(o)` |
| 「올려도 됨」 스티커 | `enumerable: true` | `Object.getOwnPropertyDescriptor(o, k).enumerable` |
| 「목록에서 빼」 스티커 | `enumerable: false` | 같은 것이 `false` |
| 글자가 아닌 이름표 | 심볼 키 | `Object.getOwnPropertySymbols(o)` |
| 윗집까지 가는 조사원 | `for...in` | 이 주제의 격자에서 체인에 닿는 목록은 이것뿐 |
| 내 서랍만 보는 조사원들 | `Object.keys`·`entries`·`JSON.stringify`·`{...}`·`Object.assign` | 격자의 상속 세 줄이 전부 `.` |
| 「이 이름은 이미 봤다」 메모 | 명세의 「already been processed」 | own 비열거가 부모의 같은 이름을 가린다 |
| 조사원이 들르는 문을 세는 계기 | `Proxy` 트랩 로그 | 이 주제의 보조 창 |

> **열거 가능(enumerable)** — 프로퍼티마다 붙은 플래그 하나. 「키를 늘어놓는 문법」 대부분이 이것이 `true` 인 것만 늘어놓는다.\
> 예: `Object.defineProperty(o, "h", { value: 1 })` 로 만든 `h` 는 기본이 `false` 라 `Object.keys(o)` 에 안 나온다(14편).

> **체인 순회(chain walk)** — 자기 것을 다 본 뒤 `[[Prototype]]` 으로 올라가 윗집의 것을 이어 보는 것. `null` 에서 끝난다.\
> 예: `for (const k in Object.create({ p: 1 }))` 이 `"p"` 를 내놓는 것은 윗집까지 갔기 때문이다.

> **가리기(shadowing)** — 아래 칸의 이름이 윗칸의 같은 이름을 보이지 않게 하는 것. 열거에서는 **아래 칸 것이 비열거여도** 가린다.\
> 예: 자기 `shared` 가 `enumerable: false` 면 부모의 열거 가능한 `shared` 도 `for...in` 에 안 나온다.

## 이 주제가 답하려는 질문

1. **키를 늘어놓는 문법 아홉 개 중 누가 체인 위까지 가나** — 그리고 비열거·심볼은 각각 누구에게 보이나?
2. **`for...in` 의 순서와 중복 처리는 무엇이 정하나** — 13편의 세 덩어리와는 어떻게 이어지고, 같은 이름이 두 칸에 있으면?
3. **배열·`null`·순회 중 변경 같은 가장자리에서 무엇이 명세 보장이고 무엇이 이 엔진의 관찰인가?**

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 출력으로 읽는다.

### (1) ★★★ 체인 순회 격자 — 누가 무엇을 보나

**언제 쓰나** — 「이 객체를 복사/직렬화/순회했더니 **키 하나가 빠졌다(또는 더 나왔다)**」를 물을 때.
뷰마다 기준이 다르니 추측하지 말고 **여섯 종을 전부 대 본다.**

★★ **13편의 격자와 무엇이 다른가** — 13편은 `Object.keys`·`for...in`·`getOwnPropertyNames` 세 뷰를 상속 칸에 댔고
(`protoEnum` 은 `for-in` 에만 `true`), `JSON`·스프레드·`assign` 은 **own 쪽**만 찍었다.
여기서는 **아홉 열 전부를 상속 세 줄에** 대서 「체인에 닿는 열이 몇 개냐」를 센다. 그리고 순서·가리기·트랩을 더한다.

```js
// js16b-18a-grid.js
// ★★ 체인 순회 격자 -- 프로퍼티 종류 × 열거하는 문법. 누가 무엇을 보나를 전수로 찍는다.
// 13편의 격자는 own 키만 봤다. 여기서는 체인 위(상속된) 칸을 더한다.
const symOwn = Symbol("symOwn");
const symInh = Symbol("symInh");
const proto = { inheritedEnum: 1, [symInh]: 1 };
Object.defineProperty(proto, "inheritedHidden", { value: 1, enumerable: false });
const o = Object.create(proto);
o.ownEnum = 1;
o[symOwn] = 1;
Object.defineProperty(o, "ownHidden", { value: 1, enumerable: false });

const kinds = [
  ["own enumerable", "ownEnum"],
  ["own non-enumerable", "ownHidden"],
  ["own symbol", symOwn],
  ["inherited enumerable", "inheritedEnum"],
  ["inherited non-enumerable", "inheritedHidden"],
  ["inherited symbol", symInh],
];
const forIn = (x) => { const r = []; for (const k in x) r.push(k); return r; };
const views = [
  ["for-in", (x) => forIn(x)],
  ["keys", (x) => Object.keys(x)],
  ["entries", (x) => Object.entries(x).map(([k]) => k)],
  ["JSON", (x) => Object.keys(JSON.parse(JSON.stringify(x)))],
  ["{...}", (x) => Reflect.ownKeys({ ...x })],
  ["assign", (x) => Reflect.ownKeys(Object.assign({}, x))],
  ["gOPN", (x) => Object.getOwnPropertyNames(x)],
  ["ownKeys", (x) => Reflect.ownKeys(x)],
  ["in", (x) => kinds.map(([, k]) => k).filter((k) => k in x)],
];
console.log("[1] who sees what   (o = sees it, . = does not)");
console.log(("".padEnd(26) + views.map(([n]) => n.padEnd(9)).join("")).trimEnd());
const seen = views.map(([, f]) => f(o));
for (const [label, k] of kinds) {
  console.log((label.padEnd(26) + seen.map((s) => (s.includes(k) ? "o" : ".").padEnd(9)).join("")).trimEnd());
}
console.log(("seen".padEnd(26) + seen.map((s) => (s.length + "/6").padEnd(9)).join("")).trimEnd());
console.log("columns that reach the chain: " + JSON.stringify(views.filter((_, i) => seen[i].includes("inheritedEnum")).map(([n]) => n)));

console.log("");
console.log("[2] for-in order across two links");
const p2 = { b: 1, 2: 1, a: 1, 1: 1 };
const c2 = Object.create(p2);
c2.z = 1; c2[9] = 1; c2.y = 1; c2[3] = 1;
console.log("  Object.keys(parent)  " + JSON.stringify(Object.keys(p2)));
console.log("  Object.keys(child)   " + JSON.stringify(Object.keys(c2)));
console.log("  for-in child         " + JSON.stringify(forIn(c2)));

console.log("");
console.log("[3] own NON-enumerable key, parent enumerable key, same name");
const p3 = { shared: "from parent", other: "from parent" };
const c3 = Object.create(p3);
Object.defineProperty(c3, "shared", { value: "own, hidden", enumerable: false });
console.log("  for-in c3            " + JSON.stringify(forIn(c3)));
console.log("  'shared' in c3       " + ("shared" in c3) + "   c3.shared  " + c3.shared);

console.log("");
console.log("[4] trap log -- what for-in asks each link of the chain");
const L = [];
const tap = (name, t) => new Proxy(t, {
  ownKeys(t) { L.push(name + ".ownKeys"); return Reflect.ownKeys(t); },
  getOwnPropertyDescriptor(t, k) { L.push(name + ".gopd(" + String(k) + ")"); return Reflect.getOwnPropertyDescriptor(t, k); },
  getPrototypeOf(t) { L.push(name + ".getPrototypeOf"); return Reflect.getPrototypeOf(t); },
  get(t, k, r) { L.push(name + ".get(" + String(k) + ")"); return Reflect.get(t, k, r); },
});
const top = tap("P", { p: 1 });
const leaf = tap("C", Object.create(top, { c: { value: 1, enumerable: true } }));
L.length = 0; const got = forIn(leaf);
console.log("  for-in keys " + JSON.stringify(got));
console.log("  trap log    " + JSON.stringify(L));
L.length = 0; Object.keys(leaf);
console.log("  Object.keys trap log " + JSON.stringify(L));
```
```text
===== node20 js16b-18a-grid.js (exit=0) =====
[1] who sees what   (o = sees it, . = does not)
                          for-in   keys     entries  JSON     {...}    assign   gOPN     ownKeys  in
own enumerable            o        o        o        o        o        o        o        o        o
own non-enumerable        .        .        .        .        .        .        o        o        o
own symbol                .        .        .        .        o        o        .        o        o
inherited enumerable      o        .        .        .        .        .        .        .        o
inherited non-enumerable  .        .        .        .        .        .        .        .        o
inherited symbol          .        .        .        .        .        .        .        .        o
seen                      2/6      1/6      1/6      1/6      2/6      2/6      2/6      3/6      6/6
columns that reach the chain: ["for-in","in"]

[2] for-in order across two links
  Object.keys(parent)  ["1","2","b","a"]
  Object.keys(child)   ["3","9","z","y"]
  for-in child         ["3","9","z","y","1","2","b","a"]

[3] own NON-enumerable key, parent enumerable key, same name
  for-in c3            ["other"]
  'shared' in c3       true   c3.shared  own, hidden

[4] trap log -- what for-in asks each link of the chain
  for-in keys ["c","p"]
  trap log    ["C.ownKeys","C.getPrototypeOf","P.ownKeys","P.getPrototypeOf","C.gopd(c)","C.gopd(p)","C.getPrototypeOf","P.gopd(p)"]
  Object.keys trap log ["C.ownKeys","C.gopd(c)"]
```

```text
   [1] 을 두 덩어리로 접으면

                      own 칸에서 멈춘다                     체인을 걷는다
               ┌──────────────────────────────────┐   ┌───────────────┐
               keys  entries  JSON  {...}  assign  gOPN  ownKeys │   for-in     in
   own 열거      o      o      o     o      o      o     o      │     o        o
   own 비열거    .      .      .     .      .      o     o      │     .        o
   own 심볼      .      .      .     o      o      .     o      │     .        o
   ─────────────────────────────────────────────────────────────┼─────────────────
   상속 열거     .      .      .     .      .      .     .      │     o        o
   상속 비열거   .      .      .     .      .      .     .      │     .        o
   상속 심볼     .      .      .     .      .      .     .      │     .        o

   ★ 가로줄 아래(상속 세 줄)에 o 가 있는 열은 오른쪽 둘뿐이다
   ★ 그중 목록을 돌려주는 문법은 for-in 하나다 (in 은 이름을 하나씩 묻는 연산자다)
```

**그림 해설 — 한 덩어리에 한 문장.**

- ★★★ **`columns that reach the chain: ["for-in","in"]`** — 이 한 줄이 이 주제의 결론이다.
  `Object.keys`·`Object.entries`·`JSON.stringify`·스프레드·`Object.assign`·`getOwnPropertyNames`·`Reflect.ownKeys` 일곱 개는
  **상속 세 줄이 전부 `.`** 이다. 전부 **첫 칸(자기 서랍)에서 멈춘다.**
- ★★★ **`for-in` 은 `2/6`** — 「**문자열 키 ∧ 열거 가능**」이면 **own 이든 상속이든** 적는다.
  13편의 요약(「enumerable ∧ 문자열, own 을 안 따진다」)이 여섯 줄 전부에서 그대로 섰다.
- ★★ **`keys`·`entries`·`JSON` 은 한 몸이다** — 셋 다 `1/6`, 「**own ∧ 열거 가능 ∧ 문자열**」.
- ★★ **`{...}`·`assign` 은 `2/6` 인데 `for-in` 과 칸이 다르다** — 심볼을 가져가고 체인은 안 간다.
  11편의 「스프레드는 own 열거 가능만」에서 「**심볼 포함**」이 보태진 줄이다(13편 [2] 에도 같은 줄이 있다).
  ★ `for-in` 과 스프레드가 **둘 다 `2/6` 인데 겹치는 칸은 own 열거 한 칸뿐**이다 — 「개수가 같다」는 아무것도 말해 주지 않는다.
- ★★ **`gOPN` 은 플래그를 안 보고, `ownKeys` 는 플래그도 키 종류도 안 본다** — own 전수가 `Reflect.ownKeys` 다(`3/6`).
- ★ **`in` 은 `6/6`** — 이름 하나를 묻는 연산자라 **플래그도 심볼도 체인도 안 가린다.** 목록을 만드는 문법이 아니다.
- ★★ **심볼은 `for-in` 이 어느 칸에서도 안 적는다** — 명세 문장 그대로다 —
  "Returned property keys do not include keys that are Symbols."
  상속 심볼은 **열거 가능한데도** 안 나온다(`proto` 의 심볼은 리터럴로 만들어 열거 가능이다).

**`[2]` — 순서는 「own 세 덩어리, 그다음 부모의 세 덩어리」다.**

```text
   c2 (own)                      p2 (부모)
   ["3","9","z","y"]      ->     ["1","2","b","a"]
    정수↑   문자 삽입순            정수↑   문자 삽입순

   for-in c2  =  ["3","9","z","y",  "1","2","b","a"]
                  └── 자기 칸 ──┘   └── 윗칸 ──┘
   ★ 부모의 정수 키 "1","2" 가 자식의 문자 키 "z","y" 뒤에 온다
     -> 「정수 키가 먼저」는 칸 하나 안의 규칙이다. 체인 전체를 다시 정렬하지 않는다
```

- ★★★ **`for-in child` 는 `Object.keys(child)` 뒤에 `Object.keys(parent)` 를 이어 붙인 것과 글자가 같다.**
  13편의 세 덩어리(배열 인덱스 오름차순 → 문자열 삽입순)는 **칸마다 따로** 적용된다.
- ★★ 이 순서가 **명세로 못 박힌 것은 ES2020** 이다(for-in order 제안). 단 **Proxy 없는 평범한 체인**이라는 조건이 붙는다 — 동작 (2).

**`[3]` — own 비열거가 부모의 열거 가능 키를 가린다.**

```text
   c3        shared  (own, enumerable: false)   ── 이름 "shared" 를 처리했다고 기억
     │
     v
   p3        shared  (enumerable: true)   ── 이미 처리한 이름 -> 건너뛴다
             other   (enumerable: true)   ── 처음 보는 이름 -> 적는다

   for-in c3  =  ["other"]
   'shared' in c3 = true,  c3.shared = "own, hidden"   <- 조회는 own 을 읽는다 (15편)
```

- ★★★ **`for-in c3` 이 `["other"]` 다** — 부모의 `shared` 는 **열거 가능한데도** 안 나왔다.
  명세가 정확히 이것을 적어 두었다 —
  "a property of a prototype is not processed if it has the same name as a property that has already been processed" ·
  "The values of [[Enumerable]] attributes are not considered when determining if a property of a prototype object has already been processed."
- ★★ 즉 **「처리했다」와 「내놓았다」가 다르다.** own `shared` 는 **처리는 됐고(이름 기억) 내놓지는 않았다(비열거).**
  그 기억 때문에 윗칸의 같은 이름이 걸러진다.
- ★ `'shared' in c3` 가 `true` 이고 값이 `own, hidden` 인 것은 **15편의 조회 규칙** 그대로다 — own 이 이긴다.
  **열거에서 안 보이는 키가 조회에서는 보인다.** 둘은 다른 질문이다.

**비용** — 재지 않았다. 체인이 길 때의 열거 비용도, 뷰 사이의 속도 차이도 **이 문서에 한 줄도 없다.**

### (2) ★★ `for...in` 은 체인을 어떻게 걷나 — 트랩 로그와 명세 알고리즘

**언제 쓰나** — 「`for...in` 은 값을 읽나?」·「윗칸의 키를 언제 모으나?」처럼 **걷는 방식**을 물을 때.
격자(1)는 **무엇이 나오나**를 답하고, 이 절은 **어떻게 걸었나**를 답한다.

(1)의 블록 `[4]` 가 V8 의 로그다. 그 옆에 놓으려고 **명세의 `%ForInIteratorPrototype%.next` 단계를 이 문서가 직접 JS 생성기로 옮겨** 같은 체인에 돌렸다.
★ 그 생성기는 **검증 대상이지 정본이 아니다** — 정본은 명세 문장이다.

```js
// js16b-18f-refimpl.js
// 명세의 CreateForInIterator 알고리즘(%ForInIteratorPrototype%.next 의 단계)을 손으로 옮긴 생성기로
// 같은 두 칸 Proxy 체인을 걸어 본다 -- 18a [4] 의 V8 로그와 나란히 놓기 위한 것이다.
// ★ 이 생성기는 명세의 참고 코드를 옮긴 것이 아니라 알고리즘 단계를 이 문서가 직접 JS 로 적은 것이다(검증 대상이지 정본이 아니다).
const L = [];
const tap = (name, t) => new Proxy(t, {
  ownKeys(t) { L.push(name + ".ownKeys"); return Reflect.ownKeys(t); },
  getOwnPropertyDescriptor(t, k) { L.push(name + ".gopd(" + String(k) + ")"); return Reflect.getOwnPropertyDescriptor(t, k); },
  getPrototypeOf(t) { L.push(name + ".getPrototypeOf"); return Reflect.getPrototypeOf(t); },
  get(t, k, r) { L.push(name + ".get(" + String(k) + ")"); return Reflect.get(t, k, r); },
});
function* specForIn(start) {
  let obj = start;
  const visited = [];
  while (obj !== null) {
    const remaining = Reflect.ownKeys(obj).filter((k) => typeof k === "string");
    for (const key of remaining) {
      if (visited.includes(key)) continue;
      const desc = Reflect.getOwnPropertyDescriptor(obj, key);
      if (desc !== undefined) {
        visited.push(key);
        if (desc.enumerable) yield key;
      }
    }
    obj = Reflect.getPrototypeOf(obj);
  }
}
const top = tap("P", { p: 1 });
const leaf = tap("C", Object.create(top, { c: { value: 1, enumerable: true } }));

console.log("[1] the same two-link Proxy chain, walked two ways");
L.length = 0; const a = [...specForIn(leaf)]; const logA = L.slice();
console.log("spec algorithm keys  " + JSON.stringify(a));
console.log("spec algorithm log   " + JSON.stringify(logA) + "  (" + logA.length + " entries)");
L.length = 0; const b = []; for (const k in leaf) b.push(k); const logB = L.slice();
console.log("V8 for-in keys       " + JSON.stringify(b));
console.log("V8 for-in log        " + JSON.stringify(logB) + "  (" + logB.length + " entries)");
console.log("same keys? " + (JSON.stringify(a) === JSON.stringify(b)) + "   same log? " + (JSON.stringify(logA) === JSON.stringify(logB)));

console.log("");
console.log("[2] the 18d mutation rows, walked by the hand-ported spec algorithm and by V8's for-in");
const rows = [
  ["delete a not-yet-visited key (c) at a", () => ({ a: 1, b: 2, c: 3 }), (o, k) => { if (k === "a") delete o.c; }],
  ["delete the current key at each step", () => ({ a: 1, b: 2, c: 3 }), (o, k) => { delete o[k]; }],
  ["delete a parent key (p) before it comes", () => { const o = Object.create({ p: 1 }); o.a = 1; return o; },
   (o, k) => { if (k === "a") delete Object.getPrototypeOf(o).p; }],
  ["add a new own key (z) at a", () => ({ a: 1, b: 2 }), (o, k) => { if (k === "a") o.z = 26; }],
  ["add a new integer key (0) at a", () => ({ a: 1, b: 2 }), (o, k) => { if (k === "a") o[0] = 0; }],
  ["add a parent key (q) at a", () => { const o = Object.create({}); o.a = 1; o.b = 2; return o; },
   (o, k) => { if (k === "a") Object.getPrototypeOf(o).q = 1; }],
  ["delete then re-add b at a", () => ({ a: 1, b: 2, c: 3 }), (o, k) => { if (k === "a") { delete o.b; o.b = 2; } }],
];
for (const [label, setup, onKey] of rows) {
  const o1 = setup(); const s = []; for (const k of specForIn(o1)) { s.push(k); onKey(o1, k); }
  const o2 = setup(); const v = []; for (const k in o2) { v.push(k); onKey(o2, k); }
  console.log(label.padEnd(42) + "spec " + JSON.stringify(s).padEnd(18) + "V8 " + JSON.stringify(v).padEnd(18) +
    (JSON.stringify(s) === JSON.stringify(v) ? "same" : "DIFFERENT"));
}
```
```text
===== node20 js16b-18f-refimpl.js (exit=0) =====
[1] the same two-link Proxy chain, walked two ways
spec algorithm keys  ["c","p"]
spec algorithm log   ["C.ownKeys","C.gopd(c)","C.getPrototypeOf","P.ownKeys","P.gopd(p)","P.getPrototypeOf"]  (6 entries)
V8 for-in keys       ["c","p"]
V8 for-in log        ["C.ownKeys","C.getPrototypeOf","P.ownKeys","P.getPrototypeOf","C.gopd(c)","C.gopd(p)","C.getPrototypeOf","P.gopd(p)"]  (8 entries)
same keys? true   same log? false

[2] the 18d mutation rows, walked by the hand-ported spec algorithm and by V8's for-in
delete a not-yet-visited key (c) at a     spec ["a","b"]         V8 ["a","b"]         same
delete the current key at each step       spec ["a","b","c"]     V8 ["a","b","c"]     same
delete a parent key (p) before it comes   spec ["a"]             V8 ["a"]             same
add a new own key (z) at a                spec ["a","b"]         V8 ["a","b"]         same
add a new integer key (0) at a            spec ["a","b"]         V8 ["a","b"]         same
add a parent key (q) at a                 spec ["a","b","q"]     V8 ["a","b"]         DIFFERENT
delete then re-add b at a                 spec ["a","b","c"]     V8 ["a","b","c"]     same
```

```text
   같은 두 칸 체인 (C -> P), 같은 결과 ["c","p"], 다른 발자국

   명세 알고리즘(손으로 옮긴 것) -- 한 칸씩 끝내고 올라간다
     C.ownKeys  C.gopd(c)  C.getPrototypeOf  |  P.ownKeys  P.gopd(p)  P.getPrototypeOf
     └──── C 칸 처리 ─────┘                     └──── P 칸 처리 ─────┘              (6)

   V8 for-in -- 먼저 체인 끝까지 키를 모으고, 그다음 키마다 확인한다
     C.ownKeys  C.getPrototypeOf  P.ownKeys  P.getPrototypeOf  |  C.gopd(c)  C.gopd(p)  C.getPrototypeOf  P.gopd(p)
     └────────────── 키 모으기 ──────────────┘                     └──────── 키마다 "아직 있나" ────────┘   (8)
```

- ★★★ **키는 같고 로그가 다르다**(`same keys? true   same log? false`). 그리고 **둘 다 명세 위반이 아니다.**
  순서 제약은 "if neither obj nor any object in its prototype chain is a Proxy exotic object …" 일 때만 걸린다 —
  **체인에 `Proxy` 가 있으면 `CreateForInIterator` 처럼 굴 의무가 없다.** 그래서 트랩 순서는 **V8 의 관찰**이다.
- ★★ **명세가 요구하는 것은 트랩의 종류다** — "must obtain the own property keys of the target object by calling its [[OwnPropertyKeys]] internal method" ·
  "Property attributes of the target object must be obtained by calling its [[GetOwnProperty]] internal method."
  두 로그 모두 **`ownKeys` 와 `gopd` 를 칸마다** 부른다. 윗칸으로 가려면 `getPrototypeOf` 도 불가피하다.
- ★★ **`get` 이 한 줄도 없다** — 두 로그 모두. `for...in` 은 **키만 내놓고 값을 안 읽는다.**
  값은 몸통의 `o[k]` 가 읽는다(그때 15편의 조회가 따로 일어난다).
- ★ V8 쪽의 **`C.gopd(p)`** 가 눈여겨볼 줄이다 — 윗칸 키 `p` 를 내놓기 전에 **아래 칸에 같은 이름이 생겼나를 다시 확인**한 것으로 읽힌다.
  (이것은 로그에서 나온 **추론**이다. V8 소스는 안 열었다.)
- ★ **`Object.keys` 트랩 로그는 `["C.ownKeys","C.gopd(c)"]` 두 줄**이다((1)의 `[4]` 끝줄) —
  **`getPrototypeOf` 가 아예 없다.** 격자가 「keys 는 첫 칸에서 멈춘다」고 한 것을 발자국으로 다시 본 것이다.

**비용** — 재지 않았다. 「키를 먼저 다 모으는 쪽이 빠르다/느리다」는 **이 로그로 말할 수 없다.**

### (3) ★★★ 배열에 `for...in` — 인덱스가 문자열이고, 붙인 것이 섞여 나온다

**언제 쓰나** — 배열을 `for (const i in arr)` 로 돌리고 싶어질 때. **거의 항상 쓰지 않을 이유를 여기서 본다.**

```js
// js16b-18b-array.js
// 배열에 for-in 을 쓰면 무엇이 나오나.
const forIn = (x) => { const r = []; for (const k in x) r.push(k); return r; };
const arr = ["a", "b", , "d"];
const show = (v) => (v === undefined ? "<undefined>" : v);

console.log("[1] what are the keys?");
for (const i in arr) { console.log("  i=" + JSON.stringify(i) + "  typeof " + typeof i + "  i + 1 = " + JSON.stringify(i + 1)); }
console.log("  for-of values  " + JSON.stringify([...arr].map(show)) + "   <- the hole at 2 is visited by for-of, skipped by for-in");

console.log("");
console.log("[2] an extra property and a prototype extension");
arr.extra = "attached";
Array.prototype.polluted = function () {};
console.log("  for-in arr          " + JSON.stringify(forIn(arr)));
console.log("  for-in []           " + JSON.stringify(forIn([])));
console.log("  for-of arr          " + JSON.stringify([...arr].map(show)));
console.log("  Object.keys(arr)    " + JSON.stringify(Object.keys(arr)));
const guarded = []; for (const k in arr) if (Object.hasOwn(arr, k)) guarded.push(k);
console.log("  for-in + hasOwn     " + JSON.stringify(guarded));
delete Array.prototype.polluted;

console.log("");
console.log("[3] the same extension, defined non-enumerable");
Object.defineProperty(Array.prototype, "quiet", { value: function () {}, enumerable: false, configurable: true, writable: true });
console.log("  for-in arr          " + JSON.stringify(forIn(arr)));
console.log("  typeof arr.quiet    " + typeof arr.quiet);
delete Array.prototype.quiet;

console.log("");
console.log("[4] built-in methods and length");
console.log("  'map' in arr        " + ("map" in arr) + "   enumerable? " + Object.getOwnPropertyDescriptor(Array.prototype, "map").enumerable);
console.log("  'length' in arr     " + ("length" in arr) + "   enumerable? " + Object.getOwnPropertyDescriptor(arr, "length").enumerable);
```
```text
===== node20 js16b-18b-array.js (exit=0) =====
[1] what are the keys?
  i="0"  typeof string  i + 1 = "01"
  i="1"  typeof string  i + 1 = "11"
  i="3"  typeof string  i + 1 = "31"
  for-of values  ["a","b","<undefined>","d"]   <- the hole at 2 is visited by for-of, skipped by for-in

[2] an extra property and a prototype extension
  for-in arr          ["0","1","3","extra","polluted"]
  for-in []           ["polluted"]
  for-of arr          ["a","b","<undefined>","d"]
  Object.keys(arr)    ["0","1","3","extra"]
  for-in + hasOwn     ["0","1","3","extra"]

[3] the same extension, defined non-enumerable
  for-in arr          ["0","1","3","extra"]
  typeof arr.quiet    function

[4] built-in methods and length
  'map' in arr        true   enumerable? false
  'length' in arr     true   enumerable? false
```

```text
   arr = ["a", "b", <구멍>, "d"]  +  arr.extra  +  Array.prototype.polluted

             "0"  "1"  (2)  "3"   "extra"         "polluted"
   for-in     o    o    .    o      o                o        <- 전부 문자열, 구멍은 건너뜀, 체인까지 감
   Object.keys o   o    .    o      o                .        <- own 만
   for-of    "a"  "b" undef "d"     .                .        <- 인덱스 0..length-1 의 값 (19편)
```

- ★★★ **인덱스가 문자열이다** — `typeof string` 이고 `i + 1` 이 **`"01"`·`"11"`·`"31"`** 이다. 덧셈이 아니라 이어 붙이기다.
  배열 인덱스도 **프로퍼티 키**이고, 프로퍼티 키는 문자열(또는 심볼)이기 때문이다(13편).
- ★★ **구멍(2번 자리)은 `for-in` 이 건너뛰고 `for-of` 는 `<undefined>` 로 방문한다.** 구멍은 「값이 `undefined` 인 칸」이 아니라 **프로퍼티가 없는 칸**이다.
  `for-in` 은 **있는 프로퍼티**를, `for-of` 는 **인덱스 범위**를 돈다 — 무엇을 도는지가 다르다(`for-of` 의 규칙은 19편).
- ★★★ **유명한 함정** — `for-in arr` 에 **`"extra"`(배열에 붙인 것)와 `"polluted"`(`Array.prototype` 에 붙인 것)가 섞여 나온다.**
  그리고 **빈 배열에서도 `["polluted"]`** 다. 누군가 프로토타입을 건드리면 **모든 배열의 `for-in`** 이 바뀐다.
- ★★ **`Object.hasOwn` 가드**가 `polluted` 는 거르지만 **`extra` 는 못 거른다** — 그것은 진짜 own 이기 때문이다.
  가드는 **「체인에서 온 것」만** 거른다. 「인덱스만」을 원하면 가드가 아니라 **`for...of` 나 인덱스 루프**를 쓴다.
- ★★ **`[3]` 같은 확장을 `enumerable: false` 로 정의하면 `for-in` 에 안 나온다** — 그런데 `typeof arr.quiet` 는 `function` 이다.
  조회에는 보이고 열거에는 안 보인다((1)의 `[3]` 과 같은 이야기다).
- ★ **`[4]` 내장 `map` 과 `length` 가 `for-in` 에 안 나오는 이유가 정확히 그것이다** — `'map' in arr` 가 `true` 인데 `enumerable? false` 다.
  내장 메서드가 전부 비열거라 **평소에는 함정이 안 보이는 것**이고, 누가 **대입으로** 붙이는 순간 드러난다.

**비용** — 재지 않았다. 배열 `for-in` 을 피하는 이유는 이 절의 **의미 차이**이지 속도가 아니다.

### (4) ★★ `hasOwnProperty` 대 `Object.hasOwn` — 그리고 `for...in` 이 받는 이상한 값

**언제 쓰나** — `for...in` 몸통에 가드를 넣을 때, 그리고 **`null` 일 수도 있는 값**을 `for...in` 에 넘길 때.

```js
// js16b-18c-hasown.js
// hasOwnProperty 대 Object.hasOwn(ES2022) -- 그리고 for-in 이 받는 이상한 값들.
const run = (label, fn) => {
  let r;
  try { r = "-> " + String(fn()); } catch (e) { r = "-> " + e.constructor.name + " " + e.message; }
  console.log(label.padEnd(66) + r);
};
const forIn = (x) => { const r = []; for (const k in x) r.push(k); return JSON.stringify(r); };

console.log("[1] three unusual objects, three ways to ask own-ness");
const bare = Object.create(null); bare.k = 1;
const liar = { k: 1, hasOwnProperty() { return false; } };
const shadowed = { k: 1, hasOwnProperty: 42 };
for (const [name, o] of [["Object.create(null)", bare], ["own hasOwnProperty() {return false}", liar], ["own hasOwnProperty: 42", shadowed]]) {
  run(name + "  o.hasOwnProperty('k')", () => o.hasOwnProperty("k"));
  run(name + "  Object.hasOwn(o, 'k')", () => Object.hasOwn(o, "k"));
  run(name + "  Object.prototype.hasOwnProperty.call", () => Object.prototype.hasOwnProperty.call(o, "k"));
}

console.log("");
console.log("[2] for-in over Object.create(null)");
const bare2 = Object.create(null); bare2.x = 1; bare2.y = 2;
run("for-in bare2", () => forIn(bare2));

console.log("");
console.log("[3] a symbol key and for-in");
const withSym = { visible: 1, [Symbol("hidden")]: 2 };
run("for-in withSym", () => forIn(withSym));
run("Object.getOwnPropertySymbols(withSym).length", () => Object.getOwnPropertySymbols(withSym).length);

console.log("");
console.log("[4] for-in over primitives, null and undefined");
run("for-in 'ab'", () => forIn("ab"));
run("for-in 42", () => forIn(42));
run("for-in true", () => forIn(true));
run("for-in null", () => forIn(null));
run("for-in undefined", () => forIn(undefined));
run("Object.keys(null)  (for contrast)", () => Object.keys(null));
```
```text
===== node20 js16b-18c-hasown.js (exit=0) =====
[1] three unusual objects, three ways to ask own-ness
Object.create(null)  o.hasOwnProperty('k')                        -> TypeError o.hasOwnProperty is not a function
Object.create(null)  Object.hasOwn(o, 'k')                        -> true
Object.create(null)  Object.prototype.hasOwnProperty.call         -> true
own hasOwnProperty() {return false}  o.hasOwnProperty('k')        -> false
own hasOwnProperty() {return false}  Object.hasOwn(o, 'k')        -> true
own hasOwnProperty() {return false}  Object.prototype.hasOwnProperty.call-> true
own hasOwnProperty: 42  o.hasOwnProperty('k')                     -> TypeError o.hasOwnProperty is not a function
own hasOwnProperty: 42  Object.hasOwn(o, 'k')                     -> true
own hasOwnProperty: 42  Object.prototype.hasOwnProperty.call      -> true

[2] for-in over Object.create(null)
for-in bare2                                                      -> ["x","y"]

[3] a symbol key and for-in
for-in withSym                                                    -> ["visible"]
Object.getOwnPropertySymbols(withSym).length                      -> 1

[4] for-in over primitives, null and undefined
for-in 'ab'                                                       -> ["0","1"]
for-in 42                                                         -> []
for-in true                                                       -> []
for-in null                                                       -> []
for-in undefined                                                  -> []
Object.keys(null)  (for contrast)                                 -> TypeError Cannot convert undefined or null to object
```

- ★★★ **`o.hasOwnProperty('k')` 가 틀리는 객체 셋** —
  `Object.create(null)` 은 **`TypeError`**(빌려 올 윗집이 없다), 자기 `hasOwnProperty()` 를 가진 객체는 **거짓말(`false`)**,
  `hasOwnProperty: 42` 로 가려진 객체는 **`TypeError`** 다.
  ★★ **세 줄 모두 `Object.hasOwn` 과 `Object.prototype.hasOwnProperty.call` 은 `true`** 다 — 둘 다 **객체에게 묻지 않고 밖에서 묻기** 때문이다.
  ★ 15편이 「이름이 섀도잉되어 있으면 엉뚱한 함수가 불린다 — 따로 안 던져 봤다」고 남긴 자리를 **여기서 던졌다** —
  거짓말 줄과 `42` 줄이 그것이다.
- ★★ **`Object.create(null)` 에도 `for-in` 은 된다**(`["x","y"]`). `for-in` 은 **문**이라 객체의 메서드를 안 빌린다.
  윗집이 없으니 **상속된 키가 섞일 걱정도 없다** — 그래서 사전용 객체와 `for-in` 은 궁합이 맞다.
- ★ **심볼 키는 이번에도 안 나온다**(`["visible"]`, 심볼은 `getOwnPropertySymbols` 로 1개).
- ★★★ **`[4]` 원시값·`null`·`undefined` 에 `for-in` 은 예외가 없다.**
  `'ab'` 은 `["0","1"]`(문자열 래퍼의 인덱스), `42`·`true` 는 `[]`, **`null`·`undefined` 도 `[]`** 다.
  ★★★ **그런데 `Object.keys(null)` 은 `TypeError`** 다. 같은 「키 목록」인데 한쪽은 조용하고 한쪽은 던진다.

```text
   for (k in X)  --  ForIn/OfHeadEvaluation

   X 가 undefined 나 null 인가?
     ├─ 예  ──▶  break 완료를 돌려준다  ──▶  몸통이 한 번도 안 돈다   (예외 아님)
     └─ 아니오 ──▶  ToObject(X)  ──▶  EnumerateObjectProperties
                     'ab' -> String 래퍼 (인덱스 "0","1")
                     42   -> Number 래퍼 (열거 가능한 own 없음)

   Object.keys(X)  --  ToObject(X) 를 먼저 한다  ──▶  null 이면 TypeError 로 막힌다
```

- ★★ **명세가 그 갈림을 적어 두었다** — `ForIn/OfHeadEvaluation` 은 열거(enumerate)일 때 값이 `undefined` 나 `null` 이면
  **break 완료**를 돌려준다. 예외가 아니라 「**루프를 끝냈다**」다.
  ★ 그래서 `for-in` 은 **`null` 을 조용히 삼킨다.** 실수로 `null` 을 넘겨도 **아무 신호가 없다** — 어디서 틀리나 (5).

### (5) ★★★ 순회 중 추가·삭제 — 명세 문구와 이 판의 관찰을 가른다

**언제 쓰나** — `for (k in o)` 몸통에서 `delete o[k]` 나 `o.x = …` 를 할 때. **무엇이 보장이고 무엇이 우연인지**가 전부다.

```js
// js16b-18d-mutate.js
// 순회 도중 프로퍼티를 지우거나 더하면 -- 명세가 보장하는 행과 이 판의 관찰일 뿐인 행을 본문에서 가른다.
const trial = (label, setup, onKey) => {
  const o = setup();
  const visited = [];
  for (const k in o) { visited.push(k); onKey(o, k); }
  console.log(label.padEnd(44) + "visited " + JSON.stringify(visited).padEnd(26) + "keys after " + JSON.stringify(Object.keys(o)));
};

console.log("[1] deleting during for-in");
trial("delete a not-yet-visited key (c) at a", () => ({ a: 1, b: 2, c: 3 }), (o, k) => { if (k === "a") delete o.c; });
trial("delete the current key at each step", () => ({ a: 1, b: 2, c: 3 }), (o, k) => { delete o[k]; });
trial("delete a parent key (p) before it comes", () => { const o = Object.create({ p: 1 }); o.a = 1; return o; },
      (o, k) => { if (k === "a") delete Object.getPrototypeOf(o).p; });

console.log("");
console.log("[2] adding during for-in");
trial("add a new own key (z) at a", () => ({ a: 1, b: 2 }), (o, k) => { if (k === "a") o.z = 26; });
trial("add a new integer key (0) at a", () => ({ a: 1, b: 2 }), (o, k) => { if (k === "a") o[0] = 0; });
trial("add a parent key (q) at a", () => { const o = Object.create({}); o.a = 1; o.b = 2; return o; },
      (o, k) => { if (k === "a") Object.getPrototypeOf(o).q = 1; });
trial("delete then re-add b at a", () => ({ a: 1, b: 2, c: 3 }), (o, k) => { if (k === "a") { delete o.b; o.b = 2; } });

console.log("");
console.log("[3] the same delete, with Object.keys(...).forEach");
const snap = { a: 1, b: 2, c: 3 };
const seenVals = [];
Object.keys(snap).forEach((k, i) => { if (i === 0) delete snap.c; seenVals.push(k + "=" + snap[k]); });
console.log("Object.keys(snap).forEach, delete c at a    " + JSON.stringify(seenVals));
```
```text
===== node20 js16b-18d-mutate.js (exit=0) =====
[1] deleting during for-in
delete a not-yet-visited key (c) at a       visited ["a","b"]                 keys after ["a","b"]
delete the current key at each step         visited ["a","b","c"]             keys after []
delete a parent key (p) before it comes     visited ["a"]                     keys after ["a"]

[2] adding during for-in
add a new own key (z) at a                  visited ["a","b"]                 keys after ["a","b","z"]
add a new integer key (0) at a              visited ["a","b"]                 keys after ["0","a","b"]
add a parent key (q) at a                   visited ["a","b"]                 keys after ["a","b"]
delete then re-add b at a                   visited ["a","b","c"]             keys after ["a","c","b"]

[3] the same delete, with Object.keys(...).forEach
Object.keys(snap).forEach, delete c at a    ["a=1","b=2","c=undefined"]
```

명세에는 **문장이 두 겹**이다.

- **첫 겹 — 모든 객체에 걸리는 일반 규칙**(`EnumerateObjectProperties`) —
  "A property that is deleted before it is processed by the iterator's next method is ignored." ·
  "If new properties are added to the target object during enumeration, the newly added properties are not guaranteed to be processed in the active enumeration." ·
  "A property name will be returned by the iterator's next method at most once in any enumeration."
- ★★★ **둘째 겹 — Proxy 없는 평범한 체인에만 걸리는 순서 제약**(ES2020) — 반복자는 `CreateForInIterator` 처럼 굴어야 한다,
  **다음 넷 중 하나가 일어날 때까지** —
  「obj 나 체인 위 객체의 `[[Prototype]]` 이 바뀐다」 · 「obj 나 체인 위 객체에서 **프로퍼티가 지워진다**」 ·
  「**체인 위 객체에** 프로퍼티가 더해진다」 · 「`[[Enumerable]]` 이 바뀐다」.
  ★★★ **목록에 「obj 자신에 더해진다」가 없다.** 그리고 `CreateForInIterator` 는 칸에 처음 들를 때 **그 칸의 own 키를 한 번 떠 두고** 그것만 돈다.

```text
   for (k in o) { ... o.z = 26 ... }      o 는 평범한 객체, 체인에 Proxy 없음

   시작    o 칸의 키를 떠 둔다   ["a","b"]
   k="a"   몸통에서 o.z = 26    <- 「obj 자신에 추가」는 제약을 푸는 사건이 아니다
   k="b"   떠 둔 목록대로 진행
   끝      z 는 목록에 없었다  ->  방문 안 함   ★ 제약이 살아 있으니 명세가 묶은 결과

   for (k in o) { ... proto.q = 1 ... }
   k="a"   몸통에서 윗칸에 q 추가  <- 「체인 위 객체에 추가」 = 제약이 풀린다
   이후    일반 규칙만 남는다: "not guaranteed to be processed"   ★ 어느 쪽이든 적법
```

그래서 일곱 행을 이렇게 가른다. **「명세 알고리즘」 열은 (2)의 생성기로 같은 행을 돌린 것**이다(18f `[2]`).

| 행 | 이 판(V8) | 명세 알고리즘 | 칸 | 근거 |
|---|---|---|---|---|
| 처리 전의 `c` 를 `a` 에서 지운다 | `["a","b"]` | `["a","b"]` | ★★★ **명세 보장** | 「deleted before it is processed … is ignored」 |
| 매번 지금 키를 지운다 | `["a","b","c"]` | `["a","b","c"]` | ★★ **집합은 보장 · 순서는 관찰** | 지운 것은 전부 **이미 처리된** 키다. 첫 삭제로 순서 제약은 풀린다 |
| 윗칸의 `p` 를 오기 전에 지운다 | `["a"]` | `["a"]` | ★ **보장으로 읽힌다(해석)** | 문장이 직접 말하는 것은 **대상 객체**다. 다만 윗칸은 「프로토타입을 넘겨 `EnumerateObjectProperties` 를 부른」 열거의 **대상**이 되므로 같은 문장이 걸린다고 읽었다 |
| 자기에게 `z` 를 더한다 | `["a","b"]` | `["a","b"]` | ★★★ **명세가 묶는다(둘째 겹)** | 「obj 자신에 추가」는 제약을 안 푼다 → 떠 둔 키 목록대로 → `z` 없음 |
| 자기에게 정수 키 `0` 을 더한다 | `["a","b"]` | `["a","b"]` | ★★★ **명세가 묶는다(둘째 겹)** | 같은 이유. **정렬상 맨 앞 키인데도** 안 나온다 |
| 윗칸에 `q` 를 더한다 | `["a","b"]` | **`["a","b","q"]`** | ★★★ **관찰** — 명세 비보장 | 「체인 위 객체에 추가」가 제약을 푼다 → 일반 규칙 「not guaranteed」 뿐 |
| `b` 를 지우고 다시 넣는다 | `["a","b","c"]` | `["a","b","c"]` | ★★ **관찰** — 명세 비보장 | 삭제가 제약을 푼다. 다시 넣은 `b` 는 「새로 더한 것」이라 보장 없음 |

- ★★★ **`윗칸에 q` 행이 증거다** — 명세 알고리즘은 `q` 를 방문했고 **V8 은 안 했다**(`DIFFERENT`).
  제약이 풀린 행이라 **둘 다 적법**하다. 「V8 에서 안 나왔으니 안 나온다」로 적으면 틀린다.
- ★★ **「추가는 명세가 안 묶는다」는 윗칸 추가와 지웠다 다시 넣기에만 맞는 말**이다.
  자기 자신에 더한 두 행은 **둘째 겹이 묶는다** — 탐침의 `[2]` 라벨이 「보장 / 비보장」을 한데 말하지 않는 이유다.
- ★★ **지웠다 다시 넣은 `b` 는 방문됐는데, 방문 순서는 `a,b,c` 이고 끝난 뒤 키 순서는 `a,c,b` 다.**
  V8 이 **시작할 때 뜬 목록의 순서**대로 가면서 「아직 있나」만 확인한 것으로 읽힌다(로그 (2)의 추론과 같은 결). **관찰이다.**
- ★★★ **`[3]` `Object.keys(...).forEach` 는 스냅숏이다** — 도중에 지운 `c` 도 `c=undefined` 로 **방문된다.**
  `for-in` 은 **처리 전 삭제를 건너뛰고**, `Object.keys` 는 **이미 만든 배열을 돈다.** 삭제에 대한 반응이 정반대다.

**비용** — 재지 않았다.

### (6) ★★ 클래스 메서드는 왜 `for...in` 에 안 나오나 — 16편과 잇는다

**언제 쓰나** — 인스턴스를 `for...in` 으로 돌렸더니 **메서드가 안 나온다**(또는 옛 코드에서는 **나온다**).

**16편이 이미 찍었다**([16 — `class` 문법](../16-class-syntax/2-summary.md)의 `js16b-16a-where.js` `[4]`) —
`class C { method() {} }` 는 **`enumerable false`**, 게터·정적 메서드도 **`false`**,
**필드**(`field = ...`)와 **정적 필드**는 **`true`**, 객체 리터럴의 메서드와 **`Old.prototype.method = function`** 은 **`true`** 다.
그리고 `Object.keys(C.prototype)` 이 `[]`, `Object.keys(Old.prototype)` 이 `["method"]` 다.

```text
   인스턴스 i 를 for (k in i) 로 돌리면

   class C { field = 1; method() {} }        function Old() { this.field = 1 }
                                              Old.prototype.method = function () {}

   i       field   (열거 가능) -> 나온다     i       field   (열거 가능) -> 나온다
    │                                         │
   C.prototype  method (비열거) -> 안 나온다  Old.prototype  method (열거 가능) -> ★ 나온다

   for-in i  ->  ["field"]                    for-in i  ->  ["field", "method"]
```

- ★★★ 이 그림은 **16편의 플래그 표 + 이 문서의 격자**를 합친 **추론**이다 — 두 인스턴스에 `for-in` 을 직접 던진 줄은 이 배치에 없다.
  근거가 되는 칸은 둘 다 실측이다 — 「`for-in` 은 상속 열거 가능을 적는다」((1)) · 「클래스 메서드는 비열거, 대입한 프로토타입 메서드는 열거 가능」(16편).
- ★★ **`class` 로 바꾸면 `for...in` 의 결과가 조용히 바뀐다** — 옛 생성자 함수 코드를 클래스로 옮길 때 `for-in` 에 기대던 곳이 있으면 거기서 드러난다.

## 문법 — 형태와 규칙

```text
   for (const k in X) 문장

   X 가 null / undefined       -> 몸통을 한 번도 안 돈다 (예외 아님)
   X 가 원시값                  -> 래퍼 객체로 바꿔 돈다
   k 에 들어오는 것             -> ★ 문자열 키뿐 (심볼 없음, 배열 인덱스도 문자열)
   무엇을 적나                  -> 열거 가능 ∧ 문자열 ∧ (own 이든 상속이든)
   어떤 순서로                  -> 자기 칸의 세 덩어리 순서 (13편) -> 윗칸 -> 그 윗칸 ...
   같은 이름이 윗칸에 또 있으면  -> 건너뛴다 (아래 칸 것이 비열거여도)
   값을 읽나                    -> 안 읽는다 (몸통의 o[k] 가 읽는다)

   가드
   Object.hasOwn(o, k)          -> 체인에서 온 것만 거른다 (ES2022)
   Object.prototype.hasOwnProperty.call(o, k)   -> 같은 질문의 옛 관용구
   o.hasOwnProperty(k)          -> ★ 체인으로 빌려 오는 호출. 세 객체에서 틀린다
```

- **`for...in` 은 「열거 가능한 문자열 키」를 체인 끝까지 모아 한 번씩 내놓는다.**
- **own 이 먼저, 윗칸이 나중이고, 칸 안의 순서는 13편의 세 덩어리다** — Proxy 없는 체인에서 ES2020 부터 명세다.
- **윗칸의 키는 같은 이름이 이미 처리됐으면 건너뛴다.** 처리됐다는 판정에 `enumerable` 은 안 본다.
- **순회 중 처리 전에 지운 키는 안 나온다.** 더한 키는 **평범한 객체 자신에 더했을 때만** 안 나온다는 것이 묶이고, 나머지는 보장이 없다.
- **`null`·`undefined` 는 조용히 0회, 원시값은 래퍼로 돈다.** `Object.keys` 는 `null`·`undefined` 에서 `TypeError` 다.
- **키 목록을 own 에서 멈추게 하려면 `Object.keys` 를 쓰고, 체인에서 온 것만 빼려면 `Object.hasOwn` 가드를 쓴다.**

## 어디서 틀리나

### (1) ★★★ 배열을 `for...in` 으로 돈다

인덱스가 **문자열**이라 `i + 1` 이 `"01"` 이 되고, **구멍은 건너뛰고**, **배열에 붙인 것(`extra`)과 `Array.prototype` 에 붙인 것(`polluted`)이 섞여 나온다.**
빈 배열에서도 `["polluted"]` 다. ★ 처방은 가드가 아니라 **`for...of`**(값) 또는 인덱스 루프다 — `hasOwn` 가드는 `extra` 를 못 거른다.

### (2) ★★★ 「비열거로 바꾸면 부모 것이 보인다」고 기대한다

**반대다.** own 비열거 `shared` 는 **이름을 처리한 것으로 쳐서** 부모의 열거 가능한 `shared` 까지 가린다(`["other"]`).
「내가 안 보이면 윗집 것이라도 보이겠지」가 틀린다. 명세가 `[[Enumerable]]` 을 **판정에 안 쓴다**고 적었다.

### (3) ★★★ 「스프레드·`Object.assign`·`JSON.stringify` 도 `for...in` 처럼 상속을 가져간다」

**안 가져간다.** 격자의 상속 세 줄이 그 열들에서 전부 `.` 이다. 체인에 닿는 목록은 `for-in` 하나다.
★ 그래서 `Object.create(defaults)` 로 기본값을 체인에 두고 `{ ...o }` 로 복사하면 **기본값이 통째로 사라진다** — 격자의 `inherited enumerable` 줄 `{...}` 칸이 바로 그 모양이다.

### (4) ★★ `o.hasOwnProperty(k)` 를 가드로 쓴다

`Object.create(null)` 에서 `TypeError`, 자기 `hasOwnProperty` 가 있으면 **거짓말**, `42` 로 가려지면 `TypeError` 다.
★ **`Object.hasOwn(o, k)`**(ES2022) 또는 `Object.prototype.hasOwnProperty.call(o, k)` 를 쓴다.

### (5) ★★ `for...in` 이 `null` 을 알려 줄 거라 믿는다

**안 알려 준다.** `for-in null`·`for-in undefined` 는 **몸통이 0회**이고 예외가 없다(명세의 break 완료).
「설정이 비었다」와 「설정 객체가 아예 `null` 이다」가 **같은 결과**가 된다. ★ 필요하면 루프 전에 **직접 검사**한다 —
`Object.keys(x)` 로 바꾸면 `null` 에서 `TypeError` 로 **시끄럽게** 실패한다.

### (6) ★★★ 순회 중 추가한 키가 「안 나온다」를 규칙으로 외운다

**반만 맞다.** 평범한 객체 **자신에** 더한 키는 명세(둘째 겹)가 「안 나온다」로 묶는다.
그러나 **윗칸에 더했거나, 지운 뒤 다시 넣었거나, 체인에 `Proxy` 가 있으면** 명세는 아무것도 약속하지 않는다 —
명세 알고리즘은 윗칸의 `q` 를 **방문했고** V8 은 **안 했다.** ★★ 순회 중 구조를 바꿔야 하면 **`Object.keys(o)` 로 스냅숏을 먼저 뜬다.**

### (7) ★★ `Object.keys(...).forEach` 도 삭제를 건너뛸 거라 믿는다

**아니다 — 스냅숏이다.** 도중에 지운 `c` 가 `c=undefined` 로 방문됐다. `for-in` 과 **정반대**다.
★ 스냅숏 위에서 지울 수 있다면 **몸통에서 `Object.hasOwn(o, k)` 로 아직 있나를 다시 묻는다.**

### (8) ★★ 심볼 키가 `for...in` 에 나올 거라 기대한다

**어느 칸에서도 안 나온다** — 열거 가능이어도, own 이어도. 명세 문장 "do not include keys that are Symbols" 그대로다.
★ 심볼까지 원하면 `Reflect.ownKeys`(own 전수) — 그리고 **스프레드·`assign` 은 심볼을 가져간다**(격자의 `own symbol` 줄).

### (9) ★ 트랩 로그의 순서를 명세로 적는다

체인에 `Proxy` 가 있으면 순서 제약이 **아예 안 걸린다.** V8 은 **키를 먼저 다 모으고** 확인했고, 명세 알고리즘은 **칸마다 끝내고** 올라갔다.
★ 명세가 요구하는 것은 **`ownKeys`·`gopd` 를 부른다**는 것까지다.

### (10) ★ 「`for...in` 은 느리다」를 근거 없이 옮긴다

★★★ **이 문서는 그 말을 하지 않는다 — 안 쟀다.** 배열·객체에서 `for...in` 을 피하는 이유로 이 문서가 댈 수 있는 것은
**의미**(문자열 인덱스 · 체인에서 온 키 · 순회 중 변경의 비보장)뿐이다. 속도는 **별도 측정이 필요한 다른 주장**이다.

## 구현 세부사항 대 언어 보장

### 명세 보장 — 어느 엔진에서도 같아야 하는 것

- ★★★ **`for...in` 이 「열거 가능한 문자열 키」를 own 과 체인 위에서 모두 내놓는 것** · **심볼을 안 내놓는 것** · **같은 이름을 한 번만 내놓는 것.**
- ★★★ **윗칸의 같은 이름을 걸러낼 때 `[[Enumerable]]` 을 안 보는 것** — own 비열거가 부모의 열거 가능을 가린다.
- ★★ **Proxy 없는 평범한 체인에서의 순서** — 칸마다 own 키 순서(13편의 세 덩어리), 칸 순서는 아래에서 위(ES2020).
- ★★ **처리 전에 지운 키를 안 내놓는 것.** **평범한 객체 자신에 순회 중 더한 키를 안 내놓는 것**(순서 제약이 살아 있을 때).
- ★★ **`for...in` 이 `[[OwnPropertyKeys]]`·`[[GetOwnProperty]]` 로 키와 속성을 얻는 것** — 그래서 `Proxy` 의 `ownKeys`·`gopd` 트랩이 불린다.
- ★★ **`undefined`·`null` 에서 break 완료(몸통 0회)** · **원시값은 `ToObject` 로 감싸 도는 것.**
- **`Object.keys`·`entries`·`JSON.stringify`·스프레드·`Object.assign`·`getOwnPropertyNames`·`Reflect.ownKeys` 가 own 에서 멈추는 것** — 그리고 각각 격자의 칸대로 보는 것.
- **`Object.keys(null)` 이 `TypeError` 인 것** · **`Object.hasOwn` 이 객체의 메서드를 안 빌리는 것.**
- **배열 인덱스가 문자열 키인 것** · **구멍은 프로퍼티가 없는 칸인 것** · **내장 `map`·`length` 가 비열거인 것.**

### 엔진(V8) 구현 · 이 판의 관찰

- ★★★ **`Proxy` 가 낀 체인의 트랩 순서** — 키를 체인 끝까지 먼저 모으고(`ownKeys`·`getPrototypeOf`) 키마다 `gopd` 로 확인했다. 8줄.
- ★★ **윗칸 키를 내놓기 전의 `C.gopd(p)`** — 아래 칸 재확인으로 읽었다(로그에서 나온 추론).
- ★★★ **순회 중 윗칸에 더한 `q` 를 안 방문한 것** · **지웠다 다시 넣은 `b` 를 원래 자리에서 방문한 것.** 둘 다 명세 비보장 행이다.
- **예외 문구** — `o.hasOwnProperty is not a function` · `Cannot convert undefined or null to object`. **종류(`TypeError`)만 명세다.**
- **두 판(18·20)이 한 글자도 안 갈린 것** — 둘 다 V8 이라서지 보장이 아니다.

### 호스트가 정하는 것 — ECMA-262 밖

- **이 주제에서는 0개다.** 블록이 `console.log` 로 찍는 것은 전부 `JSON.stringify` 한 문자열이라 **Node 의 표기 형식(`util.inspect`)이 끼지 않는다.**
- ★ 브라우저는 **안 돌렸다** — 호스트가 끼는 칸이 정말 0개인지는 Node 쪽 근거로만 말한다.

### 그래서 이렇게 적으면 틀린다

- 「`for...in` 의 순서는 보장되지 않는다」 — **낡았다.** ES2020 이 Proxy 없는 체인에서 못 박았다.
- 「순회 중 추가한 키는 안 나온다」 — **반만 맞다.** 대상 객체 자신에 더한 경우만 묶인다.
- 「비열거 own 은 없는 것과 같다」 — **열거에서는 아니다.** 부모의 같은 이름을 가린다.
- 「`for...in` 은 `null` 에서 터진다」 — **아니다.** 조용히 0회다. 터지는 것은 `Object.keys(null)` 이다.
- 「트랩 로그 순서가 `for...in` 의 알고리즘이다」 — **V8 의 순서다.** 명세 알고리즘과 달랐다.
- 「`for...in` 은 느리다」 — ★★★ **안 쟀다.**

## 언제 쓰고 언제 안 쓰나

- **`Object.keys` / `Object.entries`** — ★ **객체의 자기 키를 돌 때 기본 선택.** 체인에서 오는 것이 없고, `null` 이면 시끄럽게 실패하고, 순회 중 변경에 스냅숏으로 버틴다.
- **`for...in`** — ★ **「상속된 열거 가능 키까지」가 정말로 원하는 답일 때만.** 체인을 걷는 목록은 이것뿐이다.
  `Object.create(null)` 사전처럼 **윗집이 없는 객체**에서는 `Object.keys` 와 같은 답을 내니 써도 무방하다.
- **`for...in` + `Object.hasOwn`** — 옛 코드의 관용구. ★ 새로 쓸 거면 **`Object.keys` 로 바꾸는 것이 같은 뜻을 더 짧게** 말한다.
- **`Reflect.ownKeys`** — own 전수(비열거·심볼 포함)가 필요할 때. 디버깅·메타 코드.
- **배열** — ★★ **`for...in` 을 안 쓴다.** 값은 `for...of`(19편), 인덱스까지 필요하면 `entries()` 나 인덱스 루프.
- **프로토타입에 무언가 붙여야 한다면** — ★ **대입이 아니라 `defineProperty` + `enumerable: false`.** 그래야 모든 `for...in` 이 안 바뀐다(18b `[3]`).
- **순회 중 구조를 바꿔야 한다면** — **`Object.keys` 로 스냅숏을 먼저** 뜨고, 몸통에서 `Object.hasOwn` 으로 아직 있나를 확인한다.

## 핵심 문장

1. ★★★ **체인을 걷는 목록은 `for...in` 하나뿐이다.** 격자의 상속 세 줄에 `o` 가 있는 열은 `for-in` 과 `in` 둘이고, `in` 은 목록이 아니다.
2. ★★★ **`for...in` 은 「열거 가능 ∧ 문자열」을 own 먼저, 윗칸 나중으로 내놓고, 칸 안의 순서는 13편의 세 덩어리다.** 체인 전체를 다시 정렬하지 않는다.
3. ★★★ **own 비열거는 부모의 같은 이름을 가린다** — 「처리했다」와 「내놓았다」가 다르고, 처리 판정은 `enumerable` 을 안 본다.
4. ★★★ **순회 중 변경은 두 겹이다** — 처리 전 삭제는 무시(모든 객체), 자기 자신에 추가는 안 나옴(평범한 체인), **그 밖은 비보장**이고 V8 과 명세 알고리즘이 실제로 갈렸다.
5. ★★ **`for...in` 은 `null` 을 조용히 삼키고, 배열에서는 문자열 인덱스와 체인의 키를 섞는다** — 그래서 기본값은 `Object.keys` 와 `for...of` 다.

## 관련 자료

- [13 — 객체 리터럴과 프로퍼티](../13-object-literals-and-properties/2-summary.md) — **그쪽이 own 키 순서 세 덩어리와 정수 키 23후보의 정본**이다(`"01"`·`"4294967295"` 는 문자열 키). 여기는 **그 순서가 칸마다 이어 붙는다**는 것부터.
- [14 — 프로퍼티 디스크립터와 동결](../14-property-descriptors-and-freezing/2-summary.md) — **그쪽이 `enumerable` 플래그를 바꾸는 법의 정본**이다(★ `freeze` 는 `enumerable` 을 안 건드린다). 여기는 **그 플래그가 열거에서 하는 일**까지.
- [15 — 프로토타입 체인](../15-prototype-chain/2-summary.md) — **그쪽이 조회(`[[Get]]`)가 체인을 타는 규칙의 정본**이다. 여기는 **열거가 체인을 타는 규칙**.
- [11 — 스프레드와 나머지](../11-spread-and-rest/2-summary.md) — **그쪽이 `{ ...o }` 의 트랩 순서 정본**이다. 여기는 **그것이 체인에 안 닿는다**는 격자 칸.
- [16 — `class` 문법](../16-class-syntax/2-summary.md) — **그쪽이 클래스 멤버의 플래그 정본**이다. 여기는 **그 플래그 때문에 `for...in` 결과가 바뀐다**는 연결까지.
- [19 — 이터러블 프로토콜과 `for...of`](../19-iterable-protocol-and-for-of/2-summary.md) — **그쪽이 `for...of` 의 정본**이다. 여기는 **배열에서 둘이 갈리는 자리**(구멍·문자열 인덱스)까지.
- 목록의 **27번 주제** 「`Object` 정적 메서드」 — **그쪽이 `keys`/`entries`/`assign` 쓰임의 정본**이다.
- 목록의 **45번 주제** 「`Proxy`」 — **그쪽이 트랩 계약의 정본**이다. 여기서는 **로그 도구로만** 썼다.
- 목록의 **22번 주제** 「`Symbol` 과 잘 알려진 심볼」 — **그쪽이 심볼 키 성질의 정본**이다. 여기는 **`for...in` 이 심볼을 안 낸다**까지.
- [ECMA-262 — 문과 선언 장](https://tc39.es/ecma262/multipage/ecmascript-language-statements-and-declarations.html) — `EnumerateObjectProperties` 와 `CreateForInIterator` 가 한곳에 있다.

## 용어 풀이

- **열거 가능(enumerable)** — 「키를 늘어놓는 문법」에 보일지를 정하는 플래그. 대입으로 만든 프로퍼티는 `true`, `defineProperty` 기본은 `false`(14편).
- **열거(enumeration)** — 객체의 키를 하나씩 늘어놓는 것. 이 주제에서는 `for...in` 이 하는 일을 좁게 가리킨다.
- **체인 순회(chain walk)** — 자기 칸을 다 보고 `[[Prototype]]` 으로 올라가 이어 보는 것. `null` 에서 끝난다.
- **own 프로퍼티** — 그 객체 자신의 프로퍼티(15편).
- **가리기(shadowing)** — 아래 칸의 같은 이름이 윗칸의 것을 안 보이게 하는 것. 열거에서는 **아래 칸이 비열거여도** 가린다.
- **`EnumerateObjectProperties`** — `for...in` 이 쓰는 명세 추상 연산. 규칙(삭제·추가·심볼·가리기)을 문장으로 적어 둔 곳.
- **`CreateForInIterator`** — 평범한 체인에서 반복자가 **그대로 따라야 하는** 참조 알고리즘(ES2020). 칸에 들를 때 own 키를 한 번 떠 둔다.
- **break 완료(break completion)** — 「루프를 끝냈다」는 명세의 결과값. 예외가 아니다. `for-in null` 이 이것을 돌려준다.
- **스냅숏(snapshot)** — 어느 시점에 떠 둔 목록. `Object.keys` 의 결과가 그렇다 — 뒤의 삭제를 모른다.
- **구멍(hole)** — 배열에서 프로퍼티가 **아예 없는** 인덱스. 값이 `undefined` 인 칸과 다르다.
- **`Object.hasOwn`** — 「이 키가 own 인가」를 **객체 밖에서** 묻는 정적 함수(ES2022).
- **`Proxy` 트랩(trap)** — 내부 동작을 가로채는 갈고리. 이 주제에서는 **로그를 심는 도구**로만 썼다.

## 더 들어가면

- **왜 명세는 「순회 중 추가」를 끝내 보장하지 않나** — 명세의 노트가 이유를 직접 적었다 —
  "The list of exotic objects for which implementations are not required to match CreateForInIterator was chosen because implementations historically differed in behaviour for those cases, and agreed in all others."
  ES2020 은 **엔진들이 이미 똑같이 하던 자리만** 못 박았다. 윗칸 추가·삭제 후 재추가·Proxy 는 **엔진마다 달랐던 자리**라 열어 두었다.
  ★ (18f 의 `q` 행이 그 「달랐던 자리」의 한 예를 이 판에서 보여 준다.)
- **`Object.create(null)` 사전과 `for...in`** — 윗집이 없으니 상속 키가 섞일 수 없고, `hasOwnProperty` 를 못 빌려도 `for...in` 은 **문**이라 된다.
  「사전에는 `Object.create(null)`」(15편)과 「`for...in` 은 체인을 걷는다」가 **서로의 약점을 없애는 짝**이다.
- **엄격 모드에서 이 격자가 바뀌나** — 이 배치에서 **안 돌렸다.** 열거 문법 자체에 모드 분기가 있다는 명세 문장은 이번에 읽은 범위에 없었지만,
  「없다」는 **돌려서 확인할 일**이다.
- **TypedArray·모듈 네임스페이스 객체** — 순서 제약 예외 목록에 Proxy 와 나란히 올라 있다. **이 배치에서 안 던졌다.**
