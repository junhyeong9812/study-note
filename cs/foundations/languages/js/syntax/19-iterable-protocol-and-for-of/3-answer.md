# js/syntax/19 — 이터러블 프로토콜과 `for...of`: 「소비자는 전부 같은 계약을 부르고, 다 못 읽으면 `return()` 으로 닫는다」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **node v20.19.6**(기본 판) · **node v18.19.1**(대조) · x86-64 Linux 에서 실제로 돌려 얻은 것이고,
> 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 하나도 없다). 브라우저는 **안 돌렸다.**
>
> ★★ **예외는 `e.constructor.name` 과 `e.message` 로만 찍었다** — 스택트레이스에는 절대 경로가 박혀 재현이 안 된다.
> ★★★ **이 주제는 두 판이 갈린 블록을 하나 갖고 있다**(`js16b-19c-errors.js`) — 9번 답에 v18 판을 나란히 싣는다.
> ★ **표준 출력과 표준 오류를 한 블록에도 안 섞었다.**
>
> **이 파일이 인용하는 출력을 낸 소스** — 전문은 [1-question.md](1-question.md) 의 같은 번호 문항에 있다.
> `js16b-19a-protocol-log.js`(1번) · `js16b-19b-make-your-own.js`(2번) · `js16b-19c-errors.js`(3번 · 9번) · `js16b-19d-strings-maps.js`(4번) · `js16b-19f-close-and-helpers.js`(5번) · `js16b-vdiff.sh`(9번).

## 정답

### 1. 소비자 17가지 — **끝까지 읽으면 `next` 는 값+1 번 · `return()` 은 `done` 을 못 본 채 멈출 때만** ★★★

**출력**

```text
===== node20 js16b-19a-protocol-log.js (exit=0) =====
[1] consumers that read to the end
for (const x of it) {}
    get @@iterator | @@iterator() | next#1 -> 10 | next#2 -> 20 | next#3 -> 30 | next#4 done
[...it]
    get @@iterator | @@iterator() | next#1 -> 10 | next#2 -> 20 | next#3 -> 30 | next#4 done   [result [10,20,30]]
Array.from(it)
    get @@iterator | @@iterator() | next#1 -> 10 | next#2 -> 20 | next#3 -> 30 | next#4 done   [result [10,20,30]]
new Set(it)
    get @@iterator | @@iterator() | next#1 -> 10 | next#2 -> 20 | next#3 -> 30 | next#4 done   [result [10,20,30]]
const [a, ...rest] = it
    get @@iterator | @@iterator() | next#1 -> 10 | next#2 -> 20 | next#3 -> 30 | next#4 done   [result [10,[20,30]]]
Math.max(...it)
    get @@iterator | @@iterator() | next#1 -> 10 | next#2 -> 20 | next#3 -> 30 | next#4 done   [result 30]

[2] consumers that stop early
for-of with break at 20
    get @@iterator | @@iterator() | next#1 -> 10 | next#2 -> 20 | return()
for-of with return at 20
    get @@iterator | @@iterator() | next#1 -> 10 | next#2 -> 20 | return()   [result 20]
for-of whose body throws at 20
    get @@iterator | @@iterator() | next#1 -> 10 | next#2 -> 20 | return()   [caught Error body threw]
labelled continue outer, from inside
    get @@iterator | @@iterator() | next#1 -> 10 | return()
const [a] = it
    get @@iterator | @@iterator() | next#1 -> 10 | return()   [result 10]
const [a, b, c] = it  (exactly 3)
    get @@iterator | @@iterator() | next#1 -> 10 | next#2 -> 20 | next#3 -> 30 | return()   [result [10,20,30]]
const [a, b, c, d] = it  (one more)
    get @@iterator | @@iterator() | next#1 -> 10 | next#2 -> 20 | next#3 -> 30 | next#4 done   [result [10,20,30,"<undefined>"]]
Array.from(it, mapFn throws at 20)
    get @@iterator | @@iterator() | next#1 -> 10 | next#2 -> 20 | return()   [caught Error map threw]
new Map(it)  (10 is not an entry)
    get @@iterator | @@iterator() | next#1 -> 10 | return()   [caught TypeError Iterator value 10 is not an entry object]

[3] when next() itself throws
for-of, next#2 throws
    get @@iterator | @@iterator() | next#1 -> 10 | next#2 throws   [caught Error next failed]
[...it], next#2 throws
    get @@iterator | @@iterator() | next#1 -> 10 | next#2 throws   [caught Error next failed]

[4] Promise.all -- when does it read the iterable?
Promise.all(it)   right after the call:  get @@iterator | @@iterator() | next#1 -> 10 | next#2 -> 20 | next#3 -> 30 | next#4 done
                  resolved with [10,20,30]

[5] summary  (label / next calls / return calls)
  for (const x of it) {}                   4  0
  [...it]                                  4  0
  Array.from(it)                           4  0
  new Set(it)                              4  0
  const [a, ...rest] = it                  4  0
  Math.max(...it)                          4  0
  for-of with break at 20                  2  1
  for-of with return at 20                 2  1
  for-of whose body throws at 20           2  1
  labelled continue outer, from inside     1  1
  const [a] = it                           1  1
  const [a, b, c] = it  (exactly 3)        3  1
  const [a, b, c, d] = it  (one more)      4  0
  Array.from(it, mapFn throws at 20)       2  1
  new Map(it)  (10 is not an entry)        1  1
  for-of, next#2 throws                    2  0
  [...it], next#2 throws                   2  0
return() was called in 8 of 17 probes
```

**왜 그런가**

- ★★★ **`[1]` 여섯 소비자의 로그가 한 글자도 같다** — `get @@iterator | @@iterator() | next#1 … next#4 done`, `return()` 없음.
  **`for...of`·스프레드·`Array.from`·`new Set`·`[a, ...rest]`·호출 스프레드가 같은 프로토콜**이라는 것이 이 여섯 줄이다.
  ★★ **`next` 가 넷인 것은 값 셋 + 끝 확인 하나**다. 11번의 `[...tracedIterable(2)]` 가 `next 0, next 1, next 2` 로 **값 둘에 셋**이었던 것과 같다.
  ★ **`get @@iterator` 는 소비자당 한 번**이다 — 메서드를 한 번 읽고 한 번 부른 뒤 다시 안 읽는다.
- ★★★ **`[2]` `return()` 이 불린 줄은 전부 「`done` 을 못 받고 멈춘 줄」이다.**
  `break`·`return`·몸통 `throw` 는 `next#2 -> 20 | return()`, 바깥 `continue outer` 와 `[a]` 는 `next#1 -> 10 | return()` 이다.
- ★★★ **`const [a, b, c] = it` 은 `next#3 -> 30 | return()`** — 값이 **딱 셋인데도 닫는다.**
  **`const [a, b, c, d] = it` 은 `next#4 done` 까지 가고 `return()` 이 없다** — `d` 는 `<undefined>` 다.
  **패턴이 하나 길어져서 `done` 을 직접 받자 닫을 이유가 없어졌다.** 이유는 6번에서.
- ★★ **`Array.from(it, mapFn)` 은 `mapFn` 이 던지자 `return()` 을 부르고 `Error map threw` 를 올린다.**
  **`new Map(it)` 은 `10` 에서 `TypeError Iterator value 10 is not an entry object` 로 막히며 역시 `return()` 을 부른다.**
  ★ 둘 다 **이터레이터는 멀쩡한데 소비자 쪽이 실패한** 경우라 닫아 준다.
- ★★★ **`[3]` `next()` 가 스스로 던지면 `return()` 이 없다** — `for...of` 도 스프레드도 `next#2 throws` 에서 끝이다. 이유는 7번에서.
- ★★★ **`[4]` `Promise.all(it)` 이 돌아온 바로 다음 줄에 로그가 이미 `next#4 done` 까지 다 차 있다.**
  `then` 이 돌기 전이다 — **이터러블은 호출 안에서 동기로 다 읽힌다.** 결과는 나중에 `[10,20,30]` 으로 풀린다.
- ★★ **`[5]` 요약 표는 두 칸으로 전부를 말한다** — `return` 칸이 1 인 줄과 0 인 줄이 **「`done` 을 봤나 · `next` 가 던졌나」로 정확히 갈린다.**
  마지막 줄의 집계는 **스크립트가 센 것**이다.

### 2. 두 번 펴면 — **이터러블은 같은 것을 또 주고, 자기 자신을 돌려주는 이터레이터는 두 번째가 `[]`** ★★★

**출력**

```text
===== node20 js16b-19b-make-your-own.js (exit=0) =====
[1] a class with [Symbol.iterator]()
[...cd]  first time                           [3,2,1]
[...cd]  second time                          [3,2,1]

[2] an iterator whose [Symbol.iterator]() returns itself
[...once]  first time                         [3,2,1]
[...once]  second time                        []

[3] generators and built-in iterators
g[Symbol.iterator]() === g                    true
[...g] then [...g]                            [1,2] then []
arrayIterator[Symbol.iterator]() === itself   true
[...ai] then [...ai]                          [1,2] then []
[...m.keys()] twice from ONE keys() call      ["k"] then []
gen[Symbol.iterator]  (the function itself)   undefined

[4] the value that comes with done: true
[...withReturn()]                             ["a"]
for-of withReturn()                           ["a"]
manual next() x2                              {"value":"a","done":false} {"value":"the return value","done":true}

[5] a result object without `done`
[...noDone]                                   [1,2,3]
```

**왜 그런가**

- ★★★ **`[1]` `Countdown` 은 두 번 다 `[3,2,1]`** 이다. `[Symbol.iterator]()` 가 **부를 때마다 새 이터레이터**를 만들고, 상태 `n` 이 그 안에 있다.
- ★★★ **`[2]` `return this` 를 단 이터레이터는 두 번째가 `[]`** 다. 두 번째 스프레드도 `Symbol.iterator` 를 부르지만 **이미 `done` 인 같은 객체**를 돌려받는다.
  **에러가 아니라 빈 결과**라서 조용히 틀린다.
- ★★★ **`[3]` 제너레이터 객체 · 배열 이터레이터 · `m.keys()` 가 전부 두 번째 부류**다 — `=== itself` 가 `true` 이고 두 번째가 `[]`.
  ★ **`typeof gen[Symbol.iterator]` 는 `undefined`** — 제너레이터 **함수**는 이터러블이 아니고, **불러서 나온 객체**가 이터러블이다.
- ★★★ **`[4]` `"the return value"` 는 수동 `next()` 줄에만 보인다** — `{"value":"the return value","done":true}`.
  스프레드와 `for...of` 는 `["a"]` 뿐이다. 이유는 8번에서.
- ★★ **`[5]` `done` 이 없는 결과 셋이 `[1,2,3]` 으로 모였다** — `done` 이 없으면 **안 끝난 것**으로 읽는다.

### 3. 이터러블이 아닌 것 — **종류는 `TypeError` 하나, 문구는 자리마다 다르고, 유사 배열에 대체 경로는 없다** ★★★

**출력**

```text
===== node20 js16b-19c-errors.js (exit=0) =====
[1] a plain object in six places
for (const v of plain)                      -> TypeError plain is not iterable
[...plain]                                  -> TypeError plain is not iterable
id(...plain)                                -> TypeError Spread syntax requires ...iterable[Symbol.iterator] to be a function
const [v] = plain                           -> TypeError plain is not iterable
new Set(plain)                              -> TypeError object is not iterable (cannot read property Symbol(Symbol.iterator))
Array.from(plain)                           -> []

[2] an array-like { length: 2, 0: 'x', 1: 'y' } -- is there a fallback?
for (const v of arrayLike)                  -> TypeError arrayLike is not iterable
[...arrayLike]                              -> TypeError arrayLike is not iterable
Array.from(arrayLike)                       -> ["x","y"]
Array.prototype.slice.call(arrayLike)       -> ["x","y"]
id.apply(null, arrayLike)                   -> ["x","y"]
after borrowing Array's @@iterator: [...]   -> ["x","y"]

[3] null and undefined
for (const v of null)                       -> TypeError null is not iterable
for (const v of undefined)                  -> TypeError undefined is not iterable
[...undefined]                              -> TypeError undefined is not iterable

[4] a broken protocol -- each step checks its own contract
@@iterator is not a function                -> TypeError {(intermediate value)} is not iterable
@@iterator returns a primitive              -> TypeError Result of the Symbol.iterator method is not an object
next() returns a primitive                  -> TypeError Iterator result 1 is not an object
iterator has no next                        -> TypeError {(intermediate value)} is not iterable
return() returns a primitive (on break)     -> TypeError Iterator result 1 is not an object
```

**왜 그런가**

- ★★★ **`[1]` 여섯 줄 중 다섯이 터지고 `Array.from(plain)` 만 `[]`** 다.
  터지는 다섯의 문구는 **세 가지** — `plain is not iterable`(`for...of`·배열 스프레드·배열 구조 분해) ·
  `Spread syntax requires ...iterable[Symbol.iterator] to be a function`(호출 스프레드) ·
  `object is not iterable (cannot read property Symbol(Symbol.iterator))`(`new Set`).
  ★★ `Array.from` 은 **이터러블이 아니면 유사 배열 문으로 들어가는** 두 문짜리라(11번) 에러 대신 빈 배열이다.
- ★★★ **`[2]` 유사 배열에 `for...of` 와 스프레드는 `TypeError`**, `Array.from`·`slice.call`·`apply` 는 `["x","y"]` 다.
  **인덱스와 `length` 가 다 있어도 `for...of` 는 그것으로 돌지 않는다.**
  ★★★ **`Array.prototype[Symbol.iterator]` 를 빌려 붙이자 스프레드가 `["x","y"]`** — 이터러블 여부는 **그 프로퍼티 하나**가 정한다.
- ★★ **`[3]` `for (const v of null)` 은 `TypeError null is not iterable`** 이다. `undefined` 도 같은 꼴이다 — 11번의 `[...null]` 과 같은 문구 모양이다.
- ★★ **`[4]` 같은 문구가 두 번 나오는 쌍이 둘이다** —
  ① **`@@iterator is not a function` 과 `iterator has no next`** 가 둘 다 `{(intermediate value)} is not iterable`.
  ② **`next() returns a primitive` 와 `return() returns a primitive (on break)`** 가 둘 다 `Iterator result 1 is not an object`.
  ★★★ **①은 관찰로만 적는다** — `next` 가 없는 것은 「이터러블이 아니다」가 아니라 「이터레이터가 틀렸다」인데, **V8 이 앞쪽 문구로 보고한다.**
  ★ `Symbol.iterator` 가 원시값을 돌려준 경우만 **자기 문구**(`Result of the Symbol.iterator method is not an object`)를 가진다.

### 4. 문자열과 `Map` — **`length` 4 대 `[...s].length` 3 · `Map` 은 넣은 순서 그대로** ★★

**출력**

```text
===== node20 js16b-19d-strings-maps.js (exit=0) =====
[1] a string with one astral character (built from a code point, so this file stays ASCII)
s.length  (UTF-16 code units)               4
[...s].length  (for-of units)               3
[...s] as code points                       ["61","1F600","62"]
s.split('') as code units                   ["61","D83D","DE00","62"]
for (let i...) s[i].length each             [1,1,1,1]
for (const ch of s) ch.length each          [1,2,1]

[2] Map and Set order, with integer-like keys
[...map.keys()]                             ["b",2,"a",1]
Object.keys(same keys as an object)         ["1","2","b","a"]
after delete b, set b  -> keys              [2,"a",1,"b"]
after set(2, ...) again -> keys             [2,"a",1,"b"]
[...set]                                    ["z",3,"y",1]

[3] changing a Map / Set / Array during for-of
add 3 at 1, delete 1 at 2                   visited [1,2,3]   final [2,3]
Map: delete b at a                          visited ["a"]
Array: push 3 at 1                          visited [1,2,3]
```

**왜 그런가**

- ★★★ **`s.length` 는 4, `[...s].length` 는 3** 이다. 가운데 글자가 **코드 유닛 둘**(`D83D`·`DE00`)이고 **코드 포인트 하나**(`1F600`)다.
  인덱스 `for` 는 조각을 **넷**(`[1,1,1,1]`), `for...of` 는 **셋**(`[1,2,1]`)으로 준다 — **문자열 이터레이터가 서로게이트 쌍을 합친다.**
  ★ 쌍 자체의 이야기는 [04번](../04-strings-and-utf16/2-summary.md)이 정본이다.
- ★★★ **`[...map.keys()]` 는 `["b",2,"a",1]`, 같은 키의 `Object.keys` 는 `["1","2","b","a"]`** — **순서가 다르다.**
  정수 같은 키를 앞세우는 것은 **객체의 규칙**(13번)이고 `Map` 은 **삽입 순서**다. `Set` 도 `["z",3,"y",1]`.
- ★★ **지웠다 다시 넣은 `b` 는 맨 뒤**(`[2,"a",1,"b"]`), **이미 있는 `2` 에 `set` 은 자리 유지**다.
- ★★★ **`[3]` 도는 중에 `Set` 에 넣은 `3` 은 방문되고, `Map` 에서 지운 `b` 는 방문되지 않는다.** 배열에 `push` 한 `3` 도 방문된다.
  명세의 keyed collections note 가 `Set` 에 대해 "New values added after the call to forEach begins are visited." 라고 적는다 — 이 블록은 같은 결과를 `for...of` 로 찍었다.

### 5. `return()` 의 계약 — **없어도 되고, 있으면 함수여야 하고, 몸통의 예외가 이긴다** ★★

**출력**

```text
===== node20 js16b-19f-close-and-helpers.js (exit=0) =====
[1] what return() may be -- on a break
no return at all                                -> ok
return: 1  (not callable)                       -> TypeError number 1 is not a function
return() throws                                 -> Error from return

[2] when the body already threw, whose error wins?
body throws, return() throws too                -> Error from body
body throws, return() gives a primitive         -> Error from body

[3] the value that comes with done: true -- three more consumers
Array.from(withReturn())                        -> ["a"]
const [x, y] = withReturn()                     -> ["a","<undefined>"]
new Set(withReturn()).size                      -> 1

[4] iterator helpers (ES2025) -- present in this node?
typeof globalThis.Iterator                      -> undefined
typeof [].values().map                          -> undefined
typeof [].values().toArray                      -> undefined

[5] arguments -- array-like; is it also iterable?
typeof arguments[Symbol.iterator]               -> function
[...arguments]  (called with 1, 2)              -> [1,2]

[6] an endless iterator -- does const [a] stop after one value?
const [a] = endless                             -> {"a":1,"nexts":1,"closes":1}

[7] e followed by a combining mark (U+0301)
e + U+0301  .length / [...].length              -> 2 / 2
```

**왜 그런가**

- ★★★ **`[1]` `return` 이 없으면 `ok`** — 아무것도 안 올라온다. `IteratorClose` 가 "If return is undefined, return ? completion." 이다.
  **`return: 1` 은 `TypeError number 1 is not a function`**, **`return()` 이 던지면 `Error from return`** 이 `break` 자리에서 올라온다.
- ★★★ **`[2]` 몸통이 먼저 던졌으면 두 줄 다 `Error from body`** — `return()` 이 던져도, 원시값을 줘도 **몸통이 이긴다.**
  `IteratorClose` 의 "If completion is a throw completion, return ? completion." 이 **결과 검사보다 앞에** 있기 때문이다.
  ★ 3번 답 `[4]` 의 마지막 줄 — `break`(정상 완료)일 때 원시값을 주면 `TypeError` — 과 짝이다.
- ★★ **`[3]` 세 소비자 누구도 `"R"` 을 안 본다** — `["a"]` · `["a","<undefined>"]` · 크기 `1`.
- ★★ **`[4]` 이터레이터 헬퍼는 두 판 모두 없다** — 셋 다 `undefined`. 이 블록은 대조기에서 **identical** 이다.
- ★★ **`[5]` `arguments` 는 제 `Symbol.iterator` 를 가져 `[1,2]` 로 펴진다** — 유사 배열이라서가 아니라 **이터러블이기도 해서**다.
- ★★★ **`[6]` 끝없는 이터레이터에 `const [a]` 는 `next` 1 · `return` 1 로 멈춘다** — 패턴이 차면 더 안 읽고 닫는다.
- ★ **`[7]` 결합 문자를 붙인 `e` 는 두 길이가 다 2** — 코드 포인트 단위도 **사람이 보는 한 글자**와 다르다.

### 6. `[a, b, c]` 가 딱 맞아도 닫는 이유 — **넷째 `next` 를 안 불러서 「끝났는지 모른다」** ★★★

- ★★★ **셋째 값을 받은 순간 소비자는 「이 이터레이터가 끝났는지」 모른다.** 끝은 `done: true` 를 **받아야** 알고, 그것을 받으려면 `next` 를 한 번 더 불러야 한다.
  **패턴은 셋에서 멈추고 넷째를 안 부른다** — 그래서 「다 안 읽고 떠나는 손님」으로 분류되어 `return()` 을 부른다.
- ★★ **한 문장으로 — 「`done` 을 직접 받았으면 안 닫고, 못 받았으면 닫는다.」** `[a, b, c, d]` 는 넷째 `next` 에서 `done` 을 받았으니 안 닫는다.
  **값 개수가 아니라 「끝 신호를 봤나」가 기준**이다.
- ★ **그 규칙 덕에 끝없는 이터레이터에서도 `[a]` 가 멈춘다** — 5번 답 `[6]` 의 `{"a":1,"nexts":1,"closes":1}`.
  「그래서 그렇게 설계했다」는 **해석**이고, 로그가 보이는 것은 **멈춘다는 사실**까지다.
  ★ 배열 구조 분해 쪽 명세 문장은 **이번에 받아 둔 페이지 밖**이라 인용하지 않는다. 로그로만 섰다.

### 7. `next()` 가 던지면 안 닫는 이유 — **닫기는 멀쩡한 이터레이터에게 알리는 일이다** ★★★

- ★★★ **닫기(`IteratorClose`)는 「더 안 읽겠다」를 이터레이터에게 알려 정리할 기회를 주는 일**이다.
  **`next()` 가 던졌다는 것은 이터레이터 자신이 실패했다는 뜻**이라, 알릴 상대가 멀쩡하지 않다.
- ★★ **기호 하나 — `?` 다.** `for...of` 의 `ForIn/OfBodyEvaluation` 은 "Let nextResult be ? Call(iteratorRecord.[[NextMethod]], iteratorRecord.[[Iterator]])." 로 부르고,
  **`?` 는 예외를 그대로 위로 올린다.** `IteratorClose` 는 **몸통의 완료**를 받는 자리에만 걸려 있다.
  ★ 스프레드 쪽이 거치는 `IteratorNext` 는 throw 를 받으면 "Set iteratorRecord.[[Done]] to true." 로 그 이터레이터를 끝난 것으로 표시한다.
- ★★★ **새는 경로 — `next()` 안의 실패.** `return()` 에만 정리를 두면 그 경로에서 **정리가 안 된다.**
  **끝까지 읽은 경우**도 `return()` 이 안 불린다 — 그쪽은 `done` 을 주는 자리에서 정리해야 한다.

### 8. `done: true` 의 값을 버리는 이유 — **`done` 을 먼저 보고, 참이면 `value` 를 읽지 않는다** ★★

- ★★ **소비자는 `done` 을 먼저 읽는다.** `ForIn/OfBodyEvaluation` 이 "If done is true, return iterationResult." 로 멈추고,
  **그 다음 줄에서야** "Let nextValue be ? IteratorValue(nextResult)." 를 한다 — 끝이면 `value` 를 **읽지도 않는다.**
- ★★ **보려면 창을 바꿔 물어야 한다 — 수동 `next()`.** 2번 답 `[4]` 의 `{"value":"the return value","done":true}` 가 그 창에서만 나온다.
  ★ 이것이 이 주제의 **「창을 바꿔 물은」 자리**(제5의 상태)다 — 소비자 창은 전부 닫혀 있었다(5번 답 `[3]` 까지 다섯 소비자).
- ★ **`done` 이 없으면 끝이 아니다** — `IteratorComplete` 가 "Return ToBoolean(? Get(iteratorResult, "done"))." 라 `undefined` 는 `false` 다(2번 답 `[5]`).

### 9. 두 판이 갈린 줄 — **호출 스프레드 한 줄, 11번의 `f(...obj)` 와 같은 자리** ★★★

**출력**

```text
===== node18 js16b-19c-errors.js (exit=0) =====
[1] a plain object in six places
for (const v of plain)                      -> TypeError plain is not iterable
[...plain]                                  -> TypeError plain is not iterable
id(...plain)                                -> TypeError Found non-callable @@iterator
const [v] = plain                           -> TypeError plain is not iterable
new Set(plain)                              -> TypeError object is not iterable (cannot read property Symbol(Symbol.iterator))
Array.from(plain)                           -> []

[2] an array-like { length: 2, 0: 'x', 1: 'y' } -- is there a fallback?
for (const v of arrayLike)                  -> TypeError arrayLike is not iterable
[...arrayLike]                              -> TypeError arrayLike is not iterable
Array.from(arrayLike)                       -> ["x","y"]
Array.prototype.slice.call(arrayLike)       -> ["x","y"]
id.apply(null, arrayLike)                   -> ["x","y"]
after borrowing Array's @@iterator: [...]   -> ["x","y"]

[3] null and undefined
for (const v of null)                       -> TypeError null is not iterable
for (const v of undefined)                  -> TypeError undefined is not iterable
[...undefined]                              -> TypeError undefined is not iterable

[4] a broken protocol -- each step checks its own contract
@@iterator is not a function                -> TypeError {(intermediate value)} is not iterable
@@iterator returns a primitive              -> TypeError Result of the Symbol.iterator method is not an object
next() returns a primitive                  -> TypeError Iterator result 1 is not an object
iterator has no next                        -> TypeError {(intermediate value)} is not iterable
return() returns a primitive (on break)     -> TypeError Iterator result 1 is not an object
```

```text
===== ./js16b-vdiff.sh (exit=0) =====
js16b-16a-where.js               identical
js16b-16b-rules.js               identical
js16b-16c-order.js               identical
js16b-16d-define-vs-set.js       identical
js16b-16e-private.js             identical
js16b-16f-private-windows.js     identical
js16b-16g-forin.js               identical
js16b-17a-two-chains.js          identical
js16b-17b-super-call.js          identical
js16b-17c-homeobject.js          identical
js16b-17d-builtins.js            identical
js16b-17e-ctor-virtual.js        identical
js16b-17f-super-edges.js         identical
js16b-18a-grid.js                identical
js16b-18b-array.js               identical
js16b-18c-hasown.js              identical
js16b-18d-mutate.js              identical
js16b-18f-refimpl.js             identical
js16b-19a-protocol-log.js        identical
js16b-19b-make-your-own.js       identical
js16b-19c-errors.js              DIFFERS
    4c4
    < id(...plain)                                -> TypeError Found non-callable @@iterator
    ---
    > id(...plain)                                -> TypeError Spread syntax requires ...iterable[Symbol.iterator] to be a function
js16b-19d-strings-maps.js        identical
js16b-19f-close-and-helpers.js   identical

identical 22  ·  differs 1  ·  total 23
```

- ★★★ **갈린 줄은 `[1]` 의 넷째 `id(...plain)` 하나다.**
  v18 은 **`Found non-callable @@iterator`**, v20 은 **`Spread syntax requires ...iterable[Symbol.iterator] to be a function`** 이다.
- ★★★ **11번의 `f(...obj)` 가 갈린 것과 같은 자리, 같은 두 문구다.** 배열 자리 `[...plain]`·`for...of`·구조 분해는 **두 판 모두** `plain is not iterable` 이다.
- ★★ **값과 종류는 한 글자도 안 갈렸다.** 그래서 **근거로 쓰는 것은 `TypeError` 라는 종류와 호출 로그**이고, **문구는 근거로 쓰지 않는다.**
  ★ 대조기의 나머지 블록은 전부 `identical` 이다 — 집계 —

`identical 22  ·  differs 1  ·  total 23`

### 10. 파이썬 32번의 대체 경로 — **JS 의 `for...of` 에는 없다. 재 봤더니 없다** ★★★

- ★★★ **파이썬은 `__iter__` 가 없으면 `__getitem__` 으로 떨어져 0, 1, 2 … `IndexError` 까지 돈다** —
  Python 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **32번**이 그 사슬을 로그로 찍었다.
  ★★★ **JS 의 `for...of` 는 `Symbol.iterator` 가 없으면 바로 `TypeError`** 다 — 3번 답 `[2]` 의 `for (const v of arrayLike)` 줄.
- ★★ **「재 봤더니 없다」다** — 인덱스와 `length` 를 **다 갖춘 유사 배열로 실제로 물었다.** 「잴 것이 없다」(부적용)와 다르다.
- ★ **두 번째 문을 가진 것은 `Array.from`** 하나다(11번의 결론 · 3번 답 `[2]`).
  **끝 신호도 다르다** — 파이썬은 **`StopIteration` 예외**(같은 갈래 **16번**), JS 는 **`{ done: true }` 값**이다.
  그래서 JS 에서는 「`next()` 가 던졌다」가 「끝났다」와 **다른 사건**이고, 7번처럼 닫기 규칙도 갈린다.

### 11. `for...of null` 과 `for-in null` — **하나는 `TypeError`, 하나는 조용히 0회** ★★

- ★★ **`for (const v of null)` 은 `TypeError null is not iterable`**(3번 답 `[3]`),
  **[18번](../18-for-in-and-enumeration/2-summary.md)의 `for-in null` 은 `[]`** — 예외 없이 몸통이 한 번도 안 돈다.
- ★★ **가르는 곳은 `ForIn/OfHeadEvaluation` 한 곳**이다 — **enumerate(`for...in`)일 때만** `null`/`undefined` 를 break 완료로 바꾸고,
  iterate(`for...of`)는 `GetIterator` 로 가서 "If method is undefined, throw a TypeError exception." 에 걸린다.
- ★ **조용한 쪽이 더 위험하다** — `for...in` 은 값이 `null` 인 버그를 **0회 순회로 숨긴다.** `for...of` 는 그 자리에서 터져 알려 준다.

### 12. 경계 — **11번은 「어느 문이 이 프로토콜을 쓰나」, 여기는 「그 문 뒤에서 무엇이 불리나」** ★★

- **「세 자리의 문」**(`apply`·스프레드·`Array.from`) → [11번](../11-spread-and-rest/2-summary.md) ·
  **제너레이터의 `yield`/`next(값)` 흐름** → [목록의 **20번 주제**](../20-generators/) ·
  **이터레이터 헬퍼** → [목록의 **21번 주제**](../21-iterator-helpers/) ·
  **`for await...of`** → [목록의 **40번 주제**](../40-async-iteration-and-for-await/) ·
  **`Map` 의 키 비교(SameValueZero)** → [목록의 **23번 주제**](../23-map-set-and-weak-collections/).
- ★★★ **11번이 끝낸 것** — 배열·호출 자리는 이 프로토콜을, 객체 자리는 프로퍼티 복사를 부르고, `apply` 는 유사 배열만 연다.
  **이 주제가 시작하는 것** — 그 프로토콜이 **무엇을 몇 번 부르고, 언제 `return()` 으로 닫고, 어디서 깨지나.**
- ★ **이 주제가 끝까지 책임지는 것 셋** —
  ① **소비자 17가지의 호출 로그**와 `return()` 이 불리는 규칙(「`done` 을 못 보고 멈출 때만, `next()` 가 던지면 제외」)
  ② **이터러블과 이터레이터의 구분**(두 번 돌면 갈린다 · `it[Symbol.iterator]() === it`)
  ③ **이터러블이 아닐 때의 실패 지도**(자리마다 다른 문구 · 대체 경로의 부재 · `null` 앞의 `for...in` 대비).

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js16b-19a-protocol-log.js` | ★★★ **소비자 17가지의 호출 로그** · 조기 종료 전수 · `next()` 가 던질 때 · `Promise.all` 의 동기 읽기 · 요약 표 | node20 1벌 + node18 대조 1벌 |
| `js16b-19b-make-your-own.js` | ★★★ 이터러블 대 자기 자신을 돌려주는 이터레이터 · 내장 이터레이터 셋 · `done: true` 의 값 · `done` 없는 결과 | node20 1벌 + node18 대조 1벌 |
| `js16b-19c-errors.js` | ★★★ 여섯 자리의 문구 · 유사 배열 · `null`/`undefined` · 깨진 프로토콜 다섯 | node20 1벌 + **node18 판도 싣는다**(갈린 블록) |
| `js16b-19d-strings-maps.js` | ★★ 코드 포인트 대 코드 유닛 · `Map`/`Set` 삽입 순서 · 순회 중 변경 | node20 1벌 + node18 대조 1벌 |
| `js16b-19f-close-and-helpers.js` | ★★ `return()` 의 계약 · 누구의 예외가 이기나 · 소비자 셋의 `done` 값 · 헬퍼 유무 · `arguments` · 끝없는 이터레이터 · 결합 문자 | node20 1벌 + node18 대조 1벌 |
| `js16b-vdiff.sh` | **두 판이 갈린 블록 수** — 이 주제의 것은 `js16b-19c-errors.js` 하나 | 1벌 |
| `js16b-versions.sh` | 이 문서의 모든 출력이 **어느 판에서 나왔나** | 1벌 |

**구현 의존 항목** — 다음은 **이 환경(node 20.19.6 / 18.19.1 · x86-64 Linux)에서만** 그렇다.

- ★★★ **예외 문구 전부** — `plain is not iterable` · `Spread syntax requires ...iterable[Symbol.iterator] to be a function`(v20) · `Found non-callable @@iterator`(v18) ·
  `object is not iterable (cannot read property Symbol(Symbol.iterator))` · `{(intermediate value)} is not iterable` ·
  `Result of the Symbol.iterator method is not an object` · `Iterator result 1 is not an object` · `Iterator value 10 is not an entry object` · `number 1 is not a function`.
  **종류(`TypeError`)만 명세가 정한다.**
- ★★ **`next` 가 없는 이터레이터를 「이터러블이 아니다」 문구로 보고하는 것** — V8 의 표현이다.
- ★ **이터레이터 헬퍼가 없는 것** — 이 두 판의 사정이다(ES2025 이전에 나온 판).

**소비자가 `Symbol.iterator` 를 한 번 읽고 부른 뒤 `next()` 를 `done` 까지 반복하는 것 · `done` 을 못 보고 멈추면 `return()` 을 부르는 것 · `next()` 가 던지면 안 부르는 것 · `return` 이 없으면 그냥 끝나고 몸통의 throw 가 이기는 것 · `done` 이 참이면 `value` 를 안 읽는 것 · `for...of null` 이 `TypeError` 이고 `for...in null` 이 0회인 것 · `Map`/`Set` 이 삽입 순서인 것 · 문자열 이터레이터가 코드 포인트 단위인 것은 구현 의존이 아니다.**
어느 엔진에서도 같아야 한다.

**안 돌려 본 것 / 못 잰 것 / 부적용인 창**

- **안 돌려 본 것** —
  **브라우저**(이 배치는 Chrome 을 돌리지 않았다) · **DOM 컬렉션**이 이터러블인지 ·
  **엄격/비엄격 두 번 컴파일**(탐침은 전부 비엄격 한 벌) ·
  **`done` 을 영영 안 주는 이터레이터를 스프레드나 `Promise.all` 에 넘기기**(돌아오지 않을 것이라 일부러 안 돌렸다) ·
  **`next` 가 없는 이터레이터가 어느 시점에 던지나**(로그를 안 심었다) ·
  **빌려 붙인 배열 이터레이터가 유사 배열에서 무엇을 읽나**(로그를 안 심었다) ·
  다른 엔진(SpiderMonkey·JavaScriptCore)의 문구.
- ★ **못 잰 것** — **없다.**
- ★★★ **안 쟀다** — **성능 전부.** 「`for...of` 는 인덱스 `for` 보다 느리다」를 **한 줄도 쓰지 않았다.**
- ★★ **부적용인 창** — **③ 브랜드 태그**(이터러블 여부는 브랜드가 아니라 프로퍼티다 — 3번 답 `[2]` 의 빌려 붙이기) · **진단의 `(행,열)`**(`SyntaxError` 가 없다).
  **「잴 것이 없다」는 뜻**이다.
- ★★ **재 봤더니 없다** — 파이썬식 **`__getitem__` 대체 경로**(10번). 부적용과 **다르다.**
- ★★★ **창을 바꿔 물은 자리** — `done: true` 와 함께 온 값. 소비자 창이 전부 닫혀 **수동 `next()`** 로 바꿔 물었다(8번).

**판이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **예외 문구 전부** — 호출 스프레드는 **이 주제 안에서 실제로 바뀌었다**(9번).
- ★★ **이터레이터 헬퍼의 유무**(`js16b-19f-close-and-helpers.js` 의 `[4]`) — ES2025 를 들인 판에서는 답이 바뀐다. 그때는 [목록의 **21번 주제**](../21-iterator-helpers/)로 넘어간다.
- **프로토콜 자체(호출 순서 · `return()` 규칙 · 삽입 순서)는 다시 돌릴 필요가 없다** — ES2015 부터의 계약이다.
