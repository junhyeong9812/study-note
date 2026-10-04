# web-platform/10-rendering-strategies — CSR·SSR·SSG·스트리밍·하이드레이션: HTML을 누가 언제 만드나 — 정리 (힌트)

## 해결하는 문제

웹 페이지의 HTML은 누군가 만들어야 한다. 만드는 **장소**(서버 또는 브라우저)와 **시점**(빌드 때, 요청 때, 브라우저에서)이 다르면 사용자가 겪는 시간이 크게 달라진다.

```text
  같은 상품 목록 페이지, 만드는 방식만 다르다
  CSR   빈 HTML ──> JS 다운로드 ──> JS가 데이터 요청 ──> JS가 DOM 생성 ──> 보임 = 반응
  SSR   서버가 데이터 조회 + HTML 생성 ──> 보임 ──> JS 다운로드 ──> 하이드레이션 ──> 반응
  SSG   (빌드 때 이미 HTML) ──> 보임 ──> JS 다운로드 ──> 하이드레이션 ──> 반응
```

쉬운 예: 가구 배송이다.
- CSR = 부품과 설명서만 보낸다. 받은 사람이 조립을 마칠 때까지 쓸 수 없다.
- SSR = 주문이 들어오면 공장에서 조립해 보낸다. 받자마자 보인다. 대신 공장(서버)이 매번 일한다.
- SSG = 미리 조립해 창고(CDN)에 쌓아 둔다. 가장 빨리 오지만, 주문마다 다른 가구는 미리 만들 수 없다.
- 하이드레이션 = 조립된 가구에 전원선(이벤트 리스너)을 나중에 꽂는 일이다. 꽂기 전에는 JS로 붙이는 동작(React `onClick` 등)이 작동하지 않는다. `href`가 있는 링크 이동 같은 브라우저 기본 동작은 그 전에도 된다.

똑같은 구조다. "보이는 시점"과 "반응하는 시점"이 갈라지고, 그 사이를 무엇이 채우는지가 방식마다 다르다.

실무 예:
- 블로그·문서 사이트: 같은 HTML을 누구에게나 준다 → SSG가 맞다.
- 상품 상세: 재고·가격이 자주 바뀐다 → SSR이나 짧은 주기로 다시 만드는 정적 렌더.
- 로그인 뒤 대시보드: 사용자마다 다르고 검색 엔진에 노출할 필요가 적다 → CSR도 선택지다.
- 사용자별 SSR 페이지를 CDN이 URL만 키로 캐시하면 다른 사람의 화면이 보인다(장애 2).

## 동작·원리

### 1. 용어 — web.dev "Rendering on the Web"(Osmani·Miller, 2019 작성, 2026-01-05 갱신)의 정의

- *SSR(Server-Side Rendering)*: 서버에서 앱을 렌더링해 JS 대신 HTML을 보내는 것.
- *CSR(Client-Side Rendering)*: 브라우저에서 JS로 DOM을 고쳐 앱을 렌더링하는 것.
- *정적 렌더링(Static Rendering, SSG)*: 빌드 때 URL마다 HTML 파일을 미리 만든다. CDN에 올려 엣지에서 캐시할 수 있다.
- *프리렌더링(Prerendering)*: 클라이언트 앱을 빌드 때 실행해 초기 상태를 정적 HTML로 떠 두는 것.
- *하이드레이션(Hydration)*: 서버가 만든 HTML에 클라이언트 스크립트를 실행해 앱 상태와 상호작용을 붙이는 것.
- *스트리밍 SSR*: HTML을 여러 조각으로 보내, 브라우저가 받는 대로 그리게 하는 것.
- *TTFB*: 요청부터 응답 첫 바이트까지. *FCP*: 첫 콘텐츠가 그려진 시각. *TBT*: FCP 뒤 메인 스레드가 입력에 반응하지 못한 시간의 합(긴 태스크마다 50ms 초과분을 더한다 — web.dev "TBT").
- *INP*: 사용자 입력에 대한 반응성 지표(08번 노트에서 다룬다).

### 2. 네 방식의 시간축

```text
  시간 →
  CSR     [HTML 1KB]─[JS 195KB 다운로드·실행]─[fetch /api/items]─[렌더]─ FCP = 반응 시작
  SSR     [서버: DB 조회 + renderToString]─[HTML 198KB]─ FCP ··· [JS]─[하이드레이션]─ 반응 시작
  SSG     [HTML 198KB (빌드 때 생성)]─ FCP ··· [JS]─[하이드레이션]─ 반응 시작
  스트리밍 [셸 HTML]─ FCP ─[데이터 도착 → 나머지 HTML 조각]··· [JS]─[하이드레이션]─ 반응 시작
                         ↑
                  "···" 구간 = 보이지만 반응하지 않는 구간(19번 노트의 주제)
```

- CSR은 그리기 전에 JS와 데이터를 **차례로** 기다린다. 대신 그려지면 곧바로 반응한다.
- SSR·SSG는 HTML이 도착하면 바로 보인다. 그러나 반응하려면 같은 JS를 받아 하이드레이션해야 한다.
- SSR과 SSG의 차이는 **서버에서 HTML을 언제 만드나**다. SSR은 요청마다, SSG는 빌드 때 한 번이다. 그래서 SSR은 서버의 데이터 조회 시간이 TTFB에 그대로 더해진다.
- 스트리밍은 느린 데이터를 기다리지 않고 셸을 먼저 보낸다.
  - *셸(shell)*: `<Suspense>` 경계 밖에 있는 부분. 먼저 렌더링해 바로 보낸다(react.dev `renderToPipeableStream`).

### 3. 하이드레이션 — 서버 HTML과 클라이언트 트리를 맞춘다

```text
  서버 HTML(DOM)                      클라이언트가 다시 만든 컴포넌트 트리
  <main>                              <App>
    <h1>상품 목록</h1>      ←─ 대조 ─→    <h1>상품 목록</h1>
    <button>클릭 0</button> ←─ 대조 ─→    <button onClick=…>      ← 여기서 리스너를 붙인다
    <ul>…2000개…</ul>       ←─ 대조 ─→    <Items …/>
  결과가 같으면: DOM은 그대로 두고 리스너·상태만 연결
  결과가 다르면: hydration mismatch → 텍스트 불일치 등에서는 해당 부분(또는 루트)을 클라이언트에서 다시 만든다(아래 실험).
                속성 불일치는 고쳐진다는 보장이 없다(react.dev hydrateRoot)
```

- 하이드레이션이 되살려야 하는 것(Qwik 문서 "Resumable"의 정리)
  - 이벤트 리스너: 어느 DOM에 어떤 핸들러가 붙나.
  - 컴포넌트 트리: 프레임워크 내부 자료구조.
  - 애플리케이션 상태: 서버에서 가져온 데이터.
- 그래서 하이드레이션은 컴포넌트 코드를 클라이언트에서 **한 번 더 실행**한다. 같은 결과를 내려면 같은 입력 데이터가 필요하다.
  - 그래서 대부분의 SSR 방식은 HTML(결과)과 함께 그 데이터(JSON)도 보낸다(web.dev: "most server-side rendering solutions serialize …"). 필수 절차는 아니고, 핵심은 클라이언트 첫 렌더가 서버와 같은 출력을 내는 것이다. web.dev는 이것을 "UI 설명 + 원천 데이터 + UI 구현 코드를 모두 보낸다"는 중복 문제로 짚는다.
- react.dev `hydrateRoot`: 클라이언트 트리는 "서버와 같은 출력"을 내야 한다. React는 일부 하이드레이션 오류에서 복구하지만, 버그로 고쳐야 한다. 최악이면 이벤트 핸들러가 엉뚱한 요소에 붙는다.

### 4. 스트리밍 SSR — 실제로 오는 바이트

React 19.2.8의 `renderToPipeableStream`이 `<Suspense>` 안의 데이터를 기다리는 동안 보낸 응답(실험, 목록 3개로 줄여 `curl -N`으로 받은 원문 일부):

```text
<main><h1 id="title">상품 목록 — …</h1><button id="btn">클릭 <!-- -->0</button>
<!--$?--><template id="B:0"></template><p>불러오는 중…</p><!--/$--></main>     ← 셸 + 대체 UI, 먼저 도착
  … (DB 300ms 대기) …
<div hidden id="S:0"><ul><li><b>상품 0</b> …</li>…</ul></div>                   ← 나중 조각, 숨긴 채 도착
<script>… $RC=function(a,b){…} … $RC("B:0","S:0")</script>                     ← B:0 자리를 S:0 내용으로 교체
```

- 경계 표시는 HTML 주석이다. `<!--$?-->`는 "아직 대기 중인 경계", `<!--$-->`는 "완료된 경계"다(교체 스크립트가 `g.data="$"`로 바꾼다).
- 이 판의 `$RC`는 교체를 즉시 하지 않는다. 출력된 코드를 보면 `requestAnimationFrame`이나 `setTimeout`으로 미뤄 여러 경계를 모아 적용한다(코드상 직전 공개 뒤 약 300ms, 로드 2.0~2.3초 사이면 2.3초에 맞춤). React 19.2 블로그 "Batching Suspense Boundaries for SSR": 19.2부터 서버 렌더 경계의 공개를 잠깐 모아서 한다. 그 전에는 내용이 오는 즉시 대체 UI를 바꿨다. 페이지 로드가 2.5초(LCP "good" 기준)에 가까워지면 모으기를 멈춘다.
- `onShellReady`는 셸이 준비되면 호출된다. `onAllReady`는 경계까지 전부 끝나면 호출된다. react.dev는 크롤러·정적 생성에 `onAllReady`를 권한다.

### 실험: 같은 페이지를 네 방식으로 — FCP·반응 시작·TBT

환경: headless Chrome 151.0.7922.173, React·react-dom 19.2.8(운영 빌드, esbuild 0.28.2 `--minify`), Node 20.19.6 서버(127.0.0.1), 뷰포트 412×823, 캐시 끔, 압축 없음.
스로틀: CPU 4×(`Emulation.setCPUThrottlingRate`), 네트워크 지연 150ms·내려받기 1638.4kbps·올리기 750kbps(`Network.emulateNetworkConditions`). 상품 2000개, 서버의 DB 조회는 `setTimeout` 300ms로 흉내 냈다.

```jsx
// 서버 핵심(server.jsx 발췌)
const db = () => new Promise(r => setTimeout(() => r(items), 300));
const ssgHtml = head + `<div id="root">${renderToString(<App source={items} />)}</div>` + dataAndScript; // 빌드 때 1회
'/csr'   : head + '<div id="root"></div><script src="/csr.js"></script>'      // csr.js가 /api/items를 fetch 후 createRoot
'/ssr'   : const d = await db(); head + `<div id="root">${renderToString(<App source={d} />)}</div>` + dataAndScript
'/ssg'   : ssgHtml
'/stream': renderToPipeableStream(<App source={db()} />, { onShellReady() { s.pipe(pt); } })  // 셸 먼저, 끝나면 데이터·스크립트
// 측정: head 안의 PerformanceObserver(paint·largest-contentful-paint·longtask),
// 반응 시작 = App의 useEffect가 처음 실행된 performance.now()
```

`(실험, headless Chrome 151, CPU 4×·네트워크 스로틀, 2026-10-04)` 방식마다 5회, 최소~최대(ms):

```text
chrome 151.0.7922.173
csr     TTFB 5~17 | FCP 3652~4380 | LCP 3652~4380 | 반응 시작 3642~4371 | 최장 태스크 811~1517 | TBT 1400~2117 | HTML B 943
ssr     TTFB 339~370 | FCP 632~748 | LCP 632~748 | 반응 시작 3070~3623 | 최장 태스크 390~612 | TBT 373~617 | HTML B 198212
ssg     TTFB 7~8 | FCP 376~536 | LCP 376~536 | 반응 시작 2981~3535 | 최장 태스크 458~620 | TBT 482~641 | HTML B 198212
stream  TTFB 6~9 | FCP 320~372 | LCP 320~372 | 반응 시작 3644~4012 | 최장 태스크 443~569 | TBT 430~582 | HTML B 199232
```

- 주의: 위 표의 `TBT` 칸은 web.dev의 TBT가 아니다. 로드 중 관찰된 **모든** 긴 태스크(FCP 이전 포함)의 50ms 초과분 합이다. web.dev TBT는 FCP 뒤(~TTI) 긴 태스크만 센다.
- 사후 재실행으로 두 값을 나눠 쟀다(같은 코드·조건 5회, FCP에 걸친 태스크는 FCP 뒤 부분만 셈, 끝은 반응 시작 + 300ms까지 — TTI로 자르지 않음).

`(실험, headless Chrome 151, CPU 4×·네트워크 스로틀, 2026-10-04 재실행)` 발췌(ms):

```text
csr     FCP 3452~3540 | 최장 태스크 746~831 | TBT(전체) 1235~1325 | TBT(FCP 뒤) 0~0
ssr     FCP 564~744 | 최장 태스크 383~452 | TBT(전체) 348~447 | TBT(FCP 뒤) 348~447
ssg     FCP 412~488 | 최장 태스크 386~508 | TBT(전체) 344~487 | TBT(FCP 뒤) 344~487
stream  FCP 300~344 | 최장 태스크 392~525 | TBT(전체) 370~500 | TBT(FCP 뒤) 362~496
```

  - CSR은 긴 태스크가 모두 FCP **전**에 끝나 FCP 뒤 TBT가 0이었다. TBT만 보면 CSR이 가장 좋아 보인다. 대신 그 비용은 늦은 FCP·LCP로 나타난다. 지표 하나로 방식을 고르면 안 되는 이유다.
  - SSR·SSG·스트리밍은 하이드레이션 태스크가 FCP 뒤에 있어 두 값이 거의 같다.
- TTFB 칸 주의: 이 환경에서 Navigation Timing의 `responseStart`에는 에뮬레이션 지연 150ms가 나타나지 않았다. 같은 설정에서 하위 자원 `fetch`는 지연 0/150/400ms일 때 8/155/406ms가 걸렸다(별도 확인). 그래서 TTFB 칸은 서버 처리 시간(SSR의 DB 300ms) 비교에만 쓴다.
- 사실 점검 재실행(같은 코드·조건 5회, 다른 작업자의 브라우저가 동시에 돌던 상태): FCP csr 3684~4172 · ssr 612~804 · ssg 376~568 · stream 296~332, 반응 시작 csr 3676~4164 · ssr 2913~3511 · ssg 3033~3425 · stream 3484~3957. 범위가 겹치고 순서가 같았다.

관찰과 해석:
- **보이는 시점**: CSR의 FCP(3.7~4.4초)는 SSR(0.63~0.75초)의 약 5배다. CSR은 JS 195KB를 받고 실행한 뒤에야 데이터를 요청하기 때문이다(직렬 대기).
- **SSR vs SSG**: SSR의 TTFB에 DB 300ms가 그대로 더해졌다(339~370 vs 7~8). FCP도 그만큼 늦다.
- **스트리밍**: 셸을 DB 대기 없이 보내 FCP가 가장 빨랐다(320~372). 다만 이 페이지의 LCP 요소는 셸의 `<h1>`이었다. 목록이 LCP 요소라면 결과가 달라진다.
- **반응 시작**: SSR·SSG·스트리밍은 FCP 뒤에도 한참 보이기만 하고 반응하지 않았다. 범위끼리 빼서 어림하면 SSR 약 2.3~3.0초, SSG 약 2.4~3.2초, 스트리밍 약 3.3~3.7초다. CSR은 FCP와 반응 시작이 거의 같다.
  - 스트리밍의 반응 시작이 SSR보다 늦은 것은 이 실험이 하이드레이션 스크립트를 **데이터 조각 뒤에** 붙였기 때문이다. React의 `bootstrapScripts`로 셸을 먼저 하이드레이션하는 구성에서는 다를 수 있다(19번).
- **문서 크기**: SSR HTML 198KB 중 마크업이 109,251B, 하이드레이션용 JSON이 87,981B였다(`/ssr?size`로 따로 잼). 같은 정보가 두 형태로 간다.
- **긴 태스크**: CSR은 2000개 목록을 처음부터 만드느라 최장 태스크가 0.8~1.5초였다. 하이드레이션은 DOM을 새로 만들지 않아 더 짧았지만(0.39~0.62초) 여전히 50ms를 크게 넘는다.

### 5. 고르는 기준

| 질문 | 예 → 쪽으로 |
|---|---|
| 같은 URL이면 누구에게나 같은 HTML인가? | 예 → SSG(또는 CDN 캐시 + SSR) |
| 데이터가 요청마다 바뀌고 첫 화면이 중요한가? | 예 → SSR, 느린 데이터가 있으면 스트리밍 |
| 검색 노출·링크 미리보기가 필요한가? | 예 → HTML에 내용을 담는 쪽(SSR·SSG)이 안전하다. Google은 JS를 렌더한 뒤에도 색인하지만, JS를 실행하지 못하는 봇도 있다(Google Search Central). 링크 미리보기 수집기의 JS 실행 여부는 수집기마다 다르다 `[?]` |
| 로그인 뒤 앱이고 상호작용이 대부분인가? | 예 → CSR도 선택지(초기 JS 크기 관리가 중요) |
| URL이 수십만 개인가? | 예 → 전부 미리 만들기 어렵다. 요청 때 만들고 캐시 |

- web.dev의 비교: 정적 렌더링은 TTFB가 일관되게 빠르지만 URL마다 파일을 만들어야 한다. SSR은 서버 생성 시간이 TTFB를 늘릴 수 있다. CSR은 앱이 커질수록 JS가 늘어 INP에 영향을 줄 수 있다.
- 한 사이트 안에서도 경로마다 다르게 고를 수 있다. 문서 페이지는 SSG, 계정 페이지는 SSR이나 CSR 식이다.

## 쓰이는 자료구조·알고리즘

- **트리 직렬화 = 깊이 우선 순회**: `renderToString`은 컴포넌트 트리를 전위 순회하며 여는 태그·자식·닫는 태그를 문자열로 이어 붙인다. [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md)
- **두 트리 동시 순회(하이드레이션 매칭)**: 클라이언트 렌더가 트리를 내려가는 동안, 기존 DOM을 가리키는 커서도 같은 순서로 전진하며 노드 종류·텍스트를 대조한다. 어긋나면 mismatch다.
  - 실험 출력의 `클릭 <!-- -->0`처럼 서버는 인접한 텍스트 사이에 빈 주석을 넣는다. 브라우저 파서가 두 텍스트를 한 노드로 합쳐 버리면 클라이언트 트리와 개수가 달라지기 때문으로 보인다 `[?]`.
- **자리 표시자 ID 맵(스트리밍)**: `B:0`(대체 UI 자리) ↔ `S:0`(나중 내용)을 ID로 짝지어 교체한다. 순서에 상관없이 먼저 끝난 경계부터 보낼 수 있다.
- **캐시 키**: SSG·CDN 캐시는 (URL, 일부 헤더)를 키로 쓴다. 사용자별 응답이면 키에 사용자 구분이 없을 때 교차 노출이 난다 — HTTP 캐시 규칙은 [network/34-http-caching](../../network/34-http-caching/2-summary.md), CDN은 [network/47-cdn-and-edge](../../network/47-cdn-and-edge/2-summary.md).
- **청크 전송**: 스트리밍 SSR은 HTTP/1.1이면 `Transfer-Encoding: chunked`로 나뉘어 간다 — [network/40-chunked-and-streaming-responses](../../network/40-chunked-and-streaming-responses/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 순서

1. 페이지를 유형별로 나눈다: 공개·공통(문서·마케팅), 공개·자주 변함(상품), 개인화(계정·장바구니), 앱형(편집기).
2. 유형마다 위 표로 방식을 정한다. 기본값은 "가능하면 정적, 필요할 때만 요청 시 렌더"다.
3. SSR이면 느린 데이터를 찾는다. 첫 화면에 필요 없으면 `<Suspense>`로 감싸 스트리밍한다.
4. 개인화 응답에는 캐시 헤더를 명시한다(`Cache-Control: private` 또는 `no-store`). CDN 설정도 같이 본다.
5. 서버·클라이언트가 같은 출력을 내는지 점검한다. 시간·난수·`window`·로캘에 의존하는 렌더를 찾는다.
6. 랩 측정(이 노트의 실험처럼 스로틀을 건 반복 측정)과 실사용자 측정(RUM, 08번)을 둘 다 본다.

### 2. 코드 — 스트리밍 SSR과 개인화 캐시 헤더(Node, React 19)

```js
import { renderToPipeableStream } from 'react-dom/server';

app.get('/account', async (req, res) => {
  const user = await auth(req);                       // 사용자별 페이지
  res.setHeader('Cache-Control', 'private, no-store'); // 공유 캐시(CDN·프록시)에 저장 금지
  const { pipe } = renderToPipeableStream(<Account user={user} ordersPromise={loadOrders(user.id)} />, {
    bootstrapScripts: ['/client.js'],
    onShellReady() { res.statusCode = 200; res.setHeader('content-type', 'text/html'); pipe(res); },
    onShellError() { res.statusCode = 500; res.end('<p>잠시 후 다시 시도</p>'); },
  });
});
```

- 셸에는 사용자 이름처럼 빠른 데이터만, 주문 목록처럼 느린 데이터는 `<Suspense>` 안에 둔다.
- 서버 모듈의 전역 변수에 요청별 데이터를 넣지 않는다. 한 Node 프로세스가 여러 요청을 동시에 처리하므로 모듈 상태는 요청 사이에서 공유된다.

### 3. 의도된 서버·클라이언트 차이는 두 번 그리기로(react.dev `hydrateRoot`)

```jsx
function LocalTime({ iso }) {
  const [isClient, setIsClient] = useState(false);
  useEffect(() => { setIsClient(true); }, []);       // 하이드레이션이 끝난 뒤에만 true
  return <time dateTime={iso}>{isClient ? new Date(iso).toLocaleString() : iso}</time>;
}
```

- 첫 렌더는 서버와 같은 값(ISO 문자열)을 낸다. 하이드레이션 뒤 브라우저 로캘로 바꾼다.
- 한 단계짜리 피할 수 없는 차이(타임스탬프 등)는 `suppressHydrationWarning`을 쓸 수 있다. react.dev는 이것을 탈출구로만 쓰라고 한다. 경고만 끌 뿐, React는 어긋난 텍스트를 고치지 않는다(서버 값이 남는다).

### 4. 진단

- 페이지 소스 보기(`view-source:`)와 DevTools Elements의 DOM을 비교한다. 소스에 내용이 없으면 CSR이다.
- DevTools Network에서 문서 요청의 Timing 탭: "Waiting for server response"가 길면 SSR 서버 처리(데이터 조회)를 의심한다.
- Performance 패널: FCP 표시 뒤 하이드레이션 스크립트의 긴 태스크가 이어지는지 본다.
- `hydrateRoot`의 `onRecoverableError`로 운영 환경의 불일치를 수집한다. 운영 빌드의 메시지는 `Minified React error #418`처럼 번호만 나온다.

## 장애 시나리오와 대처

### 1. hydration mismatch — 서버와 클라이언트 렌더 결과 불일치 (⚠ 커리큘럼)

- **현상**: 처음 보인 글자가 잠깐 뒤 다른 글자로 바뀐다(깜빡임). 콘솔에 하이드레이션 오류가 뜬다.
- **보이는 형태**: 개발 빌드 `Hydration failed because the server rendered text didn't match the client. As a result this tree will be regenerated on the client.` / 운영 빌드 `Minified React error #418`.
- **원인**: 렌더 중에 `typeof window`, `Date.now()`, `Math.random()`, 브라우저 전용 API, 서버·브라우저 로캘 차이를 쓴다. react.dev가 든 다른 원인: 루트 안의 여분 공백, 서버와 다른 데이터.
- **실험**: 서버 HTML `서버에서 렌더`, 클라이언트 컴포넌트는 `typeof window`로 `브라우저에서 렌더`를 내게 했다.

`(실험, headless Chrome 151, React 19.2.8, 2026-10-04)`

```text
{"text":"브라우저에서 렌더","sameNode":false,"recoverable":["Minified React error #418; visit https://react.dev/errors/418?args[]=text&args[]= for the full message …"]}
{"text":"브라우저에서 렌더","sameNode":false,"recoverable":["Hydration failed because the server rendered text didn't match the client. As a result this tree will be regenerated on the client. This can happen if a SSR-ed Client Component used:\n\n- A server/clien"]}
```

  - 첫 줄은 운영 빌드, 둘째 줄은 개발 빌드다.
  - `sameNode:false`: 하이드레이션 전에 잡아 둔 `<p>` 노드와 이후의 `<p>`가 다른 객체다. React가 서버 DOM을 버리고 클라이언트에서 다시 만들었다는 뜻이다. react.dev는 이런 복구가 최선이어도 느려지고, 최악이면 이벤트 핸들러가 엉뚱한 요소에 붙는다고 한다.
- **대처**: 렌더 경로에서 비결정 값을 뺀다. 의도된 차이는 두 번 그리기로 처리한다. 운영에서는 `onRecoverableError`로 수집해 수를 추적한다.

### 2. SSR 응답 캐시 → 사용자별 데이터 교차 노출 (⚠ 커리큘럼)

- **현상**: 사용자 A가 B의 이름·주문 내역을 본다.
- **보이는 형태**: 고객 문의 "다른 사람 계정이 보여요". 서버 로그에는 B의 요청이 없다(캐시가 응답했으므로).
- **원인**: 쿠키에 따라 달라지는 HTML을 공유 캐시(CDN·리버스 프록시·앱 메모리 캐시)가 URL만 키로 저장했다.
- **실험**: 서버 메모리 캐시를 URL만 키로 둔 `/me`에, 쿠키가 다른 두 브라우저 컨텍스트로 차례로 접속했다.

`(실험, headless Chrome 151, 2026-10-04)`

```text
cookie user=alice /me → alice님의 주문 내역
cookie user=bob /me → alice님의 주문 내역
cookie user=bob /me?nocache → bob님의 주문 내역
```

- **실사건**: Valve의 2015-12-25 Steam 장애. Valve 성명에 따르면, DoS 공격 대응으로 캐시 파트너가 넣은 두 번째 캐시 설정이 인증된 사용자의 웹 트래픽을 잘못 캐시했다. 일부 사용자가 다른 사용자용 Store 응답(다른 사용자의 계정 페이지 포함)을 봤다. "11:50 PST와 13:20 PST 사이, 약 34k 사용자의 스토어 페이지 요청이 다른 사용자에게 반환돼 보였을 수 있다"(Steam 공지 원문).
- **대처**: 개인화 응답에 `Cache-Control: private`(또는 `no-store`). 캐시가 필요하면 공통 부분만 캐시하고 개인화 부분은 CSR·별도 요청으로 뺀다. CDN 규칙이 쿠키 있는 요청을 우회하는지 배포 전에 확인한다.

### 3. CSR 첫 화면이 늦거나 비어 있다

- **현상**: 저사양 휴대폰에서 흰 화면이 수 초 이어진다. JS를 실행하지 않는 크롤러·링크 미리보기에는 내용이 없다.
- **보이는 형태**: LCP가 나쁘다(위 실험에서 FCP·LCP 3.7~4.4초). 페이지 소스에는 `<div id="root"></div>`뿐이다. JS 오류 하나로 화면 전체가 비기도 한다.
- **원인**: HTML → JS → 데이터 → 렌더의 직렬 대기. 메인 스레드에서 전체 DOM을 처음부터 만든다.
- **대처**: 공개 페이지는 SSR·SSG로 옮긴다. CSR을 유지하면 코드 분할(09번)과 데이터 요청을 HTML에서 미리 시작(`<link rel="preload">` 등, 13번)한다.

### 4. SSR의 느린 데이터 하나가 페이지 전체를 막는다

- **현상**: 추천 상품 API가 느려지자 페이지 전체의 TTFB가 같이 늘었다.
- **보이는 형태**: 문서 요청의 서버 대기 시간 증가, 위 실험에서 SSR TTFB 339~370ms(DB 300ms 포함) vs 스트리밍 6~9ms.
- **원인**: `renderToString`은 데이터를 기다리지 않는다(react.dev: 중단된 컴포넌트는 곧바로 fallback HTML). 그래서 서버가 호출 **전에** 데이터를 다 모아야 한다(실험의 `await db()`). React WG 글(2021)이 "뭐라도 보여 주려면 전부 가져와야 한다"고 짚은 문제다.
- **대처**: 느린 부분을 `<Suspense>`로 감싸 스트리밍한다. 첫 화면에 필요 없는 데이터는 클라이언트에서 늦게 가져온다. 서버 데이터 호출에 타임아웃을 둔다([reliability/05](../../reliability/05-timeouts-and-deadline-propagation/2-summary.md)).

### 5. 서버 모듈 상태에 요청별 데이터 → 요청 간 누출

- **현상**: 간헐적으로 다른 사용자 정보가 섞인다. 부하가 높을 때만 재현된다.
- **보이는 형태**: 캐시를 꺼도 생긴다. 동시 요청이 겹칠 때만 나타난다.
- **원인**: SSR 코드가 `let currentUser`처럼 모듈 전역에 요청 정보를 넣었다. 한 프로세스가 동시 요청을 처리하므로 다른 요청이 그 값을 덮어쓴다.
- **대처**: 요청별 데이터는 인자·컨텍스트로만 전달한다(Node `AsyncLocalStorage` 같은 요청 범위 저장소 포함). 동시 요청 부하 테스트에 "응답 속 사용자 ID = 요청 사용자 ID" 검사를 넣는다.

## 핵심 문장

- 렌더링 방식은 HTML을 **어디서**(서버·브라우저) **언제**(빌드·요청·실행) 만드느냐의 선택이다.
- SSR·SSG는 보이는 시점을 앞당기지만, 반응하는 시점은 JS 다운로드와 하이드레이션이 끝나야 온다. 이 실험에서 그 간격은 2초를 넘었다.
- CSR은 HTML → JS → 데이터 → 렌더를 차례로 기다려 첫 화면이 늦다. 대신 보이면 곧 반응한다.
- 스트리밍은 느린 데이터 때문에 셸까지 기다리지 않게 한다. 경계 단위로 나중 조각을 끼워 넣는다.
- 하이드레이션은 서버와 같은 출력을 전제로 한다. 텍스트가 어긋난 이 실험에서는 React가 그 트리를 버리고 클라이언트에서 다시 만들었다. 속성 불일치는 고쳐진다는 보장이 없다.
- 사용자별 HTML을 공유 캐시에 넣으면 다른 사람에게 그대로 간다. 개인화 응답은 `private`로 표시한다.

## 관련 주제·근거

- 선행
  - [02-rendering-pipeline](../02-rendering-pipeline/2-summary.md) — 파싱·레이아웃·페인트, FCP가 무엇을 그린 시점인지
  - [09-js-modules-and-bundling](../09-js-modules-and-bundling/2-summary.md) — 번들 크기·코드 분할
- 후속·연결
  - [08-web-performance-vitals](../08-web-performance-vitals/2-summary.md) — LCP·INP·CLS와 RUM vs 랩
  - [13-critical-path-and-resource-loading](../13-critical-path-and-resource-loading/2-summary.md) — 스크립트 배치·preload
  - [19-hydration-cost-and-partial-hydration](../19-hydration-cost-and-partial-hydration/2-summary.md) — "보이지만 반응하지 않는 구간"을 줄이는 법
  - [21-component-and-state-patterns](../21-component-and-state-patterns/2-summary.md) · [22-islands-and-micro-frontends](../22-islands-and-micro-frontends/2-summary.md)
  - [network/34-http-caching](../../network/34-http-caching/2-summary.md) · [network/40-chunked-and-streaming-responses](../../network/40-chunked-and-streaming-responses/2-summary.md) · [network/47-cdn-and-edge](../../network/47-cdn-and-edge/2-summary.md)
  - [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md) — 트리 직렬화·동시 순회
  - [languages/web-api/24-document-lifecycle-events](../../../languages/web-api/24-document-lifecycle-events/2-summary.md) — `DOMContentLoaded`·`load` 시점
- 문서
  - web.dev "Rendering on the Web"(Addy Osmani·Jason Miller, 2019-02-06, 2026-01-05 갱신) — 용어 정의, 방식별 장단점, 재수화의 데이터 중복·"보이지만 반응하지 못하는" 문제 <https://web.dev/articles/rendering-on-the-web>
  - web.dev "Total Blocking Time" — 50ms 초과분 합, 예시 345ms <https://web.dev/articles/tbt>
  - Chrome for Developers "Time to Interactive" — Lighthouse 10에서 TTI 제거(이상치에 민감) <https://developer.chrome.com/docs/lighthouse/performance/interactive>
  - react.dev `hydrateRoot` — 같은 출력 요구, 일부 오류만 복구·속성 불일치 미보정, 불일치 원인 목록, `suppressHydrationWarning`, 두 번 그리기, `onRecoverableError` <https://react.dev/reference/react-dom/client/hydrateRoot>
  - react.dev `renderToString` — 스트리밍·데이터 대기 미지원, 중단 시 fallback HTML <https://react.dev/reference/react-dom/server/renderToString>
  - Google Search Central "JavaScript SEO basics" — 렌더된 HTML로 색인, "not all bots can run JavaScript" <https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics>
  - react.dev `renderToPipeableStream` — 셸, `onShellReady`·`onAllReady`, `bootstrapScripts` <https://react.dev/reference/react-dom/server/renderToPipeableStream>
  - React 18 WG "New Suspense SSR Architecture in React 18"(Dan Abramov, 2021-06-05) — SSR의 세 가지 병목 <https://github.com/reactwg/react-18/discussions/37>
  - Qwik 문서 "Resumable" — 하이드레이션이 되살리는 세 가지 <https://qwik.dev/docs/concepts/resumable/>
  - React 19.2 블로그(2025-10-01) "Batching Suspense Boundaries for SSR" <https://react.dev/blog/2025/10/01/react-19-2>
  - Steam 2015-12-25 캐시 사고 — Steam 공지 원문 <https://store.steampowered.com/news/19852/>, Valve 성명 보도: PCWorld <https://www.pcworld.com/article/418933/valve-issues-statement-regarding-christmas-day-caching-fiasco.html>, SecurityWeek <https://www.securityweek.com/details-34000-steam-users-exposed-during-ddos-attack/>
- 실험 목록(코드는 위에 발췌, 전체는 작업 scratchpad `wp/10/e10/`)
  - 네 방식 비교: headless Chrome 151.0.7922.173 + Playwright(playwright-core 1.62.1), React 19.2.8, CPU 4×·지연 150ms·1638.4kbps, 상품 2000개, 방식당 5회.
  - hydration mismatch: 운영·개발 빌드 각 1회, `onRecoverableError` 메시지와 노드 동일성.
  - URL 키 캐시 교차 노출: 쿠키만 다른 브라우저 컨텍스트 3개.
  - 스트리밍 응답 원문: 목록 3개로 줄여 `curl -N`.
  - TBT 구간 재실행: 같은 조건 5회, 긴 태스크 차단 합을 전체/FCP 뒤로 나눠 계산(`wp/10/e10/run3.cjs`).
  - 지연 에뮬레이션 확인: 지연 0/150/400ms에서 하위 자원 fetch 8/155/406ms, `responseStart`에는 미반영.
