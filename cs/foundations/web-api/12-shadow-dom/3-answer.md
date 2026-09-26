# web-api/12 — Shadow DOM: `attachShadow`·캡슐화 경계·슬롯 할당·`::part` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 `--dump-dom` 으로 실제로 받은 것**이다. 명령은 블록마다 배너로 실려 있다.\
> 규칙은 [WHATWG DOM Standard](https://dom.spec.whatwg.org/) 와 [CSS Scoping Level 1](https://drafts.csswg.org/css-scoping/) 로 접지했다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**\
> ★ **마크업 쪽의 정본은 HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 10번** 이다. 여기는 **API 쪽**만 답한다.

**★ 이 주제에는 흔들리는 칸이 거의 없다** — 시간도 좌표도 거의 안 재기 때문이다.

| 안 흔들리는 칸 | 흔들리는 칸 · 부적용인 칸 |
|---|---|
| 모든 조회 결과 · `mode` · `assignedNodes` 의 내용과 순서 · 계산값 색 · `composedPath()` 의 길이와 내용 · 예외 **이름** | `getBoundingClientRect().width` 의 **소수점** — 0 인가 아닌가만 근거로 쓴다 |
| 두 판을 돌려 **99블록이 한 글자도 같았다** | Chrome 판 번호 · 예외의 **문구**(이름은 명세, 문구는 구현) |
| — | ★ **부적용** — `--dump-dom` 트리로 그림자 속 보기(A1). 「못 잰 것」이 아니라 **잴 것이 없다** |
| — | ★ **못 잰다** — 스크린리더가 슬롯된 내용을 **어떻게 읽는지** |

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 트리를 글자로 뽑으면 — 네 상자가 전부 비어 보인다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-12-tree.html 2>/dev/null | sed -n '4,8p'
</head><body><div id="열림"></div>
<div id="닫힘"></div>
<div id="선언"><span>라이트 자식</span></div>
<div id="직렬화"></div>
<script>
(exit 0)
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-12-tree.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,6p'
창 ① 이 못 보는 것을 창 ④ 로 꺼내 온다
  #열림.shadowRoot.innerHTML                    = "<b>스크립트로 만든 것</b>"
  #닫힘.shadowRoot                              = null
  #선언.shadowRoot.innerHTML                    = "<b>선언적</b>"
  #선언.querySelector("template")               = null
  #선언.childNodes                              = SPAN
(exit 0)
```

**왜 그런가**

- **세 상자 각각** — `#열림` 과 `#닫힘` 은 **빈 `<div>`** 로 찍히고, `#선언` 에는 **라이트 자식인 `<span>` 만** 남는다. 스크립트로 만든 것도, 마크업으로 만든 것도, 열린 것도 닫힌 것도 **전부 안 보인다.**
- **`#선언` 안의 `<template>` 은 사라졌다.** 파서가 그것을 먹어 섀도 루트로 바꿨기 때문이다 — `querySelector('template')` 도 `null` 이고 `childNodes` 에 `SPAN` 하나만 남았다. **정본은 HTML 갈래의 10번** 이다.
- ★★ **그래서 이 주제에서 창 ① 은 「부적용」이다.** 재 봤더니 같았던 것이 아니라 **잴 것이 없다** — `--dump-dom` 은 `outerHTML` 이고 **`outerHTML` 은 섀도 트리를 직렬화하지 않는다.**
- ★★★ **「트리를 봤는데 없더라」는 근거로 쓸 수 없다.** 그 창이 `null` 을 주는 이유가 둘이기 때문이다 — **없다** 와 **직렬화 대상이 아니다**. 이 둘은 창 ② 로만 갈린다(`shadowRoot.innerHTML` 이 곧바로 안을 준다).
- **`#닫힘.shadowRoot` 만 `null`** 이다. 나머지 셋은 루트를 준다 — 「안 보인다」의 이유가 **모드 때문이 아니라 창 때문**임이 이 한 줄에 드러난다.

### 2. 경계를 넘겨 꺼내려면 — 기본값은 「안 나옴」이다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-12-tree.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '8,14p'
getHTML() 로 경계를 넘겨 직렬화하면
  #열림.getHTML()                                = ""
  #열림.getHTML({serializableShadowRoots: true}) = ""
  #열림.getHTML({shadowRoots: [열림의 root]})    = "<template shadowrootmode=\"open\"><b>스크립트로 만든 것</b></template>"
  #직렬화.getHTML({serializableShadowRoots:true}) = "<template shadowrootmode=\"open\" shadowrootserializable=\"\"><b>직렬화를 허락한 것</b></template>"
  root.serializable — 열림 false · 직렬화 true · 선언 false
  ★ 기본값이 false 라 「직렬화해도 되는가」를 따로 허락해야 나온다.
(exit 0)
```

**왜 그런가**

- **여섯 줄** —
  - `열림.shadowRoot.innerHTML` → `"<b>스크립트로 만든 것</b>"` (창 ② 로는 그냥 나온다)
  - `닫힘.shadowRoot` → `null`
  - `열림.getHTML()` → `""`
  - `열림.getHTML({serializableShadowRoots: true})` → `""`
  - `열림.getHTML({shadowRoots: [열림.shadowRoot]})` → `<template shadowrootmode="open">…</template>`
  - `열림.shadowRoot.serializable` → `false`
- ★★ **넷째 줄이 비는 이유** — 그 옵션은 「**직렬화해도 된다고 표시된** 루트를 포함하라」는 뜻이지 「전부 포함하라」가 아니다. `#열림` 은 표시가 없다(`serializable` 이 `false`).
- **나오게 하는 길은 둘이다** — ① `attachShadow({ serializable: true })` 로 **허락을 달아 두거나**(마크업이면 `shadowrootserializable`), ② `{shadowRoots: [root]}` 로 **내가 쥔 참조를 직접 넘기거나**. `#직렬화` 줄이 ①, `#열림` 의 다섯째 줄이 ②다.
- ★ **②가 허락 없이 통하는 것이 창 ④ 의 성격을 그대로 보여 준다** — **참조를 이미 쥔 쪽에는 막을 것이 없다.**
- ★★ **꺼낸 문자열의 모양이 `<template shadowrootmode="open">…</template>`** 이다. 즉 **직렬화의 결과가 곧 선언적 Shadow DOM 의 마크업**이고, 뱉은 것을 그대로 다시 파싱하면 같은 그림자가 선다. **서버 렌더와 하이드레이션이 이 한 줄 위에 선다.**

### 3. `open` 과 `closed` — 갈리는 칸은 16 중 3, 실질은 둘

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-12-mode.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,23p'
open 과 closed 가 실제로 갈리는 칸은 몇 개인가
무엇을 물었나                             open                  closed                판정
host.shadowRoot                           ShadowRoot 를 준다    null                  갈린다
root.mode (참조로)                        open                  closed                갈린다
root.host (참조로)                        호스트를 준다         호스트를 준다         같다
root.querySelector("p") (참조로)          찾는다                찾는다                같다
document.querySelector("#속")             못 찾는다             못 찾는다             같다
안쪽요소.getRootNode().host (참조로)      호스트를 준다         호스트를 준다         같다
바깥 시트의 p 규칙이 닿나 (#민)           안 닿는다             안 닿는다             같다
body 의 color 가 상속되나 (#글씨)         rgb(0, 100, 0)        rgb(0, 100, 0)        같다
::part(핵심) 이 닿나                      닿는다                닿는다                같다
focus 뒤 document.activeElement           호스트를 준다         호스트를 준다         같다
focus 뒤 root.activeElement (참조로)      안쪽 단추를 준다      안쪽 단추를 준다      같다
문서 리스너가 본 e.target                 호스트로 바뀐다       호스트로 바뀐다       같다
문서 리스너가 본 composedPath 길이        7 칸                  5 칸                  갈린다
elementFromPoint 가 무엇을 주나           호스트를 준다         호스트를 준다         같다
host.getHTML({shadowRoots:[root]})        보인다                보인다                같다
root.serializable                         false                 false                 같다

갈린 칸 = 3 / 16

★ closed 가 막는 것은 「host 에서 root 로 가는 길」과 「composedPath 가 안을 보여 주는 것」 둘뿐이다.
  attachShadow 의 반환값을 들고 있으면 안을 고쳐 쓸 수 있다: 안쪽 문단 -> 닫힌 쪽(고쳐 씀)
(exit 0)
```

**왜 그런가**

- **두 모드에서 각각** —
  - `host.shadowRoot` → **`open` 은 루트, `closed` 는 `null`.** ★ 여기가 갈린다.
  - `root.mode` → `'open'` / `'closed'`. 모드 그 자체다.
  - `root.host` → **둘 다 호스트를 준다.**
  - `root.querySelector('b')` → **둘 다 찾는다.** `closed` 여도 참조만 있으면 안을 다 뒤진다.
  - `document.querySelector('#안쪽b')` → **둘 다 `null`.** 조회가 막히는 것은 **모드와 무관**하다.
  - `closed` 의 반환값으로 안을 고쳐 쓰면 → **그대로 고쳐진다**(출력 마지막 줄).
  - 안쪽 요소의 `getRootNode().host` → **둘 다 호스트**를 준다.
- ★★★ **갈리는 줄은 16 중 3이고, `root.mode` 를 빼면 둘이다** — `host.shadowRoot` 와 `composedPath()` 의 길이(7칸 대 5칸).
- ★★ **`closed` 는 보안 장치가 아니다. 근거 둘** —
  1. **`attachShadow` 의 반환값을 들고 있으면 안을 마음대로 읽고 고칠 수 있다.** 모드는 그 참조를 회수하지 않는다.
  2. **안쪽 요소를 한 번이라도 잡으면 `getRootNode().host` 로 바깥으로 나올 수 있다.** 막힌 것은 **바깥→안의 한 길**뿐이다.
- **`closed` 가 진짜로 주는 것** — 「남이 **실수로** 내 속을 만지지 않게 하는 규율」이다. 적대적 스크립트는 못 막는다(같은 페이지에서 도는 스크립트는 `attachShadow` 를 가로채는 것까지 할 수 있다).
- ★ **한 가지는 진짜로 막힌다** — `closed` 에서는 **바깥 리스너의 `composedPath()` 가 안쪽 칸을 안 보여 준다.** 로깅·분석 스크립트에 속을 안 흘리는 효과는 있다.

### 4. `attachShadow` 가 거절하는 자리 — 이 주제에서 유일하게 소리가 난다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-12-mode.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '25,34p'
attachShadow 가 거절하는 자리 — 이 주제에서 조용하지 않은 유일한 곳
  이미 붙은 호스트에 또  = NotSupportedError 「Failed to execute 'attachShadow' on 'Element': Shadow root cannot be created on a host which already hosts a shadow tree.」
  mode 를 안 주면        = TypeError 「Failed to execute 'attachShadow' on 'Element': Failed to read the 'mode' property from 'ShadowRootInit': Required member is undefined.」
  인자를 아예 안 주면    = TypeError 「Failed to execute 'attachShadow' on 'Element': 1 argument required, but only 0 present.」
  mode 가 모르는 값이면  = TypeError 「Failed to execute 'attachShadow' on 'Element': Failed to read the 'mode' property from 'ShadowRootInit': The provided value 'zzz' is not a valid enum value of type ShadowRootMode.」

호스트가 될 수 있는 요소는 정해져 있다
  되는 것   = <div> · <span> · <p> · <h1> · <section> · <my-el>
  안 되는 것 = <input> NotSupportedError · <br> NotSupportedError · <table> NotSupportedError · <button> NotSupportedError · <img> NotSupportedError
  <img> 가 거절될 때의 말 = NotSupportedError 「Failed to execute 'attachShadow' on 'Element': This element does not support attachShadow」
(exit 0)
```

**왜 그런가**

- **앞의 세 줄은 전부 예외**이고 이름이 둘로 갈린다.
  - **이미 붙어 있는 호스트에 또** → `NotSupportedError` (상태가 문제다)
  - **`mode` 를 안 주면 / 인자를 아예 안 주면** → `TypeError` (인자가 문제다)
  - 덧붙여 **`mode: 'zzz'`** 도 `TypeError` 다 — 열거값이 아니어서다.
- **되는 것과 안 되는 것** — `div`·`span`·`p`·`h1`·`section` 과 **하이픈이 든 이름**(`my-el`)은 되고, **`input`·`br`·`table`·`button`·`img` 는 `NotSupportedError`** 로 막힌다.
- ★ **규칙은 「허용 목록」이다.** 명세가 이름을 나열해 두었고, 거기에 더해 **유효한 커스텀 요소 이름**이면 받는다. 「아무 요소에나 붙는다」가 아니다.
- ★★ **여기가 이 주제에서 조용하지 않은 유일한 자리인 이유** — 나머지는 전부 **「찾았는데 없다」·「배정이 안 됐다」·「규칙이 아무것도 안 잡는다」** 처럼 **결과가 비는** 모양이다. 비는 것은 예외로 만들 수 없다(빈 결과가 정상인 경우가 훨씬 많다). 반면 `attachShadow` 는 **상태를 바꾸는 호출**이라 실패를 값으로 돌려줄 자리가 없어 던진다.
- **실무 함의** — `<button>` 에 못 붙는다. 그래서 단추 컴포넌트는 **커스텀 요소**([목록의 **13번 주제**](../13-custom-element-lifecycle/))를 만들고 그 안에 `<button>` 을 넣는다.

### 5. 안팎이 서로 찾으면 — 양방향으로 막힌다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-12-border.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,12p'
경계는 양쪽으로 막는다 — 같은 class 와 같은 id 를 안팎에 두고 서로 찾게 했다
무엇으로 찾았나                               찾았나                무엇이 나왔나
document.querySelector("#안문단")             false                 null
document.getElementById("안문단")             false                 null
document.querySelectorAll(".표적").length     2                     안쪽 것은 안 세어졌다
document.querySelectorAll("p").length         1                     바깥 문단 하나뿐
root.querySelector("#안문단")                 true                  #안문단
root.getElementById("안문단")                 true                  #안문단
root.querySelector("#바깥문단")               false                 null
안.closest("body")                            false                 null
안.closest("#host")                           false                 null
안.matches("body p")                          false                 선택자는 경계를 안 넘는다
(exit 0)
```

**왜 그런가**

- **일곱 줄** — `document.querySelector('#안문단')` 과 `getElementById` 둘 다 `null`, `.표적` 은 안팎에 셋인데 **2**, `root.querySelector('#안문단')` 과 `root.getElementById` 는 **찾고**, `root.querySelector('#바깥문단')` 은 `null`, `안.closest('body')` 와 `안.closest('#host')` 도 `null`.
- ★★ **경계는 양방향이다.** 바깥에서 안을 못 찾을 뿐 아니라 **안에서 바깥도 못 찾는다.** `matches('body p')` 조차 `false` 다.
- ★ **`closest('#host')` 가 `null` 인 이유** — `closest` 는 **자신부터 조상을 따라 올라가며** 선택자를 맞춰 보는데, 그림자 안 요소의 조상 사슬은 **`ShadowRoot` 에서 끝난다.** 호스트는 그 사슬 위에 없다(호스트는 **다른 나무**에 있다).
- ★★ **「그림자마다 같은 `id` 를 써도 되는 이유」가 여기서 나온다.** `id` 의 유일성은 **그 나무 안에서만** 요구된다 — 같은 `id` 를 가진 그림자를 셋 더 만들어도 `document.querySelectorAll('#안문단').length` 가 **0** 이었다(A6 의 마지막 블록). 컴포넌트를 100개 찍어도 `id` 가 안 부딪히는 것이 이 성질 덕이다.

### 6. 경계를 건너는 길 — 참조는 자유롭게 오간다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-12-border.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '14,28p'
그런데 참조는 자유롭게 오간다 — 경계를 건너는 길이 따로 나 있다
무엇을 물었나                                 무엇이 나왔나
안.getRootNode().constructor.name             ShadowRoot
안.getRootNode().host                         #host                 이 길로 바깥에 나간다
안.getRootNode({composed: true})              HTMLDocument          문서까지 올라간다
안.ownerDocument                              HTMLDocument          소유 문서는 하나다
안.isConnected                                true                  그림자 안도 연결돼 있다
root.parentNode                               null                  root 는 host 의 자식이 아니다
root.nodeType                                 11 (DocumentFragment) 05번 주제와 같은 번호다
root instanceof DocumentFragment              true
host.childNodes.length                        1                     라이트 자식만 센다
host.firstElementChild                        #라이트

★ 안에서 바깥을 못 보는 것은 「선택자가 경계를 안 넘는다」는 뜻이지 참조가 없다는 뜻이 아니다.
  getRootNode().host 하나면 바깥으로 나가고, 거기서부터는 평범한 문서다: BODY -> #바깥문단
(exit 0)
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-12-border.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '30,32p'
그래서 그림자마다 같은 id 를 써도 된다
  같은 id 를 가진 그림자를 셋 더 만든 뒤 document.querySelectorAll("#안문단").length = 0
  document.getElementById("안문단") = null
(exit 0)
```

**왜 그런가**

- **여덟 줄** — `getRootNode()` 는 `ShadowRoot`, `getRootNode().host` 는 `#host`, `getRootNode({composed:true})` 는 `HTMLDocument`, `ownerDocument` 는 `HTMLDocument`, `isConnected` 는 `true`, `root.parentNode` 는 `null`, `host.childNodes.length` 는 1, `host.firstElementChild` 는 `#라이트`.
- ★ **트리는 둘인데 문서는 하나다.** `ownerDocument` 가 같고 `isConnected` 도 `true` 다 — **그림자 안도 「문서에 연결된」 상태**다. 그래서 레이아웃도 되고 이벤트도 난다.
- ★★ **`root.parentNode` 가 `null` 인 것의 뜻** — 섀도 루트는 **호스트의 자식이 아니라 별도의 뿌리**다. 그래서 `host.childNodes` 에 안 들어가고, 트리를 위로 훑는 코드가 **경계에서 자연스럽게 멈춘다.** 「경계」라는 말이 은유가 아니라 **링크가 실제로 없다**는 뜻이다.
- **`root` 는 `DocumentFragment` 다**(`nodeType === 11`). [05번 주제](../05-documentfragment-and-template/2-summary.md)의 그 조각과 **같은 종류**이고, 다른 점은 **호스트를 갖고 화면에 그려진다**는 것뿐이다.
- ★★★ **「막힌다」는 전부 선택자 이야기다.** 참조는 안 막힌다 — `getRootNode().host` 한 줄이면 바깥이고, 거기서부터는 평범한 문서다(출력의 `BODY -> #바깥문단`). **경계는 「이름으로 찾는 길」만 끊는다.**

### 7. 스타일이 새나 — 선택자는 막히고 상속은 넘어온다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-12-style.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,9p'
바깥 시트의 규칙이 그림자 안으로 새나 — 같은 선택자가 안팎에 걸린다
무엇을                            color               border 폭     font-size
바깥 #바깥문단 (p · .테두리)      rgb(200, 0, 0)      3px           21px
그림자 안 #민 (p · .테두리)       rgb(0, 100, 0)      0px           21px
그림자 안 #상속 (선택자 없음)     rgb(0, 100, 0)      0px           21px
슬롯에 배정된 #라이트             rgb(0, 100, 0)      3px           21px

★ 선택자는 경계에서 멈추는데 상속은 넘어온다 — 둘은 다른 길이다.
  넘어온 것: color · font-size (상속되는 속성)   막힌 것: border (상속 안 되는 속성)
(exit 0)
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-12-style.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '11,15p'
안쪽 시트를 넣으면 — 그 시트는 안에서만 산다
무엇을                            color               border 폭
그림자 안 #민                     rgb(0, 0, 255)      1px
바깥 #바깥문단                    rgb(200, 0, 0)      3px
  ★ 안쪽 시트의 p 규칙이 바깥 문단을 건드리지 않았다. 양방향이다.
(exit 0)
```

**왜 그런가**

- **다섯 값** — 그림자 안 `#민` 의 `color` 는 **`rgb(0, 100, 0)`**(바깥 `p` 규칙의 빨강이 아니다), `borderTopWidth` 는 **`0px`**, `fontSize` 는 **`21px`**. 슬롯에 배정된 `#라이트` 는 `color` **`rgb(0, 100, 0)`**, `borderTopWidth` **`3px`**.
- ★★ **막힌 것은 선택자 매칭이고 넘어온 것은 상속이다. 둘은 같은 길이 아니다.**
  - **선택자**는 시트가 속한 나무 안에서만 맞춰 본다 — `p`·`.테두리` 가 경계를 못 넘는다.
  - **상속**은 선택자를 거치지 않고 **부모의 계산값에서 곧바로** 온다 — 경계가 막을 것이 없다. 그래서 `body` 의 `color`·`font-size` 가 그대로 왔다.
- ★ **그 증거가 `border` 다.** `border` 는 **상속되지 않는 속성**이라 안 넘어왔다. 「상속되는 속성만 넘어온다」가 정확한 문장이다.
- ★★ **슬롯에 배정된 자식이 바깥 규칙을 받는 이유** — **배정은 이동이 아니기 때문**이다. `#라이트` 는 여전히 라이트 DOM 에 있고 **바깥 나무의 요소**이므로, 바깥 시트가 그것을 잡는 것이 당연하다. 화면에서 그림자 안쪽에 그려지는 것과 **어느 나무에 사는가**는 별개다(A10).
- **안쪽 시트의 규칙은 바깥 문단을 안 건드린다** — 두 번째 블록에서 `#민` 만 파랑 1px 로 바뀌고 `#바깥문단` 은 그대로였다. **양방향이다.**

### 8. `::part` — 규칙이 담긴 채 아무것도 안 잡는다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-12-style.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '28,34p'
::part — 호스트가 허락한 구멍
무엇을                            color               part 속성
그림자 안 #파트 (part="핵심")     rgb(255, 0, 255)    핵심
그림자 안 #민 (part 없음)         rgb(0, 0, 255)      null
  #host::part(없는이름) 은 아무것도 안 잡는다 — 예외도 경고도 없다.
  바깥 문서 시트의 규칙 = body · p · .테두리 · #host::part(핵심) · #host::part(없는이름) · #겉::part(속것)
  ★ 규칙은 담겼는데 아무것도 안 잡는 상태다 — 08번 주제의 「담겼는데 졌나」와 다른 제4의 상태다.
(exit 0)
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-12-style.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '36,39p'
두 겹 안쪽에 닿으려면 — exportparts
  exportparts="핵심: 속것" 이 있을 때  #깊은.color = rgb(255, 128, 0)
  exportparts 를 떼면                  #깊은.color = rgb(0, 100, 0)
  ★ part 는 한 겹만 뚫는다. 두 겹을 뚫으려면 가운데 호스트가 다시 내보내야 한다.
(exit 0)
```

**왜 그런가**

- **세 줄** — `part="핵심"` 을 단 요소는 **`rgb(255, 0, 255)`**(바깥 규칙이 닿았다), `part` 없는 요소는 **안쪽 시트의 파랑**, 그리고 `document.styleSheets[0].cssRules` 에는 **`#host::part(핵심)` 과 `#host::part(없는이름)` 이 둘 다 담겨 있다.**
- ★★ **`part` 이름이 틀리면 예외도 경고도 없다.** 문법이 맞고 규칙도 담겼는데 **맞는 요소가 없어** 아무 일도 안 일어난다.
- ★★★ **그래서 「담겼는데 아무것도 안 잡는」 상태가 된다.** [08번 주제](../08-getcomputedstyle/2-summary.md)의 「담겼는데 **졌나**」와 다르다 — 진 것이 아니라 **애초에 대상이 없다.** 진단은 `cssRules` 가 아니라 **`root.querySelectorAll('[part]')` 로 이름을 세는 것**이다.
- ★ **`part` 는 한 겹만 뚫는다.** 두 겹 안쪽에 닿으려면 가운데 호스트가 **`exportparts` 로 다시 내보내야** 한다. 속성을 떼자 색이 곧바로 상속색으로 돌아갔다.
- **`exportparts="핵심: 속것"` 은 이름을 갈아 내보낸다** — 안쪽 `part` 이름이 **공개 계약이 되지 않게** 하는 장치다.

### 9. 슬롯 할당 — 두 길이의 차이는 텍스트 노드다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-12-slot.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,7p'
슬롯이 무엇을 받았나
무엇을 물었나                             무엇이 나왔나
머리슬롯.assignedNodes()                  #머리자식
머리슬롯.assignedElements()               #머리자식
기본슬롯.assignedNodes()                  #text #text #익명 #text #text         ★ 줄바꿈 공백도 배정된다
기본슬롯.assignedElements()               #익명                                 요소만 센다
기본슬롯.assignedNodes({flatten:true})    #text #text #익명 #text #text
(exit 0)
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-12-slot.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '9,15p'
자식 쪽에서 물으면
무엇을 물었나                             무엇이 나왔나
#머리자식.assignedSlot.name               "머리"
#익명.assignedSlot.name                   ""                                    이름 없는 슬롯은 빈 이름
#미아.assignedSlot                        null                                  ★ 맞는 칸이 없으면 null
  #머리자식.getBoundingClientRect().width = 97.28   #미아 = 0.00  <- 배정 못 받으면 안 그려진다
  ★ 예외도 경고도 없다. slot="없는칸" 오타는 「조용히 사라짐」으로만 드러난다.
(exit 0)
```

**왜 그런가**

- **일곱 줄** — `머리슬롯.assignedNodes()` 는 `#머리자식`, `기본슬롯.assignedNodes()` 는 **`#text #text #익명 #text #text`**(다섯), `기본슬롯.assignedElements()` 는 `#익명`(하나), `#머리자식.assignedSlot.name` 은 `"머리"`, `#익명.assignedSlot.name` 은 `""`, `#미아.assignedSlot` 은 `null`, `#미아.getBoundingClientRect().width` 는 **`0.00`**.
- ★★ **길이가 다른 이유** — `assignedNodes()` 는 **텍스트 노드까지** 세고 `assignedElements()` 는 **요소만** 센다. 다섯 중 넷이 **마크업의 줄바꿈 공백**이다([01번 주제](../01-document-and-node-tree/2-summary.md)의 그 공백 텍스트 노드다).
- **이름 없는 슬롯의 `name` 은 빈 문자열**이다 — `null` 이 아니다.
- ★★ **`slot="없는칸"` 오타는 이렇게 드러난다** — `assignedSlot` 이 **`null`** 이 되고 **화면에서 사라진다**(`rect.width` 가 0). **예외도 경고도 없다.** 맞는 칸이 없으면 「기본 칸으로 떨어지는」 것이 아니라 **아예 안 그려진다.**
- ★ **진단은 `assignedSlot` 이다.** 「안 보인다」를 CSS 문제로 뒤지기 시작하면 한참 걸린다.

### 10. 배정과 기본 내용 — 투영이고, 공백이 막는다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-12-slot.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '17,24p'
배정은 옮기는 것이 아니다 — 트리는 그대로다
무엇을 물었나                             무엇이 나왔나
#익명.parentElement                       #host                                 여전히 host 의 자식이다
#익명.getRootNode()                       HTMLDocument                          문서 쪽에 남아 있다
#익명.assignedSlot.getRootNode()          ShadowRoot                            슬롯은 그림자 쪽이다
host.children.length                      3                                     라이트 자식 셋
root.children.length                      2                                     슬롯 둘뿐이다
host.innerHTML 에 슬롯이 보이나           false                                 안 보인다
(exit 0)
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-12-slot.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '26,31p'
기본 내용(fallback)은 언제 보이나 — 여기서 공백 텍스트가 발목을 잡는다
  배정된 요소가 있을 때  #기본값 의 rect.width = 0.00
  #익명 을 뗀 뒤        배정 노드 = #text #text #text #text · #기본값 의 rect.width = 0.00
  ★ 요소를 다 뗐는데도 기본 내용이 안 나온다 — 줄바꿈 공백 텍스트가 아직 배정돼 있기 때문이다.
  공백 없이 만든 host 에서  배정 노드 = [] · #기본값2 의 rect.width = 112.02  <- 이제 나온다
  ★ 진단은 assignedNodes() 다 — rect 만 보면 「왜 기본값이 안 나오지」에서 막힌다.
(exit 0)
```

**왜 그런가**

- **네 줄** — `#익명.parentElement` 는 **`#host`**, `#익명.getRootNode()` 는 **`HTMLDocument`**, `host.children.length` 는 **3**, `root.children.length` 는 **2**.
- ★★★ **배정은 이동이 아니라 투영이다. 근거 셋** — ① 부모가 여전히 호스트다, ② 뿌리가 여전히 문서다, ③ 두 목록(`host.children` 과 `root.children`)이 **섞이지 않는다**. 덧붙여 `host.innerHTML` 에 `<slot>` 이 안 보인다 — 직렬화도 나무를 섞지 않는다.
- ★ **`assignedSlot` 쪽은 `ShadowRoot` 에 산다.** 한 관계가 두 나무를 잇고 있는 셈이고, 그 관계가 만드는 「그려지는 순서」를 **평탄 트리(flat tree)** 라 부른다.
- ★★ **요소를 다 뗐는데 기본 내용이 안 나오는 원인** — **줄바꿈 공백 텍스트 노드가 아직 배정돼 있기 때문**이다. 기본 내용은 **배정이 완전히 비었을 때만** 나온다. 출력에서 요소를 뗀 뒤에도 `#text` 넷이 남아 있고 `rect.width` 가 `0.00` 그대로였다.
- ★★ **진단하는 법** — **`slot.assignedNodes()` 를 찍는다.** `rect.width` 만 보면 「왜 기본값이 안 나오지」에서 막힌다. 공백 없이 만든 호스트에서는 배정이 `[]` 가 되고 곧바로 `112.02` 가 나왔다.
- **실무 처방** — 마크업을 `<div id="host"><b>x</b></div>` 처럼 **한 줄로 붙이거나**, `{flatten: true}` 로 물어 「실제로 그려지는 것」을 본다(A11 의 짝).

### 11. 왜 창 ④ 가 필요한가

**출력** — 이 답의 근거는 A1·A2·A3 의 블록이다. 새 출력은 없다.

**왜 그런가**

- ★★ **창 ① 이 막히는 것은 도구의 흠이 아니라 명세의 결과다.** `--dump-dom` 은 `outerHTML` 이고, **`outerHTML` 이 섀도 트리를 직렬화하지 않도록 명세가 정해 두었다.** 캡슐화가 목적이므로 **내보내기가 opt-in** 이다(A2 의 `serializable` 이 그 스위치다). 더 좋은 도구를 쓰면 보이는 종류의 한계가 아니다.
- ★ **창 ④ 가 하는 일을 한 문장으로** — **「참조를 들고 경계를 넘어가, 바깥에서는 못 묻는 것을 안에서 묻는다.」**
- ★★ **창 ④ 가 요구하는 허락** — **열쇠**다. `open` 이면 호스트가 `shadowRoot` 로 사본을 내주고, `closed` 면 **`attachShadow` 가 돌려준 그 참조**만 통한다. 남이 만든 `closed` 그림자는 페이지 스크립트가 **다시 잡을 방법이 없다**(HTML 갈래의 **10번** 이 그 실측이다).
- ★★★ **이 주제에서 부적용인 창은 창 ①**(`--dump-dom` 트리 · `outerHTML` · `getHTML()` 의 기본값)이다. **「재 봤더니 같았다」가 아니라 「잴 것이 없다」** — 그 구분 자체가 결론이다. 「안 보인다」를 「없다」로 읽는 사고가 이 주제에서 가장 흔하다.
- **창 ② 와 창 ③ 은 그대로 쓴다** — 창 ② 는 `shadowRoot.innerHTML`·`assignedNodes()`·`getRootNode()` 로, 창 ③ 은 **같은 질문을 바깥에서 한 번 · 경계 안에서 한 번** 물어 **답이 갈리는 자리가 곧 경계**임을 보이는 데 쓴다((3)의 격자가 그 형태다).

### 12. 다른 주제와 잇기

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-12-event.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,12p'
한 번의 click 을 일곱 자리에서 본다 — e.target 과 composedPath()
리스너를 어디에 달았나    e.target      e.currentTarget composedPath()
안쪽 단추                 #단추         #단추           #단추 #껍데기 #shadow-root #host BODY HTML #document Window
그림자 안 #껍데기         #단추         #껍데기         #단추 #껍데기 #shadow-root #host BODY HTML #document Window
ShadowRoot                #단추         #shadow-root    #단추 #껍데기 #shadow-root #host BODY HTML #document Window
호스트 #host              #host         #host           #단추 #껍데기 #shadow-root #host BODY HTML #document Window
document.body             #host         BODY            #단추 #껍데기 #shadow-root #host BODY HTML #document Window
document                  #host         #document       #단추 #껍데기 #shadow-root #host BODY HTML #document Window
window                    #host         Window          #단추 #껍데기 #shadow-root #host BODY HTML #document Window

★ composedPath() 는 어디서 보든 한 글자도 같다 — 경계 안팎이 같은 배열을 받는다.
★ e.target 만 「보는 자리가 경계 밖이면 호스트로」 바뀐다.
(exit 0)
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-12-event.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '24,26p'
슬롯에 배정된 자식에서 나는 이벤트는 재타기팅되나
  target=#슬롯자식 · composedPath()=#슬롯자식 SLOT #shadow-root #host BODY HTML #document Window
  ★ 슬롯 자식은 라이트 DOM 에 있으므로 재타기팅되지 않는다. 경로에 <slot> 이 끼어 있을 뿐이다.
(exit 0)
```

**왜 그런가**

- ★ **HTML 갈래의 10번과의 경계선** — **그쪽은 「파서가 마크업을 보고 무엇을 만드나」**(`<template>` 이 왜 안 사나 · `shadowrootmode` 의 값 · 선언적 Shadow DOM 이 덤프에서 어떻게 보이나)이고, **여기는 「그것을 스크립트로 만들고 들여다보는 API」** 다. 한 문장으로: **거기는 마크업이 만드는 것, 여기는 만들어진 것을 무엇으로 묻나.**
- ★★ **`e.target` 이 호스트로 오는 현상의 이름은 재타기팅(retargeting)** 이다. 출력에서 그림자 안 세 자리는 `#단추` 를 보고 **호스트부터 바깥 네 자리는 전부 `#host`** 를 본다. `composedPath()` 는 **일곱 줄이 한 글자도 같다.**
- ★ **정본은 [목록의 21번 주제](../21-custom-events/)**(`CustomEvent`·`dispatchEvent`·`composed`)다. 전파 자체는 [목록의 **16번 주제**](../16-event-propagation-phases/), 위임이 깨지는 이야기는 [목록의 **18번 주제**](../18-event-delegation/). **여기서는 「경계가 무엇을 하는가」까지만** 본다.
- ★ **슬롯에 배정된 자식은 재타기팅되지 않는다** — 라이트 DOM 에 있기 때문이다. 경로에 `<slot>` 이 끼어 있을 뿐이다. **배정이 경로에는 반영되고 소유에는 반영되지 않는** 것이 한 줄로 보인다.
- ★★ **[10번 주제](../10-layout-thrashing/2-summary.md)와 견주면 이 주제는 명세 쪽이다.** 그 주제는 **언제 레이아웃이 돌아가는가**라는 **구현의 선택**을 실측으로 재는 주제이고, 여기는 **무엇이 막히는가**라는 **명세가 정한 계약**을 확인하는 주제다. 이 편의 표(「구현 세부사항 대 언어 보장」)에서 구현 쪽으로 분류된 것은 **예외 문구 · 좌표의 소수점 · `:host-context` 의 지원 여부** 정도뿐이다.
- ★ **[05번 주제](../05-documentfragment-and-template/2-summary.md)의 `DocumentFragment` 와 `ShadowRoot` 의 관계** — **`ShadowRoot` 는 `DocumentFragment` 를 상속한다**(`nodeType === 11` 이고 `instanceof DocumentFragment` 가 `true`). 다른 점은 **호스트를 갖고, 화면에 그려지고, 스타일 경계가 된다**는 셋이다. 「부모가 없는 조각」이라는 성질은 그대로다 — `root.parentNode` 가 `null` 인 것이 그 짝이다.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · `--window-size=1000,800`. **엔진은 이것 하나다.** **크로스 브라우저 이식성은 이 문서의 주장 범위 밖**이다.

★ **창 크기를 배너에 박은 이유** — `getBoundingClientRect()` 를 몇 군데에서 쓰기 때문이다. 다만 **이 문서는 그 값의 「0 인가 아닌가」만** 근거로 쓴다.\
★ **시간은 재지 않았다.** 그림자의 비용에 대해 이 문서는 **한 줄도 주장하지 않는다.**\
★ **부적용인 창** — `--dump-dom` 트리로 그림자 속 보기(A1). **못 잰 것이 아니라 잴 것이 없다.**\
★ **못 잰 것** — 스크린리더가 슬롯된 내용을 **어떤 순서로 읽는지**. 접근성 트리는 CDP 로 뜰 수 있지만 **그것은 보조 기술의 입력이지 출력이 아니다.**

**하네스** — 01\~11 과 같은 것을 쓴다. 블록은 `capture.sh` 가 전부 파일로 받았고 사람이 옮겨 적지 않았다.

```bash
# wa12b-12-rethrow.sh
# 블록 하나를 다시 던지는 법
google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 \
  --dump-dom wa12b-12-mode.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
```

```js
// wa12b-12-window.js
// 이 주제의 창 ④ — 참조를 들고 경계를 넘어가 묻는다
const root = host.attachShadow({ mode: 'closed' });   // 열쇠를 내가 쥔다
root.querySelector('b');                              // closed 여도 다 뒤진다
안쪽요소.getRootNode().host;                           // 안에서 바깥으로 나온다
// 창 ③ — 같은 질문을 두 자리에서 물어 답이 갈리는 곳이 경계다
document.querySelector('#안문단');  root.querySelector('#안문단');
// 한글 칸 정렬은 JS 안에서 2폭 padw 로 한다. padEnd 는 UTF-16 단위라 어긋난다.
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
```

★ **`--virtual-time-budget` 은 쓰지 않았다**(이 갈래의 정본 규칙).\
★ **출력은 `<pre>` 가 아니라 `<script type="text/plain">` 에 담아 마커로 잘랐다.**\
★ **`--dump-dom` 은 `load` 뒤의 `setTimeout(…, 0)` 을 한 겹까지만 기다린다**(이 배치에서 직접 확인했다 — 두 겹을 걸면 출력이 통째로 사라진다). 이 주제의 블록은 전부 동기라 걸리지 않았다.

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| 덤프 트리 + 네 상자의 `shadowRoot` | 2 | 동작 방식 (1) · A1 |
| `getHTML` 네 꼴 + `serializable` 세 값 | 2 | 동작 방식 (2) · A2 |
| **`open`/`closed` 16칸 격자** + 갈린 칸 자동 집계 | 2 | 동작 방식 (3) · A3 |
| `attachShadow` 거절 4종 + 호스트 후보 11종 | 2 | 동작 방식 (4) · A4 |
| 안팎 조회 10줄 | 2 | 동작 방식 (5) · A5 |
| 경계를 건너는 참조 10줄 + 같은 `id` 셋 | 2 | 동작 방식 (6) · A6 |
| 스타일 상속·차단 4행 × 3열 | 2 | 동작 방식 (7) · A7 |
| 안쪽 시트의 방향 2행 | 2 | 동작 방식 (7) · A7 |
| `:host`·`:host(.x)`·`:host-context` + 트리 순서 대 명시도 | 2 | 동작 방식 (8) |
| `::part` 2행 + `cssRules` 목록 | 2 | 동작 방식 (9) · A8 |
| `exportparts` 있을 때 / 뗐을 때 | 2 | 동작 방식 (9) · A8 |
| 슬롯 배정 5줄 + 자식 쪽 3줄 + `rect` | 2 | 동작 방식 (10) · A9 |
| 투영 6줄 + 기본 내용 3단계 | 2 | 동작 방식 (11) · A10 |
| `slotAssignment: 'manual'` 6줄 + 자동 모드에 `assign()` | 2 | 동작 방식 (12) |
| `flatten` 4줄 | 2 | 동작 방식 (13) |
| **재타기팅 7자리 격자** | 2 | 동작 방식 (14) · A12 |
| `composed`/`bubbles` 2조합 + 생성자 기본값 6종 | 2 | 동작 방식 (15) |
| 슬롯 자식의 재타기팅 | 2 | 동작 방식 (15) · A12 |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| 예외의 **문구** | 위 출력 | **이름은 명세, 문구는 구현**이다. 판이 오르면 바뀐다 |
| `getBoundingClientRect().width` | `97.28` · `112.02` | 글꼴·창 크기에 달렸다. **0 인가 아닌가만** 근거로 쓴다 |
| **`:host-context()`** | 먹는다(`padding-left: 7px`) | 표준화가 흔들린 표면이다. **Chrome 151 의 관찰**로만 적었다 |
| **`slotAssignment: 'manual'` · `serializable` · `getHTML()`** | 위 출력 | **새 표면**이다. 다른 엔진에서 던지지 않았다 |
| `attachShadow` 허용 요소 목록 | 위 출력 | **명세**가 정한 목록이다. 값이 아니라 절차를 외운다 |
| 그림자의 **비용** | **안 쟀다** | 이 문서는 성능을 주장하지 않는다 |

**안 돌려 본 것** — ① Firefox·Safari 에서의 재현(엔진이 없다). ② **`::slotted()`** — 던지지 않았다. ③ **`delegatesFocus: true`** — 던지지 않았다(포커스는 [목록의 **14번 주제**](../14-dialog-popover-scripting/)의 몫이다). ④ **`slotchange` 이벤트** — 관측하지 못했다. ⑤ **`adoptedStyleSheets`** — 던지지 않았다. ⑥ **CSS 커스텀 속성이 경계를 넘는 것** — 상속되는 속성이므로 넘을 것이 분명한데 **직접 던지지는 않았다.** ⑦ **`ElementInternals`·폼 참여** — 던지지 않았다. ⑧ **접근성 트리에서 슬롯된 내용이 어디에 놓이나** — CDP 로 뜰 수 있었지만 이 편의 과녁이 아니라 **안 떴다.** ⑨ **실제 마우스·키보드 입력에서의 재타기팅** — 합성 이벤트와 `HTMLElement.click()` 까지만 던졌다.

## 용어 풀이

- **섀도 호스트(shadow host)** — 그림자를 매단 요소. `root.host` 가 가리키는 것.
- **섀도 루트(shadow root)** — 그림자 나무의 뿌리. **호스트를 가진 `DocumentFragment`** 이고 `parentNode` 가 `null` 이다.
- **라이트 DOM(light DOM)** — 호스트의 평범한 자식들. 바깥 문서에 그대로 사는 쪽.
- **평탄 트리(flat tree)** — 슬롯 배정을 반영해 **화면에 그려지는 순서로 편** 나무. 상속과 그리기가 이것을 따른다.
- **재타기팅(retargeting)** — 이벤트를 **보는 자리에서 볼 수 있는 가장 가까운 조상**으로 `target` 을 바꾸는 것.
- **`composed`** — 이벤트가 **그림자 경계를 넘을지**. `bubbles` 와 막는 것이 다르다.
- **`composedPath()`** — 이벤트가 지나갈 전체 경로. `open` 이면 **경계 안팎이 같은 배열**을 받는다.
- **`::part` / `exportparts`** — 호스트가 이름을 내준 안쪽 요소를 바깥이 잡는 길 / 그 이름을 **한 겹 더** 내보내는 속성.
- **`:host` / `:host-context`** — 안쪽 시트가 **호스트 자신** / **호스트의 조상 조건**을 보고 잡는 선택자.
- **수동 할당(manual slot assignment)** — `slot` 속성 대신 `slot.assign()` 으로 직접 넣는 모드.
- **`flatten`** — `assignedNodes` 옵션. 슬롯 사슬을 끝까지 따라가 **실제로 그려지는 것**을 준다.
- **부적용인 창** — 「재 봤더니 같았다」가 아니라 **잴 것이 없는** 창. 이 주제에서는 `--dump-dom` 트리가 그렇다.
- **조용한 실패(silent failure)** — 예외도 경고도 없이 아무 일도 안 일어나는 것. 이 주제에서 조용하지 않은 것은 `attachShadow` 의 거절뿐이다.
