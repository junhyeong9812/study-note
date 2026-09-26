# js/syntax/29 — 정규식 기본: 「`g` 정규식은 상태를 들고 다닌다 · `match` 는 `g` 로 모양이 바뀐다 · 리터럴은 평가마다 새 객체다」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **node v20.19.6**(기본 판) · **node v18.19.1**(대조) · **Python 3.12.3**(9번) · x86-64 Linux 에서 실제로 돌려 얻은 것이고,
> 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 하나도 없다).
>
> ★★ **예외는 `e.constructor.name` 과 `e.message` 로만** `이름 「메시지」` 꼴로 찍었다 — 스택트레이스에는 절대 경로가 박혀 재현이 안 된다.
> ★★ **두 node 판이 갈린 블록은 6번 하나**이고, 갈린 줄은 `v` 플래그(ES2024) 한 줄이다.
>
> **이 파일이 인용하는 출력을 낸 소스** — 전문은 [1-question.md](1-question.md) 의 같은 번호 문항에 있다.
> `js28b-29a-lastindex.js`(1번 · 7번) · `js28b-29b-match-shape.js`(2번) · `js28b-29c-matchall.js`(3번 · 10번) · `js28b-29d-replace-callback.js`(4번) ·
> `js28b-29e-literal-identity.js`(5번 · 7번) · `js28b-29f-flags.js`(6번) · `js28b-29h-literal-vs-constructor.js`(8번) · `js28b-29g-python.sh`(9번).

## 정답

### 1. **`true false true false`** — 찾으면 `lastIndex` 가 끝 위치로, 못 찾으면 **0** 으로 · `g` 가 없으면 `lastIndex` 를 안 쓴다 ★★★

**출력**

```text
===== node20 js28b-29a-lastindex.js (exit=0) =====
[1] one regexp /a/g, the same input 'a', four calls
  call 1  test('a')           lastIndex 0  -> test true  -> lastIndex 1
  call 2  test('a')           lastIndex 1  -> test false -> lastIndex 0
  call 3  test('a')           lastIndex 0  -> test true  -> lastIndex 1
  call 4  test('a')           lastIndex 1  -> test false -> lastIndex 0

[2] the same without g
  call 1  test('a')           lastIndex 0  -> test true  -> lastIndex 0
  call 2  test('a')           lastIndex 0  -> test true  -> lastIndex 0
  call 3  test('a')           lastIndex 0  -> test true  -> lastIndex 0

[3] /a/g on the input 'aa', four calls
  call 1  test('aa')          lastIndex 0  -> test true  -> lastIndex 1
  call 2  test('aa')          lastIndex 1  -> test true  -> lastIndex 2
  call 3  test('aa')          lastIndex 2  -> test false -> lastIndex 0
  call 4  test('aa')          lastIndex 0  -> test true  -> lastIndex 1

[4] a validator shared across a list -- filter(s => re.test(s))
  input  ["one","two","three","four"]
  kept   ["one","three"]
  kept, literal without g inside the callback  ["one","two","three","four"]

[5] setting lastIndex by hand, and an input shorter than lastIndex
  lastIndex = 5, test('aaa')  lastIndex 5  -> test false -> lastIndex 0
  lastIndex = 1, test('ab')   lastIndex 1  -> test false -> lastIndex 0
  then test('ba')             lastIndex 0  -> test true  -> lastIndex 2
```

**왜 그런가**

- ★★★ **`[1]`** — `0 → true → 1` · `1 → false → 0` · `0 → true → 1` · `1 → false → 0`. `call 2` 는 **1 번 위치부터** 찾아서 길이 1 인 입력에 남은 것이 없다. 못 찾으면 `lastIndex` 를 **0 으로 되돌리므로** `call 3` 은 처음부터다.
- ★★ **`[2]`** — `g` 가 없으면 **세 번 다 `true`, `lastIndex` 는 계속 0**. 명세가 `g`·`y` 없는 정규식은 `lastIndex` 를 0 으로 보고 **쓰지도 않는다.**
- ★★★ **`[3]`** — `true` · `true` · `false` · `true`. `'aa'` 에 매치가 **둘**이라 두 번 참이고, 세 번째에 끝에 닿아 **거짓 + 0**. 규칙은 「번갈아」가 아니라 **「매치 개수만큼 참, 그다음 한 번 거짓」** 이다.
- ★★★ **`[4]`** — `kept` 는 **`["one","three"]`**. `"one"` 뒤 `lastIndex` 3 → `"two"` 를 3 번부터 찾으니 `^` 가 안 맞아 거짓 + 0 → `"three"` 참 + 5 → `"four"`(길이 4)는 `lastIndex` 가 길이를 넘어 **찾기 전에** 거짓.
  마지막 줄 — 콜백 안에 **`g` 없는 리터럴**을 쓰면 넷 다 남는다(`["one","two","three","four"]`).
- ★★ **`[5]`** — `lastIndex = 5` 에 길이 3 → **바로 `false`, 0** · `lastIndex = 1` 에 `'ab'` → 1 번부터 `a` 가 없어 `false`, 0 · 그다음 `'ba'` 는 0 부터 훑어 **1 번의 `a`** 를 찾고 **`lastIndex 2`**.

### 2. `g` 없으면 **`exec` 결과**(길이 2 · `index` · `input` · `groups`), `g` 면 **글자 배열**(길이 3 · 나머지는 `undefined`) · 실패는 둘 다 `null` · `9 / 21` ★★★

**출력**

```text
===== node20 js28b-29b-match-shape.js (exit=0) =====
[1] 'a1b22'.match(re)
            /(\d)/        /(\d)/g       /(?<n>\d)/    /(?<n>\d)/g   /x/           /x/g
  returned  array         array         array         array         null          null
  length    2             3             2             3             -             -
  [0]       "1"           "1"           "1"           "1"           -             -
  [1]       "1"           "2"           "1"           "2"           -             -
  index     1             undefined     1             undefined     -             -
  input     "a1b22"       undefined     "a1b22"       undefined     -             -
  groups    undefined     undefined     {"n":"1"}     undefined     -             -

[2] the same regexps through exec, for comparison
  /(\d)/.exec    ["1","1"]  index 1
  /(\d)/g.exec   ["1","1"]  index 1

[3] match with a string argument
  'a.c'.match('.')    ["a"]  index 0
  'abc'.match()       [""]

cells where the g column differs from its pair without g: 9 / 21
```

**왜 그런가**

- ★★★ **`length`** — `g` 없음 **2**(전체 + 캡처 1), `g` **3**(매치 셋). **`[1]`** 도 뜻이 다르다 — `g` 없음은 **첫 캡처 `"1"`**, `g` 는 **두 번째 매치 `"2"`**.
- ★★★ **`index`·`input`·`groups`** — `g` 없음은 `1` · `"a1b22"` · (명명 그룹이 있으면) `{"n":"1"}`, **`g` 는 셋 다 `undefined`**. `g` 의 결과는 **글자만 모은 새 배열**이라 그 프로퍼티가 없다.
- ★★ **실패** — `/x/`·`/x/g` 둘 다 **`null`**(`-` 는 스크립트가 `null` 이라 못 읽은 칸이다).
- ★★ **`[2]`** — `exec` 는 `g` 가 있어도 **한 매치의 상세**다(`["1","1"]  index 1`). `g` 가 바꾸는 것은 `exec` 의 **`lastIndex` 쓰기**뿐이다(1번).
- ★★ **`[3]`** — `'a.c'.match('.')` 는 **`"a"`**(인덱스 0). 문자열이 **정규식으로 바뀌어** `.` 이 아무 글자다. `match()` 는 빈 패턴이라 `[""]`.
- ★ **`9 / 21`** — 세 짝(`(\d)` · `(?<n>\d)` · `x`) × 일곱 행. 실패 짝(`/x/` 대 `/x/g`)은 한 칸도 안 갈렸고, 나머지 두 짝에서 `length`·`[1]`·`index`·`input` 넷씩 + 명명 그룹 짝의 `groups` 하나.

### 3. `g` 없으면 **`TypeError`** · 돌려받는 것은 **`RegExp String Iterator`**(`return` 없음, 한 번 소비) · **복제본**이 넘긴 `lastIndex` 에서 시작하고 원래 것은 안 바뀐다 ★★★

**출력**

```text
===== node20 js28b-29c-matchall.js (exit=0) =====
[1] the argument
  matchAll(/\d/g)  first match                ["1"]
  matchAll(/\d/)                              TypeError 「String.prototype.matchAll called with a non-global RegExp argument」
  matchAll('\\d')                             ["1","2","2"]
  matchAll('.')                               ["a",".","c"]

[2] what comes back
  Object.prototype.toString.call(it)          [object RegExp String Iterator]
  Array.isArray(it)                           false
  typeof it.next / it.return                  function / undefined
  it[Symbol.iterator]() === it                true
  each element                                [{"all":"1","one":"1","index":1},{"all":"2","one":"2","index":3},{"all":"2","one":"2","index":4}]
  spread the same iterator again              []

[3] the regexp object that was passed in
  re.lastIndex right after matchAll()         2
  first match from the iterator               "2"
  re.lastIndex after pulling one              2
  remaining                                   ["2"]

[4] when does the search run, and on which object? (RegExp.prototype.exec wrapped with a counter)
  exec calls after matchAll()                 []
  exec calls after one next()                 ["another object"]
  exec calls after spreading the rest         ["another object","another object","another object","another object"]
```

**왜 그런가**

- ★★★ **`[1]`** — `/\d/g` 는 통과, **`/\d/` 는 `TypeError 「String.prototype.matchAll called with a non-global RegExp argument」`**. 문자열 `'\\d'`·`'.'` 은 **`g` 를 붙인 정규식**으로 바뀌어 통과한다(`["1","2","2"]` · `["a",".","c"]`).
- ★★★ **`[2]`** — 태그 **`[object RegExp String Iterator]`** · 배열 아님 · **`next` 는 있고 `return` 은 `undefined`** · 자기 자신이 이터러블. 매치 셋은 `index` 1·3·4 이고, **두 번째 펼치기는 `[]`** — 이미 끝까지 소비했다.
- ★★★ **`[3]`** — `re.lastIndex = 2` 로 넘기자 첫 매치가 **3 번의 `"2"`** 다(1 번의 `"1"` 을 건너뛰었다). 그런데 **`re.lastIndex` 는 `matchAll()` 직후에도, 하나 꺼낸 뒤에도 `2`** 다. 명세 `@@matchAll` 이 **복제본을 만들고 `lastIndex` 값만 옮겨 적는다.**
- ★★★ **`[4]`** — `matchAll()` 직후 `exec` **0번** → `next()` 한 번에 **1번** → 나머지 펼치기까지 **총 4번**(매치 셋 + 「더 없다」를 확인한 한 번). 전부 **`"another object"`** — 넘긴 객체가 아니라 **복제본의 `exec`** 다.
  **찾기는 `next()` 가 불릴 때마다 한 번씩** 일어난다 — 이터레이터를 만든 순간이 아니다.

### 4. **(전체, …캡처, 위치, 원본[, groups])** — 참여 안 한 그룹도 `undefined` 로 자리를 지키고, `groups` 는 명명 그룹이 있을 때만 붙는다 ★★

**출력**

```text
===== node20 js28b-29d-replace-callback.js (exit=0) =====
[1] a string pattern
  'x1y2'.replace('1', fn)
    call 1  3 args  ["1",1,"x1y2"]
    result "x_y2"

[2] a regexp with no groups, g flag
  'x1y2'.replace(/\d/g, fn)
    call 1  3 args  ["1",1,"x1y2"]
    call 2  3 args  ["2",3,"x1y2"]
    result "x_y_"

[3] two numbered groups, the second optional
  'x1a y2'.replace(/(\d)([a-z])?/g, fn)
    call 1  5 args  ["1a","1","a",1,"x1a y2"]
    call 2  5 args  ["2","2","<undefined>",5,"x1a y2"]
    result "x_ y_"

[4] the same with a named group
  'x1a y2'.replace(/(\d)(?<L>[a-z])?/g, fn)
    call 1  6 args  ["1a","1","a",1,"x1a y2",{"L":"a"}]
    call 2  6 args  ["2","2","<undefined>",5,"x1a y2",{"L":"<undefined>"}]
    result "x_ y_"

[5] what the callback returns
    returns undefined               -> "xundefinedyundefined"
    returns null                    -> "xnullynull"
    returns 42                      -> "x42y42"
    returns { toString: () => 'T' } -> "xTyT"
    returns '$&'                    -> "x$&y$&"
```

**왜 그런가**

- ★★★ **인자 수** — `[1]` 문자열 패턴 **3** · `[2]` 그룹 없는 정규식 **3**(매치마다 한 번, 두 번) · `[3]` 그룹 둘 **5** · `[4]` 그룹 둘 중 하나가 명명 **6**(끝에 `groups`).
- ★★ **둘째 호출의 선택 그룹 자리** — **`undefined`**(스크립트가 `<undefined>` 로 찍었다). `[4]` 의 `groups` 도 `{"L": undefined}` 다. **인자 수는 줄지 않는다** — 그래서 「위치」를 인자 번호로 찾으면 그룹 개수가 바뀔 때마다 코드가 깨진다.
- ★★ **위치는 원본 기준** — 둘째 호출이 `5` 다(첫 치환으로 문자열 길이가 바뀌었어도).
- ★★ **`[5]`** — 반환값은 **`ToString`** 만 한다. `undefined` → `"undefined"` · `null` → `"null"` · 객체 → `toString()` · **`'$&'` 는 글자 그대로**(`"x$&y$&"`). 28번 1번의 넷째 열과 같은 규칙이다.

### 5. 리터럴은 **평가마다 새 객체** · `RegExp(r)` 만 `r` 자신 · 복사는 `lastIndex` 를 안 옮긴다 · **`search` 는 `lastIndex` 를 무시하고 복원**한다 ★★★

**출력**

```text
===== node20 js28b-29e-literal-identity.js (exit=0) =====
[1] identity
  make() === make()                           false
  the literal in two loop turns: same object? false
  RegExp(r) === r                             true
  new RegExp(r) === r                         false
  RegExp(r, 'g') === r                        false

[2] a regexp at module level vs a literal inside the function
  hasShared('a') x3                           true false true
  hasLocal('a')  x3                           true true true

[3] copying a regexp -- does lastIndex come along?
  new RegExp(src).lastIndex                   0
  new RegExp(src).flags                       g
  new RegExp(src, 'i').flags                  i

[4] search -- given a g regexp with lastIndex set
  'abcb'.search(b)                            1
  b.lastIndex afterwards                      3
  b.exec('abcb').index   (for comparison)     3
```

**왜 그런가**

- ★★★ **`[1]`** — `false` · `false` · **`true`** · `false` · `false`. 리터럴은 **지날 때마다** `RegExpCreate` 다. `new` 없는 `RegExp(r)` 는 플래그가 없고 `r.constructor === RegExp` 이면 **`r` 을 그대로** 돌려준다. 플래그를 주거나 `new` 를 쓰면 새것이다.
- ★★★ **`[2]`** — **`true false true`** 대 **`true true true`**. 상태는 **객체**에 산다 — 모듈 수준 `SHARED` 는 세 호출이 한 객체를, 함수 안 리터럴은 호출마다 새 객체를 쓴다.
- ★★ **`[3]`** — 복사본의 `lastIndex` **0**, `flags` 는 `"g"` 그대로, 플래그를 주면 **대체**(`"i"`).
- ★★★ **`[4]`** — `search` 는 **`1`**(처음부터 찾았다), 뒤의 `lastIndex` 는 **`3`**(복원했다). 같은 객체의 `exec` 는 3 부터 찾아 `index 3`. `@@search` 는 **저장 → 0 → 찾기 → 복원**이다.

### 6. 글자마다 프로퍼티 하나 · `flags` 는 **`d g i m s u v y`** 순서 · 중복·모르는 글자·`u`+`v`·대문자는 `SyntaxError` · **node 18 에는 `v` 가 없다** ★★

**출력**

```text
===== node20 js28b-29f-flags.js (exit=0) =====
[1] one letter at a time -- .flags and the property that turns true
  new RegExp('a', 'g')                g   global
  new RegExp('a', 'i')                i   ignoreCase
  new RegExp('a', 'm')                m   multiline
  new RegExp('a', 's')                s   dotAll
  new RegExp('a', 'u')                u   unicode
  new RegExp('a', 'y')                y   sticky
  new RegExp('a', 'd')                d   hasIndices
  new RegExp('a', 'v')                v   unicodeSets

[2] several letters -- the order of .flags
  new RegExp('a', 'ymgi').flags       gimy
  /a/yigm.flags                       gimy
  new RegExp('a', 'dgimsuy').flags    dgimsuy

[3] letters the constructor may refuse
  new RegExp('a', 'gg')               SyntaxError 「Invalid flags supplied to RegExp constructor 'gg'」
  new RegExp('a', 'x')                SyntaxError 「Invalid flags supplied to RegExp constructor 'x'」
  new RegExp('a', 'uv')               SyntaxError 「Invalid flags supplied to RegExp constructor 'uv'」
  new RegExp('a', 'G')                SyntaxError 「Invalid flags supplied to RegExp constructor 'G'」

[4] what four of them change -- i, m, s, y
  /B/.test('abc')  /B/i.test('abc')   false  true
  'a\nb'.match(/^b/)  /^b/m           null  b
  /a.b/.test('a\nb')  /a.b/s          false  true
  /b/y.test('ab')  /b/g.test('ab')    false  true
  /b/y lastIndex=1 .test('ab')        true

[5] a subclass whose flags getter returns 'gi'
  new Loud('a').flags                 gi
  new Loud('a').global                false
  new RegExp(new Loud('a')).flags     
```

node 18 판(갈린 줄은 `[1]` 의 `v` 한 줄):

```text
===== node18 js28b-29f-flags.js (exit=0) =====
[1] one letter at a time -- .flags and the property that turns true
  new RegExp('a', 'g')                g   global
  new RegExp('a', 'i')                i   ignoreCase
  new RegExp('a', 'm')                m   multiline
  new RegExp('a', 's')                s   dotAll
  new RegExp('a', 'u')                u   unicode
  new RegExp('a', 'y')                y   sticky
  new RegExp('a', 'd')                d   hasIndices
  new RegExp('a', 'v')                SyntaxError 「Invalid flags supplied to RegExp constructor 'v'」

[2] several letters -- the order of .flags
  new RegExp('a', 'ymgi').flags       gimy
  /a/yigm.flags                       gimy
  new RegExp('a', 'dgimsuy').flags    dgimsuy

[3] letters the constructor may refuse
  new RegExp('a', 'gg')               SyntaxError 「Invalid flags supplied to RegExp constructor 'gg'」
  new RegExp('a', 'x')                SyntaxError 「Invalid flags supplied to RegExp constructor 'x'」
  new RegExp('a', 'uv')               SyntaxError 「Invalid flags supplied to RegExp constructor 'uv'」
  new RegExp('a', 'G')                SyntaxError 「Invalid flags supplied to RegExp constructor 'G'」

[4] what four of them change -- i, m, s, y
  /B/.test('abc')  /B/i.test('abc')   false  true
  'a\nb'.match(/^b/)  /^b/m           null  b
  /a.b/.test('a\nb')  /a.b/s          false  true
  /b/y.test('ab')  /b/g.test('ab')    false  true
  /b/y lastIndex=1 .test('ab')        true

[5] a subclass whose flags getter returns 'gi'
  new Loud('a').flags                 gi
  new Loud('a').global                false
  new RegExp(new Loud('a')).flags     
```

**왜 그런가**

- ★★ **`[1]`** — `g`→`global` · `i`→`ignoreCase` · `m`→`multiline` · `s`→`dotAll` · `u`→`unicode` · `y`→`sticky` · `d`→`hasIndices` · `v`→`unicodeSets`. **node 18 은 `v` 가 `SyntaxError 「Invalid flags supplied to RegExp constructor 'v'」`** — ES2024 이전 판이다.
- ★★ **`[2]`** — 셋 다 정해진 순서로 다시 적힌다(`"gimy"` · `"gimy"` · `"dgimsuy"`). `get flags` 가 **`d g i m s u v y` 순서로 프로퍼티를 하나씩 읽어** 잇기 때문이다.
- ★★★ **`[3]`** — 네 줄 다 **`SyntaxError`**(같은 문구 꼴 `Invalid flags supplied to RegExp constructor '…'`). 조용히 무시하는 글자는 없다.
- ★★ **`[4]`** — `i` `false  true` · `m` `null  b`(줄 머리의 `b`) · `s` `false  true` · **`y` 는 0 번에 `b` 가 없어 `false`, `g` 는 훑어서 `true`** · `y` 에 `lastIndex = 1` 이면 **1 번에 딱 붙은 `b`** 라 `true`.
- ★ **`[5]`** — `flags` 접근자는 `"gi"` 를 말하지만 **`global` 은 `false`**, `new RegExp(그것)` 의 `flags` 는 **빈 글자**. 둘 다 **내부 슬롯 `[[OriginalFlags]]`** 를 읽는다.

### 7. **`RegExpBuiltinExec`** — `g`·`y` 일 때만 읽고, **찾으면 끝 위치 · 못 찾으면 0 · 길이를 넘으면 0** 을 쓴다 ★★★

- ★★★ `exec`·`test` 는 `RegExpExec` → **`RegExpBuiltinExec(R, S)`** 를 부른다. 이 연산은 `[[OriginalFlags]]` 에 **`g` 나 `y`** 가 있을 때만 `lastIndex` 를 **시작점으로 읽는다.** 없으면 시작점이 0 이고 `lastIndex` 를 쓰지 않는다.
- ★★★ 쓰는 경우는 **셋** — ① `lastIndex` 가 **길이를 넘으면** 0 을 쓰고 `null`(1번 `[5]` 첫 줄) ② 끝까지 **못 찾으면** 0 을 쓰고 `null`(1번 `[1]` 의 `call 2`) ③ **찾으면** 매치의 **끝 위치**를 쓴다(`call 1` 의 `1`). `y` 는 ② 대신 **그 자리에서 못 찾는 즉시** 0 을 쓴다.
- ★★ **`search`** 는 저장 → 0 → 찾기 → **복원**(5번 `[4]`) · **`split`** 은 `y` 를 붙인 **새 정규식**으로 찾아 원래 것의 `lastIndex` 를 **안 건드린다**(28번 동작 (5)의 `[3]` — `3` 그대로).
- ★ **ES5**(ES3 은 리터럴 하나에 객체 하나였다). 1번 `[4]` 의 검증기는 **모듈 수준에 한 번 만든** 객체라 `lastIndex` 가 호출 사이로 샜고, 콜백 **안의** 리터럴은 호출마다 새 객체라 안 샜다.

### 8. 문자열 리터럴이 **먼저** 백슬래시를 읽는다 — `'\d'` 는 `d` · `source` 는 다시 쓸 수 있는 꼴 · 리터럴의 잘못된 패턴은 **파싱 때** ★★

**출력**

```text
===== node20 js28b-29h-literal-vs-constructor.js (exit=0) =====
[1] backslashes in a literal and in a string
  /\d/.source                             \d
  new RegExp('\\d').source                \d
  new RegExp('\d').source                 d
  new RegExp('\d').test('7')              false
  new RegExp('\d').test('d')              true
  new RegExp(String.raw`\d`).test('7')    true

[2] source and toString
  new RegExp('a/b').source                a\/b
  String(new RegExp('a/b', 'g'))          /a\/b/g
  new RegExp('').source                   (?:)
  new RegExp('\n').source                 "\\n"

[3] a user string used as a pattern
  new RegExp(user).test('1+1')            false
  new RegExp(user).test('11')             true
  new RegExp('(').test('(')               SyntaxError 「Invalid regular expression: /(/: Unterminated group」

[4] a bad pattern in a literal -- when is it reported?
  new Function('return 1; /(/')           SyntaxError 「Invalid regular expression: /(/: Unterminated group」
  new Function('if (false) /[/;')         SyntaxError 「Invalid regular expression: missing /」
```

- ★★★ **`new RegExp('\d')` 는 `'7'` 에 `false`** — ① 문자열 리터럴 `'\d'` 는 이스케이프로 뜻이 없는 `\d` 를 **`d` 한 글자**로 읽는다 ② 정규식은 패턴 **`d`** 를 받는다. 그래서 `'d'` 에 `true`. `'\\d'` 나 `` String.raw`\d` `` 를 쓰면 패턴이 `\d` 가 되어 `'7'` 에 `true` 다.
- ★★ **`source`** — `/` 는 **`\/`**, 빈 패턴은 **`(?:)`**, 줄바꿈은 **`\n` 두 글자**(`JSON` 으로 찍어 `"\\n"`). `String(re)` 가 `/source/flags` 를 만들어도 **다시 리터럴로 읽히는 꼴**이 되게 적는다.
- ★★ **`"1+1"`** — 「`1` 이 하나 이상, 그다음 `1`」 이라 `'1+1'` 에 **`false`**, `'11'` 에 **`true`**. `"("` 는 **`SyntaxError 「Invalid regular expression: /(/: Unterminated group」`**.
- ★★★ **`[4]`** — 두 줄 다 **`new Function` 이 실패**했다 — `return 1;` 뒤의 `/(/` 도, `if (false)` 안의 `/[/` 도 **실행될 일이 없는데** 난다. 리터럴의 패턴 검사는 **조기 오류**다. `new RegExp(…)` 는 그 줄이 **실행될 때** 던진다(`[3]`).

### 9. 파이썬 `re.match` 는 **앞에서만**, `re.search` 가 JS 의 `test`/`exec` 와 짝 · 파이썬 패턴 객체엔 **상태가 없다** ★★

**출력**

```text
===== ./js28b-29g-python.sh (exit=0) =====
[1] match / search / fullmatch on 'xa'
  re.match('a', 'xa')                     None
  re.search('a', 'xa').span()             (1, 2)
  re.fullmatch('x', 'xa')                 None

[2] one compiled pattern, the same input, three calls
  p.search('a') x3                        [True, True, True]
  hasattr(p, 'lastIndex')                 False
  p.search('aa', 1).span()                (1, 2)

[3] findall / finditer -- the counterparts of match(/g/) and matchAll
  re.findall(r'\d', 'a1b22')              ['1', '2', '2']
  re.findall(r'(\d)(\d)?', 'a1b22')       [('1', ''), ('2', '2')]
  [m.group() for m in it]                 ['1', '2', '2']
  the same iterator again                 []

[4] named groups
  re.search('(?P<n>\d)', 'a1').group('n') '1'
  re.search('(?<n>\d)', 'a1')             error 「unknown extension ?<n at position 1」
```

- ★★★ **`re.match('a', 'xa')` 는 `None`** — 앞에 붙어야 한다(JS 로는 `/^a/`). **`re.search`** 가 「어디서나」로 JS `test`·`exec` 와 짝이다(`(1, 2)`). `fullmatch` 는 `/^…$/`.
- ★★★ **세 번 다 `True`** — 파이썬 패턴 객체에는 **`lastIndex` 같은 상태가 없다**(`hasattr` 가 `False`). 시작 위치는 **인자**로 준다(`p.search('aa', 1)` → `(1, 2)`). JS 1번 `[1]` 의 `true false true false` 는 **객체에 상태가 있어서** 생긴다.
- ★★ **`findall(r'(\d)(\d)?', …)`** 은 **그룹의 튜플** `[('1', ''), ('2', '2')]` — 참여 안 한 그룹이 **`''`** 다(JS 는 `undefined`, 4번). 그룹이 없으면 전체 글자 목록이다.
- ★ **`(?<n>\d)` 는 `error 「unknown extension ?<n at position 1」`** — 파이썬 3.12 의 명명 그룹은 `(?P<n>…)` 다.

### 10. `return` 이 **없으므로** `break` 해도 아무것도 안 불린다 · 두 번째 펼치기가 `[]` 인 것이 「한 번 소비」 · `[Symbol.iterator]() === it` 은 이터레이터가 이터러블인 계약 ★★

- ★★ [19번](../19-iterable-protocol-and-for-of/2-summary.md)의 규칙대로 `for...of` 가 도중에 빠지면 `IteratorClose` 가 **`return` 메서드를 찾아 있으면** 부른다. 3번 `[2]` 에서 **`typeof it.return` 이 `undefined`** 였으니 **부를 것이 없다** — 닫을 자원도 없는 이터레이터다. (도중 `break` 실험은 이 문서가 따로 안 돌렸다 — `return` 이 없다는 줄이 근거다.)
- ★★ [21번](../21-iterator-helpers/2-summary.md)이 본 이터레이터처럼 **끝까지 당기면 다시 안 돈다.** 3번 `[2]` 의 `spread the same iterator again  []` 이 그것이다. `matchAll` 을 **다시 불러** 새 이터레이터를 받는다.
- ★ 19번의 「이터레이터는 `[Symbol.iterator]()` 가 자기 자신을 돌려주는 이터러블이다」 — `%IteratorPrototype%` 을 물려받은 결과다.

### 11. 치환 **표기**는 28번 · 치환 **함수 인자**는 29번 · 명명 그룹 **문법**과 `u`/`v` 는 30번 · 찾는 **알고리즘**은 `cs/algorithm/25-string-matching/` — 명세는 알고리즘을 안 정한다 ★★

- ★★ `$1`·`$<g>` 는 [28번](../28-string-methods-and-template-literals/2-summary.md) 동작 (1)이 정본이다. 콜백이 받는 `(전체, …캡처, 위치, 원본[, groups])` 는 이 문서 4번이다.
- ★★ [30번](../30-regexp-advanced/2-summary.md) — 명명 그룹의 문법과 `groups` 객체의 성질, `u`/`v` 가 서로게이트를 어떻게 보나, 백트래킹.
- ★★ [`cs/algorithm/25-string-matching/`](../../../../../algorithm/25-string-matching/2-summary.md)(나이브·KMP). **명세는 패턴이 무엇과 맞는가(의미)만** 정하고, 그것을 어떤 알고리즘으로 찾을지는 **엔진**의 몫이다(V8 은 Irregexp).

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js28b-29a-lastindex.js` | ★★★ `lastIndex` 전·후 로그 · `g` 유무 · 매치 둘 · 검증기 공유 · 손으로 쓴 `lastIndex` | node20 1벌 + node18 대조 1벌 |
| `js28b-29b-match-shape.js` | ★★★ `match` 여섯 경우 × 속성 일곱 · 「9 / 21」 · `exec` 대비 · 문자열 인자 | node20 1벌 + node18 대조 1벌 |
| `js28b-29c-matchall.js` | ★★★ `g` 필수 · 이터레이터 태그와 `return` 부재 · 한 번 소비 · 복제본과 `lastIndex` · `exec` 호출 로그 | node20 1벌 + node18 대조 1벌 |
| `js28b-29d-replace-callback.js` | ★★ 콜백 인자 수·순서 · `undefined` 자리 · `groups` · 반환값 `ToString` | node20 1벌 + node18 대조 1벌 |
| `js28b-29e-literal-identity.js` | ★★★ 리터럴 동일성 · `RegExp(r)` · 상태 공유 · 복사 · `search` 복원 | node20 1벌 + node18 대조 1벌 |
| `js28b-29f-flags.js` | ★★ 플래그 글자·프로퍼티·순서·거절 · `i m s y` 의 뜻 · `[[OriginalFlags]]` | node20 1벌 + **node18 1벌(갈린 판)** |
| `js28b-29h-literal-vs-constructor.js` | ★★ 백슬래시 두 단계 · `source` · 사용자 문자열 · 리터럴 조기 오류 | node20 1벌 + node18 대조 1벌 |
| `js28b-29g-python.sh` | ★★ 파이썬 `re` 대비 | Python 3.12.3 1벌 |
| `js28b-vdiff.sh` · `js28b-versions.sh` | 두 판이 갈린 탐침 수 · 이 문서의 출력이 **어느 판에서 나왔나** + 판별 기능 표 | 1벌씩 |

두 node 판 대조기(이 배치 전체의 node 탐침). 이 주제의 줄(`js28b-29…`)은 `js28b-29f-flags.js` 하나만 `DIFFERS` 다. 그 밖의 `DIFFERS` 줄은 **다른 주제의 탐침**이다(같은 배치가 한 대조기를 공유한다).

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

- ★ **다시 돌릴 것** — node 판이 오르면 `js28b-29f-flags.js` 의 `v` 줄 · 예외 **문구** 전부(V8 의 글자). 파이썬 판이 오르면 `js28b-29g` 의 `error` 줄(예외 **이름**이 판에 매이는 칸이다).
- ★ **흔들린 칸** — 이 주제의 블록에는 없다(재대조 동일).
