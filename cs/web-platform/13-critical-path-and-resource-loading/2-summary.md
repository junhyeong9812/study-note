# web-platform/13-critical-path-and-resource-loading — 크리티컬 렌더링 패스, 렌더·파서 차단, preload 스캐너, 리소스 힌트 — 정리 (힌트)

## 해결하는 문제

브라우저는 HTML을 받자마자 그리지 못한다. 그리기 전에 꼭 있어야 하는 자원이 있고, 그 자원을 늦게 알게 되면 화면이 통째로 늦어진다.

```text
  <head>에 1초 걸리는 CSS 하나
  0ms   HTML 도착 ─────────────────────────── 1072ms 첫 페인트(FCP)
        └ 본문·이미지는 20ms에 이미 받았지만, CSS가 올 때까지 빈 화면
```

- 해법: "첫 화면에 꼭 필요한 자원"을 줄이고, 필요한 자원은 빨리 발견해서 먼저 받게 한다.
  - *크리티컬 렌더링 패스(critical rendering path)*: 첫 렌더 전에 브라우저가 거치는 단계의 연쇄 — HTML 파싱, CSS 받아 CSSOM 만들기, 차단 스크립트 실행, 레이아웃, 페인트(web.dev learn/performance).
  - *렌더 차단(render-blocking)*: 그 자원이 처리될 때까지 페인트를 미룬다. `<head>`의 스타일시트가 기본이다.
  - *파서 차단(parser-blocking)*: 그 자원이 처리될 때까지 HTML 파싱을 멈춘다. `async`·`defer` 없는 `<script src>`가 기본이다.

쉬운 예: 이삿짐 차.
- 냉장고(CSS)가 안 오면 주방을 못 쓴다 — 다른 짐이 다 와도 "입주"를 못 한다(렌더 차단).
- 짐 목록을 앞에서부터 읽다가 "이 상자는 열어 봐야 다음 목록을 안다"(동기 스크립트)면 목록 읽기를 멈춘다(파서 차단).
- 똑똑한 기사는 멈춘 사이에도 목록을 미리 훑어 큰 짐을 먼저 부른다(preload 스캐너).

똑같은 구조다.\
"무엇이 무엇을 기다리나"의 의존 그래프에서 가장 긴 사슬이 첫 화면 시각을 정한다.

실무 예:
- 태그 매니저·A/B 테스트 스크립트를 `<head>`에 동기로 넣었더니 LCP가 1초 늘었다.
- 히어로 이미지가 CSS `background-image`라서 CSS를 받은 뒤에야 요청된다.
- "빠르게 하려고" preload를 열 개 넣었더니 LCP가 오히려 나빠졌다.

## 동작·원리

### 1. 차단의 두 종류

```text
  HTML 파서 ──► <link rel=stylesheet> ──► (파싱 계속, 페인트는 대기)          ← 렌더 차단
           ──► <script src>          ──► 파싱 멈춤 → 받기 → 실행 → 파싱 재개  ← 파서 차단 (+렌더 차단)
           ──► <script defer src>    ──► 파싱 계속, 병렬로 받기 → 파싱 끝나면 문서 순서대로 실행
           ──► <script async src>    ──► 파싱 계속, 병렬로 받기 → 도착 즉시 실행(파싱을 잠깐 끊음)
           ──► <script type=module>  ──► defer처럼 동작(defer 속성은 효과 없음), async면 async처럼
```

- HTML 표준 "The script element": `async`가 있으면 받으면서 파싱하고 준비되는 대로 실행, `defer`만 있으면 받으면서 파싱하고 파싱이 끝나면 실행, 둘 다 없으면 받기·실행이 끝날 때까지 파싱을 막는다. 모듈 스크립트는 `async`가 없으면 파싱이 끝난 뒤 실행된다.
- 스타일시트는 스크립트도 막는다: 파서가 넣은 동기 클래식 스크립트는 문서에 "스크립트를 막는 스타일시트(style sheet that is blocking scripts)"가 있으면 그것이 끝날 때까지 실행을 기다린다. 인라인 스크립트는 HTML 표준 "prepare the script element"에서, 외부 스크립트는 파서의 `</script>` 처리("spin the event loop until the parser's Document has no style sheet that is blocking scripts…")에서 기다린다. 스크립트가 `getComputedStyle` 같은 값을 읽을 수 있기 때문이다.
- 렌더 차단이 아닌 것: 이미지, 폰트(15번), `media`가 맞지 않는 스타일시트(`media=print`). 반대로 `blocking="render"` 속성으로 `<script>`·`<style>`, 그리고 `rel=stylesheet`·`rel=expect`인 `<link>`를 명시적으로 렌더 차단으로 만들 수도 있다(HTML 표준은 `<link>`의 `blocking`을 이 두 관계에만 허용한다).

### 2. preload 스캐너 — 막혀 있는 동안 앞을 훑는다

```text
  주 파서:     [<head> ... <script src=a.js>]  ⏸ (a.js 1초 대기) ........ [<body> <img src=hero.jpg> ...]
  preload 스캐너:             └──── 앞쪽 마크업을 미리 훑음 ─► hero.jpg 요청 (20ms)
```

- *preload 스캐너*: 원시 HTML 마크업을 훑어 자원을 미리 요청하는 보조 파서(web.dev "Don't fight the browser preload scanner").
- 마크업만 본다. 그래서 다음은 못 본다.
  - JS가 넣는 `<img>`·`<script>`(DOM API로 만든 외부 스크립트는 기본이 async. `document.write()`로 쓴 `<script>`는 파서가 넣은 것이라 이 기본값이 아니다).
  - `data-src`로 바꿔 둔 지연 로딩 이미지.
  - CSS 안의 `background-image`·`@font-face`(CSS 파일을 받아 파싱해야 보인다).
  - 클라이언트 렌더링(CSR)으로 JS가 만드는 마크업 전체.

### 3. 리소스 힌트와 우선순위

| 힌트 | 하는 일 | 주의 |
|---|---|---|
| `<link rel=preconnect href=…>` | DNS·TCP·TLS 연결을 미리 연다 | 폰트 같은 CORS 자원은 `crossorigin`을 붙여야 그 연결을 재사용한다 |
| `<link rel=dns-prefetch>` | DNS 조회만 미리 | preconnect보다 싸다. 출처가 많을 때 |
| `<link rel=preload as=…>` | 지금 페이지에 필요한 자원을 일찍 요청 | `as` 필수(HTML 표준: 없거나 틀리면 목적지가 없어 preload 요청 자체를 하지 않는다). CORS 자원은 `crossorigin`(빠지면 이중 다운로드 — 장애 5) |
| `<link rel=prefetch>` | **다음 탐색**에 쓸 자원을 낮은 우선순위로 | 확신이 있을 때만, `Save-Data` 존중 |
| `<link rel=modulepreload>` | 모듈 스크립트를 미리 받아 파싱까지 | 모듈 그래프(09번) |
| `fetchpriority=high/low/auto` | `<img>`·`<link>`·`<script>`의 우선순위 조정 | Chrome 102+, Firefox 132+, Safari 17.2+(web.dev Fetch Priority) |

- Chrome의 이미지 기본 우선순위(web.dev "Fetch Priority"): 처음은 Low. 레이아웃 뒤 뷰포트 안 이미지는 High로 올린다. Chrome 117부터 처음 5개의 큰 이미지는 Medium으로 시작한다. `async`·`defer` 스크립트는 Low.
- *우선순위*는 "요청을 언제·어느 순서로 보내고 대역폭을 어떻게 나누나"의 힌트다. HTTP/1.1에서는 한 호스트에 동시 연결이 제한된다 — Chromium `net/socket/client_socket_pool_manager.cc`의 `g_max_sockets_per_group`가 일반 풀 6이다. 이미 6개가 차 있으면 높은 우선순위 요청도 빈 연결을 기다린다(아래 실험 B). HTTP/2는 연결 하나에 여러 스트림을 섞는다([network/36](../../network/36-http2-multiplexing/2-summary.md)) — 이 노트는 HTTP/2 환경을 측정하지 않았다.

### 실험 A: 차단 자원이 FCP·LCP에 주는 영향, preload 스캐너, 우선순위

조건: 로컬 서버가 800×400 JPEG(약 125KB)를 200ms 늦게 준다. `<head>`에 1초 늦는 CSS 또는 JS를 넣은 변형을 각 3회 로드. "이미지 요청 도착"은 서버가 HTML 요청을 받은 시각부터 이미지 요청을 받은 시각까지다.

```js
// exp13_critical_path.js 핵심 (scratchpad/wp/08/)
const V = {
  base: page(''),
  'css-1s': page('<link rel=stylesheet href="/s.css?delay=1000">'),
  'css-1s-print': page('<link rel=stylesheet href="/s.css?delay=1000" media=print>'),
  'sync-js-1s': page('<script src="/a.js?delay=1000"></script>'),
  'defer-js-1s': page('<script defer src="/a.js?delay=1000"></script>'),
  'async-js-1s': page('<script async src="/a.js?delay=1000"></script>'),
  'sync-js-1s+js-img': page('<script src="/a.js?delay=1000"></script>', '<h1>오늘의 특가</h1>',
     `<script>const i=new Image(800,400);i.src='/hero.jpg';document.body.append(i)</script>`),
  'css-bg': page('<link rel=stylesheet href="/bg.css?delay=300">', '<h1>…</h1><div class=hero …></div>'),        // .hero{background:url(/hero.jpg)}
  'css-bg+preload': page('<link rel=preload as=image href="/hero.jpg" fetchpriority=high><link rel=stylesheet href="/bg.css?delay=300">', …),
};
```

(실험, headless Chrome 151.0.7922.173, 스로틀 없음, 뷰포트 1000×700, 2026-10-04 — 변형당 3회의 범위, 2회 실행 중 2회차. 사실 점검 재실행에서도 순서·크기는 같았고, 예를 들어 `css-1s` FCP 1068~1076, `sync-js-1s+js-img` 이미지 요청 1024~1029, `css-bg+preload` FCP=LCP 372~448)

```text
base               FCP 52~92      LCP 264~272    이미지 요청 도착(문서 기준 ms) 20~26
css-1s             FCP 1072~1080  LCP 1072~1080  이미지 요청 도착(문서 기준 ms) 20~24
css-1s-print       FCP 60~76      LCP 264~292    이미지 요청 도착(문서 기준 ms) 17~32
sync-js-1s         FCP 1084~1092  LCP 1084~1092  이미지 요청 도착(문서 기준 ms) 24~29
defer-js-1s        FCP 60~76      LCP 264~268    이미지 요청 도착(문서 기준 ms) 19~25
async-js-1s        FCP 48~56      LCP 260~260    이미지 요청 도착(문서 기준 ms) 16~17
sync-js-1s+js-img  FCP 1048~1060  LCP 1260~1272  이미지 요청 도착(문서 기준 ms) 1026~1030
css-bg             FCP 352~368    LCP 560~576    이미지 요청 도착(문서 기준 ms) 328~329
css-bg+preload     FCP 376~376    LCP 376~376    이미지 요청 도착(문서 기준 ms) 17~21
```

관찰과 해석
- `<head>`의 1초 CSS·동기 JS는 FCP와 LCP를 둘 다 1초 넘게 민다. 이미지 자체는 20ms대에 이미 요청됐다 — **받기가 아니라 그리기가 막혔다.**
- `media=print` CSS, `defer`·`async` JS는 기준선과 같다. 같은 1초 자원이라도 차단 여부가 결과를 가른다.
- `sync-js-1s`에서 이미지 요청이 20ms대인 것은 preload 스캐너 덕이다. 파서는 1초 멈췄지만 스캐너가 뒤의 `<img>`를 먼저 봤다.
- 같은 이미지를 JS로 넣으면(`+js-img`) 요청이 1026ms로 밀리고 LCP는 1260ms다. 스캐너가 못 본 자원은 "자원 로드 지연" 조각이 그대로 늘어난다(08번 LCP 네 조각).
- CSS 배경 이미지는 CSS(300ms)를 받은 뒤에야 요청된다(328ms) → LCP 560ms. `preload`로 알려 주면 18ms에 요청되어, CSS가 오는 순간 이미지도 이미 있어 FCP = LCP = 376ms.

(같은 실험, 우선순위 페이지 — CDP `Network.requestWillBeSent.initialPriority`와 `Network.resourceChangedPriority`)

```text
우선순위 (초기 → 최종)
  /prio                        VeryHigh → VeryHigh
  /s.css                       VeryHigh → VeryHigh
  /f.woff2                     High → High
  /a.js?n=sync                 High → High
  /a.js?n=defer                Low → Low
  /a.js?n=async                Low → Low
  /hero.jpg?n=inview           Medium → High
  /hero.jpg?n=inview-high      High → High
  /hero.jpg?n=below            Medium → Medium
콘솔: warning: The resource http://127.0.0.1:38495/f.woff2 was preloaded using link preload but not used within a few seconds from the window's load event. Please make sure it has an appropriate `as` value and it is preloaded intentionally.
```

- 문서·CSS = VeryHigh, 동기 JS = High, `defer`·`async` = Low — web.dev 설명과 같다.
- 뷰포트 안 이미지는 Medium으로 시작해 레이아웃 뒤 High로 올라갔다. `fetchpriority=high`는 처음부터 High다. 3000px 아래 이미지는 Medium에 머물렀다(처음 5개의 큰 이미지 규칙). `loading=lazy` 이미지는 요청 자체가 없었다.
- 쓰지 않은 preload는 load 몇 초 뒤 콘솔 경고를 남긴다 — 남발을 찾는 단서다.

### 실험 B: preload 남발 — LCP 이미지가 대역폭을 빼앗긴다

조건: 히어로 `<img>`(1600w JPEG 38KB) 하나. 변형 ② `<head>`에 첫 화면에 안 쓰는 3840w JPEG(154KB) 5장 preload, ③ ②에 히어로 `fetchpriority=high`. CPU 4×, RTT 150ms, 1.6Mbps, 각 5회.

```js
// exp13_preload_overuse.js 핵심
const pre5 = [1, 2, 3, 4, 5].map(i => `<link rel=preload as=image href="/big.jpg?p${i}">`).join('');
```

(실험, headless Chrome 151.0.7922.173, 뷰포트 412×823, HTTP/1.1 로컬 서버, 2026-10-04)

```text
browser 151.0.7922.173  hero 38KB  preload 대상 1장 154KB
  /none           LCP 624~640 ms
  /preload5       LCP 1528~1564 ms
  /preload5+high  LCP 1532~1592 ms
```

- 쓰지도 않을 preload 5장 때문에 LCP가 0.63초 → 1.55초로 나빠졌다.
- 히어로에 `fetchpriority=high`를 붙여도 나아지지 않았다.
- 사실 점검 재실행에서 우선순위와 서버 도착 시각을 같이 찍었다. preload 5장은 모두 **Low**로 시작했다(`as=image` preload는 이미지 우선순위를 따른다 — web.dev Fetch Priority). 그런데도 히어로와 거의 같은 때(문서 기준 187~248ms) 서버에 도착했다. 히어로는 그 사이 세 번째로 도착했다.
- 해석: 요청 6개가 HTTP/1.1 연결 6개(Chromium 상한)를 하나씩 차지하고 1.6Mbps를 나눠 받는다. HTTP/1.1에는 한 연결 안의 우선순위가 없으므로, 이미 나간 요청의 바이트 배분은 우선순위로 되돌릴 수 없다(HTTP/2 우선순위 동작은 측정하지 않음).

## 쓰이는 자료구조·알고리즘

- **자원 의존 그래프와 임계 경로**: 정점 = 자원, 간선 = "A를 처리해야 B를 발견·실행할 수 있다". 첫 렌더 시각 ≈ 이 DAG에서 가장 긴 경로(가중치 = 왕복 + 전송 + 처리)의 길이다.
  ```text
  HTML ──► app.css ──► @font-face(폰트) ──► 텍스트 페인트       (3단 사슬 — font-display: block·auto처럼 글자가 폰트를 기다릴 때. swap이면 대체 폰트로 먼저 그린다, 15번)
  HTML ──► app.js  ──► JS가 넣는 <img>  ──► LCP               (3단 사슬)
  HTML ──► <img> (preload 스캐너)        ──► LCP               (1단)
  ```
  - 최장 경로는 위상 정렬 순서로 한 번 훑어 구한다(O(V+E)). 그래프 표현은 [data-structure/08 그래프](../../data-structure/08-graph/2-summary.md), 위상 정렬은 [algorithm/12 DFS](../../algorithm/12-dfs/2-summary.md).
  - preload는 "사슬 중간의 간선을 끊어 HTML에 직접 붙이는 것"이다. 사슬 길이가 줄어든다.
- **우선순위 큐**: 브라우저는 요청을 우선순위(VeryHigh~VeryLow)별로 대기시키고 연결이 비면 높은 것부터 보낸다. 개념은 [data-structure/07 힙](../../data-structure/07-heap/2-summary.md). 단 연결 수 상한(HTTP/1.1 6개)과 이미 나간 요청은 큐로 되돌릴 수 없다는 점이 실험 B의 결과를 만든다.

## 적용 — 풀어나가는 법

### 1. 진단 — 사슬을 그린다

```text
  ① DevTools Network: Priority 열·Initiator 열을 켠다 → 누가 누구를 불렀나(사슬)
  ② Performance 패널: 첫 페인트 전 "Parse HTML"이 끊긴 자리, 렌더 차단 자원 표시
  ③ LCP 요소의 요청 시작 시각 vs TTFB → "자원 로드 지연" 조각이 크면 발견이 늦은 것
  ④ Lighthouse 진단: "렌더 차단 리소스 제거", "LCP 이미지 미리 로드" 류 항목
```

### 2. 처방 순서

```html
<head>
  <!-- 1) 첫 화면에 필요한 아주 작은 CSS는 인라인, 나머지는 렌더 차단을 풀거나 나눈다 -->
  <style>/* critical CSS */</style>
  <link rel="stylesheet" href="/app.css">                       <!-- 필요한 CSS는 그대로(차단은 정상 비용) -->
  <link rel="stylesheet" href="/print.css" media="print">       <!-- 맞지 않는 media → 비차단 -->

  <!-- 2) 늦게 발견되는 LCP 자원만 preload (CSS 배경·JS 주입 이미지) -->
  <link rel="preload" as="image" href="/hero.avif" fetchpriority="high">

  <!-- 3) 다른 출처의 핵심 자원은 연결을 미리 -->
  <link rel="preconnect" href="https://fonts.example.com" crossorigin>

  <!-- 4) 스크립트는 defer(순서 필요) 또는 async(독립 — 분석·광고), 모듈은 기본이 defer -->
  <script defer src="/app.js"></script>
  <script async src="/analytics.js"></script>
</head>
<body>
  <!-- 5) LCP 이미지는 마크업에 그대로, lazy 금지, 필요하면 fetchpriority=high -->
  <img src="/hero.avif" width="1600" height="900" fetchpriority="high" alt="…">
</body>
```

- `defer`는 문서 순서대로 실행되므로 의존 관계가 있는 앱 코드에 맞다. `async`는 도착 순서로 실행되므로 서로 독립인 스크립트에만 쓴다. 문법 세부는 [html/08 script 로딩](../../../languages/html/syntax/08-script-loading/2-summary.md), [html/09 스타일시트와 리소스 힌트](../../../languages/html/syntax/09-stylesheets-and-resource-hints/2-summary.md).
- preload는 "늦게 발견되는데 첫 화면에 필요한 것" 몇 개에만 쓴다. 실험 B처럼 남발하면 진짜 중요한 자원의 대역폭을 뺏는다. 쓰지 않은 preload는 콘솔 경고로 찾는다.
- 다른 출처는 연결 수립(DNS·TCP·TLS) 비용이 붙는다([network/35 연결 관리](../../network/35-http-connection-management/2-summary.md)). 핵심 서드파티는 preconnect, 덜 중요한 것은 dns-prefetch.

### 3. 랩에서 확인하는 코드

```js
// 자원별 우선순위 변화 수집 (Playwright + CDP)
const cdp = await page.context().newCDPSession(page);
await cdp.send('Network.enable');
cdp.on('Network.requestWillBeSent', e => console.log(e.request.url, e.request.initialPriority));
cdp.on('Network.resourceChangedPriority', e => console.log(e.requestId, '→', e.newPriority));
```

## 장애 시나리오와 대처

### 1. `<head>`의 동기 스크립트·큰 CSS → FCP·LCP 지연 (⚠)

- 현상: 서버 응답은 빠른데 흰 화면이 1초 넘게 간다.
- 보이는 형태: 필드 LCP p75가 2.5s를 넘어 "개선 필요"(4s를 넘으면 "나쁨"). Performance 패널에서 첫 페인트 전 긴 대기, Network에서 첫 페인트 직전 끝나는 CSS·JS. 실험: 1초 CSS·JS → FCP 1072~1092ms.
- 원인: 렌더 차단 CSS·파서 차단 JS가 크리티컬 패스에 올라 있다. 태그 매니저·A/B 테스트 스크립트가 흔한 범인이다.
- 대처: 스크립트는 `defer`/`async`, 첫 화면 CSS만 인라인하고 나머지는 나누거나 `media`로 비차단화, 서드파티는 비동기 로더로.

### 2. preload 남발 → LCP가 오히려 나빠짐 (⚠)

- 현상: 성능 개선이라며 preload를 여러 개 넣은 배포 뒤 LCP가 늘었다.
- 보이는 형태: 콘솔 "was preloaded using link preload but not used within a few seconds". 실험: 쓰지 않는 preload 5장 → LCP 0.63s → 1.55s, `fetchpriority=high`로도 회복 안 됨.
- 원인: preload는 `<head>`에서 일찍 발견되어 바로 나간다(우선순위는 `as`의 종류를 따른다 — 이미지 preload는 실험에서 Low). 첫 화면에 안 쓰는 큰 자원이 연결·대역폭을 차지하면 LCP 자원이 대역폭을 나눠 받는다.
- 대처: preload는 LCP 자원·첫 화면 폰트처럼 늦게 발견되는 핵심 자원만. 나머지는 지우거나 `prefetch`(다음 탐색용)로 바꾼다.

### 3. 첫 화면 LCP 이미지에 `loading=lazy` → LCP 지연 (⚠)

- 현상: 이미지 전부에 `loading="lazy"`를 일괄 적용한 뒤 LCP가 나빠졌다.
- 보이는 형태: LCP 요소의 요청 시작이 레이아웃 뒤로 밀리고, 우선순위가 Low로 시작한다(14번 실험: Low → High, LCP 1.47s → 5.4s).
- 원인: lazy 이미지는 레이아웃을 해서 뷰포트 근처인지 확인한 뒤에야 요청된다. 그 사이 다른 자원이 연결을 차지한다. web.dev는 LCP 이미지 lazy 로딩이 "불필요한 자원 로드 지연"을 만든다고 한다.
- 대처: 첫 화면 이미지는 eager(기본값) + 필요하면 `fetchpriority=high`. lazy는 첫 화면 아래에만([14번](../14-image-optimization/2-summary.md)).

### 4. LCP 이미지가 CSS 배경·JS 렌더 → 발견 지연

- 현상: 히어로가 다른 이미지보다 늦게 뜬다.
- 보이는 형태: Network Initiator가 `.css` 또는 `.js`. 실험: CSS 배경 → 이미지 요청 328ms, LCP 560ms.
- 원인: preload 스캐너는 마크업만 본다. CSS·JS 안의 자원은 그 파일을 받아 처리한 뒤에 발견된다.
- 대처: 히어로를 `<img>`로 마크업에 두거나, `<link rel=preload as=image fetchpriority=high>`(실험: 18ms 요청, LCP 376ms). SSR로 마크업을 서버에서 만든다([10번](../10-rendering-strategies/2-summary.md)).

### 5. 폰트 preload에 `crossorigin` 누락 → 이중 다운로드

- 현상: 폰트가 두 번 받아진다.
- 보이는 형태: 콘솔 "A preload for '…' is found, but is not used because the request credentials mode does not match". Network에 같은 woff2 두 줄(15번 실험: 37ms·363ms).
- 원인: 폰트는 CORS 모드(익명)로 요청된다. `crossorigin` 없는 preload는 다른 자격 증명 모드라 캐시 항목이 맞지 않는다.
- 대처: 폰트 preload·preconnect에 `crossorigin`을 붙인다.

## 핵심 문장

- 첫 화면 시각은 "무엇이 무엇을 기다리나" 의존 사슬 중 가장 긴 것이 정한다.
- `<head>`의 CSS는 렌더를, 동기 스크립트는 파싱과 렌더를 막는다. `defer`·`async`·`media`로 차단을 풀 수 있다.
- preload 스캐너는 막힌 동안 마크업을 미리 훑어 자원을 요청한다. CSS·JS 안의 자원은 못 본다.
- preload는 늦게 발견되는 핵심 자원에만 쓴다. 남발하면 LCP 자원의 대역폭·연결을 빼앗아 LCP가 나빠진다.
- Chrome은 이미지를 Low/Medium으로 시작해 뷰포트 안이면 High로 올린다. `fetchpriority`로 처음부터 조정할 수 있다.

## 관련 주제·근거

- 선행
  - [02 렌더링 파이프라인](../02-rendering-pipeline/2-summary.md) — 파싱·스타일·레이아웃·페인트
  - [08 Web Vitals](../08-web-performance-vitals/2-summary.md) — FCP·LCP, LCP 네 조각
  - [network/35 HTTP 연결 관리](../../network/35-http-connection-management/2-summary.md) — 연결 수립 비용, 연결 재사용
- 후속·연결
  - [14 이미지 최적화](../14-image-optimization/2-summary.md), [15 웹 폰트 로딩](../15-web-font-loading/2-summary.md)
  - [09 모듈과 번들링](../09-js-modules-and-bundling/2-summary.md) — 코드 분할, modulepreload
  - [10 렌더링 전략](../10-rendering-strategies/2-summary.md) — CSR이 preload 스캐너를 무력화하는 이유
  - [network/36 HTTP/2 다중화](../../network/36-http2-multiplexing/2-summary.md), [network/34 HTTP 캐시](../../network/34-http-caching/2-summary.md), [network/47 CDN과 엣지](../../network/47-cdn-and-edge/2-summary.md)
  - [data-structure/08 그래프](../../data-structure/08-graph/2-summary.md), [algorithm/12 DFS(위상 정렬)](../../algorithm/12-dfs/2-summary.md), [data-structure/07 힙](../../data-structure/07-heap/2-summary.md)
- 문법: [html/08 script 로딩](../../../languages/html/syntax/08-script-loading/2-summary.md), [html/09 스타일시트와 리소스 힌트](../../../languages/html/syntax/09-stylesheets-and-resource-hints/2-summary.md)
- 근거
  - web.dev "Understand the critical path" https://web.dev/learn/performance/understanding-the-critical-path — 정의, 렌더·파서 차단, `blocking=render`, `media=print`, preload 스캐너
  - web.dev "Assist the browser with resource hints" https://web.dev/learn/performance/resource-hints — preconnect·crossorigin, dns-prefetch, preload `as`, prefetch, fetchpriority
  - web.dev "Don't fight the browser preload scanner" https://web.dev/articles/preload-scanner — 스캐너가 못 보는 패턴
  - web.dev "Optimize resource loading with the Fetch Priority API" https://web.dev/articles/fetch-priority — 이미지 Low→High, Chrome 117 처음 5개 Medium, async/defer Low, 지원 판, Google Flights 2.6s→1.9s
  - web.dev "Optimize LCP" https://web.dev/articles/optimize-lcp — LCP 이미지 lazy 금지, 늦게 발견되는 자원 preload
  - HTML 표준 "The script element" https://html.spec.whatwg.org/multipage/scripting.html — async/defer/module 동작, "style sheet that is blocking scripts"
  - HTML 표준 "Link type preload" https://html.spec.whatwg.org/multipage/links.html#link-type-preload — `as`가 preload 목적지가 아니면 "If destination is null, then return" · "The link element" https://html.spec.whatwg.org/multipage/semantics.html#the-link-element — `blocking`은 `stylesheet`·`expect`에만
  - Chromium `net/socket/client_socket_pool_manager.cc` — `g_max_sockets_per_group` 일반 6 · WebSocket 255
- 실험 목록 (headless Chrome 151.0.7922.173, Node 20.19.6 + playwright-core 1.62.1 + sharp 0.33.5, 127.0.0.1 HTTP/1.1 로컬 서버, 2026-10-04)
  - 13-A 차단 변형별 FCP·LCP·이미지 요청 시각 + 우선순위·미사용 preload 경고: `scratchpad/wp/08/exp13_critical_path.js` — 변형당 3회 × 2회 실행, 출력 `out13.txt`
  - 13-B preload 남발: `scratchpad/wp/08/exp13_preload_overuse.js` — 입력 사진 `/usr/share/backgrounds/Clouds_by_Tibor_Mokanszki.jpg`, 변형당 5회, 출력 `out13b.txt`
