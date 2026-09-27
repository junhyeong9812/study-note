# js/syntax/28 — `String` 메서드와 템플릿 리터럴: 「치환 문자열은 작은 언어다 · 태그는 같은 종이를 받는다 · 자르기 셋은 음수에서 갈린다」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **node v20.19.6**(기본 판) · **node v18.19.1**(대조) · **Python 3.12.3**(9번) · x86-64 Linux 에서 실제로 돌려 얻은 것이고,
> 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 하나도 없다).
>
> ★★ **예외는 `e.constructor.name` 과 `e.message` 로만** `이름 「메시지」` 꼴로 찍었다 — 스택트레이스에는 절대 경로가 박혀 재현이 안 된다.
> ★★ **두 node 판이 갈린 블록은 4번 하나**이고, 갈린 줄은 `isWellFormed`(ES2024) 한 줄이다.
>
> **이 파일이 인용하는 출력을 낸 소스** — 전문은 [1-question.md](1-question.md) 의 같은 번호 문항에 있다.
> `js28b-28a-dollar-grid.js`(1번 · 7번) · `js28b-28b-replace-all.js`(2번) · `js28b-28c-tagged.js`(3번 · 8번) · `js28b-28d-slice-substring.js`(4번 · 10번) ·
> `js28b-28e-split.js`(5번) · `js28b-28f-pad-trim-search.js`(6번 · 11번) · `js28b-28g-python.sh`(9번).

## 정답

### 1. 치환 **문자열**만 `$` 를 읽는다 — `$&`·`` $` ``·`$'`·`$$` 는 늘, `$n` 은 그 그룹이 있을 때, `$<이름>` 은 명명 그룹이 있을 때 · 함수 열은 전부 글자 그대로 · `20 / 44` ★★★

**출력**

```text
===== node20 js28b-28a-dollar-grid.js (exit=0) =====
[1] replacement  string pattern   /(b)/            /(?<g>b)/        /(?<g>b)/ + fn
    [$&]         "a[b]c"          "a[b]c"          "a[b]c"          "a[$&]c"
    [$`]         "a[a]c"          "a[a]c"          "a[a]c"          "a[$`]c"
    [$']         "a[c]c"          "a[c]c"          "a[c]c"          "a[$']c"
    [$$]         "a[$]c"          "a[$]c"          "a[$]c"          "a[$$]c"
    [$1]         "a[$1]c"         "a[b]c"          "a[b]c"          "a[$1]c"
    [$01]        "a[$01]c"        "a[b]c"          "a[b]c"          "a[$01]c"
    [$10]        "a[$10]c"        "a[b0]c"         "a[b0]c"         "a[$10]c"
    [$9]         "a[$9]c"         "a[$9]c"         "a[$9]c"         "a[$9]c"
    [$0]         "a[$0]c"         "a[$0]c"         "a[$0]c"         "a[$0]c"
    [$<g>]       "a[$<g>]c"       "a[$<g>]c"       "a[b]c"          "a[$<g>]c"
    [$<x>]       "a[$<x>]c"       "a[$<x>]c"       "a[]c"           "a[$<x>]c"

[2] the same template through replaceAll and split-join
    'a.b.c'.replaceAll('.', '$&$&')     "a..b..c"
    'a.b.c'.split('.').join('$&$&')     "a$&$&b$&$&c"

[3] a replacement that comes from outside -- a price string
    'cost: X'.replace('X', price)        "cost: $5"
    'cost: X'.replace('X', '$&0')        "cost: X0"
    'cost: X'.replace('X', () => '$&0')  "cost: $&0"

cells where the output differs from the plain text of the template: 20 / 44
```

**왜 그런가**

- ★★★ **넷째 열(함수)은 11줄 전부 글자 그대로**다. 치환 함수의 반환값은 `ToString` 만 거치고 **`GetSubstitution` 을 안 거친다**(7번).
- ★★★ **앞 세 열의 `$&`·`` $` ``·`$'`·`$$`** — 찾은 것 `b` · 그 앞 `a` · 그 뒤 `c` · `$` 한 글자. 캡처가 없어도 뜻이 있는 표기라 **문자열 패턴에서도** 읽힌다.
- ★★★ **둘째 열의 `[$1]` 은 `"a[b]c"`, `[$10]` 은 `"a[b0]c"`, `[$9]` 는 `"a[$9]c"`**.
  그룹이 **1개**다. `$10` 은 두 자리 `10` 번이 없어서 **한 자리 `1` 번 + 글자 `0`** 으로 읽혔다. `$9` 는 한 자리로도 없는 번호라 **글자 그대로**다. `$01` 은 두 자리 `01` = 1번이다.
- ★★ **`[$0]` 은 세 열 다 글자 그대로** — `0` 은 그룹 번호가 아니다(`$&` 가 그 자리를 맡는다).
- ★★★ **셋째 열의 `[$<g>]` 는 `"a[b]c"`, `[$<x>]` 는 `"a[]c"`**. 명명 그룹이 **있는** 정규식이라 `$<…>` 를 이름으로 찾고, 없는 이름 `x` 는 **빈 글자**다.
  둘째 열(명명 그룹 없음)에서는 둘 다 **글자 그대로**다 — 명명 캡처 객체가 `undefined` 면 `$<` 를 읽지 않는다.
- ★★ **`[2]`** — `replaceAll` 은 같은 양식을 읽어 `"a..b..c"`, `split().join()` 은 `"a$&$&b$&$&c"` 다. `join` 의 인자는 **치환 문자열이 아니다.**
- ★★★ **`[3]`** — `"$5"` 는 **그룹 5 가 없어서** 그대로 들어갔다(`"cost: $5"`). `"$&0"` 은 **`"cost: X0"`** — 바깥에서 온 글자가 표기로 읽혔다. 함수로 감싸면 `"cost: $&0"`.
- ★ **`20 / 44`** — 표기 11 × 자리 4 = 44칸 중 20칸이 `"a" + 표기 + "c"` 와 달랐다. 앞 세 열에서만 나왔다(넷째 열은 0칸).

### 2. `replace` 는 **첫 하나**, `replaceAll` 은 **전부** — 정규식에 `g` 가 없으면 `replaceAll` 은 `TypeError` ★★★

**출력**

```text
===== node20 js28b-28b-replace-all.js (exit=0) =====
[1] a string pattern
  'a-b-c'.replace('-', '+')             "a+b-c"
  'a-b-c'.replaceAll('-', '+')          "a+b+c"
  'a-b-c'.split('-').join('+')          "a+b+c"

[2] a regexp pattern, with and without g
  'a-b-c'.replace(/-/, '+')             "a+b-c"
  'a-b-c'.replace(/-/g, '+')            "a+b+c"
  'a-b-c'.replaceAll(/-/g, '+')         "a+b+c"
  'a-b-c'.replaceAll(/-/, '+')          TypeError 「String.prototype.replaceAll called with a non-global RegExp argument」

[3] the empty string as the pattern
  'abc'.replace('', '-')                "-abc"
  'abc'.replaceAll('', '-')             "-a-b-c-"

[4] overlapping candidates -- 'aaa' with 'aa'
  'aaa'.replaceAll('aa', 'X')           "Xa"
  'aaa'.split('aa')                     ["","a"]

[5] what the replacer function receives for a string pattern
  calls                                 [["-",1,"x-y-z"],["-",3,"x-y-z"]]

[6] the pattern is not a string or a regexp
  'a1b1'.replaceAll(1, '_')             "a_b_"
  'anullb'.replace(null, '_')           "a_b"
  'a.b'.replaceAll('.', undefined)      "aundefinedb"
```

**왜 그런가**

- ★★★ **`[1]`** — `replace('-', '+')` 는 `"a+b-c"`(첫 하나), `replaceAll` 과 `split().join()` 은 `"a+b+c"`.
- ★★★ **`[2]`** — `replace(/-/)` 는 하나, `replace(/-/g)` 는 전부 · `replaceAll(/-/g)` 는 전부 · **`replaceAll(/-/)` 는 `TypeError 「String.prototype.replaceAll called with a non-global RegExp argument」`**.
  「전부」를 정하는 것은 정규식이면 **`g`** 이고, `replaceAll` 은 그 `g` 가 없으면 **바꾸기 전에** 던진다.
- ★★ **`[3]`** — 빈 패턴에 `replace` 는 맨 앞 **한 곳**(`"-abc"`), `replaceAll` 은 **위치마다**(`"-a-b-c-"`, 네 곳).
- ★★ **`[4]`** — `"Xa"`. 찾은 뒤 **그 길이만큼 건너뛰므로** 겹치는 두 번째 후보(1번 위치의 `aa`)는 안 본다. `split('aa')` 도 `["","a"]` 로 같다.
- ★★ **`[5]`** — 두 번, 인자 **셋**: `["-",1,"x-y-z"]` · `["-",3,"x-y-z"]`(찾은 글자 · 위치 · 원본).
- ★ **`[6]`** — 패턴 `1` 은 `"1"`, `null` 은 `"null"` 로 `ToString` 된다(`"a_b_"` · `"a_b"`). 치환 인자 `undefined` 는 글자 `"undefined"` 로 들어간다(`"aundefinedb"`).

### 3. `strings` 는 **소스 자리마다 하나이고 동결**돼 있다 · 태그가 있으면 잘못된 이스케이프가 `cooked: undefined` 로 허용된다 ★★★

**출력**

```text
===== node20 js28b-28c-tagged.js (exit=0) =====
[1] what the tag receives
  strings                                         ["a","b","c"]
  strings.raw                                     ["a","b","c"]
  subs                                            [1,"two"]
  strings.length vs subs.length                   3 vs 2
  Array.isArray(strings)                          true
  Object.isFrozen(strings)                        true
  Object.isFrozen(strings.raw)                    true
  keep`${1}`.strings                              ["",""]

[2] the strings object across calls
  site() === site()                               true
  site() === other()   (same text, other place)   false
  three loop turns, same object?                  true
  new Function each time: equal?                  false
  writing strings[0]                              TypeError 「Cannot assign to read only property '0' of object '[object Array]'」

[3] String.raw
  String.raw`a\nb`.length                         4
  `a\nb`.length                                   3
  String.raw`C:\dir\${'x'}`                       [C:\dir\${"x"}]
  String.raw({ raw: ['x', 'y', 'z'] }, 1, 2, 3)   [x1y2z]
  String.raw({ raw: 'abc' }, '-', '-')            [a-b-c]

[4] an escape that is not a valid escape
  tag receives -- cooked                          undefined
  tag receives -- raw                             [\unicode and \xZ]
  the same text without a tag                     SyntaxError 「Invalid Unicode escape sequence」
  String.raw with it                              [\unicode and \xZ]
```

**왜 그런가**

- ★★★ **`[1]`** — `strings` 3개 대 `subs` 2개(**늘 하나 더 많다**). `${}` 로 시작·끝나면 양 끝에 빈 조각이 생긴다(``keep`${1}` `` → `["",""]`). **`strings` 와 `raw` 둘 다 얼어 있고**, 평범한 배열이다(`Array.isArray` 가 `true`).
- ★★★ **`[2]`** — `site() === site()` **`true`** · 다른 자리 `false` · 루프 세 바퀴 `true` · `new Function` 두 번 `false`.
  같은 객체를 정하는 것은 「글자」가 아니라 「**소스의 자리**」다. `new Function` 은 부를 때마다 소스를 새로 파싱하니 자리도 새것이다(8번).
- ★★ **`[2]` 쓰기** — 엄격 코드에서 `TypeError 「Cannot assign to read only property '0' of object '[object Array]'」`. 얼어 있다.
- ★★★ **`[3]`** — ``String.raw`a\nb` `` 는 4 글자(`\` 와 `n`), 그냥 템플릿은 3 글자. ★ **``String.raw`C:\dir\${"x"}` `` 에서 `${"x"}` 는 치환이 안 됐다** — `\$` 가 `$` 를 이스케이프했다. `raw` 는 그 이스케이프를 **푼 뒤의 값이 아니라 소스 글자**를 담지만, **치환 자리를 정하는 것은 파서**라서 `\${` 는 처음부터 치환이 아니다.
  `String.raw({ raw: ['x','y','z'] }, 1, 2, 3)` 은 `[x1y2z]` — 조각 사이에만 값이 들어가고 **남는 값 `3` 은 버려진다.**
- ★★★ **`[4]`** — 태그가 있으면 **`cooked` 는 `undefined`, `raw` 는 `\unicode and \xZ`**. 태그가 없으면 **`SyntaxError 「Invalid Unicode escape sequence」`**. `String.raw` 는 태그라서 통과한다.

### 4. `slice` 는 음수를 뒤에서, `substring` 은 0 으로 깎고 뒤집는다 — **`5 / 10`** · `at` 도 코드 유닛 단위 ★★★

**출력**

```text
===== node20 js28b-28d-slice-substring.js (exit=0) =====
[1] 'abcdef' -- slice / substring / substr
  args            slice      substring  substr
  (2)             "cdef"     "cdef"     "cdef"
  (-2)            "ef"       "abcdef"   "ef"
  (2, 4)          "cd"       "cd"       "cdef"
  (4, 2)          ""         "cd"       "ef"
  (-3, -1)        "de"       ""         ""
  (2, -1)         "cde"      "ab"       ""
  (-1, 2)         ""         "ab"       "f"
  (NaN, 3)        "abc"      "abc"      "abc"
  (undefined, 3)  "abc"      "abc"      "abc"
  (2, 100)        "cdef"     "cdef"     "cdef"

[2] at and bracket access
  i = 0       at "a"         s[i] "a"
  i = 5       at "f"         s[i] "f"
  i = 6       at undefined   s[i] undefined
  i = -1      at "f"         s[i] undefined
  i = -6      at "a"         s[i] undefined
  i = -7      at undefined   s[i] undefined
  i = 1.7     at "b"         s[i] undefined
  i = "1"     at "b"         s[i] "b"

[3] the same calls on a string with a code point outside the BMP (built with fromCodePoint)
  length 4   code units 61 d83d de00 62
  slice(0, 2)  code units 61 d83d   isWellFormed false
  at(1)        code units d83d
  at(-2)       code units de00

rows where slice and substring disagree: 5 / 10
```

node 18 판(갈린 줄은 `[3]` 의 둘째 줄 하나):

```text
===== node18 js28b-28d-slice-substring.js (exit=0) =====
[1] 'abcdef' -- slice / substring / substr
  args            slice      substring  substr
  (2)             "cdef"     "cdef"     "cdef"
  (-2)            "ef"       "abcdef"   "ef"
  (2, 4)          "cd"       "cd"       "cdef"
  (4, 2)          ""         "cd"       "ef"
  (-3, -1)        "de"       ""         ""
  (2, -1)         "cde"      "ab"       ""
  (-1, 2)         ""         "ab"       "f"
  (NaN, 3)        "abc"      "abc"      "abc"
  (undefined, 3)  "abc"      "abc"      "abc"
  (2, 100)        "cdef"     "cdef"     "cdef"

[2] at and bracket access
  i = 0       at "a"         s[i] "a"
  i = 5       at "f"         s[i] "f"
  i = 6       at undefined   s[i] undefined
  i = -1      at "f"         s[i] undefined
  i = -6      at "a"         s[i] undefined
  i = -7      at undefined   s[i] undefined
  i = 1.7     at "b"         s[i] undefined
  i = "1"     at "b"         s[i] "b"

[3] the same calls on a string with a code point outside the BMP (built with fromCodePoint)
  length 4   code units 61 d83d de00 62
  slice(0, 2)  code units 61 d83d   isWellFormed (no method)
  at(1)        code units d83d
  at(-2)       code units de00

rows where slice and substring disagree: 5 / 10
```

**왜 그런가**

- ★★★ **`(-2)`** — `slice` `"ef"` · **`substring` `"abcdef"`**(음수 → 0) · `substr` `"ef"`(시작만 뒤에서 센다).
- ★★★ **`(4, 2)`** — `slice` `""`(시작이 끝보다 뒤) · **`substring` `"cd"`**(뒤집는다) · `substr` `"ef"`(4부터 2글자).
- ★★★ **`(2, -1)`** — `slice` `"cde"` · **`substring` `"ab"`**(`-1` → 0, 그다음 `(2, 0)` 을 `(0, 2)` 로 뒤집는다) · `substr` `""`(길이가 음수 → 0).
- ★★ **`(-3, -1)`** 과 **`(-1, 2)`** 도 `slice` 와 `substring` 이 갈린 줄이다 — 다섯 줄 모두 **음수가 있거나 시작이 끝보다 크다.** 나머지 다섯 줄(양수이고 순서가 맞거나, `NaN`·`undefined`·넘치는 끝)은 `slice` 와 `substring` 이 같다(`substr` 은 `(2, 4)` 에서 따로 `"cdef"` 다 — 둘째 인자가 길이라서).
- ★★★ **`[2]`** — `at` 과 `s[i]` 는 **`-1`·`-6`·`1.7` 에서 갈린다.** 대괄호는 `"-1"`·`"1.7"` 이라는 **이름의 프로퍼티**를 찾아 `undefined`, `at` 은 **정수로 깎고 음수를 뒤에서** 센다. `"1"` 은 둘 다 `"b"` 다(문자열 키 `"1"` 이 곧 인덱스).
- ★★★ **`[3]`** — `slice(0, 2)` 는 **`61 d83d`**(쌍의 앞 반쪽에서 끊겼다) · `at(1)` 은 **`d83d`** · `at(-2)` 는 **`de00`**. `at` 은 **코드 유닛 하나**를 돌려준다.
- ★ **`isWellFormed` 칸은 두 판이 다르다** — node 20 `false`, node 18 `(no method)`. ES2024 메서드가 node 18 에 없다. 나머지 줄은 한 글자도 같다.
- ★ **`5 / 10`** — 스크립트가 센 `slice` ≠ `substring` 인 줄 수.

### 5. 캡처 그룹은 **결과에 끼어들고**, 참여 안 한 그룹은 **`undefined` 로** 끼어든다 · `split` 은 `lastIndex` 를 안 쓰고 안 바꾼다 ★★

**출력**

```text
===== node20 js28b-28e-split.js (exit=0) =====
[1] separators
  'a1b22c'.split('2')                 ["a1b","","c"]
  'a1b22c'.split(/\d/)                ["a","b","","c"]
  'a1b22c'.split(/\d+/)               ["a","b","c"]
  'a1b22c'.split(/(\d)/)              ["a","1","b","2","","2","c"]
  'a1b22c'.split(/(\d)+/)             ["a","1","b","2","c"]
  'a1b-c'.split(/(\d)|(-)/)           ["a","1","<undefined>","b","<undefined>","-","c"]
  'a1b-c'.split(/(?:\d|-)/)           ["a","b","c"]

[2] ends, empties and limits
  ',a,,b,'.split(',')                 ["","a","","b",""]
  ''.split(',')                       [""]
  ''.split('')                        []
  'abc'.split('')                     ["a","b","c"]
  'abc'.split()                       ["abc"]
  'a,b,c'.split(',', 2)               ["a","b"]
  'a1b2c'.split(/(\d)/, 2)            ["a","1"]
  'abc'.split(/(?:)/)                 ["a","b","c"]

[3] does split look at lastIndex or the g flag?
  'a,b,c'.split(/,/g)  lastIndex=3    ["a","b","c"]
    g.lastIndex afterwards            3
```

**왜 그런가**

- ★★★ **`[1]`** — 괄호 없는 `/\d/` 는 구분자가 **사라지고**(`["a","b","","c"]`), 괄호 있는 `/(\d)/` 는 **캡처가 사이에 끼어든다**(`["a","1","b","2","","2","c"]`).
  `(\d)+` 는 반복 그룹이라 **마지막 반복 `"2"` 하나**만 남는다. 비캡처 `(?:…)` 는 괄호가 있어도 끼어들지 않는다.
- ★★ **`/(\d)|(-)/` 에는 `<undefined>` 가 두 개**다 — 구분자마다 **두 그룹 자리**가 들어가고, 참여하지 않은 쪽이 `undefined` 다.
- ★★ **`[2]`** — `''.split(',')` 는 **`[""]`**(구분자가 없으니 원래 문자열 하나) · `''.split('')` 는 `[]` · `split()` 은 통째로 하나 ·
  **`'a1b2c'.split(/(\d)/, 2)` 는 `["a","1"]`** — `limit` 은 캡처 원소까지 **결과 배열의 길이**로 센다.
- ★★ **`[3]`** — `lastIndex = 3` 이어도 처음부터 나눴고, 원래 객체의 **`lastIndex` 는 `3` 그대로**다. `@@split` 은 **`y` 를 붙인 새 정규식**을 만들어 쓴다.

### 6. `padStart` 는 자르지 않고 · `trim` 은 **`WhiteSpace` 목록**을 지운다(`U+200B` 는 남는다) · `includes` 에 정규식은 `TypeError` ★★

**출력**

```text
===== node20 js28b-28f-pad-trim-search.js (exit=0) =====
[1] padStart / padEnd
  '7'.padStart(3, '0')                        "007"
  '7'.padStart(6, 'ab')                       "ababa7"
  '1234'.padStart(3, '0')                     "1234"
  '7'.padStart(3, '')                         "7"
  '7'.padStart(3)                             "  7"
  '7'.padEnd(3, 'xyz')                        "7xy"

[2] trim -- the first character's general category, and the code units (hex) before and after
  space tab newline         category Zs  before 0020 0009 000a 0078 000a  after trim 0078
  U+00A0 no-break space     category Zs  before 00a0 0078                 after trim 0078
  U+3000 ideographic space  category Zs  before 3000 0078                 after trim 0078
  U+FEFF byte order mark    category Cf  before feff 0078                 after trim 0078
  U+200B zero width space   category Cf  before 200b 0078                 after trim 200b 0078
  U+2028 line separator     category Zl  before 2028 0078                 after trim 0078
  '  x  '.trimStart()                         "x  "
  '  x  '.trimEnd()                           "  x"

[3] includes / startsWith / endsWith / indexOf
  'abc'.includes('')                          true
  'abc'.indexOf('')                           0
  'abc'.indexOf('', 10)                       3
  'abc'.startsWith('b', 1)                    true
  'abc'.endsWith('b', 2)                      true
  'abc'.includes('A')                         false
  'a.c'.includes('.')                         true
  'abc'.includes(/b/)                         TypeError 「First argument to String.prototype.includes must not be a regular expression」
  'abc'.startsWith(/a/)                       TypeError 「First argument to String.prototype.startsWith must not be a regular expression」
  '/b/'.includes(r)  r[Symbol.match]=false    true
  'abc'.includes(undefined)                   false
  'undefined'.includes()                      true
```

**왜 그런가**

- ★★ **`[1]`** — `"007"` · `"ababa7"`(채움 글자를 되풀이하다 자른다) · **`"1234"`**(이미 길면 그대로) · **`"7"`**(빈 채움 글자면 그대로) · `"  7"`(기본은 공백) · `"7xy"`.
- ★★★ **`[2]`** — **`U+200B` 만 남았다**(`200b 0078`). 나머지 다섯은 지워졌다.
  분류 칸을 보면 **`U+FEFF` 도 `Cf`** 인데 지워졌다 — `trim` 의 기준은 분류가 아니라 **명세의 `WhiteSpace`·`LineTerminator` 목록**이고, 거기에 `U+FEFF` 는 **ZWNBSP 로 따로** 적혀 있고 `U+200B` 는 없다. `U+2028` 은 `LineTerminator` 다.
- ★★ **`[3]` 빈 문자열** — `includes('')` `true` · `indexOf('')` `0` · **`indexOf('', 10)` `3`**(위치가 길이로 깎인다).
- ★★★ **정규식을 넘긴 두 줄은 `TypeError`** — `First argument to String.prototype.includes must not be a regular expression`(startsWith 도 같은 꼴). 명세가 **`IsRegExp`** 로 묻는다.
  **`r[Symbol.match] = false`** 로 두면 `IsRegExp` 가 거짓이 되어 **통과**하고, `ToString(r)` = `"/b/"` 를 찾아 `true` 다.
- ★ **마지막 두 줄** — `includes(undefined)` 는 글자 `"undefined"` 를 찾는다. `'abc'` 에는 없어 `false`, `'undefined'` 에는 있어 `true`.

### 7. 문자열이면 **`GetSubstitution`**, 함수면 **호출 결과를 `ToString`** — 둘은 다른 길이다 ★★★

- ★★★ 명세 `String.prototype.replace` 는 두 번째 인자가 **호출 가능하면** `Call(replaceValue, undefined, «matched, position, string»)` 의 결과를 `ToString` 하고, **아니면** `GetSubstitution(matched, string, position, captures, namedCaptures, replaceValue)` 로 채운다. 정규식 패턴이면 `RegExp.prototype[@@replace]` 가 같은 갈림을 한다.
- ★★ **문자열 패턴일 때 캡처 목록은 빈 목록, 명명 캡처는 `undefined`** 다 — 그래서 `$1` 은 「1번이 없다」로 글자 그대로, `$<g>` 는 「명명 캡처가 없다」로 글자 그대로다(1번 첫째 열).
- ★ 처방 — **바깥에서 온 문자열은 함수로 넘긴다**(`() => text`). 1번 `[3]` 의 마지막 줄이 그 실측이다.

### 8. **`GetTemplateObject`** 가 만들고 realm 의 **`[[TemplateMap]]`** 에 **소스 자리(Parse Node)** 를 키로 캐시한다 ★★★

- ★★★ 명세는 태그 호출 때 `GetTemplateObject(templateLiteral)` 을 부르고, 그 안에서 realm 의 `[[TemplateMap]]` 에 **그 템플릿 리터럴의 Parse Node** 로 이미 만든 것이 있으면 **그것을 돌려준다.** 새로 만들 때는 `raw` 배열과 조각 배열을 **`SetIntegrityLevel(…, frozen)`** 으로 얼린다.
- ★★ `new Function` 은 호출마다 **소스 글자를 새로 파싱**해 새 Parse Node 를 만든다 — 키가 다르니 `false`(3번 `[2]`). 루프는 **같은 Parse Node 를 다시 평가**할 뿐이라 `true`.
- ★★ **ES2018**(「Lifting template literal restriction」). 태그 템플릿에서 `NotEscapeSequence` 를 허용하고 그 조각의 **`cooked` 값을 `undefined`** 로 둔다. 태그 없는 템플릿에는 그대로 **조기 오류**다(3번 `[4]`).

### 9. 파이썬 `str.replace` 는 **기본이 전부**이고 표기를 안 읽는다 · `re.sub` 의 표기는 `\1`·`\g<n>` · **없는 그룹은 파이썬만 던진다** ★★

**출력**

```text
===== ./js28b-28g-python.sh (exit=0) =====
[1] str.replace
  'a-b-c'.replace('-', '+')                   'a+b+c'
  'a-b-c'.replace('-', '+', 1)                'a+b-c'
  'abc'.replace('', '-')                      '-a-b-c-'
  'abc'.replace('b', '[$&]')                  'a[$&]c'

[2] re.sub -- the replacement template
  re.sub('(b)', r'[\1]', 'abc')               'a[b]c'
  re.sub('(?P<g>b)', r'[\g<g>]', 'abc')       'a[b]c'
  re.sub('(b)', '[$1]', 'abc')                'a[$1]c'
  re.sub('(b)', r'[\9]', 'abc')               error 「invalid group reference 9 at position 2」
  re.sub('b', lambda m: r'[\1]', 'abc')       'a[\\1]c'

[3] slicing with negative and reversed bounds
  s[-2:]                                      'ef'
  s[4:2]                                      ''
  s[2:-1]                                     'cde'
```

- ★★★ **다르다** — 파이썬은 `'a+b+c'`(전부, `count=1` 이면 하나), JS 는 `"a+b-c"`(첫 하나). 이름이 같고 기본값이 반대다.
- ★★ 파이썬 `re.sub` 는 **`\1`·`\g<g>`** 를 읽는다. **`$1` 은 그냥 글자**다(`'a[$1]c'`). `str.replace` 는 어떤 표기도 안 읽는다(`'a[$&]c'`).
- ★★★ **없는 그룹** — 파이썬 `re.sub` 는 **`error 「invalid group reference 9 at position 2」`**(패턴 오류 예외 `re.error`), JS 는 **`$9` 를 글자 그대로** 둔다(1번). JS 에서 표기 오타는 **조용히** 출력에 남는다.
- ★ **`slice`** — 파이썬 `s[-2:]` 와 JS `slice(-2)` 가 같은 `"ef"`, `s[4:2]` 와 `slice(4, 2)` 가 같은 빈 글자, `s[2:-1]` 과 `slice(2, -1)` 이 같은 `"cde"` 다. `substring` 에 대응하는 파이썬 연산은 없다.

### 10. 04번의 「반쪽이 남는다」 는 **4번 `[3]` 의 `slice(0, 2)`** 이고, `at` 도 **코드 유닛** 단위다 ★★

- ★★ [04번](../04-strings-and-utf16/2-summary.md)은 서로게이트 한 쌍을 가운데서 자르면 **예외 없이 반쪽이 남는다**고 쟀다. 4번 `[3]` 의 `slice(0, 2)` 가 `61 d83d` 로 같은 일을 했다.
- ★★ **코드 유닛**이다 — `at(1)` 이 `d83d`, `at(-2)` 가 `de00` 으로 **쌍의 한 칸씩**을 돌려줬다. 코드 포인트 단위라면 `at(1)` 이 쌍 전체였을 것이다.
- ★ **`Intl.Segmenter`**(04번) — 결합 문자·이모지 연결까지 「사람이 보는 한 글자(자소 클러스터)」로 나눈다. `[...s]` 는 코드 포인트까지만 묶는다.

### 11. `` `${x}` `` 는 **`string`**, `x + ''` 는 **`default`** — 22번이 쟀다 · 정규식 콜백 인자는 **29번** · `IsRegExp` 는 **`Symbol.match`** ★★

- ★★ [22번](../22-symbol-and-well-known-symbols/2-summary.md)의 hint 로그가 `` `${x}` `` → `string`, `x + ''` → `default` 로 찍었다. 템플릿 리터럴의 `${}` 는 `ToString` 이고 `+` 는 `ToPrimitive(default)` 다.
- ★★ [29번](../29-regexp-basics/2-summary.md)이 정본이다. 이 문서는 **문자열 패턴의 콜백**(인자 셋)만 2번 `[5]` 에서 봤다.
- ★ **`Symbol.match`** — 6번 `[3]` 에서 `false` 로 덮자 `includes` 가 정규식을 받아들였다. 잘 알려진 심볼의 전수는 22번이다.

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js28b-28a-dollar-grid.js` | ★★★ `$` 표기 11 × 자리 4 격자 · 「20 / 44」 · 바깥 문자열 | node20 1벌 + node18 대조 1벌 |
| `js28b-28b-replace-all.js` | ★★★ 첫 하나 대 전부 · `g` 없는 `replaceAll` 의 `TypeError` · 빈 패턴 · 겹침 · 콜백 인자 | node20 1벌 + node18 대조 1벌 |
| `js28b-28c-tagged.js` | ★★★ `strings` 의 모양·동결·자리별 동일성 · `String.raw` · 잘못된 이스케이프 | node20 1벌 + node18 대조 1벌 |
| `js28b-28d-slice-substring.js` | ★★★ 자르기 셋 × 인자 10 · 「5 / 10」 · `at` 대 대괄호 · BMP 밖 글자 | node20 1벌 + **node18 1벌(갈린 판)** |
| `js28b-28e-split.js` | ★★ 캡처가 끼어드는 것 · `undefined` 자리 · `limit` · `lastIndex` 무시 | node20 1벌 + node18 대조 1벌 |
| `js28b-28f-pad-trim-search.js` | ★★ `padStart` · `trim` 이 지우는 글자와 그 분류 · 빈 문자열 · `IsRegExp` | node20 1벌 + node18 대조 1벌 |
| `js28b-28g-python.sh` | ★★ 파이썬 `str.replace`·`re.sub`·자르기 대비 | Python 3.12.3 1벌 |
| `js28b-vdiff.sh` · `js28b-versions.sh` | 두 판이 갈린 탐침 수 · 이 문서의 출력이 **어느 판에서 나왔나** + 판별 기능 표 | 1벌씩 |

두 node 판 대조기(이 배치 전체의 node 탐침). 이 주제의 줄(`js28b-28…`)은 `js28b-28d-slice-substring.js` 하나만 `DIFFERS` 다. 그 밖의 `DIFFERS` 줄은 **다른 주제의 탐침**이다(같은 배치가 한 대조기를 공유한다).

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

- ★ **다시 돌릴 것** — node 판이 오르면 `js28b-28d-slice-substring.js` 의 `isWellFormed` 줄 · 예외 **문구** 전부(V8 의 글자). 유니코드 판이 오르면 `js28b-28f` 의 `[2]`(분류 칸).
- ★ **흔들린 칸** — 이 주제의 블록에는 없다(재대조 동일).
