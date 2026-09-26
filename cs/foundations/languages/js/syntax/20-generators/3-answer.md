# js/syntax/20 — 제너레이터: 「`next(값)` 은 대답을 넣고 다음 질문을 받는 무전이다 — 첫 무전은 아무도 안 듣는다」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **node v20.19.6**(기본 판) · **node v18.19.1**(대조) · x86-64 Linux 에서 실제로 돌려 얻은 것이고,
> 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 하나도 없다). 브라우저는 판별 블록 말고는 **안 돌렸다.**
>
> ★★ **예외는 `이름 「메시지」` 꼴로만 찍었다** — 스택트레이스에는 절대 경로가 박혀 재현이 안 된다.
> ★★★ **이 주제는 두 판이 갈린 블록을 하나 갖고 있다**(`js20b-20f-errors.js`) — 6번 답에 v18 판을 나란히 싣는다.
> ★ **표준 출력과 표준 오류를 한 블록에도 안 섞었다** — 예외는 전부 `catch` 로 받아 표준 출력에 찍었다.
>
> **이 파일이 인용하는 출력을 낸 소스** — 전문은 [1-question.md](1-question.md) 의 같은 번호 문항에 있다(8·10번의 소스는 [2-summary.md](2-summary.md) 의 동작 (1)·(8)).
> `js20b-20b-two-way.js`(1번) · `js20b-20c-return-finally.js`(2번) · `js20b-20d-throw.js`(3번) · `js20b-20e-delegate.js`(4번) · `js20b-20g-grid.js`(5번) ·
> `js20b-20f-errors.js`(6번) · `js20b-20a-start-and-end.js`(8·9번) · `js20b-20h-lazy-seq.js`(10번) · `js20b-vdiff.sh`(실행 검증).

## 정답

### 1. 네 번의 `next(값)` — **`"A"` 는 어느 로그에도 없다 · 값은 한 박자 늦게 지난번 `yield` 에 닿는다** ★★★

**출력**

```text
===== node20 js20b-20b-two-way.js (exit=0) =====
[1] next('A'), next('B'), next('C'), next('D')
  next("A")  ->  {"value":"out-1","done":false}           body: body starts (arguments.length 0)
  next("B")  ->  {"value":"out-2","done":false}           body: yield#1 evaluated to "B"
  next("C")  ->  {"value":"done with [\"B\",\"C\"]","done":true} body: yield#2 evaluated to "C"
  next("D")  ->  {"value":"<undefined>","done":true}      body: (no log)

[2] a running total -- priming next() first, then values
  next()    {"value":0,"done":false}
  next(10)  {"value":10,"done":false}
  next(5)   {"value":15,"done":false}
  next(1)   {"value":16,"done":false}

[3] the same, without priming -- next(10) first
  next(10)  {"value":0,"done":false}
  next(5)   {"value":5,"done":false}
  next(1)   {"value":6,"done":false}
```

**왜 그런가**

- ★★★ **`"A"` 는 네 줄 어디에도 없다.** 첫 `next("A")` 가 재개하는 것은 **본문의 시작**이지 어떤 `yield` 가 아니다 — 받을 칸이 없다.
  `arguments.length 0` 이 「제너레이터 함수의 인자로 들어간 것도 아니다」를 같이 보여 준다.
- ★★★ **`"B"` 는 `out-2` 를 요청한 호출의 인자인데 `yield#1` 의 값이 됐다.** `yield` 식의 값은 **그 `yield` 를 재개시킨 `next` 의 인자**다 — 바깥에서 보면 한 박자 늦다.
- ★★ `next("C")` 가 `return` 까지 가서 `done: true` 와 `["B","C"]` 를 준다. `next("D")` 는 끝난 뒤라 본문이 없고 `D` 도 사라진다.
- ★★★ **`[2]` 와 `[3]` 은 같은 값 목록인데 `10·15·16` 대 `0·5·6`** — 프라이밍 없이 시작한 `[3]` 은 **첫 `10` 을 잃었다.** 에러가 아니라 **합계가 틀리는** 모양으로 나온다.

### 2. `return('R')` — **세 상태 모두 `{R, done: true}` 인데 `finally` 는 멈춘 상태에서만 · `finally` 가 `yield` 하면 `done: false`** ★★★

**출력**

```text
===== node20 js20b-20c-return-finally.js (exit=0) =====
[1] return('R') in three states
  before the first next: return('R')  {"value":"R","done":true}          body: (no log)
    then next()                       {"value":"<undefined>","done":true} body: (no log)
  paused at yield 1: return('R')      {"value":"R","done":true}          body: finally
    then next()                       {"value":"<undefined>","done":true} body: (no log)
  after completion: return('R')       {"value":"R","done":true}          body: (no log)

[2] a finally block that itself yields
  return('R')                         {"value":"from finally","done":false} body: finally starts
  next()                              {"value":"R","done":true}          body: finally ends
  next()                              {"value":"<undefined>","done":true} body: (no log)

[3] a finally block with its own return
  return('R')                         {"value":"F","done":true}          body: finally returns 'F'

[4] break in for-of over withFinally()
  after the loop                      "-"                                body: try / loop got 1 / finally
```

**왜 그런가**

- ★★★ **`[1]` 결과는 셋이 같고 본문 로그만 갈린다** — 시작 전·끝난 뒤는 `(no log)`, `yield 1` 에서 멈춘 것만 `finally`.
  시작 전이면 `GeneratorResumeAbrupt` 가 "If state is suspended-start, then Set gen.[[GeneratorState]] to completed." 로 **본문 없이 끝낸다** — `try` 에 들어간 적이 없으니 `finally` 도 없다.
  끝난 것에는 "If abruptCompletion is a return completion, then Return CreateIteratorResultObject(abruptCompletion.[[Value]], true)." — **준 `R` 을 그대로 돌려준다.**
- ★★★ **`[2]` `done` 이 `false` → `true` → `true`.** `return()` 은 **멈춘 자리에서 `return "R"` 을 일으킬 뿐**이고, 그 `return` 이 `finally` 를 지나다 `yield "from finally"` 에서 **다시 멈췄다.**
  `R` 은 미뤄졌다가 다음 `next()` 에서 `finally ends` 뒤에 나온다.
- ★★ **`[3]` `F`** — `finally` 의 `return` 이 앞선 `return` 을 덮는다. 평범한 함수와 같은 규칙이다.
- ★★ **`[4]` `try / loop got 1 / finally`** — 19번의 `break` → `return()` 이 제너레이터 안에서는 `finally` 로 보인다.

### 3. `throw()` — **감싸 받으면 다음 `yield` 의 값을 돌려주고, 안 받으면 호출이 던지고, 시작 전이면 본문 없이 던진다** ★★

**출력**

```text
===== node20 js20b-20d-throw.js (exit=0) =====
[1] a body that catches around its yield
  next()                        {"value":0,"done":false}                     body: yield 0
  throw(new Error('X'))         {"value":1,"done":false}                     body: caught inside: Error 「X」 / yield 1
  next()                        {"value":2,"done":false}                     body: yield 2

[2] a body with no catch
  next()                        {"value":1,"done":false}                     body: (no log)
  throw(new Error('X'))         caught outside: Error 「X」                    body: finally
  next()                        {"value":"<undefined>","done":true}          body: (no log)

[3] throw() before the first next()
  throw(new Error('early'))     caught outside: Error 「early」                body: (no log)
  next()                        {"value":"<undefined>","done":true}          body: (no log)
```

**왜 그런가**

- ★★★ **`[1]` 둘째 줄 `throw()` 가 던지지 않고 `{"value":1,"done":false}`** — 예외가 `yield 0` 자리에 떨어져 `catch` 가 받았고(`caught inside: Error 「X」`), 루프가 돌아 `yield 1` 에서 다시 멈췄다.
  **`throw()` 의 반환값은 예외를 받은 뒤 다음으로 멈춘 `yield` 의 값**이다.
- ★★ **`[2]` 받는 `catch` 가 없으니 `throw()` 호출이 `Error 「X」` 를 던지고, 가는 길에 `finally`** 가 돈다. 이후는 끝난 상태다.
- ★★ **`[3]` 시작 전 — 본문 로그 없이 `Error 「early」` 가 곧장 나온다.** 루프의 `catch` 는 아직 없다. `return()` 의 시작 전 칸과 같은 `GeneratorResumeAbrupt` 규칙이다.

### 4. `yield*` — **`got` 은 `"inner-R"` · 결과 목록엔 없다 · 세 호출이 전부 안쪽으로 가고, 안쪽에 `throw` 가 없으면 닫고 `TypeError`** ★★★

**출력**

```text
===== node20 js20b-20e-delegate.js (exit=0) =====
[1] next(value) through yield*
  next('ignored')         {"value":"i1","done":false}          log: (none)
  next('A')               {"value":"i2","done":false}          log: inner got "A"
  next('B')               {"value":"o1","done":false}          log: inner got "B" / inner finally / outer: yield* evaluated to "inner-R"
  next()                  {"value":"<undefined>","done":true}  log: (none)
  [...outer()]            ["i1","i2","o1"]

[2] throw() through yield*
  next()                  {"value":"i1","done":false}          log: (none)
  throw(new Error('X'))   {"value":"i-after-catch","done":false} log: inner caught Error 「X」
  next()                  {"value":"o1","done":false}          log: inner finally / outer: yield* evaluated to "inner-R2"

[3] return() through yield*
  next()                  {"value":"i1","done":false}          log: (none)
  return('R')             {"value":"R","done":true}            log: inner finally

[4] yield* over an array iterator -- then throw()
  next()                  {"value":1,"done":false}             log: (none)
  throw(new Error('X'))   caught outside: TypeError 「The iterator does not provide a 'throw' method.」 log: overArray finally
  next()                  {"value":"<undefined>","done":true}  log: (none)

[5] a hand-written iterator under yield* -- which methods are called
  next('a')               {"value":"h1","done":false}          log: hand next("<undefined>")
  next('b')               {"value":"h2","done":false}          log: hand next("b")
  next('c')               {"value":"<undefined>","done":true}  log: hand next("c") / overHand got "hand-R"
  next()                  {"value":"h1","done":false}          log: hand next("<undefined>")
  return('R')             {"value":"R","done":true}            log: hand return("R")
  next()                  {"value":"h1","done":false}          log: hand next("<undefined>")
  throw(new Error('X'))   caught outside: TypeError 「The iterator does not provide a 'throw' method.」 log: hand return("<undefined>")
```

**왜 그런가**

- ★★★ **`[1]` `got` 은 `"inner-R"`, `[...outer()]` 는 `["i1","i2","o1"]`** — 안쪽이 끝난 결과의 `value` 는 `yield*` **식의 값**으로만 간다.
  명세 — "If done is true, then Return ? IteratorValue(innerResult)."
- ★★ **`[2]` `throw()` 가 값 `i-after-catch` 를 돌려준다** — 안쪽이 받아 냈으니 3번의 `[1]` 과 같은 모양이다. 다음 `next()` 에서 `got` 이 `inner-R2`.
- ★★ **`[3]` `return('R')` 이 `inner finally` 를 돌리고 `outer` 도 끝낸다** — `outer: …` 로그가 없다.
- ★★★ **`[4]`·`[5]` 는 내가 던진 `Error 「X」` 가 아니라 `TypeError 「The iterator does not provide a 'throw' method.」`** 다.
  배열 이터레이터와 손으로 짠 이터레이터에는 `throw` 가 없다. 명세 NOTE — "If iterator does not have a throw method, this throw is going to terminate the yield* loop. But first we need to give iterator a chance to clean up."
  `[5]` 에서 그 「정리할 기회」가 **`hand return("<undefined>")`** 로 보인다 — **`return()` 으로 닫고 나서** 던진다.
- ★★★ **`[5]` 첫 줄의 `hand next("<undefined>")`** — `'a'` 는 `overHand` 의 시작에서 사라졌고, `yield*` 루프는 "Let received be NormalCompletion(undefined)." 로 **안쪽 첫 `next` 를 `undefined` 로** 부른다. 그 뒤로는 `"b"`·`"c"` 가 그대로 간다.

### 5. 아홉 칸 — **본문 코드가 도는 칸은 넷 · 시작 전과 끝난 뒤의 `return`/`throw` 는 본문을 안 거친다** ★★★

**출력**

```text
===== node20 js20b-20g-grid.js (exit=0) =====
suspendedStart
  next('v')   {"value":"y","done":false}       body log ["try"]
  return('R') {"value":"R","done":true}        body log []
  throw(err)  throws Error 「err」               body log []
suspendedYield
  next('v')   {"value":"<undefined>","done":true} body log ["after yield","finally"]
  return('R') {"value":"R","done":true}        body log ["finally"]
  throw(err)  {"value":"<undefined>","done":true} body log ["catch","finally"]
completed
  next('v')   {"value":"<undefined>","done":true} body log []
  return('R') {"value":"R","done":true}        body log []
  throw(err)  throws Error 「err」               body log []

cells where body code ran: 4 / 9
```

**왜 그런가**

- ★★★ **마지막 줄의 수가 결론이다.** 도는 칸은 「시작 전 × `next`」 하나와 「`yield` 에서 멈춤」 줄 셋이다.
- ★★ **`return` 줄 셋은 결과가 전부 `{"value":"R","done":true}`** 이고, `throw` 의 시작 전·끝남도 둘 다 `throws Error 「err」` 다 — **결과로는 상태를 못 가른다.** 로그로만 갈린다.
- ★ 「`yield` 에서 멈춤 × `throw`」가 `done: true` 인 것은 `catch` 다음에 `yield` 가 없어서다 — 3번의 `[1]` 과 모양이 다른 이유다.

### 6. 막히는 자리 — **`new` 는 `TypeError` · 화살표·콜백 안 `yield` 는 `SyntaxError` · 재진입과 빌린 메서드는 `TypeError`** ★★

**출력**

```text
===== node20 js20b-20f-errors.js (exit=0) =====
[1] new on a generator function
  typeof gen.prototype                                object
  Object.getPrototypeOf(gen()) === gen.prototype      true
  new gen()                                           TypeError 「gen is not a constructor」

[2] five forms passed to new Function
  const g = *() => { yield 1; };                      SyntaxError 「Unexpected token '*'」
  const g = () => { yield 1; };                       SyntaxError 「Unexpected number」
  function* g() { [1].forEach(x => { yield x; }); }   SyntaxError 「Unexpected identifier 'x'」
  const o = { *m() { yield 1; } };                    compiles
  class C { static *m() { yield 1; } }                compiles

[3] calling next() from inside the running body
  self.next() inside the body                         TypeError 「Generator is already running」
  then self.next()                                    {"done":true}

[4] next / return borrowed onto a plain object
  GenProto.next.call({})                              TypeError 「Method [Generator].prototype.next called on incompatible receiver #<Object>」
  GenProto.return.call({})                            TypeError 「Method [Generator].prototype.return called on incompatible receiver #<Object>」
```
```text
===== node18 js20b-20f-errors.js (exit=0) =====
[1] new on a generator function
  typeof gen.prototype                                object
  Object.getPrototypeOf(gen()) === gen.prototype      true
  new gen()                                           TypeError 「gen is not a constructor」

[2] five forms passed to new Function
  const g = *() => { yield 1; };                      SyntaxError 「Unexpected token '*'」
  const g = () => { yield 1; };                       SyntaxError 「Unexpected number」
  function* g() { [1].forEach(x => { yield x; }); }   SyntaxError 「Unexpected identifier」
  const o = { *m() { yield 1; } };                    compiles
  class C { static *m() { yield 1; } }                compiles

[3] calling next() from inside the running body
  self.next() inside the body                         TypeError 「Generator is already running」
  then self.next()                                    {"done":true}

[4] next / return borrowed onto a plain object
  GenProto.next.call({})                              TypeError 「Method [Generator].prototype.next called on incompatible receiver #<Object>」
  GenProto.return.call({})                            TypeError 「Method [Generator].prototype.return called on incompatible receiver #<Object>」
```

**왜 그런가**

- ★★★ **`prototype` 이 `object` 인데 `new gen()` 은 `TypeError 「gen is not a constructor」`** — 08번 격자의 반례 그대로다. 제너레이터의 `prototype` 은 **제너레이터 객체들의 프로토타입**이다.
- ★★★ **`() => { yield 1; }` 은 `Unexpected number` — `1` 에서 막혔다.** 비엄격 스크립트의 평범한 함수 안에서 `yield` 는 **식별자**라 `yield 1` 이 「식별자 뒤에 숫자」다.
- ★★ **콜백 안의 `yield` 가 두 판이 갈린 줄이다** — node18 `Unexpected identifier`, node20 `Unexpected identifier 'x'`. **종류(`SyntaxError`)는 같다.**
- ★★ **`*m() {}` 는 객체·클래스 모두 `compiles`.**
- ★★★ **재진입은 `TypeError 「Generator is already running」`** — `GeneratorValidate` 의 "If state is executing, throw a TypeError exception." 그 예외가 본문을 빠져나가 제너레이터가 끝났고, 다음 호출이 `{"done":true}` 다.
- ★★ **빌린 `next`·`return` 은 `incompatible receiver #<Object>`** — ③ 브랜드 창이다. 받는 쪽에 `[[GeneratorState]]` 슬롯이 있어야 한다.

### 7. 첫 `next(값)` 이 사라지는 이유 — **본문은 인자 없이 시작하도록 명세에 적혀 있다 · 파이썬은 `TypeError` 로 막는다** ★★★

- ★★★ `GeneratorStart` — "Set the code evaluation state of genContext such that when evaluation is resumed for that execution context, closure will be called with no arguments."
  첫 `next` 가 재개하는 것은 이 「인자 없이 불릴 본문」이다. **첫 `next` 의 값을 받을 `yield` 식이 아직 없다** — 그래서 에러 없이 버려진다(1번).
- ★★ **파이썬은 같은 자리에서 `TypeError: can't send non-None value to a just-started generator`** 를 낸다 —
  파이썬 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **17번** 이 실은 출력이다. **모델은 같고 「첫 값」의 처리만 정반대**다.

### 8. 매개변수 기본값이 호출에서 찍히는 이유 — **매개변수는 호출에서, 본문은 첫 `next()` 에서** ★★

- ★★★ `EvaluateGeneratorBody` 가 "Perform ? FunctionDeclarationInstantiation(funcObj, argList)." 로 **매개변수를 먼저 묶고**, 그 뒤에 "Perform GeneratorStart(gen, FunctionBody)." 로 **본문을 매달아 두기만** 한다.
  요약의 동작 (1) `[4]` 에서 `withDefault()` 직후 `["default evaluated"]` 가 찍혔고, `destructure()` 는 **호출 자체가** `TypeError 「Cannot destructure property 'a' of 'undefined' as it is undefined.」` 였다.
- ★★ **인자 검사를 본문 첫 줄에 두면 실패가 첫 `next()` 까지 미뤄진다.** 빨리 실패시키려면 **평범한 함수가 검사하고 안쪽 제너레이터를 돌려주는** 모양으로 쓴다.

### 9. `return` 값을 받는 소비자 — **`yield*` 하나** ★★

- ★★★ 요약의 동작 (1) `[3]` — `[...gen()]` · `for...of` · `Array.from` 은 `["y1","y2"]`, 구조 분해 `[a, b, c]` 의 셋째는 `"<undefined>"`. **넷 다 `R` 을 안 본다.**
  19번이 이유를 적었다 — 소비자는 `done` 이 참이면 **그 결과의 `value` 를 읽지 않는다.**
- ★★★ **`yield*` 만 받는다** — 4번의 `got === "inner-R"`. 그래서 제너레이터를 쪼개 조립할 때 **하위 결과를 돌려받는 통로가 `return` + `yield*`** 다.
- ★ 수동 `next()` 로도 **한 번은** 보인다(동작 (1)의 `next#3`) — 그 다음부터는 `undefined` 다.

### 10. `take(map(naturals()), 3)` 이 넷째를 안 만드는 이유 — **`take` 가 셋째 뒤에 `return` 하고, 닫기가 `for...of` 두 겹을 타고 내려간다** ★★

- ★★★ 요약의 동작 (8) `[3]` 로그가 `make 1, square 1, make 2, square 2, make 3, square 3, finally` — **한 값이 세 단을 다 지나간 뒤 다음 값이 만들어지고**, `make 4` 가 없다.
- ★★ **경로** — `take` 의 `return` → `take` 안의 `for...of` 가 `map` 을 닫는다(19번의 「`return` 으로 빠져나가면 `return()`」) → `map` 이 멈춘 자리에서 `return` → `map` 안의 `for...of` 가 `naturals` 를 닫는다 → `naturals` 의 `finally`.
- ★★★ **「메모리를 아낀다」는 이 결과로 말할 수 없다** — 센 것은 **만든 개수**뿐이고 메모리·시간은 **안 쟀다.**

### 11. `finally` 의 `yield` 가 `return()` 을 멈추는 이유 — **`return()` 은 「닫기」가 아니라 「멈춘 자리에서 `return` 을 일으키기」다** ★★★

- ★★★ `return()` 은 `GeneratorResumeAbrupt` 로 **멈춘 `yield` 자리에 return 완료를 넣어 재개**한다. 그 `return` 이 `finally` 를 지나는 동안 **본문은 평소처럼 돈다** — `yield` 를 만나면 **평소처럼 멈춘다**(2번 `[2]` 의 `done: false`).
- ★★ **19번의 `for...of` + `break` 가 이 제너레이터를 만나면** — 19번이 적은 대로 소비자는 `return()` 의 결과가 **객체이기만 하면** 떠난다. 그러니 **`for...of` 는 떠나고 제너레이터는 `finally` 중간에 멈춘 채 남을 것**이다.
  ★★★ **이 문서는 그 조합을 돌리지 않았다** — 2번 `[2]` 와 19번의 호출표를 **이어 읽은 추론**이다. 「이렇게 된다」로 적지 않는다.

### 12. 경계 — **19번은 소비자 쪽 호출표 · 여기는 제너레이터 안쪽 · 21번은 표준 파이프라인 · 40번은 비동기** ★

- [19 — 이터러블 프로토콜과 `for...of`](../19-iterable-protocol-and-for-of/2-summary.md) — 소비자가 `next`·`return` 을 **언제 부르나**(8곳)까지.
- 여기 — 그 호출이 **제너레이터 본문에서 무엇을 돌리나**(`finally`·`catch`·`yield*` 전달) · `next(값)` 의 양방향 흐름.
- [21 — 이터레이터 헬퍼](../21-iterator-helpers/2-summary.md) — `map`·`filter`·`take` 의 **표준 판**과 배열 메서드판의 호출 횟수 대비. 여기는 손으로 짠 `take`/`map` 까지.
- [목록의 **40번 주제**](../40-async-iteration-and-for-await/) — `async function*`·`for await...of`.

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js20b-20a-start-and-end.js` | 호출 직후 본문 로그 0 · `next` 다섯 번의 결과와 로그 · 소비자 넷이 `return` 값을 안 보는 것 · 매개변수가 호출에서 평가되는 것 | node20 1벌 + node18 대조 1벌 |
| `js20b-20b-two-way.js` | ★★★ **양방향 흐름** — 첫 `next(값)` 이 버려지는 것 · 한 박자 어긋남 · 프라이밍 유무의 누산 차이 | node20 1벌 + node18 대조 1벌 |
| `js20b-20c-return-finally.js` | ★★★ `return()` 의 세 상태 · `finally` 의 `yield`·`return` · `break` 의 `finally` | node20 1벌 + node18 대조 1벌 |
| `js20b-20d-throw.js` | ★★ `throw()` 를 받아 내는 본문 · 못 받는 본문 · 시작 전 | node20 1벌 + node18 대조 1벌 |
| `js20b-20e-delegate.js` | ★★★ `yield*` 식의 값 · `next`/`throw`/`return` 전달 · `throw` 없는 안쪽 | node20 1벌 + node18 대조 1벌 |
| `js20b-20f-errors.js` | ★★ `new` · 문법 다섯 · 재진입 · 빌린 메서드(브랜드) | node20 1벌 + **node18 판도 싣는다**(갈린 블록) |
| `js20b-20g-grid.js` | ★★★ 세 메서드 × 세 상태 아홉 칸 · 본문이 돈 칸 수 | node20 1벌 + node18 대조 1벌 |
| `js20b-20h-lazy-seq.js` | ★★ 끝없는 제너레이터에서 만든 개수 · 닫기의 전파 | node20 1벌 + node18 대조 1벌 |
| `js20b-vdiff.sh` | **두 판이 갈린 탐침 수** — 이 주제의 것은 `js20b-20f-errors.js` 하나 | 1벌 |
| `js20b-versions.sh` + `js20b-features.js` | 이 문서의 모든 출력이 **어느 판에서 나왔나** · 판별 기능 표(node 두 판 · Chrome) | 1벌 |

```sh
# js20b-vdiff.sh
#!/usr/bin/env bash
# 두 node 판이 갈린 탐침이 몇 개인가 -- 스크립트가 직접 센다(브라우저 탐침 *.web.js 는 대상이 아니다).
set -u -o pipefail
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
cd "$(dirname "$0")"
same=0; diffn=0
for f in js20b-2[0-3]?-*.js; do
  case $f in *.web.js) continue ;; esac
  flags=""; case $f in *-gc.js) flags="--expose-gc" ;; esac
  a="$("$N18" $flags "$f" 2>&1)"
  b="$("$N20" $flags "$f" 2>&1)"
  if [ "$a" = "$b" ]; then
    printf '%-36s identical\n' "$f"; same=$((same + 1))
  else
    printf '%-36s DIFFERS\n' "$f"; diffn=$((diffn + 1))
    diff <(printf '%s\n' "$a") <(printf '%s\n' "$b") | sed 's/^/    /'
  fi
done
echo ""
echo "identical $same  ·  differs $diffn  ·  total $((same + diffn))"
```
```text
===== ./js20b-vdiff.sh (exit=0) =====
js20b-20a-start-and-end.js           identical
js20b-20b-two-way.js                 identical
js20b-20c-return-finally.js          identical
js20b-20d-throw.js                   identical
js20b-20e-delegate.js                identical
js20b-20f-errors.js                  DIFFERS
    9c9
    <   function* g() { [1].forEach(x => { yield x; }); }   SyntaxError 「Unexpected identifier」
    ---
    >   function* g() { [1].forEach(x => { yield x; }); }   SyntaxError 「Unexpected identifier 'x'」
js20b-20g-grid.js                    identical
js20b-20h-lazy-seq.js                identical
js20b-21x-node-absent.js             identical
js20b-22a-basics.js                  identical
js20b-22b-key-grid.js                identical
js20b-22c-toprimitive-hints.js       identical
js20b-22d-hasinstance.js             identical
js20b-22e-tostringtag.js             identical
js20b-22f-species.js                 DIFFERS
    9,12c9,12
    <   toSorted          -               TypeError 「a.toSorted is not a function」
    <   toReversed        -               TypeError 「a.toReversed is not a function」
    <   with              -               TypeError 「a.with is not a function」
    <   toSpliced         -               TypeError 「a.toSpliced is not a function」
    ---
    >   toSorted          -               Array
    >   toReversed        -               Array
    >   with              -               Array
    >   toSpliced         -               Array
js20b-22g-other-hooks.js             DIFFERS
    29c29
    <   keys                                              ["copyWithin","entries","fill","find","findIndex","flat","flatMap","includes","keys","values","at","findLast","findLastIndex"]
    ---
    >   keys                                              ["at","copyWithin","entries","fill","find","findIndex","findLast","findLastIndex","flat","flatMap","includes","keys","values","toReversed","toSorted","toSpliced"]
js20b-22h-registry.js                DIFFERS
    20,21c20,21
    <   new WeakMap().set(Symbol('k'), 1)                   TypeError 「Invalid value used as weak map key」
    <   new WeakRef(Symbol('k'))                            TypeError 「WeakRef: target must be an object」
    ---
    >   new WeakMap().set(Symbol('k'), 1)                   ok
    >   new WeakRef(Symbol('k'))                            ok
    23,25c23,25
    <   new WeakRef(Symbol.for('k'))                        TypeError 「WeakRef: target must be an object」
    <   new WeakMap().set(Symbol.iterator, 1)               TypeError 「Invalid value used as weak map key」
    <   new WeakRef(Symbol.iterator)                        TypeError 「WeakRef: target must be an object」
    ---
    >   new WeakRef(Symbol.for('k'))                        TypeError 「WeakRef: invalid target」
    >   new WeakMap().set(Symbol.iterator, 1)               ok
    >   new WeakRef(Symbol.iterator)                        ok
    27c27
    < symbol kinds accepted as a WeakMap key 0 / 3
    ---
    > symbol kinds accepted as a WeakMap key 2 / 3
js20b-22i-wellknown.js               DIFFERS
    3c3
    < a `using` declaration: SyntaxError 「Unexpected identifier」
    ---
    > a `using` declaration: SyntaxError 「Unexpected identifier 'r'」
js20b-23a-key-equality-grid.js       identical
js20b-23b-stored-key.js              identical
js20b-23c-map-vs-object.js           identical
js20b-23d-weak-keys.js               DIFFERS
    10c10
    <   new WeakMap().set(Symbol('local'), 1)             TypeError 「Invalid value used as weak map key」
    ---
    >   new WeakMap().set(Symbol('local'), 1)             ok true
    12c12
    <   new WeakMap().set(Symbol.iterator, 1)             TypeError 「Invalid value used as weak map key」
    ---
    >   new WeakMap().set(Symbol.iterator, 1)             ok true
    16,19c16,19
    <   new WeakRef(1)                                    TypeError 「WeakRef: target must be an object」
    <   new WeakRef(Symbol('local')).deref()              TypeError 「WeakRef: target must be an object」
    <   new WeakRef(Symbol.for('registered'))             TypeError 「WeakRef: target must be an object」
    <   new FinalizationRegistry(f).register(1, 'h')      TypeError 「FinalizationRegistry.prototype.register: target must be an object」
    ---
    >   new WeakRef(1)                                    TypeError 「WeakRef: invalid target」
    >   new WeakRef(Symbol('local')).deref()              ok symbol
    >   new WeakRef(Symbol.for('registered'))             TypeError 「WeakRef: invalid target」
    >   new FinalizationRegistry(f).register(1, 'h')      TypeError 「FinalizationRegistry.prototype.register: invalid target」
js20b-23e-reclaim-gc.js              identical
js20b-23f-timing-gc.js               identical

identical 18  ·  differs 6  ·  total 24
```

- ★ 대조기는 **이 배치 네 주제의 node 탐침 전부**를 센다. 이 주제의 줄은 `js20b-20` 으로 시작하는 여덟 줄이고, 그중 `DIFFERS` 는 `js20b-20f-errors.js` 하나다.

**구현 의존 항목** — 다음은 **이 환경(node 20.19.6 / 18.19.1 · x86-64 Linux)에서만** 그렇다.

- ★★★ **예외 문구 전부** — `gen is not a constructor` · `Unexpected token '*'` · `Unexpected number` · `Unexpected identifier 'x'`(v20) / `Unexpected identifier`(v18) ·
  `Generator is already running` · `Method [Generator].prototype.next called on incompatible receiver #<Object>` · `The iterator does not provide a 'throw' method.` ·
  `Cannot destructure property 'a' of 'undefined' as it is undefined.` **종류(`TypeError`·`SyntaxError`)만 명세가 정한다.**
- ★ **이터레이터 헬퍼가 두 node 판에 없는 것** — 판의 사정이다(판별 블록).

**호출이 본문을 안 돌리는 것 · 첫 `next` 의 값이 버려지는 것 · `yield` 식의 값이 다음 `next` 의 인자인 것 · 시작 전·끝난 뒤의 `return`/`throw` 가 본문을 안 거치는 것 · `finally` 의 `yield` 가 `return()` 을 멈추는 것 · `yield*` 의 값 회수와 세 호출 전달 · `throw` 없는 안쪽을 닫고 `TypeError` 인 것 · 재진입과 `new` 가 `TypeError` 인 것은 구현 의존이 아니다.**
어느 엔진에서도 같아야 한다.

**안 돌려 본 것 / 못 잰 것 / 부적용인 창**

- **안 돌려 본 것** —
  **`finally` 가 `yield` 하는 제너레이터를 `for...of` + `break` 로 닫는 조합**(11번 — 추론으로만 적었다) ·
  **파이썬 `send()`**(파이썬 17번이 실은 출력을 인용했다) · **Kotlin `sequence {}`** ·
  **브라우저**(판별 블록 말고는) · **엄격 모드 스크립트·모듈**(탐침은 전부 비엄격 스크립트 — 6번 `[2]` 둘째 줄의 문구는 비엄격이라서 그렇다) ·
  **`yield` 의 우선순위·ASI** · 다른 엔진(SpiderMonkey·JavaScriptCore)의 문구.
- ★ **못 잰 것** — **없다.**
- ★★★ **안 쟀다** — **성능·메모리 전부.** 10번은 **만든 개수**만 셌다.
- ★★ **부적용인 창** — **진단의 `(행,열)`**(18-C). `SyntaxError` 는 「안 된다」를 보이려는 것이지 **값으로 못 가르는 문법 성질**을 증명하려는 것이 아니다 — **잴 것이 없다.**

**판이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **예외 문구 전부** — 콜백 안 `yield` 의 문구는 **이 주제 안에서 실제로 바뀌었다**(6번).
- ★★ **이터레이터 헬퍼의 유무** — ES2025 를 들인 판에서는 제너레이터 객체에도 `map`·`take` 가 붙는다. 그때는 [21번](../21-iterator-helpers/2-summary.md)으로 넘어간다.
- **제너레이터의 흐름 자체(양방향 · `return`/`throw` · `yield*`)는 다시 돌릴 필요가 없다** — ES2015 부터의 계약이다.
