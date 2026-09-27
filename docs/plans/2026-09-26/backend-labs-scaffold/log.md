# log — backend-labs-scaffold

## 타임라인

| 시각 | 사건 | 결과/결정 |
|------|------|----------|
| 2026-09-26 | 명세 합의 · MODE=auto | SPEC=1 기록 |
| 2026-09-26 | 사용자 추가 지시: 17개 모두 원격 repo로 올릴 예정 · 원본 md = study-note 각 주제 기본 README · lab/index.md 백엔드 절은 study-note 규약에 맞게 설계 | 명세 범위 내 — push는 이번 작업 밖(사용자 별도 진행/확인) |
| 2026-09-26 | task 01 seat-reservation-lab 스캐폴드 + wrapper 8.14.4 | 스모크 진행 |
| 2026-09-26 | task 01 스모크: seat-reservation-lab JDK21 build 0 · 8101 Tomcat 기동 · 404(매핑 없음=정상) | 가정 1·2 실증 (기본 java 1.8 → JAVA_HOME 21 필수 확인) |
| 2026-09-26 | task 02: 16개 템플릿 복제 + 17개 전수 검증(build 0 · 고유 포트 기동 · README cmp same · 00-sources same) | all OK |
| 2026-09-26 | 17개 repo git init(main) + 초기 커밋 1개, 작업트리 clean 재확인 | 완료. push 없음 |
| 2026-09-26 | 사용자 지시: study-note 구조를 lab/ 평면 → '백엔드 랩 폴더 > 2대분류 > 주제 > README(원본 그대로, 이후 append-only 워크플로)'로 변경 | 명세 변경 → task 03 보류, 경로·번호 확인 질문 중 세션 중단 — 미회답 |
| 2026-09-26 | 17개 gradlew bootRun 실기동 재검증 — 1차 auction-lab FAIL(직전 중단 실행의 고아 프로세스가 8105 점유) → 정리 후 재실행 OK, 전 17개 기동 1.1~1.5s·HTTP 응답·종료 후 포트 해제 | OK |
| 2026-09-26 | study-note 구조 재합의 → lab/backend-labs/{commerce,tenancy}/<주제>/README.md(번호 없음) + README(append-only 규칙) + index(포트·선행 cs) + lab/index 1행. 18개 cmp same, 링크 전수 OK. 08·09·16·17 선행은 원본 Flow 기준으로 정정(추정 매핑 제거) | study-note ca8647b5 (lab/ 21파일만) |
| 2026-09-26 | 초기 커밋 메시지 feat(<repo>) 형식으로 amend(미push 상태) → 사용자 확인 후 GitHub public repo 17개 생성·push | 17개 PUBLIC·main·description·로컬 HEAD=원격 확인 |
| 2026-09-26 | 사용자 지시: 코드 쪽 상위 폴더 backend-labs-{commerce,tenancy}/README.md 신설(git 밖) — 구현은 repo, 기록은 study-note 주제별 append-only, 도식화+문서화 병행 명시, 주제·포트·기록 링크 표 | 17 repo clean 유지 |
| 2026-09-26 | 작업 기록 템플릿에 '도식' 항목 추가 | study-note a3cca56d |
| 2026-09-26 | 사이클 마감: NEXT.md 최초 생성 · measurement-log 1행 · CS 이슈 아카이브 0건(스캐폴드 작업, 새 CS 개념 없음) | 완료 |

## 완료 요약

- 코드: /home/jun/project/lab/backend-labs-{commerce(9),tenancy(8)} — 주제별 독립 Kotlin 2.2.20 · Spring Boot 3.5.5 · JDK 21 프로젝트, 각 GitHub public repo(main, 초기 커밋 feat(<repo>)), bootRun 17/17 기동 확인. 상위 폴더 README(git 밖) = 구현/기록 분리·도식화 병행 규칙.
- study-note: lab/backend-labs/{README(append-only 규칙), index(포트·선행 cs·상태), commerce/*, tenancy/*} — 원본 18개 cmp 일치. 커밋 ca8647b5, a3cca56d (lab/만).
- 이월: NEXT.md 참조. docs/plans·NEXT·measurement-log는 미커밋(사용자 지시: lab/만 커밋).
| 2026-09-26 | 정정: tenancy 선행 cs '없음' 판단 오류(domain-modeling·ops만 조사) — systems/multi-tenancy·postgres-rls·foundations/security·security-standards로 연결, 링크 전수 OK. NEXT 보류 항목 삭제 | study-note ca323b55 |
| 2026-09-27 | 사용자 지시: seat-reservation-lab 제외 16개 repo private 전환 | 조회 확인 — PUBLIC 1(seat) · PRIVATE 16. 상위 README 문구 갱신 |
