# js/syntax/19 — 이터러블 프로토콜과 `for...of`: 「소비자는 전부 같은 계약을 부르고, 다 못 읽으면 `return()` 으로 닫는다」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> ★★★ **이 주제의 본체는 ① 추상 연산에 로그 심기다.**
> `for...of`·스프레드·`Array.from`·`new Set`·배열 구조 분해·`Promise.all` 은 **결과만 보면 「값을 차례로 꺼냈다」로 똑같다.**
> 그런데 그 안에서 `Symbol.iterator` 를 **몇 번 읽고**, `next()` 를 **몇 번 부르고**, `return()` 을 **부르나 안 부르나**는
> 결과 값에 한 글자도 안 남는다. ★★★ **값으로는 원리상 못 가른다.**
> 그래서 이터러블의 세 자리(`get [Symbol.iterator]` · `next` · `return`)에 **로그를 심고** 소비자 17가지를 차례로 들이댔다.
> **이 문서의 결론은 전부 그 로그에서 나온다.**
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262 최신 초안 — Abstract Operations](https://tc39.es/ecma262/multipage/abstract-operations.html) —
>   `GetIterator` · `GetIteratorFromMethod` · `IteratorNext` · `IteratorComplete` · `IteratorStep` · `IteratorClose`
> - [ECMA-262 최신 초안 — Statements and Declarations](https://tc39.es/ecma262/multipage/ecmascript-language-statements-and-declarations.html) —
>   `ForIn/OfHeadEvaluation` · `ForIn/OfBodyEvaluation`
> - [ECMA-262 최신 초안 — Keyed Collections](https://tc39.es/ecma262/multipage/keyed-collections.html) — `Map`/`Set` 의 `forEach` note(삽입 순서 · 순회 중 추가)
> - [ECMA-262 판별 아카이브](https://262.ecma-international.org/) · [TC39 finished proposals](https://github.com/tc39/proposals/blob/main/finished-proposals.md) — 판 경계를 가릴 때
>
> ★★★ **명세 조항 번호는 인용하지 않는다.** 규칙 진술은 위 문서의 **추상 연산 이름**으로, **값·호출 로그·예외 타입과 메시지는 전부 실행으로** 접지했다.
>
> **실행 검증** — 이 문서의 모든 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮겨 적은 출력이 하나도 없다).
> 배너의 `node20` 은 `~/.nvm/versions/node/v20.19.6/bin/node`, `node18` 은 기본 PATH 의 `node`(v18.19.1)다.
> ★★ **예외는 `try`/`catch` 로 받아 `e.constructor.name` 과 `e.message` 만** 찍었다 — 스택트레이스에는 절대 경로가 박혀 재현이 안 된다.
> ★ **이 주제의 블록에는 주소도 시간도 난수도 없다.** 같은 판에서 다시 돌리면 한 글자도 안 변한다.
> ★ **이 문서는 BMP 밖 글자(이모지 따위)를 한 글자도 싣지 않는다** — 문자열 탐침은 그 글자를 `String.fromCodePoint(0x1F600)` 로 **만들어서** 쓰고, 출력도 16진 코드 포인트로만 찍는다.
>
> **버전** — 이 주제의 거의 전부가 **한 판에 들어왔다.**
>
> | 무엇 | 판 |
> |---|---|
> | `Symbol.iterator` · 이터레이터 프로토콜(`next`/`return`) · `for...of` | **ES2015** |
> | 스프레드 · 배열 구조 분해가 이 프로토콜을 쓰는 것 | **ES2015** (11번·10번 주제) |
> | `Map` · `Set` · 제너레이터 · `Array.from` · 문자열 이터레이터(코드 포인트 단위) | **ES2015** |
> | `Promise.all` 이 이터러블을 받는 것 | **ES2015** |
> | 이터레이터 헬퍼(`Iterator.prototype.map` 등) | **ES2025** — ★ 이 두 판에는 **없다**(동작 (2)의 `[4]`, 두 판 identical) |
>
> **★★★ 이 주제가 쓰는 창 — 그리고 부적용인 창**
>
> | 창 | 이 주제에서 무엇을 보나 |
> |---|---|
> | ★★★ **① 추상 연산에 로그 심기**(본체) | `get @@iterator` · `@@iterator()` · `next#N` · `return()` 을 찍는 이터러블 하나로 **소비자 17가지**를 돌린다. `return()` 이 **언제 불리나**는 오직 이것으로만 보인다 |
> | ★★★ **② 전수 격자** | 그 17가지의 **요약 표**(`next` 횟수 · `return` 횟수) · 이터러블이 아닌 것을 **여섯 자리**에 · 깨진 프로토콜 **다섯 가지** |
> | ★★ **④ 예외의 `constructor.name` + `message`** | 같은 「이터러블이 아니다」가 **자리마다 문구가 다르다** — 네 가지 문구가 나온다 |
> | ★★ **⑤ 두 판 대조기** | ★★★ **이 배치에서 두 판이 갈린 유일한 블록이 이 주제의 것이다** — 호출 스프레드 `id(...plain)` 의 문구. 11번 주제의 `f(...obj)` 와 **같은 자리**다 |
> | ★★ **창을 바꿔 물었다**(제5의 상태) | `done: true` 와 함께 온 값 — **소비자 창은 전부 그것을 버려 닫혀 있다.** 수동 `next()` 로 바꿔 물어야 보인다(동작 (3)의 `[4]`) |
> | ★ **부적용 — ③ 브랜드 태그** | 「이것이 이터러블인가」는 **내부 슬롯(브랜드)이 아니라 프로퍼티 하나의 계약**이다. 유사 배열에 `Symbol.iterator` 하나를 붙이자 이터러블이 된 줄(동작 (4)의 `[2]`)이 그 증거다. 브랜드가 답할 질문이 없다 — **잴 것이 없다** |
> | ★ **부적용 — 진단의 `(행,열)`**(18-C) | 이 주제에는 `SyntaxError` 가 한 줄도 없다. 프로토콜은 전부 런타임 의미다 — **잴 것이 없다** |
> | ★ **쟀다 — 「없다」**: 파이썬식 `__getitem__` 대체 경로 | 파이썬은 `__getitem__` 만 있어도 `for` 가 돈다. JS 에 그 경로가 있나를 **유사 배열로 실제로 물었고** `for...of` 는 `TypeError` 였다(동작 (4)의 `[2]`). ★ 「잴 것이 없다」가 아니라 「**재 봤더니 없다**」다 |
> | ★ **안 쟀다 — 성능** | 「`for...of` 는 인덱스 `for` 보다 느리다」류의 말을 **한 줄도 쓰지 않는다.** 안 쟀다 |
> | ★ **안 돌렸다 — 브라우저 · 두 번 컴파일**(엄격/비엄격) | 이 배치는 Chrome 을 돌리지 않았다. 탐침은 전부 비엄격 스크립트 한 벌이다 |
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 예외 **문구** — ★ **이 주제에서 실제로 판마다 갈렸다** | ★★★ **호출 로그의 개수와 순서** · `return()` 이 불렸나 |
> | `{(intermediate value)}` 같은 V8 의 표현 조각 | ★★★ **예외의 종류**(`TypeError`) |
> | Node 스택트레이스의 절대 경로 — 한 줄도 싣지 않았다 | ★★ `Map`/`Set` 의 **삽입 순서** · 문자열의 **코드 포인트 개수** |
>
> 두 판 대조기가 **갈렸다고 세는 블록은 이 주제의 `js16b-19c-errors.js` 하나**다 — 집계 줄은 동작 (4)의 끝에 있다.
>
> **선행** — [11 — 스프레드와 나머지](../11-spread-and-rest/2-summary.md)(★★★ 직접 선행) · [10 — 구조 분해 할당](../10-destructuring-assignment/2-summary.md) ·
> [04 — 문자열과 UTF-16](../04-strings-and-utf16/2-summary.md) · [13 — 객체 리터럴과 프로퍼티](../13-object-literals-and-properties/2-summary.md).
> ★★★ **11번이 「세 자리의 문」을 이미 갈랐다** — `apply` 는 **유사 배열만**, 스프레드는 **이터러블만**, `Array.from` 은 **둘 다** 연다.
> 그리고 그 트랩 로그 `[...tracedIterable(2)]` 가 `read Symbol.iterator, next 0, next 1, next 2` 였다.
> ★★ **이 주제는 그 격자를 다시 만들지 않는다.** 11번이 「어느 자리가 이 프로토콜을 쓰나」까지였다면,
> 여기는 **프로토콜 자체** — 무엇을 몇 번 부르고, 언제 닫고, 어디서 깨지나 — 부터다.
> **이어지는 곳** — [목록의 **20번 주제**](../20-generators/) 「제너레이터」 · [목록의 **21번 주제**](../21-iterator-helpers/) 「이터레이터 헬퍼」 · [목록의 **22번 주제**](../22-symbol-and-well-known-symbols/) 「`Symbol` 과 잘 알려진 심볼」 ·
> [목록의 **23번 주제**](../23-map-set-and-weak-collections/) 「`Map`·`Set` 과 약한 컬렉션」 · 목록의 **40번 주제** 「비동기 이터레이션」
>
> ★★ **경계 — 11번이 「세 자리의 문」의 정본이다.** 여기서는 그 문 뒤에서 **무엇이 불리나**만 본다.
> ★★ **경계 — 제너레이터 내부 흐름(`yield`·`next(값)`·`yield*`)은 20번이 정본이다.** 여기서는 **제너레이터가 「자기 자신을 돌려주는 이터레이터」라는 사실**까지다.
> ★★ **경계 — `for await...of` 와 `Symbol.asyncIterator` 는 40번이 정본이다.** 여기서 `Promise.all` 은 **동기 이터러블을 받는 소비자 하나**로만 쓴다.
> ★ **경계 — `for...in` 은 [18 — `for...in` 과 열거](../18-for-in-and-enumeration/2-summary.md)가 정본이다.** 여기서는 `null` 앞에서 둘이 **반대로 군다**는 대비만 쓴다.

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

## 한눈에 — 쉽게 말하면

**이터러블은 「번호표 기계」를 달라고 하면 내주는 가게**다. 손님(소비자)은 기계를 받아 **「다음!」** 을 외치고,
기계는 매번 **「여기 있습니다(값)」** 아니면 **「끝났습니다(`done: true`)」** 를 답한다.
손님이 끝까지 안 기다리고 **중간에 떠나면** 기계에 **「그만 갑니다(`return()`)」** 라고 말하고 나간다.

- ★★★ `for...of`·스프레드·`Array.from`·`new Set`·`[a, b] = …`·`Promise.all` — **손님이 누구든 부르는 말은 이 세 마디뿐**이다.
- ★★★ **「끝났습니다」를 직접 들은 손님은 「그만 갑니다」를 말하지 않는다.** 못 듣고 떠나는 손님만 말한다.
- ★★ **기계가 고장 나서 「다음!」에 비명을 지르면**(`next()` 가 던지면) 손님은 **인사도 없이** 나간다.

```text
   소비자                          이터러블 obj
   ------                          ------------
   ① obj[Symbol.iterator] 를 읽는다 ──▶  get @@iterator      (한 번)
   ② 그것을 부른다                ──▶  @@iterator()         (한 번) -> 이터레이터 it
   ③ it.next()                   ──▶  { value: 10, done: false }
      it.next()                  ──▶  { value: 20, done: false }
      ...
      it.next()                  ──▶  { value: undefined, done: true }   <- 여기서 끝. 닫을 일 없음

   ★ 중간에 떠나면 (break · return · throw · 패턴이 먼저 참)
      it.return()                ──▶  "그만 갑니다"                       <- 이것이 IteratorClose
   ★ it.next() 자체가 던지면
      아무것도 안 부르고 예외를 그대로 올린다
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 번호표 기계를 달라고 하는 창구 | `obj[Symbol.iterator]` (메서드) | 로그의 `get @@iterator` · `@@iterator()` |
| 번호표 기계 | 이터레이터 — `next` 를 가진 객체 | `typeof it.next === "function"` |
| 「다음!」 | `it.next()` | 로그의 `next#N` |
| 「여기 있습니다」 / 「끝났습니다」 | `{ value, done: false }` / `{ done: true }` | 결과 객체 |
| 「그만 갑니다」 | `it.return()` — 명세의 `IteratorClose` | 로그의 `return()` |
| 갈 때마다 새 기계를 주는 가게 | 이터러블(배열·`Map`·직접 만든 클래스) | 두 번 돌려도 같은 값 |
| 기계 자체가 창구 노릇도 하는 것 | 자기 자신을 돌려주는 이터레이터(제너레이터 · 배열 이터레이터 · `m.keys()`) | `it[Symbol.iterator]() === it` · 두 번째는 빈 것 |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.
「**함수에 넘긴 제너레이터를 두 번째로 돌렸더니 비어 있었다**」와
「**`const [first] = stream` 한 줄이 스트림을 닫아 버렸다**」가 그것이다.
앞엣것은 **기계가 창구 노릇을 하는 쪽**이고, 뒤엣것은 **다 안 읽고 떠난 손님의 「그만 갑니다」** 다.

> **이터러블(iterable)** — `Symbol.iterator` 메서드를 가져서, 부르면 이터레이터를 내주는 값.\
> 예: 배열 · 문자열 · `Map` · `Set`. 평범한 객체 `{ a: 1 }` 은 **아니다.**

> **이터레이터(iterator)** — `next()` 를 가진 객체. `next()` 가 `{ value, done }` 모양의 결과 객체를 돌려준다.\
> 예: `[1, 2][Symbol.iterator]()` 가 돌려주는 것.

> **`IteratorClose`** — 소비자가 **다 읽기 전에** 멈출 때 이터레이터의 `return` 을 찾아 부르는 명세의 추상 연산.\
> 예: `for (const x of it) break;` 가 `it.return()` 을 부른다.

## 이 주제가 답하려는 질문

1. **소비자마다 `Symbol.iterator`·`next`·`return` 을 언제 몇 번 부르나** — 그리고 **`return()` 은 정확히 언제 불리나?**
2. **이터러블과 이터레이터는 무엇이 다르고**, 왜 어떤 것은 두 번 돌면 두 번째가 비어 있나?
3. **이터러블이 아닌 것을 들이대면** 자리마다 무엇이 터지고, 파이썬의 `__getitem__` 같은 **대체 경로가 JS 에 있나?**

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 출력으로 읽는다.

### (1) ★★★ 소비자 17가지에 로그를 심는다 — 이 주제의 본체

**언제 쓰나** — 「이 API 가 내 이터러블을 **끝까지 읽나, 몇 번 읽나, 닫나**」를 물을 때.
★★★ 값으로는 답이 안 나온다 — `[10,20,30]` 은 누가 읽었든 `[10,20,30]` 이다.

이터러블 `traced()` 는 값 **셋**(10·20·30)을 내놓고, 네 자리에 로그를 남긴다 —
**`Symbol.iterator` 를 읽을 때**(getter) · **그것을 부를 때** · **`next` 마다** · **`return` 이 불릴 때.**

```js
// js16b-19a-protocol-log.js
// ★★★ 이 주제의 본체 -- 소비자마다 Symbol.iterator · next · return 이 「언제 몇 번」 불리나를 로그로 찍는다.
// 이터러블은 값 3개(10, 20, 30)를 내놓는다.
const L = [];
function traced(n = 3, opts = {}) {
  return {
    get [Symbol.iterator]() {
      L.push("get @@iterator");
      return function () {
        L.push("@@iterator()");
        let i = 0;
        return {
          next() {
            i++;
            if (opts.throwAt === i) { L.push("next#" + i + " throws"); throw new Error("next failed"); }
            const done = i > n;
            L.push("next#" + i + (done ? " done" : " -> " + i * 10));
            return done ? { value: undefined, done: true } : { value: i * 10, done: false };
          },
          return() { L.push("return()"); return {}; },
        };
      };
    },
  };
}
const count = (name) => L.filter((m) => m.startsWith(name)).length;
const rows = [];
function probe(label, fn) {
  L.length = 0;
  let r;
  try { r = fn(); r = r === undefined ? "" : "result " + JSON.stringify(r, (k, v) => (v === undefined ? "<undefined>" : v)); } catch (e) { r = "caught " + e.constructor.name + " " + e.message; }
  rows.push([label, count("next#"), count("return()")]);
  console.log(label);
  console.log("    " + L.join(" | ") + (r ? "   [" + r + "]" : ""));
}

console.log("[1] consumers that read to the end");
probe("for (const x of it) {}", () => { for (const x of traced()) {} });
probe("[...it]", () => [...traced()]);
probe("Array.from(it)", () => Array.from(traced()));
probe("new Set(it)", () => [...new Set(traced())]);
probe("const [a, ...rest] = it", () => { const [a, ...rest] = traced(); return [a, rest]; });
probe("Math.max(...it)", () => Math.max(...traced()));

console.log("");
console.log("[2] consumers that stop early");
probe("for-of with break at 20", () => { for (const x of traced()) if (x === 20) break; });
probe("for-of with return at 20", () => (() => { for (const x of traced()) if (x === 20) return x; })());
probe("for-of whose body throws at 20", () => { for (const x of traced()) if (x === 20) throw new Error("body threw"); });
probe("labelled continue outer, from inside", () => { outer: for (const y of [1]) { for (const x of traced()) continue outer; } });
probe("const [a] = it", () => { const [a] = traced(); return a; });
probe("const [a, b, c] = it  (exactly 3)", () => { const [a, b, c] = traced(); return [a, b, c]; });
probe("const [a, b, c, d] = it  (one more)", () => { const [a, b, c, d] = traced(); return [a, b, c, d]; });
probe("Array.from(it, mapFn throws at 20)", () => Array.from(traced(), (x) => { if (x === 20) throw new Error("map threw"); return x; }));
probe("new Map(it)  (10 is not an entry)", () => new Map(traced()));

console.log("");
console.log("[3] when next() itself throws");
probe("for-of, next#2 throws", () => { for (const x of traced(3, { throwAt: 2 })) {} });
probe("[...it], next#2 throws", () => [...traced(3, { throwAt: 2 })]);

console.log("");
console.log("[4] Promise.all -- when does it read the iterable?");
L.length = 0;
const pending = Promise.all(traced());
console.log("Promise.all(it)   right after the call:  " + L.join(" | "));
pending.then((v) => {
  console.log("                  resolved with " + JSON.stringify(v));
  console.log("");
  console.log("[5] summary  (label / next calls / return calls)");
  for (const [label, n, r] of rows) console.log("  " + label.padEnd(40) + String(n).padStart(2) + "  " + r);
  console.log("return() was called in " + rows.filter(([, , r]) => r > 0).length + " of " + rows.length + " probes");
});
```
```text
===== node20 js16b-19a-protocol-log.js (exit=0) =====
[1] consumers that read to the end
for (const x of it) {}
    get @@iterator | @@iterator() | next#1 -> 10 | next#2 -> 20 | next#3 -> 30 | next#4 done
[...it]
    get @@iterator | @@iterator() | next#1 -> 10 | next#2 -> 20 | next#3 -> 30 | next#4 done   [result [10,20,30]]
Array.from(it)
    get @@iterator | @@iterator() | next#1 -> 10 | next#2 -> 20 | next#3 -> 30 | next#4 done   [result [10,20,30]]
new Set(it)
    get @@iterator | @@iterator() | next#1 -> 10 | next#2 -> 20 | next#3 -> 30 | next#4 done   [result [10,20,30]]
const [a, ...rest] = it
    get @@iterator | @@iterator() | next#1 -> 10 | next#2 -> 20 | next#3 -> 30 | next#4 done   [result [10,[20,30]]]
Math.max(...it)
    get @@iterator | @@iterator() | next#1 -> 10 | next#2 -> 20 | next#3 -> 30 | next#4 done   [result 30]

[2] consumers that stop early
for-of with break at 20
    get @@iterator | @@iterator() | next#1 -> 10 | next#2 -> 20 | return()
for-of with return at 20
    get @@iterator | @@iterator() | next#1 -> 10 | next#2 -> 20 | return()   [result 20]
for-of whose body throws at 20
    get @@iterator | @@iterator() | next#1 -> 10 | next#2 -> 20 | return()   [caught Error body threw]
labelled continue outer, from inside
    get @@iterator | @@iterator() | next#1 -> 10 | return()
const [a] = it
    get @@iterator | @@iterator() | next#1 -> 10 | return()   [result 10]
const [a, b, c] = it  (exactly 3)
    get @@iterator | @@iterator() | next#1 -> 10 | next#2 -> 20 | next#3 -> 30 | return()   [result [10,20,30]]
const [a, b, c, d] = it  (one more)
    get @@iterator | @@iterator() | next#1 -> 10 | next#2 -> 20 | next#3 -> 30 | next#4 done   [result [10,20,30,"<undefined>"]]
Array.from(it, mapFn throws at 20)
    get @@iterator | @@iterator() | next#1 -> 10 | next#2 -> 20 | return()   [caught Error map threw]
new Map(it)  (10 is not an entry)
    get @@iterator | @@iterator() | next#1 -> 10 | return()   [caught TypeError Iterator value 10 is not an entry object]

[3] when next() itself throws
for-of, next#2 throws
    get @@iterator | @@iterator() | next#1 -> 10 | next#2 throws   [caught Error next failed]
[...it], next#2 throws
    get @@iterator | @@iterator() | next#1 -> 10 | next#2 throws   [caught Error next failed]

[4] Promise.all -- when does it read the iterable?
Promise.all(it)   right after the call:  get @@iterator | @@iterator() | next#1 -> 10 | next#2 -> 20 | next#3 -> 30 | next#4 done
                  resolved with [10,20,30]

[5] summary  (label / next calls / return calls)
  for (const x of it) {}                   4  0
  [...it]                                  4  0
  Array.from(it)                           4  0
  new Set(it)                              4  0
  const [a, ...rest] = it                  4  0
  Math.max(...it)                          4  0
  for-of with break at 20                  2  1
  for-of with return at 20                 2  1
  for-of whose body throws at 20           2  1
  labelled continue outer, from inside     1  1
  const [a] = it                           1  1
  const [a, b, c] = it  (exactly 3)        3  1
  const [a, b, c, d] = it  (one more)      4  0
  Array.from(it, mapFn throws at 20)       2  1
  new Map(it)  (10 is not an entry)        1  1
  for-of, next#2 throws                    2  0
  [...it], next#2 throws                   2  0
return() was called in 8 of 17 probes
```

**`[1]` 끝까지 읽는 소비자 — 여섯이 한 글자도 같다.**

- ★★★ **여섯 줄의 로그가 전부 `get @@iterator | @@iterator() | next#1 … next#4 done` 이다.**
  `for...of` · `[...it]` · `Array.from` · `new Set` · `[a, ...rest]` · `Math.max(...it)` — **부르는 방법도 순서도 같다.**
  ★★ 이것이 README 의 목표 문장 「`for...of`·스프레드·구조 분해가 **같은 프로토콜**을 쓴다」의 증거다.
- ★★★ **`next` 는 값 개수보다 한 번 더 불린다**(값 셋에 `next` 넷). 넷째가 `done` 을 받아 오는 호출이다.
  ★ 11번의 `[...tracedIterable(2)]` 가 `next 0, next 1, next 2` — **값 둘에 셋** — 였던 것과 같은 규칙이다.
- ★★ **`Symbol.iterator` 는 읽기 한 번, 호출 한 번**이다. 소비자가 그 메서드를 **캐시해 두고 다시 읽지 않는다.**
- ★★★ **`return()` 은 한 번도 안 불렸다.** 끝까지 읽어 `done: true` 를 **직접 받은** 소비자는 닫을 일이 없다.
- ★ `const [a, ...rest]` 는 **나머지가 있어서 끝까지 읽는다** — 그래서 `[1]` 쪽에 있다.

**`[2]` 조기 종료 — `return()` 이 불리는 자리 전수.**

```text
   끝을 "직접 봤나"                 return() 을 부르나

   next#4 done 을 받았다   ──────▶  안 부른다   (이터레이터가 스스로 끝났다)

   done 을 못 보고 멈췄다
     · break / return / 몸통 throw       ──▶  부른다
     · 바깥 루프로 continue outer        ──▶  부른다
     · [a]  · [a, b, c]  (패턴이 먼저 참)  ──▶  부른다   ★ 딱 3개여도
     · Array.from 의 mapFn 이 throw       ──▶  부른다
     · new Map 이 엔트리가 아닌 값을 만남  ──▶  부른다  -> 그리고 TypeError 로 막힌다

   next() 자체가 던졌다      ──────▶  안 부른다   ([3])
```

- ★★★ **`break` · `return` · 몸통의 `throw` 셋이 전부 `next#2 -> 20 | return()`** 이다. **빠져나가는 방법은 달라도 닫는 것은 같다.**
  ★ 명세의 `ForIn/OfBodyEvaluation` 이 그 자리를 이렇게 적는다 —
  "If LoopContinues(result, labelSet) is false, then … Return ? IteratorClose(iteratorRecord, status)."
- ★★ **`continue outer` 는 안쪽 루프 입장에서는 「계속」이 아니라 「떠남」이다.** `next#1` 다음 바로 `return()` 이다.
- ★★★ **`const [a, b, c] = it` 은 값이 딱 셋인데도 `return()` 을 부른다** — 로그가 `next#3 -> 30 | return()` 이다.
  **패턴이 셋을 받자마자 멈췄고, 넷째 `next` 를 불러 `done` 을 확인하지 않았다.**
  소비자 쪽에서 보면 **「끝났는지 모른다」** 이므로 닫는다.
  ★★★ **바로 아랫줄 `[a, b, c, d]` 는 넷째 `next` 가 `done` 을 받아 와서 `return()` 이 0** 이고 `d` 는 `undefined` 다.
  **패턴이 하나 길어지자 닫는 쪽에서 안 닫는 쪽으로 넘어갔다.**
- ★★ **`Array.from` 의 `mapFn` 이 던지면 `Array.from` 이 닫는다** — 사용자 콜백의 실패도 조기 종료다.
- ★★ **`new Map(it)` 은 `10` 을 받자 `TypeError Iterator value 10 is not an entry object` 로 막히고, 그 예외를 올리면서 `return()` 을 부른다.**
  엔트리 모양 검사는 **값을 받은 뒤 소비자가 하는 일**이라, 실패해도 이터레이터는 멀쩡하다 — 그래서 닫아 준다.

**`[3]` `next()` 자체가 던지면 — 아무도 `return()` 을 안 부른다.**

- ★★★ `for...of` 도 스프레드도 **`next#2 throws` 에서 멈추고 `return()` 이 없다.** 예외(`Error next failed`)만 그대로 올라온다.
- ★★★ **왜 — 고장 난 것이 이터레이터 자신이기 때문이다.** 스프레드 같은 소비자가 거치는 `IteratorNext` 는
  "If result is a throw completion, then Set iteratorRecord.[[Done]] to true." 로 **그 이터레이터를 「끝난 것」으로 표시**하고 예외를 올린다.
  `for...of` 쪽 `ForIn/OfBodyEvaluation` 은 `next` 를 "Let nextResult be ? Call(iteratorRecord.[[NextMethod]], iteratorRecord.[[Iterator]])." 로 부른다 —
  **`?` 가 그 예외를 닫기 없이 그대로 위로 올린다.** 닫기(`IteratorClose`)는 **몸통 쪽 완료**에만 걸려 있다.
  ★ 비유로 — **기계가 비명을 질렀는데 그 기계에게 「그만 갑니다」를 말할 이유가 없다.**

**`[4]` `Promise.all` — 호출 안에서 동기로 다 읽는다.**

- ★★★ **`Promise.all(it)` 이 돌아온 바로 다음 줄에 로그가 이미 `next#4 done` 까지 차 있다.**
  `then` 이 불리기 전, **마이크로태스크가 한 번도 돌기 전**이다.
  ★★ 즉 **「비동기 API 라서 나중에 읽겠지」가 아니다** — 이터러블 읽기는 **호출 그 자리**에서 끝나고, 기다리는 것은 각 값의 결판뿐이다.
  ★ `Promise.all` 의 나머지(거부 전파·`allSettled` 와의 차이)는 목록의 **38번 주제** 「Promise 조합기」가 정본이다.

**`[5]` 요약 표 — ② 전수 격자.**

- ★★★ 17줄이 `next` 횟수와 `return` 횟수 두 칸으로 접힌다. **`return` 칸이 `1` 인 줄은 전부 「`done` 을 못 보고 멈춘 줄」이고, `0` 인 줄은 전부 「`done` 을 봤거나 `next` 가 던진 줄」이다.** 예외가 하나도 없다.
- 표 마지막 줄의 집계는 **스크립트가 직접 센 것**이다 — 그 숫자를 본문에 옮겨 적지 않는다.

### (2) ★★★ `return()` 쪽의 계약 — 없어도 되고, 있으면 함수여야 하고, 누가 이기나

**언제 쓰나** — 직접 만든 이터레이터에 **정리 코드**(파일 닫기·구독 해제)를 `return()` 으로 붙일 때.

```js
// js16b-19f-close-and-helpers.js
// return() 쪽 계약을 더 찍는다 -- 그리고 이터레이터 헬퍼(ES2025)가 이 두 판에 있나를 묻는다.
const run = (label, fn) => {
  let r;
  try { r = "-> " + fn(); } catch (e) { r = "-> " + e.constructor.name + " " + e.message; }
  console.log(label.padEnd(48) + r);
};
const J = (v) => JSON.stringify(v, (k, x) => (x === undefined ? "<undefined>" : x));
function closer(ret) {
  return { [Symbol.iterator]() { return { next: () => ({ value: 1, done: false }), return: ret }; } };
}

console.log("[1] what return() may be -- on a break");
run("no return at all", () => { for (const v of closer(undefined)) break; return "ok"; });
run("return: 1  (not callable)", () => { for (const v of closer(1)) break; return "ok"; });
run("return() throws", () => { for (const v of closer(() => { throw new Error("from return"); })) break; return "ok"; });

console.log("");
console.log("[2] when the body already threw, whose error wins?");
run("body throws, return() throws too", () => { for (const v of closer(() => { throw new Error("from return"); })) throw new Error("from body"); });
run("body throws, return() gives a primitive", () => { for (const v of closer(() => 1)) throw new Error("from body"); });

console.log("");
console.log("[3] the value that comes with done: true -- three more consumers");
function* withReturn() { yield "a"; return "R"; }
run("Array.from(withReturn())", () => J(Array.from(withReturn())));
run("const [x, y] = withReturn()", () => { const [x, y] = withReturn(); return J([x, y]); });
run("new Set(withReturn()).size", () => new Set(withReturn()).size);

console.log("");
console.log("[4] iterator helpers (ES2025) -- present in this node?");
run("typeof globalThis.Iterator", () => typeof globalThis.Iterator);
run("typeof [].values().map", () => typeof [].values().map);
run("typeof [].values().toArray", () => typeof [].values().toArray);

console.log("");
console.log("[5] arguments -- array-like; is it also iterable?");
run("typeof arguments[Symbol.iterator]", function () { return typeof arguments[Symbol.iterator]; });
run("[...arguments]  (called with 1, 2)", () => (function () { return J([...arguments]); })(1, 2));

console.log("");
console.log("[6] an endless iterator -- does const [a] stop after one value?");
let nexts = 0, closes = 0;
const endless = { [Symbol.iterator]() { return { next: () => ({ value: ++nexts, done: false }), return: () => { closes++; return {}; } }; } };
run("const [a] = endless", () => { const [a] = endless; return J({ a, nexts, closes }); });

console.log("");
console.log("[7] e followed by a combining mark (U+0301)");
const e = "e" + String.fromCodePoint(0x301);
run("e + U+0301  .length / [...].length", () => e.length + " / " + [...e].length);
```
```text
===== node20 js16b-19f-close-and-helpers.js (exit=0) =====
[1] what return() may be -- on a break
no return at all                                -> ok
return: 1  (not callable)                       -> TypeError number 1 is not a function
return() throws                                 -> Error from return

[2] when the body already threw, whose error wins?
body throws, return() throws too                -> Error from body
body throws, return() gives a primitive         -> Error from body

[3] the value that comes with done: true -- three more consumers
Array.from(withReturn())                        -> ["a"]
const [x, y] = withReturn()                     -> ["a","<undefined>"]
new Set(withReturn()).size                      -> 1

[4] iterator helpers (ES2025) -- present in this node?
typeof globalThis.Iterator                      -> undefined
typeof [].values().map                          -> undefined
typeof [].values().toArray                      -> undefined

[5] arguments -- array-like; is it also iterable?
typeof arguments[Symbol.iterator]               -> function
[...arguments]  (called with 1, 2)              -> [1,2]

[6] an endless iterator -- does const [a] stop after one value?
const [a] = endless                             -> {"a":1,"nexts":1,"closes":1}

[7] e followed by a combining mark (U+0301)
e + U+0301  .length / [...].length              -> 2 / 2
```

- ★★★ **`return` 이 아예 없으면 그냥 끝난다**(`-> ok`). `return` 은 **선택 사항**이다 —
  `IteratorClose` 가 "If return is undefined, return ? completion." 으로 **원래 완료를 그대로 돌려준다.**
  그래서 `(1)` 의 로그에 `return()` 이 찍힌 것은 **우리가 달아 놨기 때문**이지 모든 이터레이터에 있어서가 아니다.
- ★★ **`return` 이 함수가 아니면(`1`) `break` 가 `TypeError number 1 is not a function` 으로 막힌다.**
  **없는 것은 괜찮고, 있는데 틀린 것은 안 된다.**
- ★★ **`return()` 이 던지면 `break` 자리에서 그 예외가 올라온다**(`Error from return`). 정리 코드의 실패가 **루프 바깥으로 샌다.**
- ★★★ **`[2]` 몸통이 이미 던졌으면 몸통의 예외가 이긴다** — `return()` 이 던져도, 원시값을 돌려줘도 결과는 `Error from body` 다.
  명세 `IteratorClose` 의 순서 그대로다 — "If completion is a throw completion, return ? completion." 이
  "If innerResult.[[Value]] is not an Object, throw a TypeError exception." **보다 앞에** 있다.
  ★ 동작 (4)의 `[4]` 마지막 줄 — `break` 로 닫을 때 `return()` 이 원시값을 주면 `TypeError` — 와 **짝을 이룬다.**
  **원래 완료가 정상일 때만 `return()` 의 결과를 검사한다.**
- ★★ **`[3]` `done: true` 와 같이 온 값은 `Array.from` · `[x, y]` · `new Set` 도 버린다** — 동작 (3)의 `[4]` 에서 다시 본다.
- ★★ **`[4]` 이터레이터 헬퍼는 이 두 판에 없다** — `Iterator` 전역도, 배열 이터레이터의 `map`·`toArray` 도 `undefined` 다.
  ES2025 기능이고, 이 블록은 **두 판에서 identical** 이다. **이 주제는 헬퍼를 한 줄도 쓰지 않는다**([목록의 **21번 주제**](../21-iterator-helpers/)).
- ★★ **`[5]` `arguments` 는 유사 배열이면서 이터러블이다** — `arguments[Symbol.iterator]` 가 `function` 이고 `[...arguments]` 가 `[1,2]` 다.
  **유사 배열이라서 도는 것이 아니라 제 `Symbol.iterator` 를 따로 가져서 돈다.** 동작 (4)의 `[2]` 와 짝이다.
- ★★★ **`[6]` 끝없는 이터레이터에 `const [a]` 는 `next` 한 번, `return()` 한 번으로 멈춘다**(`{"a":1,"nexts":1,"closes":1}`).
  **패턴이 채워지면 더 읽지 않고 닫는다** — 동작 (1)의 `[a, b, c]` 가 딱 맞아도 닫는 것과 **같은 규칙의 다른 얼굴**이다.
- ★ **`[7]` 결합 문자 하나를 붙인 `e` 는 `length` 도 2, `[...e].length` 도 2** 다. **코드 포인트 단위는 사람이 보는 한 글자와 다르다** — 동작 (5)에서 이어진다.

### (3) ★★★ 이터러블 대 이터레이터 — 두 번 돌면 갈린다

**언제 쓰나** — 함수에 넘긴 값을 **그 함수가 두 번 돌 수 있나**를 판단할 때.

```js
// js16b-19b-make-your-own.js
// 이터러블을 직접 만든다 -- 그리고 「이터러블」과 「이터레이터」가 다른 물건인 자리를 찍는다.
const row = (label, v) => console.log(label.padEnd(46) + v);

console.log("[1] a class with [Symbol.iterator]()");
class Countdown {
  constructor(from) { this.from = from; }
  [Symbol.iterator]() {
    let n = this.from;
    return { next: () => (n > 0 ? { value: n--, done: false } : { value: undefined, done: true }) };
  }
}
const cd = new Countdown(3);
row("[...cd]  first time", JSON.stringify([...cd]));
row("[...cd]  second time", JSON.stringify([...cd]));

console.log("");
console.log("[2] an iterator whose [Symbol.iterator]() returns itself");
const once = cd[Symbol.iterator]();
once[Symbol.iterator] = function () { return this; };
row("[...once]  first time", JSON.stringify([...once]));
row("[...once]  second time", JSON.stringify([...once]));

console.log("");
console.log("[3] generators and built-in iterators");
function* gen() { yield 1; yield 2; }
const g = gen();
row("g[Symbol.iterator]() === g", g[Symbol.iterator]() === g);
row("[...g] then [...g]", JSON.stringify([...g]) + " then " + JSON.stringify([...g]));
const ai = [1, 2][Symbol.iterator]();
row("arrayIterator[Symbol.iterator]() === itself", ai[Symbol.iterator]() === ai);
row("[...ai] then [...ai]", JSON.stringify([...ai]) + " then " + JSON.stringify([...ai]));
const m = new Map([["k", 1]]);
row("[...m.keys()] twice from ONE keys() call", (() => { const k = m.keys(); return JSON.stringify([...k]) + " then " + JSON.stringify([...k]); })());
row("gen[Symbol.iterator]  (the function itself)", typeof gen[Symbol.iterator]);

console.log("");
console.log("[4] the value that comes with done: true");
function* withReturn() { yield "a"; return "the return value"; }
row("[...withReturn()]", JSON.stringify([...withReturn()]));
const seen = []; for (const x of withReturn()) seen.push(x);
row("for-of withReturn()", JSON.stringify(seen));
const it = withReturn();
row("manual next() x2", JSON.stringify(it.next()) + " " + JSON.stringify(it.next()));

console.log("");
console.log("[5] a result object without `done`");
let calls = 0;
const noDone = { [Symbol.iterator]() { return { next() { calls++; return calls > 3 ? { done: true } : { value: calls }; } }; } };
row("[...noDone]", JSON.stringify([...noDone]));
```
```text
===== node20 js16b-19b-make-your-own.js (exit=0) =====
[1] a class with [Symbol.iterator]()
[...cd]  first time                           [3,2,1]
[...cd]  second time                          [3,2,1]

[2] an iterator whose [Symbol.iterator]() returns itself
[...once]  first time                         [3,2,1]
[...once]  second time                        []

[3] generators and built-in iterators
g[Symbol.iterator]() === g                    true
[...g] then [...g]                            [1,2] then []
arrayIterator[Symbol.iterator]() === itself   true
[...ai] then [...ai]                          [1,2] then []
[...m.keys()] twice from ONE keys() call      ["k"] then []
gen[Symbol.iterator]  (the function itself)   undefined

[4] the value that comes with done: true
[...withReturn()]                             ["a"]
for-of withReturn()                           ["a"]
manual next() x2                              {"value":"a","done":false} {"value":"the return value","done":true}

[5] a result object without `done`
[...noDone]                                   [1,2,3]
```

```text
   이터러블 (가게)                         자기 자신을 돌려주는 이터레이터 (기계 겸 창구)

   cd[Symbol.iterator]()  -> 새 기계 A       g[Symbol.iterator]()  -> g   (자기 자신)
   cd[Symbol.iterator]()  -> 새 기계 B       g[Symbol.iterator]()  -> g   (같은 것)

   [...cd]  [3,2,1]                         [...g]  [1,2]
   [...cd]  [3,2,1]  <- 새 기계라 처음부터    [...g]  []     <- 이미 done 인 기계를 또 받았다
```

- ★★★ **`Countdown` 은 `[Symbol.iterator]()` 를 부를 때마다 새 이터레이터를 만든다** — 그래서 두 번 돌아도 `[3,2,1]` 이다.
  **상태(`n`)가 이터러블이 아니라 이터레이터 안에 있다**는 것이 그 비결이다.
- ★★★ **이터레이터에 `[Symbol.iterator]() { return this; }` 를 달면 두 번째가 `[]` 다.**
  두 번째 스프레드도 `Symbol.iterator` 를 부르지만 **같은 기계를 돌려받고**, 그 기계는 이미 `done` 이다. **에러가 아니라 빈 결과**다.
- ★★★ **제너레이터 객체 · 배열 이터레이터 · `m.keys()` 가 전부 이 둘째 부류다** — `g[Symbol.iterator]() === g` 가 `true`, 두 번째가 `[]`.
  ★★ 「배열은 몇 번이고 돌 수 있는데?」 — **배열(가게)** 은 그렇다. `[1, 2][Symbol.iterator]()` 가 돌려준 **기계**는 아니다.
- ★ **`typeof gen[Symbol.iterator]` 가 `undefined`** — 제너레이터 **함수**는 이터러블이 아니다. 불러서 나온 **객체**가 이터러블이다.
  제너레이터가 무엇을 어떻게 멈추고 재개하나는 [목록의 **20번 주제**](../20-generators/)가 정본이다.
- ★★★ **`[4]` `return "the return value"` 는 스프레드에도 `for...of` 에도 안 나온다** — `["a"]` 뿐이다.
  **수동 `next()` 두 번째에서만** `{"value":"the return value","done":true}` 로 보인다.
  ★★ **이것이 이 주제의 「창을 바꿔 물은」 자리다.** 소비자 창은 전부 그 값을 버리므로 **닫혀 있고**, 수동 `next()` 로 바꿔 물어야 보인다.
  ★ 왜 버리나 — 소비자의 반복은 `IteratorComplete` 가 `true` 이면 **값을 읽지 않고** 멈춘다 —
  `ForIn/OfBodyEvaluation` 은 "If done is true, return iterationResult." 다음 줄에서야 "Let nextValue be ? IteratorValue(nextResult)." 를 한다.
- ★★ **`[5]` `done` 이 없는 결과는 「안 끝났다」다** — `{ value: calls }` 세 번이 `[1,2,3]` 으로 모였다.
  `IteratorComplete` 가 "Return ToBoolean(? Get(iteratorResult, "done"))." — **`undefined` 는 `false`** 다.
  ★ 거꾸로 **`done` 을 영영 안 주는 이터레이터는 스프레드를 영영 안 끝낸다** — 이 문서는 그 무한 루프를 **일부러 안 돌렸다.**

### (4) ★★ 이터러블이 아닌 것 — 자리마다 문구가 다르고, 유사 배열에는 대체 경로가 없다

**언제 쓰나** — `X is not iterable` 을 만났을 때 **무엇이 모자란지** 문구로 거꾸로 짚을 때.

```js
// js16b-19c-errors.js
// 이터러블이 아닌 것을 들이대면 -- 문마다 에러 문구가 같은가. 유사 배열에 대체 경로가 있나.
const run = (label, fn) => {
  let r;
  try { r = "-> " + fn(); } catch (e) { r = "-> " + e.constructor.name + " " + e.message; }
  console.log(label.padEnd(44) + r);
};
const J = (v) => JSON.stringify(v);
const plain = { a: 1 };
const arrayLike = { length: 2, 0: "x", 1: "y" };
const id = (...xs) => xs;

console.log("[1] a plain object in six places");
run("for (const v of plain)", () => { for (const v of plain) {} return "ok"; });
run("[...plain]", () => J([...plain]));
run("id(...plain)", () => J(id(...plain)));
run("const [v] = plain", () => { const [v] = plain; return J(v); });
run("new Set(plain)", () => J([...new Set(plain)]));
run("Array.from(plain)", () => J(Array.from(plain)));

console.log("");
console.log("[2] an array-like { length: 2, 0: 'x', 1: 'y' } -- is there a fallback?");
run("for (const v of arrayLike)", () => { const r = []; for (const v of arrayLike) r.push(v); return J(r); });
run("[...arrayLike]", () => J([...arrayLike]));
run("Array.from(arrayLike)", () => J(Array.from(arrayLike)));
run("Array.prototype.slice.call(arrayLike)", () => J(Array.prototype.slice.call(arrayLike)));
run("id.apply(null, arrayLike)", () => J(id.apply(null, arrayLike)));
arrayLike[Symbol.iterator] = Array.prototype[Symbol.iterator];
run("after borrowing Array's @@iterator: [...]", () => J([...arrayLike]));

console.log("");
console.log("[3] null and undefined");
run("for (const v of null)", () => { for (const v of null) {} return "ok"; });
run("for (const v of undefined)", () => { for (const v of undefined) {} return "ok"; });
run("[...undefined]", () => J([...undefined]));

console.log("");
console.log("[4] a broken protocol -- each step checks its own contract");
run("@@iterator is not a function", () => J([...{ [Symbol.iterator]: 1 }]));
run("@@iterator returns a primitive", () => J([...{ [Symbol.iterator]() { return 1; } }]));
run("next() returns a primitive", () => J([...{ [Symbol.iterator]() { return { next() { return 1; } }; } }]));
run("iterator has no next", () => J([...{ [Symbol.iterator]() { return {}; } }]));
run("return() returns a primitive (on break)", () => {
  const it = { [Symbol.iterator]() { return { next: () => ({ value: 1, done: false }), return: () => 1 }; } };
  for (const v of it) break;
  return "ok";
});
```
```text
===== node20 js16b-19c-errors.js (exit=0) =====
[1] a plain object in six places
for (const v of plain)                      -> TypeError plain is not iterable
[...plain]                                  -> TypeError plain is not iterable
id(...plain)                                -> TypeError Spread syntax requires ...iterable[Symbol.iterator] to be a function
const [v] = plain                           -> TypeError plain is not iterable
new Set(plain)                              -> TypeError object is not iterable (cannot read property Symbol(Symbol.iterator))
Array.from(plain)                           -> []

[2] an array-like { length: 2, 0: 'x', 1: 'y' } -- is there a fallback?
for (const v of arrayLike)                  -> TypeError arrayLike is not iterable
[...arrayLike]                              -> TypeError arrayLike is not iterable
Array.from(arrayLike)                       -> ["x","y"]
Array.prototype.slice.call(arrayLike)       -> ["x","y"]
id.apply(null, arrayLike)                   -> ["x","y"]
after borrowing Array's @@iterator: [...]   -> ["x","y"]

[3] null and undefined
for (const v of null)                       -> TypeError null is not iterable
for (const v of undefined)                  -> TypeError undefined is not iterable
[...undefined]                              -> TypeError undefined is not iterable

[4] a broken protocol -- each step checks its own contract
@@iterator is not a function                -> TypeError {(intermediate value)} is not iterable
@@iterator returns a primitive              -> TypeError Result of the Symbol.iterator method is not an object
next() returns a primitive                  -> TypeError Iterator result 1 is not an object
iterator has no next                        -> TypeError {(intermediate value)} is not iterable
return() returns a primitive (on break)     -> TypeError Iterator result 1 is not an object
```

- ★★★ **`[1]` 평범한 객체 하나가 여섯 자리에서 네 가지로 갈린다.**
  `for...of` · `[...plain]` · `const [v] = plain` 은 **`plain is not iterable`**(변수 이름이 문구에 들어간다),
  호출 스프레드 `id(...plain)` 은 **`Spread syntax requires ...iterable[Symbol.iterator] to be a function`**,
  `new Set(plain)` 은 **`object is not iterable (cannot read property Symbol(Symbol.iterator))`**,
  그리고 **`Array.from(plain)` 은 `[]`** — 에러가 아니다.
  ★★★ **종류는 셋 다 `TypeError` 이고 문구만 다르다.** 문구는 V8 의 것이다.
  ★★ `Array.from` 만 조용한 까닭은 11번이 이미 봤다 — **이터러블이 아니면 유사 배열 문으로 들어간다.** `plain` 에는 `length` 가 없어 빈 배열이 나왔다.
- ★★★ **`[2]` 유사 배열 `{ length: 2, 0: 'x', 1: 'y' }` 에 `for...of` 와 스프레드는 `TypeError`** 다.
  **인덱스와 `length` 가 다 있어도 JS 는 그것으로 돌지 않는다.** 대체 경로가 없다.
  `Array.from` · `Array.prototype.slice.call` · `apply` 는 **유사 배열 문**이라 된다(11번의 격자 그대로).
- ★★★ **`Array.prototype[Symbol.iterator]` 를 빌려 붙이자 스프레드가 `["x","y"]`** 가 되었다.
  **이터러블은 「무엇으로 태어났나」가 아니라 「그 프로퍼티가 있나」다** — 이 줄이 ③ 브랜드 태그를 이 주제에서 부적용으로 만든다.
  ★ 빌려 온 배열 이터레이터가 이 객체에서 무엇을 읽어 도는지는 **로그를 안 심었다.** 결과만 적는다.
- ★★★ **`[3]` `null`·`undefined` 에 `for...of` 는 `TypeError`** 다.
  ★★★ **[18번](../18-for-in-and-enumeration/2-summary.md)의 `for-in null` 은 조용히 0회**(`[]`)였다 — **같은 모양의 문이 반대로 군다.**
  명세가 그 갈림을 한 자리에 적는다 — `ForIn/OfHeadEvaluation` 은 **enumerate(`for...in`)일 때만** `null`/`undefined` 를 break 완료로 바꾸고,
  iterate(`for...of`)는 그대로 `GetIterator` 로 가서 막힌다.
- ★★ **`[4]` 깨진 프로토콜 다섯 — 단계마다 제 계약을 검사한다.**
  `Symbol.iterator` 가 함수가 아니면 **`{(intermediate value)} is not iterable`**,
  그것이 원시값을 돌려주면 **`Result of the Symbol.iterator method is not an object`**(명세 `GetIteratorFromMethod` 의 "If iterator is not an Object, throw a TypeError exception."),
  `next()` 가 원시값을 주면 **`Iterator result 1 is not an object`**(`IteratorNext` 의 "If result is not an Object, then … Throw a TypeError exception.").
  ★★★ **관찰 하나** — **`next` 가 아예 없는 이터레이터도 `{(intermediate value)} is not iterable`** 이다.
  「`next` 가 없다」가 아니라 **「이터러블이 아니다」로 보고된다** — 첫 줄과 문구가 같다. **이 판의 V8 이 그렇게 적는다**는 관찰로만 적는다.
  ★ `break` 때 `return()` 이 원시값을 주면 **`Iterator result 1 is not an object`** — `next` 쪽과 **같은 문구**다.

**두 판에서 돌리면 — 이 블록 하나가 갈린다.**

```text
===== node18 js16b-19c-errors.js (exit=0) =====
[1] a plain object in six places
for (const v of plain)                      -> TypeError plain is not iterable
[...plain]                                  -> TypeError plain is not iterable
id(...plain)                                -> TypeError Found non-callable @@iterator
const [v] = plain                           -> TypeError plain is not iterable
new Set(plain)                              -> TypeError object is not iterable (cannot read property Symbol(Symbol.iterator))
Array.from(plain)                           -> []

[2] an array-like { length: 2, 0: 'x', 1: 'y' } -- is there a fallback?
for (const v of arrayLike)                  -> TypeError arrayLike is not iterable
[...arrayLike]                              -> TypeError arrayLike is not iterable
Array.from(arrayLike)                       -> ["x","y"]
Array.prototype.slice.call(arrayLike)       -> ["x","y"]
id.apply(null, arrayLike)                   -> ["x","y"]
after borrowing Array's @@iterator: [...]   -> ["x","y"]

[3] null and undefined
for (const v of null)                       -> TypeError null is not iterable
for (const v of undefined)                  -> TypeError undefined is not iterable
[...undefined]                              -> TypeError undefined is not iterable

[4] a broken protocol -- each step checks its own contract
@@iterator is not a function                -> TypeError {(intermediate value)} is not iterable
@@iterator returns a primitive              -> TypeError Result of the Symbol.iterator method is not an object
next() returns a primitive                  -> TypeError Iterator result 1 is not an object
iterator has no next                        -> TypeError {(intermediate value)} is not iterable
return() returns a primitive (on break)     -> TypeError Iterator result 1 is not an object
```

- ★★★ **갈린 것은 넷째 줄 하나 — `id(...plain)` 이다.** v18 은 **`Found non-callable @@iterator`**, v20 은 **`Spread syntax requires ...iterable[Symbol.iterator] to be a function`**.
  ★★★ **11번의 `f(...obj)` 가 갈린 것과 정확히 같은 자리, 같은 두 문구다.** 호출 자리의 스프레드만 v20 에서 문구가 바뀌었다.
  **배열 자리 `[...plain]` 과 `for...of` 는 두 판 모두 `plain is not iterable`** 이다.
- ★★ **값·종류는 한 글자도 안 갈렸다.** 갈린 것은 **문구뿐**이다 — 그래서 「흔들리는 칸」에 문구를 넣었다.

```sh
# js16b-vdiff.sh
#!/usr/bin/env bash
# 두 판이 갈린 블록이 몇 개인가 -- 스크립트가 직접 센다.
set -u -o pipefail
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
cd "$(dirname "$0")"
same=0; diffn=0
for f in js16b-1[6-9]?-*.js; do
  a="$("$N18" "$f" 2>&1)"
  b="$("$N20" "$f" 2>&1)"
  if [ "$a" = "$b" ]; then
    printf '%-32s identical\n' "$f"; same=$((same + 1))
  else
    printf '%-32s DIFFERS\n' "$f"; diffn=$((diffn + 1))
    diff <(printf '%s\n' "$a") <(printf '%s\n' "$b") | sed 's/^/    /'
  fi
done
echo ""
echo "identical $same  ·  differs $diffn  ·  total $((same + diffn))"
```
```text
===== ./js16b-vdiff.sh (exit=0) =====
js16b-16a-where.js               identical
js16b-16b-rules.js               identical
js16b-16c-order.js               identical
js16b-16d-define-vs-set.js       identical
js16b-16e-private.js             identical
js16b-16f-private-windows.js     identical
js16b-16g-forin.js               identical
js16b-17a-two-chains.js          identical
js16b-17b-super-call.js          identical
js16b-17c-homeobject.js          identical
js16b-17d-builtins.js            identical
js16b-17e-ctor-virtual.js        identical
js16b-17f-super-edges.js         identical
js16b-18a-grid.js                identical
js16b-18b-array.js               identical
js16b-18c-hasown.js              identical
js16b-18d-mutate.js              identical
js16b-18f-refimpl.js             identical
js16b-19a-protocol-log.js        identical
js16b-19b-make-your-own.js       identical
js16b-19c-errors.js              DIFFERS
    4c4
    < id(...plain)                                -> TypeError Found non-callable @@iterator
    ---
    > id(...plain)                                -> TypeError Spread syntax requires ...iterable[Symbol.iterator] to be a function
js16b-19d-strings-maps.js        identical
js16b-19f-close-and-helpers.js   identical

identical 22  ·  differs 1  ·  total 23
```

대조기의 집계 —

`identical 22  ·  differs 1  ·  total 23`

★★ **나머지 블록은 전부 `identical`** 이고, 갈린 것은 위의 `js16b-19c-errors.js` 한 줄이다.

### (5) ★★ 내장 이터러블 둘 — 문자열은 「무엇 단위로」, `Map`·`Set` 은 「어떤 순서로」

**언제 쓰나** — 문자열 길이를 세거나 한 글자씩 자를 때 · `Map` 을 돌며 순서에 기대거나 순회 중에 고칠 때.

```js
// js16b-19d-strings-maps.js
// 내장 이터러블 둘 -- 문자열은 「무엇 단위로」 도나, Map·Set 은 「어떤 순서로」 도나.
const row = (label, v) => console.log(label.padEnd(44) + v);
const hex = (c) => c.codePointAt(0).toString(16).toUpperCase();

console.log("[1] a string with one astral character (built from a code point, so this file stays ASCII)");
const s = "a" + String.fromCodePoint(0x1f600) + "b";
row("s.length  (UTF-16 code units)", s.length);
row("[...s].length  (for-of units)", [...s].length);
row("[...s] as code points", JSON.stringify([...s].map(hex)));
row("s.split('') as code units", JSON.stringify(s.split("").map((c) => c.charCodeAt(0).toString(16).toUpperCase())));
const units = []; for (let i = 0; i < s.length; i++) units.push(s[i].length);
row("for (let i...) s[i].length each", JSON.stringify(units));
const cps = []; for (const ch of s) cps.push(ch.length);
row("for (const ch of s) ch.length each", JSON.stringify(cps));

console.log("");
console.log("[2] Map and Set order, with integer-like keys");
const m = new Map([["b", 1], [2, 1], ["a", 1], [1, 1]]);
const obj = { b: 1, 2: 1, a: 1, 1: 1 };
row("[...map.keys()]", JSON.stringify([...m.keys()]));
row("Object.keys(same keys as an object)", JSON.stringify(Object.keys(obj)));
m.delete("b"); m.set("b", 1);
row("after delete b, set b  -> keys", JSON.stringify([...m.keys()]));
m.set(2, "overwritten");
row("after set(2, ...) again -> keys", JSON.stringify([...m.keys()]));
const st = new Set(["z", 3, "y", 1]);
row("[...set]", JSON.stringify([...st]));

console.log("");
console.log("[3] changing a Map / Set / Array during for-of");
const live = new Set([1, 2]);
const visited = [];
for (const v of live) { visited.push(v); if (v === 1) live.add(3); if (v === 2) live.delete(1); }
row("add 3 at 1, delete 1 at 2", "visited " + JSON.stringify(visited) + "   final " + JSON.stringify([...live]));
const lm = new Map([["a", 1], ["b", 2]]);
const lv = [];
for (const [k] of lm) { lv.push(k); if (k === "a") lm.delete("b"); }
row("Map: delete b at a", "visited " + JSON.stringify(lv));
const arr = [1, 2];
const av = [];
for (const v of arr) { av.push(v); if (v === 1) arr.push(3); }
row("Array: push 3 at 1", "visited " + JSON.stringify(av));
```
```text
===== node20 js16b-19d-strings-maps.js (exit=0) =====
[1] a string with one astral character (built from a code point, so this file stays ASCII)
s.length  (UTF-16 code units)               4
[...s].length  (for-of units)               3
[...s] as code points                       ["61","1F600","62"]
s.split('') as code units                   ["61","D83D","DE00","62"]
for (let i...) s[i].length each             [1,1,1,1]
for (const ch of s) ch.length each          [1,2,1]

[2] Map and Set order, with integer-like keys
[...map.keys()]                             ["b",2,"a",1]
Object.keys(same keys as an object)         ["1","2","b","a"]
after delete b, set b  -> keys              [2,"a",1,"b"]
after set(2, ...) again -> keys             [2,"a",1,"b"]
[...set]                                    ["z",3,"y",1]

[3] changing a Map / Set / Array during for-of
add 3 at 1, delete 1 at 2                   visited [1,2,3]   final [2,3]
Map: delete b at a                          visited ["a"]
Array: push 3 at 1                          visited [1,2,3]
```

```text
   s = "a" + (U+1F600) + "b"

   코드 유닛 (s.length, s[i], split(''))     61 | D83D | DE00 | 62        -> 4 개
   코드 포인트 (for...of, [...s])            61 | 1F600       | 62        -> 3 개
                                                 ^^^^^^^^^^^^
                                                 for...of 는 서로게이트 쌍을 한 덩어리로 준다
```

- ★★★ **`s.length` 는 4, `[...s].length` 는 3** 이다. 문자열 이터레이터는 **코드 포인트 단위**로 돈다.
  인덱스 `for` 로 돌면 조각 넷이 **각각 길이 1**(`[1,1,1,1]`)이고, `for...of` 로 돌면 가운데 조각이 **길이 2**(`[1,2,1]`)다.
  ★ 코드 유닛·서로게이트 쌍 자체는 [04번](../04-strings-and-utf16/2-summary.md)이 정본이다. 여기서는 **이터레이터가 그 쌍을 합쳐 준다**는 사실까지다.
  ★ 「글자」(사람이 보는 한 글자)는 **코드 포인트와도 또 다르다** — 결합 문자 하나를 붙인 `e` 가 `[...e].length` 2 였다(동작 (2)의 `[7]`).
- ★★★ **`Map` 의 키는 넣은 순서 그대로** `["b",2,"a",1]` 이다. **같은 키를 객체에 넣으면 `Object.keys` 가 `["1","2","b","a"]`** — 정수 같은 키가 앞으로 온다([13번](../13-object-literals-and-properties/2-summary.md)).
  ★★ **정수 키를 앞세우는 규칙은 객체의 것이지 `Map` 의 것이 아니다.** `Set` 도 `["z",3,"y",1]` 로 넣은 순서다.
  명세 note — `Map.prototype.forEach` 는 "in key insertion order".
- ★★ **지웠다 다시 넣은 키는 맨 뒤로 간다**(`[2,"a",1,"b"]`). **이미 있는 키에 `set` 은 자리를 안 바꾼다**(`set(2, …)` 뒤에도 같은 순서).
- ★★★ **`[3]` 순회는 살아 있다.** `Set` 을 도는 중에 넣은 `3` 이 **방문되고**, `Map` 을 도는 중에 지운 `b` 는 **방문되지 않는다.**
  명세 note 가 그대로 적는다 — `Set`: "New values added after the call to forEach begins are visited." ·
  `Map`: "Keys that are deleted after the call to forEach begins and before being visited are not visited …".
  ★ note 는 `forEach` 의 것이고, 이 블록은 **`for...of` 로 같은 결과**를 찍었다.
  ★★ **배열을 도는 중에 `push` 한 값도 방문된다**(`[1,2,3]`). 순회 중 변경은 **세 컨테이너 모두 「살아 있는 쪽」** 이었다.

### (6) ★★ 파이썬과의 대비 — 대체 경로가 한쪽에만 있다

**언제 쓰나** — 파이썬 습관으로 「인덱스만 주면 돌겠지」를 기대할 때.

Python 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **32번**이
「**`__iter__` 가 없어도 `__getitem__` 만 있으면 `for` 가 0, 1, 2 … `IndexError` 까지 돈다**」를 로그로 찍었다.
같은 갈래의 **16번**이 그 낡은 프로토콜과 `StopIteration` 의 정본이다.

```text
                        "나를 돌려라"를 무엇으로 약속하나     약속이 없을 때 대체 경로

   Python  for v in x    __iter__                          __getitem__ (0 부터 IndexError 까지)
   JS      for...of x    [Symbol.iterator]                 없다 -> TypeError 로 막힌다
   JS      Array.from x  [Symbol.iterator]                 length + 인덱스 (유사 배열 문)

   끝 신호               Python: StopIteration 예외         JS: { done: true } 라는 값
```

- ★★★ **JS 의 `for...of` 에는 대체 경로가 없다.** 유사 배열에 인덱스와 `length` 가 다 있어도 `TypeError` 였다(동작 (4)의 `[2]`).
  ★★ **「잴 것이 없다」가 아니라 「재 봤더니 없다」다** — 그 판단이 이 문서의 창 표에 따로 올라 있는 이유다.
  ★ JS 에서 「두 번째 문」을 가진 것은 **`Array.from` 하나**다(11번의 결론).
- ★★ **끝 신호가 다르다** — 파이썬은 **`StopIteration` 이라는 예외**, JS 는 **`{ done: true }` 라는 값**이다.
  그래서 JS 에는 「`next()` 가 던졌다」와 「끝났다」가 **명확히 다른 사건**이고, 동작 (1)의 `[3]` 처럼 **닫기 규칙도 다르게 걸린다.**
- ★ **소진된 이터레이터가 빈 것처럼 보이는 것은 두 언어가 같다** — 파이썬 16번의 「두 번째 `list(it)` 는 `[]`」와 동작 (3)의 `[...g]` 두 번째가 같은 모양이다.

## 문법 — 형태와 규칙

```text
   이터러블을 만드는 법 · 소비하는 법 · 닫는 법

   만들기
   class C { [Symbol.iterator]() { return { next() { ... } }; } }    매번 새 이터레이터 -> 여러 번 돈다
   it[Symbol.iterator] = function () { return this; }                자기 자신 -> 한 번만 돈다
   function* g() { ... }   g()                                       제너레이터 객체 (20번 주제)

   결과 객체
   { value: v, done: false }      값 하나
   { value: v, done: true }       끝  -- v 는 소비자가 버린다
   { value: v }                   done 이 없다 -> 안 끝난 것

   소비하기 (전부 같은 세 단계)
   for (const x of it) { }        [...it]        f(...it)        const [a, b] = it
   Array.from(it)                 new Set(it)    new Map(it)     Promise.all(it)

   닫기 (선택 사항)
   return() { ...정리...; return {}; }    다 못 읽고 떠날 때 불린다. 결과는 객체여야 한다
```

- **이터러블 = `Symbol.iterator` 메서드를 가진 값.** 부르면 이터레이터를 돌려줘야 하고, **그것이 객체가 아니면 `TypeError`** 다.
- **이터레이터 = `next()` 를 가진 객체.** `next()` 는 **객체**를 돌려줘야 하고, 그 `done` 을 `ToBoolean` 으로 읽는다.
- ★★★ **모든 소비자는 `Symbol.iterator` 를 한 번 읽고 한 번 부른 뒤 `next()` 를 반복한다.** 끝까지 읽으면 `next` 는 **값 개수 + 1** 번이다.
- ★★★ **`return()` 은 소비자가 `done` 을 못 보고 멈출 때만 불린다** — `break`·`return`·몸통 `throw`·바깥 `continue`·패턴이 먼저 참·콜백 실패.
  **`next()` 자체가 던지면 안 불린다.**
- ★★ **`return` 은 없어도 된다.** 있으면 **함수여야** 하고, **원래 완료가 정상일 때만** 그 결과가 객체인지 검사한다.
- ★★ **`done: true` 와 같이 온 `value` 는 어떤 소비자도 쓰지 않는다.**
- ★★ **`for...of` 에는 대체 경로가 없다.** 유사 배열은 `Array.from` 을 거쳐야 한다.
- ★ **`for...of` 의 `null`/`undefined` 는 `TypeError`** 다. `for...in` 과 반대다(18번).

## 어디서 틀리나

### (1) ★★★ 「구조 분해는 필요한 만큼만 읽고 끝이다」로 믿는다

**읽는 것은 맞는데 끝이 아니다 — 닫는다.** `const [a, b, c] = it` 은 값이 **딱 셋이어도** `return()` 을 부른다.
★★ 그 이터레이터가 **파일 핸들이나 구독**을 쥔 것이면 `const [first] = stream` 한 줄이 **스트림을 닫는다.**
그 뒤에 같은 이터레이터로 「나머지를 읽겠다」는 코드는 이미 닫힌 것을 돌게 된다.
★ 반대로 **패턴이 값 개수보다 길면**(`[a, b, c, d]`) `done` 을 직접 받아 **닫지 않는다.** 경계가 **개수 하나**에 걸려 있다.

### (2) ★★★ 제너레이터나 `arr.values()` 를 「배열처럼 두 번 돌 수 있다」고 믿는다

**두 번째가 조용히 `[]` 다.** 에러도 경고도 없다.
★★ 흔한 자리 — **함수가 인자를 두 번 순회**한다(길이를 한 번 세고 값을 한 번 쓴다). 배열을 넘기면 되고 제너레이터를 넘기면 둘째가 빈다.
★ 처방 — 두 번 돌아야 하면 **받는 쪽에서 `Array.from(x)` 로 한 번 굳히거나**, 넘기는 쪽이 **이터러블(가게)** 을 넘긴다.
**`x[Symbol.iterator]() === x` 이면 한 번짜리**라는 판별식이 동작 (3)에 있다.

### (3) ★★★ 유사 배열에 `for...of` 를 쓴다

`{ length, 0, 1 }` 모양은 **`TypeError ... is not iterable`** 다. 파이썬의 `__getitem__` 대체 경로를 기대하면 여기서 막힌다.
★ `arguments` 처럼 **이터러블이기도 한 유사 배열**이 있어서 헷갈린다 — 그것은 **`Symbol.iterator` 를 따로 가졌기 때문**이다(동작 (2)의 `[5]`).
DOM 컬렉션은 **브라우저를 안 돌려서** 이 문서가 말하지 않는다. 판별은 언제나 `typeof x[Symbol.iterator] === "function"` 이다.

### (4) ★★ 「`is not iterable` 이면 문구로 원인을 안다」고 믿는다

**반만 맞다.** `Symbol.iterator` 가 함수가 아닐 때와 **`next` 가 아예 없을 때**가 **같은 문구**(`{(intermediate value)} is not iterable`)였다.
★★ 그리고 호출 스프레드는 **판마다 문구가 다르다**(v18 `Found non-callable @@iterator` 대 v20 `Spread syntax requires …`).
★ 문구로 grep 하는 테스트·알림 규칙은 **판이 오르면 깨진다.** 근거로 쓸 것은 **종류(`TypeError`)** 뿐이다.

### (5) ★★ `return()` 에 정리 코드를 두고 「언제나 불린다」고 믿는다

**끝까지 읽으면 안 불린다** — 끝은 `next()` 가 `done` 을 알려 준 것으로 충분하다고 본다.
★★ 그리고 **`next()` 가 던지면 안 불린다.** 정리가 **꼭** 필요하면 `next()` 안의 실패 경로에서도 스스로 정리해야 한다.
★ 제너레이터의 `try`/`finally` 가 그 자리를 어떻게 메우나는 [목록의 **20번 주제**](../20-generators/)가 정본이다.

### (6) ★★ `return()` 의 예외가 몸통의 예외를 덮는다고 믿는다

**반대다 — 몸통이 이긴다.** 몸통이 던진 뒤에는 `return()` 이 던지든 원시값을 주든 **몸통의 예외가 올라온다.**
★ 그런데 **`break` 로 정상 종료할 때는** `return()` 의 실패가 **그대로 올라온다**(`Error from return` · `TypeError Iterator result 1 is not an object`).
**같은 `return()` 이 원래 완료에 따라 보이기도 하고 묻히기도 한다.**

### (7) ★★ `Map` 이 객체처럼 정수 키를 앞세운다고 믿는다

**아니다.** `Map` 과 `Set` 은 **넣은 순서**다. 정수 같은 키를 앞세우는 것은 **객체의 `OrdinaryOwnPropertyKeys` 규칙**(13번)이다.
★ 그리고 **지웠다 다시 넣으면 맨 뒤**, **이미 있는 키에 `set` 은 자리 유지**다 — 「최신 순」 LRU 를 `Map` 으로 만들 때 이 둘을 헷갈리면 순서가 안 바뀐다.

### (8) ★★ 문자열의 `length` 를 「글자 수」로 쓴다

BMP 밖 글자 하나가 **`length` 로는 2, `for...of` 로는 1** 이다. 잘라 쓰면(`s[i]`) **서로게이트 반쪽**이 나온다.
★ 그러나 `[...s].length` 도 **사람이 보는 글자 수와 다르다** — `e` 에 결합 문자 하나를 붙이면 `[...e].length` 가 2 였다(동작 (2)의 `[7]`).

### (9) ★ 「`for...of` 는 느리니 인덱스 `for` 를 써라」를 근거 없이 옮긴다

★★★ **이 문서는 그 말을 하지 않는다 — 안 쟀기 때문이다.**
말할 수 있는 것은 **의미의 차이**뿐이다 — `for...of` 는 **코드 포인트 단위**로 돌고(문자열), **`return()` 으로 닫고**, **유사 배열을 거부한다.**
인덱스 `for` 는 그 셋을 하나도 안 한다. 속도는 **별도 측정이 필요한 다른 주장**이다.

## 구현 세부사항 대 언어 보장

### 명세 보장 — 어느 엔진에서도 같아야 하는 것

- ★★★ **소비자가 `Symbol.iterator` 를 읽어 부르고 `next()` 를 `done` 까지 반복하는 것**(`GetIterator` · `GetIteratorFromMethod` · `IteratorStep`).
- ★★★ **`done` 을 못 보고 멈추면 `IteratorClose` 로 `return` 을 찾아 부르는 것** — `for...of` 의 `break`·`return`·`throw`·바깥 `continue`.
- ★★★ **`next()` 가 던지면 닫지 않고 그 예외를 올리는 것.**
- ★★ **`return` 이 `undefined` 면 그냥 원래 완료** · **원래 완료가 throw 면 그것이 이긴다** · **아니면 `return()` 의 결과가 객체여야 한다**(`IteratorClose`).
- ★★ **`Symbol.iterator` 의 결과와 `next()` 의 결과가 객체가 아니면 `TypeError`** 인 것.
- ★★ **`done` 을 `ToBoolean` 으로 읽는 것** — 없으면 `false` · **`done` 이 참이면 그 결과의 `value` 를 읽지 않는 것**(`for...of`).
- ★★ **`for...in` 만 `null`/`undefined` 를 0회로 넘기고 `for...of` 는 `GetIterator` 에서 `TypeError`** 인 것(`ForIn/OfHeadEvaluation`).
- ★★ **`Map`·`Set` 이 삽입 순서로 돌고, 순회 중 추가를 방문하고, 아직 방문 안 한 삭제를 건너뛰는 것**(keyed collections 의 note).
- ★ **문자열 이터레이터가 코드 포인트 단위인 것.**
- ★ **배열 구조 분해가 딱 맞게 끝나도 닫는 것** — ★ 이 주제는 **배열 구조 분해 쪽 명세 문장을 받아 두지 않았다.** 로그로만 섰다.

### 엔진(V8) 구현 · 이 판의 관찰

- **예외 문구 전부** — `plain is not iterable` · `Spread syntax requires ...iterable[Symbol.iterator] to be a function`(v20) · `Found non-callable @@iterator`(v18) ·
  `object is not iterable (cannot read property Symbol(Symbol.iterator))` · `{(intermediate value)} is not iterable` ·
  `Result of the Symbol.iterator method is not an object` · `Iterator result 1 is not an object` · `Iterator value 10 is not an entry object` · `number 1 is not a function`.
  **종류(`TypeError`)만 명세가 정한다.**
- ★★ **`next` 가 없는 이터레이터를 「이터러블이 아니다」로 보고하는 것** — 명세의 `GetIteratorDirect` 는 "Let nextMethod be ? Get(obj, "next")." 로 **읽기만 하고 함수인지 안 본다.**
  그러니 명세상 실패는 **그것을 부르는 자리**에서 나는데, V8 은 그 실패를 `{(intermediate value)} is not iterable` 로 적는다. **어느 시점에 던졌는지는 로그를 안 심었다** — 문구만 관찰로 적는다.
- ★★ **문구에 변수 이름(`plain`)이 들어가는 것** — 소스 텍스트를 쓰는 V8 의 버릇이다. 식이 복잡하면 `{(intermediate value)}` 가 된다.
- ★ **이터레이터 헬퍼가 v18·v20 에 없는 것** — 명세 판(ES2025)보다 이 판들이 **먼저** 나왔기 때문이다. 판의 사정이지 언어 사실이 아니다.

### 호스트가 정하는 것 — ECMA-262 밖

- **이 주제의 블록에서 호스트가 정하는 칸은 없다.** 출력은 전부 `console.log` 에 **우리가 만든 문자열**만 넘겼다(`util.inspect` 의 표기를 싣지 않았다).
- ★ **DOM 컬렉션(`NodeList` 등)이 이터러블인지**는 **웹 호스트의 명세**가 정한다 — 이 배치는 브라우저를 **안 돌렸다.**

### 그래서 이렇게 적으면 틀린다

- 「`for...of` 는 끝나면 `return()` 을 부른다」 — **반대다.** 끝까지 가면 **안** 부른다. 못 끝나고 떠날 때 부른다.
- 「구조 분해는 필요한 만큼 읽을 뿐 부작용이 없다」 — **닫는다.** 딱 맞아도 닫는다.
- 「`return()` 은 정리 보장 장치다」 — **`next()` 가 던지면 안 불린다.** 보장이 아니다.
- 「유사 배열도 `for...of` 로 돈다」 — **아니다.** 대체 경로가 없다. `Array.from` 만 두 문을 가진다.
- 「`is not iterable` 문구로 원인을 안다」 — **문구는 V8 의 것이고 판마다 바뀌었다.**
- 「`Map` 도 정수 키가 앞선다」 — **아니다.** 삽입 순서다.
- 「`Promise.all` 은 비동기라 이터러블을 나중에 읽는다」 — **아니다.** 호출 안에서 동기로 다 읽었다.
- 「`for...of` 는 느리다」 — ★★★ **안 쟀다.**

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 쓴다 | 이유 |
|---|---|---|
| 배열·`Map`·`Set`·문자열을 값으로 돈다 | **`for...of`** | 같은 계약 하나로 다 된다. 중간에 멈추면 닫아 준다 |
| 문자열을 사람 쪽 단위에 가깝게 돈다 | **`for...of`** · `[...s]` | 코드 포인트 단위 — 서로게이트 반쪽이 안 나온다 |
| 유사 배열을 돈다 | **`Array.from(x)`** 뒤 `for...of` | `for...of` 에는 대체 경로가 없다 |
| 두 번 이상 돌아야 한다 | **이터러블(가게)** 을 넘기거나 `Array.from` 으로 굳힌다 | 이터레이터는 한 번짜리다 |
| 정리 코드가 필요한 순회 | `return()` + ★ **`next()` 안의 실패 경로도 따로** | `next()` 가 던지면 `return()` 이 안 불린다 |
| 키의 순서가 곧 의미다 | **`Map`** | 삽입 순서 보장 · 정수 키도 안 움직인다 |
| 객체의 키를 돈다 | `for...of Object.keys(o)` 류 | 평범한 객체는 이터러블이 아니다. `for...in` 은 체인을 탄다(18번) |

- **안 쓸 자리** — **유사 배열에 직접 `for...of`** · **한 번짜리 이터레이터를 두 번 돌기** · **`return()` 하나에 정리를 전부 맡기기** · **예외 문구로 분기하기.**

## 핵심 문장

1. ★★★ **`for...of`·스프레드·`Array.from`·`new Set`·배열 구조 분해·`Promise.all` 은 같은 세 마디를 부른다** — `Symbol.iterator` 를 한 번 읽고 한 번 부르고, `next()` 를 `done` 까지.
   **값으로는 원리상 못 가른다** — 로그만이 말한다.
2. ★★★ **`return()` 은 「`done` 을 못 보고 떠날 때」만 불린다.** 끝까지 읽으면 안 부르고, `next()` 가 던져도 안 부른다.
   **`[a, b, c]` 는 딱 셋이어도 닫고, `[a, b, c, d]` 는 닫지 않는다.**
3. ★★★ **이터러블은 매번 새 이터레이터를 주고, 이터레이터는 한 번짜리다.** 제너레이터·배열 이터레이터·`m.keys()` 는 `it[Symbol.iterator]() === it` 인 쪽이라 두 번째가 `[]` 다.
4. ★★★ **JS 의 `for...of` 에는 파이썬의 `__getitem__` 같은 대체 경로가 없다** — 유사 배열은 `TypeError` 이고, 두 문을 가진 것은 `Array.from` 뿐이다.
5. ★★ **「이터러블이 아니다」는 종류가 `TypeError` 로 하나지만 문구는 자리마다·판마다 다르다** — 호출 스프레드가 v18 과 v20 에서 갈린 것이 11번과 같은 자리다.

## 관련 자료

- [11 — 스프레드와 나머지](../11-spread-and-rest/2-summary.md) — ★★★ **그쪽이 「세 자리의 문」(`apply`·스프레드·`Array.from`)의 정본**이다. 여기는 **그 문 뒤의 프로토콜 자체**부터.
- [10 — 구조 분해 할당](../10-destructuring-assignment/2-summary.md) — **그쪽이 패턴 문법의 정본**이다. 여기는 **배열 패턴이 이터레이터를 언제 닫나**까지.
- [04 — 문자열과 UTF-16](../04-strings-and-utf16/2-summary.md) — **그쪽이 코드 유닛·서로게이트의 정본**이다. 여기는 **문자열 이터레이터가 그 쌍을 합친다**는 사실까지.
- [13 — 객체 리터럴과 프로퍼티](../13-object-literals-and-properties/2-summary.md) — **그쪽이 객체 키 순서(정수 키 우선)의 정본**이다. 여기는 **`Map` 이 그 규칙을 안 따른다**는 대비까지.
- [18 — `for...in` 과 열거](../18-for-in-and-enumeration/2-summary.md) — **그쪽이 열거의 정본**이다. 여기는 **`null` 앞에서 둘이 반대로 군다**는 대비만.
- [목록의 **20번 주제**](../20-generators/) 「제너레이터」 — **그쪽이 `yield`·`next(값)`·`return`·`throw` 의 흐름 정본**이다. 여기는 **제너레이터 객체가 자기 자신을 돌려준다**까지.
- [목록의 **21번 주제**](../21-iterator-helpers/) 「이터레이터 헬퍼」 — ES2025. **이 두 판에는 없었다.**
- [목록의 **22번 주제**](../22-symbol-and-well-known-symbols/) 「`Symbol` 과 잘 알려진 심볼」 — **그쪽이 `Symbol.iterator` 를 포함한 잘 알려진 심볼 전체의 정본**이다.
- [목록의 **23번 주제**](../23-map-set-and-weak-collections/) 「`Map`·`Set` 과 약한 컬렉션」 — **그쪽이 키 비교(SameValueZero)와 컬렉션 선택의 정본**이다. 여기는 **순서와 순회 중 변경**까지.
- 목록의 **38번 주제** 「Promise 조합기」 — `Promise.all` 의 나머지. 여기는 **이터러블을 동기로 읽는다**까지.
- 목록의 **40번 주제** 「비동기 이터레이션」 — `for await...of` · `Symbol.asyncIterator`. 여기는 **동기 프로토콜**까지.
- Python 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **16번**·**32번** —
  ★★★ **이 주제의 대비축.** 16번이 `__iter__`/`__next__`/`StopIteration` 의 정본이고, 32번이 **`__getitem__` 대체 경로**를 로그로 찍었다. **JS 에는 그 경로가 없다.**

## 용어 풀이

- **이터러블(iterable)** — `Symbol.iterator` 메서드를 가진 값. 부르면 이터레이터를 준다.
- **이터레이터(iterator)** — `next()` 를 가진 객체. 선택으로 `return()` 을 가진다.
- **이터레이터 결과(iterator result)** — `next()` 가 돌려주는 `{ value, done }` 객체.
- **`Symbol.iterator`** — 「나를 돌리는 법」을 담는 잘 알려진 심볼 키. 명세 표기로는 `@@iterator` 다.
- **소비자(consumer)** — 이터러블을 받아 `next()` 를 부르는 쪽. `for...of`·스프레드·`Array.from` 등.
- **`IteratorClose`** — 조기 종료 때 `return` 을 찾아 부르는 추상 연산.
- **조기 종료(early exit)** — `done` 을 받기 전에 소비자가 멈추는 것.
- **자기 자신을 돌려주는 이터레이터** — `it[Symbol.iterator]() === it` 인 것. 한 번만 돈다.
- **유사 배열(array-like)** — `length` 와 정수 키를 가졌지만 `Symbol.iterator` 는 없을 수 있는 객체.
- **코드 포인트 / 코드 유닛** — 유니코드의 번호 하나 / UTF-16 의 16비트 조각 하나. BMP 밖 글자는 코드 유닛 둘(서로게이트 쌍)이다.
- **삽입 순서(insertion order)** — `Map`·`Set` 이 도는 순서. 넣은 순서 그대로다.
- **`__getitem__` 대체 경로(파이썬)** — `__iter__` 가 없을 때 0번부터 `IndexError` 까지 인덱스로 도는 옛 프로토콜. **JS 에는 없다.**

## 더 들어가면

- **`return()` 이 왜 「선택」이고 `next()` 가 던질 때는 왜 안 부르나** — 한 문장으로 모인다.
  **닫기는 「멀쩡한 이터레이터에게 더 안 읽겠다고 알리는 일」이다.** 끝까지 읽었으면 알릴 것이 없고, 이터레이터가 고장 났으면 알릴 상대가 없다.
  ★ 이 해석은 로그 17줄과 명세의 `?` 위치에서 **거꾸로 읽어 낸 것**이다 — 명세가 이 문장을 쓰지는 않는다.
- **배열 구조 분해가 「딱 맞을 때」 닫는 것은 게으름의 대가다.** 넷째 `next` 를 불러 확인하면 안 닫아도 되지만, 그러면 **필요 없는 값 하나를 더 만든다** —
  끝없는 이터레이터에서 `[a]` 가 `next` 한 번으로 멈춘 것(동작 (2)의 `[6]`)이 이 선택의 이득이다.
  ★ 「그래서 그렇게 정했다」는 **설계 의도는 해석**이다. 로그가 보이는 것은 **멈춘다는 사실**까지다.
- **`Promise.all` 이 동기로 다 읽는다는 사실은 「지연 시퀀스」와 부딪친다.** 끝없는 제너레이터를 넘기면 **호출이 돌아오지 않는다**는 결론이 따라 나오지만,
  **돌려 보지 않았다.** 지연 시퀀스는 [목록의 **20번 주제**](../20-generators/), 스트림 소비는 **40번 주제** 쪽이다.
- **이터레이터 헬퍼(ES2025)** 는 이 계약 위에 `map`·`filter`·`take` 를 **지연으로** 얹는다. 이 두 판에는 없어서 **이 문서가 아무것도 말하지 않는다**([목록의 **21번 주제**](../21-iterator-helpers/)).
