# html/syntax/11 — 구획 요소와 랜드마크: `main`/`header`/`footer`/`nav`/`aside`/`section`/`article`/`search` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★ 이 주제의 답은 **접근성 트리**에 있다. 화면에도 DOM 에도 한 글자도 안 나온다.
> ★ **「어디에 있느냐」를 늘 같이 물어라** — 같은 태그가 자리에 따라 역할이 갈린다.
> ★ **「관찰 수단이 있나」도 문항이다.** 없으면 「못 잰 것」으로 답하라 — 「안 돌려 봄」이 아니다.
> ★ 소스 펜스 첫 줄의 `<!-- 파일이름 -->` 은 **어느 파일을 던진 것인지 표시**이지 파일 내용이 아니다.
> 선행 — [05번 주제](../05-content-categories-and-models/1-question.md).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 암묵 역할을 DOM 프로브로 물으면 (예측)

```html
<!-- html09b-role-probe.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>암묵 역할이 DOM 에 보이나</title>
<script src="html09b-probe.js"></script>
</head>
<body>
<nav id="ㄱ">암묵 역할만 있는 nav</nav>
<nav id="ㄴ" role="navigation">role 을 손으로 쓴 nav</nav>
<div id="ㄷ" role="navigation">div 에 role 을 준 것</div>
<script>
window.__끝 = function () {
  for (const id of ["ㄱ", "ㄴ", "ㄷ"]) {
    const el = document.getElementById(id);
    P(("#" + id + " <" + el.nodeName.toLowerCase() + ">").padEnd(14)
      + "getAttribute('role') = " + JSON.stringify(el.getAttribute("role"))
      + "   el.role = " + JSON.stringify(el.role)
      + "   computedRole 같은 것 = " + ("computedRole" in el ? el.computedRole : "그런 프로퍼티 없음"));
  }
};
</script>
</body>
</html>
```

- 세 요소의 `getAttribute('role')` 을 예측하라.
- 세 요소의 `el.role` 을 예측하라. **`#ㄱ` 이 무엇을 돌려주는가?**
- `computedRole` 같은 프로퍼티가 있는가?
- 같은 파일을 **접근성 트리**로 덤프하면 셋이 어떻게 나오는가?

### 2. 여덟 요소를 늘어놓고 넷을 중첩하면 (예측)

```html
<!-- html09b-landmark.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>일곱 구획 요소와 search</title>
</head>
<body>
<header>최상위 header</header>
<nav>최상위 nav</nav>
<search>최상위 search</search>
<main>
  <article>
    <header>article 안의 header</header>
    <p>기사 본문</p>
    <aside>article 안의 aside</aside>
    <footer>article 안의 footer</footer>
  </article>
  <section>
    <header>section 안의 header</header>
    <footer>section 안의 footer</footer>
  </section>
  <aside>main 안의 aside</aside>
  <nav>main 안의 nav</nav>
</main>
<aside>최상위 aside</aside>
<footer>최상위 footer</footer>
</body>
</html>
```

- 최상위 여덟의 역할을 각각 대라.
- `<article>` 안의 `<header>`/`<footer>` 는 어떤 역할이 되는가?
- `<article>` 안의 `<aside>` 와 `<main>` 안의 `<aside>` 가 **갈리는가**? 갈린다면 왜인가?
- **트리에 아예 안 나오는 요소**가 있는가? 몇 개인가?

### 3. `<section>` 에 이름을 다섯 가지로 주면 (예측)

```html
<!-- html09b-section-name.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>section 에 이름이 없으면</title>
</head>
<body>
<section>이름이 아무것도 없는 section</section>
<section aria-label="aria-label 로 준 이름">있음</section>
<section aria-labelledby="ㄷ"><h2 id="ㄷ">aria-labelledby 가 가리킨 제목</h2></section>
<section><h2>제목만 있는 section</h2></section>
<section title="title 속성으로 준 이름">있음</section>
<article>이름이 없는 article</article>
<nav>이름이 없는 nav</nav>
<aside>이름이 없는 aside</aside>
</body>
</html>
```

- 다섯 `<section>` 중 `region` 이 되는 것은 몇 개인가?
- **제목(`<h2>`)만 있는 `<section>`** 은 `region` 이 되는가?
- `<article>`·`<nav>`·`<aside>` 는 이름이 없어도 역할이 붙는가?
- 이름이 없는 `<section>` 은 트리에서 어떻게 되는가?

### 4. 이 판이 아는 요소와 모르는 요소를 한 줄씩 던지면 (예측)

```html
<!-- html09b-known.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>이 판이 아는 요소와 모르는 요소</title>
<script src="html09b-probe.js"></script>
</head>
<body>
<main>m</main><header>h</header><footer>f</footer><nav>n</nav>
<aside>a</aside><section>s</section><article>ar</article><search>se</search>
<hgroup>hg</hgroup><marquee>mq</marquee><zzznope>zz</zzznope><my-thing>mt</my-thing>
<script>
window.__끝 = function () {
  for (const 이름 of ["main","header","footer","nav","aside","section","article","search",
                     "hgroup","marquee","zzznope","my-thing"]) {
    const el = document.querySelector(이름);
    P(("<" + 이름 + ">").padEnd(12) + el.constructor.name.padEnd(22)
      + "display=" + getComputedStyle(el).display);
  }
};
</script>
</body>
</html>
```

- 열두 개의 `constructor.name` 을 예측하라. **`HTMLUnknownElement` 는 몇 개인가?**
- `<search>` 와 `<my-thing>` 의 `constructor.name` 이 같은가? 같다면 왜인가?
- 그렇다면 **「이 판이 `<search>` 를 안다」를 무엇으로 증명하는가?**
- `<marquee>` 는 무엇인가?

### 5. `<main>` 을 둘 쓰면 (예측)

```html
<!-- html09b-two-main.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>main 이 둘이면</title>
</head>
<body>
<main>첫 번째 main</main>
<main>두 번째 main</main>
<main hidden>숨긴 세 번째 main</main>
</body>
</html>
```

- 파서가 둘째를 지우거나 고치는가?
- 콘솔에 경고가 나는가? 몇 줄인가?
- 접근성 트리에 `main` 이 몇 개 들어가는가?
- `hidden` 인 셋째는 어떻게 되는가?

### 6. 구획 요소를 여덟 줄 늘어놓으면 화면이 어떻게 되나 (예측)

- 여덟 요소의 `display` 계산값을 예측하라.
- `font-size`·`font-weight`·상자 폭이 서로 다른가?
- 그 결과가 이 주제에 대해 말하는 것은 무엇인가?

### 7. 왜 `<section>` 만 이름을 요구하나 (왜)

- 랜드마크가 올라가는 **목록**이 무엇인지 떠올려라. 이름 없는 `region` 이 열 개면 그 목록이 어떻게 되는가?
- `<nav>`·`<main>` 은 왜 이름 없이 통과하는가?
- 같은 논리로 **구획 안의 `<header>` 를 랜드마크에서 뺀 이유**를 설명하라.

### 8. 관찰 수단의 경계 (경계)

- 이 주제에서 **볼 수 있게 된 것**과 **여전히 못 보는 것**을 갈라라.
- 접근성 트리는 스크린리더의 **입력인가 출력인가**? 그 구분이 왜 중요한가?
- 「스크린리더가 이렇게 읽는다」를 이 문서가 못 쓰는 이유는?

### 9. 「트리에 있다」의 두 가지 (경계)

- 이 주제에서 **DOM 에는 있는데 접근성 트리에서 빠진** 노드 셋을 대라.
- 그 셋이 빠진 이유가 각각 무엇인가?
- 「DOM 에 있다」가 「보조 기술에 보인다」를 뜻하는가?

### 10. 정본 경계 긋기 (연결)

- 「구획 콘텐츠」라는 **분류**의 정본은 어느 주제인가?
- `<div role="main">` 이 **무엇을 못 얻나**의 정본은?
- `aria-label` 과 `title` 이 **겨룰 때 무엇이 이기나**의 정본은?
- 대시 있는 이름이 `HTMLUnknownElement` 가 **아닌** 이유의 정본은?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
