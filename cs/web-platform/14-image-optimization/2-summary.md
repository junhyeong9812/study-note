# web-platform/14-image-optimization — 포맷·반응형 이미지·지연 로딩·공간 예약·첫 화면 우선순위 — 정리 (힌트)

## 해결하는 문제

이미지는 페이지 바이트의 큰 몫이고, LCP 요소가 이미지인 경우가 많다. 그런데 "원본 하나를 모두에게" 보내면 세 가지가 동시에 나빠진다.

```text
  3840×2160 원본 JPEG(154KB) 하나를 그대로
  ┌ 폭 400px 휴대폰(DPR 2)  ─ 필요한 건 800px 폭 → 14KB면 충분, 154KB를 받음 (11배)
  ├ 크기 정보 없음          ─ 도착 전 높이 0 → 도착하면 아래 내용이 밀림 (CLS)
  └ 전부 loading=lazy       ─ 첫 화면 히어로까지 늦게 요청 → LCP 지연
```

- 해법은 네 갈래다.
  - 포맷: 같은 화질을 더 적은 바이트로(AVIF·WebP, JPEG 폴백).
  - 해상도: 화면 폭 × 화소 밀도에 맞는 크기 후보를 브라우저가 고르게(`srcset`·`sizes`·`<picture>`).
  - 시점: 첫 화면 아래 이미지는 늦게(`loading=lazy`), 첫 화면 히어로는 먼저(`fetchpriority=high`).
  - 공간: 도착 전에 자리를 잡아 둔다(`width`/`height`, `aspect-ratio`).
  - *DPR(device pixel ratio)*: CSS 1px에 대응하는 물리 화소 수. DPR 2 화면에서 폭 400 CSS px 이미지를 선명하게 보이려면 800 화소가 필요하다.

쉬운 예: 사진 인화.
- 지갑에 넣을 사진을 포스터 크기로 인화하지 않는다(해상도).
- 같은 사진도 인화지 종류에 따라 값이 다르다(포맷).
- 앨범에 사진 칸을 먼저 비워 두면, 사진이 늦게 와도 다른 사진이 밀리지 않는다(공간 예약).

똑같은 구조다.\
"누가 어떤 크기로 볼지"를 HTML로 알려 주면 브라우저가 맞는 파일을 고르고, 자리를 미리 잡는다.

실무 예:
- CMS에서 올린 휴대폰 사진 원본(수 MB)이 상품 목록 썸네일에 그대로 나간다.
- 리뷰 이미지가 늦게 떠서 "구매" 버튼이 아래로 밀린다.
- 성능 개선으로 모든 `<img>`에 `loading="lazy"`를 일괄 적용했더니 LCP가 늘었다.

## 동작·원리

### 1. 포맷 — 같은 화질을 더 적게

```text
  JPEG  : 8×8 블록 DCT(변환 부호화) → 양자화(손실) → 엔트로피 부호화
  WebP  : VP8 키프레임 방식 — 이웃 블록으로 예측 → 차이를 변환·양자화 (손실 모드)
  AVIF  : AV1 영상 코덱의 인트라 프레임을 HEIF(ISOBMFF) 컨테이너에 담음
```

- *변환 부호화*: 화소 값을 주파수 성분으로 바꾼 뒤, 눈에 덜 띄는 고주파 성분을 거칠게 양자화해 버리는 손실 압축. JPEG의 DCT가 대표다(ITU-T T.81).
- WebP 손실 모드는 VP8 키프레임처럼 예측 부호화를 쓴다. Google은 같은 SSIM에서 JPEG보다 25~34% 작다고 밝힌다(developers.google.com/speed/webp).
- AVIF는 "AV1 이미지를 HEIF에 담는 형식"이다(AOMedia AVIF 명세).
- 무손실 압축(LZ77·허프만 계열, [algorithm 영역](../../algorithm/curriculum.md) 33·34 미작성)과 달리, 이미지 손실 압축은 "버릴 정보"를 사람 눈 기준으로 고른다는 점이 다르다.

### 2. 반응형 이미지 — 브라우저가 후보를 고른다

```text
  <img srcset="img-400.jpg 400w, img-800.jpg 800w, img-1600.jpg 1600w, img-3840.jpg 3840w"
       sizes="(min-width: 800px) 50vw, 100vw">

  ① sizes 평가 → 이 이미지가 차지할 CSS 폭(슬롯 폭)   예: 뷰포트 400 → 100vw = 400px
  ② 후보마다 밀도 = 후보 폭(w) / 슬롯 폭               400w→1x, 800w→2x, 1600w→4x …
  ③ 화면 DPR과 비교해 후보를 고름(구체 규칙은 브라우저 재량)   DPR 2 → 800w
```

- `w` 서술자는 "이 파일의 실제 폭"을 알려 준다. 브라우저는 레이아웃 전에 골라야 하므로 `sizes`로 슬롯 폭을 미리 알려 준다. `sizes`가 없으면 `100vw`로 본다.
- HTML 표준은 마지막 선택을 "구현이 정하는 방식(implementation-defined manner)"으로 남긴다. 브라우저가 망 상태·캐시에 있는 후보 등을 고려할 여지다.
- `<picture>`
  - `<source type="image/avif">` → `<source type="image/webp">` → `<img src=jpg>`: 위에서부터 **지원하는 type의 첫 source**를 쓴다. 미지원 브라우저는 폴백으로 내려간다.
  - `<source media="(max-width: 600px)">`: 화면에 따라 다른 구도의 사진(아트 디렉션).
- 문법 세부: [html/35 srcset과 sizes](../../../languages/html/syntax/35-srcset-and-sizes/2-summary.md), [html/36 picture](../../../languages/html/syntax/36-picture-art-direction-and-format/2-summary.md).

### 3. 공간 예약 — `width`/`height`가 비율이 된다

```text
  <img width=800 height=450 style="width:100%; height:auto">
       └ HTML 표준 렌더링 절: width·height 속성 → 'aspect-ratio: auto 800 / 450' 표현 힌트
  폭 400px 컨테이너 → 도착 전부터 높이 225px 자리 확보 → 도착해도 이동 없음
```

- HTML 표준 "Rendering": `img`의 `width`·`height` 속성은 `width`·`height` 속성값으로 대응될 뿐 아니라 `aspect-ratio` 속성(형태 `auto w / h`)의 표현 힌트로도 대응된다.
- CSS로 `width: 100%`만 주고 `height: auto`를 빼면, 속성의 `height=450`이 그대로 높이가 되어 그림이 늘어난다(아래 실험의 `/cls-attrs-noauto`).
- CSS `aspect-ratio`로 직접 예약해도 된다. 문법은 [css/31 내재 크기와 aspect-ratio](../../../languages/css/syntax/31-intrinsic-sizing-and-aspect-ratio/2-summary.md).

### 4. 지연 로딩과 첫 화면 우선순위

- `loading="lazy"`: 뷰포트에서 일정 거리 안에 들어올 때까지 요청을 미룬다.
  - Chromium 임계 거리(유효 연결 유형별 기본값, Blink `settings.json5`의 `lazyLoadingImageMarginPx*`): 4G 1250px, 3G 2500px, 2G 6000px, slow-2G·오프라인 8000px, 알 수 없음 3000px. web.dev 글은 이를 "빠른 망 1250px, 3G 이하 2500px"로 줄여 말한다.
  - HTML 표준: 스크립트가 꺼져 있으면 lazy를 적용하지 않는다(서버가 이미지 요청으로 스크롤 위치를 추적하지 못하게 하는 반추적 조치).
  - 크기 지정 없는 lazy 이미지는 0×0으로 계산되어 한꺼번에 "뷰포트 안"으로 판정될 수 있다.
- lazy 이미지는 **레이아웃 뒤**에야 거리를 판정할 수 있다. 그래서 첫 화면 히어로에 lazy를 걸면 요청 자체가 늦어지고, 그 사이 다른 자원이 연결을 차지한다.
- Chrome의 이미지 우선순위는 13번 참고: Low/Medium에서 시작, 뷰포트 안이면 High. 히어로에 `fetchpriority=high`를 주면 처음부터 High.
- 스크립트로 하는 지연 로딩(IntersectionObserver + `data-src`)은 preload 스캐너가 못 본다. 마크업 `loading` 속성 쪽은 [web-api/35 IntersectionObserver](../../../languages/web-api/35-intersection-observer/2-summary.md), [html/34 img 크기와 로딩](../../../languages/html/syntax/34-img-alt-size-and-loading/2-summary.md).

### 실험: 포맷별 크기, srcset 선택, picture 폴백, 히어로 lazy, 크기 예약

조건: 호스트의 실제 사진 1장(Ubuntu 배경 `Clouds_by_Tibor_Mokanszki.jpg`, 3840×2160)을 sharp 0.33.5로 4개 폭 × 3개 포맷으로 인코딩해 로컬 서버로 준다. 히어로 실험은 CPU 4×, RTT 150ms, 1.6Mbps, 5회. 히어로 아래 2000px 뒤에 eager 3840w 이미지 6장을 둬서 대역폭 경쟁을 만든다.

```js
// exp14_images.js 핵심 (scratchpad/wp/08/)
const jpg  = await sharp(PHOTO).resize(w).jpeg({ quality: 75, mozjpeg: true }).toBuffer();
const webp = await sharp(PHOTO).resize(w).webp({ quality: 75 }).toBuffer();
const avif = await sharp(PHOTO).resize(w).avif({ quality: 50 }).toBuffer();
// 히어로 페이지: <img src="/img-1600.jpg?h" ${attr} width=1600 height=900 style="width:100%;height:auto">
//              + <div style="height:2000px"> + eager <img src="/img-3840.jpg?bN"> × 6
// attr = '' | 'loading=lazy' | 'fetchpriority=high'
```

(실험, headless Chrome 151.0.7922.173, 2026-10-04 — 히어로·CLS는 같은 조건 3회 실행에서 범위가 겹쳤다. 아래는 마지막 실행. 사실 점검 재실행 1회: 크기·srcset 선택·CLS는 같았고, 히어로 LCP eager 1452~1476 · lazy 5384~5448 · high 1488~1528ms)

```text
포맷별 크기 (실제 사진 3840x2160, sharp 0.33.5: JPEG mozjpeg q75 / WebP q75 / AVIF q50)
  3840w  jpg   154KB  webp    92KB  avif    41KB
  1600w  jpg    38KB  webp    24KB  avif    13KB
   800w  jpg    14KB  webp     8KB  avif     5KB
   400w  jpg     5KB  webp     3KB  avif     2KB

srcset 후보 선택 (요청된 파일)
  /full     뷰포트 400 DPR 1 → /img-400.jpg (5KB)  currentSrc=/img-400.jpg
  /full     뷰포트 400 DPR 2 → /img-800.jpg (14KB)  currentSrc=/img-800.jpg
  /full     뷰포트 400 DPR 3 → /img-1600.jpg (38KB)  currentSrc=/img-1600.jpg
  /full     뷰포트 1280 DPR 1 → /img-1600.jpg (38KB)  currentSrc=/img-1600.jpg
  /half     뷰포트 1280 DPR 1 → /img-800.jpg (14KB)  currentSrc=/img-800.jpg
  /half     뷰포트 400 DPR 2 → /img-800.jpg (14KB)  currentSrc=/img-800.jpg
  /nosizes  뷰포트 400 DPR 2 → /img-3840.jpg (154KB)  currentSrc=/img-3840.jpg
  /picture  뷰포트 800 DPR 1 → /img-800.avif (5KB)  currentSrc=/img-800.avif

히어로 이미지 (네트워크 150ms RTT·1.6Mbps, CPU 4×, 5회)
  /hero-eager  LCP 1460~1472  히어로 요청 시작(문서 요청 기준) 188~202 ms, 서버 도착 190~203 ms, 수신 완료 1398~1438 ms, 우선순위 Medium→High
  /hero-lazy   LCP 5384~5412  히어로 요청 시작(문서 요청 기준) 268~314 ms, 서버 도착 4929~4994 ms, 수신 완료 5320~5347 ms, 우선순위 Low→High
  /hero-high   LCP 1492~1524  히어로 요청 시작(문서 요청 기준) 189~194 ms, 서버 도착 190~199 ms, 수신 완료 1455~1477 ms, 우선순위 High

크기 예약 방식별 CLS (폭 400px, 이미지 600ms 지연)
  /cls-none          CLS 0.2200  최종 높이 225px
  /cls-attrs         CLS 0.0000  최종 높이 225px
  /cls-attrs-noauto  CLS 0.0000  최종 높이 450px
  /cls-aspect        CLS 0.0000  최종 높이 225px
```

같은 사진 1600w에서 품질 값을 바꿔 PSNR(원본 리사이즈 대비)도 쟀다(`exp14_psnr.js`). 품질 숫자는 인코더마다 척도가 달라서, 비슷한 PSNR끼리 크기를 비교하려는 것이다.

```text
jpeg  q60   25.0KB PSNR 40.40dB      webp  q60   20.2KB PSNR 40.64dB      avif  q35    6.7KB PSNR 39.84dB
jpeg  q75   38.4KB PSNR 41.88dB      webp  q75   24.2KB PSNR 41.27dB      avif  q50   12.6KB PSNR 41.81dB
jpeg  q90   89.8KB PSNR 44.02dB      webp  q90   65.3KB PSNR 43.74dB      avif  q65   24.2KB PSNR 43.63dB
```

관찰과 해석
- 포맷: PSNR 약 41.8dB에서 JPEG 38.4KB, AVIF 12.6KB — **이 사진에서는 AVIF가 JPEG의 약 1/3**이다. 하늘처럼 매끈한 영역이 많은 사진 1장, PSNR이라는 거친 척도의 결과다. 사진 종류·인코더 설정에 따라 비율은 달라진다.
- 해상도가 포맷보다 크다: 같은 JPEG에서 3840w → 800w는 154KB → 14KB(1/11). "맞는 크기"가 첫째다.
- srcset 선택(Chrome 151): 필요한 화소 = 슬롯 폭 × DPR. 400×1 → 400w, 400×2 → 800w, 400×3 = 1200 → 1600w, 1280×1 → 1600w, 1280의 50vw = 640 → 800w. 이 경우들은 "필요 화소 이상인 가장 작은 후보"와 맞는다. Chrome 내부 규칙 전체는 확인하지 않았다 `[?]`.
- srcset 없이 `src`만 둔 `/nosizes`는 휴대폰(400·DPR 2)에도 3840w 154KB를 보냈다.
- `<picture>`: 알 수 없는 `image/x-unknown` source는 건너뛰고, 다음 `image/avif`를 골랐다.
- **히어로 lazy**: 요청 "시작"은 80~110ms 늦을 뿐인데 서버 도착은 4.9초다. 해석: 레이아웃 뒤에야 요청이 만들어지는 사이 아래쪽 eager 이미지 6장이 HTTP/1.1 연결 6개(Chromium 상한)를 모두 차지했다. 히어로는 우선순위가 High로 올라가도 빈 연결을 기다렸다. 결과 LCP 1.47초 → 5.4초.
- `fetchpriority=high`는 이 페이지에서 eager와 차이가 없었다. eager 히어로가 이미 레이아웃 뒤 High로 올라갔고 먼저 요청됐기 때문이다(효과가 나는 조건은 13번 실험 B와 대비).
- 크기 미지정 → CLS 0.22. `width`/`height` + `height:auto`, 또는 `aspect-ratio` → 0. `height:auto`를 빼면 이동은 없지만 그림이 450px로 늘어난다.

## 쓰이는 자료구조·알고리즘

- **해상도 후보 선택**: 후보를 폭(w)으로 정렬해 두고, 목표 = 슬롯 폭 × DPR 이상인 첫 후보를 찾는다. 정렬 배열의 하한 탐색(이분 탐색, [algorithm/06](../../algorithm/06-binary-search/2-summary.md))과 같은 모양이다. 브라우저는 여기에 망·캐시 고려를 더할 수 있다(명세상 재량).
- **변환 부호화(손실 압축)**: 블록 → 주파수 변환(DCT 등) → 양자화(정보 버림) → 엔트로피 부호화. 무손실 단계(엔트로피 부호화)는 [algorithm 영역](../../algorithm/curriculum.md)의 33 무손실 압축·34 현대 코덱(미작성)과 이어진다.
- **내용 협상(content negotiation)**: 서버·CDN이 `Accept: image/avif,image/webp,…` 헤더를 보고 포맷을 고르는 방식. 같은 URL이 다른 바이트를 내므로 캐시 키에 `Accept`를 넣어야 한다(`Vary: Accept`, [network/34 HTTP 캐시](../../network/34-http-caching/2-summary.md)).
- **교차 판정(lazy)**: 뷰포트를 임계 거리만큼 넓힌 사각형과 이미지 사각형의 교차 검사 — IntersectionObserver의 `rootMargin`과 같은 구조.

## 적용 — 풀어나가는 법

### 1. 순서

```text
  ① LCP 요소가 이미지인지 확인(08번 attribution) → 히어로는 eager + 필요 시 fetchpriority=high, 늦게 발견되면 preload
  ② 이미지마다 width/height(또는 aspect-ratio) → CLS 제거
  ③ 크기 후보 만들기(빌드·이미지 CDN) + srcset/sizes → 휴대폰에 원본을 보내지 않기
  ④ 포맷: <picture>로 AVIF → WebP → JPEG, 또는 CDN 내용 협상(+ Vary: Accept)
  ⑤ 첫 화면 아래는 loading=lazy
```

### 2. 빌드 단계에서 후보 만들기 (Node, sharp)

```ts
import sharp from 'sharp';

const WIDTHS = [400, 800, 1600, 2400];
export async function buildVariants(src: string, outBase: string) {
  for (const w of WIDTHS) {
    const img = sharp(src).resize({ width: w, withoutEnlargement: true }); // 원본보다 키우지 않는다
    await img.clone().avif({ quality: 50 }).toFile(`${outBase}-${w}.avif`);
    await img.clone().webp({ quality: 75 }).toFile(`${outBase}-${w}.webp`);
    await img.clone().jpeg({ quality: 75, mozjpeg: true }).toFile(`${outBase}-${w}.jpg`);
  }
}
```

### 3. 마크업

```html
<!-- 히어로: 첫 화면 LCP 후보 -->
<picture>
  <source type="image/avif" srcset="/p/hero-800.avif 800w, /p/hero-1600.avif 1600w, /p/hero-2400.avif 2400w" sizes="100vw">
  <source type="image/webp" srcset="/p/hero-800.webp 800w, /p/hero-1600.webp 1600w, /p/hero-2400.webp 2400w" sizes="100vw">
  <img src="/p/hero-1600.jpg" srcset="/p/hero-800.jpg 800w, /p/hero-1600.jpg 1600w, /p/hero-2400.jpg 2400w" sizes="100vw"
       width="1600" height="900" style="width:100%;height:auto" fetchpriority="high" alt="가을 신상품">
</picture>

<!-- 목록 썸네일: 첫 화면 아래 -->
<img src="/p/item-400.jpg" srcset="/p/item-400.jpg 400w, /p/item-800.jpg 800w"
     sizes="(min-width: 800px) 25vw, 50vw" width="400" height="400" loading="lazy" alt="…">
```

- `sizes`는 CSS 레이아웃과 맞춰야 한다. 실제 슬롯이 25vw인데 `sizes`를 생략(100vw)하면 4배 큰 후보를 받는다.
- 원본 비율이 다른 후보(아트 디렉션)는 `<source media>`로 나누고, 각 source에도 `width`/`height`를 줄 수 있다.

### 4. 확인

- DevTools Network: 이미지 행의 크기·`Priority`, Elements에서 `img.currentSrc`.
- Lighthouse 진단: "적절한 크기의 이미지 사용", "차세대 형식으로 이미지 제공", "LCP 이미지 지연 로딩 안 함" 류 항목.
- 위 실험처럼 뷰포트·DPR(`deviceScaleFactor`)을 바꿔 가며 어떤 파일이 나가는지 자동 점검한다.

## 장애 시나리오와 대처

### 1. 4000px 원본을 휴대폰에 그대로 보냄 (⚠)

- 현상: 모바일 데이터 사용량이 크고 LCP가 느리다.
- 보이는 형태: Network에서 화면 폭 400px 기기가 수 MB 이미지를 받는다. 실험: `src`만 둔 페이지가 DPR 2 휴대폰에 154KB(3840w)를 보냄 — 800w면 14KB. 필드 LCP p75 악화.
- 원인: 크기 후보가 없거나, `sizes`가 실제 슬롯보다 크다.
- 대처: 빌드·이미지 CDN에서 폭별 후보를 만들고 `srcset`+`sizes`. 레이아웃이 바뀌면 `sizes`도 갱신한다.

### 2. 크기 미지정 이미지 → 로드 후 레이아웃 이동 (⚠)

- 현상: 이미지가 뜨면서 아래 버튼이 밀려 잘못 누른다.
- 보이는 형태: `layout-shift` 항목의 `sources`에 이미지 아래 요소. 실험 CLS 0.22(> 0.1, "개선 필요").
- 원인: 속성·CSS로 비율을 모르면 로드 전 높이가 0이다.
- 대처: `width`/`height` 속성 + CSS `height:auto`, 또는 `aspect-ratio`. 반응형에서 `height:auto`를 빼먹으면 그림이 늘어난다(실험: 225px → 450px).

### 3. 모든 이미지에 lazy → 히어로 LCP 지연 (⚠)

- 현상: "lazy 일괄 적용" 배포 뒤 LCP가 크게 늘었다.
- 보이는 형태: 히어로 요청의 Initiator·시작 시각이 레이아웃 뒤, 우선순위 Low로 시작. 실험: LCP 1.47초 → 5.4초, 서버 도착 0.19초 → 4.9초.
- 원인: lazy는 레이아웃 뒤에 거리를 판정하고 요청한다. 그동안 다른 이미지가 연결·대역폭을 차지한다(HTTP/1.1에서는 호스트당 연결 6개).
- 대처: 첫 화면 이미지는 lazy를 빼고(기본 eager), 필요하면 `fetchpriority=high`. CMS·컴포넌트에 "첫 N개는 eager" 규칙을 넣는다.

### 4. CDN 포맷 협상 + 캐시 키 누락 → 깨진 이미지

- 현상: 일부 사용자에게 이미지가 깨져 보인다.
- 보이는 형태: AVIF를 해독 못 하는 클라이언트가 `Content-Type: image/avif` 응답을 받는다. 같은 URL의 응답이 요청 헤더에 따라 다르다.
- 원인: CDN이 `Accept`를 보고 포맷을 바꿔 주는데, 캐시 키에 `Accept`가 없어(`Vary: Accept` 누락) 먼저 캐시된 AVIF를 모두에게 준다.
- 대처: `Vary: Accept` 또는 CDN의 포맷별 캐시 키 설정. 마크업 쪽 `<picture type>` 폴백은 브라우저가 고르므로 이 문제가 없다.

## 핵심 문장

- 이미지 최적화의 첫째는 맞는 크기다. 같은 JPEG에서 3840w → 800w가 1/11, 포맷 교체(JPEG → AVIF, 이 사진)가 약 1/3이었다.
- `srcset`의 `w`는 파일 폭, `sizes`는 레이아웃 전에 알려 주는 슬롯 폭이다. 브라우저는 슬롯 폭 × DPR에 맞는 후보를 고른다.
- `<picture>`는 지원하는 첫 `type`을 쓰므로 AVIF → WebP → JPEG 순서로 두면 미지원 브라우저도 안전하다.
- `width`/`height` 속성은 `aspect-ratio` 힌트가 되어 자리를 미리 잡는다. CSS `width:100%`와 함께 `height:auto`를 둔다.
- `loading=lazy`는 첫 화면 아래에만 쓴다. 히어로에 걸면 요청이 레이아웃 뒤로 밀리고 연결 경쟁에서 진다.

## 관련 주제·근거

- 선행
  - [13 크리티컬 패스와 자원 로딩](../13-critical-path-and-resource-loading/2-summary.md) — 우선순위, preload, fetchpriority
  - [08 Web Vitals](../08-web-performance-vitals/2-summary.md) — LCP·CLS 정의와 측정
- 후속·연결
  - [15 웹 폰트 로딩](../15-web-font-loading/2-summary.md), [17 목록 가상화](../17-list-virtualization/2-summary.md), [20 성능 예산](../20-performance-budgets-and-regression-gates/2-summary.md)
  - [network/34 HTTP 캐시](../../network/34-http-caching/2-summary.md)(Vary), [network/39 콘텐츠 인코딩](../../network/39-http-content-encoding/2-summary.md)(이미지는 이미 압축되어 있다 — 1600w JPEG 39,300B에 gzip −2.3%·brotli −3.7%, AVIF 12,913B에 −0.4%, `out14gzip.txt`), [network/47 CDN과 엣지](../../network/47-cdn-and-edge/2-summary.md)
  - [algorithm/06 이분 탐색](../../algorithm/06-binary-search/2-summary.md), [algorithm 영역](../../algorithm/curriculum.md)(33 무손실 압축·34 현대 코덱 — 미작성)
- 문법·API: [html/34 img 크기와 로딩](../../../languages/html/syntax/34-img-alt-size-and-loading/2-summary.md), [html/35 srcset·sizes](../../../languages/html/syntax/35-srcset-and-sizes/2-summary.md), [html/36 picture](../../../languages/html/syntax/36-picture-art-direction-and-format/2-summary.md), [css/31 aspect-ratio](../../../languages/css/syntax/31-intrinsic-sizing-and-aspect-ratio/2-summary.md), [css/44 배경과 object-fit](../../../languages/css/syntax/44-backgrounds-and-object-fit/2-summary.md), [web-api/35 IntersectionObserver](../../../languages/web-api/35-intersection-observer/2-summary.md)
- 근거
  - HTML 표준 "Images" https://html.spec.whatwg.org/multipage/images.html — source set 선택의 구현 재량(implementation-defined), `sizes`의 `auto`(lazy 이미지 한정)
  - HTML 표준 "Rendering" https://html.spec.whatwg.org/multipage/rendering.html — `img`의 `width`·`height` → `aspect-ratio` 표현 힌트
  - HTML 표준 "Lazy loading attributes" https://html.spec.whatwg.org/multipage/urls-and-fetching.html — 스크립트 꺼짐이면 lazy 안 함(반추적)
  - web.dev "Browser-level image lazy loading for the web" https://web.dev/articles/browser-level-image-lazy-loading — 1250px/2500px, 0×0, 첫 화면 lazy 금지
  - Chromium `third_party/blink/renderer/core/frame/settings.json5`(main, 2026-10-04 조회) — `lazyLoadingImageMarginPx4G` 1250 · `3G` 2500 · `2G` 6000 · `Slow2G`·`Offline` 8000 · `Unknown` 3000
  - web.dev "Optimize Cumulative Layout Shift" https://web.dev/articles/optimize-cls — `width`/`height`·`aspect-ratio`
  - web.dev "Optimize LCP" https://web.dev/articles/optimize-lcp · "Fetch Priority" https://web.dev/articles/fetch-priority
  - web.dev learn/design "Responsive images" https://web.dev/learn/design/responsive-images · "Preload responsive images" https://web.dev/articles/preload-responsive-images
  - Google "WebP" https://developers.google.com/speed/webp — VP8 키프레임 예측 부호화, JPEG 대비 25~34%
  - AOMedia "AV1 Image File Format (AVIF)" https://aomediacodec.github.io/av1-avif/ · ITU-T T.81(JPEG, DCT)
  - Chromium `net/socket/client_socket_pool_manager.cc` — 호스트당 연결 6
- 실험 목록 (headless Chrome 151.0.7922.173, Node 20.19.6 + playwright-core 1.62.1 + sharp 0.33.5, 127.0.0.1 HTTP/1.1 로컬 서버, 2026-10-04)
  - 14-A 포맷 크기·srcset 선택·picture·히어로 lazy/eager/high·CLS: `scratchpad/wp/08/exp14_images.js` — 출력 `out14.txt`
  - 14-B 포맷·품질별 크기와 PSNR: `scratchpad/wp/08/exp14_psnr.js` — 출력 `out14psnr.txt`
  - 14-C 이미 압축된 이미지에 gzip·brotli: Node `zlib` 한 줄(출력 `out14gzip.txt`)
  - 입력 사진: `/usr/share/backgrounds/Clouds_by_Tibor_Mokanszki.jpg`(3840×2160, Ubuntu 배경)
