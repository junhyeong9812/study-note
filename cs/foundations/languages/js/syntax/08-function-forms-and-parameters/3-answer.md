# js/syntax/08 — 함수 정의 형태와 매개변수: 「이 형태는 무엇을 가지고 무엇을 안 가지나」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **node v20.19.6**(기본 판) · **node v18.19.1**(대조) · **Google Chrome 151.0.7922.173** · x86-64 Linux 에서 실제로 돌려 얻은 것이고,
> 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 하나도 없다).
>
> ★★ **예외는 `e.constructor.name` 과 `e.message` 로만 찍었다** — 스택트레이스에는 절대 경로가 박혀 재현이 안 된다.
> ★★ **엄격/비엄격 격자는 `new Function(소스)` 으로 두 번 컴파일해 받았다** — 파일로 던지면 진단에 경로가 박힌다.
> ★★ **표준 출력과 표준 오류를 한 블록에도 안 섞었다** — 이 주제의 블록은 전부 표준 출력이다.
>
> **이 파일이 인용하는 출력을 낸 소스** — 전문은 [1-question.md](1-question.md) 의 같은 번호 문항에 있다.

```text
// js08b-08a-forms.js
// js08b-08b-hoisting.js
// js08b-08c-named-fexpr.js
// js08b-08d-arguments.js
// js08b-08e-defaults.js
// js08b-08f-param-syntax.js
// js08b-08h-browser.js
// js08b-08x-forms.js
// js08b-08p-default-contrast.py
// js08b-vdiff.sh
// js08b-versions.sh
```

> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | Node 스택트레이스의 **절대 경로** — 한 줄도 싣지 않았다 | ★★★ **격자의 칸 값**(`length`·`name`·`prototype` 소유 여부) |
> | 예외 **문구**(판이 오르면 바뀐다 — 실제로 하나 바뀌었다) | ★★★ **엄격·비엄격이 갈린 칸의 개수** |
> | 브라우저 UA 문자열의 뒷자리 | ★★ **예외의 종류** · `SyntaxError` 냐 `TypeError` 냐 |
> | — | ★★ **기본값 평가 횟수** · `arguments` 연동 여부 |
>
> ★ **이 주제의 블록에는 주소도 시간도 난수도 안 찍힌다.** 같은 판에서 다시 돌리면 한 글자도 안 변한다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 열여섯 형태를 한 격자에 놓으면 — **`prototype` 과 `new` 는 따로 논다** ★★★

**출력**

```text
===== node20 js08b-08a-forms.js (exit=0) =====
[1] form matrix -- 16 forms x 7 columns
  form              typeof    name            len  proto?  new?          call?         brand
  function decl     function  "decl"          2    true    yes           yes           [object Function]
  anon fn expr      function  "anon"          2    true    yes           yes           [object Function]
  named fn expr     function  "inner"         2    true    yes           yes           [object Function]
  arrow concise     function  "arrowConcise"  2    false   no:TypeError  yes           [object Function]
  arrow block       function  "arrowBlock"    2    false   no:TypeError  yes           [object Function]
  method shorthand  function  "method"        2    false   no:TypeError  yes           [object Function]
  generator method  function  "gen"           2    true    no:TypeError  yes           [object GeneratorFunction]
  async method      function  "am"            2    false   no:TypeError  yes           [object AsyncFunction]
  generator decl    function  "genDecl"       2    true    no:TypeError  yes           [object GeneratorFunction]
  async decl        function  "asyncDecl"     2    false   no:TypeError  yes           [object AsyncFunction]
  async arrow       function  "asyncArrow"    2    false   no:TypeError  yes           [object AsyncFunction]
  class             function  "K"             2    true    yes           no:TypeError  [object Function]
  new Function      function  "anonymous"     2    true    yes           yes           [object Function]
  bound fn          function  "bound decl"    1    false   yes           yes           [object Function]
  default param     function  "withDefault"   1    true    yes           yes           [object Function]
  rest param        function  "withRest"      1    true    yes           yes           [object Function]

[2] name -- where does an unnamed function get its name
  const assigned        "assigned"
  const arrow           "arrowAssigned"
  let then assign       "letAssigned"
  object literal key    "key"
  object literal arrow  "arrowKey"
  array element         ""
  default value         "p"
  bound                 "bound decl"
  getter                "get g"

[3] arrow has no own arguments -- it reads the enclosing function's, by identity
  same object?          true
  outer arguments       [10,20]
  brand                 [object Arguments]
  Array.isArray         false
  has callee?           true
  Symbol.iterator?      function
```

**왜 그런가**

- ★★★ **`prototype` 칸과 `new?` 칸이 어긋나는 행은 셋**이다 —
  **제너레이터 선언**과 **제너레이터 메서드**는 `prototype` 이 **있는데** `new` 가 안 되고,
  **bound 함수**는 `prototype` 이 **없는데** `new` 가 된다.
  ★ 그래서 「화살표는 `prototype` 이 없으니 `new` 가 안 된다」는 설명은 **우연히 맞는 자리에서만 맞는다.**
  외울 것은 프로퍼티가 아니라 「**생성자로 쓰일 자격이 따로 있다**」이다.
- ★★★ **`call?` 이 `no` 인 행은 하나**다 — `class`. 클래스는 `typeof` 가 `"function"` 이고
  브랜드도 `[object Function]` 인데 **`new` 없이 부르면 `TypeError`** 다.
  ★ 나머지는 전부 그냥 불린다. async 함수도 불리고 **Promise 를 돌려줄 뿐**이다.
- ★★ **브랜드는 세 가지로만 갈린다** — `[object Function]` · `[object GeneratorFunction]` · `[object AsyncFunction]`.
  **화살표·메서드 단축·클래스는 전부 `[object Function]`** 이라 **브랜드로는 안 갈린다.**
  이 주제에서 브랜드 태그는 본체가 아니라 보조 창이다.
- ★★ **이름이 빈 문자열인 줄은 「array element」 하나**다. 배열 원소에는 **이름이 붙을 자리가 없다.**
  나머지는 전부 어딘가에서 이름을 받는다 — `const` 변수명, 객체 리터럴 키, 기본값의 매개변수 이름, `get ` 접두, `bound ` 접두.
- ★ **`[3]` 의 `arguments` 는 바깥 함수의 것**이다. 근거는 **동일성**이다(`same object? true`) —
  「비슷한 것이 하나 더 있다」가 아니라 **같은 객체**다. 화살표는 그 칸을 안 만들어 **바깥 것을 그대로 읽는다.**
  ★ 브랜드는 `[object Arguments]` 이고 `Array.isArray` 는 `false` 인데 `Symbol.iterator` 는 있다.

### 2. 같은 줄 위에서 부르면 — **아홉 탐침 중 하나만 모드에 달렸다** ★★★

**출력**

```text
===== node20 js08b-08b-hoisting.js (exit=0) =====
[1] hoisting -- sloppy
  decl called before its line
    decl()                             -> decl ran 1
  typeof decl before its line
    typeof decl                        -> function
  var fn expr before its line
    typeof vexpr                       -> undefined
    vexpr()                            -> TypeError: vexpr is not a function
  const fn expr before its line
    typeof cexpr                       -> ReferenceError: Cannot access 'cexpr' before initialization
    cexpr()                            -> ReferenceError: Cannot access 'cexpr' before initialization
  arrow before its line
    typeof arr                         -> ReferenceError: Cannot access 'arr' before initialization
    arr()                              -> ReferenceError: Cannot access 'arr' before initialization
  decl inside a block, seen outside
    typeof blockFn before              -> undefined
    typeof blockFn after               -> function
  decl inside if(false)
    typeof deadFn                      -> undefined
  two decls with the same name
    dup()                              -> second
  decl and var with the same name
    typeof both                        -> number

[2] hoisting -- strict
  decl called before its line
    decl()                             -> decl ran 1
  typeof decl before its line
    typeof decl                        -> function
  var fn expr before its line
    typeof vexpr                       -> undefined
    vexpr()                            -> TypeError: vexpr is not a function
  const fn expr before its line
    typeof cexpr                       -> ReferenceError: Cannot access 'cexpr' before initialization
    cexpr()                            -> ReferenceError: Cannot access 'cexpr' before initialization
  arrow before its line
    typeof arr                         -> ReferenceError: Cannot access 'arr' before initialization
    arr()                              -> ReferenceError: Cannot access 'arr' before initialization
  decl inside a block, seen outside
    typeof blockFn before              -> undefined
    typeof blockFn after               -> undefined
  decl inside if(false)
    typeof deadFn                      -> undefined
  two decls with the same name
    dup()                              -> second
  decl and var with the same name
    typeof both                        -> number

[3] how many of the 9 probes differ between the two modes
  decl called before its line       same
  typeof decl before its line       same
  var fn expr before its line       same
  const fn expr before its line     same
  arrow before its line             same
  decl inside a block, seen outside DIFFERENT
  decl inside if(false)             same
  two decls with the same name      same
  decl and var with the same name   same
  total                             1 of 9 differ
```

**왜 그런가**

- ★★★ **두 모드가 갈린 탐침은 하나**다 — `decl inside a block, seen outside`.
  비엄격이면 블록 밖에서도 `function` 이고, **엄격이면 `undefined`** 다.
  ★ 나머지 여덟은 두 모드가 한 글자도 같다. **「호이스팅은 모드에 달렸다」는 거의 틀린 말**이다.
- ★★★ **함수 선언만 값까지 올라간다.** 줄 위에서 불러도 돌고 `typeof` 가 `function` 이다.
  **나머지 형태는 붙은 이름의 규칙을 그대로 따른다** — 화살표가 특별한 것이 아니라 `const` 가 특별하다.
- ★★ **`var` 와 `const` 가 다른 예외를 내는 이유** — `var` 는 이름이 올라가고 **값이 `undefined` 로 채워져** 있어
  `typeof` 가 `undefined` 이고 부르면 **`TypeError: vexpr is not a function`** 이다.
  `const` 는 이름만 올라가고 **초기화 전 구간(TDZ)** 이라 읽는 것 자체가 **`ReferenceError: Cannot access 'cexpr' before initialization`** 이다([05번](../05-var-let-const-and-tdz/2-summary.md)).
  ★ **「값이 없다」와 「읽을 수 없다」는 다른 상태**다.
- ★★ **`if (false)` 안의 함수 선언은 비엄격에서 이름만 올라간다.** `typeof deadFn` 이 `undefined` 인 것은
  「그런 이름이 없어서」가 아니라 「**이름은 있고 값이 안 채워져서**」다 —
  없었다면 `typeof` 가 아니라 직접 참조에서 `ReferenceError` 가 났을 것이다. 엄격에서는 블록 밖으로 아예 안 나온다.
- ★ **같은 이름의 함수 선언이 둘이면 뒤엣것이 이긴다**(`second`).
  **`var` 대입과 겹치면 대입이 이긴다** — `typeof both` 가 `number` 다. 선언이 먼저 올라가고 **대입이 나중에 덮는다.**

### 3. 이름이 안쪽에만 있는 함수 — **그 이름만 담긴 스코프가 하나 더 있다** ★★

**출력**

```text
===== node20 js08b-08c-named-fexpr.js (exit=0) =====
[1] the name is visible inside, not outside
  fact(5)                                -> 120
  fact.name                              -> selfName
  typeof selfName (outside)              -> undefined
  selfName(5) (outside)                  -> ReferenceError: selfName is not defined

[2] a function declaration puts its name outside too
  declFact(5)                            -> 120
  typeof declFact (outside)              -> function

[3] the inner name is an immutable binding -- sloppy is silent, strict throws
  sloppy: me = 1 then typeof me          -> function
  strict: me2 = 1                        -> TypeError: Assignment to constant variable.

[4] the inner binding lives in its own scope -- a parameter or a var shadows it
  named fn expr with param of same name  -> param wins: number
  named fn expr with var of same name    -> var wins: number
  named fn expr, nothing shadows         -> no shadow: function

[5] the name survives reassignment of the outer variable
  saved(5) after holder replaced         -> 120
  holder(5)                              -> replaced
  anon self-recursion still works        -> 120
  anon self-recursion after var cleared  -> TypeError: anonSelf2 is not a function
```

**왜 그런가**

- ★★ **기명 함수 표현식의 이름은 함수 바깥에 안 만들어진다.** `fact.name` 은 `selfName` 인데
  밖에서 `typeof selfName` 은 `undefined` 이고 부르면 `ReferenceError` 다.
  ★ **디버거와 `name` 에는 보이는데 코드에서는 못 부른다** — 이 착시가 이 항목의 값이다.
  함수 **선언**은 이름 하나가 안팎에 다 있다.
- ★★ **`[3]` — 같은 대입이 한쪽에서는 조용하다.** 안쪽 이름은 **변경 불가 바인딩**이라
  비엄격에서는 대입이 **무시되고**(`typeof me` 가 여전히 `function`),
  엄격에서는 **`TypeError: Assignment to constant variable.`** 이 난다.
  ★ 「조용한 실패」가 「시끄러운 실패」로 바뀌는 자리다.
- ★★ **`[4]` — 같은 이름의 매개변수나 `var` 가 이긴다.** 둘 다 `number` 다.
  그 이름은 **함수 스코프보다 한 겹 바깥의, 그 이름만 담긴 스코프**에 살기 때문이다.
  ★ 「함수 이름이니까 가장 세겠지」라는 직관이 틀린 자리다.
- ★★★ **`[5]` 가 기명 함수 표현식의 쓸모다.**
  바깥 변수 `holder` 를 다른 함수로 덮어써도 **`saved(5)` 는 여전히 `120`** 이다 — 안쪽 `me6` 이 원래 함수를 가리킨다.
  익명으로 자기 이름을 부르면 **바깥 변수가 비는 순간 `TypeError: anonSelf2 is not a function`** 이다.
  ★ **재귀를 바깥 변수 이름에 기대면 그 변수가 바뀌는 순간 깨진다.**

### 4. 같은 탐침을 두 모드로 — **열두 칸 중 일곱이 설정에 달렸다** ★★★

**출력**

```text
===== node20 js08b-08d-arguments.js (exit=0) =====
[1] sloppy vs strict -- same probe, compiled twice
  write param, read arguments
    sloppy  arguments[0]=99
    strict  arguments[0]=1   <-- DIFFERENT
  write arguments, read param
    sloppy  a=99
    strict  a=1   <-- DIFFERENT
  two params, write the second
    sloppy  arguments=[1,99]
    strict  arguments=[1,2]   <-- DIFFERENT
  param not passed, then written
    sloppy  len=0 [0]=undefined
    strict  len=0 [0]=undefined
  delete arguments[0], then write param
    sloppy  [0]=undefined a=99
    strict  [0]=undefined a=99
  default param present
    sloppy  arguments[0]=1
    strict  arguments[0]=1
  rest param present
    sloppy  arguments[0]=1
    strict  arguments[0]=1
  destructuring param present
    sloppy  arguments[0]=1
    strict  arguments[0]=1
  arguments.callee
    sloppy  callee is f? true
    strict  TypeError: 'caller', 'callee', and 'arguments' properties may not be accessed on strict mode functions or the arguments objects for calls to them   <-- DIFFERENT
  duplicate parameter names
    sloppy  a=2 arguments=[1,2]
    strict  COMPILE SyntaxError: Duplicate parameter name not allowed in this context   <-- DIFFERENT
  assign to arguments itself
    sloppy  arguments=1
    strict  COMPILE SyntaxError: Unexpected eval or arguments in strict mode   <-- DIFFERENT
  arguments as a parameter name
    sloppy  arguments=7
    strict  COMPILE SyntaxError: Unexpected eval or arguments in strict mode   <-- DIFFERENT

  settings-dependent cells      7 of 12

[2] arguments is not an array -- what it has and what it lacks
  brand                         [object Arguments]
  Array.isArray                 false
  length                        3
  fn.length                     2
  typeof args.map               undefined
  typeof args[Symbol.iterator]  function
  own keys                      ["0","1","2","length","callee"]
  proto is Object.prototype?    true
  spread to array               [1,2,3]
  Array.from                    [1,2,3]

[3] rest is a real array -- the same probe with ...r
  brand                         [object Array]
  Array.isArray                 true
  length                        2
  fn.length                     1
  typeof rest.map               function
  holds                         [2,3]
  rest only takes the leftovers []
```

**왜 그런가**

- ★★★ **설정에 달린 칸은 일곱**이다 — 연동 셋(`매개변수→arguments` · `arguments→매개변수` · 둘째 매개변수) ·
  `arguments.callee` · 중복 매개변수 이름 · `arguments` 에 대입 · `arguments` 를 매개변수 이름으로.
  ★ 뒤 셋은 **`SyntaxError`** 라 **컴파일 자체가 안 된다** — 같은 소스가 한 모드에서는 프로그램이고 한 모드에서는 아니다.
- ★★★ **기본 매개변수가 있는 탐침은 두 모드가 같았다** — 둘 다 `arguments[0]=1` 이다.
  **연동이 이미 끊겨 있어서** 엄격 모드가 더 끊을 것이 없다는 뜻이다.
  ★★ 그래서 **연동을 끊는 조건은 둘**이다 — 엄격이거나, **매개변수 목록이 단순하지 않거나**(기본값·나머지·구조 분해).
  ★★★ 실무에서 위험한 쪽은 뒤엣것이다. **시그니처에 기본값 하나를 더한 커밋이 `arguments` 를 쓰는 코드의 동작을 조용히 바꾼다.**
- ★★ **`arguments` 가 배열이 아니라는 근거 셋** — 브랜드가 `[object Arguments]` ·
  `Array.isArray` 가 `false` · **`map` 이 없다**(`typeof args.map` 이 `undefined`).
  프로토타입은 `Object.prototype` 이다.
  ★ 그런데 **`Symbol.iterator` 는 있다**(`typeof` 가 `function`). 그래서 스프레드와 `Array.from` 이 둘 다 통한다 —
  **「배열이 아니다」와 「이터러블이 아니다」는 다른 말**이다.
- ★★ **`fn.length` 두 줄이 다른 이유** — `arguments` 쪽 탐침은 `function probe(a, b)` 라 `2`,
  나머지 쪽 탐침은 `function probe2(a, ...r)` 라 **`1`** 이다.
  ★ **`fn.length` 는 「선언한 필수 자리」를 세고 `arguments.length` 는 「실제로 넘어온 개수」를 센다.**
  그래서 `probe2(1, 2, 3)` 에서 `length` 는 `1` 인데 나머지에는 둘이 들어온다.
- ★ **`delete arguments[0]` 은 그 자리의 연동을 끊는다.** 지운 뒤 `a = 99` 를 해도 `arguments[0]` 은 `undefined` 이고
  `a` 만 `99` 다 — 두 모드가 같다.

### 5. 기본값을 세 번 부르면 — **JS 는 매번 새로, 파이썬은 한 번만** ★★★

**출력**

```text
===== node20 js08b-08e-defaults.js (exit=0) =====
[1] the default expression runs on every call -- not once at definition
  fresh() 1st                                    -> ["x"]
  fresh() 2nd                                    -> ["x"]
  fresh() 3rd                                    -> ["x"]
  how many times was it evaluated                -> 3
  notFresh() 1st (shared array)                  -> ["x"]
  notFresh() 2nd (shared array)                  -> ["x","x"]
  passing a value skips the default              -> evals=0

[2] what triggers the default -- only undefined does
  trig()                                         -> string "DEFAULT"
  trig(undefined)                                -> string "DEFAULT"
  trig(null)                                     -> object "null"
  trig(0)                                        -> number "0"
  trig('')                                       -> string ""
  trig(NaN)                                      -> number "NaN"
  trig(false)                                    -> boolean "false"
  trig(void 0)                                   -> string "DEFAULT"

[3] length counts only the params before the first default or rest
  (a, b, c)                                      -> length 3
  (a, b = 1, c)                                  -> length 1
  (a = 1, b, c)                                  -> length 0
  (a, ...r)                                      -> length 1
  (...r)                                         -> length 0
  ({ a }, b)                                     -> length 2
  (a, { b } = {})                                -> length 1
  ()                                             -> length 0
  arguments.length is what was passed            -> 4

[4] a default can see the params to its left, never the ones to its right
  (a, b = a * 2) with f(3)                       -> 3,6
  (a = b, b = 2) with f()                        -> ReferenceError: Cannot access 'b' before initialization
  (a = b, b = 2) with f(1)                       -> 1,2
  (a = later()) with later below                 -> hoisted decl is fine
  (a = a) with f()                               -> ReferenceError: Cannot access 'a' before initialization

[5] a non-simple parameter list gets its own scope -- var in the body does not reach it
  param scope: (a, b = () => a) then var a = 99  -> a=99 b()=1
  simple list for comparison (no default)        -> a=99
  default sees the outer binding, not the body var -> a=outer outer=body
```

파이썬 쪽은 이렇다.

```text
===== python3 js08b-08p-default-contrast.py (exit=0) =====
[1] python: default evaluated once, at definition time
  fresh() 1st   -> ['x']
  fresh() 2nd   -> ['x', 'x']
  fresh() 3rd   -> ['x', 'x', 'x']
  the object itself -> (['x', 'x', 'x'],)

[2] python: None does not trigger anything -- there is no undefined rule
  trig()        -> ('str', 'DEFAULT')
  trig(None)    -> ('NoneType', None)
  trig(0)       -> ('int', 0)
```

**왜 그런가**

- ★★★ **JS 는 세 번 다 `["x"]`, 파이썬은 `['x']` → `['x','x']` → `['x','x','x']`** 다.
  ★ JS 의 기본값 자리에 있는 것은 「값」이 아니라 「**식**」이라서 **호출마다 평가**된다(`evalCount` 가 `3`).
  ★ **파이썬은 `def` 를 만나는 순간 기본값 객체를 한 번 만들어 함수에 붙여 둔다** —
  출력의 `fresh.__defaults__` 가 **쌓인 그 리스트 자신**이다. 정본은
  [파이썬 갈래의 20번 「가변 기본 인자 함정」](../../../python/syntax/20-mutable-default-args/)이다.
  ★★ 함정의 방향이 정반대다 — 파이썬은 **같은 객체가 계속 쓰여서**, JS 는 **매번 새 객체라서** 사고가 난다.
  ★ JS 에서 「매번 같은 것」을 원하면 **바깥에 만들어 참조**해야 한다(출력의 `notFresh`).
- ★★★ **`[2]` 에서 기본값이 걸린 값은 셋**이다 — `f()` · `f(undefined)` · `f(void 0)`.
  **`null`·`0`·`""`·`NaN`·`false` 는 전부 그대로 들어온다.**
  ★ **조건은 `undefined` 하나**이고, 이것이 `||` 로 기본값을 흉내 내던 습관과 갈리는 자리다.
  ★ 파이썬에는 이 규칙 자체가 없다 — `None` 을 주면 **그냥 `None` 이 들어온다.**
- ★★ **`[3]` 의 `length`** — `(a,b,c)`→3 · `(a,b=1,c)`→**1** · `(a=1,b,c)`→**0** ·
  `(a,...r)`→1 · `(...r)`→0 · `({a},b)`→2 · `(a,{b}={})`→1 · `()`→0.
  ★ **첫 기본값 또는 나머지 앞까지만 센다.** 뒤에 이름이 몇 개 더 있든 세지 않는다.
  ★ 같은 호출의 `arguments.length` 는 **4** 였다 — **세는 대상이 다르다.**
- ★★ **`[4]` 에서 터지는 줄은 둘**이다 — `(a = b, b = 2)` 를 인자 없이 부른 것과 `(a = a)`.
  둘 다 **`ReferenceError: Cannot access ... before initialization`** — **매개변수도 TDZ 를 탄다**([05번](../05-var-let-const-and-tdz/2-summary.md)).
  ★ `(a = b, b = 2)` 도 **인자를 주면 안 터진다**(`f(1)` → `1,2`). 기본값 식이 평가되지 않기 때문이다.
  ★ 함수 **선언**은 호이스팅되므로 기본값이 아래쪽 선언을 불러도 된다.
- ★★★ **`[5]` 는 한 함수 안에 `a` 가 둘이라는 뜻이 맞다.**
  매개변수 목록이 단순하지 않으면 **매개변수 스코프가 따로 생기고** 본문의 `var a` 는 그것을 **복사한 별개 칸**이다.
  그래서 본문에서 `a = 99` 를 해도 **기본값 식이 붙든 화살표는 매개변수 쪽 `1`** 을 본다.
  ★ 단순 목록(`(a, b)`)이면 스코프가 하나라 이런 일이 없다.
  ★ 마지막 줄도 같은 이유다 — 기본값 식은 **본문의 `var outer` 가 아니라 바깥 `outer`** 를 본다.

### 6. 매개변수 목록 스무 형태 — **일곱이 설정에 달렸다** ★★

**출력**

```text
===== node20 js08b-08f-param-syntax.js (exit=0) =====
[1] parameter list forms -- compiled twice
  form                            sloppy  strict
  f(a, b)                         ok      ok
  f(a, b,)  trailing comma        ok      ok
  f(a, a)  duplicate              ok      ERR   <-- DIFFERENT
  f(a, a = 1)  dup + default      ERR     ERR
  (a, a) => {}                    ERR     ERR
  f(a = 1) { 'use strict'; }      ERR     ERR
  f(a, b) { 'use strict'; }       ok      ok
  f(a, a) { 'use strict'; }       ERR     ERR
  f(...r)                         ok      ok
  f(...r,)  comma after rest      ERR     ERR
  f(...r, b)  rest not last       ERR     ERR
  f(...r = [])  rest default      ERR     ERR
  f(a = 1, b)  default first      ok      ok
  f({ a }, [b])  destructured     ok      ok
  f(eval)                         ok      ERR   <-- DIFFERENT
  f(arguments)                    ok      ERR   <-- DIFFERENT
  (arguments) => {}               ok      ERR   <-- DIFFERENT
  f(a) { var arguments; }         ok      ERR   <-- DIFFERENT
  f(yield)                        ok      ERR   <-- DIFFERENT
  function* f(yield) {}           ERR     ERR   <-- DIFFERENT
  settings-dependent cells        7 of 20

[2] the messages behind the ERR cells
  strict f(a, a)  duplicate                 SyntaxError: Duplicate parameter name not allowed in this context
  sloppy f(a, a = 1)  dup + default         SyntaxError: Duplicate parameter name not allowed in this context
  sloppy (a, a) => {}                       SyntaxError: Duplicate parameter name not allowed in this context
  sloppy f(a = 1) { 'use strict'; }         SyntaxError: Illegal 'use strict' directive in function with non-simple parameter list
  sloppy f(a, a) { 'use strict'; }          SyntaxError: Duplicate parameter name not allowed in this context
  sloppy f(...r,)  comma after rest         SyntaxError: Rest parameter must be last formal parameter
  sloppy f(...r, b)  rest not last          SyntaxError: Rest parameter must be last formal parameter
  sloppy f(...r = [])  rest default         SyntaxError: Rest parameter may not have a default initializer
  strict f(eval)                            SyntaxError: Unexpected eval or arguments in strict mode
  strict f(arguments)                       SyntaxError: Unexpected eval or arguments in strict mode
  strict (arguments) => {}                  SyntaxError: Unexpected eval or arguments in strict mode
  strict f(a) { var arguments; }            SyntaxError: Unexpected eval or arguments in strict mode
  strict f(yield)                           SyntaxError: Unexpected strict mode reserved word
  sloppy function* f(yield) {}              SyntaxError: Unexpected identifier 'yield'
  strict function* f(yield) {}              SyntaxError: Unexpected strict mode reserved word
```

**왜 그런가**

- ★★★ **설정에 달린 칸은 일곱**이다 — `f(a, a)` · `f(eval)` · `f(arguments)` · `(arguments) => {}` ·
  `f(a) { var arguments; }` · `f(yield)` · `function* f(yield) {}`.
  ★ 마지막 것은 **두 모드가 둘 다 `ERR` 인데 문구가 달라** `DIFFERENT` 로 잡혔다 —
  비엄격은 `Unexpected identifier`, 엄격은 `Unexpected strict mode reserved word` 다.
  ★★ **「둘 다 에러」가 「같은 에러」는 아니다** — 격자가 값만 보면 이 칸을 놓친다.
- ★★★ **비엄격에서도 터지는 줄은 여섯**이다 — `f(a, a = 1)` · `(a, a) => {}` · `f(a = 1) { 'use strict'; }` ·
  `f(a, a) { 'use strict'; }` · `f(...r,)` · `f(...r, b)` · `f(...r = [])` 중 나머지 매개변수 셋과 중복 셋.
  ★ **공통점은 「매개변수 목록이 단순하지 않다」와 「나머지 매개변수의 자리」 둘**이다.
  ★★ 그래서 **중복 이름을 금지하는 조건은 셋**이다 — 엄격이거나, 목록이 단순하지 않거나, 화살표이거나.
- ★★ **`function f(a = 1) { 'use strict'; }` 는 `SyntaxError`** 다 —
  `Illegal 'use strict' directive in function with non-simple parameter list`.
  ★ **기본값을 하나 붙인 순간 그 함수만 엄격으로 만들 방법이 사라진다.** 파일이나 모듈 단위로 올려야 한다.
  ★ 실무에서는 레거시 스크립트를 부분적으로 엄격화하려다 이 벽에 걸린다.
- ★ **나머지 매개변수의 두 문구는 다른 규칙이다** —
  `Rest parameter must be last formal parameter` 는 **자리**를,
  `Rest parameter may not have a default initializer` 는 **기본값 금지**를 말한다.
  ★ 문구가 갈리니 **어느 규칙에 걸렸는지 메시지만 보고 안다.**

### 7. `length` 는 무엇을 세나 ★★

**출력** — 5번 문항 `[3]` 블록의 여덟 줄이 그 답이다. 그 중 넷을 표로 옮기면 이렇다.

| 시그니처 | `length` |
|---|---|
| `(a, b = 1, c)` | **1** |
| `(a = 1, b, c)` | **0** |
| `(a, ...r)` | **1** |
| `({ a }, b)` | **2** |

**왜 그런가**

- ★★ **`fn.length` 는 「선언 시점」에 정해지고 `arguments.length` 는 「호출 시점」에 정해진다.**
  앞엣것은 함수 객체의 프로퍼티이고 뒤엣것은 그 호출의 사실이다.
- ★★ **`length` 는 첫 기본값 또는 나머지 앞까지만 센다.** 구조 분해 매개변수는 기본값이 없으면 **한 자리로 센다.**
- ★ **`fn.length` 로 arity 를 보고 분기하는 라이브러리는 「기본값 추가」에 조용히 깨진다.**
  콜백 시그니처를 `(err, res)` 에서 `(err, res = null)` 로 바꾼 것만으로 `length` 가 `2` 에서 `1` 이 된다.
  ★ **테스트가 안 잡는다** — 값도 타입도 안 바뀌고 분기만 바뀌기 때문이다.

### 8. 화살표를 그 자리에 쓰면 무엇을 잃나 ★★

**출력** — 1번 격자의 화살표 행이 답이다. `proto?` `false` · `new?` `no:TypeError` 이고,
`arguments` 는 `[3]` 이 「자기 것이 아니라 바깥 것」임을 동일성으로 보였다.

**왜 그런가**

- ★★ **화살표가 안 만드는 칸은 넷**이다 — 자기 `this` · 자기 `arguments` · `prototype` · `new.target`.
  그래서 `new` 가 `TypeError` 이고 생성자로 못 쓴다.
- ★★ **객체 리터럴의 메서드 자리에 화살표를 쓰면 `this` 가 그 객체가 아니다** — 바깥 것을 그대로 쓴다.
  정본은 [07번](../07-this-binding-four-rules/2-summary.md)이고, 여기서는 「형태가 그 칸을 안 만든다」까지다.
  ★ 메서드 자리의 정답은 **메서드 단축 표기**다.
- ★★ **생성자 자리에 쓰면 `TypeError`** 다. 격자의 `new?` 칸이 그 답이다.
- ★ **화살표가 정답인 자리 둘** — **콜백**(바깥 `this` 를 그대로 쓰고 싶을 때)과
  **클래스 필드**(인스턴스마다 `this` 를 못질해 두고 싶을 때). 둘 다 07번이 정본이다.

### 9. 설정에 달린 칸이 몇 개인가 ★★★

**출력** — 세 격자의 집계 줄이 답이다.

| 격자 | 설정에 달린 칸 |
|---|---|
| 호이스팅(2번) | **1 / 9** |
| `arguments`(4번) | **7 / 12** |
| 매개변수 문법(6번) | **7 / 20** |

**왜 그런가**

- ★★★ **`arguments` 쪽이 압도적으로 두껍다.** 이 주제에서 엄격 모드가 실제로 답을 바꾸는 곳은
  **거의 전부 `arguments` 주변**이고, 호이스팅은 블록 함수 선언 하나뿐이다.
  ★ 「엄격 모드는 많은 것을 바꾼다」는 인상이 **어디서 오는지**를 이 세 수치가 가른다.
- ★★★ **`arguments` 연동을 끊는 조건은 둘**이다 — 엄격이거나, **매개변수 목록이 단순하지 않거나.**
  엄격 모드 하나가 아니다. 4번 격자의 기본값·나머지·구조 분해 세 탐침이 **두 모드에서 똑같이 끊겨 있었다**는 것이 근거다.
- ★★ **중복 매개변수 이름을 금지하는 조건은 셋**이다 — 엄격이거나, 목록이 단순하지 않거나, **화살표이거나.**
- ★ **모듈(ESM)로 옮기면 저절로 바뀌는 것** — **모듈 코드는 항상 엄격**이다.
  그래서 블록 함수 선언의 가시성, `arguments` 연동, `arguments.callee`, 중복 매개변수 이름이 **한꺼번에 엄격 쪽 답이 된다.**
  ★ 정본은 [목록의 **35번 주제**](../35-strict-mode/) 「엄격 모드」와 [목록의 **42번 주제**](../42-esm-modules/) 「ESM 모듈」이다.

### 10. 보장인가 엔진 사정인가 ★★★

**출력**

```text
===== ./js08b-vdiff.sh 08 (exit=0) =====
  same      js08b-08a-forms.js
  same      js08b-08b-hoisting.js
  same      js08b-08c-named-fexpr.js
  same      js08b-08d-arguments.js
  same      js08b-08e-defaults.js
  DIFFERENT js08b-08f-param-syntax.js
      39c39
      <   sloppy function* f(yield) {}              SyntaxError: Unexpected identifier
      ---
      >   sloppy function* f(yield) {}              SyntaxError: Unexpected identifier 'yield'
  ----
  identical on node18 and node20: 5   different: 1
```

갈린 블록은 v18 쪽도 싣는다.

```text
===== node18 js08b-08f-param-syntax.js (exit=0) =====
[1] parameter list forms -- compiled twice
  form                            sloppy  strict
  f(a, b)                         ok      ok
  f(a, b,)  trailing comma        ok      ok
  f(a, a)  duplicate              ok      ERR   <-- DIFFERENT
  f(a, a = 1)  dup + default      ERR     ERR
  (a, a) => {}                    ERR     ERR
  f(a = 1) { 'use strict'; }      ERR     ERR
  f(a, b) { 'use strict'; }       ok      ok
  f(a, a) { 'use strict'; }       ERR     ERR
  f(...r)                         ok      ok
  f(...r,)  comma after rest      ERR     ERR
  f(...r, b)  rest not last       ERR     ERR
  f(...r = [])  rest default      ERR     ERR
  f(a = 1, b)  default first      ok      ok
  f({ a }, [b])  destructured     ok      ok
  f(eval)                         ok      ERR   <-- DIFFERENT
  f(arguments)                    ok      ERR   <-- DIFFERENT
  (arguments) => {}               ok      ERR   <-- DIFFERENT
  f(a) { var arguments; }         ok      ERR   <-- DIFFERENT
  f(yield)                        ok      ERR   <-- DIFFERENT
  function* f(yield) {}           ERR     ERR   <-- DIFFERENT
  settings-dependent cells        7 of 20

[2] the messages behind the ERR cells
  strict f(a, a)  duplicate                 SyntaxError: Duplicate parameter name not allowed in this context
  sloppy f(a, a = 1)  dup + default         SyntaxError: Duplicate parameter name not allowed in this context
  sloppy (a, a) => {}                       SyntaxError: Duplicate parameter name not allowed in this context
  sloppy f(a = 1) { 'use strict'; }         SyntaxError: Illegal 'use strict' directive in function with non-simple parameter list
  sloppy f(a, a) { 'use strict'; }          SyntaxError: Duplicate parameter name not allowed in this context
  sloppy f(...r,)  comma after rest         SyntaxError: Rest parameter must be last formal parameter
  sloppy f(...r, b)  rest not last          SyntaxError: Rest parameter must be last formal parameter
  sloppy f(...r = [])  rest default         SyntaxError: Rest parameter may not have a default initializer
  strict f(eval)                            SyntaxError: Unexpected eval or arguments in strict mode
  strict f(arguments)                       SyntaxError: Unexpected eval or arguments in strict mode
  strict (arguments) => {}                  SyntaxError: Unexpected eval or arguments in strict mode
  strict f(a) { var arguments; }            SyntaxError: Unexpected eval or arguments in strict mode
  strict f(yield)                           SyntaxError: Unexpected strict mode reserved word
  sloppy function* f(yield) {}              SyntaxError: Unexpected identifier
  strict function* f(yield) {}              SyntaxError: Unexpected strict mode reserved word
```

브라우저에 같은 줄을 던진 결과는 이렇다.

```text
===== google-chrome --headless --dump-dom page08.html | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' (exit=0) =====
  engine                            Chrome/151.0.0.0
  decl.length                       2
  arrow has prototype?              false
  (function (a, b = 1) {}).length   1
  sloppy param-arguments link       99
  strict param-arguments link       1
  default param breaks the link     1
  default evaluated per call        calls=3 evals=3
  arguments brand                   [object Arguments]
  strict arguments.callee           TypeError
  strict duplicate param            SyntaxError
  'use strict' + default param      SyntaxError
  named fn expr, name inside        function
  named fn expr, name outside       undefined
```

**왜 그런가**

- ★★ **두 판이 갈린 자리는 하나**다 — `SyntaxError: Unexpected identifier` 가 v20 에서
  `Unexpected identifier 'yield'` 가 됐다. 여섯 스크립트 중 다섯은 **한 글자도 같았다.**
- ★★★ **그 차이는 V8 의 사정이다.** 근거는 **무엇이 `SyntaxError` 인지가 안 바뀌었다**는 것이다 —
  두 판 모두 `ERR` 이고 **종류도 같다.** 바뀐 것은 **말하는 방식**뿐이다.
  ★ 명세는 「이 형태는 Early Error 다」까지만 정하고 **문구는 정하지 않는다.**
  ★★ 이 주제 자체가 「**문구를 근거로 쓰면 판이 오를 때 문서가 조용히 틀린다**」의 실례가 됐다.
- ★★ **호스트가 정하는 칸은 0개**였다. 브라우저에 던진 열네 줄이 Node 쪽과 전부 같다.
  ★ **07번은 호스트 칸이 넷**이었다(타이머의 `this` · 전역 객체의 브랜드 등). **정확히 대비된다** —
  함수 형태와 매개변수는 **순수하게 언어 쪽**이다.
  ★★ 다만 **「같았다」는 보장이 아니라 관찰**이다. 보장은 명세가 하고 이 줄은 그 보장이 두 호스트에서 지켜졌다는 관찰이다.
- ★ **부적용인 창은 셋**이다 — `toFixed(20)`(부동소수점이 닿는 칸이 없다) ·
  `\uXXXX` 펼치기(인코딩이 답을 바꾸는 자리가 없다) · 「여러 번 돌려 흔들림 보기」(난수·시각·순서 비보장이 없다).
  ★★ 「안 쟀다」가 아니라 「**잴 것이 없다**」이고, 그 구분 자체가 이 주제의 성질을 말한다.

### 11. 경계 — 어디까지가 이 주제인가 ★★

**출력** — 없다. 이 문항은 지도 문항이다.

**왜 그런가**

| 주제 | 정본 |
|---|---|
| `this` 네 규칙 · 화살표의 렉시컬 `this` | [07 — `this` 바인딩 네 규칙](../07-this-binding-four-rules/2-summary.md) |
| TDZ · `var`/`let`/`const` | [05 — `var`·`let`·`const` 와 TDZ](../05-var-let-const-and-tdz/2-summary.md) |
| 클로저가 환경을 붙드는 것 | [06 — 스코프와 클로저](../06-scope-and-closures/2-summary.md) |
| `call`·`apply`·`bind` 의 API | [09 — `call`·`apply`·`bind`](../09-call-apply-bind/2-summary.md) |
| 구조 분해 패턴의 규칙 | [10 — 구조 분해 할당](../10-destructuring-assignment/2-summary.md) |
| 나머지·스프레드의 세 자리 | [11 — 스프레드와 나머지](../11-spread-and-rest/2-summary.md) |
| 엄격 모드 전체 | [목록의 **35번 주제**](../35-strict-mode/) |
| 매개변수 타입·오버로드 | [TS 갈래의 16번](../../../ts/syntax/16-function-types-and-overloads/) |

- ★★★ **07번에서 이어받는 것** — 「화살표는 자기 `this` 를 안 만든다」는 결론을 그대로 받아,
  **그것이 `arguments`·`prototype`·`new` 와 한 묶음으로 빠진다**는 것을 격자로 확인한다.
- ★★ **파이썬 갈래와의 경계** — [19번](../../../python/syntax/19-function-argument-rules/)은
  **위치 인자·키워드 인자·가변 인자의 조합 규칙**이 정본이고,
  [20번](../../../python/syntax/20-mutable-default-args/)은 **기본값이 한 번만 만들어진다**는 사실이 정본이다.
  ★ 여기서는 **그 사실과 JS 가 정반대라는 대비**만 싣는다.
- ★ **이 주제가 끝까지 책임지는 것 셋** —
  ① **형태마다 무엇이 딸려 오나**(격자 16×7) ② **`arguments` 연동의 두 조건**
  ③ **기본 매개변수가 호출마다 평가되는 것**과 그 스코프.

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js08b-08a-forms.js` | ★★★ **형태 16 × 칸 7 격자** · 이름이 붙는 자리 · 화살표의 `arguments` 동일성 | node20 1벌 + node18 대조 1벌 |
| `js08b-08b-hoisting.js` | 세 형태의 호이스팅 차이 · **두 모드가 갈린 탐침이 1 / 9** | node20 1벌 + node18 대조 1벌 |
| `js08b-08c-named-fexpr.js` | 안쪽 이름의 가시성·불변성·섀도잉 · **재귀가 지켜지는 것** | node20 1벌 + node18 대조 1벌 |
| `js08b-08d-arguments.js` | ★★★ **연동 격자 7 / 12** · `arguments` 가 배열이 아닌 것 · 나머지가 배열인 것 | node20 1벌 + node18 대조 1벌 |
| `js08b-08e-defaults.js` | ★★★ **호출마다 평가** · `undefined` 에만 걸리는 것 · `length` · 매개변수 스코프 | node20 1벌 + node18 대조 1벌 |
| `js08b-08f-param-syntax.js` | 매개변수 문법 **20형태 × 두 모드 7 / 20** · 문구 | node20 1벌 + node18 1벌(**갈렸다**) |
| `js08b-08p-default-contrast.py` | ★★★ **파이썬은 정의 시점 한 번**이라는 대비 | python3 3.12.3 1벌 |
| `js08b-08h-browser.js` | ★★★ **호스트가 정하는 칸 0개** | Chrome 151 1벌 |
| `js08b-08x-forms.js` | 형태 — `node --check` **진단 0줄**(빈 출력도 블록으로) | node20 1벌 |
| `js08b-vdiff.sh` | 여섯 스크립트 중 **다섯이 두 판에서 한 글자도 같다**는 것 | 1벌 |
| `js08b-versions.sh` | 이 문서의 모든 출력이 **어느 판에서 나왔나** | 1벌 |

**구현 의존 항목** — 다음은 **이 환경(node 20.19.6 / 18.19.1 · Chrome 151 · python3 3.12.3 · x86-64 Linux)에서만** 그렇다.

- ★★ **예외 메시지 문구 전부** — `Duplicate parameter name not allowed in this context` ·
  `Illegal 'use strict' directive in function with non-simple parameter list` ·
  `Rest parameter must be last formal parameter` · `Cannot access 'b' before initialization`.
  **종류는 명세, 문구는 V8 의 것**이다.
- ★★★ **그 중 하나가 두 판에서 실제로 바뀌었다** — `Unexpected identifier` → `Unexpected identifier 'yield'`.
- ★ **`new Function` 이 만든 함수의 스코프** — 전역만 본다는 것은 명세지만 이 문서는 **값만** 받아 썼다.
- ★ **파이썬 쪽의 `__defaults__` 표기** — 그 속성 이름과 튜플 표기는 CPython 의 것이다.

**형태별 칸 유무 · 함수 선언만 값까지 호이스팅되는 것 · 기명 함수 표현식 이름의 스코프와 불변성 · `length` 의 계산 규칙 · 기본값이 호출마다 평가되고 `undefined` 에만 걸리는 것 · 매개변수 TDZ · 단순하지 않은 목록이 `arguments` 연동을 끊고 함수 안 `"use strict";` 를 금지하는 것 · 나머지 매개변수의 자리 규칙은 구현 의존이 아니다.**
어느 엔진에서도 같아야 한다.

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — ESM(`.mjs`) 파일에서 같은 탐침을 돌리는 것 · 다른 엔진(SpiderMonkey·JavaScriptCore) ·
  Node 18 보다 낮은 판 · `eval` 안에서의 함수 선언 · `with` 문 안의 매개변수 스코프 ·
  **엄격 모드 파일 전체**에서 이 여섯 스크립트를 다시 돌리는 것(두 번 컴파일로 대신했다).
- ★ **못 잰 것** — **기본값 식·나머지 매개변수·`arguments` 객체 생성의 비용.**
  「기본값은 호출마다 평가된다」는 관찰했지만 **얼마나 드는지는 재지 않았다.**
  그래서 이 문서에는 「느리다」·「빠르다」가 한 줄도 없다.
- ★ **잴 것이 없는 것(부적용)** — `toFixed(20)` · `\uXXXX` 펼치기 · 「여러 번 돌려 흔들림 보기」.
  「안 쟀다」가 아니라 「**이 주제에는 그 칸이 없다**」이다.

**판이 올랐을 때 다시 돌려야 하는 것**

- ★★ **예외 메시지 문구** — 여섯 블록에 들어 있다. **이미 한 번 바뀌었다.**
- ★★ **두 판 대조 결과** — 지금은 하나만 갈린다. 더 갈리면 그것이 곧 그 주제의 결론이 된다.
- ★ **브라우저 쪽 0개** — 호스트가 바뀌면 그 줄이 바뀐다.
- **격자의 칸 값 자체는 다시 돌릴 필요가 없다** — ES2015 에서 화살표·기본값·나머지가 들어온 뒤로 바뀐 적이 없다.
