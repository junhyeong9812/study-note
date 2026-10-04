# 집필 브리핑 — 커리큘럼 leaf 새 노트 (프론트엔드 엔지니어링 — 웹 플랫폼, 2026-10-04)

> 명세: 같은 폴더 `requirement-spec.md`. 문서 규칙 정본: `cs/README.md` 「작성 규칙」(2026-10-01 머리말 정리 반영판).
> 형식 참고(내용 복사 금지): `cs/database/16-mvcc/`, `cs/os/19-deadlock/`, `cs/network/15-tcp-handshake-and-backlog/`

## 1. 입력

- **커리큘럼 행**: `docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md` §16 프론트엔드 엔지니어링 표에서 담당 slug를 찾는다. 요지·선행·⚠ 깨지면·🔧·📚 칸은 **모두 다뤄야 할 요구사항**이다. §16 머리 문단(뼈대: WHATWG HTML Event loops·Rendering, WHATWG Fetch, web.dev Rendering performance·Core Web Vitals·learn/performance, W3C Service Workers, patterns.dev)도 읽는다.
- **영역 표**: `cs/web-platform/README.md`(생성 문서). 연결 대상 `languages/web-api/*`(Web API 문법 노트, 옛 형식 — **읽기만**, 링크 대상 — 실재 경로를 확인한다).
- **근거**: WHATWG HTML·DOM·Fetch·URL·Storage 표준(html.spec.whatwg.org 등), W3C(Service Workers, CSSOM View, Resource Hints, Preload, Long Animation Frames, Event Timing, Largest Contentful Paint, Layout Instability, WCAG 2.2·ARIA APG), ECMAScript(Promise Jobs·모듈·Intl), web.dev·Chrome for Developers 문서, MDN, Chromium/V8/Blink 문서·소스(source.chromium.org·chromium.googlesource.com), HTTP Archive Web Almanac, 프레임워크 공식 문서(React·Next.js·Vue·Astro·Qwik), patterns.dev, 사고 보고서 원문.
- WebSearch·WebFetch·curl이나 **실험(§5)** 으로 **실제 확인**한 것만 사실로 쓴다.

## 2. 출력 — `cs/web-platform/<NN-slug>/`의 4파일

- **새 형식(2026-10-01)**: 제목 다음 줄부터 바로 본문이다. **제목 아래 `>` 머리말·복습 안내·"Claude 초안" 표식 줄을 두지 않는다.** 진행 단계는 같은 폴더 `metadata.md`에 둔다.

### metadata.md (그대로)

```
# metadata

| 항목 | 값 |
|---|---|
| 단계 | 초안 |
| 초안 | 2026-10-04 (Claude) |
| 검수 | — |
| 학습 | — |
```

### 2-summary.md

```
# web-platform/<NN-slug> — <한 줄 제목> — 정리 (힌트)

## 해결하는 문제
## 동작·원리
## 쓰이는 자료구조·알고리즘
## 적용 — 풀어나가는 법
## 장애 시나리오와 대처
## 핵심 문장
## 관련 주제·근거
```

- 최상위 `## ` 헤딩은 이 7개만, 이 순서로 둔다(하위는 `###`). 실험 절은 `## 동작·원리`나 `## 적용` 안의 `### 실험: …`로 둔다.
- **해결하는 문제**: 이것이 없으면 무엇이 안 되나. 쉬운 예 → "똑같은 구조다" → 실무 예.
- **동작·원리**: 중심. ASCII 그림 먼저(요청·응답 시퀀스, 재시도 시간축, 클라이언트-서버-저장소 상자 그림, 상태 기계, 버전 호환 매트릭스, 페이지 경계 그림, 웹훅 재전송 흐름, 게이트웨이 경로), 글은 그 해설.
- **쓰이는 자료구조·알고리즘**: 예) 멱등 키-결과 저장소(TTL), keyset = B+Tree 범위 스캔, 커서 인코딩, 버전 비교(ETag), 토큰 버킷·슬라이딩 윈도, varint·zigzag, HMAC, 재시도 큐·지수 백오프, 작업 상태 기계, DataLoader(배치+캐시), 트리(자원 계층). cs 노트가 있으면 링크.
- **적용 — 풀어나가는 법**: 실무 순서. 코드(JS·TS 기본 — 브라우저 API·DOM, 필요 시 React 등 프레임워크)와 진단(Chrome DevTools Performance·Lighthouse 지표 정의, PerformanceObserver, CDP 메트릭, `chrome://` 내부 페이지 등).
- **장애 시나리오와 대처**: 3~5개. **현상 → 보이는 형태(에러·로그·지표) → 원인 → 대처**, ⚠ 칸 포함.
- **핵심 문장**: 3~6문장.
- **관련 주제·근거**: 선행·후속 링크(새 노트 `../NN-slug/2-summary.md`, 아직 없는 web-platform 주제는 `../README.md`, 다른 영역은 그 영역 README + "미작성", 다른 영역은 실제 경로 확인 — 특히 `../../network/…`(33 http-semantics·34 caching·35 connection·36 http2·38 websocket·46 load balancers), `../../database/…`(08 btree·17 OCC·18 app-level concurrency), `../../distributed/…`(15 saga·16 outbox·17 queues), `../../reliability/…`(05 timeouts·06 retry·11 rate limiter·13 idempotency), `../../security/…`(있는 것만), `../../software-design/…`(23 DbC), `../../testing/…`(13 contract testing), 사례 `../22-case-order-point/…`~`../27-case-refund/…`), 논문·문서 URL·소스 경로·교재 장, **실험 목록**(무엇을 어떤 환경에서 돌렸나).

### 1-question.md / 3-answer.md

`cs/database/16-mvcc/`와 같은 틀(머리말 없음). 질문 6~10개(왜 / 예측 / 경계 / 연결 / 장애 진단), 정답은 번호·개수 일치. 예측형 질문은 실험 출력으로 답을 확인할 수 있게 쓴다.

## 3. 쓰는 방식 (사용자와 합의된 기준)

1. **그림 먼저, 글은 그림 해설.** 단순한 그림 여러 개 > 복잡한 그림 하나.
2. **용어는 처음 나오는 자리 바로 아래에서 푼다.** 형식 `  - *용어*: 설명`.
3. 한 문장에 한 개념. 용어가 셋 넘게 든 문장은 쪼갠다.
4. **코드**: Java(기본)·JS·TS. 셸은 진단·실험 구동에만.
5. **사실 규칙**: 수치·기본값·버전은 출처나 실험으로 확인했을 때만. 확인 못 하면 `[?]`. **지어내지 않는다.** 예시 수치는 "(예시)".

## 3-1. 앞 영역에서 나온 주의 (2차 리뷰 수백 건의 유형)

- **`[?]`는 확인 못 한 것에만.** 확인했으면 근거(절·URL·소스 경로·실험)를 쓴다.
- **"항상·모든·반드시·절대" 금지** — 예외가 있으면 조건. (가장 많은 지적 유형)
- **노트 안 모순 금지**: 그림과 글, 요약과 정답, 정답 N과 M, 실험 출력과 해석. 다 쓰고 스스로 대조.
- **표준 vs 브라우저 구현 구분**: "HTML 표준은 … 라고 정한다(규범)"와 "Chrome 151에서는 …(실측)"를 섞지 않는다. 브라우저마다 다른 동작(Safari·Firefox)은 확인한 브라우저·버전으로 한정하고, 확인 못 한 엔진은 `[?]`.
- **측정 조건 명시**: 실험 수치는 headless Chrome·CPU/네트워크 스로틀링 설정·기기 클래스에 크게 좌우된다. 조건을 적고, 실사용자(CrUX/RUM) 수치와 랩 수치를 구분한다. Core Web Vitals 임계값(LCP 2.5s·INP 200ms·CLS 0.1, 75번째 백분위)은 web.dev 원문으로 확인.
- **프레임워크 동작은 버전·조건과 함께**: React 18/19, Next.js App Router vs Pages, 하이드레이션 방식 등은 해당 버전 문서로.
- **계층을 섞지 않는다**: 프로토콜(HTTP 캐시) vs 브라우저 정책(HTTP 캐시 분할·CORS) vs 앱 코드.
- **사고 보고서의 시각·수치는 원문 그대로**, 해석은 "해석"이라고 표시.

## 4. 기존 노트

- 24편 전부 신규. `languages/web-api/*`가 이미 다루는 API 사용법은 링크로 넘기고, 이 영역은 **원리·성능·설계**를 쓴다(반복 금지).

## 5. 실험 근거 (명세 I7 — 사용자 요청, 필수)

- **편마다 실행으로 보일 수 있는 핵심 주장 1개 이상을 실제 브라우저 측정으로 보인다**(23·24 종합은 선택). 예:
  - 01·02: 강제 동기 레이아웃(읽기·쓰기 교차) 전후 `LayoutCount`·`RecalcStyleCount`·레이아웃 시간(CDP `Performance.getMetrics`, 트레이스), `transform` vs `top` 애니메이션의 레이아웃·페인트 유무, 사이트 격리 프로세스 수.
  - 03·04: 마이크로태스크·매크로태스크·rAF 실행 순서, 긴 동기 작업 중 클릭 지연, 이벤트 위임 vs 개별 리스너 수, passive 리스너 경고·스크롤 차단.
  - 05·06·07: CORS 프리플라이트 발생 조건(단순 요청 vs 커스텀 헤더), credentials 모드, localStorage 동기 비용·쿼터 초과 예외, Service Worker cache-first vs network-first 오프라인 결과(로컬 정적 서버).
  - 08·13·14·15: LCP·CLS·INP 측정(PerformanceObserver/web-vitals), render-blocking CSS·동기 JS가 FCP·LCP에 주는 영향(preload·defer·async 비교), 이미지 lazy·srcset·크기 미지정 CLS, font-display별 FOIT/FOUT·CLS.
  - 09·10·19·21·22: 번들 크기·코드 분할(esbuild 등 scratchpad npm), CSR vs SSR vs 정적 렌더의 FCP·TTI 차이, 하이드레이션 비용(메인 스레드 시간), 상태 위치에 따른 재렌더 범위.
  - 11·12: 접근성 트리(CDP Accessibility.getFullAXTree)·키보드 포커스 순서, `Intl.DateTimeFormat`·`Intl.NumberFormat`·`Intl.PluralRules` 출력, 문자열 길이 변화에 따른 레이아웃 깨짐.
  - 16·17·18·20: 긴 태스크(Long Tasks/LoAF) vs Web Worker 분리 시 입력 지연, 가상화 전후 DOM 노드 수·스크롤 중 프레임 시간, 메모이제이션 전후 렌더 횟수(React Profiler 또는 카운터), 성능 예산 게이트(Lighthouse CI 대신 측정 스크립트 임계 비교).
- **실행 방법**: Playwright(`playwright-core`를 자기 scratchpad에 `npm install --prefer-offline`)로 호스트 `/usr/bin/google-chrome`(headless, Chrome 151 확인)이나 `~/.cache/ms-playwright`의 Chromium을 `executablePath`로 띄운다 — **브라우저 다운로드 금지**(`npx playwright install` 금지). CDP 세션(`page.context().newCDPSession`)으로 Performance 메트릭·트레이스·스로틀링(`Emulation.setCPUThrottlingRate`, `Network.emulateNetworkConditions`). 로컬 정적 서버는 Node `http` 모듈로 127.0.0.1의 임의 포트, 끝나면 종료.
- **노트에 싣는 것**: 실험 코드(핵심 부분), 실행 환경(브라우저·버전·스로틀링·뷰포트), **실제 출력**(손으로 만들지 않는다), 관찰과 해석. 출력 블록 앞에 `(실험, headless Chrome 151, CPU 4× 스로틀, 2026-10-04)`처럼 적는다. 시간 수치는 여러 번 돌린 범위로.
- **실험으로 보일 수 없는 주장**은 1차 출처로 대신하고 그 사실을 적는다.
- **packet에 실험 목록**: 주장 · 코드 파일(scratchpad 경로) · 실행 명령 · 환경 · 출력 요지. 사실 점검 워커가 다시 돌린다.
- **재부팅 대비**: 실험 코드의 핵심은 노트에 싣는다(/tmp는 재부팅 때 사라진다).

## 6. 실행 환경과 안전 규칙

- **브라우저**: 호스트에 이미 있는 것만 — `/usr/bin/google-chrome`(Chrome 151), `/usr/bin/firefox`, `~/.cache/ms-playwright/chromium-*`. 다운로드·설치 금지. 브라우저 프로세스는 스크립트 끝에서 `browser.close()`, 남은 프로세스가 없는지 확인(`pgrep -f "remote-debugging|headless"`로 자기 것만).
- **npm**: 자기 scratchpad 폴더 안에서만 `npm install --prefer-offline`(전역 `-g` 금지). 큰 프레임워크(React·Next 등)도 scratchpad 안에서만. 설치 실패하면 무리하지 말고 바닐라 JS로 같은 원리를 보인다.
- **로컬 서버**: 127.0.0.1에만 바인드, 작업 끝나면 종료하고 포트가 비었는지 확인. 외부에 노출하지 않는다.
- **컨테이너**: 꼭 필요하면 이미 있는 `node:22-*` 이미지로 `sn-wp-w<NN>-*` 일회용(`--rm`, `-u $(id -u):$(id -g) -e HOME=/tmp`), `docker * prune`·pull·rmi 금지.
- **부하 상한**: 실행 수십 초 이내, 동시 브라우저 1~2개, 호스트를 포화시키지 않는다. 측정 수치는 이 환경의 값이라고 적는다.
- **파일 위치**: 모든 파일은 `/tmp/claude-1000/-home-jun-project-study-note/16696510-853f-4d10-82ba-64d9eb37bcc8/scratchpad/wp/<담당 첫 번호>/`에만(절대 경로). **저장소 루트·노트 폴더에 파일을 만들지 않는다** — 셸 리다이렉트(`>`)로 이름 없는 파일이 루트에 생기지 않게 명령마다 절대 경로를 쓴다(2026-10-03 사고).
- **개인정보 금지**: 요청·파일·노트에 사용자 식별 정보를 넣지 않는다. 외부 사이트를 실험 대상으로 측정하지 않는다(로컬 페이지만).
- **금지**: 이 작업이 만들지 않은 컨테이너·볼륨·이미지·프로세스는 건드리지 않는다.

## 7. 하지 말 것

- 담당 폴더 밖 파일(원고·다른 영역·커리큘럼·README 등)을 수정하지 않는다. git은 조회만.
- 리프 폴더에는 md만(1-question·2-summary·3-answer·metadata).
- 하위 에이전트·fork 금지.

## 8. 자기 검증

- `python3 docs/plans/2026-09-30/network-writing/check_new.py <담당 폴더들>` → 전부 PASS(머리말 금지·metadata 검사 포함).
- §3-1 노트 안 모순 자기 대조. 실험 출력과 본문·정답의 수치가 같은지 대조.

## 9. 반환 packet

- 폴더 목록과 check 결과
- 편별 주요 근거(논문·문서 URL·소스 경로·교재 장)
- **실험 목록**(주장 · 코드 경로 · 명령 · 환경 · 출력 요지) + 전용 컨테이너·토픽·키를 지웠는지
- `[?]` 목록, 커리큘럼 ⚠ 칸 커버 여부, 미완료 항목
