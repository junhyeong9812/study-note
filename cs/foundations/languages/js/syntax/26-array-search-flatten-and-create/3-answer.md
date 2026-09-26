# js/syntax/26 — 배열 탐색·평탄화·생성: 「구멍을 누가 건너뛰고 누가 읽나 · 찾기는 무엇으로 비교하나 · 배열을 만드는 입구 넷」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **node v20.19.6**(기본 판) · **node v18.19.1**(대조) · **Google Chrome 151.0.7922.173**(8번) · x86-64 Linux 에서 실제로 돌려 얻은 것이고,
> 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 하나도 없다).
>
> ★★ **예외는 `e.constructor.name` 과 `e.message` 로만 찍었다** — 스택트레이스에는 절대 경로가 박혀 재현이 안 된다.
> ★★★ **이 주제의 node 탐침은 두 판에서 한 글자도 같았다** — 판이 갈린 블록이 없다(7번의 대조기).
>
> **이 파일이 인용하는 출력을 낸 소스** — 전문은 [1-question.md](1-question.md) 의 같은 번호 문항에 있다(7번의 소스만 여기 싣는다).
> `js24b-26a-hole-grid.js`(1번 · 9번 · 10번) · `js24b-26b-zero-and-nan.js`(2번 · 11번) · `js24b-26c-find-family.js`(3번 · 12번) · `js24b-26d-at.js`(4번) ·
> `js24b-26e-flat.js`(5번) · `js24b-26f-create.js`(6번) · `js24b-26x-node-fromasync.js` · `js24b-versions.sh` · `js24b-vdiff.sh`(7번) · `js24b-26g-fromasync.web.js`(8번).

## 정답

### 1. `[, 1]` × 스물아홉 줄 — **통설과 어긋난 줄은 `copyWithin` · `flat` · `flatMap`, `3 / 27`** ★★★

**출력**

```text
===== node20 js24b-26a-hole-grid.js (exit=0) =====
arr = [, 1]   (0 in arr) = false   length = 2

operation            edition  measured  rule    detail
forEach              ES5      skips     skips   
map                  ES5      skips     skips   [<hole>,1]
filter               ES5      skips     skips   [1]
some                 ES5      skips     skips   
every                ES5      skips     skips   
reduce               ES5      skips     skips   
indexOf(undefined)   ES5      skips     skips   -1
lastIndexOf(undef)   ES5      skips     skips   -1
slice()              ES3      skips     skips   [<hole>,1]
concat()             ES3      skips     skips   [<hole>,1]
reverse()            ES3      skips     skips   [1,<hole>]
sort()               ES3      skips     skips   [1,<hole>]
join('-')            ES3      (n/a)     skips   "-1"
for-in               ES3      skips     skips   
find                 ES2015   reads     reads   
findIndex            ES2015   reads     reads   
fill(0)              ES2015   reads     reads   [0,0]
copyWithin(1, 0)     ES2015   skips     reads   [<hole>,<hole>]  <- differs
keys()               ES2015   reads     reads   [0,1]
entries()            ES2015   reads     reads   [[0,null],[1,1]]
for-of               ES2015   reads     reads   
[...arr]             ES2015   reads     reads   [undefined,1]
Array.from(arr)      ES2015   reads     reads   [undefined,1]
includes(undefined)  ES2016   reads     reads   true
flat()               ES2019   skips     reads   [1]  <- differs
flatMap(x => [x])    ES2019   skips     reads   [1]  <- differs
at(0)                ES2022   (n/a)     reads   undefined
findLast             ES2023   reads     reads   
findLastIndex        ES2023   reads     reads   

rows where the edition rule misses: 3 / 27
```

**왜 그런가**

- ★★★ **ES3·ES5 열은 전부 `skips`** — `forEach`·`map`·`filter`·`some`·`every`·`reduce`·`indexOf`·`lastIndexOf`·`slice`·`concat`·`reverse`·`sort`·`for-in`. 반복 단계가 원소마다 `HasProperty` 를 먼저 묻는다.
- ★★★ **ES2015 이후인데 `skips` 인 셋** — `copyWithin` 은 `fromPresent` 가 거짓이면 **대상 자리를 지운다**(`[<hole>,<hole>]` — 구멍이 복사됐다). `flat`·`flatMap` 은 `FlattenIntoArray` 가 `exists` 를 묻는다(`[1]` — 구멍이 사라졌다).
- ★★ **돌려받는 배열** — `map`·`slice()`·`concat()`·`reverse()`·`sort()` 는 구멍을 **남긴다**(`sort` 는 끝으로 옮긴다). `filter`·`flat`·`flatMap` 은 **지운다**(`[1]`). `[...arr]`·`Array.from(arr)` 은 **`undefined` 로 채운다**(`[undefined,1]`).
- ★ `join('-')` 은 구멍을 **빈 글자**로 이어 `"-1"`. `at(0)` 은 `undefined` — 두 줄은 「건너뛰나」를 물을 거리가 없어 `(n/a)` 로 세지 않았다.
- 전부 명세가 정한 것이다. 예외도 흔들리는 칸도 없다.

### 2. `-0` 에서는 **안 갈리고** `NaN` 에서만 갈린다 — 배열은 **`-0` 을 그대로** 담는다 ★★

**출력**

```text
===== node20 js24b-26b-zero-and-nan.js (exit=0) =====
[1] searching for -0 in [0]
  [0].indexOf(-0)                             0
  [0].lastIndexOf(-0)                         0
  [0].includes(-0)                            true
[2] searching for 0 in [-0]
  [-0].indexOf(0)                             0
  [-0].includes(0)                            true
[3] which zero comes back
  Object.is([-0].find(x => x === 0), -0)      true
  Object.is([-0].at(0), -0)                   true
  [0, -0].findIndex(x => Object.is(x, -0))    1
[4] NaN, and the ways to find it
  [NaN].indexOf(NaN)                          -1
  [NaN].lastIndexOf(NaN)                      -1
  [NaN].includes(NaN)                         true
  [NaN].findIndex(Number.isNaN)               0
  [NaN].findIndex(x => x !== x)               0
[5] fromIndex -- the second argument
  [1, 2, 1].indexOf(1, 1)                     2
  [1, 2, 1].indexOf(1, -1)                    2
  [1, 2, 1].lastIndexOf(1, -2)                0
  [1, 2, 1].includes(1, 3)                    false
  [1, 2, 1].includes(1, -100)                 true
[6] strict comparison, no coercion
  ['1'].indexOf(1)                            -1
  ['1'].includes(1)                           false
  [[1]].includes([1])                         false
```

**왜 그런가**

- ★★ **`[1]`·`[2]`** — IsStrictlyEqual 과 SameValueZero 둘 다 `+0` 과 `-0` 을 같다고 본다. 그래서 `indexOf`·`lastIndexOf`·`includes` 가 전부 찾는다.
- ★★★ **`[3]`** — `find` 와 `at` 이 돌려준 값이 **`Object.is(…, -0)` 로 `true`**. 배열은 값을 바꾸지 않는다. 부호를 가려 찾으려면 `findIndex(x => Object.is(x, -0))`(`1`).
- ★★ **`[4]`** — `indexOf`·`lastIndexOf` 는 `-1`, `includes` 는 `true`(23번의 `NaN, NaN` 행과 같다). **인덱스를 돌려주는 것은 `findIndex(Number.isNaN)` 과 `findIndex(x => x !== x)`** — 둘 다 `0`.
- ★ **`[5]`** — 음수 `fromIndex` 는 `length + fromIndex` 에서 시작, 음수 방향으로 넘치면 0 으로 붙는다. `includes(1, 3)` 은 `length` 이상이라 **안 찾고** `false`.
- ★ **`[6]`** — 강제 변환이 없다(`'1'` ≠ `1`), 객체는 정체로 본다.

### 3. `find`·`findIndex` 는 **`[0,1]`**, `findLast`·`findLastIndex` 는 **`[4]`** 만 방문하고, `filter` 는 다섯 번 다 ★★

**출력**

```text
===== node20 js24b-26c-find-family.js (exit=0) =====
[1] predicate v > 10 on [5,12,8,130,44]
  find            result 12          visited indexes [0,1]
  findIndex       result 1           visited indexes [0,1]
  findLast        result 44          visited indexes [4]
  findLastIndex   result 4           visited indexes [4]
  filter          result [12,130,44] visited indexes [0,1,2,3,4]
[2] nothing matches
  find           undefined
  findIndex      -1
  findLast       undefined
  findLastIndex  -1
[3] a matching element whose value is undefined
  find(v => v === undefined)       undefined
  findIndex(v => v === undefined)  1
[4] the array grows during find -- how many calls?
  result undefined   calls 3   array now [1,2,3,10,20,30]
[5] an element is deleted during find
  values the predicate saw ["1","undefined","3"]
```

**왜 그런가**

- ★★★ **`[1]`** — 네 형제는 명세 `FindViaPredicate` 하나를 방향만 바꿔 쓴다(오름 · 내림). 맞는 순간 돌려준다. `filter` 는 전부 모아야 하므로 끝까지 간다.
- ★★ **`[2]`** — 값 쪽 `undefined`, 인덱스 쪽 `-1`.
- ★★★ **`[3]`** — `find` 는 `undefined` 를 **찾아서** 돌려줬다. 못 찾은 결과와 글자가 같다 — **판정할 수 없다.** `findIndex` 의 `1` 이 판정해 준다.
- ★★ **`[4]`** — 콜백 3번. 방문 범위는 첫 호출 전에 `len` 으로 정해진다. 배열은 그 사이 여섯 개가 됐다(`[1,2,3,10,20,30]`).
- ★★ **`[5]`** — 지운 자리도 방문하고 값은 `undefined` — note 의 "still visited and are either looked up from the prototype or are undefined".

### 4. `at` 은 **끝에서 세고 정수로 깎고**, `arr[-1]` 은 **`"-1"` 이라는 글자 키**다 ★★

**출력**

```text
===== node20 js24b-26d-at.js (exit=0) =====
[1] negative and out-of-range indexes
  i = 0   at(i) a           arr[i] a
  i = 2   at(i) c           arr[i] c
  i = -1  at(i) c           arr[i] undefined
  i = -3  at(i) a           arr[i] undefined
  i = -4  at(i) undefined   arr[i] undefined
  i = 3   at(i) undefined   arr[i] undefined
[2] non-integer arguments
  arr.at(1.7)                                         "b"
  arr.at(-1.7)                                        "c"
  arr.at('1')                                         "b"
  arr.at(NaN)                                         "a"
  arr.at()                                            "a"
  arr.at(-0)                                          "a"
  arr['1.7']                                          "<undefined>"
[3] what arr[-1] = v does
  length 3   keys ["0","1","2","-1"]   at(-1) c
[4] the same method on other receivers
  'abc'.at(-1)                                        "c"
  new Uint8Array([7, 8]).at(-1)                       8
  Array.prototype.at.call({ length: 2, 1: 'x' }, -1)  "x"
```

**왜 그런가**

- ★★ **`[1]`** — `at(-1)`·`at(-3)` 은 `c`·`a`, 괄호 접근은 `undefined`. 범위 밖(`-4`·`3`)은 두 쪽 다 `undefined`.
- ★★ **`[2]`** — `at` 은 `ToIntegerOrInfinity` 로 깎는다: `1.7` → 1(`b`), `-1.7` → −1(`c`), `'1'` → 1, `NaN`·없음·`-0` → 0(`a`). 괄호 접근 `arr['1.7']` 은 깎지 않아 `undefined`.
- ★★★ **`[3]`** — `w[-1] = "z"` 는 배열 인덱스가 아닌 **평범한 키** `"-1"` 을 만든다. `length 3` 그대로, `keys` 끝에 `"-1"`, `at(-1)` 은 여전히 `c`.
- ★ **`[4]`** — 문자열 `c`, 타입 배열 `8`, 유사 배열 `"x"`. 범용 메서드다.

### 5. `flatMap(x => [[x]])` 은 **`[[1],[2]]`** — 한 겹만. `flat` 은 **진짜 배열만** 편다 ★★

**출력**

```text
===== node20 js24b-26e-flat.js (exit=0) =====
nested = [1,[2,[3,[4,[5]]]]]
[1] depth argument
  flat(undefined) [1,2,[3,[4,[5]]]]
  flat(0        ) [1,[2,[3,[4,[5]]]]]
  flat(1        ) [1,2,[3,[4,[5]]]]
  flat(2        ) [1,2,3,[4,[5]]]
  flat(-1       ) [1,[2,[3,[4,[5]]]]]
  flat(Infinity ) [1,2,3,4,5]
  flat("2"      ) [1,2,3,[4,[5]]]
  flat(NaN      ) [1,[2,[3,[4,[5]]]]]
[2] flatMap -- callback returns
  flatMap(x => [x, x * 10])     [1,10,2,20]
  flatMap(x => [[x]])           [[1],[2]]
  flatMap(x => x)               [1,2]
  flatMap(x => [])              []
  map(x => [[x]]).flat(2)       [1,2]
[3] what counts as an array to flatten
  [[1], 'ab', spreadable].flat()   [1,"ab","<the object>"]
  [[1], 'ab', spreadable] concat   [1,"ab","p","q"]
  [new Set([1, 2])].flat()         ["<the Set>"]
[4] holes inside the nested arrays
  [[1, , 3], , [5]].flat()         [1,3,5]
[5] a very deep array with flat(Infinity)
  RangeError 「Maximum call stack size exceeded」
```

**왜 그런가**

- ★★ **`[1]`** — 기본 1 겹. `"2"` 는 2 로 바뀐다. `-1` 은 "If depthNum < 0, set depthNum to 0" 으로 0 겹, `NaN` 도 `ToIntegerOrInfinity` 에서 0 — 원래 모양 그대로.
- ★★★ **`[2]`** — `flatMap` 은 `FlattenIntoArray(…, 1, mapper, …)` 다. **깊이 1 로 고정** — 두 겹 배열은 한 겹만 벗는다. 배열이 아닌 반환값은 그대로 한 원소, `[]` 는 원소를 빼는 효과.
- ★★★ **`[3]`** — `flat` 은 `IsArray(element)` 로 묻는다. `isConcatSpreadable` 을 켠 객체도 `Set` 도 배열이 아니라 **그대로**. `concat` 은 `IsConcatSpreadable` 을 물어 **편다**(`"p","q"`).
- ★★ **`[4]`** — `[1,3,5]`. 바깥 자리 1 의 구멍과 안쪽 `[1, , 3]` 의 구멍이 둘 다 `HasProperty` 에서 걸러졌다.
- ★ **`[5]`** — `RangeError 「Maximum call stack size exceeded」`. `FlattenIntoArray` 가 재귀라 깊이만큼 스택을 쓴다. **명세에는 한계가 없다 — 이 판의 관찰이다.**

### 6. `Array(3)` 은 **구멍 셋**, `Array.of(3)` 은 **`[3]`**, `Array(3).map` 은 콜백을 **0번** 부른다 ★★★

**출력**

```text
===== node20 js24b-26f-create.js (exit=0) =====
[1] one argument to Array vs Array.of
  Array(3)                                [<hole>,<hole>,<hole>]
  Array.of(3)                             [3]
  Array('3')                              ["3"]
  Array(3, 4)                             [3,4]
  Array.of(3, 4)                          [3,4]
  Array(2.5)                              RangeError 「Invalid array length」
  Array(-1)                               RangeError 「Invalid array length」
  Array.of()                              []
[2] filling the slots of Array(3)
  Array(3).map(() => 0)                   [<hole>,<hole>,<hole>]
    callback calls                        0
  Array(3).fill(0)                        [0,0,0]
  [...Array(3)]                           [undefined,undefined,undefined]
  Array.from(Array(3))                    [undefined,undefined,undefined]
  Array.from({ length: 3 })               [undefined,undefined,undefined]
  Array.from({ length: 3 }, (_, i) => i)  [0,1,2]
  Array.apply(null, Array(3))             [undefined,undefined,undefined]
[3] what Array.from accepts
  Array.from('abc')                       ["a","b","c"]
  Array.from(new Set([1, 1, 2]))          [1,2]
  Array.from(new Map([[1, 'a']]))         [[1,"a"]]
  Array.from({ length: 2, 0: 'x' })       ["x",undefined]
  Array.from({ 0: 'x' })                  []
  Array.from(5)                           []
  Array.from(null)                        TypeError 「object null is not iterable (cannot read property Symbol(Symbol.iterator))」
  Array.from([1, 2], 'x')                 TypeError 「x is not a function」
[4] an object that is both iterable and array-like
  Array.from(both)                        ["iter-a"]
[5] the mapping function -- arguments and this
  ["p",0,2,"T"]
  ["q",1,2,"T"]
[6] Array.from called on a subclass
  Tagged.from([1]) instanceof Tagged      true
  Tagged.of(1) instanceof Tagged          true
```

**왜 그런가**

- ★★★ **`[1]`** — 명세 `Array ( ...values )` 는 인자가 **하나이고 Number** 일 때만 그것을 길이로 쓴다. `ToUint32(len)` 이 `len` 과 다르면(`2.5`·`-1`) `RangeError`. 글자 `'3'` 은 담는다. `Array.of` 는 언제나 담는다.
- ★★★ **`[2]`** — `Array(3)` 은 자리만 셋이고 프로퍼티가 없다. `map` 이 `HasProperty` 로 전부 건너뛰어 **콜백 0번**, 결과도 구멍 셋.
  `fill` 은 자리를 가리지 않고 쓴다. 스프레드·`Array.from`·`apply` 는 **`Get` 으로** 읽어 `undefined` 셋을 만든다 — 그다음부터는 구멍이 아니다.
- ★★ **`[3]`** — 문자열·`Set`·`Map` 은 이터레이터 경로. 유사 배열은 `length` 까지 `Get`(`["x",undefined]`), `length` 가 없거나 숫자면 0 → `[]`. `null` 은 이터레이터를 물을 수 없어 `TypeError`, 함수가 아닌 매핑 인자는 `TypeError`.
- ★★★ **`[4]`** — `GetMethod(items, %Symbol.iterator%)` 가 먼저다. 이터레이터가 있으면 `length` 와 인덱스는 **안 읽힌다**(`["iter-a"]`).
- ★★ **`[5]`** — 매핑 함수는 `(값, 인덱스)` **두 인자**, `this` 는 셋째 인자. **`[6]`** — `this` 가 생성자면 그것으로 만든다(`Tagged`).

### 7. **Chrome 151 에만 있다** — 근거는 `typeof` 줄이고, `Array.fromAsync` 는 **ES2026** ★★

**판별 블록**

```text
===== ./js24b-versions.sh (exit=0) =====
node 18.19.1  v8 10.2.154.26-node.28
  ES2015  Array.from / Array.of / fill / copyWithin   yes
  ES2015  find / findIndex                            yes
  ES2016  includes                                    yes
  ES2017  Object.values / Object.entries              yes
  ES2019  flat / flatMap                              yes
  ES2019  Object.fromEntries                          yes
  ES2022  Array.prototype.at                          yes
  ES2022  Object.hasOwn                               yes
  ES2023  findLast / findLastIndex                    yes
  ES2023  toSorted / toReversed / toSpliced / with    no
  ES2024  Object.groupBy                              no
  ES2024  Map.groupBy                                 no
  ES2026  Array.fromAsync                             no
node 20.19.6  v8 11.3.244.8-node.33
  ES2015  Array.from / Array.of / fill / copyWithin   yes
  ES2015  find / findIndex                            yes
  ES2016  includes                                    yes
  ES2017  Object.values / Object.entries              yes
  ES2019  flat / flatMap                              yes
  ES2019  Object.fromEntries                          yes
  ES2022  Array.prototype.at                          yes
  ES2022  Object.hasOwn                               yes
  ES2023  findLast / findLastIndex                    yes
  ES2023  toSorted / toReversed / toSpliced / with    yes
  ES2024  Object.groupBy                              no
  ES2024  Map.groupBy                                 no
  ES2026  Array.fromAsync                             no
Google Chrome 151.0.7922.173
  ES2015  Array.from / Array.of / fill / copyWithin   yes
  ES2015  find / findIndex                            yes
  ES2016  includes                                    yes
  ES2017  Object.values / Object.entries              yes
  ES2019  flat / flatMap                              yes
  ES2019  Object.fromEntries                          yes
  ES2022  Array.prototype.at                          yes
  ES2022  Object.hasOwn                               yes
  ES2023  findLast / findLastIndex                    yes
  ES2023  toSorted / toReversed / toSpliced / with    yes
  ES2024  Object.groupBy                              yes
  ES2024  Map.groupBy                                 yes
  ES2026  Array.fromAsync                             yes
```

**node 에서 불러 보면**

```text
===== node20 js24b-26x-node-fromasync.js (exit=0) =====
typeof Array.fromAsync   undefined
TypeError 「Array.fromAsync is not a function」
```

**두 node 판 대조기 — 이 주제의 탐침이 판마다 같았나**

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

**왜 그런가**

- ★★★ **판별 블록의 `ES2026  Array.fromAsync` 줄** — node 18 `no` · node 20 `no` · Chrome 151 `yes`. 그 줄은 `typeof Array.fromAsync === "function"` 을 묻는다(`js24b-features.js`).
- ★★ **없는 판에서 부르면 `TypeError 「Array.fromAsync is not a function」`** — `undefined` 를 부른 것이다. ★ 문구만으로 판정하지 않는다 — 23번에서 `getOrInsertComputed` 는 **메서드가 있는데도** 같은 모양의 문구를 냈다. **`typeof` 가 `undefined` 인 줄이 근거**다.
- ★ **판** — TC39 finished proposals 의 `Array.fromAsync` 행이 **2026** 이다. ECMA-262 **17판(2026)에 있고 16판(2025)에는 없다**(본문 검색). 목록 README 의 「`fromAsync`(ES2026)」와 **같다.**
- ★ **대조기** — `js24b-26…` 일곱 줄이 전부 `identical`. `DIFFERS` 줄은 **다른 주제의 탐침**이다(같은 배치가 한 대조기를 공유한다).

### 8. `Array.fromAsync` 는 **async function** 이고 한 값씩 `Await` 한다 ★★★

**출력**

```text
===== google-chrome --headless --virtual-time-budget=2000 --dump-dom 'js24b-page.html?js24b-26g-fromasync.web.js' | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' | sed 's/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&amp;/\&/g' (exit=0) =====
[1] return value of the call
  instanceof Promise  true
  resolved to         [1,2,3]
[2] a sync iterable whose items settle 30, 20, 10 ms after they are made
  Array.fromAsync(gen())    ["v0","v1","v2"]
                            next 0 | settle 0 | next 1 | settle 1 | next 2 | settle 2
  Promise.all([...gen()])   ["v0","v1","v2"]
                            next 0 | next 1 | next 2 | settle 2 | settle 1 | settle 0
[3] an async generator
  result [0,10,20]   pulled [0,1,2]
[4] the mapping function
  result ["aa","bb"]   mapper saw ["a",0] ["b",1]
[5] an array-like of promises
  ["x","y"]
[6] one item rejects -- what reaches the caller, and how far did it pull
  Error 「item 1」
  log ["next 0","next 1","finally ran"]
[7] a bad mapper -- thrown now, or a rejected promise?
  no exception during the call
  rejected: TypeError 「5 is not a function」
[8] not iterable, not array-like
  TypeError 「Cannot read properties of null (reading 'Symbol(Symbol.asyncIterator)')」
  []
done
```

**왜 그런가**

- ★★★ **`[2]`** — `fromAsync` 로그가 `next 0 | settle 0 | next 1 | settle 1 | next 2 | settle 2` 로 **번갈아** 간다. 동기 이터러블을 `CreateAsyncFromSyncIterator` 로 감싼 뒤 **값 하나를 `Await` 하고 나서** 다음 `next` 를 부르기 때문이다.
  `Promise.all([...gen()])` 은 스프레드가 **먼저 셋을 다 꺼내고**(`next 0 | next 1 | next 2`) 짧은 지연부터 정해진다(`settle 2 | settle 1 | settle 0`). **결과 배열은 같다** — 로그로만 갈린다.
- ★★★ **`[6]`** — 거부된 항목에서 멈춘다: `next 2` 가 없다. **`finally ran`** — 동기 이터레이터가 닫혔다. `AsyncFromSyncIteratorContinuation` 이 `closeOnRejection` 일 때 거부에서 `IteratorClose` 를 한다.
- ★★★ **`[7]`** — 호출 중에는 예외가 없고 **거부된 프라미스**로 `TypeError 「5 is not a function」` 이 온다. 명세가 이 메서드를 "This **async function** performs the following steps" 로 적는다 — 매핑 함수 검사(`IsCallable(mapper)`)도 async 본문 **안**에 있다.
- ★ 나머지 — `[1]` 프라미스를 돌려준다 · `[3]` 비동기 이터러블을 세 번 당겼다 · `[4]` 매핑 함수의 반환 프라미스도 기다린다 · `[5]` 유사 배열 · `[8]` `null` 거부, `5` 는 `[]`.
- ★ **시간은 근거가 아니다** — 가상 시간이다. 순서만 근거다(재대조 동일).

### 9. `includes` 는 **`HasProperty` 없이 `Get` 만** 한다 — note 가 「두 가지가 다르다」고 적는다 ★★★

- ★★★ note 원문 — "This method intentionally differs from the similar indexOf method in two ways. First, it uses the SameValueZero algorithm, instead of IsStrictlyEqual, allowing it to detect NaN array elements. Second, it does not skip missing array elements, instead treating them as undefined."
  **하나는 비교 규칙(`NaN`), 하나는 구멍이다.**
- ★★ **다른 한 줄** — `indexOf` 의 반복은 `Let kPresent be ? HasProperty(O, Pk)` → 참일 때만 `Get` 이다. `includes` 의 반복은 `HasProperty` 없이 곧바로 `Let elementK be ? Get(…)` 이다.
- ★ **1번 격자의 모든 줄이 이 한 줄로 설명된다** — `skips` 줄은 알고리즘에 `HasProperty` 가 있고(`FlattenIntoArray` 의 `exists`, `copyWithin` 의 `fromPresent`), `reads` 줄은 없다(`FindViaPredicate` 는 `Get` 만).

### 10. 어긋난 셋은 **새 판인데 `HasProperty` 를 묻는다** — 「판」 대신 「`HasProperty` 가 있나」로 외운다 ★★★

- ★★★ **공통점** — `copyWithin`(ES2015) · `flat`·`flatMap`(ES2019). 셋 다 알고리즘에 `HasProperty` 가 있다. `flat` 은 새 판이지만 **ES5 식 반복**(`forEach` 와 같은 `kPresent` 검사)을 따랐다.
- ★★ **한 문장** — 「**반복 단계에서 `HasProperty` 를 먼저 묻는 메서드가 구멍을 건너뛴다.** 판은 그 대부분과 겹칠 뿐이다」.
- ★ **이 격자가 못 보는 것** — 구멍이 **프로토타입에서 값을 얻는** 경우. `HasProperty` 는 체인까지 보므로 `Array.prototype[0]` 이 있으면 `skips` 쪽도 그 자리를 **방문**한다. 격자는 체인이 빈 배열만 봤다 — **그 탐침은 안 돌렸다.**

### 11. `Map` 은 **`+0` 으로 바꿔 저장**했고 배열은 **`-0` 을 그대로** 담는다 ★★

- ★★★ 23번 — `new Map([[-0, "x"]])` 의 첫 키가 `Object.is(k, -0)` **false**(`+0` 이다). 2번 — `Object.is([-0].at(0), -0)` 이 **true**.
- ★★ **차이는 `CanonicalizeKeyedCollectionKey` 가 있고 없어서**다 — `Map`/`Set` 은 입구에서 `-0` 을 `+0` 으로 접는다. 배열의 원소 쓰기에는 그런 연산이 없다. **비교 규칙(SameValueZero)은 같아도 저장된 값이 다르다.**

### 12. 3번의 `[0,1]` 과 21번의 `4 / 4` 는 **같은 사실**이다 — 「배열의 `find` 도 원래 멈춘다」 ★★

- ★★ 21번은 `find(x > 3)` 의 콜백을 배열판·헬퍼판 **둘 다 4번**으로 셌다 — 한 단계뿐이면 **배열판도 도중에 멈춘다.** 3번 `[1]` 의 `find` 가 방문 `[0,1]` 에서 멈춘 것이 같은 성질이다. 21번에서 배열판이 더 불린 것은 **`find` 앞에 `map` 이 있을 때**(`14 / 8`)다.
- ★★ **`findLast` 의 `visited indexes [4]`** — 첫 방문이 **마지막 인덱스**다. 오름차순이었다면 `[0,1,…]` 로 시작했을 것이다.
- ★ **「`find` 가 빠르다」는 「안 쟀다」 칸**이다 — 호출 수 2 대 5 는 셌고, 시간은 재지 않았다.

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js24b-26a-hole-grid.js` | ★★★ 구멍 하나 × 연산 스물아홉 줄 · 「통설이 어긋난 줄 3 / 27」 | node20 1벌 + node18 대조 1벌 |
| `js24b-26b-zero-and-nan.js` | ★★ `-0`·`NaN`·`fromIndex`·정체 비교 | node20 1벌 + node18 대조 1벌 |
| `js24b-26c-find-family.js` | ★★ 찾기 네 형제의 방문 인덱스 · 못 찾았을 때 · 도는 중 추가·삭제 | node20 1벌 + node18 대조 1벌 |
| `js24b-26d-at.js` | ★★ `at` 과 괄호 접근 · 인자 깎기 · `arr[-1]` 대입 | node20 1벌 + node18 대조 1벌 |
| `js24b-26e-flat.js` | ★★ 깊이 인자 · `flatMap` 한 겹 · `IsArray` · 안쪽 구멍 · 10만 겹 | node20 1벌 + node18 대조 1벌 |
| `js24b-26f-create.js` | ★★★ `Array(n)` · `Array.of` · `Array.from` 의 입력과 구멍 | node20 1벌 + node18 대조 1벌 |
| `js24b-26x-node-fromasync.js` | ★ node 두 판에 `Array.fromAsync` 가 없다 | node20 1벌 + node18 대조 1벌 |
| `js24b-26g-fromasync.web.js` | ★★★ `fromAsync` 의 `next`/`settle` 순서 · 거부 뒤 닫기 · async function 의 거부 | **Chrome 151 만** |
| `js24b-versions.sh` · `js24b-vdiff.sh` | 이 문서의 출력이 **어느 판에서 나왔나** + 판별 기능 표 · 두 판이 갈린 탐침 수 | 1벌씩 |

브라우저 탐침(8번)을 돌린 페이지 — 탐침 파일 이름을 주소의 `?` 뒤에 붙여 연다. `console.log` 를 가로채 줄이 늘 때마다 `<pre>` 를 다시 쓰고, `--dump-dom` 이 가상 시간 예산(`--virtual-time-budget=2000`)이 끝난 뒤 그것을 내보낸다.

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

- ★★ **10만 겹 `flat(Infinity)` 가 `RangeError` 인 것** — 명세에 한계가 없다. 스택 크기에 달렸다.
- ★★ **예외 문구 전부** — `Invalid array length` · `object null is not iterable (cannot read property Symbol(Symbol.iterator))` · `x is not a function` · `Maximum call stack size exceeded` ·
  `Array.fromAsync is not a function` · `5 is not a function` · `Cannot read properties of null (reading 'Symbol(Symbol.asyncIterator)')`. **종류만 명세가 정한다.**
- ★ **`Array.fromAsync` 가 Chrome 151 에 있고 node 18·20 에 없는 것** — 엔진의 도입 시점이다.

**격자의 `skips`/`reads` · 비교 규칙 · 방문 범위 · `at` 의 깎기 · `flat` 의 깊이와 `IsArray` · `Array` 생성자의 `RangeError` 조건 · `Array.from` 의 경로 순서와 매핑 인자 · `fromAsync` 의 한 값씩 `Await` 와 거부 뒤 닫기는 구현 의존이 아니다.**
어느 엔진에서도 같아야 한다.

**안 돌려 본 것 / 못 잰 것 / 부적용인 창**

- **안 돌려 본 것** — **구멍이 프로토타입에서 값을 얻는 경우**(10번) · 다른 엔진(SpiderMonkey·JavaScriptCore)의 문구 · 다른 스택 크기에서 `flat(Infinity)` 가 터지는 깊이.
- ★ **못 잰 것** — **`Array.fromAsync` 의 node 판 동작.** 두 node 판에 메서드가 없다(7번) — Chrome 151 로 창을 바꿨다.
- ★★★ **안 쟀다** — **성능 전부.** 「`find` 가 `filter` 보다 빠르다」·「`includes` 가 느리다」·「`flat` 이 비싸다」를 **한 줄도 쓰지 않았다.** 콜백 호출 수만 셌다.
- ★★ **부적용인 창** — **③ 브랜드 태그**(`flat` 의 `IsArray` 는 결과로 보인다) · **진단의 `(행,열)`**(`SyntaxError` 가 없다). **「잴 것이 없다」는 뜻**이다.

**판이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **node 22 이후의 판** — `Array.fromAsync` 가 들어온 판에서는 **8번을 node 로도** 돌린다. 판별 블록의 `no` 가 `yes` 로 바뀌는지 먼저 본다.
- ★★ **5번 `[5]`** — 스택 크기가 바뀌면 10만 겹이 통과할 수 있다. 통과해도 명세 위반이 아니다.
- ★ **예외 문구 전부.**
