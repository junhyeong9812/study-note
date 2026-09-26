# html/syntax/11 — 구획 요소와 랜드마크: `main`/`header`/`footer`/`nav`/`aside`/`section`/`article`/`search` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 돌려** 읽은 것이다. 하네스는 맨 아래 `## 실행 검증` 절에 있다.\
> 규칙은 [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 와 [ARIA in HTML](https://www.w3.org/TR/html-aria/) 로 접지했다.\
> ★ **엔진은 Chrome 하나다** — 이 갈래는 이식성을 주장하지 않는다.
> ★★★ **이 주제는 접근성 트리를 직접 덤프한다.** CDP(`Accessibility.getFullAXTree`)로 Chrome 이 보조 기술에 넘기는 트리를 그대로 받았다 — **세 판을 돌려 md5 가 같았다.**
> ★★ **그래도 스크린리더가 뭐라고 읽는지는 못 본다.** 접근성 트리는 **입력**이지 출력이 아니다(A8).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `el.role` 은 암묵 역할을 안 준다 — 창 ②로는 이 주제를 못 본다

**출력** — DOM 프로브(창 ②)

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

**같은 파일의 접근성 트리(창 ⑦)**

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

**왜 그런가**

- **`getAttribute('role')`** — `#ㄱ` 만 `null`, 나머지 둘은 `"navigation"`.
- ★★★ **`el.role` 도 `#ㄱ` 은 `null` 이다.** ARIA 반영 프로퍼티는 **쓴 속성만** 되돌려 준다 — 계산된 역할이 아니다.
- **`computedRole` 같은 프로퍼티는 없다.**
- ★★★ **접근성 트리에서는 셋이 전부 `navigation` 으로 같다.** 암묵 역할과 명시 역할이 **거기서는 구분되지 않는다.**
- ★ **그래서 이 주제는 새 창이 필요했다.** 창 ②로는 한 글자도 안 보인다.

### 2. 여덟이 각각 랜드마크가 되고, 중첩되면 셋이 갈린다

**출력**

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

**왜 그런가**

| 최상위 요소 | 역할 |
|---|---|
| `<header>` | **`banner`** |
| `<nav>` | **`navigation`** |
| `<search>` | **`search`** |
| `<main>` | **`main`** |
| `<aside>` | **`complementary`** |
| `<footer>` | **`contentinfo`** |

- ★★★ **`<article>` 안의 `<header>`/`<footer>` 는 `sectionheader`/`sectionfooter`** 다 — **랜드마크가 아니다.** `<section>` 안의 것도 같다.
- ★★★ **`<article>` 안의 `<aside>` 는 트리에 아예 안 나온다.** `<main>` 안의 `<aside>` 는 **`complementary` 로 살아남았다.**
- **갈리는 이유** — `<article>` 은 **구획 콘텐츠**이고 `<main>` 은 **아니기** 때문이다. 이름 없는 `<aside>` 는 **구획 콘텐츠 안에서만** 역할을 잃는다. 그 분류는 [05번 주제](../05-content-categories-and-models/2-summary.md)가 정본이다.
- **트리에 안 나오는 것** — `<article>` 안의 `<aside>` **1개**. (그리고 `<main>` 안의 `<section>` 은 이름이 없어 `region` 이 안 됐고, 그 안의 `sectionheader`/`sectionfooter` 만 남았다.)
- **`<nav>` 는 어디 있든 `navigation`** 이다.

### 3. 이름을 주는 방법 셋은 다 되고, 제목은 이름이 아니다

**출력**

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

**왜 그런가**

- **`region` 이 된 것은 셋** — `aria-label` · `aria-labelledby` · `title`.
- ★★★ **제목만 있는 `<section>` 은 `region` 이 안 된다.** `heading` 만 홀로 나왔다. **제목은 접근 가능한 이름이 아니다** — 가장 흔한 오해가 이것이다.
- **`<article>`·`<nav>`·`<aside>` 는 이름 없이도 역할이 붙었다.** 최상위이므로 `<aside>` 도 살아남았다.
- ★★ **이름 없는 `<section>` 은 트리에 아예 안 나온다.** `<div>` 와 **완전히 같다.**

### 4. `HTMLUnknownElement` 는 하나뿐 — 증거는 `display` 다

**출력**

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

**왜 그런가**

- ★★★ **`HTMLUnknownElement` 는 `<zzznope>` 하나뿐**이다.
- **`<search>` 와 `<my-thing>` 의 `constructor.name` 이 둘 다 `HTMLElement` 로 같다.** 대시가 있는 이름은 **나중에 정의될 수 있는 커스텀 요소 후보**라 파서가 미리 대우해 주기 때문이다([10번 주제](../10-template-slot-shadow-dom/2-summary.md)의 (6)).
- ★★★ **그래서 `constructor.name` 으로는 못 증명한다.** 갈라 주는 것은 **`display` 다** — `<search>` 는 `block`, `<my-thing>`·`<zzznope>` 는 `inline`. **UA 스타일시트에 규칙이 있다는 것**이 「이 판이 이 요소를 안다」는 증거다.
- **`<marquee>` 는 `HTMLMarqueeElement`** 다 — 폐기됐지만 **고유 인터페이스가 남아 있다.** `display` 도 `inline-block` 으로 특별하다.

### 5. 아무도 안 막는다 — 그리고 접근성 트리에 둘 다 들어간다

**출력** — 트리

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

**콘솔**

```text
===== echo "콘솔 줄 수 = $(google-chrome --headless --disable-gpu --no-sandbox --enable-logging=stderr \
  --dump-dom http://127.0.0.1:18709/html09b-two-main.html 2>&1 >/dev/null | grep -c ':CONSOLE:')" =====
콘솔 줄 수 = 0
(exit 0)
```

**접근성 트리**

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

**왜 그런가**

- **파서가 안 고친다.** 둘 다 그대로 있고 `hidden` 도 그대로 붙었다.
- ★★★ **콘솔 줄 수가 0 이다.** 「무효인데 아무도 안 알려 준다」의 대표 사례다. ★ **침묵도 출력이므로 명령과 종료 코드까지 담은 블록으로 남겼다.**
- ★★★ **접근성 트리에 `main` 이 둘** 들어간다. 보조 기술이 「본문」을 찾을 때 **어느 쪽인지 알 수 없다.**
- **`hidden` 인 셋째는 트리에서 빠졌다** — 숨긴 것은 접근성 트리에도 안 들어간다.
- ★ **「`<main>` 은 하나」는 명세의 규칙이지 도구가 막는 것이 아니다.** [01번 주제](../01-document-skeleton/2-summary.md)의 「파서가 안 고친 것 중에도 무효한 것이 있다」와 같은 집안이다.

### 6. 여덟이 전부 같다 — 화면에 주는 것은 `display: block` 하나뿐이다

**출력**

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

**왜 그런가**

- **여덟 전부 `display: block` · `font-size: 16px` · `font-weight: 400` · 상자 폭 764** 다.
- ★★★ **구획 요소가 화면에 주는 것은 없다.** 점선 테두리를 내가 그려 주기 전에는 **구분이 아예 안 된다.**
- **그래서 이 주제는 화면으로 배울 수 없다.** 차이는 A2 의 접근성 트리에만 있다.

**「바꿔 볼 것」도 따로 던졌다.**

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

- `<searchh>` 는 `HTMLUnknownElement` 이고 `display: inline` 이라 **줄을 통째로 차지하지 않는다**(상자 폭 213).

### 7. 건너뛰기 목록이 쓸모를 잃기 때문이다

**왜 그런가**

- **랜드마크는 건너뛰기 목록에 올라간다.** 보조 기술 사용자는 그 목록으로 페이지를 **점프**한다.
- ★★★ **이름 없는 `region` 이 열 개면 목록이 「구획, 구획, 구획…」이 되어 쓸모가 없다.** 그래서 **성격이 안 정해진 `<section>` 만** 이름을 요구한다.
- **`<nav>`·`<main>` 은 역할 이름만으로도 구분된다** — 「탐색」·「본문」이 이미 뜻을 갖는다. 그래서 이름 없이 통과한다.
- ★★ **같은 논리가 구획 안의 `<header>` 에도 적용된다** — 글 열 개짜리 목록에서 `<article>` 마다 `<header>` 가 있으면 **`banner` 가 열 개**가 된다. 「이 페이지의 머리말」이라는 뜻이 사라지므로 **다른 역할**(`sectionheader`)로 뺐다.

### 8. 볼 수 있게 된 것과 여전히 못 보는 것

| | 무엇 | 어떻게 |
|---|---|---|
| **볼 수 있게 됐다** | 암묵 역할 · 접근 가능한 이름 · 트리에서 빠지는 노드 | **CDP 접근성 트리 덤프**(창 ⑦) |
| **여전히 못 본다** | **스크린리더가 뭐라고 읽는지** | NVDA·VoiceOver·Orca 가 없다 |
| **여전히 못 본다** | 랜드마크 **건너뛰기가 실제로 도는 모습** | 보조 기술의 몫이다 |
| **여전히 못 본다** | **다른 엔진의** 접근성 트리 | Chrome 하나뿐이다 |

**왜 그런가**

- ★★★ **접근성 트리는 스크린리더의 입력이지 출력이 아니다.** 브라우저가 **거기까지** 만들어 주고, **그것을 어떻게 읽을지는 보조 기술이 정한다.**
- **그 구분이 중요한 이유** — 같은 트리를 받고도 NVDA 와 VoiceOver 가 **다르게 읽을 수 있다.** 그래서 이 문서는 **「트리에 이렇게 들어간다」까지만** 적고 **「이렇게 읽힌다」는 한 줄도 안 쓴다.**
- ★ **이것이 「못 잰 것」이다** — 「안 돌려 봤다」가 아니라 **읽어 줄 프로그램이 이 판에 없다.**

### 9. DOM 에 있는데 접근성 트리에서 빠진 셋

| 무엇이 | 왜 빠지나 |
|---|---|
| **이름 없는 `<section>`** | 접근 가능한 이름이 없으면 `region` 이 **안 된다**(A3) |
| **구획 콘텐츠 안의 이름 없는 `<aside>`** | 구획 안에서는 이름이 있어야 `complementary` 가 된다(A2) |
| **`hidden` 인 `<main>`** | 숨긴 것은 접근성 트리에 **안 들어간다**(A5) |

**왜 그런가**

- ★★★ **「DOM 에 있다」는 「보조 기술에 보인다」를 뜻하지 않는다.** 두 트리는 **다른 트리**다.
- ★ 앞의 둘은 **「역할이 없다」를 Blink 가 「노드를 안 만든다」로 표현한 것**이다 — 명세가 정하는 것은 「역할이 안 붙는다」까지이고, **트리에서 통째로 빼는 것은 구현의 표현**이다.
- 셋째는 다르다 — **숨긴 것은 접근성에서도 뺀다**가 명세 쪽 규칙이다.

### 10. 정본 경계

| 무엇이 | 어디가 정본인가 | 여기는 어디까지 |
|---|---|---|
| **구획 콘텐츠**라는 분류 | [05번 주제](../05-content-categories-and-models/2-summary.md) | **그 분류가 랜드마크를 바꾸는 결과**까지 |
| `<div role="main">` 이 **못 얻는 것** | 목록의 **41번 주제**(네이티브 시맨틱이 주는 것) | **암묵 역할이 붙는다**는 사실까지 |
| `aria-label`·`title`·내용이 **겨룰 때** | 목록의 **43번 주제**(접근 가능한 이름 계산) | **이름이 있나 없나**까지 |
| `role` 로 암묵 역할을 **덮어쓸 때** | 목록의 **42번 주제**(ARIA 를 언제 쓰지 말아야 하나) | — |
| 대시 있는 이름이 **모르는 요소가 아닌** 이유 | [10번 주제](../10-template-slot-shadow-dom/2-summary.md)의 (6) | **그래서 `display` 로 갈라야 한다**는 결과까지 |
| `getComputedStyle` 이라는 API | web-api 갈래 목록([`web-api/README.md`](../../../../web-api/README.md))의 **08번** | **재는 도구**로만 썼다 |

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · 기본 창 폭 **780**. **엔진은 이것 하나다.**\
★★ **보조 기술 없음.** NVDA·VoiceOver·Orca 가 설치돼 있지 않다.

**하네스** — 09\~12 네 주제가 공유한다. 이 주제가 쓰는 것은 `dom`·`probe`·**`ax`** 다.

```bash
# html09b-harness.sh
dom()   { google-chrome --headless --disable-gpu --no-sandbox --dump-dom "$1" 2>/dev/null; }
probe() { sed -n '/^###P###$/,/^###E###$/p' | sed '1d;$d' \
          | sed 's/&lt;/</g; s/&gt;/>/g; s/&amp;/\&/g'; }
nojs()  { sed '/^<script>$/,$d'; }
ax()    { python3 html09b-ax.py "$1"; }
serve() { python3 html09b-server.py >>"$1" 2>&1 & echo $!; }
```

**접근성 트리 덤프기** — ★★★ **이 배치가 새로 세운 창이다.** 헤드리스 Chrome 에 `--remote-debugging-port` 와 `--force-renderer-accessibility` 를 주고 CDP 로 붙어 `Accessibility.getFullAXTree` 를 받는다. **평탄한 노드 목록을 `childIds` 로 따라가며 들여쓰기**로 찍어 **순서를 결정적으로** 만들었다(그냥 받은 순서는 판마다 달라질 수 있다).

```python
# html09b-ax.py
#!/usr/bin/env python3
"""CDP 로 접근성 트리를 덤프한다(트리 순서 · 결정적). 사용: ax.py <html파일>"""
import json, subprocess, time, urllib.request, sys, websocket, os, shutil, random

PORT = 19700 + random.randint(10, 89)
PROF = f"/tmp/claude-1000/-home-jun-project-study-note/239c77f1-46a6-4abb-9874-b5e9bc8f3025/scratchpad/html09b-ax-{PORT}"
shutil.rmtree(PROF, ignore_errors=True)
p = subprocess.Popen(["google-chrome", "--headless", "--disable-gpu", "--no-sandbox",
    f"--remote-debugging-port={PORT}", f"--user-data-dir={PROF}",
    "--force-renderer-accessibility", "about:blank"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    pages = []
    for _ in range(40):
        time.sleep(0.25)
        try:
            tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/list"))
            pages = [t for t in tabs if t["type"] == "page"]
            if pages: break
        except Exception: pass
    ws = websocket.create_connection(pages[0]["webSocketDebuggerUrl"], suppress_origin=True)
    mid = [0]
    def send(m, prm=None):
        mid[0] += 1
        ws.send(json.dumps({"id": mid[0], "method": m, "params": prm or {}}))
        while True:
            r = json.loads(ws.recv())
            if r.get("id") == mid[0]: return r
    send("Page.enable")
    send("Page.navigate", {"url": "file://" + os.path.abspath(sys.argv[1])})
    time.sleep(1.2)
    send("Accessibility.enable")
    nodes = send("Accessibility.getFullAXTree")["result"]["nodes"]
    by = {n["nodeId"]: n for n in nodes}
    roots = [n for n in nodes if not n.get("parentId")]
    SKIP = {"InlineTextBox", "StaticText", "none", "generic", "LineBreak"}
    KEEP = {"level"}
    def walk(n, d):
        role = n.get("role", {}).get("value", "?")
        if role not in SKIP:
            name = n.get("name", {}).get("value", "")
            props = {q["name"]: q["value"]["value"] for q in n.get("properties", [])
                     if q["name"] in KEEP}
            extra = " ".join(f"{k}={v}" for k, v in props.items())
            print(f"{'  ' * d}{role:14} 이름={name!r:22} {extra}".rstrip())
            d += 1
        for c in n.get("childIds", []):
            if c in by: walk(by[c], d)
    for r in roots: walk(r, 0)
finally:
    p.terminate(); p.wait(); shutil.rmtree(PROF, ignore_errors=True)
```

- ★ **포트를 무작위로 고르고 프로필 디렉터리도 그 포트로 짓는다** — 같은 기계에서 도는 다른 워커의 브라우저를 건드리지 않기 위해서다. 끝나면 **자기 프로세스만** 끝낸다.
- ★ **확장 프로그램의 `background_page` 가 첫 타깃으로 잡히는 사고**가 있었다 — `type == "page"` 인 타깃만 고르게 고쳤다. 안 고쳤으면 **엉뚱한 문서의 트리를 찍고도 성공으로 보였을 것**이다.
- ★ **`--force-renderer-accessibility` 가 없으면** 트리가 안 만들어질 수 있다.

**프로브 로거** — `load` 뒤 `setTimeout(…, 0)` 에서 한 번에 찍는다.

```javascript
// html09b-probe.js
window.__L = [];
window.P = function (줄) { window.__L.push(줄); };
window.addEventListener("load", function () {
  setTimeout(function () {
    if (window.__끝) window.__끝();
    var q = document.createElement("pre");
    q.textContent = "\n###P###\n" + window.__L.join("\n") + "\n###E###\n";
    document.body.appendChild(q);
  }, 0);
});
```

**본문에 안 실린 실험 파일** — 없다. A1\~A6 이 소스를 전부 싣고 있다.

**demo 블록** — [2-summary.md](2-summary.md) 의 `demo` 와 「바꿔 볼 것」을 둘 다 던져 확인했다(A6).

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| **암묵 역할 프로브 + 접근성 트리** | 2 (+ 결정성 확인 3판) | 동작 방식 (1) · A1 |
| **여덟 요소 + 중첩 넷의 접근성 트리** | 2 (+ 결정성 확인 3판) | 동작 방식 (2)·(3) · A2 |
| **`<section>` 이름 다섯 가지** | 2 | 동작 방식 (4) · A3 |
| **아는 요소·모르는 요소 열두 개** | 2 | 동작 방식 (5) · A4 |
| **`<main>` 둘**(트리 + 콘솔 + 접근성 트리) | 2 | 동작 방식 (6) · A5 |
| **demo 와 「바꿔 볼 것」** | 2 | demo 절 · A6 |

**구현에 달린 항목**

| 항목 | 이 판의 값 | 왜 다시 찍나 |
|---|---|---|
| **`sectionheader`/`sectionfooter` 라는 역할 이름** | 그대로 나옴 | **최근 ARIA 의 표면**이다. 판마다 다를 수 있다 |
| 이름 없는 `<section>`·`<aside>` 를 **트리에서 빼는 것** | 통째로 빠짐 | 「역할이 없다」를 **구현이 그렇게 표현**한 것이다 |
| UA 스타일시트의 `display: block` | 여덟 전부 | Blink 의 기본 스타일이다 |
| **`<search>` 가 동작하는 것** | 동작함 | 판이 낮으면 안 될 수 있다 |
| CDP 노드의 **평탄 목록 순서** | 트리로 재배열해 씀 | 받은 순서는 보장이 없다 — **그래서 재배열했다** |

**안 돌려 본 것** — ① **Firefox·Safari 의 접근성 트리**(엔진이 없다). ② **`role` 로 암묵 역할을 덮어쓰는 경우** — 목록의 42번 주제의 표면이라 안 던졌다. ③ **`aria-labelledby` 가 여럿을 가리킬 때의 이름 이어 붙이기** — 43번의 표면이다. ④ **`<form role="search">` 와 `<search>` 를 함께 썼을 때** — 중복 역할이 어떻게 되는지 안 던졌다. ⑤ **`<address>`·`<figure>` 등 구획이 아닌 구조 요소** — [목록의 **19번**](../19-figure-address-hr/)이다. ⑥ **건너뛰기 링크**(목록의 49번).

**못 잰 것**(「안 돌려 본 것」과 다르다) — **스크린리더가 실제로 뭐라고 읽는지 전부.** 이 판에 **읽어 줄 프로그램이 없다.** 접근성 트리는 **스크린리더의 입력**이고, 같은 트리를 받고도 보조 기술마다 다르게 읽을 수 있다 — 그래서 이 문서에는 **「이렇게 읽힌다」가 한 줄도 없다.** 쪼개서 잰 조각은 **① 역할이 무엇인가 ② 접근 가능한 이름이 무엇인가 ③ 어떤 노드가 트리에서 빠지나** 셋까지다. ★ 같은 이유로 **랜드마크 건너뛰기 동작**도 못 잰 것이다.

**부적용인 창** — **창 ③(`innerText` 대 `textContent`)과 창 ④(`compatMode`)와 창 ⑤(요청 로그)와 창 ⑥(`renderBlockingStatus`).** 구획 요소는 렌더된 글자도, 문서 모드도, 요청도, 렌더 차단도 바꾸지 않아 **잴 것이 없다**(「재 봤더니 같았다」가 아니다). ★ **창 ①도 거의 부적용이다** — 덤프에 역할이 한 글자도 안 나온다. 이 주제는 **창 ⑦ 하나가 본체**다.

## 용어 풀이

- **구획 요소(sectioning element)** — 문서를 큰 덩어리로 나누는 요소들. 이 주제의 여덟이다.
- **구획 콘텐츠(sectioning content)** — `<article>`·`<aside>`·`<nav>`·`<section>` **넷.** `<main>`·`<header>`·`<footer>` 는 **아니다.**
- **랜드마크(landmark)** — 보조 기술이 건너뛸 수 있게 표시된 큰 영역.
- **암묵 역할(implicit role)** — `role` 속성 없이 요소 이름만으로 붙는 ARIA 역할. **DOM 프로퍼티에는 안 나온다.**
- **접근 가능한 이름(accessible name)** — 보조 기술이 그 영역을 부를 때 읽는 이름. **제목은 이름이 아니다.**
- **접근성 트리(accessibility tree)** — 브라우저가 보조 기술에 넘기는 트리. **DOM 과 다르고, 빠지는 노드가 있다.**
- **`sectionheader` / `sectionfooter`** — 구획 콘텐츠 안의 `<header>`/`<footer>` 에 붙는 역할. **랜드마크가 아니다.**
- **`HTMLUnknownElement`** — 파서가 모르는 요소의 클래스. **대시가 있는 이름은 여기 안 들어간다.**
- **CDP(Chrome DevTools Protocol)** — 브라우저에 원격으로 붙어 내부 상태를 묻는 프로토콜.
- **`--force-renderer-accessibility`** — 보조 기술이 안 붙어 있어도 접근성 트리를 만들게 하는 Chrome 플래그.
