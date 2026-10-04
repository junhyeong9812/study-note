# web-platform/15-web-font-loading — FOIT·FOUT, font-display, 서브셋과 unicode-range, preload, 대체 폰트 메트릭 — 정리 (힌트)

## 해결하는 문제

웹 폰트는 HTML·CSS를 받은 **뒤에** 발견되고, 받는 동안 브라우저는 "글자를 안 보이게 둘지, 다른 폰트로 먼저 보여 줄지"를 정해야 한다.

```text
  한글 폰트 TTF 전체 4.5MB, 모바일 망(1.6Mbps)
  0s ── HTML ── CSS ── 폰트 요청 ─────────────────────────────── 23.9s 폰트 도착
        └ 그동안 제목 글자는?  ① 안 보임(FOIT)  ② 대체 폰트로 보였다가 바뀜(FOUT)
        └ 바뀌는 순간 글자 폭이 달라 줄 수가 바뀌면 아래 내용이 밀림(CLS)
```

- *FOIT(Flash of Invisible Text)*: 폰트를 기다리는 동안 글자가 안 보이는 현상.
- *FOUT(Flash of Unstyled Text)*: 대체 폰트로 먼저 그렸다가 웹 폰트가 오면 바뀌는 현상.
- 해법은 네 갈래다.
  - 기다리는 정책을 고른다(`font-display`).
  - 파일을 작게 만든다(WOFF2, 서브셋, `unicode-range` 분할).
  - 일찍 요청한다(preload·preconnect).
  - 바뀌어도 안 밀리게 대체 폰트 크기를 맞춘다(`size-adjust` 등).

쉬운 예: 회의 자료 인쇄.
- 지정 서체 파일이 올 때까지 인쇄를 멈춘다(FOIT) vs 기본 서체로 먼저 인쇄해 나눠 주고 나중에 다시 나눠 준다(FOUT).
- 다시 나눠 준 자료의 쪽 수가 바뀌면 사람들이 읽던 위치를 잃는다(CLS).

똑같은 구조다.\
"기다림 vs 바뀜"의 선택과, 바뀔 때의 흔들림을 줄이는 문제다.

실무 예:
- 한글 웹 폰트 전체를 모든 페이지에서 받아 첫 화면 제목이 2초 넘게 안 보인다.
- `font-display: swap`으로 바꿨더니 FOIT는 사라졌지만 폰트가 바뀌는 순간 본문이 한 줄 늘어 버튼이 밀린다.

## 동작·원리

### 1. 폰트 표시 타임라인 — 세 구간

```text
  그 폰트를 페이지에서 처음 쓰려는 시점(타이머 시작 — 보통 요청 시작과 같다. preload면 요청이 더 앞설 수 있다)
  │◄── block 기간 ──►│◄────── swap 기간 ──────►│◄── failure 기간 ──►
  │ 안 보이는 대체폰트 │ 보이는 대체 폰트           │ 대체 폰트로 고정
  │ (도착 → 웹폰트)    │ (도착 → 웹폰트로 교체)     │ (도착해도 안 바꿈)
```

CSS Fonts 4 `font-display`(규범)

| 값 | block 기간 | swap 기간 | 뜻 |
|---|---|---|---|
| `auto` | 브라우저가 정함 | 브라우저가 정함 | 많은 브라우저가 `block`과 비슷하다고 명세 주석이 적는다 |
| `block` | 짧게(3초 권장) | 무한 | 안 보이다가 도착하면 교체 |
| `swap` | 아주 짧게(100ms 이하 권장) | 무한 | 바로 대체 폰트, 도착하면 교체 |
| `fallback` | 아주 짧게(100ms 이하 권장) | 짧게(3초 권장) | 3초 안에 오면 교체, 아니면 대체 폰트 고정 |
| `optional` | — | — | 첫 페인트에 "즉시" 쓸 수 있으면 쓰고, 아니면 block·swap이 다 끝난 것으로 취급. 페이지 레이아웃을 "튀게" 하면 안 된다 |

- 명세는 "UA가 조금 다른 시간이나 더 정교한 동작을 쓸 수 있다"고 허용한다. 그래서 실제 값은 브라우저 구현을 봐야 한다.
- Chromium 구현(소스 `third_party/blink/renderer/core/loader/resource/font_resource.cc`, `.../css/remote_font_face_source.cc`, main 브랜치 2026-10-04 조회)
  - 짧은 한계 `kFontLoadWaitShort` = 100ms, 긴 한계 `kFontLoadWaitLong` = 3000ms.
  - `block`: 3초까지 안 보임 → 그 뒤 swap. `fallback`: 100ms까지 안 보임 → 3초까지 swap → 그 뒤 failure.
  - `auto`: 기본은 `block`과 같지만, **탐색 시작 후 2초(LCP 한계, `DocumentLoader::kLCPLimit` = 2000ms)**가 지나도 안 왔으면 바로 swap으로 넘긴다(`NeedsInterventionToAlignWithLCPGoal`). 또 망이 3G 이하로 느리면 처음부터 swap으로 다룬다(`ShouldTriggerWebFontsIntervention`).
  - `optional`: block 기간을 건너뛴다("never render invisible fallback"). 렌더링이 시작된 뒤에는, 메모리 캐시에서 왔거나 렌더링 시작 전에 끝났거나 대기 중에 그 폰트로 그릴 일이 없었으면 쓰고(swap), 아니면 failure(`ComputePeriod`의 `kOptional` 분기).
  - web.dev "Preload optional fonts": Chrome 83부터 preload한 optional 폰트는 첫 렌더를 최대 100ms 기다려 줘서, 첫 렌더부터 웹 폰트로 그릴 기회를 준다.

### 2. 크기를 줄이는 법 — WOFF2, 서브셋, unicode-range

```text
  NanumGothic.ttf 4,582KB
    ├─ 서브셋: 한글 완성형 11,172자 + 자모 + ASCII → WOFF2 503KB
    ├─ 한글 완성형만  → 488KB                          ┐ unicode-range로 나눠 두면
    ├─ 라틴(U+0020~00FF) 224자 → 15KB                  ┘ 페이지에 쓰인 범위의 파일만 받는다
    └─ 이 페이지에 쓰인 37자 → 7KB
```

- *서브셋(subset)*: 폰트에서 실제로 쓸 글리프만 남긴 파일.
- *WOFF2*: 웹 폰트용 압축 컨테이너. web.dev는 "WOFF보다 30% 더 압축된다"고 적는다.
- `unicode-range`: `@font-face`가 담당하는 코드 포인트 범위. 명세는 이것을 "폰트를 내려받을지 정할 때의 힌트"로 정의한다. 같은 `font-family`를 범위별 파일로 나눠 두면, 페이지 텍스트와 겹치는 범위의 파일만 요청된다.
- 한글은 글자 수가 많아(완성형 11,172자) 라틴 폰트보다 크다. 전체를 한 파일로 쓰면 첫 화면이 그 무게를 진다. 대형 웹 폰트 서비스들은 한글을 사용 빈도별로 여러 `unicode-range` 조각으로 나눠 준다 `[?]`(서비스별 분할 방식은 확인하지 않았다).

### 3. 발견을 앞당기는 법 — preload·preconnect

```text
  preload 없음:  HTML ─► font.css(300ms) ─► @font-face 발견 ─► 폰트 요청(345ms)
  preload 있음:  HTML ─► 폰트 요청(29ms) ┐
                       ─► font.css ─────┴─► 이미 받는 중
```

- 폰트는 CSS 안 `@font-face`를 처리한 뒤, 그리고 그 폰트를 쓰는 텍스트가 있을 때 요청된다. preload 스캐너는 CSS 안을 못 본다(13번).
- `<link rel=preload as=font type=font/woff2 href=… crossorigin>`: 폰트 요청은 CORS 모드라서 `crossorigin`이 없으면 preload가 재사용되지 않고 한 번 더 받는다.
- 다른 출처 폰트 CDN은 `<link rel=preconnect href=… crossorigin>`으로 연결을 미리 연다.

### 4. 대체 폰트 메트릭 맞추기

- 폰트가 바뀔 때 CLS가 생기는 이유: 글자 폭·줄 높이가 달라 **블록의 크기**가 바뀌고, 그 아래 요소가 밀린다. 같은 줄 안에서 글자만 바뀌는 것은 다른 요소를 밀지 않는다.
- `@font-face`의 메트릭 재정의 서술자(CSS Fonts 4·5)
  - `size-adjust`: 글리프의 폭과 높이를 비율로 키우거나 줄인다.
  - `ascent-override`·`descent-override`·`line-gap-override`: 세로 메트릭(위·아래 높이, 줄 간격)을 덮어쓴다.
- 쓰는 법: 시스템에 있는 대체 폰트를 `src: local(...)`로 감싼 새 `@font-face`를 만들고, 웹 폰트와 폭이 같아지도록 `size-adjust`를 준다. Next.js 13+ `next/font`와 Fontaine 같은 도구가 자동으로 해 준다(Chrome for Developers "Improved font fallbacks").

### 실험 A: font-display 값별 타임라인 (Chrome 151 실측)

조건: 로컬 서버가 37자 서브셋 WOFF2를 1000ms 또는 4000ms 늦게 준다. 텍스트 영역을 CDP `Page.captureScreenshot`으로 약 60ms 간격으로 찍어 어두운 화소 수로 상태(안 보임 / 대체 폰트 / 웹 폰트)를 판정한다. 대체 폰트는 `serif`.

```js
// exp15_font_display.js 핵심 (scratchpad/wp/08/)
// @font-face{font-family:Web;src:url(/f.woff2?delay=${delay}) format('woff2');font-display:${display}}
// #t{font:32px Web, serif}
// 주의: Playwright page.screenshot()은 웹 폰트 로딩을 기다리므로 타임라인이 왜곡된다 → CDP로 직접 찍는다
const { data } = await cdp.send('Page.captureScreenshot', { format: 'png', clip: { x: 0, y: 0, width: 920, height: 70, scale: 1 } });
```

(실험, headless Chrome 151.0.7922.173, 스로틀 없음, 2026-10-04 — 시각은 Node 쪽 경과 시간이라 ±60ms 정도 거칠다. 2회 실행 중 1회차, 2회차와 사실 점검 재실행도 같은 순서·비슷한 시각 — 재실행 auto 4000ms 2093ms 대체폰트, block 4000ms 3137ms 대체폰트)

```text
기준 어두운 픽셀 수: 대체 폰트(serif) 3704  웹 폰트 3565
auto     폰트 지연 1000ms: 104ms 안보임 → 1106ms 웹폰트   (FCP 52ms)
auto     폰트 지연 4000ms: 97ms 안보임 → 2105ms 대체폰트 → 4139ms 웹폰트   (FCP 80ms)
block    폰트 지연 1000ms: 76ms 안보임 → 1128ms 웹폰트   (FCP 48ms)
block    폰트 지연 4000ms: 106ms 안보임 → 3100ms 대체폰트 → 4137ms 웹폰트   (FCP 92ms)
swap     폰트 지연 1000ms: 107ms 대체폰트 → 1157ms 웹폰트   (FCP 84ms)
swap     폰트 지연 4000ms: 113ms 대체폰트 → 4152ms 웹폰트   (FCP 96ms)
fallback 폰트 지연 1000ms: 80ms 안보임 → 198ms 대체폰트 → 1156ms 웹폰트   (FCP 64ms)
fallback 폰트 지연 4000ms: 104ms 안보임 → 205ms 대체폰트   (FCP 80ms)
optional 폰트 지연 1000ms: 108ms 대체폰트   (FCP 48ms)
optional 폰트 지연 4000ms: 113ms 대체폰트   (FCP 56ms)
(2회차 auto 4000ms: 95ms 안보임 → 2064ms 대체폰트 → 4131ms 웹폰트 / block 4000ms: 94ms 안보임 → 3084ms 대체폰트 → 4167ms 웹폰트)
```

관찰과 해석
- `block`: 3초 동안 안 보임(FOIT) → 대체 폰트 → 4초에 웹 폰트. Chromium의 3000ms 한계와 맞다.
- `auto`: **2초**에 대체 폰트로 넘어갔다. 명세의 `block` 권장(3초)이 아니라 Chromium의 LCP 한계(2000ms) 개입이다.
- `swap`: 처음부터 대체 폰트(FOUT), 도착하면 교체.
- `fallback`: 약 100ms 안 보임 뒤 대체 폰트. 1초에 온 폰트는 교체했고, 4초에 온 폰트는 쓰지 않았다(3초 swap 기간이 지남).
- `optional`: 이 실험의 1초·4초 지연(캐시 없음)에서는 끝까지 대체 폰트였다. 레이아웃이 바뀔 일이 없다. 첫 텍스트 페인트 전에 준비되면(빠른 망·preload·캐시) 웹 폰트를 쓸 수 있다.
- FCP는 10개 변형 다 100ms 안쪽이다. 안 보이는 글자도 FCP는 막지 않았다(이 페이지에서 FCP가 무엇으로 잡혔는지는 따로 확인하지 않았다 `[?]`).

### 실험 B: 한글 폰트 전체 vs 서브셋 — 텍스트 LCP

조건: 제목 한 줄(40px)이 LCP 요소. 폰트를 ① TTF 전체 4,582KB ② 한글 완성형 WOFF2 488KB ③ 37자 서브셋 7KB로 바꾸고, `font-display`는 `auto`·`swap`. CPU 4×, RTT 150ms, 1.6Mbps. ①은 1회(약 24초 걸림), 나머지 3회.

(실험, headless Chrome 151.0.7922.173, 뷰포트 412×823, 2026-10-04)

```text
browser 151.0.7922.173  크기: /full.ttf 4582KB, /hangul.woff2 488KB, /page.woff2 7KB
  /full.ttf     auto  LCP 항목(ms) 2020   폰트 수신 완료 23917~23917ms
  /full.ttf     swap  LCP 항목(ms) 272   폰트 수신 완료 23877~23877ms
  /hangul.woff2 auto  LCP 항목(ms) 2020 | 2016 | 2016   폰트 수신 완료 2892~2938ms
  /hangul.woff2 swap  LCP 항목(ms) 296 | 308 | 304   폰트 수신 완료 2930~2951ms
  /page.woff2   auto  LCP 항목(ms) 492 | 504 | 508   폰트 수신 완료 463~471ms
  /page.woff2   swap  LCP 항목(ms) 308 | 352 | 280   폰트 수신 완료 431~461ms
```

- `auto`에서 폰트가 2초 안에 못 오면 LCP가 **2016~2020ms**에 찍힌다 — 2초 개입으로 대체 폰트가 그려진 시각이다. 전체 TTF(24초)든 한글 WOFF2(2.9초)든 같다.
- 7KB 서브셋은 0.46초에 도착해 `auto`에서도 LCP 0.5초.
- `swap`은 대체 폰트로 바로 그려 LCP 0.27~0.35초. 웹 폰트로 바뀐 뒤 LCP 항목이 새로 나오지 않았다(이 실험).
- 해석: 큰 폰트는 `swap`으로 LCP를 지켜도 **24초 동안 대체 폰트**이고, 그 사이 4.5MB가 대역폭을 차지한다. 크기를 줄이는 것이 근본 처방이다.

### 실험 C: 교체 CLS와 size-adjust, unicode-range, preload crossorigin

조건: 폭 400px, `font: 16px/24px Web, serif` 영어 문단(3번 반복) 아래에 회색 상자. 웹 폰트(나눔고딕 라틴 서브셋)는 800ms 지연. size-adjust 값은 캔버스 `measureText`로 잰 문단 폭 비율(웹 폰트 3757px ÷ DejaVu Serif 4120px = 91.2%)로 정했다.

```css
/* 메트릭을 맞춘 대체 폰트 */
@font-face { font-family: FB; src: local('DejaVu Serif'); size-adjust: 91.2%; }
p { font: 16px/24px Web, FB; }
```

(실험, headless Chrome 151.0.7922.173, 2026-10-04 — CLS는 각 3회, 2회 실행 같은 값)

```text
문단 폭(px) 웹폰트 3757  serif 대체 3219  DejaVu Serif 4120  → size-adjust 116.7%
/cls-swap            CLS 0.0110 0.0110 0.0110  shift 시각 [894]  최종 문단 높이 240px
/cls-optional        CLS 0.0000 0.0000 0.0000  shift 시각 []  최종 문단 높이 216px
/cls-swap-adjusted   CLS 0.0000 0.0000 0.0000  shift 시각 []  최종 문단 높이 240px
  대체 폰트만 serif  문단 높이 216px
  대체 폰트만 FB     문단 높이 240px

unicode-range 분할 (latin.woff2 15KB · hangul.woff2 488KB)
  /ur-en   요청: /latin.woff2
  /ur-ko   요청: /hangul.woff2
  /ur-mix  요청: /latin.woff2, /hangul.woff2

폰트 preload (font.css 300ms 지연)
  /pl-none   폰트 요청 도착(문서 기준 ms): 345 
  /pl-cors   폰트 요청 도착(문서 기준 ms): 29 
  /pl-nocors 폰트 요청 도착(문서 기준 ms): 37, 363  콘솔: A preload for 'http://127.0.0.1:44845/latin.woff2' is found, but is not used because the request credentials mode does not match. Consider taking a look at crossorigin attribute. | The resource http://127.0.0.1:44845/latin.woff2 was preloaded using link preload but not used within a few seconds from the window's load event. Please make sure it has an appropriate `as` value and it is preloaded intentionally.
```

- 첫 줄의 116.7%는 일반 `serif`(이 호스트에서 DejaVu Serif가 아닌 다른 폰트로 해석됨) 기준 값이고, 실제 페이지에는 DejaVu Serif 기준 91.2%를 썼다.
- `swap`: 대체 폰트(9줄, 216px) → 웹 폰트(10줄, 240px)로 문단이 한 줄 늘어 상자가 24px 밀렸다 → CLS 0.011. 한 줄짜리 차이라 작지만, 문단이 많고 화면이 좁을수록 커진다.
- `optional`: 800ms 지연이라 첫 페인트에 못 대어 대체 폰트로 끝났다 → 이동 0(대신 웹 폰트를 못 봤다).
- `size-adjust`로 맞춘 대체 폰트: 처음부터 10줄(240px) → 교체해도 이동 0.
- `unicode-range`: 영어만 있는 페이지는 라틴 파일(15KB)만, 한글 페이지는 한글 파일만, 섞이면 둘 다 받았다.
- preload: `crossorigin`이 있으면 29ms에 요청(없을 때 345ms). 없으면 preload(37ms)와 실제 요청(363ms)이 따로 나가 **두 번** 받고, 콘솔에 credentials mode 불일치 경고가 남는다.

## 쓰이는 자료구조·알고리즘

- **사용 글리프 집합 계산**: 페이지(또는 사이트) 텍스트에서 코드 포인트 집합을 모아 서브셋 대상으로 삼는다. 유니코드 코드 포인트(최대 U+10FFFF)를 [비트셋](../../data-structure/18-bitset/2-summary.md)으로 표시하면 합집합·포함 검사가 비트 연산이다.
- **범위 겹침 검사(unicode-range)**: 각 `@font-face`의 범위 목록과 텍스트에 쓰인 코드 포인트를 비교해, 겹치는 파일만 내려받는다. 정렬된 구간 목록이면 이분 탐색으로 "이 글자가 어느 범위에 드나"를 찾는다([algorithm/06](../../algorithm/06-binary-search/2-summary.md)).
- **폰트 표시 상태 기계**: block → swap → failure의 시간 기반 상태 기계. 타이머(100ms·3000ms, Chromium의 auto는 2000ms 개입) 이벤트로 상태가 바뀌고, 상태가 바뀔 때 텍스트를 다시 그린다.
- **폰트 대체 체인**: `font-family` 목록을 앞에서부터 보며 "이미 로드된 첫 폰트"로 그린다(명세의 "render with a fallback font face"). 글자마다 지원 여부를 보는 클러스터 매칭은 목록 순회다.

## 적용 — 풀어나가는 법

### 1. 순서

```text
  ① 진단: Network에서 폰트 파일 크기·요청 시작 시각, Performance 패널에서 텍스트가 안 보이는 구간·LCP 요소
  ② 크기: WOFF2 + 서브셋(사이트에 쓰는 글자, 또는 unicode-range 조각)
  ③ 정책: 본문 = swap(+메트릭 맞춤) 또는 optional, 로고처럼 꼭 그 폰트여야 할 짧은 텍스트만 block
  ④ 발견: 첫 화면 폰트 1~2개만 preload(crossorigin), 다른 출처면 preconnect
  ⑤ 흔들림: size-adjust 등으로 대체 폰트 맞추기 → CLS 확인
```

### 2. CSS

```css
/* 범위별로 나눈 같은 패밀리 — 쓰인 범위만 받는다 */
@font-face {
  font-family: "Brand Sans";
  src: url(/fonts/brand-latin.woff2) format("woff2");
  unicode-range: U+0000-00FF;
  font-display: swap;
}
@font-face {
  font-family: "Brand Sans";
  src: url(/fonts/brand-hangul.woff2) format("woff2");
  unicode-range: U+AC00-D7A3, U+3131-318E;
  font-display: swap;
}
/* 교체 때 흔들림을 줄이는 대체 폰트 — 값은 측정으로 정한다 */
@font-face {
  font-family: "Brand Fallback";
  src: local("Arial");
  size-adjust: 97%;          /* (예시) */
  ascent-override: 92%;      /* (예시) */
}
body { font-family: "Brand Sans", "Brand Fallback", sans-serif; }
```

```html
<link rel="preload" as="font" type="font/woff2" href="/fonts/brand-latin.woff2" crossorigin>
```

### 3. 서브셋 만들기 (Node, subset-font)

```ts
import subsetFont from 'subset-font';
import { readFile, writeFile } from 'node:fs/promises';

// 사이트에서 쓰는 글자를 모아 서브셋 WOFF2를 만든다
const text = (await readFile('dist/all-text.txt', 'utf8'));
const out = await subsetFont(await readFile('NanumGothic.ttf'), text, { targetFormat: 'woff2' });
await writeFile('public/fonts/nanum-site.woff2', out);
```

- 사용자 입력 텍스트(댓글·검색어)가 화면에 나오는 곳은 서브셋 밖 글자가 섞일 수 있다. 그 글자는 다음 `font-family`로 그려진다(글자마다 다른 폰트). 그런 영역은 `unicode-range` 조각 방식이나 시스템 폰트가 낫다.

### 4. 확인 코드

```js
// 폰트 로딩 상태와 시각
document.fonts.addEventListener('loadingdone', e => console.log('loaded', e.fontfaces.map(f => f.family), performance.now()));
console.log([...document.fonts].map(f => `${f.family} ${f.status}`));
```

- Playwright로 자동화할 때 `page.screenshot()`은 웹 폰트 로딩을 기다린다. FOIT·FOUT 구간을 보려면 CDP `Page.captureScreenshot`을 직접 쓴다(실험 A의 함정).

## 장애 시나리오와 대처

### 1. 폰트 로딩 동안 텍스트가 안 보임 — FOIT (⚠)

- 현상: 첫 화면 제목·버튼 글자가 몇 초간 비어 있다.
- 보이는 형태: 필름 스트립에 빈 글자 자리. 실험: `block`은 3초, Chrome의 `auto`는 2초까지 안 보임. 텍스트가 LCP 요소면 LCP가 그 시각으로 밀림(실험 B: 2016~2020ms).
- 원인: `font-display`가 `block`이거나 지정하지 않아(`auto`) block 기간이 있다. 커리큘럼의 "블록 기간 약 3초"는 명세 권장값이고, Chrome 151의 `auto`는 실측 2초였다(LCP 한계 개입).
- 대처: 본문은 `swap`(+메트릭 맞춤) 또는 `optional`. 폰트 크기를 줄이고 preload.

### 2. swap 교체로 레이아웃 이동 (⚠)

- 현상: 폰트가 바뀌는 순간 본문 줄 수가 바뀌어 아래 버튼·이미지가 밀린다.
- 보이는 형태: 웹 폰트 도착 시각에 `layout-shift` 항목. 실험: 줄 9 → 10, CLS 0.011.
- 원인: 대체 폰트와 웹 폰트의 글자 폭·세로 메트릭이 다르다.
- 대처: `size-adjust`·`ascent-override` 등으로 대체 폰트를 맞춘다(실험: CLS 0). 또는 `optional`(이동 0이지만 첫 방문엔 웹 폰트를 못 볼 수 있다). 프레임워크 도구(`next/font`, Fontaine)를 쓴다.

### 3. 한글 폰트 전체를 모든 페이지에서 → LCP 지연·대역폭 낭비 (⚠)

- 현상: 모바일에서 첫 화면이 느리고, 폰트가 늦게 바뀐다.
- 보이는 형태: Network에 수 MB 폰트. 실험: TTF 전체 4,582KB가 1.6Mbps에서 23.9초. `auto`면 LCP 2.02초(대체 폰트), `swap`이어도 24초간 대체 폰트.
- 원인: 한글 11,172자 + 한자 + 힌팅을 담은 데스크톱용 TTF를 그대로 쓴다.
- 대처: WOFF2 + 서브셋(실험: 사이트 글자만이면 수 KB~수백 KB), `unicode-range` 조각, 굵기 수 줄이기, 첫 화면 폰트만 preload.

### 4. preload했는데 폰트를 두 번 받음

- 현상: 같은 woff2가 Network에 두 줄.
- 보이는 형태: 콘솔 "A preload for '…' is found, but is not used because the request credentials mode does not match. Consider taking a look at crossorigin attribute." (실험: 37ms·363ms 두 요청)
- 원인: 폰트는 CORS 모드로 요청된다. `crossorigin` 없는 preload는 자격 증명 모드가 달라 매칭되지 않는다.
- 대처: `<link rel=preload as=font type=font/woff2 crossorigin>`. 다른 출처면 서버가 CORS 헤더(`Access-Control-Allow-Origin`)를 줘야 폰트를 쓸 수 있다.

### 5. 서브셋 밖 글자가 다른 폰트로 섞임

- 현상: 사용자 이름·댓글의 일부 글자만 모양이 다르다.
- 보이는 형태: 같은 문장 안에서 글자마다 서체가 다르다. DevTools Computed 탭 "Rendered Fonts"에 두 폰트.
- 원인: 서브셋에 없는 코드 포인트는 `font-family`의 다음 폰트로 그려진다.
- 대처: 사용자 입력 영역은 `unicode-range` 조각 방식(필요한 조각만 추가로 받음) 또는 시스템 폰트를 쓴다.

## 핵심 문장

- 폰트 표시는 block(안 보임) → swap(대체 폰트) → failure(대체 고정)의 시간 구간이고, `font-display`가 구간 길이를 정한다.
- 명세 권장은 block 3초·swap 100ms 이하지만 구현은 다를 수 있다. Chrome 151의 `auto`는 2초에 대체 폰트로 넘어갔다(LCP 한계 개입).
- 본문은 `swap` + 대체 폰트 메트릭 맞춤, 또는 `optional`. 교체로 줄 수가 바뀌면 CLS가 생긴다.
- 한글 폰트는 서브셋·WOFF2·`unicode-range` 조각으로 줄인다. 전체 TTF 4.5MB와 37자 서브셋 7KB는 650배 차이다.
- 폰트 preload·preconnect에는 `crossorigin`을 붙인다. preload에서 빠지면 두 번 받고, preconnect에서 빠지면 미리 연 연결을 폰트 요청이 재사용하지 못할 수 있다.

## 관련 주제·근거

- 선행
  - [13 크리티컬 패스와 자원 로딩](../13-critical-path-and-resource-loading/2-summary.md) — CSS 안 자원의 늦은 발견, preload
  - [08 Web Vitals](../08-web-performance-vitals/2-summary.md) — 텍스트 LCP, CLS
- 후속·연결
  - [14 이미지 최적화](../14-image-optimization/2-summary.md), [12 국제화](../12-internationalization-and-localization/2-summary.md)(다국어 글자 범위), [20 성능 예산](../20-performance-budgets-and-regression-gates/2-summary.md)
  - [23 증상 색인](../23-web-symptom-index/2-summary.md)(폰트 깜빡임 — §1·§5·§7)
  - [data-structure/18 비트셋](../../data-structure/18-bitset/2-summary.md), [algorithm/06 이분 탐색](../../algorithm/06-binary-search/2-summary.md), [network/35 연결 관리](../../network/35-http-connection-management/2-summary.md)
- 문법: [css/50 폰트와 웹 폰트](../../../languages/css/syntax/50-fonts-and-webfonts/2-summary.md), [html/09 스타일시트와 리소스 힌트](../../../languages/html/syntax/09-stylesheets-and-resource-hints/2-summary.md)
- 근거
  - CSS Fonts Module Level 4 https://drafts.csswg.org/css-fonts-4/ — 폰트 표시 타임라인(block·swap·failure, §3.2 "At the moment the user agent first attempts to use a given downloaded font face"에 타이머 시작), `font-display` 값별 권장(3s·100ms), `unicode-range`(다운로드 힌트), 대체 폰트로 그리기, 메트릭 재정의 서술자
  - web.dev "Best practices for fonts" https://web.dev/articles/font-best-practices — 값별 표, optional 권장, WOFF2 30%, unicode-range
  - web.dev "Optimize web fonts"(learn/performance) https://web.dev/learn/performance/optimize-web-fonts · "Optimize WebFont loading and rendering" https://web.dev/articles/optimize-webfont-loading
  - web.dev "Prevent layout shifting and flashes of invisible text by preloading optional fonts" https://web.dev/articles/preload-optional-fonts — Chrome 83, 100ms
  - web.dev "Assist the browser with resource hints" https://web.dev/learn/performance/resource-hints — preconnect·preload의 `crossorigin`
  - Chrome for Developers "Improved font fallbacks" https://developer.chrome.com/blog/font-fallbacks — `size-adjust`·override 서술자, Fontaine, `next/font`
  - Chromium 소스(main, 2026-10-04 조회): `third_party/blink/renderer/core/loader/resource/font_resource.cc`(`kFontLoadWaitShort` 100ms·`kFontLoadWaitLong` 3000ms), `third_party/blink/renderer/core/css/remote_font_face_source.cc`(값별 기간 계산, `NeedsInterventionToAlignWithLCPGoal`, 3G 이하 개입, optional의 block 생략), `third_party/blink/renderer/core/loader/document_loader.h`(`kLCPLimit` 2000ms)
- 실험 목록 (headless Chrome 151.0.7922.173, Node 20.19.6 + playwright-core 1.62.1 + subset-font 2.9.0 + sharp 0.33.5, 127.0.0.1 로컬 서버, 2026-10-04)
  - 폰트 준비: `scratchpad/wp/08/mkfonts.js` — `/usr/share/fonts/truetype/nanum/NanumGothic.ttf`에서 WOFF2 4종
  - 15-A font-display 타임라인: `scratchpad/wp/08/exp15_font_display.js` — 2회, 출력 `out15a.txt`·`out15a2.txt`
  - 15-B 전체 vs 서브셋 텍스트 LCP: `scratchpad/wp/08/exp15_font_lcp.js` — 출력 `out15c.txt`
  - 15-C 교체 CLS·size-adjust·unicode-range·preload crossorigin: `scratchpad/wp/08/exp15_font_cls.js` — 2회, 출력 `out15b.txt`
