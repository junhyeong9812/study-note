# js/syntax/01 — 값의 종류와 `typeof`: 「이 값은 무엇인가」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **node v20.19.6**(기본 판) · **node v18.19.1**(대조) · **Google Chrome 151.0.7922.173** · x86-64 Linux 에서 실제로 돌려 얻은 것이고,
> 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 하나도 없다).
> 소스는 `js01b-01a-typeof-grid.js`\~`js01b-01d-browser.js` 와 `js01b-vdiff.sh` 다.
>
> ★★ **예외는 `e.constructor.name` 과 `e.message` 로만 찍었다** — 스택트레이스에는 절대 경로가 박혀 재현이 안 된다.
> ★★ **표준 출력과 표준 오류를 한 블록에도 안 섞었다** — 이 주제의 블록은 전부 표준 출력이다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | Node 스택트레이스의 **절대 경로** — 한 줄도 싣지 않았다 | ★★★ **`typeof` 의 답 여덟 가지** · **브랜드 태그 문자열** |
> | 예외 **문구**(판이 오르면 바뀐다) | ★★★ **예외 종류** — `ReferenceError` · `TypeError` |
> | `document.all.length` = `8` — 페이지의 요소 수다 | ★★★ **`typeof document.all` 이 `"undefined"` 인 것** · `=== undefined` 가 `false` 인 것 |
> | UA 의 `Chrome/151.0.0.0` — 브라우저가 축약한 값 | ★★ **`Boolean(document.all)` 이 `false` 인 것** · 종료 코드 |
>
> ★ **이 주제의 블록에는 주소도 시간도 난수도 안 찍힌다.** 같은 판에서 다시 돌리면 한 글자도 안 변한다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 스물두 줄을 두 창에 던지면 — **여덟 가지 답 · 어긋나는 줄은 다섯** ★★★

**출력**

```text
===== node20 js01b-01a-typeof-grid.js (exit=0) =====
expr                  typeof      Object.prototype.toString.call
----------------------------------------------------------------
undefined             undefined   [object Undefined]
null                  object      [object Null]
true                  boolean     [object Boolean]
42                    number      [object Number]
NaN                   number      [object Number]
Infinity              number      [object Number]
10n                   bigint      [object BigInt]
"abc"                 string      [object String]
Symbol('s')           symbol      [object Symbol]
{}                    object      [object Object]
[]                    object      [object Array]
function f(){}        function    [object Function]
() => {}              function    [object Function]
class C {}            function    [object Function]
/re/                  object      [object RegExp]
new Date(0)           object      [object Date]
new Number(42)        object      [object Number]
new String('abc')     object      [object String]
Math                  object      [object Math]
JSON                  object      [object JSON]
new Map()             object      [object Map]
Object.create(null)   object      [object Object]

typeof 가 돌려줄 수 있는 문자열은 이 여덟 가지뿐이다:
  bigint boolean function number object string symbol undefined
```

**왜 그런가**

- ★★★ **두 창이 어긋나는 줄은 다섯**이다 —
  `null`(`object` 대 `[object Null]`) · `function f(){}` · `() => {}` · `class C {}`(셋 다 `function` 대 `[object Function]`) ·
  그리고 **`Object.create(null)`**(`object` 대 `[object Object]` — 프로토타입이 없는데도 같은 태그).
  ★ 앞의 넷이 「**`typeof` 의 답과 실제 종류가 다른**」 칸이고, 마지막 하나는 「**둘째 창도 못 가르는**」 칸이다.
- ★★★ **`typeof` 가 돌려준 문자열은 여덟 가지**다 — `bigint boolean function number object string symbol undefined`.
  값의 종류도 여덟(원시 일곱 + 객체)인데 **짝이 안 맞는다.** `null` 이 객체 칸으로 가고, 객체의 일부가 `function` 칸으로 나간다.
- ★★ **`class C {}` 도 `() => {}` 도 `"function"`** 이다. `typeof` 가 보는 것은 문법이 아니라 「**부를 수 있나**」 하나다.
  ★ `class` 는 `new` 없이 부르면 `TypeError` 지만 그것은 **호출 시점**의 일이고 `typeof` 의 답은 바뀌지 않는다.
- ★★ **`Object.create(null)` 의 둘째 칸이 `{}` 와 같다.** 브랜드 태그는 프로토타입 체인이 아니라 **값의 내부 성질**을 본다.
  ★ 그래서 **둘째 창으로도 「프로토타입 없는 객체」를 가릴 수 없다.**
- ★ **`Math` 와 `JSON` 은 `[object Math]`·`[object JSON]`** 이다. 둘은 생성자가 없는 **하나뿐인 객체**라 전용 태그를 받는다.
  ★ 이 태그는 `Symbol.toStringTag` 로 그 객체에 박혀 있는 것이고, **바꿀 수 있는 축**이다(34번 주제).
- ★ `new Number(42)` 가 `object` / `[object Number]` 인 것이 **래퍼 객체가 원시 값과 다른 물건**이라는 증거다(3번).

### 2. 이름이 없을 때와 아직 없을 때 — **특권은 하나뿐이고 구멍도 하나 있다** ★★★

**출력**

```text
===== node20 js01b-01b-typeof-undeclared.js (exit=0) =====
[1] 선언조차 안 된 이름
typeof neverDeclared             -> "undefined"
neverDeclared                    -> ReferenceError: neverDeclared is not defined

[2] let/const 의 TDZ 는 typeof 도 못 넘는다
typeof tdzLet (TDZ)              -> ReferenceError: Cannot access 'tdzLet' before initialization
typeof x (initialized let)       -> "number"

[3] globalThis 에 묻는 것과 typeof 는 다른 질문이다
'nope' in globalThis             -> false
typeof nope                      -> "undefined"
globalThis.nope                  -> undefined
```

**왜 그런가**

- ★★★ **`typeof` 만 「이 이름이 있나」를 묻는 도중에 안 터진다.** 다른 모든 읽기는 `ReferenceError` 다.
  명세가 `typeof` 의 피연산자를 **평가하다 실패해도 `"undefined"` 로 떨어뜨리도록** 정해 두었다.
  ★ **언어 전체에서 이 특권을 가진 자리는 여기 하나**다.
- ★★★ **그 특권이 TDZ 에는 없다.** `let tdzLet` 이 선언된 블록 안에서는 그 이름이 **이미 있는 것**이고,
  다만 **아직 못 쓰는 상태**다. 「없는 것」이 아니므로 `typeof` 도 `ReferenceError` 를 받는다.
  ★ 메시지가 다른 것이 증거다 — `is not defined`(없다) 대 `Cannot access ... before initialization`(있는데 아직).
  ★★ **그래서 「`typeof` 는 절대 안 터진다」는 틀린 문장**이고, 정확히는
  「**선언이 아예 없는 이름에 한해** `typeof` 는 안 터진다」다.
- ★★ **`"nope" in globalThis` 는 `false` 인데 `typeof nope` 는 `"undefined"`** 다.
  앞엣것은 **전역 객체의 프로퍼티**를 묻고, 뒤엣것은 **이 이름을 읽으면 무엇이 나오나**를 묻는다.
  ★ `let`/`const` 로 만든 전역은 **전역 객체에 안 올라가므로** 두 질문의 답이 갈린다.
- ★ **`globalThis.nope` 는 예외가 아니다.** 객체의 없는 프로퍼티는 `undefined` 를 준다 — **이름 조회와 프로퍼티 조회는 다른 연산**이다.
- ★ 오타가 만드는 것이 바로 이 「선언 없음」 상태다. `typeof usrename === "undefined"` 는 **오타도 조용히 통과**시킨다.

### 3. 원시 값에 점을 찍으면 — **느슨한 모드에서만 봉투가 생긴다** ★★★

**출력**

```text
===== node20 js01b-01c-boxing.js (exit=0) =====
[1] 원시 문자열에 메서드를 부르면 this 가 무엇인가
  느슨한 모드 : {"typeofThis":"object","isStringObject":true,"tag":"[object String]"}
  엄격 모드   : {"typeofThis":"number","isNumberObject":false}

[2] 래퍼는 그 호출 한 번만 살고 버려진다
  s.mine = 1 을 한 뒤 s.mine : undefined
  new String('abc') 는 남는다: 1

[3] 래퍼 객체는 원시 값과 다른 물건이다
  'abc' === new String('abc')      : false
  'abc' ==  new String('abc')      : true
  typeof new String('abc')         : object
  Boolean(new Boolean(false))      : true
  new Boolean(false) ? 'T' : 'F'   : T
  JSON.stringify(new Number(1))    : 1

[4] 래퍼가 없는 원시 값도 있다 — 부르면 바로 터진다
  (null).toString()          -> TypeError: Cannot read properties of null (reading 'toString')
  (undefined).toString()     -> TypeError: Cannot read properties of undefined (reading 'toString')
  (10n).toString()           -> 10
  Symbol('s').toString()     -> Symbol(s)
```

**왜 그런가**

- ★★★ **`[1]` 의 두 줄이 갈리는 것은 엄격 모드다.**
  느슨한 모드의 메서드는 `this` 로 **임시 래퍼 객체**를 받고(`typeof this` 가 `"object"`, `this instanceof String` 이 `true`),
  엄격 모드의 메서드는 **원시 값 그대로** 받는다(`typeof this` 가 `"number"`).
  ★★ 이것이 「래퍼가 진짜 만들어진다」는 **관찰**이다 — 「그런 것처럼 동작한다」가 아니다.
- ★★★ **`s.mine = 1` 이 조용히 버려지는 것**도 같은 기계다. 대입할 때도 래퍼가 만들어지고,
  대입이 끝나면 **그 래퍼가 버려진다.** 다음 줄의 `s.mine` 은 **새 래퍼**를 만들어 조회하므로 `undefined` 다.
  ★★ **예외가 안 나게 하려면 아무것도 안 해도 되고, 나게 하려면 엄격 모드로 돌리면 된다** — 그러면 `TypeError` 다(35번 주제).
- ★★ **`new Boolean(false)` 가 참인 이유는 「객체는 전부 참」이기 때문**이다.
  `ToBoolean` 은 객체를 보면 안을 안 들여다보고 참을 준다 — **유일한 예외가 `document.all`**(4번)이다.
  ★ 그래서 래퍼 생성자는 **`if` 를 통째로 뒤집는다.** 쓰지 않는 것이 유일한 방어다.
- ★★ **`[4]` 를 가르는 기준**은 「래퍼가 있는가」다.
  `null`·`undefined` 는 래퍼가 없어 **점을 찍는 순간** `TypeError` 이고,
  `bigint`·`symbol` 은 래퍼가 있어 메서드가 돈다.
  ★ 원시 일곱 중 **다섯에만 래퍼가 있다.**
- ★ **`JSON.stringify(new Number(1))` 이 `1`** 인 것은 `JSON.stringify` 가 래퍼를 만나면 **원시 값으로 되돌려** 쓰기 때문이다.
  래퍼가 「거의」 원시 값처럼 굴어서 **버그가 늦게 드러난다**는 뜻이기도 하다.

### 4. 브라우저에서만 나오는 답 — **객체인데 `typeof` 가 `"undefined"` 다** ★★★

**출력**

```text
===== google-chrome --headless --disable-gpu --no-sandbox --dump-dom js01b-01d-browser.html 2>/dev/null | sed -n '/^<pre id="out">/,/<\/pre>/p' (exit=0) =====
<pre id="out">typeof document.all              : undefined
document.all === undefined       : false
document.all == undefined        : true
document.all == null             : true
Boolean(document.all)            : false
document.all ? 'T' : 'F'         : F
Object.prototype.toString.call   : [object HTMLAllCollection]
document.all.length              : 8
document.all[1].tagName          : HEAD
typeof document.body             : object</pre>
```

**왜 그런가**

- ★★★ **`typeof document.all` 은 `"undefined"` 인데 `document.all === undefined` 는 `false`** 다.
  엄격 비교는 **실제 값**을 보고, `typeof` 는 이 값에만 걸린 **예외 규칙**을 본다. 둘이 다른 답을 낸다.
- ★★★ **객체라는 증거는 둘**이다 — `Object.prototype.toString.call` 이 **`[object HTMLAllCollection]`** 을 주고,
  **`document.all[1].tagName` 으로 실제 요소를 꺼낼 수 있다**(`HEAD`).
- ★★ **`Boolean(document.all)` 이 `false`** 다. 그래서 falsy 목록은 여덟이 아니라
  **`undefined`·`null`·`false`·`0`·`-0`·`0n`·`NaN`·`""` 여덟 + `document.all`** 이다.
  ★ **원시 값이 아닌데 falsy 인 유일한 값**이다.
- ★★ **규정하는 쪽은 HTML 표준**이다. ECMA-262 는 그 예외를 받아 줄 **내부 표시**를 두고
  `typeof`·`ToBoolean`·느슨한 비교 세 곳에서 그것을 본다 — **두 명세가 맞물려 만든 예외**다.
- ★ **왜 만들었나** — 옛 IE 전용 코드가 `if (document.all)` 로 브라우저를 갈랐다.
  `document.all` 을 그냥 없애면 그 코드들이 **IE 아닌 브라우저에서 IE 경로로 들어가** 깨진다.
  그래서 「**있지만 조건문에서는 없는 것처럼 구는 값**」으로 만들었다. ★ **없앨 수 없다** — 없애려고 만든 물건이기 때문이다.
- ★ **흔들리는 칸은 `document.all.length` = `8`** 이다. 페이지의 요소 수라서 페이지를 고치면 바뀐다. 근거로 쓰지 않는다.

### 5. 두 판으로 돌리면 — **세 스크립트 전부 한 글자도 같다** ★

**출력**

```text
===== ./js01b-vdiff.sh 01 (exit=0) =====
script                             node v18.19.1 대 v20.19.6
---------------------------------- -------------------------
js01b-01a-typeof-grid.js           같다 (한 글자도)
js01b-01b-typeof-undeclared.js     같다 (한 글자도)
js01b-01c-boxing.js                같다 (한 글자도)
```

**왜 그런가**

- **세 스크립트가 두 판에서 똑같았다.** 값의 종류와 `typeof` 는 **판이 올라도 안 움직이는 층**이다.
- ★★ **「같았다」는 보장이 아니다.** 우연히 같을 수도 있고, 다음 판에서 갈릴 수도 있다.
  **보장은 명세에서만 온다** — 여기서는 `typeof` 결과표가 그 근거다.
  ★ 관찰이 해 주는 일은 「**이 문서의 출력을 어느 판에서 읽어도 된다**」까지다.
- ★ **이 배치 네 주제 전체에서 두 판이 갈린 자리는 하나**뿐이었다 — 04번의
  `String.prototype.isWellFormed`/`toWellFormed`(ES2024)가 **v18 에 없고 v20 에 있다.**
- ★ 이 스크립트가 **`*-browser.js` 를 건너뛰는** 것은 그 파일들이 `document` 를 쓰기 때문이다.
  node 로 돌리면 둘 다 같은 예외를 내고 **「같다」로 잘못 기록된다** — 그래서 아예 뺐다.

### 6. `typeof` 가 `"object"` 라고 답한 다음 — **창이 하나로는 모자란다** ★★★

- ★★★ **`typeof` 의 `"object"` 는 너무 넓다.** `null`·배열·`Date`·`Map`·정규식·`Math`·프로토타입 없는 객체가 **전부 같은 답**을 받는다.
  값이 무엇인지 알려면 **한 칸 더 들어가야** 한다.
- ★★ **둘째 창은 `Object.prototype.toString.call(x)`** 이고 `[object Null]`·`[object Array]`·`[object Date]` 처럼 **브랜드 태그**를 준다.
  1번의 출력에서 `null`·`Date`·`RegExp`·`Map`·`Math`·`JSON` 이 전부 갈렸다.
- ★★ **둘째 창도 속일 수 있다** — `Symbol.toStringTag` 를 객체에 박으면 그 문자열이 바뀐다.
  ★ 「무엇이 언제 깨지나」는 목록의 **34번 주제**가 정본이다.
- ★ **다섯을 가르는 법** — `null` 은 `x === null` · 배열은 `Array.isArray(x)` ·
  `Date`·`Map` 은 브랜드 태그나 `instanceof` · `Math` 는 값 비교(`x === Math`)다.
- ★★ **세 창으로 못 푸는 질문**이 있다 — 「**이 객체가 다른 realm(다른 창·다른 워커)에서 왔나**」.
  `instanceof` 는 realm 을 건너면 깨지고 브랜드 태그는 안 깨진다 — 세 창 중 어느 것도 **realm 을 직접 보여 주지 않는다**(34번 주제).

### 7. 세 가지 「없음」 — **서로 다른 세 상태다** ★★

| 상태 | 무엇으로 가리나 | 그냥 읽으면 |
|---|---|---|
| 선언이 아예 없다 | **`typeof x === "undefined"`** (이것만 된다) | `ReferenceError` |
| 선언은 있고 값이 `undefined` | `x === undefined` · `typeof x === "undefined"` | `undefined` |
| 값이 `null` | **`x === null`** (`typeof` 로는 못 한다) | `null` |

- ★★ **`typeof x === "undefined"` 는 앞의 둘을 참으로** 만든다. 셋째는 `"object"` 라 거짓이다.
- ★★ **`x == null` 은 뒤의 둘을 참으로** 만든다. 첫째는 **읽는 순간 터지므로** 아예 쓸 수 없다(02번 주제).
- ★ **오타가 만드는 것은 첫째 상태**다. `typeof` 로 방어하면 오타가 **영원히 조용히** 지나간다 — 그래서 무섭다.
- ★ **`let x;` 와 `let x = undefined;` 는 구분되지 않는다.** 둘 다 값이 `undefined` 이고 `in` 검사도 같다.
  ★ 객체 프로퍼티에서는 구분된다 — `"k" in o` 와 `o.k === undefined` 가 갈린다(13번 주제).

### 8. 보장인가 사정인가 — **이 주제는 보장 칸이 압도적으로 두껍다** ★★★

| 층 | 이 주제에서 여기 들어가는 것 |
|---|---|
| **명세 보장** | 값의 종류 여덟 · `typeof` 의 답 여덟 · **`typeof null === "object"`** · `[[Call]]` 있는 객체만 `"function"` · 선언 없는 이름에 `typeof` 가 안 터지는 것 · TDZ 는 터지는 것 · 임시 래퍼가 생기는 것 · 엄격 모드에서는 안 생기는 것 · `null`/`undefined` 에 래퍼가 없는 것 · 객체는 전부 truthy 인 것 |
| **엔진(V8) 구현** | 두 판의 V8 번호 · 세 스크립트가 두 판에서 같았다는 것 · Chrome 151 과 Node 20 이 같은 답을 낸 것 |
| **이 판의 관찰** | 예외 **문구** · `document.all.length` = `8` · UA 문자열 · `[object HTMLAllCollection]` 이라는 **이름** |
| **호스트(HTML) 보장** | `document.all` 의 세 가지 예외 — ECMA-262 가 아니라 **HTML 표준**이 정한다 |

- ★★★ **`typeof null === "object"` 는 명세 보장 칸**이다. 판정 근거는 **`typeof` 결과표에 그 줄이 있다**는 것이다.
  ★★ 「초기 구현의 버그에서 출발했다」는 **역사**이고, 「지금 그것이 보장이다」는 **현재의 규칙**이다 — 둘을 섞으면 안 된다.
  ★★★ **이 갈래의 축이 바로 이것**이다. JS 에서는 「버그처럼 보이는 것」이 대개 **명세에 박혀 있다.**
- ★★ **예외의 종류는 명세, 문구는 아니다.** `ReferenceError` 가 난다는 것은 보장이고
  `is not defined` 라는 글자는 V8 의 것이다 — 판이 오르면 바뀔 수 있다.
- ★★ **「두 판에서 같았다」는 엔진 구현 칸의 근거**가 된다. **명세 보장 칸의 근거는 못 된다.**
- ★ **가장 얇은 칸**은 「엔진 구현」이다. 이 주제에는 엔진이 고를 여지가 거의 없다 — 전부 명세가 정해 놓았다.

### 9. 경계 — 어디까지가 이 주제인가 ★★

| 주제 | 정본 |
|---|---|
| TDZ 와 호이스팅 | 목록의 **05번 주제** |
| 엄격 모드가 바꾸는 규칙 전부 | 목록의 **35번 주제** |
| `Array.isArray`·`instanceof`·브랜드 태그가 **어디서 깨지나** | 목록의 **34번 주제** |
| `Symbol.toStringTag` 로 태그를 바꾸는 것 | 목록의 **22번 주제** |
| 프로퍼티 열거 순서·`"k" in o` | 목록의 **13번 주제** |

- ★★★ **TypeScript 갈래와의 경계** — 그쪽([`ts/syntax/01-what-ts-adds-and-erases`](../../../ts/syntax/01-what-ts-adds-and-erases/2-summary.md))은
  「**타입 표기는 런타임에 안 남는다**」가 정본이고, 여기는 「**런타임에 남아 있는 것이 무엇인가**」가 정본이다.
- ★★ **`typeof` 는 남는 쪽**이다 — 컴파일 뒤에도 그대로 실행되는 **런타임 연산자**다.
  TS 에도 같은 철자의 **타입 연산자**가 따로 있지만 그것은 그쪽 주제다.
- ★ **이 주제가 끝까지 책임지는 것 셋** — ① 값의 종류가 무엇무엇인가 ② `typeof` 의 답이 그것과 어디서 어긋나는가
  ③ 원시 값에 점을 찍으면 무슨 일이 나는가.
- ★ **메모리 표현은 이 주제가 아니다.** 표준에 관찰할 방법이 없고, 관찰하더라도 **명세 보장이 아니다** —
  그것을 적으면 「구현 사정을 언어 사실로」 적는 사고가 된다.

### 10. 이 갈래의 창 ★★

- ★★★ **이 주제에서 쓴 창은 다섯**이다 —
  ① **`typeof`** ② **`Object.prototype.toString.call`**(브랜드 태그) ③ **실행 출력(값)**
  ④ **예외의 타입·메시지** ⑤ **두 판 대조 + 브라우저**.
- ★★ **브라우저에서만 열리는 창**은 ⑤ 의 브라우저 쪽이다 — `document.all` 은 Node 에 없다.
  ★ 그래서 **「Node 에서 안 나온다」를 「없다」로 읽으면 틀린다.**
- ★★ **스택트레이스 대신 타입·메시지를 찍은 이유**는 Node 의 트레이스에 **절대 경로**가 박히기 때문이다.
  「흔들리는 칸」을 선언하는 것보다 **안 흔들리게 만드는 쪽**이 낫다.
- ★ **표준 출력과 표준 오류를 안 섞은 이유** — stdout 은 파이프로 받으면 블록 버퍼가 되어
  **터미널에서 본 순서와 파일로 받은 순서가 달라진다.** 이 주제는 아예 stderr 를 안 쓴다.
- ★★ **안 돌려 본 것** — `Proxy` 에 `typeof` 를 던지는 것(45번 주제) · `Symbol.toStringTag` 로 태그를 바꿔 보는 것(22·34번) ·
  **realm 을 건너온 객체**(`iframe`·`vm` 모듈) · `void 0` 과 `undefined` 의 비교 · **Node 18 보다 낮은 판**.

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js01b-01a-typeof-grid.js` | 스물두 값의 `typeof` 와 브랜드 태그 · 답이 여덟 가지인 것 | node20 1벌 + node18 대조 1벌 |
| `js01b-01b-typeof-undeclared.js` | `typeof` 의 특권과 **TDZ 라는 구멍** · `in globalThis` 와의 차이 | node20 1벌 + node18 대조 1벌 |
| `js01b-01c-boxing.js` | 임시 래퍼가 **관찰된다**는 것 · 엄격 모드에서 안 생기는 것 · 래퍼 객체의 truthy | node20 1벌 + node18 대조 1벌 |
| `js01b-01d-browser.js` | **`document.all` 의 세 예외** · 객체라는 증거 둘 | Chrome 151 1벌 |
| `js01b-vdiff.sh` | 세 스크립트가 **두 판에서 한 글자도 같다**는 것 | 1벌 |
| `js01b-versions.sh` | 이 문서의 모든 출력이 **어느 판에서 나왔나** | 1벌 |

**구현 의존 항목** — 다음은 **이 환경(node 20.19.6 / 18.19.1 · Chrome 151 · x86-64 Linux)에서만** 그렇다.

- ★★ **예외 메시지 문구 전부** — `neverDeclared is not defined` · `Cannot access 'tdzLet' before initialization` ·
  `Cannot read properties of null (reading 'toString')`. **종류는 명세, 문구는 V8 의 것**이다.
- ★★ **`document.all.length` 가 `8` 인 것** — 호스트 페이지의 요소 수다.
- ★ **UA 문자열 `Chrome/151.0.0.0`** — 브라우저가 일부러 축약해 내보내는 값이라 **실제 판(`151.0.7922.173`)과 다르다.**
- ★ **`[object HTMLAllCollection]` 이라는 태그 이름** — HTML 표준이 정하지만 이름 자체는 바뀔 수 있는 축이다.

**값의 종류 여덟 · `typeof` 의 답 여덟과 그 대응 · `typeof null === "object"` · 함수만 `"function"` · 선언 없는 이름에 `typeof` 가 안 터지는 것 · TDZ 는 터지는 것 · 임시 래퍼 · 엄격 모드에서 래퍼가 안 생기는 것 · 객체는 전부 truthy 인 것은 구현 의존이 아니다.**
어느 엔진에서도 같아야 한다.

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — `Proxy` 에 대한 `typeof` · `Symbol.toStringTag` 를 바꿔 본 것 ·
  **realm 을 건너온 객체**(`iframe`·`vm`) · Node 18 보다 낮은 판 · 다른 엔진(SpiderMonkey·JavaScriptCore) ·
  `void 0` 과 `undefined` 의 비교 · **엄격 모드 파일 전체**에서 이 세 스크립트를 다시 돌리는 것.
- ★ **못 잰 것** — **「래퍼 객체가 실제로 할당되는가」.**
  느슨한 모드에서 `typeof this` 가 `"object"` 인 것은 **관찰 가능한 동작**이지만,
  엔진이 그 객체를 정말 힙에 만드는지 최적화로 없애는지는 **표준 API 로 잴 방법이 없다.**
  ★★ 그래서 본문은 **「관찰되는 동작」까지만** 적고 **「할당이 일어난다」는 적지 않았다** — 뒤엣것은 구현 사정이다.

**판이 올랐을 때 다시 돌려야 하는 것**

- ★★ **예외 메시지 문구** — 세 블록에 들어 있다.
- ★★ **`typeof` 의 답이 아홉 가지가 되었는지** — 새 원시 타입이 들어올 때만 늘어난다.
- ★ **`document.all` 의 세 예외가 그대로인지** — HTML 표준이 바꾸면 바뀐다(바꿀 이유가 없어 안 바뀔 것이다).
- ★ **브라우저 UA 의 축약 정도** — 근거로 안 쓰므로 영향은 없다.
- **값의 종류와 `typeof` 의 대응표는 다시 돌릴 필요가 없다** — `bigint` 가 들어온 ES2020 이후 바뀐 적이 없다.
