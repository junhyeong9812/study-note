# html/syntax/11 — 구획 요소와 랜드마크: `main`/`header`/`footer`/`nav`/`aside`/`section`/`article`/`search` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 [「Sections」](https://html.spec.whatwg.org/multipage/sections.html) 절과 [ARIA in HTML](https://www.w3.org/TR/html-aria/)(요소별 암묵 역할 표)·[WAI-ARIA 1.2](https://www.w3.org/TR/wai-aria-1.2/). 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에 실제로 띄워 읽은 것이다. 하네스는 [3-answer.md](3-answer.md) 의 `## 실행 검증` 절에 있다.\
> ★ **엔진은 Chrome 하나다.** 이 갈래는 **이식성을 주장하지 않는다.**
> **버전** — HTML 에는 언어 버전이 없다. 지원 상태는 **Baseline** 으로 읽는다. 구획 요소 일곱은 2010년대 초에, **`<search>` 는 2023년**에 들어왔다 — 이 목록에서 **가장 새 요소**다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.
> ★★★ **이 주제의 본체는 창 ⑦(접근성 트리)이다 — 이 편이 새로 세운다.** 암묵 역할은 **DOM 어디에도 안 나온다**(아래 (1) 이 그 실측이다). 그래서 이 배치는 **CDP(`Accessibility.getFullAXTree`)로 Chrome 의 접근성 트리를 직접 덤프**했다. 창 ①\~④ 의 정의는 [01번 주제](../01-document-skeleton/2-summary.md)에, 창 ⑤(요청 로그)는 [08번 주제](../08-script-loading/2-summary.md)에, 창 ⑥(`renderBlockingStatus`)은 [09번 주제](../09-stylesheets-and-resource-hints/2-summary.md)에 있다.
> ★★ **그래도 못 보는 것이 있다** — **스크린리더가 실제로 뭐라고 읽는지**는 이 판에 NVDA·VoiceOver 가 없어 **여전히 못 본다.** 접근성 트리는 **스크린리더의 입력**이지 **출력**이 아니다. 아래 「도구가 못 보는 것」이 그 선을 긋는다.

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
| **흔들린다** | CDP 가 쓰는 **포트 번호와 프로필 경로** | 배치마다 무작위로 고른다 — 출력에는 안 들어간다 |
| **안 흔들린다** | 접근성 트리의 **역할 이름과 중첩 순서** | 세 판을 돌려 **md5 가 같았다** |
| **안 흔들린다** | 랜드마크의 **접근 가능한 이름** | 〃 |
| **안 흔들린다** | `constructor.name`(`HTMLElement`/`HTMLUnknownElement`) | 명세가 정한다 |
| **안 흔들린다** | UA 스타일시트가 주는 `display` 값 | 〃 |
| **안 흔들린다** | 블록의 `(exit N)` | 파서는 실패하지 않는다([03번 주제](../03-parser-and-error-recovery/2-summary.md)) |

## 한눈에 — 쉽게 말하면

**★ 구획 요소가 주는 것은 모양이 아니라 「이 덩어리가 무엇인가」라는 이름표다.**

큰 서점 건물에 비유한다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 건물 입구의 **간판과 안내데스크** | **`<header>`**(최상위일 때) → 역할 `banner` |
| 층별 **안내 지도** | **`<nav>`** → 역할 `navigation` |
| 그 건물이 **팔려고 있는 것 전부** | **`<main>`** → 역할 `main` |
| 매대 옆 **추천 코너** | **`<aside>`** → 역할 `complementary` |
| **검색대** | **`<search>`** → 역할 `search` |
| 낱권으로 떼어 팔 수 있는 **책 한 권** | **`<article>`** → 역할 `article` |
| **이름표가 붙은 매대** | **`<section aria-label="…">`** → 역할 `region` |
| **이름표가 없는 매대** | **`<section>`** → **역할이 안 붙는다** |
| 건물 바깥의 **주소·영업시간 팻말** | **`<footer>`**(최상위일 때) → 역할 `contentinfo` |
| 책 한 권 **안의 표지와 판권면** | **구획 안의 `<header>`/`<footer>`** → 랜드마크가 **아니다** |

- **화면에는 아무 차이가 없다.** 여덟 요소 전부 `display: block` 하나뿐이다 — 아래 demo 가 그 실측이다.
- **이름표는 접근성 트리에만 나타난다.** DOM 프로브로는 **한 글자도 안 보인다**((1)).
- **`<section>` 만 이름을 요구한다.** 이름이 없으면 **랜드마크가 아예 안 된다**((4)).

```text
  같은 <header> 가 어디 있느냐로 역할이 갈린다

  <body>
    <header>        -> banner          ★ 랜드마크
    <main>
      <article>
        <header>    -> sectionheader   ★ 랜드마크가 아니다
        <aside>     -> (트리에서 사라진다)  ★ 구획 안의 이름 없는 aside
        <footer>    -> sectionfooter   ★ 랜드마크가 아니다
      </article>
      <aside>       -> complementary   ★ main 은 「구획」이 아니라서 살아남는다
      <nav>         -> navigation      ★ nav 는 어디 있든 랜드마크다
    </main>
    <footer>        -> contentinfo     ★ 랜드마크
  </body>
```

실무에서 이게 터지는 자리는 **`<section>` 을 `<div>` 대신 쓰는 것**이다.\
이름을 안 붙이면 **접근성 트리에 아무것도 안 남는다** — `<div>` 와 **완전히 같다.**\
그리고 더 헷갈리는 자리는 **`<main>` 을 둘 쓰는 것**이다 — 파서는 안 막고, 접근성 트리에도 **둘 다 그대로 들어간다.**

> **랜드마크(landmark)** — 보조 기술이 「페이지의 큰 덩어리」로 **건너뛸 수 있게** 표시된 영역.\
> 예: 스크린리더 사용자가 `banner` → `main` 으로 한 번에 점프한다.

> **암묵 역할(implicit role)** — `role` 속성을 안 써도 **요소 이름만으로** 붙는 ARIA 역할.\
> 예: `<nav>` 는 `role="navigation"` 을 안 써도 `navigation` 이다.

> **접근 가능한 이름(accessible name)** — 보조 기술이 그 영역을 부를 때 읽는 이름.\
> 예: `<nav aria-label="주 메뉴">` 는 「주 메뉴 탐색」처럼 읽힌다.

## 이 주제가 답하려는 질문

1. **암묵 역할을 이 판에서 관찰할 수단이 있나.** 있다면 무엇이고, 그것으로도 못 보는 것은 무엇인가.
2. **같은 요소가 어디 있느냐로 역할이 갈리는 자리는 어디인가.**
3. **이 판이 `<search>` 를 아나.** 모르는 요소는 어떻게 되나.

## 동작 방식

### (1) 창 ⑦ (새 창) — 암묵 역할은 DOM 어디에도 없다

**언제 쓰나** — 이 주제를 시작하기 전에 **관찰 수단부터** 정하는 자리.

`<nav>` 셋을 두었다 — 암묵 역할만 있는 것, `role="navigation"` 을 손으로 쓴 것, `<div>` 에 `role` 을 준 것.

```text
===== 소스: html09b-role-probe.html =====
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
===== dom http://127.0.0.1:18709/html09b-role-probe.html | probe =====
#ㄱ <nav>      getAttribute('role') = null   el.role = null   computedRole 같은 것 = 그런 프로퍼티 없음
#ㄴ <nav>      getAttribute('role') = "navigation"   el.role = "navigation"   computedRole 같은 것 = 그런 프로퍼티 없음
#ㄷ <div>      getAttribute('role') = "navigation"   el.role = "navigation"   computedRole 같은 것 = 그런 프로퍼티 없음
(exit 0)
```

```text
  같은 세 요소를 두 창이 다르게 답한다

                                 el.role        접근성 트리
  <nav>                          null           navigation
  <nav role="navigation">        "navigation"   navigation
  <div role="navigation">        "navigation"   navigation
       ^                          ^                ^
       |                          |                |
   내가 쓴 것              쓴 것을 되돌려 줌     계산한 결과

  창 ②는 「무엇을 썼나」를, 창 ⑦은 「무엇이 됐나」를 답한다.
```

- ★★★ **`el.role` 이 암묵 역할을 안 준다.** `#ㄱ` 은 `null` 이다 — ARIA 반영 프로퍼티는 **쓴 속성만** 되돌려 준다.
- **`computedRole` 같은 프로퍼티가 없다.** 이 판에 그런 표면이 없다.
- ★★ **즉 창 ②(DOM 프로브)로는 이 주제를 못 본다.** 새 창이 필요하다.

**같은 파일을 접근성 트리로 덤프한 것**이다.

```text
===== 소스: html09b-role-probe.html =====
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
===== ax html09b-role-probe.html =====
RootWebArea    이름='암묵 역할이 DOM 에 보이나'
  navigation     이름=''
  navigation     이름=''
  navigation     이름=''
(exit 0)
```

- ★★★ **셋이 전부 `navigation` 으로 같다.** 암묵 역할과 명시 역할이 **접근성 트리에서 구분되지 않는다.**
- ★ 이 창은 **CDP(`Accessibility.getFullAXTree`)** 로 연다. 헤드리스 Chrome 에 `--remote-debugging-port` 와 `--force-renderer-accessibility` 를 주고 트리를 통째로 받아 **부모-자식을 따라 들여쓰기**로 찍었다. **세 판을 돌려 md5 가 같았다** — 결정적이다.

### (2) 창 ⑦ — 일곱 구획 요소와 `<search>` 의 암묵 역할

**언제 쓰나** — 이 주제의 지도. **외울 것이 아니라 읽어 낼 것**이다.

최상위에 여덟을 늘어놓고, `<main>` 안에 `<article>`·`<section>`·`<aside>`·`<nav>` 를 중첩했다.

```text
===== 소스: html09b-landmark.html =====
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
===== ax html09b-landmark.html =====
RootWebArea    이름='일곱 구획 요소와 search'
  banner         이름=''
  navigation     이름=''
  search         이름=''
  main           이름=''
    article        이름=''
      sectionheader  이름=''
      paragraph      이름=''
      sectionfooter  이름=''
    sectionheader  이름=''
    sectionfooter  이름=''
    complementary  이름=''
    navigation     이름=''
  complementary  이름=''
  contentinfo    이름=''
(exit 0)
```

```text
  페이지 하나의 랜드마크 지도 (화면에는 아무 표시도 없다)

  ┌──────────────────────────────────────────┐
  │ <header>                     banner       │
  ├──────────────────────────────────────────┤
  │ <nav>                        navigation   │
  ├──────────────────────────────────────────┤
  │ <search>                     search       │
  ├──────────────────────────────────────────┤
  │ <main>                       main         │
  │   ┌────────────────────────────────────┐  │
  │   │ <article>            article        │  │
  │   │   <header>           sectionheader  │  │
  │   │   <aside>            (사라진다)      │  │
  │   │   <footer>           sectionfooter  │  │
  │   └────────────────────────────────────┘  │
  │   <aside>                    complementary│
  │   <nav>                      navigation   │
  ├──────────────────────────────────────────┤
  │ <footer>                     contentinfo  │
  └──────────────────────────────────────────┘
```

**읽는 법** — 들여쓰기가 트리의 깊이다. `이름=''` 은 **접근 가능한 이름이 없다**는 뜻이다.

| 요소 | 최상위에서의 역할 | 이름이 필요한가 |
|---|---|---|
| `<header>` | **`banner`** | 아니오 |
| `<nav>` | **`navigation`** | 아니오(여럿이면 권장) |
| `<search>` | **`search`** | 아니오 |
| `<main>` | **`main`** | 아니오 |
| `<article>` | **`article`** | 아니오 |
| `<aside>` | **`complementary`** | 최상위에서는 아니오 |
| `<section>` | **`region`** | ★ **예 — 없으면 역할 자체가 안 붙는다** |
| `<footer>` | **`contentinfo`** | 아니오 |

- ★ **`<article>` 의 `article` 은 엄밀히 랜드마크가 아니다** — 「문서 구조」 역할이다. 그래도 접근성 트리에는 그대로 나온다.
- ★★ **`<search>` 가 `search` 로 나왔다.** 이 판이 이 요소를 안다 — (5) 가 그 이유를 따로 판다.

### (3) 창 ⑦ — 같은 태그가 어디 있느냐로 갈린다

**언제 쓰나** — (2) 의 트리를 **다시 읽는** 자리. 이 주제의 값이 여기 몰린다.

(2) 의 같은 덤프에서 **중첩된 것들만** 뽑아 읽는다.

```text
  구획 콘텐츠 넷이 경계를 만든다

  구획 콘텐츠     <article> <aside> <nav> <section>
  그 밖           <main> <header> <footer> <body> <div> ...

  <main>                <- 구획 콘텐츠가 아니다
    <aside>  이름 없음   -> complementary   (살아남는다)

  <article>             <- 구획 콘텐츠다
    <aside>  이름 없음   -> (사라진다)
    <header>            -> sectionheader     (랜드마크가 아니다)
    <footer>            -> sectionfooter     (랜드마크가 아니다)
```

- ★★★ **`<article>` 안의 `<header>`/`<footer>` 가 `banner`/`contentinfo` 가 아니다.** `sectionheader`/`sectionfooter` 라는 **다른 역할**이 붙었다 — **랜드마크가 아니다.**
- **`<section>` 안의 `<header>`/`<footer>` 도 마찬가지**다.
- ★★★ **`<article>` 안의 `<aside>` 는 트리에서 아예 사라졌다.** 구획 콘텐츠 안에 있으면서 **이름이 없으면** `complementary` 가 안 붙는다.
- **`<main>` 안의 `<aside>` 는 `complementary` 로 살아남았다** — `<main>` 은 **구획 콘텐츠가 아니기** 때문이다.
- **`<nav>` 는 어디 있든 `navigation`** 이다.

> **구획 콘텐츠(sectioning content)** — `<article>`·`<aside>`·`<nav>`·`<section>` 넷.\
> 예: `<main>` 과 `<header>` 는 여기 **안 들어간다** — 그래서 위에서 `<aside>` 의 운명이 갈렸다.

★ **「`<main>` 은 구획 콘텐츠가 아니다」는 [05번 주제](../05-content-categories-and-models/2-summary.md)의 카테고리 표가 정본**이다. 여기는 **그 분류가 랜드마크를 바꾼다는 결과**까지다.

### (4) 창 ⑦ — `<section>` 은 이름이 없으면 랜드마크가 아니다

**언제 쓰나** — `<section>` 을 `<div>` 대신 쓰려는 자리.

이름 주는 방법을 넷 던지고, 이름이 없는 것과 견주었다.

```text
===== 소스: html09b-section-name.html =====
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
===== ax html09b-section-name.html =====
RootWebArea    이름='section 에 이름이 없으면'
  region         이름='aria-label 로 준 이름'
  region         이름='aria-labelledby 가 가리킨 제목'
    heading        이름='aria-labelledby 가 가리킨 제목' level=2
  heading        이름='제목만 있는 section'       level=2
  region         이름='title 속성으로 준 이름'
  article        이름=''
  navigation     이름=''
  complementary  이름=''
(exit 0)
```

```text
  <section> 에 이름을 주는 방법과 안 되는 방법

  <section aria-label="...">              -> region   O
  <section aria-labelledby="제목id">       -> region   O
  <section title="...">                   -> region   O
  <section><h2>제목만</h2></section>       -> (없음)   X   ★ 제목은 이름이 아니다
  <section>아무것도 없음</section>          -> (없음)   X

  같은 자리에 <article>·<nav>·<aside> 를 두면 이름 없이도 역할이 붙는다.
  <section> 만 다르다.
```

- ★★★ **이름이 없는 `<section>` 은 트리에 아예 안 나온다.** `<div>` 와 **완전히 같다.**
- **`aria-label`·`aria-labelledby`·`title` 셋 다 `region` 을 만든다.**
- ★★★ **제목(`<h2>`)만 있는 `<section>` 은 `region` 이 안 된다.** 제목은 **접근 가능한 이름이 아니다** — `heading` 만 홀로 나왔다. **가장 흔한 오해가 이것이다.**
- **`<article>`·`<nav>`·`<aside>` 는 이름이 없어도 역할이 붙었다** — `<section>` 만 다르다.

### (5) 창 ② — 이 판이 `<search>` 를 아나

**언제 쓰나** — 새 요소를 만났을 때 **되는지부터** 확인하는 자리.

여덟 구획 요소 + `<hgroup>`·`<marquee>`·모르는 이름·대시 있는 이름을 한 줄씩 던졌다.

```text
===== 소스: html09b-known.html =====
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
===== dom http://127.0.0.1:18709/html09b-known.html | probe =====
<main>      HTMLElement           display=block
<header>    HTMLElement           display=block
<footer>    HTMLElement           display=block
<nav>       HTMLElement           display=block
<aside>     HTMLElement           display=block
<section>   HTMLElement           display=block
<article>   HTMLElement           display=block
<search>    HTMLElement           display=block
<hgroup>    HTMLElement           display=block
<marquee>   HTMLMarqueeElement    display=inline-block
<zzznope>   HTMLUnknownElement    display=inline
<my-thing>  HTMLElement           display=inline
(exit 0)
```

```text
  「이 판이 이 요소를 아나」를 무엇으로 증명하나

                  constructor.name      display     결론
  <search>        HTMLElement           block       안다   <- UA 스타일시트에 규칙이 있다
  <my-thing>      HTMLElement           inline      모른다 (커스텀 요소 후보라 대우만 받는다)
  <zzznope>       HTMLUnknownElement    inline      모른다
  <marquee>       HTMLMarqueeElement    inline-block 안다 (폐기됐지만 고유 인터페이스가 있다)
                  ~~~~~~~~~~~~~~~~      ~~~~~~~
                  둘을 못 가른다         여기서 갈린다
```

- ★★★ **`constructor.name` 만으로는 못 가른다.** `<search>` 도 `<my-thing>` 도 **`HTMLElement`** 다. 대시가 있는 이름은 **커스텀 요소 후보**라 파서가 미리 대우해 주기 때문이다([10번 주제](../10-template-slot-shadow-dom/2-summary.md)의 (6)).
- ★★ **갈라 주는 것은 `display` 다.** `<search>` 는 **`block`** 이고 `<my-thing>`·`<zzznope>` 는 **`inline`** 이다 — **UA 스타일시트에 규칙이 있다는 것**이 곧 「이 판이 이 요소를 안다」는 증거다.
- **정말로 모르는 `<zzznope>` 만 `HTMLUnknownElement`** 다. ★ 대시가 없어야 이 클래스가 된다.
- **`<marquee>` 는 `HTMLMarqueeElement`** 다 — 폐기됐지만 **여전히 고유 인터페이스가 있다.**

### (6) 창 ① + 창 ⑦ — `<main>` 이 둘이면

**언제 쓰나** — 「하나여야 한다」가 **무엇에 의해 강제되나**를 묻는 자리.

```text
===== 소스: html09b-two-main.html =====
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
===== dom http://127.0.0.1:18709/html09b-two-main.html =====
<!DOCTYPE html>
<html lang="ko"><head>
<meta charset="utf-8">
<title>main 이 둘이면</title>
</head>
<body>
<main>첫 번째 main</main>
<main>두 번째 main</main>
<main hidden="">숨긴 세 번째 main</main>


</body></html>
(exit 0)
```

- ★★ **파서가 안 막는다.** 둘 다 그대로 트리에 있고 `hidden` 도 그대로 붙었다.

```text
===== echo "콘솔 줄 수 = $(google-chrome --headless --disable-gpu --no-sandbox --enable-logging=stderr \
  --dump-dom http://127.0.0.1:18709/html09b-two-main.html 2>&1 >/dev/null | grep -c ':CONSOLE:')" =====
콘솔 줄 수 = 0
(exit 0)
```

- ★★★ **콘솔에도 아무 말이 없다.** 「무효인데 아무도 안 알려 준다」의 대표 사례다.

```text
===== 소스: html09b-two-main.html =====
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
===== ax html09b-two-main.html =====
RootWebArea    이름='main 이 둘이면'
  main           이름=''
  main           이름=''
(exit 0)
```

```text
  무효인데 아무도 안 알려 준다

  파서        :  안 고친다          <main> 둘이 그대로
  콘솔        :  0줄               경고 없음
  접근성 트리  :  main 이 둘        보조 기술이 「본문」을 못 정한다
  명세        :  하나여야 한다      ★ 여기에만 규칙이 있다

  「에러가 안 난다」와 「유효하다」는 다른 말이다.
```

- ★★★ **접근성 트리에 `main` 이 둘 들어간다.** 보조 기술이 「본문」을 찾을 때 **둘 중 어느 쪽인지 알 수 없다.**
- **`hidden` 인 셋째는 트리에서 빠졌다** — 숨긴 것은 접근성 트리에도 안 들어간다.
- ★ **그래서 「`<main>` 은 하나」는 명세의 규칙이지 도구가 막는 것이 아니다.** [01번 주제](../01-document-skeleton/2-summary.md)가 말한 「파서가 안 고친 것 중에도 무효한 것이 있다」와 같은 집안이다.

### demo — 구획 요소는 화면에 아무것도 안 준다

```html demo
<header>header</header>
<nav>nav</nav>
<main>main</main>
<aside>aside</aside>
<section>section</section>
<article>article</article>
<search>search</search>
<footer>footer</footer>
<style>body > * { border: 1px dashed rgb(148, 163, 184); margin: 2px 0; }</style>
```

> **보이는 것** — 여덟 줄이 **전부 같은 모양**이다. 점선 테두리를 내가 그려 주기 전에는 구분이 아예 안 된다. 굵기도 크기도 여백도 같다 — 구획 요소가 화면에 주는 것은 **`display: block` 하나뿐**이다. 차이는 (2) 의 접근성 트리에만 있다.\
> **바꿔 볼 것** — `<search>` → `<searchh>`(이 판이 모르는 요소가 되어 `display: inline` 이므로 **줄 하나를 통째로 차지하지 않는다**)

*(Chrome 151 headless 실측, 창 폭 780: 여덟 요소 전부 `display: block` · `font-size: 16px` · `font-weight: 400` · 상자 폭 764. `<searchh>` 만 `display: inline` · 상자 폭 213)*

```text
===== 소스: html09b-demo11a.html (demo 블록 + 래퍼 + 측정 프로브) =====
<!DOCTYPE html>
<meta charset="utf-8">
<title>demo 11 검증</title>
<body>
<header>header</header>
<nav>nav</nav>
<main>main</main>
<aside>aside</aside>
<section>section</section>
<article>article</article>
<search>search</search>
<footer>footer</footer>
<style>body > * { border: 1px dashed rgb(148, 163, 184); margin: 2px 0; }</style>
<script>
const o = [];
o.push("창 폭 = " + window.innerWidth);
for (const e of document.querySelectorAll("body > *")) {
  if (e.nodeName === "STYLE" || e.nodeName === "SCRIPT") continue;
  const s = getComputedStyle(e), r = e.getBoundingClientRect();
  o.push(("<" + e.nodeName.toLowerCase() + ">").padEnd(10)
    + "display = " + s.display.padEnd(8)
    + "font-size = " + s.fontSize.padEnd(6)
    + "font-weight = " + s.fontWeight.padEnd(4)
    + "상자 폭 = " + Math.round(r.width));
}
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
===== dom html09b-demo11a.html | probe =====
창 폭 = 780
<header>  display = block   font-size = 16px  font-weight = 400 상자 폭 = 764
<nav>     display = block   font-size = 16px  font-weight = 400 상자 폭 = 764
<main>    display = block   font-size = 16px  font-weight = 400 상자 폭 = 764
<aside>   display = block   font-size = 16px  font-weight = 400 상자 폭 = 764
<section> display = block   font-size = 16px  font-weight = 400 상자 폭 = 764
<article> display = block   font-size = 16px  font-weight = 400 상자 폭 = 764
<search>  display = block   font-size = 16px  font-weight = 400 상자 폭 = 764
<footer>  display = block   font-size = 16px  font-weight = 400 상자 폭 = 764
(exit 0)
```

**「바꿔 볼 것」에 적은 단언도 따로 던져 확인했다.**

```text
===== 소스: html09b-demo11b.html (demo 블록 + 래퍼 + 측정 프로브) =====
<!DOCTYPE html>
<meta charset="utf-8">
<title>demo 11 「바꿔 볼 것」 검증</title>
<body>
<search>search — 이 판이 아는 요소</search>
<searchh>searchh — 이 판이 모르는 요소</searchh>
<script>
const o = [];
o.push("창 폭 = " + window.innerWidth);
for (const 이름 of ["search", "searchh"]) {
  const e = document.querySelector(이름), s = getComputedStyle(e);
  o.push(("<" + 이름 + ">").padEnd(11) + e.constructor.name.padEnd(20)
    + "display = " + s.display.padEnd(8)
    + "상자 폭 = " + Math.round(e.getBoundingClientRect().width));
}
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
===== dom html09b-demo11b.html | probe =====
창 폭 = 780
<search>   HTMLElement         display = block   상자 폭 = 764
<searchh>  HTMLUnknownElement  display = inline  상자 폭 = 213
(exit 0)
```

## 문법 — 형태와 규칙

HTML 은 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 뼈대 하나

```html
<body>
  <header>사이트 제목</header>
  <nav aria-label="주 메뉴">…</nav>
  <search><form role="search">…</form></search>
  <main>
    <article>
      <header><h2>글 제목</h2></header>
      <p>본문</p>
      <footer>작성자·날짜</footer>
    </article>
    <section aria-label="관련 글">…</section>
  </main>
  <aside aria-label="사이드바">…</aside>
  <footer>저작권</footer>
</body>
```

### 금지 사례 — 랜드마크가 안 생기거나 어긋나는 자리

```html
<section><h2>제목만 있는 구획</h2></section>
<main>첫 본문</main><main>둘째 본문</main>
<article><aside>이름 없는 곁가지</aside></article>
<div role="main">div 로 흉내 낸 본문</div>
```

- 첫 줄은 **`region` 이 안 된다**((4)) — 제목은 이름이 아니다.
- 둘째 줄은 **파서도 콘솔도 안 막는데** 접근성 트리에 `main` 이 둘 들어간다((6)).
- 셋째 줄의 `<aside>` 는 **트리에서 사라진다**((3)).
- 넷째 줄은 역할은 맞지만 **`<main>` 이 무료로 주는 것**(건너뛰기 대상·기본 스타일)을 못 얻는다 — 그 이야기는 목록의 **41번 주제**가 정본이다.

### 어디서 헷갈리나

- **`<section>` 은 `<div>` 의 시맨틱 버전이 아니다.** 이름이 없으면 **`<div>` 와 같다.**
- **`<header>`/`<footer>` 는 「위/아래」가 아니다.** **어느 구획의** 머리·바닥인가가 역할을 정한다.
- **`<article>` 은 「기사」가 아니다.** **떼어 내도 말이 되는 덩어리**면 댓글 하나도 `<article>` 이다.
- **`<aside>` 는 「오른쪽 사이드바」가 아니다.** 위치가 아니라 **본문과 곁가지 관계**다.
- **`<search>` 는 `<form>` 을 대신하지 않는다.** 검색 **영역**을 감싸는 것이고 폼은 그 안에 든다.

## 어디서 틀리나

### 1. `<section>` 을 `<div>` 대신 쓴다

**이름이 없으면 접근성 트리에 아무것도 안 남는다.** (4) 에서 통째로 사라졌다.\
★ 「의미가 있어 보이니까」 쓰는 것은 **아무 효과가 없다.**

```text
  DOM 트리와 접근성 트리는 다른 트리다

  DOM                                 접근성 트리
  ---                                 -----------
  <section>이름 없음</section>   ──X   (없음)
  <article><aside>...</aside>   ──X   (없음)
  <main hidden>...</main>       ──X   (없음)
  <nav>...</nav>                ──>   navigation
  <section aria-label="ㄱ">      ──>   region "ㄱ"

  「DOM 에 있다」가 「보조 기술에 보인다」를 뜻하지 않는다.
```

### 2. `<section>` 에 제목을 넣었으니 이름이 생겼다고 본다

**안 생긴다.** (4) 에서 제목만 있는 `<section>` 은 `region` 이 안 됐다.\
★ 이름은 `aria-label`·`aria-labelledby`·`title` 로 준다.

### 3. `<header>`/`<footer>` 가 언제나 랜드마크인 줄 안다

**구획 안에 있으면 아니다.** (3) 에서 `sectionheader`/`sectionfooter` 가 됐다.\
★ 「사이트 머리말」로 쓰려면 **`<body>` 바로 아래**에 둬야 한다.

### 4. `<article>` 안의 `<aside>` 가 곁가지로 읽힐 줄 안다

**이름이 없으면 트리에서 사라진다.** (3) 의 실측이다.\
★ 구획 안의 `<aside>` 에는 **이름을 붙여야** 한다.

### 5. `<main>` 을 둘 쓰고 아무도 안 막아서 괜찮은 줄 안다

**파서도 콘솔도 안 막는다.** 그런데 접근성 트리에 **둘 다 들어간다**((6)).\
★ 「에러가 안 난다」와 「유효하다」는 다른 말이다.

### 6. 암묵 역할을 `el.role` 로 확인하려 한다

**`null` 이다.** (1) 에서 확인했다.\
★ ARIA 반영 프로퍼티는 **쓴 속성만** 돌려준다. 계산된 역할은 **접근성 트리에만** 있다.

## 구현 세부사항 대 언어 보장

★ **HTML 은 명세가 오류 복구까지 정한 언어**라 「구현 정의」 칸이 작다. 세 층으로 갈라 적는다.

| 층 | 무엇을 보장하나 | 이 주제에서 |
|---|---|---|
| **명세(HTML/ARIA in HTML)** | 여덟 요소의 **암묵 역할** | (2) |
| **명세(HTML/ARIA in HTML)** | 구획 콘텐츠 안의 `<header>`/`<footer>` 는 **랜드마크가 아니다** | (3) |
| **명세(HTML/ARIA in HTML)** | `<section>` 은 **접근 가능한 이름이 있어야** `region` | (4) |
| **명세(HTML/ARIA in HTML)** | 구획 콘텐츠 안의 이름 없는 `<aside>` 는 `complementary` 가 아니다 | (3) |
| **명세(HTML)** | `<main>` 은 **문서에 하나** | (6) — 다만 **강제하는 도구가 없다** |
| **명세(HTML)** | 모르는 요소는 `HTMLUnknownElement` | (5) 의 `<zzznope>` |
| **명세(HTML)** | **대시 있는 이름**은 모르는 요소가 아니다 | (5) 의 `<my-thing>` |
| **구현(Blink)** | `sectionheader`/`sectionfooter` **라는 역할 이름** | (3) — ARIA 의 새 역할이고 판마다 다를 수 있다 |
| **구현(Blink)** | 이름 없는 `<section>`·`<aside>` 를 **트리에서 아예 빼는 것** | (3)·(4) — 「역할이 없다」를 구현이 그렇게 표현한다 |
| **구현(Blink)** | UA 스타일시트의 `display: block` | (5)·demo |
| **이 판의 관찰** | `<search>` 가 **동작한다**는 것 | 판이 낮으면 안 될 수 있다 |

**도구가 못 보는 것**

- ★★★ **스크린리더가 실제로 뭐라고 읽는지.** 이 판에 **NVDA·VoiceOver·Orca 가 없다.** 접근성 트리는 **스크린리더의 입력**이지 **출력**이 아니다 — 「이렇게 읽힌다」는 서술은 **이 문서에 없다.**
- ★★ **랜드마크 건너뛰기가 실제로 어떻게 도는지.** 사용자가 `D` 키로 랜드마크를 순회하는 동작은 **보조 기술의 몫**이라 못 본다.
- **다른 엔진의 접근성 트리.** Firefox·WebKit 이 같은 역할을 붙이는지 **못 본다.** 특히 `sectionheader`/`sectionfooter` 는 **최근 ARIA 의 표면**이라 판마다 다를 수 있다.
- **`--dump-dom` 으로는 이 주제가 통째로 안 보인다.** 창 ①에 역할은 한 글자도 안 나온다.
- **`aria-label` 의 다국어 처리·발음.** 잴 수단이 없다.

## 언제 쓰고 언제 안 쓰나

- **`<header>`/`<footer>` 는 사이트 머리·바닥에 하나씩, `<body>` 바로 아래** — 구획 안에 넣으면 랜드마크가 아니다.
- **`<main>` 은 딱 하나** — 도구가 안 막으니 **사람이 지켜야** 한다.
- **`<nav>` 가 여럿이면 `aria-label` 로 구분** — 「주 메뉴」·「보조 메뉴」.
- **`<section>` 은 이름을 줄 수 있을 때만** — 못 주겠으면 **`<div>` 를 쓴다.** 그쪽이 정직하다.
- **`<article>` 은 떼어 내도 말이 되는 덩어리에** — 글·댓글·상품 카드.
- **`<aside>` 를 구획 안에 넣을 때는 이름을 붙인다** — 안 그러면 사라진다.
- **`<search>` 는 검색 폼을 감쌀 때** — `role="search"` 를 손으로 쓸 이유가 없어졌다.

## 핵심 문장

1. **구획 요소가 주는 것은 모양이 아니라 접근성 트리의 이름표다 — 화면에는 `display: block` 하나뿐이다.**
2. **암묵 역할은 DOM 어디에도 안 나온다 — 접근성 트리를 따로 열어야 보인다.**
3. **같은 `<header>` 가 최상위면 `banner`, 구획 안이면 `sectionheader` 다.**
4. **구획 안의 이름 없는 `<aside>` 는 접근성 트리에서 아예 사라진다.**
5. **`<section>` 은 이름이 없으면 `region` 이 안 된다 — 제목은 이름이 아니다.**
6. **`<main>` 이 둘이어도 파서도 콘솔도 안 막고 접근성 트리에 둘 다 들어간다.**
7. **이 판은 `<search>` 를 안다 — 증거는 `constructor.name` 이 아니라 `display: block` 이다.**
8. **스크린리더가 뭐라고 읽는지는 이 판에서 여전히 못 본다.**

## 관련 자료

- [05번 주제 — 콘텐츠 카테고리와 콘텐츠 모델](../05-content-categories-and-models/2-summary.md) — **구획 콘텐츠라는 분류**가 정본이다. 여기는 **그 분류가 랜드마크를 바꾸는 결과**까지.
- [01번 주제 — 문서의 뼈대](../01-document-skeleton/2-summary.md) — 「파서가 안 고쳐도 무효한 것이 있다」의 근거((6) 과 같은 집안).
- [10번 주제 — `template`·`slot`·선언적 Shadow DOM](../10-template-slot-shadow-dom/2-summary.md) — **대시 있는 이름이 `HTMLUnknownElement` 가 아닌 이유**는 그쪽 (6) 이다.
- [12번 주제 — 제목 레벨과 문서 개요](../12-heading-levels-and-outline/2-summary.md) — **같은 접근성 트리 창**을 쓴다. 「구획이 제목 레벨을 안 바꾼다」가 그쪽의 본체다.
- 목록의 **41번 주제**(네이티브 시맨틱이 주는 것) — `<div role="main">` 이 **무엇을 못 얻나**는 그쪽이 정본이다.
- 목록의 **42번 주제**(ARIA 를 언제 쓰지 말아야 하나) — `role` 로 암묵 역할을 **덮어쓸 때** 생기는 일은 그쪽.
- 목록의 **43번 주제**(접근 가능한 이름 계산) — **`aria-label` 과 `title` 이 겨룰 때 무엇이 이기나**는 그쪽이 정본이다. 여기서는 **이름이 있나 없나**만 봤다.
- 목록의 **19번 주제**(`figure`·`address`·`hr`) — 구획이 아닌 나머지 구조 요소.

## 용어 풀이

- **구획 요소(sectioning element)** — 문서를 큰 덩어리로 나누는 요소들. 이 주제의 여덟이다.
- **구획 콘텐츠(sectioning content)** — `<article>`·`<aside>`·`<nav>`·`<section>` **넷**. `<main>`·`<header>`·`<footer>` 는 **아니다.**
- **랜드마크(landmark)** — 보조 기술이 건너뛸 수 있게 표시된 큰 영역. `banner`·`navigation`·`main`·`complementary`·`contentinfo`·`region`·`search`.
- **암묵 역할(implicit role)** — `role` 속성 없이 요소 이름만으로 붙는 ARIA 역할.
- **접근 가능한 이름(accessible name)** — 보조 기술이 그 영역을 부를 때 읽는 이름. `aria-label`·`aria-labelledby`·`title` 로 준다.
- **접근성 트리(accessibility tree)** — 브라우저가 보조 기술에게 넘기는 트리. **DOM 과 다르다** — 이름 없는 `<section>` 처럼 **빠지는 노드**가 있다.
- **`sectionheader` / `sectionfooter`** — 구획 콘텐츠 안의 `<header>`/`<footer>` 에 붙는 역할. **랜드마크가 아니다.**
- **`HTMLUnknownElement`** — 파서가 모르는 요소의 클래스. **대시가 있는 이름은 여기 안 들어간다.**
- **CDP(Chrome DevTools Protocol)** — 브라우저에 원격으로 붙어 내부 상태를 묻는 프로토콜. 이 배치가 **접근성 트리를 여는 열쇠**로 썼다.

## 더 들어가면

- **왜 `<section>` 만 이름을 요구하나** — 랜드마크는 **건너뛰기 목록**에 올라간다. 이름 없는 `region` 이 열 개 있으면 그 목록이 **「구획, 구획, 구획…」** 이 되어 쓸모가 없어진다. `<nav>`·`<main>` 처럼 **역할 이름만으로도 구분되는** 것은 이름 없이 통과시키고, **성격이 안 정해진 `<section>` 만** 이름을 요구한다.
- **왜 구획 안의 `<header>` 를 랜드마크에서 뺐나** — 같은 이유다. 글 열 개짜리 목록 페이지에서 `<article>` 마다 `<header>` 가 있으면 **`banner` 가 열 개**가 된다. 「이 페이지의 머리말」이라는 뜻이 사라진다.
- **`<search>` 가 왜 늦게 왔나** — `role="search"` 로 이미 되던 일이라 **요소가 필요한가**가 오래 논쟁이었다. 결국 「ARIA 없이 되게 하라」는 원칙(목록의 **42번 주제**)이 이겼다.
- **접근성 트리가 DOM 과 갈리는 폭** — 이 주제에서만 **이름 없는 `<section>`·구획 안의 `<aside>`·`hidden` 인 `<main>`** 셋이 트리에서 빠졌다. ★ **「DOM 에 있다」가 「보조 기술에 보인다」를 뜻하지 않는다.**
