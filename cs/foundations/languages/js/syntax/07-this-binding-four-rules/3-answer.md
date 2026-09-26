# js/syntax/07 — `this` 바인딩 네 규칙: 「이 호출식에서 `this` 는 무엇인가」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **node v20.19.6**(기본 판) · **node v18.19.1**(대조) · **Google Chrome 151.0.7922.173** · x86-64 Linux 에서 실제로 돌려 얻은 것이고,
> 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 하나도 없다).
>
> ★★ **예외는 `e.constructor.name` 과 `e.message` 로만 찍었다** — 스택트레이스에는 절대 경로가 박혀 재현이 안 된다.
> ★★ **엄격·비엄격 격자는 `new Function(소스)` 으로 두 번 컴파일해 받았다** — 파일로 던지면 진단에 경로가 박힌다.
> ★★ **표준 출력과 표준 오류를 한 블록에도 안 섞었다** — 이 주제의 블록은 전부 표준 출력이다.
>
> **이 파일이 인용하는 출력을 낸 소스** — 전문은 [1-question.md](1-question.md) 의 같은 번호 문항에 있다.

```text
// js06b-07a-four-rules.js
// js06b-07b-mode-matrix.js
// js06b-07c-detached.js
// js06b-07d-arrow.js
// js06b-07e-bind.js
// js06b-07f-new.js
// js06b-07g-callbacks.js
// js06b-07h-browser.js
// js06b-07x-forms.js
// js06b-vdiff.sh
```

> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | Node 스택트레이스의 **절대 경로** — 한 줄도 싣지 않았다 | ★★★ **브랜드 태그**(`[object Object]`·`[object global]`·`[object Window]`) |
> | 예외 **문구**(판이 오르면 바뀐다) | ★★★ **엄격·비엄격이 갈린 칸의 개수** |
> | 브라우저 UA 문자열의 뒷자리 | ★★ **예외의 종류** · `bound` 접두 · `length` 값 |
> | Node 타이머 객체의 **내부 필드** — 한 줄도 안 찍었다 | ★★ 타이머 콜백의 `this` 가 **`Timeout` 이라는 것** |
>
> ★ **이 주제의 블록에는 주소도 시간도 난수도 안 찍힌다.** 같은 판에서 다시 돌리면 한 글자도 안 변한다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 같은 함수를 아홉 가지로 부르면 — **함수는 하나, 답은 아홉** ★★★

**출력**

```text
===== node20 js06b-07a-four-rules.js (exit=0) =====
[1] 네 규칙 -- 같은 함수, 다른 호출식
  default   who()                -> globalThis
  implicit  holder.who()         -> [object Object] mark=holder
  implicit  nested.inner.who()   -> [object Object] mark=inner
  implicit  obj['who']()         -> [object Object] mark=holder
  implicit  arr[0]()             -> [object Array] mark=array
  explicit  who.call(o)          -> [object Object] mark=called
  explicit  who.apply(o)         -> [object Object] mark=applied
  explicit  who.bind(o)()        -> [object Object] mark=bound
  new       new who()            -> [object Object]

[2] 우선순위 -- 한 호출식에 규칙이 둘 이상 걸리면
  new beats bind                 -> [object Object]
  call beats implicit            -> [object Object] mark=called
  bind beats implicit            -> [object Object] mark=bound

[3] 점 왼쪽이 있어도 암시적 바인딩이 아닌 자리
  (holder.who)()                 -> [object Object] mark=holder
  (0, holder.who)()              -> globalThis
  (holder.who = holder.who)()    -> globalThis
  (true && holder.who)()         -> globalThis
  holder?.who()                  -> [object Object] mark=holder

[4] 원시값을 this 로 주면 -- 비엄격은 감싸고 엄격은 그대로 둔다
  this = 7          sloppy [object Number]          strict number 7
  this = s          sloppy [object String]          strict string s
  this = true       sloppy [object Boolean]         strict boolean true
  this = null       sloppy globalThis               strict null
  this = undefined  sloppy globalThis               strict undefined
```

**왜 그런가**

- ★★★ **함수 객체는 하나다.** `who` 를 한 번 정의하고 아홉 번 다르게 불렀을 뿐이다.
  ★ **답을 바꾼 것은 호출식의 모양**이다 — 점 왼쪽이 있나, `call` 로 줬나, `new` 를 붙였나.
  ★★ 점 왼쪽이 **중첩이면 바로 왼쪽**이 이기고(`nested.inner.who()` → `inner`), 배열 원소 호출은 **배열 자신**이다.
- ★★★ **우선순위 한 줄** — **`new` > `bind`/`call`/`apply` > 점 왼쪽 > 기본.**
  `[2]` 의 세 줄이 각각 그 세 경계를 하나씩 확인한다.
- ★★★ **`[3]` 에서 암시적 바인딩이 살아남는 것은 둘**이다 — `(holder.who)()` 와 `holder?.who()`.
  나머지 셋(`(0, holder.who)()` · `(holder.who = holder.who)()` · `(true && holder.who)()`)은 **기본 바인딩**이 됐다.
  ★★ **갈림의 기준은 「참조가 그대로 남아 있느냐」 하나**다. 괄호로만 감싸거나 `?.` 를 쓰면 참조가 유지되고,
  쉼표 연산자·대입·논리 연산자를 거치면 **값(함수 객체)만 남고 점 왼쪽이 버려진다.**
- ★★ **`[4]` 는 다섯 줄이 전부 갈린다.** 비엄격은 원시값을 **객체로 감싸고**(`[object Number]`·`[object String]`·`[object Boolean]`)
  엄격은 **그대로 둔다**(`number 7`·`string s`·`boolean true`).
- ★ **`null`·`undefined` 는 비엄격에서 `globalThis` 로 바뀌고** 엄격에서는 **그대로** `null`·`undefined` 다.

### 2. 같은 탐침을 두 모드로 컴파일하면 — **열네 칸 중 아홉이 갈린다** ★★★

**출력**

```text
===== node20 js06b-07b-mode-matrix.js (exit=0) =====
  probe                             sloppy                    strict
  --------------------------------------------------------------------------------------
  plain call                        globalThis                undefined   <- differs
  callback of forEach               globalThis                undefined   <- differs
  this from call(7)                 [object Number]           number 7   <- differs
  this from call(null)              globalThis                null   <- differs
  this from call(undefined)         globalThis                undefined   <- differs
  detached method (guarded)         undefined                 undefined
  detached method (unguarded)       undefined                 TypeError: Cannot read properties of undefined (reading 'n')   <- differs
  method kept on the object         obj                       obj
  arrow at top of the fn            globalThis                undefined   <- differs
  arrow called with call(7)         globalThis                undefined   <- differs
  this inside new                   {"x":1}                   {"x":1}
  assigning to an undeclared name   assigned 1                ReferenceError: undeclared_strict is not defined   <- differs
  this in a getter                  g                         g
  setTimeout-like: fn passed along  undefined                 undefined

  probes 14 · same 5 · DIFFER 9
```

**왜 그런가**

- ★★★ **갈린 칸은 아홉**이다. 맨 아래 줄이 그것을 기계로 센다 — `probes 14 · same 5 · DIFFER 9`.
  ★ **이 한 줄이 이 주제의 고정 행**이다: **`this` 는 「설정에 달린」 기능**이다.
- ★★★ **안 갈리는 다섯**은 이렇다 — 방어를 넣은 떼어 낸 메서드 · 점이 붙어 있는 메서드 · `new` 안의 `this` ·
  게터 안의 `this` · 함수에 넘겨 대신 부른 메서드.
  ★★ **점이 붙어 있으면 모드가 상관없다.** 모드가 바꾸는 것은 「**아무 규칙도 안 걸렸을 때의 기본값**」뿐이기 때문이다.
- ★★★ **방어를 넣은 줄은 두 모드가 같은 글자인데 이유가 다르다.**
  비엄격은 `this` 가 `globalThis` 이고 **`globalThis.n` 이 `undefined`** 라서,
  엄격은 **`this` 자체가 `undefined`** 라서 `this && this.n` 이 단락 평가로 `undefined` 가 된다.
  ★★ 그래서 **방어를 빼면 갈린다** — 비엄격은 여전히 `undefined`, 엄격은 `TypeError` 다.
  **같은 버그가 한쪽에서는 조용하고 한쪽에서는 시끄럽다.**
- ★★ **화살표 두 줄이 갈리는 것**이 「화살표에 `this` 가 없다」를 반박한다.
  없는 것이라면 모드와 무관해야 한다. 실제로는 **바깥의 `this` 를 쓰고**, 그 바깥이 모드에 따라 다르므로 **같이 갈린다.**
  ★ 맞는 문장은 「**자기 `this` 를 안 만든다**」다.
- ★★ **이름을 모드마다 다르게 만든 이유** — 같게 두면 **비엄격 판이 먼저 돌며 전역 프로퍼티를 만들고**,
  엄격 판의 대입이 **이미 있는 전역에 쓰는 것**이 되어 `ReferenceError` 가 안 난다. 실제로 한 번 그렇게 잘못 나왔다.
- ★ **`new Function` 을 쓴 이유**는 둘이다 — ① `SyntaxError` 는 `try`/`catch` 로 못 잡으므로 **파싱 단계까지 받아야** 하고,
  ② 파일로 던지면 진단에 **절대 경로**가 박힌다.

### 3. 점 하나가 사라지면 — **함수는 같고 호출식만 다르다** ★★★

**출력**

```text
===== node20 js06b-07c-detached.js (exit=0) =====
[1] 같은 함수인데 점이 있고 없고로 갈린다
  user.greet()                         -> "hi kim"
  const g = user.greet; g()            -> "hi undefined"
  same function object?                -> true

[2] 떼어 내는 모양이 여럿이다 -- 전부 같은 사고다
  passed to another function           -> "hi undefined"
  stored in an array                   -> "hi undefined"
  assigned to another object           -> "hi lee"
  used as a callback of map            -> "hi undefined"
  destructured out                     -> "hi undefined"

[3] 왜 조용한가 -- this 가 무엇이 되어 있나
  holder2.where()                      -> "[object Object] name=\"kim\""
  detached where()                     -> "[object global] name=undefined"
  globalThis.name in this host         -> undefined

[4] 엄격 모드에서는 조용하지 않다
  strict method, attached              -> "hi kim"
  strict method, detached              -> TypeError: Cannot read properties of undefined (reading 'name')

[5] 고치는 세 가지 -- 무엇을 옮기는지가 다르다
  bind at handoff                      -> "hi kim"
  wrap in an arrow                     -> "hi kim"
  bind in the constructor-ish factory  -> "hi park"
  arrow as the method itself           -> "hi undefined"
```

**왜 그런가**

- ★★★ **`g === user.greet` 가 `true` 다.** 그러니 달라진 것은 **함수가 아니라 호출식**이다.
  `user.greet()` 는 점 왼쪽이 있고 `g()` 는 없다 — 그게 전부다.
- ★★★ **`[2]` 에서 하나만 다르다** — `other.greet = user.greet` 뒤의 `other.greet()` 가 `"hi lee"` 다.
  ★ **점이 새로 생겼기** 때문이다. 이 줄이 규칙을 **거꾸로** 확인해 준다 — 점이 없어지면 잃고, 새로 붙이면 그 객체가 들어온다.
- ★★★ **`[3]` 이 「왜 에러가 안 나나」다.** `this` 가 `globalThis` 가 되었고 **그 객체에 `name` 이라는 프로퍼티가 있거나 없거나**
  둘 다 **읽기 자체는 성공**한다. 이 호스트에서는 `undefined` 라 `"hi undefined"` 가 나온다.
  ★★ **브라우저에서는 `window.name` 이 빈 문자열**이라 `"hi "` 가 된다(7번 문항) —
  **같은 버그인데 브라우저 쪽이 더 조용하다.** 사람 눈에는 그냥 이름이 안 채워진 것처럼 보인다.
- ★★ **`[4]` 에서 같은 코드가 `TypeError: Cannot read properties of undefined (reading 'name')` 가 된다.**
  엄격 모드에서는 `this` 가 `undefined` 라 **프로퍼티 읽기 자체가 실패**한다 — **값이 아니라 예외로 바뀐다.**
- ★ **`[5]` 의 마지막 줄은 고침이 아니다.** 화살표를 **메서드 자리**에 쓰면 그 객체를 안 본다 —
  객체 리터럴을 쓴 **바깥 자리의 `this`** 를 보기 때문이다(4번 문항 `[3]`).

### 4. 화살표를 넣으면 무엇이 달라지나 — **바꿀 자기 칸이 없다** ★★★

**출력**

```text
===== node20 js06b-07d-arrow.js (exit=0) =====
[1] 화살표는 바깥에서 this 를 가져온다 -- 이름을 찾듯이
  method + inner function()              -> "globalThis"
  method + inner arrow                   -> "[object Object] mark=obj"
  three arrows deep                      -> "[object Object] mark=obj"

[2] 화살표는 call/apply/bind 로도 안 바뀐다
  arrow: plain / call / apply / bind     -> ["[object Object] mark=host2","[object Object] mark=host2","[object Object] mark=host2","[object Object] mark=host2"]
  function(): plain / call               -> ["globalThis","[object Object] mark=forced"]

[3] 화살표를 메서드로 쓰면 깨진다
  arrow as a method                      -> "[object Object]"
  shorthand method                       -> "[object Object] mark=fine"
  what the arrow actually saw            -> "[object Object]"

[4] 그런데 콜백으로는 화살표가 맞는 도구다
  forEach + function()                   -> ["globalThis","globalThis"]
  forEach + arrow                        -> ["[object Object] mark=timer","[object Object] mark=timer"]

[5] 화살표에 없는 것이 this 만은 아니다
  new on an arrow                        -> TypeError: A is not a constructor
  arrow has a prototype property?        -> false
  function has one?                      -> true
  class field arrow keeps this           -> ["[object Object] mark=C","[object Object] mark=C"]
  class method loses this                -> ["[object Object] mark=C","undefined"]
```

**왜 그런가**

- ★★★ **`[2]` 의 네 값이 전부 같다.** 못 바꾸는 것은 **화살표의 `this`** 이고, 이유는 **바꿀 자기 칸이 없어서**다.
  화살표는 호출될 때 `this` 를 받지 않는다 — 몸통의 `this` 는 **바깥 함수의 것을 이름처럼 찾아 읽는 것**이다.
  ★ 같은 자리의 `function` 은 `call` 로 바뀐다(`mark=forced`). **칸이 있느냐가 갈림**이다.
- ★★★ **`[3]` 에서 화살표 메서드가 본 것은 `[object Object]`** 인데, 세 번째 줄이 그것의 정체를 보인다 —
  **객체 리터럴이 아니라 이 모듈의 최상위 `this`**(Node CommonJS 에서는 `module.exports`)다.
  ★★ 두 줄의 브랜드가 같아 보이는 것이 함정이라, **세 번째 줄을 일부러 넣어** 같은 값임을 보였다.
  ★ 브라우저였다면 `globalThis (window)` 로 찍혀 더 확실했을 것이다(7번 문항).
- ★★ **`[4]` 와 `[3]` 을 가르는 한 문장** — **화살표는 「바깥 `this` 를 그대로 이어야 하는 자리」에 맞고
  「자기 객체를 받아야 하는 자리」에는 안 맞는다.** 콜백은 앞이고 메서드는 뒤다.
- ★★ **`[5]` 의 마지막 두 줄이 갈리는 이유** — **클래스 필드 화살표는 인스턴스가 만들어질 때 그 인스턴스를 바깥 `this` 로 잡는다.**
  그래서 떼어 내도 `mark=C` 다. **클래스 메서드는 프로토타입에 얹혀 있어** 떼면 점이 사라지고,
  클래스 몸통은 **언제나 엄격**이라 `undefined` 가 된다. ★ **떼어 내도 안 깨지는 쪽은 필드 화살표**다.
- ★ **화살표에 없는 것 둘 더** — **`prototype` 프로퍼티**(그래서 `new` 를 못 받는다)와 **자기 `arguments`**(08번).
  ★ `super`·`new.target` 도 자기 것을 안 만든다.

### 5. `bind` 를 두 번 걸면 — **안쪽이 이긴다** ★★

**출력**

```text
===== node20 js06b-07e-bind.js (exit=0) =====
[1] 두 번 bind 해도 안쪽이 이긴다
  bind(A)()                              -> "A"
  bind(A).bind(B)()                      -> "A"
  bind(A).call(B)                        -> "A"
  bind(A).apply(B)                       -> "A"
  attached as a method of B              -> "A"

[2] bind 는 새 함수다 -- 원본은 그대로다
  bound === original                     -> false
  two binds of the same fn are equal?    -> false
  original still floats                  -> undefined

[3] 인자도 앞에서부터 박힌다 -- 그것도 되돌릴 수 없다
  add.bind(null, 1)(2, 3)                -> [1,2,3]
  add.bind(null, 1).bind(null, 9)(3)     -> [1,9,3]
  add.bind(null, 1, 2, 3)(9, 9)          -> [1,2,3]

[4] 바인딩된 함수의 이름과 length
  name / length of the original          -> ["named",3]
  name / length after bind(null)         -> ["bound named",3]
  name / length after bind(null, 1)      -> ["bound named",2]
  name after two binds                   -> "bound bound named"
  bound fn has a prototype property?     -> false

[5] new 는 bind 를 이긴다 -- 이 한 자리만 예외다
  new Bound()                            -> {"x":7}
  prototype chain still points at C      -> true
  instanceof C                           -> true
  Bound() without new (sloppy)           -> "no throw"
  new on a bound arrow                   -> TypeError: A is not a constructor
```

**왜 그런가**

- ★★★ **「한 겹 더 감싼다」가 맞는 그림이다.** `bind` 는 원본을 고치지 않고 **새 함수**를 만든다.
  두 번째 `bind` 는 **첫 번째가 만든 함수**를 감싸는데, 그 안쪽은 이미 `A` 로 못질돼 있어 바깥이 준 `this` 가 **쓰이지 않는다.**
  ★ 그래서 `call`·`apply` 로 덮어도, 점을 새로 붙여도 전부 `"A"` 다.
- ★★ **`[2]` 가 「새 함수」를 확인한다.** `bind` 결과는 원본과 다르고, 두 번 `bind` 한 것끼리도 다르다. **원본은 그대로 떠다닌다.**
- ★★ **인자는 앞에서부터 박힌다.** `add.bind(null, 1).bind(null, 9)(3)` 이 `[1,9,3]` 이다 —
  안쪽이 `1` 을 잡고, 바깥이 준 `9` 가 그다음, 호출 시 준 `3` 이 마지막이다.
  ★ 다 채운 뒤의 인자는 **버려진다**(`[1,2,3]`).
- ★★ **`[4]` 의 흔적** — 이름에 **`bound ` 접두**가 붙고 두 번이면 `bound bound named` 다.
  `length` 는 **박은 인자 수만큼 줄고**(`3` → `2`), **`prototype` 프로퍼티는 없다.**
- ★★★ **`[5]` 가 유일한 예외다.** **`new` 가 `bind` 를 이긴다** — 못질한 `this` 를 무시하고 갓 만든 객체를 쓴다.
  ★ **프로토타입은 원본(`C.prototype`)의 것**이라 `instanceof C` 가 `true` 다. 박아 둔 인자 `7` 은 그대로 남아 `{"x":7}` 가 된다.
- ★ **바인딩된 화살표에 `new` 를 걸면 여전히 `TypeError: A is not a constructor`** 다.
  `bind` 는 **생성자 능력을 만들어 주지 않는다** — 원본이 생성자일 때만 물려받는다.

### 6. `new` 를 붙이거나 빼면 — **네 단계, 그리고 예외 하나** ★★

**출력**

```text
===== node20 js06b-07f-new.js (exit=0) =====
[1] 단계를 하나씩 관찰한다
  (1) this is a brand new object           -> [0,false]
  (2) its prototype is C.prototype         -> true
  (2) so it inherits                       -> "from prototype"
  (3) the body runs with it as this        -> {"x":1,"y":2}
  (4) it comes back with no return stmt    -> "object"

[2] 4단계의 예외 -- 객체를 돌려주면 그것이 이긴다
  return an object                         -> {"x":"returned"}
  return a primitive                       -> {"x":1}
  return an array                          -> [9]
  return a function                        -> "function"
  return null                              -> {"x":1}

[3] new 없이 부르면 -- 조용히 전역을 더럽힌다
  Point(1, 2) with no new (sloppy)         -> [null,1,2]
  the same in strict mode                  -> TypeError: Cannot set properties of undefined (setting 'x')

[4] new.target 이 그 둘을 가른다
  new Guarded(1)                           -> {"x":1}
  Guarded(1)                               -> "called without new"
  new.target is the function itself        -> true

[5] new 를 못 받는 것들
  new on an arrow                          -> TypeError: A is not a constructor
  new on a shorthand method                -> TypeError: o.m is not a constructor
  new on a getter-made function            -> TypeError: o.g is not a constructor
  class called without new                 -> TypeError: Class constructor K cannot be invoked without 'new'
  new on a class                           -> {"k":1}
  new on Math.max                          -> TypeError: Math.max is not a constructor
```

**왜 그런가**

- ★★★ **`[1]` 의 네 줄이 네 단계에 하나씩 짝지어진다.**
  ① `this` 는 **키가 0개인 새 객체**이고 `globalThis` 가 아니다(`[0,false]`) ·
  ② 그 객체의 프로토타입이 **`Point.prototype`** 이라 상속이 따라온다(`"from prototype"`) ·
  ③ 그 객체를 `this` 로 몸통이 돈다(`{"x":1,"y":2}`) · ④ `return` 이 없어도 **그 객체가 돌아온다**(`"object"`).
- ★★★ **`[2]` 의 기준은 「객체냐 아니냐」 하나**다. 객체·배열·함수를 돌려주면 **그것이 이기고**,
  숫자와 `null` 은 **무시되어** 만들던 객체가 돌아온다. ★ `null` 이 객체가 아니라는 사실이 여기서 드러난다.
- ★★ **`[3]` 의 첫 줄 `[null,1,2]`** — 첫 칸은 **`Point(1,2)` 의 반환값**이다. 그 함수는 아무것도 안 돌려주므로 `undefined` 이고,
  `JSON.stringify` 가 배열 안의 `undefined` 를 `null` 로 찍는다(31번 주제).
  둘째·셋째 칸은 **`globalThis.x`·`globalThis.y`** — `this` 가 전역이라 **거기에 프로퍼티가 생겼다.**
  ★★ **에러가 한 줄도 안 났다.** 엄격에서는 `TypeError` 다.
- ★★ **`new.target` 은 `new` 면 그 함수 자신, 아니면 `undefined`** 다. 그래서 한 함수가 두 경우를 갈라 처리할 수 있다.
  ★ **`class` 는 그 검사를 언어가 해 준다** — `Class constructor K cannot be invoked without 'new'`.
- ★ **`[5]` 에서 `new` 를 받는 것은 하나**다 — `class K` 뿐이다.
  화살표·단축 메서드·게터가 만든 함수·`Math.max` 는 전부 `is not a constructor` 이고, `class` 를 `new` 없이 부르면 `TypeError` 다.

### 7. 누가 부르느냐 — 콜백과 타이머 ★★★

**출력**

```text
===== node20 js06b-07g-callbacks.js (exit=0) =====
[1] 배열 메서드는 두 번째 인자로 this 를 받는다
  forEach, no thisArg                    -> globalThis
  forEach, thisArg given                 -> [object Object] mark=given ctor=Object
  map, thisArg given                     -> [object Object] mark=given ctor=Object
  filter, thisArg given                  -> 1
  some/every take one too                -> true
  reduce does NOT take one               -> globalThis
  sort comparator saw                    -> globalThis

[2] 화살표를 주면 thisArg 가 무시된다
  forEach + arrow, thisArg given         -> [object Object] ctor=Object

[3] 메서드를 그대로 넘기면 떨어진다 -- 그리고 고치는 법 셋
  [1,2].forEach(counter.bump)            -> 0
  thisArg                                -> 2
  bind                                   -> 2
  arrow wrapper                          -> 2

[4] 타이머는 호스트가 정한다 -- 그래서 여기 값은 Node 의 것이다
  setTimeout(function(){}) this          -> [object Object] ctor=Timeout
  setTimeout(t.m) this                   -> [object Object] ctor=Timeout
  setTimeout(t.m.bind(t)) this           -> [object Object] mark=tb ctor=Object
  setTimeout(arrow inside cb) this       -> [object Object] ctor=Timeout
```

**그리고 브라우저** — 호스트 페이지는 네 줄이고 실제 검사는 옆의 `.js` 가 한다.

```text
<!doctype html><meta charset="utf-8"><title>this in a browser</title>
<p>이 페이지는 값을 찍기만 한다.</p>
<pre id="out"></pre>
<script src="js06b-07h-browser.js"></script>
```

```js
// js06b-07h-browser.js
// 같은 질문을 브라우저에 던진다 -- 호스트가 정하는 칸이 어디인지 가리려는 것이다.
function brand(t) {
  if (t === undefined) return "undefined";
  if (t === null) return "null";
  if (t === globalThis) return "globalThis (window)";
  if (typeof t === "object" || typeof t === "function") {
    return Object.prototype.toString.call(t) + (t.mark ? " mark=" + t.mark : "");
  }
  return typeof t + " " + String(t);
}
function loose() { return brand(this); }
function tight() { "use strict"; return brand(this); }

const user = { name: "kim", greet() { return "hi " + this.name; } };
const detached = user.greet;
const arrowMethod = { name: "kim", greet: () => "hi " + String(this && this.name) };

const rows = [
  ["top-level this in a classic script", brand(this)],
  ["sloppy f()", loose()],
  ["strict f()", tight()],
  ["sloppy f.call(7)", loose.call(7)],
  ["strict f.call(7)", tight.call(7)],
  ["user.greet()", user.greet()],
  ["detached greet() -- the silent one", detached()],
  ["window.name is", JSON.stringify(window.name)],
  ["arrow used as a method", arrowMethod.greet()],
  ["brand of globalThis", Object.prototype.toString.call(globalThis)],
  ["top-level arrow: arguments?", (() => { try { return String(arguments.length); } catch (e) { return e.constructor.name + ": " + e.message; } })()],
  ["forEach with no thisArg (sloppy)", (() => { let r; [1].forEach(function () { r = brand(this); }); return r; })()],
];

setTimeout(function () {
  rows.push(["setTimeout(fn) this", brand(this)]);
  rows.push(["addEventListener this", "see below"]);
  const btn = document.createElement("button");
  btn.id = "b1";
  btn.addEventListener("click", function () {
    rows[rows.length - 1] = ["addEventListener this", brand(this) + " id=" + this.id];
    document.getElementById("out").textContent =
      rows.map(([k, v]) => k.padEnd(38) + " : " + v).join("\n");
  });
  document.body.appendChild(btn);
  btn.click();
}, 0);
```

```text
===== google-chrome --headless --disable-gpu --no-sandbox --virtual-time-budget=1000 --dump-dom js06b-07h-browser.html 2>/dev/null | sed -n '/^<pre id="out">/,/<\/pre>/p' (exit=0) =====
<pre id="out">top-level this in a classic script     : globalThis (window)
sloppy f()                             : globalThis (window)
strict f()                             : undefined
sloppy f.call(7)                       : [object Number]
strict f.call(7)                       : number 7
user.greet()                           : hi kim
detached greet() -- the silent one     : hi 
window.name is                         : ""
arrow used as a method                 : hi 
brand of globalThis                    : [object Window]
top-level arrow: arguments?            : ReferenceError: arguments is not defined
forEach with no thisArg (sloppy)       : globalThis (window)
setTimeout(fn) this                    : globalThis (window)
addEventListener this                  : [object HTMLButtonElement] id=b1</pre>
```

**왜 그런가**

- ★★★ **두 호스트에서 갈린 칸은 넷이다.**
  ① **최상위 `this`** — 브라우저는 `globalThis (window)`, Node CJS 는 `module.exports`(`[object Object]`) ·
  ② **`globalThis` 의 브랜드** — `[object Window]` 대 `[object global]` ·
  ③ **`setTimeout` 콜백의 `this`** — `globalThis (window)` 대 `Timeout` 객체 ·
  ④ **`globalThis.name`** — `""` 대 `undefined`.
  ★ 나머지는 한 글자도 같다 — 엄격 `f()` 가 `undefined`, `call(7)` 의 두 모드, `forEach` 콜백의 `globalThis`.
- ★★★ **④가 「조용함의 모양」을 바꾼다.** 떼어 낸 `greet()` 이 브라우저에서 `"hi "`, Node 에서 `"hi undefined"` 다.
  ★★ **브라우저 쪽이 더 조용하다** — `undefined` 라는 글자조차 안 보여서, 화면상으로는 그냥 이름이 빈 것처럼 보인다.
  ★ 화살표 메서드도 같은 이유로 브라우저에서 `"hi "` 다.
- ★★ **`thisArg` 를 안 받는 것은 `reduce` 와 `sort`** 다. `reduce` 의 세 번째 인자는 그냥 버려지고(`globalThis`),
  `sort` 의 비교 함수도 `globalThis` 를 본다.
  ★ **화살표를 주면 받는 메서드에서도 무시된다** — 받을 칸이 없기 때문이다(4번 문항).
- ★★ **Node 의 `setTimeout` 콜백 `this` 는 `Timeout` 객체**다(`ctor=Timeout`).
  ★★★ 이것은 **호스트가 정하는 층**이다 — ECMA-262 는 타이머를 정의하지 않는다. `bind` 로 못질하면 양쪽이 같아진다.
- ★ **`addEventListener` 의 `this` 는 DOM 이 정한다** — 이벤트가 걸린 그 요소다(`[object HTMLButtonElement] id=b1`).
  ★ `[3]` 의 `[1,2].forEach(counter.bump)` 뒤 `c.n` 이 **`0`** 인 것이 이 문항의 조용한 실패다 — `globalThis.n` 이 대신 올라갔다.

### 8. 왜 `this` 만 다른 규칙인가 — **이름은 소스가, `this` 는 호출이 정한다** ★★★

**왜 그런가**

- ★★★ **한 문장씩 대비하면 이렇다.**
  [06번](../06-scope-and-closures/2-summary.md) — **이름은 「함수가 정의된 자리」가 정한다.** 부른 자리는 상관없다.
  이 주제 — **`this` 는 「함수가 불린 모양」이 정한다.** 정의된 자리는 상관없다.
  ★ 두 규칙이 **정확히 반대**라 하나를 다른 쪽에 적용하면 전부 틀린다.
- ★★★ **화살표는 06번 쪽 규칙을 따른다.** 자기 `this` 를 안 만들고 **바깥에서 이름처럼 찾아** 읽는다.
  ★★ 그래서 헷갈린다 — **한 언어 안에 두 규칙이 있고, 함수 표기 하나로 갈린다.**
  `function` 으로 쓰면 호출식이 정하고 `=>` 로 쓰면 소스가 정한다.
- ★★ **실무에서는 「이 함수의 호출부를 전부 찾아야 한다」는 뜻**이다.
  함수 본문만 읽고는 `this` 가 무엇인지 알 수 없으므로, **넘기는 자리가 곧 버그 후보**가 된다.
- ★★ **파이썬은 `self` 를 매개변수로 적는다.** 그래서 「떼어 내면 잃는다」가 **성립하지 않는다** —
  `obj.method` 를 꺼내면 **바운드 메서드라는 객체**가 만들어져 `obj` 를 이미 들고 있다.
  ★ JS 는 그 「들고 있는 객체」를 **`bind` 로 사람이 직접 만들어야** 한다. **`bind` 가 파이썬의 바운드 메서드 자리**다.
- ★ **이 주제를 한 질문으로 줄이면** — **「이 괄호 바로 왼쪽에 무엇이 붙어 있나?」**

### 9. 보장인가 호스트인가 사정인가 — **호스트 칸이 두껍다** ★★★

**왜 그런가**

- ★★★ **명세 보장 다섯** — ① **호출식이 `this` 를 정한다** ② **판정 순서 `new` → 명시적 → 암시적 → 기본**
  ③ **비엄격 기본은 `globalThis`, 엄격은 `undefined`** ④ **`bind` 는 되돌릴 수 없고 `new` 만 그것을 이긴다**
  ⑤ **화살표는 자기 `this` 를 안 만들고 `call`·`apply`·`bind`·`thisArg` 로 못 바꾼다.**
  ★ 여기에 **`new` 의 네 단계와 객체 반환 예외**, **`reduce`·`sort` 가 `thisArg` 를 안 받는 것**도 명세다.
- ★★★ **호스트가 정하는 칸 넷** — 최상위 `this` · `globalThis` 의 브랜드 · **타이머 콜백의 `this`** · `globalThis.name`.
  ★★ 그중 **조용함의 모양을 바꾸는 것은 `globalThis.name`** 이다 — `""` 냐 `undefined` 냐로 같은 버그의 겉모습이 달라진다.
  ★ `addEventListener` 의 `this` 도 호스트(DOM) 쪽이다.
- ★★ **「엄격 모드에서 기본 `this` 가 `undefined`」는 명세 보장**이다. 모드가 답을 바꾸는 것 자체가 명세에 적힌 규칙이다.
- ★★ **「`setTimeout` 의 `this` 가 `Timeout` 객체」는 호스트**다. ECMA-262 에는 타이머가 없다.
  ★ 「`Timeout` 이라는 이름」까지는 Node 의 구현 사정이라 더 아래 층이다 — 이 문서는 **그 객체의 내부 필드를 한 줄도 안 찍었다.**
- ★ **부적용인 창은 「여러 번 돌려 흔들림을 본다」 하나**다. 이 주제에는 **난수·시각·순서 비보장이 한 칸도 없어** 잴 것이 없다.
  ★★ **그 덕에 같은 판에서 다시 돌리면 한 글자도 안 변한다** — 재대조 54블록 전부 동일이었다.

### 10. 경계 — 어디까지가 이 주제인가 ★★

**왜 그런가**

- **정본은 각각 이렇다.**
  **`call`/`apply`/`bind` 의 API 세부** → [목록의 **09번 주제**](../09-call-apply-bind/) · **엄격 모드** → 목록의 **35번 주제** ·
  **클래스 필드** → [목록의 **16번 주제**](../16-class-syntax/) · **이벤트 루프** → 목록의 **36번 주제** ·
  **브랜드 태그로 타입을 가리는 것** → 목록의 **34번 주제**.
- ★★★ **06번에서 이어받는 것** — **화살표의 `this` 는 렉시컬이다.** 그 한 칸은 06번의 규칙 그대로다.
  **06번에서 뒤집는 것** — **나머지 전부.** `this` 는 정의된 자리가 아니라 호출식이 정한다.
- ★★ **08번이 이어받는 것** — **화살표에 없는 것이 `this` 만이 아니라는 것.** `arguments`·`prototype`·생성자 능력이 같이 없고,
  08번이 그 형태별 차이 표의 정본이다.
- ★ **모듈(ESM)의 최상위 `this` 를 여기서 안 다룬 이유**는 그것이 **모듈 평가 규칙**이기 때문이다 — 42번 주제의 몫이다.
  이 배치는 **CommonJS 와 브라우저 classic script 두 자리**만 던졌다.
- ★ **이 주제가 끝까지 책임지는 것 셋** — ① 네 규칙과 우선순위로 임의의 호출식을 판정하는 것
  ② **엄격 모드가 답을 바꾸는 칸이 어디인지** ③ 화살표가 왜 다르고 어디에 맞는지.

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js06b-07a-four-rules.js` | 네 규칙 아홉 줄 · **우선순위 세 줄** · 참조가 풀리는 다섯 줄 | node20 1벌 + node18 대조 1벌 |
| `js06b-07b-mode-matrix.js` | ★★★ **엄격·비엄격 14칸 중 9칸이 갈린다**는 것 | node20 1벌 + node18 대조 1벌 |
| `js06b-07c-detached.js` | 떼어 내는 다섯 모양 · **왜 조용한가** · 고침 셋 | node20 1벌 + node18 대조 1벌 |
| `js06b-07d-arrow.js` | 화살표를 **못 바꾼다**는 것 · 메서드 자리에서 깨지는 것 · 클래스 필드 | node20 1벌 + node18 대조 1벌 |
| `js06b-07e-bind.js` | `bind` 가 **한 겹 더 감싼다**는 것 · `new` 가 그것을 이기는 것 | node20 1벌 + node18 대조 1벌 |
| `js06b-07f-new.js` | `new` 의 **네 단계**와 객체 반환 예외 · `new.target` | node20 1벌 + node18 대조 1벌 |
| `js06b-07g-callbacks.js` | `thisArg` 를 받는 것과 안 받는 것 · **조용한 실패** · 타이머 | node20 1벌 + node18 대조 1벌 |
| `js06b-07h-browser.js` | ★★★ **호스트가 정하는 칸 넷** · 브라우저 쪽이 더 조용하다는 것 | Chrome 151 1벌 |
| `js06b-07x-forms.js` | 형태 — `node --check` **진단 0줄**(빈 출력도 블록으로) | node20 1벌 |
| `js06b-vdiff.sh` | 여덟 스크립트가 **두 판에서 한 글자도 같다**는 것 | 1벌 |
| `js06b-versions.sh` | 이 문서의 모든 출력이 **어느 판에서 나왔나** | 1벌 |

**구현 의존 항목** — 다음은 **이 환경(node 20.19.6 / 18.19.1 · Chrome 151 · x86-64 Linux)에서만** 그렇다.

- ★★ **예외 메시지 문구 전부** — `Cannot read properties of undefined (reading 'name')` ·
  `A is not a constructor` · `Class constructor K cannot be invoked without 'new'`.
  **종류는 명세, 문구는 V8 의 것**이다.
- ★★ **Node 타이머 콜백의 `this` 가 `Timeout` 이라는 이름** — Node 의 구현이다.
  **요점은 이름이 아니라 「전역이 아니다」라는 것**이고, 브라우저에서는 `window` 다.
- ★ **최상위 `this` 가 `module.exports` 인 것** — Node CommonJS 의 사정이다(05번).
- ★ **`globalThis.name` 이 Node 에서 `undefined`, 브라우저에서 `""` 인 것** — 호스트가 정한다.

**호출식이 `this` 를 정하는 것 · 판정 순서 · 두 모드의 기본값 · 원시 `this` 의 박싱 여부 · 참조가 풀리면 암시적 바인딩이 사라지는 것 · `bind` 가 되돌릴 수 없는 것 · `new` 가 그것을 이기는 것 · `new` 의 네 단계와 객체 반환 예외 · 화살표가 자기 `this` 를 안 만드는 것 · `reduce`·`sort` 가 `thisArg` 를 안 받는 것은 구현 의존이 아니다.**
어느 엔진에서도 같아야 한다.

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — ESM(`.mjs`)의 최상위 `this` · Web Worker · 다른 엔진(SpiderMonkey·JavaScriptCore) ·
  Node 18 보다 낮은 판 · `with` 문 · `Proxy` 로 가로챈 호출 · `super` 호출 안의 `this` ·
  **엄격 모드 파일 전체**에서 이 여덟 스크립트를 다시 돌리는 것.
- ★ **못 잰 것** — **`bind` 와 화살표 래퍼의 비용.** 함수 객체가 하나 더 생긴다는 것은 관찰했지만
  **얼마나 드는지는 재지 않았다.** 그래서 이 문서에는 「느리다」·「빠르다」가 한 줄도 없다.
- ★ **부적용인 창** — 「여러 번 돌려 흔들림을 본다」. 이 주제에는 **난수·시각·순서 비보장이 한 칸도 없어 잴 것이 없다.**

**판이 올랐을 때 다시 돌려야 하는 것**

- ★★ **예외 메시지 문구** — 다섯 블록에 들어 있다.
- ★★ **호스트가 정하는 칸 넷** — Node 나 브라우저가 바꾸면 그 줄이 바뀐다. 특히 **타이머 콜백의 `this`**.
- ★ **두 판 대조 결과** — 지금은 전부 같다. 갈리면 그것이 곧 그 주제의 결론이 된다.
- **네 규칙 자체는 다시 돌릴 필요가 없다** — 초판부터 바뀐 적이 없고, 화살표가 들어온 ES2015 이후로도 그대로다.
