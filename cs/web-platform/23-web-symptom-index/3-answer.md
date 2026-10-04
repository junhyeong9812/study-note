# web-platform/23-web-symptom-index — 정답

## 정답

### 1. 보이는 자리 ≠ 원인 자리

| 증상 | 보이는 곳 | 원인이 있는 곳 | leaf |
|---|---|---|---|
| CORS 에러 | 브라우저 콘솔 `blocked by CORS policy` | 서버 CORS 설정. 단순 요청이면 요청은 이미 서버에 갔다 — 처리됐을 수 있다(중복 주문). 처리 여부는 서버 로그로 확인한다 | [05-3](../05-fetch-from-browser/2-summary.md) |
| 옛 화면 고착 | 사용자 화면(서버 로그엔 그 사용자의 HTML 요청 없음) | 서비스 워커의 cache-first HTML, waiting 워커 | [07-1](../07-service-workers-and-offline/2-summary.md) |
| 다른 사람 계정 노출 | 고객 문의(서버 로그엔 B의 요청 없음) | 쿠키를 키에 넣지 않은 공유 캐시, 또는 SSR 모듈 전역 변수 | [10-2](../10-rendering-strategies/2-summary.md) · [10-5](../10-rendering-strategies/2-summary.md) |

- 보인 계층만 보면 "우리 문제 아님"으로 닫기 쉽다(장애 시나리오 2).
- 시작 시각은 원인 쪽 변경(배포·CDN 설정·도구 판 변경)과 맞물리는지 확인하는 데 쓴다.

### 2. 흰 화면 여섯 갈래

| 갈림 신호 | 원인 | leaf |
|---|---|---|
| HTML은 왔고 첫 페인트 직전에 끝나는 CSS·동기 JS | 렌더·파서 차단 자원 | [02-2](../02-rendering-pipeline/2-summary.md) · [13-1](../13-critical-path-and-resource-loading/2-summary.md) |
| 페이지 소스가 `<div id="root"></div>`뿐 | CSR 직렬 대기(10 실험 FCP·LCP 3.7~4.4초) | [10-3](../10-rendering-strategies/2-summary.md) |
| 콘솔 `ChunkLoadError`·`Failed to fetch dynamically imported module`, 청크 404 | 배포가 옛 청크를 지움 | [09-2](../09-js-modules-and-bundling/2-summary.md) |
| 특정 사용자만, 콘솔 `QuotaExceededError` | 초기화 중 저장 예외 | [06-2](../06-browser-storage/2-summary.md) |
| 오프라인에서만, `controlled=false` | 서비스 워커 미제어·HTML 미캐시 | [07-3](../07-service-workers-and-offline/2-summary.md) |
| 레이아웃은 있는데 글자만 없음 | 폰트 block 기간(FOIT — 15 실험 `block` 3초, Chrome `auto` 2초) | [15-1](../15-web-font-loading/2-summary.md) |

### 3. 같은 "실패"가 앱에 오는 세 형태

- (가) 500: `then`으로 `ok:false`인 응답이 왔다. 예외가 없다. 감싼 `fetch`가 `fetch-not-ok`로 따로 셌다([05-1](../05-fetch-from-browser/2-summary.md)).
- (나) CORS: 앱에는 `TypeError: Failed to fetch`만 왔다. `… has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.`는 **DevTools 콘솔에만** 있었다.
- (다) 지워진 청크: `TypeError: Failed to fetch dynamically imported module: http://127.0.0.1:PORT/assets/chart-OLDHASH.js`. webpack 런타임이면 `ChunkLoadError`로 보인다([09-2](../09-js-modules-and-bundling/2-summary.md)).
- RUM에는 예외 문구만이 아니라 요청 URL·상태 코드·배포 식별자를 함께 남긴다. 그래야 CORS(교차 출처 URL)와 옛 탭(배포 식별자)을 가를 수 있다.

### 4. 300ms 핸들러 — 신호 두 개

- `longtask` 301~302ms와 Event Timing `click`(`dur` 304, `processing` 300~301, `inputDelay` 2~3ms)에 함께 잡혔다(4회 실행).
- 큰 조각은 **processing**이다 → 핸들러 자체가 무겁다([08-3](../08-web-performance-vitals/2-summary.md), [16-1](../16-long-tasks-and-web-workers/2-summary.md)).
- input delay가 컸다면 클릭 **앞의** 다른 긴 태스크를 의심한다. 로드 직후라면 하이드레이션([19-2](../19-hydration-cost-and-partial-hydration/2-summary.md)), 저장 버튼 근처라면 동기 localStorage([06-5](../06-browser-storage/2-summary.md)), 그 밖의 앞선 작업([03-1](../03-event-loop/2-summary.md), 03 실험 249ms).

### 5. "버튼이 안 눌린다" 세 갈래

| 말 | 원인 | 보이는 형태 | leaf |
|---|---|---|---|
| (가) 늦게라도 반응 | 긴 태스크·무거운 핸들러·큰 재렌더 | INP p75 200ms 초과, Event Timing 조각 | [16-1](../16-long-tasks-and-web-workers/2-summary.md) · [08-3](../08-web-performance-vitals/2-summary.md) · [18-1](../18-ui-rerender-and-memoization/2-summary.md) · [21-3](../21-component-and-state-patterns/2-summary.md) |
| (나) 오류 없이 무시 | 하이드레이션 전 클릭(리스너가 아직 없음, React 18부터 이산 이벤트 미재생 — 경계 코드가 이미 있으면 동기 하이드레이션 뒤 처리되고, 코드가 없을 때 사라짐), 지연 로드 경계 | 19 실험 ①: 328ms 클릭 → `장바구니 0`, ②-a: `리뷰 0` | [19-1](../19-hydration-cost-and-partial-hydration/2-summary.md) · [19-4](../19-hydration-cost-and-partial-hydration/2-summary.md) |
| (다) 키보드로만 안 됨 | `div` + `onclick` — 포커스·키보드 활성화 없음 | 접근성 트리 `generic`, 11 실험 `#divbtn` clicks=[] | [11-1](../11-accessibility-basics/2-summary.md) |

- (나)와 (다)는 INP에 나쁘게 잡히지 않을 수 있다. "반응 없음"은 RUM의 첫 상호작용 시각·키보드 흐름 점검으로 찾는다.

### 6. 옛 화면 고착 — Size 칸과 비어 있는 서버 로그

- Network 탭의 **Size** 칸에 `(ServiceWorker)`가 보이면 서비스 워커가 응답했다. 서버 접근 로그에 그 사용자의 **HTML 요청이 없으면** 요청이 서버까지 오지 않았다([07-1](../07-service-workers-and-offline/2-summary.md)).
- 원인: HTML·해시 없는 `app.js`를 cache-first로 줬고, 새 워커는 탭이 열려 있는 동안 waiting에 머문다(07 실험 3·6).
- 09-2의 "실패 시 1회 새로고침"은 새 HTML을 받는다는 전제다. 서비스 워커가 cache-first로 옛 HTML을 주고 있으면 새로고침도 옛 HTML을 받는다. 그래서 HTML은 network-first로 두고 갱신 흐름(`skipWaiting`·갱신 배너)을 함께 점검한다.

### 7. LCP 분해 — 자원 로드 지연 vs 요소 렌더 지연

- 자원 로드 지연(요청 시작이 늦음)
  - 첫 화면 이미지에 lazy: 우선순위 Low로 시작, LCP 1.47s → 5.4s([14-3](../14-image-optimization/2-summary.md) · [13-3](../13-critical-path-and-resource-loading/2-summary.md)).
  - CSS 배경 등 늦은 발견: 이미지 요청 328ms, LCP 560ms — preload로 18ms·376ms([13-4](../13-critical-path-and-resource-loading/2-summary.md)).
  - preload 남발: 안 쓰는 preload 5장 → LCP 0.63s → 1.55s([13-2](../13-critical-path-and-resource-loading/2-summary.md)).
- 요소 렌더 지연(자원은 왔는데 그려지지 않음)
  - 텍스트 LCP가 폰트를 기다림: 15 실험 B, LCP 2016~2020ms([15-1](../15-web-font-loading/2-summary.md)).
  - JS가 돌아야 그려짐(CSR): FCP·LCP 3.7~4.4초([10-3](../10-rendering-strategies/2-summary.md)).

### 8. 문구 검색이 0건인 이유

- 메시지는 빌드·도구·브라우저 판마다 다르다.
  - React 하이드레이션 불일치: 개발 빌드 `Hydration failed because …`, 운영 빌드 `Minified React error #418`([10-1](../10-rendering-strategies/2-summary.md)).
  - 지워진 청크: webpack `ChunkLoadError`, 네이티브 ESM `Failed to fetch dynamically imported module`([09-2](../09-js-modules-and-bundling/2-summary.md)).
  - 그 밖에 Lighthouse 감사 이름이 판에 따라 다르고([02-2](../02-rendering-pipeline/2-summary.md)), CORS 이유는 스크립트 예외에 없다(실험 23-A).
- 대신 오류 코드(`#418`·`#321`), 예외 이름(`ChunkLoadError`·`QuotaExceededError`·`AbortError`), 요청 URL·상태 코드, 지표 이름으로 찾는다.

### 9. 처방이 만든 다른 증상

| 처방 | 생긴 증상 | 적용 범위 | leaf |
|---|---|---|---|
| 이미지 전부에 `loading="lazy"` | LCP 1.47s → 5.4s | 첫 화면 아래 이미지만 | [14-3](../14-image-optimization/2-summary.md) |
| preload 여러 개 | LCP 0.63s → 1.55s | 늦게 발견되는 핵심 자원(LCP 이미지·첫 화면 폰트)만 | [13-2](../13-critical-path-and-resource-loading/2-summary.md) |
| memo 전면 적용 | 효과 없음, 비교 비용, stale closure | 측정으로 비싼 곳만 | [18-3](../18-ui-rerender-and-memoization/2-summary.md) |
| cache-first를 HTML까지 | 배포가 반영 안 됨 | 해시 파일명 정적 자원만, HTML은 network-first | [07-1](../07-service-workers-and-offline/2-summary.md) |

- 처방 전후로 같은 수집기로 LCP·INP·CLS를 함께 보고, 회귀 게이트에 세 지표를 함께 건다([20](../20-performance-budgets-and-regression-gates/2-summary.md)).
