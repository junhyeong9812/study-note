# web-platform/22-islands-and-micro-frontends — Islands와 마이크로 프론트엔드: 페이지를 조각으로 나눠 조합하기 — 정리 (힌트)

## 해결하는 문제

한 페이지를 하나의 큰 클라이언트 앱으로 만들면 두 종류의 문제가 생긴다.

```text
  (성능) 대부분 정적인 페이지                    (조직) 여러 팀이 만드는 한 화면
  ┌───────────────────────────────┐            ┌───────────────────────────────┐
  │ 기사 본문 (정적)               │            │ 헤더·검색  ← 팀 A              │
  │ 이미지·표 (정적)               │            │ 상품 상세  ← 팀 B              │
  │ [댓글 위젯] ← 상호작용         │            │ 리뷰       ← 팀 C              │
  │ 관련 기사 (정적)               │            │ 장바구니   ← 팀 D              │
  │ [구독 버튼] ← 상호작용         │            └───────────────────────────────┘
  └───────────────────────────────┘             한 저장소·한 배포 → 팀 D의 버그 수정이
   전체를 하이드레이션 → 정적 부분까지 비용        A·B·C의 배포 일정에 묶인다
```

- **Islands**는 성능 문제를 푼다. 정적 HTML 바다에 상호작용하는 섬만 띄운다.
  - *Islands 아키텍처*: 서버가 HTML 페이지를 렌더하고, 상호작용이 많은 영역 주위에 자리(슬롯)를 둔다. 각 섬은 독립적으로 하이드레이션된다(Jason Miller, 2020). 용어는 Etsy의 Katie Sylor-Miller가 2019년에 지었다(Miller 글).
- **마이크로 프론트엔드**는 조직 문제를 푼다. 팀마다 독립적으로 배포하는 프론트엔드를 하나로 조합한다.
  - *Micro frontends*: 독립적으로 배포 가능한 프론트엔드 앱들을 더 큰 전체로 조합하는 아키텍처 스타일(Cam Jackson, martinfowler.com, 2019-06-19).
- 둘 다 "페이지를 조각으로 나누고 다시 조합한다"는 구조다. 나누는 기준이 다르다. Islands는 **상호작용 여부**, 마이크로 프론트엔드는 **소유 팀**이다.

쉬운 예: 쇼핑몰 건물이다.
- Islands = 건물 대부분은 그냥 벽과 진열대이고, 전기가 필요한 키오스크 몇 대만 따로 배선한다.
- 마이크로 프론트엔드 = 입점 매장마다 인테리어 업체가 다르다. 각자 공사(배포)하지만 같은 건물 규칙(공용 복도·간판 규격)을 지켜야 한다.

똑같은 구조다. 조각 사이의 **경계**(무엇을 공유하고 무엇을 격리하나)를 어떻게 긋느냐가 핵심이다.

실무 예:
- 마이크로 프론트엔드마다 React를 번들에 넣어, 사용자가 React를 n번 받는다(Jackson). 아래 실험: 셸 + 원격 하나만으로 JS 388,968B(공유 시 194,926B).
- 원격 팀이 React를 따로 넣었는데 셸의 React로 그 컴포넌트를 그리면 훅이 깨진다(실험 ①).
- 팀 B가 배포한 `.btn` CSS가 팀 A의 버튼 색을 바꾼다(실험 ②).
- 헤더 섬과 사이드바 섬이 같은 장바구니 API를 따로 부른다(실험 ③).

## 동작·원리

### 1. Islands — 정적 HTML + 독립 하이드레이션

```text
  서버 HTML
  ┌──────────────────────────────────────────┐
  │ <article> 정적 </article>                 │
  │ <astro-island client="visible" …>  ── 섬 A: 보일 때 자기 JS만 받아 하이드레이션
  │ <aside> 정적 </aside>                     │
  │ <astro-island client="idle" …>     ── 섬 B: 한가할 때
  └──────────────────────────────────────────┘
   섬마다 루트가 따로다 → 페이지 전체 트리를 클라이언트에서 조립하지 않는다
```

- patterns.dev "Islands Architecture": 진행형(progressive) 하이드레이션은 페이지를 **한 트리**로 보고 가지의 하이드레이션 순서만 정한다. Islands는 그 트리를 클라이언트에서 아예 조립하지 않는다.
- Astro 문서 "Islands"
  - `client:*` 지시어가 없는 UI 프레임워크(React 등) 컴포넌트는 클라이언트 JS를 내보내지 않는다(기본값 0 JS). 단 `.astro` 컴포넌트 안의 `<script>`는 지시어 없이도 번들되어 브라우저로 간다(Astro 문서 "Scripts and event handling").
  - `client:load`(로드 즉시), `client:idle`(한가할 때), `client:visible`(뷰포트에 들어올 때), `client:media`(미디어 쿼리 조건), `client:only`(서버 렌더 생략).
  - *서버 섬(server islands)*: `server:defer`로 개인화 부분만 따로 렌더해, 정적 HTML을 먼저 보이고 그 자리를 나중에 채운다.
- 하이드레이션 비용 측면(전체 vs 섬 하나 실측)은 [19번](../19-hydration-cost-and-partial-hydration/2-summary.md)에 있다.
- 잘 맞는 곳: 콘텐츠 중심 사이트(문서·블로그·마케팅·상품 상세). 안 맞는 곳: 상태가 많은 위젯 사이를 흘러야 하거나, 라우트 변경이 페이지 절반을 바꿔야 하는 앱(patterns.dev).

### 2. 마이크로 프론트엔드 — 조합하는 다섯 장소

```text
  빌드 타임                  서버                       브라우저(런타임)
  ┌──────────┐          ┌──────────────┐          ┌───────────────────────────────┐
  │ npm 패키지 │          │ SSI·ESI·템플릿 │          │ iframe │ JS 로드 후 마운트 │ Web Components │
  │ 로 합침    │          │ 조각 조합      │          │ 강한 격리│ 전역 함수·Module  │ 커스텀 요소       │
  └──────────┘          └──────────────┘          │        │ Federation        │                │
  하나라도 바뀌면 전체          서버 측 UI 조합            └───────────────────────────────┘
  재빌드·동시 배포                                           클라이언트 측 UI 조합
```

| 방식 | 장점 | 비용 (빌드 타임·iframe·JS 런타임 행은 Jackson 글 기준, 나머지는 일반 정리) |
|---|---|---|
| 빌드 타임 통합(패키지) | 단순, 중복 제거 쉬움 | 한 부분을 바꿔도 전체를 다시 빌드·배포 → 독립 배포가 사라짐 |
| 서버 측 조합 | 첫 화면 HTML 완성, JS 없이도 동작 | 서버 인프라, 조각 사이 상호작용은 별도 |
| iframe | 스타일·전역·오류가 강하게 격리 | 조각 사이 통합(라우팅·높이·통신)이 어렵다 |
| JS 런타임 통합 | 가장 유연. 셸이 번들을 받아 마운트 함수 호출 | 의존성 중복, 전역 충돌 관리 |
| Web Components | 표준 커스텀 요소로 경계, Shadow DOM으로 스타일 격리 가능 | 프레임워크 상태·SSR 연동이 별도 |

- microservices.io "Client-side UI composition": 서비스를 소유한 팀이 자기 데이터 영역의 UI 컴포넌트도 만들고, 페이지는 그것들을 조합한다. 서버 측 대안은 "Server-side page fragment composition"이다.
- *Module Federation*: 번들러가 원격 앱의 모듈을 런타임에 가져오고, `shared`로 의존성을 협상해 한 벌만 쓰게 한다.
  - `singleton`(기본 `false`): 켜면 공유 범위에 한 버전만 허용한다. 사용 전에 여러 버전이 공유 범위에 등록돼 있으면 가장 높은 버전을 쓰고, 그 버전이 어떤 소비자의 `requiredVersion`을 못 맞추면 경고한다(webpack ModuleFederationPlugin 문서). 이미 로드된 공유 모듈은 교체되지 않는다 — 나중에 온 원격이 더 높은 버전을 내놓아도 경고 없이 무시된다(webpack "Module Federation" 개념 문서). React처럼 한 벌이어야 하는 라이브러리에 필요하다(module-federation.io "shared").
  - `requiredVersion`: 허용 범위. 못 맞출 때의 기본 동작은 `strictVersion` 기본값에 달렸다. 로컬 대체 모듈이 있고 `singleton`이 아니면 기본이 `true`라 공유 버전을 버리고 대체 모듈을 쓴다. 그 밖(`singleton`이거나 대체 모듈 없음)은 기본 `false`라 콘솔 경고만 낸다. `singleton`이나 대체 모듈 없는 모듈에 `strictVersion: true`를 주면 런타임 오류가 난다(webpack ModuleFederationPlugin 문서).

### 3. 왜 React는 한 벌이어야 하나

```text
  셸 번들                               원격 번들(React 사본 B 포함)
  react(A) ── react-dom(A) ─ 렌더 중 ─> 원격 컴포넌트 Reviews() 호출
              │ "현재 디스패처"를            └─ useState ← react(B)에서 import
              │  react(A)의 내부 슬롯에 설정          │
              │                                      └─ react(B)의 슬롯은 비어 있음(null)
              v                                         → TypeError / Invalid hook call
```

- react.dev "Invalid Hook Call Warning": 훅이 동작하려면 앱 코드의 `react` import가 `react-dom` 안의 `react` import와 **같은 모듈**로 풀려야 한다. 두 개의 다른 exports 객체로 풀리면 경고가 난다.
- 그래서 마이크로 프론트엔드에서 React를 공유하지 않으려면, 각 팀이 자기 `react-dom`으로 자기 영역에 **직접 마운트**해야 한다. 그 대가는 react-dom n벌이다.

### 실험: React 두 벌·팀 간 CSS·섬 사이 이중 fetch

환경: headless Chrome 151.0.7922.173, React·react-dom 19.2.8 운영 빌드, esbuild 0.28.2 `--minify`, Node 20.19.6 서버(127.0.0.1), 압축 없음. 각 1회(결과가 결정적인 기능 실험).

```jsx
// 셸(host.jsx 발췌): 자기 React를 공유용으로 내보내고, 원격 스크립트를 받아 그 컴포넌트를 렌더
window.__shared = { React };
s.src = '/' + remote + '.js'; s.onload = () => setRemote(() => window.__remote);
// remote-dup.jsx: 원격 팀이 React를 자기 번들에 넣음(사본 B)
import React, { useState } from 'react';
window.__remote = function Reviews() { const [n, setN] = useState(0); return <button id="r" …>리뷰 {n}</button>; };
// remote-shared.jsx: 셸이 공유한 React 사용(번들에 React 없음)
const React = window.__shared.React; const { useState } = React;
// remote-selfmount.jsx: React+ReactDOM 전체를 넣고 자기 div에 createRoot로 직접 마운트
```

`(실험, headless Chrome 151, React 19.2.8, 2026-10-04)`

```text
① remote-dup       JS 합계 204067B | 같은 React? false | 원격 오류: Cannot read properties of null (reading 'useState')
① remote-shared    JS 합계 194926B | 같은 React? true | 버튼 리뷰 0 → 클릭 후 리뷰 1
① remote-selfmount JS 합계 388968B | 같은 React? n/a | 버튼 리뷰 0 → 클릭 후 리뷰 1
```

- remote-dup: 셸의 react-dom이 렌더하는데, 원격 컴포넌트는 사본 B의 `useState`를 불렀다. 사본 B의 디스패처가 비어 있어 `null`에서 `useState`를 읽다 실패했다. 원격 번들은 react만 넣어 9,340B(gzip 3,564B)로 작았지만 작동하지 않는다.
- remote-shared: 같은 React를 써서 정상 동작. 원격 번들은 199B.
- remote-selfmount: 각자 react-dom으로 마운트하니 동작은 했다. 대신 JS가 두 배(셸 194,727B + 원격 194,241B, 각각 gzip 약 60KB)가 됐다.
- 첫 시도에서 selfmount의 셸 쪽 자리 컴포넌트가 사본 B의 `React.useRef`를 불러 `Minified React error #321`(Invalid hook call)이 났다. 같은 원인이 다른 모양으로 나타난 것이다.

② 팀 A가 `.btn { background: rgb(0,0,255) }`, 나중에 배포된 팀 B가 같은 클래스에 `rgb(255,0,0)`. 팀 A 위젯의 사본 하나는 Shadow DOM 안에 자기 스타일과 함께 넣었다.

```text
② 팀 A 버튼 배경: rgb(255, 0, 0) | Shadow DOM 안 팀 A 버튼: rgb(0, 0, 255)
```

- 같은 선택자·같은 명시도면 나중 규칙이 이긴다. 팀 A의 버튼이 빨개졌다.
- 문서 스타일시트는 Shadow 트리 안의 요소에 선택자로 닿지 않는다. 섀도 안 버튼은 파란색을 유지했다([languages/web-api/12-shadow-dom](../../../languages/web-api/12-shadow-dom/2-summary.md)).

③ 헤더 섬과 사이드바 섬이 장바구니 수를 표시한다. `bundled`는 섬마다 저장소 코드를 번들에 넣었고, `module`은 두 섬이 같은 URL의 ES 모듈 `/cart-store.js`를 import한다.

```js
// cart-store.js — 모듈 최상위에서 한 번 fetch
console.log('cart-store 평가');
export const cart = fetch('/api/cart').then(r => r.json());
// island-a.js / island-b.js
import { cart } from './cart-store.js';
```

```text
③ bundled /api/cart 요청 2회 | 'cart-store 평가' 로그 2회 | 헤더 장바구니 3 / 사이드 장바구니 3
③ module  /api/cart 요청 1회 | 'cart-store 평가' 로그 1회 | 헤더 장바구니 3 / 사이드 장바구니 3
```

- 번들에 각자 넣은 코드는 서로 다른 모듈 인스턴스다. 같은 요청을 두 번 했다.
- 같은 URL의 ES 모듈은 한 번만 평가됐다. HTML 표준의 *module map*은 (URL, 모듈 종류)를 키로 해서, import된 모듈 스크립트가 Document·워커마다 한 번만 fetch·파싱·평가되게 한다. 쿼리 문자열이나 조각(`#…`)이 다르면 다른 항목이다.

### 4. 조각 사이 통신 — 공유 상태보다 메시지

```text
  권장: 이벤트·콜백·URL                        피할 것: 공유 전역 객체
  섬 A ─ dispatchEvent(new CustomEvent(        window.appState.cart = …  ← 아무 팀이나 읽고 씀
         'cart:changed', {detail}))            → 형태를 바꾸면 어느 팀이 깨질지 모른다
  섬 B ─ addEventListener('cart:changed', …)     (숨은 결합)
```

- Jackson: 마이크로 프론트엔드는 메시지·이벤트로 통신하고 공유 상태를 피한다. 마이크로서비스가 DB를 공유하면 결합이 생기는 것처럼, 자료 구조와 도메인 모델을 공유하는 순간 큰 결합이 생긴다.
- 조각 사이 계약은 이벤트 이름과 `detail`의 형태다. API처럼 문서화하고 버전을 관리한다([software-design/43-data-across-boundaries](../../software-design/43-data-across-boundaries/2-summary.md)).

## 쓰이는 자료구조·알고리즘

- **모듈 그래프 공유(중복 제거)**: 번들러는 import 그래프를 만들어 같은 모듈을 한 번만 넣는다. 브라우저는 module map((URL, 종류) → 모듈)으로 같은 URL을 한 번만 평가한다. 독립 빌드된 번들끼리는 이 그래프가 이어지지 않아 중복이 생긴다(실험 ①·③). [data-structure/34-dependency-resolver](../../data-structure/34-dependency-resolver/2-summary.md) · [data-structure/08-graph](../../data-structure/08-graph/2-summary.md)
- **버전 협상**: Module Federation `shared`는 각 소비자에게 공유 범위에서 자기 허용 범위(`requiredVersion`)를 만족하는 가장 높은 제공 버전을 준다(비싱글턴이면 여러 버전이 공존). `singleton`이면 교집합이 없어도 한 버전을 쓰고 경고한다. 이미 로드된 버전·`strictVersion` 설정도 결과를 바꾼다(webpack 문서).
- **이벤트 버스(발행·구독)**: 이름 → 리스너 목록. DOM의 `EventTarget`·`CustomEvent`가 그대로 쓰인다([languages/web-api/21-custom-events](../../../languages/web-api/21-custom-events/2-summary.md)).
- **스코프 트리**: Shadow DOM은 선택자 매칭의 범위를 섀도 트리 안으로 나눈다. CSS 이름 충돌을 구조로 막는다.
- **요청 합치기**: 공유 모듈 최상위의 promise 하나를 여러 섬이 기다린다(21번의 키 캐시와 같은 생각).

## 적용 — 풀어나가는 법

### 1. Islands를 고를 때

1. 페이지에서 상호작용 영역을 표시한다. 대부분이 정적이면 Islands 후보다.
2. 섬마다 하이드레이션 시점을 정한다: 첫 화면 핵심은 `load`, 아래쪽은 `visible`, 덜 중요한 것은 `idle`.
3. 섬 사이 공유 데이터는 공유 모듈(같은 URL)이나 작은 스토어로 한 번만 가져온다(실험 ③).
4. 섬 사이 흐름이 많아지면(장바구니·필터·목록이 서로 얽힘) 그 영역은 하나의 섬으로 합친다.

### 2. 마이크로 프론트엔드를 고를 때

1. 먼저 묻는다: 팀이 정말 독립 배포가 필요한가? 아니면 모노레포 + 모듈 경계로 충분한가([software-design/45-monolith-vs-microservices](../../software-design/45-monolith-vs-microservices/2-summary.md)와 같은 질문).
2. 통합 방식을 정한다(위 표). 첫 화면이 중요하면 서버 측 조합, 강한 격리가 필요하면 iframe, 유연성이 필요하면 JS 런타임 통합.
3. 공유 의존성 정책: 한 벌이어야 하는 것(React·라우터·디자인 시스템 런타임)은 싱글턴으로 공유하고 허용 버전 범위를 합의한다.
4. 스타일 격리 규칙: Shadow DOM, CSS Modules, 팀 접두사(BEM 등) 중 하나를 정한다.
5. 통신 계약: 이벤트 이름·`detail` 스키마·URL 파라미터를 문서화한다. 전역 객체 공유를 금지한다.
6. 성능 예산: 조각별 JS 크기를 CI에서 잰다(20번). 의존성 중복을 번들 분석으로 확인한다.

### 3. 코드 — Module Federation 공유 설정(예시, webpack 계열)

```js
new ModuleFederationPlugin({
  name: 'shell',
  remotes: { reviews: 'reviews@https://cdn.example.com/reviews/remoteEntry.js' },
  shared: {
    react:       { singleton: true, requiredVersion: '^19.0.0' },
    'react-dom': { singleton: true, requiredVersion: '^19.0.0' },
  },
});
```

### 4. 코드 — Web Component 경계 + 이벤트로 통신

```js
class CartBadge extends HTMLElement {
  connectedCallback() {
    const root = this.shadowRoot ?? this.attachShadow({ mode: 'open' });  // 팀 스타일 격리 — 재연결 때 두 번 붙이면 NotSupportedError
    root.innerHTML = `<style>.btn{background:#00f}</style><button class="btn">장바구니 <b>0</b></button>`;
    this._onChange = (e) => { root.querySelector('b').textContent = e.detail.count; };
    window.addEventListener('cart:changed', this._onChange);
  }
  disconnectedCallback() { window.removeEventListener('cart:changed', this._onChange); }  // 리스너 누수 방지
}
customElements.define('team-d-cart-badge', CartBadge);
// 다른 팀: window.dispatchEvent(new CustomEvent('cart:changed', { detail: { count: 3 } }));
```

- 커스텀 요소 이름에 팀 접두사를 붙여 이름 충돌을 막는다. 수명주기 콜백은 [languages/web-api/13-custom-element-lifecycle](../../../languages/web-api/13-custom-element-lifecycle/2-summary.md).

### 5. 진단

- 콘솔에서 React 사본 확인: 원격이 쓰는 React 객체와 셸의 React 객체를 비교한다(실험 ①의 `같은 React?`). react.dev 문서도 `window.React1 === window.React2` 비교를 권한다.
- 번들 분석기(esbuild `--metafile`, webpack-bundle-analyzer 등)로 `react-dom`이 몇 번 들어갔는지 센다.
- Network 패널에서 같은 API가 한 화면에 몇 번 불리는지(실험 ③).
- DevTools Elements의 Computed 패널에서 어느 스타일시트의 규칙이 이겼는지 본다(실험 ②).

## 장애 시나리오와 대처

### 1. 마이크로 프론트엔드마다 React 사본 → 번들 중복·싱글턴 두 벌(훅 오류) (⚠ 커리큘럼)

- **현상**: 원격 위젯 자리에 오류 화면. 또는 동작은 하는데 첫 로드가 무겁다.
- **보이는 형태**: `TypeError: Cannot read properties of null (reading 'useState')`, `Minified React error #321`(Invalid hook call). 번들 분석에 `react-dom` 여러 벌. 실험 ①: selfmount JS 388,968B vs shared 194,926B.
- **원인**: 독립 빌드한 원격 번들이 자기 React를 품었다. 셸의 react-dom이 그 컴포넌트를 렌더하면 두 React의 내부 디스패처가 어긋난다.
- **대처**: React를 싱글턴으로 공유한다(Module Federation `shared.singleton`, import map, 셸이 전역 제공). 공유가 어려우면 각자 자기 react-dom으로 자기 영역에 마운트하고 크기 비용을 받아들인다.

### 2. 팀 간 CSS 충돌 (⚠ 커리큘럼)

- **현상**: 다른 팀 배포 뒤 우리 버튼 색·여백이 바뀐다. 우리 코드는 바뀌지 않았다.
- **보이는 형태**: Computed 패널에서 다른 팀 스타일시트의 규칙이 이긴다. 실험 ②: 팀 A 버튼이 `rgb(255, 0, 0)`.
- **원인**: CSS는 전역 캐스케이드다. 출처(작성자 스타일)·`!important`·캐스케이드 레이어가 같고 같은 클래스 이름·같은 명시도면 나중 규칙이 이긴다(CSS Cascade 5).
- **대처**: Shadow DOM(실험 ②에서 섀도 안 버튼은 `rgb(0, 0, 255)` 유지), CSS Modules·CSS-in-JS의 해시 클래스, 팀 접두사 규칙. 전역 리셋·기본 요소 선택자(`button {}`)는 셸 팀만 소유한다.

### 3. 공유 상태를 전역 객체로 주고받음 → 숨은 결합 (⚠ 커리큘럼)

- **현상**: 팀 B가 `window.appState.user`의 필드 이름을 바꾸자 팀 C의 화면이 깨졌다. 팀 C 저장소에는 변경이 없다.
- **보이는 형태**: `TypeError: Cannot read properties of undefined` 같은 런타임 오류가 다른 팀 영역에서 난다. 저장소 검색으로 의존 관계가 잘 안 보인다.
- **원인**: 전역 객체가 문서화되지 않은 계약이 됐다. Jackson이 경고한 "공유 자료 구조 = 큰 결합"이다.
- **대처**: 이벤트·콜백·URL로 통신하고, 이벤트 이름·`detail` 형태를 계약으로 문서화·버전 관리한다. 꼭 공유해야 할 데이터는 서버 API로 각자 가져오되 요청을 합친다(장애 4).

### 4. 섬 사이 통신 부재 → 같은 데이터 이중 fetch (⚠ 커리큘럼)

- **현상**: 헤더와 사이드바가 장바구니 수를 따로 가져온다. 가끔 둘의 숫자가 다르다.
- **보이는 형태**: Network 패널에 같은 API가 두 번. 실험 ③ bundled: `/api/cart` 2회.
- **원인**: 섬마다 독립 번들이라 저장소 코드가 두 벌이다. 서로의 요청을 모른다.
- **대처**: 같은 URL의 공유 ES 모듈로 저장소를 한 번만 평가하게 한다(실험 ③ module: 1회). 또는 한 섬이 가져와 이벤트로 알린다. 갱신도 같은 경로로 흘려 두 숫자가 어긋나지 않게 한다.

### 5. 싱글턴 버전 협상 실패 → 한 팀만 깨짐

- **현상**: 셸이 React를 올렸더니 오래된 원격 하나가 이상하게 동작한다.
- **보이는 형태**: Module Federation 콘솔 경고(허용 범위를 못 맞춤), 그 원격 영역의 런타임 오류.
- **원인**: `singleton`이면 한 버전만 쓴다. 버전이 다르면(사용 전에 함께 등록된 경우) 높은 버전이 쓰이고, 그 버전의 바뀐 동작을 원격이 견디지 못했다.
- **대처**: 공유 라이브러리의 허용 범위를 팀 간 합의로 관리한다. 메이저 업그레이드는 원격들의 호환 확인 뒤 셸이 올린다. 계약 테스트처럼 셸·원격 조합을 CI에서 띄워 본다([testing/13-contract-testing](../../testing/13-contract-testing/2-summary.md)).

## 핵심 문장

- Islands는 상호작용 여부로, 마이크로 프론트엔드는 소유 팀으로 페이지를 나눈다. 둘 다 조각 사이 경계를 어떻게 긋느냐의 문제다.
- Islands는 페이지 전체 트리를 클라이언트에서 조립하지 않는다. 섬마다 자기 JS를 자기 시점에 하이드레이션한다.
- 독립 빌드한 번들끼리는 의존성 그래프가 이어지지 않아 같은 라이브러리가 중복된다. React처럼 한 벌이어야 하는 라이브러리는 싱글턴으로 공유한다.
- 같은 URL의 ES 모듈은 module map 덕분에 한 번만 평가된다. 섬 사이 공유 저장소를 이렇게 두면 요청이 한 번이다.
- CSS는 전역이다. 팀 경계에는 Shadow DOM·해시 클래스·접두사 같은 격리 규칙이 필요하다.
- 조각 사이는 공유 객체가 아니라 이벤트·URL 같은 메시지로 통신하고, 그 메시지를 계약으로 관리한다.

## 관련 주제·근거

- 선행
  - [10-rendering-strategies](../10-rendering-strategies/2-summary.md) · [09-js-modules-and-bundling](../09-js-modules-and-bundling/2-summary.md)
  - [19-hydration-cost-and-partial-hydration](../19-hydration-cost-and-partial-hydration/2-summary.md) — 섬의 비용 측면 실측
  - [21-component-and-state-patterns](../21-component-and-state-patterns/2-summary.md) — 상태 위치·서버 상태 캐시
- 후속·연결
  - [20-performance-budgets-and-regression-gates](../20-performance-budgets-and-regression-gates/2-summary.md) — 조각별 JS 예산
  - [software-design/45-monolith-vs-microservices](../../software-design/45-monolith-vs-microservices/2-summary.md) · [software-design/43-data-across-boundaries](../../software-design/43-data-across-boundaries/2-summary.md)
  - [testing/13-contract-testing](../../testing/13-contract-testing/2-summary.md)
  - [data-structure/34-dependency-resolver](../../data-structure/34-dependency-resolver/2-summary.md) · [data-structure/08-graph](../../data-structure/08-graph/2-summary.md)
  - [languages/web-api/12-shadow-dom](../../../languages/web-api/12-shadow-dom/2-summary.md) · [13-custom-element-lifecycle](../../../languages/web-api/13-custom-element-lifecycle/2-summary.md) · [21-custom-events](../../../languages/web-api/21-custom-events/2-summary.md)
- 문서·표준
  - Jason Miller "Islands Architecture"(2020-08-11) — 정의, Katie Sylor-Miller(2019) <https://jasonformat.com/islands-architecture/>
  - patterns.dev "Islands Architecture" — 진행형 하이드레이션과의 차이, 맞는 곳·안 맞는 곳 <https://www.patterns.dev/vanilla/islands-architecture/>
  - Astro 문서 "Islands" — `client:*` 지시어, `server:defer` <https://docs.astro.build/en/concepts/islands/>
  - Astro "Template directives reference" — `client:load`·`idle`(requestIdleCallback)·`visible`(IntersectionObserver)·`media`·`only`(서버 렌더 생략) <https://docs.astro.build/en/reference/directives-reference/>
  - Cam Jackson "Micro Frontends"(martinfowler.com, 2019-06-19) — 통합 방식, 빌드 타임 통합의 동시 배포, iframe의 유연성 한계, React n번 다운로드, 공유 상태 회피 <https://martinfowler.com/articles/micro-frontends.html>
  - microservices.io "Client-side UI composition" <https://microservices.io/patterns/ui/client-side-ui-composition.html>
  - module-federation.io "shared" — `singleton`·`requiredVersion`·`eager` <https://module-federation.io/configure/shared>
  - react.dev "Invalid Hook Call Warning" — 같은 모듈로 풀려야 하는 `react` <https://react.dev/warnings/invalid-hook-call-warning>
  - WHATWG HTML "Web application APIs" — module map: (URL, 모듈 종류) 키, Document·워커당 한 번 fetch·파싱·평가 <https://html.spec.whatwg.org/multipage/webappapis.html#module-map>
- 실험 목록(작업 scratchpad `wp/10/e22/`)
  - ① 원격 React 사본·공유·직접 마운트 3가지: JS 바이트 합(응답 본문), React 동일성, 오류 메시지, 클릭 동작.
  - ② 같은 선택자 두 팀 CSS와 Shadow DOM: `getComputedStyle().backgroundColor`.
  - ③ 섬 2개의 저장소 코드 번들 내장 vs 공유 ES 모듈: 서버 요청 수, 모듈 평가 로그 수.
  - 환경: headless Chrome 151.0.7922.173, React 19.2.8, esbuild 0.28.2, Node 20.19.6, 127.0.0.1.
