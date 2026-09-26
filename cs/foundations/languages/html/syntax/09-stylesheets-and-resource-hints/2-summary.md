# html/syntax/09 — 스타일시트·리소스 힌트 연결: `<link rel>`·`media`·`preload`/`preconnect`/`modulepreload` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 [「The `link` element」](https://html.spec.whatwg.org/multipage/semantics.html#the-link-element)·[「Link types」](https://html.spec.whatwg.org/multipage/links.html#linkTypes)·[「Blocking attribute」](https://html.spec.whatwg.org/multipage/urls-and-fetching.html#blocking-attributes) 절. 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에 실제로 띄워 읽은 것이다. 하네스는 [3-answer.md](3-answer.md) 의 `## 실행 검증` 절에 있다.\
> ★ **엔진은 Chrome 하나다.** 이 갈래는 **이식성을 주장하지 않는다.**
> **버전** — HTML 에는 언어 버전이 없다. 지원 상태는 **Baseline** 으로 읽는다. `<link rel=stylesheet>` 는 1990년대부터, `preload`/`preconnect` 는 2016년 전후, `modulepreload` 는 2019년 전후에 자리 잡았다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.
> ★★ **이 주제의 본체는 창 ②(프로브)와 창 ⑤(서버 요청 로그) 둘이다** — 「담겼나」는 프로브가, 「**받아 오기는 했나**」는 요청 로그가 답한다. 그리고 이 편이 **창 ⑥(`renderBlockingStatus`)을 새로 세운다** — 「**막았나**」는 그것 말고는 물을 데가 없다. 창 넷의 정의는 [01번 주제](../01-document-skeleton/2-summary.md)의 「이 갈래의 창」 절에, 창 ⑤ 는 [08번 주제](../08-script-loading/2-summary.md)의 (6) 에 있다.
> ★★★ **네트워크가 없다.** 이 머신은 바깥으로 나가지 못한다. 그래서 `preconnect`·`dns-prefetch` 가 실제로 무엇을 아끼는지는 「**못 잰 것**」이다 — 「안 돌려 본 것」이 아니라 **잴 수단 자체가 없는 것**이다. 아래 (6) 이 그 경계를 긋는다.

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
| **흔들린다** | **차단된 시간의 ms 값** | 서버가 재우는 0.5초 + 잡음이라 끝자리가 움직인다 — 그래서 **「300ms 이상이냐」로만** 근거를 세운다 |
| **안 흔들린다** | `document.styleSheets` 의 **개수와 순서** · 각 시트의 `media`·`cssRules.length` | 명세가 정한다 |
| **안 흔들린다** | **서버 요청 로그에 이름이 있나 없나** | 〃 |
| **안 흔들린다** | `renderBlockingStatus` 의 `blocking`/`non-blocking` | 〃 |
| **안 흔들린다** | 콘솔 경고의 문구와 **줄 번호** | Blink 의 문구지만 판 안에서는 고정 |
| **안 흔들린다** | 블록의 `(exit N)` | 파서는 실패하지 않는다([03번 주제](../03-parser-and-error-recovery/2-summary.md)) |

## 한눈에 — 쉽게 말하면

**★ `<link>` 한 줄이 정하는 것은 「무엇을 받나」가 아니라 「무엇을 받고 · 무엇을 막고 · 무엇을 쓰나」 셋이다.**

공연장 무대 준비에 비유한다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 막이 오르기 전에 반드시 걸려 있어야 하는 배경막 | **`<link rel="stylesheet">`**(렌더를 막는다) |
| 「야외 공연용 배경막」이라 오늘은 안 걸지만 **창고에는 받아 둔 것** | **`media` 가 안 맞는 스타일시트** |
| 창고에 미리 갖다 두라는 **주문서** | **`preload`** |
| 「무슨 물건인지」를 안 적어 창고가 **반품한 주문서** | **`as` 가 없는 `preload`** |
| 납품 트럭을 **미리 문 앞에 대 두는 것** | **`preconnect`·`dns-prefetch`** |
| 새 규격 자재 전용 주문서 | **`modulepreload`** |
| 창고 직원이 **모르는 낱말이 적힌 주문서** | **`rel` 값을 모를 때** — 아무 일도 안 일어난다 |

- **스타일시트는 렌더를 막는다.** 그리고 **그 뒤의 스크립트도 막는다** — 아래 (1) 이 실측이다.
- **`media` 가 안 맞아도 받기는 받는다.** 안 하는 것은 **막는 일과 먹는 일**뿐이다.
- **`rel` 을 모르면 요청조차 안 나간다.** 「받아 놓고 안 쓴다」가 아니다.

```text
  <link> 한 줄이 지나가는 세 관문

  ① rel 을 아는가?
       모른다 -> 여기서 끝. 요청도 안 나간다        <- (4) 의 실측
       안다   -> 다음
          │
  ② 이 상황에 쓰이는가? (media / as)
       안 맞는다 -> 받기는 받는다. 막지도 먹지도 않는다   <- (2) 의 실측
       맞는다   -> 다음
          │
  ③ 렌더를 막는가?
       stylesheet -> 막는다 (그 뒤 스크립트까지)          <- (1)·(3) 의 실측
       preload 류 -> 안 막는다
```

실무에서 이게 터지는 자리는 **`preload` 를 붙여 놓고 `as` 를 빠뜨렸을 때**다.\
화면은 멀쩡하고 예외도 안 나는데 **그 파일은 애초에 받아지지도 않았다** — 콘솔에만 한 줄 남는다.\
그리고 더 헷갈리는 자리는 **`media="print"` 스타일시트를 「안 받는다」고 읽는 것**이다 — 받는다.

> **렌더 차단(render-blocking)** — 그 자원이 올 때까지 브라우저가 **첫 화면을 안 그리는** 것.\
> 예: 느린 스타일시트 하나가 본문 전체를 **하얀 화면**으로 붙들어 둔다.

> **리소스 힌트(resource hint)** — 「이건 곧 필요할 거야」를 브라우저에 미리 알려 주는 `<link>`.\
> 예: `preload` 는 파일을, `preconnect` 는 **연결 자체**를 미리 준비시킨다.

## 이 주제가 답하려는 질문

1. **스타일시트는 정확히 무엇을 막는가.** 파싱인가, 렌더인가, 스크립트인가.
2. **`rel`·`media`·`as` 가 안 맞을 때 각각 어디까지 일어나는가.** 「무시된다」가 한 낱말이 아니다.
3. **네트워크 없이 잴 수 있는 힌트와 못 잴 힌트는 무엇인가.**

## 동작 방식

### (1) 창 ② — 스타일시트는 「그 뒤의 스크립트」를 막는다

**언제 쓰나** — 모든 문서의 `<head>`. **이 주제의 첫 관문**이다.

한 파일만 **0.5초 늦게 주는 로컬 서버** 위에서 던졌다. 링크 앞뒤에 인라인 스크립트를 하나씩 두고, 뒤엣것이 **얼마나 기다렸나**를 찍는다.

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

**같은 자리에 `media="print"` 만 붙인 판**은 이렇게 갈린다.

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

```text
  0.5초 늦게 주는 스타일시트 하나가 무엇을 붙드나

  시각 ->  0ms                          500ms
           |                              |
  파서     [<head> 읽기][<body> 읽기 끝]   |      <- 트리는 여기서 이미 다 만들어졌다
           |                              |
  링크     [--------- 받는 중 ----------]  |
           |                              |
  ② 스크립트                              [실행]  <- 500ms 를 기다렸다
           |                              |
  첫 렌더                                  [그림]  <- 그때까지 하얀 화면

  media="print" 판은 링크 줄만 있고 ②와 첫 렌더가 0ms 에 붙는다.
```

- ★★ **스타일시트가 막는 것은 파싱이 아니다.** 트리의 `<p>` 는 두 판 모두 **1개**로 다 만들어져 있다.
- ★★★ **막히는 것은 「그 뒤의 스크립트」와 「첫 렌더」다.** 스크립트가 스타일을 읽을 수 있어야 하므로 브라우저가 **먼저 스타일시트를 기다린다.**
- `media="print"` 판은 기다리지 않았는데도 **계산값이 안 바뀌었다**(`rgb(0, 0, 0)`) — 받았지만 **안 먹은 것**이다.

**한 블록에 결정적인 것과 흔들리는 것을 섞지 않는다.** 먼저 결정적인 쪽 — 10판을 돌려 **분류만** 센다.

```text
===== for i in $(seq 1 10); do dom http://127.0.0.1:18709/html09b-block-ms.html | probe \
  | awk '{print $1, ($(NF-1) >= 300 ? "300ms 이상" : "300ms 미만")}'; done | sort | uniq -c =====
     10 막음: 300ms 이상
     10 안막음: 300ms 미만
(exit 0)
```

같은 10판의 **원시 ms 값**은 따로 싣는다. ★ **대조할 것은 숫자가 아니라 「앞칸이 500 근처이고 뒷칸이 한 자리」라는 성질이다.**

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

### (2) 창 ② + 창 ⑤ — `media` 가 안 맞으면 「받되 안 막고 안 먹는다」

**언제 쓰나** — 「인쇄용 CSS 는 화면에서 안 받겠지」라고 읽는 자리.

네 개를 한 문서에 걸었다 — 조건 없음 · `screen` · `print` · `(min-width: 99999px)`.

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

**그런데 안 먹은 둘을 받기는 받았나** — 같은 한 판이 서버에 낸 요청이다.

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

```text
  media 가 안 맞는 스타일시트가 멈추는 자리

        받나        담기나            막나        먹나
       ------      --------          ------      ------
  맞음   O     ->      O        ->      O    ->     O
  안맞음 O     ->      O        ->      X    ->     X
                                       ^            ^
                                       |            |
                          여기서부터가 「안 하는 일」이다.
                          「안 받는다」가 아니다 — 요청 로그가 그것을 말한다.
```

- ★★★ **넷 다 요청됐다.** `print` 도 `(min-width: 99999px)` 도 **파일은 받아 온다.**
- **넷 다 `document.styleSheets` 에 담겼고** 규칙도 1개씩 들어 있고 `disabled` 도 전부 `false` 다.
- **다른 것은 계산값 하나뿐이다** — `background-color` 는 `rgba(0, 0, 0, 0)`(투명, 안 먹음), `padding-top` 은 `0px`(안 먹음).
- ★★ **「진단 3창」이 전부 정상인데 결과만 갈리는 자리**다. CSS 갈래가 「제5의 상태」라고 부른 것과 같은 모양이라, **계산값을 따로 안 읽으면 못 잡는다.**

> **`media` 속성** — 그 스타일시트를 **언제 적용할지** 미디어 쿼리로 적는 것.\
> 예: `media="print"` 는 인쇄할 때만 먹는다. **받지 않는다는 뜻이 아니다.**

★ **미디어 쿼리 문법 자체는 CSS 쪽이 정본이다** — [CSS 38번 주제(미디어 쿼리)](../../../css/syntax/38-media-queries/2-summary.md). 여기는 **`<link media>` 가 받기·막기·먹기 중 무엇을 바꾸나**까지다.

### (3) 창 ⑥ (새 창) — 무엇이 렌더를 막는지 브라우저에게 직접 묻는다

**언제 쓰나** — (1) 의 시간 재기는 **간접 증거**다. 직접 물을 방법이 있다.

`PerformanceResourceTiming.renderBlockingStatus` 는 받아 온 자원마다 **`blocking` / `non-blocking`** 을 답한다.\
★ 판마다 순서가 바뀌므로 **이름으로 정렬**해 결정적으로 만들었다.

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

```text
  창 ⑥ 이 답하는 자리 — 「시간을 재서 추측」 대신 「브라우저에게 직접」

  창 ①  --dump-dom            트리는 다 있다        -> 막혔는지 알 수 없다
  창 ②  프로브로 시간 재기      500ms 걸렸다          -> 「막혔다」를 추측한다
  창 ⑤  요청 로그              받아 오기는 했다        -> 막았는지는 모른다
  창 ⑥  renderBlockingStatus  blocking / non-blocking  <- 직접 답한다
```

- ★★★ **이 한 블록이 이 주제의 절반을 답한다** — 막는 것은 **평범한 스크립트와 조건이 맞는 스타일시트**뿐이다.
- `media` 가 안 맞는 스타일시트 둘, `preload`, `modulepreload` 는 **전부 `non-blocking`** 이다.
- ★ `modulepreload` 의 `initiatorType` 은 `link` 가 아니라 **`other`** 로 나왔다 — **Blink 의 분류**이지 명세의 보장이 아니다.

### (4) 창 ② + 창 ⑤ — `rel` 값을 모르면 요청조차 안 나간다

**언제 쓰나** — 오타·새 낱말·여러 토큰을 쓴 자리.

일곱 가지를 한 문서에 걸었다.

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

**그리고 같은 한 판의 요청 로그다.**

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

```text
  rel 토큰 하나가 가르는 것

  <link rel="stylesheet" ...>      -> 안다   -> 요청 O -> sheet O -> 규칙 O
  <link rel="Stylesheet" ...>      -> 안다   -> 요청 O -> sheet O -> 규칙 O   (대소문자 무관)
  <link rel="preload stylesheet">  -> 안다   -> 요청 O -> sheet O -> 규칙 O   (토큰 여럿)
  <link rel="alternate stylesheet" title="...">
                                   -> 안다   -> 요청 O -> sheet O -> 규칙 X   ★ 제4의 상태
  <link rel="stylesheet-zzz" ...>  -> 모른다 -> 요청 X
  <link                      ...>  -> 없다   -> 요청 X
  <link rel=""               ...>  -> 없다   -> 요청 X
```

- ★★★ **`?unknown`·`?norel`·`?empty` 가 로그에 한 줄도 없다.** 「받아 놓고 안 쓴다」가 아니라 **아예 안 받는다.**
- `rel="Stylesheet"` 는 먹는다 — **링크 타입은 대소문자를 안 가린다.** 다만 `relList` 는 **쓴 글자 그대로** 돌려준다.
- **여러 토큰을 띄어쓰기로 나열**할 수 있다. `preload stylesheet` 는 **스타일시트로 동작**했다.
- ★★ **`alternate stylesheet` 가 제4의 상태다** — 요청은 나갔고(`html09b-alt.css`) `sheet` 객체도 있고 `disabled` 도 `false` 인데 **계산값이 안 바뀌었다**(`font-style: normal`). **세 창이 전부 「정상」이라고 답하는데 규칙만 안 먹는다.**

### (5) 창 ⑤ + 콘솔 — `preload` 에 `as` 가 없으면

**언제 쓰나** — `preload` 를 처음 붙일 때 가장 흔한 실수.

세 가지를 걸었다 — `as` 없음 · `as="style"` · `as="zzznope"`.

```text
===== google-chrome --headless --disable-gpu --no-sandbox --enable-logging=stderr \
  --dump-dom http://127.0.0.1:18709/html09b-preload-noas.html 2>&1 >/dev/null \
  | grep ':CONSOLE:' | sed 's/^\[[0-9:/.]*INFO:CONSOLE:[0-9]*\] //' | sort =====
"<link rel=preload> must have a valid `as` value", source: http://127.0.0.1:18709/html09b-preload-noas.html (6)
"<link rel=preload> must have a valid `as` value", source: http://127.0.0.1:18709/html09b-preload-noas.html (8)
(exit 0)
```

**요청 로그는 이렇게 답한다.**

```text
===== 이 한 판이 서버에 낸 요청 (grep -o '^/html09b-[^ ]*' srv.log | sort | uniq -c) =====
      1 /html09b-preload-noas.html
      1 /html09b-withas.css
(exit 0)
```

```text
  as 는 「무엇을 받을지」를 말해 주는 칸이다

  <link rel="preload" href="a.css" as="style">
                                    ~~~~~~~~~~
                                    |
                    우선순위를 정하고 · Accept 헤더를 고르고 · CSP 를 판정한다

  as 가 없으면 그 셋을 못 정한다 -> 브라우저는 아예 안 받는다
      ㄴ 화면 멀쩡 · 예외 없음 · 레이아웃 그대로 · 콘솔에 한 줄
```

- ★★★ **경고도 출력이다.** 화면은 멀쩡하고 예외도 없다. **콘솔을 따로 봐야** 드러난다.
- **`as` 가 없는 것과 모르는 값을 쓴 것이 같은 문구**로 경고났다 — 줄 번호(6)·(8) 로만 갈린다.
- **받아진 것은 `as="style"` 하나뿐**이다. 나머지 둘은 **주문서가 반품됐다.**

### (6) 네 힌트 중 둘만 잴 수 있다 — 「못 잰 것」을 그렇게 적는다

**언제 쓰나** — 이 문서가 **어디까지 근거를 댈 수 있나**를 긋는 자리.

네 힌트를 한 문서에 걸고, 그중 `preload` 와 `modulepreload` 는 **실제로 쓰이는 데까지** 이었다.

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

```text
  네 힌트가 각각 어디까지 미리 하나 (왼쪽이 이 판에서 관찰 가능)

  관찰 O  modulepreload  DNS -> TCP -> TLS -> 요청 -> 모듈 맵에 올림
  관찰 O  preload        DNS -> TCP -> TLS -> 요청 -> 캐시에 둠
  관찰 X  preconnect     DNS -> TCP -> TLS                  <- 요청을 안 만든다
  관찰 X  dns-prefetch   DNS                                <- 조회만 한다

  오른쪽 둘은 이 머신에 네트워크가 없어 「못 잰 것」이다.
```

- **`preload` 한 파일이 요청 1번**이다 — 미리 받아 둔 것을 `<link rel=stylesheet>` 가 **다시 안 받고 썼다.**
- **`modulepreload` 로 미리 받은 `mod-b.mjs` 도 1번**이다 — 모듈 A 가 `import` 할 때 **다시 안 받았다**. 모듈이 한 번만 평가되는 것은 [08번 주제](../08-script-loading/2-summary.md)의 (4) 가 정본이다.
- ★★★ **`preconnect`·`dns-prefetch` 는 로그에 아무 자국도 없다.** 당연하다 — **연결만 미리 여는 힌트라 요청을 만들지 않는다.** 그리고 이 머신은 **바깥으로 못 나가므로** 그 연결이 실제로 열렸는지도 확인할 수 없다.
- ★★ **그래서 이 둘은 「못 잰 것」이다.** 「안 돌려 봤다」가 아니다 — **던졌고, 파싱된 것까지는 위 프로브가 보였고**(`relList=[preconnect]`), **그 다음을 볼 수단이 이 판에 없다.**
- **쪼개서 잰 조각** — ① 요소가 파싱돼 `relList` 에 담긴다 ② 요청 로그에 아무것도 안 남는다 ③ `renderBlockingStatus` 로도 안 잡힌다(자원이 아니므로 항목 자체가 없다). **여기까지가 이 판이 댈 수 있는 근거의 전부다.**

**`--dump-dom` 의 대기 한계와 만나는 자리** — 아무도 안 쓰는 `preload` 를 **0.5초 늦게 주는** 파일로 걸어 보았다.

```text
===== 이 한 판이 서버에 낸 요청 (grep -o '^/html09b-[^ ]*' srv.log | sort | uniq -c) =====
      1 /html09b-preload-slow.html
      1 /html09b-unused-slow.css
(exit 0)
```

- **요청은 로그에 남았다.** `--dump-dom` 이 기다려 주는 `load` + `setTimeout(…, 0)` 안에 0.5초가 들어간다는 뜻이다.
- ★★ **하지만 그것이 「언제 받았나」를 잰 것은 아니다.** 이 배치는 **요청의 유무만** 봤고 **시각은 안 봤다**. `preload` 가 실제로 **얼마를 앞당기는지**는 이 판에서 **못 잰 것**이다.
- ★ **`--virtual-time-budget` 으로 늘리는 것은 금지**다 — 가상 시간이 먼저 흘러 「아무 일도 안 일어남」이 찍히는 사고가 이 저장소에 실측으로 남아 있다.

### (7) 창 ① — `<link>` 가 `<body>` 에 있어도 되나

**언제 쓰나** — 컴포넌트마다 스타일시트를 옆에 두고 싶을 때.

`<body>` 한가운데에 `<link rel=stylesheet>` 를 두고, **그보다 앞에 있는 요소**와 **뒤에 있는 요소**를 하나씩 놓았다.

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

★ **파서가 안 고쳤다** — `<link>` 가 `<body>` 에 그대로 남아 있다. [03번 주제](../03-parser-and-error-recovery/2-summary.md)에서 본 「파서가 고쳐 주는 것」 목록에 이것은 없다.

**같은 마크업에 프로브를 붙인 판**이다.

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

```text
  <body> 안의 <link> 가 적용되는 범위

  <body>
    <p id="과녁6">    <- rgb(101,101,101)  ★ 링크보다 앞인데도 먹는다
    <link rel=stylesheet>
    <p id="과녁7">    <- rgb(102,102,102)

  스타일시트는 「여기서부터」가 아니라 「문서 전체」에 걸린다.
```

- **`<head>` 로 옮겨지지 않는다** — 부모가 `BODY` 그대로다.
- **스타일시트로 동작한다** — 규칙 2개가 담겼다.
- ★★ **자기보다 앞에 있는 요소에도 먹는다.** 스타일시트는 **문서 순서와 무관하게 문서 전체**에 적용된다.
- ★ 다만 **명세가 `<body>` 안의 `<link>` 를 허용하는 것과 그것이 좋은 배치인 것은 다른 문제**다 — 늦게 발견될수록 **첫 화면이 다시 그려진다.** 이 판은 그 「다시 그리기」를 **못 쟀다**(화면 갱신 횟수를 볼 수단이 없다).

### demo — `media` 가 안 맞으면 규칙이 담겨도 안 먹는다

```html demo
<p class="ㄱ">화면에서 보이는 색</p>
<style media="screen">.ㄱ { color: rgb(17, 17, 17); }</style>
<style media="print">.ㄱ { color: rgb(220, 38, 38); }</style>
<style media="(min-width: 99999px)">.ㄱ { font-weight: 700; }</style>
```

> **보이는 것** — 글자가 거의 검정(`rgb(17, 17, 17)`)으로 한 줄 나온다. 빨강도 굵은 글씨도 안 나온다. 그런데 `document.styleSheets` 에는 **세 개가 다 담겨 있고** 규칙도 1개씩 들어 있다 — 조건이 거짓일 뿐이다.\
> **바꿔 볼 것** — `media="print"` → `media="all"`(글자가 빨강 `rgb(220, 38, 38)` 이 된다) · `(min-width: 99999px)` → `(min-width: 1px)`(굵어져 `font-weight: 700` 이 된다)

*(Chrome 151 headless 실측, 창 폭 780: `color = rgb(17, 17, 17)` · `font-weight = 400` · `styleSheets.length = 3` · `matchMedia` 가 `screen` 만 `true`)*

```text
===== 소스: html09b-demo09a.html (demo 블록 + 래퍼 + 측정 프로브) =====
<!DOCTYPE html>
<meta charset="utf-8">
<title>demo 09 검증</title>
<body>
<p class="ㄱ">화면에서 보이는 색</p>
<style media="screen">.ㄱ { color: rgb(17, 17, 17); }</style>
<style media="print">.ㄱ { color: rgb(220, 38, 38); }</style>
<style media="(min-width: 99999px)">.ㄱ { font-weight: 700; }</style>
<script>
const o = [];
const e = document.querySelector(".ㄱ"), s = getComputedStyle(e);
o.push("창 폭 = " + window.innerWidth);
o.push("color       = " + s.color       + "   <- media=screen 규칙만 먹었다");
o.push("font-weight = " + s.fontWeight  + "   <- (min-width: 99999px) 는 거짓이라 안 먹었다");
o.push("document.styleSheets.length = " + document.styleSheets.length + "   <- 세 개 다 담겨는 있다");
for (const sh of document.styleSheets) {
  o.push("   media=" + JSON.stringify(sh.media.mediaText)
    + "   규칙 " + sh.cssRules.length + "개   matchMedia = "
    + (sh.media.mediaText === "" ? "(조건 없음)" : matchMedia(sh.media.mediaText).matches));
}
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
===== dom html09b-demo09a.html | probe =====
창 폭 = 780
color       = rgb(17, 17, 17)   <- media=screen 규칙만 먹었다
font-weight = 400   <- (min-width: 99999px) 는 거짓이라 안 먹었다
document.styleSheets.length = 3   <- 세 개 다 담겨는 있다
   media="screen"   규칙 1개   matchMedia = true
   media="print"   규칙 1개   matchMedia = false
   media="(min-width: 99999px)"   규칙 1개   matchMedia = false
(exit 0)
```

**「바꿔 볼 것」에 적은 단언도 따로 던져 확인했다.**

```text
===== 소스: html09b-demo09b.html (demo 블록 + 래퍼 + 측정 프로브) =====
<!DOCTYPE html>
<meta charset="utf-8">
<title>demo 09 「바꿔 볼 것」 검증</title>
<body>
<p class="ㄱ">99999px -> 1px 로 바꾼 판</p>
<style media="screen">.ㄱ { color: rgb(17, 17, 17); }</style>
<style media="all">.ㄱ { color: rgb(220, 38, 38); }</style>
<style media="(min-width: 1px)">.ㄱ { font-weight: 700; }</style>
<script>
const o = [];
const s = getComputedStyle(document.querySelector(".ㄱ"));
o.push("창 폭 = " + window.innerWidth);
o.push('media="print" -> media="all" 로 바꾸면  color       = ' + s.color);
o.push('99999px       -> 1px       로 바꾸면  font-weight = ' + s.fontWeight);
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
===== dom html09b-demo09b.html | probe =====
창 폭 = 780
media="print" -> media="all" 로 바꾸면  color       = rgb(220, 38, 38)
99999px       -> 1px       로 바꾸면  font-weight = 700
(exit 0)
```

★ 이 demo 는 `<style media>` 로 보인다. `<link media>` 와 **같은 규칙**인데 `demo` 블록은 **외부 파일에 기댈 수 없어서**다([render-rules.md](../../../../../../reference/render-rules.md)의 「자기완결」).

## 문법 — 형태와 규칙

HTML 은 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 여섯 가지

```html
<link rel="stylesheet" href="a.css">
<link rel="stylesheet" href="print.css" media="print">
<link rel="preload" href="a.css" as="style">
<link rel="modulepreload" href="a.mjs">
<link rel="preconnect" href="https://cdn.example.com">
<link rel="dns-prefetch" href="https://cdn.example.com">
```

### 금지 사례 — 아무 일도 안 일어나는 자리

```html
<link rel="stylesheet-zzz" href="a.css">
<link href="a.css">
<link rel="" href="a.css">
<link rel="preload" href="a.css">
<link rel="preload" href="a.css" as="zzznope">
```

- 앞의 셋은 **`rel` 을 모르는 경우**다 — 요청조차 안 나간다((4)).
- 뒤의 둘은 **`as` 가 없거나 모르는 값**이다 — 콘솔 경고 한 줄 + 요청 없음((5)).
- ★ 다섯 줄 **전부 예외가 안 난다.** 화면도 안 깨진다.

### 어디서 헷갈리나

- **`media` 는 「받을지」가 아니라 「먹일지」를 정한다.** 받는 것은 어차피 받는다.
- **`preload` 는 「빨리 받아라」가 아니다.** 「**이건 곧 쓸 거니까 우선순위를 올려서 미리 받아 둬라**」이고, `as` 로 **무엇인지 말해 줘야** 그 우선순위를 정할 수 있다.
- **`modulepreload` 는 `preload as="script"` 와 다르다.** 모듈 그래프를 따라 **의존까지** 준비하려는 힌트다(이 판에서는 **한 단계만** 던져 확인했다).
- **`preconnect` 는 파일을 안 받는다.** 연결(DNS·TCP·TLS)만 미리 연다.

## 어디서 틀리나

### 1. 「`media` 가 안 맞으면 안 받는다」고 읽는다

**받는다.** (2) 의 요청 로그에 **넷이 다 있다.**\
★ 안 하는 것은 **막는 일과 먹는 일**뿐이다. 트래픽을 아끼려고 `media` 를 쓰는 것이 아니다.

### 2. `preload` 에 `as` 를 빠뜨린다

**요청이 아예 안 나간다.** 콘솔에 한 줄 나고 끝난다((5)).\
★ 이 주제에서 가장 조용한 자리다 — **화면은 멀쩡하다.**

```text
  「무시된다」를 한 낱말로 쓰면 이 세 층이 사라진다

  rel 을 모른다        |----|                              안 받는다
  media 가 안 맞는다   |------------------|                 받고 담기고 안 먹는다
  alternate stylesheet |------------------|                 받고 담기고 안 먹는다
                       요청    styleSheets   계산값
                       ^       ^             ^
                       |       |             |
                    요청 로그  프로브       getComputedStyle
                     로만     로만           로만
                     갈린다   갈린다         갈린다
```

### 3. `rel` 오타를 「받아 놓고 안 쓰는 것」으로 읽는다

**안 받는다.** 요청 로그에 한 줄도 없다((4)).\
★ 「무시된다」를 한 낱말로 적으면 이 구분이 사라진다.

### 4. 스타일시트가 **파싱**을 막는다고 본다

**파싱은 안 막는다.** (1) 에서 트리의 `<p>` 는 두 판 모두 다 만들어져 있었다.\
★ 막는 것은 **첫 렌더와 그 뒤의 스크립트**다.

### 5. `alternate stylesheet` 가 `disabled=false` 니까 먹는 줄 안다

**안 먹었다.** (4) 에서 `font-style` 이 `normal` 그대로였다.\
★ **계산값을 따로 읽어야만** 갈린다 — `sheet` 가 있다는 것은 「담겼다」이지 「먹는다」가 아니다.

### 6. `preconnect` 의 효과를 「빨라졌다」로 적는다

**이 판에서는 못 잰다.** 네트워크가 없다((6)).\
★ **「못 잰 것」과 「안 돌려 본 것」은 다르다.** 던졌고, 파싱된 것까지는 봤고, 그 다음을 볼 수단이 없다.

## 구현 세부사항 대 언어 보장

★ **HTML 은 명세가 오류 복구까지 정한 언어**라 「구현 정의」 칸이 작다. 세 층으로 갈라 적는다.

| 층 | 무엇을 보장하나 | 이 주제에서 |
|---|---|---|
| **명세(HTML)** | 모르는 `rel` 토큰은 **무시** | (4) 의 `sheet=null` |
| **명세(HTML)** | `media` 가 안 맞는 스타일시트는 **렌더를 막지 않는다** | (2)·(3) |
| **명세(HTML)** | 맞는 스타일시트는 **렌더 차단 요소** | (1)·(3) 의 `blocking` |
| **명세(HTML)** | `rel="preload"` 는 **`as` 를 요구**한다 | (5) 의 경고 |
| **명세(HTML)** | `<link>` 는 **`<body>` 에도 놓을 수 있다** | (7) |
| **명세(Resource Timing)** | `renderBlockingStatus` 라는 항목의 존재 | (3) |
| **구현(Blink)** | **모르는 `rel` 은 요청도 안 낸다** | (4) 의 요청 로그 — 명세는 「무시」까지만 말한다 |
| **구현(Blink)** | **`as` 가 없으면 요청도 안 낸다** + 경고 문구 | (5) |
| **구현(Blink)** | `modulepreload` 의 `initiatorType = other` | (3) |
| **구현(Blink)** | `alternate stylesheet` 가 `disabled=false` 인데 안 먹는 것 | (4) |
| **이 판의 관찰** | 차단 시간이 **500ms 근처**라는 것 | 서버가 재우는 시간 + 이 머신의 잡음 |

**도구가 못 보는 것**

- ★★★ **네트워크 바깥.** `preconnect`·`dns-prefetch` 가 **실제로 아끼는 시간**을 볼 수단이 없다((6)).
- ★★ **「언제 받았나」.** 이 배치는 요청의 **유무**만 봤다. `preload` 가 **얼마를 앞당기는지**는 못 쟀다.
- **화면이 몇 번 다시 그려졌나.** `<body>` 안의 `<link>` 가 만드는 재렌더를 headless 로는 세지 못했다((7)).
- **다른 엔진.** Chrome 하나뿐이라 이식성을 주장할 수 없다. **`renderBlockingStatus` 자체가 Blink 가 먼저 낸 항목**이다.
- **인쇄 미리보기.** `media="print"` 규칙이 **실제 인쇄에서 먹는지**는 안 던졌다 — 화면 쪽 계산값으로만 갈랐다.

## 언제 쓰고 언제 안 쓰나

- **스타일시트는 `<head>` 에, 되도록 적게** — 첫 화면을 붙드는 것이 이것이다.
- **`media` 는 「이 조건에서만 먹여라」로만 쓴다** — 트래픽 절약 수단이 아니다.
- **`preload` 는 「곧 확실히 쓸 것」에만** — 안 쓰면 대역폭만 먹고 경고도 안 난다.
- **`preload` 에는 언제나 `as`** — 없으면 아무 일도 안 일어난다.
- **`modulepreload` 는 모듈 진입점의 의존에** — [08번 주제](../08-script-loading/2-summary.md)의 `type="module"` 과 짝이다.
- **`preconnect` 는 두세 개까지** — 연결을 여는 것도 비용이다. 이 판에서는 **효과를 못 잰다.**
- **`<body>` 안의 `<link>` 는 쓸 수 있지만 기본은 `<head>`** — 늦게 발견될수록 다시 그린다.

## 핵심 문장

1. **`<link>` 한 줄은 「받나 · 막나 · 먹나」 셋을 따로 정한다.**
2. **`media` 가 안 맞는 스타일시트는 받고, 담기고, 안 막고, 안 먹는다.**
3. **`rel` 을 모르면 요청조차 안 나간다 — 「받아 놓고 안 쓴다」가 아니다.**
4. **`preload` 에 `as` 가 없으면 콘솔 경고 한 줄과 함께 아무 일도 안 일어난다.**
5. **스타일시트가 막는 것은 파싱이 아니라 첫 렌더와 그 뒤의 스크립트다.**
6. **`renderBlockingStatus` 가 「무엇이 막나」를 직접 답한다 — 시간 재기보다 강한 근거다.**
7. **`preconnect`·`dns-prefetch` 의 효과는 이 판에서 「못 잰 것」이다.**

## 관련 자료

- [08번 주제 — 스크립트 로딩](../08-script-loading/2-summary.md) — **요청 로그라는 창**과 `type="module"` 은 그쪽이 정본이다. 여기는 **`<link>` 가 그 모듈을 미리 받는 것**까지.
- [05번 주제 — 콘텐츠 카테고리](../05-content-categories-and-models/2-summary.md) — `<link>` 가 **메타데이터 콘텐츠**이면서 **흐름 콘텐츠로도 셈해지는** 근거.
- [03번 주제 — 파서와 오류 복구](../03-parser-and-error-recovery/2-summary.md) — `<body>` 안의 `<link>` 를 파서가 왜 안 고치는지.
- CSS 갈래 목록([`css/syntax/README.md`](../../../css/syntax/README.md))의 **38번**([미디어 쿼리](../../../css/syntax/38-media-queries/2-summary.md)) — **미디어 쿼리 문법·범위 구문은 그쪽이 정본이다.** 여기는 `<link media>` 가 **받기·막기·먹기 중 무엇을 바꾸나**까지.
- CSS 갈래 목록([`css/syntax/README.md`](../../../css/syntax/README.md))의 **01번**([캐스케이드](../../../css/syntax/01-cascade-and-priority/2-summary.md)) — **연결된 뒤 규칙이 겨루는 이야기**는 그쪽이다.
- web-api 갈래 목록([`web-api/README.md`](../../../../web-api/README.md))의 **08번** — `getComputedStyle` 이라는 **API 표면**은 그쪽이 정본이다. 여기서는 **재는 도구**로만 썼다.
- 목록의 **50번 주제**(`meta` 계열) — `charset`·`viewport` 처럼 **`<head>` 의 다른 층**은 그쪽이다.
- 목록의 **53번 주제**(`link rel` 관계 지도) — `canonical`·`alternate hreflang` 처럼 **SEO 쪽 `rel` 토큰 전체 지도**는 그쪽이다. 여기는 **스타일시트와 리소스 힌트**까지.

## 용어 풀이

- **렌더 차단(render-blocking)** — 그 자원이 올 때까지 첫 화면을 안 그리는 것.
- **`rel`(링크 타입)** — 이 링크가 문서와 **어떤 관계**인가를 적는 토큰. 공백으로 여럿 쓸 수 있고 대소문자를 안 가린다.
- **`media`** — 그 스타일시트를 **언제 적용할지** 정하는 미디어 쿼리. 받는지 여부는 안 바꾼다.
- **`preload`** — 「곧 쓸 자원을 미리 받아 두라」는 힌트. **`as` 가 필수**다.
- **`as`** — preload 하는 것이 **무엇인지**(style·script·font·image…) 말해 주는 속성. 우선순위와 CSP 판정에 쓰인다.
- **`modulepreload`** — 자바스크립트 **모듈**을 미리 받아 모듈 맵에 올려 두는 힌트.
- **`preconnect`** — 파일이 아니라 **연결**(DNS·TCP·TLS)을 미리 여는 힌트.
- **`dns-prefetch`** — 그중 **DNS 조회만** 미리 하는, 더 가벼운 힌트.
- **`document.styleSheets`** — 문서에 **담긴** 스타일시트 목록. 담겼다는 것과 먹는다는 것은 다르다.
- **`renderBlockingStatus`** — 받아 온 자원마다 **렌더를 막았는지**를 `blocking`/`non-blocking` 으로 답하는 Resource Timing 항목.
- **대체 스타일시트(alternate stylesheet)** — `rel="alternate stylesheet"` + `title` 로 여러 벌을 두고 사용자가 고르게 하던 옛 장치.

## 더 들어가면

- **왜 스타일시트가 스크립트를 막나** — 스크립트가 `getComputedStyle` 을 읽을 수 있기 때문이다. 아직 안 온 스타일시트가 있으면 **그 답이 틀린 값**이 된다. 그래서 브라우저는 **스타일시트를 기다린 뒤에** 스크립트를 돌린다. (1) 의 500ms 가 정확히 그 기다림이다.
- **왜 `media` 가 안 맞아도 받나** — 창을 줄이거나 인쇄를 누르면 **그 순간 조건이 참**이 될 수 있다. 그때 가서 받으면 **화면이 한 번 깜빡인다.** 받아 두되 막지 않는 것이 타협점이다.
- **왜 `as` 를 필수로 했나** — 우선순위·`Accept` 헤더·CSP 판정이 전부 **자원 종류에 달려 있다.** 종류를 모르면 브라우저가 **무엇으로 받아야 할지 못 정한다** — 그래서 아예 안 받는다.
- **`blocking="render"` 속성** — 최근 명세는 `<link>`·`<script>`·`<style>` 에 **명시적으로 렌더 차단을 선언하는** `blocking` 속성을 두었다. 이 배치에서는 **던지지 않았다**(다음 배치의 자리).
