# 테스트 — `cs/testing/` 커리큘럼

> **생성 문서** — `docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md` §14에서 `docs/plans/2026-09-28/cs-restructure/gen_area_readme.py`로 만든다. 직접 고치지 말고 커리큘럼을 고친 뒤 재실행한다.
> 번호 = 권장 학습 순서. 상태: `미작성` · `원고 있음` · `초안(Claude)` · `검수 완료`. ⚠ 깨지면·🔧·📚 세부는 커리큘럼 본문에 있다.
> 현황: 미작성 21 · 원고 있음 0 · 초안(Claude) 0 · 검수 완료 0

> 기존 보유 0 — **갭 최대**. 왜·무엇을 → 단위 테스트의 질 → 테스트 더블·학파 → TDD → 설계 기법 → 통합·계약 → 고급 기법 → 불안정성.
> 뼈대: Google 『Software Engineering at Google』(이하 SWE@G — 11·12·13·14장), Khorikov 『Unit Testing Principles, Practices, and Patterns』, Beck 『TDD by Example』·"Canon TDD"(2023), Fowler "Mocks Aren't Stubs", Meszaros 『xUnit Test Patterns』, Feathers 『Working Effectively with Legacy Code』.

## 주제 목록

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 01 | `why-test-and-pyramid` | 테스트의 목적·피라미드·크기와 범위 | 필수 | 미작성 | — |
| 02 | `good-unit-tests` | 좋은 테스트 4기둥(회귀 방지·리팩터링 내성·빠른 피드백·유지보수성), AAA | 필수 | 미작성 | — |
| 03 | `test-doubles` | Dummy·Fake·Stub·Spy·Mock | 필수 | 미작성 | — |
| 04 | `classical-vs-london` | 고전파 vs 런던파(상태 검증 vs 상호작용 검증) | 권장 | 미작성 | — |
| 05 | `tdd` | 테스트 목록 → 하나씩 → 통과 → 리팩터링 | 필수 | 미작성 | — |
| 06 | `outside-in-tdd-and-acceptance-tests` | 이중 루프 TDD(인수 테스트 → 단위 테스트), Walking Skeleton, 인수 테스트·BDD(Given-When-Then)의 추상화 수준, 협력 객체 발견을 위한 mock | 권장 | 미작성 | — |
| 07 | `test-design-techniques` | 동치 분할·경계값·결정 테이블·상태 전이·쌍 조합 | 필수 | 미작성 | — |
| 08 | `integration-tests-real-dependencies` | 실제 DB·브로커로 통합 테스트(Testcontainers) | 필수 | 미작성 | — |
| 09 | `flaky-tests` | 불안정 테스트의 원인(시간·순서·동시성·공유 상태·네트워크) | 필수 | 미작성 | — |
| 10 | `testing-time-and-concurrency` | 시계 주입·결정적 스케줄·동시성 테스트 | 권장 | 미작성 | — |
| 11 | `test-data-and-fixtures` | 픽스처·빌더·오브젝트 마더·격리 | 권장 | 미작성 | — |
| 12 | `test-smells-and-xunit-patterns` | 테스트 스멜(Obscure·Fragile·Slow Test, Assertion Roulette, Mystery Guest, Conditional Test Logic, Test Code Duplication)과 처방 패턴(Humble Object·Custom Assertion·Parameterized Test·Test-Specific Subclass·Delegated Setup) | 권장 | 미작성 | — |
| 13 | `contract-testing` | 소비자 주도 계약 테스트 | 권장 | 미작성 | — |
| 14 | `property-based-testing` | 성질·생성기·축소(shrinking) | 권장 | 미작성 | — |
| 15 | `mutation-testing` | 변이 주입으로 테스트의 판별력 측정 | 권장 | 미작성 | — |
| 16 | `coverage-and-its-limits` | 라인·분기·조건 커버리지의 의미와 한계 | 권장 | 미작성 | — |
| 17 | `characterization-tests-legacy` | 레거시의 안전망 — 특성 테스트·이음새(seam) 찾기. 변경 기법(sprout·wrap·의존 끊기)은 software-design/51로 넘긴다 | 권장 | 미작성 | — |
| 18 | `e2e-and-ui-testing` | E2E·UI 테스트의 범위와 비용 | 권장 | 미작성 | — |
| 19 | `testing-in-production` | 합성 모니터링·카나리 분석·섀도 트래픽 | 심화 | 미작성 | — |
| 20 | `test-symptom-index` | 역색인: CI 가끔 실패, 리팩터링마다 대량 실패, 초록인데 운영 장애, 테스트 느림, 커버리지 높은데 버그 | 필수 | 미작성 | — |
| 21 | `test-incidents` | 실사건: Apple `goto fail`(2014, 중복 goto로 서명 검증 우회 — 음성 테스트 부재) · CrowdStrike(2024, 콘텐츠 검증기 결함과 단계적 배포 부재 — 운영 관점은 reliability/53) | 권장 | 미작성 | — |
