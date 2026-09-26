# js/syntax/25 — 배열 비변형·복사 메서드: 「원본에는 쓰기가 한 번도 안 닿는다 — 단 얕게, 그리고 콜백은 예외다」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **node v20.19.6**(기본 판) · **node v18.19.1**(대조) · x86-64 Linux 에서 실제로 돌려 얻은 것이고,
> 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 하나도 없다).
>
> ★★ **예외는 `e.constructor.name` 과 `e.message` 로만 찍었다** — 스택트레이스에는 절대 경로가 박혀 재현이 안 된다.
> ★★★ **이 주제는 두 판이 갈린 블록을 넷 갖고 있다**(`25a` · `25b` · `25c` · `25f`) — 9번 답에 v18 판을 싣는다. 넷 다 **복사 메서드가 v18 에 없어서**다.
>
> **이 파일이 인용하는 출력을 낸 소스** — 전문은 [1-question.md](1-question.md) 의 같은 번호 문항에 있다(12번의 소스는 [2-summary.md](2-summary.md) 동작 (9)에 있다).
> `js24b-25a-trap-grid.js`(1번 · 7번 · 9번) · `js24b-25b-pairs.js`(2번 · 10번) · `js24b-25c-index-range.js`(3번) · `js24b-25d-reduce.js`(4번) ·
> `js24b-25e-map-parseint.js`(5번) · `js24b-25f-comparator-throws.js`(6번 · 11번) · `js24b-25g-shapes.js`(12번) · `js24b-vdiff.sh`(9번).

## 정답

### 1. 비변형 아홉은 쓰기 트랩 0, 변형 일곱과 「콜백이 쓰는 `map`」은 0 이 아니다 — `0 / 17` 던짐 · `9 / 17` ★★★

**출력**

```text
===== node20 js24b-25a-trap-grid.js (exit=0) =====
  method                       set  define  delete   get   target after returned
  map(x => x * 10)               0       0       0     6   [3,1,2]     [30,10,20]
  filter(x => x > 1)             0       0       0     6   [3,1,2]     [3,2]
  reduce((a, x) => a + x)        0       0       0     5   [3,1,2]     6
  slice(1)                       0       0       0     5   [3,1,2]     [1,2]
  concat([9])                    0       0       0     7   [3,1,2]     [3,1,2,9]
  toSorted()                     0       0       0     5   [3,1,2]     [1,2,3]
  toReversed()                   0       0       0     5   [3,1,2]     [2,1,3]
  toSpliced(0, 1)                0       0       0     4   [3,1,2]     [1,2]
  with(0, 9)                     0       0       0     4   [3,1,2]     [9,1,2]
  sort()                         3       3       0     5   [1,2,3]     <the proxy itself>
  reverse()                      2       2       0     4   [2,1,3]     <the proxy itself>
  splice(0, 1)                   3       3       1     6   [1,2]       [3]
  push(9)                        2       2       0     2   [3,1,2,9]   4
  fill(0)                        3       3       0     2   [0,0,0]     <the proxy itself>
  shift()                        3       3       1     5   [1,2]       3
  copyWithin(0, 1)               2       2       0     4   [1,2,2]     <the proxy itself>
  map((x, i, a) => a[i] = 0)     3       3       0     6   [0,0,0]     [0,0,0]

methods that threw: 0 / 17
methods that returned with zero write traps: 9 / 17
```

**왜 그런가**

- ★★★ **`map` · `filter` · `reduce` · `slice` · `concat` · `toSorted` · `toReversed` · `toSpliced` · `with` 아홉 행이 세 열 전부 0**, `target after` 가 `[3,1,2]` 그대로다.
  명세 단계가 원본에는 `Get`·`HasProperty` 만 하고, 결과는 **새 배열**에 `CreateDataPropertyOrThrow` 로 쓴다 — 새 배열은 Proxy 가 아니라 트랩에 안 걸린다.
- ★★★ **변형 일곱은 전부 쓰기가 있다** — `sort` 3 · `reverse` 2 · `splice(0, 1)` 3+삭제 1 · `push` 2 · `fill` 3 · `shift` 3+삭제 1 · `copyWithin` 2.
- ★★★ **마지막 행은 0 이 아니다** — `map` 은 안 쓰지만 **콜백이 세 번째 인자(원본)에 쓴다**(`set 3`, 원본 `[0,0,0]`). 명세 `map` note — "the object may be mutated by the calls to callback."
- ★★ **`set` 과 `define` 이 전 행에서 같다** — 7번.
- ★ node 18 에서는 두 줄이 `4 / 17` · `5 / 17` 이 된다 — 9번.

### 2. 복사 쪽은 전부 새 배열이고 원본 그대로 — ★ `toSpliced` 는 결과 전체, 복사는 한 겹, 구멍은 `undefined` ★★★

**출력**

```text
===== node20 js24b-25b-pairs.js (exit=0) =====
[1] four pairs on [30, 10, 20]
  sort()                returned [10,20,30]      === arr true    arr [10,20,30]
  toSorted()            returned [10,20,30]      === arr false   arr [30,10,20]
  reverse()             returned [20,10,30]      === arr true    arr [20,10,30]
  toReversed()          returned [20,10,30]      === arr false   arr [30,10,20]
  splice(1, 1, 99)      returned [10]            === arr false   arr [30,99,20]
  toSpliced(1, 1, 99)   returned [30,99,20]      === arr false   arr [30,10,20]
  a[1] = 99             returned 99              === arr false   arr [30,99,20]
  with(1, 99)           returned [30,99,20]      === arr false   arr [30,10,20]

[2] a chain that starts from a copy
  base.toSorted().reverse()       [30,20,10]   base [30,10,20]
  base.slice().sort().reverse()   [30,20,10]   base [30,10,20]

[3] how deep is the copy
  sorted === rows            false
  sorted[1] === rows[0]      true
  after sorted[1].id = 200   rows [{"id":200},{"id":1}]

[4] holes in the receiver [3, <hole>, 1]
  toSorted()            [1,3,undefined]
  sort()                [1,3,<hole>]
  toReversed()          [1,undefined,3]
  reverse()             [1,<hole>,3]
  with(0, 9)            [9,undefined,1]
  slice()               [3,<hole>,1]
  map(x => x)           [3,<hole>,1]
```

**왜 그런가**

- ★★★ **`[1]`** — `sort`·`reverse` 는 `=== arr true`(원본 자신을 돌려준다), 복사 넷은 `false` 에 원본 `[30,10,20]` 그대로.
  ★★★ **`splice(1, 1, 99)` 는 지운 것 `[10]`, `toSpliced(1, 1, 99)` 는 결과 전체 `[30,99,20]`** 이다. 대입식 `a[1] = 99` 의 값은 `99`.
- ★★ **`[2]`** — 두 사슬 다 `base [30,10,20]`. 첫 고리가 복사면 뒤의 `reverse` 는 **복사본**을 뒤집는다.
- ★★★ **`[3]`** — `sorted === rows` 는 false, **`sorted[1] === rows[0]` 은 true.** 그래서 `sorted[1].id = 200` 이 **원본 `rows` 의 첫 객체**를 바꾼다(`[{"id":200},{"id":1}]`).
- ★★★ **`[4]`** — **`toSorted` · `toReversed` · `with` 는 `undefined`**, **`sort` · `reverse` · `slice` · `map` 은 `<hole>`.**
  명세 — `sort` 는 `SortIndexedProperties(…, skip-holes)` 뒤 **남는 칸을 지운다**, `toSorted` 는 `read-through-holes`. `toReversed`·`with` 는 칸마다 `Get` 해서 결과에 **칸을 만든다**(구멍을 읽으면 `undefined`).

### 3. `with` 는 `3` · `5` · `-4` 에서 `RangeError`, 대입은 늘리거나 글자 키를 만든다 ★★★

**출력**

```text
===== node20 js24b-25c-index-range.js (exit=0) =====
[1] a.with(i, 9)
  i = 2     [0,1,9]  length 3   a [0,1,2]
  i = 3     RangeError 「Invalid index : 3」   a [0,1,2]
  i = 5     RangeError 「Invalid index : 5」   a [0,1,2]
  i = -1    [0,1,9]  length 3   a [0,1,2]
  i = -3    [9,1,2]  length 3   a [0,1,2]
  i = -4    RangeError 「Invalid index : -4」   a [0,1,2]
  i = 1.5   [0,9,2]  length 3   a [0,1,2]
  i = "1"   [0,9,2]  length 3   a [0,1,2]

[2] a[i] = 9
  i = 2     [0,1,9]  length 3  own keys ["0","1","2"]
  i = 3     [0,1,2,9]  length 4  own keys ["0","1","2","3"]
  i = 5     [0,1,2,<hole>,<hole>,9]  length 6  own keys ["0","1","2","5"]
  i = -1    [0,1,2]  length 3  own keys ["0","1","2","-1"]
  i = -3    [0,1,2]  length 3  own keys ["0","1","2","-3"]
  i = -4    [0,1,2]  length 3  own keys ["0","1","2","-4"]
  i = 1.5   [0,1,2]  length 3  own keys ["0","1","2","1.5"]
  i = "1"   [0,9,2]  length 3  own keys ["0","1","2"]

[3] at(i) and with(i) read the same index
  i = -1  at 2         with [0,1,9]
  i = -3  at 0         with [9,1,2]
  i = -4  at undefined with RangeError
  i = 3   at undefined with RangeError
```

**왜 그런가**

- ★★★ **`with`** — `ToIntegerOrInfinity` 로 자른 뒤(`1.5` → `1`, `"1"` → `1`) 음수면 `len + i`, 그 결과가 `[0, len)` 밖이면 **`RangeError 「Invalid index : 3」`**. 결과 길이는 **언제나 3.**
- ★★★ **대입** — `a[3] = 9` 는 `length 4`, **`a[5] = 9` 는 구멍 둘에 `length 6`.** 음수와 `1.5` 는 **배열 인덱스가 아니라** `"-1"` · `"1.5"` 라는 **평범한 프로퍼티**가 된다(`length 3` 그대로).
- ★★ **`[3]`** — `with` 의 인덱스 해석은 `at` 과 같다. `at` 이 `undefined` 인 `-4`·`3` 에서 `with` 는 `RangeError`.
- 조건·종류는 명세 보장, 문구 `Invalid index : 3` 은 V8 의 것이다.

### 4. 빈 배열 · 구멍만 있는 배열에 초기값이 없으면 `TypeError`, 원소 하나면 콜백 0회 ★★★

**출력**

```text
===== node20 js24b-25d-reduce.js (exit=0) =====
[1] reduce
  [1, 2, 3].reduce(f)               result 6                                                             calls 2  (1,2,i1) (3,3,i2)
  [1, 2, 3].reduce(f, 0)            result 6                                                             calls 3  (0,1,i0) (1,2,i1) (3,3,i2)
  [7].reduce(f)                     result 7                                                             calls 0  
  [].reduce(f, 0)                   result 0                                                             calls 0  
  [].reduce(f)                      result TypeError 「Reduce of empty array with no initial value」       calls 0  
  [, , 5].reduce(f)                 result 5                                                             calls 0  
  [, ,].reduce(f)                   result TypeError 「Reduce of empty array with no initial value」       calls 0  
  [].reduce(f, undefined)           result undefined                                                     calls 0  

[2] reduceRight
  [1, 2, 3].reduceRight(f)          result 6                                                             calls 2  (3,2,i1) (5,1,i0)
  [].reduceRight(f)                 result TypeError 「Reduce of empty array with no initial value」       calls 0  

[3] string accumulator -- same callback, which side starts
  ['a','b','c'].reduce(f)           result "abc"                                                         calls 2  (a,b,i1) (ab,c,i2)
  ['a','b','c'].reduce(f, '')       result "abc"                                                         calls 3  (,a,i0) (a,b,i1) (ab,c,i2)
  ['a','b','c'].reduce(f, 0)        result "0abc"                                                        calls 3  (0,a,i0) (0a,b,i1) (0ab,c,i2)
```

**왜 그런가**

- ★★★ **`[].reduce(f)` 와 `[, ,].reduce(f)` 가 `TypeError 「Reduce of empty array with no initial value」`** — `reduceRight` 도 같다. 명세 note — "It is a TypeError if the array contains no elements and initialValue is not provided." 구멍은 원소가 아니다.
- ★★★ **초기값이 없으면 첫 원소가 누산기** — `[1, 2, 3]` 은 콜백 **2회**(`(1,2,i1)` 부터), 초기값 `0` 이면 **3회**(`(0,1,i0)` 부터).
  ★ **`[7]` · `[, , 5]` 는 콜백 0회**로 그 원소가 그대로 나온다.
- ★★ **`[].reduce(f, undefined)` 는 `undefined`** — 초기값은 **인자가 있느냐**로 가린다. 값이 `undefined` 여도 「있다」.
- ★★ **`[3]`** — `"abc"` · `"abc"` · **`"0abc"`**. 초기값이 누산기의 타입을 정한다.

### 5. `[1, NaN, NaN]` — 인덱스가 기수로 들어간다 ★★★

**출력**

```text
===== node20 js24b-25e-map-parseint.js (exit=0) =====
[1] what map passes to its callback
  args ["1",0,["1","2","3"]]
  args ["2",1,["1","2","3"]]
  args ["3",2,["1","2","3"]]

[2] the same arguments given to parseInt
  parseInt("1", 0)   -> 1
  parseInt("2", 1)   -> NaN
  parseInt("3", 2)   -> NaN
  parseInt.length       2

[3] map(parseInt) and the alternatives
  ['1','2','3'].map(parseInt)             [1,"NaN","NaN"]
  ['10','10','10','10'].map(parseInt)     [10,"NaN",2,3]
  ['1','2','3'].map(Number)               [1,2,3]
  ['1','2','3'].map(s => parseInt(s, 10)) [1,2,3]
  ['1.5','2px'].map(Number)               [1.5,"NaN"]
  ['1.5','2px'].map(s => parseInt(s, 10)) [1,2]
  ['1','2','3'].map(parseFloat)           [1,2,3]
  parseFloat.length     1   Number.length 1
```

**왜 그런가**

- ★★★ **`map` 은 `(값, 인덱스, 배열)` 을 넘긴다**(`[1]`). `parseInt` 는 **둘째 인자를 기수**로 받으므로 `parseInt("2", 1)`(기수 1 은 없다 — `NaN`) · `parseInt("3", 2)`(`3` 은 이진 숫자가 아니다 — `NaN`). 기수 `0` 은 「안 줌」이라 10진이다.
  ★ `['10','10','10','10']` 은 `[10, NaN, 2, 3]` — 이진·삼진 `10`.
- ★★ **JS 는 남는 인자를 조용히 넘긴다** — [08번](../08-function-forms-and-parameters/2-summary.md)의 `length`·`arguments.length` 규칙. 받는 쪽이 몇 개를 쓸지 부르는 쪽은 모른다.
- ★★ **`'2px'` 는 같은 답이 아니다** — `Number` 는 `NaN`, `parseInt(s, 10)` 은 `2`. `'1.5'` 도 `1.5` 대 `1`.

### 6. `sort` 의 원본은 비교가 몇 번째에서 던지든 그대로다 — 명세가 되쓰기를 정렬 뒤에 둔다 ★★★

**출력**

```text
===== node20 js24b-25f-comparator-throws.js (exit=0) =====
[0] how many times the comparator is called when nothing throws
  sort     4
  toSorted 4

[1] the comparator throws at call k
  sort     k=1   Error 「call 1」        a [5,4,3,2,1]
  toSorted k=1   Error 「call 1」        b [5,4,3,2,1]
  sort     k=2   Error 「call 2」        a [5,4,3,2,1]
  toSorted k=2   Error 「call 2」        b [5,4,3,2,1]
  sort     k=4   Error 「call 4」        a [5,4,3,2,1]
  toSorted k=4   Error 「call 4」        b [5,4,3,2,1]

[2] 30 elements in a fixed shuffled order, the comparator throws at call k
  comparator calls when nothing throws: 108
  sort     k=1   Error 「call 1」        a unchanged true
  sort     k=54  Error 「call 54」       a unchanged true
  sort     k=108 Error 「call 108」      a unchanged true

[3] a comparator that is not a function
  undefined sort     returned
            toSorted returned
  null      sort     TypeError 「The comparison function must be either a function or undefined」
            toSorted TypeError 「The comparison function must be either a function or undefined」
  "desc"    sort     TypeError 「The comparison function must be either a function or undefined」
            toSorted TypeError 「The comparison function must be either a function or undefined」
  1         sort     TypeError 「The comparison function must be either a function or undefined」
            toSorted TypeError 「The comparison function must be either a function or undefined」
```

**왜 그런가**

- ★★★ **`[1]` · `[2]` 전부 원본 그대로**(`a [5,4,3,2,1]` · `a unchanged true` 세 줄 — `k=108` 은 **마지막 비교**다).
  명세 `sort` 는 ① 비교 함수 검사 → ② `SortIndexedProperties` 로 **목록을 만들어 정렬** → ③ 그 뒤에야 `Set` 으로 되쓴다.
  비교가 던지면 `SortIndexedProperties` 가 "stop before performing any further calls to SortCompare and return that Completion Record" 이고, `?` 가 그것을 전파해 **③ 에 오지 않는다.**
  ★★★ **명세 보장**이다 — V8 의 사정이 아니다.
- ★★ **`[3]`** — `null`·`"desc"`·`1` 은 **두 메서드 다 `TypeError 「The comparison function must be either a function or undefined」`**, `undefined` 만 통과. 검사는 **원본을 읽기 전**(단계 ①).
- ★ **`[0]` 의 `4` · `4` 와 `[2]` 의 `108` 은 명세가 정하지 않는다** — "implementation-defined sequence of calls to SortCompare". 근거로 안 쓴다(머리말 표).

### 7. 트랩이 `receiver`(= Proxy)를 `Reflect.set` 에 넘겨서 — 쓰기 하나가 `[[Set]]` 뒤 `[[DefineOwnProperty]]` 로 다시 Proxy 에 온다 ★★

- ★★ 평범한 쓰기(`OrdinarySet`)는 결국 **「receiver 에 데이터 프로퍼티를 정의」** 로 끝난다. 탐침의 `set` 트랩은 받은 `r`(= Proxy)을 그대로 `Reflect.set(t, k, v, r)` 에 넘기므로
  그 정의가 **Proxy 의 `[[DefineOwnProperty]]`** 가 되어 `defineProperty` 트랩이 한 번 더 불린다. 그래서 1번 격자의 두 열이 **행마다 같다.**
- ★ **셀 때는 한 열(`set`)만 보면 된다.** 이 문서는 둘 다 싣고 **합**으로 0 을 판정했다 — 어느 쪽으로 세도 결론이 같다.
- ★ `receiver` 를 안 넘기면(`Reflect.set(t, k, v)`) 정의는 **대상 `t`** 에 일어나 `defineProperty` 트랩이 안 불릴 것이다 — ★ **이 판에서 돌려 보지 않았다.** 트랩 계약은 목록의 **45번 주제**다.

### 8. `map` 은 하위 클래스, `toSorted` 는 늘 `Array` — 복사 메서드는 species 를 안 읽는다 ★★★

- ★★★ **[22번](../22-symbol-and-well-known-symbols/2-summary.md) 동작 (5-b)의 집계 줄은 `methods that read species 7 / 14`** 였다. `map` · `filter` · `slice` · `splice` · `concat` · `flat` · `flatMap` 이 `read x1`,
  **`toSorted` · `toReversed` · `with` · `toSpliced` 는 `-`**(안 읽는다)였다.
- ★★ 앞쪽은 **`ArraySpeciesCreate`**(`this.constructor[Symbol.species]`), 복사 넷은 **`ArrayCreate`** 로 결과를 만든다 — 동작 (3)에서 인용한 `with` 단계 「Let A be ? ArrayCreate(len)」 과 `toSorted`·`toReversed` 의 같은 단계.
- ★★ 그래서 [17번](../17-inheritance-and-super/2-summary.md)의 `class Stack extends Array` 는 `map`·`filter`·`slice` 결과가 `Stack` 인데, **`toSorted` 결과는 평범한 `Array`** 라 `Stack` 의 메서드(`top()`)가 **없다.**
- ★ 이 배치는 species 를 다시 재지 않았다 — 22번 출력의 인용이다.

### 9. Change Array by Copy 는 **2023** — README 의 「ES2024」와 다르다 · 갈린 탐침 넷, 이유는 한 종류 ★★

- ★★★ **finished proposals 표의 Change Array by Copy 줄이 `2023`** 이다. 목록 [README](../README.md) 25번 행은 「ES2024 `toSorted`·`toReversed`·`toSpliced`·`with`」라 적었다 — **목록 쪽 표기가 다르다**(이 편은 README 를 고치지 않는다).
  [22번](../22-symbol-and-well-known-symbols/2-summary.md) 머리말 표도 이 넷을 **ES2023** 으로 적었다.
- ★★ **갈린 탐침은 넷**(`25a` · `25b` · `25c` · `25f`), **이유는 한 종류** — 복사 메서드가 v18 에 **없다**(`TypeError 「… is not a function」`). 비교·인덱스·`reduce` 처럼 v18 에도 있는 기능에서는 **한 줄도 안 갈렸다.**
- ★★★ **node 18 의 1번 격자에서 `toSorted` · `toReversed` · `toSpliced` · `with` 네 행이 「쓰기 0」인 채 던졌다.** 격자가 **「던진 행」을 따로 세서** `methods that threw: 4 / 17` 로 갈라냈고, 쓰기 0 집계는 `5 / 17` 로 줄었다.
  ★ **던진 행을 따로 안 세면** 「없는 메서드」가 「원본을 안 바꾼 메서드」로 세어진다 — 그래서 격자에 `threw` 칸을 둔다(그 전 판의 출력은 캡처로 남기지 않았으므로 싣지 않는다).

**v18 판 — 1번 격자**

```text
===== node18 js24b-25a-trap-grid.js (exit=0) =====
  method                       set  define  delete   get   target after returned
  map(x => x * 10)               0       0       0     6   [3,1,2]     [30,10,20]
  filter(x => x > 1)             0       0       0     6   [3,1,2]     [3,2]
  reduce((a, x) => a + x)        0       0       0     5   [3,1,2]     6
  slice(1)                       0       0       0     5   [3,1,2]     [1,2]
  concat([9])                    0       0       0     7   [3,1,2]     [3,1,2,9]
  toSorted()                     0       0       0     1   [3,1,2]     TypeError 「p.toSorted is not a function」
  toReversed()                   0       0       0     1   [3,1,2]     TypeError 「p.toReversed is not a function」
  toSpliced(0, 1)                0       0       0     1   [3,1,2]     TypeError 「p.toSpliced is not a function」
  with(0, 9)                     0       0       0     1   [3,1,2]     TypeError 「p.with is not a function」
  sort()                         3       3       0     5   [1,2,3]     <the proxy itself>
  reverse()                      2       2       0     4   [2,1,3]     <the proxy itself>
  splice(0, 1)                   3       3       1     6   [1,2]       [3]
  push(9)                        2       2       0     2   [3,1,2,9]   4
  fill(0)                        3       3       0     2   [0,0,0]     <the proxy itself>
  shift()                        3       3       1     5   [1,2]       3
  copyWithin(0, 1)               2       2       0     4   [1,2,2]     <the proxy itself>
  map((x, i, a) => a[i] = 0)     3       3       0     6   [0,0,0]     [0,0,0]

methods that threw: 4 / 17
methods that returned with zero write traps: 5 / 17
```

**v18 판 — 2번 · 3번 · 6번**

```text
===== node18 js24b-25b-pairs.js (exit=0) =====
[1] four pairs on [30, 10, 20]
  sort()                returned [10,20,30]      === arr true    arr [10,20,30]
  toSorted()            returned TypeError 「a.toSorted is not a function」  === arr -       arr [30,10,20]
  reverse()             returned [20,10,30]      === arr true    arr [20,10,30]
  toReversed()          returned TypeError 「a.toReversed is not a function」  === arr -       arr [30,10,20]
  splice(1, 1, 99)      returned [10]            === arr false   arr [30,99,20]
  toSpliced(1, 1, 99)   returned TypeError 「a.toSpliced is not a function」  === arr -       arr [30,10,20]
  a[1] = 99             returned 99              === arr false   arr [30,99,20]
  with(1, 99)           returned TypeError 「a.with is not a function」  === arr -       arr [30,10,20]

[2] a chain that starts from a copy
  base.toSorted().reverse()       TypeError 「base.toSorted is not a function」   base [30,10,20]
  base.slice().sort().reverse()   [30,20,10]   base [30,10,20]

[3] how deep is the copy
TypeError 「rows.toSorted is not a function」

[4] holes in the receiver [3, <hole>, 1]
  toSorted()            TypeError 「[3,(intermediate value),1].toSorted is not a function」
  sort()                [1,3,<hole>]
  toReversed()          TypeError 「[3,(intermediate value),1].toReversed is not a function」
  reverse()             [1,<hole>,3]
  with(0, 9)            TypeError 「[3,(intermediate value),1].with is not a function」
  slice()               [3,<hole>,1]
  map(x => x)           [3,<hole>,1]
```
```text
===== node18 js24b-25c-index-range.js (exit=0) =====
[1] a.with(i, 9)
  i = 2     TypeError 「a.with is not a function」   a [0,1,2]
  i = 3     TypeError 「a.with is not a function」   a [0,1,2]
  i = 5     TypeError 「a.with is not a function」   a [0,1,2]
  i = -1    TypeError 「a.with is not a function」   a [0,1,2]
  i = -3    TypeError 「a.with is not a function」   a [0,1,2]
  i = -4    TypeError 「a.with is not a function」   a [0,1,2]
  i = 1.5   TypeError 「a.with is not a function」   a [0,1,2]
  i = "1"   TypeError 「a.with is not a function」   a [0,1,2]

[2] a[i] = 9
  i = 2     [0,1,9]  length 3  own keys ["0","1","2"]
  i = 3     [0,1,2,9]  length 4  own keys ["0","1","2","3"]
  i = 5     [0,1,2,<hole>,<hole>,9]  length 6  own keys ["0","1","2","5"]
  i = -1    [0,1,2]  length 3  own keys ["0","1","2","-1"]
  i = -3    [0,1,2]  length 3  own keys ["0","1","2","-3"]
  i = -4    [0,1,2]  length 3  own keys ["0","1","2","-4"]
  i = 1.5   [0,1,2]  length 3  own keys ["0","1","2","1.5"]
  i = "1"   [0,9,2]  length 3  own keys ["0","1","2"]

[3] at(i) and with(i) read the same index
  i = -1  at 2         with TypeError
  i = -3  at 0         with TypeError
  i = -4  at undefined with TypeError
  i = 3   at undefined with TypeError
```
```text
===== node18 js24b-25f-comparator-throws.js (exit=0) =====
[0] how many times the comparator is called when nothing throws
  sort     4
  toSorted 0

[1] the comparator throws at call k
  sort     k=1   Error 「call 1」        a [5,4,3,2,1]
  toSorted k=1   TypeError 「b.toSorted is not a function」b [5,4,3,2,1]
  sort     k=2   Error 「call 2」        a [5,4,3,2,1]
  toSorted k=2   TypeError 「b.toSorted is not a function」b [5,4,3,2,1]
  sort     k=4   Error 「call 4」        a [5,4,3,2,1]
  toSorted k=4   TypeError 「b.toSorted is not a function」b [5,4,3,2,1]

[2] 30 elements in a fixed shuffled order, the comparator throws at call k
  comparator calls when nothing throws: 108
  sort     k=1   Error 「call 1」        a unchanged true
  sort     k=54  Error 「call 54」       a unchanged true
  sort     k=108 Error 「call 108」      a unchanged true

[3] a comparator that is not a function
  undefined sort     returned
            toSorted TypeError 「a.toSorted is not a function」
  null      sort     TypeError 「The comparison function must be either a function or undefined」
            toSorted TypeError 「a.toSorted is not a function」
  "desc"    sort     TypeError 「The comparison function must be either a function or undefined」
            toSorted TypeError 「a.toSorted is not a function」
  1         sort     TypeError 「The comparison function must be either a function or undefined」
            toSorted TypeError 「a.toSorted is not a function」
```

**두 판 대조기**

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

- ★ 대조기의 다른 줄은 **같은 배치의 다른 주제 탐침**이다(한 대조기를 공유한다).
- ★ 근거로 쓰는 것 — **되나/안 되나(판 경계)와 예외 종류.** 근거로 안 쓰는 것 — 문구(`[3,(intermediate value),1].toSorted is not a function` 처럼 **소스 모양이 박힌다**).

### 10. 새로 만드는 것은 **배열 한 겹**뿐 — 원소 객체는 공유, 원본 쓰기는 콜백에서 온다 ★★

- ★★ `toSorted`·`slice`·`map` 은 **새 배열(컨테이너)** 을 만든다. 원소는 **값을 옮길 뿐**이라 객체 원소는 **같은 객체**다 — 2번 `[3]` 의 `sorted[1] === rows[0]` true.
  ★ 스프레드의 얕은 복사와 같은 성질이다([11번](../11-spread-and-rest/2-summary.md)).
- ★ 중첩까지 새로 만드는 수단(`structuredClone` · JSON 왕복 …)은 목록의 **48번 주제**가 정본이다 — 이 편은 **「한 겹이다」까지**만.
- ★ 비변형 메서드가 못 막는 원본 쓰기는 **콜백**에서 온다 — 1번 마지막 행(`set 3`). 메서드의 성질은 「**자신이** 안 쓴다」까지다.

### 11. 파이썬 `sorted` ↔ JS `toSorted` · 정렬 실패 시 파이썬은 부분 변경, JS `sort` 는 원본 그대로 — 명세(문서)가 정한 차이 ★★★

- ★★ 파이썬 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **10번** — `sorted(y) -> [1, 3] | y = [3, 1]`. **원본을 두고 새 리스트**를 준다 — JS 의 짝은 **`toSorted`**(2번 `[1]`).
  ★ 파이썬 `x.sort()` 는 **`None`** 을, JS `sort()` 는 **원본 자신**을 돌려준다 — 이쪽 함정은 [24번](../24-array-mutating-methods/2-summary.md)이 정본이다.
- ★★★ 파이썬 10번 — `[3,1,2,'a'].sort()` 가 `TypeError` 로 끝난 뒤 **`m2 = [1, 2, 3, 'a']`**(바뀐 채 남았다). 파이썬 문서가 "the list will likely be left in a partially modified state" 라 적는다.
  **JS `sort` 는 비교가 마지막 호출에서 던져도 원본 그대로**였다(6번 `[2]`).
- ★★ **둘 다 문서가 정한 것**이다 — 파이썬은 **부분 변경을 허용한다**고 적고, ECMA-262 는 **되쓰기를 정렬 뒤에** 둔다. 구현의 우연이 아니다.
  ★ 파이썬 쪽은 이 배치에서 **다시 돌리지 않았다** — 10번 문서의 출력을 인용했다.

### 12. `slice` 는 범위 밖을 잘라 주고 던지지 않는다 · `concat` 은 `IsConcatSpreadable` 인 인자만 한 겹 펼친다 ★

**출력**

```text
===== node20 js24b-25g-shapes.js (exit=0) =====
[1] slice on [0, 1, 2, 3, 4]
  slice()                             [0,1,2,3,4]
  slice() === a                       false
  slice(-2)                           [3,4]
  slice(1, -1)                        [1,2,3]
  slice(3, 1)                         []
  slice(10)                           []
  slice('1', '3')                     [1,2]

[2] concat
  [1].concat(2, [3], [[4]])           [1,2,3,[4]]
  [1].concat('ab')                    [1,"ab"]
  [1].concat({ 0: 'x', length: 1 })   [1,{"0":"x","length":1}]
  [1].concat() === [1]                false
  [1].concat([2]) length              2

[3] filter and map whose callbacks keep every element
  b.filter(() => true) === b          false
  b.map(x => x) === b                 false
  b.filter(() => false)               []
```

- ★★ **`slice(-2)` → `[3,4]` · `slice(3, 1)` → `[]` · `slice(10)` → `[]`** — 음수는 끝에서, 범위 밖은 **잘린다.** `with` 는 범위 밖에서 **던진다**(3번) — 반대다.
- ★★ **`[1].concat(2, [3], [[4]])` → `[1,2,3,[4]]`** — 한 겹. **`'ab'` 와 유사 배열 `{0:'x', length:1}` 은 안 펼친다.** 기준은 이터러블이 아니라 **`IsConcatSpreadable`**(배열이거나 `Symbol.isConcatSpreadable` 이 참) — [22번](../22-symbol-and-well-known-symbols/2-summary.md) 동작 (5-c)의 `[3]` 이 정본.
- ★ **`b.filter(() => true) === b` 는 false** — 늘 새 배열이다.

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js24b-25a-trap-grid.js` | ★★★ 메서드 17 × 쓰기 트랩 세 열 · 「던짐 N / M」·「쓰기 0 N / M」 | node20 1벌 + **node18 판도 싣는다**(갈린 블록) |
| `js24b-25b-pairs.js` | ★★★ 짝 넷의 반환값·`===`·원본 · 사슬 · 한 겹 복사 · 구멍 | node20 1벌 + **node18 판도 싣는다** |
| `js24b-25c-index-range.js` | ★★★ 인덱스 8 × (`with` · 대입) · `at` 과의 대응 | node20 1벌 + **node18 판도 싣는다** |
| `js24b-25d-reduce.js` | ★★★ 초기값 유무 · 빈 배열 · 구멍 · `reduceRight` | node20 1벌 + node18 대조 1벌(동일) |
| `js24b-25e-map-parseint.js` | ★★ 콜백 인자 · 기수 · 대안 둘 | node20 1벌 + node18 대조 1벌(동일) |
| `js24b-25f-comparator-throws.js` | ★★★ 비교가 던질 때 원본 · 비교 함수 검사 | node20 1벌 + **node18 판도 싣는다** |
| `js24b-25g-shapes.js` | ★ `slice` 인덱스 · `concat` 펼치기 · 새 배열 | node20 1벌 + node18 대조 1벌(동일) |
| `js24b-vdiff.sh` · `js24b-versions.sh` | 두 판이 갈린 탐침 수 · 출력이 **어느 판에서 나왔나** + 판별 기능 표(Chrome 포함) | 1벌씩 |

판별 블록이 Chrome 을 돌린 페이지 — 탐침 파일 이름을 주소의 `?` 뒤에 붙여 연다. `console.log` 를 가로채 줄이 늘 때마다 `<pre>` 를 다시 쓰고, `--dump-dom` 이 그것을 내보낸다.

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

- ★★ **비교 함수 호출 횟수와 순서**(`4` · `108`) — 명세는 "implementation-defined sequence".
- ★ **`get` 트랩 횟수** — 근거로 쓰지 않았다.
- ★★ **예외 문구 전부** — `Invalid index : 3` · `Reduce of empty array with no initial value` · `The comparison function must be either a function or undefined` · v18 의 `a.toSorted is not a function` · `[3,(intermediate value),1].toSorted is not a function`. **종류만 명세가 정한다.**

**비변형 메서드의 쓰기 0 · `sort` 의 정렬-뒤-되쓰기 · `with` 의 범위 조건 · `reduce` 의 `TypeError` 조건 · 복사 메서드의 구멍 채우기와 `ArrayCreate` · `map` 의 콜백 인자는 구현 의존이 아니다.**
어느 엔진에서도 같아야 한다.

**안 돌려 본 것 / 못 잰 것 / 부적용인 창**

- **안 돌려 본 것** — `TypedArray` 의 복사 메서드 · `receiver` 를 안 넘긴 트랩(7번) · 되쓰기 도중 `Set` 이 던지는 `sort`(동결 배열) · 파이썬 쪽 재실행(10번 문서 인용) · species 재측정(22번 인용).
- ★ **Chrome 에서 탐침은 안 돌렸다** — 이 주제의 기능은 전부 node 20 에 있다(판별 블록). Chrome 은 판별 블록에서만 돌았다.
- ★★★ **안 쟀다** — **성능 전부.** 「`toSorted` 는 복사라서 느리다」를 **한 줄도 쓰지 않았다.**
- ★★ **부적용인 창** — **③ 브랜드 태그**(결과 클래스는 22번 인용) · **진단의 `(행,열)`**(`SyntaxError` 가 없다).

**판이 올랐을 때 다시 돌려야 하는 것**

- ★★ **비교 함수 호출 횟수**(6번 `[0]`·`[2]`) — 정렬 알고리즘이 바뀌면 움직인다. 움직여도 명세 위반이 아니다. **원본 그대로라는 결론은 안 움직여야 한다.**
- ★ **예외 문구 전부.**
