# html/syntax/09 — 스타일시트·리소스 힌트 연결: `<link rel>`·`media`·`preload`/`preconnect`/`modulepreload` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ 이 주제는 「**받나 · 막나 · 먹나**」 셋을 **갈라서** 답한다. 하나로 뭉치면 전부 틀린다.
> ★ **「무시된다」를 한 낱말로 쓰지 마라** — 요청이 안 나가는 것과, 받아 놓고 안 쓰는 것과, 받아서 담았는데 규칙이 안 먹는 것이 **다 다르다.**
> ★ **네트워크가 없는 판이다.** 무엇을 근거로 댈 수 있고 무엇이 「못 잰 것」인지도 같이 답하라.
> ★ 소스 펜스 첫 줄의 `<!-- 파일이름 -->`·`/* 파일이름 */` 은 **어느 파일을 던진 것인지 표시**이지 파일 내용이 아니다.
> 선행 — [08번 주제](../08-script-loading/1-question.md) · CSS 갈래 목록([`css/syntax/README.md`](../../../css/syntax/README.md))의 **38번**.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 느린 스타일시트를 사이에 끼우면 (예측)

```html
<!-- html09b-block.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>스타일시트가 무엇을 막나</title>
<script src="html09b-probe.js"></script>
<script>window.__t0 = performance.now(); P("① 링크 앞 인라인 스크립트");</script>
<link rel="stylesheet" href="html09b-slow.css">
<script>P("② 링크 뒤 인라인 스크립트 — 여기까지 " + (performance.now() - window.__t0 >= 300 ? "300ms 이상" : "300ms 미만") + " 걸렸다");</script>
</head>
<body>
<p id="과녁3">과녁3</p>
<script>
window.__끝 = function () {
  P("③ 트리의 <p> 개수 = " + document.querySelectorAll("p").length);
  P("④ 계산값 color = " + getComputedStyle(document.getElementById("과녁3")).color);
};
</script>
</body>
</html>
```

```css
/* html09b-slow.css */
#과녁3 { color: rgb(66, 66, 66); }
```

이 파일은 **이름에 `-slow` 가 들어 있어 서버가 0.5초 늦게 준다.**

- ② 번 줄은 「300ms 이상」과 「300ms 미만」 중 무엇을 찍는가?
- ③ 번의 `<p>` 개수는 몇인가? 그 수가 뜻하는 것은?
- ④ 번의 계산값은 무엇인가?
- 이 실험이 보이는 「막히는 것」과 「안 막히는 것」은 각각 무엇인가?

### 2. 같은 자리에 `media="print"` 만 붙이면 (예측)

```html
<!-- html09b-block-print.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>media 가 안 맞으면 안 막는다</title>
<script src="html09b-probe.js"></script>
<script>window.__t0 = performance.now(); P("① 링크 앞 인라인 스크립트");</script>
<link rel="stylesheet" href="html09b-print-slow.css" media="print">
<script>P("② 링크 뒤 인라인 스크립트 — 여기까지 " + (performance.now() - window.__t0 >= 300 ? "300ms 이상" : "300ms 미만") + " 걸렸다");</script>
</head>
<body>
<p id="과녁4">과녁4</p>
<script>
window.__끝 = function () {
  P("③ 트리의 <p> 개수 = " + document.querySelectorAll("p").length);
  P("④ 계산값 color = " + getComputedStyle(document.getElementById("과녁4")).color);
  P("⑤ document.styleSheets.length = " + document.styleSheets.length);
};
</script>
</body>
</html>
```

- ② 번 줄이 이번에는 무엇을 찍는가?
- ④ 번의 계산값은 무엇인가? 왜 그런가?
- ⑤ 번의 `document.styleSheets.length` 는 몇인가? **그 수가 이 문항의 핵심**이다.

### 3. `media` 를 네 가지로 걸면 (예측)

```html
<!-- html09b-media.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>media 가 안 맞는 스타일시트</title>
<script src="html09b-probe.js"></script>
<link rel="stylesheet" href="html09b-base.css">
<link rel="stylesheet" href="html09b-screen.css" media="screen">
<link rel="stylesheet" href="html09b-print.css" media="print">
<link rel="stylesheet" href="html09b-wide.css" media="(min-width: 99999px)">
</head>
<body>
<p id="과녁">과녁</p>
<script>
window.__끝 = function () {
  P("document.styleSheets.length = " + document.styleSheets.length);
  for (const s of document.styleSheets) {
    P("  " + s.href.split("/").pop()
      + "   media=" + JSON.stringify(s.media.mediaText)
      + "   규칙 " + s.cssRules.length + "개"
      + "   disabled=" + s.disabled);
  }
  const c = getComputedStyle(document.getElementById("과녁"));
  P("계산값 color            = " + c.color            + "   <- base.css");
  P("계산값 outline-color    = " + c.outlineColor     + "   <- screen.css");
  P("계산값 background-color = " + c.backgroundColor  + "   <- print.css");
  P("계산값 padding-top      = " + c.paddingTop      + "   <- wide.css");
};
</script>
</body>
</html>
```

- `document.styleSheets.length` 는 몇인가?
- 각 시트의 `cssRules` 개수와 `disabled` 값을 예측하라.
- 네 계산값 중 **바뀐 것과 안 바뀐 것**을 갈라라.
- **서버 요청 로그에는 몇 개가 찍히는가?** 이름을 대라.

### 4. `rel` 을 일곱 가지로 걸면 (예측)

```html
<!-- html09b-rel-unknown.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>rel 값을 모르면</title>
<script src="html09b-probe.js"></script>
<link id="ㄱ" rel="stylesheet"           href="html09b-rel.css">
<link id="ㄴ" rel="Stylesheet"           href="html09b-rel.css?upper">
<link id="ㄷ" rel="stylesheet-zzz"       href="html09b-rel.css?unknown">
<link id="ㄹ"                            href="html09b-rel.css?norel">
<link id="ㅁ" rel=""                     href="html09b-rel.css?empty">
<link id="ㅂ" rel="alternate stylesheet" href="html09b-alt.css" title="대체">
<link id="ㅅ" rel="preload stylesheet"   href="html09b-rel.css?two" as="style">
</head>
<body>
<p id="과녁2">과녁2</p>
<script>
window.__끝 = function () {
  for (const id of ["ㄱ","ㄴ","ㄷ","ㄹ","ㅁ","ㅂ","ㅅ"]) {
    const el = document.getElementById(id);
    P(id + "  rel=" + JSON.stringify(el.getAttribute("rel"))
      + "   relList=[" + [...el.relList].join(",") + "]"
      + "   sheet=" + (el.sheet ? "있음(규칙 " + el.sheet.cssRules.length + ", disabled=" + el.sheet.disabled + ")" : "null"));
  }
  P("document.styleSheets.length = " + document.styleSheets.length);
  const c2 = getComputedStyle(document.getElementById("과녁2"));
  P("계산값 color      = " + c2.color      + "   <- html09b-rel.css (평범한 stylesheet)");
  P("계산값 font-style = " + c2.fontStyle  + "   <- html09b-alt.css (alternate stylesheet)");
};
</script>
</body>
</html>
```

- 일곱 개 각각의 `sheet` 가 `null` 인지 아닌지 예측하라.
- `document.styleSheets.length` 는 몇인가?
- **서버 요청 로그에 안 나타나는 것**은 어느 것들인가?
- `alternate stylesheet` 의 `font-style` 계산값은 무엇인가? 그 답이 이상한 이유는?

### 5. `preload` 에 `as` 를 빼면 (예측)

```html
<!-- html09b-preload-noas.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>preload 에 as 가 없으면</title>
<link rel="preload" href="html09b-noas.css">
<link rel="preload" href="html09b-withas.css" as="style">
<link rel="preload" href="html09b-badas.css" as="zzznope">
</head>
<body>
<p>as 세 가지</p>
</body>
</html>
```

- 콘솔에 몇 줄이 나는가? 어느 줄 번호를 가리키는가?
- 세 파일 중 **실제로 요청되는 것**은 몇 개인가?
- 화면이나 예외로 이것을 알아챌 수 있는가?

### 6. 네 가지 힌트를 한 문서에 걸면 (예측)

```html
<!-- html09b-hints.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>리소스 힌트 네 가지</title>
<script src="html09b-probe.js"></script>
<link rel="preload"       href="html09b-hint.css" as="style">
<link rel="modulepreload" href="html09b-mod-b.mjs">
<link rel="preconnect"    href="https://example.invalid">
<link rel="dns-prefetch"  href="https://example.invalid">
<link rel="stylesheet"    href="html09b-hint.css">
<script type="module" src="html09b-mod-a.mjs"></script>
</head>
<body>
<p id="과녁5">과녁5</p>
<script>
window.__끝 = function () {
  P("계산값 color = " + getComputedStyle(document.getElementById("과녁5")).color);
  for (const el of document.querySelectorAll("link")) {
    P(("rel=" + el.rel).padEnd(24)
      + ("relList=[" + [...el.relList].join(",") + "]").padEnd(26)
      + "sheet=" + (el.sheet ? "있음" : "null"));
  }
};
</script>
</body>
</html>
```

- 요청 로그에 몇 개가 찍히는가? `html09b-hint.css` 는 **몇 번** 요청되는가?
- `html09b-mod-b.mjs` 는 몇 번 요청되는가? 왜 그런가?
- `preconnect`·`dns-prefetch` 는 로그에 무엇을 남기는가?
- 그 둘에 대해 이 판이 **댈 수 있는 근거**와 **못 대는 것**을 갈라라.

### 7. 스타일시트는 정확히 무엇을 막는가 (왜)

- 「렌더 차단」이 막는 것은 파싱인가 렌더인가 스크립트인가?
- 왜 **스크립트**까지 막는가? 그 이유를 한 문장으로 대라.
- 그래서 `<head>` 의 느린 스타일시트가 만드는 증상은 무엇인가?

### 8. 「무시된다」의 세 가지 (경계)

- `rel` 을 모를 때 · `media` 가 안 맞을 때 · `alternate stylesheet` 일 때 — **어디까지 일어나고 어디서 멈추는가**를 각각 대라.
- 셋을 가르는 **관찰 수단**은 각각 무엇인가?
- 「계산값이 안 바뀌었다」만 보고는 왜 셋을 못 가르는가?

### 9. `<link>` 를 `<body>` 에 두면 (경계)

- 파서가 그것을 `<head>` 로 옮기는가?
- 스타일시트로 동작하는가?
- **자기보다 앞에 있는 요소**에도 규칙이 먹는가?
- 그런데도 `<head>` 를 권하는 이유는 무엇인가? 그 이유를 이 판에서 **쟀는가**?

### 10. 이 판이 못 잰 것 (경계)

- `preconnect` 가 실제로 아끼는 시간을 이 판에서 잴 수 있는가? 왜인가?
- 그것을 문서에 「안 돌려 봄」으로 적으면 왜 틀린가?
- 「못 잰 것」으로 적을 때 함께 적어야 하는 것은 무엇인가?

### 11. 정본 경계 긋기 (연결)

- 미디어 쿼리 **문법**(범위 구문·논리 결합)의 정본은 어느 갈래인가?
- 연결된 뒤 규칙들이 겨루는 이야기의 정본은?
- `getComputedStyle` 이라는 **API 표면**의 정본은?
- `rel="canonical"`·`rel="alternate hreflang"` 의 정본은 이 갈래의 몇 번인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
