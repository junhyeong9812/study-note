# web-api/05 — `DocumentFragment` 와 `<template>` 복제: 일괄 삽입 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 `--dump-dom` 으로 실제로 받은 것**이다. 명령은 블록마다 배너로 실려 있다.\
> 규칙은 [WHATWG DOM Standard](https://dom.spec.whatwg.org/) 와 [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/scripting.html#the-template-element) 로 접지했다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**

**★ 이 주제에는 흔들리는 칸이 있다** — 삽입 비용을 재기 때문이다.

| 안 흔들리는 칸 | 흔들리는 칸 |
|---|---|
| 결과 트리 문자열 · 자식 수 · `ownerDocument` 동일성 · 실행 횟수 · `MutationObserver` 레코드 수 | `performance.now()` 의 **모든 수치** |
| 시간 표의 **자릿수와 순위** — 세 판 모두 같았다 | 같은 자릿수 안의 대소 |

측정 조건 — **한 파일 안에서 9판**을 돌려 **중앙값**을 쓰고 최소·최대를 함께 실었다. 일괄 삽입은 항목 **2000**, 레이아웃을 강제하는 조건은 항목 **400** 이다. 판마다 대상 컨테이너를 비우고 다시 만든다. **결론으로 쓰는 것은 자릿수와 순위뿐**이다.

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 조각을 붙이고 나서 조각을 보면 — 조각이 빈다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa05b-05-frag.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,6p'
DocumentFragment      nodeType = 11   nodeName = #document-fragment   isConnected = false
붙이기 전   frag.childNodes.length = 3   host.children.length = 0
붙인 뒤     frag.childNodes.length = 0   host.children.length = 3
host.innerHTML = <li>가</li><li>나</li><li>다</li>
appendChild(frag) 반환값 === frag = true   반환값.childNodes.length = 0
빈 frag 를 다시 붙이면 host.children.length = 3   (아무 일도 안 한다)
(exit 0)
```

**왜 그런가**

- **`nodeType` 은 11**, `nodeName` 은 `#document-fragment` 다. 요소가 아니라 별도의 노드 종류다.
- **삽입 알고리즘이 조각을 특별 취급한다** — 「넣는 노드가 조각이면 그 자식들을 전부 옮긴다」가 명세의 절차다. 그래서 조각 자신은 트리에 안 들어가고 **빈 채로 남는다**(3 → 0).
- **`appendChild` 의 반환값은 넣은 노드**, 즉 조각 자신이다. 그런데 그 조각은 이미 비었으므로 `back.childNodes.length` 가 **0** 이다. 체이닝해 다시 쓰려던 코드가 여기서 조용히 아무 일도 안 한다.
- **두 번째 `appendChild(frag)` 는 아무 일도 안 한다.** 빈 조각을 넣는 것은 합법이고 에러가 없다. `host.children.length` 는 **3** 그대로다.
- 조각 자신은 트리에 없으므로 `host.querySelector` 로 **찾을 수 없다.** 애초에 조각은 선택자로 지칭할 이름이 없다.

### 2. 같은 셋을 두 경로로 넣으면 — 결과는 같고 사건 수가 다르다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa05b-05-frag.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '8,12p'
조각에 모아 한 번  hostA.innerHTML = <li>가</li><li>나</li><li>다</li>
반복 appendChild   hostB.innerHTML = <li>가</li><li>나</li><li>다</li>
두 문자열이 같은가 = true
childNodes.length  A = 3   B = 3
outerHTML 바이트 길이  A = 50   B = 50   (id 만 다르다)
(exit 0)
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa05b-05-frag.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '14,17p'
조각을 붙였을 때  childList 레코드 = 1개   addedNodes = [3]
반복 appendChild  childList 레코드 = 3개   addedNodes = [1,1,1]
두 결과 트리는 여전히 같은가 = true
A.children.length = 6   B.children.length = 6
(exit 0)
```

**왜 그런가**

- **결과 트리가 문자열 단위로 같다.** `innerHTML` 이 같고 `childNodes.length` 도 같고 `outerHTML` 길이까지 같다 — **결과만 보고는 두 경로를 구분할 수 없다.**
- 갈리는 것은 **트리를 바꾼 횟수**다. `MutationObserver` 가 조각 쪽은 레코드 **1개**(`addedNodes` 가 3), 반복 쪽은 **3개**(각 1)를 받았다.
- ★ 그래서 **조각이 줄이는 것은** 「**삽입 사건의 수**」라고 말해야 한다. 이 수는 **명세가 정한 절차의 결과라 흔들리지 않는다** — 시간보다 단단한 근거다.
- 이 수를 세는 것들이 실제로 있다 — `MutationObserver`(목록의 **37번 주제**) · 커스텀 요소의 연결 반응(목록의 **13번 주제**) · 프레임워크의 변경 감지.

```text
   결과 트리 :  같다        <- 창 ① 과 창 ② 로는 안 갈린다
   사건 수   :  1 대 3      <- MutationObserver 로만 보인다
   시간      :  같은 자릿수 <- 아래 A6
```

### 3. `<template>` 안을 밖에서 찾으면 — 다른 문서라서 안 잡힌다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa05b-05-template.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,7p'
tpl.childNodes.length          = 0   (본 트리에서 template 은 비어 있다)
tpl.content.nodeType           = 11   nodeName = #document-fragment
tpl.content.childNodes.length  = 2
document.querySelector("#tpl li")   = null
document.querySelectorAll(".row")   = 1개  (본 문서에 있는 것만)
tpl.content.querySelectorAll(".row") = 2개
tpl.innerHTML                  = "<li class=\"row\">항목</li><li class=\"row\">항목</li>"
(exit 0)
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa05b-05-template.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '9,15p'
tpl.ownerDocument === document                = true
tpl.content.ownerDocument === document        = false
inner.ownerDocument === document              = false
tpl.content.ownerDocument.defaultView         = null
tpl.content.ownerDocument.documentElement     = null
tpl.content.ownerDocument.URL                 = "about:blank"
inner.isConnected = false   inner.getBoundingClientRect().width = 0
(exit 0)
```

**왜 그런가**

- **`tpl.childNodes.length` 가 0** 이다. 파서가 내용을 `template` 의 자식이 아니라 **`content` 라는 조각**에 넣는다.
- **`document.querySelector('#tpl li')` 는 `null`** 이고 `.row` 는 본 문서의 **1개**만 잡힌다. 조회는 **자기 문서 안**만 본다([02번 주제](../02-element-queries-and-live-collections/2-summary.md)).
- ★ **원인은 한 칸이다** — `tpl.content.ownerDocument === document` 가 **`false`** 다. 명세가 「template contents owner document」라는 **별도의 문서**를 만들라고 정한다.
- 그 문서는 **`defaultView` 가 `null`**(창이 없다), **`documentElement` 가 `null`**(`<html>` 조차 없다), `URL` 이 `about:blank` 다.
- **`--dump-dom` 에는 내용이 보인다** — 직렬화가 `<template>` 태그 안에 내용을 찍기 때문이다.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa05b-05-template.html | sed -n '1,6p'
<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>05-template</title>
<template id="tpl"><li class="row">항목</li><li class="row">항목</li></template>
</head><body><li class="row" id="real">본 문서에 있는 것</li>
<ul id="host"><li class="row">항목</li><li class="row">항목</li></ul>
(exit 0)
```

- **그래서 창 ① 로는 안 갈린다.** 창 ② (`childNodes.length`)도 `tpl` 에 대고 물으면 0 이라 「비었나 보다」로 읽힌다. **창 ④ 가 있어야** 「비어 있는 게 아니라 다른 데 있다」가 보인다.

**찍어 내면 본 문서의 것이 된다**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa05b-05-template.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '17,21p'
cloneNode(true) 한 조각.ownerDocument === document = false
붙인 뒤 host.children.length = 2
붙인 노드.ownerDocument === document = true   isConnected = true
붙인 뒤 document.querySelectorAll(".row") = 3개
tpl.content.childNodes.length = 2   (원본은 안 줄었다)
(exit 0)
```

- 복제본의 `ownerDocument` 는 **아직 다른 문서**인데 붙이는 순간 **입양**되어 `true` 가 된다.
- **원본은 안 줄어든다**(`content.childNodes.length` 가 그대로 2). 틀이 조각과 갈리는 자리가 정확히 여기다.

### 4. 틀 안의 `<script>` 와 `<img>` — 아무것도 안 돈다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa05b-05-inert.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,5p'
같은 마크업을 template 안과 보통 div 안에 하나씩 두었다
파싱이 끝난 시점 script 실행 횟수   template 안 = 0   보통 div 안 = 1
load 뒤 template 안 img   complete = true   naturalWidth = 0   currentSrc = ""
load 뒤 보통 div 안 img   complete = true   naturalWidth = 1   currentSrc 길이 = 78
template 안 script 노드 자체는 있나 = SCRIPT   img 노드 = IMG   (둘 다 트리에 있다)
(exit 0)
```

**왜 그런가**

- **`script` 실행 횟수가 0 대 1** 이다. 같은 마크업인데 자리만 다르다.
- **`img` 는 요청조차 없었다** — `currentSrc` 가 **빈 문자열**이고 `naturalWidth` 가 **0** 이다. 「받다가 실패」가 아니라 「**시작도 안 함**」이다.
- ★ **`complete` 는 `true`** 다. 이 플래그는 「받아졌나」가 아니라 「**할 일이 남았나**」를 답한다. 이것만 보면 정반대로 읽는다.
- **노드는 트리에 있다** — `tpl.content.querySelector('script')` 가 `SCRIPT` 를 돌려준다. 그래서 **창 ①·② 는 「있다」고만 답하고**, 「안 돌았다」는 **전역 실행 계수기(창 ⑤)만** 말한다([04번 주제](../04-textcontent-innerhtml-innertext/2-summary.md)에서 빌려 온 창이다).
- 원인은 A3 의 한 칸이다 — **브라우징 문맥이 없는 문서**에서는 스크립트 준비도 리소스 가져오기도 절차상 일어나지 않는다.

**복제해서 붙이면 돈다**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa05b-05-inert.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '7,11p'
cloneNode(true) 로 복제해 본 문서에 붙인 뒤 (load 까지 기다렸다)
script 실행 횟수 = 1   (붙이기 전에는 0 이었다)
붙인 img   complete = true   naturalWidth = 1   onload 횟수 = 1
붙인 script 의 textContent = "window.C.tplScript++;"
host.children.length = 2   C = {"tplScript":1,"tplImg":1,"plainScript":1,"plainImg":1}
(exit 0)
```

- **`script` 가 0 에서 1** 로, **`img.naturalWidth` 가 0 에서 1** 로 바뀌었다.
- ★ **그래서 `<template>` 은 XSS 방어 수단이 아니다.** 담아 두는 동안만 조용하고 **쓰는 순간 실행된다.**

### 5. 세 가지 복제 — 무엇을 만들고 어디에 두나

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa05b-05-clone.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,6p'
cloneNode(true)        ownerDocument === document = false   childNodes = 2
importNode(content, true)  ownerDocument === document = true   childNodes = 2
importNode(content)        (두 번째 인자 생략)           childNodes = 0
원본 tpl.content.childNodes = 2   (둘 다 원본을 안 건드린다)
둘 다 붙인 뒤 h1.innerHTML === h2.innerHTML = true
붙인 뒤 h1 자식.ownerDocument === document = true   (삽입이 입양을 대신 해 준다)
(exit 0)
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa05b-05-clone.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '8,13p'
다른 문서(iframe)의 노드를 가져온다 — 프레임 안 <p> 수 = 2
importNode(p1, true)   결과.ownerDocument === document = true   원본 p1 은 프레임에 남았나 = true
adoptNode(p2)          결과 === p2 = true   p2.ownerDocument === document = true
adoptNode 뒤 프레임 안 <p> 수 = 1   (원본이 빠졌다)
h3.innerHTML = <p id="p1">프레임 안 문단</p><p id="p2">또 하나</p>
h3 자식 둘의 ownerDocument === document = true, true
(exit 0)
```

**왜 그런가**

| | 새 노드를 만드나 | 결과의 `ownerDocument` | 원본은 |
|---|---|---|---|
| `cloneNode(true)` | 만든다 | **원본과 같은 문서** | 그대로 |
| `importNode(n, true)` | 만든다 | **내 문서** | 그대로 |
| `importNode(n)` | 만든다 | 내 문서 · **얕다**(자식 0) | 그대로 |
| `adoptNode(n)` | **안 만든다** | 내 문서 | **빠진다** |

- **`cloneNode` 는 「node document」를 그대로 쓴다** — 그래서 틀에서 찍은 것은 아직 그 다른 문서 소속이다.
- **`importNode` 는 복사 + 입양**이다. 그런데 **삽입이 입양을 대신 해 주므로**(명세의 pre-insert 가 adopt 를 부른다) 곧바로 붙일 것이면 **결과가 같다** — 실측에서 `h1.innerHTML === h2.innerHTML` 이 `true` 였다.
- ★ **`importNode` 의 두 번째 인자 기본값은 `false`** 다. `cloneNode` 와 달리 자주 빠뜨리는 자리이고, 실측에서 `childNodes` 가 **0** 이었다.
- **`adoptNode` 는 이동**이다 — 프레임 안 `<p>` 수가 2 에서 **1** 로 줄었다.
- **실제로 갈리는 경우**는 「붙이기 전에 그 노드를 만지는 코드가 있을 때」다. 붙이기 전에 `ownerDocument` 를 보거나, 그 문서의 `createElement` 를 쓰거나, 다른 문서의 API 에 넘길 때 갈린다. 만들자마자 붙일 것이면 **둘 중 무엇을 써도 같다.**

### 6. 비용 — 다시 쟀고, 다시 재현되지 않았다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa05b-05-cost.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,10p'
일괄 삽입 — 2000개 항목 · 9판의 중앙값 · 부모가 트리 안

반복 appendChild                        중앙값     2.80 ms   최소     2.60   최대     6.30
DocumentFragment 에 모아 한 번          중앙값     3.20 ms   최소     2.90   최대     4.60
template 복제를 항목마다 붙이기         중앙값     2.40 ms   최소     2.10   최대     3.40
template 복제를 조각에 모아 한 번       중앙값     2.70 ms   최소     2.40   최대     3.20

같은 것을 부모가 트리 밖(detached)일 때
반복 appendChild (트리 밖 부모)         중앙값     2.30 ms   최소     2.10   최대     3.80
DocumentFragment (트리 밖 부모)         중앙값     2.70 ms   최소     2.30   최대     3.50
(exit 0)
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa05b-05-cost.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '12,19p'
삽입 사이에 레이아웃이 도는 조건 — 400개 항목 · 9판의 중앙값
   (항목을 넣을 때마다 host.offsetHeight 를 읽어 레이아웃을 강제한다)

반복 appendChild + 매번 offsetHeight    중앙값    34.70 ms   최소    33.60   최대    95.70
조각에 모아 한 번 + 끝에 한 번만        중앙값     6.20 ms   최소     5.80   최대    10.50
반복 appendChild + 끝에 한 번만         중앙값     6.80 ms   최소     5.80   최대    11.40

sink = true   (읽은 값을 버리지 않았다는 확인)
(exit 0)
```

**왜 그런가**

- **앞의 네 방식이 전부 같은 자릿수**(`\~3 ms` 대)다. 세 판을 돌렸더니 **순위가 판마다 뒤집혔다** — 신호가 잡음보다 작다.
- **부모가 트리 밖일 때도 안 갈렸다.** [04번 주제](../04-textcontent-innerhtml-innertext/2-summary.md)가 「조각이 이기는 조건을 못 찾았다」고 적어 둔 후보를 실제로 던져 본 것인데 **여기서도 아니었다.**
- ★ **갈린 것은 세 번째 조건**이다 — 삽입 사이에 `offsetHeight` 를 읽으면 `\~40\~50 ms` 로 **한 자릿수 커진다.**
- ★★ **그런데 원인은 삽입 횟수가 아니다.** 「반복 삽입 + 끝에 한 번만 읽기」가 **「조각 + 끝에 한 번만 읽기」와 같은 시간**이었다. 삽입을 400번 한 쪽과 1번 한 쪽이 같다는 뜻이다. **비싼 것은 읽기·쓰기 교차**다(목록의 **10번 주제**).
- 그래서 이 문서는 **「조각을 쓰면 빨라진다」를 주장하지 않는다.** 조각에 대해 주장하는 것은 A2 의 **사건 수 1 대 3** 뿐이다.
- `performance.now()` 는 **100마이크로초**로 뭉개지지만, 이 표의 칸은 전부 그 위라 분해능이 문제되지 않았다.

### 7. 틀이 안 도는 이유 — 원인은 하나다

**출력** — A3·A4 의 블록이 근거다. 핵심 칸만 다시 인용한다.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa05b-05-template.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '9,15p'
tpl.ownerDocument === document                = true
tpl.content.ownerDocument === document        = false
inner.ownerDocument === document              = false
tpl.content.ownerDocument.defaultView         = null
tpl.content.ownerDocument.documentElement     = null
tpl.content.ownerDocument.URL                 = "about:blank"
inner.isConnected = false   inner.getBoundingClientRect().width = 0
(exit 0)
```

**왜 그런가**

- ★ **같은 원인이다.** `<script>` 가 안 돈 것도 `<img>` 가 요청을 안 한 것도 **그 노드들이 브라우징 문맥 없는 문서에 있기 때문**이다.
- 한 문장으로 — **「`template.content` 는 창이 없는 별도의 문서에 살고, 창이 없으면 스크립트도 리소스 요청도 절차상 시작되지 않는다」.**
- **`display: none` 인 `<div>` 안의 `<script>` 는 돈다.** 그쪽은 **본 문서에 있고** 단지 렌더가 안 될 뿐이다. 둘은 「안 보인다」가 같을 뿐 **소속 문서가 다르다.** 실측의 「보통 div」 줄이 그 대조군이다(`script` 1회 · `img` `naturalWidth` 1).
- **XSS 방어에 쓰면 안 되는 이유**는 A4 의 두 번째 블록이다 — 복제해 붙이자 **`script` 가 돌았고 `img` 가 받아졌다.** 방어는 [04번 주제](../04-textcontent-innerhtml-innertext/2-summary.md)의 결론대로 **문자열을 마크업으로 안 넣는 것**이다.

### 8. 04번과 결과가 반대인 자리 — 준비 단계를 지났느냐

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa05b-05-inert.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '7,11p'
cloneNode(true) 로 복제해 본 문서에 붙인 뒤 (load 까지 기다렸다)
script 실행 횟수 = 1   (붙이기 전에는 0 이었다)
붙인 img   complete = true   naturalWidth = 1   onload 횟수 = 1
붙인 script 의 textContent = "window.C.tplScript++;"
host.children.length = 2   C = {"tplScript":1,"tplImg":1,"plainScript":1,"plainImg":1}
(exit 0)
```

**왜 그런가**

- **갈린 것은 「이미 시작된(already started)」 표시**다. 명세는 `script` 요소에 그 플래그를 두고, 복제할 때 **그 플래그까지 복사**하라고 정한다.
- **그 표시는 「준비(prepare) 절차를 밟았을 때」 찍힌다.** 본 문서에서 파서가 만든 `script` 는 그 자리에서 준비를 밟으므로 표시가 찍히고, 그래서 [04번 주제](../04-textcontent-innerhtml-innertext/2-summary.md)의 실측처럼 **자리를 옮겨도 다시 안 돈다.**
- **틀 안의 `script` 는 준비를 밟은 적이 없다** — 창이 없는 문서라 그 절차가 시작되지 않았다. 그래서 표시가 없고, 복제본을 본 문서에 붙이면 **그때 처음 준비되어 돈다.**
- **`createElement('script')` 로 만든 것도 같다** — 준비된 적이 없으므로 붙이면 돈다. [04번 주제](../04-textcontent-innerhtml-innertext/2-summary.md)가 그것을 실측해 두었다.
- 하나의 규칙으로 — **「`script` 가 도는가는 「어디에 있나」가 아니라 「준비를 밟았나」가 정한다.」**

### 9. 조각과 틀을 언제 안 쓰나 — 「몇 번 쓸 것인가」

**출력** — A1 과 A3 의 마지막 줄이 근거다.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa05b-05-template.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '17,21p'
cloneNode(true) 한 조각.ownerDocument === document = false
붙인 뒤 host.children.length = 2
붙인 노드.ownerDocument === document = true   isConnected = true
붙인 뒤 document.querySelectorAll(".row") = 3개
tpl.content.childNodes.length = 2   (원본은 안 줄었다)
(exit 0)
```

**왜 그런가**

- **한 번만 쓸 묶음에 틀을 쓰면** 마크업에 `<template>` 을 두고 `content` 를 복제하는 두 단계가 늘어난다. 조각은 그 자리에서 만들고 버리면 된다.
- **여러 번 찍을 것에 조각을 쓰면 첫 판만 동작한다.** 조각은 넣으면 비기 때문이다(A1).
- **`host.appendChild(tpl.content)` 가 첫 렌더에서는 잘 되는** 이유도 같다 — 그 한 번은 내용이 **실제로 들어간다.** 비는 것은 **그 다음**이라 재렌더에서야 드러난다. 그래서 **가장 조용한 사고**다.
- **조각을 비우지 않고 자식만 넘기려면** 먼저 배열로 뜬다 — `const kids = [...frag.children]`. 다만 **삽입은 여전히 이동**이므로 붙이는 순간 조각에서는 빠진다([03번 주제](../03-node-creation-insertion-removal/2-summary.md)). 원본을 남기려면 **틀을 쓰거나 복제**해야 한다.

### 10. 다른 주제와 잇기

**출력** — A1 의 블록이 첫 물음의 근거다.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa05b-05-frag.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,6p'
DocumentFragment      nodeType = 11   nodeName = #document-fragment   isConnected = false
붙이기 전   frag.childNodes.length = 3   host.children.length = 0
붙인 뒤     frag.childNodes.length = 0   host.children.length = 3
host.innerHTML = <li>가</li><li>나</li><li>다</li>
appendChild(frag) 반환값 === frag = true   반환값.childNodes.length = 0
빈 frag 를 다시 붙이면 host.children.length = 3   (아무 일도 안 한다)
(exit 0)
```

**왜 그런가**

- **[03번 주제](../03-node-creation-insertion-removal/2-summary.md)의 「삽입은 이동」이 조각에도 그대로 적용된다.** 조각의 자식들이 **조각에서 빠져** 새 부모로 간다 — 그래서 조각이 빈다. 별도의 규칙이 아니라 같은 규칙의 결과다.
- **[02번 주제](../02-element-queries-and-live-collections/2-summary.md)의 조회 범위 규칙**으로 A3 이 설명된다 — `document.querySelector` 는 **그 문서의 트리**를 본다. 틀 안은 다른 문서이므로 범위 밖이다. 「선택자가 틀렸나」를 의심할 일이 아니다.
- **목록의 10번 주제(레이아웃 스래싱)가 미리 드러난 자리**는 A6 의 세 번째 조건이다. 삽입 400번과 1번의 시간이 같고 **읽기를 섞은 쪽만 한 자릿수 컸다** — 그 주제의 씨앗이 여기서 이미 보인다.
- **목록의 37번 주제(`MutationObserver`)를 근거로 쓴 이유**는 **그 수가 안 흔들리기 때문**이다. 시간은 판마다 뒤집히는데 레코드 수는 1 대 3 으로 고정이다. 「조각이 무엇을 줄이나」를 **날조 없이 말할 수 있는 유일한 창**이었다.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless. **엔진은 이것 하나다.** **크로스 브라우저 이식성은 이 문서의 주장 범위 밖**이다.

**측정 조건** — 도구는 **`performance.now()`** 하나(벤치마크 하네스가 아니다) · 머신은 이 Linux 한 대 · **판 수 9** · **중앙값**을 쓰고 최소·최대를 함께 실었다 · 일괄 삽입은 항목 **2000**, 레이아웃 강제 조건은 항목 **400** · 판마다 컨테이너를 비우고 다시 만든다.\
**재현되는 것은 자릿수와 순위**다. 절댓값은 재현되지 않는다 — **세 판을 비교해 확인했다.**\
**신호 대 잡음** — 일괄 삽입 네 줄은 **같은 자릿수 안에서 순위가 판마다 뒤집혔다**(신호가 잡음보다 작다). 레이아웃 강제 조건은 **한 자릿수 차이**라 신호가 압도적이다. **그래서 뒤엣것만 결론으로 쓴다.**

**하네스** — 01\~04 네 주제와 같은 것을 쓴다. 블록은 `capture.sh` 가 전부 파일로 받았고 사람이 옮겨 적지 않았다.

```bash
# 블록 하나를 다시 던지는 법
google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa05b-05-frag.html \
  | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
```

```js
// 이 주제의 창 ④ — 이 노드가 '어느 문서' 소속인가
n.ownerDocument === document
// 창 ⑤ (04번에서 빌림) — '트리에 있나' 가 아니라 '돌았나'
window.C = {tplScript: 0, tplImg: 0, plainScript: 0, plainImg: 0};
// 조각이 줄이는 것을 세는 창 — 시간과 달리 흔들리지 않는다
new MutationObserver(rs => { for (const r of rs) rec.push(r.addedNodes.length); }).observe(host, {childList: true});
```

★ **`--virtual-time-budget` 은 쓰지 않았다**(이 갈래의 정본 규칙). 틀 안의 실행 실험은 `load` 이벤트 뒤 `setTimeout(…, 0)` 에서 결과를 찍는다.\
★ **`--dump-dom` 은 `load` + `setTimeout(…, 0)` 까지만 기다린다.** 그 뒤에 한 턴을 더 두면 **출력이 통째로 사라진다** — 이 주제의 실험 하나가 실제로 그래서 빈 출력을 냈고, 복제·삽입을 `load` **전으로** 옮겨 고쳤다.

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| 조각의 `nodeType`·비는 것·반환값·두 번 붙이기 | 2 | 동작 방식 (1) · A1 |
| 두 경로의 결과 트리 대조 + `MutationObserver` 레코드 수 | 2 | 동작 방식 (2) · A2 |
| `<template>` 의 조회·`ownerDocument`·`defaultView`·직렬화 | 3 | 동작 방식 (3) · A3 · A7 |
| 틀 안 `script`·`img` 의 **실행 횟수와 요청 여부** | 3 | 동작 방식 (4) · A4 · A7 |
| 복제본을 붙인 뒤의 실행 횟수 | 3 | 동작 방식 (4) · A4 · A8 |
| `cloneNode`·`importNode`·`adoptNode` 의 소속과 원본 | 2 | 동작 방식 (5) · A5 |
| **일괄 삽입 6방식 × 9판** 중앙값·최소·최대 | 3 | 동작 방식 (6) · A6 |
| **레이아웃 강제 3조건 × 9판** 중앙값·최소·최대 | 3 | 동작 방식 (6) · A6 |
| `demo` 블록을 래퍼에 띄워 초기 상태·버튼 3회·바꿔 볼 것 2종 확인 | 1 | 동작 방식 (6)의 demo |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| **모든 시간 수치** | 위 표 | 판마다 흔들린다. **자릿수와 순위만 결론으로 쓴다** |
| `performance.now()` 의 분해능 | 100마이크로초 | Blink 의 정책이고 명세가 정한 값이 아니다 |
| 조각이 안 빨랐던 것 | 같은 자릿수·순위 뒤집힘 | **이 조건에서의 관찰**이다. 일반 규칙으로 읽지 않는다 |
| 직렬화 형태(`--dump-dom` 의 줄바꿈·속성 순서) | 위 출력 | 명세 + 구현 |
| `template.content.ownerDocument.URL` 이 `about:blank` 인 것 | 위 출력 | 명세가 URL 문자열을 못 박지는 않는다 |

**안 돌려 본 것** — ① Firefox·Safari 에서의 재현(엔진이 없다). ② **선언적 Shadow DOM**(`<template shadowrootmode>`)에서 `content` 가 어떻게 되는지(목록의 **12번 주제**의 몫). ③ 틀 안의 `<iframe>`·`<link>`·`<video>` 가 어떻게 구는지 — `script` 와 `img` 둘만 쟀다. **「리소스 전부가 그렇다」로 일반화하지 않는다.** ④ 커스텀 요소가 틀 안에서 업그레이드되는지(목록의 **13번 주제**). ⑤ **조각이 이기는 조건** — 04번에 이어 두 번째로 못 찾았다. **「효과가 없다」가 아니라 「이 조건들에서는 잡음 아래였다」로 적는다.**

## 용어 풀이

- **`DocumentFragment`** — 부모 없는 임시 노드 자루. `nodeType` 11. 삽입하면 자식들만 옮겨 가고 자신은 빈다.
- **`<template>`** — 파서가 만들되 내용을 본 트리에 넣지 않는 요소. 내용은 `content` 안에 있다.
- **template contents owner document** — `template.content` 가 소속된 별도의 문서. 명세가 이름 붙인 것이다.
- **브라우징 문맥(browsing context)** — 문서를 띄우는 창·프레임. 없으면 스크립트도 리소스 요청도 없다.
- **「이미 시작된」 표시(already started)** — `script` 요소에 찍히는 플래그. **준비 절차를 밟으면** 찍히고 복제에 따라온다.
- **준비(prepare)** — `script` 를 실제로 돌릴지 정하는 명세의 절차. 이것을 밟아야 표시가 찍힌다.
- **입양(adopt)** — 노드의 소속 문서를 바꾸는 절차. 삽입이 자동으로 불러 준다.
- **`importNode`** — 복사 + 입양. 두 번째 인자를 안 주면 얕다.
- **`adoptNode`** — 복사 없이 소속만 바꾼다. 원본이 원래 자리에서 빠진다.
- **`MutationObserver`** — 트리 변경을 레코드로 모아 알려 주는 관찰자.
- **`complete`(이미지)** — 「할 일이 남았나」를 답하는 플래그. 「받아졌나」가 아니다.
- **분해능(resolution)** — 측정 도구가 구분할 수 있는 최소 간격. 여기서는 100마이크로초.
- **중앙값(median)** — 여러 판을 크기순으로 늘어놓았을 때 가운데 값.
