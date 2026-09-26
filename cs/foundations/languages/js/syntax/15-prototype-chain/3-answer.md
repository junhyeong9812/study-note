# js/syntax/15 — 프로토타입 체인: 「읽기는 체인을 타고, 쓰기는 수신자에 내려앉는다」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **node v20.19.6**(기본 판) · **node v18.19.1**(대조) · **Google Chrome 151.0.7922.173** · x86-64 Linux 에서 실제로 돌려 얻은 것이고,
> 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 하나도 없다).
>
> ★★ **예외는 `e.constructor.name` 과 `e.message` 로만 찍었다** — 스택트레이스에는 절대 경로가 박혀 재현이 안 된다.
> ★★★ **이 주제에는 두 판이 갈린 블록이 0개다.** 그래서 양쪽을 나란히 실은 자리가 없다.
> ★★ **표준 출력과 표준 오류를 한 블록에도 안 섞었다** — 이 주제의 블록은 전부 표준 출력이다.
> ★★★ **엄격 블록과 비엄격 블록도 안 섞었다** — `js12b-15c-shadow.js` 와 `js12b-15e-pycontrast.js` 는
> 첫 줄이 `"use strict"` 이고, 나머지 셋은 모드와 무관한 것만 묻는다.
>
> **이 파일이 인용하는 출력을 낸 소스** — 전문은 [1-question.md](1-question.md) 의 같은 번호 문항에 있다.

```text
// js12b-15a-chain.js
// js12b-15b-proxy.js
// js12b-15c-shadow.js
// js12b-15d-misc.js
// js12b-15e-pycontrast.js
// js12b-hb-browser.js
// js12b-versions.sh
// js12b-vdiff.sh
```

> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | Node 스택트레이스의 **절대 경로** — 한 줄도 싣지 않았다 | ★★★ **트랩 로그의 개수와 순서** |
> | 예외 **문구**(판이 오르면 바뀐다) | ★★★ **예외의 종류** · **own 키 목록** |
> | 브라우저 UA 문자열의 뒷자리 | ★★★ **체인을 글자로 찍은 줄** · 격자의 `true`/`false` |
> | `console.log(bare)` 의 표기 형식(Node 의 `util.inspect`) | ★★ **브랜드 태그** `[object Object]` |
>
> ★ **이 주제의 블록에는 주소도 시간도 난수도 안 찍힌다.** 같은 판에서 다시 돌리면 한 글자도 안 변한다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 체인을 `null` 까지 찍으면 — **한 줄짜리 반복문으로 끝까지 찍히는 유한한 사슬이다** ★★

**출력**

```text
===== node20 js12b-15a-chain.js (exit=0) =====
[1] chains, each printed to null
{}                                  Object.prototype -> null
[]                                  Array.prototype -> Object.prototype -> null
function f() {}                     Function.prototype -> Object.prototype -> null
() => {}                            Function.prototype -> Object.prototype -> null
function* g() {}                    GeneratorFunction.prototype -> Function.prototype -> Object.prototype -> null
async function h() {}               AsyncFunction.prototype -> Function.prototype -> Object.prototype -> null
new A   (class A)                   A.prototype -> Object.prototype -> null
new B   (class B extends A)         B.prototype -> A.prototype -> Object.prototype -> null
new Ctor  (function Ctor)           Ctor.prototype -> Object.prototype -> null
new Map()                           Map.prototype -> Object.prototype -> null
new Error('x')                      Error.prototype -> Object.prototype -> null
new TypeError('x')                  TypeError.prototype -> Error.prototype -> Object.prototype -> null
/re/                                RegExp.prototype -> Object.prototype -> null
1  (number primitive)               Number.prototype -> Object.prototype -> null
's'  (string primitive)             String.prototype -> Object.prototype -> null
Symbol('s')                         Symbol.prototype -> Object.prototype -> null
Object.create(null)                 null
Object.create(Object.create(null))  (anonymous [object Object]) -> null
Object.create({ a: 1 })             (anonymous [object Object]) -> Object.prototype -> null

[2] the constructors themselves are objects too -- their chain is different
A  (the class object)               Function.prototype -> Object.prototype -> null
B  (extends A)                      A (the class object) -> Function.prototype -> Object.prototype -> null
Ctor  (function)                    Function.prototype -> Object.prototype -> null
Object                              Function.prototype -> Object.prototype -> null
Function                            Function.prototype -> Object.prototype -> null

[3] prototype  vs  [[Prototype]] -- two different slots with confusable names
Ctor.prototype                       [object Object]   own keys ["constructor"]
Object.getPrototypeOf(Ctor)          Function.prototype
Ctor.prototype === getPrototypeOf(Ctor)?  false
getPrototypeOf(new Ctor) === Ctor.prototype?  true
does an instance have .prototype?    false
does an arrow function have one?     false
does a class method have one?        false
does class A have one?               true
```

**왜 그런가**

- ★★ **칸이 한 개인 줄** — `{}`(`Object.prototype`)와 `Object.create(Object.create(null))`(이름 없는 칸) **둘**이다.
  ★ **칸이 0개인 줄** — `Object.create(null)` 하나뿐이다.
  **두 개인 줄** — `[]`·`function f`·`() => {}`·`new A`·`new Ctor`·`new Map()`·`new Error('x')`·`/re/`·
  `1`·`'s'`·`Symbol('s')`·`Object.create({ a: 1 })`.
  **세 개 이상** — `function* g`·`async function h`·`new B`·`new TypeError('x')`.
  ★ **19줄 중 17줄이 `Object.prototype` 에서 끝난다** — 안 그런 둘은 `Object.create(null)`(칸이 없다)과
  `Object.create(Object.create(null))`(이름 없는 칸 하나 뒤 바로 `null`)이다.
- ★★★ **`Object.create(null)` 줄에는 `null` 한 글자만 찍힌다.** 칸이 **하나도 없다.**
- ★★★ **`Object.create(Object.create(null))` 의 단 하나뿐인 칸이 `(anonymous [object Object])` 다.**
  스크립트는 **그 칸이 스스로 들고 있는 `constructor`** 로 이름을 짓는데,
  그 칸(바탕이 `null` 인 객체)은 `constructor` 가 **아예 없다.**
  ★★ **상속된 `constructor` 를 읽었다면 어땠을까** — `Object.create({ a: 1 })` 줄이 그 답이다.
  거기 **첫 칸**(`{ a: 1 }`)은 `constructor` 를 **빌려 볼 수는 있는데** own 이 아니라 역시 이름을 못 짓는다.
  ★★★ **상속된 것을 읽으면 웬만한 객체가 전부 `Object` 로 나와** 이름이 쓸모없어진다. 그래서 **own 으로만** 지었다.
  이름이 없을 때 쓴 `[object Object]` 가 **③ 브랜드 태그**다.
- ★★ **`function* g` 는 칸이 하나 더 있다** — `GeneratorFunction.prototype -> Function.prototype -> Object.prototype -> null`.
  `() => {}` 는 **`Function.prototype` 부터**라 한 칸 짧다. `async function h` 도 제너레이터와 같은 모양이다.
- ★★ **원시값 `1` 에 체인이 찍히는 것은 「원시값이 객체다」라는 뜻이 아니다.**
  스크립트가 `Object.getPrototypeOf(Object(x))` 로 **감싸서** 찍은 것이고,
  ★★★ **점 접근도 정확히 같은 일을 한다**(01번의 임시 래핑). 그래서 `(1).toFixed` 가 어디서 오는지가 이 줄 하나로 끝난다.
- ★★★ `[2]` **`B` 의 윗집은 `A` 라는 클래스 객체**다(`A (the class object) -> Function.prototype -> ...`).
  ★★★ **이것이 정적 멤버가 상속되는 이유**다. `class B extends A` 는 사슬을 **두 줄** 만든다 —
  `B.prototype -> A.prototype`(인스턴스 메서드용)과 `B -> A`(정적 멤버용).
  ★ `extends` 가 그 밖에 무엇을 하는지는 16·17번이 정본이다.
- ★★★ `[3]` **`Ctor.prototype === getPrototypeOf(Ctor)` 는 `false`** 다.
  두 이름이 비슷할 뿐 **다른 슬롯**이다 — 하나는 「내가 만들 인스턴스에게 줄 윗집」,
  하나는 「지금 나 자신의 윗집」(`Function.prototype`)이다.
  ★★ 바로 아랫줄의 `getPrototypeOf(new Ctor) === Ctor.prototype` 이 **`true`** 인 것이 그 짝이다 —
  **`new` 가 하는 일이 정확히 그 연결**이다.
- ★ `[3]` 의 마지막 네 줄 중 **`true` 는 하나**다(`does class A have one?`).
  **인스턴스도 화살표 함수도 메서드 단축도 `.prototype` 이 없다.**
  ★ `.prototype` 이 없는 함수는 **`new` 로 못 부른다** — 13번의 실측이 여기서 다시 쓰인다.

### 2. 조회가 어디서 멈추나 — **로그의 길이가 곧 걸어간 칸 수다** ★★★

**출력**

```text
===== node20 js12b-15b-proxy.js (exit=0) =====
[1] reading -- the lookup walks down until it finds the key
C.fromC             -> c            trap log ["C.get(fromC)"]
C.fromB             -> b            trap log ["C.get(fromB)","B.get(fromB)"]
C.fromA             -> a            trap log ["C.get(fromA)","B.get(fromA)","A.get(fromA)"]
C.nope              -> undefined    trap log ["C.get(nope)","B.get(nope)","A.get(nope)"]
C.toString          -> function     trap log ["C.get(toString)","B.get(toString)","A.get(toString)"]

[2] 'in' and hasOwnProperty walk differently
'fromA' in C        -> true         trap log ["C.has(fromA)","B.has(fromA)","A.has(fromA)"]
hasOwn(C,'fromA')   -> false        trap log ["C.gopd(fromA)"]
hasOwn(C,'fromC')   -> true         trap log ["C.gopd(fromC)"]

[3] writing -- the write does NOT walk to where the value lives
C.fromA = 'W'       -> done         trap log ["C.set(fromA)","B.set(fromA)","A.set(fromA)","C.gopd(fromA)"]
after the write:
C.fromA  (read)     -> W            trap log ["C.get(fromA)"]
A still holds       -> a
own keys of C's target -> ["fromC","fromA"]

[4] a setter on the chain -- now the write DOES walk
leaf.s = 'written'   log ["setter ran, this is the LEAF object"]
own keys of leaf     ["_v"]
base._v              base   leaf._v written   leaf.s written
```

**왜 그런가**

- ★★★ `[1]` **로그는 `1 · 2 · 3 · 3 · 3` 줄**이다.
  `C.fromC` 는 첫 칸에서 찾아 **`B` 와 `A` 를 아예 안 건드리고**,
  `C.fromB` 는 두 칸, `C.fromA`·`C.nope`·`C.toString` 은 세 칸을 걷는다.
  ★★★ **값만 보면 이것을 원리상 못 가른다** — `'a'` 는 어느 칸에서 왔든 `'a'` 다.
- ★★★ **`C.nope` 의 결과는 `undefined` 라는 값**이다. **예외가 아니다.**
  세 칸을 전부 뒤지고도 못 찾아 돌아온 것이고, **「없다」도 답**이다.
  ★ 12번의 `?.` 가 필요한 이유가 여기 있다 — 터지는 것은 **그 다음 점**이지 이 조회가 아니다.
- ★★★ **`C.nope` 와 `C.toString` 의 로그가 똑같이 3줄인데 답이 다르다.**
  그 사실이 말하는 것은 **로그가 「체인의 길이」가 아니라 「계측한 칸의 수」라는 것**이다.
  `A` 의 타깃은 평범한 객체라 **그 위에 `Object.prototype` 이 더 있고**, `toString` 은 거기서 왔다.
  ★★ **침묵은 「안 갔다」가 아니라 「거기엔 탐침이 없다」는 뜻**이다 — 18-A 의 규칙이 그대로 걸리는 자리다.
- ★★ `[2]` **`'fromA' in C` 는 `has` 트랩 3줄을 남기고 `true`**,
  **`Object.hasOwn(C, 'fromA')` 는 `gopd` 트랩 1줄만 남기고 `false`** 다.
  ★★★ **같은 프로퍼티에 대해 하나는 `true`, 하나는 `false`** 다. 둘은 경쟁이 아니라 **다른 질문**이다 —
  `in` 은 「쓸 수 있나」, `hasOwn` 은 「이 객체의 것인가」를 묻는다.
  ★ `Object.hasOwn(C, 'fromC')` 도 `gopd` **1줄**로 끝난다 — own 검사는 **언제나 첫 칸뿐**이다.
- ★★★ `[3]` **트랩 로그는 `["C.set(fromA)","B.set(fromA)","A.set(fromA)","C.gopd(fromA)"]`** 다.
  앞의 세 줄은 **체인을 걸어 올라간 것**이고 — 윗칸에 **setter 가 있나 · 비쓰기 데이터인가**를 보러 간 것이다 —
  ★★★ **네 번째 줄이 결정적이다.** 아무것도 안 걸리자 **처음 요청을 받은 `C` 로 되돌아가** 거기에 자리를 만들었다.
  **「탐색과 저장이 다른 객체에서 일어났다」의 유일한 발자국**이 그 한 줄이다.
- ★★★ 그 쓰기 뒤 **`A` 는 여전히 `'a'`** 를 들고 있고, **`C` 의 타깃 own 키는 `["fromC","fromA"]`** 로 늘었다.
  **윗칸의 값은 한 글자도 안 바뀌었다.**
- ★★ **쓰기 직후의 읽기는 로그가 1줄**(`["C.get(fromA)"]`)이다.
  이제 첫 칸에서 찾으므로 **더 이상 올라가지 않는다** — 섀도잉이 생겼다는 뜻이다.
- ★★★ `[4]` **setter 안의 `this` 는 `leaf`** 다. 로그가 `"setter ran, this is the LEAF object"` 라고 직접 말한다.
  setter 는 `base` 에 살지만 **점 왼쪽의 객체가 `leaf`** 이므로 **07번의 암시적 바인딩** 그대로다.
  그래서 `this._v = v` 가 **`leaf` 에 own `_v`** 를 만들었고(`own keys of leaf` 가 `["_v"]`),
  **`base._v` 는 `base` 그대로**이며 `s` 자체는 own 이 되지 않았다.

### 3. 같은 이름에 대입하면 — **읽기는 빌려 보고 쓰기는 자기 서랍에 새로 만든다** ★★★

**출력**

```text
===== node20 js12b-15c-shadow.js (exit=0) =====
[1] read walks the chain; write lands on the receiver
a.v  (before)                         from proto   ownProperty? false
a.v = 'own on a'  -> a.v              own on a   ownProperty? true
proto.v                               from proto
b.v  (the sibling)                    from proto   ownProperty? false
delete a.v  -> a.v                    from proto   ownProperty? false

[2] the trap: a shared MUTABLE value on the prototype
x.list.push(...)  -> y.list           ["pushed through x"]
x.count += 1      -> x.count          1   own? true
                  -> y.count          0   own? false
                  -> shared.count     0

[3] when the prototype's property is NOT writable, the write is blocked (strict: TypeError)
kid.v = 'try'                         TypeError Cannot assign to read only property 'v' of object '#<Object>'
own? after the failed write           false
defineProperty on kid instead         kid.v = defined   own? true   ro.v = read only

[4] a setter on the prototype takes the write -- and `this` is the receiver
child.s = 'child wrote'               child.s = child wrote
own keys of child                     ["_store"]
withSetter._store                     proto store
did 's' become an own property?       false

[5] getter-only on the prototype -- strict throws, and nothing is shadowed
c2.s = 'nope'                         TypeError Cannot set property s of #<Object> which has only a getter
own keys of c2                        []

[6] four ways to ask 'does it have v?' on a shadowing object
'v' in o2                             true
Object.hasOwn(o2, 'v')                false
o2.hasOwnProperty('v')                false
Object.keys(o2)                       []
after o2.v = 2 : Object.hasOwn        true
after o2.v = 2 : Object.keys          ["v"]
after o2.v = 2 : p2.v                 1
```

**왜 그런가**

- ★★★ `[1]` 다섯 줄을 짝지으면 이렇다 —
  `a.v` 처음 **`from proto` / own `false`** → 대입 뒤 **`own on a` / own `true`** →
  `proto.v` **`from proto`**(안 바뀜) → `b.v` **`from proto` / own `false`**(형제도 안 바뀜) →
  `delete a.v` 뒤 **`from proto` / own `false`**.
  ★★★ **윗집도 형제도 한 글자도 안 바뀌었다.**
- ★★★ **`delete` 뒤에 원래 값이 다시 나오는 것**이 「**가렸다**」의 증거다.
  덮었다면 지워도 안 돌아왔을 것이다. **섀도잉은 덮기가 아니라 가리기**다.
- ★★★ `[2]` **`x.list.push(...)` 뒤 `y.list` 는 `["pushed through x"]`** 이고,
  **`x.count += 1` 뒤 `y.count` 는 `0`(own `false`)·`shared.count` 도 `0`** 이다.
  ★★★ 두 줄이 다른 이유는 **한쪽은 고치기이고 한쪽은 대입**이기 때문이다.
  `push` 는 **대입이 아니라** 윗집에서 찾아 온 그 배열 **한 개**를 고친 것이라 own 이 안 생기고 형제에게 보인다.
  `+=` 는 **읽기 + 대입**이라 읽기는 윗집에서 `0` 을 가져오고 **쓰기는 `x` 에 own 을 만든다.**
  ★★ **증상과 진단이 어긋나는 자리다** — 값은 자기 것처럼 보이는데 `own?` 은 `false` 다.
  ★ 파이썬 29번의 「가변 클래스 변수」와 **같은 집안이고 처방도 같다** — 가변 상태는 인스턴스마다 만든다.
- ★★ `[3]` **`kid.v = 'try'` 는 `TypeError`**(`Cannot assign to read only property 'v' of object '#<Object>'`)이고,
  그 뒤 **`own?` 은 `false`** 다 — **막혔을 뿐 아니라 아무것도 안 만들어졌다.**
- ★★★ **`defineProperty` 는 통과한다.** 다음 줄에서 `kid.v` 가 `defined`, own 이 `true`,
  **`ro.v` 는 여전히 `read only`** 다.
  ★★★ **대입(`=`)과 정의(`defineProperty`)는 다른 문**이기 때문이다 —
  대입은 「값을 바꾸겠다」는 뜻이라 **윗집의 금지를 존중**하고,
  정의는 「이 객체에 이 모양의 칸을 만들겠다」는 뜻이라 **윗집과 무관**하다. 정본은 14번이다.
- ★★★ `[4]` **`child` 의 own 키는 `["_store"]`** 이고 **`s` 는 own 이 아니다**(`false`).
  **`withSetter._store` 는 `proto store` 그대로**다.
  ★★★ setter 안의 `this` 가 `withSetter` 가 아니라 **`child`** 였다는 증거가 이 세 줄이다.
- ★★ `[5]` **`c2` 의 own 키는 빈 배열 `[]`** 이다.
  `TypeError`(`Cannot set property s of #<Object> which has only a getter`)가 나고 **아무것도 섀도잉되지 않았다.**
  ★ setter 가 없으니 가져갈 사람도 없고, 그렇다고 own 을 만들지도 않는다.
  ★★ 이것을 뚫는 유일한 길이 `[3]` 과 같은 `defineProperty` 다.
- ★ `[6]` 섀도잉 **전** — `'v' in o2` 만 `true` 이고 `Object.hasOwn`·`o2.hasOwnProperty`·`Object.keys` 는 `false`/`false`/`[]`.
  **후** — `hasOwn` 이 `true`, `keys` 가 `["v"]`, 그리고 **`p2.v` 는 `1` 그대로**다.
  ★ 13번의 「일곱 가지 뷰」 격자를 **체인 위에서** 좁혀 본 것이 이 여섯 줄이다.

### 4. 계단이 없는 객체 — **메서드는 못 부르고 정적 함수는 된다** ★★★

**출력**

```text
===== node20 js12b-15d-misc.js (exit=0) =====
[1] Object.create(null) -- an object with no chain at all
typeof bare                             -> object
bare.toString                           -> undefined
bare.hasOwnProperty                     -> undefined
Object.keys(bare)                       -> ["k"]
Object.prototype.toString.call(bare)    -> [object Object]
JSON.stringify(bare)                    -> {"k":1}
String(bare)                            -> TypeError Cannot convert object to primitive value
bare + ''                               -> TypeError Cannot convert object to primitive value
`${bare}`                               -> TypeError Cannot convert object to primitive value
bare == '[object Object]'               -> TypeError Cannot convert object to primitive value
'k' in bare                             -> true
Object.hasOwn(bare, 'k')                -> true
console.log(bare) prints ->
[Object: null prototype] { k: 1 }
util.inspect(bare)       -> [Object: null prototype] { k: 1 }

[2] __proto__ is an accessor that LIVES ON Object.prototype -- so a bare object has none
descriptor on Object.prototype       get=function set=function e=false c=true
own.call(Object.prototype,'__proto__')  true
({}).__proto__ === Object.prototype    true
bare.__proto__ = {...} -> real proto?  still null
                       -> own keys     ["k","__proto__"]
                       -> bare.marker  undefined
setPrototypeOf on a normal object      M
Object.setPrototypeOf({}, 5)            -> TypeError Object prototype may only be an Object or null: 5
Object.getPrototypeOf(null)             -> TypeError Cannot convert undefined or null to object
Object.getPrototypeOf(5)                -> [object Number]

[3] what `new` links -- and what happens if you rewire .prototype afterwards
getPrototypeOf(i1) === Ctor.prototype   true
i1.constructor === Ctor                 true
own.call(i1, 'constructor')             false
hand-rolled new: same shape?            true
after reassigning Ctor.prototype:
  i1.hello()                            hi
  i2.hello                              undefined
  i2.note                               brand new prototype object
  i1 instanceof Ctor                    false
  i2 instanceof Ctor                    true
  i2.constructor.name                   Object

[4] instanceof walks the chain -- and Symbol.hasInstance can replace the walk
q instanceof Q / P / Object             true / true / true
same answer by hand (walk to null)      Q -> P -> Object
bare instanceof Object                  false
new Never() instanceof Never            false
'a string' instanceof Always            true
({}) instanceof {}                      -> TypeError Right-hand side of 'instanceof' is not callable
({}) instanceof (() => {})              -> TypeError Function has non-object prototype 'undefined' in instanceof check
Object.prototype.isPrototypeOf(q)       true
P.prototype.isPrototypeOf(q)            true
```

**왜 그런가**

- ★★★ `[1]` **`TypeError` 가 나는 줄은 네 줄**이다 —
  `String(bare)` · `bare + ''` · `` `${bare}` `` · **`bare == '[object Object]'`**.
  문구는 넷 다 `Cannot convert object to primitive value` 로 같다.
  ★ 그 앞의 `bare.toString` 과 `bare.hasOwnProperty` 는 터지지 않고 **`undefined`** 를 답한다 — **읽기는 되기 때문**이다.
- ★★★ **`==` 까지 터지는 이유는 느슨한 비교도 원시값 변환을 시도하기 때문**이다(02번).
  객체와 문자열을 비교하려면 객체를 원시값으로 바꿔야 하는데, **`toString` 도 `valueOf` 도 없어 방법이 아예 없다.**
  ★★ 이 줄이 특히 무서운 이유는 **`==` 가 「비교」로만 보여서** 변환이 일어나는 줄로 안 읽히기 때문이다.
- ★★★ **`Object.prototype.toString.call(bare)` 는 `[object Object]` 라고 답한다.**
  객체 자신에게 물을 수 없을 뿐, **그 함수를 빌려다 부르면** 되기 때문이다.
  ★★★ **이것이 「창을 바꿔 물었다」(제5의 상태)의 실물**이다 — 평소 창이 전부 닫혔고 다른 창으로 같은 질문에 답을 얻었다.
  ★ 그 창이 못 보는 것도 있다 — 브랜드 태그는 **「무슨 종류인가」만** 말하고 **내용은 안 말한다.**
- ★★ **되는 것들의 공통점 한 문장** — 넷 다 **「객체에게 메서드를 부르는」 것이 아니라 「객체를 인자로 받는」 것**이다.
  `Object.keys(bare)` 는 `["k"]`, `JSON.stringify(bare)` 는 `{"k":1}`, `'k' in bare` 는 `true`,
  `Object.hasOwn(bare, 'k')` 는 `true` 다.
  ★★★ **`bare` 에 대해 정적 함수는 되고 메서드 호출은 안 된다** — 이 한 문장이 `Object.create(null)` 을 다루는 규칙이다.
  ★ `console.log(bare)` 와 `util.inspect(bare)` 는 `[Object: null prototype] { k: 1 }` 로 찍는데,
  **이 접두는 Node 가 정한 표기**다(ECMA-262 밖). 그래도 **로그에서 체인이 없다는 것을 알아채는 신호**라 값이 크다.
- ★★★ `[2]` `bare.__proto__ = { marker: "M" }` 뒤의 세 줄은 —
  **실제 프로토타입 `still null`** · **own 키 `["k","__proto__"]`** · **`bare.marker` 가 `undefined`** 다.
  ★★★ **평범한 own 데이터 프로퍼티가 하나 생겼을 뿐 프로토타입은 그대로 `null`** 이다. **에러도 경고도 없다.**
- ★★★ **평범한 객체와 다른 이유는 `__proto__` 가 사는 곳 때문**이다.
  `__proto__` 는 **`Object.prototype` 에 놓인 접근자 프로퍼티 한 개**다
  (실측: `get=function set=function e=false c=true`, 그리고 `own.call(Object.prototype,'__proto__')` 가 `true`).
  평범한 객체는 **체인을 올라가 그 setter 를 빌려 쓰는데**, `bare` 는 **빌려 올 곳이 없어** 그냥 대입이 된다.
  ★★★ **같은 문장이 한쪽에서는 프로토타입을 바꾸고 한쪽에서는 키를 만든다** — 이것이 이 절의 급소다.
  ★ 그래서 읽기는 **`Object.getPrototypeOf`**, 쓰기는 **`Object.setPrototypeOf`** 를 쓴다
  (같은 블록에서 `setPrototypeOf` 는 평범한 객체에서 `M` 을 제대로 냈고,
  인자가 객체도 `null` 도 아니면 `TypeError` 다).
- ★★ `[3]` **`i1 instanceof Ctor` 가 `false`** 가 된다. 그런데 **`i1.hello()` 는 여전히 `hi`** 를 답한다.
  ★★★ **`i1` 은 아무것도 안 변했다** — 그 윗집은 여전히 예전 프로토타입 객체이고 `hello` 도 거기 그대로 있다.
  바뀐 것은 **`Ctor.prototype` 이 가리키는 곳**뿐이다.
  ★★★ 그래서 **`instanceof` 는 「이 생성자로 만들었나」가 아니라 「함수의 지금 `.prototype` 이 체인 위에 있나」를 묻는다**.
- ★★ **`i2.constructor.name` 이 `Object`** 인 이유는 **새 프로토타입 객체에 `constructor` 를 안 달았기** 때문이다.
  그 이름은 `Object.prototype` 에서 **빌려 온 것**이다.
  ★★★ **`constructor` 는 자동으로 유지되는 것이 아니라 프로토타입 객체의 평범한 프로퍼티 하나**다.
  ★ 이것이 「`Child.prototype = Object.create(Parent.prototype)` 뒤에 `constructor` 를 다시 달아라」는
  낡은 관용구의 이유이고, **`class` 가 그 손질을 없앤 이유**다(16번).
- ★★ `[4]` **`bare instanceof Object` 는 `false`** 다. `bare` 는 객체인데도 그렇다 —
  체인이 없어 **`Object.prototype` 을 만날 수가 없기** 때문이다.
  ★ 그래서 **`instanceof Object` 를 「객체인가」의 검사로 쓰면 안 된다**(정본은 34번).
  ★★ `Symbol.hasInstance` 를 달면 답이 통째로 바뀐다 —
  `new Never() instanceof Never` 가 **`false`**(자기가 만든 것인데도),
  `'a string' instanceof Always` 가 **`true`**(원시값인데도)다.
- ★ **두 `TypeError` 의 차이** —
  `({}) instanceof {}` 는 **`Right-hand side of 'instanceof' is not callable`**(애초에 호출 가능하지 않다),
  `({}) instanceof (() => {})` 는 **`Function has non-object prototype 'undefined' in instanceof check`**
  (호출은 가능한데 **`.prototype` 이 없다**).
  ★★ `[3]` 에서 「화살표 함수에는 `.prototype` 이 없다」를 확인한 것이 **여기서 에러 문구로 되돌아온다.**
  ★ 그리고 `isPrototypeOf` 두 줄이 **방향만 반대인 같은 질문**임을 보인다(`Object.prototype.isPrototypeOf(q)`·
  `P.prototype.isPrototypeOf(q)` 가 둘 다 `true`).

### 5. 파이썬과 같은 질문 — **읽기에서 own 이 무조건 이긴다(파이썬과 반대)** ★★★

**출력**

```text
===== node20 js12b-15e-pycontrast.js (exit=0) =====
[1] read -- does an own property beat an accessor on the prototype?
kid.v  (no own property yet)                      ACCESSOR on prototype
after defineProperty(kid, 'v')  -> kid.v          OWN data property
  own? / accessor still on proto?                 true / function
  accProto.v itself                               ACCESSOR on prototype

[2] write -- the accessor on the prototype takes it, so NO own property appears
kid2.v = 'written through'                        kid2.v = ACCESSOR on prototype
  own keys of kid2                                ["_viaSetter"]
  where did the value land?                       kid2._viaSetter = written through · accProto._viaSetter = undefined

[3] the same three cells for a PLAIN data property on the prototype
kid3.v  (before)                                  DATA on prototype   own? false
kid3.v = 'written through'                        written through   own? true
  dataProto.v                                     DATA on prototype

[4] the chain is made of OBJECTS, not classes -- two instances of one class
c1.shared / c2.shared                             on C.prototype / on C.prototype
getPrototypeOf(c1) === getPrototypeOf(c2)         true
getPrototypeOf(c1) === C.prototype                true
getPrototypeOf(c1) === C                          false
after c1.shared = 'own on c1' : c2.shared         on C.prototype
setPrototypeOf(c1, {...}) : c1 instanceof C       false
  c1.shared (own still wins)                      own on c1   own? true
  after delete c1.shared                          a different object entirely

[5] what JS does NOT have -- a per-property hook that beats an own property on READ
proto has get+set, leaf has own data -> leaf.v    own
is there any flag that flips this?                no -- ordinary [[Get]] returns at the first own hit
Proxy CAN do it, but that is a different object   PROXY wins
```

**왜 그런가**

- ★★★ `[1]` **`defineProperty` 로 own 을 만든 뒤 `kid.v` 는 `OWN data property`** 다.
  그리고 **프로토타입의 접근자는 살아 있다** — `getOwnPropertyDescriptor(accProto,'v').get` 이 여전히 `function` 이고
  `accProto.v` 자체는 `ACCESSOR on prototype` 을 답한다. **가린 것이지 없앤 것이 아니다.**
  ★★★ **파이썬은 여기서 정반대다.**
  Python 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **29번**이
  「데이터 디스크립터 > 인스턴스 칸」을 그 편의 동작 7에서 실측으로 못 박아 두었다 —
  거기서는 인스턴스 칸에 값이 **버젓이 있는데도** 클래스 쪽이 답한다.
- ★★★ `[2]` **own 키는 `["_viaSetter"]`** 이고, **`kid2.v` 를 다시 읽으면 `ACCESSOR on prototype`** 이 나온다.
  ★★ 둘을 나란히 놓으면 이상한 것이 보인다 — **쓴 값이 읽기로 안 돌아온다.**
  값은 setter 가 `this._viaSetter` 로 옮겨 놓았고(`this` 가 수신자라 `kid2` 에 들어갔다 —
  `accProto._viaSetter` 는 `undefined`), **getter 는 그 칸을 안 본다.**
  ★★★ **에러도 경고도 없는 조용한 어긋남**이라 실무에서 가장 나쁜 모양이다.
- ★★ `[3]` **대조군인 이유** — 프로토타입 쪽이 **평범한 데이터 프로퍼티**면 쓰기가 own 을 만들고
  (`written through` / own `true`) **`dataProto.v` 는 그대로**다.
  ★★★ `[2]` 와 나란히 놓으면 **갈리는 조건이 「프로토타입의 그 프로퍼티가 접근자인가」 하나뿐**임이 보인다.
- ★★★ `[4]` **`getPrototypeOf(c1)` 은 `C.prototype` 과 같고(`true`) `C` 와는 다르다(`false`).**
  ★★★ **`C` 라는 클래스는 체인 위에 없다** — 체인 위에 있는 것은 `C.prototype` 이라는 **평범한 객체**다.
  그리고 `getPrototypeOf(c1) === getPrototypeOf(c2)` 가 `true` 이므로 **두 인스턴스가 한 객체를 같이 본다.**
  ★ **파이썬은 `type(obj)` 로 클래스로 넘어가지만 JS 는 처음부터 끝까지 객체만 지난다** — 사슬의 재료가 다르다.
- ★★★ **`setPrototypeOf(c1, {...})` 뒤 `c1 instanceof C` 는 `false`** 다.
  그런데 **`c1.shared` 는 여전히 `own on c1`**(own 이 이긴다)이고,
  **`delete c1.shared` 뒤에는 `a different object entirely`** 가 나온다 — **새 윗집의 값**이다.
  ★★ **살아 있는 객체의 사슬을 갈아끼울 수 있다**는 것이 파이썬 MRO 와 가장 다른 성질이다.
- ★★★ `[5]` **JS 에 없는 것은 「읽기에서 own 프로퍼티를 이기는, 같은 객체에 다는 훅」이다**.
  프로토타입에 `get` 과 `set` 을 **둘 다** 달아 두고 자식에 own 데이터를 꽂아도 **`own` 이 답한다.**
  ★★★ **`Proxy` 가 반례가 못 되는 이유** — 그것은 **원래 객체가 아니라 앞에 세운 다른 객체**이기 때문이다.
  파이썬의 데이터 디스크립터는 **그 객체 자신의 조회 규칙**을 바꾸지만,
  `Proxy` 는 **원래 객체를 들고 있는 코드에는 아무 효과가 없다.**
  ★ (스크립트가 찍는 `no -- ordinary [[Get]] returns at the first own hit` 는 **라벨 문자열**이다.
  근거는 그 위의 `leaf.v` 가 `own` 이라는 줄과 `[1]` 의 격자다.)

### 6. `prototype` 과 `[[Prototype]]` 과 `__proto__` — **셋 다 다른 물건이다** ★★★

- ★★★ 한 문장씩 —
  - **`.prototype`** — **함수만** 갖는 **평범한 프로퍼티**. 「내가 만들 인스턴스에게 줄 윗집」을 담아 둔 상자다.
  - **`[[Prototype]]`** — **모든 객체**가 갖는 **내부 슬롯**. 「지금 나의 윗집」이다. `Object.getPrototypeOf` 로 읽는다.
  - **`__proto__`** — **`Object.prototype` 에 사는 접근자 프로퍼티 한 개**(Annex B).
    위의 내부 슬롯을 읽고 쓰는 **편의 창**이고, 그 자체가 슬롯은 아니다.
- ★★★ **체인이 없는 객체에 아예 없는 것은 `__proto__`** 다.
  `Object.prototype` 까지 올라갈 수 없으니 빌려 올 수가 없다.
  ★ `[[Prototype]]` 은 **있다** — 값이 `null` 일 뿐이다. `.prototype` 은 애초에 **함수만의 것**이라 해당이 없다.
- ★★ **인스턴스에는 `.prototype` 이 없다**(`"prototype" in inst` 가 `false`).
  ★★★ **가장 빠른 판별인 이유** — 「`.prototype` 이 보이면 그것은 함수(또는 클래스)다」가 바로 서기 때문이다.
  `obj.prototype` 을 쓰고 싶어졌다면 **거의 항상 `Object.getPrototypeOf(obj)` 를 쓰려던 것**이다.
- ★★ **네 번째 얼굴은 객체 리터럴 안의 `{ __proto__: P }`** 다(13번의 실측).
  그것은 접근자도 데이터도 아니라 **리터럴 문법**이고, **다섯 형태 중 둘에서만** 특별하다
  (`{ ["__proto__"]: P }`·단축·메서드는 평범한 프로퍼티를 만든다).
  ★★★ **같은 이름이 네 가지 뜻으로 쓰인다** — 이 넷을 갈라 두지 않으면 이 자리를 절대 못 푼다.
- ★ 읽기는 **`Object.getPrototypeOf`**, 쓰기는 **`Object.setPrototypeOf`** 다.
  `__proto__` 는 **웹 호환용 유물**이고 **체인이 없는 객체에서 조용히 다른 일을 한다.**

### 7. 쓰기가 체인 쪽에 걸리는 세 경우 — **setter · 비쓰기 데이터 · getter-only** ★★★

- ★★★ 셋을 표로 —

| 체인 위에 있는 것 | 엄격 모드에서 | own 이 생기나 | 값은 어디로 |
|---|---|---|---|
| **setter** | 조용히 성공한다 | ★ **안 생긴다** | setter 가 정하는 곳(대개 **수신자**의 다른 이름) |
| **비쓰기 데이터 프로퍼티** | ★ **`TypeError`** | ★ **안 생긴다** | 아무 데도 안 간다 |
| **getter 만 있는 접근자** | ★ **`TypeError`** | ★ **안 생긴다** | 아무 데도 안 간다 |

- ★★★ **setter 안의 `this` 는 수신자**다 — 점 왼쪽에 있던, 처음 요청을 받은 객체다.
  **07번의 암시적 바인딩** 그대로이고, setter 도 메서드이므로 예외가 아니다.
- ★★★ 그래서 값은 **자식 객체의 다른 이름**에 들어간다 —
  3번 답의 `[4]` 에서 `child` 의 own 키가 `["_store"]` 이고 `withSetter._store` 는 안 바뀌었으며,
  5번 답의 `[2]` 에서 `kid2._viaSetter` 에 들어가고 `accProto._viaSetter` 는 `undefined` 다.
  ★★ **setter 가 사는 객체에는 아무 일도 안 일어난다.**
- ★★ **셋을 전부 통과하는 문은 `Object.defineProperty`** 다.
  **대입은 체인을 보고 정의는 그 객체에 바로 꽂는다** — 다른 문이다.
  3번 답의 `[3]` 이 그 실측이다(`kid.v` 가 `defined` 가 되고 `ro.v` 는 그대로다).
- ★ **비엄격에서는 조용히 무시된다** — 값도 안 바뀌고 own 도 안 생기고 예외도 안 난다.
  ★★★ **그 실측은 이 주제의 블록에 없다.** 이 주제의 두 탐침은 **엄격 고정**이다.
  근거는 [14번](../14-property-descriptors-and-freezing/2-summary.md)의 엄격/비엄격 격자 중
  **`proto has non-writable a`** 줄이고, 거기 `sloppy: OK a=1 own=false` 라고 찍혀 있다.
  ★ **체인 위 getter-only 의 비엄격 결과는 이 배치에서 안 돌려 봤다**(14번이 잰 것은 **own** getter-only 다).

### 8. `new` 와 `instanceof` — **둘 다 「함수의 지금 `.prototype`」을 본다** ★★★

- ★★★ **`new Ctor()` 가 하는 연결** — 「함수의 **현재** `.prototype` 을 새 객체의 `[[Prototype]]` 에 꽂는다」.
  손으로 쓰면 **두 줄**이다 —
  `const o = Object.create(Ctor.prototype);` 과 `Ctor.call(o);`.
  4번 답의 `[3]` 에서 그 둘이 `hand-rolled new: same shape? true` 를 냈다.
  ★ (반환값 규칙 같은 나머지 세부는 07번의 `new` 절이 정본이다.)
- ★★★ **`instanceof` 는 「이 생성자로 만들었나」를 묻지 않는다.**
  「**우변 함수의 현재 `.prototype` 이 좌변의 체인 위에 있나**」를 묻는다.
- ★★★ **증거는 `i1 instanceof Ctor` 가 `false` 로 바뀐 줄**이다.
  `i1` 은 아무것도 안 변했고 `i1.hello()` 도 여전히 돈다 — **바뀐 것은 `Ctor.prototype` 이 가리키는 곳뿐**이다.
  ★★ 보조 증거가 둘 더 있다 — **`bare instanceof Object` 가 `false`**(체인이 없어 못 만난다)와,
  **손으로 체인을 돌린 결과가 `instanceof` 세 줄과 같은 답**(`Q -> P -> Object`)을 낸 것.
- ★★ **`Symbol.hasInstance` 를 달면 체인 순회 자체가 안 일어난다.**
  자기가 만든 것도 `false` 가 되고 원시값도 `true` 가 된다.
  ★★★ 그것이 말하는 것은 **`instanceof` 가 언어가 고정한 사실이 아니라 객체가 대답하는 질문**이라는 것이다.
  실무 검사로 믿을 수 없는 이유가 여기 있다(정본은 34번).
- ★ **`isPrototypeOf` 는 같은 질문을 프로토타입 객체 쪽에서 묻는 것**이다.
  `instanceof` 는 **함수**를 우변에 놓고 그 함수의 `.prototype` 을 꺼내 쓰는데,
  `isPrototypeOf` 는 **프로토타입 객체 자신**을 주어로 놓는다.
  ★ **속일 수 있는 쪽은 `instanceof`** 다 — `Symbol.hasInstance` 가 걸리는 것은 그쪽뿐이다.

### 9. 「쓰기는 체인을 안 탄다」 — **거친 요약이다. 탐색은 걷고 저장만 수신자다** ★★★

- ★★★ **고쳐 쓴 한 문장** — 「**쓰기도 체인을 타지만, 타는 것은 탐색뿐이고 값이 놓이는 자리는 언제나 수신자다.**」
  맞는 부분은 「**값이 윗칸에 안 들어간다**」이고, 틀린 부분은 「**올라가지 않는다**」이다.
- ★★★ **근거는 2번 답 `[3]` 의 로그** `["C.set(fromA)","B.set(fromA)","A.set(fromA)","C.gopd(fromA)"]` 이고,
  **네 번째 줄이 결정적**이다. 앞의 셋은 올라간 발자국이고, 넷째는 **수신자로 되돌아온 발자국**이다.
  ★ 그 뒤의 확인 두 줄이 결론을 닫는다 — **`A` 는 여전히 `'a'`**, **`C` 의 타깃 own 키가 늘었다.**
- ★★★ **거친 요약으로 설명할 수 없는 것은 「세 예외」다**.
  쓰기가 정말로 체인을 안 탄다면 체인 위의 setter 가 왜 불리고,
  체인 위의 비쓰기 프로퍼티가 왜 대입을 막고, 체인 위의 getter-only 가 왜 `TypeError` 를 내는지 말이 안 된다.
  ★★ **올라가서 보고 오기 때문에** 그 셋이 끼어들 수 있는 것이다.
- ★★ **로그 없이는 증명할 수 없다.** 「탐색이 걸었다」는 **값에 아무 흔적을 안 남긴다** —
  걸었든 안 걸었든 `A.fromA` 는 `'a'` 이고 `C.fromA` 는 `'W'` 다.
  ★★★ **이것이 이 주제의 본체가 ① 추상 연산에 로그 심기인 이유**다.
  ★ 유일한 간접 증거가 **세 예외의 존재**인데, 그것은 「무언가 보고 온다」까지만 말하고
  **「어느 순서로 어디까지 갔나」는 못 말한다.**
- ★ **브라우저 탐침의 `15 write does not walk` 줄**이 그 거친 요약을 라벨로 쓰고 있다.
  그대로 둔 이유는 **블록을 손으로 고치지 않기 때문**이다 — 캡처에서 나온 글자를 건드리면 재현이 깨진다.
  ★★ 대신 본문에서 「**라벨은 거친 요약이고 로그가 더 정확하다**」고 밝혀 두었다.

### 10. 보장인가 엔진 사정인가 ★★★

**출력**

```text
===== ./js12b-vdiff.sh (exit=0) =====
js12b-12a-shortcircuit.js    identical
js12b-12b-grid.js            identical
js12b-12c-assign.js          identical
js12b-12s-strict.js          identical
js12b-12x-forms.js           identical
js12b-12y-caret.js           identical
js12b-13a-order.js           identical
js12b-13b-intkeys.js         identical
js12b-13c-computed.js        identical
js12b-13d-views.js           identical
js12b-14a-dump.js            identical
js12b-14b-configurable.js    identical
js12b-14c-freeze.js          DIFFERS
    40c40
    < fa.toSorted()   OK  [1,2,3]
    ---
    > fa.toSorted()   OK  [1,2,3]  returned [1,2,3]
js12b-14s-strict.js          identical
js12b-15a-chain.js           identical
js12b-15b-proxy.js           identical
js12b-15c-shadow.js          identical
js12b-15d-misc.js            identical
js12b-15e-pycontrast.js      identical

identical 18  ·  differs 1  ·  total 19
```

```text
===== google-chrome --headless --dump-dom js12b-page.html | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' | sed 's/&lt;/</g; s/&gt;/>/g; s/&amp;/\&/g' (exit=0) =====
  engine                                Chrome/151.0.0.0
  12  0 ?? 'D' / 0 || 'D'               [0,"D"]
  12  ||= does not write                []
  12  = x || y writes                   ["set"]
  12  a?.b[f()] skips f                 calls 0
  12  a ?? b || c compiles?             SyntaxError: Unexpected token '||'
  12  new a?.b() compiles?              SyntaxError: Invalid optional chain from new expression
  13  enumeration order                 ["1","2","b","a","01","Symbol(s)"]
  13  '4294967295' is an index?         ["a","4294967295","z"]
  13  computed key calls toString       ["K"] ["toString"]
  13  __proto__ literal vs computed     true,false
  14  literal vs defineProperty desc    {"value":1,"writable":true,"enumerable":true,"configurable":true} | {"value":1,"writable":false,"enumerable":false,"configurable":false}
  14  isFrozen {} / prevExt {}          [false,true]
  14  freeze is shallow                 {"d":{"n":2}}
  14  strict write to frozen            TypeError: Cannot assign to read only property 'a' of object '#<Object>'
  15  chain of new TypeError            TypeError -> Error -> Object -> null
  15  String(Object.create(null))       TypeError: Cannot convert object to primitive value
  15  write does not walk               o/p/own:true
  15  non-writable proto blocks         TypeError: Cannot assign to read only property 'v' of object '#<Object>'
  15  Symbol.hasInstance overrides      true
```

**왜 그런가**

- ★★★ **이 주제에서 두 판이 갈린 블록은 0개다.** 위 대조기가 19블록을 두 판에서 돌려
  **갈린 것은 한 블록**뿐이라고 세는데, 그 한 블록은 **14번 주제의 `toSorted`**(ES2024, v18 에 없음)이고
  **15번 주제의 다섯 블록은 전부 `identical`** 이다.
- ★★★ **명세가 정하는 것 셋(더 있지만 대표로)** —
  ① **읽기가 체인을 타고 못 찾으면 `undefined` 인 것**
  ② **쓰기가 체인을 타되 값이 수신자에 놓이고 setter 안의 `this` 가 수신자인 것**
  ③ **`instanceof` 가 함수의 현재 `.prototype` 을 체인에서 찾고, `Symbol.hasInstance` 가 그것을 대신하는 것.**
  **V8 의 문구 셋** — `Cannot assign to read only property 'v' of object '#<Object>'` ·
  `Cannot convert object to primitive value` ·
  `Function has non-object prototype 'undefined' in instanceof check`.
  ★★ **종류(`TypeError`)만 명세가 정한다.**
- ★★ **호스트가 정하는 칸은 0개**다. Chrome 151 의 15번 다섯 줄이 Node 쪽과 전부 같다.
  ★★★ **그런데 이 문서가 호스트의 것이라고 따로 적어 둔 표기가 하나 있다** —
  `console.log(bare)` 와 `util.inspect(bare)` 가 찍는 **`[Object: null prototype]` 접두**다.
  ECMA-262 밖이고 **브라우저 콘솔은 다르게 그린다.** 그래서 「흔들리는 칸」에 넣었다.
- ★★★ **부적용인 창은 진단의 `(행,열)`**(18-C)이다.
  이 주제에는 **`SyntaxError` 가 한 줄도 없다** — 체인은 전부 런타임 의미라 파서가 볼 것이 없다.
  **「재 봤더니 같았다」가 아니라 「잴 것이 없다」는 뜻**이다.
  ★★★ **「창을 바꿔 물었다」(제5의 상태)의 자리는 `Object.create(null)` 이다.**
  「이것이 무슨 물건인가」를 평소에는 `String(x)`·`x.toString()` 으로 묻는데 **그 창이 전부 `TypeError` 로 닫혔고**,
  **③ 브랜드 태그**(`Object.prototype.toString.call`)로 바꿔 물어 `[object Object]` 라는 답을 얻었다.
  ★ 바꾼 창이 못 보는 것도 적어 둔다 — **종류만 말하고 내용은 안 말한다.**
- ★★★ 「`setPrototypeOf` 는 느리다」에 대해 이 문서는 「**안 쟀다**」라고 적는다.
  흔한 말이지만 **여기에 속도 주장이 한 줄도 없다.**
  ★★ 말할 수 있는 것은 **의미**뿐이다 — 살아 있는 객체의 사슬을 갈아끼워 **`instanceof` 의 답까지 바꾼다**
  (5번 답의 `[4]`). **그 놀라움이 안 쓸 이유**이고, 속도는 **별도의 측정이 필요한 다른 주장**이다.

### 11. 파이썬 29번과의 대비 — **같은 집안인데 이기는 방향이 반대다** ★★★

- ★★★ **파이썬은 클래스의 MRO 를 타고 JS 는 객체의 체인을 탄다.**
  파이썬은 `obj` 에서 `type(obj)` 로 **종류가 바뀌며** 클래스 줄로 넘어가는데,
  JS 는 **처음부터 끝까지 전부 그냥 객체**다.
  ★ 증거는 5번 답의 `[4]` — `getPrototypeOf(c1) === C.prototype` 이 `true` 이고 **`=== C` 는 `false`** 다.
  **클래스 `C` 는 체인 위에 없다.**
- ★★★ **읽기에서 이기는 쪽이 반대다.**
  파이썬은 **클래스 칸의 데이터 디스크립터가 인스턴스 칸을 이기고**(29번 동작 7의 ①),
  JS 는 **own 프로퍼티가 체인 위의 접근자를 무조건 이긴다**(5번 답의 `[1]`·`[5]`).
  ★★ 한 문장으로 — **「파이썬은 위가 아래를 이길 수 있고, JS 는 아래가 언제나 이긴다.」**
- ★★★ **쓰기에서는 두 언어가 같다** — **사슬 쪽이 가져간다.**
  파이썬은 `__set__` 이, JS 는 setter 가 가로채고, **둘 다 인스턴스/own 칸이 안 생긴다.**
  ★ 그리고 둘 다 **그 안의 `self`/`this` 가 원래 객체**라 값이 아래쪽에 남는다.
- ★★ 파이썬의 **판별식은 `__set__`(또는 `__delete__`)의 유무** 하나다.
  ★★★ **JS 에는 그에 해당하는 플래그가 없다.** 프로토타입에 `get` 과 `set` 을 둘 다 달아도 읽기는 own 이 이긴다.
  `Proxy` 가 유일한 우회인데 **그것은 다른 객체**라 같은 장치가 아니다.
- ★★ **못 찾았을 때** — 파이썬은 **`AttributeError`**, JS 는 **`undefined`** 다.
  ★ 그래서 JS 에서는 「없다」가 **실패가 아니라 답**이고, `?.`·`??`(12번) 같은 문법이 그 위에 선다.
  파이썬은 그 자리에 `getattr(o, 'x', 기본값)` 과 `__getattr__` 이 있다.
- ★ **런타임에 사슬을 갈아끼울 수 있는 쪽은 JS** 다.
  증거는 `Object.setPrototypeOf(c1, {...})` 뒤 **`c1 instanceof C` 가 `false`** 가 된 줄이다.
  파이썬에서 같은 일을 하려면 클래스 구조를 건드려야 한다.

### 12. 경계 — 어디까지가 이 주제인가 ★★

- **`__proto__:` 리터럴 문법** → [13번](../13-object-literals-and-properties/2-summary.md) ·
  **무엇이 쓰기를 막나** → [14번](../14-property-descriptors-and-freezing/2-summary.md) ·
  **`this` 판정** → [07번](../07-this-binding-four-rules/2-summary.md) ·
  **체인 순회 열거** → 목록의 **18번 주제** ·
  **`class` 가 무엇을 어디에 붙이나** → 목록의 **16번 주제**(그리고 `super` 는 **17번**) ·
  **어느 타입 검사가 깨지나** → 목록의 **34번 주제** ·
  **`Proxy` 트랩 계약** → 목록의 **45번 주제**.
- ★★★ **13번의 `__proto__`** 는 「객체 리터럴 안의 문법」이고
  **이 주제의 `__proto__`** 는 「`Object.prototype` 에 사는 접근자」다.
  ★★ **둘은 다른 물건인데 이름이 같다.** 13번은 「다섯 형태 중 둘만 특별하다」까지,
  여기는 「**체인이 없는 객체에는 그 접근자가 아예 없다**」까지다.
- ★★ **14번의 「비쓰기 프로퍼티」는 그 객체 자신의 것**이고,
  **이 주제의 그것은 체인 위에 있는 것**이다.
  ★ 14번이 「**왜 막히나**」의 정본이고, 여기는 「**남의 집 자물쇠가 내 대입을 막는다**」는 사실과
  **그때 own 이 안 생긴다**는 것까지다.
- ★★ **07번에서 그대로 받아 쓰는 것은 「메서드 호출에서 `this` 는 점 왼쪽의 객체(수신자)다」** 한 줄이다.
  여기서 그것을 다시 증명하지 않는다 — **setter 가 메서드라는 사실만 덧붙인다.**
- ★ **이 주제가 끝까지 책임지는 것 셋** —
  ① **읽기가 체인을 타고 어디서 멈추는지, 그리고 그것을 무엇으로 증명하는지**(트랩 로그)
  ② **쓰기가 수신자에 내려앉는다는 것과 그 규칙이 깨지는 예외 셋**
  ③ **`prototype`·`[[Prototype]]`·`__proto__` 세 이름을 가르는 것**(그리고 `new`·`instanceof` 가 그 중 무엇을 보나).

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js12b-15a-chain.js` | **체인 19종 전수** · 생성자 자신의 체인 5종 · ★★★ `prototype` 대 `[[Prototype]]` · `.prototype` 을 가진 것 4종 | node20 1벌 + node18 대조 1벌 |
| `js12b-15b-proxy.js` | ★★★ **트랩 로그로 본 조회 경로**(1·2·3·3·3줄) · `in` 대 `hasOwn` · **쓰기 로그 네 줄** · setter 의 `this` | node20 1벌 + node18 대조 1벌 |
| `js12b-15c-shadow.js` | ★★★ **읽기/쓰기 비대칭** · 공유 가변값 함정 · 비쓰기·setter·getter-only 세 예외 · 네 가지 뷰 | node20 1벌 + node18 대조 1벌 (**엄격 고정**) |
| `js12b-15d-misc.js` | ★★★ `Object.create(null)` 의 `TypeError` 4줄 + 브랜드 태그 · `__proto__` 가 사는 곳 · `new` 의 연결 · `instanceof` 와 `Symbol.hasInstance` | node20 1벌 + node18 대조 1벌 |
| `js12b-15e-pycontrast.js` | ★★★ **파이썬 29번 대비 전용** — 읽기에서 own 이 이기는 것 · 쓰기를 setter 가 가져가는 것 · 체인이 객체라는 것 · 읽기 훅의 부재 | node20 1벌 + node18 대조 1벌 (**엄격 고정**) |
| `js12b-hb-browser.js` · `js12b-page.html` | ★★★ **호스트가 정하는 칸 0개**(15번 다섯 줄) | Chrome 151 1벌 |
| `js12b-vdiff.sh` | **19블록 중 갈린 것 1개**(그 하나는 14번 주제 — **15번은 0개**) | 1벌 |
| `js12b-versions.sh` | 이 문서의 모든 출력이 **어느 판에서 나왔나** | 1벌 |

**구현 의존 항목** — 다음은 **이 환경(node 20.19.6 / 18.19.1 · Chrome 151 · x86-64 Linux)에서만** 그렇다.

- ★★★ **예외 문구 전부** — `Cannot assign to read only property 'v' of object '#<Object>'` ·
  `Cannot set property s of #<Object> which has only a getter` ·
  `Cannot convert object to primitive value` ·
  `Object prototype may only be an Object or null: 5` ·
  `Cannot convert undefined or null to object` ·
  `Right-hand side of 'instanceof' is not callable` ·
  `Function has non-object prototype 'undefined' in instanceof check`.
  **종류(`TypeError`)만 명세가 정한다.**
- ★★ **`console.log(bare)` · `util.inspect(bare)` 의 `[Object: null prototype]` 접두** — **Node 의 표기**다(호스트).
- ★ **`GeneratorFunction`·`AsyncFunction` 이라는 이름이 `constructor.name` 으로 읽히는 것** — 이 판의 관찰로 적는다.
- ★ **`(anonymous [object Object])` 표기** — **우리 스크립트가 지은 이름**이다. 엔진의 출력이 아니다.
- ★ **브라우저와 Node 20 의 문구가 같은 것** — **같은 계열의 V8 이기 때문**이다.

**읽기가 체인을 타고 못 찾으면 `undefined` 인 것 · 쓰기가 체인을 타되 값이 수신자에 놓이는 것 · setter 안의 `this` 가 수신자인 것 · 비쓰기와 getter-only 가 엄격에서 `TypeError` 인 것 · `defineProperty` 가 그 셋을 통과하는 것 · `Object.create(null)` 의 프로토타입이 `null` 인 것 · `__proto__` 가 `Object.prototype` 의 접근자인 것 · `new` 가 함수의 현재 `.prototype` 을 꽂는 것 · `instanceof` 가 그 현재 값을 체인에서 찾고 `Symbol.hasInstance` 가 그것을 대신하는 것 · `in` 이 체인을 타고 `Object.hasOwn` 이 첫 칸만 보는 것은 구현 의존이 아니다.**
어느 엔진에서도 같아야 한다.

**안 돌려 본 것 / 못 잰 것 / 부적용인 창**

- **안 돌려 본 것** —
  ★★ **체인 위 getter-only 와 setter 의 비엄격 결과.** 이 주제의 두 탐침은 **엄격 고정**이다.
  체인 위 **비쓰기 데이터**의 비엄격 결과만 14번 격자의 `proto has non-writable a` 줄에 있다(`sloppy: OK a=1 own=false`).
  · 다른 엔진(SpiderMonkey·JavaScriptCore)에서의 **문구**
  · **realm 을 건너는 `instanceof`**(`iframe`·`vm` 컨텍스트) — 34번이 다룰 자리다
  · **`Reflect.setPrototypeOf`** 의 반환값(`Object.setPrototypeOf` 만 던졌다)
  · **순환 프로토타입**(`setPrototypeOf(a, b); setPrototypeOf(b, a)`)이 무엇을 내놓나
  · **`Object.preventExtensions` 된 객체의 프로토타입 교체**
  · 파이썬 대비의 나머지 두 축 — **`__getattr__` 상당물의 부재**와 **`__slots__` 상당물의 부재**.
- ★ **못 잰 것** — **없다.** 이 주제에는 「도구가 없어 못 잰」 칸이 없었다.
- ★★★ **안 쟀다** — **성능 전부.** 「`setPrototypeOf` 가 느리다」·「체인이 길면 조회가 느리다」·
  「`Proxy` 를 씌우면 느리다」는 **한 줄도 쓰지 않았다.** 이 문서에 속도 주장이 없다.
- ★★ **부적용인 창** — **진단의 `(행,열)`**(18-C). 이 주제에는 `SyntaxError` 가 한 줄도 없다 —
  **「안 쟀다」가 아니라 「잴 것이 없다」는 뜻**이다.
- ★★★ **창을 바꿔 물은 자리** — `Object.create(null)` 의 「이것이 무슨 물건인가」.
  평소 창(`String`·`.toString()`)이 전부 `TypeError` 로 닫혀 **③ 브랜드 태그**로 바꿔 물었다.

**판이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **예외 문구 전부** — 11번 주제에서 **실제로 한 번 바뀐 전례**가 있다.
- ★★ **`console.log`/`util.inspect` 의 `[Object: null prototype]` 표기** — Node 가 언제든 바꿀 수 있다.
- ★ **`GeneratorFunction`·`AsyncFunction` 의 `constructor.name`** — 내부 객체의 이름이다.
- **체인 조회·쓰기 규칙 자체는 다시 돌릴 필요가 없다** — 초판부터 바뀐 적이 없다.
  ★ 다시 찍어야 할 것은 **새 문법이 체인을 어떻게 만드나**(예: 새 내장 클래스)이지 규칙이 아니다.
