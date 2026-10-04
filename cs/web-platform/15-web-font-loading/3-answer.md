# web-platform/15-web-font-loading — 정답

## 정답

### 1. 늦은 요청과 FOIT·FOUT

- 폰트는 CSS 안 `@font-face`로 선언된다. CSS를 받아 파싱하고, 그 폰트를 쓰는 텍스트가 있다는 것을 안 뒤에 요청된다. preload 스캐너는 CSS 안을 못 본다.
- FOIT(안 보이는 글자): 보이는 글자가 다른 서체로 바뀌는 깜빡임은 없지만, 기다리는 동안 내용을 못 읽는다. 텍스트가 LCP 요소면 LCP가 밀린다. 안 보이는 대체 폰트의 메트릭으로 자리를 잡아 두므로, 웹 폰트가 나타날 때 폭·줄 수가 달라지면 레이아웃 이동은 생길 수 있다.
- FOUT(대체 폰트 먼저): 바로 읽을 수 있지만, 바뀔 때 모양이 달라지고 줄 수가 바뀌면 레이아웃 이동(CLS)이 생긴다.

### 2. 세 구간과 권장값

- block: 폰트가 아직이면 **안 보이는** 대체 폰트로 그린다. 그 안에 오면 웹 폰트.
- swap: **보이는** 대체 폰트로 그린다. 그 안에 오면 웹 폰트로 교체.
- failure: 아직 안 왔으면 실패로 보고 대체 폰트로 고정.
- CSS Fonts 4 권장: `block` = block 짧게(3초)·swap 무한, `swap` = block 아주 짧게(100ms 이하)·swap 무한, `fallback` = block 아주 짧게(100ms 이하)·swap 짧게(3초), `optional` = 첫 페인트에 즉시 쓸 수 있을 때만 쓰고 레이아웃을 튀게 하지 않음. 명세는 UA가 시간을 조정할 수 있다고 허용한다.

### 3. 4000ms 지연에서의 Chrome 151

(실험, headless Chrome 151, CDP 스크린샷 판정)
- `auto`: 안 보임 → **약 2.06~2.1초** 대체 폰트 → 4.11~4.14초 웹 폰트.
- `block`: 안 보임 → **약 3.08~3.14초** 대체 폰트 → 4.14~4.17초 웹 폰트.
- `fallback`: 약 0.1초 안 보임 → 0.2초 대체 폰트 → 끝까지 대체 폰트(3초 swap 기간이 지난 뒤 도착).
- `auto`가 2초인 이유: Chromium `remote_font_face_source.cc`의 `NeedsInterventionToAlignWithLCPGoal()` — `font-display: auto` 폰트가 LCP 한계(`DocumentLoader::kLCPLimit` = 2000ms, 탐색 시작 기준)까지 안 오면 swap 기간으로 넘긴다. 그 밖에 `auto`는 망이 3G 이하로 느리면 처음부터 swap으로 다룬다. `block`은 `kFontLoadWaitLong` = 3000ms를 그대로 쓴다.

### 4. 전체 폰트 vs 서브셋의 LCP

(실험, CPU 4×·RTT 150ms·1.6Mbps)
- ① TTF 전체 4,582KB: 도착 23.9초. `auto` LCP 2020ms(2초 개입으로 대체 폰트가 그려진 시각), `swap` LCP 272ms.
- ② 7KB 서브셋: 도착 약 0.44~0.48초. `auto` LCP 480~520ms, `swap` 280~352ms(재실행 포함).
- (참고) 한글 완성형 WOFF2 488KB: 도착 2.9초, `auto` LCP 2016~2020ms.
- `swap`이면 LCP 수치는 지키지만, 24초 동안 대체 폰트로 보이고 그동안 4.5MB가 대역폭을 차지해 다른 자원도 늦어진다. 크기를 줄이는 것이 근본 처방이다.

### 5. unicode-range 매칭

(실험) 영어만 → 라틴 파일(15KB)만, 한글만 → 한글 파일(488KB)만, 섞임 → 둘 다.
- 명세는 `unicode-range`를 "이 텍스트에 이 폰트 파일을 내려받을지"의 힌트로 정의한다. 페이지 텍스트와 범위가 겹치는 `@font-face`만 요청된다.

### 6. preload 이중 다운로드

- 경고 핵심: "A preload for '…' is found, but is not used because the request credentials mode does not match. Consider taking a look at crossorigin attribute." 몇 초 뒤 "preloaded using link preload but not used within a few seconds"도 나온다.
- 원인: 폰트는 CORS(익명) 모드로 요청된다. `crossorigin` 없는 preload는 다른 자격 증명 모드라 실제 폰트 요청과 매칭되지 않는다. 실험: 37ms(preload)와 363ms(실제 요청) 두 번.
- 고침: `<link rel=preload as=font type=font/woff2 href=… crossorigin>`. 실험: 29ms 한 번만 요청(preload 없을 때 345ms).

### 7. 교체 CLS와 처방

(실험, 폭 400px, 영어 문단 + 상자)
- `swap`: 9줄(216px) → 10줄(240px), 상자 24px 이동 → **CLS 0.011**(3회 같음).
- `optional`: 800ms 지연이라 첫 페인트에 못 대어 대체 폰트로 끝 → CLS 0. 대가: 첫 방문에 웹 폰트를 못 볼 수 있다.
- `size-adjust: 91.2%`로 맞춘 DejaVu Serif 대체 폰트: 처음부터 10줄 → CLS 0. 대가: 대체 폰트별로 값을 재서 관리해야 한다(도구로 자동화 가능 — `next/font`, Fontaine).
- 같은 줄 안에서 글자만 바뀌는 것은 다른 요소를 밀지 않는다. 블록 크기(줄 수·줄 높이)가 바뀔 때 CLS가 생긴다.

### 8. optional의 규칙과 preload

- 명세: 첫 페인트에 "즉시" 쓸 수 있으면 웹 폰트, 아니면 block·swap이 다 끝난 것으로 보고 대체 폰트. 대체 폰트로 그린 뒤에는 그 페이지 수명 동안 바꾸지 않는다.
- Chromium: block 기간을 건너뛴다. 렌더링이 시작된 뒤에는 메모리 캐시에서 왔거나, 렌더링 시작 전에 끝났거나, 대기 중에 그 폰트로 그릴 일이 없었으면 쓴다. 실험에서 1초·4초 지연 둘 다 끝까지 대체 폰트였다.
- preload와 함께: Chrome 83부터 preload한 optional 폰트는 첫 렌더를 최대 100ms 기다린다(web.dev). 그 안에 오면 첫 렌더부터 웹 폰트로 그려진다. 재방문(캐시)에서는 웹 폰트가 쓰일 가능성이 높아지지만 보장되지는 않는다(명세는 "might have finished downloading"이라고만 쓴다. 캐시에서도 첫 페인트에 늦으면 대체 폰트).

### 9. Playwright 스크린샷 함정

- `page.screenshot()`은 웹 폰트가 로드될 때까지 기다렸다가 찍는다. 그래서 FOIT·FOUT 구간이 찍히지 않는다(실험 초기에 `block`·`fallback` 결과가 왜곡된 원인).
- CDP `Page.captureScreenshot`을 직접 호출하면 기다리지 않고 현재 화면을 찍는다.

### 10. 자료구조와 서브셋 밖 글자

- 글자 집합: 사이트 텍스트의 코드 포인트를 모아 집합으로 만든다. 코드 포인트를 비트셋(최대 U+10FFFF)으로 표시하면 합집합·포함 검사가 비트 연산이다.
- `unicode-range` 매칭: 정렬된 구간 목록에서 "이 코드 포인트가 어느 구간에 드나"를 이분 탐색으로 찾고, 겹치는 파일만 받는다.
- 서브셋 밖 글자: 그 폰트에 글리프가 없으니 `font-family` 목록의 다음 폰트(대체 폰트)로 그 글자만 그려진다. 같은 문장에 서체가 섞인다. 사용자 입력 영역은 `unicode-range` 조각 방식이나 시스템 폰트가 낫다.
