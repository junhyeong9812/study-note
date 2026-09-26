# html/syntax/09 — 스타일시트·리소스 힌트 연결: `<link rel>`·`media`·`preload`/`preconnect`/`modulepreload` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 돌려** 읽은 것이다. 하네스는 맨 아래 `## 실행 검증` 절에 있다.\
> 규칙은 [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 로 접지했다.\
> ★ **엔진은 Chrome 하나다** — 이 갈래는 이식성을 주장하지 않는다.
> ★★ **「받나 · 막나 · 먹나」를 갈라 읽어라.** 이 파일의 절반이 그 구분이다.
> ★★★ **네트워크가 없다.** `preconnect`·`dns-prefetch` 는 「**못 잰 것**」이고 A10 이 그 경계를 적는다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 「300ms 이상」 · `<p>` 는 이미 1개 · 색은 먹었다 — 막힌 것은 파싱이 아니다

**출력** (Chrome 151 headless, 로컬 HTTP 서버 위)

```text
===== 소스: html09b-block.html =====
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
===== dom http://127.0.0.1:18709/html09b-block.html | probe =====
① 링크 앞 인라인 스크립트
② 링크 뒤 인라인 스크립트 — 여기까지 300ms 이상 걸렸다
③ 트리의 <p> 개수 = 1
④ 계산값 color = rgb(66, 66, 66)
(exit 0)
```

**왜 그런가**

- **② 가 「300ms 이상」이다.** 서버가 0.5초를 재웠고 그 시간을 **링크 뒤의 인라인 스크립트가 고스란히 기다렸다.**
- **③ 의 `<p>` 는 1개다.** 스크립트가 도는 시점에 트리는 **이미 다 만들어져 있었다** — ★ **파싱은 안 막혔다.**
- **④ 는 `rgb(66, 66, 66)`** 이다. 기다린 끝에 스타일시트가 왔고 규칙이 먹었다.
- **막힌 것** = 첫 렌더 + 그 뒤의 스크립트. **안 막힌 것** = HTML 파싱.

### 2. 「300ms 미만」 · 색은 안 먹었는데 `styleSheets.length` 는 1 이다

**출력**

```text
===== 소스: html09b-block-print.html =====
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
===== dom http://127.0.0.1:18709/html09b-block-print.html | probe =====
① 링크 앞 인라인 스크립트
② 링크 뒤 인라인 스크립트 — 여기까지 300ms 미만 걸렸다
③ 트리의 <p> 개수 = 1
④ 계산값 color = rgb(0, 0, 0)
⑤ document.styleSheets.length = 1
(exit 0)
```

**왜 그런가**

- **② 가 「300ms 미만」이다** — `media="print"` 가 안 맞으므로 **렌더 차단 요소가 아니다.** 기다릴 이유가 없다.
- **④ 가 `rgb(0, 0, 0)`** — 규칙이 **안 먹었다.**
- ★★★ **⑤ 가 1 이다.** 안 먹었는데 **담기기는 담겼다.** 즉 **받아 왔다.** 이 수 하나가 「안 받는다」는 오해를 깨뜨린다.

**10판을 돌린 결정적 분류**

```text
===== for i in $(seq 1 10); do dom http://127.0.0.1:18709/html09b-block-ms.html | probe \
  | awk '{print $1, ($(NF-1) >= 300 ? "300ms 이상" : "300ms 미만")}'; done | sort | uniq -c =====
     10 막음: 300ms 이상
     10 안막음: 300ms 미만
(exit 0)
```

**같은 10판의 원시 ms** — ★ **대조할 것은 숫자가 아니라 「앞칸은 500 근처, 뒷칸은 한 자리」라는 성질이다.**

```text
===== for i in $(seq 1 10); do dom http://127.0.0.1:18709/html09b-block-ms.html | probe \
  | awk '{printf "%sms ", $(NF-1)}'; echo; done =====
498ms 0ms 
500ms 0ms 
500ms 0ms 
501ms 1ms 
500ms 1ms 
500ms 0ms 
499ms 1ms 
499ms 0ms 
499ms 0ms 
499ms 0ms 
(exit 0)
```

### 3. 넷 다 담기고 넷 다 요청된다 — 갈리는 것은 계산값뿐이다

**출력**

```text
===== 소스: html09b-media.html =====
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
===== dom http://127.0.0.1:18709/html09b-media.html | probe =====
document.styleSheets.length = 4
  html09b-base.css   media=""   규칙 1개   disabled=false
  html09b-screen.css   media="screen"   규칙 1개   disabled=false
  html09b-print.css   media="print"   규칙 1개   disabled=false
  html09b-wide.css   media="(min-width: 99999px)"   규칙 1개   disabled=false
계산값 color            = rgb(11, 11, 11)   <- base.css
계산값 outline-color    = rgb(44, 44, 44)   <- screen.css
계산값 background-color = rgba(0, 0, 0, 0)   <- print.css
계산값 padding-top      = 0px   <- wide.css
(exit 0)
```

```text
===== 이 한 판이 서버에 낸 요청 (grep -o '^/html09b-[^ ]*' srv.log | sort | uniq -c) =====
      1 /html09b-base.css
      1 /html09b-media.html
      1 /html09b-print.css
      1 /html09b-probe.js
      1 /html09b-screen.css
      1 /html09b-wide.css
(exit 0)
```

**왜 그런가**

- **`styleSheets.length = 4`** — 조건이 거짓인 둘도 **담긴다.** 규칙도 1개씩 들어 있고 `disabled` 도 전부 `false` 다.
- **요청 로그에 넷이 다 있다** — `print.css` 도 `wide.css` 도 **받아 왔다.**
- **바뀐 계산값** — `color`(조건 없음) · `outline-color`(`screen`).\
  **안 바뀐 계산값** — `background-color` 가 `rgba(0, 0, 0, 0)`(투명) · `padding-top` 이 `0px`.
- ★★ **세 창이 전부 정상인데 결과만 갈린다.** 규칙도 담겼고 시트도 살아 있는데 **조건이 거짓**일 뿐이다 — 계산값을 따로 읽지 않으면 못 잡는다.

### 4. 모르는 `rel` 은 요청조차 안 나간다 · `alternate` 는 담겼는데 안 먹는다

**출력**

```text
===== 소스: html09b-rel-unknown.html =====
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
===== dom http://127.0.0.1:18709/html09b-rel-unknown.html | probe =====
ㄱ  rel="stylesheet"   relList=[stylesheet]   sheet=있음(규칙 1, disabled=false)
ㄴ  rel="Stylesheet"   relList=[Stylesheet]   sheet=있음(규칙 1, disabled=false)
ㄷ  rel="stylesheet-zzz"   relList=[stylesheet-zzz]   sheet=null
ㄹ  rel=null   relList=[]   sheet=null
ㅁ  rel=""   relList=[]   sheet=null
ㅂ  rel="alternate stylesheet"   relList=[alternate,stylesheet]   sheet=있음(규칙 1, disabled=false)
ㅅ  rel="preload stylesheet"   relList=[preload,stylesheet]   sheet=있음(규칙 1, disabled=false)
document.styleSheets.length = 4
계산값 color      = rgb(55, 55, 55)   <- html09b-rel.css (평범한 stylesheet)
계산값 font-style = normal   <- html09b-alt.css (alternate stylesheet)
(exit 0)
```

```text
===== 이 한 판이 서버에 낸 요청 (grep -o '^/html09b-[^ ]*' srv.log | sort | uniq -c) =====
      1 /html09b-alt.css
      1 /html09b-probe.js
      1 /html09b-rel-unknown.html
      1 /html09b-rel.css
      1 /html09b-rel.css?two
      1 /html09b-rel.css?upper
(exit 0)
```

**왜 그런가**

- **`sheet` 가 있는 것은 넷** — `stylesheet` · `Stylesheet`(대소문자 무관) · `alternate stylesheet` · `preload stylesheet`.
- **`sheet=null` 인 셋** — 모르는 값 · `rel` 없음 · 빈 값.
- ★★★ **요청 로그에 `?unknown`·`?norel`·`?empty` 가 한 줄도 없다.** 「받아 놓고 안 쓴다」가 아니라 **아예 안 받는다.** 이것이 이 문항의 핵심이다.
- **`styleSheets.length = 4`** — `sheet` 가 있는 넷이 그대로 담겼다.
- ★★ **`alternate stylesheet` 의 `font-style` 이 `normal` 이다** — 요청은 나갔고 `sheet` 도 있고 `disabled` 도 `false` 인데 **규칙이 안 먹었다.** `title` 이 붙은 대체 스타일시트는 **사용자가 고르기 전까지 활성 집합에 안 들어간다.** ★ **`disabled` 가 `false` 라고 답하는 것은 Blink 의 관찰**이고, **먹지 않는다는 사실**이 명세 쪽이다.

### 5. 경고 두 줄 · 요청은 하나뿐 · 화면으로는 절대 안 보인다

**출력** — 콘솔

```text
===== google-chrome --headless --disable-gpu --no-sandbox --enable-logging=stderr \
  --dump-dom http://127.0.0.1:18709/html09b-preload-noas.html 2>&1 >/dev/null \
  | grep ':CONSOLE:' | sed 's/^\[[0-9:/.]*INFO:CONSOLE:[0-9]*\] //' | sort =====
"<link rel=preload> must have a valid `as` value", source: http://127.0.0.1:18709/html09b-preload-noas.html (6)
"<link rel=preload> must have a valid `as` value", source: http://127.0.0.1:18709/html09b-preload-noas.html (8)
(exit 0)
```

**요청 로그**

```text
===== 이 한 판이 서버에 낸 요청 (grep -o '^/html09b-[^ ]*' srv.log | sort | uniq -c) =====
      1 /html09b-preload-noas.html
      1 /html09b-withas.css
(exit 0)
```

**왜 그런가**

- **경고가 두 줄**이다. `as` 가 **없는 줄**(6) 과 **모르는 값인 줄**(8) 이 **같은 문구**로 경고났다 — 줄 번호로만 갈린다.
- **요청된 것은 `html09b-withas.css` 하나**다. 나머지 둘은 **주문서가 반품됐다.**
- ★★★ **화면으로는 알 수 없다.** 예외도 안 나고 레이아웃도 안 깨진다. **콘솔을 따로 봐야** 드러나는 무음 실패다.

### 6. `preload` 도 `modulepreload` 도 요청 1번 · 나머지 둘은 흔적이 없다

**출력**

```text
===== 소스: html09b-hints.html =====
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
===== dom http://127.0.0.1:18709/html09b-hints.html | probe =====
모듈 B 평가됨
모듈 A 평가됨 — B 에서 받은 값 = B의값
계산값 color = rgb(99, 99, 99)
rel=preload             relList=[preload]         sheet=null
rel=modulepreload       relList=[modulepreload]   sheet=null
rel=preconnect          relList=[preconnect]      sheet=null
rel=dns-prefetch        relList=[dns-prefetch]    sheet=null
rel=stylesheet          relList=[stylesheet]      sheet=있음
(exit 0)
```

```text
===== 이 한 판이 서버에 낸 요청 (grep -o '^/html09b-[^ ]*' srv.log | sort | uniq -c) =====
      1 /html09b-hint.css
      1 /html09b-hints.html
      1 /html09b-mod-a.mjs
      1 /html09b-mod-b.mjs
      1 /html09b-probe.js
(exit 0)
```

**왜 그런가**

- **`html09b-hint.css` 가 1번**이다. `preload` 로 받아 둔 것을 뒤의 `<link rel=stylesheet>` 가 **다시 안 받고 그대로 썼다.**
- **`html09b-mod-b.mjs` 도 1번**이다. `modulepreload` 로 받아 둔 것을 모듈 A 의 `import` 가 **다시 안 받았다** — 모듈 맵에 이미 올라가 있기 때문이다([08번 주제](../08-script-loading/2-summary.md)의 (4)).
- **로그의 모듈 순서** — `mod-b.mjs` 가 먼저 평가되고 `mod-a.mjs` 가 나중이다. 의존이 먼저 평가되는 것은 **JS 모듈의 규칙**이고 그쪽이 정본이다.
- ★★★ **`preconnect`·`dns-prefetch` 는 로그에 아무 자국도 없다.** 요청을 만들지 않는 힌트이므로 **당연하다.** 그리고 이 머신은 **바깥으로 못 나가므로** 연결이 실제로 열렸는지도 볼 수 없다.
- **이 판이 댈 수 있는 근거** — ① 요소가 파싱돼 `relList` 에 담겼다 ② 요청 로그가 비었다 ③ `renderBlockingStatus` 항목 자체가 안 생긴다.\
  **못 대는 것** — 연결이 열렸나 · 얼마를 아꼈나.

### 7. 파싱은 안 막고, 첫 렌더와 그 뒤의 스크립트를 막는다

**출력** — 브라우저에게 직접 물은 것

```text
===== 소스: html09b-rbs.html =====
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>무엇이 렌더를 막는가</title>
<script src="html09b-probe.js"></script>
<link rel="stylesheet"    href="html09b-base.css">
<link rel="stylesheet"    href="html09b-print.css" media="print">
<link rel="preload"       href="html09b-hint.css" as="style">
<link rel="modulepreload" href="html09b-mod-b.mjs">
<link rel="stylesheet"    href="html09b-body.css" media="(min-width: 99999px)">
</head>
<body>
<p id="과녁">과녁</p>
<script>
window.__끝 = function () {
  const 목록 = performance.getEntriesByType("resource")
    .map(e => [e.name.split("/").pop(), e.initiatorType, e.renderBlockingStatus])
    .sort((a, b) => a[0] < b[0] ? -1 : 1);   // 판마다 순서가 바뀌므로 이름으로 정렬한다
  for (const e of 목록) {
    P(e[0].padEnd(22) + ("initiatorType=" + e[1]).padEnd(24)
      + "renderBlockingStatus=" + e[2]);
  }
};
</script>
</body>
</html>
===== dom http://127.0.0.1:18709/html09b-rbs.html | probe =====
html09b-base.css      initiatorType=link      renderBlockingStatus=blocking
html09b-body.css      initiatorType=link      renderBlockingStatus=non-blocking
html09b-hint.css      initiatorType=link      renderBlockingStatus=non-blocking
html09b-mod-b.mjs     initiatorType=other     renderBlockingStatus=non-blocking
html09b-print.css     initiatorType=link      renderBlockingStatus=non-blocking
html09b-probe.js      initiatorType=script    renderBlockingStatus=blocking
(exit 0)
```

**왜 그런가**

- **`blocking` 은 둘뿐**이다 — 평범한 스크립트와 **조건이 맞는** 스타일시트.
- **`media` 가 안 맞는 스타일시트 둘 · `preload` · `modulepreload` 는 전부 `non-blocking`** 이다.
- ★★★ **왜 스크립트까지 막나** — 스크립트가 `getComputedStyle` 을 읽을 수 있기 때문이다. 아직 안 온 스타일시트가 있으면 **그 답이 틀린 값**이 된다. 그래서 브라우저는 **스타일시트를 기다린 뒤에** 스크립트를 돌린다.
- **증상** — `<head>` 의 느린 스타일시트 하나가 본문 전체를 **하얀 화면**으로 붙들어 둔다. A1 의 500ms 가 그 기다림이다.
- ★ `modulepreload` 의 `initiatorType` 이 `link` 가 아니라 **`other`** 인 것은 **Blink 의 분류**다.

### 8. 세 가지가 멈추는 자리가 다 다르다

| 무엇이 | 요청이 나가나 | `document.styleSheets` 에 담기나 | 규칙이 먹나 | 무엇으로 갈리나 |
|---|---|---|---|---|
| **`rel` 을 모른다** | **안 나간다** | 아니오 | 아니오 | **서버 요청 로그** |
| **`media` 가 안 맞는다** | **나간다** | **예** | 아니오 | **계산값** |
| **`alternate stylesheet`** | **나간다** | **예**(`disabled=false` 인 채) | 아니오 | **계산값** |

**왜 그런가**

- ★★ **「계산값이 안 바뀌었다」만 보면 셋이 전부 같아 보인다.** 세 창(요청 로그 · `styleSheets` · 계산값)을 **다 봐야** 갈린다.
- ★ **「무시된다」를 한 낱말로 적으면 이 표가 통째로 사라진다.** SQL 갈래가 「미지원」을 에러 번호로 갈랐던 것과 같은 집안이다.

### 9. `<head>` 로 안 옮겨지고, 그대로 동작하고, 앞 요소에도 먹는다

**출력** — 스크립트가 없는 판의 트리

```text
===== 소스: html09b-body-link.html =====
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>link 이 body 에 있어도 되나</title>
</head>
<body>
<p id="과녁6">과녁6</p>
<link rel="stylesheet" href="html09b-body.css">
<p id="과녁7">과녁7</p>
</body>
</html>
===== dom http://127.0.0.1:18709/html09b-body-link.html =====
<!DOCTYPE html>
<html lang="ko"><head>
<meta charset="utf-8">
<title>link 이 body 에 있어도 되나</title>
</head>
<body>
<p id="과녁6">과녁6</p>
<link rel="stylesheet" href="html09b-body.css">
<p id="과녁7">과녁7</p>


</body></html>
(exit 0)
```

**프로브를 붙인 판**

```text
===== 소스: html09b-body-link-probe.html =====
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>link 이 body 에 있어도 되나 — 프로브</title>
<script src="html09b-probe.js"></script>
</head>
<body>
<p id="과녁6">과녁6</p>
<link rel="stylesheet" href="html09b-body.css">
<p id="과녁7">과녁7</p>
<script>
window.__끝 = function () {
  const el = document.querySelector("link[rel=stylesheet]");
  P("link 의 부모 = " + el.parentNode.nodeName + "   (head 로 옮겨졌나?)");
  P("link 의 sheet = " + (el.sheet ? "있음(규칙 " + el.sheet.cssRules.length + ")" : "null"));
  P("과녁6 color = " + getComputedStyle(document.getElementById("과녁6")).color + "   <- link 보다 앞에 있는 요소");
  P("과녁7 color = " + getComputedStyle(document.getElementById("과녁7")).color + "   <- link 보다 뒤에 있는 요소");
};
</script>
</body>
</html>
===== dom http://127.0.0.1:18709/html09b-body-link-probe.html | probe =====
link 의 부모 = BODY   (head 로 옮겨졌나?)
link 의 sheet = 있음(규칙 2)
과녁6 color = rgb(101, 101, 101)   <- link 보다 앞에 있는 요소
과녁7 color = rgb(102, 102, 102)   <- link 보다 뒤에 있는 요소
(exit 0)
```

**왜 그런가**

- **파서가 안 옮긴다.** `<link>` 의 부모가 `BODY` 그대로다. 명세가 `<body>` 안의 `<link>` 를 허용한다.
- **스타일시트로 동작한다** — 규칙 2개가 담겼다.
- ★★ **자기보다 앞에 있는 `#과녁6` 에도 먹었다.** 스타일시트는 **문서 순서와 무관하게 문서 전체**에 적용된다.
- **그런데도 `<head>` 를 권하는 이유** — 늦게 발견될수록 **첫 화면을 그린 뒤에 다시 그리게** 되기 때문이다. ★ **이 판은 그 「다시 그리기」를 못 쟀다** — headless 에서 화면 갱신 횟수를 볼 수단이 없다. 그래서 위 문장은 **실측이 아니라 명세·통념을 읽어 적은 것**이다.

### 10. 「못 잰 것」이지 「안 돌려 본 것」이 아니다

**출력** — 아무도 안 쓰는 `preload` 를 0.5초 늦게 주는 파일로 건 판

```text
===== 이 한 판이 서버에 낸 요청 (grep -o '^/html09b-[^ ]*' srv.log | sort | uniq -c) =====
      1 /html09b-preload-slow.html
      1 /html09b-unused-slow.css
(exit 0)
```

**왜 그런가**

- **못 재는 이유** — 이 머신에 **네트워크가 없다.** `preconnect` 가 여는 것은 **바깥 호스트와의 연결**이고, 열렸는지도 얼마를 아꼈는지도 볼 수단이 없다.
- ★★ **「안 돌려 봄」으로 적으면 틀린다.** 실제로 **던졌고**, 파싱된 것까지는 A6 의 프로브가 **봤다.** 안 한 것이 아니라 **측정 방법 자체가 성립하지 않는 것**이다.
- **「못 잰 것」에 함께 적어야 하는 것** — ① **못 잰 이유** ② **쪼개서 잰 조각들**. 이 주제의 조각은 「파싱은 된다 · 요청은 안 난다 · 타이밍 항목이 안 생긴다」 셋이다.
- ★ 위 블록이 보이는 것은 **다른 사실**이다 — 0.5초 늦게 주는 `preload` 도 **요청 자체는 `--dump-dom` 의 대기 안에 들어온다.** 다만 이 배치는 요청의 **유무만** 봤고 **시각은 안 봤다.**

### 11. 정본 경계

| 무엇이 | 어디가 정본인가 | 여기는 어디까지 |
|---|---|---|
| 미디어 쿼리 **문법**(범위 구문·논리 결합·미디어 타입) | CSS 갈래 목록([`css/syntax/README.md`](../../../css/syntax/README.md))의 **38번**([미디어 쿼리](../../../css/syntax/38-media-queries/2-summary.md)) | `<link media>` 가 **받기·막기·먹기 중 무엇을 바꾸나** |
| 연결된 뒤 규칙이 겨루는 것(캐스케이드·명시도) | CSS 갈래의 **01번**([캐스케이드](../../../css/syntax/01-cascade-and-priority/2-summary.md))·**02번** | **문서에 담기기까지** |
| `getComputedStyle` 이라는 API 표면 | web-api 갈래 목록([`web-api/README.md`](../../../../web-api/README.md))의 **08번** | **재는 도구**로만 썼다 |
| `rel="canonical"`·`hreflang`·`rel` 토큰 전체 지도 | 목록의 **53번 주제** | **스타일시트와 리소스 힌트**까지 |
| 모듈이 한 번만 평가되는 것 | [08번 주제](../08-script-loading/2-summary.md)의 (4) | `<link rel=modulepreload>` 가 **미리 받는 것**까지 |

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · 기본 창 폭 **780**. **엔진은 이것 하나다.**\
★★ **네트워크 없음.** 바깥으로 나가는 요청은 이 판에서 관찰 불가다.

**하네스** — 09\~12 네 주제가 공유한다. 블록의 배너에 적힌 `dom`·`probe`·`ax` 가 그 함수들이다.

```bash
# html09b-harness.sh
dom()   { google-chrome --headless --disable-gpu --no-sandbox --dump-dom "$1" 2>/dev/null; }
probe() { sed -n '/^###P###$/,/^###E###$/p' | sed '1d;$d' \
          | sed 's/&lt;/</g; s/&gt;/>/g; s/&amp;/\&/g'; }
nojs()  { sed '/^<script>$/,$d'; }
ax()    { python3 html09b-ax.py "$1"; }
serve() { python3 html09b-server.py >>"$1" 2>&1 & echo $!; }
```

**서버** — 이 주제는 `file://` 이 아니라 **로컬 HTTP 서버** 위에서 돌렸다. 이유가 셋이다.\
① **한 파일을 0.5초 늦게 주어야** 렌더 차단이 시간으로 드러난다. ② **요청 로그**가 있어야 「안 받아 옴」과 「받아 놓고 안 씀」이 갈린다. ③ `file://` 은 **출처가 불투명해 `cssRules` 를 읽으면 `SecurityError`** 가 난다(첫 시도가 그래서 막혔다).

```python
# html09b-server.py
import http.server
import time


class 느린서버(http.server.SimpleHTTPRequestHandler):
    """이름에 `-slow` 가 든 파일만 0.5초 늦게 준다.

    렌더 차단은 「얼마나 기다렸나」로만 드러나므로 한 파일을 확실히 늦게 준다.
    요청 로그는 「안 받아 옴」과 「받아 놓고 안 씀」을 가르는 유일한 창이다.
    ThreadingHTTPServer 라야 한 요청을 재우는 동안 다른 요청이 지나간다.
    """

    def do_GET(self):
        if "-slow" in self.path:
            time.sleep(0.5)
        return super().do_GET()

    def log_message(self, fmt, *args):
        print(self.path, flush=True)


http.server.ThreadingHTTPServer(("127.0.0.1", 18709), 느린서버).serve_forever()
```

**프로브 로거** — `load` 뒤 `setTimeout(…, 0)` 에서 한 번에 찍는다. 그것이 `--dump-dom` 의 한계선이다([08번 주제](../08-script-loading/2-summary.md)의 (7)).

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

**실험에 쓴 스타일시트** — 전부 한 줄짜리다.

```css
/* html09b-base.css */
#과녁 { color: rgb(11, 11, 11); }
```

```css
/* html09b-screen.css */
#과녁 { outline-color: rgb(44, 44, 44); }
```

```css
/* html09b-print.css */
#과녁 { background-color: rgb(22, 22, 22); }
```

```css
/* html09b-wide.css */
#과녁 { padding-top: 33px; }
```

```css
/* html09b-rel.css */
#과녁2 { color: rgb(55, 55, 55); }
```

```css
/* html09b-alt.css */
#과녁2 { font-style: italic; }
```

```css
/* html09b-slow.css */
#과녁3 { color: rgb(66, 66, 66); }
```

```css
/* html09b-print-slow.css */
#과녁4 { color: rgb(77, 77, 77); }
```

```css
/* html09b-hint.css */
#과녁5 { color: rgb(99, 99, 99); }
```

```css
/* html09b-body.css */
#과녁6 { color: rgb(101, 101, 101); }
#과녁7 { color: rgb(102, 102, 102); }
```

**모듈 두 개** — `modulepreload` 실험용이다.

```javascript
// html09b-mod-a.mjs
import { 값 } from "./html09b-mod-b.mjs";
window.P("모듈 A 평가됨 — B 에서 받은 값 = " + 값);
```

```javascript
// html09b-mod-b.mjs
window.P("모듈 B 평가됨");
export const 값 = "B의값";
```

**본문에 안 실린 실험 파일** — 위 A 들이 소스를 전부 싣고 있고, 나머지는 이것 둘이다.

```html
<!-- html09b-rbs.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>무엇이 렌더를 막는가</title>
<script src="html09b-probe.js"></script>
<link rel="stylesheet"    href="html09b-base.css">
<link rel="stylesheet"    href="html09b-print.css" media="print">
<link rel="preload"       href="html09b-hint.css" as="style">
<link rel="modulepreload" href="html09b-mod-b.mjs">
<link rel="stylesheet"    href="html09b-body.css" media="(min-width: 99999px)">
</head>
<body>
<p id="과녁">과녁</p>
<script>
window.__끝 = function () {
  const 목록 = performance.getEntriesByType("resource")
    .map(e => [e.name.split("/").pop(), e.initiatorType, e.renderBlockingStatus])
    .sort((a, b) => a[0] < b[0] ? -1 : 1);   // 판마다 순서가 바뀌므로 이름으로 정렬한다
  for (const e of 목록) {
    P(e[0].padEnd(22) + ("initiatorType=" + e[1]).padEnd(24)
      + "renderBlockingStatus=" + e[2]);
  }
};
</script>
</body>
</html>
```

```html
<!-- html09b-block-ms.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>스타일시트가 막은 시간</title>
<script src="html09b-probe.js"></script>
<script>window.__t0 = performance.now();</script>
<link rel="stylesheet" href="html09b-slow.css">
<script>window.__막힘 = performance.now() - window.__t0;</script>
<link rel="stylesheet" href="html09b-print-slow.css" media="print">
<script>window.__안막힘 = performance.now() - window.__t0 - window.__막힘;</script>
</head>
<body>
<p id="과녁3">과녁3</p>
<script>
window.__끝 = function () {
  P("막음:   맞는 스타일시트 뒤까지 " + Math.round(window.__막힘) + " ms");
  P("안막음: media 가 안 맞는 스타일시트 뒤까지 " + Math.round(window.__안막힘) + " ms");
};
</script>
</body>
</html>
```

**demo 블록** — [2-summary.md](2-summary.md) 의 `demo` 와 「바꿔 볼 것」을 둘 다 던져 확인했다.

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| **느린 스타일시트 앞뒤의 인라인 스크립트** | 2 | 동작 방식 (1) · A1 |
| **`media="print"` 로 바꾼 같은 판** | 2 | 동작 방식 (1) · A2 |
| **차단 시간 10판 분류 + 원시 ms** | 2 (각 10판) | 동작 방식 (1) · A2 |
| **`media` 네 가지 + 요청 로그** | 2 | 동작 방식 (2) · A3 |
| **`renderBlockingStatus`** | 2 (+ 결정성 확인 3판) | 동작 방식 (3) · A7 |
| **`rel` 일곱 가지 + 요청 로그** | 2 | 동작 방식 (4) · A4 · A8 |
| **`as` 세 가지 + 콘솔 + 요청 로그** | 2 | 동작 방식 (5) · A5 |
| **힌트 네 가지 + 요청 로그** | 2 | 동작 방식 (6) · A6 |
| **안 쓰는 느린 `preload`** | 2 | 동작 방식 (6) · A10 |
| **`<body>` 안의 `<link>`**(트리 + 프로브) | 2 | 동작 방식 (7) · A9 |
| **demo 와 「바꿔 볼 것」** | 2 | demo 절 |

**구현에 달린 항목**

| 항목 | 이 판의 값 | 왜 다시 찍나 |
|---|---|---|
| **차단 시간의 ms** | 앞칸 498\~501 · 뒷칸 0\~1 | 서버가 재우는 시간 + 잡음 — **300ms 경계로만** 근거를 쓴다 |
| 콘솔 경고의 문구와 줄 번호 | ``"<link rel=preload> must have a valid `as` value"`` (6)·(8) | Blink 의 문구다. **막힌다는 사실**만 명세가 정한다 |
| `modulepreload` 의 `initiatorType` | `other` | Blink 의 분류다 |
| `alternate stylesheet` 의 `disabled` | `false` 인데 안 먹음 | Blink 의 답이다. **안 먹는다는 사실**이 명세 쪽 |
| 모르는 `rel`·`as` 에서 **요청을 안 내는 것** | 요청 0 | 명세는 「무시」까지만 말한다 — 요청 여부는 구현 |

**안 돌려 본 것** — ① **Firefox·Safari 재현**(엔진이 없다). ② **인쇄 미리보기** — `media="print"` 규칙이 실제 인쇄에서 먹는지는 안 던졌고 **화면 쪽 계산값으로만** 갈랐다. ③ **`blocking="render"` 속성** — 최근 명세의 표면인데 이 배치에서 안 던졌다. ④ **`preload` 의 `crossorigin`·글꼴 preload** — `as="font"` 는 `crossorigin` 을 요구하는데 던지지 않았다. ⑤ **`modulepreload` 가 의존 그래프를 몇 단계까지 따라가나** — 한 단계만 던졌다. ⑥ **`<link rel=stylesheet>` 가 `onload` 로 `media` 를 바꾸는 흔한 기법** — 스크립트 표면이라 뺐다.

**못 잰 것**(「안 돌려 본 것」과 다르다) — **`preconnect`·`dns-prefetch` 의 효과 전부.** 이 머신에 **네트워크가 없어** 연결이 열렸는지도, 얼마를 아꼈는지도 **잴 수단 자체가 없다**(A10). 쪼개서 잰 조각은 **① 파싱돼 `relList` 에 담긴다 ② 요청 로그가 빈다 ③ 타이밍 항목이 안 생긴다** 셋까지다. **`preload` 가 실제로 몇 ms 를 앞당기나**도 같은 상태다 — 요청의 **유무**만 봤고 **시각은 안 봤다.** 그리고 **`<body>` 안의 `<link>` 가 만드는 재렌더 횟수**도 볼 수단이 없다.

**부적용인 창** — **창 ③(`innerText` 대 `textContent`)과 창 ④(`compatMode`).** 스타일시트 연결은 렌더된 **글자**도 문서 모드도 바꾸지 않아 **잴 것이 없다**(「재 봤더니 같았다」가 아니다). ★ 대신 이 주제는 **창 ⑤(요청 로그)를 [08번 주제](../08-script-loading/2-summary.md)에서 이어받고, 창 ⑥(`renderBlockingStatus`)을 새로 세웠다.**

## 용어 풀이

- **렌더 차단(render-blocking)** — 그 자원이 올 때까지 첫 화면을 안 그리는 것. **파싱은 안 막는다.**
- **`rel`(링크 타입)** — 링크와 문서의 관계를 적는 토큰. 공백으로 여럿 쓸 수 있고 **대소문자를 안 가린다.**
- **`media`** — 그 스타일시트를 **언제 적용할지** 정한다. **받는지 여부는 안 바꾼다.**
- **`preload`** — 곧 쓸 자원을 미리 받아 두라는 힌트. **`as` 가 없으면 아무 일도 안 일어난다.**
- **`as`** — preload 하는 것이 무엇인지 말해 주는 속성. 우선순위·`Accept` 헤더·CSP 판정에 쓰인다.
- **`modulepreload`** — 모듈을 미리 받아 **모듈 맵**에 올려 두는 힌트.
- **`preconnect` / `dns-prefetch`** — 파일이 아니라 **연결**(전자) 또는 **DNS 조회**(후자)만 미리 하는 힌트.
- **`renderBlockingStatus`** — 받아 온 자원이 렌더를 막았는지를 `blocking`/`non-blocking` 으로 답하는 Resource Timing 항목.
- **대체 스타일시트(alternate stylesheet)** — `rel="alternate stylesheet"` + `title` 로 여러 벌을 두던 옛 장치. **담기지만 안 먹는다.**
- **무음 실패(silent failure)** — 예외도 화면 이상도 없이 결과만 다른 것. `as` 없는 `preload` 가 그것이다.
