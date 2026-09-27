# js/syntax/51 — 명시적 자원 관리 `using`: 「Chrome 151 만 다 있고(`11 / 21`) · 역순으로 모든 길에서 치우며 · 치우다 던지면 본문 오류는 `.suppressed` 로 들어간다」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 출력은 **node v20.19.6 · v18.19.1 · Google Chrome 151 · tsc 7.0.2** · x86-64 Linux 에서 실제로 돌려 얻은 것이고, 블록은 **전부 캡처 파일에서 조립**했다.
> ★★★ **`using` 의 동작을 확인한 엔진은 Chrome 151 하나다** — node 18·20 에는 문법이 없어, node 쪽 답은 **손으로 쓴 코드(7번)와 tsc 방출물(8번)** 로 다시 물은 것이다.
>
> **이 파일이 인용하는 출력을 낸 소스** — 전문은 [1-question.md](1-question.md) 의 같은 번호 문항에 있다.
> `js48b-51a-support.js` + `.sh`(1번 · 9번) · `js48b-51b-positions.js`(2번) · `js48b-51c-order.js`(3번 · 10번) · `js48b-51d-errors.js`(4번 · 11번) · `js48b-51e-stack.js`(5번 — 소스는 [2-summary.md](2-summary.md) 동작 (5)) · `js48b-51f-await-using.js`(6번) · `js48b-51g-by-hand.js`(7번) · `in51h.ts` + `tsconfig.json` + `js48b-51h-tsc.sh`(8번).

## 정답

### 1. Chrome 151 은 **일곱 칸 다 yes**, node 18·20 은 **`Symbol.dispose`·`Symbol.asyncDispose` 만 yes** · **`supported cells: 11 / 21`** · `#` 줄 — node 는 `Symbol(nodejs.dispose)` · `nodejs.dispose`, Chrome 은 `Symbol(Symbol.dispose)` · `undefined` ★★★

**출력**

```text
===== ./js48b-51a-support.sh (exit=0) =====
                                     node18                 node20                 Chrome 151
using declaration in a block         no                     no                     yes
await using in an async function     no                     no                     yes
Symbol.dispose                       yes                    yes                    yes
Symbol.asyncDispose                  yes                    yes                    yes
DisposableStack                      no                     no                     yes
AsyncDisposableStack                 no                     no                     yes
SuppressedError                      no                     no                     yes
# String(Symbol.dispose)             Symbol(nodejs.dispose) Symbol(nodejs.dispose) Symbol(Symbol.dispose)
# Symbol.keyFor(Symbol.dispose)      nodejs.dispose         nodejs.dispose         undefined

supported cells: 11 / 21
```

**왜 그런가**

- ★★★ node 18·20 은 **문법이 없다** — `new Function("{ using x = null; }")` 이 `SyntaxError` 라 `no`. 그런데 `Symbol.dispose` 는 **node 가 `Symbol.for("nodejs.dispose")` 로 만들어 둔 것**이 있어 `yes` — `Symbol.keyFor` 가 키를 돌려주는 것이 **등록된 심볼**이라는 증거다(9번).
- ★★ 두 node 판은 **한 칸도 안 갈렸다.**

### 2. Chrome 151 — **`parsed` 9줄**(함수 몸통 · 블록 · 스크립트 최상위의 블록 · `for…of` · `for(;;)` · `case` 안의 블록 · 바인딩 둘 · `let using` · async 안 `await using`) · 거절 6줄 · node 20 — **`let using = 1; return using;` 한 줄만 `parsed`** ★★

**출력**

```text
===== ./js48b-browser.sh js48b-51b-positions.js (exit=0) =====
  function body     { using x = R51; }                            parsed
  function body     using x = R51;                                parsed
  script top level  using x = R51;                                SyntaxError 「Unexpected identifier 'x'」
  script top level  { using x = R51; }                            parsed
  function body     for (using x of [R51]) {}                     parsed
  function body     for (using x = R51; false; ) {}               parsed
  function body     for (using x in { a: 1 }) {}                  SyntaxError 「Invalid 'using' in for-in loop」
  function body     switch (1) { case 1: using x = R51; }         SyntaxError 「Unexpected identifier 'x'」
  function body     switch (1) { case 1: { using x = R51; } }     parsed
  function body     using x;                                      SyntaxError 「Missing initializer in using declaration」
  function body     using { a } = R51;                            SyntaxError 「Unexpected token '{'」
  function body     using x = R51, y = R51;                       parsed
  function body     let using = 1; return using;                  parsed
  function body     return async () => { await using x = R51; };  parsed
  function body     await using x = R51;                          SyntaxError 「await is only valid in async functions and the top level bodies of modules」
```

```text
===== node20 js48b-51b-positions.js (exit=0) =====
  function body     { using x = R51; }                            SyntaxError 「Unexpected identifier 'x'」
  function body     using x = R51;                                SyntaxError 「Unexpected identifier 'x'」
  script top level  using x = R51;                                SyntaxError 「Unexpected identifier 'x'」
  script top level  { using x = R51; }                            SyntaxError 「Unexpected identifier 'x'」
  function body     for (using x of [R51]) {}                     SyntaxError 「Unexpected identifier 'x'」
  function body     for (using x = R51; false; ) {}               SyntaxError 「Unexpected identifier 'x'」
  function body     for (using x in { a: 1 }) {}                  SyntaxError 「Unexpected identifier 'x'」
  function body     switch (1) { case 1: using x = R51; }         SyntaxError 「Unexpected identifier 'x'」
  function body     switch (1) { case 1: { using x = R51; } }     SyntaxError 「Unexpected identifier 'x'」
  function body     using x;                                      SyntaxError 「Unexpected identifier 'x'」
  function body     using { a } = R51;                            SyntaxError 「Unexpected token '{'」
  function body     using x = R51, y = R51;                       SyntaxError 「Unexpected identifier 'x'」
  function body     let using = 1; return using;                  parsed
  function body     return async () => { await using x = R51; };  SyntaxError 「Unexpected identifier 'x'」
  function body     await using x = R51;                          SyntaxError 「await is only valid in async functions and the top level bodies of modules」
```

**왜 그런가**

- ★★★ **스크립트 최상위**(명세 16.1.1)와 **`case` 절 바로 밑**(14.12.1)은 명세의 Syntax Error — 문구는 둘 다 `Unexpected identifier 'x'` 라 **「`using` 을 모르는 엔진」 과 글자가 같다.** 블록으로 감싸면 `parsed`.
- ★★ `for…in` · 초기자 없음 · 구조 분해 · async 밖 `await using` 은 **문구가 각각 다르다**(V8). `using` 은 예약어가 아니어서 `let using = 1` 은 **세 판 다** 된다.
- ★ node 18 은 같은 자리에서 **`Unexpected identifier`**(식별자 없이)를 냈다 — 2-summary 동작 (2).

### 3. **`[1]` `dispose c · b · a` · `[2]` `dispose b` 가 안쪽 블록 끝, 이어 `make c` · `[3]`·`[4]` 둘 다 `dispose a` 뒤 원래 결과 · `[5]` `dispose a` 가 `finally` 보다 먼저 · `[6]` 반복마다 · `[7]` `dispose c` 만 · `[8]` `TypeError` 전에 `dispose a` · `[9]` 처음 메서드 · `[10]` `TypeError 「Assignment to using variable.」`** ★★★

**출력**

```text
===== ./js48b-browser.sh js48b-51c-order.js (exit=0) =====
[1] one declaration, three bindings
    make a · make b · make c · body · dispose c · dispose b · dispose a  ->  returned undefined
[2] three declarations, the middle one in an inner block
    make a · make b · inner body · dispose b · make c · outer body · dispose c · dispose a  ->  returned undefined
[3] leaving by return
    make a · before return · dispose a  ->  returned r
[4] leaving by throw
    make a · dispose a  ->  threw Error 「from the body」
[5] inside try, with a finally
    make a · try body · dispose a · finally  ->  returned undefined
[6] loop: for (using x of ...)
    make p · make q · loop body · dispose p · loop body · dispose q  ->  returned undefined
[7] null and undefined as the value
    make c · body · dispose c  ->  returned undefined
[8] a value without Symbol.dispose
    make a · before the second declaration · dispose a  ->  threw TypeError 「Symbol(Symbol.dispose) is not a function」
[9] replacing the method after the declaration
    body · the method present at the declaration  ->  returned undefined
[10] assigning to the binding
    make a · make other · dispose a  ->  threw TypeError 「Assignment to using variable.」
```

**왜 그런가**

- ★★★ 명세 `DisposeResources` 는 장부를 「**in reverse List order**」 로 읽고, 장부는 **블록마다** 있다(`[2]`). 블록을 떠나는 완료가 무엇이든 그 완료를 **들고** 해제한 뒤 그대로 내보낸다(`[3]`·`[4]`) — `try` 블록 안의 `using` 은 그 블록의 끝에 속하니 `finally` 보다 먼저다(`[5]`).
- ★★ `null`·`undefined` 는 장부에 **안 적힌다**(`[7]`) · 객체인데 메서드가 없으면 **그 선언에서** `TypeError` — 이미 적힌 것은 치운다(`[8]`) · 메서드는 선언 때 **레코드에 담긴다**(`[9]`).
- ★ `[6]` 의 `make p · make q` 가 먼저인 것은 **배열 리터럴** 때문이다.

### 4. **`[1]` `SuppressedError` — `.error` = `dispose a` · `.suppressed` = `body`** · **`[2]` `Error 「dispose a」` 그대로** · **`[3]` 두 겹 — 겉 `.error` = `dispose a`, 안쪽 `SuppressedError(.error = dispose b, .suppressed = body)`** · **`[4]` `log: dispose a` 뒤 `Error 「dispose b」`** · `[5]` `.error x · .suppressed y · .message m` · `[6]` `message error suppressed` ★★★

**출력**

```text
===== ./js48b-browser.sh js48b-51d-errors.js (exit=0) =====
[1] the body throws, the one resource throws while disposing
    SuppressedError 「An error was suppressed during disposal」
      .error:
        Error 「dispose a」
      .suppressed:
        Error 「body」
[2] the body finishes, the one resource throws while disposing
    Error 「dispose a」
[3] the body throws, two resources throw while disposing
    SuppressedError 「An error was suppressed during disposal」
      .error:
        Error 「dispose a」
      .suppressed:
        SuppressedError 「An error was suppressed during disposal」
          .error:
            Error 「dispose b」
          .suppressed:
            Error 「body」
[4] the body finishes, b throws while disposing, a does not
    log: dispose a
    Error 「dispose b」
[5] new SuppressedError(x, y, 'm')
    .error x · .suppressed y · .message m · own keys message error suppressed · instanceof Error true
[6] own keys of the error that [1] threw
    message error suppressed · Object.hasOwn(e, 'message') true
```

**왜 그런가**

- ★★★ 앞의 완료가 throw 인데 해제가 또 던지면 명세가 **새 `SuppressedError`** 를 만들어 `"error"` 에 **새 오류**, `"suppressed"` 에 **앞의 것**을 넣는다. 역순이므로 `b` 가 먼저 한 겹, `a` 가 그 위에 한 겹(`[3]`) — **본문 오류는 맨 안쪽**이다.
- ★★ 본문이 정상이면 **앞의 throw 가 없으니** 감싸지 않는다(`[2]`) · 한 해제가 던져도 **나머지를 계속** 치운다(`[4]`).
- ★★ `[6]` 의 `message` 는 **V8 이 더한 것** — 이 문서가 읽은 명세 단계에는 `message` 가 없다(2-summary 동작 (4)).

### 5. `use(v)` — **값**을 받아 그 `[Symbol.dispose]` 를 적는다 · `adopt(v, fn)` — **아무 값 + 함수**, 해제 때 `fn(v)` · `defer(fn)` — **함수만** · 넣은 **역순**(`defer c · adopt b · dispose a`) · 두 번째 `dispose()` 는 조용히 `undefined` · 닫힌 스택에 `use` 는 **`ReferenceError`** · `move()` 뒤 원래 스택은 **이미 disposed** 라 아무것도 안 치운다 ★★

**출력**

```text
===== ./js48b-browser.sh js48b-51e-stack.js (exit=0) =====
[1] use · adopt · defer, then dispose()
  s.use(res('a')).name                          ok a
  s.adopt('b', (v) => log.push('adopt ' + v))   ok b
  s.defer(() => log.push('defer c'))            ok undefined
  s.use(null)                                   ok null
  s.use({})                                     TypeError 「Symbol(Symbol.dispose) is not a function」
  s.disposed                                    ok false
  s.dispose()                                   ok undefined
    log: defer c · adopt b · dispose a
  s.disposed                                    ok true
  s.dispose()   (again)                         ok undefined
  s.use(res('d'))   (after dispose)             ReferenceError 「Cannot call DisposableStack.prototype.use on an already-disposed DisposableStack」
[2] move() hands the steps to a new stack
  t.disposed · u.disposed                       ok true · false
  t.dispose()                                   ok undefined
    log after t.dispose(): []
  u.dispose()                                   ok undefined
    log after u.dispose(): [dispose e]
[3] a stack held by using
    log: block body · defer g · dispose f
```

- ★★ 명세 27.3 — 「added in the order they are initialized, and are disposed in reverse order」 · `use`·`move` 는 disposed 면 `ReferenceError`. `move()` 는 **장부를 새 스택으로 옮기고** 원래 것을 disposed 로 만든다(`t.disposed · u.disposed` → `true · false`).

### 6. `[1]` **b 를 끝까지 기다린 뒤 a** · `[2]` `sync dispose a` 뒤 **`tick 2` 다음** · **`[3]` `tick 2` 뒤** · **`[4]` `tick 1` 뒤** · `[5]` **`TypeError 「Symbol(Symbol.dispose) is not a function」`** ★★

**출력**

```text
===== ./js48b-browser.sh js48b-51f-await-using.js (exit=0) =====
[1] two async resources
    body · start async dispose b · tick 1 · end async dispose b · tick 2 · start async dispose a · tick 3 · end async dispose a · tick 4 · after the block
[2] a value with only Symbol.dispose
    body · sync dispose a · tick 1 · tick 2 · after the block · tick 3
[3] null as the value
    body · tick 1 · tick 2 · after the block · tick 3
[4] no await using at all
    body · tick 1 · after the block · tick 2 · tick 3
[5] plain using holding an object that has only Symbol.asyncDispose
    TypeError 「Symbol(Symbol.dispose) is not a function」 · after the block
```

**왜 그런가**

- ★★★ `await using` 은 해제마다 결과를 **Await** 한다 — 겹치지 않고 하나씩, 역순(`[1]`).
- ★★★ **`null` 이어도 한 틱**(`[3]` 대 `[4]`) — 명세 NOTE 「null·undefined 여도 **여전히 Await** 하도록 기록한다」. `Symbol.dispose` 만 있는 값도 같은 한 틱을 치른다(`[2]`).
- ★★ 동기 `using` 은 `Symbol.asyncDispose` 를 **찾지 않는다**(`[5]`).

### 7. `[2]` — `finally` 안의 해제가 던진 오류가 **`try` 의 완료를 바꿔 쥐어** 본문 오류가 **흔적 없이** 사라진다 — 32번 동작 (2) `[4]` 와 같은 칸 · `[3]` — node 20 은 **`SuppressedByHand`**, Chrome 151 은 **`SuppressedError`** — Chrome 에만 진짜 생성자가 있어 소스의 `typeof SuppressedError === "function"` 분기가 갈렸다 ★★

**출력**

```text
===== node20 js48b-51g-by-hand.js (exit=0) =====
[1] three resources, one try/finally each
    body · dispose c · dispose b · dispose a
[2] the body throws, the resource throws while disposing -- plain try/finally
    caught Error 「dispose r」
[3] the same, keeping both errors by hand
    caught SuppressedByHand 「kept both」 · .error dispose r · .suppressed body
```

```text
===== ./js48b-browser.sh js48b-51g-by-hand.js (exit=0) =====
[1] three resources, one try/finally each
    body · dispose c · dispose b · dispose a
[2] the body throws, the resource throws while disposing -- plain try/finally
    caught Error 「dispose r」
[3] the same, keeping both errors by hand
    caught SuppressedError 「kept both」 · .error dispose r · .suppressed body
```

- ★★ `[1]` 의 역순은 중첩 `try`/`finally` 로도 나온다 — `using` 이 **보태는 것**은 순서가 아니라 **두 오류를 다 남기는 것**과 **한 겹씩 쓰지 않아도 되는 것**이다.

### 8. `using ` **0줄** · 헬퍼 **`__addDisposableResource`·`__disposeResources`** · node 18·20 — `[2]` **`constructor Error · name SuppressedError`**, `[3]` `typeof SuppressedError undefined · … Symbol(nodejs.dispose)` · Chrome 151 — **`constructor SuppressedError`**, `function · Symbol(Symbol.dispose)` · `esnext` 방출물은 `using ` **2줄** — node 18 `SyntaxError 「Unexpected identifier」` · node 20 `「Unexpected identifier 'a'」` ★★

**출력**

```text
===== ./js48b-51h-tsc.sh (exit=0) =====
tsc Version 7.0.2
tsc -p .   (target es2022) exit=0
  lines of out/in51h.js that contain 'using ': 0
  helpers defined: __addDisposableResource __disposeResources 
  TypeError messages in the helpers: "Object expected." "Symbol.asyncDispose is not defined." "Symbol.dispose is not defined." "Object not disposable." 
--- out/in51h.js after the two helpers
const log = [];
const res = (name, throws = false) => ({
    [Symbol.dispose]() { log.push("dispose " + name); if (throws)
        throw new Error("dispose " + name); },
});
function order() {
    const env_2 = { stack: [], error: void 0, hasError: false };
    try {
        const a = __addDisposableResource(env_2, res("a"), false), b = __addDisposableResource(env_2, res("b"), false), c = __addDisposableResource(env_2, res("c"), false);
        log.push("body");
    }
    catch (e_2) {
        env_2.error = e_2;
        env_2.hasError = true;
    }
    finally {
        __disposeResources(env_2);
    }
}
order();
console.log("[1] " + log.join(" · "));
try {
    const env_1 = { stack: [], error: void 0, hasError: false };
    try {
        const r = __addDisposableResource(env_1, res("r", true), false);
        throw new Error("body");
    }
    catch (e_1) {
        env_1.error = e_1;
        env_1.hasError = true;
    }
    finally {
        __disposeResources(env_1);
    }
}
catch (e) {
    console.log("[2] caught constructor " + e.constructor.name + " · name " + e.name + " · 「" + e.message + "」" +
        " · .error " + e.error?.message + " · .suppressed " + e.suppressed?.message);
}
console.log("[3] typeof SuppressedError " + typeof SuppressedError + " · String(Symbol.dispose) " + String(Symbol.dispose));
--- node18 out/in51h.js
[1] body · dispose c · dispose b · dispose a
[2] caught constructor Error · name SuppressedError · 「An error was suppressed during disposal.」 · .error dispose r · .suppressed body
[3] typeof SuppressedError undefined · String(Symbol.dispose) Symbol(nodejs.dispose)
--- node20 out/in51h.js
[1] body · dispose c · dispose b · dispose a
[2] caught constructor Error · name SuppressedError · 「An error was suppressed during disposal.」 · .error dispose r · .suppressed body
[3] typeof SuppressedError undefined · String(Symbol.dispose) Symbol(nodejs.dispose)
--- Chrome 151 out/in51h.js
[1] body · dispose c · dispose b · dispose a
[2] caught constructor SuppressedError · name SuppressedError · 「An error was suppressed during disposal.」 · .error dispose r · .suppressed body
[3] typeof SuppressedError function · String(Symbol.dispose) Symbol(Symbol.dispose)

tsc -p . --target esnext --outDir out-esnext   exit=0
  lines of out-esnext/in51h.js that contain 'using ': 2
  node18 parses out-esnext/in51h.js: SyntaxError 「Unexpected identifier」
  node20 parses out-esnext/in51h.js: SyntaxError 「Unexpected identifier 'a'」
```

**왜 그런가**

- ★★★ `target es2022` 는 `using` 을 모르는 판을 겨냥하므로 tsc 가 **`try`/`catch`/`finally` + 장부 객체(`env.stack`)** 로 낮춘다 — 해제는 `stack.pop()` 이라 역순이고, 두 오류를 다 남긴다.
- ★★★ 헬퍼는 `SuppressedError` 가 없으면 **`new Error(message)` 에 `name` 만** 단다 — 그래서 node 에서는 `constructor Error`. Chrome 에서는 같은 방출물이 **진짜 생성자**를 쓴다.
- ★★ `target esnext` 는 `using` 을 **그대로 둔다** — 실행 책임이 런타임으로 넘어가고, node 18·20 은 파싱부터 실패한다.

### 9. **문법(파서)과 심볼(전역 값)은 따로 온다** — node 는 심볼만 가지고 있다 · 명세의 `Symbol.dispose` 와 **같은 것이 아니다**: `Symbol.keyFor(Symbol.dispose)` 가 node 에서 **`nodejs.dispose`**(등록된 심볼), Chrome 에서 **`undefined`**(well-known symbol 은 등록되지 않는다) · 기능 검사는 **`new Function("{ using x = null; }")` 같은 파싱**으로 한다 ★★★

- ★★ 심볼로 검사하면 node 18·20 에서 **거짓 양성**이 난다(1번의 `Symbol.dispose yes` 대 `using … no`). node 가 그 심볼을 무엇에 쓰는지는 이 문서가 **확인하지 않았다.**

### 10. **값의 해제는 `using` 의 규칙**(반복마다 `[Symbol.dispose]` — 3번 `[6]`), **이터레이터의 닫기는 19·20·40번의 규칙**(`return()` 은 소비자가 떠날 때 부르고, 무엇을 할지는 이터레이터가 정한다) · 47번과 정반대 — `FinalizationRegistry` 는 **「언제」 가 명세 밖(may)** 이었고, `using` 은 **블록 끝이라는 문법상의 순간**에 **반드시** 부른다 ★★

- ★ 둘 다 「떠나는 모든 길」 에서 불린다는 점은 같다 — 3번 `[3]`·`[4]` 와 40번의 `break`·`return`·`throw` 세 줄.

### 11. Python — 정리 중 예외가 **`__context__` 사슬**로 이어진다(묶음이 아니다 — Python 28) · Java — 주 예외에 **`addSuppressed`** 로 매단다(주인공은 **본문 예외** — Java 26) · JS — **새 `SuppressedError` 가 겉**이 되고 본문 오류는 **`.suppressed` 안**으로 들어간다(4번) ★★

- ★★ 셋 다 「둘 다 던졌을 때만」 둘을 함께 남기고, 순서는 셋 다 **역순**이다. **모양이 다르다** — Java 는 본문 예외를 꺼내면 첨부가 따라오고, JS 는 겉을 벗겨야 본문이 나온다(이 비교는 각 편의 결과를 견준 해석이다 — 세 갈래를 한 탐침으로 돌리지는 않았다).

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js48b-51a-support.js` + `.sh` | ★★★ 21칸 · 「`11 / 21`」 · node 심볼의 정체 | node18 · node20 · Chrome 151 |
| `js48b-51b-positions.js` · `js48b-51b-module.mjs` | ★★ 선언 자리 15곳 · 모듈 최상위 | Chrome 151(고전 · 모듈) · node20 · node18 |
| `js48b-51c-order.js` | ★★★ 역순 · 떠나는 길 · 루프 · `null` · 메서드 읽는 시점 | Chrome 151 |
| `js48b-51d-errors.js` | ★★★ `SuppressedError` 의 중첩 · `message` 의 출처 | Chrome 151 |
| `js48b-51e-stack.js` | ★★ `DisposableStack` 의 순서 · `ReferenceError` · `move()` | Chrome 151 |
| `js48b-51f-await-using.js` | ★★ 해제 사이의 틱 · `null` 의 한 틱 | Chrome 151 |
| `js48b-51g-by-hand.js` | ★★ 손 코드의 역순 · 본문 오류 소실 | node20 · node18(같음) · Chrome 151(`[3]` 이름만 다름) |
| `in51h.ts` + `tsconfig.json` + `js48b-51h-tsc.sh` | ★★ tsc 7.0.2 의 방출 · 방출물의 세 판 실행 | tsc 7.0.2 → node18 · node20 · Chrome 151 |

- ★ 캡처를 두 번 돌려 정규화 대조했다 — 실행마다 바뀌는 칸이 **없었다**(머리말 흔들리는 칸 표).

**구현 의존 항목 — 판이 오르면 다시 돌릴 것** — ★★★ **1번 격자 전체**(node 가 문법을 받는 판이 오면 칸이 바뀐다 · 그때 `Symbol.keyFor(Symbol.dispose)` 도) · 2번 · 3번의 **문구** · 4번 `[6]` 의 `message` · **8번의 헬퍼 모양**(tsc 판). 순서와 중첩 모양(3번 · 4번 · 6번)은 명세 칸이라 판이 올라도 같아야 한다.
