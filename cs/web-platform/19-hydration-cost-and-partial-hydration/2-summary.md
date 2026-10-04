# web-platform/19-hydration-cost-and-partial-hydration — 하이드레이션 비용과 점진·선택적·부분 하이드레이션, 서버 컴포넌트 — 정리 (힌트)

## 해결하는 문제

SSR은 화면을 빨리 보여 준다. 그러나 JS 핸들러(`onClick`)에만 의존하는 버튼은 JS가 도착해 하이드레이션을 마칠 때까지 눌러도 반응하지 않는다(10번). `<form>` 안의 제출 버튼처럼 HTML 기본 동작이 있는 버튼은 JS 없이도 작동한다(WHATWG HTML `button` 요소의 활성화 동작).

```text
  SSR 페이지의 시간축 (10번 실험, SSR, CPU 4×·네트워크 스로틀)
  0        0.6~0.7초                                   3.1~3.6초
  |── HTML ──| FCP: 보인다 ······· JS 195KB 다운로드 ······ 하이드레이션 ──| 반응한다
                          ↑
                   이 구간의 클릭은 어떻게 되나?
```

- 이 구간의 클릭은 사라질 수 있다. 아래 실험 ①에서 JS가 늦게 온 페이지의 첫 클릭은 반영되지 않았다.
- 하이드레이션 자체도 메인 스레드를 오래 잡는다. 그동안 들어온 입력은 기다린다(INP 악화).
  - *하이드레이션 비용*: JS 다운로드 + 파싱·실행 + 컴포넌트 트리 재실행 + DOM 대조 + 리스너 연결. 페이지의 인터랙티브하지 않은 부분까지 같이 치른다.

쉬운 예: 전시장의 가구 전부에 전원선을 꽂아야 문을 여는 가게다.
- 실제로 전기가 필요한 것은 조명 하나와 계산대뿐이다. 나머지 수백 개는 그냥 보기만 하는 가구다.
- 방법은 셋이다. 필요한 것부터 꽂기(선택적), 손님이 다가갈 때 꽂기(점진·지연), 전기 필요 없는 가구엔 아예 선을 안 달기(부분 하이드레이션·islands·서버 컴포넌트).

똑같은 구조다. 페이지의 대부분이 정적 콘텐츠인데 전체를 하이드레이션하면 쓰지 않을 비용을 치른다.

실무 예:
- 상품 목록 5000행 + 장바구니 버튼 하나 페이지를 통째로 하이드레이션 → 아래 실험 ③에서 최장 태스크 0.45~0.62초.
- 상세 페이지의 리뷰 위젯 코드가 늦게 와서, 그 사이 누른 "도움돼요" 클릭이 사라진다(실험 ②).
- 초기 상태 JSON이 HTML에 그대로 들어가 문서가 두 배 가까이 커진다(실험 ③의 HTML 크기).

## 동작·원리

### 1. 하이드레이션이 하는 일과 비용의 출처

```text
  서버                                  브라우저
  컴포넌트 트리 ─렌더→ HTML ─────────→ DOM (보임)
        │                                │
        └─ 데이터 JSON ──────────────→ window.__DATA__
                                         │
               JS 번들 ─────────────→ 컴포넌트를 다시 실행 → 트리 재구성
                                         │
                                  DOM과 대조하며 리스너 연결 (반응)
```

- Qwik 문서("Resumable")는 하이드레이션이 되살리는 것을 셋으로 든다.
  - 리스너: 어느 DOM 노드에 어떤 핸들러가 붙는지.
  - 컴포넌트 트리: 프레임워크 내부 자료구조.
  - 애플리케이션 상태: 서버에서 가져온 데이터.
- 비용은 페이지 크기에 비례한다. 화면에 보이는 정적 텍스트도 컴포넌트로 만들었다면 다시 실행된다.
- web.dev "Rendering on the Web": 서버 렌더 페이지는 로드되어 인터랙티브해 보이지만, 컴포넌트 스크립트가 실행되고 핸들러가 붙기 전에는 입력에 반응하지 못한다.

### 실험 ①: JS가 오기 전 클릭

SSR 페이지(행 200개)의 `full.js`를 서버가 2초 늦게 보낸다. 버튼이 보이자마자 클릭한다.

`(실험, headless Chrome 151, React 19.2.8, 스로틀 없음, 2026-10-04)`

```text
① 클릭 시각 328ms, 하이드레이션 끝 2232ms → 버튼: 장바구니 0
   하이드레이션 뒤 다시 클릭 → 버튼: 장바구니 1
```

- 328ms의 클릭은 버려졌다. 그 시점에는 리스너가 없다. React도 아직 로드되지 않았으니 기록해 둘 주체가 없다.
- 하이드레이션 뒤 클릭은 정상 처리됐다.

### 2. 줄이는 방법의 스펙트럼

```text
  전체 하이드레이션 ── 점진 ── 선택적 ── 부분(islands) ── 서버 컴포넌트 ── 재개(resumability)
  전부 한 번에        순서를 나눔  상호작용 우선   필요한 곳만       서버 전용 코드는     하이드레이션 대신
                                                                   클라이언트에 안 감   직렬화된 상태로 재개
```

| 방법 | 무엇을 줄이나 | 예 |
|---|---|---|
| 점진 하이드레이션(progressive) | 한 번에 하는 양 — 조각별로 나눠 부팅 | web.dev 정의 |
| 선택적 하이드레이션(selective) | 순서 — 사용자가 건드린 경계를 먼저 | React 18+ `<Suspense>` 경계 |
| 부분 하이드레이션(partial)·islands | 대상 — 정적 부분은 하이드레이션하지 않음 | Astro `client:*`, 22번 |
| 서버 컴포넌트 | 대상과 코드 — 서버 전용 컴포넌트의 코드·입력은 번들에 없음 | React Server Components |
| 재개(resumability) | 재실행 자체 — 리스너·상태를 HTML에 직렬화 | Qwik |

- *점진 하이드레이션*: 앱 조각을 한꺼번에가 아니라 하나씩 부팅하는 것(web.dev).
- *부분 하이드레이션*: 페이지를 분석해 대부분 정적인 부분을 찾아, 그 부분의 클라이언트 비용을 거의 0으로 줄이는 것(web.dev).
- *서버 컴포넌트*: 번들링 전에, 클라이언트 앱과 분리된 환경(빌드 서버·웹 서버)에서 미리 렌더링되는 컴포넌트. 브라우저로 보내지지 않는다. `useState`·`useEffect`를 쓸 수 없고, 상호작용은 `"use client"` 컴포넌트와 조합한다(react.dev "Server Components").
  - react.dev의 예: 마크다운 렌더에 쓰는 라이브러리(gzip 75K)를 클라이언트가 내려받지 않아도 된다.
- *재개(resumability)*: 리스너를 `<button on:click="./chunk.js#handler_symbol">`처럼 HTML 속성으로 직렬화해, 클릭이 일어날 때 해당 코드만 가져온다(Qwik 문서).

### 3. React의 선택적 하이드레이션과 클릭 처리

```text
  hydrateRoot
   ├─ 셸(경계 밖) ── 먼저 하이드레이션
   ├─ <Suspense> A ── 코드·데이터가 있으면 이어서
   └─ <Suspense> B ── 코드가 아직 없으면 "탈수 상태(dehydrated)"로 남음
                         │
            사용자가 B 안을 클릭 ──> 캡처 단계에서 B를 동기 하이드레이션 시도
                                      ├─ 성공하면 → 그 클릭을 바로 처리
                                      └─ 코드가 없어 못 하면 → 클릭은 전파 중단(재생 안 함)
```

- React 18 WG 글(2021)은 SSR의 병목을 셋으로 정리했다. 데이터를 다 가져와야 보여 줄 수 있고, 코드를 다 받아야 하이드레이션할 수 있고, 다 하이드레이션해야 상호작용할 수 있다. 해법은 스트리밍 HTML과 선택적 하이드레이션이다.
- 이산 이벤트(클릭 등)의 처리 방식은 이후 바뀌었다. React PR #22448 "Sync hydrate discrete events in capture phase and dont replay discrete events": 이산 이벤트는 **재생하지 않고**, 루트의 캡처 단계에서 해당 경계를 동기 하이드레이션해 그 자리에서 처리하려 한다. 연속 이벤트(포커스·마우스 오버 등)는 대기열에 넣었다가 재생한다.
- react-dom 19.2.8 소스(`react-dom-client.development.js`의 `dispatchEvent`)도 같은 구조다.
  - `queueIfContinuousEvent`는 `focusin` 같은 연속 이벤트만 대기열에 넣는다.
  - `discreteReplayableEvents`(click·keydown·input 등)는 막는 경계를 동기 레인으로 하이드레이션하는 반복문을 돈다. 그래도 막혀 있으면 `nativeEvent.stopPropagation()`으로 끝낸다.

### 실험 ②: 아직 하이드레이션 안 된 경계를 클릭

②-a: 셸(A 버튼)은 하이드레이션됐고, B 버튼이 든 `<Suspense>` 경계의 코드(`React.lazy` 청크)는 서버가 1.5초 늦게 보낸다. 그 사이 B를 클릭한다.

`(실험, headless Chrome 151, React 19.2.8, 스로틀 없음, 2026-10-04)`

```text
② 셸 하이드레이션 153ms, B 클릭 202ms 직후 B: 리뷰 0
   청크 도착 뒤 B: 리뷰 0 / A: 찜 0
   다시 클릭 → B: 리뷰 1
```

- 코드가 없어 동기 하이드레이션이 불가능했다. 클릭은 재생되지 않았다. 위 소스 구조와 맞는다.

②-b: 코드는 다 왔고 하이드레이션이 진행 중일 때(앞 경계에 5000행, 뒤 경계에 B) B를 클릭한다. CPU 4×, 뷰포트 1280×720, 각 3회. `rootCommit`·`bLayout`·`heavyLayout`은 셸·B·5000행 경계의 `useLayoutEffect` 시각(= 커밋 시각)이다.

처음 구성은 B가 5000행 아래(y≈130,032px, 화면 밖)에 있어서, 좌표로 누른 클릭이 B가 아니라 `<html>`에 떨어졌다. 그래서 `리뷰 0`이 나왔다(클릭 대상 `HTML`, React 루트에는 이벤트가 오지 않음). B를 화면 안으로 스크롤한 뒤 같은 시점에 누르면 결과가 달라진다(출력의 이벤트 배열 필드는 생략):

```text
scroll false boxY 130032 {"start":3547,"rootCommit":3638,"bLayout":4622,"heavyLayout":4622,"b":"리뷰 0","docClick":["HTML@4228"],"rootEv":[]}
scroll true boxY 687 {"start":3226,"rootCommit":3333,"bLayout":3980,"heavyLayout":4582,"clickHandled":3996,"b":"리뷰 1", …}
scroll true boxY 687 {"start":3559,"rootCommit":3643,"bLayout":3943,"heavyLayout":4414,"clickHandled":3958,"b":"리뷰 1", …}
scroll true boxY 687 {"start":3231,"rootCommit":3359,"bLayout":3856,"heavyLayout":4428,"clickHandled":3869,"b":"리뷰 1", …}
```

- B를 실제로 누르면, 5000행 경계가 하이드레이션되는 도중인데도 B가 **먼저** 커밋됐다(`bLayout` 3856~3980 < `heavyLayout` 4414~4582). 그 직후 핸들러가 실행됐다(`clickHandled`, `리뷰 1`).
- PR #22448의 설계 의도(캡처 단계에서 클릭된 경계를 동기 하이드레이션하고, 그 자리에서 처리)와 맞는다. 코드가 이미 있으면 하이드레이션 **중** 클릭은 사라지지 않는다.
- B를 앞 경계로 옮긴 구성(화면 안)에서도 3회 모두 `리뷰 1`이었다.
- 사라지는 경우는 ①(React 자체가 아직 없음)과 ②-a(그 경계의 코드가 아직 없음)다. 중요한 동작은 이 구간을 위해 JS 없이도 작동하는 HTML(`<form action>`, `<a href>`)로 만든다.
- 실험 교훈: 좌표 클릭(`mouse.click`)은 스크롤하지 않는다. 화면 밖 요소를 누르는 실험은 클릭 대상(`event.target`)을 같이 기록한다.

### 실험 ③: 전체 하이드레이션 vs 섬 하나

상품 행 수(n)가 같은 서버 HTML을 두 방식으로 만들어 하이드레이션한다. HTML 자체도 다르다(아래 정의 — full에만 버튼과 JSON이 있다).
- `full`: 페이지 전체가 한 React 트리. 행마다 "담기" 버튼 컴포넌트가 있고, 하이드레이션 입력으로 전체 행 JSON을 HTML에 넣는다.
- `island`: 목록은 정적 HTML(버튼 없음). 장바구니 카운터 하나만 `hydrateRoot(#island-cart)`. JSON 없음.

측정은 `load` 300ms 뒤에 하이드레이션을 시작해 첫 레이아웃·페인트 비용을 뺐다. "하이드레이션" = `hydrateRoot` 직전부터 카운터의 `useEffect`까지, "최장 태스크" = 그 이후 관찰된 Long Task 중 최대.

```jsx
// full-entry.jsx(발췌)
const go = () => { window.__hydrateStart = performance.now(); hydrateRoot(document.getElementById('root'), <FullPage rows={window.__DATA__} />); };
// island-entry.jsx(발췌) — 섬 하나만
const go = () => { window.__hydrateStart = performance.now(); hydrateRoot(document.getElementById('island-cart'), <Counter />); };
```

`(실험, headless Chrome 151, React 19.2.8 운영 빌드, CPU 4×, 각 5회 최소~최대, 2026-10-04)`

```text
③ n=500 full   하이드레이션 177~256ms | 최장 태스크 153~225ms | HTML 58852B
③ n=500 island 하이드레이션 79~115ms | 최장 태스크 52~74ms | HTML 25500B
③ n=2000 full   하이드레이션 254~326ms | 최장 태스크 228~290ms | HTML 236144B
③ n=2000 island 하이드레이션 84~122ms | 최장 태스크 50~77ms | HTML 100146B
③ n=5000 full   하이드레이션 478~657ms | 최장 태스크 446~618ms | HTML 593744B
③ n=5000 island 하이드레이션 70~114ms | 최장 태스크 0~68ms | HTML 250446B
```

- 전체 하이드레이션 시간은 행 수를 따라 늘었다(177~256 → 478~657ms). 섬 하나는 행 수와 거의 무관했다(70~122ms).
- 사실 점검 재실행(같은 코드, 다른 작업자의 브라우저가 동시에 돌던 상태): full 203~309 → 315~490 → 523~865ms, island 92~108 / 96~176 / 105~168ms. 절대값은 부하에 따라 더 컸지만 경향(전체는 행 수에 비례, 섬은 거의 일정)과 HTML 크기는 같았다.
- 전체 방식의 최장 태스크는 n=5000에서 0.45~0.62초다. 이 동안 들어온 입력은 그만큼 기다린다.
- HTML은 전체 방식이 약 2.3~2.4배 컸다. 차이의 대부분은 하이드레이션 입력 JSON과 버튼 마크업이다.
- 주의: 두 방식 모두 react-dom 번들(약 194KB, 압축 전)은 똑같이 받는다. 이 실험의 섬은 **하이드레이션 작업과 데이터**를 줄였지, 라이브러리 크기를 줄이지 않았다. 섬 프레임워크(Astro)는 지시어 없는 UI 프레임워크 컴포넌트의 코드도 번들에서 뺀다(22번).
- 첫 시도에서는 스크립트 실행 직후 측정을 시작해 레이아웃·페인트까지 섞였다(섬 n=5000이 1.4~1.6초). 측정 시작점을 `load` 이후로 옮겨 하이드레이션만 분리했다.

## 쓰이는 자료구조·알고리즘

- **DOM 트리와 컴포넌트 트리의 동시 순회**: 컴포넌트를 깊이 우선으로 렌더하며 기존 DOM 커서를 같은 순서로 전진시켜 대조한다. 비용은 대상 노드 수에 비례한다(실험 ③의 full). [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md)
- **우선순위 정렬 목록**: react-dom 19.2.8의 `queuedExplicitHydrationTargets`는 명시적 하이드레이션 요청을 우선순위 순으로 끼워 넣는다(삽입 위치를 찾아 `splice`). 우선순위 큐의 단순 구현이다. [data-structure/07-heap](../../data-structure/07-heap/2-summary.md)
- **직렬화**: 서버 상태를 JSON으로 HTML에 넣고 클라이언트가 파싱한다. 크기는 데이터에 비례하고, HTML 마크업과 정보가 겹친다.
- **지연 로딩 트리거**: 보일 때(`IntersectionObserver`), 한가할 때(`requestIdleCallback`), 상호작용할 때(이벤트 위임) 하이드레이션을 시작한다. [languages/web-api/35](../../../languages/web-api/35-intersection-observer/2-summary.md) · [languages/web-api/39](../../../languages/web-api/39-idle-scheduling/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 순서

1. 측정: 랩에서 CPU 4× 스로틀로 FCP·하이드레이션 끝 시각·최장 태스크를 잰다. RUM에서는 INP와 "하이드레이션 전 클릭" 비율을 본다.
2. 지도 그리기: 페이지에서 실제로 상호작용하는 부분을 표시한다. 대개 일부다.
3. 대상 줄이기: 정적 부분을 하이드레이션 대상에서 뺀다(서버 컴포넌트, islands). `"use client"` 경계를 가능한 한 잎 쪽으로 내린다.
4. 순서 바꾸기: 남은 부분은 중요도 순으로. 첫 화면 밖은 보일 때·한가할 때로 미룬다.
5. 쪼개기: 큰 하이드레이션을 `<Suspense>` 경계로 나눠 긴 태스크를 줄인다(16번의 양보 원리).
6. 데이터 줄이기: 하이드레이션 입력 JSON에 화면에 필요한 필드만 넣는다.
7. 기본 동작 보장: 핵심 버튼은 `<form>`·`<a>`로 만들어 JS 없이도 작동하게 한다.

### 2. 코드 — 보일 때 하이드레이션하는 섬(바닐라 + React)

```js
// 섬 마크업: <div data-island="reviews" data-props='{"productId":42}'>…서버 HTML…</div>
const loaders = { reviews: () => import('./islands/reviews.js') };

const io = new IntersectionObserver((entries) => {
  for (const e of entries) {
    if (!e.isIntersecting) continue;
    io.unobserve(e.target);
    const name = e.target.dataset.island;
    loaders[name]().then(({ default: Comp }) => {
      hydrateRoot(e.target, createElement(Comp, JSON.parse(e.target.dataset.props)));
    });
  }
}, { rootMargin: '200px' });                         // 화면에 들어오기 조금 전에 시작

document.querySelectorAll('[data-island]').forEach((el) => io.observe(el));
```

- Astro의 `client:visible`·`client:idle`·`client:load`·`client:media`가 같은 생각을 지시어로 제공한다(22번).
- 섬마다 props만 직렬화한다. 페이지 전체 상태를 넣지 않는다.

### 3. 코드 — 서버 컴포넌트 경계 내리기(React 19, 프레임워크가 RSC를 지원할 때)

```jsx
// ProductPage.jsx — 서버 컴포넌트(지시어 없음): 코드가 클라이언트로 가지 않는다
import { marked } from 'marked';
export default async function ProductPage({ id }) {
  const p = await db.product(id);
  return <article>
    <h1>{p.name}</h1>
    <div dangerouslySetInnerHTML={{ __html: marked(p.descriptionMd) }} />
    <AddToCart productId={id} />            {/* 이것만 클라이언트 컴포넌트 */}
  </article>;
}

// AddToCart.jsx
'use client';
export function AddToCart({ productId }) { const [n, setN] = useState(0); /* … */ }
```

- `'use client'`는 **모듈 의존성 트리**에 경계를 긋는다(react.dev `'use client'`). 레이아웃 파일 최상단에 두면 그 파일이 import하는 모듈 전체가 클라이언트 모듈이 된다. 서버 컴포넌트의 이점이 사라진다(장애 5). 단, 서버 컴포넌트가 `children` 같은 props로 넘긴 JSX는 import가 아니므로 서버에서 렌더된다.

### 4. 진단

- DevTools Performance(CPU 4× 스로틀): FCP 뒤 `hydrateRoot`에서 시작하는 긴 태스크 묶음을 찾는다.
- `new PerformanceObserver(cb).observe({ type: 'longtask' })`(LoAF는 `type: 'long-animation-frame'`)로 하이드레이션 구간의 긴 태스크를 수집한다.
- 문서 응답에서 `__NEXT_DATA__`·`self.__next_f` 같은 직렬화 데이터의 크기를 잰다(프레임워크마다 이름이 다르다).
- 하이드레이션 전 클릭 수집: 인라인 스크립트로 문서에 `click` 캡처 리스너를 달고, 하이드레이션 완료 플래그 전의 클릭을 센다.

## 장애 시나리오와 대처

### 1. SSR로 LCP는 빨라졌는데 하이드레이션 전 클릭이 무시된다 (⚠ 커리큘럼)

- **현상**: "버튼을 눌렀는데 아무 일도 없다", 두세 번 누르면 된다. 저사양 기기·느린 망에서 심하다.
- **보이는 형태**: 오류 로그 없음. RUM에서 첫 상호작용 시각이 하이드레이션 완료 전인 세션 비율이 높다. 실험 ①: 328ms 클릭 → `장바구니 0`.
- **원인**: 리스너는 하이드레이션 때 붙는다. 그 전의 클릭은 받아 줄 코드가 없다. React는 18 개발 중(PR #22448, 2021-10 병합) 이산 이벤트 재생을 그만뒀다. v18.0.0 태그의 `ReactDOMEventListener.js`에 이 동작(캡처 단계 동기 하이드레이션, 실패하면 `stopPropagation`)이 플래그 없이 들어 있다. 19.2.8 소스도 재생하지 않는다. 다만 경계 코드가 이미 있으면 그 클릭은 동기 하이드레이션 뒤 처리된다(실험 ②-b).
- **대처**: 하이드레이션 대상·JS를 줄여 간격을 좁힌다. 핵심 동작은 `<form action>`·링크로 JS 없이 작동하게 한다(점진적 향상). 하이드레이션 전에는 버튼을 시각적으로 비활성 표시하는 방법도 있다(대신 접근성 상태도 함께 관리한다).

### 2. 페이지 전체를 한 번에 하이드레이션 → 긴 태스크, INP 악화 (⚠ 커리큘럼)

- **현상**: 로드 직후 몇 초간 스크롤·입력이 버벅인다.
- **보이는 형태**: Performance 패널의 수백 ms 긴 태스크, TBT 증가, 로드 직후 상호작용의 INP 악화. 실험 ③ full n=5000: 최장 태스크 446~618ms.
- **원인**: 정적 부분까지 컴포넌트로 다시 실행하고 DOM과 대조한다. 하나의 큰 태스크로 몰린다.
- **대처**: 정적 부분을 하이드레이션에서 뺀다(서버 컴포넌트·islands). 남은 부분은 `<Suspense>` 경계로 쪼개 React가 경계 사이에서 양보하게 한다. 첫 화면 밖은 보일 때로 미룬다.

### 3. 직렬화한 초기 상태 JSON이 HTML에 중복 삽입 → 문서 비대 (⚠ 커리큘럼)

- **현상**: 문서가 수백 KB다. 느린 망에서 FCP가 늦다.
- **보이는 형태**: HTML 끝의 큰 `<script>` JSON. 10번 실험: 마크업 109,251B + JSON 87,981B. 실험 ③: full 593,744B vs island 250,446B(n=5000).
- **원인**: 하이드레이션 입력이 필요하다. 쓰지 않는 필드까지 API 응답 전체를 넣거나, 같은 데이터를 여러 컴포넌트용으로 두 번 넣는다.
- **대처**: 필요한 필드만 선택해 직렬화한다. islands는 정적 부분을 데이터 없이 HTML만 보낸다. 서버 컴포넌트는 서버 전용 **코드**를 번들에서 빼지만, 렌더 결과와 클라이언트 컴포넌트에 넘긴 props는 RSC 페이로드로 함께 간다(Next.js App Router 문서 — 첫 로드에서 `self.__next_f`). 그래서 경계 props도 필요한 필드만 넘긴다. 전송 압축은 크기를 줄이지만 파싱 비용은 남는다.

### 4. 지연 로드한 경계의 코드가 늦어 클릭이 사라진다

- **현상**: 리뷰 영역 버튼이 처음 한 번은 반응하지 않는다.
- **보이는 형태**: 실험 ②-a — 청크 대기 중 클릭은 청크 도착 뒤에도 `리뷰 0`.
- **원인**: 경계가 탈수 상태이고 코드가 없어 동기 하이드레이션을 할 수 없다. 이산 이벤트는 재생하지 않는다.
- **대처**: 첫 화면의 상호작용 경계는 지연 로드하지 않거나 `<link rel="modulepreload">`로 미리 받는다. 지연 로드는 화면 밖 경계에만 쓴다.

### 5. `"use client"`를 최상위에 둬서 서버 컴포넌트 이점이 사라짐

- **현상**: 서버 컴포넌트를 도입했는데 번들 크기·하이드레이션 시간이 그대로다.
- **보이는 형태**: 번들 분석에 마크다운 파서·날짜 라이브러리 같은 서버 전용이어야 할 코드가 있다.
- **원인**: 레이아웃 같은 상위 파일에 `'use client'`를 붙여, 그 아래가 모두 클라이언트 모듈 그래프에 들어갔다.
- **대처**: 상호작용하는 잎 컴포넌트에만 `'use client'`를 붙인다. 상위 서버 컴포넌트가 클라이언트 컴포넌트를 `children`으로 감싸는 구조로 바꾼다.

## 핵심 문장

- 하이드레이션은 서버가 만든 HTML에 리스너·트리·상태를 되살리는 일이다. 그 전까지 화면은 보이지만 반응하지 않는다.
- 하이드레이션 비용은 대상 노드 수에 비례한다. 실험에서 5000행 전체는 0.48~0.66초, 섬 하나는 0.07~0.11초였다(CPU 4×).
- React 19.2.8은 클릭 같은 이산 이벤트를 재생하지 않는다. 대신 클릭된 경계를 그 자리에서 동기 하이드레이션해 처리한다. 코드가 아직 없으면(JS 도착 전, 지연 청크 대기 중) 그 클릭은 이 실험에서 사라졌다.
- 줄이는 길은 순서(선택적·점진), 대상(부분·islands·서버 컴포넌트), 재실행 자체(재개) 세 갈래다.
- 하이드레이션 입력 JSON은 HTML과 정보가 겹친다. 하이드레이션 대상을 줄이면 데이터도 같이 준다.

## 관련 주제·근거

- 선행
  - [10-rendering-strategies](../10-rendering-strategies/2-summary.md) — CSR·SSR·SSG·스트리밍, 보이는 시점 vs 반응 시점
  - [09-js-modules-and-bundling](../09-js-modules-and-bundling/2-summary.md) — 코드 분할·청크
  - [16-long-tasks-and-web-workers](../16-long-tasks-and-web-workers/2-summary.md) — 긴 태스크와 양보
- 후속·연결
  - [08-web-performance-vitals](../08-web-performance-vitals/2-summary.md) — INP·TBT
  - [18-ui-rerender-and-memoization](../18-ui-rerender-and-memoization/2-summary.md) — 재렌더 비용
  - [20-performance-budgets-and-regression-gates](../20-performance-budgets-and-regression-gates/2-summary.md) — 하이드레이션 시간을 예산으로
  - [22-islands-and-micro-frontends](../22-islands-and-micro-frontends/2-summary.md) — islands의 설계 관점
  - [languages/web-api/18-event-delegation](../../../languages/web-api/18-event-delegation/2-summary.md) — React 루트의 이벤트 위임
  - [languages/web-api/35-intersection-observer](../../../languages/web-api/35-intersection-observer/2-summary.md) · [languages/web-api/39-idle-scheduling](../../../languages/web-api/39-idle-scheduling/2-summary.md)
  - [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md) · [data-structure/07-heap](../../data-structure/07-heap/2-summary.md)
- 문서·소스
  - web.dev "Rendering on the Web" — 하이드레이션, 점진·부분 재수화, 인터랙티브해 보이지만 반응하지 못하는 문제 <https://web.dev/articles/rendering-on-the-web>
  - patterns.dev "Islands Architecture" — islands와 점진 하이드레이션의 차이(트리를 클라이언트에서 조립하지 않음) <https://www.patterns.dev/vanilla/islands-architecture/>
  - React 18 WG "New Suspense SSR Architecture in React 18"(Dan Abramov, 2021-06-05) <https://github.com/reactwg/react-18/discussions/37>
  - React PR #22448 "Sync hydrate discrete events in capture phase and dont replay discrete events" <https://github.com/react/react/pull/22448>
  - react-dom 19.2.8 `cjs/react-dom-client.development.js` — `dispatchEvent`, `queueIfContinuousEvent`, `discreteReplayableEvents`, `queuedExplicitHydrationTargets`
  - react.dev "Server Components" — 번들 제외, 75K(gzip) 예, 빌드 시·요청 시 실행, `"use client"` 조합 <https://react.dev/reference/rsc/server-components>
  - Qwik 문서 "Resumable" — 하이드레이션이 되살리는 세 가지, 리스너 직렬화 <https://qwik.dev/docs/concepts/resumable/>
  - Astro 문서 "Islands" — `client:idle`·`client:visible`, 지시어 없는 UI 프레임워크 컴포넌트는 JS 제거(`.astro` 안의 `<script>`는 예외 — 22번) <https://docs.astro.build/en/concepts/islands/>
  - Astro "Template directives reference" — `client:load`·`idle`·`visible`·`media`·`only` 정의 <https://docs.astro.build/en/reference/directives-reference/>
  - react.dev `'use client'` — 모듈 의존성 트리의 경계, children으로 넘긴 서버 컴포넌트 <https://react.dev/reference/rsc/use-client>
  - React v18.0.0 `packages/react-dom/src/events/ReactDOMEventListener.js` — 캡처 단계 동기 하이드레이션(`attemptSynchronousHydration`)
- 실험 목록(작업 scratchpad `wp/10/e19/`)
  - ① JS 2초 지연 + 즉시 클릭: headless Chrome 151.0.7922.173, React 19.2.8, 행 200개, 스로틀 없음.
  - ②-a `React.lazy` 청크 1.5초 지연 중 클릭, ②-b 5000행 경계 하이드레이션 중 뒤 경계 클릭(CPU 4×, 3회 — 처음 구성은 B가 화면 밖이라 클릭이 `<html>`에 떨어졌고, 사실 점검에서 B를 화면 안으로 스크롤해 다시 쟀다).
  - ③ 전체 vs 섬 하나: n=500·2000·5000, CPU 4×, 각 5회, `load`+300ms 뒤 시작.
