# 엔지니어링 실천 — `cs/engineering-practice/` 커리큘럼

> **생성 문서** — `docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md` §17에서 `scripts/notes/gen_area_readme.py`로 만든다. 직접 고치지 말고 커리큘럼을 고친 뒤 재실행한다.
> 번호 = 권장 학습 순서. 상태: `미작성` · `원고 있음` · `초안(Claude)` · `검수 완료`. ⚠ 깨지면·🔧·📚 세부는 커리큘럼 본문에 있다.
> 현황: 미작성 0 · 원고 있음 0 · 초안(Claude) 20 · 검수 완료 0

> SWEBOK v4의 Requirements·Configuration Management·Process·Management·Professional Practice·Economics KA를 개발자 시점으로 압축. 기존 agile-and-squad·development-standards(4축)·three-virtues가 들어온다.
> 뼈대: SWEBOK v4, SWE@G 9·16·18·23·24장(16·18 `[?]`), DORA, Google eng-practices, ISO/IEC/IEEE 29148.

## 주제 목록

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 01 | `lifecycle-and-agile` | 개발 수명 주기·애자일·스쿼드 | 필수 | 초안(Claude) | [01-lifecycle-and-agile](01-lifecycle-and-agile/) · [../engineering/agile-and-squad](../engineering/agile-and-squad/) |
| 02 | `requirements-engineering` | 요구 도출·명세·검증·추적 | 권장 | 초안(Claude) | [02-requirements-engineering](02-requirements-engineering/) |
| 03 | `version-control-and-git-internals` | 스냅샷·객체 모델·브랜치·병합 | 필수 | 초안(Claude) | [03-version-control-and-git-internals](03-version-control-and-git-internals/) |
| 04 | `branching-strategies` | git-flow vs trunk-based·피처 플래그 | 필수 | 초안(Claude) | [04-branching-strategies](04-branching-strategies/) |
| 05 | `code-review` | 리뷰의 목적·기준·크기 | 필수 | 초안(Claude) | [05-code-review](05-code-review/) |
| 06 | `ci-cd-pipelines` | 지속적 통합·전달·배포 파이프라인 | 필수 | 초안(Claude) | [06-ci-cd-pipelines](06-ci-cd-pipelines/) |
| 07 | `build-systems-and-reproducibility` | 증분 빌드·캐시·재현 가능 빌드 | 권장 | 초안(Claude) | [07-build-systems-and-reproducibility](07-build-systems-and-reproducibility/) |
| 08 | `container-image-optimization` | 멀티스테이지 빌드, 최소 베이스(distroless·slim·alpine의 musl 함정), 레이어 순서와 빌드 캐시, `.dockerignore`, 이미지 크기가 pull·스케일 아웃·롤백 시간에 주는 영향 | 권장 | 초안(Claude) | [08-container-image-optimization](08-container-image-optimization/) |
| 09 | `dora-metrics` | 배포 빈도·리드 타임·변경 실패율·복구 시간·재작업률 | 권장 | 초안(Claude) | [09-dora-metrics](09-dora-metrics/) |
| 10 | `technical-debt` | 기술부채 4사분면·상환 전략 | 권장 | 초안(Claude) | [10-technical-debt](10-technical-debt/) |
| 11 | `documentation-practices` | 문서 유형(튜토리얼·방법·레퍼런스·설명)·문서 신선도 | 권장 | 초안(Claude) | [11-documentation-practices](11-documentation-practices/) |
| 12 | `estimation-and-planning` | 추정·불확실성 원뿔·계획 | 권장 | 초안(Claude) | [12-estimation-and-planning](12-estimation-and-planning/) |
| 13 | `build-vs-buy-and-adoption` | 직접 만들기 vs SaaS·OSS 도입: 핵심·범용 판별, 총소유비용(운영·온콜 포함), 종료 비용·데이터 반출, 벤더 종속, OSS 건강도(유지보수자·라이선스) | 권장 | 초안(Claude) | [13-build-vs-buy-and-adoption](13-build-vs-buy-and-adoption/) |
| 14 | `quality-standards` | 품질 표준(코드 품질 기준) | 권장 | 초안(Claude) | [14-quality-standards](14-quality-standards/) · [../engineering/development-standards/quality-standards](../engineering/development-standards/quality-standards/) |
| 15 | `security-standards` | 보안 표준(개발 보안 기준) | 권장 | 초안(Claude) | [15-security-standards](15-security-standards/) · [../engineering/development-standards/security-standards](../engineering/development-standards/security-standards/) |
| 16 | `operational-standards` | 운영 표준 | 권장 | 초안(Claude) | [16-operational-standards](16-operational-standards/) · [../engineering/development-standards/operational-standards](../engineering/development-standards/operational-standards/) |
| 17 | `legal-standards` | 법률 표준(개인정보·라이선스 등) | 권장 | 초안(Claude) | [17-legal-standards](17-legal-standards/) · [../engineering/development-standards/legal-standards](../engineering/development-standards/legal-standards/) · [../index.md](../index.md) · [../README.md](../README.md) |
| 18 | `engineering-virtues` | 게으름·조급함·오만 — 개발자 태도 | 심화 | 초안(Claude) | [18-engineering-virtues](18-engineering-virtues/) · [../foundations/three-virtues](../foundations/three-virtues/) |
| 19 | `practice-symptom-index` | 역색인: 머지 지옥, CI 불신, 배포 공포, 리뷰 병목, "이건 왜 이렇게 했지?" | 필수 | 초안(Claude) | [19-practice-symptom-index](19-practice-symptom-index/) |
| 20 | `practice-incidents` | 실사건: Knight Capital(2012-08-01, 수동 배포 누락 서버 + 재사용된 플래그로 45분 4.4억 달러 손실) · Cloudflare WAF 규칙 전역 즉시 배포(2019-07-02 — 알고리즘 관점은 algorithm/43) | 권장 | 초안(Claude) | [20-practice-incidents](20-practice-incidents/) |
