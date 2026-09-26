# html/syntax/12 — 제목 레벨과 문서 개요: `h1`\~`h6` 가 실제로 계산되는 방식 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 [「Headings and outlines」](https://html.spec.whatwg.org/multipage/sections.html#headings-and-outlines)·[「The `hgroup` element」](https://html.spec.whatwg.org/multipage/sections.html#the-hgroup-element) 절과 [ARIA in HTML](https://www.w3.org/TR/html-aria/). 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에 실제로 띄워 읽은 것이다. 하네스는 [3-answer.md](3-answer.md) 의 `## 실행 검증` 절에 있다.\
> ★ **엔진은 Chrome 하나다.** 이 갈래는 **이식성을 주장하지 않는다.**
> **버전** — HTML 에는 언어 버전이 없다. 지원 상태는 **Baseline** 으로 읽는다. ★ 이 주제의 핵심은 「**한때 명세에 있었다가 빠진 것**」이라 버전보다 **연혁**이 중요하다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.
> ★★★ **이 주제의 본체는 창 ⑦(접근성 트리)이다** — [11번 주제](../11-sectioning-and-landmarks/2-summary.md)가 세운 창을 그대로 쓴다. 「제목 레벨」은 **화면 크기도 태그 이름도 아니고** 접근성 트리의 `level` 값이기 때문이다. 창 ①\~④ 의 정의는 [01번 주제](../01-document-skeleton/2-summary.md)에 있다.
> ★★★ **이 주제는 「널리 퍼진 오해」를 깨뜨리는 것이 전부다.** 「`<section>` 을 중첩하면 `<h1>` 이 알아서 `<h2>` 처럼 된다」는 **명세에 한때 있었고 어느 브라우저도 구현하지 않았으며 지금은 빠졌다.** 아래 (1)·(2) 가 **두 창으로** 그것을 잰다.

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
| **안 흔들린다** | 접근성 트리의 `level` 값과 중첩 순서 | 세 판을 돌려 **md5 가 같았다** |
| **안 흔들린다** | UA 스타일시트가 주는 `font-size`·`margin` | 판 안에서는 고정 |
| **안 흔들린다** | `hgroup` 의 역할과 그 안의 노드 구성 | 명세가 정한다 |
| **안 흔들린다** | 블록의 `(exit N)` | 파서는 실패하지 않는다([03번 주제](../03-parser-and-error-recovery/2-summary.md)) |

## 한눈에 — 쉽게 말하면

**★ `<h1>` 은 어디에 있든 언제나 레벨 1 이다. 레벨을 정하는 것은 숫자 하나뿐이다.**

책의 목차에 비유한다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 목차에 적힌 **장·절 번호의 깊이** | **제목 레벨** (`h1`\~`h6` 의 숫자) |
| 원고를 **폴더에 넣어 정리한 것** | **`<section>` 중첩** |
| 「폴더에 넣었으니 **번호가 알아서 깊어지겠지**」 | ★ **폐기된 문서 개요 알고리즘** — **그렇게 안 된다** |
| 목차 번호를 **손으로 고쳐 적는 것** | **오늘의 유일한 방법** |
| 제목 옆의 **작은 부제** | **`<hgroup>` 안의 `<p>`** |
| 글자를 크게 인쇄한 것 | **`font-size`** — 목차 번호와 **아무 상관 없다** |

- **`<section>` 을 세 겹 중첩해도 `<h1>` 은 레벨 1 이다** — (1) 이 접근성 트리로 잰 것이다.
- **글꼴 크기도 안 바뀐다.** ★ **이 판에서는 UA 스타일시트가 중첩 `<h1>` 을 안 줄인다** — (2) 가 그 실측이고, **한때는 줄였다.**
- **제목을 건너뛰어도 아무도 안 막는다.** 파서도 콘솔도 조용하다 — (3).

```text
  「알아서 깊어진다」는 이렇게 될 줄 알았다  |  실제로는 이렇다
                                          |
  <h1>맨 바깥</h1>          -> level 1      |  -> level 1
  <section>                                |
    <h1>1겹</h1>            -> level 2 ?    |  -> level 1   ★
    <section>                              |
      <h1>2겹</h1>          -> level 3 ?    |  -> level 1   ★
      <section>                            |
        <h1>3겹</h1>        -> level 4 ?    |  -> level 1   ★
      </section>                           |
    </section>                             |
  </section>                               |
  <h2>맨 바깥</h2>          -> level 2      |  -> level 2
                                          |
  왼쪽이 「문서 개요 알고리즘」이다.           |  오른쪽이 이 판의 실측이다.
  명세에 있었지만 어느 엔진도 구현하지 않았고 지금은 빠졌다.
```

실무에서 이게 터지는 자리는 **컴포넌트마다 `<h1>` 을 쓰고 「중첩되니까 알아서 되겠지」라고 믿는 것**이다.\
보조 기술에는 **레벨 1 짜리 제목이 다섯 개** 있는 페이지로 들린다 — 목차가 **평평해진다.**\
그리고 더 헷갈리는 자리는 **글꼴 크기를 레벨의 증거로 읽는 것**이다 — 둘은 **아무 상관이 없다.**

> **제목 레벨(heading level)** — 그 제목이 목차에서 **몇 번째 깊이**인가. `h1`\~`h6` 의 숫자가 곧 그것이다.

> **문서 개요 알고리즘(document outline algorithm)** — 구획 요소의 중첩으로 제목 레벨을 **자동 계산하려던** 규칙.\
> 예: `<section>` 안의 `<h1>` 을 레벨 2로 치는 것. **어느 브라우저도 구현하지 않았고 명세에서 빠졌다.**

## 이 주제가 답하려는 질문

1. **`<section>` 중첩이 제목 레벨을 정말로 안 바꾸나.** 무엇으로 재야 그것이 증명되나.
2. **글꼴 크기는 어떤가.** 「중첩하면 작아진다」가 이 판에서 맞나.
3. **제목을 건너뛰거나 `hgroup` 으로 묶으면 무엇이 달라지나.**

## 동작 방식

### (1) 창 ⑦ — `<section>` 을 세 겹 중첩해도 레벨 1 이다

**언제 쓰나** — 이 주제의 본체. **이 한 블록이 오해 하나를 통째로 깨뜨린다.**

`<h1>` 을 맨 바깥에 하나, `<section>` 1·2·3겹 안에 하나씩, `<article>`·`<nav>`·`<aside>` 안에 하나씩 두고, 끝에 `<h2>` 를 하나 놓았다.

```text
===== 소스: html09b-outline.html =====
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
===== ax html09b-outline.html =====
RootWebArea    이름='section 중첩이 제목 레벨을 바꾸나'
  heading        이름='맨 바깥 h1'              level=1
  heading        이름='section 1겹 안의 h1'     level=1
  heading        이름='section 2겹 안의 h1'     level=1
  heading        이름='section 3겹 안의 h1'     level=1
  article        이름=''
    heading        이름='article 안의 h1'        level=1
  navigation     이름=''
    heading        이름='nav 안의 h1'            level=1
  complementary  이름=''
    heading        이름='aside 안의 h1'          level=1
  heading        이름='맨 바깥 h2'              level=2
(exit 0)
```

```text
  레벨을 정하는 것은 숫자 하나뿐이다

  <h1>  -> level 1      태그 이름의 숫자가 곧 레벨이다
  <h2>  -> level 2
  <h3>  -> level 3

  바꾸지 못하는 것들
  ------------------
  <section> 중첩 0겹 / 1겹 / 2겹 / 3겹   -> 전부 level 1
  <article> / <nav> / <aside> 안         -> 전부 level 1
  font-size 를 CSS 로 줄임                -> level 1 그대로
```

- ★★★ **일곱 `<h1>` 이 전부 `level=1` 이다.** 중첩 깊이가 0겹이든 3겹이든 같다.
- **`<article>`·`<nav>`·`<aside>` 안에서도 같다** — 구획 콘텐츠 넷 모두 레벨을 안 바꾼다.
- **맨 끝의 `<h2>` 만 `level=2`** 다 — 레벨을 바꾼 것은 **태그 이름 하나**뿐이다.
- ★★ **랜드마크는 중첩을 따라 제대로 생겼다** — `article`·`navigation`·`complementary` 가 트리에 있다. 즉 **구획 구조는 읽히는데 제목 레벨만 안 따라간다.** 「그럼 구획이 아무 일도 안 하나」에 대한 답이 이것이다.

**「레벨」을 무엇으로 쟀나** — ★ `<h1>` 이라는 **태그 이름을 세는 것**은 증명이 아니다. 그것은 입력이다.\
접근성 트리의 `level` 은 **브라우저가 계산해서 보조 기술에 넘기는 값**이라, 「자동 계산이 있었다면 여기서 달라졌을 자리」다. 그래서 이 창으로 잰다.

### (2) 창 ② — 글꼴 크기도 안 바뀐다 (이 판에서는)

**언제 쓰나** — 「중첩하면 작아지던데?」라는 반문이 나오는 자리.

같은 중첩을 두고 **계산된 `font-size` 와 `margin`** 을 읽었다.

```text
===== 소스: html09b-outline-probe.html =====
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
===== dom http://127.0.0.1:18709/html09b-outline-probe.html | probe =====
h1 (중첩 0겹)          font-size = 32px    margin = 21.44px 21.44px
h1 (section 1겹)     font-size = 32px    margin = 21.44px 21.44px
h1 (section 2겹)     font-size = 32px    margin = 21.44px 21.44px
h1 (section 3겹)     font-size = 32px    margin = 21.44px 21.44px
h1 (article 안)      font-size = 32px    margin = 21.44px 21.44px
h2 (중첩 0겹)          font-size = 24px    margin = 19.92px 19.92px
h3 (중첩 0겹)          font-size = 18.72px margin = 18.72px 18.72px
(exit 0)
```

```text
  세 축을 섞지 마라 — 서로 독립이다

  태그 이름   h1 h2 h3 ...      명세가 레벨을 정한다
  글꼴 크기   32px 24px ...     UA 스타일시트가 정한다 (CSS 한 줄로 바뀐다)
  레벨       level=1 2 ...      접근성 트리에 나온다

  「글자가 작아졌으니 레벨이 내려갔다」 -> 틀렸다
  「<section> 안에 넣었으니 레벨이 내려갔다」 -> 틀렸다
  「<h2> 로 썼다」 -> 이것만 맞다
```

- ★★★ **중첩 0\~3겹의 `<h1>` 이 전부 `32px` 이다.** `<article>` 안의 것도 같다.
- **작아지는 것은 태그를 바꿨을 때뿐** — `h2` 가 `24px`, `h3` 이 `18.72px`.
- ★★★ **이것은 이 판의 관찰이다.** 한때 브라우저 기본 스타일시트에는 `:is(article, aside, nav, section) h1 { font-size: 1.5em; … }` 같은 규칙이 있었고, **Chrome 151 에는 없다.** 문서 개요 알고리즘이 명세에서 빠지면서 **그 흔적도 정리된 것**이다.
- ★★ **그러니 「중첩하면 글자가 작아진다」는 오래된 지식이다.** 그리고 **작아졌더라도 그것은 레벨이 아니었다** — CSS 한 줄로 되돌릴 수 있는 것은 레벨이 아니다.

**콘솔은 이 판에서 아무 말도 안 한다.**

```text
===== echo "콘솔 줄 수 = $(google-chrome --headless --disable-gpu --no-sandbox --enable-logging=stderr \
  --dump-dom http://127.0.0.1:18709/html09b-outline.html 2>&1 >/dev/null | grep -c ':CONSOLE:')" =====
콘솔 줄 수 = 0
(exit 0)
```

- ★ **침묵도 출력이다.** 「중첩 `<h1>` 은 이제 권하지 않는다」 같은 경고는 **한 줄도 없다.**

★ 브라우저 기본 스타일시트가 주는 값 자체는 **CSS 갈래가 정본**이다 — CSS 갈래 목록([`css/syntax/README.md`](../../../css/syntax/README.md))의 **01번**([캐스케이드](../../../css/syntax/01-cascade-and-priority/2-summary.md))이 UA 스타일시트의 자리를 설명한다. 여기는 **그 값이 레벨의 증거가 아니라는 것**까지다.

### (3) 창 ⑦ + 창 ① — 건너뛰기도 되돌아가기도 아무도 안 막는다

**언제 쓰나** — 「파서가 잡아 주겠지」라고 믿는 자리.

`h1` → `h3` → `h6` → `h2` 로 뛰어다니고, `role="heading"` 과 `aria-level` 도 함께 던졌다.

```text
===== 소스: html09b-skip.html =====
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
===== ax html09b-skip.html =====
RootWebArea    이름='제목을 건너뛰면'
  heading        이름='h1'                   level=1
  heading        이름='h3 — h2 를 건너뛰었다'      level=3
  heading        이름='h6 — 또 건너뛰었다'         level=6
  heading        이름='h2 — 뒤로 돌아왔다'         level=2
  heading        이름='div 에 role=heading + aria-level=4' level=4
  heading        이름='h1 에 aria-level=5 를 덮어썼다' level=5
  group          이름=''
    heading        이름='hgroup 의 제목'          level=2
    paragraph      이름=''
(exit 0)
```

```text
  건너뛰면 목차에 빈 층이 생긴다 (아무도 안 막는다)

  쓴 것            들리는 목차
  ------           -----------
  <h1>             1. h1
  <h3>               (2층 없음)
                   1.?.1 h3        <- 여기가 어디에 붙는지 알 수 없다
  <h6>                 (4·5층 없음)
                   1.?.?.?.?.1 h6
  <h2>             2. h2           <- 다시 2층으로 돌아왔다
```

- ★★★ **레벨이 쓴 그대로다** — 1 → 3 → 6 → 2. **건너뛰어도 되돌아가도 아무 일도 안 일어난다.**
- **파서도 콘솔도 안 막는다** — (2) 의 콘솔 블록과 같은 상태다.
- ★★ **그 사실 자체가 교재다** — 제목 구조는 **도구가 강제하지 않는다.** 지키는 것은 사람 몫이고, 그래서 틀리기 쉽다.
- **`<div role="heading" aria-level="4">` 가 `level=4` 짜리 제목이 됐다** — 마크업 없이 역할만으로도 제목이 된다.
- ★★★ **`<h1 aria-level="5">` 가 `level=5` 로 나왔다** — `aria-level` 이 **태그가 정한 레벨을 덮어쓴다.** ★ 그렇다고 이것을 쓰라는 말이 아니다. 「ARIA 없는 것이 나쁜 ARIA 보다 낫다」는 목록의 **42번 주제**가 정본이다. 여기서는 **덮어쓰기가 실제로 일어난다는 것**까지만 봤다.

### (4) 창 ⑦ + 창 ② — `hgroup` 이 오늘 하는 일

**언제 쓰나** — 제목과 부제를 함께 묶고 싶을 때.

`<hgroup>` 두 개를 던졌다 — 하나는 `<h1>` + `<p>`(오늘의 용법), 하나는 `<h1>` + `<h2>`(옛 용법).

```text
===== 소스: html09b-hgroup.html =====
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
===== ax html09b-hgroup.html =====
RootWebArea    이름='hgroup 이 오늘 하는 일'
  group          이름=''
    heading        이름='책 제목'                 level=1
    paragraph      이름=''
  group          이름=''
    heading        이름='h1 과 h2 를 함께 넣은 hgroup' level=1
    heading        이름='이 h2 는 레벨이 바뀌나'       level=2
  heading        이름='hgroup 밖의 h2'         level=2
(exit 0)
```

```text
  hgroup 이 한때 하려던 일과 오늘 하는 일

  한때 (개요 알고리즘 시절)        오늘
  -----------------------         ----
  <hgroup>                        <hgroup>              -> group
    <h1>제목</h1>                    <h1>제목</h1>        -> level 1 (그대로)
    <h2>부제</h2>  <- 접어서         <p>부제</p>          -> paragraph
  </hgroup>          제목 하나로    </hgroup>
                     쳐 주려 했다
                                  ★ 레벨은 한 글자도 안 바뀐다.
                                    부제는 <h2> 가 아니라 <p> 로 쓴다.
```

- ★★ **`hgroup` 은 역할 `group` 이 된다.** 랜드마크도 제목도 아니다.
- **그 안의 `<h1>` 은 여전히 `level=1`, `<p>` 는 여전히 `paragraph`** 다 — **아무것도 안 바뀐다.**
- ★★★ **`<h1>` + `<h2>` 를 넣은 판도 레벨이 1 과 2 그대로다.** 옛 `hgroup` 은 **여러 제목을 하나로 접어** 레벨을 계산해 주려던 것이었는데, **지금은 그 일을 안 한다.**

**트리와 글꼴 크기도 그대로다.**

```text
===== 소스: html09b-hgroup.html =====
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
===== dom http://127.0.0.1:18709/html09b-hgroup.html =====
<!DOCTYPE html>
<html lang="ko"><head>
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


</body></html>
(exit 0)
```

```text
===== 소스: html09b-hgroup-probe.html =====
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
===== dom http://127.0.0.1:18709/html09b-hgroup-probe.html | probe =====
hgroup 안 h1     font-size = 32px  margin = 21.44px / 21.44px
hgroup 안 p      font-size = 16px  margin = 16px / 16px
hgroup 밖 h1     font-size = 32px  margin = 21.44px / 21.44px
hgroup 밖 p      font-size = 16px  margin = 16px / 16px
hgroup 의 display = block
(exit 0)
```

- **파서가 아무것도 안 고쳤다** — 쓴 그대로다.
- **`hgroup` 안팎의 `<h1>`·`<p>` 가 글꼴 크기도 여백도 같다** — `hgroup` 자체는 `display: block` 하나뿐이다.
- ★ **그래서 오늘 `hgroup` 의 값은 「이 둘이 한 덩어리다」라는 의미 표시 하나**다. 현재 명세는 **제목 하나 + `<p>` 여럿**을 허용한다.

### demo — 중첩해도 글자가 안 작아진다

```html demo
<h1>h1 — 맨 바깥</h1>
<section>
  <h1>h1 — section 1겹</h1>
  <section><h1>h1 — section 2겹</h1></section>
</section>
<h2>h2 — 맨 바깥</h2>
<h3>h3 — 맨 바깥</h3>
```

> **보이는 것** — 위 세 줄의 `<h1>` 이 **전부 같은 크기**(32px)로 나온다. 중첩이 깊어져도 글자가 안 작아진다. 아래 두 줄만 작다 — `h2` 가 24px, `h3` 이 18.72px. 즉 **크기를 바꾼 것은 태그 이름뿐**이다.\
> **바꿔 볼 것** — 2겹 안의 `<h1>` → `<h3>`(그때 비로소 18.72px 로 작아진다 — 중첩이 아니라 **태그**가 크기를 정한다)

*(Chrome 151 headless 실측, 창 폭 780: `h1` 셋이 전부 `font-size: 32px` · `margin-top: 21.44px` · `h2` 가 24px · `h3` 이 18.72px)*

```text
===== 소스: html09b-demo12a.html (demo 블록 + 래퍼 + 측정 프로브) =====
<!DOCTYPE html>
<meta charset="utf-8">
<title>demo 12 검증</title>
<body>
<h1>h1 — 맨 바깥</h1>
<section>
  <h1>h1 — section 1겹</h1>
  <section><h1>h1 — section 2겹</h1></section>
</section>
<h2>h2 — 맨 바깥</h2>
<h3>h3 — 맨 바깥</h3>
<script>
const o = [];
o.push("창 폭 = " + window.innerWidth);
for (const e of document.querySelectorAll("h1, h2, h3")) {
  const s = getComputedStyle(e);
  o.push(e.textContent.padEnd(20) + "font-size = " + s.fontSize.padEnd(9)
    + "font-weight = " + s.fontWeight.padEnd(5)
    + "margin = " + s.marginTop);
}
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
===== dom html09b-demo12a.html | probe =====
창 폭 = 780
h1 — 맨 바깥           font-size = 32px     font-weight = 700  margin = 21.44px
h1 — section 1겹     font-size = 32px     font-weight = 700  margin = 21.44px
h1 — section 2겹     font-size = 32px     font-weight = 700  margin = 21.44px
h2 — 맨 바깥           font-size = 24px     font-weight = 700  margin = 19.92px
h3 — 맨 바깥           font-size = 18.72px  font-weight = 700  margin = 18.72px
(exit 0)
```

**「바꿔 볼 것」에 적은 단언도 따로 던져 확인했다.**

```text
===== 소스: html09b-demo12b.html (demo 블록 + 래퍼 + 측정 프로브) =====
<!DOCTYPE html>
<meta charset="utf-8">
<title>demo 12 「바꿔 볼 것」 검증</title>
<body>
<h1>h1 — 맨 바깥</h1>
<section>
  <h1>h1 — section 1겹</h1>
  <section><h3>h3 — section 2겹 (h1 을 h3 으로 바꾼 판)</h3></section>
</section>
<script>
const o = [];
o.push("창 폭 = " + window.innerWidth);
for (const e of document.querySelectorAll("h1, h3")) {
  o.push(("<" + e.nodeName.toLowerCase() + "> ").padEnd(6)
    + e.textContent.padEnd(34) + "font-size = " + getComputedStyle(e).fontSize);
}
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
===== dom html09b-demo12b.html | probe =====
창 폭 = 780
<h1>  h1 — 맨 바깥                         font-size = 32px
<h1>  h1 — section 1겹                   font-size = 32px
<h3>  h3 — section 2겹 (h1 을 h3 으로 바꾼 판) font-size = 18.72px
(exit 0)
```

## 문법 — 형태와 규칙

HTML 은 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 손으로 맞춘 목차

```html
<h1>사이트 제목</h1>
<section aria-label="소개">
  <h2>소개</h2>
  <section aria-label="연혁">
    <h3>연혁</h3>
  </section>
</section>
<hgroup>
  <h2>책 제목</h2>
  <p>부제 — 한 줄 설명</p>
</hgroup>
```

### 금지 사례 — 아무도 안 막는데 목차가 망가지는 자리

```html
<section><h1>중첩했으니 h2 처럼 되겠지</h1></section>
<h1>제목</h1><h3>h2 를 건너뛰었다</h3>
<hgroup><h1>제목</h1><h2>부제로 쓴 h2</h2></hgroup>
<h1 aria-level="5">태그와 레벨을 어긋나게 썼다</h1>
```

- 첫 줄은 **레벨 1 그대로**다((1)).
- 둘째 줄은 **레벨 3** 그대로고 아무도 안 막는다((3)).
- 셋째 줄의 `<h2>` 는 **부제가 아니라 레벨 2 제목**이다 — 오늘은 `<p>` 를 쓴다((4)).
- 넷째 줄은 **`aria-level` 이 이긴다**((3)) — 읽는 사람과 보조 기술이 **다른 목차**를 보게 된다.

### 어디서 헷갈리나

- **`<h1>` 을 문서에 하나만 써야 하는 것이 아니다.** 여럿이어도 유효하다 — 다만 **목차가 평평해진다.**
- **글꼴 크기는 레벨이 아니다.** CSS 한 줄로 바뀌는 것은 레벨이 아니다.
- **`<hgroup>` 은 레벨을 안 바꾼다.** 오늘은 **제목 + `<p>` 부제**를 묶는 표시다.
- **`<section>` 은 제목을 요구하지 않는다.** 그리고 제목은 **`<section>` 의 이름이 되지도 않는다**([11번 주제](../11-sectioning-and-landmarks/2-summary.md)의 (4)).
- **레벨을 건너뛰는 것은 무효가 아니라 「권장되지 않는 것」이다** — 도구가 안 막는 이유가 그것이다.

## 어디서 틀리나

### 1. 「`<section>` 중첩이 레벨을 낮춰 준다」고 믿는다

**안 낮춘다.** (1) 에서 세 겹 안의 `<h1>` 이 `level=1` 이었다.\
★ 이 주제에서 가장 널리 퍼진 오해다. **명세에 있었다가 빠졌고, 구현된 적이 없다.**

### 2. 글꼴 크기가 작아지는 것을 레벨의 증거로 읽는다

**이 판에서는 작아지지도 않는다.** (2) 에서 전부 `32px` 였다.\
★ 설령 작아지더라도 그것은 **UA 스타일시트**이지 레벨이 아니다.

```text
  컴포넌트마다 <h1> 을 쓰면 목차가 평평해진다

  기대한 목차               실제 목차
  -----------               ---------
  1. 페이지 제목            1. 페이지 제목
    1.1 카드 A              1. 카드 A
    1.2 카드 B              1. 카드 B
      1.2.1 카드 B 상세     1. 카드 B 상세
    1.3 카드 C              1. 카드 C

  오른쪽이 이 판의 실측이다. 컴포넌트는 자기 깊이를 모르므로
  레벨을 속성으로 받아야 한다.
```

### 3. 컴포넌트마다 `<h1>` 을 쓴다

**레벨 1 짜리 제목이 여러 개인 페이지가 된다.**\
★ 보조 기술의 목차가 **평평해진다.** 컴포넌트가 자기 깊이를 모르는 것이 이 문제의 뿌리다.

### 4. 제목을 건너뛰어도 아무 일 없으니 괜찮은 줄 안다

**아무도 안 막는 것이 맞다**((3)).\
★ 「에러가 안 난다」와 「괜찮다」는 다른 말이다. 목차를 듣는 사람에게는 **빈 층**이 생긴다.

### 5. `<hgroup>` 에 `<h2>` 를 넣어 부제로 쓴다

**부제가 안 된다.** (4) 에서 `level=2` 짜리 제목 그대로였다.\
★ 오늘은 **`<p>`** 를 쓴다.

```text
  aria-level 은 태그가 정한 레벨을 덮어쓴다

  <h1>                          -> level 1
  <h1 aria-level="5">           -> level 5   ★ 이긴다
  <div role="heading" aria-level="4">  -> level 4

  보이는 태그와 들리는 레벨이 어긋난다 — 되지만 권하지 않는다.
```

### 6. `aria-level` 로 레벨을 맞춘다

**먹기는 먹는다**((3)). 그런데 **태그와 어긋난다.**\
★ 「ARIA 없는 것이 나쁜 ARIA 보다 낫다」 — 목록의 **42번 주제**가 정본이다. 올바른 `h` 태그를 고르는 것이 먼저다.

## 구현 세부사항 대 언어 보장

★ **HTML 은 명세가 오류 복구까지 정한 언어**라 「구현 정의」 칸이 작다. 세 층으로 갈라 적는다.

| 층 | 무엇을 보장하나 | 이 주제에서 |
|---|---|---|
| **명세(HTML)** | 제목 레벨은 **`h1`\~`h6` 의 숫자**가 정한다 | (1) |
| **명세(HTML)** | **문서 개요 알고리즘은 없다** — 명세에서 빠졌다 | (1) 의 `level=1` 일곱 |
| **명세(HTML)** | 레벨 건너뛰기는 **파싱 오류가 아니다** | (3) |
| **명세(HTML)** | `hgroup` 은 **제목 하나 + `<p>` 여럿** | (4) |
| **명세(ARIA)** | `aria-level` 이 **암묵 레벨을 덮어쓴다** | (3) 의 `level=5` |
| **구현(Blink)** | `hgroup` 에 **역할 `group`** 을 주는 것 | (4) |
| **구현(Blink)** | ★ **중첩 `<h1>` 의 글꼴 크기를 안 줄이는 것** | (2) — **한때는 줄였다.** 판이 오르며 바뀐 자리다 |
| **구현(Blink)** | UA 스타일시트의 `32px`/`24px`/`18.72px` | (2) |
| **구현(Blink)** | 중첩 `<h1>` 에 **경고를 안 내는 것** | (2) 의 콘솔 0줄 |
| **이 판의 관찰** | 「글자가 안 작아진다」 | **Chrome 151 의 관찰**이다. 옛 판·다른 엔진은 다를 수 있다 |

**도구가 못 보는 것**

- ★★★ **스크린리더가 목차를 어떻게 읽어 주는지.** 이 판에 **NVDA·VoiceOver·Orca 가 없다.** 접근성 트리는 **스크린리더의 입력**이지 출력이 아니다 — 「목차가 평평하게 들린다」는 **명세·통념을 읽어 적은 것**이지 실측이 아니다.
- ★★ **「레벨 건너뛰기가 실제로 얼마나 나쁜가」.** 사용자 실험이 필요한 물음이라 **이 갈래의 도구로는 원리상 못 잰다.**
- **다른 엔진의 UA 스타일시트.** Firefox·WebKit 이 중첩 `<h1>` 을 여전히 줄이는지 **못 본다.** ★ **이 자리는 특히 엔진마다 다를 수 있다.**
- **옛 Chrome 판.** 「한때는 줄였다」는 **이 판에서 확인한 것이 아니다** — 지금 안 줄인다는 것만 실측했다.
- **검색엔진이 제목 구조를 어떻게 쓰나.** 마케팅 영역이고 이 목록 밖이다.

## 언제 쓰고 언제 안 쓰나

- **문서에 `<h1>` 은 하나, 그 아래로 레벨을 손으로 맞춘다** — 자동으로 되는 것은 없다.
- **건너뛰지 않는다** — `h1` → `h2` → `h3`. 도구가 안 막으니 사람이 지킨다.
- **컴포넌트가 제목을 갖는다면 레벨을 밖에서 주입한다** — 자기가 정할 수 없기 때문이다.
- **부제는 `<hgroup>` + `<p>`** — `<h2>` 를 부제로 쓰지 않는다.
- **`aria-level` 은 마지막 수단** — 올바른 `h` 태그가 먼저다.
- **글꼴 크기는 CSS 로 정한다** — 크기 때문에 태그를 고르지 않는다.
- **`<section>` 에는 이름을 붙인다** — 제목이 있어도 이름이 안 된다([11번 주제](../11-sectioning-and-landmarks/2-summary.md)).

## 핵심 문장

1. **제목 레벨을 정하는 것은 `h1`\~`h6` 의 숫자 하나뿐이다.**
2. **`<section>` 을 세 겹 중첩해도 `<h1>` 은 레벨 1 이다 — 접근성 트리가 그렇게 답한다.**
3. **문서 개요 알고리즘은 명세에 있었다가 빠졌고 구현된 적이 없다.**
4. **이 판에서는 중첩 `<h1>` 의 글꼴 크기도 안 줄어든다 — 한때는 줄었다.**
5. **레벨을 건너뛰어도 파서도 콘솔도 안 막는다. 그 사실이 교재다.**
6. **`hgroup` 은 역할 `group` 일 뿐 레벨을 안 바꾼다 — 부제는 `<p>` 다.**
7. **`aria-level` 은 태그가 정한 레벨을 덮어쓴다 — 되지만 권하지 않는다.**
8. **「구획 구조는 읽히는데 제목 레벨만 안 따라간다」 — 둘을 한 몸으로 생각하면 틀린다.**

## 관련 자료

- [11번 주제 — 구획 요소와 랜드마크](../11-sectioning-and-landmarks/2-summary.md) — **접근성 트리라는 창**과 구획 요소의 암묵 역할은 그쪽이 정본이다. 여기는 **그 구획이 제목 레벨을 안 바꾼다는 것**까지.
- [05번 주제 — 콘텐츠 카테고리와 콘텐츠 모델](../05-content-categories-and-models/2-summary.md) — **헤딩 콘텐츠**라는 분류가 정본이다.
- [01번 주제 — 문서의 뼈대](../01-document-skeleton/2-summary.md) — 「파서가 안 고쳐도 무효한 것이 있다」의 근거.
- CSS 갈래 목록([`css/syntax/README.md`](../../../css/syntax/README.md))의 **01번**([캐스케이드](../../../css/syntax/01-cascade-and-priority/2-summary.md)) — **UA 스타일시트가 캐스케이드의 어디에 있나**는 그쪽이 정본이다. 여기는 **그 값이 레벨의 증거가 아니라는 것**까지.
- 목록의 **42번 주제**(ARIA 를 언제 쓰지 말아야 하나) — **`aria-level` 을 쓰지 말아야 하는 이유**는 그쪽이 정본이다.
- 목록의 **43번 주제**(접근 가능한 이름 계산) — 제목이 **다른 요소의 이름이 되는 경우**(`aria-labelledby`)는 그쪽.
- 목록의 **13번 주제**(구절 시맨틱) — `<strong>`·`<b>` 처럼 **굵게 보이지만 제목이 아닌 것**.
- [`history/web/03-HTML-CSS-진화.md`](../../../../../../history/web/03-HTML-CSS-진화.md) — **HTML5 가 무엇을 시도하고 무엇을 접었나**의 연혁은 그쪽이다.

## 용어 풀이

- **제목 레벨(heading level)** — 그 제목이 목차에서 몇 번째 깊이인가. `h1`\~`h6` 의 숫자가 곧 그것이다.
- **문서 개요 알고리즘(document outline algorithm)** — 구획 중첩으로 레벨을 **자동 계산하려던** 규칙. **구현된 적 없이 명세에서 빠졌다.**
- **헤딩 콘텐츠(heading content)** — `h1`\~`h6` 와 `hgroup` 이 드는 콘텐츠 카테고리.
- **`<hgroup>`** — 제목 하나와 그에 딸린 `<p>` 들을 묶는 요소. **레벨을 안 바꾼다.**
- **`aria-level`** — 제목의 레벨을 **직접 지정**하는 ARIA 속성. 태그가 정한 레벨을 덮어쓴다.
- **`role="heading"`** — 제목이 아닌 요소를 제목으로 만드는 역할. `aria-level` 과 짝으로 쓴다.
- **UA 스타일시트(user agent stylesheet)** — 브라우저가 기본으로 적용하는 스타일. `h1` 이 32px 인 것이 여기서 온다.
- **접근성 트리의 `level`** — 브라우저가 계산해 보조 기술에 넘기는 제목 깊이. **이 주제가 재는 값이 이것이다.**

## 더 들어가면

- **왜 개요 알고리즘이 폐기됐나** — ① **어느 브라우저도 구현하지 않았다.** 명세에 10년 넘게 적혀 있었지만 실제로 레벨을 계산해 준 엔진이 없었다. ② **보조 기술도 그것을 안 썼다** — 사용자에게 도달한 적이 없다. ③ 그래서 「**명세에는 있는데 아무 데도 없는 규칙**」이 되었고, 명세가 **현실에 맞춰 그 절을 들어냈다.** ★ [03번 주제](../03-parser-and-error-recovery/2-summary.md)의 「XHTML 의 엄격함이 좌초한 이유」와 같은 집안이다 — **WHATWG 는 구현되지 않는 규칙을 명세에 두지 않는다.**
- **그래서 컴포넌트는 어떻게 하나** — 오늘의 답은 「**레벨을 속성으로 받아라**」다. 컴포넌트가 자기 깊이를 알 수 없으니 **바깥이 알려 주는 수밖에** 없다. 한때 제안됐던 `<h>` 요소(레벨 없는 제목)는 채택되지 않았다.
- **`<h1>` 을 여럿 쓰면 안 되나** — **유효하다.** 다만 목차가 평평해진다. 블로그 목록처럼 **`<article>` 마다 독립된 글**인 경우에는 각 글의 제목을 `<h2>` 로 두고 페이지 제목을 `<h1>` 로 두는 편이 목차를 살린다.
- **글꼴 크기 규칙이 언제 사라졌나** — 이 판(Chrome 151)에는 **없다**는 것만 실측했다. **언제 없어졌는지는 이 판에서 확인할 수 없다** — 옛 판이 없기 때문이다. ★ 「한때 있었다」는 **명세의 옛 UA 스타일시트 권고를 읽어 적은 것**이고, 이 문서의 실측은 **지금 없다**까지다.
