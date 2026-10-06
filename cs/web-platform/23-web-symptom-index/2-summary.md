# web-platform/23-web-symptom-index — 증상 사전: 흰 화면·멈춤·CORS·ChunkLoadError·옛 버전·hydration mismatch·레이아웃 튐·INP/LCP 나쁨·폰트 깜빡임 → 계층·원인·첫 진단·leaf — 정리 (힌트)

## 해결하는 문제

웹 플랫폼 영역의 다른 노트는 **원인에서 증상으로** 간다.\
"이미지에 `width`/`height`가 없다 → 로드 뒤 아래 내용이 밀린다(CLS)"처럼 쓴다.\
현장에서는 반대 방향이 필요하다.\
손에 든 것은 "결제 버튼이 안 눌려요"라는 문의, 콘솔의 빨간 줄 하나, RUM 대시보드에서 오른 p75 한 줄뿐이다.

이 노트는 그 **역방향 색인**이다.

```text
  다른 노트 (정방향)                               이 노트 (역방향)
  원인 --> 결함 --> 보이는 증상                      증상 --> 어느 계층에서 보였나 --> 흔한 원인 --> 첫 진단 --> leaf
  "히어로 이미지에 loading=lazy"                     "LCP가 늘었다. LCP 요소의 요청 시작 시각과 우선순위부터 본다"
```

쉬운 예: 병원 응급실의 분류(triage)다.\
"배가 아프다"만으로 병명을 정하지 않는다. 어디가, 언제부터, 무엇을 먹고 나서인지를 먼저 묻는다.\
같은 "배가 아프다"가 맹장·식중독·근육통으로 갈린다.

똑같은 구조다.\
"화면이 하얗다"는 적어도 여섯 갈래로 갈린다.\
렌더 차단 CSS·JS가 첫 페인트를 막았거나([02-2](../02-rendering-pipeline/2-summary.md) · [13-1](../13-critical-path-and-resource-loading/2-summary.md)), CSR 번들이 아직 안 돌았거나([10-3](../10-rendering-strategies/2-summary.md)), 배포 뒤 옛 청크를 못 받았거나([09-2](../09-js-modules-and-bundling/2-summary.md)), 초기화 중 `QuotaExceededError`로 멈췄거나([06-2](../06-browser-storage/2-summary.md)), 오프라인에서 서비스 워커가 HTML을 못 줬거나([07-3](../07-service-workers-and-offline/2-summary.md)), 글자만 폰트를 기다리느라 안 보이는 것이다([15-1](../15-web-font-loading/2-summary.md)).\
같은 "하얗다"인데 고치는 곳이 HTML·번들·배포·저장소·서비스 워커·폰트로 다르다.

실무 예:
- 프론트엔드 증상은 **보는 쪽과 원인 쪽이 다르다.** CORS 에러는 브라우저 콘솔에만 보이지만, 단순 요청이면 요청은 이미 서버에 갔다(처리됐을 수 있다 — [05-3](../05-fetch-from-browser/2-summary.md)). 고칠 곳은 서버 설정과 멱등 키다.
- 같은 결함이 **어디서 보느냐**에 따라 이름이 바뀐다. 랩 Lighthouse는 초록인데 CrUX p75는 "개선 필요"다([08-1](../08-web-performance-vitals/2-summary.md)). 둘 다 같은 페이지의 같은 LCP다.
- 많은 프론트엔드 장애는 **예외 없이** 진행된다. 하이드레이션 전 클릭 무시, 레이아웃 이동, 옛 버전 고착, 다른 사용자의 페이지 노출은 에러 로그가 비어 있다. 지표(RUM)와 고객 문의로 늦게 드러난다.

  - *역색인(inverted index)*: "문서 → 단어" 목록을 뒤집어 "단어 → 문서" 목록으로 만든 것이다. 여기서는 "leaf → 증상"을 "증상 → leaf"로 뒤집었다.
  - *leaf 표기 `NN-k`*: 이 영역 `NN`번 노트의 「장애 시나리오와 대처」 `k`번째 시나리오(`### k.`)다. 예: `09-2` = 09번 노트의 시나리오 2(배포 직후 `ChunkLoadError`).
  - *메시지 옆 판*: 각 leaf 실험에서 실제로 찍힌 메시지다. 대부분 headless Chrome 151에서 찍었다. 다른 브라우저·판은 문구가 다를 수 있다(장애 시나리오 4).
  - *RUM(Real User Monitoring)*: 실제 사용자 브라우저에서 지표를 모아 보내는 측정이다. 랩 측정(Lighthouse 등 정해진 조건 한 번)과 구분한다([08](../08-web-performance-vitals/2-summary.md)).

## 동작·원리

### 0. 증상이 보이는 자리 — 페이지 한 번이 지나는 계층

```text
  [서버·CDN]  ─HTML─▶  [네트워크·HTTP 캐시·SW]  ─▶  [메인 스레드: 파싱·JS·스타일·레이아웃]  ─▶  [합성·화면]  ─▶  [사용자]
   접근 로그·CDN 로그      Network 탭: 상태·Initiator        Performance 탭: 긴 태스크·Layout 막대      Layers·Rendering 탭       "안 눌려요"
   TTFB                  (ServiceWorker)·(disk cache)      Console: 예외·CORS·SRI·CSP 메시지         Layout Shift Regions      RUM p75
                         Priority Low/High                 Memory: 힙 스냅샷                         필름 스트립                 Search Console

  보이는 자리 ≠ 원인 자리
   CORS 에러              보이는 곳: 브라우저 콘솔        원인: 서버 CORS 설정. 단순 요청이면 서버에 이미 도달      05-3
   옛 화면이 계속 뜸        보이는 곳: 사용자 화면          원인: 서비스 워커의 cache-first HTML, waiting 워커      07-1
   다른 사람 계정이 보임    보이는 곳: 고객 문의            원인: 공유 캐시 키에 쿠키 없음, 서버 모듈 전역 변수        10-2 · 10-5
   "버튼이 안 눌려요"       보이는 곳: 사용자·INP           원인: 하이드레이션 전, 긴 태스크, div 버튼(키보드)       19-1 · 16-1 · 11-1
   LCP 악화                보이는 곳: RUM·CrUX             원인: 첫 화면 이미지 lazy, preload 남발, 폰트 대기       13-3 · 13-2 · 15-1
```

- 그래서 증상을 받으면 **어느 계층의 기록에서 봤는지**를 먼저 적는다.
- 사용자 화면에서만 보이고 서버 로그가 비어 있으면, 요청이 서버에 오지 않았을 수 있다. 서비스 워커·CDN·HTTP 캐시가 대신 응답했는지 Network 탭의 Size 칸을 본다([07-1](../07-service-workers-and-offline/2-summary.md), [10-2](../10-rendering-strategies/2-summary.md)).
  - *Initiator*: Network 탭에서 그 요청을 일으킨 주체(HTML 파서·CSS·스크립트 줄)다. "발견이 늦었다"를 가르는 칸이다([13-4](../13-critical-path-and-resource-loading/2-summary.md)).

### 0-1. 첫 확보 — 증상 하나에 붙일 여섯 가지

| 확보할 것 | 왜 | 어디서 |
|---|---|---|
| 브라우저·판·기기 등급 | "Safari만"·"저사양 안드로이드만"을 가른다. 프로세스 배치·저장소 축출·폰트 `auto` 동작이 엔진·판마다 다르다 | User-Agent, RUM 차원, 지원 문의 |
| 첫 방문인가 재방문인가 | 서비스 워커·HTTP 캐시·폰트 캐시가 끼는지 가른다 | RUM, 재현 시 새 프로필 vs 기존 프로필 |
| 배포·설정 변경 시각 | `ChunkLoadError`·옛 버전 고착·싱글턴 협상 실패는 배포와 맞물린다 | 배포 기록, CDN 설정 이력 |
| 콘솔 메시지 원문 | CORS·SRI·CSP·하이드레이션·preload 경고는 원문이 원인을 말해 준다 | DevTools Console, `error`·`unhandledrejection` 수집 |
| Network 행 하나(상태·Size·Priority·Initiator) | 500/404/`(pending)`/`(ServiceWorker)`/Low 우선순위를 가른다 | DevTools Network |
| 랩인가 필드인가, 몇 번째 백분위인가 | 랩 1회 값과 필드 p75는 다른 질문에 답한다 | Lighthouse vs CrUX·RUM([08](../08-web-performance-vitals/2-summary.md)) |

### 실험: 결함 다섯 개를 한 페이지에 심고, 공통 수집기 하나로 분류하기

목적: 색인의 "첫 진단" 칸이 실제로 서로 다른 신호로 잡히는지 확인한다.\
페이지 맨 앞에 수집기(`PerformanceObserver` 4종 + `error`·`unhandledrejection` + `fetch` 감싸기)를 두고, 다섯 결함을 심었다.

```js
// 페이지 <head> 맨 앞 — 공통 수집기 (핵심만)
const log = (kind, d) => __log.push({ t: Math.round(performance.now()), kind, ...d });
addEventListener('error', e => log('window.error', { msg: String(e.message) }));
addEventListener('unhandledrejection', e => log('unhandledrejection', { msg: e.reason.name + ': ' + e.reason.message }));
new PerformanceObserver(l => l.getEntries().forEach(e => log('longtask', { dur: Math.round(e.duration) })))
  .observe({ type: 'longtask', buffered: true });
new PerformanceObserver(l => l.getEntries().forEach(e => { if (!e.hadRecentInput) log('layout-shift', { value: +e.value.toFixed(4),
  src: e.sources.map(s => s.node?.id).filter(Boolean).join(',') }); }))
  .observe({ type: 'layout-shift', buffered: true });
new PerformanceObserver(l => l.getEntries().forEach(e => log('lcp', { at: e.startTime, el: e.element?.id })))
  .observe({ type: 'largest-contentful-paint', buffered: true });
new PerformanceObserver(l => l.getEntries().forEach(e => e.name === 'click' && log('event-timing', {
  dur: e.duration, inputDelay: e.processingStart - e.startTime, processing: e.processingEnd - e.processingStart })))
  .observe({ type: 'event', durationThreshold: 16, buffered: true });
const _fetch = window.fetch;
window.fetch = async (...a) => { const r = await _fetch(...a); if (!r.ok) log('fetch-not-ok', { url: String(a[0]), status: r.status }); return r; };

// 심은 결함 다섯
fetch('/api/500').then(r => log('app-saw', { what: '500 응답을 then으로 받음', ok: r.ok }));  // (1) 500 — reject 안 됨
fetch('http://127.0.0.1:<다른 포트>/api/data').catch(e => log('fetch-reject', { msg: e.name + ': ' + e.message })); // (2) CORS 헤더 없음
import('/assets/chart-OLDHASH.js').catch(e => log('dynamic-import-fail', { msg: e.name + ': ' + e.message }));   // (3) 지워진 청크
Promise.reject(new Error('잡지 않은 거부'));                                // (4)
btn.addEventListener('click', () => { const s = performance.now(); while (performance.now() - s < 300) {} });  // (5) 300ms 핸들러
// + 크기 없는 <img>(400×200 SVG, 서버가 400ms 늦게 줌)
```

- 환경: 로컬 Node `http` 서버 두 개(127.0.0.1, 포트만 다름 = 다른 출처), Playwright(`playwright-core`) + `/usr/bin/google-chrome` headless, 뷰포트 800×600, 스로틀 없음. 클릭은 로드 뒤 약 0.8초에 한 번.

`(실험, headless Chrome 151.0.7922.173, 스로틀 없음, 2026-10-04 — 포트 번호는 PORT로 가림)`

```text
{"t":113,"kind":"unhandledrejection","msg":"Error: 잡지 않은 거부"}
{"t":114,"kind":"fetch-not-ok","url":"/api/500","status":500}
{"t":115,"kind":"app-saw","what":"500 응답을 then으로 받음","ok":false}
{"t":117,"kind":"fetch-reject","msg":"TypeError: Failed to fetch"}
{"t":119,"kind":"dynamic-import-fail","msg":"TypeError: Failed to fetch dynamically imported module: http://127.0.0.1:PORT/assets/chart-OLDHASH.js"}
{"t":131,"kind":"lcp","at":124,"el":"title"}
{"t":448,"kind":"layout-shift","value":0.0202,"src":"below,btn"}
{"t":1705,"kind":"longtask","dur":302}
{"t":1714,"kind":"event-timing","name":"click","dur":304,"inputDelay":3,"processing":300}
--- console error (DevTools Console에 보이는 줄) ---
Failed to load resource: the server responded with a status of 500 (Internal Server Error)
Access to fetch at 'http://127.0.0.1:PORT/api/data' from origin 'http://127.0.0.1:PORT' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.
Failed to load resource: net::ERR_FAILED
Failed to load resource: the server responded with a status of 404 (Not Found)
Failed to load resource: the server responded with a status of 404 (Not Found)
```

- 세 번 더 돌렸다. `longtask` 301~302ms, 클릭 `dur` 304·`processing` 300~301·`inputDelay` 2~3ms, `layout-shift` 0.0202, LCP 요소 `title`이 매번 같았다. LCP 시각은 실행마다 조금씩 흔들렸다(사실 점검 재실행 3회 포함 108~136ms).

관찰과 해석:
- **(1) 500**은 앱 코드에 `ok:false`인 *성공*으로 왔다. 감싼 `fetch`가 따로 세지 않으면 에러 수집기에 아무것도 남지 않는다([05-1](../05-fetch-from-browser/2-summary.md)).
- **(2) CORS**는 앱 코드에는 `TypeError: Failed to fetch` 한 줄뿐이다. 원인을 말해 주는 `blocked by CORS policy` 문장은 **DevTools 콘솔에만** 있다. 스크립트가 받는 예외에는 이유가 빠져 있으니, RUM으로 CORS를 가르려면 요청 URL·출처를 함께 보내야 한다(해석).
- **(3) 지워진 청크**는 `Failed to fetch dynamically imported module`로 왔다. webpack 런타임이면 같은 상황이 `ChunkLoadError`로 보인다([09-2](../09-js-modules-and-bundling/2-summary.md)).
- **(5) 300ms 핸들러**는 `longtask`와 `event-timing` 두 신호에 동시에 잡혔다. Event Timing의 `processing` ≈ 300ms가 "핸들러 자체가 무겁다"를 가리킨다. 앞선 다른 작업 때문이라면 `inputDelay`가 컸을 것이다([08-3](../08-web-performance-vitals/2-summary.md), [16-1](../16-long-tasks-and-web-workers/2-summary.md)).
- **크기 없는 이미지**는 `layout-shift` 항목을 남겼고, `sources`가 밀린 문단(`below`)과 버튼(`btn`)을 가리켰다. 값이 0.02로 작은 것은 밀린 요소의 면적이 작아서다. 같은 결함도 아래 내용이 크면 0.1을 넘는다(08 실험 0.2313, 14 실험 0.22).
- 덤으로 본 함정: 400×200 이미지가 도착한 뒤에도 LCP 요소는 `title`(h1)로 남았다. 단색 SVG라서다. web.dev "Largest Contentful Paint"는 Chromium이 "Placeholder images or other images with a low entropy"를 LCP에서 뺀다고 쓴다. 이 이미지가 그 규칙에 걸렸다고 보는 것은 해석이다 `[?]`. "LCP 요소가 예상과 다르다"면 `lcp` 항목의 `element`부터 찍어 본다.

### 증상 지도 — 무엇을 먼저 묻나

```text
  증상을 받았다
     │
     ├─ 콘솔에 빨간 줄이 있나? ── 예 ─▶ 메시지 원문으로 §8(네트워크·CORS) §9(배포) §10(하이드레이션) §17(번들)
     │                         └ 아니오 ─▶ "예외 없는 장애" — 지표·트레이스로 간다
     │
     ├─ 언제? ─ 첫 로드 중 ─────────▶ §1(흰 화면) §6(LCP) §7(글자)
     │        ├ 로드 직후 몇 초 ─────▶ §10(하이드레이션) §3(INP)
     │        ├ 상호작용할 때 ────────▶ §3(INP) §4(스크롤) §16(이벤트) §13(키보드)
     │        ├ 오래 쓴 뒤 ───────────▶ §15(메모리) §11(저장소 축출)
     │        └ 배포 직후·며칠째 ──────▶ §9(배포)
     │
     ├─ 누구에게? ─ 저사양·모바일만 ─▶ §18(랩 vs 필드) §6 §3
     │           ├ 특정 언어·지역만 ─▶ §14(국제화)
     │           ├ 특정 브라우저만 ──▶ §11(Safari 저장소) §5(CDN 포맷) §1(엔진 차이)
     │           └ 다른 사람 데이터 ─▶ §11(교차 노출) — 보안 사고로 바로 올린다
     │
     └─ 화면 값이 틀린가(에러 없음)? ──▶ §12(상태·캐시) §14(서식·복수형)
```

- 그림 해설: 첫 질문은 "콘솔이 무엇을 말하나"다. 콘솔이 조용하면 그 장애는 지표·트레이스·고객 문의로만 보인다. 이 영역 leaf의 장애 시나리오 104건 중 다수가 그쪽이다(아래 표의 "보이는 것" 칸에 "오류 없음"이 많은 이유).

### 1. 흰 화면·빈 화면 — 첫 로드에서 아무것도 안 뜬다

먼저 **HTML이 왔는지, 첫 페인트가 있었는지, 콘솔이 무엇을 말하는지**를 본다.

```text
  화면이 하얗다
     │
     ├─ HTML은 왔고 첫 페인트 전 긴 대기, 끝나는 CSS·JS가 있다 ─▶ 렌더·파서 차단 자원      02-2 · 13-1
     ├─ 소스가 <div id="root"></div>뿐, JS 실행 뒤에야 그려짐 ───▶ CSR 직렬 대기          10-3
     ├─ 콘솔 ChunkLoadError / Failed to fetch dynamically imported ─▶ 배포가 옛 청크를 지움  09-2
     ├─ 콘솔 QuotaExceededError, 특정 사용자만 ─────────────────▶ 초기화 중 저장 예외      06-2
     ├─ 오프라인·비행기 모드에서만 ───────────────────────────▶ SW 미제어·HTML 미캐시     07-3
     └─ 레이아웃은 있는데 글자만 없다 ─────────────────────────▶ 폰트 block 기간(FOIT)    15-1
```

| 보이는 것 (메시지·지표·판) | 계층 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|---|
| 흰 화면이 오래가고 Lighthouse 렌더 차단 자원 항목("Eliminate render-blocking resources" — 판에 따라 이름이 다르다), FCP·LCP 지연 | 메인 스레드(파서·CSSOM) | `<head>`의 CSS·동기 `<script>` | 워터폴에서 첫 페인트 직전에 끝나는 자원 | [02-2](../02-rendering-pipeline/2-summary.md) |
| 서버 응답은 빠른데 흰 화면 1초 넘음. 13 실험: 1초 걸리는 CSS·JS → FCP 1072~1092ms | 메인 스레드(크리티컬 패스) | 렌더 차단 CSS·파서 차단 JS, 태그 매니저·A/B 테스트 스크립트 | Performance 패널의 첫 페인트 전 대기, Network의 차단 자원 | [13-1](../13-critical-path-and-resource-loading/2-summary.md) |
| 저사양 휴대폰에서 흰 화면 수 초, 페이지 소스가 `<div id="root"></div>`뿐. 10 실험: CSR FCP·LCP 3.7~4.4초. JS 오류 하나로 화면 전체가 비기도 함 | 앱(렌더링 전략) | HTML → JS → 데이터 → 렌더 직렬 대기 | "페이지 소스 보기"에 본문이 있나, LCP 분해 | [10-3](../10-rendering-strategies/2-summary.md) |
| 배포 직후 기존 탭에서 특정 화면으로 갈 때 흰 화면. webpack `ChunkLoadError: Loading chunk 123 failed.`, 네이티브 ESM `TypeError: Failed to fetch dynamically imported module: …`, 그 청크 404(09 실험 C, 위 실험 (3)) | 배포·CDN | 열린 탭이 옛 해시 청크를 가리키는데 배포가 옛 파일을 지움, 캐시된 옛 HTML | Network의 404 청크 이름과 현재 배포 자산 목록 비교 | [09-2](../09-js-modules-and-bundling/2-summary.md) |
| 특정 사용자만 흰 화면, 콘솔 `QuotaExceededError: Failed to execute 'setItem' on 'Storage': …exceeded the quota.` | 브라우저 저장소 | localStorage에 큰 JSON 누적, 예외 처리 없음(Chrome에서 약 5Mi 문자에서 막힘 — 06 실험 2) | Application → Local Storage 크기, `setItem` 주변 try/catch | [06-2](../06-browser-storage/2-summary.md) |
| 비행기 모드에서 "인터넷 연결 없음", `controlled=false` | 서비스 워커 | 오프라인 전에 워커가 활성화되지 않음(첫 방문 페이지는 미제어), HTML 미캐시, 시간 제한 없는 network-first | Application → Service Workers 상태, `navigator.serviceWorker.controller` | [07-3](../07-service-workers-and-offline/2-summary.md) |
| 첫 화면 제목·버튼 글자가 몇 초간 빈칸. 15 실험: `block` 3초, Chrome `auto` 2초 | 폰트 로딩 | `font-display` 미지정·`block` | 필름 스트립의 빈 글자, `@font-face`의 `font-display` | [15-1](../15-web-font-loading/2-summary.md) |

### 2. 화면이 멈춘다·탭이 응답 없음·탭이 재로드된다

먼저 **CPU가 도는지(멈춤), 메모리가 크는지(재로드), 그 탭만인지**를 본다.

```text
  화면이 굳었다
     │
     ├─ "페이지 응답 없음", 그 탭 CPU 100%, 다른 탭 정상 ─▶ 끝나지 않는 동기 코드        01-1
     ├─ 끝나지 않는 태스크 안에 Run Microtasks, rAF 0회 ─────▶ 마이크로태스크 무한 연쇄    03-2
     ├─ 정렬·펼치기에서만, Layout 막대 촘촘 + Forced reflow ─▶ layout thrashing           02-1
     ├─ 표 화면 진입·창 크기 변경 때마다 수 초 ──────────────▶ 거대 DOM                    17-1
     ├─ "앗, 이런!" 오류 페이지(sad tab) ─────────────────────▶ 렌더러 충돌·메모리 한도      01-2
     └─ 저사양 기기에서 탭이 자꾸 재로드 ─────────────────────▶ 메모리: §15                 01-3 · 02-4 · 04-1
```

| 보이는 것 (메시지·지표·판) | 계층 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|---|
| "페이지 응답 없음" 대화상자, 작업 관리자에서 그 탭 프로세스 CPU 100%(코어 하나), 다른 탭 정상 | 렌더러 프로세스(메인 스레드) | 조건이 틀린 `while`, 거대한 JSON 동기 처리. 같은 이벤트 루프의 opener 팝업도 같이 멈춤 | DevTools 일시 정지 버튼으로 루프 위치 | [01-1](../01-browser-architecture/2-summary.md) |
| 화면이 얼고 타이머도 안 돎, CPU 100%. 03 실험: 500ms 동안 rAF 0회, 먼저 건 `setTimeout`이 501ms에야 실행 | 이벤트 루프 | `then` 재귀, `while(await check())`, `MutationObserver` 순환 | Performance 패널에서 끝나지 않는 태스크 안의 "Run Microtasks" | [03-2](../03-event-loop/2-summary.md) |
| 정렬·아코디언에서 굳음, 보라색 Layout 막대 반복 + "Forced reflow is a likely performance bottleneck". 02 실험: `LayoutCount` 300 | 메인 스레드(레이아웃) | 루프 안에서 쓰기 직후 `offsetHeight`·`getBoundingClientRect()` 읽기 | 트레이스의 강제 레이아웃 스택(어느 줄이 읽었나) | [02-1](../02-rendering-pipeline/2-summary.md) |
| 표 화면 진입 몇 초 멈춤, 폭을 바꾸면 또 멈춤. 17 실험(4× 스로틀): 노드 108,589, 로드 5.7~7.8초, 폭 변경 레이아웃 2.1~2.7초 | 메인 스레드(DOM 크기) | 1만 행을 그대로 DOM에 | `document.querySelectorAll('*').length`, Layout 블록 길이 | [17-1](../17-list-virtualization/2-summary.md) |
| 탭 내용이 오류 화면("앗, 이런!" 류)과 오류 코드로 바뀜, 다른 탭은 정상 | 렌더러 프로세스 | 메모리 한도 초과, 렌더러 버그, 확장 충돌 | Memory 패널 힙 스냅샷(누수면 §15) | [01-2](../01-browser-architecture/2-summary.md) |

### 3. "버튼이 안 눌린다"·INP 나쁨

먼저 **Event Timing 세 조각(input delay · processing · presentation) 중 무엇이 큰지**, 그리고 **하이드레이션 전인지**를 본다.

```text
  클릭·입력이 늦게 반영되거나 무시된다
     │
     ├─ 클릭이 아예 무시됨(오류 없음), 로드 직후만 ───────▶ 하이드레이션 전 클릭           19-1 · 19-4
     ├─ 키보드로만 안 눌림(마우스는 됨) ─────────────────▶ div 버튼: §13                  11-1
     ├─ processing이 큼 ────────────────────────────────▶ 핸들러 안의 무거운 계산        16-1 · 08-3
     │                  └ 키마다 큰 목록 재렌더 ─────────▶ 상태 위치·memo                18-1 · 18-2 · 21-3
     ├─ input delay가 큼 ───────────────────────────────▶ 다른 긴 태스크(하이드레이션·저장) 03-1 · 19-2 · 06-5
     ├─ presentation delay가 큼, LoAF 남음 ──────────────▶ 양보 뒤 큰 DOM 갱신            16-4
     ├─ 워커로 옮겼는데 더 느림 ──────────────────────────▶ 구조적 복제 비용              16-2
     └─ 스피너를 켰는데 안 보임 ──────────────────────────▶ await는 렌더 기회를 안 줌      03-3
```

| 보이는 것 (메시지·지표·판) | 계층 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|---|
| 버튼이 한참 뒤 반응, RUM INP p75 200ms 초과. 03 실험: `processingStart − startTime` 249ms | 이벤트 루프 | 앞선 긴 태스크(JSON 파싱·무거운 렌더) | Event Timing의 input delay, Performance 패널 50ms 초과 태스크 | [03-1](../03-event-loop/2-summary.md) |
| 필터 버튼 뒤 0.3초 이상 그대로. 08 실험: Event Timing `click` `duration` 312ms, `processingEnd − processingStart` ≈ 300ms, `web-vitals` INP `needs-improvement`. 위 실험: `processing` 300~301 | 앱(핸들러) | 핸들러의 동기 작업(processing), 다른 긴 태스크(input delay), 큰 DOM 변경(presentation) | `web-vitals` attribution 빌드로 세 조각 중 큰 쪽 | [08-3](../08-web-performance-vitals/2-summary.md) |
| 필터·정렬 클릭 뒤 굳고, 그 사이 누른 다른 버튼도 늦음. 16 실험 sync: 312ms, 다른 클릭 input delay 242~246ms | 메인 스레드 | 동기 계산 한 태스크 | Performance 패널의 빨간 삼각형 긴 태스크 | [16-1](../16-long-tasks-and-web-workers/2-summary.md) |
| 워커 도입 뒤에도 클릭 직후 굳음, 전체 시간은 늘어남. 16 실험: 객체 20만 개 복제 = 메인 240~305ms | 메인 ↔ 워커 메시지 | 큰 객체 그래프 왕복 구조적 복제 | Performance 패널의 `postMessage`·`message` 태스크 길이 | [16-2](../16-long-tasks-and-web-workers/2-summary.md) |
| 긴 태스크는 사라졌는데 INP 그대로, presentation delay 큼. 16 실험 yield에서도 LoAF 55~65ms | 렌더링(스타일·레이아웃) | 조각이 한 프레임에 몰림, 큰 DOM 갱신, 서드파티 긴 태스크 | LoAF `scripts` 속성으로 출처 | [16-4](../16-long-tasks-and-web-workers/2-summary.md) |
| 검색창 타이핑이 한 박자 늦음, Profiler에서 키마다 목록 전체 커밋. 18 실험 plain: 키 5번에 Row 15,000회, 상호작용 160~424ms(4× 스로틀) | 앱(재렌더) | 입력 상태가 큰 목록의 공통 조상에 | React Profiler 커밋별 렌더 컴포넌트 수 | [18-1](../18-ui-rerender-and-memoization/2-summary.md) |
| `React.memo`를 붙였는데 Profiler에서 매번 렌더, 이유가 props 변경. 18 실험 memo-broken: 15,000회 그대로 | 앱(참조 동일성) | 렌더마다 새 객체·배열·함수 prop | Profiler "Record why each component rendered" | [18-2](../18-ui-rerender-and-memoization/2-summary.md) |
| memo·useMemo·useCallback 전면 적용 뒤에도 안 빨라지고 stale closure 버그 | 앱 | 싼 렌더·매번 바뀌는 props에 memo | 측정 전후 비교 — 붙인 곳의 렌더 시간이 실제로 컸나 | [18-3](../18-ui-rerender-and-memoization/2-summary.md) |
| 큰 목록 화면에서 타이핑 끊김, 키마다 목록 전체가 번쩍임. 21 실험 ① global: 10글자에 행 렌더 10,000회, 스크립트 217~251ms(local 72~80ms) | 앱(상태 위치) | 자주 바뀌는 값을 많은 컴포넌트가 읽는 Context·스토어에 둠 | 그 값을 읽는 구독자 수 | [21-3](../21-component-and-state-patterns/2-summary.md) |
| "저장" 누를 때마다 잠깐 멈춤, `setItem`·`JSON.stringify`가 든 수십 ms 태스크. 06 실험 3: 4MiB 42~54ms | 브라우저 저장소(동기 API) | MiB 단위 localStorage 쓰기 | Performance 패널의 태스크 안 `setItem` | [06-5](../06-browser-storage/2-summary.md) |
| 스피너 DOM은 들어가는데 화면에 안 보이고, 작업 끝나면 바로 사라짐 | 이벤트 루프 | `show(); await Promise.resolve(); heavy();` — 마이크로태스크라 렌더 틈 없음 | 트레이스에서 스피너 삽입과 무거운 작업이 같은 태스크인가 | [03-3](../03-event-loop/2-summary.md) |

- 하이드레이션 전 클릭 무시(19-1·19-4)는 §10, 키보드로만 안 눌림(11-1)은 §13에 있다. 둘 다 **오류가 없다**. INP는 입력에서 다음 페인트까지의 지연만 잰다(Event Timing은 리스너가 없는 입력도 기록한다). 그래서 이 둘은 기능이 "반응 없음"이어도 INP가 나쁘게 나오지 않을 수 있다.

### 4. 스크롤·애니메이션이 버벅인다

| 보이는 것 (메시지·지표·판) | 계층 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|---|
| 모바일에서 스크롤 시작이 늦음, 콘솔 Violation "Added non-passive event listener to a scroll-blocking 'touchstart' event. …" | 입력·컴포지터 | 문서 수준이 아닌 요소에 단 `touchstart`·`wheel` 리스너는 기본 passive가 아님 | 콘솔 Violation, Rendering 탭 "Scrolling Performance Issues" | [04-5](../04-dom-and-event-model/2-summary.md) |
| 저사양 기기에서 슬라이드·드로어가 끊김. 02 실험: 1초에 Layout 61~62·Paint 122~124 | 메인 스레드(레이아웃·페인트) | `top`/`left` 같은 기하 속성 애니메이션 | Performance 패널에서 프레임마다 Layout·Paint, Rendering 탭 Paint flashing | [02-3](../02-rendering-pipeline/2-summary.md) |
| 모바일에서 스크롤이 오히려 느려지거나 탭 재로드, Layers 패널에 수백 개 레이어. 02 실험: `will-change` 100개 → 104 레이어 | 합성 | `will-change`·`translateZ(0)` 남발 | Layers 패널 레이어 수·합성 이유 | [02-4](../02-rendering-pipeline/2-summary.md) |
| `body` 클래스 토글 테마 전환이 느림, Recalculate Style의 "Elements affected"가 DOM 전체에 가까움 | 메인 스레드(스타일) | 조상 클래스 변경의 넓은 무효화 | Recalculate Style 막대의 영향 요소 수 | [02-5](../02-rendering-pipeline/2-summary.md) |
| 스크롤바 막대 길이가 끌수록 변하고, 끝으로 끌어도 끝이 아님, 측정 안 하면 행이 겹침. 17 실험: 그리기 9번에 `scrollHeight` 9가지, 측정 안 하면 26쌍 겹침 | 앱(가상화) | 가변 높이 추정값과 실측의 차이 | 행 높이 추정값 vs 실측 평균, 측정 캐시 키 | [17-2](../17-list-virtualization/2-summary.md) |

- 거대 DOM(17-1)은 §2에도 있다 — 스크롤 중 프레임 드롭으로도, 진입 시 멈춤으로도 보인다.

### 5. 레이아웃이 튄다 (CLS)

먼저 `layout-shift` 항목의 **`sources`**(밀린 요소)와 **시각**(무엇이 도착한 순간인가)을 본다.

| 보이는 것 (메시지·지표·판) | 계층 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|---|
| 읽거나 누르려는 순간 내용이 아래로 밀림. 08 실험 CLS 0.2313, 위 실험 0.0202(`sources`: 아래 문단·버튼) | 레이아웃(이미지 공간 예약) | `<img>`에 `width`/`height`·`aspect-ratio` 없음, 늦게 끼우는 배너 | `layout-shift` `sources`, Rendering 탭 Layout Shift Regions | [08-2](../08-web-performance-vitals/2-summary.md) |
| 이미지가 뜨면서 아래 버튼이 밀려 잘못 누름. 14 실험 CLS 0.22. `height:auto`를 빼먹으면 그림이 늘어남(225px → 450px) | 레이아웃 | 속성·CSS로 비율을 모름 | 이동 시각 = 이미지 도착 시각인가 | [14-2](../14-image-optimization/2-summary.md) |
| 폰트가 바뀌는 순간 줄 수가 바뀌어 아래가 밀림. 15 실험: 줄 9 → 10, CLS 0.011 | 폰트 로딩 | 대체 폰트와 웹 폰트의 글자 폭·세로 메트릭 차이(`swap`) | 이동 시각 = 웹 폰트 도착 시각인가 | [15-2](../15-web-font-loading/2-summary.md) |

- 가상 목록에서 "보던 행이 갑자기 밀림"(17-2)은 CLS 지표에 잡힐 수도 안 잡힐 수도 있다(클릭·탭·키 같은 이산 입력 뒤 500ms 안의 이동은 `hadRecentInput`으로 빠지지만, 스크롤은 이 "최근 입력"에 들지 않는다 — 08). 스크롤 위치 보정 문제로 따로 본다(§4).

### 6. LCP가 나쁘다 — 첫 화면 핵심 요소가 늦다

먼저 **LCP 요소가 무엇인지**(`lcp` 항목의 `element`), 그리고 그 요소의 **요청 시작 시각·우선순위·Initiator**를 본다. web.dev의 LCP 분해(TTFB · 자원 로드 지연 · 자원 로드 시간 · 요소 렌더 지연) 중 어디가 큰지를 가른다([08](../08-web-performance-vitals/2-summary.md)).

```text
  LCP가 늦다
     │
     ├─ TTFB가 크다 ───────────────────────────────────▶ SSR 데이터 대기         10-4
     ├─ 요청 시작이 늦다(자원 로드 지연)
     │     ├─ Initiator가 .css·.js ──────────────────────▶ 발견 지연(배경·JS 렌더)  13-4
     │     ├─ 우선순위 Low로 시작, 레이아웃 뒤 요청 ───────▶ 첫 화면 이미지에 lazy   13-3 · 14-3
     │     └─ 앞에 쓰지 않는 preload 여러 개 ─────────────▶ preload 남발           13-2
     ├─ 다운로드가 길다 ────────────────────────────────▶ 원본 크기 그대로         14-1
     │                 └ 거대 HTML(직렬화 JSON) ───────▶ 하이드레이션 데이터     19-3
     └─ 요소 렌더가 늦다
           ├─ 텍스트 LCP가 폰트를 기다림 ──────────────▶ FOIT·거대 폰트         15-1 · 15-3
           └─ JS가 돌아야 그려짐 ─────────────────────▶ CSR·번들 비대          10-3 · 09-1 · 09-4
```

| 보이는 것 (메시지·지표·판) | 계층 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|---|
| preload 여러 개 추가 배포 뒤 LCP 증가, 콘솔 "was preloaded using link preload but not used within a few seconds". 13 실험: 안 쓰는 preload 5장 → LCP 0.63s → 1.55s, `fetchpriority=high`로도 회복 안 됨 | 네트워크(우선순위·대역폭) | 첫 화면에 안 쓰는 큰 자원의 preload | 콘솔 미사용 preload 경고, 워터폴에서 LCP 자원 앞의 경쟁 | [13-2](../13-critical-path-and-resource-loading/2-summary.md) |
| 이미지 전부에 `loading="lazy"` 일괄 적용 뒤 LCP 악화. 14 실험: 우선순위 Low → High, LCP 1.47s → 5.4s, 서버 도착 0.19s → 4.9s | 네트워크·레이아웃 | 레이아웃 뒤 거리 판정 후 요청 | LCP 이미지의 `loading` 속성, 요청 시작 시각·Priority | [13-3](../13-critical-path-and-resource-loading/2-summary.md) · [14-3](../14-image-optimization/2-summary.md) |
| 히어로가 다른 이미지보다 늦음, Network Initiator가 `.css`·`.js`. 13 실험: CSS 배경 → 이미지 요청 328ms, LCP 560ms(preload 시 18ms·376ms) | preload 스캐너 | CSS·JS 안의 자원은 그 파일 처리 뒤 발견 | LCP 이미지 행의 Initiator | [13-4](../13-critical-path-and-resource-loading/2-summary.md) |
| 화면 폭 400px 기기가 수 MB 이미지를 받음. 14 실험: `src`만 둔 페이지가 DPR 2 휴대폰에 154KB(3840w), 800w면 14KB | 마크업·이미지 CDN | `srcset`·`sizes` 없음, `sizes`가 실제 슬롯보다 큼 | Network의 이미지 크기 vs 표시 크기 × DPR | [14-1](../14-image-optimization/2-summary.md) |
| 모바일에서 첫 화면 느림, Network에 수 MB 폰트. 15 실험: TTF 4,582KB가 1.6Mbps에서 23.9초, `auto`면 LCP 2.02초 | 폰트 로딩 | 한글 전체 데스크톱용 TTF를 그대로 | Network의 폰트 크기·형식(WOFF2인가) | [15-3](../15-web-font-loading/2-summary.md) |
| 추천 API가 느려지자 페이지 전체 TTFB 증가. 10 실험: SSR TTFB 339~370ms(DB 300ms 포함) vs 스트리밍 6~9ms | 서버(SSR) | `renderToString`은 데이터를 기다리지 않아, 호출 전에 데이터를 다 모아야 함 | 문서 요청의 서버 대기 시간, 서버 데이터 호출별 시간 | [10-4](../10-rendering-strategies/2-summary.md) |
| 첫 화면이 몇 초 늦음, Lighthouse "Reduce unused JavaScript", Coverage 패널의 높은 미사용 비율 | 번들 | 전체 라이브러리 import, CJS로 트리 셰이킹 실패, 분할 없음 | Coverage 패널, 번들 분석(metafile) | [09-1](../09-js-modules-and-bundling/2-summary.md) |
| 번들 없는 배포에서 JS 요청이 계단처럼 순차. 09 실험 B: 깊이 6에서 약 870ms vs 번들 약 225ms(요청당 지연 100ms) | 네트워크(모듈 폭포) | 모듈을 받아 파싱해야 다음 import를 앎 | Network 워터폴의 계단 모양 | [09-4](../09-js-modules-and-bundling/2-summary.md) |
| 몇 주 뒤 저사양 기기에서 느리다는 신고, 번들 크기 추이에 계단. 20 실험: `import _ from 'lodash'` 한 줄로 gzip 0.2 → 26.3 KB, 랩 LCP 480 → 872 ms | 빌드·CI | 크기 예산·게이트 없음, 리뷰가 번들 diff를 안 봄 | 배포별 번들 크기 이력, metafile의 기여 모듈 | [20-1](../20-performance-budgets-and-regression-gates/2-summary.md) |

- 하이드레이션 JSON으로 문서가 커진 경우(19-3)는 §10, 랩·필드 차이(08-1)는 §18에 있다.

### 7. 글자가 안 보이거나·깜빡이거나·섞인다

| 보이는 것 (메시지·지표·판) | 계층 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|---|
| 같은 woff2가 Network에 두 줄, 콘솔 "A preload for '…' is found, but is not used because the request credentials mode does not match. Consider taking a look at crossorigin attribute." 15 실험: 37ms·363ms | 네트워크(자격 증명 모드) | 폰트 preload에 `crossorigin` 누락 | 콘솔 경고, `<link rel=preload as=font>`의 속성 | [15-4](../15-web-font-loading/2-summary.md) · [13-5](../13-critical-path-and-resource-loading/2-summary.md) |
| 사용자 이름·댓글의 일부 글자만 모양이 다름 | 폰트(글리프 대체) | 서브셋에 없는 코드 포인트가 다음 폰트로 | Computed 탭 "Rendered Fonts"에 두 폰트 | [15-5](../15-web-font-loading/2-summary.md) |
| 처음 보인 글자가 잠깐 뒤 다른 글자로 바뀜(깜빡임) + 하이드레이션 오류 | SSR·하이드레이션 | 렌더 중 비결정 값 | §10의 10-1 | [10-1](../10-rendering-strategies/2-summary.md) |

- FOIT(15-1)는 §1, swap 이동(15-2)은 §5에 있다. "폰트 깜빡임"이라는 같은 말이 **안 보임(FOIT)**·**바뀌며 밀림(FOUT+CLS)**·**글자마다 다름(서브셋)** 셋을 가리킨다. 사용자 말보다 필름 스트립을 먼저 본다.

### 8. 네트워크·API — CORS 에러, "성공인데 실패", 무한 로딩, 401

먼저 **Network 행의 상태 칸과 콘솔 원문**을 나란히 본다. 앱이 받은 예외에는 이유가 빠져 있다(위 실험 (2)).

```text
  요청이 이상하다
     │
     ├─ Network는 빨간 500, 앱은 "성공" ──────────────────▶ res.ok 미확인             05-1
     ├─ (pending)이 끝나지 않음 ───────────────────────────▶ 타임아웃 기본값 없음        05-2
     ├─ 콘솔 "blocked by CORS policy", 서버엔 POST 두 번 ────▶ 단순 요청은 서버에 감     05-3
     ├─ 401, 요청 헤더에 Cookie 없음 ───────────────────────▶ credentials 모드·ACAO *    05-4
     ├─ Uncaught (in promise) AbortError ──────────────────▶ read() 루프 미처리         05-5
     └─ 이미지가 일부 사용자에게만 깨짐, 같은 URL 다른 형식 ─▶ CDN 협상 + Vary 누락       14-4
```

| 보이는 것 (메시지·지표·판) | 계층 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|---|
| 결제 실패인데 완료 화면, 에러 모니터링 0건. Network 빨간 500, 앱 로그 성공, `SyntaxError: Unexpected token '<'`. 위 실험 (1): `ok:false`가 `then`으로 옴 | 앱(fetch 사용) | `res.ok`를 안 봄 — 상태 코드는 거부 사유가 아님(Fetch 표준) | 공통 래퍼에 `!res.ok` 처리가 있나 | [05-1](../05-fetch-from-browser/2-summary.md) |
| 스피너가 끝나지 않음, Network `(pending)`. 05 실험 4: 신호 없는 요청은 서버가 줄 때(3009ms)까지 기다림 | 앱(fetch 사용) | Fetch 표준에 시간 제한 없음 | 요청에 `signal`이 있나 | [05-2](../05-fetch-from-browser/2-summary.md) |
| 콘솔 `… has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header …`, 앱은 `TypeError: Failed to fetch`(위 실험 (2)), 서버 로그에 POST 두 번, 주문 두 건 | 브라우저 정책(CORS) + 서버 | 단순 요청(POST `text/plain`·form)은 프리플라이트 없이 서버에 가서 처리될 수 있음, 막힌 것은 응답 읽기 | 서버 접근 로그에 그 요청이 있나, 응답 헤더의 `Access-Control-Allow-Origin` | [05-3](../05-fetch-from-browser/2-summary.md) |
| `api.` 서브도메인 호출이 401, 요청 헤더에 `Cookie` 없음, 또는 `Failed to fetch` | 브라우저 정책(credentials) | 교차 출처 기본 credentials는 `same-origin`. `include`면 `ACAO: *`가 거부됨 | 요청의 `credentials`, 응답의 ACAO·ACAC·`Vary: Origin`, 쿠키 `SameSite`·`Domain` | [05-4](../05-fetch-from-browser/2-summary.md) |
| 검색어 변경 뒤에도 이전 스트림을 그림, 콘솔 `Uncaught (in promise) AbortError` | 앱(스트림) | `reader.read()` 루프의 `AbortError`를 안 받음 | 읽기 루프 전체가 try/catch 안인가 | [05-5](../05-fetch-from-browser/2-summary.md) |
| 일부 사용자에게만 이미지가 깨짐, AVIF를 못 읽는 클라이언트가 `Content-Type: image/avif`를 받음 | CDN(캐시 키) | `Accept`로 포맷을 바꾸는데 캐시 키에 `Accept` 없음(`Vary: Accept` 누락) | 같은 URL을 `Accept`만 바꿔 두 번 요청해 응답 비교 | [14-4](../14-image-optimization/2-summary.md) |

- 폰트 preload의 자격 증명 모드 불일치(15-4·13-5)도 같은 "CORS 계열"이다(§7). 폰트는 CORS 모드로 요청되므로, 다른 출처 폰트는 서버가 `Access-Control-Allow-Origin`을 줘야 쓸 수 있다([15-4](../15-web-font-loading/2-summary.md)).

### 9. 배포했는데 반영 안 됨·배포 직후 깨짐

먼저 **Network의 Size 칸**(`(ServiceWorker)`·`(disk cache)`·`(memory cache)`)과 **배포 시각**을 본다.

```text
  배포 뒤 이상하다
     │
     ├─ 일부 사용자만 며칠째 옛 화면, Size=(ServiceWorker) ─▶ SW cache-first HTML·waiting   07-1
     ├─ 새 워커가 나타났다 사라짐(redundant) ─────────────▶ 사전 캐시 목록에 404         07-2
     ├─ 기존 탭에서 청크 404 ─────────────────────────────▶ 옛 청크 삭제               09-2
     ├─ 프로덕션 빌드에서만 스타일·폴리필 없음 ─────────────▶ sideEffects:false 오선언     09-3
     ├─ 셸 업그레이드 뒤 오래된 원격 하나만 깨짐 ───────────▶ 싱글턴 버전 협상            22-5
     └─ 예산을 크게 넘는 변경이 게이트를 통과 ──────────────▶ 도구 판 변경으로 게이트 무력화 20-3
```

| 보이는 것 (메시지·지표·판) | 계층 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|---|
| 새 기능 배포 뒤 일부 사용자는 며칠째 옛 화면, HTML·JS가 `(ServiceWorker)`로 응답, 서버 로그에 그 사용자의 HTML 요청 없음 | 서비스 워커 | HTML·해시 없는 `app.js`를 cache-first, 탭이 열려 있으면 새 워커가 waiting(07 실험 3·6) | Application → Service Workers의 waiting 워커, 캐시 안 HTML | [07-1](../07-service-workers-and-offline/2-summary.md) |
| 새 워커 `redundant`, 옛 워커가 계속 제어, 콘솔 `Uncaught (in promise) TypeError: Failed to execute 'addAll' on 'Cache': Request failed`. 07 실험: 캐시 항목 0개, `registration.active=null` | 서비스 워커(install) | 사전 캐시 목록에 404 URL — `addAll`은 하나라도 실패하면 전체 거부 | 사전 캐시 목록 URL 각각의 상태 | [07-2](../07-service-workers-and-offline/2-summary.md) |
| 프로덕션에서만 버튼 스타일 없음, 구형 브라우저에서만 `xxx is not a function`. 빌드 경고 `Ignoring this import because ... was marked as having no side effects`(esbuild, 09 실험 A) | 빌드(트리 셰이킹) | 패키지의 `"sideEffects": false`가 CSS·폴리필 import를 지움 | 빌드 경고, 개발·프로덕션 결과 비교 | [09-3](../09-js-modules-and-bundling/2-summary.md) |
| 셸이 React를 올렸더니 오래된 원격 하나만 이상, Module Federation 콘솔 경고(허용 범위 불일치) | 마이크로 프론트엔드 런타임 | `singleton`이면 한 버전만 — 높은 버전의 바뀐 동작을 원격이 못 견딤 | 공유 라이브러리 허용 범위, 실제 로드된 판 | [22-5](../22-islands-and-micro-frontends/2-summary.md) |
| 예산 초과 변경이 게이트 통과, CI 로그에 실패도 경고도 없음, 단언 결과 0개 | CI(측정 도구) | Lighthouse 12.0.0의 "remove budgets (#15950)" — 옛 `budgets` 설정을 읽는 쪽이 사라짐 | 게이트 실행 로그의 단언 수, 카나리(일부러 넘는 페이지)가 실패하나 | [20-3](../20-performance-budgets-and-regression-gates/2-summary.md) |

- `ChunkLoadError`(09-2)는 §1에 있다. 09-2의 대처("실패 시 1회 새로고침")와 07-1의 원인(SW가 옛 HTML을 줌)이 겹치면 새로고침도 옛 HTML을 받는다. 그래서 두 leaf를 함께 본다.

### 10. 하이드레이션·SSR — 깜빡임, 클릭 무시, 로드 직후 버벅임

| 보이는 것 (메시지·지표·판) | 계층 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|---|
| 처음 글자가 잠깐 뒤 바뀜. 개발 `Hydration failed because the server rendered text didn't match the client. …` / 운영 `Minified React error #418`. 10 실험(React 19.2.8): `sameNode:false` — 서버 DOM을 버리고 다시 만듦 | SSR·하이드레이션 | 렌더 중 `typeof window`·`Date.now()`·`Math.random()`·로캘 차이, 여분 공백, 서버와 다른 데이터 | 개발 빌드 콘솔의 diff, 운영은 `onRecoverableError` 수집 | [10-1](../10-rendering-strategies/2-summary.md) |
| "눌렀는데 아무 일도 없다", 두세 번 누르면 됨. 오류 없음. 19 실험 ①: 328ms 클릭 → `장바구니 0` | 하이드레이션 전 | 리스너는 하이드레이션 때 붙음. React 18 이후 이산 이벤트를 재생하지 않음(경계 코드가 이미 있으면 그 자리에서 동기 하이드레이션해 처리 — 19 실험 ②-b, 코드가 없으면 클릭이 사라짐) | RUM에서 첫 상호작용 시각 < 하이드레이션 완료 시각인 세션 비율 | [19-1](../19-hydration-cost-and-partial-hydration/2-summary.md) |
| 리뷰 영역 버튼이 처음 한 번만 반응 안 함. 19 실험 ②-a: 청크 대기 중 클릭은 청크 도착 뒤에도 `리뷰 0` | 하이드레이션(지연 로드 경계) | 경계 코드가 없어 동기 하이드레이션 불가, 이산 이벤트 미재생 | 그 경계가 `lazy`인가, 청크 도착 시각 | [19-4](../19-hydration-cost-and-partial-hydration/2-summary.md) |
| 로드 직후 몇 초간 스크롤·입력 버벅임, TBT 증가. 19 실험 ③ full n=5000: 최장 태스크 446~618ms | 하이드레이션(메인 스레드) | 정적 부분까지 한 번에 하이드레이션 | Performance 패널의 로드 직후 긴 태스크 안 React 작업 | [19-2](../19-hydration-cost-and-partial-hydration/2-summary.md) |
| 문서가 수백 KB, 느린 망에서 FCP 늦음. HTML 끝의 큰 `<script>` JSON. 19 실험 ③: full 593,744B vs island 250,446B. 10 실험: 마크업 109,251B + JSON 87,981B | SSR(직렬화) | 쓰지 않는 필드까지 직렬화, 같은 데이터 이중 삽입 | 문서 크기 중 상태 JSON 비율 | [19-3](../19-hydration-cost-and-partial-hydration/2-summary.md) |
| 서버 컴포넌트 도입 뒤에도 번들·하이드레이션 시간 그대로, 번들에 마크다운 파서·날짜 라이브러리 | 앱(경계 배치) | 상위 레이아웃에 `'use client'` | 번들 분석에 서버 전용이어야 할 모듈 | [19-5](../19-hydration-cost-and-partial-hydration/2-summary.md) |

- SSR 응답 캐시의 교차 노출(10-2)·모듈 전역 누출(10-5)은 보안 사고라서 §11에 따로 둔다.

### 11. 다른 사용자 데이터가 보인다·데이터가 사라진다·토큰이 샜다

먼저 **누가 응답했는지**(캐시인가 서버인가)와 **언제부터인지**를 본다. 교차 노출은 성능 장애가 아니라 개인정보 사고로 다룬다.

| 보이는 것 (메시지·지표·판) | 계층 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|---|
| "다른 사람 계정이 보여요", 서버 로그에 B의 요청 없음. 10 실험: `cookie user=bob /me → alice님의 주문 내역`. 실사건 Steam 2015-12-25([24](../24-web-incidents/2-summary.md)) | 공유 캐시(CDN·프록시·앱 메모리) | 쿠키에 따라 다른 HTML을 URL만 키로 캐시 | 응답 헤더의 `Cache-Control`·`Age`·CDN 캐시 상태, 캐시 키 규칙 | [10-2](../10-rendering-strategies/2-summary.md) |
| 간헐적으로 다른 사용자 정보가 섞임, 캐시를 꺼도 생김, 부하가 높을 때만 | SSR 서버(동시성) | `let currentUser` 같은 모듈 전역에 요청 정보 | 동시 요청 부하 테스트에서 "응답 속 사용자 ID = 요청 사용자 ID" 검사 | [10-5](../10-rendering-strategies/2-summary.md) |
| 로그아웃 뒤 같은 기기의 다른 사용자가 이전 사용자 화면 일부를 봄, Cache storage에 `/api/me` | 서비스 워커(런타임 캐시) | 런타임 캐시가 인증 API까지 담음 | Application → Cache storage 항목 목록 | [07-5](../07-service-workers-and-offline/2-summary.md) |
| 계정 탈취 신고, 서버 로그에 낯선 IP·User-Agent의 정상 인증 요청, 프론트엔드 로그는 빈칸 | 앱(토큰 저장 위치) + 공급망 | 변조된 서드파티 스크립트·XSS가 `localStorage`의 토큰을 읽어 보냄 | 페이지가 싣는 스크립트 목록·변경 이력, 토큰 저장 위치 | [06-1](../06-browser-storage/2-summary.md) |
| 한동안 안 쓴 iPhone 사용자의 오프라인 초안이 없어짐, IndexedDB 비어 있음, SW 재설치, 오류 로그 없음 | 브라우저 정책(Safari) | 사용자 상호작용 없이 Safari 사용 7일이 지나면 스크립트가 쓴 저장소 삭제(WebKit 2020-03-24) | 마지막 방문일, 브라우저 | [06-3](../06-browser-storage/2-summary.md) |
| 디스크가 거의 찬 기기에서 오프라인 데이터 전체 소실, `navigator.storage.persisted()` false | 브라우저 저장소(축출) | best-effort 버킷은 공간 압박 시 통째 삭제(Storage 표준) | `persisted()`·`estimate()` 값을 RUM에 | [06-4](../06-browser-storage/2-summary.md) |
| 일정 시간 쓰면 오프라인 저장 실패, `cache.put`이 `QuotaExceededError` | 서비스 워커(Cache Storage) | Cache Storage에 만료 없음, 쿼리마다 항목 누적 | Application → Storage 사용량, 캐시별 항목 수 | [07-4](../07-service-workers-and-offline/2-summary.md) |

- 06-1의 "변조된 서드파티 스크립트"가 실제로 일어난 모습은 [24](../24-web-incidents/2-summary.md)의 British Airways 2018·polyfill.io 2024다. 그 노트의 실험은 SRI·CSP가 무엇을 막고 무엇을 못 막는지 보인다.

### 12. 화면 값이 틀리거나 안 바뀐다 — 오류 없는 상태 버그

| 보이는 것 (메시지·지표·판) | 계층 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|---|
| 프로필 이름을 바꿨는데 헤더엔 옛 이름, 새로고침하면 맞음. 21 실험 ③: 키 캐시 `김영희`, 전역 복사본 `김철수` | 앱(서버 상태) | 서버 데이터를 전역 스토어에 복사, 무효화 경로 누락 | 같은 값을 들고 있는 곳이 몇 군데인가 | [21-1](../21-component-and-state-patterns/2-summary.md) |
| 다른 상품을 골랐는데 편집 폼엔 이전 값. 21 실험 ②: 부모 2000, 자식 1000 | 앱(파생 상태) | `useState(prop)` — 인자는 첫 렌더에만 쓰임 | prop을 state로 복사한 곳 | [21-2](../21-component-and-state-patterns/2-summary.md) |
| 입력이 갑자기 고정되거나 콘솔 `A component is changing an uncontrolled input to be controlled.` / `You provided a \`value\` prop to a form field without an \`onChange\` handler.` | 앱(폼) | `value`가 `undefined`로 시작, `onChange` 누락 | 개발 콘솔 경고, 초기값 | [21-5](../21-component-and-state-patterns/2-summary.md) |
| `items.push(x); setItems(items)` 뒤 화면 그대로 | 앱(불변 갱신) | 같은 참조 → `Object.is`로 "같음" | 갱신 코드가 새 배열·객체를 만드나 | [18-4](../18-ui-rerender-and-memoization/2-summary.md) |
| 정렬 뒤 입력 중이던 값이 다른 행으로 옮겨 감·사라짐, 매 렌더 DOM 재생성 | 앱(재조정 key) | 인덱스 key, `Math.random()` key | 목록의 `key` 값 | [18-5](../18-ui-rerender-and-memoization/2-summary.md) |
| 값 하나 추가하는데 중간 컴포넌트 9개의 props를 고침, 리뷰 diff가 넓음(런타임 오류 없음 — 변경 비용으로 보이는 증상) | 앱(컴포넌트 구조) | 상태를 너무 위로 끌어올림, 합성 대신 깊은 계층 | 쓰지 않는 props를 받아 넘기기만 하는 중간 컴포넌트 수 | [21-4](../21-component-and-state-patterns/2-summary.md) |
| 헤더와 사이드바의 장바구니 수가 가끔 다름, 같은 API 두 번. 22 실험 ③ bundled: `/api/cart` 2회 | 마이크로 프론트엔드·섬 | 섬마다 저장소 코드 두 벌 | Network의 같은 URL 요청 수 | [22-4](../22-islands-and-micro-frontends/2-summary.md) |
| 팀 B 배포 뒤 팀 C 영역에서 `TypeError: Cannot read properties of undefined`, 팀 C 저장소엔 변경 없음 | 마이크로 프론트엔드(계약) | `window.appState` 같은 전역 객체가 문서화 안 된 계약 | 오류 스택의 전역 객체 접근, 다른 팀 배포 시각 | [22-3](../22-islands-and-micro-frontends/2-summary.md) |
| 무한 스크롤 피드에서 같은 글 두 번·빠짐 | 데이터 로드(페이지네이션) | offset 중 새 항목이 앞에 끼어 경계가 밀림 — 가상화와 무관 | 받은 ID 목록의 중복 수 | [17-4](../17-list-virtualization/2-summary.md) |

### 13. 키보드·스크린리더로 쓸 수 없다

먼저 **마우스 없이 Tab·Enter·Space로** 같은 흐름을 끝까지 해 보고, 막힌 요소의 **접근성 트리 노드**(역할·이름·ignored)를 본다. 자동 검사 통과는 증거가 아니다(11 실험에서 axe가 div 버튼을 못 잡음).

| 보이는 것 (메시지·지표·판) | 계층 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|---|
| 키보드로 "결제하기"에 도달 못 함, Tab이 건너뜀, 접근성 트리 `generic`·이름 없음. 11 실험 `#divbtn` clicks=[] | 마크업(시맨틱) | `div` + `onclick` — 역할·포커스·키보드 활성화 없음 | DevTools Accessibility 패널의 역할, Tab 순서 | [11-1](../11-accessibility-basics/2-summary.md) |
| 스크린리더가 엉뚱한 역할을 읽거나 포커스가 갔는데 침묵, axe `aria-hidden-focus` 등, 트리에서 `ignored=true`인데 Tab이 멈춤(11 실험 `#ghost`) | ARIA | 배경에 `aria-hidden`만 걸고 포커스는 그대로, 지키지 않을 `role="menu"` | 접근성 트리의 ignored 노드에 포커스가 가나 | [11-2](../11-accessibility-basics/2-summary.md) |
| Tab을 누르면 뭔가 움직이는데 위치가 안 보임, CSS 리셋에 `*:focus { outline: none }` | CSS | 포커스 표시 일괄 제거(WCAG 2.4.7 위반) | Tab을 누르며 화면 확인, 스타일의 `outline` | [11-3](../11-accessibility-basics/2-summary.md) |
| SPA 화면 전환 뒤 스크린리더 침묵, `document.activeElement`가 `body` | 앱(라우팅) | 전체 페이지 로드가 없으니 새 문서를 알리지 않음 | 전환 직후 `document.activeElement` | [11-4](../11-accessibility-basics/2-summary.md) |
| "버튼", "편집"만 읽힘, axe `button-name`·`label`·`link-name`, 트리 이름 `""`(11 실험 `#iconbtn`) | 마크업(접근 가능한 이름) | 아이콘만 넣고 텍스트 대안 없음, placeholder를 레이블 대신 | 접근성 트리의 이름 칸 | [11-5](../11-accessibility-basics/2-summary.md) |
| Ctrl+F로 안 찾아짐, 스크린리더가 "목록, 32개 항목". 17 실험: `window.find('Row 9999')` = `false`, 트리에 행 32개 | 앱(가상화) | 가상화가 DOM에서 행을 뺌 | 접근성 트리의 행 수 vs 데이터 행 수 | [17-3](../17-list-virtualization/2-summary.md) |

### 14. 특정 언어·지역에서만 깨진다

| 보이는 것 (메시지·지표·판) | 계층 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|---|
| 번역 화면에 문법이 틀린 문장, 번역 파일에 "총 ", "개 상품" 같은 조각 키 | 앱(메시지 조립) | 문장을 코드에서 이어 붙임 | 카탈로그의 조각 키 | [12-1](../12-internationalization-and-localization/2-summary.md) |
| "1 items", 러시아어 "21 товаров" | 앱(복수형) | `n === 1 ? 단수 : 복수`. 12 실험 5: ru 21=one, 22=few, pl 21=many | `Intl.PluralRules(locale).select(n)`과 화면 문구 대조 | [12-2](../12-internationalization-and-localization/2-summary.md) |
| 독일 사용자의 `1.234,5`€가 1.23€로 결제, 에러 없음. 12 실험 4: `parseFloat("1.234,5") = 1.234` | 앱·서버(숫자 파싱) | `parseFloat`·서버 기본 로캘 파서 | 전송 형식이 로캘 무관인가 | [12-3](../12-internationalization-and-localization/2-summary.md) |
| 자정 근처 주문만 날짜가 하루 어긋남. 12 실험 6: 같은 순간이 뉴욕 3/1, 서울 3/2 | 앱·서버(시간대) | 순간을 UTC 날짜로 자르거나 서버 시간대로 표시 | 저장된 값이 순간(UTC)+시간대인가 | [12-4](../12-internationalization-and-localization/2-summary.md) |
| 한 단어 이름·여러 단어 성·비라틴 이름 사용자가 가입 못 함, "영문만 입력" | 폼 검증·스키마 | 한 문화의 이름 구조를 규칙으로 박음 | 국가별 가입 이탈, 검증 정규식 | [12-5](../12-internationalization-and-localization/2-summary.md) |

### 15. 메모리가 계속 는다·탭이 재로드된다

먼저 **같은 동작을 N번 반복한 뒤 GC를 하고** `Nodes`·`JSEventListeners`·힙 크기가 원래로 돌아오는지 본다.

| 보이는 것 (메시지·지표·판) | 계층 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|---|
| SPA를 오래 쓰면 느려지고 재로드, 화면 전환마다 GC 뒤에도 선형 증가. 04 실험: 300회 → 리스너 +300, 노드 +15,900, 힙 스냅샷에 Detached `HTMLDivElement` | DOM·리스너 수명 | 전역 대상 리스너를 언마운트 때 안 뗌, `removeEventListener`에 다른 함수 참조 | 전환 N회 뒤 `JSEventListeners`·`Nodes`(CDP 메트릭), 힙 스냅샷 Detached 필터 | [04-1](../04-dom-and-event-model/2-summary.md) |
| 광고·임베드가 많은 페이지에서 저사양 기기 탭이 자주 재로드, 작업 관리자에 "Subframe: https://…" 행 다수 | 브라우저 프로세스(사이트 격리) | 부모와 다른 사이트의 iframe은 OOPIF 렌더러로 감 — iframe 수가 아니라 다른 사이트 수만큼 늚(01 실험: +1) | 작업 관리자의 iframe 행 수와 메모리 합 | [01-3](../01-browser-architecture/2-summary.md) |
| 탭 재로드·스크롤 느림, 레이어 수백 개 | 합성 | `will-change` 남발 | Layers 패널 | [02-4](../02-rendering-pipeline/2-summary.md) |
| 렌더러 RSS가 큼. 17 실험: 약 321MB(가상화 117MB) | DOM 크기 | 1만 행 DOM | 가상화 전후 메모리 | [17-1](../17-list-virtualization/2-summary.md) |

### 16. 이벤트가 안 잡힌다·로직이 멈춘다

| 보이는 것 (메시지·지표·판) | 계층 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|---|
| 특정 컴포넌트 안 클릭만 분석 로그 누락, "바깥 클릭 닫기" 안 됨. 04 실험: 위임 쪽 ③ X | DOM 이벤트 전파 | 하위 컴포넌트의 `e.stopPropagation()` | Elements → Event Listeners, 그 영역의 `stopPropagation` 호출 | [04-2](../04-dom-and-event-model/2-summary.md) |
| 무한 스크롤·필터 뒤 새 행이 반응 안 함. 04 실험: 개별 방식 ② X | DOM 이벤트(리스너 위치) | 최초 렌더 요소에만 리스너, `innerHTML`로 다시 그림 | 새 요소에 리스너가 있나(Event Listeners 탭) | [04-3](../04-dom-and-event-model/2-summary.md) |
| 폼 컨테이너의 `focus`·`blur` 리스너가 한 번도 안 불림 | DOM 이벤트(버블 여부) | `focus`·`blur`는 `bubbles=false` | 이벤트의 `bubbles` 값 | [04-4](../04-dom-and-event-model/2-summary.md) |
| 탭을 돌렸다 오면 진행 표시·폴링이 멈춰 있음 | 이벤트 루프(렌더링 업데이트) | 숨겨진 문서는 렌더링 업데이트에서 빠지고, rAF는 그 안에서 돎 | 비시각 로직이 rAF에 있나 | [03-4](../03-event-loop/2-summary.md) |
| 탭 간 동기화가 기기·판마다 다르게 동작(한쪽이 무거울 때 다른 쪽도 느려지거나 아님) | 브라우저 프로세스 배치 | 같은 프로세스를 전제한 설계 — 배치는 브라우저 구현 | 같은 시나리오를 기기·판별로 재현 | [01-4](../01-browser-architecture/2-summary.md) |

### 17. 번들·워커·마이크로 프론트엔드 — 같은 라이브러리 두 벌, 실행 환경 차이, 팀 간 충돌

| 보이는 것 (메시지·지표·판) | 계층 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|---|
| React "Invalid hook call", 상태 공유 라이브러리 상태가 둘로 갈림, 번들 분석에 같은 패키지 두 경로·두 판 | 번들(의존 해석) | 중복 설치, 마이크로 프론트엔드별 사본 | `npm ls <패키지>`, 번들 분석 | [09-5](../09-js-modules-and-bundling/2-summary.md) |
| 원격 위젯 자리에 오류, `TypeError: Cannot read properties of null (reading 'useState')`, `Minified React error #321`. 22 실험 ①: selfmount JS 388,968B vs shared 194,926B | 마이크로 프론트엔드 런타임 | 원격 번들이 자기 React를 품음 → 디스패처 어긋남 | 로드된 `react-dom` 사본 수 | [22-1](../22-islands-and-micro-frontends/2-summary.md) |
| 메인에서 쓰던 유틸을 워커로 옮기자 워커 `error` 이벤트, 콘솔 `ReferenceError: document is not defined`(16 실험 출력). 함수·DOM 노드를 메시지에 넣으면 `DataCloneError` | 웹 워커 전역 | 워커 전역(`DedicatedWorkerGlobalScope`)에는 DOM이 없음 | 의존 라이브러리가 `window`·`document`를 참조하나 | [16-3](../16-long-tasks-and-web-workers/2-summary.md) |
| 다른 팀 배포 뒤 우리 버튼 색·여백이 바뀜, 우리 코드 변경 없음. 22 실험 ②: 팀 A 버튼 `rgb(255, 0, 0)` | CSS 캐스케이드 | 같은 클래스·같은 명시도면(출처·`!important`·`@layer`도 같을 때) 나중 규칙이 이김 | Computed 패널에서 이긴 규칙의 스타일시트 | [22-2](../22-islands-and-micro-frontends/2-summary.md) |

### 18. 측정이 거짓말한다 — 랩·대시보드·RUM·게이트

| 보이는 것 (메시지·지표·판) | 계층 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|---|
| CI Lighthouse 95인데 Search Console 모바일 LCP "개선 필요". 08 실험: 같은 페이지가 CPU·망에 따라 0.25s → 7.9s | 측정(랩 vs 필드) | 랩은 고정된 한 조건(기기 하나·망 하나) — 실제 사용자 분포를 대표하지 못함 | CrUX·RUM p75를 모바일·데스크톱으로 나눠 보기 | [08-1](../08-web-performance-vitals/2-summary.md) |
| CI 게이트 초록인데 CrUX p75 LCP·INP "개선 필요" | 측정(랩 조건) | 랩에 로그인·개인화·광고·서드파티 없음. INP는 상호작용이 있어야 나옴(랩은 TBT로 대신) | 랩 시나리오와 실제 사용자 흐름 비교 | [20-4](../20-performance-budgets-and-regression-gates/2-summary.md) |
| "평균 LCP 1.4초"는 좋은데 불만 계속. 08 실험: p50 0.3s vs p75 2.1s | 측정(집계) | 평균·중앙값, 페이지별 p75의 평균 | 원자료·히스토그램을 합쳐 다시 계산한 p75 | [08-4](../08-web-performance-vitals/2-summary.md) |
| INP·CLS 보고가 모바일에서 크게 빠짐, SPA 화면 전환 뒤 LCP가 첫 화면 값 그대로 | 측정(RUM 전송) | `unload`에서 전송(모바일에서 안 불리는 경우), 기본 설정에서는 SPA 전환이 새 탐색이 아님(Chrome 151+·`web-vitals` `reportSoftNavs`로 전환별 측정 가능) | 수집 서버의 지표별 건수, 전송 시점 코드 | [08-5](../08-web-performance-vitals/2-summary.md) |
| 문서 수정 PR에서 성능 게이트 실패, 재실행하면 통과. 20 실험 A/A: 단일 실행 + 5% 허용이 15번 중 3번 오탐 | CI(노이즈) | 단일 실행·좁은 허용 폭·공유 러너 | A/A로 노이즈 폭 측정 | [20-2](../20-performance-budgets-and-regression-gates/2-summary.md) |

## 쓰이는 자료구조·알고리즘

- **역색인(해시 맵: 증상 → leaf 목록)**: 이 노트 자체다. 키는 "보이는 형태"(메시지 원문·지표 이름), 값은 `NN-k` 목록이다. 같은 키에 값이 여럿이면(예: "흰 화면" → 6개) 키 하나로 끝나지 않는다. 두 번째 키(콘솔 원문·시각·대상)로 좁힌다. → [data-structure 영역 표](../../data-structure/curriculum.md)(해시 테이블)
- **결정 트리**: 각 절의 ASCII 분기도다. 질문 하나(콘솔에 줄이 있나, 언제, 누구에게)로 후보를 나눈다. 싼 질문(콘솔 보기)을 먼저, 비싼 질문(트레이스 분석·재현 환경 구성)을 나중에 둔다.
- **이진 탐색(배포 이분)**: "배포 직후부터"인 증상은 배포 이력에서 범위를 반씩 줄여 원인 변경을 찾는다. `git bisect`가 같은 방식이다. 성능 회귀는 측정 노이즈 때문에 한 번 측정으로 좋음·나쁨을 정하기 어렵다. 그래서 각 단계를 반복 측정의 중앙값으로 판정한다([20-2](../20-performance-budgets-and-regression-gates/2-summary.md)). → [algorithm/06 이분 탐색](../../algorithm/06-binary-search/2-summary.md)
- **백분위(p75)·분포**: "평균은 좋은데 불만"을 가르는 도구다. 백분위는 원자료나 히스토그램을 합친 뒤 다시 구한다(08-4).
- **트리 순회**: 접근성 트리·DOM 트리·컴포넌트 트리를 따라 "어느 노드가 이상한가"를 찾는다. Detached 노드 찾기(04-1)는 힙 그래프에서 DOM 트리에 연결되지 않은 노드를 찾는 일이다.

## 적용 — 풀어나가는 법

### 순서 — 증상 하나를 받았을 때

1. **보인 계층과 원문을 적는다.** 고객 말("버튼이 안 눌려요")을 그대로 쓰지 않고, 콘솔 원문·Network 한 줄·지표 이름으로 바꾼다(0-1 표).
2. **언제·누구에게를 적는다.** 첫 로드/로드 직후/상호작용/오래 쓴 뒤/배포 직후, 기기·브라우저·언어(증상 지도).
3. **이 노트의 절로 간다.** 표의 "보이는 것" 칸에서 가장 가까운 행을 찾고, "첫 진단" 칸을 한다.
4. **leaf에서 원인과 대처를 읽는다.** leaf의 실험을 로컬에서 다시 돌려 같은 신호가 나는지 본다.
5. **대처 뒤 같은 신호로 확인한다.** 고친 뒤에도 같은 수집기·같은 백분위로 본다. 랩 1회로 닫지 않는다(장애 시나리오 3).

### 첫 진단 도구 — 무엇을 어디서 보나

| 질문 | 도구(Chrome DevTools 기준) | 이 노트에서 쓰는 절 |
|---|---|---|
| 무슨 예외·경고가 났나 | Console(원문), `error`·`unhandledrejection` 수집 | §1 §8 §9 §10 §17 |
| 요청이 갔나, 누가 응답했나 | Network: 상태, Size(`(ServiceWorker)`·`(disk cache)`), Priority, Initiator | §1 §6 §8 §9 §11 |
| 메인 스레드가 무엇을 했나 | Performance: 긴 태스크(빨간 삼각형), Layout·Recalculate Style 막대, 강제 레이아웃 경고 | §2 §3 §4 §10 |
| 무엇이 움직였나·다시 칠해졌나 | Rendering 탭: Layout Shift Regions, Paint flashing, Layer borders, Scrolling Performance Issues | §4 §5 |
| 레이어가 몇 개인가 | Layers 패널 | §4 §15 |
| 서비스 워커·저장소 상태 | Application: Service Workers(waiting·redundant), Cache storage, Local Storage, Storage 사용량 | §1 §9 §11 |
| 메모리가 새나 | Memory: 힙 스냅샷(Detached 필터), CDP `Performance.getMetrics`의 `Nodes`·`JSEventListeners` | §15 |
| 안 쓰는 코드가 얼마인가 | Coverage 패널, 번들 분석(metafile) | §6 §17 |
| 키보드·스크린리더에 어떻게 보이나 | Accessibility 패널(역할·이름·ignored), Tab 순서 | §13 |
| 실제 사용자 값은 | CrUX·Search Console, RUM(`web-vitals` + attribution) | §3 §6 §18 |

- Rendering 탭 항목 이름은 Chrome for Developers "Discover issues with rendering performance" 문서 기준이다(Paint flashing, Layout Shift Regions, Layer borders, Frame rendering stats, Scrolling Performance Issues).

### RUM에 남겨 둘 것 — 위 실험의 수집기를 운영용으로

```ts
// 증상 색인의 "보이는 것" 칸을 운영에서 다시 볼 수 있게 남기는 최소 필드
type Signal =
  | { kind: 'fetch-not-ok'; url: string; status: number }            // 05-1
  | { kind: 'fetch-reject'; url: string; msg: string }               // 05-3·05-4 (CORS 이유는 콘솔에만 — URL을 남긴다)
  | { kind: 'dynamic-import-fail'; msg: string; build: string }      // 09-2 (어느 배포의 탭인가)
  | { kind: 'hydration-recoverable'; msg: string }                   // 10-1 (onRecoverableError)
  | { kind: 'inp'; value: number; inputDelay: number; processing: number; presentation: number } // 08-3·16
  | { kind: 'cls'; value: number; sources: string[] }               // 08-2·14-2·15-2
  | { kind: 'lcp'; value: number; element: string; url?: string }    // 13·14·15
  | { kind: 'sw'; controlled: boolean; scriptVersion?: string };     // 07-1

// 전송은 visibilitychange(hidden)에서 sendBeacon — unload에 기대지 않는다(08-5)
addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'hidden') navigator.sendBeacon('/rum', JSON.stringify(queue.splice(0)));
});
```

- `build`(배포 식별자)와 `sw.scriptVersion`을 함께 보내면 "옛 탭·옛 워커에서만"을 지표로 가를 수 있다(07-1·09-2). 이 필드 구성은 이 노트의 제안이다.

## 장애 시나리오와 대처

### 1. 같은 증상 이름으로 원인을 오판

- **현상**: "흰 화면" 신고에 렌더 차단 CSS를 줄였는데 그대로다.
- **보이는 형태**: 대처 뒤에도 같은 사용자군에서 같은 신고. 콘솔에는 처음부터 `ChunkLoadError`가 있었다.
- **원인**: 증상 이름 하나에 원인이 여럿이다(§1: 6갈래). 첫 질문(콘솔 원문·시각·대상)을 건너뛰었다.
- **대처**: 증상을 받으면 0-1의 여섯 가지를 먼저 채운다. 표에서 행을 고를 때 "보이는 것" 칸의 메시지·수치가 맞는지 대조한다.

### 2. 보인 계층만 보고 "우리 문제 아님"으로 닫음

- **현상**: 프론트엔드 팀은 CORS 에러를 "서버 설정 문제"로 넘겼고, 서버 팀은 "에러 로그 없음"으로 닫았다. 주문이 두 건씩 생겼다.
- **보이는 형태**: 콘솔 `blocked by CORS policy`, 서버 접근 로그에 같은 POST 두 번(05-3).
- **원인**: 콘솔에서 보인 에러를 "요청이 안 갔다"로 읽었다. 단순 요청은 서버까지 가서 처리될 수 있고, 막힌 것은 응답 읽기다.
- **대처**: 증상의 "보이는 자리"와 "원인 자리"를 따로 적는다(동작·원리 0). 서버 접근 로그에서 같은 요청을 찾아 처리 여부를 확인한다. 쓰기 요청엔 멱등 키를 둔다([reliability/13](../../reliability/13-idempotency/2-summary.md)).

### 3. 랩에서 재현이 안 돼서 닫음

- **현상**: "INP 나쁨" 신고를 개발자 노트북에서 재현하지 못해 "재현 불가"로 닫았다.
- **보이는 형태**: 랩 Lighthouse 초록, CrUX 모바일 p75 "개선 필요"(08-1·20-4).
- **원인**: 랩은 고정된 한 조건(기기 하나·망 하나)이다. 개발자 PC 무스로틀이든 Lighthouse 기본 모바일(CPU 4×·느린 4G 시뮬레이션)이든 실제 사용자 분포 전체를 대표하지 못한다. INP는 상호작용이 있어야 생기므로 페이지 로드 랩 측정에 안 잡힌다.
- **대처**: CPU 4×·느린 망 스로틀로 다시 잰다. RUM의 기기·망 차원에서 나쁜 구간을 찾고, 그 조건으로 재현한다. 닫기 전에 필드 p75를 확인한다.

### 4. 색인의 메시지로 검색했는데 안 나온다

- **현상**: 운영 로그에서 이 노트의 문구로 검색했는데 결과가 0건이다.
- **보이는 형태**: 같은 결함이 다른 문구로 찍혀 있다.
- **원인**: 메시지는 빌드·도구·브라우저 판마다 다르다. React는 개발 빌드가 `Hydration failed because …`, 운영 빌드가 `Minified React error #418`이다(10-1). 지워진 청크는 webpack이면 `ChunkLoadError`, 네이티브 ESM이면 `Failed to fetch dynamically imported module`이다(09-2). Lighthouse 감사 이름도 판에 따라 바뀐다(02-2). CORS 이유는 콘솔에만 있고 스크립트 예외는 `TypeError: Failed to fetch`뿐이다(위 실험 (2)).
- **대처**: 문구 대신 구조로 찾는다. 오류 코드(`#418`·`#321`), 예외 이름(`ChunkLoadError`·`QuotaExceededError`·`AbortError`), 요청 URL·상태 코드, 지표 이름으로 검색한다.

### 5. 증상 하나를 고쳤더니 다른 증상이 생김

- **현상**: 성능 개선 배포 뒤 다른 지표가 나빠졌다.
- **보이는 형태**: 이미지 전부에 lazy → LCP 1.47s → 5.4s(14-3). preload 추가 → LCP 0.63s → 1.55s(13-2). memo 전면 적용 → 효과 없음·stale closure(18-3). 정적 자원 cache-first를 HTML까지 → 옛 화면 고착(07-1). `font-display: optional` → 첫 방문에 웹 폰트를 못 볼 수 있음(15-2).
- **원인**: 처방마다 적용 범위(첫 화면 아래만·늦게 발견되는 핵심 자원만·비싼 곳만·해시 파일만)가 있다. 범위를 넘겨 일괄 적용했다.
- **대처**: 처방 전후로 **같은 수집기**로 LCP·INP·CLS를 함께 본다. 처방의 적용 범위를 leaf의 "대처" 칸에서 확인한다. 회귀 게이트에 세 지표를 함께 건다([20](../20-performance-budgets-and-regression-gates/2-summary.md)).

## 핵심 문장

- 증상 이름 하나에 원인이 여럿이다. "흰 화면"은 차단 자원·CSR·옛 청크·저장 예외·SW·폰트로 갈린다. 콘솔 원문·시각·대상이 그 갈림길이다.
- 보이는 자리와 원인 자리가 다르다. CORS 에러는 콘솔에 보이지만, 단순 요청이면 요청은 이미 서버에 갔다(처리됐을 수 있다).
- 프론트엔드 장애의 상당수는 예외 없이 진행된다. 클릭 무시·레이아웃 이동·옛 버전·교차 노출은 지표·트레이스·고객 문의로만 보인다.
- 같은 결함이 신호 두 개로 잡힌다. 300ms 클릭 핸들러는 `longtask`와 Event Timing `processing`에 함께 찍혔다. 어느 조각이 큰지가 처방을 고른다.
- 스크립트가 받는 예외에는 이유가 빠져 있다. CORS는 `TypeError: Failed to fetch`뿐이고 이유는 DevTools 콘솔에만 있다. RUM에는 URL·상태·배포 식별자를 함께 남긴다.
- 처방에는 적용 범위가 있다. lazy·preload·memo·cache-first를 범위 밖까지 일괄 적용하면 다른 증상이 생긴다.

## 관련 주제·근거

- 선행(이 영역 전체 — 색인의 출처)
  - 16.1 원리: [01 브라우저 아키텍처](../01-browser-architecture/2-summary.md) · [02 렌더링 파이프라인](../02-rendering-pipeline/2-summary.md) · [03 이벤트 루프](../03-event-loop/2-summary.md) · [04 DOM·이벤트 모델](../04-dom-and-event-model/2-summary.md) · [05 브라우저의 fetch](../05-fetch-from-browser/2-summary.md) · [06 브라우저 저장소](../06-browser-storage/2-summary.md) · [07 서비스 워커](../07-service-workers-and-offline/2-summary.md) · [09 모듈·번들링](../09-js-modules-and-bundling/2-summary.md) · [10 렌더링 전략](../10-rendering-strategies/2-summary.md) · [11 접근성](../11-accessibility-basics/2-summary.md) · [12 국제화](../12-internationalization-and-localization/2-summary.md)
  - 16.2 성능: [08 웹 바이탈](../08-web-performance-vitals/2-summary.md) · [13 크리티컬 패스](../13-critical-path-and-resource-loading/2-summary.md) · [14 이미지](../14-image-optimization/2-summary.md) · [15 웹 폰트](../15-web-font-loading/2-summary.md) · [16 긴 태스크·워커](../16-long-tasks-and-web-workers/2-summary.md) · [17 목록 가상화](../17-list-virtualization/2-summary.md) · [18 재렌더·메모이제이션](../18-ui-rerender-and-memoization/2-summary.md) · [19 하이드레이션 비용](../19-hydration-cost-and-partial-hydration/2-summary.md) · [20 성능 예산](../20-performance-budgets-and-regression-gates/2-summary.md)
  - 16.3 설계: [21 컴포넌트·상태 패턴](../21-component-and-state-patterns/2-summary.md) · [22 Islands·마이크로 프론트엔드](../22-islands-and-micro-frontends/2-summary.md)
- 후속: [24 실사건](../24-web-incidents/2-summary.md) — 변조된 스크립트(06-1)·공유 캐시 교차 노출(10-2)이 실제로 일어난 모습
- 다른 영역의 증상 색인(같은 형식): [api-design/28](../../api-design/28-api-symptom-index/2-summary.md) · [network/52](../../network/52-network-symptom-index/2-summary.md) · [reliability/52](../../reliability/52-reliability-symptom-index/2-summary.md). [security 29](../../security/29-security-symptom-index/2-summary.md)(증상 색인 — CORS 에러 등)
- 다른 영역: [network/34 HTTP 캐시](../../network/34-http-caching/2-summary.md)(10-2·14-4의 캐시 키), [reliability/13 멱등성](../../reliability/13-idempotency/2-summary.md)(05-3), [reliability/05 타임아웃](../../reliability/05-timeouts-and-deadline-propagation/2-summary.md)(05-2·10-4), [api-design/06 페이지네이션](../../api-design/06-pagination/2-summary.md)(17-4), [algorithm/06 이분 탐색](../../algorithm/06-binary-search/2-summary.md)
- Web API 문법(읽기 전용 레퍼런스): [web-api/10 layout thrashing](../../../languages/web-api/10-layout-thrashing/) · [web-api/19 passive](../../../languages/web-api/19-passive-and-scroll/) · [web-api/20 리스너 수명](../../../languages/web-api/20-listener-lifetime/) · [web-api/27 abort·timeout](../../../languages/web-api/27-abort-and-timeout/) · [web-api/28 CORS](../../../languages/web-api/28-cors-simple-and-preflight/) · [web-api/29 credentials](../../../languages/web-api/29-credentials-and-cookies/)
- 문서
  - web.dev "Largest Contentful Paint (LCP)" <https://web.dev/articles/lcp> — LCP에서 빠지는 요소("Placeholder images or other images with a low entropy" 등)
  - Chrome for Developers "Discover issues with rendering performance" <https://developer.chrome.com/docs/devtools/rendering/performance> — Rendering 탭 항목
  - 각 행의 메시지·수치의 근거는 해당 leaf의 「관련 주제·근거」에 있다(표준 절·소스 경로·실험 조건).
- 실험 목록
  - 23-A 결함 다섯 개 + 크기 없는 이미지를 한 페이지에 심고 공통 수집기로 분류 — 로컬 Node `http` 서버 두 개(127.0.0.1, 포트 다름), Playwright `playwright-core` + `/usr/bin/google-chrome` 151.0.7922.173 headless, 뷰포트 800×600, 스로틀 없음, 4회 실행(긴 태스크 301~302ms, 클릭 duration 304ms, CLS 0.0202 동일). 2026-10-04. 사실 점검에서 3회 다시 돌려 같은 분류·같은 범위를 확인했다.
