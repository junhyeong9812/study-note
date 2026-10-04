# web-platform/13-critical-path-and-resource-loading — 정답

## 정답

### 1. 렌더 차단 vs 파서 차단

- 렌더 차단: 그 자원이 처리될 때까지 **페인트**를 미룬다. HTML 파싱은 계속된다. `<head>`의 스타일시트가 기본으로 그렇다.
- 파서 차단: 그 자원을 받아 실행할 때까지 **HTML 파싱**을 멈춘다. `async`·`defer` 없는 클래식 `<script src>`가 그렇다(그동안 페인트도 못 하므로 렌더도 늦어진다).
- 스타일시트가 스크립트를 막는 이유: 스크립트가 `getComputedStyle`·`offsetWidth` 같은 스타일 의존 값을 읽을 수 있다. 그래서 HTML 표준은 파서가 넣은 동기 클래식 스크립트를, 문서에 "스크립트를 막는 스타일시트"가 있으면 그것이 끝날 때까지 기다리게 한다.

### 2. 1초 자원별 FCP

(실험, headless Chrome 151, 스로틀 없음, 변형당 3회)

| 변형 | FCP | LCP |
|---|---|---|
| 기준선 | 52~92ms | 264~272ms |
| ① CSS | 1072~1080ms | 1072~1080ms |
| ② `media=print` CSS | 60~76ms | 264~292ms |
| ③ 동기 JS | 1084~1092ms | 1084~1092ms |
| ④ `defer` JS | 60~76ms | 264~268ms |
| ⑤ `async` JS | 48~56ms | 260ms |

- 차단 자원(①③)만 1초를 그대로 더한다. 같은 1초 자원이라도 비차단(②④⑤)이면 이 실험에서는 첫 화면에 영향이 없었다. 다만 받기가 비차단이어도 실행이 길면(`async`는 파싱을 끊고 실행한다) 메인 스레드를 잡아 페인트·LCP를 늦출 수 있다 — 이 실험의 스크립트는 실행이 거의 없었다.

### 3. 동기 스크립트 뒤의 이미지

- 마크업의 `<img>`: 1초를 기다리지 않는다. 이미지 요청이 문서 기준 24~29ms에 서버에 도착했다. preload 스캐너가 파서가 멈춘 동안 뒤쪽 마크업을 훑어 먼저 요청했다. 다만 페인트는 스크립트가 끝난 뒤라 LCP는 1084~1092ms.
- `new Image()`로 넣은 경우: 스크립트가 실행되어야 존재를 안다. 요청 1026~1030ms, LCP 1260~1272ms. 발견이 늦어진 만큼 "자원 로드 지연" 조각이 늘었다.

### 4. preload 스캐너의 사각지대

- JS가 넣는 `<img>`·`<script>`(DOM API로 만든 외부 스크립트는 기본 async — `document.write()`로 쓴 것은 예외).
- `data-src`로 바꿔 둔 스크립트 지연 로딩 이미지.
- CSS 안의 `background-image`·`@font-face`.
- 클라이언트 렌더링(CSR)이 만드는 마크업 전체.
- CSS 배경 히어로 처방: 마크업 `<img>`로 바꾸거나 `<link rel=preload as=image href=… fetchpriority=high>`.
- 실험: CSS 배경만 → 이미지 요청 328ms, LCP 560~576ms. preload 추가 → 요청 17~21ms, LCP 376ms(재실행 372~448ms. CSS 300ms가 끝나는 순간 이미지도 준비되어 FCP = LCP).

### 5. defer · async · module

| | 받기 | 실행 시점 | 실행 순서 |
|---|---|---|---|
| `defer` | 파싱과 병렬 | 파싱이 끝난 뒤 | 문서 순서 |
| `async` | 파싱과 병렬 | 도착하는 대로(파싱을 잠깐 끊음) | 도착 순서 |
| `type=module` | 파싱과 병렬(의존 모듈까지) | `async` 없으면 파싱 뒤, 있으면 도착하는 대로 | `defer` 속성은 효과 없음 |

- `defer`: 서로 의존하는 앱 코드, DOM이 다 만들어진 뒤 돌아야 하는 코드.
- `async`: 다른 스크립트와 독립인 분석·광고·위젯.

### 6. Chrome 151 초기 우선순위

(실험, CDP `initialPriority` → `resourceChangedPriority`)
- 문서 VeryHigh, CSS VeryHigh, 동기 JS High, `defer`·`async` JS Low, 폰트 preload High.
- 뷰포트 안 이미지: Medium → 레이아웃 뒤 **High**로 상향.
- `fetchpriority=high` 이미지: 처음부터 High.
- 3000px 아래 이미지: Medium 유지(처음 5개의 큰 이미지는 Medium으로 시작 — web.dev, Chrome 117+). `loading=lazy`면 요청이 없다.

### 7. preload 남발

- 원인(해석): `<head>`의 preload 5개가 일찍 발견되어 바로 나간다. 우선순위는 높지 않다 — 재실행에서 5장 모두 Low였다(`as=image` preload는 이미지 우선순위를 따른다). HTTP/1.1에서 Chrome은 호스트당 연결 6개(`g_max_sockets_per_group`)를 쓴다. 요청 6개(preload 5 + 히어로)가 거의 동시에 연결 6개를 하나씩 차지하고, 히어로는 다섯과 1.6Mbps를 나눠 받는다.
- `fetchpriority=high`가 안 듣는 이유: 우선순위는 "대기 중인 요청을 어느 순서로 보내나"를 바꾼다. 이미 나가서 받는 중인 요청의 대역폭을 되돌리지는 못한다.
- 실험: LCP 624~640ms → 1528~1564ms, `fetchpriority=high` 1532~1592ms.
- 콘솔 단서: "The resource … was preloaded using link preload but not used within a few seconds from the window's load event." 쓰지 않은 preload를 찾는 경고다.

### 8. 힌트 고르기

- preconnect: 곧 쓸 핵심 다른 출처(폰트 CDN·API)의 DNS·TCP·TLS를 미리.
- dns-prefetch: 덜 중요하거나 출처가 많을 때 DNS만 — 더 싸다.
- preload: 지금 페이지에 필요한데 늦게 발견되는 자원(LCP 이미지·폰트). `as` 필수(HTML 표준: 없으면 preload를 하지 않는다).
- prefetch: 다음 탐색에 쓸 자원을 낮은 우선순위로.
- `crossorigin` 누락: 폰트는 CORS 모드로 요청되므로 자격 증명 모드가 다른 preload는 재사용되지 않는다. 같은 파일을 두 번 받고("credentials mode does not match" 경고, 15번 실험 37ms·363ms 두 요청), preconnect는 그 연결을 재사용하지 못한다.

### 9. 그래프로 본 크리티컬 패스

- 정점 = 자원(HTML·CSS·JS·폰트·이미지), 간선 = "A를 처리해야 B를 발견하거나 실행할 수 있다".
- 첫 렌더(또는 LCP) 시각 ≈ 시작점에서 그 렌더까지의 **최장 경로** 길이(가중치 = 왕복 + 전송 + 처리). DAG의 최장 경로는 위상 정렬 순서로 한 번 훑어 구한다.
- preload는 사슬 중간(HTML → CSS → 이미지)의 간선을 HTML → 이미지로 바꿔 경로를 짧게 만든다. 반대로 preload를 남발하면 간선이 아니라 **가중치**(공유 대역폭)가 커져 다른 경로가 길어진다.
