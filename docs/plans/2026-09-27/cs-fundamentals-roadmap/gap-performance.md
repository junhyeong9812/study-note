# 갭 리서치 — 성능 공학 (2026-09-28, L0)

> **대상**: [`curriculum.md`](curriculum.md) (18개 영역, 517 leaf) 가운데 **성능 공학**에서 빠진 주제를 찾는다.
> **방법**: 컴퓨터 구조(§4)·OS(§5)·언어(§6)·네트워크 7.8~7.9·DB 9.3~9.8·신뢰성(§11)·웹 플랫폼(§16)·엔지니어링 실천(§17)의 leaf 표를 직접 읽었다. 조사 항목마다 기존 leaf와 맞춰 보고, 근거는 WebSearch로 확인했다(약 26회).
> **표기**: 커리큘럼과 같다. `[?]` = 이번 작업에서 원문(장·절·수치)을 직접 확인하지 못한 것.
> **상태**: 제안(L0). curriculum.md는 고치지 않았다. 반영할지는 따로 정한다.

---

## 1. 커버 점검표

판정 기준:
- **있음**: 기존 leaf의 요지나 ⚠ 칸이 이미 그 주제를 다룬다.
- **부분**: 기존 leaf에 한두 줄 걸쳐 있다. 서머리 절을 하나 늘려서 흡수할 수 있다.
- **부분→독립**: 걸쳐는 있지만 흡수하면 그 leaf의 질문이 10개를 넘는다(§0.4). 그래서 독립 leaf로 뺀다.
- **없음**: 어디에도 없다.

### 1.1 프론트엔드 렌더링·로딩

| 조사 항목 | 판정 | 기존 slug / 흡수 위치 | 비고 |
|---|---|---|---|
| Core Web Vitals(LCP·INP·CLS) 정의·측정 | 있음 | `web-platform/08-web-performance-vitals` | RUM과 랩 측정, p75 집계까지 있다. 지표별 **개선 기법**은 아래 신규 leaf로 나눈다 |
| 크리티컬 렌더링 패스·렌더 차단 자원·리소스 힌트(preload·preconnect·fetchpriority) | 부분→독립 | `web-platform/02-rendering-pipeline` ⚠ 칸의 "렌더 차단 CSS·JS" 한 줄 | 02는 파이프라인의 **단계**를 다룬다. **로딩 순서와 우선순위**는 다른 축이라 신규 14 |
| 리플로우·리페인트(layout thrashing) | 있음 | `web-platform/02-rendering-pipeline` | — |
| 합성 레이어(transform·opacity만 합성, will-change 남용) | 부분 | `web-platform/02-rendering-pipeline`에 흡수(합성 절 1개 추가) | 신규 leaf는 만들지 않는다 |
| CLS 원인(크기 미지정 이미지·주입 콘텐츠·폰트 교체) | 부분 | `08`(이미지 크기 미지정 한 줄) + 신규 15·16이 원인별로 다룬다 | — |
| 긴 목록 가상화(windowing) | 없음 | — | 신규 18 |
| 이미지 최적화(AVIF·WebP·srcset·lazy·크기 예약) | 없음 | — | 신규 15 |
| 웹 폰트 최적화(font-display·서브셋·preload) | 없음 | — | 신규 16. 한글 폰트는 파일이 커서 실무 빈도가 높다 |
| 번들 크기: 트리 셰이킹·코드 분할 | 있음 | `web-platform/09-js-modules-and-bundling` | — |
| 번들 크기: 전송 압축(gzip·br·zstd) | 있음 | `network/46-http-content-encoding` | — |
| 성능 예산·CI 회귀 게이트(bundlesize·Lighthouse CI) | 없음 | — | 신규 21 |
| 하이드레이션 비용(보이는데 반응 없음, 부분·점진 하이드레이션, islands) | 부분→독립 | `web-platform/10-rendering-strategies`(전략 선택과 mismatch **정합성**만 다룸) | 신규 20 |
| React 리렌더 최적화(memo·useMemo·재조정) | 없음 | — | 신규 19. 웹 플랫폼 영역이 "개념만"이라 **선언형 UI의 재렌더 모델**로 일반화하고, React는 예시로만 든다 |
| 웹 워커·긴 태스크 쪼개기(INP 개선) | 부분→독립 | `web-platform/03-event-loop` ⚠ 칸 "긴 태스크 → INP 악화" | 03은 원인만 말하고 처방(양보·워커·전송 비용)이 없다. 신규 17 |
| 서비스 워커 캐싱 | 있음 | `web-platform/07-service-workers-and-offline` | — |

### 1.2 백엔드·런타임

| 조사 항목 | 판정 | 기존 slug / 흡수 위치 | 비고 |
|---|---|---|---|
| CPU 프로파일링·플레임 그래프·off-CPU·락 | 있음 | `reliability/19-profiling` | — |
| 샘플링 vs 계측, 세이프포인트 편향 | 있음 | `reliability/19-profiling` ⚠ 칸 | async-profiler의 AsyncGetCallTrace 설명은 19의 실습 절로 넣는다 |
| 메모리 프로파일링: 힙 덤프·지배자 트리·누수 패턴·native 누수 | 부분→독립 | `reliability/19`("메모리 프로파일링" 한 단어), `reliability/33` 증상 "메모리 우상향" | 진단 절차가 따로 한 편 분량이다. 신규 37 |
| JIT vs AOT 개념 | 있음 | `language/01-compile-interpret-jit` | — |
| JIT 계층 컴파일·워밍업·역최적화·코드 캐시 | 부분→독립 | `language/01` ⚠ 칸 "워밍업 전 첫 요청 느림" | 01은 개념 leaf라 운영 증상까지 담으면 넘친다. 신규 22 |
| GC 알고리즘·STW 일시정지 | 있음 | `language/13-garbage-collection` | — |
| GC 튜닝(수집기 선택·힙 크기·일시정지 목표·GC 로그·컨테이너 인지) | 부분→독립 | `language/13` | 13은 **알고리즘**, 튜닝은 **운영**이다. 신규 24 |
| 네이티브 이미지·AOT 캐시·시작 시간 | 없음 | (`language/01` ⚠ "AOT/JIT 차이로 리플렉션 실패" 한 줄) | 신규 23 |
| 바이너리 크기 | 없음 | — | 신규 26(LTO와 묶음) |
| 메모리 레이아웃(캐시 지역성·정렬·패딩) | 있음 | `architecture/12-memory-hierarchy-and-locality`, `architecture/04-byte-order-and-alignment`, `architecture/13-cache-organization`(false sharing) | — |
| 객체 헤더·박싱·탈출 분석·할당률 줄이기 | 없음 | — | 신규 25 |
| 커넥션 풀 크기 | 있음 | `database/32-connection-pooling` | — |
| N+1 | 있음 | `database/33-orm-and-n-plus-one`, `architecture/14-latency-numbers` | — |
| 배칭·파이프라이닝·왕복 줄이기(bulk insert·Redis pipeline·DataLoader) | 없음 | (N+1의 일반화로 볼 수 있지만 따로 다루는 leaf가 없다) | 신규 40 |
| 캐시 패턴(cache-aside·스탬피드·일관성) | 있음 | `database/38-caching-with-databases`, `reliability/13-cache-stampede`, `distributed/30-distributed-cache-consistency`, `data-structure/10-lru-cache` | — |
| 캐시 **계층**(로컬 L1 + 분산 L2, near cache, 인스턴스 간 무효화) | 부분→독립 | `database/38` | 38은 DB 앞 캐시 한 겹만 다룬다. 신규 41 |
| 비동기·논블로킹의 실제 이득과 한계 | 부분→독립 | `os/28-io-models`, `os/21-event-based-concurrency`, `language/15-concurrency-models`(블로킹·pinning 증상) | **"지연이 아니라 동시성이 는다"는 용량 추론**은 없다. 신규 39 |
| 벤치마크 방법론(매크로)·coordinated omission | 있음 | `reliability/18-performance-measurement` | open vs closed 부하 모델은 18·21에 흡수한다 |
| 마이크로벤치마크(JMH·DCE·상수 접기·포크·워밍업) | 부분→독립 | `language/05` ⚠ "마이크로벤치마크 결과가 DCE로 0ns" 한 줄 | 신규 36 |
| 부하 테스트 | 있음 | `reliability/21-capacity-and-load-testing` | — |
| 용량 계획(Little's law·USL) | 있음 | `math/15-queueing-and-littles-law`, `reliability/20-scaling-principles`, `reliability/21` | — |
| 성능 방법론(측정 우선·Amdahl·병목 이동·안티 방법론) | 부분→독립 | `os/35`(USE), `reliability/20`(USL). 기존 노트 `engineering/engineering-axes/performance.md`(대원칙 3개)는 `software-design/20`에 병합될 예정 | Amdahl이 커리큘럼 어디에도 없다. 성능 트랙의 입구가 없다. 신규 35 |

### 1.3 바이너리·빌드·배포

| 조사 항목 | 판정 | 기존 slug / 흡수 위치 | 비고 |
|---|---|---|---|
| 데드 코드 제거 | 있음 | `language/05-ir-and-optimization`(컴파일러), `web-platform/09`(트리 셰이킹) | — |
| 링크 타임 최적화(LTO·ThinLTO)·PGO | 없음 | — | 신규 26(심화) |
| 컨테이너 이미지 크기(멀티스테이지·distroless·레이어 캐시) | 없음 | (`os/34`는 이미지 레이어의 **원리**만 다룸) | 신규 `engineering-practice/19` |
| 콜드 스타트(서버리스 Init·이미지 pull·스케일 아웃 직후 워밍업) | 없음 | (`reliability/22-autoscaling` ⚠ 칸 "스케일 반응 지연"은 제어 루프 관점) | 신규 38 |

**정리**: 조사 항목 41개 가운데 있음 17 · 부분(흡수) 2 · 부분→독립 10 · 없음 12. 커리큘럼은 **측정과 용량**(reliability 11.3)과 **하드웨어 메커니즘**(architecture)을 잘 덮는다. 빠진 곳은 세 군데다. ① 프론트엔드의 **처방** 쪽(로딩·이미지·폰트·가상화·리렌더) ② 런타임의 **운영 튜닝** 쪽(JIT 워밍업·GC 튜닝·할당·시작 시간) ③ **빌드 산출물 크기**.

---

## 2. 신규 leaf 제안 (21개)

번호는 각 영역의 현재 마지막 번호 뒤에 잇는다. 기존 7.8b(network 46~52)와 같은 방식이다. 역색인·실사건 leaf는 번호를 그대로 두고 영역 끝에 둔다. `선행` 칸에는 curriculum.md에 **실제로 있는** slug만 적었다(신규끼리 참조할 때는 같은 영역 번호만 적는다).

### 2.1 `web-platform/` — 단원 "16.2 성능"을 새로 둔다 (기존 08 + 신규 14~21)

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 14-critical-path-and-resource-loading | 크리티컬 렌더링 패스, 파서 차단·렌더 차단 자원, preload 스캐너, 리소스 힌트(preconnect·dns-prefetch·preload·fetchpriority), async/defer | 02, 08, network/35-http-connection-management | `<head>`의 동기 `<script>`·큰 CSS → FCP·LCP 지연(LCP > 2.5s = "개선 필요"). preload를 남발하면 대역폭을 서로 빼앗아 LCP가 오히려 나빠진다. 첫 화면 LCP 이미지에 `loading=lazy`를 걸면 LCP가 늦어진다 | 자원 의존 그래프의 임계 경로(최장 경로, data-structure/08-graph), 우선순위 큐 | web.dev "Understand the critical path"(learn/performance) · web.dev "Assist the browser with resource hints" · web.dev "Optimize resource loading" | 필수 | 신규 |
| 15-image-optimization | 포맷 선택(AVIF·WebP·JPEG 폴백), 반응형 이미지(`srcset`·`sizes`·`<picture>`), 지연 로딩, `width`/`height`로 공간 예약, 첫 화면 이미지 우선순위 | 14 | 4000px 원본을 모바일에 그대로 보냄 → 수 MB 전송, LCP 악화. 크기를 지정하지 않은 이미지 → 로드 후 레이아웃 이동(CLS > 0.1). 모든 이미지에 lazy → 히어로 이미지 LCP 지연 | 해상도별 후보 선택(DPR × 뷰포트), 손실 압축(변환 부호화 — algorithm/42-modern-codecs-lz4-zstd-brotli와 무손실 대비) [?] | web.dev "Responsive images"(learn/design) · web.dev "Optimize Cumulative Layout Shift" · web.dev "Preload responsive images" | 권장 | 신규 |
| 16-web-font-loading | FOIT·FOUT, `font-display`(swap·fallback·optional), 서브셋과 `unicode-range`, 폰트 preload, 대체 폰트 메트릭 맞추기 | 14 | 폰트 로딩 동안 텍스트가 보이지 않음(FOIT — 블록 기간 약 3초 [?]). swap으로 폰트가 바뀔 때 글자 폭 차이로 CLS 발생. 한글 폰트 전체(수 MB)를 모든 페이지에서 로드 → LCP 지연 | 사용 글리프 집합 계산(data-structure/18-bitset), 유니코드 범위 분할 | web.dev "Optimize web fonts"(learn/performance) · web.dev "Optimize WebFont loading and rendering" · web.dev "Preload optional fonts" | 권장 | 신규 |
| 17-long-tasks-and-web-workers | 긴 태스크(50ms 초과)와 INP, 메인 스레드에 양보(yield)하기, 작업 쪼개기, 웹 워커로 넘기기, `postMessage`의 구조적 복제 비용과 Transferable | 03, 08 | 클릭 핸들러 안의 무거운 계산 → INP > 200ms, "버튼이 안 눌린다". 큰 객체를 워커로 넘기면 구조적 복제 비용 때문에 오히려 느려진다. 워커 안에서 DOM 접근 → `ReferenceError: document is not defined` | 협력적 스케줄링(청크 분할), 메시지 큐, 소유권 이전(Transferable) | web.dev "Optimize long tasks" · web.dev "Use web workers to run JavaScript off the browser's main thread" · HTML 표준 "Web workers" 절 | 필수 | 신규 (연결: `foundations/web-api/39-idle-scheduling`) |
| 18-list-virtualization | 보이는 행만 렌더링(windowing), overscan, 가변 높이 측정, 무한 스크롤과의 결합 | 02, 04 | 1만 행 테이블을 그대로 DOM에 올림 → 스크롤 프레임 드롭, 탭 메모리 수백 MB [?]. 가변 높이를 잘못 추정 → 스크롤바가 튀고 위치가 어긋남. 가상화한 목록은 브라우저 찾기(Ctrl+F)와 스크린리더 탐색에서 빠진다 | 보이는 구간 계산 = 누적 높이(algorithm/10-prefix-sum) + 이진 탐색(algorithm/06-binary-search). 높이 갱신에는 data-structure/17-fenwick-tree | web.dev "Virtualize large lists with react-window" | 권장 | 신규 |
| 19-ui-rerender-and-memoization | 선언형 UI의 재렌더 모델: 상태 변경 → 하위 트리 재렌더 → 재조정(diff). 참조 동일성, memo·useMemo·useCallback, 상태를 어디에 둘지 | 04, language/07-values-references-passing | 최상위 상태 하나가 바뀌면 수천 개 자식이 재렌더 → 타이핑 지연(INP 악화). 렌더할 때마다 새 객체·함수를 prop으로 넘김 → memo가 무력화된다. memo를 남발하면 비교 비용과 메모리만 늘고 효과가 없다 | 트리 diff 휴리스틱 O(n)(일반 트리 편집 거리는 O(n³)) [?], 얕은 비교, 메모이제이션(algorithm/21-dp-basics) | react.dev "memo" · react.dev "useMemo" | 권장 | 신규 |
| 20-hydration-cost-and-partial-hydration | 하이드레이션 비용(보이지만 반응하지 않는 구간), 점진·부분 하이드레이션, islands 아키텍처, 서버 컴포넌트 | 10, 09, 17 | SSR로 LCP는 빨라졌는데 하이드레이션 전 클릭이 무시됨(TTI 격차). 페이지 전체를 한 번에 하이드레이션 → 긴 태스크, INP 악화. 직렬화한 초기 상태 JSON이 HTML에 중복 삽입 → 문서 비대 | DOM 트리와 컴포넌트 트리 매칭(트리 순회) | web.dev "Rendering on the Web" · patterns.dev "Islands Architecture" | 권장 | 신규 |
| 21-performance-budgets-and-regression-gates | 성능 예산(번들 KB·LCP·요청 수), 랩 도구(Lighthouse), CI 회귀 게이트, 측정 노이즈 다루기 | 08, 09, engineering-practice/08-ci-cd-pipelines | 의존성 하나를 추가했는데 번들이 수백 KB 늘어난 것을 아무도 모름. Lighthouse 점수가 실행마다 흔들려 게이트가 오탐 → 결국 꺼 둠 [?] | 임계값 비교, 반복 측정의 중앙값(data-analysis/04-descriptive-statistics) | web.dev "Performance budgets 101" · web.dev "Incorporate performance budgets into your build process" · MDN "Performance budgets" | 권장 | 신규 |

- `web-platform/02`에는 **합성 절**(transform·opacity만 컴포지터에서 처리, 레이어 과다는 메모리 비용)을 추가한다. 근거: web.dev "Stick to Compositor-Only Properties and Manage Layer Count".
- `web-platform/12-web-symptom-index`에 증상을 더한다: "INP 나쁨", "LCP 이미지 늦음", "폰트 깜빡임", "스크롤 버벅임", "하이드레이션 전 클릭 무시".

### 2.2 `language/` — 단원 "6.3b 런타임 성능"

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 22-jit-tiered-compilation-and-warmup | 계층 컴파일(인터프리터 → C1 → C2), 프로파일 수집, 인라이닝, OSR, 역최적화(deopt), 코드 캐시, 워밍업 전략 | 01, 05, 11 | 배포 직후 readiness는 통과했는데 JIT가 끝나지 않아 p99가 몇 배로 뜀. 타입 프로파일이 깨져 역최적화가 연쇄 → 간헐적 CPU 스파이크. `CodeCache is full. Compiler has been disabled.` 경고 뒤 전체가 인터프리터 속도로 떨어짐 | 호출·백엣지 카운터, 타입 프로파일(인라인 캐시), 호출 그래프 | OpenJDK HotSpot 문서 [?] · JEP 483(AOT 클래스 로딩·링킹) | 권장 | 신규 |
| 23-aot-native-image-and-startup | 닫힌 세계 가정의 AOT 네이티브 이미지(GraalVM), 리플렉션·프록시 설정, AOT 캐시(CDS·Leyden)로 시작 시간 줄이기, 최고 처리량과의 트레이드오프 | 22, os/32-linking-and-loading | 리플렉션 대상이 설정에서 빠짐 → JVM에선 되는데 네이티브에서만 `ClassNotFoundException`·`NoSuchMethodException`. 빌드가 수 분 걸리고 메모리를 수 GB 씀. PGO가 없으면 최고 처리량이 JIT보다 낮을 수 있다 [?] | **도달성 분석**(호출 그래프 순회, algorithm/11-bfs), 스냅숏(힙 이미지) | GraalVM "Native Image" 레퍼런스 매뉴얼(호환성·최적화 가이드) · JEP 483 · Spring Boot "GraalVM Native Image Support" | 권장 | 신규 |
| 24-gc-tuning-and-gc-logs | 수집기 선택(처리량형 vs 지연형 — Parallel·G1·ZGC), 힙 크기와 일시정지 목표(`MaxGCPauseMillis`), GC 로그 읽기, 할당률과 승격률, 컨테이너 메모리 인지(`MaxRAMPercentage`) | 13, os/13-oom-and-memory-limits | 컨테이너에서 기본 최대 힙(메모리의 1/4)을 그대로 씀 → 메모리 낭비. 반대로 힙을 limit 가까이 잡음 → native 영역 포함 초과로 `OOMKilled`(exit 137). G1 `to-space exhausted`·evacuation failure 뒤 Full GC. humongous 할당 반복 | 세대 가설, 영역 기반 수집 집합 선택(탐욕, algorithm/23-greedy) | Oracle "HotSpot Virtual Machine Garbage Collection Tuning Guide"(G1 절) · Oracle "Garbage First Garbage Collector Tuning" | 권장 | 신규 |
| 25-object-layout-and-allocation-reduction | 객체 헤더·압축 참조(compressed oops)·패딩, 박싱 비용, 객체 배열 vs 원시 배열, 탈출 분석과 스칼라 치환, TLAB, 할당률 줄이기, 객체 풀링 반패턴 | 12, 13, architecture/12-memory-hierarchy-and-locality, architecture/04-byte-order-and-alignment | `List<Long>` 1천만 개 → `long[]`보다 몇 배 많은 메모리(헤더 + 참조 + 패딩). 초당 GB 단위로 할당 → Young GC가 잦아지고 p99가 튄다. 객체 풀링 → 오래 사는 객체가 Old 영역을 오염시켜 Full GC | AoS vs SoA, 원시형 특화 컬렉션, 탈출 분석(데이터 흐름 분석) | OpenJDK JOL README · Shipilëv "JVM Anatomy Quark #18: Scalar Replacement" | 권장 | 신규 |
| 26-lto-pgo-and-binary-size | 링크 타임 최적화(LTO·ThinLTO), 프로파일 기반 최적화(PGO), 링크 단계 데드 코드 제거, 심볼 제거(strip), 정적·동적 링크별 바이너리 크기 | 05, os/32-linking-and-loading | full LTO를 켜자 링크 시간과 메모리가 급증해 CI 타임아웃 [?]. 대표성 없는 프로파일로 PGO를 돌림 → 실제 핫 경로가 더 느려짐. 디버그 심볼이 들어간 채 배포 → 바이너리 수백 MB, 이미지 pull 지연 | 전역 호출 그래프 분석, 도달성 기반 제거 | LLVM "How To Build Clang and LLVM with Profile-Guided Optimizations" · Clang ThinLTO 문서 [?] | 심화 | 신규 |

### 2.3 `reliability/` — 11.3 "성능·용량" 확장

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 35-performance-method-and-amdahl | 측정 → 병목 특정 → 한 가지만 바꾸기 → 재측정. Amdahl의 법칙, 병목 이동, 안티 방법론(가로등 효과·무작위 튜닝) | os/35-os-observability-tools, 18 | 전체의 5%인 구간을 2배 빠르게 해 봐야 전체는 약 2.5% 개선(Amdahl). JVM·커널 플래그를 여러 개 한꺼번에 바꿈 → 무엇이 효과였는지 모르고 회귀도 재현하지 못함 | Amdahl 식, 병목 탐색 순서(USE 체크리스트) | Amdahl AFIPS 1967 · Gregg 『Systems Performance』 2판 2장 [?] | 필수 | 신규 (연결: `engineering/engineering-axes/performance.md` 대원칙 절) |
| 36-microbenchmarking | JMH, 워밍업·반복·포크, 데드 코드 제거·상수 접기 함정, Blackhole, 결과 비교의 통계 | 18, language/05-ir-and-optimization, data-analysis/08-confidence-intervals | 결과가 0.3 ns/op → 계산이 DCE로 지워졌다. `System.nanoTime` 루프로 직접 잼 → OSR·워밍업 때문에 왜곡. 포크 1회로 여러 벤치마크를 돌림 → 프로파일이 섞여 실행 순서마다 결과가 다름 | 반복 측정 분포, 신뢰구간 | OpenJDK JMH(`jmh-samples`) · Georges 외 OOPSLA 2007 "Statistically Rigorous Java Performance Evaluation" [?] | 권장 | 신규 |
| 37-memory-leak-and-heap-analysis | 힙 덤프·히스토그램, 지배자 트리와 retained size, 누수 패턴(static 컬렉션·리스너·ThreadLocal·무제한 캐시), 힙 밖 누수(direct buffer·native·NMT), RSS vs 힙 | 19, language/13-garbage-collection, os/13-oom-and-memory-limits | GC 후 바닥선이 계속 올라가는 톱니 → 결국 `OutOfMemoryError: Java heap space`. 힙은 정상인데 RSS만 우상향 → native·direct 메모리 누수로 `OOMKilled`. 운영 중에 힙 덤프를 뜸 → 수십 초 STW와 디스크 풀 | **지배자 트리**(Lengauer–Tarjan), 객체 그래프 도달성(algorithm/12-dfs) | Eclipse MAT 문서 "Dominator Tree" [?] · Lengauer–Tarjan TOPLAS 1979 | 필수 | 신규 |
| 38-cold-start-and-scale-from-zero | 서버리스 Init 단계, 컨테이너 이미지 pull, 런타임 시작 + JIT 워밍업, readiness 설계, provisioned concurrency·스냅숏 복원(SnapStart) | 22, language/23-aot-native-image-and-startup, os/34-containers-namespaces-cgroups | Lambda Init Duration 수 초 → 첫 요청 타임아웃. 스케일 아웃된 새 파드가 이미지 pull과 워밍업 도중 트래픽을 받아 p99가 급등. 스냅숏 복원 뒤 난수 시드·커넥션 같은 고유 상태가 복제되는 문제 [?] | 인스턴스 풀(예열 풀 크기 = Little's law, math/15-queueing-and-littles-law) | AWS Lambda "Understanding the Lambda execution environment lifecycle" · AWS Lambda "Improving startup performance with Lambda SnapStart" · AWS Compute Blog "Understanding and Remediating Cold Starts" | 권장 | 신규 |
| 39-async-io-gains-and-limits | 비동기·논블로킹·가상 스레드가 늘려 주는 것은 **동시성**(처리량)이지 지연이 아니다. CPU 바운드에서는 이득 없음, 블로킹 경로가 섞였을 때, 병목이 하류 풀로 이동 | language/15-concurrency-models, os/28-io-models, math/15-queueing-and-littles-law, database/32-connection-pooling | 리액티브로 전환했는데 JDBC가 블로킹 → 이벤트 루프 스레드 고갈로 처리량이 오히려 떨어짐. 가상 스레드로 동시 요청이 10배 → DB 풀 고갈 `Connection is not available, request timed out`. 백프레셔 없는 비동기 팬아웃 → 메모리 폭증 | Little's law(L=λW), 유계 큐 | JEP 444 "Virtual Threads"(scale, not speed) · Little 1961 | 권장 | 신규 |
| 40-batching-and-round-trips | 왕복(RTT) 줄이기: 요청 배칭, 파이프라이닝, bulk insert·`COPY`, DataLoader식 모으기. 배치 크기 ↔ 지연 트레이드오프, 배치의 부분 실패 | architecture/14-latency-numbers, database/33-orm-and-n-plus-one, network/22-nagle-and-delayed-ack | 1건씩 INSERT 10만 번 → 수 분(배치하면 수 초 [?]). 배치가 너무 큼 → 락 장기 보유, MySQL `Packet for query is too large`(max_allowed_packet). 배치를 모으는 대기 시간이 p99에 더해진다. 배치 중 일부만 실패했는데 전체 성공으로 처리 | 버퍼 + 크기·시간 트리거 flush(data-structure/38-ring-buffer) | Redis 문서 "Pipelining" [?] · PostgreSQL 문서 "Populating a Database"(COPY) [?] | 권장 | 신규 |

- `reliability/18`·`21`에는 **open vs closed 부하 모델**(도착률 고정 vs 사용자 수 고정) 절을 추가한다. 근거: Grafana k6 "Open and closed models", giltene/wrk2 README.
- `reliability/19`의 실습 절에는 async-profiler(AsyncGetCallTrace + perf_events)를 넣는다.
- `reliability/33-reliability-symptom-index`에 증상을 더한다: "배포 직후만 느림"(22·38), "RSS만 우상향"(37), "비동기 전환 후 더 느림"(39).

### 2.4 `database/`

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 41-multi-level-caching | 로컬 L1(프로세스 내) + 분산 L2(Redis) 계층, 인스턴스 간 무효화 전파(pub/sub·서버 지원 클라이언트 캐싱), 로컬 캐시의 크기 제한과 GC 압박, 핫키 로컬화 | 38, distributed/30-distributed-cache-consistency, data-structure/10-lru-cache | L1 무효화가 전파되지 않음 → 로드밸런서 라운드로빈 때문에 새로고침마다 값이 바뀜. 로컬 캐시에 크기 제한이 없음 → Old 영역이 커지고 GC 일시정지. Redis 핫키 하나 → 단일 샤드 CPU 100%, 네트워크 포화 | W-TinyLFU 허용 정책, 무효화 브로드캐스트, 서버 측 추적 테이블 | Redis 문서 "Client-side caching reference" · Redis `CLIENT TRACKING` · Einziger 외 "TinyLFU" ACM TOS 2017 [?] | 권장 | 신규 |

### 2.5 `engineering-practice/`

| slug | 요지 | 선행 | ⚠ 깨지면 | 🔧 | 📚 | 등급 | 기존 |
|---|---|---|---|---|---|---|---|
| 19-container-image-optimization | 멀티스테이지 빌드, 최소 베이스(distroless·slim·alpine의 musl 함정), 레이어 순서와 빌드 캐시, `.dockerignore`, 이미지 크기가 pull·스케일 아웃·롤백 시간에 주는 영향 | 07-build-systems-and-reproducibility, os/34-containers-namespaces-cgroups | 2GB 이미지 → 새 노드에서 pull에 수십 초~수 분 걸려 스케일 아웃과 롤백이 늦어지고, 실패하면 `ImagePullBackOff`. `COPY . .`를 의존성 설치보다 앞에 둠 → 코드 한 줄만 바꿔도 의존성 레이어 전체를 다시 빌드. distroless에는 셸이 없어 `exec: "sh": executable file not found` 때문에 디버깅이 막힘 | 콘텐츠 주소 레이어(해시), 캐시 = 레이어 접두사 일치 | Docker 문서 "Multi-stage builds" [?] · GoogleContainerTools/distroless README [?] | 권장 | 신규 (연결: os/32 musl·glibc 증상) |

**배치 요약**: web-platform 8 · language 5 · reliability 6 · database 1 · engineering-practice 1 = **21개**(필수 4 · 권장 16 · 심화 1). 모두 반영하면 leaf 517 → 538.

---

## 3. `performance/` 영역을 새로 만들어야 하나

**결론: 만들지 않는다.** 성능 leaf는 각 층위 영역에 흩어 두고, **"성능 트랙"을 읽기 경로(뷰)로만** roadmap.md에 둔다. 트랙은 폴더가 아니라 leaf 목록이다.

근거:

1. **선행 의존이 층위 안에 닫혀 있다.** 신규 21개의 선행을 따라가면 GC 튜닝(24)은 `language/13`, 가상화(18)는 `web-platform/02·04`, 캐시 계층(41)은 `database/38`로 이어진다. `performance/`로 옮기면 거의 모든 leaf가 다른 영역을 선행으로 가리키게 된다. 그러면 §0.3의 층위 순서(Part 1→6)와 어긋나는 영역이 하나 생긴다.
2. **§0.1 원칙과 맞는다.** 커리큘럼은 "장애는 **주제 안에서** 가르친다"(Stevens)는 원칙을 따른다. 성능 저하도 장애의 한 형태다. GC 일시정지는 GC 옆에, layout thrashing은 렌더링 파이프라인 옆에 있을 때 ⚠ 칸이 메커니즘과 바로 이어진다.
3. **기존 성능 leaf가 이미 흩어져 있다.** `reliability/18~22`, `architecture/12~14`, `os/35`, `database/16·19·32·33`, `web-platform/08`이 그렇다. 새 영역을 만들면 이 leaf들을 옮길지 말지부터 다시 정해야 하고, 그 자체로 재편 churn이 된다. 옮기지 않으면 성능이 두 군데로 쪼개진다.
4. **표준 분류에도 독립 성능 영역이 없다.** CS2023에서 성능은 SF(System Fundamentals)의 한 주제로 들어가 있다 [?]. SWEBOK v4에서도 품질 속성의 하나다. 이 커리큘럼의 §0.6 대응표와도 맞는다.
5. **보완책**: 흩어 놓으면 "성능을 한 번에 공부하는 길"이 안 보인다. 이 약점은 아래 두 가지로 메운다.
   - `web-platform/`에 단원 "16.2 성능"(08·14~21), `language/`에 "6.3b 런타임 성능"(22~26)을 둔다. 영역 안에서는 한데 모인다.
   - roadmap.md에 **성능 트랙** 순서를 둔다: `reliability/35 → 18 → 19 → architecture/12·13·14 → os/35 → language/22·24·25 → reliability/36·37·39·40 → database/32·33·41 → reliability/20·21·38 → web-platform/08·14~21 → engineering-practice/19`.

**다시 판단해야 할 조건**: 이후 갭 리서치에서 성능 leaf가 더 늘어나 `reliability/` 11.3 단원이 15개를 넘는 경우, 또는 사용자가 "성능 엔지니어" 직무 트랙을 따로 원하는 경우에는 `performance/`를 신설하는 편이 낫다. 그때는 Gregg 『Systems Performance』 목차(방법론·관측·CPU·메모리·파일시스템·디스크·네트워크·클라우드·벤치마킹)를 뼈대로 삼는다 [?].

---

## 4. 확인하지 못한 것 (`[?]`)

- FOIT 블록 기간 "약 3초"의 브라우저별 현재 값(16).
- 가상화하지 않은 1만 행의 메모리 "수백 MB" 수치(18). 기기와 행 복잡도에 따라 다르다.
- React 재조정의 O(n) 휴리스틱과 일반 트리 편집 거리 O(n³)의 공식 문서 문구(19). 구 React 문서 "Reconciliation"에 있던 것으로 기억하지만 이번에 확인하지 못했다.
- Lighthouse 점수의 실행 간 변동 폭(21).
- HotSpot 계층 컴파일 공식 문서의 URL과 절(22). JIT 절은 JEP 483 외 1차 문서를 확인하지 않았다.
- 네이티브 이미지의 최고 처리량이 JIT보다 낮다는 일반화(23). PGO·버전에 따라 다르다.
- 1건씩 INSERT와 배치 INSERT의 속도 차이 수치(40). Redis Pipelining·PostgreSQL COPY 문서 제목은 기억에 의존했다.
- SnapStart 복원 뒤 고유 상태 복제 문제의 공식 문서 문구(38).
- Eclipse MAT, Docker, distroless, Clang ThinLTO, TinyLFU, Georges 외 2007, Gregg 2판 2장의 정확한 URL·장 번호.
- CS2023에서 성능이 SF KA 안에 있다는 점(§3 근거 4). CS2023 원문 KA 목록은 이번 작업에서 다시 열지 않았다.

## 5. 출처 (이번 작업의 WebSearch로 확인)

- web.dev: [Core Web Vitals 임계값 정의](https://web.dev/articles/defining-core-web-vitals-thresholds) · [Understand the critical path](https://web.dev/learn/performance/understanding-the-critical-path) · [Resource hints](https://web.dev/learn/performance/resource-hints) · [Optimize resource loading](https://web.dev/learn/performance/optimize-resource-loading) · [Responsive images](https://web.dev/learn/design/responsive-images) · [Preload responsive images](https://web.dev/articles/preload-responsive-images) · [Optimize CLS](https://web.dev/articles/optimize-cls) · [Optimize web fonts](https://web.dev/learn/performance/optimize-web-fonts) · [Optimize WebFont loading](https://web.dev/articles/optimize-webfont-loading) · [Optimize long tasks](https://web.dev/articles/optimize-long-tasks) · [Off-main-thread](https://web.dev/articles/off-main-thread) · [Virtualize long lists](https://web.dev/articles/virtualize-long-lists-react-window) · [Compositor-only properties](https://web.dev/articles/stick-to-compositor-only-properties-and-manage-layer-count) · [Performance budgets 101](https://web.dev/articles/performance-budgets-101) · [Budgets in build tools](https://web.dev/articles/incorporate-performance-budgets-into-your-build-tools)
- [react.dev memo](https://react.dev/reference/react/memo) · [react.dev useMemo](https://react.dev/reference/react/useMemo) · [patterns.dev Islands Architecture](https://www.patterns.dev/vanilla/islands-architecture/)
- [JEP 444 Virtual Threads](https://openjdk.org/jeps/444) · [JEP 483 AOT Class Loading & Linking](https://openjdk.org/jeps/483) · [OpenJDK JOL README](https://github.com/openjdk/jol/blob/master/README.md) · [Shipilëv JVM Anatomy Quark #18](https://shipilev.net/jvm/anatomy-quarks/18-scalar-replacement/) · [G1 GC Tuning (Oracle)](https://docs.oracle.com/javase/8/docs/technotes/guides/vm/gctuning/g1_gc_tuning.html) · [GraalVM Native Image Limitations](https://www.graalvm.org/22.1/reference-manual/native-image/Limitations/)
- [async-profiler](https://github.com/SAP/async-profiler) · [giltene/wrk2](https://github.com/giltene/wrk2) · [k6 Open and closed models](https://grafana.com/docs/k6/latest/using-k6/scenarios/concepts/open-vs-closed/) · [Gunther USL 요약(perfdynamics)](https://www.perfdynamics.com/Manifesto/USLscalability.pdf)
- [AWS Lambda 실행 환경 수명](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html) · [Lambda SnapStart](https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html) · [Redis client-side caching](https://redis.io/docs/latest/develop/reference/client-side-caching/) · [LLVM HowToBuildWithPGO](https://llvm.org/docs/HowToBuildWithPGO.html)
