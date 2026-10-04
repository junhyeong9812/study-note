# web-platform/08-web-performance-vitals — Core Web Vitals(LCP·INP·CLS)와 측정: 랩 vs 필드 — 정리 (힌트)

## 해결하는 문제

"페이지가 빠르다"는 말은 숫자 하나로 정하기 어렵다.

```text
  옛 지표 하나로 볼 때
  navigation ──────────────── onload(3.1s) ──>
                 └ 사용자는 0.8s에 본문을 이미 읽고 있다
                 └ 1.5s에 누른 버튼은 0.6s 뒤에 반응했다
                 └ 2.0s에 광고가 끼어들어 누르려던 링크가 밀렸다
  → onload 하나로는 "보였나·반응했나·흔들렸나"를 구분하지 못한다
```

- 해법: 사용자가 느끼는 세 가지를 따로 잰다.
  - *Core Web Vitals*: web.dev가 정한 핵심 사용자 경험 지표 3개. LCP(로딩), INP(반응성), CLS(시각적 안정성).
  - *LCP(Largest Contentful Paint)*: 뷰포트 안에서 가장 큰 이미지·텍스트 블록·비디오가 그려진 시각.
  - *INP(Interaction to Next Paint)*: 클릭·탭·키 입력부터 그 결과가 화면에 그려지기까지의 지연 중 가장 나쁜 쪽.
  - *CLS(Cumulative Layout Shift)*: 예상하지 못한 레이아웃 이동 점수의 가장 큰 묶음.

쉬운 예: 식당.
- 메뉴판이 테이블에 놓이는 시각 = LCP.
- "주문할게요"에 직원이 "네" 하고 답하는 시간 = INP.
- 접시가 식탁 위에서 미끄러지는 정도 = CLS.

똑같은 구조다.\
"언제 보였나 · 누르면 바로 반응하나 · 화면이 흔들리나"를 각각 숫자로 만든다.

실무 예:
- 쇼핑몰 상품 페이지: 히어로 이미지가 늦다(LCP), "장바구니" 버튼이 굼뜨다(INP), 광고 배너가 늦게 끼어 결제 버튼이 밀린다(CLS).
- 개발자 노트북의 Lighthouse는 초록인데, Search Console의 필드 데이터는 "개선 필요"다 — 랩과 필드의 차이다.

## 동작·원리

### 1. 세 지표가 보는 시간축

```text
  [LCP]  navigation ─ FCP ──── 후보1(텍스트) ─── 후보2(히어로 이미지) ──┤ 첫 입력이 오면 후보 갱신 중단
                                                         ↑ LCP = 마지막 후보의 렌더 시각

  [INP]  입력 ──┬─ input delay ─┬─ processing ─┬─ presentation delay ─┤ 다음 프레임 표시
               (메인 스레드 대기)  (핸들러 실행)     (스타일·레이아웃·페인트)
         한 상호작용의 지연 = 위 전체.  INP = 방문 동안 상호작용 지연의 (거의) 최댓값

  [CLS]  이동 ▮ ▮▮      ▮          ▮▮▮
         └─ 창 1 ─┘   └창 2┘     └─ 창 3 ─┘   (간격 1초 미만, 길이 최대 5초로 묶음)
         CLS = 점수 합이 가장 큰 창의 합
```

### 2. LCP — 가장 큰 콘텐츠가 그려진 시각

- 후보가 되는 요소(web.dev LCP 문서)
  - `<img>`, SVG 안 `<image>`, `<video>`(포스터나 첫 프레임 중 이른 쪽), `url()` 배경 이미지, 텍스트를 담은 블록 요소.
- 크기는 **뷰포트 안에 보이는 넓이**다. 이미지는 보이는 크기와 원래(intrinsic) 크기 중 작은 쪽을 쓴다. 여백·패딩·테두리는 빼고 잰다.
- 제외 휴리스틱(web.dev가 밝힌 **Chromium 기반 브라우저**의 휴리스틱 — 공통 표준 규칙은 아니다): `opacity: 0`, 뷰포트 전체를 덮는 배경으로 보이는 요소, 엔트로피가 낮은 자리표시 이미지.
- 더 큰 요소가 그려지면 새 후보 항목이 나온다. **사용자가 탭·스크롤·키를 누르면 새 항목을 내지 않는다.**
- 백그라운드 탭에서 열린 페이지는 항목이 늦게 나올 수 있다. bfcache 복원 때는 API가 항목을 내지 않는다(라이브러리가 따로 계산한다).
  - *bfcache(back/forward cache)*: 뒤로·앞으로 가기 때 페이지를 메모리에 통째로 두었다가 바로 되살리는 캐시.

LCP 네 조각(web.dev "Optimize LCP")

| 조각 | 뜻 | 권장 비중 |
|---|---|---|
| TTFB | 탐색 시작 → HTML 첫 바이트 | 약 40% |
| 자원 로드 지연(resource load delay) | TTFB → LCP 자원 요청 시작 | 10% 미만 |
| 자원 로드 시간(resource load duration) | LCP 자원을 받는 시간 | 약 40% |
| 요소 렌더 지연(element render delay) | 자원 도착 → 화면에 그려짐 | 10% 미만 |

- "지연" 두 조각이 크면 발견이 늦거나(13번) 렌더가 막힌 것(13번 렌더 차단 자원)이다. "로드 시간"이 크면 자원이 큰 것(14번 이미지·15번 폰트)이다.

### 3. INP — 입력에서 다음 페인트까지

- 대상 입력: 마우스 클릭, 터치 탭, 키 누름. 호버·스크롤·확대는 대상이 아니다(web.dev INP).
- 측정 원천은 W3C Event Timing API다.
  - 한 번의 탭은 `pointerdown`·`pointerup`·`click` 세 이벤트를 만든다. 셋은 같은 `interactionId`를 받는다.
  - 각 항목의 `duration` = 입력 시각(`timeStamp`)부터 처리 후 **다음 렌더링 갱신**까지, 8ms 단위로 반올림.
  - 기본 `durationThreshold`는 104ms, 최소 16ms까지 낮출 수 있다.
  - 한 상호작용의 지연 = 그 `interactionId`를 가진 항목들 중 가장 긴 `duration`.
- 페이지 전체 INP: 가장 나쁜 상호작용을 보고하되, **상호작용 50번마다 가장 높은 것 1개를 무시**한다(이상치 완화, web.dev INP의 정의).
- 상호작용이 한 번도 없으면 INP 값이 없다.
- INP는 2023년 pending 단계에 올랐고, 2024년 FID를 대신해 Core Web Vital이 됐다(web.dev Web Vitals).

### 4. CLS — 예상 못 한 이동의 가장 큰 묶음

```text
  이동 점수 = 영향 비율(impact fraction) × 거리 비율(distance fraction)

  뷰포트 800×600
  ┌──────────────────┐        ┌──────────────────┐
  │ h1 / 버튼          │        │ h1 / 버튼          │
  │ ┌──── p (이전) ──┐│        │ [이미지 300px]     │
  │ │ y=130, h=200   ││   →    │                  │
  │ └────────────────┘│        │ ┌──── p (이후) ──┐│
  │                  │        │ │ y=430, 보이는 h=170│
  └──────────────────┘        └─┴────────────────┴┘
  영향 영역 = 이전 사각형 ∪ 이후 사각형(뷰포트로 자른 것)
  거리 비율 = 가장 크게 움직인 거리 / 뷰포트의 긴 변
```

- *영향 비율*: 불안정 요소가 이전·이후 프레임에서 차지한 보이는 영역(합집합)이 뷰포트에서 차지하는 비율.
- *거리 비율*: 불안정 요소가 움직인 가장 큰 가로·세로 거리 ÷ 뷰포트의 긴 변.
- 클릭·탭·키 입력 같은 **이산 입력** 후 500ms 안에 생긴 이동은 `hadRecentInput = true`로 표시되어 빠진다(사용자가 눌러서 펼친 메뉴는 "예상한 이동"). 스크롤·드래그·핀치 같은 연속 동작은 이 "최근 입력"에 들지 않는다(web.dev CLS, Layout Instability Input Exclusion).
- 세션 창: 이동 사이 간격 1초 미만, 창 길이 최대 5초. CLS는 **합이 가장 큰 창의 값**이다(web.dev CLS).

### 5. 임계값과 p75

| 지표 | 좋음 | 개선 필요 | 나쁨 |
|---|---|---|---|
| LCP | ≤ 2.5s | 2.5s 초과 ~ 4.0s | > 4.0s |
| INP | ≤ 200ms | 200 초과 ~ 500ms | > 500ms |
| CLS | ≤ 0.1 | 0.1 초과 ~ 0.25 | > 0.25 |

- 판정 기준: **페이지 로드의 75번째 백분위(p75)**, 모바일과 데스크톱을 나눠서(web.dev Web Vitals).
  - *p75*: 값을 정렬했을 때 75% 지점의 값. "사용자 4명 중 3명은 이보다 좋다."
- 같은 경계는 `web-vitals` 6.2.2 소스 상수로도 확인했다: LCP `[2500, 4000]`, INP `[200, 500]`, CLS `[0.1, 0.25]`, FCP `[1800, 3000]`, TTFB `[800, 1800]`.

### 6. 랩 vs 필드

```text
  랩(lab)                                필드(field, RUM)
  ┌──────────────────────────┐          ┌─────────────────────────────────────┐
  │ 기기 1대 · 네트워크 1종 · 장소 1곳 │          │ 실제 사용자들의 기기·망·위치·캐시 상태      │
  │ 같은 조건 반복 → 원인 찾기 좋음   │          │ 분포(p75) → "실제로 어떤가"            │
  │ Lighthouse, DevTools        │          │ CrUX, PageSpeed Insights 필드 칸,     │
  │ 로드만 재면 INP 없음 → TBT로 대신 │          │ Search Console, web-vitals 직접 수집   │
  └──────────────────────────┘          └─────────────────────────────────────┘
```

- *RUM(Real User Monitoring)*: 실제 사용자의 브라우저에서 지표를 재서 서버로 보내는 방식.
- *CrUX(Chrome UX Report)*: 조건을 갖춘 Chrome 사용자(사용 통계 보고 켬, 방문 기록 동기화, 동기화 암호문 없음)의 데스크톱·Android 데이터. iOS Chrome·WebView는 빠진다(CrUX methodology). 공개 색인 가능하고 방문이 충분한 출처·페이지만 나온다.
- 차이가 나는 이유(web.dev "Why lab and field data can be different")
  - 기기·망: 랩은 한 조건, 필드는 분포.
  - 캐시: 실제 재방문자는 자원이 캐시에 있어 필드 LCP가 더 빠를 수 있다.
  - LCP 요소: 화면 크기·`#fragment` 링크에 따라 필드의 LCP 요소가 다를 수 있다.
  - CLS: 로드만 재는 랩(Lighthouse 탐색 등)은 로드 중·첫 화면만, 필드는 페이지 수명 전체(스크롤 중 이동 포함). DevTools 실시간 측정이나 상호작용을 넣은 랩 기록은 로드 뒤 이동도 잡는다.
  - INP: 랩은 사용자가 언제 누를지 모른다. 사용자 입력 없이 로드만 재는 Lighthouse 탐색 감사는 INP를 못 재서 TBT로 대신한다(web.dev Web Vitals). 아래 실험처럼 스크립트·DevTools로 직접 누르면 랩에서도 그 상호작용의 INP는 잴 수 있다.
    - *TBT(Total Blocking Time)*: FCP 이후 긴 태스크마다 (길이 − 50ms)를 더한 값. Lighthouse 탐색 측정은 FCP부터 TTI까지를 합산한다(Timespan 모드는 그 뒤도 잴 수 있다). 평균 모바일 기기에서 200ms 미만을 권한다(web.dev TBT).
  - 기간: 필드(CrUX)는 28일 기간의 경험이다.
- Lighthouse 기본 모바일 설정(Lighthouse docs/throttling.md): 시뮬레이션 스로틀링, RTT 150ms, 1.6Mbps 다운 / 750Kbps 업, CPU 4배 감속 — "4G 하위 25%·3G 상위 25%" 수준.

### 실험: 크기 미지정 이미지의 CLS, LCP 후보 교체, 핸들러 길이별 INP

조건: 로컬 서버(127.0.0.1)가 800×300 PNG를 700ms 늦게 준다. 같은 페이지 세 벌 — `/nodim`(이미지 `width`/`height` 없음, 클릭 작업 20ms), `/dim`(속성 있음, 20ms), `/slow`(속성 있음, 300ms). `PerformanceObserver`와 `web-vitals` 6.2.2(`reportAllChanges: true`)를 함께 붙이고, Playwright `page.click()`으로 버튼을 3번 누른다.

```js
// exp08_vitals.js 핵심 (scratchpad/wp/08/)
new PerformanceObserver(l => l.getEntries().forEach(e => out.shifts.push({
  t: Math.round(e.startTime), value: +e.value.toFixed(4),
  sources: e.sources.map(s => [s.node && s.node.nodeName, s.previousRect.y, s.previousRect.height, s.currentRect.y, s.currentRect.height])
}))).observe({ type: 'layout-shift', buffered: true });
new PerformanceObserver(l => l.getEntries().forEach(e => { if (e.interactionId) out.events.push({
  name: e.name, duration: e.duration,
  inputDelay: Math.round(e.processingStart - e.startTime),
  processing: Math.round(e.processingEnd - e.processingStart) }); })).observe({ type: 'event', durationThreshold: 16, buffered: true });
for (const f of ['onLCP', 'onCLS', 'onINP', 'onFCP']) {
  const on = webVitals[f];
  on(m => { out.wv[m.name] = { value: m.value, rating: m.rating }; }, { reportAllChanges: true });
}
```

(실험, headless Chrome 151.0.7922.173, 스로틀 없음, 뷰포트 800×600, 2026-10-04 — 버튼 위치를 고친 뒤 4회 실행 중 마지막 출력. 4회 범위: `/nodim` CLS 0.2313 고정, 이미지 LCP 788~800ms, `/slow` 클릭 304~312ms. 같은 날 다른 컨텍스트에서 4회 더 돌린 재실행: CLS 0.2313·INP 32/312 동일, `/nodim` 이미지 LCP 772~792ms)

```text
== /nodim
 LCP entries: [{"t":176,"el":"P","size":6766},{"t":800,"el":"IMG","size":240000}]
 layout-shift: [{"t":759,"value":0.2313,"hadRecentInput":false,"sources":[["P",129.875,200,429.875,170.125]]}]
 click event durations: 32(지연2+처리21), 24(지연1+처리20), 24(지연1+처리20)
 web-vitals: {"FCP":{"value":176,"rating":"good"},"LCP":{"value":800,"rating":"good"},"CLS":{"value":0.2313,"rating":"needs-improvement"},"INP":{"value":32,"rating":"good"}}
== /dim
 LCP entries: [{"t":88,"el":"P","size":6766},{"t":764,"el":"IMG","size":240000}]
 layout-shift: []
 click event durations: 24(지연2+처리21), 24(지연1+처리20), 24(지연1+처리20)
 web-vitals: {"FCP":{"value":88,"rating":"good"},"LCP":{"value":764,"rating":"good"},"CLS":{"value":0,"rating":"good"},"INP":{"value":32,"rating":"good"}}
== /slow
 LCP entries: [{"t":104,"el":"P","size":6766},{"t":768,"el":"IMG","size":240000}]
 layout-shift: []
 click event durations: 312(지연2+처리301), 304(지연1+처리300), 304(지연1+처리300)
 web-vitals: {"FCP":{"value":104,"rating":"good"},"LCP":{"value":768,"rating":"good"},"CLS":{"value":0,"rating":"good"},"INP":{"value":312,"rating":"needs-improvement"}}
```

관찰과 해석
- **LCP 후보 교체**: 먼저 문단 `P`(넓이 6,766)가 후보였다가, 이미지(800×300 = 240,000)가 그려지자 `IMG`로 바뀌었다. 최종 LCP는 마지막 후보다.
- **CLS 0.2313 손 계산**: `sources`의 `P`가 y=129.875(높이 200) → y=429.875(보이는 높이 170.125)로 300px 내려갔다.
  - 이전 사각형(129.875~329.875)과 이후 사각형(429.875~600)은 겹치지 않는다. 합집합 높이 = 200 + 170.125 = 370.125.
  - 영향 비율 = 800×370.125 / (800×600) = 0.6169. 거리 비율 = 300 / 800 = 0.375.
  - 0.6169 × 0.375 = **0.2313** — 측정값과 같다. 영향 영역은 바운딩 박스가 아니라 **합집합**이다.
- `width`/`height`만 넣은 `/dim`은 이동이 0건이다. 브라우저가 속성으로 비율을 알아 자리를 미리 잡았다(14번).
- **INP**: 핸들러 300ms → INP 312ms("개선 필요"). input delay는 1~2ms로 작고 processing이 거의 전부다. 다른 일이 메인 스레드를 막고 있었다면 input delay가 커진다(16번).
- `/dim`의 INP가 32인데 `click` 항목이 24인 것: `web-vitals`의 `onINP`는 기본 `durationThreshold`가 40이라 24·32ms짜리 `event` 항목을 아예 받지 않는다. 대신 함께 관찰하는 `first-input` 항목(첫 상호작용의 `pointerdown`)으로 값을 낸다(`onINP.js`의 `types = ['event', 'first-input']`). 재실행에서 `first-input` 항목 duration이 32였고 INP도 32였다.
  - 재실행 원시 출력에서는 한 상호작용의 `pointerdown`·`pointerup`·`click` duration이 매번 같았다(32·32·32 또는 24·24·24). 상호작용 지연은 같은 `interactionId` 항목 중 최댓값이다.
- 측정 함정(이 환경에서 관찰): 버튼이 뷰포트 아래쪽(y≈520, 뷰포트 높이 600)에 있을 때 headless Chrome에서 Event Timing 항목이 나오지 않는 실행이 있었다. 버튼을 위로 옮기자 안정됐다. 원인은 확인하지 못했다 `[?]`.

### 실험: 같은 페이지, 다른 조건 — 섞인 분포의 p50과 p75

조건: 1200×600 JPEG(약 349KB) 히어로 + 150ms 초기화 스크립트. CDP `Emulation.setCPUThrottlingRate`·`Network.emulateNetworkConditions`로 세 조건을 만들고 조건당 5회. 그다음 "데스크톱 60% · 모바일 30% · 저사양 10%"의 가상 사용자 20명 표본을 만들어 백분위를 구했다(예시 — 실제 사용자 분포가 아니다).

| 조건 | CPU | RTT | 다운로드 |
|---|---|---|---|
| desktop | 1× | 0 | 제한 없음 |
| mobile | 4× | 150ms | 1.6Mbps |
| slow | 6× | 400ms | 0.4Mbps |

(실험, headless Chrome 151.0.7922.173, 뷰포트 412×823, 2026-10-04 — 2회 실행 + 사실 점검 재실행 1회. 스로틀은 CDP 요청 단위 스로틀이라 Lighthouse 기본(시뮬레이션)과 방식이 다르다)

```text
desktop  LCP ms 300 248 256 256 252  범위 248~300
mobile   LCP ms 2148 2152 2136 2136 2136  범위 2136~2152
slow     LCP ms 7920 7916 7904 7952 7940  범위 7904~7952
혼합 표본 n= 20  p50 300  p75 2136  p95 7916
(2회차) desktop 252~292 · mobile 2144~2164 · slow 7944~8072 · p50 292 · p75 2148 · p95 7944
(사실 점검 재실행) desktop 244~296 · mobile 2144~2168 · slow 7940~8096 · p50 296 · p75 2160 · p95 7940
```

- 같은 페이지가 조건에 따라 0.25초에서 7.9초까지 벌어진다. 개발자 PC(desktop)만 보면 "0.3초짜리 페이지"다.
- 섞인 분포에서 p50은 0.3초, p75는 2.1초, p95는 7.9초다. **중앙값은 데스크톱 사용자만 대변하고, p75부터 모바일이 보인다.** p75를 쓰는 이유다.
- 이 표본의 p75(2.1초)는 "좋음"이지만 모바일 값이다. 20명 중 p75는 15번째 값(nearest-rank)이라, 저사양이 25%를 넘으면(20명 중 6명 이상) p75가 저사양 구간(7.9초)으로 넘어간다. 섞인 분포는 구성비에 따라 판정이 뒤집히므로 모바일·데스크톱을 나눠 보라는 권고가 있다.

## 쓰이는 자료구조·알고리즘

- **백분위(p75)**: 정렬 후 순위로 고르는 방법(nearest-rank). 실험 코드의 `pct()`가 이 방식이다. 대량 RUM에서는 히스토그램 버킷으로 근사한다 — CrUX는 좋음·개선 필요·나쁨 구간 비율과 p75를 낸다.
  - 주의: 페이지별 p75를 평균 내면 전체 p75가 아니다. 백분위는 원자료(또는 히스토그램)를 합친 뒤 다시 구한다. 기술통계·백분위 노트는 [data-analysis](../../data-analysis/README.md)(04·05 미작성).
- **세션 창 묶기(CLS)**: 시간순 이동을 "직전과 1초 미만 & 창 시작과 5초 미만"이면 같은 창에 더하고, 아니면 새 창을 연다. 한 번 훑기 O(n). `web-vitals`의 `LayoutShiftManager`가 이 두 조건(`< 1000`, `< 5000`)을 그대로 쓴다.
- **상위 k개 유지(INP)**: `web-vitals`의 `InteractionManager`는 가장 긴 상호작용 최대 10개만 정렬해 둔다. INP 후보 인덱스 = `min(목록 길이 − 1, floor(상호작용 수 / 50))` — "50번마다 1개 무시"를 제한된 후보로 **근사**한 구현이다. 목록이 10개뿐이라 상호작용 500번 이상이면 인덱스가 9에 묶여 10번째로 느린 값을 고른다(정의대로면 11번째). 작은 고정 크기 상위 k 목록은 [힙](../../data-structure/07-heap/2-summary.md) 대신 정렬 배열로도 충분하다.
- **누적 최댓값(LCP)**: 새 후보가 더 크면 갱신하고, 입력이 오면 멈추는 단순 상태 기계.

## 적용 — 풀어나가는 법

### 1. 필드부터 본다

```text
  ① CrUX / PageSpeed Insights 필드 칸 / Search Console → 어느 지표가, 모바일·데스크톱 중 어디서 나쁜가 (p75)
  ② 자체 RUM(web-vitals attribution) → 어느 페이지 유형·어느 요소·어느 상호작용인가
  ③ 랩 재현(DevTools Performance, 스로틀링) → 왜 그런가 (원인 추적)
  ④ 고친 뒤 → 랩으로 회귀 확인(20번), 필드 p75로 효과 확인(28일 기간이라 늦게 반영)
```

### 2. RUM 수집 코드

```ts
import { onLCP, onINP, onCLS } from 'web-vitals/attribution';

function send(metric: { name: string; value: number; rating: string; id: string;
                        navigationURL?: string; attribution?: any }) {
  const a = metric.attribution ?? {};
  const body = JSON.stringify({ name: metric.name, value: metric.value, rating: metric.rating, id: metric.id,
    url: metric.navigationURL ?? location.href,   // 지표가 속한 탐색의 URL(SPA에서 현재 경로와 다를 수 있다)
    target: a.target ?? a.interactionTarget ?? a.largestShiftTarget,   // LCP·INP·CLS 요소 선택자
    conn: (navigator as any).connection?.effectiveType });
  const queued = navigator.sendBeacon('/rum', body);   // 떠나는 중에도 보낼 수 있게 대기열에 넣는다
  // queued === true는 "대기열에 들어감"이지 서버 도착이 아니다. false면 대기열 한도 등으로 거부된 것
}
onLCP(send);
onINP(send);   // 페이지가 hidden이 될 때 보고된다 → 한 페이지에서 여러 번 불릴 수 있다(id로 갱신)
onCLS(send);
```

- `web-vitals` README: CLS·INP는 `visibilityState`가 `hidden`이 될 때마다 보고된다. `unload`·`beforeunload` 대신 `visibilitychange`를 쓰라고 권하고, 이유는 Chrome Page Lifecycle 가이드로 넘긴다(모바일에서는 페이지가 `unload` 없이 사라질 수 있다).
- `sendBeacon`의 동작·제한은 [web-api/34](../../../languages/web-api/34-send-beacon-and-keepalive/2-summary.md), 문서 수명 이벤트는 [web-api/24](../../../languages/web-api/24-document-lifecycle-events/2-summary.md).
- 차원(dimension)을 붙여 보낸다: 페이지 유형, 기기 종류, 망 종류, 요소 선택자(attribution 빌드의 `target`·`interactionTarget`·`largestShiftTarget` — 직접 꺼내 직렬화해야 한다). 나중에 "어디가 나쁜가"를 자르려면 필요하다.
- 경로는 `location.pathname` 대신 `metric.navigationURL`(`web-vitals` 6.2.2 타입 정의)을 쓴다. 보고 콜백은 SPA 경로가 바뀐 **뒤에** 불릴 수 있어서, 현재 경로를 쓰면 이전 화면의 지표가 새 경로로 잘못 기록된다(`web-vitals` README).

### 3. 랩에서 직접 재기

```js
// DevTools 콘솔에 붙여 넣기 — 새로고침 후 값 확인
new PerformanceObserver(l => console.log('LCP', l.getEntries().at(-1).startTime, l.getEntries().at(-1).element))
  .observe({ type: 'largest-contentful-paint', buffered: true });
new PerformanceObserver(l => l.getEntries().forEach(e => !e.hadRecentInput && console.log('shift', e.value, e.sources)))
  .observe({ type: 'layout-shift', buffered: true });
new PerformanceObserver(l => l.getEntries().forEach(e => e.interactionId && console.log(e.name, e.duration)))
  .observe({ type: 'event', durationThreshold: 16, buffered: true });
```

- DevTools Performance 패널: 스로틀링(CPU 4×, 네트워크 "Slow 4G" 등)을 켜고 기록한다. 레이아웃 이동·LCP 마커·긴 태스크가 한 시간축에 나온다.
- Lighthouse 점수 가중치(Lighthouse 10): FCP 10% · Speed Index 10% · LCP 25% · TBT 30% · CLS 25%. 점수는 실행마다 흔들린다 — 한 번의 값이 아니라 분포로 본다(20번).
- 자동화: Playwright + CDP로 위 실험처럼 조건을 고정해 반복 측정한다.

## 장애 시나리오와 대처

### 1. 랩은 초록, 필드는 "개선 필요" — 저사양 기기 성능이 숨는다 (⚠)

- 현상: CI의 Lighthouse 점수는 95인데 Search Console 핵심 웹 지표 보고서는 모바일 LCP "개선 필요".
- 보이는 형태: CrUX 모바일 p75 LCP 3.4초(예시), 데스크톱 1.2초(예시). 랩 LCP 1.1초.
- 원인: 랩은 고정된 한 조건(기기 하나·망 하나)이다. 개발자 PC 무스로틀이면 빠른 쪽으로, Lighthouse 기본 모바일(CPU 4×·느린 4G 시뮬레이션)이어도 실제 사용자 분포 전체는 대표하지 못한다. 위 실험처럼 같은 페이지가 CPU·망에 따라 0.25s → 7.9s로 벌어진다. 랩 측정만으로는 이 꼬리가 안 보인다.
- 대처: 필드 p75를 기준 지표로 삼고, 모바일·데스크톱을 나눠 본다. 랩은 CPU 4×·느린 망 스로틀로 돌리고, RUM에 기기·망 차원을 붙여 나쁜 구간을 찾는다.

### 2. 이미지 크기 미지정 → 레이아웃 이동 (⚠)

- 현상: 본문을 읽거나 버튼을 누르려는 순간 내용이 아래로 밀린다.
- 보이는 형태: `layout-shift` 항목의 `sources`가 본문 요소를 가리킨다. 실험에서 CLS 0.2313("개선 필요").
- 원인: `<img>`에 `width`/`height`(또는 CSS `aspect-ratio`)가 없으면 로드 전 높이가 0이다. 이미지가 도착하면 그 아래가 통째로 밀린다.
- 대처: `width`/`height` 속성 + CSS `height: auto`로 비율을 알려 준다(14번). 광고·임베드는 자리를 미리 잡는다. 늦게 끼워 넣는 배너는 기존 내용 위가 아니라 아래에 넣거나 자리를 예약한다.

### 3. INP 나쁨 — "버튼이 안 눌린다"

- 현상: 필터 버튼을 누르면 화면이 0.3초 이상 그대로다.
- 보이는 형태: Event Timing `click` 항목 `duration` 312ms, `processingEnd − processingStart` ≈ 300ms. `web-vitals` INP rating `needs-improvement`.
- 원인: 클릭 핸들러가 무거운 동기 작업을 한다(processing). 또는 다른 긴 태스크가 메인 스레드를 쥐고 있었다(input delay). 또는 핸들러 뒤 큰 DOM 변경으로 렌더가 길다(presentation delay).
- 대처: 세 조각 중 큰 쪽을 attribution으로 확인하고, 작업 쪼개기·양보·워커([16번](../16-long-tasks-and-web-workers/2-summary.md)), 재렌더 범위 줄이기([18번](../18-ui-rerender-and-memoization/2-summary.md))로 간다.

### 4. 평균·잘못된 합산으로 꼬리를 숨김

- 현상: 대시보드의 "평균 LCP 1.4초"는 좋은데 사용자 불만이 계속된다.
- 보이는 형태: 평균은 낮고 p75·p95가 높다. 또는 페이지별 p75를 평균 내 전체 값을 만든다.
- 원인: 성능 분포는 오른쪽 꼬리가 길다. 평균·중앙값은 빠른 다수에 끌려간다(실험: p50 0.3s vs p75 2.1s).
- 대처: p75(와 p95)를 보고, 백분위는 원자료나 히스토그램을 합친 뒤 다시 계산한다.

### 5. RUM 값이 비거나 이상하다

- 현상: INP·CLS 보고가 모바일에서 크게 빠진다. 또는 SPA에서 화면을 바꿔도 LCP가 첫 화면 값 그대로다.
- 보이는 형태: 수집 서버의 INP 건수가 LCP 건수보다 훨씬 적다(INP는 상호작용이 있어야 생기므로 어느 정도 적은 것은 정상이다).
- 원인: `unload`에서 보내도록 짠 코드 — 모바일에서 `unload`가 안 불리는 경우가 있다. SPA의 화면 전환은 문서를 새로 받는 탐색이 아니라서 기본 설정의 LCP는 첫 탐색 값에 머문다. Chrome 151부터는 조건(상호작용 → URL 변경 → 페인트)을 갖춘 소프트 내비게이션을 기본으로 감지하고, `web-vitals` 6.x는 `reportSoftNavs: true`로 전환별 지표를 낸다(Chrome for Developers "Measuring soft navigations"). CrUX 반영 방식은 아직 정해지지 않았다.
- 대처: `visibilitychange`(hidden) 시점에 `sendBeacon`으로 보낸다(`web-vitals` 권장). SPA는 `reportSoftNavs: true`를 켜고 `metric.navigationURL`로 경로를 붙이거나, 라우트 전환 지표를 따로 정의한다(소프트 내비게이션을 지원하지 않는 브라우저 대비).

## 핵심 문장

- Core Web Vitals는 LCP(보였나)·INP(반응했나)·CLS(흔들렸나) 셋이고, 경계는 2.5s·200ms·0.1이다.
- 판정은 페이지 로드의 p75로, 모바일과 데스크톱을 나눠서 한다. 평균·중앙값은 느린 사용자를 숨긴다.
- LCP는 마지막 후보의 렌더 시각이고 입력이 오면 갱신을 멈춘다. INP는 상호작용 지연의 최댓값(50번마다 1개 무시)이다. CLS는 가장 큰 세션 창의 합이다.
- 이동 점수 = 영향 비율(이전∪이후 영역) × 거리 비율이다. 실험의 0.2313이 손 계산과 맞았다.
- 랩은 원인 찾기, 필드는 판정이다. 로드만 재는 랩(Lighthouse 탐색)은 INP를 못 재서 TBT로 대신하고, 로드 중 CLS만 본다.

## 관련 주제·근거

- 선행
  - [02 렌더링 파이프라인](../02-rendering-pipeline/2-summary.md) — 레이아웃 이동과 페인트가 생기는 자리
  - [03 이벤트 루프](../03-event-loop/2-summary.md) — input delay가 생기는 이유(태스크 대기)
- 후속(처방)
  - [13 크리티컬 패스와 자원 로딩](../13-critical-path-and-resource-loading/2-summary.md) — LCP의 "지연" 조각
  - [14 이미지 최적화](../14-image-optimization/2-summary.md) — LCP의 "로드 시간" 조각, 크기 예약(CLS)
  - [15 웹 폰트 로딩](../15-web-font-loading/2-summary.md) — 텍스트 LCP·폰트 교체 CLS
  - [16 긴 태스크와 웹 워커](../16-long-tasks-and-web-workers/2-summary.md) — INP
  - [20 성능 예산과 회귀 게이트](../20-performance-budgets-and-regression-gates/2-summary.md) — 랩 측정 노이즈, CI 게이트
  - [23 증상 색인](../23-web-symptom-index/2-summary.md)
- 문법·API: [web-api/34 sendBeacon](../../../languages/web-api/34-send-beacon-and-keepalive/2-summary.md), [web-api/24 문서 수명 이벤트](../../../languages/web-api/24-document-lifecycle-events/2-summary.md), [web-api/38 requestAnimationFrame](../../../languages/web-api/38-request-animation-frame/2-summary.md)
- 다른 영역: [data-analysis](../../data-analysis/README.md)(04 기술통계·05 백분위 — 미작성), [data-structure/07 힙](../../data-structure/07-heap/2-summary.md), [network/03 지연·대역폭](../../network/03-latency-bandwidth-bdp/2-summary.md)
- 근거
  - web.dev "Web Vitals" https://web.dev/articles/vitals — 세 지표, 임계값, p75·모바일/데스크톱 분리, 단계(stable), INP 2023 pending → 2024 stable, 필드·랩 도구
  - web.dev "Largest Contentful Paint (LCP)" https://web.dev/articles/lcp — 후보 요소, 크기 계산, 제외 휴리스틱, 입력 시 중단, bfcache·백그라운드 탭
  - web.dev "Optimize Largest Contentful Paint" https://web.dev/articles/optimize-lcp — 4.0s 나쁨, 네 조각과 권장 비중
  - web.dev "Interaction to Next Paint (INP)" https://web.dev/articles/inp — 대상 입력, 세 조각, 50번마다 1개 무시, 200/500ms
  - web.dev "Cumulative Layout Shift (CLS)" https://web.dev/articles/cls — 세션 창(1s·5s), 점수 공식, `hadRecentInput` 500ms(이산 입력만), 0.1/0.25, 랩은 로드 중만
  - Chrome for Developers "Measuring soft navigations" https://developer.chrome.com/docs/web-platform/soft-navigations — Chrome 151 기본 활성, `web-vitals` v6부터 지원, CrUX 반영 미정
  - web.dev "Why lab and field data can be different" https://web.dev/articles/lab-and-field-data-differences — 기기·캐시·LCP 요소·CLS 범위·INP·28일
  - web.dev "Total Blocking Time (TBT)" https://web.dev/articles/tbt — FCP~TTI 합산, Timespan 모드
  - W3C Beacon https://www.w3.org/TR/beacon/ — `sendBeacon()` 반환값(대기열 성공 여부)
  - W3C Event Timing https://w3c.github.io/event-timing/ — `durationThreshold` 기본 104·최소 16, 8ms 반올림, `interactionId` 대상 이벤트
  - W3C Largest Contentful Paint https://w3c.github.io/largest-contentful-paint/ · W3C Layout Instability https://wicg.github.io/layout-instability/
  - Chrome for Developers "CrUX methodology" https://developer.chrome.com/docs/crux/methodology — 사용자·플랫폼·출처 자격
  - Lighthouse "Performance scoring" https://developer.chrome.com/docs/lighthouse/performance/performance-scoring — 가중치 · GoogleChrome/lighthouse `docs/throttling.md` — 150ms·1.6Mbps·CPU 4×
  - `web-vitals` 6.2.2 소스(npm) — `dist/web-vitals.js` 임계값 상수, `dist/modules/lib/InteractionManager.js`(최대 10개·`/50`), `LayoutShiftManager.js`(1000·5000), `onINP.js`(기본 `durationThreshold` 40), README(visibilitychange·sendBeacon·`navigationURL`·`reportSoftNavs`), `types/base.d.ts`(`navigationURL`), `types/lcp·inp·cls.d.ts`(attribution 선택자 필드)
- 실험 목록 (headless Chrome 151.0.7922.173, Node 20.19.6 + playwright-core 1.62.1 + web-vitals 6.2.2 + sharp 0.33.5, 127.0.0.1 로컬 서버, 2026-10-04)
  - 08-A CLS·LCP·INP 관측: `scratchpad/wp/08/exp08_vitals.js` (공용 `lib.js`) — 4회, 출력 `out08a.txt`
  - 08-B 조건별 LCP와 섞인 분포 백분위: `scratchpad/wp/08/exp08_lab_vs_field.js` — 조건당 5회 × 2회 실행, 출력 `out08b.txt`
