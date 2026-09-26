# html/syntax/17 — 표 구조: `table`/`thead`/`tbody`/`tfoot`/`caption`/`colgroup` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ 이 주제의 본체는 **창 ① `--dump-dom`** 이다. 답할 때마다 「**소스에 쓴 것**」과 「**DOM 에 생긴 것**」을 따로 적어라.
> ★ **명세·구현·관찰을 갈라라** — 파서 규칙과 표 처리 모델은 WHATWG HTML 이, 역할 대응은 HTML-AAM 이, 트리는 Chrome 이 만든다.
> ★ 소스 펜스 첫 줄의 `<!-- 파일이름 -->` 은 **어느 파일을 던진 것인지 표시**이지 파일 내용이 아니다. 펜스의 소스는 전부 실제로 던진 파일이다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰이다. 이식성은 주장 범위 밖이다.
> 선행 — [03번 주제](../03-parser-and-error-recovery/1-question.md)(파서 오류 복구) · [05번 주제](../05-content-categories-and-models/1-question.md)(콘텐츠 모델).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 다섯 표를 파서에 넣으면 (예측)

```html
<!-- html17b-17-parse.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>17 파서가 고친 표</title>
</head>
<body>
<table id="가"><tr><td>셀</td></tr></table>
<table id="나"><div id="div">div</div>글자<tr><td>셀</td></tr></table>
<table id="다"><tr><td>셀</td>꼬리<span id="span">span</span></tr></table>
<table id="라"><tr><td>셀</td></tr><caption id="cap">늦은 caption</caption></table>
<table id="마"><td>td 만</td></table>
</body>
</html>
```

- `--dump-dom` 에서 다섯 표 각각의 **`<table>` 바로 안**에는 무엇이 있는가?
- `#나` 의 `div` 와 「글자」, `#다` 의 「꼬리」와 `span` 은 DOM 의 어디에 있는가?
- `#라` 의 `caption` 은 어느 자리에 있는가?
- `#마` 의 `td` 위에는 무엇이 생기는가?

### 2. 표 안에 열네 가지를 넣으면 (예측)

```html
<!-- html17b-17-foster.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>17 표 안에 넣은 것</title>
</head>
<body>
<hr id="시작">
<table data-k="div"><div>x</div><tr><td>셀</td></tr></table>
<table data-k="span"><span>x</span><tr><td>셀</td></tr></table>
<table data-k="글자">x<tr><td>셀</td></tr></table>
<table data-k="공백"> <tr><td>셀</td></tr></table>
<table data-k="img"><img alt="x"><tr><td>셀</td></tr></table>
<table data-k="input text"><input type="text"><tr><td>셀</td></tr></table>
<table data-k="input hidden"><input type="hidden"><tr><td>셀</td></tr></table>
<table data-k="script"><script></script><tr><td>셀</td></tr></table>
<table data-k="style"><style></style><tr><td>셀</td></tr></table>
<table data-k="template"><template>x</template><tr><td>셀</td></tr></table>
<table data-k="form"><form><input name="q"></form><tr><td>셀</td></tr></table>
<table data-k="주석"><!-- x --><tr><td>셀</td></tr></table>
<table data-k="tr 안 div"><tr><div>x</div><td>셀</td></tr></table>
<table data-k="td 안 div"><tr><td><div>x</div></td></tr></table>
<script>
window.__대상 = [];
const 이름 = n => n.nodeType === 1 ? "<" + n.localName + (n.type && n.localName === "input" ? " " + n.type : "") + ">"
  : n.nodeType === 3 ? (n.data.trim() ? "글자" : "공백") : n.nodeType === 8 ? "주석" : "?";
window.__끝 = () => {
  const O = ["표 안에 쓴 것이 어디로 갔나 — 표 바로 앞 형제 / 표의 직속 자식(tbody 말고) / td 안"];
  let 나감 = 0, 전체 = 0;
  for (const t of document.querySelectorAll("table[data-k]")) {
    const 앞 = [];
    for (let n = t.previousSibling; n && !(n.nodeType === 1 && (n.localName === "table" || n.id === "시작")); n = n.previousSibling)
      if (!(n.nodeType === 3 && n.data === "\n")) 앞.unshift(이름(n));
    const 안 = [...t.childNodes].filter(n => !(n.nodeType === 1 && n.localName === "tbody")).map(이름);
    const td안 = [...t.querySelector("td").childNodes].map(이름);
    전체++; if (앞.length) 나감++;
    O.push("  " + t.dataset.k.padEnd(13) + "표 앞 = " + (앞.join(" ") || "—").padEnd(16)
      + "표 직속 = " + (안.join(" ") || "—").padEnd(18) + "td 안 = " + td안.join(" "));
  }
  const f = document.querySelector('table[data-k="form"]');
  const 입력 = f.previousElementSibling, 폼 = f.querySelector("form");
  O.push("");
  O.push("form 칸 — 표 앞으로 나간 input 의 .form 이 표 안에 남은 form 인가 = " + (입력.form === 폼)
    + " · form.elements.length = " + 폼.elements.length + " · form.childNodes.length = " + 폼.childNodes.length);
  O.push("");
  O.push("표 앞으로 나간 칸 = " + 나감 + " / " + 전체);
  return O.join("\n");
};
</script>
</body>
</html>
```

- 열네 칸 중 **표 바로 앞 형제**가 된 칸은 몇인가? 어느 것들인가?
- `input type=text` 와 `input type=hidden` 은 같은 곳으로 가는가?
- `form` 칸에서 `form` 과 그 안의 `input` 은 각각 어디에 있는가? `input.form` 은 무엇을 가리키는가?
- 공백만 넣은 칸과 주석 칸은?

### 3. 스크립트 API 가 세는 것 (예측)

```html
<!-- html17b-17-api.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>17 스크립트 API 가 세는 것</title>
</head>
<body>
<table id="쓴표"><tr><td>가</td></tr><tr><td>나</td></tr></table>
<div id="상자"></div>
<template id="틀"></template>
<table id="빈표"></table>
<table id="넣을표"><tbody id="몸"></tbody></table>
<script>
window.__대상 = [];
const $ = id => document.getElementById(id);
const 자식 = n => [...n.childNodes].map(c => c.nodeType === 1 ? c.localName : c.nodeType === 3 ? JSON.stringify(c.data) : "?").join(" ");
window.__끝 = () => {
  const O = [];
  const t = $("쓴표");
  O.push("(가) 소스에 tbody 를 안 쓴 표");
  O.push("  table.tBodies.length           = " + t.tBodies.length);
  O.push("  table.rows.length              = " + t.rows.length);
  O.push("  table.children                 = " + 자식(t));
  O.push("  querySelectorAll('table > tr') = " + document.querySelectorAll("#쓴표 > tr").length);
  O.push("  querySelectorAll('table tr')   = " + document.querySelectorAll("#쓴표 tr").length);
  O.push("");
  const 조각 = "<tr><td>셀</td></tr>";
  O.push("(나) 같은 문자열 " + JSON.stringify(조각) + " 을 innerHTML 로 넣으면");
  $("상자").innerHTML = 조각;
  O.push("  div.innerHTML            -> div 의 자식      = " + 자식($("상자")));
  $("틀").innerHTML = 조각;
  O.push("  template.innerHTML       -> content 의 자식  = " + 자식($("틀").content));
  $("빈표").innerHTML = 조각;
  O.push("  table.innerHTML          -> table 의 자식    = " + 자식($("빈표")));
  $("몸").innerHTML = 조각;
  O.push("  tbody.innerHTML          -> tbody 의 자식    = " + 자식($("몸")));
  O.push("");
  O.push("(다) 스크립트 API 로 행을 만들면");
  const 새표 = document.createElement("table");
  새표.insertRow().insertCell().textContent = "셀";
  O.push("  빈 table.insertRow()     -> table 의 자식    = " + 자식(새표));
  const 둘째 = document.createElement("table");
  둘째.createTHead();
  둘째.insertRow();
  O.push("  thead 만 있는 table.insertRow() -> table 의 자식 = " + 자식(둘째));
  return O.join("\n");
};
</script>
</body>
</html>
```

- `#쓴표` 의 `tBodies.length`·`rows.length`·`children` 은?
- `table > tr` 과 `table tr` 은 각각 몇 개를 잡는가?
- 같은 문자열 `<tr><td>셀</td></tr>` 을 `div`·`template`·`table`·`tbody` 의 `innerHTML` 로 넣으면 각각의 자식은?
- 빈 표와 `thead` 만 있는 표에서 `insertRow()` 를 부르면 표의 자식은?

### 4. 네 행의 순서를 다섯 창에 물으면 (예측)

```html
<!-- html17b-17-order.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>17 행의 순서</title>
<style>body { font-family: sans-serif; } td { padding: 4px; }</style>
</head>
<body>
<table id="표">
<tfoot><tr id="발"><td>tfoot 의 행</td></tr></tfoot>
<tbody><tr id="본문1"><td>첫 tbody 의 행</td></tr></tbody>
<thead><tr id="머리"><td>thead 의 행</td></tr></thead>
<tbody><tr id="본문2"><td>둘째 tbody 의 행</td></tr></tbody>
</table>
<script>
window.__대상 = [];
window.__내부 = true;
const 표 = document.getElementById("표");
// 명세 「표 만들기(forming a table)」 알고리즘에서 행 순서를 정하는 부분만 옮긴 것
function 명세순서(t) {
  const 앞 = [], 미룬 = [];
  for (const g of t.children) {
    if (g.localName === "tfoot") 미룬.push(g);
    else if (["thead", "tbody"].includes(g.localName)) 앞.push(g);
    else if (g.localName === "tr") 앞.push({ children: [g] });
  }
  return [...앞, ...미룬].flatMap(g => [...g.children]).map(r => r.id);
}
window.__끝 = () => {
  const O = [];
  const DOM = [...표.querySelectorAll("tr")].map(r => r.id);
  const 창 = {
    "① DOM 트리 순서": DOM,
    "   table.rows": [...표.rows].map(r => r.id),
    "② 화면 위→아래": [...표.querySelectorAll("tr")].sort((a, b) =>
      a.getBoundingClientRect().top - b.getBoundingClientRect().top).map(r => r.id),
    "   명세 표 모델(스크립트)": 명세순서(표),
    "⑦ 트리 tableRowIndex": [...표.querySelectorAll("tr")].sort((a, b) =>
      __INT[a.id].속성.tableRowIndex - __INT[b.id].속성.tableRowIndex).map(r => r.id),
  };
  O.push("같은 네 행을 다섯 창에 물었다 — 위(앞)에서부터");
  let 갈림 = 0;
  for (const [k, v] of Object.entries(창)) {
    const 다름 = v.join() !== DOM.join();
    if (k !== "① DOM 트리 순서" && 다름) 갈림++;
    O.push("  " + k.padEnd(20) + v.join(" · ") + (k === "① DOM 트리 순서" ? "" : 다름 ? "   <- DOM 과 다름" : "   = DOM"));
  }
  O.push("");
  O.push("table.tHead = #" + 표.tHead.rows[0].id + " · table.tFoot = #" + 표.tFoot.rows[0].id + " · tBodies.length = " + 표.tBodies.length);
  O.push("DOM 순서와 갈린 창 = " + 갈림 + " / " + (Object.keys(창).length - 1));
  return O.join("\n");
};
</script>
</body>
</html>
```

- 다섯 줄(DOM · `table.rows` · 화면 · 명세 표 모델 · 트리) 각각의 순서를 적어라.
- 마지막 줄 「**DOM 순서와 갈린 창 = N / 4**」 의 N 은?
- 명세 표 모델의 순서는 화면 순서와 같은가?

### 5. 창 ⑦ 에 표를 물으면 (예측)

```html
<!-- html17b-17-name.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>17 표의 이름</title>
</head>
<body>
<table id="캡션"><caption>분기별 매출</caption><tr><th>분기</th><th>매출</th></tr><tr><td>1</td><td>10</td></tr></table>
<table id="없음"><tr><th>분기</th><th>매출</th></tr><tr><td>1</td><td>10</td></tr></table>
<table id="title" title="제목 속성"><tr><th>분기</th><th>매출</th></tr><tr><td>1</td><td>10</td></tr></table>
<table id="둘다" title="제목 속성"><caption>분기별 매출</caption><tr><th>분기</th><th>매출</th></tr><tr><td>1</td><td>10</td></tr></table>
<table id="aria" aria-label="에어리아 이름"><caption>분기별 매출</caption><tr><th>분기</th><th>매출</th></tr><tr><td>1</td><td>10</td></tr></table>
<table id="늦은"><tr><th>분기</th><th>매출</th></tr><tr><td>1</td><td>10</td></tr><caption>분기별 매출</caption></table>
<table id="숨긴"><caption style="display: none">분기별 매출</caption><tr><th>분기</th><th>매출</th></tr><tr><td>1</td><td>10</td></tr></table>
<table id="클립"><caption style="position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%)">분기별 매출</caption><tr><th>분기</th><th>매출</th></tr><tr><td>1</td><td>10</td></tr></table>
<table id="h2"><caption><h2>분기별 매출</h2></caption><tr><th>분기</th><th>매출</th></tr><tr><td>1</td><td>10</td></tr></table>
<script>
const 표 = ["캡션", "없음", "title", "둘다", "aria", "늦은", "숨긴", "클립", "h2"];
window.__대상 = 표.map(k => [k, "#" + k]);
window.__내부 = true;
const J = v => JSON.stringify(v);
window.__끝 = () => {
  const O = ["표마다 창 ⑦ 이 준 역할·이름·설명과 이름의 출처(nameFrom — 내부 덤프)"];
  for (const k of 표) {
    const a = __AX[k], i = __INT[k].속성;
    O.push("  #" + k.padEnd(6) + "역할 = " + a.역할.padEnd(7) + "이름 = " + J(a.이름).padEnd(12)
      + "설명 = " + J(a.설명).padEnd(10) + "nameFrom = " + (i.nameFrom || "—"));
  }
  return O.join("\n");
};
</script>
</body>
</html>
```

```html
<!-- html17b-17-ax.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>17 행 묶음은 트리에 남나</title>
</head>
<body>
<table><thead><tr><th>머리</th></tr></thead><tbody><tr><td>본문</td></tr></tbody><tfoot><tr><td>발</td></tr></tfoot></table>
<table><thead id="h"><tr><th>머리</th></tr></thead><tbody id="b"><tr><td>본문</td></tr></tbody><tfoot id="f"><tr><td>발</td></tr></tfoot></table>
<table><tr><th>머리</th></tr><tr><td>본문</td></tr></table>
</body>
</html>
```

- 첫 소스의 아홉 표 각각의 **이름·설명·`nameFrom`** 은?
- `aria-label` 과 `caption` 이 같이 있으면 `caption` 의 글자는 어디로 가는가?
- `#숨긴` 과 `#클립` 은 같은 결과인가?
- 둘째 소스의 세 표에서 트리에 **`rowgroup` 노드**가 몇 개씩 나오는가?

### 6. `col` 에 속성을 하나씩 주면 (예측)

```html
<!-- html17b-17-col.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>17 col 에 준 속성</title>
<style>
body { font-family: sans-serif; margin: 8px; }
table { border-collapse: collapse; margin-bottom: 4px; }
td { padding: 8px; }
.background-color { background-color: gold; }
.border { border: 6px solid rgb(0, 0, 255); }
.width { width: 200px; }
.visibility { visibility: collapse; }
.color { color: rgb(255, 0, 0); }
.font-weight { font-weight: 700; }
.text-align { text-align: right; }
.padding { padding: 20px; }
</style>
</head>
<body>
<script>
const 속성 = ["없음", "background-color", "border", "width", "visibility", "color", "font-weight", "text-align", "padding"];
for (const p of 속성)
  document.body.insertAdjacentHTML("beforeend",
    `<table><colgroup><col><col class="${p}"><col></colgroup><tr><td>가</td><td id="셀-${p}">가나</td><td>다</td></tr></table>`);
window.__대상 = [];
const 셀 = p => document.getElementById("셀-" + p);
window.__픽셀 = () => 속성.map(p => { const r = 셀(p).getBoundingClientRect(); return [p, r.left + 2, r.top + 2]; });
const 잰것 = p => {
  const e = 셀(p), r = e.getBoundingClientRect(), s = getComputedStyle(e);
  return { "셀 폭": r.width.toFixed(1), "셀 x": r.left.toFixed(1), "계산 color": s.color, "계산 background": s.backgroundColor,
    "계산 weight": s.fontWeight, "계산 align": s.textAlign, "계산 padding": s.paddingLeft, "칠해진 픽셀": __PX[p] };
};
window.__끝 = () => {
  const O = ["가운데 col 에 속성 하나씩 — 가운데 셀에서 무엇이 바뀌었나(속성 없는 표와 견준다)"];
  const 기준 = 잰것("없음");
  O.push("  기준(속성 없음)      " + Object.entries(기준).map(([k, v]) => k + "=" + v).join(" · "));
  let 닿음 = 0;
  for (const p of 속성.slice(1)) {
    const v = 잰것(p);
    const col값 = getComputedStyle(document.querySelector("col." + p)).getPropertyValue(p === "border" ? "border-top-width" : p);
    const 바뀐 = Object.keys(v).filter(k => v[k] !== 기준[k]);
    if (바뀐.length) 닿음++;
    O.push("  " + p.padEnd(18) + " col 자신의 계산값 = " + col값.padEnd(20) + "셀에서 바뀐 것 = "
      + (바뀐.length ? 바뀐.map(k => k + " " + 기준[k] + "->" + v[k]).join(" · ") : "없음"));
  }
  O.push("");
  O.push("셀에 닿은 속성 = " + 닿음 + " / " + (속성.length - 1));
  return O.join("\n");
};
</script>
</body>
</html>
```

- 여덟 속성 중 가운데 셀에서 **무엇이든 바뀐** 속성은 몇 개인가? 어느 것들인가?
- `background-color` 는 셀의 **어느 칸**에서 보이는가?
- `color` 를 준 `col` 자신의 계산값은? 셀의 계산값은?

### 7. 6번의 결과를 두 문장으로 (왜)

- 6번에서 셀에 닿은 속성과 안 닿은 속성을 가르는 **트리의 사실 하나**는 무엇인가?
- CSS 2.1 §17.3 은 그 목록을 어떻게 적는가? `border` 에 붙은 조건은?
- 계산 `background` 로 판정하면 어느 칸을 틀리게 되는가?

### 8. 창을 바꿔 물은 자리 (경계)

- 4번에서 「명세 표 모델」 열은 **어느 창의 답**인가? 그것은 제 몇의 상태인가?
- 창 ① · 창 ② · `table.rows` 가 4번에 다른 답을 한 것은 틀린 답들인가?
- 이 주제에서 **부적용**인 창을 대고 그 이유를 한 줄씩 적어라.

### 9. 명세·구현·관찰 가르기 (경계)

- `tbody` 삽입 · foster parenting · `rows` 의 정렬 · `insertRow()` 의 `tbody` 생성은 각각 명세의 **어느 절**이 정하나?
- 4번의 트리 행 순서와 5번 둘째 소스의 `rowgroup` 개수는 명세인가 구현인가? 각각 명세와 **같은가**?
- 표의 이름 우선순위는 누가 정하나?

### 10. 이 판이 못 보는 것 (경계)

- 「스크린리더가 `caption` 을 표 제목으로 읽는다」를 이 문서가 실측으로 쓸 수 있는가?
- HTML-AAM 이 적는 플랫폼 API(IAccessible2·UIA·ATK·AX)의 표 값을 이 판의 두 창이 보여 주는가? 그것은 「못 잰 것」인가 「잴 것이 없다」인가?

### 11. 정본 경계 긋기 (연결)

- `tbody` 삽입과 foster parenting 의 **정본**은 어느 주제의 몇 절인가?
- `innerHTML` 이 문맥에 따라 파싱하는 것의 정본은?
- `display: table` 계열의 CSS 레이아웃은 CSS 갈래에서 **어떻게 처리돼 있나**?
- 다음 편(18번)은 이 주제의 **무엇**을 이어받는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
