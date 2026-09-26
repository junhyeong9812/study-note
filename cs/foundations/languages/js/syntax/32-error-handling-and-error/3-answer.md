# js/syntax/32 — 오류 처리와 `Error`: 「`finally` 가 끝을 쥐면 `try` 의 끝은 사라진다 · `cause` 는 손으로 잇는다」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **node v20.19.6**(기본 판) · **node v18.19.1**(대조) · **Google Chrome 151.0.7922.173**(6번의 `.web.js`) · **python3 3.12.3**(9번) · x86-64 Linux 에서 실제로 돌려 얻은 것이고,
> 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 하나도 없다).
>
> ★★ **예외는 `이름 「메시지」` 꼴로** 찍었다 — 스택트레이스에는 절대 경로가 박혀 재현이 안 된다. 5번의 둘째 블록만 `node -e` 의 표준 오류 전문이다(경로 대신 `[eval]`).
> ★★ **이 주제에서 두 node 판이 갈린 탐침은 없다**(대조기의 `identical`).
>
> **이 파일이 인용하는 출력을 낸 소스** — 전문은 [1-question.md](1-question.md) 의 같은 번호 문항에 있다.
> `js32b-32a-finally-grid.js`(1번 · 7번) · `js32b-32b-finally-details.js`(2번 · 7번) · `js32b-32c-cause-chain.js`(3번 · 8번) · `js32b-32d-hierarchy.js`(4번) ·
> `js32b-32e-thrown-values.js` 와 `js32b-32i-uncaught.sh`(5번 · 8번) · `js32b-32g-iserror-node.js` 와 `js32b-32h-iserror.web.js`(6번 · 8번 · 10번) · `js32b-32f-python-contrast.sh` 와 `js32b-32-h-pyerr.py`(9번).

## 정답

### 1. **`finally` 가 `return`·`throw` 로 끝난 여섯 칸은 전부 `finally` 의 것**이 나간다 — `try` 의 끝이 닿지 못한 칸 `6 / 9` · 던진 행 중 예외가 사라진 행 `2 / 3` ★★★

**출력**

```text
===== node20 js32b-32a-finally-grid.js (exit=0) =====
[1] try x finally -- what the caller receives
  try ends with     finally ends with  try's own ending reached the caller?  log                     caller receives
  return 'T'        return 'F'         no                                    try > finally           value "F"
  return 'T'        throw E('F')       no                                    try > finally           Error 「F」
  return 'T'        (nothing)          yes                                   try > finally           value "T"
  throw E('T')      return 'F'         no                                    try > finally           value "F"
  throw E('T')      throw E('F')       no                                    try > finally           Error 「F」
  throw E('T')      (nothing)          yes                                   try > finally           Error 「T」
  (falls through)   return 'F'         no                                    try > finally           value "F"
  (falls through)   throw E('F')       no                                    try > finally           Error 「F」
  (falls through)   (nothing)          yes                                   try > finally > after   value "after"

rows where try threw and the caller never saw that exception: 2 / 3
cells where the try block's own ending did not reach the caller: 6 / 9
```

**왜 그런가**

- ★★★ **`finally` 가 아무 말 없이 끝난 세 행만 `yes`** 다 — `value "T"` · `Error 「T」` · `value "after"`. 나머지 여섯 행은 `try` 가 무엇이었든 **`value "F"` 아니면 `Error 「F」`** 다.
- ★★★ **`throw E('T')` × `return 'F'` 는 예외를 삼킨다** — 호출자는 `value "F"` 를 받고, 예외가 있었다는 것조차 모른다. **`throw E('T')` × `throw E('F')` 는 바꿔치기**다.
- ★★ **`after` 는 마지막 행 하나에만** 찍혔다 — `finally` 가 끝을 쥐면 `try` 뒤의 문장도 안 돈다. `log` 는 아홉 행 모두 `try > finally` 로 시작한다(**`finally` 는 늘 돈다**).
- ★ 마지막 두 줄 **`2 / 3`** 과 **`6 / 9`**. 명세의 한 문장이 전부를 만든다(7번).

### 2. **반환값은 `finally` 전에 정해지고**, `break`·`continue` 도 예외를 삼키며, 바꿔치기한 예외에는 **흔적이 없다** ★★★

**출력**

```text
===== node20 js32b-32b-finally-details.js (exit=0) =====
[1] return x, then finally changes x
  primitive: return n; finally n = 2            value 1
  object: return o; finally o.v = 2             value {"v":2}
    log: return expr > finally
  order of evaluation                           value "R"
[2] break / continue inside finally, with an exception in flight
  for: try throw; finally break                 value "after loop"
  for: try throw; finally continue              value "after loop, n=3"
  label: try return; finally break out          value "after block"
[3] catch and finally together
  try throw; catch returns; finally logs        value "C"
    order                                       try > catch > finally
  try throw; catch throws; finally returns      value "F"
  try throw; catch throws; finally (nothing)    Error 「C」
[4] the replacing exception -- does it point back to the one it replaced?
  caught.message                                F
  'cause' in caught                             false
  own keys of caught                            ["stack","message"]
```

**왜 그런가**

- ★★★ **`[1]` 원시값은 `value 1`, 객체는 `value {"v":2}`** — `return n` 이 값 1 을 **먼저** 담았고, 객체는 **같은 객체**를 담았다. 로그가 `return expr > finally` 다.
- ★★★ **`[2]` 세 줄 모두 예외(또는 `return`)가 사라졌다** — `finally { break; }` 는 `after loop`, `finally { continue; }` 는 세 번 던진 예외를 세 번 다 삼켜 `n=3`, `break out` 은 `return "T"` 를 삼켜 `after block`.
- ★★ **`[3]` `try > catch > finally`** — `catch` 의 `"C"` 가 나간다. `catch` 가 던진 `Error 「C」` 는 `finally` 가 `return "F"` 하면 삼켜지고(`value "F"`), `finally` 가 조용하면 그대로 올라온다(`Error 「C」`).
- ★★★ **`[4]` `message` 는 `F`, `'cause' in caught` 는 `false`, own 키는 `["stack","message"]`** — 원래 예외 `T` 를 가리키는 것이 **아무것도 없다.** (`stack` 이 own 인 것은 V8 의 사정 — 5번.)

### 3. 사슬은 **세 층** — `TypeError` → `Error` → `SyntaxError` → `undefined` · `cause` 는 **옵션에 키가 있을 때만** 붙는 비열거 own 프로퍼티 ★★★

**출력**

```text
===== node20 js32b-32c-cause-chain.js (exit=0) =====
[1] three layers, each wrapping the one below
  depth 0  TypeError 「app failed to start」
    depth 1  Error 「settings could not be loaded」
      depth 2  SyntaxError 「Unexpected token } in config.json」
[2] what the option actually creates
  new Error('m', { cause: 1 }) -> cause                   {"value":1,"writable":true,"enumerable":false,"configurable":true}
  hasOwn(new Error('m'), 'cause')                         false
  hasOwn(new Error('m', {}), 'cause')                     false
  hasOwn(new Error('m', { cause: undefined }), 'cause')   true
  new Error('m', 'text').cause                            undefined
  JSON.stringify(new Error('m', { cause: 1 }))            {}
[3] how the constructor reads the option (a Proxy logs every trap)
  traps                                                   has cause > get cause
[4] a cause that is not an Error, and a cause chain that loops
  typeof s.cause                                          string
  walk with a seen-set                                    b -> a -> (seen before: b)
```

**왜 그런가**

- ★★★ **`[1]` 세 줄** — `depth 0 TypeError 「app failed to start」` · `depth 1 Error 「settings could not be loaded」` · `depth 2 SyntaxError 「Unexpected token } in config.json」`. 각 `catch` 가 `{ cause: e }` 를 **손으로 넘겼기 때문에** 이어졌다.
- ★★★ **`[2]` `enumerable:false`** 인 데이터 프로퍼티다. `hasOwn` 은 **옵션 없음 `false` · `{}` `false` · `{ cause: undefined }` `true`**. 문자열 옵션은 무시되어 `undefined`. **`JSON.stringify` 는 `{}`**(비열거는 안 나온다 — 31번).
- ★★ **`[3]` `has cause > get cause`** — 두 번 묻는다. 먼저 **키가 있나**, 있으면 **값을 읽는다**(8번).
- ★★ **`[4]` `typeof s.cause` 는 `string`**, 고리 걷기는 **`b -> a -> (seen before: b)`** 에서 멈춘다 — `seen` 집합이 없으면 끝나지 않는다.

### 4. 언어가 고르는 생성자는 **명세가 정한다** · 일곱 하위 생성자는 **전부 `Error` 의 자식이고 브랜드가 같다** · 상속한 클래스의 `name` 은 **`"Error"`** ★★

**출력**

```text
===== node20 js32b-32d-hierarchy.js (exit=0) =====
[1] which constructor the language itself picks
  null.x                                  TypeError       instanceof Error true
  new Array(-1)                           RangeError      instanceof Error true
  JSON.parse('{')                         SyntaxError     instanceof Error true
  notDeclaredAnywhere                     ReferenceError  instanceof Error true
  decodeURIComponent('%')                 URIError        instanceof Error true
  (1).toFixed(101)                        RangeError      instanceof Error true
  Symbol() + ''                           TypeError       instanceof Error true
  new Function('return (')                SyntaxError     instanceof Error true
[2] the family tree
  TypeError                               proto of ctor: Error   name on prototype: true   tag [object Error]
  RangeError                              proto of ctor: Error   name on prototype: true   tag [object Error]
  SyntaxError                             proto of ctor: Error   name on prototype: true   tag [object Error]
  ReferenceError                          proto of ctor: Error   name on prototype: true   tag [object Error]
  EvalError                               proto of ctor: Error   name on prototype: true   tag [object Error]
  URIError                                proto of ctor: Error   name on prototype: true   tag [object Error]
  AggregateError                          proto of ctor: Error   name on prototype: true   tag [object Error]
[3] message, name, and String(e)
  new Error().message                     ""
  hasOwn(new Error(), 'message')          false
  new Error(42).message                   "42"
  String(new TypeError('bad'))            TypeError: bad
  String(new TypeError())                 TypeError
  new NotFound('x').name                  Error
  new NotFound2('x').name                 NotFound2
  String(new NotFound2('x'))              NotFound2: x
  new NotFound2('x', { cause: 1 }).cause  1
[4] AggregateError -- one error holding several
  ag.message                              two failed
  ag.errors.length                        2
  ag.errors kinds                         RangeError, TypeError
  ag.errors[1].cause                      deep
  ag.cause                                top
  Array.isArray(ag.errors)                true
  descriptor of errors                    {"value":"[...]","writable":true,"enumerable":false,"configurable":true}
  errors copied from the iterable?        2 (source now 3)
  Promise.any rejects with                AggregateError 「All promises were rejected」
    its errors                            ["Error a","b"]
```

**왜 그런가**

- ★★ **`[1]`** — `null.x` `TypeError` · `new Array(-1)` `RangeError` · `JSON.parse('{')` `SyntaxError` · 선언 안 된 이름 `ReferenceError` · `decodeURIComponent('%')` `URIError` · `toFixed(101)` `RangeError` · `Symbol() + ''` `TypeError` · `new Function('return (')` `SyntaxError`. 여덟 모두 `instanceof Error true`.
- ★★ **`[2]` 일곱 줄의 세 칸이 모두 같다** — 부모 `Error`, `name` 은 각자의 `prototype` 에, 브랜드 `[object Error]`. **브랜드로는 종류를 못 가른다.**
- ★★★ **`[3]` `NotFound` 는 `Error`, `NotFound2` 는 `NotFound2`** — `name` 은 프로토타입에서 읽히므로 직접 넣어야 한다. `message` 를 안 주면 own `message` 가 **없다**(`false`).
- ★★ **`[4]` `errors.length` 2 · 원본에 `push` 해도 `2 (source now 3)`**(복사) · `Promise.any` 는 **`AggregateError 「All promises were rejected」`**, `errors` 는 `["Error a","b"]` — 거부 이유가 **그대로** 들어간다.

### 5. **`stack` 은 `Error` 에만** 있고 `null`·`undefined` 에서는 읽는 순간 던진다 · 아무도 안 받은 문자열에는 **호출 경로가 없다** ★★

**출력**

```text
===== node20 js32b-32e-thrown-values.js (exit=0) =====
[1] what catch receives
  throw 'disk full'                 typeof string    e.stack -> undefined
  throw 404                         typeof number    e.stack -> undefined
  throw { code: 'E1' }              typeof object    e.stack -> undefined
  throw null                        typeof null      e.stack -> TypeError 「Cannot read properties of null (reading 'stack')」
  throw undefined                   typeof undefined e.stack -> TypeError 「Cannot read properties of undefined (reading 'stack')」
  throw new Error('disk full')      typeof object    e.stack -> "Error: disk full"
[2] where stack lives on a real Error (V8)
  hasOwn(e, 'stack')                true
  descriptor kind                   data, enumerable false
  'stack' in Error.prototype        false
  typeof Error.captureStackTrace    function
  Error.stackTraceLimit             10
  after captureStackTrace(plain)    "Error: not an error"
```

```text
===== ./js32b-32i-uncaught.sh (exit=0) =====
--- node20 -e 'throw "disk full"'

[eval]:1
throw "disk full"
^
disk full
(Use `node --trace-uncaught ...` to show where the exception was thrown)

Node.js v20.19.6
(exit 1)
--- node20 -e 'throw { code: "E1" }'
[eval]:1
throw { code: "E1" }
^

{ code: 'E1' }

Node.js v20.19.6
(exit 1)
--- node20 -e 'throw new Error("disk full")'
[eval]:1
throw new Error("disk full")
^

Error: disk full
    at [eval]:1:7
    at runScriptInThisContext (node:internal/vm:209:10)
    at node:internal/process/execution:118:14
    at [eval]-wrapper:6:24
    at runScript (node:internal/process/execution:101:62)
    at evalScript (node:internal/process/execution:133:3)
    at node:internal/main/eval_string:51:3

Node.js v20.19.6
(exit 1)
```

**왜 그런가**

- ★★★ **`[1]`** — 문자열·숫자·평범한 객체는 `e.stack -> undefined`, **`null`·`undefined` 는 `TypeError`**(읽다가 던진다), `Error` 만 `"Error: disk full"`.
- ★★ **`[2]` 이 node 20 에서는 own 데이터**(`data, enumerable false`), `Error.prototype` 에는 없다. `stack` 은 **ECMA-262 밖**이다 — Chrome 151 은 접근자였다(6번 `[3]`).
- ★★★ **둘째 블록** — 셋 다 `(exit 1)`. 문자열은 값 아래 ``(Use `node --trace-uncaught ...` to show where the exception was thrown)`` 안내가 붙고, 객체는 `{ code: 'E1' }`, `Error` 는 `Error: disk full` 다음에 `at [eval]:1:7` 부터 **호출 경로**가 찍힌다.

### 6. 다른 realm 의 오류는 **`instanceof Error` 가 `false`, `Error.isError` 는 `true`** — node `vm` 과 Chrome iframe 이 같았다 ★★★

**출력**

```text
===== node20 js32b-32g-iserror-node.js (exit=0) =====
  typeof Error.isError                        undefined
  Error.isError(new Error('x'))               TypeError 「Error.isError is not a function」
  other instanceof Error                      false
  other instanceof TypeError                  false
  other.constructor === TypeError             false
  Object.prototype.toString.call(other)       [object Error]
  util.types.isNativeError(other)  (host)     true
  other.name / other.message                  TypeError / from another realm
```

```text
===== google-chrome --headless --virtual-time-budget=2000 --dump-dom 'js32b-page.html?js32b-32h-iserror.web.js' | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' | sed 's/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&amp;/\&/g' (exit=0) =====
[1] one question, three ways to ask it
                                                    Error.isError  instanceof Error  toString
  new Error('x')                                    true           true              [object Error]
  new (class E2 extends Error {})()                 true           true              [object Error]
  new AggregateError([])                            true           true              [object Error]
  iframe: new W.TypeError('x')                      true           false             [object Error]
  Object.create(Error.prototype)                    false          true              [object Object]
  { name: 'Error', message: 'x' }                   false          false             [object Object]
  { [Symbol.toStringTag]: 'Error' }                 false          false             [object Error]
  new Proxy(new Error('x'), {})                     false          true              [object Object]
  new DOMException('x')  (host)                     true           true              [object DOMException]
[2] non-objects
  Error.isError('Error: x') / (null) / ()           false / false / false
[3] where stack lives on a real Error (this V8)
  hasOwn(e, 'stack')                                true
  descriptor kind                                   accessor, enumerable false
  'stack' in Error.prototype                        false
  first line of e.stack                             "Error: m"
```

**왜 그런가**

- ★★★ **node 20 — `typeof Error.isError` 는 `undefined`**, 부르면 `TypeError 「Error.isError is not a function」`. 다른 realm 의 오류는 `instanceof Error`·`instanceof TypeError`·`constructor === TypeError` 가 **전부 `false`** 인데 브랜드는 `[object Error]`, 호스트 함수 `util.types.isNativeError` 는 `true`.
- ★★★ **Chrome `[1]` — 두 열이 갈린 행은 셋** — iframe 오류(`true`/`false`) · `Object.create(Error.prototype)`(`false`/`true`) · `Proxy`(`false`/`true`).
- ★★ **`Proxy` 는 `Error.isError` 가 `false`** — 슬롯은 대상에 있다. **`DOMException` 은 `true`/`true`**(호스트 객체 — Chrome 의 관찰). **브랜드를 위조한 객체는 `false`/`false`** — 브랜드 열만 `[object Error]` 로 속았다.
- ★ **`[3]` 접근자**(`accessor, enumerable false`) — node 20 의 데이터와 다르다.

### 7. 「**`F` 가 정상 완료면 `F` 를 `B` 로 바꾼다**」 — 삼킴은 이 규칙의 뒷면이다 ★★★

- ★★★ `B` 는 `Block` 을 평가한 완료 기록, `F` 는 `Finally` 를 평가한 완료 기록이다. **`F` 가 정상일 때만 `B` 가 나가고**, `F` 가 `return`·`throw`·`break`·`continue` 면 `F` 가 나간다.
- ★★ **따로 있는 규칙이 아니다** — 「`finally` 가 조용할 때만 앞의 것을 되살린다」의 뒷면이 「`finally` 가 말하면 앞의 것을 버린다」다.
- ★★ `catch` 가 있으면 `B` 가 던진 경우 **`CatchClauseEvaluation` 의 결과 `C`** 가 그 자리에 들어간다. 그래서 2번 `[3]` 의 `catch` 가 던진 `Error 「C」` 도 `finally` 의 `return "F"` 에 버려졌다.
- ★ `return n` 은 **식을 평가한 값**을 완료 기록에 담는다. `finally` 에서 변수를 바꿔도 **이미 담긴 값**은 안 바뀐다.

### 8. `cause` 는 **`HasProperty` → `Get`** 으로 명세가 정하고, `stack` 은 **명세 밖**이다 ★★

- ★★★ **`HasProperty(options, "cause")` 가 먼저, 참이면 `Get`** — 그래서 **키만 있고 값이 `undefined`** 여도 own `cause` 가 생긴다(3번 `[2]`).
- ★★ `cause`·`message`·`errors`·`stack` 이 **전부 비열거**라 `JSON.stringify(err)` 는 `{}`, `Object.keys` 도 빈 배열이다. 로그에는 **칸을 골라** 담아야 한다.
- ★★★ **`stack` 은 ECMA-262 에 없다** — node 20 은 own **데이터**, Chrome 151 은 own **접근자**로 서로 달랐다(5번 · 6번).

### 9. 원인 사슬은 세 언어가 같은 모양 · **바꿔치기의 흔적은 파이썬만 자동으로 남긴다** · `finally` 의 `return` 은 셋 다 삼킨다 ★★

**출력**

```text
===== ./js32b-32f-python-contrast.sh (exit=0) =====
python3.14: not found
python3.13: not found
python3.12: Python 3.12.3
python3.11: Python 3.11.15
--- python3.12 -W error - < js32b-32-h-pyerr.py
[1] raise ... from e -- walk __cause__ to the end
  depth 0 TypeError 「app failed to start」
    depth 1 RuntimeError 「settings could not be loaded」
      depth 2 SyntaxError 「Unexpected token } in config.json」
[2] finally raises while another exception is in flight
  caught         KeyError 「'F'」
  __cause__      None
  __context__    ValueError 「T」
[3] return inside finally, with an exception in flight
  swallow() -> 'F'
(exit 0)
```

- ★★★ 파이썬 `[2]` 의 **`__context__` 는 `ValueError 「T」`** — 바꿔치기된 예외가 **자동으로** 걸렸다. JS 는 2번 `[4]` 에서 **아무것도 없었다**(`'cause' in caught false`).
- ★★ **3.12 는 `-W error` 에서도 조용했다**(`swallow() -> 'F'`, `exit 0`). **3.14 는 이 머신에 없어 못 쟀다**(`python3.14: not found`) — PEP 765 의 경고는 확인하지 않은 채로 둔다.
- ★★ 자바는 **`javac -Xlint` 가 `finally clause cannot complete normally`** 로 알려 준다([Java 25](../../../java/syntax/25-exceptions/2-summary.md) 동작 (5)). JS 는 엔진이 알려 주지 않는다.
- ★ Go 의 **`errors.Unwrap` 을 `nil` 까지 도는 창**이 JS 의 **`for (e = top; e; e = e.cause)`** 다([Go 24](../../../go/syntax/24-error-wrapping-and-errors-is-as-join/2-summary.md)). JS 에는 **`errors.Is`/`As` 같은 표준 함수가 없다** — 직접 걷는다.

### 10. `AggregateError` **ES2021** · `cause` **ES2022** · `Error.isError` **ES2026(Chrome 151 에만)** · 비동기는 **37·39번** · 판정은 **34번** · 정리 예외는 **51번** ★★

- ★★★ TC39 finished proposals — `Promise.any`(와 `AggregateError`) **2021**, Error Cause **2022**, `Error.isError` **2026**. 판별 블록에서 앞의 둘은 **세 판 다 `yes`**, `Error.isError` 는 **node 18·20 `no`, Chrome 151 `yes`**.
- ★★ 프로미스 거부는 목록의 **37번 주제**, `await` 의 `try`/`catch` 는 목록의 **39번 주제**.
- ★★ [34 — 타입 검사 관용구](../34-type-checking-idioms/2-summary.md) — realm 격자의 정본.
- ★ **`SuppressedError`**(`using` 의 정리 중 예외) — 목록의 **51번 주제**.

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js32b-32a-finally-grid.js` | ★★★ `try` 3 × `finally` 3 격자 · 「`6 / 9`」 · 「`2 / 3`」 | node20 1벌 + node18 대조 1벌 |
| `js32b-32b-finally-details.js` | ★★★ 반환값의 시점 · `break`/`continue` · `catch` 순서 · 바꿔치기의 흔적 | node20 1벌 + node18 대조 1벌 |
| `js32b-32c-cause-chain.js` | ★★★ `cause` 사슬 · 서술자 · `has`→`get` 로그 · 고리 | node20 1벌 + node18 대조 1벌 |
| `js32b-32d-hierarchy.js` | ★★ 언어가 고르는 생성자 · 가족 트리 · `name` · `AggregateError` | node20 1벌 + node18 대조 1벌 |
| `js32b-32e-thrown-values.js` · `js32b-32i-uncaught.sh` | ★★ `Error` 아닌 값 · `stack` 의 자리(V8) · 안 받은 `throw` 의 표준 오류 | node20 1벌(+ `.js` 는 node18 대조) |
| `js32b-32g-iserror-node.js` | `Error.isError` 가 node 에 있나 · `vm` realm 의 오류 | node20 1벌 + node18 대조 1벌 |
| `js32b-32h-iserror.web.js` | ★★★ `Error.isError` 대 `instanceof Error` · iframe realm · Chrome 의 `stack` | **Chrome 151 만** |
| `js32b-32f-python-contrast.sh` · `js32b-32-h-pyerr.py` | 파이썬 대비 · 파이썬 판 목록 | python3.12 1벌 |
| `js32b-vdiff.sh` · `js32b-versions.sh` | 두 판이 갈린 탐침 수 · 판별 기능 표 | 1벌씩 |

두 node 판 대조기(이 배치 전체의 node 탐침). `DIFFERS` 가 한 줄도 없다.

```sh
# js32b-vdiff.sh
#!/usr/bin/env bash
# 두 node 판이 갈린 탐침이 몇 개인가 -- 스크립트가 직접 센다(브라우저 탐침 *.web.js 와 셸 탐침 *.sh 는 대상이 아니다).
set -u -o pipefail
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
cd "$(dirname "$0")"
same=0; diffn=0
for f in js32b-3[2345]?-*.js; do
  [ -e "$f" ] || continue
  case $f in *.web.js) continue ;; esac
  a="$("$N18" "$f" 2>&1)"
  b="$("$N20" "$f" 2>&1)"
  if [ "$a" = "$b" ]; then
    printf '%-40s identical\n' "$f"; same=$((same + 1))
  else
    printf '%-40s DIFFERS\n' "$f"; diffn=$((diffn + 1))
    diff <(printf '%s\n' "$a") <(printf '%s\n' "$b") | sed 's/^/    /'
  fi
done
echo ""
echo "identical $same  ·  differs $diffn  ·  total $((same + diffn))"
```

```text
===== ./js32b-vdiff.sh (exit=0) =====
js32b-32a-finally-grid.js                identical
js32b-32b-finally-details.js             identical
js32b-32c-cause-chain.js                 identical
js32b-32d-hierarchy.js                   identical
js32b-32e-thrown-values.js               identical
js32b-32g-iserror-node.js                identical
js32b-33a-new-places.js                  identical
js32b-33c-typed-and-string.js            identical
js32b-34a-realm-grid.js                  identical
js32b-34c-array-edges.js                 identical
js32b-35a-new-cells.js                   identical
js32b-35b-directive.js                   identical

identical 12  ·  differs 0  ·  total 12
```

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- ★★★ **`Error.isError`** — node 가 ES2026 을 받으면 `js32b-32g-iserror-node.js` 가 `function` 을 답할 것이다. 그때 `js32b-32h-iserror.web.js` 의 `[1]` 을 node 로도 돌린다.
- ★★ **`stack` 의 자리**(데이터 대 접근자) — 이미 node 20 과 Chrome 151 이 다르다.
- ★ 예외 **문구**와 `node:internal/…` 줄 번호 — V8·node 의 것이다.
- ★ 파이썬 **3.14** 가 생기면 `finally` 의 `return` 경고(PEP 765)를 잰다.
