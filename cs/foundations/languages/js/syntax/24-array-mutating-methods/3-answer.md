# js/syntax/24 — 배열 변형 메서드: 「무엇이 원본을 바꾸고 무엇을 돌려주나 — 그리고 `sort` 는 무엇으로 비교하나」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **node v20.19.6**(기본 판) · **node v18.19.1**(대조) · x86-64 Linux 에서 실제로 돌려 얻은 것이고,
> 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 하나도 없다).
>
> ★★ **예외는 `e.constructor.name` 과 `e.message` 로만 찍었다** — 스택트레이스에는 절대 경로가 박혀 재현이 안 된다.
> ★★★ **이 주제의 탐침은 두 node 판에서 한 글자도 같았다** — 판 대조기의 집계 줄은 [2-summary.md](2-summary.md) 머리말에 있다.
> ★★ **8번의 둘째 블록(난수 비교 함수)은 분포를 찍지 않는다** — 가짓수만 찍어 흔들리지 않게 만들었다.
>
> **이 파일이 인용하는 출력을 낸 소스** — 전문은 [1-question.md](1-question.md) 의 같은 번호 문항에 있다(7·8·10번의 소스만 여기 싣는다).
> `js24b-24a-mutation-grid.js`(1번) · `js24b-24b-return-values.js`(2번) · `js24b-24c-default-order.js`(3번) · `js24b-24g-undefined-and-holes.js`(4번) ·
> `js24b-24h-same-array.js`(5번) · `js24b-24i-frozen-target.js`(6번) · `js24b-24d-equal-keys.js`(7번) · `js24b-24e-inconsistent-fixed.js` · `js24b-24f-inconsistent-random.js`(8번) · `js24b-24j-frozen-sloppy.js`(10번).

## 정답

### 1. 원본을 바꾸는 것은 **열 개**, 원본을 돌려주는 넷과 길이를 바꾸는 여섯은 **한 칸도 겹치지 않는다** ★★★

**출력**

```text
===== node20 js24b-24a-mutation-grid.js (exit=0) =====
start value for every row: [3,1,2]

method              returns     same?  content  length  after
push(9)             4           n      y        y       [3,1,2,9]
pop()               2           n      y        y       [3,1]
shift()             3           n      y        y       [1,2]
unshift(9)          4           n      y        y       [9,3,1,2]
splice(1, 1)        [1]         n      y        y       [3,2]
splice(1, 0, 9)     []          n      y        y       [3,9,1,2]
sort()              (arr)       y      y        n       [1,2,3]
reverse()           (arr)       y      y        n       [2,1,3]
fill(0)             (arr)       y      y        n       [0,0,0]
copyWithin(0, 2)    (arr)       y      y        n       [2,1,2]
slice(1)            [1,2]       n      n        n       [3,1,2]
concat([9])         [3,1,2,9]   n      n        n       [3,1,2]
map(x => x)         [3,1,2]     n      n        n       [3,1,2]
filter(x => x > 1)  [3,2]       n      n        n       [3,1,2]
join()              "3,1,2"     n      n        n       [3,1,2]

rows whose content column is y: 10 / 15
rows where same? and length are both y: 0 / 15
cells answering y: 20 / 45
```

**왜 그런가**

- ★★★ **두 가족** — `push`·`pop`·`shift`·`unshift`·`splice` 둘은 **길이를 바꾸고 원본 아닌 것**(새 길이 · 뺀 원소 · 지운 것들)을 돌려준다.
  `sort`·`reverse`·`fill`·`copyWithin` 은 **길이를 안 바꾸고 원본을** 돌려준다 — 명세의 마지막 단계가 "Return O"(`sort` 는 "Return obj")다.
- ★★★ **`rows where same? and length are both y: 0 / 15`** — 이 열다섯 개 안에서는 「원본을 돌려주면서 길이도 바꾸는」 메서드가 없다.
- ★★ **`splice(1, 1)` 의 반환값 `[1]` 은 배열이지만 원본이 아니다** — `same?` n. `splice(1, 0, 9)` 는 `[]` 를 돌려주고 원본을 바꿨다.
- ★ 대조 행 다섯(`slice`·`concat`·`map`·`filter`·`join`)은 세 칸 전부 n — 25번의 영역이다.
- 전부 명세 보장이다. 예외도 흔들리는 칸도 없다.

### 2. `push`·`unshift` 는 **새 길이**, `pop`·`shift` 는 **뺀 원소**, `splice` 는 **지운 것들의 새 배열** ★★★

**출력**

```text
===== node20 js24b-24b-return-values.js (exit=0) =====
[1] push / pop / unshift / shift
a.push(3, 4)                -> 4   arr [1,2,3,4]
a.pop()                     -> 4   arr [1,2,3]
a.unshift(0)                -> 4   arr [0,1,2,3]
a.shift()                   -> 0   arr [1,2,3]
[].pop()                    -> undefined
[].shift()                  -> undefined
[].push()                   -> 0

[2] splice(start, deleteCount, ...items)
splice(1, 2)                -> ["b","c"]   arr ["a","d","e"]
splice(1, 0, 'x')           -> []   arr ["a","x","b","c","d","e"]
splice(1, 2, 'x', 'y', 'z') -> ["b","c"]   arr ["a","x","y","z","d","e"]
splice(-2)                  -> ["d","e"]   arr ["a","b","c"]
splice(2)                   -> ["c","d","e"]   arr ["a","b"]
splice()                    -> []   arr ["a","b","c","d","e"]
splice(1, 99)               -> ["b","c","d","e"]   arr ["a"]
splice(9, 1, 'x')           -> []   arr ["a","b","c","d","e","x"]

[3] push with an array argument
c.push([2, 3])              -> 2   arr [1,[2,3]]
d.push(...[2, 3])           -> 3   arr [1,2,3]
```

**왜 그런가**

- ★★★ **`a.push(3, 4)` 가 `4`** — 명세 `push` 는 마지막 단계에서 **새 `len`** 을 돌려준다. **넣은 값이 아니라 길이**다. `unshift(0)` 도 새 길이 `4`.
- ★★ **빈 배열의 `pop()`·`shift()` 는 `undefined`** — 던지지 않는다. `[].push()` 는 `0`.
- ★★★ **`splice` 는 지운 것들을 돌려준다** — `splice(1, 2)` 가 `["b","c"]`. 끼우기만 하면 `[]`.
  ★ **인자 개수로 갈린다** — `splice()` 는 **아무것도 안 지우고**(`[]`), `splice(2)` 는 **끝까지** 지운다. 명세가 「start 가 없으면 0 개」·「deleteCount 가 없으면 `len - actualStart`」를 따로 적는다.
  `splice(1, 99)` 는 넘치는 개수를 **잘라서**(clamp) 끝까지, `splice(9, 1, 'x')` 는 start 를 **길이로 잘라서** 끝에 붙인다.
- ★ **`push([2, 3])` 은 배열 하나를 원소 하나로** 넣어 반환 `2`, `push(...[2, 3])` 은 둘을 넣어 반환 `3`.

### 3. 비교 함수가 없으면 **글자로** — `[1,10,9]`. 불리언 비교 함수는 이 판에서 **한 자리도 안 움직였다** ★★★

**출력**

```text
===== node20 js24b-24c-default-order.js (exit=0) =====
[1] no comparator
[10, 9, 1].sort()                               -> [1,10,9]
[5, 25, 100, 1].sort()                          -> [1,100,25,5]
[-1, -2, 3, -10].sort()                         -> [-1,-10,-2,3]
[3, 'a', 1, 'B', true].sort()                   -> [1,3,"B","a",true]
['b', 'a', 'C', 'A'].sort()                     -> ["A","C","a","b"]
[0.5, 1e21, 2, 1e-7].sort()                     -> [0.5,1e+21,1e-7,2]

[2] what each element is compared as
  10      String(x) = "10"
  9       String(x) = "9"
  1       String(x) = "1"
  -10     String(x) = "-10"
  1e+21   String(x) = "1e+21"
  1e-7    String(x) = "1e-7"
  true    String(x) = "true"

[3] with a numeric comparator
[10, 9, 1].sort((a, b) => a - b)                -> [1,9,10]
[5, 25, 100, 1].sort((a, b) => a - b)           -> [1,5,25,100]
[5, 25, 100, 1].sort((a, b) => b - a)           -> [100,25,5,1]
['b','a','C','A'].sort(localeCompare)           -> ["a","A","b","C"]

[4] a comparator that returns a boolean
  [3,1,2].sort((a, b) => a > b)                 -> [3,1,2]
  [1,3,2].sort((a, b) => a > b)                 -> [1,3,2]
  [2,1].sort((a, b) => a > b)                   -> [2,1]
  [5,1,4,2,3].sort((a, b) => a > b)             -> [5,1,4,2,3]
  [10,9,8,7,6,5,4,3,2,1].sort((a, b) => a > b)  -> [10,9,8,7,6,5,4,3,2,1]

[5] a comparator argument that is not a function
sort(undefined)                                 -> [1,2]
sort(null)                                      -> TypeError 「The comparison function must be either a function or undefined」
sort(1)                                         -> TypeError 「The comparison function must be either a function or undefined」
sort('desc')                                    -> TypeError 「The comparison function must be either a function or undefined」
```

**왜 그런가**

- ★★★ **`[1]`** — 비교 함수가 없으면 `CompareArrayElements` 가 **`ToString(x)` 와 `ToString(y)` 를 코드 유닛 순서로** 비교한다. `"1" < "10" < "9"`.
  `-10` 은 `"-10"`, `1e21` 은 `"1e+21"` 이라 글자 순서로 선다. **섞인 타입도 전부 글자**가 되어 던지지 않는다 — 대문자 `"B"` 가 소문자 `"a"` 앞이다.
- ★★ **`[3]`** — `a - b` 가 숫자 오름차순, `b - a` 가 내림차순. `localeCompare` 는 사람의 알파벳 순서(`a A b C`) — 이 줄만 ECMA-402 와 ICU 데이터에 매인다.
- ★★★ **`[4]`** — 다섯 입력 전부 **입력 그대로**다. `a > b` 는 불리언이라 `ToNumber` 로 `1` 아니면 `0` — **음수가 안 나온다.**
  ★★★ 이 결과는 **명세가 약속한 것이 아니다** — 불리언 비교 함수는 「consistent comparator」가 아니고(「v is a Number」를 어긴다), 그 순서는 **implementation-defined** 다(8번). 「안 움직인다」는 **이 판(V8 11.3·10.2)의 관찰**이다.
- ★★ **`[5]`** — `undefined` 는 「비교 함수 없음」과 같아 통과, 나머지는 **`TypeError`**. 명세 `sort` 의 **첫 단계** — "If comparator is not undefined and IsCallable(comparator) is false, throw a TypeError exception." 배열을 읽기 전이다.

### 4. **값 → `undefined` → 구멍** 순서. 비교 함수는 `undefined` 를 **한 번도 안 받는다** ★★★

**출력**

```text
===== node20 js24b-24g-undefined-and-holes.js (exit=0) =====
[1] no comparator
before  [3, undefined, 1, <hole>, 2, undefined, <hole>, 10]  length 8
after   [1, 10, 2, 3, undefined, undefined, <hole>, <hole>]  length 8

[2] numeric comparator, logging every call
after   [1, 2, 3, undefined, <hole>]  length 5
calls   4   1,3 | 2,1 | 2,3 | 2,1
any call received undefined? n

[3] a comparator that returns -1 when x is undefined
after   [1, 2, undefined]  length 3

[4] null and undefined in one array
after   [1, 2, null, undefined]  length 4
numeric [null, 1, 2, undefined]  length 4
```

**왜 그런가**

- ★★★ **`[1]`** — `sort` 는 `SortIndexedProperties` 를 **`skip-holes`** 로 부른다. 구멍은 목록에 **안 들어가고**, 정렬한 목록을 자리 0 부터 쓴 뒤 **남은 자리를 `Delete`** 한다 — 그래서 구멍이 **끝에 모인다.**
  `undefined` 는 `CompareArrayElements` 의 ①\~③ 이 **값들보다 뒤로** 보낸다. 명세 Note 1 이 그대로 적는다 — "undefined property values always sort to the end of the result, followed by non-existent property values."
- ★★★ **`[2]`** — 네 번의 호출이 전부 숫자 쌍이다. `undefined` 판정이 **비교 함수를 부르기 전에** 끝난다.
- ★★ **`[3]`** — 그래서 `x === undefined ? -1 : …` 가지는 **불릴 일이 없고**, 결과는 `[1, 2, undefined]`.
- ★ **`[4]`** — `null` 은 특별 취급이 없다. 기본 정렬에서는 `"null"` 이라는 글자(`"2"` 뒤), 숫자 비교에서는 `ToNumber(null)` 이 `0` 이라 맨 앞. 끝 자리가 고정된 것은 `undefined` 뿐이다.

### 5. 반환값과 원본이 **한 배열**이다 — `rev === orig`, `fill([])` 은 **배열 하나를 세 자리에** ★★★

**출력**

```text
===== node20 js24b-24h-same-array.js (exit=0) =====
[1] rev = orig.reverse()
rev  [3,2,1]   orig [3,2,1]   rev === orig true

[2] four chains
top    [30,20]   scores [30,20,10]
last   "c"   names ["c","b","a"]
copied [1,2,3]   src [3,1,2]
spread [2,1,3]   src [3,1,2]

[3] fill with an object
grid [["x"],["x"],["x"]]
grid[0] === grid[1] true   grid[1] === grid[2] true
rows [["x"],[],[]]   rows[0] === rows[1] false
Array(3)            length 3   0 in it false
Array(3).fill(0)    [0,0,0]
[1,2,3,4].fill(9, 1, 3)  [1,9,9,4]
[1,2,3,4].fill(9, -1)    [1,2,3,9]

[4] copyWithin(target, start, end)
  [1,2,3,4,5].copyWithin(0, 3)      -> [4,5,3,4,5]   length 5   same true
  [1,2,3,4,5].copyWithin(1, 0)      -> [1,1,2,3,4]   length 5   same true
  [1,2,3,4,5].copyWithin(0, 1, 3)   -> [2,3,3,4,5]   length 5   same true
  [1,2,3,4,5].copyWithin(-2, 0)     -> [1,2,3,1,2]   length 5   same true
  [1,2,3,4,5].copyWithin(2, 0, 2)   -> [1,2,1,2,5]   length 5   same true

[5] assigning to length
after length = 2   t [1,2]   alias [1,2]   t[3] undefined
after length = 4   t.length 4   2 in t false   t[2] undefined
after alias.length = 0   t []
length = -1          -> RangeError 「Invalid array length」
length = 1.5         -> RangeError 「Invalid array length」
length = 4294967296  -> RangeError 「Invalid array length」
```

**왜 그런가**

- ★★★ **`[1]`** — `reverse` 는 원본을 뒤집고 **원본을** 돌려준다. `rev` 와 `orig` 는 한 배열의 두 이름이다.
- ★★★ **`[2]`** — `scores.sort(…)` 가 먼저 **원본을** 정렬하고, 그 원본에 `slice` 가 붙는다. `scores` 가 `[30,20,10]` 으로 바뀌었다. `names` 도 정렬되고 뒤집혔다.
  ★ **복사를 먼저** 하는 두 줄만 원본이 산다 — `src` 가 `[3,1,2]` 그대로다.
- ★★★ **`[3]`** — `fill` 은 `value` 를 **한 번 받아** 자리마다 `Set` 한다. `[]` 하나가 세 자리에 들어가므로 `grid[0] === grid[1]` 이 true 이고 `push` 한 번이 세 칸에 보인다.
  `Array.from({ length: 3 }, () => [])` 은 **콜백을 자리마다** 불러 새 배열 셋을 만든다. `Array(3)` 은 구멍 셋이다(`0 in it false`).
- ★★ **`[4]`** — `copyWithin(0, 3)` 은 자리 3·4 의 `4,5` 를 자리 0·1 로 덮는다. `copyWithin(1, 0)` 은 **겹치는데도** `[1,1,2,3,4]` — 명세가 `from < to` 이고 겹치면 **뒤에서부터** 복사해 원래 값이 덮이기 전에 읽는다.
  음수 `target`(`-2`)은 `length + target`. 다섯 줄 전부 길이 5, `same true`.
- ★★★ **`[5]`** — `length = 2` 는 **자르고**, `alias` 도 같은 배열이라 같이 잘린다. `length = 4` 는 **구멍**을 만든다(`2 in t false`). `alias.length = 0` 이 `t` 까지 비운다.
  잘못된 길이 셋은 `RangeError 「Invalid array length」` — `ArraySetLength` 는 `ToUint32` 한 값과 `ToNumber` 한 값이 다르면 `RangeError` 를 던진다.

### 6. 변형 메서드는 **쓰는 순간** 던진다 — 이미 정렬된 배열의 `sort` 도, 빈 배열의 `pop` 도 ★★

**출력**

```text
===== node20 js24b-24i-frozen-target.js (exit=0) =====
frozen [3,1,2]
  push(9)           TypeError 「Cannot add property 3, object is not extensible」             after [3,1,2]
  pop()             TypeError 「Cannot delete property '2' of [object Array]」                after [3,1,2]
  shift()           TypeError 「Cannot assign to read only property '0' of object '[object Array]'」  after [3,1,2]
  unshift(9)        TypeError 「Cannot add property 3, object is not extensible」             after [3,1,2]
  splice(0, 1)      TypeError 「Cannot assign to read only property '0' of object '[object Array]'」  after [3,1,2]
  sort()            TypeError 「Cannot assign to read only property '0' of object '[object Array]'」  after [3,1,2]
  reverse()         TypeError 「Cannot assign to read only property '0' of object '[object Array]'」  after [3,1,2]
  fill(0)           TypeError 「Cannot assign to read only property '0' of object '[object Array]'」  after [3,1,2]
  copyWithin(0, 1)  TypeError 「Cannot assign to read only property '0' of object '[object Array]'」  after [3,1,2]
  length = 0        TypeError 「Cannot assign to read only property 'length' of object '[object Array]'」  after [3,1,2]
  slice()           no throw                                                                after [3,1,2]
frozen [1,2,3]
  push(9)           TypeError 「Cannot add property 3, object is not extensible」             after [1,2,3]
  pop()             TypeError 「Cannot delete property '2' of [object Array]」                after [1,2,3]
  shift()           TypeError 「Cannot assign to read only property '0' of object '[object Array]'」  after [1,2,3]
  unshift(9)        TypeError 「Cannot add property 3, object is not extensible」             after [1,2,3]
  splice(0, 1)      TypeError 「Cannot assign to read only property '0' of object '[object Array]'」  after [1,2,3]
  sort()            TypeError 「Cannot assign to read only property '0' of object '[object Array]'」  after [1,2,3]
  reverse()         TypeError 「Cannot assign to read only property '0' of object '[object Array]'」  after [1,2,3]
  fill(0)           TypeError 「Cannot assign to read only property '0' of object '[object Array]'」  after [1,2,3]
  copyWithin(0, 1)  TypeError 「Cannot assign to read only property '0' of object '[object Array]'」  after [1,2,3]
  length = 0        TypeError 「Cannot assign to read only property 'length' of object '[object Array]'」  after [1,2,3]
  slice()           no throw                                                                after [1,2,3]
frozen []
  push(9)           TypeError 「Cannot add property 0, object is not extensible」             after []
  pop()             TypeError 「Cannot assign to read only property 'length' of object '[object Array]'」  after []
  shift()           TypeError 「Cannot assign to read only property 'length' of object '[object Array]'」  after []
  unshift(9)        TypeError 「Cannot add property 0, object is not extensible」             after []
  splice(0, 1)      TypeError 「Cannot assign to read only property 'length' of object '[object Array]'」  after []
  sort()            no throw                                                                after []
  reverse()         no throw                                                                after []
  fill(0)           no throw                                                                after []
  copyWithin(0, 1)  no throw                                                                after []
  length = 0        TypeError 「Cannot assign to read only property 'length' of object '[object Array]'」  after []
  slice()           no throw                                                                after []
```

**왜 그런가**

- ★★★ **`frozen [3,1,2]`** — 변형 메서드 열 개가 전부 `TypeError`, `slice()` 만 통과. 문구는 **세 가지** — 새 자리를 만들다(`Cannot add property 3, object is not extensible`) · 지우다(`Cannot delete property '2' …`) · 있는 자리에 쓰다(`Cannot assign to read only property …`).
  원본은 그대로다 — **첫 쓰기**에서 멈췄다.
- ★★★ **`frozen [1,2,3]`** — `sort()` 가 **이미 정렬됐는데도** 던진다. 명세 `sort` 는 정렬한 목록을 **자리 0 부터 전부 `Set`** 한다. 값이 같은지 묻지 않는다.
- ★★★ **`frozen []`** — `sort`·`reverse`·`fill`·`copyWithin` 은 **쓸 자리가 없어** 안 던진다. `pop`·`shift`·`splice` 는 문구가 `'length'` 다 — 명세 `pop`·`shift` 는 길이가 0 이어도 `Set(O, "length", +0)` 을 한다.
  ★ **기준** — 「원본이 바뀌나」가 아니라 **「명세의 단계가 원본에 `Set`/`Delete` 를 부르나」**.
- 예외의 **종류**는 명세 보장, 문구는 V8 의 것이다.

### 7. 안정 정렬은 **ES2019(10판)부터** — 두 node 판은 **둘 다 그 뒤**라 판 대조로는 못 보고 같은 키 격자로 보였다 ★★★

**소스**

```js
// js24b-24d-equal-keys.js
// 키가 같은 원소들은 정렬 뒤에 원래 순서를 지키나 -- 길이를 바꿔 가며 묻는다.
// 원소 = { k: 키(0~2), i: 원래 자리 }. 키로만 비교한다.
const make = (n) => Array.from({ length: n }, (_, i) => ({ k: (i * 7) % 3, i }));
const kept = (sorted) => sorted.every((x, j) => j === 0 || sorted[j - 1].k !== x.k || sorted[j - 1].i < x.i);

console.log("[1] a small case, printed in full");
const small = make(9);
console.log("before  " + small.map((x) => x.k + ":" + x.i).join(" "));
small.sort((a, b) => a.k - b.k);
console.log("after   " + small.map((x) => x.k + ":" + x.i).join(" "));

console.log("");
console.log("[2] same question at many lengths");
let ok = 0, total = 0;
for (const n of [2, 5, 10, 11, 22, 23, 50, 100, 1000, 10000]) {
  const s = make(n).sort((a, b) => a.k - b.k);
  const r = kept(s);
  total++; if (r) ok++;
  console.log("  n = " + String(n).padEnd(6) + "equal-key groups in original order? " + (r ? "y" : "n"));
}
console.log("lengths answering y: " + ok + " / " + total);

console.log("");
console.log("[3] two passes -- secondary key first, then primary key");
const people = [["kim", "dev", 3], ["lee", "ops", 1], ["park", "dev", 1], ["choi", "ops", 3], ["jung", "dev", 1]];
const p = people.slice();
p.sort((a, b) => a[2] - b[2]);
p.sort((a, b) => (a[1] < b[1] ? -1 : a[1] > b[1] ? 1 : 0));
console.log(JSON.stringify(p));
```

**출력**

```text
===== node20 js24b-24d-equal-keys.js (exit=0) =====
[1] a small case, printed in full
before  0:0 1:1 2:2 0:3 1:4 2:5 0:6 1:7 2:8
after   0:0 0:3 0:6 1:1 1:4 1:7 2:2 2:5 2:8

[2] same question at many lengths
  n = 2     equal-key groups in original order? y
  n = 5     equal-key groups in original order? y
  n = 10    equal-key groups in original order? y
  n = 11    equal-key groups in original order? y
  n = 22    equal-key groups in original order? y
  n = 23    equal-key groups in original order? y
  n = 50    equal-key groups in original order? y
  n = 100   equal-key groups in original order? y
  n = 1000  equal-key groups in original order? y
  n = 10000 equal-key groups in original order? y
lengths answering y: 10 / 10

[3] two passes -- secondary key first, then primary key
[["park","dev",1],["jung","dev",1],["kim","dev",3],["lee","ops",1],["choi","ops",3]]
```

**왜 그런가**

- ★★★ **9판(ES2018)** — "The sort is not necessarily stable (that is, elements that compare equal do not necessarily remain in their original order)."
  **10판(ES2019)** — "The sort must be stable (that is, elements that compare equal must remain in their original order)."
- ★★ **최신 초안** — 그 문장을 `SortIndexedProperties` 의 조건으로 옮겼다. 「SortCompare 가 0 이면 원래 자리가 앞선 쪽이 앞」 — "if ℝ(SortCompare(old[j], old[k])) = 0, then π(j) < π(k); i.e., the sort is stable."
- ★★ **이 머신의 node 18 과 20 은 둘 다 경계 뒤**다. 그래서 「판에 따라 갈리나」로는 물을 수 없고, **길이 열 가지 × 같은 키**로 「이 판이 약속을 지키나」를 물었다 — `10 / 10`.
  ★ 이것은 **창을 바꿔 물은 것**이다(제5의 상태). 바꾼 창이 못 보는 것 — **ES2019 이전 엔진이 실제로 불안정했나.** 이 머신에 그 판이 없다.
- ★ `[3]` 두 번 나눠 정렬이 되는 것이 안정성의 쓸모다 — `dev` 무리 안에서 등급 순이 남았다.

### 8. 규칙을 어긴 비교 함수의 순서는 **implementation-defined** — 이 판에서는 흔들리지 않았고, 난수 비교 함수는 **모든 순열**이 나왔다 ★★★

**소스**

```js
// js24b-24e-inconsistent-fixed.js
// 일관되지 않은 비교 함수 -- 입력이 같으면 결과도 같나(이 블록의 비교 함수에는 난수가 없다).
const show = (label, r) => console.log(label.padEnd(44) + "-> " + JSON.stringify(r));
const base = [5, 1, 4, 2, 3];
const cmps = [
  ["() => 1", () => 1],
  ["() => -1", () => -1],
  ["() => 0", () => 0],
  ["(a, b) => a > b", (a, b) => a > b],
  ["(a, b) => a < b", (a, b) => a < b],
  ["(a, b) => (a % 2) - (b % 2) || 1", (a, b) => (a % 2) - (b % 2) || 1],
  ["() => NaN", () => NaN],
];
console.log("input " + JSON.stringify(base));
for (const [label, f] of cmps) {
  const outs = new Set();
  for (let t = 0; t < 50; t++) outs.add(JSON.stringify(base.slice().sort(f)));
  show(label, [...outs].map((s) => JSON.parse(s)));
  console.log("".padEnd(44) + "   distinct results over 50 runs: " + outs.size);
}

console.log("");
console.log("[2] how many times each comparator is called on the same input");
for (const [label, f] of cmps) {
  let calls = 0;
  base.slice().sort((a, b) => { calls++; return f(a, b); });
  console.log("  " + label.padEnd(42) + "calls " + calls);
}
```

**출력**

```text
===== node20 js24b-24e-inconsistent-fixed.js (exit=0) =====
input [5,1,4,2,3]
() => 1                                     -> [[5,1,4,2,3]]
                                               distinct results over 50 runs: 1
() => -1                                    -> [[3,2,4,1,5]]
                                               distinct results over 50 runs: 1
() => 0                                     -> [[5,1,4,2,3]]
                                               distinct results over 50 runs: 1
(a, b) => a > b                             -> [[5,1,4,2,3]]
                                               distinct results over 50 runs: 1
(a, b) => a < b                             -> [[5,1,4,2,3]]
                                               distinct results over 50 runs: 1
(a, b) => (a % 2) - (b % 2) || 1            -> [[4,2,5,1,3]]
                                               distinct results over 50 runs: 1
() => NaN                                   -> [[5,1,4,2,3]]
                                               distinct results over 50 runs: 1

[2] how many times each comparator is called on the same input
  () => 1                                   calls 4
  () => -1                                  calls 4
  () => 0                                   calls 4
  (a, b) => a > b                           calls 4
  (a, b) => a < b                           calls 4
  (a, b) => (a % 2) - (b % 2) || 1          calls 8
  () => NaN                                 calls 4
```

```js
// js24b-24f-inconsistent-random.js
// 비교 함수가 난수를 돌려주면 -- 같은 입력으로 여러 번 정렬해 서로 다른 결과가 몇 가지인지 센다.
// 분포(어느 결과가 몇 번)는 실행마다 흔들리므로 찍지 않는다. 가짓수와 그 목록만 찍는다.
const trials = 20000;
for (const base of [[1, 2, 3], [1, 2, 3, 4]]) {
  const outs = new Set();
  for (let t = 0; t < trials; t++) outs.add(base.slice().sort(() => Math.random() - 0.5).join(""));
  let perms = 1;
  for (let k = 2; k <= base.length; k++) perms *= k;
  console.log("input " + JSON.stringify(base) + "  trials " + trials);
  console.log("  distinct results: " + outs.size + " / " + perms + " permutations");
  console.log("  " + [...outs].sort().join(" "));
}
```
```text
===== node20 js24b-24f-inconsistent-random.js (exit=0) =====
input [1,2,3]  trials 20000
  distinct results: 6 / 6 permutations
  123 132 213 231 312 321
input [1,2,3,4]  trials 20000
  distinct results: 24 / 24 permutations
  1234 1243 1324 1342 1423 1432 2134 2143 2314 2341 2413 2431 3124 3142 3214 3241 3412 3421 4123 4132 4213 4231 4312 4321
```

**왜 그런가**

- ★★★ **어기는 조건** — 「consistent comparator」의 첫 조건이 "Calling comparator(a, b) always returns the same value v … Furthermore, v is a Number, and v is not NaN." 이다.
  `(a, b) => a > b` 는 **Number 가 아니다**(불리언). `() => 1` 은 **대칭성**(a = b 이면 b = a, a < b 와 a > b 중 하나만)을 어긴다. 난수는 **같은 쌍에 같은 값**을 어긴다.
- ★★★ **명세의 이름** — "The sort order is implementation-defined if SortCompare is not a consistent comparator for the elements of items."
  그래서 3번 `[4]` 의 「입력 그대로」는 **이 엔진·이 판의 사실**이지 언어의 사실이 아니다.
- ★★ **난수가 없는 일곱 개는 50판 모두 한 가지** — 흔들리지 않았다. 흔들리지 않는다고 **약속이 되는 것은 아니다**(규칙 3 — 「여러 번 같았다」는 보장이 아니다).
- ★★★ **난수 비교 함수** — 원소 3개에서 `6 / 6`, 4개에서 `24 / 24`. 결과 자체는 판마다 흔들리지만 **가짓수는 흔들리지 않는다** — 분포를 안 찍고 가짓수만 찍은 이유다.
  ★ **고르게 나오는가는 안 쟀다.** 섞기에는 피셔-예이츠를 쓴다.

### 9. 파이썬은 **`None` 을 돌려줘 체이닝을 막고 못 비교하면 던진다** · JS 는 **원본을 돌려줘 체이닝이 조용히 원본을 바꾸고 전부 글자로 비교한다** ★★★

- ★★★ 파이썬 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **10번** 출력 — `x.sort()        -> None`, 그리고 `sort().reverse()-> AttributeError 'NoneType' object has no attribute 'reverse'`.
  JS 의 `a.sort()` 는 **`a` 자신**(1번의 `same?` y).
- ★★★ **사고의 모양** — 파이썬은 체이닝이 **그 자리에서 터진다**(시끄럽다). JS 는 체이닝이 **된다** — 그리고 **원본을 바꾼다**(5번의 `[2]` — `names` 가 뒤집혔다, 에러 없음).
- ★★ **섞인 타입** — 파이썬 10번 `[3,'a',1].sort()   -> TypeError '<' not supported between instances of 'str' and 'int'`. JS 는 `[3, 'a', 1, 'B', true]` 가 `[1,3,"B","a",true]`(3번) — **전부 글자로 만들어** 비교한다.
  ★ 파이썬은 던진 뒤에도 **일부가 정렬된 채** 남는다(`[3,1,2,'a'].sort()` 뒤 `m2 = [1, 2, 3, 'a']`).
- ★ **안정성** — 파이썬은 **라이브러리 문서**가 "guaranteed to be stable" 이라 적고, 31번 ③ 이 `reverse=True` 도 안정임을 출력으로 보였다. JS 는 **ECMA-262 가 ES2019 부터** 요구한다.
- ★ 파이썬 쪽은 이 배치에서 다시 돌리지 않았다 — 두 문서의 출력을 인용했다.

### 10. `sort` 는 정렬한 목록을 **자리 0 부터 전부 `Set`** 한다 — 그리고 변형 메서드는 **모드와 상관없이** 던진다 ★★

**소스**

```js
// js24b-24j-frozen-sloppy.js
// 같은 질문을 엄격 모드 지시어 없이 -- 메서드 호출과 대입식 두 가지로.
const calls = [
  ["a.push(9)", (a) => a.push(9)],
  ["a.sort()", (a) => a.sort()],
  ["a.reverse()", (a) => a.reverse()],
  ["a.length = 0", (a) => { a.length = 0; }],
  ["a[0] = 9", (a) => { a[0] = 9; }],
  ["a[3] = 9", (a) => { a[3] = 9; }],
];
console.log("strict mode here? " + (function () { return this === undefined; })());
for (const [label, run] of calls) {
  const a = Object.freeze([3, 1, 2]);
  let r;
  try { run(a); r = "no throw"; }
  catch (e) { r = e.constructor.name + " 「" + e.message + "」"; }
  console.log("  " + label.padEnd(16) + r.padEnd(70) + "  after " + JSON.stringify(a));
}
```

**출력**

```text
===== node20 js24b-24j-frozen-sloppy.js (exit=0) =====
strict mode here? false
  a.push(9)       TypeError 「Cannot add property 3, object is not extensible」             after [3,1,2]
  a.sort()        TypeError 「Cannot assign to read only property '0' of object '[object Array]'」  after [3,1,2]
  a.reverse()     TypeError 「Cannot assign to read only property '0' of object '[object Array]'」  after [3,1,2]
  a.length = 0    no throw                                                                after [3,1,2]
  a[0] = 9        no throw                                                                after [3,1,2]
  a[3] = 9        no throw                                                                after [3,1,2]
```

**왜 그런가**

- ★★ **되돌려 놓는 법** — 명세 `sort` 의 5\~10단계: `SortIndexedProperties(…, skip-holes)` 로 목록을 만들어 정렬 → 자리 `0..itemCount-1` 에 차례로 **`Set(obj, j, sortedList[j], true)`** → 남은 자리를 **`DeletePropertyOrThrow`**.
  **값이 같은지 묻는 단계가 없다** — 그래서 6번의 `frozen [1,2,3]` 이 던진다. `frozen []` 은 `itemCount` 도 `len` 도 0 이라 쓰기가 하나도 없어 안 던진다.
- ★ **구멍** — 목록을 만들 때 `HasProperty` 가 false 인 자리를 **건너뛰어** 빠지고, 마지막의 `Delete` 단계에서 **끝에 다시** 생긴다. 명세 note — "The remaining indices are deleted to preserve the number of holes that were detected and excluded from the sort."
- ★★★ **엄격 모드 지시어를 빼도** `push`·`sort`·`reverse` 는 같은 `TypeError` 다. 명세 메서드의 쓰기는 전부 `Set(…, true)` — 마지막 `true` 가 「실패하면 던져라」다. **호출한 코드의 모드를 안 본다.**
  ★ **대입식 셋만 `no throw`** 다 — `a.length = 0` · `a[0] = 9` · `a[3] = 9` 는 **그 코드의 모드**를 따르고, 비엄격에서는 실패를 삼킨다. 원본은 그대로다.

### 11. 스택은 **`push`/`pop`**, 큐는 **`push`/`shift`** — 원리는 `data-structures-basics` 가 정본이고, 「`shift` 가 느리다」는 **안 쟀다** ★★

- ★★ **스택** — 끝에 넣고 끝에서 뺀다(`push`/`pop`). **큐** — 끝에 넣고 앞에서 뺀다(`push`/`shift`). `unshift`/`pop` 짝도 큐가 된다.
- ★★ **「`shift` 가 느리다」** — 이 문서의 「**안 쟀다**」 칸이다. 명세 `shift` 가 자리 `1..len-1` 을 **하나씩 앞으로 옮기는 단계**로 적혀 있다는 것까지가 이 문서가 말할 수 있는 것이고, 그것이 **이 엔진에서 시간으로 어떻게 나타나나는 재지 않았다.**
- ★ **경계** — [`cs/foundations/data-structures-basics/`](../../../../data-structures-basics/README.md) 는 **스택(4절)·큐(5절)가 무엇이고 어디에 쓰나**까지, 이 주제는 **JS 배열의 네 메서드가 무엇을 돌려주고 원본을 어떻게 바꾸나**부터다.

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js24b-24a-mutation-grid.js` | ★★★ 메서드 15 × 세 칸 격자 · 집계 줄 셋 | node20 1벌 + node18 대조 1벌 |
| `js24b-24b-return-values.js` | ★★★ 넣고 빼는 넷 · `splice` 여덟 형태의 반환값 | node20 1벌 + node18 대조 1벌 |
| `js24b-24c-default-order.js` | ★★★ 기본 문자열 비교 · 숫자 비교 함수 · 불리언 비교 함수 · 함수 아닌 인자 | node20 1벌 + node18 대조 1벌 |
| `js24b-24d-equal-keys.js` | ★★★ 같은 키 격자(길이 10가지) · 두 번 나눠 정렬 | node20 1벌 + node18 대조 1벌 |
| `js24b-24e-inconsistent-fixed.js` | ★★ 규칙을 어긴 비교 함수 일곱 개 × 50판 · 호출 수 | node20 1벌(판 안에서 50판) + node18 대조 1벌 |
| `js24b-24f-inconsistent-random.js` | ★★ 난수 비교 함수 × 2만 판 — **가짓수만** | node20 1벌 + node18 대조 1벌 |
| `js24b-24g-undefined-and-holes.js` | ★★★ `undefined`·구멍의 자리 · 비교 함수가 받은 인자 | node20 1벌 + node18 대조 1벌 |
| `js24b-24h-same-array.js` | ★★★ 반환값과 원본의 정체 · `fill` 공유 · `copyWithin` · `length` 대입 | node20 1벌 + node18 대조 1벌 |
| `js24b-24i-frozen-target.js` | ★★ 동결 배열 × 메서드 11 × 입력 셋(엄격 모드) | node20 1벌 + node18 대조 1벌 |
| `js24b-24j-frozen-sloppy.js` | ★★ 같은 질문을 비엄격 모드로 — 메서드 대 대입식 | node20 1벌 + node18 대조 1벌 |
| `js24b-vdiff.sh` · `js24b-versions.sh` | 두 판이 갈린 탐침 수 · 이 문서의 출력이 **어느 판에서 나왔나** + 판별 기능 표 | 1벌씩 |

판별 블록의 Chrome 줄을 낸 페이지 — 탐침 파일 이름을 주소의 `?` 뒤에 붙여 연다. `console.log` 를 가로채 줄이 늘 때마다 `<pre>` 를 다시 쓰고, `--dump-dom` 이 그것을 내보낸다.

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

- ★★★ **규칙을 어긴 비교 함수의 결과 전부**(3번 `[4]` · 8번) — 명세가 **implementation-defined** 라 부른다. 두 node 판에서 같았다 — 그래도 약속이 아니다.
- ★★ **비교 함수의 호출 순서와 횟수**(4번 `[2]` · 8번 `[2]`) — 명세는 "an implementation-defined sequence of calls to SortCompare" 다.
- ★★ **난수 비교 함수의 가짓수**(`6 / 6` · `24 / 24`) — 이 판 · 2만 판의 관찰이다.
- ★ **예외 문구 전부** — `The comparison function must be either a function or undefined` · `Cannot add property 3, object is not extensible` · `Cannot delete property '2' of [object Array]` ·
  `Cannot assign to read only property '0' of object '[object Array]'` · `Cannot assign to read only property 'length' of object '[object Array]'` · `Invalid array length`. **종류만 명세가 정한다.**
- ★ `localeCompare` 한 줄 — ECMA-402 · ICU 데이터.

**격자의 세 칸 · 반환값 · 기본 문자열 비교 · `undefined`/구멍의 자리 · 비교 함수가 `undefined` 를 안 받는 것 · 안정 정렬 · `sort` 의 전부 쓰기 · 모드와 상관없이 던지는 것 · `fill` 공유 · `copyWithin` 의 겹침 처리 · `length` 대입은 구현 의존이 아니다.**
어느 엔진에서도 같아야 한다.

**안 돌려 본 것 / 못 잰 것 / 부적용인 창**

- **안 돌려 본 것** — **Chrome 에서의 이 주제 탐침**(판별 블록만 돌렸다 — 같은 V8 계열이다) · **파이썬 쪽 재실행**(10번·31번 인용) · 다른 엔진(SpiderMonkey·JavaScriptCore)의 불리언 비교 함수 결과 · `TypedArray.prototype.sort`.
- ★★ **못 잰 것** — **ES2019 이전 엔진의 불안정 정렬.** 이 머신의 두 node 판이 다 경계 뒤다 — 명세 두 판의 문장과 같은 키 격자로 창을 바꿨다(7번).
- ★★★ **안 쟀다** — **성능 전부.** 「`push` 가 `concat` 보다 빠르다」·「`shift` 가 느리다」·「제자리 정렬이 메모리를 아낀다」를 **한 줄도 쓰지 않았다.**
- ★★ **부적용인 창** — **③ 브랜드 태그**(메서드가 전부 generic) · **진단의 `(행,열)`**(`SyntaxError` 가 없다). **「잴 것이 없다」는 뜻**이다.
- ★ **미룬 창** — Proxy `set` 트랩으로 **쓰기 횟수** 세기는 [25번](../25-array-non-mutating-and-copy-methods/2-summary.md)의 본체다.

**판이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **3번 `[4]` 과 8번 전부** — 엔진의 정렬 구현이 바뀌면 **결과가 바뀔 수 있고, 바뀌어도 명세 위반이 아니다.**
- ★★ **예외 문구 전부.**
- ★ 나머지(격자 · 반환값 · 안정성 · 구멍의 자리)는 **바뀌면 명세 위반**이다 — 다시 돌려 같은지 확인만 한다.
