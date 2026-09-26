# js/syntax/02 — 강제 변환과 `==` 대 `===`: 「엔진이 무엇을 먼저 부르나」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **node v20.19.6**(기본 판) · **node v18.19.1**(대조) · **Google Chrome 151.0.7922.173** · x86-64 Linux 에서 실제로 돌려 얻은 것이고,
> 블록은 **전부 캡처 파일에서 조립**했다.
> 소스는 `js01b-02a-toprimitive-spy.js`\~`js01b-02g-browser.js` 와 `js01b-vdiff.sh` 다.
>
> ★★ **격자는 손으로 한 칸도 안 채웠다** — 15개 값을 서로 던져 **한 연산자당 225칸**, 세 연산자로 **675칸**을 받았다.
> ★★ **예외는 `e.constructor.name` 과 `e.message` 로만 찍었다** — 스택트레이스에는 절대 경로가 박힌다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | Node 스택트레이스의 **절대 경로** — 한 줄도 싣지 않았다 | ★★★ **675칸 격자 전부** · 참인 칸의 개수(67·13·12) |
> | 예외 **문구** — `Cannot convert object to primitive value` 등 | ★★★ **`valueOf`/`toString` 의 호출 순서와 횟수** |
> | `String(new Date(0))` — **시간대·로캘**에 달렸다. 어느 블록에도 안 실었다 | ★★★ **힌트 문자열** `default`·`number`·`string` |
> | UA 의 `Chrome/151.0.0.0` | ★★ **예외의 종류** · **`+` 가 문자열로 기우는 것** · 종료 코드 |

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 로그를 심은 객체를 연산자에 던지면 — **힌트가 셋이고 `default` 는 숫자 쪽이다** ★★★ 본체

**출력**

```text
===== node20 js01b-02a-toprimitive-spy.js (exit=0) =====
[1] 힌트가 number 인 자리 — valueOf 가 먼저다
  o * 2                  => 14                 | 부른 것: valueOf()
  o - 0                  => 7                  | 부른 것: valueOf()
  o < 1                  => false              | 부른 것: valueOf()
  Number(o)              => 7                  | 부른 것: valueOf()
  +o                     => 7                  | 부른 것: valueOf()

[2] 힌트가 string 인 자리 — toString 이 먼저다
  `${o}`                 => S                  | 부른 것: toString()
  String(o)              => S                  | 부른 것: toString()
  ({})[o] = 1            => S                  | 부른 것: toString()
  [o] + ''               => S                  | 부른 것: toString()

[3] 힌트가 default 인 자리 — 기본 객체는 number 처럼 군다
  o + 1                  => 8                  | 부른 것: valueOf()
  o + 'x'                => 7x                 | 부른 것: valueOf()
  o == 7                 => true               | 부른 것: valueOf()

[4] 첫 메서드가 원시 값을 안 돌려주면 다음 것을 부른다
  valueOf -> obj         => S1                 | 부른 것: valueOf() -> toString()
  toString -> obj        => 7                  | 부른 것: toString() -> valueOf()
  both -> obj            => TypeError: Cannot convert object to primitive value | 부른 것: valueOf() -> toString()

[5] Symbol.toPrimitive 가 있으면 나머지 둘은 아예 안 불린다
  o + 1                  => 100                | 부른 것: [Symbol.toPrimitive]("default")
  `${o}`                 => 99                 | 부른 것: [Symbol.toPrimitive]("string")
  o * 2                  => 198                | 부른 것: [Symbol.toPrimitive]("number")
```

**왜 그런가**

- ★★★ **`o + 1` 은 `valueOf` 를 먼저 부른다.** 힌트가 `default` 인데 **기본 객체는 `default` 를 `number` 처럼** 다루기 때문이다.
  ★★ 「`+` 는 문자열 연산자니까 `toString` 이겠지」가 **가장 흔한 오답**이고, 로그가 그것을 바로 반증한다.
  ★ `+` 가 문자열로 기우는 것은 **`ToPrimitive` 가 끝난 다음** 단계의 일이다 — 두 단계를 한 단계로 보면 틀린다.
- ★★★ **`` `${o}` `` 와 `[o] + ''` 는 둘 다 `toString`** 이다.
  템플릿은 힌트를 `string` 으로 보내고, 배열을 문자열로 만들 때는 **원소마다 `String()` 을 부르므로** 역시 `string` 이 된다.
  ★ **한 겹 감쌌을 뿐인데 순서가 뒤집힌다** — `o + ''` 는 `valueOf` 인데 `[o] + ''` 는 `toString` 이다.
- ★★★ **`[4]` 의 셋째 줄은 `valueOf` 와 `toString` 을 둘 다 부른 뒤** `TypeError: Cannot convert object to primitive value` 를 던진다.
  로그에 `valueOf() -> toString()` 이 찍혀 있다 — **두 번 다 실패해야** 터진다.
  ★ 둘째 줄은 반대 순서(`toString() -> valueOf()`)가 찍혔다. **힌트가 `string` 이면 순서가 통째로 뒤집힌다.**
- ★★ **`[5]` 에서 `valueOf` 는 한 번도 안 불렸다.** `Symbol.toPrimitive` 가 있으면 **나머지 둘을 아예 안 본다.**
- ★★ **힌트 문자열은 `default`·`number`·`string` 셋**이고, 그것이 로그에 그대로 찍혔다.
  `o + 1` 이 `default`, `` `${o}` `` 가 `string`, `o * 2` 가 `number` 다.
- ★ **`o == 7` 이 `valueOf` 를 부르는 것은 `o + 1` 과 같은 이유**다 — 느슨한 비교도 힌트를 `default` 로 보낸다.

### 2. `Date` 를 연산자에 던지면 — **순서가 아니라 힌트가 갈아 끼워진다** ★★★

**출력**

```text
===== node20 js01b-02b-date-hint.js (exit=0) =====
[1] Date 는 무엇을 부르나
  d + 1   ->
      toString() 이 불렸다
  d * 1   ->
      valueOf() 가 불렸다
  d - 0   ->
      valueOf() 가 불렸다
  `${d}`  ->
      toString() 이 불렸다

[2] 그래서 같은 연산자가 타입을 다르게 낸다
  typeof (date + 1) : string
  typeof (date - 0) : number
  typeof ({} + 1)   : number

[3] 진짜 이유 — Date 에는 제 Symbol.toPrimitive 가 있다
  typeof Date.prototype[Symbol.toPrimitive] : function
  typeof Object.prototype[Symbol.toPrimitive]: undefined
  hint "default" 로 직접 부르면 타입이 : string
  hint "number"  로 직접 부르면 타입이 : number
  hint "string"  로 직접 부르면 타입이 : string
  hint "nope"    로 부르면 : TypeError: Invalid hint: nope
```

**왜 그런가**

- ★★★ **「순서가 반대」라는 설명이 틀렸다.** `Date.prototype` 에는 **제 `Symbol.toPrimitive`** 가 있고,
  1번의 규칙대로 **그것만 불린다.** 그 함수가 하는 일이 **힌트 `default` 를 `string` 취급**하는 것이다.
  ★★ 규칙이 깨진 게 아니라 **그대로 적용된** 결과다.
- ★★★ **힌트를 직접 주고 불러 보면** `default` 와 `string` 은 문자열을, `number` 만 숫자를 준다.
  `typeof f.call(d, "default")` 가 `string` 이라는 한 줄이 이 절의 증거다.
- ★★ **없는 힌트를 주면 `TypeError: Invalid hint: nope`** 다. **힌트가 세 글자로 닫혀 있다**는 관찰이다.
- ★★ **`typeof (date + 1)` 이 `"string"`, `typeof (date - 0)` 이 `"number"`** 인 것이 그 결과다.
  `-` 는 힌트를 `number` 로 보내므로 갈아 끼울 것이 없다.
- ★ **`Object.prototype[Symbol.toPrimitive]` 는 `undefined`** 다. 기본 객체에는 그 창구가 없다 — 그래서 `valueOf`→`toString` 순서를 탄다.

### 3. 225칸을 세 번 던지면 — **67 · 13 · 12 칸** ★★★

**출력**

```text
===== node20 js01b-02c-equality-grids.js (exit=0) =====
[==]  T = 참 · . = 거짓 · ! = 예외
       undef  null false  true     0    -0     1    ""   "0"   "1"   NaN    []   [0]    {}    0n
undef      T     T     .     .     .     .     .     .     .     .     .     .     .     .     .
null       T     T     .     .     .     .     .     .     .     .     .     .     .     .     .
false      .     .     T     .     T     T     .     T     T     .     .     T     T     .     T
true       .     .     .     T     .     .     T     .     .     T     .     .     .     .     .
0          .     .     T     .     T     T     .     T     T     .     .     T     T     .     T
-0         .     .     T     .     T     T     .     T     T     .     .     T     T     .     T
1          .     .     .     T     .     .     T     .     .     T     .     .     .     .     .
""         .     .     T     .     T     T     .     T     .     .     .     T     .     .     T
"0"        .     .     T     .     T     T     .     .     T     .     .     .     T     .     T
"1"        .     .     .     T     .     .     T     .     .     T     .     .     .     .     .
NaN        .     .     .     .     .     .     .     .     .     .     .     .     .     .     .
[]         .     .     T     .     T     T     .     T     .     .     .     .     .     .     T
[0]        .     .     T     .     T     T     .     .     T     .     .     .     .     .     T
{}         .     .     .     .     .     .     .     .     .     .     .     .     .     .     .
0n         .     .     T     .     T     T     .     T     T     .     .     T     T     .     T
  225칸 중 참 67칸 · 예외 0칸

[===]  T = 참 · . = 거짓 · ! = 예외
       undef  null false  true     0    -0     1    ""   "0"   "1"   NaN    []   [0]    {}    0n
undef      T     .     .     .     .     .     .     .     .     .     .     .     .     .     .
null       .     T     .     .     .     .     .     .     .     .     .     .     .     .     .
false      .     .     T     .     .     .     .     .     .     .     .     .     .     .     .
true       .     .     .     T     .     .     .     .     .     .     .     .     .     .     .
0          .     .     .     .     T     T     .     .     .     .     .     .     .     .     .
-0         .     .     .     .     T     T     .     .     .     .     .     .     .     .     .
1          .     .     .     .     .     .     T     .     .     .     .     .     .     .     .
""         .     .     .     .     .     .     .     T     .     .     .     .     .     .     .
"0"        .     .     .     .     .     .     .     .     T     .     .     .     .     .     .
"1"        .     .     .     .     .     .     .     .     .     T     .     .     .     .     .
NaN        .     .     .     .     .     .     .     .     .     .     .     .     .     .     .
[]         .     .     .     .     .     .     .     .     .     .     .     .     .     .     .
[0]        .     .     .     .     .     .     .     .     .     .     .     .     .     .     .
{}         .     .     .     .     .     .     .     .     .     .     .     .     .     .     .
0n         .     .     .     .     .     .     .     .     .     .     .     .     .     .     T
  225칸 중 참 13칸 · 예외 0칸

[Object.is]  T = 참 · . = 거짓 · ! = 예외
       undef  null false  true     0    -0     1    ""   "0"   "1"   NaN    []   [0]    {}    0n
undef      T     .     .     .     .     .     .     .     .     .     .     .     .     .     .
null       .     T     .     .     .     .     .     .     .     .     .     .     .     .     .
false      .     .     T     .     .     .     .     .     .     .     .     .     .     .     .
true       .     .     .     T     .     .     .     .     .     .     .     .     .     .     .
0          .     .     .     .     T     .     .     .     .     .     .     .     .     .     .
-0         .     .     .     .     .     T     .     .     .     .     .     .     .     .     .
1          .     .     .     .     .     .     T     .     .     .     .     .     .     .     .
""         .     .     .     .     .     .     .     T     .     .     .     .     .     .     .
"0"        .     .     .     .     .     .     .     .     T     .     .     .     .     .     .
"1"        .     .     .     .     .     .     .     .     .     T     .     .     .     .     .
NaN        .     .     .     .     .     .     .     .     .     .     T     .     .     .     .
[]         .     .     .     .     .     .     .     .     .     .     .     .     .     .     .
[0]        .     .     .     .     .     .     .     .     .     .     .     .     .     .     .
{}         .     .     .     .     .     .     .     .     .     .     .     .     .     .     .
0n         .     .     .     .     .     .     .     .     .     .     .     .     .     .     T
  225칸 중 참 12칸 · 예외 0칸

던진 칸 합계: 675
```

**왜 그런가**

- ★★★ **참인 칸은 `==` 가 67, `===` 가 13, `Object.is` 가 12**다.
  `===` 와 `Object.is` 는 **한 칸 차이로 보이지만 갈린 칸은 둘**이다 — `NaN`/`NaN` 이 하나 늘고 `0`/`-0` 짝이 둘 줄었다.
- ★★★ **`===` 와 `Object.is` 가 갈리는 칸은 넷**(대칭까지 세면) —
  `0`↔`-0` 두 칸이 `===` 에서 참이고 `Object.is` 에서 거짓, `NaN`↔`NaN` 한 칸이 그 반대다.
  ★ **값의 종류로 세면 자리는 둘**이다 — `±0` 과 `NaN`.
- ★★★ **`==` 격자에서 가장 넓은 행은 `false`·`0`·`-0`·`0n` 네 행**이고 **모두 같은 모양**이다.
  `false` 가 먼저 `0` 이 되고, 오른쪽도 숫자가 되어 견줘지므로 **`""`·`"0"`·`[]`·`[0]` 이 전부 참**이 된다.
- ★★ **`undefined` 와 `null` 의 두 행은 대각선 위의 2×2 블록 하나**다.
  한 문장으로 하면 「**서로만 같고 다른 어떤 것과도 안 같다**」 이다 — `0` 과도 `""` 와도 `false` 와도 거짓이다.
- ★★ **`[]` 행과 `[]` 열이 만나는 칸은 거짓**이다. **양쪽이 객체면 변환을 아예 안 하고 참조만** 본다.
  `[] == 0` 이 참인 것은 **한쪽만 객체**일 때 `ToPrimitive` 가 돌기 때문이다 — 규칙이 다른 줄이다.
- ★★ **`0n` 행은 `0` 행과 한 칸도 안 다르다.** `==` 는 BigInt 와 Number 를 **수학적 값**으로 견준다.
  그런데 **`===` 격자에서는 `0n` 이 `0n` 하고만 참**이다 — `0n === 0` 이 거짓이다(03번 주제).
- ★ **예외가 난 칸은 0개**다. **`==` 는 어떤 조합에서도 안 터진다** — 그래서 **조용히 틀린다.**
  터지는 비교였다면 이 주제는 훨씬 덜 위험했을 것이다.
- ★ **값을 thunk 로 둔 것**은 `[]` 와 `[]` 를 **매번 새 객체**로 만들기 위해서다.
  한 번 만들어 재사용했으면 `[] == []` 가 **참으로 나와 정반대 결론**이 됐을 것이다.

### 4. 유명한 식들 — **두 규칙이 겹친 것이지 마법이 아니다** ★★

**출력**

```text
===== node20 js01b-02d-famous.js (exit=0) =====
[1] [] == false
  ![]                  = false   | ToBoolean([]) 은 true 라서 !true = false
  [] == false          = true    | false -> 0 · [] -> ToPrimitive -> '' -> 0
  [].toString()        = ""      | 빈 배열의 toString 은 빈 문자열
  Number('')           = 0       | 빈 문자열의 ToNumber 는 0
  [] == ![]            = true    | 오른쪽이 false 가 되므로 위와 같은 식이 된다
  [] == []             = false   | 둘 다 객체라 ToPrimitive 를 안 하고 참조만 본다

[2] null 과 undefined 는 서로만 같다
  null == undefined    = true
  null === undefined   = false
  null == 0            = false
  null >= 0            = true
  null > 0             = false
  null <= 0            = true
  undefined == 0       = false
  Number(null)         = 0
  Number(undefined)    = NaN

[3] NaN 은 자기 자신과도 다르다
  NaN == NaN               = false
  NaN === NaN              = false
  Object.is(NaN,NaN)       = true
  [NaN].includes(NaN)      = true
  [NaN].indexOf(NaN)       = -1
  new Set([NaN,NaN]).size  = 1

[4] + 는 한쪽이 문자열이면 문자열로 기운다 — 나머지는 안 그렇다
  1 + '2'                  = "12"
  1 - '2'                  = -1
  1 * '2'                  = 2
  '3' + null               = "3null"
  3 - null                 = 3
  [1,2] + [3]              = "1,23"
  {} + []                  = "[object Object]"
  1 + 2 + '3'              = "33"
  '1' + 2 + 3              = "123"
  true + true              = 2
  'b' + 'a' + +'a' + 'a'   = "baNaNa"

[5] 관계 연산자는 문자열 둘이면 사전순이다
  '10' < '9'               = true
  10 < 9                   = false
  '10' < 9                 = false
  [] < [1]                 = true
  'a' < 'b'                = true
  NaN < 1                  = false
  NaN >= 1                 = false
```

**왜 그런가**

- ★★★ **`[] == ![]` 는 두 규칙이 겹친 것**이다.
  ① `![]` 는 **ToBoolean** 을 쓴다 — **객체는 전부 참**이므로(01번 주제) `![]` 는 `false` 다.
  ② 그러면 식이 `[] == false` 가 되고, 여기서는 **ToNumber** 가 쓰인다 — `false` 는 `0`, `[]` 는 `""` 를 거쳐 `0`.
  ★ **한 식 안에서 `!` 와 `==` 가 서로 다른 변환을 쓴다**는 것이 요점이다.
- ★★★ **`null == 0` 은 거짓인데 `null >= 0` 은 참이다.**
  `==` 표에는 `null`/`undefined` **전용 줄**이 있어 숫자로 안 바꾼다.
  관계 연산자에는 그 줄이 없어 `null` 이 `0` 으로 바뀐다. ★ **같은 값에 두 연산자가 다른 표를 쓴다.**
  ★★ 그래서 `null >= 0 && null <= 0` 이 참인데 `null == 0` 은 거짓인 **모순처럼 보이는 상태**가 나온다.
- ★★ **`includes` 와 `indexOf` 가 갈린다.** `indexOf` 만 `===` 를 쓰고, `includes`·`Set`·`Map` 키는 **SameValueZero** 를 쓴다.
  ★ **동등성 규칙이 넷**이다 — `==`·`===`·SameValue(`Object.is`)·SameValueZero(33번 주제가 정본).
- ★★ **`1 + 2 + '3'` 은 `"33"`, `'1' + 2 + 3` 은 `"123"`** 이다.
  `+` 는 **왼쪽부터** 접히므로 **문자열이 몇 번째에 들어오는지**가 결과를 가른다.
  앞엣것은 `3 + '3'` 이 되어 `"33"`, 뒤엣것은 `'12' + 3` 이 되어 `"123"` 이다.
- ★ **`'10' < '9'` 는 참**이다. 양쪽이 문자열이면 숫자로 안 바꾸고 **코드 유닛 순서**로 앞에서부터 견준다 —
  `'1'`(0x31)이 `'9'`(0x39)보다 작다(04번 주제).
- ★ **`NaN < 1` 도 `NaN >= 1` 도 거짓**이다. 관계 비교 절차는 참·거짓 말고 「**비교 불가**」를 돌려줄 수 있고,
  `NaN` 이 걸리면 그 답이 나와 **어느 쪽으로 묻든 거짓**으로 떨어진다.

### 5. 세 방향으로 바꾸면 — **falsy 목록과 `== false` 목록은 다르다** ★★

**출력**

```text
===== node20 js01b-02e-conversion-table.js (exit=0) =====
value       Number()      String()                Boolean()  == false
---------------------------------------------------------------------
undefined   NaN           "undefined"             false      false
null        0             "null"                  false      false
true        1             "true"                  true       false
false       0             "false"                 false      true
0           0             "0"                     false      true
-0          0             "0"                     false      true
1           1             "1"                     true       false
NaN         NaN           "NaN"                   false      false
Infinity    Infinity      "Infinity"              true       false
""          0             ""                      false      true
" "         0             " "                     true       true
"0"         0             "0"                     true       true
"12"        12            "12"                    true       false
"0x10"      16            "0x10"                  true       false
"1e3"       1000          "1e3"                   true       false
"12px"      NaN           "12px"                  true       false
"Infinity"  Infinity      "Infinity"              true       false
[]          0             ""                      true       true
[7]         7             "7"                     true       false
[1,2]       NaN           "1,2"                   true       false
{}          NaN           "[object Object]"       true       false
0n          0             "0"                     false      true
1n          1             "1"                     true       false

falsy 인데 `== false` 는 거짓 : undefined null NaN
truthy 인데 `== false` 가 참   : " " "0" []
둘 다 인 것                    : false 0 -0 "" 0n

★ 두 목록은 같지 않다. `if (x)` 와 `x == false` 는 다른 질문이다.
```

**왜 그런가**

- ★★★ **어긋나는 칸이 여섯**이다.
  **falsy 인데 `== false` 가 거짓**인 것은 `undefined`·`null`·`NaN` 셋이고(`==` 표의 전용 줄과 `NaN` 규칙 때문이다),
  **truthy 인데 `== false` 가 참**인 것은 `" "`·`"0"`·`[]` 셋이다(숫자로 바꾸면 `0` 이 되기 때문이다).
  ★ **`if (x)` 와 `x == false` 는 서로 부정도 아니다.**
- ★★ **`"0x10"` 이 `16`** 이다. `Number()` 는 16진·8진·2진 접두와 지수 표기를 받는다.
  `parseInt("0x10")` 도 `16` 이지만 **`Number("12px")` 는 `NaN` 이고 `parseInt("12px")` 는 `12`** 라 규칙이 다르다.
  ★ 특히 **`Number("")` 는 `0` 인데 `parseInt("")` 는 `NaN`** 이다 — 정반대다.
- ★★ **`" "`(공백 하나)이 `0`** 이다. 앞뒤 공백을 버린 뒤 빈 문자열이 되고, 빈 문자열은 `0` 이다.
  ★ **폼 입력에서 공백만 친 값이 `0` 으로 통과**하는 자리가 정확히 이것이다.
- ★★ **`[7]` 은 `7`, `[1,2]` 는 `NaN`** 이다. 배열의 `toString` 이 `"7"`·`"1,2"` 를 주고 그것을 숫자로 바꾼다.
  ★ **원소가 하나인 배열만 숫자가 된다** — `[]` 는 `""` 라서 `0` 이다.
- ★ **`Date` 를 뺀 이유는 「흔들리는 칸」이기 때문**이다. `String(new Date(0))` 에는 **시간대와 로캘**이 박힌다.
  같은 블록에 두면 다른 머신에서 재대조가 깨진다 — **선언하는 것보다 안 흔들리게 만드는 쪽**이 낫다.

### 6. `==` 를 써도 되는 자리 — **아홉 줄이 전부 같다** ★★

**출력**

```text
===== node20 js01b-02f-loose-eq-safe.js (exit=0) =====
value       x == null   x === null || x === undefined   두 칸이 같은가
----------------------------------------------------------------------
undefined   true        true                            같다
null        true        true                            같다
0           false       false                           같다
""          false       false                           같다
false       false       false                           같다
NaN         false       false                           같다
0n          false       false                           같다
[]          false       false                           같다
{}          false       false                           같다

아홉 줄 전부 같은가: true

★ 그런데 `x == null` 과 `!x` 는 전혀 다른 질문이다
value       x == null   !x      x ?? 'D'    x || 'D'
------------------------------------------------------
undefined   true        true    D           D
null        true        true    D           D
0           false       true    0           D
""          false       true                D
false       false       true    false       D
NaN         false       true    NaN         D
0n          false       true    0           D
```

**왜 그런가**

- ★★★ **`x == null` 은 `x === null || x === undefined` 와 아홉 줄에서 전부 같다.**
  근거는 `==` 표의 **`undefined`/`null` 전용 줄**이다 — 그 둘은 **서로만 같고**, 다른 어떤 값과도 참이 안 된다.
  ★ **표에 그 줄이 있기 때문에** 안전한 것이지 관습이라서가 아니다.
- ★★★ **`x == null` 과 `!x` 는 다섯 줄에서 갈린다** — `0`·`""`·`false`·`NaN`·`0n` 이다.
  「값이 비었나」와 「값이 falsy 인가」는 **다른 질문**이다.
- ★★ **`??` 는 `x == null` 편, `||` 는 `!x` 편**이다.
  `0 ?? "D"` 는 `0` 이고 `0 || "D"` 는 `"D"` 다 — 12번 주제의 자리다.
- ★ 실무 규칙 한 줄은 「**`==` 는 `x == null` 에서만 쓴다**」 이다.

### 7. 두 판과 브라우저 ★

**출력**

```text
===== ./js01b-vdiff.sh 02 (exit=0) =====
script                             node v18.19.1 대 v20.19.6
---------------------------------- -------------------------
js01b-02a-toprimitive-spy.js       같다 (한 글자도)
js01b-02b-date-hint.js             같다 (한 글자도)
js01b-02c-equality-grids.js        같다 (한 글자도)
js01b-02d-famous.js                같다 (한 글자도)
js01b-02e-conversion-table.js      같다 (한 글자도)
js01b-02f-loose-eq-safe.js         같다 (한 글자도)
```

```text
===== google-chrome --headless --disable-gpu --no-sandbox --dump-dom js01b-02g-browser.html 2>/dev/null | sed -n '/^<pre id="out">/,/<\/pre>/p' (exit=0) =====
<pre id="out">엔진                                             : Chrome/151.0.0.0
[] == false                                    : true
[] == ![]                                      : true
null == undefined                              : true
NaN === NaN                                    : false
Object.is(NaN, NaN)                            : true
1 + '2'                                        : 12
typeof (new Date(0) + 1)                       : string
typeof document.all                            : undefined
document.all == undefined                      : true
Boolean(document.all)                          : false
Object.prototype.toString.call(document.all)   : [object HTMLAllCollection]</pre>
```

**왜 그런가**

- **여섯 스크립트가 두 판에서 한 글자도 같았다.** 강제 변환은 판이 올라도 안 움직이는 층이다.
- ★★ **Chrome 과 Node 가 같은 답을 낸 것은 「다른 엔진에서도 같다」의 근거가 못 된다.**
  **둘 다 V8** 이다 — 판이 다를 뿐 엔진이 같다. ★ 이 문서가 확인한 것은 「**같은 엔진의 세 판에서 같았다**」까지다.
- ★★ **브라우저에서만 나오는 세 줄은 `document.all`** 이다.
  `typeof` 가 `"undefined"` 이고 **`== undefined` 가 참**이며 **falsy** 다 —
  `==` 표에 **호스트가 뚫어 놓은 예외**이고, 01번 주제의 그 값과 같은 것이다.
- ★ **「두 판에서 같았다」로 주장할 수 있는 것**은 「이 문서의 출력을 어느 판에서 읽어도 된다」까지이고,
  **주장할 수 없는 것**은 「명세가 그렇게 정했다」다. 보장은 비교표에서 온다.

### 8. 보장인가 사정인가 — **거의 전부가 명세 칸이다** ★★★

| 층 | 이 주제에서 여기 들어가는 것 |
|---|---|
| **명세 보장** | **느슨한 비교 표 225칸 전부** · `undefined`/`null` 전용 줄 · **양쪽이 객체면 변환 없음** · 힌트 세 가지와 그 이름 · **`default` 는 `number` 처럼** · `Symbol.toPrimitive` 가 나머지 둘을 덮는 것 · 둘 다 실패하면 `TypeError` · **`+` 만 문자열로 기우는 것** · `Object.is` 가 `===` 와 갈리는 자리가 `NaN`·`±0` 둘뿐인 것 · **`==` 가 예외를 안 던지는 것** |
| **엔진(V8) 구현** | 두 판의 V8 번호 · 여섯 스크립트가 두 판에서 같았다는 것 · Chrome 151 이 같은 답을 낸 것 |
| **이 판의 관찰** | 예외 **문구**(`Cannot convert object to primitive value` · `Invalid hint: nope`) · UA 문자열 |
| **호스트(HTML) 보장** | `document.all` 이 `== undefined` 에서 참이고 falsy 인 것 |

- ★★ **`==` 표가 엔진마다 다를 여지는 없다.** 675칸을 던져 두 판이 한 글자도 안 달랐고,
  **더 중요한 것은 표 자체가 명세에 적혀 있다는 것**이다 — 관찰이 보장을 대신하지 않는다.
- ★★ **`==` 는 예외를 안 던진다.** 다만 **`ToPrimitive` 가 던질 수는 있다** —
  `({valueOf:()=>({}) , toString:()=>({})}) == 1` 은 `TypeError` 다. **비교가 아니라 변환이 던진 것**이다.
- ★ **「엔진 구현」 칸이 얇은 이유**는 강제 변환이 **전부 표로 닫혀 있기** 때문이다. 엔진이 고를 여지가 없다.

### 9. 경계 — 어디까지가 이 주제인가 ★★

| 주제 | 정본 |
|---|---|
| `??`·`\|\|`·`?.` 와 falsy 케이스 | [목록의 **12번 주제**](../12-optional-chaining-nullish-and-logical-assignment/) |
| `===`·`Object.is`·SameValueZero 가 **`Map` 키·`includes`** 에서 갈리는 것 | 목록의 **33번 주제** |
| `Symbol.toPrimitive` 를 포함한 **잘 알려진 심볼 전반** | [목록의 **22번 주제**](../22-symbol-and-well-known-symbols/) |
| 엄격 모드가 바꾸는 규칙 | 목록의 **35번 주제** |

- ★★★ **TypeScript 갈래와의 경계** — 그쪽([`ts/syntax/01-what-ts-adds-and-erases`](../../../ts/syntax/01-what-ts-adds-and-erases/2-summary.md))은
  「**검사기가 무엇을 지우는가**」가 정본이고, 여기는 「**지워진 뒤 런타임이 무엇을 하는가**」가 정본이다.
  ★ TS 는 `==` 를 정적으로 막을 수 있지만 **막지 못하고 통과한 `==` 의 동작**은 이 문서의 표가 정한다.
- ★★ **`0n == 0` 은 03번**(숫자와 `BigInt`)으로, **`'10' < '9'` 는 04번**(문자열과 UTF-16)으로 이어진다.
- ★ **이 주제가 끝까지 책임지는 것 셋** — ① `ToPrimitive` 가 무엇을 어느 순서로 부르나
  ② `==` 표의 모든 칸 ③ `==` 를 써도 되는 자리가 어디인가.

### 10. 이 갈래의 창 ★★★

- ★★★ **새로 연 창은** 「추상 연산에 로그를 심기」다.
  명세의 `ToPrimitive` 는 이름으로 못 부르지만, **그것이 부르는 메서드는 내 객체의 것**이다 —
  `valueOf`·`toString`·`Symbol.toPrimitive` 에 `log.push` 를 넣으면 **순서와 횟수와 힌트가 그대로 찍힌다.**
  ★★ 이 창이 없으면 이 주제는 전부 「**결과값만 보고 뒤로 추측하는**」 이야기가 된다.
- ★★★ **두 번째로 연 창은** 「전수 격자」다. 15개 값을 서로 던져 **한 연산자당 225칸**을 받았다.
  ★ **손으로 표를 옮겨 적으면 반드시 틀린다** — 이 문서는 한 칸도 손으로 안 채웠다.
- ★★ **`Date` 를 변환표에서 뺀 것**은 「흔들리는 칸을 선언하는 것보다 **안 흔들리게 만드는 쪽**이 낫다」는 규칙을 따른 것이다.
  ★ 대신 `Date` 는 **타입만 찍는** 별도 블록(2번)으로 다뤘다 — 거기서는 값이 안 흔들린다.
- ★ **이 주제에서 안 돌려 본 것** — `Symbol` 을 격자에 넣는 것(행·열이 통째로 비고 `+` 에서만 터진다) ·
  `Proxy` 를 씌운 객체의 `ToPrimitive` · **다른 엔진**(SpiderMonkey·JavaScriptCore) ·
  린터(`eqeqeq`)를 실제로 돌려 보는 것 · `valueOf` 가 **부작용을 두 번 내는** 경우의 평가 횟수.

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js01b-02a-toprimitive-spy.js` | **`ToPrimitive` 의 호출 순서·횟수·힌트** · 둘 다 실패하면 `TypeError` | node20 1벌 + node18 대조 1벌 |
| `js01b-02b-date-hint.js` | `Date` 가 **제 `Symbol.toPrimitive`** 로 힌트를 갈아 끼우는 것 · 없는 힌트에 `TypeError` | node20 1벌 + node18 대조 1벌 |
| `js01b-02c-equality-grids.js` | **675칸 격자** · 참인 칸 67·13·12 · 예외 칸 0 | node20 1벌 + node18 대조 1벌 |
| `js01b-02d-famous.js` | `[] == ![]` · `null >= 0` · `NaN` 네 규칙 · `+` 만 문자열로 기우는 것 | node20 1벌 + node18 대조 1벌 |
| `js01b-02e-conversion-table.js` | 세 방향 변환표 · **falsy 와 `== false` 가 어긋나는 여섯 칸** | node20 1벌 + node18 대조 1벌 |
| `js01b-02f-loose-eq-safe.js` | `x == null` 이 아홉 줄에서 등가인 것 · `!x` 와 다섯 줄에서 갈리는 것 | node20 1벌 + node18 대조 1벌 |
| `js01b-02g-browser.js` | Chrome 151 이 **같은 답**을 내는 것 · **`document.all` 세 줄** | Chrome 151 1벌 |
| `js01b-vdiff.sh` | 여섯 스크립트가 **두 판에서 한 글자도 같다**는 것 | 1벌 |

**구현 의존 항목** — 다음은 **이 환경(node 20.19.6 / 18.19.1 · Chrome 151)에서만** 그렇다.

- ★★ **예외 메시지 문구 전부** — `Cannot convert object to primitive value` · `Invalid hint: nope`.
  **종류는 명세, 문구는 V8 의 것**이다.
- ★ **UA 문자열** `Chrome/151.0.0.0` — 브라우저가 축약한 값이다.
- ★ **「두 판에서 같았다」는 관찰** — 보장이 아니다.

**느슨한 비교 표 225칸 · `ToPrimitive` 의 순서와 힌트 · `Symbol.toPrimitive` 가 나머지 둘을 덮는 것 · `Date` 의 힌트 치환 · `+` 만 문자열로 기우는 것 · `Object.is` 가 갈리는 자리 둘 · `==` 가 예외를 안 던지는 것은 구현 의존이 아니다.**
어느 엔진에서도 같아야 한다.

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — 격자에 `Symbol` 을 넣는 것 · `Proxy` 를 씌운 객체의 변환 ·
  **다른 엔진**(SpiderMonkey·JavaScriptCore) · 린터(`eqeqeq`) 실행 · `valueOf` 의 **부작용 횟수** ·
  `document.all` 을 격자에 넣는 것(브라우저에서만 되고 열이 하나 늘어난다).
- ★ **못 잰 것** — **「엔진이 `ToPrimitive` 를 몇 번 부르는가」의 최적화 여부.**
  로그로 세면 **관찰 가능한 호출 횟수**는 알 수 있지만, 엔진이 결과를 캐시하는지 인라이닝하는지는
  **부작용이 있는 메서드를 넣어야** 알 수 있고 그러면 **내가 만든 조건의 답**이 나온다.
  ★★ 그래서 본문은 **「무엇이 불렸나」까지만** 적고 **「몇 번 불릴 수 있나」는 적지 않았다.**

**판이 올랐을 때 다시 돌려야 하는 것**

- ★★ **예외 메시지 문구** — 세 블록에 들어 있다.
- ★★ **`==` 표에 줄이 늘었는지** — 새 원시 타입이 들어오면 늘어난다(마지막이 `BigInt`, ES2020).
- ★ **`document.all` 의 예외가 그대로인지** — HTML 표준의 몫이다.
- **675칸 격자는 다시 돌릴 필요가 없다** — 표가 명세에 있고, 바꾸면 웹이 깨진다.
