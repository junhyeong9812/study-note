# web-api/15 — 리스너 등록과 해제: `addEventListener` 옵션 객체·`removeEventListener` 의 동일성 조건·`handleEvent` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 `--dump-dom` 으로 실제로 받은 것**이다. 명령은 블록마다 배너로 실려 있다.\
> 규칙은 [WHATWG DOM Standard — Events](https://dom.spec.whatwg.org/#events) 의 「add an event listener」·「remove an event listener」·「inner invoke」 절로 접지했다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**\
> ★ **재지 않은 것** — `passive` 의 성능 이득과 리스너가 붙드는 메모리(A8·A11).

**★ 이 주제에는 흔들리는 칸이 거의 없다** — 세는 것이 전부 호출 횟수이고 시간을 안 재기 때문이다.

| 안 흔들리는 칸 | 흔들리는 칸 · 못 잰 칸 |
|---|---|
| 모든 호출 횟수 · 동일성 격자 14칸 · `defaultPrevented` 값 · 예외 이름과 문구 | **콘솔 경고의 줄 수** — Chrome 이 같은 자리를 합친다(A8) |
| 디스패치 도중 목록 변경의 순서 | **못 잰 것** — `passive` 의 성능 이득 |
| 두 판을 돌려 **한 글자도 같았다** | **못 잰 것** — 리스너가 붙드는 메모리 |
| — | **부적용** — `--dump-dom` 트리(리스너는 자국을 안 남긴다) |
| — | Chrome 판 번호 |

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 명부가 보는 것은 글자가 아니라 객체다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-15-ident.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,6p'
익명 함수는 왜 못 지우나
  똑같이 생긴 익명 함수로 지운 뒤 호출 횟수 = 1
  두 함수가 같은가: true (글자는 같다) · false (참조는 다르다)
  같은 참조로 지운 뒤 호출 횟수 = 0
  ★ 「같은 코드」가 아니라 「같은 객체」라야 한다. bind() 도 새 함수를 만든다:
    원본.bind(null) === 원본.bind(null) 는 false
(exit 0)
```

**왜 그런가**

- **익명 함수로 달고 익명 함수로 지우면 안 지워진다** — `n` 이 **1** 이다. 예외도 경고도 없다.
- **`toString()` 은 `true`, `===` 는 `false`** 다. **글자는 같고 객체가 다르다.** 명세의 「remove an event listener」는 **콜백이 같은 객체인지**를 본다.
- **같은 참조로 지우면 `m` 이 0** 이다 — 변수에 담아 두는 것이 유일한 길이다.
- ★ **`bind()` 는 부를 때마다 새 함수를 만든다** — `원본.bind(null) === 원본.bind(null)` 이 **`false`** 다. 그래서 `addEventListener('t', f.bind(this))` 로 단 리스너는 **원리상 지울 수 없다.** 만든 함수를 변수에 담아 두거나 `signal` 을 쓴다(A6).

### 2. 둘째 등록은 조용히 무시되고, `capture` 가 다르면 다른 줄이다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-15-ident.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '8,11p'
같은 리스너를 두 번 등록하면
  두 번 등록하고 한 번 던지면 호출 횟수 = 1  <- 둘째 등록은 조용히 무시된다
  한 번만 지우고 다시 던지면    호출 횟수 = 0  <- 둘 다 사라진다(애초에 하나였다)
  capture 만 다르게 두 번 등록하면 호출 횟수 = 2  <- 이번엔 둘 다 산다
(exit 0)
```

**왜 그런가**

- **두 번 등록하고 한 번 던지면 `k` 가 1** 이다. 명세가 「같은 열쇠가 이미 있으면 **아무것도 하지 마라**」로 정한다 — **예외도 경고도 없다.**
- **그래서 한 번만 지워도 둘 다 사라진다**(0회). 애초에 **한 줄**이었기 때문이다.
- ★ **`capture` 만 다르게 두 번 달면 둘 다 산다** — 2회다. 열쇠의 **셋째 칸이 다르면 다른 줄**이다.
- ★ **「두 번 달아도 괜찮다」가 성립하는 것은 참조가 같을 때뿐이다.** 매번 새 화살표 함수를 넘기면 **부를 때마다 한 줄씩 쌓이고**, 그 줄들은 (1)에 따라 **하나도 지울 수 없다.**

### 3. 동일성 키는 셋뿐이다 — 안 지워진 칸 4 / 14 가 전부 `capture` 다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-15-ident.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '13,33p'
동일성 조건 — 등록 옵션과 해제 옵션을 격자로 던진다
등록 옵션                                   해제 옵션                                   결과
undefined                                   undefined                                   지워졌다
{"capture":true}                            {"capture":true}                            지워졌다
{"capture":true}                            undefined                                   ★ 안 지워졌다
undefined                                   {"capture":true}                            ★ 안 지워졌다
true                                        {"capture":true}                            지워졌다
{"capture":false}                           true                                        ★ 안 지워졌다
false                                       undefined                                   지워졌다
{"once":true}                               undefined                                   지워졌다
{"once":true}                               {"once":false}                              지워졌다
{"passive":true}                            {"passive":false}                           지워졌다
{"passive":true}                            undefined                                   지워졌다
{"capture":true,"once":true,"passive":true} {"capture":true}                            지워졌다
{"capture":false,"once":true}               {"capture":true}                            ★ 안 지워졌다
{"signal":{}}                               undefined                                   지워졌다

안 지워진 칸 = 4 / 14
★ 키에 들어가는 것은 셋뿐이다 — 이벤트 종류 · 콜백(같은 객체) · capture.
★ once·passive·signal 은 키가 아니다. 넣든 빼든 반대로 넣든 지워진다.
★ 세 번째 인자가 불리언이면 그것이 곧 capture 다 — true 와 {capture:true} 는 같은 키다.
(exit 0)
```

**왜 그런가**

- **안 지워진 칸이 14 중 4** 이고 **넷의 공통점은 하나** — 등록과 해제의 `capture` 가 다르다.
  - `{capture:true}` 로 달고 **안 적고** 지움 · **안 적고** 달고 `{capture:true}` 로 지움 · `{capture:false}` 로 달고 `true` 로 지움 · `{capture:false, once:true}` 로 달고 `{capture:true}` 로 지움.
- **`capture` 를 안 적으면 `false` 로 읽힌다** — 그래서 「옵션 없음」과 「`{capture:false}`」는 같은 키다(격자의 첫 줄과 일곱째 줄).
- ★ **세 번째 인자가 불리언이면 그것이 곧 `capture`** 다 — `true` 로 달고 `{capture:true}` 로 지우면 **지워진다.**
- ★ **`once`·`passive`·`signal` 은 키가 아니다.** 넣든 빼든 **반대로** 넣든 지워졌다. 명세의 「remove an event listener」가 **타입·콜백·`capture` 셋만** 비교하기 때문이다.
- **`{capture:true, once:true, passive:true}` 로 달고 `{capture:true}` 만으로 지워졌다** — 나머지 둘을 안 보는 것이 이 줄에서 확인된다.

### 4. `handleEvent` 는 부를 때마다 찾는다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-15-obj.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,3p'
함수가 아니라 객체를 리스너로 넘기면
  handleEvent 가 불렸다 · this.이름 = 나는 객체다 · e.type = 가 · this === 등록한 객체 ? true
  removeEventListener(같은 객체) 뒤 다시 던졌고, 위 줄은 한 번만 찍혔다 (센횟수=1)
(exit 0)
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-15-obj.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '5,10p'
handleEvent 는 언제 찾나
  handleEvent 가 없는 객체를 등록하고 던지면 = 예외 없음
  나중에 붙인 handleEvent 가 불렸다
  ★ 등록할 때가 아니라 부를 때마다 찾는다. 등록 시점에는 검사도 안 한다.
  숫자를 리스너로 등록하면 = TypeError 「Failed to execute 'addEventListener' on 'EventTarget': parameter 2 is not of type 'Object'.」
  null 을 등록하면        = 예외 없음 (조용히 아무 일도 안 한다)
(exit 0)
```

**왜 그런가**

- **`handleEvent` 를 가진 객체는 그대로 리스너가 된다.** `this` 가 **등록한 객체**이고(`true`), 지울 때도 **같은 객체**를 넘긴다(센횟수 1).
- ★ **`handleEvent` 가 없는 객체를 등록해도 예외가 없다** — 던져도 조용하다. **나중에 붙이면 그때부터 불린다.**
- **등록 시점에는 검사도 안 한다** — 명세의 「inner invoke」가 **부를 때** `handleEvent` 를 읽기 때문이다.
- ★ **그 사실이 만드는 사고** — 메서드 이름 오타(`handleevent`)가 **예외도 경고도 없이** 「영영 안 불림」이 된다. 이 주제의 조용한 실패 넷 가운데 **가장 찾기 어려운 것**이다.
- **숫자를 넘기면 `TypeError` 로 막힌다**(`parameter 2 is not of type 'Object'.`) — 객체도 함수도 아니어서다.
- **`null` 은 조용히 무시**된다 — IDL 이 `EventListener?` 로 **널 허용**이기 때문이다.

### 5. 보통 함수의 `this` 는 `currentTarget` 이다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-15-obj.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '12,19p'
this 가 무엇인가
  보통 함수   this === e.currentTarget ? true · this = #겉
  화살표 함수 this === window ? true · e.currentTarget = #겉
  bind 한 함수 this.표 = 내가 묶은 것
  handleEvent  this.표 = 객체 자신
  ★ 보통 함수의 this 는 currentTarget 이다 — target 이 아니다.
  ★ 화살표 함수는 바깥 this 를 그대로 쓰므로 currentTarget 을 잃는다. e.currentTarget 으로 받는다.
  ★ 객체를 넘기면 this 가 그 객체다 — 상태를 들고 다니는 리스너가 된다.
(exit 0)
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-15-obj.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '21,22p'
한 객체를 두 요소에 등록하면
  한 번 던지고 모아 둔 것 = ["#속","#겉"]  <- 같은 객체가 두 자리에서 각각 불린다
(exit 0)
```

**왜 그런가**

- **보통 함수** — `this === e.currentTarget` 이 **`true`** 이고 값은 `#겉` 이다. ★ **`target` 이 아니다.** 위임(목록의 **18번 주제**)에서 이 구분이 결정적이다.
- **화살표 함수** — `this` 가 **바깥의 `this`**(여기서는 `window`)다. `currentTarget` 을 잃으므로 **`e.currentTarget` 으로 받아야** 한다.
- **`bind` 한 함수** — 묶은 객체가 `this` 다. 대신 (1)대로 **지우기가 어려워진다.**
- **객체 리스너** — `this` 가 **그 객체**다. `bind` 없이 상태를 들고 다니는 길이고 **지우기도 쉽다.**
- ★ **한 객체를 두 요소에 등록하면** 두 자리에서 각각 불리고(`["#속","#겉"]`) **`this` 는 두 번 다 같은 객체**다. **갈리는 것은 `currentTarget` 뿐**이다 — 객체 리스너에서 「어디서 불렸나」는 `this` 가 아니라 `e.currentTarget` 으로 묻는다.
- 규칙 자체의 정본은 JS 갈래 목록([`js/syntax/README.md`](../../languages/js/syntax/README.md))의 **07번** 이고, 리스너 자리는 그중 **암시적 바인딩**(메서드처럼 불린다)이 걸리는 자리다.

### 6. 떼는 세 길 — `once` 는 부르기 전에 빠지고 `signal` 은 열쇠를 안 본다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-15-life.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,4p'
once — 한 번 불리고 스스로 사라진다
  세 번 던졌는데 호출 = 1회
  once 안에서 자기를 다시 등록하고 두 번 던지면 = ["불렸다","불렸다"]
  once 리스너가 예외를 던져도 = 1회 (사라지는 것은 그대로다 · 예외는 콘솔로 샌다)
(exit 0)
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-15-life.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '6,10p'
signal — 여러 개를 한 번에 뗀다
  abort 전에 세 자리에 던지면 호출 = 3회
  abort() 한 뒤 같은 것을 던지면 = 0회
  이미 abort 된 signal 로 등록하면 = 0회 (등록 자체가 안 된다)
  ★ removeEventListener 는 등록 옵션을 다시 적어야 하는데 signal 은 안 그렇다 — 요즘 관용구다.
(exit 0)
```

**왜 그런가**

- **세 번 던져도 1회** — `once` 가 붙은 줄은 **콜백을 부르기 직전에** 명부에서 빠진다(명세의 inner invoke).
- ★ **그것을 확인하는 방법이 「예외를 던져 보는 것」이다.** 리스너가 예외를 던져도 호출은 **1회에서 멈춘다** — **이미 지워진 뒤에 불렸다**는 뜻이다. 예외는 콘솔로 새고 디스패치는 계속된다.
- **`once` 안에서 자기를 다시 등록하면** 다음 판에 또 불린다(`["불렸다","불렸다"]`) — **떼고 다는 것을 손으로 한 것과 같다.**
- **`signal` 은 세 자리를 한 번에 뗀다** — 3회가 0회가 됐다.
- ★ **이미 `abort()` 된 signal 로 등록하면 0회** 다 — 명세가 「신호가 이미 중단됐으면 **그냥 돌아가라**」로 정한다. **등록 자체가 안 된다.**
- ★ **`capture` 를 다시 안 적어도 되는 것은 `once` 와 `signal`** 이다. (3)에서 샌 네 칸이 **원리상 생기지 않는다** — 그래서 요즘 관용구다.

### 7. 디스패치는 목록을 복사한다 — 더하기와 빼기가 비대칭이다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-15-life.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '12,18p'
디스패치 도중에 리스너 목록을 건드리면
  ① 리스너 안에서 새 리스너를 더하면  = ["첫째","둘째"]
     그 다음 디스패치에서는          = ["첫째","둘째","나중에 더한 것"]
  ② 리스너 안에서 뒤엣것을 지우면    = ["첫째","둘째"]
  ③ 지웠다가 곧바로 다시 더하면      = ["첫째"]
  ★ 더한 것은 이번 디스패치에 안 들어오고, 지운 것은 이번 디스패치에서 곧바로 빠진다.
  ★ 비대칭이다 — 명세가 「목록을 복사해 두되 지워진 것은 건너뛴다」로 정했기 때문이다.
(exit 0)
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-15-life.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '20,21p'
stopImmediatePropagation 과 견주면
  같은 요소의 뒤엣것을 막으면 = ["첫째"]  (정본은 목록의 17번 주제다)
(exit 0)
```

**왜 그런가**

- **① 더한 것은 이번 판에 안 들어온다** — `["첫째","둘째"]`. **그 다음 판**에서야 `["첫째","둘째","나중에 더한 것"]` 이 된다.
- **② 지운 것은 이번 판에서 곧바로 빠진다** — 「셋째」가 안 불렸다.
- ★ **③ 지웠다가 곧바로 다시 더하면 `["첫째"]` 뿐이다** — 한 번도 안 불린다.
- **대칭이 아니다.** 명세의 「inner invoke」가 두 가지를 동시에 한다.
  - **디스패치를 시작할 때 명부를 통째로 복사한다** → 뒤에 더한 줄은 복사본에 없어 **이번 판에 안 보인다.**
  - **복사본의 줄을 부르기 직전에 「아직 명부에 있나」를 다시 본다** → 지워진 줄은 **건너뛴다.**
- **③ 은 그 둘이 겹친 것**이다 — 복사본의 그 줄은 **이미 명부에 없고**, 명부의 새 줄은 **복사본에 없다.**
- **`stopImmediatePropagation()` 은 같은 요소의 뒤엣것까지 막아** 겉보기 결과가 `["첫째"]` 로 같다. 하지만 **하는 일이 다르다** — 지우기는 **명부를 바꾸고**, 이쪽은 **이번 디스패치만 멈춘다.** 정본은 목록의 **17번 주제**다.

### 8. `passive` 는 `preventDefault()` 를 조용히 무효로 만든다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-15-passive.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,5p'
passive 가 preventDefault 를 막는다
  passive: true  에서 preventDefault() 뒤 defaultPrevented = false
  passive: false 에서 preventDefault() 뒤 defaultPrevented = true
  ★ 예외가 아니라 「아무 일도 안 일어남」이다. 경고 한 줄이 콘솔에만 남는다.
  ★ cancelable 은 그대로 true 다 — 이벤트가 막을 수 없게 된 것이 아니라 이 리스너가 못 막는 것이다.
(exit 0)
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --enable-logging=stderr --dump-dom wa12b-15-passive.html 2>&1 >/dev/null | grep ':CONSOLE:' | sed 's/^\[[0-9:/.]*INFO:CONSOLE:[0-9]*\] //' | sed 's#, source: file://[^ ]*/# · #'
"Unable to preventDefault inside passive event listener invocation." · wa12b-15-passive.html (14)
"Unable to preventDefault inside passive event listener invocation." · wa12b-15-passive.html (14)
(exit 0)
```

**왜 그런가**

- **`passive: true` 에서 `defaultPrevented` 가 `false`**, **`passive: false` 에서 `true`** 다.
- **예외도 반환값도 없다** — 명세가 「passive 면 **set the canceled flag 를 하지 마라**」로 정한다. **아무 일도 안 일어난다.**
- **경고 한 줄이 콘솔에만 남는다**(`Unable to preventDefault inside passive event listener invocation.`).
- ★ **`e.cancelable` 은 그대로 `true`** 다. **이벤트가 막을 수 없게 된 것이 아니라 이 리스너가 못 막는 것**이다. 그래서 **`if (e.cancelable) e.preventDefault()` 로 판정하면 틀린다** — `cancelable` 은 **이벤트의 성질**이고 `passive` 는 **리스너의 성질**이라 둘이 서로를 모른다.
- ★ ★ **콘솔 줄 수를 근거로 쓰면 안 된다.** 이 실행에서 `passive` 리스너 안의 `preventDefault()` 는 **여덟 번** 불렸는데 콘솔에는 **두 줄**만 남았고, 두 줄 다 **같은 소스 줄**을 가리킨다. Chrome 이 같은 자리를 합친다. **「경고가 안 보인다」는 「안 났다」가 아니다.**
- ★ **`passive` 가 스크롤을 얼마나 빠르게 하는지는 재지 않았다** — 이 문서는 **규칙만** 주장한다. 이득의 정본은 목록의 **19번 주제**다.

### 9. 기본값이 대상에 달려 있다 — 코드만 읽어서는 안 보인다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-15-passive.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '7,21p'
기본값이 passive 인 자리 — 같은 코드가 대상에 따라 갈린다
어디에 달았나             이벤트        preventDefault 가 먹히나
window                    touchstart    ★ 안 먹힌다 (기본이 passive)
window                    touchmove     ★ 안 먹힌다 (기본이 passive)
window                    wheel         ★ 안 먹힌다 (기본이 passive)
window                    mousewheel    ★ 안 먹힌다 (기본이 passive)
window                    click         먹힌다
document                  touchstart    ★ 안 먹힌다 (기본이 passive)
document.body             touchstart    ★ 안 먹힌다 (기본이 passive)
document.documentElement  touchstart    ★ 안 먹힌다 (기본이 passive)
평범한 div                touchstart    먹힌다
평범한 div                wheel         먹힌다

★ window·document·body·html 에 다는 touchstart·touchmove·wheel·mousewheel 은 기본이 passive 다.
★ 나머지는 기본이 passive 가 아니다. 같은 한 줄이 대상에 따라 다르게 산다.
(exit 0)
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-15-passive.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '23,27p'
되돌리려면 passive: false 를 명시한다
  window + {passive: false} 에서 = true

passive 는 동일성 키가 아니므로 지울 때는 안 적어도 된다
  {passive:true} 로 달고 옵션 없이 지운 뒤 호출 = 0회
(exit 0)
```

**왜 그런가**

- ★ **`window`·`document`·`document.body`·`document.documentElement`** 에 다는 **`touchstart`·`touchmove`·`wheel`·`mousewheel`** 은 **기본이 `passive`** 다. 옵션을 한 글자도 안 적었는데 그렇다.
- **같은 넷이라도 `click` 은 아니다** — `window` 의 `click` 에서는 먹혔다. **이벤트 종류 넷에만** 걸린다.
- **평범한 `div` 에서는 `touchstart` 도 `wheel` 도 먹힌다** — **대상이 갈림길**이다.
- **왜 그렇게 정했나** — 문서 전체를 덮는 스크롤 관련 리스너가 **스크롤을 붙들 수 있어서**다. 기본을 `passive` 로 두면 브라우저가 **리스너를 기다리지 않고 스크롤할 수 있다.** (**이 문서는 그 이득을 재지 않았다.**)
- **되돌리려면 `{passive: false}` 를 명시**한다 — `window` 에서도 `true` 가 됐다.
- ★ **코드만 읽어서는 알 수 없다.** 같은 한 줄이 `window` 에서는 안 먹히고 `div` 에서는 먹힌다. **대상을 보고 판단해야** 한다.
- **지울 때는 `passive` 를 안 적어도 된다** — A3 대로 열쇠가 아니다(0회).

### 10. 창 ④ 가 본체인 이유 — 나머지 창은 원리상 말을 못 한다

**출력** — 이 답의 근거는 앞의 블록들 전부와 명세의 `EventTarget` 표면이다. 새 출력은 없다.

**왜 그런가**

- **창 ① 이 부적용인 이유** — `addEventListener` 로 단 리스너는 **속성으로 남지 않는다.** `--dump-dom` 으로 뽑은 트리에 **한 글자도 안 나온다.**
- **창 ② 가 부적용인 이유** — 노드에 **물어볼 프로퍼티가 없다.** 명세상 `EventTarget` 의 표면은 `addEventListener`·`removeEventListener`·`dispatchEvent` **셋뿐**이고, 셋 다 「지금 무엇이 달려 있나」를 안 알려 준다. `addEventListener` 의 반환값은 `undefined` 다.
- ★ **창 ③ 은 「같은 이벤트를 두 번 던지기」로 바뀌었다.** 「대입하고 되읽기」가 성립하지 않으므로 **같은 질문(「그 줄이 아직 사나」)을 다른 창으로** 물은 것이다 — 이것이 **제5의 상태**(「같은 질문을 다른 창으로 물었다」)다. `once` 의 판정(A6)이 정확히 그 자리다.
- **창 ④ 가 하는 일** — **이벤트를 던지고 몇 번 불렸나를 센다.** 0 이면 지워진 것, 1 이상이면 남은 것이다. 이 문서의 모든 판정이 이 한 가지에서 나왔다.
- ★ 콘솔을 근거로 쓸 때 **믿으면 안 되는 수치**는 「**경고의 건수**」다(A8). **있다/없다**는 근거가 되지만 **몇 줄인가**는 아니다.

### 11. 예외를 던지는 자리는 둘뿐이고 나머지는 전부 조용하다

**출력** — 근거는 A1·A2·A4·A8 의 블록이다. 새 출력은 없다.

**왜 그런가**

- **예외를 던지는 자리 둘**
  - **콜백 자리에 객체도 함수도 아닌 것**을 넘겼을 때 — `TypeError` 로 막힌다(A4).
  - **`super()` 를 안 부른 클래스** 같은 자바스크립트 자체의 오류 — 이 주제의 표면이 아니다.
- **나머지 네 가지는 전부 조용하다.**

  | 실패 | 어떻게 드러나나 |
  |---|---|
  | 옵션(`capture`)이 달라 **안 지워짐** | 던져 보면 **계속 불린다**(창 ④) |
  | 익명 함수·`bind` 라 **안 지워짐** | 던져 보면 **계속 불린다**(창 ④) |
  | `handleEvent` 오타로 **영영 안 불림** | 던져 보면 **0회**다. 콘솔에도 안 남는다 |
  | `passive` 에서 `preventDefault()` | `defaultPrevented` 가 **`false`** · 콘솔에 경고(건수는 못 믿는다) |

- **같은 열쇠로 두 번 등록한 것**도 예외가 아니라 **조용한 무시**다(A2).
- ★ **그래서 「됐다」를 확인하는 방법은 하나뿐이다** — **던져서 세기.** 리스너 코드를 고친 뒤에는 **호출 횟수를 직접 세는 한 줄**을 붙여 본다. 「달았으니 되겠지」는 이 주제에서 가장 비싼 가정이다.

### 12. 다른 주제와 잇기

**출력** — 이 답의 근거는 앞의 블록들과 이웃 주제들이다. 새 출력은 없다.

**왜 그런가**

- `capture` 의 정본은 목록의 **16번 주제**(전파 3단계)다 — **내려가며 잡나 올라가며 잡나**가 그쪽 이야기다. **이 주제가 맡은 부분은 「그 값이 동일성 키의 셋째 칸이라는 것」** 하나다. 두 편이 같은 낱말을 다른 각도에서 본다.
- **[12번 주제](../12-shadow-dom/2-summary.md)에서는 리스너를 어디에 다느냐가 `e.target` 을 바꾼다** — 그림자 경계 **밖**에 달면 `target` 이 호스트로 재타기팅되고, **안**에 달면 안쪽 요소 그대로다. **같은 콜백인데 받는 값이 달라진다.** `composedPath()` 는 어느 자리에서나 같다.
- `signal` 이 [목록의 **13번 주제**](../13-custom-element-lifecycle/)에서 값어치를 내는 이유 — 커스텀 요소는 `connectedCallback` 에서 달고 `disconnectedCallback` 에서 떼야 하는데, 그 짝을 맞추려면 **함수 참조와 `capture` 를 필드에 들고 있어야** 한다. `signal` 하나면 **`connected` 에서 컨트롤러를 만들고 `disconnected` 에서 `abort()`** 하는 두 줄로 끝난다. 그리고 그 요소는 **같은 부모에 다시 붙여도 한 쌍이 난다**([목록의 **13번 주제**](../13-custom-element-lifecycle/) 실측) — **떼는 쪽을 빠뜨리면 그때마다 한 줄씩 쌓인다.**
- 보통 함수의 `this` 는 JS 갈래 07번의 「**암시적 바인딩**」에 해당한다 — 브라우저가 `콜백.call(currentTarget, 이벤트)` 꼴로 부르기 때문이다. 화살표 함수가 그 규칙에서 빠지는 것도 같은 편이 정본이다.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · `--window-size=1000,800`. **엔진은 이것 하나다.** **크로스 브라우저 이식성은 이 문서의 주장 범위 밖**이다.

★ **시간은 재지 않았다.** 이 주제에서 `passive` 의 이득·리스너의 메모리는 **전부 못 잰 칸**이다.\
★ **이벤트는 전부 합성 이벤트**(`new Event`·`new WheelEvent`)로 던졌다. **진짜 입력은 던지지 않았다** — 진짜 터치·휠에서 달라지는 것은 확인하지 않았다.\
★ **창 ①·② 는 부적용**이다. 이 주제의 판정은 전부 **창 ④(던져서 세기)** 로만 했다.

**하네스** — 01\~14 와 같은 것을 쓴다. 블록은 `capture.sh` 가 전부 파일로 받았고 사람이 옮겨 적지 않았다.

```bash
# wa12b-15-rerun.sh
# 블록 하나를 다시 던지는 법
google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 \
  --dump-dom wa12b-15-ident.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}'

# 콘솔 경고를 따로 받는 법
google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 \
  --enable-logging=stderr --dump-dom wa12b-15-passive.html 2>&1 >/dev/null | grep ':CONSOLE:'
```

```js
// wa12b-15-win4.js
// 이 주제의 창 ④ — 던져서 센다
let n = 0;  const f = () => n++;
el.addEventListener('t', f, 등록옵션);
el.removeEventListener('t', f, 해제옵션);
el.dispatchEvent(new Event('t'));
n === 0 ? '지워졌다' : '★ 안 지워졌다';
// 한글 칸 정렬은 JS 안에서 2폭 padw 로 한다. padEnd 는 UTF-16 단위라 어긋난다.
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
```

★ **`--virtual-time-budget` 은 쓰지 않았다**(이 갈래의 정본 규칙).\
★ **출력은 `<pre>` 가 아니라 `<script type="text/plain">` 에 담아 마커로 잘랐다.**

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| 익명 함수·`bind` 의 동일성 | 2 | 동작 방식 (1) · A1 |
| 중복 등록 3단계 | 2 | 동작 방식 (2) · A2 |
| **동일성 격자 14칸** | 2 | 동작 방식 (3) · A3 |
| `handleEvent` 객체 · 지연 조회 · 비객체 4종 | 2 | 동작 방식 (4) · A4 |
| `this` 네 꼴 + 한 객체 두 자리 | 2 | 동작 방식 (5) · A5 |
| `once` 3단계 · `signal` 3단계 | 2 | 동작 방식 (6)·(7) · A6 |
| 디스패치 중 목록 변경 ①②③ + `stopImmediatePropagation` | 2 | 동작 방식 (8) · A7 |
| `passive` 대 비`passive` + 콘솔 | 2 | 동작 방식 (9) · A8 |
| **기본 `passive` 격자 10칸** + 되돌리기 | 2 | 동작 방식 (10) · A9 |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| 예외 문구 | `parameter 2 is not of type 'Object'.` 등 | **Chrome 의 문구**다. 외울 것은 이름(`TypeError`)이다 |
| 콘솔 경고 문구와 **줄 수** | 두 줄 | ★ 합쳐지는 규칙이 판에 달렸다 |
| **기본이 `passive` 인 대상·이벤트 목록** | 위 격자 | 구현 관행이 명세가 된 자리다. **판이 오르면 다시 찍는다** |
| 동일성 키가 셋인 것 | 위 격자 | **명세**가 정한 절차다. 값이 아니라 절차를 외운다 |
| 디스패치가 목록을 복사하는 것 | 위 출력 | **명세**(inner invoke)가 정한 절차다 |

**안 돌려 본 것** — ① Firefox·Safari 에서의 재현(엔진이 없다). ② **진짜 터치·휠 입력** — 합성 이벤트로만 던졌다. ③ **`passive` 의 성능 이득** — **재지 않았다.** ④ **리스너가 붙드는 메모리와 누수** — 힙을 안 찍었다. ⑤ **`el.onclick` 표면** — 이 문서의 대상이 아니라 던지지 않았다. ⑥ **`AbortSignal.timeout()`·`AbortSignal.any()`** — 던지지 않았다. ⑦ **`capture` 단계에서 `stopPropagation()`** — 목록의 17번 주제 몫이라 던지지 않았다. ⑧ **그림자 경계를 넘는 리스너** — [12번 주제](../12-shadow-dom/2-summary.md)가 정본이라 여기서 다시 던지지 않았다. ⑨ **워커·`document` 밖의 `EventTarget`**(`XMLHttpRequest`·`WebSocket` 등)에서 같은 규칙이 성립하는지 — **확인하지 않았다.**

## 용어 풀이

- **리스너(event listener)** — 명부의 한 줄. 타입·콜백·`capture` 와 성질(`once`·`passive`·`signal`)로 이루어진다.
- **동일성 조건** — `removeEventListener` 가 「같은 줄」로 인정하는 조건. **타입 · 콜백(같은 객체) · `capture`** 셋.
- **`capture`** — 이벤트가 내려갈 때 잡을지 올라갈 때 잡을지. 단계 자체의 정본은 목록의 **16번 주제**.
- **`once`** — 한 번 불리고 스스로 빠지는 성질. **부르기 직전에** 빠진다.
- **`passive`** — 「기본 동작을 막지 않겠다」는 약속. 어기면 `preventDefault()` 가 **조용히 무효**가 된다.
- **`signal`** — `AbortSignal`. `abort()` 한 번으로 묶인 리스너를 전부 뗀다.
- **`handleEvent`** — 객체를 리스너로 쓸 때 불리는 메서드 이름. **호출할 때마다** 찾는다.
- **`currentTarget`** — 지금 이 리스너가 달려 있는 요소. 보통 함수의 `this` 가 이것이다.
- **`defaultPrevented`** — `preventDefault()` 가 실제로 먹혔는지. `passive` 면 `false` 로 남는다.
- **inner invoke** — 명세에서 한 요소의 리스너들을 차례로 부르는 절차. **목록을 복사하고, 부르기 직전에 다시 본다.**
- **조용한 실패(silent failure)** — 예외도 경고도 없이 아무 일도 안 일어나는 것. 이 주제에 네 가지가 있다.
- **창 ④ (디스패치 계수기)** — 이벤트를 던져 몇 번 불렸나를 세는 관측. 이 주제의 본체다.
- **제5의 상태** — 같은 질문을 **다른 창으로 바꿔** 물은 것. 이 주제의 창 ③ 이 그렇다.
