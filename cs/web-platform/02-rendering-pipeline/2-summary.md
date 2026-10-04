# web-platform/02-rendering-pipeline — 렌더링 파이프라인: 파싱부터 합성까지, 강제 동기 레이아웃과 합성 레이어 — 정리 (힌트)

## 해결하는 문제

HTML·CSS는 글자다. 화면은 픽셀이다. 그 사이를 매번 처음부터 다시 계산하면 느리다.

```text
  "<div class=card>안녕</div>" + ".card{width:50%}"
        │ 무엇을 그리나(DOM·스타일) → 어디에 얼마나 크게(레이아웃) → 어떤 순서로 칠하나(페인트)
        ▼                                                                → 겹쳐서 화면에(합성)
   [ 픽셀 1920×1080 ]
```

- 브라우저는 이 변환을 **단계로 나누고**, 바뀐 것이 닿는 단계부터만 다시 돈다. 단계마다 결과물(트리·목록)을 캐시해 두는 구조다.
- 개발자에게 생기는 문제는 둘이다.
  - 어떤 CSS 속성을 바꾸느냐에 따라 다시 도는 단계가 다르다. `top`을 바꾸면 레이아웃부터, `transform`을 바꾸면 합성만 다시 돌 수 있다.
  - 스크립트가 "지금 크기"를 물으면, 브라우저는 미뤄 둔 계산을 그 자리에서 끝내야 한다. 읽기와 쓰기를 번갈아 하면 이 계산이 반복된다(**layout thrashing**).

쉬운 예: 신문 편집이다.
- 원고(DOM)와 편집 규칙(CSS)으로 지면 배치(레이아웃)를 정하고, 인쇄판(페인트)을 만들고, 사진 필름을 겹쳐 인쇄(합성)한다.
- 기사 한 줄을 고치면 배치부터 다시 한다. 사진 위치만 옮기면 필름만 다시 겹친다.

똑같은 구조다.\
"어느 단계부터 다시 하나"가 성능을 가른다.

실무 예:
- 목록 300행의 폭을 하나씩 읽고 고치는 코드가 1×에서 약 120~190ms, 4× CPU 스로틀에서 0.5~0.9초 메인 스레드를 잡았다(아래 실험, 사실 점검 재실행 포함 범위).
- `left`로 움직이는 애니메이션은 1초에 레이아웃 61~62번, `transform`은 1번이었다(아래 실험).
- `will-change`를 목록 100행에 붙였더니 합성 레이어가 4개에서 104개로 늘었다(아래 실험).

## 동작·원리

### 1. 전체 그림

```text
 바이트 ─▶ HTML 파서 ─▶ DOM 트리 ───┐
                                    ├─▶ 스타일 계산 ─▶ 레이아웃 ─▶ 페인트 ─▶ (커밋) ─▶ 래스터·합성 ─▶ 화면
 바이트 ─▶ CSS 파서 ─▶ CSSOM ───────┘   (계산값)      (박스 위치·  (그리기    │           (레이어를
                                                      크기)        명령 목록)│            타일로 칠해 겹침)
 ◀──────────────── 렌더러 메인 스레드 ─────────────────────────────────────▶│◀─ 컴포지터 스레드 · GPU(Viz) ─▶
```

- web.dev "Rendering performance"의 픽셀 파이프라인은 JavaScript → Style → Layout → Paint → Composite 다섯 칸이다.
- Chromium RenderingNG 문서는 더 잘게 12단계로 적는다: Animate, Style, Layout, Pre-paint(속성 트리 계산), Scroll, Paint(디스플레이 리스트), Commit(컴포지터 스레드로 복사), Layerize, Raster·decode, Activate, Aggregate, Draw.
  - *디스플레이 리스트*: "이 사각형을 이 색으로, 이 글자를 이 위치에" 같은 그리기 명령 목록. 페인트는 픽셀을 바로 칠하지 않고 이 목록을 만든다.
  - *래스터*: 그리기 명령을 실제 픽셀(비트맵 타일)로 바꾸는 일.
  - *합성(composite)*: 따로 칠해 둔 레이어들을 순서·변환(이동·회전·투명도)을 적용해 한 장으로 겹치는 일.

### 2. 파싱 — DOM과 CSSOM

```text
 HTML 바이트 → 디코딩 → 토큰화(상태 기계) → 트리 구성 → DOM
                          <div>, "안녕", </div>   스택에 열린 요소를 쌓고 닫으며 노드를 붙임

 <script>(동기)를 만나면 ─▶ 파서 일시 정지 ─▶ (앞선 CSS가 아직 오는 중이면 기다렸다가) 실행 ─▶ 파싱 재개
 <link rel=stylesheet> ─▶ 파싱은 계속, 대신 렌더링(첫 페인트)이 CSS를 기다림 = 렌더 차단
```

- HTML 표준 13.2(Parsing HTML documents)는 파서를 **토큰화 단계(상태 기계)** 와 **트리 구성 단계**로 정의한다. 문법 오류도 정해진 규칙으로 복구한다. → [language/03 파싱·문법·AST](../../language/README.md)
  - *DOM*: 문서를 노드 트리로 표현한 것이자 그 트리를 다루는 API. → [04](../04-dom-and-event-model/2-summary.md)
  - *CSSOM*: 스타일시트를 규칙 객체로 표현한 것.
- 동기 `<script>`는 파서를 멈춘다(스크립트가 `document.write`로 문서를 바꿀 수 있어서다). CSS는 파서를 멈추지 않지만 첫 렌더링을 막는다. 단 HTML 표준에서 렌더링·스크립트를 막는 것은 조건을 채운 스타일시트다(예: 파서가 넣은 것, `media`가 현재 환경과 맞는 것, 비활성화되지 않은 것). `media="print"` 같은 시트는 화면 렌더링을 막지 않는다(HTML "Interactions of styling and scripting", `link rel=stylesheet` 처리). 이 둘과 preload 스캐너·`async`/`defer`는 [13 `critical-path-and-resource-loading`](../13-critical-path-and-resource-loading/2-summary.md)이 본문이다.

### 3. 스타일 계산 — 어느 규칙이 이 요소에 맞나

```text
 규칙 ".list li.item a { color: red }"
          조상 ◀───────── 가장 오른쪽 compound "a"

 Blink: 규칙 집합(RuleSet)을 가장 오른쪽 compound로 분류
   IdRules{...}  ClassRules{...}  TagRules{"a": [이 규칙, ...]}  UniversalRules[...]
   (오른쪽 끝이 "a"라 TagRules에 든다. 조상의 ".item"은 ②에서 검사)
 요소 <a>의 스타일 계산:
   ① 내 태그·클래스·id 버킷과 UniversalRules 등에서 후보를 꺼냄
   ② 후보마다 오른쪽 → 왼쪽으로 결합자를 따라 부모·조상을 검사
   ③ 조상 검사 전에 Bloom 필터로 "그런 조상이 있을 수 없음"이면 즉시 탈락
```

- Blink 문서 `style-calculation.md`: "가장 오른쪽 compound 선택자를 보고 어느 맵(id·class·tag 등)에 넣을지 고른다." 예: `p.cname`은 `ClassRules`의 `"cname"` 키에 들어간다.
- `selector_checker.cc`의 `MatchSelector`는 요소 e에서 시작해 결합자를 따라 형제·조상으로 간다. 실패 결과도 "e와 e의 모든 형제·조상에 대해 실패" 같은 단위로 돌려준다.
- `selector_filter.h`는 조상의 태그·id·클래스 해시를 비트 집합(사실상 Bloom 필터)에 담아, 조상 조건이 있는 규칙을 싸게 걸러 낸다고 적는다.
- 그래서 **오른쪽 끝이 넓은 선택자**(`.sidebar *`, `div a`)는 후보가 많아 비싸다. 다만 선택자 비용이 체감 문제가 되는 경우는 DOM이 크고 스타일 무효화가 잦을 때다 — 먼저 측정한다.

### 4. 레이아웃과 "더러움" 표시

```text
  스크립트: el.style.width = '120px'   ─▶ 스타일·레이아웃에 "더러움(dirty)" 표시만 하고 반환
  스크립트: el.style.height = '40px'   ─▶ 표시만
  (태스크 끝) ─▶ 렌더링 기회에 스타일 → 레이아웃 1번 ─▶ 페인트

  그런데 중간에 스크립트가 묻는다:
  스크립트: el.offsetWidth             ─▶ "더러우면 지금 당장 스타일·레이아웃을 끝내고 답한다"
                                           = 강제 동기 레이아웃(forced synchronous layout)
```

- 브라우저는 쓰기를 모아 두었다가 다음 렌더링 업데이트에서 한 번에 계산한다. HTML 표준의 "update the rendering" 단계가 "Recalculate styles and update layout"을 부르는 자리다. → [03 이벤트 루프](../03-event-loop/2-summary.md)
- `offsetWidth`·`getBoundingClientRect()`·`getComputedStyle(el).width`·`scrollTop` 같은 **기하 읽기**는 최신 값을 돌려줘야 하므로, 더러운 상태면 그 자리에서 계산한다. → [web-api/09 요소 기하](../../../languages/web-api/09-element-geometry/2-summary.md), [web-api/08 getComputedStyle](../../../languages/web-api/08-getcomputedstyle/2-summary.md)
- 쓰기 → 읽기 → 쓰기 → 읽기를 반복하면 읽을 때마다 레이아웃이 다시 돈다 = **layout thrashing**. → [web-api/10 레이아웃 스래싱](../../../languages/web-api/10-layout-thrashing/2-summary.md)

### 실험: 읽기·쓰기 교차 vs 모아 읽고 모아 쓰기

환경: headless Chrome 151.0.7922.173, Playwright `playwright-core`, Node 20, 127.0.0.1 로컬 페이지, 막대 `div` 300개, CDP `Performance.getMetrics`의 `LayoutCount`·`RecalcStyleCount`·`LayoutDuration`(초) 함수 실행 전후 차이, `Emulation.setCPUThrottlingRate` 1×·4×, 각 5회(새 탭).

```js
function interleaved(){ for (const el of els) { const w = el.offsetWidth; el.style.width = (w + 1) + 'px'; } }  // 읽기→쓰기 교차
function batched(){ const ws = els.map(el => el.offsetWidth);                 // 읽기만 먼저
                    els.forEach((el, i) => { el.style.width = (ws[i] + 1) + 'px'; }); }  // 쓰기만 나중
```

(실험, headless Chrome 151, CPU 1×·4× 스로틀, 2026-10-04 — 5회 범위)

```text
CPU 1x interleaved N=300  LayoutCount+300  RecalcStyleCount+300  LayoutDuration 136.3~161.3ms  함수 실행 145.7~180.5ms  (5회)
CPU 1x batched     N=300  LayoutCount+1  RecalcStyleCount+1  LayoutDuration 1.1~1.6ms  함수 실행 1.3~2.5ms  (5회)
CPU 4x interleaved N=300  LayoutCount+300  RecalcStyleCount+300  LayoutDuration 503.7~682.9ms  함수 실행 532.6~767.3ms  (5회)
CPU 4x batched     N=300  LayoutCount+1  RecalcStyleCount+1  LayoutDuration 5.0~7.5ms  함수 실행 5.4~9.0ms  (5회)
```

- 교차하면 행마다 강제 레이아웃이 한 번씩, 300번 돌았다. 모으면 첫 읽기에서 1번뿐이다(쓰기 결과의 레이아웃은 다음 렌더링 업데이트로 미뤄진다).
- 횟수(300 대 1)는 다섯 번 모두 같았다. 시간은 판마다 흔들렸고, 4× 스로틀에서 약 4~5배로 늘었다. 저사양 기기에서는 교차 코드 하나가 0.5초 넘는 긴 태스크가 될 수 있다는 뜻이다(랩 수치 — 실사용 기기 수치 아님).
- 사실 점검 재실행(같은 코드·같은 조건, 5회×2벌): 횟수는 같았고, 시간 범위는 1× 교차 `LayoutDuration` 116.5~171.2ms·함수 124.2~185.8ms, 4× 교차 `LayoutDuration` 533.9~798.8ms·함수 579.2~914.9ms였다. 다른 작업자의 브라우저가 동시에 돌던 호스트라 시간 값은 흔들릴 수 있다.

### 5. 페인트와 합성 — 세 갈래 경로

```text
  바꾼 속성                     다시 도는 단계
  width, top, left, font-size   Style → Layout → Paint → Composite     (기하가 바뀜)
  color, background-color        Style →          Paint → Composite     (모양만 바뀜)
  transform, opacity             Style →                  Composite     (레이어를 옮기거나 투명도만)
                                 └─ CSS 애니메이션이 합성 가능 조건을 채우면 컴포지터 스레드가 프레임마다 직접 진행
```

- web.dev "Rendering performance"의 세 경로다. 레이아웃·페인트를 건너뛰는 마지막 경로가 가장 싸다.
- web.dev "Stick to compositor-only properties and manage layer count": 애니메이션은 `transform`과 `opacity`만 쓰라고 권한다. 이 둘만 레이아웃·페인트 없이 애니메이션할 수 있다.
  - *합성 레이어*: 따로 래스터되어 GPU 텍스처로 올라가는 화면 조각. 레이어가 따로 있어야 다시 칠하지 않고 옮길 수 있다.
  - *`will-change: transform`*: "이 요소는 곧 transform이 바뀐다"는 힌트. 이 실험의 Chrome 151은 이 요소를 자기 레이어로 승격했다(합성 이유 `WillChangeTransform`). 명세상 힌트일 뿐이라, 선언한 요소가 너무 많으면 브라우저가 승격을 피할 수도 있다(CSS Will Change §2).
- 같은 글: "레이어마다 메모리와 관리가 필요하고 공짜가 아니다." "불필요하게 승격하지 말라." 메모리가 제한된 기기에서는 GPU 텍스처 업로드 대역폭과 GPU 메모리가 병목이 된다.

### 실험: 같은 1초 이동 — `left` / `transform`(rAF) / `transform`(CSS 애니메이션)

환경: 위와 같음, 스로틀 없음. 80px 상자를 1초에 300px 이동. `devtools.timeline` 트레이스에서 `Layout`·`Paint`·`UpdateLayoutTree`(스타일 계산) 이벤트 수, 3회.

```js
function step(t) { const p = Math.min((t - t0) / 1000, 1);
  if (mode === 'left') box.style.left = (300 * p) + 'px';
  else box.style.transform = 'translateX(' + (300 * p) + 'px)';
  if (p < 1) requestAnimationFrame(step); }
// css 모드: @keyframes mv { from {transform:translateX(0)} to {transform:translateX(300px)} } 1s linear
```

(실험, headless Chrome 151, 스로틀 없음, 2026-10-04 — 집필 3회는 같은 값. 사실 점검 재실행 3회 중 1회는 `left`가 61프레임(Layout 61·Paint 122·UpdateLayoutTree 61), `transform`·`css`는 매번 같았다)

```text
run1 left      LayoutCount+62  RecalcStyleCount+62  trace: Layout=62 Paint=124 UpdateLayoutTree=62
run1 transform LayoutCount+1  RecalcStyleCount+62  trace: Layout=1 Paint=2 UpdateLayoutTree=62
run1 css       LayoutCount+2  RecalcStyleCount+6  trace: Layout=2 Paint=5 UpdateLayoutTree=6
```

- `left`: 프레임(61~62)마다 스타일·레이아웃·페인트가 모두 돌았다. 프레임 수는 1초 동안 몇 번의 렌더링 기회가 왔느냐에 따라 ±1 흔들린다.
- `transform`(rAF): 스타일 계산은 프레임마다 돌지만(스크립트가 인라인 스타일을 바꾸므로) 레이아웃 1번·페인트 2번뿐이다.
- CSS 애니메이션: 메인 스레드의 스타일 계산조차 6번이었다. 해석: 프레임별 진행을 컴포지터가 맡고, 메인 스레드는 시작·끝 무렵에만 일했다.

### 실험: `will-change`와 레이어 수

환경: 같음. 200×20px `div` 100개 중 k개에 `will-change: transform`. CDP `LayerTree.layerTreeDidChange`의 레이어 목록과 `LayerTree.compositingReasons`.

(실험, headless Chrome 151, 스로틀 없음, 2026-10-04)

```text
will-change 요소   0개 → 레이어 4개, 레이어 면적 합 4677120px², 합성 이유 {"OverflowScrolling":2,"RootScroller":1,"Viewport":1}
will-change 요소  10개 → 레이어 14개, 레이어 면적 합 4717120px², 합성 이유 {"OverflowScrolling":2,"RootScroller":1,"WillChangeTransform":10,"Viewport":1}
will-change 요소 100개 → 레이어 104개, 레이어 면적 합 5077120px², 합성 이유 {"OverflowScrolling":2,"RootScroller":1,"WillChangeTransform":100,"Viewport":1}
```

- 이 실험(Chrome 151, 100개까지)에서는 요소 하나에 레이어 하나씩 정확히 늘었다. 면적은 요소당 4,000px²(200×20)씩 늘었다.
- 메모리 어림(예시): 픽셀당 4바이트(RGBA)로 래스터한다고 가정하면 100개 × 4,000px² × 4B ≈ 1.6MB다. 실제 타일 크기·DPR(기기 픽셀 비율)·래스터 방식에 따라 달라지며 이 실험은 메모리를 직접 재지 않았다.

## 쓰이는 자료구조·알고리즘

- **트리 여러 벌**: DOM 트리 → (스타일이 붙은) 레이아웃 트리 → 프래그먼트 트리 → 속성 트리(transform·clip·effect·scroll) → 레이어 목록. 단계마다 앞 트리를 순회해 다음 결과를 만든다. → [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md)
- **더러움 비트 + 지연 계산**: 노드마다 "스타일 다시"·"레이아웃 다시" 비트를 두고, 조상에게 "자손이 더럽다"를 올려 표시한다. 다음 계산은 더러운 부분 트리만 내려간다. 기하 읽기는 이 지연을 강제로 끝낸다.
- **해시 버킷 + Bloom 필터**: 규칙을 가장 오른쪽 compound의 id·class·tag로 해시 버킷에 나누고, 조상 조건은 비트 집합 필터로 먼저 거른다. → [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md), [data-structure/11-bloom-filter](../../data-structure/11-bloom-filter/2-summary.md)
- **상태 기계**: HTML 토큰화는 문자 하나마다 상태를 옮기는 상태 기계다(HTML 표준 13.2.5).
- **디스플레이 리스트 + 타일 래스터**: 페인트는 명령 목록(재사용 가능한 캐시), 래스터는 화면을 타일로 나눠 보이는 타일부터 칠한다 [?: 타일 크기·우선순위의 세부는 미확인].

## 적용 — 풀어나가는 법

1. **먼저 잰다.** DevTools Performance 패널에서 녹화하고, 보라색(Rendering: Recalculate Style·Layout)·초록색(Painting) 막대와 "Forced reflow" 경고를 찾는다. 자동화하면 CDP `Performance.getMetrics`의 `LayoutCount`·`RecalcStyleCount`·`LayoutDuration` 차이를 본다(위 실험).
2. **읽기와 쓰기를 나눈다.** 한 프레임 안에서 읽기를 모두 먼저, 쓰기를 모두 나중에 한다.

```js
// 나쁨: 읽고 쓰고 읽고 쓰고 → 행마다 강제 레이아웃
for (const row of rows) row.style.height = row.firstElementChild.offsetHeight + 'px';
// 좋음: 읽기 단계 → 쓰기 단계
const hs = rows.map(r => r.firstElementChild.offsetHeight);
rows.forEach((r, i) => { r.style.height = hs[i] + 'px'; });
```

3. **쓰기를 다음 프레임으로 미룬다.** 여러 컴포넌트가 제각각 읽고 쓴다면, 읽기는 지금·쓰기는 `requestAnimationFrame` 콜백으로 모은다(fastdom류 패턴). → [web-api/38 requestAnimationFrame](../../../languages/web-api/38-request-animation-frame/2-summary.md)
4. **움직임은 `transform`·`opacity`로.** `top/left/width` 애니메이션 대신 `transform: translate()/scale()`. 가능하면 JS 대신 CSS 애니메이션·Web Animations API로 두어 컴포지터가 진행할 수 있게 한다(합성 못 하는 경우는 Lighthouse "Avoid non-composited animations"가 이유를 보여 준다).
5. **레이어는 필요한 곳에만, 필요한 동안만.** 곧 움직일 요소에 `will-change`를 (예: hover 때처럼) 조금 앞서 걸고, 끝나면 뗀다. 시작 바로 직전에 걸면 준비할 시간이 없어 효과가 적다(CSS Will Change §1.2). 목록 전체·`*`에 걸지 않는다. DevTools Layers 패널과 Rendering 탭의 "Layer borders"로 레이어 수를 확인한다. → [css/56 렌더링 파이프라인과 will-change](../../../languages/css/syntax/56-rendering-pipeline-and-will-change/2-summary.md)
6. **스타일 계산 범위를 줄인다.** 큰 DOM에서는 오른쪽 끝이 좁은 선택자(클래스)를 쓰고, `contain`·`content-visibility: auto`로 레이아웃·페인트 범위를 가둔다(→ [17 `list-virtualization`](../17-list-virtualization/2-summary.md)).

## 장애 시나리오와 대처

### 1. 읽기·쓰기 교대 → layout thrashing 강제 동기 레이아웃 (⚠ 커리큘럼)

- **현상**: 목록 정렬·아코디언 펼치기·높이 맞추기에서 화면이 굳는다.
- **보이는 형태**: Performance 패널에 보라색 Layout 막대가 촘촘히 반복되고 "Forced reflow is a likely performance bottleneck" 경고. `LayoutCount`가 요소 수만큼 늘어난다(실험: 300).
- **원인**: 루프 안에서 스타일을 쓴 직후 `offsetHeight`·`getBoundingClientRect()`를 읽는다.
- **대처**: 읽기·쓰기 단계 분리, 쓰기는 rAF로 미루기, 가능하면 측정 자체를 없애는 CSS(`grid`·`flex`의 자동 맞춤)로 바꾸기.

### 2. 렌더 차단 CSS·JS → 첫 화면이 늦게 뜸 (⚠ 커리큘럼)

- **현상**: 흰 화면이 오래간다.
- **보이는 형태**: Lighthouse의 렌더 차단 자원 항목("Eliminate render-blocking resources" — 판에 따라 이름이 다르다), FCP·LCP 지연. 워터폴에서 `<head>`의 CSS·동기 스크립트가 끝난 뒤에야 첫 페인트.
- **원인**: 렌더링은 CSSOM을 기다리고, 동기 `<script>`는 파서를 멈춘다(2절).
- **대처**: 핵심 CSS 인라인·나머지 지연, 스크립트 `defer`/`async`. 세부는 [13 `critical-path-and-resource-loading`](../13-critical-path-and-resource-loading/2-summary.md).

### 3. `top/left` 애니메이션 버벅임

- **현상**: 저사양 기기에서 슬라이드·드로어 애니메이션이 끊긴다.
- **보이는 형태**: 프레임마다 Layout·Paint가 찍힌다(실험: 1초에 Layout 61~62·Paint 122~124). 메인 스레드가 바쁘면 애니메이션도 함께 멈춘다.
- **원인**: 기하 속성 애니메이션은 매 프레임 레이아웃·페인트를 부른다.
- **대처**: `transform`으로 바꾸고, CSS 애니메이션으로 두어 (합성 가능하면) 컴포지터에서 진행되게 한다(실험: Layout 2).

### 4. 레이어 과다 → 메모리 증가·합성 지연

- **현상**: 모바일에서 스크롤이 오히려 느려지거나 탭이 재로드된다.
- **보이는 형태**: Layers 패널에 수백 개 레이어, 합성 이유 `WillChangeTransform`이 요소 수만큼(실험: 100개 → 104 레이어).
- **원인**: 성능을 위해 `will-change`·`translateZ(0)`를 넓게 뿌렸다. 레이어마다 메모리·관리 비용이 든다.
- **대처**: 실제로 움직이는 요소에만, 움직이는 동안만 건다. 프로파일로 합성 시간을 확인한다.

### 5. 넓은 선택자 + 잦은 클래스 토글 → 스타일 계산 비용

- **현상**: `body`에 클래스를 붙였다 떼는 테마 전환이 느리다.
- **보이는 형태**: Recalculate Style 막대가 길고, "Elements affected" 수가 DOM 전체에 가깝다.
- **원인**: 조상 클래스 변경은 많은 자손의 스타일을 무효화한다. 오른쪽 끝이 넓은 선택자는 후보가 많다.
- **대처**: 영향 범위를 좁히는 구조(테마는 CSS 사용자 정의 속성 값만 바꾸기), 측정 후 선택자 단순화. [?: 사용자 정의 속성 변경의 무효화 범위가 클래스 토글보다 좁다는 일반 수치는 미확인 — 측정으로 확인한다]

## 핵심 문장

- 렌더링은 파싱 → DOM/CSSOM → 스타일 → 레이아웃 → 페인트 → 합성 단계이고, 바뀐 것이 닿는 단계부터만 다시 돈다.
- 스타일 쓰기는 "더러움" 표시로 미뤄지고, 기하 읽기는 그 미룬 계산을 그 자리에서 강제로 끝낸다. 교차하면 요소 수만큼 레이아웃이 돈다(실험: 300 대 1).
- `transform`·`opacity`는 레이아웃·페인트 없이 합성만으로 바뀔 수 있다. 합성 가능한 CSS 애니메이션이면 메인 스레드 일도 거의 없었다(실험: Layout 61~62 대 2).
- 레이어는 공짜가 아니다. 이 실험의 Chrome 151에서는 `will-change` 하나에 레이어 하나가 늘었다(100개 → 104 레이어).
- Blink는 규칙을 가장 오른쪽 compound로 버킷에 나누고, 요소에서 조상 쪽으로 검사하며, 조상 조건은 Bloom 필터로 먼저 거른다.

## 관련 주제·근거

- 선행
  - [01-browser-architecture](../01-browser-architecture/2-summary.md) — 렌더러의 메인·컴포지터 스레드, Viz
  - language 03 `parsing-grammars-ast` — [language README](../../language/README.md)(원고: foundations/compiler-pipeline)
- 후속·연결
  - [03-event-loop](../03-event-loop/2-summary.md) — 렌더링 업데이트가 이벤트 루프의 어디서 도나
  - [04-dom-and-event-model](../04-dom-and-event-model/2-summary.md)
  - [08 `web-performance-vitals`](../08-web-performance-vitals/2-summary.md), [13 `critical-path-and-resource-loading`](../13-critical-path-and-resource-loading/2-summary.md), [16 `long-tasks-and-web-workers`](../16-long-tasks-and-web-workers/2-summary.md), [17 `list-virtualization`](../17-list-virtualization/2-summary.md)
  - Web API 문법: [web-api/10 레이아웃 스래싱](../../../languages/web-api/10-layout-thrashing/2-summary.md), [web-api/08 getComputedStyle](../../../languages/web-api/08-getcomputedstyle/2-summary.md), [web-api/09 요소 기하](../../../languages/web-api/09-element-geometry/2-summary.md), [web-api/38 rAF](../../../languages/web-api/38-request-animation-frame/2-summary.md)
  - CSS 문법: [css/56 렌더링 파이프라인과 will-change](../../../languages/css/syntax/56-rendering-pipeline-and-will-change/2-summary.md), [css/22 쌓임 맥락](../../../languages/css/syntax/22-stacking-context-and-z-index/2-summary.md)
  - 자료구조: [data-structure/11-bloom-filter](../../data-structure/11-bloom-filter/2-summary.md), [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md)
- 문서·소스
  - web.dev, "Rendering performance" <https://web.dev/articles/rendering-performance> — 픽셀 파이프라인 5단계, 세 경로, 프레임 예산
  - web.dev, "Stick to compositor-only properties and manage layer count" <https://web.dev/articles/stick-to-compositor-only-properties-and-manage-layer-count> — transform·opacity, will-change, 레이어 비용
  - W3C CSS Will Change Level 1 <https://drafts.csswg.org/css-will-change-1/> — §1.2 미리 걸고 끝나면 떼기, §2 요소가 너무 많으면 승격 회피 가능
  - WHATWG HTML "Interactions of styling and scripting" <https://html.spec.whatwg.org/multipage/semantics.html#interactions-of-styling-and-scripting> — 스크립트를 막는 스타일시트의 조건(`media` 일치·활성 등)
  - Chrome for Developers, "Avoid non-composited animations" <https://developer.chrome.com/docs/lighthouse/performance/non-composited-animations/> — 합성 못 하는 애니메이션과 실패 이유
  - Chrome for Developers, "RenderingNG architecture" <https://developer.chrome.com/docs/chromium/renderingng-architecture> — 12단계, 스레드 분담
  - HTML 표준 13.2 Parsing HTML documents <https://html.spec.whatwg.org/multipage/parsing.html> · 8.1.7.3 Processing model("update the rendering"의 "Recalculate styles and update layout") <https://html.spec.whatwg.org/multipage/webappapis.html#event-loop-processing-model>
  - Blink `third_party/blink/renderer/core/css/style-calculation.md`(RuleSet 버킷), `selector_checker.cc`(`MatchSelector`), `selector_filter.h`(조상 Bloom 필터) <https://chromium.googlesource.com/chromium/src/+/HEAD/third_party/blink/renderer/core/css/>
- 실험 목록(headless Chrome 151.0.7922.173, Playwright `playwright-core`, Node 20, 127.0.0.1 로컬 페이지, 2026-10-04)
  - `e02-layout.js`: 막대 300개 읽기·쓰기 교차 vs 분리 — `LayoutCount`·`RecalcStyleCount`·`LayoutDuration`, CPU 1×·4×, 5회
  - `e02b-anim.js`: 1초 이동 `left`/`transform`(rAF)/CSS 애니메이션 — 트레이스 Layout·Paint·UpdateLayoutTree 수, 3회
  - `e02c-layers.js`: `will-change` 0·10·100개 — 레이어 수·면적·합성 이유
