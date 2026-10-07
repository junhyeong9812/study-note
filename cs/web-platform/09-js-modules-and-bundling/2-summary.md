# web-platform/09-js-modules-and-bundling — JS 모듈 체계·번들링·코드 분할·트리 셰이킹 — 정리 (힌트)

## 해결하는 문제

앱 코드는 파일 수백 개로 나뉜다. 브라우저는 그것을 네트워크로 받아야 한다.

```text
  파일을 나눈 채로 보내면                   하나로 합쳐 보내면
  ─────────────────────                   ──────────────────────
  main.js 받기 → 파싱 → import 발견          bundle.js 한 번
    → utils.js 받기 → 파싱 → import 발견      (안 쓰는 코드까지 다 받음)
      → ... 깊이만큼 왕복이 쌓인다            첫 화면에 필요 없는 코드도 먼저 받음
```

- 모듈 체계는 "파일끼리 무엇을 주고받나"를 정한다. 번들러는 그 의존 그래프를 빌드 때 따라가 **배포용 파일 묶음**을 만든다.
  - *모듈(module)*: 자기 스코프를 갖고 `export`로 내보내고 `import`로 가져오는 코드 단위.
  - *번들러(bundler)*: 진입점에서 의존 그래프를 따라가 파일을 합치고(번들), 안 쓰는 코드를 빼고(트리 셰이킹), 필요할 때 받을 조각으로 나누는(코드 분할) 빌드 도구. esbuild·webpack·Rollup·Vite(프로덕션 빌드는 Vite 7까지 Rollup, Vite 8부터 Rollup 호환 Rolldown — vite.dev Vite 8 발표) 등.

쉬운 예: 이사 짐 싸기다.
- 물건마다 상자 하나씩 보내면 트럭 왕복이 끝없다(모듈마다 요청).
- 전부 한 상자에 넣으면 왕복은 한 번이지만, 당장 안 쓸 겨울옷까지 첫날 다 풀어야 한다(번들 비대).
- 그래서 "첫날 상자"와 "나중 상자"로 나누고(코드 분할), 안 쓰는 물건은 버린다(트리 셰이킹). 상자에는 내용물 목록 이름표를 붙인다(해시 파일명).

똑같은 구조다.\
이름표가 바뀌는 순간 옛 이름표로 상자를 찾는 사람이 생긴다. 이것이 배포 직후 `ChunkLoadError`다.

실무 예:
- 날짜 라이브러리 함수 하나 쓰려고 전체를 import했더니 번들이 수백 KB 커졌다.
- 배포 직후 기존 탭에서 "관리자 화면" 버튼을 누른 사용자만 흰 화면을 봤다.

## 동작·원리

### 1. 두 모듈 체계 — CommonJS와 ES 모듈

```text
  CommonJS (Node 전통)                     ES 모듈 (ECMA-262, 브라우저 표준)
  ─────────────────────                   ──────────────────────────────────
  const { f } = require('./u')            import { f } from './u.js'
  실행 중에 불러온다(동적, 동기)              정적 import 그래프는 실행 전에 안다(정적 구조)
  module.exports 값을 받음(구조 분해=복사)     살아 있는 바인딩(live binding)
  조건부 require 가능                        조건부는 import() (동적, Promise)
  → 정적 분석이 어렵다                        → 트리 셰이킹·분할의 바탕
```

- ECMA-262의 모듈 적재는 세 단계다.
  1. **파싱·적재**: 각 모듈 소스를 파싱해 import 목록을 얻고 의존 모듈을 가져온다(가져오기는 호스트=HTML이 맡음).
  2. **링크(Link)**: import 이름을 export 바인딩에 연결한다. 없는 이름이면 실행 전에 `SyntaxError`.
  3. **평가(Evaluate)**: 의존 모듈부터(후위 순서) 한 번씩 실행한다.
  - ECMA-262의 링크·평가 알고리즘은 깊이 우선 탐색으로 그래프를 돌며 `[[DFSIndex]]`·`[[DFSAncestorIndex]]`로 순환(강연결 요소)을 묶어 처리한다. [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md) · [algorithm/18-scc](../../algorithm/18-scc/2-summary.md)
  - *살아 있는 바인딩*: 내보낸 쪽이 변수를 바꾸면 가져온 쪽에서도 바뀐 값이 보인다.
- HTML 표준: `<script type="module">`은 기본이 지연(defer) 실행이다. 같은 문서(환경)에서 같은 URL·모듈 타입 조합은 *모듈 맵*에 한 번만 적재된다(모듈 맵 키 = (URL, 모듈 타입) — HTML 표준 "module map"). `import()`는 Promise를 돌려주는 동적 적재다.
- 모듈 해석(`'react'` 같은 bare specifier → 실제 경로)은 브라우저에서는 import map, Node·번들러는 `node_modules` 탐색 규칙이다. 의존 해석 일반론은 [language 19번](../../language/19-modules-and-dependency-resolution/2-summary.md)과 [data-structure/34-dependency-resolver](../../data-structure/34-dependency-resolver/2-summary.md).

### 2. 번들 안 한 ES 모듈의 폭포(waterfall)

```text
  시간 →  (요청마다 왕복 지연 100ms 가정)
  HTML   ████
  entry       ████        ← HTML 파싱 후에야 entry를 안다
  m0               ████   ← entry를 받아 파싱해야 m0를 안다
  m1                    ████
  ...                          ████ ████ ████   (깊이만큼 순차)

  modulepreload: HTML에 미리 적어 두면 m0~m5를 동시에 요청
  번들: 한 파일이라 왕복 1번
```

- 브라우저는 모듈을 받아 파싱해야 다음 import를 안다. 그래서 의존 깊이만큼 왕복이 순차로 쌓인다.
  - *modulepreload*: `<link rel="modulepreload" href=...>`로 모듈을 미리 가져오게 하는 HTML 힌트.
- HTTP/2 다중화는 요청을 **동시에** 보낼 때 이득이다. 순차로 발견되는 사슬의 왕복 수는 줄이지 못한다([network/36-http2-multiplexing](../../network/36-http2-multiplexing/2-summary.md)).

### 3. 번들러가 하는 일

```text
  진입점 main.js
     │ ① 의존 그래프 구축 (import를 따라 DFS/BFS)
     ▼
  main ──▶ utils {formatPrice ✔, bigUnusedA ✘, bigUnusedB ✘, TABLE ?}
       ──▶ register (부수 효과: window.__registered++)
       ┄┄▶ chart  (동적 import = 분할 지점)
     │ ② 트리 셰이킹: 쓰이는 export에서 도달 가능한 코드만 남김
     │                단, 부수 효과가 있을지 모르는 문장은 남김 (TABLE = Array.from(...))
     │ ③ 코드 분할: 동적 import 대상·공유 모듈을 별도 청크로
     │ ④ 축소(minify), 파일명에 내용 해시
     ▼
  main-62GD74A7.js  +  chart-MK4S35YN.js
```

- *트리 셰이킹(tree shaking)*: 쓰이지 않는 export를 빼는 것. ES 모듈의 정적 구조 덕에 빌드 때 도달성을 판정할 수 있다.
  - 함수 호출 결과로 초기화한 변수(`TABLE = Array.from(...)`)는 호출에 부수 효과가 있을지 몰라 남긴다. `/* @__PURE__ */` 주석이 "이 호출은 부수 효과 없음"이라고 알려 준다(webpack·esbuild 문서).
  - `package.json`의 `"sideEffects": false`는 "이 패키지 파일은 import만으로 하는 일이 없다"는 선언이다. 틀리게 선언하면 CSS·폴리필 import가 사라진다(webpack Tree Shaking 가이드).
- *코드 분할(code splitting)*: 동적 `import()`를 경계로 따로 받을 청크를 만든다. esbuild 분할은 현재 `esm` 출력에서만 된다(esbuild API 문서).
- *내용 해시 파일명*: 파일 내용이 바뀌면 이름이 바뀐다. 같은 이름에 다른 내용을 다시 올리지 않는 배포 규칙을 지키면 "이름이 같으면 내용도 같다"고 볼 수 있어(해시 충돌은 드물지만 불가능하지 않다) `Cache-Control: immutable`로 오래 캐시할 수 있다([network/34-http-caching](../../network/34-http-caching/2-summary.md)).
  - 청크 이름이 바뀌면 그 이름을 담은 부모 청크 내용도 바뀌어 부모 해시도 바뀐다(아래 실험 C: chart만 바꿨는데 main 해시도 바뀜).

### 실험 A: 트리 셰이킹·PURE·sideEffects (esbuild 0.28.2)

`src/utils.js`는 `formatPrice`(쓰임), `bigUnusedA`·`bigUnusedB`(안 쓰임), `TABLE = Array.from(...)`(안 쓰임)을 내보낸다. `register.js`는 import만 해도 `window.__registered`를 바꾼다. `main.js`는 `formatPrice`만 쓰고 `chart.js`를 동적 import한다. `src2`는 `TABLE` 앞에 `/* @__PURE__ */`를 붙인 판. `src3`은 `utils`·`register`를 `"sideEffects": false` 패키지 `mylib`로 옮긴 판.

```text
(실험, esbuild 0.28.2, 2026-10-04 — 파일별 바이트와 문자열 출현 수)
1-no-treeshake.min.js         903 B  unused-A/B:2  row-:1  __registered:2  chart:1
2-treeshake.min.js            625 B  unused-A/B:0  row-:1  __registered:2  chart:1
3-treeshake-pure.min.js       529 B  unused-A/B:0  row-:0  __registered:2  chart:1
4-split/chart-MK4S35YN.js     105 B  unused-A/B:0  row-:0  __registered:0  chart:1
4-split/main-62GD74A7.js      312 B  unused-A/B:0  row-:1  __registered:2  chart:0
--- sideEffects:false 패키지의 부수 효과 import
▲ [WARNING] Ignoring this import because "src3/node_modules/mylib/register.js" was marked as having no side effects [ignored-bare-import]
function o(t){return t.toLocaleString("ko-KR")+"\uC6D0"}var r=Array.from({length:50},(t,e)=>"row-"+e+"-et dolore magna aliqua ut enim ad minim veniam");document.title=o(1);
```

- 트리 셰이킹으로 `bigUnusedA/B`가 빠졌다(903 → 625B). `TABLE`(`row-`)은 남았다.
- `@__PURE__`를 붙이자 `TABLE`도 빠졌다(529B).
- 분할하면 첫 로드 파일 `main`은 312B, `chart`(105B)는 버튼을 누를 때 받는다.
- `sideEffects: false` 패키지에서는 `import 'mylib/register.js'`가 경고와 함께 **통째로 사라졌다**(`__registered` 없음). 선언이 틀리면 부수 효과 코드가 조용히 빠진다.

### 실험 B: 의존 사슬 깊이 6 — 번들 안 함 vs modulepreload vs 번들

`entry.js → m0 → m1 → … → m5` 사슬. 각 페이지를 CDP `Network.emulateNetworkConditions`(latency 100ms, 대역폭 제한 없음)와 캐시 끔으로 3번씩 열고, 마지막 모듈이 실행된 `performance.now()`를 쟀다.

```js
// exp09-bundle.js 핵심
await cdp.send('Network.emulateNetworkConditions', { offline: false, latency: 100, downloadThroughput: -1, uploadThroughput: -1 });
await page.goto(base + p);
await page.waitForFunction(() => window.doneAt !== undefined);   // entry.js: window.doneAt = performance.now()
```

(실험, headless Chrome 151.0.7922.173, 요청당 지연 100ms 에뮬레이션, 127.0.0.1 Node 서버, 2026-10-04 — 2회 × 3번)

```text
/unbundled.html   JS 요청 7개, 마지막 모듈 실행 시각(performance.now) = [870, 868, 866] ms
/preload.html     JS 요청 7개, 마지막 모듈 실행 시각(performance.now) = [329, 337, 333] ms
/bundled.html     JS 요청 1개, 마지막 모듈 실행 시각(performance.now) = [225, 222, 224] ms
```

두 번째 실행: unbundled 866~881ms, preload 331~337ms, bundled 227ms. 사실 점검 재실행 2회(같은 스크립트): unbundled 871~895ms, preload 334~350ms, bundled 226~233ms — 순서와 크기는 같다.

사실 점검에서 서버 도착 시각(페이지 이동 시작 기준)과 요청이 온 소켓을 따로 찍었다(`fc09-preload-timing.js`, 같은 조건 1회, `...`은 생략한 줄).

```text
== /preload.html doneAt=345ms sockets=6
  22ms /preload.html sock#0
  138ms /chain/m0.js sock#0
  143ms /chain/m1.js sock#1
  ...
  153ms /chain/m5.js sock#5
  249ms /chain/entry.js sock#0
== /unbundled.html doneAt=876ms sockets=1
  11ms /unbundled.html sock#0
  127ms /chain/entry.js sock#0
  239ms /chain/m0.js sock#0
  ...
  779ms /chain/m5.js sock#0
```

- 번들 안 한 사슬은 약 870ms. 요청 7개가 순차로 각 100ms 이상 걸렸다(해석: HTML 1 + JS 7 ≈ 8 왕복).
- `modulepreload`로 미리 알려 주면 m0~m5 여섯 개가 연결 6개로 거의 동시에 갔다. `entry.js`는 연결이 빌 때까지 기다려 한 왕복 뒤에 갔다. 이 서버는 HTTP/1.1이고, 관측된 동시 연결이 6개였다(해석: 호스트당 연결 수 상한). 그래서 약 330ms(HTML·preload 6개·entry 세 왕복 남짓)다. HTTP/2 서버라면 한 연결에서 다중화돼 차이가 있을 수 있다(미실험).
- 번들은 요청 1개로 약 225ms.

### 실험 C: 배포 후 옛 청크 요청 — `ChunkLoadError` 류

v1을 빌드해 서버에 올리고 페이지를 연다. 그다음 `chart.js` 내용만 바꾼 v2로 서버 폴더를 바꿔치기한다(옛 파일 삭제 = 흔한 배포). 열려 있던 탭에서 `loadChart()`(동적 import)를 부른다.

(실험, headless Chrome 151.0.7922.173, esbuild 0.28.2, 2026-10-04 — 2회 동일, 포트만 다름)

```text
v1 파일: chart-XZXOI6CO.js main-WH74W3PA.js | v2 파일: chart-D6VA76Y2.js main-UOA7NCRO.js
v1 페이지 로드 완료. 이제 서버를 v2 로 교체(옛 파일 삭제)
탭에서 차트 버튼 클릭 → TypeError: Failed to fetch dynamically imported module: http://127.0.0.1:PORT/chart-XZXOI6CO.js
서버 요청: /chart-XZXOI6CO.js
새로고침 후 클릭 → chart-v2
```

- 옛 탭의 `main`(v1)은 옛 청크 이름 `chart-XZXOI6CO.js`를 들고 있다. 서버엔 그 파일이 없어 404 → 네이티브 동적 import는 `TypeError: Failed to fetch dynamically imported module`.
- 같은 상황을 webpack 런타임은 `ChunkLoadError`(`Loading chunk N failed.`)로, Vite는 `vite:preloadError` 이벤트로 알린다(각 소스·문서).
- chart만 바꿨는데 `main` 해시도 바뀌었다. `main`이 chart의 파일명을 담기 때문이다.
- 새로고침하면 새 HTML이 v2 `main`을 가리켜 정상.

## 쓰이는 자료구조·알고리즘

- **모듈 의존 그래프** = 유향 그래프(순환 가능). [data-structure/08-graph](../../data-structure/08-graph/2-summary.md)
- **링크·평가 순서** = DFS 후위 순서, 순환은 Tarjan식 강연결 요소로 묶음(ECMA-262 `[[DFSIndex]]`·`[[DFSAncestorIndex]]`). [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md) · [algorithm/18-scc](../../algorithm/18-scc/2-summary.md)
- **트리 셰이킹** = 도달성 분석(mark-and-sweep과 같은 모양): 진입점과 부수 효과 문장에서 출발해 닿는 선언만 표시, 나머지 제거.
- **코드 분할** = 그래프 분할: 동적 import 경계와 "어느 진입점들이 이 모듈을 쓰나" 집합으로 청크를 나눈다.
- **내용 주소화** = 해시(내용) → 파일명. 같은 이름을 덮어쓰지 않는 배포 규칙 아래서 이름이 같으면 내용이 같다고 본다.
- **모듈 맵** = (URL, 모듈 타입) → 모듈 스크립트 맵(같은 조합은 한 번만 적재·평가, 문서·워커 환경마다 따로). [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 번들 크기를 먼저 본다

- 빌드 메타파일·분석기: esbuild `--metafile` + 분석 페이지, webpack-bundle-analyzer, Vite `rollup-plugin-visualizer` 등으로 어떤 모듈이 몇 KB인지 본다.
- 큰 덩어리부터: 전체 import(`import _ from 'lodash'`) → 개별 import(`import debounce from 'lodash-es/debounce'`), 무거운 위젯은 동적 import.

### 2. 분할 지점은 "사용자가 지금 안 보는 것"

```ts
// 라우트 단위 분할 (React 예시 — 원리 설명용)
const AdminPage = lazy(() => import('./pages/AdminPage'));
// 상호작용 단위 분할
button.onclick = async () => (await import('./chart')).drawChart(el);
```

- 첫 화면에 필요한 코드만 초기 청크에. 너무 잘게 나누면 요청 수·폭포가 다시 늘어난다(실험 B).

### 3. 배포 직후 청크 실패를 설계로 막는다

1. **옛 자산을 바로 지우지 않는다.** 해시 파일명 자산은 이전 몇 개 배포분을 남겨 둔다(CDN·버킷 보존 기간).
2. HTML은 `Cache-Control: no-cache`(Vite 문서도 권함), 해시 자산은 `max-age=31536000, immutable`.
3. 그래도 실패하면 한 번 새로고침한다(무한 루프 방지 플래그와 함께).

```ts
// 네이티브 ESM / Vite
window.addEventListener('vite:preloadError', (e) => { e.preventDefault(); reloadOnce(); });
async function safeImport<T>(load: () => Promise<T>): Promise<T> {
  try { return await load(); }
  catch (e) {
    if (/Failed to fetch dynamically imported module|ChunkLoadError|Loading chunk/.test(String(e))) reloadOnce();
    throw e;
  }
}
function reloadOnce() {
  if (sessionStorage.getItem('chunk-reload')) return;   // 한 번만
  sessionStorage.setItem('chunk-reload', '1');
  location.reload();
}
```

- 서비스 워커가 HTML을 캐시하면 새로고침해도 옛 HTML이 뜰 수 있다([07-service-workers-and-offline](../07-service-workers-and-offline/2-summary.md)).

### 4. 트리 셰이킹이 되는 코드를 쓴다

- ES 모듈로 배포된 라이브러리를 고른다(`"module"`·`"exports"` 필드). CommonJS는 정적 분석이 어려워 덜 빠진다.
- 모듈 최상위에서 부수 효과를 줄이고, 필요한 호출엔 `/* @__PURE__ */`.
- 자기 패키지에 `"sideEffects"`를 줄 때는 CSS·폴리필을 예외로 적는다(`["**/*.css", "./src/polyfills.js"]`).

### 5. 진단

- DevTools Network: JS 요청 수·폭포 모양(Initiator 열로 누가 불렀나). Coverage 패널: 받은 JS 중 실행 안 된 바이트 비율.
- 오류 모니터링에서 `ChunkLoadError`·`Failed to fetch dynamically imported module`이 배포 시각 직후에 몰리는지 본다.

## 장애 시나리오와 대처

### 1. 번들 비대 → 초기 로드 지연 (⚠)

- **현상**: 첫 화면이 몇 초 늦게 뜬다. 저사양 모바일에서 특히 느리다.
- **보이는 형태**: Lighthouse "Reduce unused JavaScript", Coverage 패널의 높은 미사용 비율, 큰 `main.js`.
- **원인**: 전체 라이브러리 import, CommonJS 의존으로 트리 셰이킹 실패, 부수 효과로 판정돼 남은 코드(실험 A의 `TABLE`), 분할 없이 관리자 화면까지 초기 번들에.
- **대처**: 번들 분석 → 개별 import·ESM 판 교체 → 라우트·상호작용 단위 동적 import → `@__PURE__`·`sideEffects` 선언. 크기 예산을 CI에 건다([20-performance-budgets-and-regression-gates](../20-performance-budgets-and-regression-gates/2-summary.md)).

### 2. 배포 직후 `ChunkLoadError` (⚠ 청크 해시 불일치)

- **현상**: 배포 직후 기존 탭 사용자가 특정 화면으로 갈 때 흰 화면.
- **보이는 형태**: webpack `ChunkLoadError: Loading chunk 123 failed.`, 네이티브 ESM `TypeError: Failed to fetch dynamically imported module: .../chart-XZXOI6CO.js`, Network 탭에 그 청크 404(실험 C).
- **원인**: 열려 있던 탭의 코드가 옛 해시 청크 이름을 가리키는데 배포가 옛 파일을 지웠다. 또는 CDN·서비스 워커에 캐시된 옛 HTML이 옛 `main`을 가리킨다.
- **대처**: 옛 자산 보존, HTML `no-cache`, 실패 시 1회 새로고침, 서비스 워커 갱신 흐름 점검.

### 3. `sideEffects: false` 오선언 → 스타일·폴리필 사라짐

- **현상**: 프로덕션 빌드에서만 버튼 스타일이 없거나, 구형 브라우저에서만 `xxx is not a function`.
- **보이는 형태**: 빌드 경고 `Ignoring this import because ... was marked as having no side effects`(esbuild, 실험 A). 개발 서버에서는 정상.
- **원인**: 패키지가 `"sideEffects": false`로 선언해 CSS·폴리필 import가 제거됐다.
- **대처**: `"sideEffects": ["**/*.css", ...]`로 예외를 적는다. 빌드 경고를 CI에서 실패로 다룬다.

### 4. 번들 안 한 ESM의 폭포

- **현상**: 개발 서버나 번들 없는 배포에서 첫 상호작용까지 오래 걸린다. 지연 큰 망에서 심하다.
- **보이는 형태**: Network 탭에 JS 요청이 계단처럼 순차로 늘어선다(실험 B: 깊이 6에서 약 870ms vs 번들 약 225ms, 요청당 지연 100ms 조건).
- **원인**: 브라우저는 모듈을 받아 파싱해야 다음 import를 안다.
- **대처**: 프로덕션 번들, 또는 `modulepreload` 목록 생성(실험 B: 약 330ms), 의존 깊이 줄이기.

### 5. 같은 라이브러리 두 벌 (싱글턴 깨짐)

- **현상**: React 훅 오류("Invalid hook call"), 상태 공유 라이브러리의 상태가 둘로 갈림.
- **보이는 형태**: 번들 분석에 같은 패키지가 두 경로·두 버전으로 보인다.
- **원인**: 의존 해석이 서로 다른 버전·경로로 갈렸다(중복 설치, 마이크로 프론트엔드별 사본).
- **대처**: 패키지 매니저 dedupe·`resolutions`/`overrides`, 번들러 alias로 한 경로에 고정. 마이크로 프론트엔드의 공유 모듈은 [22 `islands-and-micro-frontends`](../22-islands-and-micro-frontends/2-summary.md).

## 핵심 문장

- ES 모듈은 import·export 선언이 정적이라 빌드 때 정적 의존 그래프를 알 수 있고(경로를 실행 중 계산하는 `import(expr)`의 대상은 예외), 이것이 트리 셰이킹과 코드 분할의 바탕이다.
- 번들 안 한 모듈은 받아서 파싱해야 다음 import를 알아, 의존 깊이만큼 왕복이 쌓인다. 요청당 지연 100ms 실험에서 깊이 6 사슬은 약 870ms, modulepreload 약 330ms, 번들 약 225ms였다.
- 트리 셰이킹은 도달성 분석이다. 부수 효과가 있을지 모르는 문장은 남기고, `@__PURE__`·`sideEffects`가 그 판단을 바꾼다. 선언이 틀리면 필요한 import가 조용히 빠진다.
- 코드 분할은 동적 `import()`를 경계로 청크를 나눈다. 해시 파일명은 오래 캐시할 수 있게 해 주지만, 배포가 옛 청크를 지우면 열린 탭이 `ChunkLoadError`류 오류를 낸다.
- 배포 직후 청크 오류는 옛 자산 보존 + HTML `no-cache` + 실패 시 1회 새로고침으로 막는다.

## 관련 주제·근거

- 선행
  - [05-fetch-from-browser](../05-fetch-from-browser/2-summary.md) — 자원 요청 수명
  - [language/19-modules-and-dependency-resolution](../../language/19-modules-and-dependency-resolution/2-summary.md)
- 후속·연결
  - [07-service-workers-and-offline](../07-service-workers-and-offline/2-summary.md) — 캐시된 옛 HTML과 청크 불일치
  - [20-performance-budgets-and-regression-gates](../20-performance-budgets-and-regression-gates/2-summary.md) — 번들 크기 예산
  - [10 렌더링 전략](../10-rendering-strategies/2-summary.md)·[13 크리티컬 패스·preload](../13-critical-path-and-resource-loading/2-summary.md)·[19 하이드레이션](../19-hydration-cost-and-partial-hydration/2-summary.md)·[22 마이크로 프론트엔드](../22-islands-and-micro-frontends/2-summary.md)·[23 증상 색인](../23-web-symptom-index/2-summary.md)(`ChunkLoadError`)
  - [network/34-http-caching](../../network/34-http-caching/2-summary.md) — `immutable`·해시 자산 캐시 · [network/36-http2-multiplexing](../../network/36-http2-multiplexing/2-summary.md) · [network/47-cdn-and-edge](../../network/47-cdn-and-edge/2-summary.md)
  - [reliability/23-deployment-strategies](../../reliability/23-deployment-strategies/2-summary.md) — 배포 중 옛·새 버전 공존
  - [data-structure/08-graph](../../data-structure/08-graph/2-summary.md) · [data-structure/34-dependency-resolver](../../data-structure/34-dependency-resolver/2-summary.md) · [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md) · [algorithm/18-scc](../../algorithm/18-scc/2-summary.md)
- 표준·문서
  - ECMA-262 "Modules"(§16.2) <https://tc39.es/ecma262/#sec-modules> — Module Record, Link·Evaluate, `[[DFSIndex]]`·`[[DFSAncestorIndex]]`, `import()`
  - WHATWG HTML "Module scripts"·module map(키 = URL·모듈 타입 튜플)·`modulepreload`·import maps <https://html.spec.whatwg.org/multipage/webappapis.html#integration-with-the-javascript-module-system>
  - esbuild API 문서 <https://esbuild.github.io/api/> — 분할은 `esm` 출력에서만, `[name]`·`[hash]` 템플릿, `@__PURE__`
  - webpack "Tree Shaking" 가이드 <https://webpack.js.org/guides/tree-shaking/> — `sideEffects`(CSS 예외), `/*#__PURE__*/`
  - webpack 소스 `lib/web/JsonpChunkLoadingRuntimeModule.js` — `error.name = 'ChunkLoadError'`, `'Loading chunk ' + chunkId + ' failed.'`
  - Vite "Building for Production — Load Error Handling" <https://vite.dev/guide/build> — `vite:preloadError`, 배포가 옛 자산을 지울 때, HTML `Cache-Control: no-cache`
- 실험 목록
  - `build09.sh` — esbuild 0.28.2(scratchpad npm). 트리 셰이킹 끔/켬, `@__PURE__`, 분할, `sideEffects: false` 패키지의 부수 효과 import 제거. 출력 바이트·문자열 출현 수.
  - `exp09-bundle.js` — Node 20.19.6 + playwright-core 1.62.1, headless Chrome 151.0.7922.173, 127.0.0.1 Node 서버. (B) 깊이 6 ESM 사슬 unbundled·modulepreload·bundled를 latency 100ms 에뮬레이션·캐시 끔으로 3회씩, (C) v1→v2 바꿔치기 후 열린 탭의 동적 import 실패와 새로고침 후 회복. 스크립트 2회 실행.
  - `fc09-preload-timing.js`(사실 점검) — 같은 환경·같은 사슬에서 preload·unbundled 페이지의 요청별 서버 도착 시각과 소켓 수(서버 `req.socket.remotePort`).
