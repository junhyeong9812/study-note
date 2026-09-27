# html/syntax/05 — 콘텐츠 카테고리와 콘텐츠 모델: 어디에 무엇을 넣을 수 있나 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ 이 주제는 **「유효한가」와 「파서가 고치나」를 갈라서** 답한다. 두 축은 겹치지 않는다.
> ★ 답은 **트리의 모양**으로 적는다 — 「된다/안 된다」가 아니라 `ul > (p, li)` 처럼.
> ★ 소스 펜스 첫 줄의 `<!-- 파일이름 -->` 은 **어느 파일을 던진 것인지 표시**이지 파일 내용이 아니다.
> 선행 — [03번 주제](../03-parser-and-error-recovery/1-question.md).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 한 문단 안에 요소 75개를 하나씩 던지면 (예측)

```html
<!-- html05b-category-probe.html -->
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
```

- 세 갈래(문단이 닫힘 / 안에 들어감 / 태그가 사라짐)의 **개수**를 각각 예측하라.
- 태그가 사라지는 쪽에 어떤 요소들이 있겠는가?
- 「안에 들어간다」의 목록이 **구절 콘텐츠와 정확히 같겠는가?**
- 다르다면 그 사실이 뜻하는 것은 무엇인가?

### 2. 목록 요소 안에 문단을 쓰면 (예측)

```html
<!-- html05b-ul-p.html -->
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
```

- 세 트리를 각각 그려라.
- 이 마크업은 유효한가?
- 파서가 개입했는가?
- 두 답이 갈린다면 그 사실을 어떻게 읽어야 하는가?

### 3. 다섯 가지 겹쳐 쓰기 (예측)

```html
<!-- html05b-a-in-a.html -->
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
```

- 다섯 줄이 각각 어떤 트리가 되는지 예측하라.
- 다섯이 **같은 처분**을 받겠는가?
- `<input name="x">` 는 결국 어느 `<form>` 의 자식이 되는가?
- 「중첩은 금지다」로 한 줄 요약하면 무엇을 놓치는가?

### 4. 인라인 요소 안에 블록 요소를 쓰면 (예측)

```html
<!-- html05b-span-div.html -->
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
```

- 세 줄의 트리를 예측하라.
- `<p>` 안에 `<div>` 를 쓴 경우([03번 주제](../03-parser-and-error-recovery/1-question.md))와 무엇이 다른가?
- 둘 다 무효인데 처분이 갈린다면, 갈리게 만든 것은 무엇인가?
- 그렇다면 「유효성」을 파서로 판정할 수 있는가?

### 5. 같은 링크 중첩을 부모만 바꿔서 (예측)

```html
<!-- html05b-transparent.html -->
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
```

- 다섯 줄의 트리를 각각 예측하라.
- 1행과 2행은 소스가 거의 같은데 결과가 같겠는가?
- 트리에 `<a>` 가 **몇 개** 생기는가?
- `<ins>` 두 줄에서는 무엇이 남고 무엇이 밀려나는가?

### 6. 부모 없이 쓴 자식 일곱 (예측)

```html
<!-- html05b-orphan.html -->
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
```

- 일곱 중 몇 개가 태그째 살아남는지 예측하라.
- 살아남지 못하는 것이 있다면 그 요소의 공통점은?
- 일곱이 전부 유효한가?
- 이 결과가 조각 템플릿 미리보기에 뜻하는 것은?

### 7. 카테고리를 왜 만들었나 (왜)

- 「어느 요소 안에 어느 요소」를 조합으로 외우면 몇 가지를 외워야 하는가?
- 카테고리로 바꾸면 외울 것이 무엇으로 줄어드는가?
- 한 요소가 카테고리 여럿에 속할 수 있는 이유는?
- 카테고리가 CSS 의 「블록/인라인」과 같은 축인가?

### 8. 파서를 검증기로 쓸 수 있나 (경계)

- 「파서가 안 고쳤다」에서 「유효하다」를 끌어낼 수 있는가?
- 반대로 「파서가 고쳤다」에서 「무효하다」를 끌어낼 수 있는가?
- 이 환경에서 유효성을 판정할 도구가 있는가?
- 그러면 이 주제의 「무효하다」는 무엇에 근거한 것인가?

### 9. 투명 콘텐츠 모델의 경계 (경계)

- 투명 모델을 한 문장으로 정의하라.
- 투명 모델을 가진 요소를 셋 대라.
- 「`<a>` 안에는 아무거나 된다」가 틀린 이유는?
- `<a>` 안에 `<a>` 를 넣는 것은 투명 모델로 설명되는가?

### 10. 표 요소만 다른 이유 (왜)

- 표 전용 요소가 자리 밖에서 받는 처분은 무엇인가?
- `<li>`·`<option>` 은 왜 같은 처분을 안 받는가?
- 이 규칙이 [03번 주제](../03-parser-and-error-recovery/1-question.md)의 어떤 규칙과 같은 집안인가?
- 그 규칙을 모르면 어떤 사고가 나는가?

### 11. 정본 경계 긋기 (연결)

- 「블록/인라인」의 정본은 어느 갈래인가? 여기는 무엇까지인가?
- `childNodes`·`querySelector` 라는 API 의 정본은 어느 갈래인가?
- `<p><div>` 의 파싱 과정 정본은 어느 주제인가?
- 이 주제가 03번과 겹치면서도 독립 주제인 이유는 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
