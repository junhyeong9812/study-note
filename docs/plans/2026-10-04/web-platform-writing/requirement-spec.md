# 요구사항 명세서 — web-platform-writing

> 작성일: 2026-10-04 · 작업 폴더: `docs/plans/2026-10-04/web-platform-writing/` · 브랜치: main(5261d34f, origin과 같음)에서 `docs/web-platform-writing`.
> 선행: network·os·database·distributed·reliability·software-design·domain-modeling·testing·api-design(모두 main 반영·push). 브리핑·실험 규칙·도구는 api-design판을 재사용한다.
> **동시 실행 금지**: 같은 작업 트리에서 다른 실행이 이 영역을 진행하지 않는다는 전제. 착수·회수마다 `git log`·`git branch`·파일 mtime으로 다른 실행의 흔적을 확인하고, 있으면 멈추고 사용자에게 묻는다.

## 0. 요구사항 원문 (인터뷰)

- 원문: "커리큘럼 작성을 너가 하던거 아니야? 진행하면 될 꺼 같은데 서브에이전트한테 시키면서 진행하던 거 아니야? 다 되면 받아서 너가 검수하는 식으로 했을텐데?"
- 해석: 커리큘럼 순서상 다음 영역 **프론트엔드 엔지니어링**(`cs/web-platform/`, §16)을 **앞 영역과 같은 방식**(Opus 서브에이전트 집필 → 사실 점검·실험 재실행 → 2차 리뷰(codex, 한도면 Opus 적대 리뷰) → 판정 → 정합 → 웹 표본)으로 진행.

## 1. 목표·대상 (필수)

- `cs/web-platform/NN-slug/{1-question,2-summary,3-answer,metadata}.md` **24편**(커리큘럼 §16 01~24, 전부 신규). 종합 23 web-symptom-index·24 web-incidents는 마지막.
- 연결(링크로만, 반복 금지): `languages/web-api/*`(08·09·10·15~18·20·25~30·38·39 등 실재 경로 확인), network·security·api-design leaf.
- 생성 문서 `cs/web-platform/README.md` 재생성: 24편 전부 `초안(Claude)`.

## 2. 경계·불변식 (필수)

- **I1 형식**: 7절 골격, Q/A 6~10, 제목 아래 머리말·표식 없음, metadata 단계 `초안`.
- **I2 근거**: WHATWG HTML(Event loops·Rendering·Origin)·DOM·Fetch 표준, W3C(Service Workers·CSSOM View·Resource Hints·Preload·WCAG 2.2·Long Animation Frames), web.dev(Rendering performance·Core Web Vitals·learn/performance), MDN, Chromium·V8·Blink 문서와 소스, ECMAScript(모듈·Intl), patterns.dev, 프레임워크 공식 문서(React·Next.js·Vue·Astro), 사고 보고서 원문. 확인 못 한 것은 `[?]`. 브라우저마다 다른 동작은 **브라우저·버전**을 붙인다(예: "Chrome 14x에서는").
- **I3 커리큘럼 일치**: §16 각 행의 요지·⚠·🔧·📚 전부, 선행 링크.
- **I4 기존 보존**: `languages/web-api`·다른 영역 노트 수정 금지(링크만).
- **I5 링크·트리**: 새로 깨는 링크 0, 리프에 md만.
- **I6 재현 안전**: 호스트의 headless Chrome·Playwright 브라우저(이미 설치된 것만)와 Node 18 또는 이미 있는 `node:22` 이미지를 쓴다. 새 브라우저·이미지 다운로드 금지, npm 의존성은 scratchpad 안에서만(전역 설치 금지). 로컬 정적 서버는 127.0.0.1·작업 끝나면 종료. 컨테이너를 쓰면 `sn-wp-w<NN>-*`·`docker rm -fv`·prune·pull·rmi 금지. 개인정보 금지, 저장소 루트 파일 금지(절대 경로).
- **I7 실험 근거 우선 — 웹 해석**: 편마다 실행 가능한 핵심 주장 1개 이상을 **실제 브라우저(headless Chrome/Playwright) 측정 출력**으로 보인다(23·24 제외 가능) — 예: 강제 동기 레이아웃(layout thrashing) 전후 레이아웃 횟수·시간(Performance 트레이스), 마이크로태스크 vs 매크로태스크 실행 순서, 이벤트 위임·passive 리스너, CORS 프리플라이트 발생 조건, storage 쿼터·삭제, Service Worker 캐시 전략, CLS·LCP·INP 측정(web-vitals 또는 PerformanceObserver), render-blocking CSS/JS가 FCP에 주는 영향, 이미지 lazy·srcset, font-display별 FOIT/FOUT, 긴 태스크 vs Web Worker, 가상화 전후 DOM 노드 수·스크롤 프레임, 메모이제이션 전후 재렌더 횟수, 하이드레이션 비용. 출력은 실제 실행 결과만, 실행 환경(브라우저·버전·CPU 제한/스로틀링 설정)을 함께 적는다. 비결정적 수치는 여러 번 돌린 범위.

## 3. 기준소스 (필수)

- curriculum.md §16, `cs/web-platform/README.md`, I2 출처, `languages/web-api/*`(연결 대상)

## 4. 금지영역 (필수)

- web-platform 새 leaf 밖 노트(languages/web-api 포함 — 읽기만), 커리큘럼 본문(NEXT로)
- 생성 문서 수기 수정 · 이번 작업이 만들지 않은 컨테이너·볼륨·이미지 · 브라우저·전역 패키지 설치

## 5. 검증 방법 (필수)

- V1 check_new · V1b 사실 점검이 편당 실험 1개+ 재실행 · V2 Opus 사실 점검 · V3 codex(high) 2차 리뷰, 한도 시 Opus 적대 리뷰 → 판정 · V4 정합(network·security·api-design·languages/web-api 선행 포함) · V5 웹 교차 20+, 링크 신규 깨짐 0, 생성 문서 재생성, 정리 확인(서버·브라우저 프로세스·컨테이너)

## 6. stakes (필수)

- **중간** — 새 학습 자료 24편, 사실 오류(브라우저별 동작·표준 문구·측정 해석) 위험.

## 7. 자율성

- [x] auto

## 8. load-bearing 가정

- **A1**: 호스트 `google-chrome`(headless)과 `~/.cache/ms-playwright`의 Chromium으로 트레이스·PerformanceObserver 측정이 된다. 착수 직후 메인이 스모크한다(Playwright 패키지는 npm 캐시에서 scratchpad로 설치 가능 여부 포함).
- **A2**: codex 한도는 10-04 08:53에 풀렸다 — 2차 리뷰는 codex 우선, 한도면 Opus 대체.

## 9. task 분해

| task | 목표 | acceptance |
|---|---|---|
| 01 | 실험 환경 스모크(A1) + 브리핑(api-design판 이식 + 웹 실험 예시) | 스모크 기록·브리핑 |
| 02 | 집필(Opus 병렬 5~6, 워커당 4~5편), 종합 23·24 후속 | 24 PASS |
| 03 | 사실 점검 + 실험 재실행 | packet |
| 04 | 2차 리뷰 → 판정 → 정합 → 웹 | V3~V5 |
| 05 | README 재생성·정리·커밋·(확인 후) push·log·NEXT·측정로그 | V5 |

## 승인 상태

- [x] 6칸
- [x] 합의: 사용자 답변(2026-10-04)
- [x] auto
