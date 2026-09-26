# js/syntax/13 — 객체 리터럴과 프로퍼티: 「키는 전부 문자열이고, 정수처럼 생긴 것만 앞줄에 선다」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v18.19.1(기본 PATH) · v20.19.6(nvm) · Google Chrome 151.0.7922.173 · x86-64 Linux.
> 배너의 `node20` 은 v20.19.6, `node18` 은 v18.19.1 이다.
>
> ★★★ **이 주제의 본체는 ② 전수 격자다.**
> 「정수 키」의 경계는 **규칙을 외워서 맞히는 자리가 아니라 던져서 갈라야** 하는 자리다 —
> `"1"`·`"01"`·`"1.0"`·`"4294967295"` 가 **눈으로는 전부 숫자처럼 보이는데 답이 갈린다.**
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① **무엇이 키가 되나** ② ★★★ **나오는 순서를 무엇이 정하나** ③ **어느 뷰가 무엇을 보나**.
> ★★ **아래 1·2번은 「출력을 그대로 적어 보라」가 아니라 「순서와 개수를 적어 보라」가 과녁**이다.
> 스물세 줄을 다 맞히려 들지 말고 **경계가 어디인지**를 먼저 대라.
> ★★★ **이 주제에는 두 판이 갈린 줄이 하나도 없다.** 그래서 「판이 갈렸나」를 묻는 문항이 없다 —
> 대신 **「이 순서가 왜 보장인가」** 를 묻는다.
>
> **선행** — [12 — 옵셔널 체이닝·널 병합·논리 할당](../12-optional-chaining-nullish-and-logical-assignment/2-summary.md) · [11 — 스프레드와 나머지](../11-spread-and-rest/2-summary.md) · [02 — 강제 변환과 `==` 대 `===`](../02-coercion-and-loose-equality/2-summary.md) · [01 — 값의 종류와 `typeof`](../01-value-types-and-typeof/2-summary.md).

## 이 파일을 푸는 법

- ★★ **예측형 네 문항(1\~4)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **1번은 「무엇이 나오나」가 아니라 「무슨 순서로 나오나」를** 적어야 답이다. 덩어리를 먼저 그려라.
- ★★★ **2번은 스물세 줄 중 몇 줄이 어느 쪽인지를 숫자로** 적어야 답이다.
- ★★ **3번은 「무엇이 불렸나」를 적어야** 답이다. 값만 적으면 절반도 못 맞힌 것이다.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이것은 명세인가, 호스트인가, 이 엔진의 사정인가**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 넣은 순서와 나온 순서 (예측) ★★★ 이 주제의 축

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

- ★★★ `[1]` 의 오른쪽 칸(`ownKeys`)에 **열한 개 키가 어떤 순서로** 나오는가?
- ★★★ `bucket` 칸의 세 값이 **몇 개씩** 나뉘는가?
- ★★ `[2]` 의 **일곱 뷰가 전부 같은 순서**인가? 다른 것이 있다면 무엇이 다른가?
- ★★ `[3]` 에서 **문자열 키를 지웠다 다시 넣으면** 자리가 유지되는가? **정수 키는?**
- ★ `[4]` 의 `Map` 은 같은 열한 쌍을 어떤 순서로 내놓는가?

### 2. 어떤 키가 앞줄에 서는가 (예측) ★★★

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

- ★★★ 스물세 후보 중 **`ARRAY INDEX` 로 판정되는 것은 몇 개**이고 무엇인가?
- ★★★ `"4294967295"` 와 `"4294967294"` 는 **같은 쪽인가 다른 쪽인가**? 그 자리에서 갈리는 이유는?
- ★★ `"01"`·`"1.0"`·`"-0"`·`"1e2"` 는 각각 어느 쪽인가?
- ★★ `[3]` 에서 `n[1]`·`n["1"]`·`n[1.0]` 세 번 쓰면 **서랍이 몇 개** 생기는가?
- ★ `big[1e21]` 의 키는 무슨 글자가 되는가?

### 3. 키 자리에 객체를 넣으면 (예측) ★★★

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

- ★★★ `[1]` 첫 줄에서 **`toString` 과 `valueOf` 중 무엇이 불리는가**? 둘 다 있는데도 그런가?
- ★★★ `Symbol.toPrimitive` 가 있으면 무엇이 이기고, **힌트는 무엇**인가?
- ★★ 같은 객체로 **읽기만** 할 때도(`o3[plain]`) 로그가 찍히는가?
- ★★ `[3]` 에서 중복 키의 **버려지는 값**은 평가되는가? **키의 자리**는 첫 등장인가 마지막 등장인가?
- ★★★ `[5]` 의 **다섯 형태 중 프로토타입이 바뀌는 것은 몇 개**인가?
- ★ `JSON.parse('{"__proto__":…}')` 는 프로토타입을 바꾸는가?

### 4. 어느 뷰가 무엇을 보는가 (예측) ★★

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

- ★★★ `[1]` 의 격자에서 **`Object.keys` 칸이 `true` 인 줄은 몇 줄**인가?
- ★★★ `for...in` 과 `getOwnPropertyNames` 는 **서로 다른 한 칸씩**을 본다 — 각각 어느 줄인가?
- ★★ **심볼 키**는 `Object.keys` 와 `for...in` 중 어디에 나오는가?
- ★★ 그런데 `{ ...o }` 와 `Object.assign` 은 심볼을 가져가는가?
- ★ `[3]` 의 마지막 줄이 `[]` 인 것은 **무엇을 증명**하는가?

### 5. 키가 될 수 있는 것은 무엇인가 (경계) ★★★

- ★★★ 프로퍼티 키가 될 수 있는 타입은 **몇 가지**이고 무엇인가?
- ★★ 그 밖의 값을 키 자리에 넣으면 **누가 무엇으로 바꾸는가**?
- ★ `o[-0]` 의 키와 `o[0]` 의 키는 같은가 다른가? 그 답이 **33번 주제의 `Object.is`** 와 어떻게 어긋나는가?

### 6. 「배열 인덱스」의 조건을 한 문장으로 (경계) ★★★

- ★★★ 「숫자로 읽히면 배열 인덱스」가 **왜 틀린 진술**인가? 반례 셋을 대면?
- ★★ 상한이 2³²−1 인 이유는 무엇과 묶여 있는가?
- ★ 배열에 `a[4294967295] = 1` 을 하면 `length` 는 얼마가 되는가?

### 7. 중복 키는 왜 조용히 지나가는가 (왜) ★★

- ★★★ 엄격 모드가 중복 키를 막는가? **어느 판의 이야기인가**?
- ★★ 「나중 것이 이긴다」와 「첫 자리를 쓴다」가 **동시에 성립**하는 것을 어떻게 확인했는가?
- ★ 이것이 실무에서 위험한 자리는 어디인가?

### 8. `__proto__` 는 어디서 특별한가 (경계) ★★★

- ★★★ `{ __proto__: x }` 와 `{ ["__proto__"]: x }` 가 **왜 다른가**?
- ★★ 단축 표기 `{ __proto__ }` 와 메서드 `{ __proto__() {} }` 는 어느 쪽인가?
- ★★ 이 문법은 **명세의 어느 자리**에 있는가 — 본문인가 부록인가? 그래도 믿어도 되는 이유는?
- ★ `JSON.parse` 의 결과를 `obj[k] = v` 로 옮겨 쓰면 무엇이 달라지는가?

### 9. 이 순서는 왜 「보장」인가 (연결) ★★★

- ★★★ 「객체의 키 순서는 보장되지 않는다」는 말은 **언제까지 맞았는가**?
- ★★★ 두 판과 브라우저에서 **같은 줄이 나온 것**이 보장의 근거가 되는가? 되지 않는다면 근거는 무엇인가?
- ★★ `Object.keys`·`for...in`·`JSON.stringify` 가 그 순서에 묶인 것은 **`Reflect.ownKeys` 와 같은 판인가**?
- ★ 이 주제에서 **순서를 그대로 실은 블록**이 규칙 위반이 아닌 이유를 한 문장으로.

### 10. 보장인가 엔진 사정인가 (연결) ★★★

- 이 주제에서 **두 판이 갈린 칸은 몇 개**였는가?
- ★★ 브라우저에 같은 줄을 던졌을 때 **호스트가 정하는 칸은 몇 개**였는가?
- ★★★ 이 주제에서 **부적용인 창**은 무엇이고, 「안 쟀다」와 어떻게 다른가?
- ★ 엔진이 내부적으로 정수 키를 따로 저장한다는 이야기를 **이 문서가 근거로 쓸 수 있는가**?

### 11. 경계 — 어디까지가 이 주제인가 (연결) ★★

- **세 플래그의 의미** · **체인 순회** · **심볼의 성질** · **`ToPrimitive`** 는 각각 어느 주제가 정본인가?
- ★★★ 11번이 실측한 「`{ ...o }` 는 자기 것이고 열거 가능한 것만 가져간다」에서,
  이 주제가 **채워 넣은 정의**는 무엇인가?
- ★★ 파이썬의 dict 와 이 주제가 **같은 것**과 **정반대인 것**을 각각 하나씩 대면?
- ★ 이 주제가 **끝까지 책임지는 것** 세 가지를 대면?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
