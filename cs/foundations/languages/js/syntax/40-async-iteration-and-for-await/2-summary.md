# js/syntax/40 — 비동기 이터레이션: 「`for await` 는 값마다 기다리고, 떠날 때 `return()` 을 기다리며, 동기 이터러블은 감싸서 쓴다」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> ★★★ **이 주제의 본체는 ② 전수 격자다** — 루프 셋(`for...of` + 동기 제너레이터 · `for await` + async generator · `for await` + **프라미스를 내는 동기 제너레이터**) × 루프가 끝나는 법 다섯(`break` · `return` · `throw` · 끝까지 · **값이 거부된 프라미스**) = 15칸에서 **`return()` 이 불렸나 · `finally` 가 돌았나**를 찍고, 마지막 줄에 「**동기판과 갈린 칸 N / M**」을 스크립트가 찍는다(동작 (1)).
> ★★ 보조로 **① 추상 연산에 로그 심기**(`Symbol.asyncIterator`/`Symbol.iterator` 를 읽는 getter · 계수 잡의 `@k` · `next()` 세 번의 줄 순서)와 **④ 예외의 `constructor.name` + `message`**(이터러블이 아닐 때의 `TypeError`)를 쓴다.
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262 — `GetIterator`](https://tc39.es/ecma262/multipage/abstract-operations.html) — 「kind 가 async 면 `@@asyncIterator` 를 먼저 찾고, **없으면 `@@iterator` 를 찾아 `CreateAsyncFromSyncIterator` 로 감싼다**」 · `AsyncIteratorClose` — 「`return` 을 부르고 그 결과를 **`Await`** 한다」
> - [ECMA-262 — `Yield` · `AsyncGeneratorYield` · `AsyncFromSyncIteratorContinuation`](https://tc39.es/ecma262/multipage/control-abstraction-objects.html) — 「genKind 가 async 면 `AsyncGeneratorYield(? Await(arg))`」 · 「**queue 가 비어 있지 않으면 멈추지 않고 계속 간다**」 · 「값 프라미스가 거부되면 **`closeOnRejection` 일 때 동기 이터레이터를 닫는다**」
> - [ECMA-262 2025 (16판)](https://262.ecma-international.org/16.0/) · [2024 (15판)](https://262.ecma-international.org/15.0/) — **`closeOnRejection` 이라는 낱말이 16판에는 있고 15판·14판에는 없다**(본문 문자열 검색: 4건 / 0건 / 0건)
> - [TC39 finished proposals](https://github.com/tc39/proposals/blob/main/finished-proposals.md) — 판 경계(Asynchronous Iteration **2018** · `Array.fromAsync` **2026**)
> - [Node.js v20 — `--unhandled-rejections`](https://nodejs.org/docs/latest-v20.x/api/cli.html#--unhandled-rejectionsmode) — 동작 (2)의 `exit 1` 이 어디서 오나(37번과 같다)
>
> ★★★ **명세 조항 번호는 인용하지 않는다.** 규칙 진술은 **추상 연산 이름**으로, 순서·틱 수·예외는 **전부 실행으로** 접지했다.
>
> **실행 검증** — 이 문서의 모든 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다.
> 배너의 `node20` 은 `~/.nvm/versions/node/v20.19.6/bin/node`, `node18` 은 기본 PATH 의 `node`(v18.19.1)다. Chrome 151 은 `./js40b-browser.sh`(소스는 [42번](../42-esm-modules/2-summary.md) 머리말 — `file://` 에 **`--allow-file-access-from-files`** 를 기본으로 넣었다).
> ★★★ **격자 한 칸이 Chrome 151 과 두 node 판에서 갈렸다** — 동작 (1)의 C 행 `rejects` 칸. 나머지 탐침은 세 판이 한 글자도 같았다(아래 대조기).
> ★★ **시간은 재지 않았다** — 「`for await` 가 느리다」·「스트림이 메모리를 아낀다」를 **쓰지 않는다.**
>
> **버전**
>
> | 무엇 | 판 | 이 머신에서 |
> |---|---|---|
> | `for await...of` · `async function*` · `Symbol.asyncIterator` | **ES2018** | 세 판 다 있다 |
> | 값이 거부되면 감싼 동기 이터레이터를 닫는다(`closeOnRejection`) | **ES2025(16판) 본문에서 처음 보인다** | ★★★ **Chrome 151 만 닫았다**, node 18·20 은 안 닫았다(동작 (1)) |
> | `Array.fromAsync` | **ES2026** | node 18·20 에 없다 · Chrome 151 에 있다(26번) |
>
> ★★ **판 경계는 TC39 finished proposals 표와 이 목록의 README 를 대조했다** — Asynchronous Iteration **2018**. README 40행은 판을 적지 않는다.
>
> **★★★ 이 주제가 쓰는 창 — 그리고 부적용인 창**
>
> | 창 | 이 주제에서 무엇을 보나 |
> |---|---|
> | ★★★ **② 전수 격자**(본체) | 루프 3 × 끝나는 법 5 = 15칸 — `return()` · `finally` · 결과 · 이벤트 줄 · 마지막 줄 「`… differs from row A …: N / 10`」(동작 (1)) · 미리 만든 프라미스 4행(동작 (2)) |
> | ★★ **① 추상 연산에 로그 심기** | `@@asyncIterator`/`@@iterator` 를 **읽는 순간** getter 가 찍는다(동작 (3)) · 계수 잡의 `@k`(동작 (4)) · `next()` 세 번의 줄 순서(동작 (5)) |
> | ★★ **④ 예외의 `constructor.name` + `message`** | 이터러블이 아닌 것에 `for await`/`for...of` → `TypeError` 문구(동작 (3)) · 거부가 어디로 올라오나 |
> | ★ **부적용 — ③ 브랜드 태그** | 판정할 객체의 종류가 없다(async generator 객체가 무엇을 가졌나는 `typeof` 로 충분했다) |
> | ★ **안 쟀다 — 시간·메모리** | 「스트림처럼 조금씩 읽으면 가볍다」는 **이 문서의 근거가 아니다** |
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 판별 블록의 판 문자열 — 머신에 매인다 | ★★★ 격자의 `yes`/`no` · 이벤트 줄 순서 · `@k` · 종료 코드 `0`·`1` — 걸음은 전부 **마이크로태스크나 `setTimeout` 0 하나씩**이다(36번) |
> | ★ **이 주제의 탐침에는 재실행에서 흔들린 칸이 없다**(재대조 동일) | ★★ **판 사이에서 갈린 칸**(C 행 `rejects`)은 흔들림이 아니라 **판의 차이**다 — 세 판 모두 재실행에서 같았다 |
>
> **층** — `for await` 와 async generator 는 **언어(ECMA-262)** 의 것이다. **호스트가 끼는 자리는 둘**이다 — 걸음을 만든 **타이머**와, 기다리기 전에 거부된 프라미스를 **보고하는** node(동작 (2) · 37번).
>
> **선행** — [20 — 제너레이터](../20-generators/2-summary.md)(직접 선행 — ★★★ **`return()` 과 `finally`** 의 동기판이 거기 (3)에 있다) ·
> [19 — 이터러블 프로토콜과 `for...of`](../19-iterable-protocol-and-for-of/2-summary.md)(★★★ **소비자 17가지 중 `return()` 을 부른 것 8** — 이 문서의 A 행이 그 격자의 `break`·`return`·`throw` 줄과 같은 것을 다시 보인다) ·
> [39 — `async`/`await`](../39-async-await/2-summary.md)(★★★ **`await` 의 틱 · 먼저 만든 프라미스의 거부** — 동작 (2)는 39번 동작 (4)의 `for await` 판이다) ·
> [37 — Promise 상태 모델](../37-promise-state-model/2-summary.md)(미처리 거부 보고 · 틱 세는 계수 잡) · [26 — 배열 탐색·평탄화·생성](../26-array-search-flatten-and-create/2-summary.md)(`Array.fromAsync` — 비동기 이터러블을 배열로 모으는 내장 함수).
>
> ★★ **경계** — 동기 쪽 **소비자별 `return()` 호출표는 19번**, 제너레이터 **`return()`·`throw()` 의 상태별 동작은 20번**이 정본이다. 여기서는 **그것이 `for await` 에서 어떻게 달라지나**만 본다.
> ★ **취소**(`AbortSignal` 로 루프를 끊기)는 [41번](../41-cancellation-and-timeouts/2-summary.md), **모듈**은 [42번](../42-esm-modules/2-summary.md)이다.

```text
===== ./js40b-versions.sh (exit=0) =====
node 18.19.1  v8 10.2.154.26-node.28
  ES2018  async function* / for await               yes
  ES2018  Symbol.asyncIterator                      yes
  ES2020  import() in a classic script              yes
  ES2026  Array.fromAsync                           no
  host    AbortController                           yes
  host    AbortSignal.abort                         yes
  host    AbortSignal.timeout                       yes
  host    AbortSignal.any                           yes
  host    AbortSignal.prototype.throwIfAborted      yes
  host    DOMException                              yes
  host    fetch                                     yes
  host    require (this script's scope)             yes
node 20.19.6  v8 11.3.244.8-node.33
  ES2018  async function* / for await               yes
  ES2018  Symbol.asyncIterator                      yes
  ES2020  import() in a classic script              yes
  ES2026  Array.fromAsync                           no
  host    AbortController                           yes
  host    AbortSignal.abort                         yes
  host    AbortSignal.timeout                       yes
  host    AbortSignal.any                           yes
  host    AbortSignal.prototype.throwIfAborted      yes
  host    DOMException                              yes
  host    fetch                                     yes
  host    require (this script's scope)             yes
Google Chrome 151.0.7922.173
  ES2018  async function* / for await               yes
  ES2018  Symbol.asyncIterator                      yes
  ES2020  import() in a classic script              yes
  ES2026  Array.fromAsync                           yes
  host    AbortController                           yes
  host    AbortSignal.abort                         yes
  host    AbortSignal.timeout                       yes
  host    AbortSignal.any                           yes
  host    AbortSignal.prototype.throwIfAborted      yes
  host    DOMException                              yes
  host    fetch                                     yes
  host    require (this script's scope)             no
```

세 판 대조기의 집계 줄 — 전문은 [3-answer.md](3-answer.md) 의 「실행 검증」에 있다.

`node18 vs node20: identical 7 · differs 2   ·   node20 vs Chrome 151: identical 3 · differs 3 · node only 3`

## 한눈에 — 쉽게 말하면

**`for await` 는 「택배를 하나씩 받는 사람」이다. 문을 열 때마다(`next()`) 상자가 오기를 기다리고, 상자 안의 물건(값)만 꺼내 쓴다. 다 받기 전에 그만두면 택배사에 「그만 보내세요」(`return()`)를 전화하고, 그 통화가 끝날 때까지 문 앞에 서 있는다.**

- ★★★ **상자가 아니라 물건을 받는다** — 루프 몸통에 오는 것은 **프라미스가 아니라 확정된 값**이다. async generator 의 `yield` 도 **값을 기다린 뒤** 내보낸다.
- ★★★ **그만두는 법은 달라도 전화는 똑같이 건다** — `break` · `return` · `throw` 셋 다 `return()` 이 불리고 `finally` 가 돈다. **동기 `for...of` 와 같은 모양**이다.
- ★★ **전화 통화도 기다린다** — 정리 코드(`finally`) 안에 `await` 가 있으면 **루프 뒤의 줄은 그것이 끝난 뒤에** 돈다.
- ★★★ **미리 쌓아 둔 상자 더미를 하나씩 뜯으면 위험하다** — `[p1, p2, p3]` 를 `for await` 로 돌면 **p2 가 먼저 깨졌을 때 아무도 안 보고 있다**(미처리 거부).

```text
   for await (const v of src) { … }

   src[@@asyncIterator] ?  ── 있다 ──▶  그 이터레이터
          │ 없다
          ▼
   src[@@iterator] ?       ── 있다 ──▶  감싼다(CreateAsyncFromSyncIterator) — 값마다 Await
          │ 없다
          ▼
   TypeError

   매 바퀴:  await it.next()  ─▶  { value, done }  ─▶  몸통은 value(확정된 값)를 받는다
   떠날 때:  await it.return()   ← break · return · throw 모두
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 문을 열고 상자를 기다린다 | 매 바퀴 `Await(it.next())` | 동작 (4)의 `@k` |
| 상자 안의 물건만 꺼낸다 | 몸통이 받는 `value` 는 확정된 값 — async generator 의 `yield` 는 `Await(arg)` 뒤에 내보낸다 | 동작 (4)의 `body got string "v"` |
| 「그만 보내세요」 전화 | `AsyncIteratorClose` — `return()` 을 부르고 **그 결과를 `Await`** | 동작 (1) 격자 · 동작 (3)의 `[4]` |
| 동기 택배사를 비동기 창구로 | `CreateAsyncFromSyncIterator` — `@@iterator` 만 있는 것을 감싼다 | 동작 (3)의 `iterator only` |
| 미리 쌓아 둔 상자 더미 | 이미 만들어 둔 프라미스 배열 | 동작 (2) |

**똑같은 구조다** — 실무에서 물리는 자리도 굳어 있다.
「**페이지를 넘기며 API 를 읽는 async generator 를 `break` 했더니 연결 정리가 돌았다**」,
「**`for await (const r of urls.map(fetch))` 에서 두 번째 요청이 먼저 실패하자 프로세스가 죽었다**」,
「**`for...of` 로 async generator 를 돌렸더니 `is not iterable`**」이 그것이다(동작 (1)·(2)·(3)).

> **async generator** — `async function*` 로 만드는 함수. 부르면 **`next()` 가 프라미스를 돌려주는** 이터레이터가 나온다.\
> 예: `async function* pages() { let p = 1; while (p <= 3) yield await load(p++); }`

## 이 주제가 답하려는 질문

1. **`for await` 가 루프를 떠날 때 `return()` 과 `finally` 는 언제 도나** — 동기 `for...of` 와 **어느 칸이 다르나**, 동기 이터러블을 감쌀 때는?
2. **이미 만들어 둔 프라미스 배열을 `for await` 로 돌면 무엇이 위험한가** — `Promise.all` · async generator 와 무엇이 다른가?
3. **`for await` 는 어떤 메서드를 먼저 찾고, 몸통은 무엇을 받나** — `yield` 는 값을 기다리나, 몇 틱인가, `next()` 를 겹쳐 부르면?

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 출력으로 읽는다.

### (1) ★★★ 동기판 대 비동기판 `return()` 격자 — 15칸

**언제 쓰나** — async generator 안에 **정리 코드**(연결 닫기·구독 해제)를 `try`/`finally` 로 둘 때 · 동기 이터러블(배열·제너레이터)을 `for await` 로 돌릴 때.
★★★ 이터레이터의 `return` 을 **자기 속성으로 덮어** 불리면 `return()` 을 찍게 했다. 제너레이터의 `finally` 는 `finally` 를 찍는다. 몸통은 **둘째 값**에서 움직인다.

```js
// js40b-40a-close-grid.js
// Three loops x five ways the loop ends. In each cell: is the iterator's return() called? does the generator's finally run?
//   A  for...of   over a sync generator            (values 1, 2, 3)
//   B  for await  over an async generator          (values 1, 2, 3)
//   C  for await  over a sync generator of promises (Promise.resolve(1), ...(2), ...(3))
// The loop body acts on the second value. In the "rejects" column the second value is a rejected promise.
const rejected = () => { const p = Promise.reject(new Error("rejected value")); p.catch(() => {}); return p; };
function* syncGen(L, vals) { try { for (const v of vals) yield v; } finally { L.push("finally"); } }
async function* asyncGen(L, vals) { try { for (const v of vals) yield v; } finally { L.push("finally"); } }
const watch = (it, L) => { const r = it.return; it.return = function (v) { L.push("return()"); return r.call(this, v); }; return it; };
const show = (v) => (v instanceof Promise ? "a Promise" : String(v));
const exits = ["break", "return", "throw", "end", "rejects"];
const values = (exit, wrap) => [1, 2, 3].map((v) => (exit === "rejects" && v === 2 ? rejected() : wrap ? Promise.resolve(v) : v));
const act = (exit, v, L) => {
  L.push("got " + show(v));
  if (v !== 2) return "";
  if (exit === "break") return "break";
  if (exit === "return") return "return";
  if (exit === "throw") throw new Error("body threw");
  return "";
};
const loops = {
  "A for...of + sync generator": (exit, L) => {
    const run = () => { for (const v of watch(syncGen(L, values(exit, false)), L)) { const a = act(exit, v, L); if (a === "break") break; if (a === "return") return "returned"; } return "completed"; };
    try { const r = run(); return Promise.resolve(r === "completed" && exit === "break" ? "left by break" : r); } catch (e) { return Promise.resolve("caught " + e.message); }
  },
  "B for await + async generator": async (exit, L) => {
    const run = async () => { for await (const v of watch(asyncGen(L, values(exit, false)), L)) { const a = act(exit, v, L); if (a === "break") break; if (a === "return") return "returned"; } return "completed"; };
    try { const r = await run(); return r === "completed" && exit === "break" ? "left by break" : r; } catch (e) { return "caught " + e.message; }
  },
  "C for await + sync generator of promises": async (exit, L) => {
    const run = async () => { for await (const v of watch(syncGen(L, values(exit, true)), L)) { const a = act(exit, v, L); if (a === "break") break; if (a === "return") return "returned"; } return "completed"; };
    try { const r = await run(); return r === "completed" && exit === "break" ? "left by break" : r; } catch (e) { return "caught " + e.message; }
  },
};
(async () => {
  const cells = {};
  for (const [name, loop] of Object.entries(loops)) {
    console.log(name);
    for (const exit of exits) {
      const L = [];
      const outcome = await loop(exit, L);
      const key = [L.includes("return()"), L.includes("finally")];
      cells[name[0] + exit] = key.join();
      console.log("  " + exit.padEnd(8) + ("return() " + (key[0] ? "yes" : "no ")).padEnd(13) + ("finally " + (key[1] ? "yes" : "no ")).padEnd(13) + outcome.padEnd(24) + L.join(" > "));
    }
  }
  let n = 0, m = 0;
  for (const row of ["B", "C"]) for (const exit of exits) { m++; if (cells[row + exit] !== cells["A" + exit]) n++; }
  console.log("cells where a for await row differs from row A in (return() called, finally ran): " + n + " / " + m);
})();
```

```text
===== node20 js40b-40a-close-grid.js (exit=0) =====
A for...of + sync generator
  break   return() yes finally yes  left by break           got 1 > got 2 > return() > finally
  return  return() yes finally yes  returned                got 1 > got 2 > return() > finally
  throw   return() yes finally yes  caught body threw       got 1 > got 2 > return() > finally
  end     return() no  finally yes  completed               got 1 > got 2 > got 3 > finally
  rejects return() no  finally yes  completed               got 1 > got a Promise > got 3 > finally
B for await + async generator
  break   return() yes finally yes  left by break           got 1 > got 2 > return() > finally
  return  return() yes finally yes  returned                got 1 > got 2 > return() > finally
  throw   return() yes finally yes  caught body threw       got 1 > got 2 > return() > finally
  end     return() no  finally yes  completed               got 1 > got 2 > got 3 > finally
  rejects return() no  finally yes  caught rejected value   got 1 > finally
C for await + sync generator of promises
  break   return() yes finally yes  left by break           got 1 > got 2 > return() > finally
  return  return() yes finally yes  returned                got 1 > got 2 > return() > finally
  throw   return() yes finally yes  caught body threw       got 1 > got 2 > return() > finally
  end     return() no  finally yes  completed               got 1 > got 2 > got 3 > finally
  rejects return() no  finally no   caught rejected value   got 1
cells where a for await row differs from row A in (return() called, finally ran): 1 / 10
```

같은 소스를 Chrome 151 에서 — **C 행 마지막 칸만** 다르다(node 18 은 node 20 과 한 글자도 같았다 — 대조기).

```text
===== ./js40b-browser.sh js40b-40a-close-grid.js (exit=0) =====
A for...of + sync generator
  break   return() yes finally yes  left by break           got 1 > got 2 > return() > finally
  return  return() yes finally yes  returned                got 1 > got 2 > return() > finally
  throw   return() yes finally yes  caught body threw       got 1 > got 2 > return() > finally
  end     return() no  finally yes  completed               got 1 > got 2 > got 3 > finally
  rejects return() no  finally yes  completed               got 1 > got a Promise > got 3 > finally
B for await + async generator
  break   return() yes finally yes  left by break           got 1 > got 2 > return() > finally
  return  return() yes finally yes  returned                got 1 > got 2 > return() > finally
  throw   return() yes finally yes  caught body threw       got 1 > got 2 > return() > finally
  end     return() no  finally yes  completed               got 1 > got 2 > got 3 > finally
  rejects return() no  finally yes  caught rejected value   got 1 > finally
C for await + sync generator of promises
  break   return() yes finally yes  left by break           got 1 > got 2 > return() > finally
  return  return() yes finally yes  returned                got 1 > got 2 > return() > finally
  throw   return() yes finally yes  caught body threw       got 1 > got 2 > return() > finally
  end     return() no  finally yes  completed               got 1 > got 2 > got 3 > finally
  rejects return() yes finally yes  caught rejected value   got 1 > return() > finally
cells where a for await row differs from row A in (return() called, finally ran): 1 / 10
```

- ★★★ **`break` · `return` · `throw` · 끝까지 — 네 열은 세 행이 한 글자도 같다.** 앞의 셋은 `return() yes · finally yes`, 끝까지는 `return() no · finally yes` 다. 19번 격자에서 `break`·`return`·몸통의 `throw` 가 **전부 `return()`** 이었던 것과 같은 모양이다 — **`for await` 도 같은 규칙으로 닫는다.**
- ★★★ **갈린 것은 `rejects` 열 하나다**(`1 / 10`) — 그런데 **세 행이 세 가지로** 갈렸다.
  - **A**(`for...of`) — 거부된 프라미스는 **그냥 값**이다(`got a Promise`). 기다리지 않으니 던지지도 않고 **끝까지** 간다.
  - **B**(async generator) — `yield` 가 값을 **기다리다 거부를 받아** 제너레이터 **안에서** 던져진다. 그래서 `finally` 는 **제너레이터 스스로** 돌리고, 루프는 `caught rejected value` 로 나온다. **`return()` 은 안 불렸다** — 닫을 필요가 없다(이미 끝났다).
  - **C**(동기 제너레이터 + 프라미스) — 제너레이터는 거부된 프라미스를 **값으로 내보냈을 뿐** 아무 일도 없다. 기다리는 쪽은 **감싸개**(`CreateAsyncFromSyncIterator`)다.
- ★★★ **C 행 `rejects` 칸이 판마다 갈렸다** — **node 18·20 은 `return() no · finally no`**(제너레이터가 **열린 채 버려졌다**), **Chrome 151 은 `return() yes · finally yes`** 다. 명세 본문의 `AsyncFromSyncIteratorContinuation` 이 「값 프라미스가 거부되면 **`closeOnRejection` 일 때 동기 이터레이터를 닫는다**」고 적고, 그 낱말이 **ES2025(16판)에서 처음 보인다**(15판·14판 0건). node 20 의 V8(11.3)이 그 판보다 앞선다 — **판의 차이이지 흔들림이 아니다.**

```text
   「rejects」 열 — 둘째 값이 거부된 프라미스일 때 누가 그것을 기다리나

   A  for...of   · 동기 gen      아무도 안 기다린다 ── 값으로 받는다 ──▶ 끝까지 · finally(끝나서)
   B  for await  · async gen     gen 안의 yield 가 Await ── gen 안에서 던진다 ──▶ finally(gen 이 스스로) · return() 없음
   C  for await  · 동기 gen       감싸개가 Await ── 거부 ──┬─▶ node 18·20 : gen 을 안 닫는다 → finally 없음
                                                     └─▶ Chrome 151  : IteratorClose → return() → finally
```

### (2) ★★★ 미리 만든 프라미스 배열 — 뒤의 것이 먼저 거부되면

**언제 쓰나** — `for await (const r of urls.map(fetchIt))` 처럼 **프라미스 배열**을 `for await` 로 돌 때.
★★ `a` 는 세 걸음 뒤 이행, `b` 는 **한 걸음 뒤 거부**, `c` 는 두 걸음 뒤 이행, `d` 는 세 걸음 뒤 거부. 행마다 새 프로세스다(39번 동작 (4)와 같은 방식). 네 번째 행은 **async generator 가 `yield` 할 때 하나씩 만든다.**

```js
// js40b-40-h-premade.js
// Promises made up front, then consumed one by one with for await (argv[2] says how).
//   a: succeeds after three steps · b: rejects after one step · c: succeeds after two steps · d: rejects after three steps
// argv[3] === "hooks" installs node's process events and prints them on standard output.
const how = process.argv[2];
if (process.argv[3] === "hooks") {
  process.on("unhandledRejection", (r) => console.log("unhandledRejection(" + r.message + ")"));
  process.on("rejectionHandled", () => console.log("rejectionHandled"));
}
const steps = (n) => new Promise((r) => { const go = (k) => (k === 0 ? r() : setTimeout(go, 0, k - 1)); go(n); });
const ok = async (name, n) => { await steps(n); console.log(name + " settles"); return name; };
const bad = async (name, n) => { await steps(n); console.log(name + " rejects"); throw new Error(name); };
(async () => {
  try {
    if (how === "array-a-b-c") { for await (const v of [ok("a", 3), bad("b", 1), ok("c", 2)]) console.log("got " + v); }
    if (how === "array-b-d") { for await (const v of [bad("b", 1), bad("d", 3)]) console.log("got " + v); }
    if (how === "all-a-b-c") { for (const v of await Promise.all([ok("a", 3), bad("b", 1), ok("c", 2)])) console.log("got " + v); }
    if (how === "gen-a-b-c") {
      async function* lazy() { yield ok("a", 3); yield bad("b", 1); yield ok("c", 2); }
      for await (const v of lazy()) console.log("got " + v);
    }
  } catch (e) {
    console.log("caught " + e.constructor.name + " 「" + e.message + "」");
  }
})();
```

```sh
# js40b-40b-premade.sh
#!/usr/bin/env bash
# Promises made up front and consumed with for await -- against Promise.all and a lazy async generator.
# With hooks: standard output. No hooks: exit code only.
set -u -o pipefail
cd "$(dirname "$0")"
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
same=0; t=0
for how in array-a-b-c array-b-d all-a-b-c gen-a-b-c; do
  t=$((t + 1))
  echo "--- $how"
  out="$("$N20" js40b-40-h-premade.js "$how" hooks | paste -sd' ' -)"
  echo "  with hooks : $out"
  "$N20" js40b-40-h-premade.js "$how" > /dev/null 2>&1
  e=$?
  echo "  no hooks   : exit $e"
  o18="$("$N18" js40b-40-h-premade.js "$how" hooks | paste -sd' ' -)"
  "$N18" js40b-40-h-premade.js "$how" > /dev/null 2>&1
  [ "$o18 $?" = "$out $e" ] && same=$((same + 1))
done
echo ""
echo "rows where node18 gives the same two answers as node20: $same / $t"
```

```text
===== ./js40b-40b-premade.sh (exit=0) =====
--- array-a-b-c
  with hooks : b rejects unhandledRejection(b) c settles a settles got a caught Error 「b」 rejectionHandled
  no hooks   : exit 1
--- array-b-d
  with hooks : b rejects caught Error 「b」 d rejects unhandledRejection(d)
  no hooks   : exit 1
--- all-a-b-c
  with hooks : b rejects caught Error 「b」 c settles a settles
  no hooks   : exit 0
--- gen-a-b-c
  with hooks : a settles got a b rejects caught Error 「b」
  no hooks   : exit 0

rows where node18 gives the same two answers as node20: 4 / 4
```

```text
   array-a-b-c:  [a(), b(), c()]  ── 셋 다 지금 시작한다
                 for await 는 a 를 기다리는 중 ─ b 가 한 걸음 뒤 거부 ─ 그 순간 b 에 처리기가 없다 ─▶ unhandledRejection
                 a 가 끝나야 b 차례 ─ 이제야 처리기가 달린다 ─▶ caught · rejectionHandled   (훅 없으면 exit 1)

   array-b-d:    b 가 먼저 거부 ─▶ 루프가 b 에서 던지고 떠난다 ─ d 는 아무도 안 기다린다 ─▶ d 거부 = unhandledRejection

   all-a-b-c:    Promise.all 이 셋에 처리기를 곧바로 건다 ─▶ 보고 없음 · exit 0
   gen-a-b-c:    lazy() 가 yield 할 때 하나씩 만든다 ─▶ a 뒤에야 b 가 시작 · c 는 시작도 안 한다 · exit 0
```

- ★★★ **`array-a-b-c` 는 `caught Error 「b」` 가 찍히는데도 `unhandledRejection(b)` 가 먼저 끼고, 훅이 없으면 `exit 1`** 이다 — `try`/`catch` 가 코드에 **분명히 있다.** `for await` 는 배열을 **하나씩** 기다리므로, `a` 를 기다리는 동안 먼저 깨진 `b` 에는 **처리기가 없다.**
- ★★★ **`array-b-d` 는 다른 모양의 같은 함정** — 루프는 `b` 에서 **던지고 떠난다.** 뒤에 남은 `d` 는 **영영 기다려지지 않아** 거부가 처리기 없이 도착한다(`unhandledRejection(d)` · `exit 1`).
- ★★ **`all-a-b-c`·`gen-a-b-c` 는 `exit 0`** — `Promise.all` 은 **모두에 곧바로** 처리기를 걸고, async generator 는 **당길 때 만든다**(`a settles got a b rejects` — `c` 는 **시작도 안 했다**).
- ★★ 두 node 판이 **같은 두 답**을 냈다(`4 / 4`). 보고와 종료 코드는 **node 의 것**이다(37번 동작 (5)가 정본).

### (3) ★★ 어떤 메서드를 찾나 — `@@asyncIterator` 먼저, 없으면 `@@iterator` 를 감싼다

**언제 쓰나** — 직접 만든 객체를 `for await` 와 `for...of` 양쪽에 쓰게 할 때 · async generator 를 `for...of` 에 잘못 넣었을 때.
★★ 두 심볼 속성을 **getter** 로 달아 **읽는 순간** 찍게 했다.

```js
// js40b-40c-which-protocol.js
// Which method does each loop look up? Getters log every read of Symbol.asyncIterator / Symbol.iterator.
const show = (e) => e.constructor.name + " 「" + e.message + "」";
const make = (L, withAsync, withSync) => {
  const o = {};
  if (withAsync) Object.defineProperty(o, Symbol.asyncIterator, { get() { L.push("get asyncIterator"); return async function* () { yield "from async"; }; } });
  if (withSync) Object.defineProperty(o, Symbol.iterator, { get() { L.push("get iterator"); return function* () { yield "from sync"; }; } });
  return o;
};
const cases = [["both", true, true], ["asyncIterator only", true, false], ["iterator only", false, true], ["neither", false, false]];
(async () => {
  console.log("[1] for await ... of");
  for (const [label, a, s] of cases) {
    const L = [];
    try { for await (const v of make(L, a, s)) L.push("got " + v); } catch (e) { L.push(show(e)); }
    console.log("  " + label.padEnd(20) + L.join(" > "));
  }
  console.log("[2] for ... of");
  for (const [label, a, s] of cases) {
    const L = [];
    try { for (const v of make(L, a, s)) L.push("got " + v); } catch (e) { L.push(show(e)); }
    console.log("  " + label.padEnd(20) + L.join(" > "));
  }
  console.log("[3] an async generator object");
  async function* ag() { yield 1; }
  const g = ag();
  console.log("  typeof g[Symbol.asyncIterator] " + typeof g[Symbol.asyncIterator] + " · typeof g[Symbol.iterator] " + typeof g[Symbol.iterator] + " · g[Symbol.asyncIterator]() === g " + (g[Symbol.asyncIterator]() === g));
  try { for (const v of ag()) console.log(v); } catch (e) { console.log("  for...of over it: " + show(e)); }
  try { console.log([...ag()]); } catch (e) { console.log("  spread of it:     " + show(e)); }

  console.log("[4] break out of for await -- the generator's finally contains an await");
  const L = [];
  const step = () => new Promise((r) => setTimeout(r, 0));
  async function* withCleanup() { try { yield 1; yield 2; } finally { L.push("finally start"); await step(); L.push("finally end"); } }
  for await (const v of withCleanup()) { L.push("got " + v); break; }
  L.push("line after the loop");
  console.log("  " + L.join(" > "));
})();
```

```text
===== node20 js40b-40c-which-protocol.js (exit=0) =====
[1] for await ... of
  both                get asyncIterator > got from async
  asyncIterator only  get asyncIterator > got from async
  iterator only       get iterator > got from sync
  neither             TypeError 「make(...) is not a function or its return value is not async iterable」
[2] for ... of
  both                get iterator > got from sync
  asyncIterator only  TypeError 「make is not a function or its return value is not iterable」
  iterator only       get iterator > got from sync
  neither             TypeError 「make is not a function or its return value is not iterable」
[3] an async generator object
  typeof g[Symbol.asyncIterator] function · typeof g[Symbol.iterator] undefined · g[Symbol.asyncIterator]() === g true
  for...of over it: TypeError 「ag is not a function or its return value is not iterable」
  spread of it:     TypeError 「ag is not a function or its return value is not iterable」
[4] break out of for await -- the generator's finally contains an await
  got 1 > finally start > finally end > line after the loop
```

```text
                         @@asyncIterator 만   @@iterator 만        둘 다               둘 다 없음
   for await ... of      그것을 쓴다           감싸서 쓴다           @@asyncIterator     TypeError
   for ... of            TypeError            그것을 쓴다           @@iterator          TypeError
                         ▲ async generator 객체가 이 칸이다
```

- ★★★ **`both` 는 `for await` 가 `get asyncIterator` 만, `for...of` 가 `get iterator` 만 읽었다** — 각자 **자기 것 하나만** 찾는다. `iterator only` 를 `for await` 에 주면 **`get iterator` 로 내려가** 돌았다(감싸개).
- ★★★ **거꾸로는 안 된다** — `asyncIterator only` 를 `for...of` 에 주면 `TypeError`. async generator 객체도 `typeof g[Symbol.iterator] undefined` 라 **`for...of`·스프레드가 둘 다 `TypeError`** 다.
- ★★ **문구가 원인을 가리키지 않는다** — `make is not a function or its return value is not iterable` 에서 `make` 는 **함수가 맞다.** V8 이 호출식 전체를 한 문장으로 뭉뚱그린 것이다. `for await` 쪽은 `make(...)` · `async iterable` 로 **글자가 조금 다르다.** 근거는 **`TypeError` 라는 종류**와 **getter 로그**다.
- ★★★ **`[4]` — `finally` 안의 `await` 가 끝나야 루프 뒤의 줄이 돈다**(`finally start > finally end > line after the loop`). `AsyncIteratorClose` 가 `return()` 의 결과를 **`Await`** 하기 때문이다.

### (4) ★★ `yield` 는 값을 기다린다 — 몸통이 받는 것과 틱

**언제 쓰나** — async generator 에서 `yield promise` 와 `yield await promise` 중 무엇을 쓸지 · 동기 제너레이터가 낸 프라미스가 어디서 풀리는지.
★★ 39번 동작 (2)와 같은 **계수 잡**이다 — `@k` 는 루프를 시작한 뒤 **k 틱**.

```js
// js40b-40d-yield-and-ticks.js
// [1] What does the loop body receive, and after how many microtask ticks does it first run?
//     A counter job requeues itself once per tick; @k = k ticks since the loop started.
// [2] it.next() on an async generator, called three times in a row without waiting.
const settledP = Promise.resolve("v");
const kind = (v) => (v instanceof Promise ? "a Promise" : typeof v + " " + JSON.stringify(v));
const measure = (label, loop) => new Promise((done) => {
  let tick = 0, stop = false;
  const counter = () => { if (stop) return; tick++; queueMicrotask(counter); };
  const ev = [];
  queueMicrotask(counter);
  loop((v) => ev.push("body got " + kind(v) + " @" + tick)).then(() => { stop = true; });
  setTimeout(() => { console.log("  " + label.padEnd(44) + ev.join(" > ")); done(); }, 0);
});
(async () => {
  console.log("[1] one value, one loop");
  await measure("async gen: yield 1", async (f) => { async function* g() { yield 1; } for await (const v of g()) f(v); });
  await measure("async gen: yield settledP", async (f) => { async function* g() { yield settledP; } for await (const v of g()) f(v); });
  await measure("async gen: yield await settledP", async (f) => { async function* g() { yield await settledP; } for await (const v of g()) f(v); });
  await measure("for await over [1]", async (f) => { for await (const v of [1]) f(v); });
  await measure("for await over [settledP]", async (f) => { for await (const v of [settledP]) f(v); });
  await measure("for...of over sync gen: yield settledP", async (f) => { function* g() { yield settledP; } for (const v of g()) f(v); });

  console.log("[2] three it.next() calls in a row");
  const L = [];
  const step = () => new Promise((r) => setTimeout(r, 0));
  async function* slow() { for (let i = 1; i <= 3; i++) { L.push("body: step " + i + " begins"); await step(); L.push("body: yield " + i); yield i; } }
  const it = slow();
  const ps = [it.next(), it.next(), it.next()];
  L.push("caller: three next() calls returned " + ps.map((p) => (p instanceof Promise ? "Promise" : typeof p)).join(","));
  ps.forEach((p, i) => p.then((r) => L.push("caller: next#" + (i + 1) + " -> " + JSON.stringify(r))));
  await Promise.all(ps);
  await step();
  console.log("  " + L.join("\n  "));
})();
```

```text
===== node20 js40b-40d-yield-and-ticks.js (exit=0) =====
[1] one value, one loop
  async gen: yield 1                          body got number 1 @2
  async gen: yield settledP                   body got string "v" @2
  async gen: yield await settledP             body got string "v" @3
  for await over [1]                          body got number 1 @2
  for await over [settledP]                   body got string "v" @2
  for...of over sync gen: yield settledP      body got a Promise @0
[2] three it.next() calls in a row
  body: step 1 begins
  caller: three next() calls returned Promise,Promise,Promise
  body: yield 1
  body: step 2 begins
  caller: next#1 -> {"value":1,"done":false}
  body: yield 2
  body: step 3 begins
  caller: next#2 -> {"value":2,"done":false}
  body: yield 3
  caller: next#3 -> {"value":3,"done":false}
```

```text
   async function* g() { yield settledP; }       Yield(arg) — async 면 AsyncGeneratorYield(? Await(arg))

   ① Await(settledP)   ← 제너레이터가 스스로 기다린다
   ② 값 "v" 로 next() 의 프라미스를 이행한다
   ③ for await 가 그 프라미스를 Await ─▶ 몸통: string "v"

   function* g() { yield settledP; }  +  for...of  ─▶ 아무도 안 기다린다 ─▶ 몸통: a Promise @0
```

- ★★★ **`yield settledP` 도 몸통에는 `string "v"`** 가 왔다 — 명세의 `Yield` 가 async 제너레이터에서는 **`AsyncGeneratorYield(? Await(arg))`** 다. 동기 제너레이터를 `for...of` 로 돌면 **`a Promise @0`** — 아무도 안 기다린다.
- ★★ **`yield 1` 과 `yield settledP` 가 같은 `@2`**, **`yield await settledP` 는 `@3`** — `await` 를 하나 더 쓰면 **한 틱 더** 든다. 배열을 감싼 `for await` 도 `@2` 였다.
- ★ 세 판이 같은 `@k` 를 냈다. 이 문서는 **이 판의 잡 개수**를 보일 뿐 옛 판의 틱 수를 말하지 않는다.

### (5) ★★ `next()` 를 겹쳐 부르면 — 줄을 선다

**언제 쓰나** — async generator 의 `next()` 를 `await` 없이 여러 번 부를 때(`Promise.all([it.next(), it.next()])`).
위 소스의 `[2]` 다. 본문의 각 걸음은 `setTimeout` 0 하나를 기다린다.

```text
   caller: next() next() next()  ── 세 요청이 큐에 선다 (AsyncGeneratorQueue)

   body: step 1 … yield 1 ──▶ next#1 이행
     └ 큐가 비어 있지 않다 ─▶ 멈추지 않고 계속: step 2 … yield 2 ──▶ next#2 이행
                                               └ step 3 … yield 3 ──▶ next#3 이행
```

- ★★★ **세 호출이 모두 곧바로 `Promise` 를 돌려주고**, 본문은 **한 번에 한 걸음씩** 돌았다 — `next#1` 이 `1`, `next#2` 가 `2` 로 **요청한 순서대로** 이행됐다. 겹쳐 불러도 **본문이 둘로 갈라져 돌지 않는다.**
- ★★ **`body: step 2 begins` 가 `caller: next#1 -> …` 보다 먼저** 찍혔다 — `AsyncGeneratorYield` 가 「**queue 가 비어 있지 않으면 멈추지 않고 계속 간다**」고 적은 그대로다. 동기 제너레이터에는 이 큐가 없다 — 실행 중에 자기 `next()` 를 부르면 `TypeError 「Generator is already running」` 이었다(20번 동작 (7)).

## 문법 — 형태와 규칙

★ 이 절은 **형태 표**다 — 모든 동작 주장은 위 동작 절의 캡처 블록에서만 한다.

| 형태 | 하는 일 | 판 | 어디서 봤나 |
|---|---|---|---|
| `for await (const v of src) {}` | `@@asyncIterator` → 없으면 `@@iterator` 를 **감싸서** · 매 바퀴 `next()` 결과를 **`Await`** | ES2018 | 동작 (3)·(4) |
| `async function* g() {}` | 부르면 **`next()`·`return()`·`throw()` 가 프라미스를 돌려주는** 이터레이터 | ES2018 | 동작 (3)·(5) |
| `yield x` (async generator 안) | `x` 를 **기다린 뒤** 그 값을 내보낸다 | ES2018 | 동작 (4) |
| `yield* src` (async generator 안) | 안쪽 비동기(또는 감싼 동기) 이터레이터에 위임 | ES2018 | (이 문서는 따로 재지 않았다 — 20번의 `yield*` 가 동기판) |
| `[Symbol.asyncIterator]() { return this; }` | 직접 만든 비동기 이터러블 | ES2018 | 동작 (3) |

- **`for await` 는 `async` 함수 안(또는 모듈 최상위)에서만** 쓴다 — `await` 와 같은 자리다(39번).
- **떠날 때 `return()` 을 `await` 한다** — 정리 코드가 비동기여도 끝난 뒤에 루프 뒤로 간다.
- **async generator 는 `for...of` 에 못 넣는다** — `@@iterator` 가 없다.

## 어디서 틀리나

### (1) ★★★ 프라미스 배열을 `for await` 로 돌면 「병렬로 기다리는 것」이라 믿는다

**하나씩 기다린다** — 먼저 깨진 뒤의 것은 **처리기 없이** 거부된다(`unhandledRejection(b)` · 훅 없으면 `exit 1`). 동시에 시작한 것들은 **`Promise.all`/`allSettled`** 로 기다린다(동작 (2)).

### (2) ★★★ 루프가 먼저 던지고 떠나면 나머지는 「버려질 뿐」이라 믿는다

**버려진 것이 나중에 거부되면 미처리 거부다**(`array-b-d` 의 `unhandledRejection(d)`).

### (3) ★★★ 동기 제너레이터를 `for await` 로 돌면 거부가 나도 `finally` 가 돈다고 믿는다

**판에 따라 다르다** — node 18·20 은 **안 돌았고**(`return() no · finally no`), Chrome 151 은 돌았다. ES2025 본문의 규칙이다. 정리 코드가 중요하면 **async generator 로 쓰거나 거부를 제너레이터 안에서 잡는다**(동작 (1)).

### (4) ★★ async generator 를 `for...of` 나 스프레드에 넣는다

**`TypeError`** — `@@iterator` 가 없다(`typeof g[Symbol.iterator] undefined`). 문구의 「is not a function」은 **원인이 아니다**(동작 (3)).

### (5) ★★ `yield promise` 는 몸통에 프라미스를 준다고 믿는다

**값을 준다** — async generator 의 `yield` 가 기다린다(`body got string "v"`). `yield await p` 는 **한 틱 더**다(동작 (4)).

### (6) ★★ `break` 하면 정리 코드는 뒤에서 알아서 돈다고 믿는다

**루프가 그 정리를 기다린다** — `finally` 안의 `await` 가 끝나야 루프 뒤의 줄이 돈다(동작 (3)의 `[4]`).

### (7) ★ `next()` 를 겹쳐 부르면 본문이 겹쳐 돈다고 믿는다

**줄을 선다** — 한 번에 한 걸음, 요청한 순서대로 이행한다(동작 (5)).

## 구현 세부사항 대 언어 보장

### 명세 보장(ECMA-262)

- ★★★ **`GetIterator(obj, async)`** — `@@asyncIterator` 먼저, 없으면 `@@iterator` 를 **`CreateAsyncFromSyncIterator` 로 감싼다**, 둘 다 없으면 `TypeError`.
- ★★★ **`AsyncIteratorClose`** — `return` 을 부르고 **그 결과를 `Await`** 한다. `break`·`return`·`throw` 가 이것을 부른다.
- ★★ **`Yield`** 는 async generator 에서 **`AsyncGeneratorYield(? Await(arg))`** — 값을 기다린 뒤 내보낸다.
- ★★ **`AsyncGeneratorYield`** — 요청 큐가 비어 있지 않으면 **멈추지 않고** 다음 요청을 처리한다.
- ★★ **`AsyncFromSyncIteratorContinuation(…, closeOnRejection)`** — 값 프라미스가 거부되면 **동기 이터레이터를 닫는다**(ES2025 본문부터 보인다).

### 호스트

- ★★ **node 의 미처리 거부 보고와 종료 코드**(동작 (2)) — 37번이 정본이다.
- ★ 걸음을 만든 `setTimeout` 0 — 같은 지연의 타이머는 등록 순서(36번).

### 구현(V8) · 이 판의 관찰

- ★★★ **node 18·20(V8 10.2·11.3)은 `closeOnRejection` 을 하지 않았다**, Chrome 151 은 했다 — 이 문서가 본 **유일한 판 차이**다.
- ★ 예외 문구 — `… is not a function or its return value is not iterable` · `… not async iterable`.
- ★ 틱 수(`@2`·`@3`)는 세 판이 같았다.

### 그래서 이렇게 적으면 틀린다

- ✗ 「`for await (const x of promises)` 는 `Promise.all` 과 같다」 → ○ 「**하나씩** 기다린다 — 먼저 깨진 뒤의 것은 처리기가 없다」
- ✗ 「`for await` 는 동기 이터러블도 똑같이 닫는다」 → ○ 「`break`·`return`·`throw` 는 닫는다 — **값이 거부된 경우는 판에 따라 다르다**(node 18·20 은 안 닫았다)」
- ✗ 「async generator 는 이터러블이다」 → ○ 「**비동기** 이터러블이다 — `for...of` 에는 못 넣는다」

## 언제 쓰고 언제 안 쓰나

- **async generator + `for await`** — 페이지 넘김·줄 단위 읽기처럼 **다음 것을 당길 때 만드는** 흐름. 떠날 때의 정리를 `finally` 에 둔다.
- **`for await` + 동기 이터러블** — 이미 있는 값·프라미스를 **차례로** 쓸 때. 단 프라미스가 **이미 다 시작됐으면** `Promise.all`/`allSettled` 쪽이 안전하다(동작 (2)).
- **`Array.fromAsync`** — 비동기 이터러블을 배열로 모을 때(ES2026 — node 18·20 에 없다, 26번).
- ★ **안 쓰는 자리** — 「병렬 요청 배열을 `for await` 로 기다리기」 · async generator 를 `for...of` 에.

## 핵심 문장

1. ★★★ `for await` 는 `@@asyncIterator` 를 먼저 찾고, 없으면 **`@@iterator` 를 감싸서** 쓴다 — 몸통은 늘 **확정된 값**을 받는다.
2. ★★★ `break`·`return`·`throw` 는 동기 `for...of` 와 **똑같이** `return()` 을 부르고 `finally` 를 돌린다 — 그리고 **그 결과를 기다린다.**
3. ★★★ 격자에서 동기판과 갈린 칸은 **`1 / 10`** — 값이 거부된 프라미스일 때뿐이고, 감싼 동기 제너레이터를 닫느냐는 **Chrome 151 만 닫았다**(ES2025 본문의 `closeOnRejection`).
4. ★★★ 미리 만든 프라미스 배열을 `for await` 로 돌면 **먼저 깨진 뒤의 것에 처리기가 없다** — node 는 `exit 1`. async generator 는 **당길 때 만든다.**
5. ★★ async generator 의 `yield` 는 **값을 기다린다** · `next()` 를 겹쳐 부르면 **줄을 선다.**

## 관련 자료

- [ECMA-262 — Abstract Operations(`GetIterator`·`AsyncIteratorClose`)](https://tc39.es/ecma262/multipage/abstract-operations.html) · [Control Abstraction Objects(`Yield`·`AsyncGeneratorYield`·`AsyncFromSyncIteratorContinuation`)](https://tc39.es/ecma262/multipage/control-abstraction-objects.html) · [TC39 finished proposals](https://github.com/tc39/proposals/blob/main/finished-proposals.md)
- [20 — 제너레이터](../20-generators/2-summary.md) — `return()`·`finally` 의 동기판(정본). [19 — 이터러블 프로토콜과 `for...of`](../19-iterable-protocol-and-for-of/2-summary.md) — 소비자별 `return()` 호출표(정본).
- [39 — `async`/`await`](../39-async-await/2-summary.md) — 틱 · 먼저 부르고 차례로 기다리는 함정. [37](../37-promise-state-model/2-summary.md) · [36](../36-event-loop-and-microtasks/2-summary.md) · [38](../38-promise-combinators/2-summary.md).
- [26 — 배열 탐색·평탄화·생성](../26-array-search-flatten-and-create/2-summary.md) — `Array.fromAsync`.
- [41 — 취소와 타임아웃](../41-cancellation-and-timeouts/2-summary.md) — 루프를 신호로 끊기. [42 — ESM 모듈](../42-esm-modules/2-summary.md) — 모듈 최상위의 `for await`.

## 용어 풀이

- **비동기 이터러블** — `Symbol.asyncIterator` 메서드가 있는 객체. 그 메서드가 비동기 이터레이터를 돌려준다.
- **비동기 이터레이터** — `next()` 가 **`{ value, done }` 을 이행하는 프라미스**를 돌려주는 객체.
- **async generator** — `async function*`. `await` 와 `yield` 를 한 함수에서 쓴다.
- **`CreateAsyncFromSyncIterator`** — 동기 이터레이터를 비동기 이터레이터처럼 쓰게 감싸는 명세 연산. 값마다 `Await` 한다.
- **`AsyncIteratorClose`** — 루프를 일찍 떠날 때 `return()` 을 부르고 그 결과를 기다리는 명세 연산.
- **`closeOnRejection`** — 감싼 동기 이터레이터가 낸 **값 프라미스가 거부되면 그 이터레이터를 닫는다**는 명세 플래그(ES2025 본문부터).
- **요청 큐(`AsyncGeneratorQueue`)** — 끝나지 않은 `next()`·`return()`·`throw()` 호출이 서는 줄.
- **미처리 거부** — 거부된 순간 처리기가 없는 프라미스. node 는 보고하고 기본값으로 `exit 1`(37번).

## 더 들어가면

- **`yield*` 의 비동기판** — async generator 안의 `yield*` 가 동기 이터러블을 받는 자리. **이 문서는 재지 않았다** — 동작 (1)의 C 행과 같은 감싸개가 끼는지는 다음 판에서 격자에 한 행으로 더할 자리다.
- **`return()` 을 이미 도는 중에 또 부르면**(요청 큐 안의 `return`) — 재지 않았다.
- **호스트의 비동기 이터러블**(node 스트림 등) — 이 문서는 언어 쪽만 봤다.
