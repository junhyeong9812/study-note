# js/syntax/10 — 구조 분해 할당: 「왼쪽은 값이 아니라 모양이다」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **node v20.19.6**(기본 판) · **node v18.19.1**(대조) · **Google Chrome 151.0.7922.173** · x86-64 Linux 에서 실제로 돌려 얻은 것이고,
> 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 하나도 없다).
>
> ★★ **예외는 `e.constructor.name` 과 `e.message` 로만 찍었다** — 스택트레이스에는 절대 경로가 박혀 재현이 안 된다.
> ★★★ **문구에 박히는 변수 이름은 근거가 아니다** — V8 은 그 자리의 소스 텍스트를 메시지에 넣는다.
> ★★ **표준 출력과 표준 오류를 한 블록에도 안 섞었다** — 이 주제의 블록은 전부 표준 출력이다.
>
> **이 파일이 인용하는 출력을 낸 소스** — 전문은 [1-question.md](1-question.md) 의 같은 번호 문항에 있다.

```text
// js08b-10a-forms.js
// js08b-10b-failures.js
// js08b-10c-order.js
// js08b-10d-params.js
// js08b-10h-browser.js
// js08b-10x-forms.js
// js08b-vdiff.sh
// js08b-versions.sh
```

> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | Node 스택트레이스의 **절대 경로** — 한 줄도 싣지 않았다 | ★★★ **예외의 종류** · **터진 칸의 개수** |
> | 예외 **문구** · 문구에 박히는 **변수 이름** | ★★★ **getter·`next` 호출 순서와 횟수** |
> | 브라우저 UA 문자열의 뒷자리 | ★★ **`length` 값** · 객체 나머지가 무엇을 복사하는지 |
>
> ★ **이 주제의 블록에는 주소도 시간도 난수도 안 찍힌다.** 같은 판에서 다시 돌리면 한 글자도 안 변한다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 네 묶음을 뜯으면 — **왼쪽 모양이 읽는 문을 정한다** ★★

**출력**

```text
===== node20 js08b-10a-forms.js (exit=0) =====
[1] array pattern -- position decides
  const [a, b] = [1, 2]                        -> [1,2]
  const [, b] = [1, 2]  hole                   -> 2
  const [a, , c] = [1, 2, 3]                   -> [1,3]
  const [a, b, c] = [1, 2]  short              -> [1,2,"<undefined>"]
  const [a, ...r] = [1, 2, 3]                  -> [1,[2,3]]
  const [a, ...r] = [1]                        -> [1,[]]
  const [[x], [y]] = [[1], [2]]                -> [1,2]
  const [a, b] = 'hi'  string                  -> ["h","i"]
  const [a, b] = new Set([1, 2])               -> [1,2]
  const [[k, v]] = new Map([['x', 1]])         -> ["x",1]

[2] object pattern -- the key decides, order does not
  const { a, b } = { b: 2, a: 1 }              -> [1,2]
  const { a: x } = { a: 1 }  rename            -> 1
  const { a: { b } } = { a: { b: 1 } }         -> 1
  const { missing } = { a: 1 }                 -> "<undefined>"
  const { a, ...rest } = { a: 1, b: 2, c: 3 }  -> [1,{"b":2,"c":3}]
  const { [key]: v } = { dyn: 9 }  computed    -> 9
  const { length } = 'abc'  primitive          -> 3
  const { toFixed } = 7  from prototype        -> function
  const { 0: first } = ['a', 'b']  index key   -> "a"
  const { [sym]: sv } = { [sym]: 1 }           -> 1

[3] what object rest copies -- and what it leaves behind
  own enumerable string keys                   -> ["b","getter"]
  non-enumerable 'hidden' copied?              -> false
  symbol key copied?                           -> true
  inherited 'inherited' copied?                -> false
  getter copied as a value?                    -> {"value":5,"writable":true,"enumerable":true,"configurable":true}
  prototype of the rest object                 -> true
  rest is a shallow copy                       -> {"inner":{"n":99}}

[4] assignment without a declaration -- the parentheses are not optional
  ({ a: A } = { a: 1 })                        -> 1
  [p, q] = [1, 2]  no parens needed            -> [1,2]
  swap: [p, q] = [q, p]                        -> [2,1]
  { a: A } = { a: 1 }  without parens          -> SyntaxError: Unexpected token '='
  target can be a property                     -> {"x":1,"y":2}
  target can be an index                       -> [7]
```

**왜 그런가**

- ★★ **배열이 아닌데 배열 패턴으로 뜯어진 것은 셋**이다 — 문자열(`'hi'`) · `Set` · `Map`.
  **배열 패턴은 이터러블이면 받는다.** `Map` 은 원소가 `[키, 값]` 쌍이라 중첩 패턴으로 한 번에 뜯힌다.
- ★★★ **원시값을 객체 패턴으로 뜯으면 임시 래퍼에서 읽는다.**
  `const { length } = "abc"` 가 `3` 이고 `const { toFixed } = 7` 이 `function` 이다.
  근거는 [01번](../01-value-types-and-typeof/2-summary.md)의 **원시값 임시 래핑**이다 —
  ★ 래퍼 객체가 만들어졌다가 읽고 나면 버려진다.
  ★ **인덱스를 키로 읽을 수도 있다** — `const { 0: first } = ["a","b"]` 는 이터레이터를 안 탄다.
- ★★★ **객체 나머지가 안 가져오는 것 셋** — **비열거 프로퍼티**(`hidden`) · **상속된 프로퍼티**(`inherited`) ·
  그리고 **`a` 자신**(앞에서 이미 뽑혔다). **심볼 키는 가져온다.**
  ★★ **getter 는 「그때 부른 값」으로 굳는다** — 복사본의 디스크립터가 `{"value":5,"writable":true,...}` 다.
  ★★ **그리고 얕다** — `{ ...nested }` 를 만든 뒤 `shallow.inner.n = 99` 를 하니 **원본이 바뀌었다.**
- ★★ **줄 첫머리의 `{` 는 블록으로 파싱된다.** 그래서 `{ a: A } = { a: 1 }` 이
  `SyntaxError: Unexpected token '='` 이다 — **패턴으로 읽히기 전에 문(statement)으로 읽힌 것**이다.
  ★ 배열 패턴은 `[` 로 시작해도 문이 될 여지가 없어 괄호가 필요 없다.
  ★ **대입 대상은 변수가 아니어도 된다** — `[t.x, t.y] = [1,2]` 도 `({ a: t[0] } = { a: 7 })` 도 된다.

### 2. 값 열다섯 × 패턴 넷 — **60칸 중 28칸이 터졌다** ★★★

**출력**

```text
===== node20 js08b-10b-failures.js (exit=0) =====
[1] value x pattern -- what comes out, or what is thrown
  value             { a }           {}              [a]             []
  { a: 1 }          a=1             ok              TypeError       TypeError
  [1, 2]            a=undefined     ok              a=1             ok
  'ab'              a=undefined     ok              a=a             ok
  7                 a=undefined     ok              TypeError       TypeError
  0                 a=undefined     ok              TypeError       TypeError
  true              a=undefined     ok              TypeError       TypeError
  false             a=undefined     ok              TypeError       TypeError
  null              TypeError       TypeError       TypeError       TypeError
  undefined         TypeError       TypeError       TypeError       TypeError
  NaN               a=undefined     ok              TypeError       TypeError
  Symbol('s')       a=undefined     ok              TypeError       TypeError
  10n               a=undefined     ok              TypeError       TypeError
  function f() {}   a=undefined     ok              TypeError       TypeError
  new Set([1])      a=undefined     ok              a=1             ok
  { length: 1 }     a=undefined     ok              TypeError       TypeError
  cells thrown      28 of 60

[2] the messages behind the thrown cells
  [a] = { a: 1 }            TypeError: v is not iterable
  [] = { a: 1 }             TypeError: v is not iterable
  [a] = 7                   TypeError: v is not iterable
  [] = 7                    TypeError: v is not iterable
  [a] = 0                   TypeError: v is not iterable
  [] = 0                    TypeError: v is not iterable
  [a] = true                TypeError: v is not iterable
  [] = true                 TypeError: v is not iterable
  [a] = false               TypeError: v is not iterable
  [] = false                TypeError: v is not iterable
  { a } = null              TypeError: Cannot destructure property 'a' of 'v' as it is null.
  {} = null                 TypeError: Cannot destructure 'v' as it is null.
  [a] = null                TypeError: v is not iterable
  [] = null                 TypeError: v is not iterable
  { a } = undefined         TypeError: Cannot destructure property 'a' of 'v' as it is undefined.
  {} = undefined            TypeError: Cannot destructure 'v' as it is undefined.
  [a] = undefined           TypeError: v is not iterable
  [] = undefined            TypeError: v is not iterable
  [a] = NaN                 TypeError: v is not iterable
  [] = NaN                  TypeError: v is not iterable
  [a] = Symbol('s')         TypeError: v is not iterable
  [] = Symbol('s')          TypeError: v is not iterable
  [a] = 10n                 TypeError: v is not iterable
  [] = 10n                  TypeError: v is not iterable
  [a] = function f() {}     TypeError: v is not iterable
  [] = function f() {}      TypeError: v is not iterable
  [a] = { length: 1 }       TypeError: v is not iterable
  [] = { length: 1 }        TypeError: v is not iterable

[3] the same two failures are not the same failure
  const { a } = null                   -> TypeError: Cannot destructure property 'a' of 'null' as it is null.
  const [a] = null                     -> TypeError: null is not iterable
  const { a } = {}                     -> undefined
  const [a] = {}                       -> TypeError: {} is not iterable
  const [a] = { length: 1 }            -> TypeError: {(intermediate value)} is not iterable
  const [a] = { 0: 'x', length: 1 }    -> TypeError: {(intermediate value)(intermediate value)} is not iterable
  Array.from({ 0: 'x', length: 1 })    -> ["x"]
  const { a } = Object.create(null)    -> undefined

[4] a default value turns the undefined case into a value -- and only that case
  const { a = 'D' } = { a: undefined }     -> D
  const { a = 'D' } = { a: null }          -> null
  const { a = 'D' } = {}                   -> D
  const { a = 'D' } = null                 -> TypeError: Cannot read properties of null (reading 'a')
  const [a = 'D'] = [undefined]            -> D
  const [a = 'D'] = [null]                 -> null
  const [a = 'D'] = []                     -> D
  const [a = 'D'] = null                   -> TypeError: null is not iterable
  const { a: { b } = {} } = {}             -> undefined
  const { a: { b } } = {}                  -> TypeError: Cannot read properties of undefined (reading 'b')
```

**왜 그런가**

- ★★★ **터진 칸은 28개**다. 두 덩어리로 나뉜다 —
  **`null`·`undefined` 가 네 패턴 모두에서 터진 8칸**과 **이터러블이 아닌 값이 배열 패턴 둘에서 터진 20칸**이다.
- ★★★ **객체 패턴이 거부하는 값은 둘**이다 — `null` 과 `undefined`.
  나머지 열셋은 전부 통과한다(숫자·문자열·불리언·`NaN`·심볼·BigInt·함수·`Set`·유사 배열).
  ★★★ **배열 패턴이 받아들이는 값은 셋**이다 — 배열·문자열·`Set`.
  ★ **두 패턴의 넓이가 정반대**다. 한쪽은 둘만 거부하고 한쪽은 셋만 받는다.
- ★★★ **빈 패턴도 터진다.** `const {} = null` 과 `const [] = null` 이 둘 다 `TypeError` 다.
  ★ **아무것도 안 뜯어도 「뜯을 수 있는 대상인가」는 먼저 묻기 때문**이다.
  객체 패턴은 「객체로 강제할 수 있나」를, 배열 패턴은 「`Symbol.iterator` 가 있나」를 먼저 본다.
- ★★ **`{ a } = null` 과 `{} = null` 의 문구 차이는 프로퍼티 이름의 유무**다 —
  `Cannot destructure property 'a' of 'v' as it is null.` 대 `Cannot destructure 'v' as it is null.`
  ★ **뽑으려던 키가 있으면 그 이름을 알려 준다.**
- ★★★ **`const { a } = {}` 와 `const [a] = {}` 를 가른 것은 왼쪽 모양 하나**다.
  같은 빈 객체인데 객체 패턴은 `undefined` 를 주고 배열 패턴은 `{} is not iterable` 로 터진다.
  ★★ **읽는 문이 다르다** — 프로퍼티 조회는 없는 키를 `undefined` 로 답하고, 이터레이터는 **없으면 그 자리에서 거부**한다.
  ★ `Array.from({0:'x',length:1})` 은 `["x"]` 인데 같은 값에 배열 패턴을 대면 터진다 —
  **`Array.from` 은 유사 배열도 보고 구조 분해는 안 본다.**
- ★★★ **`{ a = 'D' } = { a: null }` 은 `null`** 이다. **기본값은 `null` 을 구해 주지 않는다.**
  ★★ **대상이 `null` 인 것도 못 구한다** — `{ a = 'D' } = null` 은 여전히 `TypeError` 다.
  ★ 다만 **문구가 바뀐다** — `Cannot read properties of null (reading 'a')` 다. **종류는 같고 말이 다르다.**
- ★★ **기본값을 어디에 다느냐가 갈린다.** `{ a: { b } = {} } = {}` 는 통과하고 `{ a: { b } } = {}` 는 터진다.
  ★ 앞엣것은 「**안쪽 모양을 댈 대상이 없으면 `{}` 를 쓰라**」는 뜻이고, 뒤엣것은 그 대비가 없어
  `undefined` 에 객체 패턴을 대게 된다.

### 3. 로그를 심으면 무엇이 보이나 — **두 패턴이 서로 다른 문을 쓴다** ★★★

**출력**

```text
===== node20 js08b-10c-order.js (exit=0) =====
[1] object pattern -- the pattern's order wins, not the object's
  const { a, b } = src                    ["get a","get b"]
  const { b, a } = src                    ["get b","get a"]
  const { a } = src                       ["get a"]
  const {} = src                          []
  const { ...all } = src                  ["get b","get a","get c"]
  const { a, ...rest } = src              ["get a","get b","get c"]

[2] a default is evaluated only when the slot is undefined
  { present = d(1) }                      []
  { undef = d(2) }                        ["default 2"]
  { nul = d(3) }                          []
  { missing = d(4) }                      ["default 4"]
  { absent: renamed = d(5) }              ["default 5"]

[3] array pattern goes through the iterator protocol, not through indexes
  const [a, b] = tracked(3 items)         ["Symbol.iterator","next 0","next 1","return"]
  const [a] = tracked(3 items)            ["Symbol.iterator","next 0","return"]
  const [] = tracked(3 items)             ["Symbol.iterator","return"]
  const [a, ...r] = tracked(3 items)      ["Symbol.iterator","next 0","next 1","next 2","next 3"]
  const [a,b,c,d] = tracked(2 items)      ["Symbol.iterator","next 0","next 1","next 2"]
  const [, , third] = tracked(3)          ["Symbol.iterator","next 0","next 1","next 2","return"]

[4] the array's own iterator can be replaced -- destructuring follows it
  const [first, second] = arr             [30,20]
  arr[0], arr[1] are still                [10,20]
  object pattern reads keys instead       [10,20]

[5] a failing pattern still closes the iterator
  const [a, { b }] = throwing()           ["next","next","return called","threw TypeError"]
  const [a, b] = throwing()  plain        ["next","next","return called"]
```

**왜 그런가**

- ★★★ **`{ a, b }` 와 `{ b, a }` 의 로그가 다르다** — 각각 `["get a","get b"]` 와 `["get b","get a"]` 다.
  **읽는 순서는 패턴의 순서**이지 객체의 키 순서가 아니다.
  ★ 빈 패턴은 **아무 getter 도 안 부른다**(`[]`).
- ★★ **`{ ...all }` 은 셋을 다 읽는다.** 그 순서는 **객체의 키 순서**(`b`,`a`,`c`)다 —
  나머지는 「남은 것 전부」라 **패턴이 순서를 못 정한다.**
  ★ `{ a, ...rest }` 는 **`a` 를 먼저 읽고** 그 다음 나머지를 키 순서로 읽는다.
- ★★★ **`const [a, b] = it(3)` 은 `next` 를 두 번 부르고 `return` 을 부른다.**
  필요한 만큼만 돌고 **다 안 돌았으니 닫아 준다.**
  ★★★ **`const [a, ...r] = it(3)` 은 `return` 을 안 부른다** — `next` 를 네 번 불러 `done` 을 받았기 때문이다.
  **이미 끝난 이터레이터는 닫을 것이 없다.**
  ★ **`const [] = it(3)` 도 이터레이터를 얻는다** — 「뜯을 수 있는 대상인가」를 먼저 묻기 때문이다. 그리고 곧바로 닫는다.
  ★ **구멍은 건너뛰는 것이 아니라 버리는 것**이다 — `[, , third]` 가 `next` 를 세 번 부른다.
- ★★★ **`[4]` 는 「배열 패턴이 인덱스를 안 읽는다」의 증명**이다.
  배열의 `Symbol.iterator` 를 뒤집어 놓으니 `[first, second]` 가 `[30, 20]` 인데
  `arr[0]`, `arr[1]` 은 여전히 `[10, 20]` 이고, **같은 배열을 객체 패턴으로 읽으면 `[10, 20]`** 이 나온다.
  ★★ **한 값에 두 패턴을 대면 서로 다른 답이 나온다** — 두 문이 다르다는 가장 강한 근거다.
- ★★ **`[5]` 는 자원 보장**이다. 안쪽 패턴이 터지는데도 `return called` 가 **예외보다 먼저** 찍혔다.
  ★ **다 못 돌고 빠져나갈 때는 무슨 이유든 닫는다** — 제너레이터의 `finally` 가 도는 자리다([목록의 **20번 주제**](../20-generators/)).

### 4. 매개변수 자리와 설정에 달린 칸 — **열둘 중 둘** ★★

**출력**

```text
===== node20 js08b-10d-params.js (exit=0) =====
[1] sloppy vs strict -- same probe, compiled twice
  no declaration keyword
    sloppy  typeof gObj = number
    strict  ReferenceError: gObj is not defined   <-- DIFFERENT
  array target, no declaration
    sloppy  typeof gArr = number
    strict  ReferenceError: gArr is not defined   <-- DIFFERENT
  f({ a }) called with nothing
    sloppy  TypeError: Cannot destructure property 'a' of 'undefined' as it is undefined.
    strict  TypeError: Cannot destructure property 'a' of 'undefined' as it is undefined.
  f({ a } = {}) called with nothing
    sloppy  undefined
    strict  undefined
  f({ a = 1 } = {}) called with nothing
    sloppy  1
    strict  1
  f([a, b]) called with nothing
    sloppy  TypeError: undefined is not iterable (cannot read property Symbol(Symbol.iterator))
    strict  TypeError: undefined is not iterable (cannot read property Symbol(Symbol.iterator))
  f([a, b]) called with an object
    sloppy  TypeError: object is not iterable (cannot read property Symbol(Symbol.iterator))
    strict  TypeError: object is not iterable (cannot read property Symbol(Symbol.iterator))
  f({ a }, { a })  same name twice
    sloppy  COMPILE SyntaxError: Duplicate parameter name not allowed in this context
    strict  COMPILE SyntaxError: Duplicate parameter name not allowed in this context
  f(a, { a })  name reused
    sloppy  COMPILE SyntaxError: Duplicate parameter name not allowed in this context
    strict  COMPILE SyntaxError: Duplicate parameter name not allowed in this context
  const { a, a } = { a: 1 }
    sloppy  COMPILE SyntaxError: Identifier 'a' has already been declared
    strict  COMPILE SyntaxError: Identifier 'a' has already been declared
  var { a } = {}; var { a } = {}
    sloppy  2
    strict  2
  f({ a }) { 'use strict'; }
    sloppy  COMPILE SyntaxError: Illegal 'use strict' directive in function with non-simple parameter list
    strict  COMPILE SyntaxError: Illegal 'use strict' directive in function with non-simple parameter list

  settings-dependent cells      2 of 12

[2] length and name when the parameter is a pattern
  function ({ a })            length 1
  function ({ a } = {})       length 0
  function ([a, b])           length 1
  function (x, { a })         length 2
  function ({ a }, ...r)      length 1

[3] the shapes that read well in real code
  point()                           p(0,0)
  point({ x: 1 })                   p(1,0)
  point({ y: 2, label: 'q' })       q(0,2)
  entries.map(([k, v]) => ...)      a=1,b=2
  nested pattern in a callback      1:x
  head([1, 2, 3])                   1 / [2,3]
  head()                            undefined / []
```

**왜 그런가**

- ★★★ **설정에 달린 칸은 둘**이다 — **선언 키워드 없이 대입한 두 탐침**이다.
  비엄격은 **암시적 전역**을 만들어 `typeof` 가 `number` 이고, 엄격은 **`ReferenceError`** 다.
  ★ 나머지 열은 두 모드가 같다 — 구조 분해 자체의 규칙은 **모드와 무관**하다.
- ★★★ **이 격자는 엄격 쪽을 먼저 돌려야 한다.** 비엄격이 먼저 돌면 **전역에 이름이 생기고**,
  뒤에 도는 엄격 쪽이 **그 전역을 읽어** 성공해 버린다.
  ★★ 실제로 처음엔 거짓 「**0 / 12**」가 나왔다. 값도 그럴듯하고 에러도 없어서 **눈으로는 안 걸린다.**
  ★★★ **「두 번 컴파일」 격자는 탐침끼리 전역을 통해 새는지 늘 의심해야 한다** — 이 주제가 그 실례다.
- ★★★ **세 모양의 답이 전부 다르다** —
  `f({ a })` 는 **`TypeError`**(「`undefined` 에 객체 패턴을 댈 수 없다」),
  `f({ a } = {})` 는 **`undefined`**, `f({ a = 1 } = {})` 는 **`1`** 이다.
  ★★ **바깥 기본값은 「대상이 없을 때」를, 안쪽 기본값은 「키가 없을 때」를** 막는다. **둘은 서로를 대신하지 못한다.**
- ★★ **중복 이름 네 줄은 이유가 둘로 갈린다.** 문구가 가른다 —
  `f({ a }, { a })`·`f(a, { a })` 는 **`Duplicate parameter name not allowed in this context`**(매개변수 규칙),
  `const { a, a }` 는 **`Identifier 'a' has already been declared`**(렉시컬 선언 규칙)다.
  ★ **`var` 는 안 막힌다** — 같은 패턴을 두 번 써도 통과한다(`2`). **선언 키워드가 규칙을 정한다.**
  ★ `f({ a }) { 'use strict'; }` 가 막히는 것은 [08번](../08-function-forms-and-parameters/2-summary.md)의 규칙이다 —
  **패턴이 있으면 목록이 단순하지 않아** 함수 안 `"use strict";` 를 못 쓴다.
- ★ **패턴 하나는 `length` 한 자리로 센다** — `({ a })` 가 `1`, `({ a } = {})` 가 `0`.
  **첫 기본값 앞까지만 센다**는 08번의 규칙 그대로다.

### 5. 두 패턴은 왜 다른 실패를 하나 ★★★

**출력** — 2번 `[1]`·`[3]` 이 답의 근거다.

**왜 그런가**

- ★★ 객체 패턴이 먼저 묻는 것은 「**객체로 강제할 수 있나**」이고,
  배열 패턴이 먼저 묻는 것은 「**`Symbol.iterator` 가 있나**」다.
  ★ 앞엣것은 `null`·`undefined` 만 실패하고, 뒤엣것은 **대부분이 실패**한다.
- ★★★ **`7` 은 객체 패턴만 통과한다**(래퍼에서 읽고 없는 키는 `undefined`).
  **`{ length: 1 }` 도 객체 패턴만 통과한다** — 배열 패턴은 `length` 를 안 본다.
  ★ 반대로 **`Set` 은 양쪽 다 통과**하는데 뜻이 다르다 — 객체 패턴은 키를 못 찾아 `undefined` 를 주고,
  배열 패턴은 원소를 꺼낸다.
- ★★ **`Array.from` 은 두 문을 다 연다** — 이터러블이면 그쪽으로, 아니면 유사 배열로 읽는다.
  **구조 분해의 배열 패턴은 이터러블 문만 연다.** 그래서 같은 값에 답이 갈린다.
  ★ 09번의 `apply` 는 **유사 배열 문만** 연다 — 세 도구가 서로 다르다.

### 6. 기본값은 무엇을 막고 무엇을 못 막나 ★★★

**출력** — 2번 `[4]` 와 3번 `[2]` 가 답이다.

**왜 그런가**

- ★★★ **조건은 하나뿐이다 — 그 칸이 `undefined` 일 때.**
  3번 `[2]` 가 그것을 로그로 증명한다 — `null` 에도 `0` 에도 기본값 식이 **아예 평가되지 않았다.**
- ★★★ **`const { a = 1 } = { a: null }` 은 `null`** 이다.
  ★ 실무적 결과는 분명하다 — **API 가 「없음」을 `null` 로 주면 기본값이 안 걸린다.**
  JSON 에는 `undefined` 가 없으므로 **네트워크에서 온 데이터에는 거의 항상 `null` 이 온다.**
  ★ 고치는 법은 `a ?? 1` 이다([목록의 **12번 주제**](../12-optional-chaining-nullish-and-logical-assignment/)).
- ★★ 바깥 기본값은 「**대상이 없을 때**」를, 안쪽 기본값은 「**키가 없을 때**」를 막는다.
  `f({ a = 1 })` 은 `f()` 에서 여전히 터지고, `f({ a } = {})` 는 안 터지지만 `a` 가 `undefined` 다.
  **둘 다 필요하면 둘 다 단다** — `f({ a = 1 } = {})`.
- ★ **[08번](../08-function-forms-and-parameters/2-summary.md)의 매개변수 기본값과 같은 규칙**이다.
  ★ 08번에서 확인한 「호출마다 평가된다」도 그대로 적용된다 — 3번 `[2]` 의 로그가 그 자리다.

### 7. 객체 나머지는 무엇을 복사하나 ★★

**출력** — 1번 `[3]` 의 일곱 줄이 답이다.

**왜 그런가**

- ★★ **자기 것이고 열거 가능한 프로퍼티만 복사한다.**
  **비열거는 안 오고**(`hidden`), **상속은 안 오고**(`inherited`), **심볼 키는 온다**, **getter 는 값으로 굳는다.**
- ★★ **복사된 것의 프로토타입은 `Object.prototype`** 이다 — 원본이 무엇이었든 **평범한 객체**가 된다.
  ★ 그래서 클래스 인스턴스에 쓰면 **메서드가 사라진다**(11번에서 그 격자를 편다).
- ★★★ **「비밀 필드만 빼고 넘기기」가 안전하지 않은 경우가 둘** 있다.
  ① **심볼 키로 숨긴 것은 그대로 복사된다** — 이름으로 뺄 수 없다.
  ② **얕은 복사라** 중첩 객체 안의 비밀은 **같은 객체를 공유**한다. 뺀 것은 한 겹뿐이다.
  ★ 그리고 **getter 가 전부 불린다** — 「읽으면 기록이 남는」 프로퍼티가 있으면 그것도 부수 효과다.

### 8. 어디서 조용히 틀리나 ★★

**출력** — 2번 `[4]` 와 4번 `[1]`, 1번 `[3]` 이 각각 근거다.

**왜 그런가**

- ★★ **조용히 틀리는 자리 셋** —
  ① **`null` 에 기본값이 안 걸리는 것**(`{ a = 1 } = { a: null }` → `null`) — 에러가 없다.
  ② **선언 키워드를 빼먹어 암시적 전역이 생기는 것** — 비엄격에서 에러가 없다.
  ③ **객체 나머지가 얕은 복사라 중첩이 공유되는 것** — 원본이 바뀌어도 에러가 없다.
- ★★ **비싼 getter 가 있는 객체에 `{ ...rest }` 를 쓰면 전부 불린다.**
  3번 `[1]` 이 그것을 로그로 보인다 — 필요한 키만 적으면 그 키만 부른다.
- ★ **선언 키워드를 빼먹으면 비엄격에서 전역 프로퍼티가 생긴다.** 모듈은 항상 엄격이라 `ReferenceError` 다.

### 9. 보장인가 엔진 사정인가 ★★★

**출력**

```text
===== ./js08b-vdiff.sh 10 (exit=0) =====
  same      js08b-10a-forms.js
  same      js08b-10b-failures.js
  same      js08b-10c-order.js
  same      js08b-10d-params.js
  ----
  identical on node18 and node20: 4   different: 0
```

브라우저에 같은 줄을 던진 결과는 이렇다.

```text
===== google-chrome --headless --dump-dom page10.html | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' (exit=0) =====
  engine                                Chrome/151.0.0.0
  const { a } = null                    TypeError: Cannot destructure property 'a' of 'null' as it is null.
  const {} = null                       TypeError: Cannot destructure 'null' as it is null.
  const { a } = undefined               TypeError: Cannot destructure property 'a' of 'undefined' as it is undefined.
  const [a] = null                      TypeError: null is not iterable
  const [a] = {}                        TypeError: {} is not iterable
  const { a } = 7                       undefined
  const { length } = 'abc'              3
  const { a = 'D' } = { a: null }       null
  const { a = 'D' } = { a: undefined }  D
  f({ a }) with no argument             TypeError: Cannot destructure property 'a' of 'undefined' as it is undefined.
  pattern order beats object order      a,b
  iterator calls for [a, b]             next,next,return
```

**왜 그런가**

- ★★ **두 판이 갈린 자리는 0개**다. 네 스크립트가 **예외 문구까지 한 글자도 같았다.**
  ★★ **그래도 문구를 보장으로 읽지 않는다** — [08번](../08-function-forms-and-parameters/2-summary.md)에서
  같은 성격의 문구가 **실제로 두 판 사이에 바뀌었다.**
- ★★★ **문구를 근거로 쓰면 안 되는 이유가 이 주제의 출력에 그대로 있다.**
  같은 실패가 **`v is not iterable`**(변수 이름) · **`{} is not iterable`**(리터럴) ·
  **`{(intermediate value)} is not iterable`**(중간값)로 **세 가지 문구**로 나왔다.
  ★ **V8 이 그 자리의 소스 텍스트를 메시지에 넣기 때문**이다. **코드를 바꾸면 문구가 바뀐다.**
  ★★ 그래서 이 문서가 근거로 쓰는 것은 **`TypeError` 라는 종류와 터진 칸의 개수**다.
- ★★ **호스트가 정하는 칸은 0개**다. 브라우저의 열세 줄이 Node 와 전부 같다 — **문구까지 같다.**
  ★ **문구까지 같은 것은 둘 다 V8 이기 때문**이지 명세가 정해서가 아니다.
  다른 엔진(SpiderMonkey·JavaScriptCore)에서는 문구가 다를 것이다 — **안 돌려 봤다.**
- ★ **부적용인 창은 셋**이다 — ③ 브랜드 태그(보조로만 썼다) · ⑥ `toFixed(20)` · ⑦ `\uXXXX` 펼치기.
  **잴 것이 없다**는 뜻이지 안 쟀다는 뜻이 아니다.

### 10. 경계 — 어디까지가 이 주제인가 ★★

**출력** — 없다. 이 문항은 지도 문항이다.

**왜 그런가**

| 주제 | 정본 |
|---|---|
| 원시값 임시 래핑 | [01 — 값의 종류와 `typeof`](../01-value-types-and-typeof/2-summary.md) |
| 매개변수 목록이 단순하지 않아지는 것 | [08 — 함수 정의 형태와 매개변수](../08-function-forms-and-parameters/2-summary.md) |
| 유사 배열을 펴는 `apply` | [09 — `call`·`apply`·`bind`](../09-call-apply-bind/2-summary.md) |
| `...` 의 세 자리 · 얕은 복사 | [11 — 스프레드와 나머지](../11-spread-and-rest/2-summary.md) |
| 이터러블 프로토콜 계약 | [목록의 **19번 주제**](../19-iterable-protocol-and-for-of/) |
| `null` 막기(`?.`·`??`) | [목록의 **12번 주제**](../12-optional-chaining-nullish-and-logical-assignment/) |
| 프로퍼티 열거 순서 | [목록의 **13번 주제**](../13-object-literals-and-properties/) |
| 깊은 복사 수단 비교 | [목록의 **48번 주제**](../48-deep-copy-methods-compared/) |

- ★★★ **08번에서 이어받는 것** — 「매개변수 목록에 패턴이 있으면 단순하지 않아진다」는 사실을 받아,
  **그 패턴 자체의 규칙**(무엇을 받고 무엇을 거부하고 기본값이 언제 걸리나)을 여기서 편다.
- ★★ **파이썬의 `a, *rest = seq` 와 닮은 것** — **이터러블을 자리로 뜯는다**는 점과 **나머지가 마지막**이라는 점이다.
  **다른 것 셋** — 파이썬에는 **객체 패턴이 없고**(이름으로 뜯는 문법이 없다),
  **개수가 안 맞으면 조용히 `undefined` 가 아니라 `ValueError` 로 터지며**,
  **기본값 문법이 없다.** 정본은 [파이썬 갈래의 11번](../../../python/syntax/11-tuple-and-unpacking/)이다.
- ★ **이 주제가 끝까지 책임지는 것 셋** —
  ① **두 패턴이 서로 다른 문을 쓴다는 것**(프로퍼티 조회 대 이터레이터)과 그 실패 문구
  ② **기본값이 `undefined` 에만 걸린다는 것**과 바깥·안쪽 기본값의 차이
  ③ **객체 나머지가 무엇을 복사하고 무엇을 안 하는가.**

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js08b-10a-forms.js` | 네 형태의 결과 · **객체 나머지가 거르는 것 넷** · 괄호 규칙 | node20 1벌 + node18 대조 1벌 |
| `js08b-10b-failures.js` | ★★★ **값 15 × 패턴 4 격자 28 / 60** · 예외 문구 · 기본값의 한계 | node20 1벌 + node18 대조 1벌 |
| `js08b-10c-order.js` | ★★★ **getter 호출 순서** · **`next` 횟수와 `return` 시점** · 이터레이터 교체 | node20 1벌 + node18 대조 1벌 |
| `js08b-10d-params.js` | **설정에 달린 칸 2 / 12** · 세 기본값 모양 · 중복 이름 두 규칙 | node20 1벌 + node18 대조 1벌 |
| `js08b-10h-browser.js` | ★★★ **호스트가 정하는 칸 0개** | Chrome 151 1벌 |
| `js08b-10x-forms.js` | 형태 — `node --check` **진단 0줄**(빈 출력도 블록으로) | node20 1벌 |
| `js08b-vdiff.sh` | 네 스크립트가 **두 판에서 한 글자도 같다**는 것 | 1벌 |
| `js08b-versions.sh` | 이 문서의 모든 출력이 **어느 판에서 나왔나** | 1벌 |

**구현 의존 항목** — 다음은 **이 환경(node 20.19.6 / 18.19.1 · Chrome 151 · x86-64 Linux)에서만** 그렇다.

- ★★★ **예외 문구 전부.** 그 중에서도 **문구에 박히는 소스 텍스트**는 코드를 바꾸면 따라 바뀐다 —
  같은 실패가 `v is not iterable` · `{} is not iterable` · `{(intermediate value)} is not iterable` 로 나왔다.
- ★★ **기본값이 붙으면 문구가 바뀌는 것** — `Cannot destructure property ...` 대 `Cannot read properties of null ...`.
  **종류는 같다.**
- ★ **브라우저와 Node 의 문구가 같은 것** — **둘 다 V8 이기 때문**이다. 명세가 정한 것이 아니다.

**객체 패턴이 `null`·`undefined` 만 거부하는 것 · 배열 패턴이 이터러블만 받는 것 · 빈 패턴도 대상을 먼저 검사하는 것 · 기본값이 `undefined` 에만 걸리는 것 · 객체 패턴의 읽기 순서가 패턴 순서인 것 · 배열 패턴이 필요한 만큼만 돌고 닫는 것 · 예외로 끝나도 닫는 것 · 객체 나머지가 자기 것이고 열거 가능한 것만 얕게 복사하는 것 · 나머지의 자리 규칙 · 패턴 매개변수가 `length` 한 자리인 것은 구현 의존이 아니다.**
어느 엔진에서도 같아야 한다.

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — 다른 엔진(SpiderMonkey·JavaScriptCore)에서의 **문구** ·
  `Proxy` 로 `ownKeys`/`get` 을 가로챈 대상의 구조 분해(11번에서 스프레드 쪽으로 돌렸다) ·
  `for await (const [k, v] of ...)` · `catch ({ message })` · 정규식 명명 그룹 구조 분해 ·
  Node 18 보다 낮은 판.
- ★ **못 잰 것** — **구조 분해와 손으로 뽑기(`const a = o.a`)의 비용 차이.**
  객체 패턴이 프로퍼티를 한 번씩 읽는다는 것은 로그로 확인했지만 **얼마나 드는지는 재지 않았다.**
  그래서 이 문서에는 「느리다」·「빠르다」가 한 줄도 없다.
- ★ **부적용인 창** — ③ 브랜드 태그(보조로만 썼다) · ⑥ `toFixed(20)` · ⑦ `\uXXXX` 펼치기.
  「안 쟀다」가 아니라 「**이 주제에는 그 칸이 없다**」이다.

**판이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **예외 문구** — 네 블록 전부에 들어 있다. 08번에서 같은 성격의 문구가 실제로 바뀐 전례가 있다.
- ★★ **두 판 대조 결과** — 지금은 0개다. 갈리면 그것이 곧 그 주제의 결론이 된다.
- ★ **브라우저 쪽 0개** — 호스트나 엔진이 바뀌면 그 줄이 바뀐다.
- **패턴의 규칙 자체는 다시 돌릴 필요가 없다** — ES2015(객체 나머지는 ES2018) 이후 바뀐 적이 없다.
