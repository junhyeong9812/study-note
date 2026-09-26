# js/syntax/47 — `WeakRef`·`FinalizationRegistry`: 「명세가 약속하는 것은 『살아 있는 동안은 돌려준다』 쪽뿐이다 — 『언젠가 비워진다』·『콜백이 불린다』는 이 판에서 `gc()` 를 불렀을 때의 관찰이다」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> ★★★ **이 주제의 본체는 층 가르기다** — 같은 칸의 숫자라도 **명세가 보장한 것 / V8 이 그렇게 한 것 / 이 판에서 `gc()` 를 불렀을 때 본 것**이 섞여 있다. 문서의 모든 결론 줄에 **어느 층인지**를 붙인다(아래 「층」 표).
> ★★★ 그 층을 가르는 도구가 **② 관찰 격자**다 — (`gc()` 있음/없음) × (`gc()` 부름/안 부름) × (기다림 넷: 없음 · `await null` 한 번 · 열 번 · `setTimeout` 한 번) 칸마다 **20판 중 몇 판**에서 `deref()` 가 `undefined` 였고 콜백이 불렸나를 센다(동작 (1)). 판 격자는 **node 20 · node 18 · Chrome 151**(`--js-flags=--expose-gc` 유무)이다. ★ **「모든 판에서」 라는 전칭 칸은 두지 않는다** — 칸은 「20판 중 N」, 요약 줄은 「**한 판이라도**」 로 센다(규칙 24).
> ★★ 보조로 **① 로그 심기**(`deref()` 가 대상을 **다시 붙잡는** 것 — 동작 (2)) · **④ 예외의 이름 + 문구**(`unregister(1)` — 동작 (4)) · **교차 갈래 한 쌍**(CPython 은 `del` 직후 — 동작 (5))을 쓴다.
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262 — Processing Model of WeakRef and FinalizationRegistry Targets](https://tc39.es/ecma262/multipage/executable-code-and-execution-contexts.html) — Objectives 첫 문장 「**This specification does not make any guarantees that any object or symbol will be garbage collected. Objects or symbols which are not live may be released after long periods of time, or never at all.**」 · 「`deref` 가 돌려준 대상은 **이어지는 동기 접근도 같은 값**을 받도록 살려 둔다 — 그 목록은 동기 작업이 끝나면 **`ClearKeptObjects`** 로 비운다」 · 「정리 콜백은 **may eventually be made, after synchronous ECMAScript execution completes**」 · 「**`ClearKeptObjects`·`CleanupFinalizationRegistry` 는 동기 실행을 끊지 못한다** … 그 일정은 **호스트**에 맡긴다」 · Execution 절 — 「살아 있지 않으면 구현은 **may** 비울 수 있다 … 정리 잡을 넣을지는 **implementation-defined choice**」 · `ClearKeptObjects` 는 「**when a synchronous sequence of ECMAScript executions completes**」 에 부르게 되어 있다(`[[KeptAlive]]` 를 빈 목록으로) · `AddToKeptObjects`
> - [ECMA-262 — Managing Memory](https://tc39.es/ecma262/multipage/managing-memory.html) — `WeakRef.prototype.deref` 의 note 「첫 `deref` 가 `undefined` 가 아니었으면 **둘째도 그럴 수 없다**」 · `FinalizationRegistry.prototype.unregister` — **`CanBeHeldWeakly(unregisterToken)` 이 거짓이면 `TypeError`** · 지운 칸이 있으면 `true`
> - [HTML — Perform a microtask checkpoint](https://html.spec.whatwg.org/multipage/webappapis.html) — 체크포인트의 끝에서 **「Perform ClearKeptObjects()」** · `HostEnqueueFinalizationRegistryCleanupJob` 절 「**The timing and occurrence of cleanup work is implementation-defined** … Authors would be best off **not depending on the timing details** of garbage collection implementations」
> - ★ 명세의 이름은 **`AddToKeptObjects`/`ClearKeptObjects`/`[[KeptAlive]]`** 다. 제안 시절의 이름(`KeepDuringJob`)은 **지금 명세 텍스트에 없다** — 이 문서는 지금 이름을 쓴다.
>
> **실행 검증** — 이 문서의 모든 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다.
> 배너의 `node20` 은 v20.19.6, `node18` 은 v18.19.1, 파이썬은 `python3`(3.12.3). 하네스 소스는 [44번](../44-dynamic-import-top-level-await-and-import-attributes/2-summary.md) 머리말에 있다 — ★ **이 주제를 위해 `--gc` 선택지를 더했다**(`--js-flags=--expose-gc`). ★ Chrome 은 `--virtual-time-budget` 로 시간을 당겨 돌리므로 `setTimeout` 이 **실제 시간을 안 쓴다.**
> ★★★ **`gc()` 는 ECMA-262 에 없다** — V8 플래그 `--expose-gc` 가 여는 전역 함수다(판별 블록 — 플래그 없이는 `undefined`). **「`gc()` 를 부르면 비워진다」 는 이 판의 관찰**이다.
> ★★★ **성능·메모리 양은 재지 않았다.**
>
> **버전** — `WeakRef`·`FinalizationRegistry` 는 **ES2021** · 세 판 다 있다(판별 블록). `cleanupSome` 은 **표준에 없고 세 판 다 없다.**
>
> **★★★ 층 — 이 문서의 결론이 기대는 세 층**
>
> | 층 | 무엇 | 어디서 |
> |---|---|---|
> | ★★★ **명세 보장** | 강하게 붙잡힌 것은 안 비워진다 · **`deref()` 가 대상을 돌려주면 그 동기 실행이 끝날 때까지 계속 돌려준다**(`[[KeptAlive]]`) · 콜백은 **동기 실행을 끊고 들어오지 않는다** · `unregister` 의 반환값과 `TypeError` | 동작 (1)의 `no wait` 행 · 동작 (2)의 `[1]`·`[4]` · 동작 (4) |
> | ★★ **호스트** | `ClearKeptObjects` 를 **언제** 부르나(HTML 은 **마이크로태스크 체크포인트의 끝**) · 정리 잡을 **언제** 넣나 | 동작 (1)의 `await` 행 · 동작 (2)의 `[2]` |
> | ★★★ **이 판의 관찰(V8 + `--expose-gc`)** | `gc()` 한 번에 **비워졌다**(20/20) · 콜백이 그 뒤 **불렸다**(20/20) · 할당 압력만으로는 `deref()` 가 **한 판도** `undefined` 가 안 됐고 콜백은 **판마다 달랐다** | 동작 (1)의 `setTimeout` 행 · 동작 (3) |
>
> **★★★ 이 주제가 쓰는 창 — 그리고 부적용인 창**
>
> | 창 | 이 주제에서 무엇을 보나 |
> |---|---|
> | ★★★ **② 관찰 격자**(본체의 도구) | 8칸 × 20판 × 판 넷 — 「`deref() undefined N/20`」 · 「`callback ran N/20`」 · 「**한 판이라도** 본 칸 N / M」(동작 (1)) |
> | ★★ **① 로그 심기** | 한 판 안에서 다섯 지점의 `deref()` — `deref()` 자신이 대상을 **다시 붙잡는다**(동작 (2)) |
> | ★★ **흔들리는 칸을 따로 센다** | 할당 압력 — 20판 × 다섯 벌 · 벌마다 다른 수(동작 (3)) |
> | ★★ **교차 갈래 한 쌍** | CPython — `del` 다음 줄 전에 콜백 · 순환은 `gc.collect()` 뒤(동작 (5)) |
> | ★ **④ 예외 문구** | `unregister(1)` — 판마다 문구가 달랐다(동작 (4)) |
> | ★★★ **「못 잰 것」 이 아니라 「창을 바꿔 물었다」**(제5의 상태) | Chrome 에서 `gc()` 없이 「언제 비워지나」 는 **잴 수 없다**(비울 방아쇠가 없다). 그래서 **`--js-flags=--expose-gc` 로 같은 질문을 다시 물었다**(동작 (1)) — ★ 바꾼 창이 못 보는 것: 그 `gc()` 는 **평소에는 없는 방아쇠**라, 실제 페이지에서 **언제** 비워지는지는 여전히 말하지 않는다 |
> | ★ **부적용 — 양** | 얼마나 붙드나(바이트)는 이 API 가 말하지 않는다 — 06번의 「못 잰 것」과 같다 |
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ★★★ **동작 (3) 할당 압력 블록의 `run N` 다섯 줄과 마지막 줄의 수**(node 20 은 콜백이 한 판이라도 온 벌이 다섯 중 `0\~1`, Chrome 은 칸마다 `3\~10 / 20` — 재실행마다 바뀌었다). 재대조는 이 줄들을 정규화한다 | ★★★ 동작 (1)의 **모든 칸**(`0/20` · `20/20`)과 요약 줄 · 동작 (2)의 다섯 줄 · 동작 (4) · 동작 (5) — **재대조 동일** |
> | 판별 블록의 판 문자열 · `unregister(1)` 의 **문구**(node 18 과 20 이 달랐다 — 판의 차이) | ★★ 단 동작 (1)의 `20/20` 은 **안 흔들렸을 뿐 보장이 아니다**(층 표의 셋째 줄) |
>
> **선행** — [23 — `Map`·`Set` 과 약한 컬렉션](../23-map-set-and-weak-collections/2-summary.md)(직접 선행 — ★★★ **이미 쟀다**: 수명 조건 6개 × 20판(`Map` 의 키 `0/20` · `WeakMap` 의 키 `20/20` · 에피머론 · `unregister` 한 뒤 콜백 `0/20`) · **같은 잡 안에서 `gc()` 직후 `deref()` 는 6행 전부 `20/20`** · 콜백은 `gc()` 뒤 **첫 매크로태스크** · `gc()` 없이는 **20틱 안에 안 옴** · 약한 쪽에 넣을 수 있는 값(`CanBeHeldWeakly`) — 거기 동작 (4)\~(6). 그 편 머리말은 브라우저의 GC 를 **안 돌렸다**고 적었다(그 페이지 하네스가 `setTimeout` 뒤의 출력을 못 받아서) → 이 묶음의 하네스는 받는다. ★ 이 문서는 23번을 **다시 재지 않고** 「기다림의 종류」 축 · Chrome · 할당 압력 · `deref()` 가 다시 붙잡는 것 · 파이썬 대비만 더한다) ·
> [06 — 스코프와 클로저](../06-scope-and-closures/2-summary.md)(★★ `WeakRef` + `--expose-gc` 를 **도구로** 썼다 — 거기 동작 (6) · 「형제 함수가 읽으면 살아 남는다」는 **V8 의 구현**이라고 적었다) ·
> [22 — `Symbol`](../22-symbol-and-well-known-symbols/2-summary.md)(심볼을 약한 대상으로 — ES2023) · [36 — 이벤트 루프](../36-event-loop-and-microtasks/2-summary.md)(마이크로태스크 대 매크로태스크).
>
> ★★★ **경계 — README 가 적은 정본 `cs/foundations/memory-management/`** — 그 폴더는 [`README.md`](../../../../memory-management/README.md) **한 파일**이고, 절은 메모리 계층 · 스택 프레임 · 가상 메모리 · 페이징 · TLB · 힙 구조 · 엔디언이다. ★★ **GC 알고리즘(추적·참조 계수·세대) 절은 없다** — GC 는 「2. 캐시와 지역성」의 한 줄(「가비지 컬렉터: 객체 위치가 수시로 바뀐다」) · 「11. 페이지 폴트와 다이나믹 힙」의 Young/Old 세대 그림 한 개(「가비지 컬렉터가 객체 수명에 따라 자동 분리」) · 「14」의 「단점: GC 오버헤드」 로만 나온다. GC **전략**의 논증은 [Java 언어 특성](../../../java/언어-특성/README.md)(세대 가설 · G1 · ZGC)이 더 가깝다. **이 문서는 어느 쪽도 다시 쓰지 않는다** — 여기는 **「약한 참조로 프로그램이 무엇을 볼 수 있나」의 계약**만이다.
>
> ★★ **교차 갈래** — [Python 01 — 객체와 이름 바인딩](../../../python/syntax/01-object-and-name-binding/2-summary.md)(「7. `del` 은 객체가 아니라 이름을 지운다」 · 「8. 참조를 세는 두 도구」 — CPython 의 **참조 계수**) · [C++ 27 — `shared_ptr` 와 참조 계수](../../../cpp/syntax/27-shared-ptr-and-reference-counting/2-summary.md) · [C++ 28 — `weak_ptr` 와 순환 참조](../../../cpp/syntax/28-weak-ptr-and-reference-cycles/2-summary.md)(`lock()` 은 **해지 직후** `nullptr` — 결정적). ★ Java 의 `WeakReference`·`Cleaner` 와 C# 의 `WeakReference<T>` 는 **각 갈래 목록에 주제가 없다**(Java 목록은 「JVM 내부(GC…)는 이 목록에서 다루지 않는다」 · C# 은 결정적 해제를 C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **37번**(`IDisposable`)으로 둔다) — 이 문서는 그 둘을 **돌리지 않았다.**

```text
===== ./js44b-versions.sh (exit=0) =====
node 18.19.1  v8 10.2.154.26-node.28
  ES2015  Proxy / Reflect                           yes
  ES2015  Proxy.revocable                           yes
  ES2020  import() in a classic script              yes
  ES2025  import() with a second argument           yes
  ES2021  WeakRef / FinalizationRegistry            yes
          FinalizationRegistry cleanupSome          no
  host    require (this script's scope)             yes
node 20.19.6  v8 11.3.244.8-node.33
  ES2015  Proxy / Reflect                           yes
  ES2015  Proxy.revocable                           yes
  ES2020  import() in a classic script              yes
  ES2025  import() with a second argument           yes
  ES2021  WeakRef / FinalizationRegistry            yes
          FinalizationRegistry cleanupSome          no
  host    require (this script's scope)             yes
Google Chrome 151.0.7922.173
  ES2015  Proxy / Reflect                           yes
  ES2015  Proxy.revocable                           yes
  ES2020  import() in a classic script              yes
  ES2025  import() with a second argument           yes
  ES2021  WeakRef / FinalizationRegistry            yes
          FinalizationRegistry cleanupSome          no
  host    require (this script's scope)             no
gc():
  node20                        typeof gc: undefined
  node20 --expose-gc            typeof gc: function
  Chrome                        typeof gc: undefined
  Chrome --js-flags=--expose-gc typeof gc: function
```

## 한눈에 — 쉽게 말하면

**`WeakRef` 는 「주소만 적어 둔 쪽지」다. 쪽지가 집을 지켜 주지는 않는다 — 아무도 안 사는 집은 철거반(GC)이 언젠가 헐 수 있고, 헐리면 쪽지를 들고 가도 빈터(`undefined`)다. `FinalizationRegistry` 는 「철거되면 알려 달라」는 신청서인데, 철거반은 알려 줄 의무가 없다. 딱 하나 약속된 것 — 쪽지로 집을 한 번 찾아갔으면(`deref()`), 그날 일과(동기 실행)가 끝날 때까지는 그 집을 헐지 않는다.**

- ★★★ **명세는 「비워진다」를 약속하지 않는다** — "or never at all". `gc()` 없이는 이 판에서 **한 칸도** 비워지지 않았다(동작 (1)).
- ★★★ **명세가 약속하는 쪽** — `deref()` 가 돌려준 대상은 **그 동기 실행이 끝날 때까지** 계속 돌려준다. `gc()` 를 불러도 같은 턴 안에서는 **20/20 객체**(동작 (1)·(2)).
- ★★ **「같은 턴」 의 끝은 호스트가 정한다** — `await null` 을 **열 번** 넘겨도 아직 같은 체크포인트라 **20/20 객체**였고, **`setTimeout` 을 한 번 넘기자** `gc()` 뒤 **20/20 `undefined`** 였다(동작 (1)).
- ★★ **CPython 은 반대로 결정적이다** — `del` 한 줄에 콜백이 **다음 줄보다 먼저** 돈다(참조 계수). 순환만 `gc.collect()` 를 기다린다(동작 (5)).

```text
   한 판 (target 은 WeakRef 말고는 아무도 안 붙든다)

   동기 실행 ─────────┬─ 마이크로태스크들 ─────────┬─ (체크포인트 끝: ClearKeptObjects) ─┬─ 다음 매크로태스크 ─
   new WeakRef(t)     │  await null  × 1 · × 10    │                                   │  setTimeout 0 뒤
   [[KeptAlive]] += t │                            │  [[KeptAlive]] = []               │
   gc() → deref()     │  gc() → deref()            │                                   │  gc() → deref()
     object 20/20     │    object 20/20            │                                   │    undefined 20/20   ← 이 판의 관찰
   ── 명세 보장 ───────┴── 호스트가 끝을 정한다 ─────┴───────────────────────────────────┴────────────────────
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 주소만 적은 쪽지 | `new WeakRef(t)` — 대상을 **살리지 않는다** | 동작 (1) |
| 쪽지로 찾아가기 | `ref.deref()` — 대상 또는 `undefined` | 동작 (1)·(2) |
| 그날 일과 동안은 안 헌다 | `AddToKeptObjects` → `[[KeptAlive]]` · 동기 실행이 끝나면 `ClearKeptObjects` | 동작 (2)의 `[1]`·`[4]` |
| 「그날」 이 언제 끝나나 | HTML — **마이크로태스크 체크포인트의 끝** | 동작 (1)의 `await` 행 대 `setTimeout` 행 |
| 철거반 | GC — 언제 오는지 명세 밖 | 동작 (1)의 `nothing` 행 · 동작 (3) |
| 철거반을 부르는 호루라기 | `gc()` — **V8 플래그**가 여는 것 | 판별 블록 |
| 알려 달라는 신청서 | `FinalizationRegistry.register` — 콜백은 **may** | 동작 (1)의 `callback` 열 |
| 신청 취소 | `unregister(token)` — 지운 칸이 있으면 `true` | 동작 (4) · 23번 |

**똑같은 구조다** — 실무에서 물리는 자리도 굳어 있다.
「**캐시를 `WeakRef` 로 두고 `deref()` 가 곧 `undefined` 가 되리라 기대했는데 개발 중에는 절대 안 비워진다**」,
「**`FinalizationRegistry` 로 파일·소켓을 닫았더니 테스트에서는 되고 운영에서는 안 닫힌다**」,
「**`deref()` 결과를 확인한 뒤 `await` 를 몇 번 지나 다시 `deref()` 했는데 멀쩡했다 — 그래서 안전하다고 믿었다**」가 그것이다(동작 (1)·(3)).

> **`WeakRef`** — 대상을 붙들지 않고 가리키는 참조(ES2021). `deref()` 로 대상을 얻고, 비워졌으면 `undefined`.\
> 예: `const r = new WeakRef(obj); r.deref()?.method();`

## 이 주제가 답하려는 질문

1. **약한 참조로 프로그램이 볼 수 있는 것은 무엇이고, 그중 명세가 보장하는 것은 어느 쪽인가** — `gc()` 가 있을 때와 없을 때, 기다림의 종류마다?
2. **「같은 동기 실행 안에서는 살아 있다」 의 「같은」 은 어디까지인가** — `await` 는? `setTimeout` 은? `deref()` 를 한 번 더 부르면?
3. **`gc()` 를 안 부르면 무엇을 기대할 수 있나** — 할당 압력만 줄 때 · 다른 언어(CPython)와 견주면?

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 출력으로 읽는다.

### (1) ★★★ 관찰 격자 — `gc()` 유무 × 부름 × 기다림 넷 × 20판 × 판 넷

**언제 쓰나** — 「이 캐시 항목은 언제 비워지나」·「이 정리 콜백에 기대도 되나」를 판단할 때.
★★ 판마다 **새 대상**을 즉시 실행 함수 안에서 만들고, `WeakRef` 와 레지스트리 말고는 **아무도 안 붙든다.** 기다림 → (`gc()`) → `deref()` 순서이고, 콜백은 그 뒤 `setTimeout` **열 번**까지 기다린다.

```js
// js44b-47a-observe-grid.js
// What a WeakRef and a FinalizationRegistry let a program see. One cell = ROUNDS rounds; each round makes a new target
// that nothing else holds, registers it, and keeps only a WeakRef to it. Then it
//   waits:      not at all | await null once | await null ten times | one setTimeout(0)
//   does:       nothing | calls gc()
//   reads:      ref.deref() -- is it undefined?
//   and last waits up to ten more setTimeout(0) turns for the cleanup callback.
// A cell prints in how many of the ROUNDS rounds deref() was undefined, and in how many the callback ran.
// The "gc()" rows need a global gc(); without one they print n/a.
const ROUNDS = 20;
const turn = () => new Promise((r) => setTimeout(r, 0));
const waits = {
  "no wait": null,
  "await null x1": async () => { await null; },
  "await null x10": async () => { for (let i = 0; i < 10; i++) await null; },
  "setTimeout 0": turn,
};
const actions = {
  "nothing": () => {},
  "gc()": () => gc(),
};
async function round(wait, action) {
  let called = false;
  const reg = new FinalizationRegistry(() => { called = true; });
  let ref;
  (() => { const target = {}; ref = new WeakRef(target); reg.register(target, "held"); })();
  if (waits[wait]) await waits[wait]();
  actions[action]();
  const gone = ref.deref() === undefined;
  for (let i = 0; i < 10 && !called; i++) await turn();
  return { gone, called };
}
(async () => {
  const hasGc = typeof gc === "function";
  console.log("typeof gc: " + typeof gc + " · " + ROUNDS + " rounds per cell");
  console.log("  " + "does".padEnd(10) + "waits".padEnd(16) + "deref() undefined".padEnd(20) + "callback ran");
  let seen = 0, cells = 0;
  for (const action of Object.keys(actions)) {
    for (const wait of Object.keys(waits)) {
      if (action === "gc()" && !hasGc) { console.log("  " + action.padEnd(10) + wait.padEnd(16) + "n/a"); continue; }
      let gone = 0, called = 0;
      for (let r = 0; r < ROUNDS; r++) { const o = await round(wait, action); gone += o.gone; called += o.called; }
      cells++;
      if (gone > 0 || called > 0) seen++;
      console.log("  " + action.padEnd(10) + wait.padEnd(16) + (gone + "/" + ROUNDS).padEnd(20) + called + "/" + ROUNDS);
    }
  }
  console.log("cells where at least one round saw deref() undefined or the callback: " + seen + " / " + cells);
})();
```

```sh
# js44b-47a-observe.sh
#!/usr/bin/env bash
# The observation grid (js44b-47a-observe-grid.js) with and without a global gc():
# node20, node20 --expose-gc, Chrome 151 with --js-flags=--expose-gc in full,
# then node18 --expose-gc and Chrome 151 without the flag compared with the run that has the same gc() situation.
set -u -o pipefail
cd "$(dirname "$0")"
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
a="$("$N20" js44b-47a-observe-grid.js)" || exit 1
b="$("$N20" --expose-gc js44b-47a-observe-grid.js)" || exit 1
c="$(./js44b-browser.sh --gc js44b-47a-observe-grid.js)" || exit 1
d="$("$N18" --expose-gc js44b-47a-observe-grid.js)" || exit 1
e="$(./js44b-browser.sh js44b-47a-observe-grid.js)" || exit 1
echo "--- node20"; printf '%s\n' "$a"
echo "--- node20 --expose-gc"; printf '%s\n' "$b"
echo "--- Chrome 151 --js-flags=--expose-gc"; printf '%s\n' "$c"
echo ""
[ "$d" = "$b" ] && s=yes || s=no
echo "node18 --expose-gc prints the same as node20 --expose-gc: $s"
[ "$e" = "$a" ] && s=yes || s=no
echo "Chrome 151 without the flag prints the same as node20 without it: $s"
```

```text
===== ./js44b-47a-observe.sh (exit=0) =====
--- node20
typeof gc: undefined · 20 rounds per cell
  does      waits           deref() undefined   callback ran
  nothing   no wait         0/20                0/20
  nothing   await null x1   0/20                0/20
  nothing   await null x10  0/20                0/20
  nothing   setTimeout 0    0/20                0/20
  gc()      no wait         n/a
  gc()      await null x1   n/a
  gc()      await null x10  n/a
  gc()      setTimeout 0    n/a
cells where at least one round saw deref() undefined or the callback: 0 / 4
--- node20 --expose-gc
typeof gc: function · 20 rounds per cell
  does      waits           deref() undefined   callback ran
  nothing   no wait         0/20                0/20
  nothing   await null x1   0/20                0/20
  nothing   await null x10  0/20                0/20
  nothing   setTimeout 0    0/20                0/20
  gc()      no wait         0/20                0/20
  gc()      await null x1   0/20                0/20
  gc()      await null x10  0/20                0/20
  gc()      setTimeout 0    20/20               20/20
cells where at least one round saw deref() undefined or the callback: 1 / 8
--- Chrome 151 --js-flags=--expose-gc
typeof gc: function · 20 rounds per cell
  does      waits           deref() undefined   callback ran
  nothing   no wait         0/20                0/20
  nothing   await null x1   0/20                0/20
  nothing   await null x10  0/20                0/20
  nothing   setTimeout 0    0/20                0/20
  gc()      no wait         0/20                0/20
  gc()      await null x1   0/20                0/20
  gc()      await null x10  0/20                0/20
  gc()      setTimeout 0    20/20               20/20
cells where at least one round saw deref() undefined or the callback: 1 / 8

node18 --expose-gc prints the same as node20 --expose-gc: yes
Chrome 151 without the flag prints the same as node20 without it: yes
```

```text
                         gc() 없음 (node20 · Chrome)      gc() 있음 (node20 · node18 · Chrome --js-flags)
                         deref undefined / callback      deref undefined / callback
   nothing · 네 기다림     0/20 · 0/20  (4칸)              0/20 · 0/20  (4칸)
   gc()    · no wait     n/a                             0/20 · 0/20      ← 명세 보장 (KeptAlive)
   gc()    · await ×1    n/a                             0/20 · 0/20      ← 호스트: 아직 같은 체크포인트
   gc()    · await ×10   n/a                             0/20 · 0/20      ← 〃
   gc()    · setTimeout  n/a                             20/20 · 20/20    ← 이 판의 관찰
                         ─────────────────────           ─────────────────────
   한 판이라도 본 칸        0 / 4                           1 / 8
```

- ★★★ **`gc()` 가 없으면 — `cells where at least one round saw …: 0 / 4`**(node 20 · Chrome 151 둘 다, 한 글자도 같음). 20판 × 4칸 × 콜백 대기 열 틱 동안 **한 번도** 비워지지 않았다. ★ 이것을 「안 비워진다」로 적으면 틀린다 — **이 짧은 시간에 GC 가 안 돈 것**이다(23번 동작 (6)의 `-1` 과 같은 성격 · 명세 "or never at all").
- ★★★ **`gc()` 가 있고 같은 턴 — `no wait` 행 `0/20 · 0/20`.** 방금 `new WeakRef(t)` 가 `t` 를 `[[KeptAlive]]` 에 넣었으니 `gc()` 도 못 거둔다 — **명세 보장**(23번의 「같은 잡 안 6행 `20/20`」 을 이 격자가 다시 확인한 것). 콜백도 `0/20` — 안 거둬졌으니 부를 것이 없고, 그 뒤 열 틱 동안 `gc()` 가 다시 안 불렸다.
- ★★★ **`await null` 한 번 · 열 번도 `0/20`.** 마이크로태스크를 **열 번** 넘겨도 `[[KeptAlive]]` 가 안 비었다 — HTML 이 `ClearKeptObjects` 를 **마이크로태스크 체크포인트의 끝**에 두기 때문이고, node 도 같았다. ★★ **「동기 실행」 은 명세의 말이고, 그 끝을 어디로 볼지는 호스트가 정한다** — 이 두 호스트는 「**체크포인트가 빌 때까지**」였다.
- ★★★ **`setTimeout` 한 번 뒤 — `20/20 · 20/20`**(node 20 · node 18 · Chrome 151 셋 다). 체크포인트가 끝나 목록이 비었고, 그다음 `gc()` 가 거뒀고, 콜백이 열 틱 안에 불렸다. ★★★ **이 줄은 이 판의 관찰이다** — 명세는 `gc()` 도, 「한 번에 거둔다」 도, 「콜백을 부른다」 도 약속하지 않는다. **안 흔들렸을 뿐**이다.
- ★★ **판 넷이 같았다** — `node18 --expose-gc prints the same as node20 --expose-gc: yes` · `Chrome 151 without the flag prints the same as node20 without it: yes`. 23번이 못 돌린 브라우저 쪽이 **같은 모양**이었다.

### (2) ★★ `deref()` 는 대상을 다시 붙잡는다 — 한 판의 다섯 지점

**언제 쓰나** — 「한 번 `deref()` 로 확인했으니 그 턴에서는 믿어도 되나」 를 판단할 때.

```js
// js44b-47c-kept-alive.js
// Needs a global gc(). One round: make a target that only a WeakRef points to, then read deref() at five points.
// Prints, for each point, in how many of ROUNDS rounds deref() gave the object back.
const ROUNDS = 20;
const turn = () => new Promise((r) => setTimeout(r, 0));
const points = ["[1] same job: gc(), then deref()",
  "[2] after await null: gc(), then deref()",
  "[3] next setTimeout turn: deref() before any gc()",
  "[4]   same turn, after that deref(): gc(), then deref()",
  "[5] one more setTimeout turn: gc(), then deref()"];
async function round() {
  let ref;
  (() => { ref = new WeakRef({}); })();
  const got = [];
  const read = () => got.push(ref.deref() !== undefined);
  gc(); read();
  await null; gc(); read();
  await turn(); read();
  gc(); read();
  await turn(); gc(); read();
  return got;
}
(async () => {
  console.log("typeof gc: " + typeof gc + " · " + ROUNDS + " rounds");
  const count = points.map(() => 0);
  for (let r = 0; r < ROUNDS; r++) (await round()).forEach((alive, i) => { count[i] += alive; });
  points.forEach((p, i) => console.log("  " + p.padEnd(56) + "object " + count[i] + "/" + ROUNDS));
})();
```

```text
===== node20 --expose-gc js44b-47c-kept-alive.js (exit=0) =====
typeof gc: function · 20 rounds
  [1] same job: gc(), then deref()                        object 20/20
  [2] after await null: gc(), then deref()                object 20/20
  [3] next setTimeout turn: deref() before any gc()       object 20/20
  [4]   same turn, after that deref(): gc(), then deref() object 20/20
  [5] one more setTimeout turn: gc(), then deref()        object 0/20
```

Chrome 151 — `--js-flags=--expose-gc` 로.

```text
===== ./js44b-browser.sh --gc js44b-47c-kept-alive.js (exit=0) =====
typeof gc: function · 20 rounds
  [1] same job: gc(), then deref()                        object 20/20
  [2] after await null: gc(), then deref()                object 20/20
  [3] next setTimeout turn: deref() before any gc()       object 20/20
  [4]   same turn, after that deref(): gc(), then deref() object 20/20
  [5] one more setTimeout turn: gc(), then deref()        object 0/20
```

```text
   [1] 같은 동기 실행       new WeakRef → KeptAlive 에 t     gc()  deref() → object     ← 명세
   [2] await null 뒤        (같은 체크포인트)                  gc()  deref() → object     ← 호스트(체크포인트 끝에 비운다)
       ─── 체크포인트 끝: ClearKeptObjects ───
   [3] 다음 setTimeout 턴   deref() 먼저 → object · 그리고 KeptAlive 에 다시 t          ← 명세(AddToKeptObjects)
   [4]   같은 턴            gc()  deref() → object                                      ← 명세 — [3] 의 deref 가 붙잡았다
       ─── 체크포인트 끝 ───
   [5] 또 다음 턴           gc()  deref() → undefined                                   ← 이 판의 관찰
```

- ★★★ **`[3]`·`[4]` 가 교재다 — 새 턴에서 `gc()` **전에** `deref()` 를 한 번 부르면, 그 뒤의 `gc()` 도 못 거둔다(`object 20/20`).** `deref()` 자신이 `AddToKeptObjects` 로 대상을 **다시 목록에 넣는다** — 명세 note 「첫 `deref` 가 `undefined` 가 아니었으면 둘째도 그럴 수 없다」 가 그 보증이다.
- ★★★ **`[5]` 에서야 `object 0/20`** — 목록이 빈 턴에서 `gc()` 를 부르면 이 판은 거뒀다(관찰).
- ★★ node 20 · node 18 · Chrome 151 이 한 글자도 같았다.
- ★ **「`deref()` 로 확인했으니 이 턴 안에서는 안전하다」 는 맞다**(명세). **「다음 턴에도」 는 틀릴 수 있다** — 다음 턴의 첫 `deref()` 가 다시 확인해야 한다.

### (3) ★★ `gc()` 없이 할당 압력만 — 흔들리는 칸을 다섯 벌 센다

**언제 쓰나** — 「실제 프로그램처럼 메모리를 쓰면 언젠가 비워지겠지」 를 확인하고 싶을 때.
★★★ **이 블록은 흔들리는 칸으로 선언한다**(머리말 표). 한 판이 약 20만 개의 짧게 사는 객체를 만든다. 칸은 「`deref()` undefined / 콜백」 의 20판 중 수이고, 같은 격자를 **다섯 벌** 돌린다.

```js
// js44b-47b-pressure-grid.js
// js44b-47a-observe-grid.js with gc() replaced by allocation "pressure": the round allocates about 200 000
// short-lived objects, so a collection may start on its own. The whole grid (four waits x ROUNDS rounds) runs RUNS times;
// one line per run: for each wait, "deref() undefined N · callback ran M" out of ROUNDS rounds.
const ROUNDS = 20, RUNS = 5;
const turn = () => new Promise((r) => setTimeout(r, 0));
const waits = {
  "no wait": null,
  "await null x1": async () => { await null; },
  "await null x10": async () => { for (let i = 0; i < 10; i++) await null; },
  "setTimeout 0": turn,
};
const pressure = () => { let junk = []; for (let i = 0; i < 200000; i++) junk.push({ i }); junk = null; };
async function round(wait) {
  let called = false;
  const reg = new FinalizationRegistry(() => { called = true; });
  let ref;
  (() => { const target = {}; ref = new WeakRef(target); reg.register(target, "held"); })();
  if (waits[wait]) await waits[wait]();
  pressure();
  const gone = ref.deref() === undefined;
  for (let i = 0; i < 10 && !called; i++) await turn();
  return { gone, called };
}
(async () => {
  console.log("typeof gc: " + typeof gc + " · " + ROUNDS + " rounds per cell · each cell is: deref() undefined / callback ran");
  console.log("       " + Object.keys(waits).map((w) => w.padEnd(17)).join("").trimEnd());
  let anyGone = 0, anyCalled = 0;
  for (let run = 1; run <= RUNS; run++) {
    const cells = [];
    let g = false, c = false;
    for (const wait of Object.keys(waits)) {
      let gone = 0, called = 0;
      for (let r = 0; r < ROUNDS; r++) { const o = await round(wait); gone += o.gone; called += o.called; }
      if (gone) g = true;
      if (called) c = true;
      cells.push((gone + " / " + called).padEnd(17));
    }
    anyGone += g; anyCalled += c;
    console.log("run " + run + "  " + cells.join("").trimEnd());
  }
  console.log("runs with deref() undefined in at least one round: " + anyGone + " / " + RUNS +
    " · runs with the callback in at least one round: " + anyCalled + " / " + RUNS);
})();
```

```sh
# js44b-47b-pressure.sh
#!/usr/bin/env bash
# The pressure grid (js44b-47b-pressure-grid.js) on node20 and in Chrome 151, both without a global gc().
set -u -o pipefail
cd "$(dirname "$0")"
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
echo "--- node20"; "$N20" js44b-47b-pressure-grid.js || exit 1
echo "--- Chrome 151"; ./js44b-browser.sh js44b-47b-pressure-grid.js || exit 1
```

```text
===== ./js44b-47b-pressure.sh (exit=0) =====
--- node20
typeof gc: undefined · 20 rounds per cell · each cell is: deref() undefined / callback ran
       no wait          await null x1    await null x10   setTimeout 0
run 1  0 / 1            0 / 0            0 / 0            0 / 0
run 2  0 / 0            0 / 0            0 / 0            0 / 0
run 3  0 / 0            0 / 0            0 / 0            0 / 0
run 4  0 / 0            0 / 0            0 / 0            0 / 0
run 5  0 / 0            0 / 0            0 / 0            0 / 0
runs with deref() undefined in at least one round: 0 / 5 · runs with the callback in at least one round: 1 / 5
--- Chrome 151
typeof gc: undefined · 20 rounds per cell · each cell is: deref() undefined / callback ran
       no wait          await null x1    await null x10   setTimeout 0
run 1  0 / 4            0 / 10           0 / 10           0 / 10
run 2  0 / 10           0 / 10           0 / 10           0 / 10
run 3  0 / 10           0 / 10           0 / 10           0 / 10
run 4  0 / 10           0 / 10           0 / 10           0 / 10
run 5  0 / 10           0 / 10           0 / 10           0 / 10
runs with deref() undefined in at least one round: 0 / 5 · runs with the callback in at least one round: 5 / 5
```

- ★★★ **`deref()` 가 `undefined` 인 판은 두 호스트 다섯 벌 전부에서 한 판도 없었다**(`runs with deref() undefined …: 0 / 5`). 할당 압력이 부른 GC 는 **이 대상을 거두지 않았다** — 같은 판 안에서 `deref()` 할 때까지는.
- ★★★ **콜백은 흔들렸다** — node 20 은 다섯 벌 중 **0\~1 벌**에서 한 판이라도 불렸고, Chrome 151 은 **다섯 벌 다** 칸마다 **`3 / 20`\~`10 / 20`** 사이였다(이 문서가 돌린 판들에서 본 범위). 재실행마다 수가 바뀌었다(재대조가 이 줄들을 흔들리는 칸으로 걸렀다). ★ 「그러니 Chrome 은 콜백을 잘 부른다」 는 **주장하지 않는다** — **한 판이라도 불린 벌이 있다**까지만 근거다.
- ★★ **동작 (1)의 `nothing` 행과 견주면** — 압력이 없으면 **0**, 압력이 있으면 **때때로**. 「언제」 는 이 탐침이 정할 수 없고, **정할 수 없다는 것이 이 블록의 결론**이다.

### (4) ★ 등록과 취소 — 무엇을 돌려주나

**언제 쓰나** — 정리를 **명시적으로 끝낸 뒤** 콜백이 안 오게 하고 싶을 때.

```js
// js44b-47d-registry-api.js
// What the FinalizationRegistry and WeakRef objects offer, and what unregister() answers.
const run = (label, f) => {
  let r;
  try { r = "ok " + String(f()); } catch (e) { r = e.constructor.name + " 「" + e.message + "」"; }
  console.log("  " + label.padEnd(52) + r);
};
const own = (o) => Object.getOwnPropertyNames(o).join(" ");
console.log("[1] own properties");
run("WeakRef.prototype", () => own(WeakRef.prototype));
run("FinalizationRegistry.prototype", () => own(FinalizationRegistry.prototype));
console.log("[2] register and unregister");
const reg = new FinalizationRegistry(() => {});
const token = {};
run("reg.register({}, 'h1', token)", () => reg.register({}, "h1", token));
run("reg.register({}, 'h2', token)", () => reg.register({}, "h2", token));
run("reg.unregister(token)   (first time)", () => reg.unregister(token));
run("reg.unregister(token)   (second time)", () => reg.unregister(token));
run("reg.unregister({})   (a token never used)", () => reg.unregister({}));
run("reg.unregister(1)", () => reg.unregister(1));
const t = {};
run("reg.register(t, 'h', t)   (token = target)", () => reg.register(t, "h", t));
run("reg.unregister(t)", () => reg.unregister(t));
run("reg.register({}, 'h', 1)   (a number as token)", () => reg.register({}, "h", 1));
run("new FinalizationRegistry()", () => new FinalizationRegistry());
```

```text
===== node20 js44b-47d-registry-api.js (exit=0) =====
[1] own properties
  WeakRef.prototype                                   ok constructor deref
  FinalizationRegistry.prototype                      ok constructor register unregister
[2] register and unregister
  reg.register({}, 'h1', token)                       ok undefined
  reg.register({}, 'h2', token)                       ok undefined
  reg.unregister(token)   (first time)                ok true
  reg.unregister(token)   (second time)               ok false
  reg.unregister({})   (a token never used)           ok false
  reg.unregister(1)                                   TypeError 「Invalid unregisterToken ('1')」
  reg.register(t, 'h', t)   (token = target)          ok undefined
  reg.unregister(t)                                   ok true
  reg.register({}, 'h', 1)   (a number as token)      TypeError 「Invalid unregisterToken ('1')」
  new FinalizationRegistry()                          TypeError 「FinalizationRegistry: cleanup must be callable」
```

node 18 — 문구만 다르다.

```text
===== node18 js44b-47d-registry-api.js (exit=0) =====
[1] own properties
  WeakRef.prototype                                   ok constructor deref
  FinalizationRegistry.prototype                      ok constructor register unregister
[2] register and unregister
  reg.register({}, 'h1', token)                       ok undefined
  reg.register({}, 'h2', token)                       ok undefined
  reg.unregister(token)   (first time)                ok true
  reg.unregister(token)   (second time)               ok false
  reg.unregister({})   (a token never used)           ok false
  reg.unregister(1)                                   TypeError 「unregisterToken ('1') must be an object」
  reg.register(t, 'h', t)   (token = target)          ok undefined
  reg.unregister(t)                                   ok true
  reg.register({}, 'h', 1)   (a number as token)      TypeError 「unregisterToken ('1') must be an object」
  new FinalizationRegistry()                          TypeError 「FinalizationRegistry: cleanup must be callable」
```

- ★★ **`WeakRef.prototype` 에는 `deref` 하나**, **`FinalizationRegistry.prototype` 에는 `register`·`unregister` 둘**(과 `constructor`) — 「지금 몇 개 등록돼 있나」·「이 대상이 아직 살아 있나」를 묻는 **다른 창이 없다.**
- ★★ **`unregister(token)` — 처음 `true`, 둘째 `false`, 안 쓴 토큰 `false`.** 같은 토큰으로 둘을 등록했으면 **한 번에 둘 다** 지워진다(명세 — 토큰이 같은 칸을 전부 지운다).
- ★★ **`unregister(1)` · 토큰 `1` 로 `register` — `TypeError`**(토큰은 `CanBeHeldWeakly` 여야 한다). **문구는 판마다 달랐다** — node 20 · Chrome 151 `Invalid unregisterToken ('1')`, node 18 `unregisterToken ('1') must be an object`.
- ★ **토큰 = 대상(`register(t, 'h', t)`)은 된다** — 명세 note 「자기 자신을 토큰으로 등록해도 영원히 살리지 않는다」. (보관값 = 대상은 `TypeError` 다 — 23번.)
- ★ **`unregister` 가 콜백만 취소하고 수거는 막지 않는다**는 것은 23번이 쟀다(콜백 `0/20` · `deref()` `0/20`).

### (5) ★★ CPython 과 한 쌍 — `del` 다음 줄보다 먼저

**언제 쓰나** — 「파이썬에서는 되던 정리 패턴」 을 JS 로 옮길 때.

```python
# js44b-47e-python.py
# The same question in CPython: a weakref.ref and a weakref.finalize on an object, then del.
# [1]-[2] an object that only one name holds; [3]-[5] an object that holds itself (a reference cycle).
import gc
import weakref


class Box:
    pass


b = Box()
r = weakref.ref(b)
weakref.finalize(b, print, "  finalize callback for b ran")
print("[1] before del b: r() is alive ->", r() is not None)
del b
print("[2] the line after del b: r() ->", r())

c = Box()
c.me = c
r2 = weakref.ref(c)
weakref.finalize(c, print, "  finalize callback for c ran")
del c
print("[3] the line after del c (c.me = c): r2() is None ->", r2() is None)
print("[4] gc.collect() found", gc.collect(), "unreachable objects")
print("[5] after gc.collect(): r2() is None ->", r2() is None)
```

```text
===== python3 js44b-47e-python.py (exit=0) =====
[1] before del b: r() is alive -> True
  finalize callback for b ran
[2] the line after del b: r() -> None
[3] the line after del c (c.me = c): r2() is None -> False
  finalize callback for c ran
[4] gc.collect() found 2 unreachable objects
[5] after gc.collect(): r2() is None -> True
```

```text
   CPython (참조 계수 + 순환 수집기)                       JS (추적 GC · 명세는 may)
   del b   ─▶ 계수 0 ─▶ 즉시 해제 ─▶ finalize 콜백 ─▶ 다음 줄     deref() 는 턴이 끝나야 비워질 「수」 있다
   del c   (c.me = c) ─▶ 계수 1 남음 ─▶ 안 풀림                   콜백은 「may」 — gc() 없이는 0/20
   gc.collect() ─▶ 순환 수거 ─▶ 콜백 ─▶ None
```

- ★★★ **`[1]` 과 `[2]` 사이에 `finalize callback for b ran`** — `del b` 의 **그 줄에서** 콜백이 돌았고, `[2]` 는 이미 `None` 이다. CPython 은 **참조 계수가 0 이 되는 순간** 해제한다(Python 01번 — 「`del` 은 이름을 지운다」·「참조를 세는 두 도구」).
- ★★★ **순환은 다르다** — `c.me = c` 면 `del c` 뒤에도 `r2() is None -> False`, **`gc.collect()` 가 순환을 거둔 뒤에야** 콜백과 `True`. 파이썬에서도 「즉시」 는 **순환이 없을 때만**이다.
- ★★ **`python3.11`(3.11.15)로 같은 파일을 돌려도 한 글자도 같았다**(블록은 3.12 판 하나만 싣는다 — 규칙 10). 단 이것도 **CPython 의 구현**이다 — 언어 문서가 즉시 해제를 약속하는 것은 아니다(이 문서는 그 문서를 확인하지 않았다).
- ★★ **C++ `weak_ptr` 도 결정적 쪽**이다 — 마지막 `shared_ptr` 가 죽는 순간 `lock()` 이 `nullptr`(C++ 27 · 28번). **JS 만 「언제」 가 명세 밖**이다.

## 문법 — 형태와 규칙

★ 이 절은 **형태 표**다 — 모든 동작 주장은 위 동작 절의 캡처 블록에서만 한다.

| 형태 | 하는 일 | 보장 | 어디서 봤나 |
|---|---|---|---|
| `new WeakRef(target)` | 대상을 붙들지 않는 참조 · **그 동기 실행 동안은** 대상을 살려 둔다 | 명세 | 동작 (1) `no wait` |
| `ref.deref()` | 대상 또는 `undefined` · 돌려주면 **다시** 살려 둔다 | 명세 | 동작 (2) `[3]`·`[4]` |
| `new FinalizationRegistry(cb)` | 콜백 등록부 — `cb` 가 함수가 아니면 `TypeError` | 명세 | 동작 (4) |
| `reg.register(target, held, token?)` | 대상이 비워지면 `cb(held)` 를 **부를 수 있다** | 콜백은 **may** | 동작 (1) `callback` 열 |
| `reg.unregister(token)` | 그 토큰의 칸을 전부 지운다 → 지웠으면 `true` | 명세 | 동작 (4) |
| `gc()` | 전역 함수 — **`--expose-gc` 가 있을 때만** | ★ **V8 플래그** | 판별 블록 |

## 어디서 틀리나

### (1) ★★★ `FinalizationRegistry` 콜백을 정리의 **보장**으로 쓴다

`gc()` 없이는 이 판에서 **한 칸도 안 불렸고**(동작 (1)), 압력을 주면 **벌마다 달랐다**(동작 (3)). 명세는 "may". 파일·락·소켓은 `try`/`finally`·명시적 `close()`(23번과 같은 결론).

### (2) ★★★ 「`gc()` 를 부르면 비워진다」 를 언어의 성질로 적는다

**V8 플래그가 연 함수에 대한 이 판의 관찰**이다(`20/20`). `gc()` 는 ECMA-262 에 없다.

### (3) ★★★ 「`await` 를 지나면 새 턴이다」 로 읽는다

**`await null` 을 열 번 지나도 같은 체크포인트** — `gc()` 뒤 `deref()` 가 `20/20` 객체였다(동작 (1)). 비워질 수 있는 것은 **매크로태스크를 넘긴 뒤**였다(이 두 호스트).

### (4) ★★ `deref()` 결과를 변수에 두지 않고 매번 다시 부른다

같은 턴 안에서는 **둘 다 같은 값**이라 괜찮다(명세). 문제는 **턴을 넘긴 뒤의 첫 `deref()`** 다 — 그때마다 `undefined` 를 다룰 분기가 있어야 한다.

### (5) ★★ 개발 중에 안 비워지니 「안 새는 캐시」 라고 믿는다 · 반대로 「곧 비워지는 캐시」 라고 믿는다

**둘 다 근거가 없다** — `gc()` 없이는 0, 압력을 주면 가끔(동작 (1)·(3)).

### (6) ★ 파이썬의 `weakref.finalize` 처럼 `del` 직후 정리를 기대한다

CPython 은 **참조 계수**라 즉시였다(동작 (5)) — JS 에는 그런 순간이 없다.

## 구현 세부사항 대 언어 보장

### 명세 보장(ECMA-262)

- ★★★ **어떤 객체도 비워진다는 보장이 없다** — "or never at all".
- ★★★ **`[[KeptAlive]]`** — `new WeakRef` 와 `deref()` 가 대상을 넣고, **동기 실행이 끝날 때** `ClearKeptObjects` 가 비운다. 그 전에는 `deref()` 가 대상을 돌려준다(동작 (1) `no wait` · 동작 (2) `[1]`·`[4]`).
- ★★ **정리 콜백은 동기 실행을 끊고 들어오지 않는다** · 부를지는 구현의 선택.
- ★★ `unregister` 의 반환값 · 토큰이 `CanBeHeldWeakly` 가 아니면 `TypeError`.

### 호스트

- ★★★ **`ClearKeptObjects` 를 언제 부르나** — HTML 은 **마이크로태스크 체크포인트의 끝**. node 도 같은 자리로 보였다(`await ×10` 도 `0/20`). ★ 「node 가 HTML 과 같은 규칙을 쓴다」 는 **관찰에서 끌어낸 것**이다 — node 문서를 확인하지 않았다.
- ★★ **정리 잡을 언제 넣나** — `HostEnqueueFinalizationRegistryCleanupJob` · HTML 도 「implementation-defined」 로 적는다.

### 구현(V8) · 이 판의 관찰

- ★★★ **`gc()`**(`--expose-gc` · Chrome 은 `--js-flags=--expose-gc`) · 한 번에 거둔 것(`20/20`) · 콜백이 열 틱 안에 온 것(`20/20`) · 압력만으로는 `deref()` 가 안 비워진 것 · 압력 아래 콜백이 가끔 온 것.
- ★ `unregister(1)` 의 **문구**(node 18 과 20 이 다르다).
- ★ CPython 의 즉시 해제 — **CPython 의 구현**(참조 계수).

### 그래서 이렇게 적으면 틀린다

- ✗ 「`WeakRef` 의 대상은 다른 참조가 없으면 GC 된다」 → ○ 「**될 수 있다** — 명세는 약속하지 않고, 이 판은 `gc()` 없이는 한 번도 안 했다」
- ✗ 「`FinalizationRegistry` 콜백은 GC 직후 불린다」 → ○ 「**이 판에서 `gc()` 를 부른 뒤** 열 틱 안에 불렸다 — 명세는 may」
- ✗ 「같은 동기 함수 안에서만 `deref()` 가 안전하다」 → ○ 「**체크포인트가 끝날 때까지** — `await` 를 넘겨도 이 두 호스트에서는 같았다」
- ✗ 「`gc()` 는 JS 의 전역 함수다」 → ○ 「**V8 플래그**가 여는 함수다」

## 언제 쓰고 언제 안 쓰나

- **`WeakRef`** — 「있으면 쓰고 없으면 다시 만드는」 캐시 · 관찰자 목록처럼 **비워져도 맞게 도는** 자리. 턴마다 `deref()` 결과를 **`undefined` 로 분기**한다.
- **`FinalizationRegistry`** — 새는 것을 **알려 주는 보조**(진단 · 외부 자원의 뒷정리 보험). 정리의 **본선**은 명시적 `close()`·`try`/`finally`(C# 갈래의 37번 · 목록의 **51번 주제** `using`).
- **`WeakMap`** — 「이 객체에 딸린 데이터」 는 대개 이쪽이다 — 키가 살아 있는 동안만 값이 살고, **비워지는 순간이 프로그램에 안 보인다**(23번 — `WeakMap` 에는 들여다볼 창이 없다). `WeakRef` 는 그 순간을 **보이게** 만드는 API 다 — 그래서 명세가 이 절 전체를 "may" 로 적는다.
- ★ **안 쓰는 자리** — 정리가 반드시 일어나야 하는 자원 · 테스트에서 `gc()` 로 확인한 동작을 운영의 가정으로 삼기.

## 핵심 문장

1. ★★★ **명세는 「비워진다」·「콜백이 불린다」 를 약속하지 않는다** — `gc()` 없이는 판 넷 모두 **「한 판이라도 본 칸 `0 / 4`」**.
2. ★★★ **명세가 약속하는 쪽** — `deref()` 가 돌려준 대상은 **동기 실행이 끝날 때까지** 계속 돌려준다. `gc()` 를 불러도 같은 턴 · `await ×10` 뒤 **`0/20` undefined**, `setTimeout` 뒤에야 **`20/20`**(이 판의 관찰).
3. ★★★ **「같은 턴」 의 끝은 호스트가 정한다** — HTML 은 마이크로태스크 체크포인트의 끝에 `ClearKeptObjects`. `deref()` 는 대상을 **다시** 붙잡는다(새 턴에서 `gc()` 전에 부르면 `object 20/20`).
4. ★★ 할당 압력만으로는 `deref()` 가 **다섯 벌 한 판도** 안 비워졌고, 콜백은 **벌마다 달랐다** — 「언제」 는 잴 수 없다는 것이 결론이다.
5. ★★ CPython 은 `del` 한 줄에 콜백이 **다음 줄보다 먼저** — 참조 계수. 순환만 `gc.collect()` 를 기다린다. **JS 만 「언제」 가 명세 밖**이다.

## 관련 자료

- [ECMA-262 — Processing Model of WeakRef and FinalizationRegistry Targets](https://tc39.es/ecma262/multipage/executable-code-and-execution-contexts.html) · [ECMA-262 — Managing Memory](https://tc39.es/ecma262/multipage/managing-memory.html) · [HTML — Event loops / microtask checkpoint](https://html.spec.whatwg.org/multipage/webappapis.html)
- [23 — `Map`·`Set` 과 약한 컬렉션](../23-map-set-and-weak-collections/2-summary.md) — ★ **경계**: 약한 쪽에 무엇을 넣나 · 수명 조건 6 × 20판 · 콜백의 「언제」 블록은 거기. 여기는 **기다림의 종류 · 브라우저 · 압력 · `deref()` 의 재붙잡기 · 층 가르기**.
- [`cs/foundations/memory-management/README.md`](../../../../memory-management/README.md) — README 가 가리키는 정본. ★ **경계**: 그쪽은 **메모리 계층·스택·가상 메모리·페이징**이고 GC 알고리즘 절은 없다(머리말). [Java 언어 특성](../../../java/언어-특성/README.md) — GC 전략의 논증.
- [06 — 스코프와 클로저](../06-scope-and-closures/2-summary.md) · [36 — 이벤트 루프](../36-event-loop-and-microtasks/2-summary.md) · [Python 01](../../../python/syntax/01-object-and-name-binding/2-summary.md) · [C++ 28 — `weak_ptr`](../../../cpp/syntax/28-weak-ptr-and-reference-cycles/2-summary.md).

## 용어 풀이

- **`WeakRef`** — 대상을 붙들지 않는 참조(ES2021). `deref()` 만 있다.
- **`FinalizationRegistry`** — 대상이 비워진 **뒤에** 콜백을 부를 **수 있는** 등록부(ES2021). `register`·`unregister`.
- **`[[KeptAlive]]`** — 에이전트가 들고 있는 목록. `new WeakRef`·`deref()` 가 대상을 넣고 `ClearKeptObjects` 가 비운다. 이 목록에 있는 동안 대상은 안 비워진다.
- **`ClearKeptObjects`** — 「동기 실행이 끝날 때」 목록을 비우는 명세 연산. 언제 부를지는 호스트가 정한다(HTML — 마이크로태스크 체크포인트의 끝).
- **마이크로태스크 체크포인트** — 매크로태스크 하나가 끝난 뒤 마이크로태스크 큐를 **빌 때까지** 도는 단계(36번).
- **`--expose-gc`** — V8 플래그. 전역 `gc()` 를 연다. Chrome 에는 `--js-flags=--expose-gc` 로 넘긴다.
- **참조 계수(reference counting)** — 객체를 가리키는 참조의 수를 세다가 0 이 되면 **그 순간** 해제하는 방식(CPython). 순환은 따로 수집기가 필요하다.
- **할당 압력** — 짧게 사는 객체를 많이 만들어 GC 가 스스로 돌 조건을 만드는 것(이 문서의 말).

## 더 들어가면

- **`cleanupSome`** — 제안 단계에서 빠진 메서드. 세 판 다 없다(판별 블록).
- **node 의 `ClearKeptObjects` 호출 자리** — 관찰로는 HTML 과 같았다. node 소스는 읽지 않았다.
- **GC 알고리즘 자체** — 이 목록의 몫이 아니다(머리말의 경계).
