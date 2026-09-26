# js/syntax/13 — 객체 리터럴과 프로퍼티: 「키는 전부 문자열이고, 정수처럼 생긴 것만 앞줄에 선다」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> ★★★ **이 주제의 본체는 ② 전수 격자다.**
> 열거 순서와 「정수 키」의 경계는 **규칙을 외워서 맞히는 것이 아니라 던져서 갈라야** 하는 자리다 —
> `"1"` 과 `"01"` 과 `"1.0"` 과 `"4294967295"` 가 **눈으로는 전부 숫자처럼 보이는데 답이 갈린다.**
> 23개 후보를 한 스크립트에 넣어 **어느 쪽인지 스크립트가 세게** 했다.
> ① 로그 심기가 계산된 키에서 한 번 더 쓰인다 — **객체를 키로 주면 무엇이 불리나**.
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262 최신 초안](https://tc39.es/ecma262/) — Object Initializer · `ToPropertyKey` · `OrdinaryOwnPropertyKeys` · array index 의 정의 · `__proto__` 의 Annex B
> - [ECMA-262 판별 아카이브](https://262.ecma-international.org/) — 열거 순서가 **명세로 못 박힌 판**과 중복 키 금지가 **사라진 판**을 가릴 때
> - [MDN — Object initializer](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Object_initializer)
> - [TC39 — for-in order 제안](https://tc39.es/proposal-for-in-order/) — `for...in` 순서가 **마지막으로** 못 박힌 판을 가릴 때
>
> ★★★ **명세 조항 번호는 인용하지 않는다.** 규칙 진술은 위 문서로, **값·순서·예외는 전부 실행으로** 접지했다.
>
> **실행 검증** — 이 문서의 모든 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다.
> 배너의 `node20` 은 `~/.nvm/versions/node/v20.19.6/bin/node`, `node18` 은 기본 PATH 의 `node`(v18.19.1)다.
>
> ★★★ **이 문서는 순서가 그대로 실린 블록을 갖고 있다 — 그것이 금지 규칙의 예외인 이유를 먼저 밝힌다.**
> 「순서가 보장되지 않는 출력을 싣지 마라」는 규칙이 있는데, **객체 프로퍼티의 열거 순서는 명세가 못 박은 것**이다.
> ES2015 의 `[[OwnPropertyKeys]]` 가 **①배열 인덱스 오름차순 → ②나머지 문자열 키 삽입순 → ③심볼 키 삽입순** 을 규정했고,
> 그때 `Object.keys`·`getOwnPropertyNames`·`Reflect.ownKeys`·`JSON.stringify` 가 그 순서에 묶였다.
> **`for...in` 만 그때까지 남아 있었고 ES2020 이 마지막으로 못 박았다**([for-in order 제안](https://tc39.es/proposal-for-in-order/)).
> ★ 근거는 **명세 문서 + 두 판 + 브라우저에서 같은 줄이 나온 것**이다. 다만 **「여러 판에서 같았다」는 보장이 아니므로**
> 보장의 근거는 명세 쪽이고, 실행은 **확인**이다.
>
> ★★ **예외는 `try`/`catch` 로 받아 `e.constructor.name` 과 `e.message` 만 찍는다**(스택트레이스에는 절대 경로가 박힌다).
> ★★ **이 문서의 모든 블록은 표준 출력뿐이다.**
>
> **버전** — **단축 표기·계산된 키·`get`/`set` 리터럴·메서드 단축은 ES2015**,
> **열거 순서가 `Object.keys`·`JSON.stringify` 에 고정된 것은 ES2015 이고 `for...in` 까지 못 박힌 것은 ES2020**,
> **`__proto__:` 리터럴 문법은 Annex B**(웹 호환을 위한 규범적 선택 사항이지만 **모든 웹 엔진이 구현한다**)이다.
> ★★★ **중복 키를 엄격 모드에서 금지하던 ES5 규칙은 ES6 에서 사라졌다** — 「옛날 규칙과 다르다」의 대표 사례다.
>
> **★★★ 이 주제가 쓰는 창 — 그리고 부적용인 창**
>
> | 창 | 이 주제에서 무엇을 보나 |
> |---|---|
> | ★★★ **② 전수 격자**(본체) | 정수 키 후보 **23종** · 열거 순서 11키 · 프로퍼티 뷰 7종 × 프로퍼티 6종 · `__proto__` 5형태 |
> | ★★★ **① 추상 연산에 로그 심기** | 계산된 키가 `ToPropertyKey` 를 부르는 것 — `toString` 인가 `Symbol.toPrimitive` 인가, **힌트는 무엇인가** |
> | ★★ **평가 순서 로그** | 키와 값 중 **무엇이 먼저** 평가되나 · 중복 키의 **버려지는 값도 평가되나** |
> | ★ **④ 예외의 `constructor.name` + `message`** | 이 주제에서는 거의 안 쓰인다 — **객체 리터럴은 웬만해선 안 터진다**(보조) |
> | ★ **⑤ 두 판 대조기 + 브라우저** | 판이 갈린 칸 · 호스트가 정하는 칸이 있나 — **이 주제에서는 0** |
> | ★ **부적용 — 두 번 컴파일**(엄격/비엄격) | **중복 키 한 칸만** 모드를 탈 뻔했고 그마저 ES6 에서 사라졌다. 나머지는 잴 것이 없다 |
> | ★ **부적용 — 성능 측정** | 「정수 키가 빠르다」·「객체가 Map 보다 느리다」는 **재지 않았다.** 이 문서에 속도 주장이 한 줄도 없다 |
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | Node 스택트레이스의 **절대 경로** — 한 줄도 싣지 않았다 | ★★★ **열거 순서**(명세가 못 박은 것) |
> | 브라우저 UA 문자열의 뒷자리 | ★★★ **정수 키 판정** · **로그의 이름과 순서** |
> | 엔진 내부의 저장 방식(관찰 불가) | ★★ **디스크립터의 모양** · 뷰 7종의 `true`/`false` 격자 |
>
> ★★ **이 주제의 블록에는 주소도 시간도 난수도 한 곳도 안 찍힌다.** 같은 판에서 다시 돌리면 **한 글자도 안 변한다.**
> ★★★ **두 판이 갈린 블록은 이 주제에 0개다.**
>
> **선행** — [12 — 옵셔널 체이닝·널 병합·논리 할당](../12-optional-chaining-nullish-and-logical-assignment/2-summary.md) · [11 — 스프레드와 나머지](../11-spread-and-rest/2-summary.md) · [01 — 값의 종류와 `typeof`](../01-value-types-and-typeof/2-summary.md) · [02 — 강제 변환과 `==` 대 `===`](../02-coercion-and-loose-equality/2-summary.md).
> ★★★ **02번이 계산된 키의 뿌리다.** 객체를 키로 쓰면 `ToPropertyKey` 가 **`ToPrimitive`(힌트 `string`)** 를 부른다 —
> **강제 변환의 정본은 02번**이고, 여기서는 **그것이 키 자리에서 불린다는 사실**만 본다.
> ★★ **11번이 `{ ...o }` 가 자기 것이고 열거 가능한 것만 가져간다**는 것을 실측했다. 여기서는 **그 「열거 가능」이 무엇인지**를 격자로 연다.
> **이어지는 곳** — [14 — 프로퍼티 디스크립터와 동결](../14-property-descriptors-and-freezing/2-summary.md) · [15 — 프로토타입 체인](../15-prototype-chain/2-summary.md) · 목록의 **18번 주제** 「`for...in` 과 열거」 · 목록의 **22번 주제** 「`Symbol` 과 잘 알려진 심볼」 · 목록의 **27번 주제** 「`Object` 정적 메서드」
>
> ★★ **경계 — 세 플래그의 의미와 동결은 14번이 정본이다.** 여기서는 **어느 문법이 어떤 디스크립터를 만드나**까지다.
> ★★ **경계 — 체인 순회는 15번과 18번이 정본이다.** 여기서는 **`for...in` 이 체인을 탄다는 사실**까지다.
> ★★ **경계 — 심볼의 성질과 잘 알려진 심볼은 22번이 정본이다.** 여기서는 **심볼 키가 열거 순서의 셋째 덩어리**라는 것까지다.
> ★★ **경계 — `Object.assign`·`groupBy` 같은 정적 메서드 API 는 27번이 정본이다.**

```sh
# js12b-versions.sh
#!/usr/bin/env bash
# 이 문서의 모든 출력이 어느 판에서 나왔는지 -- 첫 블록에 싣는다.
set -u -o pipefail
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
for n in "$N18" "$N20"; do
  "$n" -e 'const v = process.versions;
    const ord = {}; ord.b = 1; ord[2] = 1; ord.a = 1; ord[1] = 1;
    const box = { p: 0 };
    box.p ??= 9;
    console.log("node " + v.node + "  v8 " + v.v8 +
      "  optchain " + String(({ a: { b: 7 } }).a?.b) +
      "  nullish " + String(0 ?? "D") + "/" + String(0 || "D") +
      "  logical-assign " + box.p +
      "  ownKeys " + JSON.stringify(Reflect.ownKeys(ord)) +
      "  hasOwn " + typeof Object.hasOwn +
      "  desc " + JSON.stringify(Object.getOwnPropertyDescriptor({ q: 1 }, "q")) +
      "  defineProp-desc " + JSON.stringify(Object.getOwnPropertyDescriptor(Object.defineProperty({}, "q", { value: 1 }), "q")));'
done
google-chrome --version 2>/dev/null
```

```text
===== ./js12b-versions.sh (exit=0) =====
node 18.19.1  v8 10.2.154.26-node.28  optchain 7  nullish 0/D  logical-assign 0  ownKeys ["1","2","b","a"]  hasOwn function  desc {"value":1,"writable":true,"enumerable":true,"configurable":true}  defineProp-desc {"value":1,"writable":false,"enumerable":false,"configurable":false}
node 20.19.6  v8 11.3.244.8-node.33  optchain 7  nullish 0/D  logical-assign 0  ownKeys ["1","2","b","a"]  hasOwn function  desc {"value":1,"writable":true,"enumerable":true,"configurable":true}  defineProp-desc {"value":1,"writable":false,"enumerable":false,"configurable":false}
Google Chrome 151.0.7922.173 
```

## 한눈에 — 쉽게 말하면

**객체는 「이름표가 붙은 서랍장」인데, 이름표는 전부 글자이고 서랍은 세 칸으로 나뉘어 있다.**

```text
   하나의 객체 = 서랍 세 덩어리

   ┌─────────────────────────────────────────────┐
   │ ① 배열 인덱스처럼 생긴 키   "0" "1" "2" "10"  │  숫자 오름차순으로 정렬된다
   ├─────────────────────────────────────────────┤
   │ ② 나머지 문자열 키          "b" "a" "-1" "01" │  넣은 순서 그대로
   ├─────────────────────────────────────────────┤
   │ ③ 심볼 키                   Symbol(s1) …      │  넣은 순서 그대로
   └─────────────────────────────────────────────┘

   ★ ①에 들어가는 조건이 좁다 -- "01" 도 "1.0" 도 "-1" 도 ②로 떨어진다.
   ★ 넣은 순서는 ②와 ③에서만 살아남는다.
```

- **키는 문자열 아니면 심볼, 둘뿐이다.** 숫자로 써도 **저장되기 전에 문자열이 된다**(`o[1]` 과 `o["1"]` 은 같은 서랍).
- **`{ }` 안에서 대괄호를 쓰면 키를 계산한다** — 그때 값이 객체면 `toString`(또는 `Symbol.toPrimitive`)이 불린다.
- **같은 키를 두 번 쓰면 나중 것이 이긴다** — 엄격 모드에서도 그렇다.

> **프로퍼티 키(property key)** — 객체의 서랍 이름. **문자열 아니면 심볼**이고 다른 타입은 될 수 없다.\
> 예: `o[1] = 'a'` 는 `1` 을 `"1"` 로 바꿔 저장한다. 그래서 `Object.keys(o)` 가 `["1"]` 이다.

## 이 주제가 답하려는 질문

1. **키는 무엇이 될 수 있고, 아닌 것을 주면 어떻게 바뀌는가** — 그리고 바꾸는 일은 **누가** 하는가?
2. **열거 순서는 무엇이 정하는가** — 「넣은 순서」인가, 아니면 다른 규칙이 앞서는가?
3. **「정수 키」의 경계는 정확히 어디인가** — `"01"` 은? `"4294967295"` 는?

## 동작 방식

### (1) ★★★ 열거 순서 — 넣은 순서와 나온 순서를 나란히

**언제 쓰나** — 객체를 순회하거나 `JSON.stringify` 한 결과의 키 순서가 **기대와 다를 때.**

```js
// js12b-13a-order.js
// 열거 순서 전수 격자 -- 넣은 순서와 나온 순서를 나란히 찍는다.
// ★ 이 순서는 명세가 못 박은 것이라 「순서 비보장 출력 금지」의 예외다(OrdinaryOwnPropertyKeys).
const s1 = Symbol("s1");
const s2 = Symbol("s2");

const inserted = [
  ["b", "str b"], ["2", "int 2"], [s1, "sym s1"], ["a", "str a"],
  ["1", "int 1"], ["0", "int 0"], [s2, "sym s2"], ["10", "int 10"],
  ["-1", "str -1"], ["01", "str 01"], ["1.5", "str 1.5"],
];
const o = {};
for (const [k, v] of inserted) o[k] = v;

const nm = (k) => (typeof k === "symbol" ? String(k) : JSON.stringify(k));

console.log("[1] inserted order  vs  Reflect.ownKeys order");
console.log("#".padEnd(4) + "inserted".padEnd(14) + "ownKeys".padEnd(14) + "bucket");
const keys = Reflect.ownKeys(o);
const bucket = (k) => {
  if (typeof k === "symbol") return "3 symbol";
  const n = Number(k);
  return (String(n >>> 0) === k && n >>> 0 !== 4294967295) ? "1 array index" : "2 string";
};
for (let i = 0; i < Math.max(inserted.length, keys.length); i += 1) {
  const ins = i < inserted.length ? nm(inserted[i][0]) : "";
  const out = i < keys.length ? nm(keys[i]) : "";
  console.log(String(i).padEnd(4) + ins.padEnd(14) + out.padEnd(14) + (out ? bucket(keys[i]) : ""));
}

console.log("");
console.log("[2] the four views, in order");
console.log("Object.keys             " + JSON.stringify(Object.keys(o)));
console.log("Object.values           " + JSON.stringify(Object.values(o)));
console.log("getOwnPropertyNames     " + JSON.stringify(Object.getOwnPropertyNames(o)));
console.log("getOwnPropertySymbols   " + JSON.stringify(Object.getOwnPropertySymbols(o).map(String)));
console.log("Reflect.ownKeys         " + JSON.stringify(keys.map(nm)));
console.log("JSON.stringify keys     " + JSON.stringify(Object.keys(JSON.parse(JSON.stringify(o)))));
const forIn = [];
for (const k in o) forIn.push(k);
console.log("for...in                " + JSON.stringify(forIn));
console.log("spread { ...o } keys    " + JSON.stringify(Object.keys({ ...o })));

console.log("");
console.log("[3] does the order survive a delete + re-add?  (string keys are insertion-ordered)");
const o2 = { a: 1, b: 2, c: 3 };
console.log("start                   " + JSON.stringify(Object.keys(o2)));
delete o2.a; o2.a = 9;
console.log("delete a; o2.a = 9      " + JSON.stringify(Object.keys(o2)));
const o3 = { 3: 1, 1: 2, 2: 3 };
console.log("{3:_,1:_,2:_}           " + JSON.stringify(Object.keys(o3)));
delete o3[1]; o3[1] = 9;
console.log("delete 1; o3[1] = 9     " + JSON.stringify(Object.keys(o3)));

console.log("");
console.log("[4] the same rule on a Map -- insertion order only, no integer bucket");
const m = new Map();
for (const [k, v] of inserted) m.set(k, v);
console.log("Map keys                " + JSON.stringify([...m.keys()].map(nm)));
```

```text
===== node20 js12b-13a-order.js (exit=0) =====
[1] inserted order  vs  Reflect.ownKeys order
#   inserted      ownKeys       bucket
0   "b"           "0"           1 array index
1   "2"           "1"           1 array index
2   Symbol(s1)    "2"           1 array index
3   "a"           "10"          1 array index
4   "1"           "b"           2 string
5   "0"           "a"           2 string
6   Symbol(s2)    "-1"          2 string
7   "10"          "01"          2 string
8   "-1"          "1.5"         2 string
9   "01"          Symbol(s1)    3 symbol
10  "1.5"         Symbol(s2)    3 symbol

[2] the four views, in order
Object.keys             ["0","1","2","10","b","a","-1","01","1.5"]
Object.values           ["int 0","int 1","int 2","int 10","str b","str a","str -1","str 01","str 1.5"]
getOwnPropertyNames     ["0","1","2","10","b","a","-1","01","1.5"]
getOwnPropertySymbols   ["Symbol(s1)","Symbol(s2)"]
Reflect.ownKeys         ["\"0\"","\"1\"","\"2\"","\"10\"","\"b\"","\"a\"","\"-1\"","\"01\"","\"1.5\"","Symbol(s1)","Symbol(s2)"]
JSON.stringify keys     ["0","1","2","10","b","a","-1","01","1.5"]
for...in                ["0","1","2","10","b","a","-1","01","1.5"]
spread { ...o } keys    ["0","1","2","10","b","a","-1","01","1.5"]

[3] does the order survive a delete + re-add?  (string keys are insertion-ordered)
start                   ["a","b","c"]
delete a; o2.a = 9      ["b","c","a"]
{3:_,1:_,2:_}           ["1","2","3"]
delete 1; o3[1] = 9     ["1","2","3"]

[4] the same rule on a Map -- insertion order only, no integer bucket
Map keys                ["\"b\"","\"2\"","Symbol(s1)","\"a\"","\"1\"","\"0\"","Symbol(s2)","\"10\"","\"-1\"","\"01\"","\"1.5\""]
```

**그림 해설 — 한 단계에 한 문장.**

- `[1]` **왼쪽(넣은 순서)과 오른쪽(나온 순서)이 완전히 다르다.** `"b"` 를 맨 먼저 넣었는데 다섯 번째로 나온다.
- ★★★ **세 덩어리가 그대로 보인다** — `bucket` 칸이 `1 array index` 넷 → `2 string` 다섯 → `3 symbol` 둘이다.
  덩어리 ①은 **넣은 순서와 무관하게 숫자 오름차순**이고(`"0" "1" "2" "10"`), ②와 ③은 **넣은 순서 그대로**다.
- ★★ `[2]` **일곱 가지 뷰가 전부 같은 순서**를 낸다. `Object.keys`·`for...in`·`JSON.stringify`·스프레드가 한 줄기다.
  ★ 다만 **보는 범위**는 다르다 — 심볼은 `Reflect.ownKeys` 와 `getOwnPropertySymbols` 에만 나온다.
- ★★ `[3]` **지웠다 다시 넣으면 문자열 키는 맨 뒤로 간다**(`["b","c","a"]`). **정수 키는 제자리로 돌아온다** —
  ②는 삽입순이고 ①은 정렬이기 때문이다. **같은 조작의 결과가 덩어리에 따라 다르다.**
- ★ `[4]` `Map` 은 **덩어리가 없다.** 넣은 순서 그대로 나오고 숫자도 앞으로 안 끌려간다 — 대비가 선명하다.

**비용** — 재지 않았다. 이 문서에 속도 주장은 한 줄도 없다.

```text
   이 키가 앞줄에 설 자격이 있나 -- 되돌려 보는 것이 판정이다

   글자 "01"                       글자 "10"
     │ 숫자로 읽으면 1               │ 숫자로 읽으면 10
     │ 다시 글자로 만들면 "1"        │ 다시 글자로 만들면 "10"
     └─> "01" 과 다르다 -> 탈락      └─> "10" 과 같다 -> 통과
                                        그리고 2**32-1 보다 작다 -> 배열 인덱스

   통과선 ───────────────────────────────────────────
   … 4294967293   4294967294 │ 4294967295   4294967296 …
        배열 인덱스          │      그냥 문자열 키
                             │
            여기가 끊기는 자리 -- 배열의 최대 length 가 2**32-1 이고
            인덱스는 length 보다 작아야 한다.
```

### (2) ★★★ 「정수 키」의 경계 — 23종 전수 격자

**언제 쓰나** — 어떤 키가 앞줄로 끌려갈지 **눈으로 판단하려 할 때.** 눈으로는 못 가른다.

```js
// js12b-13b-intkeys.js
// 「정수 키」의 경계를 전수로 가른다.
// 판정법 -- 앞뒤로 문자열 키를 박아 두고, 후보가 그 앞으로 끌려가면 배열 인덱스다.
const candidates = [
  "0", "1", "2", "10", "4294967293", "4294967294", "4294967295", "4294967296",
  "01", "00", "1.0", "1.5", "-0", "-1", "+1", " 1", "1 ", "1e2", "0x1",
  "9007199254740993", "", "NaN", "Infinity",
];

console.log("[1] is this key an array index?   (a=inserted first, z=inserted last)");
console.log("key".padEnd(20) + "ownKeys".padEnd(30) + "verdict".padEnd(16) + "Array check");
let idx = 0;
for (const k of candidates) {
  const o = { a: 0 };
  o[k] = 1;
  o.z = 2;
  const keys = Object.keys(o);
  const first = keys[0] === k;
  if (first) idx += 1;
  const arr = [];
  arr[k] = 1;
  const arrLen = Array.isArray(arr) ? arr.length : -1;
  console.log(JSON.stringify(k).padEnd(20) + JSON.stringify(keys).padEnd(30) +
    (first ? "ARRAY INDEX" : "string key").padEnd(16) + "arr.length=" + arrLen);
}
console.log("");
console.log("array-index keys " + idx + " / " + candidates.length);

console.log("");
console.log("[2] the boundary itself -- 2**32-2 is the last array index, 2**32-1 is not");
console.log("2**32-2 = 4294967294   " + JSON.stringify(Object.keys((() => { const o = { a: 0 }; o[4294967294] = 1; o.z = 2; return o; })())));
console.log("2**32-1 = 4294967295   " + JSON.stringify(Object.keys((() => { const o = { a: 0 }; o[4294967295] = 1; o.z = 2; return o; })())));
console.log("max array length       " + (() => { const a = []; a[4294967294] = 1; return a.length; })());
try { const a = []; a[4294967295] = 1; console.log("a[2**32-1] -> length " + a.length + "  keys " + JSON.stringify(Object.keys(a))); }
catch (e) { console.log("a[2**32-1] -> " + e.constructor.name + " " + e.message); }

console.log("");
console.log("[3] number keys are converted to strings first -- the key is always a string");
const n = {};
n[1] = "a"; n["1"] = "b"; n[1.0] = "c";
console.log("n[1]=a; n['1']=b; n[1.0]=c  -> keys " + JSON.stringify(Object.keys(n)) + "  value " + n[1]);
const f = {};
f[1.5] = "x"; f["1.5"] = "y";
console.log("f[1.5]=x; f['1.5']=y        -> keys " + JSON.stringify(Object.keys(f)) + "  value " + f[1.5]);
const neg = {};
neg[-0] = "x";
console.log("neg[-0]='x'                 -> keys " + JSON.stringify(Object.keys(neg)));
const big = {};
big[1e21] = "x"; big[1e2] = "y";
console.log("big[1e21], big[1e2]         -> keys " + JSON.stringify(Object.keys(big)));
```

```text
===== node20 js12b-13b-intkeys.js (exit=0) =====
[1] is this key an array index?   (a=inserted first, z=inserted last)
key                 ownKeys                       verdict         Array check
"0"                 ["0","a","z"]                 ARRAY INDEX     arr.length=1
"1"                 ["1","a","z"]                 ARRAY INDEX     arr.length=2
"2"                 ["2","a","z"]                 ARRAY INDEX     arr.length=3
"10"                ["10","a","z"]                ARRAY INDEX     arr.length=11
"4294967293"        ["4294967293","a","z"]        ARRAY INDEX     arr.length=4294967294
"4294967294"        ["4294967294","a","z"]        ARRAY INDEX     arr.length=4294967295
"4294967295"        ["a","4294967295","z"]        string key      arr.length=0
"4294967296"        ["a","4294967296","z"]        string key      arr.length=0
"01"                ["a","01","z"]                string key      arr.length=0
"00"                ["a","00","z"]                string key      arr.length=0
"1.0"               ["a","1.0","z"]               string key      arr.length=0
"1.5"               ["a","1.5","z"]               string key      arr.length=0
"-0"                ["a","-0","z"]                string key      arr.length=0
"-1"                ["a","-1","z"]                string key      arr.length=0
"+1"                ["a","+1","z"]                string key      arr.length=0
" 1"                ["a"," 1","z"]                string key      arr.length=0
"1 "                ["a","1 ","z"]                string key      arr.length=0
"1e2"               ["a","1e2","z"]               string key      arr.length=0
"0x1"               ["a","0x1","z"]               string key      arr.length=0
"9007199254740993"  ["a","9007199254740993","z"]  string key      arr.length=0
""                  ["a","","z"]                  string key      arr.length=0
"NaN"               ["a","NaN","z"]               string key      arr.length=0
"Infinity"          ["a","Infinity","z"]          string key      arr.length=0

array-index keys 6 / 23

[2] the boundary itself -- 2**32-2 is the last array index, 2**32-1 is not
2**32-2 = 4294967294   ["4294967294","a","z"]
2**32-1 = 4294967295   ["a","4294967295","z"]
max array length       4294967295
a[2**32-1] -> length 0  keys ["4294967295"]

[3] number keys are converted to strings first -- the key is always a string
n[1]=a; n['1']=b; n[1.0]=c  -> keys ["1"]  value c
f[1.5]=x; f['1.5']=y        -> keys ["1.5"]  value y
neg[-0]='x'                 -> keys ["0"]
big[1e21], big[1e2]         -> keys ["100","1e+21"]
```

**그림 해설.**

- ★★★ **23종 중 배열 인덱스는 6종뿐**이다 — `"0"`·`"1"`·`"2"`·`"10"`·`"4294967293"`·`"4294967294"`.
- ★★★ **`"4294967295"`(2³²−1)는 배열 인덱스가 아니다.** 바로 아래인 `"4294967294"` 는 맞다.
  ★ 왜 하필 거기서 끊기나 — **배열의 최대 `length` 가 2³²−1** 이라, 인덱스는 **`length` 보다 작아야** 하기 때문이다.
  같은 블록의 `arr.length` 칸이 그것을 보인다: `4294967294` 를 넣으면 `length` 가 **4294967295**(최댓값)가 되고,
  `4294967295` 를 넣으면 배열의 **`length` 가 0 인 채 문자열 키로만 들어간다.**
- ★★★ **`"01"` 은 문자열 키다.** `"1.0"`·`"+1"`·`" 1"`·`"1 "`·`"1e2"`·`"0x1"`·`"-0"`·`"-1"` 전부 그렇다.
  판정 기준은 「숫자로 읽히나」가 아니라 **「그 숫자를 다시 문자열로 만들면 원래 글자와 같나」** 이다 —
  `String(Number("01"))` 은 `"1"` 이지 `"01"` 이 아니므로 탈락이다.
- ★★ `[3]` 이 그 규칙의 다른 얼굴이다. `o[1]`·`o["1"]`·`o[1.0]` 은 **한 서랍**이고,
  `o[-0]` 은 키가 **`"0"`** 이 되며, `o[1e21]` 은 키가 **`"1e+21"`** 이 된다 — **숫자를 문자열로 바꾸는 규칙이 키를 정한다.**

> **배열 인덱스(array index)** — 명세가 따로 정의한 좁은 개념. **정수를 그대로 적은 문자열이면서 2³²−1 보다 작은 것.**\
> 예: `"7"` 은 배열 인덱스이고 `"07"` 은 아니다. 열거 순서의 첫 덩어리에 들어가는 것이 정확히 이것이다.

```text
   키 자리에 무엇을 넣든 서랍 이름은 둘 중 하나가 된다

   o[ 값 ]
      │
      ├─ 심볼이면 ──────────────────────────> 그대로 심볼 키   (아무것도 안 불린다)
      │
      └─ 심볼이 아니면
             ToPrimitive( 값, 힌트 "string" )
                  │
                  ├─ Symbol.toPrimitive 가 있으면 그것 하나만 부른다 (힌트를 인자로 받는다)
                  └─ 없으면 toString 먼저, 그게 원시값을 안 주면 valueOf
             그 결과를 ToString 으로 ──────────> 문자열 키

   ★ 힌트가 "string" 이라 toString 이 먼저다 -- 그래서 valueOf 는 보통 안 불린다.
   ★ 읽을 때도 같은 길을 간다. o[k] 는 쓸 때든 읽을 때든 매번 키를 다시 만든다.
```

### (3) ★★★ 계산된 키 — 무엇이 불리나

**언제 쓰나** — 키 자리에 변수를 넣었는데 그 변수가 문자열이 아닐 때.

```js
// js12b-13c-computed.js
// 계산된 키가 ToPropertyKey 를 부르는 것을 로그로 증명한다.
// ToPropertyKey -> ToPrimitive(hint string) -> Symbol.toPrimitive 가 있으면 그것, 없으면 toString/valueOf.
const L = [];
const reset = () => { L.length = 0; };

console.log("[1] plain object as a computed key -- which method is called, with which hint?");
reset();
const plain = {
  toString() { L.push("toString"); return "K1"; },
  valueOf() { L.push("valueOf"); return "V1"; },
};
const o1 = { [plain]: 1 };
console.log("{ [plain]: 1 }        keys " + JSON.stringify(Object.keys(o1)) + "   log " + JSON.stringify(L));

reset();
const prim = {
  [Symbol.toPrimitive](hint) { L.push("Symbol.toPrimitive hint=" + hint); return "K2"; },
  toString() { L.push("toString"); return "K1"; },
};
const o2 = { [prim]: 1 };
console.log("{ [prim]: 1 }         keys " + JSON.stringify(Object.keys(o2)) + "   log " + JSON.stringify(L));

reset();
const o3 = {};
o3[plain] = 1;
console.log("o3[plain] = 1         keys " + JSON.stringify(Object.keys(o3)) + "   log " + JSON.stringify(L));
reset();
const readBack = o3[plain];
console.log("o3[plain]  (read)     value " + readBack + "        log " + JSON.stringify(L));

reset();
const sym = Symbol("S");
const o4 = { [sym]: 1 };
console.log("{ [sym]: 1 }          symbols " + JSON.stringify(Object.getOwnPropertySymbols(o4).map(String)) + "   log " + JSON.stringify(L));

console.log("");
console.log("[2] evaluation order -- computed keys are evaluated in source order, before the value");
reset();
const say = (t, v) => { L.push(t); return v; };
const o5 = { [say("key-a", "a")]: say("val-a", 1), [say("key-b", "b")]: say("val-b", 2) };
console.log("keys " + JSON.stringify(Object.keys(o5)) + "   order " + JSON.stringify(L));

console.log("");
console.log("[3] duplicate keys -- later wins, and the earlier VALUE is still evaluated");
reset();
const o6 = { a: say("first", 1), b: say("mid", 9), a: say("second", 2) };
console.log("{ a: 1st, b: mid, a: 2nd }  -> " + JSON.stringify(o6) + "   order " + JSON.stringify(L));
console.log("key position follows the FIRST appearance: " + JSON.stringify(Object.keys(o6)));

console.log("");
console.log("[4] shorthand, methods, get/set -- what descriptor does each make?");
const val = 7;
const o7 = {
  val,
  m() { return 1; },
  get g() { return "G"; },
  set g(v) { this.stored = v; },
  arrow: () => 2,
};
const d = (k) => {
  const x = Object.getOwnPropertyDescriptor(o7, k);
  const kind = "get" in x && (x.get || x.set) ? "accessor" : "data";
  return (kind === "accessor"
    ? "get=" + (x.get ? x.get.name : "undefined") + " set=" + (x.set ? x.set.name : "undefined")
    : "value=" + JSON.stringify(x.value === undefined ? String(x.value) : (typeof x.value === "function" ? "[fn " + x.value.name + "]" : x.value)) + " w=" + x.writable)
    + " e=" + x.enumerable + " c=" + x.configurable;
};
for (const k of ["val", "m", "g", "arrow"]) console.log(("o7." + k).padEnd(10) + d(k));
console.log("m.prototype exists?     " + Object.prototype.hasOwnProperty.call(o7.m, "prototype"));
console.log("arrow.prototype exists? " + Object.prototype.hasOwnProperty.call(o7.arrow, "prototype"));

console.log("");
console.log("[5] __proto__ in an object literal is special -- but only in two of these five forms");
const P = { marker: "PROTO" };
const forms = {
  "{ __proto__: P }": { __proto__: P },
  '{ "__proto__": P }': { "__proto__": P },
  "{ ['__proto__']: P }": { ["__proto__"]: P },
  "{ __proto__ }  shorthand": (() => { const __proto__ = P; return { __proto__ }; })(),
  "{ __proto__() {} }  method": { __proto__() { return 1; } },
};
console.log("form".padEnd(28) + "prototype is P?".padEnd(18) + "own keys");
for (const [label, obj] of Object.entries(forms)) {
  console.log(label.padEnd(28) + String(Object.getPrototypeOf(obj) === P).padEnd(18) +
    JSON.stringify(Object.getOwnPropertyNames(obj)));
}
console.log("");
console.log("JSON.parse('{\"__proto__\":{\"x\":1}}') -> proto is Object.prototype? " +
  (Object.getPrototypeOf(JSON.parse('{"__proto__":{"x":1}}')) === Object.prototype) +
  "   own keys " + JSON.stringify(Object.getOwnPropertyNames(JSON.parse('{"__proto__":{"x":1}}'))));
```

```text
===== node20 js12b-13c-computed.js (exit=0) =====
[1] plain object as a computed key -- which method is called, with which hint?
{ [plain]: 1 }        keys ["K1"]   log ["toString"]
{ [prim]: 1 }         keys ["K2"]   log ["Symbol.toPrimitive hint=string"]
o3[plain] = 1         keys ["K1"]   log ["toString"]
o3[plain]  (read)     value 1        log ["toString"]
{ [sym]: 1 }          symbols ["Symbol(S)"]   log []

[2] evaluation order -- computed keys are evaluated in source order, before the value
keys ["a","b"]   order ["key-a","val-a","key-b","val-b"]

[3] duplicate keys -- later wins, and the earlier VALUE is still evaluated
{ a: 1st, b: mid, a: 2nd }  -> {"a":2,"b":9}   order ["first","mid","second"]
key position follows the FIRST appearance: ["a","b"]

[4] shorthand, methods, get/set -- what descriptor does each make?
o7.val    value=7 w=true e=true c=true
o7.m      value="[fn m]" w=true e=true c=true
o7.g      get=get g set=set g e=true c=true
o7.arrow  value="[fn arrow]" w=true e=true c=true
m.prototype exists?     false
arrow.prototype exists? false

[5] __proto__ in an object literal is special -- but only in two of these five forms
form                        prototype is P?   own keys
{ __proto__: P }            true              []
{ "__proto__": P }          true              []
{ ['__proto__']: P }        false             ["__proto__"]
{ __proto__ }  shorthand    false             ["__proto__"]
{ __proto__() {} }  method  false             ["__proto__"]

JSON.parse('{"__proto__":{"x":1}}') -> proto is Object.prototype? true   own keys ["__proto__"]
```

**그림 해설.**

- `[1]` ★★★ **`toString` 이 불린다** — `valueOf` 가 있어도 그쪽은 안 불린다.
  `Symbol.toPrimitive` 가 있으면 **그것이 이기고, 힌트는 `string`** 이다.
  ★★ **읽을 때도 똑같이 불린다** — `o3[plain]` 을 읽는 줄에서도 로그에 `toString` 이 찍힌다.
  ★ 심볼을 키로 주면 **아무것도 안 불린다** — 심볼은 이미 키가 될 수 있는 타입이라 변환이 필요 없다.
- `[2]` **키가 값보다 먼저**다. 한 프로퍼티 안에서 `key-a` → `val-a` 순이고, 프로퍼티끼리는 소스 순서다.
- `[3]` ★★★ **나중 것이 이기지만, 버려지는 값도 평가된다.** 로그가 `["first","mid","second"]` 로 세 개다 —
  `a: 1st` 의 값이 계산되고 나서 버려진다. **부수효과가 있는 식이면 그 부수효과는 남는다.**
  ★★ 그리고 **키의 자리는 첫 등장을 따른다** — `{"a":2,"b":9}` 에서 `a` 가 앞이다.
- `[4]` **단축 표기·메서드·화살표는 전부 `w,e,c = true,true,true` 데이터 프로퍼티**이고,
  `get`/`set` 만 **접근자**다. ★ **메서드 단축과 화살표는 `prototype` 을 안 만든다**(그래서 `new` 로 못 부른다).
- `[5]` ★★★ **`__proto__` 는 다섯 형태 중 둘에서만 특별하다.**
  `{ __proto__: P }` 와 `{ "__proto__": P }` 는 **프로토타입을 바꾸고**,
  `{ ["__proto__"]: P }`·`{ __proto__ }`(단축)·`{ __proto__() {} }`(메서드)는 **평범한 프로퍼티**를 만든다.
  ★★ 그 아래 줄이 실무에서 중요하다 — **`JSON.parse` 는 절대 프로토타입을 안 바꾼다.** `"__proto__"` 가 own 키로 들어온다.

```text
   두 축으로 자르면 뷰가 제자리를 찾는다

                 enumerable: true        enumerable: false
              ┌───────────────────────┬───────────────────────┐
   own        │  Object.keys          │                       │
              │  for...in             │  getOwnPropertyNames  │
              │  getOwnPropertyNames  │  Reflect.ownKeys      │
              │  JSON.stringify       │  in                   │
              │  { ...o }             │                       │
              ├───────────────────────┼───────────────────────┤
   상속       │  for...in             │                       │
              │  in                   │  in                   │
              └───────────────────────┴───────────────────────┘

   ★ Object.keys 는 왼쪽 위 한 칸만 본다. for...in 은 왼쪽 열 전체,
     getOwnPropertyNames 는 위쪽 행 전체, in 은 네 칸 전부다.
   ★ 심볼 키는 이 격자와 별개다 -- Reflect.ownKeys 와 getOwnPropertySymbols 만 본다.
     그런데 { ...o } 와 Object.assign 은 가져간다.
```

### (4) ★★ 일곱 가지 뷰 — 무엇이 무엇을 보나

**언제 쓰나** — 「분명히 있는데 `Object.keys` 에 안 나온다」가 나올 때.

```js
// js12b-13d-views.js
// Object.keys 대 for...in 대 getOwnPropertyNames -- 상속 x 열거가능 격자.
const proto = {};
Object.defineProperty(proto, "protoEnum", { value: "pe", enumerable: true, writable: true, configurable: true });
Object.defineProperty(proto, "protoHidden", { value: "ph", enumerable: false, writable: true, configurable: true });
const protoSym = Symbol("protoSym");
proto[protoSym] = "ps";

const o = Object.create(proto);
Object.defineProperty(o, "ownEnum", { value: "oe", enumerable: true, writable: true, configurable: true });
Object.defineProperty(o, "ownHidden", { value: "oh", enumerable: false, writable: true, configurable: true });
const ownSym = Symbol("ownSym");
o[ownSym] = "os";

const names = ["ownEnum", "ownHidden", "protoEnum", "protoHidden"];
const forIn = []; for (const k in o) forIn.push(k);
const nm = (k) => (typeof k === "symbol" ? String(k) : k);

console.log("[1] which view sees which property?");
console.log("property".padEnd(14) + "own?".padEnd(7) + "enum?".padEnd(7) +
  "keys".padEnd(7) + "for-in".padEnd(8) + "getOwnPropertyNames".padEnd(21) + "in".padEnd(6) + "hasOwn");
for (const k of names) {
  const own = Object.prototype.hasOwnProperty.call(o, k);
  const holder = own ? o : proto;
  const en = Object.getOwnPropertyDescriptor(holder, k).enumerable;
  console.log(k.padEnd(14) + String(own).padEnd(7) + String(en).padEnd(7) +
    String(Object.keys(o).includes(k)).padEnd(7) +
    String(forIn.includes(k)).padEnd(8) +
    String(Object.getOwnPropertyNames(o).includes(k)).padEnd(21) +
    String(k in o).padEnd(6) + String(own));
}
for (const [label, s] of [["ownSym", ownSym], ["protoSym", protoSym]]) {
  const own = Object.prototype.hasOwnProperty.call(o, s);
  console.log(label.padEnd(14) + String(own).padEnd(7) + "true".padEnd(7) +
    "false".padEnd(7) + "false".padEnd(8) +
    String(Object.getOwnPropertySymbols(o).includes(s)).padEnd(21) +
    String(s in o).padEnd(6) + String(own) + "   (symbols: getOwnPropertySymbols column)");
}

console.log("");
console.log("[2] the views themselves");
console.log("Object.keys(o)               " + JSON.stringify(Object.keys(o)));
console.log("for...in over o              " + JSON.stringify(forIn));
console.log("getOwnPropertyNames(o)       " + JSON.stringify(Object.getOwnPropertyNames(o)));
console.log("getOwnPropertySymbols(o)     " + JSON.stringify(Object.getOwnPropertySymbols(o).map(String)));
console.log("Reflect.ownKeys(o)           " + JSON.stringify(Reflect.ownKeys(o).map(nm)));
console.log("Object.entries(o)            " + JSON.stringify(Object.entries(o)));
console.log("JSON.stringify(o)            " + JSON.stringify(o));
console.log("{ ...o } own keys            " + JSON.stringify(Reflect.ownKeys({ ...o }).map(nm)));
console.log("Object.assign({}, o) keys    " + JSON.stringify(Reflect.ownKeys(Object.assign({}, o)).map(nm)));

console.log("");
console.log("[3] for...in walks the chain; Object.keys does not");
const gp = { fromGrandparent: 1 };
const par = Object.create(gp); par.fromParent = 2;
const kid = Object.create(par); kid.own = 3;
const walked = []; for (const k in kid) walked.push(k);
console.log("for...in over a 3-level chain  " + JSON.stringify(walked));
console.log("Object.keys                    " + JSON.stringify(Object.keys(kid)));
console.log("Object.prototype is enumerable? " + JSON.stringify(Object.keys(Object.prototype)));
```

```text
===== node20 js12b-13d-views.js (exit=0) =====
[1] which view sees which property?
property      own?   enum?  keys   for-in  getOwnPropertyNames  in    hasOwn
ownEnum       true   true   true   true    true                 true  true
ownHidden     true   false  false  false   true                 true  true
protoEnum     false  true   false  true    false                true  false
protoHidden   false  false  false  false   false                true  false
ownSym        true   true   false  false   true                 true  true   (symbols: getOwnPropertySymbols column)
protoSym      false  true   false  false   false                true  false   (symbols: getOwnPropertySymbols column)

[2] the views themselves
Object.keys(o)               ["ownEnum"]
for...in over o              ["ownEnum","protoEnum"]
getOwnPropertyNames(o)       ["ownEnum","ownHidden"]
getOwnPropertySymbols(o)     ["Symbol(ownSym)"]
Reflect.ownKeys(o)           ["ownEnum","ownHidden","Symbol(ownSym)"]
Object.entries(o)            [["ownEnum","oe"]]
JSON.stringify(o)            {"ownEnum":"oe"}
{ ...o } own keys            ["ownEnum","Symbol(ownSym)"]
Object.assign({}, o) keys    ["ownEnum","Symbol(ownSym)"]

[3] for...in walks the chain; Object.keys does not
for...in over a 3-level chain  ["own","fromParent","fromGrandparent"]
Object.keys                    ["own"]
Object.prototype is enumerable? []
```

**그림 해설.**

- ★★★ `[1]` 의 격자가 전부다. **`Object.keys` 는 「own ∧ enumerable ∧ 문자열」** 이고,
  **`for...in` 은 「enumerable ∧ 문자열」**(own 을 안 따진다), **`getOwnPropertyNames` 는 「own ∧ 문자열」**(enumerable 을 안 따진다),
  **`in` 은 아무것도 안 따진다.**
- ★★ **심볼 키는 `Object.keys` 에도 `for...in` 에도 안 나온다.** `Reflect.ownKeys` 와 `getOwnPropertySymbols` 만 본다.
  ★ 그런데 **스프레드와 `Object.assign` 은 심볼을 가져간다** — 11번에서 본 그대로다. **열거 규칙이 뷰마다 다르다.**
- ★ `[3]` `for...in` 은 **체인을 끝까지** 탄다(세 단계가 다 나온다). `Object.prototype` 의 것이 안 나오는 이유는
  **거기 있는 프로퍼티가 전부 `enumerable: false`** 이기 때문이다 — `Object.keys(Object.prototype)` 이 빈 배열인 것이 그 증거다.

### (5) ★ 같은 질문을 브라우저에 던지면

```js
// js12b-hb-browser.js
// 같은 질문을 브라우저에 던진다 -- 네 주제에 호스트가 정하는 칸이 있나.
const lines = [];
function row(k, v) { lines.push("  " + k.padEnd(38) + v); }
function attempt(label, run) {
  try { row(label, String(run())); }
  catch (e) { row(label, e.constructor.name + ": " + e.message); }
}
const J = JSON.stringify;
row("engine", navigator.userAgent.replace(/^.*(Chrome\/[0-9.]+).*$/, "$1"));
attempt("12  0 ?? 'D' / 0 || 'D'", () => J([0 ?? "D", 0 || "D"]));
attempt("12  ||= does not write", () => {
  const log = []; let v = "keep";
  const o = { get x() { return v; }, set x(n) { log.push("set"); v = n; } };
  o.x ||= "R"; return J(log);
});
attempt("12  = x || y writes", () => {
  const log = []; let v = "keep";
  const o = { get x() { return v; }, set x(n) { log.push("set"); v = n; } };
  o.x = o.x || "R"; return J(log);
});
attempt("12  a?.b[f()] skips f", () => {
  let n = 0; const o = { a: null }; void o.a?.b[(n += 1, "c")]; return "calls " + n;
});
attempt("12  a ?? b || c compiles?", () => { new Function("let a,b,c; return a ?? b || c;"); return "ok"; });
attempt("12  new a?.b() compiles?", () => { new Function("let a; return new a?.b();"); return "ok"; });
attempt("13  enumeration order", () => {
  const s = Symbol("s"); const o = {};
  o.b = 1; o[2] = 1; o[s] = 1; o.a = 1; o[1] = 1; o["01"] = 1;
  return J(Reflect.ownKeys(o).map(String));
});
attempt("13  '4294967295' is an index?", () => {
  const o = { a: 0 }; o["4294967295"] = 1; o.z = 2; return J(Object.keys(o));
});
attempt("13  computed key calls toString", () => {
  const log = []; const k = { toString() { log.push("toString"); return "K"; } };
  const o = { [k]: 1 }; return J(Object.keys(o)) + " " + J(log);
});
attempt("13  __proto__ literal vs computed", () => {
  const P = {}; return String(Object.getPrototypeOf({ "__proto__": P }) === P) + "," +
    String(Object.getPrototypeOf({ ["__proto__"]: P }) === P);
});
attempt("14  literal vs defineProperty desc", () =>
  J(Object.getOwnPropertyDescriptor({ a: 1 }, "a")) + " | " +
  J(Object.getOwnPropertyDescriptor(Object.defineProperty({}, "a", { value: 1 }), "a")));
attempt("14  isFrozen {} / prevExt {}", () =>
  J([Object.isFrozen({}), Object.isFrozen(Object.preventExtensions({}))]));
attempt("14  freeze is shallow", () => {
  const o = Object.freeze({ d: { n: 1 } }); o.d.n = 2; return J(o);
});
attempt("14  strict write to frozen", () => { "use strict"; const o = Object.freeze({ a: 1 }); o.a = 2; return "no throw"; });
attempt("15  chain of new TypeError", () => {
  const out = []; let c = Object.getPrototypeOf(new TypeError("x"));
  while (c !== null) { out.push(Object.prototype.hasOwnProperty.call(c, "constructor") ? c.constructor.name : "?"); c = Object.getPrototypeOf(c); }
  return out.join(" -> ") + " -> null";
});
attempt("15  String(Object.create(null))", () => String(Object.create(null)));
attempt("15  write does not walk", () => {
  const p = { v: "p" }; const o = Object.create(p); o.v = "o";
  return o.v + "/" + p.v + "/own:" + Object.prototype.hasOwnProperty.call(o, "v");
});
attempt("15  non-writable proto blocks", () => {
  "use strict";
  const p = Object.defineProperty({}, "v", { value: 1 }); const o = Object.create(p);
  o.v = 2; return "no throw";
});
attempt("15  Symbol.hasInstance overrides", () =>
  String("s" instanceof class { static [Symbol.hasInstance]() { return true; } }));
document.documentElement.appendChild(document.createElement("pre")).textContent =
  "===OUT===" + String.fromCharCode(10) + lines.join(String.fromCharCode(10)) + String.fromCharCode(10) + "===END===";
```

```html
<!-- js12b-page.html -->
<!doctype html>
<meta charset="utf-8">
<title>js12b</title>
<script src="js12b-hb-browser.js"></script>
```

```text
===== google-chrome --headless --dump-dom js12b-page.html | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' | sed 's/&lt;/</g; s/&gt;/>/g; s/&amp;/\&/g' (exit=0) =====
  engine                                Chrome/151.0.0.0
  12  0 ?? 'D' / 0 || 'D'               [0,"D"]
  12  ||= does not write                []
  12  = x || y writes                   ["set"]
  12  a?.b[f()] skips f                 calls 0
  12  a ?? b || c compiles?             SyntaxError: Unexpected token '||'
  12  new a?.b() compiles?              SyntaxError: Invalid optional chain from new expression
  13  enumeration order                 ["1","2","b","a","01","Symbol(s)"]
  13  '4294967295' is an index?         ["a","4294967295","z"]
  13  computed key calls toString       ["K"] ["toString"]
  13  __proto__ literal vs computed     true,false
  14  literal vs defineProperty desc    {"value":1,"writable":true,"enumerable":true,"configurable":true} | {"value":1,"writable":false,"enumerable":false,"configurable":false}
  14  isFrozen {} / prevExt {}          [false,true]
  14  freeze is shallow                 {"d":{"n":2}}
  14  strict write to frozen            TypeError: Cannot assign to read only property 'a' of object '#<Object>'
  15  chain of new TypeError            TypeError -> Error -> Object -> null
  15  String(Object.create(null))       TypeError: Cannot convert object to primitive value
  15  write does not walk               o/p/own:true
  15  non-writable proto blocks         TypeError: Cannot assign to read only property 'v' of object '#<Object>'
  15  Symbol.hasInstance overrides      true
```

★★ **호스트가 정하는 칸이 하나도 없었다.** 열거 순서·정수 키 판정·계산된 키 로그·`__proto__` 다섯 형태가 전부 Node 쪽과 같다.

## 문법 — 형태와 규칙

```text
   객체 리터럴의 일곱 형태

   { a: 1 }                 이름: 값
   { a }                    단축 표기 -- 변수 a 의 값을 a 라는 키로
   { [expr]: 1 }            계산된 키 -- expr 을 ToPropertyKey 로 통과시킨다
   { m() {} }               메서드 단축 -- prototype 을 안 만든다
   { get g() {} }           접근자 -- 읽을 때 불린다
   { set g(v) {} }          접근자 -- 쓸 때 불린다
   { ...o }                 스프레드 -- 11번 주제
```

- **키는 문자열 아니면 심볼이다.** 나머지는 전부 `ToPropertyKey` 로 문자열이 된다.
- **`ToPropertyKey` 는 심볼이면 그대로 두고, 아니면 `ToPrimitive`(힌트 `string`) → `ToString` 순으로 간다.**
- **중복 키는 나중 것이 이긴다.** 엄격 모드에서도 그렇다(ES6 이후).
- **키의 자리는 첫 등장이 정한다.** 값만 덮어쓰인다.
- **`__proto__: value` 는 리터럴 안에서만, 그리고 계산되지 않은 키·단축이 아닌 형태에서만 특별하다.**
- **열거 순서는 배열 인덱스 오름차순 → 나머지 문자열 삽입순 → 심볼 삽입순이다.**

## 어디서 틀리나

### (1) ★★★ 「넣은 순서대로 나온다」고 믿는다

숫자처럼 생긴 키가 하나라도 섞이면 **그것이 맨 앞으로 끌려간다.**
★ 특히 **ID 를 키로 쓰는 객체**(`{ 1001: …, 1000: … }`)에서 순서가 **정렬되어 버린다.**
순서가 의미를 가지면 **`Map` 이나 배열**을 쓴다.

### (2) ★★★ `"01"` 과 `"1"` 이 같은 규칙을 탈 것이라 믿는다

전수 격자의 23종 중 **여섯만** 배열 인덱스다. **0 으로 채운 ID·전화번호·우편번호는 전부 문자열 키**로 떨어진다.
★ 그래서 같은 데이터에서도 **어떤 키는 정렬되고 어떤 키는 삽입순**인, 가장 헷갈리는 상태가 만들어진다.

### (3) ★★★ `JSON.parse` 가 프로토타입을 오염시킬 수 있다고 믿는다(또는 그 반대)

`JSON.parse('{"__proto__":…}')` 는 **own 프로퍼티**를 만든다. 오염은 **그 값을 다시 `obj[k] = v` 로 옮겨 쓸 때** 생긴다.
★ 실측에서 `Object.getPrototypeOf` 가 여전히 `Object.prototype` 이었고 own 키에 `"__proto__"` 가 있었다.

### (4) ★★ 중복 키가 엄격 모드에서 막힐 것이라 믿는다

**ES5 의 규칙이다. ES6 에서 사라졌다.** 지금은 두 모드 모두 조용히 **나중 것이 이긴다.**
★ 객체를 기계로 생성하는 코드에서 **키 충돌이 경고 없이 값을 잡아먹는다.**

### (5) ★★ 버려지는 값은 평가되지 않을 것이라 믿는다

`{ a: expensive(), a: 2 }` 에서 `expensive()` 는 **불린다.** 로그가 세 개인 것이 그 증거다.

### (6) ★★ `Object.keys` 에 안 보이면 없는 것으로 친다

**심볼 키**와 **`enumerable: false` 프로퍼티**는 거기 안 나온다. `Reflect.ownKeys` 가 전수다.

### (7) ★ 계산된 키에 객체를 넣고 `valueOf` 를 기대한다

키 변환의 힌트는 **`string`** 이라 `toString` 쪽이 불린다.
★ `Symbol.toPrimitive` 가 있으면 그것이 모두를 이긴다.

### (8) ★ `{ __proto__: x }` 와 `{ ["__proto__"]: x }` 를 같은 것으로 읽는다

**전혀 다르다.** 앞엣것은 프로토타입을 바꾸고 뒤엣것은 own 프로퍼티를 만든다.

## 구현 세부사항 대 언어 보장

### 명세 보장 — 어느 엔진에서도 같아야 하는 것

- ★★★ **열거 순서 세 덩어리** — 이것은 **예전엔 「구현 나름」이라던 것이 명세로 못 박힌 자리**다.
  ES5 시절에는 순서가 규정돼 있지 않았고, ES2015 가 `[[OwnPropertyKeys]]` 로 세 덩어리를 고정했으며
  (그때 `Object.keys`·`getOwnPropertyNames`·`Reflect.ownKeys`·`JSON.stringify` 가 묶였다),
  **마지막까지 남아 있던 `for...in` 을 ES2020 이 못 박았다.**
- **키가 문자열 아니면 심볼인 것** · **`ToPropertyKey` 가 힌트 `string` 으로 `ToPrimitive` 를 부르는 것.**
- **배열 인덱스의 정의**(정수를 그대로 적은 문자열 ∧ 2³²−1 미만).
- **중복 키에서 나중 것이 이기는 것** · **자리는 첫 등장을 따르는 것** · **버려지는 값도 평가되는 것.**
- **`__proto__:` 가 리터럴의 비계산·비단축·비메서드 형태에서만 특별한 것**(Annex B — 규범적 선택 사항이지만 웹 엔진 전부가 구현한다).
- **각 리터럴 형태가 만드는 디스크립터.**

### 엔진(V8) 구현 · 이 판의 관찰

```text
===== ./js12b-vdiff.sh (exit=0) =====
js12b-12a-shortcircuit.js    identical
js12b-12b-grid.js            identical
js12b-12c-assign.js          identical
js12b-12s-strict.js          identical
js12b-12x-forms.js           identical
js12b-12y-caret.js           identical
js12b-13a-order.js           identical
js12b-13b-intkeys.js         identical
js12b-13c-computed.js        identical
js12b-13d-views.js           identical
js12b-14a-dump.js            identical
js12b-14b-configurable.js    identical
js12b-14c-freeze.js          DIFFERS
    40c40
    < fa.toSorted()   OK  [1,2,3]
    ---
    > fa.toSorted()   OK  [1,2,3]  returned [1,2,3]
js12b-14s-strict.js          identical
js12b-15a-chain.js           identical
js12b-15b-proxy.js           identical
js12b-15c-shadow.js          identical
js12b-15d-misc.js            identical
js12b-15e-pycontrast.js      identical

identical 18  ·  differs 1  ·  total 19
```

- **내부 저장 방식**(요소 배열과 프로퍼티 저장소를 나누는 것 등)은 **관찰 대상이 아니다.** 이 문서는 관찰 가능한 순서만 본다.
- **두 판(18·20)과 Chrome 151 이 이 주제에서 한 글자도 안 갈렸다** — 셋 다 V8 이기 때문이지 보장이 아니다.
  ★ **보장의 근거는 명세이고 실행은 확인**이라는 점을 그래서 위에 따로 적었다.

### 호스트가 정하는 것 — ECMA-262 밖

- **없다.** 이 주제의 브라우저 대조에서 호스트가 정하는 칸이 0개였다.

### 그래서 이렇게 적으면 틀린다

- 「객체의 키 순서는 보장되지 않는다」 — **낡았다.** ES2015 가 세 덩어리를, ES2020 이 `for...in` 을 못 박았다.
- 「숫자처럼 생긴 키는 앞으로 간다」 — **부정확하다.** `"01"`·`"1.0"`·`"-1"`·`"4294967295"` 는 안 간다.
- 「엄격 모드는 중복 키를 막는다」 — **ES5 의 이야기다.**

## 언제 쓰고 언제 안 쓰나

- **객체 리터럴** — 키가 **고정된 이름**이고 개수가 적을 때. 설정·DTO·옵션 가방.
- **`Map`** — 키가 **데이터**일 때(사용자 ID·객체 자체). ★ **삽입 순서가 의미를 가지면 이쪽이다** — 덩어리가 없다.
- **계산된 키** — 키 이름이 런타임에 정해질 때. ★ 다만 **키가 객체이면 `Map` 을 의심하라** — 문자열로 뭉개진다.
- **심볼 키** — 라이브러리가 사용자 객체에 **충돌 없이 메타데이터를 붙일 때.** 일반 열거에 안 잡히는 성질이 그 목적이다.
- **안 쓸 자리** — `__proto__` 를 평범한 데이터 키로 쓰는 것. 형태에 따라 의미가 갈려 읽는 사람이 못 믿는다.

## 핵심 문장

1. **키는 문자열 아니면 심볼이고, 그 밖의 것은 저장되기 전에 문자열이 된다.**
2. **열거 순서는 배열 인덱스 오름차순 → 나머지 문자열 삽입순 → 심볼 삽입순이고, 이것은 명세다.**
3. **「배열 인덱스」의 조건은 좁다 — 23종 중 6종만 통과했다.**
4. **계산된 키는 `ToPropertyKey` 를 부르고, 그 힌트는 `string` 이다.**
5. **중복 키는 나중 값이 이기고 첫 자리를 쓰며, 버려지는 값도 평가된다.**

## 관련 자료

- [14 — 프로퍼티 디스크립터와 동결](../14-property-descriptors-and-freezing/2-summary.md) — **그쪽이 세 플래그의 정본**이다. 여기는 **어느 문법이 어떤 디스크립터를 만드나**까지.
- [15 — 프로토타입 체인](../15-prototype-chain/2-summary.md) — **그쪽이 `__proto__` 와 체인의 정본**이다. 여기는 **리터럴에서의 특수 형태**까지.
- [11 — 스프레드와 나머지](../11-spread-and-rest/2-summary.md) — **그쪽이 `{ ...o }` 의 정본**이다. 여기는 **그것이 보는 「열거 가능」의 정의**까지.
- [02 — 강제 변환과 `==` 대 `===`](../02-coercion-and-loose-equality/2-summary.md) — **그쪽이 `ToPrimitive` 의 정본**이다.
- 목록의 **18번 주제** 「`for...in` 과 열거」 — **그쪽이 체인 순회의 정본**이다.
- 목록의 **22번 주제** 「`Symbol` 과 잘 알려진 심볼」 — **그쪽이 심볼의 정본**이다.
- Python 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **12번** 「dict 와 키 요건」 —
  파이썬의 dict 는 **3.7 부터 삽입 순서가 언어 보장**이고 **덩어리가 없다.** 키 요건도 다르다(해시 가능한 아무 값이나).
  ★ **「순서가 나중에 보장으로 승격됐다」는 점만 같고 규칙은 정반대다.**
- Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **39번** 「컬렉션 프레임워크 지도 — 인터페이스 계층과 구현체 선택」 —
  `HashMap` 은 **순서가 보장되지 않고** `LinkedHashMap` 이라야 삽입순이다. **JS 객체는 그 선택지가 없다.**

## 용어 풀이

- **프로퍼티 키(property key)** — 문자열 또는 심볼. 다른 타입은 될 수 없다.
- **`ToPropertyKey`** — 아무 값을 프로퍼티 키로 바꾸는 추상 연산. 심볼이면 그대로, 아니면 문자열로.
- **`ToPrimitive`(힌트 `string`)** — 객체를 원시값으로 바꾸는 절차. `Symbol.toPrimitive` → `toString` → `valueOf` 순으로 시도한다.
- **배열 인덱스(array index)** — 정수를 그대로 적은 문자열이면서 2³²−1 미만인 키. 열거 순서의 첫 덩어리.
- **계산된 키(computed key)** — `{ [expr]: v }` 형태. 대괄호 안의 식을 평가해 키로 쓴다.
- **단축 표기(shorthand)** — `{ a }` 가 `{ a: a }` 와 같은 것.
- **메서드 단축(method shorthand)** — `{ m() {} }`. `prototype` 을 만들지 않아 `new` 로 못 부른다.
- **접근자 프로퍼티(accessor property)** — 값 대신 `get`/`set` 함수를 들고 있는 프로퍼티.
- **열거 가능(enumerable)** — `Object.keys`·`for...in`·`JSON.stringify` 에 보일지를 정하는 플래그.
- **own 프로퍼티** — 프로토타입이 아니라 그 객체 자신이 들고 있는 프로퍼티.

## 더 들어가면

- **열거 순서가 명세로 올라온 과정 자체가 교훈이다.** 「구현 나름」이던 것을 고정하려면
  **이미 모든 엔진이 하던 일**을 골라야 했고, 그래서 **정수 키 우선**이라는 다소 기묘한 규칙이 표준이 됐다.
  ★ 결이 비슷한 자리가 이 갈래에 하나 더 있다 — **14번의 디스크립터**는
  「프로퍼티에 값 말고 무엇이 더 붙어 있나」를 **코드로 볼 수 있게 연 API** 다. 그쪽 문서가 그 이력을 따로 다룬다.
- **`__proto__` 의 두 얼굴**(리터럴 문법 / `Object.prototype` 의 접근자)은 15번에서 갈라 본다.
  둘은 **다른 물건**인데 이름이 같아 가장 많이 헷갈린다.
- **키가 늘 문자열이라는 사실이 `Map` 의 존재 이유**다. 객체를 키로 쓰고 싶으면 객체 리터럴로는 원리상 안 된다 —
  `toString` 이 불려 **전부 `"[object Object]"` 한 서랍에 겹쳐 들어간다.**
