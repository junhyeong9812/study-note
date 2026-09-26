# js/syntax/39 — `async`/`await`: 「부르면 첫 `await` 까지 지금 돌고, 늘 프라미스를 돌려주고, `await` 마다 틱 하나 이상 쉰다」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> ★★★ **이 주제의 본체는 ① 추상 연산에 로그 심기다** — `async` 함수 본문의 줄마다, 호출한 쪽의 다음 줄에, **`await` 가 멈추고 다시 도는 지점**마다 로그를 심는다.
> 틱 수는 37번의 **계수 잡**으로 센다(동작 (2)). ★★★ **순차 대 병렬은 시간이 아니라 「시작 로그의 순서」로** 가른다 — **`b` 가 `a` 가 끝나기 전에 시작했나**(참/거짓)를 스크립트가 찍는다(동작 (3)).
> ★★ 보조로 **② 전수 격자**(반환 모양 4 · 틱 6행 · 순차/병렬 4행)와 **④ 예외의 `constructor.name` + `message`**(`catch` 가 잡았나 · 최상위 `await` 의 `SyntaxError`)를 쓴다.
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262 — Async Function Abstract Operations · `Await`](https://tc39.es/ecma262/multipage/control-abstraction-objects.html#sec-async-function-objects) — `Await(arg)`: 「`PromiseResolve(%Promise%, arg)` → `PerformPromiseThen(promise, onFulfilled, onRejected)` → 호출자 문맥으로 돌아간다」
> - [TC39 finished proposals](https://github.com/tc39/proposals/blob/main/finished-proposals.md) — 판 경계(Async functions **2017** · Top-level `await` **2022**)
> - [Node.js v20 — `--unhandled-rejections`](https://nodejs.org/docs/latest-v20.x/api/cli.html#--unhandled-rejectionsmode) — 동작 (4)의 `exit 1` 이 어디서 오나(37번과 같다)
>
> ★★★ **명세 조항 번호는 인용하지 않는다.** 규칙 진술은 **추상 연산 이름**으로, 순서·틱 수·예외는 **전부 실행으로** 접지했다.
>
> **실행 검증** — 이 문서의 모든 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다.
> 배너의 `node20` 은 `~/.nvm/versions/node/v20.19.6/bin/node`, `node18` 은 기본 PATH 의 `node`(v18.19.1)다. 파이썬은 3.12.
> ★★ **이 주제의 node 탐침은 두 node 판과 Chrome 151 에서 한 글자도 같았다**(아래 대조기의 집계 줄 · Chrome 은 `./js36b-browser.sh` — 소스는 [36번](../36-event-loop-and-microtasks/2-summary.md)).
> ★★★ **시간은 한 번도 재지 않았다** — 「병렬이 빠르다」·「`await` 가 느리다」를 **쓰지 않는다.**
>
> **버전**
>
> | 무엇 | 판 | 이 머신에서 |
> |---|---|---|
> | `async function` · `await` · `async` 화살표 · `async` 메서드 | **ES2017** | 세 판 다 있다 |
> | 최상위 `await`(모듈 코드에서만) | **ES2022** | node 18 · 20 둘 다 ES 모듈에서 돌았다(동작 (7)) |
>
> ★★ **판 경계는 TC39 finished proposals 표와 이 목록의 README 를 대조했다** — Async functions **2017** · Top-level `await` **2022**. README 39행은 판을 적지 않는다.
>
> **★★★ 이 주제가 쓰는 창 — 그리고 부적용인 창**
>
> | 창 | 이 주제에서 무엇을 보나 |
> |---|---|
> | ★★★ **① 추상 연산에 로그 심기**(본체) | 본문 줄 · 호출자의 다음 줄 · `await` 뒤 — **어느 줄이 먼저 찍히나**(동작 (1)·(3)·(4)·(5)) · 계수 잡의 `@k`(동작 (2)) |
> | ★★ **② 전수 격자** | 반환 모양 4행 · 틱 6행 · 순차/병렬 4행 — 마지막 칸 「`b started before a ended`」 를 스크립트가 찍는다 |
> | ★★ **④ 예외의 `constructor.name` + `message`** | `return` 과 `return await` 에서 **`catch` 가 잡았나** · CommonJS 의 최상위 `await` → `SyntaxError` |
> | ★ **창을 바꿔 물었다**(제5의 상태) | 「`async` 함수는 제너레이터 + 프라미스 러너인가」를 **명세 비교가 아니라 로그 비교**로 물었다 — 옆에서 도는 다른 마이크로태스크와 **한 줄씩 같은가**(동작 (8)) |
> | ★ **부적용 — ③ 브랜드 태그** | 판정할 객체의 종류가 없다(반환값이 `Promise` 인지는 `instanceof` 로 충분했다) |
> | ★ **안 쟀다 — 시간** | ★★★ 순차 대 병렬을 **시간으로 재지 않았다.** 「시작 로그의 순서」가 전부다 |
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 판별 블록의 판 문자열 — 머신에 매인다 | ★★★ 모든 로그의 **줄 순서** · `@k` · `true`/`false` — 걸음은 전부 **마이크로태스크나 `setTimeout` 0 하나씩**이고, 같은 지연의 타이머는 등록 순서다(36번) |
> | ★ **이 주제의 탐침에는 재실행에서 흔들린 칸이 없다**(재대조 동일) | 종료 코드 `0`·`1` · 두 node 판이 같은 두 답(`2 / 2`) |
>
> **층** — `async`/`await` 의 멈춤과 재개는 **언어(ECMA-262)** 의 것이다. **호스트가 끼는 자리는 둘**이다 — 걸음을 만든 **타이머**와, 먼저 거부된 프라미스를 **보고하는** node(동작 (4) · 37번).
>
> **선행** — [37 — Promise 상태 모델](../37-promise-state-model/2-summary.md)(직접 선행 — ★★★ **흡수 규칙과 틱 세는 창**이 거기서 온다 · 미처리 거부) ·
> [36 — 이벤트 루프와 마이크로태스크](../36-event-loop-and-microtasks/2-summary.md)(★★ **`A1` 이 `S2` 보다 먼저**였던 것 — 여기서 정본으로 다시 잰다) ·
> [20 — 제너레이터](../20-generators/2-summary.md)(★★★ **`yield` ↔ `await`** — 멈췄다 이어 도는 함수. 동작 (8)이 러너로 같은 로그를 낸다) ·
> [32 — 오류 처리와 `Error`](../32-error-handling-and-error/2-summary.md)(★★ **`try`/`catch`/`finally` 의 흐름** — `return` 과 `return await` 가 그 흐름에서 갈린다. 동작 (6)) ·
> [38 — Promise 조합기](../38-promise-combinators/2-summary.md)(`Promise.all` 은 **이미 시작한 것**을 기다린다) · [26 — 배열 탐색·평탄화·생성](../26-array-search-flatten-and-create/2-summary.md)(★ `Array.fromAsync` 는 하나씩, `Promise.all([...gen()])` 은 셋 다 먼저 — 순차 대 병렬의 **내장 함수 쪽 짝**).
>
> ★★ **경계 — 연혁**(`co` 러너에서 언어 문법으로)은 [`history/js/04-비동기-진화.md`](../../../../../../history/js/04-비동기-진화.md) 의 **「4단계 — 제너레이터/이터레이터」** 와 **「5단계 — async/await (ES2017)」** 절이 정본이다. 그 절의 순차/병렬 그림은 **「가로 길이는 원문 수치가 아니다」** 라고 스스로 적는다 — 여기서는 **시작 로그의 순서**로 같은 차이를 보인다.
> ★ **경계 — `for await` 와 `async function*`** 는 목록의 **40번 주제**, **취소와 타임아웃**은 목록의 **41번 주제**, **모듈 적재 순서**는 목록의 **42번 주제**다.

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

**`async` 함수는 「번호표를 받고 기다리는 손님」이다. 호출되면 창구까지는 곧장 걸어오고(첫 `await` 까지 동기), 그 자리에서 번호표(프라미스)를 호출한 쪽에 쥐여 준 뒤, 차례(마이크로태스크)가 오면 **멈춘 그 줄부터** 이어 간다.**

- ★★★ **창구까지는 지금 걷는다** — 부르는 순간 본문이 **첫 `await` 까지** 돈다. 호출한 쪽의 다음 줄은 **그 뒤에** 돈다.
- ★★★ **번호표는 늘 준다** — 값을 돌려줘도, 던져도, 아무것도 안 돌려줘도 **프라미스**다. 던지면 **거부된 번호표**다(호출한 자리로 던지지 않는다).
- ★★ **`await` 는 값이 이미 있어도 한 번은 줄을 선다** — `await 1` 도 마이크로태스크 하나를 쉰다.
- ★★★ **두 손님을 한 줄로 세우면(`await a(); await b();`) 둘째는 첫째가 끝나야 창구로 온다** — 둘 다 먼저 부르고 나서 기다리면 **둘이 같이 줄을 선다.**

```text
   async function f() {             호출자
     line 1        ◀── f() 를 부르면 여기부터 지금 돈다
     line 2
     await x;      ──▶ 프라미스를 돌려주고 호출자에게 돌아간다 ──▶  caller: after f()
                                                                   (호출자가 끝까지 돈다)
     after await   ◀── x 가 확정되면 마이크로태스크 하나로 여기서 이어 간다
   }
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 창구까지 곧장 걷는다 | `AsyncFunctionStart` — 본문을 **지금** 돌리기 시작한다 | 동작 (1)의 `[2]` |
| 번호표 | 호출이 돌려주는 **새 프라미스**(늘 새것 — 안에서 돌려준 프라미스와 같은 객체가 아니다) | 동작 (1)의 `[1]` |
| 줄을 선다 | `Await` — `PromiseResolve` 로 감싸 **`then` 을 건다** | 동작 (2) |
| 멈춘 줄부터 이어 간다 | 반응 잡이 **멈춘 실행 문맥**을 다시 돌린다 | 동작 (2)의 `after await @k` |
| 한 줄로 세운다 / 같이 세운다 | `await a(); await b();` / `const pa = a(), pb = b();` | 동작 (3) |

**똑같은 구조다** — 실무에서 물리는 자리도 굳어 있다.
「**독립적인 요청 둘을 `await` 두 줄로 썼더니 둘째가 첫째를 기다렸다**」와
「**`forEach(async …)` 뒤의 코드가 항목 처리가 끝나기 전에 돌았다**」, 그리고
「**`try` 안에서 `return promise` 했더니 `catch` 가 안 잡았다**」가 그것이다(동작 (3)·(5)·(6)).

> **`await`** — 피연산자를 프라미스로 감싸 확정을 기다리는 동안 **이 함수만** 멈추는 연산자. 스레드는 멈추지 않는다.\
> 예: `const v = await fetchUser();`

## 이 주제가 답하려는 질문

1. **`async` 함수를 부르면 무엇이 돌아오고, 본문은 어디까지 지금 도나** — `await` 는 값이 이미 있어도 쉬나, 몇 틱을 쉬나?
2. **`await a(); await b();` 와 `await Promise.all([a(), b()])` 는 무엇이 다른가** — 시간이 아니라 **시작 순서**로 말하면? `forEach` 안의 `await` 는?
3. **`try` 안의 `return p` 와 `return await p` 는 무엇이 다른가** — 최상위 `await` 는 어디서 되나 · `async` 함수는 제너레이터 + 프라미스와 무엇이 같은가?

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 출력으로 읽는다.

### (1) ★★★ 늘 프라미스 · 첫 `await` 까지는 지금

**언제 쓰나** — `async` 함수의 반환값을 다룰 때 · `async` 함수를 부른 **다음 줄**이 무엇을 볼 수 있는지 판단할 때.

```js
// js36b-39a-async-basics.js
// [1] What does calling an async function return? [2] How far does its body run before the call returns?
// [3] Microtask ticks: a counter job requeues itself once per tick, and the probe reads the counter (@k = k ticks so far).
const show = (x) => (x instanceof Error ? x.constructor.name + " 「" + x.message + "」" : JSON.stringify(x));
const log = (s) => console.log(s);
(async () => {
  log("[1] return values");
  const inner = Promise.resolve("v");
  const cases = [
    ["async () => 1", async () => 1],
    ["async () => { throw Error('x') }", async () => { throw new Error("x"); }],
    ["async () => inner (a promise)", async () => inner],
    ["async () => {} (nothing)", async () => {}],
  ];
  for (const [label, f] of cases) {
    let r, how = "returned";
    try { r = f(); } catch (e) { how = "threw " + show(e); }
    let settled;
    try { settled = "fulfilled " + show(await r); } catch (e) { settled = "rejected " + show(e); }
    log("  " + label.padEnd(34) + how.padEnd(9) + (r instanceof Promise ? "a Promise" : typeof r) + " · same object as inner " + (r === inner) + " · " + settled);
  }

  log("[2] order of lines around a call");
  const order = [];
  async function f() {
    order.push("f: line 1");
    order.push("f: line 2");
    await null;
    order.push("f: after await");
  }
  order.push("caller: before f()");
  const pr = f();
  order.push("caller: after f()");
  await pr;
  log("  " + order.join(" > "));

  log("[3] microtask ticks until the step after X runs");
  const measure = (label, body) => new Promise((done) => {
    let tick = 0, stop = false;
    const counter = () => { if (stop) return; tick++; queueMicrotask(counter); };
    const ev = [];
    body(ev, () => tick).then(() => { stop = true; ev.push("caller's then @" + tick); });
    ev.push("caller's next line @" + tick);
    queueMicrotask(counter);
    setTimeout(() => { log("  " + label.padEnd(40) + ev.join(" > ")); done(); }, 0);
  });
  const settledP = Promise.resolve("v");
  const thenable = { then(onF) { onF("t"); } };
  await measure("await 1", async (ev, t) => { await 1; ev.push("after await @" + t()); });
  await measure("await settledP", async (ev, t) => { await settledP; ev.push("after await @" + t()); });
  await measure("await thenable", async (ev, t) => { await thenable; ev.push("after await @" + t()); });
  await measure("no await, return 'v'", async () => "v");
  await measure("return settledP", async () => settledP);
  await measure("return await settledP", async () => await settledP);
})();
```

```text
===== node20 js36b-39a-async-basics.js (exit=0) =====
[1] return values
  async () => 1                     returned a Promise · same object as inner false · fulfilled 1
  async () => { throw Error('x') }  returned a Promise · same object as inner false · rejected Error 「x」
  async () => inner (a promise)     returned a Promise · same object as inner false · fulfilled "v"
  async () => {} (nothing)          returned a Promise · same object as inner false · fulfilled undefined
[2] order of lines around a call
  caller: before f() > f: line 1 > f: line 2 > caller: after f() > f: after await
[3] microtask ticks until the step after X runs
  await 1                                 caller's next line @0 > after await @0 > caller's then @1
  await settledP                          caller's next line @0 > after await @0 > caller's then @1
  await thenable                          caller's next line @0 > after await @1 > caller's then @2
  no await, return 'v'                    caller's next line @0 > caller's then @0
  return settledP                         caller's next line @0 > caller's then @2
  return await settledP                   caller's next line @0 > caller's then @1
```

- ★★★ **`[1]` 네 행 모두 `returned`**(던지지 않았다) · **`a Promise`** · **`same object as inner false`**.
  `throw` 도 **호출한 자리로 나오지 않고** `rejected Error 「x」` 인 프라미스가 된다. 안에서 프라미스(`inner`)를 돌려줘도 **바깥 프라미스는 새것**이고 그것을 **따라간다**(`fulfilled "v"`).
- ★★★ **`[2]` `caller: before f() > f: line 1 > f: line 2 > caller: after f() > f: after await`** — 본문은 **첫 `await` 까지 지금** 돌고, 거기서 호출자에게 돌아간다. 명세의 `Await` 마지막 단계가 「**호출자 문맥으로 돌아간다**」다.
- ★★ 36번의 순서 퍼즐에서 `A1` 이 `S2` 보다 먼저였던 것이 이것이다.

### (2) ★★★ `await` 가 쉬는 틱 — 계수 잡으로

**언제 쓰나** — 「`await` 를 안 쓰면 한 틱 빨라지나」·「`return await` 는 쓸데없나」를 판단할 때.
★★★ 위 소스의 `[3]` 이다. **37번 동작 (2)와 같은 창**이다 — `@k` 는 계수 잡이 **k 번** 돈 뒤. 본문을 부른 **다음 줄**(`caller's next line`)도 찍는다.

```text
   await v   — Await(v) 가 하는 일

   ① promise = PromiseResolve(%Promise%, v)   ← v 가 진짜 프라미스면 그대로, 아니면 새로 감싼다
   ② PerformPromiseThen(promise, 재개, 재개-던지기)
   ③ 호출자에게 돌아간다                        ← caller's next line 이 여기서 찍힌다
   ─── 틱 ───
   ④ 반응 잡이 멈춘 문맥을 다시 돌린다            ← after await

   v = 1 · 진짜 프라미스   → ①이 새 잡을 안 만든다 → 반응 잡 하나
   v = thenable            → ①이 새 프라미스를 만들고 NewPromiseResolveThenableJob 를 건다 → 하나 더
```

- ★★★ **`await 1` 도 쉰다** — `caller's next line @0 > after await @0` 에서 **호출자의 다음 줄이 먼저**다. 값이 이미 있어도 `then` 을 걸고 **반응 잡으로** 돌아온다.
- ★★★ **`await 1` 과 `await` 진짜 프라미스는 같은 틱**(`after await @0` · 호출자의 `then` 은 `@1`), **`await thenable` 은 하나 더**(`@1` · `@2`) — 37번의 흡수 규칙 그대로다.
- ★★★ **반환 쪽** — `return 'v'` 는 `@0`, **`return settledP` 는 `@2`**, **`return await settledP` 는 `@1`**. `async` 함수의 결과 프라미스를 **프라미스로 resolve** 하면 37번의 +2 가 붙고, `await` 로 **값을 꺼내 돌려주면** 그 값으로 resolve 되기 때문이다.
  ★ 「`return await` 는 틱을 낭비한다」는 **이 판에서는 거꾸로**였다 — 단 **이 문서는 시간을 재지 않았다.** 틱 하나의 차이가 무엇을 바꾸나는 동작 (5)가 보인다(`catch`).
- ★★ **두 node 판과 Chrome 151 이 같은 `@k` 를 냈다** — 틱 수는 명세의 잡 개수다.

### (3) ★★★ 순차 대 병렬 — 시간 대신 「시작 로그의 순서」

**언제 쓰나** — 서로 기다릴 필요가 없는 작업 둘을 `await` 할 때.
★★★ 작업 `a`·`b` 는 각각 `start` 를 찍고 **`setTimeout` 0 세 걸음**을 걸은 뒤 `end` 를 찍는다. **시계를 읽지 않는다** — 묻는 것은 **`b start` 가 `a end` 보다 먼저인가** 하나다.

```js
// js36b-39b-seq-vs-par.js
// Two independent jobs a and b. Each prints "start", waits three steps (a setTimeout 0 each), prints "end".
// No clock is read: the question is only whether b's "start" comes before a's "end".
const run = async (label, body) => {
  const lines = [];
  const job = async (name) => {
    lines.push(name + " start");
    for (let i = 0; i < 3; i++) await new Promise((r) => setTimeout(r, 0));
    lines.push(name + " end");
    return name;
  };
  const result = await body(job);
  const overlap = lines.indexOf("b start") < lines.indexOf("a end");
  console.log(label);
  console.log("  " + lines.join(" > ") + "   result " + JSON.stringify(result));
  console.log("  b started before a ended: " + overlap);
};
(async () => {
  await run("[1] await a(); await b();", async (job) => { const x = await job("a"); const y = await job("b"); return [x, y]; });
  await run("[2] await Promise.all([a(), b()])", async (job) => Promise.all([job("a"), job("b")]));
  await run("[3] const pa = a(), pb = b(); await pa; await pb;", async (job) => { const pa = job("a"), pb = job("b"); return [await pa, await pb]; });
  await run("[4] for (const n of ['a', 'b']) await job(n)", async (job) => { const out = []; for (const n of ["a", "b"]) out.push(await job(n)); return out; });
})();
```

```text
===== node20 js36b-39b-seq-vs-par.js (exit=0) =====
[1] await a(); await b();
  a start > a end > b start > b end   result ["a","b"]
  b started before a ended: false
[2] await Promise.all([a(), b()])
  a start > b start > a end > b end   result ["a","b"]
  b started before a ended: true
[3] const pa = a(), pb = b(); await pa; await pb;
  a start > b start > a end > b end   result ["a","b"]
  b started before a ended: true
[4] for (const n of ['a', 'b']) await job(n)
  a start > a end > b start > b end   result ["a","b"]
  b started before a ended: false
```

```text
   [1] await a(); await b();                 [2] await Promise.all([a(), b()])
                                             [3] const pa = a(), pb = b(); await pa; await pb;

   a start ── ── ── a end                    a start ── ── ── a end
                        b start ── ── ── b end   b start ── ── ── b end
   b 는 a 가 끝난 뒤에야 「불린다」             둘 다 먼저 불리고, 그다음 기다린다

   b started before a ended:  false          true
```

- ★★★ **`[1]` 과 `[4]`(`for…of` 안의 `await`)는 `false`**, **`[2]` 와 `[3]` 은 `true`**. 결과는 넷 다 `["a","b"]` 로 **같다** — 달라진 것은 **`b` 를 언제 불렀나**뿐이다.
- ★★★ **갈림의 원인은 `Promise.all` 이 아니다** — `[3]` 은 `Promise.all` 없이 `true` 다. **`b()` 를 부른 줄이 `a` 를 `await` 하는 줄보다 앞에 있느냐**가 전부다. 38번 동작 (2)의 「입력은 조합기에 넘기기 전에 이미 시작했다」와 같은 이야기다.
- ★★ 연혁 문서의 순차/병렬 그림은 가로 길이가 **원문 수치가 아니라고** 스스로 적는다. 이 문서도 **시간을 재지 않았다** — 「`[2]` 가 빠르다」는 여기서 나오지 않는다. 나오는 것은 **겹쳤다**(`true`)는 사실까지다.
- ★ **26번의 짝** — `Array.fromAsync` 는 `next`·settle 을 **하나씩**(`[4]` 의 모양), `Promise.all([...gen()])` 은 `next` 셋을 **먼저**(`[2]` 의 모양) 불렀다.

### (4) ★★★ `[3]` 의 함정 — 먼저 시작한 쪽이 먼저 거부되면

**언제 쓰나** — `const pa = a(), pb = b(); await pa; await pb;` 로 「병렬」을 쓸 때.
★★ `a` 는 세 걸음 뒤 이행, `b` 는 **한 걸음 뒤 거부**한다. 둘 다 먼저 부르고 **차례로** 기다린다 — 또는 `Promise.all` 로 기다린다. 행마다 새 프로세스다(37번 동작 (5)와 같은 방식).

```js
// js36b-39-h-early-reject.js
// a takes three steps and succeeds; b rejects after one step. Both are started first, then awaited (argv[2] says how).
// argv[3] === "hooks" installs node's process events and prints them on standard output.
const how = process.argv[2];
if (process.argv[3] === "hooks") {
  process.on("unhandledRejection", (r) => console.log("unhandledRejection(" + r.message + ")"));
  process.on("rejectionHandled", () => console.log("rejectionHandled"));
}
const step = () => new Promise((r) => setTimeout(r, 0));
const a = async () => { for (let i = 0; i < 3; i++) await step(); console.log("a end"); return "a"; };
const b = async () => { await step(); console.log("b rejects"); throw new Error("b"); };
(async () => {
  try {
    if (how === "one-by-one") { const pa = a(), pb = b(); await pa; await pb; }
    if (how === "all") { await Promise.all([a(), b()]); }
  } catch (e) {
    console.log("caught " + e.constructor.name + " 「" + e.message + "」");
  }
})();
```

```sh
# js36b-39c-early-reject.sh
#!/usr/bin/env bash
# Start both, then await: one-by-one (await pa; await pb) or Promise.all. With hooks: standard output. No hooks: exit code only.
set -u -o pipefail
cd "$(dirname "$0")"
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
same=0
for how in one-by-one all; do
  echo "--- $how"
  out="$("$N20" js36b-39-h-early-reject.js "$how" hooks | paste -sd' ' -)"
  echo "  with hooks : $out"
  "$N20" js36b-39-h-early-reject.js "$how" > /dev/null 2>&1
  e=$?
  echo "  no hooks   : exit $e"
  o18="$("$N18" js36b-39-h-early-reject.js "$how" hooks | paste -sd' ' -)"
  "$N18" js36b-39-h-early-reject.js "$how" > /dev/null 2>&1
  [ "$o18 $?" = "$out $e" ] && same=$((same + 1))
done
echo ""
echo "rows where node18 gives the same two answers as node20: $same / 2"
```

```text
===== ./js36b-39c-early-reject.sh (exit=0) =====
--- one-by-one
  with hooks : b rejects unhandledRejection(b) a end caught Error 「b」 rejectionHandled
  no hooks   : exit 1
--- all
  with hooks : b rejects caught Error 「b」 a end
  no hooks   : exit 0

rows where node18 gives the same two answers as node20: 2 / 2
```

```text
   one-by-one:  await pa  ──────────────────────▶ (pa 를 기다리는 중)
                pb 가 한 걸음 뒤 거부 ─ 이때 pb 에 처리기가 없다 ─▶ node: unhandledRejection (훅 없으면 exit 1)
                pa 가 끝난 뒤 await pb ─ 이제야 처리기가 달린다 ─▶ caught … · rejectionHandled

   all:         Promise.all 이 pa·pb 둘 다에 처리기를 곧바로 건다 ─▶ 보고 없음 · caught · exit 0
```

- ★★★ **`one-by-one` 은 훅이 있으면 `unhandledRejection(b)` 가 먼저 찍히고, 훅이 없으면 `exit 1`** 이다 — `await pb` 에 닿기 **전에** `pb` 가 거부됐는데, 그때 `pb` 에는 **처리기가 하나도 없다.** `catch` 블록은 코드에 **분명히 있는데도** 그렇다.
- ★★★ **`all` 은 `exit 0`** — `Promise.all` 은 **모든 입력에 곧바로 `then` 을 건다.** 거부가 **처리된 채로** 도착한다.
- ★★ 두 node 판이 **같은 두 답**을 냈다(`2 / 2`). 이 보고와 종료는 **node 의 것**이다(37번 동작 (5) — 거기가 정본).

### (5) ★★★ `forEach` 안의 `await` — 기다리지 않는다

**언제 쓰나** — 배열의 항목마다 비동기 작업을 할 때.

```js
// js36b-39d-foreach.js
// An async callback per item; each waits one step (setTimeout 0) and prints. When does the line after the loop print?
const step = () => new Promise((r) => setTimeout(r, 0));
const items = ["x", "y", "z"];
(async () => {
  const lines = [];
  console.log("[1] items.forEach(async (it) => { await step(); ... })");
  const ret = items.forEach(async (it) => { lines.push(it + " start"); await step(); lines.push(it + " done"); });
  lines.push("-- line after forEach · forEach returned " + ret);
  await step(); await step();
  console.log("  " + lines.join(" > "));

  lines.length = 0;
  console.log("[2] for (const it of items) { await step(); ... }");
  for (const it of items) { lines.push(it + " start"); await step(); lines.push(it + " done"); }
  lines.push("-- line after for...of");
  console.log("  " + lines.join(" > "));

  lines.length = 0;
  console.log("[3] await Promise.all(items.map(async (it) => { await step(); ... }))");
  await Promise.all(items.map(async (it) => { lines.push(it + " start"); await step(); lines.push(it + " done"); }));
  lines.push("-- line after Promise.all");
  console.log("  " + lines.join(" > "));
})();
```

```text
===== node20 js36b-39d-foreach.js (exit=0) =====
[1] items.forEach(async (it) => { await step(); ... })
  x start > y start > z start > -- line after forEach · forEach returned undefined > x done > y done > z done
[2] for (const it of items) { await step(); ... }
  x start > x done > y start > y done > z start > z done > -- line after for...of
[3] await Promise.all(items.map(async (it) => { await step(); ... }))
  x start > y start > z start > x done > y done > z done > -- line after Promise.all
```

- ★★★ **`[1]` — `-- line after forEach` 가 `x done` 보다 먼저**이고 **`forEach returned undefined`** 다. `forEach` 는 콜백이 돌려준 프라미스를 **받아서 버린다** — 기다릴 방법이 없다. 세 항목은 `[3]` 처럼 **겹쳐서** 돌았다(`x start > y start > z start`).
- ★★★ **`[2]` `for…of` 는 항목마다 기다린다**(`x start > x done > y start …`), **`[3]` `Promise.all(map(…))` 은 겹치고 기다린다** — 뒤의 줄이 **맨 끝**이다.
- ★★ 그래서 「`forEach` 가 비동기를 못 기다린다」는 `forEach` 의 결함이 아니라 **돌려준 값을 쓰지 않는 함수**라서다(`map` 은 콜백이 돌려준 프라미스를 **배열로 돌려준다** — 그래서 `Promise.all` 로 기다릴 수 있다).

### (6) ★★★ `return p` 대 `return await p` — `try` 안에서

**언제 쓰나** — `try`/`catch`/`finally` 안에서 다른 `async` 함수의 결과를 돌려줄 때. 32번의 `try`/`finally` 흐름이 비동기에서 어떻게 되나.
★★ `failLater()` 는 **한 걸음 뒤** 거부한다. 두 변형은 `await` 한 글자만 다르다.

```js
// js36b-39e-return-await.js
// A promise that rejects one step later. Returned from inside try, with and without await.
// Which lines run, and what does the caller get?
const step = () => new Promise((r) => setTimeout(r, 0));
const failLater = async () => { await step(); throw new Error("late"); };
const show = (x) => (x instanceof Error ? x.constructor.name + " 「" + x.message + "」" : JSON.stringify(x));
const variants = [
  ["return failLater()", async (L) => { try { return failLater(); } catch (e) { L.push("catch ran"); return "from catch"; } finally { L.push("finally ran"); } }],
  ["return await failLater()", async (L) => { try { return await failLater(); } catch (e) { L.push("catch ran"); return "from catch"; } finally { L.push("finally ran"); } }],
];
(async () => {
  for (const [label, f] of variants) {
    const L = [];
    const p = f(L);
    const done = p.then((v) => L.push("caller got fulfilled " + show(v)), (e) => L.push("caller got rejected " + show(e)));
    L.push("caller: call returned");
    await done;
    console.log(label);
    console.log("  " + L.join(" > "));
  }
})();
```

```text
===== node20 js36b-39e-return-await.js (exit=0) =====
return failLater()
  finally ran > caller: call returned > caller got rejected Error 「late」
return await failLater()
  caller: call returned > catch ran > finally ran > caller got fulfilled "from catch"
```

```text
   return failLater();                         return await failLater();

   try {                                       try {
     return p;   ── 곧바로 try 를 떠난다          await p;  ── 여기서 멈춘다 (아직 try 안이다)
   } catch …     ── p 가 나중에 거부돼도          } catch …  ── p 가 거부되면 여기로 온다 ◀
                    여기에 안 온다                              "from catch"
   finally …     ── 지금 돈다(p 는 아직 pending)   finally … ── p 가 확정된 뒤 돈다
   → 호출자는 p 를 따라가 rejected              → 호출자는 fulfilled "from catch"
```

- ★★★ **`return failLater()`** — `finally ran` 이 **`caller: call returned` 보다 먼저** 찍혔다(호출 안에서 이미 `try` 를 떠났다). `catch` 는 **안 돌았고**, 호출자는 **`rejected Error 「late」`** 를 받았다.
- ★★★ **`return await failLater()`** — `catch ran > finally ran` 이 **호출자의 다음 줄보다 뒤에** 찍혔고, 호출자는 **`fulfilled "from catch"`** 를 받았다.
- ★★ 32번의 규칙이 **그대로** 걸린 것이다 — `return 식` 은 식을 평가해 **완료 기록에 담고 `try` 를 떠난다.** 그 식이 **아직 확정되지 않은 프라미스**면, 나중의 거부는 **`try` 밖에서** 일어난다. `await` 는 확정될 때까지 **`try` 안에 머문다.**
- ★ 동작 (2)의 틱 수와 함께 읽으면 — `return await` 가 틱이 **적었고**, 거부를 **잡았다.**

### (7) ★★ 최상위 `await` — ES 모듈에서만

**언제 쓰나** — 설정 파일을 읽어야 시작할 수 있는 모듈 · 스크립트 파일의 맨 위에서 `await` 를 쓰고 싶을 때.

```js
// js36b-39-h-tla.mjs
// await at the top level of the file, outside any function.
console.log("before");
const v = await new Promise((r) => setTimeout(() => r("value"), 0));
console.log("after: " + v);
```

```sh
# js36b-39f-top-level-await.sh
#!/usr/bin/env bash
# The same text as an ES module file, and as CommonJS through standard input.
# For the CommonJS run only standard error is kept, and of it only the line that names the error.
set -u -o pipefail
cd "$(dirname "$0")"
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
for v in 18 20; do
  [ $v = 18 ] && n="$N18" || n="$N20"
  echo "--- node$v js36b-39-h-tla.mjs"
  "$n" js36b-39-h-tla.mjs
  echo "(exit $?)"
  echo "--- node$v --input-type=module < js36b-39-h-tla.mjs"
  "$n" --input-type=module < js36b-39-h-tla.mjs
  echo "(exit $?)"
  echo "--- node$v --input-type=commonjs < js36b-39-h-tla.mjs   (standard error: the error line only)"
  out="$("$n" --input-type=commonjs < js36b-39-h-tla.mjs 2>/dev/null)"
  err="$("$n" --input-type=commonjs < js36b-39-h-tla.mjs 2>&1 >/dev/null)"
  e=$?
  printf '%s\n' "$err" | grep -E '^[A-Za-z]*Error' || true
  echo "(exit $e · standard output had $(printf '%s' "$out" | grep -c '' || true) lines)"
done
```

```text
===== ./js36b-39f-top-level-await.sh (exit=0) =====
--- node18 js36b-39-h-tla.mjs
before
after: value
(exit 0)
--- node18 --input-type=module < js36b-39-h-tla.mjs
before
after: value
(exit 0)
--- node18 --input-type=commonjs < js36b-39-h-tla.mjs   (standard error: the error line only)
SyntaxError: await is only valid in async functions and the top level bodies of modules
(exit 1 · standard output had 0 lines)
--- node20 js36b-39-h-tla.mjs
before
after: value
(exit 0)
--- node20 --input-type=module < js36b-39-h-tla.mjs
before
after: value
(exit 0)
--- node20 --input-type=commonjs < js36b-39-h-tla.mjs   (standard error: the error line only)
SyntaxError: await is only valid in async functions and the top level bodies of modules
(exit 1 · standard output had 0 lines)
```

- ★★★ **같은 글자가 ES 모듈로는 돌고(`before` · `after: value` · `exit 0`), CommonJS 로는 `SyntaxError 「await is only valid in async functions and the top level bodies of modules」` · `exit 1`** — 그리고 **표준 출력은 0 줄**이다. 컴파일 단계에서 거절돼 `before` 조차 안 찍혔다(35번의 early error 와 같은 모양).
- ★★ **`.mjs` 만이 아니다** — `--input-type=module` 로 표준 입력에 준 **같은 글자**도 돌았다. 기준은 **확장자가 아니라 「모듈 코드인가」** 다(모듈 판정은 호스트의 몫 — 목록의 **42번 주제**).
- ★ 두 node 판이 같은 답을 냈다(node 18 도 ES2022 기능을 갖고 있다).

### (8) ★★ `async` 함수 = 제너레이터 + 프라미스 러너 — 로그가 한 줄씩 같은가

**언제 쓰나** — `await` 가 「마법」처럼 느껴질 때 · 20번의 `yield` 를 떠올려 `await` 를 설명할 때.
★★★ 같은 걸음을 **`async` 함수**로 한 번, **제너레이터 + 열 줄짜리 러너**로 한 번 쓴다. 옆에서 **다른 마이크로태스크 사슬**(`other k`)이 한 틱에 한 줄씩 찍는다 — 두 로그가 **틱 단위로 같은지** 본다.

```js
// js36b-39g-generator-runner.js
// The same steps written twice: as an async function, and as a generator driven by a small runner.
// A second, unrelated microtask chain prints "other k" so the two runs can be compared tick by tick.
function run(genFn) {
  return new Promise((resolve, reject) => {
    const it = genFn();
    const go = (method, arg) => {
      let r;
      try { r = it[method](arg); } catch (e) { reject(e); return; }
      if (r.done) { resolve(r.value); return; }
      Promise.resolve(r.value).then((v) => go("next", v), (e) => go("throw", e));
    };
    go("next", undefined);
  });
}
const other = (L, n) => { let k = 0; const f = () => { if (k < n) { L.push("other " + ++k); queueMicrotask(f); } }; queueMicrotask(f); };
const failing = Promise.reject(new Error("r"));
failing.catch(() => {});
async function viaAsync(L) {
  L.push("body start");
  const a = await 1;
  L.push("got " + a);
  const b = await Promise.resolve(2);
  L.push("got " + b);
  try { await failing; } catch (e) { L.push("caught " + e.message); }
  return "done";
}
function* viaGen(L) {
  L.push("body start");
  const a = yield 1;
  L.push("got " + a);
  const b = yield Promise.resolve(2);
  L.push("got " + b);
  try { yield failing; } catch (e) { L.push("caught " + e.message); }
  return "done";
}
(async () => {
  const A = [], G = [];
  const settle = () => new Promise((r) => setTimeout(r, 0));
  other(A, 6); viaAsync(A).then((v) => A.push("result " + v)); await settle();
  other(G, 6); run(() => viaGen(G)).then((v) => G.push("result " + v)); await settle();
  console.log("async function    " + A.join(" > "));
  console.log("generator + run() " + G.join(" > "));
  console.log("identical: " + (A.join() === G.join()));
})();
```

```text
===== node20 js36b-39g-generator-runner.js (exit=0) =====
async function    body start > other 1 > got 1 > other 2 > got 2 > other 3 > caught r > other 4 > result done > other 5 > other 6
generator + run() body start > other 1 > got 1 > other 2 > got 2 > other 3 > caught r > other 4 > result done > other 5 > other 6
identical: true
```

```text
   async function          ≈   function* + run()

   await x                 ≈   yield x   →  run 이 Promise.resolve(x).then(next, throw) 를 건다
   await 가 거부를 던진다    ≈   run 이 it.throw(e) 를 부른다  →  제너레이터 안의 try/catch 가 받는다
   return v                ≈   { done: true, value: v }  →  run 의 resolve(v)
```

- ★★★ **`identical: true`** — 옆 사슬(`other 1`\~`other 6`)과 섞인 **줄 순서까지** 같았다. `await 1` · `await` 진짜 프라미스 · **거부된 프라미스를 `try` 안에서 `await`** 셋 모두.
- ★★ 명세의 `Await` 도 **`PromiseResolve` → `PerformPromiseThen`** 이다 — 러너의 `Promise.resolve(r.value).then(…)` 과 같은 두 걸음이다. 연혁 문서의 「async 함수는 본질적으로 제너레이터 + Promise 자동 러너」를 **로그로** 확인한 셈이다.
- ★ **같지 않은 자리도 있다** — 이 러너는 **thenable 이 아닌 값**과 **진짜 프라미스**만 봤다. 실제 `async` 함수는 러너가 없어도 되고, `yield` 와 `await` 를 **한 함수에 같이** 쓰면 `async function*` 이 된다(목록의 **40번 주제**). 20번의 `yield` 흐름이 정본이다.

### (9) ★★ 파이썬 대비 — 코루틴은 부르기만 해서는 안 돈다

**언제 쓰나** — 파이썬 `asyncio` 에서 온 사람이 「부르기만 하면 아무 일도 안 일어난다」를 JS 에 기대할 때 · 반대 방향.

```python
# js36b-39-h-lazy.py
# Call an async function without awaiting it. Does any of its body run?
import asyncio

log = []

async def f():
    log.append("f: line 1")
    await asyncio.sleep(0)
    log.append("f: after await")

log.append("caller: before f()")
c = f()
log.append("caller: after f() -- got " + type(c).__name__)
print(" > ".join(log))

log.clear()
async def main():
    log.append("main: before f()")
    t = asyncio.create_task(f())
    log.append("main: after create_task")
    await t
    log.append("main: after await t")
asyncio.run(main())
print(" > ".join(log))
c.close()
```

```js
// js36b-39-h-eager.js
// The same question in JS: call an async function without awaiting it.
const log = [];
async function f() {
  log.push("f: line 1");
  await null;
  log.push("f: after await");
}
log.push("caller: before f()");
const c = f();
log.push("caller: after f() -- got " + c.constructor.name);
console.log(log.join(" > "));
```

```sh
# js36b-39h-python-contrast.sh
#!/usr/bin/env bash
# Python coroutine against JS async function: what runs at the moment of the call?
set -u -o pipefail
cd "$(dirname "$0")"
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
echo "--- python3 $(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])') js36b-39-h-lazy.py"
python3 js36b-39-h-lazy.py
echo "(exit $?)"
echo "--- node20 js36b-39-h-eager.js"
"$N20" js36b-39-h-eager.js
echo "(exit $?)"
```

```text
===== ./js36b-39h-python-contrast.sh (exit=0) =====
--- python3 3.12 js36b-39-h-lazy.py
caller: before f() > caller: after f() -- got coroutine
main: before f() > main: after create_task > f: line 1 > f: after await > main: after await t
(exit 0)
--- node20 js36b-39-h-eager.js
caller: before f() > f: line 1 > caller: after f() -- got Promise
(exit 0)
```

```text
                   부른 순간                     돌게 하려면
   Python          코루틴 객체를 돌려줄 뿐 — 본문 0 줄     await 하거나 create_task 로 루프에 올린다
   JS              첫 await 까지 지금 돈다                (이미 돌고 있다)
   Rust(대비만)     Future 를 돌려줄 뿐 (러스트 목록 54번)   await·실행기가 있어야 돈다 — 이 문서는 돌리지 않았다
```

- ★★★ **파이썬은 `f()` 를 불러도 `f: line 1` 이 안 찍힌다**(`caller: before f() > caller: after f() -- got coroutine`). `create_task` 로 루프에 올려야 돈다. **JS 는 부르는 순간 `f: line 1` 이 찍힌다**(`got Promise`).
- ★★ 그래서 **JS 에서 「부르고 안 기다린」 async 함수는 이미 일을 하고 있다** — 동작 (4)의 거부가 그래서 **처리기 없이** 도착한다. 파이썬은 기다리지 않은 코루틴이 **아예 안 돈다**(이 탐침은 그 코루틴을 끝에서 `close()` 로 닫았다).
- ★ 파이썬 쪽 정본은 파이썬 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **51번**(`asyncio` 코루틴 기초 — 아직 폴더가 없다). Rust 는 러스트 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **54번**(`async`/`await` 와 `Future`) — **이 문서는 Rust 를 돌리지 않았다.**

## 문법 — 형태와 규칙

★ 이 절은 **형태 표**다 — 모든 동작 주장은 위 동작 절의 캡처 블록에서만 한다.

| 형태 | 하는 일 | 판 | 어디서 봤나 |
|---|---|---|---|
| `async function f() {}` · `async () => {}` · `{ async m() {} }` | 부르면 **새 프라미스**를 돌려주고 본문을 **첫 `await` 까지 지금** 돌린다 | ES2017 | 동작 (1) |
| `await 식` | 식을 `PromiseResolve` 로 감싸 `then` 을 걸고 **이 함수만** 멈춘다 · 거부면 그 자리에서 던진다 | ES2017 | 동작 (2)·(6) |
| `return 식` (async 안) | 결과 프라미스를 **그 식으로 resolve** — 프라미스면 따라간다(+2 틱) | ES2017 | 동작 (2)·(6) |
| `return await 식` | 확정될 때까지 **`try` 안에 머문 뒤** 값으로 resolve | ES2017 | 동작 (6) |
| 모듈 최상위 `await` | 모듈 평가를 멈춘다 — **모듈 코드에서만** | **ES2022** | 동작 (7) |

- **`await` 는 `async` 함수(와 모듈 최상위) 안에서만** 쓴다. CommonJS 최상위에서는 `SyntaxError` 다.
- **동시에 시작하려면 먼저 부르고 나중에 기다린다** — 기다리는 방법은 **`Promise.all` 처럼 곧바로 처리기를 거는 것**이어야 안전하다(동작 (4)).
- **`try` 안에서 프라미스를 돌려줄 때는 `return await`** — 그래야 `catch`·`finally` 가 그 결과를 본다.

## 어디서 틀리나

### (1) ★★★ 독립적인 작업을 `await` 두 줄로 쓴다

**둘째는 첫째가 끝난 뒤에야 불린다**(`b started before a ended: false`). 먼저 둘 다 부르고 기다린다 — 결과는 같다(`["a","b"]`).

### (2) ★★★ 「먼저 부르고 차례로 `await`」를 안전한 병렬로 믿는다

**뒤의 것이 먼저 거부되면 처리기 없이 거부된다** — node 는 `unhandledRejection`, 훅이 없으면 **`exit 1`**(동작 (4)). `Promise.all`(또는 `allSettled`)로 기다린다.

### (3) ★★★ `forEach(async …)` 뒤에서 항목 처리가 끝났다고 믿는다

**안 끝났다** — 뒤의 줄이 먼저 돈다(`-- line after forEach` 가 `x done` 앞). `for…of` + `await`(차례로) 또는 `Promise.all(map(…))`(겹쳐서).

### (4) ★★★ `try` 안의 `return promise` 가 `catch` 에 잡힐 것이라 믿는다

**안 잡힌다** — 호출자가 `rejected Error 「late」` 를 받았다. `finally` 도 **확정 전에** 돈다(동작 (6)). `return await` 를 쓴다.

### (5) ★★ `async` 함수의 `throw` 가 호출한 자리에서 잡힐 것이라 믿는다

**거부된 프라미스가 된다**(동작 (1)의 `[1]` — `returned … rejected Error 「x」`). 호출한 자리의 `try`/`catch` 는 `await` 할 때만 잡는다.

### (6) ★★ 「`await` 는 값이 이미 있으면 안 쉰다」

**쉰다** — `await 1` 뒤의 줄이 호출자의 다음 줄보다 **나중**이다(`caller's next line @0 > after await @0`).

### (7) ★★ 「`return await` 는 쓸데없는 틱 낭비다」

**이 판에서 `return await settledP` 는 `@1`, `return settledP` 는 `@2`** 였다 — 틱이 **적었다.** 그리고 `try` 안에서는 **뜻이 다르다**(4). 속도는 **안 쟀다.**

### (8) ★★ 최상위 `await` 는 `.mjs` 에서만 된다고 외운다

**모듈 코드면 된다** — `--input-type=module` 의 표준 입력도 돌았다. 기준은 확장자가 아니라 **모듈인가**다.

### (9) ★ 「`async` 를 붙이면 별도 스레드에서 돈다」

**같은 스레드**다 — 본문이 첫 `await` 까지 **호출자와 같은 흐름에서** 돌고(`f: line 1` 이 `caller: after f()` 앞), 재개도 **마이크로태스크**다(36번).

## 구현 세부사항 대 언어 보장

### 명세 보장(ECMA-262)

- ★★★ **`async` 함수 호출은 새 프라미스를 만들고 `AsyncFunctionStart` 로 본문을 곧바로 돌린다** — 던지면 그 프라미스를 거부한다.
- ★★★ **`Await(arg)`** — `PromiseResolve(%Promise%, arg)` → `PerformPromiseThen` → **호출자로 돌아간다**. 재개는 **반응 잡**이다. 그래서 값이 이미 있어도 한 틱 쉬고, thenable 은 **한 틱 더**(37번).
- ★★ `return 식` 은 결과 프라미스를 **그 값으로 resolve** — 프라미스면 37번의 흡수 규칙(+2 틱)이 걸린다.
- ★★ 최상위 `await` 는 **모듈 코드**의 문법이다. 스크립트에서는 early error(`SyntaxError`).

### 호스트

- ★★ **node 의 미처리 거부 보고와 종료 코드**(동작 (4)) — 37번이 정본이다.
- ★★ **어느 파일이 모듈인가** — `.mjs` · `--input-type=module` · `package.json` 의 `type`. node 의 규칙이다(42번).
- ★ 걸음을 만든 `setTimeout` 0 — 같은 지연의 타이머는 등록 순서(36번).

### 구현(V8) · 이 판의 관찰

- 예외 문구 — `await is only valid in async functions and the top level bodies of modules`.
- ★★ 틱 수(`@0`·`@1`·`@2`)가 두 node 판과 Chrome 151 에서 같았다 — 명세의 잡 개수에서 나오지만, **옛 판의 명세와 대조하지 않았으므로** 옛 엔진에서의 틱 수는 이 문서가 말하지 않는다.

### 그래서 이렇게 적으면 틀린다

- ✗ 「`Promise.all` 로 감싸야 병렬이 된다」 → ○ 「**먼저 부르면** 겹친다(`[3]` 도 `true`). `Promise.all` 은 **거부를 곧바로 받아 주는** 기다리는 방법이다」
- ✗ 「병렬로 바꾸면 빨라진다」 → ○ **안 쟀다** — 「`b` 가 `a` 가 끝나기 전에 시작했다」까지가 이 문서의 근거다
- ✗ 「`async` 함수는 호출되면 나중에 실행된다」 → ○ 「**첫 `await` 까지 지금**」
- ✗ 「`return await` 는 항상 불필요하다」 → ○ 「**`try` 안에서는 뜻이 다르다** — 그리고 이 판에서는 틱도 적었다」

## 언제 쓰고 언제 안 쓰나

- **`await` 한 줄씩** — 뒤의 작업이 **앞의 결과를 쓸 때**만.
- **먼저 부르고 `await Promise.all([...])`** — 서로 독립인 작업들. 부분 실패를 모으려면 `allSettled`.
- **`for…of` + `await`** — 항목을 **차례로** 처리해야 할 때(순서·부하 제한). **`forEach` 에는 `async` 콜백을 넘기지 않는다.**
- **`return await`** — `try`/`catch`/`finally` 안에서 프라미스를 돌려줄 때.
- **최상위 `await`** — ES 모듈의 초기화. CommonJS 에서는 `async` 즉시 실행 함수로 감싼다.
- ★ **안 쓰는 자리** — 「먼저 부르고 차례로 `await`」(거부가 처리기 없이 도착한다) · 기다릴 필요가 없는 값에 습관적으로 `await`.

## 핵심 문장

1. ★★★ `async` 함수는 **늘 새 프라미스**를 돌려주고, 본문은 **첫 `await` 까지 지금** 돈다 — 던져도 호출한 자리가 아니라 **거부된 프라미스**다.
2. ★★★ `await` 는 값이 이미 있어도 **반응 잡 하나**를 쉰다 — 진짜 프라미스도 하나, thenable 은 **하나 더**. `return p` 는 `@2`, `return await p` 는 `@1` 이었다.
3. ★★★ 순차 대 병렬은 **`b` 를 언제 불렀나**다 — `await a(); await b();` 는 `false`, 먼저 부르면(`Promise.all` 이든 아니든) `true`. 시간은 재지 않았다.
4. ★★★ **먼저 부르고 차례로 `await`** 하면 뒤의 거부가 **처리기 없이** 도착한다 — node 는 `exit 1`. `Promise.all` 은 처리기를 **곧바로** 건다.
5. ★★ `forEach` 는 `async` 콜백을 **기다리지 않는다** · `try` 안의 `return p` 는 **`catch` 를 건너뛴다** · 최상위 `await` 는 **모듈 코드에서만** 된다 · `async` 함수의 로그는 **제너레이터 + 러너**와 틱 단위로 같았다.

## 관련 자료

- [ECMA-262 — Async Function Objects](https://tc39.es/ecma262/multipage/control-abstraction-objects.html#sec-async-function-objects) · [TC39 finished proposals](https://github.com/tc39/proposals/blob/main/finished-proposals.md)
- [`history/js/04-비동기-진화.md`](../../../../../../history/js/04-비동기-진화.md) — ★ **경계**: 그쪽은 **`co` 러너에서 `async`/`await` 까지의 연혁과 순차/병렬의 개념 그림**, 여기는 **그 멈춤·재개를 로그와 틱으로 재는 것**부터.
- [37 — Promise 상태 모델](../37-promise-state-model/2-summary.md) — 흡수 규칙 · 틱 세는 창 · 미처리 거부. [36](../36-event-loop-and-microtasks/2-summary.md) · [38](../38-promise-combinators/2-summary.md).
- [20 — 제너레이터](../20-generators/2-summary.md) — `yield` 흐름의 정본. [32 — 오류 처리와 `Error`](../32-error-handling-and-error/2-summary.md) — `return` 이 완료 기록에 담기는 시점. [35 — 엄격 모드](../35-strict-mode/2-summary.md) — early error.
- [26 — 배열 탐색·평탄화·생성](../26-array-search-flatten-and-create/2-summary.md) — `Array.fromAsync` 대 `Promise.all`.
- 파이썬 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **51번** · [Python 17 — 제너레이터](../../../python/syntax/17-generators-yield/2-summary.md) · 러스트 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **54번**.
- 목록의 **40번 주제**(비동기 이터레이션) · **41번 주제**(취소와 타임아웃) · **42번 주제**(ESM 모듈).

## 용어 풀이

- **`async` 함수** — 부르면 프라미스를 돌려주고, 안에서 `await` 로 멈출 수 있는 함수.
- **`await`** — 피연산자가 확정될 때까지 **이 함수만** 멈추는 연산자. 재개는 마이크로태스크다.
- **`AsyncFunctionStart`** — 본문을 곧바로 돌리기 시작하는 명세 연산.
- **`Await`** — `PromiseResolve` → `PerformPromiseThen` → 호출자로 돌아가는 명세 연산.
- **순차 / 병렬(겹침)** — 이 문서의 말로는 「`b` 를 `a` 가 끝난 뒤에 불렀나 / 전에 불렀나」. 시간이 아니라 **시작 순서**다.
- **최상위 `await`(top-level await)** — 모듈의 맨 바깥에서 쓰는 `await`(ES2022).
- **러너(runner)** — 제너레이터가 `yield` 한 프라미스를 기다렸다가 `next`/`throw` 로 다시 넣어 주는 함수. `co` 가 대표였다.
- **코루틴(파이썬)** — `async def` 를 부르면 나오는 객체. 루프에 올리기 전에는 본문이 안 돈다.

## 더 들어가면

- **최상위 `await` 가 모듈 그래프에 주는 영향** — 그 모듈을 `import` 한 쪽의 평가가 기다린다고 알려져 있다. **이 문서는 돌리지 않았다**(42번).
- **옛 명세의 `await` 틱 수** — ES2019 전의 `await` 는 진짜 프라미스에도 틱을 더 먹었다고 알려져 있다. 이 머신의 세 판은 모두 새 모양이었다.
- **`async` 함수의 스택 추적**(V8 의 async stack trace) — 명세 밖이다. 재지 않았다.
