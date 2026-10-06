# 요구사항 명세서 — math-writing

> 작성일: 2026-10-07 · 작업 폴더: `docs/plans/2026-10-07/math-writing/` · 브랜치: main(origin/main 064707b6 + 로컬 log 커밋 1)에서 `docs/math-writing`.
> 선행: security-writing(30편, push 064707b6). 브리핑·도구는 dsa-remaining/security판을 재사용한다.

## 0. 요구사항 원문 (인터뷰)

- 원문: "다음 주제도 진행해보자"
- Q/A (2026-10-07): 영역 **수학 17편**(Part 0 기본기, 다른 영역의 "math 미작성" 표기 약 50곳) · 진행 **앞 영역과 같게(원고 보강, 영역 밖 미작성 링크 교정 포함), 합의 auto**

## 1. 목표·대상 (필수)

- `cs/math/NN-slug/{1-question,2-summary,3-answer,metadata}.md` **17편**(커리큘럼 §1 01~17).
  - 보강 1편: 10-queueing-and-littles-law ← 원고 `cs/systems/server-design/01-scaling-principles.md`(읽기만, 해당 절)
  - 종합 2편(16 symptom-index·17 incidents)은 마지막.
- 영역 표 `cs/math/README.md` 재생성(17편 `초안(Claude)`).
- 정합 단계에서 다른 영역 노트가 math 01~17을 "미작성"·math README로 가리키는 곳을 **링크만** 교정.

## 2. 경계·불변식 (필수)

- **I1 형식**: 7절 골격, Q/A 6~10, 제목 아래 머리말 없음, metadata 단계 `초안`, `흔한 오해:` 한 줄(선택).
- **I2 근거**: MIT 6.042 MCS(Lehman·Leighton·Meyer, OCW PDF — 장 번호 확인), CLRS 3판(부록 A·C, 3·4장), OpenIntro Statistics 3·4장, Sedgewick 『Algorithms』, Knuth TAOCP 2권(난수), Shannon 1948, Hamming 1950, Goldberg 1991 "What Every Computer Scientist Should Know About Floating-Point Arithmetic", Higham 『Accuracy and Stability』, Kahan 1965, Little 1961, Kleinrock 『Queueing Systems』, Harchol-Balter 『Performance Modeling』, MIT 18.06(Strang), JLS(§15.17.3 나머지, §4.2), Java·Python 문서, 사고 원문(Debian DSA-1571, de Gouw 외 2015 CAV, JDK 버그). 책 본문을 못 열면 장 단위·`[?]`.
- **I3 커리큘럼 일치**: 각 행의 요지·선행·⚠·🔧·📚 전부, 선행 링크 실재 확인(자료구조·알고리즘은 커리큘럼 번호 ≠ 폴더 번호 — 대응표 사용).
- **I4 기존 보존**: 원고·다른 영역 노트 수정 금지(정합 단계의 링크 교정만 예외 — 문장 의미 변경 금지).
- **I5 링크·트리**: 새로 깨는 링크 0, 리프에 md만.
- **I6 재현 안전**: 전용 일회용 `sn-math-w<NN>-*`(`--rm --pull never --cpus=2 -u $(id -u):$(id -g) -e HOME=/tmp`, `--network none`), 이미지는 있는 것만(eclipse-temurin:21-jdk, python:3.12-slim), pull·빌드·rmi·prune 금지. 호스트 python3(표준 라이브러리만)·gcc 가능, 패키지 설치 금지. 개인정보 금지, 저장소 루트 파일 금지.
- **I7 실험 근거 우선**: 편마다 실행 가능한 핵심 주장 1개 이상(종합 선택) — 예: 드모르간 위반으로 권한 검사 우회 재현(진리표 전수), 루프 불변식 assert, `equals` 비대칭 → HashSet 중복·비교자 추이성 위반 예외, 위상정렬 사이클 탐지, 32비트 ID 생일 충돌 실측 vs 근사식, `-7 % 3` Java/Python 차이·`floorMod`·`Math.abs(MIN_VALUE)`, 점화식 호출 수 측정, 기저율 시뮬레이션(오탐 비율), 꼬리 부등식 vs 실측, 분포 표본(포아송 vs 버스트·Zipf 캐시 적중률), 같은 시드 지터 동기화·Fisher–Yates 편향 비교, 행/열 순회 캐시 효과·코사인 정규화, 엔트로피·CRC·해밍 코드, 부동소수 합산 순서·Kahan, M/M/1 시뮬레이션 대기 ∝ ρ/(1−ρ). 출력은 실제 실행만, 시뮬레이션은 시뮬레이션이라고 명시.

## 3. 기준소스 (필수)

- curriculum.md §1, `cs/math/README.md`, I2 출처, 원고 `cs/systems/server-design/01-scaling-principles.md`, 관련 기존 노트(algorithm/12·33·39·40, security/09·16, data-structure 대응표, reliability 큐잉·지연 노트)

## 4. 금지영역 (필수)

- math 밖 노트(정합 단계 링크 교정 제외 — 읽기만), 커리큘럼 본문(NEXT로), `check_new.py`·생성기, 생성 문서 수기 수정, 이 작업이 만들지 않은 컨테이너·이미지

## 5. 검증 방법 (필수)

- V1 check_new · V1b 사실 점검이 편당 실험 1개+ 재실행 · V2 Opus 사실 점검 · V3 codex(high) 2차 → 판정 · V4 정합(algorithm·data-structure·security·reliability 겹치는 주제 + 영역 밖 링크) · V5 웹 교차 24+, 링크 신규 깨짐 0, 영역 표 재생성, 정리 확인(sn-math 컨테이너 0)

## 6. stakes (필수)

- **중간** — 새 학습 자료 17편, 사실 오류(공식·정리 전제·수치) 위험. 문서라 되돌리기 쉬움.

## 7. 자율성

- [x] auto

## 8. load-bearing 가정

- **A1**: 실험은 Java 21(JDK만)·python 표준 라이브러리·gcc로 새 패키지 없이 된다(numpy 없음 — 행렬·분포는 직접 구현).
- **A2**: codex 사용 가능 — 한도 시 Opus 대체.

## 9. task 분해

| task | 목표 | acceptance |
|---|---|---|
| 01 | 브리핑 3종(dsa/security판 이식 + 수학 실험 예시) | 브리핑 |
| 02 | 집필(Opus 병렬 4, 워커당 3~4편), 종합 16·17 후속 | 17 PASS |
| 03 | 사실 점검 + 실험 재실행 | packet |
| 04 | codex 2차 → 판정 → 정합(영역 밖 링크 포함) → 웹 | V3~V5 |
| 05 | 영역 표·정리·커밋·(확인 후) push·log·NEXT·측정로그 | V5 |

## 승인 상태

- [x] 6칸
- [x] 합의: 사용자 답변(2026-10-07)
- [x] auto
