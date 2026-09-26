# js/syntax/45 — `Proxy`: 「트랩은 무엇이든 돌려줄 수 있지만, 대상이 굳혀 둔 사실과 어긋나면 엔진이 그 자리에서 `TypeError` 로 끊는다」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> ★★★ **이 주제의 본체는 ② 전수 격자다** — 트랩 **8개** × 대상 상태 **3개**(보통 · `x` 가 쓰기 불가+설정 불가 · `preventExtensions`) = **24칸**에서, 트랩이 **대상과 다른 답**을 돌려줄 때 **던진 칸 N / 24** 를 스크립트가 찍는다(동작 (1)의 `[1]`). 같은 24칸을 **`Reflect` 로 넘기는 트랩**으로 다시 돌려 「**맨 대상과 답이 다른 칸 N / 24**」도 찍는다(`[2]` — 46번이 이 줄을 인용한다).
> ★★ 보조로 **④ 예외의 이름 + 문구**(불변식 위반 문구 12개 · 내부 슬롯 `Method Map.prototype.get called on incompatible receiver` — 동작 (1)의 `[3]` · (3)) · **③ 브랜드 태그**(`[object Map]` 인데 `Map` 메서드가 안 도는 것 — 동작 (4))를 쓴다.
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262 — Proxy Object Internal Methods and Internal Slots](https://tc39.es/ecma262/multipage/ordinary-and-exotic-objects-behaviours.html) — 내부 메서드 13개(`[[GetPrototypeOf]]` · `[[SetPrototypeOf]]` · `[[IsExtensible]]` · `[[PreventExtensions]]` · `[[GetOwnProperty]]` · `[[DefineOwnProperty]]` · `[[HasProperty]]` · `[[Get]]` · `[[Set]]` · `[[Delete]]` · `[[OwnPropertyKeys]]` · `[[Call]]` · `[[Construct]]`)마다 붙은 note 「**… enforces the following invariants**」 · `[[Get]]` 은 트랩 결과를 받은 **뒤** 대상의 `[[GetOwnProperty]]` 를 읽어 「설정 불가 + 쓰기 불가 데이터 프로퍼티면 **`SameValue` 가 거짓일 때 `TypeError`**」 · `ProxyCreate` 는 **대상이 호출 가능할 때만 `[[Call]]` 을 단다** · 트랩이 없으면(`GetMethod` 가 `undefined`) **대상의 내부 메서드를 그대로** 부른다 · `ValidateNonRevokedProxy`
> - [ECMA-262 — Reflection · `Proxy.revocable`](https://tc39.es/ecma262/multipage/reflection.html) — 취소 함수는 `[[ProxyTarget]]`·`[[ProxyHandler]]` 를 **`null` 로 비우고**, 두 번째 호출은 **그냥 `undefined`**
> - ★ **`Proxy` 는 ES2015 본문**이다(TC39 finished proposals 표에 없다).
>
> ★★★ **명세 조항 번호는 인용하지 않는다.** 규칙 진술은 **내부 메서드 이름**으로, 값·예외는 **전부 실행으로** 접지했다.
>
> **실행 검증** — 이 문서의 모든 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다.
> 배너의 `node20` 은 v20.19.6, `node18` 은 v18.19.1 이다. 하네스(헤드리스 Chrome · 로컬 서버)의 소스는 [44번](../44-dynamic-import-top-level-await-and-import-attributes/2-summary.md) 머리말에 있다.
> ★★★ **이 주제의 탐침 넷은 node 18 · node 20 · Chrome 151 에서 한 글자도 같았다** — 예외 **문구까지**(세 판 대조기 · 아래 집계 줄). 그래서 블록은 **node 20 판 하나씩**만 싣는다.
> ★★★ **성능은 재지 않았다** — 「`Proxy` 는 느리다」를 **쓰지 않는다.**
>
> **버전** — `Proxy` · `Proxy.revocable` · 트랩 13개 · 불변식 검사는 전부 **ES2015** 다. 판별 블록에서 세 판 다 있다.
>
> **★★★ 이 주제가 쓰는 창 — 그리고 부적용인 창**
>
> | 창 | 이 주제에서 무엇을 보나 |
> |---|---|
> | ★★★ **② 전수 격자**(본체) | 트랩 8 × 상태 3 — 거짓말하는 트랩 「`cells that threw: N / 24`」 · 넘기는 트랩 「`bare target gave a different answer: N / 24`」(동작 (1)) |
> | ★★ **④ 예외의 이름 + 문구** | 불변식 위반 문구 12개 — **무엇을 어겼는지 문구가 말한다**(동작 (1)의 `[3]`) · 내부 슬롯 문구(동작 (3)) · 취소된 Proxy 문구(동작 (4)) |
> | ★★ **엄격 / 비엄격 한 쌍** | `set`·`deleteProperty` 트랩의 `false` 가 **엄격에서만** `TypeError`(동작 (2)) |
> | ★★ **③ 브랜드 태그** | `Object.prototype.toString` 이 `[object Map]` · `Array.isArray` 가 `true` — 그런데 `Map` 메서드는 `TypeError`(동작 (3)·(4)) |
> | ★ **부적용 — 판 격자** | 세 판이 한 글자도 같아 **갈린 칸이 없다**(집계 줄) — 불변식 검사는 **언어**의 것이다 |
> | ★ **안 쟀다 — 성능** | 트랩 한 번의 비용은 재지 않았다 |
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 판별 블록의 판 문자열 | ★★★ 격자의 모든 칸과 두 집계 줄 · 예외의 **종류** · 로그 값 |
> | ★ **이 주제의 탐침에는 재실행에서 흔들린 칸이 없다**(재대조 동일) | ★★ 예외 **문구** — 이 세 판에서는 같았지만 **엔진 판의 것**이다(규칙 27 — 칸이 근거, 문구는 보조) |
>
> **층** — 트랩 이름 · 트랩이 불리는 조건 · **불변식 검사와 그 `TypeError`** 는 전부 **언어(ECMA-262)** 다. 문구만 **엔진(V8)** 의 것이다. 호스트는 끼지 않는다.
>
> **선행** — [14 — 프로퍼티 디스크립터와 동결](../14-property-descriptors-and-freezing/2-summary.md)(직접 선행 — ★★★ **「막힌 것은 값이 아니라 플래그에 적혀 있다」** · 설정 불가 27칸 격자 · ★★ **비엄격에서는 막힌 쓰기가 조용히 버려진다**(거기 동작 (4)) — 이 문서의 「대상 상태」 세 가지가 거기서 온다) ·
> [15 — 프로토타입 체인](../15-prototype-chain/2-summary.md)(★★ **`Proxy` 를 로그 도구로만** 썼다 — 거기 머리말이 「트랩의 계약과 불변식은 45번이 정본」이라고 적는다) ·
> [35 — 엄격 모드](../35-strict-mode/2-summary.md) · [16 — `class` 문법](../16-class-syntax/2-summary.md)(프라이빗 `#x`).
>
> ★★ **교차 갈래** — 파이썬은 가로채는 자리가 **클래스의 갈고리 메서드**다: [Python 29 — 클래스와 속성 조회](../../../python/syntax/29-classes-and-attribute-lookup/2-summary.md)의 **6절 「두 갈고리 — `__getattr__` 과 `__getattribute__`」**. JS 의 `Proxy` 는 **대상 객체를 감싼 별도 객체**이고, 파이썬의 갈고리는 **그 클래스 자신**에 붙는다. 파이썬 쪽에 이 문서의 「불변식 검사」에 해당하는 것이 있는지는 **여기서 돌리지 않았다.**
> ★ Java 의 `java.lang.reflect.Proxy` 는 [Java 58 — 리플렉션](../../../java/syntax/58-reflection/2-summary.md)에 **절이 없다**(그 파일에서 `Proxy` 를 찾으면 0건).

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

세 판 대조기의 집계 줄 — 전문은 [3-answer.md](3-answer.md) 의 「실행 검증」에 있다.

`node18 vs node20: identical 7 · differs 2   ·   node20 vs Chrome 151: identical 8 · differs 0 · node only 1`

## 한눈에 — 쉽게 말하면

**`Proxy` 는 「대리인」이다. 누가 대상 객체에 무엇을 묻든 대리인이 먼저 받고(트랩), 원하면 대답을 지어낼 수 있다. 다만 대상이 공증해 둔 사실(설정 불가 · 확장 불가)과 어긋나는 대답을 하면, 공증인(엔진)이 그 자리에서 대답을 찢어 버린다(`TypeError`).**

- ★★★ **트랩은 보통 대상 앞에서는 무엇이든 말할 수 있다** — `get` 이 `'lie'` 를, `has` 가 `false` 를, `ownKeys` 가 `[]` 를 돌려줘도 **보통 대상이면 통과**한다(24칸 중 보통 열 8칸 전부).
- ★★★ **대상이 굳혀 둔 사실을 부정하면 `TypeError`** — 설정 불가·쓰기 불가 `x` 앞에서는 8개 중 **7개**가, `preventExtensions` 앞에서는 **5개**가 던졌다 — **`12 / 24`**.
- ★★ **`Reflect` 로 그대로 넘기면 맨 대상과 구분이 안 된다** — 24칸 전부 **맨 대상과 같은 답**(`0 / 24`).
- ★★ **대리인은 대상의 「속」까지는 못 빌린다** — `Map`·`Set`·`Date`·프라이빗 `#x` 는 **`this` 가 Proxy 면** `TypeError`. 겉모습(`[object Map]`)은 빌린다.

```text
   p.x  ─▶ [[Get]](p)
             │
             ├─ handler.get 이 없으면 ─▶ target.[[Get]] 그대로          (투명)
             │
             └─ trapResult = handler.get(target, "x", p)
                   │
                   ▼  공증 대조 — target.[[GetOwnProperty]]("x")
                   설정 불가 + 쓰기 불가 데이터?  ── 예 ─▶ SameValue(trapResult, 진짜 값)?
                   │ 아니오                                  │ 예 → 통과     │ 아니오 → TypeError
                   ▼
                  trapResult 그대로 돌려준다 ('lie' 도 통과)
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 대리인 | `new Proxy(target, handler)` — 별도 객체 | 동작 (4) `typeof` |
| 먼저 받는 창구 | 트랩 — `handler.get` 등 13개 | 동작 (1) |
| 대답을 지어낸다 | 트랩의 반환값 — 보통 대상 앞에서는 무엇이든 | 동작 (1)의 보통 열 |
| 공증해 둔 사실 | 설정 불가(`configurable: false`) · 확장 불가 | 14번 · 동작 (1)의 두 열 |
| 공증인이 찢는다 | 내부 메서드가 트랩 결과를 **대상과 대조**하고 어긋나면 `TypeError` | 동작 (1)의 `[1]`·`[3]` |
| 대리인이 못 빌리는 속 | 내부 슬롯(`[[MapData]]` · `[[DateValue]]`) · 프라이빗 이름 | 동작 (3) |
| 위임장 회수 | `Proxy.revocable` 의 `revoke()` | 동작 (4) |

**똑같은 구조다** — 실무에서 물리는 자리도 굳어 있다.
「**`Object.freeze` 한 설정을 Proxy 로 감싸 기본값을 끼워 넣다 `TypeError`**」,
「**`Map` 을 Proxy 로 감싸자 `.get()` 이 `incompatible receiver`**」,
「**비엄격 코드에서 `set` 트랩이 `false` 를 돌려줘도 아무 일도 안 난다**」가 그것이다(동작 (1)·(2)·(3)).

> **트랩(trap)** — `Proxy` 의 `handler` 에 두는 함수. 대상 객체의 내부 동작(읽기·쓰기·삭제·열거 …)을 가로챈다.\
> 예: `new Proxy({}, { get: (t, k) => k.toUpperCase() }).abc` → `"ABC"`.

## 이 주제가 답하려는 질문

1. **트랩이 대상과 다른 답을 돌려주면 언제 `TypeError` 인가** — 트랩 8개 × 대상 상태 3개의 24칸에서?
2. **트랩이 `false` 를 돌려주면** — 엄격과 비엄격에서 무엇이 다른가?
3. **Proxy 는 대상을 어디까지 흉내 내나** — 내부 슬롯이 있는 내장 객체 · 프라이빗 이름 · `typeof` · `Array.isArray` · 취소한 뒤에는?

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 출력으로 읽는다.

### (1) ★★★ 불변식 격자 — 트랩 8 × 대상 상태 3

**언제 쓰나** — 동결·봉인된 객체를 Proxy 로 감쌀 때 · 트랩이 값을 「고쳐서」 돌려주고 싶을 때.
★★★ **탐침 파일은 일부러 비엄격**이다 — 실패한 대입·삭제가 비엄격에서는 던지지 않으므로(14번 동작 (4)), **표 `[1]` 에서 던진 것은 전부 Proxy 의 대조**다. 칸마다 **새 대상 · 새 Proxy** 다.

```js
// js44b-45a-invariant-grid.js
// Eight traps x three states of the target. In each cell the handler has one trap, and the probe runs one operation on the proxy.
// Sloppy-mode script on purpose: an assignment or a delete that fails does not throw here, so what throws comes from the proxy.
// Table [1]: the trap reports something the target does not hold (column "what the trap returns").
// Table [2]: the same trap hands the call on with Reflect.<the same name>(...arguments),
//            and each cell is compared with the same operation on the bare target (no proxy).
// [3]: the message of every exception in table [1].
// A cell prints "ok " + what the operation gave, or the name of the exception it threw.
const states = [
  ["ordinary", () => ({ x: "real" })],
  ["x non-writable+non-configurable", () => Object.defineProperty({}, "x", { value: "real", writable: false, configurable: false, enumerable: true })],
  ["preventExtensions", () => Object.preventExtensions({ x: "real" })],
];
const desc = (d) => (d === undefined ? undefined : d.value + " w:" + d.writable + " c:" + d.configurable);
const traps = [
  ["get", "'lie'", () => "lie", (p) => p.x],
  ["set", "true (writes nothing)", () => true, (p) => { p.x = "new"; return p.x; }],
  ["has", "false", () => false, (p) => "x" in p],
  ["deleteProperty", "true (deletes nothing)", () => true, (p) => delete p.x],
  ["defineProperty", "true (defines nothing)", () => true, (p) => { Object.defineProperty(p, "x", { value: "new" }); return p.x; }],
  ["getOwnPropertyDescriptor", "undefined", () => undefined, (p) => desc(Object.getOwnPropertyDescriptor(p, "x"))],
  ["ownKeys", "[]", () => [], (p) => Object.keys(p)],
  ["getPrototypeOf", "a new {}", () => ({}), (p) => Object.getPrototypeOf(p) === Object.prototype],
];
const messages = [];
const run = (subject, op, where) => {
  try { return "ok " + JSON.stringify(op(subject)); }
  catch (e) { if (where) messages.push(where + ": " + e.message); return e.constructor.name; }
};
const head = () => console.log("  " + "trap".padEnd(25) + "what the trap returns".padEnd(34) + states.map(([s]) => s.padEnd(33)).join("").trimEnd());
const row = (name, second, cells) => console.log("  " + name.padEnd(25) + second.padEnd(34) + cells.map((c) => c.padEnd(33)).join("").trimEnd());

console.log("[1] the trap returns what is in the second column");
head();
let thrown = 0;
for (const [name, lie, trap, op] of traps) {
  const cells = states.map(([s, make]) => run(new Proxy(make(), { [name]: trap }), op, name + " / " + s));
  thrown += cells.filter((c) => !c.startsWith("ok")).length;
  row(name, lie, cells);
}
console.log("  cells that threw: " + thrown + " / " + traps.length * states.length);

console.log("");
console.log("[2] the trap forwards with Reflect");
head();
let thrown2 = 0, differ = 0;
for (const [name, , , op] of traps) {
  const cells = states.map(([, make]) => {
    const viaProxy = run(new Proxy(make(), { [name]: (...args) => Reflect[name](...args) }), op);
    if (viaProxy !== run(make(), op)) differ++;
    if (!viaProxy.startsWith("ok")) thrown2++;
    return viaProxy;
  });
  row(name, "Reflect." + name, cells);
}
console.log("  cells that threw: " + thrown2 + " / " + traps.length * states.length);
console.log("  cells where the bare target gave a different answer: " + differ + " / " + traps.length * states.length);

console.log("");
console.log("[3] messages of the exceptions in [1]");
for (const m of messages) console.log("  " + m);
```

```text
===== node20 js44b-45a-invariant-grid.js (exit=0) =====
[1] the trap returns what is in the second column
  trap                     what the trap returns             ordinary                         x non-writable+non-configurable  preventExtensions
  get                      'lie'                             ok "lie"                         TypeError                        ok "lie"
  set                      true (writes nothing)             ok "real"                        TypeError                        ok "real"
  has                      false                             ok false                         TypeError                        TypeError
  deleteProperty           true (deletes nothing)            ok true                          TypeError                        TypeError
  defineProperty           true (defines nothing)            ok "real"                        TypeError                        ok "real"
  getOwnPropertyDescriptor undefined                         ok undefined                     TypeError                        TypeError
  ownKeys                  []                                ok []                            TypeError                        TypeError
  getPrototypeOf           a new {}                          ok false                         ok false                         TypeError
  cells that threw: 12 / 24

[2] the trap forwards with Reflect
  trap                     what the trap returns             ordinary                         x non-writable+non-configurable  preventExtensions
  get                      Reflect.get                       ok "real"                        ok "real"                        ok "real"
  set                      Reflect.set                       ok "new"                         ok "real"                        ok "new"
  has                      Reflect.has                       ok true                          ok true                          ok true
  deleteProperty           Reflect.deleteProperty            ok true                          ok false                         ok true
  defineProperty           Reflect.defineProperty            ok "new"                         TypeError                        ok "new"
  getOwnPropertyDescriptor Reflect.getOwnPropertyDescriptor  ok "real w:true c:true"          ok "real w:false c:false"        ok "real w:true c:true"
  ownKeys                  Reflect.ownKeys                   ok ["x"]                         ok ["x"]                         ok ["x"]
  getPrototypeOf           Reflect.getPrototypeOf            ok true                          ok true                          ok true
  cells that threw: 1 / 24
  cells where the bare target gave a different answer: 0 / 24

[3] messages of the exceptions in [1]
  get / x non-writable+non-configurable: 'get' on proxy: property 'x' is a read-only and non-configurable data property on the proxy target but the proxy did not return its actual value (expected 'real' but got 'lie')
  set / x non-writable+non-configurable: 'set' on proxy: trap returned truish for property 'x' which exists in the proxy target as a non-configurable and non-writable data property with a different value
  has / x non-writable+non-configurable: 'has' on proxy: trap returned falsish for property 'x' which exists in the proxy target as non-configurable
  has / preventExtensions: 'has' on proxy: trap returned falsish for property 'x' but the proxy target is not extensible
  deleteProperty / x non-writable+non-configurable: 'deleteProperty' on proxy: trap returned truish for property 'x' which is non-configurable in the proxy target
  deleteProperty / preventExtensions: 'deleteProperty' on proxy: trap returned truish for property 'x' but the proxy target is non-extensible
  defineProperty / x non-writable+non-configurable: 'defineProperty' on proxy: trap returned truish for adding property 'x'  that is incompatible with the existing property in the proxy target
  getOwnPropertyDescriptor / x non-writable+non-configurable: 'getOwnPropertyDescriptor' on proxy: trap returned undefined for property 'x' which is non-configurable in the proxy target
  getOwnPropertyDescriptor / preventExtensions: 'getOwnPropertyDescriptor' on proxy: trap returned undefined for property 'x' which exists in the non-extensible proxy target
  ownKeys / x non-writable+non-configurable: 'ownKeys' on proxy: trap result did not include 'x'
  ownKeys / preventExtensions: 'ownKeys' on proxy: trap result did not include 'x'
  getPrototypeOf / preventExtensions: 'getPrototypeOf' on proxy: proxy target is non-extensible but the trap did not return its actual prototype
```

```text
   거짓말하는 트랩 — 어느 칸이 던졌나 (T = TypeError, · = 통과)

                            보통    x 설정불가+쓰기불가    preventExtensions
   get       → 'lie'          ·            T                      ·
   set       → true           ·            T                      ·
   has       → false          ·            T                      T
   deleteProperty → true      ·            T                      T
   defineProperty → true      ·            T                      ·
   getOwnPropertyDescriptor → undefined
                              ·            T                      T
   ownKeys   → []             ·            T                      T
   getPrototypeOf → {}        ·            ·                      T
                             ───          ───                    ───
                             0 / 8        7 / 8                  5 / 8         합 12 / 24
```

- ★★★ **`[1]` 마지막 줄 — `cells that threw: 12 / 24`.** 보통 열은 **8칸 전부 통과**다 — `get` 이 `"lie"` 를, `has` 가 `false` 를, `ownKeys` 가 `[]` 를 돌려줘도 된다. **대상이 아무것도 굳혀 두지 않았으면 대조할 것이 없다.**
- ★★★ **설정 불가+쓰기 불가 열 — 7 / 8** 이 던졌다. 빠진 하나는 **`getPrototypeOf`** — 프로토타입을 굳히는 것은 **확장 불가**이지 프로퍼티 플래그가 아니다. 그래서 **`preventExtensions` 열에서만** 던졌다.
- ★★★ **`preventExtensions` 열 — 5 / 8.** 통과한 셋(`get`·`set`·`defineProperty`)은 **`x` 가 아직 쓰기 가능·설정 가능**이라 값에 대해서는 대조할 사실이 없다. 던진 다섯은 **「있는 것을 없다고 하기」**(`has`·`getOwnPropertyDescriptor`·`ownKeys`) · **「지우지 않고 지웠다고 하기」**(`deleteProperty`) · **프로토타입 바꿔 말하기**(`getPrototypeOf`)다 — 확장 불가 대상은 **키 목록과 프로토타입이 굳는다.**
- ★★★ **`[3]` 의 문구가 무엇을 어겼는지 말한다** — 예: `'get' on proxy: property 'x' is a read-only and non-configurable data property on the proxy target but the proxy did not return its actual value (expected 'real' but got 'lie')`. 명세 note 의 불변식 문장과 **1:1** 로 읽힌다.
- ★★★ **`[2]` — `Reflect` 로 넘기면 `bare target gave a different answer: 0 / 24`.** 던진 **1칸**(`defineProperty` / 설정 불가)은 Proxy 탓이 아니다 — **맨 대상도 같은 `TypeError`** 다(`Object.defineProperty` 가 `false` 를 예외로 바꾼다 — 46번). 대입·삭제 실패는 비엄격이라 `ok "real"` · `ok false` 로 조용히 지나갔다(맨 대상과 같다).

### (2) ★★ 트랩이 `false` 를 돌려주면 — 엄격 대 비엄격

**언제 쓰나** — 「쓰기 금지」 Proxy 를 만들려고 `set` 트랩에서 `false` 를 돌려줄 때.
★ **엄격 함수를 먼저** 돌렸다(규칙 22). 이 탐침은 전역을 만들지 않는다.

```js
// js44b-45c-falsish.js
// A set trap and a deleteProperty trap that return false -- the same statement in a strict function and in a sloppy one.
// Strict first (rule 22), then sloppy, then the Reflect calls that report the same result as a value.
const p = new Proxy({}, { set: () => false, deleteProperty: () => false });
const run = (f) => { try { return "no exception · " + f(); } catch (e) { return e.constructor.name + " 「" + e.message + "」"; } };
function strictSet() { "use strict"; p.x = 1; return "p.x = " + p.x; }
function sloppySet() { p.x = 1; return "p.x = " + p.x; }
function strictDelete() { "use strict"; return "delete gave " + delete p.x; }
function sloppyDelete() { return "delete gave " + delete p.x; }
console.log("[1] strict  p.x = 1     -> " + run(strictSet));
console.log("[2] sloppy  p.x = 1     -> " + run(sloppySet));
console.log("[3] strict  delete p.x  -> " + run(strictDelete));
console.log("[4] sloppy  delete p.x  -> " + run(sloppyDelete));
console.log("[5] Reflect.set(p, 'x', 1) -> " + Reflect.set(p, "x", 1) + " · Reflect.deleteProperty(p, 'x') -> " + Reflect.deleteProperty(p, "x"));
```

```text
===== node20 js44b-45c-falsish.js (exit=0) =====
[1] strict  p.x = 1     -> TypeError 「'set' on proxy: trap returned falsish for property 'x'」
[2] sloppy  p.x = 1     -> no exception · p.x = undefined
[3] strict  delete p.x  -> TypeError 「'deleteProperty' on proxy: trap returned falsish for property 'x'」
[4] sloppy  delete p.x  -> no exception · delete gave false
[5] Reflect.set(p, 'x', 1) -> false · Reflect.deleteProperty(p, 'x') -> false
```

- ★★★ **`[1]` 엄격 — `TypeError 「'set' on proxy: trap returned falsish for property 'x'」`, `[2]` 비엄격 — `no exception · p.x = undefined`.** `false` 는 「안 썼다」는 **보고**일 뿐이고, 그 보고를 예외로 바꾸는 것은 **엄격 모드의 대입**이다(14번 동작 (4)와 같은 규칙이 Proxy 에도 그대로 선다).
- ★★ **`delete` 도 같다** — 엄격 `TypeError`, 비엄격 `delete gave false`.
- ★★ **`[5]` `Reflect.set`·`Reflect.deleteProperty` 는 모드와 무관하게 `false` 를 값으로** 돌려준다 — 46번의 「`Reflect` 는 던지는 대신 `false`」다.
- ★ 이 `TypeError` 는 **불변식 위반이 아니다** — 문구가 `trap returned falsish` 로 동작 (1)의 `[3]`(`trap returned truish …`)과 갈린다.

### (3) ★★ 내부 슬롯 — `this` 가 Proxy 면 `Map` 메서드가 안 돈다

**언제 쓰나** — `Map`·`Set`·`Date`·프라이빗 필드가 있는 클래스 인스턴스를 Proxy 로 감쌀 때.

```js
// js44b-45d-internal-slots.js
// Built-in methods called with this = a Proxy whose target is the built-in object (empty handler: every trap is missing).
const run = (label, f) => {
  let r;
  try { r = "ok " + JSON.stringify(f()); } catch (e) { r = e.constructor.name + " 「" + e.message + "」"; }
  console.log("  " + label.padEnd(64) + r);
};
console.log("[1] empty handler");
run("new Proxy(new Map([[1, 'a']]), {}).get(1)", () => new Proxy(new Map([[1, "a"]]), {}).get(1));
run("new Proxy(new Map([[1, 'a']]), {}).size", () => new Proxy(new Map([[1, "a"]]), {}).size);
run("new Proxy(new Set([1]), {}).has(1)", () => new Proxy(new Set([1]), {}).has(1));
run("new Proxy(new Date(0), {}).getTime()", () => new Proxy(new Date(0), {}).getTime());
run("new Proxy([1, 2], {}).push(3)", () => new Proxy([1, 2], {}).push(3));
run("new Proxy({ n: 1, twice() { return this.n * 2; } }, {}).twice()", () => new Proxy({ n: 1, twice() { return this.n * 2; } }, {}).twice());
class C { #x = 1; getX() { return this.#x; } }
run("new Proxy(new C(), {}).getX()   (C has a private #x)", () => new Proxy(new C(), {}).getX());
console.log("[2] a get trap that binds functions to the target");
const bound = {
  get(t, k) {
    const v = Reflect.get(t, k);
    return typeof v === "function" ? v.bind(t) : v;
  },
};
run("new Proxy(new Map([[1, 'a']]), bound).get(1)", () => new Proxy(new Map([[1, "a"]]), bound).get(1));
run("new Proxy(new Map([[1, 'a']]), bound).size", () => new Proxy(new Map([[1, "a"]]), bound).size);
run("new Proxy(new C(), bound).getX()", () => new Proxy(new C(), bound).getX());
```

```text
===== node20 js44b-45d-internal-slots.js (exit=0) =====
[1] empty handler
  new Proxy(new Map([[1, 'a']]), {}).get(1)                       TypeError 「Method Map.prototype.get called on incompatible receiver #<Map>」
  new Proxy(new Map([[1, 'a']]), {}).size                         TypeError 「Method get Map.prototype.size called on incompatible receiver #<Map>」
  new Proxy(new Set([1]), {}).has(1)                              TypeError 「Method Set.prototype.has called on incompatible receiver #<Set>」
  new Proxy(new Date(0), {}).getTime()                            TypeError 「this is not a Date object.」
  new Proxy([1, 2], {}).push(3)                                   ok 3
  new Proxy({ n: 1, twice() { return this.n * 2; } }, {}).twice() ok 2
  new Proxy(new C(), {}).getX()   (C has a private #x)            TypeError 「Cannot read private member #x from an object whose class did not declare it」
[2] a get trap that binds functions to the target
  new Proxy(new Map([[1, 'a']]), bound).get(1)                    ok "a"
  new Proxy(new Map([[1, 'a']]), bound).size                      ok 1
  new Proxy(new C(), bound).getX()                                ok 1
```

```text
   p.get(1)      p = new Proxy(map, {})

   ① p.[[Get]]("get")  ─▶ 트랩 없음 ─▶ map 에서 찾는다 ─▶ Map.prototype.get     (여기까지는 된다)
   ② Map.prototype.get 을 this = p 로 부른다
   ③ RequireInternalSlot(p, [[MapData]])  ─▶ p 에는 [[MapData]] 가 없다      ─▶ TypeError
                                            (대리인은 대상의 칸을 빌려 주지 않는다)

   고침: get 트랩에서 함수면 target 에 bind  ─▶ this = map  ─▶ "a"
```

- ★★★ **`Map`·`Set`·`Date` — 전부 `TypeError`.** 문구가 원인을 적는다 — `Method Map.prototype.get called on incompatible receiver #<Map>`(받는 쪽 `#<Map>` 이 **Map 처럼 찍힌다** — 동작 (4)의 브랜드 태그와 같은 속임), `this is not a Date object.` 메서드를 **찾는 데까지는 됐고**, 그 메서드가 `this` 의 **내부 슬롯**을 찾다가 막혔다.
- ★★★ **프라이빗 `#x` 도 같다** — `Cannot read private member #x from an object whose class did not declare it`. 프라이빗 이름은 **그 객체 자신**에 붙어 있고 Proxy 는 **다른 객체**다(16번의 「인스턴스에 붙는다」).
- ★★ **배열의 `push` 와 평범한 메서드(`this.n`)는 된다** — `ok 3` · `ok 2`. 이것들은 `this` 의 **프로퍼티**만 읽고 쓰므로 트랩을 거쳐 대상에 닿는다.
- ★★ **고침 — `get` 트랩에서 함수를 대상에 `bind`** 하면 셋 다 된다(`ok "a"` · `ok 1` · `ok 1`). 대가 — 메서드 호출은 **더는 트랩을 거치지 않는다**(`this` 가 대상이 됐으니).

### (4) ★★ Proxy 가 빌리는 겉모습 — 그리고 `revoke()` 뒤

**언제 쓰나** — 「이것이 배열인가·함수인가」를 판별하는 코드에 Proxy 가 들어올 때 · Proxy 를 나중에 무효로 만들어야 할 때.

```js
// js44b-45e-what-a-proxy-looks-like.js
// What typeof, Array.isArray, Object.prototype.toString and JSON.stringify say about a Proxy -- and a revoked one.
const run = (label, f) => {
  let r;
  try { r = "ok " + String(f()); } catch (e) { r = e.constructor.name + " 「" + e.message + "」"; }
  console.log("  " + label.padEnd(52) + r);
};
const tag = (v) => Object.prototype.toString.call(v);
console.log("[1] a live proxy");
const t = {};
run("new Proxy(t, {}) === t", () => new Proxy(t, {}) === t);
run("typeof new Proxy({}, {})", () => typeof new Proxy({}, {}));
run("typeof new Proxy(function () {}, {})", () => typeof new Proxy(function () {}, {}));
run("typeof new Proxy(class {}, {})", () => typeof new Proxy(class {}, {}));
run("Array.isArray(new Proxy([], {}))", () => Array.isArray(new Proxy([], {})));
run("toString tag of new Proxy([], {})", () => tag(new Proxy([], {})));
run("toString tag of new Proxy(new Map(), {})", () => tag(new Proxy(new Map(), {})));
run("JSON.stringify(new Proxy([1, 2], {}))", () => JSON.stringify(new Proxy([1, 2], {})));
run("new Proxy({}, {}) instanceof Proxy", () => new Proxy({}, {}) instanceof Proxy);
run("Proxy({}, {})   (without new)", () => Proxy({}, {}));
console.log("[2] Proxy.revocable, then revoke()");
const o = Proxy.revocable({ a: 1 }, {});
const arr = Proxy.revocable([], {});
const fn = Proxy.revocable(function () {}, {});
run("proxy.a before revoke()", () => o.proxy.a);
o.revoke(); arr.revoke(); fn.revoke();
run("proxy.a", () => o.proxy.a);
run("'a' in proxy", () => "a" in o.proxy);
run("typeof proxy", () => typeof o.proxy);
run("typeof (a revoked proxy of a function)", () => typeof fn.proxy);
run("Array.isArray(a revoked proxy of [])", () => Array.isArray(arr.proxy));
run("revoke() a second time", () => o.revoke());
```

```text
===== node20 js44b-45e-what-a-proxy-looks-like.js (exit=0) =====
[1] a live proxy
  new Proxy(t, {}) === t                              ok false
  typeof new Proxy({}, {})                            ok object
  typeof new Proxy(function () {}, {})                ok function
  typeof new Proxy(class {}, {})                      ok function
  Array.isArray(new Proxy([], {}))                    ok true
  toString tag of new Proxy([], {})                   ok [object Array]
  toString tag of new Proxy(new Map(), {})            ok [object Map]
  JSON.stringify(new Proxy([1, 2], {}))               ok [1,2]
  new Proxy({}, {}) instanceof Proxy                  TypeError 「Function has non-object prototype 'undefined' in instanceof check」
  Proxy({}, {})   (without new)                       TypeError 「Constructor Proxy requires 'new'」
[2] Proxy.revocable, then revoke()
  proxy.a before revoke()                             ok 1
  proxy.a                                             TypeError 「Cannot perform 'get' on a proxy that has been revoked」
  'a' in proxy                                        TypeError 「Cannot perform 'has' on a proxy that has been revoked」
  typeof proxy                                        ok object
  typeof (a revoked proxy of a function)              ok function
  Array.isArray(a revoked proxy of [])                TypeError 「Cannot perform 'IsArray' on a proxy that has been revoked」
  revoke() a second time                              ok undefined
```

- ★★★ **`typeof` 는 대상을 따른다** — `{}` 는 `object`, 함수·클래스는 `function`. `ProxyCreate` 가 **대상이 호출 가능할 때만 `[[Call]]` 을 달기** 때문이고, `typeof` 는 `[[Call]]` 이 있나로 가른다.
- ★★★ **`Array.isArray(new Proxy([], {}))` 는 `true`** · 태그 `[object Array]` · `JSON.stringify` 도 `[1,2]`. **배열 판별은 Proxy 를 뚫고 대상을 본다.** 반면 `[object Map]` 은 태그만 빌린 것이다 — 동작 (3)에서 `Map` 메서드는 안 돌았다.
- ★★ **`instanceof Proxy` 는 `TypeError`** — `Proxy` 에는 `prototype` 이 없다(`Function has non-object prototype 'undefined'`). **「이것이 Proxy 인가」를 묻는 표준 수단이 없다.** `new` 없이 부르면 `Constructor Proxy requires 'new'`.
- ★★★ **`revoke()` 뒤 — `get`·`has` 는 `TypeError 「Cannot perform 'get' on a proxy that has been revoked」`**, 그런데 **`typeof` 는 여전히 `object`/`function`**(취소가 `[[Call]]` 을 떼지 않는다) · **`Array.isArray` 는 `TypeError 「Cannot perform 'IsArray' …」`** — 배열 판별이 대상을 따라가려다 막혔다. **`revoke()` 두 번째는 `undefined`**(명세 — 이미 비었으면 그냥 돌아간다).

## 문법 — 형태와 규칙

★ 이 절은 **형태 표**다 — 모든 동작 주장은 위 동작 절의 캡처 블록에서만 한다.

| 형태 | 하는 일 | 어디서 봤나 |
|---|---|---|
| `new Proxy(target, handler)` | 대리 객체 — 트랩 없는 동작은 **대상으로 그대로** | 동작 (3)의 `push` · 동작 (4) |
| `handler.get(target, key, receiver)` | 읽기 · 불변식: 설정 불가+쓰기 불가면 **진짜 값만** | 동작 (1) |
| `handler.set(target, key, value, receiver)` | 쓰기 · `false` → **엄격에서만** `TypeError` | 동작 (1)·(2) |
| `handler.has` · `deleteProperty` · `defineProperty` · `getOwnPropertyDescriptor` · `ownKeys` · `getPrototypeOf` | 각 내부 메서드 · 대상과 대조 | 동작 (1) |
| `Proxy.revocable(target, handler)` | `{ proxy, revoke }` — 취소 뒤 대부분 `TypeError` | 동작 (4) |

- **트랩 이름은 13개** — 이 문서가 격자에 쓴 8개 + `setPrototypeOf` · `isExtensible` · `preventExtensions` · `apply` · `construct`(목록과 `Reflect` 와의 1:1 은 46번).
- **`handler` 가 비어 있으면 투명**하다 — 단 **내부 슬롯과 프라이빗 이름은 예외**(동작 (3)).

## 어디서 틀리나

### (1) ★★★ 동결된 객체를 Proxy 로 감싸 값을 바꿔 보이게 한다

**`TypeError`** — 설정 불가+쓰기 불가 `x` 앞에서 `get` 이 `'lie'` 를 돌려주자 던졌다(동작 (1)). 굳힌 사실은 대리인도 못 바꾼다.

### (2) ★★★ 「트랩은 무엇이든 돌려줄 수 있다」로 외운다

**보통 대상 앞에서만** 그렇다(보통 열 `0 / 8`). 설정 불가·확장 불가가 끼면 **12 / 24** 가 던졌다.

### (3) ★★★ `Map`·`Set`·`Date` 를 빈 `handler` 로 감싸면 투명하다고 믿는다

**`incompatible receiver`** — 내부 슬롯은 대리인이 못 빌린다(동작 (3)). 함수를 대상에 `bind` 해서 돌려준다.

### (4) ★★ `set` 트랩의 `false` 로 쓰기를 「막았다」고 믿는다

**비엄격에서는 조용히 지나간다**(`no exception`, 동작 (2)). 막았다는 신호가 필요하면 트랩에서 **직접 던진다.**

### (5) ★★ `x instanceof Proxy` 로 Proxy 인지 가린다

**`TypeError`** — `Proxy.prototype` 이 없다(동작 (4)). 표준 판별 수단이 없다.

### (6) ★★ 취소한 Proxy 는 `typeof` 도 안 된다고 믿는다

**`typeof` 는 된다**(`object`/`function`) — 그런데 `Array.isArray` 는 **던진다**(동작 (4)). 연산마다 대상에 닿느냐가 다르다.

### (7) ★ 「`Proxy` 는 느리다」를 근거로 쓴다

**이 문서는 재지 않았다.**

## 구현 세부사항 대 언어 보장

### 명세 보장(ECMA-262)

- ★★★ **불변식 검사** — 내부 메서드가 트랩 결과를 받은 **뒤** 대상의 상태(`[[GetOwnProperty]]` · `[[IsExtensible]]` · `[[GetPrototypeOf]]`)와 대조하고, 어긋나면 **`TypeError`**. 24칸의 **던진 자리**가 전부 여기서 나온다(세 판 같음).
- ★★ **트랩이 없으면 대상의 내부 메서드로 그대로** · `[[Call]]`·`[[Construct]]` 는 **대상이 그것을 가질 때만** 단다(그래서 `typeof`).
- ★★ **`false` 보고를 예외로 바꾸는 것은 호출한 쪽**(엄격 대입 · `Object.defineProperty`) — Proxy 의 불변식 검사와 **다른 자리**다.
- ★★ **내부 슬롯 검사**(`RequireInternalSlot`)는 Proxy 를 뚫지 않는다 · **`Array.isArray` 는 뚫는다**(동작 (4)).
- ★ `revoke()` 는 두 칸을 `null` 로 비우고, 두 번째 호출은 아무것도 안 한다.

### 구현(V8) · 이 판의 관찰

- ★★ **문구 전부** — `'get' on proxy: … (expected 'real' but got 'lie')` · `trap returned falsish …` · `incompatible receiver #<Map>` · `Cannot perform 'get' on a proxy that has been revoked`. **세 판(V8 10.2 · 11.3 · Chrome 151)이 한 글자도 같았다** — 그래도 보장이 아니다(규칙 3 — 「여러 버전에서 같았다」).
- ★ `defineProperty` 위반 문구에 **공백 두 칸**(`'x'  that`)이 있다 — 문구를 대조에 쓰면 이런 것까지 걸린다.

### 그래서 이렇게 적으면 틀린다

- ✗ 「Proxy 트랩은 대상과 상관없이 아무 값이나 돌려줄 수 있다」 → ○ 「**대상이 설정 불가·확장 불가로 굳힌 사실**과 어긋나면 `TypeError` — 24칸 중 12」
- ✗ 「빈 `handler` 의 Proxy 는 대상과 완전히 같다」 → ○ 「**내부 슬롯·프라이빗 이름**을 쓰는 메서드는 `this` 가 Proxy 면 `TypeError`」
- ✗ 「`set` 트랩이 `false` 면 대입이 에러가 난다」 → ○ 「**엄격 모드에서만**」

## 언제 쓰고 언제 안 쓰나

- **로그·검증·기본값 끼우기** — 보통 객체 앞에서는 자유롭다. 넘길 때는 **`Reflect.<같은 이름>(...arguments)`** 로 넘기면 맨 대상과 구분이 안 된다(`0 / 24` — 46번).
- **동결·봉인 객체를 감쌀 때** — 트랩이 **대상과 같은 답**을 하게 둔다. 바꿔 보여야 하면 **동결하지 않은 사본**을 대상으로 쓴다.
- **내장 객체(`Map`·`Date`)나 프라이빗 필드가 있는 인스턴스** — 메서드를 대상에 `bind` 하는 `get` 트랩이 필요하다(대신 메서드 호출은 트랩을 안 탄다).
- ★ **안 쓰는 자리** — `instanceof Proxy` 판별 · 「쓰기 금지」를 `false` 하나로 믿기(비엄격).

## 핵심 문장

1. ★★★ 트랩은 **대상이 굳힌 사실과 대조**된다 — 거짓말하는 트랩 **`12 / 24`** 가 던졌고, **보통 대상 열은 `0 / 8`**, 설정 불가+쓰기 불가 **`7 / 8`**, `preventExtensions` **`5 / 8`**.
2. ★★★ `Reflect` 로 넘기는 트랩은 **맨 대상과 답이 다른 칸 `0 / 24`** — 던진 1칸은 맨 대상도 던진다.
3. ★★ 트랩의 **`false`** 는 보고일 뿐 — **엄격에서만** `TypeError`, 비엄격은 조용히 지나간다.
4. ★★ **내부 슬롯·프라이빗 이름**은 Proxy 를 뚫지 않는다 — `Map.prototype.get` 이 `incompatible receiver`. 겉모습(`[object Map]` · `Array.isArray` `true` · `typeof`)은 대상을 따른다.
5. ★ `revoke()` 뒤 대부분 `TypeError` — 그러나 `typeof` 는 되고 `Array.isArray` 는 던진다. 세 판이 **문구까지** 같았다.

## 관련 자료

- [ECMA-262 — Proxy Object Internal Methods](https://tc39.es/ecma262/multipage/ordinary-and-exotic-objects-behaviours.html) · [ECMA-262 — Reflection](https://tc39.es/ecma262/multipage/reflection.html)
- [14 — 프로퍼티 디스크립터와 동결](../14-property-descriptors-and-freezing/2-summary.md) — ★ **경계**: 플래그 셋과 동결·봉인이 **무엇을 막나**까지는 거기. 여기는 **그 막힌 사실을 Proxy 가 부정하면**부터.
- [15 — 프로토타입 체인](../15-prototype-chain/2-summary.md) — Proxy 를 로그 도구로 쓴 편. [46 — `Reflect`](../46-reflect/2-summary.md) — `Reflect` 와 트랩의 1:1 · `receiver` · 이 문서 `[2]` 줄의 인용.
- [Python 29 — 클래스와 속성 조회](../../../python/syntax/29-classes-and-attribute-lookup/2-summary.md) — `__getattr__`·`__getattribute__`(가로채는 자리가 클래스에 있다).

## 용어 풀이

- **`Proxy`** — 대상 객체를 감싸 내부 동작을 트랩으로 가로채는 별도 객체(ES2015).
- **트랩(trap)** — `handler` 의 함수. 13개(`get`·`set`·`has`·`deleteProperty`·`defineProperty`·`getOwnPropertyDescriptor`·`ownKeys`·`getPrototypeOf`·`setPrototypeOf`·`isExtensible`·`preventExtensions`·`apply`·`construct`).
- **불변식(invariant)** — 트랩 결과가 어겨서는 안 되는 조건. 대상이 **설정 불가**·**확장 불가**로 굳힌 사실과 어긋나면 `TypeError`.
- **내부 슬롯(internal slot)** — 객체 안의 숨은 칸(`[[MapData]]`·`[[DateValue]]`). 프로퍼티가 아니라서 트랩으로 안 닿는다.
- **`Proxy.revocable`** — 취소 함수가 딸린 Proxy 를 만든다. 취소 뒤 대부분의 동작이 `TypeError`.
- **투명(transparent)** — 트랩이 없거나 `Reflect` 로 그대로 넘겨서 맨 대상과 구분이 안 되는 상태(이 문서의 말).

## 더 들어가면

- **`apply`·`construct`·`setPrototypeOf`·`isExtensible`·`preventExtensions` 의 불변식** — 격자에 넣지 않았다. 명세 note 에 각각 있다(예: `[[Construct]]` 의 결과는 **객체**여야 한다).
- **`receiver` 인자** — `get`/`set` 트랩의 셋째·넷째 인자. 46번 동작 (3)이 정본이다.
- **막 쓰는 Proxy 의 비용·엔진 최적화** — 재지 않았다.
