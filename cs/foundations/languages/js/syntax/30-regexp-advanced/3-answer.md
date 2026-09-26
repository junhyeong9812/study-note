# js/syntax/30 — 정규식 심화: 「그룹·둘러보기·유니코드 — 그리고 같은 패턴이 어떤 엔진에서는 끝나지 않는다」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **node v20.19.6**(기본 판) · **node v18.19.1**(대조) · **Google Chrome 151.0.7922.173**(8번) · **go1.27.1** · **Python 3.12.3** · x86-64 Linux 에서 실제로 돌려 얻은 것이고,
> 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 하나도 없다).
>
> ★★★ **경과 시간은 이 파일 어디에도 없다** — 셸이 `timeout 2` 의 종료 코드만 보고 참/거짓으로 바꿨다.
> ★★ **예외는 `e.constructor.name` 과 `e.message` 로만** `이름 「메시지」` 꼴로 찍었다(Go 는 `%T 「%v」`, 파이썬은 `type(e).__name__ 「str(e)」`).
> ★★ **이 주제에서 두 node 판이 갈린 탐침은 셋**이다(1번 · 3번 · 4번) — 갈린 판의 블록을 나란히 싣는다.
>
> **이 파일이 인용하는 출력을 낸 소스** — 1\~6번의 소스 전문은 [1-question.md](1-question.md) 의 같은 번호 문항에 있다. 7 · 8 · 10 · 11번의 소스는 여기 싣는다.
> `js28b-30a-groups.js`(1번) · `js28b-30b-lookaround.js`(2번) · `js28b-30c-unicode.js`(3번) · `js28b-30d-vflag.js`(4번) · `js28b-30x-explode.sh`(5번 · 12번) · `js28b-30y-steps.sh`(6번) ·
> `js28b-30e-indices.js`(7번) · `js28b-30f-es2025.web.js` · `js28b-30g-es2025-node.js`(8번) · `js28b-30u-syntax.sh`(10번 · 12번) · `js28b-30v-v8flags.sh` · `js28b-30w-linear.sh`(11번).

## 정답

### 1. 비캡처는 칸이 없고, 명명 그룹은 칸에 **이름표를 더한다** — `groups` 는 **null 프로토타입**, 반복 안의 캡처는 **반복마다 비워진다** ★★★

**출력**

```text
===== node20 js28b-30a-groups.js (exit=0) =====
[1] the same date, grouped three ways
  /(\d+)-(\d+)-(\d+)/.exec(s)                   ["2026-09-26","2026","09","26"]
  /(?:\d+)-(\d+)-(?:\d+)/.exec(s)               ["2026-09-26","09"]
  named -- the array part                       ["2026-09-26","2026","09","26"]
  named -- m.groups                             {"y":"2026","mo":"09","d":"26"}
  named -- m.groups.mo                          09

[2] the groups object itself
  Object.getPrototypeOf(m.groups) === null      true
  'toString' in m.groups                        false
  String(m.groups)                              TypeError 「Cannot convert object to primitive value」
  JSON.stringify(m.groups)                      {"y":"2026","mo":"09","d":"26"}
  groups when the pattern has no named group    undefined
  key order of /(?<b>x)(?<a>y)/                 ["b","a"]

[3] an optional group -- /(?<a>a)?(?<b>b)/.exec('b')
  array                                         ["b","<undefined>","b"]
  Object.keys(groups)                           ["a","b"]
  groups.a                                      undefined
  'a' in groups                                 true

[4] a group inside a quantifier
  /(\w)+/.exec('abc')                           ["abc","c"]
  /(?:(a)|b)+/.exec('ab')                       ["ab","<undefined>"]
  /(?:(a)|(b))+/.exec('ab')                     ["ab","<undefined>","b"]

[5] referring back to a group
  /(?<q>['"]).*?\k<q>/.exec(`say "hi" 'yo'`)    ["\"hi\"","\""]
  /(a)|\1b/.exec('b')                           ["b","<undefined>"]
  s.replace(named, '$<d>.$<mo>.$<y>')           26.09.2026
  callback -- typeof the last argument          object {"y":"2026"}

[6] \k and group names at the edges
  new RegExp('\\k<z>').test('k<z>')             true
  new RegExp('\\k<z>', 'u')                     SyntaxError 「Invalid regular expression: /\k<z>/u: Invalid named capture referenced」
  new RegExp('(?<a>x)\\k<z>')                   SyntaxError 「Invalid regular expression: /(?<a>x)\k<z>/: Invalid named capture referenced」
  new RegExp('(?<a>x)(?<a>y)')                  SyntaxError 「Invalid regular expression: /(?<a>x)(?<a>y)/: Duplicate capture group name」
  new RegExp('(?<1a>x)')                        SyntaxError 「Invalid regular expression: /(?<1a>x)/: Invalid capture group name」
```

```text
===== node18 js28b-30a-groups.js (exit=0) =====
[1] the same date, grouped three ways
  /(\d+)-(\d+)-(\d+)/.exec(s)                   ["2026-09-26","2026","09","26"]
  /(?:\d+)-(\d+)-(?:\d+)/.exec(s)               ["2026-09-26","09"]
  named -- the array part                       ["2026-09-26","2026","09","26"]
  named -- m.groups                             {"y":"2026","mo":"09","d":"26"}
  named -- m.groups.mo                          09

[2] the groups object itself
  Object.getPrototypeOf(m.groups) === null      true
  'toString' in m.groups                        false
  String(m.groups)                              TypeError 「Cannot convert object to primitive value」
  JSON.stringify(m.groups)                      {"y":"2026","mo":"09","d":"26"}
  groups when the pattern has no named group    undefined
  key order of /(?<b>x)(?<a>y)/                 ["b","a"]

[3] an optional group -- /(?<a>a)?(?<b>b)/.exec('b')
  array                                         ["b","<undefined>","b"]
  Object.keys(groups)                           ["a","b"]
  groups.a                                      undefined
  'a' in groups                                 true

[4] a group inside a quantifier
  /(\w)+/.exec('abc')                           ["abc","c"]
  /(?:(a)|b)+/.exec('ab')                       ["ab","<undefined>"]
  /(?:(a)|(b))+/.exec('ab')                     ["ab","<undefined>","b"]

[5] referring back to a group
  /(?<q>['"]).*?\k<q>/.exec(`say "hi" 'yo'`)    ["\"hi\"","\""]
  /(a)|\1b/.exec('b')                           ["b","<undefined>"]
  s.replace(named, '$<d>.$<mo>.$<y>')           26.09.2026
  callback -- typeof the last argument          object {"y":"2026"}

[6] \k and group names at the edges
  new RegExp('\\k<z>').test('k<z>')             true
  new RegExp('\\k<z>', 'u')                     SyntaxError 「Invalid regular expression: /\k<z>/: Invalid named capture referenced」
  new RegExp('(?<a>x)\\k<z>')                   SyntaxError 「Invalid regular expression: /(?<a>x)\k<z>/: Invalid named capture referenced」
  new RegExp('(?<a>x)(?<a>y)')                  SyntaxError 「Invalid regular expression: /(?<a>x)(?<a>y)/: Duplicate capture group name」
  new RegExp('(?<1a>x)')                        SyntaxError 「Invalid regular expression: /(?<1a>x)/: Invalid capture group name」
```

**왜 그런가**

- ★★ **`[1]` 비캡처 쪽은 두 칸**(`["2026-09-26","09"]`)이다. 명명 그룹 쪽의 배열 부분은 **번호 그룹과 같은 네 칸**이다 — 이름은 번호를 대신하지 않고 **더해진다.**
- ★★★ **`[2]` `groups` 의 프로토타입은 `null`** — 명세가 결과 객체를 `OrdinaryObjectCreate(null)` 로 만든다. 그래서 `'toString' in m.groups` 가 `false`,
  `String(m.groups)` 가 **`TypeError 「Cannot convert object to primitive value」`** 다(`toString`·`valueOf` 를 못 찾는다). 27번의 `Object.groupBy` 결과와 같은 이유 · 같은 증상이다.
  ★ 명명 그룹이 **없는** 패턴이면 `groups` 는 **`undefined`** 다. 키 순서는 **괄호가 나온 순서**(`["b","a"]`).
- ★★ **`[3]` 참여하지 않은 그룹도 키는 만든다** — `["a","b"]` · `'a' in groups` 가 `true`, 값만 `undefined`. 배열 칸도 `<undefined>` 다.
- ★★★ **`[4]` 반복 안의 캡처** — `/(\w)+/` 는 마지막 반복의 `"c"` 만 남긴다.
  ★★★ `/(?:(a)|b)+/.exec('ab')` 의 1번 칸이 **`<undefined>`** 다 — 명세의 반복 매처는 **반복을 한 번 더 돌기 전에 그 안의 캡처를 전부 비운다.** 둘째 반복이 `b` 갈래로 끝났으니 `(a)` 는 빈 채 남는다.
  `(?:(a)|(b))+` 로 두 갈래에 다 캡처를 걸면 `["ab","<undefined>","b"]` — **첫 반복의 `a` 가 지워진 것**이 한 줄로 보인다.
- ★★ **`[5]`** — `/(a)|\1b/.exec('b')` 는 `["b","<undefined>"]` 다. **참여하지 않은 그룹의 역참조는 빈 문자열처럼 통과**한다(에러도 실패도 아니다).
  콜백의 마지막 인자는 **`groups` 객체**(`object {"y":"2026"}`) — 명명 그룹이 있을 때만 붙는다.
- ★★★ **`[6]` `\k<z>` 는 첫 줄에서만 통과한다** — 명명 그룹도 `u` 도 없으면 부록 B(웹 호환) 문법이 `\k` 를 **그냥 글자 `k`** 로 읽어 `'k<z>'` 에 `true`.
  `u` 가 있거나 **명명 그룹이 하나라도 있으면** 엄격한 문법이 되어 `SyntaxError 「… Invalid named capture referenced」`.
  같은 이름 두 번은 `Duplicate capture group name`, 숫자로 시작하는 이름은 `Invalid capture group name` 이다.
- ★ **두 판이 갈린 줄은 하나** — `[6]` 둘째 줄의 문구가 node18 에서 `/\k<z>/`, node20 에서 `/\k<z>/u` 다. 종류(`SyntaxError`)와 뜻은 같다 — **문구는 흔들리는 칸**이다.

### 2. 둘러보기는 **보기만 하고 먹지 않으며**, JS 의 룩비하인드는 **길이가 변해도 되고 오른쪽부터 채운다** ★★★

**출력**

```text
===== node20 js28b-30b-lookaround.js (exit=0) =====
[1] four lookarounds on t = "30 USD, 45 EUR, $12, 7"
  t.match(/\d+(?= USD)/g)                     ["30"]
  t.match(/\b\d+\b(?! USD)/g)                 ["45","12","7"]
  t.match(/(?<=\$)\d+/g)                      ["12"]
  t.match(/(?<!\$)\b\d+/g)                    ["30","45","7"]

[2] how much does a lookaround consume?
  /(?=b)/.exec('abc') -- index, [0]           1 ""
  'abc'.replace(/(?=b)/, '|')                 a|bc
  '1234567'.replace(/\B(?=(\d{3})+$)/g, ',')  1,234,567
  /(?=(a+))/.exec('baaa')                     ["","aaa"]

[3] lookbehind of varying length
  /(?<=\$\d+\.)\d+/.exec('cost $12.50')       ["50"]
  /(?<=^a+)b/.test('aaaab')                   true
  /(?<=a|bc)x/g on 'ax bcx cx'                ["x","x"]

[4] groups inside a lookbehind -- '1053'
  /(?<=(\d+)(\d+))$/.exec('1053')             ["","1","053"]
  /(?<=(\d+?)(\d+))$/.exec('1053')            ["","1","053"]
  /((\d+)(\d+))$/.exec('1053')                ["1053","1053","105","3"]

[5] several conditions on one string: /^(?=.*\d)(?=.*[a-z])\S{6,}$/
  "abc123"                                    true
  "abcdef"                                    false
  "123456"                                    false
  "ab1"                                       false
  "ABC123"                                    false
  "abc 123"                                   false
```

**왜 그런가**

- ★★ **`[1]` `(?! USD)` 줄에 `30` 이 없다**(`["45","12","7"]`) — `\b\d+\b` 가 `30` 전체를 잡으면 뒤에 ` USD` 가 있어 실패하고, `\d+` 를 `3` 으로 줄이면 `\b` 가 `3` 과 `0` 사이에서 실패한다. **빠져나갈 길이 없다.**
  `(?<!\$)\b\d+` 가 `12` 를 빼는 것도 같은 구조다(`$` 바로 뒤의 `1` 에서 막히고, `2` 앞은 `\b` 가 아니다).
- ★★★ **`[2]` `(?=b)` 는 `index 1`, `[0]` 이 `""`** — 길이 0 매치다. `replace` 는 그 **자리**에 끼운다(`a|bc`).
  `\B(?=(\d{3})+$)` 는 「뒤에 세 자리 묶음들이 끝까지 이어지는 자리」마다 길이 0 매치를 만들어 `1,234,567` 이 된다.
  `/(?=(a+))/.exec('baaa')` 는 **두 칸**(`["","aaa"]`) — 먹지 않았지만 **둘러보기 안의 캡처는 남는다.**
- ★★★ **`[3]` 받는다** — `(?<=\$\d+\.)` 가 `["50"]`, `(?<=^a+)b` 가 `true`, `(?<=a|bc)` 가 두 갈래 길이가 달라도 `["x","x"]`.
  ★ 명세는 룩비하인드 안에 **어떤 패턴이든** 둘 수 있게 적었다 — 길이 제한이 없다. **파이썬 `re` 는 고정 길이만** 받는다(12번).
- ★★★ **`[4]` 안에서는 `"1"`·`"053"`, 밖에서는 `"105"`·`"3"`** — 룩비하인드는 명세가 **역방향**으로 평가하게 적었다.
  역방향에서는 **오른쪽 그룹**이 먼저 매칭되어 욕심껏 `053` 을 가져가고, 왼쪽 그룹에는 `1` 이 남는다. 왼쪽을 게으르게 해도 남은 것이 `1` 뿐이라 같다.
- ★ **`[5]` `"abc123"` 하나만 `true`** — 숫자 없음(`abcdef`)·소문자 없음(`123456`·`ABC123`)·짧음(`ab1`)·공백(`abc 123` — `\S`)이 각각 떨어진다.

### 3. 플래그가 없으면 **글자 = 코드 유닛**, `u`·`v` 면 **글자 = 코드 포인트** — 일곱 줄 중 여섯이 갈렸다 ★★★

**출력**

```text
===== node20 js28b-30c-unicode.js (exit=0) =====
[1] the input
  face = String.fromCodePoint(0x1f600)        length 2  units [d83d de00]

[2] the same pattern, three flag settings (no flag / u / v)
  ^.$ on face                                 -:false  u:true  v:true
  ^..$ on face                                -:true  u:false  v:false
  ^[face]$ on face                            -:false  u:true  v:true
  ^face{2}$ on face+face                      -:false  u:true  v:true
  ^\S$ on face                                -:false  u:true  v:true
  high half alone, on face                    -:true  u:false  v:false
  ^.$ on the high half alone                  -:true  u:true  v:true
  rows where no-flag and u differ: 6 / 7

[3] what did . take?
  face.match(/./)[0]                          [d83d]
  face.match(/./u)[0]                         [d83d de00]
  (face + 'x').match(/./g).length             3
  (face + 'x').match(/./gu).length            2
  face.split(/(?:)/)                          [d83d] [de00]
  face.split(/(?:)/u)                         [d83d de00]

[4] the escape \u{1F600}
  /\u{1F600}/u.test(face)                     true
  /\u{1F600}/.test(face)                      false
  /\u{1F600}/.test('u{1F600}')                true
  /^\u{3}$/.test('uuu')                       true

[5] unicode property escapes \p{...}
  /\p{L}/u on 'a' / e-acute / hangul / '1'    true true true false
  /\p{Script=Hangul}/u on hangul / 'a'        true false
  /\p{L}/ (no flag) on 'p{L}' / 'a'           true false
  new RegExp('\\p{Nope}', 'u')                SyntaxError 「Invalid regular expression: /\p{Nope}/u: Invalid property name」
  /^\p{Emoji}$/u on face / '1'                true true
```

```text
===== node18 js28b-30c-unicode.js (exit=0) =====
[1] the input
  face = String.fromCodePoint(0x1f600)        length 2  units [d83d de00]

[2] the same pattern, three flag settings (no flag / u / v)
  ^.$ on face                                 -:false  u:true  v:SyntaxError
  ^..$ on face                                -:true  u:false  v:SyntaxError
  ^[face]$ on face                            -:false  u:true  v:SyntaxError
  ^face{2}$ on face+face                      -:false  u:true  v:SyntaxError
  ^\S$ on face                                -:false  u:true  v:SyntaxError
  high half alone, on face                    -:true  u:false  v:SyntaxError
  ^.$ on the high half alone                  -:true  u:true  v:SyntaxError
  rows where no-flag and u differ: 6 / 7

[3] what did . take?
  face.match(/./)[0]                          [d83d]
  face.match(/./u)[0]                         [d83d de00]
  (face + 'x').match(/./g).length             3
  (face + 'x').match(/./gu).length            2
  face.split(/(?:)/)                          [d83d] [de00]
  face.split(/(?:)/u)                         [d83d de00]

[4] the escape \u{1F600}
  /\u{1F600}/u.test(face)                     true
  /\u{1F600}/.test(face)                      false
  /\u{1F600}/.test('u{1F600}')                true
  /^\u{3}$/.test('uuu')                       true

[5] unicode property escapes \p{...}
  /\p{L}/u on 'a' / e-acute / hangul / '1'    true true true false
  /\p{Script=Hangul}/u on hangul / 'a'        true false
  /\p{L}/ (no flag) on 'p{L}' / 'a'           true false
  new RegExp('\\p{Nope}', 'u')                SyntaxError 「Invalid regular expression: /\p{Nope}/: Invalid property name」
  /^\p{Emoji}$/u on face / '1'                true true
```

**왜 그런가**

- ★★★ **`[2]` N / M 은 `6 / 7`** — 플래그 없음과 `u` 가 **같은 답을 낸 것은 `^.$ on the high half alone` 하나뿐**이다.
  플래그가 없으면 `face` 는 **글자 둘**(`d83d`·`de00`)이라 `^.$` 가 `false`, `^..$` 가 `true` 이고 `[face]` 는 **반쪽 둘의 집합**(한 칸만 먹는다), `face{2}` 의 `{2}` 는 **뒤쪽 반쪽에만** 붙는다.
  `u` 면 `face` 가 **글자 하나**라 전부 뒤집힌다. ★ **`v` 열은 `u` 열과 일곱 줄 전부 같다.**
- ★★★ **끝에서 두 줄** — `high half alone, on face` 는 **`-:true  u:false  v:false`**. `u` 는 **쌍의 한가운데에서 매칭을 시작하지 않는다** — 코드 포인트 열로 읽으니 반쪽이 따로 없다.
  `^.$ on the high half alone` 은 **셋 다 `true`** — 짝이 없는 반쪽은 `u` 에서도 **그 자체로 한 코드 포인트**로 읽힌다(04번의 「짝을 잃은 반쪽은 예외 없이 남는다」).
- ★★ **`[3]`** — `.` 이 플래그 없이 `[d83d]`, `u` 로 `[d83d de00]`. 개수는 `3` 과 `2`. `split` 두 줄은 04번의 그림과 같은 결과를 16진수로 본 것이다.
- ★★★ **`[4]` 플래그 없는 `\u{1F600}` 은 「글자 `u` + 글자 `{1F600}`」** — `u` 모드가 아니면 `\u` 뒤에 네 자리 16진수가 아닌 것이 오면 부록 B 가 **그냥 `u`** 로 읽고, `{1F600}` 은 수량자 모양이 아니라 **글자 그대로**다(`'u{1F600}'` 에 `true`).
  **`\u{3}` 은 `{3}` 이 진짜 수량자**라 `u` 를 세 번 — `'uuu'` 에 `true`. 같은 꼴인데 중괄호 안이 숫자냐 아니냐로 뜻이 갈린다.
- ★★★ **`[5]` `/\p{L}/` 은 에러 없이 글자 `p{L}` 을 찾는다**(`true false`). 모르는 속성은 `u` 모드에서 `SyntaxError 「… Invalid property name」`.
- ★★ **node18 에서는 `v` 열 일곱 칸이 전부 `SyntaxError`** 로 바뀌고 나머지는 같다. 문구의 플래그 표기(`/\p{Nope}/` 대 `/\p{Nope}/u`)도 한 줄 갈렸다.

### 4. `v` 는 **집합 연산과 글자열 속성을 더하고**, 클래스 안의 **맨 구두점을 거절한다** ★★

**출력**

```text
===== node20 js28b-30d-vflag.js (exit=0) =====
[1] set operations -- inputs 'a' / e-acute / hangul / '1'
  ^[\p{L}--\p{ASCII}]$  v                       false true true false
  ^[\p{L}&&\p{ASCII}]$  v                       true false false false
  ^[\p{L}--\p{ASCII}]$  u                       SyntaxError 「Invalid regular expression: /^[\p{L}--\p{ASCII}]$/u: Invalid character class」
  ^[[a-z]--[aeiou]]+$  v   on 'rhythm' / 'rain' true false

[2] strings in a class -- family = [d83d dc68 200d d83d dc69 200d d83d dc67]  (length 8)
  ^\p{RGI_Emoji}$  v   on family / face         true true
  ^\p{Emoji}$      u   on family / face         false true
  ^\p{RGI_Emoji}$  u                            SyntaxError 「Invalid regular expression: /^\p{RGI_Emoji}$/u: Invalid property name」
  ^[\q{abc|d}]$    v   on 'abc' / 'd' / 'a'     true true false
  family.match(v)[0]  for [\p{RGI_Emoji}]       [d83d dc68 200d d83d dc69 200d d83d dc67]

[3] the same source under u and under v
  [(]                                           u:ok  v:SyntaxError
  [a-]                                          u:ok  v:SyntaxError
  [|]                                           u:ok  v:SyntaxError
  [a&&&b]                                       u:ok  v:SyntaxError
  [\-]                                          u:ok  v:ok
  sources accepted under u but not under v: 4 / 5
  new RegExp('[(]', 'v') -- message             SyntaxError 「Invalid regular expression: /[(]/v: Invalid character in character class」
  new RegExp('a', 'uv')                         SyntaxError 「Invalid flags supplied to RegExp constructor 'uv'」

[4] the flag's properties
  new RegExp('a', 'v').unicodeSets / .unicode   true / false
  new RegExp('a', 'v').flags                    v
```

```text
===== node18 js28b-30d-vflag.js (exit=0) =====
[1] set operations -- inputs 'a' / e-acute / hangul / '1'
  ^[\p{L}--\p{ASCII}]$  v                       SyntaxError 「Invalid flags supplied to RegExp constructor 'v'」
  ^[\p{L}&&\p{ASCII}]$  v                       SyntaxError 「Invalid flags supplied to RegExp constructor 'v'」
  ^[\p{L}--\p{ASCII}]$  u                       SyntaxError 「Invalid regular expression: /^[\p{L}--\p{ASCII}]$/: Invalid character class」
  ^[[a-z]--[aeiou]]+$  v   on 'rhythm' / 'rain' SyntaxError 「Invalid flags supplied to RegExp constructor 'v'」

[2] strings in a class -- family = [d83d dc68 200d d83d dc69 200d d83d dc67]  (length 8)
  ^\p{RGI_Emoji}$  v   on family / face         SyntaxError 「Invalid flags supplied to RegExp constructor 'v'」
  ^\p{Emoji}$      u   on family / face         false true
  ^\p{RGI_Emoji}$  u                            SyntaxError 「Invalid regular expression: /^\p{RGI_Emoji}$/: Invalid property name」
  ^[\q{abc|d}]$    v   on 'abc' / 'd' / 'a'     SyntaxError 「Invalid flags supplied to RegExp constructor 'v'」
  family.match(v)[0]  for [\p{RGI_Emoji}]       SyntaxError 「Invalid flags supplied to RegExp constructor 'v'」

[3] the same source under u and under v
  [(]                                           u:ok  v:SyntaxError
  [a-]                                          u:ok  v:SyntaxError
  [|]                                           u:ok  v:SyntaxError
  [a&&&b]                                       u:ok  v:SyntaxError
  [\-]                                          u:ok  v:SyntaxError
  sources accepted under u but not under v: 5 / 5
  new RegExp('[(]', 'v') -- message             SyntaxError 「Invalid flags supplied to RegExp constructor 'v'」
  new RegExp('a', 'uv')                         SyntaxError 「Invalid flags supplied to RegExp constructor 'uv'」

[4] the flag's properties
  new RegExp('a', 'v').unicodeSets / .unicode   SyntaxError 「Invalid flags supplied to RegExp constructor 'v'」
  new RegExp('a', 'v').flags                    SyntaxError 「Invalid flags supplied to RegExp constructor 'v'」
```

**왜 그런가**

- ★★ **`[1]` 셋째 줄은 `SyntaxError 「… Invalid character class」`** — `u` 문법에서 `[\p{L}--…]` 는 **속성 이스케이프로 범위를 시작한** 것이라 틀린 클래스다. **조용히 다르게 되지 않고 막힌다.**
  `v` 의 `--` 는 é·한글만, `&&` 는 `a` 만 남긴다. `[[a-z]--[aeiou]]` 는 모음을 뺀 소문자 — `rhythm` 만 `true`.
- ★★★ **`[2]` 가족 이모지** — `v` 의 `\p{RGI_Emoji}` 는 **`true`**(코드 유닛 여덟 칸을 한 원소로), `u` 의 `\p{Emoji}` 는 **`false`**(코드 포인트 하나짜리 속성이라 `^…$` 사이에 여러 개가 있으면 안 맞는다).
  `face` 는 둘 다 `true` 다. `match` 로 잡으면 여덟 칸이 **통째로** 나온다.
- ★★ **`\p{RGI_Emoji}` 를 `u` 로 쓰면 `Invalid property name`** — 글자열 속성은 **`v` 에만** 있다.
- ★★★ **`[3]` `4 / 5`** — `[(]`·`[a-]`·`[|]`·`[a&&&b]` 가 `u:ok  v:SyntaxError`, `[\-]` 만 둘 다 `ok`.
  `v` 는 집합 연산 문법(`--`·`&&`·중첩 `[…]`)과 겹치지 않도록 **클래스 안의 몇몇 구두점을 이스케이프 없이 못 쓰게** 했다. 문구는 `Invalid character in character class`.
- ★ **`[4]` `unicodeSets` 가 `true`, `unicode` 가 `false`** — `v` 는 `u` 를 **켜는 것이 아니라 대신하는** 플래그다. 그래서 `uv` 는 `Invalid flags`.
- ★★ **node18** — `v` 를 쓴 줄은 전부 `Invalid flags supplied to RegExp constructor 'v'`(ES2024 이전 V8). `u` 줄만 node20 과 같은 답이고 문구의 플래그 표기만 다르다.

### 5. 백트래킹 엔진 셋은 **두 자릿수 n 에서 잘렸고**, 상태 집합 쪽 셋은 **n = 1000 까지 전부 끝났다** — 답은 모두 같았다 ★★★

**출력**

```text
===== ./js28b-30x-explode.sh (exit=0) =====
  n     node18           node20           node20 l-flag    node20 fallback  go RE2           python3 re       
  10    yes (false)      yes (false)      yes (false)      yes (false)      yes (false)      yes (False)      
  20    yes (false)      yes (false)      yes (false)      yes (false)      yes (false)      yes (False)      
  30    no               no               yes (false)      yes (false)      yes (false)      no               
  40    no               no               yes (false)      yes (false)      yes (false)      no               
  1000  no               no               yes (false)      yes (false)      yes (false)      no               

  node18            first n that did not finish: 30
  node20            first n that did not finish: 30
  node20 l-flag     first n that did not finish: none
  node20 fallback   first n that did not finish: none
  go RE2            first n that did not finish: none
  python3 re        first n that did not finish: 30

finished within 2s: 21 / 30   ·   finished with a wrong answer: 0
```

**왜 그런가**

- ★★★ **node18 · node20 · python3 re 는 `10`·`20` 이 yes, `30`·`40`·`1000` 이 no.** **node20 l-flag · node20 fallback · go RE2 는 다섯 행 전부 yes.** 끝난 칸의 답은 전부 `false`(파이썬은 `False`) — 입력 끝의 `!` 때문에 매치가 없다.
- ★★★ **「처음 끝나지 않은 n」은 백트래킹 셋이 `30`, 나머지 셋이 `none`** 이다. 그런데 이 `30` 은 **격자 간격이 10 이라 나온 값**이다 — 말할 수 있는 것은 「**두 자릿수 — 20 과 30 사이 어딘가**」까지다.
  어느 n 에서 2초를 넘기느냐는 **머신과 제한 시간에 달리므로** 값에 뜻을 두지 않는다. 뜻이 있는 것은 **「세 자릿수까지도 못 간다」는 성질**이다.
- ★★ **마지막 줄 — `21 / 30` · 틀린 답 `0`.**
- ★★ **Go 는 빌드한 실행 파일에 `timeout` 을 건다** — `go run` 은 부를 때마다 **컴파일과 링크까지** 제한 시간 안에 넣는다. 그러면 「엔진이 2초 안에 끝났나」가 아니라 「컴파일과 엔진이 합쳐 2초 안에 끝났나」를 묻게 된다. **창의 조건을 엔진끼리 맞추려는 것**이다.
- ★★★ **이 블록으로 「몇 배 느려지나」는 말할 수 없다** — 시간을 안 찍었기 때문이다. 증가의 모양은 **6번(되돌이 수)** 이 답한다.
  ★ node 두 열과 python 열이 **같은 칸에서 끊긴 것**도 「셋이 같은 속도」라는 뜻이 아니다 — 격자가 거칠어 **같은 칸에 떨어졌을 뿐**이다.

### 6. 비율은 **2.00 에 붙고**, 같은 언어의 `/^a+$/` 는 **변하지 않으며**, K 를 열 배씩 올려도 **첫 n 은 3\~4 씩만** 는다 ★★★

**출력**

```text
===== ./js28b-30y-steps.sh (exit=0) =====
[1] node20  /^(a+)+$/
  n       smallest K with no fallback  ratio to the row above
  1       5                            -
  2       8                            1.60
  3       14                           1.75
  4       26                           1.86
  5       50                           1.92
  6       98                           1.96
  7       194                          1.98
  8       386                          1.99
  9       770                          1.99
  10      1538                         2.00
  11      3074                         2.00
  12      6146                         2.00

[2] node20  /^a+$/  (the same language, no nested quantifier)
  n       smallest K with no fallback  ratio to the row above
  1       3                            -
  10      3                            1.00
  100     3                            1.00
  1000    3                            1.00
  10000   3                            1.00

[3] node18  /^(a+)+$/ -- is the table the same as [1]?
  identical to [1]

[4] K = 1000, 10000, 100000, 1000000 -- the first n (1..30) that falls back, node20  /^(a+)+$/
  K = 1000      first n = 10
  K = 10000     first n = 13
  K = 100000    first n = 17
  K = 1000000   first n = 20
```

**왜 그런가**

- ★★★ **`[1]` 비율이 `1.60 → 1.75 → 1.86 → … → 2.00`** — n 이 하나 늘 때 **되돌이 수가 거의 두 배**가 된다(작은 n 에서 2 보다 작은 것은 되돌이 말고 드는 고정 몫이 상대적으로 크기 때문으로 보인다 — **추론이다**).
  `^(a+)+$` 는 `a` n 개를 **몇 덩어리로 나누느냐**가 전부 갈래가 되고, 끝의 `!` 때문에 **모든 나누기가 실패해야** 끝난다. 나누는 방법의 수가 n 마다 두 배로 는다 — 원리의 정본은 알고리즘 갈래다.
- ★★★ **`[2]` `/^a+$/` 는 `n = 1` 에서 `10000` 까지 K 가 `3`** — 같은 문자열을 받는 패턴인데 되돌이 수가 **입력 길이와 무관**했다. 폭발은 **언어가 아니라 패턴 모양(중첩 수량자)** 에서 온다.
- ★★ **`[3]` `identical to [1]`** — node18(V8 10.2)과 node20(V8 11.3)의 표가 한 글자도 같다. 시간이었다면 판·머신마다 흔들렸을 칸이다.
- ★★★ **`[4]` `10 → 13 → 17 → 20`** — K 가 **곱으로** 늘 때 첫 n 은 **덧셈으로** 는다. 5번의 「두 자릿수에서 잘린다」가 이 표로 설명된다.
- ★★★ **시간이 아니라 되돌이 수인 이유** — 되돌이 수는 **엔진이 한 일의 양**이라 **머신·부하·판과 무관하게 재현**된다(`[3]` 이 증거). 시간은 그 양에 머신 속도가 곱해진 것이라 흔들린다.
  ★ 대가 — 이 계수기는 **V8 에만 있고**, 무엇을 한 번으로 세는지는 V8 의 정의다. 그래서 **K 의 절댓값이 아니라 비율과 추세만** 근거로 쓴다.

### 7. `d` 의 숫자는 **코드 유닛 위치** — `u` 를 달아도 단위가 안 바뀐다 ★★

**출력**

```js
// js28b-30e-indices.js
// The d flag -- where each group started and ended.
const J = (x) => JSON.stringify(x);
const show = (label, f) => {
  try { console.log("  " + label.padEnd(40) + f()); }
  catch (e) { console.log("  " + label.padEnd(40) + e.constructor.name + " 「" + e.message + "」"); }
};
const line = "a=1; key=val";
const re = /(?<k>\w+)=(?<v>\w+)/d;

console.log("[1] one match with d -- input " + J(line));
const m = re.exec(line);
show("m[0] / m.index", () => J(m[0]) + " / " + m.index);
show("m.indices", () => J(m.indices));
show("m.indices.groups", () => J(m.indices.groups));
show("Object.getPrototypeOf(m.indices.groups)", () => String(Object.getPrototypeOf(m.indices.groups)));
show("line.slice(...m.indices.groups.v)", () => J(line.slice(...m.indices.groups.v)));

console.log("");
console.log("[2] the same pattern without d");
const plain = /(?<k>\w+)=(?<v>\w+)/.exec(line);
show("plain.indices", () => String(plain.indices));
show("'indices' in plain", () => "indices" in plain);

console.log("");
console.log("[3] every match, and an optional group");
show("matchAll(/(\\w+)=(\\w+)/dg) -> indices", () => J([...line.matchAll(/(\w+)=(\w+)/dg)].map((x) => x.indices)));
show("/(a)?b/d.exec('b').indices", () => J([.../(a)?b/d.exec("b").indices].map((v) => (v === undefined ? "<undefined>" : v))));

console.log("");
console.log("[4] the numbers count code units -- input: face + 'x=1'");
const face = String.fromCodePoint(0x1f600);
show("/(\\w)=(\\d)/d.exec(face + 'x=1').indices", () => J(/(\w)=(\d)/d.exec(face + "x=1").indices));
show("same with du", () => J(/(\w)=(\d)/du.exec(face + "x=1").indices));

console.log("");
console.log("[5] the flag's properties");
show("re.hasIndices / re.flags", () => re.hasIndices + " / " + re.flags);
show("new RegExp('a', 'ygsmid').flags", () => new RegExp("a", "ygsmid").flags);
```

```text
===== node20 js28b-30e-indices.js (exit=0) =====
[1] one match with d -- input "a=1; key=val"
  m[0] / m.index                          "a=1" / 0
  m.indices                               [[0,3],[0,1],[2,3]]
  m.indices.groups                        {"k":[0,1],"v":[2,3]}
  Object.getPrototypeOf(m.indices.groups) null
  line.slice(...m.indices.groups.v)       "1"

[2] the same pattern without d
  plain.indices                           undefined
  'indices' in plain                      false

[3] every match, and an optional group
  matchAll(/(\w+)=(\w+)/dg) -> indices    [[[0,3],[0,1],[2,3]],[[5,12],[5,8],[9,12]]]
  /(a)?b/d.exec('b').indices              [[0,1],"<undefined>"]

[4] the numbers count code units -- input: face + 'x=1'
  /(\w)=(\d)/d.exec(face + 'x=1').indices [[2,5],[2,3],[4,5]]
  same with du                            [[2,5],[2,3],[4,5]]

[5] the flag's properties
  re.hasIndices / re.flags                true / d
  new RegExp('a', 'ygsmid').flags         dgimsy
```

**왜 그런가**

- ★★ **`indices` 는 `[[0,3],[0,1],[2,3]]`** — 칸마다 `[시작, 끝)` 이고, `indices.groups` 가 이름으로 같은 쌍을 준다(`{"k":[0,1],"v":[2,3]}` · 그 객체도 null 프로토타입).
- ★★★ **앞에 `face` 를 붙이면 `x` 는 `2` 에서 시작하고, `du` 로 바꿔도 `2`** — 매치 위치는 **문자열의 코드 유닛 번호**다. `u` 는 패턴이 무엇을 한 글자로 보느냐를 바꿀 뿐 **자리 번호를 코드 포인트로 다시 매기지 않는다.**
- ★★ **04번의 `length` 와 같은 단위**다 — 그래서 `line.slice(...indices.groups.v)` 가 그대로 맞는다.
- ★ **`d` 가 없으면 `indices` 는 아예 없다**(`undefined` · `'indices' in plain` 이 `false`). 참여하지 않은 그룹의 칸은 `undefined`.

### 8. 없는 판에서는 **「없다」가 아니라 문법 오류·「함수가 아니다」로** 보인다 ★★

**출력**

```js
// js28b-30g-es2025-node.js
// The same three ES2025 additions, asked of node -- what does an engine without them say?
const show = (label, f) => {
  try { console.log("  " + label.padEnd(40) + f()); }
  catch (e) { console.log("  " + label.padEnd(40) + e.constructor.name + " 「" + e.message + "」"); }
};
show("typeof RegExp.escape", () => typeof RegExp.escape);
show("RegExp.escape('a.b')", () => RegExp.escape("a.b"));
show("new RegExp('(?<y>a)|(?<y>b)')", () => String(new RegExp("(?<y>a)|(?<y>b)")));
show("new RegExp('a(?i:b)c')", () => String(new RegExp("a(?i:b)c")));
```

```text
===== node20 js28b-30g-es2025-node.js (exit=0) =====
  typeof RegExp.escape                    undefined
  RegExp.escape('a.b')                    TypeError 「RegExp.escape is not a function」
  new RegExp('(?<y>a)|(?<y>b)')           SyntaxError 「Invalid regular expression: /(?<y>a)|(?<y>b)/: Duplicate capture group name」
  new RegExp('a(?i:b)c')                  SyntaxError 「Invalid regular expression: /a(?i:b)c/: Invalid group」
```

```text
===== google-chrome --headless --virtual-time-budget=2000 --dump-dom 'js28b-page.html?js28b-30f-es2025.web.js' | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' | sed 's/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&amp;/\&/g' (exit=0) =====
[1] RegExp.escape
  RegExp.escape("a.b*c")                        \x61\.b\*c
  RegExp.escape("1+1=2")                        \x31\+1\x3d2
  RegExp.escape("$5 (approx)")                  \$5\x20\(approx\)
  RegExp.escape("x|y")                          \x78\|y
  RegExp.escape("- ,")                          \x2d\x20\x2c
  RegExp.escape("foo_bar")                      \x66oo_bar
  new RegExp(user).test('axb')                  true
  new RegExp(RegExp.escape(user)).test('axb')   false
  new RegExp(RegExp.escape(user)).test('a.b')   true
  RegExp.escape(12)                             TypeError 「input argument must be a string」

[2] one name in two alternatives
  date.exec('2026-09').groups                   {"y":"2026"}
  date.exec('09/2026').groups                   {"y":"2026"}
  date.exec('09/2026') -- array                 ["09/2026","<undefined>","2026"]
  '09/2026'.replace(date, '[$<y>]')             [2026]
  new RegExp('(?<y>a)(?<y>b)')                  SyntaxError 「Invalid regular expression: /(?<y>a)(?<y>b)/: Duplicate capture group name」
  new RegExp('(?:(?<y>a)|(?<y>b))\\k<y>').exec('bb')["bb","<undefined>","b"]

[3] modifiers -- a flag for part of a pattern
  /a(?i:b)c/.test("abc")                        true
  /a(?i:b)c/.test("aBc")                        true
  /a(?i:b)c/.test("ABc")                        false
  /a(?i:b)c/.test("abC")                        false
  /a(?-i:b)c/i.test('AbC') / ('ABC')            true / false
  new RegExp('(?g:a)')                          SyntaxError 「Invalid regular expression: /(?g:a)/: Invalid group」
```

**왜 그런가**

- ★★ **node 두 판(블록이 한 글자도 같다)** — `RegExp.escape` 는 `TypeError 「RegExp.escape is not a function」`, 다른 갈래의 같은 이름은 `SyntaxError 「… Duplicate capture group name」`, `(?i:…)` 는 `SyntaxError 「… Invalid group」`.
- ★★★ **그 문구는 「기능이 없다」를 말하지 않는다** — 중복 이름은 **옛 규칙으로 판정한 문법 오류**, 수정자는 **알 수 없는 그룹 문법**이다. 문구만 보면 「패턴을 잘못 썼다」로 읽힌다.
  ★ 그래서 판별은 문구가 아니라 **기능 판별 블록**(요약의 `js28b-features.js` — 세 판에 같은 스크립트)으로 한다.
- ★★ **Chrome 151 의 `RegExp.escape("a.b*c")` 는 `\x61\.b\*c`** — 첫 글자 `a` 가 `\x61` 이 됐다. 가운데 영숫자(`b`)는 그대로다.
- ★ **같은 갈래 안의 중복은 ES2025 에서도 `Duplicate capture group name`** 이다(`(?<y>a)(?<y>b)`). 허용된 것은 **한 매치에서 둘이 함께 참여할 수 없는** 경우뿐이다.

### 9. 명세는 **어느 답을 찾을지(의미)** 를 정하고, **어떻게 찾을지(알고리즘)** 는 엔진에 맡긴다 ★★★

- ★★★ **어느 답인가** — 왼쪽에서 가장 먼저 시작하는 매치, 그 안에서는 **수량자는 욕심 쪽 먼저 · 갈래는 왼쪽 먼저** 시도했을 때 처음 성공하는 것. 그 우선순위가 명세의 뜻이다.
- ★★★ **백트래킹처럼 보이는 이유** — 명세는 패턴을 **매처**(상태와 **연속**을 받아 결과를 돌려주는 추상 함수)로 풀어 적는다. 한 선택지로 연속을 불러 실패하면 **다음 선택지로 다시 부른다** — 우선순위를 정의하는 가장 짧은 방법이 이 모양이다.
  ★ 그러나 이것은 **결과를 정의하는 서술**이지 실행 방법의 지시가 아니다. **같은 결과를 내는 한** 상태 집합 방식으로 찾아도 명세에 맞는다 — V8 의 `l` 엔진이 그 예다(5번에서 같은 `false` 를 냈다).
- ★★ **5번의 no 칸은 명세 밖의 일**이다 — 명세에는 시간도 되돌이 수도 없다. 답을 끝내 내기만 하면 명세 위반이 아니다. 「끝나지 않는다」는 **V8(Irregexp)·파이썬 `re` 의 구현**이 가진 성질이다.
- ★ **룩비하인드 안의 캡처 방향은 명세의 사실**이다 — 역방향 평가가 뜻에 들어 있다(2번 `[4]`). 엔진이 바꾸면 **답이 바뀌므로** 엔진의 몫이 아니다.

### 10. 셋이 다 받은 것은 **폭발하는 그 패턴 하나** — RE2 는 **지나온 길을 기억해야 하는 문법**을 전부 거절했다 ★★★

**출력**

```js
// js28b-30-h-syntax-v8.js
// 인자로 받은 패턴을 u 플래그로 컴파일만 한다 -- 받으면 accept, 아니면 reject 와 문구. js28b-30u-syntax.sh 가 부른다.
for (const src of process.argv.slice(2)) {
  try { new RegExp(src, "u"); console.log("accept"); }
  catch (e) { console.log("reject\t" + e.constructor.name + " 「" + e.message + "」"); }
}
```

```go
// js28b-30-h-syntax-re2.go
// 인자로 받은 패턴을 Go 의 regexp(RE2)로 컴파일만 한다. js28b-30u-syntax.sh 가 부른다.
package main

import (
	"fmt"
	"os"
	"regexp"
)

func main() {
	for _, src := range os.Args[1:] {
		if _, err := regexp.Compile(src); err != nil {
			fmt.Printf("reject\t%T 「%v」\n", err, err)
		} else {
			fmt.Println("accept")
		}
	}
}
```

```python
# js28b-30-h-syntax-re.py
# 인자로 받은 패턴을 파이썬 re 로 컴파일만 한다. js28b-30u-syntax.sh 가 부른다.
import re
import sys

for src in sys.argv[1:]:
    try:
        re.compile(src)
        print("accept")
    except re.error as e:
        print("reject\t" + type(e).__name__ + " 「" + str(e) + "」")
```

```sh
# js28b-30u-syntax.sh
#!/usr/bin/env bash
# 같은 패턴 열두 개를 세 엔진에 컴파일만 시킨다 -- V8(node20, u 플래그) · Go regexp(RE2) · 파이썬 re.
# 패턴 목록은 여기 한 곳에만 있고, 세 보조 파일은 인자로 받는다.
set -u -o pipefail
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
GO="$HOME/.local/opt/go/bin/go"
BIN="$PWD/build-30"
mkdir -p "$BIN"
"$GO" build -o "$BIN/syntax" js28b-30-h-syntax-re2.go || { echo "go build failed"; exit 1; }
P=('^(a+)+$' '(a)\1' '(?=a)a' '(?<=a)b' '(?<=a+)b' '(?<n>a)' '(?P<n>a)' '(?<n>a)\k<n>' '\p{L}' '(?i:a)b' 'a++' '(?>a+)')
mapfile -t js < <("$N20" js28b-30-h-syntax-v8.js "${P[@]}")
mapfile -t go < <("$BIN/syntax" "${P[@]}")
mapfile -t py < <(python3 js28b-30-h-syntax-re.py "${P[@]}")
printf '  %-16s %-8s %-8s %s\n' "pattern" "V8" "RE2" "python re"
split=0
for i in "${!P[@]}"; do
  a="${js[$i]%%$'\t'*}"; b="${go[$i]%%$'\t'*}"; c="${py[$i]%%$'\t'*}"
  printf '  %-16s %-8s %-8s %s\n' "${P[$i]}" "$a" "$b" "$c"
  if [ "$a" != "$b" ] || [ "$b" != "$c" ]; then split=$((split + 1)); fi
done
echo ""
echo "  messages of the rejections:"
for i in "${!P[@]}"; do
  for pair in "V8:${js[$i]}" "RE2:${go[$i]}" "py:${py[$i]}"; do
    case $pair in *reject*) printf '  %-16s %-4s %s\n' "${P[$i]}" "${pair%%:*}" "${pair#*$'\t'}" ;; esac
  done
done
echo ""
echo "patterns on which the three engines do not all agree: $split / ${#P[@]}"
```

```text
===== ./js28b-30u-syntax.sh (exit=0) =====
  pattern          V8       RE2      python re
  ^(a+)+$          accept   accept   accept
  (a)\1            accept   reject   accept
  (?=a)a           accept   reject   accept
  (?<=a)b          accept   reject   accept
  (?<=a+)b         accept   reject   reject
  (?<n>a)          accept   accept   reject
  (?P<n>a)         reject   accept   accept
  (?<n>a)\k<n>     accept   reject   reject
  \p{L}            accept   accept   reject
  (?i:a)b          reject   accept   accept
  a++              reject   reject   accept
  (?>a+)           reject   reject   accept

  messages of the rejections:
  (a)\1            RE2  *syntax.Error 「error parsing regexp: invalid escape sequence: `\1`」
  (?=a)a           RE2  *syntax.Error 「error parsing regexp: invalid or unsupported Perl syntax: `(?=`」
  (?<=a)b          RE2  *syntax.Error 「error parsing regexp: invalid named capture: `(?<=a)b`」
  (?<=a+)b         RE2  *syntax.Error 「error parsing regexp: invalid named capture: `(?<=a+)b`」
  (?<=a+)b         py   error 「look-behind requires fixed-width pattern」
  (?<n>a)          py   error 「unknown extension ?<n at position 1」
  (?P<n>a)         V8   SyntaxError 「Invalid regular expression: /(?P<n>a)/u: Invalid group」
  (?<n>a)\k<n>     RE2  *syntax.Error 「error parsing regexp: invalid escape sequence: `\k`」
  (?<n>a)\k<n>     py   error 「unknown extension ?<n at position 1」
  \p{L}            py   error 「bad escape \p at position 0」
  (?i:a)b          V8   SyntaxError 「Invalid regular expression: /(?i:a)b/u: Invalid group」
  a++              V8   SyntaxError 「Invalid regular expression: /a++/u: Nothing to repeat」
  a++              RE2  *syntax.Error 「error parsing regexp: invalid nested repetition operator: `++`」
  (?>a+)           V8   SyntaxError 「Invalid regular expression: /(?>a+)/u: Invalid group」
  (?>a+)           RE2  *syntax.Error 「error parsing regexp: invalid or unsupported Perl syntax: `(?>`」

patterns on which the three engines do not all agree: 11 / 12
```

**왜 그런가**

- ★★★ **셋이 다 받은 것은 `^(a+)+$` 하나**(`11 / 12` 가 갈렸다). 문법 검사로는 폭발을 막지 못한다 — 막는 것은 **엔진의 방식**이다.
- ★★★ **RE2 가 거절한 것** — 역참조(`\1`·`\k<n>`) · 룩어헤드 · 룩비하인드(가변·고정 모두) · 소유 수량자 · 원자 그룹.
  공통점은 **「앞에서 무엇을 잡았나」나 「이 자리에서 따로 탐색해 보기」가 필요한 것**이다. 상태 집합 방식은 **같은 자리의 상태를 하나로 합치기** 때문에 그 기억을 들고 다닐 수 없다.
  ★ 그 대가로 `go doc regexp` 가 「guaranteed to run in time linear in the size of the input」 을 약속한다 — 5번 Go 열의 yes 다섯 칸이 그 약속의 관찰이다.
- ★★ **명명 그룹** — JS 는 `(?<n>)` 만(`(?P<n>` 은 `Invalid group`), 파이썬 `re` 는 `(?P<n>)` 만(`(?<n>` 은 `unknown extension ?<n`), Go 는 둘 다.
- ★ **`a++`·`(?>…)` 는 파이썬 3.12 만 받았다** — 백트래킹을 **끊는** 문법이라 백트래킹 엔진에만 뜻이 있다. JS 에는 없다.

### 11. 스위치는 **두 판 다 있고 기본값이 꺼져 있다** — 켜도 **열하나 중 여섯**만 받는다 ★★

**출력**

```sh
# js28b-30v-v8flags.sh
#!/usr/bin/env bash
# 두 node 판의 V8 에 비백트래킹(선형) 엔진 스위치가 있나 -- 없다고 적기 전에 판에게 묻는다.
# --v8-options 전체를 받은 뒤 이름 줄만 거른다(파이프로 node 를 죽이지 않는다).
set -u -o pipefail
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
for n in "$N18" "$N20"; do
  echo "node $("$n" -p 'process.versions.node + "  v8 " + process.versions.v8')"
  all="$("$n" --v8-options)"
  printf '%s\n' "$all" | sed -n 's/^ *\(--[a-z-]*experimental-regexp[a-z-]*\|--regexp-backtracks-before-fallback\) .*/  \1/p'
done
```

```text
===== ./js28b-30v-v8flags.sh (exit=0) =====
node 18.19.1  v8 10.2.154.26-node.28
  --enable-experimental-regexp-engine
  --default-to-experimental-regexp-engine
  --trace-experimental-regexp-engine
  --enable-experimental-regexp-engine-on-excessive-backtracks
  --regexp-backtracks-before-fallback
node 20.19.6  v8 11.3.244.8-node.33
  --enable-experimental-regexp-engine
  --default-to-experimental-regexp-engine
  --trace-experimental-regexp-engine
  --enable-experimental-regexp-engine-on-excessive-backtracks
  --regexp-backtracks-before-fallback
```

```js
// js28b-30-h-lflag.js
// V8 의 l 플래그(선형 엔진) 한 줄씩 -- 받아 주나, 거절하면 무엇이라 하나. js28b-30w-linear.sh 가 부른다.
const rows = [
  ["^(a+)+$", "l"], ["^a+$", "l"], ["(a)\\1", "l"], ["(?=a)a", "l"], ["(?<=a)b", "l"],
  ["a{2,5}", "l"], ["(?<n>a)b", "l"], ["^(a+)+$", "il"], ["\\p{L}", "ul"], ["a", "gl"], ["a", "yl"],
];
let ok = 0;
for (const [src, flags] of rows) {
  let r;
  try { const re = new RegExp(src, flags); r = "accepted   flags=" + re.flags; ok += 1; }
  catch (e) { r = e.constructor.name + " 「" + e.message + "」"; }
  console.log("  " + ("/" + src + "/" + flags).padEnd(14) + r);
}
console.log("  accepted " + ok + " / " + rows.length);
```

```sh
# js28b-30w-linear.sh
#!/usr/bin/env bash
# l 플래그 -- 스위치 없이 / 스위치를 켜고(node 두 판). 선형 엔진이 무엇을 거절하는지 한 표로.
set -u -o pipefail
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
echo "[1] node20 without --enable-experimental-regexp-engine"
"$N20" js28b-30-h-lflag.js
echo ""
echo "[2] node20 --enable-experimental-regexp-engine"
"$N20" --enable-experimental-regexp-engine js28b-30-h-lflag.js
echo ""
echo "[3] node18 --enable-experimental-regexp-engine"
"$N18" --enable-experimental-regexp-engine js28b-30-h-lflag.js
```

```text
===== ./js28b-30w-linear.sh (exit=0) =====
[1] node20 without --enable-experimental-regexp-engine
  /^(a+)+$/l    SyntaxError 「Invalid flags supplied to RegExp constructor 'l'」
  /^a+$/l       SyntaxError 「Invalid flags supplied to RegExp constructor 'l'」
  /(a)\1/l      SyntaxError 「Invalid flags supplied to RegExp constructor 'l'」
  /(?=a)a/l     SyntaxError 「Invalid flags supplied to RegExp constructor 'l'」
  /(?<=a)b/l    SyntaxError 「Invalid flags supplied to RegExp constructor 'l'」
  /a{2,5}/l     SyntaxError 「Invalid flags supplied to RegExp constructor 'l'」
  /(?<n>a)b/l   SyntaxError 「Invalid flags supplied to RegExp constructor 'l'」
  /^(a+)+$/il   SyntaxError 「Invalid flags supplied to RegExp constructor 'il'」
  /\p{L}/ul     SyntaxError 「Invalid flags supplied to RegExp constructor 'ul'」
  /a/gl         SyntaxError 「Invalid flags supplied to RegExp constructor 'gl'」
  /a/yl         SyntaxError 「Invalid flags supplied to RegExp constructor 'yl'」
  accepted 0 / 11

[2] node20 --enable-experimental-regexp-engine
  /^(a+)+$/l    accepted   flags=l
  /^a+$/l       accepted   flags=l
  /(a)\1/l      SyntaxError 「Invalid regular expression: /(a)\1/l: Cannot be executed in linear time」
  /(?=a)a/l     SyntaxError 「Invalid regular expression: /(?=a)a/l: Cannot be executed in linear time」
  /(?<=a)b/l    SyntaxError 「Invalid regular expression: /(?<=a)b/l: Cannot be executed in linear time」
  /a{2,5}/l     accepted   flags=l
  /(?<n>a)b/l   accepted   flags=l
  /^(a+)+$/il   SyntaxError 「Invalid regular expression: /^(a+)+$/il: Cannot be executed in linear time」
  /\p{L}/ul     SyntaxError 「Invalid regular expression: /\p{L}/lu: Cannot be executed in linear time」
  /a/gl         accepted   flags=gl
  /a/yl         accepted   flags=ly
  accepted 6 / 11

[3] node18 --enable-experimental-regexp-engine
  /^(a+)+$/l    accepted   flags=l
  /^a+$/l       accepted   flags=l
  /(a)\1/l      SyntaxError 「Invalid regular expression: /(a)\1/: Cannot be executed in linear time」
  /(?=a)a/l     SyntaxError 「Invalid regular expression: /(?=a)a/: Cannot be executed in linear time」
  /(?<=a)b/l    SyntaxError 「Invalid regular expression: /(?<=a)b/: Cannot be executed in linear time」
  /a{2,5}/l     accepted   flags=l
  /(?<n>a)b/l   accepted   flags=l
  /^(a+)+$/il   SyntaxError 「Invalid regular expression: /^(a+)+$/: Cannot be executed in linear time」
  /\p{L}/ul     SyntaxError 「Invalid regular expression: /\p{L}/: Cannot be executed in linear time」
  /a/gl         accepted   flags=gl
  /a/yl         accepted   flags=ly
  accepted 6 / 11
```

**왜 그런가**

- ★★ **다섯 스위치가 두 판에 똑같이 있다** — `--enable-experimental-regexp-engine`(`l` 을 알아듣게) · `--default-to-experimental-regexp-engine` · `--trace-experimental-regexp-engine` · `--enable-experimental-regexp-engine-on-excessive-backtracks` · `--regexp-backtracks-before-fallback`.
- ★★★ **스위치 없이 `/x/l` 은 `SyntaxError 「Invalid flags supplied to RegExp constructor 'l'」`**(`0 / 11`). 켜면 **`6 / 11`**.
- ★★★ **켜도 거절되는 것** — 역참조 · 룩어헤드 · 룩비하인드 · **`i` 플래그** · **`\p{L}`(`u`)** — 문구는 전부 `Cannot be executed in linear time`(node18 은 문구에 플래그를 안 붙인다). **RE2 보다도 좁다** — RE2 는 `\p{L}` 과 `(?i:…)` 를 받았다(10번).
- ★★ **이 엔진은 V8 의 실험 기능**이다 — ECMA-262 에 `l` 플래그는 없다. 그래서 실무 처방은 이 스위치가 아니라 **폭발하는 모양을 안 쓰기 · 입력 길이 제한 · 신뢰할 수 없는 패턴을 받지 않기**다.
  ★ 6번의 「되돌이가 많으면 갈아타기」는 **답을 바꾸지 않고 멈춤만 막는** 스위치라는 점에서 쓸모가 다르다 — 그러나 역시 기본값이 꺼져 있다.

### 12. 파이썬 `re` 는 **node 쪽과 같이 잘렸고**, 룩비하인드는 **고정 길이만**, `\p{L}` 은 **받지 않는다** ★★

- ★★ **5번의 파이썬 열은 node 열과 같은 모양**(`10`·`20` yes, `30` 부터 no)이다 — 파이썬 `re` 도 **백트래킹 엔진**이다. Go 열과는 다르다.
- ★★★ **가변 룩비하인드** — JS 는 `(?<=a+)b` 를 받고(2번 `[3]`), 파이썬은 `error 「look-behind requires fixed-width pattern」` 으로 거절한다(10번). 고정 길이 `(?<=a)b` 는 둘 다 받는다.
- ★★ **`\p{L}` 을 받지 않는 쪽은 파이썬 `re`**(`bad escape \p at position 0`). Go 와 V8(`u`)은 받는다.
- ★ **Rust 는 부적용** — 정규식이 표준 라이브러리에 없고 `regex` **외부 크레이트**의 몫이라 Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))이 다루지 않는다. 파이썬 쪽 정본은 파이썬 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **46번**(`re`) — 폴더가 아직 없어 이 문서가 직접 던졌다.

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js28b-30a-groups.js` | ★★ 캡처·비캡처·명명 · `groups` 의 null 프로토타입 · 반복 안의 캡처 비우기 · `\k` 의 두 뜻 | node20 1벌 + node18 1벌(**문구 한 줄 갈림**) |
| `js28b-30b-lookaround.js` | ★★ 둘러보기 네 가지 · 길이 0 · 가변 룩비하인드 · 역방향 캡처 | node20 1벌 + node18 대조 1벌(같음) |
| `js28b-30c-unicode.js` | ★★★ 플래그 없음/`u`/`v` × 패턴 일곱 · 「갈린 줄 6 / 7」 · `\u{…}` · `\p{…}` | node20 1벌 + node18 1벌(**`v` 열 갈림**) |
| `js28b-30d-vflag.js` | ★★ 집합 연산 · 글자열 속성 · `v` 가 거절하는 소스 「4 / 5」 | node20 1벌 + node18 1벌(**`v` 줄 전부 갈림**) |
| `js28b-30e-indices.js` | ★ `indices` · 코드 유닛 단위 · `flags` 순서 | node20 1벌 + node18 대조 1벌(같음) |
| `js28b-30f-es2025.web.js` | ★★ `RegExp.escape` · 중복 명명 그룹 · 수정자 | **Chrome 151 만** |
| `js28b-30g-es2025-node.js` | ★ 같은 셋을 없는 판에 — 예외 종류와 문구 | node20 1벌 + node18 대조 1벌(같음) |
| `js28b-30x-explode.sh` | ★★★ n 다섯 × 엔진 여섯의 「2초 안에 끝났나」 · 「21 / 30」 | 셸 1벌(**시간을 안 찍는다**) |
| `js28b-30y-steps.sh` | ★★★ 되돌이 한도 이분 탐색 · 비율 · node18 동일 · K 별 첫 n | 셸 1벌 |
| `js28b-30u-syntax.sh` | ★★ 패턴 열둘 × V8·RE2·파이썬 받나/거절하나 · 「11 / 12」 | 셸 1벌 |
| `js28b-30v-v8flags.sh` · `js28b-30w-linear.sh` | ★ 선형 엔진 스위치의 존재 · `l` 이 받는 것 「6 / 11」 | 셸 1벌씩 |
| `js28b-vdiff.sh` · `js28b-versions.sh` | 두 판이 갈린 탐침 수 · 이 문서의 출력이 **어느 판에서 나왔나** + 판별 기능 표 | 1벌씩 |

★ **재대조** — 제출 전에 캡처를 처음부터 다시 돌려(`./capture.sh blocks-30-recheck 30`) `normalize-shaky.py` 로 견줬다. 셸 탐침의 참/거짓 칸과 되돌이 표까지 **다시 돌려 같아야 하는 칸**이다.

두 node 판 대조기(이 배치 전체의 node 탐침). 이 주제의 줄(`js28b-30…`) 중 `DIFFERS` 는 **30a · 30c · 30d** 셋이다. 그 밖의 `DIFFERS` 줄은 **다른 주제의 탐침**이다(같은 배치가 한 대조기를 공유한다).

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
