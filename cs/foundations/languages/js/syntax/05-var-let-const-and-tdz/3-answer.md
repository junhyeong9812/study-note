# js/syntax/05 — `var`·`let`·`const` 와 TDZ: 「이 이름은 언제부터 쓸 수 있나」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **node v20.19.6**(기본 판) · **node v18.19.1**(대조) · **Google Chrome 151.0.7922.173** · x86-64 Linux 에서 실제로 돌려 얻은 것이고,
> 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 하나도 없다).
> 소스는 `js05b-05a-hoisting-grid.js`\~`js05b-05f-redeclare.js` 와 `js05b-07g-browser.js`·`js05b-vdiff.sh` 다.
>
> ★★ **예외는 `e.constructor.name` 과 `e.message` 로만 찍었다** — 스택트레이스에는 절대 경로가 박혀 재현이 안 된다.
> ★★ **`SyntaxError` 는 `new Function(소스)` 으로 파싱만 시켜 받았다** — 파일로 던지면 진단에 경로가 박힌다.
> ★★ **표준 출력과 표준 오류를 한 블록에도 안 섞었다** — 이 주제의 블록은 전부 표준 출력이다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | Node 스택트레이스의 **절대 경로** — 한 줄도 싣지 않았다 | ★★★ **어느 칸이 터지고 어느 칸이 안 터지는가** |
> | 예외 **문구** — ★ 이 주제에서는 「없다」와 「잠겼다」를 가르는 **유일한 근거**라 특히 아프다 | ★★★ **예외의 종류** — `ReferenceError`·`TypeError`·`SyntaxError` |
> | Node 모듈 래퍼의 **인자 다섯 개**가 무엇인가 | ★★ **프로퍼티 디스크립터** · **`globalThis` 에 붙나** · 종료 코드 |
> | 브라우저 UA 의 뒷자리 | ★★ **두 판 대조 결과**(전부 같음) |
>
> ★ **이 주제의 블록에는 주소도 시간도 난수도 안 찍힌다.** 같은 판에서 다시 돌리면 한 글자도 안 변한다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 여섯 선언을 두 가지 방법으로 건드리면 — **열두 칸 중 일곱이 터진다** ★★★

**출력**

```text
===== node20 js05b-05a-hoisting-grid.js (exit=0) =====
decl          read it                                                 typeof it
--------------------------------------------------------------------------------------------------------------------
var v         undefined                                               "undefined"
let l         ReferenceError: Cannot access 'l' before initialization ReferenceError: Cannot access 'l' before initialization
const c       ReferenceError: Cannot access 'c' before initialization ReferenceError: Cannot access 'c' before initialization
function f    [Function: f]                                           "function"
class K       ReferenceError: Cannot access 'K' before initialization ReferenceError: Cannot access 'K' before initialization
(undeclared)  ReferenceError: nope is not defined                     "undefined"

[함수 선언은 이름만이 아니라 본문까지 이미 있다]
  calling f(1) before its declaration -> 2
```

**왜 그런가**

- ★★★ **터지는 칸은 일곱**이다 — `let`·`const`·`class` 가 **두 칸씩 여섯**, 거기에 `(undeclared)` 의 **읽기 칸 하나**.
  안 터지는 다섯은 `var` 둘 · `function` 둘 · `(undeclared)` 의 `typeof` 칸이다.
- ★★★ **두 칸의 답이 어긋나는 줄은 `(undeclared)` 하나**다 — 읽으면 `ReferenceError` 인데 `typeof` 는 `"undefined"` 를 준다.
  ★ **언어 전체에서 `typeof` 가 예외를 삼키는 자리가 여기뿐**이고, 그 정본이 [01번](../01-value-types-and-typeof/2-summary.md)이다.
  ★★ 나머지 다섯 줄은 두 칸이 **같은 답**을 낸다 — 그래서 **`typeof` 는 「없다」와 「아직」을 구분해 주지 않는다.**
- ★★ **`ReferenceError` 의 문구가 두 가지**다.
  `nope is not defined` 는 **칸이 아예 없다**는 뜻이고,
  `Cannot access 'l' before initialization` 은 **칸은 있는데 아직 초기화 전**이라는 뜻이다.
  ★★★ **뒤엣것이 「`let` 도 호이스팅된다」의 증거**다 — 이름이 없었다면 앞의 문구가 나왔을 것이다.
- ★★ **「`let` 은 호이스팅이 안 된다」는 틀렸다.** 셋 다 스코프 진입 시 이름이 만들어지고,
  **`var` 만 그때 `undefined` 로 초기화된다.** 안 되는 것은 호이스팅이 아니라 **초기화**다.
- ★ **`function` 선언은 본문까지 이미 있다** — 마지막 줄이 선언문 앞에서 `f(1)` 을 불러 `2` 를 받았다.
  ★ **`var` 로 만든 함수 표현식은 아니다** — 그 자리에서는 `undefined` 를 부르게 되어 `TypeError: expr is not a function` 이다(08번이 그 격자를 편다).

### 2. 블록에 들어선 순간과 선언문이 실행되는 순간 — **TDZ 는 줄이 아니라 시간이다** ★★★

**출력**

```text
===== node20 js05b-05b-tdz-boundary.js (exit=0) =====
[1] TDZ 는 선언문 줄이 아니라 블록 진입에서 시작한다
  (바깥에 v = "outer" 가 있다 — 그것이 보이는지를 본다)
  block entered                  -> ReferenceError: Cannot access 'v' before initialization
  peek() before the let          -> ReferenceError: Cannot access 'v' before initialization
  after the let stmt             -> "inner"
  the same peek() again          -> "inner"

[2] 끝나는 것은 선언문이 놓인 줄이 아니라 그 문장이 실행되는 순간이다
  read() with flag=true          -> ReferenceError: Cannot access 'w' before initialization
  read() after the let ran       -> 1

[3] 초기화자가 없어도 TDZ 는 있다
  before `let u;`                -> ReferenceError: Cannot access 'u' before initialization
  after  `let u;`                -> undefined

[4] 매개변수 기본값에도 TDZ 가 있고 왼쪽에서 오른쪽이다
  ok()  -- b sees a              -> [1,2]
  bad() -- a sees b              -> ReferenceError: Cannot access 'b' before initialization

[5] class 선언도 TDZ 에 들어가고 function 선언은 안 들어간다
  new K() before class K         -> ReferenceError: Cannot access 'K' before initialization
  g() before function g          -> "g ran"
```

**왜 그런가**

- ★★★ **바깥의 `v = "outer"` 가 안 읽혔다는 것이 「블록 진입부터」의 증거**다.
  TDZ 가 선언문 줄에서 시작했다면 그 위에서는 **안쪽 `v` 가 아직 없어 바깥 것이 보였어야** 한다.
  안 보였다는 것은 **블록에 들어선 순간 이미 안쪽 `v` 가 바깥을 덮었다**는 뜻이다.
- ★★★ **`[2]` 에서 바뀐 것은 함수가 아니라 칸이다.** `read` 는 같은 함수 객체이고,
  `let w = 1` 이 **실행되는 순간** 그 칸의 잠금이 풀린다. 그래서 같은 함수가 앞에서는 터지고 뒤에서는 `1` 을 준다.
  ★★ **그래서 「선언문 아래면 괜찮다」가 아니다** — 아래에 있어도 아직 실행 전이면 잠겨 있다.
- ★★ **`[3]` 은 「잠김」과 「`undefined`」를 가른다.** `let u;` 앞은 `ReferenceError`, 뒤는 `undefined` 다.
  **초기화자가 없어도 TDZ 는 있고**, 선언문이 실행되면 `undefined` 로 초기화된다.
- ★★ **`[4]` 의 규칙 한 문장** — **매개변수는 왼쪽에서 오른쪽으로 초기화되고, 아직 안 온 이름은 TDZ 다.**
  그래서 `b = a + 1` 은 되고 `a = b` 는 안 된다. 08번이 이 칸을 이어받는다.
- ★ **`class` 는 TDZ 에 들어가고 `function` 은 안 들어간다.** 문법이 선언처럼 생긴 것과 호이스팅 방식은 별개다 —
  `function` 은 **이름과 본문이 같이** 올라가고, `class` 는 **이름만** 올라간 뒤 잠긴다.

### 3. `const` 로 묶어 두면 무엇이 안 되나 — **이름 하나만 못질된다** ★★★

**출력**

```text
===== node20 js05b-05d-const.js (exit=0) =====
[1] const 가 고정하는 것은 이름이지 그 뒤의 값이 아니다
  const n = 1; n = 2                 -> TypeError: Assignment to constant variable.
  const o = {}; o.k = 1              -> {"k":1}
  const a = []; a.push(1)            -> [1]
  const o = {}; o = {}               -> TypeError: Assignment to constant variable.

[2] 값까지 고정하고 싶으면 그것은 다른 도구다
  frozen.k = 1 (sloppy)              -> {"k":0}
  frozen.k = 1 (strict)              -> TypeError: Cannot assign to read only property 'k' of object '#<Object>'
  freeze is shallow                  -> {"inner":{"k":1}}

[3] const 는 초기화자가 있어야 하고 let 은 없어도 된다
  const c;                           -> SyntaxError: Missing initializer in const declaration
  let l;                             -> parsed ok
  const c = 1;                       -> parsed ok

[4] 루프의 const — for-of 는 회차마다 새 이름, for(;;) 는 아니다
  for (const x of [1,2,3])           -> [1,2,3]
  for (const k in {a:1,b:2})         -> ["a","b"]
  for (const i=0; i<3; i++)          -> TypeError: Assignment to constant variable.

[5] 섀도잉은 재선언이 아니다 — 안쪽 블록은 같은 이름을 다시 쓸 수 있다
  inner block shadows outer          -> ["outer","inner"]
  same block twice                   -> SyntaxError: Identifier 'n' has already been declared
```

**왜 그런가**

- ★★★ **가르는 기준은 「대입의 왼쪽이 그 이름이냐」** 하나다.
  `n = 2` 와 `o = {}` 는 왼쪽이 그 이름이라 `TypeError` 이고,
  `o.k = 1` 과 `a.push(1)` 은 **왼쪽이 그 이름이 아니라** 그냥 된다.
- ★★ **`[2]` 의 첫 두 줄은 엄격 모드로 갈린다.** 느슨한 모드는 `Object.freeze` 한 객체에 대입해도 **에러 없이 버린다.**
  ★★★ **「에러가 안 났다」가 「먹혔다」가 아니다** — 값을 다시 읽어야 안다(`{"k":0}`).
  엄격 모드에서만 `TypeError: Cannot assign to read only property 'k' of object '#<Object>'` 다.
  ★ 그리고 **`freeze` 는 얕다** — `o.inner.k` 는 그대로 바뀐다.
- ★★ **`[3]` 은 파싱 에러다.** `SyntaxError: Missing initializer in const declaration` 은 **런타임에 도달하기 전에** 난다 —
  그 파일의 다른 코드가 **한 줄도 안 돈다.** 런타임 에러처럼 `try` 로 감쌀 수 없다.
- ★★ **`for (const x of ...)` 가 되는 이유는 회차마다 이름이 새로 만들어지기 때문**이고,
  `for (const i = 0; i < 3; i++)` 가 안 되는 이유는 **같은 이름에 `i++` 가 재대입을 하기 때문**이다.
  ★ 이 한 쌍이 06번의 「회차마다 새 바인딩」과 **같은 사실의 다른 얼굴**이다.
- ★ **`[5]` 가 가르는 두 낱말은 섀도잉과 재선언**이다.
  안쪽 블록의 같은 이름은 **다른 칸**이라 통과하고, **같은 블록**에서 두 번은 `SyntaxError` 다.

### 4. 같은 이름을 두 번 쓰면 — **열세 줄 중 여섯이 통과한다** ★★★

**출력**

```text
===== node20 js05b-05f-redeclare.js (exit=0) =====
source                                        result
--------------------------------------------------------------------------------------------------
var a = 1; var a = 2;                         parsed ok
let a = 1; let a = 2;                         SyntaxError: Identifier 'a' has already been declared
const a = 1; const a = 2;                     SyntaxError: Identifier 'a' has already been declared
var a = 1; let a = 2;                         SyntaxError: Identifier 'a' has already been declared
let a = 1; var a = 2;                         SyntaxError: Identifier 'a' has already been declared
let a = 1; const a = 2;                       SyntaxError: Identifier 'a' has already been declared
function a() {} function a() {}               parsed ok
let a = 1; function a() {}                    SyntaxError: Identifier 'a' has already been declared
var a = 1; function a() {}                    parsed ok
let a = 1; { let a = 2; }                     parsed ok
let a = 1; function f(a) {}                   parsed ok
function f(a, a) { return a; }                parsed ok
'use strict'; function f(a, a) { return a; }  SyntaxError: Duplicate parameter name not allowed in this context

[통과한 것이 실제로 무엇을 만들었나 — 통과도 출력이다]
  var a=1; var a=2 -> a is 2
  function a twice -> a() is 2
  sloppy dup param -> f(1,2) is 2
```

**왜 그런가**

- ★★★ **통과하는 줄은 여섯**이다 —
  `var`+`var` · `function`+`function` · `var`+`function` · `let` 과 **다른 블록**의 `let` ·
  `let` 과 **매개변수** · **비엄격의 중복 매개변수**.
  ★ 나머지 일곱은 전부 `let`/`const` 가 **같은 스코프에** 끼어 있거나 **엄격 모드의 중복 매개변수**다.
- ★★★ **통과한 것들이 무엇을 만들었나** — 전부 **마지막 것이 이긴다.**
  `var a=1; var a=2` 는 `a` 가 `2`, `function a` 두 번은 뒤엣것이 불리고(`2`),
  비엄격의 `f(a, a)` 는 `f(1, 2)` 가 `2` 를 돌려준다.
  ★★ **「통과했다」가 「아무 일도 안 났다」가 아니다** — 앞엣것이 조용히 덮였다.
- ★★ **마지막 두 줄을 가른 것은 엄격 모드**다. 비엄격은 중복 매개변수를 받고,
  엄격은 `SyntaxError: Duplicate parameter name not allowed in this context` 다.
  ★ **설정이 답을 바꾸는 칸**이라 두 줄을 나란히 실었다.
- ★★ **이 에러는 파싱 단계에서 난다.** `try`/`catch` 로 못 잡고, **그 스크립트의 다른 코드가 한 줄도 안 돈다.**
  그래서 이 격자는 실행이 아니라 `new Function(소스)` 으로 **파싱만 시켜** 받았다.
- ★ **`let a = 1; { let a = 2; }` 가 통과하는 이유는 스코프가 다르기 때문**이고, 그것을 **섀도잉**이라 부른다.
  재선언은 **같은 스코프**에서만 성립한다.

### 5. 루프가 끝난 뒤, 그리고 루프가 만든 함수들 — **`[3,3,3]` 대 `[0,1,2]`** ★★

**출력**

```text
===== node20 js05b-05e-loop-scope.js (exit=0) =====
[1] 루프가 끝난 뒤에 그 이름이 남아 있나
  var: read i after loop         -> 3
  let: read i after loop         -> ReferenceError: i is not defined

[2] 루프 안에서 만든 함수 셋을 나중에 부르면
  var                            -> [3,3,3]
  let                            -> [0,1,2]

[3] 블록 하나로도 갈린다 — if 블록 안의 선언
  var inside if block            -> "number"
  let inside if block            -> "undefined"

[4] var 는 블록을 몇 겹이든 빠져나오지만 함수는 못 빠져나온다
  var out of nested blocks       -> 7
  let out of nested blocks       -> "undefined"
  var out of a function          -> "undefined"
```

**왜 그런가**

- ★★★ **「나중에 읽어서」는 증상의 절반만 설명한다.**
  칸이 셋이었다면 **나중에 읽어도** `0`·`1`·`2` 가 나왔을 것이다.
  실제 원인은 **칸이 하나**라서 셋이 같은 것을 보는 것이고, **칸을 셋으로 가르면 나중에 읽어도 `[0,1,2]`** 다.
  ★★ 06번이 그 **개수를 직접 세어** 이 문장을 증명한다.
- ★★ **`[4]` 가 「함수 스코프」의 정확한 정의**다 — **`var` 는 블록을 몇 겹이든 빠져나오지만 함수 경계는 못 넘는다.**
  `{ { var q = 7; } }` 밖에서 `q` 가 `7` 이고, 함수 안의 `var deep` 는 밖에서 `"undefined"` 다.
- ★★ **`var` 를 `let` 으로 일괄 치환하면 `[1]` 의 첫 줄과 `[3]`·`[4]` 의 `var` 줄이 깨진다.**
  루프 뒤에 `i` 를 쓰던 코드가 `ReferenceError` 로 죽는다. **기계 치환이 안 되는 자리다.**
- ★ **06번이 이어받는 칸은 `[2]`** 다. 여기서는 **값**으로 보이고, 06번에서는 「**서로 다른 상자 개수**」로 센다.

### 6. 이 파일의 최상위는 전역인가 — **Node 의 `.js` 에서는 아니다** ★★★

**출력 — Node**

```text
===== node20 js05b-05c-globalthis.js (exit=0) =====
[1] 이 파일은 Node 가 감싼 모듈이라 최상위가 전역 스코프가 아니다
  typeof module                          -> "object"
  this === module.exports                -> true
  top-level arrow arguments.length       -> 5
  what those 5 arguments are             -> ["object","function","object","string","string"]
  globalThis.topVar                      -> undefined
  globalThis.topLet                      -> undefined

[2] 진짜 전역 스코프의 스크립트 — vm.runInThisContext
  globalThis.sv                          -> 1
  descriptor of sv                       -> {"value":1,"writable":true,"enumerable":true,"configurable":false}
  'sl' in globalThis                     -> false
  'sc' in globalThis                     -> false
  descriptor of sf                       -> {"writable":true,"enumerable":true,"configurable":false}

[3] let/const 도 거기 있다 — 다만 프로퍼티가 아닐 뿐이다
  a later script reading sl              -> 2
  a later script reading sc              -> 3

[4] var 가 만든 전역 프로퍼티는 못 지우고 그냥 대입한 것은 지워진다
  delete globalThis.sv                   -> false
  globalThis.sv after delete             -> 1
  delete globalThis.plain                -> true
  descriptor of an eval-made var         -> {"value":1,"writable":true,"enumerable":true,"configurable":true}

[5] 전역 let 은 두 번째 선언을 거부한다 — 스크립트가 달라도
  let sl = 9;                            -> SyntaxError: Identifier 'sl' has already been declared
  var sl = 9;                            -> SyntaxError: Identifier 'sl' has already been declared
  var sv = 9;                            -> ok
```

**출력 — 브라우저**

```text
===== google-chrome --headless --disable-gpu --no-sandbox --virtual-time-budget=1000 --dump-dom js05b-07g-browser.html 2>/dev/null | sed -n '/^<pre id="out">/,/<\/pre>/p' (exit=0) =====
<pre id="out">top-level this in a classic script     : globalThis (window)
sloppy f()                             : globalThis (window)
strict f()                             : undefined
globalThis === window                  : true
window.name is                         : ""
obj.hello()                            : hi obj
detached hello() -- the silent one     : hi 
window.declaredVar                     : on window
window.declaredLet                     : undefined
declaredLet read by name               : not on window
top-level arrow: arguments?            : ReferenceError: arguments is not defined
setTimeout(fn) this                    : globalThis (window)</pre>
```

**왜 그런가**

- ★★★ **Node 의 `.js` 는 인자 다섯 개짜리 함수로 감싸여 돈다.** 그래서 최상위 화살표의 `arguments.length` 가 `5` 다 —
  화살표는 자기 `arguments` 를 안 만들므로 **감싼 함수의 것**을 본 것이다(08번).
  다섯은 `exports`·`require`·`module`·`__filename`·`__dirname` 이고, 출력의 `["object","function","object","string","string"]` 이 그 타입 순서다.
  ★★★ **브라우저에서 같은 줄이 `ReferenceError: arguments is not defined` 다** — 거기에는 래퍼가 없다.
  **같은 문장이 두 호스트에서 갈리는 것이 이 사실의 증명**이다.
- ★★★ **「전역 `var` 는 `globalThis` 에 붙는다」는 「진짜 전역 스코프의 스크립트」에서만 참**이다.
  `vm.runInThisContext` 로 던진 `var sv` 는 붙고(`globalThis.sv === 1`), 브라우저의 `var declaredVar` 도 붙는다(`"on window"`).
  **이 파일의 최상위 `var` 는 안 붙는다** — 래퍼 함수의 지역 변수이기 때문이다.
- ★★ **`sl`·`sc` 는 프로퍼티가 아닐 뿐 없는 것이 아니다.** 전역에도 **이름만 사는 자리**(전역 렉시컬 환경)가 따로 있고,
  뒤이은 스크립트가 **이름으로는** 읽는다(`2`, `3`). 브라우저에서도 `window.declaredLet` 은 `undefined` 인데 `declaredLet` 은 `"not on window"` 다.
  ★★ **「`in` 검사가 `false`」를 「없다」로 읽으면 두 번 틀린다.**
- ★★ **셋이 다 다르다.**
  `var` 가 만든 전역 프로퍼티는 **`configurable: false`** 라 `delete` 가 `false` 를 돌려주고 값이 남는다.
  **그냥 대입**해 만든 프로퍼티는 지워진다.
  **`eval` 이 만든 `var`** 는 `configurable: true` 라 지워진다 — 같은 `var` 라는 낱말인데 성질이 다르다.
- ★ **`window.name` 이 `""`** 인 것이 07번으로 이어진다 — 메서드를 떼어 내 부르면 Node 에서는 `hi undefined`,
  **브라우저에서는 `hi ` 로 끝나** 사고가 더 조용해진다.

### 7. `typeof` 의 특권과 그 구멍 ★★

- ★★★ **`typeof` 가 안 터지는 자리는 「이름이 어느 스코프에도 선언되지 않았을 때」 하나**다.
- ★★★ **TDZ 에서 터져야 하는 이유는 칸이 이미 있기 때문**이다.
  `typeof` 의 특권은 「**칸을 못 찾았을 때** `"undefined"` 로 떨어뜨린다」는 것이지
  「**어떤 실패든** 삼킨다」가 아니다. TDZ 는 **칸을 찾은 뒤에** 나는 실패라 그 그물에 안 걸린다.
- ★★ **`typeof x === "undefined"` 가 참이 되는 상태는 둘**이다 — 「선언이 없다」와 「값이 `undefined` 다」.
  「`null` 이다」는 `"object"` 이고 「TDZ 다」는 **참·거짓을 내기 전에 터진다.**
- ★★ **깨지는 코드는 이 모양**이다.

  ```js
  function f() {
    if (typeof cfg === "undefined") { /* 기본값 */ }
    let cfg = loadConfig();
  }
  ```

  방어하려던 줄이 **그 자리에서 `ReferenceError`** 다.
- ★ **정본은 [01번](../01-value-types-and-typeof/2-summary.md)이고**, 이 주제가 더한 것은 **여섯 줄 격자**다 —
  01번이 `let` 한 줄로 보인 것을 `const`·`class`·`function`·`var` 까지 넓혀 **「특권이 걸리는 줄과 안 걸리는 줄」을 전수로** 만들었다.

### 8. 세 가지 「아직 없음」 ★★

| 상태 | 무엇으로 가리나 | 그냥 읽으면 | `typeof` 하면 |
|---|---|---|---|
| 칸이 없다 (선언 안 됨) | **`typeof x === "undefined"`** (이것만 된다) | `ReferenceError: x is not defined` | `"undefined"` |
| 칸이 잠겼다 (TDZ) | ★ **가릴 수단이 없다** — 무엇을 해도 터진다 | `ReferenceError: Cannot access 'x' before initialization` | 같은 `ReferenceError` |
| 칸에 `undefined` 가 있다 | `x === undefined` · `typeof x === "undefined"` | `undefined` | `"undefined"` |

- ★★ **`ReferenceError` 가 나는 것은 앞의 둘**이다. 그런데 **예외의 종류는 같다.**
- ★★★ **셋을 가르는 유일한 근거가 예외 문구**라는 것이 이 주제의 약한 고리다.
  **문구는 V8 의 것이고 판이 오르면 바뀔 수 있다** — 그래서 이 문서는 **그 위에 결론을 세우지 않았다.**
  결론은 「둘 다 `ReferenceError` 이고, **가릴 방법이 있는 쪽과 없는 쪽**으로 갈린다」까지다.
- ★ **`let u;` 와 `let u = undefined;` 는 구분되지 않는다.** 둘 다 선언문이 실행되면 `undefined` 다.
- ★ **「호이스팅이 안 된다」가 맞는 상태는 첫째 하나**다 — 애초에 선언이 없으니 올라갈 것도 없다.

### 9. 보장인가 호스트인가 사정인가 ★★★

| 층 | 이 주제에서 여기 들어가는 것 |
|---|---|
| **명세 보장** | 셋 다 스코프 진입 시 이름이 만들어지는 것 · `var` 만 `undefined` 로 초기화되는 것 · **TDZ 가 블록 진입에서 시작해 선언문 실행으로 끝나는 것** · TDZ 에서 `typeof` 도 터지는 것 · `const` 가 재대입만 막는 것 · `const` 가 초기화자를 요구하는 것 · `var` 는 함수 스코프·`let`/`const` 는 블록 스코프인 것 · `let`/`const` 가 낀 재선언이 `SyntaxError` 인 것 · 엄격 모드의 중복 매개변수가 `SyntaxError` 인 것 · 진짜 전역에서 `var` 만 프로퍼티가 되고 `configurable: false` 인 것 |
| **호스트가 정하는 것** | ★★ **「최상위」가 무엇이냐** — Node 의 `.js` 는 래퍼 함수 안, 브라우저 classic script 는 진짜 전역. **ECMA-262 는 이것을 안 정한다** |
| **엔진(V8) 구현** | 두 판의 V8 번호 · 일곱 스크립트가 두 판에서 같았다는 것 |
| **이 판의 관찰** | 예외 **문구** 전부 · Node 래퍼의 인자가 다섯인 것 · 브라우저 UA |

- ★★★ **「전역 `var` 가 `globalThis` 에 붙는다」는 명세 보장과 호스트 칸에 걸쳐 있다.**
  「**진짜 전역 스코프의 스크립트라면** 붙는다」까지가 명세이고,
  「**내 파일이 진짜 전역 스코프인가**」는 호스트가 정한다. **두 칸을 섞으면 이 주제에서 가장 크게 틀린다.**
- ★★ **예외의 종류는 명세, 문구는 V8 의 것**이다. 이 주제에서는 특히 아프다 —
  **「칸이 없다」와 「칸이 잠겼다」를 가르는 근거가 문구뿐**이기 때문이다. 그래서 그 위에 결론을 세우지 않았다.
- ★★ **「두 판에서 같았다」는 엔진 구현 칸의 근거**가 된다. **명세 보장 칸의 근거는 못 된다.**
- ★ **가장 얇은 칸은 「엔진 구현」이다**. 선언과 스코프에는 엔진이 고를 여지가 거의 없다 —
  ★ 대신 이 주제는 **「호스트」 칸이 다른 주제보다 두껍다.**

### 10. 경계 — 어디까지가 이 주제인가 ★★

| 주제 | 정본 |
|---|---|
| 클로저 · 루프 클로저의 「상자 개수」 | 목록의 **06번 주제** |
| `this` 가 어떻게 정해지나 | 목록의 **07번 주제** |
| 함수 선언의 호이스팅 · 매개변수 기본값 | 목록의 **08번 주제** |
| 엄격 모드가 바꾸는 규칙 전부 | 목록의 **35번 주제** |
| 모듈(ESM)의 최상위 · 라이브 바인딩 | 목록의 **42번 주제** |
| 프로퍼티 디스크립터(`configurable`) | 목록의 **14번 주제** |
| `let`/`const` 가 언제 왜 들어왔나 | [`history/js/02-ES6-모던.md`](../../../../../../history/js/02-ES6-모던.md) |

- ★★★ **06번이 이어받는 것은 「칸이 몇 개냐」다**. 이 주제는 `[3,3,3]` 대 `[0,1,2]` 라는 **값**까지 보이고,
  06번이 그것을 **「서로 다른 상자 개수 1 대 3」** 으로 바꿔 센다.
- ★★ **파이썬에는 블록 스코프가 없다**([`python/syntax/21-scope-legb-global-nonlocal`](../../../python/syntax/21-scope-legb-global-nonlocal/2-summary.md)).
  `if`/`for` 안에서 만든 이름이 **함수 전체에 산다** — JS 의 `var` 쪽이다.
  **그쪽은 「어느 스코프에서 찾나(LEGB)」까지, 여기는 「그 이름이 언제부터 쓸 수 있나」부터다.**
- ★ **연혁이 이 주제가 아닌 이유**는 「지금 이 규칙이 무엇을 만드나」와 「왜 그 규칙이 생겼나」가 다른 질문이기 때문이다.
- ★ **이 주제가 끝까지 책임지는 것 셋** — ① 선언 전에 건드리면 무엇이 나오나 ② TDZ 의 시작과 끝
  ③ `const` 가 무엇을 고정하나.

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js05b-05a-hoisting-grid.js` | 여섯 선언 × 두 칸 격자 · **`typeof` 가 어긋나는 줄이 하나**인 것 | node20 1벌 + node18 대조 1벌 |
| `js05b-05b-tdz-boundary.js` | **TDZ 의 시작(블록 진입)과 끝(선언문 실행)** · 매개변수 기본값의 TDZ | node20 1벌 + node18 대조 1벌 |
| `js05b-05c-globalthis.js` | Node 모듈 래퍼 · **진짜 전역에서 `var` 만 프로퍼티** · 디스크립터 세 가지 | node20 1벌 + node18 대조 1벌 |
| `js05b-05d-const.js` | `const` 가 이름만 막는 것 · `freeze` 의 조용한 실패 · 루프의 `const` | node20 1벌 + node18 대조 1벌 |
| `js05b-05e-loop-scope.js` | `var`/`let` 의 루프 뒤 수명 · `[3,3,3]` 대 `[0,1,2]` · 함수 스코프의 정의 | node20 1벌 + node18 대조 1벌 |
| `js05b-05f-redeclare.js` | **재선언 13줄 격자** · 통과한 것이 만든 값 · 엄격 모드가 가른 두 줄 | node20 1벌 + node18 대조 1벌 |
| `js05b-05x-forms.js` | 형태 — `node --check` **진단 0줄**(빈 출력도 블록으로) | node20 1벌 |
| `js05b-07g-browser.js` | **브라우저 최상위가 진짜 전역**인 것 · 최상위 화살표의 `arguments` | Chrome 151 1벌 |
| `js05b-vdiff.sh` | 일곱 스크립트가 **두 판에서 한 글자도 같다**는 것 | 1벌 |
| `js05b-versions.sh` | 이 문서의 모든 출력이 **어느 판에서 나왔나** | 1벌 |

**구현 의존 항목** — 다음은 **이 환경(node 20.19.6 / 18.19.1 · Chrome 151 · x86-64 Linux)에서만** 그렇다.

- ★★ **예외 메시지 문구 전부** — `Cannot access 'l' before initialization` · `l is not defined` ·
  `Identifier 'a' has already been declared` · `Assignment to constant variable.` · `Missing initializer in const declaration`.
  **종류는 명세, 문구는 V8 의 것**이다.
- ★★ **Node 모듈 래퍼의 인자가 다섯 개**인 것 — Node 의 구현이다. **요점은 개수가 아니라 「래퍼가 있다」이다**.
- ★ **`[object Object]` 로 찍힌 최상위 `this`** — Node CJS 에서 `module.exports` 다. 호스트마다 다르다.

**셋 다 호이스팅되는 것 · `var` 만 `undefined` 로 초기화되는 것 · TDZ 의 시작과 끝 · TDZ 에서 `typeof` 도 터지는 것 · `const` 가 재대입만 막는 것 · `var` 는 함수 스코프·`let`/`const` 는 블록 스코프인 것 · `let`/`const` 가 낀 재선언이 `SyntaxError` 인 것은 구현 의존이 아니다.**
어느 엔진에서도 같아야 한다.

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — ESM(`.mjs`)의 최상위 · Web Worker · `vm.createContext` 로 만든 다른 realm ·
  Node 18 보다 낮은 판 · 다른 엔진(SpiderMonkey·JavaScriptCore) · `with` 문 · `--frozen-intrinsics` 같은 플래그 ·
  **엄격 모드 파일 전체**에서 이 여섯 스크립트를 다시 돌리는 것.
- ★ **못 잰 것** — **「엔진이 TDZ 를 어떻게 표시하나」.**
  잠긴 칸과 `undefined` 가 든 칸을 엔진이 **어떻게 구별해 담는지**는 표준 API 로 볼 방법이 없다.
  ★★ 그래서 본문은 **「읽으면 터진다」는 관찰까지만** 적고 **「특별한 표식 값이 들어 있다」는 적지 않았다** — 뒤엣것은 구현 사정이다.
- ★ **부적용인 창** — 이 주제에는 **시각·로캘·난수·순서 비보장 출력이 한 칸도 없다.**
  「여러 번 돌려 흔들림을 본다」는 창이 **잴 것이 없어** 부적용이다. 그 덕에 같은 판에서는 한 글자도 안 변한다.

**판이 올랐을 때 다시 돌려야 하는 것**

- ★★ **예외 메시지 문구** — 여섯 블록에 들어 있다. 특히 **「없다」와 「잠겼다」를 가르는 두 문구**.
- ★★ **Node 의 모듈 래퍼가 그대로인지** — 인자 개수가 바뀌면 `arguments.length` 가 `5` 가 아니게 된다.
- ★ **두 판 대조 결과** — 지금은 전부 같다. 갈리면 그것이 곧 그 주제의 결론이 된다.
- **선언과 스코프의 규칙 자체는 다시 돌릴 필요가 없다** — `let`/`const` 가 들어온 ES2015 이후 바뀐 적이 없다.
