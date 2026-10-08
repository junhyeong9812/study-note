# 프론트엔드 엔지니어링 — `cs/web-platform/` 커리큘럼

> **생성 문서** — `docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md` §16에서 `scripts/notes/gen_area_readme.py`로 만든다. 직접 고치지 말고 커리큘럼을 고친 뒤 재실행한다.
> 번호 = 권장 학습 순서. 상태: `미작성` · `원고 있음` · `초안(Claude)` · `검수 완료`. ⚠ 깨지면·🔧·📚 세부는 커리큘럼 본문에 있다.
> 현황: 미작성 0 · 원고 있음 0 · 초안(Claude) 24 · 검수 완료 0

> 브라우저라는 **실행 환경의 원리**(렌더링 파이프라인·이벤트 루프·출처 모델·저장소·캐시)에서 출발해 **성능 최적화**(로딩 순서·이미지·폰트·긴 태스크·가상화·재렌더·하이드레이션·성능 예산)와 **프론트엔드 설계**(컴포넌트·상태·Islands·마이크로 프론트엔드)까지 다룬다. 특정 프레임워크(React 등)는 원리의 예시로만 든다. DOM API 118파일 레퍼런스(`languages/web-api`)와 프레임워크 API 레퍼런스는 CS 밖(§19) — 여기서 실습 근거로 링크한다. SOP/CORS 본문은 security/21, HTTP 캐시 본문은 network/34, 전송 압축은 network/39.
> 뼈대: WHATWG HTML 표준(Event loops 절·Rendering 절), WHATWG Fetch, web.dev "Rendering performance"·Core Web Vitals·learn/performance, W3C Service Workers, patterns.dev.

## 16.1 원리

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 01 | `browser-architecture` | 멀티 프로세스·사이트 격리·렌더러 | 권장 | 초안(Claude) | [01-browser-architecture](01-browser-architecture/) |
| 02 | `rendering-pipeline` | 파싱 → DOM/CSSOM → 스타일 → 레이아웃 → 페인트 → 합성. 합성 레이어 — transform·opacity만 컴포지터에서 처리, 레이어 과다는 메모리 비용 | 필수 | 초안(Claude) | [02-rendering-pipeline](02-rendering-pipeline/) |
| 03 | `event-loop` | 태스크·마이크로태스크·렌더링 기회·rAF | 필수 | 초안(Claude) | [03-event-loop](03-event-loop/) |
| 04 | `dom-and-event-model` | DOM 트리·이벤트 전파(캡처/버블)·위임 | 필수 | 초안(Claude) | [04-dom-and-event-model](04-dom-and-event-model/) |
| 05 | `fetch-from-browser` | fetch 수명·스트리밍·중단·자격 증명 | 필수 | 초안(Claude) | [05-fetch-from-browser](05-fetch-from-browser/) |
| 06 | `browser-storage` | 쿠키·localStorage·IndexedDB·쿼터·축출 | 권장 | 초안(Claude) | [06-browser-storage](06-browser-storage/) |
| 07 | `service-workers-and-offline` | 서비스 워커 수명·캐시 전략 | 권장 | 초안(Claude) | [07-service-workers-and-offline](07-service-workers-and-offline/) |
| 09 | `js-modules-and-bundling` | 모듈 체계·번들링·코드 분할·트리 셰이킹 | 권장 | 초안(Claude) | [09-js-modules-and-bundling](09-js-modules-and-bundling/) |
| 10 | `rendering-strategies` | CSR·SSR·SSG·스트리밍·하이드레이션 | 권장 | 초안(Claude) | [10-rendering-strategies](10-rendering-strategies/) |
| 11 | `accessibility-basics` | 시맨틱 마크업·접근성 트리·키보드·ARIA | 권장 | 초안(Claude) | [11-accessibility-basics](11-accessibility-basics/) |
| 12 | `internationalization-and-localization` | 로캘 협상(`Accept-Language`·BCP 47), 메시지 카탈로그, 복수형 규칙, 숫자·통화·날짜 서식, RTL, 이름·주소 가정 | 권장 | 초안(Claude) | [12-internationalization-and-localization](12-internationalization-and-localization/) |

## 16.2 성능 (2026-09-28 추가 — 측정은 08, 처방은 13~20)

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 08 | `web-performance-vitals` | LCP·INP·CLS와 측정(RUM vs 랩) | 필수 | 초안(Claude) | [08-web-performance-vitals](08-web-performance-vitals/) |
| 13 | `critical-path-and-resource-loading` | 크리티컬 렌더링 패스, 파서 차단·렌더 차단 자원, preload 스캐너, 리소스 힌트(preconnect·dns-prefetch·preload·fetchpriority), async/defer | 필수 | 초안(Claude) | [13-critical-path-and-resource-loading](13-critical-path-and-resource-loading/) |
| 14 | `image-optimization` | 포맷 선택(AVIF·WebP·JPEG 폴백), 반응형 이미지(`srcset`·`sizes`·`<picture>`), 지연 로딩, `width`/`height`로 공간 예약, 첫 화면 이미지 우선순위 | 권장 | 초안(Claude) | [14-image-optimization](14-image-optimization/) |
| 15 | `web-font-loading` | FOIT·FOUT, `font-display`(swap·fallback·optional), 서브셋과 `unicode-range`, 폰트 preload, 대체 폰트 메트릭 맞추기 | 권장 | 초안(Claude) | [15-web-font-loading](15-web-font-loading/) |
| 16 | `long-tasks-and-web-workers` | 긴 태스크(50ms 초과)와 INP, 메인 스레드에 양보(yield)하기, 작업 쪼개기, 웹 워커로 넘기기, `postMessage`의 구조적 복제 비용과 Transferable | 필수 | 초안(Claude) | [16-long-tasks-and-web-workers](16-long-tasks-and-web-workers/) |
| 17 | `list-virtualization` | 보이는 행만 렌더링(windowing), overscan, 가변 높이 측정, 무한 스크롤과의 결합 | 권장 | 초안(Claude) | [17-list-virtualization](17-list-virtualization/) |
| 18 | `ui-rerender-and-memoization` | 선언형 UI의 재렌더 모델: 상태 변경 → 하위 트리 재렌더 → 재조정(diff). 참조 동일성, memo·useMemo·useCallback, 상태를 어디에 둘지 (React는 예시) | 권장 | 초안(Claude) | [18-ui-rerender-and-memoization](18-ui-rerender-and-memoization/) |
| 19 | `hydration-cost-and-partial-hydration` | 하이드레이션 비용(보이지만 반응하지 않는 구간), 점진·부분 하이드레이션, islands 아키텍처(설계 관점은 22), 서버 컴포넌트 | 권장 | 초안(Claude) | [19-hydration-cost-and-partial-hydration](19-hydration-cost-and-partial-hydration/) |
| 20 | `performance-budgets-and-regression-gates` | 성능 예산(번들 KB·LCP·요청 수), 랩 도구(Lighthouse), CI 회귀 게이트, 측정 노이즈 다루기 | 권장 | 초안(Claude) | [20-performance-budgets-and-regression-gates](20-performance-budgets-and-regression-gates/) |

## 16.3 프론트엔드 설계 (2026-09-28 추가)

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 21 | `component-and-state-patterns` | 컴포넌트 합성(Compound·Container/Presentational → 커스텀 훅·Render props), 제어/비제어 컴포넌트, 단방향 데이터 흐름(Flux/Redux/Elm), 상태 위치 선정(로컬·끌어올리기·전역), **서버 상태 캐시 vs 클라이언트 상태**, 파생 상태 | 권장 | 초안(Claude) | [21-component-and-state-patterns](21-component-and-state-patterns/) |
| 22 | `islands-and-micro-frontends` | Islands(서버 HTML + 부분 하이드레이션 — 비용 측면은 19), Micro-frontends(빌드 타임 vs 런타임 통합 — iframe·Web Components·Module Federation), 서버·클라이언트 측 UI 조합 | 심화 | 초안(Claude) | [22-islands-and-micro-frontends](22-islands-and-micro-frontends/) |

## 16.4 영역 마감

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 23 | `web-symptom-index` | 역색인: CORS 에러, fetch 성공인데 에러, 화면 멈춤, hydration mismatch, `ChunkLoadError`, 배포가 반영 안 됨, 레이아웃 튐, INP 나쁨, LCP 이미지 늦음, 폰트 깜빡임, 스크롤 버벅임, 하이드레이션 전 클릭 무시 | 필수 | 초안(Claude) | [23-web-symptom-index](23-web-symptom-index/) |
| 24 | `web-incidents` | 실사건: British Airways 결제 페이지 스크립트 변조(Magecart, 2018) · polyfill.io 도메인 인수 후 악성 코드 배포(2024) | 권장 | 초안(Claude) | [24-web-incidents](24-web-incidents/) |
