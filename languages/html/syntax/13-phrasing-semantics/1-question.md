# html/syntax/13 — 구절 시맨틱: `strong`/`em`/`b`/`i`/`mark`/`small`/`code`/`kbd`/`samp`/`abbr` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ 이 주제는 **두 창의 대조**다. 답할 때마다 「**어느 창으로 물었나**」를 같이 적어라 — 같은 질문이 창에 따라 「같다」와 「다르다」로 갈린다.
> ★ **명세·구현·관찰을 갈라라** — 역할 대응은 HTML-AAM 이, 트리는 Chrome 이 만든다.
> ★ 소스 펜스 첫 줄의 `<!-- 파일이름 -->` 은 **어느 파일을 던진 것인지 표시**이지 파일 내용이 아니다. 펜스의 소스는 전부 실제로 던진 파일이다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰이다. 이식성은 주장 범위 밖이다.
> 선행 — [05번 주제](../05-content-categories-and-models/1-question.md) · [11번 주제](../11-sectioning-and-landmarks/1-question.md)(창 ⑦).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 열 요소의 계산 스타일을 찍으면 (예측)

```html
<!-- html13b-13-grid.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>13 보이는 것 대 의미</title>
<style>body { font-family: sans-serif; }</style>
</head>
<body>
<p>
<strong id="strong">가</strong> <b id="b">가</b>
<em id="em">가</em> <i id="i">가</i>
<code id="code">가</code> <kbd id="kbd">가</kbd> <samp id="samp">가</samp>
<mark id="mark">가</mark> <small id="small">가</small>
<abbr id="abbr" title="월드 와이드 웹">WWW</abbr> <span id="span">가</span>
</p>
<script>
const 요소 = ["strong", "b", "em", "i", "code", "kbd", "samp", "mark", "small", "abbr", "span"];
window.__대상 = 요소.map(t => [t, "#" + t]);
const 열 = ["font-weight", "font-style", "font-family", "font-size", "background-color"];
const 칸 = (s, w) => String(s).padEnd(w);
window.__끝 = () => {
  const O = [];
  const 값 = {};
  for (const t of 요소) {
    const c = getComputedStyle(document.getElementById(t));
    값[t] = Object.fromEntries(열.map(k => [k, c.getPropertyValue(k)]));
    값[t]["역할"] = window.__AX[t].역할;
  }
  O.push("열 요소의 계산 스타일(창 ②)과 접근성 역할(창 ⑦)");
  O.push(칸("요소", 10) + 칸("weight", 8) + 칸("style", 8) + 칸("family", 12) + 칸("size", 11)
       + 칸("background", 18) + "역할");
  for (const t of 요소) {
    const v = 값[t];
    O.push(칸("<" + t + ">", 10) + 칸(v["font-weight"], 8) + 칸(v["font-style"], 8)
         + 칸(v["font-family"], 12) + 칸(v["font-size"], 11) + 칸(v["background-color"], 18) + v["역할"]);
  }
  O.push("");
  O.push("「똑같아 보이는 짝」끼리 견주면 — 어느 칸이 갈리나");
  const 짝 = [["strong", "b"], ["em", "i"], ["code", "kbd"], ["code", "samp"], ["kbd", "samp"]];
  const 모든열 = [...열, "역할"];
  let 스타일갈림 = 0, 스타일전체 = 0, 역할갈림 = 0, 역할전체 = 0;
  for (const [a, b] of 짝) {
    const 갈린 = 모든열.filter(k => 값[a][k] !== 값[b][k]);
    for (const k of 모든열) {
      const 다름 = 값[a][k] !== 값[b][k];
      if (k === "역할") { 역할전체++; if (다름) 역할갈림++; }
      else { 스타일전체++; if (다름) 스타일갈림++; }
    }
    O.push("  " + 칸(a + " 대 " + b, 16) + (갈린.length ? "갈린 열 = " + 갈린.join(", ") : "갈린 열 없음"));
  }
  O.push("");
  O.push("스타일 칸 갈림 = " + 스타일갈림 + " / " + 스타일전체 + " · 역할 칸 갈림 = " + 역할갈림 + " / " + 역할전체);
  O.push("갈린 칸 = " + (스타일갈림 + 역할갈림) + " / " + (스타일전체 + 역할전체));
  return O.join("\n");
};
</script>
</body>
</html>
```

- `<strong>` 과 `<b>` 의 `font-weight` 는 각각 몇인가?
- `<code>`·`<kbd>`·`<samp>` 의 `font-family` 와 `font-size` 는? 문단은 16px 이다.
- `<small>` 의 `font-size` 는?
- `<mark>` 의 `background-color` 는?

### 2. 같은 파일의 접근성 역할과 「갈린 칸」 (예측)

- 1번 소스 그대로다. 열 요소와 `<span>` 의 **역할**을 하나씩 예측하라.
- 다섯 짝(`strong`/`b` · `em`/`i` · `code`/`kbd` · `code`/`samp` · `kbd`/`samp`)의 마지막 줄 「**갈린 칸 = N / 30**」 의 N 은?
- 갈린 칸은 **어느 열에** 몰리는가?
- `<abbr>` 의 역할 이름은 무엇으로 찍히는가?

### 3. 겹쳐 쓰면 (예측)

```html
<!-- html13b-13-more.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>13 겹치기·지우기·이름</title>
<style>
body { font-family: sans-serif; }
#민strong { font-weight: 400; }
#굵span { font-weight: 700; }
</style>
</head>
<body>
<p id="겹">
<b id="b1">바깥 b<b id="b2">안 b<b id="b3">그 안 b</b></b></b>
<strong id="s1">바깥 strong<strong id="s2">안 strong</strong></strong>
<em id="e1">바깥 em<em id="e2">안 em</em></em>
<kbd id="k1"><kbd id="k2">Ctrl</kbd>+<kbd id="k3">C</kbd></kbd>
<small id="m1">바깥 small<small id="m2">안 small</small></small>
</p>
<p>
<strong id="민strong">굵기를 지운 strong</strong>
<span id="굵span">굵기를 입힌 span</span>
</p>
<p>
<abbr id="abbr" title="월드 와이드 웹">WWW</abbr>
<span id="span" title="월드 와이드 웹">WWW</span>
<abbr id="맨abbr">WWW</abbr>
</p>
<p id="글"><strong>꼭</strong> <em>지금</em> <mark>여기</mark> <kbd>Enter</kbd></p>
<script>
window.__대상 = [["b1", "#b1"], ["b2", "#b2"], ["b3", "#b3"], ["s1", "#s1"], ["s2", "#s2"], ["e1", "#e1"], ["e2", "#e2"],
  ["k1", "#k1"], ["k2", "#k2"], ["m1", "#m1"], ["m2", "#m2"],
  ["민strong", "#민strong"], ["굵span", "#굵span"],
  ["abbr", "#abbr"], ["span", "#span"], ["맨abbr", "#맨abbr"]];
const $ = id => document.getElementById(id);
const cs = id => getComputedStyle($(id));
const J = v => JSON.stringify(v);
window.__끝 = () => {
  const O = [];
  O.push("(가) 겹쳐 쓰면 — bolder·smaller 는 「더」라서 쌓인다");
  for (const id of ["b1", "b2", "b3", "s1", "s2"])
    O.push("  " + ("#" + id).padEnd(6) + "font-weight = " + cs(id).fontWeight.padEnd(5) + "역할 = " + __AX[id].역할);
  for (const id of ["e1", "e2"])
    O.push("  " + ("#" + id).padEnd(6) + "font-style = " + cs(id).fontStyle.padEnd(8) + "역할 = " + __AX[id].역할
      + "   level 같은 속성 = " + J(__AX[id].속성));
  for (const id of ["k1", "k2", "m1", "m2"])
    O.push("  " + ("#" + id).padEnd(6) + "font-size = " + cs(id).fontSize.padEnd(10) + "역할 = " + __AX[id].역할);
  O.push("");
  O.push("(나) 모양과 의미를 엇갈리게 — 스타일을 지운 strong · 스타일을 입힌 span");
  for (const id of ["민strong", "굵span"])
    O.push("  " + ("#" + id).padEnd(10) + "font-weight = " + cs(id).fontWeight.padEnd(5) + "역할 = " + __AX[id].역할);
  O.push("");
  O.push("(다) title 은 무엇이 되나 — 이름인가 설명인가");
  for (const id of ["abbr", "span", "맨abbr"])
    O.push("  " + ("#" + id).padEnd(8) + "역할 = " + __AX[id].역할.padEnd(9) + "이름 = " + J(__AX[id].이름).padEnd(12)
      + "설명 = " + J(__AX[id].설명) + "   text-decoration = " + cs(id).textDecorationLine + " " + cs(id).textDecorationStyle);
  O.push("");
  O.push("(라) 창 ③ — 의미는 글자에 남나");
  O.push("  innerText   = " + J($("글").innerText));
  O.push("  textContent = " + J($("글").textContent));
  return O.join("\n");
};
</script>
</body>
</html>
```

- `#b1`·`#b2`·`#b3` 의 `font-weight` 는?
- `#m1`·`#m2`(small 안 small)와 `#k1`·`#k2`(kbd 안 kbd)의 `font-size` 는?
- 안쪽 `<strong>`·`<em>` 의 역할에 **겹친 수**가 나타나는가?

### 4. 모양과 의미를 엇갈리게 놓으면 (예측)

- 3번 소스의 둘째 문단이다. `#민strong`(굵기를 지운 strong)의 역할은?
- `#굵span`(굵기를 입힌 span)의 역할은?
- 그 두 답이 「CSS 와 역할」의 관계에 대해 말하는 것은?

### 5. `title` 은 무엇이 되나 (예측)

- 3번 소스의 셋째 문단이다. `<abbr title>` 의 이름과 설명은?
- 같은 `title` 을 단 `<span>` 은?
- `title` 이 없는 `<abbr>` 에 점선 밑줄이 있는가? 왜인가?

### 6. `<small>` 은 「작은 글씨」가 아니다 (왜)

- 명세가 `<small>` 에 준 뜻은 무엇인가?
- 그 뜻이 **역할로 드러나는가**? 드러나지 않으면 무엇이 그 뜻을 지키는가?
- `<small>` 을 겹치면 크기는 어떻게 되는가? 그것이 왜 사고가 되는가?

### 7. 「보이는 것은 같다」를 무엇으로 증명하나 (경계)

- 창 ② 가 「같다」고 답한 것은 틀린 답인가?
- 같은 질문을 창 ⑦ 로 다시 물은 것은 제 몇의 상태인가? 그 이름을 대라.
- 창 ① 과 창 ③ 은 이 주제에서 무엇을 보였나?

### 8. 명세·구현·관찰 가르기 (경계)

- `<strong>` → `strong` 역할은 **누가** 정하나?
- `<abbr>` 가 `Abbr` 로 찍힌 것은 명세인가 구현인가? 근거는?
- `<code>` 의 `13px` 은 어느 층의 값인가?

### 9. 이 판이 못 보는 것 (경계)

- 「스크린리더가 `<strong>` 을 힘주어 읽는다」를 이 문서가 실측으로 쓸 수 있는가?
- 「`<strong>` 이 SEO 에 좋다」는 어떤 상태의 주장인가 — 「못 잰 것」인가 「잴 것이 없다」인가?
- CDP 트리가 HTML-AAM 의 **플랫폼 API 층**을 보여 주는가?

### 10. 정본 경계 긋기 (연결)

- **구절 콘텐츠라는 카테고리**의 정본은 어느 주제인가?
- **UA 스타일시트가 캐스케이드의 어디에 있나**의 정본은?
- **`title` 이 이름과 설명 중 어디로 가나의 전체 규칙**은?
- 다음 편(14번)이 이어받는 요소는 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
