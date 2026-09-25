# html/syntax/05 — 콘텐츠 카테고리와 콘텐츠 모델: 어디에 무엇을 넣을 수 있나 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 [「Kinds of content」](https://html.spec.whatwg.org/multipage/dom.html#kinds-of-content)·[「Transparent content models」](https://html.spec.whatwg.org/multipage/dom.html#transparent-content-models)·[「Parsing HTML documents」](https://html.spec.whatwg.org/multipage/parsing.html) 절. 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에 실제로 띄워 `--dump-dom` 과 DOM 프로브로 읽은 것이다. 하네스는 [3-answer.md](3-answer.md) 의 `## 실행 검증` 절에 있다.\
> ★ **엔진은 Chrome 하나다.** Firefox 155.0.1 이 설치돼 있으나 이 환경에서 headless 산출이 **조용히 실패**하고 WebKit 은 없다. 그러므로 이 갈래는 **「이식성」을 주장하지 않는다.**
> **버전** — HTML 에는 언어 버전이 없다. 지원 상태는 **Baseline** 으로 읽는다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.
> ★★ **이 주제의 본체는 창 ① (`--dump-dom`)이다** — 「내가 쓴 중첩이 트리에서 어떤 모양이 됐나」가 전부이기 때문이다. 창 ② 는 **75개를 한 번에 세는** 자리에서만 쓴다. 창 넷의 정의는 [01번](../01-document-skeleton/2-summary.md) 의 「이 갈래의 창」 절에 있다.

**이 판의 Chrome**

```text
===== google-chrome --version =====
Google Chrome 151.0.7922.173 
(exit 0)
```

### 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | Chrome 판 번호 · 실행 시각 | 판이 오르면 바뀐다 |
| **흔들린다** | demo 의 높이·너비 픽셀 | 글꼴·창 폭에 달렸다 — **갈린다는 사실**만 근거로 쓴다 |
| **안 흔들린다** | **`--dump-dom` 트리 전체** | 파싱 알고리즘이 명세에 있다 |
| **안 흔들린다** | 75개의 A/B/C 갈래와 그 개수 | 〃 |
| **안 흔들린다** | 블록의 `(exit N)` | 파서는 실패하지 않는다([03번 주제](../03-parser-and-error-recovery/2-summary.md)) |

## 한눈에 — 쉽게 말하면

**★ 「어디에 무엇을 넣을 수 있나」를 정한 것은 명세이고, 어긴 것을 처리하는 것은 파서다. 그리고 파서는 규정을 반만 안다.**

출입 규정이 있는 건물에 비유한다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 「이 방에는 이런 사람만」이라 적힌 규정집 | **콘텐츠 모델**(명세가 요소마다 정한 것) |
| 사람을 묶은 종류 — 어른 / 아이 / 짐 | **콘텐츠 카테고리**(흐름·구절·임베디드…) |
| 규정집을 **반만** 외운 경비원 | **HTML 파서** |
| 경비가 방문을 닫아 버림 | `<p>` 가 강제로 닫힌다 |
| 경비가 못 본 척 들여보냄 | **무효인데 트리에 그대로 들어간다** |
| 이름표만 떼고 사람만 들여보냄 | 태그가 사라지고 글자만 남는다 |
| 「이 방은 바깥 방 규정을 그대로 쓴다」 | **투명 콘텐츠 모델**(`<a>`·`<ins>`) |

- **카테고리는 태그의 「종류」가 아니라 「자리의 종류」다.** 한 요소가 여러 카테고리에 동시에 들어간다.
- **콘텐츠 모델을 어겨도 에러는 없다.** 대신 셋 중 하나가 일어난다 — 닫히거나, 그냥 들어가거나, 태그가 사라진다.
- ★★ **「파서가 안 고쳤다」와 「유효하다」는 다른 말이다.** `<span>` 안의 `<div>` 는 트리에 그대로 들어가지만 **무효**다.

```text
  내가 쓴 것                   파서가 하는 일 세 가지            트리
  +--------------------+
  | <p>앞<div>안</div> |  --(A) 방문을 닫는다 --------->  p "앞" / div "안"
  +--------------------+          31개 (흐름 콘텐츠)         형제가 된다

  +--------------------+
  | <p>앞<span>안</sp> |  --(B) 그냥 들여보낸다 ------->  p > span "안"
  +--------------------+          35개 (구절·메타데이터)       그대로 중첩

  +--------------------+
  | <p>앞<td>안</td>   |  --(C) 이름표를 뗀다 --------->  p "앞안뒤"
  +--------------------+           9개 (표 전용 요소)        태그만 사라진다
```

```text
  「유효한가」 와 「파서가 고치나」 는 다른 축이다 — 네 칸이 다 있다

                    파서가 고친다            파서가 안 고친다
                +------------------------+------------------------+
    무효하다    | <p><div>                | <span><div>            |
                | <a><a>  <form><form>    | <ul><p>  <label><label>|
                +------------------------+------------------------+
    유효하다    |          (없다)          | <div><p>  <a><div>     |
                +------------------------+------------------------+
                                            ↑ 이 칸이 사고가 난다
```

실무에서 이게 터지는 자리는 **템플릿 엔진이 조각을 끼워 넣을 때**다.\
`<p>{{본문}}</p>` 에 `<div>` 가 든 문자열이 들어오면 **문단이 세 조각으로 쪼개진다** — 그런데 화면은 그럴듯해서 모른다.\
반대로 `<ul>` 안에 `<p>` 를 넣은 것은 **아무 일도 안 일어나서** 몇 년을 모르고 산다.

> **콘텐츠 카테고리(content category)** — 명세가 요소들을 묶어 놓은 이름표. 한 요소가 여럿에 속한다.\
> 예: `<a>` 는 흐름 콘텐츠이면서 구절 콘텐츠이고 대화형 콘텐츠다.

> **콘텐츠 모델(content model)** — 「이 요소 **안에** 무엇이 올 수 있나」를 정한 규칙.\
> 예: `<p>` 의 콘텐츠 모델은 「구절 콘텐츠」라서 `<div>`(흐름이지만 구절이 아닌 것)를 못 담는다.

## 이 주제가 답하려는 질문

1. **카테고리는 무엇을 위해 있나.** 태그를 외우는 것과 무엇이 다른가.
2. **콘텐츠 모델을 어기면 무슨 일이 일어나나.** 파서가 언제 개입하고 언제 가만히 있나.
3. **「파서가 안 고쳤다」를 「유효하다」로 읽으면 무엇을 놓치나.**

## 동작 방식

### (1) 창 ① — 카테고리는 「자리의 종류」다

**언제 쓰나** — 「이 요소 안에 저 요소를 넣어도 되나」를 판정할 때. 태그 이름이 아니라 **카테고리로** 답한다.

```text
  흐름(flow)     문서 본문에 놓이는 거의 전부
    +---------------------------------------------------+
    |  div  p  ul  table  section  h1  form  pre  hr     |
    |                                                    |
    |   구절(phrasing)   문단 안에 섞이는 글자 수준        |
    |     +------------------------------------------+   |
    |     |  span  em  code  a  img  br  input       |   |
    |     |                                          |   |
    |     |   임베디드(embedded)  바깥 자원을 끌어옴    |   |
    |     |     +---------------------------------+  |   |
    |     |     |  img  video  canvas  iframe     |  |   |
    |     |     |  object  picture(는 아님)        |  |   |
    |     |     +---------------------------------+  |   |
    |     |                                          |   |
    |     |   대화형(interactive)  사용자가 조작함     |   |
    |     |     +---------------------------------+  |   |
    |     |     |  a[href]  button  input  select |  |   |
    |     |     +---------------------------------+  |   |
    |     +------------------------------------------+   |
    +---------------------------------------------------+

    구획(sectioning)  section article aside nav      <- 흐름의 부분집합
    헤딩(heading)     h1~h6  hgroup                  <- 흐름의 부분집합
    메타데이터        link meta style title script base  <- head 에 사는 것들
```

그림 해설 (한 단계씩):

- **구절 콘텐츠는 흐름 콘텐츠의 부분집합이다.** 그래서 `<span>` 은 `<div>` 안에도 `<p>` 안에도 들어간다.
- **`<p>` 의 콘텐츠 모델이 「구절 콘텐츠」다.** 그래서 「`<p>` 안에 `<div>`」가 무효인 것은 **`<div>` 가 구절이 아니기 때문**이다.
- **임베디드·대화형은 구절의 부분집합이다.** `<img>`·`<button>` 이 문단 안에 섞일 수 있는 근거가 이것이다.
- **메타데이터 콘텐츠만 계통이 다르다.** `<head>` 에 사는 것들이고, 그래서 [01번 주제](../01-document-skeleton/2-summary.md)가 그 자리를 따로 다뤘다.

★ 이 그림은 **명세의 정의를 옮긴 것**이지 실행으로 잰 것이 아니다. 아래 (2) 가 **실행으로 잰 판**이다.

### (2) 창 ② 전수 — `<p>` 안에 75개를 던졌다

**언제 쓰나** — 「어디까지 파서가 개입하나」를 산문이 아니라 **수로** 말할 때.

`<p id="t-xxx">앞<xxx>안</xxx>뒤</p>` 를 **75벌** 만들어 한 문서에 담고, 문단이 닫혔는지·안에 들어갔는지·태그가 사라졌는지를 셌다.\
★ 이 파일만 **프로브 스크립트를 문서에 넣었다** — 여기서 읽는 것은 트리의 직렬화가 아니라 **세 갈래의 개수**라서 오염될 것이 없다.

```text
===== 소스: html05b-category-probe.html =====
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>p 안에 던져 본 요소 75개</title>
</head>
<body>
<p id="t-span">앞<span>안</span>뒤</p>
<p id="t-em">앞<em>안</em>뒤</p>
<p id="t-a">앞<a>안</a>뒤</p>
<p id="t-code">앞<code>안</code>뒤</p>
<p id="t-img">앞<img>안</img>뒤</p>
<p id="t-br">앞<br>안</br>뒤</p>
<p id="t-input">앞<input>안</input>뒤</p>
<p id="t-button">앞<button>안</button>뒤</p>
<p id="t-label">앞<label>안</label>뒤</p>
<p id="t-select">앞<select>안</select>뒤</p>
<p id="t-textarea">앞<textarea>안</textarea>뒤</p>
<p id="t-video">앞<video>안</video>뒤</p>
<p id="t-canvas">앞<canvas>안</canvas>뒤</p>
<p id="t-object">앞<object>안</object>뒤</p>
<p id="t-iframe">앞<iframe>안</iframe>뒤</p>
<p id="t-output">앞<output>안</output>뒤</p>
<p id="t-progress">앞<progress>안</progress>뒤</p>
<p id="t-meter">앞<meter>안</meter>뒤</p>
<p id="t-del">앞<del>안</del>뒤</p>
<p id="t-ins">앞<ins>안</ins>뒤</p>
<p id="t-ruby">앞<ruby>안</ruby>뒤</p>
<p id="t-wbr">앞<wbr>안</wbr>뒤</p>
<p id="t-picture">앞<picture>안</picture>뒤</p>
<p id="t-map">앞<map>안</map>뒤</p>
<p id="t-slot">앞<slot>안</slot>뒤</p>
<p id="t-link">앞<link>안</link>뒤</p>
<p id="t-meta">앞<meta>안</meta>뒤</p>
<p id="t-style">앞<style>안</style>뒤</p>
<p id="t-title">앞<title>안</title>뒤</p>
<p id="t-script">앞<script>안</script>뒤</p>
<p id="t-option">앞<option>안</option>뒤</p>
<p id="t-optgroup">앞<optgroup>안</optgroup>뒤</p>
<p id="t-legend">앞<legend>안</legend>뒤</p>
<p id="t-template">앞<template>안</template>뒤</p>
<p id="t-noscript">앞<noscript>안</noscript>뒤</p>
<p id="t-div">앞<div>안</div>뒤</p>
<p id="t-p">앞<p>안</p>뒤</p>
<p id="t-ul">앞<ul>안</ul>뒤</p>
<p id="t-ol">앞<ol>안</ol>뒤</p>
<p id="t-li">앞<li>안</li>뒤</p>
<p id="t-dl">앞<dl>안</dl>뒤</p>
<p id="t-dt">앞<dt>안</dt>뒤</p>
<p id="t-dd">앞<dd>안</dd>뒤</p>
<p id="t-table">앞<table>안</table>뒤</p>
<p id="t-h1">앞<h1>안</h1>뒤</p>
<p id="t-section">앞<section>안</section>뒤</p>
<p id="t-article">앞<article>안</article>뒤</p>
<p id="t-form">앞<form>안</form>뒤</p>
<p id="t-blockquote">앞<blockquote>안</blockquote>뒤</p>
<p id="t-pre">앞<pre>안</pre>뒤</p>
<p id="t-hr">앞<hr>안</hr>뒤</p>
<p id="t-address">앞<address>안</address>뒤</p>
<p id="t-details">앞<details>안</details>뒤</p>
<p id="t-summary">앞<summary>안</summary>뒤</p>
<p id="t-dialog">앞<dialog>안</dialog>뒤</p>
<p id="t-main">앞<main>안</main>뒤</p>
<p id="t-figure">앞<figure>안</figure>뒤</p>
<p id="t-figcaption">앞<figcaption>안</figcaption>뒤</p>
<p id="t-fieldset">앞<fieldset>안</fieldset>뒤</p>
<p id="t-header">앞<header>안</header>뒤</p>
<p id="t-footer">앞<footer>안</footer>뒤</p>
<p id="t-nav">앞<nav>안</nav>뒤</p>
<p id="t-aside">앞<aside>안</aside>뒤</p>
<p id="t-search">앞<search>안</search>뒤</p>
<p id="t-hgroup">앞<hgroup>안</hgroup>뒤</p>
<p id="t-menu">앞<menu>안</menu>뒤</p>
<p id="t-td">앞<td>안</td>뒤</p>
<p id="t-tr">앞<tr>안</tr>뒤</p>
<p id="t-th">앞<th>안</th>뒤</p>
<p id="t-thead">앞<thead>안</thead>뒤</p>
<p id="t-tbody">앞<tbody>안</tbody>뒤</p>
<p id="t-caption">앞<caption>안</caption>뒤</p>
<p id="t-col">앞<col>안</col>뒤</p>
<p id="t-colgroup">앞<colgroup>안</colgroup>뒤</p>
<p id="t-frameset">앞<frameset>안</frameset>뒤</p>
<script>
const els = ["span", "em", "a", "code", "img", "br", "input", "button", "label", "select", "textarea", "video", "canvas", "object", "iframe", "output", "progress", "meter", "del", "ins", "ruby", "wbr", "picture", "map", "slot", "link", "meta", "style", "title", "script", "option", "optgroup", "legend", "template", "noscript", "div", "p", "ul", "ol", "li", "dl", "dt", "dd", "table", "h1", "section", "article", "form", "blockquote", "pre", "hr", "address", "details", "summary", "dialog", "main", "figure", "figcaption", "fieldset", "header", "footer", "nav", "aside", "search", "hgroup", "menu", "td", "tr", "th", "thead", "tbody", "caption", "col", "colgroup", "frameset"];
const 닫힘 = [], 들어감 = [], 사라짐 = [];
for (const e of els) {
  const p = document.getElementById("t-" + e);
  if (p === null || p.textContent === "앞") 닫힘.push(e);
  else if (p.querySelector(e)) 들어감.push(e);
  else 사라짐.push(e);
}
const 줄바꿈 = (a) => { const r = []; for (let i = 0; i < a.length; i += 6) r.push("    " + a.slice(i, i + 6).join(" ")); return r.join("\n"); };
const o = [];
o.push("던진 요소 = " + els.length + "개");
o.push("");
o.push("[A] p 가 닫힌다 (" + 닫힘.length + "개)");
o.push(줄바꿈(닫힘));
o.push("[B] p 안에 그대로 들어간다 (" + 들어감.length + "개)");
o.push(줄바꿈(들어감));
o.push("[C] 태그만 사라지고 글자는 남는다 (" + 사라짐.length + "개)");
o.push(줄바꿈(사라짐));
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
</body>
</html>
===== dom html05b-category-probe.html | probe =====
던진 요소 = 75개

[A] p 가 닫힌다 (31개)
    div p ul ol li dl
    dt dd table h1 section article
    form blockquote pre hr address details
    summary dialog main figure figcaption fieldset
    header footer nav aside search hgroup
    menu
[B] p 안에 그대로 들어간다 (35개)
    span em a code img br
    input button label select textarea video
    canvas object iframe output progress meter
    del ins ruby wbr picture map
    slot link meta style title script
    option optgroup legend template noscript
[C] 태그만 사라지고 글자는 남는다 (9개)
    td tr th thead tbody caption
    col colgroup frameset
(exit 0)
```

```text
   던진 75개                 파서가 한 처분
   +-------------+
   |             |--(A) 닫는다 31개 ---> 흐름이면서 구절이 아닌 것 전부
   |   <p> 안에  |                       div p ul ol li dl dt dd table h1
   |   던진 요소  |                       section article form blockquote pre
   |             |                       hr address details summary dialog
   |             |                       main figure figcaption fieldset
   |             |                       header footer nav aside search
   |             |                       hgroup menu
   |             |
   |             |--(B) 들여보낸다 35개 -> 구절 콘텐츠 + 메타데이터 콘텐츠
   |             |                       span em a code img br input button
   |             |                       label select textarea video canvas
   |             |                       object iframe output progress meter
   |             |                       del ins ruby wbr picture map slot
   |             |                       link meta style title script
   |             |                       option optgroup legend template noscript
   |             |
   |             |--(C) 이름표를 뗀다 9개 -> 표 전용 + frameset
   +-------------+                       td tr th thead tbody caption
                                         col colgroup frameset
```

그림 해설:

- **(A) 31개는 전부 「흐름이지만 구절이 아닌 것」이다.** 파서에는 「**`<p>` 를 닫는 시작 태그 목록**」이 박혀 있고, 그 목록이 카테고리와 거의 겹친다.
- **(B) 35개 중 `option`·`optgroup`·`legend`·`link`·`meta`·`style`·`title`·`script`·`template`·`noscript` 는 구절 콘텐츠가 아니다.** 그런데도 들어갔다 — ★ **파서는 콘텐츠 모델을 강제하지 않는다.** 목록에 없으면 그냥 넣는다.
- **(C) 9개는 「표 전용 요소」다.** 표 안이 아닌 자리에서 이 태그들은 **무시**되고 안의 글자만 남는다(`<td>안</td>` → `안`). 03번이 다룬 **foster parenting** 과 같은 집안의 규칙이다.
- ★ **그래서 세 갈래는 카테고리와 「거의」 겹치고 완전히 겹치지 않는다.** 겹치는 부분이 (A), 어긋나는 부분이 (B) 의 꼬리 10개다. **이 어긋남이 이 주제의 핵심**이다.

### (3) 파서가 고치는 것 — 중첩이 풀린다

**언제 쓰나** — 같은 요소를 겹쳐 쓴 마크업을 만났을 때. `<a>` 안의 `<a>` 가 대표다.

★ [03번 주제](../03-parser-and-error-recovery/2-summary.md)가 `<p><div>` 를 이미 다뤘으므로 여기서는 **다른 조합 다섯**을 던진다.

```text
===== 소스: html05b-a-in-a.html =====
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>a 안에 쓴 a</title>
</head>
<body>
<a href="/밖">밖<a href="/안">안</a>뒤</a>
<button>겉<button>속</button></button>
<label>겉<label>속</label></label>
<form action="/1"><form action="/2"><input name="x"></form></form>
<details>겉<details>속</details></details>
</body>
</html>
===== dom html05b-a-in-a.html =====
<!DOCTYPE html>
<html lang="ko"><head>
<meta charset="utf-8">
<title>a 안에 쓴 a</title>
</head>
<body>
<a href="/밖">밖</a><a href="/안">안</a>뒤
<button>겉</button><button>속</button>
<label>겉<label>속</label></label>
<form action="/1"><input name="x"></form>
<details>겉<details>속</details></details>


</body></html>
(exit 0)
```

```text
   소스                                      트리
   +---------------------------------+      +--------------------------------+
   | <a href="/밖">밖                 |      | a[href=/밖] "밖"               |
   |   <a href="/안">안</a>뒤</a>      | ==>  | a[href=/안] "안"               |
   +---------------------------------+      | #text "뒤"                     |
                                            +--------------------------------+
      중첩이 형제로 펴진다 · 「뒤」는 두 a 밖으로 나온다

   +---------------------------------+      +--------------------------------+
   | <form action="/1">               |      | form[action=/1]                |
   |   <form action="/2">             | ==>  |   input[name=x]                |
   |     <input name="x"></form></f>  |      +--------------------------------+
   +---------------------------------+
      안쪽 form 은 통째로 사라지고 input 은 바깥 form 의 자식이 된다
```

그림 해설:

- **`<a>` 안의 `<a>`** — 바깥 `<a>` 가 먼저 닫히고 안쪽이 **형제**가 된다. 「뒤」까지 밖으로 밀린다. 파서의 **adoption agency algorithm** 이 하는 일이다.
- **`<button>` 안의 `<button>`** — 같은 모양으로 펴진다(`겉` / `속` 두 형제).
- **`<form>` 안의 `<form>`** — 모양이 다르다. **안쪽 `<form>` 시작 태그가 통째로 무시**되고 `<input>` 은 바깥 폼의 자식이 된다. 「형제로 편다」가 아니라 「**없던 일로 한다**」다.
- ★ **세 경우의 처분이 서로 다르다.** 「중첩을 금지한다」는 한 문장으로 묶으면 트리를 못 맞춘다.

### (4) ★ 파서가 안 고치는 것 — 여기가 이 주제의 값이다

**언제 쓰나** — 「경고가 안 났으니 맞겠지」라고 생각할 때. **가장 조용한 무효**가 여기 있다.

```text
===== 소스: html05b-span-div.html =====
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>span 안에 쓴 div</title>
</head>
<body>
<span>앞<div>span 안의 div</div>뒤</span>
<em>앞<section>em 안의 section</section>뒤</em>
<code>앞<ul><li>code 안의 목록</li></ul>뒤</code>
</body>
</html>
===== dom html05b-span-div.html =====
<!DOCTYPE html>
<html lang="ko"><head>
<meta charset="utf-8">
<title>span 안에 쓴 div</title>
</head>
<body>
<span>앞<div>span 안의 div</div>뒤</span>
<em>앞<section>em 안의 section</section>뒤</em>
<code>앞<ul><li>code 안의 목록</li></ul>뒤</code>


</body></html>
(exit 0)
```

```text
   소스                                     트리
   <span>앞<div>…</div>뒤</span>    ==>    span > (#text, div, #text)
   <em>앞<section>…</section>뒤</em> ==>   em   > (#text, section, #text)
   <code>앞<ul><li>…</ul>뒤</code>  ==>    code > (#text, ul, #text)

   한 글자도 안 바뀌었다. 그런데 셋 다 콘텐츠 모델 위반이다.
```

```text
===== 소스: html05b-ul-p.html =====
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>ul 안에 쓴 p</title>
</head>
<body>
<ul><p>목록 안의 문단</p><li>진짜 항목</li></ul>
<ol><div>번호 목록 안의 div</div><li>항목</li></ol>
<dl><p>정의 목록 안의 문단</p><dt>용어</dt><dd>뜻</dd></dl>
</body>
</html>
===== dom html05b-ul-p.html =====
<!DOCTYPE html>
<html lang="ko"><head>
<meta charset="utf-8">
<title>ul 안에 쓴 p</title>
</head>
<body>
<ul><p>목록 안의 문단</p><li>진짜 항목</li></ul>
<ol><div>번호 목록 안의 div</div><li>항목</li></ol>
<dl><p>정의 목록 안의 문단</p><dt>용어</dt><dd>뜻</dd></dl>


</body></html>
(exit 0)
```

```text
   소스                                     트리
   <ul><p>문단</p><li>항목</li></ul>  ==>   ul > (p, li)      <- p 가 ul 의 자식으로 남는다
   <ol><div>…</div><li>…</li></ol>   ==>   ol > (div, li)
   <dl><p>…</p><dt>…</dt><dd>…</dd>  ==>   dl > (p, dt, dd)
```

그림 해설:

- **`<ul>` 의 콘텐츠 모델은 「0개 이상의 `<li>`(와 스크립트 지원 요소)」다.** `<p>` 는 거기에 없다 — **무효다.**
- 그런데 **파서는 아무것도 안 한다.** `<p>` 가 `<ul>` 의 자식으로 그대로 남는다.
- **`<span>` 안의 `<div>`** 도 마찬가지다. `<span>` 의 콘텐츠 모델은 구절 콘텐츠이고 `<div>` 는 구절이 아니다 — 무효인데 트리는 소스 그대로다.
- ★★ **「`<p>` 안의 `<div>`」가 고쳐지는 이유는 콘텐츠 모델이 아니다** — 파서에 **`<p>` 를 닫는 목록**이 박혀 있기 때문이다. `<span>` 에는 그런 목록이 없다. **같은 위반인데 처분이 갈리는 근거가 카테고리가 아니라 파서의 목록**이다.
- **`<label>` 안의 `<label>`·`<details>` 안의 `<details>`** 도 (3) 의 블록에서 **안 고쳐진 채 중첩으로 남았다** — `<a>`·`<button>` 과 갈린다.

### (5) 투명 콘텐츠 모델 — `<a>` 는 부모를 따라간다

**언제 쓰나** — 링크로 카드 전체를 감쌀 때. 「`<a>` 안에 `<div>` 를 넣어도 되나」의 답이 「**부모를 봐라**」다.

```text
===== 소스: html05b-transparent.html =====
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>투명 콘텐츠 모델</title>
</head>
<body>
<div><a href="/t"><div>div 안의 a 안의 div</div></a></div>
<p><a href="/t"><div>p 안의 a 안의 div</div></a></p>
<div><a href="/t"><button>a 안의 button</button></a></div>
<div><ins><h2>ins 안의 제목</h2></ins></div>
<p><ins><h2>p 안의 ins 안의 제목</h2></ins></p>
</body>
</html>
===== dom html05b-transparent.html =====
<!DOCTYPE html>
<html lang="ko"><head>
<meta charset="utf-8">
<title>투명 콘텐츠 모델</title>
</head>
<body>
<div><a href="/t"><div>div 안의 a 안의 div</div></a></div>
<p><a href="/t"></a></p><div><a href="/t">p 안의 a 안의 div</a></div><p></p>
<div><a href="/t"><button>a 안의 button</button></a></div>
<div><ins><h2>ins 안의 제목</h2></ins></div>
<p><ins></ins></p><h2>p 안의 ins 안의 제목</h2><p></p>


</body></html>
(exit 0)
```

```text
   부모가 div 일 때 (유효)                   부모가 p 일 때 (무효)
   +---------------------------+            +---------------------------+
   | <div>                     |            | <p>                       |
   |   <a href="/t">           |            |   <a href="/t">           |
   |     <div>…</div>          |            |     <div>…</div>          |
   |   </a>                    |            |   </a>                    |
   | </div>                    |            | </p>                      |
   +---------------------------+            +---------------------------+
             ↓ 트리                                    ↓ 트리
   div > a > div                            p > a(빈 것)
   한 글자도 안 바뀐다                        div > a > "p 안의 a 안의 div"
                                            p(빈 것)
                                              a 가 새로 복제돼 옮겨 간다
```

그림 해설:

- **`<a>` 의 콘텐츠 모델은 「투명」이다** — 「부모의 콘텐츠 모델을 그대로 쓴다」는 뜻이다.
- 부모가 `<div>`(흐름 콘텐츠를 받는다)면 `<a>` 안의 `<div>` 는 **유효**하고 트리도 그대로다.
- 부모가 `<p>`(구절만 받는다)면 같은 `<a><div>` 가 **무효**가 되고, `<p>` 가 닫히면서 **`<a>` 가 새 위치에 복제된다** — 트리에 `<a>` 가 **둘**이 된다.
- **`<ins>` 도 투명이다.** `<div><ins><h2>` 는 그대로 남고, `<p><ins><h2>` 는 `<h2>` 가 `<p>` 밖으로 밀려나며 `<ins>` 는 **빈 껍데기**만 남는다.
- ★ **투명 모델이 「아무거나 된다」가 아니다.** 판정을 **한 단계 위로 미루는 것**이다.

### (6) 부모 없이 쓴 자식 — `<td>` 만 사라진다

**언제 쓰나** — 조각 템플릿을 부모 없이 단독 렌더할 때.

```text
===== 소스: html05b-orphan.html =====
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>부모 없이 쓴 자식 요소</title>
</head>
<body>
<li>목록 밖의 li</li>
<dt>목록 밖의 dt</dt>
<td>표 밖의 td</td>
<option>select 밖의 option</option>
<legend>fieldset 밖의 legend</legend>
<figcaption>figure 밖의 figcaption</figcaption>
<summary>details 밖의 summary</summary>
</body>
</html>
===== dom html05b-orphan.html =====
<!DOCTYPE html>
<html lang="ko"><head>
<meta charset="utf-8">
<title>부모 없이 쓴 자식 요소</title>
</head>
<body>
<li>목록 밖의 li</li>
<dt>목록 밖의 dt</dt>
표 밖의 td
<option>select 밖의 option</option>
<legend>fieldset 밖의 legend</legend>
<figcaption>figure 밖의 figcaption</figcaption>
<summary>details 밖의 summary</summary>


</body></html>
(exit 0)
```

```text
   던진 것                   트리
   <li>…</li>       ==>     li      그대로
   <dt>…</dt>       ==>     dt      그대로
   <option>…        ==>     option  그대로
   <legend>…        ==>     legend  그대로
   <figcaption>…    ==>     figcaption 그대로
   <summary>…       ==>     summary 그대로
   <td>…</td>       ==>     #text "표 밖의 td"   <- 이것만 태그가 사라진다
```

그림 해설:

- **일곱 중 여섯은 그대로 남는다.** `<ul>` 없는 `<li>`, `<select>` 없는 `<option>` 이 전부 무효인데 **아무 일도 안 일어난다.**
- **`<td>` 하나만 사라진다.** 표 관련 태그는 「**표 안이 아니면 무시**」라는 규칙이 파서에 따로 있기 때문이다 — (2) 의 (C) 9개와 같은 규칙이다.
- ★ **그래서 「부모 없는 자식」을 한 덩어리로 외우면 틀린다.** 표 계열만 다르다.

### (7) demo — 파서가 안 고쳤는데 화면은 갈라진다

```html demo
<span class="s">앞<div class="d">span 안의 div</div>뒤</span>
<style>
  .s { border: 2px solid #2563eb; padding: 4px; }
  .d { border: 2px dashed #b91c1c; padding: 4px; }
</style>
```

> **보이는 것** — 파란 실선(`span`)이 **세 조각으로 끊겨** 보인다. 「앞」 한 조각, 빨간 점선 상자(`div`)가 줄을 통째로 차지한 뒤, 「뒤」가 또 한 조각. 트리는 `span > div` 그대로인데 **상자는 셋으로 쪼개진다.**\
> **바꿔 볼 것** — `.d` 에 `display: inline` 을 더하면 → 끊김이 사라지고 `span` 의 높이가 **96에서 36으로** 줄어든다 · 바깥 `<span>` 을 `<div>` 로 바꾸면 → 높이는 **96 그대로**다(갈라진 원인이 「span 이라서」가 아니라 **블록 상자가 인라인 흐름을 끊어서**임이 드러난다).
>
> *(Chrome 151 headless 실측, 창 폭 780: `span` 이 만든 상자 3개 · `div` 가 만든 상자 1개 · `div` 너비 764 · `span` 높이 96)*

★ 「보이는 것」과 「바꿔 볼 것」의 단언을 **각각 따로 던져** 확인했다 — [3-answer.md](3-answer.md) 의 `## 실행 검증` 절에 두 블록이 있다.

## 문법 — 형태와 규칙

HTML 은 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 판정하는 순서

```text
  1. 넣으려는 요소가 어느 카테고리인가        <- img 는 흐름·구절·임베디드
  2. 담으려는 요소의 콘텐츠 모델이 무엇인가    <- p 는 「구절 콘텐츠」
  3. 1 이 2 에 들어가나                      <- 들어간다 -> 유효
  4. (투명이면) 한 단계 위로 올라가 다시 1 부터
```

### 금지 사례 — 무효한데 **파서가 안 고쳐서** 조용한 것

```html
<span>앞<div>블록</div>뒤</span>
<ul><p>목록 안의 문단</p><li>항목</li></ul>
<label>겉<label>속</label></label>
<li>부모 없는 항목</li>
<p><a href="/x"><div>카드 전체</div></a></p>
```

### 어디서 헷갈리나

- **`<div>` 안에는 아무거나 되나** — 흐름 콘텐츠는 된다. `<td>`·`<option>` 은 흐름이 아니라서 **안 된다.**
- **`<a>` 로 카드를 감싸도 되나** — 부모가 흐름을 받으면 **된다**(투명 모델). `<p>` 안에서는 안 된다.
- **`<button>` 안에 `<div>`** — `<button>` 의 콘텐츠 모델은 구절이라 **무효**다. 그런데 파서는 (2) 의 (B) 처럼 **그냥 넣는다.**

## 어디서 틀리나

### 1. 「에러가 안 나니까 맞다」고 읽는다

HTML 파서는 **절대 멈추지 않는다**([03번 주제](../03-parser-and-error-recovery/2-summary.md)). 그러니 「안 터졌다」는 아무 정보가 아니다.\
이 판에서 던진 무효한 중첩 **15가지가 한 글자도 안 고쳐진 채** 트리에 들어갔다(겹쳐 쓴 것 2 · 구절 안의 블록 3 · 목록 안의 비목록 3 · `<a>` 안의 대화형 1 · 부모 없는 자식 6).

### 2. 「파서가 고치는 것 = 무효한 것」으로 외운다

거꾸로도 앞으로도 틀린다.\
`<p><div>` 는 고치고 `<span><div>` 는 안 고친다 — **둘 다 무효인데** 처분이 갈린다.

### 3. `<p>` 를 「블록이니까 뭐든 담는다」고 본다

`<p>` 의 콘텐츠 모델은 **구절 콘텐츠**다. 「블록/인라인」은 CSS 의 말이고 콘텐츠 모델은 그 말을 쓰지 않는다.\
★ 겹치는 곳이 많아서 헷갈린다 — 그런데 `<option>`·`<legend>` 처럼 **CSS 축으로는 설명이 안 되는** 것들이 있다.

### 4. 투명 모델을 「제한 없음」으로 읽는다

`<a>` 안에 무엇이든 되는 게 아니라 **부모가 받는 것만** 된다.\
`<p>` 안의 `<a><div>` 는 이 판에서 **`<a>` 가 둘로 복제되는** 트리를 만들었다.

### 5. 표 조각을 단독으로 렌더한다

`<td>` 는 표 밖에서 **태그가 사라진다.** 조각 템플릿을 `innerHTML` 로 붙이거나 단독 파일로 미리보기 할 때 여기서 무너진다.\
★ 같은 자리에서 `<li>`·`<option>` 은 **멀쩡히 남으므로** 「조각은 다 위험하다」로 외우면 어느 것이 실제로 깨지는지 못 가린다.

### 6. 중첩 금지를 한 규칙으로 외운다

`<a>`·`<button>` 은 **형제로 펴지고**, `<form>` 은 **안쪽이 사라지고**, `<label>`·`<details>` 는 **그대로 중첩된다.** 셋이 다 다르다.

## 구현 세부사항 대 언어 보장

★ **HTML 은 명세가 오류 복구까지 정한 언어**라 「구현 정의」 칸이 작다. 세 층으로 갈라 적는다.

| 층 | 무엇을 보장하나 | 이 주제에서 |
|---|---|---|
| **명세(WHATWG HTML)** | 콘텐츠 모델 — 「무엇이 유효한가」 | `<span>` 안의 `<div>` 는 **무효**다. 카테고리 정의도 여기 |
| **명세(파싱 알고리즘)** | 오류 복구 — 「어긴 것을 어떻게 트리로 만드나」 | `<p>` 를 닫는 태그 목록 · adoption agency · 표 전용 태그 무시 **전부 명세에 있다** |
| **구현(Blink)** | 명세 구현 | 이 판의 출력이 명세와 어긋난 자리를 **찾지 못했다** |
| **이 판의 관찰** | Chrome 151 이 실제로 뱉은 것 | 75개의 31/35/9 갈래 · 15가지의 「안 고침」 |

**도구가 못 보는 것**

- **유효성 자체.** 이 환경에 마크업 검증기가 없다 — 「무효다」는 **명세를 읽어 적은 것**이고 실행으로 판정한 것이 아니다.
- **다른 엔진.** Chrome 하나뿐이라 **이식성을 주장할 수 없다.** 다만 이 주제가 기대는 것이 **명세에 적힌 파싱 알고리즘**이라 다른 엔진도 같을 「이유」는 있다 — 그러나 그것은 **추론이고 관찰이 아니다.**
- **접근성 트리.** 무효한 중첩이 보조 기술에 어떻게 노출되는지는 스크린리더가 없어 **못 잰다.**

## 언제 쓰고 언제 안 쓰나

- **카테고리로 판정한다** — 「`<x>` 안에 `<y>` 가 되나」를 외우지 말고 두 카테고리를 본다. 외울 것은 **카테고리 여섯 개**지 조합 수천 개가 아니다.
- **파서 처분에 기대지 않는다** — 「어차피 고쳐 주니까」로 쓰면 고쳐 주지 않는 절반에서 터진다.
- **조각 템플릿은 부모와 함께 미리보기 한다** — 표 계열은 단독으로는 사라진다.
- **링크로 감쌀 때는 부모를 먼저 본다** — 투명 모델은 판정을 위로 미룬다.

## 핵심 문장

1. **콘텐츠 모델은 명세가 정하고, 어긴 것의 처분은 파서가 정한다. 둘은 다른 규칙이다.**
2. **`<p>` 안에 75개를 던지면 31은 닫히고 35는 들어가고 9는 태그가 사라진다.**
3. **「파서가 안 고쳤다」는 「유효하다」가 아니다 — 이 판에서 일곱 종류가 무효인 채 그대로 들어갔다.**
4. **투명 콘텐츠 모델은 제한 없음이 아니라 판정을 부모로 미루는 것이다.**
5. **표 전용 요소만 「자리가 아니면 무시」라는 별도 규칙을 받는다.**

## 관련 자료

- [03번 주제 — 파서와 오류 복구](../03-parser-and-error-recovery/2-summary.md) — **그쪽은 「파서가 어떻게 트리를 만드나」까지, 여기는 「무엇을 넣어도 되나」부터.** `<p><div>` 는 그쪽이 정본이라 여기서는 다른 조합만 던졌다.
- [01번 주제 — 문서의 뼈대](../01-document-skeleton/2-summary.md) — 메타데이터 콘텐츠와 `<head>` 의 경계. **창 넷의 정의도 그쪽이 정본이다.**
- CSS 갈래 목록([`css/syntax/README.md`](../../../css/syntax/README.md)) — **「블록/인라인」은 CSS 의 말이다.** 콘텐츠 모델과 겹쳐 보이지만 다른 축이다.
- web-api 갈래 목록([`web-api/README.md`](../../../../web-api/README.md))의 **01번** — 노드와 요소, `childNodes` 대 `children`. **DOM API 는 그쪽이 정본이다.**
- 목록의 **10번 주제**(`template`·`slot`) · **11번 주제**(구획 요소) · **17번 주제**(표 구조) — 카테고리를 실제로 쓰는 자리들.

## 용어 풀이

- **콘텐츠 카테고리(content category)** — 요소를 묶은 이름표. 흐름·구절·구획·헤딩·임베디드·대화형·메타데이터.
- **흐름 콘텐츠(flow content)** — 문서 본문에 놓이는 거의 전부. `<div>`·`<p>`·`<table>`·`<span>` 이 다 여기 든다.
- **구절 콘텐츠(phrasing content)** — 문단 안에 섞이는 글자 수준의 것. 흐름의 부분집합.
- **임베디드 콘텐츠(embedded content)** — 문서 밖 자원을 끌어오는 것. `<img>`·`<video>`·`<iframe>`.
- **대화형 콘텐츠(interactive content)** — 사용자 조작을 받는 것. `<a href>`·`<button>`·`<input>`.
- **콘텐츠 모델(content model)** — 「이 요소 안에 무엇이 올 수 있나」. 요소마다 명세가 정한다.
- **투명 콘텐츠 모델(transparent content model)** — 부모의 콘텐츠 모델을 그대로 쓰는 것. `<a>`·`<ins>`·`<del>`·`<map>`.
- **adoption agency algorithm** — 겹쳐 쓴 서식 요소를 파서가 형제로 펴는 절차. `<a>` 안의 `<a>` 가 그 대상이다.
- **foster parenting** — 표 안에 못 들어갈 것을 표 **앞으로** 옮기는 파서 규칙. 03번 주제가 정본이다.

## 더 들어가면

- **명세의 콘텐츠 모델은 「저작 요건」이고 파싱 알고리즘은 「처리 요건」이다.** 앞엣것은 문서를 쓰는 사람에게, 뒤엣것은 브라우저에게 건 규칙이라 **둘이 어긋나는 자리가 생긴다** — 이 주제가 잰 「안 고침」 일곱이 전부 그 틈이다.
- **`<p>` 를 닫는 태그 목록은 명세에 열거돼 있다.** 그래서 (2) 의 (A) 31개는 카테고리에서 유도한 것이 아니라 **목록을 실행으로 되찾은 것**이다.
- **왜 파서에 「모든 콘텐츠 모델」을 안 넣었나** — 넣으면 기존 웹의 절반이 다른 트리가 된다. 03번이 다룬 「**절대 멈추지 않는다**」와 같은 이유의 결과다.
