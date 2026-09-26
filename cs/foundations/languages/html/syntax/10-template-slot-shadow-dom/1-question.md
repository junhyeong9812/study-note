# html/syntax/10 — `template`·`slot`·선언적 Shadow DOM·커스텀 요소 맛보기 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ 이 주제는 「**트리에 있나 · 화면에 있나 · 덤프에 보이나**」 셋을 **갈라서** 답한다. 셋이 다 다르다.
> ★★ **「`--dump-dom` 에 안 보인다」를 「없다」로 답하지 마라** — 이 주제에 그 함정이 하나 있다.
> ★ **경계** — Shadow DOM 과 커스텀 요소의 **API** 는 web-api 갈래 목록([`web-api/README.md`](../../../../web-api/README.md))의 **12번**·**13번**이 정본이다. 여기서 묻는 것은 **마크업**뿐이다.
> ★ 소스 펜스 첫 줄의 `<!-- 파일이름 -->` 은 **어느 파일을 던진 것인지 표시**이지 파일 내용이 아니다.
> 선행 — [05번 주제](../05-content-categories-and-models/1-question.md) · [08번 주제](../08-script-loading/1-question.md).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `<template>` 안에 `<script>`·`<img>`·`<style>`·`<p>` 를 넣으면 (예측)

```html
<!-- html09b-template-inert.html -->
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
```

- 「★ 틀 안의 스크립트가 돌았다 ★」가 로그에 나오는가?
- `<img>` 개수 · `<p>` 개수 · `document.styleSheets.length` 를 예측하라.
- `#표식` 의 계산값 색은 무엇인가?
- `틀.childNodes.length` 와 `틀.content.childNodes.length` 를 각각 예측하라.
- `틀.content.ownerDocument === document` 는 무엇인가? **그 답이 이 문항의 핵심**이다.
- **서버 요청 로그에 `?in` 이 나오는가?**

### 2. 그 `<template>` 이 `--dump-dom` 에 어떻게 보이나 (예측)

```html
<!-- html09b-template-tree.html -->
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
```

- 덤프에 `<template>` 안의 `<p>안</p>` 이 보이는가?
- 표 **밖의** `<template>` 안에 쓴 `<td>` 는 어떻게 되는가?
- 표 **안의** `<template>` 안에 쓴 `<tr><td>` 는 어떻게 되는가?
- 1번의 `querySelectorAll` 결과와 여기 덤프가 어긋난다 — 무엇이 다른가?

### 3. `shadowrootmode` 를 세 가지로 주면 (예측)

```html
<!-- html09b-dsd-tree.html -->
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
```

- 이 판에서 선언적 Shadow DOM 이 **되는가**?
- 덤프에서 `<template>` 이 남아 있는 것은 셋 중 어느 것인가?
- **그림자 안의 `<p>` 가 덤프에 보이는가?**
- 콘솔에 무엇이 나는가?

### 4. 그림자를 글자로 다시 뽑으면 (예측)

```html
<!-- html09b-dsd-probe.html -->
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
```

- `my-card.shadowRoot` · `my-closed.shadowRoot` · `my-bad.shadowRoot` 를 각각 예측하라.
- `열림.outerHTML` 과 `열림.getHTML()` 에 그림자가 보이는가?
- `getHTML({serializableShadowRoots: true})` 에는 보이는가? **`my-ser` 와 갈리는가?**
- 왜 기본값이 「안 보임」인가?

### 5. 슬롯 셋을 두고 하나만 채우면 (예측)

```html
<!-- html09b-slot.html -->
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
```

- 세 슬롯의 `assignedNodes()` 를 각각 예측하라.
- `slot="오타"` 인 요소의 `assignedSlot` 은 무엇인가? 화면에는 나오는가?
- `호스트.textContent` 와 `호스트.innerText` 가 갈리는가? 어떻게 갈리는가?
- **기본 내용이 진짜 그려진 칸**은 어느 것인가? 그것을 무엇으로 쟀겠는가?

### 6. `define` 보다 먼저 파서가 만든 요소는 (예측)

```html
<!-- html09b-custom.html -->
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
```

- `define` 전의 세 `constructor.name` 을 예측하라. **셋이 다 같은가?**
- `define` 하는 순간 무엇이 불리는가? 순서는?
- `define` 후 `#먼저` 의 `constructor.name` 은?
- `constructor` 안에서 읽은 `this.id` 가 두 번 다 값이 있는가?

### 7. `<template>` 안은 왜 안 사나 (왜)

- 「숨겼다」와 「안 산다」가 무엇이 다른가?
- 스크립트가 안 돌고 자원을 안 받는 **한 줄짜리 이유**를 대라.
- 그 이유를 프로브의 어느 줄로 확인했는가?

### 8. 「안 보인다」의 세 가지 (경계)

- `<template>` 안의 `<p>` · 그림자 안의 `<p>` · `display: none` 인 `<p>` — 셋을 **덤프 / `querySelectorAll` / 화면** 세 칸으로 갈라라.
- 「`--dump-dom` 에 없다」가 「문서에 없다」를 뜻하는 경우와 안 뜻하는 경우를 대라.
- 이 주제에서 창 ①이 **통째로 사각지대**가 되는 자리는 어디인가?

### 9. `<slot>` 의 기본 내용이 안 나오는 이유 (경계)

- 기본 내용이 나오는 조건을 한 문장으로 대라.
- 이름 없는 칸에서 기본 내용이 잘 안 나오는 이유는?
- 그것을 `innerText` 로 확인할 수 있는가? 없다면 무엇으로 재야 하는가?

### 10. 마크업과 API 의 경계 (연결)

- `attachShadow`·`::part`·이벤트 재타깃팅의 정본은 어느 갈래의 몇 번인가?
- 커스텀 요소 수명주기(`attributeChangedCallback` 등)의 정본은?
- `template.content` 를 **복제해 붙이는** 이야기의 정본은?
- 웹 컴포넌트가 **왜 생겼나**의 정본은?
- 그렇다면 이 주제에 **남는 것**은 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
