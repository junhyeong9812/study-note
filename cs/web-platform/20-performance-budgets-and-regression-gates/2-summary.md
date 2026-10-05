# web-platform/20-performance-budgets-and-regression-gates — 성능 예산·랩 측정·CI 회귀 게이트·노이즈 — 정리 (힌트)

## 해결하는 문제

성능은 한 번에 무너지지 않는다. 작은 변경이 쌓여 조금씩 나빠진다.

```text
  주차      변경                         번들(gzip)   LCP(랩)
  1주   기준                              0.2 KB     ~480 ms
  2주   + 디바운스 쓰려고 lodash 전체 import  26.3 KB     ~870 ms   ← 아무도 리뷰에서 못 봄
  3주   + 날짜 라이브러리                    ...        ...
  ...
  6개월 "왜 이렇게 느려졌지?" — 범인을 찾을 커밋이 수백 개
```

- 위 1·2주 수치는 아래 실험의 실측이다(headless Chrome 151, CPU 4×, 1.6 Mbps·150 ms). 3주 이후는 (예시).
- 해법: 숫자로 된 한계(**성능 예산**)를 정하고, 변경마다 자동으로 재서 넘으면 머지를 막는다(**회귀 게이트**).
  - *성능 예산(performance budget)*: 팀이 넘지 않기로 정한 성능 지표의 한계값. 예: "첫 화면 JS 170 KB 이하", "랩 LCP 2.5 s 이하".
  - *회귀 게이트(regression gate)*: CI에서 측정값을 예산·기준선과 비교해, 넘으면 빌드를 실패시키는 단계.
  - *랩(lab) 측정*: 고정된 기기·네트워크 조건에서 스크립트로 재는 것. Lighthouse·WebPageTest·이 노트의 측정 스크립트.

쉬운 예: 가계부의 월 식비 예산이다. 한 끼 외식은 티가 안 나지만, 예산표가 있으면 "이번 달 초과"가 바로 보인다.

똑같은 구조다.\
의존성 하나·이미지 하나는 티가 안 난다. 예산과 게이트가 "이번 PR이 초과"를 바로 보여 준다.

실무 예:
- 날짜 포맷 하나 쓰려고 큰 라이브러리를 추가했는데 번들이 수백 KB 늘어난 것을 배포 몇 주 뒤에야 안다(커리큘럼 ⚠).
- Lighthouse 점수 게이트를 걸었더니 같은 코드에서도 실행마다 점수가 흔들려 오탐이 나고, 팀이 게이트를 꺼 버린다.

## 동작·원리

### 1. 예산의 세 종류

web.dev "Performance budgets 101"의 분류다.

```text
  ┌────────────────────┬───────────────────────────────┬───────────────────────┐
  │ 종류                │ 예                            │ 측정 노이즈             │
  ├────────────────────┼───────────────────────────────┼───────────────────────┤
  │ 양(quantity)        │ JS·이미지·폰트 KB, 요청 수        │ 작음(빌드 산출물은 결정적)  │
  │ 시점(milestone)     │ FCP·LCP·TTI, TBT               │ 큼(실행마다 흔들림)       │
  │ 규칙(rule-based)    │ Lighthouse 성능 점수            │ 큼(지표 점수의 가중 평균)   │
  └────────────────────┴───────────────────────────────┴───────────────────────┘
```

- 같은 글의 출발 기준: 3G·기준 모바일 기기에서 "TTI 5 s 미만", "크리티컬 경로 자원 170 KB 미만(압축·축소 후)".
- 양 예산은 빌드 결과물만 보면 되므로 빠르고 흔들리지 않는다. 시점 예산은 사용자 경험에 가깝지만 흔들린다. 둘을 같이 쓴다(해석).
- Lighthouse 10+ 성능 점수 가중치: FCP 10%, Speed Index 10%, LCP 25%, TBT 30%, CLS 25%(Chrome for Developers "Lighthouse performance scoring"). 각 지표의 원시값을 먼저 0~100 점수로 바꾼 뒤 가중 평균한다. CLS는 시점이 아니라 이동량 지표다.
- 빌드 산출물 크기는 같은 코드면 같다. 페이지의 요청 목록·전송량은 광고·A/B 테스트 같은 비결정 콘텐츠가 있으면 같은 코드에서도 달라질 수 있다(Lighthouse variability 문서의 "페이지 비결정성"). 아래 실험의 "9회 모두 같음"은 그런 요소가 없는 고정 페이지의 결과다.

### 2. 게이트의 위치 — 빌드 → 랩 → 현장

```text
  PR ──> [빌드]  번들 크기 비교 ─────────── 결정적, 수 초       ── 초과 → 실패
            │      (webpack performance.hints, esbuild metafile, 크기 비교 스크립트)
            ▼
         [랩]    고정 조건 N회 측정 → 중앙값 ── 흔들림, 수십 초~분 ── 초과 → 실패/경고
            │      (Lighthouse CI, 측정 스크립트)
            ▼
       배포 ──> [현장(RUM·CrUX)]  p75 LCP·INP·CLS ── 실제 사용자, 일·주 단위 ── 알람
```

- 현장 지표의 "좋음" 기준: LCP 2.5 s 이하, INP 200 ms 이하, CLS 0.1 이하, 모바일·데스크톱을 나눈 75번째 백분위(web.dev "Web Vitals").
- 랩 게이트는 "같은 조건에서 이전보다 나빠졌나"를 본다. 현장 지표는 "실제 사용자가 괜찮나"를 본다. 랩 통과가 현장 통과를 뜻하지 않는다(08번).

### 3. 노이즈 — 같은 코드를 재도 값이 다르다

```text
  같은 페이지 LCP 15회 (실험)
  452 ─────●──●●●●●●●●●●●────●─ 524 ms     폭 72 ms
          ↑ 기준 중앙값 484        한계 = 484 × 1.05 = 508
  단일 실행 비교: 15번 중 3번이 "회귀"   ← 코드는 똑같다 = 오탐 (재실행에서는 1번)
  5회 중앙값 비교: 3묶음 중 0번          (재실행도 0번)
```

- Lighthouse variability 문서가 꼽는 노이즈 원천: 페이지 비결정성(A/B 테스트·광고), 로컬 네트워크, 원격 네트워크, 웹 서버 응답 시간, 클라이언트 하드웨어, **클라이언트 자원 경합**, 브라우저 비결정성.
- 같은 문서: "5회 실행의 Lighthouse 점수 중앙값은 1회보다 두 배 안정적이다"(대상은 성능 점수다. LCP 같은 개별 지표나 별도 측정 스크립트에 같은 배율이 보장되지는 않는다). 전용 코어 2개 이상(권장 4)·메모리 2 GB 이상(권장 4~8)을 권하고, 같은 기계에서 여러 리포트를 **동시에** 수집하지 말라고 한다.
- Lighthouse CI의 `collect.numberOfRuns` 기본값은 3이다. 단언(assert)은 여러 실행을 `median`·`optimistic`·`pessimistic`·`median-run` 중 하나로 모은다. 옵션을 주지 않은 단언의 기본은 `{"aggregationMethod": "optimistic", "minScore": 1}`이다 — `optimistic`은 "가장 통과하기 쉬운 값"이라, 회귀 게이트로 쓰려면 `median`을 명시한다.

### 실험: 의존성 추가 → 예산 초과를 게이트가 잡는다

환경: esbuild 0.28.1(번들·축소), lodash 4.17.23, lodash-es 4.18.1, Node 20.19, 2026-10-04.

```js
// src/base.js        — 직접 쓴 debounce 6줄
// src/full-lodash.js — import _ from 'lodash';            _.debounce(...)
// src/es-lodash.js   — import { debounce } from 'lodash-es'; debounce(...)
const r = await esbuild.build({ entryPoints: [`src/${name}.js`], bundle: true, minify: true,
                                format: 'iife', write: false, metafile: true });
const code = r.outputFiles[0].contents;
console.log(code.length, zlib.gzipSync(code, { level: 9 }).length, zlib.brotliCompressSync(code).length);
```

(실험, esbuild 0.28.1, 2026-10-04)

```text
base         min=0.2KB gzip=0.2KB br=0.1KB inputs=1
full-lodash  min=72.3KB gzip=26.3KB br=23.3KB inputs=2
es-lodash    min=3.0KB gzip=1.5KB br=1.3KB inputs=641
```

- `lodash`(CommonJS 한 파일)는 함수 하나만 써도 전체가 들어온다. `lodash-es`(ES 모듈)는 641개 입력 파일을 거쳤지만 트리 셰이킹으로 `debounce`와 의존 함수만 남아 3.0 KB다([09-js-modules-and-bundling](../09-js-modules-and-bundling/2-summary.md)).
- 같은 기능에 축소 크기 0.2 → 72.3 → 3.0 KB. 리뷰 diff에는 `import` 한 줄 차이다.

이어서 세 번들을 페이지 `<head>`의 동기 `<script>`로 넣고 랩 조건에서 9회씩 쟀다.

```js
// measure.js 핵심 — 실행마다 새 컨텍스트(캐시 없음), 같은 조건
await cdp.send('Network.emulateNetworkConditions', { offline: false, latency: 150,
  downloadThroughput: 1.6 * 1024 * 1024 / 8, uploadThroughput: 750 * 1024 / 8 });
await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 });
// addInitScript: PerformanceObserver로 'largest-contentful-paint'의 마지막 startTime,
//                'longtask' 각 항목의 (duration - 50) 합(= TBT 근사. 단 FCP 이전 태스크까지 합산한다)
// CDP Network.loadingFinished의 encodedDataLength 합(favicon 제외) = 전송 KB, 개수 = 요청 수
await page.goto(url, { waitUntil: 'load' }); await page.waitForTimeout(300);

// gate.js 핵심 — 지표마다 N회 중앙값을 예산과 비교, 하나라도 넘으면 exit 1
const budget = { lcp: 800, tbt: 100, kb: 20, reqs: 3 };   // (예시) 이 랩 조건 전용 값
```

(실험, headless Chrome 151.0.7922.173, CPU 4× 스로틀, 네트워크 150 ms·1.6 Mbps 다운·750 Kbps 업, 뷰포트 412×823, 로컬 서버 127.0.0.1 gzip 전송, 24코어 호스트, 2026-10-04)

```text
lcp  median=480 min=468 max=556 budget<=800 PASS
tbt  median=0 min=0 max=64 budget<=100 PASS
kb   median=3 min=3 max=3 budget<=20 PASS
reqs median=2 min=2 max=2 budget<=3 PASS
variant=base runs=9 → GATE PASS
exit=0
lcp  median=872 min=812 max=960 budget<=800 FAIL
tbt  median=216 min=176 max=277 budget<=100 FAIL
kb   median=29.1 min=29.1 max=29.1 budget<=20 FAIL
reqs median=2 min=2 max=2 budget<=3 PASS
variant=full-lodash runs=9 → GATE FAIL (exit 1)
exit=1
lcp  median=504 min=480 max=540 budget<=800 PASS
tbt  median=0 min=0 max=0 budget<=100 PASS
kb   median=4.3 min=4.3 max=4.3 budget<=20 PASS
reqs median=2 min=2 max=2 budget<=3 PASS
variant=es-lodash runs=9 → GATE PASS
exit=0
```

관찰과 해석
- 전송 KB와 요청 수는 9회 모두 같았다(min = max). 시간 지표(LCP·TBT)는 같은 코드에서도 수십~200 ms 폭으로 흔들렸다(재실행 포함).
- 사실 점검 재실행(같은 코드·조건, 다른 작업자의 브라우저가 동시에 돌아 호스트 load average ~16): base LCP 중앙값 504(444~656), full-lodash 872(800~992)·TBT 208(158~289), es-lodash 540(488~576) ms. KB·요청 수는 같았고 세 게이트 판정(PASS·FAIL·PASS)도 같았다. 시간 수치는 실행마다 수십 ms 달라진다.
- lodash 전체를 동기 스크립트로 넣자 LCP 중앙값이 480 → 872 ms, TBT 근사가 0 → 216 ms로 늘었다(이 스크립트는 첫 렌더 전에 실행되므로, FCP 이후만 세는 실제 TBT 정의(web.dev)로는 이 값만큼 늘었다고 단정할 수 없다 — 216 ms는 이 스크립트의 긴 태스크 비용이다). 4× CPU에서 72 KB 스크립트의 파싱·실행이 긴 태스크가 됐고, 동기 스크립트라 그동안 첫 렌더가 막혔다([13-critical-path-and-resource-loading](../13-critical-path-and-resource-loading/2-summary.md)).
- 이 수치는 이 호스트·이 조건의 랩 값이다. 실사용자 LCP와 같은 값이 아니다.
- 처음 측정 스크립트는 요청 수가 실행마다 2·3으로 흔들렸다. 로드 완료 시점과 경합하는 `favicon.ico` 요청이 섞인 탓이었고, 걸러 낸 뒤 2로 고정됐다. "결정적인 지표"도 측정 방법이 흔들림을 들여올 수 있다.

### 실험: A/A 비교 — 같은 코드를 게이트에 넣으면 몇 번 실패하나

같은 `base`를 15회씩 두 묶음(A, A2), 그리고 바쁜 루프 Node 프로세스 2개를 함께 돌리며 15회(noisy) 쟀다. A의 중앙값을 기준선으로 A2·noisy를 "기준 대비 +5%·+10%" 상대 게이트에 넣었다.

```js
// aa.js 핵심
const base = med(a);
const single = b.filter(x => x > base * tol).length;               // 1회씩 비교
const groups = chunk(b, 5).map(med).filter(x => x > base * tol);   // 5회 중앙값끼리 비교
```

(실험, 위와 같은 조건, 2026-10-04)

```text
A      n=15 min=452 median=484 max=524 spread=72ms  [508,452,480,496,500,504,492,472,480,484,480,468,460,524,484]
A2     n=15 min=464 median=484 max=544 spread=80ms  [544,512,464,468,476,496,472,484,472,504,476,492,492,476,512]
noisy  n=15 min=476 median=500 max=544 spread=68ms  [524,484,476,504,516,480,500,500,520,496,544,480,520,484,484]
허용 5% (기준 중앙값 484 → 한계 508ms): 단일 실행 오탐 3/15, 5회 중앙값 오탐 0/3 [476,484,492], 부하 러너 단일 오탐 5/15, 부하 러너 5회 중앙값 오탐 0/3 [504,500,484]
허용 10% (기준 중앙값 484 → 한계 532ms): 단일 실행 오탐 1/15, 5회 중앙값 오탐 0/3 [476,484,492], 부하 러너 단일 오탐 1/15, 부하 러너 5회 중앙값 오탐 0/3 [504,500,484]
```

관찰과 해석
- 코드가 같은데도 단일 실행 + 5% 허용 게이트는 15번 중 3번(부하 시 5번) "회귀"를 외쳤다. 사실 점검 재실행에서는 1번(기준 중앙값 500, A2에 728 ms 튀는 값 1개)이었다. 오탐 횟수 자체가 실행마다 흔들린다. 이런 게이트가 몇 번 틀리면 팀은 게이트를 무시하거나 끈다(커리큘럼 ⚠, 해석).
- 5회 중앙값끼리 비교하면 이 실험에서는 오탐 0이었다. 대신 실행 시간이 5배다.
- 바쁜 프로세스 2개를 함께 돌린 묶음의 중앙값은 집필 실행에서 500 ms(기준 484), 재실행에서 496 ms(기준 500)였다. 24코어 호스트에서는 바쁜 프로세스 2개의 영향이 실행 간 노이즈에 묻혀 방향이 일정하지 않았다(해석). 코어가 적은 공유 CI 러너에서는 영향이 더 클 수 있다(이 실험에서는 확인하지 않음 `[?]`).
- 허용 폭은 "측정 폭보다 크고, 잡고 싶은 회귀보다 작게" 잡는다. 이 실험에서 실제 회귀(lodash, +390 ms)는 노이즈 폭(집필 실행 70~80 ms, 재실행 96~264 ms — 튀는 값 1개 포함)보다 커서 어느 설정으로도 잡혔다.

## 쓰이는 자료구조·알고리즘

- **임계값 비교** — `측정값 ≤ 예산`(고정값) 또는 `측정값 ≤ 기준선 × (1 + 허용)`(상대값). 고정값 예산은 목표를, 상대 예산은 "나빠지지 않기"를 지킨다.
- **중앙값(반복 측정의 대푯값)** — 평균은 튀는 값 하나에 끌려가고 중앙값은 덜 끌려간다. N개를 정렬해 가운데를 고르거나 선택 알고리즘(quickselect, 평균 O(N))으로 구한다. [algorithm/03-quick-sort](../../algorithm/03-quick-sort/2-summary.md), [data-analysis/04-descriptive-statistics](../../data-analysis/README.md)(미작성, 영역 표)
- **백분위(p75) 집계** — 현장 지표는 페이지 조회(page views)의 75번째 백분위로 판정한다(사용자 수 기준이 아니다). 스트림에서 근사 백분위를 구하려면 히스토그램·스케치를 쓴다. [data-structure/19-probabilistic-counting](../../data-structure/19-probabilistic-counting/2-summary.md)
- **모듈 의존 그래프와 도달성** — 번들 크기는 진입점에서 도달 가능한 모듈의 합이다. 트리 셰이킹은 쓰지 않는 export를 그래프에서 잘라 낸다. esbuild `metafile`이 입력별 기여 바이트를 준다. [data-structure/08-graph](../../data-structure/08-graph/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 예산을 정한다

1. 현장 데이터(CrUX·RUM)에서 지금의 p75 LCP·INP·CLS를 본다.
2. 목표: Core Web Vitals "좋음"(LCP 2.5 s·INP 200 ms·CLS 0.1). 경쟁 서비스·과거 최고치도 참고한다.
3. 시점 목표를 양 예산으로 번역한다. 예: "느린 모바일(3G·기준 기기)에서 TTI 5 s 미만 → 크리티컬 경로 자원 170 KB(압축·축소) 이하"(web.dev "Performance budgets 101"의 기본값). LCP 2.5 s 같은 다른 시점 목표라면 양 예산은 자기 측정으로 다시 정한다.
4. 랩 예산은 **고정한 랩 조건 전용**으로 기준선을 재서 정한다. 다른 조건의 수치와 비교하지 않는다.

### 2. 빌드 단계 — 결정적인 양 예산부터

```js
// webpack: 기본은 production에서 'warning', 한계 250000 바이트(자산·진입점)
module.exports = { performance: { hints: 'error', maxAssetSize: 170_000, maxEntrypointSize: 170_000 } };
```

```js
// 번들러 무관: 빌드 산출물 gzip 크기를 예산과 비교
const fs = require('fs'), zlib = require('zlib');
const budgetKB = { 'dist/app.js': 170 };   // (예시)
let fail = false;
for (const [f, kb] of Object.entries(budgetKB)) {
  const gz = zlib.gzipSync(fs.readFileSync(f)).length / 1024;
  console.log(`${f} ${gz.toFixed(1)}KB / ${kb}KB`);
  if (gz > kb) fail = true;
}
process.exit(fail ? 1 : 0);
```

- 초과하면 esbuild `metafile`(또는 번들 분석기)로 어느 입력이 몇 바이트를 차지하는지 본다. 실험처럼 `import _ from 'lodash'` 한 줄이 원인인 경우가 많다(해석).
- PR 코멘트에 "기준 브랜치 대비 +N KB"를 남기면 리뷰어가 숫자를 본다.

### 3. 랩 단계 — 노이즈를 다스린다

- 조건 고정: 같은 Chrome 판, CPU·네트워크 스로틀, 뷰포트, 캐시 없음, 로컬·스테이징의 고정 데이터.
- 반복 + 중앙값: Lighthouse CI는 `numberOfRuns`(기본 3)를 늘리고 `aggregationMethod: 'median'`을 쓴다.
- 직렬 실행: 같은 기계에서 측정을 동시에 돌리지 않는다(Lighthouse variability 문서).
- 허용 폭: A/A 실험(같은 코드 두 번)으로 노이즈 폭을 먼저 재고, 그보다 넓게 잡는다.
- 단계 도입: 처음에는 `warn`(경고만), 오탐률을 확인한 뒤 `error`(실패)로 올린다. Lighthouse CI 단언 수준은 `off`·`warn`·`error`다.

```json
{
  "ci": {
    "collect": { "numberOfRuns": 5 },
    "assert": {
      "assertions": {
        "largest-contentful-paint": ["error", { "maxNumericValue": 2500, "aggregationMethod": "median" }],
        "resource-summary:script:size": ["error", { "maxNumericValue": 174080 }],
        "resource-summary:font:count": ["warn", { "maxNumericValue": 1 }]
      }
    }
  }
}
```

- 위 설정은 Lighthouse CI configuration 문서의 형식(`maxNumericValue`·`aggregationMethod`·`resource-summary:<종류>:<size|count>`)을 따른 예시다. 수치는 (예시).

### 4. 현장 단계 — 게이트가 아니라 알람

- RUM(`web-vitals` 라이브러리·PerformanceObserver)으로 p75를 모으고, 배포 단위로 비교해 나빠지면 알린다.
- 랩 게이트를 통과했는데 현장이 나빠지면, 원인 후보는 여럿이다. 랩 조건이 실제 사용자 기기·네트워크를 대표하지 못함, 로그인·개인화 콘텐츠, 캐시 상태, 사용자 행동, 현장 데이터의 집계 기간(CrUX는 28일) 등(web.dev "Why lab and field data can be different"). 원인을 확인한 뒤 랩 조건을 실제 분포에 맞춘다.

## 장애 시나리오와 대처

### 1. 의존성 하나로 번들이 수십~수백 KB 증가 — 아무도 모름

- **현상**: 몇 주 뒤 저사양 기기에서 첫 화면이 느리다는 신고. 현장 p75 LCP 상승.
- **보이는 형태**: 번들 크기 추이 그래프의 계단. 실험에서 `import _ from 'lodash'` 한 줄로 gzip 0.2 → 26.3 KB, 랩 LCP 480 → 872 ms.
- **원인**: 크기 예산·게이트가 없거나, 리뷰가 코드 diff만 보고 번들 diff를 보지 않았다.
- **대처**: 빌드 단계 양 예산(결정적이라 오탐이 거의 없다)을 먼저 건다. 초과 시 metafile로 기여 모듈을 찾고 ES 모듈판·개별 import·직접 구현으로 바꾼다(실험: 3.0 KB).

### 2. 점수가 흔들려 게이트가 오탐 → 결국 꺼 둠

- **현상**: 코드와 무관한 PR(문서 수정)에서 성능 게이트가 실패한다. 재실행하면 통과한다. 몇 주 뒤 누군가 게이트를 비활성화한다.
- **보이는 형태**: 같은 커밋의 Lighthouse 점수·LCP가 실행마다 다름. 실험 A/A에서 단일 실행 + 5% 허용이 15번 중 3번(재실행 1번) 오탐.
- **원인**: 단일 실행, 좁은 허용 폭, 공유 러너의 자원 경합, 동시 측정.
- **대처**: 반복 측정 중앙값(Lighthouse 문서: 5회 점수 중앙값이 1회보다 두 배 안정), 전용·고정 러너, 직렬 실행, A/A로 잰 노이즈보다 넓은 허용 폭, 결정적 지표(KB·요청 수)는 엄격히·시간 지표는 느슨히. 게이트를 끄기 전에 `warn`으로 내린다.

### 3. 도구 판이 바뀌어 게이트가 조용히 아무것도 검사하지 않음

- **현상**: 예산을 크게 넘는 변경이 게이트를 통과한다.
- **보이는 형태**: CI 로그에 실패도 경고도 없다. 단언 결과가 0개.
- **원인**: Lighthouse 12.0.0 릴리스 노트의 breaking change 목록에 "remove budgets (#15950)"이 있다. 옛 `budgets`/`budgetPath` 설정과 `performance-budget` 단언에 기대던 게이트는 도구를 올린 뒤 읽는 쪽이 사라진다. 실제로 그렇게 게이트가 아무것도 강제하지 않게 된 사례가 공개 PR에 보고됐다(아래 근거 링크).
- **대처**: `resource-summary:*` 단언 같은 지원되는 방식으로 옮긴다. 게이트 자체를 테스트한다 — 일부러 예산을 넘는 고정 페이지(카나리)를 두고 게이트가 실패하는지 주기적으로 확인한다(실험의 `full-lodash`가 그런 역할).

### 4. 랩은 통과, 현장은 나쁨

- **현상**: CI 게이트는 초록인데 CrUX p75 LCP·INP가 "개선 필요".
- **보이는 형태**: 랩 LCP 1 s대, 현장 p75 3 s대(예시).
- **원인**: 랩 조건이 실제 사용자 기기·네트워크보다 좋다. 로그인 상태·개인화·광고·서드파티 스크립트가 랩 페이지에 없다. INP는 상호작용이 있어야 나오므로 페이지 로드 랩 측정에 잡히지 않는다(랩에서는 TBT로 대신 본다).
- **대처**: 랩 조건을 현장 분포(기기 등급·RTT)에 맞추고, 실제 사용자 흐름(로그인 뒤 화면)을 랩 시나리오에 넣는다. 현장 p75 알람을 함께 둔다.

## 핵심 문장

- 성능 예산은 팀이 넘지 않기로 한 숫자이고, 회귀 게이트는 변경마다 그 숫자를 재서 넘으면 머지를 막는 CI 단계다.
- 양 예산(KB·요청 수)은 빌드 산출물 기준이면 결정적이라 엄격히 걸 수 있다(요청 수는 비결정 콘텐츠가 없을 때). 시점 예산(LCP·TBT)은 실행마다 흔들리므로 반복 측정의 중앙값과 넓은 허용 폭이 필요하다.
- 실험에서 `import _ from 'lodash'` 한 줄이 gzip 번들을 0.2 → 26.3 KB, 랩 LCP 중앙값을 480 → 872 ms로 늘렸고, 게이트가 exit 1로 잡았다.
- 같은 코드를 단일 실행 + 5% 허용으로 비교하면 15번 중 3번(재실행 1번) 오탐이 났다. 5회 중앙값끼리는 두 실행 모두 0번이었다.
- 랩 게이트는 "나빠졌나"를, 현장 p75는 "사용자가 괜찮나"를 본다. 둘은 서로를 대신하지 않는다.
- 게이트도 코드다. 도구 판 변경으로 조용히 무력화될 수 있으니, 일부러 실패해야 하는 카나리로 게이트를 시험한다.

## 관련 주제·근거

- 선행
  - [08-web-performance-vitals](../08-web-performance-vitals/2-summary.md) — LCP·INP·CLS, 랩 vs RUM
  - [09-js-modules-and-bundling](../09-js-modules-and-bundling/2-summary.md) — 트리 셰이킹·코드 분할
  - [engineering-practice/06-ci-cd-pipelines](../../engineering-practice/06-ci-cd-pipelines/2-summary.md) — CI 파이프라인
- 후속·연결
  - [13-critical-path-and-resource-loading](../13-critical-path-and-resource-loading/2-summary.md) — 동기 스크립트가 첫 렌더를 막는 이유
  - [16-long-tasks-and-web-workers](../16-long-tasks-and-web-workers/2-summary.md) — TBT·긴 태스크
  - [data-analysis/04-descriptive-statistics](../../data-analysis/README.md) — 중앙값·분위수(미작성, 영역 표)
  - [algorithm/03-quick-sort](../../algorithm/03-quick-sort/2-summary.md), [data-structure/19-probabilistic-counting](../../data-structure/19-probabilistic-counting/2-summary.md), [data-structure/08-graph](../../data-structure/08-graph/2-summary.md)
- 문서
  - web.dev "Performance budgets 101" — 양·시점·규칙 예산, TTI 5 s·170 KB 기준 <https://web.dev/articles/performance-budgets-101>
  - web.dev "Incorporate performance budgets into your build process" <https://web.dev/articles/incorporate-performance-budgets-into-your-build-tools>
  - MDN "Performance budgets" <https://developer.mozilla.org/en-US/docs/Web/Performance/Guides/Performance_budgets>
  - web.dev "Web Vitals" — LCP 2.5 s·INP 200 ms·CLS 0.1, p75 <https://web.dev/articles/vitals>
  - Chrome for Developers "Lighthouse performance scoring" — 가중치, 점수를 분포로 보라 <https://developer.chrome.com/docs/lighthouse/performance/performance-scoring>
  - Lighthouse docs/variability.md — 노이즈 원천 7가지, 5회 점수 중앙값 두 배 안정, 하드웨어·직렬 실행 권고 <https://github.com/GoogleChrome/lighthouse/blob/main/docs/variability.md>
  - Lighthouse docs/throttling.md — 모바일 기본 150 ms·1.6 Mbps/750 Kbps·CPU 4×, simulated vs DevTools 스로틀 <https://github.com/GoogleChrome/lighthouse/blob/main/docs/throttling.md>
  - Lighthouse CI configuration — 단언 수준, `aggregationMethod`, `numberOfRuns` 기본 3, `resource-summary` 단언 <https://github.com/GoogleChrome/lighthouse-ci/blob/main/docs/configuration.md>
  - Lighthouse v12.0.0 릴리스 노트 — "remove budgets (#15950)" <https://github.com/GoogleChrome/lighthouse/releases/tag/v12.0.0>
  - 게이트 무력화 보고 사례(공개 PR, 2차 출처) <https://github.com/ritik4ever/stellar-portfolio-rebalancer/pull/1905>
  - webpack `performance` 설정 — `hints` 기본(production 'warning'), `maxAssetSize`·`maxEntrypointSize` 250000 <https://webpack.js.org/configuration/performance/>
  - esbuild metafile <https://esbuild.github.io/api/#metafile>
- 실험 목록
  - 번들 크기: esbuild 0.28.1 + lodash 4.17.23 / lodash-es 4.18.1, 축소·gzip(level 9)·brotli 크기(Node 20.19 zlib).
  - 예산 게이트: headless Chrome 151.0.7922.173 + playwright-core 1.62.1, CDP 네트워크(150 ms·1.6 Mbps/750 Kbps)·CPU 4× 스로틀, 뷰포트 412×823, 로컬 Node `http` 서버 127.0.0.1(gzip), 변형마다 9회, 중앙값 vs 예산(예시 값).
  - A/A 노이즈: 같은 조건 `base` 15회 × 2 + 바쁜 루프 2개 동시 15회, 상대 허용 5%·10%에서 단일 vs 5회 중앙값 오탐 수.
  - 사실 점검 재실행(2026-10-04): 번들 크기 출력은 같았다. 게이트 판정은 같았고 시간 수치는 범위 안에서 달랐다. A/A 단일 실행 오탐은 3/15 → 1/15, 5회 중앙값 오탐은 0/3으로 같았다. 다른 작업자의 측정이 동시에 돌던 호스트라 시간 수치가 흔들렸을 수 있다.
  - Lighthouse 자체는 scratchpad 설치가 의존성 해석 실패(npm `notarget`)로 되지 않아, 같은 원리의 측정 스크립트로 대신했다. Lighthouse 동작은 위 1차 문서로 근거를 댔다.
