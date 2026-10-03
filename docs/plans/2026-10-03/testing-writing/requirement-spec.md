# 요구사항 명세서 — testing-writing

> 작성일: 2026-10-03 · 작업 폴더: `docs/plans/2026-10-03/testing-writing/` · 브랜치: main(07f855e3, origin과 같음)에서 `docs/testing-writing`.
> 선행: network·os·database·distributed·reliability·software-design·domain-modeling(모두 main 반영·push). 브리핑·실험 규칙·도구는 domain-modeling판을 재사용한다.
> **동시 실행 금지**: 같은 작업 트리에서 다른 실행이 이 영역을 진행하지 않는다는 전제(10-01~03에 같은 세션의 다른 실행이 병렬로 영역을 진행한 이력). 착수·회수마다 `git log`·`git branch`·파일 mtime으로 다른 실행의 흔적을 확인하고, 있으면 멈추고 사용자에게 묻는다.

## 0. 요구사항 원문 (인터뷰)

- 원문: "테스트 진행하고 하기 전에 우선 스터디 노트 내용들 전부 main에 머지하고 진행시작하자"
- 사전 조치: 모든 로컬·원격 브랜치가 main에 포함됨을 확인(미병합 0) · 남은 dm push 기록 1줄을 `docs/dm-push-record` → main ff(07f855e3) → push(사용자 승인)
- Q/A (2026-10-03): 영역 **테스트**(`cs/testing/`, 커리큘럼 §14) · 검증 **앞 영역과 같게** · **명세 합의, auto** · dm 기록 커밋 지금 push

## 1. 목표·대상 (필수)

- `cs/testing/NN-slug/{1-question,2-summary,3-answer,metadata}.md` **21편**(커리큘럼 §14 01~21, 기존 노트 0 — 전부 신규)
  - 종합 2편(20 test-symptom-index·21 test-incidents)은 마지막.
- 영역 표 `cs/testing/README.md` 재생성(생성기): 21편 전부 `초안(Claude)`.

## 2. 경계·불변식 (필수)

- **I1 형식**: 7절 골격, Q/A 6~10, 제목 아래 머리말·표식 없음, metadata 단계 `초안`.
- **I2 근거**: SWE@G(11·12·13·14장, abseil.io 온라인판), Khorikov 『Unit Testing PPP』, Beck 『TDD by Example』·"Canon TDD"(2023), Fowler "Mocks Aren't Stubs"·"TestPyramid"·"ContractTest"·"Eradicating Non-Determinism in Tests", Meszaros 『xUnit Test Patterns』(xunitpatterns.com), Feathers 『WELC』, Freeman–Pryce 『GOOS』, ISTQB CTFL 4.0 syllabus, Claessen–Hughes 2000, Jia–Harman 2011, Luo 외 FSE 2014, Google Testing Blog, 제품 문서·소스(JUnit 5·Mockito·AssertJ·Testcontainers·Pact·jqwik·PIT·JaCoCo·k6 등), CVE-2014-1266·CrowdStrike PIR/RCA. 책 원문을 못 열면 장 단위·`[?]`.
- **I3 커리큘럼 일치**: §14 각 행의 요지·⚠·🔧·📚 전부, 선행 링크(software-design·os·reliability·math·api-design 실재 경로 확인).
- **I4 기존 보존**: 다른 영역 노트 수정 금지(링크만).
- **I5 링크·트리**: 새로 깨는 링크 0, 리프에 md만.
- **I6 재현 안전**: 전용 일회용 컨테이너 `sn-ts-w<NN>-*`(`--cpus=2`, 포트 미개방 또는 127.0.0.1), 끝나면 `docker rm -fv <이름>`. `docker * prune`·일괄 삭제 금지, **이미지 새로 받기·지우기 금지**(있는 것만: eclipse-temurin:21-jdk, maven:3.9-eclipse-temurin-21, postgres:17, redis:7-alpine, node:22-*, grafana/k6:1.2.3, testcontainers/ryuk:0.12.0·0.14.0). **Testcontainers 실험(08 등)만** docker.sock 마운트 허용 — 이미 있는 postgres:17·ryuk 태그로 고정, 실행 전후 `docker ps -a --filter label=org.testcontainers=true`로 남은 것 0 확인. 라이브러리는 maven/npm으로 scratchpad에 받는다. 개인정보 금지, 저장소 루트 파일 금지(절대 경로).
- **I7 실험 근거 우선 — 테스트 해석**: 편마다 실행 가능한 핵심 주장 1개 이상을 실험의 실제 출력으로 보인다(20·21 제외 가능) — 예: 구현 세부를 검증한 테스트가 리팩터링에서 깨지는 수(거짓 양성) vs 관찰 가능한 동작 검증, mock이 실제 계약과 달라 초록인데 통합에서 실패, H2 vs PostgreSQL 방언·락 차이(Testcontainers), 경계값 테스트가 잡는 off-by-one, 속성 기반 테스트의 축소 출력(jqwik), PIT 변이 점수 vs 라인 커버리지(JaCoCo), 순서 의존·시간 의존 불안정 테스트 재현과 가짜 `Clock`, 계약 테스트(Pact) 실패 출력, 특성 테스트 골든 출력, goto fail 재현과 음성 테스트. 출력은 실제 실행만, 코드·환경·출력·관찰을 노트에 싣는다.

## 3. 기준소스 (필수)

- curriculum.md §14, `cs/testing/README.md`, I2 출처

## 4. 금지영역 (필수)

- testing 밖 노트(읽기만), 커리큘럼 본문(필요 시 NEXT)
- 생성 문서 수기 수정 · 이번 작업이 만들지 않은 컨테이너·볼륨·이미지

## 5. 검증 방법 (필수)

- V1 check_new · V1b 사실 점검이 편당 실험 1개+ 재실행 · V2 Opus 사실 점검 · V3 codex(high) 2차 리뷰, 한도(10-04 08:53 리셋) 시 Opus 적대 리뷰 → 판정 · V4 정합(software-design·reliability·domain-modeling 선행 포함) · V5 웹 교차 24+, 링크 신규 깨짐 0, README 재생성, 정리 확인(컨테이너·Testcontainers 라벨 0)

## 6. stakes (필수)

- **중간** — 새 학습 자료 21편, 사실 오류(책 인용·도구 기본값·라이브러리 동작) 위험. Testcontainers의 docker.sock 접근은 라벨·이미지 고정·전후 확인으로 되돌릴 수 있게 한다.

## 7. 자율성

- [x] auto

## 8. load-bearing 가정

- **A1**: 테스트 실험은 maven 이미지 안에서 JUnit 5·Mockito·AssertJ·jqwik·PIT·JaCoCo를 받아 돌리는 소규모 프로젝트로 충분하다(인터넷으로 Maven Central 접근 가능). 착수 직후 한 워커가 스모크로 확인한다.
- **A2**: Testcontainers는 컨테이너 안에서 호스트 docker.sock으로 동작하고, 이미 있는 postgres:17·ryuk만으로 새 pull 없이 된다(`TESTCONTAINERS_RYUK_CONTAINER_IMAGE` 고정). 안 되면 일회용 PG 컨테이너에 직접 붙는 방식으로 대체하고 노트에 밝힌다.

## 9. task 분해

| task | 목표 | acceptance |
|---|---|---|
| 01 | 브리핑(dm판 이식 + 테스트 실험 예시·Testcontainers 규칙) | 브리핑 |
| 02 | 집필(Opus 병렬 5, 워커당 3~5편), 종합 20·21 후속 | 21 PASS |
| 03 | 사실 점검 + 실험 재실행 | packet |
| 04 | 2차 리뷰 → 판정 → 정합 → 웹 | V3~V5 |
| 05 | README·정리·커밋·(확인 후) push·log·NEXT·측정로그 | V5 |

## 승인 상태

- [x] 6칸
- [x] 합의: 사용자 답변(2026-10-03)
- [x] auto
