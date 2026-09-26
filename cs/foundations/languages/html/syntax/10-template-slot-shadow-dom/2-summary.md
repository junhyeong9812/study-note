# html/syntax/10 — `template`·`slot`·선언적 Shadow DOM·커스텀 요소 맛보기 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 [「The `template` element」](https://html.spec.whatwg.org/multipage/scripting.html#the-template-element)·[「The `slot` element」](https://html.spec.whatwg.org/multipage/scripting.html#the-slot-element)·[「Custom elements」](https://html.spec.whatwg.org/multipage/custom-elements.html) 절과 [WHATWG DOM Standard](https://dom.spec.whatwg.org/) 의 [「Shadow tree」](https://dom.spec.whatwg.org/#shadow-trees) 절. 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에 실제로 띄워 읽은 것이다. 하네스는 [3-answer.md](3-answer.md) 의 `## 실행 검증` 절에 있다.\
> ★ **엔진은 Chrome 하나다.** 이 갈래는 **이식성을 주장하지 않는다.**
> **버전** — HTML 에는 언어 버전이 없다. 지원 상태는 **Baseline** 으로 읽는다. `<template>`·`<slot>`·커스텀 요소는 2018년 전후, **선언적 Shadow DOM(`shadowrootmode`)은 2023\~2024년**에 자리 잡았다 — 이 묶음에서 **가장 새 표면**이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.
> ★★ **이 주제의 본체는 창 ①(`--dump-dom`)과 창 ⑤(서버 요청 로그) 둘이다** — 「`<template>` 안이 안 산다」는 **요청 로그**가 가장 강하게 말하고(받아 오지도 않는다), 「그림자가 생겼나」는 **창 ①이 못 보는 자리**라 창 ②가 대신 답한다. 창 넷의 정의는 [01번 주제](../01-document-skeleton/2-summary.md)의 「이 갈래의 창」 절에, 창 ⑤ 는 [08번 주제](../08-script-loading/2-summary.md)의 (6) 에 있다.
> ★★★ **경계** — **Shadow DOM 의 API 는 web-api 갈래가 정본이다.** web-api 갈래 목록([`web-api/README.md`](../../../../web-api/README.md))의 **12번**(`attachShadow`·캡슐화 경계·`::part`)과 **13번**(커스텀 요소 수명주기)이 그쪽이고, **여기는 마크업까지**다 — `<template>` 의 파싱, `shadowrootmode` 라는 **속성**, `<slot>` 의 **문법과 기본 내용**. 웹 컴포넌트가 **왜 생겼나**는 [`history/web/05-웹플랫폼-API.md`](../../../../../../history/web/05-웹플랫폼-API.md) §6 이 정본이다.

**이 판의 Chrome**

```text
===== google-chrome --version =====
Google Chrome 151.0.7922.173 
(exit 0)
```

### 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | Chrome 판 번호 | 판이 오르면 바뀐다 |
| **흔들린다** | 글자의 **픽셀 폭**(demo 의 `63px`) | 글꼴에 달렸다 — **0 이냐 아니냐**만 근거로 쓴다 |
| **안 흔들린다** | `--dump-dom` 이 `<template>` 을 어떻게 직렬화하나 | 직렬화 규칙이 정한다 |
| **안 흔들린다** | `shadowRoot` 가 `null` 이냐 아니냐 · `mode` 값 | 명세가 정한다 |
| **안 흔들린다** | **요청 로그에 이름이 있나 없나** | 〃 |
| **안 흔들린다** | `assignedNodes()` 의 **내용과 순서** | 〃 |
| **안 흔들린다** | 커스텀 요소의 `constructor.name` 과 콜백 순서 | 〃 |
| **안 흔들린다** | 블록의 `(exit N)` | 파서는 실패하지 않는다([03번 주제](../03-parser-and-error-recovery/2-summary.md)) |

## 한눈에 — 쉽게 말하면

**★ `<template>` 은 「숨긴 것」이 아니라 「아직 문서가 아닌 것」이다.**

옷가게에 비유한다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 매장에 걸린 옷 | **문서 트리의 요소** — 보이고, 입을 수 있고, 값이 매겨진다 |
| **창고의 본(패턴) 종이** | **`<template>` 의 내용** — 모양은 완전한데 **입을 수 없다** |
| 본을 떠서 만든 옷 | `template.content` 를 **복제해 넣은 것** |
| 옷에 붙은 **이름표 자리** | **`<slot>`** — 비어 있으면 **기본 문구**가 인쇄돼 있다 |
| 손님이 준 이름표를 그 자리에 **끼우는 것** | **슬롯 할당**(`slot="이름"`) |
| 가게 뒷방 — 손님이 못 들어가는 곳 | **Shadow DOM** |
| 뒷방 문을 **열어 두느냐 잠그느냐** | **`shadowrootmode="open"` / `"closed"`** |

- **`<template>` 안은 파싱은 되는데 아무것도 안 산다.** 스크립트가 안 돌고 **이미지를 받아 오지도 않는다.**
- **선언적 Shadow DOM 은 `<template>` 을 먹어 치운다.** 파싱이 끝나면 **그 `<template>` 은 트리에 없다.**
- **`--dump-dom` 은 그림자를 못 본다.** 이 주제의 **도구 한계**가 정확히 거기다.

```text
  같은 <p>세 개가 어디에 사느냐로 갈린다

  ① 그냥 문서에 있는 <p>
       querySelectorAll("p") 에 잡힌다 · 화면에 나온다 · 스크립트도 돈다

  ② <template> 안의 <p>
       querySelectorAll("p") 에 안 잡힌다
       ownerDocument 가 다르다   <- 문서가 아예 다르다
       안의 <script> 안 돈다 · 안의 <img> 를 안 받는다
       그런데 --dump-dom 에는 보인다   <- ★ 직렬화는 해 준다

  ③ 그림자(shadow root) 안의 <p>
       querySelectorAll("p") 에 안 잡힌다
       화면에는 나온다              <- ★ ②와 여기서 갈린다
       --dump-dom 에는 안 보인다     <- ★ 도구가 못 보는 자리
```

실무에서 이게 터지는 자리는 **`<template>` 안에 써 둔 `<img>` 가 「미리 받아져 있겠지」라고 믿는 것**이다.\
안 받는다. 복제해서 문서에 붙이는 **그 순간부터** 받기 시작한다.\
그리고 더 헷갈리는 자리는 **`<slot>` 의 기본 내용이 안 나오는 것**이다 — 소스의 **줄바꿈 공백**이 이미 그 칸을 채웠기 때문이다.

> **inert(불활성)** — 파싱은 됐는데 **아무 일도 안 일어나는** 상태.\
> 예: `<template>` 안의 `<script>` 는 문법도 맞고 트리에도 있는데 **평가되지 않는다.**

> **라이트 DOM / 섀도 DOM** — 호스트 요소가 **문서에 드러내 놓은 자식**(라이트)과, 그 뒤에 숨겨 둔 **자기만의 트리**(섀도).\
> 예: `<my-card>` 안에 내가 쓴 `<span>` 은 라이트, `shadowrootmode` 로 만든 것은 섀도다.

## 이 주제가 답하려는 질문

1. **`<template>` 안의 내용은 어디까지 「안 사나」.** 파싱은 되는데 무엇이 안 일어나나.
2. **선언적 Shadow DOM 이 이 판에서 되나.** 되면 `--dump-dom` 에 보이나.
3. **`<slot>` 의 기본 내용은 언제 나오고 언제 안 나오나.**

## 동작 방식

### (1) 창 ⑤ + 창 ② — `<template>` 안은 「받아 오지도」 않는다

**언제 쓰나** — 이 주제의 본체. **「숨긴 것」과 「안 사는 것」을 가르는 자리.**

`<img>`·`<script>`·`<style>`·`<p>` 를 **밖에 하나씩, `<template>` 안에 하나씩** 두고 던졌다.\
바깥 `<img>` 는 `?out`, 틀 안의 `<img>` 는 `?in` 으로 **같은 파일에 다른 질의**를 붙여 요청 로그에서 갈리게 했다.

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

**그리고 같은 한 판이 서버에 낸 요청이다.**

```text
===== 이 한 판이 서버에 낸 요청 (grep -o '^/html09b-[^ ]*' srv.log | sort | uniq -c) =====
      1 /html09b-dot.gif?out
      1 /html09b-probe.js
      1 /html09b-template-inert.html
(exit 0)
```

```text
  <template> 의 내용은 「다른 문서」에 산다

  ┌─ document (내가 보는 문서) ───────────────┐
  │  <img src="...?out">   <- 받는다           │
  │  <script>              <- 돈다             │
  │  <p id="표식">밖의 p    <- querySelector 에 잡힌다
  │  <template id="틀">  ──────────┐           │
  └───────────────────────────────│───────────┘
                                  │ content
  ┌─ 템플릿 내용 소유 문서 ─────────▼──────────┐
  │  <img src="...?in">    <- 안 받는다         │
  │  <script>              <- 안 돈다           │
  │  <style>               <- 안 먹는다         │
  │  <p id="표식">틀 안의 p  <- 안 잡힌다        │
  └──────────────────────────────────────────┘

  ownerDocument 가 다르다 — 이 한 줄이 나머지 전부의 이유다.
```

- ★★★ **`?in` 이 로그에 한 줄도 없다.** 「안 그렸다」가 아니라 **받아 오지도 않았다.** 이것이 이 주제에서 가장 강한 근거다.
- **틀 안의 `<script>` 가 안 돌았다** — 로그에 「★ 틀 안의 스크립트가 돌았다 ★」가 없다.
- **틀 안의 `<style>` 이 안 먹었다** — `styleSheets.length` 가 **1**이고 `#표식` 의 색이 바깥 규칙 `rgb(120, 120, 120)` 이다.
- **`querySelectorAll` 에 안 잡힌다** — `<img>` 1개 · `<p>` 1개. `getElementById("표식")` 도 **바깥 것**을 준다.
- ★★ **`틀.childNodes.length = 0` 인데 `틀.content.childNodes.length = 9` 다.** 내용은 `<template>` 의 **자식이 아니다.**
- ★★★ **`content.ownerDocument !== document`** — 내용이 **다른 문서에 산다.** 「안 사는」 것의 진짜 이유가 이것이다.
- **틀 안 `<img>` 는 `complete = true`·`naturalWidth = 0`** 이다 — 「다 받았다」가 아니라 **시작도 안 했다**는 뜻이다.

### (2) 창 ① — `content` 는 다른 문서인데 덤프에는 보인다

**언제 쓰나** — 창 ①이 **무엇을 보여 주고 무엇을 안 보여 주는지** 정하는 자리.

스크립트를 한 줄도 안 넣은 판이다.

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

```text
  같은 조각을 두 창이 다르게 답한다

                              --dump-dom      document.querySelectorAll
  <template> 안의 <p>            보인다              안 잡힌다
                                  ^                     ^
                                  |                     |
                    직렬화기가 content 를          문서 트리에는
                    대신 찍어 준다                  없다

  ★ 「덤프에 있다」와 「문서에 있다」는 다른 말이다.
```

- ★★ **`--dump-dom` 은 `<template>` 안을 보여 준다.** 직렬화 알고리즘이 `<template>` 만 특별히 **`content` 를 대신 직렬화**하기 때문이다.
- ★★★ **그래서 「덤프에 보인다」와 「문서에 있다」는 다른 말이다.** (1) 에서 `querySelectorAll` 이 못 찾은 것을 창 ①은 보여 준다.
- ★ **`<td>` 가 사라졌다.** 표 밖의 `<template>` 안에 쓴 `<td>` 는 태그가 버려지고 **글자만 남았다** — `<template>` 안도 **파서의 삽입 모드 규칙**을 그대로 받는다([03번 주제](../03-parser-and-error-recovery/2-summary.md)).
- ★ **반대로 `<table>` 안의 `<template>` 에서는 `<tr><td>` 가 살아남았다.** 같은 태그가 **어디 있느냐로 갈린다.**

### (3) 창 ① 의 한계 — 선언적 Shadow DOM 은 덤프에 안 보인다

**언제 쓰나** — 이 판에서 **되는지부터** 확인하는 자리.

`open`·`closed`·모르는 값 셋을 던졌다. 스크립트는 한 줄도 없다.

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

```text
  선언적 Shadow DOM — 파싱 전과 후

  내가 쓴 것                          파싱이 끝난 뒤
  ----------                          --------------
  <my-card>                           <my-card>
    <template shadowrootmode="open">     #shadow-root (open)   <- 덤프에 안 나온다
      <p>그림자 안의 p</p>                  <p>그림자 안의 p</p>
      <slot></slot>                         <slot></slot>
    </template>                          <span>라이트 DOM</span>
    <span>라이트 DOM</span>             </my-card>
  </my-card>
                                      ★ <template> 이 통째로 사라졌다
```

- ★★★ **된다.** 그리고 **`<template>` 이 트리에서 사라졌다** — 파서가 그것을 먹어 **섀도 루트로 바꿔 놓았다.**
- ★★★ **그런데 그림자 안의 내용이 덤프에 하나도 없다.** `--dump-dom` 은 `outerHTML` 이고, **`outerHTML` 은 섀도 트리를 직렬화하지 않는다.**
- **모르는 값(`zzznope`)은 평범한 `<template>` 으로 남았다** — 먹히지 않았다.
- **이 판의 덤프만 보면 `my-card` 가 빈 것처럼 보인다.** ★ **「안 보인다」를 「없다」로 읽으면 안 되는 대표 사례다.**

**콘솔은 따로 말해 준다.**

```text
===== google-chrome --headless --disable-gpu --no-sandbox --enable-logging=stderr \
  --dump-dom http://127.0.0.1:18709/html09b-dsd-tree.html 2>&1 >/dev/null \
  | grep ':CONSOLE:' | sed 's/^\[[0-9:/.]*INFO:CONSOLE:[0-9]*\] //' | sort =====
"Invalid declarative shadowrootmode attribute value. Valid values are "open" and "closed".", source: http://127.0.0.1:18709/html09b-dsd-tree.html (20)
(exit 0)
```

- ★ **경고도 출력이다.** 모르는 값을 썼다는 사실이 **콘솔에만** 남는다.

### (4) 창 ② — 그림자를 글자로 다시 뽑을 수 있나

**언제 쓰나** — (3) 이 못 본 것을 **다른 창으로** 확인하는 자리.

같은 마크업에 프로브를 붙이고, **`shadowrootserializable` 을 붙인 넷째 호스트**를 더했다.

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

```text
  그림자를 글자로 되돌리는 네 경로 — 기본은 전부 「안 보임」

  열림.outerHTML                                  -> 안 보인다
  열림.getHTML()                                  -> 안 보인다
  열림.getHTML({serializableShadowRoots: true})   -> 안 보인다   ★ 허락이 없다
  직렬.getHTML({serializableShadowRoots: true})   -> 보인다      <- shadowrootserializable

  캡슐화가 목적이므로 마크업이 미리 허락해야 뽑힌다.
```

- **`open` 은 `shadowRoot` 를 준다.** `mode` 가 `open` 이고 `innerHTML` 로 안을 읽을 수 있다.
- ★★ **`closed` 는 스크립트에도 `null` 이다.** 선언적으로 만든 닫힌 그림자는 **페이지 스크립트가 다시 잡을 방법이 없다.**
- **모르는 값은 `<template>` 1개가 그대로 남았다** — (3) 의 덤프와 같은 답이다.
- ★★★ **직렬화는 기본이 「안 보임」이다.** `outerHTML` 도 `getHTML()` 도 **안 보인다**고 답했고, `getHTML({serializableShadowRoots: true})` 조차 **`shadowrootserializable` 이 마크업에 없으면 안 보인다.**
- ★ **그 속성을 붙인 넷째 호스트에서만 보였다.** 즉 **그림자를 글자로 되돌리려면 마크업이 미리 허락해야 한다.**

### (5) 창 ② + 좌표 — `<slot>` 의 기본 내용은 언제 나오나

**언제 쓰나** — 컴포넌트에 「기본값」을 주는 자리.

이름 있는 칸 둘과 이름 없는 칸 하나를 두고, 바깥에서 **하나만 채우고 하나는 이름을 틀리게** 썼다.

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

```text
  슬롯 투영 — 라이트 DOM 은 옮겨지지 않고 「그려질 때만」 그 자리로 간다

  라이트 DOM (트리)                 섀도 (그려지는 자리)
  -----------------                 --------------------
  <h2 slot="제목">바깥이 준 제목  ──> <slot name="제목">기본 제목</slot>
  <p>바깥이 준 본문            ──> <slot>기본 본문</slot>
  <p slot="오타">이름이 틀린 것  ─X   (어느 칸에도 안 간다 — 화면에서 사라진다)
                                     <slot name="없는칸">아무도 안 채우는 칸</slot>
                                                ^
                                                | 비었으므로 기본 내용이 그려진다

  textContent 에는 「이름이 틀린 것」이 있고 innerText 에는 없다.
```

- **`slot="제목"` 이 이름 있는 칸에 들어갔다.** 채워진 칸은 **기본 내용을 안 쓴다.**
- **이름 없는 칸**에는 `slot` 속성이 없는 `<p>` 가 들어갔다.
- **아무도 안 채운 칸**만 **기본 내용**이 나왔다.
- ★★★ **이름이 틀린 것은 어느 칸에도 안 들어가고 화면에서 사라진다** — `assignedSlot` 이 `null` 이다. **예외도 경고도 없다.**
- ★★ **창 ③ 이 여기서 갈린다** — `textContent`(트리)에는 **이름이 틀린 글자까지** 들어 있는데 `innerText`(렌더)에는 **없다.**
- ★★★ **그런데 `innerText` 에는 기본 내용도 없다.** Chrome 151 의 `innerText` 는 **그림자 안을 안 본다.** 그래서 「기본 내용이 진짜 그려졌나」는 **상자 높이로 따로 쟀다** — 아무도 안 채운 칸만 **0 보다 컸다.**
- ★ **한 관찰로 두 질문에 답하지 않는다** — 「할당됐나」는 `assignedNodes()` 가, 「그려졌나」는 **좌표**가 답한다.

### (6) 창 ② — 커스텀 요소 맛보기: 업그레이드는 `define` 하는 순간이다

**언제 쓰나** — 파서가 **정의보다 먼저** 만든 요소가 어떻게 되나.

★ **여기는 맛보기다.** 수명주기 전체는 **web-api 갈래 목록([`web-api/README.md`](../../../../web-api/README.md))의 13번이 정본**이다.

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

```text
  업그레이드 시점 — 두 경로의 시각이 다르다

  파서가 먼저 만든 것                  나중에 만든 것
  -------------------                  ---------------
  <my-clock id="먼저">                 (아직 없음)
        |  HTMLElement                       |
        |                                    |
  customElements.define("my-clock", 시계)     |
        |                                    |
        +-- constructor(this.id="먼저")       |
        +-- connectedCallback                |
        |  시계                          createElement("my-clock")
                                             +-- constructor(this.id="")   ★ 속성 전
                                        appendChild
                                             +-- connectedCallback
```

- ★★★ **대시가 있으면 `HTMLElement`, 없으면 `HTMLUnknownElement` 다.** 정의가 없어도 **이름 모양만으로** 갈린다 — 「나중에 정의될 수 있는 이름」을 파서가 미리 대우해 준다.
- **`define` 하는 순간 이미 있던 요소가 업그레이드된다** — `constructor` 와 `connectedCallback` 이 **그 자리에서** 불리고, 클래스가 `HTMLElement` 에서 `시계` 로 바뀐다.
- **나중에 만든 것은 `createElement` 시점에 `constructor`, 붙이는 시점에 `connectedCallback`** 이 불린다 — 두 시점이 **갈라진다.**
- ★ `constructor` 시점에는 **`id` 가 아직 비어 있다**(빈 문자열) — 속성은 그 뒤에 붙는다.

### demo — 그림자와 슬롯을 스크립트 한 줄 없이

```html demo
<my-badge>
  <template shadowrootmode="open">
    <style>b { color: rgb(37, 99, 235); }</style>
    <b><slot name="라벨">기본 라벨</slot></b>
    <slot name="설명">기본 설명</slot>
    <slot>기본 본문</slot>
  </template>
  <span slot="라벨">채운 라벨</span>
</my-badge>
```

> **보이는 것** — 「채운 라벨」이 파란 굵은 글씨로 나오고 그 옆에 「기본 설명」이 나온다. 스크립트가 한 줄도 없다.\
> ★ **「기본 본문」은 안 나온다** — 소스의 **줄바꿈 공백**(`#text` 두 개)이 이미 이름 없는 칸에 할당됐기 때문이다.\
> **바꿔 볼 것** — `slot="라벨"` 을 지우면(라벨 칸이 기본 내용으로 돌아가고 그 `<span>` 이 이름 없는 칸으로 간다) · `shadowrootmode="open"` → `"zzz"`(그림자가 안 생기고 `<template>` 이 그대로 남아 **화면에는 라이트 DOM 만** 보인다)

*(Chrome 151 headless 실측, 창 폭 780: `shadowRoot.mode = open` · 남은 `<template>` 0개 · `<b>` 의 `color = rgb(37, 99, 235)` · 기본 내용의 그려진 폭이 라벨 칸 `0px` · 설명 칸 `63px` · 본문 칸 `0px`)*

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

**「바꿔 볼 것」에 적은 단언도 따로 던져 확인했다.**

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

## 문법 — 형태와 규칙

HTML 은 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 네 가지

```html
<template id="틀"><li>복제해서 쓸 조각</li></template>

<my-card>
  <template shadowrootmode="open">
    <slot name="제목">기본 제목</slot>
    <slot>기본 본문</slot>
  </template>
  <h2 slot="제목">바깥이 준 제목</h2>
</my-card>
```

### 금지 사례 — 아무 일도 안 일어나는 자리

```html
<template><script>console.log("안 돈다")</script></template>
<template><img src="a.png"></template>
<my-card><template shadowrootmode="zzz"><p>안 생긴다</p></template></my-card>
<my-card><template shadowrootmode="open"><slot name="제목">기본</slot></template><h2 slot="제묵">오타</h2></my-card>
```

- 첫 줄은 **안 돌고**, 둘째 줄은 **안 받아 온다**((1)).
- 셋째 줄은 **그림자가 안 생기고** `<template>` 이 그대로 남는다((3)).
- 넷째 줄의 오타는 **어느 칸에도 안 들어가고 화면에서 사라진다**((5)). ★ **네 줄 다 예외가 안 난다.**

### 어디서 헷갈리나

```text
  「숨긴 것」과 「안 사는 것」

  display: none 인 <div>            <template>
  ----------------------            ----------
  트리에 있다                        트리에 없다
  querySelectorAll 에 잡힌다          안 잡힌다
  안의 <img> 를 받는다                안 받는다
  안의 <script> 가 돈다               안 돈다
  안 하는 것은 「그리는 일」뿐          아무 일도 안 한다
```

- **`<template>` 은 `display: none` 이 아니다.** 「안 보이는 것」이 아니라 **문서에 없는 것**이다.
- **`<template>` 은 `<head>`·`<body>`·`<table>` 안 어디에나 놓을 수 있다.** 콘텐츠 모델의 특례다([05번 주제](../05-content-categories-and-models/2-summary.md)).
- **`shadowrootmode` 는 `<template>` 의 속성**이지 호스트의 속성이 아니다.
- **`slot` 속성은 라이트 DOM 쪽**, `<slot>` 요소는 **섀도 쪽**에 있다. 이름이 같아 헷갈린다.
- **커스텀 요소 이름에는 대시가 있어야 한다.** 없으면 `HTMLUnknownElement` 가 되고 영영 업그레이드되지 않는다.

## 어디서 틀리나

### 1. `<template>` 안의 이미지가 미리 받아져 있다고 믿는다

**안 받는다.** (1) 의 요청 로그에 `?in` 이 한 줄도 없다.\
★ 「미리 받아 두려고」 `<template>` 에 넣는 것은 **정확히 반대 효과**다.

### 2. `--dump-dom` 에 안 보이니 그림자가 안 생겼다고 읽는다

**생겼다.** (3) 의 덤프에는 없지만 (4) 의 프로브가 `ShadowRoot(mode=open)` 을 돌려준다.\
★ **「도구가 못 보는 것」과 「없는 것」은 다르다.**

```text
  세 곳의 <p> 가 세 칸에서 다 다르게 나온다

                       --dump-dom   querySelectorAll   화면
  <template> 안         보인다          안 잡힌다       안 나온다
  그림자 안             안 보인다        안 잡힌다       나온다      ★ 창 ①이 사각지대
  display:none          보인다          잡힌다          안 나온다
```

### 3. `<template>` 안의 내용을 `querySelector` 로 찾는다

**못 찾는다.** `document.querySelector` 는 **문서 트리**만 본다.\
★ `틀.content.querySelector(…)` 라야 한다 — 그 API 표면은 **web-api 갈래의 05번이 정본**이다.

### 4. `<slot>` 의 기본 내용이 나올 줄 안다

**공백이 이미 채웠을 수 있다.** demo 에서 **이름 없는 칸**이 그랬다.\
★ 기본 내용을 확실히 쓰려면 **이름 있는 칸**으로 두거나 **호스트 안의 공백을 없애야** 한다.

### 5. `closed` 그림자를 나중에 스크립트로 열 수 있다고 본다

**못 연다.** (4) 에서 `shadowRoot` 가 `null` 이다.\
★ `closed` 는 **보안 경계가 아니라 규율**이지만, 선언적으로 만든 것은 **참조를 받을 자리조차 없다.**

### 6. 대시 없는 이름을 커스텀 요소로 쓴다

**영영 업그레이드되지 않는다.** (6) 에서 `HTMLUnknownElement` 였다.\
★ 이름 규칙이 **파서 단계에서** 이미 갈린다.

## 구현 세부사항 대 언어 보장

★ **HTML 은 명세가 오류 복구까지 정한 언어**라 「구현 정의」 칸이 작다. 세 층으로 갈라 적는다.

| 층 | 무엇을 보장하나 | 이 주제에서 |
|---|---|---|
| **명세(HTML)** | `<template>` 의 내용은 **별도 `DocumentFragment`**·별도 문서 | (1) 의 `ownerDocument !== document` |
| **명세(HTML)** | 그 안의 스크립트·자원은 **동작하지 않는다** | (1) |
| **명세(HTML)** | `<template>` 안도 **파서의 삽입 모드**를 따른다 | (2) 의 `<td>` |
| **명세(HTML)** | `shadowrootmode` 가 `open`/`closed` 일 때만 섀도 루트가 된다 | (3) |
| **명세(DOM)** | `closed` 섀도 루트는 `element.shadowRoot` 로 안 준다 | (4) |
| **명세(HTML/DOM)** | 채워진 슬롯은 기본 내용을 **안 쓴다** | (5) |
| **명세(HTML)** | 커스텀 요소 이름은 **대시를 포함**해야 한다 | (6) |
| **구현(Blink)** | `outerHTML` 이 `<template>` 은 직렬화하고 **섀도는 안 한다** | (2)·(3) |
| **구현(Blink)** | `innerText` 가 **그림자 안을 안 본다** | (5) |
| **구현(Blink)** | 잘못된 `shadowrootmode` 의 **콘솔 문구** | (3) |
| **이 판의 관찰** | 기본 내용의 **픽셀 폭** | 글꼴에 달렸다 — **0 이냐 아니냐**만 쓴다 |

**도구가 못 보는 것**

- ★★★ **`--dump-dom` 은 섀도 트리를 못 본다.** 이 주제의 가장 큰 한계다 — 창 ①이 **통째로 사각지대**라 창 ②로 갈아탔다((3)·(4)).
- ★★ **`innerText` 도 섀도 안을 못 본다.** 그래서 「화면에 나왔나」를 **좌표로** 따로 쟀다((5)).
- **접근성 트리에서 슬롯이 어떻게 평탄화되나.** 이 배치는 슬롯 쪽 접근성 트리를 **안 봤다**(11·12 에서 쓴 도구를 여기에 적용하지 않았다).
- **`<template>` 을 복제해 붙이는 순간의 동작.** 그것은 **web-api 05번의 표면**이라 던지지 않았다.
- **다른 엔진.** Chrome 하나뿐이라 이식성을 주장할 수 없다. **선언적 Shadow DOM 은 이 묶음에서 가장 새 표면**이라 특히 그렇다.

## 언제 쓰고 언제 안 쓰나

- **`<template>` 은 「나중에 복제할 조각」에만** — 지금 보여 줄 것은 그냥 문서에 둔다.
- **미리 받게 하려고 `<template>` 에 넣지 마라** — 정확히 반대다((1)).
- **선언적 Shadow DOM 은 서버 렌더와 짝이다** — 스크립트 없이 **첫 화면부터** 캡슐화된 마크업을 줄 수 있다.
- **`closed` 는 기본으로 쓰지 마라** — 디버깅·테스트가 막힌다. **`open` 이 기본값 취급**이다.
- **`<slot>` 의 기본 내용에 기대려면 이름을 붙여라** — 이름 없는 칸은 **공백이 먼저 채운다**.
- **커스텀 요소의 동작 자체는 여기서 안 짠다** — web-api 갈래 13번의 몫이다.

## 핵심 문장

1. **`<template>` 안은 「숨긴 것」이 아니라 「아직 문서가 아닌 것」이다 — 다른 문서에 산다.**
2. **그 안의 이미지는 받아 오지도 않는다 — 요청 로그가 그것을 말한다.**
3. **`--dump-dom` 은 `<template>` 안은 보여 주고 섀도 안은 안 보여 준다.**
4. **선언적 Shadow DOM 은 이 판에서 동작하고, 파싱이 끝나면 그 `<template>` 은 트리에 없다.**
5. **`closed` 로 선언한 그림자는 페이지 스크립트에도 `null` 이다.**
6. **그림자를 글자로 되돌리려면 마크업에 `shadowrootserializable` 이 미리 있어야 한다.**
7. **`<slot>` 의 기본 내용은 아무도 안 채운 칸에서만 나온다 — 공백도 채운 것으로 친다.**
8. **커스텀 요소는 이름에 대시가 있어야 하고, `define` 하는 순간 이미 있던 요소가 업그레이드된다.**

## 관련 자료

- [05번 주제 — 콘텐츠 카테고리와 콘텐츠 모델](../05-content-categories-and-models/2-summary.md) — `<template>` 이 **어디에나 놓일 수 있는** 특례의 근거.
- [03번 주제 — 파서와 오류 복구](../03-parser-and-error-recovery/2-summary.md) — `<template>` 안에서도 **삽입 모드**가 그대로 적용되는 것((2) 의 `<td>`).
- [08번 주제 — 스크립트 로딩](../08-script-loading/2-summary.md) — **요청 로그라는 창**과 「실행 안 됨의 두 가지」는 그쪽이 정본이다.
- web-api 갈래 목록([`web-api/README.md`](../../../../web-api/README.md))의 **12번** — **Shadow DOM 의 API 가 정본이다** — `attachShadow`·캡슐화가 선택자·스타일·이벤트에 하는 일·`::part`. 여기는 **`shadowrootmode` 라는 마크업 표면**까지.
- web-api 갈래 목록([`web-api/README.md`](../../../../web-api/README.md))의 **13번** — **커스텀 요소 수명주기가 정본이다.** 여기는 **업그레이드 시점 맛보기**까지.
- web-api 갈래 목록([`web-api/README.md`](../../../../web-api/README.md))의 **05번** — `DocumentFragment` 와 **`<template>` 복제**는 그쪽이 정본이다.
- [`history/web/05-웹플랫폼-API.md`](../../../../../../history/web/05-웹플랫폼-API.md) §6 — **웹 컴포넌트가 왜 생겼나**는 그쪽이다. 여기는 **오늘 마크업으로 무엇이 되나**까지.
- [11번 주제 — 구획 요소와 랜드마크](../11-sectioning-and-landmarks/2-summary.md) — 그림자 안의 마크업도 **같은 시맨틱 규칙**을 받는다.

## 용어 풀이

- **`<template>`** — 파싱은 되지만 **문서 트리에 들어가지 않는** 조각을 담는 요소.
- **`content`** — `<template>` 의 내용이 담긴 `DocumentFragment`. **`ownerDocument` 가 문서와 다르다.**
- **inert(불활성)** — 파싱은 됐는데 스크립트도 안 돌고 자원도 안 받는 상태.
- **`DocumentFragment`** — 부모가 없는 노드 묶음. 문서에 붙이면 **자기는 사라지고 자식만** 들어간다.
- **Shadow DOM** — 호스트 요소가 가진 **자기만의 트리**. 바깥 선택자가 못 들어간다.
- **선언적 Shadow DOM** — 스크립트 없이 **마크업만으로** 섀도 루트를 만드는 것. `<template shadowrootmode>` 가 그 표면이다.
- **`shadowrootmode`** — `open`(스크립트가 `shadowRoot` 로 잡을 수 있다) / `closed`(못 잡는다).
- **`shadowrootserializable`** — 그 섀도를 **`getHTML()` 로 다시 글자로 뽑을 수 있게** 허락하는 속성.
- **라이트 DOM** — 호스트의 **문서 쪽 자식들.** 슬롯에 할당될 후보다.
- **`<slot>`** — 라이트 DOM 을 섀도 안으로 **투영하는 자리.** 비었으면 **기본 내용**이 그려진다.
- **슬롯 할당(slot assignment)** — 라이트 자식의 `slot` 속성 값과 `<slot name>` 을 맞춰 넣는 것. **안 맞으면 아무 데도 안 간다.**
- **업그레이드(upgrade)** — 이미 트리에 있던 요소가 `customElements.define` 시점에 **그 클래스로 바뀌는** 것.

## 더 들어가면

- **왜 `<template>` 안이 안 사나** — 그 내용은 **「템플릿 내용 소유 문서」라는 별도 문서**에 담긴다. 자원 로딩·스크립트 실행은 **문서에 딸린 일**이라, 문서가 다르면 아무 일도 안 일어난다. (1) 의 `ownerDocument !== document` 가 그 한 줄짜리 증거다.
- **왜 선언적 Shadow DOM 이 필요했나** — `attachShadow` 는 **스크립트가 돌아야** 하므로 서버가 보낸 첫 HTML 에는 그림자가 없다. 그래서 컴포넌트가 **화면에 늦게 나타나거나 한 번 깜빡였다.** 마크업만으로 만들 수 있게 한 것이 이 표면이다.
- **왜 직렬화가 기본 「안 보임」인가** — 섀도는 **캡슐화**가 목적이다. `innerHTML` 로 아무나 안을 꺼내 갈 수 있으면 그 목적이 깨진다. 그래서 **마크업이 `shadowrootserializable` 로 명시적으로 허락**해야 뽑힌다((4)).
- **`<slot>` 이 왜 「투영」인가** — 라이트 자식은 **옮겨지지 않는다.** 트리에서는 여전히 호스트의 자식이고, **그려질 때만** 슬롯 자리로 간다. (5) 에서 `textContent` 와 `innerText` 가 갈린 것이 그 흔적이다.
