# js/syntax/06 — 스코프와 클로저: 「이 함수는 어느 칸을 몇 개 붙들고 있나」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262 최신 초안](https://tc39.es/ecma262/) — 환경 레코드·함수 환경·`for` 문의 회차별 환경
> - [ECMA-262 판별 아카이브](https://262.ecma-international.org/) — 블록 스코프와 회차별 바인딩이 들어온 판(ES2015)을 가릴 때
> - [MDN — Closures](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Closures) · [MDN — `for`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/for)
>
> ★★★ **명세 조항 번호는 인용하지 않는다.** 규칙 진술은 위 문서로, **값·예외 타입과 메시지는 전부 실행으로** 접지했다.
>
> **실행 검증** — 이 문서의 모든 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮겨 적은 출력이 하나도 없다).
> 배너의 `node20` 은 `~/.nvm/versions/node/v20.19.6/bin/node`, `node18` 은 기본 PATH 의 `node`(v18.19.1)다.
> **어느 판에서 나왔는지는 아래 첫 블록**에 있다.

```sh
// js06b-versions.sh
#!/usr/bin/env bash
# 이 문서의 모든 출력이 어느 판에서 나왔는지 -- 첫 블록에 싣는다.
set -u -o pipefail
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
for n in "$N18" "$N20"; do
  "$n" -e 'const v = process.versions;
    console.log("node " + v.node + "  v8 " + v.v8 +
                "  strict-this " + String((function(){ "use strict"; return this; })()) +
                "  globalThis " + Object.prototype.toString.call(globalThis) +
                "  arrow-proto " + Object.prototype.hasOwnProperty.call(() => {}, "prototype") +
                "  class-fields " + typeof (new (class { f = 1 })()).f);'
done
google-chrome --version 2>/dev/null
```

```text
===== ./js06b-versions.sh (exit=0) =====
node 18.19.1  v8 10.2.154.26-node.28  strict-this undefined  globalThis [object global]  arrow-proto false  class-fields number
node 20.19.6  v8 11.3.244.8-node.33  strict-this undefined  globalThis [object global]  arrow-proto false  class-fields number
Google Chrome 151.0.7922.173 
```

> ★★ **던지는 형태를 하나로 고정했다** — 예외는 `try`/`catch` 로 받아 **`e.constructor.name` 과 `e.message` 만** 찍는다.
> Node 의 스택트레이스에는 **절대 경로**가 박혀 다른 머신에서 재현이 안 되기 때문이다.
> 그래서 이 주제의 블록에는 **표준 오류가 한 줄도 섞이지 않는다** — 전부 표준 출력이다.
> ★★ **`padEnd` 격자의 라벨은 전부 ASCII 다.** 한글은 터미널에서 두 칸이라 칸이 어긋난다.
>
> **버전** — 클로저(함수가 바깥 이름을 붙드는 것)는 **초판부터**다.
> **블록 스코프와 「`for` 회차마다 새 바인딩」은 ES2015** 다. `WeakRef` 는 **ES2021** 이고 6번 절에서만 쓴다.
> 이 주제에는 **시각·로캘·난수가 닿는 칸이 하나도 없다.**
>
> **★ 이 주제가 쓰는 창 — 그리고 부적용인 창**
>
> | 창 | 이 주제에서 무엇을 보나 |
> |---|---|
> | ★★★ **쓰기 탐침**(한 함수로 쓰고 나머지로 읽는다) | **서로 다른 변수가 몇 개인가** — 이 주제의 본체 |
> | 값 읽기(`[3,3,3]` 대 `[0,1,2]`) | 증상. **원인은 아니다** |
> | `WeakRef` + `--expose-gc` | 잡은 것이 **수거됐나 아직 살아 있나**(6번 절에서만) |
> | ★ **부적용** — 파이썬의 `__closure__`·`cell_contents` 같은 속 보기 | **JS 에는 없다.** 잡힌 변수에 손잡이가 없어 **잴 것이 없다** |
> | ★ **부적용** — `const` 로 잡은 칸의 쓰기 탐침 | **쓰기가 거부된다.** 안 잰 것이 아니라 **잴 수 없는 것**이라 `n/a` 로 찍는다 |
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | Node 스택트레이스의 **절대 경로** — 한 줄도 싣지 않았다 | ★★★ **서로 다른 변수 개수**(1 대 3) · 어느 함수가 어느 무리인가 |
> | 예외 **문구**(판이 오르면 바뀐다) | ★★★ **예외의 종류** — `ReferenceError`·`TypeError` |
> | ★ GC 가 **언제** 도는가 — 명세가 정하지 않는다 | ★★ 같은 판·같은 소스의 **출력 값**과 종료 코드 |
> | 최상위 `this` 가 무엇이냐(호스트 사정) | ★★ **수거됐나 살아 있나**(이 판에서 6회 전부 같았다 — 그래도 관찰이다) |
>
> ★★ **이 주제의 블록에는 주소도 시간도 난수도 한 곳도 안 찍힌다.** 같은 판에서 다시 돌리면 **한 글자도 안 변한다**(재대조 54블록 전부 동일).
>
> **선행** — [05 — `var`·`let`·`const` 와 TDZ](../05-var-let-const-and-tdz/2-summary.md).
> ★★★ 거기 4번 절이 `[3,3,3]` 대 `[0,1,2]` 를 **값으로** 보였고, **「칸이 몇 개냐」는 여기서 센다.**
> 블록 스코프·TDZ·`const` 의 규칙은 **전부 그쪽이 정본**이다 — 여기서는 결론만 쓰고 링크한다.
> **이어지는 곳** — 목록의 **07번 주제** 「`this` 바인딩 네 규칙」 · 목록의 **08번 주제** 「함수 정의 형태와 매개변수」
>
> ★★ **경계 — `this` 는 여기가 아니다.** **`this` 는 스코프로 안 찾는다** — 호출식이 정한다.
> 그 규칙은 07번의 것이고, 여기서 다루는 것은 **이름**뿐이다.

## 한눈에 — 쉽게 말하면

**함수는 「값을 복사해 나오는」 것이 아니라 「자기가 태어난 자리로 가는 길」을 들고 나온다.**

- 함수를 만들면 그 자리에 있던 **이름들이 사는 방**이 함수에 딸려 붙는다.
- 나중에 그 함수를 부르면, 모르는 이름은 **그 방부터 시작해 바깥으로 올라가며** 찾는다.
- **부른 자리는 아무 상관이 없다.** 어디서 불러도 답이 같다.
- 그래서 그 방의 값을 누가 바꿔 놓으면 **바뀐 것이 나온다.** 값이 아니라 **칸**을 붙들었기 때문이다.

```text
   function makeReader() {        <- 방이 하나 생긴다
     const where = "inside";         [ where | "inside" ]
     return () => where;          <- 이 함수가 그 방으로 가는 길을 들고 나간다
   }

   const r = makeReader();        <- makeReader 는 끝났다
   r()                            <- 그래도 방은 살아 있다 -> "inside"

   ★ 방이 살아 있는 이유는 하나뿐이다 — r 이 그 방을 붙들고 있기 때문이다.
```

**그리고 이 주제의 본론은 「방이 몇 개냐」다.**

```text
   for (var i = 0; i < 3; i++)          for (let i = 0; i < 3; i++)

   방 하나를 셋이 나눠 쓴다               회차마다 방이 새로 생긴다
   +------------------+                 +-----+  +-----+  +-----+
   |   i              |                 | i=0 |  | i=1 |  | i=2 |
   +------------------+                 +-----+  +-----+  +-----+
     ^   ^   ^                             ^        ^        ^
     f0  f1  f2                            f0       f1       f2

   f0 으로 써 보면 f1·f2 도 바뀐다        f0 으로 써도 f1·f2 는 그대로다
   -> 서로 다른 변수 1개                  -> 서로 다른 변수 3개
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 방 | 한 스코프의 이름들이 사는 자리 | 그 안의 이름을 읽어 본다 |
| 방으로 가는 길 | 클로저가 붙든 것 | 바깥 함수가 끝난 뒤에도 읽힌다 |
| 방 안의 칸 하나 | 바인딩(변수 하나) | ★ **쓰기 탐침** — 하나로 쓰고 나머지로 읽는다 |
| 방이 몇 개냐 | 회차마다 바인딩이 새로 생기나 | ★ 「서로 다른 변수 개수」 |
| 길을 따라 올라간다 | 스코프 체인 조회 | 안쪽에 없으면 바깥에서 찾는다 |
| 길이 하나라도 남아 있으면 방이 안 치워진다 | 클로저가 메모리를 붙드는 것 | `WeakRef` 로 수거 여부만 본다 |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 하나로 굳어 있다.
`for (var i = 0; ...)` 로 버튼 열 개에 핸들러를 달았더니 **전부 마지막 인덱스**를 쓰는 사고가 그것이고,
큰 응답 객체 한 줄만 쓰는 작은 콜백이 **응답 전체를 캐시에 붙들고 있는** 사고가 그것이다.
**둘 다 「이 함수가 어느 방을 붙들고 있나」 한 문장이 답이다.**

> **스코프(scope)** — 어떤 이름이 통하는 구역.
> 예: 함수 몸통 하나, `{ }` 블록 하나. JS 는 **`var` 만 함수 구역**이고 나머지는 블록 구역이다(05번).

> **클로저(closure)** — 함수 + 그 함수가 태어난 자리의 스코프를 **함께 묶은 것**.
> 예: `makeCounter()` 가 돌려준 함수는 자기 코드와 바깥의 `n` 을 함께 들고 다닌다.

> **렉시컬 스코프(lexical scope)** — 이름을 **소스에 적힌 자리** 기준으로 찾는 것. 「정적 스코프」라고도 한다.
> 예: 함수를 어디서 부르든 답이 같다. 반대는 **동적 스코프** — 부른 쪽의 이름이 보이는 것인데, **JS 는 아니다.**

## 이 주제가 답하려는 질문

1. **이름은 어디서 찾나** — 정의된 자리인가 부른 자리인가. 그리고 그 답이 왜 클로저를 만드나.
2. **루프에서 만든 함수 셋이 왜 같은 값을 내나** — 「나중에 읽어서」인가, 「**애초에 칸이 하나여서**」인가. 그것을 **무엇으로 증명하나.**
3. **클로저는 무엇을 살려 두나** — 값인가 칸인가. 그리고 그것이 메모리에 무슨 뜻인가.

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 문장으로 읽는다.

### (1) ★★ 이름은 정의된 자리에서 바깥으로 올라가며 찾는다

**언제 쓰나** — 「이 안에서 `x` 라고 쓰면 어느 `x` 인가」를 물을 때. 모든 클로저 이야기의 출발점이다.

```text
   module                                호출은 아래에서 하는데
   +---------------------------+          찾기는 위로 올라간다
   | where = "module"          |
   |  outer()                  |
   |  +----------------------+ |          inner() 안에서 where 를 읽으면
   |  | where = "outer"      | |            inner 방   -> 없다
   |  |  middle()            | |            middle 방  -> 없다
   |  |  +-----------------+ | |            outer 방   -> 있다  "outer"
   |  |  | inner()         | | |          -> 모듈까지 안 올라간다
   |  |  |  return where   | | |
   |  |  +-----------------+ | |
   |  +----------------------+ |
   +---------------------------+
```

```js
// js06b-06a-lexical-scope.js
// 이름을 어디서 찾나 — 정의된 자리인가 부른 자리인가.
// 라벨은 전부 ASCII 다 — 한글을 padEnd 격자에 넣으면 칸이 어긋난다.
function probe(label, run) {
  let r;
  try { r = JSON.stringify(run()); }
  catch (e) { r = e.constructor.name + ": " + e.message; }
  console.log("  " + label.padEnd(36) + " -> " + r);
}

const where = "module";

console.log("[1] 이름은 정의된 자리에서 바깥으로 올라가며 찾는다");
function outer() {
  const where = "outer";
  function middle() {
    function inner() { return where; }
    return inner();
  }
  return middle();
}
probe("inner() finds it in outer", outer);
probe("no local at all -> module level", () => { function f() { return where; } return f(); });
probe("missing name", () => { function f() { return nowhere; } return f(); });

console.log("");
console.log("[2] 부른 자리의 지역 변수는 안 보인다 -- 동적 스코프가 아니다");
function readsWhere() { return where; }
function callerWithOwn() { const where = "caller"; return readsWhere(); }
probe("caller has its own `where`", callerWithOwn);

console.log("");
console.log("[3] 정의된 자리가 다르면 같은 소스라도 답이 다르다");
function makeReader() { const where = "inside makeReader"; return () => where; }
probe("reader defined inside", () => makeReader()());
probe("reader defined outside", () => (() => where)());

console.log("");
console.log("[4] 스코프 체인은 몇 겹이든 올라간다 -- 가장 가까운 것이 이긴다");
function depth() {
  const seen = [];
  const n = "L0";
  { const n = "L1"; { const n = "L2"; { seen.push(n); } } }
  { const n = "L1b"; seen.push(n); }
  seen.push(n);
  return seen;
}
probe("nearest wins at each level", depth);

console.log("");
console.log("[5] 함수 몸통은 자기 스코프를 만들고 블록도 만든다");
probe("block does not leak let", () => { { let b = 1; } return typeof b; });
probe("function does not leak var", () => { function f() { var v = 1; } f(); return typeof v; });
probe("inner sees outer, not the reverse", () => {
  const outerName = "o";
  function f() { const innerName = "i"; return outerName + innerName; }
  return [f(), typeof innerName];
});
```

```text
===== node20 js06b-06a-lexical-scope.js (exit=0) =====
[1] 이름은 정의된 자리에서 바깥으로 올라가며 찾는다
  inner() finds it in outer            -> "outer"
  no local at all -> module level      -> "module"
  missing name                         -> ReferenceError: nowhere is not defined

[2] 부른 자리의 지역 변수는 안 보인다 -- 동적 스코프가 아니다
  caller has its own `where`           -> "module"

[3] 정의된 자리가 다르면 같은 소스라도 답이 다르다
  reader defined inside                -> "inside makeReader"
  reader defined outside               -> "module"

[4] 스코프 체인은 몇 겹이든 올라간다 -- 가장 가까운 것이 이긴다
  nearest wins at each level           -> ["L2","L1b","L0"]

[5] 함수 몸통은 자기 스코프를 만들고 블록도 만든다
  block does not leak let              -> "undefined"
  function does not leak var           -> "undefined"
  inner sees outer, not the reverse    -> ["oi","undefined"]
```

그림 해설 (한 단계씩).

- ★★★ **부른 자리의 지역 변수는 안 보인다.** `callerWithOwn` 이 자기 `where = "caller"` 를 두고 `readsWhere()` 를 불렀는데 답은 `"module"` 이다.
  **이것이 「렉시컬」의 전부**다 — 함수가 무엇을 볼지는 **소스에 적힌 자리**가 정하고, 실행 중에 바뀌지 않는다.
- ★★★ **그래서 클로저가 성립한다.** 정의된 자리가 정해져 있으니 **그 자리를 붙들어 두기만 하면** 나중에 어디서 불러도 답이 같다.
  `[3]` 의 두 줄이 그 대비다 — 같은 `() => where` 인데 **안에서 만든 것**과 **밖에서 만든 것**의 답이 다르다.
- ★★ **가장 가까운 것이 이긴다.** `[4]` 가 `["L2","L1b","L0"]` 다. 세 겹을 들어가면 `L2`, 형제 블록에서는 `L1b`, 다 나오면 `L0` 다.
- ★★ **안쪽은 바깥을 보지만 바깥은 안쪽을 못 본다.** `[5]` 의 마지막 줄이 `["oi","undefined"]` — 길이 **한 방향**이다.
- ★ **없는 이름은 `ReferenceError: nowhere is not defined`** 다. 「칸이 아예 없다」는 뜻이고, 「있는데 잠겼다」와 문구가 다르다([05번](../05-var-let-const-and-tdz/2-summary.md)).

**비용** — 렉시컬이라서 **읽는 사람이 소스만 보고 판정**할 수 있다. 대신 **바깥 이름을 실수로 잡기 쉽다** —
그 실수가 2번 절의 루프 사고이고, 이름을 안 잡으려면 **일부러 새 이름을 만들어야** 한다.

### (2) ★★★ 루프 클로저 — 값이 아니라 「서로 다른 변수 개수」로 가른다

**언제 쓰나** — 이 주제의 핵심. 「나중에 읽어서 그렇다」에서 「**애초에 칸이 하나여서 그렇다**」로 넘어갈 때.

[05번 4번 절](../05-var-let-const-and-tdz/2-summary.md)이 이 자리를 **값으로** 보였다 — `[3,3,3]` 대 `[0,1,2]`.
**그런데 값은 증상이다.** 「나중에 읽어서 덮어써졌다」는 설명은 증상의 절반만 말한다 —
**칸이 셋이었다면 나중에 읽어도 `0 1 2` 가 나왔을 것**이기 때문이다.

문제는 JS 에는 **잡힌 변수에 손잡이가 없다**는 것이다.
파이썬은 `함수.__closure__[0]` 으로 셀을 꺼내고, Go 는 `&i` 로 포인터를 찍는다. **JS 에는 둘 다 없다.**

```text
   그래서 「개수」를 쓰기로 센다 — 쓰기 탐침

   함수마다 읽기 짝과 쓰기 짝을 만든다
     fn0 = { get: () => i, set: v => { i = v } }
     fn1 = { get: () => i, set: v => { i = v } }
     fn2 = { get: () => i, set: v => { i = v } }

   fn0.set("probe-0")  하고 나서 셋을 전부 읽는다
     같이 바뀐 것들  -> 같은 칸을 본다  (한 무리)
     안 바뀐 것들    -> 다른 칸을 본다  (다음 무리)

   무리의 개수 = 서로 다른 변수 개수.   ★ 주소를 한 번도 안 쓴다.
```

```js
// js06b-06b-box-count.js
// 루프 클로저를 「값」이 아니라 「서로 다른 변수 개수」로 가른다.
// JS 에는 파이썬의 __closure__ 도 Go 의 포인터도 없다 -- 잡힌 변수에 손잡이가 없다.
// 그래서 개수를 **쓰기 탐침**으로 센다: 한 함수로 써서 다른 함수의 읽기가 따라 바뀌면 같은 변수다.
// 라벨은 전부 ASCII 다.

// 쓰기 탐침 -- handles[a] 로 써서 값이 따라 바뀐 것들을 한 무리로 묶는다.
// 무리의 개수가 곧 「서로 다른 변수 개수」다. 주소를 한 번도 안 쓴다.
// ★ 쓰기가 아예 안 먹는 경우(const)는 세지 않고 "n/a" 로 돌려준다 -- 잴 것이 없는 것과 안 잰 것은 다르다.
function countBoxes(handles) {
  const group = new Array(handles.length).fill(-1);
  let boxes = 0;
  for (let a = 0; a < handles.length; a++) {
    if (group[a] !== -1) continue;
    const mark = "probe-" + a;
    handles[a].set(mark);
    if (handles[a].get() !== mark) return { boxes: "n/a", group: "write refused" };
    for (let b = a; b < handles.length; b++) {
      if (group[b] === -1 && handles[b].get() === mark) group[b] = boxes;
    }
    boxes += 1;
  }
  return { boxes, group: JSON.stringify(group) };
}

const builders = [
  ["for (var i)", () => { const h = []; for (var i = 0; i < 3; i++) h.push({ get: () => i, set: (v) => { i = v; } }); return h; }],
  ["for (let i)", () => { const h = []; for (let i = 0; i < 3; i++) h.push({ get: () => i, set: (v) => { i = v; } }); return h; }],
  ["var + IIFE", () => { const h = []; for (var i = 0; i < 3; i++) (function (j) { h.push({ get: () => j, set: (v) => { j = v; } }); })(i); return h; }],
  ["var + let copy in body", () => { const h = []; for (var i = 0; i < 3; i++) { let j = i; h.push({ get: () => j, set: (v) => { j = v; } }); } return h; }],
  ["for (let x of ...)", () => { const h = []; for (let x of [0, 1, 2]) h.push({ get: () => x, set: (v) => { x = v; } }); return h; }],
  ["for (const x of ...)", () => { const h = []; for (const x of [0, 1, 2]) h.push({ get: () => x, set: (v) => { try { x = v; } catch (e) { return e; } } }); return h; }],
  ["while + let outside", () => { const h = []; let i = 0; while (i < 3) { h.push({ get: () => i, set: (v) => { i = v; } }); i++; } return h; }],
  ["while + let inside", () => { const h = []; let i = 0; while (i < 3) { let j = i; h.push({ get: () => j, set: (v) => { j = v; } }); i++; } return h; }],
  ["factory make(i)", () => { const make = (j) => ({ get: () => j, set: (v) => { j = v; } }); const h = []; for (var i = 0; i < 3; i++) h.push(make(i)); return h; }],
];

console.log("[1] 함수는 늘 셋이다 -- 갈리는 것은 그 셋이 보는 변수의 개수다");
console.log("  " + "how the loop declares".padEnd(24) + "fns".padEnd(5) + "boxes".padEnd(7) + "which box".padEnd(15) + "read");
console.log("  " + "-".repeat(24) + "-".repeat(5) + "-".repeat(7) + "-".repeat(15) + "-".repeat(9));
for (const [label, build] of builders) {
  const read = JSON.stringify(build().map((h) => h.get()));
  const n = build().length;
  const { boxes, group } = countBoxes(build());
  console.log("  " + label.padEnd(24) + String(n).padEnd(5) + String(boxes).padEnd(7) + group.padEnd(15) + read);
}

console.log("");
console.log("[2] 탐침이 무엇을 했는지 한 짝만 펼쳐 본다");
function pair(label, build) {
  const h = build();
  const before = h.map((x) => x.get());
  h[0].set("WRITTEN");
  const after = h.map((x) => x.get());
  console.log("  " + label.padEnd(14) + " before " + JSON.stringify(before).padEnd(12) +
              " after writing through fn0 " + JSON.stringify(after));
}
pair("for (var i)", builders[0][1]);
pair("for (let i)", builders[1][1]);

console.log("");
console.log("[3] const 줄은 쓰기 탐침이 부적용이다 -- 그 자리는 for (let x of) 로 잰다");
const constHandles = builders[5][1]();
let what;
const thrown = constHandles[0].set("x");
what = thrown ? thrown.constructor.name + ": " + thrown.message : "no error";
console.log("  writing through a `const` handle -> " + what + ", still reads " + JSON.stringify(constHandles[0].get()));
```

```text
===== node20 js06b-06b-box-count.js (exit=0) =====
[1] 함수는 늘 셋이다 -- 갈리는 것은 그 셋이 보는 변수의 개수다
  how the loop declares   fns  boxes  which box      read
  ------------------------------------------------------------
  for (var i)             3    1      [0,0,0]        [3,3,3]
  for (let i)             3    3      [0,1,2]        [0,1,2]
  var + IIFE              3    3      [0,1,2]        [0,1,2]
  var + let copy in body  3    3      [0,1,2]        [0,1,2]
  for (let x of ...)      3    3      [0,1,2]        [0,1,2]
  for (const x of ...)    3    n/a    write refused  [0,1,2]
  while + let outside     3    1      [0,0,0]        [3,3,3]
  while + let inside      3    3      [0,1,2]        [0,1,2]
  factory make(i)         3    3      [0,1,2]        [0,1,2]

[2] 탐침이 무엇을 했는지 한 짝만 펼쳐 본다
  for (var i)    before [3,3,3]      after writing through fn0 ["WRITTEN","WRITTEN","WRITTEN"]
  for (let i)    before [0,1,2]      after writing through fn0 ["WRITTEN",1,2]

[3] const 줄은 쓰기 탐침이 부적용이다 -- 그 자리는 for (let x of) 로 잰다
  writing through a `const` handle -> TypeError: Assignment to constant variable., still reads 0
```

그림 해설.

- ★★★ **함수 개수는 늘 3 이고 변수 개수만 갈린다.** `for (var i)` 는 **1**, `for (let i)` 는 **3** 이다.
  ★★ 그래서 답은 「나중에 읽어서」가 아니라 「**애초에 칸이 하나여서**」다. `[2]` 가 그 장면을 펼쳐 보인다 —
  `fn0` 으로 한 번 썼더니 `var` 판은 `["WRITTEN","WRITTEN","WRITTEN"]`, `let` 판은 `["WRITTEN",1,2]` 다.
- ★★★ **`while` 이 반례다.** `while + let outside` 는 `let` 을 썼는데도 **변수 1개**에 읽기가 `[3,3,3]` 이다.
  ★★ **그러니 「`let` 이 고친다」는 부정확하다** — 고치는 것은 **`for` 헤더의 `let`** 이다(3번 절이 그것만 따로 본다).
- ★★ **IIFE 와 몸통의 `let` 과 팩토리가 전부 같은 답을 낸다** — 셋 다 **변수 3개**다.
  ★ 「옛날 고침(IIFE)」과 「지금 고침(`let`)」이 **같은 일**을 한다는 것이 이 표의 값어치다. 4번 절이 그 대비를 편다.
- ★ **`for (const x of ...)` 줄만 `n/a`** 다. `const` 는 **쓰기가 거부되어 탐침이 성립하지 않는다.**
  ★★ **이것은 「안 쟀다」가 아니라 「잴 것이 없다」는 뜻**이므로 그렇게 찍었다. `[3]` 이 그 거부를 출력으로 보인다 —
  `TypeError: Assignment to constant variable.` 그리고 **같은 자리는 바로 위의 `for (let x of ...)` 줄이 잰다**(변수 3개).

**비용** — 쓰기 탐침은 **읽기 짝과 쓰기 짝을 둘 다 만들어야** 성립한다. 실제 코드에는 읽기만 있는 경우가 많다.
대신 **주소도 시각도 안 쓰므로 재대조에서 한 글자도 안 흔들린다** — 「개수」는 「주소」와 달리 안 흔들리는 칸이다.

### (3) ★★★ `for` 헤더의 `let` 이 회차마다 무엇을 하나 — 관찰로만

**언제 쓰나** — 「회차마다 새 바인딩」이라는 말을 **명세 용어 없이** 확인하고 싶을 때.

```text
   for (let i = 0; i < 3; i++) { ... }

   회차 0  [ i=0 ] --값을 베껴 넘긴다--> 회차 1  [ i=1 ] --베껴 넘긴다--> 회차 2  [ i=2 ]
             ^                                    ^                              ^
             f0 가 이 칸을 본다                    f1                             f2

   ★ 칸은 새것인데 값은 이어진다 — 두 사실을 따로 확인해야 한다.
     ① 새것이다   : f0 으로 써도 f1 이 안 바뀐다
     ② 이어진다   : 몸통에서 i 를 바꾸면 다음 회차의 시작값이 바뀐다
```

```js
// js06b-06c-per-iteration.js
// for 헤더의 let 이 회차마다 새 칸을 만드는 것을 명세 용어 없이 관찰로 보인다.
// 창은 넷이다: ① 쓰기 탐침 ② 값이 이어지나 ③ 회차 안에서 쓰면 다음 회차가 보나 ④ 어느 문법이 그 일을 하나
function probe(label, run) {
  let r;
  try { r = JSON.stringify(run()); }
  catch (e) { r = e.constructor.name + ": " + e.message; }
  console.log("  " + label.padEnd(40) + " -> " + r);
}

console.log("[1] 칸이 새로 생겼다는 것 -- 한 회차에서 쓴 값이 다른 회차에 안 번진다");
probe("let: write in fn0 leaks to fn1?", () => {
  const set = [], get = [];
  for (let i = 0; i < 3; i++) { set.push((v) => { i = v; }); get.push(() => i); }
  set[0]("X");
  return get.map((g) => g());
});
probe("var: write in fn0 leaks to fn1?", () => {
  const set = [], get = [];
  for (var i = 0; i < 3; i++) { set.push((v) => { i = v; }); get.push(() => i); }
  set[0]("X");
  return get.map((g) => g());
});

console.log("");
console.log("[2] 그런데 값은 이어진다 -- 새 칸이 앞 회차의 값을 받아 온다");
probe("body sets i = 1 on the first pass", () => {
  const seen = [];
  for (let i = 0; i < 3; i++) { seen.push(i); if (i === 0) i = 1; }
  return seen;
});
probe("same with var", () => {
  const seen = [];
  for (var i = 0; i < 3; i++) { seen.push(i); if (i === 0) i = 1; }
  return seen;
});

console.log("");
console.log("[3] 회차 안에서 바꾼 값이 그 회차의 클로저에 남는다");
probe("let: change i after pushing the fn", () => {
  const fns = [];
  for (let i = 0; i < 3; i++) { fns.push(() => i); i += 10; }
  return fns.map((f) => f());
});
probe("how many passes did it make", () => {
  let count = 0;
  for (let i = 0; i < 3; i++) { count++; i += 10; }
  return count;
});

console.log("");
console.log("[4] 그 일을 하는 것은 let 이 아니라 for 헤더의 let 이다");
probe("for (let i;;) header", () => { const f = []; for (let i = 0; i < 3; i++) f.push(() => i); return f.map((g) => g()); });
probe("while + let declared outside", () => { const f = []; let i = 0; while (i < 3) { f.push(() => i); i++; } return f.map((g) => g()); });
probe("do..while + let outside", () => { const f = []; let i = 0; do { f.push(() => i); i++; } while (i < 3); return f.map((g) => g()); });
probe("for (;;) with let outside header", () => { const f = []; let i; for (i = 0; i < 3; i++) f.push(() => i); return f.map((g) => g()); });
probe("for..of with let", () => { const f = []; for (let x of [0, 1, 2]) f.push(() => x); return f.map((g) => g()); });
probe("for..in with let", () => { const f = []; for (let k in { a: 0, b: 1 }) f.push(() => k); return f.map((g) => g()); });
probe("forEach callback param", () => { const f = []; [0, 1, 2].forEach((x) => f.push(() => x)); return f.map((g) => g()); });

console.log("");
console.log("[5] 헤더의 이름과 몸통의 같은 이름은 다른 칸이다");
probe("body shadows the header name", () => {
  const f = [];
  for (let i = 0; i < 3; i++) { let i = "body"; f.push(() => i); }
  return f.map((g) => g());
});
probe("and the loop still counts", () => { let n = 0; for (let i = 0; i < 3; i++) { let i = "body"; n++; } return n; });
```

```text
===== node20 js06b-06c-per-iteration.js (exit=0) =====
[1] 칸이 새로 생겼다는 것 -- 한 회차에서 쓴 값이 다른 회차에 안 번진다
  let: write in fn0 leaks to fn1?          -> ["X",1,2]
  var: write in fn0 leaks to fn1?          -> ["X","X","X"]

[2] 그런데 값은 이어진다 -- 새 칸이 앞 회차의 값을 받아 온다
  body sets i = 1 on the first pass        -> [0,2]
  same with var                            -> [0,2]

[3] 회차 안에서 바꾼 값이 그 회차의 클로저에 남는다
  let: change i after pushing the fn       -> [10]
  how many passes did it make              -> 1

[4] 그 일을 하는 것은 let 이 아니라 for 헤더의 let 이다
  for (let i;;) header                     -> [0,1,2]
  while + let declared outside             -> [3,3,3]
  do..while + let outside                  -> [3,3,3]
  for (;;) with let outside header         -> [3,3,3]
  for..of with let                         -> [0,1,2]
  for..in with let                         -> ["a","b"]
  forEach callback param                   -> [0,1,2]

[5] 헤더의 이름과 몸통의 같은 이름은 다른 칸이다
  body shadows the header name             -> ["body","body","body"]
  and the loop still counts                -> 3
```

그림 해설.

- ★★★ **`[1]` 이 「새 칸」을 보인다.** `let` 판은 `["X",1,2]` — `fn0` 으로 쓴 것이 `fn1`·`fn2` 에 안 번진다. `var` 판은 셋이 전부 `"X"` 다.
- ★★★ **`[2]` 가 「그런데 값은 이어진다」를 보인다.** 첫 회차 몸통에서 `i = 1` 로 바꾸면 다음 회차가 `2` 로 시작해 `[0,2]` 가 된다 —
  **`var` 판과 글자가 같다.** ★★ 「새 칸」이 「독립된 카운터」라는 뜻은 **아니다.** 칸은 새로 생기되 **앞 회차의 값을 받아 온다.**
- ★★ **`[3]` 은 그 둘을 한 장면에 넣는다.** `i += 10` 을 몸통에 두면 루프는 **한 번만 돌고**, 그 회차의 클로저가 보는 값은 `10` 이다 —
  **함수를 넣은 뒤에 바꾼 값이 그 함수에 보인다.** 클로저가 붙든 것이 **값이 아니라 칸**이라는 증거가 여기서도 나온다.
- ★★★ **`[4]` 가 「무엇이 그 일을 하나」를 가른다.** `for` 헤더의 `let`·`for..of`·`for..in`·콜백 매개변수는 `[0,1,2]` 인데,
  **`while`·`do..while`·`for (i = 0; ...)`(헤더 밖에서 선언) 은 전부 `[3,3,3]`** 이다.
  ★★ 그러니 「`let` 을 쓰면 된다」는 틀리고 **「선언이 루프 헤더 안에 있어야 한다」가 맞는 문장**이다.
- ★ **`[5]` 는 헤더의 이름과 몸통의 같은 이름이 다른 칸임을 보인다.** 몸통에서 `let i = "body"` 로 가려도 **루프는 그대로 세 번 돈다.**

**비용** — 회차마다 칸을 만드는 것은 **`var` 시절에 IIFE 로 손수 하던 일**을 언어가 대신해 주는 것이다.
대신 **`while` 로 옮겨 적으면 조용히 의미가 바뀐다** — 같은 `let` 인데 답이 갈린다.

### (4) ★★ 클로저가 붙드는 것은 값이 아니라 칸이다

**언제 쓰나** — 「만들 때 값을 복사한 것 아닌가?」를 물을 때. 그리고 「진짜로 복사하고 싶을 때」를 고를 때.

```text
   값을 복사했다면 (틀린 그림)           칸을 붙들었다면 (맞는 그림)

   let v = "before"                      let v = "before"
   read = () => v                        read = () => v
        [ read 안에 "before" ]                 read ---> [ v | "before" ]
   v = "after"                           v = "after"
        [ read 안에 "before" ]                 read ---> [ v | "after"  ]
   read() -> "before"                    read() -> "after"

   ★ 실제 출력이 "after" 다 -> 오른쪽이 맞다.
```

```js
// js06b-06d-variable-not-value.js
// 클로저가 붙드는 것은 값의 사본이 아니라 그 변수 자체다.
function probe(label, run) {
  let r;
  try { r = JSON.stringify(run()); }
  catch (e) { r = e.constructor.name + ": " + e.message; }
  console.log("  " + label.padEnd(38) + " -> " + r);
}

console.log("[1] 만든 뒤에 바꿔도 따라온다 -- 값이었다면 안 따라온다");
probe("changed after the fn was made", () => {
  let v = "before";
  const read = () => v;
  const first = read();
  v = "after";
  return [first, read()];
});
probe("the fn was even called in between", () => {
  let v = 0;
  const read = () => v;
  const seen = [read()];
  v = 1; seen.push(read());
  v = 2; seen.push(read());
  return seen;
});

console.log("");
console.log("[2] 두 함수가 한 변수를 나눠 쓴다 -- 하나로 쓰면 다른 하나가 본다");
probe("read/write pair", () => {
  function make() { let n = 0; return { read: () => n, write: (v) => { n = v; } }; }
  const a = make();
  const out = [a.read()];
  a.write(42);
  out.push(a.read());
  return out;
});
probe("two calls to make() do not share", () => {
  function make() { let n = 0; return { read: () => n, write: (v) => { n = v; } }; }
  const a = make(), b = make();
  a.write(42);
  return [a.read(), b.read()];
});

console.log("");
console.log("[3] 그 변수는 함수가 끝난 뒤에도 산다");
probe("counter survives the call that made it", () => {
  function makeCounter() { let n = 0; return () => ++n; }
  const tick = makeCounter();
  return [tick(), tick(), tick()];
});
probe("two counters are independent", () => {
  function makeCounter() { let n = 0; return () => ++n; }
  const a = makeCounter(), b = makeCounter();
  return [a(), a(), b()];
});

console.log("");
console.log("[4] 인자로 받은 것도 같은 성질이다 -- 다만 이름이 회차마다 새로 생긴다");
probe("param is a fresh name per call", () => {
  function make(x) { return { read: () => x, write: (v) => { x = v; } }; }
  const a = make(1), b = make(2);
  a.write(99);
  return [a.read(), b.read()];
});
probe("object arg: box fresh, contents shared", () => {
  const shared = { n: 0 };
  function make(o) { return () => o.n; }
  const r = make(shared);
  shared.n = 5;
  return r();
});

console.log("");
console.log("[5] 「값을 박아 두고 싶다」는 다른 도구다");
probe("copy into a new name at make time", () => {
  let v = "before";
  const snapshot = ((copy) => () => copy)(v);
  v = "after";
  return [snapshot(), v];
});
probe("bind freezes the argument", () => {
  let v = "before";
  const show = (x) => x;
  const bound = show.bind(null, v);
  v = "after";
  return [bound(), v];
});
```

```text
===== node20 js06b-06d-variable-not-value.js (exit=0) =====
[1] 만든 뒤에 바꿔도 따라온다 -- 값이었다면 안 따라온다
  changed after the fn was made          -> ["before","after"]
  the fn was even called in between      -> [0,1,2]

[2] 두 함수가 한 변수를 나눠 쓴다 -- 하나로 쓰면 다른 하나가 본다
  read/write pair                        -> [0,42]
  two calls to make() do not share       -> [42,0]

[3] 그 변수는 함수가 끝난 뒤에도 산다
  counter survives the call that made it -> [1,2,3]
  two counters are independent           -> [1,2,1]

[4] 인자로 받은 것도 같은 성질이다 -- 다만 이름이 회차마다 새로 생긴다
  param is a fresh name per call         -> [99,2]
  object arg: box fresh, contents shared -> 5

[5] 「값을 박아 두고 싶다」는 다른 도구다
  copy into a new name at make time      -> ["before","after"]
  bind freezes the argument              -> ["before","after"]
```

그림 해설.

- ★★★ **`[1]` 이 `["before","after"]` 다.** 같은 함수가 **만들어진 뒤의 변경을 본다.** 값이었다면 둘 다 `"before"` 여야 한다.
  ★ 그 사이에 **한 번 불러 봤는데도** 그렇다 — 「처음 부를 때 굳는다」도 아니다.
- ★★★ **`[2]` 가 「한 칸을 나눠 쓴다」를 보인다.** `read`/`write` 는 서로 다른 함수인데 하나로 쓰면 다른 하나가 본다.
  그리고 **`make()` 를 두 번 부르면 안 나눠 쓴다**(`[42,0]`) — **호출마다 방이 새로 생기기 때문**이다.
  ★★ 이것이 2번 절의 「팩토리」가 칸을 셋으로 가른 이유와 **같은 사실**이다.
- ★★ **`[3]` 이 「방이 함수보다 오래 산다」를 보인다.** `makeCounter()` 는 끝났는데 `n` 은 살아서 `[1,2,3]` 을 센다.
  그리고 **카운터 둘은 독립**이다(`[1,2,1]`).
- ★★ **`[4]` 는 매개변수도 같은 성질임을 보인다.** 다만 **호출마다 이름이 새로 생기므로** 서로 안 섞인다.
  ★ **객체를 넘기면 칸은 새것인데 안의 내용물은 공유**다(`5`) — 「칸」과 「내용물」을 가르는 것은 [05번의 `const`](../05-var-let-const-and-tdz/2-summary.md)와 같은 구분이다.
- ★ **`[5]` 가 「값을 박아 두는」 두 도구를 보인다.** 새 이름에 복사하거나(IIFE) `bind` 로 인자를 박으면 둘 다 `"before"` 로 굳는다.

**비용** — 칸을 붙드는 쪽이 **상태를 나눠 쓰는 일**을 공짜로 해 준다(모듈 패턴·카운터).
대신 **「그때 그 값」이 필요하면 일부러 복사해야** 하고, 그 복사를 잊은 것이 2번 절의 루프 사고다.

### (5) ★★ 모듈 패턴 — 클로저로 「밖에서 못 보는 것」을 만든다

**언제 쓰나** — 객체에 내부 상태를 두되 **프로퍼티로 드러내고 싶지 않을** 때.

```text
   makeAccount(100) 이 돌려준 것

   +-------------------------+       그 함수들이 붙든 방
   | deposit  read  size     | ----> [ balance | 100 ]
   +-------------------------+       [ history | []  ]
     ^ Object.keys 로 보이는 것        ^ 어떤 API 로도 이름이 안 보인다

   ★ 감춰지는 것은 "이름"이다. 안의 객체를 밖으로 돌려주면 그 객체는 그대로 만져진다.
```

```js
// js06b-06e-module-pattern.js
// 모듈 패턴 -- 클로저로 비공개 상태를 만드는 관용구. 무엇이 감춰지고 무엇이 안 감춰지나.
function probe(label, run) {
  let r;
  try { r = JSON.stringify(run()); }
  catch (e) { r = e.constructor.name + ": " + e.message; }
  console.log("  " + label.padEnd(38) + " -> " + r);
}

function makeAccount(start) {
  let balance = start;              // 비공개 -- 밖에서 이름으로 못 건드린다
  const history = [];
  return {
    deposit(n) { balance += n; history.push(n); return balance; },
    read() { return balance; },
    size() { return history.length; },
  };
}

console.log("[1] 밖에서는 이름이 아예 안 보인다");
const acc = makeAccount(100);
probe("acc.read()", () => acc.read());
probe("Object.keys(acc)", () => Object.keys(acc));
probe("acc.balance", () => acc.balance);
probe('"balance" in acc', () => "balance" in acc);
probe("JSON.stringify(acc)", () => JSON.stringify(acc));
probe("getOwnPropertyNames", () => Object.getOwnPropertyNames(acc));

console.log("");
console.log("[2] 인스턴스마다 자기 칸이다");
probe("two accounts do not share", () => {
  const a = makeAccount(0), b = makeAccount(0);
  a.deposit(10);
  return [a.read(), b.read()];
});
probe("methods of one account share", () => {
  const a = makeAccount(0);
  a.deposit(10); a.deposit(20);
  return [a.read(), a.size()];
});

console.log("");
console.log("[3] 한 번만 만들고 싶으면 IIFE 로 즉시 부른다 -- 같은 기계다");
const single = (function () {
  let hits = 0;
  return { hit: () => ++hits, count: () => hits };
})();
probe("IIFE module: hit twice", () => { single.hit(); single.hit(); return single.count(); });
probe("typeof the IIFE result", () => typeof single);

console.log("");
console.log("[4] 감춰지는 것은 이름이지 값이 아니다");
probe("a leaked object is still reachable", () => {
  function make() { const secret = { k: 1 }; return { peek: () => secret }; }
  const m = make();
  const got = m.peek();
  got.k = 999;
  return m.peek();
});
probe("a leaked primitive is a copy", () => {
  function make() { let n = 1; return { peek: () => n, read: () => n }; }
  const m = make();
  let got = m.peek();
  got = 999;
  return m.read();
});

console.log("");
console.log("[5] 같은 일을 하는 다른 도구 -- 클래스의 # 필드");
class Acct {
  #balance = 0;
  deposit(n) { this.#balance += n; return this.#balance; }
  read() { return this.#balance; }
}
const k = new Acct();
probe("class #field: deposit then read", () => { k.deposit(7); return k.read(); });
probe("Object.keys of the instance", () => Object.keys(k));
probe("reading #balance from outside", () => new Function("o", "return o.#balance;"));
```

```text
===== node20 js06b-06e-module-pattern.js (exit=0) =====
[1] 밖에서는 이름이 아예 안 보인다
  acc.read()                             -> 100
  Object.keys(acc)                       -> ["deposit","read","size"]
  acc.balance                            -> undefined
  "balance" in acc                       -> false
  JSON.stringify(acc)                    -> "{}"
  getOwnPropertyNames                    -> ["deposit","read","size"]

[2] 인스턴스마다 자기 칸이다
  two accounts do not share              -> [10,0]
  methods of one account share           -> [30,2]

[3] 한 번만 만들고 싶으면 IIFE 로 즉시 부른다 -- 같은 기계다
  IIFE module: hit twice                 -> 2
  typeof the IIFE result                 -> "object"

[4] 감춰지는 것은 이름이지 값이 아니다
  a leaked object is still reachable     -> {"k":999}
  a leaked primitive is a copy           -> 1

[5] 같은 일을 하는 다른 도구 -- 클래스의 # 필드
  class #field: deposit then read        -> 7
  Object.keys of the instance            -> []
  reading #balance from outside          -> SyntaxError: Private field '#balance' must be declared in an enclosing class
```

그림 해설.

- ★★★ **`[1]` 에서 `balance` 가 어떤 창에도 안 걸린다.** `Object.keys`·`getOwnPropertyNames`·`in`·`JSON.stringify` 가 전부 메서드만 본다.
  ★★ **프로퍼티가 아니라 이름이기 때문**이다 — 「안 보인다」와 「없다」는 다르다는 [05번의 전역 `let`](../05-var-let-const-and-tdz/2-summary.md) 이야기와 같은 자리다.
- ★★ **`[2]` 가 「인스턴스마다 방」임을 보인다.** 계좌 둘이 안 섞이고(`[10,0]`), 한 계좌의 메서드들은 나눠 쓴다(`[30,2]`).
- ★★ **`[3]` 의 IIFE 는 같은 기계다** — 팩토리를 만들고 **그 자리에서 한 번 부른** 것뿐이다.
- ★★ **`[4]` 가 경계를 긋는다.** 안의 **객체를 돌려주면 그 객체는 그대로 만져진다**(`{"k":999}`).
  ★ 원시 값을 돌려주면 복사라서 안 만져진다(`1`). **감춰지는 것은 이름이지 값이 아니다.**
- ★ **`[5]` 는 같은 일을 하는 다른 도구다.** 클래스의 `#` 필드도 `Object.keys` 에 안 보이고,
  밖에서 읽으면 **`SyntaxError`** 다 — 클로저 쪽은 `undefined` 였는데 이쪽은 파싱 단계에서 죽는다. 정본은 목록의 **16번 주제**다.

**비용** — 클로저 비공개는 **인스턴스마다 함수 객체를 새로 만든다**(메서드가 프로토타입에 안 얹힌다).
★ **그 비용이 얼마인지는 안 쟀다** — 이 노트는 벤치마크를 돌리지 않는다.

### (6) ★ 클로저가 붙들면 치워지지 않는다 — 수거 여부만 본다

**언제 쓰나** — 「작은 콜백 하나가 왜 큰 응답을 붙들고 있나」를 물을 때.

★★ **이 절은 「관찰」이다.** GC 가 언제 도는지는 명세가 정하지 않으므로 **보장으로 읽으면 안 된다.**
그래서 **바이트를 재지 않고** 「수거됐나 아직 살아 있나」 두 상태만 본다. 이 블록만 `--expose-gc` 로 던진다.

```js
// js06b-06f-retain.js
// 클로저는 잡은 것을 살려 둔다 -- 「잰다」가 아니라 「수거됐나 아직 살아 있나」만 본다.
// ★ 이 블록만 --expose-gc 로 던진다. GC 시점은 명세가 정하지 않으므로 아래는 전부 「관찰」이다.
function kept(label, build) {
  const [fn, obj] = build();
  return [label, fn, new WeakRef(obj)];
}

const rows = [
  kept("nobody reads it", () => { const big = { tag: "big" }; return [() => "small", big]; }),
  kept("the returned fn reads it", () => { const big = { tag: "big" }; return [() => big.tag, big]; }),
  kept("only a sibling fn reads it", () => {
    const big = { tag: "big" };
    const sibling = () => big.tag;       // 만들기만 하고 돌려주지는 않는다
    return [() => "small", big];
  }),
  kept("copy out the one field it needs", () => {
    const big = { tag: "big" };
    const tag = big.tag;                 // 큰 것 대신 조각 하나만 들고 나간다
    return [() => tag, big];
  }),
];

setTimeout(() => {
  globalThis.gc();
  globalThis.gc();
  console.log("  " + "what the returned closure does".padEnd(32) + "the captured object is");
  console.log("  " + "-".repeat(32) + "-".repeat(22));
  for (const [label, fn, ref] of rows) {
    console.log("  " + label.padEnd(32) + (ref.deref() === undefined ? "collected" : "still alive").padEnd(14) +
                "fn() = " + JSON.stringify(fn()));
  }
  console.log("");
  console.log("[함수가 끝났는데 그 지역 변수를 아직 읽을 수 있다 -- 그것이 「잡고 있다」의 뜻이다]");
  function makeReader() { const rows2 = Array.from({ length: 1000 }, (_, i) => i); return () => rows2.length; }
  const r = makeReader();
  console.log("  makeReader() returned long ago, r() = " + r());
  console.log("  ten readers made the same way, sum = " +
    Array.from({ length: 10 }, () => makeReader()).reduce((s, f) => s + f(), 0));
}, 10);
```

```text
===== node20 --expose-gc js06b-06f-retain.js (exit=0) =====
  what the returned closure does  the captured object is
  ------------------------------------------------------
  nobody reads it                 collected     fn() = "small"
  the returned fn reads it        still alive   fn() = "big"
  only a sibling fn reads it      still alive   fn() = "small"
  copy out the one field it needs collected     fn() = "big"

[함수가 끝났는데 그 지역 변수를 아직 읽을 수 있다 -- 그것이 「잡고 있다」의 뜻이다]
  makeReader() returned long ago, r() = 1000
  ten readers made the same way, sum = 10000
```

그림 해설.

- ★★ **대조군이 있어야 뜻이 있다.** 첫 줄이 `collected` 로 나왔으므로 **GC 가 실제로 돌았다**는 것이 이 표의 전제다.
  ★ 전부 `still alive` 였다면 「GC 가 안 돈 것」과 구분이 안 된다.
- ★★★ **둘째 줄은 당연하고 셋째 줄이 교재다.** **돌려주지도 않은 형제 함수**가 그 객체를 읽는다는 이유만으로 **살아 남는다.**
  ★★ 이것이 실무의 「작은 콜백이 큰 응답을 붙든다」의 정확한 모양이다 — **같은 방을 나눠 쓰기 때문**이다.
  ★★★ **다만 이것은 V8 의 구현이다.** 명세는 「무엇이 수거되는가」를 약속하지 않는다.
- ★ **넷째 줄이 고침이다.** 큰 것 대신 **필요한 조각 하나만** 새 이름에 복사해 두면 수거된다.
- ★ 아래 두 줄은 **GC 없이도 성립하는 관찰**이다 — `makeReader()` 는 끝났는데 그 지역 배열이 아직 읽힌다.
  **「함수가 끝났는데 그 지역 변수를 읽을 수 있다」가 곧 「붙들고 있다」의 뜻**이다.

**비용** — 클로저는 **쓰는 이름만이 아니라 같은 방의 형제까지** 붙들 수 있다(이 판의 관찰).
★ **얼마나 붙드는지는 안 쟀다.** 재려면 힙 스냅샷이 필요하고, 그것은 이 주제가 아니다.

### (7) 두 판에서 돌려 보면 — 갈리는 자리가 없다

**언제 쓰나** — 「이게 이 판에서만 그런 건 아닐까」를 물을 때.

```sh
// js06b-vdiff.sh
#!/usr/bin/env bash
# 이 배치의 스크립트를 두 판으로 돌려 한 글자라도 다른지 본다.
# 쓰는 법: ./js06b-vdiff.sh <주제번호>
set -u -o pipefail
N18=node                                          # v18.19.1 (기본 PATH)
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"  # v20.19.6 (nvm)
printf '%-30s %s\n' "script" "node v18.19.1 vs v20.19.6"
printf '%-30s %s\n' "------------------------------" "-------------------------"
for f in js06b-"$1"*.js; do
  case "$f" in *-browser.js) continue;; esac      # 브라우저용은 뺀다
  flags=""
  case "$f" in *-retain.js) flags="--expose-gc";; esac
  a=$("$N18" $flags "$f" 2>&1); b=$("$N20" $flags "$f" 2>&1)
  if [ "$a" = "$b" ]; then printf '%-30s same (byte for byte)\n' "$f"
  else printf '%-30s DIFF -- lines %s\n' "$f" "$(diff <(printf '%s\n' "$a") <(printf '%s\n' "$b") | grep -c '^[<>]')"
  fi
done
```

```text
===== ./js06b-vdiff.sh 06 (exit=0) =====
script                         node v18.19.1 vs v20.19.6
------------------------------ -------------------------
js06b-06a-lexical-scope.js     same (byte for byte)
js06b-06b-box-count.js         same (byte for byte)
js06b-06c-per-iteration.js     same (byte for byte)
js06b-06d-variable-not-value.js same (byte for byte)
js06b-06e-module-pattern.js    same (byte for byte)
js06b-06f-retain.js            same (byte for byte)
js06b-06x-forms.js             same (byte for byte)
```

그림 해설.

- **일곱 스크립트 전부 한 글자도 같았다.** 스코프와 클로저는 **판이 올라도 안 움직이는 층**이다.
- ★★ **그런데 「같았다」는 보장이 아니다.** 보장은 명세에서 오고 이것은 관찰이다.
- ★ **6번 절의 GC 관찰도 두 판에서 같았다** — 그래도 그것은 여전히 관찰이다.

## 문법 — 형태와 규칙

**형태 — 이것이 전부다.** 출력이 없는 파일이라 `--check` 로 문법만 확인했다(「진단 0줄」도 블록으로 싣는다).

```js
// js06b-06x-forms.js
// 형태만 모아 둔 파일 -- 출력은 없다. `node --check` 로 문법만 확인한다.
const where = "module";                    // 바깥 이름

function outer() {
  const where = "outer";                   // 가장 가까운 것이 이긴다
  return function inner() { return where; };  // 정의된 자리의 사슬을 붙든다
}

const fns = [];
for (var i = 0; i < 3; i++) fns.push(() => i);   // ★ 변수 1개 -- 셋이 같은 칸을 본다
const fns2 = [];
for (let j = 0; j < 3; j++) fns2.push(() => j);  // ★ 변수 3개 -- 회차마다 새 칸

for (var k = 0; k < 3; k++) {                    // 옛 고침 -- IIFE 로 칸을 가른다
  (function (copy) { fns.push(() => copy); })(k);
}

function makeCounter() {                   // 모듈 패턴 -- balance 는 밖에서 안 보인다
  let n = 0;
  return { tick: () => ++n, read: () => n };
}

const single = (function () {              // 즉시 실행 -- 한 벌만 만든다
  let hits = 0;
  return { hit: () => ++hits };
})();

function snapshot(v) { return () => v; }   // 값을 박아 두고 싶으면 이름을 새로 만든다
```

```text
===== node20 --check js06b-06x-forms.js (exit=0) =====

```

> ★ **이 빈 블록이 근거다.** 「경고가 안 났다」를 산문으로 적으면 **안 물어본 것과 구분이 안 된다.**
> 명령과 `(exit=0)` 까지 담긴 **빈 출력**이라야 「던졌고 조용했다」가 된다.

규칙은 일곱이다.

1. **이름은 정의된 자리 기준으로 안에서 바깥으로 찾는다.** 부른 자리는 상관없다.
2. **함수를 만들면 그 자리의 스코프가 함수에 딸려 붙는다** — 바깥 함수가 끝나도 안 없어진다.
3. **클로저가 붙드는 것은 값이 아니라 칸이다.** 나중에 바뀌면 바뀐 것이 나온다.
4. ★★★ **`for` 헤더에 `let`/`const` 로 선언하면 회차마다 칸이 새로 생긴다.** `var` 는 함수당 하나다.
5. ★★ **그 일을 하는 것은 `let` 이 아니라 「루프 헤더의 선언」이다** — `while` 로 옮기면 안 된다.
6. **한 방을 나눠 쓰는 함수들은 서로의 변경을 본다.** 팩토리를 다시 부르면 새 방이다.
7. **값을 그때로 굳히려면 새 이름을 만들어야 한다** — IIFE·매개변수·`bind` 중 하나다.

## 어디서 틀리나

### (1) ★★★ 「나중에 읽어서 마지막 값이 나온다」로 외운다

**증상의 절반만 맞다.** 칸이 셋이었다면 나중에 읽어도 `0 1 2` 가 나왔을 것이다.
**원인은 「칸이 하나」라는 것**이고, 2번 절이 그 개수를 쓰기 탐침으로 직접 센다.

### (2) ★★★ 「`let` 을 쓰면 루프 클로저가 고쳐진다」로 외운다

고치는 것은 **`for` 헤더의 선언**이다.

```text
   for (let i = 0; i < 3; i++) fns.push(() => i);   // 변수 3개  -> [0,1,2]
   let i = 0; while (i < 3) { fns.push(() => i); i++; }  // 변수 1개 -> [3,3,3]
```

**같은 `let` 인데 답이 갈린다.** 3번 절 `[4]` 의 일곱 줄이 그 목록이다.

### (3) ★★ 「회차마다 새 칸이면 값도 따로 센다」로 읽는다

**칸은 새것인데 값은 이어진다.** 몸통에서 `i` 를 바꾸면 다음 회차의 시작값이 바뀐다 — `var` 와 **글자가 같은 출력**이 나온다.

### (4) ★★ 함수를 어디서 부르느냐가 이름에 영향을 준다고 믿는다

**안 준다.** 부른 쪽의 지역 변수는 안 보인다(1번 절 `[2]`).
★ 그런데 **`this` 는 정반대**다 — 호출식이 정한다. **이름 규칙을 `this` 에 적용하면 07번의 사고가 전부 여기서 나온다.**

### (5) ★★ 클로저가 값을 복사해 간다고 믿는다

**안 한다.** 만든 뒤에 바꾸면 바뀐 것이 나온다. 굳히고 싶으면 **새 이름을 만들어야** 한다(4번 절 `[5]`).

### (6) ★ 모듈 패턴이 값을 지켜 준다고 믿는다

**지키는 것은 이름이다.** 안의 객체를 밖으로 돌려주면 그 객체는 그대로 만져진다(5번 절 `[4]`).

### (7) ★ 작은 콜백은 메모리를 조금만 붙든다고 믿는다

**같은 방의 형제가 큰 것을 읽으면 그것까지 살아 남는다**(이 판의 관찰). 조각만 복사해 두면 수거된다.

## 구현 세부사항 대 언어 보장

세 층으로 가른다. ★ **이 주제는 「명세 보장」 칸이 두껍고, 「관찰」 칸이 딱 하나 — GC 다.**

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **명세(ECMA-262) 보장** | 어느 엔진에서도 같아야 하는 것 | 위 기준 소스를 열어서 + 실행으로 재확인 |
| **엔진(V8) 구현** | V8 이 그렇게 하는 것 — **예외 문구**와 **무엇을 살려 두는가** | 실행 + 두 판 대조 |
| **이 판의 관찰** | node 20.19.6 / 18.19.1 에서 그랬을 뿐 | 「관찰」로 명기 |

### 명세 보장

| 사실 | 어떻게 확인했나 |
|---|---|
| **이름은 정의된 자리 기준으로 풀린다** | 부른 쪽의 같은 이름이 **안 읽힌다**는 관찰 |
| **함수는 자기가 태어난 스코프를 붙든다** | 바깥 함수가 끝난 뒤에도 그 이름이 읽힌다 |
| **붙드는 것은 값이 아니라 바인딩이다** | 만든 뒤의 변경이 보인다 · 두 함수가 서로의 쓰기를 본다 |
| ★★★ **`for` 헤더의 `let`/`const` 는 회차마다 새 바인딩을 만든다** | 쓰기 탐침의 **서로 다른 변수 개수 3** |
| ★★★ **`var` 는 함수당 하나다** | 같은 탐침의 **개수 1** |
| **그 새 바인딩은 앞 회차의 값을 이어받는다** | 몸통에서 `i` 를 바꾸면 다음 회차 시작값이 바뀐다 |
| **`while`·`do..while` 은 그 일을 하지 않는다** | 같은 `let` 인데 `[3,3,3]` |
| **호출마다 새 스코프가 생긴다** | 팩토리를 두 번 부르면 안 섞인다 |
| **`const` 로 잡은 이름은 재대입이 `TypeError`** | 탐침의 거부 출력(정본은 05번) |

### 엔진(V8) 구현 · 이 판의 관찰

| 관찰 | 어디가 흔들리나 |
|---|---|
| `Assignment to constant variable.` 같은 **문구** | 예외의 **종류**는 명세지만 문구는 아니다 |
| ★★★ **형제 클로저가 읽으면 같이 살아 남는 것** | **V8 이 스코프를 통째로 붙드는 사정**이다. 명세는 「무엇이 수거되나」를 약속하지 않는다 |
| **`collected` / `still alive` 라는 판정 자체** | GC 시점이 명세 밖이라 **관찰**이다. 이 판에서 6회 전부 같았다 |
| Node 20.19.6 의 V8 은 **11.3.244.8**, 18.19.1 은 **10.2.154.26** | `process.versions.v8` |
| 이 주제의 일곱 스크립트가 **두 판에서 한 글자도 같았다** | `js06b-vdiff.sh 06` |

### 그래서 이렇게 적으면 틀린다

- ✗ 「루프 클로저는 나중에 읽어서 마지막 값이 나온다」
  ○ **칸이 하나여서** 그렇다. 칸이 셋이면 나중에 읽어도 `0 1 2` 다.
- ✗ 「`let` 을 쓰면 고쳐진다」
  ○ **`for` 헤더에 선언해야** 고쳐진다. `while` 로 옮기면 그대로다.
- ✗ 「회차마다 새 변수니까 값도 따로 센다」
  ○ **값은 이어받는다.** 몸통에서 바꾸면 다음 회차가 그 값으로 시작한다.
- ✗ 「클로저는 만들 때 값을 복사한다」
  ○ **칸을 붙든다.** 나중에 바뀌면 바뀐 것이 나온다.
- ✗ 「함수를 어디서 부르느냐에 따라 보이는 이름이 달라진다」
  ○ **안 달라진다.** 그것은 `this` 의 이야기이고 07번이다.
- ✗ 「안 쓰는 변수는 클로저가 안 붙든다」
  ○ **형제가 쓰면 같이 붙든다**(V8 관찰). 명세 보장이 아니므로 **거꾸로도 단정하면 안 된다.**

**판정 기준 한 줄**: 어떤 함수를 보면 「**이 함수가 붙든 칸이 몇 개이고 누구와 나눠 쓰나**」를 묻는다. 값을 먼저 보지 않는다.

## 언제 쓰고 언제 안 쓰나

| 쓰는 것 | 상황 |
|---|---|
| `for (const x of ...)` | 순회 — 회차마다 새 이름이라 클로저를 만들어도 안전하다 |
| `for (let i = 0; ...)` | 인덱스가 필요하고 **콜백을 만들** 때. 헤더 안에 선언하는 것이 요점이다 |
| 팩토리 함수 | 인스턴스마다 자기 상태가 필요할 때. 클로저 비공개의 표준형 |
| IIFE | **옛 코드를 읽을 때.** 새 코드에서는 블록 스코프가 대신한다 |
| `bind`(인자 고정) | 그때의 **값**을 박아 두고 싶을 때 — 칸이 아니라 값이다 |
| 조각만 복사 | 큰 객체를 붙들기 싫을 때. 필요한 필드만 새 이름에 옮긴다 |

**안 쓰는 자리**는 셋이다.
**`var` 로 루프 클로저를 만들지 마라** — 칸이 하나라 셋이 같은 것을 본다.
**`while` 로 옮기면서 `let` 만 믿지 마라** — 헤더가 아니면 회차마다 칸이 안 생긴다.
**클로저를 「값 스냅샷」으로 쓰지 마라** — 그것은 새 이름을 만드는 일이고 클로저가 하는 일이 아니다.

## 핵심 문장

- **이름은 정의된 자리 기준으로 찾는다.** 부른 자리는 상관없다 — 그래서 클로저가 성립한다.
- **클로저가 붙드는 것은 값이 아니라 칸이다.** 나중에 바뀌면 바뀐 것이 나온다.
- ★★★ **루프 클로저의 원인은 값이 아니라 개수다** — `var` 는 변수 1개, `for` 헤더의 `let` 은 3개.
- ★★ **회차마다 칸은 새로 생기되 값은 이어받는다.** 두 사실이 따로다.
- ★★ **고치는 것은 `let` 이 아니라 「루프 헤더의 선언」이다** — `while` 은 그대로다.
- **IIFE·몸통의 `let`·팩토리는 전부 같은 일을 한다** — 칸을 가르는 것.
- ★ **클로저는 자기가 읽는 것만이 아니라 같은 방의 형제가 읽는 것까지 살려 둔다**(V8 관찰).

## 관련 자료

- 목록: [js/syntax 주제 목록](../README.md) — 이 주제는 **06번**
- 선행: [05 — `var`·`let`·`const` 와 TDZ](../05-var-let-const-and-tdz/2-summary.md) —
  **블록 스코프·TDZ·`const` 의 정본**이다. **그쪽은 「이 이름이 언제부터 쓸 수 있나」까지, 여기는 「그 이름을 누가 몇 개 붙들고 있나」부터다.**
- 이어지는 곳: 목록의 **07번 주제** 「`this` 바인딩 네 규칙」 — ★★ **`this` 는 이 문서의 규칙을 따르지 않는다.** 그 대비가 07번의 첫 문장이다.
- 이어지는 곳: 목록의 **08번 주제** 「함수 정의 형태와 매개변수」 — 매개변수도 클로저가 잡는 이름이다. **기본값의 스코프**가 거기 있다.
- 이어지는 곳: 목록의 **16번 주제** 「`class` 문법」 — `#` 필드가 클로저 비공개와 같은 자리를 다른 방법으로 푼다.
- 이어지는 곳: 목록의 **47번 주제** 「`WeakRef`·`FinalizationRegistry`」 — 6번 절이 쓴 도구의 정본. **GC 시점에 기대면 안 되는 이유**가 거기다.
- ★★★ 경계 — 다른 언어의 **같은 결함**: [`python/syntax/22-closures-and-late-binding`](../../../python/syntax/22-closures-and-late-binding/2-summary.md) —
  파이썬도 **루프가 상자를 안 만든다.** 그쪽은 `함수.__closure__[0]` 을 꺼내 **`is` 로 셀 개수를 세고**, 여기는 손잡이가 없어 **쓰기 탐침으로 센다.**
  ★★ **파이썬은 언어가 이 결함을 안 고쳤다** — 기본 인자·팩토리·`partial` 로 **쓰는 쪽이** 고친다.
  **그쪽은 「고치는 세 가지」까지, 여기는 「언어가 새 선언 형태로 고쳤다」부터다.**
- ★★★ 경계 — **같은 결함의 세 번째 답**: [`go/syntax/13-closures-variable-capture-and-loop-variable-change`](../../../go/syntax/13-closures-variable-capture-and-loop-variable-change/2-summary.md) —
  Go 는 **언어 판 자체를 바꿔**(1.22) 같은 소스의 의미를 뒤집었다. 그쪽은 포인터 주소를 모아 「**서로 다른 상자 개수**」를 센다.
  **셋이 같은 칸을 세는데 도구가 전부 다르다** — 파이썬은 셀 객체, Go 는 포인터, JS 는 쓰기 탐침.
- 경계 — 스코프 일반론: [`python/syntax/21-scope-legb-global-nonlocal`](../../../python/syntax/21-scope-legb-global-nonlocal/2-summary.md) —
  **파이썬에는 블록 스코프가 없다.** 그쪽은 「어느 스코프에서 찾나(LEGB)」, 여기는 「그 스코프가 몇 개 생기나」다.
- 경계 — 연혁은 여기가 아니다: [`history/js/02-ES6-모던.md`](../../../../../../history/js/02-ES6-모던.md) — 블록 스코프가 **언제 왜** 들어왔나.
- 경계 — 타입 이야기: TypeScript 갈래 목록([`ts/syntax/README.md`](../../../ts/syntax/README.md))의 **01번**.
  **그쪽은 「타입은 런타임에 안 남는다」, 여기는 런타임 규칙이다.**

## 용어 풀이

- **스코프(scope)**: 어떤 이름이 통하는 구역. JS 는 `var` 만 함수 구역이고 나머지는 블록 구역이다.
- **바인딩(binding)**: 이름과 값이 들어가는 칸 하나. 「변수」라고 부르는 것의 실체다.
- **클로저(closure)**: 함수 + 그 함수가 태어난 자리의 스코프를 함께 묶은 것.
- **렉시컬 스코프(lexical scope)**: 이름을 **소스에 적힌 자리** 기준으로 찾는 것. 반대는 **동적 스코프** — JS 는 아니다.
- **스코프 체인(scope chain)**: 안쪽 스코프에서 바깥 스코프로 이어진 조회 경로. 가장 가까운 것이 이긴다.
- **자유 변수(free variable)**: 어떤 함수에서 **쓰이는데 그 함수가 선언하지는 않은** 이름.
- **회차별 바인딩(per-iteration binding)**: `for` 헤더에 `let`/`const` 로 선언했을 때 회차마다 새로 생기는 칸. **값은 앞 회차에서 이어받는다.**
- **IIFE (Immediately Invoked Function Expression)**: 만들자마자 부르는 함수 표현식. `let` 이 없던 시절 **블록 스코프 대용**이었다.
- **모듈 패턴(module pattern)**: 팩토리 안의 이름을 비공개 상태로 쓰고 메서드만 돌려주는 관용구.
- **쓰기 탐침(write probe)**: 이 문서가 쓰는 도구. 한 함수로 쓰고 나머지로 읽어 **같은 칸인지 판정**한다. 주소를 안 쓴다.
- **`WeakRef`**: 대상을 **붙들지 않고** 가리키는 참조(ES2021). 수거되면 `deref()` 가 `undefined` 다. 정본은 목록의 **47번 주제**다.

## 더 들어가면

- **엔진이 스코프를 어떻게 담는가**(변수 하나짜리 슬롯인가, 방 통째인가)는 **이 주제가 아니다.**
  표준 API 로 볼 방법이 없고, 6번 절의 「형제까지 산다」는 그 사정이 **밖으로 새어 나온 것**일 뿐 명세 보장이 아니다.
- **`with` 와 직접 `eval` 이 스코프 체인을 바꾸는 자리**는 엄격 모드에서 막히거나 쓰지 않는다 — 목록의 **35번 주제**에서 한 줄로 다룬다.
- **모듈(ESM)의 최상위 스코프**는 또 다르다. 이 배치는 CommonJS 와 브라우저 classic script 두 자리만 던졌다 — **ESM 은 42번 주제**의 몫이다.
- **안 돌려 본 것** — ESM(`.mjs`) 최상위 · Web Worker · 다른 엔진(SpiderMonkey·JavaScriptCore) ·
  Node 18 보다 낮은 판 · **힙 스냅샷으로 실제 보유량을 재는 것** · `--max-old-space-size` 같은 플래그를 바꿔 GC 관찰을 되풀이하는 것.
- ★ **못 잰 것** — **「클로저가 얼마나 붙드나」.** `WeakRef` 는 **수거 여부**만 말하고 **양**은 말하지 않는다.
  양을 재려면 힙 스냅샷이 필요하고, 그 수치는 이 문서의 「안 흔들리는 칸」에 없다. 그래서 **양에 대한 문장은 한 줄도 쓰지 않았다.**
