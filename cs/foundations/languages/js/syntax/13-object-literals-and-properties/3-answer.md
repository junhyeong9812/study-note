# js/syntax/13 — 객체 리터럴과 프로퍼티: 「키는 전부 문자열이고, 정수처럼 생긴 것만 앞줄에 선다」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **node v20.19.6**(기본 판) · **node v18.19.1**(대조) · **Google Chrome 151.0.7922.173** · x86-64 Linux 에서 실제로 돌려 얻은 것이고,
> 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 하나도 없다).
>
> ★★★ **이 문서는 순서가 그대로 실린 블록을 갖고 있다.**
> 「순서가 보장되지 않는 출력을 싣지 마라」는 규칙의 예외인 이유는 **이 순서가 명세가 못 박은 것**이기 때문이다.
> 근거의 갈래를 섞지 않는다 — **보장의 근거는 명세이고, 아래 출력은 확인이다.**
> ★★ **예외는 `e.constructor.name` 과 `e.message` 로만 찍었다** — 스택트레이스에는 절대 경로가 박혀 재현이 안 된다.
> ★★★ **이 주제에는 두 판이 갈린 블록이 0개다.** 그래서 양쪽을 나란히 실은 자리가 없다.
> ★★ **표준 출력과 표준 오류를 한 블록에도 안 섞었다** — 이 주제의 블록은 전부 표준 출력이다.
>
> **이 파일이 인용하는 출력을 낸 소스** — 전문은 [1-question.md](1-question.md) 의 같은 번호 문항에 있다.

```text
// js12b-13a-order.js
// js12b-13b-intkeys.js
// js12b-13c-computed.js
// js12b-13d-views.js
// js12b-hb-browser.js
// js12b-versions.sh
// js12b-vdiff.sh
```

> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | Node 스택트레이스의 **절대 경로** — 한 줄도 싣지 않았다 | ★★★ **열거 순서**(명세가 못 박은 것) |
> | 브라우저 UA 문자열의 뒷자리 | ★★★ **정수 키 판정** · **로그의 이름과 순서** |
> | 엔진 내부의 저장 방식(관찰 불가) | ★★ **디스크립터의 모양** · 뷰 일곱 종의 `true`/`false` 격자 |
>
> ★ **이 주제의 블록에는 주소도 시간도 난수도 안 찍힌다.** 같은 판에서 다시 돌리면 한 글자도 안 변한다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 넣은 순서와 나온 순서 — **세 덩어리로 갈리고 첫 덩어리만 정렬된다** ★★★

**출력**

```text
===== node20 js12b-13a-order.js (exit=0) =====
[1] inserted order  vs  Reflect.ownKeys order
#   inserted      ownKeys       bucket
0   "b"           "0"           1 array index
1   "2"           "1"           1 array index
2   Symbol(s1)    "2"           1 array index
3   "a"           "10"          1 array index
4   "1"           "b"           2 string
5   "0"           "a"           2 string
6   Symbol(s2)    "-1"          2 string
7   "10"          "01"          2 string
8   "-1"          "1.5"         2 string
9   "01"          Symbol(s1)    3 symbol
10  "1.5"         Symbol(s2)    3 symbol

[2] the four views, in order
Object.keys             ["0","1","2","10","b","a","-1","01","1.5"]
Object.values           ["int 0","int 1","int 2","int 10","str b","str a","str -1","str 01","str 1.5"]
getOwnPropertyNames     ["0","1","2","10","b","a","-1","01","1.5"]
getOwnPropertySymbols   ["Symbol(s1)","Symbol(s2)"]
Reflect.ownKeys         ["\"0\"","\"1\"","\"2\"","\"10\"","\"b\"","\"a\"","\"-1\"","\"01\"","\"1.5\"","Symbol(s1)","Symbol(s2)"]
JSON.stringify keys     ["0","1","2","10","b","a","-1","01","1.5"]
for...in                ["0","1","2","10","b","a","-1","01","1.5"]
spread { ...o } keys    ["0","1","2","10","b","a","-1","01","1.5"]

[3] does the order survive a delete + re-add?  (string keys are insertion-ordered)
start                   ["a","b","c"]
delete a; o2.a = 9      ["b","c","a"]
{3:_,1:_,2:_}           ["1","2","3"]
delete 1; o3[1] = 9     ["1","2","3"]

[4] the same rule on a Map -- insertion order only, no integer bucket
Map keys                ["\"b\"","\"2\"","Symbol(s1)","\"a\"","\"1\"","\"0\"","Symbol(s2)","\"10\"","\"-1\"","\"01\"","\"1.5\""]
```

**왜 그런가**

- ★★★ **나온 순서는 `"0" "1" "2" "10" "b" "a" "-1" "01" "1.5" Symbol(s1) Symbol(s2)`** 다.
  넣은 순서(`"b"` 가 첫째, `"1.5"` 가 마지막)와 **완전히 다르다.**
- ★★★ `bucket` 칸이 **`1 array index` 넷 · `2 string` 다섯 · `3 symbol` 둘**로 나뉜다.
  ① 덩어리는 **넣은 순서와 무관하게 숫자 오름차순**이고(`"2"` 를 `"0"` 보다 먼저 넣었는데 `"0"` 이 앞에 있다),
  ② 와 ③ 은 **넣은 순서 그대로**다(`"b"` 가 `"a"` 보다 앞, `Symbol(s1)` 이 `Symbol(s2)` 보다 앞).
- ★★ `[2]` 의 **일곱 뷰가 전부 같은 순서**다. 다른 것은 순서가 아니라 **보는 범위**다 —
  심볼은 `Reflect.ownKeys` 와 `getOwnPropertySymbols` 에만 나오고 나머지 다섯에는 안 나온다.
- ★★ `[3]` **문자열 키는 자리를 잃는다** — `delete o2.a; o2.a = 9` 뒤에 `["b","c","a"]` 로 맨 뒤로 간다.
  **정수 키는 제자리로 돌아온다** — `delete o3[1]; o3[1] = 9` 뒤에도 `["1","2","3"]` 이다.
  ★★★ **②는 삽입순이고 ①은 정렬이기 때문**이다. 같은 조작의 결과가 **덩어리에 따라 다르다**는 것이 이 주제의 대표 사고다.
- ★ `[4]` `Map` 은 **넣은 순서 그대로** 열한 쌍을 내놓는다. `"2"` 가 `"0"` 보다 앞에 있고 심볼도 섞인 자리에 그대로 있다 —
  **덩어리가 없다.** 순서가 의미를 가지면 이쪽을 쓴다.

### 2. 어떤 키가 앞줄에 서는가 — **스물세 후보 중 여섯만 배열 인덱스다** ★★★

**출력**

```text
===== node20 js12b-13b-intkeys.js (exit=0) =====
[1] is this key an array index?   (a=inserted first, z=inserted last)
key                 ownKeys                       verdict         Array check
"0"                 ["0","a","z"]                 ARRAY INDEX     arr.length=1
"1"                 ["1","a","z"]                 ARRAY INDEX     arr.length=2
"2"                 ["2","a","z"]                 ARRAY INDEX     arr.length=3
"10"                ["10","a","z"]                ARRAY INDEX     arr.length=11
"4294967293"        ["4294967293","a","z"]        ARRAY INDEX     arr.length=4294967294
"4294967294"        ["4294967294","a","z"]        ARRAY INDEX     arr.length=4294967295
"4294967295"        ["a","4294967295","z"]        string key      arr.length=0
"4294967296"        ["a","4294967296","z"]        string key      arr.length=0
"01"                ["a","01","z"]                string key      arr.length=0
"00"                ["a","00","z"]                string key      arr.length=0
"1.0"               ["a","1.0","z"]               string key      arr.length=0
"1.5"               ["a","1.5","z"]               string key      arr.length=0
"-0"                ["a","-0","z"]                string key      arr.length=0
"-1"                ["a","-1","z"]                string key      arr.length=0
"+1"                ["a","+1","z"]                string key      arr.length=0
" 1"                ["a"," 1","z"]                string key      arr.length=0
"1 "                ["a","1 ","z"]                string key      arr.length=0
"1e2"               ["a","1e2","z"]               string key      arr.length=0
"0x1"               ["a","0x1","z"]               string key      arr.length=0
"9007199254740993"  ["a","9007199254740993","z"]  string key      arr.length=0
""                  ["a","","z"]                  string key      arr.length=0
"NaN"               ["a","NaN","z"]               string key      arr.length=0
"Infinity"          ["a","Infinity","z"]          string key      arr.length=0

array-index keys 6 / 23

[2] the boundary itself -- 2**32-2 is the last array index, 2**32-1 is not
2**32-2 = 4294967294   ["4294967294","a","z"]
2**32-1 = 4294967295   ["a","4294967295","z"]
max array length       4294967295
a[2**32-1] -> length 0  keys ["4294967295"]

[3] number keys are converted to strings first -- the key is always a string
n[1]=a; n['1']=b; n[1.0]=c  -> keys ["1"]  value c
f[1.5]=x; f['1.5']=y        -> keys ["1.5"]  value y
neg[-0]='x'                 -> keys ["0"]
big[1e21], big[1e2]         -> keys ["100","1e+21"]
```

**왜 그런가**

- ★★★ **`ARRAY INDEX` 는 6 / 23** 이다 — `"0"`·`"1"`·`"2"`·`"10"`·`"4294967293"`·`"4294967294"`.
  판정법은 앞뒤에 문자열 키(`a`·`z`)를 박아 두고 **후보가 `a` 앞으로 끌려가는지** 보는 것이다.
  끌려갔으면 ① 덩어리, 제자리면 ② 덩어리다.
- ★★★ **`"4294967294"` 는 배열 인덱스이고 `"4294967295"`(2³²−1)는 아니다.**
  ★ 왜 하필 거기서 끊기나 — **배열의 최대 `length` 가 2³²−1** 이고 **인덱스는 `length` 보다 작아야** 하기 때문이다.
  같은 블록의 `Array check` 칸이 그것을 보인다: `arr[4294967294] = 1` 이면 `length` 가 **4294967295**(최댓값)가 되고,
  `arr[4294967295] = 1` 이면 **`length` 가 0 인 채** 문자열 키로만 들어간다(`[2]` 의 마지막 줄).
- ★★ `"01"`·`"1.0"`·`"-0"`·`"1e2"` 는 **전부 문자열 키**다.
  판정 기준은 「숫자로 읽히나」가 아니라 **「그 숫자를 다시 문자열로 만들면 원래 글자와 같나」** 이다 —
  `String(Number("01"))` 은 `"1"` 이라 `"01"` 과 다르므로 탈락이다. `"1.0"`·`"1e2"`·`"-0"` 도 같은 이유로 탈락한다.
  ★ `"-1"`·`"+1"`·`" 1"`·`"1 "`·`"0x1"`·`""`·`"NaN"`·`"Infinity"`·`"9007199254740993"` 도 전부 ②로 떨어진다.
- ★★ `[3]` `n[1]`·`n["1"]`·`n[1.0]` 세 번 써도 **서랍은 하나**(`["1"]`)이고 값은 마지막에 쓴 `"c"` 다.
  **숫자는 저장되기 전에 문자열이 된다** — 키는 원리상 숫자일 수 없다.
- ★ `big[1e21]` 의 키는 **`"1e+21"`** 이다. `big[1e2]` 는 `"100"` 이다.
  **숫자를 문자열로 바꾸는 규칙이 그대로 키를 정한다** — 그래서 큰 수에서 지수 표기가 키에 박힌다.

### 3. 키 자리에 객체를 넣으면 — **`toString` 이 불리고 힌트는 `string` 이다** ★★★

**출력**

```text
===== node20 js12b-13c-computed.js (exit=0) =====
[1] plain object as a computed key -- which method is called, with which hint?
{ [plain]: 1 }        keys ["K1"]   log ["toString"]
{ [prim]: 1 }         keys ["K2"]   log ["Symbol.toPrimitive hint=string"]
o3[plain] = 1         keys ["K1"]   log ["toString"]
o3[plain]  (read)     value 1        log ["toString"]
{ [sym]: 1 }          symbols ["Symbol(S)"]   log []

[2] evaluation order -- computed keys are evaluated in source order, before the value
keys ["a","b"]   order ["key-a","val-a","key-b","val-b"]

[3] duplicate keys -- later wins, and the earlier VALUE is still evaluated
{ a: 1st, b: mid, a: 2nd }  -> {"a":2,"b":9}   order ["first","mid","second"]
key position follows the FIRST appearance: ["a","b"]

[4] shorthand, methods, get/set -- what descriptor does each make?
o7.val    value=7 w=true e=true c=true
o7.m      value="[fn m]" w=true e=true c=true
o7.g      get=get g set=set g e=true c=true
o7.arrow  value="[fn arrow]" w=true e=true c=true
m.prototype exists?     false
arrow.prototype exists? false

[5] __proto__ in an object literal is special -- but only in two of these five forms
form                        prototype is P?   own keys
{ __proto__: P }            true              []
{ "__proto__": P }          true              []
{ ['__proto__']: P }        false             ["__proto__"]
{ __proto__ }  shorthand    false             ["__proto__"]
{ __proto__() {} }  method  false             ["__proto__"]

JSON.parse('{"__proto__":{"x":1}}') -> proto is Object.prototype? true   own keys ["__proto__"]
```

**왜 그런가**

- ★★★ `[1]` 첫 줄의 로그가 **`["toString"]`** 이다. `valueOf` 도 달려 있는데 **그쪽은 안 불린다.**
  `ToPropertyKey` 가 `ToPrimitive` 를 **힌트 `string`** 으로 부르기 때문이고, 그 힌트에서는 `toString` 이 먼저다.
- ★★★ `Symbol.toPrimitive` 가 있으면 **그것이 이기고**, 로그가 **`["Symbol.toPrimitive hint=string"]`** 로 힌트까지 찍는다.
  `toString` 은 달려 있어도 안 불린다.
- ★★ **읽기도 똑같다.** `o3[plain]` 을 읽는 줄에서도 로그가 `["toString"]` 이다 —
  **대괄호 안의 값은 쓸 때든 읽을 때든 매번 키로 변환된다.**
  ★ 심볼을 키로 주면 **로그가 비어 있다**(`[]`). 심볼은 이미 키가 될 수 있는 타입이라 변환이 필요 없다.
- ★★ `[3]` **버려지는 값도 평가된다** — 로그가 `["first","mid","second"]` 로 셋이다.
  `a: say("first", 1)` 의 값이 계산되고 나서 버려진다. **부수효과가 있는 식이면 그 부수효과는 남는다.**
  ★★★ 그리고 **자리는 첫 등장을 따른다** — 결과가 `{"a":2,"b":9}` 이고 `Object.keys` 가 `["a","b"]` 다.
  **값은 나중 것이 이기고 자리는 첫 것이 이긴다** — 둘이 동시에 성립한다.
- ★★★ `[5]` **다섯 형태 중 프로토타입이 바뀌는 것은 둘**이다 —
  `{ __proto__: P }` 와 `{ "__proto__": P }`. 이 둘은 own 키가 **비어 있다**(`[]`).
  나머지 셋(`{ ["__proto__"]: P }`·단축 `{ __proto__ }`·메서드 `{ __proto__() {} }`)은
  **프로토타입을 안 바꾸고 `"__proto__"` 라는 평범한 own 키를 만든다.**
  ★ 따옴표는 상관없고 **계산된 키인지, 단축인지, 메서드인지**가 가른다.
- ★ **`JSON.parse` 는 프로토타입을 안 바꾼다.** 결과의 프로토타입이 `Object.prototype` 이고 own 키에 `"__proto__"` 가 들어 있다.
  ★★ 그러므로 프로토타입 오염은 `JSON.parse` 자체가 아니라 **그 결과를 `obj[k] = v` 로 옮겨 쓰는 코드**에서 난다 —
  `obj["__proto__"] = v` 는 15번 주제의 **접근자**를 건드린다.
- ★ `[4]` 는 14번 주제로 넘어가는 다리다 — **단축 표기·메서드·화살표는 전부 `w,e,c` 가 `true,true,true` 인 데이터 프로퍼티**이고
  `get`/`set` 만 **접근자**다. ★ 메서드 단축과 화살표는 **`prototype` 을 안 만든다**(그래서 `new` 로 못 부른다).

### 4. 어느 뷰가 무엇을 보는가 — **own 과 enumerable 두 축의 격자다** ★★

**출력**

```text
===== node20 js12b-13d-views.js (exit=0) =====
[1] which view sees which property?
property      own?   enum?  keys   for-in  getOwnPropertyNames  in    hasOwn
ownEnum       true   true   true   true    true                 true  true
ownHidden     true   false  false  false   true                 true  true
protoEnum     false  true   false  true    false                true  false
protoHidden   false  false  false  false   false                true  false
ownSym        true   true   false  false   true                 true  true   (symbols: getOwnPropertySymbols column)
protoSym      false  true   false  false   false                true  false   (symbols: getOwnPropertySymbols column)

[2] the views themselves
Object.keys(o)               ["ownEnum"]
for...in over o              ["ownEnum","protoEnum"]
getOwnPropertyNames(o)       ["ownEnum","ownHidden"]
getOwnPropertySymbols(o)     ["Symbol(ownSym)"]
Reflect.ownKeys(o)           ["ownEnum","ownHidden","Symbol(ownSym)"]
Object.entries(o)            [["ownEnum","oe"]]
JSON.stringify(o)            {"ownEnum":"oe"}
{ ...o } own keys            ["ownEnum","Symbol(ownSym)"]
Object.assign({}, o) keys    ["ownEnum","Symbol(ownSym)"]

[3] for...in walks the chain; Object.keys does not
for...in over a 3-level chain  ["own","fromParent","fromGrandparent"]
Object.keys                    ["own"]
Object.prototype is enumerable? []
```

**왜 그런가**

- ★★★ **`Object.keys` 칸이 `true` 인 줄은 한 줄**(`ownEnum`)뿐이다.
  `Object.keys` 의 조건이 **「own ∧ enumerable ∧ 문자열」** 세 개를 전부 요구하기 때문이다.
- ★★★ **`for...in` 과 `getOwnPropertyNames` 는 서로 다른 축 하나씩을 버린다** —
  `for...in` 은 **own 을 안 따져서** `protoEnum` 을 더 보고,
  `getOwnPropertyNames` 는 **enumerable 을 안 따져서** `ownHidden` 을 더 본다.
  ★ **`in` 은 아무것도 안 따진다** — 네 줄이 전부 `true` 다.
- ★★ **심볼 키는 `Object.keys` 에도 `for...in` 에도 안 나온다.**
  `Reflect.ownKeys` 와 `getOwnPropertySymbols` 만 본다.
- ★★ **그런데 `{ ...o }` 와 `Object.assign` 은 심볼을 가져간다** — 둘 다 결과 키가 `["ownEnum","Symbol(ownSym)"]` 이다.
  ★★★ **「열거 가능한 것만 복사한다」와 「열거에 나온다」가 같은 말이 아니다** — 11번에서 본 규칙의 정확한 범위가 여기서 정해진다.
  복사는 **own ∧ enumerable** 이면 심볼이어도 가져가고, 열거(`Object.keys`·`for...in`)는 **문자열만** 본다.
- ★ `[3]` 마지막 줄의 `[]` 는 **`Object.prototype` 의 프로퍼티가 전부 `enumerable: false` 라는 증명**이다.
  `for...in` 이 체인을 **끝까지** 타는데도(세 단계가 다 나온다) `toString`·`hasOwnProperty` 가 안 나오는 이유가 그것이다.
  ★ 「`for...in` 이 `Object.prototype` 에서 멈춘다」가 아니라 **「거기 있는 것들이 안 보이게 표시돼 있다」** 가 맞다.

### 5. 키가 될 수 있는 것은 무엇인가 ★★★

- ★★★ **두 가지뿐이다 — 문자열과 심볼.** 다른 타입은 키가 될 수 없다.
- ★★ 그 밖의 값을 키 자리에 넣으면 **`ToPropertyKey` 가 바꾼다.**
  심볼이면 그대로 두고, 아니면 `ToPrimitive`(힌트 `string`) → `ToString` 을 거친다.
  3번 답의 로그가 그 절차를 그대로 보인다 — 객체를 넣으면 `toString` 이 불리고, 심볼을 넣으면 아무것도 안 불린다.
- ★ **`o[-0]` 의 키는 `"0"` 이라 `o[0]` 과 같은 서랍**이다(2번 답 `[3]` 의 `neg` 줄).
  ★★ 이것이 **33번 주제의 `Object.is`** 와 어긋나는 자리다 — `Object.is(0, -0)` 은 `false` 인데
  **키로 쓰면 둘이 같아진다.** 비교 규칙과 키 변환 규칙은 **다른 물건**이다.

### 6. 「배열 인덱스」의 조건을 한 문장으로 ★★★

- ★★★ 「숫자로 읽히면 배열 인덱스」가 틀린 이유는 **`Number()` 를 통과하는 글자가 훨씬 많기** 때문이다.
  반례 셋 — **`"01"`**(`Number` 는 1 로 읽지만 되돌리면 `"1"`) · **`"1.0"`**(되돌리면 `"1"`) ·
  **`"1e2"`**(되돌리면 `"100"`). 셋 다 2번 답에서 `string key` 로 떨어졌다.
  ★ 조건은 「**그 문자열을 숫자로 읽고 다시 문자열로 만들었을 때 원래 글자와 같고, 그 값이 2³²−1 보다 작은 정수**」다.
- ★★ 상한이 2³²−1 인 이유는 **배열의 `length` 와 묶여 있기** 때문이다.
  `length` 가 부호 없는 32비트 수라 최댓값이 2³²−1 이고, **인덱스는 `length` 보다 작아야** 하므로 인덱스의 상한은 그보다 하나 아래다.
- ★ `a[4294967295] = 1` 을 하면 **`length` 는 0** 이고 키는 `["4294967295"]` 다(2번 답 `[2]` 의 마지막 줄).
  **배열인데 요소가 아니라 그냥 프로퍼티**로 들어간 것이다.

### 7. 중복 키는 왜 조용히 지나가는가 ★★

- ★★★ **엄격 모드는 지금 중복 키를 안 막는다.** 막던 것은 **ES5 의 엄격 모드**이고 **ES6 에서 그 금지가 사라졌다.**
  12번 주제의 문법 격자가 두 모드 모두 `OK {"a":3}` 을 내놓는 것으로 그것을 확인했다.
- ★★ 「나중 것이 이긴다」와 「첫 자리를 쓴다」가 동시에 성립하는 것은 **3번 답 `[3]` 의 두 줄**로 확인했다 —
  값은 `{"a":2,"b":9}` 이고 키 순서는 `["a","b"]` 다.
  ★ 두 번째 `a` 가 **새 프로퍼티를 만드는 것이 아니라 기존 프로퍼티에 값을 다시 쓰는 것**이라 자리가 안 움직인다.
  1번 답 `[3]` 에서 **지웠다 다시 넣으면 자리가 움직였던 것**과 나란히 놓고 보면 규칙이 하나로 읽힌다.
- ★ 실무에서 위험한 자리는 **객체를 기계로 만드는 코드**다 —
  스프레드로 합치거나 템플릿으로 키를 생성할 때 **충돌이 경고 한 줄 없이 값을 잡아먹는다.**

### 8. `__proto__` 는 어디서 특별한가 ★★★

- ★★★ **`{ __proto__: x }` 는 프로토타입을 바꾸고 `{ ["__proto__"]: x }` 는 own 프로퍼티를 만든다.**
  3번 답 `[5]` 가 다섯 형태를 전수로 가른다. 갈림선은 **「계산되지 않은 보통 키 자리인가」** 하나다.
- ★★ 단축 `{ __proto__ }` 와 메서드 `{ __proto__() {} }` 는 **둘 다 평범한 own 프로퍼티**다.
  ★ 「이름이 `__proto__` 면 특별하다」가 아니라 **「그 자리에 그 형태로 쓰였을 때만」** 특별하다.
- ★★ 이 문법은 **명세의 부록(Annex B — 웹 브라우저용 추가 기능)** 에 있다. 본문이 아니다.
  그래도 믿어도 되는 이유는 **웹 호환을 위해 모든 엔진이 구현하기 때문**이고, 실제로 Node 두 판과 Chrome 151 이 같은 답을 냈다.
  ★ 다만 그것은 **확인**이지 보장의 근거가 아니다 — 근거는 「부록에 규범적으로 적혀 있다」는 사실 쪽이다.
- ★ `JSON.parse` 의 결과를 `obj[k] = v` 로 옮겨 쓰면 **그때 오염이 일어날 수 있다.**
  `JSON.parse` 자체는 own 키로만 넣었지만(3번 답의 마지막 줄), 그 키를 꺼내 **대입문으로 다시 쓰면**
  `Object.prototype` 의 `__proto__` 접근자가 불린다. 그 접근자의 정체는 15번 주제가 다룬다.

### 9. 이 순서는 왜 「보장」인가 ★★★

- ★★★ 「객체의 키 순서는 보장되지 않는다」는 말은 **ES5 시절까지 맞았다.**
  ES2015 가 `[[OwnPropertyKeys]]` 로 **세 덩어리**를 못 박으면서
  `Object.keys`·`getOwnPropertyNames`·`Reflect.ownKeys`·`JSON.stringify` 가 그 순서에 묶였고,
  **마지막까지 남아 있던 `for...in` 을 ES2020 이 못 박았다**([for-in order 제안](https://tc39.es/proposal-for-in-order/)).
- ★★★ **두 판과 브라우저에서 같은 줄이 나온 것은 보장의 근거가 아니다.**
  형제 편에서 실측한 대로 **「여러 판에서 같았다」는 그 자체로 아무것도 보장하지 않는다** —
  오히려 우연히 같으면 **더 위험하다.** 보장의 근거는 **명세 문서**이고, 이 문서의 출력은 **확인**이다.
  ★ 그래서 머리말에서 둘을 갈라 선언했다.
- ★★ **`Reflect.ownKeys` 와 `for...in` 은 같은 판이 아니다.** 앞엣것은 ES2015, 뒤엣것은 ES2020 이다.
  ★ 「한 판에 다 정해졌다」로 뭉뚱그리면 **`for...in` 이 가장 늦게 합류했다는 사실**이 지워진다.
- ★ 순서를 그대로 실은 블록이 규칙 위반이 아닌 이유 —
  **금지되는 것은 「명세가 보장하지 않는 순서」이고, 이 순서는 명세가 보장한다.** 그래서 근거를 같이 적으라는 단서가 붙는다.

### 10. 보장인가 엔진 사정인가 ★★★

**출력**

```text
===== ./js12b-vdiff.sh (exit=0) =====
js12b-12a-shortcircuit.js    identical
js12b-12b-grid.js            identical
js12b-12c-assign.js          identical
js12b-12s-strict.js          identical
js12b-12x-forms.js           identical
js12b-12y-caret.js           identical
js12b-13a-order.js           identical
js12b-13b-intkeys.js         identical
js12b-13c-computed.js        identical
js12b-13d-views.js           identical
js12b-14a-dump.js            identical
js12b-14b-configurable.js    identical
js12b-14c-freeze.js          DIFFERS
    40c40
    < fa.toSorted()   OK  [1,2,3]
    ---
    > fa.toSorted()   OK  [1,2,3]  returned [1,2,3]
js12b-14s-strict.js          identical
js12b-15a-chain.js           identical
js12b-15b-proxy.js           identical
js12b-15c-shadow.js          identical
js12b-15d-misc.js            identical
js12b-15e-pycontrast.js      identical

identical 18  ·  differs 1  ·  total 19
```

```text
===== google-chrome --headless --dump-dom js12b-page.html | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' | sed 's/&lt;/</g; s/&gt;/>/g; s/&amp;/\&/g' (exit=0) =====
  engine                                Chrome/151.0.0.0
  12  0 ?? 'D' / 0 || 'D'               [0,"D"]
  12  ||= does not write                []
  12  = x || y writes                   ["set"]
  12  a?.b[f()] skips f                 calls 0
  12  a ?? b || c compiles?             SyntaxError: Unexpected token '||'
  12  new a?.b() compiles?              SyntaxError: Invalid optional chain from new expression
  13  enumeration order                 ["1","2","b","a","01","Symbol(s)"]
  13  '4294967295' is an index?         ["a","4294967295","z"]
  13  computed key calls toString       ["K"] ["toString"]
  13  __proto__ literal vs computed     true,false
  14  literal vs defineProperty desc    {"value":1,"writable":true,"enumerable":true,"configurable":true} | {"value":1,"writable":false,"enumerable":false,"configurable":false}
  14  isFrozen {} / prevExt {}          [false,true]
  14  freeze is shallow                 {"d":{"n":2}}
  14  strict write to frozen            TypeError: Cannot assign to read only property 'a' of object '#<Object>'
  15  chain of new TypeError            TypeError -> Error -> Object -> null
  15  String(Object.create(null))       TypeError: Cannot convert object to primitive value
  15  write does not walk               o/p/own:true
  15  non-writable proto blocks         TypeError: Cannot assign to read only property 'v' of object '#<Object>'
  15  Symbol.hasInstance overrides      true
```

**왜 그런가**

- **이 주제에서 두 판이 갈린 칸은 0개다.** 대조기가 19블록을 두 판에서 돌려 **갈린 것은 한 블록**뿐이라고 세는데,
  그 한 블록은 **14번 주제의 `toSorted`**(ES2024, v18 에 없음)이고 **13번 주제의 네 블록은 전부 동일**하다.
- ★★ **호스트가 정하는 칸은 0개**다. Chrome 151 의 네 줄 —
  열거 순서 `["1","2","b","a","01","Symbol(s)"]` · `"4294967295"` 가 인덱스가 아닌 것 ·
  계산된 키가 `toString` 을 부르는 것 · `__proto__` 가 리터럴에서만 특별한 것(`true,false`) — 이 전부 Node 쪽과 같다.
- ★★★ **부적용인 창은 「두 번 컴파일」(엄격/비엄격)** 이다.
  객체 리터럴에서 모드를 탈 뻔한 칸은 **중복 키 하나뿐**이었고 그마저 ES6 에서 사라져,
  이제 **두 모드를 견줄 칸이 아예 없다.** 「재 봤더니 같았다」가 아니라 **「잴 것이 없다」** 이고,
  그 구분 자체가 결론이다 — **객체 리터럴은 엄격 모드와 무관한 문법**이라는 뜻이기 때문이다.
  ★ 「안 쟀다」는 다르다. 이 문서에서 안 잰 것은 **속도**이고, 그래서 속도 주장이 한 줄도 없다.
- ★ **엔진의 내부 저장 방식은 근거로 쓸 수 없다.** 정수 키를 따로 저장한다는 이야기는 **관찰할 수 없고**,
  이 문서가 관찰한 것은 **밖으로 나오는 순서**뿐이다. 둘을 같은 문장에 섞으면 구현 세부를 언어 사실로 적는 것이 된다.

### 11. 경계 — 어디까지가 이 주제인가 ★★

- **세 플래그의 의미** → [14번](../14-property-descriptors-and-freezing/2-summary.md) ·
  **체인 순회** → [15번](../15-prototype-chain/2-summary.md)과 목록의 **18번 주제** 「`for...in` 과 열거」 ·
  **심볼의 성질** → 목록의 **22번 주제** 「`Symbol` 과 잘 알려진 심볼」 ·
  **`ToPrimitive`** → [02번](../02-coercion-and-loose-equality/2-summary.md).
- ★★★ 11번이 실측한 것은 「`{ ...o }` 는 **자기 것이고 열거 가능한 것만** 가져간다」였다.
  이 주제가 채워 넣은 정의는 **「열거 가능」이 정확히 무엇을 가르는가**이다 —
  4번 답의 격자가 그것을 own × enumerable 두 축으로 펼쳤고,
  ★★ 덤으로 **복사는 심볼을 가져가는데 열거는 안 가져간다**는 어긋남까지 드러냈다.
- ★★ 파이썬의 dict 와 **같은 것** — 「순서가 나중에 언어 보장으로 승격됐다」는 이력.
  **정반대인 것** — 파이썬은 **삽입 순서 하나뿐**이라 덩어리가 없고, 키 요건도 **해시 가능한 아무 값**이다.
  JS 는 **문자열 아니면 심볼**뿐이고 **정수처럼 생긴 것이 앞줄에 선다.**
  자세한 것은 Python 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **12번** 「dict 와 키 요건」에 있다.
- ★ 이 주제가 끝까지 책임지는 것 셋 —
  ① **키가 문자열 아니면 심볼이라는 것**(그리고 아닌 것이 어떻게 바뀌는지)
  ② **열거 순서 세 덩어리와 「배열 인덱스」의 정확한 경계**
  ③ **어느 리터럴 형태가 어떤 프로퍼티를 만드는가**(`__proto__` 의 다섯 형태 포함).

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js12b-13a-order.js` | ★★★ **세 덩어리 열거 순서** · 일곱 뷰가 같은 순서인 것 · 지웠다 넣으면 덩어리마다 다른 것 · `Map` 대비 | node20 1벌 + node18 대조 1벌 |
| `js12b-13b-intkeys.js` | ★★★ **배열 인덱스 6 / 23** · 2³²−1 경계 · 숫자 키가 문자열이 되는 규칙 | node20 1벌 + node18 대조 1벌 |
| `js12b-13c-computed.js` | ★★★ **`ToPropertyKey` 로그**(`toString` · `Symbol.toPrimitive` 힌트 `string`) · 평가 순서 · 중복 키 · 다섯 리터럴 형태의 디스크립터 · **`__proto__` 5형태** | node20 1벌 + node18 대조 1벌 |
| `js12b-13d-views.js` | ★★ **뷰 일곱 종 × 프로퍼티 여섯 종 격자** · 복사와 열거가 심볼에서 어긋나는 것 | node20 1벌 + node18 대조 1벌 |
| `js12b-hb-browser.js` · `js12b-page.html` | ★★ **호스트가 정하는 칸 0개**(이 주제의 대표 네 줄) | Chrome 151 1벌 |
| `js12b-vdiff.sh` | **19블록 중 갈린 것 1개**(그 하나는 14번 주제) | 1벌 |
| `js12b-versions.sh` | 이 문서의 모든 출력이 **어느 판에서 나왔나** | 1벌 |

**구현 의존 항목** — 다음은 **이 환경(node 20.19.6 / 18.19.1 · Chrome 151 · x86-64 Linux)에서만** 그렇다.

- ★★ **`console.log`/`util.inspect` 의 표시 형식** — 이 문서는 그것을 근거로 쓰지 않고 `JSON.stringify` 로만 찍었다.
- ★ **심볼의 `String()` 표현**(`Symbol(s1)`)은 명세가 정하지만, **어느 뷰가 그것을 어떻게 보여 주는가**는 도구의 몫이다.
- ★ **엔진의 내부 저장 방식** — 관찰하지 않았고 근거로 쓰지 않았다.

**키가 문자열 아니면 심볼인 것 · `ToPropertyKey` 가 힌트 `string` 으로 `ToPrimitive` 를 부르는 것 · 열거 순서 세 덩어리 · 배열 인덱스의 정의(2³²−1 미만) · 중복 키에서 나중 값이 이기고 첫 자리를 쓰는 것 · 버려지는 값도 평가되는 것 · 각 리터럴 형태가 만드는 디스크립터 · `__proto__:` 가 비계산·비단축·비메서드 형태에서만 특별한 것은 구현 의존이 아니다.**
어느 엔진에서도 같아야 한다(마지막 항목은 Annex B — 규범적 선택 사항이지만 웹 엔진 전부가 구현한다).

**안 돌려 본 것 / 못 잰 것 / 부적용인 창**

- **안 돌려 본 것** — 다른 엔진(SpiderMonkey·JavaScriptCore)에서의 같은 격자 ·
  키가 10만 개일 때의 순서(덩어리 규칙은 개수와 무관하지만 **안 돌려 봤다**) ·
  `Object.defineProperties` 로 한 번에 넣었을 때의 순서 · Node 18 보다 낮은 판.
- ★ **못 잰 것** — **정수 키와 문자열 키의 비용 차이.** 「정수 키가 빠르다」·「객체가 `Map` 보다 느리다」는
  **재지 않았다.** 그래서 이 문서에는 속도 주장이 한 줄도 없다.
- ★★ **부적용인 창** — **두 번 컴파일**(엄격/비엄격). 10번 답에 적은 대로 **잴 칸이 아예 없다.**
  ★ **③ 브랜드 태그**도 이 주제에서는 안 쓰인다 — 객체 리터럴이 만드는 것은 전부 평범한 객체라 브랜드로 가를 칸이 없다.

**판이 올랐을 때 다시 돌려야 하는 것**

- ★★ **없다고 말하고 싶지만 한 가지 있다** — **새 리터럴 형태가 추가되면** 3번 답 `[4]`·`[5]` 를 다시 찍어야 한다.
  형태가 늘면 「어떤 디스크립터를 만드나」 표에 줄이 하나 더 생긴다.
- **열거 순서와 배열 인덱스의 정의는 다시 돌릴 필요가 없다** — ES2015·ES2020 이후 바뀐 적이 없다.
- ★ **브라우저 대조는 판이 오르면 다시 찍는 쪽이 싸다** — 호스트가 정하는 칸이 0개라는 결론은 **그 판에서의 결론**이다.
