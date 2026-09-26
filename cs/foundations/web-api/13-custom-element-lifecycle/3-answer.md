# web-api/13 — 커스텀 요소 수명주기: `customElements.define`·`connected`/`disconnected`/`attributeChanged`·업그레이드 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 받은 것**이다. 명령은 블록마다 배너로 실려 있고, **콘솔 블록 하나만 `--enable-logging=stderr` 로 따로** 받았다.\
> 규칙은 [WHATWG HTML Living Standard — Custom elements](https://html.spec.whatwg.org/multipage/custom-elements.html) 로 접지했다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.** 특히 **내장 요소 확장(`is=`)은 엔진마다 갈린다.**\
> ★ **못 잰 것이 둘 있다** — **페이지를 떠날 때의 `disconnectedCallback`** 과 **가비지 컬렉션**(A8·A10).

**★ 이 주제에는 흔들리는 칸이 거의 없다** — 시간도 좌표도 안 재고 **순서만** 재기 때문이다.

| 안 흔들리는 칸 | 흔들리는 칸 · 부적용인 칸 · 못 잰 칸 |
|---|---|
| 모든 콜백 **순서** · `constructor.name` · `:defined` · 이름 규칙의 통과/거절 · 예외 **이름** · `observedAttributes` 가 읽힌 **횟수** | Chrome 판 번호 · 예외의 **문구** · 콘솔 줄의 **파일 줄 번호** |
| 두 판을 돌려 **한 글자도 같았다** | ★ **합쳐진다** — 콘솔 줄 수(같은 자리를 Chrome 이 합친다) |
| — | ★ **부적용** — `--dump-dom` 트리로 「업그레이드됐나」 보기(A9) |
| — | ★ **못 잰다** — 페이지 이탈 시점 · 가비지 컬렉션(A8·A10) |

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `define` 전의 정체 — 알 수 없는 태그가 아니다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-13-order.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,7p'
define 하기 전 — 파서가 만들어 둔 요소의 정체
  constructor.name          = HTMLElement
  instanceof HTMLElement    = true
  matches(":defined")       = false
  customElements.get("my-card") = undefined
  ★ 알 수 없는 태그가 아니다 — HTMLElement 로는 이미 살아 있다. 「업그레이드 안 된 것」일 뿐이다.
  참고: 하이픈 없는 알 수 없는 태그는 HTMLUnknownElement 이다.
(exit 0)
```

**왜 그런가**

- **다섯 줄** — `constructor.name` 은 **`HTMLElement`**, `instanceof HTMLElement` 는 **`true`**, `matches(':defined')` 는 **`false`**, `customElements.get('my-card')` 는 **`undefined`**, `createElement('zzznope').constructor.name` 은 **`HTMLUnknownElement`**.
- ★★ **하이픈 하나가 둘을 가른다.** 하이픈이 든 이름은 **「앞으로 커스텀 요소가 될 수 있다」는 예약**이라 파서가 `HTMLElement` 로 만들어 둔다. 하이픈이 없으면 영영 그럴 수 없으므로 `HTMLUnknownElement` 다.
- ★ **「아직 정의 안 됨」은 `matches(':defined')` 한 줄에만** 나타난다. 태그 이름도, 자식도, 속성도, `instanceof` 도 전부 정상으로 보인다. **그래서 창 ② 가 필요하다.**
- **실무 함의** — 스크립트가 늦게 오면 그 사이 페이지에 **껍데기가 그려진다.** `my-el:not(:defined) { visibility: hidden }` 으로 가리는 관용구가 여기서 나온다(**이 문서는 그 CSS 를 던지지 않았다**).

### 2. `define` 한 줄이 만든 순서 — 넷이 고정이고 동기다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-13-order.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '9,19p'
define("my-card", MyCard) 한 줄이 만든 순서
   1. (define 을 부르기 직전)
   2. static observedAttributes 를 읽는다
   3. constructor
   4. attributeChangedCallback 라벨 null -> "처음값"
   5. connectedCallback
   6. (define 이 돌아온 직후)

  ★ 업그레이드는 define 이 돌아오기 전에 끝난다 — 동기다.
  ★ 순서가 고정이다: observedAttributes -> constructor -> attributeChanged(초기 속성) -> connected.
  ★ 안본다="이것도" 는 observedAttributes 에 없어 한 줄도 안 남겼다.
(exit 0)
```

**왜 그런가**

- **로그는 여섯 줄**이고, 가운데 넷이 수명주기다 — **`observedAttributes` → `constructor` → `attributeChangedCallback`(초기 속성) → `connectedCallback`.**
- ★★ **마지막 줄이 「(define 이 돌아온 직후)」인 것이 증명하는 것** — **업그레이드가 동기라는 것**이다. `define` 이 돌아오기 전에 넷이 전부 끝났다. 그래서 `define` 다음 줄에서 곧바로 인스턴스의 메서드를 불러도 된다.
- ★ **`observedAttributes` 가 가장 먼저인 이유** — 그 목록을 알아야 초기 속성을 훑을 수 있다. **`static` 인 것도 그 때문**이다. 인스턴스가 아직 없는 시점에 읽어야 한다.
- ★★ **초기 속성에도 `attributeChangedCallback` 이 온다** — `라벨` 이 `null -> "처음값"` 으로 한 번 왔다. 「값이 바뀐 적이 없는데 왜 오나」가 아니라 **「없음에서 있음으로 바뀐 것」으로 친다.**
- **`안본다="이것도"` 는 한 줄도 안 남았다** — `observedAttributes` 에 없기 때문이다. **목록에 없는 속성은 존재하지 않는 것처럼 지나간다.**

### 3. `define` 을 먼저 하면 — 초기 속성이라는 것이 없다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-13-order.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '28,36p'
define 한 뒤에 만들면 — 순서가 달라진다
   1. constructor
   2. (createElement 가 돌아온 직후)
   3. attributeChangedCallback 라벨 null -> "나중값"
   4. (setAttribute 가 돌아온 직후)
   5. connectedCallback
   6. (appendChild 가 돌아온 직후)
  ★ 이쪽은 constructor 가 먼저고 속성·연결은 내가 부른 만큼만 난다.
  ★ 「초기 속성에도 attributeChangedCallback 이 온다」는 업그레이드 경로의 성질이다.
(exit 0)
```

**왜 그런가**

- **순서** — `constructor` → (createElement 반환) → `attributeChangedCallback` → (setAttribute 반환) → `connectedCallback` → (appendChild 반환).
- ★★ **2번과 갈리는 칸은 「초기 속성에 콜백이 오나」** 다. 이 경로에는 **초기 속성이라는 것이 아예 없다** — 요소가 만들어지는 순간 속성이 하나도 없기 때문이다. 콜백은 **내가 `setAttribute` 를 부른 만큼만** 난다.
- ★ **나머지는 같은 절차다.** 세 콜백이 **내가 부른 DOM 연산에 하나씩** 붙는다 — 이쪽이 오히려 읽기 쉽다.
- ★★ **서버 렌더와 클라이언트 렌더에서 뜻하는 것** — 서버가 뱉은 마크업을 하이드레이션할 때는 **①** 경로라 속성이 이미 다 달린 채로 `attributeChangedCallback` 이 한꺼번에 온다. 클라이언트에서 만들 때는 **②** 경로라 속성을 넣는 순서대로 온다. **같은 컴포넌트 코드가 두 경로에서 콜백 횟수부터 다르다** — 초기화를 「몇 번째 콜백」에 기대어 쓰면 한쪽에서 깨진다.

### 4. 문서 밖 요소 — 업그레이드가 안 미친다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-13-upgrade.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,10p'
문서에 없는 요소는 define 해도 업그레이드되지 않는다
  define 전 constructor.name = HTMLElement
  define 직후 로그 = [] · constructor.name = HTMLElement
  ★ 「문서 안의 요소」만 자동으로 업그레이드된다 — 떼어 놓은 트리는 그대로다.

직접 재촉하는 두 길
  customElements.upgrade(밖) 뒤 로그 = ["constructor","attrChanged 라벨 null->\"ㄱ\""]
    constructor.name = Late · connected 는 안 불렸다(문서에 없으니까)
  그 요소를 문서에 붙이면 로그 = ["connected"]
  upgrade() 없이 그냥 붙이면 로그 = ["constructor","attrChanged 라벨 null->\"ㄴ\"","connected"]  <- 붙이는 순간 업그레이드된다
(exit 0)
```

**왜 그런가**

- **세 자리** —
  - `define` 직후: 로그 **`[]`** · `constructor.name` 은 그대로 **`HTMLElement`**.
  - `upgrade(밖)` 뒤: **`["constructor","attrChanged 라벨 null->\"ㄱ\""]`** · `constructor.name` 이 `Late`.
  - 문서에 붙인 뒤: **`["connected"]`**.
- ★★ **`define` 은 「문서(그림자 포함) 안의 요소」만 훑는다.** 떼어 놓은 트리·`DocumentFragment`·`<template>` 의 `content` 는 대상이 아니다.
- ★★ **`upgrade()` 가 `connectedCallback` 을 안 부르는 이유** — **「연결」은 문서에 있어야 성립하는 상태**이기 때문이다. 업그레이드는 「클래스를 갈아 끼우는 일」이고 연결은 「트리에 들어오는 일」로, **서로 다른 사건**이다.
- ★ **`upgrade()` 를 꼭 써야 하는 자리는 좁다** — 「문서에 붙이기 **전에** 인스턴스의 메서드·프로퍼티를 써야 할 때」뿐이다. 그냥 붙이면 세 콜백이 한꺼번에 나므로(출력 마지막 줄) 대부분의 경우 필요 없다.

### 5. `observedAttributes` 는 `define` 때 한 번 읽히고 굳는다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-13-upgrade.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '12,15p'
static observedAttributes 는 언제 읽히나
  define 직후 읽힌 횟수 = 1
  요소를 만들고 속성을 세 번 바꾼 뒤 읽힌 횟수 = 1 · 로그 = ["attrChanged 보는것","attrChanged 보는것"]
  ★ define 시점에 한 번만 읽는다 — 나중에 목록을 바꿔도 소용없다.
(exit 0)
```

**왜 그런가**

- **`static get` 으로 써도 부를 때마다 읽히지 않는다.** 읽힌 횟수가 **`define` 직후 1** 이고, **요소를 만들고 속성을 세 번 바꾼 뒤에도 1** 이다.
- ★★ **명세가 `define` 안에서 한 번 읽어 레지스트리에 저장하도록** 정해 두었다. 그래서 **나중에 목록을 바꿔도 아무 일도 안 일어난다** — 예외도 경고도 없이 조용하다.
- **목록에 없는 속성은 콜백을 안 낸다** — `안보는것` 을 바꿨는데 로그가 두 줄뿐이다.
- ★ **동적인 목록이 필요하면** 「모든 속성을 감시하는」 길은 없다. `MutationObserver`(목록의 **37번 주제**)로 따로 보거나, 목록을 넉넉히 선언해 둔다.

### 6. 생성자 규칙을 어기면 — 예외가 안 온다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-13-ctor.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,8p'
생성자 규칙을 어기고 createElement 로 만들면
  속성을 붙이면         = 예외 없음 · HTMLUnknownElement · tagName=BAD-ATTR
  자식을 만들면         = 예외 없음 · HTMLUnknownElement · tagName=BAD-CHILD
  super() 를 안 부르면  = 예외 없음 · HTMLUnknownElement · tagName=NO-SUPER
  생성자가 던지면       = 예외 없음 · HTMLUnknownElement · tagName=BAD-THROW
  규칙을 지키면         = 예외 없음 · 착한것 · tagName=OK-EL
  ★ 호출한 쪽에는 예외가 안 온다. 돌아온 것이 HTMLUnknownElement 로 바뀔 뿐이다.
  ★ 예외 전문은 콘솔에만 남는다 — 아래 콘솔 블록이 그 자리다.
(exit 0)
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-13-ctor.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '10,13p'
그 요소를 문서에 넣으면 어떻게 되나
  constructor.name = HTMLUnknownElement · matches(":defined") = false · isConnected = true
  ★ 「실패 상태」로 굳는다 — 나중에 upgrade() 를 불러도 안 살아난다.
  customElements.upgrade(망가진) 뒤 constructor.name = HTMLUnknownElement -> HTMLUnknownElement
(exit 0)
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --enable-logging=stderr --dump-dom wa12b-13-ctor.html 2>&1 >/dev/null | grep ':CONSOLE:' | sed 's/^\[[0-9:/.]*INFO:CONSOLE:[0-9]*\] //' | sed 's#, source: file://[^ ]*/# · #'
"Uncaught NotSupportedError: Failed to execute 'createElement' on 'Document': The result must not have attributes" · wa12b-13-ctor.html (24)
"Uncaught NotSupportedError: Failed to execute 'createElement' on 'Document': The result must not have children" · wa12b-13-ctor.html (25)
"Uncaught ReferenceError: Must call super constructor in derived class before accessing 'this' or returning from derived constructor" · wa12b-13-ctor.html (13)
"Uncaught Error: 생성자가 일부러 터진다" · wa12b-13-ctor.html (14)
"Uncaught NotSupportedError: Failed to execute 'createElement' on 'Document': The result must not have attributes" · wa12b-13-ctor.html (34)
(exit 0)
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-13-ctor.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '15,19p'
new 로 직접 부르면 — 검사가 없다
  new 속성붙임()  tagName=BAD-ATTR 속성수=1 · 예외 없음
  new 자식만듦()  tagName=BAD-CHILD 자식수=1 · 예외 없음
  new 슈퍼없음()  = ReferenceError 「Must call super constructor in derived class before accessing 'this' or returning from derived constructor」
  ★ 「생성자에서 하면 안 되는 일」을 강제하는 것은 생성자가 아니라 createElement 쪽이다.
(exit 0)
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-13-ctor.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '21,25p'
파서·innerHTML 로 만들면 — 검사가 아예 없다
  bad-attr  = 속성붙임 · 속성수=1
  bad-child = 자식만듦 · 자식수=1
  ★ 업그레이드 경로에는 「속성·자식을 만들면 안 된다」 검사가 없다 — 같은 클래스가 길에 따라 다르게 산다.
  ★ 그래서 규칙은 「어기면 터진다」가 아니라 「어기면 어떤 길에서는 조용히 죽는다」로 외운다.
(exit 0)
```

**왜 그런가**

- **다섯 줄이 돌려주는 것** —
  - `createElement('bad-attr')` → **`HTMLUnknownElement`** · 예외 없음
  - `createElement('bad-child')` → **`HTMLUnknownElement`** · 예외 없음
  - `createElement('no-super')` → **`HTMLUnknownElement`** · 예외 없음
  - `new 속성붙임()` → **`BAD-ATTR` · 속성 1개** · 예외 없음
  - `innerHTML` 로 파싱 → **`속성붙임` · 속성 1개** · 예외 없음
- ★★★ **호출한 쪽에는 예외가 한 번도 안 왔다.** 전부 **조용하다.** 돌아온 것이 `HTMLUnknownElement` 로 바뀔 뿐이고, 태그 이름은 `BAD-ATTR` 그대로다 — **겉은 멀쩡하고 알맹이만 없다.**
- ★★★ **예외 전문은 콘솔에만 있다** — `The result must not have attributes` · `The result must not have children`. 명세가 「생성자가 돌고 난 결과에 속성이나 자식이 있으면 **예외를 보고하고** 실패 상태의 요소를 돌려주라」고 정해 두었다. **`try/catch` 로는 잡히지 않는다.**
- ★ **한번 실패하면 굳는다** — `matches(':defined')` 가 `false` 이고 **나중에 `upgrade()` 를 불러도 안 살아난다.**
- ★★★ **세 경로 가운데 검사가 있는 곳은 하나뿐이다** — `createElement` 쪽. `new` 로 직접 부르면 검사가 아예 없고(속성도 자식도 그대로 붙는다), **파서·`innerHTML` 로 만들어 업그레이드하는 경로에도 검사가 없다.**
- ★★ **그래서 규칙을 「어기면 터진다」로 외우면 틀린다.** 정확한 문장은 **「어기면 `createElement` 경로에서만, 그것도 조용히 죽는다」** 이다. 파서로 만든 페이지에서는 멀쩡히 돌던 컴포넌트가 **스크립트로 만드는 순간** 죽는다.
- **`super()` 를 안 부른 것만 `ReferenceError`** 인데, 그것은 커스텀 요소 규칙이 아니라 **자바스크립트 자체의 규칙**이라 어디서든 터진다(정본은 JS 갈래 목록([`js/syntax/README.md`](../../languages/js/syntax/README.md))의 **16번**).

### 7. 이름과 등록이 거절되는 자리 — `SyntaxError` 와 `NotSupportedError`

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-13-name.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,17p'
이름 규칙 — 무엇이 valid custom element name 인가
던진 이름             결과
"my-el"               통과
"x-"                  통과
"a-b-c"               통과
"my-EL"               SyntaxError 「Failed to execute 'define' on 'CustomElementRegistry': "my-EL" is not a valid custom element name」
"My-El"               SyntaxError 「Failed to execute 'define' on 'CustomElementRegistry': "My-El" is not a valid custom element name」
"myel"                SyntaxError 「Failed to execute 'define' on 'CustomElementRegistry': "myel" is not a valid custom element name」
"-el"                 SyntaxError 「Failed to execute 'define' on 'CustomElementRegistry': "-el" is not a valid custom element name」
"1-el"                SyntaxError 「Failed to execute 'define' on 'CustomElementRegistry': "1-el" is not a valid custom element name」
"font-face"           SyntaxError 「Failed to execute 'define' on 'CustomElementRegistry': "font-face" is not a valid custom element name」
"annotation-xml"      SyntaxError 「Failed to execute 'define' on 'CustomElementRegistry': "annotation-xml" is not a valid custom element name」
"my-el2"              통과
"my-엘"               통과

  ★ 하이픈 하나가 전부가 아니다 — 소문자로 시작해야 하고 대문자가 섞이면 안 되며 예약된 이름이 있다.
  ★ 예약어 목록(annotation-xml·font-face 등)은 SVG·MathML 이 이미 쓰는 이름이다.
(exit 0)
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-13-name.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '19,23p'
같은 이름·같은 클래스를 두 번 등록하면
  처음 등록          = 통과
  같은 이름을 또     = NotSupportedError 「Failed to execute 'define' on 'CustomElementRegistry': the name "once-el" has already been used with this registry」
  같은 클래스를 다른 이름에 = NotSupportedError 「Failed to execute 'define' on 'CustomElementRegistry': this constructor has already been used with this registry」
  ★ 이름도 클래스도 한 번씩만 쓸 수 있다. 되돌리는 API 는 없다.
(exit 0)
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-13-name.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '25,36p'
클래스가 아닌 것을 넘기면
  함수 선언          = 통과
  화살표 함수        = TypeError 「Failed to execute 'define' on 'CustomElementRegistry': constructor argument is not a constructor」
  HTMLElement 를 안 물려받은 클래스 = 통과
  객체                = TypeError 「Failed to execute 'define' on 'CustomElementRegistry': parameter 2 is not of type 'Function'.」
  ★ 통과한 둘은 define 이 봐준 것이지 쓸 수 있다는 뜻이 아니다 — 만들 때 드러난다:
    document.createElement("plain-el") 의 결과 = HTMLUnknownElement
    document.createElement("fn-el")    의 결과 = HTMLUnknownElement
    (콘솔에 예외 전문이 남는다 — 13-ctor 와 같은 모양이다)

  ★ 이름에 아스키가 아닌 글자를 써도 된다 — 다만 첫 글자는 아스키 소문자여야 한다:
    "my-엘" = 통과 · "엘-my" = SyntaxError 「Failed to execute 'define' on 'CustomElementRegistry': "엘-my" is not a valid custom element name」
(exit 0)
```

**왜 그런가**

- **통과** — `my-el` · `x-` · `a-b-c` · `my-el2` · **`my-엘`**.
- **막힘** — `my-EL` · `My-El`(대문자) · `myel`(하이픈 없음) · `-el`(하이픈으로 시작) · `1-el`(숫자로 시작) · `font-face` · `annotation-xml`(예약어) · **`엘-my`**(첫 글자가 아스키 소문자가 아니다).
- ★★ **`my-엘` 이 통과하는 것이 의외다.** 조건은 **「아스키 소문자로 시작 + 하이픈을 담음 + 아스키 대문자 없음 + 예약어 아님」** 이고, **나머지 글자는 아스키가 아니어도 된다.**
- ★ **예약어는 SVG·MathML 이 이미 쓰는 이름**이다. 명세에 일곱 개가 나열돼 있다.
- ★★ **이름 문제와 등록 문제는 예외 이름이 다르다** — 이름이 틀리면 **`SyntaxError`**, 이미 쓴 이름·클래스면 **`NotSupportedError`** 다. **어느 쪽이 문제인지가 이름 한 줄에 드러난다.**
- ★★ **`plain-el`(`HTMLElement` 를 안 물려받은 `class`)과 `fn-el`(평범한 `function`)은 통과한다.** `define` 은 「생성자인가」만 보고 「`HTMLElement` 의 자손인가」는 안 본다.
- ★★★ **통과는 「쓸 수 있다」가 아니다** — 만들어 보면 **`HTMLUnknownElement`** 가 돌아오고 예외 전문은 **콘솔에만** 남는다. A6 과 같은 모양이다. **「통과도 출력이다」 — 통과한 문이 무엇을 만들었는지 다시 읽어야 한다.**
- **되돌리는 API 는 없다.** 그래서 같은 모듈이 두 번 읽힐 수 있는 환경에서는 `customElements.get(이름)` 으로 먼저 본다(A11).

### 8. `disconnectedCallback` 이 안 오는 자리 — 다섯

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-13-life.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,13p'
disconnectedCallback 은 언제 오고 언제 안 오나
무엇을 했나                             로그                                    뜻
다른 부모로 appendChild                 ["disconnected","connected"]            옮기기는 뗐다 붙이기다
원래 부모로 다시 appendChild            ["disconnected","connected"]            
같은 부모에 또 appendChild              ["disconnected","connected"]            제자리인데도 한 쌍이 난다
display:none 으로 숨기면                []                                      isConnected=true
remove()                                ["disconnected"]                        
부모의 innerHTML = ""                   ["disconnected"]                        
문서 밖 div 에 붙이면                   []                                      connected 가 안 온다
그 div 를 버리면                        []                                      disconnected 도 안 온다
그림자 트리 안에 만들면                 ["connected"]                           그림자도 「연결」이다
호스트를 떼면                           ["disconnected"]                        
다른 문서로 옮기면                      ["disconnected","adopted","connected"]  adopted 가 가운데 낀다
(exit 0)
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-13-life.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '15,18p'
moveBefore — 떼지 않고 옮기는 새 표면
  Element.prototype.moveBefore 가 있나 = function
connectedMoveCallback 이 있는 요소      ["connectedMove"]                       disconnected 가 안 난다
connectedMoveCallback 이 없는 요소      ["disconnected","connected"]            옛 코드를 위해 한 쌍을 낸다
(exit 0)
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-13-life.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '20,25p'
★ 「안 불리는 자리」 정리
  1. 문서(또는 그림자)에 붙은 적이 없으면 connected 도 disconnected 도 안 온다.
  2. display:none·visibility:hidden 은 아무 콜백도 안 낸다 — 연결은 그대로다.
  3. connectedMoveCallback 을 정의하면 moveBefore 가 disconnected 를 안 낸다.
  4. 페이지를 떠날 때(탭 닫기·이동)는 안 온다 — 이 문서의 도구로는 그 순간을 못 본다(못 잰 것).
  5. 가비지 컬렉션은 콜백을 내지 않는다 — 「소멸자」가 아니다.
(exit 0)
```

**왜 그런가**

- **안 오는 자리 다섯** —
  1. **`display: none`·`visibility: hidden`** — 「연결」은 **트리에 있나**이지 **보이나**가 아니다.
  2. **붙은 적이 없는 요소** — 문서 밖 `<div>` 에 만들어 붙이고 그 `<div>` 를 버려도 안 온다. **뗄 것이 없다.**
  3. **`moveBefore()` 로 옮길 때, `connectedMoveCallback` 을 정의한 요소** — 그쪽이 대신 불린다.
  4. **페이지를 떠날 때**(탭 닫기·다른 주소로 이동) — ★ **이 문서는 그 순간을 관측하지 못했다.** 로그를 뱉을 문서가 이미 없다. **「안 돌려 본 것」이 아니라 「못 잰 것」이다.**
  5. **가비지 컬렉션** — ★ **GC 시점을 이 도구로 몰 수 없어 확인하지 못했다.** 명세가 「콜백이 아니다」로 정해 두었을 뿐이다.
- ★★ **그래서 「정리」를 이 콜백에만 걸면 탭을 닫는 순간 아무 일도 안 일어난다.** 서버에 보낼 것이 있으면 [목록의 **24번 주제**](../24-document-lifecycle-events/)(`visibilitychange`·`pagehide`)와 [목록의 **34번 주제**](../34-send-beacon-and-keepalive/)(`sendBeacon`)를 쓴다.
- ★★ **`moveBefore()` 가 이 이야기를 바꾼다** — 「옮기기는 뗐다 붙이기다」라는 오래된 사실에 예외가 생겼다. 다만 **`connectedMoveCallback` 을 정의한 요소에만** 적용되고, 안 정의한 요소에는 **옛 코드를 위해 한 쌍을 그대로 낸다.** 새 표면이라 **다른 엔진에서 던지지 않았다.**
- **오는 자리** — `remove()` · `innerHTML = ""` · 다른 부모로 옮기기 · **같은 부모에 다시 붙이기**(제자리인데도) · 다른 문서로 옮기기(`adopted` 가 가운데 낀다) · 그림자 호스트를 떼기.

### 9. 같은 노드가 클래스를 갈아입는다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-13-order.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '21,26p'
업그레이드 뒤
  constructor.name    = MyCard
  matches(":defined") = true
  자식 텍스트는 그대로 = "파서가 먼저 만든 것"
  customElements.get("my-card") = MyCard
  customElements.getName(MyCard) = my-card
(exit 0)
```

**왜 그런가**

- ★★ **새 노드를 만들지 않는다는 근거 셋** — ① `id` 가 그대로(`#파서`), ② **자식 텍스트가 그대로**(`"파서가 먼저 만든 것"`), ③ **내가 들고 있던 참조가 그대로 통한다**(같은 변수로 읽었는데 `constructor.name` 만 바뀌었다). 프로토타입을 갈아 끼운 것이지 바꿔 끼운 것이 아니다.
- ★★★ **그래서 창 ① 이 부적용이다.** `--dump-dom` 은 태그 이름과 속성만 뱉는데 **그 둘이 업그레이드 전후로 한 글자도 같다.** 「재 봤더니 같았다」가 아니라 **잴 것이 없다** — 업그레이드는 직렬화에 자국을 안 남긴다.
- ★★ **업그레이드가 동기인 것이 중요한 이유** — `define` 다음 줄에서 곧바로 인스턴스를 쓸 수 있고, **`define` 이 여러 개 있으면 부른 순서대로 끝난다.** 만약 비동기였다면 「define 했는데 아직 안 살아났다」는 상태를 매번 다뤄야 했을 것이다. 대신 **업그레이드 도중에 사용자 코드가 돌므로** 생성자 안에서 DOM 을 크게 건드리면 그 자리에서 재진입이 난다 — 생성자 규칙이 엄한 배경이 이것이다.

### 10. 왜 창 ⑤ 가 필요한가

**출력** — 이 답의 근거는 A2(순서)와 A6(콘솔)의 블록이다. 새 출력은 없다.

**왜 그런가**

- ★ **창 ④ 가 답하는 것** — 「무엇이 불렸나」가 아니라 **「무엇이 몇 번째로 불렸나」** 다. 이 주제의 사실이 거의 전부 **순서**이기 때문에, 한 시점만 찍으면 넷이 구분되지 않는다. 콜백을 전부 **로그 배열**로 받아 한 번에 읽는 것이 창 ④ 다.
- ★★★ **창 ⑤(콘솔)가 없으면 생성자 규칙의 예외 전문이 통째로 안 보인다.** 반환값에도 없고 `try/catch` 에도 안 잡힌다. **`--enable-logging=stderr` 를 붙이지 않으면 이 주제에서 가장 중요한 사실이 사라진다.**
- ★★ **「콘솔에 두 줄뿐이니 두 번 났다」로 읽으면 안 된다.** Chrome 이 **같은 자리에서 난 것을 합친다** — [목록의 **15번 주제**](../15-listener-registration/)의 실측에서 여덟 번 어긴 것이 **두 줄로만** 남았다. **콘솔 줄 수는 건수의 근거가 못 된다.**
- ★★ **이 주제에서 못 재는 것은 둘이다** — **페이지 이탈 시점의 `disconnectedCallback`**(문서가 이미 없어 로그를 뱉을 자리가 없다)과 **가비지 컬렉션**(시점을 못 몬다). 둘 다 **「안 돌려 본 것」이 아니라 「못 잰 것」** 이다.
- **부적용인 창은 창 ①** 이다(A9).

### 11. 실무의 짝 맞추기

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-13-name.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '38,42p'
내장 요소 확장(customized built-in) 은 이 판에서 되나
  define("my-btn", 내단추, {extends: "button"}) = 통과
  createElement("button", {is:"my-btn"}) 의 constructor.name = 내단추 · outerHTML = <button is="my-btn"></button>
  matches(":defined") = true
  ★ Chrome 은 된다 — 그런데 이것은 엔진마다 갈리는 표면이라 이 문서가 이식성을 주장하지 않는다.
(exit 0)
```

**왜 그런가**

- ★★ **`connectedCallback` 에서 리스너를 달면 옮길 때마다 또 달린다.** A8 에서 **같은 부모에 다시 붙여도 한 쌍**이 났다 — DOM 을 재배치하는 코드가 있으면 리스너가 쌓인다. **처방은 `disconnectedCallback` 과 짝을 맞추는 것**이고, 더 나은 처방은 [목록의 **20번 주제**](../20-listener-lifetime/)의 `AbortController` 다 — `connectedCallback` 에서 컨트롤러를 만들어 `{signal}` 로 전부 달고 `disconnectedCallback` 에서 `abort()` 한 번이면 된다.
- ★★ **컴포넌트를 `<button>` 으로 만들 수 없는 이유** — [12번 주제](../12-shadow-dom/2-summary.md)에서 **`<button>` 에는 `attachShadow` 가 `NotSupportedError` 로 막힌다.** 해법은 둘이다. ① **커스텀 요소를 만들고 그 안에 `<button>` 을 넣는다**(권장). ② **내장 요소 확장**(`is=`)을 쓴다 — 출력에서 Chrome 은 **된다**. 그런데 **엔진마다 갈리는 표면**이라 이 문서는 이식성을 주장하지 않는다.
- ★ **같은 모듈이 두 번 읽힐 수 있으면** `customElements.get('my-el')` 로 먼저 보고 이미 있으면 건너뛴다. A7 에서 재등록이 **`NotSupportedError`** 였고 **되돌리는 API 가 없다.**
- **`is=` 로 만든 것도 `outerHTML` 에 `is="my-btn"` 이 남는다** — 직렬화하고 다시 파싱해도 같은 것이 선다.

### 12. 다른 주제와 잇기

**출력** — 이 답의 근거는 앞의 블록들과 선행 주제들이다. 새 출력은 없다.

**왜 그런가**

- ★ **[12번 주제](../12-shadow-dom/2-summary.md)와의 경계선** — **그쪽은 「경계가 무엇을 막나」**(공간)이고 **여기는 「언제 무엇이 불리나」**(시간)다. 한 문장으로: **거기는 어디까지 보이나, 여기는 언제 살아나나.** 둘이 만나는 자리가 「`connectedCallback` 에서 `attachShadow` 하기」인데, 그것은 **생성자 규칙 때문에 생성자에 못 쓰는 것이 아니라** 쓸 수 있다 — 그림자 루트는 **자식으로 안 세기** 때문이다(그 확인은 이 문서가 **하지 않았다**).
- ★★ **[03번 주제](../03-node-creation-insertion-removal/2-summary.md)의 「삽입은 복사가 아니라 이동이다」가 콜백이 한 쌍으로 나는 이유**다. 이미 트리에 있는 노드를 다시 삽입하면 **먼저 떼고 붙이므로** `disconnected` 와 `connected` 가 순서대로 난다. **제자리에 붙여도** 그 절차를 그대로 밟는다.
- ★ **[06번 주제](../06-attribute-vs-property/2-summary.md)의 구분이 그대로 걸린다** — `attributeChangedCallback` 은 **속성(attribute)** 쪽만 본다. `el.라벨 = 'x'` 처럼 **프로퍼티에 써도 콜백이 안 온다.** 반영(reflect)을 원하면 **내가 getter/setter 를 만들어 `setAttribute` 를 부르게** 해야 한다 — 내장 요소가 하는 일을 손으로 하는 셈이다.
- ★ **「떠날 때」의 정본은 [목록의 24번 주제](../24-document-lifecycle-events/)**(`visibilitychange`·`pagehide`·bfcache)다. `disconnectedCallback` 은 그 자리를 못 메운다(A8).

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · `--window-size=1000,800`. **엔진은 이것 하나다.** **크로스 브라우저 이식성은 이 문서의 주장 범위 밖**이다.

★ **콘솔을 따로 받은 이유** — 생성자 규칙 위반의 예외 전문이 **콘솔에만** 남기 때문이다(A6). `--dump-dom` 만으로는 이 주제의 핵심이 통째로 안 보인다.\
★ **시간은 재지 않았다.** 커스텀 요소의 비용에 대해 이 문서는 **한 줄도 주장하지 않는다.**\
★ **부적용인 창** — `--dump-dom` 트리로 「업그레이드됐나」 보기(A9). **못 잰 것이 아니라 잴 것이 없다.**\
★ **못 잰 것 둘** — **페이지 이탈 시점의 `disconnectedCallback`** 과 **가비지 컬렉션**(A8·A10).

**하네스** — 01\~12 와 같은 것을 쓴다. 블록은 `capture.sh` 가 전부 파일로 받았고 사람이 옮겨 적지 않았다.

```bash
# wa12b-13-rethrow.sh
# 블록 하나를 다시 던지는 법
google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 \
  --dump-dom wa12b-13-order.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}'

# 콘솔만 따로 받는 법 (생성자 규칙 위반의 예외 전문이 여기에만 남는다)
google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 \
  --enable-logging=stderr --dump-dom wa12b-13-ctor.html 2>&1 >/dev/null | grep ':CONSOLE:'
```

```js
// wa12b-13-window.js
// 이 주제의 창 ④ — 콜백을 전부 로그로 받아 '순서' 를 본다
const 로그 = [];
class L extends HTMLElement {
  static observedAttributes = ['라벨'];
  constructor() { super(); 로그.push('constructor'); }
  connectedCallback() { 로그.push('connected'); }
  disconnectedCallback() { 로그.push('disconnected'); }
  adoptedCallback() { 로그.push('adopted'); }
  attributeChangedCallback(n, o, v) { 로그.push('attrChanged ' + n); }
}
// 창 ⑤ — 콘솔. 생성자 규칙 위반은 반환값에도 예외에도 안 나오고 여기에만 남는다
// 창 ③ — 같은 요소를 define 전후로 두 번 읽는다
파서.constructor.name;   customElements.define('my-card', MyCard);   파서.constructor.name;
```

★ **`--virtual-time-budget` 은 쓰지 않았다**(이 갈래의 정본 규칙).\
★ **출력은 `<pre>` 가 아니라 `<script type="text/plain">` 에 담아 마커로 잘랐다.**\
★ **`--dump-dom` 은 `load` 뒤의 `setTimeout(…, 0)` 을 한 겹까지만 기다린다**(이 배치에서 직접 확인했다 — 두 겹을 걸면 출력이 통째로 사라진다). `whenDefined` 블록은 **한 겹 안에서 `await` 로 마이크로태스크를 돌려** 그 한계를 피했다.

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| `define` 전의 정체 5줄 | 2 | 동작 방식 (1) · A1 |
| **수명주기 순서 로그**(업그레이드 경로) | 2 | 동작 방식 (2) · A2 |
| 업그레이드 뒤의 동일성 5줄 | 2 | 동작 방식 (2) · A9 |
| **수명주기 순서 로그**(`createElement` 경로) | 2 | 동작 방식 (3) · A3 |
| 문서 밖 트리 + `upgrade()` + 붙이기 | 2 | 동작 방식 (4) · A4 |
| `observedAttributes` 읽힌 횟수 | 2 | 동작 방식 (5) · A5 |
| `whenDefined` 두 경우 + `:defined` | 2 | 동작 방식 (5) |
| **생성자 규칙 위반 5종**(`createElement`) | 2 | 동작 방식 (6) · A6 |
| 실패 상태가 굳는 것 + `upgrade()` 재시도 | 2 | 동작 방식 (6) · A6 |
| **콘솔 전문**(`--enable-logging=stderr`) | 2 | 동작 방식 (6) · A6 · A10 |
| `new` 로 직접 부르기 3종 | 2 | 동작 방식 (6) · A6 |
| 파싱 경로 2종 | 2 | 동작 방식 (6) · A6 |
| **이름 13종** | 2 | 동작 방식 (8) · A7 |
| 재등록 3종 | 2 | 동작 방식 (9) · A7 |
| 생성자가 아닌 것 4종 + 통과한 둘의 실제 결과 | 2 | 동작 방식 (9) · A7 |
| 내장 요소 확장 4줄 | 2 | 동작 방식 (9) · A11 |
| **`disconnectedCallback` 11칸 격자** | 2 | 동작 방식 (7) · A8 |
| `moveBefore` 2종 | 2 | 동작 방식 (7) · A8 |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| 예외의 **문구** | 위 출력 | **이름은 명세, 문구는 구현**이다 |
| **콘솔 줄 수** | 5줄 | Chrome 이 같은 자리를 합친다. **건수의 근거로 쓰면 안 된다** |
| 콘솔 줄의 **파일 줄 번호** | `(24)` 등 | 소스를 한 줄만 고쳐도 바뀐다 |
| **내장 요소 확장(`is=`)** | 된다 | **엔진마다 갈린다.** Chrome 151 의 관찰로만 적었다 |
| **`connectedMoveCallback`·`moveBefore()`** | 위 출력 | **새 표면.** 다른 엔진에서 던지지 않았다 |
| **`customElements.getName()`** | `my-card` | **새 표면** |
| 이름 규칙의 통과/거절 | 위 출력 | **명세**가 정한 절차다. 값이 아니라 절차를 외운다 |
| 커스텀 요소의 **비용** | **안 쟀다** | 이 문서는 성능을 주장하지 않는다 |

**안 돌려 본 것** — ① Firefox·Safari 에서의 재현(엔진이 없다). ② **페이지 이탈 시점** — **못 쟀다.** ③ **가비지 컬렉션** — **못 쟀다.** ④ **`ElementInternals`·`formAssociated`·커스텀 상태(`:state()`)** — 던지지 않았다. ⑤ **스코프드 레지스트리**(`new CustomElementRegistry()`) — 던지지 않았다. ⑥ **`<template>` 의 `content` 안에서 꺼내 붙일 때의 `adoptedCallback`** — 따로 찍지 않았다. ⑦ **`my-el:not(:defined)` CSS 관용구** — 던지지 않았다. ⑧ **생성자 안에서 `attachShadow` 하기** — **확인하지 않았다.** ⑨ **`whenDefined` 가 유효하지 않은 이름에 거절되는 것** — 유효한 이름만 던졌다. ⑩ **업그레이드 도중 예외가 난 뒤의 재진입** — 던지지 않았다.

## 용어 풀이

- **커스텀 요소(custom element)** — 이름에 하이픈이 든, 스크립트가 클래스를 등록해 쓰는 요소.
- **업그레이드(upgrade)** — 이미 만들어진 요소의 **프로토타입을 등록된 클래스로 갈아 끼우고** 콜백을 부르는 절차. **새 노드를 만들지 않는다.**
- **수명주기 콜백(lifecycle callback)** — `constructor`·`connectedCallback`·`disconnectedCallback`·`adoptedCallback`·`attributeChangedCallback`, 그리고 새로 붙은 `connectedMoveCallback`.
- **`observedAttributes`** — 감시할 속성 이름 배열. **`static` 이고 `define` 때 한 번** 읽힌다.
- **실패 상태(failed custom element state)** — 생성자가 규칙을 어겼을 때 요소가 빠지는 상태. `HTMLUnknownElement` 가 되고 **다시 살아나지 않는다.**
- **`:defined`** — 업그레이드가 끝난 요소를 잡는 의사 클래스.
- **내장 요소 확장(customized built-in)** — `is=` 로 내장 요소를 확장하는 방식. **엔진이 갈린다.**
- **`connectedMoveCallback`** — `moveBefore()` 로 옮길 때 `disconnected`/`connected` 대신 불리는 새 콜백.
- **부적용인 창** — 「재 봤더니 같았다」가 아니라 **잴 것이 없는** 창. 이 주제에서는 `--dump-dom` 트리가 그렇다.
- **못 잰 것** — 도구가 그 순간을 볼 수 없어 확인하지 못한 것. 이 주제에서는 **페이지 이탈**과 **가비지 컬렉션**이 그렇다.
- **조용한 실패(silent failure)** — 예외도 경고도 없이 아무 일도 안 일어나는 것. 이 주제에서는 생성자 규칙 위반이 대표다.
