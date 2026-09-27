# js/syntax/22 — `Symbol` 과 잘 알려진 심볼: 「심볼은 이름이 겹칠 수 없는 키이고, 잘 알려진 심볼은 언어가 먼저 들여다보는 키다」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **node v20.19.6**(기본 판) · **node v18.19.1**(대조) · **Google Chrome 151**(한 블록) · x86-64 Linux 에서 실제로 돌려 얻은 것이고,
> 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 하나도 없다).
>
> ★★ **예외는 `이름 「메시지」` 꼴로만 찍었다** — 스택트레이스에는 절대 경로가 박혀 재현이 안 된다.
> ★★★ **이 주제는 두 판이 갈린 블록을 넷 갖고 있다**(`22f`·`22g`·`22h`·`22i`) — 6번·8번·11번 답에 node18 판을 나란히 싣는다.
> ★ **표준 출력과 표준 오류를 한 블록에도 안 섞었다** — 모든 예외를 `catch` 해 표준 출력으로 찍었다.
>
> **이 파일이 인용하는 출력을 낸 소스** — 전문은 [1-question.md](1-question.md) 의 같은 번호 문항에 있다.
> `js20b-22c-toprimitive-hints.js`(1번 · 9번) · `js20b-22b-key-grid.js`(2번) · `js20b-22a-basics.js`(3번 · 7번) · `js20b-22e-tostringtag.js`(4번) ·
> `js20b-22d-hasinstance.js`(5번 · 9번) · `js20b-22f-species.js`(6번) · `js20b-22h-registry.js`(8번) · `js20b-22g-other-hooks.js`(10번 · 11번) · `js20b-22i-wellknown.js`(11번).

## 정답

### 1. hint — **`+`·`==` 는 `default`, 산술·대소는 `number`, 템플릿·키·`String()` 은 `string`, `===`·`!`·`JSON` 은 안 부른다** ★★★

**출력**

```text
===== node20 js20b-22c-toprimitive-hints.js (exit=0) =====
[1] expression               hint(s)                   result
  x + 1                   default                   8
  x + ''                  default                   "7"
  `${x}`                  string                    "S"
  x == 7                  default                   true
  x != 'S'                default                   true
  x === 7                 (no call)                 false
  x < 8                   number                    true
  x * 1                   number                    7
  +x                      number                    7
  -x                      number                    -7
  x ** 1                  number                    7
  x | 0                   number                    7
  String(x)               string                    "S"
  Number(x)               number                    7
  BigInt(x)               number                    7n
  [x].join()              string                    "S"
  ({})[x] = 1 -> key      string                    "S"
  x in {S: 1}             string                    true
  new Date(x).getTime()   default                   7
  isNaN(x)                number                    false
  'aSb'.includes(x)       string                    true
  !x                      (no call)                 false
  x ? 'y' : 'n'           (no call)                 "y"
  JSON.stringify(x)       (no call)                 "{}"

[2] hint tally {"default":5,"number":9,"string":6,"(no call)":4}

[3] what the method returns, or what it is
  returns an object       @@toPrimitive(default)    TypeError 「Cannot convert object to primitive value」
  returns a symbol        @@toPrimitive(default)    TypeError 「Cannot convert a Symbol value to a number」
  is the number 1         (no call)                 TypeError 「number 1 is not a function」
  is null                 valueOf                   2
  is undefined            valueOf                   2
  returns a symbol, `${}` @@toPrimitive(string)     TypeError 「Cannot convert a Symbol value to a string」

[4] Date carries its own Symbol.toPrimitive -- spy on it
  typeof (d + 1)          default                   "string"
  typeof (d - 1)          number                    "number"
  d == d.toString()       default                   true
  d < 1                   number                    true
  own descriptor on Date.prototype: {"value":"fn","writable":false,"enumerable":false,"configurable":true}
```

**왜 그런가**

- ★★★ **`ToPrimitive` 를 부르는 쪽이 원하는 타입을 말하느냐가 hint 를 정한다.** 말하지 않으면 `"default"`, 숫자를 원하면 `"number"`, 문자열을 원하면 `"string"`.
  - **`+` 는 말하지 않는다** — 두 쪽을 원시값으로 만든 **다음에** 문자열이 끼었나를 본다. 그래서 `x + ''` 는 `"default"` 를 받고 메서드가 준 `7` 이 이어 붙어 **`"7"`** 이다.
  - **`==`·`!=` 도 말하지 않는다**(`"default"`). **`<` 는 숫자를 원한다**(`"number"`).
  - **템플릿 리터럴·`String()`·`join`·키 자리·`in`·`includes`** 는 문자열을 원한다(`"string"`).
  - **`new Date(x)`** 는 인자 하나일 때 원하는 타입을 말하지 않는다(`"default"`).
- ★★★ **안 부른 넷** — `===` 는 변환이 없고, `!`·삼항은 `ToBoolean` 이라 **객체는 무조건 참**이며, `JSON.stringify` 는 `toJSON` 을 볼 뿐이다.
  **진릿값을 바꾸는 심볼은 없다**(12번).
- ★★ **`[3]`** — 메서드 자리가 `null`/`undefined` 면 명세의 `GetMethod` 가 「없음」으로 읽어 `valueOf` 로 넘어간다(`2`). `1` 이면 「함수가 아님」이라 `TypeError`.
  **객체를 돌려주면 재시도 없이 `TypeError`**, **심볼을 돌려주면 통과한 뒤** 다음 단계(`+ 1` 의 숫자화, 템플릿의 문자열화)에서 던진다.
- ★★ **`[4]`** — `Date.prototype[Symbol.toPrimitive]` 는 `"default"` 를 **`"string"` 처럼** 다룬다(명세 문장). 그래서 `d + 1` 은 `"string"`, `d - 1` 은 `"number"` 다.
  **hint 는 같은 `"default"` 인데 객체가 해석을 바꾼 것**이다 — 02편의 기본 객체는 `default` 를 `number` 처럼 다뤘다.

### 2. 심볼 키 격자 — **글자 키와 `6 / 10` 열이 갈리고, 스프레드·`assign`·`ownKeys`·`hasOwn` 은 심볼을 본다**

**출력**

```text
===== node20 js20b-22b-key-grid.js (exit=0) =====
[1] who sees what   (o = sees it, . = does not)
                            for-in   keys     entries  JSON     gOPN     gOPS     ownKeys  {...}    assign   hasOwn
string key                  o        o        o        o        o        .        o        o        o        o
symbol key                  .        .        .        .        .        o        o        o        o        o
symbol key, non-enumerable  .        .        .        .        .        o        o        .        .        o
Symbol.for key              .        .        .        .        .        o        o        o        o        o
Symbol.iterator key         .        .        .        .        .        o        o        o        o        o

[2] row 'symbol key' against row 'string key', column by column
  columns that differ ["for-in","keys","entries","JSON","gOPN","gOPS"]
  'Symbol.for key' row equals 'symbol key' row       true
  'Symbol.iterator key' row equals 'symbol key' row  true

[3] Reflect.ownKeys order -- keys added as: sym1, b, 2, sym2, a, 1
  ["1","2","b","a","Symbol(sym1)","Symbol(sym2)"]

differing cells (string key vs symbol key) 6 / 10
```

**왜 그런가**

- ★★★ **`for-in`·`keys`·`entries`·`JSON`·`gOPN` 은 문자열 키만**, **`gOPS` 는 심볼 키만** 늘어놓는다 — 그 여섯 열이 갈린다.
  **`ownKeys`·`{...}`·`assign`·`hasOwn` 은 키 종류를 안 가린다** — 그래서 **심볼 키는 비공개가 아니다.** 스프레드가 복사해 간다.
- ★★ **비열거 심볼**은 스프레드·`assign` 에서도 빠진다. 그 둘의 기준은 「own ∧ 열거 가능」이고(18편), 심볼이냐는 기준에 없다.
- ★★ **`Symbol.for` 심볼·잘 알려진 심볼도 키로서는 보통 심볼과 같다**(두 `true`).
- ★★ **순서** — `["1","2","b","a","Symbol(sym1)","Symbol(sym2)"]`. 13편의 세 덩어리 그대로이고 **심볼은 먼저 넣어도 끝**이다.

### 3. 심볼의 성질 — **`new` 는 `TypeError`, 설명은 없음과 빈 문자열을 가르고, 여섯 변환 중 `String(s)` 만 된다**

**출력**

```text
===== node20 js20b-22a-basics.js (exit=0) =====
[1] making symbols
  typeof Symbol('a')                  "symbol"
  Symbol('a') === Symbol('a')         false
  new Symbol('a')                     TypeError 「Symbol is not a constructor」
  typeof Object(Symbol('a'))          "object"
  Object(s) == s  (same s)            true

[2] description
  Symbol('a').description             "a"
  Symbol('').description              ""
  Symbol().description                undefined
  Symbol(undefined).description       undefined
  Symbol(42).description              "42"
  Symbol({}).description              "[object Object]"

[3] String() · .toString() · Boolean() · a symbol key under Object.keys
  String(s)                           "Symbol(k)"
  s.toString()                        "Symbol(k)"
  Boolean(s) / !!s                    "true / true"
  Object.keys({ [s]: 1 }).length      0

[4] operators · concat · join · Number() · JSON
  s + ''                              TypeError 「Cannot convert a Symbol value to a string」
  `${s}`                              TypeError 「Cannot convert a Symbol value to a string」
  'x'.concat(s)                       TypeError 「Cannot convert a Symbol value to a string」
  [s].join()                          TypeError 「Cannot convert a Symbol value to a string」
  +s                                  TypeError 「Cannot convert a Symbol value to a number」
  Number(s)                           TypeError 「Cannot convert a Symbol value to a number」
  s + 1                               TypeError 「Cannot convert a Symbol value to a number」
  s == 'Symbol(k)'                    false
  s < 1                               TypeError 「Cannot convert a Symbol value to a number」
  JSON.stringify(s)                   undefined
  JSON.stringify({ v: s })            "{}"
  JSON.stringify([s])                 "[null]"

[5] six conversions: String(s):ok  s + '':TypeError  `${s}`:TypeError  [s].join():TypeError  Number(s):TypeError  +s:TypeError
throwing cells 5 / 6
```

**왜 그런가**

- ★★ **`new Symbol` 은 `TypeError 「Symbol is not a constructor」`** — `Symbol` 함수의 첫 단계가 `NewTarget` 이 있으면 던진다. **`Object(Symbol('a'))` 는 래퍼를 만든다**(`"object"`, `==` 로는 원래 심볼과 같다).
- ★★ **`Symbol()`·`Symbol(undefined)` 의 `description` 은 `undefined`, `Symbol('')` 은 `""`** — 인자가 `undefined` 일 때만 「없음」이고 나머지는 `ToString` 을 거친다(`42` → `"42"`, `{}` → `"[object Object]"`).
- ★★★ **`throwing cells 5 / 6`** — 문자열로는 `String(s)` 만, 숫자로는 **하나도** 안 된다. 이유는 7번.
- ★★ **`s == 'Symbol(k)'` 는 던지지 않고 `false`** — 느슨한 같음은 심볼을 문자열로 바꾸지 않는다. **`s < 1` 은 던진다**(숫자화).
- ★★ **`JSON` 은 심볼을 지운다** — 값 자체면 `undefined`, 객체의 값이면 키째 사라져 `"{}"`, 배열의 원소면 `"[null]"`.

### 4. 브랜드 태그 — **일곱 칸 전부(`7 / 7`) 태그와 슬롯이 어긋난다: 위조 넷 · 은폐 셋**

**출력**

```text
===== node20 js20b-22e-tostringtag.js (exit=0) =====
[1] brand tags of built-ins, as they come
  []                        [object Array]
  new Map()                 [object Map]
  new Date(0)               [object Date]
  Promise.resolve()         [object Promise]
  new Error('e')            [object Error]
  function(){}              [object Function]
  null                      [object Null]
  {}                        [object Object]
  Symbol()                  [object Symbol]

[2] a string-valued Symbol.toStringTag, and a slot check on the same value
  value                                 toString tag        slot check
  { tag 'Array' }                       [object Array]      Array slot false
  { tag 'Map' }                         [object Map]        Map slot false
  { tag 'Date' }                        [object Date]       Date slot false
  { tag 'Promise' }                     [object Promise]    Promise slot false
  [] with tag 'Foo'                     [object Foo]        Array slot true
  new Map() with tag 'Foo'              [object Foo]        Map slot true
  new Date(0) with tag 'Foo'            [object Foo]        Date slot true

[3] a tag that is not a string
  { tag 42 }                            [object Object]
  { tag undefined }                     [object Object]

[4] where Map's tag lives -- and after deleting it
  descriptor on Map.prototype  {"value":"Map","writable":false,"enumerable":false,"configurable":true}
  descriptor on Array.prototype "none"
  after delete: tag(new Map()) [object Object]

cells where the toString tag and the slot check disagree 7 / 7
```

**왜 그런가**

- ★★★ **`Object.prototype.toString` 은 슬롯에서 `builtinTag` 를 구한 뒤 `Symbol.toStringTag` 가 문자열이면 그것으로 덮는다.**
  그래서 평범한 객체가 `[object Array]` 를 **자칭**할 수 있고(위조), 진짜 배열이 `[object Foo]` 로 **숨을** 수 있다(은폐).
  ★ **배열은 슬롯 목록(`IsArray`)에 있는데도 덮인다** — 태그는 마지막 단계다.
- ★★ **`Map` 의 `"Map"` 은 `Map.prototype` 의 프로퍼티**라 지우면 `[object Object]` 로 떨어진다. **`Array.prototype` 에는 그 프로퍼티가 없다** — 배열의 `"Array"` 는 슬롯에서 온다.
- ★ **태그가 문자열이 아니면**(`42`·`undefined`) 무시된다.
- ★★ **판별은 슬롯을 두드려라** — `Array.isArray` · `Map.prototype.has.call(v, …)` 이 던지나. [목록의 **34번 주제**](../34-type-checking-idioms/)가 이어받는다.

### 5. `hasInstance` — **대입은 물려받은 `writable: false` 에 막혀 비엄격은 조용히 무시, 엄격은 `TypeError`; `defineProperty` 는 된다**

**출력**

```text
===== node20 js20b-22d-hasinstance.js (exit=0) =====
[1] a logging hasInstance -- what it receives, what instanceof returns
  4 instanceof Even                                 true
  3 instanceof Even                                 false
  typeof (4 instanceof Even)                        boolean
  log                                               ["hasInstance(4)","hasInstance(3)","hasInstance(4)"]

[2] the right-hand side
  ({}) instanceof { [Symbol.hasInstance]: () => true }true
  ({}) instanceof {}                                TypeError 「Right-hand side of 'instanceof' is not callable」
  ({}) instanceof { [Symbol.hasInstance]: 1 }       TypeError 「number 1 is not a function」
  ({}) instanceof 1                                 TypeError 「Right-hand side of 'instanceof' is not an object」

[3] Function.prototype[Symbol.hasInstance] -- its descriptor
  descriptor                                        {"value":"fn","writable":false,"enumerable":false,"configurable":false}

[4] putting a hasInstance on a plain function F
  sloppy  F[Symbol.hasInstance] = () => true        no throw
    then ({}) instanceof F                          false
    then hasOwn(F, Symbol.hasInstance)              false
  strict  F[Symbol.hasInstance] = () => true        TypeError 「Cannot assign to read only property 'Symbol(Symbol.hasInstance)' of function 'function F() {}'」
  defineProperty(F, Symbol.hasInstance, ...)        no throw
    then ({}) instanceof F                          true

[5] the default path for comparison -- Function.prototype[Symbol.hasInstance].call
  Function.prototype[@@hasInstance].call(A, a)      true
  Function.prototype[@@hasInstance].call(A, {})     false
```

**왜 그런가**

- ★★ **`[1]`** — `instanceof` 는 우변의 `hasInstance` 를 **좌변 하나**로 부르고, 돌려받은 `"yes"`/`0` 을 **`ToBoolean`** 한다. 로그는 세 번(세 번 `instanceof` 했다).
- ★★ **`[2]`** — 우변이 **객체가 아니면** `not an object`, `hasInstance` 가 **함수가 아니면** `number 1 is not a function`, 그것도 없고 **부를 수 없으면** `not callable`.
  명세 `InstanceofOperator` 의 세 단계에 문구가 하나씩 대응한다. ★ 우변은 **평범한 객체여도** 된다.
- ★★★ **`[4]`** — `Function.prototype[Symbol.hasInstance]` 가 `writable: false`(`[3]`)라서 **`F` 에 대입해도 own 프로퍼티가 안 생긴다.**
  비엄격은 **아무 말 없이**(`hasOwn` 이 `false`, `instanceof` 는 여전히 `false`), 엄격은 `TypeError 「Cannot assign to read only property ...」`.
  15편의 「체인 위의 읽기 전용 프로퍼티는 대입을 막는다」가 심볼 키에서도 그대로다. **`defineProperty` 는 체인을 안 보므로** 된다.
- ★ **`[5]`** — 기본 경로는 `Function.prototype[Symbol.hasInstance].call(A, v)` 로 직접 부를 수 있고 `instanceof` 와 같은 답이다.

### 6. species — **`7 / 14`: ES2015 계열 일곱은 한 번씩 읽고, ES2023 복사 메서드·`Array.from`·스프레드·`sort` 는 안 읽는다**

**출력**

```text
===== node20 js20b-22f-species.js (exit=0) =====
[1] method          species read?   result constructor
  map               read x1         Array
  filter            read x1         Array
  slice             read x1         Array
  splice            read x1         Array
  concat            read x1         Array
  flat              read x1         Array
  flatMap           read x1         Array
  toSorted          -               Array
  toReversed        -               Array
  with              -               Array
  toSpliced         -               Array
  Array.from(a)     -               Array
  [...a]            -               Array
  sort              -               Tracked
methods that read species 7 / 14

[2] species values other than a constructor
  species = undefined           Array [1,2]
  species = null                Array [1,2]
  species = 42                  TypeError 「object.constructor[Symbol.species] is not a constructor」
  species = function returning {}Object {"0":1,"1":2}

[3] Promise.prototype.then and species
  tp.then(...) constructor Promise   species reads 1
  tp.finally(...) constructor Promise   species reads 2
```

node18 판 — ES2023 복사 메서드 넷이 **없다.**

```text
===== node18 js20b-22f-species.js (exit=0) =====
[1] method          species read?   result constructor
  map               read x1         Array
  filter            read x1         Array
  slice             read x1         Array
  splice            read x1         Array
  concat            read x1         Array
  flat              read x1         Array
  flatMap           read x1         Array
  toSorted          -               TypeError 「a.toSorted is not a function」
  toReversed        -               TypeError 「a.toReversed is not a function」
  with              -               TypeError 「a.with is not a function」
  toSpliced         -               TypeError 「a.toSpliced is not a function」
  Array.from(a)     -               Array
  [...a]            -               Array
  sort              -               Tracked
methods that read species 7 / 14

[2] species values other than a constructor
  species = undefined           Array [1,2]
  species = null                Array [1,2]
  species = 42                  TypeError 「object.constructor[Symbol.species] is not a constructor」
  species = function returning {}Object {"0":1,"1":2}

[3] Promise.prototype.then and species
  tp.then(...) constructor Promise   species reads 1
  tp.finally(...) constructor Promise   species reads 2
```

**왜 그런가**

- ★★★ **`map`·`filter`·`slice`·`splice`·`concat`·`flat`·`flatMap` 은 명세의 `ArraySpeciesCreate` 로 결과를 만든다** — `constructor[Symbol.species]` 를 읽는다.
  **`toSorted`·`toReversed`·`with`·`toSpliced` 는 그것을 안 쓰고 늘 `Array` 를 만든다.** `Array.from(a)` 는 **호출한 쪽**(`Array`)이 생성자이고, 스프레드는 배열 리터럴이다. `sort` 는 새 배열을 안 만든다.
- ★★ **`[2]`** — species 가 `undefined`/`null` 이면 `Array`(`ArraySpeciesCreate` 가 `null` 을 `undefined` 로 바꾼다), `42` 면 생성자가 아니라 `TypeError`,
  **아무 객체나 돌려주는 함수면 결과가 배열이 아니다** — 명세가 "It does not enforce that the constructor function returns an Array." 라고 적는다.
- ★ **`[3]`** — `then` 이 한 번, `finally` 가 두 번(자기가 한 번 · 안에서 부른 `then` 이 한 번).
- ★★ **node18** — `[1]` 의 네 줄이 `TypeError 「a.toSorted is not a function」` 꼴이다. 기능의 **유무**가 판 경계(ES2023)다.

### 7. `String(s)` 만 된다 — **`String` 함수가 심볼을 먼저 걸러 내고, 나머지는 전부 `ToString`/`ToNumber` 를 부르기 때문**

**출력** — 3번의 `[3]`·`[4]`·`[5]` 가 그대로 답이다.

**왜 그런가**

- ★★★ 명세의 함수 `String ( value )` 가 **「`NewTarget` 이 없고 값이 심볼이면 `SymbolDescriptiveString`」** 을 **`ToString` 보다 먼저** 한다. 그 샛길이 **문자열 쪽에만** 있다.
  템플릿 리터럴·`+ ''`·`concat`·`join` 은 추상 연산 **`ToString`** 을 부르고, `ToString` 은 심볼이면 던진다. **`Number()` 는 `ToNumber` 를 곧장 부른다** — 샛길이 없다.
- ★★ 그래서 「명시적 변환은 된다」는 틀리다 — **`Number(s)` 는 명시적인데 던진다.** 갈리는 곳은 「명시적이냐」가 아니라 「**그 함수가 심볼을 따로 챙기느냐**」다.
- ★ 로그에 심볼 키를 끼우려면 **`String(k)`** 이나 **`k.description`** 이다. `` `${k}` `` 는 **로그 자체가 예외를 낸다.**

### 8. `Symbol.for` — **같은 문자열이면 realm 을 넘어 같은 심볼이고, 그래서 약한 키가 못 된다**

**출력**

```text
===== node20 js20b-22h-registry.js (exit=0) =====
[1] same description, three ways
  Symbol.for('app') === Symbol.for('app')             true
  Symbol('app') === Symbol('app')                     false
  Symbol.for('app') === Symbol('app')                 false
  Symbol.for('app').description                       app

[2] Symbol.keyFor
  Symbol.keyFor(Symbol.for('app'))                    app
  Symbol.keyFor(Symbol('app'))                        undefined
  Symbol.keyFor(Symbol.iterator)                      undefined
  Symbol.keyFor('app')                                TypeError 「app is not a symbol」
  Symbol.iterator === Symbol.for('Symbol.iterator')   false

[3] across realms -- a fresh vm context (node:vm)
  other.reg === Symbol.for('app')                     true
  other.it === Symbol.iterator                        true
  other.plain === Symbol('app')                       false

[4] as a WeakMap key / WeakRef target
  new WeakMap().set(Symbol('k'), 1)                   ok
  new WeakRef(Symbol('k'))                            ok
  new WeakMap().set(Symbol.for('k'), 1)               TypeError 「Invalid value used as weak map key」
  new WeakRef(Symbol.for('k'))                        TypeError 「WeakRef: invalid target」
  new WeakMap().set(Symbol.iterator, 1)               ok
  new WeakRef(Symbol.iterator)                        ok

symbol kinds accepted as a WeakMap key 2 / 3
```

node18 판 — `[4]` 만 갈린다(심볼 약한 키가 ES2023).

```text
===== node18 js20b-22h-registry.js (exit=0) =====
[1] same description, three ways
  Symbol.for('app') === Symbol.for('app')             true
  Symbol('app') === Symbol('app')                     false
  Symbol.for('app') === Symbol('app')                 false
  Symbol.for('app').description                       app

[2] Symbol.keyFor
  Symbol.keyFor(Symbol.for('app'))                    app
  Symbol.keyFor(Symbol('app'))                        undefined
  Symbol.keyFor(Symbol.iterator)                      undefined
  Symbol.keyFor('app')                                TypeError 「app is not a symbol」
  Symbol.iterator === Symbol.for('Symbol.iterator')   false

[3] across realms -- a fresh vm context (node:vm)
  other.reg === Symbol.for('app')                     true
  other.it === Symbol.iterator                        true
  other.plain === Symbol('app')                       false

[4] as a WeakMap key / WeakRef target
  new WeakMap().set(Symbol('k'), 1)                   TypeError 「Invalid value used as weak map key」
  new WeakRef(Symbol('k'))                            TypeError 「WeakRef: target must be an object」
  new WeakMap().set(Symbol.for('k'), 1)               TypeError 「Invalid value used as weak map key」
  new WeakRef(Symbol.for('k'))                        TypeError 「WeakRef: target must be an object」
  new WeakMap().set(Symbol.iterator, 1)               TypeError 「Invalid value used as weak map key」
  new WeakRef(Symbol.iterator)                        TypeError 「WeakRef: target must be an object」

symbol kinds accepted as a WeakMap key 0 / 3
```

**왜 그런가**

- ★★ **`true` 는 넷** — `Symbol.for` 끼리 · `vm` realm 의 `Symbol.for('app')` 와 이쪽 것 · `vm` realm 의 `Symbol.iterator` 와 이쪽 것.
  `Symbol()` 끼리, `Symbol.for` 와 `Symbol()`, `Symbol.iterator` 와 `Symbol.for('Symbol.iterator')` 는 **다르다.**
- ★★ **`keyFor`** 는 장부 심볼에만 문자열을 돌려주고, 잘 알려진 심볼·보통 심볼은 `undefined`, 심볼이 아니면 `TypeError`.
- ★★★ **`[4]` — node20 `2 / 3`, node18 `0 / 3`.** node20 에서 거절되는 것은 **장부 심볼뿐**이다.
  명세 **`CanBeHeldWeakly`**: 객체이거나, **심볼이면서 `KeyForSymbol` 이 `undefined`** 일 때만 참이다.
  장부 심볼은 **누구나 같은 문자열로 다시 만들 수 있어서** 「이제 아무도 못 가리킨다」가 성립하지 않는다(명세 note: "does not have language identity").
  잘 알려진 심볼은 **허용된다**(명세 note).
- ★ **`vm` 은 창을 바꿔 물은 것**이다 — 브라우저 iframe 대신 Node 호스트 API 로 realm 을 만들었다.

### 9. `null` 은 「없음」, `1` 은 「잘못 있음」 — **명세의 `GetMethod`** (왜)

**출력** — 1번 `[3]` 의 `is null` · `is undefined` · `is the number 1` 세 줄과 5번 `[2]` 의 `{ [Symbol.hasInstance]: 1 }` 줄.

**왜 그런가**

- ★★★ 언어가 잘 알려진 심볼 키를 읽을 때는 대개 명세의 `GetMethod` 를 쓴다 — 값이 `undefined`·`null` 이면 **「없음」으로 돌려주고**, 함수가 아니면 **`TypeError` 로 던진다.**
  그래서 `toPrimitive: null` 은 `valueOf` 로 넘어가고, `toPrimitive: 1` 과 `hasInstance: 1` 은 **같은 문구**(`number 1 is not a function`)로 던진다.
- ★★ `Symbol.iterator` 에도 같은 「없음」이 선다 — 10번 `[2]` 에서 `undefined` 로 지운 배열을 **`Array.from` 은 「이터레이터 없음」으로 읽고 유사 배열 경로로** 갔다.
  `for...of`·스프레드는 없으면 **이터러블이 아니라고 던진다** — 「없음」을 받은 **소비자가 무엇을 하느냐**가 갈린 것이다.

### 10. `Symbol.iterator` 교체 — **이터러블 소비자 넷만 따라가고 인덱스로 읽는 쪽은 그대로; 지우면 `Array.from` 은 유사 배열로 우회**

**출력**

```text
===== node20 js20b-22g-other-hooks.js (exit=0) =====
[1] an array whose own Symbol.iterator yields 'x' once
  [...arr]                                          ["x"]
  Array.from(arr)                                   ["x"]
  const [a, b] = arr                                ["x","<undefined>"]
  for-of collects                                   ["x"]
  arr.map(v => v)                                   [1,2,3]
  arr.join('')                                      "123"
  Math.max.apply(null, arr)                         3
  JSON.stringify(arr)                               [1,2,3]

[2] the same array with Symbol.iterator set to undefined
  [...arr]                                          TypeError 「arr is not iterable」
  Array.from(arr)                                   [1,2,3]
  for-of                                            TypeError 「arr is not iterable」
  arr.map(v => v)                                   [1,2,3]

[3] Symbol.isConcatSpreadable
  [0].concat([1, 2])                                [0,1,2]
  [0].concat(array with flag false)                 2
  [0].concat({0:'a', length:1})                     2
  [0].concat({0:'a', length:1, flag true})          [0,"a"]

[4] Symbol.match -- what String methods decide is a RegExp
  '/a/b'.startsWith(/a/)                            TypeError 「First argument to String.prototype.startsWith must not be a regular expression」
  re[Symbol.match] = false; '/a/b'.startsWith(re)   true
  'xa'.includes({ [Symbol.match]: true })           TypeError 「First argument to String.prototype.includes must not be a regular expression」

[5] Symbol.unscopables on Array.prototype -- its keys
  keys                                              ["at","copyWithin","entries","fill","find","findIndex","findLast","findLastIndex","flat","flatMap","includes","keys","values","toReversed","toSorted","toSpliced"]
  prototype of that object                          null
  sloppy: with ([1, 2]) { keys / length }           ["string","length 2"]
  strict: compile a with statement                  SyntaxError 「Strict mode code may not include a with statement」
```

**왜 그런가**

- ★★★ **스프레드·`Array.from`·구조 분해·`for...of` 는 `Symbol.iterator` 를 부르고**(`["x"]`), **`map`·`join`·`apply`·`JSON` 은 `length` 와 인덱스로 읽는다**(`[1,2,3]`).
  11편의 「`apply` 는 유사 배열만, 스프레드는 이터러블만, `Array.from` 은 둘 다」가 **한 배열 안에서** 갈라진 줄이다.
- ★★★ **지우면(`undefined`) `Array.from` 만 살아남는다** — 이터레이터 메서드가 없으면 유사 배열로 읽는다. 19편 동작 (4)의 「**`for...of` 에는 유사 배열 대체 경로가 없다**」와 정확히 짝이다 — 대체 경로를 가진 것은 `Array.from` 쪽이다.
- ★★ **`Symbol.match`** 는 명세 `IsRegExp` 가 읽는 키다. 정규식에 `false` 를 두면 **정규식이 아닌 셈**이 되고, 평범한 객체에 `true` 를 두면 **정규식인 셈**이 된다.
  ★ 4번의 `toStringTag` 와 같은 꼴 — **판별이 슬롯이 아니라 키 하나**에 걸려 있다.

### 11. `unscopables` 는 `with` 전용이고, `dispose` 는 **심볼만 먼저 와 있다** (경계)

**출력** — 10번 `[5]` 가 `unscopables` 의 답이고, 목록은 아래 셋이다.

```text
===== node20 js20b-22i-wellknown.js (exit=0) =====
15 ["asyncIterator","hasInstance","isConcatSpreadable","iterator","match","matchAll","replace","search","species","split","toPrimitive","toStringTag","unscopables","dispose","asyncDispose"]
Symbol.iterator descriptor {"value":"Symbol(Symbol.iterator)","writable":false,"enumerable":false,"configurable":false}
a `using` declaration: SyntaxError 「Unexpected identifier 'r'」
```
```text
===== node18 js20b-22i-wellknown.js (exit=0) =====
15 ["asyncIterator","hasInstance","isConcatSpreadable","iterator","match","matchAll","replace","search","species","split","toPrimitive","toStringTag","unscopables","dispose","asyncDispose"]
Symbol.iterator descriptor {"value":"Symbol(Symbol.iterator)","writable":false,"enumerable":false,"configurable":false}
a `using` declaration: SyntaxError 「Unexpected identifier」
```

Chrome 151 — 같은 내용의 파일을 페이지에서 돌렸다.

```js
// js20b-22j-wellknown-chrome.web.js
// 이 판의 잘 알려진 심볼 목록 -- Symbol 생성자에 붙은 심볼 값 프로퍼티를 전부 찍는다.
const names = Object.getOwnPropertyNames(Symbol).filter((k) => typeof Symbol[k] === "symbol");
console.log(names.length + " " + JSON.stringify(names));
const d = Object.getOwnPropertyDescriptor(Symbol, "iterator");
console.log("Symbol.iterator descriptor " + JSON.stringify({ ...d, value: String(d.value) }));
let compiled;
try { new Function("{ using r = null; }"); compiled = "compiled"; } catch (e) { compiled = e.constructor.name + " 「" + e.message + "」"; }
console.log("a `using` declaration: " + compiled);
```
```text
===== google-chrome --headless --dump-dom 'js20b-page.html?js20b-22j-wellknown-chrome.web.js' | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' | sed 's/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&amp;/\&/g' (exit=0) =====
15 ["asyncIterator","hasInstance","isConcatSpreadable","iterator","match","matchAll","replace","search","species","split","toPrimitive","toStringTag","unscopables","dispose","asyncDispose"]
Symbol.iterator descriptor {"value":"Symbol(Symbol.iterator)","writable":false,"enumerable":false,"configurable":false}
a `using` declaration: compiled
```

**왜 그런가**

- ★★ **`Symbol.unscopables` 는 `with` 문이 객체에서 찾지 않을 이름**을 정한다(`with ([1, 2])` 안의 `keys` 가 바깥 변수). **그런데 `with` 는 엄격 모드에서 `SyntaxError` 이고 모듈·`class` 몸통은 늘 엄격**이라 효과를 볼 자리가 거의 없다.
  ★ 그 객체의 **프로토타입이 `null`** 인 것은 `Object.prototype` 의 이름이 섞이지 않게 하려는 모양새다. 키 **순서**는 두 판이 다르게 찍었다(흔들리는 칸).
- ★★★ **잘 알려진 심볼은 세 판 다 15개이고 목록이 같다.** 그중 **`dispose`·`asyncDispose` 는 ES2026 본문에 없다**(finished proposals 표로 ES2027).
  ★★★ **그런데 `using` 선언은 node 두 판에서 `SyntaxError`, Chrome 151 에서만 `compiled`** 다. **「심볼이 있다」는 「문법이 있다」가 아니다.** [목록의 **51번 주제**](../51-explicit-resource-management-and-using/)가 이어받는다.
- ★ `using` 의 문구가 node 두 판에서 다르다(`Unexpected identifier` / `... 'r'`) — **문구만** 갈린 블록이다.

### 12. 파이썬은 **이름**, JS 는 **심볼** — 그리고 진릿값 훅은 JS 에 없다 (연결)

**왜 그런가**

- ★★ 파이썬은 언어 동작을 바꾸는 훅을 **`__iter__`·`__getitem__`·`__bool__` 같은 이름(문자열)** 으로 부른다(Python 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **32번**·**05번**).
  **이름 규약(앞뒤 밑줄 둘)으로 충돌을 피한다.** JS 는 같은 역할의 키를 **심볼**로 만들어 **문자열 키와는 원리상 겹칠 수 없게** 했다 — 2번 격자의 `6 / 10` 이 그 분리의 모양이다.
- ★★★ **파이썬의 `__bool__` 에 해당하는 심볼은 JS 에 없다.** 1번의 `!x`·`x ? :` 가 **`(no call)`** 이다 — 객체는 `toPrimitive` 가 무엇을 돌려주든 **무조건 참**이다.
- ★ 이 문항은 파이썬을 **이 배치에서 다시 돌리지 않았다** — 파이썬 쪽 사실은 그 갈래 문서의 실행 결과를 인용한 것이다.

## 이 파일로 확인할 것

- ① **hint 의 전수 지도**(`default`·`number`·`string`·안 부름)와 `Date` 의 예외
- ② **심볼 키가 누구에게 보이나**(`6 / 10`) — 그리고 「비공개가 아니다」
- ③ **심볼 자신의 변환**(`String()` 만 · `5 / 6`)과 **레지스트리의 대가**(약한 키 불가)
- ④ **잘 알려진 심볼 여럿이 판별을 바꾼다**(`toStringTag` `7 / 7` · `hasInstance` · `match`) · **species 를 읽는 메서드는 절반**(`7 / 14`)

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js20b-22c-toprimitive-hints.js` | ★★★ **연산 24가지의 hint** · 메서드 자리의 `null`/`1`/객체/심볼 · `Date` 의 자체 `toPrimitive` | node20 1벌 + node18 대조 1벌(같음) |
| `js20b-22b-key-grid.js` | ★★★ 키 종류 5 × 문법 10 격자 · 「갈린 칸 `6 / 10`」 · own 키 순서 | node20 1벌 + node18 대조 1벌(같음) |
| `js20b-22a-basics.js` | ★★ `new Symbol` · `description` · 변환 여섯 가지 「`5 / 6`」 · JSON | node20 1벌 + node18 대조 1벌(같음) |
| `js20b-22e-tostringtag.js` | ★★★ 태그 대 슬롯 판별 「`7 / 7`」 · 태그의 출처 · 지우기 | node20 1벌 + node18 대조 1벌(같음) |
| `js20b-22d-hasinstance.js` | ★★ `hasInstance` 의 인자·`ToBoolean` · 우변 문구 셋 · 대입 대 `defineProperty` | node20 1벌 + node18 대조 1벌(같음) |
| `js20b-22f-species.js` | ★★ species 를 읽는 메서드 「`7 / 14`」 · species 값 넷 · `Promise` | node20 1벌 + **node18 판도 싣는다**(갈린 블록) |
| `js20b-22g-other-hooks.js` | ★★ `iterator` 교체·삭제 · `isConcatSpreadable` · `match` · `unscopables` | node20 1벌 + node18 대조(갈림 — `unscopables` 키 목록 한 줄) |
| `js20b-22h-registry.js` | ★★ 레지스트리 같음 · `keyFor` · `vm` realm · 약한 키 「`2 / 3`」 | node20 1벌 + **node18 판도 싣는다**(갈린 블록 · `0 / 3`) |
| `js20b-22i-wellknown.js` · `js20b-22j-wellknown-chrome.web.js` | 잘 알려진 심볼 목록 · `using` 컴파일 여부 | node20 · **node18**(갈림 — 문구) · Chrome 151 각 1벌 |
| `js20b-versions.sh` · `js20b-features.js` | 이 문서의 모든 출력이 **어느 판에서 나왔나** · 판별 기능 표 | 1벌 |
| `js20b-vdiff.sh` | **두 판이 갈린 탐침 수** — 이 주제의 것은 넷 | 1벌(아래) |

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

**구현 의존 항목** — 다음은 **이 환경(node 20.19.6 / 18.19.1 · Chrome 151 · x86-64 Linux)에서만** 그렇다.

- ★★★ **예외 문구 전부** — `Cannot convert a Symbol value to a string` · `... to a number` · `Symbol is not a constructor` · `Right-hand side of 'instanceof' is not callable` ·
  `Right-hand side of 'instanceof' is not an object` · `number 1 is not a function` · `Cannot convert object to primitive value` · `Cannot assign to read only property ...` ·
  `object.constructor[Symbol.species] is not a constructor` · `First argument to String.prototype.startsWith must not be a regular expression` · `arr is not iterable` ·
  `Invalid value used as weak map key` · `WeakRef: invalid target`(node20) / `WeakRef: target must be an object`(node18) · `Unexpected identifier` 계열.
  **종류(`TypeError`·`SyntaxError`)만 명세가 정한다.**
- ★★ **`unscopables` 객체의 키 순서** — 두 판이 다르다.
- ★★ **node18 에 ES2023 기능(배열 복사 메서드 · 심볼 약한 키)이 없는 것** · **`Symbol.dispose` 가 세 판에 있는 것**(ES2026 본문에 없다) · **`using` 을 Chrome 151 만 컴파일하는 것.**
- ★ **`node:vm` 의 realm** — 호스트 API 다.

**hint 가 연산자마다 정해진 것 · `null`/`undefined` 가 「없음」인 것 · 심볼 키가 격자에서 보이는 칸 · own 키 순서 · `String(sym)` 만 되는 것 · `Date` 의 `default` 해석 ·
`instanceof` 의 `ToBoolean` · `Function.prototype[Symbol.hasInstance]` 의 `writable: false` · 태그가 슬롯을 덮는 것 · species 를 쓰는 메서드 목록 · 장부 심볼이 약한 키가 될 수 없는 것은 구현 의존이 아니다.**
어느 엔진에서도 같아야 한다.

**안 돌려 본 것 / 못 잰 것 / 부적용인 창**

- **안 돌려 본 것** — Chrome 에서 22a\~22h(브라우저는 목록·`using` 한 블록만) · 브라우저 **iframe realm**(대신 `vm`) · `Symbol.asyncIterator`(40번) ·
  `Symbol.matchAll`·`replace`·`search`·`split`(정규식 29·30번) · `RegExp` 의 species · 다른 엔진(SpiderMonkey·JavaScriptCore)의 문구.
- ★ **못 잰 것** — **없다.**
- ★★★ **안 쟀다** — **성능 전부.** 심볼 키 접근이 빠르다/느리다는 말을 **한 줄도 쓰지 않았다.**
- ★★ **부적용인 창** — **진단의 `(행,열)`**(`SyntaxError` 두 줄은 결합 방향을 가를 일이 없다). **`Symbol.unscopables` 는 반쯤 부적용** — 엄격 모드에 `with` 가 없다.
- ★★ **창을 바꿔 물은 자리** — realm 을 넘는 같음을 **`vm`** 으로(8번).

**판이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **예외 문구 전부** — `WeakRef` 문구는 **이 주제 안에서 실제로 바뀌었다**(8번).
- ★★ **`using` 컴파일 여부**(11번) — ES2027 을 들인 node 판에서는 답이 바뀐다.
- ★ **`unscopables` 목록**(10번 `[5]`) — 배열 메서드가 늘면 키가 는다(node18 → node20 에서 셋 늘었다).
- **hint · 격자 · 태그 · species 목록은 다시 돌릴 필요가 없다** — ES2015(복사 메서드는 ES2023)부터의 계약이다.
