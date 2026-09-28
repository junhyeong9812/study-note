# CS 수학 — `cs/math/` 커리큘럼

> **생성 문서** — `docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md` §1에서 `docs/plans/2026-09-28/cs-restructure/gen_area_readme.py`로 만든다. 직접 고치지 말고 커리큘럼을 고친 뒤 재실행한다.
> 번호 = 권장 학습 순서. 상태: `미작성` · `원고 있음` · `초안(Claude)` · `검수 완료`. ⚠ 깨지면·🔧·📚 세부는 커리큘럼 본문에 있다.
> 현황: 미작성 16 · 원고 있음 1 · 초안(Claude) 0 · 검수 완료 0

> 백엔드에서 수학이 "틀리면" 보이는 곳: 정렬 예외, 음수 샤드 인덱스, ID 충돌, 부동소수 합계 불일치, 이용률 80% 절벽. 증명보다 **불변식·확률·큐잉**을 우선한다.
> 뼈대: MIT 6.042 『Mathematics for Computer Science』(Lehman·Leighton·Meyer, 이하 MCS — 장 번호 `[?]`), CLRS 3판 부록, OpenIntro 3·4장(확률 부분).

## 1.1 논리·증명·관계

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 01 | `propositional-logic` | 명제·술어 논리, 드모르간, 조건문의 부정 | 필수 | 미작성 | — |
| 02 | `induction-and-invariants` | 수학적 귀납과 루프 불변식 — 코드 정확성 논증의 기본 도구 | 필수 | 미작성 | — |
| 03 | `sets-relations-orders` | 집합·함수·동치관계·부분/전순서 | 필수 | 미작성 | — |

## 1.2 이산 구조·세기

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 04 | `graph-theory-basics` | 그래프·트리·DAG·연결성·사이클의 정의와 성질 | 필수 | 미작성 | — |
| 05 | `counting-and-birthday-bound` | 경우의 수·비둘기집·이항계수·생일 한계 | 필수 | 미작성 | — |
| 06 | `recurrences-and-asymptotics` | 점화식·급수·로그 — 마스터 정리까지 | 필수 | 미작성 | — |
| 11 | `modular-arithmetic` | 모듈러·GCD·소수·모듈러 역원·빠른 거듭제곱 | 권장 | 미작성 | — |

## 1.3 확률

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 07 | `probability-and-bayes` | 확률 공리·조건부 확률·독립·베이즈 정리 | 필수 | 미작성 | — |
| 08 | `expectation-variance-tails` | 기댓값 선형성·분산·꼬리 부등식(마르코프·체비셰프·체르노프) | 필수 | 미작성 | — |
| 09 | `common-distributions` | 균등·기하·이항·포아송·지수·정규·멱법칙(Zipf) | 권장 | 미작성 | — |
| 12 | `randomness-and-prng` | 의사난수·시드·CSPRNG·셔플·샘플링 | 권장 | 미작성 | — |

## 1.4 선형대수·정보·수치·큐잉

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 10 | `queueing-and-littles-law` | L=λW, M/M/1, 이용률과 대기시간의 비선형 관계 | 필수 | 원고 있음 | [../systems/server-design/01-scaling-principles.md](../systems/server-design/01-scaling-principles.md) |
| 13 | `linear-algebra-essentials` | 벡터·행렬·내적·노름·코사인 유사도 | 권장 | 미작성 | — |
| 14 | `information-theory-basics` | 엔트로피·부호화·압축 한계·오류 검출/정정 부호 | 권장 | 미작성 | — |
| 15 | `numerical-stability` | 부동소수 오차 누적·파국적 상쇄·Kahan 합 | 권장 | 미작성 | — |

## 1.5 영역 마감

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 16 | `math-symptom-index` | 증상→원인 역색인: 정렬 계약 위반 예외, 음수 모듈러, 간헐 ID 충돌, 합계 불일치, 이용률 절벽 | 필수 | 미작성 | — |
| 17 | `math-incidents` | 실사건: Debian OpenSSL PRNG(2008, 키 공간 32,767개로 축소) · Java 7 TimSort 계약 위반 예외 대량 발생 · TimSort 자체 버그의 형식 검증 발견(de Gouw 외 2015) | 권장 | 미작성 | — |
