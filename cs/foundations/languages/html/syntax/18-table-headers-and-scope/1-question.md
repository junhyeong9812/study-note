# html/syntax/18 — 표 머리 연결: `th`·`scope`·`headers`/`id`·`rowspan`/`colspan` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ 이 주제는 **명세 계산 대 트리**의 대조다. 답할 때마다 「**명세가 정한 것**」과 「**Chrome 의 트리가 준 것**」을 따로 적어라.
> ★ 명세 쪽 답은 [2-summary.md](2-summary.md) (3) 에 실린 **모델 스크립트**가 계산한다 — 명세 4.9.12 「표 처리 모델」을 옮긴 것이다. 먼저 **명세 문장으로** 답하고 스크립트로 확인하라.
> ★ 소스 펜스 첫 줄의 `<!-- 파일이름 -->` 은 **어느 파일을 던진 것인지 표시**이지 파일 내용이 아니다. 펜스의 소스는 전부 실제로 던진 파일이다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰이다. 이식성은 주장 범위 밖이다.
> 선행 — [17번 주제](../17-table-structure/1-question.md)(표 구조 · 표 처리 모델의 좌표).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `th` 스무 개의 머리 종류와 역할 (예측)

```html
<!-- html17b-18-scope.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>18 th 는 무슨 머리인가</title>
<script src="html17b-18-model.js"></script>
</head>
<body>
<table data-k="첫 행이 th"><tr><th id="a1">이름</th><th id="a2">값</th></tr><tr><td>사과</td><td>1</td></tr></table>
<table data-k="첫 열이 th"><tr><th id="b1">사과</th><td>1</td></tr><tr><th id="b2">배</th><td>2</td></tr></table>
<table data-k="첫 행과 첫 열"><tr><th id="c1">과일</th><th id="c2">값</th></tr><tr><th id="c3">사과</th><td>1</td></tr></table>
<table data-k="가운데 th"><tr><td>가</td><th id="d1">나</th><td>다</td></tr><tr><td>1</td><td>2</td><td>3</td></tr></table>
<table data-k="th 만 있는 표"><tr><th id="e1">가</th><th id="e2">나</th></tr><tr><th id="e3">다</th><th id="e4">라</th></tr></table>
<table data-k="첫 행에 scope=row"><tr><th id="f1" scope="row">가</th><th id="f2" scope="row">나</th></tr><tr><td>1</td><td>2</td></tr></table>
<table data-k="첫 열에 scope=col"><tr><th id="g1" scope="col">사과</th><td>1</td></tr><tr><th id="g2" scope="col">배</th><td>2</td></tr></table>
<table data-k="모르는 scope 값"><tr><th id="h1" scope="위">사과</th><td>1</td></tr><tr><th id="h2" scope="위">배</th><td>2</td></tr></table>
<table data-k="scope=colgroup"><colgroup span="2"></colgroup><tr><th id="i1" scope="colgroup" colspan="2">묶음</th></tr><tr><td>1</td><td>2</td></tr></table>
<table data-k="scope=rowgroup"><tbody><tr><th id="j1" scope="rowgroup">묶음</th><td>1</td></tr><tr><td>2</td><td>3</td></tr></tbody></table>
<script>
window.__대상 = [...document.querySelectorAll("th")].map(e => [e.id, "#" + e.id]);
window.__끝 = () => {
  const O = ["th 마다 — 명세의 표 모델이 정한 머리 종류(스크립트 계산) · 그 종류에 HTML-AAM 이 대응시키는 역할 · 트리의 역할"];
  const AAM = { "열": "columnheader", "열묶음": "columnheader", "행": "rowheader", "행묶음": "rowheader", "아님": "cell" };
  let 갈림 = 0, 전체 = 0;
  for (const t of document.querySelectorAll("table[data-k]")) {
    const 표 = 표만들기(t);
    for (const c of 표.칸.filter(c => c.머리)) {
      const 종류 = 머리종류(표, c), 기대 = AAM[종류], 트리 = __AX[c.el.id].역할;
      전체++; if (기대 !== 트리) 갈림++;
      O.push("  " + t.dataset.k.padEnd(18) + ("#" + c.el.id).padEnd(4) + "(" + c.x + "," + c.y + ")  명세 = " + 종류.padEnd(4)
        + "-> " + 기대.padEnd(13) + "트리 = " + 트리.padEnd(13) + (기대 === 트리 ? "" : "<- 갈림"));
    }
  }
  O.push("");
  O.push("갈린 칸 = " + 갈림 + " / " + 전체);
  return O.join("\n");
};
</script>
</body>
</html>
```

- 표 열 개의 `th` 스무 개 각각에 대해 — 명세의 머리 종류(열·행·열묶음·행묶음·아님)는? 트리의 역할은?
- 마지막 줄 「**갈린 칸 = N / 20**」 의 N 은? 갈린 칸이 있다면 어느 표인가?
- `th` 만 있는 표의 **둘째 행** `th` 는 무슨 머리인가?
- `scope="위"` 는 어느 상태로 읽히는가?

### 2. 복합 머리 표의 좌표와 역할 (예측)

```html
<!-- html17b-18-grid.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>18 복합 머리 표</title>
<script src="html17b-18-model.js"></script>
</head>
<body>
<table id="판매">
<caption>지역별 판매</caption>
<colgroup><col></colgroup><colgroup span="2"></colgroup><colgroup span="2"></colgroup>
<thead>
<tr><td id="모서리" rowspan="2"></td><th id="상" colspan="2" scope="colgroup">상반기</th><th id="하" colspan="2" scope="colgroup">하반기</th></tr>
<tr><th id="m1">1월</th><th id="m2" abbr="이월">2월</th><th id="m7">7월</th><th id="m8">8월</th></tr>
</thead>
<tbody>
<tr><th id="서울" scope="row">서울</th><td id="c21">1</td><td id="c22" headers="서울 m2 상">2</td><td id="c23">3</td><td id="c24" rowspan="0">4</td></tr>
<tr><th id="인천" scope="row">인천</th><td id="c31" headers="m1 인천">5</td><td id="c32" headers="m2 서울">6</td><td id="c33" headers="없는아이디">7</td><td id="c34">8</td></tr>
</tbody>
<tbody>
<tr><th id="부산" rowspan="2">부산</th><td id="c41">9</td><td id="c42" colspan="2">10</td><td id="c44">11</td></tr>
<tr><td id="c51">12</td><td id="c52">13</td><td id="c53">14</td><td id="c54">15</td></tr>
</tbody>
</table>
<script>
// 둘째 표 — 첫 표를 복제해 모서리의 <td> 만 <th> 로 바꾼다. id 와 headers 에는 「_2」를 붙인다.
const 둘째 = document.getElementById("판매").cloneNode(true);
둘째.id = "판매_2";
for (const e of 둘째.querySelectorAll("[id]")) e.id += "_2";
for (const e of 둘째.querySelectorAll("[headers]"))
  e.setAttribute("headers", e.getAttribute("headers").split(" ").map(t => t + "_2").join(" "));
const 옛 = 둘째.querySelector("#모서리_2"), 새 = document.createElement("th");
for (const a of 옛.attributes) 새.setAttribute(a.name, a.value);
옛.replaceWith(새);
document.body.append(둘째);
window.__대상 = [...document.querySelectorAll("th, td")].map(e => [e.id, "#" + e.id]);
window.__내부 = true;
const AAM = { "열": "columnheader", "열묶음": "columnheader", "행": "rowheader", "행묶음": "rowheader", "아님": "cell" };
const 이름 = cs => cs.length ? cs.map(c => c.el.id).join(" ") : "—";
const 트리 = c => { const a = __INT[c.el.id].속성; return { x: +a.tableCellColumnIndex, y: +a.tableCellRowIndex,
  w: +a.tableCellColumnSpan, h: +a.tableCellRowSpan, 역할: __AX[c.el.id].역할 }; };
function 재기(id, O, 자세히) {
  const 표 = 표만들기(document.getElementById(id));
  let 좌갈 = 0, 좌전 = 0, 역갈 = 0, 역전 = 0;
  for (const c of 표.칸) {
    const t = 트리(c), 명 = [c.x, c.y, c.w, c.h], 트 = [t.x, t.y, t.w, t.h];
    const 갈린 = 명.filter((v, i) => v !== 트[i]).length;
    좌갈 += 갈린; 좌전 += 4;
    const 기대 = c.머리 ? AAM[머리종류(표, c)] : "cell";
    역전++; if (기대 !== t.역할) 역갈++;
    if (자세히 === "좌표") O.push("  " + ("#" + c.el.id).padEnd(6) + "명세 (" + 명.join(",") + ")  트리 (" + 트.join(",") + ")"
      + (갈린 ? "  <- 좌표 " + 갈린 + "칸" : "        ") + "   역할 명세->" + 기대.padEnd(13) + "트리 " + t.역할
      + (기대 !== t.역할 ? "  <- 역할" : ""));
  }
  const 요약1 = "  좌표 칸 갈림 = " + 좌갈 + " / " + 좌전 + " · 역할 칸 갈림 = " + 역갈 + " / " + 역전
    + " · 표 크기 명세 " + 표.폭 + "x" + 표.높이 + " / 트리 " + __INT[id].속성.tableColumnCount + "x" + __INT[id].속성.tableRowCount;
  const 머리칸 = 표.칸.map(c => ({ c, t: 트리(c) }));
  let 같음 = 0, 전체 = 0, 우연 = 0;
  for (const c of 표.칸.filter(c => !c.머리 && c.el.textContent.trim())) {
    const t = 트리(c);
    const 겹침 = (a, n, b, m) => a < b + Math.max(m, 1) && b < a + Math.max(n, 1);
    const 단순 = 머리칸.filter(({ t: h }) =>
      (h.역할 === "rowheader" && 겹침(h.y, h.h, t.y, t.h)) ||
      (h.역할 === "columnheader" && 겹침(h.x, h.w, t.x, t.w))).map(({ c }) => c);
    const 명세 = 머리찾기(표, c);
    const 정렬 = cs => cs.map(k => k.el.id).sort().join(" ");
    const 일치 = 정렬(명세) === 정렬(단순);
    전체++; if (일치) { 같음++; if (c.el.hasAttribute("headers")) 우연++; }
    if (자세히 === "머리") O.push("  " + ("#" + c.el.id).padEnd(8)
      + (c.el.hasAttribute("headers") ? "headers=" + JSON.stringify(c.el.getAttribute("headers")) : "").padEnd(26)
      + "명세 = " + 이름(명세).padEnd(24) + "단순 규칙 = " + 이름(단순).padEnd(24) + (일치 ? "같음" : "다름"));
  }
  const 요약2 = "  머리가 같은 칸 = " + 같음 + " / " + 전체 + " · 그중 headers 속성이 있는 칸 = " + 우연;
  return [요약1, 요약2];
}
window.__끝 = () => {
  const O = [];
  O.push("(가) 첫 표(모서리 td) — 칸마다 좌표 (x,y,w,h)와 역할: 명세 표 모델(스크립트) 대 트리(내부 덤프 tableCell* · CDP 역할)");
  const [a1, a2] = 재기("판매", O, "좌표");
  O.push(a1);
  O.push("");
  O.push("(나) 첫 표 — 글자가 있는 데이터 칸마다 머리: 명세 알고리즘(스크립트) 대 「트리 재료로 셈한 단순 규칙」(같은 행 rowheader + 같은 열 columnheader)");
  재기("판매", O, "머리");
  O.push(a2);
  O.push("");
  O.push("(다) 둘째 표(모서리 th) — 같은 머리 격자와 두 요약");
  const [b1, b2] = 재기("판매_2", O, "머리");
  O.push(b2);
  O.push(b1);
  O.push("");
  O.push("(라) 트리가 셀 노드에 단 속성 — #c31(headers 있음) · #c21(없음) · #m2(abbr 있음)");
  for (const id of ["c31", "c21"]) O.push("  #" + id + "  CDP properties = " + JSON.stringify(Object.keys(__AX[id].속성))
    + " · 내부 덤프 속성 중 이름에 header 가 든 것 = " + JSON.stringify(Object.keys(__INT[id].속성).filter(k => /header/i.test(k))));
  O.push("  #m2   abbr=" + JSON.stringify(document.getElementById("m2").getAttribute("abbr")) + " · CDP 이름 = " + JSON.stringify(__AX.m2.이름)
    + " · CDP 설명 = " + JSON.stringify(__AX.m2.설명) + " · 내부 덤프 속성 중 이름에 abbr 가 든 것 = "
    + JSON.stringify(Object.keys(__INT.m2.속성).filter(k => /abbr/i.test(k))));
  O.push("");
  O.push("(마) 창 ② — rowspan=0 인 #c24 와 이웃의 화면 상자(위·높이 px), 그리고 #c34 의 가로 순서");
  const R = id => document.getElementById(id).getBoundingClientRect();
  for (const id of ["c23", "c24", "c33", "c34"]) O.push("  #" + id + "  top = " + R(id).top.toFixed(0) + " · height = " + R(id).height.toFixed(0)
    + " · left = " + R(id).left.toFixed(0));
  O.push("  #c34 의 left 가 #c24 의 left 와 같은가 = " + (R("c34").left === R("c24").left));
  return O.join("\n");
};
</script>
</body>
</html>
```

- 첫 표(`#판매`)의 칸 스물다섯 각각의 **명세 좌표 (x,y,w,h)** 와 **트리 좌표**가 갈리는 칸은 어디인가?
- 「**좌표 칸 갈림 = N / 100**」·「**역할 칸 갈림 = N / 25**」의 N 은?
- 표 크기는 명세와 트리가 각각 몇 × 몇인가?
- 역할이 갈리는 칸이 있다면 어느 칸들인가?

### 3. `rowspan="0"` 은 어디까지 가나 (예측)

- 2번 소스의 `#c24` 다. 내부 덤프의 `tableCellRowSpan` 은 몇으로 찍히는가?
- 화면에서 `#c24` 는 몇 행 높이인가? `#c34` 는 `#c24` 의 왼쪽·같은 열·오른쪽 중 어디에 그려지는가?
- 트리의 `#c34` 는 몇 번 열인가?

### 4. 첫 표의 데이터 칸이 받는 머리 (예측)

- 2번 소스의 첫 표다. 명세 알고리즘이 **`#c21`·`#c24`·`#c31`·`#c32`·`#c33`·`#c41`·`#c42`** 에 배정하는 머리를 각각 적어라.
- 같은 칸들을 「트리의 좌표·역할로 센 단순 규칙」(같은 행에 걸친 `rowheader` + 같은 열에 걸친 `columnheader`)으로 세면?
- 열다섯 칸 중 두 방법이 **같은 칸**은 몇인가? 그중 `headers` 속성이 있는 칸은?

### 5. 모서리 칸 하나를 바꾼 둘째 표 (예측)

- 둘째 표(`#판매_2`)는 모서리의 `<td>` 를 `<th>` 로 바꾼 것뿐이다. **역할 칸 갈림**과 **좌표 칸 갈림**은 각각 몇 / 몇이 되는가?
- 머리가 같은 칸은 몇 / 15 가 되는가? 그중 `headers` 속성이 있는 칸은?
- 그래도 다른 칸들은 각각 **왜** 다른가?

### 6. 표 열 개는 데이터 표인가 (예측)

```html
<!-- html17b-18-layout.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>18 레이아웃 표 판정</title>
<style>.선 td { border: 1px solid black; }</style>
</head>
<body>
<table id="t1"><tr><td>왼쪽</td><td>오른쪽</td></tr></table>
<table id="t2"><tr><td>1</td><td>2</td><td>3</td></tr><tr><td>4</td><td>5</td><td>6</td></tr><tr><td>7</td><td>8</td><td>9</td></tr></table>
<table id="t3" border="1"><tr><td>왼쪽</td><td>오른쪽</td></tr></table>
<table id="t4" class="선"><tr><td>왼쪽</td><td>오른쪽</td></tr></table>
<table id="t5"><tr><th>머리</th><td>오른쪽</td></tr></table>
<table id="t6"><caption>캡션</caption><tr><td>왼쪽</td><td>오른쪽</td></tr></table>
<table id="t7" role="table"><tr><td>왼쪽</td><td>오른쪽</td></tr></table>
<table id="t8" role="presentation"><tr><td>왼쪽</td><td>오른쪽</td></tr></table>
<table id="t9" role="presentation"><caption>캡션</caption><tr><th>머리</th><td>오른쪽</td></tr></table>
<table id="t10"></table>
<script>
const 설명 = { t1: "td 만 1행 2칸", t2: "td 만 3행 3칸", t3: "td 만 + border=1", t4: "td 만 + CSS 테두리",
  t5: "th 하나", t6: "caption 하나", t7: "td 만 + role=table", t8: "td 만 + role=presentation",
  t9: "caption·th + role=presentation", t10: "td 만 25행 2칸" };
for (let i = 0; i < 25; i++) document.getElementById("t10").insertRow().append(
  Object.assign(document.createElement("td"), { textContent: "가" }), Object.assign(document.createElement("td"), { textContent: "나" }));
const 표 = Object.keys(설명);
for (const k of 표) document.querySelector("#" + k + " td").id = k + "셀";
window.__대상 = 표.flatMap(k => [[k, "#" + k], [k + "셀", "#" + k + "셀"]]);
window.__내부 = true;
window.__끝 = () => {
  const O = ["표마다 — CDP 역할(표 · 첫 td) · 내부 덤프 역할(표 · 첫 td) · 무시 여부"];
  let 데이터 = 0;
  for (const k of 표) {
    const a = __AX[k], c = __AX[k + "셀"];
    const 내 = n => !n ? "(덤프에 없음)" : n.속성.ignored ? "(무시)" : n.역할, i = 내(__INT[k]), ic = 내(__INT[k + "셀"]);
    if (i === "table") 데이터++;
    O.push("  " + 설명[k].padEnd(32) + "CDP 표 = " + (a.무시 ? "(무시)" : a.역할).padEnd(13) + "첫 td = " + (c.무시 ? "(무시)" : c.역할).padEnd(17)
      + "내부 표 = " + i.padEnd(12) + "첫 td = " + ic);
  }
  O.push("");
  O.push("내부 덤프가 table 로 판정한 표 = " + 데이터 + " / " + 표.length);
  return O.join("\n");
};
</script>
</body>
</html>
```

- 표 열 개 각각의 CDP 역할(표·첫 `td`)과 내부 덤프 역할은?
- 마지막 줄 「**내부 덤프가 table 로 판정한 표 = N / 10**」 의 N 은?
- `role="presentation"` 을 준 두 표에서 **표 노드**는 어떻게 되는가?

### 7. 머리 관계는 트리의 어디에 있나 (경계)

- 셀 노드의 CDP `properties` 와 내부 덤프 속성에서 `headers`·`abbr` 의 흔적을 찾으면 무엇이 나오는가?
- HTML-AAM 은 `headers` 속성을 WAI-ARIA 층과 플랫폼 API 층에 각각 어떻게 대응시키나?
- 그래서 이 주제는 「이 칸의 머리」를 **무엇으로** 물었나? 그것은 제 몇의 상태인가?

### 8. 두 표의 「명세 → 역할」 열 (왜)

- 2번(모서리 `td`)과 5번(모서리 `th`)의 표는 한 칸만 다르다. 두 표의 「명세 → 역할」 열이 어떻게 되는지 명세의 **열 머리·행 머리 정의** 문장으로 설명하라.
- 명세는 빈 `th` 모서리를 머리 목록에 넣는가? 어느 단계가 그것을 정하나?
- `scope` 를 명시한 칸은 모서리의 영향을 받는가?

### 9. 명세·구현·관찰 가르기 (경계)

- 1\~3번에서 **명세와 Chrome 이 갈린 자리**를 전부 대라. 각각 명세의 어느 문장과 갈렸나?
- 4번·5번의 「같은 칸」을 「Chrome 이 `headers` 를 반영한다」의 근거로 쓸 수 있는가? 쓸 수 없는 칸이 있다면 무엇이고 왜인가?
- 레이아웃 표 판정은 명세가 정하나?

### 10. 이 판이 못 보는 것 (경계)

- 「스크린리더가 `#c32` 를 『2월, 서울, 6』으로 읽는다」를 이 문서가 쓸 수 있는가?
- **Chrome 이 `headers` 를 존중하나**를 이 판에서 판정할 수 있는가? 판정하려면 어느 층을 봐야 하나?

### 11. 정본 경계 긋기 (연결)

- 표 처리 모델의 **좌표**와 행 묶음은 어느 주제가 정본인가?
- `role="presentation"` 으로 암묵 역할을 덮어쓰는 규칙의 정본은?
- 「우연히 맞는 칸을 세는 격자」의 원형은 어느 주제의 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
