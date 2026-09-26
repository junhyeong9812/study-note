# html/syntax/10 — `template`·`slot`·선언적 Shadow DOM·커스텀 요소 맛보기 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 돌려** 읽은 것이다. 하네스는 맨 아래 `## 실행 검증` 절에 있다.\
> 규칙은 [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 와 [WHATWG DOM Standard](https://dom.spec.whatwg.org/) 로 접지했다.\
> ★ **엔진은 Chrome 하나다** — 이 갈래는 이식성을 주장하지 않는다. **선언적 Shadow DOM 은 이 묶음에서 가장 새 표면**이라 특히 그렇다.
> ★★★ **이 주제에는 도구 한계가 있다** — `--dump-dom` 은 **섀도 트리를 못 본다**(A3). 그 자리에서는 창 ②로 갈아탔다.
> ★ **경계** — Shadow DOM·커스텀 요소의 **API** 는 web-api 갈래 목록([`web-api/README.md`](../../../../web-api/README.md))의 **12번**·**13번**이 정본이다(A10).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 아무것도 안 산다 — 그리고 이미지를 받아 오지도 않는다

**출력** (Chrome 151 headless, 로컬 HTTP 서버 위)

```text
===== 소스: html09b-template-inert.html =====
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>template 안은 살아 있지 않다</title>
<script src="html09b-probe.js"></script>
</head>
<body>
<img src="html09b-dot.gif?out">
<script>P("밖의 스크립트가 돌았다");</script>
<style>#표식 { color: rgb(120, 120, 120); }</style>
<p id="표식">밖의 p</p>

<template id="틀">
  <img src="html09b-dot.gif?in">
  <script>window.P("★ 틀 안의 스크립트가 돌았다 ★");</script>
  <style>#표식 { color: rgb(220, 220, 220); }</style>
  <p id="표식">틀 안의 p</p>
</template>

<script>
window.__끝 = function () {
  P("문서의 <img> 개수      = " + document.querySelectorAll("img").length);
  P("문서의 <p> 개수        = " + document.querySelectorAll("p").length);
  P("getElementById('표식') = " + document.getElementById("표식").textContent);
  P("표식의 계산값 color    = " + getComputedStyle(document.getElementById("표식")).color);
  P("document.styleSheets.length = " + document.styleSheets.length);
  const t = document.getElementById("틀");
  P("틀.childNodes.length         = " + t.childNodes.length);
  P("틀.content.childNodes.length = " + t.content.childNodes.length);
  P("틀.content.constructor.name  = " + t.content.constructor.name);
  P("틀.content.ownerDocument === document ? " + (t.content.ownerDocument === document));
  const 안img = t.content.querySelector("img");
  P("틀 안 img.complete = " + 안img.complete + "   naturalWidth = " + 안img.naturalWidth);
};
</script>
</body>
</html>
===== dom http://127.0.0.1:18709/html09b-template-inert.html | probe =====
밖의 스크립트가 돌았다
문서의 <img> 개수      = 1
문서의 <p> 개수        = 1
getElementById('표식') = 밖의 p
표식의 계산값 color    = rgb(120, 120, 120)
document.styleSheets.length = 1
틀.childNodes.length         = 0
틀.content.childNodes.length = 9
틀.content.constructor.name  = DocumentFragment
틀.content.ownerDocument === document ? false
틀 안 img.complete = true   naturalWidth = 0
(exit 0)
```

**같은 한 판이 서버에 낸 요청**

```text
===== 이 한 판이 서버에 낸 요청 (grep -o '^/html09b-[^ ]*' srv.log | sort | uniq -c) =====
      1 /html09b-dot.gif?out
      1 /html09b-probe.js
      1 /html09b-template-inert.html
(exit 0)
```

**왜 그런가**

- **틀 안의 스크립트가 안 돌았다** — 로그에 그 줄이 없다.
- **`<img>` 1개 · `<p>` 1개 · `styleSheets.length = 1`** — 전부 **바깥 것 하나씩**이다.
- **`#표식` 의 색이 `rgb(120, 120, 120)`** — 바깥 `<style>` 의 값이다. 틀 안의 `<style>` 은 **안 먹었다.**
- **`틀.childNodes.length = 0` · `content.childNodes.length = 9`** — 내용은 `<template>` 의 **자식이 아니다.**
- ★★★ **`content.ownerDocument === document` 가 `false`** 다. 내용이 **다른 문서에 산다** — 이것이 나머지 전부의 이유다.
- **틀 안 `<img>` 는 `complete = true`·`naturalWidth = 0`** — 「다 받았다」가 아니라 **시작도 안 했다**는 뜻이다.
- ★★★ **요청 로그에 `?out` 만 있고 `?in` 이 없다.** 「안 그렸다」가 아니라 **안 받았다.**

### 2. 덤프에는 보인다 — 「덤프에 있다」와 「문서에 있다」는 다른 말이다

**출력**

```text
===== 소스: html09b-template-tree.html =====
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>template 은 덤프에 어떻게 보이나</title>
</head>
<body>
<p>밖</p>
<template id="틀"><p>안</p><td>표 밖의 td</td></template>
<table><template><tr><td>표 안의 틀</td></tr></template></table>
</body>
</html>
===== dom http://127.0.0.1:18709/html09b-template-tree.html =====
<!DOCTYPE html>
<html lang="ko"><head>
<meta charset="utf-8">
<title>template 은 덤프에 어떻게 보이나</title>
</head>
<body>
<p>밖</p>
<template id="틀"><p>안</p>표 밖의 td</template>
<table><template><tr><td>표 안의 틀</td></tr></template></table>


</body></html>
(exit 0)
```

**왜 그런가**

- ★★ **`<p>안</p>` 이 덤프에 있다.** 직렬화 알고리즘이 `<template>` 만 특별히 **`content` 를 대신 직렬화**하기 때문이다.
- **표 밖의 `<td>` 는 태그가 버려지고 글자만 남았다**(`표 밖의 td`) — `<template>` 안도 **파서의 삽입 모드**를 그대로 받는다([03번 주제](../03-parser-and-error-recovery/2-summary.md)).
- **표 안의 `<template>` 에서는 `<tr><td>` 가 살아남았다** — 같은 태그가 **어디 있느냐로 갈린다.**
- ★★★ **A1 의 `querySelectorAll` 과 여기 덤프가 어긋난다.** 창 ①은 **직렬화된 글자**를 보여 주고, `querySelectorAll` 은 **문서 트리**를 본다. **둘은 같은 것이 아니다.**

### 3. 된다 · `<template>` 이 사라진다 · 그런데 그림자는 덤프에 없다

**출력**

```text
===== 소스: html09b-dsd-tree.html =====
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>선언적 Shadow DOM 이 덤프에 보이나</title>
</head>
<body>
<my-card>
  <template shadowrootmode="open">
    <style>p { color: rgb(130, 130, 130); }</style>
    <p>그림자 안의 p</p>
    <slot></slot>
  </template>
  <span>라이트 DOM 의 span</span>
</my-card>
<my-closed>
  <template shadowrootmode="closed"><p>닫힌 그림자</p></template>
</my-closed>
<my-bad>
  <template shadowrootmode="zzznope"><p>모르는 값</p></template>
</my-bad>
</body>
</html>
===== dom http://127.0.0.1:18709/html09b-dsd-tree.html =====
<!DOCTYPE html>
<html lang="ko"><head>
<meta charset="utf-8">
<title>선언적 Shadow DOM 이 덤프에 보이나</title>
</head>
<body>
<my-card>
  
  <span>라이트 DOM 의 span</span>
</my-card>
<my-closed>
  
</my-closed>
<my-bad>
  <template shadowrootmode="zzznope"><p>모르는 값</p></template>
</my-bad>


</body></html>
(exit 0)
```

**콘솔**

```text
===== google-chrome --headless --disable-gpu --no-sandbox --enable-logging=stderr \
  --dump-dom http://127.0.0.1:18709/html09b-dsd-tree.html 2>&1 >/dev/null \
  | grep ':CONSOLE:' | sed 's/^\[[0-9:/.]*INFO:CONSOLE:[0-9]*\] //' | sort =====
"Invalid declarative shadowrootmode attribute value. Valid values are "open" and "closed".", source: http://127.0.0.1:18709/html09b-dsd-tree.html (20)
(exit 0)
```

**왜 그런가**

- ★★★ **된다.** Chrome 151 에서 선언적 Shadow DOM 이 동작한다.
- **`open`·`closed` 는 `<template>` 이 사라졌다** — 파서가 그것을 먹어 **섀도 루트로 바꿔 놓았다.**
- **모르는 값(`zzznope`)만 `<template>` 이 그대로 남았다.**
- ★★★ **그림자 안의 `<p>` 가 덤프에 하나도 없다.** `--dump-dom` 은 `outerHTML` 이고, **`outerHTML` 은 섀도 트리를 직렬화하지 않는다.** 덤프만 보면 `my-card` 가 **빈 것처럼** 보인다.
- **콘솔에 한 줄** — 잘못된 `shadowrootmode` 를 썼다는 사실이 거기에만 남는다. ★ **경고도 출력이다.**

### 4. `open` 만 준다 · 직렬화는 기본이 「안 보임」이다

**출력**

```text
===== 소스: html09b-dsd-probe.html =====
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>선언적 Shadow DOM — 프로브</title>
<script src="html09b-probe.js"></script>
</head>
<body>
<my-card><template shadowrootmode="open"><p>그림자안p</p><slot></slot></template><span>라이트 span</span></my-card>
<my-closed><template shadowrootmode="closed"><p>닫힌그림자</p></template></my-closed>
<my-bad><template shadowrootmode="zzznope"><p>모르는값</p></template></my-bad>
<my-ser><template shadowrootmode="open" shadowrootserializable><p>직렬화허용</p></template></my-ser>
<script>
window.__끝 = function () {
  const 바늘 = 함침 => 함침[0] + 함침[1];
  const 열림 = document.querySelector("my-card");
  const 닫힘 = document.querySelector("my-closed");
  const 잘못 = document.querySelector("my-bad");
  const 직렬 = document.querySelector("my-ser");
  P("my-card.shadowRoot             = " + (열림.shadowRoot ? "ShadowRoot(mode=" + 열림.shadowRoot.mode + ")" : "null"));
  P("my-card 안의 <template> 개수   = " + 열림.querySelectorAll("template").length);
  P("my-card.childNodes             = " + [...열림.childNodes].map(n => n.nodeName).join(" "));
  P("my-card.shadowRoot.innerHTML   = " + 열림.shadowRoot.innerHTML);
  P("my-closed.shadowRoot           = " + (닫힘.shadowRoot ? "있음" : "null") + "   <- closed 는 스크립트에도 안 준다");
  P("my-closed 안의 <template> 개수 = " + 닫힘.querySelectorAll("template").length);
  P("my-bad.shadowRoot              = " + (잘못.shadowRoot ? "있음" : "null"));
  P("my-bad 안의 <template> 개수    = " + 잘못.querySelectorAll("template").length + "   <- 모르는 값이면 평범한 template 으로 남는다");
  P("--- 직렬화: 그림자를 글자로 다시 뽑을 수 있나 ---");
  P("열림.outerHTML 에 그림자가       = " + (열림.outerHTML.includes(바늘(["그림자", "안p"])) ? "보인다" : "안 보인다"));
  P("열림.getHTML() 기본값에          = " + (열림.getHTML().includes(바늘(["그림자", "안p"])) ? "보인다" : "안 보인다"));
  P("열림.getHTML({serializableShadowRoots:true}) 에 = "
    + (열림.getHTML({serializableShadowRoots: true}).includes(바늘(["그림자", "안p"])) ? "보인다" : "안 보인다")
    + "   <- shadowrootserializable 이 없다");
  P("직렬.getHTML({serializableShadowRoots:true}) 에 = "
    + (직렬.getHTML({serializableShadowRoots: true}).includes(바늘(["직렬화", "허용"])) ? "보인다" : "안 보인다")
    + "   <- shadowrootserializable 이 있다");
};
</script>
</body>
</html>
===== dom http://127.0.0.1:18709/html09b-dsd-probe.html | probe =====
my-card.shadowRoot             = ShadowRoot(mode=open)
my-card 안의 <template> 개수   = 0
my-card.childNodes             = SPAN
my-card.shadowRoot.innerHTML   = <p>그림자안p</p><slot></slot>
my-closed.shadowRoot           = null   <- closed 는 스크립트에도 안 준다
my-closed 안의 <template> 개수 = 0
my-bad.shadowRoot              = null
my-bad 안의 <template> 개수    = 1   <- 모르는 값이면 평범한 template 으로 남는다
--- 직렬화: 그림자를 글자로 다시 뽑을 수 있나 ---
열림.outerHTML 에 그림자가       = 안 보인다
열림.getHTML() 기본값에          = 안 보인다
열림.getHTML({serializableShadowRoots:true}) 에 = 안 보인다   <- shadowrootserializable 이 없다
직렬.getHTML({serializableShadowRoots:true}) 에 = 보인다   <- shadowrootserializable 이 있다
(exit 0)
```

**왜 그런가**

- **`my-card.shadowRoot` 가 `ShadowRoot(mode=open)`** 이고 `innerHTML` 로 안을 읽을 수 있다.
- ★★ **`my-closed.shadowRoot` 가 `null`** 이다 — 선언적으로 만든 닫힌 그림자는 **페이지 스크립트가 다시 잡을 방법이 없다.** 그런데 `<template>` 은 **사라졌다**(개수 0) — 즉 **만들어지긴 했다.**
- **`my-bad.shadowRoot` 가 `null` 이고 `<template>` 이 1개 남았다** — 아예 안 만들어졌다.
- ★★★ **`outerHTML` 도 `getHTML()` 도 「안 보인다」이고, `getHTML({serializableShadowRoots: true})` 조차 「안 보인다」다.** `shadowrootserializable` 을 붙인 `my-ser` 에서만 「**보인다**」가 나왔다.
- **왜 기본이 「안 보임」인가** — 섀도는 **캡슐화**가 목적이다. 아무나 `innerHTML` 로 안을 꺼내 가면 그 목적이 깨지므로, **마크업이 명시적으로 허락**해야 뽑힌다.

### 5. 채워진 칸은 기본을 안 쓰고, 이름이 틀린 것은 사라진다

**출력**

```text
===== 소스: html09b-slot.html =====
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>slot 의 기본 내용</title>
<script src="html09b-probe.js"></script>
</head>
<body>
<my-box id="채움">
  <template shadowrootmode="open">
    <slot name="제목"><h2>기본 제목</h2></slot>
    <slot><p>기본 본문</p></slot>
    <slot name="없는칸"><p>아무도 안 채우는 칸</p></slot>
  </template>
  <h2 slot="제목">바깥이 준 제목</h2>
  <p>바깥이 준 본문</p>
  <p slot="오타">슬롯 이름이 틀린 것</p>
</my-box>
<script>
window.__끝 = function () {
  const 그 = document.getElementById("채움").shadowRoot;
  for (const s of 그.querySelectorAll("slot")) {
    const 할당 = s.assignedNodes().filter(n => n.nodeType === 1 || n.textContent.trim());
    P(("slot name=" + JSON.stringify(s.name)).padEnd(22)
      + "assignedNodes(요소만) = [" + 할당.map(n => n.nodeName + "「" + n.textContent.trim() + "」").join(", ") + "]");
    P("   -> 화면에 실제로 나오는 것: "
      + (할당.length ? 할당.map(n => n.textContent.trim()).join(" / ")
                     : "기본 내용 「" + s.textContent.trim() + "」"));
  }
  const 오타 = document.querySelector('[slot="오타"]');
  P('slot="오타" 인 요소의 assignedSlot = ' + 오타.assignedSlot);
  P("   -> 이름이 안 맞으면 어느 칸에도 안 들어가고 화면에서 사라진다");
  const 호스트 = document.getElementById("채움");
  P("--- 창 ③ 렌더 대 트리 ---");
  P("호스트.textContent (트리)  = " + JSON.stringify(호스트.textContent.replace(/\s+/g, " ").trim()));
  P("호스트.innerText  (렌더)   = " + JSON.stringify(호스트.innerText));
  P("document.body.innerText    = " + JSON.stringify(document.body.innerText));
  P("   -> innerText 는 그림자 안을 못 본다. 「기본 내용이 화면에 있나」는 좌표로 따로 재야 한다");
  P("--- 기본 내용이 진짜 그려졌나: 상자 높이 ---");
  for (const s2 of 그.querySelectorAll("slot")) {
    const 기본 = s2.firstElementChild;
    P(("slot name=" + JSON.stringify(s2.name)).padEnd(22)
      + "기본 내용 " + (기본 ? "<" + 기본.nodeName.toLowerCase() + "> 높이 = "
        + (기본.getBoundingClientRect().height > 0 ? "0 보다 큼 (그려졌다)" : "0 (안 그려졌다)") : "없음"));
  }
};
</script>
</body>
</html>
===== dom http://127.0.0.1:18709/html09b-slot.html | probe =====
slot name="제목"        assignedNodes(요소만) = [H2「바깥이 준 제목」]
   -> 화면에 실제로 나오는 것: 바깥이 준 제목
slot name=""          assignedNodes(요소만) = [P「바깥이 준 본문」]
   -> 화면에 실제로 나오는 것: 바깥이 준 본문
slot name="없는칸"       assignedNodes(요소만) = []
   -> 화면에 실제로 나오는 것: 기본 내용 「아무도 안 채우는 칸」
slot="오타" 인 요소의 assignedSlot = null
   -> 이름이 안 맞으면 어느 칸에도 안 들어가고 화면에서 사라진다
--- 창 ③ 렌더 대 트리 ---
호스트.textContent (트리)  = "바깥이 준 제목 바깥이 준 본문 슬롯 이름이 틀린 것"
호스트.innerText  (렌더)   = "바깥이 준 제목\n\n바깥이 준 본문"
document.body.innerText    = "바깥이 준 제목\n\n바깥이 준 본문"
   -> innerText 는 그림자 안을 못 본다. 「기본 내용이 화면에 있나」는 좌표로 따로 재야 한다
--- 기본 내용이 진짜 그려졌나: 상자 높이 ---
slot name="제목"        기본 내용 <h2> 높이 = 0 (안 그려졌다)
slot name=""          기본 내용 <p> 높이 = 0 (안 그려졌다)
slot name="없는칸"       기본 내용 <p> 높이 = 0 보다 큼 (그려졌다)
(exit 0)
```

**왜 그런가**

- **`slot="제목"` 의 `<h2>` 가 이름 있는 칸에** 들어갔다. **채워진 칸은 기본 내용을 안 쓴다.**
- **`slot` 속성이 없는 `<p>` 가 이름 없는 칸에** 들어갔다.
- **아무도 안 채운 `없는칸` 만 기본 내용**이 나왔다.
- ★★★ **`slot="오타"` 의 `assignedSlot` 이 `null`** 이다 — 어느 칸에도 안 들어가고 **화면에서 사라진다.** **예외도 경고도 없다.**
- ★★ **`textContent` 에는 「슬롯 이름이 틀린 것」이 들어 있는데 `innerText` 에는 없다.** 창 ③(렌더 대 트리)이 여기서 갈린다.
- ★★★ **그런데 `innerText` 에는 기본 내용도 없다.** Chrome 151 의 `innerText` 는 **그림자 안을 안 본다.** 그래서 「진짜 그려졌나」는 **상자 높이로 따로 쟀고**, 아무도 안 채운 칸만 **`0 보다 큼`** 이었다.
- ★ **한 관찰로 두 질문에 답하지 않는다** — 「할당됐나」는 `assignedNodes()` 가, 「그려졌나」는 **좌표**가 답한다.

### 6. 대시가 이름을 가르고, `define` 이 업그레이드를 일으킨다

**출력**

```text
===== 소스: html09b-custom.html =====
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>커스텀 요소의 업그레이드 시점</title>
<script src="html09b-probe.js"></script>
</head>
<body>
<my-clock id="먼저">파서가 먼저 만든 것</my-clock>
<plain-tag id="정의없음">정의가 없는 대시 이름</plain-tag>
<nodash id="대시없음">대시가 없는 이름</nodash>
<script>
P("define 전  #먼저      = " + document.getElementById("먼저").constructor.name);
P("define 전  #정의없음  = " + document.getElementById("정의없음").constructor.name);
P("define 전  #대시없음  = " + document.getElementById("대시없음").constructor.name);
class 시계 extends HTMLElement {
  constructor() { super(); window.P("   constructor 가 불렸다: " + this.id); }
  connectedCallback() { window.P("   connectedCallback 이 불렸다: " + this.id); }
}
customElements.define("my-clock", 시계);
P("define 후  #먼저      = " + document.getElementById("먼저").constructor.name);
const 나중 = document.createElement("my-clock");
나중.id = "나중";
document.body.appendChild(나중);
window.__끝 = function () {
  P("맨 끝      #먼저      = " + document.getElementById("먼저").constructor.name);
  P("맨 끝      #나중      = " + document.getElementById("나중").constructor.name);
  P("customElements.get('my-clock')   = " + (customElements.get("my-clock") ? "정의 있음" : "없음"));
  P("customElements.get('plain-tag')  = " + (customElements.get("plain-tag") ? "정의 있음" : "없음"));
};
</script>
</body>
</html>
===== dom http://127.0.0.1:18709/html09b-custom.html | probe =====
define 전  #먼저      = HTMLElement
define 전  #정의없음  = HTMLElement
define 전  #대시없음  = HTMLUnknownElement
   constructor 가 불렸다: 먼저
   connectedCallback 이 불렸다: 먼저
define 후  #먼저      = 시계
   constructor 가 불렸다: 
   connectedCallback 이 불렸다: 나중
맨 끝      #먼저      = 시계
맨 끝      #나중      = 시계
customElements.get('my-clock')   = 정의 있음
customElements.get('plain-tag')  = 없음
(exit 0)
```

**왜 그런가**

- ★★★ **셋이 다 같지 않다.** 대시가 있는 `my-clock`·`plain-tag` 는 **`HTMLElement`**, 대시가 없는 `nodash` 는 **`HTMLUnknownElement`** 다. **정의가 없어도 이름 모양만으로** 갈린다 — 「나중에 정의될 수 있는 이름」을 파서가 미리 대우해 준다.
- **`define` 하는 순간 `constructor` → `connectedCallback` 순서로** 이미 있던 요소가 업그레이드된다.
- **`define` 후 `#먼저` 의 클래스가 `시계`** 로 바뀌었다.
- ★ **`constructor` 안의 `this.id` 는 업그레이드 때는 `먼저` 로 보이는데, `createElement` 로 새로 만들 때는 빈 문자열**이다 — 그때는 **속성이 아직 안 붙었기** 때문이다. 두 경로의 **시점이 다르다.**
- **`customElements.get('plain-tag')` 가 「없음」** — 이름은 유효하지만 정의가 없다.

### 7. 「숨긴 것」이 아니라 「다른 문서에 있는 것」이다

**왜 그런가**

- **「숨겼다」** — `display: none` 은 트리에 **있고**, `querySelectorAll` 에 **잡히고**, 안의 `<img>` 도 **받는다.** 안 하는 것은 그리는 일뿐이다.
- **「안 산다」** — `<template>` 의 내용은 트리에 **없고**, 안 잡히고, 스크립트도 자원도 **아무 일도 안 한다.**
- ★★★ **한 줄짜리 이유** — 그 내용은 **「템플릿 내용 소유 문서」라는 별도 문서**에 담긴다. 자원 로딩과 스크립트 실행은 **문서에 딸린 일**이라, 문서가 다르면 아무 일도 안 일어난다.
- **확인한 줄** — A1 의 `틀.content.ownerDocument === document ? false`. 이 한 줄이 나머지 전부의 근거다.

### 8. 세 가지가 세 칸에서 다 다르게 나온다

| 무엇이 | `--dump-dom` 에 | `document.querySelectorAll` 에 | 화면에 |
|---|---|---|---|
| **`<template>` 안의 `<p>`** | **보인다** | 안 잡힌다 | 안 나온다 |
| **그림자 안의 `<p>`** | **안 보인다** | 안 잡힌다 | **나온다** |
| **`display: none` 인 `<p>`** | 보인다 | **잡힌다** | 안 나온다 |

**왜 그런가**

- ★★★ **「`--dump-dom` 에 없다」가 「문서에 없다」를 뜻하지 않는 경우** — 그림자다. 창 ①이 **통째로 사각지대**다(A3).
- **뜻하는 경우** — 파서가 아예 안 만든 것(예: 잘못된 자리의 태그). 그때는 `querySelectorAll` 도 못 찾는다.
- ★ **그래서 이 주제는 창 ①을 믿지 않고 창 ②로 확인한다.** A4 가 그 자리다.

### 9. 「아무도 안 채운 칸」에서만 나온다 — 공백도 채운 것으로 친다

**왜 그런가**

- **조건 한 문장** — **`assignedNodes()` 가 비어 있는 칸에서만** 기본 내용이 그려진다.
- ★★★ **이름 없는 칸이 잘 안 나오는 이유** — 호스트 안의 **줄바꿈·들여쓰기가 텍스트 노드**이고, 그것이 **이름 없는 칸에 할당**되기 때문이다. demo 의 `assignedNodes = [#text, #text]` 가 그 실측이다. **공백 텍스트 노드**는 [04번 주제](../04-whitespace-and-character-references/2-summary.md)가 정본이다.
- ★★ **`innerText` 로는 확인할 수 없다.** Chrome 151 의 `innerText` 가 그림자 안을 안 보기 때문이다(A5). **좌표**(`Range.getBoundingClientRect`)로 재야 한다.

### 10. 마크업과 API 의 경계

| 무엇이 | 어디가 정본인가 | 여기는 어디까지 |
|---|---|---|
| `attachShadow`·캡슐화 경계·슬롯 할당 API·`::part` | web-api 갈래 목록([`web-api/README.md`](../../../../web-api/README.md))의 **12번** | **`shadowrootmode` 라는 마크업 속성**까지 |
| 커스텀 요소 수명주기(`attributeChangedCallback`·`observedAttributes`) | web-api 갈래의 **13번** | **업그레이드 시점 맛보기**까지 |
| `DocumentFragment` 와 `<template>` **복제** | web-api 갈래의 **05번** | **`content` 가 별도 문서라는 사실**까지 |
| 웹 컴포넌트가 **왜 생겼나** | [`history/web/05-웹플랫폼-API.md`](../../../../../../history/web/05-웹플랫폼-API.md) §6 | **오늘 마크업으로 무엇이 되나**까지 |
| 공백 텍스트 노드 | [04번 주제](../04-whitespace-and-character-references/2-summary.md) | 슬롯 할당에서 **그것이 칸을 먹는다**는 결과까지 |

**여기에 남는 것** — ★ **스크립트를 한 줄도 안 쓰고 되는 것 전부.** `<template>` 의 파싱과 불활성, `shadowrootmode`·`shadowrootserializable` 이라는 **속성**, `<slot>`/`slot` 의 **문법과 기본 내용**, 그리고 **커스텀 요소 이름 규칙**이다. 이 중 어느 것도 JS API 를 부르지 않는다.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · 기본 창 폭 **780**. **엔진은 이것 하나다.**

**하네스** — 09\~12 네 주제가 공유한다.

```bash
# html09b-harness.sh
dom()   { google-chrome --headless --disable-gpu --no-sandbox --dump-dom "$1" 2>/dev/null; }
probe() { sed -n '/^###P###$/,/^###E###$/p' | sed '1d;$d' \
          | sed 's/&lt;/</g; s/&gt;/>/g; s/&amp;/\&/g'; }
nojs()  { sed '/^<script>$/,$d'; }
ax()    { python3 html09b-ax.py "$1"; }
serve() { python3 html09b-server.py >>"$1" 2>&1 & echo $!; }
```

**서버** — 이 주제는 **요청 로그** 때문에 로컬 HTTP 서버 위에서 돌렸다. 「`<template>` 안의 이미지를 **안 받는다**」는 그것 말고는 보일 방법이 없다.

```python
# html09b-server.py
import http.server
import time


class 느린서버(http.server.SimpleHTTPRequestHandler):
    """이름에 `-slow` 가 든 파일만 0.5초 늦게 준다.

    렌더 차단은 「얼마나 기다렸나」로만 드러나므로 한 파일을 확실히 늦게 준다.
    요청 로그는 「안 받아 옴」과 「받아 놓고 안 씀」을 가르는 유일한 창이다.
    ThreadingHTTPServer 라야 한 요청을 재우는 동안 다른 요청이 지나간다.
    """

    def do_GET(self):
        if "-slow" in self.path:
            time.sleep(0.5)
        return super().do_GET()

    def log_message(self, fmt, *args):
        print(self.path, flush=True)


http.server.ThreadingHTTPServer(("127.0.0.1", 18709), 느린서버).serve_forever()
```

**프로브 로거** — `load` 뒤 `setTimeout(…, 0)` 에서 한 번에 찍는다.

```javascript
// html09b-probe.js
window.__L = [];
window.P = function (줄) { window.__L.push(줄); };
window.addEventListener("load", function () {
  setTimeout(function () {
    if (window.__끝) window.__끝();
    var q = document.createElement("pre");
    q.textContent = "\n###P###\n" + window.__L.join("\n") + "\n###E###\n";
    document.body.appendChild(q);
  }, 0);
});
```

**이미지** — 1×1 투명 GIF 한 장(`html09b-dot.gif`, 43바이트)을 `?out`·`?in` 두 질의로 나눠 썼다. **같은 파일인데 요청 로그에서 갈린다.**

**본문에 안 실린 실험 파일** — 없다. A1\~A6 이 소스를 전부 싣고 있다.

**demo 블록** — [2-summary.md](2-summary.md) 의 `demo` 와 「바꿔 볼 것」을 둘 다 던져 확인했다.

```text
===== 소스: html09b-demo10a.html (demo 블록 + 래퍼 + 측정 프로브) =====
<!DOCTYPE html>
<meta charset="utf-8">
<title>demo 10 검증</title>
<body>
<my-badge>
  <template shadowrootmode="open">
    <style>b { color: rgb(37, 99, 235); }</style>
    <b><slot name="라벨">기본 라벨</slot></b>
    <slot name="설명">기본 설명</slot>
    <slot>기본 본문</slot>
  </template>
  <span slot="라벨">채운 라벨</span>
</my-badge>
<script>
const o = [];
const 기본폭 = s => { const r = document.createRange(); r.selectNodeContents(s); return r.getBoundingClientRect().width; };
const 호스트 = document.querySelector("my-badge"), 그 = 호스트.shadowRoot;
o.push("창 폭 = " + window.innerWidth);
o.push("shadowRoot = " + (그 ? "ShadowRoot(mode=" + 그.mode + ")" : "null"));
o.push("<template> 이 남았나 = " + 호스트.querySelectorAll("template").length + "개");
for (const s of 그.querySelectorAll("slot")) {
  o.push(("slot name=" + JSON.stringify(s.name)).padEnd(18)
    + "할당된 노드 = [" + s.assignedNodes().map(n => n.nodeName).join(", ") + "]"
    + "   기본 내용이 그려진 폭 = " + Math.round(기본폭(s)) + "px");
}
o.push("<b> 의 계산값 color = " + getComputedStyle(그.querySelector("b")).color);
o.push("document.body.innerText = " + JSON.stringify(document.body.innerText)
  + "   <- innerText 는 그림자 안을 못 본다");
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
===== dom html09b-demo10a.html | probe =====
창 폭 = 780
shadowRoot = ShadowRoot(mode=open)
<template> 이 남았나 = 0개
slot name="라벨"    할당된 노드 = [SPAN]   기본 내용이 그려진 폭 = 0px
slot name="설명"    할당된 노드 = []   기본 내용이 그려진 폭 = 63px
slot name=""      할당된 노드 = [#text, #text]   기본 내용이 그려진 폭 = 0px
<b> 의 계산값 color = rgb(37, 99, 235)
document.body.innerText = "채운 라벨"   <- innerText 는 그림자 안을 못 본다
(exit 0)
```

```text
===== 소스: html09b-demo10b.html (demo 블록 + 래퍼 + 측정 프로브) =====
<!DOCTYPE html>
<meta charset="utf-8">
<title>demo 10 「바꿔 볼 것」 검증</title>
<body>
<my-badge id="ㄱ">
  <template shadowrootmode="open">
    <b><slot name="라벨">기본 라벨</slot></b>
    <slot>기본 본문</slot>
  </template>
  <span>채운 라벨</span>
</my-badge>
<my-badge id="ㄴ">
  <template shadowrootmode="zzz">
    <b><slot name="라벨">기본 라벨</slot></b>
  </template>
  <span slot="라벨">채운 라벨</span>
</my-badge>
<script>
const o = [];
const ㄱ = document.getElementById("ㄱ"), ㄴ = document.getElementById("ㄴ");
o.push('slot="라벨" 을 지우면');
for (const s of ㄱ.shadowRoot.querySelectorAll("slot")) {
  o.push("   slot name=" + JSON.stringify(s.name).padEnd(8)
    + " 에 들어간 것 = " + (s.assignedNodes().length ? "「" + s.assignedNodes()[0].textContent + "」" : "없음(기본 내용이 나온다)"));
}
o.push('shadowrootmode="zzz" 로 바꾸면');
o.push("   shadowRoot = " + (ㄴ.shadowRoot ? "있음" : "null")
  + "   남은 <template> = " + ㄴ.querySelectorAll("template").length + "개");
o.push("   그 호스트의 innerText = " + JSON.stringify(ㄴ.innerText));
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
===== dom html09b-demo10b.html | probe =====
slot="라벨" 을 지우면
   slot name="라벨"     에 들어간 것 = 없음(기본 내용이 나온다)
   slot name=""       에 들어간 것 = 「
  
  」
shadowrootmode="zzz" 로 바꾸면
   shadowRoot = null   남은 <template> = 1개
   그 호스트의 innerText = "채운 라벨"
(exit 0)
```

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| **`<template>` 안의 script·img·style·p** | 2 | 동작 방식 (1) · A1 · A7 |
| **그 판의 요청 로그** | 2 | 동작 방식 (1) · A1 |
| **`<template>` 의 덤프**(표 안팎) | 2 | 동작 방식 (2) · A2 · A8 |
| **`shadowrootmode` 세 값의 덤프 + 콘솔** | 2 | 동작 방식 (3) · A3 |
| **그림자 프로브 + 직렬화 네 경로** | 2 | 동작 방식 (4) · A4 |
| **슬롯 셋 + 좌표** | 2 | 동작 방식 (5) · A5 · A9 |
| **커스텀 요소 업그레이드** | 2 | 동작 방식 (6) · A6 |
| **demo 와 「바꿔 볼 것」** | 2 | demo 절 |

**구현에 달린 항목**

| 항목 | 이 판의 값 | 왜 다시 찍나 |
|---|---|---|
| `outerHTML` 이 `<template>` 은 직렬화하고 **섀도는 안 하는 것** | (2)·(3) | Blink 의 직렬화다. 다만 **섀도 쪽은 명세도 그렇게 정한다** |
| `innerText` 가 **그림자 안을 안 보는 것** | (5) | `innerText` 는 명세가 헐거운 자리다 |
| 잘못된 `shadowrootmode` 의 **콘솔 문구** | `"Invalid declarative shadowrootmode attribute value. …"` | Blink 의 문구다 |
| 기본 내용의 **픽셀 폭** | `0px` 대 `63px` | 글꼴에 달렸다 — **0 이냐 아니냐**만 근거로 쓴다 |
| 선언적 Shadow DOM 자체 | 동작함 | **이 묶음에서 가장 새 표면**이다. 판이 낮으면 안 될 수 있다 |

**안 돌려 본 것** — ① **Firefox·Safari 재현**(엔진이 없다). **선언적 Shadow DOM 은 특히 이식성을 주장할 수 없다.** ② **`template.content` 를 복제해 붙이는 것** — web-api 05번의 표면이라 안 던졌다. ③ **`attachShadow` 로 만든 그림자** — web-api 12번의 표면이다. ④ **`::part`·`::slotted` 같은 섀도 선택자** — CSS·web-api 쪽이다. ⑤ **슬롯이 접근성 트리에서 어떻게 평탄화되나** — 11·12 에서 쓴 접근성 트리 도구를 **여기에는 적용하지 않았다**(다음 배치의 자리). ⑥ **`attributeChangedCallback`·`observedAttributes`** — web-api 13번이다. ⑦ **`<template>` 안에 선언적 Shadow DOM 을 중첩한 경우.**

**못 잰 것**(「안 돌려 본 것」과 다르다) — **`--dump-dom` 으로 섀도 트리 안을 보는 것.** 도구가 `outerHTML` 을 쓰고 `outerHTML` 이 섀도를 직렬화하지 않으므로 **측정 방법 자체가 없다**(A3). 쪼개서 잰 조각은 **① `shadowRoot` 가 있다 ② `shadowRoot.innerHTML` 로 안을 읽을 수 있다 ③ `shadowrootserializable` 을 붙이면 `getHTML` 로 뽑힌다** 셋이다. 같은 이유로 **`innerText` 로 섀도 안의 글자를 읽는 것**도 못 잰 것이고, 대신 **좌표**로 갈랐다(A5·A9).

**부적용인 창** — **창 ④(`compatMode`).** `<template>`·섀도·커스텀 요소는 문서 모드를 안 바꾸므로 **잴 것이 없다**(「재 봤더니 같았다」가 아니다). ★ 반대로 **창 ③(`innerText` 대 `textContent`)은 이 주제에서 새 뜻을 얻었다** — 슬롯이 **트리와 렌더를 갈라 놓는** 대표 사례다(A5).

## 용어 풀이

- **`<template>`** — 파싱은 되지만 **문서 트리에 안 들어가는** 조각을 담는 요소.
- **`content`** — 그 내용이 담긴 `DocumentFragment`. **`ownerDocument` 가 문서와 다르다.**
- **inert(불활성)** — 파싱은 됐는데 스크립트도 안 돌고 자원도 안 받는 상태.
- **선언적 Shadow DOM** — 스크립트 없이 **마크업만으로** 섀도 루트를 만드는 것.
- **`shadowrootmode`** — `open`(스크립트가 `shadowRoot` 로 잡는다) / `closed`(못 잡는다). **모르는 값이면 아무 일도 안 일어난다.**
- **`shadowrootserializable`** — 그 섀도를 `getHTML()` 로 **다시 글자로 뽑을 수 있게** 허락하는 속성.
- **라이트 DOM** — 호스트의 **문서 쪽 자식들.** 슬롯에 할당될 후보다.
- **`<slot>`** — 라이트 DOM 을 섀도 안으로 **투영하는 자리.**
- **슬롯 할당** — `slot` 속성 값과 `<slot name>` 을 맞춰 넣는 것. **공백 텍스트 노드도 이름 없는 칸을 채운다.**
- **업그레이드(upgrade)** — 이미 트리에 있던 요소가 `customElements.define` 시점에 그 클래스로 바뀌는 것.
- **`HTMLUnknownElement`** — 파서가 모르는 요소의 클래스. **대시가 있는 이름은 여기에 안 들어간다.**
