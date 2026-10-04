# 요구사항 명세서 — engineering-practice-writing

> 작성일: 2026-10-05 · 작업 폴더: `docs/plans/2026-10-05/engineering-practice-writing/` · 브랜치: main(3b190e5e, origin과 같음 — 웹 플랫폼 push 포함)에서 `docs/engineering-practice-writing`.
> 선행: network~api-design·web-platform(모두 main 반영·push). 브리핑·실험 규칙·도구는 api-design판을 재사용한다.
> **동시 실행 금지**: 같은 작업 트리에서 다른 실행이 이 영역을 진행하지 않는다는 전제(10-04에 다른 실행이 web-platform을 같은 트리에서 진행 — 끝난 뒤 이 실행이 push·인수). 착수·회수마다 `git log`·`git branch`·파일 mtime으로 흔적을 확인하고, 있으면 멈추고 사용자에게 묻는다.

## 0. 요구사항 원문 (인터뷰)

- 원문: "다음 작업하고 ai-engineering-from-scratch라는 … 리포 한번 확인해볼래? … 적용할만한게 있는 지도 분석해보면서 다음 작업을 하면 될꺼 같은데"
- 선행 조치: AIEFS 분석 보고서 `docs/plans/2026-10-04/aie-analysis/report.md`(L0) · 웹 플랫폼 로컬 커밋을 사용자 승인으로 main ff + push(c79e2d8b..3b190e5e)
- Q/A (2026-10-05): 영역 **엔지니어링 실천**(§17) · 기존 원고 6편 **보강 방식, 20편 전부** · 형식 개선 **용어 풀이 "흔한 오해" 한 줄 + 규칙↔검사기 대조표(보고만)** · 검증 **앞 영역과 같게, 합의 auto** · pgvector·AI 영역은 나중에(NEXT)

## 1. 목표·대상 (필수)

- `cs/engineering-practice/NN-slug/{1-question,2-summary,3-answer,metadata}.md` **20편**(커리큘럼 §17 01~20)
  - 보강 6편(원본은 그대로, 링크로 이어받음): 01 `engineering/agile-and-squad` · 14 `engineering/development-standards/quality-standards` · 15 `…/security-standards` · 16 `…/operational-standards` · 17 `…/legal-standards`(+`provisions.md`·`index.md`·`README.md`) · 18 `foundations/three-virtues`
  - 종합 2편(19 practice-symptom-index·20 practice-incidents)은 마지막.
- 영역 표 `cs/engineering-practice/README.md` 재생성: 20편 전부 `초안(Claude)`.
- 부속: **규칙↔검사기 대조표** — `cs/README.md` 「작성 규칙」의 규칙마다 `check_new.py`가 검사하는지 표로 정리(L0 보고, `docs/plans/2026-10-05/engineering-practice-writing/rules-vs-checker.md`). 검사기 수정은 하지 않는다(별도 합의).

## 2. 경계·불변식 (필수)

- **I1 형식**: 7절 골격, Q/A 6~10, 제목 아래 머리말·표식 없음, metadata 단계 `초안`. 용어 풀이에 헷갈리기 쉬운 용어만 `흔한 오해:` 한 줄(선택, 근거 있는 것만 — 새 절 금지).
- **I2 근거**: SWEBOK v4, SWE@G(9·10·16·18·23·24장 — abseil.io), DORA(dora.dev), Google eng-practices, ISO/IEC/IEEE 29148, Agile Manifesto, Pro Git(10장), trunkbaseddevelopment.com, Humble–Farley 『Continuous Delivery』, Fowler(TechnicalDebtQuadrant 등), Diátaxis, McConnell 『Software Estimation』, Reproducible Builds, Docker 문서, SEC 34-70694, Cloudflare 사후 보고서, 원본 노트. 책 원문을 못 열면 장 단위·`[?]`.
- **I3 커리큘럼 일치**: §17 각 행의 요지·⚠·🔧·📚 전부, 선행 링크 실재 확인.
- **I4 기존 보존**: 원본 노트·다른 영역 노트 수정 금지(링크만).
- **I5 링크·트리**: 새로 깨는 링크 0, 리프에 md만.
- **I6 재현 안전**: 전용 일회용 `sn-ep-w<NN>-*`(`--cpus=2`, `-u $(id -u):$(id -g) -e HOME=/tmp`), 이미지 **pull·rmi·prune 금지**(있는 것만). **이미지 빌드(08 등)는 허용** — 이미 있는 베이스 이미지로만, 태그 `sn-ep-*`, 끝나면 자기가 만든 이미지만 `docker rmi`·`docker builder prune` 금지. git 실험은 scratchpad의 일회용 저장소에서만(이 저장소 git 금지). 개인정보 금지(git 실험 author는 `Example <ex@example.invalid>`), 저장소 루트 파일 금지.
- **I7 실험 근거 우선**: 편마다 실행 가능한 핵심 주장 1개 이상을 실제 출력으로(19·20 선택) — 예: git 객체 모델(`git cat-file`·해시 재계산), force push 뒤 reflog 복구·유실, 3-way merge 충돌·잘못된 해결로 조용한 소실, 장수 브랜치 vs 짧은 브랜치 충돌 수, 리뷰 크기와 검토 시간(공개 데이터나 시뮬레이션 명시), 빌드 DAG 위상정렬·증분 빌드 캐시 적중·오염, 재현 가능 빌드(타임스탬프 → 해시 차이), 멀티스테이지·레이어 순서에 따른 이미지 크기·캐시 적중, DORA 지표 계산(일회용 git 이력), 3점 추정 몬테카를로, 라이선스 스캔, 문서 신선도(링크 깨짐·마지막 수정). 출력은 실제 실행만.

## 3. 기준소스 (필수)

- curriculum.md §17, `cs/engineering-practice/README.md`, I2 출처, §1 원본 노트, AIEFS 분석 보고서(형식 개선 근거)

## 4. 금지영역 (필수)

- engineering-practice 밖 노트(원본·다른 영역 — 읽기만), 커리큘럼 본문(NEXT로), `check_new.py`·생성기(대조표는 보고만)
- 생성 문서 수기 수정 · 이번 작업이 만들지 않은 컨테이너·볼륨·이미지

## 5. 검증 방법 (필수)

- V1 check_new · V1b 사실 점검이 편당 실험 1개+ 재실행 · V2 Opus 사실 점검 · V3 codex(high) 2차 리뷰(한도 남으면 codex, 한도 시 Opus 적대 리뷰) → 판정 · V4 정합(reliability·testing·security·software-design·api-design·원본 포함) · V5 웹 교차 24+, 링크 신규 깨짐 0, 영역 표 재생성, 정리 확인(컨테이너·자기 빌드 이미지 0)

## 6. stakes (필수)

- **중간** — 새 학습 자료 20편, 사실 오류(책 인용·도구 동작·사고 수치) 위험. 이미지 빌드는 자기 태그만 지워 되돌릴 수 있다.

## 7. 자율성

- [x] auto

## 8. load-bearing 가정

- **A1**: git 실험은 호스트 git(일회용 scratchpad 저장소)으로, 빌드 실험은 maven·node 이미지로, 이미지 실험은 기존 베이스(eclipse-temurin:21-jdk/jre, node:22-alpine 등)로 새 pull 없이 된다.
- **A2**: codex는 10-04 08:53 리셋 이후라 사용 가능 — 2차 리뷰 시점에 한도에 닿으면 Opus 대체(명세 V3).

## 9. task 분해

| task | 목표 | acceptance |
|---|---|---|
| 01 | 브리핑(api-design판 이식 + §17 실험 예시·이미지 빌드 규칙·흔한 오해 줄) + 규칙↔검사기 대조표 | 브리핑·대조표 |
| 02 | 집필(Opus 병렬 5, 워커당 3~4편), 종합 19·20 후속 | 20 PASS |
| 03 | 사실 점검 + 실험 재실행 | packet |
| 04 | 2차 리뷰(codex) → 판정 → 정합 → 웹 | V3~V5 |
| 05 | 영역 표·정리·커밋·(확인 후) push·log·NEXT(AI 영역 후보 포함)·측정로그 | V5 |

## 승인 상태

- [x] 6칸
- [x] 합의: 사용자 답변(2026-10-05)
- [x] auto
