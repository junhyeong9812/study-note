# js/syntax/48 — 깊은 복사 수단 비교: 「잃음 `24 / 68` · 공유 `20 / 68` — 스프레드·`assign` 은 얕고, `structuredClone` 은 호스트가 준 깊은 복사지만 함수·심볼 키·프로토타입·getter 를 못 옮긴다」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 출력은 **node v20.19.6 · v18.19.1 · Google Chrome 151 · Python 3.12.3** · x86-64 Linux 에서 실제로 돌려 얻은 것이고, 블록은 **전부 캡처 파일에서 조립**했다.
> ★★★ **`structuredClone` 은 ECMA-262 가 아니라 호스트 API 다** — 이 파일의 `clone` 열과 2\~4번의 `structuredClone` 줄은 **세 호스트의 관찰**이고, 이 문서는 HTML 의 해당 절을 읽지 않았다(7번).
>
> **이 파일이 인용하는 출력을 낸 소스** — 전문은 [1-question.md](1-question.md) 의 같은 번호 문항에 있다.
> `js48b-48a-copy-grid.js` + `.sh`(1번 · 6번 · 7번 · 9번) · `js48b-48b-clone-details.js`(2번 · 3번 · 4번 · 8번) · `js48b-48d-python.py`(5번).

## 정답

### 1. `JSON` 열 — 16칸을 잃고 `kept` 는 **`nested plain object`** 하나 · `spread` 와 `assign` 은 **한 칸도 다르지 않다** · 둘 다 `shared` 가 아닌 행은 원시 값·`undefined` 속성·심볼 키(`kept`)와 클래스 인스턴스·getter(`->`) · `clone` 열의 넷 — **함수 `throws DOMException/DataCloneError`** · **심볼 키 `-> key gone`** · **클래스 인스턴스 `-> plain {"x":1}`** · **getter `-> data property 1`** · **`20 / 68`** · **`24 / 68`** · 비교 두 줄 **`yes`** ★★★

**출력**

```text
===== ./js48b-48a-copy-grid.sh (exit=0) =====
--- node20
                     JSON                                  spread                 assign                 clone
Date                 -> string "1970-01-01T00:00:00.000Z"  shared                 shared                 kept
Map                  -> plain {}                           shared                 shared                 kept
Set                  -> plain {}                           shared                 shared                 kept
RegExp               -> plain {}                           shared                 shared                 kept
undefined property   -> key gone                           kept                   kept                   kept
NaN                  -> null                               kept                   kept                   kept
-0                   -> number 0                           kept                   kept                   kept
BigInt               throws TypeError/TypeError            kept                   kept                   kept
function             -> key gone                           shared                 shared                 throws DOMException/DataCloneError
symbol key           -> key gone                           kept                   kept                   -> key gone
cycle                throws TypeError/TypeError            shared (c.me === src)  shared (c.me === src)  kept
class instance       -> plain {"x":1}                      -> plain {"x":1}       -> plain {"x":1}       -> plain {"x":1}
getter               -> data property 1                    -> data property 1     -> data property 1     -> data property 1
same object twice    -> two objects                        shared                 shared                 kept
Error with cause     -> plain {}                           shared                 shared                 kept
Uint8Array           -> plain {"0":1,"1":2}                shared                 shared                 kept
nested plain object  kept                                  shared                 shared                 kept

per column, kept:          JSON 1 · spread 5 · assign 5 · clone 13
per column, shared:        JSON 0 · spread 10 · assign 10 · clone 0
per column, not preserved: JSON 16 · spread 2 · assign 2 · clone 4
cells shared with the source (===): 20 / 68
cells not preserved (-> or throws): 24 / 68

node18 prints the same as node20: yes
Chrome 151 prints the same as node20: yes
```

**왜 그런가**

- ★★★ **JSON 은 글자를 거친다** — 글자로 표현되지 않는 타입은 모양이 바뀌거나(`Date` → 문자열 · `Map` 등 → `{}`) 빠지거나(`undefined`·함수·심볼 키) 던진다(`BigInt`·순환). 31번이 13행에서 본 그대로다.
- ★★★ **스프레드와 `assign` 은 속성 값을 옮길 뿐 다시 복사하지 않는다** — 그래서 객체가 든 칸은 전부 `shared`, 원시 값 칸은 `kept`. 두 열이 같은 것은 이 격자의 행들(own 열거 가능 데이터 속성 · getter 하나)에서 두 연산의 결과가 같기 때문이다(갈리는 자리 — 대상에 setter 가 있을 때 — 는 27번).
- ★★ **`clone` 열** — 그래프를 새로 만들어 공유 0 · 순환과 「같은 객체 두 번」까지 `kept`. 잃은 넷은 **거절(함수)** 과 **옮기지 않는 것(심볼 키 · 프로토타입 · 접근자)** 두 종류다.

### 2. 다섯 줄 모두 **`DOMException` · `DataCloneError` · `code 25`** · 문구는 `… could not be cloned.` · 여섯째 줄 **`true`** · Chrome 151 은 **문구 앞에 `Failed to execute 'structuredClone' on 'Window': `** 가 붙는다 ★★

**출력**

```text
===== node20 js48b-48b-clone-details.js (exit=0) =====
[1] values it refuses
  a function                          throws DOMException (name DataCloneError, code 25) 「function f() {} could not be cloned.」
  an arrow function                   throws DOMException (name DataCloneError, code 25) 「() => 1 could not be cloned.」
  a symbol value                      throws DOMException (name DataCloneError, code 25) 「Symbol(s) could not be cloned.」
  a WeakMap                           throws DOMException (name DataCloneError, code 25) 「#<WeakMap> could not be cloned.」
  a Promise                           throws DOMException (name DataCloneError, code 25) 「#<Promise> could not be cloned.」
  DOMException instanceof Error       true
[2] Error objects -- what the copy has
  new TypeError('m', { cause })
    constructor TypeError · name TypeError · message m · cause {"code":7} · cause is a new object true · extra undefined · stack is a string true · stack equal true
  new RangeError('m')
    constructor RangeError · name RangeError · message m · cause undefined · cause is a new object false · extra undefined · stack is a string true · stack equal true
  new MyError('m')  (subclass)
    constructor Error · name Error · message m · cause undefined · cause is a new object false · extra undefined · stack is a string true · stack equal true
[3] property-level things
  getter read during the copy         reads 1
  non-enumerable key copied           false
  frozen source -> copy frozen        false
  own property on a Date copied       undefined
  own property on an Array copied     x
[4] the transfer option
  source byteLength after transfer    0
  copy byteLength                     8
  source byteLength without transfer  8
```

Chrome 151.

```text
===== ./js48b-browser.sh js48b-48b-clone-details.js (exit=0) =====
[1] values it refuses
  a function                          throws DOMException (name DataCloneError, code 25) 「Failed to execute 'structuredClone' on 'Window': function f() {} could not be cloned.」
  an arrow function                   throws DOMException (name DataCloneError, code 25) 「Failed to execute 'structuredClone' on 'Window': () => 1 could not be cloned.」
  a symbol value                      throws DOMException (name DataCloneError, code 25) 「Failed to execute 'structuredClone' on 'Window': Symbol(s) could not be cloned.」
  a WeakMap                           throws DOMException (name DataCloneError, code 25) 「Failed to execute 'structuredClone' on 'Window': #<WeakMap> could not be cloned.」
  a Promise                           throws DOMException (name DataCloneError, code 25) 「Failed to execute 'structuredClone' on 'Window': #<Promise> could not be cloned.」
  DOMException instanceof Error       true
[2] Error objects -- what the copy has
  new TypeError('m', { cause })
    constructor TypeError · name TypeError · message m · cause {"code":7} · cause is a new object true · extra undefined · stack is a string true · stack equal true
  new RangeError('m')
    constructor RangeError · name RangeError · message m · cause undefined · cause is a new object false · extra undefined · stack is a string true · stack equal true
  new MyError('m')  (subclass)
    constructor Error · name Error · message m · cause undefined · cause is a new object false · extra undefined · stack is a string true · stack equal true
[3] property-level things
  getter read during the copy         reads 1
  non-enumerable key copied           false
  frozen source -> copy frozen        false
  own property on a Date copied       undefined
  own property on an Array copied     x
[4] the transfer option
  source byteLength after transfer    0
  copy byteLength                     8
  source byteLength without transfer  8
```

**왜 그런가**

- ★★ `DataCloneError` 는 **호스트 API 의 예외**(`DOMException`)다 — `TypeError` 계열이 아니다. `instanceof Error` 가 `true` 인 것은 이 판들의 `DOMException` 이 `Error` 를 상속하는 관찰이다.
- ★★ **문구는 호스트가 붙인다** — 같은 V8 인데 Chrome 은 「어느 인터페이스의 어느 메서드인가」를 앞에 붙였다. 판별은 `e.name` 으로.
- ★ node 18 은 이 블록이 node 20 과 **한 글자도 같았다**(캡처가 node18 블록을 따로 안 만들었다).

### 3. `TypeError` · `TypeError` · `cause {"code":7}`(**새 객체**) · `RangeError` · `RangeError` · **`MyError` → `constructor Error · name Error`** · `extra` 는 **셋 다 `undefined`** · `stack` 은 셋 다 **문자열이고 원본과 같다** ★★★

**출력** — 2번 블록의 `[2]` 여섯 줄.

**왜 그런가**

- ★★★ **표준 생성자 이름(`TypeError`·`RangeError`)이면 그 생성자로, 아니면 `Error` 로** 돌아왔다 — 하위 클래스는 **클래스 인스턴스 행(1번)과 같은 이유로** 프로토타입을 잃고, 생성자에서 붙인 own `name`(`MyError`)과 `extra` 도 안 왔다.
- ★★ `cause` 는 **새 객체로** 따라왔다 — 깊은 복사답게 원인 객체도 복사됐다. `stack` 은 원본과 같은 글자였다.
- ★★★ **이 줄들은 세 판의 관찰이다** — 이 문서는 HTML 절을 읽지 않았으므로 `cause`·`stack` 을 옮기는 것을 보장으로 적지 않는다.

### 4. `reads 1` · `false` · `false` · **`undefined`** · **`x`** · `0` · `8` · `8` ★★

**출력** — 2번 블록의 `[3]`·`[4]` 여덟 줄.

**왜 그런가**

- ★★ **getter 는 복사하는 동안 한 번 읽혀** 그 값(`1`)이 데이터 속성이 된다 — 1번 격자의 `-> data property 1`.
- ★★ **비열거 속성은 안 오고, 얼린 상태도 안 온다** — 복사본은 새 평범한 객체다.
- ★★ **여분의 속성은 객체 종류에 따라 갈렸다** — `Date` 에 붙인 `note` 는 사라지고(`undefined`) 배열에 붙인 `extra` 는 왔다(`x`). `Date` 는 **날짜 값 하나**로, 배열은 **속성의 모음**으로 복사된 것으로 읽힌다(관찰에서 끌어낸 해석).
- ★★ `transfer` 에 넣은 버퍼는 **옮겨져** 원본이 `0` 이 된다 — 안 넣으면 원본은 `8` 그대로.

### 5. `True` · `False` · `2` · `MyError` · `('m',)` · `42` · **`None`** · `True` — `clone` 열과 반대로 나온 것은 **클래스 인스턴스 행**(파이썬은 클래스를 지킨다) ★★

**출력**

```text
===== python3 js48b-48d-python.py (exit=0) =====
[1] class instance: type(copy) is Point -> True · copy is p -> False
[2] property on the class: copy.doubled -> 2
[3] exception: type -> MyError · args -> ('m',) · extra -> 42 · __cause__ -> None
[4] function: deepcopy(f) is f -> True
```

**왜 그런가**

- ★★★ **클래스·접근자는 파이썬이 지킨다** — `deepcopy` 가 복사본을 **같은 클래스로** 만들고, `property` 는 클래스에 붙어 있어 그대로 동작한다(`doubled -> 2`).
- ★★★ **예외는 서로 반대로 잃었다** — 파이썬은 하위 클래스·`extra` 를 지키고 **`__cause__` 를 잃었다**(`None`), JS 는 `cause` 를 지키고 하위 클래스·`extra` 를 잃었다(3번).
- ★★ **함수** — 파이썬은 같은 객체를 돌려주고(`True`), JS 는 던졌다(2번).

### 6. **`shared` 10칸이 보존 쪽으로 넘어가 스프레드·`assign` 이 `clone` 을 앞지른다** — 그러나 `shared` 는 원본과 **같은 객체**라, 복사본에서 `c.v.setTime(1)` 한 줄이면 **원본의 날짜도 바뀐다** ★★★

- ★★★ 「값이 같다」와 「따로 논다」는 다른 질문이다. 격자가 `shared` 를 `kept` 와 **따로 센 이유**가 이것이다 — 합치면 얕은 복사가 깊은 복사를 이긴다.
- ★★ 그 쓰기 실험은 27번 동작 (2) `[3]` 이 이미 했다 — 복사본의 `inner.deep = 99` 가 **원본의 `inner.deep` 도 `99`** 로 만들었다.

### 7. **ECMA-262** — `JSON`·`spread`·`assign` 세 열 전부(얕음 · getter 를 값으로 · 프로토타입 안 옮김) · **호스트(HTML)** — `clone` 열 전체 · `DataCloneError`/`DOMException` · `transfer` · **이 판의 구현으로만** — 예외 문구 · `Error` 의 `cause`·`stack`·하위 클래스 칸 · **세 판이 같았다는 것은 이 구분을 거의 돕지 못한다**(셋 다 V8) ★★★

- ★★★ `structuredClone` 자체가 ECMA-262 에 없다 — 이 한 사실이 `clone` 열을 통째로 호스트 층에 둔다.
- ★★ 「node 와 Chrome 이 같다」는 **같은 엔진의 두 호스트**라는 뜻이다. HTML 이 정한 것과 V8 이 고른 것을 가르려면 **다른 엔진**이 필요하다(요약 「더 들어가면」).

### 8. JSON 은 함수 키를 **조용히 뺀다**(`-> key gone`) · `structuredClone` 은 **던진다**(`DataCloneError`) · 심볼 **키**는 `clone` 이 조용히 빼고(1번), 심볼 **값**은 던진다(2번) ★★

- ★★ 조용한 실패는 **나중에** 다른 자리에서 터진다(없는 메서드를 부를 때). 시끄러운 실패는 **복사한 그 줄**에서 멈춘다 — 원인을 찾기 쉬운 쪽은 뒤쪽이다.
- ★ 같은 종류의 값이라도 **자리**(키냐 값이냐)가 실패의 모양을 바꾼다 — 격자가 둘을 다른 행으로 둔 이유다.

### 9. **클래스 인스턴스**(`-> plain {"x":1}`)와 **getter**(`-> data property 1`) — 둘 다 **값이 아니라 객체의 「모양」**(프로토타입 · 접근자 서술자)이다 · 클래스 인스턴스는 **클래스 자신의 복사 메서드**에 기댄다 ★★

- ★★ 네 수단은 모두 **값을 읽어 새 평범한 객체에 넣는다** — 읽는 순간 getter 는 값이 되고, 새 객체의 프로토타입은 `Object.prototype` 이다. 모양을 옮기는 수단은 이 넷에 없다.
- ★ 복사 메서드를 권하는 것은 **설계 권고**다 — 이 문서는 그 대안들을 돌려 비교하지 않았다.

### 10. **판 격자와 신호 대 잡음** — 여러 판(node 18 · 20 · Chrome) × 여러 크기 · 모양의 입력 × 반복 · 흔들림 폭을 세우고, 「움직인 칸 / 안 움직인 칸」을 선언한 뒤에야 적을 수 있다(규칙 24) ★

- ★ 이 문서는 시간도 바이트도 **안 쟀다** — 31번 · 27번과 같은 선이다. 「무엇을 잃나」라는 이 주제의 질문에는 그 창이 필요 없다.

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js48b-48a-copy-grid.js` + `.sh` | ★★★ 68칸 · 「`20 / 68`」 · 「`24 / 68`」 · 열마다 세 줄 | node20(전문) · node18 · Chrome 151 — 세 판 비교 줄 `yes` · `yes` |
| `js48b-48b-clone-details.js` | ★★ 거절 다섯 · `Error` 셋 · 속성 수준 다섯 · `transfer` 셋 | node20 · node18(같음 — 블록 없음) · Chrome 151(`[1]` 문구만 다름) |
| `js48b-48d-python.py` | ★★ CPython `deepcopy` 의 클래스 · 예외 · 함수 | python3 3.12.3 |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것** — ★★★ **`clone` 열 전체**와 2\~4번의 `structuredClone` 줄(호스트 API — 특히 `Error` 의 `cause`·`stack`·하위 클래스 칸과 예외 문구). 왼쪽 세 열(ECMA-262)은 판이 올라도 같아야 한다.
