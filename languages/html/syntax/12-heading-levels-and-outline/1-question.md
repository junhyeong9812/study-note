# html/syntax/12 — 제목 레벨과 문서 개요: `h1`\~`h6` 가 실제로 계산되는 방식 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ 이 주제에는 **널리 퍼진 오해**가 하나 있다. 답하기 전에 **자기가 그것을 믿고 있는지부터** 확인하라.
> ★★ **「레벨」을 무엇으로 재는지**도 문항이다. 태그 이름을 세는 것은 증명이 아니다 — 그것은 입력이다.
> ★ **관찰과 보장을 갈라라** — 글꼴 크기는 관찰이고 레벨은 명세다.
> ★ 소스 펜스 첫 줄의 `<!-- 파일이름 -->` 은 **어느 파일을 던진 것인지 표시**이지 파일 내용이 아니다.
> 선행 — [11번 주제](../11-sectioning-and-landmarks/1-question.md).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `<h1>` 을 구획 안에 넣어 가며 일곱 번 쓰면 (예측)

```html
<!-- html09b-outline.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>section 중첩이 제목 레벨을 바꾸나</title>
</head>
<body>
<h1>맨 바깥 h1</h1>
<section>
  <h1>section 1겹 안의 h1</h1>
  <section>
    <h1>section 2겹 안의 h1</h1>
    <section>
      <h1>section 3겹 안의 h1</h1>
    </section>
  </section>
</section>
<article><h1>article 안의 h1</h1></article>
<nav><h1>nav 안의 h1</h1></nav>
<aside><h1>aside 안의 h1</h1></aside>
<h2>맨 바깥 h2</h2>
</body>
</html>
```

- 일곱 `<h1>` 의 접근성 트리 `level` 을 **하나씩** 예측하라.
- 맨 끝 `<h2>` 의 `level` 은?
- 랜드마크(`article`·`navigation`·`complementary`)는 트리에 생기는가?
- 「구획은 읽히는데 제목만 안 따라간다」가 맞는가?

### 2. 그 중첩의 글꼴 크기를 재면 (예측)

```html
<!-- html09b-outline-probe.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>중첩 h1 의 글꼴 크기</title>
<script src="html09b-probe.js"></script>
</head>
<body>
<h1 id="ㄱ">맨 바깥 h1</h1>
<section>
  <h1 id="ㄴ">section 1겹 안의 h1</h1>
  <section>
    <h1 id="ㄷ">section 2겹 안의 h1</h1>
    <section><h1 id="ㄹ">section 3겹 안의 h1</h1></section>
  </section>
</section>
<article><h1 id="ㅁ">article 안의 h1</h1></article>
<h2 id="ㅂ">맨 바깥 h2</h2>
<h3 id="ㅅ">맨 바깥 h3</h3>
<script>
window.__끝 = function () {
  for (const [id, 설명] of [["ㄱ","h1 (중첩 0겹)"],["ㄴ","h1 (section 1겹)"],["ㄷ","h1 (section 2겹)"],
                            ["ㄹ","h1 (section 3겹)"],["ㅁ","h1 (article 안)"],["ㅂ","h2 (중첩 0겹)"],["ㅅ","h3 (중첩 0겹)"]]) {
    const c = getComputedStyle(document.getElementById(id));
    P(설명.padEnd(20) + "font-size = " + c.fontSize.padEnd(8)
      + "margin = " + c.marginTop + " " + c.marginBottom);
  }
};
</script>
</body>
</html>
```

- 중첩 0겹·1겹·2겹·3겹 `<h1>` 의 `font-size` 를 각각 예측하라.
- `<article>` 안의 `<h1>` 은?
- `h2`·`h3` 의 크기는?
- 콘솔에 경고가 나는가? 몇 줄인가?

### 3. 제목을 건너뛰고 되돌아가면 (예측)

```html
<!-- html09b-skip.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>제목을 건너뛰면</title>
</head>
<body>
<h1>h1</h1>
<h3>h3 — h2 를 건너뛰었다</h3>
<h6>h6 — 또 건너뛰었다</h6>
<h2>h2 — 뒤로 돌아왔다</h2>
<div role="heading" aria-level="4">div 에 role=heading + aria-level=4</div>
<h1 aria-level="5">h1 에 aria-level=5 를 덮어썼다</h1>
<hgroup>
  <h2>hgroup 의 제목</h2>
  <p>hgroup 안의 부제</p>
</hgroup>
</body>
</html>
```

- 네 제목(`h1`·`h3`·`h6`·`h2`)의 `level` 을 예측하라.
- 파서나 콘솔이 막는가?
- `<div role="heading" aria-level="4">` 는 트리에 어떻게 들어가는가?
- **`<h1 aria-level="5">`** 의 `level` 은 몇인가? 그 답이 뜻하는 것은?

### 4. `<hgroup>` 을 두 가지로 쓰면 (예측)

```html
<!-- html09b-hgroup.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>hgroup 이 오늘 하는 일</title>
</head>
<body>
<hgroup>
  <h1>책 제목</h1>
  <p>부제 — 한 줄 설명</p>
</hgroup>
<hgroup>
  <h1>h1 과 h2 를 함께 넣은 hgroup</h1>
  <h2>이 h2 는 레벨이 바뀌나</h2>
</hgroup>
<h2>hgroup 밖의 h2</h2>
</body>
</html>
```

- `hgroup` 의 역할은 무엇인가?
- 그 안의 `<h1>`·`<p>` 는 어떻게 들어가는가?
- **`<h1>` + `<h2>` 를 넣은 판**에서 `<h2>` 의 레벨이 바뀌는가?
- 파서가 무엇을 고치는가?

### 5. `<hgroup>` 안팎의 글꼴 크기를 재면 (예측)

```html
<!-- html09b-hgroup-probe.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>hgroup 의 글꼴 크기</title>
<script src="html09b-probe.js"></script>
</head>
<body>
<hgroup><h1 id="ㄱ">hgroup 안의 h1</h1><p id="ㄴ">hgroup 안의 p</p></hgroup>
<h1 id="ㄷ">hgroup 밖의 h1</h1>
<p id="ㄹ">hgroup 밖의 p</p>
<script>
window.__끝 = function () {
  for (const [id, 설명] of [["ㄱ","hgroup 안 h1"],["ㄴ","hgroup 안 p"],["ㄷ","hgroup 밖 h1"],["ㄹ","hgroup 밖 p"]]) {
    const c = getComputedStyle(document.getElementById(id));
    P(설명.padEnd(16) + "font-size = " + c.fontSize.padEnd(6)
      + "margin = " + c.marginTop + " / " + c.marginBottom);
  }
  P("hgroup 의 display = " + getComputedStyle(document.querySelector("hgroup")).display);
};
</script>
</body>
</html>
```

- `hgroup` 안의 `<h1>` 과 밖의 `<h1>` 이 다른가?
- `hgroup` 안의 `<p>` 와 밖의 `<p>` 가 다른가?
- `hgroup` 자체의 `display` 는?
- 그렇다면 오늘 `hgroup` 이 주는 것은 무엇인가?

### 6. 왜 문서 개요 알고리즘이 폐기됐나 (왜)

- 그 규칙이 명세에 있던 동안 **무슨 일이 있었나** — 세 가지를 대라.
- 그것이 [03번 주제](../03-parser-and-error-recovery/1-question.md)의 어느 이야기와 같은 집안인가?
- 그래서 오늘 컴포넌트는 제목 레벨을 어떻게 정하는가?

### 7. 「레벨」을 무엇으로 재나 (경계)

- `<h1>` 이라는 **태그를 세는 것**이 왜 증명이 못 되는가?
- 글꼴 크기가 왜 증명이 못 되는가?
- 이 주제가 쓰는 창은 무엇이고, 왜 그것이라야 하는가?

### 8. 관찰과 보장을 가르기 (경계)

- 「중첩 `<h1>` 의 레벨이 1 이다」는 명세인가 관찰인가?
- 「중첩 `<h1>` 의 글꼴이 안 작아진다」는?
- 둘 중 **판이 오르면 다시 찍어야 하는 것**은 어느 쪽인가?
- 「한때는 작아졌다」를 이 문서가 **실측으로** 적을 수 있는가?

### 9. 이 판이 못 보는 것 (경계)

- 「목차가 평평하게 들린다」를 이 문서가 실측으로 쓸 수 있는가? 왜인가?
- 접근성 트리가 보여 주는 것과 안 보여 주는 것의 경계는?
- 「레벨 건너뛰기가 얼마나 나쁜가」는 어떤 종류의 물음인가?

### 10. 정본 경계 긋기 (연결)

- 구획 요소의 **암묵 역할**의 정본은 어느 주제인가?
- **UA 스타일시트가 캐스케이드의 어디에 있나**의 정본은?
- **`aria-level` 을 쓰지 말아야 하는 이유**의 정본은?
- HTML5 가 **무엇을 시도하고 무엇을 접었나**의 연혁은 어디인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
