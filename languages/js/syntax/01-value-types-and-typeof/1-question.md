# js/syntax/01 — 값의 종류와 `typeof`: 「이 값은 무엇인가」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v18.19.1(기본 PATH) · v20.19.6(nvm) · Google Chrome 151.0.7922.173 · x86-64 Linux.
> 배너의 `node20` 은 v20.19.6, `node18` 은 v18.19.1 이다.
>
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① **값의 종류와 `typeof` 의 답이 어디서 어긋나나** ② **`"object"` 를 더 갈라 보는 둘째 창**
> ③ **원시 값에 점을 찍으면 무엇이 생겼다 사라지나**.
> ★★★ **「버그처럼 보이는데 명세가 보장하는 것」과 「구현 사정」을 가르는 것**이 이 갈래의 축이다 — 8번이 그 문항이다.
> ★★ **예외는 타입과 메시지로만 답한다** — 이 문서의 블록에는 스택트레이스가 한 줄도 없다(절대 경로가 박히기 때문이다).
> ★ **4번은 Node 로는 못 푼다.** 브라우저로 던져야 나오는 답이다.
>
> **선행** — 없다. 이 갈래의 첫 주제다.

## 이 파일을 푸는 법

- ★★ **예측형 다섯 문항(1·2·3·4·5)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **1번은 「스물두 줄 중 몇 줄이 어긋나나」를 세는 것이 답의 절반**이다.
- ★★ **3번은 「엄격 모드에서 달라지는 줄이 어느 것인가」까지 적어야** 답이다.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이것은 명세인가 이 엔진의 사정인가**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 스물두 줄을 두 창에 던지면 (예측) ★★★ 이 주제의 축

```js
// js01b-01a-typeof-grid.js
// 원시 7종과 객체를 한 줄씩 typeof 에 던진다.
// ★ 둘째 칸은 Object.prototype.toString.call — typeof 가 "object" 로 뭉갠 것을 갈라 준다.
const tag = (v) => Object.prototype.toString.call(v);

const rows = [
  ["undefined",            undefined],
  ["null",                 null],
  ["true",                 true],
  ["42",                   42],
  ["NaN",                  NaN],
  ["Infinity",             Infinity],
  ["10n",                  10n],
  ['"abc"',                "abc"],
  ["Symbol('s')",          Symbol("s")],
  ["{}",                   {}],
  ["[]",                   []],
  ["function f(){}",       function f() {}],
  ["() => {}",             () => {}],
  ["class C {}",           class C {}],
  ["/re/",                 /re/],
  ["new Date(0)",          new Date(0)],
  ["new Number(42)",       new Number(42)],
  ["new String('abc')",    new String("abc")],
  ["Math",                 Math],
  ["JSON",                 JSON],
  ["new Map()",            new Map()],
  ["Object.create(null)",  Object.create(null)],
];

console.log("expr".padEnd(22) + "typeof".padEnd(12) + "Object.prototype.toString.call");
console.log("-".repeat(22) + "-".repeat(12) + "-".repeat(30));
for (const [label, v] of rows) {
  console.log(label.padEnd(22) + String(typeof v).padEnd(12) + tag(v));
}

console.log("");
console.log("typeof 가 돌려줄 수 있는 문자열은 이 여덟 가지뿐이다:");
console.log("  " + [...new Set(rows.map(([, v]) => typeof v))].sort().join(" "));
```

- 스물두 줄의 **`typeof` 칸**을 각각 적으면?
- ★★★ 그중 **둘째 창(`Object.prototype.toString.call`)과 답이 어긋나는 줄**은 몇 줄이고 어느 것인가?
- ★★★ `typeof` 가 돌려준 **서로 다른 문자열이 몇 가지**인가? 그것으로 무엇을 말할 수 있나?
- ★★ `class C {}` 와 `() => {}` 는 어느 칸으로 가는가? **왜인가**?
- ★★ `Object.create(null)` 의 둘째 칸은 `{}` 와 같은가 다른가?
- ★ `Math` 와 `JSON` 의 둘째 칸은 무엇인가? 그것이 **왜 특별한가**?

### 2. 이름이 없을 때와 아직 없을 때 (예측) ★★★

```js
// js01b-01b-typeof-undeclared.js
// typeof 가 ReferenceError 를 피해 가는 유일한 자리 — 그리고 그 예외의 예외.
function show(label, f) {
  let r;
  try { r = JSON.stringify(f()); }
  catch (e) { r = e.constructor.name + ": " + e.message; }
  console.log(label.padEnd(32) + " -> " + r);
}

console.log("[1] 선언조차 안 된 이름");
show("typeof neverDeclared", () => typeof neverDeclared);
show("neverDeclared", () => neverDeclared);

console.log("");
console.log("[2] let/const 의 TDZ 는 typeof 도 못 넘는다");
function tdzProbe() { const r = typeof tdzLet; let tdzLet = 1; return r; }
show("typeof tdzLet (TDZ)", tdzProbe);
function okProbe() { let x = 1; return typeof x; }
show("typeof x (initialized let)", okProbe);

console.log("");
console.log("[3] globalThis 에 묻는 것과 typeof 는 다른 질문이다");
show("'nope' in globalThis", () => "nope" in globalThis);
show("typeof nope", () => typeof nope);
show("globalThis.nope", () => globalThis.nope);
```

- 세 묶음의 출력을 각각 적으면?
- ★★★ `typeof neverDeclared` 와 `neverDeclared` 가 **왜 다른 결과**를 내는가?
- ★★★ `typeof tdzLet` 은 **왜 안 터지지 않는가**? 이것이 1번 문단의 규칙에 무엇을 뚫는가?
- ★★ `"nope" in globalThis` 와 `typeof nope` 가 **다른 질문**인 이유는?
- ★ `globalThis.nope` 는 왜 예외가 아닌가?
- ★★ 「`typeof` 는 절대 안 터진다」를 **정확히 고쳐 적으면**?

### 3. 원시 값에 점을 찍으면 (예측) ★★★

```js
// js01b-01c-boxing.js
// 원시 값에 메서드를 부르면 무슨 일이 나는가 — 래퍼를 실제로 붙잡아 본다.
String.prototype.peek = function () {
  return { typeofThis: typeof this, isStringObject: this instanceof String,
           tag: Object.prototype.toString.call(this) };
};
Number.prototype.peekStrict = function () {
  "use strict";
  return { typeofThis: typeof this, isNumberObject: this instanceof Number };
};

const s = "abc";
console.log("[1] 원시 문자열에 메서드를 부르면 this 가 무엇인가");
console.log("  느슨한 모드 :", JSON.stringify(s.peek()));
console.log("  엄격 모드   :", JSON.stringify((42).peekStrict()));

console.log("");
console.log("[2] 래퍼는 그 호출 한 번만 살고 버려진다");
s.mine = 1;
console.log("  s.mine = 1 을 한 뒤 s.mine :", s.mine);
const boxed = new String("abc");
boxed.mine = 1;
console.log("  new String('abc') 는 남는다:", boxed.mine);

console.log("");
console.log("[3] 래퍼 객체는 원시 값과 다른 물건이다");
console.log("  'abc' === new String('abc')      :", "abc" === new String("abc"));
console.log("  'abc' ==  new String('abc')      :", "abc" == new String("abc"));
console.log("  typeof new String('abc')         :", typeof new String("abc"));
console.log("  Boolean(new Boolean(false))      :", Boolean(new Boolean(false)));
console.log("  new Boolean(false) ? 'T' : 'F'   :", new Boolean(false) ? "T" : "F");
console.log("  JSON.stringify(new Number(1))    :", JSON.stringify(new Number(1)));

console.log("");
console.log("[4] 래퍼가 없는 원시 값도 있다 — 부르면 바로 터진다");
for (const [label, f] of [
  ["(null).toString()", () => null.toString()],
  ["(undefined).toString()", () => undefined.toString()],
  ["(10n).toString()", () => (10n).toString()],
  ["Symbol('s').toString()", () => Symbol("s").toString()],
]) {
  let r; try { r = f(); } catch (e) { r = e.constructor.name + ": " + e.message; }
  console.log("  " + label.padEnd(26) + " -> " + r);
}
```

- 네 묶음의 출력을 각각 적으면?
- ★★★ `[1]` 의 두 줄이 **왜 다른가**? 무엇이 그 차이를 만드는가?
- ★★★ `[2]` 에서 `s.mine` 이 `undefined` 인데 **예외는 왜 안 나는가**? 어떻게 하면 나게 할 수 있나?
- ★★ `new Boolean(false)` 가 **참**인 이유는? 이것이 왜 위험한가?
- ★★ `[4]` 에서 **터지는 둘과 안 터지는 둘**을 가르는 기준은 무엇인가?
- ★ `JSON.stringify(new Number(1))` 이 `1` 인 것은 무엇을 뜻하나?

### 4. 브라우저에서만 나오는 답 (예측) ★★★

```text
<!doctype html><meta charset="utf-8"><title>document.all</title>
<p>이 페이지는 값을 찍기만 한다.</p>
<pre id="out"></pre>
<script src="js01b-01d-browser.js"></script>
```

```js
// js01b-01d-browser.js
const rows = [
  ["typeof document.all",            typeof document.all],
  ["document.all === undefined",     document.all === undefined],
  ["document.all == undefined",      document.all == undefined],
  ["document.all == null",           document.all == null],
  ["Boolean(document.all)",          Boolean(document.all)],
  ["document.all ? 'T' : 'F'",       document.all ? "T" : "F"],
  ["Object.prototype.toString.call", Object.prototype.toString.call(document.all)],
  ["document.all.length",            document.all.length],
  ["document.all[1].tagName",        document.all[1].tagName],
  ["typeof document.body",           typeof document.body],
];
document.getElementById("out").textContent =
  rows.map(([k, v]) => k.padEnd(32) + " : " + String(v)).join("\n");
```

- 열 줄의 출력을 각각 적으면?
- ★★★ `typeof document.all` 과 `document.all === undefined` 가 **왜 엇갈리는가**?
- ★★★ 이 값이 **객체라는 증거** 두 가지를 대면?
- ★★ `Boolean(document.all)` 이 `false` 인 것은 **falsy 목록에 무엇을 더하는가**?
- ★★ 이것은 **어느 명세**가 정한 것인가? ECMA-262 인가 아닌가?
- ★ 이 예외가 **왜 만들어졌는가**? 없앨 수 있나?
- ★ 이 출력에서 **흔들리는 칸**은 어느 것인가?

### 5. 두 판으로 돌리면 (예측) ★

```sh
// js01b-vdiff.sh
#!/usr/bin/env bash
# 이 주제의 모든 스크립트를 두 판으로 돌려 한 글자라도 다른지 본다.
# 쓰는 법: ./js01b-vdiff.sh <주제번호>
set -u -o pipefail
N18=node                                        # v18.19.1 (기본 PATH)
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"  # v20.19.6 (nvm)
printf '%-34s %s\n' "script" "node v18.19.1 대 v20.19.6"
printf '%-34s %s\n' "----------------------------------" "-------------------------"
for f in js01b-"$1"*.js; do
  case "$f" in *-browser.js|*-forms.js) continue;; esac   # 브라우저용·형태만 모은 것은 뺀다
  a=$("$N18" "$f" 2>&1); b=$("$N20" "$f" 2>&1)
  if [ "$a" = "$b" ]; then printf '%-34s 같다 (한 글자도)\n' "$f"
  else printf '%-34s ★ 다르다 — 다른 줄 %s개\n' "$f" "$(diff <(printf '%s\n' "$a") <(printf '%s\n' "$b") | grep -c '^[<>]')"
  fi
done
```

- 세 스크립트에서 **갈린 것이 있는가**?
- ★★ 「세 판에서 같았다」가 **보장인가**? 그러면 무엇으로 보장을 삼아야 하는가?
- ★ 이 배치 네 주제 전체에서 **두 판이 갈린 자리는 몇 개**이고 어디인가?
- ★ 이 스크립트가 **브라우저용 파일을 건너뛰는** 이유는?

### 6. `typeof` 가 `"object"` 라고 답한 다음 (왜) ★★★

- ★★★ `typeof` 하나로는 **왜 모자란가**? 한 문장으로.
- ★★ 둘째 창은 무엇이고 그것이 **무엇을 갈라 주는가**?
- ★★ 둘째 창도 **속일 수 있다** — 어떻게인가? 어느 주제의 일인가?
- ★ `null`·배열·`Date`·`Map`·`Math` 다섯을 **가르려면** 각각 무엇을 쓰나?
- ★★ 세 창(`typeof` · 브랜드 태그 · 실행 출력)으로 **못 푸는 질문**을 하나 대면?

### 7. 세 가지 「없음」 (경계) ★★

- **「선언이 없다」·「`undefined` 다」·**「`null` 이다」 세 상태를 각각 무엇으로 가리는가?
- ★★ `typeof x === "undefined"` 는 그중 **몇 개를 참으로** 만드는가?
- ★★ `x == null` 은 몇 개를 참으로 만드는가? (02번 주제로 넘어간다)
- ★ 세 상태 중 **오타가 만드는 것**은 어느 것인가? 그것이 왜 무서운가?
- ★ `let x;` 와 `let x = undefined;` 는 구분되는가?

### 8. 보장인가 사정인가 (연결) ★★★ 이 갈래의 축

- ★★★ 이 주제에서 **명세 보장** 칸에 들어가는 것 다섯을 대면?
- ★★★ **엔진 구현** 칸과 **이 판의 관찰** 칸에는 각각 무엇이 들어가는가?
- ★★★ `typeof null === "object"` 는 **어느 칸**인가? 그렇게 판정하는 근거는?
- ★★ 예외의 **종류**와 **문구**는 같은 칸인가?
- ★★ 「두 판에서 같았다」는 어느 칸의 근거가 되는가? 어느 칸은 못 되는가?
- ★ 이 주제에서 **가장 얇은 칸**은 어느 것인가?

### 9. 경계 — 어디까지가 이 주제인가 (연결) ★★

- **TDZ** · **엄격 모드** · **타입 검사 관용구** · **`Symbol.toStringTag`** 는 각각 어느 주제가 정본인가?
- ★★★ **TypeScript 갈래와 어떻게 갈리는가**? 한 문장으로.
- ★★ `typeof` 는 **지워지는 쪽**인가 **남는 쪽**인가? 그래서 어느 갈래의 것인가?
- ★ 이 주제가 **끝까지 책임지는 것** 세 가지를 대면?
- ★ 값의 **메모리 표현**(포인터 태깅 같은 것)은 왜 이 주제가 아닌가?

### 10. 이 갈래의 창 (연결) ★★

- ★★★ 이 주제에서 쓴 **창**을 전부 대면?
- ★★ 그중 **브라우저에서만 열리는 창**은 어느 것인가?
- ★★ **예외를 스택트레이스 대신 타입·메시지로 찍은** 이유는?
- ★ 표준 출력과 표준 오류를 **왜 섞지 않았는가**?
- ★★ 이 주제에서 「**안 돌려 본 것**」은 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
