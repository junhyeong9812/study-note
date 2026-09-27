# 요구사항 명세서 (requirement-spec)

> 작성일: 2026-09-26 · 작업 폴더: `docs/plans/2026-09-26/backend-labs-scaffold/`

---

## 0. 요구사항 원문 (인터뷰 기록)

- 원문: "lab/index.md에 17개 폴더 구조만 만들어줘. 그리고 /home/jun/project/lab폴더 안에 {backend-labs-commerce,backend-labs-tenancy} 2개 폴더 만들고 그 안에 위 주제별로 폴더 만들고 리드미는 /home/jun/다운로드/backend-labs-01-17/backend-labs-all 여기 마크다운 그대로 만들고 전부 코틀린 스프링 21로 app구동만 되도록 코틀린과 스프링 기본설정만 해서 서버 구동 되는 초기값으로 구조만 싹다 만들어놔줘" / "각각 lab주제별로 git init해서 주제별 깃 관리하자."
- 역할 분담 합의: 실 구현 = `/home/jun/project/lab/backend-labs-*/<주제>`, 문서화 = study-note `lab/`.
- Q/A:
  - Boot 버전 → **Spring Boot 3.5.x** (로컬 캐시 3.5.5), Kotlin 2.2.x, JDK 21 toolchain
  - 빌드 구조 → **주제별 완전 독립 프로젝트** (폴더마다 gradle wrapper·settings)
  - 의존성 → **web만** (starter-web + jackson-module-kotlin + kotlin-reflect + starter-test)
  - 포트 → **모듈별 고유 포트** (commerce 8101~8109, tenancy 8210~8217 — 원본 번호 대응)
  - 패키지 → **com.jun.labs.<주제>** (예: `com.jun.labs.seatreservation.SeatReservationApplication`), 폴더명 = 원본 파일명에서 번호 제거
  - git → **주제 폴더마다 git init** (17개 독립 repo)
  - study-note 17개 폴더 → **README에 원본 md 전문 복사**
  - study-note 반영 → **현재 브랜치(docs/nextjs-app-render)에 lab 파일만 커밋**

## 1. 목표·대상 (필수)

- A. `/home/jun/project/lab/backend-labs-commerce/`(01~09, 9개) · `/home/jun/project/lab/backend-labs-tenancy/`(10~17, 8개)에 주제별 독립 Kotlin+Spring Boot 3.5 / JDK 21 프로젝트 17개 — 각 README = 원본 md 전문, 각각 `./gradlew bootRun`으로 고유 포트에서 기동, 각각 독립 git repo(초기 커밋 1개).
- B. study-note `lab/<주제>/README.md` 17개(원본 md 전문) + `lab/index.md` 17행(상태 `예정`).
- 폴더명(양쪽 동일): seat-reservation-lab, payment-consistency-lab, order-saga-lab, ledger-lab, auction-lab, notification-lab, cache-consistency-lab, integration-concert-ticketing, integration-auction-to-order / tenant-isolation-lab, noisy-neighbor-lab, tenant-provisioning-migration-lab, tenant-aware-cache-search-lab, token-lifecycle-lab, authorization-model-lab, cross-tenant-authz-lab, sso-service-auth-lab.
- `00-sources-tenancy-auth.md`(10~17 근거자료): 코드 쪽 `backend-labs-tenancy/00-sources-tenancy-auth.md`(상위 폴더, git 밖) + study-note `lab/backend-labs-tenancy-sources/README.md`로 전문 복사, index에는 "근거자료" 1행.

## 2. 경계·불변식 (필수)

- README는 원본 md와 **바이트 동일**(cmp 일치) — 수정·요약 없음.
- 앱 코드는 `main` + `application.yml`(포트·앱 이름) + contextLoads 테스트뿐 — 도메인 코드·추가 의존성·DB 설정 없음.
- 17개 프로젝트끼리 코드 공유 없음(상위 폴더는 git·빌드 대상 아님).

## 3. 기준소스 (필수)

- 원본 문서: `/home/jun/다운로드/backend-labs-01-17/backend-labs-all/*.md` (18개)
- 빌드 기준: 로컬 Gradle 8.14.4 wrapper, JDK `~/.sdkman/candidates/java/21.0.5-tem`, 캐시된 Spring Boot 3.5.5 / Kotlin 2.2.20

## 4. 금지영역 (필수)

- 원본 폴더(`다운로드/...`) 수정 금지.
- `/home/jun/project/lab`의 기존 6개 네트워크 lab 폴더·README 변경 금지.
- study-note의 미커밋 nextjs·cs 변경을 스테이징/커밋에 섞지 않음 — `lab/` 경로만 add.
- 원격 repo 생성·push 금지.

## 5. 검증 방법 (필수)

- 17개 전부: `./gradlew build`(contextLoads 통과) + bootRun 기동 로그 `Started ...` 및 지정 포트 LISTEN 확인 후 종료 — 스크립트로 결과 17행 표 수집.
- README 17+1개 × 2곳 `cmp` 원본 일치.
- 17개 repo `git log --oneline` 1커밋 확인, study-note 커밋 diff가 `lab/`만 포함하는지 `git show --stat`.

## 6. stakes (필수)

- 판정: **낮음** — 신규 폴더 생성뿐, 기존 코드·데이터 무변경, 삭제로 즉시 복구 가능. 리뷰 = 셀프체크.

---

## 7. 자율성

- [ ] auto (권장)
- [ ] lazy

## 8. load-bearing 가정

1. Gradle wrapper + 캐시된 Boot 3.5.5 / Kotlin 2.2.20 조합으로 JDK 21에서 빌드·기동된다 (첫 프로젝트 1개로 스모크 후 복제).
2. 기본 `java`가 1.8이므로 `JAVA_HOME`을 21로 지정해야 한다 — 각 프로젝트 gradle toolchain 21 명시.

## 9. task 분해

| task | 목표 | 의존 | acceptance |
|------|------|------|-----------|
| 01 | seat-reservation-lab 1개 스캐폴드 + 스모크 | — | build·bootRun 8101 기동 |
| 02 | 나머지 16개 생성(스크립트) + README 복사 + git init/커밋 | 01 | 17행 기동 표 all OK, cmp 일치 |
| 03 | study-note lab 17+1 폴더·index.md + lab/ 한정 커밋 | — | cmp 일치, 커밋 stat = lab/만 |

---

## 승인 상태

- [x] 필수 6칸 전부 기입
- [ ] 사용자 합의 → SPEC=1
- [ ] 자율성 선택 → MODE 기록

---

## 변경 (2026-09-26, 사용자 재합의)

- §1-B 대체: study-note 경로 = `lab/backend-labs/{commerce,tenancy}/<주제>/README.md` (주제 폴더명 = 코드 repo와 동일, 번호 없음). README = 원본 md 그대로(cmp 일치), 이후 작업 기록은 README 끝에 append-only.
- 00-sources → `lab/backend-labs/tenancy/00-sources-tenancy-auth.md`.
- 추가: `lab/backend-labs/README.md`(append-only 워크플로 규칙) + `lab/backend-labs/index.md`(study-note 규약에 맞춘 17행 인덱스) + `lab/index.md`에 backend-labs 1행.
- §4 금지영역 변경(사용자 재합의): GitHub **public** repo 17개 생성 + 초기 커밋 push 허용. repo명 = 번호 없는 폴더명, description = 원본 README 3~4행 주제 문장(08·09는 동시 기동 전환 예정 문구 추가). 초기 커밋 메시지 = `feat(<repo>): 초기 세팅 구조 (...)`.
