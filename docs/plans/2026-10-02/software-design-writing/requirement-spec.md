# 요구사항 명세서 — software-design-writing

> 작성일: 2026-10-02 · 작업 폴더: `docs/plans/2026-10-02/software-design-writing/` · 브랜치: reliability 커밋 뒤 `docs/software-design-writing`(그전까지 미추적).
> 선행: network·os·database·distributed(완료·push d2733634), reliability(`docs/plans/2026-10-01/reliability-writing/`, 2차 리뷰 진행 중). 브리핑·실험 규칙·도구를 재사용한다.

## 0. 요구사항 원문 (인터뷰)

- 원문: "다음 진행하자"
- Q/A (2026-10-02, 2026-10-01 인터뷰 연장): 영역 **소프트웨어 설계**(`cs/software-design/`, 커리큘럼 §12) · 검증 **운영·신뢰성과 같게**(실험 근거 우선 I7·Docker 재현 허용·기존 노트 새 leaf 보강·codex 한도 시 Opus 대체·개인정보 금지·이미 있던 이미지 rmi 금지) · **명세 합의·auto를 인터뷰에서 함께 받음** · 분산 push 승인(함께 받음)

## 1. 목표·대상 (필수)

- `cs/software-design/NN-slug/{1-question,2-summary,3-answer,metadata}.md` **56편**(커리큘럼 §12 01~56)
  - 보강 7편(원본은 그대로, 링크로 이어받음): 06 `engineering/clean-code` · 20 `foundations/oop-basics` · 22 `engineering/solid-principles` · 27 `engineering/design-patterns-gof` · 37 `systems/architecture-styles` · 46 `engineering/engineering-axes` · 49 `systems/multi-tenancy`
  - 종합 2편(55 design-symptom-index·56 design-incidents)은 마지막.
- 영역 표 `cs/software-design/README.md` 재생성: 56편 전부 `초안(Claude)`.

## 2. 경계·불변식 (필수)

- **I1 형식**: 7절 골격, Q/A 6~10, 머리말·표식 없음, metadata 단계 `초안`.
- **I2 근거**: APOSD 2판, Fowler 『Refactoring』 2판·refactoring.com·martinfowler.com, Martin 『Clean Architecture』, GoF, Parnas 1972, Beck 『Tidy First?』, Meyer DbC, Page-Jones/Weirich connascence(connascence.io), Kerievsky 『Refactoring to Patterns』, Feathers 『Working Effectively with Legacy Code』, Tornhill 『Your Code as a Crime Scene』, McCabe 1976, ISO/IEC 25010:2023, SWEBOK v4, 12-factor, Nygard ADR, ArchUnit·jMolecules 등 문서·소스. 책 원문을 못 열면 장 단위·`[?]`(목차·출판사 발췌로 확인한 범위만 단정). 확인 못 하면 `[?]`.
- **I3 커리큘럼 일치**: §12 각 행의 요지·⚠(스멜·변경 시 증상)·🔧·📚 전부, 선행 링크.
- **I4 기존 보존**: 원본·다른 영역 노트 수정 금지.
- **I5 링크·트리**: 새로 깨는 링크 0, 리프에 md만.
- **I6 재현 안전**: reliability 규칙 그대로(전용 일회용 `sn-sd-w<NN>-*`, `--cpus=2`, 이번에 처음 받은 이미지만 rmi, 개인정보 금지, 루트 파일 금지).
- **I7 실험 근거 우선 — 설계 영역 해석**: "깨지면"이 변경 비용·결합으로 보이므로, 실험은 **코드 비교 측정**으로 한다 — 같은 요구 변경을 두 설계에 적용해 바뀐 파일·줄·클래스 수(git diff --stat), 의존 그래프(jdeps·ArchUnit 결과), 순환 복잡도·인지 복잡도(도구 출력), 테스트 작성 비용(필요 목 수), 실행 결과(예: null/Optional 예외 경로, 불변 객체 공유 버그, 프록시 self-invocation으로 @Transactional 미적용, 데코레이터·체인 순서). 출력은 실제 실행·도구 결과만. 편마다 1개 이상(종합 55·56 제외), 실험이 과한 주장은 1차 출처로 대신하고 밝힌다.

## 3. 기준소스 (필수)

- curriculum.md §12, `cs/software-design/README.md`, I2 출처, §1 원본 노트

## 4. 금지영역 (필수)

- software-design 밖 노트(진행 중인 `cs/reliability/**` 포함 — 읽기만), 원본 노트, 커리큘럼 본문(NEXT로)
- 생성 문서 수기 수정 · 이번 작업이 만들지 않은 컨테이너·볼륨·이미지

## 5. 검증 방법 (필수)

- V1 check_new · V1b 사실 점검이 편당 실험 1개+ 재실행 · V2 Opus 사실 점검 · V3 codex(high) 2차 리뷰, 한도 시 Opus 적대 리뷰 → 판정 · V4 정합(reliability·distributed·domain-modeling 선행 포함) · V5 웹 교차 24+, 링크 신규 깨짐 0, README 재생성, 정리 확인

## 6. stakes (필수)

- **중간** — 새 학습 자료 56편, 사실 오류(책 인용·도구 기본값) 위험.

## 7. 자율성

- [x] auto

## 8. load-bearing 가정

- **A1**: 설계 실험은 대부분 JDK 21 단일 파일·소규모 Maven 프로젝트(temurin·maven 이미지, 이미 있음) + git으로 diff를 재는 방식으로 된다. 외부 도구(ArchUnit·PMD 등)는 maven으로 scratchpad에 받는다.
- **A2**: reliability 2차 리뷰와 codex 한도를 나눠 쓴다 — 한도면 Opus 대체.

## 9. task 분해

| task | 목표 | acceptance |
|---|---|---|
| 01 | 브리핑(reliability판 이식 + 설계 실험 예시) | 브리핑 |
| 02 | 집필(Opus 병렬 10, 워커당 5~6편), 종합 55·56 후속 | 56 PASS |
| 03 | 사실 점검 + 실험 재실행 | packet |
| 04 | 2차 리뷰 → 판정 → 정합 → 웹 | V3~V5 |
| 05 | README·정리·커밋·(확인 후) push·log·NEXT·측정로그 | V5 |

## 승인 상태

- [x] 6칸
- [x] 합의: 인터뷰에서 영역·검증·명세 합의를 함께 받음(2026-10-02)
- [x] auto
