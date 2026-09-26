# js/syntax/21 — 이터레이터 헬퍼: 「배열 메서드는 단계마다 전부 돌고, 헬퍼는 한 값씩 끝까지 흘려보낸다」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 출력은 **Google Chrome 151 헤드리스**(`.web.js` 탐침 — 배너가 `google-chrome --headless …`)와
> **node v20.19.6**(기본 판) · **node v18.19.1**(대조)에서 실제로 돌려 얻은 것이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 하나도 없다).
>
> ★★ **예외는 `이름 「메시지」` 꼴로만 찍었다** — 스택트레이스는 싣지 않는다.
> ★★★ **헬퍼가 node 두 판에 없어서 본체는 브라우저 한 판뿐이다** — 두 판 대조기는 이 주제의 node 탐침 **하나**(`js20b-21x-node-absent.js`)만 대조한다(10번).
> ★ **표준 출력과 표준 오류를 한 블록에도 안 섞었다.**
>
> **이 파일이 인용하는 출력을 낸 소스** — 전문은 [1-question.md](1-question.md) 의 같은 번호 문항에 있다.
> `js20b-21a-when.web.js`(1번) · `js20b-21b-grid.web.js`(2번) · `js20b-21g-close.web.js`(3번 · 9번) · `js20b-21f-consume.web.js`(4번) · `js20b-21h-args.web.js`(5번) ·
> `js20b-21e-from.web.js`(6번) · `js20b-21d-chain.web.js`(7번) · `js20b-21c-endless.web.js`(8번) · `js20b-21x-node-absent.js` · `js20b-vdiff.sh`(10번) · `js20b-21i-concat.web.js`(12번).

## 정답

### 1. 두 벌의 콜백 로그 — **배열판 `10 / 10` 이 단계별로 뭉치고, 헬퍼판 `4 / 4` 가 값마다 번갈아 간다** ★★★

**출력**

```text
===== google-chrome --headless --dump-dom 'js20b-page.html?js20b-21a-when.web.js' | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' | sed 's/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&amp;/\&/g' (exit=0) =====
[1] array methods: arr.map(f).filter(g).slice(0, 2)
    result [20,40]
    map calls 10 · filter calls 10
    order  map(1) map(2) map(3) map(4) map(5) map(6) map(7) map(8) map(9) map(10) filter(10) filter(20) filter(30) filter(40) filter(50) filter(60) filter(70) filter(80) filter(90) filter(100)

[2] iterator helpers: arr.values().map(f).filter(g).take(2)
    after building the pipeline:  log entries 0
    after toArray():  result [20,40]
    map calls 4 · filter calls 4
    order  map(1) filter(10) map(2) filter(20) map(3) filter(30) map(4) filter(40)

[3] the same helper pipeline, one next() at a time
    next#1  {"value":20,"done":false}    callbacks run in this call: map(1) filter(10) map(2) filter(20)
    next#2  {"value":40,"done":false}    callbacks run in this call: map(3) filter(30) map(4) filter(40)
    next#3  {"done":true}                callbacks run in this call: (none)

[4] counts side by side  (array / helper)
    map     10 / 4
    filter  10 / 4
    results equal: true
```

**왜 그런가**

- ★★★ **`[1]` 배열판은 `map` 열 번이 전부 끝난 뒤 `filter` 열 번**이다 — `map(1) … map(10) filter(10) … filter(100)`.
  `map` 은 **새 배열을 다 채워야** 돌려줄 수 있고, `filter` 는 그 배열을 받아서야 시작한다. `slice(0, 2)` 는 다 만든 것에서 자를 뿐이다.
- ★★★ **`[2]` 헬퍼판은 사슬을 만든 직후 `log entries 0`** — `map`·`filter`·`take` 는 **헬퍼 객체를 만들 뿐** 원본을 안 당긴다.
  `toArray()` 가 값을 달라고 하자 **`map(1) filter(10) map(2) filter(20) map(3) filter(30) map(4) filter(40)`** — 값 하나가 **`map` → `filter` 를 끝까지 지난 뒤** 다음 값이 온다.
- ★★★ **`[3]` `next#1` 이 `map(1) filter(10) map(2) filter(20)`** 을 한다 — 1 이 걸러져서 **통과할 값이 나올 때까지** 원본을 더 당겼다.
  **`next#3` 은 `(none)` 에 `{"done":true}`** — `take(2)` 가 **둘을 이미 냈으니 원본을 당기지 않고 끝낸다.** 그래서 `map(5)` 가 없다.
- ★ **`[4]` `results equal: true`** — 같은 결과를 다른 양의 일로 얻었다. ★ **시간·메모리는 재지 않았다.**

### 2. 격자 — **값은 `0 / 10`, 호출 수는 `5 / 10` 이 갈린다** ★★★

**출력**

```text
===== google-chrome --headless --dump-dom 'js20b-page.html?js20b-21b-grid.web.js' | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' | sed 's/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&amp;/\&/g' (exit=0) =====
pipeline                        array value     helper value    calls array / helper
map(x*2) then first 3           [2,4,6]         [2,4,6]         10 /  3   <- differs
filter(odd) then first 2        [1,3]           [1,3]           10 /  3   <- differs
skip 3, then map, first 2       [-4,-5]         [-4,-5]          7 /  2   <- differs
find(x > 3)                     4               4                4 /  4
some(x === 2)                   true            true             2 /  2
every(x < 4)                    false           false            4 /  4
map then find(x > 30)           40              40              14 /  8   <- differs
flatMap([x, x]) then first 3    [1,1,2]         [1,1,2]         10 /  2   <- differs
reduce(sum)                     55              55              10 / 10
map then reduce(sum)            110             110             20 / 20

value cells that differ 0 / 10
call-count cells that differ 5 / 10
```

**왜 그런가**

- ★★★ **값이 갈린 칸은 없다**(`value cells that differ 0 / 10`) — 두 판은 **같은 계산**이다.
- ★★★ **호출 수가 갈린 다섯 줄은 전부 「앞의 몇 개만」(`slice`/`take`/`find`) 이 앞 단계 뒤에 붙은 줄**이다 —
  `10 / 3` · `10 / 3` · `7 / 2` · `14 / 8` · `10 / 2`. 헬퍼판은 뒤의 「그만」이 **앞 단계까지** 올라가 멈춘다.
- ★★★ **안 갈린 다섯 줄은 두 부류**다.
  **한 단계짜리 `find`·`some`·`every`** — `4 / 4` · `2 / 2` · `4 / 4`. **배열의 이 셋도 답이 나오면 멈춘다** — 만들 중간 배열이 없어서 헬퍼가 줄일 것이 없다.
  **`reduce`** — `10 / 10` · `20 / 20`. **전부 봐야 답이 나오니** 어느 쪽이든 끝까지 간다.
- ★ `skip 3, then map, first 2` 의 배열판 `7` 은 `slice(3)` 이 콜백 없이 앞 셋을 버려서다.

### 3. 헬퍼·종단 열네 가지 — **`return()` 은 9 / 14. `done` 을 직접 받은 다섯 줄만 안 닫는다** ★★★

**출력**

```text
===== google-chrome --headless --dump-dom 'js20b-page.html?js20b-21g-close.web.js' | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' | sed 's/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&amp;/\&/g' (exit=0) =====
[1] helpers and terminals over a 5-value source
take(2).toArray()
    next#1 | next#2 | return()   [result [1,2]]
take(5).toArray()
    next#1 | next#2 | next#3 | next#4 | next#5 | return()   [result [1,2,3,4,5]]
take(9).toArray()
    next#1 | next#2 | next#3 | next#4 | next#5 | next#6 done   [result [1,2,3,4,5]]
drop(2).toArray()
    next#1 | next#2 | next#3 | next#4 | next#5 | next#6 done   [result [3,4,5]]
find(x => x === 2)
    next#1 | next#2 | return()   [result 2]
some(x => x === 2)
    next#1 | next#2 | return()   [result true]
every(x => x < 2)
    next#1 | next#2 | return()   [result false]
find(x => x === 99)
    next#1 | next#2 | next#3 | next#4 | next#5 | next#6 done   [result undefined]
forEach(x => {})
    next#1 | next#2 | next#3 | next#4 | next#5 | next#6 done   [result undefined]
reduce((s, x) => s + x)
    next#1 | next#2 | next#3 | next#4 | next#5 | next#6 done   [result 15]

[2] when a callback throws, or the consumer leaves
map(throws at 2).toArray()
    next#1 | next#2 | return()   [caught Error 「mapper threw」]
for (x of map(f)) break at 2
    next#1 | next#2 | return()   [result undefined]
const [a] = map(f)
    next#1 | return()   [result 1]
flatMap(x => [x, x]).take(3).toArray()
    next#1 | next#2 | return()   [result [1,1,2]]

[3] summary  (label / source next calls / source return calls)
  take(2).toArray()                        2  1
  take(5).toArray()                        5  1
  take(9).toArray()                        6  0
  drop(2).toArray()                        6  0
  find(x => x === 2)                       2  1
  some(x => x === 2)                       2  1
  every(x => x < 2)                        2  1
  find(x => x === 99)                      6  0
  forEach(x => {})                         6  0
  reduce((s, x) => s + x)                  6  0
  map(throws at 2).toArray()               2  1
  for (x of map(f)) break at 2             2  1
  const [a] = map(f)                       1  1
  flatMap(x => [x, x]).take(3).toArray()   2  1
return() was called in 9 of 14 probes
```

**왜 그런가**

- ★★★ **`take(2)` 는 `next#1 | next#2 | return()`** — 두 개를 채우자 **셋째를 당기지 않고 원본을 닫는다.**
- ★★★ **`take(5)` 도 `next#5` 다음에 바로 `return()`** — 원본이 딱 다섯이어도 **여섯째로 끝을 확인하지 않는다.** 한도가 찼으니 닫는다.
  **`take(9)` 는 `next#6 done` 이고 `return()` 이 없다** — 원본이 먼저 `done` 을 줬다. 이 두 줄이 9번의 답이다.
- ★★ **`drop(2)`·`find(없는 값)`·`forEach`·`reduce` 는 `next#6 done` · `return()` 없음** — 끝까지 가서 `done` 을 받았다.
  **`find(있는 값)`·`some(참)`·`every(거짓)` 은 답이 나온 `next#2` 에서 `return()`** 이다.
- ★★★ **`[2]` 콜백이 던지면 닫고 그 예외(`Error 「mapper threw」`)를 올린다.**
  ★★★ **`for…of` 의 `break`, `const [a] = …` 가 원본의 `return()` 까지 닿는다** — 소비자는 **헬퍼**를 닫고, 헬퍼가 **원본**을 닫는다.
- ★ `flatMap(x => [x, x]).take(3)` 은 원본 `next` 두 번이다 — 원본 값 하나가 **값 두 개**로 펴진다.
- ★ **마지막 줄 `return() was called in 9 of 14 probes` 는 스크립트가 센 것**이다. 19번의 `8 of 17` 과 **같은 규칙의 다른 표본**이다.

### 4. 두 번 쓰면 — **두 번째 `toArray()` 는 `[]`, 한 원본의 두 헬퍼는 번갈아 가져간다, `throw` 는 없다** ★★★

**출력**

```text
===== google-chrome --headless --dump-dom 'js20b-page.html?js20b-21f-consume.web.js' | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' | sed 's/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&amp;/\&/g' (exit=0) =====
[1] one helper, two toArray() calls
  first  toArray()  [2,4,6]
  second toArray()  []

[2] the source after a helper has been drained
  doubled.toArray()   [2,4,6]
  src.next()          {"done":true}

[3] two helpers built on one source, pulled in turn
  a, b, a, b, ...     ["a1","b2","a3","b4","a5","b6","undefined","undefined"]

[4] the array, by contrast
  arr.map twice       [2,4,6] [2,4,6]
  arr after           [1,2,3]

[5] h[Symbol.iterator]() === h, and two spreads of h
  h[Symbol.iterator]() === h   true
  [...h] then [...h]           [1,2] []

[6] callback arguments, and the methods a helper object has
  map((v, i) => v + ':' + i)       ["10:0","20:1","30:2"]
  reduce((s, v, i) => s + i, '')   "012"
  typeof next / return / throw     function / function / undefined
```

**왜 그런가**

- ★★★ **`[1]` `[2,4,6]` 다음 `[]`** — 헬퍼는 **원본을 붙들고 있을 뿐**이고, 첫 `toArray()` 가 원본을 끝까지 당겼다. **에러가 아니라 빈 결과**다.
- ★★★ **`[2]` 원본의 `next()` 가 `{"done":true}`** — 헬퍼가 원본의 복사본을 만든 것이 **아니다.**
- ★★★ **`[3]` `["a1","b2","a3","b4","a5","b6","undefined","undefined"]`** — `a` 와 `b` 가 **같은 원본에서 번갈아 한 칸씩** 가져갔다. 일곱째·여덟째는 원본이 끝나 `undefined` 다.
- ★ **`[4]` 배열은 두 번 `map` 해도 두 번 다 `[2,4,6]`** — 배열은 **값을 저장한 것**이고 이터레이터는 **한 번 지나가는 커서**다.
- ★★ **`[5]` `h[Symbol.iterator]() === h` 가 `true` 이고 스프레드 두 번이 `[1,2] []`** — 19번의 「자기 자신을 돌려주는 이터레이터」 부류다.
- ★★ **`[6]` 콜백은 `(값, 번호)` 를 받는다**(`"10:0"` …) · **헬퍼 객체에는 `next`·`return` 만 있고 `throw` 가 `undefined`** — 20번의 제너레이터 객체와 다르다.

### 5. 잘못된 인자 — **숫자·콜백 검사는 만들 때 던지고 원본을 닫는다. `flatMap` 의 반환값만 첫 `next()` 에서** ★★

**출력**

```text
===== google-chrome --headless --dump-dom 'js20b-page.html?js20b-21h-args.web.js' | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' | sed 's/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&amp;/\&/g' (exit=0) =====
take(-1)                          at build: RangeError 「-1 must be positive」
                                  source log: return()
take(NaN)                         at build: RangeError 「NaN must be positive」
                                  source log: return()
take('2')                         ok {"value":1,"done":false}
                                  source log: next#1
take(Infinity)                    ok {"value":1,"done":false}
                                  source log: next#1
drop(-1)                          at build: RangeError 「-1 must be positive」
                                  source log: return()
map('not a function')             at build: TypeError 「string "not a function" is not a function」
                                  source log: return()
filter(undefined)                 at build: TypeError 「undefined is not a function」
                                  source log: return()
flatMap(x => 'ab')                at first next(): TypeError 「Iterator.prototype.flatMap called on non-object」
                                  source log: next#1 | return()
flatMap(x => [x, x])              ok {"value":1,"done":false}
                                  source log: next#1
flatMap(x => x)                   at first next(): TypeError 「Iterator.prototype.flatMap called on non-object」
                                  source log: next#1 | return()

[].values().reduce((s, x) => s + x)         TypeError 「Reduce of a done iterator with no initial value」
[].values().reduce((s, x) => s + x, 0)      0
Iterator.prototype.map.call(1, x => x)      TypeError 「Iterator.prototype.map called on non-object」
Iterator.prototype.toArray.call({})         TypeError 「undefined is not a function」
```

**왜 그런가**

- ★★★ **`take(-1)`·`take(NaN)`·`drop(-1)` 은 `at build: RangeError`, `map('not a function')`·`filter(undefined)` 는 `at build: TypeError`** 다.
  ★★★ **원본 로그가 `return()` 한 줄** — 원본을 **한 번도 안 당겼는데 닫았다.** 16판 `take` 의 단계 「`If numLimit is NaN, then … Return ? IteratorClose(iterated, error).`」 그대로다.
- ★★ **`take('2')`·`take(Infinity)` 는 받는다** — `"2"` 는 숫자로 바뀌고, `Infinity` 는 `NaN` 도 음수도 아니다.
- ★★★ **`flatMap(x => 'ab')`·`flatMap(x => x)` 는 `at first next(): TypeError 「Iterator.prototype.flatMap called on non-object」`** 이고 원본 로그가 `next#1 | return()` 이다.
  **반환값은 값이 와야 볼 수 있으니** 첫 `next()` 에서 던지고, 그때 원본을 닫는다. 헬퍼 `flatMap` 은 **문자열을 거절한다**(명세의 `GetIteratorFlattenable(…, reject-primitives)`).
  ★★★ **문구는 원인을 가리키지 않는다** — 틀린 것은 `flatMap` 을 부른 대상이 아니라 **콜백의 반환값**이다. **던진 시점**이 원인을 말한다.
- ★ **`[].values().reduce(f)` 는 `TypeError 「Reduce of a done iterator with no initial value」`**, 초기값을 주면 `0` — 배열의 `reduce` 와 같은 계약이다.
- ★ **`Iterator.prototype.map.call(1, …)` 은 `called on non-object`** — 이쪽은 문구 그대로 `this` 가 원시값이다. **`toArray.call({})` 는 `undefined is not a function`** — `next` 가 없다.

### 6. `Iterator.from` — **이미 물려받았으면 그대로, 아니면 감싼다. `{}` 는 부를 때 통과하고 나중에 던진다** ★★

**출력**

```text
===== google-chrome --headless --dump-dom 'js20b-page.html?js20b-21e-from.web.js' | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' | sed 's/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&amp;/\&/g' (exit=0) =====
[1] what comes back
  from(bare { next }) === bare                              false
  typeof from(bare).map                                     function
  from(bare).map(x => x * 100).toArray()                    [100,200,300]
  from([7, 8].values()) === that iterator                   true
  from([1, 2, 3])  -> toArray()                             [1,2,3]
  from(iterable object) -> toArray()                        ["v1","v2"]
  from('ab') -> toArray()                                   ["a","b"]

[2] other arguments
  from(42)                                                  TypeError 「Iterator.from called on non-object」
  from(null)                                                TypeError 「Iterator.from called on non-object」
  typeof from({})  (the call alone)                         object
  from({}).toArray()                                        TypeError 「undefined is not a function」
  from({ a: 1 }).next()                                     TypeError 「undefined is not a function」

[3] a bare { next } object: typeof map, and map borrowed with call
  typeof bare2.map                                          undefined
  Iterator.prototype.map.call(bare2, x => -x).toArray()     [-1,-2]
```

**왜 그런가**

- ★★★ **`from(bare) === bare` 는 `false`** — 사슬에 `Iterator.prototype` 이 없는 것은 **감싼 새 객체**로 준다. 그 객체에 `map` 이 있다(`[100,200,300]`).
- ★★★ **`from([7, 8].values()) === that iterator` 는 `true`** — 이미 `Iterator.prototype` 을 물려받았으면 **그대로 돌려준다**(명세는 `OrdinaryHasInstance(%Iterator%, …)` 로 가른다).
- ★★ **배열 · `Symbol.iterator` 를 가진 객체 · 문자열**을 다 받는다 — **원시값 중 문자열만** 예외로 허용된다(`iterate-string-primitives`).
  `42`·`null` 은 **부르는 순간** `TypeError 「Iterator.from called on non-object」`.
- ★★★ **`typeof from({})` 는 `object`** — `Symbol.iterator` 가 없으면 **그 객체를 이터레이터로 보고** 받아 둔다. **`toArray()` 에서야** `undefined is not a function` 이다.
- ★ **`[3]` 감싸지 않고 `Iterator.prototype.map.call(bare2, …)` 로 빌려 써도 된다**(`[-1,-2]`) — 헬퍼는 `this` 의 `next` 만 본다.

### 7. 헬퍼가 붙는 이유 — **헬퍼는 `Iterator.prototype` 에 있고, 내장 이터레이터의 사슬이 전부 그곳을 지난다** ★★★

**출력**

```text
===== google-chrome --headless --dump-dom 'js20b-page.html?js20b-21d-chain.web.js' | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' | sed 's/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&amp;/\&/g' (exit=0) =====
[1] prototype chain of each iterator
  [1].values()                      (Array Iterator proto) -> Iterator.prototype -> Object.prototype
  new Map([[1, 2]]).entries()       (Map Iterator proto) -> Iterator.prototype -> Object.prototype
  new Set([1]).values()             (Set Iterator proto) -> Iterator.prototype -> Object.prototype
  'ab'[Symbol.iterator]()           (String Iterator proto) -> Iterator.prototype -> Object.prototype
  'a-b'.matchAll(/-/g)              (RegExp String Iterator proto) -> Iterator.prototype -> Object.prototype
  gen()                             gen.prototype -> (Generator proto) -> Iterator.prototype -> Object.prototype
  { next() {...} }  (hand-written)  Object.prototype

[2] typeof o.map / typeof o.toArray
  [1].values()                      function / function
  new Map([[1, 2]]).entries()       function / function
  new Set([1]).values()             function / function
  'ab'[Symbol.iterator]()           function / function
  'a-b'.matchAll(/-/g)              function / function
  gen()                             function / function
  { next() {...} }  (hand-written)  undefined / undefined

[3] own properties of Iterator.prototype (names, sorted)
  Symbol(Symbol.dispose) Symbol(Symbol.iterator) Symbol(Symbol.toStringTag) constructor drop every filter find flatMap forEach map reduce some take toArray

[4] Iterator itself
  typeof Iterator                                         function
  new Iterator()                                          TypeError 「Abstract class Iterator not directly constructable」
  class C extends Iterator; new C() instanceof Iterator   true
  [1].values() instanceof Iterator                        true
  gen() instanceof Iterator                               true
```

**왜 그런가**

- ★★★ **내장 여섯 가지의 사슬이 한두 단계 위에서 `Iterator.prototype` 을 만난다** — `(Array Iterator proto) -> Iterator.prototype`, 제너레이터는 `gen.prototype -> (Generator proto) -> Iterator.prototype`.
  **15번의 조회 규칙대로** `o.map` 은 자기 프로퍼티에 없으니 사슬을 올라가 거기서 찾는다.
- ★★★ **`{ next() {...} }` 의 사슬은 `Object.prototype` 하나**라 `map` 이 `undefined` 다.
  **「이터레이터다」(19번 — `next` 가 있다)와 「헬퍼가 있다」(사슬에 `Iterator.prototype` 이 있다)는 다른 질문**이다.
- ★★ **`new Iterator()` 는 `TypeError 「Abstract class Iterator not directly constructable」`**, `class C extends Iterator` 는 된다 — 손으로 만든 이터레이터를 **처음부터 헬퍼가 있게** 만드는 길이다.
- ★ `[3]` 에 `Symbol(Symbol.dispose)` 가 있는 것은 Chrome 151 이 ES2027 쪽 기능까지 들여서다 — 이 주제 밖이다.

### 8. 끝없는 원본 — **헬퍼는 필요한 만큼만 당기고, 배열 메서드는 원본을 배열로 먼저 만들어야 한다** ★★

**출력**

```text
===== google-chrome --headless --dump-dom 'js20b-page.html?js20b-21c-endless.web.js' | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' | sed 's/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&amp;/\&/g' (exit=0) =====
naturals().take(5).toArray()                  [1,2,3,4,5]           values pulled 5
naturals().map(x => x * x).take(4).toArray()  [1,4,9,16]            values pulled 4
naturals().filter(x => x % 7 === 0).take(3)   [7,14,21]             values pulled 21
naturals().drop(100).take(2).toArray()        [101,102]             values pulled 102
naturals().find(x => x * x > 50)              8                     values pulled 8
naturals().some(x => x === 3)                 true                  values pulled 3
naturals().every(x => x < 5)                  false                 values pulled 5
naturals().map(x => x)  (no terminal)         "built"               values pulled 0
naturals().take(0).toArray()                  []                    values pulled 0
```

**왜 그런가**

- ★★★ **`take(5)` 는 `values pulled 5`** — 헬퍼 사슬은 **원본을 값 단위로 당기므로** 끝이 없어도 된다.
- ★★ **`filter(x => x % 7 === 0).take(3)` 은 `21`**, **`drop(100).take(2)` 은 `102`** — 걸러지는 값·버리는 값도 **당겨야** 걸러지고 버려진다.
- ★★ **종단 메서드가 없으면 `0`** 이고, `take(0)` 도 `0` 이다.
- ★★★ **배열 메서드는 배열에만 있다** — 끝없는 원본을 배열로 만들려면 `[...naturals()]` 가 **끝나야** 하는데 끝나지 않는다.
  ★ **끝나지 않는 탐침은 캡처를 멈추므로 일부러 돌리지 않았다** — 「안 돌렸다」이고, 그 이유가 곧 답이다.

### 9. `take(5)` 와 19번 — **「`done` 을 직접 받았나」 한 규칙** ★★★

- ★★★ **19번** — `const [a, b, c] = it` 은 `next#3 -> 30 | return()`(값이 딱 셋인데 닫았다), `[a, b, c, d]` 는 `next#4 done` 까지 가서 **안 닫았다.**
- ★★★ **여기** — `take(5)` 는 `next#5 | return()`(딱 다섯인데 닫았다), `take(9)` 는 `next#6 done` 까지 가서 **안 닫았다**(3번).
- ★★★ **같은 규칙이다** — **소비자가 `done` 을 직접 받지 못하고 멈추면 닫고, 받았으면 닫지 않는다.**
  `take(n)` 은 n 개를 받으면 **다음을 당길 이유가 없어** `done` 을 못 본 채 멈춘다 — 그래서 닫는다.
- ★ 이 규칙은 **19번이 정본**이다. 여기는 **헬퍼가 그 규칙을 그대로 따른다**는 관찰이다.

### 10. node 18/20 — **`TypeError 「… .map is not a function」`, 그리고 제너레이터로 바꿔 물었더니 로그가 같았다** ★★

**출력**

```text
===== node20 js20b-21x-node-absent.js (exit=0) =====
[1] the helper call on this node
  TypeError 「src(...).values(...).map is not a function」
  typeof globalThis.Iterator  undefined

[2] a hand-rolled pipeline with generator functions
  result [20,40]
  map calls 4 · filter calls 4
  order  map(1) filter(10) map(2) filter(20) map(3) filter(30) map(4) filter(40)
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

**왜 그런가**

- ★★★ **`[1]` node20 의 헬퍼 호출은 `TypeError 「src(...).values(...).map is not a function」`** — 파싱은 되고 **실행에서 메서드를 못 찾는다.** `typeof globalThis.Iterator` 가 `undefined`.
  ★ **node18 도 같다** — 대조기의 `js20b-21x-node-absent.js` 줄이 `identical` 이다. (대조기의 다른 줄은 20·22·23번의 탐침이다.)
- ★★★ **`[2]` 제너레이터 함수 셋으로 손수 만든 파이프라인의 로그가 1번 `[2]` 의 헬퍼판과 한 글자도 같다** — `map calls 4 · filter calls 4`, `map(1) filter(10) map(2) filter(20) …`.
  **「값이 한 칸씩 흐른다」는 헬퍼의 발명이 아니라 이터레이터를 사슬로 이은 것의 성질**이다. 헬퍼는 그것을 **표준 메서드**로 준 것이다.
- ★★ **이것은 「창을 바꿔 물었다」(제5의 상태)** — 헬퍼 창이 node 에서 안 열려 제너레이터 창으로 같은 질문을 던졌다.
  ★ 바꾼 창은 **닫기(`return()`)를 보지 않았다** — 손수 만든 `take` 에 로그를 안 심었다. 닫기의 근거는 3번의 Chrome 로그뿐이다.

### 11. 다른 갈래 — **파이썬은 처음부터 지연 도구가 있었고, Rust 는 어댑터가 원래 지연, Kotlin 은 즉시가 기본** ★★

- ★★ **Python**(목록 15 · 16 · 44번) — 제너레이터 표현식과 `itertools` 가 **오래전부터 지연**이다. 여기의 `map`·`filter`·`take` 자리가 `(f(x) for x in it if g(x))` 와 `islice` 다.
  ★★ **갈래 복제 `itertools.tee` 가 파이썬에는 있고 JS 헬퍼에는 없다** — 4번의 `[3]`(한 원본을 두 헬퍼가 번갈아 가져간다)이 그 빈자리다.
- ★★ **Rust**(목록 36번) — 어댑터 사슬이 **최종 소비(`collect` 등) 전엔 아무 일도 안 한다.** 여기의 「종단 메서드 없이는 로그 0」과 같은 계약이다.
- ★★ **Kotlin**(목록 47번) — 컬렉션 연산은 **기본이 즉시**이고 `Sequence` 로 **명시적으로** 바꾼다. JS 도 같은 모양이다 — **배열 메서드가 즉시**, `arr.values()` 로 이터레이터를 얻어야 헬퍼(지연)다.
- ★★★ **JS 가 늦게 왔다** — 지연 사슬을 **표준 메서드로** 들인 것이 **ES2025** 다. 그 전에는 10번처럼 제너레이터로 손수 만들었다.
- ★ 이 문서는 **다른 갈래를 돌리지 않았다** — 위는 그 갈래 목록의 주제 진술을 견준 것이고, 실측은 그쪽 편의 몫이다.

### 12. `Iterator.concat` — **ES2026. 이터러블만 받고, 인자의 `Symbol.iterator` 는 차례가 올 때 부른다** ★★

**출력**

```text
===== google-chrome --headless --dump-dom 'js20b-page.html?js20b-21i-concat.web.js' | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' | sed 's/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&amp;/\&/g' (exit=0) =====
[1] concat of two iterables
  after the call      log []
  next()              {"value":1,"done":false}  log ["A @@iterator()"]
  rest                [2,3]  log ["A @@iterator()","B @@iterator()"]

[2] other arguments
  Iterator.concat([1], 'ab')              TypeError 「Iterator.concat called on non-object」
  Iterator.concat([1], { next() {} })     TypeError 「#<Object> is not iterable」
  Iterator.concat([1], [2].values())      [1,2]
```

**왜 그런가**

- ★★★ **판 경계** — ECMA-262 **16판(2025)** 본문에서 `Iterator.concat` 을 찾으면 **0건**, **17판(2026)** 에서 **2건**이다. finished proposals 의 「Iterator Sequencing」 도 **2026**.
  **ES2025 의 헬퍼(`map`·`take`…)와 한 묶음이 아니다.** Chrome 151 에는 둘 다 있다(판별 블록).
- ★★★ **`[1]` 부른 직후 로그가 `[]`**, 첫 `next()` 에서 `A @@iterator()`, 다 당기자 `B @@iterator()` — **인자마다 자기 차례가 와야 연다.**
- ★★ **`[2]` 문자열 `'ab'` 는 `TypeError 「Iterator.concat called on non-object」`**, **`{ next() {} }` 는 `TypeError 「#<Object> is not iterable」`** —
  `concat` 은 **이터러블 객체만** 받는다. `Iterator.from` 이 문자열과 `{ next }` 를 받던 것(6번)과 **반대**다. 이터레이터 `[2].values()` 는 이터러블이기도 하니 된다.
- ★★★ **이 주제가 재지 않은 것** — **시간과 메모리 전부.** 「메모리를 아낀다」·「빠르다」에 이 주제는 **답하지 않는다.**
  근거로 쓸 수 있는 것은 **콜백 호출 수(1·2번)와 원본을 당긴 수(3·8번)** 뿐이다. 「중간 배열을 만들지 않는다」는 명세의 구조에서 오는 말이고, **그것이 몇 바이트인지는 잰 적이 없다.**

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js20b-21a-when.web.js` | ★★★ **배열판 대 헬퍼판의 콜백 로그**(횟수 · 순서) · 사슬을 만든 직후 0 · `next()` 마다 한 일 | Chrome 151 1벌(재대조 1벌) |
| `js20b-21b-grid.web.js` | ★★★ 파이프라인 열 벌의 **값 / 호출 수 격자** — `0 / 10` · `5 / 10` | Chrome 151 1벌(재대조 1벌) |
| `js20b-21c-endless.web.js` | ★★ 끝없는 원본을 당긴 수 · 종단 없음 0 | Chrome 151 1벌(재대조 1벌) |
| `js20b-21d-chain.web.js` | ★★ 내장 이터레이터 일곱 가지의 사슬 · `Iterator.prototype` 의 자기 프로퍼티 · 추상 클래스 | Chrome 151 1벌(재대조 1벌) |
| `js20b-21e-from.web.js` | ★★ `Iterator.from` 의 반환 · 거절 · `{}` 의 늦은 실패 | Chrome 151 1벌(재대조 1벌) |
| `js20b-21f-consume.web.js` | ★★★ 소비 · 원본 공유 · 배열 대조군 · 콜백 인자 · 헬퍼 객체의 메서드 | Chrome 151 1벌(재대조 1벌) |
| `js20b-21g-close.web.js` | ★★★ 헬퍼·종단 열네 가지의 **원본 `next`/`return` 로그**와 요약 | Chrome 151 1벌(재대조 1벌) |
| `js20b-21h-args.web.js` | ★★ 인자 검사의 **시점**과 원본 닫기 · 문구 | Chrome 151 1벌(재대조 1벌) |
| `js20b-21i-concat.web.js` | ★ `Iterator.concat`(ES2026) 의 여는 시점 · 거절 | Chrome 151 1벌(재대조 1벌) |
| `js20b-21x-node-absent.js` | ★★ node 에서 헬퍼 호출 · 제너레이터로 손수 만든 파이프라인의 로그 | node20 1벌 + node18 대조 1벌(identical) |
| `js20b-versions.sh` · `js20b-features.js` | 이 문서의 모든 출력이 **어느 판에서 나왔나** · 판별 표 | 1벌 |

**구현 의존 항목** — 다음은 **이 환경(Chrome 151.0.7922.173 · node 20.19.6 / 18.19.1 · x86-64 Linux)에서만** 그렇다.

- ★★★ **예외 문구 전부** — `-1 must be positive` · `NaN must be positive` · `string "not a function" is not a function` · `Abstract class Iterator not directly constructable` ·
  `Iterator.from called on non-object` · `Iterator.prototype.flatMap called on non-object` · `Iterator.concat called on non-object` · `#<Object> is not iterable` ·
  `Reduce of a done iterator with no initial value` · `src(...).values(...).map is not a function`. **종류(`TypeError`/`RangeError`)만 명세가 정한다.**
- ★★ **node 18/20 에 헬퍼가 없는 것** — 그 판들의 V8 이 ES2025 이전이라서다.
- ★ **`Iterator.prototype[Symbol.dispose]` 가 보이는 것** — Chrome 151 의 사정이다.

**콜백이 값마다 번갈아 불리는 것 · 종단 전 0 · `take` 가 한도를 채우면 닫는 것 · `done` 을 받으면 안 닫는 것 · 콜백이 던지면 닫는 것 · 인자 검사가 만들 때 일어나고 원본을 닫는 것 · 헬퍼가 원본을 소비하는 것 · 헬퍼가 `Iterator.prototype` 에 있는 것 · `Iterator.from` 이 문자열을 받는 것은 구현 의존이 아니다.**
어느 엔진에서도 같아야 한다.

**안 돌려 본 것 / 못 잰 것 / 부적용인 창**

- **안 돌려 본 것** — **끝나지 않는 탐침**(`[...naturals()]` — 캡처를 멈춘다) · **다른 엔진**(SpiderMonkey·JavaScriptCore)의 문구 ·
  **손수 만든 제너레이터 파이프라인의 닫기**(로그를 안 심었다) · **비동기 이터레이터 헬퍼**(ES2025 에 없다 — 40번 주제) · 다른 갈래(Python·Rust·Kotlin) 의 실측.
- ★ **못 잰 것** — **node 두 판에서의 헬퍼 동작 전부** — 그 판에 기능이 없다(판별 블록이 근거). 그래서 **제너레이터 창으로 바꿔 물었다**(10번).
- ★★★ **안 쟀다** — **시간 · 메모리 전부.** 「메모리를 아낀다」·「빠르다」를 한 줄도 쓰지 않았다.
- ★★ **부적용인 창** — **③ 브랜드 태그**(헬퍼 유무는 사슬이 정한다 — 7번) · **진단의 `(행,열)`**(`SyntaxError` 가 없다). **「잴 것이 없다」는 뜻**이다.
- ★★★ **창을 바꿔 물은 자리** — node 에서의 「한 값씩 흐르나」를 **제너레이터 함수로 손수 만든 파이프라인**으로 물었다(10번).

**판이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **node 판이 ES2025 를 들이면** — 판별 블록부터 다시 찍고, `.web.js` 탐침을 node 에서도 돌려 Chrome 과 대조한다. 그때 두 판 대조기의 대상이 늘어난다.
- ★★ **예외 문구 전부** — 특히 `flatMap` 의 문구(원인과 어긋나 있다).
- **평가 순서 · 닫기 규칙 · 소비는 다시 돌릴 필요가 없다** — ES2025 의 계약이다.
