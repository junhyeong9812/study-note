# html/syntax/05 — 콘텐츠 카테고리와 콘텐츠 모델: 어디에 무엇을 넣을 수 있나 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 돌려** `--dump-dom` 과 DOM 프로브로 읽은 것이다. 하네스는 맨 아래 `## 실행 검증` 절에 있다.\
> 규칙은 [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 로 접지했다 — **「무효하다」는 명세를 읽어 적은 것이고 실행으로 판정한 것이 아니다**(A8).\
> ★ **엔진은 Chrome 하나다** — 이 갈래는 이식성을 주장하지 않는다.
> ★ **이 주제의 본체는 창 ① (`--dump-dom`)이다.** 창 ② 는 75개를 한 번에 세는 A1 에서만 쓴다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 31 / 35 / 9 로 갈린다 — 그리고 35 쪽이 카테고리와 어긋난다

**출력** (Chrome 151 headless)

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

**왜 그런가**

- **(A) 닫히는 31개는 「흐름이면서 구절이 아닌 것」과 거의 같다.** 파서에는 **`<p>` 를 닫는 시작 태그 목록**이 박혀 있고, 그 목록이 이 31개다. 카테고리에서 유도한 것이 아니라 **목록을 실행으로 되찾은 것**이다.
- **(B) 들어가는 35개가 구절 콘텐츠와 같지 않다.** `option`·`optgroup`·`legend`·`link`·`meta`·`style`·`title`·`script`·`template`·`noscript` **열 개**는 구절 콘텐츠가 아닌데 그냥 들어갔다.\
  ★ 그중 `link`·`meta`·`style`·`title`·`script`·`template`·`noscript` 일곱은 **메타데이터 콘텐츠**이고, `option`·`optgroup`·`legend` 셋은 **부모가 정해진 요소**다.
  ★★ **이 어긋남이 이 주제의 핵심이다** — **파서는 콘텐츠 모델을 강제하지 않는다.** 자기 목록에 없으면 넣는다.
- **(C) 사라지는 9개는 표 전용 요소 여덟 + `frameset`.** 표 관련 태그는 **표 안이 아니면 무시**된다(A10). `<td>안</td>` 에서 태그만 없어지고 글자 「안」은 남으므로 문단의 글자가 「앞안뒤」가 된다.
- **★ 이 판정은 「직렬화를 눈으로 읽어」 한 것이 아니라 세 조건으로 센 것이다** — `textContent` 가 「앞」뿐이면 (A), `querySelector` 로 잡히면 (B), 둘 다 아니면 (C).

### 2. `<ul>` 안의 `<p>` 는 그대로 남는다 — 무효인 채로

**출력**

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

**왜 그런가**

- **트리는 소스와 한 글자도 다르지 않다.** `ul > (p, li)` · `ol > (div, li)` · `dl > (p, dt, dd)`.
- **유효하지 않다.** `<ul>` 의 콘텐츠 모델은 「**0개 이상의 `<li>` 와 스크립트 지원 요소(`<script>`·`<template>`)**」다. `<p>` 는 거기 없다.
- **파서는 개입하지 않았다.** `<ul>` 에는 `<p>` 처럼 「나를 닫는 태그 목록」이 없고, `<li>` 를 강제로 끼워 넣는 규칙도 없다.
- ★ **그래서 두 답이 갈린다 — 무효인데 아무 일도 안 일어난다.** 이것이 **가장 조용한 무효**이고, 「파서가 검증기가 아니다」(A8)의 실물이다.

### 3. 다섯이 세 가지 처분으로 갈린다

**출력**

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

**왜 그런가**

| 소스 | 트리 | 처분 |
|---|---|---|
| `<a>밖<a>안</a>뒤</a>` | `a"밖"` · `a"안"` · `#text"뒤"` | **형제로 펴진다** |
| `<button>겉<button>속</button></button>` | `button"겉"` · `button"속"` | **형제로 펴진다** |
| `<label>겉<label>속</label></label>` | `label > (#text, label)` | **안 고친다** |
| `<form/1><form/2><input></form></form>` | `form[/1] > input` | **안쪽이 사라진다** |
| `<details>겉<details>속</details></details>` | `details > (#text, details)` | **안 고친다** |

- **`<a>`·`<button>` 은 서식 요소·특수 요소로서 파서에 「같은 것을 다시 열면 앞것을 닫는다」는 규칙이 있다.** `<a>` 는 **adoption agency algorithm** 을 타서 「뒤」까지 바깥으로 밀려난다.
- **`<form>` 은 규칙이 또 다르다.** 파서가 **폼 요소 포인터**를 하나만 들고 있어서, 이미 열려 있으면 **안쪽 시작 태그를 통째로 무시**한다. `<input>` 은 그래서 바깥 폼의 자식이 된다.
- **`<label>`·`<details>` 에는 그런 규칙이 없다.** 중첩이 그대로 남는다 — **둘 다 무효인데** 그렇다.
- ★ **「중첩은 금지다」로 요약하면 세 가지 처분이 하나로 뭉개진다.** 트리를 맞히려면 **요소마다** 알아야 한다.

### 4. 트리가 소스 그대로다 — `<p><div>` 와 갈리는 것은 카테고리가 아니라 파서의 목록이다

**출력**

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

**왜 그런가**

- `span > (#text, div, #text)` · `em > (#text, section, #text)` · `code > (#text, ul, #text)` — **셋 다 안 고쳐졌다.**
- **셋 다 무효다.** `<span>`·`<em>`·`<code>` 의 콘텐츠 모델은 전부 **구절 콘텐츠**이고 `<div>`·`<section>`·`<ul>` 은 구절이 아니다.
- **`<p><div>` 는 고쳐진다**([03번 주제](../03-parser-and-error-recovery/3-answer.md)). 같은 성격의 위반인데 처분이 갈린다.
- ★★ **갈리게 만든 것은 콘텐츠 모델이 아니라 파서의 목록이다.** 「`<div>` 시작 태그를 만나면 열려 있는 `<p>` 를 닫는다」가 명세 파싱 알고리즘에 **`<p>` 에 대해서만** 있다. `<span>` 에는 없다.
- **그러므로 파서로 유효성을 판정할 수 없다**(A8). 파서가 아는 것은 「무엇이 유효한가」가 아니라 「이 태그를 만나면 무엇을 닫는가」다.

### 5. 부모가 `<p>` 면 `<a>` 가 둘로 복제된다

**출력**

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

**왜 그런가**

- **1행 `<div><a><div>`** — 한 글자도 안 바뀐다. `<a>` 는 **투명 콘텐츠 모델**이라 부모(`<div>`)의 모델을 그대로 쓰고, `<div>` 는 흐름 콘텐츠를 받으므로 **유효**하다.
- **2행 `<p><a><div>`** — 소스는 부모 한 글자만 다른데 트리가 완전히 달라진다.

```text
  <p><a href="/t"><div>p 안의 a 안의 div</div></a></p>

    ↓ 파서

  p  > a[href=/t]        (빈 것)            <- <div> 를 만나 <p> 가 닫힌다
  div > a[href=/t] "p 안의 a 안의 div"       <- 열려 있던 a 가 새 자리에 복제된다
  p  (빈 것)                                <- </p> 가 빈 문단을 하나 더 만든다
```

- **트리의 `<a>` 는 두 개다.** 「서식 요소 목록」에 남아 있던 `<a>` 가 새 삽입 지점에서 **다시 열리기** 때문이다. 링크 하나를 쓴 적 없는데 **링크가 둘**이 된다.
- **3행 `<div><a><button>`** — 그대로 남는다. `<button>` 은 구절이고 대화형이므로 트리는 안 바뀌지만, **대화형 콘텐츠를 `<a>` 안에 넣는 것은 무효**다(투명 모델이라도 「대화형 안의 대화형」을 금지한다). ★ **파서는 이것도 안 고친다.**
- **4행 `<div><ins><h2>`** — 그대로. **5행 `<p><ins><h2>`** — `<h2>` 가 `<p>` 밖으로 밀려나고 `<ins>` 는 **빈 껍데기**로 남는다. `<ins>` 도 투명 모델이라 2행과 같은 일이 난다.
- ★ **투명 모델은 「제한 없음」이 아니라 판정을 한 단계 위로 미루는 것**이다.

### 6. 일곱 중 여섯이 그대로 남고 `<td>` 만 사라진다

**출력**

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

**왜 그런가**

- **`<li>`·`<dt>`·`<option>`·`<legend>`·`<figcaption>`·`<summary>` 여섯은 태그째 남는다.** 전부 **무효**다 — 각각 `<ul>`/`<ol>`·`<dl>`·`<select>` 계열·`<fieldset>`·`<figure>`·`<details>` 를 부모로 요구한다.
- **`<td>` 하나만 `#text` 가 된다.** 표 관련 태그는 파서의 **「in body」 삽입 모드에서 무시 대상**이라 시작 태그도 끝 태그도 버려지고 글자만 남는다.
- ★ **A1 의 (C) 9개와 같은 규칙이다** — 자리가 정해진 것은 표 계열뿐이다.
- **조각 템플릿에 뜻하는 것** — `<li>` 조각을 단독으로 미리보기 하면 **멀쩡해 보이고**, `<td>` 조각은 **무너진다.** 「조각은 다 위험하다」로 외우면 어느 것이 실제로 깨지는지 못 가린다.

### 7. 조합이 아니라 자리의 종류로 외우는 장치다

**왜 그런가**

- HTML 요소는 100개를 넘는다. 「어느 안에 어느」를 조합으로 외우면 **만 단위**가 된다.
- 카테고리로 바꾸면 외울 것이 **카테고리 여섯 개 + 요소마다 「나는 어느 카테고리인가 / 나는 어느 카테고리를 받나」 두 줄**로 줄어든다.
- **한 요소가 여럿에 속하는 이유** — 카테고리는 「종류」가 아니라 「**어느 자리에 놓일 수 있나**」이기 때문이다. `<a>` 는 문단 안(구절)에도 놓이고 본문 직계(흐름)에도 놓이며 사용자 조작을 받으므로(대화형) 셋 다다.
- **CSS 의 블록/인라인과 다른 축이다.** 겹치는 곳이 많지만 `<option>`·`<legend>`·`<template>` 처럼 CSS 축으로는 설명이 안 되는 것이 있고, 반대로 CSS `display` 는 **선언 한 줄로 바뀌지만** 카테고리는 안 바뀐다.

### 8. 파서는 검증기가 아니다 — 양방향으로 못 쓴다

**왜 그런가**

- **「안 고쳤다」 → 「유효하다」는 거짓이다.** A2·A4·A6 이 반례다 — 무효한 중첩 **15가지**가 한 글자도 안 고쳐진 채 들어갔다(겹쳐 쓴 것 2 · 구절 안의 블록 3 · 목록 안의 비목록 3 · `<a>` 안의 대화형 1 · 부모 없는 자식 6).
- **「고쳤다」 → 「무효하다」는 이 배치가 던진 범위에서는 반례를 못 찾았다.** 다만 **전수로 확인한 것이 아니므로** 「그렇다」고 적지 않는다.
- **이 환경에 마크업 검증기가 없다.** W3C Nu Validator 같은 것이 설치돼 있지 않고 네트워크로 부르지도 않았다.
- **그래서 이 주제의 「무효하다」는 전부 명세를 읽어 적은 것**이다. 실행으로 잰 것은 **트리의 모양**뿐이다. ★ 둘을 섞어 읽으면 「Chrome 이 무효라고 했다」는 없던 말을 만들게 된다.

### 9. 투명 모델은 판정을 부모로 미룬다

**왜 그런가**

- **정의** — 「이 요소의 콘텐츠 모델은 **부모의 콘텐츠 모델과 같다**」.
- **가진 요소** — `<a>`·`<ins>`·`<del>`·`<map>`·`<object>`·`<video>`/`<audio>`(폴백 부분)·`<slot>`·`<canvas>`.
- **「아무거나 된다」가 틀린 이유** — 부모가 `<p>` 면 `<a>` 안도 구절 콘텐츠만 받는다. A5 의 2행이 그 실물이고, 트리에 `<a>` 가 **둘**이 됐다.
- **`<a>` 안의 `<a>` 는 투명 모델로 설명되지 않는다.** 투명 모델 위에 「**대화형 콘텐츠를 자손으로 두지 않는다**」는 별도 제약이 얹혀 있다. 같은 제약이 A5 3행의 `<a><button>` 도 무효로 만든다 — 그런데 **파서는 셋 중 `<a><a>` 만 고친다.**

### 10. 표 요소만 「자리 밖이면 무시」라는 규칙을 받는다

**왜 그런가**

- **처분** — 표 전용 요소(`td`·`tr`·`th`·`thead`·`tbody`·`caption`·`col`·`colgroup`)는 표 밖에서 **시작 태그가 무시**된다. 요소가 아예 안 생기고 안의 글자만 남는다.
- **`<li>`·`<option>` 이 같은 처분을 안 받는 이유** — 이 요소들에는 그런 규칙이 명세에 없다. 파서의 무시 목록은 **표 계열에만** 있다.
- **같은 집안의 규칙** — [03번 주제](../03-parser-and-error-recovery/3-answer.md)의 **foster parenting**(표 안에 못 들어갈 것을 표 **앞으로** 옮기는 것)이다. 둘 다 「**표는 특별 취급**」이라는 한 뿌리에서 나온다.
- **모르면 나는 사고** — 서버가 돌려준 `<td>…</td>` 조각을 `<div>` 에 꽂으면 **셀이 사라지고 글자만 남는다.** 에러도 경고도 없다.

### 11. 정본 경계

**왜 그런가**

| 무엇 | 정본 | 여기는 |
|---|---|---|
| 블록/인라인·`display` | CSS 갈래 목록([`css/syntax/README.md`](../../../css/syntax/README.md)) | **CSS 의 축이다.** 여기는 그 말을 쓰지 않는다 |
| `childNodes`·`querySelector`·노드 대 요소 | web-api 갈래 목록([`web-api/README.md`](../../../../web-api/README.md))의 **01번**·**02번** | **API 는 그쪽이 정본**이다. 여기서는 **세는 도구**로만 썼다 |
| `<p><div>` 의 파싱 과정·foster parenting | [03번 주제](../03-parser-and-error-recovery/3-answer.md) | 그쪽은 **어떻게 트리가 되나**, 여기는 **무엇을 넣어도 되나** |
| 메타데이터 콘텐츠와 `<head>` | [01번 주제](../01-document-skeleton/3-answer.md) | 카테고리 하나를 그쪽이 먼저 썼다 |

- **03번과 독립인 이유** — 03번은 **처리 요건**(브라우저가 무엇을 하나)이고, 이 주제는 **저작 요건**(내가 무엇을 써도 되나)이다. 둘이 어긋나는 **틈**이 이 주제의 본체이고, 그 틈은 03번 안에서는 보이지 않는다.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · 기본 창 폭 **780**. **엔진은 이것 하나다.** **마크업 검증기는 없다.**

**하네스** — 05\~08 네 주제가 공유한다. 블록의 배너에 적힌 `dom`·`probe`·`nojs` 가 그 함수들이다(`serve` 는 [08번 주제](../08-script-loading/3-answer.md)에서만 쓴다).

```bash
# html05b-harness.sh
dom()   { google-chrome --headless --disable-gpu --no-sandbox --dump-dom "$1" 2>/dev/null; }
probe() { sed -n '/^###P###$/,/^###E###$/p' | sed '1d;$d' \
          | sed 's/&lt;/</g; s/&gt;/>/g; s/&amp;/\&/g'; }
nojs()  { sed '/^<script>$/,$d'; }
serve() { python3 html05b-server.py >"$1" 2>&1 & echo $!; }
```

- ★ **`--virtual-time-budget` 은 쓰지 않는다**(정본 규칙).
- ★ **트리가 본체인 블록에는 프로브 스크립트를 넣지 않았다** — `<script>` 가 트리에 섞이면 관찰 대상이 오염된다. A1 만 예외인데, 거기서 읽는 것은 직렬화가 아니라 **세 갈래의 개수**다.

**demo 블록 검증** — 문서의 `demo` 블록에 래퍼와 측정 프로브를 붙인 사본을 따로 띄워 `보이는 것` 을 확인했다.

```text
===== 소스: html05b-demo05a.html (demo 블록 + 래퍼 + 측정 프로브) =====
<!DOCTYPE html>
<meta charset="utf-8">
<title>demo 05 검증</title>
<body>
<span class="s">앞<div class="d">span 안의 div</div>뒤</span>
<style>
  .s { border: 2px solid #2563eb; padding: 4px; }
  .d { border: 2px dashed #b91c1c; padding: 4px; }
</style>
<script>
const o = [];
const s = document.querySelector(".s"), d = document.querySelector(".d");
o.push("창 폭                  = " + window.innerWidth);
o.push("d 의 부모              = " + d.parentElement.tagName + "   (파서가 안 고쳤다)");
o.push("s 의 display           = " + getComputedStyle(s).display);
o.push("d 의 display           = " + getComputedStyle(d).display);
o.push("s 가 만든 상자 개수    = " + s.getClientRects().length + "개");
o.push("d 가 만든 상자 개수    = " + d.getClientRects().length + "개");
o.push("d 의 너비              = " + Math.round(d.getBoundingClientRect().width));
o.push("s 의 높이              = " + Math.round(s.getBoundingClientRect().height));
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
===== dom html05b-demo05a.html | probe =====
창 폭                  = 780
d 의 부모              = SPAN   (파서가 안 고쳤다)
s 의 display           = inline
d 의 display           = block
s 가 만든 상자 개수    = 3개
d 가 만든 상자 개수    = 1개
d 의 너비              = 764
s 의 높이              = 96
(exit 0)
```

- **`span` 이 만든 상자가 3개**다 — 트리는 `span > div` 하나인데 **렌더 상자는 셋으로 쪼개진다**(「앞」 / 「뒤」 앞뒤 조각 + 사이). `div` 는 상자 1개에 너비 764 로 줄을 통째로 차지한다.
- `div` 의 부모가 `SPAN` 으로 나온다 — **파서가 안 고쳤다**는 것의 재확인이다.
- 높이 96 은 **흔들리는 칸**이므로 「세 조각으로 갈린다」는 사실만 근거로 쓴다.

`바꿔 볼 것` 에 적은 두 단언도 따로 던졌다.

```text
===== 소스: html05b-demo05b.html (demo 블록 + 래퍼 + 측정 프로브) =====
<!DOCTYPE html>
<meta charset="utf-8">
<title>demo 05 의 '바꿔 볼 것' 검증</title>
<body>
<span class="v1">앞<div class="d1">span 안의 div</div>뒤</span>
<div class="v2">앞<div class="d2">div 안의 div</div>뒤</div>
<style>
  .v1, .v2 { border: 2px solid #2563eb; padding: 4px; }
  .d1, .d2 { border: 2px dashed #b91c1c; padding: 4px; }
  .d1 { display: inline; }
</style>
<script>
const o = [];
const g = (sel, name) => {
  const e = document.querySelector(sel);
  o.push(name + "  display = " + getComputedStyle(e).display
    + "   상자 개수 = " + e.getClientRects().length
    + "   부모 = " + e.parentElement.tagName);
};
o.push("창 폭 = " + window.innerWidth);
g(".d1", "d1(display:inline 을 준 div)  ");
g(".v1", "v1(그 div 를 품은 span)       ");
g(".d2", "d2(div 안의 div)              ");
g(".v2", "v2(바깥 div)                  ");
o.push("v1 높이 = " + Math.round(document.querySelector(".v1").getBoundingClientRect().height)
     + "   v2 높이 = " + Math.round(document.querySelector(".v2").getBoundingClientRect().height));
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
===== dom html05b-demo05b.html | probe =====
창 폭 = 780
d1(display:inline 을 준 div)    display = inline   상자 개수 = 1   부모 = SPAN
v1(그 div 를 품은 span)         display = inline   상자 개수 = 1   부모 = BODY
d2(div 안의 div)                display = block   상자 개수 = 1   부모 = DIV
v2(바깥 div)                    display = block   상자 개수 = 1   부모 = BODY
v1 높이 = 36   v2 높이 = 96
(exit 0)
```

- **`display: inline` 을 주면** `div` 의 상자가 1개인 채 `span` 높이가 **96 → 36** 으로 줄었다(`v1 높이 = 36`). 줄이 안 갈린다.
- **바깥을 `<div>` 로 바꾸면 높이가 96 으로 같다**(`v2 높이 = 96`). 갈라진 원인이 「`span` 이라서」가 아니라 **블록 상자가 흐름을 끊어서**임이 드러난다.

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| **`<p>` 안에 75개** — 31/35/9 갈래 | 2 | 동작 방식 (2) · A1 · A7 |
| `<ul>`·`<ol>`·`<dl>` 안의 문단·`div` | 2 | 동작 방식 (4) · A2 |
| 겹쳐 쓴 다섯(`a`·`button`·`label`·`form`·`details`) | 2 | 동작 방식 (3) · A3 |
| `<span>`·`<em>`·`<code>` 안의 블록 | 2 | 동작 방식 (4) · A4 · A8 |
| **투명 모델** — 같은 중첩을 두 부모 아래 | 2 | 동작 방식 (5) · A5 · A9 |
| 부모 없이 쓴 자식 일곱 | 2 | 동작 방식 (6) · A6 · A10 |
| **demo 블록**과 그 `바꿔 볼 것` 두 단언 | 2 | 동작 방식 (7) |

**구현에 달린 항목**

| 항목 | 이 판의 값 | 왜 다시 찍나 |
|---|---|---|
| A1 의 31/35/9 | `31 / 35 / 9` | 파서의 목록이 명세에 있으나 **판이 바뀌면 다시 센다** |
| demo 의 높이·너비 픽셀 | `96` · `36` · `764` | 글꼴·창 폭에 달렸다 — **갈린다는 사실**만 근거로 쓴다 |
| `--dump-dom` 의 줄바꿈 자리 | 소스의 텍스트 노드 그대로 | 직렬화 + 도구 |

**안 돌려 본 것** — ① **Firefox·Safari 재현**(엔진이 없다). ② **`<p>` 밖의 부모로 던진 전수** — 75개 실험은 `<p>` 를 부모로 한 것뿐이다. `<span>`·`<button>` 을 부모로 한 전수는 던지지 않았다. ③ **`<table>` 안에 흐름 콘텐츠를 넣는 경우**(foster parenting)는 03번이 이미 던졌으므로 여기서 다시 던지지 않았다.

**못 잰 것**(「안 돌려 본 것」과 다르다) — **유효성 그 자체.** 검증기가 없어 **측정 수단이 없다.** 쪼개서 잰 조각은 **트리의 모양**뿐이고, 「무효하다」는 전부 명세를 읽어 적은 것이다(A8).

**부적용인 창** — **창 ③(`innerText` 대 `textContent`)과 창 ④(`compatMode`).** 이 주제는 렌더된 글자도 문서 모드도 바꾸지 않아 **잴 것이 없다**(「재 봤더니 같았다」가 아니다).

## 용어 풀이

- **콘텐츠 카테고리(content category)** — 요소를 묶은 이름표. 흐름·구절·구획·헤딩·임베디드·대화형·메타데이터.
- **흐름 콘텐츠(flow content)** — 문서 본문에 놓이는 거의 전부.
- **구절 콘텐츠(phrasing content)** — 문단 안에 섞이는 글자 수준의 것. 흐름의 부분집합.
- **임베디드 콘텐츠(embedded content)** — 문서 밖 자원을 끌어오는 것. `<img>`·`<video>`·`<iframe>`.
- **대화형 콘텐츠(interactive content)** — 사용자 조작을 받는 것. `<a href>`·`<button>`·`<input>`.
- **메타데이터 콘텐츠(metadata content)** — 문서 자체를 설명하는 것. `<link>`·`<meta>`·`<style>`·`<title>`·`<script>`.
- **콘텐츠 모델(content model)** — 「이 요소 안에 무엇이 올 수 있나」.
- **투명 콘텐츠 모델(transparent content model)** — 부모의 콘텐츠 모델을 그대로 쓰는 것.
- **저작 요건(authoring requirement)** — 문서를 **쓰는 사람**에게 건 규칙. 콘텐츠 모델이 여기 든다.
- **처리 요건(processing requirement)** — **브라우저**에게 건 규칙. 파싱 알고리즘이 여기 든다.
- **adoption agency algorithm** — 겹쳐 쓴 서식 요소를 형제로 펴는 파서 절차.
- **폼 요소 포인터(form element pointer)** — 파서가 들고 있는 「지금 열린 폼」 하나. 중첩 `<form>` 이 무시되는 근거.
- **foster parenting** — 표 안에 못 들어갈 것을 표 앞으로 옮기는 파서 규칙. 03번 주제가 정본이다.
