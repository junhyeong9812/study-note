# js/syntax/37 — Promise 상태 모델: 「한 번 정해지면 안 바뀐다 · `then` 은 새 프라미스를 만든다 · 거부를 아무도 안 받으면 호스트가 알린다」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> ★★★ **이 주제의 본체는 ② 전수 격자 셋이다** — **상태 전이 11행**(나중 호출이 상태를 바꾼 행을 스크립트가 센다 — 동작 (1)) ·
> **`finally` 8칸**(상류의 결과가 호출자에게 닿지 못한 칸을 센다 — 동작 (4)) · **미처리 거부 6행 × node 두 판**(두 판이 갈린 행을 센다 — 동작 (5)).
> ★★★ **틱 수는 ① 추상 연산에 로그 심기로 센다** — 한 틱에 한 번씩 스스로 다시 걸리는 **계수 잡**을 돌리고, `then` 콜백이 **몇 틱째에** 돌았나를 찍는다(동작 (2)).
> ★★ 보조로 **④ 예외의 `constructor.name` + `message`** — 자기 자신으로 `resolve` 한 프라미스의 `TypeError 「Chaining cycle detected for promise #<Promise>」`.
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262 — Promise Objects](https://tc39.es/ecma262/multipage/control-abstraction-objects.html#sec-promise-objects) — `CreateResolvingFunctions`(resolve·reject 가 **한 칸을 나눠 쓰는** 것) · `NewPromiseResolveThenableJob` · `HostPromiseRejectionTracker`(「`"reject"`」·「`"handle"`」) · `Promise.prototype.finally`
> - [HTML — Unhandled promise rejections](https://html.spec.whatwg.org/multipage/webappapis.html#unhandled-promise-rejections) — HTML 의 `HostPromiseRejectionTracker` 구현(「**classic script 이고 muted errors 면 return**」) · `notify about rejected promises`(**태스크를 하나 큐에 넣어** 이벤트를 쏜다)
> - [Node.js v20 — `--unhandled-rejections`](https://nodejs.org/docs/latest-v20.x/api/cli.html#--unhandled-rejectionsmode) — v15.0.0 에서 기본값이 `throw` · [process 의 `unhandledRejection`·`rejectionHandled` 이벤트](https://nodejs.org/docs/latest-v20.x/api/process.html#event-unhandledrejection)
> - [TC39 finished proposals](https://github.com/tc39/proposals/blob/main/finished-proposals.md) — `Promise.prototype.finally` **2018**
>
> ★★★ **명세 조항 번호는 인용하지 않는다.** 규칙 진술은 **추상 연산 이름**으로, 상태·틱 수·예외는 **전부 실행으로** 접지했다.
>
> **실행 검증** — 이 문서의 모든 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다.
> 배너의 `node20` 은 `~/.nvm/versions/node/v20.19.6/bin/node`, `node18` 은 기본 PATH 의 `node`(v18.19.1)다. Chrome 151 은 헤드리스(`./js36b-browser.sh` — 소스는 [36번](../36-event-loop-and-microtasks/2-summary.md)에 있다).
> ★★ **예외는 `이름 「메시지」` 꼴로** 찍었다. ★★★ **미처리 거부 경고는 표준 오류다** — 격자에서는 node 의 이벤트(`process.on`)로 받아 **표준 출력**에 찍었고, 표준 오류 그 자체는 **따로 한 블록**에 실었다(동작 (5)).
> ★★ **이 주제의 node 탐침은 두 node 판과 Chrome 151 에서 한 글자도 같았다**(아래 대조기의 집계 줄).
>
> **버전**
>
> | 무엇 | 판 | 이 머신에서 |
> |---|---|---|
> | `Promise` · `then` · `catch` · `Promise.resolve`/`reject` | ES2015 | 세 판 다 있다 |
> | `Promise.prototype.finally` | **ES2018** | 세 판 다 있다 |
> | `HostPromiseRejectionTracker`(명세의 호스트 훅) | — **이 문서는 들어온 판을 대조하지 않았다** | 훅 자체는 관찰할 수 없다 — 호스트의 보고로만 본다 |
> | `unhandledrejection`·`rejectionhandled` 이벤트 | — **HTML** | Chrome 151 |
> | `process.on('unhandledRejection')` · `--unhandled-rejections` | — **node**(기본 `throw` 는 v15.0.0 부터 — node 문서) | node 18 · 20 둘 다 `throw` 로 동작했다 |
>
> ★★ **판 경계는 TC39 finished proposals 표와 이 목록의 README 를 대조했다** — `Promise.prototype.finally` 가 **2018**. README 37행은 판을 적지 않는다.
>
> **★★★ 이 주제가 쓰는 창 — 그리고 부적용인 창**
>
> | 창 | 이 주제에서 무엇을 보나 |
> |---|---|
> | ★★★ **② 전수 격자**(본체) | 상태 전이 **11행** · `finally` **8칸** · 미처리 거부 **6행 × 2판** — 셋 다 마지막 줄을 스크립트가 센다 |
> | ★★★ **① 추상 연산에 로그 심기** | 계수 잡으로 **틱 수**를 센다 · thenable 의 **`then` 게터가 읽히는 때**와 **`then()` 이 불리는 때**를 찍는다(동작 (2)) |
> | ★★ **④ 예외의 `constructor.name` + `message`** | 자기 자신으로 `resolve` → `TypeError` · `then` 게터가 던진 `Error 「g」` 가 **그대로 거부 이유**가 되는 것 |
> | ★ **부적용 — ③ 브랜드 태그** | 프라미스인지 가리는 판정은 34번이 정본이다. 여기서는 **thenable**(`then` 이 함수인 객체)이 판정 기준이다 |
> | ★ **창을 바꿔 물었다**(제5의 상태) | 「이 거부가 보고됐나」를 node 에서는 **`process.on` 이벤트 + 종료 코드**로, Chrome 에서는 **`window` 의 이벤트**로 물었다 — ECMA-262 에는 보고하는 동작이 없다(훅뿐) |
> | ★ **안 쟀다 — 시간** | 「`then` 은 느리다」를 쓰지 않는다. **틱 수는 세고 시간은 안 잰다** |
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ★★ **`--unhandled-rejections=warn` 블록의 `(node:PID)`** — 실행마다 바뀐다(재대조에서 정규화한다) | ★★★ 세 격자의 **칸 글자**와 마지막 줄 `0 / 5` · `4 / 8` · `0 / 6` |
> | 기본 모드 표준 오류 블록의 **`node:internal/…:줄:칸`** — node **판마다** 바뀐다(판을 고정했으므로 재실행에서는 같다) | ★★★ **틱 수**(`@0`·`@1`·`@2`·`@3`) — 계수 잡이 틱을 세므로 기계 속도에 안 매인다 · 두 node 판과 Chrome 이 같았다 |
> | 예외 **문구** — V8 의 글자다 | 종료 코드 `0`·`1` · Chrome 이벤트의 **순서** |
>
> **★★★ 층 — 거부를 「보고하는」 것은 언어가 아니다**
>
> | 층 | 무엇을 정하나 | 이 문서의 어디 |
> |---|---|---|
> | **언어 명세(ECMA-262)** | 상태 전이(한 번만) · `then` 의 전파 · thenable 을 **잡 하나로** 흡수 · 미처리 거부 때 **`HostPromiseRejectionTracker` 를 부르는 것까지** | 동작 (1)\~(4) |
> | **호스트 — HTML** | 훅을 받아 **체크포인트 뒤 태스크 하나로** `unhandledrejection` 을 쏜다 · 나중에 달리면 `rejectionhandled` · **muted errors 면 아무것도 안 한다** | 동작 (5)의 Chrome |
> | **호스트 — node** | 한 콜백 뒤의 비우기가 끝났을 때 **아직 처리기가 없으면** 보고 · 기본 모드 `throw` 면 **종료 코드 1** · `process.on` 이 있으면 그것만 부른다 | 동작 (5)의 node |
> | **구현(V8)** | 예외 문구(`Chaining cycle detected …`) | 동작 (1) |
>
> **선행** — [36 — 이벤트 루프와 마이크로태스크](../36-event-loop-and-microtasks/2-summary.md)(직접 선행 — ★★★ **틱**이 거기서 나온다: 마이크로태스크는 등록 순서대로 빌 때까지) ·
> [32 — 오류 처리와 `Error`](../32-error-handling-and-error/2-summary.md)(★★★ **`try`/`finally` 격자 `6 / 9`** — 이 문서의 `.finally()` 격자와 **나란히** 읽는다. 동작 (4)) ·
> [19 — 이터러블 프로토콜과 `for...of`](../19-iterable-protocol-and-for-of/2-summary.md)(★ **thenable 은 이터러블과 같은 「덕 타이핑 프로토콜」** 이다 — 이름이 `then` 인 함수가 있으면 된다).
>
> ★★ **경계 — 연혁**(콜백 지옥 · 평탄화가 왜 필요했나)은 [`history/js/04-비동기-진화.md`](../../../../../../history/js/04-비동기-진화.md) 의 **「3단계 — Promise (ES2015): 미래의 값을 객체로」** 절이 정본이다. 여기서는 **그 규칙을 재고 틱을 센다.**
> ★ **경계 — 조합기**(`all`·`race`…)는 [38번](../38-promise-combinators/2-summary.md), **`await` 로 거부를 받는 법**은 [39번](../39-async-await/2-summary.md), **순서 자체**는 36번.

```text
===== ./js36b-versions.sh (exit=0) =====
node 18.19.1  v8 10.2.154.26-node.28
  ES2015  Promise                                   yes
  ES2017  async function / await                    yes
  ES2018  Promise.prototype.finally                 yes
  ES2020  Promise.allSettled                        yes
  ES2021  Promise.any / AggregateError              yes
  ES2024  Promise.withResolvers                     no
  ES2025  Promise.try                               no
  ES2026  Array.fromAsync                           no
  host    queueMicrotask                            yes
  host    setTimeout                                yes
  host    setImmediate                              yes
  host    process.nextTick                          yes
node 20.19.6  v8 11.3.244.8-node.33
  ES2015  Promise                                   yes
  ES2017  async function / await                    yes
  ES2018  Promise.prototype.finally                 yes
  ES2020  Promise.allSettled                        yes
  ES2021  Promise.any / AggregateError              yes
  ES2024  Promise.withResolvers                     no
  ES2025  Promise.try                               no
  ES2026  Array.fromAsync                           no
  host    queueMicrotask                            yes
  host    setTimeout                                yes
  host    setImmediate                              yes
  host    process.nextTick                          yes
Google Chrome 151.0.7922.173
  ES2015  Promise                                   yes
  ES2017  async function / await                    yes
  ES2018  Promise.prototype.finally                 yes
  ES2020  Promise.allSettled                        yes
  ES2021  Promise.any / AggregateError              yes
  ES2024  Promise.withResolvers                     yes
  ES2025  Promise.try                               yes
  ES2026  Array.fromAsync                           yes
  host    queueMicrotask                            yes
  host    setTimeout                                yes
  host    setImmediate                              no
  host    process.nextTick                          no
Python 3.12.3
```

두 node 판 · Chrome 대조기의 집계 줄 — 전문은 [3-answer.md](3-answer.md) 의 「실행 검증」에 있다.

`node18 vs node20: identical 13 · differs 0   ·   node20 vs Chrome 151: identical 12 · differs 0 · node only 1`

## 한눈에 — 쉽게 말하면

**프라미스는 「봉인되는 봉투」다. 봉투에는 칸이 하나 — 「결과」 — 있고, 처음 넣은 것으로 봉인된다. 그 뒤로 넣는 것은 전부 버려진다.**

- ★★★ **처음 온 것만 들어간다** — `resolve` 를 두 번 해도, `resolve` 뒤에 `reject` 해도, 그 뒤에 `throw` 해도 **첫 것**이다.
- ★★★ **봉투를 넣으면(`resolve(다른 프라미스)`) 그 봉투를 따라간다** — 이때는 **봉인은 됐는데 아직 비어 있다**(pending 인 채로 잠긴다). 따라가는 데 **틱이 든다.**
- ★★ **`then` 은 봉투를 여는 게 아니라 「이 봉투가 열리면 할 일」을 적은 새 봉투를 만든다** — 그래서 사슬이 된다.
- ★★ **아무도 안 여는 「거부」 봉투는 호스트가 알린다** — 언어는 「이런 봉투가 생겼다」고 **훅**만 부른다.

```text
                         resolve(v) — v 가 thenable 이 아님
              ┌────────────────────────────────────────────▶  fulfilled (값 v)
              │
   pending ───┼── resolve(p) — p 가 thenable ──▶ pending(잠김) ──▶ p 를 따라 fulfilled / rejected
              │
              └── reject(e) · executor 의 throw ──────────────▶  rejected (이유 e)

   fulfilled · rejected 에서는 어디로도 안 간다  (둘을 합쳐 settled)
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 봉투의 결과 칸 | `[[PromiseState]]` · `[[PromiseResult]]` | 동작 (1)의 `final` 열 |
| 봉인 | resolve·reject 두 함수가 **한 칸을 나눠 쓰고**, 처음 불린 쪽이 그 칸을 비운다(`CreateResolvingFunctions`) | 동작 (1)의 `0 / 5` |
| 봉투를 넣는다 | `resolve(thenable)` — **잡 하나**를 걸어 그 `then` 을 부른다(`NewPromiseResolveThenableJob`) | 동작 (2)의 `@2` |
| 「열리면 할 일」 적은 새 봉투 | `p.then(f, r)` 이 돌려주는 **새 프라미스** | 동작 (3) |
| 호스트가 알린다 | `HostPromiseRejectionTracker(p, "reject")` → HTML/node 가 보고 | 동작 (5) |

**똑같은 구조다** — 실무에서 물리는 자리도 굳어 있다.
「**`new Promise` 안에서 `resolve()` 뒤에 에러가 났는데 아무 데서도 안 잡혔다**」(이미 봉인됐다)와
「**`.catch` 를 나중에 붙였더니 node 가 먼저 죽었다**」(한 바퀴가 지났다)가 그것이다(동작 (1)·(5)).

> **settled(확정)** — fulfilled 이거나 rejected 인 상태. 한 번 되면 다시 안 바뀐다.\
> 예: `Promise.resolve(1)` 은 만들어지는 순간 settled 다.

> **thenable** — `then` 이라는 **함수** 프로퍼티를 가진 객체. 프라미스가 아니어도 된다.\
> 예: `{ then(onF) { onF(1); } }`.

## 이 주제가 답하려는 질문

1. **프라미스의 상태는 언제 정해지고, 정해진 뒤 또 부르면 무엇이 되나** — `resolve(다른 프라미스)` 와 `resolve(thenable)` 은 무엇을 하고, **틱이 몇 개 드나**?
2. **`then` 사슬에서 값과 예외는 어떻게 흘러가나** — 처리기가 없는 칸 · 던지는 칸 · `.finally()` 는 무엇을 넘기나(`try`/`finally` 와 무엇이 다른가)?
3. **거부를 아무도 안 받으면 언제, 누가, 어떻게 알리나** — 같은 틱 · 다음 마이크로태스크 · 다음 매크로태스크에 `catch` 를 달면? node 두 판과 Chrome 에서?

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 출력으로 읽는다.

### (1) ★★★ 상태 전이 격자 — 처음 것이 이긴다

**언제 쓰나** — `new Promise` 의 executor 안에서 여러 갈래로 `resolve`/`reject` 를 부르는 코드를 읽을 때 · 콜백 API 를 프라미스로 감쌀 때.
★★★ 행마다 executor 가 **여러 번** 부른다. 최종 상태는 **모든 잡이 끝난 뒤** `then(onF, onR)` 으로 읽는다.

```js
// js36b-37a-transitions.js
// Each row: an executor that makes several calls. Every call is recorded; the final state is read later.
// Final state = what then(onFulfilled, onRejected) sees after all queued jobs ran (or "pending" if neither ran).
const show = (x) => (x instanceof Error ? x.constructor.name + " 「" + x.message + "」" : JSON.stringify(x));
const later = { p: null, resolve: null };
later.p = new Promise((r) => { later.resolve = r; });
const thenable = (body) => ({ then(onF, onR) { body(onF, onR); } });
const rows = [
  ["resolve('a') · resolve('b')",                (res, rej) => { res("a"); res("b"); }],
  ["resolve('a') · reject('b')",                 (res, rej) => { res("a"); rej("b"); }],
  ["reject('a') · resolve('b')",                 (res, rej) => { rej("a"); res("b"); }],
  ["throw Error('a')",                           (res, rej) => { throw new Error("a"); }],
  ["resolve('a') · throw Error('b')",            (res, rej) => { res("a"); throw new Error("b"); }],
  ["resolve(p pending) · reject('b')",           (res, rej) => { res(later.p); rej("b"); }],
  ["resolve(Promise.reject('r'))",               (res, rej) => { res(Promise.reject("r")); }],
  ["resolve(thenable: onF('t'))",                (res, rej) => { res(thenable((f) => f("t"))); }],
  ["resolve(thenable: onF('t') · onR('u') · throw)", (res, rej) => { res(thenable((f, r) => { f("t"); r("u"); throw new Error("x"); })); }],
  ["resolve(object whose then getter throws)",   (res, rej) => { res({ get then() { throw new Error("g"); } }); }],
  ["resolve(the promise itself)",                (res, rej) => { setTimeout(() => res(self), 0); }],
];
let self;
const out = rows.map(([label, ex]) => {
  const row = { label, final: "pending" };
  const p = new Promise(ex);
  if (label.startsWith("resolve(the promise itself)")) self = p;
  p.then((v) => { row.final = "fulfilled " + show(v); }, (e) => { row.final = "rejected  " + show(e); });
  return row;
});
setTimeout(() => {
  console.log("[before p settles]");
  for (const r of out) if (r.label.startsWith("resolve(p pending)")) console.log("  " + r.label.padEnd(48) + r.final);
  later.resolve("c");
  setTimeout(() => {
    console.log("[after everything settled]");
    for (const r of out) console.log("  " + r.label.padEnd(48) + r.final);
    const firstWins = out.filter((r) => /^resolve\('a'\)|^reject\('a'\)|^throw/.test(r.label));
    const later2 = firstWins.filter((r) => !r.final.includes('"a"') && !r.final.includes("「a」"));
    console.log("rows with a plain first call where a later call decided the state: " + later2.length + " / " + firstWins.length);
  }, 0);
}, 0);
```

```text
===== node20 js36b-37a-transitions.js (exit=0) =====
[before p settles]
  resolve(p pending) · reject('b')                pending
[after everything settled]
  resolve('a') · resolve('b')                     fulfilled "a"
  resolve('a') · reject('b')                      fulfilled "a"
  reject('a') · resolve('b')                      rejected  "a"
  throw Error('a')                                rejected  Error 「a」
  resolve('a') · throw Error('b')                 fulfilled "a"
  resolve(p pending) · reject('b')                fulfilled "c"
  resolve(Promise.reject('r'))                    rejected  "r"
  resolve(thenable: onF('t'))                     fulfilled "t"
  resolve(thenable: onF('t') · onR('u') · throw)  fulfilled "t"
  resolve(object whose then getter throws)        rejected  Error 「g」
  resolve(the promise itself)                     rejected  TypeError 「Chaining cycle detected for promise #<Promise>」
rows with a plain first call where a later call decided the state: 0 / 5
```

```text
   CreateResolvingFunctions(promise)  — resolve 와 reject 가 나눠 쓰는 한 칸

        칸: [ promise ]
             │
   resolve(x) ─┤  칸이 비어 있으면 → return (아무것도 안 한다)       ← 둘째 호출부터 여기서 끝난다
   reject(e)  ─┘  칸을 비운다 (이제 둘 다 무력)
                  x 가 promise 자신          → TypeError 로 reject
                  x 가 객체가 아님            → fulfill(x)
                  x.then 을 읽다 던짐         → 그 예외로 reject
                  x.then 이 함수가 아님       → fulfill(x)
                  x.then 이 함수              → 잡 하나를 건다 (동작 (2))   ← 여기서 「잠김」 — 아직 pending
```

- ★★★ **집계 줄 — `rows with a plain first call where a later call decided the state: 0 / 5`.** 첫 호출이 평범한 값·이유·`throw` 인 다섯 행에서 **뒤의 호출이 이긴 행은 없다.**
  `resolve('a')` 뒤의 `throw` 도 **삼켜진다** — executor 의 예외는 **reject 를 부르는 것**인데, 칸이 이미 비었다.
- ★★★ **`resolve(p pending) · reject('b')`** — `resolve` 직후 **상태는 여전히 `pending`** 이다(`[before p settles]`). 그런데 **`reject('b')` 는 무시됐다** — 칸은 `resolve(p)` 가 이미 비웠다.
  나중에 `p` 가 `"c"` 로 이행하자 **`fulfilled "c"`** 가 됐다. **「pending」과 「아직 안 정해짐」은 다르다** — 잠긴 pending 이 있다.
- ★★ **`resolve(Promise.reject('r'))` 는 `rejected "r"`** — `resolve` 라는 이름으로 불러도 **따라간 쪽이 거부면 거부**다.
- ★★ **thenable 도 같은 규칙**이다 — `onF('t')` 뒤의 `onR('u')` 와 `throw` 는 무시된다(thenable 에 넘어간 두 함수도 **한 칸을 나눠 쓴다**).
- ★★ **④ `then` 게터가 던지면 그 예외가 거부 이유**(`Error 「g」`)이고, **자기 자신으로 `resolve` 하면 `TypeError 「Chaining cycle detected for promise #<Promise>」`** — 종류는 명세가, 문구는 V8 이 정한다.

### (2) ★★★ `resolve(thenable)` 이 먹는 틱 — 계수 잡으로 센다

**언제 쓰나** — 「이 `then` 이 저 `then` 보다 먼저 도나」가 **틱 하나 차이**로 갈리는 코드를 볼 때 · `then` 안에서 프라미스를 돌려주는 코드.
★★★ **계수 잡**이 한 틱에 한 번 스스로 다시 걸리며 `tick` 을 올린다. `then` 콜백이 돌 때 `tick` 을 읽는다(`@k` = 계수 잡이 **k 번** 돈 뒤). 행마다 `setTimeout` 으로 떼어 **서로 섞이지 않게** 했다.

```js
// js36b-37b-ticks.js
// Count microtask ticks. A counter job requeues itself once per tick; the probe's then callback reads the counter.
// Each row runs alone (the rows are separated by a setTimeout), so rows cannot disturb each other.
function measure(label, make) {
  return new Promise((done) => {
    let tick = 0, stop = false;
    const counter = () => { if (stop) return; tick++; queueMicrotask(counter); };
    const events = [];
    const p = make(events);
    p.then(() => { stop = true; events.push("then callback @" + tick); });
    queueMicrotask(counter);
    events.push("sync code done @" + tick);
    setTimeout(() => { console.log("  " + label.padEnd(44) + events.join(" > ")); done(); }, 0);
  });
}
const loggingThenable = (events) => ({
  get then() {
    events.push("get then");
    return (onF) => { events.push("then() called"); onF("t"); };
  },
});
(async () => {
  console.log("[1] new Promise((resolve) => resolve(X))");
  await measure("X = 'v'", () => new Promise((r) => r("v")));
  await measure("X = Promise.resolve('v')", () => new Promise((r) => r(Promise.resolve("v"))));
  await measure("X = thenable (then calls onF at once)", (ev) => new Promise((r) => r(loggingThenable(ev))));
  console.log("[2] Promise.resolve(X)");
  const q = Promise.resolve("v");
  console.log("  Promise.resolve(q) === q        " + (Promise.resolve(q) === q));
  await measure("Promise.resolve(Promise.resolve('v'))", () => Promise.resolve(Promise.resolve("v")));
  await measure("Promise.resolve(thenable)", (ev) => Promise.resolve(loggingThenable(ev)));
  console.log("[3] a then callback returns X -- ticks counted from the start");
  await measure("then(() => 'v')", () => Promise.resolve().then(() => "v"));
  await measure("then(() => Promise.resolve('v'))", () => Promise.resolve().then(() => Promise.resolve("v")));
})();
```

```text
===== node20 js36b-37b-ticks.js (exit=0) =====
[1] new Promise((resolve) => resolve(X))
  X = 'v'                                     sync code done @0 > then callback @0
  X = Promise.resolve('v')                    sync code done @0 > then callback @2
  X = thenable (then calls onF at once)       get then > sync code done @0 > then() called > then callback @1
[2] Promise.resolve(X)
  Promise.resolve(q) === q        true
  Promise.resolve(Promise.resolve('v'))       sync code done @0 > then callback @0
  Promise.resolve(thenable)                   get then > sync code done @0 > then() called > then callback @1
[3] a then callback returns X -- ticks counted from the start
  then(() => 'v')                             sync code done @0 > then callback @1
  then(() => Promise.resolve('v'))            sync code done @0 > then callback @3
```

같은 파일을 Chrome 151 에서 — **한 글자도 같다.**

```text
===== ./js36b-browser.sh js36b-37b-ticks.js (exit=0) =====
[1] new Promise((resolve) => resolve(X))
  X = 'v'                                     sync code done @0 > then callback @0
  X = Promise.resolve('v')                    sync code done @0 > then callback @2
  X = thenable (then calls onF at once)       get then > sync code done @0 > then() called > then callback @1
[2] Promise.resolve(X)
  Promise.resolve(q) === q        true
  Promise.resolve(Promise.resolve('v'))       sync code done @0 > then callback @0
  Promise.resolve(thenable)                   get then > sync code done @0 > then() called > then callback @1
[3] a then callback returns X -- ticks counted from the start
  then(() => 'v')                             sync code done @0 > then callback @1
  then(() => Promise.resolve('v'))            sync code done @0 > then callback @3
```

```text
   resolve(q) — q 는 이미 fulfilled 인 진짜 프라미스            큐 (왼쪽이 먼저)

   동기     resolve(q) → 잡 J1(q.then 을 불러라) 을 건다             [J1]
            p.then(cb) 등록 · 계수 잡 C 를 건다                      [J1 C]
   틱 0     J1: q.then(res, rej) — q 는 이미 fulfilled → 반응 J2 를 건다   [C J2]
   틱 1     C (tick=1)                                               [J2 C]
            J2: res("v") — 이제 p 가 fulfilled → cb 를 건다            [C cb]
   틱 2     C (tick=2)                                               [cb C]
            cb: then callback @2

   thenable 이 onF 를 곧바로 부르면 J2 가 없다 → @1
```

- ★★★ **값으로 `resolve` → `@0`, 진짜 프라미스로 → `@2`, `then` 이 곧바로 부르는 thenable 로 → `@1`.**
  진짜 프라미스는 **잡 둘**을 더 먹는다 — ① `NewPromiseResolveThenableJob` 이 `q.then` 을 부르는 잡, ② `q` 의 반응 잡(`q` 가 이미 이행했어도 `then` 은 콜백을 **잡으로** 건다).
  thenable 은 ①만 먹는다 — 그 `then` 이 **곧바로** `onF` 를 불렀기 때문이다.
- ★★★ **`then` 게터는 `resolve` 를 부른 그 자리에서(동기로) 읽히고, `then()` 호출은 잡 안에서** 일어난다 — `get then > sync code done @0 > then() called`. 명세의 순서 그대로다(`Get(resolution, "then")` 은 resolve 함수 안, 호출은 잡 안).
- ★★★ **`Promise.resolve(q) === q`** — 진짜 프라미스를 넘기면 **그대로 돌려준다.** 그래서 `@0` 이다(`new Promise(r => r(q))` 의 `@2` 와 다르다).
- ★★ **`then` 콜백이 프라미스를 돌려주면 `@3`**, 값을 돌려주면 `@1` — 같은 흡수 규칙이 **`then` 이 만든 새 프라미스**에도 걸린다(+2).
- ★ 이 틱 수는 **명세의 잡 개수**에서 나온다 — 두 node 판과 Chrome 151 이 같았다. 39번이 `await`·`return` 의 틱 수를 같은 창으로 잰다.

### (3) ★★ `then` 사슬 — 값과 예외가 흐르는 길

**언제 쓰나** — `.then().then().catch()` 사슬에서 **어느 처리기가 돌고 어느 것이 건너뛰어지나**를 읽을 때.

```js
// js36b-37c-chain.js
// [1] One chain. Every handler that runs prints a line; a handler that does not run prints nothing.
// [2] upstream (fulfilled 'T' / rejected Error T) x what the finally callback does -> what the caller receives.
const show = (x) => (x instanceof Error ? "Error 「" + x.message + "」" : JSON.stringify(x));
const log = (s) => console.log(s);
(async () => {
  log("[1] a chain");
  await Promise.resolve(1)
    .then((v) => { log("  h1 got " + show(v)); return v + 1; })
    .then((v) => { log("  h2 got " + show(v)); throw new Error("from h2"); })
    .then((v) => { log("  h3 got " + show(v)); return "h3"; })
    .then(undefined, undefined)
    .catch((e) => { log("  h4 (catch) got " + show(e)); return "from h4"; })
    .then((v) => { log("  h5 got " + show(v)); return Promise.reject(new Error("from h5")); })
    .then((v) => { log("  h6 got " + show(v)); }, (e) => { log("  h6 (second argument) got " + show(e)); })
    .finally((...a) => { log("  h7 (finally) got " + a.length + " arguments"); })
    .then((v) => log("  h8 got " + show(v)));

  log("[2] Promise.prototype.finally grid");
  const ups = [["fulfilled 'T'", () => Promise.resolve("T")], ["rejected Error T", () => Promise.reject(new Error("T"))]];
  const fins = [
    ["returns nothing", () => {}],
    ["returns 'F'", () => "F"],
    ["throws Error F", () => { throw new Error("F"); }],
    ["returns Promise.reject(Error F)", () => Promise.reject(new Error("F"))],
  ];
  let lost = 0, n = 0;
  for (const [u, mk] of ups) for (const [f, fn] of fins) {
    let got;
    try { got = "value " + show(await mk().finally(fn)); } catch (e) { got = "threw " + show(e); }
    const reached = got.includes("T");
    n++; if (!reached) lost++;
    log("  " + u.padEnd(18) + f.padEnd(33) + got.padEnd(20) + "upstream reached caller: " + reached);
  }
  log("cells where the upstream outcome did not reach the caller: " + lost + " / " + n);
})();
```

```text
===== node20 js36b-37c-chain.js (exit=0) =====
[1] a chain
  h1 got 1
  h2 got 2
  h4 (catch) got Error 「from h2」
  h5 got "from h4"
  h6 (second argument) got Error 「from h5」
  h7 (finally) got 0 arguments
  h8 got undefined
[2] Promise.prototype.finally grid
  fulfilled 'T'     returns nothing                  value "T"           upstream reached caller: true
  fulfilled 'T'     returns 'F'                      value "T"           upstream reached caller: true
  fulfilled 'T'     throws Error F                   threw Error 「F」     upstream reached caller: false
  fulfilled 'T'     returns Promise.reject(Error F)  threw Error 「F」     upstream reached caller: false
  rejected Error T  returns nothing                  threw Error 「T」     upstream reached caller: true
  rejected Error T  returns 'F'                      threw Error 「T」     upstream reached caller: true
  rejected Error T  throws Error F                   threw Error 「F」     upstream reached caller: false
  rejected Error T  returns Promise.reject(Error F)  threw Error 「F」     upstream reached caller: false
cells where the upstream outcome did not reach the caller: 4 / 8
```

```text
   [1] 의 흐름

   1 ─h1─▶ 2 ─h2─▶ ✗(from h2) ─h3 건너뜀─▶ ✗ ─then(undefined, undefined)─▶ ✗ ─h4(catch)─▶ "from h4"
                                                                          (값을 돌려줘서 이행으로 돌아온다)
   ─h5─▶ ✗(from h5: 거부된 프라미스를 돌려줬다) ─h6(둘째 인자)─▶ undefined ─h7(finally, 인자 0개)─▶ undefined ─h8─▶

   처리기가 없는 칸(h3 의 거부 쪽 · then(undefined, undefined))은 받은 것을 그대로 넘긴다
```

- ★★★ **`then(f)` 는 거부를 건너뛴다** — `h3` 은 안 찍혔다. 처리기가 없는 쪽은 **받은 것을 그대로 새 프라미스에 넘긴다**(`then(undefined, undefined)` 도 그렇다).
- ★★★ **처리기가 던지면 거부, 값을 돌려주면 이행** — `catch` 도 예외가 아니다. `h4` 가 `"from h4"` 를 돌려주자 사슬이 **이행으로 돌아왔다.**
- ★★ **거부된 프라미스를 돌려줘도 거부**다(`h5` → `h6` 둘째 인자). 동작 (2)의 흡수 규칙이다.
- ★★ **`finally` 콜백은 인자를 받지 않는다**(`0 arguments`) — 앞이 이행이었는지 거부였는지 **모른다.**

### (4) ★★★ `.finally()` 격자 — 값을 통과시킨다, `try`/`finally` 와 다르다

**언제 쓰나** — 로딩 표시 끄기·연결 닫기를 `.finally()` 에 넣을 때 · 32번의 `finally` 규칙을 그대로 옮겨 생각할 때.
★★★ 위 소스의 `[2]` 다 — 상류 2(이행 `'T'` · 거부 `Error T`) × `finally` 콜백 4 = **8칸**.

```text
                                   try/finally (32번 · 9칸)            .finally(cb) (이 격자 · 8칸)

   finally 가 조용히 끝남           try 의 것이 나간다                  상류의 것이 나간다
   finally 가 값 'F' 를 돌려줌      ★ 'F' 가 나간다 (return 'F')          ★ 상류의 것이 나간다 — 'F' 는 버려진다
   finally 가 던짐                  finally 의 예외가 나간다             cb 의 예외가 나간다
   finally 가 거부된 프라미스        (해당 없음)                          그 거부가 나간다

   닿지 못한 칸                     6 / 9                                4 / 8
```

- ★★★ **집계 줄 — `cells where the upstream outcome did not reach the caller: 4 / 8`.** 닿지 못한 넷은 **전부 콜백이 던지거나 거부된 프라미스를 돌려준 칸**이다.
- ★★★ **콜백이 `'F'` 를 돌려줘도 호출자는 `"T"`**(또는 `Error 「T」`)를 받는다 — **`.finally()` 는 값을 통과시킨다.**
  32번의 `try`/`finally` 에서는 **`finally` 의 `return 'F'` 가 `try` 의 것을 버렸다**(32번 동작 (1) — `6 / 9`). **같은 이름, 다른 규칙**이다.
- ★★ 명세의 모양 그대로다 — `thenFinally` 는 콜백을 부르고 그 결과를 `PromiseResolve` 로 감싼 뒤 **「원래 `value` 를 돌려주는 함수」** 를 `then` 에 건다. 콜백의 **값은 기다리기만 하고 버린다.** 던지거나 거부되면 그 `then` 이 거부로 끝난다.

### (5) ★★★ 미처리 거부 — 언제 보고되나(node 두 판 · Chrome)

**언제 쓰나** — 거부될 수 있는 프라미스를 만들고 **나중에** `catch` 를 붙이는 코드 · 서버가 「unhandled rejection」으로 죽었을 때.
★★★ **node 는 행마다 새 프로세스**다. `hooks` 가 있으면 `process.on('unhandledRejection')` · `'rejectionHandled'` 가 **표준 출력**에 찍고, 없으면 **종료 코드**와 「표준 오류에 `ERR_UNHANDLED_REJECTION` 이 있나」만 본다.

```js
// js36b-37-h-late-catch.js
// A promise is rejected at once. When is the catch attached? (argv[2]) Are node's hooks installed? (argv[3])
const when = process.argv[2], hooks = process.argv[3] === "hooks";
if (hooks) {
  process.on("unhandledRejection", (reason) => console.log("unhandledRejection(" + reason + ")"));
  process.on("rejectionHandled", () => console.log("rejectionHandled"));
}
const p = Promise.reject("R");
const attach = () => p.catch(() => console.log("catch ran"));
if (when === "same-tick") attach();
if (when === "next-microtask") queueMicrotask(attach);
if (when === "3rd-microtask") Promise.resolve().then().then().then(attach);
if (when === "setTimeout-0") setTimeout(attach, 0);
if (when === "setImmediate") setImmediate(attach);
if (when === "never") { /* nothing is attached */ }
```

```sh
# js36b-37d-unhandled-node.sh
#!/usr/bin/env bash
# One row per "when the catch is attached", for node18 and node20.
#   with hooks : what node's process events printed (standard output), then the exit code
#   no hooks   : the exit code, and whether standard error mentions ERR_UNHANDLED_REJECTION
set -u -o pipefail
cd "$(dirname "$0")"
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
cases="same-tick next-microtask 3rd-microtask setTimeout-0 setImmediate never"
declare -A row
for v in 18 20; do
  [ $v = 18 ] && n="$N18" || n="$N20"
  echo "--- node$v"
  printf '  %-16s %-52s %-9s %s\n' "catch attached" "with hooks: stdout" "exit" "no hooks: exit · ERR_UNHANDLED_REJECTION on stderr"
  for c in $cases; do
    out="$("$n" js36b-37-h-late-catch.js "$c" hooks | paste -sd' ' -)"; e1=$?
    err="$("$n" js36b-37-h-late-catch.js "$c" 2>&1 >/dev/null)"; e2=$?
    case $err in *ERR_UNHANDLED_REJECTION*) m=yes ;; *) m=no ;; esac
    line="$(printf '  %-16s %-52s %-9s %s' "$c" "$out" "$e1" "$e2 · $m")"
    printf '%s\n' "$line"
    row[$v,$c]="$line"
  done
done
d=0; t=0
for c in $cases; do t=$((t + 1)); [ "${row[18,$c]}" = "${row[20,$c]}" ] || d=$((d + 1)); done
echo ""
echo "rows where node18 and node20 differ: $d / $t"
```

```text
===== ./js36b-37d-unhandled-node.sh (exit=0) =====
--- node18
  catch attached   with hooks: stdout                                   exit      no hooks: exit · ERR_UNHANDLED_REJECTION on stderr
  same-tick        catch ran                                            0         0 · no
  next-microtask   catch ran                                            0         0 · no
  3rd-microtask    catch ran                                            0         0 · no
  setTimeout-0     unhandledRejection(R) catch ran rejectionHandled     0         1 · yes
  setImmediate     unhandledRejection(R) catch ran rejectionHandled     0         1 · yes
  never            unhandledRejection(R)                                0         1 · yes
--- node20
  catch attached   with hooks: stdout                                   exit      no hooks: exit · ERR_UNHANDLED_REJECTION on stderr
  same-tick        catch ran                                            0         0 · no
  next-microtask   catch ran                                            0         0 · no
  3rd-microtask    catch ran                                            0         0 · no
  setTimeout-0     unhandledRejection(R) catch ran rejectionHandled     0         1 · yes
  setImmediate     unhandledRejection(R) catch ran rejectionHandled     0         1 · yes
  never            unhandledRejection(R)                                0         1 · yes

rows where node18 and node20 differ: 0 / 6
```

```text
   node — 콜백 하나(여기서는 메인 스크립트)가 끝난 뒤

   스크립트 끝 ─▶ nextTick·마이크로태스크 비우기 ─▶ 「거부됐는데 아직 처리기 없는 것」 을 본다 ─▶ 다음 단계(타이머 …)
                   (same-tick · next-microtask ·        │
                    3rd-microtask 의 catch 가            ├─ hooks 있음 → unhandledRejection(R) 이벤트
                    여기서 이미 달린다 → 보고 없음)        └─ hooks 없음 → 기본 모드 throw → 종료 코드 1
                                                                      (setTimeout-0 의 catch 는 끝내 못 돈다)
```

- ★★★ **같은 틱 · 다음 마이크로태스크 · 세 번째 마이크로태스크 — 보고 없음, `exit 0`.** 마이크로태스크를 다 비운 **뒤에** 보므로, 그 안에 달리면 늦지 않다.
- ★★★ **다음 매크로태스크(`setTimeout` 0 · `setImmediate`) — 보고된다.** 훅이 있으면 `unhandledRejection(R)` → `catch ran` → **`rejectionHandled`**(뒤늦게 달린 것도 알린다), 훅이 없으면 **`exit 1`** 이고 `catch` 는 **돌 기회조차 없다.**
- ★★★ **훅이 있으면 기본 모드에서도 `exit 0`** 이다 — node 문서의 `throw` 모드: 「`unhandledRejection` 을 쏜다. **이 훅이 없으면** 미처리 예외로 올린다.」
- ★★★ **`rows where node18 and node20 differ: 0 / 6`** — 두 판 모두 v15 이후라 기본이 `throw` 다.

훅이 없을 때 node20 이 표준 오류에 적는 것 — 기본 모드와 `--unhandled-rejections=warn`(표준 출력은 버렸다).

```sh
# js36b-37e-unhandled-stderr.sh
#!/usr/bin/env bash
# The "never" row with no hooks: what node20 writes to standard error (standard output is thrown away),
# once with the default mode and once with --unhandled-rejections=warn.
set -u -o pipefail
cd "$(dirname "$0")"
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
for flag in "" "--unhandled-rejections=warn"; do
  echo "--- node20${flag:+ $flag} js36b-37-h-late-catch.js never"
  "$N20" $flag js36b-37-h-late-catch.js never 2>&1 >/dev/null
  echo "(exit $?)"
done
```

```text
===== ./js36b-37e-unhandled-stderr.sh (exit=0) =====
--- node20 js36b-37-h-late-catch.js never
node:internal/process/promises:389
      new UnhandledPromiseRejection(reason);
      ^

UnhandledPromiseRejection: This error originated either by throwing inside of an async function without a catch block, or by rejecting a promise which was not handled with .catch(). The promise rejected with the reason "R".
    at throwUnhandledRejectionsMode (node:internal/process/promises:389:7)
    at processPromiseRejections (node:internal/process/promises:470:17)
    at process.processTicksAndRejections (node:internal/process/task_queues:96:32) {
  code: 'ERR_UNHANDLED_REJECTION'
}

Node.js v20.19.6
(exit 1)
--- node20 --unhandled-rejections=warn js36b-37-h-late-catch.js never
(node:212044) UnhandledPromiseRejectionWarning: R
(Use `node --trace-warnings ...` to show where the warning was created)
(node:212044) UnhandledPromiseRejectionWarning: Unhandled promise rejection. This error originated either by throwing inside of an async function without a catch block, or by rejecting a promise which was not handled with .catch(). To terminate the node process on unhandled promise rejection, use the CLI flag `--unhandled-rejections=strict` (see https://nodejs.org/api/cli.html#cli_unhandled_rejections_mode). (rejection id: 1)
(exit 0)
```

- ★★ **기본 모드는 `exit 1`**, **`warn` 모드는 경고만 적고 `exit 0`** 이다 — **같은 코드의 종료 코드가 명령줄 플래그 하나로 바뀐다.** 거부를 보고하는 방식이 **호스트의 설정**이라는 증거다.
- ★★ 이유가 **문자열 `"R"`** 이라 호출 경로가 없다 — 스택은 **node 내부**(`node:internal/process/promises`)뿐이다. 32번 동작 (6)의 「**`Error` 가 아닌 값을 던지면 스택이 없다**」와 같은 이야기다.

**Chrome 151** — 한 페이지에 다섯 프라미스, 이유가 곧 이름이다.

```js
// js36b-37f-unhandled.web.js
// Chrome. Five promises rejected at once, each with its own reason; the catch is attached at different moments.
// Every event the page receives is printed with the reason it carries.
addEventListener("unhandledrejection", (e) => console.log("unhandledrejection(" + e.reason + ")"));
addEventListener("rejectionhandled", (e) => console.log("rejectionhandled(" + e.reason + ")"));
const make = (reason, attachLater) => {
  const p = Promise.reject(reason);
  attachLater(() => p.catch(() => console.log("catch ran(" + reason + ")")));
};
make("same-tick", (a) => a());
make("next-microtask", (a) => queueMicrotask(a));
make("setTimeout-0", (a) => setTimeout(a, 0));
make("setTimeout-0-twice", (a) => setTimeout(() => setTimeout(a, 0), 0));
make("never", () => {});
```

```text
===== ./js36b-browser.sh js36b-37f-unhandled.web.js (exit=0) =====
catch ran(same-tick)
catch ran(next-microtask)
catch ran(setTimeout-0)
unhandledrejection(setTimeout-0-twice)
unhandledrejection(never)
catch ran(setTimeout-0-twice)
rejectionhandled(setTimeout-0-twice)
```

```text
   HTML — 마이크로태스크 체크포인트 끝에서

   체크포인트 끝 ─▶ 「알릴 목록」 을 복사해 두고 ─▶ 태스크 하나를 큐에 넣는다 ──▶ (그 태스크가 돌 때)
                                                                       아직 처리기 없는 것만 unhandledrejection
   setTimeout-0 의 catch       ── 이 태스크보다 먼저 돌았다(이 판의 관찰) → 보고 없음
   setTimeout-0-twice 의 catch ── 그 뒤 → unhandledrejection, 그다음 rejectionhandled
```

- ★★★ **Chrome 에서는 `setTimeout-0` 이 보고되지 않았다** — node 에서는 같은 자리가 **보고됐다**(위 격자). **「다음 매크로태스크」의 뜻이 호스트마다 다르다.**
  HTML 은 알림을 **태스크 하나로** 미루는데, 그 태스크(DOM 조작 태스크 원천)와 타이머 태스크 중 무엇이 먼저인지는 **HTML 이 정하지 않는다** — 이 순서는 **Chrome 151 의 관찰**이다(가상 시간 예산 아래 — 제출 전 재캡처에서도 같았다).
- ★★ **`setTimeout` 을 두 번 거친 `catch` 는 보고된 뒤 `rejectionhandled`** 가 따라왔다 — node 의 `rejectionHandled` 와 같은 모양이다.
- ★ **이벤트 이름이 다르다** — Chrome 은 `unhandledrejection`(소문자), node 는 `unhandledRejection`. 둘 다 **호스트의 것**이다.

★★★ **같은 페이지를 `--allow-file-access-from-files` 없이** 열면 — 이벤트가 **하나도** 안 온다.

```text
===== ./js36b-browser.sh --muted js36b-37f-unhandled.web.js (exit=0) =====
catch ran(same-tick)
catch ran(next-microtask)
catch ran(setTimeout-0)
catch ran(setTimeout-0-twice)
```

- ★★★ **`unhandledrejection` 이 0 줄**이다 — 거부는 여전히 두 개 남았는데. HTML 의 `HostPromiseRejectionTracker` 첫 단계가 「**running script 가 classic script 이고 muted errors 가 참이면 return**」이다.
  `file://` 로 불러온 스크립트는 **교차 출처**로 취급되어 muted 가 된다 — **거부가 없는 것이 아니라 보고를 안 하는 것**이다(규칙 18-B 의 「안 보인다는 없다가 아니다」).
- ★ 그래서 이 배치의 Chrome 블록은 **전부 그 플래그를 켜고** 떴다(`js36b-browser.sh` 의 기본값). 앞 배치들의 페이지(`js24b`·`js32b`)도 `unhandledrejection` 리스너를 걸어 두었는데 **이 플래그 없이 떴다** — 그 리스너가 찍은 줄은 그 배치들의 문서에 **한 줄도 없다**(들을 수 없었으니 당연하다).

## 문법 — 형태와 규칙

★ 이 절은 **형태 표**다 — 모든 동작 주장은 위 동작 절의 캡처 블록에서만 한다.

| 형태 | 하는 일 | 판 | 어디서 봤나 |
|---|---|---|---|
| `new Promise((resolve, reject) => { … })` | executor 를 **지금** 부른다 · 두 함수는 **한 칸을 나눠 쓴다** · executor 의 `throw` 는 `reject` | ES2015 | 동작 (1) |
| `resolve(x)` | `x` 가 thenable 이면 **잡 하나로** 따라간다(잠긴 pending) · 아니면 이행 | ES2015 | 동작 (1)·(2) |
| `Promise.resolve(x)` | `x` 가 **같은 생성자의 프라미스면 그대로** 돌려준다 | ES2015 | 동작 (2) |
| `p.then(onF, onR)` | **새 프라미스** — 처리기가 없는 쪽은 그대로 넘긴다 · 던지면 거부 · 프라미스를 돌려주면 따라간다 | ES2015 | 동작 (3) |
| `p.catch(onR)` | `then(undefined, onR)` | ES2015 | 동작 (3) |
| `p.finally(cb)` | `cb()` 를 인자 없이 부르고 **상류의 것을 통과** — `cb` 가 던지거나 거부되면 그것 | **ES2018** | 동작 (4) |

- **처음 호출만 효력이 있다.** 뒤의 `resolve`·`reject`·`throw` 는 **에러 없이** 버려진다.
- **거부는 처리기를 만날 때까지 사슬을 따라 흐른다.** 처리기가 값을 돌려주면 이행으로 돌아온다.
- **처리기는 거부를 「받자마자」가 아니라 「그 바퀴가 끝나기 전에」 달면 된다** — 마이크로태스크 안이면 늦지 않다(node · Chrome 둘 다).

## 어디서 틀리나

### (1) ★★★ `resolve()` 뒤의 코드가 던진 예외가 어딘가에서 잡힐 것이라 믿는다

**삼켜진다**(동작 (1)의 `resolve('a') · throw Error('b')` → `fulfilled "a"`). 경고도 없다. executor 안에서는 `resolve` 를 **마지막**에 부른다.

### (2) ★★★ `resolve(p)` 직후 상태가 정해졌다고 믿는다

**여전히 `pending`** 이다 — 잠겼을 뿐이다. 이후 `reject` 는 무시되고, 결과는 **`p` 가 정한다**(`fulfilled "c"`).

### (3) ★★★ `.finally()` 에서 값을 돌려주면 결과가 바뀐다고 믿는다

**안 바뀐다**(`4 / 8` 격자의 `returns 'F'` 두 칸). 32번의 `try`/`finally` 와 **반대**다. 결과를 바꾸려면 `.then` 을 쓴다. **던지면 바뀐다.**

### (4) ★★★ 거부될 수 있는 프라미스를 만들어 두고 `setTimeout` 뒤에 `catch` 를 단다

**node 는 기본 모드에서 그 전에 죽는다**(`exit 1`, `catch` 는 못 돈다). 처리기는 **만든 바퀴 안에** 단다 — 나란히 시작해 차례로 `await` 하는 코드가 이 모양이 된다(39번 동작 (4)).

### (5) ★★ `process.on('unhandledRejection', log)` 을 달아 두면 여전히 죽는 줄 안다

**훅이 있으면 기본 모드에서도 `exit 0`** 이다 — 로그만 남기고 **계속 돈다.** 죽이고 싶으면 훅 안에서 직접 끝낸다(또는 `strict` 모드 — 이 문서는 돌리지 않았다).

### (6) ★★ 「다음 매크로태스크에 달면 보고된다」를 호스트 무관한 규칙으로 외운다

**node 는 보고했고 Chrome 151 은 안 했다**(`setTimeout-0` 행). 알림 시점은 **호스트**가 정한다.

### (7) ★★ `file://` 로 연 테스트 페이지에서 `unhandledrejection` 이 안 오니 거부가 없다고 믿는다

**muted errors** 라서 **보고를 안 한 것**이다(동작 (5)의 마지막 블록). 로컬 서버로 열거나, 헤드리스라면 `--allow-file-access-from-files`.

### (8) ★★ 「`resolve(thenable)` 은 틱 두 개를 더 먹는다」를 모든 thenable 에 적용한다

**진짜 프라미스는 +2, `then` 이 곧바로 부르는 thenable 은 +1** 이었다(동작 (2)). 틱 수는 **그 `then` 이 무엇을 하느냐**에 달려 있다.

### (9) ★ 사슬 중간의 `then(f)` 가 거부도 받을 것이라 믿는다

**안 받는다** — `h3` 은 안 찍혔다. 둘째 인자나 `catch` 가 받는다.

## 구현 세부사항 대 언어 보장

### 명세 보장(ECMA-262)

- ★★★ `CreateResolvingFunctions` — resolve·reject 가 **한 칸을 나눠 쓰고**, 처음 불린 쪽이 칸을 비우면 **둘 다 무력**해진다. 자기 자신 → `TypeError` · 비객체 → 이행 · `then` 게터가 던짐 → 거부 · `then` 이 함수 → **잡 하나**.
- ★★★ `NewPromiseResolveThenableJob` — thenable 의 `then` 을 **잡 안에서** 부른다(그래서 `then()` 호출이 동기 코드 뒤에 온다).
- ★★ `then` 은 **새 프라미스**를 만들고, 처리기의 결과로 그것을 resolve 한다(같은 흡수 규칙). `finally` 는 콜백 결과를 기다린 뒤 **원래 값을 돌려준다.**
- ★★ **`HostPromiseRejectionTracker`** — 처리기 없는 프라미스가 거부되면 `"reject"`, 거부된 프라미스에 처리기가 **처음** 달리면 `"handle"`. **기본 구현은 아무것도 안 한다** — 보고는 호스트의 몫이다.

### 호스트 — HTML

- ★★ 훅을 받아 **「알릴 목록」에 넣고**, 체크포인트 끝에서 **태스크 하나로** `unhandledrejection` 을 쏜다. 그 전에 처리기가 달리면 목록에서 빠진다. 쏜 뒤에 달리면 `rejectionhandled`.
- ★★★ **muted errors 인 classic script 에서는 아무것도 안 한다.**

### 호스트 — node

- ★★★ 기본 모드 `throw` — 훅이 있으면 이벤트만, **없으면 미처리 예외 → 종료 코드 1**. `warn` 모드는 경고 + `exit 0`.
- ★★ `rejectionHandled` 는 「**한 바퀴보다 늦게** 처리기가 달렸을 때」(node 문서).

### 구현(V8) · 이 판의 관찰

- 예외 문구 — `Chaining cycle detected for promise #<Promise>`.
- ★★ **Chrome 151 에서 `setTimeout` 0 의 `catch` 가 알림 태스크보다 먼저 돈 것** — HTML 이 두 태스크 원천의 순서를 정하지 않으므로 **관찰**이다.
- 틱 수가 두 node 판과 Chrome 에서 같았다 — 틱 수 자체는 **명세의 잡 개수**가 정한다.

### 그래서 이렇게 적으면 틀린다

- ✗ 「`resolve` 하면 fulfilled 가 된다」 → ○ 「**thenable 로 `resolve` 하면 잠긴 pending** 이 되고, 그것을 따라간다 — 거부로 끝날 수도 있다」
- ✗ 「`finally` 는 `try`/`finally` 처럼 결과를 덮어쓸 수 있다」 → ○ 「**값은 통과**, 던지거나 거부될 때만 덮는다 — `4 / 8`」
- ✗ 「JavaScript 는 미처리 거부에서 프로세스를 죽인다」 → ○ 「**언어는 훅만 부른다.** node 기본 모드가 죽이고, 브라우저는 이벤트를 쏜다」
- ✗ 「`then` 은 느리다」 → ○ **안 쟀다** — 틱을 **셌다**

## 언제 쓰고 언제 안 쓰나

- **`new Promise(executor)`** — 콜백 API 를 감쌀 때만. `resolve`·`reject` 를 **한 번만** 부르는 구조로 쓴다. 이미 프라미스인 것을 감싸지 않는다(틱만 는다 — 동작 (2)의 `@2`).
- **`Promise.resolve(x)`** — 값이든 프라미스든 **프라미스로 맞출 때.** 진짜 프라미스면 그대로 돌아온다.
- **`.catch`** — 사슬 **끝**에 하나. 처리기는 **만든 바퀴 안에** 단다.
- **`.finally`** — 정리(로딩 끄기·닫기). **결과를 바꾸는 데 쓰지 않는다.**
- ★ **안 쓰는 자리** — `process.on('unhandledRejection')` 으로 오류를 **처리**하는 것(보고와 기록용이다) · `file://` 페이지로 거부 보고를 시험하는 것.

## 핵심 문장

1. ★★★ 프라미스의 결과는 **처음 온 호출**이 정한다 — resolve·reject 가 한 칸을 나눠 쓰고, 뒤의 호출과 `throw` 는 **에러 없이** 버려진다(`0 / 5`).
2. ★★★ **thenable 로 `resolve` 하면 잠긴 pending** 이 되고 **잡으로** 따라간다 — 진짜 프라미스는 **+2 틱**, 곧바로 부르는 thenable 은 **+1 틱**이었다.
3. ★★ `then` 은 **새 프라미스**를 만든다 — 처리기가 없으면 통과, 던지면 거부, 값을 돌려주면 이행.
4. ★★★ **`.finally()` 는 값을 통과시킨다** — 닿지 못한 칸 **`4 / 8`**(던지거나 거부될 때만). 32번 `try`/`finally` 의 **`6 / 9`** 와 규칙이 다르다.
5. ★★★ **미처리 거부는 언어가 아니라 호스트가 보고한다** — node 는 마이크로태스크를 다 비운 뒤 보고하고 기본 모드에서 **`exit 1`**(두 판 `0 / 6`), Chrome 151 은 `setTimeout` 0 에 단 것은 **보고하지 않았고**, `file://` 스크립트면 **아무것도** 보고하지 않는다.

## 관련 자료

- [ECMA-262 — Promise Objects](https://tc39.es/ecma262/multipage/control-abstraction-objects.html#sec-promise-objects) · [HTML — Unhandled promise rejections](https://html.spec.whatwg.org/multipage/webappapis.html#unhandled-promise-rejections)
- [Node.js v20 — `--unhandled-rejections`](https://nodejs.org/docs/latest-v20.x/api/cli.html#--unhandled-rejectionsmode) · [process 이벤트](https://nodejs.org/docs/latest-v20.x/api/process.html#event-unhandledrejection)
- [`history/js/04-비동기-진화.md`](../../../../../../history/js/04-비동기-진화.md) — ★ **경계**: 그쪽은 **Promise 가 왜 나왔나와 평탄화의 뜻**까지, 여기는 **전이·틱·보고를 재는 것**부터.
- [36 — 이벤트 루프와 마이크로태스크](../36-event-loop-and-microtasks/2-summary.md) — 틱과 체크포인트. [32 — 오류 처리와 `Error`](../32-error-handling-and-error/2-summary.md) — `try`/`finally` 의 `6 / 9` · `Error` 가 아닌 값의 스택.
- [38 — Promise 조합기](../38-promise-combinators/2-summary.md) · [39 — `async`/`await`](../39-async-await/2-summary.md).

## 용어 풀이

- **pending · fulfilled · rejected** — 대기 · 이행 · 거부. 뒤의 둘을 합쳐 **settled**.
- **잠김(locked in)** — thenable 로 `resolve` 되어 **더는 다른 호출에 반응하지 않지만 아직 pending** 인 상태. 이 문서의 말이 아니라 흔히 쓰는 말이다.
- **thenable** — `then` 이 함수인 객체.
- **resolving functions** — executor 가 받는 `resolve`·`reject`. 한 칸을 나눠 쓴다.
- **반응 잡(reaction job)** — `then` 에 건 처리기를 도는 마이크로태스크.
- **`HostPromiseRejectionTracker`** — 거부를 추적하라고 **호스트에 넘기는** 명세의 훅.
- **muted errors** — 교차 출처 classic script 의 오류를 페이지에 감추는 HTML 의 표시. 미처리 거부 보고도 끈다.
- **`unhandledRejection` / `rejectionHandled`** — node 의 process 이벤트. **`unhandledrejection` / `rejectionhandled`** — HTML 의 window 이벤트.

## 더 들어가면

- **`--unhandled-rejections=strict`** — 훅이 있어도 죽인다고 node 문서가 적는다. **이 문서는 돌리지 않았다.**
- **`Promise` 를 상속한 생성자**(`SpeciesConstructor`) — `then`·`finally` 가 새 프라미스를 **어느 생성자로** 만드나. 이 문서는 기본 `Promise` 만 봤다.
- **가비지 컬렉션과 거부 추적** — 명세 노트는 `"handle"` 때 프라미스를 붙들지 말라고 적는다. 재지 않았다.
