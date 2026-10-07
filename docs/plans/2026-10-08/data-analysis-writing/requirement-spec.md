# 요구사항 명세서 — data-analysis-writing

> 작성일: 2026-10-08 · 작업 폴더: `docs/plans/2026-10-08/data-analysis-writing/` · 브랜치: `docs/data-analysis-writing`(docs/language-writing 068c845b에서 이어 만듦 — push는 이 영역을 마친 뒤 한 번 사용자에게 묻는다).
> 선행: data-engineering(17)·network-lb(1)·language(27), 모두 커밋·미push. 브리핑·도구는 data-engineering판을 이식.

## 0. 요구사항 원문 (인터뷰)

- 원문: "남은 커리큘럼도 전부 진행 계획에 넣어서 쭉 진행하도록 해보자"
- Q/A (2026-10-07): 순서 **네트워크 원고 1 → 언어 27 → 데이터 분석 28** · push **영역마다 커밋만, 마지막에 한 번 묻기** · 방식은 앞 영역과 같게(영역 밖 미작성 링크 교정, 출처 URL 사전 제공), 합의 auto · 동시 서브에이전트 ≤5("병렬로 순차처리").

## 1. 목표·대상 (필수)

- `cs/data-analysis/NN-slug/{1-question,2-summary,3-answer,metadata}.md` **28편**(커리큘럼 §18 01~28). 원고 없음 — 전부 신규.
  - 종합 2편(27 da-symptom-index·28 da-incidents)은 마지막.
- 영역 표 `cs/data-analysis/README.md` 재생성.
- 정합 단계에서 다른 영역 노트가 data-analysis 01~28을 "미작성"으로 가리키는 곳을 **링크만** 교정.

## 2. 경계·불변식 (필수)

- **I1 형식**: 7절 골격, Q/A 6~10, 제목 아래 머리말 없음, metadata 단계 `초안`, `흔한 오해:` 한 줄(선택).
- **I2 근거**: OpenIntro Statistics 4판(무료 PDF — 장·절 확인), Kohavi·Tang·Xu 2020(장 번호는 열 수 있는 목차로만, 아니면 `[?]`), Fabijan 외 KDD 2019, Ioannidis 2005, Dunning–Ertl t-digest, HdrHistogram, Wickham 2014, Wilke 온라인판, Hyndman–Athanasopoulos 3판 온라인, Wilson 외 2017, Downey Think Stats/Bayes, ASA 2016 p값 성명, Python `statistics` 문서, PostgreSQL 17 문서, 사고 원문(Squire 1988, Lazer 외 2014, Herndon 외 2013, PHE 2020-10). **확률·분포 기초는 math/07~09가 단일 출처**(링크). 기억으로 쓴 절·장·연도에는 반드시 `[?]`.
- **I3 커리큘럼 일치**: 각 행의 요지·선행·⚠·🔧·📚 전부, 선행 링크 실재 확인.
- **I4 기존 보존**: 다른 영역 노트 수정 금지(정합 단계 링크 교정만 예외 — 문장 의미 변경 금지).
- **I5 링크·트리**: 새로 깨는 링크 0, 리프에 md만.
- **I6 재현 안전**: 전용 일회용 `sn-da-w<NN>-*`(`--rm --pull never --cpus=2`, postgres는 바인드 마운트 없이 `docker exec -i … psql`, Java/Python은 `-u $(id -u):$(id -g) -e HOME=/tmp --network none`), 이미지는 있는 것만(postgres:17·python:3.12-slim·eclipse-temurin:21-jdk), pull·빌드·rmi·prune 금지, `docker create`/`rm` 대신 `--rm`만. 호스트 python3(표준 라이브러리) 가능, sudo·패키지 설치 금지(numpy·scipy·pandas 없음). 데이터는 합성(개인정보 금지), 저장소 루트 파일 금지.
- **I7 실험 근거 우선**: 편마다 실행 가능한 핵심 주장 1개 이상(종합 선택) — briefing §5 예시. 시뮬레이션은 시드·반복 수를 적는다.
- **I8 동시성**: 동시 서브에이전트 ≤5.

## 3. 기준소스 (필수)

- curriculum.md §18, `cs/data-analysis/README.md`, I2 출처, 관련 기존 노트(math/07·08·09·10·13·15, database/04·05·27, data-engineering/03·10·17, reliability 지표·백분위 노트, data-structure 스케치, algorithm 선택, domain-modeling/advanced/27-ab-assign)

## 4. 금지영역 (필수)

- data-analysis 밖 노트(정합 단계 링크 교정 제외 — 읽기만), 커리큘럼 본문(NEXT로), `check_new.py`·생성기, 생성 문서 수기 수정, 이 작업이 만들지 않은 컨테이너·볼륨·네트워크·이미지, I6의 금지 행위

## 5. 검증 방법 (필수)

- V1 check_new · V1b 사실 점검이 편당 실험 1개+ 재실행 · V2 Opus 사실 점검 · V3 codex(high) 2차 → 판정(출처 직접 열람) · V4 정합(math·database·data-engineering·reliability 겹치는 주제 + 영역 밖 링크, 종합 색인은 leaf 판정이 모두 끝난 뒤 재대조) · V5 웹 교차 40+, 링크 신규 깨짐 0, 영역 표 재생성, 정리 확인(sn-da 컨테이너 0)

## 6. stakes (필수)

- **중간** — 새 학습 자료 28편, 사실 오류(통계 정리의 전제·p값 해석·검정 절차·사고 수치) 위험. 문서라 되돌리기 쉬움.

## 7. 자율성

- [x] auto

## 8. load-bearing 가정

- **A1**: Python 3.12 표준 라이브러리(`statistics`·`random`·`math`)와 PostgreSQL 17로 필요한 통계 계산·시뮬레이션을 새 패키지 없이 할 수 있다(카이제곱·t 분포 꼬리는 직접 구현하거나 표 값과 대조).
- **A2**: WebSearch 한도 소진 — 브리핑에 1차 출처 URL을 미리 넣고 curl로 연다.

## 9. task 분해

| task | 목표 | acceptance |
|---|---|---|
| 01 | 브리핑 3종(data-engineering판 이식 + 통계 실험·출처) | 브리핑 |
| 02 | 집필(Opus 5워커: 01·02·03·04·06 / 05·07·08·09·10 / 11·12·13·20·21 / 14·15·22·25·26 / 16·17·18·19·23·24), 종합 27·28 후속 | 28 PASS |
| 03 | 사실 점검 + 실험 재실행(끝난 묶음부터, 동시 ≤5) | packet |
| 04 | codex 2차 → 판정 → 정합(영역 밖 링크 포함) → 웹 | V3~V5 |
| 05 | 영역 표·정리·커밋·(확인 후) push·log·NEXT·측정로그 | V5 |

## 승인 상태

- [x] 6칸
- [x] 합의: 사용자 답변(2026-10-07)
- [x] auto
