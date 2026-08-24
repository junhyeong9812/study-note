# cs/development-standards/quality-standards — 품질 기준 (ISO/IEC 25010:2023) — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 원고: 내가 직접 쓴다(작성 예정). 본문 절은 원고, 「전체 흐름」「핵심 문장」은 원고 압축, 맨 아래 「[Claude 추가]」 절만 원고에 없던 내용.
> 상위 묶음: [development-standards](../README.md)

## 전체 흐름

<!-- 원고 완성 후 압축 -->

## 본문 (원고 — 골격 후보, 쓰면서 바꿔도 됨)

### 1. 이 기준이 답하려는 질문 — "좋은 소프트웨어"를 무엇으로 재는가
### 2. 제품 품질 모델(Product quality) — 9개 특성
<!-- 25010:2023 기준 9특성: Functional suitability · Performance efficiency · Compatibility · Interaction capability(구 Usability) · Reliability · Security · Maintainability · Flexibility(구 Portability) · Safety(2023 신설) -->
### 3. 각 특성의 하위 특성과 "내 코드에서 어떻게 드러나는가"
### 4. 사용 품질 모델(Quality in use) — 제품이 아니라 "쓰는 상황"을 재는 축
### 5. 2011판 → 2023판에서 바뀐 것 (Safety 추가, Usability→Interaction capability, Portability→Flexibility)
### 6. 현장에서 만나는 상황 — 요구사항·테스트·코드 리뷰에 이 특성을 어떻게 매핑하는가

## 핵심 문장

-

## 관련 자료 (공부 레퍼런스)

- **ISO/IEC 25010:2023** — Systems and software Quality Requirements and Evaluation (SQuaRE), Product quality model: https://www.iso.org/standard/78176.html (유료 표준 — 목차·개요는 무료)
- ISO/IEC 25019:2023 — Quality-in-use model(사용 품질이 25010에서 분리된 문서): https://www.iso.org/standard/78177.html
- ISO 25000 포털(SQuaRE 시리즈 개요·특성 설명): https://iso25000.com/index.php/en/iso-25000-standards/iso-25010
- 선행 주제: [solid-principles](../../solid-principles/) — Maintainability 특성과 연결

---

## [Claude 추가] 더 알면 좋은 것

> 원고 완성 후 작성. 복습 대상은 본문, 이 절은 확장 읽을거리.
