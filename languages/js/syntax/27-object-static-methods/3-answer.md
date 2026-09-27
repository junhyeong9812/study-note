# js/syntax/27 — `Object` 정적 메서드: 「복사·나열·묶기 — 결과가 같아 보여도 부르는 것이 다르다」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **node v20.19.6**(기본 판) · **node v18.19.1**(대조) · **Google Chrome 151.0.7922.173**(6번) · x86-64 Linux 에서 실제로 돌려 얻은 것이고,
> 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 하나도 없다).
>
> ★★ **예외는 `e.constructor.name` 과 `e.message` 로만** `이름 「메시지」` 꼴로 찍었다 — 스택트레이스에는 절대 경로가 박혀 재현이 안 된다.
> ★★ **이 주제의 node 탐침은 두 판에서 전부 같았다** — 판이 갈린 블록이 없다.
>
> **이 파일이 인용하는 출력을 낸 소스** — 전문은 [1-question.md](1-question.md) 의 같은 번호 문항에 있다(10번의 소스만 여기 싣는다).
> `js24b-27a-assign-log.js`(1번 · 8번) · `js24b-27b-copy-grid.js`(2번 · 11번) · `js24b-27c-readonly-target.js`(3번 · 7번 · 11번) · `js24b-27d-keys-values-entries.js`(4번) ·
> `js24b-27e-fromentries.js`(5번) · `js24b-27f-groupby.web.js`(6번 · 9번) · `js24b-27g-merge-order.js`(10번).

## 정답

### 1. `assign` 은 **원본 getter 를 키마다 한 번 부르고 대상에 대입한다 — 대상 setter 가 불리고, 비열거 키는 값도 안 읽는다** ★★★

**출력**

```text
===== node20 js24b-27a-assign-log.js (exit=0) =====
[1] one source, a target with a setter on q
  log                  ["get A.p","get A.q","set target.q <- Aq"]
  returns the target?  true
  own keys of target   ["q","p","Symbol(sym)"]
  target.q descriptor  ["get","set","enumerable","configurable"]
  target.p descriptor  {"value":"Ap","writable":true,"enumerable":true,"configurable":true}

[2] two sources, left to right
  log                  ["get A.p","get A.q","set target.q <- Aq","get B.p","get B.q","set target.q <- Bq"]
  t2.p  t2.q           ["Bp","Bq"]

[3] the same source spread into an object literal (compare [1])
  log                  ["get target.q","get A.p","get A.q"]
  lit.q descriptor     ["value","writable","enumerable","configurable"]

[4] a source getter throws in the middle
  Error 「from getter」
  log                  ["get first","get second"]
  target afterwards    {"first":1}

[5] sources that are not plain objects
  null, undefined      {}
  'ab'                 {"0":"a","1":"b"}
  5, true              {}
  [7, 8]               {"0":7,"1":8}
  target null          TypeError 「Cannot convert undefined or null to object」
```

**왜 그런가**

- ★★★ **`[1]` 로그는 `get A.p` → `get A.q` → `set target.q <- Aq`** 다. 명세 `Object.assign` 은 원본의 own 키 목록을 받고, 키마다 **디스크립터를 보고 → 열거 가능하면 `Get` → `Set(to, key, value, true)`** 를 한다.
  **키 하나를 끝내고 다음 키로** 간다 — 모두 읽은 뒤 한꺼번에 쓰지 않는다.
  ★ **`hidden` 은 로그에 없다** — 디스크립터가 비열거라 **`Get` 단계에 가지 않는다.**
- ★★ **`target.q` 는 대입 뒤에도 접근자**(`get`/`set` 키)다. 대입은 **프로퍼티를 바꾸는 게 아니라 setter 를 부르는 것**이기 때문이다. 대상에 없던 `p` 는 **데이터 프로퍼티**로 생겼다.
- ★★★ **`[2]`** — 원본 A 를 끝낸 뒤 B. setter 가 **두 번**(`Aq`, `Bq`) 불리고, 결과는 **오른쪽 원본의 값**(`["Bp","Bq"]`)이다.
- ★★★ **`[3]` 스프레드에는 `set` 이 없다.** 첫 항목 `get target.q` 는 스프레드가 `...makeTarget()` 을 **원본으로 읽은** 것이다. 결과의 `q` 는 **데이터 프로퍼티**다 — 스프레드는 **정의**한다.
- ★★ **`[4]`** — `Error 「from getter」`. 대상에는 **`{"first":1}`** 이 남았다 — 되돌리지 않는다. `third` 의 getter 는 안 불렸다.
- ★ **`[5]`** — `null`·`undefined` 는 건너뛴다(`{}`) · `'ab'` 는 `{"0":"a","1":"b"}` · `5`·`true` 는 `{}` · 배열은 인덱스 키 · **대상 `null` 은 `TypeError 「Cannot convert undefined or null to object」`**.

### 2. 격자 — **`assign` 과 스프레드는 한 칸도 안 갈리고, 갈린 칸은 `3 / 18`, 앞의 셋은 전부 얕다** ★★★

**출력**

```text
===== node20 js24b-27b-copy-grid.js (exit=0) =====
[1] grid -- y/n per cell
                                assign   spread   entries  clone
  inner is the same object      y        y        y        n
  counter is still a getter     n        n        n        n
  symbol key copied             y        y        n        n
  non-enumerable key copied     n        n        n        n
  prototype is Point.prototype  n        n        n        n
  copy !== src                  y        y        y        y

[2] how many times was the getter read during the copy?
  Object.assign({}, src)        1
  { ...src }                    1
  fromEntries(entries(src))     1
  structuredClone(src)          1

[3] writing through the copy
  src.inner.deep  99
  src.x           1

cells whose answer differs from the Object.assign column: 3 / 18
```

**왜 그런가**

- ★★★ **첫 행** — `structuredClone` 만 `n`. 나머지 셋은 **바깥 한 겹만** 새로 만든다. 그래서 `[3]` 에서 **`src.inner.deep` 이 `99`** 가 됐고, 바깥 키 `src.x` 는 `1` 그대로다.
- ★★ **셋째 행(심볼)** — `assign`·스프레드는 `y`, **`entries` 왕복은 `n`**(`EnumerableOwnProperties` 가 심볼을 건너뛴다), `structuredClone` 도 `n`.
- ★★ **getter · 비열거 · 프로토타입 세 행은 네 열 다 `n`** — 넷 다 **값을 읽어 평범한 객체에 담는다.** `[2]` 에서 getter 가 넷 다 **한 번** 읽힌 것이 그 증거다.
- ★ **`3 / 18`** — `assign` 열을 기준으로 나머지 세 열 × 여섯 행. `entries` 가 1칸, `clone` 이 2칸.
- 예외도 흔들리는 칸도 없다. `structuredClone` 은 호스트 API 라 그 열만 **node 의 구현**을 본 것이다.

### 3. 읽기 전용 대상 — **`assign` 은 비엄격에서도 던지고, 앞서 쓴 키는 남긴다** ★★★

**출력**

```text
===== node20 js24b-27c-readonly-target.js (exit=0) =====
[1] a frozen target
  sloppy   Object.assign(frozen, { a: 2 })  TypeError 「Cannot assign to read only property 'a' of object '#<Object>'」
  sloppy   frozen.a = 2                     no exception
  strict   Object.assign(frozen, { a: 2 })  TypeError 「Cannot assign to read only property 'a' of object '#<Object>'」
  strict   frozen.a = 2                     TypeError 「Cannot assign to read only property 'a' of object '#<Object>'」

[2] the target has one read-only key, b -- the source writes a, b, c
  Object.assign(t, { a: 1, b: 2, c: 3 })    TypeError 「Cannot assign to read only property 'b' of object '#<Object>'」
  t afterwards                              {"b":"old","a":1}

[3] a frozen source, an ordinary target
  copy is frozen?     false
  fs.a  fs.inner.deep [1,2]
```

**왜 그런가**

- ★★★ **`[1]` 비엄격 함수에서 `Object.assign(frozen, …)` 은 `TypeError`, `frozen.a = 2` 는 `no exception`.** 엄격 함수에서는 둘 다 같은 문구 `Cannot assign to read only property 'a' of object '#<Object>'` 로 던진다.
  ★ **`assign` 의 대입은 호출한 코드의 모드를 보지 않는다** — 7번이 그 이유다.
- ★★★ **`[2]` `t afterwards` 는 `{"b":"old","a":1}`** — `a` 는 들어갔고, `b` 에서 던졌고, **`c` 는 시도되지 않았다.** 원자적이지 않다.
- ★★ **`[3]` 복사본은 안 얼어 있다**(`false`) — `assign` 은 값을 옮길 뿐 **디스크립터(`writable: false`)를 옮기지 않는다**(대상에 새로 생긴 키는 기본 데이터 프로퍼티다).
  그리고 **`fs.inner.deep` 이 `2`** — 얼린 것은 바깥 한 겹이고(14번의 「동결은 얕다」), 복사도 한 겹이라 안쪽을 공유한다.

### 4. 세 뷰 — **순서는 `1, 2, b, a`, 심볼은 `Reflect.ownKeys` 에만, `keys` 는 값을 안 읽고, 목록은 처음에 한 번 받는다** ★★★

**출력**

```text
===== node20 js24b-27d-keys-values-entries.js (exit=0) =====
[1] order -- keys inserted as b, 2, a, 1, Symbol
  Object.keys                   ["1","2","b","a"]
  Object.values                 ["one","two","B","A"]
  Object.entries                [["1","one"],["2","two"],["b","B"],["a","A"]]
  Reflect.ownKeys               ["1","2","b","a","Symbol(s)"]

[2] what each one asks a Proxy (two keys, one of them non-enumerable)
  keys      ["ownKeys","gopd x","gopd y"]
  values    ["ownKeys","gopd x","get x","gopd y"]
  entries   ["ownKeys","gopd x","get x","gopd y"]

[3] a getter that deletes a later key and adds a new one
  Object.entries(m)             [["first","F"],["third","T"]]
  Object.keys(m) afterwards     ["first","third","added"]

[4] non-objects
  Object.keys('ab')             ["0","1"]
  Object.entries(5)             []
  Object.values([7, , 9])       [7,9]
  Object.keys(null)             TypeError 「Cannot convert undefined or null to object」
```

**왜 그런가**

- ★★★ **`[1]`** — `[[OwnPropertyKeys]]` 의 순서(정수 키 오름차순 → 글자 키 삽입순 → 심볼)를 셋이 그대로 쓴다. 규칙 자체는 [13번](../13-object-literals-and-properties/2-summary.md)이 정본이다.
  심볼은 `EnumerableOwnProperties` 가 **「키가 문자열이면」** 조건으로 걸러서 셋 다 안 낸다.
- ★★★ **`[2]`** — `keys` 는 `["ownKeys","gopd x","gopd y"]` 로 **`get` 이 없다.** `values`·`entries` 는 **열거 가능한 `x` 에만** `get x` 가 붙는다. `y` 는 디스크립터만 묻고 끝난다.
- ★★ **`[3]`** — 결과 `[["first","F"],["third","T"]]`. 키 목록(`first, second, third`)은 **맨 처음에** 받았고, `second` 차례에 디스크립터를 다시 물었더니 **없어서** 건너뛰었다. `added` 는 목록에 없었으니 안 나온다(실제로는 들어가 있다 — 둘째 줄).
- ★ **`[4]`** — `["0","1"]` · `[]` · `[7,9]`(구멍은 own 프로퍼티가 아니다) · `TypeError 「Cannot convert undefined or null to object」`.

### 5. `fromEntries` — **쌍의 이터러블을 받아 키를 글자로 정의한다. `Map` 왕복은 `size 4` 가 `3` 이 되고, `"__proto__"` 는 자기 키가 된다** ★★

**출력**

```text
===== node20 js24b-27e-fromentries.js (exit=0) =====
[1] inputs
  fromEntries([['a', 1], ['b', 2]])       {"a":1,"b":2}
  fromEntries(new Map([['a', 1]]))        {"a":1}
  fromEntries([['k', 1], ['k', 2]])       {"k":2}
  fromEntries([['a']])  keys, String(a)   [["a"],"undefined"]
  fromEntries(['ab'])                     TypeError 「Iterator value ab is not an entry object」
  fromEntries([1])                        TypeError 「Iterator value 1 is not an entry object」
  fromEntries({ a: 1 })                   TypeError 「object is not iterable (cannot read property Symbol(Symbol.iterator))」

[2] Map -> object -> Map
  map.size                  4
  Object.keys(obj)          ["1","[object Object]","true"]
  obj['1']                  "string one"
  back.size                 3
  back.get(1)               undefined
  back.get('1')             string one
  back.get(key)             undefined

[3] object -> entries -> transform -> object
  doubled                   {"apple":6,"pear":10}

[4] the key "__proto__" -- fromEntries and assign side by side
  own keys of the JSON source       ["__proto__"]
  fromEntries   own keys ["__proto__"]  marker undefined prototype changed false
  Object.assign own keys []             marker true      prototype changed true
```

**왜 그런가**

- ★★ **`[1]`** — 배열의 배열과 `Map` 은 된다 · 겹친 키는 **나중 것** · 쌍의 둘째가 없으면 `undefined` 값 ·
  원소가 객체가 아니면 `TypeError 「Iterator value ab is not an entry object」`(문자열도 쌍이 아니다) · 평범한 객체는 이터러블이 아니라 `TypeError`.
- ★★★ **`[2]`** — 키가 `ToPropertyKey` 로 글자가 되어 `1` 과 `"1"` 이 한 칸(나중의 `"string one"`), 객체는 `"[object Object]"`. 되돌린 `Map` 은 `size 3`, **`get(1)` 은 `undefined`**(키가 `"1"` 이다), `get(key)` 도 `undefined`.
- ★ **`[3]`** — 값만 두 배가 된 **새 객체**.
- ★★★ **`[4]`** — `fromEntries` 는 `CreateDataPropertyOrThrow` 로 **정의**해서 `"__proto__"` 가 **자기 키**(`own keys ["__proto__"]`, 프로토타입 그대로)다.
  `Object.assign` 은 **대입**이라 `Object.prototype` 의 `__proto__` setter 가 불려 **프로토타입이 바뀌었다**(`own keys []` · `marker true` · `prototype changed true`).

### 6. `groupBy` — **결과의 프로토타입이 `null` 이라 `toString` 이 없고, 키는 글자로 정수 키 순서, `Map.groupBy` 는 정체로 묶는다** ★★★

**출력**

```text
===== google-chrome --headless --virtual-time-budget=2000 --dump-dom 'js24b-page.html?js24b-27f-groupby.web.js' | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' | sed 's/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&amp;/\&/g' (exit=0) =====
[1] Object.groupBy -- the returned object
  JSON.stringify                            {"fruit":[{"name":"a","kind":"fruit","n":3},{"name":"c","kind":"fruit","n":2}],"herb":[{"name":"b","kind":"herb","n":10}]}
  Object.getPrototypeOf(g) === null         true
  'toString' in g                           false
  g.toString()                              TypeError 「g.toString is not a function」
  String(g)                                 TypeError 「Cannot convert object to primitive value」
  `${g}`                                    TypeError 「Cannot convert object to primitive value」
  Object.prototype.toString.call(g)         [object Object]
  g.fruit[0] === items[0]                   true
  Array.isArray(g.fruit)                    true
  g.vegetable                               undefined

[2] the callback -- arguments and call count
  calls                                     [["x",0,0],["y",1,0],["z",2,0]]

[3] the keys -- returned values of different types
  Object.keys                               ["1","odd","[object Object]","true"]
  keys for 'z', '10', '2' (in that order)   ["2","10","z"]

[4] Map.groupBy on the same kind of input
  mg instanceof Map                         true
  mg.size                                   3
  mg.get(k1)                                [1,3]
  mg.get(k2)                                [2]
  mg.get({ id: 1 })                         undefined
  mg.get(0)                                 [4,5]
  Object.is(zero key, -0)                   false

[5] inputs that are not arrays
  Object.groupBy(new Set([1, 2, 3]))        {"small":[1],"big":[2,3]}
  Object.groupBy('aba')                     {"a":["a","a"],"b":["b"]}
  Object.groupBy({ length: 2 })             TypeError 「object is not iterable (cannot read property Symbol(Symbol.iterator))」
  typeof [].groupBy                         undefined

[6] group keys named like Object.prototype members -- a hand-written version into {} and groupBy
  by hand into {}   key "toString"          TypeError 「acc[w].push is not a function」
  Object.groupBy    key "toString"          ["toString"]
  by hand into {}   key "__proto__"         TypeError 「acc[w].push is not a function」
  Object.groupBy    key "__proto__"         ["__proto__"]
  by hand into {}   key "plain"             ["plain"]
  Object.groupBy    key "plain"             ["plain"]
```

**왜 그런가**

- ★★★ **`[1]`** — `getPrototypeOf` 가 `null`, `'toString' in g` 가 `false`, `g.toString()` 은 `TypeError 「g.toString is not a function」`,
  `String(g)` 와 템플릿은 `TypeError 「Cannot convert object to primitive value」` — `ToPrimitive` 가 `toString`·`valueOf` 를 **체인에서 못 찾는다.**
  `Object.prototype.toString.call(g)` 는 **남의 메서드를 빌려 와** `[object Object]` 를 답한다. 묶음은 새 배열이고 원소는 **원본과 같은 객체**다.
- ★★ **`[2]`** — `[["x",0,0],["y",1,0],["z",2,0]]`. 원소마다 한 번, `(값, 인덱스)` 둘뿐이다.
- ★★★ **`[3]`** — 첫 줄 `["1","odd","[object Object]","true"]`(`ToPropertyKey`). **둘째 줄 `["2","10","z"]`** — 묶음이 생긴 순서(`z, 10, 2`)가 아니라 **정수 키 먼저**다. 결과가 평범한 객체라 13번의 순서를 따른다.
- ★★★ **`[4]`** — `Map` 이고, **`size 3`**(`k1`·`k2` 가 따로, `-0`·`0` 이 한 칸). `mg.get(k2)` 는 `[2]`, 새 객체 `{ id: 1 }` 로는 `undefined`. **남은 영(0) 키는 `+0`**(`Object.is(…, -0)` false) — `CanonicalizeKeyedCollectionKey`.
- ★ **`[5]`** — `Set`·문자열은 되고, 유사 배열은 `TypeError`(이터러블만 받는다), **`typeof [].groupBy` 는 `undefined`**.
- ★★★ **`[6]`** — `"toString"`·`"__proto__"` 에서 손으로 짠 쪽만 `TypeError 「acc[w].push is not a function」` 이다. `groupBy` 는 세 키 다 자기 키로 만든다. 이유는 9번.

### 7. `assign` 의 대입은 **`Set(to, key, value, true)`** 다 — 마지막 인자가 「실패하면 던져라」이고 늘 `true` 다 ★★★

- ★★★ 명세 `Object.assign` 은 열거 가능한 키마다 **`Get(from, nextKey)`** 로 읽고 **`Set(to, nextKey, propValue, true)`** 로 쓴다. `Set` 의 넷째 인자 `Throw` 가 `true` 면 `[[Set]]` 이 `false` 를 돌려줄 때 **`TypeError`** 를 던진다.
- ★★ **평범한 대입식 `t.a = 2` 는 같은 연산을 「엄격 모드면 `true`, 아니면 `false`」로 부른다** — 그래서 비엄격에서 조용하다. `assign` 은 그 자리에 **상수 `true`** 를 박아 두어서 **호출한 코드의 모드와 무관**하다(3번 `[1]` 의 sloppy 줄).
- ★ 알고리즘에 **되돌리는 단계가 없다** — `?` 가 붙은 단계(`? Set(…)`)에서 예외가 나면 그대로 빠져나간다. 3번 `[2]` 의 `{"b":"old","a":1}` 이 그 결과다.

### 8. 11번의 「0회 대 1회」 는 **1번 `[1]` 의 `set target.q` 한 줄과 `[3]` 에 그 줄이 없는 것**이다 ★★★

- ★★★ [11번](../11-spread-and-rest/2-summary.md) `[4]` 는 `setter calls after spread 0` · `setter calls after Object.assign 1` 을 찍었다. 이 문서 1번의 `[1]`(assign)에는 `set target.q <- Aq` 가 있고 `[3]`(스프레드)에는 없다.
- ★★ `[3]` 의 `get target.q` 는 **스프레드가 앞자리 `...makeTarget()` 을 원본으로 읽은 것**이다 — setter 가 아니라 **getter** 이고, 대상 쪽이 아니라 **원본 쪽** 호출이다.
- ★ **대상에 setter 가 없어도 갈리는 자리가 남는다** — ① `assign` 은 **첫 인자를 고친다**(새 객체가 아니다) ② 대상 쪽에 **읽기 전용 프로퍼티**가 있으면 `assign` 만 던진다(3번) ③ 대상의 **체인에 setter** 가 있으면(`"__proto__"` 가 대표 — 5번 `[4]`) `assign` 만 그것을 부른다.

### 9. 결과는 **`OrdinaryObjectCreate(null)`** 로 만든다 — 묶음 키가 `Object.prototype` 의 이름과 부딪치지 않게 ★★

- ★★ 명세 `Object.groupBy` 는 `GroupBy(items, callback, property)` 뒤 **`OrdinaryObjectCreate(null)`** 로 객체를 만들고 묶음마다 `CreateDataPropertyOrThrow` 한다.
  note — "The return value of groupBy is an object that does not inherit from %Object.prototype%."
- ★★★ 결과가 `{}` 였다면 **묶음 키가 물려받은 이름과 부딪친다.** 6번 `[6]` 이 그대로 보인다 —
  `{}` 에 손으로 모으는 흔한 코드 `(acc[w] ??= []).push(w)` 가 `"toString"` 과 `"__proto__"` 에서 **`TypeError 「acc[w].push is not a function」`** 이다.
  `acc.toString` 은 **체인의 함수**, `acc.__proto__` 는 **`Object.prototype` 자체**라서 `??=` 가 「이미 있다」고 보고 배열을 안 만든다.
  `Object.groupBy` 는 같은 키를 **자기 키로** 만든다(`["toString"]` · `["__proto__"]`) — 물려받은 것이 없으니 부딪칠 것도 없다.
  「물려받은 이름이 사전을 오염시킨다」는 [23번](../23-map-set-and-weak-collections/2-summary.md) 동작 (3)의 `[3]` 이 `constructor` 로 쟀다(`"function Object() { [native code] }1"`).
- ★ **같은 문구 두 줄** — `String(g)` 와 `` `${g}` `` 의 `Cannot convert object to primitive value`. [15번](../15-prototype-chain/2-summary.md)이 `String(bare)` · `` `${bare}` `` 로 한 글자도 같은 문구를 찍었다.

### 10. 두 언어 다 **「자리는 먼저 들어간 쪽, 값은 나중 쪽」** — 갈리는 것은 정수 키 ★★

**소스**

```js
// js24b-27g-merge-order.js
// Merging two objects -- which position and which value does a shared key end up with?
const J = (x) => JSON.stringify(x);
const a = { x: 1, y: 2 };
const b = { y: 20, z: 30 };
console.log("Object.assign({}, a, b)   " + J(Object.assign({}, a, b)));
console.log("Object.assign({}, b, a)   " + J(Object.assign({}, b, a)));
console.log("{ ...b, ...a }            " + J({ ...b, ...a }));
console.log("a afterwards              " + J(a));
const words = { b: 1 };
const numbers = { 2: "two", 1: "one" };
console.log("Object.assign({}, words, numbers)  keys " + J(Object.keys(Object.assign({}, words, numbers))));
```

**출력**

```text
===== node20 js24b-27g-merge-order.js (exit=0) =====
Object.assign({}, a, b)   {"x":1,"y":20,"z":30}
Object.assign({}, b, a)   {"y":2,"z":30,"x":1}
{ ...b, ...a }            {"y":2,"z":30,"x":1}
a afterwards              {"x":1,"y":2}
Object.assign({}, words, numbers)  keys ["1","2","b"]
```

- ★★★ 파이썬 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **12번**은 `b | a` 를 `{'y': 2, 'z': 30, 'x': 1}` 로 찍었다 — `y` 가 **0번 자리에 값 2**. JS `Object.assign({}, b, a)` 도 `{"y":2,"z":30,"x":1}` 이다. 스프레드도 같다.
  둘 다 겹친 키를 **덮어쓰기**(자리 유지)로 처리한다.
- ★★ **JS 만 정수 키를 앞으로 옮긴다** — `words` 를 먼저 넣었는데 결과 키가 `["1","2","b"]`. 파이썬 `dict` 는 3.7 부터 **넣은 순서**가 언어 보장이고 키 종류로 줄을 가르지 않는다(12번 문서의 인용).
- ★ 파이썬 `a | [("k", 9)]` 는 `TypeError: unsupported operand type(s) for |: 'dict' and 'list'` 였다. JS `Object.assign({}, [7, 8])` 은 **`{"0":7,"1":8}`**(1번 `[5]`) — 원본을 객체로 보고 own 키를 읽을 뿐이다.
- ★ 파이썬 쪽은 이 배치에서 다시 돌리지 않았다 — 12번 문서의 출력 인용이다.

### 11. `structuredClone` 은 `inner` 와 심볼 두 행에서 갈리지만 getter·비열거·프로토타입은 잃는다 · 동결은 복사로 안 따라온다 — 깊은 복사는 **48번 주제** ★★

- ★★ 2번 격자에서 `clone` 열은 **`inner` 공유가 `n`**(안쪽까지 새로 만든다)과 **심볼이 `n`**(심볼 키를 안 옮긴다) 두 칸이 `assign` 과 다르다.
  그래도 **getter(값으로 굳는다) · 비열거 키 · `Point.prototype`** 은 넷 다 잃는다 — `structuredClone` 도 예외가 아니다.
- ★★ 3번 `[3]` — `Object.freeze` 한 원본을 `assign` 으로 복사하면 **`isFrozen` 이 `false`**. 그리고 동결이 얕으므로 **복사본을 거쳐 원본의 `inner.deep` 이 바뀐다**(`[1,2]`). [14번](../14-property-descriptors-and-freezing/2-summary.md)은 「동결은 얕다」까지, 깊은 동결과 깊은 복사는 [목록의 **48번 주제**](../48-deep-copy-methods-compared/)가 정본이다.
- ★ 이 문서는 `structuredClone` 을 **격자의 한 열**로만 쓴다(호스트 API — ECMA-262 밖).

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js24b-27a-assign-log.js` | ★★★ `assign` 의 getter·setter 로그 · 두 원본 · 스프레드 대비 · 도중 예외 · 원시값 원본 | node20 1벌 + node18 대조 1벌 |
| `js24b-27b-copy-grid.js` | ★★★ 복사 도구 4 × 성질 6 격자 · 「갈린 칸 3 / 18」 · getter 읽은 횟수 · 얕음 | node20 1벌 + node18 대조 1벌 |
| `js24b-27c-readonly-target.js` | ★★★ 비엄격·엄격 × `assign`·대입 · 부분 쓰기 · 얼린 원본 | node20 1벌 + node18 대조 1벌 |
| `js24b-27d-keys-values-entries.js` | ★★★ 순서 · `Proxy` 트랩 로그 · 도중 삭제·추가 · 원시값 | node20 1벌 + node18 대조 1벌 |
| `js24b-27e-fromentries.js` | ★★ 입력 검사 · `Map` 왕복 · `"__proto__"` 정의 대 대입 | node20 1벌 + node18 대조 1벌 |
| `js24b-27f-groupby.web.js` | ★★★ null 프로토타입 · 콜백 인자 · 키 강제 변환과 순서 · `Map.groupBy` · 입력 | **Chrome 151 만** |
| `js24b-27g-merge-order.js` | ★★ 병합의 자리와 값 · 정수 키 — 파이썬 대비 | node20 1벌 + node18 대조 1벌 |
| `js24b-vdiff.sh` · `js24b-versions.sh` | 두 판이 갈린 탐침 수 · 이 문서의 출력이 **어느 판에서 나왔나** + 판별 기능 표 | 1벌씩 |

두 node 판 대조기(이 배치 전체의 node 탐침). 이 주제의 줄(`js24b-27…`)은 전부 `identical` 이다. `DIFFERS` 줄은 **다른 주제의 탐침**이다(같은 배치가 한 대조기를 공유한다).

```sh
# js24b-vdiff.sh
#!/usr/bin/env bash
# 두 node 판이 갈린 탐침이 몇 개인가 -- 스크립트가 직접 센다(브라우저 탐침 *.web.js 는 대상이 아니다).
set -u -o pipefail
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
cd "$(dirname "$0")"
same=0; diffn=0
for f in js24b-2[4-7]?-*.js; do
  case $f in *.web.js) continue ;; esac
  a="$("$N18" "$f" 2>&1)"
  b="$("$N20" "$f" 2>&1)"
  if [ "$a" = "$b" ]; then
    printf '%-44s identical\n' "$f"; same=$((same + 1))
  else
    printf '%-44s DIFFERS\n' "$f"; diffn=$((diffn + 1))
    diff <(printf '%s\n' "$a") <(printf '%s\n' "$b") | sed 's/^/    /'
  fi
done
echo ""
echo "identical $same  ·  differs $diffn  ·  total $((same + diffn))"
```
```text
===== ./js24b-vdiff.sh (exit=0) =====
js24b-24a-mutation-grid.js                   identical
js24b-24b-return-values.js                   identical
js24b-24c-default-order.js                   identical
js24b-24d-equal-keys.js                      identical
js24b-24e-inconsistent-fixed.js              identical
js24b-24f-inconsistent-random.js             identical
js24b-24g-undefined-and-holes.js             identical
js24b-24h-same-array.js                      identical
js24b-24i-frozen-target.js                   identical
js24b-24j-frozen-sloppy.js                   identical
js24b-25a-trap-grid.js                       DIFFERS
    7,10c7,10
    <   toSorted()                     0       0       0     1   [3,1,2]     TypeError 「p.toSorted is not a function」
    <   toReversed()                   0       0       0     1   [3,1,2]     TypeError 「p.toReversed is not a function」
    <   toSpliced(0, 1)                0       0       0     1   [3,1,2]     TypeError 「p.toSpliced is not a function」
    <   with(0, 9)                     0       0       0     1   [3,1,2]     TypeError 「p.with is not a function」
    ---
    >   toSorted()                     0       0       0     5   [3,1,2]     [1,2,3]
    >   toReversed()                   0       0       0     5   [3,1,2]     [2,1,3]
    >   toSpliced(0, 1)                0       0       0     4   [3,1,2]     [1,2]
    >   with(0, 9)                     0       0       0     4   [3,1,2]     [9,1,2]
    20,21c20,21
    < methods that threw: 4 / 17
    < methods that returned with zero write traps: 5 / 17
    ---
    > methods that threw: 0 / 17
    > methods that returned with zero write traps: 9 / 17
js24b-25b-pairs.js                           DIFFERS
    3c3
    <   toSorted()            returned TypeError 「a.toSorted is not a function」  === arr -       arr [30,10,20]
    ---
    >   toSorted()            returned [10,20,30]      === arr false   arr [30,10,20]
    5c5
    <   toReversed()          returned TypeError 「a.toReversed is not a function」  === arr -       arr [30,10,20]
    ---
    >   toReversed()          returned [20,10,30]      === arr false   arr [30,10,20]
    7c7
    <   toSpliced(1, 1, 99)   returned TypeError 「a.toSpliced is not a function」  === arr -       arr [30,10,20]
    ---
    >   toSpliced(1, 1, 99)   returned [30,99,20]      === arr false   arr [30,10,20]
    9c9
    <   with(1, 99)           returned TypeError 「a.with is not a function」  === arr -       arr [30,10,20]
    ---
    >   with(1, 99)           returned [30,99,20]      === arr false   arr [30,10,20]
    12c12
    <   base.toSorted().reverse()       TypeError 「base.toSorted is not a function」   base [30,10,20]
    ---
    >   base.toSorted().reverse()       [30,20,10]   base [30,10,20]
    16c16,18
    < TypeError 「rows.toSorted is not a function」
    ---
    >   sorted === rows            false
    >   sorted[1] === rows[0]      true
    >   after sorted[1].id = 200   rows [{"id":200},{"id":1}]
    19c21
    <   toSorted()            TypeError 「[3,(intermediate value),1].toSorted is not a function」
    ---
    >   toSorted()            [1,3,undefined]
    21c23
    <   toReversed()          TypeError 「[3,(intermediate value),1].toReversed is not a function」
    ---
    >   toReversed()          [1,undefined,3]
    23c25
    <   with(0, 9)            TypeError 「[3,(intermediate value),1].with is not a function」
    ---
    >   with(0, 9)            [9,undefined,1]
js24b-25c-index-range.js                     DIFFERS
    2,9c2,9
    <   i = 2     TypeError 「a.with is not a function」   a [0,1,2]
    <   i = 3     TypeError 「a.with is not a function」   a [0,1,2]
    <   i = 5     TypeError 「a.with is not a function」   a [0,1,2]
    <   i = -1    TypeError 「a.with is not a function」   a [0,1,2]
    <   i = -3    TypeError 「a.with is not a function」   a [0,1,2]
    <   i = -4    TypeError 「a.with is not a function」   a [0,1,2]
    <   i = 1.5   TypeError 「a.with is not a function」   a [0,1,2]
    <   i = "1"   TypeError 「a.with is not a function」   a [0,1,2]
    ---
    >   i = 2     [0,1,9]  length 3   a [0,1,2]
    >   i = 3     RangeError 「Invalid index : 3」   a [0,1,2]
    >   i = 5     RangeError 「Invalid index : 5」   a [0,1,2]
    >   i = -1    [0,1,9]  length 3   a [0,1,2]
    >   i = -3    [9,1,2]  length 3   a [0,1,2]
    >   i = -4    RangeError 「Invalid index : -4」   a [0,1,2]
    >   i = 1.5   [0,9,2]  length 3   a [0,1,2]
    >   i = "1"   [0,9,2]  length 3   a [0,1,2]
    22,25c22,25
    <   i = -1  at 2         with TypeError
    <   i = -3  at 0         with TypeError
    <   i = -4  at undefined with TypeError
    <   i = 3   at undefined with TypeError
    ---
    >   i = -1  at 2         with [0,1,9]
    >   i = -3  at 0         with [9,1,2]
    >   i = -4  at undefined with RangeError
    >   i = 3   at undefined with RangeError
js24b-25d-reduce.js                          identical
js24b-25e-map-parseint.js                    identical
js24b-25f-comparator-throws.js               DIFFERS
    3c3
    <   toSorted 0
    ---
    >   toSorted 4
    7c7
    <   toSorted k=1   TypeError 「b.toSorted is not a function」b [5,4,3,2,1]
    ---
    >   toSorted k=1   Error 「call 1」        b [5,4,3,2,1]
    9c9
    <   toSorted k=2   TypeError 「b.toSorted is not a function」b [5,4,3,2,1]
    ---
    >   toSorted k=2   Error 「call 2」        b [5,4,3,2,1]
    11c11
    <   toSorted k=4   TypeError 「b.toSorted is not a function」b [5,4,3,2,1]
    ---
    >   toSorted k=4   Error 「call 4」        b [5,4,3,2,1]
    21c21
    <             toSorted TypeError 「a.toSorted is not a function」
    ---
    >             toSorted returned
    23c23
    <             toSorted TypeError 「a.toSorted is not a function」
    ---
    >             toSorted TypeError 「The comparison function must be either a function or undefined」
    25c25
    <             toSorted TypeError 「a.toSorted is not a function」
    ---
    >             toSorted TypeError 「The comparison function must be either a function or undefined」
    27c27
    <             toSorted TypeError 「a.toSorted is not a function」
    ---
    >             toSorted TypeError 「The comparison function must be either a function or undefined」
js24b-25g-shapes.js                          identical
js24b-26a-hole-grid.js                       identical
js24b-26b-zero-and-nan.js                    identical
js24b-26c-find-family.js                     identical
js24b-26d-at.js                              identical
js24b-26e-flat.js                            identical
js24b-26f-create.js                          identical
js24b-26x-node-fromasync.js                  identical
js24b-27a-assign-log.js                      identical
js24b-27b-copy-grid.js                       identical
js24b-27c-readonly-target.js                 identical
js24b-27d-keys-values-entries.js             identical
js24b-27e-fromentries.js                     identical
js24b-27g-merge-order.js                     identical

identical 26  ·  differs 4  ·  total 30
```

브라우저 탐침(6번)을 돌린 페이지 — 탐침 파일 이름을 주소의 `?` 뒤에 붙여 연다. `console.log` 를 가로채 줄을 모으고, 줄이 늘 때마다 `<pre>` 를 다시 쓴다. `--dump-dom` 이 그것을 내보낸다.

```html
<!-- js24b-page.html -->
<!doctype html>
<meta charset="utf-8">
<title>js24b</title>
<pre id="o"></pre>
<script>
// 탐침 스크립트 하나를 이 페이지에서 돌린다 -- 파일 이름은 주소의 ? 뒤에 온다.
// console.log 를 가로채 줄을 모으고, 줄이 늘 때마다 <pre> 를 다시 쓴다.
// 그래서 프라미스·타이머 뒤에 찍힌 줄도 --dump-dom 이 내보낼 때(가상 시간 예산이 끝날 때) 들어 있다.
const __lines = [];
const __render = () => {
  document.getElementById("o").textContent = "==" + "=OUT===\n" + __lines.join("\n") + "\n===END" + "===";
};
console.log = (...a) => { __lines.push(a.join(" ")); __render(); };
window.addEventListener("error", (e) => { __lines.push("uncaught " + e.message); __render(); });
window.addEventListener("unhandledrejection", (e) => { __lines.push("unhandled rejection " + String(e.reason)); __render(); });
__render();
document.write('<script src="' + location.search.slice(1) + '"><\/script>');
</script>
```

**구현 의존 항목** — 다음은 **이 환경에서만** 그렇다.

- ★★ **예외 문구 전부** — `Cannot assign to read only property 'a' of object '#<Object>'` · `Cannot convert undefined or null to object` · `Iterator value ab is not an entry object` · `Iterator value 1 is not an entry object` ·
  `object is not iterable (cannot read property Symbol(Symbol.iterator))` · `g.toString is not a function` · `Cannot convert object to primitive value`. **종류만 명세가 정한다.**
- ★ `structuredClone` 열 — 호스트(node 20)의 구현이다.

**`assign` 의 호출 순서와 `Set(…, true)` · 되돌리지 않는 것 · `EnumerableOwnProperties` 의 순서·심볼 제외·재조회 · `fromEntries` 의 정의 · `groupBy` 의 null 프로토타입·키 강제 변환·콜백 인자 · `Map.groupBy` 의 `-0` 접기는 구현 의존이 아니다.**
어느 엔진에서도 같아야 한다.

**안 돌려 본 것 / 못 잰 것 / 부적용인 창**

- **안 돌려 본 것** — getter 를 디스크립터째 옮기는 `defineProperties` 경로 · 파이썬 쪽 재실행(12번 문서 인용) · 다른 엔진의 문구.
- ★ **못 잰 것** — **`groupBy` 의 node 판 동작.** 두 node 판에 메서드가 없다(판별 블록) — Chrome 151 로 창을 바꿨다.
- ★★★ **안 쟀다** — **성능 전부.** 센 것은 호출 횟수뿐이다.
- ★★ **부적용인 창** — **진단의 `(행,열)`**(`SyntaxError` 가 없다). **「잴 것이 없다」는 뜻**이다.

**판이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **node 22 이후의 판** — `Object.groupBy`·`Map.groupBy`(ES2024)가 들어온 판에서는 **6번을 node 로도** 돌린다. 판별 블록의 `no` 가 `yes` 로 바뀌는지 먼저 본다.
- ★★ **예외 문구 전부**.
