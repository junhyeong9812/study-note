# js/syntax/12 — 옵셔널 체이닝·널 병합·논리 할당: 「안 부르는 것」이 전부다 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> ★★★ **이 주제의 본체는 ① 추상 연산에 로그 심기다.**
> `?.`·`??`·`??=` 세 문법이 하는 일은 **무엇을 만드는 것이 아니라 무엇을 안 하는 것**이다.
> 안 한 일은 **값에 흔적을 남기지 않는다** — `o.x ||= 'R'` 와 `o.x = o.x || 'R'` 는 **끝난 값이 한 글자도 같고**
> 갈리는 것은 **setter 가 불렸느냐 하나뿐**이다.
> 그래서 이 주제의 근거는 전부 **호출 횟수 로그**이고, 그 중 결정적인 것은 「**0회**」다.
> ② 전수 격자가 `??` 와 `||` 가 갈리는 칸을 세고, ④ 예외의 종류와 문구가 엄격/비엄격의 경계를 가른다.
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262 최신 초안](https://tc39.es/ecma262/) — Optional Chains · Coalesce Expression · Logical Assignment Operators · `delete` 연산자
> - [ECMA-262 판별 아카이브](https://262.ecma-international.org/) — `?.`/`??` 가 ES2020, 논리 할당이 ES2021 인 것을 가릴 때
> - [MDN — Optional chaining](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Optional_chaining) · [MDN — Nullish coalescing](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Nullish_coalescing)
>
> ★★★ **명세 조항 번호는 인용하지 않는다.** 규칙 진술은 위 문서로, **값·예외 타입과 메시지는 전부 실행으로** 접지했다.
>
> **실행 검증** — 이 문서의 모든 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮겨 적은 출력이 하나도 없다).
> 배너의 `node20` 은 `~/.nvm/versions/node/v20.19.6/bin/node`, `node18` 은 기본 PATH 의 `node`(v18.19.1)다.
>
> ★★ **던지는 형태를 하나로 고정했다** — 예외는 `try`/`catch` 로 받아 `e.constructor.name` 과 `e.message` 만 찍는다.
> Node 의 스택트레이스에는 **절대 경로**가 박혀 다른 머신에서 재현이 안 되기 때문이다.
> ★★ **`SyntaxError` 는 `try`/`catch` 로 못 잡는다** — 그래서 문법 격자는 `new Function(소스)` 으로 **컴파일만** 해 본다.
> ★★★ **캐럿이 필요한 자리는 `vm.Script` 에 파일명을 박아 던졌다** — `node --check` 는 **절대 경로를 찍어** 재현이 안 된다.
> ★★ **이 문서의 모든 블록은 표준 출력뿐이다** — 표준 오류와 섞은 블록이 하나도 없다.
>
> **버전** — **`?.` 와 `??` 는 ES2020**, **`??=`·`||=`·`&&=` 는 ES2021** 이다.
> ★ 한 묶음처럼 보이지만 **한 판에 들어온 문법이 아니다.**
>
> **★★★ 이 주제가 쓰는 창 — 그리고 부적용인 창**
>
> | 창 | 이 주제에서 무엇을 보나 |
> |---|---|
> | ★★★ **① 추상 연산에 로그 심기**(본체) | getter·setter·함수에 카운터를 달아 **호출 횟수 0** 을 찍는다. 단축 평가는 **오직 이것으로만** 보인다 |
> | ★★★ **② 전수 격자** | `??` 대 `\|\|` 가 falsy 13종에서 갈리는 칸 수 · 엄격/비엄격 11칸 · 문법 20형태 |
> | ★★ **④ 예외의 `constructor.name` + `message`** | 엄격 모드에서만 나오는 `TypeError` · `SyntaxError` 의 문구 |
> | ★★ **진단의 `(행,열)`**(18-C) | `a ?? b \|\| c` 가 **어느 열에서** 거부되나 — 값으로는 원리상 못 가른다 |
> | ★★ **두 번 컴파일**(엄격 먼저 / 비엄격 나중) | **설정에 달린 칸이 몇 개인가** — 11칸 중 **6칸**이었다 |
> | ★ **⑤ 두 판 대조기 + 브라우저** | 판이 갈린 칸 · 호스트가 정하는 칸이 있나 — **이 주제에서는 0** |
> | ★ **부적용 — ③ 브랜드 태그**(`Object.prototype.toString.call`) | `?.`·`??` 는 값의 **종류**를 묻지 않는다. `null`/`undefined` 인지만 본다 — **잴 것이 없다** |
> | ★ **부적용 — 성능 측정** | 「`?.` 가 느리다」는 **재지 않았다.** 이 문서에 속도 주장이 한 줄도 없다 |
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | Node 스택트레이스의 **절대 경로** — 한 줄도 싣지 않았다 | ★★★ **호출 횟수**(특히 0회) |
> | 예외 **문구**(판이 오르면 바뀐다) | ★★★ **예외의 종류** · `SyntaxError` 가 가리키는 **열** |
> | 브라우저 UA 문자열의 뒷자리 | ★★ **격자의 SAME/SPLIT 판정** · 전역 오염 목록 |
>
> ★★ **이 주제의 블록에는 주소도 시간도 난수도 한 곳도 안 찍힌다.** 같은 판에서 다시 돌리면 **한 글자도 안 변한다.**
> ★★★ **두 판이 갈린 블록은 이 주제에 0개다**(전체 19블록 중 갈린 것은 14번 주제의 `toSorted` 한 블록뿐이다).
>
> **선행** — [11 — 스프레드와 나머지](../11-spread-and-rest/2-summary.md) · [10 — 구조 분해 할당](../10-destructuring-assignment/2-summary.md) · [02 — 강제 변환과 `==` 대 `===`](../02-coercion-and-loose-equality/2-summary.md) · [01 — 값의 종류와 `typeof`](../01-value-types-and-typeof/2-summary.md).
> ★★★ **02번이 이 주제의 뿌리다.** `||` 가 보는 것은 **truthy/falsy**(`ToBoolean`)이고 `??` 가 보는 것은 **`null`/`undefined` 둘뿐**이다.
> 「무엇을 거짓으로 치나」의 정본은 02번이고, 여기서는 **그 목록이 기본값 문법에서 만드는 사고**만 본다.
> ★★ **10번이 바로 앞에서 같은 갈림을 실측했다** — 구조 분해의 기본값은 **`undefined` 에만** 걸리고 `null` 에는 안 걸린다.
> `??` 는 그 짝이 아니다 — **`null` 도 막는다.** 두 문법이 「비었다」를 **서로 다르게 센다**는 것이 이 주제의 첫 매듭이다.
> **이어지는 곳** — 목록의 **33번 주제** 「동등성 세 종류」 · 목록의 **35번 주제** 「엄격 모드」 · [14 — 프로퍼티 디스크립터와 동결](../14-property-descriptors-and-freezing/2-summary.md)
>
> ★★ **경계 — 엄격 모드가 바꾸는 규칙 전부는 35번이 정본이다.** 여기서는 **논리 할당이 실패하는 자리에서 모드가 만드는 차이**까지다.
> ★★ **경계 — `Object.is`·SameValueZero 는 33번이 정본이다.** 여기서는 `??` 가 **`null`/`undefined` 만 본다**는 사실까지다.
> ★★ **경계 — 왜 쓰기가 막히는가(디스크립터·동결)는 14번이 정본이다.** 여기서는 **막혔을 때 무엇이 보이나**까지다.

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

**세 문법은 전부 「하던 일을 도중에 그만두는」 장치다.**
값을 만드는 문법이 아니라 **평가를 멈추는** 문법이라서, 무엇이 나왔는지가 아니라 **무엇을 건너뛰었는지**를 봐야 한다.

- **`?.`** — 왼쪽이 `null`/`undefined` 면 **그 뒤의 사슬 전체**를 건너뛰고 `undefined` 를 내놓는다.
- **`??`** — 왼쪽이 `null`/`undefined` 일 때**만** 오른쪽을 평가한다.
- **`??=`·`||=`·`&&=`** — 조건이 안 맞으면 **대입 자체를 하지 않는다**(오른쪽도 평가 안 하고 setter 도 안 부른다).

```text
   자물쇠 세 개가 달린 복도

   o.a   ?.   b   .c   .d
    │    │
    │    └── 왼쪽이 null/undefined 이면
    │        여기서 복도가 끝난다. b 도 c 도 d 도 안 본다.
    └── 왼쪽이 0 · '' · false · NaN 이면 자물쇠가 안 걸린다. 그냥 지나간다.

   ★ 자물쇠가 걸리면 그 뒤의 대괄호 안 식도, 괄호 안 인자도 아예 평가되지 않는다.
```

```text
   같은 결과, 다른 일

   o.x ||= 'R'            o.x = o.x || 'R'
   ┌──────────────┐       ┌──────────────┐
   │ get  o.x     │       │ get  o.x     │
   │ truthy 면 끝 │       │ truthy 라도  │
   │ (set 안 함)  │       │ set 을 한다  │
   └──────────────┘       └──────────────┘
        setter 0회              setter 1회

   ★ 두 줄의 「끝난 값」은 한 글자도 같다. 갈리는 것은 로그뿐이다.
```

```text
   세 연산자가 보는 것이 다르다

   값 여덟 개를 두 개의 원으로 갈라 보면

   falsy 여덟                       nullish 둘
   ┌──────────────────────────────┐
   │ false  0  -0  0n  ''  NaN    │   <- || 와 ||= 가 여기 전부에 반응한다
   │                ┌─────────────┴──┐
   │                │ null undefined │ <- ?? 와 ??= 와 ?. 는 여기 둘에만 반응한다
   └────────────────┴────────────────┘
                    ↑
        겹치는 둘에서는 ?? 와 || 의 답이 같다.
        갈리는 것은 왼쪽 여섯 -- 이 여섯이 「?? 로 바꿨더니 달라졌다」의 범인이다.
```

> **단축 평가(short-circuit evaluation)** — 답이 이미 정해졌으면 나머지를 아예 계산하지 않는 것.\
> 예: `false && f()` 에서 `f()` 는 호출되지 않는다. 결과만 보면 알 수 없고, `f` 안에 로그를 심어야 보인다.

## 이 주제가 답하려는 질문

1. **`?.` 는 어디까지 건너뛰는가** — 한 칸인가, 사슬 전체인가? 괄호를 치면 무엇이 달라지나?
2. **`??` 와 `||` 는 어느 값에서 갈리는가** — 그리고 그 목록은 누가 정하나?
3. **`??=` 가 「대입을 안 한다」는 것을 무엇으로 증명하는가** — 값으로는 안 갈린다면?

## 동작 방식

### (1) ★★★ 단축 평가를 「안 불린 것」으로 증명한다

**언제 쓰나** — 「`?.` 를 썼으니 안전하다」를 믿기 전에, **무엇이 건너뛰어졌는지**를 눈으로 봐야 할 때.

```js
// js12b-12a-shortcircuit.js
// 단축 평가를 「안 불린 것」으로 증명한다 -- 값이 아니라 호출 횟수로.
// 격자의 라벨은 전부 ASCII 다(폭이 안 맞으면 표가 깨진다).
// 예외는 try/catch 로 받아 e.constructor.name + e.message 만 찍는다.
const row = (a, b, c) => console.log(String(a).padEnd(34) + String(b).padEnd(12) + c);

function probe() {
  let n = 0;
  return { calls: () => n, f: (v) => { n += 1; return v; } };
}

console.log("[1] argument of ?.[] and ?.() is never evaluated when the chain is cut");
row("expression", "result", "probe calls");
{
  const p = probe(); const o = { a: null };
  const r = o.a?.[p.f("k")];
  row("o.a?.[f('k')]        a=null", String(r), p.calls());
}
{
  const p = probe(); const o = { a: { k: "hit" } };
  row("o.a?.[f('k')]        a=obj", String(o.a?.[p.f("k")]), p.calls());
}
{
  const p = probe(); const o = {};
  row("o.fn?.(f(1))         no fn", String(o.fn?.(p.f(1))), p.calls());
}
{
  const p = probe(); const o = { fn: (x) => "got" + x };
  row("o.fn?.(f(1))         has fn", String(o.fn?.(p.f(1))), p.calls());
}

console.log("");
console.log("[2] was the right-hand side called?  ??  vs  ||  vs  &&");
row("expression", "result", "rhs calls");
for (const [label, left] of [["0", 0], ["null", null], ["undefined", undefined], ["'x'", "x"]]) {
  const p1 = probe(); const r1 = left ?? p1.f("R");
  row(("left=" + label).padEnd(18) + "left ?? f('R')", String(r1), p1.calls());
  const p2 = probe(); const r2 = left || p2.f("R");
  row(("left=" + label).padEnd(18) + "left || f('R')", String(r2), p2.calls());
  const p3 = probe(); const r3 = left && p3.f("R");
  row(("left=" + label).padEnd(18) + "left && f('R')", String(r3), p3.calls());
}

console.log("");
console.log("[3] a?.b.c short-circuits the WHOLE chain; parentheses end it");
const show = (tag, fn) => {
  try { console.log(tag.padEnd(26) + "-> " + String(fn())); }
  catch (e) { console.log(tag.padEnd(26) + "-> " + e.constructor.name + " " + e.message); }
};
const nil = { a: null };
show("nil.a?.b.c", () => nil.a?.b.c);
show("nil.a?.b.c.d.e", () => nil.a?.b.c.d.e);
show("(nil.a?.b).c", () => (nil.a?.b).c);
show("nil.a.b.c", () => nil.a.b.c);
show("nil.a?.b?.c", () => nil.a?.b?.c);
{
  const p = probe(); const deep = { a: null };
  const r = deep.a?.b[p.f("c")].d;
  console.log("deep.a?.b[f('c')].d".padEnd(26) + "-> " + String(r) + "   probe calls " + p.calls());
}

console.log("");
console.log("[4] ?. stops at null and undefined ONLY");
row("value", "v?.ctor", "v?.nope");
for (const [label, v] of [["0", 0], ["-0", -0], ["''", ""], ["NaN", NaN], ["false", false],
                          ["0n", 0n], ["null", null], ["undefined", undefined]]) {
  row(label, String(v?.constructor?.name), String(v?.nope));
}

console.log("");
console.log("[5] delete a?.b");
const del = { a: null };
show("delete del.a?.b", () => delete del.a?.b);
const del2 = { a: { b: 1 } };
show("delete del2.a?.b", () => delete del2.a?.b);
console.log("keys of del2.a after delete -> " + JSON.stringify(Object.keys(del2.a)));
```

```text
===== node20 js12b-12a-shortcircuit.js (exit=0) =====
[1] argument of ?.[] and ?.() is never evaluated when the chain is cut
expression                        result      probe calls
o.a?.[f('k')]        a=null       undefined   0
o.a?.[f('k')]        a=obj        hit         1
o.fn?.(f(1))         no fn        undefined   0
o.fn?.(f(1))         has fn       got1        1

[2] was the right-hand side called?  ??  vs  ||  vs  &&
expression                        result      rhs calls
left=0            left ?? f('R')  0           0
left=0            left || f('R')  R           1
left=0            left && f('R')  0           0
left=null         left ?? f('R')  R           1
left=null         left || f('R')  R           1
left=null         left && f('R')  null        0
left=undefined    left ?? f('R')  R           1
left=undefined    left || f('R')  R           1
left=undefined    left && f('R')  undefined   0
left='x'          left ?? f('R')  x           0
left='x'          left || f('R')  x           0
left='x'          left && f('R')  R           1

[3] a?.b.c short-circuits the WHOLE chain; parentheses end it
nil.a?.b.c                -> undefined
nil.a?.b.c.d.e            -> undefined
(nil.a?.b).c              -> TypeError Cannot read properties of undefined (reading 'c')
nil.a.b.c                 -> TypeError Cannot read properties of null (reading 'b')
nil.a?.b?.c               -> undefined
deep.a?.b[f('c')].d       -> undefined   probe calls 0

[4] ?. stops at null and undefined ONLY
value                             v?.ctor     v?.nope
0                                 Number      undefined
-0                                Number      undefined
''                                String      undefined
NaN                               Number      undefined
false                             Boolean     undefined
0n                                BigInt      undefined
null                              undefined   undefined
undefined                         undefined   undefined

[5] delete a?.b
delete del.a?.b           -> true
delete del2.a?.b          -> true
keys of del2.a after delete -> []
```

**그림 해설 — 한 단계에 한 문장.**

- `[1]` **대괄호 안의 식과 괄호 안의 인자가 아예 평가되지 않는다.** `o.a` 가 `null` 이면 탐침 호출이 **0회**다.
  값만 보면 `undefined` 뿐이라 갈리지 않는다 — **0 이라는 숫자가 유일한 근거**다.
- `[2]` `??` 는 `0` 에서 오른쪽을 **안 부르고**, `||` 는 **부른다.** 같은 자리에서 `&&` 는 정반대로 움직인다.
- `[3]` ★★★ **`nil.a?.b.c.d.e` 가 통째로 조용하다.** `?.` 뒤의 `.c`·`.d`·`.e` 는 **평범한 점**인데도 안 터진다 —
  옵셔널 체인은 **한 칸이 아니라 사슬 전체**를 단위로 끊기 때문이다.
  ★ **괄호가 사슬을 끝낸다** — `(nil.a?.b).c` 는 `TypeError` 다. 괄호 안에서 사슬이 닫히고, 그 결과 `undefined` 에 `.c` 를 다시 건 것이다.
- `[4]` `?.` 는 **`0`·`-0`·`''`·`NaN`·`false`·`0n` 을 전부 통과시킨다.** 막는 것은 `null` 과 `undefined` 둘뿐이다.
- `[5]` `delete nil.a?.b` 는 **터지지 않고 `true`** 를 내놓는다. 지운 것이 없어도 `true` 다.

**비용** — 추가 비용은 **재지 않았다.** 이 문서에 속도 주장은 한 줄도 없다.

### (2) ★★ `??` 대 `||` — falsy 13종 전수 격자

**언제 쓰나** — 기본값을 주는 자리에서 `||` 를 `??` 로 바꿔도 되는지(또는 그 반대) 판단할 때.

```js
// js12b-12b-grid.js
// ?? 대 || 전수 격자 -- 어느 칸에서 갈리나. 라벨은 전부 ASCII.
// 값 자체를 찍으면 -0 과 0 이, "" 와 0 이 구분되지 않으므로 라벨을 따로 들고 다닌다.
const D = "DEF";
const cases = [
  ["0", 0], ["-0", -0], ["''", ""], ["NaN", NaN], ["false", false],
  ["0n", 0n], ["null", null], ["undefined", undefined],
  ["'0'", "0"], ["[]", []], ["{}", {}], ["' '", " "], ["1", 1],
];
const tag = (v) => {
  if (v === null) return "null";
  if (v === undefined) return "undefined";
  if (typeof v === "number" && Object.is(v, -0)) return "-0";
  if (typeof v === "string") return "'" + v + "'";
  if (typeof v === "bigint") return String(v) + "n";
  if (Array.isArray(v)) return "[]";
  if (typeof v === "object") return "{}";
  return String(v);
};

console.log("[1] v ?? DEF   vs   v || DEF   vs   v && DEF");
console.log("value".padEnd(12) + "truthy".padEnd(9) + "nullish".padEnd(9) +
            "v ?? DEF".padEnd(12) + "v || DEF".padEnd(12) + "v && DEF".padEnd(12) + "?? vs ||");
let split = 0;
for (const [label, v] of cases) {
  const a = v ?? D, b = v || D, c = v && D;
  const same = Object.is(a, b);
  if (!same) split += 1;
  console.log(label.padEnd(12) + String(Boolean(v)).padEnd(9) +
    String(v === null || v === undefined).padEnd(9) +
    tag(a).padEnd(12) + tag(b).padEnd(12) + tag(c).padEnd(12) + (same ? "same" : "SPLIT"));
}
console.log("");
console.log("split cells " + split + " / " + cases.length);

console.log("");
console.log("[2] the same grid written as a default-value idiom");
const port = (v) => v ?? 8080;
const portOr = (v) => v || 8080;
console.log("input".padEnd(12) + "v ?? 8080".padEnd(12) + "v || 8080");
for (const [label, v] of [["0", 0], ["''", ""], ["false", false], ["null", null], ["undefined", undefined], ["3000", 3000]]) {
  console.log(label.padEnd(12) + tag(port(v)).padEnd(12) + tag(portOr(v)));
}

console.log("");
console.log("[3] ?? is NOT the same as an isNullish() call: it also short-circuits");
let n = 0;
const expensive = () => { n += 1; return 8080; };
n = 0; const r1 = 0 ?? expensive();
console.log("0 ?? expensive()      -> " + r1 + "   calls " + n);
n = 0; const r2 = 0 || expensive();
console.log("0 || expensive()      -> " + r2 + "   calls " + n);
n = 0; const r3 = (0 === null || 0 === undefined) ? expensive() : 0;
console.log("ternary on isNullish  -> " + r3 + "   calls " + n);
```

```text
===== node20 js12b-12b-grid.js (exit=0) =====
[1] v ?? DEF   vs   v || DEF   vs   v && DEF
value       truthy   nullish  v ?? DEF    v || DEF    v && DEF    ?? vs ||
0           false    false    0           'DEF'       0           SPLIT
-0          false    false    -0          'DEF'       -0          SPLIT
''          false    false    ''          'DEF'       ''          SPLIT
NaN         false    false    NaN         'DEF'       NaN         SPLIT
false       false    false    false       'DEF'       false       SPLIT
0n          false    false    0n          'DEF'       0n          SPLIT
null        false    true     'DEF'       'DEF'       null        same
undefined   false    true     'DEF'       'DEF'       undefined   same
'0'         true     false    '0'         '0'         'DEF'       same
[]          true     false    []          []          'DEF'       same
{}          true     false    {}          {}          'DEF'       same
' '         true     false    ' '         ' '         'DEF'       same
1           true     false    1           1           'DEF'       same

split cells 6 / 13

[2] the same grid written as a default-value idiom
input       v ?? 8080   v || 8080
0           0           8080
''          ''          8080
false       false       8080
null        8080        8080
undefined   8080        8080
3000        3000        3000

[3] ?? is NOT the same as an isNullish() call: it also short-circuits
0 ?? expensive()      -> 0   calls 0
0 || expensive()      -> 8080   calls 1
ternary on isNullish  -> 0   calls 0
```

**그림 해설.**

- ★★★ **갈린 칸은 13칸 중 6칸**이고, 그 여섯은 전부 **falsy 인데 nullish 가 아닌 값**이다 — `0`·`-0`·`''`·`NaN`·`false`·`0n`.
- ★★ `null`·`undefined` 에서는 **두 연산자가 같은 답**을 낸다. 그래서 「`??` 로 바꿨더니 갑자기 달라졌다」는
  **`null` 때문이 아니라 `0` 이나 `''` 때문**이다.
- ★ `[3]` 이 중요한 단서다 — `??` 는 「nullish 인지 검사하는 함수」가 아니라 **연산자**라서, 아니면 **오른쪽을 평가조차 안 한다.**
  `isNullish(x) ? f() : x` 로 손수 쓴 삼항과 **호출 횟수가 같다**는 것이 그 확인이다.

### (3) ★★★ `||=` 와 `= x || y` 의 차이는 setter 로그에만 있다

**언제 쓰나** — 프록시·getter/setter·동결된 객체가 섞인 코드에서 「그냥 같은 거 아닌가」를 확인할 때.

```js
// js12b-12c-assign.js
// ||= 와 = x || y 의 차이는 값이 아니라 「setter 가 불렸나」에 있다.
// setter 와 오른쪽 식에 각각 로그를 심어 호출 횟수로 가른다.
function box(init) {
  const log = [];
  let v = init;
  const o = {
    get x() { log.push("get"); return v; },
    set x(n) { log.push("set:" + String(n)); v = n; },
  };
  return { o, log, read: () => v };
}
function rhs(val) {
  let n = 0;
  return { calls: () => n, v: () => { n += 1; return val; } };
}
const tag = (v) => (typeof v === "string" ? "'" + v + "'" : String(v));

console.log("[1] b.x ||= R   vs   b.x = b.x || R      (same value, different writes)");
console.log("start".padEnd(10) + "form".padEnd(22) + "final".padEnd(10) +
            "rhs calls".padEnd(11) + "setter log");
for (const [label, init] of [["'keep'", "keep"], ["0", 0], ["''", ""], ["null", null]]) {
  {
    const b = box(init); const r = rhs("R");
    b.o.x ||= r.v();
    console.log(label.padEnd(10) + "b.x ||= R".padEnd(22) + tag(b.read()).padEnd(10) +
      String(r.calls()).padEnd(11) + JSON.stringify(b.log));
  }
  {
    const b = box(init); const r = rhs("R");
    b.o.x = b.o.x || r.v();
    console.log(label.padEnd(10) + "b.x = b.x || R".padEnd(22) + tag(b.read()).padEnd(10) +
      String(r.calls()).padEnd(11) + JSON.stringify(b.log));
  }
}

console.log("");
console.log("[2] ??=  vs  ||=  vs  &&=      (setter log is the answer)");
console.log("start".padEnd(10) + "form".padEnd(12) + "final".padEnd(10) +
            "rhs calls".padEnd(11) + "setter log");
for (const [label, init] of [["0", 0], ["''", ""], ["null", null], ["undefined", undefined], ["'v'", "v"]]) {
  for (const form of ["??=", "||=", "&&="]) {
    const b = box(init); const r = rhs("R");
    if (form === "??=") b.o.x ??= r.v();
    else if (form === "||=") b.o.x ||= r.v();
    else b.o.x &&= r.v();
    console.log(label.padEnd(10) + ("b.x " + form + " R").padEnd(12) + tag(b.read()).padEnd(10) +
      String(r.calls()).padEnd(11) + JSON.stringify(b.log));
  }
}

console.log("");
console.log("[3] on a frozen object: ||= only fails when it actually tries to write (sloppy mode)");
console.log("case".padEnd(34) + "result");
const shot = (label, obj, key, fn) => {
  try { fn(); console.log(label.padEnd(34) + "no throw, value=" + tag(obj[key])); }
  catch (e) { console.log(label.padEnd(34) + e.constructor.name + " " + e.message); }
};
const fz1 = Object.freeze({ keep: "kept" });
shot("frozen.keep ||= 'R'   (truthy)", fz1, "keep", () => { fz1.keep ||= "R"; });
const fz2 = Object.freeze({ keep: "" });
shot("frozen.keep ||= 'R'   (falsy)", fz2, "keep", () => { fz2.keep ||= "R"; });
const fz3 = Object.freeze({ keep: null });
shot("frozen.keep ??= 'R'   (null)", fz3, "keep", () => { fz3.keep ??= "R"; });
const fz4 = Object.freeze({ keep: "" });
shot("frozen.keep = keep || 'R'", fz4, "keep", () => { fz4.keep = fz4.keep || "R"; });
```

```text
===== node20 js12b-12c-assign.js (exit=0) =====
[1] b.x ||= R   vs   b.x = b.x || R      (same value, different writes)
start     form                  final     rhs calls  setter log
'keep'    b.x ||= R             'keep'    0          ["get"]
'keep'    b.x = b.x || R        'keep'    0          ["get","set:keep"]
0         b.x ||= R             'R'       1          ["get","set:R"]
0         b.x = b.x || R        'R'       1          ["get","set:R"]
''        b.x ||= R             'R'       1          ["get","set:R"]
''        b.x = b.x || R        'R'       1          ["get","set:R"]
null      b.x ||= R             'R'       1          ["get","set:R"]
null      b.x = b.x || R        'R'       1          ["get","set:R"]

[2] ??=  vs  ||=  vs  &&=      (setter log is the answer)
start     form        final     rhs calls  setter log
0         b.x ??= R   0         0          ["get"]
0         b.x ||= R   'R'       1          ["get","set:R"]
0         b.x &&= R   0         0          ["get"]
''        b.x ??= R   ''        0          ["get"]
''        b.x ||= R   'R'       1          ["get","set:R"]
''        b.x &&= R   ''        0          ["get"]
null      b.x ??= R   'R'       1          ["get","set:R"]
null      b.x ||= R   'R'       1          ["get","set:R"]
null      b.x &&= R   null      0          ["get"]
undefined b.x ??= R   'R'       1          ["get","set:R"]
undefined b.x ||= R   'R'       1          ["get","set:R"]
undefined b.x &&= R   undefined 0          ["get"]
'v'       b.x ??= R   'v'       0          ["get"]
'v'       b.x ||= R   'v'       0          ["get"]
'v'       b.x &&= R   'R'       1          ["get","set:R"]

[3] on a frozen object: ||= only fails when it actually tries to write (sloppy mode)
case                              result
frozen.keep ||= 'R'   (truthy)    no throw, value='kept'
frozen.keep ||= 'R'   (falsy)     no throw, value=''
frozen.keep ??= 'R'   (null)      no throw, value=null
frozen.keep = keep || 'R'         no throw, value=''
```

**그림 해설.**

- ★★★ **첫 두 줄이 이 주제의 급소다.** 시작값이 `'keep'`(truthy)일 때
  `b.x ||= R` 의 로그는 `["get"]` 이고 `b.x = b.x || R` 의 로그는 `["get","set:keep"]` 이다.
  **끝난 값은 둘 다 `'keep'` 으로 똑같다.** 갈리는 것은 **setter 가 한 번 불렸다는 사실**뿐이다.
- ★★ `[2]` 의 격자가 세 연산자를 한눈에 가른다 — `??=` 는 **nullish 두 값에서만** 쓰고,
  `||=` 는 **falsy 전부**에서 쓰고, `&&=` 는 **truthy 일 때만** 쓴다.
- ★ `[3]` 동결된 객체에서 `||=` 는 **값이 truthy 면 아예 시도조차 안 한다.**
  그래서 「동결했는데 `||=` 가 안 터지더라」는 **동결이 느슨해서가 아니라 쓰기를 시도하지 않아서**다.
  값을 falsy 로 바꾸면 그때 비로소 시도하고, 비엄격이라 **조용히 실패**한다.

> **setter** — 프로퍼티에 값을 대입할 때 대신 불리는 함수.\
> 예: `set x(v) { ... }` 를 달아 두면 `o.x = 1` 이 그 함수를 부른다. 그래서 「대입했나」를 로그로 셀 수 있다.

### (4) ★★ 엄격 / 비엄격 — 설정에 달린 칸을 스크립트가 센다

**언제 쓰나** — 같은 줄이 모듈에서는 터지고 스크립트에서는 조용할 때.

> ★★★ **바로 앞 배치가 여기서 사고를 냈다.** 비엄격 탐침을 먼저 돌리면 **암시적 전역**이 만들어지고,
> 뒤에 도는 엄격 탐침이 그것을 읽어 **두 모드가 「같다」는 거짓 결과**가 나온다.
> 값도 정상이고 에러도 없어 **모든 검사기를 통과한다.**
> 처방은 둘이다 — **엄격을 먼저 돌린다** · **탐침마다 전역 이름을 다르게 준다.**
> 아래 블록은 그 둘을 다 쓰고, **무엇이 실제로 샜는지**를 마지막에 찍는다.

```js
// js12b-12s-strict.js
// 엄격 / 비엄격 전수 격자.
// ★ 바로 앞 배치의 사고를 막는 처방 둘을 그대로 쓴다 --
//   (1) 엄격을 먼저 돌린다  (2) 탐침마다 전역 이름을 다르게 준다.
// 두 탐침이 같은 전역을 쓰면 비엄격이 만든 암시적 전역을 엄격이 읽어 「같다」는 거짓 결과가 난다.
// 이름이 다르면 메시지에 그 이름이 박히므로, 비교 전에 이름을 <G> 로 되돌려 놓는다.
const probes = [
  ["plain  G = 1", "G = 1; return String(G);"],
  ["plain  var q; q = 1", "var q; q = 1; return String(q);"],
  ["logical  G ??= 1", "G ??= 1; return String(G);"],
  ["logical  G ||= 1", "G ||= 1; return String(G);"],
  ["frozen.p ||= 'R'   p=''", "const o = Object.freeze({ p: '' }); o.p ||= 'R'; return JSON.stringify(o.p);"],
  ["frozen.p ??= 'R'   p=null", "const o = Object.freeze({ p: null }); o.p ??= 'R'; return JSON.stringify(o.p);"],
  ["getter-only ??= 'R'", "const o = { get p() { return null; } }; o.p ??= 'R'; return JSON.stringify(o.p);"],
  ["getter-only ||= 'R'", "const o = { get p() { return 0; } }; o.p ||= 'R'; return JSON.stringify(o.p);"],
  ["delete o?.p   configurable", "const o = { p: 1 }; const r = delete o?.p; return r + ' keys=' + JSON.stringify(Object.keys(o));"],
  ["delete o?.p   non-config", "const o = Object.defineProperty({}, 'p', { value: 1 }); const r = delete o?.p; return r + ' keys=' + JSON.stringify(Object.getOwnPropertyNames(o));"],
  ["delete nul?.p  nul=null", "const nul = null; return String(delete nul?.p);"],
];

function run(mode, body, gname) {
  const src = (mode === "strict" ? '"use strict";\n' : "") + body.replace(/\bG\b/g, gname);
  let out;
  try { out = "OK " + new Function(src)(); }
  catch (e) { out = e.constructor.name + " " + e.message; }
  return out.split(gname).join("<G>");
}

// ★ 엄격을 먼저 -- 비엄격이 전역을 만들기 전에 찍는다.
const strictOut = probes.map(([, body], i) => run("strict", body, "js12bStrictG" + i));
const sloppyOut = probes.map(([, body], i) => run("sloppy", body, "js12bSloppyG" + i));

console.log("[1] strict-first grid   (each probe owns a unique global name, printed back as <G>)");
let split = 0;
probes.forEach(([label], i) => {
  const same = strictOut[i] === sloppyOut[i];
  if (!same) split += 1;
  console.log(label.padEnd(30) + (same ? "SAME  " : "SPLIT ") + "strict: " + strictOut[i]);
  console.log("".padEnd(30) + "      " + "sloppy: " + sloppyOut[i]);
});
console.log("");
console.log("mode-dependent cells " + split + " / " + probes.length);

console.log("");
console.log("[2] what the sloppy probes left behind on globalThis");
const leaked = Object.getOwnPropertyNames(globalThis).filter((k) => k.startsWith("js12b")).sort();
console.log("globals starting with js12b -> " + JSON.stringify(leaked));
console.log("any js12bStrictG* leaked?   -> " + leaked.some((k) => k.startsWith("js12bStrictG")));
console.log("if strict had run SECOND it would have read the sloppy leftover and reported SAME.");
```

```text
===== node20 js12b-12s-strict.js (exit=0) =====
[1] strict-first grid   (each probe owns a unique global name, printed back as <G>)
plain  G = 1                  SPLIT strict: ReferenceError <G> is not defined
                                    sloppy: OK 1
plain  var q; q = 1           SAME  strict: OK 1
                                    sloppy: OK 1
logical  G ??= 1              SAME  strict: ReferenceError <G> is not defined
                                    sloppy: ReferenceError <G> is not defined
logical  G ||= 1              SAME  strict: ReferenceError <G> is not defined
                                    sloppy: ReferenceError <G> is not defined
frozen.p ||= 'R'   p=''       SPLIT strict: TypeError Cannot assign to read only property 'p' of object '#<Object>'
                                    sloppy: OK ""
frozen.p ??= 'R'   p=null     SPLIT strict: TypeError Cannot assign to read only property 'p' of object '#<Object>'
                                    sloppy: OK null
getter-only ??= 'R'           SPLIT strict: TypeError Cannot set property p of #<Object> which has only a getter
                                    sloppy: OK null
getter-only ||= 'R'           SPLIT strict: TypeError Cannot set property p of #<Object> which has only a getter
                                    sloppy: OK 0
delete o?.p   configurable    SAME  strict: OK true keys=[]
                                    sloppy: OK true keys=[]
delete o?.p   non-config      SPLIT strict: TypeError Cannot delete property 'p' of #<Object>
                                    sloppy: OK false keys=["p"]
delete nul?.p  nul=null       SAME  strict: OK true
                                    sloppy: OK true

mode-dependent cells 6 / 11

[2] what the sloppy probes left behind on globalThis
globals starting with js12b -> ["js12bSloppyG0"]
any js12bStrictG* leaked?   -> false
if strict had run SECOND it would have read the sloppy leftover and reported SAME.
```

**그림 해설.**

- ★★★ **설정에 달린 칸은 11칸 중 6칸**이다. 나머지 5칸은 모드와 무관하다.
- ★★★ **전제가 하나 뒤집혔다** — 「비엄격에서 `G ??= 1` 은 암시적 전역을 만든다」가 **틀렸다.**
  논리 할당은 **먼저 읽기 때문에**(`GetValue`) 선언 안 된 이름에서 **두 모드 모두 `ReferenceError`** 다.
  암시적 전역을 만드는 것은 **평범한 `G = 1`** 뿐이다 — `[2]` 에 그 하나만 남아 있다.
- ★★ **그래서 「엄격을 먼저」가 실제로 필요했다.** `[2]` 가 `js12bSloppyG0` 하나를 찍는다 —
  이름을 공유했다면 그 값을 뒤이어 도는 엄격 탐침이 읽어 **`OK 1` 로 답했을** 자리다.
- ★ `delete o?.p` 는 **옵셔널 체이닝이 붙어도 `delete` 의 규칙 그대로**다 — 설정 불가 프로퍼티에서 엄격은 `TypeError`, 비엄격은 `false`.

```text
   같은 줄, 두 모드 -- 무엇이 갈리고 무엇이 안 갈리나

   쓰기가 막힌 자리                 이름이 없는 자리              문법
   (동결·getter-only·non-config)    (선언 안 된 G)                (?? 와 || 섞기)
        │                                │                          │
   엄격 ├─> TypeError 로 멈춘다      엄격 ├─> ReferenceError     엄격 ├─> SyntaxError
   비엄 ├─> 조용히 지나간다          비엄 ├─> 전역을 만든다       비엄 ├─> SyntaxError
        │                                │                          │
        └ 갈린다                         └ G = 1 만 갈린다          └ 안 갈린다
                                           (G ??= 1 은 양쪽 다 터진다)

   ★ 순서가 중요하다 -- 비엄격을 먼저 돌리면 가운데 칸이 만든 전역을
     엄격 탐침이 읽어 「안 갈렸다」는 거짓 결과가 난다.
```

### (5) ★★ 문법 — 무엇이 애초에 컴파일되지 않나

**언제 쓰나** — 「괄호를 왜 쳐야 하지?」가 나올 때. 이것은 실행 오류가 아니라 **파싱 단계에서 거부되는 것**이다.

```js
// js12b-12x-forms.js
// 문법 격자 -- SyntaxError 는 try/catch 로 못 잡으므로 new Function 으로 「컴파일만」 해 본다.
// ★ 엄격을 먼저 돌린다. 이 격자는 값을 만들지 않으므로 전역을 오염시키지 않는다.
const forms = [
  "a ?? b || c",
  "a || b ?? c",
  "a ?? b && c",
  "a && b ?? c",
  "(a ?? b) || c",
  "a ?? (b || c)",
  "a ?? b ?? c",
  "a || b || c",
  "new a?.b()",
  "new (a?.b)()",
  "a?.b()",
  "a?.()",
  "new a?.()",
  "a?.b`tpl`",
  "a?.b = 1",
  "delete a?.b",
  "a?.b++",
  "a ??= b",
  "a?.b ??= c",
  "({}) ?? 1",
];

function compile(mode, expr) {
  const src = (mode === "strict" ? '"use strict";\n' : "") + "let a, b, c; return (" + expr + ");";
  try { new Function(src); return "OK"; }
  catch (e) { return e.constructor.name + " " + e.message; }
}

// ★ 엄격 먼저.
const strictOut = forms.map((f) => compile("strict", f));
const sloppyOut = forms.map((f) => compile("sloppy", f));

console.log("[1] does it even compile?   (strict run first, then sloppy)");
let split = 0;
forms.forEach((f, i) => {
  const same = strictOut[i] === sloppyOut[i];
  if (!same) split += 1;
  console.log(f.padEnd(18) + (same ? "SAME  " : "SPLIT ") + strictOut[i]);
  if (!same) console.log("".padEnd(18) + "      sloppy: " + sloppyOut[i]);
});
console.log("");
console.log("mode-dependent cells " + split + " / " + forms.length);

console.log("");
console.log("[2] duplicate keys in an object literal -- ES5 strict forbade this, ES6+ does not");
for (const mode of ["strict", "sloppy"]) {
  const src = (mode === "strict" ? '"use strict";\n' : "") + "return JSON.stringify({ a: 1, a: 2, a: 3 });";
  let out;
  try { out = "OK " + new Function(src)(); } catch (e) { out = e.constructor.name + " " + e.message; }
  console.log(mode.padEnd(8) + "{ a: 1, a: 2, a: 3 }  -> " + out);
}
```

```text
===== node20 js12b-12x-forms.js (exit=0) =====
[1] does it even compile?   (strict run first, then sloppy)
a ?? b || c       SAME  SyntaxError Unexpected token '||'
a || b ?? c       SAME  SyntaxError Unexpected token '??'
a ?? b && c       SAME  SyntaxError Unexpected token '&&'
a && b ?? c       SAME  SyntaxError Unexpected token '??'
(a ?? b) || c     SAME  OK
a ?? (b || c)     SAME  OK
a ?? b ?? c       SAME  OK
a || b || c       SAME  OK
new a?.b()        SAME  SyntaxError Invalid optional chain from new expression
new (a?.b)()      SAME  OK
a?.b()            SAME  OK
a?.()             SAME  OK
new a?.()         SAME  SyntaxError Invalid optional chain from new expression
a?.b`tpl`         SAME  SyntaxError Invalid tagged template on optional chain
a?.b = 1          SAME  SyntaxError Invalid left-hand side in assignment
delete a?.b       SAME  OK
a?.b++            SAME  SyntaxError Invalid left-hand side expression in postfix operation
a ??= b           SAME  OK
a?.b ??= c        SAME  SyntaxError Invalid left-hand side in assignment
({}) ?? 1         SAME  OK

mode-dependent cells 0 / 20

[2] duplicate keys in an object literal -- ES5 strict forbade this, ES6+ does not
strict  { a: 1, a: 2, a: 3 }  -> OK {"a":3}
sloppy  { a: 1, a: 2, a: 3 }  -> OK {"a":3}
```

★★ **설정에 달린 칸이 20칸 중 0개다** — 문법은 모드를 안 탄다.
★ 중복 키가 **엄격에서도 통과**하는 것이 `[2]` 다. ES5 엄격 모드는 이것을 `SyntaxError` 로 막았는데 **ES6 이후 그 금지가 사라졌다** — 13번 주제에서 다시 본다.

### (6) ★★ 값으로 못 가르는 것은 진단의 열로 가른다 (18-C)

**언제 쓰나** — 「`??` 와 `||` 를 섞으면 왜 안 되나」를 **어디서** 거부당하는지까지 보고 싶을 때.

```js
// js12b-12y-caret.js
// 18-C -- 값으로 못 가르는 문법 성질은 진단이 가리키는 열로 증명한다.
// new Function 은 파일명을 못 주므로 vm.Script 에 filename 을 고정해 캐럿까지 결정적으로 받는다.
// (node --check 는 절대 경로를 박아 재현이 안 된다 -- 그래서 안 쓴다.)
const vm = require("vm");
for (const src of [
  "a ?? b || c",
  "a || b ?? c",
  "a ?? b && c",
  "a && b ?? c",
  "(a ?? b) || c",
  "a ?? (b || c)",
  "a ?? b ?? c",
  "new a?.b()",
  "a?.b`t`",
  "a?.b ??= c",
]) {
  try {
    new vm.Script(src, { filename: "ex.js" });
    console.log("=== " + src);
    console.log("compiles.");
  } catch (e) {
    console.log("=== " + src);
    console.log(e.stack.split("\n").slice(0, 3).join("\n"));
    console.log(e.constructor.name + " " + e.message);
  }
  console.log("");
}
```

```text
===== node20 js12b-12y-caret.js (exit=0) =====
=== a ?? b || c
ex.js:1
a ?? b || c
       ^^
SyntaxError Unexpected token '||'

=== a || b ?? c
ex.js:1
a || b ?? c
       ^^
SyntaxError Unexpected token '??'

=== a ?? b && c
ex.js:1
a ?? b && c
       ^^
SyntaxError Unexpected token '&&'

=== a && b ?? c
ex.js:1
a && b ?? c
       ^^
SyntaxError Unexpected token '??'

=== (a ?? b) || c
compiles.

=== a ?? (b || c)
compiles.

=== a ?? b ?? c
compiles.

=== new a?.b()
ex.js:1
new a?.b()
     ^^
SyntaxError Invalid optional chain from new expression

=== a?.b`t`
ex.js:1
a?.b`t`
    ^^^
SyntaxError Invalid tagged template on optional chain

=== a?.b ??= c
ex.js:1
a?.b ??= c
^^^^
SyntaxError Invalid left-hand side in assignment
```

**그림 해설.**

- ★★★ **네 조합이 전부 같은 열(8열)에서 거부된다.** `a ?? b` 까지는 읽히고 **세 번째 연산자를 만나는 순간** 파서가 멈춘다.
  「`??` 가 `||` 보다 우선순위가 낮다/높다」가 아니라 **둘의 우선순위를 아예 정의하지 않았다**는 뜻이다.
- ★★ `new a?.b()` 는 **`?.` 자리(6열)** 를 가리키고, ``a?.b`t` `` 는 **템플릿 자리(5\~7열)** 를 가리킨다.
  **어디를 가리키느냐가 무엇이 금지되었는지를 말한다.**
- ★ `a?.b ??= c` 는 캐럿이 **식 전체(1\~4열)** 를 덮는다 — 옵셔널 체인은 **대입의 왼쪽이 될 수 없다.**

### (7) ★ 같은 질문을 브라우저에 던지면

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

★★ **호스트가 정하는 칸이 하나도 없었다.** 네 주제의 대표 줄이 전부 Node 쪽과 같다.
★ **예외 문구까지 같은 것**은 **둘 다 V8 이기 때문**이지 명세가 정한 것이 아니다.

## 문법 — 형태와 규칙

```text
   옵셔널 체이닝 세 꼴
   o?.b            프로퍼티
   o?.[expr]       계산된 키 -- expr 은 끊기면 평가되지 않는다
   o?.(arg)        호출      -- arg 도 끊기면 평가되지 않는다

   널 병합
   a ?? b          a 가 null/undefined 일 때만 b

   논리 할당 셋
   a ??= b         a 가 null/undefined 일 때만 대입
   a ||= b         a 가 falsy 일 때만 대입
   a &&= b         a 가 truthy 일 때만 대입
```

- **`?.` 는 사슬 단위로 끊는다.** `a?.b.c.d` 에서 `a` 가 nullish 면 `.b`·`.c`·`.d` 가 **전부** 건너뛰어진다.
- **괄호가 사슬을 닫는다.** `(a?.b).c` 는 새 식이라 다시 터질 수 있다.
- **`??` 는 `||`·`&&` 와 괄호 없이 못 섞는다.** 파서가 거부한다.
- **`?.` 뒤에 `new` 는 못 온다**(`new a?.b()` 는 `SyntaxError`). `new (a?.b)()` 는 된다.
- **`?.` 다음에 태그 템플릿도 못 온다**(``a?.b`t` ``).
- **옵셔널 체인은 대입의 왼쪽이 될 수 없다**(`a?.b = 1`·`a?.b ??= c`·`a?.b++` 전부 `SyntaxError`).
- **`delete a?.b` 는 된다** — 이것 하나가 예외다.
- **논리 할당의 오른쪽은 조건이 맞을 때만 평가된다** — 그리고 **대입 자체도 그때만 일어난다.**

## 어디서 틀리나

### (1) ★★★ `||` 를 기본값에 써서 `0` 과 `''` 를 삼킨다

`count || 10` 은 `count` 가 `0` 일 때 **10** 이 된다. 사용자가 명시적으로 넣은 `0` 이 사라진다.
★ 격자의 **6칸이 전부 이 사고**다. 고치는 법은 `count ?? 10`.

### (2) ★★★ 「`?.` 를 붙였으니 안전하다」로 읽는다

`?.` 는 **`null`/`undefined` 만** 막는다. `0`·`''`·`false` 는 그대로 통과해 **그 다음 줄에서** 터진다.
★ 그리고 **왼쪽만** 막는다 — `a?.b.c` 에서 `a.b` 가 `null` 이면 `a?.b.c` 는 여전히 터진다(그 자리에는 `a?.b?.c` 가 필요하다).

### (3) ★★★ `||=` 를 `= x || y` 로 바꿔 적는다(또는 그 반대)

값은 같고 **쓰기 횟수가 다르다.** setter·Proxy·동결 객체·리액티브 프레임워크가 걸린 자리에서
**의도하지 않은 쓰기 한 번**이 화면을 다시 그리거나 `TypeError` 를 낸다.
★ 실측의 `["get"]` 과 `["get","set:keep"]` 이 그 차이다.

### (4) ★★ `??` 를 `||` 와 섞어 쓰고 런타임 오류를 찾는다

이것은 **런타임 오류가 아니다.** 파일 전체가 컴파일되지 않아 **그 줄과 무관한 곳에서** 실패한다.

### (5) ★★ `(a?.b).c` 로 괄호를 치고 안전하다고 믿는다

괄호가 **사슬을 닫아 버려** 보호가 사라진다. 실측에서 이 줄만 `TypeError` 였다.

### (6) ★★ 동결된 객체에 `||=` 를 쓰고 「안 터지네」로 결론 낸다

값이 truthy 면 **시도조차 안 하므로** 조용하다. falsy 로 바뀌는 날 비엄격이면 **조용히 실패**하고 엄격이면 `TypeError` 다.

### (7) ★ `delete a?.b` 의 `true` 를 「지웠다」로 읽는다

`a` 가 nullish 면 **아무것도 안 지우고 `true`** 다. `delete` 의 반환값은 원래 「삭제에 성공했나」가 아니라 「거부되지 않았나」다.

### (8) ★ `a ??= b` 로 선언 안 된 변수를 초기화하려 한다

**두 모드 모두 `ReferenceError`** 다. 논리 할당은 먼저 읽기 때문이다.

## 구현 세부사항 대 언어 보장

### 명세 보장 — 어느 엔진에서도 같아야 하는 것

- **`?.` 가 사슬 전체를 끊는 것** · **대괄호 안 식과 인자가 평가되지 않는 것.**
- **`??` 가 보는 것이 `null`/`undefined` 둘뿐인 것**(`ToBoolean` 을 안 쓴다).
- **`??` 를 `||`/`&&` 와 괄호 없이 못 섞는 것** · **`new` 와 태그 템플릿이 옵셔널 체인 뒤에 못 오는 것.**
- **논리 할당이 조건이 맞을 때만 대입하는 것**(그래서 setter 가 안 불린다).
- **`delete a?.b` 가 허용되는 것** · **엄격 모드에서 실패한 쓰기가 `TypeError` 인 것.**

### 엔진(V8) 구현 · 이 판의 관찰

- **예외 문구 전부** — `Cannot read properties of undefined (reading 'c')` · `Unexpected token '||'` ·
  `Invalid optional chain from new expression` 은 **V8 의 문구**다. 종류(`TypeError`·`SyntaxError`)만 명세가 정한다.
- **캐럿이 가리키는 열** — 이 판에서 안정적이었지만 **파서의 사정**이다.
- **두 판(18·20)과 Chrome 151 이 이 주제에서 한 글자도 안 갈렸다** — 셋 다 V8 이기 때문이지 보장이 아니다.

### 호스트가 정하는 것 — ECMA-262 밖

- **없다.** 이 주제의 브라우저 대조에서 호스트가 정하는 칸이 0개였다.

### 그래서 이렇게 적으면 틀린다

- 「`??` 는 falsy 를 걸러 준다」 — **아니다.** falsy 를 걸러 주는 것은 `||` 다.
- 「`??=` 는 비엄격에서 전역을 만든다」 — **아니다.** 두 모드 모두 `ReferenceError` 다(실측으로 뒤집혔다).
- 「`?.` 는 한 칸만 막는다」 — **아니다.** 괄호로 닫기 전까지 사슬 전체다.

## 언제 쓰고 언제 안 쓰나

- **`??`** — 기본값을 줄 때의 **기본 선택**이다. `0`·`''`·`false` 가 정상 값인 도메인(포트·수량·플래그)에서 특히.
- **`||`** — 「빈 문자열도 없는 것으로 친다」가 **의도일 때만.** 그 의도를 주석이나 이름으로 남긴다.
- **`?.`** — **모양을 모르는 데이터**(외부 응답·선택적 설정)에 쓴다.
  내 코드가 만든 객체에 `?.` 를 줄줄이 다는 것은 **계약이 없다는 신호**이지 안전장치가 아니다.
- **`??=`** — 지연 초기화(`cache ??= compute()`)에 맞는다. `||=` 는 **캐시 값이 `0`·`''` 일 수 있으면 쓰지 않는다.**
- **안 쓸 자리** — 값이 `null` 인지 `undefined` 인지를 **구별해야 하는** 곳. `??` 는 둘을 같은 것으로 뭉갠다.

## 핵심 문장

1. **이 세 문법이 하는 일은 「안 하는 것」이고, 안 한 일은 값에 흔적을 안 남긴다** — 그래서 근거가 호출 횟수다.
2. **`||` 는 falsy 를, `??` 는 nullish 를 본다** — falsy 13종 중 6종이 그 차이다.
3. **`?.` 는 사슬 전체를 끊고, 괄호가 사슬을 닫는다.**
4. **`||=` 와 `= x || y` 는 값이 같고 쓰기 횟수가 다르다.**
5. **`??` 를 `||`/`&&` 와 섞는 것은 런타임이 아니라 파서가 막는다.**

## 관련 자료

- [02 — 강제 변환과 `==` 대 `===`](../02-coercion-and-loose-equality/2-summary.md) — **그쪽이 `ToBoolean`·falsy 목록의 정본**이다. 여기는 **그 목록이 기본값 문법에서 만드는 사고**부터.
- [10 — 구조 분해 할당](../10-destructuring-assignment/2-summary.md) — **그쪽이 `undefined` 에만 걸리는 기본값의 정본**이다. 여기는 **`null` 까지 막는 `??` 와의 대비**만.
- [14 — 프로퍼티 디스크립터와 동결](../14-property-descriptors-and-freezing/2-summary.md) — **그쪽이 「왜 쓰기가 막히나」의 정본**이다. 여기는 **막혔을 때 무엇이 보이나**까지.
- 목록의 **35번 주제** 「엄격 모드」 — **그쪽이 모드가 바꾸는 규칙 전부의 정본**이다. 여기는 **이 세 문법이 걸리는 칸**까지.
- 목록의 **33번 주제** 「동등성 세 종류」 — **그쪽이 `Object.is`·SameValueZero 의 정본**이다.
- Python 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **05번** — 파이썬의 `or`/`and` 는 **값을 돌려주는 단축 평가**라는 점이 같고, **nullish 전용 연산자가 없다**는 점이 다르다.

## 용어 풀이

- **옵셔널 체이닝(optional chaining)** — `?.` 로 시작해 다음 괄호·점을 묶은 하나의 사슬. 왼쪽이 nullish 면 사슬 전체를 건너뛴다.
- **널 병합(nullish coalescing)** — `??`. 왼쪽이 `null` 또는 `undefined` 일 때만 오른쪽을 쓴다.
- **nullish** — `null` 과 `undefined` 둘만 가리키는 말. falsy 와 다르다.
- **falsy** — `ToBoolean` 이 `false` 로 바꾸는 값. `false`·`0`·`-0`·`0n`·`''`·`null`·`undefined`·`NaN` 여덟이다.
- **단축 평가(short-circuit evaluation)** — 답이 정해지면 나머지를 계산하지 않는 것.
- **논리 할당(logical assignment)** — `??=`·`||=`·`&&=`. 조건이 맞을 때만 **대입까지** 한다.
- **암시적 전역(implicit global)** — 비엄격 모드에서 선언 없이 대입하면 생기는 전역 프로퍼티.
- **getter / setter** — 프로퍼티를 읽거나 쓸 때 대신 불리는 함수. 호출 로그를 심는 자리가 여기다.
- **엄격 모드(strict mode)** — `"use strict"` 나 모듈에서 켜지는 모드. 조용히 실패하던 것들이 `TypeError` 가 된다.

## 더 들어가면

- **`?.` 는 「짧은 사슬(short-circuiting)」을 값이 아니라 구문 구조로 구현한다.** 그래서 `(a?.b).c` 가 갈린다 —
  괄호가 **구문 단위**를 끝내기 때문이지 값이 달라서가 아니다.
- **논리 할당의 「조건이 맞을 때만 대입」은 프록시를 쓰는 프레임워크에서 의미가 크다.**
  Vue·MobX 처럼 setter 로 변경을 추적하는 코드에서 `||=` 와 `= x || y` 는 **재렌더 횟수가 다르다.**
  ★ 다만 **그 비용은 재지 않았다** — 여기서 말할 수 있는 것은 **쓰기 횟수가 다르다**는 사실까지다.
- **`??` 에 우선순위를 안 준 것은 의도된 설계다.** `a ?? b || c` 가 어떻게 묶여야 자연스러운지에 합의가 없어
  **아예 문법으로 막았다.** 그 결정의 흔적이 `[6]` 의 캐럿 위치에 남아 있다.
