# web-platform/17-list-virtualization — 목록 가상화: 보이는 행만 DOM에 두기 — 정리 (힌트)

## 해결하는 문제

1만 행 표를 그대로 DOM에 올리면 행마다 요소가 생기고, 브라우저는 그 전부의 스타일·레이아웃을 계산하고 메모리에 들고 있다.
화면에 보이는 행은 수십 개뿐인데 비용은 1만 행 전체에 대해 낸다.

```text
  전체 렌더링                              가상화(windowing)
  ┌──────────── 뷰포트 600px ┐             ┌──────────── 뷰포트 600px ┐
  │ row 0 … row 19 (보임)     │             │ row 0 … row 19 + 아래 여유 │ ← 맨 위에서 DOM에 26행
  └──────────────────────────┘             └──────────────────────────┘
    row 20 … row 9999 (안 보임, DOM에 있음)    (나머지 9974행은 DOM에 없음 — 높이만 빈 공간으로 예약)
```

- *가상화(virtualization, windowing)*: 사용자에게 보이는 것만 렌더링하는 기법. 보이는 범위는 스크롤에 따라 바뀌고, DOM 크기는 목록 길이가 아니라 창 크기에 비례한다(web.dev "Virtualize large lists with react-window").

쉬운 예: 기차 창밖 풍경이다.
- 기차가 지나갈 풍경 전부를 미리 세워 둘 필요가 없다. 창에 보이는 구간만 그때그때 보여 주면 된다.
- 단, 전체 노선 길이(스크롤바 길이)는 알아야 승객이 "어디쯤 왔나"를 안다.

똑같은 구조다.\
실무 예: 관리자 화면의 주문 1만 건 표, 채팅 기록, 로그 뷰어, 스프레드시트형 그리드, 무한 스크롤 피드.

## 동작·원리

### 1. 고정 높이 — 보이는 구간은 나눗셈 한 번

```text
  스크롤 컨테이너 (height 600, overflow auto)
  └─ spacer (height = N × 30 = 300000px)   ← 스크롤바 길이를 만드는 빈 상자
       ├─ row 3323  (position:absolute; top = 3323 × 30)   ← scrollTop 99840, overscan 5 일 때
       ├─ ...
       └─ row 3353

  first = floor(scrollTop / 30) - overscan
  last  = ceil((scrollTop + 600) / 30) + overscan
```

- 스크롤 이벤트마다 `first`~`last`만 다시 그린다. 전체 높이는 spacer가 대신 차지한다.
- *overscan*: 보이는 구간 위아래로 미리 더 그려 두는 행 수. 빠르게 스크롤할 때 빈칸이 번쩍이는 것을 막는다. react-window의 `overscanCount`가 이것이다. web.dev 글은 기본값을 1이라고 적지만, react-window 1.8.11 소스(`src/createListComponent.js`의 `defaultProps`)는 2다 — 스크롤 중에는 진행 방향 쪽에만 이 값을 쓰고 반대쪽은 1, 스크롤이 멈춰 있으면 양쪽 모두 이 값을 쓴다(`_getRangeToRender`). 너무 크면 가상화 효과가 줄어든다(web.dev 같은 글).

### 2. 가변 높이 — 누적 높이 + 이진 탐색

```text
  높이 h[i]:   31   49   67   85  103   31   49 ...
  누적 pre[i]: 0   31   80  147  232  335  366  415 ...    pre[i] = 행 i의 top
                         ▲
  scrollTop = 150  →  pre[k] ≤ 150 인 최대 k = 3   (이진 탐색, O(log N))
  전체 높이 = pre[N]
```

- 행 높이가 다르면 `scrollTop`에서 첫 행을 바로 계산할 수 없다. 누적 높이 배열에서 이진 탐색한다.
- 문제는 **높이를 그려 보기 전에는 모른다**는 점이다. 그래서
  1. 아직 안 그린 행은 추정 높이(예: 30px)로 둔다.
  2. 그린 뒤 실제 높이(`offsetHeight`, `ResizeObserver`)를 측정해 캐시에 넣는다.
  3. 누적 높이를 갱신한다 → 전체 높이(스크롤바 길이)와 아래 행들의 위치가 바뀐다.
- 측정으로 위쪽 행 높이가 바뀌면 지금 보던 내용이 밀린다. 라이브러리는 보던 위치를 기준(anchor)으로 `scrollTop`을 보정한다. 예: TanStack Virtual(`@tanstack/virtual-core` 3.17.11 `src/index.ts`)은 처음 측정한 행의 top이 현재 스크롤 위치보다 위면 높이 차이만큼 스크롤을 보정한다.
  - *scroll anchoring*(`overflow-anchor`): 브라우저가 화면 안 앵커 노드의 위치 변화만큼 스크롤을 자동 보정하는 CSS 기능. 명세상 스크롤 상자 안에서 절대 위치로 놓인 행도 앵커 후보다(제외 조건은 `display:none`·fixed·sticky·containing block이 스크롤 상자 바깥인 absolute·`overflow-anchor:none` — CSS Scroll Anchoring "excluded subtree"). 다만 가상 목록은 스크롤마다 행 DOM을 갈아 끼우므로 라이브러리가 직접 보정하는 편이다. 브라우저 앵커링이 실제 가상 목록에서 얼마나 작동하는지는 확인하지 않았다 [?].

### 3. 무한 스크롤과 결합

```text
  [ 가상화 창: DOM 30행 ]
  data: [0 .......................... 1999] [로딩 중…]
                                 ▲ last ≥ data.length - 20 이면 다음 페이지 요청
```

- 가상화는 **DOM 수**를 묶고, 무한 스크롤은 **데이터 로드**를 나눈다. 둘은 다른 문제다.
- 끝 근처(`last`가 데이터 길이에 가까워짐)에 오면 다음 페이지를 요청한다. react-window에는 `react-window-infinite-loader`가 이 역할을 한다(web.dev 글).
- 다음 페이지 요청은 커서(keyset) 페이지네이션이 맞다. 오프셋은 새 항목이 끼면 중복·누락이 생긴다 — [api-design/06 페이지네이션](../../api-design/06-pagination/2-summary.md).
- 데이터 배열은 계속 커진다. 아주 긴 세션이면 먼 과거 페이지를 버리는 상한도 정한다.

### 실험: 1만 행 — 전체 DOM vs 가상화 vs `content-visibility`

행 하나 = `div.row` + `span` 5개(텍스트 포함). 뷰포트 600px, 행 30px, overscan 5.

```js
// vl.html 핵심 (scratchpad/wp/16/www/vl.html) — 고정 높이 가상화
spacer.style.height = N * ROW + 'px';
const draw = () => {
  const first = Math.max(0, Math.floor(vp.scrollTop / ROW) - OVERSCAN);
  const last = Math.min(N - 1, Math.ceil((vp.scrollTop + vp.clientHeight) / ROW) + OVERSCAN);
  let h = '';
  for (let i = first; i <= last; i++) h += `<div class=row style="position:absolute;top:${i * ROW}px;left:0;right:0">${cells(i)}</div>`;
  spacer.innerHTML = h;
};
vp.addEventListener('scroll', draw, { passive: true }); draw();
// mode=cv: 전체 DOM + .row { content-visibility:auto; contain-intrinsic-size:auto 30px }
```

측정: 로드 완료까지 시간, `Performance.getMetrics`의 `Nodes`, 컨테이너 폭 변경(700→650px) 뒤 강제 레이아웃의 `LayoutDuration` 증가분, 휠 스크롤 2초 동안 rAF 간격, `window.find('Row 9999')`(Ctrl+F와 비슷한 비표준 API — MDN "Window: find()").

(실험, headless Chrome 151.0.7922.173, **CPU 4× 스로틀**, 뷰포트 800×700, 2026-10-04, 모드당 3회. 같은 호스트에서 다른 브라우저 측정이 함께 돈 시간대가 있어 수치는 이 환경의 값이다)

```text
full 0 {"loadMs":6802,"scriptRenderMs":271,"rowsInDom":10000,"Nodes":108589,"heapMB":0.8,"relayoutMs":2470,"layoutCount":1,"frames":98,"p50":16.7,"p95":50,"max":66.7,"findRow9999":true}
full 1 {"loadMs":5673,"scriptRenderMs":254,"rowsInDom":10000,"Nodes":108589,"heapMB":0.8,"relayoutMs":2527,"layoutCount":1,"frames":94,"p50":16.7,"p95":50.1,"max":66.7,"findRow9999":true}
full 2 {"loadMs":6803,"scriptRenderMs":377,"rowsInDom":10000,"Nodes":108589,"heapMB":0.8,"relayoutMs":2106,"layoutCount":1,"frames":102,"p50":16.7,"p95":33.4,"max":50,"findRow9999":true}
virtual 0 {"loadMs":230,"scriptRenderMs":10,"rowsInDom":32,"Nodes":300,"heapMB":0.8,"relayoutMs":9,"layoutCount":1,"frames":97,"p50":16.7,"p95":33.4,"max":50,"findRow9999":false}
virtual 1 {"loadMs":198,"scriptRenderMs":12,"rowsInDom":32,"Nodes":300,"heapMB":0.8,"relayoutMs":13,"layoutCount":1,"frames":93,"p50":16.7,"p95":50,"max":50.1,"findRow9999":false}
virtual 2 {"loadMs":207,"scriptRenderMs":12,"rowsInDom":32,"Nodes":300,"heapMB":0.8,"relayoutMs":13,"layoutCount":1,"frames":96,"p50":16.7,"p95":33.4,"max":50.1,"findRow9999":false}
cv 0 {"loadMs":2370,"scriptRenderMs":294,"rowsInDom":10000,"Nodes":108589,"heapMB":0.8,"relayoutMs":205,"layoutCount":1,"frames":18,"p50":50,"p95":383.4,"max":383.4,"findRow9999":true}
cv 1 {"loadMs":2297,"scriptRenderMs":285,"rowsInDom":10000,"Nodes":108589,"heapMB":0.8,"relayoutMs":172,"layoutCount":1,"frames":18,"p50":66.7,"p95":366.6,"max":366.6,"findRow9999":true}
cv 2 {"loadMs":2359,"scriptRenderMs":281,"rowsInDom":10000,"Nodes":108589,"heapMB":0.8,"relayoutMs":160,"layoutCount":1,"frames":18,"p50":66.6,"p95":350.1,"max":350.1,"findRow9999":true}
```

같은 페이지를 브라우저 하나에 탭 하나만 띄워 렌더러 프로세스 RSS(`ps`)와 `Memory.getDOMCounters`를 본 결과(스로틀 없음, 3회):

```text
full 0 rendererRSS_MB(before→after) 115+70+100 → 186+70+321 domNodes 108602
full 1 rendererRSS_MB(before→after) 117+70+100 → 189+70+321 domNodes 108602
full 2 rendererRSS_MB(before→after) 113+70+100 → 190+70+322 domNodes 108602
virtual 0 rendererRSS_MB(before→after) 112+70+100 → 165+70+117 domNodes 313
virtual 1 rendererRSS_MB(before→after) 110+70+100 → 164+70+117 domNodes 313
virtual 2 rendererRSS_MB(before→after) 115+70+100 → 165+70+117 domNodes 313
```

- **노드 수**: 108,589 → 300(약 360분의 1). DOM에 있는 행 1만 → 32(`Nodes`는 로드 직후 맨 위, 행 수는 스크롤 뒤에 잰 값 — 맨 위에서는 overscan이 아래쪽에만 붙어 26행이다).
- **로드**: 5.7~6.8초 → 0.2초(4× 스로틀). 폭 변경 한 번의 레이아웃: 2.1~2.5초 → 9~13ms. 사실 점검 재실행(같은 조건 3회씩)은 full 로드 6.6~7.8초·레이아웃 2.4~2.7초, virtual 0.19~0.24초·7~9ms였다. 레이아웃 비용이 DOM 크기를 따라 커진다.
- **메모리**: 페이지를 담은 것으로 보이는 렌더러(100MB에서 출발한 프로세스)가 321~322MB vs 117MB. RSS는 공유 메모리를 포함하므로 대략적인 비교다. `JSHeapUsedSize`는 두 모드 모두 0.8MB로 같았다 — 이 지표에는 DOM 메모리가 잡히지 않았다.
- **스크롤 프레임**: full과 virtual 모두 p50 16.7ms였다. 이 단순한 행에서는 스크롤 자체가 병목이 아니었다(합성 스크롤로 해석). 행에 이미지·그림자·복잡한 레이아웃이 있으면 달라질 수 있다 [?].
- **찾기**: 가상화하면 `window.find('Row 9999')`가 `false` — DOM에 없는 행은 찾을 수 없다.
- **`content-visibility:auto`**: DOM은 그대로(노드 108,589, 찾기 `true`)인데 로드 2.3~2.4초·재레이아웃 160~205ms로 full보다 줄었다(재실행 2.3~2.7초·181~193ms). 대신 이 조건에서 **스크롤 중 프레임이 p50 50~67ms, 최대 350~383ms**로 나빠졌다(재실행 p50 67~117ms, 최대 417~617ms — 다른 작업자의 브라우저가 동시에 돌던 시간대라 흔들림이 크다). 해석: 화면에 들어오는 행의 렌더링을 스크롤 중에 메인 스레드에서 하기 때문이다. 4× 스로틀 headless의 값이며 실기기에서는 확인하지 않았다 [?].

### 실험: 가변 높이 — 측정하면 스크롤바가 바뀌고, 안 하면 행이 겹친다

행 높이 31·49·67·85·103px 반복(실제 전체 = 2000 × (31+49+67+85+103) = 670,000px). 추정 30px로 시작해, 그린 행을 `offsetHeight`로 측정해 누적 높이를 고친다(`measure=1`). `measure=0`은 측정하지 않는다.

```js
// var.html 핵심 — 누적 높이 + 이진 탐색
const rebuild = () => { for (let i = 0; i < N; i++) pre[i + 1] = pre[i] + h[i]; };
const firstAt = y => { let lo = 0, hi = N - 1;
  while (lo < hi) { const m = (lo + hi + 1) >> 1; if (pre[m] <= y) lo = m; else hi = m - 1; } return lo; };
// 그린 뒤: real = el.offsetHeight; if (real !== h[i]) { h[i] = real; rebuild(); 위치·spacer 높이 갱신 }
```

(실험, headless Chrome 151.0.7922.173, 스로틀 없음, 휠 1500px × 8번 뒤 `scrollTop=150000`으로 점프, 2026-10-04)

```text
measure=1 {"first":{"scrollTop":0,"scrollHeight":300852,"firstVisible":0},"last":{"scrollTop":12000,"scrollHeight":307401,"firstVisible":179},"distinctScrollHeights":9,"overlaps":0,"estTotal":300000} jump→ {"scrollTop":150000,"scrollHeight":308346,"firstVisible":4752} overlapsAfterJump 0
measure=0 {"first":{"scrollTop":0,"scrollHeight":300000,"firstVisible":0},"last":{"scrollTop":12000,"scrollHeight":300000,"firstVisible":400},"distinctScrollHeights":1,"overlaps":26,"estTotal":300000} jump→ {"scrollTop":150000,"scrollHeight":300000,"firstVisible":5000} overlapsAfterJump 26
```

- 측정할 때: 처음 그리기와 휠 스크롤 8번(그리기 9번) 동안 전체 높이가 9가지 값(300,852 → 301,665 → … → 307,401)으로 바뀌었고, 점프 뒤 308,346이 됐다(사실 점검 재실행에서 같은 값 — 결정적). 실제 전체(670,000)와는 아직 멀다 — 안 그린 행은 추정값이기 때문이다. 스크롤바 길이와 위치가 스크롤할 때마다 바뀐다 = "스크롤바가 튄다". 행 겹침은 0.
- 측정하지 않을 때: 전체 높이는 300,000으로 고정이지만 실제 높이가 더 큰 행들이 30px 간격에 놓여 **화면 안에서 26쌍이 겹쳤다**. 같은 `scrollTop=12000`에서 첫 행이 179(측정) vs 400(추정) — 위치가 어긋난다.
- 처방: 추정값을 실제 평균에 가깝게(예시: 처음 그린 행들의 평균), 측정 즉시 캐시, 보던 행 기준으로 `scrollTop` 보정.

## 쓰이는 자료구조·알고리즘

- **누적합(prefix sum)**: `pre[i]` = 행 i의 top. 전체 높이 = `pre[N]`. 갱신 없는 조회는 O(1) — [algorithm/10 누적합](../../algorithm/10-prefix-sum/2-summary.md)(커리큘럼 13).
- **이진 탐색**: `pre[k] ≤ scrollTop`인 최대 k를 O(log N)에 찾는다. `pre`가 단조 증가라서 가능하다 — [algorithm/06 이진 탐색](../../algorithm/06-binary-search/2-summary.md)(커리큘럼 04).
- **펜윅 트리**: 측정으로 높이 하나가 바뀔 때 누적합 배열을 다시 만들면 O(N)이다. 펜윅 트리는 점 갱신·누적합 조회를 각각 O(log N)에 한다. 이진 탐색도 트리 위에서 O(log N)에 내려갈 수 있다 — [data-structure/17 펜윅 트리](../../data-structure/17-fenwick-tree/2-summary.md)(커리큘럼 34). 위 실험 코드는 단순화를 위해 O(N) 재계산을 썼다.
- **캐시(측정값 맵)**: 인덱스(또는 항목 ID) → 측정 높이. 데이터 정렬이 바뀌면 인덱스 키가 틀어지므로 ID 키가 안전하다.
- **슬라이딩 윈도**: 보이는 구간 `[first, last]`는 스크롤에 따라 미끄러지는 창이다 — [algorithm/09 슬라이딩 윈도](../../algorithm/09-sliding-window/2-summary.md).

## 적용 — 풀어나가는 법

1. **가상화가 필요한지 먼저 판단** — 수백 행이면 페이지네이션이나 `content-visibility:auto`로 충분할 수 있다. 위 실험처럼 1만 행에서 로드·레이아웃이 문제면 가상화를 쓴다.
2. **라이브러리 선택** — react-window(`FixedSizeList`·`VariableSizeList`, web.dev 글 — 1.x 기준. 2.x(2.3.3 확인)는 `List`·`Grid` 컴포넌트와 `rowHeight` prop으로 API가 바뀌었다), TanStack Virtual 등. 직접 만들면 측정·보정·키보드·접근성을 다 떠안는다.
3. **높이 전략**
   - 고정 높이로 만들 수 있으면 고정(가장 단순, O(1)).
   - 가변이면 추정값 + 측정 캐시 + 앵커 보정. 텍스트 줄바꿈·이미지 로드로 높이가 나중에 바뀌면 `ResizeObserver`로 다시 측정한다 — [web-api/36 ResizeObserver](../../../languages/web-api/36-resize-observer/2-summary.md).
4. **스크롤 핸들러는 가볍게** — `passive: true`, 그리기만. 데이터 가공은 미리. 끝 근처 감지는 인덱스 비교 또는 `IntersectionObserver` 센티널 — [web-api/35 IntersectionObserver](../../../languages/web-api/35-intersection-observer/2-summary.md).
5. **잃는 것 보완**
   - 찾기(Ctrl+F): 앱 안에 검색 상자를 두고, 결과 행으로 스크롤한다.
   - 스크린리더: 목록 전체 크기와 현재 위치를 알린다. WAI-ARIA 1.2의 `aria-setsize`·`aria-posinset`(목록), `aria-rowcount`·`aria-rowindex`(grid·table)는 "DOM에 일부만 있을 때" 쓰라고 정의된 속성이다.
   - 키보드 포커스: 포커스된 행이 창 밖으로 나가 DOM에서 사라지면 포커스를 잃는다. 포커스된 행은 렌더 범위에 고정해 둔다.
6. **진단** — DevTools Performance 패널의 Layout·Recalculate Style 시간, `Performance.getMetrics`의 `Nodes`·`LayoutCount`, Memory 패널 힙 스냅숏의 Detached 노드.

## 장애 시나리오와 대처

### 1. 1만 행을 그대로 DOM에 — 로드·레이아웃 폭증, 탭 메모리 증가

- 현상: 표 화면에 들어가면 몇 초간 멈춘다. 창 크기를 바꾸거나 열을 접으면 또 멈춘다.
- 보이는 형태: Performance 패널의 긴 Layout 블록. 위 실험(4× 스로틀): 노드 108,589, 로드 5.7~7.8초, 폭 변경 레이아웃 2.1~2.7초(재실행 포함), 렌더러 RSS 약 321MB(가상화 117MB). 실기기·실데이터의 메모리는 행 구조에 따라 달라진다.
- 원인: 스타일·레이아웃·메모리 비용이 화면이 아니라 DOM 전체에 비례한다.
- 대처: 가상화. 가상화가 어렵다면 `content-visibility:auto` + `contain-intrinsic-size`로 화면 밖 행의 내용 렌더링을 건너뛴다(스크롤 중 비용은 따로 측정).

### 2. 가변 높이 추정 오류 — 스크롤바가 튀고 위치가 어긋남

- 현상: 스크롤바 막대가 끌수록 길이가 변하고, 끝으로 끌었는데 끝이 아니다. 보던 행이 갑자기 밀린다. 측정을 안 하면 행이 겹친다.
- 보이는 형태: 위 실험 — 측정 시 `scrollHeight`가 그리기 9번(처음 + 휠 8번)에 9가지 값, 측정 안 하면 화면 안 26쌍 겹침.
- 원인: 안 그린 행의 높이는 추정값이다. 측정할 때마다 누적 높이와 아래 행 위치가 바뀐다.
- 대처: 추정값을 실제 평균에 가깝게, 측정 캐시(ID 키), 보던 행 기준 `scrollTop` 보정, 이미지는 크기를 지정해 측정 뒤 높이가 다시 바뀌지 않게(14 이미지 최적화).

### 3. 찾기·스크린리더에서 사라진 행

- 현상: "Ctrl+F로 찾아지지 않는다", 스크린리더가 "목록, 32개 항목"이라고 읽는다.
- 보이는 형태: 위 실험의 `window.find('Row 9999')` = `false`. 접근성 트리에 행 32개뿐.
- 원인: 가상화는 DOM에서 행을 빼므로 브라우저 찾기와 접근성 트리에도 없다.
- 대처: 앱 내 검색, `aria-setsize`·`aria-posinset`(또는 `aria-rowcount`·`aria-rowindex`), 포커스 행 고정. 찾기가 핵심 요구면 `content-visibility`가 대안이다(DOM·접근성 트리에 남는다 — web.dev "content-visibility").

### 4. 무한 스크롤 + 가상화에서 중복·누락

- 현상: 피드를 내리다 같은 글이 두 번 보이거나 빠진다.
- 원인: 오프셋 페이지네이션 중 새 항목이 앞에 끼어 페이지 경계가 밀린다. 가상화와 무관한 데이터 로드 문제다.
- 대처: 커서(keyset) 페이지네이션, 항목 ID로 dedup, 가상화 키도 ID로(api-design/06).

## 핵심 문장

- 가상화는 DOM 크기를 목록 길이가 아니라 창 크기에 비례하게 만든다.
- 고정 높이는 나눗셈 한 번으로, 가변 높이는 누적 높이에 대한 이진 탐색으로 보이는 구간을 찾는다.
- 가변 높이는 그려 보기 전에 모르므로, 추정·측정·보정 과정에서 스크롤바 길이가 바뀐다.
- 가상화한 행은 DOM에 없으므로 브라우저 찾기·접근성 트리·포커스에서도 빠진다 — 보완을 따로 설계해야 한다.
- 가상화는 DOM 수를, 무한 스크롤은 데이터 로드를 다루는 별개의 해법이다.

## 관련 주제·근거

- 선행: [02 렌더링 파이프라인](../02-rendering-pipeline/2-summary.md), [04 DOM과 이벤트 모델](../04-dom-and-event-model/2-summary.md), [16 긴 태스크와 웹 워커](../16-long-tasks-and-web-workers/2-summary.md)
- 후속: [18 재렌더와 메모이제이션](../18-ui-rerender-and-memoization/2-summary.md), [11 접근성 기초](../11-accessibility-basics/2-summary.md), [14 이미지 최적화](../14-image-optimization/2-summary.md), [23 증상 색인](../23-web-symptom-index/2-summary.md)
- 문법·API: [web-api/35 IntersectionObserver](../../../languages/web-api/35-intersection-observer/2-summary.md), [web-api/36 ResizeObserver](../../../languages/web-api/36-resize-observer/2-summary.md), [web-api/10 layout thrashing](../../../languages/web-api/10-layout-thrashing/2-summary.md), [web-api/19 passive 리스너](../../../languages/web-api/19-passive-and-scroll/2-summary.md)
- 다른 영역: [algorithm/10 누적합](../../algorithm/10-prefix-sum/2-summary.md), [algorithm/06 이진 탐색](../../algorithm/06-binary-search/2-summary.md), [algorithm/09 슬라이딩 윈도](../../algorithm/09-sliding-window/2-summary.md), [data-structure/17 펜윅 트리](../../data-structure/17-fenwick-tree/2-summary.md), [api-design/06 페이지네이션](../../api-design/06-pagination/2-summary.md)
- 근거
  - web.dev "Virtualize large lists with react-window" https://web.dev/articles/virtualize-long-lists-react-window — 정의, overscanCount, Fixed/VariableSizeList, infinite loader
  - web.dev "content-visibility: the new CSS property that boosts your rendering performance" https://web.dev/articles/content-visibility — 화면 밖 렌더링 생략, DOM·접근성 트리 유지, `contain-intrinsic-size`
  - WAI-ARIA 1.2 https://www.w3.org/TR/wai-aria-1.2/ — `aria-setsize`·`aria-posinset`·`aria-rowcount`·`aria-rowindex`
  - CSS Scroll Anchoring https://drafts.csswg.org/css-scroll-anchoring/
- 실험 목록 (headless Chrome 151.0.7922.173, Node 20.19.6 + playwright-core 1.62.1, 127.0.0.1 로컬 서버, 2026-10-04)
  - 17-A full·virtual·cv 비교(CPU 4×): `scratchpad/wp/16/exp17-vl.js`(인자 `full,virtual` / `cv`), `www/vl.html` — 3회씩
  - 17-B 렌더러 RSS·DOM 카운터: `scratchpad/wp/16/exp17-mem.js` — 3회씩
  - 17-C 가변 높이 측정 유무: `scratchpad/wp/16/exp17-var.js`, `www/var.html`
  - 사실 점검 재실행(같은 코드·같은 환경, 2026-10-04): 17-A·17-B 3회씩, 17-C 1회 + `scrollHeight` 순서 확인 — `scratchpad/wp/fc-16/out17-*.txt`. 노드 수·찾기·가변 높이 출력은 일치, 시간은 범위가 넓어졌다
  - 근거 추가: react-window 1.8.11 `src/createListComponent.js`(unpkg), react-window 2.3.3 `dist/react-window.d.ts`, `@tanstack/virtual-core` 3.17.11 `src/index.ts`, MDN "Window: find()" https://developer.mozilla.org/en-US/docs/Web/API/Window/find
