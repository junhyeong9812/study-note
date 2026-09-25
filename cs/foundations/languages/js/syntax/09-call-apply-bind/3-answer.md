# js/syntax/09 — `call`·`apply`·`bind`: 「`this` 와 인자를 손으로 건넨다」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **node v20.19.6**(기본 판) · **node v18.19.1**(대조) · **Google Chrome 151.0.7922.173** · x86-64 Linux 에서 실제로 돌려 얻은 것이고,
> 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 하나도 없다).
>
> ★★ **예외는 `e.constructor.name` 과 `e.message` 로만 찍었다** — 스택트레이스에는 절대 경로가 박혀 재현이 안 된다.
> ★★★ **인자 개수의 경계는 자릿수로만 찍었다** — 정확한 수는 그 순간 스택 상태에 달려 흔들린다.
> ★★ **표준 출력과 표준 오류를 한 블록에도 안 섞었다** — 이 주제의 블록은 전부 표준 출력이다.
>
> **이 파일이 인용하는 출력을 낸 소스** — 전문은 [1-question.md](1-question.md) 의 같은 번호 문항에 있다.

```text
// js08b-09a-three-methods.js
// js08b-09b-bind.js
// js08b-09c-limits.js
// js08b-09d-fixes.js
// js08b-09h-browser.js
// js08b-09x-forms.js
// js08b-vdiff.sh
// js08b-versions.sh
```

> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ★★★ **인자 개수 경계의 정확한 수** — 자릿수만 싣는다 | ★★★ **브랜드 태그** · **설정에 달린 칸의 개수** |
> | Node 스택트레이스의 **절대 경로** — 한 줄도 싣지 않았다 | ★★★ **`bound ` 접두** · `length` 의 감소량 |
> | 예외 **문구**(판이 오르면 바뀐다) | ★★ **예외의 종류** · `instanceof` 결과 |
> | 브라우저 UA 문자열의 뒷자리 | ★★ **동일성 판정**(`bind` 는 매번 다른 객체) |
>
> ★ **이 주제의 블록에는 주소도 시간도 난수도 안 찍힌다.** 같은 판에서 다시 돌리면 한 글자도 안 변한다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 같은 값을 셋으로 건네면 — **세 열이 한 글자도 같다** ★★★

**출력**

```text
===== node20 js08b-09a-three-methods.js (exit=0) =====
[1] same this value through call / apply / bind -- sloppy callee
  this given      call                        apply                       bind()()
  object          [object Object] mark=given  [object Object] mark=given  [object Object] mark=given
  number 7        [object Number]             [object Number]             [object Number]
  string s        [object String]             [object String]             [object String]
  boolean true    [object Boolean]            [object Boolean]            [object Boolean]
  null            globalThis                  globalThis                  globalThis
  undefined       globalThis                  globalThis                  globalThis
  array           [object Array]              [object Array]              [object Array]
  function        [object Function]           [object Function]           [object Function]

[2] the same grid with a strict callee -- how many cells change
  this given      call                        apply                       bind()()
  object          [object Object] mark=given  [object Object] mark=given  [object Object] mark=given
  number 7        number 7                    number 7                    number 7
  string s        string s                    string s                    string s
  boolean true    boolean true                boolean true                boolean true
  null            null                        null                        null
  undefined       undefined                   undefined                   undefined
  array           [object Array]              [object Array]              [object Array]
  function        [object Function]           [object Function]           [object Function]
  settings-dependent cells      15 of 24

[3] how the arguments are handed over
  call(t, 1, 2, 3)              a=1 b=2 c=3 n=3
  apply(t, [1, 2, 3])           a=1 b=2 c=3 n=3
  apply(t, undefined)           a=undefined b=undefined c=undefined n=0
  apply(t, null)                a=undefined b=undefined c=undefined n=0
  apply(t, [])                  a=undefined b=undefined c=undefined n=0
  apply(t, arguments-like)      a=1 b=2 c=undefined n=2
  apply(t, { length: 3 })       a=undefined b=undefined c=undefined n=3
  apply(t, 'abc')               TypeError: CreateListFromArrayLike called on non-object
  apply(t, new Set([1, 2]))     a=undefined b=undefined c=undefined n=0
  apply(t, 7)                   TypeError: CreateListFromArrayLike called on non-object
  apply(t, true)                TypeError: CreateListFromArrayLike called on non-object
  call(t) with no args          a=undefined b=undefined c=undefined n=0
  Reflect.apply(f, t, [1, 2])   a=1 b=2 c=undefined n=2
  Reflect.apply(f, t, 'ab')     TypeError: CreateListFromArrayLike called on non-object
  f(...[1, 2, 3]) spread        a=1 b=2 c=3 n=3
```

**왜 그런가**

- ★★★ **세 열이 다른 줄은 0개**다. `call`·`apply`·`bind()()` 가 **`this` 를 정하는 규칙은 완전히 같다.**
  달라지는 것은 **인자를 어떻게 건네느냐**뿐이다. 이 사실이 이 주제의 뼈대다.
- ★★★ **설정에 달린 칸은 24칸 중 15칸**이다. 갈린 행은 **`number 7` · `string s` · `boolean true` · `null` · `undefined`** 다섯 줄
  × 세 열 = 15칸이고, **객체·배열·함수 세 줄은 안 갈린다.**
  ★★ 공통점은 「**원시값이거나 비어 있는 값**」이다. 비엄격은 그 둘을 **손보고**(감싸거나 전역으로 바꾸고) 엄격은 **그대로 둔다.**
  객체는 손볼 것이 없으니 두 모드가 같다.
- ★★★ **`String(this)` 로 찍었으면 `"7"` 이 나와 비엄격과 엄격이 구분되지 않았을 것이다.**
  비엄격의 `this` 는 **숫자가 아니라 `Number` 래퍼 객체**인데, 문자열로 만들면 **원시값과 똑같이 보인다.**
  ★ 그래서 이 주제의 본체 창이 **브랜드 태그**다 — `[object Number]` 와 `number 7` 은 눈으로 갈린다.
- ★★ **열다섯 모양 중 터지는 것은 셋**이다 — `apply(t, 'abc')` · `apply(t, 7)` · `apply(t, true)`.
  공통점은 「**둘째 인자가 객체가 아니다**」이고 문구는 셋 다 `CreateListFromArrayLike called on non-object` 다.
  ★ `null`·`undefined` 는 **예외로 허용**되어 인자 0개가 된다.
- ★★★ **`Set` 은 `length` 프로퍼티가 없어서 인자 0개**다. **`apply` 는 이터러블이 아니라 유사 배열을 본다.**
  `Set` 은 객체이므로 `TypeError` 조건에도 안 걸리고, `length` 가 `undefined` 라 **길이 0으로 읽힌다** —
  ★★ **에러도 안 나고 인자도 안 들어가는** 이 주제의 가장 조용한 실패다.
- ★ **`{ length: 3 }` 은 `undefined` 세 개를 넘긴다.** `arguments.length` 가 `3` 이다 —
  **인덱스 키가 없어도 길이만 보고 그만큼 만든다.**

### 2. `bind` 가 만든 함수는 무엇인가 — **원본이 아니라 한 겹 덧씌운 새 함수** ★★★

**출력**

```text
===== node20 js08b-09b-bind.js (exit=0) =====
[1] the bound function is a different object
  bound1 === orig                          -> false
  orig.name                                -> "orig"
  bound1.name                              -> "bound orig"
  orig.length                              -> 3
  bound1.length                            -> 2
  orig has prototype?                      -> true
  bound1 has prototype?                    -> false
  proto of bound1 is orig?                 -> false
  proto of bound1 is Function.prototype?   -> true
  bound1 own keys                          -> ["length","name"]
  String(bound1)                           -> function () { [native code] }

[2] you cannot rebind it -- the first bind wins
  bound1(2, 3)                             -> [object Object] mark=A args=1,2,3
  bound1.call(B, 2, 3)                     -> [object Object] mark=A args=1,2,3
  bound1.apply(B, [2, 3])                  -> [object Object] mark=A args=1,2,3
  bound1.bind(B)(2, 3)                     -> [object Object] mark=A args=1,2,3
  bound1.bind(B, 9)(3)                     -> [object Object] mark=A args=1,9,3
  ({ mark: 'host', m: bound1 }).m(2, 3)    -> [object Object] mark=A args=1,2,3
  Reflect.apply(bound1, B, [2, 3])         -> [object Object] mark=A args=1,2,3

[3] new beats bind -- but the bound arguments stay
  new BoundCtor(2).got                     -> [1,2]
  made instanceof Ctor                     -> true
  made instanceof BoundCtor                -> true
  made.kind (from prototype chain)         -> Ctor.prototype
  proto of made is Ctor.prototype?         -> true
  BoundCtor.prototype                      -> undefined
  new (bound arrow)                        -> TypeError: ba is not a constructor

[4] bind on an arrow changes nothing about this -- but still fixes arguments
  arrowFn(1, 2)                            -> [object Object] mark=outer args=1,2
  arrowFn.call(B, 1, 2)                    -> [object Object] mark=outer args=1,2
  arrowFn.bind(B)(1, 2)                    -> [object Object] mark=outer args=1,2
  arrowFn.bind(B, 9)(2)                    -> [object Object] mark=outer args=9,2
  arrowFn.bind(B).length                   -> 2
  arrowFn.bind(B, 9).length                -> 1

[5] borrowing a method -- the classic uses
  slice.call(arrayLike)                    -> ["a","b"]
  join.call(arrayLike, '-')                -> a-b
  uncurried hasOwn({ x: 1 }, 'x')          -> true
  uncurried hasOwn({ x: 1 }, 'y')          -> false
  uncurried toString([])                   -> [object Array]
  Math.max.apply(null, [3, 1, 2])          -> 3
  Math.max(...[3, 1, 2])                   -> 3

[6] how many wrappers does bind add
  depth 0 name="orig" length=3
  depth 1 name="bound orig" length=3
  depth 2 name="bound bound orig" length=3
  depth 3 name="bound bound bound orig" length=3
  4-deep bound call                        -> [object Object] mark=A args=undefined,undefined,undefined
```

**왜 그런가**

- ★★★ **`[1]`** — 이름은 `"bound orig"`(접두 `bound `), `length` 는 `3 - 1 = 2`,
  **`prototype` 은 없고**, 프로토타입은 **`Function.prototype`** 이다(원본이 아니다).
  소유 프로퍼티는 `length` 와 `name` 둘뿐이고 `String(bound1)` 은 `function () { [native code] }` 다.
  ★ **원본 소스가 안 나온다** — bound 함수는 소스 텍스트를 안 갖는다.
- ★★★ **`[2]` 의 다섯 경로 중 `this` 를 되돌린 것은 0개**다.
  `call`·`apply`·재`bind`·점 왼쪽·`Reflect.apply` **전부 `mark=A`** 다.
  ★★ **인자는 다르다** — `bound1.bind(B, 9)(3)` 이 `args=1,9,3` 이다.
  못질한 `1` 뒤에 `9`, 그 뒤에 `3` 이 붙는다. **`this` 는 못이고 인자는 앞쪽만 못**이다.
- ★★★ **`[3]` — `instanceof` 는 둘 다 `true`** 다.
  `BoundCtor.prototype` 은 `undefined` 인데도 그렇다. **bound 함수의 `instanceof` 는 원본의 `prototype` 을 본다.**
  ★ 만들어진 객체의 프로토타입도 `Ctor.prototype` 이라 `made.kind` 가 체인을 타고 나온다.
  ★★ **못질한 `this` 는 버려지고**(`ignored` 가 안 나온다) **못질한 인자는 남는다**(`got` 이 `[1,2]`).
  ★ 화살표를 `bind` 한 뒤 `new` 하면 **`TypeError: ba is not a constructor`** 다 — 08번 격자의 「자격」이 따라온다.
- ★★ **`[4]` — 화살표는 `this` 가 안 바뀌고 `length` 만 줄어든다.**
  `arrowFn.bind(B)(1,2)` 가 여전히 `mark=outer` 이고, `arrowFn.bind(B, 9).length` 는 `2 - 1 = 1` 이다.
  ★★ **바인딩 객체는 만들어진다.** 그래서 「무언가 일어났다」는 착각을 준다 — 실제로 바뀌는 것은 인자뿐이다.
- ★ **`[6]` — 겹칠 때마다 `bound ` 접두가 하나씩 더 붙는다**(`bound bound bound orig`).
  **`length` 는 `3` 그대로**다 — 인자를 못질하지 않고 `this` 만 걸었기 때문이다.
  네 겹 함수를 인자 없이 부르면 세 인자가 전부 `undefined` 다.

### 3. 인자 개수의 한계와 `thisArg` — **상한은 명세에 없다** ★★

**출력**

```text
===== node20 js08b-09c-limits.js (exit=0) =====
[1] where does each call form stop accepting arguments
  f.apply(null, arr)            last ok   6-digit   RangeError: Maximum call stack size exceeded
  Reflect.apply(f, null, arr)   last ok   6-digit   RangeError: Maximum call stack size exceeded
  f(...arr)  spread             last ok   6-digit   RangeError: Maximum call stack size exceeded
  f.bind(null, ...arr)()        last ok   6-digit   RangeError: Maximum call stack size exceeded
  new Array(n) itself           no fail   10-digit

[2] what the spec fixes -- these are not engine numbers
  Function.prototype.call.length    1
  Function.prototype.apply.length   2
  Function.prototype.bind.length    1
  Reflect.apply.length              3
  call is a function?               function
  Math.max.length                   2
  Math.max() with no args           -Infinity
  [].reduce.length                  1

[3] thisArg on built-ins -- which ones take one
  map           ["HOST"]
  filter        1
  forEach       "HOST"
  some          true
  every         true
  find          1
  flatMap       ["HOST"]
  reduce        undefined
  sort          [2,1]
  Array.from    ["HOST"]
```

**왜 그런가**

- ★★★ **네 호출 형태가 전부 여섯 자리 수에서 `RangeError: Maximum call stack size exceeded` 를 낸다.**
  ★★ **이 수는 명세에 없다** — V8 의 스택 크기가 정한다. 그래서 **자릿수와 예외 종류만** 싣는다.
  정확한 수는 그 순간 스택이 얼마나 차 있는지에 달려 흔들리고, **두 판 사이에서도 다르다.**
- ★★★ **`new Array(n)` 은 10자리까지 안 터진다.** 배열을 **만드는 일**은 막히지 않는다.
  막히는 것은 **그 배열을 호출 인자로 펴는 일**이다 — 인자가 스택에 올라가기 때문이다.
  ★ 그래서 대안은 「배열을 작게」가 아니라 「**펴지 말고 루프나 청크로**」다.
- ★★ **`[2]` 의 `length` 값은 명세가 정한 수**다(`call` 1 · `apply` 2 · `bind` 1 · `Reflect.apply` 3).
  ★ **`[1]` 은 엔진이 정하고 `[2]` 는 명세가 정한다** — 같은 「숫자」인데 성격이 정반대라 나란히 실었다.
- ★★★ **열 줄 중 `thisArg` 를 안 받는 것은 둘**이다 — **`reduce` 와 `sort`.**
  `reduce` 는 `undefined` 를, `sort` 는 정렬되지 않은 `[2,1]` 을 돌려줬다.
  ★★ **에러가 안 난다.** 인자를 받아 놓고 **쓰지 않는다** — 「통과도 출력이다」의 실례다.
  ★ 나머지 여덟(`map`·`filter`·`forEach`·`some`·`every`·`find`·`flatMap`·`Array.from`)은 `HOST` 를 받았다.

### 4. 떼어 낸 메서드를 고치는 네 가지 — **셋 다 고치고 셋 다 새 객체를 만든다** ★★

**출력**

```text
===== node20 js08b-09d-fixes.js (exit=0) =====
[1] four ways to hand the method to someone else
  detached()                         -> undefined n=NaN
  bound()                            -> counter n=1
  wrapped()                          -> counter n=2
  viaCall()                          -> counter n=3
  counter.n after those calls        -> 3

[2] are two fixes the same function object
  counter.inc === counter.inc           true
  bind twice gives the same fn?         false
  arrow twice gives the same fn?        false
  a saved bound fn === itself           true
  why it matters                        removeEventListener needs the same object

[3] a fake listener registry shows what that costs
  on(counter.inc.bind(counter))      -> 1
  off(counter.inc.bind(counter))     -> deleted=false left=1
  on(saved)                          -> 2
  off(saved)                         -> deleted=true left=1

[4] what each fix keeps and drops
  fix               name            length  proto?  new?
  original          "inc"           0       false   no:TypeError
  bound             "bound inc"     0       false   no:TypeError
  arrow wrapper     ""              0       false   no:TypeError
  bound with an arg "bound inc"     0       false   no:TypeError
  bound forwards later args          -> got 1,2
  arrow wrapper with no params       -> got 1,2
  arrow wrapper that drops args      -> got undefined,undefined
```

**왜 그런가**

- ★★★ **`detached()` 가 예외를 안 내는 이유** — 비엄격이라 `this` 가 **전역 객체**가 되고,
  `globalThis.n` 은 `undefined` 라 `undefined + 1` 이 `NaN` 이 된다. `this.mark` 도 `undefined` 다.
  ★★ **전역에 `n` 이라는 프로퍼티가 새로 생긴다** — 읽기도 쓰기도 되니 **터질 이유가 없다.**
  ★ 엄격이었다면 `this` 가 `undefined` 라 **`TypeError` 로 시끄럽게 실패**했을 것이다(07번).
- ★★★ **`bind` 는 부를 때마다 새 함수를 만든다** — `counter.inc.bind(counter) === counter.inc.bind(counter)` 가 `false` 다.
  ★★ **그래서 등록·해제를 짝으로 하는 API 에서 해제가 안 된다.**
  `removeEventListener`·`Set.delete`·구독 해제 함수가 전부 **같은 객체**를 요구한다.
  ★ 화살표 래퍼도 같다 — `(() => f()) === (() => f())` 가 `false` 다.
- ★★ **`[3]` 의 `deleted=false`** 는 「**지울 것을 못 찾았다**」는 뜻이다. `left=1` 이라 **등록된 것이 그대로 남아 있다.**
  ★ **에러가 안 난다** — `Set.delete` 는 `false` 를 돌려줄 뿐이고, `removeEventListener` 는 아무것도 안 돌려준다.
  고치는 법은 **만든 함수를 저장해 두고 그 객체로 해제**하는 것뿐이다(`deleted=true left=1`).
- ★★★ **인자를 잃는 고침은 `() => f.call(o)`** 다. 마지막 줄이 `got undefined,undefined` 다.
  ★ `bind` 와 `(...args) => f.apply(o, args)` 는 인자를 그대로 넘긴다(`got 1,2`).
  ★★ 「화살표로 감싸면 된다」가 **인자를 쓰는 콜백에서 조용히 틀리는** 자리가 여기다 —
  이벤트 핸들러의 `event` 인자가 사라지는 사고가 이 모양이다.

### 5. `call` 과 `apply` 중 무엇을 고르나 ★★

**출력** — 1번 `[3]` 의 `f(...[1, 2, 3]) spread` 줄과 `apply(t, { length: 3 })` 줄이 답의 근거다.

**왜 그런가**

- ★★ **인자가 배열에 있으면 오늘날의 정답은 스프레드**다(`f(...arr)`). `apply` 와 결과가 같고 짧으며
  **`this` 를 안 바꿔도 될 때 `null` 을 억지로 넣지 않아도 된다.** 정본은 [11번](../11-spread-and-rest/2-summary.md)이다.
- ★★★ 스프레드로 대신할 수 없는 자리는 「**유사 배열**」이다.
  `apply` 는 `{ 0: 1, 1: 2, length: 2 }` 를 펴지만 **스프레드는 이터러블만 편다** — 유사 배열은 `TypeError` 다.
  ★ 반대로 **`Set` 은 스프레드만 편다.** 두 도구가 **서로 못 덮는 자리를 하나씩 갖는다.**
- ★★ **`apply(t, null)` 은 인자 0개**이고 **`apply(t, 7)` 은 `TypeError`** 다.
  `null`/`undefined` 만 **예외로 허용**되고 그 밖의 비객체는 거부되기 때문이다.
- ★ **`Reflect.apply` 는 값이 같다.** 다른 점은 **`f.apply` 가 `f` 의 `apply` 프로퍼티를 조회한다**는 것 —
  누가 그것을 바꿔 놨으면 다른 함수가 불린다. `Reflect.apply` 는 그 조회를 건너뛴다. 정본은 목록의 **46번 주제**다.

### 6. `bind` 를 두 번 걸면 ★★

**출력** — 2번 `[2]` 의 `bound1.bind(B)(2, 3)` 과 `[6]` 의 네 줄이 답이다.

**왜 그런가**

- ★★ **한 문장** — **`bind` 는 원본을 고치는 것이 아니라 한 겹 감싸는 것**이라,
  두 번 감싸면 **바깥 겹의 `this` 는 안쪽 겹이 삼켜 버린다.** 안쪽이 이미 정해 놨기 때문이다.
- ★★ **두 번째 `bind` 가 무의미하지는 않다** — **인자는 붙는다.**
  `bound1.bind(B, 9)(3)` 이 `args=1,9,3` 이다. `this` 만 무시된다.
- ★ **`length` 는 두 번째 `bind` 에서도 못질한 인자 수만큼 준다.** `[6]` 에서 인자를 안 못질했더니 `3` 그대로였다.

### 7. `new` 와 `bind` 가 만나면 ★★★

**출력** — 2번 `[3]` 의 일곱 줄이 답이다.

**왜 그런가**

- ★★★ **`this` 는 새 객체가 되고 인자는 못질한 것이 앞에 남는다.**
  `new (Ctor.bind({mark:'ignored'}, 1))(2)` 에서 `got` 이 `[1,2]` 다.
  ★ **`new` 는 `this` 만 이긴다** — 인자까지 되돌리지는 않는다.
- ★★★ **`instanceof` 가 둘 다 `true` 인 이유** — bound 함수는 **자기 `prototype` 이 없고**,
  `instanceof` 판정을 **원본에게 넘긴다.** 그래서 `made instanceof BoundCtor` 도 `Ctor.prototype` 을 본다.
  ★ `BoundCtor.prototype` 이 `undefined` 인데도 판정이 되는 것이 그 증거다 —
  ★★ **「프로퍼티가 없다」와 「판정을 못 한다」는 다른 말**이다.
- ★★ **화살표를 `bind` 한 뒤 `new` 하면 `TypeError: ba is not a constructor`** 다.
  ★ [08번 격자](../08-function-forms-and-parameters/2-summary.md)의 **`new?` 칸**이 그대로 따라온다 —
  bound 함수는 **원본이 생성자로 쓰일 자격이 있을 때만** 생성자가 된다.

### 8. 화살표에 세 메서드를 쓰면 ★★

**출력** — 2번 `[4]` 의 여섯 줄이 답이다.

**왜 그런가**

- ★★ **`this` 는 안 바뀐다.** 화살표는 자기 `this` 칸을 안 만들어 **바꿀 자리가 없기** 때문이다.
  ★ **바뀌는 것은 인자와 `length`** 다 — `bind(B, 9)` 는 `9` 를 못질하고 `length` 를 하나 줄인다.
- ★★ **위험한 이유는 에러가 안 나기 때문**이다. `call`·`apply`·`bind` 가 **문법적으로 전부 통하고**
  **아무 경고도 없이** `this` 만 그대로다. 코드를 읽는 사람은 「`this` 를 바꿨다」고 읽는다.
  ★ `length` 가 줄어 **무언가 일어난 것처럼 보이는 것**이 착각을 더한다.
- ★ 정본은 **[07번](../07-this-binding-four-rules/2-summary.md)** 이다. 여기서는 세 메서드 쪽에서 같은 사실을 확인한다.

### 9. 설정에 달린 칸이 몇 개인가 ★★★

**출력** — 1번 `[2]` 의 집계 줄이 답이다 — **`settings-dependent cells 15 of 24`.**

**왜 그런가**

- ★★★ **24칸 중 15칸**이 갈렸다. 갈린 행은 **원시값 셋**(`7`·`"s"`·`true`)과 **빈 값 둘**(`null`·`undefined`)이다.
- ★★★ 공통점은 「**비엄격이 손보는 값인가**」다. 비엄격은 원시값을 **래퍼 객체로 감싸고**
  `null`/`undefined` 를 **전역 객체로 바꾼다.** 엄격은 **아무것도 안 한다** — 건네받은 것을 그대로 `this` 로 쓴다.
  ★ **객체·배열·함수는 손볼 것이 없으니** 두 모드가 같다.
- ★★ **모듈(ESM)에서 돌리면 엄격 쪽 답이 나온다.** 모듈 코드는 **항상 엄격**이기 때문이다.
  ★ 그래서 `f.call(null)` 의 뜻이 **파일을 모듈로 바꾸는 것만으로 달라진다.** 정본은 목록의 **42번 주제**다.

### 10. 보장인가 호스트인가 엔진 사정인가 ★★★

**출력**

```text
===== ./js08b-vdiff.sh 09 (exit=0) =====
  same      js08b-09a-three-methods.js
  same      js08b-09b-bind.js
  same      js08b-09c-limits.js
  same      js08b-09d-fixes.js
  ----
  identical on node18 and node20: 4   different: 0
```

브라우저에 같은 줄을 던진 결과는 이렇다.

```text
===== google-chrome --headless --dump-dom page09.html | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' (exit=0) =====
  engine                              Chrome/151.0.0.0
  sloppy call(null)                   globalThis
  strict call(null)                   null
  sloppy call(7)                      [object Number]
  strict call(7)                      number 7
  globalThis brand                    [object Window]
  bind name                           "bound orig"
  bind length                         2
  bind has prototype?                 false
  rebinding is ignored                args=1,9,3
  new on a bound ctor                 true
  apply with a string                 TypeError
  apply with a Set (no length)        0
  apply with { length: 3 }            3
  reduce ignores thisArg              true
```

**왜 그런가**

- ★★ **두 판이 갈린 자리는 0개**다. 네 스크립트가 **한 글자도 같았다.**
  ★ 08번은 예외 문구 하나가 갈렸는데 여기서는 0개다 —
  ★★ **인자 개수 경계를 자릿수로만 찍은 덕**이다. 정확한 수를 찍었으면 **여기서 갈렸을 것**이다.
  「흔들리는 칸」을 미리 선언해 두면 **제출 전 재대조가 한 줄에 판정된다**는 것이 이 블록이다.
- ★★★ **호스트가 정하는 칸은 하나**다 — **비엄격 `call(null)` 이 주는 전역 객체의 정체**다.
  Node 는 `[object global]`, **브라우저는 `[object Window]`** 다.
  ★ **규칙은 언어가 정한다**(「`null` 이면 전역을 넣는다」). **그 전역이 무엇인지만 호스트가 정한다.**
  ★ 나머지 열네 줄은 Node 와 전부 같다.
- ★★★ **인자 개수의 상한은 「엔진」이다.** 근거 셋 —
  ① **명세에 상한 수치가 없다**(있으면 `length` 처럼 고정값이었을 것이다) ·
  ② **정확한 수가 실행 상태에 따라 흔들린다** ·
  ③ **예외가 `RangeError: Maximum call stack size exceeded`** 로, 「인자가 너무 많다」가 아니라 **스택 이야기**를 한다.
- ★ **부적용인 창은 셋**이다 — `toFixed(20)` · `\uXXXX` 펼치기 · **성능 측정**.
  ★★ 성능은 「안 쟀다」가 아니라 「**이 문서가 안 재기로 한 것**」이다.
  `bind` 가 함수 객체를 하나 더 만든다는 것은 관찰했지만 **얼마나 드는지는 재지 않았고**,
  그래서 이 문서에는 「느리다」·「빠르다」가 한 줄도 없다.

### 11. 경계 — 어디까지가 이 주제인가 ★★

**출력** — 없다. 이 문항은 지도 문항이다.

**왜 그런가**

| 주제 | 정본 |
|---|---|
| `this` 네 규칙 · 우선순위 · 화살표의 렉시컬 `this` | [07 — `this` 바인딩 네 규칙](../07-this-binding-four-rules/2-summary.md) |
| 함수 형태별 `prototype`·`new` 자격 | [08 — 함수 정의 형태와 매개변수](../08-function-forms-and-parameters/2-summary.md) |
| 스프레드 문법 세 자리 | [11 — 스프레드와 나머지](../11-spread-and-rest/2-summary.md) |
| `Reflect` 전체 | 목록의 **46번 주제** |
| `Object.prototype.toString` 을 타입 검사로 쓰기 | 목록의 **34번 주제** |
| 엄격 모드 전체 | 목록의 **35번 주제** |

- ★★★ **07번에서 이어받는 것** — 「명시적 바인딩이 암시적 바인딩을 이기고 `new` 가 그것을 이긴다」는 우선순위를 그대로 받아,
  **그 세 메서드가 실제로 어떤 물건을 만들고 무엇을 못 하는지**를 편다.
- ★★ **08번 격자의 `bound fn` 행**이 이 주제 전체로 펼쳐진 것이다 —
  `prototype` 없음 · `new` 됨 · `name` 에 접두 · `length` 감소, 네 칸이 여기서 각각 한 절이 됐다.
- ★ **이 주제가 끝까지 책임지는 것 셋** —
  ① **세 메서드가 `this` 를 정하는 규칙이 같고 인자 방식만 다르다는 것**
  ② **`bind` 가 만든 함수의 성질 전부**(이름·`length`·`prototype`·`new`·재바인딩 불가·매번 새 객체)
  ③ **`apply` 가 유사 배열을 본다는 것**과 그 조용한 실패.

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js08b-09a-three-methods.js` | ★★★ **값 8종 × 메서드 3종 × 모드 2 격자 15 / 24** · 인자 건네는 15모양 | node20 1벌 + node18 대조 1벌 |
| `js08b-09b-bind.js` | ★★★ **bound 함수의 성질 전부** · 다섯 경로의 재바인딩 실패 · `new` 와 `instanceof` | node20 1벌 + node18 대조 1벌 |
| `js08b-09c-limits.js` | 인자 개수 경계의 **자릿수** · 명세가 정한 `length` · **`thisArg` 를 안 받는 둘** | node20 1벌 + node18 대조 1벌 · 자릿수는 3판 확인 |
| `js08b-09d-fixes.js` | ★★★ **`bind` 가 매번 새 객체** · 해제 실패 · **인자를 잃는 고침** | node20 1벌 + node18 대조 1벌 |
| `js08b-09h-browser.js` | ★★★ **호스트가 정하는 칸 1개**(전역 객체의 브랜드) | Chrome 151 1벌 |
| `js08b-09x-forms.js` | 형태 — `node --check` **진단 0줄**(빈 출력도 블록으로) | node20 1벌 |
| `js08b-vdiff.sh` | 네 스크립트가 **두 판에서 한 글자도 같다**는 것 | 1벌 |
| `js08b-versions.sh` | 이 문서의 모든 출력이 **어느 판에서 나왔나** | 1벌 |

**구현 의존 항목** — 다음은 **이 환경(node 20.19.6 / 18.19.1 · Chrome 151 · x86-64 Linux)에서만** 그렇다.

- ★★★ **인자 개수 경계가 여섯 자리라는 것.** 명세에 상한이 없다. 다른 엔진·다른 스택 설정에서 달라진다.
- ★★ **예외 메시지 문구 전부** — `CreateListFromArrayLike called on non-object` ·
  `Maximum call stack size exceeded` · `ba is not a constructor`. **종류는 명세, 문구는 V8 의 것**이다.
- ★★ **비엄격 `call(null)` 이 주는 전역 객체의 브랜드** — `[object global]`(Node) / `[object Window]`(브라우저). **호스트가 정한다.**
- ★ **`String(bound)` 의 `[native code]` 문구** — 명세는 「구현 정의 문자열」이라고만 한다.

**세 메서드가 `this` 를 정하는 규칙이 같은 것 · 비엄격의 박싱과 전역 치환 · `apply` 가 유사 배열을 보는 것 · `null`/`undefined` 만 예외로 허용되는 것 · bound 함수의 이름·`length`·`prototype`·재바인딩 불가 · `new` 가 `this` 만 이기는 것 · `instanceof` 가 원본 기준인 것 · 화살표에 셋을 걸어도 `this` 가 안 바뀌는 것 · `reduce`·`sort` 가 `thisArg` 를 안 받는 것은 구현 의존이 아니다.**
어느 엔진에서도 같아야 한다.

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — ESM(`.mjs`)에서 같은 격자를 돌리는 것(두 번 컴파일로 대신했다) ·
  다른 엔진(SpiderMonkey·JavaScriptCore) · Node 18 보다 낮은 판 ·
  `Proxy` 로 `apply` 트랩을 건 함수 · `Symbol.hasInstance` 를 덮은 생성자의 bound 판정 ·
  실제 `addEventListener`/`removeEventListener`(`Set` 으로 대신했다 — 같은 「같은 객체여야 한다」 규칙이다).
- ★★ **못 잰 것 — `bind` 와 화살표 래퍼의 비용.** 함수 객체가 하나 더 생긴다는 것은 관찰했지만
  **얼마나 드는지는 재지 않았다.** 그래서 이 문서에는 「느리다」·「빠르다」가 한 줄도 없다.
- ★ **일부러 안 실은 것 — 인자 개수 경계의 정확한 수.** 받아는 봤지만 **흔들리는 칸**이라 자릿수만 실었다.
  ★★ 이것은 「못 잰 것」이 아니라 「**재 봤는데 근거로 안 쓰기로 한 것**」이다.
- ★ **부적용인 창** — `toFixed(20)` · `\uXXXX` 펼치기. 이 주제에는 그 칸이 없다.

**판이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **인자 개수 경계의 자릿수** — 스택 설정이 바뀌면 자릿수도 바뀔 수 있다.
- ★★ **예외 메시지 문구** — 네 블록에 들어 있다. 08번에서 실제로 하나가 바뀌었다.
- ★★ **호스트가 정하는 칸 하나** — 전역 객체의 브랜드.
- **세 메서드의 규칙 자체는 다시 돌릴 필요가 없다** — `bind` 가 들어온 ES5 이후로 바뀐 적이 없다.
