# js/syntax/31 — `JSON`: 「같은 값도 놓인 자리에 따라 다른 글자가 된다」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **node v20.19.6**(기본 판) · **node v18.19.1**(대조) · **Google Chrome 151.0.7922.173**(6번의 `.web.js`) · **python3 3.12.3**(9번) · x86-64 Linux 에서 실제로 돌려 얻은 것이고,
> 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 하나도 없다).
>
> ★★ **예외는 `e.constructor.name` 과 `e.message` 로만** 찍었다 — 스택트레이스에는 절대 경로가 박혀 재현이 안 된다.
> ★★ **이 주제에서 두 node 판이 갈린 탐침은 `js28b-31d-parse-reviver.js` 하나**다 — `JSON.parse` 의 실패 **문구**만 갈렸다(4번).
>
> **이 파일이 인용하는 출력을 낸 소스** — 전문은 [1-question.md](1-question.md) 의 같은 번호 문항에 있다.
> `js28b-31a-type-grid.js`(1번 · 7번) · `js28b-31b-throws.js`(2번 · 8번) · `js28b-31c-tojson-replacer.js`(3번 · 8번) · `js28b-31d-parse-reviver.js`(4번 · 8번 · 10번) ·
> `js28b-31e-deep-copy.js`(5번 · 10번 · 11번) · `js28b-31x-node-rawjson.js` 와 `js28b-31f-rawjson.web.js`(6번 · 11번) · `js28b-31g-python-contrast.sh` 와 `js28b-31-h-pyjson.py`(9번).

## 정답

### 1. 못 싣는 값(`undefined`·함수·심볼)만 자리가 가른다 — **속성이면 키째 빠지고, 배열이면 `null`, 최상위면 `undefined`** · 갈린 행 `3 / 14` ★★★

**출력**

```text
===== node20 js28b-31a-type-grid.js (exit=0) =====
[1] value                      as property                 as array element            top level
  null                        null                        null                        null
  's'                         "s"                         "s"                         "s"
  undefined                   (key gone)                  null                        (undefined)
  () => 1                     (key gone)                  null                        (undefined)
  Symbol('s')                 (key gone)                  null                        (undefined)
  NaN                         null                        null                        null
  Infinity                    null                        null                        null
  -0                          0                           0                           0
  1n                          TypeError                   TypeError                   TypeError
  new Date(0)                 "1970-01-01T00:00:00.000Z"  "1970-01-01T00:00:00.000Z"  "1970-01-01T00:00:00.000Z"
  new Map([[1, 2]])           {}                          {}                          {}
  new Set([1])                {}                          {}                          {}
  Object.create(null) + a:1   {"a":1}                     {"a":1}                     {"a":1}
  new Boolean(false)          false                       false                       false

[2] a hole in a sparse array, next to an explicit undefined
  JSON.stringify([1, , 3])          [1,null,3]
  JSON.stringify([1, undefined, 3]) [1,null,3]
  JSON.stringify(new Array(2))      [null,null]

[3] keys that are not plain strings
  { [sym]: 1, a: 2 }        {"a":2}
  { 2: 'x', 1: 'y', b: 0 }  {"1":"y","2":"x","b":0}
  non-enumerable h          {"a":1}
  class instance            {"own":1}

rows whose three positions do not all agree: 3 / 14
```

**왜 그런가**

- ★★★ **세 칸이 전부 다른 행은 `undefined` · `() => 1` · `Symbol('s')` 셋**이다 — `(key gone)` / `null` / `(undefined)`.
  명세의 `SerializeJSONProperty` 가 이 셋에 **`undefined` 를 돌려주고**, 그것을 받은 쪽이 자리마다 다르게 처리한다 — 객체는 **멤버를 안 만들고**, 배열은 **`"null"` 을 넣고**, 최상위는 **그대로 돌려준다**(7번).
- ★★★ **최상위의 `(undefined)` 는 글자가 아니다** — `JSON.stringify` 의 반환값이 `undefined` 라는 값이다. 탐침이 그것을 `(undefined)` 로 표시했다.
- ★★ **`NaN`·`Infinity` 는 `null`**, **`-0` 은 `0`** — 세 자리 모두 같다. 이들은 「숫자이지만 유한하지 않다」 갈래라 `"null"` 이라는 **글자**가 돌아오고, 그래서 **속성 자리에서도 키가 남는다.**
- ★★ **`Date` 는 ISO 문자열**(`toJSON`) · **`Map`·`Set` 은 `{}`**(own 키가 없다 — `Map` 은 23번이 정본) · **null 프로토타입 객체는 `{"a":1}`** · **`new Boolean(false)` 는 `false`**(래퍼를 푼다) · **`1n` 은 `TypeError`**.
- ★★★ **`[2]` 구멍과 `undefined` 는 결과 글자로 못 가른다** — 둘 다 `[1,null,3]`, `new Array(2)` 는 `[null,null]`.
- ★★ **`[3]`** — 심볼 키는 빠지고(`{"a":2}`), 정수 키는 앞으로(`{"1":"y","2":"x","b":0}` — 13번의 순서), 비열거 키는 빠지고, 상속된 키도 빠진다(`{"own":1}`).
- ★ 마지막 줄 **`3 / 14`** — 「세 자리가 모두 같지는 않은 행」의 수 / 값의 수.

### 2. 순환은 **`TypeError` 이고 V8 이 경로를 그려 준다** · 공유는 순환이 아니다 · `BigInt` 는 속성 안에서도 `TypeError` ★★★

**출력**

```text
===== node20 js28b-31b-throws.js (exit=0) =====
[1] cycles
  self.me = self                  TypeError
    | Converting circular structure to JSON
    |     --> starting at object with constructor 'Object'
    |     --- property 'me' closes the circle
  a.b.c.back = a                  TypeError
    | Converting circular structure to JSON
    |     --> starting at object with constructor 'Object'
    |     |     property 'b' -> object with constructor 'Object'
    |     |     property 'c' -> object with constructor 'Object'
    |     --- property 'back' closes the circle
  arr[1][1] = arr                 TypeError
    | Converting circular structure to JSON
    |     --> starting at object with constructor 'Array'
    |     |     index 1 -> object with constructor 'Array'
    |     --- index 1 closes the circle
  class instances, n1 <-> n2      TypeError
    | Converting circular structure to JSON
    |     --> starting at object with constructor 'Node2'
    |     |     property 'next' -> object with constructor 'Node2'
    |     --- property 'next' closes the circle

[2] one object reached through two keys
  { x: shared, y: shared }        returned {"x":{"v":1},"y":{"v":1}}

[3] BigInt
  1n                              TypeError
    | Do not know how to serialize a BigInt
  { id: 10n }                     TypeError
    | Do not know how to serialize a BigInt
  replacer: bigint -> toString()  returned {"id":"10"}
  BigInt.prototype.toJSON set     returned {"id":"10n"}

[4] a.b.c.back = a again, with a WeakSet replacer
  WeakSet replacer                returned {"name":"a","b":{"c":{"back":"[seen]"}}}
```

**왜 그런가**

- ★★★ **네 경우 모두 `TypeError`** 이고, 메시지는 **`Converting circular structure to JSON`** 다음에 경로를 그린다.
  `self.me = self` 는 **세 줄**(시작 · 닫는 키 `me`), `a.b.c.back = a` 는 **다섯 줄**(`b` · `c` 를 거쳐 `back` 이 닫는다).
- ★★ 배열은 **`index 1`** 로, 클래스 인스턴스는 **`constructor 'Node2'`** 로 적는다 — 객체 쪽은 `property '…'` · `constructor 'Object'` 다.
- ★★★ **이 경로 그림은 V8 의 것**이다. 명세는 「`[[Stack]]` 에 이미 있으면 `TypeError`」까지만 정한다(8번). **종류는 보장, 문구는 관찰**이다.
- ★★★ **`[2]` 공유는 통과**하고 `{"v":1}` 이 **두 번** 쓰인다 — stack 은 **지금 내려가는 길**만 들고 있어서 옆 가지에서 본 객체에는 안 걸린다.
- ★★★ **`[3]` `BigInt` 는 자리와 상관없이 `TypeError 「Do not know how to serialize a BigInt」`** — 속성 안에서도 조용히 빠지지 않는다.
  `replacer` 로 문자열로 바꾸면 `{"id":"10"}`, **`BigInt.prototype.toJSON` 을 달면 `{"id":"10n"}`** — 명세가 `toJSON` 을 「**객체이거나 BigInt**」에서 찾기 때문이다.
- ★★ **`[4]` `back` 자리는 `"[seen]"`** — `replacer` 가 이미 본 객체를 글자로 바꿔 고리를 끊었다. (이 `WeakSet` 판은 순환이 아닌 공유도 같이 바꾼다.)

### 3. **`toJSON` 이 먼저, `replacer` 가 그 다음** — `replacer` 는 바뀐 값을 받고, `this` 는 그 값을 들고 있던 객체다 ★★★

**출력**

```text
===== node20 js28b-31c-tojson-replacer.js (exit=0) =====
[1] call log
  replacer(key="", value:object, this={"": root})
  toJSON(key="a")
  replacer(key="a", value:object, this=root)
  replacer(key="swapped", value:boolean, this={swapped})
  replacer(key="b", value:array, this=root)
  replacer(key="0", value:number, this=array)
  replacer(key="1", value:string, this=array)
  result {"a":{"swapped":true},"b":[10,"1970-01-01T00:00:00.000Z"]}

[2] toJSON on the root object itself
  root toJSON(key="")
  replacer(key="", value 42)
  result 42

[3] what the replacer returns
  undefined for key b        {"a":1}
  undefined for key ""       undefined
  undefined for index 1      [1,null,3]
  typeof key for an index    string

[4] replacer as an array -- an allow-list of keys
  ['id', 'meta']             {"id":1,"meta":{"id":2}}
  ['id', 'meta', 'list']     {"id":1,"meta":{"id":2},"list":[{"id":3}]}
  [1, 'id', 'id']            {"1":"one","id":1}
  ['0'] on an array          ["a","b"]

[5] the space argument
  2          "{\n  \"a\": [\n    1\n  ]\n}"
  10         "{\n          \"a\": [\n                    1\n          ]\n}"
  20         "{\n          \"a\": [\n                    1\n          ]\n}"
  -1         "{\"a\":[1]}"
  '--'       "{\n--\"a\": [\n----1\n--]\n}"
  'abcdefghijklmnop'  "{\nabcdefghij\"a\": [\nabcdefghijabcdefghij1\nabcdefghij]\n}"
  length of the indent for 20         10
```

**왜 그런가**

- ★★★ **`toJSON` 은 둘째 줄**이다 — 첫 줄은 루트의 `replacer(key="")`, 그 다음 키 `a` 에서 **`toJSON(key="a")` → `replacer(key="a", …)`** 순이다.
  넷째 줄의 키는 **`swapped`** — `replacer` 는 `toJSON` 이 돌려준 새 객체 안을 돈다. 원래의 `x` 는 **한 번도 안 나온다.**
- ★★★ **마지막 줄의 `value` 는 `string`** — `Date` 가 `toJSON` 으로 이미 ISO 문자열이 된 뒤다.
- ★★ **첫 줄의 `this` 는 `{"": root}`** — 명세가 만드는 감싸개 객체다. 그래서 `replacer` 가 루트도 한 번 받는다.
- ★★ **`[2]`** — 루트의 `toJSON(key="")` 가 먼저, 그 다음 `replacer(key="", value 42)`, 결과 **`42`**.
- ★★★ **`[3]`** — 속성은 빠지고(`{"a":1}`), 루트면 결과가 **`undefined`**, 배열 원소면 **`null`**(`[1,null,3]`). 배열 인덱스의 키도 **`string`** 으로 온다.
- ★★★ **`[4]` 허용 목록은 모든 깊이의 객체 키에 적용**된다 — `meta` 안에서도 `id` 만 남는다(`{"id":2}`). `list` 를 넣어야 배열이 나오고 그 안에도 적용된다. **배열의 인덱스에는 적용되지 않는다**(`["a","b"]`). `1` 은 `"1"` 로 바뀌고 중복은 한 번.
- ★★ **`[5]` `10` 과 `20` 은 한 글자도 같다** — `space` 의 상한이 **10**(`min(10, …)`). 마지막 줄 **`10`**. 문자열은 **앞 10글자**, `1` 보다 작으면 들여쓰기 없음.

### 4. `reviver` 는 **후위 순서**(잎 → 뿌리 `""`) · JSON 의 `"__proto__"` 는 **그냥 데이터 키** · 가장자리는 전부 `SyntaxError`, 문구는 판마다 다르다 ★★★

**출력**

```text
===== node20 js28b-31d-parse-reviver.js (exit=0) =====
[1] call order
   1. "b" = 1
   2. "0" = 2
   3. "1" = 3
   4. "c" (object)
   5. "a" (object)
   6. "d" = 4
   7. "" (object)

[2] returning undefined, and returning something else
  drop key b       {"a":{"c":[2,3]},"d":4}
  drop index 0     {"a":{"b":1,"c":[null,3]},"d":4}
  double numbers   {"a":{"b":2,"c":[4,6]},"d":8}
  drop key ""      undefined
  without reviver  typeof when = string
  with reviver     when instanceof Date = true

[3] the key "__proto__" in JSON text, next to the same key in an object literal
  JSON.parse      own keys ["__proto__"]   o.marker undefined  prototype is Object.prototype true
  object literal  own keys []              o.marker 1          prototype is Object.prototype false

[4] texts at the edge of the grammar
  "{'a': 1}"        -> SyntaxError 「Expected property name or '}' in JSON at position 1」
  "{\"a\": 1,}"     -> SyntaxError 「Expected double-quoted property name in JSON at position 8」
  "[1, 2,]"         -> SyntaxError 「Unexpected token ']', "[1, 2,]" is not valid JSON」
  "{a: 1}"          -> SyntaxError 「Expected property name or '}' in JSON at position 1」
  "NaN"             -> SyntaxError 「"NaN" is not valid JSON」
  "undefined"       -> SyntaxError 「"undefined" is not valid JSON」
  "01"              -> SyntaxError 「Unexpected number in JSON at position 1」
  ""                -> SyntaxError 「Unexpected end of JSON input」
  " [1] "           -> [1]
  "{\"a\":1,\"a\":2}"-> {"a":2}
```

node 18 에서는 `[4]` 의 문구 여섯 줄이 이렇게 달랐다(나머지는 한 글자도 같다).

```text
===== node18 js28b-31d-parse-reviver.js (exit=0) =====
[1] call order
   1. "b" = 1
   2. "0" = 2
   3. "1" = 3
   4. "c" (object)
   5. "a" (object)
   6. "d" = 4
   7. "" (object)

[2] returning undefined, and returning something else
  drop key b       {"a":{"c":[2,3]},"d":4}
  drop index 0     {"a":{"b":1,"c":[null,3]},"d":4}
  double numbers   {"a":{"b":2,"c":[4,6]},"d":8}
  drop key ""      undefined
  without reviver  typeof when = string
  with reviver     when instanceof Date = true

[3] the key "__proto__" in JSON text, next to the same key in an object literal
  JSON.parse      own keys ["__proto__"]   o.marker undefined  prototype is Object.prototype true
  object literal  own keys []              o.marker 1          prototype is Object.prototype false

[4] texts at the edge of the grammar
  "{'a': 1}"        -> SyntaxError 「Unexpected token ' in JSON at position 1」
  "{\"a\": 1,}"     -> SyntaxError 「Unexpected token } in JSON at position 8」
  "[1, 2,]"         -> SyntaxError 「Unexpected token ] in JSON at position 6」
  "{a: 1}"          -> SyntaxError 「Unexpected token a in JSON at position 1」
  "NaN"             -> SyntaxError 「Unexpected token N in JSON at position 0」
  "undefined"       -> SyntaxError 「Unexpected token u in JSON at position 0」
  "01"              -> SyntaxError 「Unexpected number in JSON at position 1」
  ""                -> SyntaxError 「Unexpected end of JSON input」
  " [1] "           -> [1]
  "{\"a\":1,\"a\":2}"-> {"a":2}
```

**왜 그런가**

- ★★★ **`[1]` 순서는 `b, 0, 1, c, a, d, ""`** — 첫 줄 `"b"`, 마지막 줄 **`""`(뿌리)**. `InternalizeJSONProperty` 가 **자식을 전부 돈 다음 자기 이름으로** `reviver` 를 부르기 때문이다(8번).
- ★★★ **`[2]`** — `undefined` 를 돌려주면 지운다. **`drop index 0` 의 배열은 여전히 두 칸**이고 앞칸이 구멍이라 다시 찍으면 `[null,3]` 이다. 뿌리에서 지우면 결과 전체가 `undefined`. **`Date` 는 `reviver` 가 만들어 줘야** 돌아온다.
- ★★★ **`[3]` `JSON.parse` 의 `"__proto__"` 는 own 키**(`["__proto__"]`)이고 `o.marker` 는 `undefined`, 프로토타입은 **그대로**다. 객체 리터럴은 반대로 own 키가 없고 `marker 1`, 프로토타입이 **바뀌었다.**
- ★★ **`[4]` 앞의 여덟 줄은 전부 `SyntaxError`** — 작은따옴표 · 끝 쉼표(객체·배열) · 따옴표 없는 키 · `NaN` · `undefined` · 앞자리 `0` · 빈 문자열. **앞뒤 공백은 통과**하고 **중복 키는 뒤의 것이 이긴다**(`{"a":2}`).
- ★★★ **문구는 두 판이 다르다** — node18 은 `Unexpected token ' in JSON at position 1` 꼴, node20 은 `Expected property name or '}' in JSON at position 1` · `"NaN" is not valid JSON` 꼴이다. **이 주제에서 두 판이 갈린 유일한 블록**이고, 갈린 것은 **문구뿐**(종류 · 위치 숫자 · 나머지 줄은 같다).

### 5. 두 열이 `11 / 13` 행에서 갈린다 — **JSON 왕복은 `Date`·`Map`·`Set`·`undefined`·`NaN`·`-0`·`RegExp`·공유·순환을 잃고, 둘 다 프로토타입과 getter 를 잃는다** ★★★

**출력**

```text
===== node20 js28b-31e-deep-copy.js (exit=0) =====
[1] kind of value            JSON round trip         structuredClone
  Date                      string                  Date
  Map                       {}                      Map size 1
  Set                       {}                      Set size 1
  undefined property        key gone                key kept
  NaN                       null                    NaN
  -0                        0                       -0
  BigInt                    TypeError               bigint
  RegExp                    {}                      RegExp /a/g
  class instance            plain {"x":1}           plain {"x":1}
  function property         undefined               DOMException
  same object twice         two objects             still one object
  cycle                     TypeError               cycle kept
  getter                    data 1                  data 1

[2] the two exceptions -- constructor, name, and the first line of the message
  JSON round trip   cycle     TypeError (name TypeError) 「Converting circular structure to JSON」
  structuredClone   function  DOMException (name DataCloneError) 「() => 1 could not be cloned.」

rows where the two columns differ: 11 / 13
```

**왜 그런가**

- ★★★ JSON 왕복 열은 **1번 격자를 한 번 지나 글자에서 다시 만든 것**이다 — `Date` 는 `string`, `Map`·`Set`·`RegExp` 는 `{}`, `undefined` 속성은 `key gone`, `NaN` 은 `null`, `-0` 은 `0`, `BigInt` 와 순환은 `TypeError`, 공유는 **두 객체**가 된다.
- ★★ **`class instance` 와 `getter` 행은 두 열이 같다** — 둘 다 **`plain {"x":1}`**(프로토타입을 잃는다)와 **`data 1`**(getter 가 값으로 굳는다). 그래서 갈린 행이 13 이 아니라 **11** 이다.
- ★★ **`function property`** — JSON 은 `undefined`(속성이 빠졌다), `structuredClone` 은 **`DOMException`**(던졌다).
- ★★ **`[2]`** — 순환은 `TypeError (name TypeError)`, 함수는 **`DOMException (name DataCloneError)`** — 생성자 이름과 `name` 이 **다르다.** `DOMException` 은 한 생성자가 `name` 으로 종류를 가른다(호스트 API).
- ★ 마지막 줄 **`11 / 13`**.

### 6. node 두 판에는 **없다** — Chrome 151 에서는 `context.source` 가 **원래 글자**를 주고 `JSON.rawJSON` 이 그 글자를 **그대로 끼운다**(ES2026) ★★

**출력**

```text
===== node20 js28b-31x-node-rawjson.js (exit=0) =====
typeof JSON.rawJSON      undefined
typeof JSON.isRawJSON    undefined
reviver arguments.length 2
JSON.rawJSON('1')        TypeError 「JSON.rawJSON is not a function」
```

```text
===== google-chrome --headless --virtual-time-budget=2000 --dump-dom 'js28b-page.html?js28b-31f-rawjson.web.js' | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' | sed 's/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&amp;/\&/g' (exit=0) =====
[1] a number with more digits than a double holds
  JSON.parse(big)                               12345678901234567000
  reviver: value, context.source                12345678901234567000   {"source":"12345678901234567890"}
  reviver returns BigInt(context.source)        12345678901234567890n

[2] which keys get a source
  key "n"   context {"source":"1.50"}
  key "s"   context {"source":"\"x\""}
  key "t"   context {"source":"true"}
  key "o"   context {}
  key "0"   context {"source":"null"}
  key "a"   context {}
  key ""    context {}

[3] JSON.rawJSON
  JSON.stringify({ id: JSON.rawJSON(big) })     {"id":12345678901234567890}
  JSON.stringify({ id: 12345678901234567890 })  {"id":12345678901234567000}
  JSON.stringify({ n: JSON.rawJSON('1.50') })   {"n":1.50}
  JSON.isRawJSON(JSON.rawJSON('1'))             true
  Object.isFrozen(JSON.rawJSON('1'))            true
  Object.getPrototypeOf(JSON.rawJSON('1'))      null
  JSON.rawJSON('{}')                            SyntaxError 「Unexpected token '{', "{}" is not valid JSON」
  JSON.rawJSON(' 1')                            SyntaxError 「Unexpected token ' ', " 1" is not valid JSON」
  JSON.rawJSON('abc')                           SyntaxError 「Unexpected token 'a', "abc" is not valid JSON」
  replacer returns rawJSON for a BigInt         {"id":100000000000000000000}
```

**왜 그런가**

- ★★★ **node 20 — `typeof` 둘 다 `undefined`, `reviver` 의 인자는 2개**, `JSON.rawJSON('1')` 은 `TypeError 「JSON.rawJSON is not a function」`. node 18 도 한 글자도 같았다(대조기의 `identical`).
- ★★★ **Chrome `[1]`** — 그냥 파싱하면 `12345678901234567000`(double 로 반올림), **`context.source` 는 `"12345678901234567890"`** — 다른 글자다. 그것으로 `BigInt` 를 만들면 끝자리가 산다.
- ★★ **`[2]` `source` 가 있는 키는 원시값뿐** — `n`·`s`·`t`·`0`. 객체·배열·뿌리(`o`·`a`·`""`)는 `{}`. `"1.50"` 은 **글자 그대로**, 문자열은 **따옴표째**(`"\"x\""`).
- ★★ **`[3]`** — `JSON.rawJSON` 은 **원시 JSON 값 하나의 글자**만 받는다. `'{}'` · `' 1'`(앞 공백) · `'abc'` 는 **`SyntaxError`**. 만든 객체는 **동결**되어 있고 프로토타입이 **`null`** 이다.

### 7. `SerializeJSONProperty` 가 **`undefined` 를 돌려주는 값**이 있고, 그것을 받은 **호출자가 자리마다 다르다** ★★★

- ★★★ **`undefined`·함수(호출 가능한 객체)·심볼** — 타입별 갈래 어디에도 안 걸려 마지막 단계 「`undefined` 를 돌려준다」에 떨어진다.
- ★★★ **`SerializeJSONObject` 는 `strP` 가 `undefined` 면 멤버를 안 만든다**(키째 빠짐), **`SerializeJSONArray` 는 `undefined` 면 `"null"` 을 넣는다**(인덱스를 지킨다).
- ★★ 최상위 값은 감싸개 `{"": v}` 에 넣고 **`SerializeJSONProperty` 를 한 번 부른 결과를 그대로 돌려준다** — 객체·배열의 처리를 안 거치므로 `undefined` 가 그대로 나온다.
- ★ `NaN` 은 **숫자**라 「숫자면 유한할 때 `ToString`, 아니면 `"null"`」 갈래로 간다 — `undefined` 가 아니라 **`"null"` 이라는 글자**가 돌아오므로 속성 자리에서도 키가 남는다.

### 8. 한 키마다 **`toJSON`(2단계) → `replacer`(3단계)** · `reviver` 는 **자식 재귀가 끝난 뒤 마지막 단계** · 순환은 **`[[Stack]]`** ★★★

- ★★★ `SerializeJSONProperty` — ① `Get` ② 객체이거나 `BigInt` 면 **`toJSON`** ③ **`replacer`** ④ 래퍼 풀기 ⑤ 이후 타입별 글자. 그래서 `replacer` 는 **바뀐 값**을 받는다(3번).
- ★★★ `InternalizeJSONProperty` — 값이 객체면 **키마다 자기 자신을 재귀로 먼저** 부르고, **마지막 단계에서** `Call(reviver, holder, « name, val »)` 한다. 후위 순서다(4번 `[1]`).
- ★★ 그래서 `reviver` 가 부모를 받을 때 자식은 **이미 `reviver` 를 거친 값**이다(지워진 키는 이미 없다).
- ★ 순환 — `SerializeJSONObject`·`SerializeJSONArray` 가 들어갈 때 값을 **`[[Stack]]` 에 넣고 나올 때 뺀다.** 2번 `[2]` 의 `shared` 는 `x` 를 다 쓰고 **빠진 뒤**에 `y` 에서 다시 들어가므로 안 걸린다.

### 9. **파이썬은 거절이 기본, JS 는 조용한 변환이 기본** — `default=` 는 못 싣는 값에만 불린다 ★★

**출력**

```text
===== ./js28b-31g-python-contrast.sh (exit=0) =====
[1] the values of the JS grid, and dict keys
  json.dumps(float('nan'))                    'NaN'
  json.dumps(math.inf)                        'Infinity'
  json.dumps(nan, allow_nan=False)            ValueError 「Out of range float values are not JSON compliant: nan」
  json.dumps(None)                            'null'
  json.dumps({'k': None})                     '{"k": null}'
  json.dumps(-0.0)                            '-0.0'
  json.dumps({1: 'a', 2: 'b'})                '{"1": "a", "2": "b"}'
  json.dumps({1: 'a', '1': 'b'})              '{"1": "a", "1": "b"}'
  json.dumps({(1, 2): 'a'})                   TypeError 「keys must be str, int, float, bool or None, not tuple」
  json.dumps({1, 2})                          TypeError 「Object of type set is not JSON serializable」
  json.dumps(10 ** 20)                        '100000000000000000000'
  json.dumps(lambda: 1)                       TypeError 「Object of type function is not JSON serializable」

[2] cycle
  d['me'] = d                                 ValueError 「Circular reference detected」

[3] default= -- when is it called?
  dumps({'s': {2, 1}, 'n': 1}, default=...)   '{"s": [1, 2], "n": 1}'
  default called for                          ['set']

[4] loads
  json.loads('NaN')                           nan
  json.loads('12345678901234567890')          12345678901234567890
  json.loads('{"a":1,"a":2}')                 {'a': 2}
  json.loads('[1,]')                          JSONDecodeError 「Expecting value: line 1 column 4 (char 3)」
```

- ★★★ **`NaN`** — 파이썬 `'NaN'`(JSON 이 아닌 글자, `allow_nan=False` 면 `ValueError`), JS `null`. **집합** — 파이썬 `TypeError`, JS `{}`. **함수** — 파이썬 `TypeError`, JS 속성이면 빠진다. **순환** — 파이썬 `ValueError 「Circular reference detected」`, JS `TypeError` + 경로.
- ★★ **`default=` 는 한 번, `set` 에만** 불렸다(`['set']`). JS `replacer` 는 **모든 키에** 불린다(3번 `[1]` 의 일곱 줄).
- ★★ 파이썬이 쓴 `NaN` 을 JS `JSON.parse` 는 **`SyntaxError`** 로 거절한다(4번 `[4]` 의 `"NaN"` 줄).
- ★ `{1: 'a', '1': 'b'}` 는 **키가 두 번 나오는 JSON** 이 되고, JS 는 **뒤의 `"b"`** 를 남긴다(4번 `[4]` 마지막 줄의 규칙).

### 10. JSON 왕복은 27번 네 도구와 달리 **얕지 않다 — 대신 다시 만든다** · `"__proto__"` 는 파싱에서는 데이터, 대입에서는 프로토타입 ★★

- ★★★ 27번 격자의 `inner is the same object` 행에서 앞의 셋은 `y`(얕다), `structuredClone` 은 `n` 이었다. JSON 왕복도 **`n`** 이다 — 5번의 `same object twice → two objects` 처럼 **참조를 끊고 새로 만든다.** 대신 5번 격자의 손실을 전부 치른다.
- ★★ 4번 `[3]` 의 `JSON.parse` 결과는 `"__proto__"` 를 **own 키**로 갖는다. 27번 `[4]` 는 **바로 그 결과**를 `Object.assign` 에 넣었고 그때 **프로토타입이 바뀌었다** — 대입이 `__proto__` setter 를 부르기 때문이다.
- ★★ 23번의 우회로 — **`JSON.stringify([...map])`**(항목 배열)와 **`Object.fromEntries(map)`**(글자 키 객체).
- ★ 22번 표의 `JSON.stringify(x)` 줄은 **`(no call)` · `"{}"`** — `stringify` 는 `Symbol.toPrimitive` 를 안 부른다.

### 11. `structuredClone` 은 **HTML 표준(호스트)** · 깊은 복사는 **48번** · 원문 접근은 **ES2026 이고 Chrome 151 에만** 있다 ★★

- ★★ `structuredClone` 은 ECMA-262 가 아니라 **HTML 표준**의 API 다. 실패는 **`DOMException`(이름 `DataCloneError`)**.
- ★★ 깊은 복사 수단 비교는 목록의 **48번 주제**가 정본이다.
- ★★★ JSON.parse source text access 는 TC39 finished proposals 에서 **2026** 이다(ES2026). 판별 블록에서 **node 18 · node 20 은 `no`, Chrome 151 은 `yes`**.
- ★ JSON 모듈은 목록의 **44번 주제**(동적 `import`·import attributes)의 몫이다.

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js28b-31a-type-grid.js` | ★★★ 값 14 × 자리 3 격자 · 「갈린 행 3 / 14」 · 구멍 · 키 종류 | node20 1벌 + node18 대조 1벌 |
| `js28b-31b-throws.js` | ★★★ 순환 참조 네 경우의 **여러 줄 메시지** · 공유 · `BigInt` · `replacer` 로 끊기 | node20 1벌 + node18 대조 1벌 |
| `js28b-31c-tojson-replacer.js` | ★★★ `toJSON` → `replacer` 로그 · `this` · `undefined` 반환 · 허용 목록 · `space` 상한 | node20 1벌 + node18 대조 1벌 |
| `js28b-31d-parse-reviver.js` | ★★★ `reviver` 후위 순서 · 삭제 · `"__proto__"` · 문법 가장자리(★ **문구가 두 판에서 갈림**) | node20 1벌 + **node18 1벌(따로 실음)** |
| `js28b-31e-deep-copy.js` | ★★★ JSON 왕복 × `structuredClone` 격자 · 「갈린 행 11 / 13」 · 두 예외 | node20 1벌 + node18 대조 1벌 |
| `js28b-31x-node-rawjson.js` | ES2026 원문 접근이 node 에 있나 | node20 1벌 + node18 대조 1벌 |
| `js28b-31f-rawjson.web.js` | ★★ `context.source` · `JSON.rawJSON` | **Chrome 151 만** |
| `js28b-31g-python-contrast.sh` · `js28b-31-h-pyjson.py` | 파이썬 `json` 대비 | python3 3.12.3 1벌 |
| `js28b-vdiff.sh` · `js28b-versions.sh` | 두 판이 갈린 탐침 수 · 이 문서의 출력이 **어느 판에서 나왔나** + 판별 기능 표 | 1벌씩 |

두 node 판 대조기(이 배치 전체의 node 탐침). 이 주제의 줄(`js28b-31…`) 가운데 `DIFFERS` 는 `js28b-31d-parse-reviver.js` 하나다. 그 밖의 `DIFFERS` 줄은 **다른 주제의 탐침**이다(같은 배치가 한 대조기를 공유한다).

```sh
# js28b-vdiff.sh
#!/usr/bin/env bash
# 두 node 판이 갈린 탐침이 몇 개인가 -- 스크립트가 직접 센다(브라우저 탐침 *.web.js 와 셸 탐침 *.sh 는 대상이 아니다).
set -u -o pipefail
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
cd "$(dirname "$0")"
same=0; diffn=0
for f in js28b-2[89]?-*.js js28b-3[01]?-*.js; do
  [ -e "$f" ] || continue
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
===== ./js28b-vdiff.sh (exit=0) =====
js28b-28a-dollar-grid.js                     identical
js28b-28b-replace-all.js                     identical
js28b-28c-tagged.js                          identical
js28b-28d-slice-substring.js                 DIFFERS
    26c26
    <   slice(0, 2)  code units 61 d83d   isWellFormed (no method)
    ---
    >   slice(0, 2)  code units 61 d83d   isWellFormed false
js28b-28e-split.js                           identical
js28b-28f-pad-trim-search.js                 identical
js28b-29a-lastindex.js                       identical
js28b-29b-match-shape.js                     identical
js28b-29c-matchall.js                        identical
js28b-29d-replace-callback.js                identical
js28b-29e-literal-identity.js                identical
js28b-29f-flags.js                           DIFFERS
    9c9
    <   new RegExp('a', 'v')                SyntaxError 「Invalid flags supplied to RegExp constructor 'v'」
    ---
    >   new RegExp('a', 'v')                v   unicodeSets
js28b-29h-literal-vs-constructor.js          identical
js28b-30a-groups.js                          DIFFERS
    35c35
    <   new RegExp('\\k<z>', 'u')                     SyntaxError 「Invalid regular expression: /\k<z>/: Invalid named capture referenced」
    ---
    >   new RegExp('\\k<z>', 'u')                     SyntaxError 「Invalid regular expression: /\k<z>/u: Invalid named capture referenced」
js28b-30b-lookaround.js                      identical
js28b-30c-unicode.js                         DIFFERS
    5,11c5,11
    <   ^.$ on face                                 -:false  u:true  v:SyntaxError
    <   ^..$ on face                                -:true  u:false  v:SyntaxError
    <   ^[face]$ on face                            -:false  u:true  v:SyntaxError
    <   ^face{2}$ on face+face                      -:false  u:true  v:SyntaxError
    <   ^\S$ on face                                -:false  u:true  v:SyntaxError
    <   high half alone, on face                    -:true  u:false  v:SyntaxError
    <   ^.$ on the high half alone                  -:true  u:true  v:SyntaxError
    ---
    >   ^.$ on face                                 -:false  u:true  v:true
    >   ^..$ on face                                -:true  u:false  v:false
    >   ^[face]$ on face                            -:false  u:true  v:true
    >   ^face{2}$ on face+face                      -:false  u:true  v:true
    >   ^\S$ on face                                -:false  u:true  v:true
    >   high half alone, on face                    -:true  u:false  v:false
    >   ^.$ on the high half alone                  -:true  u:true  v:true
    32c32
    <   new RegExp('\\p{Nope}', 'u')                SyntaxError 「Invalid regular expression: /\p{Nope}/: Invalid property name」
    ---
    >   new RegExp('\\p{Nope}', 'u')                SyntaxError 「Invalid regular expression: /\p{Nope}/u: Invalid property name」
js28b-30d-vflag.js                           DIFFERS
    2,5c2,5
    <   ^[\p{L}--\p{ASCII}]$  v                       SyntaxError 「Invalid flags supplied to RegExp constructor 'v'」
    <   ^[\p{L}&&\p{ASCII}]$  v                       SyntaxError 「Invalid flags supplied to RegExp constructor 'v'」
    <   ^[\p{L}--\p{ASCII}]$  u                       SyntaxError 「Invalid regular expression: /^[\p{L}--\p{ASCII}]$/: Invalid character class」
    <   ^[[a-z]--[aeiou]]+$  v   on 'rhythm' / 'rain' SyntaxError 「Invalid flags supplied to RegExp constructor 'v'」
    ---
    >   ^[\p{L}--\p{ASCII}]$  v                       false true true false
    >   ^[\p{L}&&\p{ASCII}]$  v                       true false false false
    >   ^[\p{L}--\p{ASCII}]$  u                       SyntaxError 「Invalid regular expression: /^[\p{L}--\p{ASCII}]$/u: Invalid character class」
    >   ^[[a-z]--[aeiou]]+$  v   on 'rhythm' / 'rain' true false
    8c8
    <   ^\p{RGI_Emoji}$  v   on family / face         SyntaxError 「Invalid flags supplied to RegExp constructor 'v'」
    ---
    >   ^\p{RGI_Emoji}$  v   on family / face         true true
    10,12c10,12
    <   ^\p{RGI_Emoji}$  u                            SyntaxError 「Invalid regular expression: /^\p{RGI_Emoji}$/: Invalid property name」
    <   ^[\q{abc|d}]$    v   on 'abc' / 'd' / 'a'     SyntaxError 「Invalid flags supplied to RegExp constructor 'v'」
    <   family.match(v)[0]  for [\p{RGI_Emoji}]       SyntaxError 「Invalid flags supplied to RegExp constructor 'v'」
    ---
    >   ^\p{RGI_Emoji}$  u                            SyntaxError 「Invalid regular expression: /^\p{RGI_Emoji}$/u: Invalid property name」
    >   ^[\q{abc|d}]$    v   on 'abc' / 'd' / 'a'     true true false
    >   family.match(v)[0]  for [\p{RGI_Emoji}]       [d83d dc68 200d d83d dc69 200d d83d dc67]
    19,21c19,21
    <   [\-]                                          u:ok  v:SyntaxError
    <   sources accepted under u but not under v: 5 / 5
    <   new RegExp('[(]', 'v') -- message             SyntaxError 「Invalid flags supplied to RegExp constructor 'v'」
    ---
    >   [\-]                                          u:ok  v:ok
    >   sources accepted under u but not under v: 4 / 5
    >   new RegExp('[(]', 'v') -- message             SyntaxError 「Invalid regular expression: /[(]/v: Invalid character in character class」
    25,26c25,26
    <   new RegExp('a', 'v').unicodeSets / .unicode   SyntaxError 「Invalid flags supplied to RegExp constructor 'v'」
    <   new RegExp('a', 'v').flags                    SyntaxError 「Invalid flags supplied to RegExp constructor 'v'」
    ---
    >   new RegExp('a', 'v').unicodeSets / .unicode   true / false
    >   new RegExp('a', 'v').flags                    v
js28b-30e-indices.js                         identical
js28b-30g-es2025-node.js                     identical
js28b-31a-type-grid.js                       identical
js28b-31b-throws.js                          identical
js28b-31c-tojson-replacer.js                 identical
js28b-31d-parse-reviver.js                   DIFFERS
    23,28c23,28
    <   "{'a': 1}"        -> SyntaxError 「Unexpected token ' in JSON at position 1」
    <   "{\"a\": 1,}"     -> SyntaxError 「Unexpected token } in JSON at position 8」
    <   "[1, 2,]"         -> SyntaxError 「Unexpected token ] in JSON at position 6」
    <   "{a: 1}"          -> SyntaxError 「Unexpected token a in JSON at position 1」
    <   "NaN"             -> SyntaxError 「Unexpected token N in JSON at position 0」
    <   "undefined"       -> SyntaxError 「Unexpected token u in JSON at position 0」
    ---
    >   "{'a': 1}"        -> SyntaxError 「Expected property name or '}' in JSON at position 1」
    >   "{\"a\": 1,}"     -> SyntaxError 「Expected double-quoted property name in JSON at position 8」
    >   "[1, 2,]"         -> SyntaxError 「Unexpected token ']', "[1, 2,]" is not valid JSON」
    >   "{a: 1}"          -> SyntaxError 「Expected property name or '}' in JSON at position 1」
    >   "NaN"             -> SyntaxError 「"NaN" is not valid JSON」
    >   "undefined"       -> SyntaxError 「"undefined" is not valid JSON」
js28b-31e-deep-copy.js                       identical
js28b-31x-node-rawjson.js                    identical

identical 19  ·  differs 6  ·  total 25
```

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- ★★ `JSON.parse` 의 **실패 문구**(이미 node18 → node20 에서 바뀌었다) · 순환 참조 메시지의 **경로 그림**.
- ★★ ES2026 원문 접근 — node 가 올라가면 `js28b-31x-node-rawjson.js` 가 `function` 을 답할 것이다. 그때 `js28b-31f-rawjson.web.js` 를 node 로도 돌린다.
- ★ `structuredClone` 의 `DOMException` 문구 — 호스트의 것이다.
