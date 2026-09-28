# 프로그래밍 언어·컴파일러 — `cs/language/` 커리큘럼

> **생성 문서** — `docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md` §6에서 `docs/plans/2026-09-28/cs-restructure/gen_area_readme.py`로 만든다. 직접 고치지 말고 커리큘럼을 고친 뒤 재실행한다.
> 번호 = 권장 학습 순서. 상태: `미작성` · `원고 있음` · `초안(Claude)` · `검수 완료`. ⚠ 깨지면·🔧·📚 세부는 커리큘럼 본문에 있다.
> 현황: 미작성 17 · 원고 있음 10 · 초안(Claude) 0 · 검수 완료 0

> **언어 중립 원리**만 둔다(문법 레퍼런스는 CS 밖 — §19 판정). 코드가 실행되기까지(어휘→구문→의미→코드), 타입, 메모리 관리, 동시성 모델, 의존성.
> 뼈대: Aho 외 『Compilers』(Dragon Book, 장 번호 `[?]`), Pierce 『TAPL』 [?], Jones 외 『The Garbage Collection Handbook』 [?], JSR-133(JMM), CS2023 FPL.

## 6.1 실행 모델과 컴파일 파이프라인

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 01 | `compile-interpret-jit` | 컴파일·인터프리트·바이트코드·JIT | 필수 | 원고 있음 | [../foundations/compiler-pipeline](../foundations/compiler-pipeline/) |
| 02 | `lexing-and-regular-languages` | 토큰화·정규식·유한 오토마타 | 필수 | 원고 있음 | [../foundations/compiler-pipeline](../foundations/compiler-pipeline/) |
| 03 | `parsing-grammars-ast` | BNF·CFG·재귀 하강·AST | 필수 | 원고 있음 | [../foundations/compiler-pipeline](../foundations/compiler-pipeline/) |
| 04 | `semantic-analysis-and-scopes` | 심벌 테이블·스코프·바인딩 | 권장 | 원고 있음 | [../foundations/compiler-pipeline](../foundations/compiler-pipeline/) · [../foundations/variables-and-memory](../foundations/variables-and-memory/) |
| 22 | `ir-and-optimization` | IR·SSA·인라이닝·데드 코드 제거·레지스터 할당 | 심화 | 미작성 | — |

## 6.2 타입·값·추상화

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 05 | `type-systems` | 정적/동적·강/약·명목/구조·제네릭·변성 | 필수 | 미작성 | — |
| 06 | `values-references-passing` | 값/참조, 전달 방식, 얕은/깊은 복사, 동일성 vs 동등성 | 필수 | 원고 있음 | [../foundations/variables-and-memory](../foundations/variables-and-memory/) |
| 07 | `scope-closures-first-class-functions` | 1급 함수·클로저·람다 | 권장 | 원고 있음 | [../foundations/variables-and-memory](../foundations/variables-and-memory/) |
| 08 | `error-handling-models` | 예외·에러 값·Result/Option·panic | 필수 | 미작성 | — |
| 17 | `dispatch-and-polymorphism-mechanics` | 정적/동적 디스패치·vtable·단형화·인라인 캐시 | 권장 | 미작성 | — |
| 18 | `functional-concepts` | 불변·순수 함수·고차 함수·지연 평가 | 권장 | 미작성 | — |

## 6.3 메모리 관리

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 09 | `memory-management-models` | 수동·참조 카운팅·추적 GC·소유권 | 필수 | 원고 있음 | [../foundations/variables-and-memory](../foundations/variables-and-memory/) |
| 10 | `garbage-collection` | mark-sweep·copying·세대·동시 GC(G1·ZGC) | 필수 | 미작성 | — |
| 13 | `language-memory-model` | happens-before·data race·volatile·final | 권장 | 미작성 | — |

## 6.3b 런타임 성능 (2026-09-28 추가)

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 11 | `gc-tuning-and-gc-logs` | 수집기 선택(처리량형 vs 지연형 — Parallel·G1·ZGC), 힙 크기와 일시정지 목표(`MaxGCPauseMillis`), GC 로그 읽기, 할당률과 승격률, 컨테이너 메모리 인지(`MaxRAMPercentage`) | 권장 | 미작성 | — |
| 12 | `object-layout-and-allocation-reduction` | 객체 헤더·압축 참조(compressed oops)·패딩, 박싱 비용, 객체 배열 vs 원시 배열, 탈출 분석과 스칼라 치환, TLAB, 할당률 줄이기, 객체 풀링 반패턴 | 권장 | 미작성 | — |
| 23 | `jit-tiered-compilation-and-warmup` | 계층 컴파일(인터프리터 → C1 → C2), 프로파일 수집, 인라이닝, OSR, 역최적화(deopt), 코드 캐시, 워밍업 전략 | 권장 | 미작성 | — |
| 24 | `aot-native-image-and-startup` | 닫힌 세계 가정의 AOT 네이티브 이미지(GraalVM), 리플렉션·프록시 설정, AOT 캐시(CDS·Leyden)로 시작 시간 줄이기, 최고 처리량과의 트레이드오프 | 권장 | 미작성 | — |
| 25 | `lto-pgo-and-binary-size` | 링크 타임 최적화(LTO·ThinLTO), 프로파일 기반 최적화(PGO), 링크 단계 데드 코드 제거, 심볼 제거(strip), 정적·동적 링크별 바이너리 크기 | 심화 | 미작성 | — |

## 6.4 동시성 모델

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 14 | `concurrency-models` | 스레드·액터·CSP·async/await·코루틴·가상 스레드 | 필수 | 미작성 | — |
| 15 | `gil-and-runtime-constraints` | GIL 같은 런타임 제약 | 권장 | 원고 있음 | [../foundations/process-thread](../foundations/process-thread/) |
| 16 | `concurrency-design-patterns` | Executor·스레드 풀(크기·큐·거부 정책)·Future/Promise 합성·Active Object·Monitor Object·Scoped Locking(RAII/try-with-resources)·Thread-Specific Storage·**Double-Checked Locking의 함정**·불변 스냅샷 + 원자 참조 교체 | 필수 | 미작성 | — |

## 6.5 빌드·생태계·선택

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 19 | `modules-and-dependency-resolution` | 모듈·패키지·semver·락파일 | 필수 | 미작성 | — |
| 20 | `undefined-behavior-and-memory-safety` | UB·경계 검사·메모리 안전 | 권장 | 원고 있음 | [../../languages/c-cpp-csharp.md](../../languages/c-cpp-csharp.md) |
| 21 | `language-choice-tradeoffs` | "틀렸을 때 어떻게 틀리는가"로 언어 고르기 | 권장 | 원고 있음 | [../../languages/README.md](../../languages/README.md) · [../../languages/c-cpp-csharp.md](../../languages/c-cpp-csharp.md) · [../../languages/go/언어-특성](../../languages/go/언어-특성/) · [../../languages/java/언어-특성](../../languages/java/언어-특성/) · [../../languages/kotlin/언어-특성](../../languages/kotlin/언어-특성/) · [../../languages/rust/언어-특성](../../languages/rust/언어-특성/) |

## 6.6 영역 마감

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 26 | `pl-symptom-index` | 역색인: `NoSuchMethodError`·`ClassCastException`·`NullPointerException`·`StackOverflowError`·`GC overhead`·정규식 CPU 100%·async 정지 | 필수 | 미작성 | — |
| 27 | `pl-incidents` | 실사건: Cloudbleed(2017, 생성된 파서 버퍼 오버런) · Heartbleed(2014, 경계 검사 누락 — 보안 관점은 security/30) · left-pad(2016, 의존성 제거로 빌드 연쇄 실패) | 권장 | 미작성 | — |
