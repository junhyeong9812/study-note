# html/syntax/12 — 제목 레벨과 문서 개요: `h1`\~`h6` 가 실제로 계산되는 방식 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 돌려** 읽은 것이다. 하네스는 맨 아래 `## 실행 검증` 절에 있다.\
> 규칙은 [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 와 [ARIA in HTML](https://www.w3.org/TR/html-aria/) 로 접지했다.\
> ★ **엔진은 Chrome 하나다** — 이 갈래는 이식성을 주장하지 않는다.
> ★★★ **이 주제의 본체는 접근성 트리다.** 「레벨」은 태그 이름도 글꼴 크기도 아니고 **브라우저가 계산해 보조 기술에 넘기는 값**이다(A7).
> ★★ **스크린리더가 뭐라고 읽는지는 못 본다**(A9). 「목차가 평평하게 들린다」는 **실측이 아니다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 일곱 `<h1>` 이 전부 `level=1` 이다 — 중첩은 레벨을 안 바꾼다

**출력**

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

**왜 그런가**

- ★★★ **일곱 `<h1>` 이 전부 `level=1`** 이다. 중첩 0겹·1겹·2겹·3겹, `<article>`·`<nav>`·`<aside>` 안 — **전부 같다.**
- **맨 끝 `<h2>` 만 `level=2`** 다. 레벨을 바꾼 것은 **태그 이름 하나**뿐이다.
- ★★ **랜드마크는 제대로 생겼다** — `article`·`navigation`·`complementary` 가 트리에 있다.
- ★★★ **그래서 「구획 구조는 읽히는데 제목 레벨만 안 따라간다」가 맞다.** 구획이 아무 일도 안 하는 것이 아니라, **제목 레벨만 그 구조를 안 따라가는 것**이다.
- ★ 「중첩하면 `<h1>` 이 `<h2>` 처럼 된다」가 **문서 개요 알고리즘**이었고, 그것은 **명세에 있었다가 빠졌으며 구현된 적이 없다**(A6).

### 2. 글꼴 크기도 전부 32px — 이 판에서는 줄지 않는다

**출력**

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

**콘솔**

```text
===== echo "콘솔 줄 수 = $(google-chrome --headless --disable-gpu --no-sandbox --enable-logging=stderr \
  --dump-dom http://127.0.0.1:18709/html09b-outline.html 2>&1 >/dev/null | grep -c ':CONSOLE:')" =====
콘솔 줄 수 = 0
(exit 0)
```

**왜 그런가**

- ★★★ **중첩 0\~3겹의 `<h1>` 이 전부 `32px`** 이고 `margin` 도 같다. `<article>` 안의 것도 같다.
- **작아지는 것은 태그를 바꿨을 때뿐** — `h2` 가 `24px`, `h3` 이 `18.72px`.
- ★★★ **콘솔 줄 수가 0 이다.** 「중첩 `<h1>` 은 권하지 않는다」 같은 경고가 **한 줄도 없다.** ★ **침묵도 출력이므로 명령과 종료 코드까지 담은 블록으로 남겼다.**
- ★★ **한때 브라우저 기본 스타일시트에는 중첩 `<h1>` 을 줄이는 규칙이 있었다.** Chrome 151 에는 **없다** — 개요 알고리즘이 명세에서 빠지며 **그 흔적도 정리된 것**이다. ★ 「한때 있었다」는 **명세의 옛 UA 스타일시트 권고를 읽어 적은 것**이고, 이 문서의 실측은 **지금 없다**까지다(A8).

### 3. 쓴 그대로다 — 아무도 안 막고, `aria-level` 은 이긴다

**출력**

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

**왜 그런가**

- **레벨이 1 → 3 → 6 → 2** 로 쓴 그대로다. **건너뛰어도 되돌아가도** 아무 일도 안 일어난다.
- **파서도 콘솔도 안 막는다** — A2 의 콘솔 블록이 0줄이었다.
- **`<div role="heading" aria-level="4">` 가 `level=4` 짜리 `heading` 으로** 들어갔다 — 마크업 없이 역할만으로도 제목이 된다.
- ★★★ **`<h1 aria-level="5">` 가 `level=5`** 다. **`aria-level` 이 태그가 정한 레벨을 덮어쓴다.**
- ★★ **그 답이 뜻하는 것** — 보이는 태그와 들리는 레벨이 **어긋날 수 있다.** 그래서 「ARIA 없는 것이 나쁜 ARIA 보다 낫다」가 나온다 — 목록의 **42번 주제**가 정본이다. 여기서는 **덮어쓰기가 실제로 일어난다는 것**까지만 봤다.

### 4. 역할 `group` 일 뿐 — 레벨은 하나도 안 바뀐다

**출력**

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

**트리**

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

**왜 그런가**

- ★★ **`hgroup` 의 역할은 `group`** 이다. 랜드마크도 제목도 아니다.
- **그 안의 `<h1>` 은 `level=1`, `<p>` 는 `paragraph`** — **아무것도 안 바뀐다.**
- ★★★ **`<h1>` + `<h2>` 판에서도 레벨이 1 과 2 그대로**다. 옛 `hgroup` 은 여러 제목을 **하나로 접어** 레벨을 계산해 주려던 것이었는데 **지금은 그 일을 안 한다.**
- **파서는 아무것도 안 고쳤다** — 덤프가 쓴 그대로다.

### 5. 안팎이 한 글자도 안 다르다 — 오늘 `hgroup` 은 의미 표시 하나다

**출력**

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

**왜 그런가**

- **`hgroup` 안의 `<h1>` 과 밖의 `<h1>` 이 `32px`·`margin 21.44px` 로 같다.**
- **`<p>` 도 `16px`·`margin 16px` 로 같다.**
- **`hgroup` 자체는 `display: block`** 하나뿐이다.
- ★★ **그래서 오늘 `hgroup` 이 주는 것은 「이 둘이 한 덩어리다」라는 의미 표시**와 **역할 `group`** 뿐이다. 현재 명세는 **제목 하나 + `<p>` 여럿**을 허용한다 — 부제는 `<p>` 로 쓴다.

### 6. 아무도 구현하지 않았기 때문이다

**왜 그런가**

- ① **어느 브라우저도 구현하지 않았다.** 명세에 10년 넘게 적혀 있었지만 실제로 레벨을 계산해 준 엔진이 없었다.
- ② **보조 기술도 그것을 안 썼다.** 사용자에게 도달한 적이 없다.
- ③ 그래서 「**명세에는 있는데 아무 데도 없는 규칙**」이 되었고, 명세가 **현실에 맞춰 그 절을 들어냈다.**
- ★★★ **같은 집안** — [03번 주제](../03-parser-and-error-recovery/2-summary.md)의 「XHTML 의 엄격함이 좌초한 이유」다. **WHATWG 는 구현되지 않는 규칙을 명세에 두지 않는다.** 이 주제와 03 은 **같은 결정의 앞뒤 면**이다.
- **오늘의 답** — **컴포넌트는 레벨을 속성으로 받는다.** 자기 깊이를 알 수 없으니 바깥이 알려 주는 수밖에 없다. 한때 제안됐던 `<h>` 요소(레벨 없는 제목)는 채택되지 않았다.

### 7. 태그도 글꼴도 증명이 못 된다 — 접근성 트리의 `level` 이라야 한다

**왜 그런가**

- ★★★ **태그를 세는 것은 입력을 세는 것**이다. 「`<h1>` 이라고 썼다」는 내가 쓴 것이지 **브라우저가 계산한 결과**가 아니다. 자동 계산이 있었다면 **그 계산 뒤의 값**이 달라졌을 텐데, 태그 이름은 그대로다.
- ★★★ **글꼴 크기는 CSS 다.** UA 스타일시트 한 줄로 바뀌고 내 CSS 한 줄로 되돌릴 수 있다 — **레벨이 아니다.** A2 에서 「안 작아진다」가 나왔지만, 설령 작아졌더라도 그것이 레벨의 증거가 되지는 않았다.
- ★★ **이 주제가 쓰는 창은 창 ⑦(접근성 트리)** 이다. 거기의 `level` 은 **브라우저가 계산해 보조 기술에 넘기는 값**이라, 「**자동 계산이 있었다면 달라졌을 자리**」가 정확히 거기다.

### 8. 레벨은 명세, 글꼴은 관찰

| 문장 | 명세인가 관찰인가 | 판이 오르면 |
|---|---|---|
| **중첩 `<h1>` 의 레벨이 1 이다** | **명세**(개요 알고리즘이 빠졌다) | 안 바뀐다 |
| **중첩 `<h1>` 의 글꼴이 안 작아진다** | **관찰**(Blink 의 UA 스타일시트) | ★ **다시 찍어야 한다** |

**왜 그런가**

- ★★★ **다시 찍어야 하는 것은 글꼴 쪽**이다. UA 스타일시트는 **구현의 자유**라 판마다·엔진마다 다를 수 있다.
- ★★ **「한때는 작아졌다」를 실측으로 적을 수 없다.** 이 판에 **옛 Chrome 이 없다.** 그 문장은 **명세의 옛 UA 스타일시트 권고를 읽어 적은 것**이고, 실측은 **지금 없다**까지다.
- ★ **그래서 2-summary 는 그 둘을 갈라 적었다** — 「명세」 행과 「구현(Blink)」 행이 따로다.

### 9. 「들린다」는 이 판에서 못 본다

**왜 그런가**

- ★★★ **「목차가 평평하게 들린다」는 실측이 아니다.** 이 판에 **NVDA·VoiceOver·Orca 가 없다.** 그 문장은 **명세·통념을 읽어 적은 것**이다.
- **접근성 트리가 보여 주는 것** — 역할 · 접근 가능한 이름 · `level` · 어떤 노드가 빠지나.\
  **안 보여 주는 것** — **보조 기술이 그것을 어떻게 읽는가.** 트리는 **입력**이지 출력이 아니다.
- ★★ **「레벨 건너뛰기가 얼마나 나쁜가」는 사용자 실험이 필요한 물음**이다 — **이 갈래의 도구로는 원리상 못 잰다.** 「못 잰 것」이지 「안 돌려 본 것」이 아니다.

### 10. 정본 경계

| 무엇이 | 어디가 정본인가 | 여기는 어디까지 |
|---|---|---|
| 구획 요소의 **암묵 역할**·랜드마크 | [11번 주제](../11-sectioning-and-landmarks/2-summary.md) | **그 구획이 제목 레벨을 안 바꾼다**는 것까지 |
| **UA 스타일시트가 캐스케이드의 어디에 있나** | CSS 갈래 목록([`css/syntax/README.md`](../../../css/syntax/README.md))의 **01번**([캐스케이드](../../../css/syntax/01-cascade-and-priority/2-summary.md)) | **그 값이 레벨의 증거가 아니라는 것**까지 |
| **`aria-level` 을 쓰지 말아야 하는 이유** | 목록의 **42번 주제** | **덮어쓰기가 실제로 일어난다**는 관찰까지 |
| HTML5 가 **무엇을 시도하고 무엇을 접었나** | [`history/web/03-HTML-CSS-진화.md`](../../../../../../history/web/03-HTML-CSS-진화.md) | **오늘 무엇이 되고 안 되나**까지 |
| **헤딩 콘텐츠**라는 분류 | [05번 주제](../05-content-categories-and-models/2-summary.md) | — |
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

**접근성 트리 덤프기** — [11번 주제](../11-sectioning-and-landmarks/3-answer.md)가 세운 것을 그대로 쓴다. CDP 로 `Accessibility.getFullAXTree` 를 받아 **`childIds` 를 따라가며 들여쓰기**로 찍는다(받은 순서는 보장이 없어 **트리로 재배열**했다). **세 판을 돌려 md5 가 같았다.**

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

**본문에 안 실린 실험 파일** — 없다. A1\~A5 가 소스를 전부 싣고 있다.

**demo 블록** — [2-summary.md](2-summary.md) 의 `demo` 와 「바꿔 볼 것」을 둘 다 던져 확인했다.

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

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| **중첩 `<h1>` 일곱의 접근성 트리** | 2 (+ 결정성 확인 3판) | 동작 방식 (1) · A1 · A7 |
| **같은 중첩의 글꼴 크기 + 콘솔** | 2 | 동작 방식 (2) · A2 · A8 |
| **건너뛰기 + `role=heading` + `aria-level`** | 2 | 동작 방식 (3) · A3 |
| **`hgroup` 두 가지**(접근성 트리 + 트리) | 2 | 동작 방식 (4) · A4 |
| **`hgroup` 안팎의 글꼴 크기** | 2 | 동작 방식 (4) · A5 |
| **demo 와 「바꿔 볼 것」** | 2 | demo 절 |

**구현에 달린 항목**

| 항목 | 이 판의 값 | 왜 다시 찍나 |
|---|---|---|
| ★★★ **중첩 `<h1>` 의 글꼴 크기** | **32px — 안 줄어든다** | **UA 스타일시트는 구현의 자유**다. 옛 판·다른 엔진은 다를 수 있다 |
| UA 스타일시트의 `32px`/`24px`/`18.72px`·`margin` | 그대로 | 〃 |
| `hgroup` 에 **역할 `group`** 을 주는 것 | 그대로 | ARIA 매핑이 판마다 다를 수 있다 |
| 중첩 `<h1>` 에 **경고를 안 내는 것** | 콘솔 0줄 | 판이 오르며 경고가 생길 수 있다 |
| CDP 노드의 **평탄 목록 순서** | 트리로 재배열해 씀 | 받은 순서는 보장이 없다 |

**안 돌려 본 것** — ① **Firefox·Safari 의 UA 스타일시트와 접근성 트리**(엔진이 없다). ★ **이 주제에서 가장 아쉬운 자리다** — 「중첩 `<h1>` 을 안 줄인다」가 **엔진마다 다를 수 있는 항목**이기 때문이다. ② **옛 Chrome 판** — 「한때는 줄였다」를 실측으로 확인하지 못했다. ③ **`<h1>` 을 CSS 로 다시 줄이는 경우** — CSS 갈래의 표면이다. ④ **`aria-labelledby` 로 제목이 다른 요소의 이름이 되는 경우** — 목록의 43번이다. ⑤ **`<h1>`\~`<h6>` 밖의 제목**(`role="heading"` 만 쓴 것)의 **접근 가능한 이름 계산** — 43번이다. ⑥ **검색엔진이 제목 구조를 어떻게 쓰나** — 이 목록 밖이다.

**못 잰 것**(「안 돌려 본 것」과 다르다) — **스크린리더가 목차를 어떻게 읽어 주는지 전부.** 이 판에 **읽어 줄 프로그램이 없다**(A9). 접근성 트리는 **입력**이고, 같은 트리를 받고도 보조 기술마다 다르게 읽을 수 있다 — 그래서 「목차가 평평하게 들린다」는 **명세·통념을 읽어 적은 것**이지 실측이 아니다. 쪼개서 잰 조각은 **① `level` 값이 무엇인가 ② 그 값이 중첩에 안 따라간다 ③ `aria-level` 이 그것을 덮어쓴다** 셋까지다. ★ 같은 이유로 「**레벨 건너뛰기가 얼마나 나쁜가**」는 **원리상 못 잰다** — 사용자 실험이 필요한 물음이다.

**부적용인 창** — **창 ③(`innerText` 대 `textContent`) · 창 ④(`compatMode`) · 창 ⑤(요청 로그) · 창 ⑥(`renderBlockingStatus`).** 제목 레벨은 렌더된 글자도, 문서 모드도, 요청도, 렌더 차단도 바꾸지 않아 **잴 것이 없다**(「재 봤더니 같았다」가 아니다). ★ **창 ①은 거의 부적용이다** — 덤프에는 내가 쓴 태그가 그대로 나올 뿐 **레벨이 한 글자도 안 나온다.** 다만 `hgroup` 에서 **파서가 아무것도 안 고쳤다**를 보이는 데 썼다(A4).

## 용어 풀이

- **제목 레벨(heading level)** — 그 제목이 목차에서 몇 번째 깊이인가. **`h1`\~`h6` 의 숫자가 곧 그것이다.**
- **문서 개요 알고리즘(document outline algorithm)** — 구획 중첩으로 레벨을 **자동 계산하려던** 규칙. **구현된 적 없이 명세에서 빠졌다.**
- **헤딩 콘텐츠(heading content)** — `h1`\~`h6` 와 `hgroup` 이 드는 콘텐츠 카테고리.
- **`<hgroup>`** — 제목 하나와 그에 딸린 `<p>` 들을 묶는 요소. **레벨을 안 바꾸고 역할은 `group`.**
- **`aria-level`** — 제목 레벨을 **직접 지정**하는 ARIA 속성. **태그가 정한 레벨을 덮어쓴다.**
- **`role="heading"`** — 제목이 아닌 요소를 제목으로 만드는 역할. `aria-level` 과 짝이다.
- **UA 스타일시트(user agent stylesheet)** — 브라우저가 기본으로 적용하는 스타일. **구현의 자유**다.
- **접근성 트리의 `level`** — 브라우저가 계산해 보조 기술에 넘기는 제목 깊이. **이 주제가 재는 값이 이것이다.**
- **CDP(Chrome DevTools Protocol)** — 브라우저에 원격으로 붙어 내부 상태를 묻는 프로토콜.
